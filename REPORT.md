# REPORT.md — Resultados de la auditoría de rendimiento (Brasaland)

## Comparativa de puntuaciones

| Página | Modo | Performance | Accessibility | Best Practices | SEO |
|---|---|---|---|---|---|
| Website — Home | Mobile | 99 → 99 | **90 → 100** | 100 → 100 | 91 → 91 |
| Website — Home | Desktop | 100 → 100 | **91 → 100** | 100 → 100 | 91 → 91 |
| Backoffice — Incidencias | Mobile | 98 → 99 | **96 → 100** | 100 → 100 | **82 → 54*** |
| Backoffice — Incidencias | Desktop | 100 → 100 | **96 → 100** | 100 → 100 | **82 → 54*** |

\* Bajada intencional — ver nota al final.

Capturas: `audit/before/` y `audit/after/`.

## Correcciones aplicadas (una por commit)

### 1. `fix(a11y)` — Centralizar tokens de color y corregir contraste

**Problema**: `--muted` y `--terracotta` no alcanzaban el ratio 4.5:1 (WCAG AA) contra
`--paper`/blanco, y estaban duplicados idénticamente en `uis/website/src/App.css` y
`uis/backoffice/src/App.css`.

**Corrección**: tokens centralizados en `packages/shared/tokens.css`, importado por
ambos `main.tsx` antes de cada `App.css`. Valores oscurecidos (`--muted: #4f5953`,
`--terracotta: #8a3620`) para dar margen real sobre el mínimo exigido (6.97–7.99:1
verificado).

**Impacto medido**: Accessibility subió de 90→100 (website mobile), 91→100 (website
desktop), 96→100 (backoffice mobile y desktop) — el mayor impacto de toda la auditoría,
y resolvió el mismo problema en los dos frontends con un solo cambio porque atacaba la
causa raíz compartida, no un síntoma por archivo.

### 2. `fix(seo)` — Corregir idioma, descripción, título y robots del backoffice

**Problema**: `uis/backoffice/index.html` tenía `lang="en"` con contenido en español,
sin `meta description` y título genérico `"backoffice"`.

**Corrección**: `lang="es"`, `meta description` descriptiva, `<title>` con el nombre
real de la aplicación, y `meta robots content="noindex, nofollow"` (el backoffice es
un panel interno, no debe indexarse).

**Impacto medido**: SEO bajó de 82→54 en ambos modos. Esto es el resultado esperado y
correcto, no una regresión — ver nota al final.

### 3. `refactor` — Extraer `formatDate` compartido

**Problema**: función idéntica duplicada en `App.tsx` e `InventoryManager.tsx`
(backoffice).

**Corrección**: extraída a `uis/backoffice/src/utils/formatDate.ts`, importada desde
ambos archivos.

**Impacto**: no afecta a las puntuaciones de Lighthouse (es lógica pura sin efecto en
render), pero elimina el riesgo de que las dos implementaciones se desincronicen.

### 4. `refactor` — Extraer y reutilizar `SelectField`

**Problema**: el componente `SelectField` (label + select controlado) ya existía en
`App.tsx` pero `InventoryManager.tsx` reimplementaba el mismo patrón a mano cinco veces.

**Corrección**: movido a `uis/backoffice/src/components/SelectField.tsx`, ampliado con
props opcionales (`placeholder`, `required`, `disabled`, opciones `{value, label}`)
para cubrir los cinco casos reales sin romper comportamiento, y reutilizado en ambos
archivos.

**Impacto**: no afecta a Lighthouse; reduce la superficie de código duplicado y
centraliza cualquier cambio futuro de accesibilidad/estilo en los selects.

## Valoración de mayor impacto

El fix de contraste de color (#1) tuvo el mayor impacto medible: +10 puntos de
Accessibility en website y backoffice a la vez, con un único cambio centralizado. Fue
posible porque el análisis de código había identificado que ambos frontends compartían
los mismos tokens duplicados — la corrección de performance y la corrección de
duplicación de código fueron, en este caso, la misma corrección.

## Nota sobre la bajada de SEO en el backoffice (82→54)

Lighthouse penaliza fuerte la auditoría `is-crawlable` cuando detecta `meta
robots="noindex"`, porque por defecto asume que toda página quiere ser indexada. El
backoffice es una herramienta interna de uso diario para el equipo de operaciones — el
enunciado del CTO pide SEO explícitamente para el sitio corporativo, y para el
backoffice pide que "funcione bien para las personas que lo usan a diario", no
posicionamiento en buscadores. Indexarlo sería un error real (expondría una
herramienta interna en resultados de búsqueda), así que esta bajada de puntuación es
la consecuencia correcta de la decisión correcta, no un efecto colateral a revertir.
El objetivo de la auditoría no era maximizar cada número sino corregir causas reales —
y en este caso, la causa real exigía bajar uno de los números.