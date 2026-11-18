# Roadmap — Myths and Legends API (proyecto completo)

**Metodología:** Spec-Driven Development con GitHub Spec Kit (v1.4.2).
**Unidad de trabajo:** cada *sesión* = un ciclo `/speckit-specify → (clarify) → plan → tasks → (analyze) → implement → converge`, una rama `type/short-description`, un PR.
**Alcance:** API + frontend + deploy (decidido por Carlos).
**Fuentes:** `docs/superpowers/specs/2026-07-16-backend-phase1-hardening-design.md`, issues/PRs abiertos, `reviews/code-review-report.md`, CHANGELOG.

> Estado al 2026-11-18: PRs #73 (admin write-surface), #74 (spec refresh-tokens) y #75 (refresh-token flow) abiertos sin mergear. Issues abiertos: #26, #31, #54, #60, #67, #68, #69, #70.

---

## Fase 0 — Cimientos y base estable

Meta: `develop` con #73–#75 integrados, Spec Kit activo y docs al día. Nada de features nuevas hasta cerrar esto.

| Sesión | Qué | Entregable |
|---|---|---|
| **0.1** | Mergear `chore/add-speckit` | Spec Kit en `develop` |
| **0.2** | `/speckit-constitution`: principios del proyecto (TDD, security-first, minimalist, `def` sync + `Session` sync, error envelope `HTTPException`, conventional commits) | `.specify/memory/constitution.md` |
| **0.3** | Revisar y mergear en orden: #74 (spec) → #73 (superficie admin + move `entities/`→`domains/`) → #75 (refresh tokens, rebase). Suite completa verde tras cada merge | #67, #69, #70 cerrados (verificar contra el diff) |
| **0.4** | Sync de docs: `CLAUDE.md` y README desactualizados (mencionan `characters`, FastAPI 0.79, estructura vieja). CHANGELOG `[Unreleased]` | Docs = realidad |

## Fase 1 — Backend hardening (lo que falta de la spec Phase 1)

Meta: contrato de API estable y robusto para el frontend. Cada sesión es una feature Spec Kit.

| Sesión | Feature | Cierra | Notas |
|---|---|---|---|
| **1.1** | CHECK constraints en columnas enum (`Category.name`, `EntityType.name`, `Characteristic.type`, `EntityRelation.relation_type`, `Source.source_type`) | #68 | Migración Alembic, verificar up/down/up en Postgres real |
| **1.2** | Búsqueda con `pg_trgm` (extensión + índices GIN; dropear `ix_entity_description`) | #60 | Sin cambio de query, solo índices |
| **1.3** | Caching `fastapi-cache2` InMemory en GET de categories/entity-types (5–10 min) y sources (60 s) | #26 | Sin invalidación explícita |
| **1.4** | Leftovers #54: validar `sort` en countries/users, `max_length` en params libres, rate limit en `reset-password`, docstring del limiter, test de `Settings()` sin secretos, quitar default `POSTGRES_PASSWORD:-myths` | #54 | Una concern por commit |
| **1.5** | Decidir y (si aplica) implementar `DELETE /entities/{id}/relations/{relation_id}` | — | Decisión abierta en la spec |
| **1.6** | Tests E2E: ciclo de entidad+relaciones, ciclo de auth con refresh, límites de rate-limit | #31 | Depende de 1.1–1.5 |
| **1.7** | Cierre: nota "Fair Use" en `/docs`, CHANGELOG, tag `v0.2.0` | — | Hito: API congelada para frontend |

## Fase 2 — Frontend (Nuxt): catálogo público + panel admin

Meta: UI completa consumiendo la API. Decisión previa en 2.1: repo separado vs monorepo.

| Sesión | Qué |
|---|---|
| **2.1** | Spec del frontend (`/speckit-specify` + `/speckit-clarify`): alcance, repo, constitution propia, estética |
| **2.2** | Scaffold Nuxt + cliente tipado generado desde OpenAPI + CI básico |
| **2.3** | Catálogo público: listado paginado, detalle de entidad con relaciones, búsqueda |
| **2.4** | Auth: login, manejo de refresh token (httpOnly cookies, no localStorage), guards de ruta admin |
| **2.5** | Admin CRUD: entities y countries (incluye imágenes) |
| **2.6** | Admin CRUD: categories, entity-types, locations, sources y relaciones |
| **2.7** | Docs de API con tema propio + página de Fair Use |
| **2.8** | Tests E2E del frontend (Playwright), accesibilidad, performance, tag `v0.9.0` |

## Fase 3 — Deploy a producción (`space-server`, patrón `portfolio-api`)

| Sesión | Qué |
|---|---|
| **3.1** | Spec de deploy: estudiar patrón `portfolio-api`, definir topología (API, DB, frontend, proxy) |
| **3.2** | Docker/compose de producción: secretos, migraciones al arrancar, healthchecks, usuario no-root |
| **3.3** | CI/CD: GitHub Actions build → push → deploy, con tests como gate |
| **3.4** | Red y seguridad: HTTPS, proxy IPs confiables para `X-Forwarded-For`, CORS de producción, backups de Postgres |
| **3.5** | Observabilidad y smoke tests post-deploy, runbook, tag `v1.0.0` |

---

## Riesgos y decisiones abiertas

1. **Verificar el alcance real de #73/#75 contra los diffs** antes de marcar #67/#69/#70 como cerrados.
2. **Refresh tokens:** sesión única por usuario vs tabla de tokens (default de la spec: una sesión).
3. **Frontend:** ¿repo separado o monorepo? Condiciona CI y deploy.
4. **Spec Kit y specs previas:** `docs/superpowers/` queda como historial; lo nuevo vive en `specs/NNN-*/`.
5. **Dependencias viejas:** CLAUDE.md cita FastAPI 0.79 / SQLAlchemy 1.4, pero el plan habla de SQLAlchemy 2.0 y Pydantic v2. Confirmar versiones reales en 0.4.
