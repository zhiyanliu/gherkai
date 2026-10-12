# Run Store Persistence Ports

> 20 nodes · cohesion 0.14

## Key Concepts

- **RunPersistence application service** (8 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunStore Port** (5 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **DynamoDBRunStore** (4 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **core.schedule (execution reducer)** (4 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **Commit-point Write Order (data plane first)** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunStore.finalize_run()** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **Store.preflight() probe** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunState.jobs as Map<scope_id>** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunStore.update_job_state()** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunStore.create_run()** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **DDB Single-Table Schema (run_id + item_type)** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **Cloud Failure Exit Code Layering** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **RunState high_water_mark Conditional Write** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **JobSink Port** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **schedule.on_job_complete callback** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **S3StepArgumentOffloader** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ResultStore.save_job_result()** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **schedule.on_event bypass observer** (1 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **ReportStore.write Failure Isolation** (1 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **S3ResultStore** (1 connections) — `docs/adr/0030-realtime-persistence-seam.md`

## Relationships

- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (3 shared connections)

## Source Files

- `docs/adr/0030-realtime-persistence-seam.md`

## Audit Trail

- EXTRACTED: 27 (93%)
- INFERRED: 2 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*