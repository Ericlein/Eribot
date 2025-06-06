# EriBot 🤖

[![CI](https://github.com/Ericlein/monitor-slackbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Ericlein/monitor-slackbot/actions)
[![CD](https://github.com/Ericlein/monitor-slackbot/actions/workflows/cd.yml/badge.svg)](https://github.com/Ericlein/monitor-slackbot/actions)
[![Security](https://github.com/Ericlein/Eribot/actions/workflows/security.yml/badge.svg)](https://github.com/Ericlein/Eribot/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**EriBot** is a hybrid Python + C# DevOps monitoring and auto-remediation system that watches your infrastructure and intelligently responds to issues while keeping your team informed via Slack.

## 🌟 Features

### 🔍 **Intelligent Monitoring**
- **System Metrics**: CPU, memory, disk usage monitoring with configurable thresholds
- **Health Checks**: Comprehensive service and dependency health monitoring
- **Real-time Alerts**: Instant Slack notifications when issues are detected
- **Cross-platform**: Works on Windows, Linux, and macOS

### 🛠️ **Automated Remediation**
- **Smart Actions**: Automatically fix common issues (high CPU, disk cleanup, memory optimization)
- **Safe Execution**: All remediation actions are carefully simulated for safety
- **Configurable**: Enable/disable specific remediation actions
- **Audit Trail**: Complete logging of all remediation activities

### 📱 **Slack Integration**
- **Rich Notifications**: Formatted alerts with system context and severity levels
- **Real-time Updates**: Immediate notifications when remediation actions are taken
- **Channel Routing**: Send different alert types to different channels
- **Bot Authentication**: Secure OAuth bot token integration

### 🏗️ **Enterprise Ready**
- **Multi-deployment**: Docker, systemd services, Windows services, or manual deployment
- **Scalable Architecture**: Microservices design with Python monitoring + C# remediation service
- **Security First**: No hardcoded secrets, environment-based configuration
- **Production Tested**: Comprehensive test suite with unit and integration tests

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** with pip
- **.NET 8.0+ SDK**
- **Slack Bot Token** ([Get one here](https://api.slack.com/apps))
- **Docker** (optional, for containerized deployment)

### ⚡ One-Line Install

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/Ericlein/eribot/main/scripts/install.sh | sudo bash -s -- "xoxb-your-slack-token-here" --service
```

**Windows (PowerShell as Administrator):**
```powershell
irm https://raw.githubusercontent.com/Ericlein/eribot/main/scripts/install.ps1 | iex -SlackToken "xoxb-your-slack-token-here" -InstallAsService
```

**Docker Compose:**
```bash
# Create .env file
echo "SLACK_BOT_TOKEN=xoxb-your-token-here" > .env
echo "SLACK_CHANNEL=#devops-alerts" >> .env

# Start services
docker-compose up -d
```

### 🔧 Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ericlein/eribot.git
   cd eribot
   ```

2. **Set up Python monitoring service:**
   ```bash
   cd python_monitor
   pip install -r requirements.txt
   ```

3. **Build C# remediation service:**
   ```bash
   cd ../csharp_remediator
   dotnet build --configuration Release
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Slack token and preferences
   ```

5. **Start services:**
   ```bash
   # Terminal 1: Start remediation service
   cd csharp_remediator
   dotnet run

   # Terminal 2: Start monitoring service
   cd python_monitor
   python monitor.py
   ```

## 📋 Configuration

### Environment Variables
```bash
# Required
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# Optional (with defaults)
SLACK_CHANNEL=#devops-alerts
CPU_THRESHOLD=90
MEMORY_THRESHOLD=90
DISK_THRESHOLD=90
CHECK_INTERVAL=60
REMEDIATOR_URL=http://localhost:5001
LOG_LEVEL=INFO
```

### Configuration File (`config/config.yaml`)
```yaml
monitoring:
  cpu_threshold: 90      # CPU % threshold to trigger alerts
  disk_threshold: 90     # Disk % threshold to trigger alerts  
  memory_threshold: 90   # Memory % threshold to trigger alerts
  check_interval: 60     # Check frequency in seconds

slack:
  channel: "#devops-alerts"
  username: "EriBot"
  icon_emoji: ":robot_face:"

remediator:
  url: "http://localhost:5001"
  timeout: 30
  retry_attempts: 3

logging:
  level: "INFO"
  max_file_size: "10MB"
  backup_count: 5
```

## 🏗️ Architecture

```
┌─────────────────┐    HTTP/REST    ┌──────────────────────┐
│   Python        │ ───────────────▶│   C# Remediation     │
│   Monitor       │                 │   Service            │
│                 │                 │                      │
│ • System Stats  │                 │ • REST API           │
│ • Health Checks │                 │ • Action Execution   │
│ • Slack Alerts  │                 │ • Safety Controls    │
└─────────────────┘                 └──────────────────────┘
         │                                     │
         │                                     │
         ▼                                     ▼
┌─────────────────┐                 ┌──────────────────────┐
│   Slack API     │                 │   System Resources   │
│                 │                 │                      │
│ • Notifications │                 │ • Process Management │
│ • Rich Messages │                 │ • File Cleanup       │
│ • Bot Identity  │                 │ • Service Restarts   │
└─────────────────┘                 └──────────────────────┘
```

### Key Components

- **Python Monitor** (`python_monitor/`): Lightweight system monitoring with Slack integration
- **C# Remediator** (`csharp_remediator/`): High-performance remediation service with REST API
- **Configuration** (`config/`): Centralized YAML and environment-based configuration
- **Docker Support** (`docker/`): Multi-architecture container support with health checks

## 🔧 Available Remediation Actions

| Action | Description | Safety Level |
|--------|-------------|--------------|
| **high_cpu** | Terminate high-CPU processes, clean temp files | 🟡 Simulated |
| **high_disk** | Clean temp files, rotate logs, platform-specific cleanup | 🟢 Safe |
| **high_memory** | Force garbage collection, clear system caches | 🟢 Safe |
| **service_restart** | Restart specified services | 🟡 Simulated |

> **Note**: All potentially disruptive actions are currently simulated for safety. Enable production mode via configuration when ready.

## 📊 Monitoring Capabilities

### System Metrics
- **CPU Usage**: Real-time CPU percentage with configurable thresholds
- **Memory Usage**: Physical and virtual memory monitoring
- **Disk Usage**: Disk space monitoring with multi-drive support
- **Network Health**: Connectivity tests to external services

### Service Health
- **Remediation Service**: HTTP health checks and response time monitoring
- **Slack Connectivity**: API authentication and rate limit monitoring
- **Dependency Status**: External service availability checks

### Alert Types
- 🟢 **Info**: System status updates and successful actions
- 🟡 **Warning**: Threshold approaches and minor issues
- 🔴 **Error**: Threshold exceeded and remediation failures
- 🚨 **Critical**: System failures and emergency conditions

## 🐳 Docker Deployment

### Quick Start with Docker Compose
```bash
# Clone and enter project
git clone https://github.com/Ericlein/eribot.git
cd eribot

# Configure environment
cp .env.example .env
# Edit .env with your Slack token

# Start all services
docker-compose up -d

# Include monitoring stack (Grafana + Prometheus)
docker-compose --profile monitoring up -d
```

### Individual Container Deployment
```bash
# Build images
docker build -f docker/Dockerfile.python -t eribot-monitor .
docker build -f docker/Dockerfile.csharp -t eribot-remediator .

# Run remediation service
docker run -d --name eribot-remediator -p 5001:5001 eribot-remediator

# Run monitoring service
docker run -d --name eribot-monitor \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_CHANNEL=#alerts \
  --link eribot-remediator \
  eribot-monitor
```

## 🔒 Security Considerations

### Authentication & Authorization
- **Slack Bot Tokens**: Store securely using environment variables
- **Service Communication**: HTTP-only on localhost by default
- **User Permissions**: Run services with minimal required privileges

### Data Protection
- **No Sensitive Logging**: Tokens and secrets are masked in logs
- **Secure Defaults**: All configuration defaults prioritize security
- **Network Isolation**: Services communicate only as needed

### Operational Security
- **Remediation Safety**: Destructive actions are simulated by default
- **Audit Logging**: All actions are logged with timestamps and context
- **Rate Limiting**: Built-in protection against API abuse

## 🧪 Testing

### Run Unit Tests
```bash
cd python_monitor
pytest tests/ -v --cov=. -m "unit"
```

### Run Integration Tests
```bash
# Requires real services running
pytest tests/ -v --run-integration -m "integration"
```

### Run Security Scans
```bash
# GitHub Actions includes automated security scanning
# Manual security scan:
python -m bandit -r python_monitor/
```

## 📖 API Documentation

### Remediation Service Endpoints

**Health Check:**
```http
GET /health
```

**Execute Remediation:**
```http
POST /remediate
Content-Type: application/json

{
  "issueType": "high_cpu",
  "context": {
    "cpu_percent": 95.0
  }
}
```

**Get Available Actions:**
```http
GET /actions
```

**Service Status:**
```http
GET /status
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone repository
git clone https://github.com/Ericlein/eribot.git
cd eribot

# Install development dependencies
pip install -r requirements.txt
pip install pre-commit

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Code Quality Standards
- **Python**: PEP 8 compliance with Black formatting
- **C#**: Microsoft .NET conventions
- **Testing**: Minimum 80% code coverage
- **Security**: Automated security scanning with Bandit and CodeQL

## 🐛 Troubleshooting

### Common Issues

**Slack messages not sending:**
```bash
# Check token format
echo $SLACK_BOT_TOKEN | grep "^xoxb-"

# Test connection
python -c "
from slack_client import test_slack_connection
print(test_slack_connection())
"
```

**High resource usage not triggering:**
```bash
# Check current thresholds
cat config/config.yaml | grep threshold

# Test with lower thresholds temporarily
export CPU_THRESHOLD=50
python monitor.py
```

**Service connection issues:**
```bash
# Check if remediation service is running
curl http://localhost:5001/health

# Check logs
tail -f logs/monitor.log
tail -f logs/remediator.log
```

### Log Locations
- **Docker**: `docker-compose logs -f`
- **Linux Service**: `/opt/eribot/logs/`
- **Windows Service**: `C:\EriBot\logs\`
- **Manual**: `./logs/`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Slack SDK](https://slack.dev/python-slack-sdk/) for Python
- System monitoring powered by [psutil](https://github.com/giampaolo/psutil)
- Cross-platform service capabilities with [.NET 8](https://dotnet.microsoft.com/)

## 📞 Support

- **Documentation**: [Wiki](https://github.com/Ericlein/eribot/wiki)
- **Issues**: [GitHub Issues](https://github.com/Ericlein/eribot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ericlein/eribot/discussions)

---