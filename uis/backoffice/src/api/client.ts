import { trackRequest } from '../services/telemetry'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? ''

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// Route templates allowed by the telemetry schema; ids and query strings are never sent.
const ROUTE_TEMPLATES: [RegExp, string][] = [
  [/^\/health$/, '/health'],
  [/^\/incidents$/, '/incidents'],
  [/^\/incidents\/[^/]+$/, '/incidents/{incidencia_id}'],
  [/^\/inventory\/articles$/, '/inventory/articles'],
  [/^\/inventory\/articles\/[^/]+$/, '/inventory/articles/{article_id}'],
  [/^\/inventory\/locals$/, '/inventory/locals'],
  [/^\/inventory\/movements$/, '/inventory/movements'],
  [/^\/inventory\/movements\/[^/]+$/, '/inventory/movements/{movement_id}'],
  [/^\/inventory\/stock$/, '/inventory/stock'],
]

function routeTemplate(path: string): string {
  const pathname = path.split('?')[0]
  return ROUTE_TEMPLATES.find(([pattern]) => pattern.test(pathname))?.[1] ?? 'other'
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  return trackRequest(async ({ headers: telemetryHeaders, track }) => {
    const method = (options?.method ?? 'GET').toUpperCase()
    const route = routeTemplate(path)
    const startedAt = performance.now()
    const trackCompletion = (outcome: 'success' | 'error' | 'cancelled', httpStatus?: number) => {
      track('performance.client_request_completed', {
        method,
        route,
        durationMs: Math.round((performance.now() - startedAt) * 10) / 10,
        outcome,
        ...(httpStatus === undefined ? {} : { httpStatus }),
      })
    }

    let response: Response
    try {
      response = await fetch(`${apiBaseUrl}${path}`, {
        headers: { 'Content-Type': 'application/json', ...telemetryHeaders },
        ...options,
      })
    } catch (error) {
      trackCompletion(error instanceof DOMException && error.name === 'AbortError' ? 'cancelled' : 'error')
      throw error
    }
    trackCompletion(response.ok ? 'success' : 'error', response.status)

    if (!response.ok) {
      let message = `La API respondio con ${response.status}.`
      try {
        const body = await response.json() as { detail?: string }
        if (body.detail) message = body.detail
      } catch {
        // Use the HTTP status when the response is not JSON.
      }
      throw new ApiError(message, response.status)
    }
    return response.json() as Promise<T>
  })
}