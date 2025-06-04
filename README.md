# EriBot 🛠️

[![CI](https://github.com/Ericlein/monitor-slackbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Ericlein/monitor-slackbot/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python + C# hybrid DevOps bot that monitors systems and talks to Slack.

## Overview

EriBot is a monitoring system that consists of two main components:
- A Python-based monitoring service that watches system metrics and reports to Slack
- A C# remediation service that can automatically fix common issues

## Features

- System monitoring (CPU, disk usage)
- Slack notifications for system alerts
- Automated remediation capabilities:
  - Service restarts for high CPU usage
  - Temp file cleanup for disk space issues

## Prerequisites

- Python 3.10+
- .NET 7.0+ (8.0+ Recommended)
- Docker (optional)
- Slack workspace with bot token

## Configuration

1. Create a `.env` file with your Slack credentials:
```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL=#your-channel
```

2. Update `python_monitor/config.yaml` with your monitoring preferences.

## Running the Application

### Docker (Recommended)

```bash
# Start the Python monitor
docker build -f docker/Dockerfile.python -t eribot-monitor .
docker run eribot-monitor

# Start the C# remediator
docker build -f docker/Dockerfile.csharp -t eribot-remediator .
docker run -p 5001:5001 eribot-remediator
```

### Local Development

```bash
# Start the Python monitor
cd python_monitor
pip install -r requirements.txt
python monitory.py

# Start the C# remediator
cd csharp_remediator
dotnet run
```

## Development

- Python monitor runs on default port 5000
- C# remediator service runs on port 5001
- Tests can be run using pytest for Python and dotnet test for C#

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
