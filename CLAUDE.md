# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based REST API called "The API of Myths and Legends" that manages mythological characters and countries. It uses PostgreSQL as the database backend with SQLAlchemy ORM and implements a service-layer architecture.

## Architecture Structure

- **app/main.py**: Main FastAPI application entry point with CORS middleware and pagination
- **app/api/v1/**: API version 1 with endpoints, services, models, schemas, and enums
- **app/api/v1/endpoints/**: API route definitions (characters, countries, images, login, home)
- **app/api/v1/services/**: Business logic layer with CRUD operations (character_service, country_service, etc.)
- **app/api/v1/models/**: SQLAlchemy database models (Character, Country, User)
- **app/api/v1/schemas/**: Pydantic data transfer objects for request/response validation
- **app/api/common/**: Shared utilities including base service class and exception handlers
- **app/core/config.py**: Configuration settings using Pydantic BaseSettings
- **app/db/base_class.py**: Base SQLAlchemy class with automatic table naming

## Development Commands

### Starting the Application
- `./myths up` - Start the application in foreground
- `./myths up -d` - Start the application in background
- `./myths stop` - Stop the application
- `./myths restart` - Restart the application

### Database Operations
- `./myths alembic revision --autogenerate -m "migration message"` - Create a new migration
- `./myths alembic upgrade head` - Apply all pending migrations
- `./myths psql` - Connect to PostgreSQL database directly

### Testing
- `./myths test` - Run tests

### Container Operations
- `./myths shell` or `./myths bash` - Access application container shell
- `./myths root-shell` - Access application container as root

### Development Utilities
- `./myths python ...` - Execute Python commands in the container
- `./myths build --no-cache` - Rebuild all containers

## Key Technologies

- FastAPI (0.79.0) - Modern Python web framework
- SQLAlchemy (1.4.40) - Database ORM
- PostgreSQL - Primary database
- Docker & Docker Compose - Containerization
- Alembic - Database migrations
- Pydantic - Data validation and settings management
- fastapi-pagination - Pagination support

## API Structure

The API follows a service-oriented architecture with:
- **Endpoints** in `app/api/v1/endpoints/` - Handle HTTP requests and responses
- **Services** in `app/api/v1/services/` - Implement business logic using the CRUDBaseService
- **Models** in `app/api/v1/models/` - Define database schema
- **Schemas** in `app/api/v1/schemas/` - Define API request/response structures

## Common Patterns

- Service classes extend `CRUDBaseService` for standard CRUD operations
- Dependency injection using FastAPI's Depends for database sessions
- Form handling with `schema.as_form` pattern for multipart uploads
- Custom response functions for standardized API responses (created, updated, deleted, etc.)
- Exception handling with custom exception classes
- Image upload functionality integrated into character creation/update

## Environment Configuration

Configuration is managed through environment variables defined in `.env` file and accessed via `app/core/config.py`. Key settings include database connection, server host/port, and security configurations.