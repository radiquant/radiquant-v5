#!/usr/bin/env python3
"""Check committed OpenAPI against the FastAPI runtime OpenAPI for the current skeleton."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402

COMMITTED = ROOT / "packages" / "contracts" / "openapi" / "openapi.v1.json"


def normalize(schema: dict) -> dict:
    """Normalize volatile fields while the skeleton is still minimal."""
    keep = {
        "openapi": schema.get("openapi"),
        "info": schema.get("info"),
        "paths": schema.get("paths"),
        "components": schema.get("components", {}),
    }
    # FastAPI may omit servers; the planning contract may include them.
    if "servers" in schema:
        keep["servers"] = schema["servers"]
    return keep


def main() -> int:
    runtime = normalize(app.openapi())
    committed = normalize(json.loads(COMMITTED.read_text(encoding="utf-8")))

    runtime_paths = set(runtime.get("paths", {}))
    committed_paths = set(committed.get("paths", {}))
    if runtime_paths != committed_paths:
        print("[FAIL] Runtime OpenAPI path drift")
        print("only_runtime", sorted(runtime_paths - committed_paths))
        print("only_committed", sorted(committed_paths - runtime_paths))
        return 1

    runtime_ops = {
        (path, method)
        for path, methods in runtime.get("paths", {}).items()
        for method in methods
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    committed_ops = {
        (path, method)
        for path, methods in committed.get("paths", {}).items()
        for method in methods
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    }
    if runtime_ops != committed_ops:
        print("[FAIL] Runtime OpenAPI operation drift")
        print("only_runtime", sorted(runtime_ops - committed_ops))
        print("only_committed", sorted(committed_ops - runtime_ops))
        return 1

    print(f"[OK] runtime OpenAPI paths match committed contract: {len(runtime_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
