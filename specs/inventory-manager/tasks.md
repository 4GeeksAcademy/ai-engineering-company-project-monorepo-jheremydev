# Tasks de implementación - inventory-manager (Fase 3)

Cada TASK debe completarse y verificarse en su propio commit antes de iniciar la siguiente.

## TASK-01: Modelos Pydantic de inventario

- **Criterios EARS:** INV-003, INV-006, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-017, INV-018, INV-019, INV-021.
- **Plan:** §1 Modelo de datos.
- **Archivos que toca:** `services/api/models/inventory.py`; `services/api/tests/test_inventory_models.py`.
- **Qué hacer:** Implementar los modelos y enums descritos en el plan, con pruebas unitarias acotadas a sus campos y validaciones.
- **Cómo verificar:** Desde `services/api/`, ejecutar `python -m unittest discover -s tests -p "test_inventory_models.py"`. Deben aceptarse los valores de dominio válidos y cantidades decimales, y rechazarse categoría/tipo inválidos y datos requeridos ausentes, incluidos autor y fecha.
- **Commit sugerido:** `feat(inventory): add Pydantic domain models`

## TASK-02: Storage y cálculo de stock

- **Criterios EARS:** INV-001, INV-002, INV-004, INV-005, INV-011, INV-012, INV-013, INV-014, INV-015, INV-016, INV-021.
- **Plan:** §2 Cálculo de stock; §3 Almacenamiento.
- **Archivos que toca:** `services/api/storage/inventory.py`; `services/api/tests/test_inventory_storage.py`.
- **Qué hacer:** Añadir las listas y operaciones de storage indicadas en el plan; verificar el cálculo y el rechazo de movimientos antes de persistir cambios.
- **Cómo verificar:** Desde `services/api/`, ejecutar `python -m unittest discover -s tests -p "test_inventory_storage.py"`. Comprobar saldo cero sin movimientos, aislamiento por artículo y local, suma/resta de los tres tipos, decimales y que un saldo negativo rechazado no añada movimiento ni altere el saldo previo.
- **Commit sugerido:** `feat(inventory): add in-memory movement storage`

## TASK-03: Router y registro de endpoints

- **Criterios EARS:** INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-016, INV-017, INV-018, INV-019, INV-020, INV-021.
- **Plan:** §4 Endpoints.
- **Archivos que toca:** `services/api/routers/inventory.py`; `services/api/main.py`.
- **Qué hacer:** Implementar el router conforme a las rutas, contratos y errores del plan e incluirlo en la API centralizada.
- **Cómo verificar:** Desde `services/api/`, ejecutar `python -m compileall -q routers/inventory.py main.py` y `python -c "from main import app; assert any(route.path == '/inventory/stock' for route in app.routes)"`. Iniciar `uvicorn main:app --reload` y confirmar en `http://127.0.0.1:8000/docs` que aparecen las rutas del dominio.
- **Commit sugerido:** `feat(inventory): add inventory API router`

## TASK-04: Verificación del backend

- **Criterios EARS:** INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-016, INV-017, INV-018, INV-019, INV-020, INV-021.
- **Plan:** §1 Modelo de datos; §2 Cálculo de stock; §3 Almacenamiento; §4 Endpoints.
- **Archivos que toca:** `services/api/verify_inventory.py`.
- **Qué hacer:** Añadir un verificador repetible con `TestClient`, siguiendo `services/api/verify_incidents.py`; aislar el estado en memoria para que pueda ejecutarse más de una vez y probar casos válidos e inválidos del contrato.
- **Cómo verificar:** Desde `services/api/`, ejecutar `python verify_inventory.py`; cada etapa debe reportar `OK` y el resumen debe indicar cero fallos. El script debe afirmar `201` para registros válidos, `200` para consultas (incluido stock inicial cero), `422` para payload incompleto, `404` para artículo inexistente, `409` para saldo negativo y `405` para métodos de mutación no admitidos; tras los rechazos, saldo e historial deben permanecer iguales. Además, iniciar `uvicorn main:app --reload` y confirmar en `/docs` las rutas documentadas.
- **Commit sugerido:** `test(inventory): add backend API verification script`

## TASK-05: Tipos compartidos

- **Criterios EARS:** INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-017, INV-018, INV-019, INV-021.
- **Plan:** §5 Tipos compartidos.
- **Archivos que toca:** `packages/shared/types/inventory.ts`; `packages/shared/types/index.ts`.
- **Qué hacer:** Declarar los tipos de dominio, payloads, filtros y respuesta de stock del plan y reexportarlos desde el barrel compartido.
- **Cómo verificar:** Desde la raíz, ejecutar `npm run build --workspace backoffice`. TypeScript debe resolver el barrel compartido sin errores y conservar los tipos actuales de incidencias.
- **Commit sugerido:** `feat(shared-types): add inventory types`

## TASK-06: Cliente API del dominio

- **Criterios EARS:** INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-016, INV-017, INV-018, INV-019, INV-020, INV-021.
- **Plan:** §4 Endpoints; §5 Tipos compartidos; §6 Cliente API frontend.
- **Archivos que toca:** `uis/backoffice/src/api/inventory.ts`.
- **Qué hacer:** Implementar las funciones de consulta y registro descritas en el plan, usando tipos de `@repo/shared-types` y el `request<T>` compartido; no añadir llamadas de escritura para stock ni de edición/eliminación de movimientos.
- **Cómo verificar:** Desde la raíz, ejecutar `npm run build --workspace backoffice` y `npm run lint --workspace backoffice`. Ambos deben finalizar sin errores de TypeScript o ESLint.
- **Commit sugerido:** `feat(backoffice): add inventory API client`

## TASK-07: UI mínima de inventario

- **Criterios EARS:** INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-016, INV-017, INV-018, INV-019, INV-020, INV-021.
- **Plan:** §6 Cliente API frontend; §7 Fuera de este plan.
- **Archivos que toca:** `uis/backoffice/src/App.tsx`; `uis/backoffice/src/App.css` (y los componentes frontend estrictamente necesarios dentro de `uis/backoffice/src/`).
- **Qué hacer:** Incorporar al backoffice un formulario para registrar artículos, un formulario para registrar entradas/salidas/ajustes y una vista para consultar el stock por artículo y local. Mantener la integración con el cliente API de inventario; las decisiones visuales concretas se toman al implementar, siguiendo el patrón existente de incidencias.
- **Cómo verificar:** Desde la raíz, ejecutar `npm run build --workspace backoffice` y `npm run lint --workspace backoffice`. Para la comprobación funcional, configurar `VITE_API_BASE_URL=http://localhost:8000`, iniciar la API con `uvicorn main:app --reload` desde `services/api/` y el backoffice con `npm run dev --workspace backoffice`; en la interfaz crear un artículo, registrar movimientos y consultar el saldo actualizado. Confirmar que no existe control para editar stock ni para modificar o eliminar movimientos.
- **Commit sugerido:** `feat(backoffice): add minimum inventory workflow`

## TASK-08: Checklist de verificación end-to-end

- **Criterios EARS:** INV-001, INV-002, INV-003, INV-004, INV-005, INV-006, INV-007, INV-008, INV-009, INV-010, INV-011, INV-012, INV-013, INV-014, INV-015, INV-016, INV-017, INV-018, INV-019, INV-020, INV-021.
- **Plan:** §2 Cálculo de stock; §4 Endpoints; §6 Cliente API frontend; §7 Fuera de este plan.
- **Archivos que toca:** `specs/inventory-manager/e2e-checklist.md`.
- **Qué hacer:** Documentar un recorrido reproducible desde la UI para crear artículo, registrar movimientos y consultar el stock; incluir las comprobaciones de rechazo requeridas para los invariantes y confirmar que fallar no modifica el saldo ni el historial.
- **Cómo verificar:** Seguir el checklist con API y backoffice activos. Confirmar el saldo tras el flujo válido; intentar una escritura directa de stock (INV-001, INV-007), una salida o ajuste negativo que cruce cero (INV-016) y `PATCH`/`DELETE` de un movimiento existente (INV-020). Observar rechazo HTTP para cada intento y comprobar después que el saldo e historial siguen intactos. Reiniciar la API antes del recorrido para partir de storage limpio.
- **Commit sugerido:** `docs: add inventory end-to-end checklist`