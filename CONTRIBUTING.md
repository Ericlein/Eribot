# Contributing to EriBot 🤝

Thank you for your interest in contributing to EriBot! This guide will help you get started with contributing to our system monitoring and auto-remediation project.

## 🌟 Ways to Contribute

- 🐛 **Bug Reports**: Help us identify and fix issues
- ✨ **Feature Requests**: Suggest new functionality
- 📝 **Documentation**: Improve guides, examples, and API docs
- 🧪 **Testing**: Add test coverage and improve test quality
- 🔧 **Code**: Fix bugs, implement features, optimize performance
- 🎨 **UX/UI**: Improve user experience and interface design
- 🔒 **Security**: Identify vulnerabilities and improve security

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** with pip
- **.NET 8.0+ SDK**
- **Git** for version control
- **Docker** (optional, for testing)
- **Basic knowledge** of system monitoring concepts

### Development Setup

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/YOUR-USERNAME/eribot.git
   cd eribot
   ```

2. **Set Up Python Environment**
   ```bash
   cd python_monitor
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install pytest pytest-cov black flake8 mypy pre-commit
   ```

3. **Set Up C# Environment**
   ```bash
   cd ../csharp_remediator
   dotnet restore
   dotnet build
   ```

4. **Install Pre-commit Hooks**
   ```bash
   cd ..
   pre-commit install
   ```

5. **Set Up Test Environment**
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit .env with test values (you can use fake tokens for most development)
   # SLACK_BOT_TOKEN=xoxb-test-token-for-development
   ```

### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make Your Changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Run Python tests
   cd python_monitor
   pytest tests/ -v --cov=.
   
   # Run C# tests
   cd ../csharp_remediator
   dotnet test
   
   # Run integration tests (optional)
   pytest tests/ --run-integration
   ```

4. **Format Code**
   ```bash
   # Python formatting
   black python_monitor/
   flake8 python_monitor/
   
   # C# formatting
   dotnet format csharp_remediator/
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new monitoring feature"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to GitHub and create a pull request
   - Fill out the PR template
   - Wait for review and CI checks

## 📝 Development Guidelines

### Code Style

#### Python (PEP 8 + Black)
```python
# ✅ Good
def check_system_health(threshold: float = 90.0) -> HealthStatus:
    """Check if system is healthy based on CPU usage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    
    if cpu_percent > threshold:
        return HealthStatus(
            is_healthy=False,
            message=f"High CPU usage: {cpu_percent}%"
        )
    
    return HealthStatus(is_healthy=True, message="System healthy")

# ❌ Bad
def checkSystemHealth(threshold=90):
    cpu=psutil.cpu_percent()
    if cpu>threshold:
        return {"healthy":False,"msg":"high cpu"}
    return {"healthy":True}
```

#### C# (Microsoft .NET Conventions)
```csharp
// ✅ Good
public async Task<RemediationResult> ExecuteRemediationAsync(RemediationRequest request)
{
    var stopwatch = Stopwatch.StartNew();
    
    try
    {
        var result = request.IssueType.ToLower() switch
        {
            "high_cpu" => await RemediateHighCpuAsync(request),
            "high_disk" => await RemediateHighDiskAsync(request),
            _ => RemediationResult.CreateFailure($"Unknown issue type: {request.IssueType}")
        };
        
        stopwatch.Stop();
        return result with { ExecutionTimeMs = stopwatch.ElapsedMilliseconds };
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Remediation failed for {IssueType}", request.IssueType);
        return RemediationResult.CreateFailure(ex.Message);
    }
}

// ❌ Bad
public RemediationResult ExecuteRemediation(RemediationRequest req) {
    if(req.IssueType=="high_cpu") return new RemediationResult{Success=true};
    return new RemediationResult{Success=false};
}
```

### Testing Guidelines

#### Unit Tests
```python
# ✅ Good unit test
def test_validate_slack_token_valid():
    """Test that valid Slack tokens pass validation."""
    valid_token = "xoxb-123456789-123456789-abcdefghijklmnopqrstuvwx"
    
    result = validate_slack_token(valid_token)
    
    assert result is True

def test_validate_slack_token_invalid_format():
    """Test that invalid token format raises ValidationError."""
    invalid_token = "invalid-token-format"
    
    with pytest.raises(ValidationError, match="Invalid Slack token format"):
        validate_slack_token(invalid_token)
```

#### Integration Tests
```python
# ✅ Good integration test
@pytest.mark.integration
def test_end_to_end_monitoring_flow(mock_slack_client):
    """Test complete monitoring workflow."""
    # Arrange
    config = create_test_config()
    monitor = SystemMonitor(config)
    
    # Act
    with patch('psutil.cpu_percent', return_value=95.0):
        result = monitor.check_system()
    
    # Assert
    assert result.alerts_triggered > 0
    mock_slack_client.send_message.assert_called()
```

### Documentation Guidelines

#### Code Documentation
```python
def trigger_remediation(self, issue_type: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Trigger remediation for a specific issue type.
    
    Args:
        issue_type: Type of issue ('high_cpu', 'high_disk', etc.)
        context: Additional context information about the issue
        
    Returns:
        bool: True if remediation was triggered successfully
        
    Raises:
        RemediationError: If remediation fails or service is unavailable
        ValidationError: If issue_type is not supported
        
    Example:
        >>> client = RemediationClient(config)
        >>> success = client.trigger_remediation("high_cpu", {"cpu_percent": 95.0})
        >>> print(f"Remediation triggered: {success}")
        Remediation triggered: True
    """
```

#### README Updates
When adding new features, update:
- Feature list in README.md
- Configuration examples
- Usage examples
- API documentation

## 🧪 Testing

### Test Categories

#### Unit Tests (Fast, No External Dependencies)
```bash
# Run only unit tests
pytest tests/ -m "unit" -v

# With coverage
pytest tests/ -m "unit" --cov=. --cov-report=html
```

#### Integration Tests (Require External Services)
```bash
# Run integration tests (requires real Slack token)
pytest tests/ -m "integration" --run-integration
```

#### Security Tests
```bash
# Run security scans
bandit -r python_monitor/
safety check
```

### Test Data and Mocking

#### Good Test Practices
```python
@pytest.fixture
def mock_psutil_healthy():
    """Mock psutil with healthy system metrics."""
    with patch('psutil.cpu_percent', return_value=45.0), \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk:
        
        mock_memory.return_value.percent = 60.0
        mock_disk.return_value.percent = 70.0
        
        yield

def test_system_health_check_healthy(mock_psutil_healthy):
    """Test system health check with healthy metrics."""
    checker = SystemHealthChecker()
    
    result = checker.check_system_health()
    
    assert result.is_healthy is True
    assert "healthy" in result.status
```

### Test Environment Setup

#### Environment Variables for Testing
```bash
# .env.test
SLACK_BOT_TOKEN=xoxb-test-token-123456789-123456789-abcdefghijklmnopqrstuvwx
SLACK_CHANNEL=#test-alerts
CPU_THRESHOLD=95
DISK_THRESHOLD=95
REMEDIATOR_URL=http://localhost:5001
LOG_LEVEL=DEBUG
```

## 🐛 Bug Reports

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to ensure the bug still exists
3. **Gather system information**:
   ```bash
   # System info
   python --version
   dotnet --version
   docker --version
   
   # OS info
   uname -a        # Linux/macOS
   systeminfo      # Windows
   ```

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Set configuration to '...'
2. Run command '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 13]
- Python Version: [e.g., 3.11.2]
- .NET Version: [e.g., 8.0.1]
- Docker Version: [e.g., 24.0.5] (if using Docker)

**Configuration**
```yaml
# Relevant parts of your config (mask sensitive data)
monitoring:
  cpu_threshold: 90
```

**Logs**
```
# Relevant log output (mask sensitive data)
```

**Additional Context**
Any other context about the problem.
```

## ✨ Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How would you like this feature to work?

**Alternatives Considered**
What other solutions have you considered?

**Use Cases**
- Use case 1: ...
- Use case 2: ...

**Implementation Ideas**
Any ideas on how this could be implemented?

**Additional Context**
Screenshots, mockups, or examples.
```

## 🔄 Pull Request Process

### PR Checklist

Before submitting your PR, ensure:

- [ ] **Code Quality**
  - [ ] Code follows style guidelines
  - [ ] No linting errors
  - [ ] Type hints added (Python)
  - [ ] XML documentation (C#)

- [ ] **Testing**
  - [ ] New features have tests
  - [ ] All tests pass
  - [ ] Test coverage maintained/improved
  - [ ] Integration tests added if needed

- [ ] **Documentation**
  - [ ] Code is documented
  - [ ] README updated if needed
  - [ ] API docs updated
  - [ ] Configuration examples updated

- [ ] **Security**
  - [ ] No secrets in code
  - [ ] Input validation added
  - [ ] Security implications considered

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] All tests pass

## Screenshots/Demo
(If applicable)

## Related Issues
Fixes #123
```

### Review Process

1. **Automated Checks**: CI must pass
2. **Code Review**: At least one maintainer review
3. **Testing**: Reviewers test the changes
4. **Documentation**: Ensure docs are updated
5. **Merge**: Squash and merge preferred

## 🏷️ Commit Guidelines

### Conventional Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>[optional scope]: <description>

# Examples
feat: add CPU temperature monitoring
fix: resolve Slack rate limiting issue
docs: update installation guide
test: add unit tests for config validation
refactor: simplify remediation service architecture
perf: optimize system metrics collection
ci: add security scanning workflow
```

### Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code changes that neither fix bugs nor add features
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **ci**: CI/CD changes
- **chore**: Maintenance tasks

## 🏆 Recognition

### Contributors

We recognize contributors in:
- **README.md**: Contributors section
- **Release Notes**: Major contributions highlighted
- **GitHub**: Contributor role assignment

### Types of Recognition

- **Code Contributors**: Bug fixes, features, optimizations
- **Documentation Contributors**: Guides, examples, API docs
- **Community Contributors**: Issue triage, user support
- **Security Contributors**: Vulnerability reports, security improvements

## 📞 Getting Help

### Community Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community chat
- **Pull Request Comments**: Code-specific discussions

### Maintainer Contact

- **@Ericlein**: Project maintainer
- **Email**: eric@ericklein.se
- **Response Time**: Usually within 48 hours

### Development Questions

For development-specific questions:
1. Check existing issues and discussions
2. Create a GitHub discussion
3. Tag relevant maintainers
4. Provide context and code examples

## 🎯 Project Roadmap

### Current Priorities

1. **Enhanced Monitoring**: More system metrics and health checks
2. **Advanced Remediation**: More sophisticated auto-remediation actions
3. **Web Dashboard**: Optional web interface for monitoring
4. **Multi-tenant Support**: Support for monitoring multiple systems
5. **Plugin Architecture**: Extensible plugin system for custom monitoring

### Future Goals

- **Machine Learning**: Predictive monitoring and anomaly detection
- **Multi-platform**: Better support for macOS and Windows
- **Cloud Integration**: Native support for AWS, Azure, GCP monitoring
- **Mobile Alerts**: Mobile app for critical alerts
- **Integration Hub**: Connectors for popular DevOps tools

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project maintainers. All complaints will be reviewed and investigated promptly and fairly.

---

**Thank you for contributing to EriBot!** Every contribution, no matter how small, helps make system monitoring better for everyone. 🚀