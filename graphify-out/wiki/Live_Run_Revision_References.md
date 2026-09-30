# Live Run Revision References

> 4 nodes · cohesion 0.50

## Key Concepts

- **_referenced_by_live_run()** (4 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_non_terminal_statuses()** (3 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`

## Relationships

- [Worker Image Management](Worker_Image_Management.md) (3 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*