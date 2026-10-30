# Diseño del pipeline de desempeño de negocio — Parte 1 de 3

**Estado:** diseño documental, aún no implementado. No se añade código de orquestación, migración, endpoint ni cambios al esquema de captura en esta parte. No requiere Docker.

**Límite del briefing:** `CONTEXT.md` no contiene las secciones "KPIs a medir" ni "Destination table", ni una sección "data-pipelines". El KPI ejecutivo y la frecuencia de este diseño se toman literalmente de la sección "Dirección ejecutiva" de `CONTEXT.md`. El nombre de tabla propuesto y la métrica obligatoria de telemetría quedan marcados como decisiones pendientes; no se atribuyen al briefing.

## Fuentes y vocabulario del monorepo

- **`CONTEXT.md`:** Brasaland opera en Colombia y Florida; Mariana Restrepo es CEO; los POS de los dos países son distintos y no están integrados. La sección "Dirección ejecutiva" pide ventas totales de la cadena en USD y COP e informe semanal automatizado cada lunes a las 7 de la mañana. Pregunta además cuánto se vendió esta semana en Florida y qué local tuvo el ticket medio más alto este mes.
- **`docs/telemetry/event-schemas.json`** y **`docs/telemetry/telemetry-plan.md`:** contrato de telemetría 1.0.0 y catálogo de eventos. El plan especifica que ventas y pagos no están incluidos en el catálogo ni implementados en el backoffice/API actual.
- **`infra/supabase/migrations/20261026180000_create_telemetry_events.sql`:** `public.telemetry_events` es append-only; `eventId` UUID es clave primaria y el envelope contiene `timestamp`, `event_type`, `tags`, `source`, `environment`, entre otros campos.
- **`services/telemetry/analysis.py`** y **`services/api/routers/telemetry_report.py`:** reporte técnico existente, que permanece sin cambios.
- **`services/api/models/inventory.py`** y **`services/api/storage/inventory.py`:** dominio actual de inventario. Sus cantidades no son ventas ni importes monetarios y el almacenamiento de artículos, locales y movimientos es en memoria.

---

## FASE 1 — Análisis del estado actual

### Estado Actual

**Eventos capturados y almacenamiento**

El catálogo actual contiene eventos de `inventory.*`, `incident.*`, `navigation.*`, `form.*`, `performance.*`, `frontend.*`, `api.*` y `operations.health_check_completed`. Entre ellos se encuentran `inventory.movement_received`, `inventory.movement_created`, `inventory.movement_validation_failed`, `inventory.reorder_signal_active`, eventos de incidencias, errores y rendimiento. No existe en ese catálogo un evento de venta, pago, ticket POS, importe de venta ni moneda. La necesidad de medir ventas en `CONTEXT.md` no significa que esos datos estén ya instrumentados.

El endpoint existente `POST /telemetry/events` valida el envelope y cada tipo de evento con el esquema definido en `docs/telemetry/event-schemas.json`. El campo entrante `properties` se almacena como `tags` en `public.telemetry_events` de Supabase. Los campos del envelope incluyen `eventId`, `timestamp` UTC, `sessionId`, `userId` (nulo en el contrato actual), `event_type`, `schemaVersion`, `requestId`, `tags`, `source` y `environment`. `eventId` identifica una ocurrencia de telemetría; `requestId` identifica una petición HTTP y `formAttemptId` una interacción de formulario. No son intercambiables.

El dominio de inventario existente usa `Articulo.id`, `Local.id` y `Movimiento.id`. Un movimiento contiene `articulo_id`, `local` (texto), `tipo` (entrada, salida, ajuste), `cantidad`, `autor`, `fecha` y `motivo`. El evento `inventory.movement_created` incluye IDs opacos `articleId`, `localId`, `movementId` y propiedades como `movementType`, `quantity`, `stockAfter` y `unit`. Ninguno de esos valores representa una venta monetaria. Además, el almacenamiento actual del dominio está en memoria y no es un ledger durable de ventas.

**Reporte técnico actual para ingeniería**

`GET /telemetry/report` lee `public.telemetry_events` para un período UTC (por defecto, los últimos siete días), utiliza una caché en memoria de 60 segundos y responde con:

- `events_per_day`: volumen de eventos observado por día.
- `error_rate_by_day`: conteo y proporción diaria de eventos clasificados como errores respecto al total observado.
- `event_type_distribution`: recuento de eventos por `event_type`.

La implementación refina `timestamp`, `event_type` y `tags`; extrae `outcome` y `httpStatus` cuando están disponibles. Es un informe técnico de telemetría, no un informe de ventas. **No modificar `services/telemetry/analysis.py` ni `GET /telemetry/report`; deben seguir funcionando igual para ingeniería.**

### Brecha de negocio

La sección "Dirección ejecutiva" de `CONTEXT.md` afirma que Mariana no puede responder cuánto se vendió esta semana en Florida ni qué local tuvo el ticket medio más alto este mes. Pide un dashboard con ventas totales de la cadena en USD y COP y un informe semanal automatizado cada lunes a las 7 de la mañana. El reporte técnico actual cuenta señales de software y no contiene importes, monedas, ventas, tickets ni dimensiones POS necesarias para responder esas preguntas.

Por tanto, el pipeline debe ser separado y consumir una fuente de ventas autoritativa de POS, normalizar sus dimensiones y agregar los importes y tickets por período. Los sistemas POS existentes no están integrados según `CONTEXT.md`, y no hay una tabla integrada de ventas en el monorepo. Hasta incorporar una fuente POS real y su contrato, las métricas de ventas no son calculables. `telemetry_events` puede servir como fuente de control operativo de captura, nunca como ledger de ventas ni como destino de este pipeline.

---

## FASE 2 — Diseño del pipeline

### Propósito

Producir el consolidado de ventas totales de la cadena en USD y COP que alimentará el informe ejecutivo semanal de Mariana Restrepo, generado y enviado cada lunes a las 07:00, según la frecuencia indicada en `CONTEXT.md`; el pipeline también deberá permitir explorar las preguntas allí planteadas sobre ventas de Florida por semana y ticket medio por local en el mes, una vez que la fuente POS y sus definiciones estén disponibles.

El único KPI expresamente incluido en el propósito contractual de esta parte es el de `CONTEXT.md`: ventas totales de la cadena en USD y COP. Las consultas sobre Florida y ticket medio aparecen como preguntas de negocio en el contexto, pero su fórmula, inclusión como KPI formal y reglas contables requieren confirmación antes de publicarlas como métricas certificadas.

> **DECISIÓN PENDIENTE — métrica obligatoria de telemetría:** no está especificada en `CONTEXT.md` ni en otro archivo del repositorio. Propuesta a validar: conteo de ocurrencias únicas de `inventory.movement_created` por `eventId` y día de `timestamp`, solo como indicador de actividad/cobertura de captura operativa. No mide ventas, no alimenta el total monetario y no se afirma que sea obligatoria por el briefing.

### Formato de extracción

- **Fuente comercial primaria — pendiente de integración:** el POS autoritativo de cada mercado, o una tabla de dominio durable que reciba sus transacciones. `CONTEXT.md` dice que hay POS distintos sin integración y el monorepo no tiene una tabla integrada de ventas. El contrato futuro debe incluir, como mínimo, ID estable de venta/ticket, fecha-hora de la venta, referencia a local, mercado, moneda original, importe con precisión decimal, estado y datos necesarios para tratar anulaciones/devoluciones conforme a Finanzas. Los nombres concretos de campos deben fijarse cuando se conozca el contrato del POS; no se inventa un nombre de tabla fuente.
- **Fuente de telemetría auxiliar:** `public.telemetry_events`, lectura solamente, filtrada por rango de `timestamp` y `event_type` acordado. El resultado JSON/PostgREST contiene columnas del envelope y `tags` JSONB. Se puede usar `eventId` para deduplicar e `inventory.movement_created` como candidato de control técnico si se aprueba. No usar `quantity`, `stockAfter` ni `movementId` como importe o clave de venta.
- **Dimensiones de dominio:** maestro de locales del POS con referencia estable, país/mercado y moneda. El modelo actual `Local` solo tiene `id` y `nombre`, vive en memoria y no define país ni moneda; no se debe inferir Florida/Colombia desde el nombre del local. La correspondencia del ID POS con `localId` del dominio queda pendiente.
- **Cadencia:** extracción y agregación diaria como propuesta operativa; publicación del consolidado semanal cada lunes a las 07:00, según `CONTEXT.md`. La zona horaria de ejecución y el cierre de semana deben confirmarse con negocio. Como propuesta inicial de frescura, recalcular una ventana móvil que incluya los últimos siete días y 24 horas de gracia; admitir backfill controlado para períodos anteriores. Esto no modifica la hora de entrega indicada en el briefing.
- **Formato y precisión:** extraer JSON/JSONB sobre HTTPS (PostgREST o API POS); validar esquema, timestamps, moneda, estado e IDs. Representar importes como NUMERIC/Decimal, nunca float. Preservar moneda original por fila. Si se solicita conversión a moneda única además del total por USD y COP, usar una fuente y regla de FX aprobadas por Finanzas; no inventar una tasa ni sumar monedas distintas.

### Diagrama de flujo

> ⚠️ **Pendiente de completar** — el diagrama (texto o Mermaid) con las tres etapas separadas (extracción, transformación, carga) no se incluyó en este borrador y debe añadirse antes de considerar esta fase cerrada.

Las etapas de extracción, transformación y carga son independientes. El flujo no podrá publicar ventas hasta contar con acceso a la fuente POS y validar su contrato.

### Transformación propuesta

- Validar IDs de venta/ticket y mapear cada transacción al maestro de locales; referencias desconocidas se aíslan como errores de calidad, no se les asigna local por aproximación de nombre.
- Aplicar reglas contables aprobadas para ventas válidas, anulaciones y devoluciones. No borrar transacciones ni sumar de nuevo una venta reemitida.
- Conservar moneda original y calcular totales separados para USD y COP. Agrupar por período y dimensiones aprobadas (al menos cadena; propuesta adicional: mercado y local). Confirmar con Finanzas si el total es bruto o neto, impuestos incluidos/excluidos y fecha que determina la semana comercial.
- El ticket medio se puede calcular como importe neto dividido por número de tickets únicos solo después de definir qué constituye un ticket válido y el tratamiento de anulaciones/devoluciones. Si no hay tickets y el denominador es cero, devolver no disponible/null y explicación de cobertura; no presentar un cero engañoso.
- No inferir importe desde inventario: `inventory.movement_created` y campos como `quantity`, `stockAfter`, `unit`, `movementId` reflejan cantidades o registro operativo, no importe monetario.
- Para telemetría, deduplicar por `eventId`; contar por separado entradas, duplicados y eventos válidos. `requestId` correlaciona peticiones HTTP, no ventas ni ocurrencias.

### Estrategia concreta de actualización

La granularidad propuesta de publicación es una fila por semana comercial, moneda y alcance (cadena; y opcionalmente mercado/local una vez que exista la dimensión). La clave natural concreta debe cerrarse junto con el modelo de destino. Candidata: `(week_start, market, local_id, currency)` con una convención explícita para el total de cadena (por ejemplo, una fila con `local_id` nulo y dimensión `market` de cadena), evitando colisiones entre total y filas de local.

Cada corrida recomputa por completo los grupos de su ventana desde transacciones POS deduplicadas. Primero escribe staging asociada a `run_id`, valida conteos, sumas, monedas y claves; después ejecuta upsert transaccional sobre la clave natural. En conflicto actualiza los importes, conteos, watermark/cursor, `last_refreshed_at`, `run_id` y calidad de datos; nunca suma el valor nuevo al agregado previamente publicado. El avance del watermark/cursor se guarda en la misma transacción que publica el agregado. Ante error antes del commit, se revierte la carga y no avanza el cursor.

Para proteger a los lectores de una publicación incompleta, publicar toda la ventana atómicamente (o intercambiar partición/versionado bajo una transacción) y mantener una restricción única sobre las claves naturales. Usar lock distribuido por período para impedir escritores concurrentes sobre la misma ventana.

### Tabla de destino y separación de servicios

> **DECISIÓN PENDIENTE — nombre exacto de tabla:** la sección "Destination table" no existe en `CONTEXT.md` ni en ningún archivo localizado del repositorio. El nombre contractual exacto no está especificado. Propuesta a validar, no atribuida al briefing: `reporting.weekly_sales_summary`, escogida por el entregable explícito de ventas semanales en USD/COP. Las tablas de destino futuras irán bajo el esquema `reporting`; esta propuesta no debe implementarse como nombre definitivo sin aprobación.

Columnas candidatas de la tabla propuesta, pendientes del contrato POS y de las definiciones de Finanzas:

- **Dimensiones:** `week_start`, `week_end`, `market`, `local_id`, `currency`.
- **Medidas:** `sales_total_amount` (NUMERIC en la moneda de la fila), `ticket_count` y, si se valida su definición, `average_ticket_amount` (NUMERIC, nullable cuando no aplique).
- **Control:** `source_watermark`, `source_record_count`, `duplicate_record_count`, `last_refreshed_at`, `run_id`, `data_quality_status`.

Como apoyo operativo se propone `reporting.pipeline_run_log` para las ejecuciones, también pendiente de aprobación. Ninguna tabla propuesta se crea en este entregable. `telemetry_events` es fuente de telemetría y permanece separada de las tablas `reporting.*`.

Los endpoints de reporting serán nuevos en `services/reporting/`, separados de `services/telemetry/` y de `GET /telemetry/report`:

- `GET /reporting/status`: estado y frescura de corridas desde metadatos Prefect/log de reporting.
- `POST /reporting/runs`: disparo manual idempotente de una corrida Prefect; no ejecuta ETL en FastAPI.
- `GET /reporting/kpis`: lectura de agregados ya publicados en la tabla `reporting.*`; no computa ETL en la petición.

---

## FASE 3 — Resiliencia e idempotencia

### Idempotencia ante fallos

- **Reintento de extracción:** conservar el cursor confirmado del origen y extraer con una ventana de solapamiento. Deduplicar ventas por el ID estable del POS. Si el origen no ofrece un identificador estable, la integración queda bloqueada hasta acordar una clave fiable con el propietario del POS; no se usará `requestId` o un hash de campos no garantizado como sustituto.
- **Reintento de carga:** generar de nuevo el resultado completo de cada período afectado desde la fuente deduplicada. Las claves únicas más el upsert reemplazan cada fila de agregado; no se añaden deltas a lo ya publicado. Si la transacción falla antes del commit, destino y cursor quedan como estaban. Si el commit tuvo éxito pero se perdió el acuse, el reintento converge al mismo contenido por la misma clave natural y no duplica cifras.
- **Publicación transaccional:** staging identificada por `run_id`, validación previa, transacción única para el upsert del período y el avance de watermark. Si la fuente no permite una transacción distribuida, guardar el cursor únicamente luego de confirmar la publicación, y hacer el retry relectura/deduplicación segura.
- **Deduplicación de telemetría:** para `public.telemetry_events`, usar `eventId` del envelope. La tabla tiene `eventId` como primary key y es append-only. El consumidor de este pipeline vuelve a descartar IDs ya vistos en su staging/ventana; no modificar eventos existentes ni asumir que `requestId`, `formAttemptId` o `movementId` equivalen al `eventId`.
- **Eventos tardíos:** recalcular desde cero el grupo de semana/local/mercado/moneda afectado, usando IDs de ticket únicos; hacer upsert de la misma clave. Registrar qué corrida y cursor modificaron la publicación y conservar historial o snapshots/versiones para reconstruir valores anteriores. No incrementar el total previo al recibir una fila tardía. La ventana móvil de siete días más 24 horas es propuesta y no sustituye la política contable de cierre.

### Log de ejecución

Tabla candidata `reporting.pipeline_run_log` (nombre propuesto, pendiente de aprobación) con al menos estos campos:

| Campo | Por qué se necesita |
|---|---|
| `run_id` | ID único para correlacionar las tasks, el estado de Prefect y las filas que publicó esa corrida. |
| `flow_name`, `trigger_type` (schedule, manual, backfill) | Identifica el pipeline y diferencia ejecución programada de intervención manual o histórica. |
| `started_at` (UTC) | Detecta retrasos, mide duración y descubre ejecuciones huérfanas que comenzaron pero no finalizaron. |
| `finished_at` (UTC, nullable) | Registra fin real; nulo mientras corre o si el proceso murió sin poder cerrar el registro. |
| `status` (Running, Completed, Failed) | Permite auditar si se completó y evita confundir presencia de filas con ejecución exitosa. |
| `period_start`, `period_end`, `source_watermark` | Precisa qué intervalo y posición de origen se procesaron y desde dónde reanudar/reproducir. |
| `source_records_read`, `unique_records_processed`, `duplicate_records_skipped`, `destination_rows_upserted` | Reconcilia origen, deduplicación y destino para detectar huecos, duplicados o carga incompleta. |
| `error_code`, `error_summary` | Deja rastro de errores sin almacenar secretos ni payloads personales/sensibles. |
| `initiated_by` y `request_id` (nullable) | Permite auditar un disparo manual y correlacionarlo con los logs de API sin tratar `requestId` como identidad ni clave de venta. |

Registrar el inicio antes de extraer, y cierre, estado, conteos y error seguro al terminar. Si una caída impide escribir el cierre, detectar el registro con `finished_at` nulo y `started_at` antiguo y conciliarlo con el estado de Prefect antes de relanzar.

---

## Preguntas de Diseño

### Idempotencia

**Duplicados en el origen:** en `telemetry_events`, ¿cómo evitar contar una misma acción dos veces? Deduplicar por `eventId`, UUID del envelope, en el consumidor/extracción y en staging con restricción única. En el dominio, `tags.movementId` de `inventory.movement_created` identifica el movimiento asociado, no la ocurrencia telemétrica; puede servir para conciliación, no reemplaza `eventId`. Para ventas, deduplicar por el ID inmutable de ticket/venta que ofrezca el POS; ese campo y la fuente aún no existen en el monorepo. Los eventos de inventario no se cuentan como ventas.

**Reintento después de fallo con carga parcial:** al morir el pipeline, staging queda vinculada al `run_id`; si la transacción no confirmó, rollback evita publicación parcial y el cursor no avanza. Al rerun se vuelve a leer la ventana desde el cursor confirmado, se deduplica por ID POS/`eventId`, se recalculan todos los agregados y se hace upsert por clave natural. Si la carga sí confirmó pero se perdió el ACK, la misma carga reemplaza las filas con los mismos valores y no suma otra vez. Consultar el estado Prefect/lock antes de relanzar para no solapar el escritor activo.

**Eventos tardíos:** usar el `timestamp` del ticket POS como fecha comercial, con la zona horaria del local resuelta por el maestro POS; el `timestamp` del envelope telemétrico es hora de observación UTC, no hora de la venta. Recalcular el período afectado completo con IDs únicos y upsert en la clave natural, sin sumar al total ya publicado. Registrar `run_id`, cursor, conteos y versión/snapshot anterior para mantener auditoría. La ventana de siete días + 24 horas es propuesta; el tratamiento posterior al cierre semanal queda pendiente de Finanzas.

### Observabilidad

**Silencio vs. ausencia real:** declarar actividad cero solo si el run fue exitoso, la extracción tiene cobertura confirmada del POS para el intervalo y el local estaba abierto según calendario fiable. Si falla la conexión, el POS no confirma cobertura o el pipeline no corrió, marcar estado desconocido/stale, no cero. Señales mínimas: `started_at`, `finished_at`, `status`, última corrida, watermark, filas leídas/únicas/duplicadas, timestamp de última transacción, cobertura por local/período, errores de conexión y `last_refreshed_at`. `operations.health_check_completed` ayuda a comprobar disponibilidad de API cuando el probe responde, pero la ausencia del evento no demuestra por sí sola que no hubiese actividad de negocio.

**Trazabilidad de recolección:** guardar la relación agregado → `run_id` → ventana/cursor y conteos de entradas/tickets; guardar IDs de fuente o referencias a staging restringida para reproducir la suma. Para telemetría, registrar conteos por `event_type`, `eventId`, `source`, `environment` e intervalo; correlacionar logs HTTP por `requestId` cuando exista, sin usarlo como ID de venta. Medir watermark, min/max timestamps, retraso de llegada, gaps, duplicados, ráfagas y duración por task. Hoy `telemetry_events` no define `received_at`; si se requiere medir latencia entre evento y recepción, esa capacidad debe diseñarse aparte, no fingirse usando `timestamp` como ambos relojes.

**Crecimiento vs. pérdida/duplicación:** comparar transacciones y tickets POS únicos día/semana, registros leídos frente a únicos/upserted, cobertura por `localId`, cursor y totales de control con el cierre/export POS. Comparar telemetría solo con su propia línea base y health probes, sin interpretarla como crecimiento de ventas. Alertar sobre huecos, saltos anómalos, variación de duplicados o reducción de cobertura. Publicar estado incompleto/stale cuando no se pueda reconciliar la fuente, en lugar de una métrica financiera aparentemente válida.

### Recuperabilidad

**Caída de base de datos:** recuperar desde el último watermark de origen confirmado en la misma transacción de publicación, y desde staging persistente asociada a `run_id` si está completa. Si staging no es durable, reextraer desde el último cursor confirmado con ventana de solapamiento y deduplicar por ID estable POS/`eventId`. Nunca adelantar el checkpoint al iniciar extracción. `telemetry_events` permanece como fuente append-only, no como checkpoint ni destino.

**Buffer en el frontend:** no usar el navegador como buffer autoritativo de ventas ni de datos POS. Una cola acotada para telemetría de browser puede perderse, duplicarse, agotarse o manipularse; el plan de telemetría contempla límites propuestos de 1 MiB/1.000 eventos y 24 horas, no garantía de durabilidad. Si hace falta entrega durable, la responsabilidad corresponde al colector/API servidor o al conector POS mediante outbox/cola, no al frontend ni al módulo `services/reporting/`. No añadir buffer en esta fase.

**Reintento de `POST /telemetry/events`:** el emisor genera `eventId` una vez y reenvía el mismo ID y payload con backoff exponencial y jitter; no genera otro `eventId` para el retry. La tabla tiene `eventId` como clave primaria, pero el endpoint actual no documenta una respuesta especial "ya almacenado"; actualmente informa `received`/`stored`/`rejected` y devuelve 503 ante fallo de persistencia. Como diseño futuro, responder 2xx con un resultado explícito de "ya almacenado" solo tras confirmar que ese `eventId` existe; 503/timeout/transitorio significa reintentar el mismo evento; error 4xx de contrato significa no repetir sin corregir. No cambiar el endpoint ni afirmar que ese comportamiento ya está implementado.

### Transversal

**Corridas concurrentes:** registrar `flow_run_id`, `run_id`, `trigger_type`, período, estado, duración y resultado de adquisición del lock. Adquirir lock distribuido por ventana/partición y usar una clave de idempotencia para disparos manuales. Si cron y `POST /reporting/runs` coinciden en el mismo período, devolver/enlazar la corrida activa o encolar el nuevo pedido, no permitir dos upserts simultáneos. Ante lock expirado, reconciliar estado Prefect, heartbeat y `started_at` antes de recuperación; revalidar cursor/ventana justo antes del commit. Permitir paralelismo solo para particiones comprobablemente disjuntas.

---

## FASE 4 — Mapeo a Prefect

### Flow y tasks

Flow principal propuesto: `weekly_sales_summary_flow(period_start, period_end, trigger_type, requested_run_id=None)`.

1. **`extract_pos_sales_task`**: leer tickets/ventas desde el conector POS identificado, con cursor confirmado y ventana solapada. No se habilita publicación productiva hasta disponer de origen y contrato real.
2. **`extract_telemetry_control_task`**: lectura de solo lectura de `public.telemetry_events` para `event_type` y rango aprobados; obtener conteos únicos por `eventId` como control, no importe.
3. **`validate_and_deduplicate_task`**: validar esquema, IDs, referencias de local, timestamps, moneda y estados; deduplicar por ID estable POS y `eventId` telemétrico; contabilizar registros rechazados y duplicados.
4. **`transform_weekly_sales_task`**: normalizar semana/local/mercado/moneda y calcular totales en moneda original, más ticket medio solo si su fórmula queda acordada. Añadir estado de cobertura/calidad.
5. **`load_reporting_summary_task`**: staging, verificaciones, lock y upsert transaccional idempotente; actualizar watermark en la misma publicación.
6. **`finalize_run_log_task`**: registrar hora fin, estado, conteos y errores saneados; ante excepción dejar watermark anterior y marcar Failed cuando se pueda persistir.

Estados Prefect mínimos que la integración expondrá: `Running`, `Completed` y `Failed`. Un estado `Completed` solo tras confirmar commit y log; una corrida fallida no puede adelantar checkpoint. Configurar retries con backoff para fallos transitorios; no reintentar indefinidamente errores permanentes de esquema, moneda o referencias de dominio. Las tasks deben ser idempotentes porque Prefect puede reintentarlas.

### Prefect blocks y secretos

- Block/secret para URL y credenciales Supabase, con privilegio mínimo: lectura de `public.telemetry_events` y escritura limitada a tablas `reporting.*` necesarias.
- Block de credenciales del POS cuando se identifique proveedor, con scope de lectura, rotación y timeouts propios.
- Block de configuración de zona horaria `America/Bogota` para el schedule de lunes a las 07:00 y parámetros de ventana/reintento. Confirmar si la hora del briefing se refiere a esa zona antes de desplegar.
- Block/secret para proveedor de tipo de cambio solo si Finanzas aprueba conversión monetaria y su metodología.
- Secretos fuera del repositorio, payloads y logs; nunca exponerlos a través de endpoints.

Los flows y blocks son diseño futuro; no están implementados en el monorepo.

---

## FASE 5 — Integración con la aplicación (solo diseño)

Los tres endpoints nuevos se implementarían en un módulo independiente `services/reporting/`, nunca en `services/telemetry/` ni en el router de `GET /telemetry/report`. Las rutas y funciones siguientes son propuestas documentales:

| Endpoint propuesto | Consumidor/uso | Función o flow llamado | Responsabilidad de `services/reporting/` |
|---|---|---|---|
| `GET /reporting/status` | Negocio consulta estado actual, última ejecución y frescura. | `get_weekly_sales_pipeline_status()` consulta el estado Prefect y/o `reporting.pipeline_run_log`. | Responder con estado (Running/Completed/Failed), período, última finalización, watermark y cobertura. Sin ETL ni cálculo de agregados. |
| `POST /reporting/runs` | Disparo manual autorizado para período permitido. | `trigger_weekly_sales_summary_flow(...)` solicita el flow de Prefect definido en `data/pipelines/`; devuelve 202 Accepted y `flow_run_id`/estado. | Validar parámetros y clave de idempotencia de solicitud; orquestar el disparo, no ejecutar extracción, transformación o carga dentro de FastAPI. |
| `GET /reporting/kpis` | Consulta de ventas semanales publicadas por cadena y, una vez confirmadas dimensiones, filtros por mercado/local/moneda. | `query_weekly_sales_summary(...)` lee agregados ya publicados de `reporting.weekly_sales_summary`. | Validar fechas/filtros y devolver el snapshot con `last_refreshed_at`/calidad. No ejecutar ETL al consultar ni leer `GET /telemetry/report`. |

La lógica de extracción, transformación, deduplicación, carga, retries y scheduling pertenece a `data/pipelines/`. Los endpoints nuevos quedan explícitamente separados de `POST /telemetry/events`, `public.telemetry_events` y el endpoint técnico `GET /telemetry/report`.

---

## Criterios y decisiones pendientes antes de implementar

1. **Destino exacto:** acordar si `reporting.weekly_sales_summary` es el nombre aprobado, ya que `CONTEXT.md` no especifica una tabla de destino.
2. **Fuente POS:** identificar proveedor/exports/APIs, credenciales, IDs estables de tickets, campos, estados, anulaciones, devoluciones y política de actualización.
3. **Definiciones financieras:** bruto/neto, impuestos, descuentos, redondeo, fecha/semana comercial, moneda original y tasa/fecha FX si se requiere conversión.
4. **Dimensiones:** maestro de los 14 locales, ID estable, mapeo de cada POS, mercado/país y calendario de apertura. No inferir país ni mercado desde un nombre.
5. **Métrica obligatoria de telemetría:** `CONTEXT.md` no la especifica. Validar si se necesita una señal de captura y si la propuesta `inventory.movement_created` es útil; no usarla como KPI financiero.
6. **Operación:** confirmar zona horaria de la entrega de lunes 07:00, retención de historial, ventanas de late-arriving data, locks, permisos de reporting y Prefect blocks.

## Conclusión

El KPI real de negocio documentado es el total semanal de ventas de la cadena en USD y COP, y la cadencia indicada es cada lunes a las 07:00. El monorepo todavía no contiene una fuente POS integrada ni el nombre contractual de tabla destino; por ello, este documento diseña el flujo sin presentar las propuestas como hechos ni habilitar cifras no verificables.
