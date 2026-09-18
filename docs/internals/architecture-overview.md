# 架构总览：五层结构、一次 run 的一生、包与发行物

> 本文讲**机制如何协同工作**，不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。「有哪些部件、各自负责什么、一次 run 依次经过谁」这张全景图，散在 [ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（分层）、[ADR 0024](../adr/0024-worker-core-protocol.md)（协议）、[ADR 0037](../adr/0037-distribution-and-packaging.md)（打包）等六七个 ADR 里，每个 ADR 只露出自己那一角。

本文是**入口页**：给全景与边界。推进链细节、判定算法、产物落点、确定性 step 派发、云端载体的更新传播各有自己的 owner 页，下文只给链接、不重复。使用者视角的操作与选项在 [`docs/user-guide/`](../user-guide/README.md)。

**术语速览**（下文按此用词，完整术语见 [`CONTEXT.md`](../../CONTEXT.md)）：**scope** = 共享同一操作上下文的 scenario 分组，也是执行与调度的最小单位（一个 scope = 一个 job）；**worker** = 跑一个 job 的引擎进程；**adapter** = 把核心接到某个具体落库/执行实现上的可替换件；**组合根** = 选定并注入这些 adapter 的装配层。

## 1. 全景图

![五层全景：用例文本经 CLI / runtime / core 到两个对称的引擎 worker，再经云端浏览器连上被测应用](../diagrams/architecture-overview-layers.svg)

图注：**部署 provider 不在 run 的执行路径上**——只有 `deploy` / `destroy` 与 `doctor` 的部署工具链自检会碰它；云端跑时参与的只是它的产出（stack 资源、Lambda、task-def）。图上 ① 只有一条去向 ②（用例文本经 CLI 读入），`steps/` 的实际加载者是 ③ 的 worker——两档的差异见 §2 表 ① 行，搬运链见 [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md)。

## 2. 五层各自的职责

| 层 | code | 负责 | 不负责 | 权威 |
|---|---|---|---|---|
| ① 用例层 | 使用方项目的 `.feature` 与 `steps/`（仓库内示例见 [`features/`](../../features/)） | 用自然语言写动作与断言；用 `@scope` / `@engine` / `@timeout` tag 表达分组、引擎与超时预算（未标 `@engine` 的 scenario 走 `--default-engine`，缺省 `novaact`）；确定性 step 在 `steps/` 里注册正则 | 不含框架实现：这一层只有 `.feature` 文本与 `steps/` 里 import 注册 API 的少量胶水代码，调度、判定、引擎驱动都不在这里；`steps/` 在本机档直接被 worker 加载、在云端档由镜像提供 | [ADR 0019](../adr/0019-feature-tags-scope-and-engine.md)（tag 语义）、[ADR 0036](../adr/0036-deterministic-capability-discovery.md) |
| ② 产品层：CLI | `cli/gherkai_cli/`（`__main__.py` argparse 入口、`render.py`、`deploy.py`、`skill_install.py`） | 解析参数 → 读 feature → 注入引擎解析器 → 调核心 → 渲染文本与 `--json`；退出码由它给出。另有两个隐藏子命令（`_reconcile` / `_tunnel_watch`）是 `submit` fork 出的后台进程与隧道守护的入口，不给使用者直接调；完整命令面与各命令的选项见 [`docs/user-guide/`](../user-guide/README.md) 与 `gherkai --help` | 不含判定逻辑、不含引擎知识；核心库不依赖这层命令行入口——当前 CLI 是唯一前端，将来若再加别的前端（如 Web 界面，尚未实装），同样按这一分层直接调 `gherkai-core`、不 shell-out CLI | [ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md) |
| ② 产品层：gherkai-runtime | `runtime/gherkai_runtime/`（`compose.py` 组合根、`names.py` 命名、`detached.py` 后台推进进程、`tunnel*.py` 隧道） | 把抽象的核心接线到具体实现：解析各引擎 worker 的拉起命令（四级顺序：env 覆写 → 同 venv 的 import 模块 → PATH 上的命令 → 按版本临时拉起；第二级只 Python 引擎有、第四级只 Nova Act 有）、按 `--backend` 注入 adapter、由 `--prefix` 推导全部云资源名、起隧道、`submit` 时 fork 出脱离 CLI 的推进进程 | 不做判定与调度决策；命名纯函数零依赖，部署 provider 直接 import 同一份 | [ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 3、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（两层命名）、[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md)（隧道） |
| ② 产品层：gherkai-core | `core/gherkai_core/`（`parse` / `scope` / `schedule` / `reconcile` / `project` / `persist` / `model` / `ports` / `wire` / `serialize` / `errors` / `adapters`） | 解析 `.feature`、分组成 job、并发调度或单步推进、归约事件成判定、落库与归集报告。全部外部能力经 `ports.py` 的 `Engine` / `RunStore` / `ResultStore` / `ReportStore` 与 `reconcile.py` 的 `EventLog` / `Launcher` 六个注入口 | **零引擎依赖**：不 import 引擎、不知道 worker 是子进程还是容器；编排模块内不 import `subprocess` / `boto3` | [ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)、[ADR 0025](../adr/0025-plan-module-feature-to-jobs.md)、[ADR 0026](../adr/0026-schedule-module.md)、[ADR 0034](../adr/0034-detached-batch-reconciler.md) |
| ③ 执行层 | `engines/novaact/gherkai_worker_novaact/`、`engines/midscene/src/` | 各自拿一个 job（= 一个 scope），起一个浏览器会话，逐 step 决定走确定性判定还是交给 AI，把事件逐条吐给核心，收集证据与引擎产物。两侧对称、讲同一套协议 | 不做跨 scope 的调度与判定归约；对「我在哪跑」无知（产物落点与上传目标都是注入的） | [ADR 0024](../adr/0024-worker-core-protocol.md)、[ADR 0017](../adr/0017-cloud-execution-fargate-over-runtime.md)（云端 worker 的计算载体选 Fargate/ECS）、[ADR 0044](../adr/0044-engine-model-selection-and-override.md)（模型选定与覆写） |
| ④ 浏览器层 | Amazon Bedrock AgentCore Browser | 提供云端浏览器；两个 worker 都经 CDP 连进去——Midscene 自己签 SigV4 的升级请求（浏览器标识 `aws.browser.v1`），Nova Act 经 SDK 的 `AgentCoreBrowserSessionProvider`——**每个 scope 一个会话**，会话生命周期在 worker 内 | 本机不装 Chromium；会话不跨 scope 复用 | [ADR 0011](../adr/0011-agentcore-browser-system-default-vs-custom.md)（系统默认 browser vs 自建）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（会话跟踪与清理） |
| ⑤ 被测应用 | 使用方的站点 | 公网可达的站点直连；只在本机或内网可达的应用经 `--expose-local` 起的 ngrok 隧道回连，提交时把 job 文本里的原始 origin 替换成公网 URL | gherkai 不部署被测应用 | [ADR 0035](../adr/0035-local-app-testing-via-tunnel.md) |

两个引擎各自的模型是**当前值**，真源在代码常量、不在文档（故不写在图上）：`engines/novaact/gherkai_worker_novaact/lib/constants.py` 的 `MODEL_ID`（env `NOVA_MODEL_ID` 可覆写）、`engines/midscene/src/lib/agentcore-sigv4.mts` 的 `DEFAULT_MODEL`（env `MIDSCENE_MODEL_ID` 覆写，家族按同文件的推断表得出、必要时 `MIDSCENE_MODEL_FAMILY` 显式给）。

## 3. 一次 run 的生命周期

主干五步（图上末一步拆成「判定归约」与「报告与退出码」两格）。图上顶部两段标的是命令的覆盖范围——`plan` 到分组为止，`run` / `submit` 同样从 `parse` 起、只是不在分组处停，一直走到退出码；`循环体` 那条泳道里的事每个 job 反复发生、可并发；每步的细节各有 owner 页：

![一次 run 的主干：parse → scope 分组 → begin → 驱动循环（起 worker、逐 step、事件与退出信号两条回传）→ 判定归约 → 报告与退出码](../diagrams/architecture-overview-run-lifecycle.svg)

图注：两条回传的**物理通道**在四种组合下各不相同（本机管道 / 云端表、父进程 / 平台观察），本图只画两条回传的方向；通道与推进链的解剖见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)。

1. **parse**：`.feature` 文本 → `Scenario` / `Step` 领域模型。第三方 Gherkin 解析器藏在 `parse.py` 之内，Background / Outline / DataTable / DocString 在这里被展开（[ADR 0025](../adr/0025-plan-module-feature-to-jobs.md)）。
2. **scope 分组**：按 tag 把 scenario 归到 scope，校验 engine 与 timeout 的一致性，产出 `Job[]`——**一个 job 就是一个 scope**，也是调度与执行的最小单位。`plan` 另外对本批用到的**每个引擎**各起一个瞬时本机 worker，问它这些 step 文本各命中哪条确定性模式（某个引擎问不到只丢它那部分标注、不影响 plan 本体）；前两步纯本地、零费用。
3. **begin**：落 definition（run 元数据）与初始运行态。此后一切写入都经 `RunStore` / `ResultStore`，落哪由注入的 adapter 决定（见 §4）。
4. **驱动**：`run` 走 `schedule.py` 的在线循环（每个 worker 一个线程，`--max-concurrency` 即同时活的浏览器会话数上限，缺省 1）；`submit` 走 `reconcile.py` 的无状态单步推进，由每个 run 一个的本机后台进程、`status --wait` 的接力者或云端 Lambda 反复调用。两种驱动的对照、四种组合的解剖见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)。循环内反复发生两件事：
   - **每 scope 一个 worker**：核心经 `Engine` 起 worker，worker 起浏览器会话、逐 step 判断该走哪条路。step 派发的决策链、`steps/` 目录的两个真值源、worker 的两个非 job 入口（能力自述 `--capabilities`、正则匹配查询 `--match-steps`）见 [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md)。
   - **事件流与退出信号**：worker 对核心只说两件事——逐条事件（`scope_started` / `step_done` / …）与进程退出信号；判定要求两件都成立（事件完整 ∧ 进程干净终止）。四种组合下事件走的四条物理通道、退出观察者是谁、job 超时怎么兜，见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) §5-§6。
5. **判定归约与报告**：一票 → step → scenario → job → run 四层归约，七个状态（五个终态，外加 `pending` / `running` 两个前置态）与各命令退出码的分工见 [`verdict-model.md`](./verdict-model.md)；判定真值、引擎产物、逐步证据与 RunReport 落在哪、`explain` 解引用到哪一层，见 [`artifacts-and-evidence.md`](./artifacts-and-evidence.md)；`--json` 的字段级契约见 [`cli-json-contract.md`](./cli-json-contract.md)。

## 4. 本机与云端：同一条链的两种载体

`--backend` 只换 adapter，**不换核心**：`parse` / 分组 / 归约 / 判定模型两档共用一份代码。

| 面 | `--backend local`（缺省） | `--backend cloud` |
|---|---|---|
| worker 在哪 | 本机子进程，事件走专用 fd | Fargate task（ECS cluster `{prefix}cluster`），job 输入放 S3、事件逐条写 DynamoDB |
| 起 worker 的 adapter | `adapters/subprocess_engine.py`（前台）、`runtime/gherkai_runtime/detached.py` 的 `SubprocessLauncher`（后台） | `adapters/fargate_engine.py`（前台）、`adapters/cloud_launcher.py`（后台） |
| 运行态与判定真值 | 文件树 `<report-dir>/<run_id>/`（缺省 `reports/`） | DynamoDB `{prefix}runs`（元数据与运行态两个 item）+ S3 `{prefix}artifacts`（判定真值与报告，key 镜像本机树的相对路径） |
| 事件 | 前台在线消费、不落盘；后台推进时事件另写入 `events.db`（SQLite） | DynamoDB `{prefix}events`（worker `PutItem`，读侧 `Query`） |
| `submit` 谁在推进 | 本机 `setsid` 脱离出的后台进程，本机需保持开机 | 三个 Lambda（`{prefix}kicker` / `{prefix}reconciler` / `{prefix}exit-observer`）由两条表 Stream 与一条「ECS 任务已停止」事件规则串起（互不调用），提交完关机也跑完 |
| 确定性 step 从哪来 | `--steps-dir`（缺省 `./steps`，或 env `GHERKAI_STEPS_DIR`），worker 启动时加载 | 在构建 variant 镜像时打包进镜像，提交侧 `--steps-dir` 对它无效（给了只警告） |
| worker 日志 | 屏幕；`--quiet` 时落 `<report-dir>/<run_id>/worker.log` | CloudWatch 日志组 `/<prefix>worker/<engine>` |
| 前置 | 本机 AWS 凭证 + 用到的那个引擎 worker 装在本机 | 部署方先跑过 `gherkai deploy --vpc <档> --prefix <前缀>`；提交侧只需最小云端权限 |

一个 `--prefix` = 一套完整环境，多环境靠多 prefix 并存。云端那边由五种各自独立更新的载体拼成（stack、Lambda asset、基底镜像、variant 镜像、SSM 参数），「改了东西为什么云端没变」的反查表在 [`cloud-backend-carriers.md`](./cloud-backend-carriers.md)。

## 5. 包与发行物

版本真源是一个 git tag：五个 Python 包同号、兄弟包之间 `==` 同版本钉死，npm 包与两个基底镜像用同一个版本号。下表只给发行物与通道的对应关系；安装步骤、AWS 前置与 `doctor` 预检见 [`getting-started.md`](../user-guide/getting-started.md)。

| 发行物 | 通道 | import / 命令名 | 装在谁的机器上 |
|---|---|---|---|
| `gherkai` | PyPI（CLI 主包） | 包 `gherkai_cli`，命令 `gherkai`；随 wheel 带 agent skill 包数据 | 所有使用者 |
| `gherkai-runtime` | PyPI，被 `==` 钉住 | 包 `gherkai_runtime` | 随 CLI 装，使用者不直接装 |
| `gherkai-core` | PyPI，被 `==` 钉住 | 包 `gherkai_core` | 随 CLI 装 |
| `gherkai-worker-novaact` | PyPI，经 CLI extra `[local]` 装进**同一个** venv | 包 `gherkai_worker_novaact`，命令 `gherkai-worker-novaact` | 要在本机跑 Nova Act 的人 |
| `@gherkai/worker-midscene` | npm，Node ≥22 | 命令 `gherkai-worker-midscene` | 要在本机跑 Midscene 的人 |
| `gherkai-deploy-aws` | PyPI，经 CLI extra `[deploy-aws]`；按 entry point group `gherkai.deploy` 被发现（名 `aws`） | 包 `gherkai_deploy_aws`，命令 `gherkai deploy` / `destroy` | 部署方（另需 Node ≥22 与容器引擎） |
| 两个基底镜像 | GHCR：`ghcr.io/zhiyanliu/gherkai-worker-novaact:X.Y.Z`、`…-midscene:X.Y.Z`（linux/amd64） | — | 不直接运行时拉：`gherkai deploy` 把它同步进使用方 ECR |
| variant 镜像 | 使用方私有 ECR | — | 使用方自己 build（基底 + 自己的 `steps/`），`gherkai deploy push-worker` 推送注册 |

仓库里的 `features/`、`tools/`、`docs/`、`graphify-out/`、`skills/` 都不随包分发。CLI 与云端后端必须同版本：`--backend cloud` 在提交前检查里比对两侧的版本戳——CLI 比后端**新**时拒绝执行，并给出两条出路（部署方把后端升上来 / 临时用与后端同版本的 CLI）；CLI 比后端**旧**时只打一行提示、不拦；后端没有版本戳，或任一侧不是纯发行版本，则跳过比对。升级的传播顺序见 [`cloud-backend-carriers.md`](./cloud-backend-carriers.md)。

## 6. 延伸阅读

| 想深入的主题 | 去哪读 |
|---|---|
| 谁在推进 run、事件走哪条通道、超时怎么兜 | [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) |
| 判定怎么算出来、七个状态、各命令退出码 | [`verdict-model.md`](./verdict-model.md) |
| 产物与证据落在哪、失败先读哪 | [`artifacts-and-evidence.md`](./artifacts-and-evidence.md) |
| 确定性 step 从写下到云端命中 | [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) |
| 云端后端的五种载体与更新传播 | [`cloud-backend-carriers.md`](./cloud-backend-carriers.md) |
| `--json` 的字段级契约 | [`cli-json-contract.md`](./cli-json-contract.md) |
| 云端浏览器为何用系统默认、何时切自建 | [ADR 0011](../adr/0011-agentcore-browser-system-default-vs-custom.md) |
| 分层总纲与三层切分的理由 | [ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) |
| worker↔核心协议（三通道分离：事件专用管道 / stdout / stderr；job 入口、退出码、终止契约） | [ADR 0024](../adr/0024-worker-core-protocol.md) |
| 分发与打包（五包、三名分离、版本真源、worker 定位、基底镜像分工） | [ADR 0037](../adr/0037-distribution-and-packaging.md) |
| 云资源清单、两层命名、IAM、提交前检查 | [ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md) |
| 引擎模型的选定与覆写 | [ADR 0044](../adr/0044-engine-model-selection-and-override.md) |
| 怎么用（安装、写用例、跑、看结果、部署、配置） | [`docs/user-guide/`](../user-guide/README.md) |
| 怎么参与开发（目录、测试、发布链） | 根 [`CONTRIBUTING.md`](../../CONTRIBUTING.md) 与各包 `DEVELOPMENT.md` |
