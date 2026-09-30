# Container Engine Wrapper

> 16 nodes · cohesion 0.16

## Key Concepts

- **ContainerEngine** (16 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **._run()** (6 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **._stream()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.login()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.pull()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.push()** (3 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.tag()** (2 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.__init__()** (2 connections) — `deploy_aws/tests/test_container.py`
- **test_probe_reports_missing_binary_without_raising()** (2 connections) — `deploy_aws/tests/test_container.py`
- **.__init__()** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **拉镜像（基础镜像同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 结构不同）。 `binary`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`

## Relationships

- [Container Engine Tests](Container_Engine_Tests.md) (4 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (3 shared connections)
- [Engine Probe & Inspect](Engine_Probe_%26_Inspect.md) (3 shared connections)
- [Container Engine Resolution](Container_Engine_Resolution.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`

## Audit Trail

- EXTRACTED: 29 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*