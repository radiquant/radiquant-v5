import { useMemo, useState } from 'react';

export function WorkflowWizardIsland() {
  const [sessionId, setSessionId] = useState('');
  const resultHref = useMemo(
    () => `/modules/radi144/result?session_id=${encodeURIComponent(sessionId.trim())}`,
    [sessionId],
  );

  return (
    <section className="shell-card" aria-labelledby="workflow-wizard-title">
      <p className="muted">Workflow MVP</p>
      <h2 id="workflow-wizard-title">Radi144 Workflow starten</h2>
      <p className="muted">
        Dieser Einstieg hält den Workflow auf der freigegebenen Shell-Ebene und führt direkt zur Radi144 Ergebnisansicht.
      </p>
      <div className="form-grid">
        <label>
          Session-ID
          <input
            name="session_id"
            placeholder="UUID der aktiven Session"
            value={sessionId}
            onChange={(event) => setSessionId(event.currentTarget.value)}
          />
        </label>
      </div>
      <div className="action-row">
        <a href={sessionId.trim() ? resultHref : '/modules/radi144/result'}>Ergebnis ansehen</a>
      </div>
    </section>
  );
}
