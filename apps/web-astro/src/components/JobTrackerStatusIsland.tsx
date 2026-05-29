import { useMemo, useState } from 'react';

import { listSessionEvents } from '../lib/api/client';
import type { EventReplayItem, Radi144WorkerEventType, RealtimeConnectionState } from '../lib/api/types';
import { ClientAccessFields } from './ClientAccessFields';

const CONNECTION_STATES: RealtimeConnectionState[] = [
  'connected',
  'reconnecting',
  'fallback',
  'offline',
  'failed',
  'auth_error',
];

const STATE_LABELS: Record<RealtimeConnectionState, string> = {
  connected: 'Verbunden',
  reconnecting: 'Verbindung wird erneuert',
  fallback: 'Fallback aktiv',
  offline: 'Offline',
  failed: 'Fehlgeschlagen',
  auth_error: 'Anmeldung prüfen',
};

const RADI144_WORKER_EVENT_TYPES: Radi144WorkerEventType[] = [
  'job.running',
  'job.done',
  'job.failed',
  'module.radi144.started',
  'module.radi144.completed',
  'module.radi144.failed',
];

const RADI144_EVENT_LABELS: Record<Radi144WorkerEventType, string> = {
  'job.running': 'Radi144 Verarbeitung läuft',
  'job.done': 'Radi144 Verarbeitung abgeschlossen',
  'job.failed': 'Radi144 Verarbeitung sicher gestoppt',
  'module.radi144.started': 'Radi144 Modul gestartet',
  'module.radi144.completed': 'Radi144 Modul abgeschlossen',
  'module.radi144.failed': 'Radi144 Modul sicher gestoppt',
};

function isRadi144WorkerEvent(event: EventReplayItem): event is EventReplayItem & { event_type: Radi144WorkerEventType } {
  return RADI144_WORKER_EVENT_TYPES.indexOf(event.event_type as Radi144WorkerEventType) >= 0;
}

function eventReason(event: EventReplayItem): string {
  const reason = event.payload.reason;
  return typeof reason === 'string' ? reason : 'kein Statusgrund gesetzt';
}

export function JobTrackerStatusIsland() {
  const [token, setToken] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [afterEventId, setAfterEventId] = useState('');
  const [connectionState, setConnectionState] = useState<RealtimeConnectionState>('offline');
  const [events, setEvents] = useState<EventReplayItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canLoad = Boolean(token && tenantId && sessionId);
  const radi144Events = useMemo(() => events.filter(isRadi144WorkerEvent), [events]);
  const latestEventLabel = useMemo(() => {
    const latest = events.at(-1);
    return latest ? `${latest.event_type} · ${new Date(latest.occurred_at).toLocaleString('de-DE')}` : 'Noch keine Events geladen.';
  }, [events]);
  const latestRadi144Label = useMemo(() => {
    const latest = radi144Events.at(-1);
    return latest ? `${RADI144_EVENT_LABELS[latest.event_type]} · ${eventReason(latest)}` : 'Noch kein Radi144 Worker-Event geladen.';
  }, [radi144Events]);

  async function handleLoad() {
    setIsLoading(true);
    setError(null);
    setConnectionState('reconnecting');
    try {
      const response = await listSessionEvents({ token, tenantId }, sessionId, afterEventId || undefined);
      setEvents(response.items);
      setNextCursor(response.next_cursor);
      setConnectionState(response.connection_state);
    } catch {
      setConnectionState('failed');
      setError('Eventstatus konnte nicht geladen werden. Bitte Zugriffskontext und Replay-Cursor prüfen.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="shell-card" aria-labelledby="jobtracker-title">
      <p className="muted">JobTracker UI Gate · Fallback zuerst</p>
      <h2 id="jobtracker-title">Verbindungsstatus & Event-Replay</h2>
      <p className="muted">
        Diese Anzeige nutzt nur den freigegebenen Realtime-Contract. Sie zeigt Verbindungszustände und Replay-Events, ohne
        Ausführung, Ergebnisdaten oder synthetischen Fortschritt zu erzeugen.
      </p>

      <div className="connection-grid" aria-label="Realtime-Verbindungszustände">
        {CONNECTION_STATES.map((state) => (
          <span className={`connection-state ${state === connectionState ? 'is-active' : ''}`} key={state}>
            {STATE_LABELS[state]}
          </span>
        ))}
      </div>

      <ClientAccessFields token={token} tenantId={tenantId} onTokenChange={setToken} onTenantIdChange={setTenantId} />
      <div className="form-grid">
        <label>
          Session-ID
          <input
            name="session_id"
            placeholder="UUID der freigegebenen Session"
            value={sessionId}
            onChange={(event) => setSessionId(event.currentTarget.value)}
          />
        </label>
        <label>
          Replay-Cursor optional
          <input
            name="after_event_id"
            placeholder="Event-ID für Replay ab Cursor"
            value={afterEventId}
            onChange={(event) => setAfterEventId(event.currentTarget.value)}
          />
        </label>
      </div>

      <div className="action-row">
        <button type="button" onClick={handleLoad} disabled={isLoading || !canLoad}>
          {isLoading ? 'Status wird geladen…' : 'Fallback-Replay laden'}
        </button>
        {nextCursor ? <span className="muted">Nächster Cursor: {nextCursor}</span> : null}
      </div>

      <p className="muted" aria-live="polite">Aktueller Status: {STATE_LABELS[connectionState]}</p>
      <p className="muted">Letztes Event: {latestEventLabel}</p>
      <p className="muted">Radi144 Worker-Status: {latestRadi144Label}</p>
      {error ? <p className="error" role="alert">{error}</p> : null}

      <div className="event-list" aria-live="polite">
        {radi144Events.length > 0 ? (
          <article className="client-summary">
            <h3>Radi144 Event-Truth</h3>
            <p className="muted">Quelle: Event-Replay der freigegebenen Session</p>
            <p className="muted">Anzahl Radi144 Worker-Events: {radi144Events.length}</p>
          </article>
        ) : null}
        {events.map((event) => (
          <article className="client-summary" key={event.event_id}>
            <h3>{isRadi144WorkerEvent(event) ? RADI144_EVENT_LABELS[event.event_type] : event.event_type}</h3>
            <p className="muted">Zeitpunkt: {new Date(event.occurred_at).toLocaleString('de-DE')}</p>
            <p className="muted">Korrelation: {event.correlation_id}</p>
            <p className="muted">Ressource: {event.resource_type ?? 'nicht gesetzt'}</p>
            {isRadi144WorkerEvent(event) ? <p className="muted">Statusgrund: {eventReason(event)}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
