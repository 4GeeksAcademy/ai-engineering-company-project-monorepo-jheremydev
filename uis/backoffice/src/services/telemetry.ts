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

/**
 * Single entry point for backoffice telemetry. The envelope (eventId, timestamp,
 * sessionId, userId, schemaVersion, requestId, source, environment) is generated here.
 */
export function track(eventType: string, properties: Record<string, unknown>): void {
  try {
    enqueue(buildEvent(eventType, properties, null))
  } catch {
    // Telemetry must never break the UI.
  }
}

/**
 * Internal correlation helper for api/client.ts only: generates the X-Request-ID for one
 * HTTP request and a tracker whose events carry that requestId. Components use track().
 */
export function trackRequest<T>(
  run: (context: {
    requestId: string
    track: (eventType: string, properties: Record<string, unknown>) => void
  }) => Promise<T>,
): Promise<T> {
  const requestId = uuidV4()
  return run({
    requestId,
    track: (eventType, properties) => {
      try {
        enqueue(buildEvent(eventType, properties, requestId))
      } catch {
        // Telemetry must never break the UI.
      }
    },
  })
}
