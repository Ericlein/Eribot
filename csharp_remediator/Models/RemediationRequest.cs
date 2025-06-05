using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace EriBot.Remediator.Models;

/// <summary>
/// Represents a request for remediation action
/// </summary>
public record RemediationRequest
{
    /// <summary>
    /// Type of issue to remediate (e.g., "high_cpu", "high_disk")
    /// </summary>
    [Required]
    [JsonPropertyName("issueType")]
    public required string IssueType { get; init; }

    /// <summary>
    /// Additional context information about the issue
    /// </summary>
    [JsonPropertyName("context")]
    public Dictionary<string, object>? Context { get; init; }

    /// <summary>
    /// Timestamp when the issue was detected
    /// </summary>
    [JsonPropertyName("timestamp")]
    public DateTime? Timestamp { get; init; }

    /// <summary>
    /// Hostname where the issue occurred
    /// </summary>
    [JsonPropertyName("hostname")]
    public string? Hostname { get; init; }

    /// <summary>
    /// Priority level of the remediation (1-10, 10 being highest)
    /// </summary>
    [JsonPropertyName("priority")]
    [Range(1, 10)]
    public int Priority { get; init; } = 5;

    /// <summary>
    /// Whether to force the remediation even if it might be disruptive
    /// </summary>
    [JsonPropertyName("force")]
    public bool Force { get; init; } = false;
}