import sys
from typing import Any

from fastapi.testclient import TestClient

import storage
from main import app


client = TestClient(app)
passed: list[str] = []


def assert_status(response: Any, expected: int) -> None:
    assert response.status_code == expected, (
        f"Esperaba HTTP {expected}, recibí {response.status_code}: {response.text}"
    )


def record(stage: str) -> None:
    passed.append(stage)
    print(f"OK: {stage}")


def create_payload(
    *,
    severity: str = "Media",
    area: str = "Operaciones de Restaurante",
    author: str = "reporter",
) -> dict[str, str]:
    return {
        "canal": "WhatsApp",
        "tipo": "Quiebre de stock",
        "severidad": severity,
        "area_responsable": area,
        "autor": author,
    }


def run_verification() -> None:
    storage.incidencias.clear()
    storage.historial_cambios.clear()

    created_response = client.post(
        "/incidents",
        json=create_payload(author="creator"),
    )
    assert_status(created_response, 201)
    incident = created_response.json()
    incident_id = incident["id"]
    assert incident["estado"] == "Abierta"
    record("creación con estado inicial Abierta")

    state_changes = [
        ("En progreso", "progress-author"),
        ("Escalada", "escalation-author"),
        ("Resuelta", "resolution-author"),
        ("Cerrada", "closure-author"),
    ]
    expected_states = ["Abierta", "En progreso", "Escalada", "Resuelta", "Cerrada"]
    for previous_state, (new_state, author) in zip(expected_states, state_changes):
        response = client.patch(
            f"/incidents/{incident_id}",
            json={"estado": new_state, "autor": author},
        )
        assert_status(response, 200)
        assert response.json()["estado"] == new_state
        assert previous_state != new_state
    record("ciclo completo de estados con autores distintos")

    detail_response = client.get(f"/incidents/{incident_id}")
    assert_status(detail_response, 200)
    detail = detail_response.json()
    state_history = [
        change for change in detail["historial"] if change["campo"] == "estado"
    ]
    assert len(state_history) == 4
    assert [change["autor"] for change in state_history] == [
        "progress-author",
        "escalation-author",
        "resolution-author",
        "closure-author",
    ]
    assert [(change["valor_anterior"], change["valor_nuevo"]) for change in state_history] == [
        ("Abierta", "En progreso"),
        ("En progreso", "Escalada"),
        ("Escalada", "Resuelta"),
        ("Resuelta", "Cerrada"),
    ]
    assert [change["timestamp"] for change in state_history] == sorted(
        change["timestamp"] for change in state_history
    )
    record("historial con cuatro cambios de estado en orden cronológico")

    area_response = client.patch(
        f"/incidents/{incident_id}",
        json={
            "area_responsable": "Tecnología",
            "autor": "area-author",
        },
    )
    assert_status(area_response, 200)
    detail_after_area = client.get(f"/incidents/{incident_id}")
    assert_status(detail_after_area, 200)
    history_after_area = detail_after_area.json()["historial"]
    area_history = [
        change for change in history_after_area if change["campo"] == "area_responsable"
    ]
    state_history_after_area = [
        change for change in history_after_area if change["campo"] == "estado"
    ]
    assert len(area_history) == 1
    assert area_history[0]["autor"] == "area-author"
    assert area_history[0]["valor_anterior"] == "Operaciones de Restaurante"
    assert area_history[0]["valor_nuevo"] == "Tecnología"
    assert len(state_history_after_area) == 4
    record("cambio de área con entrada de historial independiente")

    target_response = client.post(
        "/incidents",
        json=create_payload(
            severity="Alta",
            area="Tecnología",
            author="filter-target",
        ),
    )
    assert_status(target_response, 201)
    target_id = target_response.json()["id"]
    target_update = client.patch(
        f"/incidents/{target_id}",
        json={"estado": "En progreso", "autor": "filter-target-updater"},
    )
    assert_status(target_update, 200)

    other_state_response = client.post(
        "/incidents",
        json=create_payload(
            severity="Alta",
            area="Tecnología",
            author="filter-other-state",
        ),
    )
    assert_status(other_state_response, 201)
    other_state_id = other_state_response.json()["id"]
    assert_status(
        client.patch(
            f"/incidents/{other_state_id}",
            json={"estado": "Escalada", "autor": "filter-other-state-updater"},
        ),
        200,
    )

    other_area_response = client.post(
        "/incidents",
        json=create_payload(
            severity="Alta",
            area="Compras y Proveedores",
            author="filter-other-area",
        ),
    )
    assert_status(other_area_response, 201)

    filtered_response = client.get(
        "/incidents",
        params={
            "estado": "En progreso",
            "severidad": "Alta",
            "area_responsable": "Tecnología",
        },
    )
    assert_status(filtered_response, 200)
    filtered_ids = [item["id"] for item in filtered_response.json()]
    assert filtered_ids == [target_id]
    record("filtros combinados de estado, severidad y área")

    missing_id = "missing-incident-id"
    missing_detail_response = client.get(f"/incidents/{missing_id}")
    assert_status(missing_detail_response, 404)
    missing_update_response = client.patch(
        f"/incidents/{missing_id}",
        json={"estado": "En progreso", "autor": "missing-author"},
    )
    assert_status(missing_update_response, 404)
    record("404 controlado para detalle y actualización inexistentes")


def main() -> int:
    failure: str | None = None
    try:
        run_verification()
    except AssertionError as error:
        failure = f"AssertionError: {error}"
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"

    print("\nResumen de verificación")
    print(f"- Etapas superadas: {len(passed)}")
    for stage in passed:
        print(f"  - {stage}")
    if failure:
        print(f"- Fallo: {failure}")
        return 1
    print("- Fallos: ninguno")
    return 0


if __name__ == "__main__":
    sys.exit(main())
