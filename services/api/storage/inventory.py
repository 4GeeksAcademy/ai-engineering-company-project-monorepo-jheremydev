from decimal import Decimal
from typing import Optional
from uuid import uuid4

from models.inventory import (
    Articulo,
    ArticuloCreate,
    Local,
    LocalCreate,
    Movimiento,
    MovimientoCreate,
    TipoMovimiento,
)


articulos: list[Articulo] = []
locales: list[Local] = []
movimientos: list[Movimiento] = []


class ArticleNotFoundError(ValueError):
    pass


class LocalNotFoundError(ValueError):
    pass


class NegativeStockError(ValueError):
    pass


def create_article(payload: ArticuloCreate) -> Articulo:
    article = Articulo(id=str(uuid4()), **payload.model_dump())
    articulos.append(article)
    return article


def list_articles() -> list[Articulo]:
    return list(articulos)


def find_article(article_id: str) -> Optional[Articulo]:
    return next((article for article in articulos if article.id == article_id), None)


def create_local(payload: LocalCreate) -> Local:
    local = Local(id=str(uuid4()), **payload.model_dump())
    locales.append(local)
    return local


def list_locals() -> list[Local]:
    return list(locales)


def find_local(local_id: str) -> Optional[Local]:
    return next((local for local in locales if local.id == local_id), None)


def list_movements(
    articulo_id: Optional[str] = None,
    local: Optional[str] = None,
) -> list[Movimiento]:
    return [
        movement
        for movement in movimientos
        if (articulo_id is None or movement.articulo_id == articulo_id)
        and (local is None or movement.local == local)
    ]


def find_movement(movement_id: str) -> Optional[Movimiento]:
    return next(
        (movement for movement in movimientos if movement.id == movement_id),
        None,
    )


def calculate_stock(articulo_id: str, local: str) -> Decimal:
    stock = Decimal("0")
    for movement in movimientos:
        if movement.articulo_id != articulo_id or movement.local != local:
            continue
        if movement.tipo == TipoMovimiento.ENTRADA:
            stock += movement.cantidad
        elif movement.tipo == TipoMovimiento.SALIDA:
            stock -= movement.cantidad
        else:
            stock += movement.cantidad
    return stock


def register_movement(payload: MovimientoCreate) -> Movimiento:
    if find_article(payload.articulo_id) is None:
        raise ArticleNotFoundError(
            f"Artículo no encontrado: {payload.articulo_id}"
        )
    if find_local(payload.local) is None:
        raise LocalNotFoundError(f"Local no encontrado: {payload.local}")

    resulting_stock = calculate_stock(payload.articulo_id, payload.local)
    resulting_stock += _stock_delta(payload)
    if resulting_stock < 0:
        raise NegativeStockError(
            "El movimiento dejaría el stock del artículo en el local por debajo de cero"
        )

    movement = Movimiento(id=str(uuid4()), **payload.model_dump())
    movimientos.append(movement)
    return movement


def _stock_delta(movement: MovimientoCreate) -> Decimal:
    if movement.tipo == TipoMovimiento.SALIDA:
        return -movement.cantidad
    return movement.cantidad