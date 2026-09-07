# novaact (Python 引擎子工程)

Nova Act (Python) 侧的执行引擎。用 Amazon 自家模型 `nova-act-latest`，**纯 IAM 鉴权（经 `@workflow`）**，浏览器跑在 **AgentCore 云端**。

> 目录故意叫 `novaact`（无下划线），避开与 pip 包 `import nova_act` 撞名。
>
> 本目录即发行包 **`gherkai-worker-novaact`**（import 名 `gherkai_worker_novaact`、命令名 `gherkai-worker-novaact`，ADR 0037 决策 3）：worker 代码住在 `gherkai_worker_novaact/`，`spikes/` 与 `tests/` 不随包发行。

## 鉴权（纯 IAM，不用 NOVA_ACT_API_KEY）

复用本机 AWS 凭证，经 Nova Act 的 `Workflow` 构造（见 ADR 0004）：

- `model_id="nova-act-latest"`，`boto_session_kwargs={"region_name": <AWS_REGION>}`（region 不硬编码：由组合根落实后经 `AWS_REGION` 注入，见 `gherkai_worker_novaact/run_scope.py` 的 `REGION`；ADR 0016 决策 C / 0033）
- workflow definition：**代码自动 create-if-not-exists**（`gherkai_worker_novaact/lib/workflow_setup.py` 的 `ensure_workflow_definition()`，worker 与 spike 已接入），无需手动 CLI。boto3 与 `aws nova-act create-workflow-definition` 等价。
- 注意：`provider.cdp_session()` 靠 contextvar 识别 workflow；用 `@workflow` 装饰器，或手动 `set_current_workflow(wf)`（见 `gherkai_worker_novaact/run_scope.py` 的 `with wf` + `set_current_workflow`）。

## 环境

**本目录不再有自己的 `.venv`**：它是 repo 根 uv workspace 的一个成员，worker 装进**与 CLI 同一个 venv**（ADR 0037 决策 3——「安装」与「拉起」正交，同 venv 让组合根用 `[sys.executable, "-m", "gherkai_worker_novaact"]` 直接拉起、无包装进程、EVENTS_FD 经 `pass_fds` 直达）。

```bash
uv sync            # 在 repo 根跑一次，core/runtime/cli + 本 worker 一并装好（editable）
```

## 执行形态：薄 worker（pytest-bdd 已退役）

执行入口是包入口 `python -m gherkai_worker_novaact`（= `gherkai_worker_novaact/run_scope.py` 的 `main()`）——被组合根 spawn 的薄 worker（core 自解析 `.feature`、
把每个 step 经 ADR 0024 协议派发进来，ADR 0022）。**pytest-bdd 入口（`bdd/` 层）已随 v0.x BDD 层退役删除**。
正常经 `gherkai` CLI 跑；worker 也可手动直跑调试（下列命令从 repo 根跑）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 uv run python -m gherkai_worker_novaact

# 另有两个「自述」入口（不建会话、不跑 job、零 AWS，ADR 0036）——cli 的 list-deterministic / plan 标注即转述它们：
uv run gherkai-worker-novaact --list-deterministic                    # dump 确定性注册表（pattern + description + example）
echo '["页面地址匹配 \"/wiki/OpenAI\""]' | uv run python -m gherkai_worker_novaact --match-steps   # 批量问这些 step 各命中什么
```

> `python -m gherkai_worker_novaact` 与 console script `gherkai-worker-novaact` 是**同一个 `main()`**（定位链的第二、三级，ADR 0037 决策 3），行为逐字一致。

## 确定性 step：内建脚手架 vs 使用方的 `steps/`

确定性注册表 = **本包内建脚手架**（`gherkai_worker_novaact/deterministic_steps.py`，一条 URL 锚点作范例）
**+ 使用方项目里的 `steps/` 目录**（ADR 0037 决策 4）。使用方**不改包内文件**（那是发行内容、改它等于 fork），
而是在自己项目里写 `steps/*.py`：

```python
# steps/login.py
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'以 "(?P<user>[^"]+)" 登录', description="确定性登录", example='Given 以 "alice" 登录')
def login(ctx, user):
    ctx.page.fill("#user", user)
```

worker **只认一个环境变量 `GHERKAI_STEPS_DIR`**——`--steps-dir` flag / 默认 `./steps` / 随 run definition 持久化
全由 CLI 侧（组合根）解析后注入，worker 不猜路径（ADR 0037 决策 4）。故日常用 `gherkai run --steps-dir …`
就够；手动直跑 worker 时自己给 env：

```bash
GHERKAI_STEPS_DIR=$PWD/steps uv run gherkai-worker-novaact --list-deterministic   # 清单含使用方 step
```

加载规则（`gherkai_worker_novaact/user_steps.py`）：排序递归遍历 `*.py`；跳过 `_*.py`（供相对 import 的辅助模块）
与 `test_*.py`（使用方自己的测试）；**任一文件 import 失败或目录不存在即非 0 退出并指名文件**（绝不静默跳过——
跳过等于把确定性 step 悄悄换成 AI catch-all）；steps 根**不进 `sys.path`**（使用方一个 `json.py` 也不会遮蔽标准库）。
云端档的 steps 烙进定制镜像（ADR 0038），不经此 env。

## 跑测试

从 **repo 根**跑（本目录不再有独立 venv）：

```bash
uv run pytest -q engines/novaact/tests     # 只跑本引擎
uv run pytest -q                           # 跑全 workspace（根 testpaths 已含本目录）
```

## 跑 spike（可独立跑，不随包发行）

```bash
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/wikipedia_benchmark.py    # 对标基准（维基百科端到端）
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/negative_assertions.py    # 负向断言（"该红能红"，对标 midscene 05）
```

## 报告

Nova Act 每次 `act`/`act_get` 各出一个 trajectory HTML。落点分两种：

- **正常经 cli 跑**：组合根经环境变量 `NOVA_LOGS_DIR` 注入 run 专属持久目录 `reports/<run_id>/nova-trajectories`，worker 原样交给 `NovaAct(logs_directory=...)`（ADR 0027；scope 级 `session_summary.json` 落同一 base）；产物再经 `ArtifactUploader` 传 S3（ADR 0029）。
- **手动直跑 worker / 跑 spike**（不设 `NOVA_LOGS_DIR`）：回落 SDK 默认的系统临时目录 `$TMPDIR/..._nova_act_logs/`（会被系统清理），要持久化就自己给 `NovaAct(logs_directory=...)`（见 ADR 0010）。

## 容器镜像

`Dockerfile` = Fargate 档的 worker 基底镜像（`COPY gherkai_worker_novaact/` + `PYTHONPATH=/app` + `CMD python -m gherkai_worker_novaact`，**零使用方内容**）。必须 `--platform linux/amd64`，理由与定制层模板见 ADR 0033 / 0037 决策 5 / 0038。
