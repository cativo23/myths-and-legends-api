# The API of Myths and Legends // La API de Mitos y Leyendas

[https://leyendasdeelsalvador.com/](https://leyendasdeelsalvador.com/)

## Quick Start with Docker

### 1. Start All Services
```bash
docker-compose up -d
```

This starts:
- **API** - http://localhost:8080
- **PostgreSQL** - localhost:5432
- **pgAdmin** - http://localhost:8081
- **MailHog** (email testing) - http://localhost:8025

### 2. Access the API
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **API Root**: http://localhost:8080

### 3. View Logs
```bash
docker-compose logs -f api
docker-compose logs -f db
```

### 4. Stop Services
```bash
docker-compose down
```

## Local Development with venv

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Start PostgreSQL (Docker)
```bash
docker-compose up -d db
```

### 3. Run the API
```bash
uvicorn app.main:app --reload --port 8080
```

## Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Admin User | admin@example.com | admin123 |
| Database | myths | myths |
| pgAdmin | admin@example.com | admin123 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/api/v1/characters/` | List characters |
| POST | `/api/v1/characters/` | Create character |
| GET | `/api/v1/characters/{id}` | Get character |
| PUT | `/api/v1/characters/{id}` | Update character |
| DELETE | `/api/v1/characters/{id}` | Delete character |
| GET | `/api/v1/characters/search/` | Search characters |
| GET | `/api/v1/countries/` | List countries |
| POST | `/api/v1/countries/` | Create country |
| GET | `/api/v1/countries/{id}` | Get country |
| PUT | `/api/v1/countries/{id}` | Update country |
| DELETE | `/api/v1/countries/{id}` | Delete country |
| POST | `/api/v1/auth/login` | Login |

## Technologies

- FastAPI 0.135.2
- pydantic 2.12.5
- SQLAlchemy 2.0.48
- PostgreSQL 15
- pydantic-settings 2.13.1
