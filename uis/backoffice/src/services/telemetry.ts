import {
  TELEMETRY_SCHEMA_VERSION,
  type TelemetryEnvironment,
  type TelemetryEvent,
} from '@repo/shared-types'

const ENDPOINT: string = import.meta.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT || '/telemetry/events'
const MAX_BATCH_SIZE = 20
const FLUSH_INTERVAL_MS = 10_000
const MAX_ATTEMPTS = 3
const BASE_BACKOFF_MS = 1_000

const SESSION_STORAGE_KEY = 'brasaland.telemetry.session.v1'
const SESSION_IDLE_TIMEOUT_MS = 30 * 60 * 1000
const SESSION_MAX_AGE_MS = 24 * 60 * 60 * 1000

interface StoredSession {
  id: string
  startedAt: number
  lastActivityAt: number
}

interface PendingBatch {
  events: TelemetryEvent[]
  attempts: number
  retryTimer: ReturnType<typeof setTimeout> | null
}

interface PropertyRules {
  allowed: readonly string[]
  required: readonly string[]
}

const rules = (required: readonly string[], optional: readonly string[] = []): PropertyRules => ({
  allowed: [...required, ...optional],
  required,
})

/**
 * Browser-emitted (source=browser) event types and their property allowlists, copied from
 * docs/telemetry/event-schemas.json. API-only event types are rejected here.
 */
const BROWSER_EVENT_RULES: Record<string, PropertyRules> = {
  'inventory.stock_lookup_completed': rules(['articleId', 'localId', 'stock', 'unit', 'belowReorderPoint', 'querySource', 'observationCount', 'windowMs']),
  'inventory.reorder_indicator_displayed': rules(['articleId', 'localId', 'surface']),
  'navigation.section_viewed': rules(['view', 'trigger']),
  'inventory.article_selected': rules(['articleId', 'surface'], ['formAttemptId']),
  'incident.detail_opened': rules(['incidentId', 'trigger']),
  'incident.filters_applied': rules(['filters', 'changedFilter']),
  'incident.filter_empty_result': rules(['filters', 'rowCount']),
  'form.started': rules(['formType', 'formAttemptId']),
  'form.abandoned': rules(['formType', 'formAttemptId', 'reason', 'elapsedMs', 'inferred']),
  'inventory.prerequisite_blocked': rules(['missing']),
  'incident.edit_discarded': rules(['incidentId', 'formAttemptId', 'changedFields', 'reason']),
  'form.validation_blocked': rules(['formType', 'formAttemptId', 'field', 'rule']),
  'performance.client_request_completed': rules(['method', 'route', 'durationMs', 'outcome'], ['httpStatus']),
  'performance.backoffice_initial_load_completed': rules(['durationMs', 'outcome', 'requestCount', 'duplicateRequestCount', 'loadKind'], ['documentLoadMs']),
  'performance.inventory_view_load_completed': rules(['durationMs', 'outcome', 'loadKind'], ['moduleLoadMs', 'dataLoadMs']),
  'performance.incident_detail_load_completed': rules(['durationMs', 'outcome', 'loadKind'], ['moduleLoadMs', 'dataLoadMs']),
  'performance.reorder_batch_completed': rules(['localId', 'articleCount', 'successfulCount', 'failedCount', 'durationMs', 'outcome']),
  'frontend.uncaught_exception': rules(['module', 'errorFamily', 'releaseVersion'], ['errorFingerprint']),
  'frontend.unhandled_rejection': rules(['module', 'errorFamily', 'releaseVersion'], ['errorFingerprint']),
  'frontend.lazy_module_failed': rules(['module', 'releaseVersion'], ['errorFingerprint']),
  'api.network_failed': rules(['method', 'route', 'operation', 'failureKind'], ['formAttemptId']),
  'api.response_decode_failed': rules(['method', 'route', 'httpStatus', 'operation'], ['formAttemptId']),
  'ui.operation_failed': rules(['operation', 'errorKind'], ['httpStatus', 'formAttemptId']),
  'ui.post_write_refresh_failed': rules(['operation', 'formAttemptId', 'writeConfirmed', 'refreshStage'], ['httpStatus']),
}

function isAllowed(eventType: string, properties: Record<string, unknown>): boolean {
  const eventRules = BROWSER_EVENT_RULES[eventType]
  if (!eventRules) return false
  const keys = Object.keys(properties)
  return keys.every((key) => eventRules.allowed.includes(key))
    && eventRules.required.every((key) => properties[key] !== undefined)
}

const queue: TelemetryEvent[] = []
const pendingBatches = new Set<PendingBatch>()
let flushTimer: ReturnType<typeof setTimeout> | null = null
let memorySession: StoredSession | null = null

const environment: TelemetryEnvironment =
  import.meta.env.MODE === 'production' ? 'production'
    : import.meta.env.MODE === 'test' ? 'test'
      : 'development'

function uuidV4(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

function readStoredSession(): StoredSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY)
    return raw ? JSON.parse(raw) as StoredSession : null
  } catch {
    return memorySession
  }
}

function writeStoredSession(session: StoredSession): void {
  memorySession = session
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
  } catch {
    // Storage unavailable: the in-memory copy is used and a reload starts a new session.
  }
}

/** Anonymous per-tab session id; rotates after 30 min idle or 24 h. Never an identity. */
function currentSessionId(now: number): string {
  let session = readStoredSession()
  const expired = !session
    || now - session.lastActivityAt > SESSION_IDLE_TIMEOUT_MS
    || now - session.startedAt > SESSION_MAX_AGE_MS
  if (!session || expired) session = { id: uuidV4(), startedAt: now, lastActivityAt: now }
  else session = { ...session, lastActivityAt: now }
  writeStoredSession(session)
  return session.id
}

function buildEvent(
  eventType: string,
  properties: Record<string, unknown>,
  requestId: string | null,
): TelemetryEvent {
  const now = Date.now()
  return {
    eventId: uuidV4(),
    timestamp: new Date(now).toISOString(),
    sessionId: currentSessionId(now),
    userId: null,
    event_type: eventType,
    schemaVersion: TELEMETRY_SCHEMA_VERSION,
    requestId,
    properties: { ...properties },
    source: 'browser',
    environment,
  }
}

function scheduleFlush(): void {
  if (flushTimer !== null) return
  flushTimer = setTimeout(() => {
    flushTimer = null
    flush()
  }, FLUSH_INTERVAL_MS)
}

function flush(): void {
  if (flushTimer !== null) {
    clearTimeout(flushTimer)
    flushTimer = null
  }
  while (queue.length > 0) {
    const batch: PendingBatch = { events: queue.splice(0, MAX_BATCH_SIZE), attempts: 0, retryTimer: null }
    pendingBatches.add(batch)
    void send(batch)
  }
}

async function send(batch: PendingBatch): Promise<void> {
  batch.retryTimer = null
  batch.attempts += 1
  try {
    const response = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: batch.events }),
      keepalive: true,
    })
    if (!response.ok) throw new Error(`telemetry endpoint responded ${response.status}`)
    pendingBatches.delete(batch)
  } catch {
    if (!pendingBatches.has(batch)) return
    if (batch.attempts >= MAX_ATTEMPTS) {
      pendingBatches.delete(batch)
      return
    }
    const delay = BASE_BACKOFF_MS * 2 ** (batch.attempts - 1)
    batch.retryTimer = setTimeout(() => void send(batch), delay)
  }
}

function sendWithBeacon(events: TelemetryEvent[]): void {
  for (let i = 0; i < events.length; i += MAX_BATCH_SIZE) {
    const body = JSON.stringify({ events: events.slice(i, i + MAX_BATCH_SIZE) })
    const sent = typeof navigator.sendBeacon === 'function'
      && navigator.sendBeacon(ENDPOINT, new Blob([body], { type: 'application/json' }))
    if (!sent) {
      void fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        keepalive: true,
      }).catch(() => undefined)
    }
  }
}

/** Hands the queue and batches awaiting retry to sendBeacon so they survive tab close. */
function flushWithBeacon(): void {
  if (flushTimer !== null) {
    clearTimeout(flushTimer)
    flushTimer = null
  }
  const events = queue.splice(0, queue.length)
  for (const batch of pendingBatches) {
    if (batch.retryTimer === null) continue
    clearTimeout(batch.retryTimer)
    pendingBatches.delete(batch)
    events.push(...batch.events)
  }
  if (events.length > 0) sendWithBeacon(events)
}

if (typeof document !== 'undefined') {
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flushWithBeacon()
  })
}

function enqueue(event: TelemetryEvent): void {
  queue.push(event)
  if (queue.length >= MAX_BATCH_SIZE) flush()
  else scheduleFlush()
}

function capture(eventType: string, properties: Record<string, unknown>, requestId: string | null): void {
  try {
    if (!isAllowed(eventType, properties)) {
      if (import.meta.env.DEV) console.warn(`[telemetry] discarded ${eventType}: not in allowlist`)
      return
    }
    enqueue(buildEvent(eventType, properties, requestId))
  } catch {
    // Telemetry must never break the UI.
  }
}

/**
 * Single entry point for backoffice telemetry. The envelope (eventId, timestamp,
 * sessionId, userId, schemaVersion, requestId, source, environment) is generated here.
 * Events whose properties fall outside the schema allowlist are discarded before queueing.
 */
export function track(eventType: string, properties: Record<string, unknown>, fromResponse?: object): void {
  capture(eventType, properties, (fromResponse && responseRequestIds.get(fromResponse)) ?? null)
}

// API responses remember the X-Request-ID that produced them, so track() can correlate
// events derived from a response without components ever handling requestId.
const responseRequestIds = new WeakMap<object, string>()

/** UUID v4 for form attempts (formAttemptId), so components never need their own generator. */
export function newFormAttemptId(): string {
  return uuidV4()
}

/**
 * Internal correlation helper for api/client.ts only: generates the X-Request-ID for one
 * HTTP request (plus the anonymous session header) and a tracker whose events carry that
 * requestId. Components use track().
 */
export function trackRequest<T>(
  run: (context: {
    requestId: string
    headers: Record<string, string>
    track: (eventType: string, properties: Record<string, unknown>) => void
  }) => Promise<T>,
): Promise<T> {
  const requestId = uuidV4()
  return run({
    requestId,
    headers: {
      'X-Request-ID': requestId,
      'X-Telemetry-Session-Id': currentSessionId(Date.now()),
    },
    track: (eventType, properties) => capture(eventType, properties, requestId),
  }).then((result) => {
    if (typeof result === 'object' && result !== null) responseRequestIds.set(result, requestId)
    return result
  })
}
