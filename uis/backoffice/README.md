# Brasaland Backoffice

Aplicacion interna de Brasaland Digital para centralizar herramientas operativas. El primer caso de uso sera el gestor de incidencias.

## Stack

- Vite
- React
- TypeScript

## Instalacion

Desde `uis/backoffice/`:

```bash
npm install
```

Copia `.env.example` a `.env.local` y ajusta la URL de la API si es necesario:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Desarrollo local

Desde `uis/backoffice/`:

```bash
npm run dev
```

Vite mostrara la URL local del backoffice en la terminal.

## API

La aplicacion se conectara a la API FastAPI centralizada de `services/api/`. La URL base se configura mediante `VITE_API_BASE_URL`; no debe hardcodearse en el codigo fuente.

## Scripts

- `npm run dev`: inicia el servidor de desarrollo.
- `npm run build`: genera la compilacion de produccion.
- `npm run lint`: ejecuta ESLint.
- `npm run preview`: sirve localmente la compilacion de produccion.
