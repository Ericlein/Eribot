using EriBot.Remediator.Services;
using System.Diagnostics;

namespace EriBot.Remediator.Services;

/// <summary>
/// Implementation of health check services
/// </summary>
public class HealthService : IHealthService
{
    private readonly ILogger<HealthService> _logger;
    private readonly DateTime _startTime;
    private static long _requestCount = 0;
    private static long _successfulRequests = 0;
    private static long _failedRequests = 0;

    public HealthService(ILogger<HealthService> logger)
    {
        _logger = logger;
        _startTime = DateTime.UtcNow;
    }

    public Task<HealthCheckResult> CheckHealthAsync()
    {
        var startTime = DateTime.UtcNow;
        var stopwatch = Stopwatch.StartNew();

        try
        {
            var data = new Dictionary<string, object>();

            // Check basic system health
            var memoryUsage = GC.GetTotalMemory(false);
            data["memory_usage_bytes"] = memoryUsage;
            data["gc_collections"] = new
            {
                gen0 = GC.CollectionCount(0),
                gen1 = GC.CollectionCount(1),
                gen2 = GC.CollectionCount(2)
            };

            // Check if we can access file system
            try
            {
                var tempFile = Path.GetTempFileName();
                File.WriteAllText(tempFile, "health_check");
                File.Delete(tempFile);
                data["filesystem_access"] = true;
            }
            catch
            {
                data["filesystem_access"] = false;
            }

            stopwatch.Stop();

            var result = new HealthCheckResult
            {
                IsHealthy = true,
                Status = "healthy",
                CheckedAt = startTime,
                Duration = stopwatch.Elapsed,
                Data = data
            };

            return Task.FromResult(result);
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Health check failed");

            var result = new HealthCheckResult
            {
                IsHealthy = false,
                Status = $"unhealthy: {ex.Message}",
                CheckedAt = startTime,
                Duration = stopwatch.Elapsed,
                Data = new Dictionary<string, object> { ["error"] = ex.Message }
            };

            return Task.FromResult(result);
        }
    }

    public async Task<DetailedHealthStatus> GetDetailedHealthAsync()
    {
        try
        {
            var uptime = DateTime.UtcNow - _startTime;
            var components = new Dictionary<string, ComponentHealth>();

            // System component
            components["system"] = await CheckSystemComponentAsync();

            // Memory component
            components["memory"] = await CheckMemoryComponentAsync();

            // Disk component
            components["disk"] = await CheckDiskComponentAsync();

            // Service metrics
            var metrics = await GetMetricsAsync();

            var overallHealthy = components.Values.All(c => c.IsHealthy);

            return new DetailedHealthStatus
            {
                OverallStatus = overallHealthy ? "healthy" : "degraded",
                Timestamp = DateTime.UtcNow,
                Uptime = uptime,
                Version = "1.0.0",
                Components = components,
                Metrics = metrics
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Detailed health check failed");
            
            return new DetailedHealthStatus
            {
                OverallStatus = "unhealthy",
                Timestamp = DateTime.UtcNow,
                Uptime = DateTime.UtcNow - _startTime,
                Components = new Dictionary<string, ComponentHealth>
                {
                    ["error"] = new ComponentHealth
                    {
                        IsHealthy = false,
                        Status = "error",
                        ErrorMessage = ex.Message
                    }
                }
            };
        }
    }

    public async Task<Dictionary<string, DependencyStatus>> CheckDependenciesAsync()
    {
        var dependencies = new Dictionary<string, DependencyStatus>();

        // Check file system dependency
        dependencies["filesystem"] = await CheckFileSystemDependencyAsync();

        // Check network dependency (optional)
        dependencies["network"] = await CheckNetworkDependencyAsync();

        return dependencies;
    }

    public Task<ServiceMetrics> GetMetricsAsync()
    {
        try
        {
            var uptime = DateTime.UtcNow - _startTime;
            var process = Process.GetCurrentProcess();

            var metrics = new ServiceMetrics
            {
                RequestCount = Interlocked.Read(ref _requestCount),
                SuccessfulRequests = Interlocked.Read(ref _successfulRequests),
                FailedRequests = Interlocked.Read(ref _failedRequests),
                AverageResponseTime = 0, // Would need to track this over time
                MemoryUsageBytes = GC.GetTotalMemory(false),
                CpuUsagePercent = 0, // Would need performance counters
                StartTime = _startTime,
                Uptime = uptime,
                RemediationCounts = new Dictionary<string, long>() // Would be populated by remediation service
            };

            return Task.FromResult(metrics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get metrics");
            var fallbackMetrics = new ServiceMetrics
            {
                StartTime = _startTime,
                Uptime = DateTime.UtcNow - _startTime
            };
            return Task.FromResult(fallbackMetrics);
        }
    }

    private async Task<ComponentHealth> CheckSystemComponentAsync()
    {
        try
        {
            await Task.CompletedTask; // Make it properly async
            
            var metadata = new Dictionary<string, object>
            {
                ["platform"] = Environment.OSVersion.Platform.ToString(),
                ["os_version"] = Environment.OSVersion.VersionString,
                ["processor_count"] = Environment.ProcessorCount,
                ["working_set"] = Environment.WorkingSet
            };

            return new ComponentHealth
            {
                IsHealthy = true,
                Status = "operational",
                LastChecked = DateTime.UtcNow,
                Metadata = metadata
            };
        }
        catch (Exception ex)
        {
            return new ComponentHealth
            {
                IsHealthy = false,
                Status = "failed",
                ErrorMessage = ex.Message,
                LastChecked = DateTime.UtcNow
            };
        }
    }

    private async Task<ComponentHealth> CheckMemoryComponentAsync()
    {
        try
        {
            await Task.CompletedTask; // Make it properly async
            
            var memoryUsage = GC.GetTotalMemory(false);
            var workingSet = Environment.WorkingSet;
            
            // Consider unhealthy if using more than 500MB
            var isHealthy = memoryUsage < 500 * 1024 * 1024;

            var metadata = new Dictionary<string, object>
            {
                ["gc_memory_bytes"] = memoryUsage,
                ["working_set_bytes"] = workingSet,
                ["gc_collections_gen0"] = GC.CollectionCount(0),
                ["gc_collections_gen1"] = GC.CollectionCount(1),
                ["gc_collections_gen2"] = GC.CollectionCount(2)
            };

            return new ComponentHealth
            {
                IsHealthy = isHealthy,
                Status = isHealthy ? "normal" : "high_usage",
                LastChecked = DateTime.UtcNow,
                Metadata = metadata
            };
        }
        catch (Exception ex)
        {
            return new ComponentHealth
            {
                IsHealthy = false,
                Status = "check_failed",
                ErrorMessage = ex.Message,
                LastChecked = DateTime.UtcNow
            };
        }
    }

    private async Task<ComponentHealth> CheckDiskComponentAsync()
    {
        try
        {
            await Task.CompletedTask; // Make it properly async
            
            var currentDir = Directory.GetCurrentDirectory();
            var drive = new DriveInfo(Path.GetPathRoot(currentDir) ?? "C:\\");
            
            var freeSpaceGB = drive.AvailableFreeSpace / (1024.0 * 1024.0 * 1024.0);
            var totalSpaceGB = drive.TotalSize / (1024.0 * 1024.0 * 1024.0);
            var usagePercent = ((totalSpaceGB - freeSpaceGB) / totalSpaceGB) * 100;

            // Consider unhealthy if disk usage > 90%
            var isHealthy = usagePercent < 90;

            var metadata = new Dictionary<string, object>
            {
                ["drive_name"] = drive.Name,
                ["total_space_gb"] = Math.Round(totalSpaceGB, 2),
                ["free_space_gb"] = Math.Round(freeSpaceGB, 2),
                ["usage_percent"] = Math.Round(usagePercent, 2)
            };

            return new ComponentHealth
            {
                IsHealthy = isHealthy,
                Status = isHealthy ? "normal" : "high_usage",
                LastChecked = DateTime.UtcNow,
                Metadata = metadata
            };
        }
        catch (Exception ex)
        {
            return new ComponentHealth
            {
                IsHealthy = false,
                Status = "check_failed",
                ErrorMessage = ex.Message,
                LastChecked = DateTime.UtcNow
            };
        }
    }

    private async Task<DependencyStatus> CheckFileSystemDependencyAsync()
    {
        var startTime = DateTime.UtcNow;
        var stopwatch = Stopwatch.StartNew();

        try
        {
            var tempFile = Path.GetTempFileName();
            await File.WriteAllTextAsync(tempFile, "dependency_check");
            var content = await File.ReadAllTextAsync(tempFile);
            File.Delete(tempFile);

            stopwatch.Stop();

            return new DependencyStatus
            {
                Name = "filesystem",
                IsAvailable = content == "dependency_check",
                Status = "available",
                ResponseTime = stopwatch.Elapsed,
                CheckedAt = startTime
            };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();

            return new DependencyStatus
            {
                Name = "filesystem",
                IsAvailable = false,
                Status = "unavailable",
                ResponseTime = stopwatch.Elapsed,
                ErrorMessage = ex.Message,
                CheckedAt = startTime
            };
        }
    }

    private async Task<DependencyStatus> CheckNetworkDependencyAsync()
    {
        var startTime = DateTime.UtcNow;
        var stopwatch = Stopwatch.StartNew();

        try
        {
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(5);
            
            // Simple check - just verify we can resolve DNS
            var response = await client.GetAsync("https://www.google.com");
            
            stopwatch.Stop();

            return new DependencyStatus
            {
                Name = "network",
                IsAvailable = response.IsSuccessStatusCode,
                Status = response.IsSuccessStatusCode ? "available" : "degraded",
                ResponseTime = stopwatch.Elapsed,
                CheckedAt = startTime
            };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();

            return new DependencyStatus
            {
                Name = "network",
                IsAvailable = false,
                Status = "unavailable",
                ResponseTime = stopwatch.Elapsed,
                ErrorMessage = ex.Message,
                CheckedAt = startTime
            };
        }
    }

    // Static methods to track metrics
    public static void IncrementRequestCount() => Interlocked.Increment(ref _requestCount);
    public static void IncrementSuccessCount() => Interlocked.Increment(ref _successfulRequests);
    public static void IncrementFailureCount() => Interlocked.Increment(ref _failedRequests);
}