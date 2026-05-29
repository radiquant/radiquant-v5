import { ROLE_PROJECTIONS } from '../lib/theme/role-projections';

export function RoleProjectionShell() {
  return (
    <section className="shell-card" aria-labelledby="dashboard-title">
      <p className="muted">Role Projection Shell</p>
      <h2 id="dashboard-title">Dashboard-Shell</h2>
      <p className="muted">
        Diese Ansicht zeigt nur freigegebene Rollenprojektionen. Fachliche Praxis-, Sitzungs- und Modulbereiche bleiben bis zu ihren Contracts geschlossen.
      </p>
      <div className="role-grid" aria-label="Rollenprojektionen">
        {ROLE_PROJECTIONS.map((projection) => (
          <article className="shell-card" key={projection.role}>
            <p className="muted">{projection.role}</p>
            <h3>{projection.title}</h3>
            <p>{projection.description}</p>
            <p className="muted">{projection.allowedNextStep}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
