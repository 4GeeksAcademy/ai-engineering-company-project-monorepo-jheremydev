export const inventoryCategories = [
  'carne',
  'verduras',
  'salsas',
  'bebidas',
  'packaging',
  'productos de limpieza',
] as const

export type InventoryCategory = typeof inventoryCategories[number]

export const movementTypes = ['entrada', 'salida', 'ajuste'] as const

export type MovementType = typeof movementTypes[number]

export interface InventoryArticle {
  id: string
  nombre: string
  categoria: InventoryCategory
  unidad_medida: string
}

export interface InventoryMovement {
  id: string
  articulo_id: string
  local: string
  tipo: MovementType
  cantidad: string
  autor: string
  fecha: string
  motivo?: string | null
}

export interface InventoryStock {
  articulo_id: string
  local: string
  stock: string
  unidad_medida: string
}

export interface NewInventoryArticle {
  nombre: string
  categoria: InventoryCategory
  unidad_medida: string
}

export interface NewInventoryMovement {
  articulo_id: string
  local: string
  tipo: MovementType
  cantidad: string
  autor: string
  fecha: string
  motivo?: string | null
}

export interface InventoryMovementFilters {
  articulo_id?: string
  local?: string
}
