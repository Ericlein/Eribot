# Security Policy 🔒

EriBot takes security seriously. This document outlines our security practices, how to report vulnerabilities, and guidelines for secure deployment.

## 🛡️ Security Overview

### Design Principles

- **Principle of Least Privilege**: Services run with minimal required permissions
- **Defense in Depth**: Multiple layers of security controls
- **Secure by Default**: Security-focused default configurations
- **Transparency**: Open source code for security review

### Architecture Security

```
┌─────────────────┐    HTTP (localhost)    ┌──────────────────────┐
│   Python        │ ───────────────────────▶│   C# Remediation     │
│   Monitor       │                         │   Service            │
│                 │   No auth required      │                      │
│ • Read-only     │   (localhost-only)      │ • Controlled actions │
│ • No secrets    │                         │ • Safety checks      │
│ • Limited scope │                         │ • Audit logging      │
└─────────────────┘                         └──────────────────────┘
         │                                             │
         │ HTTPS + OAuth                               │ Limited system access
         ▼                                             ▼
┌─────────────────┐                         ┌──────────────────────┐
│   Slack API     │                         │   System Resources   │
│                 │                         │                      │
│ • Bot token     │                         │ • Read-only metrics  │
│ • Rate limited  │                         │ • Safe file cleanup  │
│ • Audit trail   │                         │ • Controlled actions │
└─────────────────┘                         └──────────────────────┘
```

## 🔐 Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Yes             |
| 0.x.x   | ❌ No              |

## 🚨 Reporting Security Vulnerabilities

### Responsible Disclosure

If you discover a security vulnerability, please follow responsible disclosure practices:

1. **DO NOT** create a public GitHub issue
2. **DO NOT** discuss the vulnerability in public forums
3. **DO** report privately using one of the methods below

### How to Report

**Email:** security@ericklein.se (if available)

**GitHub Security Advisory:** 
1. Go to the [Security tab](https://github.com/Ericlein/eribot/security)
2. Click "Report a vulnerability"
3. Fill out the private vulnerability report

**Include in your report:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### Response Timeline

- **24 hours**: Initial acknowledgment
- **72 hours**: Preliminary assessment
- **7 days**: Detailed response with timeline
- **30 days**: Security fix released (if applicable)

## 🔒 Security Features

### Authentication & Authorization

#### Slack Integration
- **OAuth Bot Tokens**: Industry-standard authentication
- **Scope Limitation**: Minimal required permissions (`chat:write`)
- **Token Rotation**: Support for regular token updates
- **Rate Limiting**: Built-in Slack API rate limit compliance

#### Service Communication
- **Local-only**: HTTP communication restricted to localhost
- **No Authentication**: Internal services don't require auth (localhost assumption)
- **Process Isolation**: Services run in separate processes/containers

### Data Protection

#### Sensitive Information Handling
```python
# ✅ Good: Tokens masked in logs
logger.info(f"Using Slack token: {token[:10]}...")

# ❌ Bad: Token exposed
logger.info(f"Using Slack token: {token}")
```

#### Configuration Security
- **Environment Variables**: Secrets stored in environment, not files
- **File Permissions**: Configuration files have restricted permissions (600)
- **No Default Secrets**: No hardcoded credentials in code

#### Logging Security
- **Sanitized Logs**: Sensitive data automatically masked
- **Log Rotation**: Prevents log files from growing indefinitely
- **Access Control**: Log files protected with appropriate permissions

### Input Validation

#### Configuration Validation
```python
# Slack token format validation
if not token.startswith('xoxb-'):
    raise ValidationError("Invalid Slack token format")

# Threshold range validation  
if not (0 <= threshold <= 100):
    raise ValidationError("Threshold must be between 0-100")

# URL validation
parsed = urlparse(url)
if parsed.scheme not in ['http', 'https']:
    raise ValidationError("Invalid URL scheme")
```

#### API Input Validation
```csharp
[Required]
[JsonPropertyName("issueType")]
public required string IssueType { get; init; }

[Range(1, 10)]
[JsonPropertyName("priority")]
public int Priority { get; init; } = 5;
```

### Remediation Safety

#### Safe Actions Only
All potentially destructive actions are **simulated by default**:

```csharp
// ✅ Safe: Simulated process termination
private async Task<string> SimulateProcessTerminationLinux()
{
    await Task.Delay(500);
    return "High CPU processes identified and terminated (simulated)";
}

// ✅ Safe: Actual file cleanup with safety checks
private async Task<string> ClearTempFilesAsync()
{
    var cutoffTime = DateTime.Now.AddDays(-1); // Only old files
    // ... safe implementation
}
```

#### Action Whitelisting
```yaml
# Only explicitly allowed actions can be executed
EriBot:
  Remediation:
    AllowedActions:
      - "high_cpu"
      - "high_disk" 
      - "high_memory"
      - "service_restart"
```

#### Audit Trail
Every action is logged with:
- Timestamp
- Action type
- Initiating condition
- Execution result
- Duration
- System context

## 🏗️ Secure Deployment

### Environment Security

#### Production Environment Variables
```bash
# Required
SLACK_BOT_TOKEN=xoxb-xxx                # Store securely, rotate regularly

# Security settings
ASPNETCORE_ENVIRONMENT=Production       # Disable debug features
LOG_LEVEL=WARNING                       # Reduce log verbosity
ENABLE_SIMULATION_MODE=true             # Keep destructive actions simulated

# Network security
ASPNETCORE_URLS=http://127.0.0.1:5001   # Bind to localhost only
REMEDIATOR_URL=http://127.0.0.1:5001    # Internal communication only
```

#### File Permissions
```bash
# Configuration files
chmod 600 config/.env
chmod 644 config/config.yaml

# Application directories
chmod 755 /opt/eribot
chown -R eribot:eribot /opt/eribot

# Log files
chmod 640 logs/*.log
chown eribot:syslog logs/
```

### Network Security

#### Firewall Configuration
```bash
# Allow only necessary ports
# Remediation service (localhost only)
iptables -A INPUT -i lo -p tcp --dport 5001 -j ACCEPT
iptables -A INPUT -p tcp --dport 5001 -j REJECT

# SSH for management (if needed)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Outbound HTTPS for Slack API
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
```

#### Container Security
```yaml
# docker-compose.yml security settings
services:
  eribot-remediator:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
```

### Service Security

#### User Accounts
```bash
# Create dedicated service user
useradd -r -s /bin/false -d /opt/eribot eribot

# Service runs as non-root
User=eribot
Group=eribot
NoNewPrivileges=true
```

#### Process Isolation
```ini
# systemd service security
[Service]
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/eribot/logs
NoNewPrivileges=true
```

## 🔍 Security Monitoring

### Automated Security Scanning

Our CI/CD pipeline includes:

#### Static Analysis
- **Bandit**: Python security linter
- **CodeQL**: Semantic code analysis
- **Semgrep**: Multi-language static analysis

#### Dependency Scanning  
- **Safety**: Python package vulnerability scanner
- **pip-audit**: Python dependency auditing
- **Trivy**: Container vulnerability scanner

#### Secrets Detection
- **TruffleHog**: Git history secret scanning
- **GitHub Secret Scanning**: Automatic token detection

### Security Metrics

Monitor these security indicators:

```bash
# Failed authentication attempts
grep "Slack API error" logs/monitor.log | wc -l

# Unusual remediation requests
grep "Unexpected error" logs/remediator.log

# Resource access failures
grep "Permission denied" logs/*.log

# Rate limiting triggers
grep "rate limit" logs/*.log
```

### Incident Response

#### Security Event Types
1. **Authentication Failures**: Invalid Slack tokens, API errors
2. **Unauthorized Access**: Attempts to access restricted endpoints
3. **Privilege Escalation**: Unexpected system access attempts
4. **Data Exfiltration**: Unusual outbound network traffic

#### Response Procedures
1. **Detect**: Automated alerting on security events
2. **Contain**: Isolate affected services
3. **Investigate**: Analyze logs and system state
4. **Remediate**: Apply fixes and security patches
5. **Recover**: Restore normal operations
6. **Learn**: Update procedures and security controls

## 🔧 Security Configuration

### Hardening Checklist

#### ✅ System Level
- [ ] Services run as non-root users
- [ ] File permissions properly configured
- [ ] Firewall rules restrict network access
- [ ] System packages kept up to date
- [ ] Logging and monitoring enabled

#### ✅ Application Level
- [ ] Input validation on all external inputs
- [ ] Sensitive data properly masked in logs
- [ ] Error messages don't expose internal details
- [ ] Rate limiting implemented
- [ ] Secure defaults used for all configuration

#### ✅ Deployment Level
- [ ] Environment variables used for secrets
- [ ] No hardcoded credentials in code
- [ ] Container images regularly updated
- [ ] Security scanning integrated in CI/CD
- [ ] Access controls implemented

### Security Headers

For web interfaces (if added):

```csharp
// Security headers
app.Use(async (context, next) =>
{
    context.Response.Headers.Add("X-Frame-Options", "DENY");
    context.Response.Headers.Add("X-Content-Type-Options", "nosniff");
    context.Response.Headers.Add("X-XSS-Protection", "1; mode=block");
    context.Response.Headers.Add("Referrer-Policy", "strict-origin-when-cross-origin");
    await next();
});
```

## 🎯 Security Best Practices

### For Administrators

#### Token Management
```bash
# Generate strong Slack bot tokens
# Rotate tokens every 90 days
# Use different tokens for different environments
# Store tokens in secure secret management systems

# Monitor token usage
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
     https://slack.com/api/auth.test
```

#### Access Control
```bash
# Principle of least privilege
# Regular access reviews
# Multi-factor authentication for admin accounts
# Audit trails for all administrative actions
```

#### Monitoring
```bash
# Set up security alerting
# Monitor for unusual patterns
# Regular security assessments
# Automated vulnerability scanning
```

### For Developers

#### Secure Coding
```python
# ✅ Good: Input validation
def validate_threshold(value):
    if not isinstance(value, (int, float)):
        raise ValidationError("Threshold must be numeric")
    if not 0 <= value <= 100:
        raise ValidationError("Threshold must be 0-100")
    return value

# ✅ Good: Error handling
try:
    response = requests.post(url, json=data, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error("Request failed: %s", str(e))
    # Don't expose internal details
    raise RemediationError("External service unavailable")
```

#### Secret Management
```python
# ✅ Good: Environment variables
SLACK_TOKEN = os.getenv('SLACK_BOT_TOKEN')
if not SLACK_TOKEN:
    raise ConfigurationError("SLACK_BOT_TOKEN not set")

# ✅ Good: Masked logging
logger.info("Connecting to Slack with token: %s***", SLACK_TOKEN[:10])

# ❌ Bad: Hardcoded secrets
SLACK_TOKEN = "xoxb-123456789-abcdef"  # Never do this!
```

## 📋 Security Audit

### Regular Security Tasks

#### Monthly
- [ ] Review access logs
- [ ] Update dependencies
- [ ] Check for new CVEs
- [ ] Rotate Slack tokens
- [ ] Review firewall rules

#### Quarterly  
- [ ] Security scan of infrastructure
- [ ] Review and update security policies
- [ ] Penetration testing (if applicable)
- [ ] Security training for team
- [ ] Incident response plan testing

#### Annually
- [ ] Comprehensive security audit
- [ ] Third-party security assessment
- [ ] Update disaster recovery plans
- [ ] Review and update access controls
- [ ] Security policy review

### Compliance Considerations

#### Data Protection
- **GDPR**: Minimal data collection, right to deletion
- **CCPA**: Data transparency and user rights
- **SOX**: Audit trails and access controls (if applicable)

#### Industry Standards
- **NIST Cybersecurity Framework**: Risk management approach
- **ISO 27001**: Information security management
- **CIS Controls**: Cybersecurity best practices

## 🔗 Security Resources

### Tools and References
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Slack Security Best Practices](https://slack.com/help/articles/115004930943)

### Security Training
- Regular security awareness training
- Secure coding practices
- Incident response procedures
- Threat modeling workshops

## 📞 Security Contact

For security-related questions or concerns:

- **Security Email**: security@ericklein.se
- **GitHub Security**: Use private vulnerability reporting
- **Emergency**: Create a private GitHub issue and tag @Ericlein

---

**Remember**: Security is everyone's responsibility. When in doubt, choose the more secure option.