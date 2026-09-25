# Inventory Manager - Fase 1: Specify

## Contexto

El backoffice de Brasaland necesita registrar existencias por local para dar visibilidad a las roturas y excesos de stock.
Hoy los pedidos de ingredientes se hacen sin datos de inventario; el contexto operativo está en `CONTEXT.md` y `company-choice.md`.
Las convenciones y el contexto ya documentado se encuentran en `memory-bank/`.

## Alcance

- Incluye registrar y consultar artículos de inventario, registrar entradas, salidas y ajustes asociados a un artículo y un local, y consultar el stock disponible de cada artículo por local a partir de sus movimientos.
- No incluye gestión de proveedores, precios, órdenes de compra, aprobaciones, pedidos de emergencia, integración con POS, transferencias automatizadas entre locales ni consolidación de compras.
- No incluye predicción de demanda, umbrales o alertas de stock, alertas de merma, registro detallado de desperdicio, ni automatizaciones del agente de inventario predictivo descrito en `company-choice.md`. El gestor de incidencias sigue siendo un módulo distinto.

## Criterios de aceptación

- **INV-001 (Ubicuo):** En todo momento, el stock de un artículo se calcula a partir de sus movimientos. No existe un endpoint, un campo de formulario ni una operación que edite el stock directamente.
- **INV-002 (Ubicuo):** El sistema muestra el stock disponible asociado al artículo y al local consultados, sin mezclar movimientos de otros artículos o locales.
- **INV-003 (Basado en evento):** Cuando se registra un artículo de inventario, el sistema permite identificarlo y consultarlo para registrar sus movimientos y consultar su stock.
- **INV-004 (Basado en evento):** Cuando se registra una entrada, salida o ajuste válido para un artículo y un local, el sistema conserva el movimiento con su tipo y cantidad y refleja su efecto en el stock consultado para ese artículo y local.
- **INV-005 (De estado):** Mientras un artículo y un local no tengan movimientos registrados, la consulta de stock de ese artículo en ese local muestra cero, sin crear un valor de stock editable.
- **INV-006 (Comportamiento no deseado):** Si se intenta registrar un movimiento sin artículo o local identificable, sin tipo entre entrada, salida y ajuste, o sin una cantidad válida, el sistema lo rechaza y no altera el stock calculado.
- **INV-007 (Comportamiento no deseado):** Si se intenta asignar o modificar directamente el stock de un artículo, el sistema no ofrece esa operación y no cambia el stock; los cambios de existencias se registran mediante movimientos.

No se define comportamiento opcional en este alcance: las capacidades condicionales del agente predictivo y las integraciones quedan fuera de este módulo.

## Preguntas abiertas / decisiones pendientes

- ¿Qué campos identifican un artículo y si su catálogo es común a todos los locales o específico de cada uno? `CONTEXT.md` menciona carne, verduras, salsas, bebidas, packaging y productos de limpieza, pero no define un catálogo cerrado ni sus campos.
- ¿Qué unidad de medida usa cada artículo y se permiten cantidades fraccionarias o conversiones de unidades?
- ¿El inventario requiere lotes, fechas de caducidad o trazabilidad adicional por proveedor? Ninguna de las fuentes define estos datos.
- ¿Cómo se registra el inventario inicial: como entrada o como ajuste, y qué significado y signo tiene un ajuste de stock?
- ¿Se permiten saldos negativos al registrar salidas o ajustes y, de ser así, cómo se presentan?
- ¿Se necesita asignar un mínimo por artículo, categoría o local? El umbral de tres días de `company-choice.md` corresponde a stock proyectado antes de la próxima entrega; no define mínimos para este registro básico.
- ¿Qué datos de auditoría son obligatorios en cada movimiento (autor, fecha, motivo) y es posible corregir o anular movimientos ya registrados?