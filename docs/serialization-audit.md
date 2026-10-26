# Auditoría de serialización de la API

**Fecha:** 2026-10-21
**Alcance:** endpoints HTTP declarados por la aplicación FastAPI en `services/api`. Esta fase documenta el estado observado; no modifica contratos ni código de la API.

## Resumen

| Estado | Endpoints |
|---|---:|
| ✅ Ya serializado | 14 |
| ⚠️ Parcialmente serializado | 0 |
| ❌ Sin serializar | 0 |
| **Total** | **14** |

La aplicación mantiene datos en memoria y sus modelos de dominio son modelos Pydantic; no se encontraron entidades ORM en las respuestas auditadas. Los modelos Pydantic declarados como `response_model` controlan los campos de la mayoría de las rutas.

## Hallazgos de autenticación y datos sensibles

No existen rutas de autenticación registradas: no hay registro, login, recuperación/restablecimiento de contraseña ni `/auth/me`. Por tanto, no hay respuestas de esos flujos en las que comprobar exposición de emails. Tampoco se encontraron campos de contraseña (hasheada o no), tokens, flags de borrado lógico ni timestamps de auditoría ajenos a los campos de dominio descritos abajo.

`autor`, `created_at`, `updated_at` y `timestamp` forman parte del seguimiento operativo de incidencias y movimientos. El backoffice muestra los autores y las fechas; no son credenciales. `articulo_id` y `local` identifican las relaciones de inventario y el backoffice los usa para filtrar, seleccionar o enlazar registros; son identificadores de dominio, no claves que deban ocultarse automáticamente.

## Inventario de endpoints

`response_model` indica si está declarado explícitamente en el decorador. Las anotaciones de retorno pueden hacer que FastAPI genere un esquema implícito, pero no equivalen a la declaración explícita auditada aquí.

| Método y ruta | Propósito | `response_model` explícito | Respuesta actual y exposición | Consumidor y estado | Problema y mejora propuesta |
|---|---|---|---|---|---|
| `GET /health` | Confirmar que la API está disponible. | Sí: `HealthResponse` | Esquema Pydantic con `status: str` y `service: str`; sin datos sensibles. | Los frontends no lo llaman; queda disponible para comprobaciones operativas. ✅ | **Cambios aplicados:** creado `HealthResponse` y declarado como `response_model` explícito. |
| `POST /incidents` (201) | Crear una incidencia. | Sí: `Incidencia` | Devuelve la instancia Pydantic con `id`, canal, tipo, severidad, área, estado, autor y fechas de creación/actualización. | `uis/backoffice` usa `id` para seleccionar la incidencia recién creada; la vista de detalle carga luego el registro completo. La representación completa es válida y no revela campos sensibles. ✅ |
| `GET /incidents` | Listar incidencias, con filtros opcionales de estado, severidad y área. | Sí: `list[IncidenciaResumen]` | Esquema de resumen con `id`, canal, tipo, severidad, área, estado y autor; no incluye `created_at` ni `updated_at`. | La tabla y el resumen operativo del backoffice consumen los campos del resumen; las fechas del registro completo se conservan en el endpoint de detalle. ✅ | **Cambios aplicados:** creado `IncidenciaResumen` y limitado a él el `response_model`; el listado ya no incluye timestamps. |
| `GET /incidents/{incidencia_id}` | Obtener una incidencia y su historial ordenado. | Sí: `IncidenciaDetalle` | Envelope Pydantic `{incidencia, historial}`. `incidencia` mantiene el modelo completo con `created_at` y `updated_at`; los elementos de historial tienen ID, campo, valores anterior/nuevo, autor y timestamp, sin `incidencia_id`. | El drawer de detalle usa las fechas completas y los campos del historial. ✅ | **Cambios aplicados:** creado `IncidenciaDetalle` con `HistorialItemResponse` y declaración explícita; el historial se proyecta a sus campos de salida y omite el ID de incidencia redundante. En las respuestas GET, las fechas completas quedan en el detalle y no en el listado. El POST de creación conserva su contrato existente, fuera del alcance de esta fase. |
| `PATCH /incidents/{incidencia_id}` | Cambiar estado y/o área responsable, registrando el historial. | Sí: `IncidenciaUpdateConfirmacion` | Devuelve únicamente `id`, `estado`, `area_responsable` y `updated_at`. | El backoffice descarta el cuerpo, vuelve a solicitar el detalle y actualiza la vista con esa lectura; no se cambió su comportamiento. ✅ | **Cambios aplicados:** creado y declarado `IncidenciaUpdateConfirmacion`, con confirmación acotada en lugar de devolver la incidencia completa. |
| `POST /inventory/locals` (201) | Crear un local. | Sí: `Local` | Devuelve `id` y `nombre`. | El backoffice usa el ID para seleccionar el local y el nombre en el mensaje de confirmación. ✅ |
| `GET /inventory/locals` | Listar locales para selectores. | Sí: `list[Local]` | Devuelve `id` y `nombre`. | El backoffice usa ambos campos en los selectores de local. ✅ |
| `POST /inventory/articles` (201) | Crear un artículo. | Sí: `Articulo` | Devuelve `id`, nombre, categoría, unidad de medida y punto de reorden. | El backoffice usa el ID para seleccionar el artículo y luego recarga el listado; la respuesta completa corresponde a la representación del recurso creado y todos sus campos son datos de inventario. ✅ |
| `GET /inventory/articles` | Listar artículos. | Sí: `list[Articulo]` | Devuelve ID, nombre, categoría, unidad de medida y punto de reorden. | El backoffice utiliza estos campos en la lista, los selectores y la señalización del punto de reorden. ✅ |
| `GET /inventory/articles/{article_id}` | Obtener un artículo por ID. | Sí: `Articulo` | Devuelve la misma representación Pydantic del artículo que el listado. | Hay una función cliente `getArticle`, pero no está llamada actualmente por la interfaz. La forma es consistente con el recurso y no añade campos internos innecesarios. ✅ |
| `POST /inventory/movements` (201) | Registrar una entrada, salida o ajuste de stock. | Sí: `Movimiento` | Devuelve ID, artículo, local, tipo, cantidad, autor, fecha y motivo. | El backoffice actualmente descarta el cuerpo y recarga el historial y, cuando corresponde, el stock. El recurso devuelto es una representación útil del movimiento registrado; los campos de relación y trazabilidad tienen uso funcional en el listado. ✅ |
| `GET /inventory/movements` | Listar movimientos, con filtros opcionales por artículo y local. | Sí: `list[Movimiento]` | Devuelve ID, artículo, local, tipo, cantidad, autor, fecha y motivo. | El historial del backoffice muestra tipo, cantidad, autor, fecha y motivo, y usa `articulo_id` para mostrar el nombre del artículo; `local` identifica el local. ✅ |
| `GET /inventory/movements/{movement_id}` | Obtener un movimiento por ID. | Sí: `Movimiento` | Devuelve el modelo Pydantic del movimiento, incluida su relación con artículo/local y sus datos de trazabilidad. | Hay una función cliente `getMovement`, pero no se usa actualmente en la interfaz. La forma coincide con el recurso y no hay datos sensibles observados. ✅ |
| `GET /inventory/stock` | Consultar stock derivado para un artículo y local. | Sí: `StockResponse` | Esquema Pydantic con `articulo_id`, `local`, `stock: Decimal`, `unidad_medida: str`, `punto_reorden: Decimal` y `bajo_punto_reorden: bool`. | El backoffice consume los seis campos para mostrar cantidad, unidad, artículo, local y alerta de reorden. ✅ | **Cambios aplicados:** creado `StockResponse` y declarado como `response_model`; cantidades y punto de reorden usan `Decimal`, coherente con los modelos de inventario. |

## Consumidores revisados

- **`uis/backoffice`:** consume incidencias e inventario mediante `src/api/incidents.ts` y `src/api/inventory.ts`. Los tipos del cliente están en `packages/shared/types/incidents.ts` y `inventory.ts`. La tabla de incidencias usa los campos de resumen; su drawer usa fechas y datos de historial. El historial de movimientos utiliza los identificadores para enlazar artículos y mostrar los datos de movimiento.
- **`uis/website`:** es una web corporativa estática y no realiza llamadas a la API. No hay consumidores de estos endpoints en su código actual.
- **Funciones de cliente no utilizadas:** `getArticle` y `getMovement` están definidas, pero no tienen llamadas desde la interfaz actual. Sus respuestas de detalle conservan el modelo de recurso existente.

## Fuentes examinadas

- `services/api/main.py`
- `services/api/routers/incidents.py` y `services/api/routers/inventory.py`
- `services/api/models/incidents.py` y `services/api/models/inventory.py`
- `uis/backoffice/src/api/`, `uis/backoffice/src/App.tsx` y `uis/backoffice/src/InventoryManager.tsx`
- `packages/shared/types/incidents.ts` y `packages/shared/types/inventory.ts`
- `uis/website/src/`
