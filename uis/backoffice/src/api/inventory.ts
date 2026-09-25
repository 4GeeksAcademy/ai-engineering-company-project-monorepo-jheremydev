import type {
  InventoryArticle,
  InventoryLocation,
  InventoryMovement,
  InventoryMovementFilters,
  InventoryStock,
  NewInventoryArticle,
  NewInventoryLocation,
  NewInventoryMovement,
} from '@repo/shared-types'
import { request } from './client'

export function getArticles() {
  return request<InventoryArticle[]>('/inventory/articles')
}

export function getArticle(id: string) {
  return request<InventoryArticle>(`/inventory/articles/${id}`)
}

export function createArticle(payload: NewInventoryArticle) {
  return request<InventoryArticle>('/inventory/articles', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getLocals() {
  return request<InventoryLocation[]>('/inventory/locals')
}

export function createLocal(payload: NewInventoryLocation) {
  return request<InventoryLocation>('/inventory/locals', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getMovements(filters: InventoryMovementFilters = {}) {
  const params = new URLSearchParams()
  if (filters.articulo_id) params.set('articulo_id', filters.articulo_id)
  if (filters.local) params.set('local', filters.local)
  const query = params.toString()
  return request<InventoryMovement[]>(`/inventory/movements${query ? `?${query}` : ''}`)
}

export function getMovement(id: string) {
  return request<InventoryMovement>(`/inventory/movements/${id}`)
}

export function createMovement(payload: NewInventoryMovement) {
  return request<InventoryMovement>('/inventory/movements', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getStock(articuloId: string, local: string) {
  const params = new URLSearchParams({ articulo_id: articuloId, local })
  return request<InventoryStock>(`/inventory/stock?${params.toString()}`)
}
