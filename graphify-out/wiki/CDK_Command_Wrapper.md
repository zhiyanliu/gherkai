# CDK Command Wrapper

> 47 nodes · cohesion 0.06

## Key Concepts

- **._run_cdk()** (14 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.deploy()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target_or_report()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.bootstrap()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk_command()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._require_vpc()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_version()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.synth_only()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._toolchain_gate()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.build_context()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._container_engine()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.diff()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.doctor()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.push_worker()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._work_dir()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._worker_image_steps()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.write_cdk_json()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Path** (5 connections)
- **check_cdk()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.app_command()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.destroy()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.list_workers()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_sts_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- *... and 22 more nodes in this community*

## Relationships

- [AWS Deploy Provider Tests](AWS_Deploy_Provider_Tests.md) (21 shared connections)
- [AWS Deploy CLI Provider](AWS_Deploy_CLI_Provider.md) (9 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (3 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (2 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (2 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 99 (95%)
- INFERRED: 5 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*