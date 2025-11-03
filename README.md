# FleetManager

A microservice-based logistics fleet management system that processes emails to extract logistics orders and data.

## 🚀 Features

- **Microservice Architecture**: Scalable service-oriented design
- **Automated Email Processing**: Polls Gmail for new emails automatically
- **AI-Powered Classification**: Uses Google Gemini AI to classify emails
- **Logistics Data Extraction**: Extracts order details, addresses, and contact info
- **Geocoding**: Converts addresses to coordinates using Google Maps API
- **Google Sheets Integration**: Stores processed data in Google Sheets
- **Dockerized**: Fully containerized for easy deployment
- **CI/CD Pipeline**: Automated testing and deployment via GitHub Actions

## 📚 Documentation

### Service Documentation
- **[Email Processor](./services/email-processor/README.md)** - Email processing service details
- **[Database Migration](./services/database-migration/)** - Database schema management
- **[Database Models](./services/database-models/)** - Shared ORM models

### Shared Components
- **[Database Models](./services/database-models/)** - Shared ORM models using SQLAlchemy
- **[Migrations](./services/database-models/migrations/)** - Alembic database migrations

## 🏗️ Architecture

### Microservice Structure

```
FleetManager/
├── services/                       # Microservices
│   ├── database-models/           # Shared ORM models 📦
│   ├── database-migration/        # Schema migrations ✅
│   └── email-processor/           # Gmail processing service ✅
├── tests/                         # Integration & e2e tests
└── credentials/                   # Service account credentials
```

### Current Services

**Database Models** (📦 Shared)
- SQLAlchemy ORM models
- Shared across all services via uv workspace

**Database Migration** (✅ Active)
- Alembic-based schema migrations
- Idempotent migration runner
- Runs on every deployment

**Email Processor** (✅ Active)
- Gmail polling and email classification
- AI-powered logistics data extraction
- PostgreSQL storage with geocoding

### Future Services

**Web UI** (🚧 Planned)
- Fleet management dashboard
- Order tracking and analytics
- User interface for fleet operations

**API Gateway** (🚧 Planned)
- REST API for fleet operations
- Authentication and authorization
- GraphQL interface

## 🔧 Technology Stack

- **Language**: Python 3.13
- **Package Manager**: uv (fast Python package manager)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Container**: Docker (multi-stage builds with uv)
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Registry**: GitHub Container Registry
- **APIs**: Gmail, Google Gemini AI, Google Maps, Google Sheets

## 📦 Project Structure

```
FleetManager/
├── services/                    # UV workspace services
│   ├── database-models/        # 📦 Shared ORM models
│   │   ├── database_models/
│   │   │   ├── __init__.py     # Exports Base, Order
│   │   │   └── orm.py          # SQLAlchemy models
│   │   ├── migrations/         # Alembic migrations
│   │   └── pyproject.toml
│   ├── database-migration/     # ✅ Migration runner
│   │   ├── main.py             # Migration script
│   │   ├── alembic.ini
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── email-processor/        # ✅ Email processing
│       ├── main.py
│       ├── clients/            # External API clients
│       ├── models/             # Pydantic models
│       ├── pipeline/           # Processing pipeline
│       ├── services/           # Business logic
│       ├── Dockerfile
│       └── pyproject.toml
├── tests/                      # Integration & e2e tests
├── .github/workflows/          # CI/CD pipeline
├── docker-compose.yml          # Local development
├── docker-compose.prod.yml     # Production deployment
├── pyproject.toml              # UV workspace config
└── uv.lock                     # Dependency lockfile
```

## 🚀 Quick Start

### Running with Docker Compose

1. **Setup Environment**
   ```bash
   # Clone repository
   git clone https://github.com/Valkozaur/FleetManager.git
   cd FleetManager

   # Add credentials
   mkdir -p .credentials
   cp /path/to/service-account.json .credentials/
   
   # Create .env file
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run All Services**
   ```bash
   docker-compose up
   # Services will start in order: db → database-migration → email-processor
   ```

3. **Run Specific Service**
   ```bash
   docker-compose up email-processor
   ```

### Local Development

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync workspace dependencies
uv sync

# Run database migrations
cd services/database-migration
uv run python main.py

# Run email processor
cd services/email-processor
uv run python main.py
```

## 🔄 Email Processing Workflow

1. **Database Migration**: Alembic applies schema changes (idempotent)
2. **Email Polling**: Checks Gmail for new emails since last check
3. **Classification**: Gemini AI determines if email contains order data
4. **Extraction**: Extracts logistics details (addresses, dates, cargo info)
5. **Geocoding**: Converts addresses to coordinates via Google Maps API
6. **Storage**: Saves to PostgreSQL database
7. **Logging**: Records all operations with structured logging

## 📊 Service Management

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f email-processor
docker-compose logs -f database-migration

# Build and run services
docker-compose up --build

# Stop services
docker-compose down

# Run migrations manually
docker-compose run --rm database-migration

# Access database
docker-compose exec db psql -U fleetmanager -d fleetmanager
```

## 🔮 Roadmap

### Completed ✅
- UV workspace monorepo with shared database-models
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations with automatic deployment
- Email processing service with AI classification
- Docker Compose orchestration with health checks
- CI/CD pipeline with GitHub Actions

### In Progress 🚧
- OpenTelemetry observability integration
- Enhanced error handling and retry logic
- Service-level metrics and monitoring

### Future Plans 📋
- Web UI for order management
- REST API gateway
- Real-time order tracking
- Analytics dashboard
- Multi-tenant support

## 🆘 Support

- **Issues**: Open a GitHub Issue
- **Questions**: Use GitHub Discussions
- **Service Documentation**: Check individual service README files

## 📝 License

MIT License - See LICENSE file for details

## 👤 Maintainer

**Valkozaur**
- GitHub: [@Valkozaur](https://github.com/Valkozaur)

---

**Version**: 4.0 (UV Workspace + PostgreSQL)
**Last Updated**: November 2025
**Status**: Production Ready ✅
