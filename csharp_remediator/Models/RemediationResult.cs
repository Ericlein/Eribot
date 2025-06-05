using System.Text.Json.Serialization;

namespace EriBot.Remediator.Models;

/// <summary>
/// Represents the result of a remediation action
/// </summary>
public record RemediationResult
{
    /// <summary>
    /// Whether the remediation was successful
    /// </summary>
    [JsonPropertyName("success")]
    public bool Success { get; init; }

    /// <summary>
    /// Human-readable message describing the result
    /// </summary>
    [JsonPropertyName("message")]
    public required string Message { get; init; }

    /// <summary>
    /// Detailed execution steps taken
    /// </summary>
    [JsonPropertyName("details")]
    public List<string>? Details { get; init; }

    /// <summary>
    /// Time taken to complete the remediation (in milliseconds)
    /// </summary>
    [JsonPropertyName("executionTimeMs")]
    public long ExecutionTimeMs { get; init; }

    /// <summary>
    /// Any warnings generated during remediation
    /// </summary>
    [JsonPropertyName("warnings")]
    public List<string>? Warnings { get; init; }

    /// <summary>
    /// Error details if the remediation failed
    /// </summary>
    [JsonPropertyName("error")]
    public string? Error { get; init; }

    /// <summary>
    /// Timestamp when the remediation completed
    /// </summary>
    [JsonPropertyName("completedAt")]
    public DateTime CompletedAt { get; init; } = DateTime.UtcNow;

    /// <summary>
    /// Create a successful result
    /// </summary>
    public static RemediationResult CreateSuccess(string message, List<string>? details = null, long executionTimeMs = 0)
    {
        return new RemediationResult
        {
            Success = true,
            Message = message,
            Details = details,
            ExecutionTimeMs = executionTimeMs
        };
    }

    /// <summary>
    /// Create a failure result
    /// </summary>
    public static RemediationResult CreateFailure(string message, string? error = null, long executionTimeMs = 0)
    {
        return new RemediationResult
        {
            Success = false,
            Message = message,
            Error = error,
            ExecutionTimeMs = executionTimeMs
        };
    }
}