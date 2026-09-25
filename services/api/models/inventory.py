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


class UnidadMedida(str, Enum):
    KG = "kg"
    G = "g"
    L = "l"
    ML = "ml"
    UNIDAD = "unidad"


class Local(str, Enum):
    LOCAL_01 = "Local 01"
    LOCAL_02 = "Local 02"
    LOCAL_03 = "Local 03"
    LOCAL_04 = "Local 04"
    LOCAL_05 = "Local 05"
    LOCAL_06 = "Local 06"
    LOCAL_07 = "Local 07"
    LOCAL_08 = "Local 08"
    LOCAL_09 = "Local 09"
    LOCAL_10 = "Local 10"
    LOCAL_11 = "Local 11"
    LOCAL_12 = "Local 12"
    LOCAL_13 = "Local 13"
    LOCAL_14 = "Local 14"


class TipoMovimiento(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"


class ArticuloCreate(BaseModel):
    nombre: TextoNoVacio
    categoria: CategoriaArticulo
    unidad_medida: UnidadMedida


class Articulo(ArticuloCreate):
    id: str


class MovimientoCreate(BaseModel):
    articulo_id: TextoNoVacio
    local: Local
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
