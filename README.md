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
- **[Web UI](./services/ui/README.md)** - Future web interface
- **[API Gateway](./services/api-gateway/README.md)** - Future API gateway

### Shared Components
- **[Shared Models](./shared/models/)** - Common data models
- **[Shared Utilities](./shared/utils/)** - Common utilities
- **[Shared Configuration](./shared/config/)** - Common configuration

## 🏗️ Architecture

### Microservice Structure

```
FleetManager/
├── services/                       # Microservices
│   ├── email-processor/           # Gmail processing service ✅
│   ├── ui/                        # Future web interface 🚧
│   └── api-gateway/               # Future API gateway 🚧
├── shared/                        # Shared components
│   ├── models/                    # Common data models
│   ├── utils/                     # Shared utilities
│   └── config/                    # Shared configuration
├── infrastructure/                # Infrastructure setup
│   └── nginx/                     # Reverse proxy config
└── tests/                         # Integration & e2e tests
```

### Current Services

**Email Processor** (✅ Active)
- Gmail polling and email classification
- AI-powered logistics data extraction
- Geocoding and Google Sheets integration

### Future Services

**Web UI** (🚧 Planned)
- Fleet management dashboard
- Order tracking and analytics
- User interface for fleet operations

**API Gateway** (🚧 Planned)
- Single entry point for all services
- Authentication and authorization
- Request routing and load balancing

## 🔧 Technology Stack

- **Language**: Python 3.13
- **Container**: Docker (multi-stage builds)
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions
- **Registry**: GitHub Container Registry
- **APIs**: Gmail, Google Sheets, Google Maps, Google Gemini

## 📦 Project Structure

```
FleetManager/
├── services/                    # Microservices
│   ├── email-processor/        # ✅ Email processing service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── src/
│   │   └── tests/
│   ├── ui/                     # 🚧 Future web interface
│   └── api-gateway/            # 🚧 Future API gateway
├── shared/                     # Shared components
│   ├── models/                 # Common data models
│   ├── utils/                  # Shared utilities
│   └── config/                 # Shared configuration
├── infrastructure/             # Infrastructure setup
│   └── nginx/                  # Reverse proxy configuration
├── tests/                      # Integration tests
├── .github/workflows/          # CI/CD pipeline
├── docker-compose.yml          # Service orchestration
└── README.md                   # This file
```

## 🚀 Quick Start

### Running the Email Processor Service

1. **Setup Environment**
   ```bash
   # Clone repository
   git clone https://github.com/Valkozaur/FleetManager.git
   cd FleetManager

   # Add credentials
   mkdir -p credentials
   cp /path/to/credentials.json credentials/
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up email-processor
   ```

3. **Run Single Service**
   ```bash
   cd services/email-processor
   docker build -t email-processor:local .
   docker run -v $(pwd)/../../credentials:/app/credentials --env-file .env email-processor:local
   ```

### Local Development

```bash
# Install service dependencies
cd services/email-processor
pip install -r requirements.txt

# Run locally
python src/orders/poller/main.py
```

## 🔄 Email Processing Workflow

1. **Email Polling**: Checks Gmail for new emails
2. **Classification**: AI determines if email is logistics-related
3. **Extraction**: Extracts sender, receiver, addresses, contacts
4. **Geocoding**: Converts addresses to lat/long coordinates
5. **Storage**: Saves structured data to Google Sheets
6. **Logging**: Records all operations for monitoring

## 📊 Service Management

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f email-processor

# Build and run services
docker-compose up --build

# Stop services
docker-compose down
```

## 🔮 Roadmap

### Completed ✅
- Microservice architecture foundation
- Email processing service containerization
- Shared components structure
- Service orchestration with Docker Compose

### In Progress 🚧
- Web UI service development
- API gateway implementation
- Service-to-service communication

### Future Plans 📋
- Real-time order tracking
- Analytics dashboard
- Mobile app integration
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

**Version**: 3.0 (Microservice Architecture)
**Last Updated**: October 2025
**Status**: Production Ready ✅
