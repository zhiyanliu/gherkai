# Worker Image Push Workflow

> 95 nodes · cohesion 0.05

## Key Concepts

- **workers.py** (57 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_push_one()** (20 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **Aws** (19 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **rederive_variants()** (18 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **list_workers()** (17 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **cleanup_pass()** (15 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **run_deploy_steps()** (13 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_register_revision()** (12 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **push_worker()** (11 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **WorkerCommandError** (11 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **datetime** (10 connections)
- **sync_base()** (9 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **current_version_mappings()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **read_mapping()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **scan_family()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_short_arn()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_template_arn()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **ImageMapping** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **init_default_pointer()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_print_pending_cleanup()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **PushOutcome** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **RevisionInfo** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_skew_gate_read_failure_exits_2_without_a_traceback()** (7 connections) — `deploy_aws/tests/test_workers.py`
- **CleanupOutcome** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **make_aws()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- *... and 70 more nodes in this community*

## Relationships

- [Container Push Tests](Container_Push_Tests.md) (29 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (10 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (6 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (3 shared connections)
- [Live Run Reference Check](Live_Run_Reference_Check.md) (3 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)
- [AWS Env Fixture](AWS_Env_Fixture.md) (1 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (1 shared connections)
- [Revision Lineage Tags](Revision_Lineage_Tags.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 247 (95%)
- INFERRED: 12 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*