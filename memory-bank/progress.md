# Progress

_Actualizar cada vez que el proyecto evolucione: nuevas decisiones, features completadas, problemas encontrados. Un `progress.md` desactualizado deja de ser útil en días._

## Estado por feature

| Feature | Estado | Rama | PR |
|---|---|---|---|
| Gestor de incidencias | Implementado, tests en verde | `feature/incident-manager` | #1, abierto (sin mergear) |
| Gestor de inventario | Implementado, tests en verde, 29 criterios EARS verificados | `feature/inventory-manager` (sale de `incident-manager`) | #2, abierto, marcado "Ready to merge" |
| Infraestructura de agentes (banco de memoria, `AGENTS.md`, `.agents/rules`, `.agents/skills`) | En curso — este desarrollo | `feature/agent-memory-bank` (sale de `inventory-manager`) | pendiente de abrir |
| Auditoría de serialización de API | Implementadas y verificadas mejoras de respuesta para health, incidencias y stock | `feature/serialization-audit` (desde `main`) | — |
| Optimización de rendimiento/caching | Fase 2 implementa TTL e invalidación en catálogos, lazy loading de inventario/detalle y Map memoizado; verificación documentada | `feature/caching-optimisation` | — |
| Plan de telemetría | Fases 1-3: catálogo y 47 esquemas draft-07 con allowlists cerrados, envelope sin identidad autenticada, entrega de 18 tipos stream y 29 batch, controles de frecuencia y privacidad; contratos validados con AJV y reglas HTTP/reorden comprobadas con TestClient; diseño sin instrumentación en `docs/telemetry/` | `feature/telemetry-plan` | — |
| Captura de telemetría | Fase 1 completa y probada: stub `POST /telemetry/events` (`services/api/routers/telemetry.py`, modelo `TelemetryEvent` con el envelope cerrado de 10 campos de `event-schemas.json`, `userId` siempre null), loguea cantidad y `event_type`, responde `{"received": N}`, sin persistencia; lee `TELEMETRY_ENDPOINT`. Probado contra uvicorn: lote válido → 200 `{"received":2}`, campo extra → 422, `userId` no-null → 422. Fases 2 (TelemetryService) y 3 (instrumentación) pendientes | `feature/telemetry-capture` (sale de `telemetry-plan`) | — |
| `uis/website` (web corporativa pública) | Construida; pendiente de verificación en ejecución | `feature/agent-memory-bank` | — |
| `uis/backoffice` | Funcional: pestañas de Incidencias e Inventario, ambas consumiendo la API real | ya en `inventory-manager` | — |

## Orden de merge previsto

`incident-manager` → `inventory-manager` → `agent-memory-bank`, en ese orden, cada uno contra `main`. Como cada rama sale de la anterior, el diff de cada PR se limpia automáticamente en cuanto se mergea el anterior.

## Lo que ya funciona de verdad (no solo planeado)

- API FastAPI centralizada en `services/api`, con routers y storage separados por dominio (incidencias, inventario). Almacenamiento en memoria — sin base de datos todavía.
- `uis/backoffice`: React+Vite+TS, con navegación por pestañas entre Incidencias e Inventario, formularios de alta, filtros, detalle con historial de cambios (incidencias) y gestión de stock/locales/punto de reorden (inventario).
- `feature/caching-optimisation`: catálogos de artículos/locales cacheados por proceso con TTL e invalidación al crear; la entrada del backoffice difiere los módulos de inventario y detalle de incidencia.
- Banco de memoria con contexto de negocio y arquitectura, reglas de agente documentadas en `.agents/rules/`.

## Pendiente / próximos pasos

1. Crear `memory-bank/projectbrief.md`, `techContext.md`, `progress.md` (este archivo) — hecho.
2. Añadir al menos una skill formal en `.agents/skills/` para una tarea recurrente del flujo (scaffolding de un nuevo módulo de dominio en el backoffice).
3. Reescribir `AGENTS.md` con el flujo obligatorio pre-commit y las restricciones de edición.
4. Verificar `uis/website` en ejecución: web corporativa construida y alineada con `CONTEXT.md`.
5. Abrir PR de `feature/agent-memory-bank` → `main`, con capturas de `website` y `backoffice`.
6. Mergear los tres PRs en orden.
7. (Futuro, fuera de alcance de este desarrollo) Migrar el almacenamiento en memoria a una base de datos persistente.

## Problemas encontrados

- Al abrir el PR de inventario se creó por error contra el repo de la organización (`ai-engineering-company-project-monorepo`, sin sufijo) en vez del fork personal (`...-jheremydev`). Corregido reabriendo el PR en el repo correcto.
- `memory-bank/current-state.md` (heredado de la fase de incidencias) decía "todavía no existe implementación funcional" — quedó desactualizado en cuanto se completaron incidencias e inventario. Este `progress.md` lo sustituye como fuente de estado actual.
- La verificación interactiva desde el origen `127.0.0.1:5173` no puede consultar la API configurada en `localhost:8000` por la allowlist CORS existente; se documentó sin modificar configuración fuera del alcance.
