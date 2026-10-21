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
