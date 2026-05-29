import { getApiBaseUrl } from './config';
import type {
  ClientConsentCreate,
  ClientConsentListResponse,
  ClientConsentResponse,
  ClientProfileCreate,
  ClientProfileListResponse,
  ClientProfileResponse,
  ClientProfileUpdate,
  EventReplayResponse,
  HealthResponse,
  LoginRequest,
  LogoutResponse,
  TokenResponse,
} from './types';

export const API_PATHS = [
  '/health',
  '/auth/login',
  '/auth/logout',
  '/clients',
  '/clients/{client_id}',
  '/clients/{client_id}/consents',
  '/sessions/{session_id}/events',
] as const;
type ApiPath = (typeof API_PATHS)[number];

type HttpMethod = 'GET' | 'POST' | 'PATCH';

interface TenantRequestContext {
  token: string;
  tenantId: string;
}

interface RequestOptions {
  method?: HttpMethod;
  token?: string;
  tenantId?: string;
  body?: unknown;
}

function clientPath(clientId: string): ApiPath {
  return `/clients/${encodeURIComponent(clientId)}` as ApiPath;
}

function clientConsentsPath(clientId: string): ApiPath {
  return `/clients/${encodeURIComponent(clientId)}/consents` as ApiPath;
}

function sessionEventsPath(sessionId: string): ApiPath {
  return `/sessions/${encodeURIComponent(sessionId)}/events` as ApiPath;
}

async function requestJson<TResponse>(path: ApiPath, options: RequestOptions = {}): Promise<TResponse> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  if (options.tenantId) {
    headers['X-Tenant-ID'] = options.tenantId;
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

export function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/health');
}

export function login(payload: LoginRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>('/auth/login', { method: 'POST', body: payload });
}

export function logout(token: string): Promise<LogoutResponse> {
  return requestJson<LogoutResponse>('/auth/logout', { method: 'POST', token });
}

export function listClients(context: TenantRequestContext): Promise<ClientProfileListResponse> {
  return requestJson<ClientProfileListResponse>('/clients', {
    token: context.token,
    tenantId: context.tenantId,
  });
}

export function createClient(
  context: TenantRequestContext,
  payload: ClientProfileCreate,
): Promise<ClientProfileResponse> {
  return requestJson<ClientProfileResponse>('/clients', {
    method: 'POST',
    token: context.token,
    tenantId: context.tenantId,
    body: payload,
  });
}

export function getClient(context: TenantRequestContext, clientId: string): Promise<ClientProfileResponse> {
  return requestJson<ClientProfileResponse>(clientPath(clientId), {
    token: context.token,
    tenantId: context.tenantId,
  });
}

export function updateClient(
  context: TenantRequestContext,
  clientId: string,
  payload: ClientProfileUpdate,
): Promise<ClientProfileResponse> {
  return requestJson<ClientProfileResponse>(clientPath(clientId), {
    method: 'PATCH',
    token: context.token,
    tenantId: context.tenantId,
    body: payload,
  });
}

export function listClientConsents(context: TenantRequestContext, clientId: string): Promise<ClientConsentListResponse> {
  return requestJson<ClientConsentListResponse>(clientConsentsPath(clientId), {
    token: context.token,
    tenantId: context.tenantId,
  });
}

export function recordClientConsent(
  context: TenantRequestContext,
  clientId: string,
  payload: ClientConsentCreate,
): Promise<ClientConsentResponse> {
  return requestJson<ClientConsentResponse>(clientConsentsPath(clientId), {
    method: 'POST',
    token: context.token,
    tenantId: context.tenantId,
    body: payload,
  });
}

export function listSessionEvents(
  context: TenantRequestContext,
  sessionId: string,
  afterEventId?: string,
): Promise<EventReplayResponse> {
  const path = sessionEventsPath(sessionId);
  const query = afterEventId ? `?after_event_id=${encodeURIComponent(afterEventId)}` : '';
  return requestJson<EventReplayResponse>(`${path}${query}` as ApiPath, {
    token: context.token,
    tenantId: context.tenantId,
  });
}
