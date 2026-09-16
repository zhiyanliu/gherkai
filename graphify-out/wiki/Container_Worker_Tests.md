# Container Worker Tests

> 99 nodes · cohesion 0.06

## Key Concepts

- **test_workers.py** (70 connections) — `deploy_aws/tests/test_workers.py`
- **FakeContainer** (50 connections) — `deploy_aws/tests/test_workers.py`
- **seed_backend()** (47 connections) — `deploy_aws/tests/test_workers.py`
- **_push()** (35 connections) — `deploy_aws/tests/test_workers.py`
- **_out()** (25 connections) — `deploy_aws/tests/test_workers.py`
- **_mapping()** (17 connections) — `deploy_aws/tests/test_workers.py`
- **timedelta** (13 connections)
- **_revisions()** (12 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_skips_the_whole_pass_when_the_mappings_cannot_be_listed()** (12 connections) — `deploy_aws/tests/test_workers.py`
- **_cleanup()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_keeps_a_retired_revision_still_referenced_by_a_mapping()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_keeps_within_the_quiet_period()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **_retire_now()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_deletes_after_quiet_period_when_unreferenced()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_deletes_when_the_referencing_run_is_terminal()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_keeps_when_a_pending_run_references_it()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_enumerates_ssm_once_for_all_engines()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_list_workers_marks_retired_and_orphan_revisions()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_push_worker_runs_a_cleanup_pass_at_the_end()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_rederive_does_not_read_the_template_when_nothing_is_stale()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_rederive_registers_from_the_new_template_and_retires_the_old()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_repush_retires_the_replaced_revision_and_prints_digest_change()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_deploy_steps_are_idempotent()** (8 connections) — `deploy_aws/tests/test_workers.py`
- **test_orphan_revision_is_reused_instead_of_registered()** (8 connections) — `deploy_aws/tests/test_workers.py`
- *... and 74 more nodes in this community*

## Relationships

- [Worker Image Management](Worker_Image_Management.md) (40 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (7 shared connections)
- [Task Definition Cleanup Stub](Task_Definition_Cleanup_Stub.md) (5 shared connections)
- [AWS Call Spy](AWS_Call_Spy.md) (4 shared connections)
- [ECS Call Counting Stub](ECS_Call_Counting_Stub.md) (3 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (2 shared connections)
- [Worker Image Version Mappings](Worker_Image_Version_Mappings.md) (2 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (2 shared connections)
- [Task Definition Revision Lineage](Task_Definition_Revision_Lineage.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 342 (96%)
- INFERRED: 14 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*