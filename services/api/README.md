# Brasaland Central API

API FastAPI centralizada de Brasaland. Los dominios de la compañía se incorporarán como routers dentro de esta aplicación; el primer módulo preparado es `incidents`.

## Requisitos

- Python 3.9 o posterior

## Instalación

Desde `services/api/`:

```bash
python -m venv .venv

# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

## Ejecución

Desde `services/api/`:

```bash
uvicorn main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`.

Cada petición registra en el log de Uvicorn el método, la ruta FastAPI, el
código HTTP y `duration_ms`.

Los catálogos `GET /inventory/articles` y `GET /inventory/locals` usan caché
en memoria con TTL de 300 y 900 segundos, respectivamente. Crear un artículo
o un local invalida inmediatamente su catálogo. La caché es local al proceso
de la API; si se ejecutan varios workers o réplicas, se necesitará una
estrategia compartida de caché e invalidación.

Para cargar datos variados en una API local recién iniciada y vacía:

```bash
python seed_performance_data.py
```

El script inserta 180 incidencias, 14 locales, 20 artículos y 420 movimientos
con fechas distribuidas durante los últimos 120 días. Rechaza colecciones no
vacías para evitar duplicados. Como el almacenamiento es en memoria, los datos
solo viven en el proceso de API que recibe las peticiones y desaparecen al
reiniciarlo.

## Endpoints actuales

- `GET /health`: confirma que la API está levantada.
- `GET /docs`: documentación OpenAPI interactiva generada por FastAPI.

El router `/incidents` está registrado como estructura inicial del dominio. La lógica de negocio y los endpoints de incidencias se implementarán en pasos posteriores, siguiendo `memory-bank/incident-manager-plan.md`.

## Telemetría persistida en Supabase

Aplicar primero la [migración de almacenamiento](../../infra/supabase/README.md).
Configurar en el proceso del **backend** `SUPABASE_URL` (origen HTTPS del proyecto)
y `SUPABASE_SERVICE_ROLE_KEY` (clave backend con rol `service_role`).
No usar prefijos `VITE_`/`NEXT_PUBLIC_`, incluir claves en código ni compartirlas
en logs o chat. En Compose, el servicio API ya carga estas variables desde el
archivo de entorno raíz. Al ejecutar uvicorn directamente, exportarlas en su
entorno: la API no carga archivos de entorno automáticamente.

El servicio `interfaces` no carga el archivo de entorno completo: Compose le
entrega solo los puertos y la configuración pública del proxy. Las peticiones
de dominio y telemetría usan rutas relativas y el proxy hacia `api`, sin
credenciales de Supabase en el contenedor de interfaces. Si el puerto del
backoffice está ocupado, sobrescribirlo en PowerShell antes de iniciar:

```powershell
$env:BACKOFFICE_PORT = "5175"
docker compose up --build interfaces
```

El servicio inicia backoffice y website juntos; el puerto de website también
debe estar libre. No usar `docker compose config` para compartir la configuración
resuelta, porque puede mostrar secretos del servicio API.
El comando de `interfaces` normaliza los finales CRLF de la copia de `start.sh`
en el contenedor antes de ejecutarla, para admitir checkouts de Windows sin
modificar el script fuente. Los bind mounts no cubren ese script.

`TELEMETRY_ENDPOINT` sigue siendo la URL del colector usada por los emisores,
por ejemplo `http://127.0.0.1:8000/telemetry/events`; no es la URL de Supabase.

`POST /telemetry/events` recibe `{"events": [...]}` sin validar el lote completo
como `list[TelemetryEvent]`. Cada elemento pasa por el modelo existente y por
el [JSON Schema](../../docs/telemetry/event-schemas.json), con comprobación de
formatos, claves, valores y objetos anidados. Un elemento inválido se cuenta
como rechazado sin impedir procesar los restantes. No se registran payloads
ni mensajes de validación con datos de usuario.

Los válidos se envían en un único POST de inserción masiva a Supabase; únicamente
`properties` cambia de nombre a `tags`. No se actualizan ni eliminan eventos.
La respuesta es HTTP 200 con `{"received": N, "stored": M, "rejected": R}` y
`N = M + R`. Un lote vacío o totalmente inválido no contacta Supabase.
Un body sin arreglo `events`, o JSON malformado, devuelve 422.

Si faltan credenciales o falla Supabase, devuelve HTTP 503 con detalle genérico
y log seguro; no devuelve un éxito ficticio. La inserción es atómica: un conflicto
de PK por `eventId` repetido rechaza toda la operación y produce 503. No hay
upsert, deduplicación silenciosa ni reintentos dentro del handler; los reintentos
de emisores no garantizan entrega exactamente una vez.

El contenedor incluye el schema usando el contexto adicional `monorepo` de
Compose, igual que la infraestructura de interfaces. Reconstruir la imagen API
tras cambios al schema. Un schema ausente o inválido impide iniciar el colector
en vez de desactivar silenciosamente la validación.
