# 开发笔记（contributor）

> 面向使用者的文档是同目录的 [`README.md`](./README.md)（它逐字上 PyPI 页面）；**本文件面向 contributor**，不随包发行。

## 这个目录是什么

本目录即发行包 **`gherkai-worker-novaact`**（import 名 `gherkai_worker_novaact`、console script `gherkai-worker-novaact`，见 [ADR 0037](../../docs/adr/0037-distribution-and-packaging.md) 决策 3）：worker 代码住 `gherkai_worker_novaact/`，`spikes/` 与 `tests/` 不进 wheel（装上的包里没有；sdist 按 hatch 默认仍收录）。

> 目录故意叫 `novaact`（无下划线），避开与 pip 包 `import nova_act` 撞名。

## 环境

**本目录没有自己的 `.venv`**：它是 repo 根 uv workspace 的一个成员，worker 装进**与 CLI 同一个 venv**（ADR 0037 决策 3——「安装」与「拉起」正交，同 venv 让组合根用 `[sys.executable, "-m", "gherkai_worker_novaact"]` 直接拉起、无包装进程、EVENTS_FD 经 `pass_fds` 直达）。

```bash
uv sync            # 在 repo 根跑一次，core/runtime/cli + 本 worker 一并装好（editable）
```

## 执行形态：薄 worker（pytest-bdd 已退役）

执行入口是包入口 `python -m gherkai_worker_novaact`（= `gherkai_worker_novaact/run_scope.py` 的 `main()`）——被组合根 spawn 的薄 worker（core 自解析 `.feature`、把每个 step 经 [ADR 0024](../../docs/adr/0024-worker-core-protocol.md) 协议派发进来，[ADR 0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md)）。**pytest-bdd 入口（`bdd/` 层）已随 v0.x BDD 层退役删除**。

`python -m gherkai_worker_novaact` 与 console script `gherkai-worker-novaact` 是**同一个 `main()`**（定位链第二、三级，ADR 0037 决策 3），行为逐字一致；**入口不做任何包装**（不起子进程、不改 fd）——worker 必须是组合根直接 spawn 的那个进程，中间任何包装层都会吞掉 fd3（EVENTS_FD 经 `pass_fds` 继承，ADR 0024 三通道）。

正常经 `gherkai` CLI 跑；worker 也可手动直跑调试（下列命令从 repo 根跑）：

```bash
echo '<job json>' | AWS_REGION=us-east-1 uv run python -m gherkai_worker_novaact

# 两个「自述」入口（不建会话、不跑 job、零 AWS，[ADR 0036](../../docs/adr/0036-deterministic-capability-discovery.md)）——cli 的 list-deterministic / plan 标注即转述它们：
uv run gherkai-worker-novaact --list-deterministic                    # dump 确定性注册表（pattern + description + example）
echo '["页面地址匹配 \"/wiki/OpenAI\""]' | uv run python -m gherkai_worker_novaact --match-steps   # 批量问这些 step 各命中什么
```

让 CLI 指向本 checkout（dev 覆写，定位链第一级）：`export GHERKAI_WORKER_NOVAACT_CMD="$(pwd)/.venv/bin/python -m gherkai_worker_novaact"`——workspace 已装 editable 时通常**不需要**（第二级同 venv 就命中）。

## 鉴权（纯 IAM，不用 NOVA_ACT_API_KEY）

复用本机 AWS 凭证，经 Nova Act 的 `Workflow` 构造（见 [ADR 0004](../../docs/adr/0004-novaact-iam-auth-via-workflow.md)）：

- `model_id="nova-act-latest"`，`boto_session_kwargs={"region_name": <AWS_REGION>}`（region 不硬编码：由组合根落实后经 `AWS_REGION` 注入，见 `gherkai_worker_novaact/run_scope.py` 的 `REGION`；[ADR 0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 决策 C / [ADR 0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)）
- workflow definition：**代码自动 create-if-not-exists**（`gherkai_worker_novaact/lib/workflow_setup.py` 的 `ensure_workflow_definition()`，worker 与 spike 已接入），无需手动 CLI。boto3 与 `aws nova-act create-workflow-definition` 等价。
- **真踩过**：`provider.cdp_session()` 靠 contextvar 识别 workflow——用 `@workflow` 装饰器，或手动 `set_current_workflow(wf)`（worker 走 `with Workflow`，故须手动补，见 `gherkai_worker_novaact/run_scope.py` 的 `with wf` + `set_current_workflow`）。

## 确定性 step：内建脚手架 vs 使用方的 `steps/`

确定性注册表 = **本包内建脚手架**（`gherkai_worker_novaact/deterministic_steps.py`，一条 URL 锚点作范例）**+ 使用方项目里的 `steps/` 目录**（ADR 0037 决策 4）。使用方**不改包内文件**（那是发行内容、改它等于 fork）。

worker **只认一个环境变量 `GHERKAI_STEPS_DIR`**——`--steps-dir` flag / 默认 `./steps` / 随 run definition 持久化全由 CLI 侧（组合根）解析后注入，worker 不猜路径（ADR 0037 决策 4）。手动直跑 worker 时自己给 env：

```bash
GHERKAI_STEPS_DIR=$PWD/steps uv run gherkai-worker-novaact --list-deterministic   # 清单含使用方 step
```

加载实现（`gherkai_worker_novaact/user_steps.py`）的两条不变量，各有具体的坑作依据：

- **steps 根不进 `sys.path`**：否则使用方目录里一个 `json.py` / `re.py` 就遮蔽标准库、症状离原因极远。故按文件路径 `spec_from_file_location` 加载，模块名挂在合成命名空间 `gherkai_user_steps.*` 下；合成包的 `__path__` 指向 steps 目录本身，使 step 文件间的**相对** import（`from . import _helpers`）可用——这也是 `_*` 前缀被排除在自动加载之外的用途。
- **加载失败 fail-loud**：任一文件 import 失败或目录不存在 → 非 0 退出（`EX_STEPS_LOAD = 2`）并指名文件。绝不静默跳过——跳过等于把确定性 step 悄悄换成 AI catch-all、run 还可能「通过」。

Nova 侧**不需要** midscene 那条「加载完某文件若零注册即报错」的兜底：同进程 + 绝对包 import 恒命中同一 module 对象，不存在 midscene 的「模块双实例把注册写进一张永远不读的表」风险。

云端档的 steps 烙进定制镜像（[ADR 0038](../../docs/adr/0038-worker-image-delivery.md)），不经此 env。

## 跑测试

从 **repo 根**跑（本目录没有独立 venv）：

```bash
uv run pytest -q engines/novaact/tests     # 只跑本引擎
uv run pytest -q                           # 跑全 workspace（根 testpaths 已含本目录）
```

## 跑 spike（可独立跑，不进 wheel）

```bash
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/wikipedia_benchmark.py    # 对标基准（维基百科端到端）
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/negative_assertions.py    # 负向断言（"该红能红"，对标 midscene 05）
```

## 报告落点

Nova Act 每次 `act`/`act_get` 各出一个 trajectory HTML。落点分两种：

- **正常经 cli 跑**：组合根经环境变量 `NOVA_LOGS_DIR` 注入 run 专属持久目录 `reports/<run_id>/nova-trajectories`，worker 原样交给 `NovaAct(logs_directory=...)`（[ADR 0027](../../docs/adr/0027-runreport-aggregation-index.md)；scope 级 `session_summary.json` 落同一 base）；产物再经 `ArtifactUploader` 传 S3（[ADR 0029](../../docs/adr/0029-engine-artifacts-to-s3.md)）。
- **手动直跑 worker / 跑 spike**（不设 `NOVA_LOGS_DIR`）：回落 SDK 默认的系统临时目录 `$TMPDIR/..._nova_act_logs/`（会被系统清理），要持久化就自己给 `NovaAct(logs_directory=...)`（见 [ADR 0010](../../docs/adr/0010-spike-as-apples-to-apples-benchmark.md)）。

`--no-report` 档由组合根经 env 告知，worker 不生成也不上报引擎原生产物（ADR 0037 决策 3）。

## 容器镜像（维护者向）

`Dockerfile` = Fargate 档的 worker **基底**镜像（`gherkai-worker-novaact` + SDK 运行时 + 协议层，**零使用方内容**）；使用方的定制层模板（`FROM <基底>` + `COPY steps/` + `GHERKAI_STEPS_DIR`）在 README 与 ADR 0038。

同一份 Dockerfile **两态**，`--build-arg WORKER_SOURCE=` 选（ADR 0037 决策 5）：

- `index`（默认，CI 态）：按 `--build-arg WORKER_VERSION=X.Y.Z` 从 PyPI 装已发行包；本态不 COPY，build context 任意。
- `local`（发行前本地验镜像）：装 build context 里的 wheel——容器内无 git 元数据、`pip install .` 算不出版本，故先 `uv build`：

```bash
uv build --package gherkai-worker-novaact --out-dir dist
docker build --platform linux/amd64 -f engines/novaact/Dockerfile \
  --build-arg WORKER_SOURCE=local --build-arg WORKER_WHEEL=gherkai_worker_novaact-<ver>-py3-none-any.whl \
  -t gherkai-worker-novaact:dev dist/        # context = 放 wheel 的目录
```

真 build 踩过的三条：

- **必须 `--platform linux/amd64`**：Fargate task-def 固定 X86_64；arm Mac 不加则 build 出 arm64、容器启动期 `exec format error` 挂死（ADR 0033/0038）。
- **经典 builder（无 buildx）会把未选中的 stage 也跑一遍**，故两个 stage 都对「自己的参数没给」保持容忍（`if [ -n … ]`）；真正的把关在 final stage 的冒烟（`--list-deterministic`，不需要 AWS），漏 build-arg 在那里 fail-loud、不拖到 Fargate 启动期。
- wheel 必须用**原文件名**装：pip 从文件名解析发行名/版本/tag，改名会被拒「Invalid wheel filename」。

**不装 chromium 二进制**：worker 连的是 AgentCore 云浏览器（`cdp_session` → `connectOverCDP`），playwright 只作 CDP 客户端库、不 launch 本地 chromium——省几百 MB，真跑验证过。

## 相关 ADR

[0004](../../docs/adr/0004-novaact-iam-auth-via-workflow.md) IAM 鉴权 ·
[0016](../../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 ·
[0020](../../docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md) step 措辞与角色边界 ·
[0022](../../docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md) 薄 worker ·
[0024](../../docs/adr/0024-worker-core-protocol.md) worker↔core 协议 ·
[0027](../../docs/adr/0027-runreport-aggregation-index.md) 报告聚合 ·
[0028](../../docs/adr/0028-transient-network-ssl-resilience.md) 网络韧性与退出码 80 ·
[0029](../../docs/adr/0029-engine-artifacts-to-s3.md) 产物上传 ·
[0033](../../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) IaC 与装配 ·
[0036](../../docs/adr/0036-deterministic-capability-discovery.md) 能力自述 ·
[0037](../../docs/adr/0037-distribution-and-packaging.md) 分发与打包 ·
[0038](../../docs/adr/0038-worker-image-delivery.md) 镜像交付
