import { FormEvent, useState } from 'react';

import { login } from '../lib/api/client';
import type { TokenResponse } from '../lib/api/types';

interface LoginFormState {
  tenant_slug: string;
  email: string;
  password: string;
}

const INITIAL_FORM: LoginFormState = {
  tenant_slug: '',
  email: '',
  password: '',
};

export function LoginShell() {
  const [form, setForm] = useState<LoginFormState>(INITIAL_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenResponse, setTokenResponse] = useState<TokenResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setTokenResponse(null);

    try {
      const response = await login(form);
      setTokenResponse(response);
    } catch {
      setError('Anmeldung nicht möglich. Bitte Tenant, E-Mail und Passwort prüfen.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="shell-card" aria-labelledby="login-title">
      <p className="muted">Contract-bound Identity Shell</p>
      <h2 id="login-title">Sicher anmelden</h2>
      <p className="muted">
        Diese Oberfläche nutzt ausschließlich den freigegebenen Identity-Contract. Praxisdaten bleiben bis zur nächsten Gate-Freigabe geschlossen.
      </p>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Tenant-Kennung
          <input
            name="tenant_slug"
            autoComplete="organization"
            minLength={3}
            required
            value={form.tenant_slug}
            onChange={(event) => setForm({ ...form, tenant_slug: event.currentTarget.value })}
          />
        </label>
        <label>
          E-Mail
          <input
            name="email"
            type="email"
            autoComplete="email"
            required
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.currentTarget.value })}
          />
        </label>
        <label>
          Passwort
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            minLength={8}
            required
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.currentTarget.value })}
          />
        </label>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Anmeldung läuft…' : 'Anmelden'}
        </button>
      </form>

      {error ? <p className="error" role="alert">{error}</p> : null}
      {tokenResponse ? (
        <p className="success" role="status">
          Anmeldung bestätigt für Rolle {tokenResponse.role}. Die Session-Speicherung folgt erst nach expliziter Security-Entscheidung.
        </p>
      ) : null}
    </section>
  );
}
