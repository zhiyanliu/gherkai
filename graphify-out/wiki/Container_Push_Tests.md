# Container Push Tests

> 83 nodes · cohesion 0.07

## Key Concepts

- **test_workers.py** (61 connections) — `deploy_aws/tests/test_workers.py`
- **FakeContainer** (45 connections) — `deploy_aws/tests/test_workers.py`
- **seed_backend()** (41 connections) — `deploy_aws/tests/test_workers.py`
- **_push()** (30 connections) — `deploy_aws/tests/test_workers.py`
- **_out()** (19 connections) — `deploy_aws/tests/test_workers.py`
- **_mapping()** (17 connections) — `deploy_aws/tests/test_workers.py`
- **timedelta** (13 connections)
- **_revisions()** (12 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_skips_the_whole_pass_when_the_mappings_cannot_be_listed()** (12 connections) — `deploy_aws/tests/test_workers.py`
- **_cleanup()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_keeps_a_retired_revision_still_referenced_by_a_mapping()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_keeps_within_the_quiet_period()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **_retire_now()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_deletes_after_quiet_period_when_unreferenced()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_deletes_when_the_referencing_run_is_terminal()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_keeps_when_a_pending_run_references_it()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_marks_retired_and_orphan_revisions()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_push_worker_runs_a_cleanup_pass_at_the_end()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_rederive_registers_from_the_new_template_and_retires_the_old()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_repush_retires_the_replaced_revision_and_prints_digest_change()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_deploy_steps_are_idempotent()** (8 connections) — `deploy_aws/tests/test_workers.py`
- **test_orphan_revision_is_reused_instead_of_registered()** (8 connections) — `deploy_aws/tests/test_workers.py`
- **test_rederive_ignores_other_versions()** (8 connections) — `deploy_aws/tests/test_workers.py`
- **test_arch_mismatch_exits_2_before_touching_ecr_or_ecs()** (7 connections) — `deploy_aws/tests/test_workers.py`
- **test_push_worker_happy_path()** (7 connections) — `deploy_aws/tests/test_workers.py`
- *... and 58 more nodes in this community*

## Relationships

- [Worker Image Push Workflow](Worker_Image_Push_Workflow.md) (29 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (7 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (6 shared connections)
- [AWS Env Fixture](AWS_Env_Fixture.md) (3 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (2 shared connections)
- [AWS Client Spy](AWS_Client_Spy.md) (2 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 285 (95%)
- INFERRED: 14 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*