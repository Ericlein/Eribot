#!/bin/bash
# EriBot Linux Installation Script
# Usage: sudo bash install.sh <slack_token> [options]

set -e

# Default values
SLACK_CHANNEL="#devops-alerts"
INSTALL_PATH="/opt/eribot"
INSTALL_AS_SERVICE=false
USER="eribot"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${GREEN}$1${NC}"; }
log_warn() { echo -e "${YELLOW}$1${NC}"; }
log_error() { echo -e "${RED}$1${NC}"; }

show_usage() {
    echo "Usage: $0 <slack_token> [options]"
    echo "Options:"
    echo "  -c, --channel CHANNEL    Slack channel (default: #devops-alerts)"
    echo "  -p, --path PATH          Installation path (default: /opt/eribot)"
    echo "  -s, --service            Install as systemd service"
    echo "  -u, --user USER          Service user (default: eribot)"
    echo "  -h, --help               Show this help"
    exit 1
}

# Parse arguments
if [ $# -eq 0 ]; then
    show_usage
fi

SLACK_TOKEN="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--channel)
            SLACK_CHANNEL="$2"
            shift 2
            ;;
        -p|--path)
            INSTALL_PATH="$2"
            shift 2
            ;;
        -s|--service)
            INSTALL_AS_SERVICE=true
            shift
            ;;
        -u|--user)
            USER="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            ;;
    esac
done

log_info "🤖 EriBot Linux Installation Starting..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    DISTRO=$ID
    log_info "Detected OS: $OS"
else
    log_error "Cannot detect OS. /etc/os-release not found."
    exit 1
fi

# Check prerequisites
log_warn "Checking prerequisites..."

# Check Python 3.10+
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        log_info "✓ Python: $(python3 --version)"
    else
        log_error "Python 3.10+ required. Current: $(python3 --version)"
        exit 1
    fi
else
    log_error "Python3 not found. Installing..."
    
    # Install Python based on distro
    case $DISTRO in
        ubuntu|debian)
            apt update && apt install -y python3 python3-pip python3-venv
            ;;
        centos|rhel|fedora)
            if command -v dnf &> /dev/null; then
                dnf install -y python3 python3-pip
            else
                yum install -y python3 python3-pip
            fi
            ;;
        *)
            log_error "Unsupported distribution for automatic Python installation"
            exit 1
            ;;
    esac
fi

# Check .NET
if command -v dotnet &> /dev/null; then
    log_info "✓ .NET: $(dotnet --version)"
else
    log_warn ".NET not found. Installing..."
    
    # Install .NET based on distro
    case $DISTRO in
        ubuntu)
            apt update
            apt install -y wget
            wget https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
            dpkg -i packages-microsoft-prod.deb
            rm packages-microsoft-prod.deb
            apt update
            apt install -y dotnet-sdk-8.0
            ;;
        debian)
            apt update
            apt install -y wget
            wget https://packages.microsoft.com/config/debian/$(cat /etc/debian_version | cut -d. -f1)/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
            dpkg -i packages-microsoft-prod.deb
            rm packages-microsoft-prod.deb
            apt update
            apt install -y dotnet-sdk-8.0
            ;;
        centos|rhel)
            if command -v dnf &> /dev/null; then
                dnf install -y dotnet-sdk-8.0
            else
                yum install -y dotnet-sdk-8.0
            fi
            ;;
        fedora)
            dnf install -y dotnet-sdk-8.0
            ;;
        *)
            log_error "Unsupported distribution for automatic .NET installation"
            exit 1
            ;;
    esac
fi

# Create user for service
if $INSTALL_AS_SERVICE && ! id "$USER" &>/dev/null; then
    log_warn "Creating user: $USER"
    useradd -r -s /bin/false -d $INSTALL_PATH $USER
fi

# Create installation directory
log_warn "Creating installation directory..."
if [ -d "$INSTALL_PATH" ]; then
    log_warn "Installation directory exists, backing up..."
    BACKUP_PATH="${INSTALL_PATH}.backup.$(date +%Y%m%d-%H%M%S)"
    mv "$INSTALL_PATH" "$BACKUP_PATH"
    log_info "Backup created at: $BACKUP_PATH"
fi

mkdir -p "$INSTALL_PATH"
cd "$INSTALL_PATH"

# Create directory structure
mkdir -p python_monitor csharp_remediator logs config bin

# Create Python requirements file
cat > python_monitor/requirements.txt << 'EOF'
slack-sdk==3.20.0
requests==2.31.0
psutil==5.9.0
pyyaml==6.0
pytest==7.4.0
EOF

# Create configuration file
cat > config/config.yaml << EOF
monitoring:
  cpu_threshold: 90
  disk_threshold: 90
  check_interval: 60

slack:
  channel: "$SLACK_CHANNEL"

remediator:
  url: "http://localhost:5001/remediate"
EOF

# Create environment file
cat > config/.env << EOF
SLACK_BOT_TOKEN=$SLACK_TOKEN
SLACK_CHANNEL=$SLACK_CHANNEL
CPU_THRESHOLD=90
DISK_THRESHOLD=90
CHECK_INTERVAL=60
REMEDIATOR_URL=http://localhost:5001/remediate
EOF

# Install Python dependencies
log_warn "Installing Python dependencies..."
cd "$INSTALL_PATH/python_monitor"
python3 -m pip install -r requirements.txt

# Build C# application
log_warn "Building C# remediation service..."
cd "$INSTALL_PATH/csharp_remediator"

# Create C# project file
cat > EriBot.Remediator.csproj << 'EOF'
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <InvariantGlobalization>true</InvariantGlobalization>
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>true</SelfContained>
    <RuntimeIdentifier>linux-x64</RuntimeIdentifier>
  </PropertyGroup>
</Project>
EOF

dotnet publish -c Release -o "$INSTALL_PATH/bin"

# Create startup scripts
cd "$INSTALL_PATH"

# Python monitor startup script
cat > start_monitor.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/python_monitor"
export PYTHONPATH="$(pwd)"
python3 monitor.py
EOF
chmod +x start_monitor.sh

# C# remediator startup script
cat > start_remediator.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/bin"
./EriBot.Remediator
EOF
chmod +x start_remediator.sh

# Combined startup script
cat > start_eribot.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(dirname "$0")"
echo "Starting EriBot Services..."

# Start monitor in background
"$SCRIPT_DIR/start_monitor.sh" &
MONITOR_PID=$!
echo "Monitor started with PID: $MONITOR_PID"

# Wait a moment, then start remediator
sleep 2
"$SCRIPT_DIR/start_remediator.sh" &
REMEDIATOR_PID=$!
echo "Remediator started with PID: $REMEDIATOR_PID"

# Save PIDs for stopping
echo $MONITOR_PID > "$SCRIPT_DIR/monitor.pid"
echo $REMEDIATOR_PID > "$SCRIPT_DIR/remediator.pid"

echo "Both services started!"
echo "Monitor PID: $MONITOR_PID"
echo "Remediator PID: $REMEDIATOR_PID"

# Wait for services
wait
EOF
chmod +x start_eribot.sh

# Create stop script
cat > stop_eribot.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(dirname "$0")"

echo "Stopping EriBot services..."

# Stop using PID files if they exist
if [ -f "$SCRIPT_DIR/monitor.pid" ]; then
    MONITOR_PID=$(cat "$SCRIPT_DIR/monitor.pid")
    if kill -0 "$MONITOR_PID" 2>/dev/null; then
        kill "$MONITOR_PID"
        echo "Monitor stopped (PID: $MONITOR_PID)"
    fi
    rm -f "$SCRIPT_DIR/monitor.pid"
fi

if [ -f "$SCRIPT_DIR/remediator.pid" ]; then
    REMEDIATOR_PID=$(cat "$SCRIPT_DIR/remediator.pid")
    if kill -0 "$REMEDIATOR_PID" 2>/dev/null; then
        kill "$REMEDIATOR_PID"
        echo "Remediator stopped (PID: $REMEDIATOR_PID)"
    fi
    rm -f "$SCRIPT_DIR/remediator.pid"
fi

# Fallback: kill by process name
pkill -f "python3.*monitor.py" 2>/dev/null || true
pkill -f "EriBot.Remediator" 2>/dev/null || true

echo "EriBot services stopped."
EOF
chmod +x stop_eribot.sh

# Install as systemd service (optional)
if $INSTALL_AS_SERVICE; then
    log_warn "Installing as systemd service..."
    
    # Create monitor service
    cat > /etc/systemd/system/eribot-monitor.service << EOF
[Unit]
Description=EriBot System Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_PATH/python_monitor
Environment=PYTHONPATH=$INSTALL_PATH/python_monitor
EnvironmentFile=$INSTALL_PATH/config/.env
ExecStart=/usr/bin/python3 $INSTALL_PATH/python_monitor/monitor.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_PATH/logs/monitor.log
StandardError=append:$INSTALL_PATH/logs/monitor-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Create remediator service
    cat > /etc/systemd/system/eribot-remediator.service << EOF
[Unit]
Description=EriBot Remediation Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_PATH/bin
EnvironmentFile=$INSTALL_PATH/config/.env
ExecStart=$INSTALL_PATH/bin/EriBot.Remediator
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_PATH/logs/remediator.log
StandardError=append:$INSTALL_PATH/logs/remediator-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Set proper ownership
    chown -R $USER:$USER "$INSTALL_PATH"
    
    # Reload systemd and enable services
    systemctl daemon-reload
    systemctl enable eribot-monitor.service
    systemctl enable eribot-remediator.service
    
    log_info "✓ Services installed successfully!"
    log_warn "Use 'systemctl start/stop/status eribot-monitor' and 'systemctl start/stop/status eribot-remediator' to manage services"
    
    # Start services
    systemctl start eribot-remediator
    sleep 2
    systemctl start eribot-monitor
    
    log_info "✓ Services started!"
else
    # Set ownership for manual operation
    chown -R $USER:$USER "$INSTALL_PATH" 2>/dev/null || true
fi

# Create uninstall script
cat > uninstall.sh << 'EOF'
#!/bin/bash
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root (use sudo)"
    exit 1
fi

echo "Stopping EriBot services..."

# Stop systemd services if they exist
systemctl stop eribot-monitor 2>/dev/null || true
systemctl stop eribot-remediator 2>/dev/null || true
systemctl disable eribot-monitor 2>/dev/null || true
systemctl disable eribot-remediator 2>/dev/null || true

# Remove service files
rm -f /etc/systemd/system/eribot-monitor.service
rm -f /etc/systemd/system/eribot-remediator.service
systemctl daemon-reload

# Stop manual processes
pkill -f "python3.*monitor.py" 2>/dev/null || true
pkill -f "EriBot.Remediator" 2>/dev/null || true

echo "EriBot services stopped and removed."
echo "Installation directory remains at: $INSTALL_PATH"
echo "Run 'rm -rf $INSTALL_PATH' to completely remove EriBot."
EOF
chmod +x uninstall.sh

# Set final permissions
chmod -R 755 "$INSTALL_PATH"
chown -R $USER:$USER "$INSTALL_PATH" 2>/dev/null || true

log_info ""
log_info "🎉 EriBot Installation Complete!"
log_info "Installation Location: $INSTALL_PATH"
log_info ""
log_warn "Next Steps:"
log_info "1. Review configuration in: $INSTALL_PATH/config/config.yaml"
log_info "2. Test Slack connection"

if $INSTALL_AS_SERVICE; then
    log_info "3. Services are installed and running:"
    log_info "   - systemctl status eribot-monitor"
    log_info "   - systemctl status eribot-remediator"
    log_info "4. View logs: tail -f $INSTALL_PATH/logs/*.log"
else
    log_info "3. Start manually: $INSTALL_PATH/start_eribot.sh"
    log_info "4. Stop manually: $INSTALL_PATH/stop_eribot.sh"
fi

log_info ""
log_info "Monitoring will begin immediately and alerts will be sent to: $SLACK_CHANNEL"

# Test installation
log_warn "Testing installation..."
if $INSTALL_AS_SERVICE; then
    sleep 5
    if systemctl is-active --quiet eribot-monitor && systemctl is-active --quiet eribot-remediator; then
        log_info "✓ All services are running successfully!"
    else
        log_error "⚠ Some services failed to start. Check logs in $INSTALL_PATH/logs/"
    fi
else
    log_warn "Run $INSTALL_PATH/start_eribot.sh to test the installation"
fi