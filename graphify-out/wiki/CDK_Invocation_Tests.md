# CDK Invocation Tests

> 15 nodes · cohesion 0.13

## Key Concepts

- **_Recorder** (11 connections) — `deploy_aws/tests/test_provider.py`
- **cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **_FakeEngine** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_rejects_an_unimplemented_container_engine_before_touching_the_account()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_returncode_is_passed_through()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **_clean_aws_env()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **fixture** (2 connections)
- **.probe()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **`subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **`GHERKAI_CONTAINER_ENGINE=podman` → 退 2 且**不调 cdk**：纯参数问题，账户一个字节都不该动…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **.__call__()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (14 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 27 (93%)
- INFERRED: 2 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*