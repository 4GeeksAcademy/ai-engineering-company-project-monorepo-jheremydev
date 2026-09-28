# Tech Context

## Stack real (verificado en el código, no de memoria)

### Backend — `services/api`

- **FastAPI** + `uvicorn[standard]` (ver `services/api/requirements.txt`).
- **Almacenamiento actual: en memoria** (listas Python en `services/api/storage/incidents.py` e `inventory.py`). No hay driver de base de datos instalado todavía — cualquier mención a PostgreSQL en documentación anterior es un objetivo futuro, no el estado real.
- Un único API centralizado, organizado por routers/módulos de dominio (`models/`, `routers/`, `storage/` por dominio), sin microservicios independientes por gestor.
- Scripts de verificación end-to-end por dominio: `verify_incidents.py`, `verify_inventory.py`.

### Frontend — `uis/backoffice` y `uis/website`

- **React 19 + TypeScript + Vite**, monorepo gestionado con **npm workspaces** (`workspaces: ["uis/*", "packages/*"]` en el `package.json` raíz).
- Tipos compartidos entre frontend y contrato de API en `packages/shared/types` (`@repo/shared-types`).
- Cliente API por dominio: `uis/backoffice/src/api/{incidents,inventory}.ts`, con un `client.ts` compartido para fetch/errores.
- Estilo: fuentes Manrope (texto) + Georgia (títulos) + DM Mono (etiquetas), paleta definida en `App.css` (`--ink`, `--muted`, `--line`, `--paper`, `--terracotta`, `--teal`).

### Metodología

- **Spec Driven Development** para cada feature: `specify → plan → tasks → implement → verify`, documentado en `specs/<feature>/{spec,plan,tasks}.md`.

## Decisiones de arquitectura tomadas

| Decisión | Dónde vive | Regla que la formaliza |
|---|---|---|
| API centralizada en `services/`, sin microservicio por dominio | `services/api/` | `.agents/rules/api-centralizada-fastapi.md` |
| Orquestación local en `docker-compose.yml` en la raíz; el resto de infra en `infra/` | raíz + `infra/` | `.agents/rules/docker-compose-en-raiz.md` |
| Cada app/servicio/agente/pipeline documenta su propia subcarpeta con README | `uis/**`, `services/**`, `agents/**`, `data/pipelines/**` | `.agents/rules/documentacion-por-componente.md` |
| Peticiones a la API organizadas por dominio, un archivo por dominio + cliente compartido | `uis/backoffice/src/api/**`, `services/api/**` | `.agents/rules/separacion-por-dominio.md` |
| Cada agente vive en su propia subcarpeta con `agent.py` + README + `tests/` | `agents/**` | `.agents/rules/estructura-de-agente.md` |
| Cada skill de producto vive en carpeta propia con `SKILL.md` | `skills/**` | `.agents/rules/estructura-de-skill.md` |
| El stock de inventario nunca se edita directamente, solo se deriva de movimientos | `services/api` (inventario) | invariante verificado en tests y `verify_inventory.py` |

## Restricciones técnicas

- No se introducen dependencias nuevas sin justificar su necesidad frente a la arquitectura existente (`memory-bank/architecture.md`).
- `.agents/` (reglas y skills de configuración del agente) es distinto de `/agents` y `/skills` en la raíz (código de producto de módulos posteriores) — no deben confundirse.
- Todo cambio de requisito durante el desarrollo se resuelve editando primero `spec.md`, luego `plan.md`, y regenerando solo las tareas afectadas — nunca parcheando código antes de tocar el spec.
