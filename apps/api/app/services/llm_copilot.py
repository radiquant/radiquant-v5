"""Feature-flagged therapist copilot service."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.session import ClientSession
from app.schemas.llm_copilot import CopilotRequest, CopilotResponse
from app.services.claim_linter import ClaimLinterService, ClaimViolationError

FEATURE_LLM_COPILOT = os.getenv("RQ5_FEATURE_LLM_COPILOT", "false").lower() == "true"
PII_REDACTION_PATTERNS = ["name", "email", "phone", "address", "birthdate", "patient_id"]
PII_VALUE_PATTERNS = [
    r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
    r"\b\+?[0-9][0-9 .()/-]{6,}[0-9]\b",
]


class LLMCopilotService:
    """Generate simulated therapist copilot responses behind a feature flag."""

    async def generate(
        self,
        request: CopilotRequest,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> CopilotResponse:
        if not FEATURE_LLM_COPILOT:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM Copilot feature not enabled",
            )
        session_exists = await db.scalar(
            select(ClientSession.id).where(
                ClientSession.id == request.session_id,
                ClientSession.tenant_id == tenant_id,
            )
        )
        if session_exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        redacted_question, pii_redacted = self._redact_pii(request.question)
        answer = (
            f"[Copilot-Simulation] Frage: {redacted_question} - Antwort: "
            "Bitte konsultieren Sie die fachliche Sitzungsdokumentation und vermeiden Sie "
            "Heilversprechen."
        )
        claim_violations: list[str] = []
        try:
            ClaimLinterService().lint(answer)
        except ClaimViolationError as exc:
            claim_violations = exc.violations

        await db.execute(
            insert(AuditLog).values(
                tenant_id=tenant_id,
                actor_user_id=None,
                action="llm_copilot_query",
                resource_type="session",
                resource_id=str(request.session_id),
                reason="llm_copilot_query",
                metadata_json={"details": {"pii_redacted": pii_redacted}},
                correlation_id=str(uuid4()),
            )
        )
        await db.commit()
        return CopilotResponse(
            answer=answer,
            pii_redacted=pii_redacted,
            claim_violations=claim_violations,
            model_used="copilot-simulation",
            generated_at=datetime.now(UTC),
        )

    def _redact_pii(self, question: str) -> tuple[str, bool]:
        redacted = question
        for pattern in PII_REDACTION_PATTERNS:
            redacted = re.sub(
                rf"\b{re.escape(pattern)}\b",
                "[REDACTED]",
                redacted,
                flags=re.IGNORECASE,
            )
        for pattern in PII_VALUE_PATTERNS:
            redacted = re.sub(pattern, "[REDACTED]", redacted)
        return redacted, redacted != question
