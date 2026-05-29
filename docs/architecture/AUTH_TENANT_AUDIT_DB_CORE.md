# Auth / Tenant / Audit DB Core

**Status:** Initial ORM metadata and first Alembic migration skeleton created.  
**Scope:** Security and persistence foundation only; no login/session/client feature routes yet.

## Created models

| Model | Table | Purpose |
|---|---|---|
| `Tenant` | `tenants` | Tenant boundary for all future client/session/result resources. |
| `Role` | `roles` | Canonical RBAC role catalog. |
| `User` | `users` | Tenant-scoped user identity shell. Password/session logic intentionally deferred. |
| `AuditLog` | `audit_logs` | Tenant-scoped immutable audit event shell. |

## Created migration baseline

| File | Purpose |
|---|---|
| `apps/api/alembic/versions/0001_identity_tenant_audit.py` | Creates `tenants`, `roles`, `users`, `audit_logs` and indexes/constraints. |
| `apps/api/alembic/env.py` | Alembic metadata wiring. |
| `apps/api/alembic.ini` | Alembic configuration. |

## Verification

`make verify` now checks:

1. contracts,
2. route security manifest,
3. runtime OpenAPI path parity,
4. ORM metadata contains required Auth/Tenant/Audit tables,
5. tenant-scoped metadata includes `tenant_id`,
6. initial migration exists.

## Deliberately not implemented yet

| Item | Reason |
|---|---|
| Password hashing/login routes | Must be implemented in Auth Core after DB baseline verification. |
| Client domain routes | Blocked until Auth/Tenant/Audit gates are stable. |
| Session workflow routes | Blocked until client + consent core. |
| DB connection runtime | Migrations/metadata first; runtime DB session follows in next phase. |

## Next step

Implement Auth Core contracts and runtime DB session infrastructure, then add tenant guards and negative tests before any client feature route.
