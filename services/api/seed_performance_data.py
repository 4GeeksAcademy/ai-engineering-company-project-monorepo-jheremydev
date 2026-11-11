"""Populate an empty local API process with representative performance data."""

import json
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"
RANDOM_SEED = 20261021
INCIDENT_COUNT = 180
MOVEMENT_COUNT = 420

LOCATIONS = [
    "Poblado", "Laureles", "Centro Medellín", "Envigado", "Rionegro",
    "Cartagena Centro", "Barranquilla Norte", "Bogotá Zona G",
    "Miami Brickell", "Miami Doral", "Kendall", "Coral Gables",
    "Fort Lauderdale", "Orlando Lake Eola",
]

ARTICLES = [
    ("Punta de anca", "carne", "kg", "18.0"),
    ("Costilla de res", "carne", "kg", "14.0"),
    ("Pechuga de pollo", "carne", "kg", "12.0"),
    ("Chorizo artesanal", "carne", "kg", "8.0"),
    ("Tomate chonto", "verduras", "kg", "9.0"),
    ("Cebolla blanca", "verduras", "kg", "7.0"),
    ("Aguacate hass", "verduras", "kg", "10.0"),
    ("Lechuga romana", "verduras", "unidad", "12.0"),
    ("Papa criolla", "verduras", "kg", "11.0"),
    ("Limón tahití", "verduras", "kg", "8.0"),
    ("Salsa de la casa", "salsas", "l", "6.0"),
    ("Ají ahumado", "salsas", "l", "4.0"),
    ("Gaseosa cola", "bebidas", "unidad", "36.0"),
    ("Agua sin gas", "bebidas", "unidad", "30.0"),
    ("Limonada de panela", "bebidas", "l", "10.0"),
    ("Cerveza lager", "bebidas", "unidad", "24.0"),
    ("Caja para llevar mediana", "packaging", "unidad", "80.0"),
    ("Servilletas kraft", "packaging", "unidad", "120.0"),
    ("Desengrasante de cocina", "productos de limpieza", "l", "5.0"),
    ("Jabón lavaloza", "productos de limpieza", "l", "4.0"),
]

INCIDENT_CHANNELS = [
    "WhatsApp", "Teléfono", "Email", "Presencial / en local", "Sistema POS",
]
INCIDENT_TYPES = [
    "Quiebre de stock", "Merma anómala", "Proveedor", "Ventas / POS",
    "Personal / RRHH", "Calidad / Formación", "Marketing / Digital",
]
SEVERITIES = ["Baja", "Media", "Alta", "Crítica"]
AREAS = [
    "Operaciones de Restaurante", "Compras y Proveedores",
    "Marketing y Experiencia Digital", "Personas y Cultura",
    "Formación y Estándares de Calidad", "Tecnología",
    "Dirección Ejecutiva",
]
INCIDENT_AUTHORS = [
    "María Gómez", "Andrés Vélez", "Laura Cárdenas", "Julián Restrepo",
    "Sofía Muñoz", "Daniela Ruiz", "Carlos Herrera", "Camila Torres",
    "Equipo de turno Medellín", "Supervisión Florida",
]
MOVEMENT_AUTHORS = [
    "Jefe de cocina", "Auxiliar de bodega", "Supervisor de turno",
    "Coordinación de compras", "Recepción de proveedores",
]
MOVEMENT_REASONS = [
    "Recepción de pedido semanal", "Reposición por consumo del turno",
    "Conteo físico de inventario", "Ajuste por merma de cocina",
    "Entrega extraordinaria de proveedor", "Traslado operativo registrado",
]


def request_json(
    method: str,
    path: str,
    payload: Optional[dict[str, object]] = None,
) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError(f"{method} {path} failed: {error}") from error


def seed() -> None:
    rng = random.Random(RANDOM_SEED)
    initial_counts = {
        "incidents": len(request_json("GET", "/incidents")),
        "locals": len(request_json("GET", "/inventory/locals")),
        "articles": len(request_json("GET", "/inventory/articles")),
        "movements": len(request_json("GET", "/inventory/movements")),
    }
    if any(initial_counts.values()):
        raise RuntimeError(
            "Refusing to seed non-empty collections; current counts: "
            f"{initial_counts}"
        )

    locals_by_id = [
        request_json("POST", "/inventory/locals", {"nombre": name})
        for name in LOCATIONS
    ]
    articles_by_id = [
        request_json(
            "POST",
            "/inventory/articles",
            {
                "nombre": name,
                "categoria": category,
                "unidad_medida": unit,
                "punto_reorden": reorder_point,
            },
        )
        for name, category, unit, reorder_point in ARTICLES
    ]

    balance: dict[tuple[str, str], Decimal] = {}
    movement_types: dict[str, int] = {"entrada": 0, "salida": 0, "ajuste": 0}
    now = datetime.now(timezone.utc)
    for _ in range(MOVEMENT_COUNT):
        article = rng.choice(articles_by_id)
        location = rng.choice(locals_by_id)
        key = (article["id"], location["id"])
        current_stock = balance.get(key, Decimal("0"))
        quantity = Decimal(rng.choice(["1.5", "2", "3", "4.5", "6", "8"]))
        movement_type = rng.choices(
            ["entrada", "salida", "ajuste"], weights=[65, 30, 5], k=1
        )[0]
        if movement_type != "entrada" and current_stock < quantity:
            movement_type = "entrada"
        delta = -quantity if movement_type == "salida" else quantity
        balance[key] = current_stock + delta
        movement_types[movement_type] += 1
        occurred_at = now - timedelta(
            days=rng.randrange(0, 120),
            hours=rng.randrange(0, 24),
            minutes=rng.randrange(0, 60),
        )
        request_json(
            "POST",
            "/inventory/movements",
            {
                "articulo_id": article["id"],
                "local": location["id"],
                "tipo": movement_type,
                "cantidad": str(quantity),
                "autor": rng.choice(MOVEMENT_AUTHORS),
                "fecha": occurred_at.isoformat(),
                "motivo": rng.choice(MOVEMENT_REASONS),
            },
        )

    target_states = (
        ["Abierta"] * 100
        + ["En progreso"] * 35
        + ["Escalada"] * 18
        + ["Resuelta"] * 20
        + ["Cerrada"] * 7
    )
    rng.shuffle(target_states)
    for state in target_states[:INCIDENT_COUNT]:
        incident = request_json(
            "POST",
            "/incidents",
            {
                "canal": rng.choice(INCIDENT_CHANNELS),
                "tipo": rng.choice(INCIDENT_TYPES),
                "severidad": rng.choice(SEVERITIES),
                "area_responsable": rng.choice(AREAS),
                "autor": rng.choice(INCIDENT_AUTHORS),
            },
        )
        if state != "Abierta":
            request_json(
                "PATCH",
                f"/incidents/{incident['id']}",
                {"estado": state, "autor": "Carga histórica de operaciones"},
            )

    print(f"Counts before seed: {initial_counts}")
    print(
        "Inserted: "
        f"{INCIDENT_COUNT} incidents, {len(locals_by_id)} locations, "
        f"{len(articles_by_id)} articles, {MOVEMENT_COUNT} movements."
    )
    print(f"Movement mix: {movement_types}")
    print(
        "Counts after seed: "
        f"incidents={len(request_json('GET', '/incidents'))}, "
        f"locals={len(request_json('GET', '/inventory/locals'))}, "
        f"articles={len(request_json('GET', '/inventory/articles'))}, "
        f"movements={len(request_json('GET', '/inventory/movements'))}"
    )


if __name__ == "__main__":
    try:
        seed()
    except Exception as error:
        print(f"Seed failed: {error}", file=sys.stderr)
        raise
