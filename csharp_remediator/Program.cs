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
        "high_cpu" => RestartService("YourCpuHogService"),
        "high_disk" => CleanTempFiles(),
        _ => "Unknown issue"
    };

    await context.Response.WriteAsync(result);
});

app.Run("http://localhost:5001");

string RestartService(string serviceName)
{
    // placeholder
    return $"Simulated restart of {serviceName}";
}

string CleanTempFiles()
{
    // placeholder
    return "Simulated disk cleanup";
}

record Issue(string IssueType);
