import type { Incident, IncidentDetail, IncidentFilters, NewIncident, IncidentUpdate } from './types'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  if (!apiBaseUrl) throw new Error('Falta configurar VITE_API_BASE_URL.')

  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    let message = `La API respondio con ${response.status}.`
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Use the HTTP status when the response is not JSON.
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

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
