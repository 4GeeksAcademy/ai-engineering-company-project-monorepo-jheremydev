# Checklist manual E2E - inventory-manager

Ejecuta los pasos en orden con la API FastAPI y el backoffice activos. Marca cada casilla solo después de observar el resultado indicado. El storage es en memoria; reiniciar Uvicorn limpia los datos de la prueba.

## Preparación

1. [ ] Detén y vuelve a iniciar Uvicorn desde `services/api/` con `uvicorn main:app --reload`. Confirma que responde en `http://127.0.0.1:8000` y que el backoffice está abierto en `http://localhost:5173` con `VITE_API_BASE_URL=http://localhost:8000`. El reinicio debe dejar el catálogo y el historial vacíos.

## Flujo válido

2. [ ] En la pestaña **Inventario**, registra un artículo de prueba, por ejemplo nombre `E2E Arroz`, categoría `verduras` y unidad `kg`. Confirma el mensaje de éxito y que el artículo aparece en el selector. Anota su nombre para identificarlo en el historial.
3. [ ] Registra una **entrada** para el artículo recién creado, local `E2E Norte`, cantidad `12.5`, autor `Verificación E2E`, fecha actual y motivo `Carga inicial`. Confirma el mensaje de éxito y que el historial muestra el tipo, cantidad, autor, fecha y motivo.
4. [ ] Registra una **salida** para el mismo artículo y local por `2.25`, con autor y fecha. Consulta el stock de ese artículo en `E2E Norte` y confirma que la UI muestra `10.25 kg`, igual al cálculo manual `12.5 - 2.25 = 10.25`. Confirma también que el historial contiene exactamente la entrada y la salida.

## Restricciones de stock e historial

5. [ ] Comprueba que la UI no ofrece campo ni acción para fijar o modificar stock. Abre `http://127.0.0.1:8000/docs`, expande `inventory` y confirma que bajo `/inventory/stock` solo existe `GET`, sin operación de escritura. **Criterios: INV-001, INV-007.**
6. [ ] Desde el formulario de movimiento, intenta registrar para `E2E Norte` una salida de `10.26` (mayor que el saldo `10.25`). Confirma que la UI muestra el detalle de rechazo de la API (`409 Conflict`). Vuelve a consultar el stock y verifica que sigue en `10.25 kg`; confirma que el historial conserva sus dos movimientos, sin añadir el intento rechazado. **Criterio: INV-016.**
7. [ ] Anota el `id` de uno de los movimientos válidos consultando `GET /inventory/movements` o la pestaña Network del navegador. En `/docs`, intenta `PATCH /inventory/movements/{movement_id}` con un cuerpo de prueba y `DELETE /inventory/movements/{movement_id}`. Confirma que ambos responden `405 Method Not Allowed`. Vuelve a consultar el movimiento por `GET /inventory/movements/{movement_id}` y el stock: sus datos deben seguir iguales y el saldo debe ser `10.25`. **Criterio: INV-020.**
8. [ ] Confirma los errores de validación y referencia desde `/docs` o el cliente HTTP: (a) intenta `POST /inventory/articles` con una categoría fuera de las seis permitidas y confirma `422`; (b) intenta `POST /inventory/movements` sin `autor` y confirma `422`; (c) intenta `POST /inventory/movements` con `articulo_id` inexistente y los demás campos válidos y confirma `404`. Comprueba después que estos intentos no aparecen en el historial y no alteran el saldo. **Criterios: INV-003, INV-006, INV-009, INV-018.**
9. [ ] En la UI, revisa el historial y confirma que es de solo lectura: no hay acciones ni controles para editar o eliminar movimientos. Al cerrar la prueba, consulta de nuevo el stock y el historial; deben coincidir exactamente con el flujo válido del paso 4: saldo `10.25 kg` y solo la entrada `12.5` y la salida `2.25`. Ninguno de los intentos rechazados debe haber dejado rastro. **Criterios: INV-001, INV-016, INV-020.**
