# Plan técnico del gestor de inventario (Fase 2 - Plan)

Este documento define la arquitectura y los contratos que guiarán la implementación de los criterios INV-001 a INV-021. El backend se integrará en la API FastAPI centralizada; no se crea un microservicio ni se añade una dependencia nueva.

## 1. Modelo de datos

Los modelos persistidos del dominio vivirán en `services/api/models/inventory.py`, siguiendo el estilo Pydantic de `models/incidents.py`. Los esquemas de creación serán payloads separados, sin identificador generado por el cliente.

### `Articulo`

- `id: str`: UUID generado al registrar el artículo; identifica el mismo artículo en todos los locales (INV-003, INV-008, INV-009).
- `nombre: str`: obligatorio y no vacío (INV-003, INV-009).
- `categoria: CategoriaArticulo`: enum limitado a `carne`, `verduras`, `salsas`, `bebidas`, `packaging` y `productos de limpieza` (INV-003, INV-009).
- `unidad_medida: str`: obligatoria y no vacía; texto simple, por ejemplo `kg`, `unidad` o `litro`, sin conversión entre unidades (INV-003, INV-010, INV-011).

`CategoriaArticulo` será un enum de texto. El catálogo de artículos no contiene local ni stock: es global y común a todos los locales (INV-001, INV-008).

### `Movimiento` y `TipoMovimiento`

`TipoMovimiento` será un enum de texto con los valores `entrada`, `salida` y `ajuste` (INV-004, INV-006).

- `id: str`: UUID generado para conservar e identificar cada registro (INV-004, INV-020).
- `articulo_id: str`: referencia obligatoria a un artículo existente; evita mezclar existencias entre artículos (INV-002, INV-004, INV-006).
- `local: str`: identificador obligatorio y no vacío de texto libre, no validado contra un catálogo cerrado (INV-002, INV-004, INV-006, INV-021).
- `tipo: TipoMovimiento`: obligatorio y limitado a los tres tipos admitidos (INV-004, INV-006, INV-013).
- `cantidad: Decimal`: obligatoria y admite fracciones. Entrada y salida requieren cantidad mayor que cero; ajuste conserva el signo de la cantidad para sumar o restar (INV-006, INV-012, INV-014, INV-015, INV-016).
- `autor: str`: obligatorio y no vacío; no se sintetiza si falta en el payload (INV-017, INV-018).
- `fecha: datetime`: obligatoria y aportada al registrar; no se sustituye por una fecha implícita si falta (INV-017, INV-018).
- `motivo: str | None`: nota opcional, conservada si se proporciona (INV-019).

No habrá campo de stock mutable en `Articulo`, `Movimiento` ni en los payloads de movimiento. Tampoco habrá operaciones para editar o eliminar movimientos (INV-001, INV-007, INV-020). Registrar inventario inicial consiste en crear un movimiento `ajuste` con la cantidad inicial, no una `entrada` (INV-013).

## 2. Cálculo de stock

El stock se obtiene cada vez a partir de los movimientos que coincidan simultáneamente con `articulo_id` y `local`; no se guarda ni se actualiza un saldo independiente. Sin movimientos coincidentes, el resultado es cero (INV-001, INV-002, INV-005).

La lógica reduce el historial aplicando `+cantidad` a una entrada, `-cantidad` a una salida y la cantidad con su signo a un ajuste. Las cantidades se manejan como decimales (`Decimal`) y siempre en la unidad del artículo; el módulo no convierte unidades (INV-011, INV-012, INV-014, INV-015).

Antes de aceptar una salida o un ajuste negativo, el registro calcula el saldo actual para ese artículo y local y calcula el saldo resultante con el movimiento propuesto. Si el resultado es menor que cero, rechaza la operación antes de añadir nada al almacenamiento; por tanto, se conserva tanto el historial como el stock anterior (INV-016). Las entradas y ajustes positivos aumentan el saldo. No existe escritura directa del stock (INV-001, INV-007).

## 3. Almacenamiento

`services/api/storage/inventory.py` mantendrá listas en memoria, siguiendo `services/api/storage/incidents.py`:

- `articulos: list[Articulo]` para el catálogo global.
- `movimientos: list[Movimiento]` como historial inmutable.

El módulo expondrá operaciones de dominio para crear y listar artículos, buscar un artículo por identificador, listar y buscar movimientos, calcular stock por artículo y local, y registrar un movimiento. El registro validará la referencia al artículo y el saldo resultante antes de anexarlo, sin dejar cambios parciales. No expondrá setters de stock ni funciones de actualización o eliminación de movimientos (INV-001, INV-006, INV-016, INV-020). La persistencia es en memoria, coherente con el patrón de incidencias; no implica base de datos en esta fase.

## 4. Endpoints

El router se ubicará en `services/api/routers/inventory.py`, con prefijo `/inventory` y tag `inventory`, y se incluirá en la API centralizada de `services/api/main.py` igual que el router de incidencias.

| Método y ruta | Comportamiento y criterios | Respuestas de error |
|---|---|---|
| `POST /inventory/articles` | Crea un artículo con UUID y lo incorpora al catálogo común (INV-003, INV-008, INV-009). Responde `201`. | `422` si falta nombre, categoría o unidad, o si su valor no es válido (INV-003, INV-009, INV-010). |
| `GET /inventory/articles` | Lista el catálogo común, sin duplicarlo por local (INV-008, INV-009). Responde `200`. | No aplica validación de local. |
| `GET /inventory/articles/{article_id}` | Consulta un artículo por su identificador global (INV-003, INV-008). Responde `200`. | `404` si no existe el artículo. |
| `POST /inventory/movements` | Registra una entrada, salida o ajuste y conserva el movimiento y sus metadatos (INV-004, INV-012 a INV-019, INV-021). Responde `201`. | `422` ante campos requeridos ausentes, local vacío, tipo inválido, cantidad no válida, o autor/fecha ausentes (INV-006, INV-018); `404` si `articulo_id` no identifica un artículo (INV-006); `409` si una salida o ajuste negativo dejaría saldo menor que cero, sin anexar el movimiento (INV-016). El local libre no se rechaza por no pertenecer a un catálogo (INV-021). |
| `GET /inventory/movements` | Consulta el historial, con filtros opcionales `articulo_id` y `local`; filtrar por ambos permite inspeccionar exactamente el historial que compone un saldo (INV-002, INV-004, INV-017, INV-019, INV-020, INV-021). Responde `200`. | `404` si se filtra por un identificador de artículo inexistente. |
| `GET /inventory/movements/{movement_id}` | Consulta un movimiento existente con todos sus datos preservados (INV-004, INV-017, INV-019, INV-020). Responde `200`. | `404` si no existe el movimiento. |
| `GET /inventory/stock?articulo_id=…&local=…` | Calcula y devuelve el stock para el par exacto de artículo y local, incluso cero si no hay movimientos (INV-001, INV-002, INV-005, INV-008, INV-011, INV-021). Responde `200`. | `422` si falta alguno de los dos parámetros; `404` si el artículo no existe. |

Los cuerpos inválidos usan el `422` de validación de FastAPI/Pydantic. No se implementarán endpoints de escritura de stock ni de `PATCH`, `PUT` o `DELETE` de movimientos. Cuando la ruta del recurso exista, esos métodos no admitidos responderán `405 Method Not Allowed`; las rutas no registradas responden `404`. Así se rechaza la modificación directa del stock y se preserva la inmutabilidad del historial (INV-007, INV-020).

## 5. Tipos compartidos

`packages/shared/types/inventory.ts` definirá los tipos que consume el backoffice a través de `@repo/shared-types`, siguiendo `incidents.ts`:

- `inventoryCategories` y `InventoryCategory`, con las seis categorías del modelo.
- `movementTypes` y `MovementType`, con `entrada`, `salida` y `ajuste`.
- `InventoryArticle`, con identificador, nombre, categoría y unidad de medida.
- `InventoryMovement`, con identificador, `articulo_id`, `local`, tipo, cantidad decimal representada como `number` en JSON, autor, fecha ISO como `string` y motivo opcional.
- `InventoryStock`, con `articulo_id`, `local`, saldo y unidad de medida; es una respuesta calculada, no un campo editable del artículo.
- `NewInventoryArticle`, `NewInventoryMovement` e `InventoryMovementFilters` para los payloads y filtros del cliente.

`packages/shared/types/index.ts` reexportará `./inventory`; las aplicaciones no redefinirán estos tipos localmente (INV-001 a INV-021, según el campo o contrato correspondiente).

## 6. Cliente API frontend

`uis/backoffice/src/api/inventory.ts` seguirá el patrón de `api/incidents.ts`, importará tipos desde `@repo/shared-types` y delegará cada petición en `request<T>` de `api/client.ts`. No duplicará `fetch`, la URL base ni el manejo de errores.

Expondrá `getArticles()`, `getArticle(id)`, `createArticle(payload)`, `getMovements(filters)`, `getMovement(id)`, `createMovement(payload)` y `getStock(articleId, local)`. Las funciones serializarán los payloads como JSON; para filtros y consulta de stock construirán los parámetros con `URLSearchParams`, de modo que el identificador de local de texto libre se transmita correctamente. No habrá función para cambiar stock, editar movimientos ni borrarlos (INV-001, INV-007, INV-020, INV-021).

## 7. Fuera de este plan

Este plan no decide pantallas, navegación, tablas, formularios, validaciones visuales, estados de carga, mensajes, filtros interactivos ni presentación del stock. La especificación determina los comportamientos y datos; el diseño de esas decisiones de UI/UX se hará al implementar el frontend. No se incluyen aquí tareas ni orden de implementación; se definirán en el documento separado de Fase 3 (`tasks.md`).