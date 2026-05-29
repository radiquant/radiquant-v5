export function getApiBaseUrl(): string {
  const configured = import.meta.env.PUBLIC_API_BASE_URL?.trim();
  if (!configured) {
    return '';
  }
  return configured.replace(/\/$/, '');
}
