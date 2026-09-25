import type { Incident, IncidentDetail, IncidentFilters, NewIncident, IncidentUpdate } from '../types'
import { request } from './client'

export function getIncidents(filters: IncidentFilters = {}) {
  const params = new URLSearchParams()
  if (filters.estado) params.set('estado', filters.estado)
  if (filters.severidad) params.set('severidad', filters.severidad)
  if (filters.area_responsable) params.set('area_responsable', filters.area_responsable)
  const query = params.toString()
  return request<Incident[]>(`/incidents${query ? `?${query}` : ''}`)
}

export function createIncident(payload: NewIncident) {
  return request<Incident>('/incidents', { method: 'POST', body: JSON.stringify(payload) })
}

export function getIncident(id: string) {
  return request<IncidentDetail>(`/incidents/${id}`)
}

export function updateIncident(id: string, payload: IncidentUpdate) {
  return request<Incident>(`/incidents/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
}