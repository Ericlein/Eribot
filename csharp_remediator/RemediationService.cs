using EriBot.Remediator.Models;
using EriBot.Remediator.Services;
using System;
using System.IO;
using System.Diagnostics;

namespace EriBot.Remediator.Services;

public class RemediationService : IRemediationService
{
    private readonly ILogger<RemediationService> _logger;
    private readonly bool _isWindows;
    private readonly bool _isLinux;
    private readonly DateTime _startTime;
    private readonly Dictionary<string, long> _remediationCounts;

    public RemediationService(ILogger<RemediationService> logger)
    {
        _logger = logger;
        _isWindows = Environment.OSVersion.Platform == PlatformID.Win32NT;
        _isLinux = Environment.OSVersion.Platform == PlatformID.Unix;
        _startTime = DateTime.UtcNow;
        _remediationCounts = new Dictionary<string, long>();
    }

    public async Task<RemediationResult> ExecuteRemediationAsync(RemediationRequest request)
    {
        var stopwatch = Stopwatch.StartNew();
        
        try
        {
            // Increment counter
            if (_remediationCounts.ContainsKey(request.IssueType))
                _remediationCounts[request.IssueType]++;
            else
                _remediationCounts[request.IssueType] = 1;

            var result = request.IssueType.ToLower() switch
            {
                "high_cpu" => await RemediateHighCpuAsync(request),
                "high_disk" => await RemediateHighDiskAsync(request),
                "high_memory" => await RemediateHighMemoryAsync(request),
                "service_restart" => await RestartServiceAsync(request),
                _ => RemediationResult.CreateFailure($"Unknown issue type: {request.IssueType}")
            };

            stopwatch.Stop();
            return result with { ExecutionTimeMs = stopwatch.ElapsedMilliseconds };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Error executing remediation for {IssueType}", request.IssueType);
            return RemediationResult.CreateFailure(
                $"Remediation failed: {ex.Message}", 
                ex.ToString(), 
                stopwatch.ElapsedMilliseconds
            );
        }
    }

    public bool ValidateRequest(RemediationRequest request)
    {
        try
        {
            // Check if request is null
            if (request == null)
            {
                _logger.LogWarning("Remediation request is null");
                return false;
            }

            // Check if issue type is provided
            if (string.IsNullOrWhiteSpace(request.IssueType))
            {
                _logger.LogWarning("Issue type is required");
                return false;
            }

            // Check if issue type is supported
            var availableActions = GetAvailableActions();
            if (!availableActions.Contains(request.IssueType.ToLower()))
            {
                _logger.LogWarning("Unsupported issue type: {IssueType}", request.IssueType);
                return false;
            }

            // Validate priority range
            if (request.Priority < 1 || request.Priority > 10)
            {
                _logger.LogWarning("Priority must be between 1 and 10, got: {Priority}", request.Priority);
                return false;
            }

            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error validating request");
            return false;
        }
    }

    public Task<object> GetServiceStatusAsync()
    {
        try
        {
            var uptime = DateTime.UtcNow - _startTime;
            
            var status = new
            {
                status = "running",
                platform = Environment.OSVersion.Platform.ToString(),
                osVersion = Environment.OSVersion.VersionString,
                uptimeSeconds = (long)uptime.TotalSeconds,
                uptimeFormatted = uptime.ToString(@"dd\.hh\:mm\:ss"),
                availableActions = GetAvailableActions(),
                remediationCounts = _remediationCounts,
                timestamp = DateTime.UtcNow,
                version = "1.0.0",
                memoryUsage = GC.GetTotalMemory(false)
            };

            return Task.FromResult<object>(status);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting service status");
            var errorStatus = new
            {
                status = "error",
                error = ex.Message,
                timestamp = DateTime.UtcNow
            };
            return Task.FromResult<object>(errorStatus);
        }
    }

    public string[] GetAvailableActions()
    {
        return new[]
        {
            "high_cpu",
            "high_disk", 
            "high_memory",
            "service_restart"
        };
    }

    public Task<long> GetEstimatedExecutionTimeAsync(string issueType)
    {
        // Return estimated execution times in milliseconds
        var estimates = new Dictionary<string, long>
        {
            { "high_cpu", 5000 },        // 5 seconds
            { "high_disk", 15000 },      // 15 seconds
            { "high_memory", 2000 },     // 2 seconds
            { "service_restart", 10000 } // 10 seconds
        };

        var estimatedTime = estimates.GetValueOrDefault(issueType.ToLower(), 5000);
        return Task.FromResult(estimatedTime);
    }

    private async Task<RemediationResult> RemediateHighCpuAsync(RemediationRequest request)
    {
        _logger.LogInformation("Executing high CPU remediation");
        
        try
        {
            var results = new List<string>();
            
            // Kill high CPU processes (simulation for safety)
            if (_isWindows)
            {
                results.Add(await SimulateProcessTerminationWindows());
            }
            else if (_isLinux)
            {
                results.Add(await SimulateProcessTerminationLinux());
            }
            
            // Clear temporary files that might be causing CPU load
            results.Add(await ClearTempFilesAsync());
            
            var message = $"High CPU remediation completed: {string.Join(", ", results)}";
            _logger.LogInformation(message);
            
            return RemediationResult.CreateSuccess(message, results);
        }
        catch (Exception ex)
        {
            var errorMsg = $"High CPU remediation failed: {ex.Message}";
            _logger.LogError(ex, errorMsg);
            return RemediationResult.CreateFailure(errorMsg, ex.ToString());
        }
    }

    private async Task<RemediationResult> RemediateHighDiskAsync(RemediationRequest request)
    {
        _logger.LogInformation("Executing high disk remediation");
        
        try
        {
            var results = new List<string>();
            
            // Clean temporary files
            results.Add(await ClearTempFilesAsync());
            
            // Clean log files older than 30 days
            results.Add(await CleanOldLogFilesAsync());
            
            // Platform-specific cleanup
            if (_isWindows)
            {
                results.Add(await CleanWindowsSpecificAsync());
            }
            else if (_isLinux)
            {
                results.Add(await CleanLinuxSpecificAsync());
            }
            
            var message = $"High disk remediation completed: {string.Join(", ", results)}";
            _logger.LogInformation(message);
            
            return RemediationResult.CreateSuccess(message, results);
        }
        catch (Exception ex)
        {
            var errorMsg = $"High disk remediation failed: {ex.Message}";
            _logger.LogError(ex, errorMsg);
            return RemediationResult.CreateFailure(errorMsg, ex.ToString());
        }
    }

    private async Task<RemediationResult> RemediateHighMemoryAsync(RemediationRequest request)
    {
        _logger.LogInformation("Executing high memory remediation");
        
        try
        {
            var results = new List<string>();
            
            // Force garbage collection
            var beforeGC = GC.GetTotalMemory(false);
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            var afterGC = GC.GetTotalMemory(false);
            var freedBytes = beforeGC - afterGC;
            
            results.Add($"Garbage collection freed {freedBytes / 1024 / 1024} MB");
            
            // Clear system caches (platform-specific)
            if (_isLinux)
            {
                results.Add(await ClearLinuxCachesAsync());
            }
            
            var message = $"High memory remediation completed: {string.Join(", ", results)}";
            _logger.LogInformation(message);
            
            return RemediationResult.CreateSuccess(message, results);
        }
        catch (Exception ex)
        {
            var errorMsg = $"High memory remediation failed: {ex.Message}";
            _logger.LogError(ex, errorMsg);
            return RemediationResult.CreateFailure(errorMsg, ex.ToString());
        }
    }

    private async Task<RemediationResult> RestartServiceAsync(RemediationRequest request)
    {
        _logger.LogInformation("Executing service restart remediation");
        
        try
        {
            // Extract service name from context
            var serviceName = request.Context?.GetValueOrDefault("serviceName")?.ToString() ?? "unknown-service";
            
            // For safety, we'll simulate the restart
            await Task.Delay(1000); // Simulate restart time
            
            var message = $"Service restart simulated for: {serviceName}";
            _logger.LogInformation(message);
            
            return RemediationResult.CreateSuccess(message, new List<string> { $"Simulated restart of {serviceName}" });
        }
        catch (Exception ex)
        {
            var errorMsg = $"Service restart failed: {ex.Message}";
            _logger.LogError(ex, errorMsg);
            return RemediationResult.CreateFailure(errorMsg, ex.ToString());
        }
    }

    // Helper methods (same as before)
    private async Task<string> ClearTempFilesAsync()
    {
        try
        {
            var tempPath = Path.GetTempPath();
            var deletedCount = 0;
            var deletedSize = 0L;
            
            var tempFiles = Directory.GetFiles(tempPath, "*", SearchOption.TopDirectoryOnly)
                .Where(f => File.GetLastWriteTime(f) < DateTime.Now.AddDays(-1));
            
            foreach (var file in tempFiles)
            {
                try
                {
                    var fileInfo = new FileInfo(file);
                    deletedSize += fileInfo.Length;
                    File.Delete(file);
                    deletedCount++;
                }
                catch (Exception ex)
                {
                    _logger.LogDebug("Could not delete temp file {File}: {Error}", file, ex.Message);
                }
            }
            
            await Task.CompletedTask;
            return $"Cleared {deletedCount} temp files ({deletedSize / 1024 / 1024} MB)";
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Temp file cleanup failed");
            return "Temp file cleanup failed";
        }
    }

    private async Task<string> CleanOldLogFilesAsync()
    {
        try
        {
            var logDirectories = new[]
            {
                "/var/log", // Linux
                @"C:\Windows\Logs", // Windows
                "./logs" // Local logs
            }.Where(Directory.Exists);

            var deletedCount = 0;
            var deletedSize = 0L;

            foreach (var logDir in logDirectories)
            {
                var oldLogFiles = Directory.GetFiles(logDir, "*.log", SearchOption.TopDirectoryOnly)
                    .Where(f => File.GetLastWriteTime(f) < DateTime.Now.AddDays(-30));

                foreach (var file in oldLogFiles)
                {
                    try
                    {
                        var fileInfo = new FileInfo(file);
                        deletedSize += fileInfo.Length;
                        File.Delete(file);
                        deletedCount++;
                    }
                    catch (Exception ex)
                    {
                        _logger.LogDebug("Could not delete log file {File}: {Error}", file, ex.Message);
                    }
                }
            }

            await Task.CompletedTask;
            return $"Cleaned {deletedCount} old log files ({deletedSize / 1024 / 1024} MB)";
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Log cleanup failed");
            return "Log cleanup failed";
        }
    }

    private async Task<string> CleanWindowsSpecificAsync()
    {
        try
        {
            var results = new List<string>();
            
            // Clean Windows temp directories
            var windowsTempDirs = new[]
            {
                Environment.GetEnvironmentVariable("TEMP"),
                Environment.GetEnvironmentVariable("TMP"),
                @"C:\Windows\Temp"
            }.Where(d => !string.IsNullOrEmpty(d) && Directory.Exists(d));

            foreach (var tempDir in windowsTempDirs)
            {
                try
                {
                    if (tempDir == null) continue;
                    var files = Directory.GetFiles(tempDir, "*", SearchOption.TopDirectoryOnly)
                        .Where(f => File.GetLastWriteTime(f) < DateTime.Now.AddHours(-1));
                    
                    var count = 0;
                    foreach (var file in files)
                    {
                        try
                        {
                            File.Delete(file);
                            count++;
                        }
                        catch { /* Ignore locked files */ }
                    }
                    
                    if (count > 0)
                        results.Add($"Cleaned {count} files from {tempDir}");
                }
                catch (Exception ex)
                {
                    _logger.LogDebug("Could not clean {TempDir}: {Error}", tempDir, ex.Message);
                }
            }

            await Task.CompletedTask;
            return results.Any() ? string.Join(", ", results) : "Windows cleanup completed";
        }
        catch (Exception ex)
        {
            return $"Windows cleanup failed: {ex.Message}";
        }
    }

    private async Task<string> CleanLinuxSpecificAsync()
    {
        try
        {
            var results = new List<string>();
            
            // Clean common Linux temp/cache directories
            var linuxCleanupDirs = new[]
            {
                "/tmp",
                "/var/tmp",
                "/var/cache"
            }.Where(Directory.Exists);

            foreach (var dir in linuxCleanupDirs)
            {
                try
                {
                    var files = Directory.GetFiles(dir, "*", SearchOption.TopDirectoryOnly)
                        .Where(f => File.GetLastWriteTime(f) < DateTime.Now.AddHours(-1));
                    
                    var count = 0;
                    foreach (var file in files)
                    {
                        try
                        {
                            File.Delete(file);
                            count++;
                        }
                        catch { /* Ignore permission issues */ }
                    }
                    
                    if (count > 0)
                        results.Add($"Cleaned {count} files from {dir}");
                }
                catch (Exception ex)
                {
                    _logger.LogDebug("Could not clean {Dir}: {Error}", dir, ex.Message);
                }
            }

            await Task.CompletedTask;
            return results.Any() ? string.Join(", ", results) : "Linux cleanup completed";
        }
        catch (Exception ex)
        {
            return $"Linux cleanup failed: {ex.Message}";
        }
    }

    private async Task<string> ClearLinuxCachesAsync()
    {
        try
        {
            // Note: This would require root privileges in a real scenario
            // For now, we'll simulate the action
            await Task.Delay(500);
            return "Linux memory caches cleared (simulated)";
        }
        catch (Exception ex)
        {
            return $"Cache clearing failed: {ex.Message}";
        }
    }

    private async Task<string> SimulateProcessTerminationWindows()
    {
        await Task.Delay(500);
        return "High CPU processes identified and terminated (simulated)";
    }

    private async Task<string> SimulateProcessTerminationLinux()
    {
        await Task.Delay(500);
        return "High CPU processes identified and terminated (simulated)";
    }
}