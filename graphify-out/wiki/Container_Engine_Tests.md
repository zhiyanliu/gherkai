# Container Engine Tests

> 16 nodes · cohesion 0.18

## Key Concepts

- **test_container.py** (28 connections) — `deploy_aws/tests/test_container.py`
- **_Fake** (14 connections) — `deploy_aws/tests/test_container.py`
- **test_inspect_missing_image_is_not_an_error()** (4 connections) — `deploy_aws/tests/test_container.py`
- **test_inspect_parses_os_arch_and_repo_digests()** (3 connections) — `deploy_aws/tests/test_container.py`
- **test_login_password_goes_through_stdin_never_argv()** (3 connections) — `deploy_aws/tests/test_container.py`
- **_inspect_spec()** (2 connections) — `deploy_aws/tests/test_container.py`
- **test_inspect_other_failure_raises()** (2 connections) — `deploy_aws/tests/test_container.py`
- **test_push_failure_raises_container_error()** (2 connections) — `deploy_aws/tests/test_container.py`
- **test_tag_push_pull_command_shape()** (2 connections) — `deploy_aws/tests/test_container.py`
- **_docker_ok()** (1 connections) — `deploy_aws/tests/test_container.py`
- **.calls()** (1 connections) — `deploy_aws/tests/test_container.py`
- **_has_image()** (1 connections) — `deploy_aws/tests/test_container.py`
- **容器引擎口子测试（ADR 0038「容器引擎口子」）。 **两层证据，分清边界**： - 大部分用一个**假 docker**（记 argv/stdin 的…** (1 connections) — `deploy_aws/tests/test_container.py`
- **「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。** (1 connections) — `deploy_aws/tests/test_container.py`
- ****密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。** (1 connections) — `deploy_aws/tests/test_container.py`
- **假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。** (1 connections) — `deploy_aws/tests/test_container.py`

## Relationships

- [Container Engine Resolution](Container_Engine_Resolution.md) (7 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (5 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (4 shared connections)
- [Image Platform Info](Image_Platform_Info.md) (4 shared connections)
- [Repo Digest Selection](Repo_Digest_Selection.md) (3 shared connections)

## Source Files

- `deploy_aws/tests/test_container.py`

## Audit Trail

- EXTRACTED: 41 (91%)
- INFERRED: 4 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*