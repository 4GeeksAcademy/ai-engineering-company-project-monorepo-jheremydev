from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class Canal(str, Enum):
    WHATSAPP = "WhatsApp"
    TELEFONO = "Teléfono"
    EMAIL = "Email"
    PRESENCIAL = "Presencial / en local"
    SISTEMA_POS = "Sistema POS"


class TipoIncidencia(str, Enum):
    QUIEBRE_DE_STOCK = "Quiebre de stock"
    MERMA_ANOMALA = "Merma anómala"
    PROVEEDOR = "Proveedor"
    VENTAS_POS = "Ventas / POS"
    PERSONAL_RRHH = "Personal / RRHH"
    CALIDAD_FORMACION = "Calidad / Formación"
    MARKETING_DIGITAL = "Marketing / Digital"


class Severidad(str, Enum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"
    CRITICA = "Crítica"


class AreaResponsable(str, Enum):
    OPERACIONES_DE_RESTAURANTE = "Operaciones de Restaurante"
    COMPRAS_Y_PROVEEDORES = "Compras y Proveedores"
    MARKETING_Y_EXPERIENCIA_DIGITAL = "Marketing y Experiencia Digital"
    PERSONAS_Y_CULTURA = "Personas y Cultura"
    FORMACION_Y_ESTANDARES_DE_CALIDAD = "Formación y Estándares de Calidad"
    TECNOLOGIA = "Tecnología"
    DIRECCION_EJECUTIVA = "Dirección Ejecutiva"


class EstadoIncidencia(str, Enum):
    ABIERTA = "Abierta"
    EN_PROGRESO = "En progreso"
    ESCALADA = "Escalada"
    RESUELTA = "Resuelta"
    CERRADA = "Cerrada"


class Incidencia(BaseModel):
    id: str
    canal: Canal
    tipo: TipoIncidencia
    severidad: Severidad
    area_responsable: AreaResponsable
    estado: EstadoIncidencia
    autor: str
    created_at: datetime
    updated_at: datetime


class HistorialCambio(BaseModel):
    id: str
    incidencia_id: str
    campo: Literal["estado", "area_responsable"]
    valor_anterior: str
    valor_nuevo: str
    autor: str
    timestamp: datetime
