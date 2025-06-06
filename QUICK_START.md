# EriBot Quick Start Guide

## 🚀 Quick Installation

### Prerequisites
- Python 3.10+ 
- .NET 8.0+ SDK
- Slack Bot Token

### 1. Get Slack Bot Token
1. Go to https://api.slack.com/apps
2. Create a new app for your workspace
3. Go to OAuth & Permissions
4. Add bot token scopes: `chat:write`, `chat:write.public`
5. Install app to workspace
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 2. Windows Installation

```powershell
# Download and run as Administrator
powershell -ExecutionPolicy Bypass -Command "& {Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/your-repo/eribot/main/install.ps1' -OutFile 'install.ps1'; .\install.ps1 -SlackToken 'xoxb-your-token-here' -InstallAsService}"
```

### 3. Linux Installation

```bash
# Download and run as root
curl -fsSL https://raw.githubusercontent.com/your-repo/eribot/main/install.sh | sudo bash -s -- "xoxb-your-token-here" --service
```

### 4. Docker Installation

```bash
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

# View logs
docker-compose logs -f
```

## ⚙️ Manual Installation

### Clone and Setup
```bash
git clone https://github.com/your-repo/eribot.git
cd eribot

# Copy your source files to the project structure:
# python_monitor/monitor.py
# python_monitor/config_loader.py
# python_monitor/slack_client.py
# python_monitor/remediation_client.py
# csharp_remediator/Program.cs
# config/config.yaml
```

### Python Setup
```bash
cd python_monitor
pip install -r requirements.txt

# Create .env file
echo "SLACK_BOT_TOKEN=xoxb-your-token-here" > .env
echo "SLACK_CHANNEL=#devops-alerts" >> .env

# Test
python monitor.py
```

### C# Setup
```bash
cd csharp_remediator
dotnet build
dotnet run

# Test endpoint
curl http://localhost:5001/health
```

## 🔧 Configuration

### Basic Configuration (`config/config.yaml`)
```yaml
monitoring:
  cpu_threshold: 90      # CPU % to trigger alert
  disk_threshold: 90     # Disk % to trigger alert  
  check_interval: 60     # Check every 60 seconds

slack:
  channel: "#devops-alerts"

remediator:
  url: "http://localhost:5001/remediate"
```

### Environment Variables
```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token

# Optional overrides
SLACK_CHANNEL=#your-channel
CPU_THRESHOLD=90
DISK_THRESHOLD=90
CHECK_INTERVAL=30
REMEDIATOR_URL=http://localhost:5001/remediate
```

## 🎯 Testing

### Test Slack Connection
```bash
# Python test
python -c "
import os
from slack_client import SlackClient
from config_loader import SlackConfig

config = SlackConfig(
    channel='#devops-alerts',
    token=os.getenv('SLACK_BOT_TOKEN')
)
client = SlackClient(config)
client.send_message('🤖 EriBot test message!')
"
```

### Test Remediation Service
```bash
# Test health endpoint
curl http://localhost:5001/health

# Test remediation
curl -X POST http://localhost:5001/remediate \
  -H "Content-Type: application/json" \
  -d '{"issueType": "high_cpu", "context": {"cpu_percent": 95}}'
```

### Simulate High Resource Usage
```bash
# Simulate high CPU (Linux/Mac)
yes > /dev/null &  # Start background CPU load
# Kill with: pkill yes

# Simulate high disk (create large file)
dd if=/dev/zero of=/tmp/bigfile bs=1M count=1000

# Watch monitoring
tail -f logs/monitor.log
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Start with monitoring stack
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f eribot-monitor
docker-compose logs -f eribot-remediator

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## 🔍 Troubleshooting

### Common Issues

**1. Slack messages not sending**
- Check bot token is correct
- Verify bot has permission to post in channel
- Check channel name includes `#`

**2. High CPU/Disk not triggering**
- Lower thresholds for testing
- Check system actually exceeds thresholds
- Verify remediation service is reachable

**3. Service won't start**
- Check logs in `logs/` directory
- Verify Python/C# are installed correctly
- Check firewall blocking port 5001

**4. Permission errors (Linux)**
- Ensure service user has correct permissions
- Check SELinux/AppArmor policies
- Run with `sudo` for testing

### Log Locations
- **Windows Service**: `C:\EriBot\logs\`
- **Linux Service**: `/opt/eribot/logs/`
- **Docker**: `docker-compose logs`
- **Manual**: `./logs/`

### Useful Commands
```bash
# Check service status (Linux)
systemctl status eribot-monitor
systemctl status eribot-remediator

# Windows services
Get-Service EriBot-Monitor
Get-Service EriBot-Remediator

# Manual process check
ps aux | grep -E "(monitor\.py|EriBot\.Remediator)"

# Test network connectivity
telnet localhost 5001
```

## 📊 Monitoring

### Default Alerts
- **High CPU**: >85% for 1+ minutes
- **High Disk**: >90% usage
- **Service Failures**: Remediation errors
- **System Events**: Startup/shutdown

### Remediation Actions
- **High CPU**: Process termination simulation, temp cleanup
- **High Disk**: Temp file cleanup, log rotation
- **High Memory**: Garbage collection, cache clearing

### Extending EriBot
- Add new remediation actions in `RemediationService.cs`
- Create custom monitoring checks in `SystemMonitor`
- Add new alert types in `SlackClient`

## 🔒 Security Notes

- **Bot Token**: Keep secure, rotate regularly
- **Service Account**: Run with minimal privileges
- **Network**: Consider firewall rules for port 5001
- **Logs**: May contain sensitive system information
- **Remediation**: Currently simulated for safety

## 🆘 Support

If you encounter issues:
1. Check logs for error messages
2. Verify configuration files
3. Test individual components
4. Check network connectivity
5. Review Slack permissions

For additional help, check the project documentation or create an issue.