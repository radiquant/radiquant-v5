export type RoleName = 'admin' | 'therapist' | 'assistant' | 'client' | 'researcher' | 'system';
export type ClientStatus = 'active' | 'archived';
export type ConsentPurpose =
  | 'analysis'
  | 'harmonization'
  | 'trend_analysis'
  | 'report_export'
  | 'replay_research_use'
  | 'hrv_processing'
  | 'media_upload_processing';
export type ConsentStatus = 'granted' | 'revoked';
export type RealtimeConnectionState = 'connected' | 'reconnecting' | 'fallback' | 'offline' | 'failed' | 'auth_error';

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'fail';
  service: 'radiquant-v5-api';
  version: string;
}

export interface LoginRequest {
  tenant_slug: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  tenant_id: string;
  user_id: string;
  role: RoleName;
}

export interface LogoutResponse {
  status: 'ok';
}

export interface ClientProfileCreate {
  display_name: string;
  client_code?: string | null;
}

export interface ClientProfileUpdate {
  display_name?: string | null;
  client_code?: string | null;
  status?: ClientStatus | null;
}

export interface ClientProfileResponse {
  id: string;
  tenant_id: string;
  display_name: string;
  client_code: string | null;
  status: ClientStatus;
  created_at: string;
  updated_at: string;
}

export interface ClientProfileListResponse {
  items: ClientProfileResponse[];
  limit: number;
  offset: number;
}

export interface ClientConsentCreate {
  purpose: ConsentPurpose;
  status?: ConsentStatus;
  consent_text_version: string;
  expires_at?: string | null;
}

export interface ClientConsentResponse {
  id: string;
  tenant_id: string;
  client_id: string;
  purpose: ConsentPurpose;
  status: ConsentStatus;
  consent_text_version: string;
  granted_at: string;
  revoked_at: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClientConsentListResponse {
  items: ClientConsentResponse[];
}

export type Radi144WorkerEventType =
  | 'job.running'
  | 'job.done'
  | 'job.failed'
  | 'module.radi144.started'
  | 'module.radi144.completed'
  | 'module.radi144.failed';

export interface EventReplayItem {
  event_id: string;
  event_type: string;
  occurred_at: string;
  tenant_id: string;
  correlation_id: string;
  session_id: string | null;
  workflow_run_id: string | null;
  workflow_step_run_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  payload: Record<string, unknown>;
}

export interface EventReplayResponse {
  items: EventReplayItem[];
  limit: number;
  after_event_id: string | null;
  next_cursor: string | null;
  connection_state: 'fallback';
}
