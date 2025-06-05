using EriBot.Remediator.Models;

namespace EriBot.Remediator.Services;

/// <summary>
/// Interface for platform-specific operations
/// </summary>
public interface IPlatformService
{
    /// <summary>
    /// Get current platform type
    /// </summary>
    PlatformType GetPlatformType();

    /// <summary>
    /// Check if running on Windows
    /// </summary>
    bool IsWindows { get; }

    /// <summary>
    /// Check if running on Linux
    /// </summary>
    bool IsLinux { get; }

    /// <summary>
    /// Check if running on macOS
    /// </summary>
    bool IsMacOS { get; }

    /// <summary>
    /// Get system information for the current platform
    /// </summary>
    /// <returns>System information</returns>
    Task<SystemInfo> GetSystemInfoAsync();

    /// <summary>
    /// Execute a platform-specific command
    /// </summary>
    /// <param name="command">Command to execute</param>
    /// <param name="arguments">Command arguments</param>
    /// <returns>Command result</returns>
    Task<CommandResult> ExecuteCommandAsync(string command, string arguments = "");

    /// <summary>
    /// Get temporary directory path for the current platform
    /// </summary>
    /// <returns>Temporary directory path</returns>
    string GetTempDirectory();

    /// <summary>
    /// Clean temporary files for the current platform
    /// </summary>
    /// <returns>Cleanup result</returns>
    Task<CleanupResult> CleanTempFilesAsync();

    /// <summary>
    /// Restart a service on the current platform
    /// </summary>
    /// <param name="serviceName">Name of the service to restart</param>
    /// <returns>Service restart result</returns>
    Task<ServiceResult> RestartServiceAsync(string serviceName);

    /// <summary>
    /// Get list of running processes consuming high CPU
    /// </summary>
    /// <param name="threshold">CPU threshold percentage</param>
    /// <returns>List of high CPU processes</returns>
    Task<List<ProcessInfo>> GetHighCpuProcessesAsync(double threshold = 80.0);
}

/// <summary>
/// Platform types
/// </summary>
public enum PlatformType
{
    Windows,
    Linux,
    MacOS,
    Unknown
}

/// <summary>
/// Command execution result
/// </summary>
public record CommandResult
{
    public bool Success { get; init; }
    public string Output { get; init; } = string.Empty;
    public string Error { get; init; } = string.Empty;
    public int ExitCode { get; init; }
    public TimeSpan Duration { get; init; }
}

/// <summary>
/// Cleanup operation result
/// </summary>
public record CleanupResult
{
    public bool Success { get; init; }
    public long FilesDeleted { get; init; }
    public long BytesFreed { get; init; }
    public List<string> Errors { get; init; } = new();
    public TimeSpan Duration { get; init; }
}

/// <summary>
/// Service operation result
/// </summary>
public record ServiceResult
{
    public bool Success { get; init; }
    public string ServiceName { get; init; } = string.Empty;
    public string Status { get; init; } = string.Empty;
    public string Message { get; init; } = string.Empty;
}

/// <summary>
/// Process information
/// </summary>
public record ProcessInfo
{
    public int ProcessId { get; init; }
    public string ProcessName { get; init; } = string.Empty;
    public double CpuPercent { get; init; }
    public long MemoryBytes { get; init; }
    public DateTime StartTime { get; init; }
}