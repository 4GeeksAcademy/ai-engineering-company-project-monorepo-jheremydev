# AUDIT.md — Auditoría de rendimiento frontend (Brasaland)

## Metodología

Las mediciones se ejecutaron con Lighthouse (Chrome DevTools) contra el **build de
producción** servido con `vite preview` dentro de Docker (`docker compose run ... npm run build && npm run preview`),
no contra `npm run dev`. Esto es intencional: el modo dev sirve código sin minificar,
con HMR activo y sin tree-shaking, lo que da puntuaciones no representativas de lo que
verá un usuario real en producción.

Nota técnica: `uis/website/vite.config.ts` y `uis/backoffice/vite.config.ts` disparan un
bug de Vite 8 / rolldown (`sourcemapPathTransform` recibe un array en vez de string) al
cargar el config en este monorepo. Workaround aplicado: flag `--configLoader runner` en
`build` y `preview`.

## Puntuaciones iniciales (before)

| Página | Modo | Performance | Accessibility | Best Practices | SEO |
|---|---|---|---|---|---|
| Website — Home | Mobile | 99 | 90 | 100 | 91 |
| Website — Home | Desktop | 100 | 91 | 100 | 91 |
| Backoffice — Centro de incidencias | Mobile | 98 | 96 | 100 | 82 |
| Backoffice — Centro de incidencias | Desktop | 100 | 96 | 100 | 82 |

Capturas: `audit/before/`.

Las cuatro puntuaciones de Performance ya superan el benchmark de 90 definido en el
enunciado, en ambos modos y ambos frontends, por lo que no fue necesario instalar
ninguna skill de agente de rendimiento (core-web-vitals / performance / web-perf) —
no había problemas de LCP, CLS o INP que corregir.

## Problemas identificados

### 1. SEO del backoffice (82/100, mobile y desktop)

**Causa raíz**: `uis/backoffice/index.html` tiene:
- `<html lang="en">` con todo el contenido de la aplicación en español.
- Sin etiqueta `<meta name="description">`.
- `<title>backoffice</title>` — genérico, no identifica la aplicación.

Lighthouse penaliza directamente estos tres puntos en su categoría SEO (idioma
declarado incorrecto, `meta-description` ausente, título poco descriptivo).

Dado que el backoffice es un panel interno (no debe indexarse en buscadores), la
corrección correcta no es "optimizar para SEO" sino declarar explícitamente que no
debe indexarse (`<meta name="robots" content="noindex, nofollow">`) además de corregir
el idioma y añadir descripción/título — resuelve la causa raíz sin perseguir un 100
que no tiene sentido de negocio aquí.

### 2. Accessibility — contraste de color insuficiente (90-91 website, 96 backoffice)

**Causa raíz**: Lighthouse marca "Background and foreground colors do not have a
sufficient contrast ratio" en ambos frontends, sobre los mismos elementos de texto
secundario: `p.lede`, `p.eyebrow` y `.section-head p` en el website; `div.live-status`,
`button.domain-tab`, `.filter-field span` en el backoffice.

En ambos casos el culpable es el mismo: el token de color `--muted: #68736e` (y en
menor medida `--terracotta: #b5492f`) usado como color de texto sobre fondos
`--paper: #fbfaf7` o blanco no alcanza el ratio 4.5:1 exigido por WCAG AA para texto
normal. Estos tokens están definidos de forma **idéntica y duplicada** en
`uis/website/src/App.css` y `uis/backoffice/src/App.css` (ver duplicación #3 más
abajo), así que el problema de contraste es el mismo problema de diseño repetido en
dos sitios.

## Análisis de código: duplicación

### Caso 1 — `formatDate()` duplicado literal

**Dónde aparece**: `uis/backoffice/src/App.tsx` (función `formatDate`, usada en
`IncidentDetailView`) y `uis/backoffice/src/InventoryManager.tsx` (función `formatDate`,
usada en la tabla de movimientos). Ambas implementaciones son prácticamente idénticas:
formatean con `Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })`.

**Por qué es candidato a refactor**: es lógica pura sin dependencias de UI, repetida
palabra por palabra en dos archivos. Cualquier cambio futuro en el formato de fecha
(zona horaria, idioma, formato) exige editar dos sitios y arriesga que queden
desincronizados.

**Abstracción propuesta**: extraer a `uis/backoffice/src/utils/formatDate.ts` como
función pura exportada, e importarla desde ambos componentes.

### Caso 2 — Componente de `<select>` reimplementado a mano

**Dónde aparece**: `App.tsx` ya define un componente genérico `SelectField<T extends
string>` (label + select controlado) y lo reutiliza internamente. Sin embargo,
`InventoryManager.tsx` no lo importa: repite manualmente el mismo patrón JSX
(`<label className="field"><span>{label}</span><select>...</select></label>`) al menos
cinco veces — para categoría, unidad de medida, tipo de movimiento, local y artículo.

**Por qué es candidato a refactor**: es el mismo componente conceptual
(label + select controlado + mapeo de opciones) reescrito a mano en vez de reutilizado,
solo porque vive en un archivo distinto. Duplica el riesgo de inconsistencia de
estilos/accesibilidad entre formularios.

**Abstracción propuesta**: mover `SelectField` de `App.tsx` a
`uis/backoffice/src/components/SelectField.tsx`, importarlo en ambos archivos y
sustituir las repeticiones manuales en `InventoryManager.tsx` por el componente
compartido.

### Caso 3 — Tokens de diseño CSS duplicados entre frontends

**Dónde aparece**: `uis/website/src/App.css` y `uis/backoffice/src/App.css` definen,
de forma idéntica, el mismo bloque `:root { --ink: #20302f; --muted: #68736e;
--line: #d9d4ca; --paper: #fbfaf7; --terracotta: #b5492f; --teal: #32665d; }`.

**Por qué es candidato a refactor**: no es solo duplicación de código — es la causa
directa de que el mismo problema de accesibilidad (contraste insuficiente de
`--muted`/`--terracotta`) exista en los dos frontends a la vez. Al estar copiado en dos
sitios, corregirlo requiere recordar tocar ambos archivos; si solo se corrige uno,
queda un frontend con el bug y el otro sin él.

**Abstracción propuesta**: mover el bloque de tokens a un archivo CSS compartido (por
ejemplo `packages/shared/tokens.css` o similar dentro del monorepo) e importarlo desde
ambos `App.css`. No se refactoriza el resto del CSS, solo se centraliza la fuente de
verdad de los colores.