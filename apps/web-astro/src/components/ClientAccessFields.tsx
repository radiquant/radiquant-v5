interface ClientAccessFieldsProps {
  token: string;
  tenantId: string;
  onTokenChange: (value: string) => void;
  onTenantIdChange: (value: string) => void;
}

export function ClientAccessFields({ token, tenantId, onTokenChange, onTenantIdChange }: ClientAccessFieldsProps) {
  return (
    <fieldset className="form-grid">
      <legend>Zugriffskontext</legend>
      <p className="muted">
        Bis zur finalen sicheren Session-Entscheidung werden Token und Tenant nur für diese Anfrage eingegeben und nicht gespeichert.
      </p>
      <label>
        Bearer Token
        <input
          name="access_token"
          autoComplete="off"
          required
          value={token}
          onChange={(event) => onTokenChange(event.currentTarget.value)}
        />
      </label>
      <label>
        Tenant-ID
        <input
          name="tenant_id"
          autoComplete="off"
          required
          value={tenantId}
          onChange={(event) => onTenantIdChange(event.currentTarget.value)}
        />
      </label>
    </fieldset>
  );
}
