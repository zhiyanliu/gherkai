# Worker Image Lifecycle

> 76 nodes · cohesion 0.05

## Key Concepts

- **workers.py** (58 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **Aws** (23 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **rederive_variants()** (21 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_push_one()** (20 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **cleanup_pass()** (15 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **run_deploy_steps()** (13 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **push_worker()** (11 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **WorkerCommandError** (11 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **datetime** (10 connections)
- **sync_base()** (9 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **current_version_mappings()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **read_mapping()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_template_arn()** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_connect()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **ImageMapping** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **init_default_pointer()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **PushOutcome** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_short_arn()** (7 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_parse_mapping()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_put_ssm()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_read_ssm()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_set_default()** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_ecr_login()** (5 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_error_code()** (5 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **_iter_image_params()** (5 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- *... and 51 more nodes in this community*

## Relationships

- [Worker Image Management Tests](Worker_Image_Management_Tests.md) (22 shared connections)
- [Task Definition Lineage Cleanup](Task_Definition_Lineage_Cleanup.md) (16 shared connections)
- [List Workers Command](List_Workers_Command.md) (13 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (7 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (4 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (3 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (3 shared connections)
- [Terminal UI Rendering](Terminal_UI_Rendering.md) (1 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (1 shared connections)
- [Worker Image Version Mappings](Worker_Image_Version_Mappings.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`

## Audit Trail

- EXTRACTED: 220 (96%)
- INFERRED: 8 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*