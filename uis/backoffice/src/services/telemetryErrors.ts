import { ApiError } from '../api/client'
import { track } from './telemetry'

declare const __APP_RELEASE__: string

export const RELEASE_VERSION = /^\d+\.\d+\.\d+$/.test(__APP_RELEASE__) ? __APP_RELEASE__ : '0.0.0'

type ErrorModule = 'app' | 'inventory' | 'incident_detail' | 'api_client' | 'unknown'
type LazyModule = 'inventory' | 'incident_detail'
export type UiOperation =
  | 'initial_load' | 'inventory_load' | 'incident_create' | 'incident_update' | 'article_create'
  | 'local_create' | 'movement_create' | 'stock_lookup' | 'history_load' | 'reorder_batch'
  | 'incident_detail_load' | 'incident_list_load'

// Only used to classify into controlled codes; messages and stacks are never sent.
function errorFamily(error: unknown): string {
  if (!(error instanceof Error)) return 'unknown'
  if (/dynamically imported module|Importing a module script failed|ChunkLoadError/i.test(error.message)) {
    return 'chunk_load_error'
  }
  if (error instanceof TypeError && /fetch|network/i.test(error.message)) return 'network_error'
  if (error instanceof TypeError) return 'type_error'
  if (error instanceof ReferenceError) return 'reference_error'
  if (error instanceof RangeError) return 'range_error'
  if (error instanceof SyntaxError) return 'syntax_error'
  return 'unknown'
}

function errorModule(error: unknown): ErrorModule {
  const stack = error instanceof Error ? error.stack ?? '' : ''
  if (stack.includes('InventoryManager')) return 'inventory'
  if (stack.includes('IncidentDetailView')) return 'incident_detail'
  if (stack.includes('/api/')) return 'api_client'
  if (stack.includes('App.tsx')) return 'app'
  return 'unknown'
}

let installed = false

export function installGlobalErrorTracking(): void {
  if (installed || typeof window === 'undefined') return
  installed = true
  window.addEventListener('error', (event) => {
    track('frontend.uncaught_exception', {
      module: errorModule(event.error),
      errorFamily: errorFamily(event.error),
      releaseVersion: RELEASE_VERSION,
    })
  })
  window.addEventListener('unhandledrejection', (event) => {
    track('frontend.unhandled_rejection', {
      module: errorModule(event.reason),
      errorFamily: errorFamily(event.reason),
      releaseVersion: RELEASE_VERSION,
    })
  })
}

/** Wraps a React.lazy loader so a failed chunk is reported before the error propagates. */
export function trackedLazyImport<T>(module: LazyModule, loader: () => Promise<T>): () => Promise<T> {
  return () => loader().catch((error: unknown) => {
    track('frontend.lazy_module_failed', { module, releaseVersion: RELEASE_VERSION })
    throw error
  })
}

export function trackOperationFailed(operation: UiOperation, error: unknown, formAttemptId?: string): void {
  const errorKind = error instanceof ApiError ? 'http'
    : error instanceof TypeError ? 'network_or_cors'
      : error instanceof SyntaxError ? 'decode'
        : 'unknown'
  track('ui.operation_failed', {
    operation,
    errorKind,
    ...(error instanceof ApiError ? { httpStatus: error.status } : {}),
    ...(formAttemptId ? { formAttemptId } : {}),
  })
}
