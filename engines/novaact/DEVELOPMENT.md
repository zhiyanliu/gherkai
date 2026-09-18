# 开发笔记（contributor）

> 使用者向文档是 [user guide](../../docs/user-guide/README.md)，同目录的 [`README.md`](./README.md) 是它的入口页（逐字用作 PyPI 页面）；contributor 的总入口是根 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。**本文件面向 contributor**，不随包发行。

## 包身份

本目录即发行包 **`gherkai-worker-novaact`**（import 名 `gherkai_worker_novaact`、console script `gherkai-worker-novaact`，见 [ADR 0037](../../docs/adr/0037-distribution-and-packaging.md) 决策 3）：worker 代码位于 `gherkai_worker_novaact/`，`spikes/` 与 `tests/` 不进 wheel（安装后的包内没有这两个目录；sdist 按 hatch 默认仍收录）。

> 目录名取 `novaact`（无下划线），以避开与 pip 包的 import 名 `nova_act` 同名。

## 模块

```
gherkai_worker_novaact/
├── __init__.py             ← 包级契约：零 `gherkai_core` / `gherkai_runtime` 依赖、必须是被组合根直接 spawn 的那个进程（ADR 0024）；修改本包前先阅读该文件
├── __main__.py             ← 包入口，argv 直通 `run_scope.main`（console script 指向同一个 main，零包装）
├── run_scope.py            ← 薄 worker 主流程：job 循环、step 派发、会话与信号收尾、两个非 job 入口的分派
├── deterministic.py        ← 确定性 step 注册表：`@deterministic` 登记、单条匹配与批量 match
├── deterministic_steps.py  ← 包内建脚手架 step（一条 URL 锚点作范例）
├── user_steps.py           ← 使用方 `steps/` 目录的加载（fail-loud，退出码 `EX_STEPS_LOAD = 2`）
├── evidence.py             ← step 级机读证据：Nova trajectory 裁成自有 schema 的 `evidence.json`（[ADR 0042](../../docs/adr/0042-step-evidence-and-explain.md)）
└── lib/                    ← I/O 边缘与常量：`job_source.py`（job 入口）· `event_sink.py`（事件出口）· `artifact_upload.py`（产物上传）· `workflow_setup.py`（workflow definition 的 create-if-not-exists）· `constants.py`（`MODEL_ID` / `WORKFLOW_DEF` / `NOVA_GRACE_MARGIN_S`）；`__init__.py` 说明这组为何单独成子包
```

`tests/` 是 pytest 用例（`fixtures/` 中是真产物裁出的 trajectory 与一个中断用 worker），`spikes/` 是可独立运行的对标脚本。

## 环境

**本目录没有自己的 `.venv`**：它是 repo 根 uv workspace 的一个成员，worker 装进**与 CLI 同一个 venv**。依据见 ADR 0037 决策 3：「安装」与「拉起」正交；同 venv 使组合根可用 `[sys.executable, "-m", "gherkai_worker_novaact"]` 直接拉起，无包装进程，EVENTS_FD 经 `pass_fds` 直达。

```bash
uv sync            # 在 repo 根跑一次，core/runtime/cli + 本 worker 一并装为 editable
```

依赖与版本钉法（`pyproject.toml`）：`requires-python = ">=3.13"`；SDK **钉精确版本** `nova-act==3.4.187.0`
（升级 = 改 pin → 全套测试 + 评测集真跑 → 随发版说明，见 [ADR 0042](../../docs/adr/0042-step-evidence-and-explain.md) 决策六），
`boto3>=1.34` 直接声明，不经 nova-act 传递依赖（ADR 0037 决策 2c）；包版本由 git tag 经 uv-dynamic-versioning 算出，不写入文件（ADR 0037 决策 2b）。

## 执行形态：薄 worker（pytest-bdd 已退役）

执行入口是包入口 `python -m gherkai_worker_novaact`（= `gherkai_worker_novaact/run_scope.py` 的 `main()`），即被组合根 spawn 的薄 worker：core 自解析 `.feature`，把每个 step 经 [ADR 0024](../../docs/adr/0024-worker-core-protocol.md) 协议派发给 worker（[ADR 0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md)）。**pytest-bdd 入口（`bdd/` 层）已随 v0.x BDD 层退役删除**。

`python -m gherkai_worker_novaact` 与 console script `gherkai-worker-novaact` 是**同一个 `main()`**（定位链第二、三级，ADR 0037 决策 3），行为逐字一致；**入口不做任何包装**（不起子进程、不改 fd）：worker 必须是组合根直接 spawn 的那个进程，中间任何包装层都会使 fd3 丢失（EVENTS_FD 经 `pass_fds` 继承，ADR 0024 三通道）。

常规路径是经 `gherkai` CLI 运行；调试时也可手动直跑 worker（下列命令从 repo 根跑；`<job json>` 的字段说明与可直接改用的样例见 [ADR 0024](../../docs/adr/0024-worker-core-protocol.md)「输入（core → worker）」一节）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 uv run python -m gherkai_worker_novaact

# 两个非 job 入口（不建会话、不跑 job、零 AWS，[ADR 0036](../../docs/adr/0036-deterministic-capability-discovery.md)）；cli 的 `list-deterministic` / `doctor` / run 前置 / plan 标注即转述它们：
uv run gherkai-worker-novaact --capabilities                          # 能力自述：{schema_version, engine, min_grace_s, deterministic_steps, model_id}（清单 = 注册表 pattern + description + example）
echo '["页面地址匹配 \"/wiki/OpenAI\""]' | uv run python -m gherkai_worker_novaact --match-steps   # 批量查询这些 step 各命中什么
```

worker 侧**只有这两个 flag**：确定性清单是 `--capabilities` 对象的 `deterministic_steps` 键，**没有 `--list-deterministic` 入口**（加键不加入口，ADR 0036「5.」）；未识别的 flag 会进入 job 模式并读取 stdin，不会输出不完整的自述。

引擎特定的 env（worker 侧读取；`lib/constants.py` 与 `run_scope.py`）。使用者向的完整 env 清单与「在哪里设才生效」见 [`docs/user-guide/configuration.md`](../../docs/user-guide/configuration.md)，取值的权威在 code 与该页；下表只补充 contributor 需要的定位：常量所在文件、缺省值的标定依据。

| env | 缺省 | 作用 |
|---|---|---|
| `NOVA_MODEL_ID` | `nova-act-v1.0`（`lib/constants.py` 的 `MODEL_ID`） | 传给 `Workflow(model_id=...)` 的模型 id，同时是 `--capabilities` 的 `model_id`。默认钉 GA 版本、不用 `nova-act-latest` 别名，更换默认值须随发版评估（[ADR 0044](../../docs/adr/0044-engine-model-selection-and-override.md) 决策 1/2 两引擎同律，现值登记在该 ADR）；Nova 侧的选型证据见 [ADR 0004](../../docs/adr/0004-novaact-iam-auth-via-workflow.md)「模型版本选择策略」 |
| `NOVA_ACT_TIMEOUT_S` | `120`（`run_scope.ACT_TIMEOUT_S`） | 单个 `act` / `act_get` 的超时上界（SDK 允许 [2,1800]）；真值在组合根，由它注入 worker（[ADR 0024](../../docs/adr/0024-worker-core-protocol.md) act 有界返回） |
| `NOVA_GRACE_MARGIN_S` | `30`（`lib/constants.py`） | 自报 grace 下限的收尾余量：`min_grace_s = NOVA_ACT_TIMEOUT_S + NOVA_GRACE_MARGIN_S`。30 由真容器标定得出（会话释放 ≤9 秒 + 截图队列退出档排空 6 秒，留约两倍余量；推导写在该常量旁注） |
| `NOVA_LOGS_DIR` | 无（不设即回落 SDK `mkdtemp` 出的临时目录） | Nova SDK 的 trajectory 落点，组合根注入 `<report_dir>/<run_id>/nova-trajectories` 绝对路径（子目录名的单一真源是 `runtime/gherkai_runtime/names.py` 的 `ARTIFACT_SUBDIR`）；worker 主流程与 uploader 都读它 |
| `AWS_REGION` | 无（模块级读一次，未设则 `Workflow` 构造失败） | Workflow / AgentCore 会话 / 三条 I/O 边共用的 region，由组合根落实后注入（见 `run_scope.REGION`） |
| `GHERKAI_EXTRA_HTTP_HEADERS` | 无（未设即零行为变化） | JSON 对象；组合根在 `--expose-local` 档注入，worker 在 browser context 级设为额外请求头（[ADR 0035](../../docs/adr/0035-local-app-testing-via-tunnel.md)） |

使 CLI 指向本 checkout（dev 覆写，定位链第一级）：`export GHERKAI_WORKER_NOVAACT_CMD="$(pwd)/.venv/bin/python -m gherkai_worker_novaact"`；workspace 已装 editable 时通常**不需要**（第二级同 venv 即命中）。本引擎还有**第四级**：CLI 版本是纯发行版、且 `uvx` 在 PATH 时，回落到 `uvx gherkai-worker-novaact==<CLI 版本>` 拉起（uvx 虽是包装进程，实测不丢弃 fd3，也转发 SIGTERM）；midscene 没有这一级（`npx` 实测会替换 fd，事件全部丢失）。

## 鉴权（纯 IAM，不用 NOVA_ACT_API_KEY）

复用本机 AWS 凭证，经 Nova Act 的 `Workflow` 构造（见 [ADR 0004](../../docs/adr/0004-novaact-iam-auth-via-workflow.md)）：

- `model_id=MODEL_ID`（`lib/constants.py` 里钉死的 GA 版本 `nova-act-v1.0`，env `NOVA_MODEL_ID` 可覆盖，[ADR 0004](../../docs/adr/0004-novaact-iam-auth-via-workflow.md)「模型版本选择策略」），`boto_session_kwargs={"region_name": <AWS_REGION>}`（region 不硬编码：由组合根落实后经 `AWS_REGION` 注入，见 `gherkai_worker_novaact/run_scope.py` 的 `REGION`；[ADR 0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 决策 C / [ADR 0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）
- workflow definition：**代码自动 create-if-not-exists**（`gherkai_worker_novaact/lib/workflow_setup.py` 的 `ensure_workflow_definition()`，worker 与 spike 已接入），无需手动执行 CLI。boto3 调用与 `aws nova-act create-workflow-definition` 等价。
- **实测约束**：`provider.cdp_session()` 依赖 contextvar 识别 workflow，因此须使用 `@workflow` 装饰器或手动调用 `set_current_workflow(wf)`；worker 使用 `with Workflow`，故须手动调用（见 `gherkai_worker_novaact/run_scope.py` 的 `with wf` + `set_current_workflow`）。

## 确定性 step：内建脚手架 vs 使用方的 `steps/`

确定性注册表 = **本包内建脚手架**（`gherkai_worker_novaact/deterministic_steps.py`，一条 URL 锚点作范例）**+ 使用方项目里的 `steps/` 目录**（ADR 0037 决策 4）。使用方**不修改包内文件**（包内文件是发行内容，修改等同于 fork）；使用方侧的写法见 [user guide](../../docs/user-guide/writing-deterministic-steps.md)。

steps 目录 worker **只认环境变量 `GHERKAI_STEPS_DIR`**：`--steps-dir` flag / 默认 `./steps` / 随 run definition 持久化，全部由 CLI 侧（组合根）解析后注入，worker 不自行推断路径（ADR 0037 决策 4）。手动直跑 worker 时须自行设置该 env：

```bash
GHERKAI_STEPS_DIR=$PWD/steps uv run gherkai-worker-novaact --capabilities   # deterministic_steps 含使用方 step
```

自动加载的筛选与顺序**两引擎同一条规则**：按相对 steps 根的路径排序递归遍历 `*.py`，排除路径任一段以 `_` 开头的文件或目录（供其它 step 文件 import 的辅助模块，`_pages/` 整棵目录跳过）与 `test_*.py`（使用方自己的测试），再逐个按文件路径加载。排序的目的是使注册顺序可复现，进而使能力清单与 conflict 清单可复现。

加载实现（`gherkai_worker_novaact/user_steps.py`）的两条不变量，各有实测依据：

- **steps 根不进 `sys.path`**：否则使用方目录里的一个 `json.py` / `re.py` 即遮蔽标准库，且症状与原因相距极远。故按文件路径 `spec_from_file_location` 加载，模块名置于合成命名空间 `gherkai_user_steps.*` 下；合成包的 `__path__` 指向 steps 目录本身，使 step 文件间的**相对** import（`from . import _helpers`、`from ._pages import selectors`）可用；被排除在自动加载之外的 `_` 前缀文件 / 目录正是这类辅助模块。
- **加载失败 fail-loud**：任一文件 import 失败或目录不存在 → 非 0 退出（`EX_STEPS_LOAD = 2`）并指名文件。绝不静默跳过：跳过等同于把确定性 step 替换为 AI catch-all，且 run 仍可能判为「通过」。

Nova 侧**不需要** midscene 那条「加载完某文件若零注册即报错」的校验：同进程 + 绝对包 import 恒命中同一 module 对象，不存在 midscene 的「模块双实例导致注册写入一张不会被读取的表」风险。

云端档同样**只认 `GHERKAI_STEPS_DIR`**，但取值来自定制 worker 镜像的 `ENV GHERKAI_STEPS_DIR=/app/steps`（steps 随 `COPY` 构建进镜像），不由本机 shell 或 CLI 注入（[ADR 0038](../../docs/adr/0038-worker-image-delivery.md)）。

## 跑测试

从 **repo 根**跑（本目录没有独立 venv）：

```bash
uv run pytest -q engines/novaact/tests     # 只跑本引擎：2026-09-17 实跑 209 passed
uv run pytest -q                           # 跑全 workspace（根 testpaths 已含本目录）
```

## 跑 spike（可独立跑，不进 wheel）

```bash
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/wikipedia_benchmark.py    # 对标基准（维基百科端到端）
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/negative_assertions.py    # 负向断言探针：构造必假断言，验证失败能被判为失败（对标 midscene 05）
```

## 报告落点

Nova Act 每次 `act`/`act_get` 各产出一个 trajectory HTML。落点分两种：

- **正常经 cli 跑**：组合根经环境变量 `NOVA_LOGS_DIR` 注入 run 专属持久目录 `reports/<run_id>/nova-trajectories`，worker 原样交给 `NovaAct(logs_directory=...)`（[ADR 0027](../../docs/adr/0027-runreport-aggregation-index.md)；scope 级 `session_summary.json` 落同一 base）；产物再经 `ArtifactUploader` 传 S3（[ADR 0029](../../docs/adr/0029-engine-artifacts-to-s3.md)）。
- **手动直跑 worker / 跑 spike**（不设 `NOVA_LOGS_DIR`）：回落 SDK 默认的系统临时目录 `$TMPDIR/..._nova_act_logs/`（会被系统清理）；需持久化时自行传入 `NovaAct(logs_directory=...)`（见 [ADR 0010](../../docs/adr/0010-spike-as-apples-to-apples-benchmark.md)）。

`--no-report` 档由组合根经 env `GHERKAI_NO_ARTIFACTS=1` 告知：worker **不收集、不上报**引擎原生产物（不带 `session_summary.json`、不发任何 reportRef、不产 step 级 evidence）。Nova Act SDK 没有关闭 trajectory 的开关，此档下 worker 不传 `logs_directory`，SDK 仍把 trajectory 写入自己 `mkdtemp` 出的临时目录；这是 SDK 内部行为、不进项目（ADR 0037 决策 3）。一次 run 的全部产物落点（两引擎横向、local 与 cloud 两档）见 [`docs/internals/artifacts-and-evidence.md`](../../docs/internals/artifacts-and-evidence.md)。

## 容器镜像（维护者向）

`Dockerfile` = Fargate 档的 worker **基底**镜像（`gherkai-worker-novaact` + SDK 运行时 + 协议层，**零使用方内容**）；使用方的定制层模板（`FROM <基底>` + `COPY steps/` + `GHERKAI_STEPS_DIR`）与推送流程见 [ADR 0038](../../docs/adr/0038-worker-image-delivery.md)（包 README 已降为入口页、不再带模板）。

同一份 Dockerfile 有**两态**，由 `--build-arg WORKER_SOURCE=` 选择（ADR 0037 决策 5）：

- `index`（默认，CI 态）：按 `--build-arg WORKER_VERSION=X.Y.Z` 从 PyPI 安装已发行包；本态不 COPY，build context 任意。
- `local`（发行前本地验证镜像）：安装 build context 里的 wheel；容器内无 git 元数据，`pip install .` 无法算出版本，故先执行 `uv build`：

```bash
uv build --package gherkai-worker-novaact --out-dir dist
docker build --platform linux/amd64 -f engines/novaact/Dockerfile \
  --build-arg WORKER_SOURCE=local --build-arg WORKER_WHEEL=gherkai_worker_novaact-<ver>-py3-none-any.whl \
  -t gherkai-worker-novaact:dev dist/        # context = 放 wheel 的目录
```

真 build 已验证的三条约束：

- **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64；在 arm Mac 上不加该参数会 build 出 arm64 镜像，容器启动期报 `exec format error` 挂死（ADR 0033/0038）。
- **经典 builder（无 buildx）会连未选中的 stage 一并执行**，故两个 stage 都对「本 stage 的参数未给」保持容忍（`if [ -n … ]`）；把关点在 final stage 的冒烟（`--capabilities`，不需要 AWS）：未给 build-arg 时在此处 fail-loud，不延后到 Fargate 启动期。
- wheel 必须以**原文件名**安装：pip 从文件名解析发行名 / 版本 / tag，改名后 pip 以「Invalid wheel filename」拒绝安装。

**不装 chromium 二进制**：worker 连接的是 AgentCore 云浏览器（`cdp_session` → `connectOverCDP`），playwright 只作 CDP 客户端库、不 launch 本地 chromium；镜像因此省下几百 MB，已真跑验证。

## 相关 ADR

[0004](../../docs/adr/0004-novaact-iam-auth-via-workflow.md) IAM 鉴权 ·
[0010](../../docs/adr/0010-spike-as-apples-to-apples-benchmark.md) spike 作同题对标 ·
[0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 ·
[0020](../../docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md) step 措辞与角色边界 ·
[0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md) 薄 worker ·
[0024](../../docs/adr/0024-worker-core-protocol.md) worker↔core 协议 ·
[0027](../../docs/adr/0027-runreport-aggregation-index.md) 报告聚合 ·
[0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 网络韧性与退出码 80 ·
[0029](../../docs/adr/0029-engine-artifacts-to-s3.md) 产物上传 ·
[0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) IaC 与装配 ·
[0035](../../docs/adr/0035-local-app-testing-via-tunnel.md) 本机应用隧道 ·
[0036](../../docs/adr/0036-deterministic-capability-discovery.md) 能力自述 ·
[0037](../../docs/adr/0037-distribution-and-packaging.md) 分发与打包 ·
[0038](../../docs/adr/0038-worker-image-delivery.md) 镜像交付 ·
[0042](../../docs/adr/0042-step-evidence-and-explain.md) step 级证据与 SDK 钉版本 ·
[0044](../../docs/adr/0044-engine-model-selection-and-override.md) 模型选择与覆盖
