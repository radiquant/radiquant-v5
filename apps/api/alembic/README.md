# Alembic migrations — radiquant-v5

Initial migration baseline for Auth/Tenant/Audit models.

Rules:

- Every migration must support upgrade and downgrade.
- Sensitive/client/session tables must be tenant-scoped.
- Route/security/domain contracts must be updated before migrations that expose new API features.
