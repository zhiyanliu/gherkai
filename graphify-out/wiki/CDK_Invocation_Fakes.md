# CDK Invocation Fakes

> 20 nodes · cohesion 0.11

## Key Concepts

- **_Recorder** (12 connections) — `deploy_aws/tests/test_provider.py`
- **_CdkWritingContext** (9 connections) — `deploy_aws/tests/test_provider.py`
- **_cache_env()** (7 connections) — `deploy_aws/tests/test_provider.py`
- **context_cache_path()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_FakeEngine** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_context_cache_is_saved_after_the_run_and_seeded_into_the_next_fresh_work_dir()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_context_cache_survives_a_failed_cdk_run()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_context_cache_is_per_prefix()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **.__call__()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.probe()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **`subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **`subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **.__call__()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (25 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (2 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (1 shared connections)
- [Test Fixtures and Conftest](Test_Fixtures_and_Conftest.md) (1 shared connections)
- [CFN/SSM Client Stubs](CFN-SSM_Client_Stubs.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 48 (94%)
- INFERRED: 3 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*