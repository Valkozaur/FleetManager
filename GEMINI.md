# FleetManager Project Overview

This document provides a comprehensive overview of the FleetManager project, intended for developers and future AI assistants.

## Project Purpose and Architecture

FleetManager is a microservice-based logistics fleet management system designed to automate the processing of logistics orders from emails. The system is built with a scalable, service-oriented architecture and is fully containerized using Docker.

The primary service, `email-processor`, is responsible for the following workflow:

1.  **Email Polling**: Fetches new emails from a designated Gmail account.
2.  **AI-Powered Classification**: Uses the Gemini API to classify emails as either logistics-related or not.
3.  **Logistics Data Extraction**: If an email is classified as a logistics order, the system uses the Gemini API to extract key information such as sender, receiver, addresses, and contact details.
4.  **Address Cleaning**: The extracted addresses are cleaned and standardized using the Gemini API.
5.  **Geocoding**: The cleaned addresses are converted into geographic coordinates (latitude and longitude) using the Google Maps API.
6.  **Data Storage**: The processed data is saved to a Google Sheet and PostgreSQL for easy access and analysis.

The project is designed to be extensible, with plans for a future web UI and an API gateway.

## Google Authentication with OAuth2-Proxy

The project uses [OAuth2-Proxy](https://oauth2-proxy.github.io/oauth2-proxy/) to protect the services with Google Authentication. The `oauth2-proxy` service is configured to use Google as the identity provider. When a user tries to access a protected service, they are redirected to Google for authentication. After successful authentication, the user is redirected back to the application.

### Configuration

To enable Google Authentication, you need to create a new project in the [Google Cloud Console](https://console.cloud.google.com/) and create new OAuth 2.0 credentials. You will need to provide the following environment variables in the `.env` file:

- `OAUTH2_PROXY_CLIENT_ID`: The client ID of your OAuth 2.0 credentials.
- `OAUTH2_PROXY_CLIENT_SECRET`: The client secret of your OAuth 2.0 credentials.
- `OAUTH2_PROXY_COOKIE_SECRET`: A secret to encrypt the session cookie. You can generate a new secret with the following command:

```bash
python -c 'import os,base64; print(base64.b64encode(os.urandom(16)).decode("ascii"))'
```

Create a `.env` file in the root of the project and add the environment variables listed above. You can use the `.env.example` file as a template.

## Technology Stack

*   **Language**: Python 3.13
*   **AI**: Google Gemini API
*   **APIs**: Gmail API, Google Maps API, Google Sheets API
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy
*   **Database Migrations**: Alembic
*   **Containerization**: Docker, Docker Compose
*   **CI/CD**: GitHub Actions

## Building and Running the Project

### Prerequisites

*   Docker and Docker Compose
*   Google Cloud project with the following APIs enabled:
    *   Gmail API
    *   Google Maps API
    *   Google Sheets API
*   A service account with credentials (`credentials.json`)
*   A `.env` file with the necessary environment variables (see `.env.example`)

### Running with Docker Compose

The recommended way to run the project is with Docker Compose.

1.  **Place Credentials**: Place your `credentials.json` file in the `.credentials` directory.
2.  **Create `.env` file**: Copy `.env.example` to `.env` and fill in the required values.
3.  **Build and Run**:
    ```bash
    docker-compose up --build database-migration email-processor
    ```

### Running Tests

The project uses `pytest` for testing. To run the tests, you can use the following command:

```bash
python -m pytest
```

## Development Conventions

*   **Code Style**: The project follows the PEP 8 style guide for Python code.
*   **Type Hinting**: All functions and methods should have type hints.
*   **Logging**: The project uses the `structlog` library for structured logging.
*   **Modularity**: The code is organized into modules and services, with a clear separation of concerns.
*   **Pipeline Architecture**: The `email-processor` service uses a pipeline pattern to process emails, with each step in the pipeline being a separate class.
