import { useState } from 'react';
import type { FormEvent } from 'react';

import { listClientConsents, recordClientConsent } from '../lib/api/client';
import type { ClientConsentResponse, ConsentPurpose, ConsentStatus } from '../lib/api/types';

interface ConsentIslandProps {
  clientId: string;
  token: string;
  tenantId: string;
}

const PURPOSES: ConsentPurpose[] = [
  'analysis',
  'harmonization',
  'trend_analysis',
  'report_export',
  'replay_research_use',
  'hrv_processing',
  'media_upload_processing',
];

export function ConsentIsland({ clientId, token, tenantId }: ConsentIslandProps) {
  const [items, setItems] = useState<ClientConsentResponse[]>([]);
  const [purpose, setPurpose] = useState<ConsentPurpose>('analysis');
  const [status, setStatus] = useState<ConsentStatus>('granted');
  const [textVersion, setTextVersion] = useState('v1');
  const [expiresAt, setExpiresAt] = useState('');
  const [isWorking, setIsWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleLoad() {
    setIsWorking(true);
    setError(null);
    setMessage(null);
    try {
      const response = await listClientConsents({ token, tenantId }, clientId);
      setItems(response.items);
    } catch {
      setError('Consent-Einträge konnten nicht geladen werden. Bitte Zugriffskontext prüfen.');
    } finally {
      setIsWorking(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsWorking(true);
    setError(null);
    setMessage(null);
    try {
      const recorded = await recordClientConsent(
        { token, tenantId },
        clientId,
        {
          purpose,
          status,
          consent_text_version: textVersion,
          expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
        },
      );
      setItems((current) => [...current, recorded]);
      setMessage('Consent wurde dokumentiert.');
    } catch {
      setError('Consent konnte nicht dokumentiert werden. Bitte Eingaben und Zugriffskontext prüfen.');
    } finally {
      setIsWorking(false);
    }
  }

  return (
    <section className="shell-card" aria-labelledby="consent-title">
      <p className="muted">Consent-Gate</p>
      <h3 id="consent-title">Consent dokumentieren und prüfen</h3>
      <p className="muted">
        Consent wird als Compliance-Voraussetzung erfasst. Sitzungen, Workflows und Module bleiben bis zu ihren Gates geschlossen.
      </p>
      <div className="action-row">
        <button type="button" onClick={handleLoad} disabled={isWorking || !token || !tenantId}>
          {isWorking ? 'Lädt…' : 'Consent laden'}
        </button>
      </div>
      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Zweck
          <select value={purpose} onChange={(event) => setPurpose(event.currentTarget.value as ConsentPurpose)}>
            {PURPOSES.map((item) => (
              <option value={item} key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={status} onChange={(event) => setStatus(event.currentTarget.value as ConsentStatus)}>
            <option value="granted">granted</option>
            <option value="revoked">revoked</option>
          </select>
        </label>
        <label>
          Textversion
          <input
            name="consent_text_version"
            maxLength={80}
            required
            value={textVersion}
            onChange={(event) => setTextVersion(event.currentTarget.value)}
          />
        </label>
        <label>
          Ablaufzeit optional
          <input
            name="expires_at"
            type="datetime-local"
            value={expiresAt}
            onChange={(event) => setExpiresAt(event.currentTarget.value)}
          />
        </label>
        <button type="submit" disabled={isWorking || !token || !tenantId || !textVersion.trim()}>
          {isWorking ? 'Speichert…' : 'Consent dokumentieren'}
        </button>
      </form>
      {error ? <p className="error" role="alert">{error}</p> : null}
      {message ? <p className="success" role="status">{message}</p> : null}
      <div className="client-list" aria-live="polite">
        {items.map((item) => (
          <article className="client-summary" key={item.id}>
            <h4>{item.purpose}</h4>
            <p><span className="status-badge">{item.status}</span></p>
            <p className="muted">Textversion: {item.consent_text_version}</p>
            <p className="muted">Dokumentiert: {new Date(item.created_at).toLocaleString('de-DE')}</p>
            <p className="muted">Ablauf: {item.expires_at ? new Date(item.expires_at).toLocaleString('de-DE') : 'nicht gesetzt'}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
