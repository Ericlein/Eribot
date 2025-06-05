# EriBot Windows Installation Script
# Run as Administrator: powershell -ExecutionPolicy Bypass -File install.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$SlackToken,
    
    [string]$SlackChannel = "#devops-alerts",
    [string]$InstallPath = "C:\EriBot",
    [switch]$InstallAsService
)

Write-Host "🤖 EriBot Windows Installation Starting..." -ForegroundColor Green

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator!"
    exit 1
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.([0-9]+)") {
        $minorVersion = [int]$matches[1]
        if ($minorVersion -lt 10) {
            Write-Error "Python 3.10+ required. Current: $pythonVersion"
            exit 1
        }
        Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
    }
} catch {
    Write-Error "Python not found. Please install Python 3.10+ and add to PATH"
    exit 1
}

# Check .NET
try {
    $dotnetVersion = dotnet --version 2>&1
    Write-Host "✓ .NET: $dotnetVersion" -ForegroundColor Green
} catch {
    Write-Error ".NET not found. Please install .NET 8.0+ SDK"
    exit 1
}

# Create installation directory
Write-Host "Creating installation directory..." -ForegroundColor Yellow
if (Test-Path $InstallPath) {
    Write-Host "Installation directory exists, backing up..." -ForegroundColor Yellow
    $backupPath = "$InstallPath.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Move-Item $InstallPath $backupPath
    Write-Host "Backup created at: $backupPath" -ForegroundColor Green
}

New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Set-Location $InstallPath

# Copy application files
Write-Host "Installing application files..." -ForegroundColor Yellow

# Create directory structure
$dirs = @("python_monitor", "csharp_remediator", "logs", "config")
foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Create Python requirements file
@"
slack-sdk==3.20.0
requests==2.31.0
psutil==5.9.0
pyyaml==6.0
pytest==7.4.0
"@ | Out-File -FilePath "python_monitor\requirements.txt" -Encoding UTF8

# Create configuration file
@"
monitoring:
  cpu_threshold: 85
  disk_threshold: 90
  check_interval: 60

slack:
  channel: "$SlackChannel"

remediator:
  url: "http://localhost:5001/remediate"
"@ | Out-File -FilePath "config\config.yaml" -Encoding UTF8

# Create environment file
@"
SLACK_BOT_TOKEN=$SlackToken
SLACK_CHANNEL=$SlackChannel
CPU_THRESHOLD=85
DISK_THRESHOLD=90
CHECK_INTERVAL=60
REMEDIATOR_URL=http://localhost:5001/remediate
"@ | Out-File -FilePath "config\.env" -Encoding UTF8

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Set-Location "$InstallPath\python_monitor"
python -m pip install -r requirements.txt

# Build C# application
Write-Host "Building C# remediation service..." -ForegroundColor Yellow
Set-Location "$InstallPath\csharp_remediator"

# Create C# project file
@"
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <InvariantGlobalization>true</InvariantGlobalization>
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>true</SelfContained>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
  </PropertyGroup>
</Project>
"@ | Out-File -FilePath "EriBot.Remediator.csproj" -Encoding UTF8

dotnet publish -c Release -o "$InstallPath\bin"

# Create startup scripts
Set-Location $InstallPath

# Python monitor startup script
@"
@echo off
cd /d "$InstallPath\python_monitor"
set PYTHONPATH=%CD%
python monitor.py
pause
"@ | Out-File -FilePath "start_monitor.bat" -Encoding ASCII

# C# remediator startup script
@"
@echo off
cd /d "$InstallPath\bin"
EriBot.Remediator.exe
pause
"@ | Out-File -FilePath "start_remediator.bat" -Encoding ASCII

# Combined startup script
@"
@echo off
echo Starting EriBot Services...
start "EriBot Monitor" cmd /k "$InstallPath\start_monitor.bat"
timeout /t 2 /nobreak > nul
start "EriBot Remediator" cmd /k "$InstallPath\start_remediator.bat"
echo Both services started!
"@ | Out-File -FilePath "start_eribot.bat" -Encoding ASCII

# Create Windows Service installer (optional)
if ($InstallAsService) {
    Write-Host "Installing as Windows Service..." -ForegroundColor Yellow
    
    # Install NSSM (Non-Sucking Service Manager) for service wrapper
    try {
        $nssmPath = "$InstallPath\nssm.exe"
        if (-not (Test-Path $nssmPath)) {
            Write-Host "Downloading NSSM..." -ForegroundColor Yellow
            Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "$InstallPath\nssm.zip"
            Expand-Archive "$InstallPath\nssm.zip" -DestinationPath $InstallPath
            Copy-Item "$InstallPath\nssm-2.24\win64\nssm.exe" $nssmPath
            Remove-Item "$InstallPath\nssm.zip", "$InstallPath\nssm-2.24" -Recurse -Force
        }
        
        # Install services
        & $nssmPath install "EriBot-Monitor" python "$InstallPath\python_monitor\monitor.py"
        & $nssmPath set "EriBot-Monitor" AppDirectory "$InstallPath\python_monitor"
        & $nssmPath set "EriBot-Monitor" DisplayName "EriBot System Monitor"
        & $nssmPath set "EriBot-Monitor" Description "EriBot Python monitoring service"
        & $nssmPath set "EriBot-Monitor" Start SERVICE_AUTO_START
        
        & $nssmPath install "EriBot-Remediator" "$InstallPath\bin\EriBot.Remediator.exe"
        & $nssmPath set "EriBot-Remediator" AppDirectory "$InstallPath\bin"
        & $nssmPath set "EriBot-Remediator" DisplayName "EriBot Remediation Service"
        & $nssmPath set "EriBot-Remediator" Description "EriBot C# remediation service"
        & $nssmPath set "EriBot-Remediator" Start SERVICE_AUTO_START
        
        Write-Host "✓ Services installed successfully!" -ForegroundColor Green
        Write-Host "Use 'services.msc' to manage EriBot services" -ForegroundColor Yellow
        
    } catch {
        Write-Warning "Service installation failed: $_"
        Write-Host "You can still run EriBot manually using start_eribot.bat" -ForegroundColor Yellow
    }
}

# Create uninstall script
@"
@echo off
echo Stopping EriBot services...
taskkill /f /im python.exe /fi "WINDOWTITLE eq EriBot Monitor*" 2>nul
taskkill /f /im EriBot.Remediator.exe 2>nul

if exist "$InstallPath\nssm.exe" (
    echo Removing Windows services...
    "$InstallPath\nssm.exe" stop EriBot-Monitor 2>nul
    "$InstallPath\nssm.exe" stop EriBot-Remediator 2>nul
    "$InstallPath\nssm.exe" remove EriBot-Monitor confirm 2>nul
    "$InstallPath\nssm.exe" remove EriBot-Remediator confirm 2>nul
)

echo EriBot stopped. Run this again to completely remove EriBot.
pause
"@ | Out-File -FilePath "uninstall.bat" -Encoding ASCII

# Set file permissions
icacls $InstallPath /grant "Users:(RX)" /t | Out-Null

Write-Host "`n🎉 EriBot Installation Complete!" -ForegroundColor Green
Write-Host "Installation Location: $InstallPath" -ForegroundColor White
Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Review configuration in: $InstallPath\config\config.yaml" -ForegroundColor White
Write-Host "2. Test Slack connection by running: $InstallPath\start_eribot.bat" -ForegroundColor White

if ($InstallAsService) {
    Write-Host "3. Services are installed and will start automatically" -ForegroundColor White
    Write-Host "   - EriBot-Monitor" -ForegroundColor Gray
    Write-Host "   - EriBot-Remediator" -ForegroundColor Gray
} else {
    Write-Host "3. Start manually: $InstallPath\start_eribot.bat" -ForegroundColor White
}

Write-Host "`nMonitoring will begin immediately and alerts will be sent to: $SlackChannel" -ForegroundColor Green