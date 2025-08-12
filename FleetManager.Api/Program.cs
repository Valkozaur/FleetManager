using FleetManager.Infrastructure;
using Google.Apis.Auth.AspNetCore3;
using Google.Apis.Gmail.v1;
using Google.Apis.Services;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddOpenApi();
builder.Services.AddInfrastructure(builder.Configuration);

builder.Services
    .AddAuthentication(o =>
    {
        o.DefaultChallengeScheme = GoogleOpenIdConnectDefaults.AuthenticationScheme;
        o.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
    })
    .AddCookie(options =>
    {
        options.Cookie.SameSite = SameSiteMode.Lax;
        options.Cookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
    })
    .AddGoogleOpenIdConnect(options =>
    {
        var googleAuth = builder.Configuration.GetSection("Google");
        options.ClientId = googleAuth["ClientId"];
        options.ClientSecret = googleAuth["ClientSecret"];

        options.CorrelationCookie.SameSite = SameSiteMode.Lax;
        options.CorrelationCookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;
        options.NonceCookie.SameSite = SameSiteMode.Lax;
        options.NonceCookie.SecurePolicy = CookieSecurePolicy.SameAsRequest;

        options.Scope.Add("openid");
        options.Scope.Add("profile");
        options.Scope.Add("email");
        options.Scope.Add(GmailService.Scope.GmailReadonly);
    });

builder.Services.AddAuthorization();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/", (HttpContext context) =>
{
    if (context.User.Identity?.IsAuthenticated == true)
    {
        return Results.Ok($"Hello {context.User.Identity.Name}! You are authenticated. Visit /emails to see your messages.");
    }
    return Results.Redirect("/login");
});

// Remove the old /email endpoint that uses IGmailServiceFactory - it's conflicting with the new flow

app.MapGet("/login", () => Results.Challenge(new AuthenticationProperties { RedirectUri = "/emails" }));

app.MapGet("/emails", async (IGoogleAuthProvider auth) =>
{
    var credential = await auth.GetCredentialAsync();
    if (credential is null)
    {
        return Results.Unauthorized();
    }

    var service = new GmailService(new BaseClientService.Initializer
    {
        HttpClientInitializer = credential,
        ApplicationName = "FleetManager API"
    });

    var request = service.Users.Messages.List("me");
    request.MaxResults = 10;
    var response = await request.ExecuteAsync();

    return Results.Ok(response.Messages);
}).RequireAuthorization();

app.Run();