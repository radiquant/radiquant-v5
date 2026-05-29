# Event Schema Gate

Status: initialized with contracts, event-log model, validator, service, migration, and tests (2026-05-23).

## Scope opened

The Event Schema Gate opens schema-validated event envelopes only:

- `packages/contracts/events/event-registry.v1.json`
- `packages/contracts/events/event-envelope.schema.v1.json`
- `event_records` tenant-scoped table
- `EventEnvelopeCreate` / `EventRecordResponse` Pydantic schemas
- `EventRegistryService` validation
- `EventWriter` durable append primitive

## Explicitly still blocked

- WebSocket/WebTransport
- Job tracker runtime
- Workflow UI progress
- Engine execution and module progress

## Contract invariants

- Event payloads require `event_id`, `event_type`, `occurred_at`, `tenant_id`, and `correlation_id`.
- Event types must be declared in the event registry.
- Workflow/step/substep events must carry the relevant session/workflow/step context IDs.
- Event payloads must not contain raw debug, internal state, tokens, secrets, or passwords.
- Event records are tenant-scoped and contain no realtime transport columns.
- Later realtime routes must keep using validated event envelopes and tenant/session filters.

## Verification

`make verify` is the gate command. Event Schema Gate remains a prerequisite for later Realtime API validation.
