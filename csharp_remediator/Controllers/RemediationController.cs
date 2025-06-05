using Microsoft.AspNetCore.Mvc;
using EriBot.Remediator.Models;
using EriBot.Remediator.Services;
using System.ComponentModel.DataAnnotations;

namespace EriBot.Remediator.Controllers;

/// <summary>
/// Controller for handling remediation requests
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class RemediationController : ControllerBase
{
    private readonly IRemediationService _remediationService;
    private readonly ILogger<RemediationController> _logger;

    public RemediationController(IRemediationService remediationService, ILogger<RemediationController> logger)
    {
        _remediationService = remediationService;
        _logger = logger;
    }

    /// <summary>
    /// Execute a remediation action
    /// </summary>
    /// <param name="request">The remediation request</param>
    /// <returns>Remediation result</returns>
    [HttpPost]
    [Route("")]
    [Route("execute")]
    public async Task<IActionResult> ExecuteRemediation([FromBody] RemediationRequest request)
    {
        try
        {
            // Validate the request
            if (!_remediationService.ValidateRequest(request))
            {
                _logger.LogWarning("Invalid remediation request received: {IssueType}", request.IssueType);
                return BadRequest(new
                {
                    error = "Invalid remediation request",
                    message = "The request does not meet validation requirements",
                    timestamp = DateTime.UtcNow
                });
            }

            _logger.LogInformation("Executing remediation for issue type: {IssueType}", request.IssueType);

            var startTime = DateTime.UtcNow;
            var result = await _remediationService.ExecuteRemediationAsync(request);
            var duration = DateTime.UtcNow - startTime;

            _logger.LogInformation("Remediation completed for {IssueType}. Success: {Success}, Duration: {Duration}ms", 
                request.IssueType, result.Success, duration.TotalMilliseconds);

            if (result.Success)
            {
                return Ok(result);
            }
            else
            {
                return StatusCode(500, result);
            }
        }
        catch (ValidationException ex)
        {
            _logger.LogWarning(ex, "Validation error in remediation request");
            return BadRequest(new
            {
                error = "Validation error",
                message = ex.Message,
                timestamp = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error during remediation execution");
            return StatusCode(500, new
            {
                error = "Internal server error",
                message = "An unexpected error occurred during remediation",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Get available remediation actions
    /// </summary>
    /// <returns>List of available actions</returns>
    [HttpGet("actions")]
    public IActionResult GetAvailableActions()
    {
        try
        {
            var actions = _remediationService.GetAvailableActions();
            return Ok(new
            {
                actions = actions,
                count = actions.Length,
                timestamp = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to retrieve available actions");
            return StatusCode(500, new
            {
                error = "Failed to retrieve available actions",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Get estimated execution time for a remediation action
    /// </summary>
    /// <param name="issueType">The type of issue to estimate</param>
    /// <returns>Estimated execution time in milliseconds</returns>
    [HttpGet("estimate/{issueType}")]
    public async Task<IActionResult> GetExecutionTimeEstimate(string issueType)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(issueType))
            {
                return BadRequest(new
                {
                    error = "Issue type is required",
                    timestamp = DateTime.UtcNow
                });
            }

            var estimatedTime = await _remediationService.GetEstimatedExecutionTimeAsync(issueType);
            
            return Ok(new
            {
                issueType = issueType,
                estimatedTimeMs = estimatedTime,
                estimatedTimeSeconds = estimatedTime / 1000.0,
                timestamp = DateTime.UtcNow
            });
        }
        catch (ArgumentException ex)
        {
            return BadRequest(new
            {
                error = "Invalid issue type",
                message = ex.Message,
                timestamp = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get execution time estimate for {IssueType}", issueType);
            return StatusCode(500, new
            {
                error = "Failed to get execution time estimate",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Get service status and statistics
    /// </summary>
    /// <returns>Service status information</returns>
    [HttpGet("status")]
    public async Task<IActionResult> GetServiceStatus()
    {
        try
        {
            var status = await _remediationService.GetServiceStatusAsync();
            return Ok(status);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to retrieve service status");
            return StatusCode(500, new
            {
                error = "Failed to retrieve service status",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Validate a remediation request without executing it
    /// </summary>
    /// <param name="request">The remediation request to validate</param>
    /// <returns>Validation result</returns>
    [HttpPost("validate")]
    public IActionResult ValidateRequest([FromBody] RemediationRequest request)
    {
        try
        {
            var isValid = _remediationService.ValidateRequest(request);
            var availableActions = _remediationService.GetAvailableActions();

            return Ok(new
            {
                isValid = isValid,
                issueType = request.IssueType,
                isKnownAction = availableActions.Contains(request.IssueType),
                availableActions = availableActions,
                timestamp = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to validate request");
            return StatusCode(500, new
            {
                error = "Failed to validate request",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Legacy endpoint for backward compatibility
    /// </summary>
    /// <param name="request">The remediation request</param>
    /// <returns>Remediation result</returns>
    [HttpPost("remediate")]
    public async Task<IActionResult> RemediateLegacy([FromBody] RemediationRequest request)
    {
        // Redirect to the main execute endpoint
        return await ExecuteRemediation(request);
    }
}