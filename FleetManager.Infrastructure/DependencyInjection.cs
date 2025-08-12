using FleetManager.Infrastructure.Google;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace FleetManager.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        // Register Google services
        services.AddScoped<IGmailServiceFactory, GmailServiceFactory>();

        // Register other infrastructure services here
        // e.g., services.AddScoped<IReadMessagesService, ReadMessagesService>();

        return services;
    }
}