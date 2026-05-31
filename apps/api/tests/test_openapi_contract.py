"""OpenAPI contract generation tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parents[1]
sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402


def test_openapi_json_exists_and_is_valid() -> None:
    openapi_path = API_ROOT / "openapi.json"

    with openapi_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    assert data["openapi"] == "3.1.0"
    assert data["info"]["title"] == "radiquant-v5 API"


def test_openapi_json_matches_fastapi_app() -> None:
    openapi_path = API_ROOT / "openapi.json"
    stored = json.loads(openapi_path.read_text(encoding="utf-8"))

    assert stored == app.openapi()


def test_typescript_schema_exists_and_exports_paths() -> None:
    schema_path = REPO_ROOT / "apps/web-astro/src/lib/api/schema.gen.ts"
    content = schema_path.read_text(encoding="utf-8")

    assert "export interface paths" in content
    assert '"/metrics/"' in content


def test_package_json_has_codegen_scripts() -> None:
    package_path = REPO_ROOT / "apps/web-astro/package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))

    assert package["scripts"]["codegen:api"].startswith("openapi-typescript")
    assert "codegen:api:check" in package["scripts"]
