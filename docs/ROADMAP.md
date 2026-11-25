# Roadmap — Myths and Legends API (proyecto completo)

**Metodología:** Spec-Driven Development con GitHub Spec Kit (v1.4.2).
**Unidad de trabajo:** cada *sesión* = un ciclo `/speckit-specify → (clarify) → plan → tasks → (analyze) → implement → converge`, una rama `type/short-description`, un PR.
**Alcance:** API + frontend + deploy (decidido por Carlos).
**Fuentes:** `docs/superpowers/specs/2026-07-16-backend-phase1-hardening-design.md`, issues/PRs abiertos, `reviews/code-review-report.md`, CHANGELOG.

> Estado al 2026-11-25: Fase 0 completa; sesiones 1.1 a 1.4 hechas (#54 se cierra a mano tras el merge). Issues abiertos: #31, #54.

---

## Fase 0 — Cimientos y base estable

Meta: `develop` con #73–#75 integrados, Spec Kit activo y docs al día. Nada de features nuevas hasta cerrar esto. **Estado: completa.**

| Sesión | Qué | Entregable |
|---|---|---|
| **0.1** | Mergear `chore/add-speckit` | Spec Kit en `develop` |
| **0.2** | `/speckit-constitution`: principios del proyecto (TDD, security-first, minimalist, `def` sync + `Session` sync, error envelope `HTTPException`, conventional commits) | `.specify/memory/constitution.md` |
| **0.3** | Revisar y mergear en orden: #74 (spec) → #73 (superficie admin + move `entities/`→`domains/`) → #75 (refresh tokens, rebase). Suite completa verde tras cada merge | #67, #69, #70 cerrados (verificar contra el diff) |
| **0.4** | Sync de docs: `CLAUDE.md` y README desactualizados (mencionan `characters`, FastAPI 0.79, estructura vieja). CHANGELOG `[Unreleased]`. Incluye tope superior en `requirements.txt` y `test_cors` hermético | Docs = realidad |
| **0.5** | Tooling (chore; el reemplazo de passlib siguió el ciclo Spec Kit completo en `specs/001-replace-passlib-bcrypt/`): `./myths test` arreglado; artefactos de coverage root-owned limpiados (`./myths test` corre como `myths`); passlib reemplazado por `bcrypt` directo (sin monkeypatch); `requirements.in` (topes) + `requirements.txt` lock con hashes (`uv pip compile --universal`), instalado con `--require-hashes` en Docker y CI, con job `lock` que falla si está desactualizado | Tests y CI reproducibles |

## Fase 1 — Backend hardening (lo que falta de la spec Phase 1)

Meta: contrato de API estable y robusto para el frontend. Cada sesión es una feature Spec Kit.

| Sesión | Feature | Cierra | Notas |
|---|---|---|---|
| **1.1** ✅ | CHECK constraints en columnas enum (`Category.name`, `EntityType.name`, `Characteristic.type`, `EntityRelation.relation_type`, `Source.source_type`) | #68 | `specs/002-enum-check-constraints/`. Migración `ce04f762989d` verificada up/down/up en Postgres 15; aborta sin tocar datos si hay filas fuera del enum. Editar un enum ahora exige migración (un test lo detecta) |
| **1.2** ✅ | Búsqueda con `pg_trgm` (extensión + índices GIN; dropear `ix_entity_description`) | #60 | `specs/003-pg-trgm-search-indexes/`. Migración `b0ac58dc2755` verificada up/down/up en Postgres 15: `pg_trgm` + 4 GIN (`entity.name/description/origin`, `location.department`); se quedan `ix_entity_name` e `ix_location_department`. Un índice solo en `description` no sirve: el OR de `search()` necesita los tres. Con 80k filas sintéticas, `search()` pasa de Seq Scan (96 ms) a BitmapOr (0,6 ms) y el filtro de department de 30 ms a ~5 ms. Costo: más escritura en `entity`. Limitaciones en `specs/003-pg-trgm-search-indexes/research.md` |
| **1.3** ✅ | Caching `fastapi-cache2` InMemory en GET de categories/entity-types (5–10 min) y sources (60 s) | #26 | `specs/004-cache-reference-reads/`. 6 GET públicos (listado y detalle), TTL 300 s / 60 s, sin invalidación (dato viejo hasta el TTL, decidido con Carlos). Clave propia solo con parámetros validados (la clave por defecto incluye el repr de la `Session` y nunca da hit). `jinja2` es dependencia oculta de fastapi-cache2 (import de `starlette.templating`), fijada en `requirements.in`. Backend InMemory propio por instancia que no guarda páginas vacías (el de la librería solo borra vencidos al releer: `?page=N` crecía sin tope). Se quita `X-FastAPI-Cache`; quedan `Cache-Control` y `ETag`. Caché por worker; ETag cambia al reiniciar (`hash()` salado). `Cache-Control: no-cache` del cliente fuerza refresco (acotado por el rate limit) |
| **1.4** ✅ | Leftovers #54: validar `sort` en countries/users, `max_length` en params libres, rate limit en `reset-password`, docstring del limiter, test de `Settings()` sin secretos, quitar default `POSTGRES_PASSWORD:-myths` | #54 | `specs/005-hardening-leftovers-54/`. Verificado contra el código: 1 (rate limit), 3 (docstring) y 4 (test de `Settings()`) ya estaban resueltos. Hecho: `app/api/common/sorting.py` (`SortOrder` + `apply_sort`, NULL al final y desempate por `id`) usado por los 6 listados (categories, entity-types y sources refactorizados sin cambio de comportamiento); `sort`/`order` con `Literal` en countries, users y entities. Users y entities aceptaban `sort`/`order` y los ignoraban; ahora se aplican en SQL (entities pasa del orden por `id` al default documentado, `name`). `created_at` no se ofrece en countries/users: esos modelos no lo tienen (los ejemplos de la API lo anunciaban y caía a `id`). `relations` de countries se quitó: `Country` no tiene relaciones, todo valor daba 500. Compose: `POSTGRES_PASSWORD` obligatorio (`:?`) con step de CI que lo verifica; README corregido |
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
5. **Dependencias:** resuelto en 0.4 y 0.5 (FastAPI 0.135, SQLAlchemy 2.0, Pydantic; topes en `requirements.in`, versiones exactas en el lock `requirements.txt`). Lección: un tope solo por major no alcanzó (`fastapi-pagination` 0.15.16 rompió la app en CI); el lock con hashes lo previene. Pendiente: subir el tope de `fastapi-pagination` (`<0.15.16`) cuando salga un fix, con `-P fastapi-pagination`.
6. **Contenedor `api` corre como root** (el Dockerfile no define `USER`), lo que contradice Constitution II (least privilege) y origina artefactos root-owned en el bind mount. Sin sesión asignada; candidato a la fase de deploy (3.2) o a una sesión propia.
7. **Passwords con bytes NUL:** pasaron de rechazados (500 latente) a aceptados al reemplazar passlib; verificado y con test. Sin acción pendiente.
8. **`./myths psql` roto:** apunta al servicio `pgsql`, pero el servicio de compose se llama `db`. Hallado en 1.1 (se consultó con `docker compose exec -T db psql`). Sin sesión asignada; arreglo de una línea en `myths`.
9. **Migraciones en modo offline (`alembic --sql`)** no funcionan con `ce04f762989d`: el pre-chequeo necesita conexión. El proyecto no usa modo offline; se deja así (YAGNI).
10. **Índices trigram (1.2):** términos de menos de 3 caracteres no usan el índice; `%` y `_` en el término no se escapan (comodines); sin unificar acentos. Sin acción pendiente; si se quiere, `min_length=3` o escapado son cambios de API (otra sesión).
11. **`ix_location_department` difiere entre modelo y BD migrada:** en la BD migrada es compuesto `(department, municipality)`, pero el modelo declara índices simples (`index=True`). Hallado en 1.2; sin tocar. Revisar al alinear modelos y migraciones.
12. **Caché por worker (1.3):** con varios workers cada uno tiene su propia copia, con TTL y ETag independientes. Si se despliega con más de un worker (fase 3) y importa la coherencia, evaluar Redis (`fastapi-cache2` ya lo soporta) o invalidar al escribir. Sin acción pendiente hoy.
13. **Deuda de estilo/API detectada en 1.4 (sin tocar):** `datetime.utcnow()` está deprecado desde Python 3.12 (`app/utils.py`, `health.py`, default de `Entity.created_at`); `.dict()` de Pydantic V1 en `app/api/common/responses/api_responses.py` (usar `model_dump()`); `Optional[X]` en vez de `X | None` en varios archivos; `python-jose` tiene poco mantenimiento (evaluar `PyJWT` o `joserfc`). Sin sesión asignada.
14. **`Country` sin relaciones:** el parámetro `relations` se eliminó en 1.4. Si el frontend necesita países con sus entidades/ubicaciones, hay que modelar la relación (cambio de modelo y migración) en una sesión propia.
