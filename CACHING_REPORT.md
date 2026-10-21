# Fase 1 — Auditoría de rendimiento y candidatos de caching

**Estado:** Fase 1 medida y documentada; Fase 2 implementa caché de catálogos, lazy loading y el `useMemo` propuesto.

## Metodología

- Rama `feature/caching-optimisation`, basada en `feature/serialization-audit`.
- Arranqué FastAPI y las dos aplicaciones Vite. `/health` y ambas páginas respondieron HTTP 200. La API permitió preflight CORS para los orígenes configurados `http://localhost:5173` y `http://localhost:5174`; los primeros intentos con origen `127.0.0.1` fallaron por no coincidir con esa allowlist, así que la verificación siguió usando `localhost` sin cambiar CORS.
- El middleware en `services/api/main.py` registra en la salida de Uvicorn método, plantilla de ruta, status y duración de extremo a extremo del middleware (`duration_ms`, tres decimales). Incluye serialización/respuesta del endpoint, pero no latencia de red del cliente.
- Antes del seed las cuatro colecciones estaban vacías: 0 incidencias, 0 locales, 0 artículos y 0 movimientos. El proceso in-memory no era una muestra de carga.
- `services/api/seed_performance_data.py` insertó **634 registros principales**: 180 incidencias, 14 locales, 20 artículos y 420 movimientos; 80 incidencias recibieron un cambio de estado, creando además historial. Los locales abarcan Colombia y Florida, hay artículos de las categorías del dominio y movimientos con entradas/salidas/ajustes y fechas distribuidas en los últimos 120 días. El stock resultante se mantuvo no negativo.
- En el proceso instrumentado repetí cada uno de los nueve endpoints `GET` ocho veces con la misma ruta y los mismos filtros/IDs. Las llamadas de seed también recorrieron repetidamente las cinco rutas de escritura. Los logs resultantes contienen al menos ocho observaciones de cada endpoint; `n` abajo incluye además lecturas de preparación/verificación y operaciones de seed.
- Las latencias son medianas (`p50`) de una corrida secuencial local, sin concurrencia. Sirven para comparar rutas en esta muestra, no para inferir SLA o capacidad de producción.
- Ejecuté `npm run build` para los dos frontends antes de medir bundle: backoffice JavaScript **243.41 kB / 74.07 kB gzip**, CSS 9.84 kB / 2.75 kB gzip; website JavaScript **224.29 kB / 70.23 kB gzip**, CSS 3.87 kB / 1.28 kB gzip. El build incluye todos los módulos en un chunk JavaScript por aplicación; no hay desglose medido por componente.

## Candidatos de backend

Los tiempos siguientes son sin caching y con el seed descrito. La frecuencia procede de las llamadas observadas en el código del backoffice, no de analítica de usuarios de producción.

| Método y endpoint | Propósito | Coste medido (p50; n) | Frecuencia estimada | Estabilidad | Evaluación |
|---|---|---:|---|---|---|
| `GET /health` | Estado de servicio | 1.190 ms; n=9 | No lo llama el frontend; probable polling operativo, no medido. | Debe reflejar disponibilidad actual. | **No cachear:** un valor cacheado puede ocultar una caída. El primer request frío fue 19.243 ms; el resto quedó alrededor de 1 ms. |
| `POST /incidents` | Crear incidencia | 1.772 ms; n=180 | Por envío explícito del formulario. | Mutación. | No cachear. |
| `GET /incidents` | Listar/filtrar incidencias | 2.178 ms; n=11 | Dos lecturas iniciales en `App`, más filtros y recargas después de crear/actualizar. | Cambia en cada alta o cambio de estado/área; estable entre escrituras. | **Candidato privado condicional.** Es la lectura GET más costosa de esta muestra y de frecuencia alta. La respuesta incluye `autor` (nombres/atribución interna): no usar caché compartida; solo valorar caché privada por usuario cuando exista una identidad de usuario y una política de invalidación tras escritura. Hoy no hay autenticación ni clave de usuario disponible. |
| `GET /incidents/{incidencia_id}` | Detalle e historial | 1.418 ms; n=8 | Al abrir una incidencia y después de guardar cambios. | El historial cambia en actualizaciones. | No caché compartida; `autor` en el historial. La lectura es puntual y de bajo coste. |
| `PATCH /incidents/{incidencia_id}` | Actualizar seguimiento | 1.899 ms; n=80 | Solo al guardar cambios. | Mutación; modifica estado/área y `updated_at`. | No cachear. |
| `POST /inventory/locals` | Crear local | 2.603 ms; n=14 | Acción administrativa poco frecuente. | Mutación infrecuente. | No cachear. |
| `GET /inventory/locals` | Catálogo de locales | 1.206 ms; n=11 | Una carga al montar el gestor; recarga tras crear local. | Muy estable; cambia solo al crear local. | **Candidato secundario a caché compartida:** payload pequeño y no personalizado, con invalidación en alta. El coste absoluto observado es bajo, por lo que la ganancia inmediata sería modesta. |
| `POST /inventory/articles` | Crear artículo | 2.114 ms; n=20 | Acción administrativa poco frecuente. | Mutación infrecuente. | No cachear. |
| `GET /inventory/articles` | Catálogo de artículos | 1.173 ms; n=11 | Una carga al montar el gestor; recarga tras crear artículo o movimiento. | Muy estable; cambia solo al crear artículo. | **Candidato secundario a caché compartida:** catálogo no personalizado e invalidable en alta. Coste absoluto bajo; confirmar que las lecturas concurrentes/producción lo justifican antes de implementar. |
| `GET /inventory/articles/{article_id}` | Detalle de artículo | 1.314 ms; n=8 | Hay wrapper cliente, pero no se invoca desde la UI actual. | Muy estable salvo alta del artículo. | No priorizar hasta que exista consumidor frecuente; ahorro marginal en la UI presente. |
| `POST /inventory/movements` | Registrar movimiento | 1.990 ms; n=420 (máx. 13.321 ms) | Acción explícita de registro. | Mutación que cambia stock e historial. | No cachear. |
| `GET /inventory/movements` | Historial de movimientos filtrable | 1.473 ms; n=11 | Una carga al abrir inventario; recarga tras crear artículo o registrar movimiento. | Historial append-only: estable entre altas, pero crece y cambia con cada movimiento. | **No compartir en caché:** incluye `autor` y aumenta con escrituras; no tiene scope de usuario disponible. Es candidato a medir con volumen/concurrencia mayores, no a cachear compartidamente ahora. |
| `GET /inventory/movements/{movement_id}` | Detalle de movimiento | 1.170 ms; n=8 | Wrapper presente pero sin llamada desde la UI. | Inmutable una vez creado. | No priorizar: sin consumidor frecuente y coste local bajo. |
| `GET /inventory/stock` | Stock derivado por artículo/local | 1.421 ms; n=8 | El montaje de inventario solicita stock para cada artículo/local seleccionado; también hay consulta manual y refresco tras movimiento. | Muy volátil: deriva de movimientos y queda obsoleto tras cualquier escritura. | **No candidato de caché simple:** aunque puede ser frecuente, necesita invalidación por par artículo/local en cada movimiento; latencia observada baja. |

### Candidatos mejor posicionados

1. **`GET /incidents`**, como caché privada/user-scoped condicional: mayor coste GET medido (p50 2.178 ms), varias llamadas por sesión de uso y estabilidad entre escrituras. **No habilitar clave compartida:** devuelve nombres de autores y hoy no hay identidad autenticada para aislar entradas.
2. **`GET /inventory/articles`**, como caché de catálogo con invalidación en alta: estable, se recarga al entrar al módulo y tras crear artículo, p50 1.173 ms. No contiene autor/datos de sesión y es técnicamente apto para caché compartida si la política de frescura lo permite.

`GET /inventory/locals` es otro candidato de bajo riesgo con comportamiento similar. La medición no demuestra una mejora perceptible: todos los GET tuvieron p50 entre **1.170 y 2.178 ms** en esta máquina y carga, y no se midió concurrencia. Se consideran prioridades de experimento, no una justificación para activar caching en producción sin una prueba representativa.

## Candidatos de frontend

### Lazy Loading

| Componente/ruta | Evidencia y justificación | Beneficio estimado |
|---|---|---|
| `InventoryManager` en `uis/backoffice/src/App.tsx` | Se importa estáticamente, pero solo se renderiza cuando el usuario selecciona la pestaña Inventario. Es una vista de 580 líneas que carga listas, historial y gestión de stock; el usuario que entra al backoffice para incidencias descarga código que no usa en esa sesión. | El chunk principal actual mide 243.41 kB (74.07 kB gzip). Un `import()` podría diferir parte de ese código hasta abrir Inventario. No hay chunk por componente en el build actual, así que el ahorro exacto no se puede atribuir sin implementar y volver a construir. |
| `IncidentDetailView` en `uis/backoffice/src/App.tsx` | Solo se monta cuando existe `selectedId`, después de elegir una fila. Puede extraerse a un módulo dinámico para diferir el drawer, formulario de actualización e historial hasta que se abra un detalle. | Reduce JavaScript inicial para usuarios que solo revisan la tabla. El módulo actual está dentro del chunk común; tamaño individual no medido. Validar que la primera apertura no produzca una espera perceptible. |

El website tiene un bundle JS de 224.29 kB (70.23 kB gzip), pero es una página pública estática cuyos componentes y contenido son pequeños y forman el recorrido principal. `Departments` y `Locations` aparecen más abajo en la página, pero no hay evidencia de peso suficiente para justificar división de chunk y solicitudes adicionales; no los propongo como prioridad de lazy loading.

### Oportunidad de `useMemo`

En `uis/backoffice/src/InventoryManager.tsx`, la tabla recorre `movements` y ejecuta `articles.find(...)` para resolver el nombre del artículo en cada fila. Con el seed medido son 420 movimientos y 20 artículos: el peor caso representa aproximadamente **8.400 comparaciones por render** (`O(movements × articles)`). Cambios en formularios, estados de guardado o mensajes vuelven a renderizar el componente aunque `articles` permanezca igual.

Experimento propuesto, sin implementarlo en esta fase: memoizar un `Map<articleId, article>` creado desde `articles`, con dependencias `[articles]`, y hacer búsquedas `Map.get` al renderizar filas. El coste pasa a `O(articles + movements)` para construir/usar el índice en vez de repetir `find` por movimiento; la dependencia correcta es el array `articles`, que se reemplaza al recargar el catálogo. No incluir `movements` en esas dependencias porque el índice solo depende del catálogo.

No priorizaría `useMemo` para los contadores de severidad: con 180 incidencias y cuatro categorías son cuatro filtros lineales (aprox. 720 comprobaciones), coste pequeño frente a red y renderizado de la tabla.

## Qué se descartó y por qué

- **Caché de `GET /inventory/stock`:** parece candidato por las consultas por artículo, pero el valor cambia con cada movimiento y exige invalidación por clave compuesta (`articulo_id`, `local`). Su p50 fue solo 1.421 ms; no justifica una política de invalidación adicional con la evidencia actual.
- **Caché compartida de incidencias e historial de movimientos:** las respuestas incluyen `autor`, atribución de personas internas. No hay autenticación/identidad de usuario para acotar la clave; quedan fuera de caché compartida. Una caché privada por usuario solo se reconsideraría cuando exista ese contexto.
- **Lazy loading de website:** componentes estáticos ligeros, sin rutas o dependencias pesadas y con un bundle de 70.23 kB gzip; el overhead de división y carga bajo demanda podría superar el ahorro.
- **`useMemo` para agregaciones pequeñas:** los conteos del resumen recorren pocos datos/categorías y no constituyen un cálculo costoso demostrado.

## Limitaciones de la evidencia

La API usa listas en memoria, una sola instancia local y ausencia de concurrencia. El dataset sintético mejora el tamaño de las colecciones, pero no representa distribución/ritmo real de escrituras ni usuarios simultáneos. No hay telemetría de producción ni mediciones del React Profiler; la frecuencia del frontend y la oportunidad de `useMemo` se estiman desde el código y el volumen de prueba. Repetir el benchmark con concurrencia, volumen mayor y perfiles representativos antes de elegir TTLs o aprobar caché compartida.

## Fase 2 — decisiones de implementación y verificación

### Decisiones en el backend

Se usa un diccionario/cache TTL en memoria con `threading.Lock`, sin dependencia adicional: la API solo tiene almacenamiento en memoria y `fastapi-cache` no estaba instalado. Cada catálogo conserva su TTL y una invalidación por generación evita que una lectura concurrente repueble con datos anteriores una entrada invalidada.

| Endpoint | Coste base Fase 1 (p50) | Frecuencia y estabilidad | TTL | Invalidación |
|---|---:|---|---:|---|
| `GET /inventory/articles` | 1.173 ms (n=11) | Se lee al abrir inventario y después de crear artículos o movimientos; el catálogo solo cambia al crear artículo. | **300 s (5 min)** | `POST /inventory/articles` limpia la entrada inmediatamente tras guardar. |
| `GET /inventory/locals` | 1.206 ms (n=11) | Se lee al abrir inventario; cambia solo al crear un local, una acción administrativa poco frecuente. | **900 s (15 min)** | `POST /inventory/locals` limpia la entrada inmediatamente tras guardar. |

Los TTL son un límite de frescura para cambios fuera de las rutas de escritura; dentro del flujo actual, que conserva el estado en memoria, los POST invalidan inmediatamente y no esperan al vencimiento. Artículos recibe un TTL menor porque el catálogo puede ampliarse durante la operación de inventario; los locales son un catálogo organizativo que cambia con menor frecuencia. Son valores iniciales razonables, no frecuencias de cambio medidas en producción.

La verificación HTTP en Compose usó 20 artículos y 3 locales iniciales. El middleware registró para artículos **7.091 ms en la lectura fría y 1.290 ms en la siguiente lectura**; para locales, **4.571 ms y 1.062 ms**, respectivamente. Después de crear un artículo y un local, las siguientes lecturas devolvieron **21 artículos** y **4 locales**, incluidos ambos nuevos IDs. En 12 pares adicionales, el tiempo extremo a extremo mediano del cliente fue 3.723 ms frío frente a 3.610 ms caliente para artículos; la diferencia es pequeña y sensible al ruido de red/proceso. Las mediciones confirman el hit y la invalidación, pero no demuestran un beneficio perceptible para estos catálogos pequeños.

La caché es por proceso. Es consistente con el Compose actual, que ejecuta una instancia Uvicorn sin múltiples workers y mantiene los datos en memoria. Si se agregan workers o réplicas, cada uno tendrá su propia entrada y la invalidación local no propagará; antes de ese despliegue habrá que usar una caché compartida o un mecanismo de invalidación distribuido.

### Decisiones en el frontend

- `InventoryManager` y `IncidentDetailView` se cargan con `React.lazy` dentro de límites `Suspense`. El primero solo se necesita al abrir la pestaña de inventario; el drawer solo se monta al elegir una incidencia.
- El build de backoffice pasó de un único chunk JavaScript de **243.41 kB / 74.07 kB gzip** en Fase 1 a una entrada inicial de **229.77 kB / 71.92 kB gzip**. El build actual separa `InventoryManager` (**12.11 kB / 3.05 kB gzip**) e `IncidentDetailView` (**3.64 kB / 1.26 kB gzip**) en chunks diferidos, más un chunk compartido `formatDate` (**0.16 kB / 0.15 kB gzip**). La entrada inicial ahorra aproximadamente **13.64 kB / 2.15 kB gzip**; si se abren ambos flujos, esos bytes se descargan al usarlos. Si se descargan todos los chunks, suman **245.68 kB / 76.38 kB gzip**, algo más que el chunk único previo por la división y el chunk compartido. Los builds no son una medición de latencia percibida y el desglose compara una salida anterior con el build actual.
- `InventoryManager` crea con `useMemo` un `Map<string, InventoryArticle>` dependiente solo de `[articles]` y lo usa en el render de cada movimiento. En el dataset de referencia sustituye hasta unas 8.400 comparaciones (`420 × 20`) por unas 20 inserciones y 420 consultas promedio O(1). Es una estimación algorítmica; no se ejecutó React Profiler. No se memoizan los contadores triviales de severidad.

En el navegador cargado desde `127.0.0.1:5173` se observó la carga diferida de `InventoryManager`. No se pudo completar la interacción de detalle ni las solicitudes de datos: la base API configurada usa `localhost:8000`, mientras que la página tenía origen `127.0.0.1:5173`, no permitido por CORS. Se mantuvo la configuración CORS existente y no se modificó el flujo funcional del frontend.

Las 23 pruebas unitarias del backend, el build y ESLint del backoffice pasan. Los scripts `verify_incidents.py` y `verify_inventory.py` no pudieron ejecutarse dentro de la imagen: el `TestClient` de Starlette requiere `httpx2`, ausente en el entorno y no declarado en `requirements.txt`. No se agregó una dependencia; las rutas cacheadas y su invalidación se comprobaron mediante solicitudes HTTP directas al stack Compose.

### Intercambio entre frescura y rendimiento

Un hit puede ahorrar la copia del listado y trabajo de acceso al almacenamiento, pero la medición base quedó alrededor de 1 ms y el benchmark cliente mostró una ganancia mediana pequeña. Se acepta un máximo de cinco minutos de antigüedad eventual para artículos y quince para locales solo como protección ante cambios que eludan los POST; las altas ordinarias invalidan de inmediato. Se eligieron TTL cortos para limitar sorpresas de frescura sin exigir coordinación compleja en el despliegue actual. Se deben revisar con datos reales antes de crecer a múltiples procesos.

### Qué no se cacheó

Se mantiene fuera de caché `GET /incidents`, `GET /incidents/{incidencia_id}` y `GET /inventory/movements`: contienen atribución de autor y no hay identidad de usuario con la que aislar una clave; las escrituras también cambian sus datos. No se cachea `GET /inventory/stock`, cuyo valor cambia por movimientos y requiere invalidación por par artículo/local, ni `/health`, que debe reflejar disponibilidad actual. No se añadió lazy loading a website ni `useMemo` a contadores triviales.
