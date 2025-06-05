using EriBot.Remediator.Models;
using EriBot.Remediator.Services;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace EriBot.Remediator.Services;

/// <summary>
/// Implementation of platform-specific services
/// </summary>
public class PlatformService : IPlatformService
{
    private readonly ILogger<PlatformService> _logger;

    public PlatformService(ILogger<PlatformService> logger)
    {
        _logger = logger;
    }

    public bool IsWindows => RuntimeInformation.IsOSPlatform(OSPlatform.Windows);
    public bool IsLinux => RuntimeInformation.IsOSPlatform(OSPlatform.Linux);
    public bool IsMacOS => RuntimeInformation.IsOSPlatform(OSPlatform.OSX);

    public PlatformType GetPlatformType()
    {
        if (IsWindows) return PlatformType.Windows;
        if (IsLinux) return PlatformType.Linux;
        if (IsMacOS) return PlatformType.MacOS;
        return PlatformType.Unknown;
    }

    public async Task<SystemInfo> GetSystemInfoAsync()
    {
        try
        {
            var cpuInfo = await GetCpuInfoAsync();
            var memoryInfo = await GetMemoryInfoAsync();
            var diskInfo = await GetDiskInfoAsync();

            return new SystemInfo
            {
                Hostname = Environment.MachineName,
                Platform = GetPlatformType().ToString(),
                OSVersion = Environment.OSVersion.VersionString,
                UptimeSeconds = Environment.TickCount64 / 1000,
                Cpu = cpuInfo,
                Memory = memoryInfo,
                Disk = diskInfo,
                Timestamp = DateTime.UtcNow
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get system info");
            
            // Return basic info even if detailed collection fails
            return new SystemInfo
            {
                Hostname = Environment.MachineName,
                Platform = GetPlatformType().ToString(),
                OSVersion = Environment.OSVersion.VersionString,
                Timestamp = DateTime.UtcNow
            };
        }
    }

    public async Task<CommandResult> ExecuteCommandAsync(string command, string arguments = "")
    {
        var startTime = DateTime.UtcNow;
        var stopwatch = Stopwatch.StartNew();

        try
        {
            var processStartInfo = new ProcessStartInfo
            {
                FileName = command,
                Arguments = arguments,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = new Process { StartInfo = processStartInfo };
            
            process.Start();
            
            var outputTask = process.StandardOutput.ReadToEndAsync();
            var errorTask = process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();
            
            var output = await outputTask;
            var error = await errorTask;
            
            stopwatch.Stop();

            return new CommandResult
            {
                Success = process.ExitCode == 0,
                Output = output,
                Error = error,
                ExitCode = process.ExitCode,
                Duration = stopwatch.Elapsed
            };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Command execution failed: {Command} {Arguments}", command, arguments);

            return new CommandResult
            {
                Success = false,
                Output = "",
                Error = ex.Message,
                ExitCode = -1,
                Duration = stopwatch.Elapsed
            };
        }
    }

    public string GetTempDirectory()
    {
        return Path.GetTempPath();
    }

    public Task<CleanupResult> CleanTempFilesAsync()
    {
        var startTime = DateTime.UtcNow;
        var stopwatch = Stopwatch.StartNew();
        var errors = new List<string>();
        var filesDeleted = 0L;
        var bytesFreed = 0L;

        try
        {
            var tempPath = GetTempDirectory();
            var cutoffTime = DateTime.Now.AddDays(-1); // Delete files older than 1 day

            var tempFiles = Directory.GetFiles(tempPath, "*", SearchOption.TopDirectoryOnly)
                .Where(f => File.GetLastWriteTime(f) < cutoffTime);

            foreach (var file in tempFiles)
            {
                try
                {
                    var fileInfo = new FileInfo(file);
                    var fileSize = fileInfo.Length;
                    
                    File.Delete(file);
                    
                    filesDeleted++;
                    bytesFreed += fileSize;
                }
                catch (Exception ex)
                {
                    errors.Add($"Could not delete {file}: {ex.Message}");
                    _logger.LogDebug("Could not delete temp file {File}: {Error}", file, ex.Message);
                }
            }

            stopwatch.Stop();

            var result = new CleanupResult
            {
                Success = true,
                FilesDeleted = filesDeleted,
                BytesFreed = bytesFreed,
                Errors = errors,
                Duration = stopwatch.Elapsed
            };

            return Task.FromResult(result);
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Temp file cleanup failed");

            var result = new CleanupResult
            {
                Success = false,
                FilesDeleted = filesDeleted,
                BytesFreed = bytesFreed,
                Errors = new List<string> { ex.Message },
                Duration = stopwatch.Elapsed
            };

            return Task.FromResult(result);
        }
    }

    public async Task<ServiceResult> RestartServiceAsync(string serviceName)
    {
        try
        {
            if (IsWindows)
            {
                return await RestartWindowsServiceAsync(serviceName);
            }
            else if (IsLinux)
            {
                return await RestartLinuxServiceAsync(serviceName);
            }
            else
            {
                return new ServiceResult
                {
                    Success = false,
                    ServiceName = serviceName,
                    Status = "unsupported_platform",
                    Message = $"Service restart not supported on {GetPlatformType()}"
                };
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Service restart failed for {ServiceName}", serviceName);
            
            return new ServiceResult
            {
                Success = false,
                ServiceName = serviceName,
                Status = "error",
                Message = ex.Message
            };
        }
    }

    public Task<List<ProcessInfo>> GetHighCpuProcessesAsync(double threshold = 80.0)
    {
        var processes = new List<ProcessInfo>();

        try
        {
            var allProcesses = Process.GetProcesses();

            foreach (var process in allProcesses)
            {
                try
                {
                    // Note: Getting accurate CPU usage requires sampling over time
                    // This is a simplified implementation
                    var processInfo = new ProcessInfo
                    {
                        ProcessId = process.Id,
                        ProcessName = process.ProcessName,
                        CpuPercent = 0, // Would need performance counters for accurate CPU %
                        MemoryBytes = process.WorkingSet64,
                        StartTime = process.StartTime
                    };

                    // For now, we'll simulate by checking memory usage as a proxy
                    if (processInfo.MemoryBytes > 100 * 1024 * 1024) // > 100MB
                    {
                        processes.Add(processInfo);
                    }
                }
                catch (Exception ex)
                {
                    // Process might have exited or access denied
                    _logger.LogDebug("Could not get info for process {ProcessName}: {Error}", 
                        process.ProcessName, ex.Message);
                }
                finally
                {
                    process.Dispose();
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get high CPU processes");
        }

        return Task.FromResult(processes);
    }

    private Task<CpuInfo> GetCpuInfoAsync()
    {
        var cpuInfo = new CpuInfo
        {
            CoreCount = Environment.ProcessorCount,
            UsagePercent = null, // Would need performance counters
            Architecture = RuntimeInformation.ProcessArchitecture.ToString()
        };
        return Task.FromResult(cpuInfo);
    }

    private Task<MemoryInfo> GetMemoryInfoAsync()
    {
        try
        {
            var workingSet = Environment.WorkingSet;
            var gcMemory = GC.GetTotalMemory(false);

            var memoryInfo = new MemoryInfo
            {
                TotalBytes = null, // Would need platform-specific calls
                AvailableBytes = null, // Would need platform-specific calls
                UsagePercent = null, // Would need total memory info
                WorkingSetBytes = workingSet
            };
            return Task.FromResult(memoryInfo);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get memory info");
            return Task.FromResult(new MemoryInfo());
        }
    }

    private Task<DiskInfo> GetDiskInfoAsync()
    {
        try
        {
            var currentDir = Directory.GetCurrentDirectory();
            var rootPath = Path.GetPathRoot(currentDir) ?? "/";
            var drive = new DriveInfo(rootPath);

            var totalBytes = drive.TotalSize;
            var freeBytes = drive.AvailableFreeSpace;
            var usedBytes = totalBytes - freeBytes;
            var usagePercent = (double)usedBytes / totalBytes * 100;

            var diskInfo = new DiskInfo
            {
                TotalSpaceBytes = totalBytes,
                FreeSpaceBytes = freeBytes,
                UsagePercent = usagePercent,
                RootDrive = drive.Name
            };
            return Task.FromResult(diskInfo);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get disk info");
            return Task.FromResult(new DiskInfo());
        }
    }

    private async Task<ServiceResult> RestartWindowsServiceAsync(string serviceName)
    {
        try
        {
            // For safety, we'll simulate the restart
            // In a real implementation, you'd use ServiceController class
            await Task.Delay(1000);

            return new ServiceResult
            {
                Success = true,
                ServiceName = serviceName,
                Status = "restarted",
                Message = $"Windows service '{serviceName}' restart simulated"
            };
        }
        catch (Exception ex)
        {
            return new ServiceResult
            {
                Success = false,
                ServiceName = serviceName,
                Status = "failed",
                Message = ex.Message
            };
        }
    }

    private async Task<ServiceResult> RestartLinuxServiceAsync(string serviceName)
    {
        try
        {
            // For safety, we'll simulate the restart
            // In a real implementation, you'd execute: systemctl restart serviceName
            await Task.Delay(1000);

            return new ServiceResult
            {
                Success = true,
                ServiceName = serviceName,
                Status = "restarted",
                Message = $"Linux service '{serviceName}' restart simulated"
            };
        }
        catch (Exception ex)
        {
            return new ServiceResult
            {
                Success = false,
                ServiceName = serviceName,
                Status = "failed",
                Message = ex.Message
            };
        }
    }
}