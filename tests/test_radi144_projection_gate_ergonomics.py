from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_radi144_projection_gate_ergonomics_validates() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_radi144_projection_gate_ergonomics.py")],
        check=True,
    )
