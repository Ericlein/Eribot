using Microsoft.AspNetCore.Mvc;
using EriBot.Remediator.Services;

namespace EriBot.Remediator.Controllers;

/// <summary>
/// Health check controller for monitoring service status
/// </summary>
[ApiController]
[Route("api/[controller]")]
public class HealthController : ControllerBase
{
    private readonly IHealthService _healthService;
    private readonly ILogger<HealthController> _logger;

    public HealthController(IHealthService healthService, ILogger<HealthController> logger)
    {
        _healthService = healthService;
        _logger = logger;
    }

    /// <summary>
    /// Basic health check endpoint
    /// </summary>
    /// <returns>Simple health status</returns>
    [HttpGet]
    [Route("")]
    [Route("check")]
    public async Task<IActionResult> CheckHealth()
    {
        try
        {
            var result = await _healthService.CheckHealthAsync();
            
            if (result.IsHealthy)
            {
                return Ok(new
                {
                    status = "healthy",
                    timestamp = result.CheckedAt,
                    duration = result.Duration.TotalMilliseconds
                });
            }
            else
            {
                return StatusCode(503, new
                {
                    status = "unhealthy",
                    timestamp = result.CheckedAt,
                    duration = result.Duration.TotalMilliseconds,
                    details = result.Data
                });
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Health check failed");
            return StatusCode(503, new
            {
                status = "unhealthy",
                error = "Health check failed",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Detailed health status with metrics
    /// </summary>
    /// <returns>Comprehensive health information</returns>
    [HttpGet("detailed")]
    public async Task<IActionResult> GetDetailedHealth()
    {
        try
        {
            var health = await _healthService.GetDetailedHealthAsync();
            return Ok(health);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Detailed health check failed");
            return StatusCode(500, new
            {
                error = "Failed to retrieve detailed health status",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Check external dependencies
    /// </summary>
    /// <returns>Status of external dependencies</returns>
    [HttpGet("dependencies")]
    public async Task<IActionResult> CheckDependencies()
    {
        try
        {
            var dependencies = await _healthService.CheckDependenciesAsync();
            var allHealthy = dependencies.Values.All(d => d.IsAvailable);
            
            var statusCode = allHealthy ? 200 : 503;
            
            return StatusCode(statusCode, new
            {
                overall_status = allHealthy ? "healthy" : "degraded",
                dependencies = dependencies,
                timestamp = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Dependency check failed");
            return StatusCode(500, new
            {
                error = "Failed to check dependencies",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Get service metrics
    /// </summary>
    /// <returns>Performance and usage metrics</returns>
    [HttpGet("metrics")]
    public async Task<IActionResult> GetMetrics()
    {
        try
        {
            var metrics = await _healthService.GetMetricsAsync();
            return Ok(metrics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to retrieve metrics");
            return StatusCode(500, new
            {
                error = "Failed to retrieve metrics",
                timestamp = DateTime.UtcNow
            });
        }
    }

    /// <summary>
    /// Liveness probe for Kubernetes
    /// </summary>
    /// <returns>Simple alive status</returns>
    [HttpGet("live")]
    public IActionResult LivenessProbe()
    {
        return Ok(new
        {
            status = "alive",
            timestamp = DateTime.UtcNow
        });
    }

    /// <summary>
    /// Readiness probe for Kubernetes
    /// </summary>
    /// <returns>Ready status</returns>
    [HttpGet("ready")]
    public async Task<IActionResult> ReadinessProbe()
    {
        try
        {
            var result = await _healthService.CheckHealthAsync();
            
            if (result.IsHealthy)
            {
                return Ok(new
                {
                    status = "ready",
                    timestamp = DateTime.UtcNow
                });
            }
            else
            {
                return StatusCode(503, new
                {
                    status = "not_ready",
                    timestamp = DateTime.UtcNow
                });
            }
        }
        catch
        {
            return StatusCode(503, new
            {
                status = "not_ready",
                timestamp = DateTime.UtcNow
            });
        }
    }
}