Nginx configuration used for routing UI and API traffic in production.

Place site-specific files in `sites-available/` and mount certificates from `/etc/letsencrypt` when deploying.
# Nginx Configuration

Nginx reverse proxy configuration for FleetManager microservices.

This directory contains:
- `nginx.conf`: Main nginx configuration
- `ssl/`: SSL certificates (when configured)
- `conf.d/`: Additional configuration files

## Configuration (Future)

When UI and API Gateway services are implemented, this will provide:
- HTTPS termination
- Load balancing
- Static file serving
- API routing

## Setup (Future)

```bash
# Test configuration
nginx -t

# Reload configuration
nginx -s reload
```