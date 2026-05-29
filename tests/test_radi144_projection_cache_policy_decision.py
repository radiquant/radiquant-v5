from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_radi144_projection_cache_policy_decision_gate_validates() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_radi144_projection_cache_policy_decision.py")],
        check=True,
    )
