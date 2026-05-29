#!/usr/bin/env python3
"""Validate the contract-bound frontend shell without requiring node_modules."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "web-astro"
OPENAPI = ROOT / "packages" / "contracts" / "openapi" / "openapi.v1.json"

REQUIRED_FILES = [
    WEB_ROOT / "astro.config.mjs",
    WEB_ROOT / "tsconfig.json",
    WEB_ROOT / "src" / "env.d.ts",
    WEB_ROOT / "src" / "layouts" / "AppShell.astro",
    WEB_ROOT / "src" / "pages" / "index.astro",
    WEB_ROOT / "src" / "pages" / "login.astro",
    WEB_ROOT / "src" / "pages" / "dashboard.astro",
    WEB_ROOT / "src" / "pages" / "clients" / "index.astro",
    WEB_ROOT / "src" / "pages" / "clients" / "new.astro",
    WEB_ROOT / "src" / "pages" / "clients" / "[client_id].astro",
    WEB_ROOT / "src" / "components" / "LoginShell.tsx",
    WEB_ROOT / "src" / "components" / "RoleProjectionShell.tsx",
    WEB_ROOT / "src" / "components" / "ClientAccessFields.tsx",
    WEB_ROOT / "src" / "components" / "ClientListIsland.tsx",
    WEB_ROOT / "src" / "components" / "ClientCreateIsland.tsx",
    WEB_ROOT / "src" / "components" / "ClientDetailIsland.tsx",
    WEB_ROOT / "src" / "components" / "ConsentIsland.tsx",
    WEB_ROOT / "src" / "components" / "JobTrackerStatusIsland.tsx",
    WEB_ROOT / "src" / "lib" / "api" / "config.ts",
    WEB_ROOT / "src" / "lib" / "api" / "types.ts",
    WEB_ROOT / "src" / "lib" / "api" / "client.ts",
    WEB_ROOT / "src" / "lib" / "theme" / "role-projections.ts",
    WEB_ROOT / "src" / "styles" / "tokens.css",
    WEB_ROOT / "src" / "styles" / "global.css",
]

ALLOWED_API_PATHS = {
    "/health",
    "/auth/login",
    "/auth/logout",
    "/clients",
    "/clients/{client_id}",
    "/clients/{client_id}/consents",
    "/sessions/{session_id}/events",
}
FORBIDDEN_FRONTEND_FRAGMENTS = [
    "/workflows",
    "/engines",
    "/reports",
    "/realtime",
]
FORBIDDEN_FIELD_LABELS = ["raw_debug", "debug_json", "internal_state", "metadata_json", "password_hash"]
FORBIDDEN_BACKEND_LITERALS = ["http://", "https://", "localhost", "127.0.0.1", ":8050"]
TEXT_SUFFIXES = {".astro", ".css", ".js", ".mjs", ".ts", ".tsx"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def iter_frontend_files() -> list[Path]:
    return [path for path in WEB_ROOT.rglob("*") if path.is_file() and path.suffix in TEXT_SUFFIXES]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        fail(f"Missing frontend shell files: {missing}")

    openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
    openapi_paths = set(openapi.get("paths", {}))
    if not ALLOWED_API_PATHS.issubset(openapi_paths):
        fail(f"Frontend allowed API paths are not all in OpenAPI: {sorted(ALLOWED_API_PATHS - openapi_paths)}")

    client_source = read(WEB_ROOT / "src" / "lib" / "api" / "client.ts")
    declared_api_paths = set(
        re.findall(
            r"['\"](/(?:health|auth/login|auth/logout|clients|clients/\{client_id\}|clients/\{client_id\}/consents|sessions/\{session_id\}/events))['\"]",
            client_source,
        )
    )
    if declared_api_paths != ALLOWED_API_PATHS:
        fail(f"Frontend API client must expose exactly allowed paths: {sorted(declared_api_paths)}")

    for path in iter_frontend_files():
        source = read(path)
        rel = path.relative_to(ROOT)
        if any(literal in source for literal in FORBIDDEN_BACKEND_LITERALS):
            fail(f"Hardcoded backend URL literal in {rel}")
        if any(fragment in source for fragment in FORBIDDEN_FRONTEND_FRAGMENTS):
            fail(f"Forbidden unopened frontend domain fragment in {rel}")
        if any(label in source for label in FORBIDDEN_FIELD_LABELS):
            fail(f"Forbidden raw/debug/internal field label in {rel}")
        if "fetch(" in source and path != WEB_ROOT / "src" / "lib" / "api" / "client.ts":
            fail(f"Direct fetch outside central API client: {rel}")

    app_shell = read(WEB_ROOT / "src" / "layouts" / "AppShell.astro")
    if "skip-link" not in app_shell or "main-content" not in app_shell or "data-biorhythm" not in app_shell:
        fail("AppShell lacks skip link, main content target, or biorhythm data attribute")
    if 'href="/clients"' not in app_shell:
        fail("AppShell lacks contract-backed Clients navigation")

    tokens = read(WEB_ROOT / "src" / "styles" / "tokens.css")
    global_css = read(WEB_ROOT / "src" / "styles" / "global.css")
    if "prefers-reduced-motion" not in tokens:
        fail("Design tokens lack reduced motion handling")
    if ".skip-link" not in global_css or ":focus-visible" not in global_css:
        fail("Global CSS lacks accessibility foundations")

    role_projection = read(WEB_ROOT / "src" / "lib" / "theme" / "role-projections.ts")
    for role in ["client", "therapist", "assistant", "admin", "researcher", "system"]:
        if f"role: '{role}'" not in role_projection:
            fail(f"Missing role projection: {role}")

    jobtracker = read(WEB_ROOT / "src" / "components" / "JobTrackerStatusIsland.tsx")
    for state in ["connected", "reconnecting", "fallback", "offline", "failed", "auth_error"]:
        if state not in jobtracker:
            fail(f"JobTracker UI lacks connection state: {state}")
    if "listSessionEvents" not in jobtracker or "EventSource" in jobtracker:
        fail("JobTracker UI must use fallback replay via central API client and must not open EventSource without header auth")
    for token in ["Radi144WorkerEventType", "RADI144_WORKER_EVENT_TYPES", "isRadi144WorkerEvent", "Radi144 Worker-Status", "Radi144 Event-Truth"]:
        if token not in jobtracker:
            fail(f"JobTracker UI lacks Radi144 event binding token: {token}")

    print(f"[OK] frontend shell/client/consent/jobtracker files validate: {len(REQUIRED_FILES)}")
    print(f"[OK] frontend API paths are contract-bound: {', '.join(sorted(ALLOWED_API_PATHS))}")
    print("[OK] frontend has central API wrapper, client profile UI, consent UI, JobTracker connection states, design tokens, skip link, and reduced motion gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
