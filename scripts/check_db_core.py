#!/usr/bin/env python3
"""Validate the initial Auth/Tenant/Audit database core without connecting to DB."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.db.base import Base  # noqa: E402
from app import models  # noqa: F401,E402

REQUIRED_TABLES = {
    "tenants",
    "roles",
    "users",
    "audit_logs",
    "client_profiles",
    "client_consents",
    "session_goals",
    "sessions",
    "workflow_runs",
    "workflow_step_runs",
    "event_records",
}
TENANT_SCOPED_TABLES = {
    "users",
    "audit_logs",
    "client_profiles",
    "client_consents",
    "session_goals",
    "sessions",
    "workflow_runs",
    "workflow_step_runs",
    "event_records",
}
REQUIRED_MIGRATION = API_ROOT / "alembic" / "versions" / "0001_identity_tenant_audit.py"
REQUIRED_PASSWORD_MIGRATION = API_ROOT / "alembic" / "versions" / "0002_user_password_hash.py"
REQUIRED_CLIENT_MIGRATION = API_ROOT / "alembic" / "versions" / "0003_client_profile_consent.py"
REQUIRED_SESSION_MIGRATION = API_ROOT / "alembic" / "versions" / "0004_session_domain.py"
REQUIRED_WORKFLOW_MIGRATION = API_ROOT / "alembic" / "versions" / "0005_workflow_api_gate.py"
REQUIRED_EVENT_MIGRATION = API_ROOT / "alembic" / "versions" / "0006_event_schema_gate.py"
REQUIRED_RUNTIME_FILES = [
    API_ROOT / "app" / "core" / "config.py",
    API_ROOT / "app" / "db" / "session.py",
    API_ROOT / "app" / "services" / "auth.py",
    API_ROOT / "app" / "services" / "audit.py",
    API_ROOT / "app" / "services" / "consent.py",
    API_ROOT / "app" / "security" / "tenant_guard.py",
    API_ROOT / "app" / "security" / "passwords.py",
    API_ROOT / "app" / "routes" / "auth.py",
    API_ROOT / "app" / "routes" / "clients.py",
    API_ROOT / "app" / "routes" / "sessions.py",
    API_ROOT / "app" / "routes" / "workflows.py",
    API_ROOT / "app" / "routes" / "realtime.py",
    API_ROOT / "app" / "schemas" / "auth.py",
    API_ROOT / "app" / "schemas" / "client.py",
    API_ROOT / "app" / "schemas" / "session.py",
    API_ROOT / "app" / "schemas" / "workflow.py",
    API_ROOT / "app" / "schemas" / "realtime.py",
    API_ROOT / "app" / "models" / "client.py",
    API_ROOT / "app" / "models" / "session.py",
    API_ROOT / "app" / "models" / "workflow.py",
    API_ROOT / "app" / "services" / "workflow_manifest.py",
    API_ROOT / "app" / "models" / "event.py",
    API_ROOT / "app" / "schemas" / "event.py",
    API_ROOT / "app" / "services" / "event_registry.py",
    ROOT / "tests" / "test_runtime_security_core.py",
    ROOT / "tests" / "test_client_routes.py",
    ROOT / "tests" / "test_consent_service.py",
    ROOT / "tests" / "test_session_routes.py",
    ROOT / "tests" / "test_workflow_routes.py",
    ROOT / "tests" / "test_event_schema_gate.py",
    ROOT / "tests" / "test_realtime_routes.py",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main() -> int:
    tables = set(Base.metadata.tables)
    missing = REQUIRED_TABLES - tables
    if missing:
        fail(f"Missing required DB tables in metadata: {sorted(missing)}")

    for table_name in TENANT_SCOPED_TABLES:
        table = Base.metadata.tables[table_name]
        if "tenant_id" not in table.columns:
            fail(f"Tenant-scoped table lacks tenant_id: {table_name}")

    users = Base.metadata.tables["users"]
    if not any(constraint.name == "uq_users_tenant_id_email" for constraint in users.constraints):
        fail("users table lacks tenant-scoped email uniqueness")
    if "password_hash" not in users.columns:
        fail("users table lacks password_hash for Identity Core login")

    audit = Base.metadata.tables["audit_logs"]
    for column in ["action", "resource_type", "correlation_id", "metadata_json"]:
        if column not in audit.columns:
            fail(f"audit_logs missing column: {column}")

    client_profiles = Base.metadata.tables["client_profiles"]
    for column in ["tenant_id", "display_name", "status", "created_by_user_id", "updated_by_user_id"]:
        if column not in client_profiles.columns:
            fail(f"client_profiles missing column: {column}")

    client_consents = Base.metadata.tables["client_consents"]
    for column in ["tenant_id", "client_id", "purpose", "status", "consent_text_version", "recorded_by_user_id"]:
        if column not in client_consents.columns:
            fail(f"client_consents missing column: {column}")

    session_goals = Base.metadata.tables["session_goals"]
    for column in ["tenant_id", "client_id", "title", "description", "created_by_user_id"]:
        if column not in session_goals.columns:
            fail(f"session_goals missing column: {column}")

    sessions = Base.metadata.tables["sessions"]
    for column in ["tenant_id", "client_id", "goal_id", "status", "started_at", "created_by_user_id", "updated_by_user_id"]:
        if column not in sessions.columns:
            fail(f"sessions missing column: {column}")
    forbidden_session_columns = {"workflow_id", "workflow_step", "engine_id", "module_id", "module", "result", "realtime"}
    if forbidden_session_columns & set(sessions.columns):
        fail(f"sessions contains forbidden workflow/engine columns: {sorted(forbidden_session_columns & set(sessions.columns))}")

    if not REQUIRED_MIGRATION.is_file():
        fail(f"Missing required migration: {REQUIRED_MIGRATION}")
    if not REQUIRED_PASSWORD_MIGRATION.is_file():
        fail(f"Missing required migration: {REQUIRED_PASSWORD_MIGRATION}")
    if not REQUIRED_CLIENT_MIGRATION.is_file():
        fail(f"Missing required migration: {REQUIRED_CLIENT_MIGRATION}")
    if not REQUIRED_SESSION_MIGRATION.is_file():
        fail(f"Missing required migration: {REQUIRED_SESSION_MIGRATION}")
    if not REQUIRED_WORKFLOW_MIGRATION.is_file():
        fail(f"Missing required migration: {REQUIRED_WORKFLOW_MIGRATION}")
    if not REQUIRED_EVENT_MIGRATION.is_file():
        fail(f"Missing required migration: {REQUIRED_EVENT_MIGRATION}")

    workflow_runs = Base.metadata.tables["workflow_runs"]
    for column in ["tenant_id", "session_id", "workflow_id", "workflow_slug", "status", "created_by_user_id", "updated_by_user_id"]:
        if column not in workflow_runs.columns:
            fail(f"workflow_runs missing column: {column}")
    forbidden_workflow_columns = {"engine_run_id", "module_result", "result", "raw_debug", "debug_json", "realtime", "progress"}
    if forbidden_workflow_columns & set(workflow_runs.columns):
        fail(f"workflow_runs contains forbidden execution columns: {sorted(forbidden_workflow_columns & set(workflow_runs.columns))}")

    workflow_step_runs = Base.metadata.tables["workflow_step_runs"]
    for column in ["tenant_id", "workflow_run_id", "step_index", "module_id", "phase", "status"]:
        if column not in workflow_step_runs.columns:
            fail(f"workflow_step_runs missing column: {column}")
    if forbidden_workflow_columns & set(workflow_step_runs.columns):
        fail(
            "workflow_step_runs contains forbidden execution columns: "
            f"{sorted(forbidden_workflow_columns & set(workflow_step_runs.columns))}"
        )

    event_records = Base.metadata.tables["event_records"]
    for column in ["tenant_id", "event_id", "event_type", "occurred_at", "correlation_id", "payload_json"]:
        if column not in event_records.columns:
            fail(f"event_records missing column: {column}")
    forbidden_event_columns = {"sse", "websocket", "connection_state", "replay_cursor", "stream_id"}
    if forbidden_event_columns & set(event_records.columns):
        fail(f"event_records contains forbidden realtime columns: {sorted(forbidden_event_columns & set(event_records.columns))}")

    missing_runtime_files = [str(path.relative_to(ROOT)) for path in REQUIRED_RUNTIME_FILES if not path.is_file()]
    if missing_runtime_files:
        fail(f"Missing runtime security core files: {missing_runtime_files}")

    from app.db.session import AsyncSessionLocal, get_db_session  # noqa: E402
    from app.routes.auth import router as auth_router  # noqa: E402
    from app.routes.clients import router as clients_router  # noqa: E402
    from app.routes.realtime import router as realtime_router  # noqa: E402
    from app.routes.sessions import router as sessions_router  # noqa: E402
    from app.routes.workflows import router as workflows_router  # noqa: E402
    from app.security.tenant_guard import require_tenant_context  # noqa: E402
    from app.services.audit import AuditService  # noqa: E402
    from app.services.auth import AuthService  # noqa: E402
    from app.services.consent import ConsentService  # noqa: E402
    from app.services.event_registry import EventRegistryService  # noqa: E402

    if AsyncSessionLocal is None or get_db_session is None:
        fail("Runtime DB session dependency is not importable")
    if AuthService is None:
        fail("Auth service is not importable")
    if require_tenant_context is None:
        fail("Tenant guard dependency is not importable")
    if AuditService is None:
        fail("Audit service is not importable")
    if ConsentService is None:
        fail("Consent service is not importable")
    if EventRegistryService is None:
        fail("Event registry service is not importable")
    auth_paths = {route.path for route in auth_router.routes if isinstance(route, APIRoute)}
    if not {"/auth/login", "/auth/logout"}.issubset(auth_paths):
        fail("Identity login/logout routes are not registered")
    client_paths = {route.path for route in clients_router.routes if isinstance(route, APIRoute)}
    if not {"/clients", "/clients/{client_id}", "/clients/{client_id}/consents"}.issubset(client_paths):
        fail("Client domain routes are not registered")
    session_paths = {route.path for route in sessions_router.routes if isinstance(route, APIRoute)}
    if not {"/sessions", "/sessions/{session_id}", "/sessions/{session_id}/status"}.issubset(session_paths):
        fail("Session domain routes are not registered")
    workflow_paths = {route.path for route in workflows_router.routes if isinstance(route, APIRoute)}
    if not {"/sessions/{session_id}/workflow-runs"}.issubset(workflow_paths):
        fail("Workflow API Gate routes are not registered")
    realtime_paths = {route.path for route in realtime_router.routes if isinstance(route, APIRoute)}
    if not {"/sessions/{session_id}/events", "/sessions/{session_id}/events/stream"}.issubset(realtime_paths):
        fail("Realtime API Gate routes are not registered")

    print(f"[OK] DB core metadata tables: {', '.join(sorted(REQUIRED_TABLES))}")
    print("[OK] Tenant-scoped tables include tenant_id")
    print("[OK] Initial migrations exist")
    print("[OK] Runtime DB session, auth service, tenant guard, audit service, consent service, identity/client/session routes, and negative tests exist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
