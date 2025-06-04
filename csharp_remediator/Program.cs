using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using Microsoft.AspNetCore.Http;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapPost("/remediate", async (HttpContext context) =>
{
    var body = await context.Request.ReadFromJsonAsync<Issue>();
    Console.WriteLine($"Remediating issue: {body?.IssueType}");

    string result = body?.IssueType switch
    {
        "high_cpu" => RemediationService.RestartService("YourCpuHogService"),
        "high_disk" => RemediationService.CleanTempFiles(),
        _ => "Unknown issue type"
    };

    await context.Response.WriteAsync(result);
});

app.Run("http://localhost:5001");

record Issue(string IssueType);