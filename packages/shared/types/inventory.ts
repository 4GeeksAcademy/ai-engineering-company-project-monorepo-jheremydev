export const inventoryCategories = [
  'carne',
  'verduras',
  'salsas',
  'bebidas',
  'packaging',
  'productos de limpieza',
] as const

export type InventoryCategory = typeof inventoryCategories[number]

export const inventoryUnits = ['kg', 'g', 'l', 'ml', 'unidad'] as const

export type InventoryUnit = typeof inventoryUnits[number]

export const inventoryLocals = [
  'Local 01',
  'Local 02',
  'Local 03',
  'Local 04',
  'Local 05',
  'Local 06',
  'Local 07',
  'Local 08',
  'Local 09',
  'Local 10',
  'Local 11',
  'Local 12',
  'Local 13',
  'Local 14',
] as const

export type InventoryLocal = typeof inventoryLocals[number]

export const movementTypes = ['entrada', 'salida', 'ajuste'] as const

export type MovementType = typeof movementTypes[number]

export interface InventoryArticle {
  id: string
  nombre: string
  categoria: InventoryCategory
  unidad_medida: InventoryUnit
}

export interface InventoryMovement {
  id: string
  articulo_id: string
  local: InventoryLocal
  tipo: MovementType
  cantidad: string
  autor: string
  fecha: string
  motivo?: string | null
}

export interface InventoryStock {
  articulo_id: string
  local: InventoryLocal
  stock: string
  unidad_medida: InventoryUnit
}

export interface NewInventoryArticle {
  nombre: string
  categoria: InventoryCategory
  unidad_medida: InventoryUnit
}

export interface NewInventoryMovement {
  articulo_id: string
  local: InventoryLocal
  tipo: MovementType
  cantidad: string
  autor: string
  fecha: string
  motivo?: string | null
}

export interface InventoryMovementFilters {
  articulo_id?: string
  local?: InventoryLocal
}
