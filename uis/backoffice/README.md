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

Todo el tracking pasa por `track(eventType, properties)` de `src/services/telemetry.ts`; ningun otro archivo llama a `fetch` para telemetria. El servicio genera el envelope de `docs/telemetry/event-schemas.json` (`eventId`, `timestamp` de captura, `sessionId` anonimo por pestana en `sessionStorage`, `userId` siempre `null`, `schemaVersion` desde `@repo/shared-types`, `requestId`, `source`, `environment`). Encola en memoria y envia lotes cada 10 s o al llegar a 20 eventos, con hasta 3 intentos y backoff exponencial (1 s, 2 s); hace flush con `sendBeacon` cuando la pestana pasa a `hidden`. `trackRequest()` es un helper interno reservado a `src/api/client.ts` para correlacionar eventos con el `X-Request-ID` de una peticion; ademas asocia cada respuesta de la API con su `requestId`, y `track(eventType, properties, respuesta)` lo hereda sin que el componente lo maneje. `track()` descarta (sin encolar) cualquier evento cuyo `event_type` no sea de navegador o cuyas propiedades no cumplan el allowlist de `event-schemas.json`.

Instrumentacion: `src/api/client.ts` (`performance.client_request_completed`), `src/services/telemetryErrors.ts` (`frontend.uncaught_exception`, `frontend.unhandled_rejection`, `frontend.lazy_module_failed`, `ui.operation_failed`), `src/hooks/useFormTelemetry.ts` (`form.started`, `form.validation_blocked`, `form.abandoned`), `src/App.tsx` (navegacion, filtros y detalle de incidencias) y `src/InventoryManager.tsx` (prerequisitos, consultas de stock, indicador de reorden, seleccion de articulo). Los eventos obligatorios de inventario los emite el backend (`source: "api"`).

## Componentes compartidos

`src/components/SelectField.tsx` reutiliza los selectores con la clase `field` en incidencias e inventario. Acepta opciones de texto o `{ value, label }` y props opcionales `placeholder`, `required` y `disabled` para conservar los nombres visibles, IDs y validaciones de los formularios.

## Scripts

- `npm run dev`: inicia el servidor de desarrollo.
- `npm run build`: genera la compilacion de produccion.
- `npm run lint`: ejecuta ESLint.
- `npm run preview`: sirve localmente la compilacion de produccion.
