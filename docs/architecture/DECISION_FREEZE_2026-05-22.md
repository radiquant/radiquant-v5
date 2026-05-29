# Decision Freeze 2026-05-22

| Area | Confirmed decision |
|---|---|
| Rebuild strategy | Controlled rebuild with `/opt/radiquant4` as reference and migration source |
| Backend | FastAPI / Python |
| Frontend | Astro SSR + React Islands |
| Database | PostgreSQL |
| Cache / queue / events | Redis |
| Architecture | Modular monolith + worker first; internal engine microservices optional later |
| First vertical engine | Radi144 first, RadiWorks fallback only if extraction is blocked |
| MVP scope | Core + client + session + workflow manifest + one vertical engine |
| Workflow taxonomy | New W-A to W-L taxonomy |
| MVP entity scope | Human/client only; animal/plant/room later |

See canonical planning source:

`/opt/radiquant4/docs/restart-radiquant-v5/09_DECISION_FREEZE_2026-05-22.md`
