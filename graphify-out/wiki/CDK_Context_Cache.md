# CDK Context Cache

> 14 nodes · cohesion 0.19

## Key Concepts

- **_CdkWritingContext** (9 connections) — `deploy_aws/tests/test_provider.py`
- **_cache_env()** (7 connections) — `deploy_aws/tests/test_provider.py`
- **context_cache_path()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_context_cache_is_saved_after_the_run_and_seeded_into_the_next_fresh_work_dir()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_context_cache_survives_a_failed_cdk_run()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **Path** (5 connections)
- **test_refresh_context_discards_the_cache_before_running()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_context_cache_is_per_prefix()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **.__call__()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (18 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (2 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (1 shared connections)
- [CDK Invocation Tests](CDK_Invocation_Tests.md) (1 shared connections)
- [AWS Client Stubs (CFN/SSM)](AWS_Client_Stubs_%28CFN-SSM%29.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 39 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*