/** Envelope contract from docs/telemetry/event-schemas.json. Bump on breaking changes. */
export const TELEMETRY_SCHEMA_VERSION = '1.0.0' as const;

export type TelemetrySource = 'browser' | 'api' | 'probe';
export type TelemetryEnvironment = 'production' | 'development' | 'test';

export interface TelemetryEvent {
  eventId: string;
  timestamp: string;
  sessionId: string | null;
  userId: null;
  event_type: string;
  schemaVersion: typeof TELEMETRY_SCHEMA_VERSION;
  requestId: string | null;
  properties: Record<string, unknown>;
  source: TelemetrySource;
  environment: TelemetryEnvironment;
}
