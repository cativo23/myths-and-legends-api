# Myths and Legends API

> A RESTful API for managing mythological characters and folklore data.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135.2-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org/)

[Spanish version](#espanol)

---

## Overview

The Myths and Legends API is a production-ready RESTful service built with FastAPI. It provides endpoints for managing mythological characters, countries, and related folklore data with full CRUD operations, authentication, and image upload support.

## Features

- RESTful API design with OpenAPI documentation
- JWT-based authentication
- PostgreSQL database with SQLAlchemy ORM
- Database migrations with Alembic
- File upload support for character images
- Email notifications support
- Docker-based development environment
- Hot reload for development

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone git@github.com:cativo23/myths-and-legends-api.git
   cd myths-and-legends-api
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   ./myths alembic upgrade head
   ```

5. **Access the API**
   - Swagger UI: http://localhost:8080/docs
   - ReDoc: http://localhost:8080/redoc
   - API Root: http://localhost:8080

### Local Development

1. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start database**
   ```bash
   docker-compose up -d db pgadmin
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the API**
   ```bash
   uvicorn app.main:app --reload --port 8080
   ```

## Configuration

Copy `.env.example` to `.env` and configure the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_PORT` | API port | `8080` |
| `SECRET_KEY` | JWT secret key | Auto-generated |
| `POSTGRES_HOST` | Database host | `db` |
| `POSTGRES_USER` | Database user | `myths` |
| `POSTGRES_PASSWORD` | Database password | `myths` |
| `POSTGRES_DB` | Database name | `myths` |
| `PGADMIN_EMAIL` | pgAdmin email | `admin@example.com` |
| `PGADMIN_PASSWORD` | pgAdmin password | `admin123` |

## API Endpoints

### Entities (Mythological Characters, Creatures, Places, Objects)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/entities/` | List entities (paginated, filterable) |
| GET | `/api/v1/entities/search?q=term` | Search entities by name/description |
| GET | `/api/v1/entities/{id}` | Get entity with full relations |
| GET | `/api/v1/entities/{id}/relations` | Get entity relations |
| POST | `/api/v1/entities/` | Create entity (admin) |
| PUT | `/api/v1/entities/{id}` | Update entity (admin) |
| DELETE | `/api/v1/entities/{id}` | Delete entity (admin) |

### Countries

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/countries/` | List all countries |
| GET | `/api/v1/countries/{id}` | Get country by ID |
| POST | `/api/v1/countries/` | Create country (admin) |
| PUT | `/api/v1/countries/{id}` | Update country (admin) |
| DELETE | `/api/v1/countries/{id}` | Delete country (admin) |

### Categories, Entity Types, Locations, Sources

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/categories/` | List categories |
| GET | `/api/v1/entity-types/` | List entity types |
| GET | `/api/v1/locations/` | List locations (filterable by department) |
| GET | `/api/v1/sources/` | List sources (filterable by type) |

### Authentication & Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/password-recovery/{email}` | Request password reset |
| POST | `/api/v1/auth/reset-password/` | Reset password with token |
| GET/POST/PUT/DELETE | `/api/v1/users/` | User management (admin only) |

### Health & Images

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Basic health check |
| GET | `/api/v1/health/live` | Liveness probe |
| GET | `/api/v1/health/ready` | Readiness probe (checks DB) |
| GET | `/api/v1/images/{filename}` | Serve image file |

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Admin User | admin@example.com | (set via `FIRST_SUPERUSER_PASSWORD`) |
| Database | myths | (set via `POSTGRES_PASSWORD`) |
| pgAdmin | admin@example.com | admin123 |

> **Note**: `SECRET_KEY`, `POSTGRES_PASSWORD`, and `FIRST_SUPERUSER_PASSWORD` are required environment variables with no default values. See `.env.example`.

## Development Commands

The `./myths` script provides convenient commands:

```bash
./myths up              # Start all services
./myths up -d           # Start in background
./myths stop            # Stop all services
./myths restart         # Restart services
./myths shell           # Open shell in API container
./myths alembic ...     # Run Alembic commands
./myths python ...      # Run Python in container
./myths test            # Run tests
```

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── domains/            # Domain-driven modules
│   │   │   │   ├── auth/           # Authentication (login, password reset)
│   │   │   │   ├── countries/      # Country CRUD
│   │   │   │   ├── health/         # Health check endpoints
│   │   │   │   ├── home/           # API root endpoint
│   │   │   │   ├── images/         # Image serving
│   │   │   │   └── users/          # User management
│   │   │   ├── entities/           # Entity domain (mythological items)
│   │   │   │   ├── endpoints/      # Entity-related routes
│   │   │   │   ├── models/         # Entity DB models
│   │   │   │   ├── schemas/        # Pydantic schemas
│   │   │   │   └── services/       # Business logic
│   │   │   └── shared/             # Shared deps (auth, db)
│   │   └── common/
│   │       ├── middleware/         # Rate limiting, security headers, request ID
│   │       ├── services/           # Base CRUD service
│   │       ├── responses/          # Response helpers
│   │       └── exceptions/         # Custom exceptions
│   ├── core/
│   │   ├── config.py               # Application settings
│   │   ├── security.py             # JWT, password hashing
│   │   ├── logging_config.py       # Structured JSON logging
│   │   └── openapi_config.py       # Public/admin OpenAPI separation
│   └── db/
│       ├── session.py              # Database session
│       └── base_class.py           # SQLAlchemy base
├── alembic/                        # Database migrations
├── tests/                          # Test suite
├── docker-compose.yml
├── requirements.txt
└── ./myths                         # Development script
```

## Technology Stack

- **Framework:** FastAPI 0.135.2
- **Language:** Python 3.10+
- **Validation:** Pydantic 2.x
- **ORM:** SQLAlchemy 2.x
- **Database:** PostgreSQL 15
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose)
- **Password Hashing:** bcrypt
- **Containerization:** Docker & Docker Compose

## Testing

```bash
# Run tests in container
./myths test

# Run tests locally
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Release Process

This project uses automatic releases via GitHub Actions. To create a new release:

1. **Create a release branch** from `main`:
   ```bash
   git checkout main
   git pull
   git checkout -b release/v0.1.0
   ```

2. **Update CHANGELOG.md** with your release notes under the version heading:
   ```markdown
   ## [0.1.0] - 2026-04-02

   ### Added
   - New feature description

   ### Fixed
   - Bug fix description
   ```

3. **Push and create PR**:
   ```bash
   git push origin release/v0.1.0
   ```
   Then open a PR from `release/v0.1.0` to `main`.

4. **Merge the PR** — GitHub Actions will automatically:
   - Extract version from branch name
   - Parse release notes from CHANGELOG.md
   - Create a GitHub Release with the notes
   - Mark as prerelease if version is `v0.x.y`

**Branch naming:** `release/v0.1.0` or `release/0.1.0` (both supported)

## License

This project is licensed under the MIT License.

---

## Español

> API RESTful para gestionar personajes mitológicos y datos de folclore.

### Inicio Rápido

1. **Clonar el repositorio**
   ```bash
   git clone git@github.com:cativo23/myths-and-legends-api.git
   cd myths-and-legends-api
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   ```

3. **Iniciar servicios**
   ```bash
   docker-compose up -d
   ./myths alembic upgrade head
   ```

4. **Acceder a la API**
   - Swagger UI: http://localhost:8080/docs
   - API: http://localhost:8080

### Documentación

- [Documentación en inglés](#overview)
- [Documentación de la API](http://localhost:8080/docs)

### Proceso de Release

Este proyecto usa releases automáticos vía GitHub Actions. Para crear un nuevo release:

1. **Crear rama de release** desde `main`:
   ```bash
   git checkout main
   git pull
   git checkout -b release/v0.1.0
   ```

2. **Actualizar CHANGELOG.md** con las notas del release:
   ```markdown
   ## [0.1.0] - 2026-04-02

   ### Added
   - Descripción de nueva funcionalidad

   ### Fixed
   - Descripción de corrección
   ```

3. **Push y crear PR**:
   ```bash
   git push origin release/v0.1.0
   ```
   Luego abrí un PR de `release/v0.1.0` a `main`.

4. **Merge del PR** — GitHub Actions automáticamente:
   - Extrae la versión del nombre de la rama
   - Parsea las notas desde CHANGELOG.md
   - Crea un GitHub Release con las notas
   - Lo marca como prerelease si la versión es `v0.x.y`

**Nombre de rama:** `release/v0.1.0` o `release/0.1.0` (ambos soportados)
