"""Wellbeing claim linter for generated report text."""

from __future__ import annotations

import re

FORBIDDEN_CLAIM_PATTERNS = [
    "heilt",
    "behandelt",
    "diagnostiziert",
    "medizinisch",
    "klinisch",
    "garantiert",
    "kuriert",
    "therapiert",
]


class ClaimViolationError(Exception):
    """Raised when generated text contains forbidden wellbeing claims."""

    def __init__(self, violations: list[str]) -> None:
        super().__init__("Forbidden wellbeing claims detected")
        self.violations = violations


class ClaimLinterService:
    """Detect forbidden wellbeing claims in generated report text."""

    def lint(self, text: str) -> None:
        violations: list[str] = []
        for pattern in FORBIDDEN_CLAIM_PATTERNS:
            for match in re.finditer(re.escape(pattern), text, flags=re.IGNORECASE):
                violations.append(match.group(0))
        if violations:
            raise ClaimViolationError(violations)
