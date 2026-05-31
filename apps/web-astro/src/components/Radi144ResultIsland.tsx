import { useMemo, useState } from 'react';

import { listSessionEvents } from '../lib/api/client';
import type { EventReplayItem } from '../lib/api/types';
import { ClientAccessFields } from './ClientAccessFields';

interface Radi144ResultIslandProps {
  session_id: string;
}

type ResultState = 'idle' | 'loading' | 'loaded' | 'not_found' | 'error';

const RADI144_EVENT_TYPES = new Set([
  'job.running',
  'job.done',
  'job.failed',
  'module.radi144.started',
  'module.radi144.completed',
  'module.radi144.failed',
]);

function moduleStatus(events: EventReplayItem[]): string {
  if (events.some((event) => event.event_type === 'module.radi144.completed' || event.event_type === 'job.done')) {
    return 'abgeschlossen';
  }
  if (events.some((event) => event.event_type === 'module.radi144.failed' || event.event_type === 'job.failed')) {
    return 'fehlgeschlagen';
  }
  if (events.some((event) => event.event_type === 'module.radi144.started' || event.event_type === 'job.running')) {
    return 'läuft';
  }
  return 'nicht gefunden';
}

function payloadValue(event: EventReplayItem, key: string): string | null {
  const value = event.payload[key];
  return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' ? String(value) : null;
}

export function Radi144ResultIsland({ session_id }: Radi144ResultIslandProps) {
  const [token, setToken] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [state, setState] = useState<ResultState>('idle');
  const [events, setEvents] = useState<EventReplayItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const radi144Events = useMemo(
    () => events.filter((event) => RADI144_EVENT_TYPES.has(event.event_type)),
    [events],
  );
  const latestEvent = radi144Events.at(-1);
  const status = moduleStatus(radi144Events);
  const canLoad = Boolean(session_id && token && tenantId);

  async function handleLoad() {
    if (!canLoad) {
      return;
    }
    setState('loading');
    setError(null);
    try {
      const response = await listSessionEvents({ token, tenantId }, session_id);
      const nextEvents = response.items.filter((event) => RADI144_EVENT_TYPES.has(event.event_type));
      setEvents(response.items);
      setState(nextEvents.length > 0 ? 'loaded' : 'not_found');
    } catch (caught) {
      setEvents([]);
      setState('error');
      setError(caught instanceof Error && caught.message.includes('404') ? 'Ergebnis nicht gefunden' : 'Ergebnis konnte nicht geladen werden');
    }
  }

  return (
    <section className="shell-card" aria-labelledby="radi144-result-title">
      <p className="muted">Radi144 Projektion</p>
      <h2 id="radi144-result-title">Radi144 Analyse Ergebnis</h2>
      <p className="muted">{session_id ? `Session: ${session_id}` : 'Analyse wird geladen...'}</p>
      <ClientAccessFields token={token} tenantId={tenantId} onTokenChange={setToken} onTenantIdChange={setTenantId} />
      <div className="action-row">
        <button type="button" onClick={handleLoad} disabled={!canLoad || state === 'loading'}>
          {state === 'loading' ? 'Lade Analyse...' : 'Analyse laden'}
        </button>
      </div>

      {state === 'not_found' ? <p className="error" role="alert">Ergebnis nicht gefunden</p> : null}
      {state === 'error' ? <p className="error" role="alert">{error}</p> : null}

      {state === 'loaded' ? (
        <article className="client-summary">
          <h3>ModuleRun-Status: {status}</h3>
          <p className="muted">Letztes Radi144 Event: {latestEvent?.event_type ?? 'nicht gesetzt'}</p>
          <p className="muted">Statusgrund: {latestEvent ? (payloadValue(latestEvent, 'reason') ?? 'kein Statusgrund gesetzt') : 'kein Statusgrund gesetzt'}</p>
          <p className="muted">Projektion geschrieben: {latestEvent ? (payloadValue(latestEvent, 'projection_written') ?? 'nicht gemeldet') : 'nicht gemeldet'}</p>
        </article>
      ) : null}
    </section>
  );
}
