# EriBot 🛠️

[![CI](https://github.com/Ericlein/monitor-slackbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Ericlein/monitor-slackbot/actions)
[![CD](https://github.com/Ericlein/monitor-slackbot/actions/workflows/cd.yml/badge.svg)](https://github.com/Ericlein/monitor-slackbot/actions)
[![CI](https://github.com/Ericlein/monitor-slackbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Ericlein/monitor-slackbot/actions/workflows/ci.yml)
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
- .NET 8.0+
- Docker (optional)
- Slack workspace with bot token

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
