# CDK Invocation Tests

> 14 nodes · cohesion 0.15

## Key Concepts

- **_Recorder** (12 connections) — `deploy_aws/tests/test_provider.py`
- **_FakeEngine** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_missing_cdk_stops_deploy_before_any_aws_read()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_rejects_an_unimplemented_container_engine_before_touching_the_account()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_returncode_is_passed_through()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **.probe()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **`subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。** (1 connections) — `deploy_aws/tests/test_provider.py`
- **把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **`GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…** (1 connections) — `deploy_aws/tests/test_provider.py`
- **.__call__()** (1 connections) — `deploy_aws/tests/test_provider.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_provider.py`

## Relationships

- [Deploy Provider Interface](Deploy_Provider_Interface.md) (15 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)
- [CDK Destroy/Bootstrap CLI](CDK_Destroy-Bootstrap_CLI.md) (1 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 30 (94%)
- INFERRED: 2 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*