# Incident Manager — Discovery Notes

## Resumen de la estructura del monorepo

El agente exploró el README raíz y los README de cada carpeta de primer nivel. Resumen de responsabilidades:

| Carpeta | Responsabilidad |
|---|---|
| `uis/` | Frontends: web pública, backoffice, portales, dashboards |
| `services/` | API centralizada FastAPI, backends y workers |
| `data/` | raw, pipelines, process, eval — datos y su transformación |
| `agents/` | Agentes de IA concretos, uno por subcarpeta |
| `skills/` | Capacidades reutilizables para agentes |
| `mcps/` | Servidores MCP que exponen herramientas/datos a modelos |
| `workflows/` | Automatización y orquestación (n8n, etc.) |
| `packages/` | Librerías versionables compartidas |
| `shared/` | Schemas, plantillas, assets sueltos |
| `docs/` | Documentación transversal del proyecto |
| `infra/` | Docker, despliegue, infraestructura |
| `scripts/` | Scripts puntuales |
| `internal/` | CLIs y herramientas internas con proyecto propio |

## Convenciones ya establecidas (identificadas)

1. **API centralizada, no microservicios**: `services/` está pensado para una única API FastAPI con routers por dominio, separando workers solo cuando sea estrictamente necesario (README.md raíz).
2. **Estructura fija por agente**: cada agente nuevo va en su propia subcarpeta dentro de `agents/`, siguiendo la plantilla de `agents/_template/` (`agent.py`, `README.md`, `tests/`).
3. **Estructura fija por skill**: cada skill requiere un `SKILL.md`, con `examples/`, `resources/` y `scripts/` opcionales (`skills/README.md`).
4. **Documentación obligatoria por pieza nueva**: cada app, servicio, agente o pipeline nuevo debe tener su propia subcarpeta + README, sin excepciones.
5. **`docker-compose.yml` fijo en la raíz**: toda la orquestación local vive ahí; el resto de infraestructura (Docker, Terraform, K8s) va en `infra/`.

## Discrepancias entre el resumen del agente y el código real

- **Afirmación inicial del árbol**: el README raíz enlaza conceptualmente a `data/README.md` como si documentara la carpeta `data/` en su conjunto.
- **Realidad verificada**: ese archivo **no existe**. La documentación real está fragmentada en `data/raw/README.md`, `data/pipelines/README.md`, `data/process/README.md`, `data/eval/README.md`. El agente lo detectó al intentar leerlo y confirmó su ausencia con una búsqueda directa en el sistema de archivos.
- **Otras confirmaciones**: el estado del repo coincide con lo que advierte el propio README raíz — no hay `AGENTS.md` en la raíz, no hay apps ejecutables, `CONTEXT.md` ya fue reemplazado por el briefing real de Brasaland (no es un placeholder), y `company-choice.md` ya documenta la elección de empresa.

## Práctica mejorable (propuesta, no aplicada)

**Propuesta**: crear un `data/README.md` de nivel superior que actúe como índice, enlazando a `raw/`, `pipelines/`, `process/` y `eval/`, en vez de dejar que el README raíz apunte a un archivo que no existe.

Esto no se aplica en este ejercicio — queda registrado como propuesta para discutir con el equipo, siguiendo la instrucción del CTO de no sobrescribir convenciones por preferencia personal sin acuerdo.