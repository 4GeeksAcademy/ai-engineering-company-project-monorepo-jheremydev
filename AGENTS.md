# Agent Guidance

Este archivo define cómo debe operar cualquier agente de código (Cursor, Windsurf, Claude Code, etc.) sobre este repositorio. No confundir con `/agents` y `/skills` en la raíz — esas carpetas son código de producto (agentes e integraciones para Brasaland), no configuración del agente de desarrollo.

## Qué leer al inicio de cada sesión

Antes de tocar cualquier archivo, el agente debe leer, en este orden:

1. `CONTEXT.md` — briefing de la empresa (Brasaland).
2. `memory-bank/projectbrief.md` — negocio, objetivo y problema que resuelve el proyecto.
3. `memory-bank/techContext.md` — stack real, decisiones de arquitectura y restricciones técnicas.
4. `memory-bank/progress.md` — estado actual de cada feature y próximos pasos.
5. Las reglas aplicables en `.agents/rules/` según el alcance de lo que se vaya a tocar (ver más abajo).

## Flujo obligatorio antes de cada commit

Ningún agente escribe código sin pasar por este proceso:

1. **Leer** el banco de memoria y las reglas de `.agents/rules/` relevantes para el área a modificar.
2. **Verificar contra el spec**, si el cambio pertenece a una feature con Spec Driven Development (`specs/<feature>/spec.md`): confirmar que el cambio está cubierto por un criterio de aceptación existente, o actualizar primero el spec/plan/tasks antes de tocar código.
3. **Implementar** el cambio siguiendo las reglas de `.agents/rules/` aplicables (ubicación de archivos, separación por dominio, documentación por componente).
4. **Verificar**: correr los tests/scripts de verificación del componente afectado (`services/api/tests`, `verify_incidents.py`, `verify_inventory.py`, o `npm run build`/`lint` en `uis/*`) y confirmar que pasan.
5. **Actualizar `memory-bank/progress.md`** con el estado nuevo (feature completada, decisión tomada, problema encontrado) antes de commitear.
6. **Commit**, con un mensaje que describa el cambio y, si aplica, el criterio de aceptación que cubre.

Si algún paso falla o el agente no tiene información suficiente para completarlo (por ejemplo, un requisito ambiguo o un cambio que afecta a una carpeta protegida), se detiene y pregunta antes de continuar.

## Carpetas y archivos que el agente no debe modificar sin confirmación explícita del desarrollador

- `CONTEXT.md` / `CONTEXT.es.md` — briefing oficial de la empresa; solo el desarrollador lo actualiza.
- `company-choice.md` — decisión de negocio ya tomada.
- Cualquier `spec.md` ya verificado (checklist E2E completo) de una feature — un cambio ahí es un cambio de requisito y sigue el proceso de `specs/<feature>/spec.md` → `plan.md` → tareas regeneradas, nunca una edición directa.
- `package.json` de la raíz (workspaces) y `docker-compose.yml` — cambios de configuración estructural del monorepo.
- Migraciones o esquemas de base de datos, si en el futuro se introducen (hoy el almacenamiento es en memoria).

## Dónde están las skills del agente

- **Skills de configuración del agente** (tareas recurrentes de este flujo de trabajo, ej. scaffolding de código): `.agents/skills/<skill>/SKILL.md`.
- **Skills de producto** (capacidades que usarán los agentes que se construyan para Brasaland en módulos posteriores): `/skills`, sin relación con esta configuración.

## Reglas de trabajo

Reglas individuales, con su alcance de aplicación, en `.agents/rules/`:

- `api-centralizada-fastapi.md` — `services/**`
- `docker-compose-en-raiz.md` — todo el repositorio
- `documentacion-por-componente.md` — `uis/**`, `services/**`, `agents/**`, `data/pipelines/**`
- `estructura-de-agente.md` — `agents/**`
- `estructura-de-skill.md` — `skills/**`
- `separacion-por-dominio.md` — `uis/backoffice/src/**`, `services/api/**`
