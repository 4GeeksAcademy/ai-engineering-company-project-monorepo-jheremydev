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
NEXT_PUBLIC_TELEMETRY_ENDPOINT=/telemetry/events
```

`vite.config.ts` declara `envPrefix: ['VITE_', 'NEXT_PUBLIC_']` para exponer la variable de telemetría. Si no se define, el servicio usa `/telemetry/events`, que el proxy de Vite (`/telemetry`) reenvía a `API_PROXY_TARGET`. Un endpoint del mismo origen evita preflight CORS en `sendBeacon`.

## Desarrollo local

Desde `uis/backoffice/`:

```bash
npm run dev
```

Vite mostrara la URL local del backoffice en la terminal.

## API

La aplicacion se conectara a la API FastAPI centralizada de `services/api/`. La URL base se configura mediante `VITE_API_BASE_URL`; no debe hardcodearse en el codigo fuente.

## Telemetria

Todo el tracking pasa por `track(eventType, properties)` de `src/services/telemetry.ts`; ningun otro archivo llama a `fetch` para telemetria. El servicio genera el envelope de `docs/telemetry/event-schemas.json` (`eventId`, `timestamp` de captura, `sessionId` anonimo por pestana en `sessionStorage`, `userId` siempre `null`, `schemaVersion` desde `@repo/shared-types`, `requestId`, `source`, `environment`). Encola en memoria y envia lotes cada 10 s o al llegar a 20 eventos, con hasta 3 intentos y backoff exponencial (1 s, 2 s); hace flush con `sendBeacon` cuando la pestana pasa a `hidden`. `trackRequest()` es un helper interno reservado a `src/api/client.ts` para correlacionar eventos con el `X-Request-ID` de una peticion.

## Componentes compartidos

`src/components/SelectField.tsx` reutiliza los selectores con la clase `field` en incidencias e inventario. Acepta opciones de texto o `{ value, label }` y props opcionales `placeholder`, `required` y `disabled` para conservar los nombres visibles, IDs y validaciones de los formularios.

## Scripts

- `npm run dev`: inicia el servidor de desarrollo.
- `npm run build`: genera la compilacion de produccion.
- `npm run lint`: ejecuta ESLint.
- `npm run preview`: sirve localmente la compilacion de produccion.
