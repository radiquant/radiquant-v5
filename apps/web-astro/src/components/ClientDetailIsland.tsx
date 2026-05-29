import { FormEvent, useState } from 'react';

import { getClient, updateClient } from '../lib/api/client';
import type { ClientProfileResponse, ClientStatus } from '../lib/api/types';
import { ClientAccessFields } from './ClientAccessFields';
import { ConsentIsland } from './ConsentIsland';

interface ClientDetailIslandProps {
  clientId: string;
}

export function ClientDetailIsland({ clientId }: ClientDetailIslandProps) {
  const [token, setToken] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [client, setClient] = useState<ClientProfileResponse | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [clientCode, setClientCode] = useState('');
  const [status, setStatus] = useState<ClientStatus>('active');
  const [isWorking, setIsWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function applyClient(nextClient: ClientProfileResponse) {
    setClient(nextClient);
    setDisplayName(nextClient.display_name);
    setClientCode(nextClient.client_code ?? '');
    setStatus(nextClient.status);
  }

  async function handleLoad() {
    setIsWorking(true);
    setError(null);
    try {
      applyClient(await getClient({ token, tenantId }, clientId));
    } catch {
      setError('Klient konnte nicht geladen werden. Bitte Zugriffskontext prüfen.');
    } finally {
      setIsWorking(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsWorking(true);
    setError(null);
    try {
      applyClient(
        await updateClient(
          { token, tenantId },
          clientId,
          { display_name: displayName, client_code: clientCode.trim() ? clientCode : null, status },
        ),
      );
    } catch {
      setError('Klient konnte nicht aktualisiert werden. Bitte Zugriffskontext und Felder prüfen.');
    } finally {
      setIsWorking(false);
    }
  }

  return (
    <section className="shell-card" aria-labelledby="client-detail-title">
      <p className="muted">Client-Contract Detail</p>
      <h2 id="client-detail-title">Klient bearbeiten</h2>
      <ClientAccessFields token={token} tenantId={tenantId} onTokenChange={setToken} onTenantIdChange={setTenantId} />
      <div className="action-row">
        <button type="button" onClick={handleLoad} disabled={isWorking || !token || !tenantId}>
          {isWorking ? 'Lädt…' : 'Klient laden'}
        </button>
        <a href="/clients">Zur Übersicht</a>
      </div>
      {error ? <p className="error" role="alert">{error}</p> : null}
      {client ? (
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Anzeigename
            <input
              name="display_name"
              maxLength={200}
              required
              value={displayName}
              onChange={(event) => setDisplayName(event.currentTarget.value)}
            />
          </label>
          <label>
            Klienten-Code optional
            <input
              name="client_code"
              maxLength={80}
              value={clientCode}
              onChange={(event) => setClientCode(event.currentTarget.value)}
            />
          </label>
          <label>
            Status
            <select value={status} onChange={(event) => setStatus(event.currentTarget.value as ClientStatus)}>
              <option value="active">active</option>
              <option value="archived">archived</option>
            </select>
          </label>
          <button type="submit" disabled={isWorking || !displayName.trim()}>
            {isWorking ? 'Speichert…' : 'Änderungen speichern'}
          </button>
        </form>
      ) : (
        <p className="muted">Noch kein Klient geladen.</p>
      )}
      {client ? <ConsentIsland clientId={clientId} token={token} tenantId={tenantId} /> : null}
    </section>
  );
}
