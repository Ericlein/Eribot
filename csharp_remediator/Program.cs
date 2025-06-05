using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.AspNetCore.Http;
using System.Diagnostics;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using EriBot.Remediator.Services;
using EriBot.Remediator.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddLogging();
builder.Services.AddControllers();

// Register your services
builder.Services.AddScoped<IRemediationService, RemediationService>();
builder.Services.AddScoped<IHealthService, HealthService>();
builder.Services.AddScoped<IPlatformService, PlatformService>();

// Configure Kestrel for cross-platform compatibility
builder.WebHost.ConfigureKestrel(options =>
{
    options.ListenAnyIP(5001); // Listen on all interfaces
});

var app = builder.Build();

// Configure logging
var logger = app.Services.GetRequiredService<ILogger<Program>>();

// Middleware for logging requests
app.Use(async (context, next) =>
{
    logger.LogInformation($"Request: {context.Request.Method} {context.Request.Path}");
    await next();
});

// Map controllers
app.MapControllers();

// Legacy endpoints for backward compatibility
app.MapGet("/health", async (IHealthService healthService) =>
{
    try
    {
        var result = await healthService.CheckHealthAsync();
        
        if (result.IsHealthy)
        {
            return Results.Ok(new
            {
                status = "healthy",
                timestamp = result.CheckedAt,
                duration = result.Duration.TotalMilliseconds
            });
        }
        else
        {
            return Results.Problem(
                detail: "Service is unhealthy",
                statusCode: 503
            );
        }
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Health check failed");
        return Results.Problem("Health check failed", statusCode: 503);
    }
});

app.MapGet("/status", async (IRemediationService remediationService) =>
{
    try
    {
        var status = await remediationService.GetServiceStatusAsync();
        return Results.Ok(status);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Status check failed");
        return Results.Problem("Status check failed", statusCode: 500);
    }
});

app.MapGet("/actions", (IRemediationService remediationService) =>
{
    try
    {
        var actions = remediationService.GetAvailableActions();
        return Results.Ok(new
        {
            actions = actions,
            count = actions.Length,
            timestamp = DateTime.UtcNow
        });
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Failed to get actions");
        return Results.Problem("Failed to get actions", statusCode: 500);
    }
});

// Legacy remediation endpoint
app.MapPost("/remediate", async (HttpContext context, IRemediationService remediationService) =>
{
    try
    {
        var body = await context.Request.ReadFromJsonAsync<RemediationRequest>();
        if (body == null)
        {
            logger.LogWarning("Invalid request body received");
            return Results.BadRequest("Invalid request body");
        }

        logger.LogInformation($"Remediation requested for: {body.IssueType}");

        var result = await remediationService.ExecuteRemediationAsync(body);
        
        logger.LogInformation($"Remediation completed: {result.Success}");
        
        if (result.Success)
        {
            return Results.Ok(result);
        }
        else
        {
            return Results.Problem(result.Message, statusCode: 500);
        }
    }
    catch (JsonException ex)
    {
        logger.LogError(ex, "JSON parsing error");
        return Results.BadRequest("Invalid JSON format");
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Unexpected error during remediation");
        return Results.Problem("Internal server error", statusCode: 500);
    }
});

// Graceful shutdown
var cts = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) =>
{
    logger.LogInformation("Shutdown signal received");
    cts.Cancel();
    e.Cancel = true;
};

logger.LogInformation($"EriBot Remediation Service starting on port 5001");
logger.LogInformation($"Platform: {Environment.OSVersion.Platform}");
logger.LogInformation($"OS Version: {Environment.OSVersion.VersionString}");

try
{
    await app.RunAsync(cts.Token);
}
catch (OperationCanceledException)
{
    logger.LogInformation("Service stopped gracefully");
}
catch (Exception ex)
{
    logger.LogCritical(ex, "Service stopped unexpectedly");
}