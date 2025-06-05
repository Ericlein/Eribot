using EriBot.Remediator.Models;

namespace EriBot.Remediator.Services;

/// <summary>
/// Interface for remediation services
/// </summary>
public interface IRemediationService
{
    /// <summary>
    /// Execute a remediation action based on the request
    /// </summary>
    /// <param name="request">The remediation request</param>
    /// <returns>The result of the remediation action</returns>
    Task<RemediationResult> ExecuteRemediationAsync(RemediationRequest request);

    /// <summary>
    /// Get the current status of the remediation service
    /// </summary>
    /// <returns>Service status information</returns>
    Task<object> GetServiceStatusAsync();

    /// <summary>
    /// Get list of available remediation actions
    /// </summary>
    /// <returns>Array of available action types</returns>
    string[] GetAvailableActions();

    /// <summary>
    /// Validate if a remediation request is valid
    /// </summary>
    /// <param name="request">The request to validate</param>
    /// <returns>True if valid, false otherwise</returns>
    bool ValidateRequest(RemediationRequest request);
    
    /// <summary>
    /// Get estimated execution time for a remediation action
    /// </summary>
    /// <param name="issueType">The type of issue to remediate</param>
    /// <returns>Estimated time in milliseconds</returns>
    Task<long> GetEstimatedExecutionTimeAsync(string issueType);
}