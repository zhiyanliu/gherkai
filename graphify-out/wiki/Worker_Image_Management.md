# Worker Image Management

> 97 nodes · cohesion 0.04

## Key Concepts

- **workers.py** (56 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **Aws** (22 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **list_workers()** (21 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **rederive_variants()** (21 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_push_one()** (20 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
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
- **_template_arn()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **ImageMapping** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **init_default_pointer()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **PushOutcome** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_short_arn()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_skew_gate_read_failure_exits_2_without_a_traceback()** (7 connections) — `deploy_aws/tests/test_workers.py`
- **CleanupOutcome** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **make_aws()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_parse_mapping()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_pending_cleanup()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- *... and 72 more nodes in this community*

## Relationships

- [Container Worker Tests](Container_Worker_Tests.md) (40 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (9 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (5 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (3 shared connections)
- [Task Definition Revision Lineage](Task_Definition_Revision_Lineage.md) (3 shared connections)
- [Task Definition Cleanup Stub](Task_Definition_Cleanup_Stub.md) (1 shared connections)
- [Worker Image Version Mappings](Worker_Image_Version_Mappings.md) (1 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 256 (96%)
- INFERRED: 10 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*