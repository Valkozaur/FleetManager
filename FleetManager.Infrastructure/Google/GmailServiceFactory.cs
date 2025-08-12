using Google.Apis.Auth.OAuth2;
using Google.Apis.Gmail.v1;
using Google.Apis.Services;
using Microsoft.Extensions.Configuration;

namespace FleetManager.Infrastructure.Google;

public interface IGmailServiceFactory
{
    Task<GmailService> CreateAsync();
}

public class GmailServiceFactory(IConfiguration config) : IGmailServiceFactory
{
    public async Task<GmailService> CreateAsync()
    {
        var clientSecrets = new ClientSecrets
        {
            ClientId = config["Google:ClientId"],
            ClientSecret = config["Google:ClientSecret"]
        };

        var credential = await GoogleWebAuthorizationBroker.AuthorizeAsync(
            clientSecrets,
            [ GmailService.Scope.GmailReadonly ],
            "user",
            CancellationToken.None
        );

        return new GmailService(new BaseClientService.Initializer()
        {
            HttpClientInitializer = credential,
            ApplicationName = config["Google:ApplicationName"],
        });
    }
}