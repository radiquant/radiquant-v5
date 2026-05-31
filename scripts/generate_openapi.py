"""Generate the FastAPI OpenAPI contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
OUTPUT = API_ROOT / "openapi.json"

sys.path.insert(0, str(API_ROOT))

from app.main import app  # noqa: E402


def main() -> None:
    OUTPUT.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
