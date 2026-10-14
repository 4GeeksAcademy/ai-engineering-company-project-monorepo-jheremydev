# Progress

_Actualizar cada vez que el proyecto evolucione: nuevas decisiones, features completadas, problemas encontrados. Un `progress.md` desactualizado deja de ser útil en días._

## Estado por feature

| Feature | Estado | Rama | PR |
|---|---|---|---|
| Gestor de incidencias | Implementado, tests en verde | `feature/incident-manager` | #1, abierto (sin mergear) |
| Gestor de inventario | Implementado, tests en verde, 29 criterios EARS verificados | `feature/inventory-manager` (sale de `incident-manager`) | #2, abierto, marcado "Ready to merge" |
| Infraestructura de agentes (banco de memoria, `AGENTS.md`, `.agents/rules`, `.agents/skills`) | En curso — este desarrollo | `feature/agent-memory-bank` (sale de `inventory-manager`) | pendiente de abrir |
| `uis/website` (web corporativa pública) | Construida; pendiente de verificación en ejecución | `feature/agent-memory-bank` | — |
| `uis/backoffice` | Funcional: pestañas de Incidencias e Inventario, ambas consumiendo la API real | ya en `inventory-manager` | — |

## Orden de merge previsto

`incident-manager` → `inventory-manager` → `agent-memory-bank`, en ese orden, cada uno contra `main`. Como cada rama sale de la anterior, el diff de cada PR se limpia automáticamente en cuanto se mergea el anterior.

## Lo que ya funciona de verdad (no solo planeado)

- API FastAPI centralizada en `services/api`, con routers y storage separados por dominio (incidencias, inventario). Almacenamiento en memoria — sin base de datos todavía.
- `uis/backoffice`: React+Vite+TS, con navegación por pestañas entre Incidencias e Inventario, formularios de alta, filtros, detalle con historial de cambios (incidencias) y gestión de stock/locales/punto de reorden (inventario).
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
