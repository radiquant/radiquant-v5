import { useState } from 'react';

import { listClients } from '../lib/api/client';
import type { ClientProfileResponse } from '../lib/api/types';
import { ClientAccessFields } from './ClientAccessFields';

export function ClientListIsland() {
  const [token, setToken] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [clients, setClients] = useState<ClientProfileResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLoad() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listClients({ token, tenantId });
      setClients(response.items);
    } catch {
      setError('Klienten konnten nicht geladen werden. Bitte Zugriffskontext prüfen.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="shell-card" aria-labelledby="clients-title">
      <p className="muted">Tenant-geschützte Klientenübersicht</p>
      <h2 id="clients-title">Klienten</h2>
      <p className="muted">
        Diese Ansicht zeigt ausschließlich sichere Profilfelder aus dem freigegebenen Client-Contract.
      </p>
      <ClientAccessFields token={token} tenantId={tenantId} onTokenChange={setToken} onTenantIdChange={setTenantId} />
      <div className="action-row">
        <button type="button" onClick={handleLoad} disabled={isLoading || !token || !tenantId}>
          {isLoading ? 'Lädt…' : 'Klienten laden'}
        </button>
        <a href="/clients/new">Neuen Klienten anlegen</a>
      </div>
      {error ? <p className="error" role="alert">{error}</p> : null}
      {clients.length === 0 && !isLoading ? <p className="muted">Noch keine Klienten geladen.</p> : null}
      <div className="client-list" aria-live="polite">
        {clients.map((client) => (
          <article className="client-summary" key={client.id}>
            <h3>{client.display_name}</h3>
            <p className="muted">Code: {client.client_code ?? 'nicht vergeben'}</p>
            <p><span className="status-badge">{client.status}</span></p>
            <p className="muted">Aktualisiert: {new Date(client.updated_at).toLocaleString('de-DE')}</p>
            <a href={`/clients/${client.id}`}>Details öffnen</a>
          </article>
        ))}
      </div>
    </section>
  );
}
