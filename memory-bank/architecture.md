# Arquitectura

## Stack previsto

### Backend

El backend del gestor vivirá en `services/`, dentro de la API FastAPI centralizada de la compañía. La API debe organizarse mediante routers o módulos por dominio y no mediante un microservicio independiente por cada dominio. Un worker solo se separará si necesita ejecutarse de forma independiente del API.

Esta convención está definida en `README.md` y formalizada en `.agents/rules/api-centralizada-fastapi.md`.

### Frontend

La interfaz del gestor vivirá en `uis/`, como parte del backoffice interno, previsiblemente en `uis/backoffice/` o una subcarpeta equivalente. `uis/README.md` define esta carpeta como el lugar para interfaces humanas y menciona explícitamente el backoffice como aplicación interna.

## Estructura de carpetas para este desarrollo

- `services/`: API FastAPI centralizada, incluyendo los routers y módulos del gestor de incidencias.
- `uis/backoffice/`: aplicación de backoffice que permitirá registrar, consultar, filtrar y seguir incidencias.
- `packages/`: solo si aparece código versionable reutilizado por varias aplicaciones, agentes o pipelines.
- `shared/`: solo para schemas, plantillas o assets compartidos que no constituyan una librería.
- `docs/`: documentación transversal del proyecto.
- `.agents/rules/`: reglas de trabajo del monorepo.
- `memory-bank/`: contexto y plan de este desarrollo.

Cada nueva aplicación o servicio debe tener su propia subcarpeta y `README.md`, según `README.md` y `.agents/rules/documentacion-por-componente.md`.

## Orquestación local

El archivo global de orquestación local debe ser `docker-compose.yml` en la raíz del repositorio. Debe conectar `services/`, las bases de datos y los demás contenedores del stack local. Dockerfiles auxiliares y otra configuración de infraestructura o despliegue pertenecen a `infra/`.

Esta convención está definida en `README.md` y `.agents/rules/docker-compose-en-raiz.md`.

## Dependencias

No se introducirán dependencias nuevas sin justificar primero su necesidad, su relación con la arquitectura existente y el problema que resuelven. Este plan no prescribe ninguna dependencia adicional.