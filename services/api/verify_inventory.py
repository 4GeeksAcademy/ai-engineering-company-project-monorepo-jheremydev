import sys
from decimal import Decimal
from typing import Any, Callable

from fastapi.testclient import TestClient

from main import app
from storage import inventory as storage


def assert_status(response: Any, expected: int) -> None:
    if response.status_code != expected:
        raise AssertionError(
            f"Esperaba HTTP {expected}, recibí {response.status_code}: {response.text}"
        )


def movement_payload(article_id: str, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "articulo_id": article_id,
        "local": "Brasaland Norte",
        "tipo": "entrada",
        "cantidad": 4.5,
        "autor": "verify-inventory",
        "fecha": "2026-09-25T12:00:00",
    }
    payload.update(overrides)
    return payload


def run_verification(client: TestClient) -> tuple[list[str], list[str]]:
    storage.articulos.clear()
    storage.movimientos.clear()

    passed: list[str] = []
    failed: list[str] = []
    state: dict[str, str] = {}

    def run_stage(name: str, operation: Callable[[], None]) -> None:
        try:
            operation()
        except Exception as error:
            failed.append(name)
            print(f"FALLO: {name}: {type(error).__name__}: {error}")
        else:
            passed.append(name)
            print(f"OK: {name}")

    def require_state(key: str) -> str:
        value = state.get(key)
        if value is None:
            raise AssertionError(f"Falta el dato de estado requerido: {key}")
        return value

    def get_stock(article_id: str) -> dict[str, Any]:
        response = client.get(
            "/inventory/stock",
            params={"articulo_id": article_id, "local": "Brasaland Norte"},
        )
        assert_status(response, 200)
        return response.json()

    def get_history(article_id: str) -> list[dict[str, Any]]:
        response = client.get(
            "/inventory/movements",
            params={"articulo_id": article_id, "local": "Brasaland Norte"},
        )
        assert_status(response, 200)
        return response.json()

    def create_article() -> None:
        response = client.post(
            "/inventory/articles",
            json={
                "nombre": "Artículo de verificación",
                "categoria": "verduras",
                "unidad_medida": "kg",
            },
        )
        assert_status(response, 201)
        article = response.json()
        if not article.get("id"):
            raise AssertionError("La respuesta no contiene id de artículo")
        state["article_id"] = article["id"]

    run_stage("crear artículo válido (201)", create_article)

    def check_initial_stock() -> None:
        stock = get_stock(require_state("article_id"))
        if Decimal(str(stock["stock"])) != Decimal("0"):
            raise AssertionError(f"Se esperaba stock 0, recibí {stock['stock']}")

    run_stage("consultar stock inicial en cero (200)", check_initial_stock)

    def create_entry() -> None:
        article_id = require_state("article_id")
        response = client.post(
            "/inventory/movements",
            json=movement_payload(article_id),
        )
        assert_status(response, 201)
        movement = response.json()
        if not movement.get("id"):
            raise AssertionError("La respuesta no contiene id de movimiento")
        state["movement_id"] = movement["id"]
        stock = get_stock(article_id)
        if Decimal(str(stock["stock"])) != Decimal("4.5"):
            raise AssertionError(f"Se esperaba stock 4.5, recibí {stock['stock']}")

    run_stage("registrar entrada y reflejar stock (201)", create_entry)

    def reject_negative_exit_without_mutation() -> None:
        article_id = require_state("article_id")
        stock_before = get_stock(article_id)
        history_before = get_history(article_id)
        response = client.post(
            "/inventory/movements",
            json=movement_payload(
                article_id,
                tipo="salida",
                cantidad=5,
            ),
        )
        assert_status(response, 409)
        stock_after = get_stock(article_id)
        history_after = get_history(article_id)
        if stock_after != stock_before:
            raise AssertionError("El stock cambió tras rechazar la salida negativa")
        if history_after != history_before:
            raise AssertionError("El historial cambió tras rechazar la salida negativa")

    run_stage("rechazar salida con stock negativo sin mutación (409)", reject_negative_exit_without_mutation)

    def reject_unknown_article() -> None:
        response = client.post(
            "/inventory/movements",
            json=movement_payload("missing-inventory-article"),
        )
        assert_status(response, 404)

    run_stage("rechazar artículo inexistente (404)", reject_unknown_article)

    def reject_incomplete_movements() -> None:
        article_id = require_state("article_id")
        missing_quantity = movement_payload(article_id)
        del missing_quantity["cantidad"]
        assert_status(
            client.post("/inventory/movements", json=missing_quantity),
            422,
        )

        missing_author = movement_payload(article_id)
        del missing_author["autor"]
        assert_status(
            client.post("/inventory/movements", json=missing_author),
            422,
        )

    run_stage("rechazar cantidad o autor ausentes (422)", reject_incomplete_movements)

    def reject_movement_mutations() -> None:
        article_id = require_state("article_id")
        movement_id = require_state("movement_id")
        movement_url = f"/inventory/movements/{movement_id}"
        movement_before_response = client.get(movement_url)
        assert_status(movement_before_response, 200)
        movement_before = movement_before_response.json()
        stock_before = get_stock(article_id)
        history_before = get_history(article_id)

        assert_status(client.patch(movement_url, json={"motivo": "modificado"}), 405)
        assert_status(client.delete(movement_url), 405)

        movement_after_response = client.get(movement_url)
        assert_status(movement_after_response, 200)
        if movement_after_response.json() != movement_before:
            raise AssertionError("El movimiento cambió tras rechazar su modificación")
        if get_stock(article_id) != stock_before:
            raise AssertionError("El stock cambió tras rechazar la mutación")
        if get_history(article_id) != history_before:
            raise AssertionError("El historial cambió tras rechazar la mutación")

    run_stage("rechazar PATCH/DELETE y conservar movimiento (405)", reject_movement_mutations)

    def reject_invalid_category() -> None:
        response = client.post(
            "/inventory/articles",
            json={
                "nombre": "Artículo inválido",
                "categoria": "frutas",
                "unidad_medida": "kg",
            },
        )
        assert_status(response, 422)

    run_stage("rechazar categoría inválida (422)", reject_invalid_category)

    return passed, failed


def main() -> int:
    with TestClient(app) as client:
        passed, failed = run_verification(client)

    total = len(passed) + len(failed)
    print("\nResumen de verificación")
    print(f"- Etapas totales: {total}")
    print(f"- Etapas superadas: {len(passed)}")
    print(f"- Etapas fallidas: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())