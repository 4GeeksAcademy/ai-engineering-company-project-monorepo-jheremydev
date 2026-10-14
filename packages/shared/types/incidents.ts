export const channels = ['WhatsApp', 'Teléfono', 'Email', 'Presencial / en local', 'Sistema POS'] as const
export const incidentTypes = ['Quiebre de stock', 'Merma anómala', 'Proveedor', 'Ventas / POS', 'Personal / RRHH', 'Calidad / Formación', 'Marketing / Digital'] as const
export const severities = ['Baja', 'Media', 'Alta', 'Crítica'] as const
export const areas = ['Operaciones de Restaurante', 'Compras y Proveedores', 'Marketing y Experiencia Digital', 'Personas y Cultura', 'Formación y Estándares de Calidad', 'Tecnología', 'Dirección Ejecutiva'] as const
export const statuses = ['Abierta', 'En progreso', 'Escalada', 'Resuelta', 'Cerrada'] as const

export type Channel = typeof channels[number]
export type IncidentType = typeof incidentTypes[number]
export type Severity = typeof severities[number]
export type Area = typeof areas[number]
export type Status = typeof statuses[number]

export interface Incident {
  id: string
  canal: Channel
  tipo: IncidentType
  severidad: Severity
  area_responsable: Area
  estado: Status
  autor: string
  created_at: string
  updated_at: string
}

export interface ChangeHistory {
  id: string
  incidencia_id: string
  campo: 'estado' | 'area_responsable'
  valor_anterior: string
  valor_nuevo: string
  autor: string
  timestamp: string
}

export interface IncidentDetail {
  incidencia: Incident
  historial: ChangeHistory[]
}

export interface NewIncident {
  canal: Channel
  tipo: IncidentType
  severidad: Severity
  area_responsable: Area
  autor: string
}

export interface IncidentUpdate {
  autor: string
  estado?: Status
  area_responsable?: Area
}

export interface IncidentFilters {
  estado?: Status
  severidad?: Severity
  area_responsable?: Area
}