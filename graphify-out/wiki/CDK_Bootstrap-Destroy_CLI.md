# CDK Bootstrap/Destroy CLI

> 14 nodes · cohesion 0.15

## Key Concepts

- **_argv()** (9 connections) — `deploy_aws/tests/test_provider.py`
- **test_synth_only_pins_a_relative_dir_to_the_callers_cwd()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **Path** (5 connections)
- **test_bootstrap_needs_no_vpc_and_never_loads_the_app()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_destroy_yes_passes_force_to_cdk_and_is_off_by_default()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_diff_invokes_cdk_with_app_output_and_context()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **_parse_destroy()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_destroy_invokes_cdk_destroy_with_same_context()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **.__call__()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **Namespace** (2 connections)
- **用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证， 不会跑…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [Deploy Provider Tests](Deploy_Provider_Tests.md) (16 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (7 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (2 shared connections)
- [Deploy CLI Test Doubles](Deploy_CLI_Test_Doubles.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 40 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*