---
scope: uis/backoffice/src/**, services/api/**
Regla:
- Frontend: las peticiones a la API se organizan en uis/backoffice/src/api/,
  con un archivo por dominio de negocio (incidents.ts, inventory.ts, etc.) y
  un client.ts compartido con el wrapper de fetch, manejo de errores y la
  URL base (VITE_API_BASE_URL). Ningún archivo de dominio reimplementa el
  wrapper de fetch.
- Backend: los modelos y el almacenamiento se organizan por dominio en
  services/api/models/ y services/api/storage/, con un archivo por dominio
  (models/incidents.py, models/inventory.py, storage/incidents.py,
  storage/inventory.py). Los routers ya siguen esta separación
  (routers/incidents.py) y deben seguir haciéndolo para cada módulo nuevo.
- Tipos compartidos: los tipos de dominio del frontend (Incident, IncidentDetail,
  etc.) se definen en packages/shared/types/, con un archivo por dominio
  (incidents.ts, inventory.ts) reexportado desde index.ts. Las apps del
  monorepo (uis/*) los consumen vía el paquete @repo/shared-types, nunca
  redefiniéndolos localmente.

Justificación: uis/backoffice/src/api.ts mezcla todas las peticiones en un
solo archivo sin separación por dominio, y services/api/models.py y
storage.py son archivos planos sin separación por dominio. Ambos se vuelven
inmanejables en cuanto se agrega un segundo módulo de negocio
(inventory-manager).
---