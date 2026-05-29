#!/usr/bin/env python3
"""Check that all runtime FastAPI routes are classified in the route security manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402

MANIFEST = ROOT / "packages" / "contracts" / "routes" / "route-security-manifest.v1.json"

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    classified = {
        (route["path"], method.upper())
        for route in manifest.get("routes", [])
        for method in route.get("methods", [])
    }
    runtime = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in sorted((route.methods or set()) & HTTP_METHODS):
            if method in {"HEAD", "OPTIONS"}:
                continue
            runtime.add((route.path, method))

    missing = sorted(runtime - classified)
    stale = sorted(classified - runtime)
    if missing:
        print("[FAIL] Runtime routes missing route-security classification:")
        for path, method in missing:
            print(f"  {method} {path}")
        return 1
    if stale:
        print("[FAIL] Route security manifest contains routes not present at runtime:")
        for path, method in stale:
            print(f"  {method} {path}")
        return 1

    print(f"[OK] runtime routes classified: {len(runtime)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
