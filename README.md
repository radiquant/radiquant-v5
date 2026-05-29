# radiquant-v5

Controlled ground-zero rebuild of the Radiquant radionics wellbeing platform.

## Status

**Phase:** 5 — Auth/Tenant/Audit DB metadata and initial migration initialized.  
**Decision freeze:** confirmed on 2026-05-22 in the radiquant4 reference repository.  
**Reference repository:** `/opt/radiquant4`.

## Confirmed baseline

| Area | Decision |
|---|---|
| Backend | FastAPI / Python |
| Frontend | Astro SSR + React Islands |
| Database | PostgreSQL |
| Cache / Queue / Events | Redis |
| Initial architecture | Modular monolith + worker |
| First vertical engine | Radi144 |
| MVP scope | Core + client + session + workflow manifest + one vertical engine |
| Workflow taxonomy | W-A to W-L new taxonomy |
| Entity scope | Human/client MVP; animal/plant/room later |

## Required reading before implementation

1. `docs/architecture/START_HERE.md`
2. `docs/pi/project.yml`
3. `/opt/radiquant4/docs/pi/*.yml`
4. `/opt/radiquant4/docs/restart-radiquant-v5/05_MASTER_SPECIFICATION.md`
5. `/opt/radiquant4/docs/restart-radiquant-v5/08_OPTIMAL_REBUILD_SEQUENCE.md`

## Current rule

Phase 2 toolchain/standards, Phase 3 contract foundation, initial Security/Database gates, and Auth/Tenant/Audit DB metadata/migration are established. Feature application code remains blocked until runtime DB sessions, auth services, tenant guards, and negative tests are created.
