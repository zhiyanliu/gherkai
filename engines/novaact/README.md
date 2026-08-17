# novaact (Python 引擎子工程)

Nova Act (Python) 侧的执行引擎。用 Amazon 自家模型 `nova-act-latest`，**纯 IAM 鉴权（经 `@workflow`）**，浏览器跑在 **AgentCore 云端**。

> 目录故意叫 `novaact`（无下划线），避开与 pip 包 `import nova_act` 撞名。

## 鉴权（纯 IAM，不用 NOVA_ACT_API_KEY）

复用本机 AWS 凭证，经 Nova Act 的 `Workflow` 构造（见 ADR 0004）：

- `model_id="nova-act-latest"`，`boto_session_kwargs={"region_name": <AWS_REGION>}`（region 不硬编码：由组合根落实后经 `AWS_REGION` 注入，见 `worker/run_scope.py` 的 `REGION`；ADR 0016 决策 C / 0033）
- workflow definition：**代码自动 create-if-not-exists**（`lib/workflow_setup.py` 的 `ensure_workflow_definition()`，worker 与 spike 已接入），无需手动 CLI。boto3 与 `aws nova-act create-workflow-definition` 等价。
- 注意：`provider.cdp_session()` 靠 contextvar 识别 workflow；用 `@workflow` 装饰器，或手动 `set_current_workflow(wf)`（见 `worker/run_scope.py` 的 `with wf` + `set_current_workflow`）。

## 环境

`uv` 管理的 `.venv`（Python 3.13）。所有命令用 `.venv/bin/python`，不碰系统 Python。

## 执行形态：薄 worker（pytest-bdd 已退役）

本引擎的执行入口是 `worker/run_scope.py`——被根 `core/` spawn 的薄 worker（core 自解析 `.feature`、
把每个 step 经 0024 协议派发进来，ADR 0022）。**pytest-bdd 入口（`bdd/` 层）已随 v0.x BDD 层退役删除**。
正常经 cli 跑（根 `cli/`）；worker 也可手动直跑调试：

```bash
echo '<job json>' | AWS_REGION=us-east-1 .venv/bin/python worker/run_scope.py
```

## 跑 spike（可独立跑）

```bash
AWS_REGION=us-east-1 .venv/bin/python spikes/wikipedia_benchmark.py    # 对标基准（维基百科端到端）
AWS_REGION=us-east-1 .venv/bin/python spikes/negative_assertions.py    # 负向断言（"该红能红"，对标 midscene 05）
```

## 报告

Nova Act 每次 `act`/`act_get` 各出一个 trajectory HTML。落点分两种：

- **正常经 cli 跑**：组合根经环境变量 `NOVA_LOGS_DIR` 注入 run 专属持久目录 `reports/<run_id>/nova-trajectories`，worker 原样交给 `NovaAct(logs_directory=...)`（ADR 0027；scope 级 `session_summary.json` 落同一 base）；产物再经 `ArtifactUploader` 传 S3（ADR 0029）。
- **手动直跑 worker / 跑 spike**（不设 `NOVA_LOGS_DIR`）：回落 SDK 默认的系统临时目录 `$TMPDIR/..._nova_act_logs/`（会被系统清理），要持久化就自己给 `NovaAct(logs_directory=...)`（见 ADR 0010）。
