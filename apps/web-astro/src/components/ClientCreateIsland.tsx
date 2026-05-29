import { FormEvent, useState } from 'react';

import { createClient } from '../lib/api/client';
import type { ClientProfileResponse } from '../lib/api/types';
import { ClientAccessFields } from './ClientAccessFields';

export function ClientCreateIsland() {
  const [token, setToken] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [clientCode, setClientCode] = useState('');
  const [created, setCreated] = useState<ClientProfileResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setCreated(null);
    try {
      const response = await createClient(
        { token, tenantId },
        { display_name: displayName, client_code: clientCode.trim() ? clientCode : null },
      );
      setCreated(response);
    } catch {
      setError('Klient konnte nicht angelegt werden. Bitte Eingaben und Zugriffskontext prüfen.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="shell-card" aria-labelledby="client-create-title">
      <p className="muted">Client-Contract Create</p>
      <h2 id="client-create-title">Klienten anlegen</h2>
      <form className="form-grid" onSubmit={handleSubmit}>
        <ClientAccessFields token={token} tenantId={tenantId} onTokenChange={setToken} onTenantIdChange={setTenantId} />
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
        <button type="submit" disabled={isSubmitting || !token || !tenantId || !displayName.trim()}>
          {isSubmitting ? 'Speichert…' : 'Klient anlegen'}
        </button>
      </form>
      {error ? <p className="error" role="alert">{error}</p> : null}
      {created ? (
        <p className="success" role="status">
          Klient {created.display_name} wurde angelegt. <a href={`/clients/${created.id}`}>Details öffnen</a>
        </p>
      ) : null}
    </section>
  );
}
