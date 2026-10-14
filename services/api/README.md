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

## Endpoints actuales

- `GET /health`: confirma que la API está levantada.
- `GET /docs`: documentación OpenAPI interactiva generada por FastAPI.

El router `/incidents` está registrado como estructura inicial del dominio. La lógica de negocio y los endpoints de incidencias se implementarán en pasos posteriores, siguiendo `memory-bank/incident-manager-plan.md`.
