# Plan del gestor de incidencias

Este documento define el plan previo a la implementación. No contiene código ni introduce dependencias nuevas.

## 1. Ubicación del desarrollo

- El backend se implementará dentro de `services/`, como parte de la API FastAPI centralizada y con routers o módulos para el dominio de incidencias.
- El frontend se implementará dentro de `uis/backoffice/` o una subcarpeta equivalente bajo `uis/`, como aplicación interna para responsables de área.
- Cada aplicación o servicio nuevo tendrá su subcarpeta y `README.md`, conforme a `.agents/rules/documentacion-por-componente.md`.
- La orquestación local global, si se incorpora, se mantendrá en `docker-compose.yml` en la raíz. La configuración de infraestructura restante irá en `infra/`.

Estas decisiones siguen `README.md`, `services/README.md`, `uis/README.md`, `.agents/rules/api-centralizada-fastapi.md`, `.agents/rules/documentacion-por-componente.md` y `.agents/rules/docker-compose-en-raiz.md`.

## 2. Modelo de datos de una incidencia

La entidad `Incidencia` tendrá, como mínimo, estos campos:

- `id`: identificador de la incidencia.
- `canal`: uno de los canales definidos en `incident-domain.md`.
- `tipo`: uno de los tipos de incidencia definidos en `incident-domain.md`.
- `severidad`: `Baja`, `Media`, `Alta` o `Crítica`.
- `area_responsable`: una de las siete áreas responsables de `incident-domain.md`.
- `estado`: estado actual del ciclo de la incidencia.
- `autor`: persona o sistema que registró la incidencia.
- `created_at`: marca temporal de creación.
- `updated_at`: marca temporal de la última actualización.

El modelo debe permitir identificar el local, proveedor o ingrediente relacionado cuando esa información sea necesaria para interpretar los tipos de incidencia de Brasaland. La forma exacta de esos campos adicionales se definirá al implementar cada caso de uso respaldado por `CONTEXT.md` y `company-choice.md`.

## 3. Ciclo de estados

Se propone el siguiente ciclo completo:

`Abierta` → `En progreso` → `Escalada` → `Resuelta` → `Cerrada`

- **Abierta**: la incidencia fue registrada y aún no está siendo atendida.
- **En progreso**: un responsable está trabajando en ella.
- **Escalada**: requiere atención de un responsable de mayor nivel o aprobación, por ejemplo Lucía Fernández para un pedido de emergencia superior a 500 USD o Felipe Guerrero ante tres semanas consecutivas de merma no explicada.
- **Resuelta**: se aplicó una solución o acción correctiva, pendiente de confirmación final.
- **Cerrada**: la resolución fue confirmada y no quedan acciones pendientes.

El ciclo es una propuesta de implementación derivada de las necesidades de seguimiento y escalamiento documentadas en `CONTEXT.md` y `company-choice.md`.

## 4. Trazabilidad

Cada cambio de estado y cada cambio de área responsable debe crear una entrada de historial asociada a la incidencia. Cada entrada debe registrar:

- estado anterior y estado nuevo, cuando corresponda;
- área responsable anterior y nueva, cuando corresponda;
- autor del cambio;
- marca temporal del cambio.

El historial debe poder consultarse desde la ficha de detalle de la incidencia. No se debe sobrescribir la historia previa al actualizar el estado o el responsable.

## 5. Endpoints necesarios

La API centralizada debe exponer, como mínimo:

- `POST /incidents`: crear una incidencia.
- `PATCH /incidents/{incident_id}`: editar los datos permitidos de una incidencia y registrar cambios de estado o responsable.
- `GET /incidents`: listar incidencias, con filtros por `estado`, `severidad` y `area_responsable`.
- `GET /incidents/{incident_id}`: consultar el detalle de una incidencia junto con su historial de trazabilidad.

Los nombres son una propuesta inicial de rutas para el router de incidencias; deberán mantenerse dentro de la API FastAPI centralizada de `services/`.

## 6. Vista operativa

El backoffice debe incluir una vista del volumen de incidencias abiertas agrupado por severidad: `Baja`, `Media`, `Alta` y `Crítica`. La vista debe ayudar a los responsables de área a identificar la carga abierta y priorizar los casos de mayor severidad.

La vista se ubicará en el backoffice de `uis/` y consumirá la API centralizada de `services/`.

## 7. Dependencias y orden de implementación

No se introducirá ninguna dependencia nueva sin justificarla. El orden previsto es:

1. Crear y documentar la subcarpeta del backend dentro de `services/`.
2. Definir el modelo de incidencia, los catálogos de `incident-domain.md` y el historial de cambios.
3. Implementar los endpoints de creación, edición, listado y detalle.
4. Crear y documentar la subcarpeta del backoffice dentro de `uis/`.
5. Implementar el registro, los filtros, el detalle con historial y el volumen abierto por severidad.
6. Verificar el ciclo de estados, los filtros y la trazabilidad antes de ampliar el alcance.