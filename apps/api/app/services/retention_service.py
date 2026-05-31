"""Retention cleanup service and CLI entrypoint."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.audit import AuditLog
from app.models.engine import ModuleResult, ModuleRun
from app.models.event import EventRecord
from app.models.retention import RetentionPolicy
from app.models.session import ClientSession
from app.schemas.retention import RetentionCleanupReport
from app.services.gdpr_service import GdprService


class RetentionService:
    """Anonymize client data touched by expired tenant-scoped records."""

    async def run_cleanup(
        self,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> RetentionCleanupReport:
        policies = list(
            (
                await db.execute(
                    select(RetentionPolicy)
                    .where(
                        RetentionPolicy.tenant_id == tenant_id,
                        RetentionPolicy.enabled.is_(True),
                    )
                    .order_by(RetentionPolicy.data_type, RetentionPolicy.created_at)
                )
            )
            .scalars()
            .all()
        )
        ran_at = datetime.now(UTC)
        processed_total = 0
        anonymized_clients: set[UUID] = set()
        processed_types: list[str] = []

        for policy in policies:
            cutoff = ran_at - timedelta(days=policy.retention_days)
            processed_types.append(policy.data_type)
            records, client_ids = await self._expired_records(
                tenant_id=tenant_id,
                data_type=policy.data_type,
                cutoff=cutoff,
                db=db,
            )
            processed_total += records
            anonymized_clients.update(client_ids)

        for client_id in sorted(anonymized_clients, key=str):
            await GdprService().anonymize(client_id, tenant_id, db)

        data_type = ",".join(processed_types) if processed_types else "none"
        await self._append_audit_event(
            db=db,
            tenant_id=tenant_id,
            data_type=data_type,
            records_processed=processed_total,
            records_anonymized=len(anonymized_clients),
        )
        await db.commit()
        return RetentionCleanupReport(
            tenant_id=tenant_id,
            data_type=data_type,
            records_processed=processed_total,
            records_anonymized=len(anonymized_clients),
            ran_at=ran_at,
        )

    async def _expired_records(
        self,
        *,
        tenant_id: UUID,
        data_type: str,
        cutoff: datetime,
        db: AsyncSession,
    ) -> tuple[int, set[UUID]]:
        if data_type == "sessions":
            return await self._expired_sessions(tenant_id, cutoff, db)
        if data_type == "events":
            return await self._expired_events(tenant_id, cutoff, db)
        if data_type == "module_results":
            return await self._expired_module_results(tenant_id, cutoff, db)
        return 0, set()

    async def _expired_sessions(
        self,
        tenant_id: UUID,
        cutoff: datetime,
        db: AsyncSession,
    ) -> tuple[int, set[UUID]]:
        rows = list(
            (
                await db.execute(
                    select(ClientSession.id, ClientSession.client_id).where(
                        ClientSession.tenant_id == tenant_id,
                        ClientSession.created_at < cutoff,
                    )
                )
            ).all()
        )
        return len(rows), {client_id for _session_id, client_id in rows}

    async def _expired_events(
        self,
        tenant_id: UUID,
        cutoff: datetime,
        db: AsyncSession,
    ) -> tuple[int, set[UUID]]:
        rows = list(
            (
                await db.execute(
                    select(
                        EventRecord.resource_type,
                        EventRecord.resource_id,
                        ClientSession.client_id,
                    )
                    .outerjoin(
                        ClientSession,
                        (ClientSession.id == EventRecord.session_id)
                        & (ClientSession.tenant_id == tenant_id),
                    )
                    .where(
                        EventRecord.tenant_id == tenant_id,
                        EventRecord.created_at < cutoff,
                    )
                )
            ).all()
        )
        client_ids: set[UUID] = set()
        for resource_type, resource_id, session_client_id in rows:
            if session_client_id is not None:
                client_ids.add(session_client_id)
                continue
            if resource_type == "client_profile" and resource_id is not None:
                try:
                    client_ids.add(UUID(resource_id))
                except ValueError:
                    continue
        return len(rows), client_ids

    async def _expired_module_results(
        self,
        tenant_id: UUID,
        cutoff: datetime,
        db: AsyncSession,
    ) -> tuple[int, set[UUID]]:
        rows = list(
            (
                await db.execute(
                    select(ModuleResult.id, ClientSession.client_id)
                    .join(ModuleRun, ModuleRun.id == ModuleResult.module_run_id)
                    .join(ClientSession, ClientSession.id == ModuleRun.session_id)
                    .where(
                        ModuleResult.tenant_id == tenant_id,
                        ModuleRun.tenant_id == tenant_id,
                        ClientSession.tenant_id == tenant_id,
                        ModuleResult.created_at < cutoff,
                    )
                )
            ).all()
        )
        return len(rows), {client_id for _result_id, client_id in rows}

    async def _append_audit_event(
        self,
        *,
        db: AsyncSession,
        tenant_id: UUID,
        data_type: str,
        records_processed: int,
        records_anonymized: int,
    ) -> None:
        await db.execute(
            insert(AuditLog).values(
                tenant_id=tenant_id,
                actor_user_id=None,
                action="retention_cleanup",
                resource_type="retention_policy",
                resource_id=str(tenant_id),
                reason="retention_cleanup",
                metadata_json={
                    "data_type": data_type,
                    "records_processed": records_processed,
                    "records_anonymized": records_anonymized,
                },
                correlation_id=str(uuid4()),
            )
        )


async def _run_cli(tenant_id: UUID) -> None:
    async with AsyncSessionLocal() as db:
        report = await RetentionService().run_cleanup(tenant_id, db)
        print(report.model_dump_json())


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", required=True)
    args = parser.parse_args()
    asyncio.run(_run_cli(UUID(args.tenant_id)))
