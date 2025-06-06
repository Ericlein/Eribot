# EriBot Quick Start Guide 🚀

Get EriBot up and running in less than 5 minutes! This guide will have you monitoring your system and receiving Slack alerts in no time.

## 📋 Prerequisites Checklist

Before you begin, ensure you have:

- [ ] **Python 3.10+** installed ([Download](https://python.org))
- [ ] **.NET 8.0+ SDK** installed ([Download](https://dotnet.microsoft.com/download))
- [ ] **Slack workspace** with admin permissions
- [ ] **5 minutes** of your time ⏰

## 🔑 Step 1: Get Your Slack Bot Token

### Create a Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Name your app **"EriBot"** and select your workspace
4. Click **"Create App"**

### Configure Bot Permissions
1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Add these permissions:
   - `chat:write` - Send messages
   - `chat:write.public` - Send messages to public channels

### Install to Workspace
1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. **Copy the Bot User OAuth Token** (starts with `xoxb-`)

> 💡 **Keep this token secure!** Never commit it to version control.

## ⚡ Step 2: Choose Your Installation Method

### 🐳 Option A: Docker (Recommended)

**Fastest setup with zero dependencies to install:**

```bash
# Clone the repository
git clone https://github.com/Ericlein/eribot.git
cd eribot

# Create environment file
cat > .env << EOF
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#devops-alerts
CPU_THRESHOLD=90
DISK_THRESHOLD=90
CHECK_INTERVAL=60
EOF

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

### 🖥️ Option B: Native Installation

**For when you want full control:**

**Windows (PowerShell as Administrator):**
```powershell
# Download and run installer
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Ericlein/eribot/main/scripts/install.ps1" -OutFile "install.ps1"
.\install.ps1 -SlackToken "xoxb-your-token-here" -InstallAsService
```

**Linux/macOS:**
```bash
# Download and run installer
curl -fsSL https://raw.githubusercontent.com/Ericlein/eribot/main/scripts/install.sh | sudo bash -s -- "xoxb-your-token-here" --service
```

### 🛠️ Option C: Manual Setup

**For developers who want to see what's happening:**

```bash
# 1. Clone repository
git clone https://github.com/Ericlein/eribot.git
cd eribot

# 2. Set up Python environment
cd python_monitor
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Build C# service
cd ../csharp_remediator
dotnet build --configuration Release

# 4. Configure environment
cd ..
cp .env.example .env
# Edit .env with your token

# 5. Start services (in separate terminals)
# Terminal 1: Remediation service
cd csharp_remediator && dotnet run

# Terminal 2: Monitoring service
cd python_monitor && python main.py
```

## 🧪 Step 3: Test Your Installation

### Verify Services are Running

**Docker:**
```bash
# Check container status
docker-compose ps

# Should show both services as "Up"
```

**Native/Manual:**
```bash
# Test remediation service
curl http://localhost:5001/health
# Should return: {"status":"healthy"}

# Check logs
tail -f logs/monitor.log
tail -f logs/remediator.log
```

### Test Slack Integration

**Send a test message:**
```bash
# Docker
docker-compose exec eribot-monitor python -c "
from clients.slack import SlackClient
from config import load_config
config = load_config()
client = SlackClient(config.slack)
print('Test result:', client.send_message('🤖 EriBot test message!'))
"

# Native
cd python_monitor
python -c "
from clients.slack import SlackClient
from config import load_config
config = load_config()
client = SlackClient(config.slack)
print('Test result:', client.send_message('🤖 EriBot test message!'))
"
```

You should see a message in your Slack channel! 🎉

### Trigger a Test Alert

**Simulate high CPU usage:**

**Linux/macOS:**
```bash
# Start CPU load (in background)
yes > /dev/null &
CPU_PID=$!

# Wait for alert (should trigger within 60 seconds)
# Stop the load
kill $CPU_PID
```

**Windows:**
```powershell
# Start CPU intensive process
Start-Job { while($true) { Get-Random } }

# Wait for alert, then stop
Get-Job | Stop-Job
Get-Job | Remove-Job
```

**Docker (any platform):**
```bash
# Stress test the container
docker-compose exec eribot-monitor python -c "
import multiprocessing
import time
# This will spike CPU briefly
[x*x for x in range(10000000)]
"
```

## 📊 Step 4: Monitor Your System

### Default Monitoring

EriBot automatically monitors:
- **CPU Usage** > 90%
- **Memory Usage** > 90%  
- **Disk Usage** > 90%
- **Service Health** every 60 seconds

### Customize Thresholds

**Environment variables (recommended):**
```bash
export CPU_THRESHOLD=80        # Alert at 80% CPU
export MEMORY_THRESHOLD=85     # Alert at 85% memory
export CHECK_INTERVAL=30       # Check every 30 seconds
```

**Configuration file:**
```yaml
# config/config.yaml
monitoring:
  cpu_threshold: 80
  memory_threshold: 85
  disk_threshold: 80
  check_interval: 30
```

### View Real-time Status

**Check system health:**
```bash
# Get current system status
curl http://localhost:5001/api/health/detailed

# Get available remediation actions
curl http://localhost:5001/api/remediation/actions
```

## 🛡️ Step 5: Understanding Alerts

### Alert Types and What They Mean

| Alert | Cause | Action Taken |
|-------|-------|--------------|
| 🟡 **High CPU** | CPU > threshold | Process cleanup, temp file removal |
| 🟡 **High Memory** | Memory > threshold | Garbage collection, cache clearing |
| 🟡 **High Disk** | Disk > threshold | Temp cleanup, log rotation |
| 🔴 **Service Down** | Health check fails | Service restart (simulated) |
| 🟢 **Remediation Success** | Action completed | Confirmation message |
| ❌ **Remediation Failed** | Action failed | Error details and next steps |

### Sample Slack Messages

```
🟡 WARNING: High CPU usage detected: 92.5%
🛠️ Remediation triggered for high_cpu
✅ High CPU remediation completed: cleaned 47 temp files (125 MB)
```

## 🔧 Step 6: Advanced Configuration

### Multiple Channels

Route different alerts to different channels:

```bash
# Environment approach
export SLACK_CHANNEL_ALERTS="#critical-alerts"
export SLACK_CHANNEL_INFO="#system-info"

# Or use webhooks for multiple channels
export SLACK_WEBHOOK_CRITICAL="https://hooks.slack.com/services/..."
export SLACK_WEBHOOK_INFO="https://hooks.slack.com/services/..."
```

### Custom Remediation Actions

Add your own remediation scripts:

```bash
# Add to csharp_remediator/Services/RemediationService.cs
case "custom_cleanup":
    return await CustomCleanupAsync(request);
```

### Production Settings

For production environments:

```yaml
# config/config.yaml
monitoring:
  cpu_threshold: 90
  memory_threshold: 90
  check_interval: 30        # More frequent checks

logging:
  level: "WARNING"          # Less verbose logging
  max_file_size: "50MB"     # Larger log files

remediator:
  timeout: 60              # Longer timeouts
  retry_attempts: 5        # More retries
```

## 🧪 Step 7: Testing Your Setup

### Run Unit Tests

```bash
cd python_monitor

# Install test dependencies (if not already installed)
pip install pytest pytest-cov pytest-mock

# Run unit tests
pytest tests/ -v -m "unit"

# Run with coverage
pytest tests/ -v -m "unit" --cov=. --cov-report=html
```

### Run Integration Tests

```bash
# Set up test environment
export SLACK_BOT_TOKEN=xoxb-your-token-here
export SLACK_CHANNEL=#test-alerts

# Run integration tests (requires real services)
pytest tests/ -v -m "integration" --run-integration
```

### Test Categories

- **Unit Tests**: Fast tests with mocking, no external dependencies
- **Integration Tests**: Tests with real Slack API and services
- **Slow Tests**: Performance and stress tests

### View Test Coverage

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🚨 Troubleshooting

### Common Issues

**"Slack messages not sending"**
```bash
# Check token format
echo $SLACK_BOT_TOKEN | head -c 20
# Should start with "xoxb-"

# Test authentication
cd python_monitor
python -c "
from clients.slack import SlackClient
from config import load_config
config = load_config()
client = SlackClient(config.slack)
print('Auth test:', client.test_connection())
"
```

**"Remediation service not responding"**
```bash
# Check if port is in use
netstat -an | grep 5001

# Check logs
tail -f logs/remediator.log

# Restart service
docker-compose restart eribot-remediator
# OR
sudo systemctl restart eribot-remediator
```

**"High resource usage not triggering alerts"**
```bash
# Lower threshold temporarily for testing
export CPU_THRESHOLD=50
export MEMORY_THRESHOLD=50

# Check current usage
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

**"Import errors in Python"**
```bash
# Check Python path
cd python_monitor
export PYTHONPATH=$(pwd)
python -c "from config import load_config; print('Imports working')"

# Verify dependencies
pip install -r requirements.txt
```

### Getting Help

**Check system status:**
```bash
# Docker
docker-compose logs --tail=50 eribot-monitor
docker-compose logs --tail=50 eribot-remediator

# Native
tail -f logs/monitor.log
tail -f logs/remediator.log
```

**Validate configuration:**
```bash
cd python_monitor
python -c "
from config import load_config
try:
    config = load_config()
    print('Configuration loaded successfully')
    print(f'CPU threshold: {config.monitoring.cpu_threshold}%')
    print(f'Slack channel: {config.slack.channel}')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

**Test individual components:**
```bash
# Test Slack client
cd python_monitor
python -c "
from clients.slack import SlackClient
from config import load_config
config = load_config()
client = SlackClient(config.slack)
print('Slack test:', client.send_message('Test from setup'))
"

# Test remediation client
python -c "
from clients.remediation import RemediationClient
from config import load_config
config = load_config()
client = RemediationClient(config.remediator)
print('Remediation status:', client.get_service_status())
"
```

## 🎯 Next Steps

Now that EriBot is running:

1. **📱 Set up additional Slack channels** for different alert types
2. **⚙️ Customize thresholds** based on your system requirements  
3. **📊 Add monitoring dashboards** using the optional Grafana setup
4. **🔒 Review security settings** for production deployment
5. **📖 Read the full documentation** for advanced features

### Optional Enhancements

**Add monitoring dashboard:**
```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana at http://localhost:3000
# Default login: admin/admin
```

**Set up log aggregation:**
```bash
# Start with logging stack
docker-compose --profile logging up -d
```

**Run security scans:**
```bash
# Security scanning
bandit -r python_monitor/
safety check
```

## 🎉 Congratulations!

You now have a fully functional system monitoring and auto-remediation bot! EriBot will:

- ✅ Monitor your system 24/7
- ✅ Send intelligent Slack alerts
- ✅ Automatically fix common issues
- ✅ Keep detailed logs of all activities

**Pro tip:** Join the `#devops-alerts` channel and watch EriBot in action. You'll be amazed at how much peace of mind automated monitoring can provide!

---

**Need help?** Check out the [full README](README.md) or [open an issue](https://github.com/Ericlein/eribot/issues).