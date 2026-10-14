# Project Brief

## Qué es Brasaland

Brasaland es una cadena de restaurantes de cocina a la brasa fundada en 2008 en Medellín, Colombia. Opera 14 restaurantes propios en dos países (Colombia y Florida, EE.UU.), emplea a unas 115 personas y factura aproximadamente 6 millones de dólares anuales. Lidera la compañía Mariana Restrepo (CEO desde 2019), y el mandato de transformación digital recae en el equipo interno **Brasaland Digital**, del que este monorepo es la base técnica.

Fuente: `CONTEXT.md`.

## Objetivo del proyecto

Sustituir procesos manuales y sin visibilidad (pedidos por WhatsApp, hojas de cálculo, llamadas telefónicas, informes semanales en PDF) por sistemas internos que permitan a Brasaland operar como una empresa moderna en dos países, sin perder la consistencia de marca que la hizo crecer.

## Problema que resuelve este monorepo

Brasaland gestiona una operación en dos países con herramientas pensadas para un único restaurante local. En concreto, este desarrollo ataca:

- **Falta de visibilidad de inventario**: los pedidos de materia prima se deciden a mano por cada gerente de local, sin datos de stock consolidados, y son propensos a quiebres o pedidos de emergencia tardíos (recargo del 8%).
- **Falta de trazabilidad operativa**: incidencias de operación, calidad o proveedores se reportan de forma informal y sin seguimiento por área responsable.
- **Falta de presencia digital coherente**: no existe una web corporativa ni un backoffice interno unificado; la tecnología actual es mínima (web estática, app obsoleta, POS distintos por país).

## Departamentos implicados

- **Operaciones de Restaurante** (Felipe Guerrero) — 14 locales en dos países.
- **Compras y Proveedores** (Lucía Fernández) — ~20 proveedores, aprobación de pedidos de emergencia >500 USD.
- **Marketing y Experiencia Digital** (Camila Ospina) — presencia de marca, web, fidelización.
- **Personas y Cultura** (Ashley Turner), **Formación y Estándares de Calidad** (Jake Morrison), **Tecnología** (Nicolás Park, CTO), **Dirección Ejecutiva** (Mariana Restrepo).

Fuente: `CONTEXT.md`, `company-choice.md`.

## Alcance actual de este monorepo

1. **Gestor de incidencias** — registro, filtrado y seguimiento de incidencias por área responsable.
2. **Gestor de inventario** — alta de artículos, movimientos de stock (entrada/salida/ajuste), stock derivado y señal de punto de reorden.
3. **Infraestructura de agentes** (este desarrollo) — banco de memoria, reglas de trabajo y skills para que cualquier agente de código opere de forma consistente sobre el repo.
4. **Capa de aplicación** — `uis/backoffice` (interno, ya consume ambos gestores) y `uis/website` (web corporativa pública).
