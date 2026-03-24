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

### Characters

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/characters/` | List all characters (paginated) |
| POST | `/api/v1/characters/` | Create a new character |
| GET | `/api/v1/characters/{id}` | Get character by ID |
| PUT | `/api/v1/characters/{id}` | Update character |
| DELETE | `/api/v1/characters/{id}` | Delete character |
| GET | `/api/v1/characters/search/` | Search characters by name |

### Countries

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/countries/` | List all countries |
| POST | `/api/v1/countries/` | Create a new country |
| GET | `/api/v1/countries/{id}` | Get country by ID |
| PUT | `/api/v1/countries/{id}` | Update country |
| DELETE | `/api/v1/countries/{id}` | Delete country |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user |

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Admin User | admin@example.com | admin123 |
| Database | myths | myths |
| pgAdmin | admin@example.com | admin123 |

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
│   │   │   ├── endpoints/      # API route handlers
│   │   │   ├── services/       # Business logic layer
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── enums/          # Enum definitions
│   │   └── common/
│   │       ├── services/       # Base services
│   │       ├── schemas/        # Common schemas
│   │       └── responses/      # Response helpers
│   ├── core/
│   │   └── config.py           # Application settings
│   └── db/
│       ├── session.py          # Database session
│       └── base_class.py       # SQLAlchemy base
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── docker-compose.yml
├── requirements.txt
└── ./myths                     # Development script
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
