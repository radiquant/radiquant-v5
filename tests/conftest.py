"""Pytest bootstrap for the API package."""

from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))
