# novaact (Python 引擎子工程)

Nova Act (Python) 侧的执行引擎。用 Amazon 自家模型 `nova-act-latest`，**纯 IAM 鉴权（经 `@workflow`）**，浏览器跑在 **AgentCore 云端**。

> 目录故意叫 `novaact`（无下划线），避开与 pip 包 `import nova_act` 撞名。

## 鉴权（纯 IAM，不用 NOVA_ACT_API_KEY）

复用本机 AWS 凭证，经 Nova Act 的 `Workflow` 构造（见 ADR 0004）：

- `model_id="nova-act-latest"`，`boto_session_kwargs={"region_name": "us-east-1"}`
- workflow definition：**代码自动 create-if-not-exists**（`lib/workflow_setup.py` 的 `ensure_workflow_definition()`，bdd 与 spike 已接入），无需手动 CLI。boto3 与 `aws nova-act create-workflow-definition` 等价。
- 注意：`provider.cdp_session()` 靠 contextvar 识别 workflow；用 `@workflow` 装饰器，或在 fixture 内手动 `set_current_workflow(wf)`（见 `bdd/test_generic_steps.py`）。

## 环境

`uv` 管理的 `.venv`（Python 3.13）。所有命令用 `.venv/bin/python`，不碰系统 Python。

## 跑 BDD（pytest-bdd，加载根 `features/`）

```bash
AWS_REGION=us-east-1 .venv/bin/python -m pytest bdd/test_wikipedia.py -s
```

## 跑 spike（对标基准，可独立跑）

```bash
AWS_REGION=us-east-1 .venv/bin/python spikes/wikipedia_benchmark.py
```

## 报告

Nova Act 每次 `act`/`act_get` 各出一个 trajectory HTML，默认落系统临时目录 `$TMPDIR/..._nova_act_logs/`（会被系统清理）。要持久化可给 `NovaAct(logs_directory=...)`（见 ADR 0010）。
