namespace EriBot.Remediator.Services;

/// <summary>
/// Interface for health check services
/// </summary>
public interface IHealthService
{
    /// <summary>
    /// Check if the service is healthy
    /// </summary>
    /// <returns>Health check result</returns>
    Task<HealthCheckResult> CheckHealthAsync();

    /// <summary>
    /// Get detailed health information
    /// </summary>
    /// <returns>Detailed health status</returns>
    Task<DetailedHealthStatus> GetDetailedHealthAsync();

    /// <summary>
    /// Check if external dependencies are available
    /// </summary>
    /// <returns>Dependency check results</returns>
    Task<Dictionary<string, DependencyStatus>> CheckDependenciesAsync();

    /// <summary>
    /// Get service metrics
    /// </summary>
    /// <returns>Service metrics</returns>
    Task<ServiceMetrics> GetMetricsAsync();
}

/// <summary>
/// Health check result
/// </summary>
public record HealthCheckResult
{
    public bool IsHealthy { get; init; }
    public string Status { get; init; } = string.Empty;
    public DateTime CheckedAt { get; init; } = DateTime.UtcNow;
    public TimeSpan Duration { get; init; }
    public Dictionary<string, object> Data { get; init; } = new();
}

/// <summary>
/// Detailed health status
/// </summary>
public record DetailedHealthStatus
{
    public string OverallStatus { get; init; } = string.Empty;
    public DateTime Timestamp { get; init; } = DateTime.UtcNow;
    public TimeSpan Uptime { get; init; }
    public string Version { get; init; } = "1.0.0";
    public Dictionary<string, ComponentHealth> Components { get; init; } = new();
    public ServiceMetrics Metrics { get; init; } = new();
}

/// <summary>
/// Component health status
/// </summary>
public record ComponentHealth
{
    public bool IsHealthy { get; init; }
    public string Status { get; init; } = string.Empty;
    public string? ErrorMessage { get; init; }
    public DateTime LastChecked { get; init; } = DateTime.UtcNow;
    public Dictionary<string, object> Metadata { get; init; } = new();
}

/// <summary>
/// Dependency status
/// </summary>
public record DependencyStatus
{
    public string Name { get; init; } = string.Empty;
    public bool IsAvailable { get; init; }
    public string Status { get; init; } = string.Empty;
    public TimeSpan ResponseTime { get; init; }
    public string? ErrorMessage { get; init; }
    public DateTime CheckedAt { get; init; } = DateTime.UtcNow;
}

/// <summary>
/// Service metrics
/// </summary>
public record ServiceMetrics
{
    public long RequestCount { get; init; }
    public long SuccessfulRequests { get; init; }
    public long FailedRequests { get; init; }
    public double AverageResponseTime { get; init; }
    public long MemoryUsageBytes { get; init; }
    public double CpuUsagePercent { get; init; }
    public DateTime StartTime { get; init; }
    public TimeSpan Uptime { get; init; }
    public Dictionary<string, long> RemediationCounts { get; init; } = new();
}