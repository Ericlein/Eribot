using System.Runtime.InteropServices;
using System.Text.Json.Serialization;

namespace EriBot.Remediator.Models;

/// <summary>
/// Represents system information and health metrics
/// </summary>
public record SystemInfo
{
    /// <summary>
    /// Hostname of the system
    /// </summary>
    [JsonPropertyName("hostname")]
    public string Hostname { get; init; } = Environment.MachineName;

    /// <summary>
    /// Operating system platform
    /// </summary>
    [JsonPropertyName("platform")]
    public string Platform { get; init; } = Environment.OSVersion.Platform.ToString();

    /// <summary>
    /// OS version information
    /// </summary>
    [JsonPropertyName("osVersion")]
    public string OSVersion { get; init; } = Environment.OSVersion.VersionString;

    /// <summary>
    /// System uptime in seconds
    /// </summary>
    [JsonPropertyName("uptimeSeconds")]
    public long UptimeSeconds { get; init; } = Environment.TickCount64 / 1000;

    /// <summary>
    /// CPU information
    /// </summary>
    [JsonPropertyName("cpu")]
    public CpuInfo Cpu { get; init; } = new();

    /// <summary>
    /// Memory information
    /// </summary>
    [JsonPropertyName("memory")]
    public MemoryInfo Memory { get; init; } = new();

    /// <summary>
    /// Disk information
    /// </summary>
    [JsonPropertyName("disk")]
    public DiskInfo Disk { get; init; } = new();

    /// <summary>
    /// Timestamp when this information was collected
    /// </summary>
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; init; } = DateTime.UtcNow;
}

/// <summary>
/// CPU-related information
/// </summary>
public record CpuInfo
{
    /// <summary>
    /// Number of logical processors
    /// </summary>
    [JsonPropertyName("coreCount")]
    public int CoreCount { get; init; } = Environment.ProcessorCount;

    /// <summary>
    /// Current CPU usage percentage (if available)
    /// </summary>
    [JsonPropertyName("usagePercent")]
    public double? UsagePercent { get; init; }

    /// <summary>
    /// CPU architecture
    /// </summary>
    [JsonPropertyName("architecture")]
    public string Architecture { get; init; } = RuntimeInformation.ProcessArchitecture.ToString();
}

/// <summary>
/// Memory-related information
/// </summary>
public record MemoryInfo
{
    /// <summary>
    /// Total physical memory in bytes
    /// </summary>
    [JsonPropertyName("totalBytes")]
    public long? TotalBytes { get; init; }

    /// <summary>
    /// Available memory in bytes
    /// </summary>
    [JsonPropertyName("availableBytes")]
    public long? AvailableBytes { get; init; }

    /// <summary>
    /// Memory usage percentage
    /// </summary>
    [JsonPropertyName("usagePercent")]
    public double? UsagePercent { get; init; }

    /// <summary>
    /// Working set memory of current process
    /// </summary>
    [JsonPropertyName("workingSetBytes")]
    public long WorkingSetBytes { get; init; } = Environment.WorkingSet;
}

/// <summary>
/// Disk-related information
/// </summary>
public record DiskInfo
{
    /// <summary>
    /// Available free space in bytes
    /// </summary>
    [JsonPropertyName("freeSpaceBytes")]
    public long? FreeSpaceBytes { get; init; }

    /// <summary>
    /// Total disk space in bytes
    /// </summary>
    [JsonPropertyName("totalSpaceBytes")]
    public long? TotalSpaceBytes { get; init; }

    /// <summary>
    /// Disk usage percentage
    /// </summary>
    [JsonPropertyName("usagePercent")]
    public double? UsagePercent { get; init; }

    /// <summary>
    /// Root drive information
    /// </summary>
    [JsonPropertyName("rootDrive")]
    public string RootDrive { get; init; } = Directory.GetDirectoryRoot(Environment.CurrentDirectory);
}