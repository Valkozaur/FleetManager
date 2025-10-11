# API Gateway Service

Future API gateway for FleetManager microservices.

This service will provide:
- Single entry point for all client requests
- Request routing and load balancing
- Authentication and authorization
- Rate limiting and caching
- API versioning

## Technology Stack (Planned)
- FastAPI or Flask
- NGINX for reverse proxy
- JWT for authentication
- Redis for caching

## Development Setup (Future)
```bash
pip install -r requirements.txt
python main.py
```

## Docker Build (Future)
```bash
docker build -t fleetmanager-api-gateway:local .
```