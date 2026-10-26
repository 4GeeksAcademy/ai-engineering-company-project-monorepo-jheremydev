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
| Persistencia de telemetría | Fase 1 aplicada y verificada en Supabase por el desarrollador: 10 columnas, 3 índices + PK, trigger append-only, RLS, service_role SELECT/INSERT y comprobaciones de allowlist correctas. Fase 2 implementada: envelope laxo, TelemetryEvent.model_validate por item sin modificar el modelo, validación adicional contra JSON Schema con formatos, properties → tags y único bulk insert PostgREST; 200 received/stored/rejected, 422 para envelope inválido y 503 explícito para fallo de almacenamiento (autorizado). Configuración API de Compose/Dockerfile autorizada para incluir el schema; variables SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY solo backend. Verificación HTTP local con Supabase simulado: lote mixto de 9 → stored=2/rejected=7 con una llamada bulk; vacíos/todos inválidos sin llamada; 422 envelope y JSON malformado; 503 conflicto/conexión/credenciales ausentes. Sintaxis Pylance y YAML OK. Frontend y modelo intactos. No probada todavía la inserción remota desde la API ni la imagen Docker; Fase 3 pendiente de confirmación explícita | `feature/telemetry-storage` (desde `telemetry-capture`) | — |
| Captura de telemetría | Fase 1 completa y probada: stub `POST /telemetry/events` (`services/api/routers/telemetry.py`, modelo `TelemetryEvent` con el envelope cerrado de 10 campos de `event-schemas.json`, `userId` siempre null), loguea cantidad y `event_type`, responde `{"received": N}`, sin persistencia; lee `TELEMETRY_ENDPOINT`. Probado contra uvicorn: lote válido → 200 `{"received":2}`, campo extra → 422, `userId` no-null → 422. Fase 2 completa y probada en navegador: `uis/backoffice/src/services/telemetry.ts` (cola en memoria, lote a 20 eventos → envío inmediato 200 `{"received":20}`, 1 evento → envío a ~10 s con timestamp de captura; reintentos 503 a 0/1/3 s y éxito al tercero; lote siempre fallido descartado tras 3 intentos; `sendBeacon` en `visibilitychange` hidden → 200 `{"received":3}`; `trackRequest` propaga su `requestId` y `track()` envía null), `TELEMETRY_SCHEMA_VERSION` en `@repo/shared-types`, `envPrefix` `NEXT_PUBLIC_` y proxy `/telemetry` en Vite. Fase 3 completa y probada (sin commit): backend emite los 7 eventos obligatorios de inventario con `source=api` (`services/api/storage/telemetry.py`, middleware y handler de validación en `main.py`, `routers/inventory.py`) hacia `TELEMETRY_ENDPOINT`; frontend instrumenta errores globales, rendimiento de peticiones, `navigation.section_viewed`, formularios (`useFormTelemetry`), incidencias e inventario; allowlist por `event_type` descarta antes de encolar; `environment` desde `import.meta.env.MODE`. Probado: recorrido E2E en navegador → 4 lotes POST `/telemetry/events` 200 con `received` = enviados (65 eventos, 0 inválidos con jsonschema draft-07); eventos `api` validados contra el schema y recibidos por el stub; 23 unit tests API OK; `npm run build` y `eslint` OK. `verify_*.py` no ejecutables en `.venv-1` (TestClient sin `httpx2`). Pendiente: propagar `formAttemptId` a eventos de backend | `feature/telemetry-capture` (sale de `telemetry-plan`) | — |
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

- Fase 3 verificada por el desarrollador en Supabase: inventory.movement_created entrada eventId 1b685428-5403-4438-97cd-cd1cd63da946 (quantity=10/stockAfter=10/kg), salida eventId f28931a9-9e26-49e7-8c78-83f280f26609 (quantity=3/stockAfter=7/kg). Confirmadas también 2 filas ui.operation_failed y 3 inventory.stock_lookup_completed reales; lote mixto real HTTP 200 received=13/stored=10/rejected=3 y IDs inválidos ausentes. Autorizada evidencia tabular de 7 filas en el PR en lugar de captura de pantalla (no disponible); timestamps de los dos eventos de negocio no proporcionados. Esta fase no cambia frontend/modelo; PR contra main solicitado incluye ramas de captura/plan heredadas.

- Tras recrear API con TELEMETRY_ENDPOINT, repetidos movimientos reales desde UI: entrada 10 kg (movementId f2fcda7c-2a23-4b67-81f2-f6e727ce45c9), salida 3 kg (movementId b1c53d47-f9c7-421a-b30a-9d0d2e27c1b9), ambas 201; stock final 7 kg, artículo 30ba729f-9275-4098-8453-06fce8ba26d0/local 97428172-e085-4a51-97d8-bb3da81a5a46. Logs del colector muestran lotes stored=received/rejected=0 y sin sink local en el rango revisado. Lectura directa de los dos inventory.movement_created y sus eventIds pendiente de consulta por tags.movementId en Supabase. Desarrollador confirmó los 5 eventos previos de UI y ausencia de los 2 IDs inválidos; captura final pendiente.

- Fase 3, recorrido real de UI 2026-10-26 19:29-19:31 UTC: creado artículo/local de verificación; entrada 10 kg y salida 3 kg confirmadas por 201 e historial, stock final 7 kg. Fallo de red forzado en consulta real mostró Failed to fetch y emitió ui.operation_failed (eventId ec05ba7e-8278-40ed-a859-62fad56c603d). Lote mixto interceptado antes del primer envío: 10 eventos reales + 3 inválidos → HTTP 200 received=13/stored=10/rejected=3. Logs revelan que eventos backend inventory.movement_created quedaron en sink local por TELEMETRY_ENDPOINT ausente; no se afirma persistencia de esos eventos. Corregido cableado API en Compose hacia su propio colector. Pendiente recrear API por el desarrollador (reinicia inventario en memoria), repetir movimientos y verificar filas/captura en Supabase. Frontend intacto.

- Arranque Docker de interfaces bloqueado por CRLF en `uis/start.sh`: reproducido en imagen aislada sin volúmenes, script presente pero shebang `/bin/sh\r` provoca exit 127. Corregido únicamente el comando Compose: normaliza la copia del script en el contenedor y ejecuta con `exec`; no se modifican fuentes bajo `uis/` ni sus montajes.

- Fase 3 de telemetría: `localhost:5173` pertenece a otro proyecto (Rootine); no se interactuó con él. Autorizada la separación de variables de `interfaces` en Compose: ya no recibe el archivo raíz con la clave service_role; usa solo puertos y rutas públicas con proxy a `api`. Arranque por el desarrollador pendiente, con override de BACKOFFICE_PORT a un puerto libre (propuesto 5175). Fase 2 confirmada por el desarrollador con lectura directa en Supabase: exactamente dos filas sintéticas environment=test, tags correctos. Eventos reales de interfaz y captura de tabla aún pendientes.

- Al abrir el PR de inventario se creó por error contra el repo de la organización (`ai-engineering-company-project-monorepo`, sin sufijo) en vez del fork personal (`...-jheremydev`). Corregido reabriendo el PR en el repo correcto.
- `memory-bank/current-state.md` (heredado de la fase de incidencias) decía "todavía no existe implementación funcional" — quedó desactualizado en cuanto se completaron incidencias e inventario. Este `progress.md` lo sustituye como fuente de estado actual.
- La verificación interactiva desde el origen `127.0.0.1:5173` no puede consultar la API configurada en `localhost:8000` por la allowlist CORS existente; se documentó sin modificar configuración fuera del alcance.
