# Estado actual

## Situación del repositorio para este desarrollo

El monorepo dispone de una estructura base y documentación de orientación. Para el gestor de incidencias existen como referencias de trabajo:

- `CONTEXT.md`, con el briefing operativo de Brasaland.
- `company-choice.md`, con la elección de Brasaland, los departamentos de interés y la idea del agente de inventario predictivo.
- `docs/incident-manager-discovery.md`, con las cinco convenciones del monorepo que deben respetarse.
- `.agents/rules/`, con las reglas individuales derivadas de esas convenciones.
- Las carpetas organizativas del monorepo, incluyendo `uis/`, `services/`, `data/`, `agents/`, `skills/`, `packages/`, `shared/`, `docs/`, `infra/`, `scripts/` e `internal/`.

## Estado del gestor

El gestor de incidencias es el primer desarrollo funcional sobre este monorepo. Todavía no existe una implementación funcional del backend del gestor, del backoffice ni del flujo de incidencias; este `memory-bank/` documenta el contexto y el plan antes de escribir código.

La afirmación de que el gestor es el primer desarrollo y que aún no hay código funcional se refiere al gestor de incidencias, no a la documentación y estructura base del repositorio.

## Próximo paso

Seguir el plan de `memory-bank/incident-manager-plan.md` paso a paso, empezando por definir la estructura documentada del backend y del backoffice antes de implementar funcionalidades.