# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Database Migrations

- No new migrations required

## [0.1.0] - 2026-04-02

### Added

- Public and admin OpenAPI documentation (`/docs` and `/admin/docs`)
- OAuth2 authentication schema for Swagger/ReDoc
- Domain-driven project structure
- Comprehensive API descriptions, examples, and response schemas
- Rate limiting middleware
- Security headers middleware (CSP, X-Frame-Options, etc.)
- Request ID middleware for tracing
- Entity management (entities, categories, entity_types, locations, sources)
- Country and character management
- User authentication with JWT tokens
- Health check endpoints
- Image upload and serving functionality
- PostgreSQL database with Alembic migrations
- Docker and Docker Compose configuration
- CI/CD pipeline with GitHub Actions

### Changed

- Refactored from flat structure to domain-driven architecture
- Updated Pydantic schemas to v2
- Improved error handling with custom exception classes

### Fixed

- Fixed images router prefix duplication
- Fixed Pydantic deprecation warnings
- Fixed CI lint and test failures

### Database Migrations

- `4758804d863e_add_entities_tables.py` - Add entities, categories, entity_types, locations, sources tables
- `d077d52b1166_remove_characters_table.py` - Remove deprecated characters table
- `d15753a0d7f5_add_characters.py` - Add characters with new structure
- `53cafc_add_unique_fields_on_character_s_name.py` - Add unique constraints
