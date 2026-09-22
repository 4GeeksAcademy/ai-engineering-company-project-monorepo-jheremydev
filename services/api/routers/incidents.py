from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models import (
	AreaResponsable,
	Canal,
	EstadoIncidencia,
	HistorialCambio,
	Incidencia,
	Severidad,
	TipoIncidencia,
)
import storage

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidenciaCreate(BaseModel):
	canal: Canal
	tipo: TipoIncidencia
	severidad: Severidad
	area_responsable: AreaResponsable
	autor: str


class IncidenciaUpdate(BaseModel):
	estado: Optional[EstadoIncidencia] = None
	area_responsable: Optional[AreaResponsable] = None
	autor: str


@router.post("", response_model=Incidencia, status_code=201)
def create_incident(payload: IncidenciaCreate) -> Incidencia:
	now = datetime.now()
	incident = Incidencia(
		id=str(uuid4()),
		canal=payload.canal,
		tipo=payload.tipo,
		severidad=payload.severidad,
		area_responsable=payload.area_responsable,
		estado=EstadoIncidencia.ABIERTA,
		autor=payload.autor,
		created_at=now,
		updated_at=now,
	)
	storage.incidencias.append(incident)
	return incident


@router.get("", response_model=list[Incidencia])
def list_incidents(
	estado: Optional[EstadoIncidencia] = None,
	severidad: Optional[Severidad] = None,
	area_responsable: Optional[AreaResponsable] = None,
) -> list[Incidencia]:
	return [
		incident
		for incident in storage.incidencias
		if (estado is None or incident.estado == estado)
		and (severidad is None or incident.severidad == severidad)
		and (
			area_responsable is None
			or incident.area_responsable == area_responsable
		)
	]


def _find_incident(incidencia_id: str) -> Incidencia:
	for incident in storage.incidencias:
		if incident.id == incidencia_id:
			return incident
	raise HTTPException(status_code=404, detail="Incidencia no encontrada")


@router.get("/{incidencia_id}")
def get_incident(incidencia_id: str):
	incident = _find_incident(incidencia_id)
	history = sorted(
		(
			change
			for change in storage.historial_cambios
			if change.incidencia_id == incidencia_id
		),
		key=lambda change: change.timestamp,
	)
	return {"incidencia": incident, "historial": history}


@router.patch("/{incidencia_id}", response_model=Incidencia)
def update_incident(
	incidencia_id: str, payload: IncidenciaUpdate
) -> Incidencia:
	incident = _find_incident(incidencia_id)
	now = datetime.now()

	if payload.estado is not None and payload.estado != incident.estado:
		storage.historial_cambios.append(
			HistorialCambio(
				id=str(uuid4()),
				incidencia_id=incident.id,
				campo="estado",
				valor_anterior=incident.estado.value,
				valor_nuevo=payload.estado.value,
				autor=payload.autor,
				timestamp=now,
			)
		)
		incident.estado = payload.estado

	if (
		payload.area_responsable is not None
		and payload.area_responsable != incident.area_responsable
	):
		storage.historial_cambios.append(
			HistorialCambio(
				id=str(uuid4()),
				incidencia_id=incident.id,
				campo="area_responsable",
				valor_anterior=incident.area_responsable.value,
				valor_nuevo=payload.area_responsable.value,
				autor=payload.autor,
				timestamp=now,
			)
		)
		incident.area_responsable = payload.area_responsable

	incident.updated_at = now
	return incident
