using Projects;

var builder = DistributedApplication.CreateBuilder(args);

builder.AddProject<FleetManager_Api>("Api");

builder.Build().Run();

