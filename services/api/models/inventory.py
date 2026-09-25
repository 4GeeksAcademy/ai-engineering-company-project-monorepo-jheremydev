from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, StringConstraints, model_validator


TextoNoVacio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CategoriaArticulo(str, Enum):
    CARNE = "carne"
    VERDURAS = "verduras"
    SALSAS = "salsas"
    BEBIDAS = "bebidas"
    PACKAGING = "packaging"
    PRODUCTOS_DE_LIMPIEZA = "productos de limpieza"


class TipoMovimiento(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"


class ArticuloCreate(BaseModel):
    nombre: TextoNoVacio
    categoria: CategoriaArticulo
    unidad_medida: TextoNoVacio


class Articulo(ArticuloCreate):
    id: str


class MovimientoCreate(BaseModel):
    articulo_id: TextoNoVacio
    local: TextoNoVacio
    tipo: TipoMovimiento
    cantidad: Decimal
    autor: TextoNoVacio
    fecha: datetime
    motivo: Optional[str] = None

    @model_validator(mode="after")
    def validar_cantidad(self) -> MovimientoCreate:
        if not self.cantidad.is_finite():
            raise ValueError("La cantidad debe ser un número finito")
        if self.tipo in (TipoMovimiento.ENTRADA, TipoMovimiento.SALIDA):
            if self.cantidad <= 0:
                raise ValueError("La cantidad de entrada o salida debe ser mayor que cero")
        elif self.cantidad == 0:
            raise ValueError("La cantidad de un ajuste no puede ser cero")
        return self


class Movimiento(MovimientoCreate):
    id: str
