# 变更记录

本文件按发行版记录 gherkai 对使用者可见的变化：新增的命令与选项、行为与默认值的调整、修复的问题，以及升级时需要执行的动作。每个发行版在这里都有一节，GitHub Release 的正文取自对应的一节。每个版本的 Release 页（1.4.0 起）见 [GitHub Releases](https://github.com/zhiyanliu/gherkai/releases)。

全部发行包同号发布：命令行工具、两个引擎 worker 与云端后端须装同一个版本。命令与选项的完整说明见[用户指南](./docs/user-guide/README.md)，环境变量总表见[配置](./docs/user-guide/configuration.md)。

格式沿用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 新增

- agent skill 新增一份给测试开发的参考 `references/deterministic-steps.md`：确定性 step 该不该写（含成本与速度判据）、等待与判定、失败消息带现场、判定逻辑与注册分离、本地用真浏览器单测、改一条在用的 step、症状速查。用户指南「编写确定性 step」同步补这几节与两侧完整示例。

### 变化

- 用户指南与 skill 里 Midscene 侧的最小模板改为带等待的判定（此前示例直接读 `isVisible()` 的瞬时值，是确定性 step 假失败的常见来源）。

## [1.4.4] - 2026-09-20

### 变化

- Midscene 引擎的默认模型改为 `us.openai.gpt-5.6-terra`（OpenAI GPT-5.6 Terra，经 Amazon Bedrock 调用）。在同一批用例上重复运行，它的判定稳定不抖动，并且比原默认模型 `qwen.qwen3-vl-235b-a22b` 快约三成、少用约四分之一 token；调用请求已按 Bedrock 对 GPT 系模型的要求调整。费用相应上升：一条 5 步左右的 scenario 约 5 美分，原默认模型约 2 美分（以你账户的 AWS 账单为准），量级与口径见[运行测试与查看结果](./docs/user-guide/running-and-results.md)。该模型经 Bedrock 跨区推理调用，Midscene 的 AI step 模型调用在美国境内三个 region（us-east-1 / us-east-2 / us-west-2）处理；浏览器会话与产物仍在你选的 region，Nova Act 引擎不变。
- Nova Act 引擎的默认模型改为固定的 `nova-act-v1.0`，不再使用跟随最新 GA 版本的别名。同一条断言在不同模型版本上可能翻转，固定版本让结果可复现；换模型只随 gherkai 发版，并在本文件里点明。
- 两个引擎的模型都可用环境变量覆盖：Nova Act 侧 `NOVA_MODEL_ID`；Midscene 侧 `MIDSCENE_MODEL_ID`，模型家族一般由模型 id 自动识别，识别不出时 worker 启动即报错并要求补 `MIDSCENE_MODEL_FAMILY`。本机 local 后端在 shell 里设置即生效；云端 cloud 后端把变量写进定制 worker 镜像。
- `gherkai doctor` 新增一行，显示本机各引擎 worker 实际会用的模型（`--json` 里是 `engines` 段的 `model.<engine>`），在 shell 里设过覆盖变量的机器可以直接核对；云端 worker 的模型写在定制镜像里，不在这一行显示。
- 云端 worker 现在可以调用 Bedrock 上的模型与你账户里的跨区推理入口，不再限定单一模型：换模型只需改定制 worker 镜像里的环境变量，不必重新部署后端。
- 两个引擎的第三方依赖改为固定精确版本：Midscene 侧 `@midscene/web` 升到 1.12.8、Playwright 1.63.0，Nova Act 侧 `nova-act` 3.4.187.0。此前声明的是版本范围，不同时间安装的机器会取到不同版本。
- Midscene 引擎的 token 用量改用引擎 SDK 公开的累计计数，元素定位时的区域搜索调用也计入。同一条用例的报告用量会比此前略高，是统计范围更全，不是模型消耗变多。
- `gherkai deploy` 结束时改为逐行说明默认 worker 镜像 variant 与 worker 运行配置的更新结果，例如「已保留默认 worker 镜像 variant `base`」「各 variant 的 worker 运行配置已是最新」。
- 仓库首页新增「判定由谁做出」一节，列出两个引擎各自使用的模型与服务、版本策略、查看与更换方式，以及费用来源。
- 文档重组：面向使用者的完整说明集中到 [`docs/user-guide/`](./docs/user-guide/README.md)，新增[常见问题](./docs/user-guide/faq.md)页；文档里的图改为统一风格的架构 / 流程 / 时序图，执行与推进全景、云端交付与 worker 身份两张大图另有可交互版本（https://zhiyanliu.github.io/gherkai/ ）；各发行包在 PyPI / npm 上的页面改为入口页，只留定位、装法、最小用法与指向用户指南的链接；本文件是新增的变更记录。
- 命令行的帮助、提示、警告、错误与 `gherkai deploy` 的步骤行统一了用词：口语的「跑」改为「运行」或「执行」；`--default-job-timeout` 的帮助改称「job 墙钟预算秒」；`gherkai skill` 各命令的帮助改称「agent skill」；`deploy` 里同步官方 worker 镜像的那一步改称「基础镜像同步」；`plan` 的输出表头改称「用例预检」。用户文档与随包发行的 agent skill 同批对齐了同一套用词：`plan` 一律称「用例预检」，前台与后台之别称「执行方式」、本机与云端之别称「执行后端」，两者的四种组合称「四种组合」；指一次运行时不再称「批」，统一称 `run` 或「本次运行」。`--vpc` 在帮助与用法行里的取值占位符改为 `取值`，`--require-approval` 的帮助改称「审批级别」，`gherkai deploy` 关于 VPC 的提示与报错统一说「VPC 取值」，与用户指南里的选项表用词一致。命令、选项、输出结构与退出码都没有变化。
- `gherkai --help` 不再列出 `_reconcile` 与 `_tunnel_watch`：它们是 `submit` 在后台启动的子进程入口，不供直接使用；此前二者以「==SUPPRESS==」出现在命令列表里。

- 命令行帮助、提示与两个引擎 worker 的日志继续统一措辞：不再用等号、箭头这类符号代替连词，「退 2」一律写成「退出码 2」；`gherkai status` 的几条帮助去掉了内部名词；两个引擎 worker 对同一种产物用同一个名字（「证据截图」）；产物上传失败的日志只说明什么没传成、不再承诺稍后重试；`gherkai deploy delete-worker` 的占位说明改为使用者语言。命令、选项、输出结构与退出码都没有变化。

### 修复

- Midscene 引擎每个 run 在日志里打出的一段 `Execution context was destroyed` 报错栈已消除（关闭了对云端浏览器无意义的一项 SDK 渲染开关）。
- 引擎无法回答能力查询时的提示改为先给出 worker 自己的报错原文，常见成因（版本不一致、模型配置不对）只在原文没有说明原因时补充。
- `gherkai deploy` 及其 `list-workers` / `push-worker` 子命令：给了不存在的 `--profile` 名、或配不出 region 时，现在以退出码 2 结束并说明「连不上 AWS」；此前会打印一段 Python 报错栈。
- 云端后端：一次 run 的 job 超过 100 个时，job 超时处置此前会失败，或把仍在运行的 task 误判为已不存在而直接记为超时；现在按页读取、分批查询。超时处置的兜底检查出错时，也不再影响同一批事件里其它 run 的推进。
- Midscene worker 收到停止信号时若正在释放浏览器会话，此前可能提前退出而漏掉释放、会话继续计费且退出码仍为 0；现在等释放完成再退出。
- `gherkai deploy` 同时给出只读选项（`--diff` / `--synth-only` / `--bootstrap`）与 worker 镜像子命令时的提示改为可执行的建议；此前对 `--bootstrap` 与 `--synth-only` 给出的建议命令无法运行。
- `gherkai run --json` 的帮助此前写「不打进度」，实际进度与诊断仍走标准错误、只有 `--quiet` 静音逐事件进度；帮助已改准，用户指南同步。
- 各 Python 发行包的源码包（sdist）不再包含测试目录，Nova Act worker 的源码包不再包含探针脚本；源码包内容改为显式白名单，不再受本机忽略规则影响。

### 升级须知

- 在本机 local 后端运行用例的机器上，把命令行工具与你的用例用到的引擎 worker 升到同一版本（`uv tool upgrade gherkai`；Midscene worker 另外执行 `npm i -g @gherkai/worker-midscene@<CLI 版本>`），新的默认模型随 worker 一起升级；版本不一致会在运行前检查时以退出码 2 结束。安装形态见[开始使用](./docs/user-guide/getting-started.md)。
- 部署方须重新执行 `gherkai deploy`：新的默认模型在新版本的 worker 基础镜像里，放宽后的模型调用权限也随部署更新。有自定义 worker 镜像 variant 的团队，从新版本的基础镜像重新构建后用 `gherkai deploy push-worker` 推送一次。升级步骤见[云端后端](./docs/user-guide/cloud-backend.md)。
- 想继续用原来的 Midscene 模型：把 `MIDSCENE_MODEL_ID` 设为 `qwen.qwen3-vl-235b-a22b`（本机 local 后端设在 shell 里，云端 cloud 后端写进定制镜像的环境变量）。

## [1.4.3] - 2026-09-16

### 变化

- 停止 worker 的宽限秒数下限改由引擎 worker 自己报告：本机 local 后端不给 `--grace` 就按 run 里用到的各引擎报出的最短宽限取值，通常是分钟量级（只用 Midscene 引擎的 run 更短），给出小于该下限的值直接退 2。宽限过短会让正在进行的 AI 操作被强制杀掉、云端浏览器会话泄漏。
- `--backend cloud` 不再接受显式 `--grace`：云端 worker 的停止宽限由部署侧的 `gherkai deploy --stop-timeout` 决定，给了这个选项直接退 2，且不会产生任何云端调用。
- `gherkai doctor --backend cloud` 新增一行，把引擎 worker 报出的最短宽限与云端任务定义的停止宽限做比对；不足时提示可以调高部署侧的 `--stop-timeout`。
- 在本机运行之前，命令行工具会先向用到的每个引擎 worker 查询一次它的能力与最短宽限。worker 与命令行工具版本不一致时，命令几秒内退 2 并提示升级该引擎的 worker，不再等到超时。
- `gherkai explain --scenario <SEL> --step N` 点名的那一步一律展开证据，通过的 step 也展开，不必再加 `--all`。
- `gherkai deploy` 少给 `--vpc` 时的提示改为直接说明三档各是什么；后端记着上次部署用的档时，提示里直接给出沿用它的写法。

### 升级须知

- 在本机 local 后端运行用例的机器上，命令行工具与你的用例用到的引擎 worker 要升到同一版本；版本不一致会在运行前检查时退 2（没用到的引擎不受影响）。

## [1.4.2] - 2026-09-16

### 新增

- `gherkai explain <run_id>`：读出失败那一步的证据——AI 的推理、当时页面截图的位置、断言票数与页面地址。`--scenario` / `--step` 收窄范围，`--all` 连通过的 step 也展开，`--full` 逐段全文，`--json` 输出机读结构。
- `gherkai doctor`：一条命令自检环境——引擎是否装好、`steps/` 能否加载；加 `--backend cloud --prefix <前缀>` 连带查 AWS 凭证、region 与云端后端。
- `gherkai skill install`：把驾驭 gherkai 的 agent 技能装进项目（或用户级）的 agent 目录，`--agent` 支持 `claude-code` / `codex` / `all`。技能随命令行工具一起发行。
- 筛选与机读选项补齐：`plan` / `run` / `submit` 支持 `--scenario`（按 `<文件>:<行号>`、行号或标题片段选）与 `--scope`（按 scope_id 精确选整个 scope）；查询类命令都有 `--json`；`--quiet` 不打逐事件进度，本机 worker 日志改落 `<report-dir>/<run_id>/worker.log` 并只打一行位置。
- 判定明细与报告里每个 step 带一行原因（`message`）：说明它为什么不是 `passed`，通过的 step 为 null。

### 变化

- AI step 的截图改为运行期后台上传：每步完成即入队上传，不必等 scope 收尾；收尾时最多等待固定时长让剩余上传完成，失败重试一次。run 被中途停止时，已完成的 step 的截图仍会上传到产物桶，但不会进判定明细——`gherkai explain` 会在该 job 上提示这一点。
- `gherkai status` 在 run 到达终态时打出报告与判定明细的位置；建议加 `--wait` 继续等到终态的提示只在所有 job 都尚未开始运行时出现。
- `explain` 的文本输出统一用机读字段名作前缀（`message:` / `thought:` / `screenshot:` / `error:`），与 `--json` 的字段一致。
- `@scope` 的取值与另一个未标 `@scope` 的 scenario 自动生成的 scope_id 相同时，`plan` / `run` / `submit` 直接报错并给出位置，不再让两个 scope 使用同一个 scope_id。
- Nova Act 引擎在你账户里自动创建的 workflow definition 改名为 `gherkai-worker`；无需手动迁移，云端按新名自动建出。

### 移除

- `gherkai submit` 去掉 `--events-table` 与 `--cluster`：这两个资源名一律按 `--prefix` 推导。
- `gherkai destroy` 去掉 `--allow-vpc-change` 与 `--require-approval`：这条命令从不使用它们，此前给了会被静默忽略，现在直接退 2。

### 修复

- 本机 local 后端的判定明细与报告文件改为原子写入，运行期间读取不会读到写了一半的内容。
- `submit` 起了隧道、后台进程还没接管就失败时，隧道会被立即拆掉，不再残留。
- `explain` 在判定明细还没落地时的提示带上各后端定位 run 的选项。
- `gherkai skill install` 读到非 UTF-8 的目标文件时退 2 并说明真正的原因。

## [1.4.1] - 2026-09-10

### 变化

- 失败或超时的 AI step 同样报出它消耗的时间与用量，此前这部分统计整块丢失。
- 后台批量运行的报告带上 run 级总时长。
- 被测界面的语言支持范围写进文档：Midscene 引擎不限语言（中文界面上的操作与 AI 断言与英文同级可靠）；Nova Act 引擎的支持范围是英文界面——它在中文页面上能操作、能判页面级语义，但「正文里是否出现某个中文词」这类断言会稳定判否。非英文应用请用 `@engine:midscene` 路由。
- worker 镜像 variant 解析失败时的提示补上第二条出路：先用 `--worker-variant base` 运行。
- 各发行包在 PyPI / npm 上的说明页改为面向使用者，开发相关内容移到仓库内。

### 修复

- 云端 worker 未能启动时（例如拉不到镜像、缺少密钥），后台 run 会永久停在 `running`。现在会落到 `error` 终态，并在 `message` 里给出容器的停止原因。
- 云端 job 到达超时预算时的处置：正在停止中的任务不再被当作查不到而直接判超时，恰在预算点前运行结束的 job 也不会被误判为超时。
- 云端事件读取不再跳过短暂缺号的记录，判定明细不会因此少 step。
- 后台 run 收尾时先落判定明细再提交终态，run 的判定明细不会缺失。
- `gherkai status` 与后台推进进程并发读写运行状态文件时不再读到不完整内容（改为原子写入）。
- 后台 run 因超时被停止时，按该引擎的最短宽限等待 worker 退出，不再用极短宽限强制终止、导致云端浏览器会话泄漏。
- `gherkai deploy` 同时给出 `--diff` / `--synth-only` / `--bootstrap` 与 `push-worker` 等子命令时退 2，不再静默推送镜像。
- Midscene 引擎在 `--no-report` 下不再把引擎原生产物上传到 S3。
- `.feature` 路径指向目录、无读取权限或编码不对时退 2 并说明原因，不再打印调用栈。
- `--grace` 拒绝 `nan` / `inf` 这类取值（它们会让强制停止永不触发）。
- `@scope` 的名字里含 `#` 时，云端后台推进不再取错 run_id。
- 报告页与文本输出里，`skipped` / `aborted` 的原因会照原样显示。

## [1.4.0] - 2026-09-08

首个以发行包形式发布的版本；此前只能从仓库 checkout 运行。

### 新增

- 发行包：命令行工具 `gherkai`（PyPI）、本机 Nova Act worker `gherkai-worker-novaact`（随 `gherkai[local]` 装）、本机 Midscene worker `@gherkai/worker-midscene`（npm）、云端部署 provider `gherkai-deploy-aws`（随 `gherkai[deploy-aws]` 装）、库层 `gherkai-core` 与 `gherkai-runtime`；worker 基础镜像发布到 `ghcr.io/zhiyanliu/gherkai-worker-novaact` 与 `ghcr.io/zhiyanliu/gherkai-worker-midscene`。各包同号发布，`gherkai --version` 查看版本。
- `gherkai deploy` / `gherkai destroy`：一条命令建起或拆掉云端后端（运行状态表、产物桶、cluster、任务定义、Lambda 函数、VPC）。`--vpc` 三档（`default` / `new` / `vpc-<id>`）必给；`--diff` 只看变更集、`--synth-only` 只导出模板、`--bootstrap` 只做账户初始化；`--stop-timeout` 设 worker 容器的停止宽限。非交互场景用 `gherkai destroy --yes`。
- `gherkai deploy push-worker` / `list-workers`：把一套 `steps/` 构建成定制 worker 镜像、推成一个具名 variant，并查看各引擎当前的 variant、镜像 digest 与默认指针；提交时用 `--worker-variant` 选。
- 使用方自己的确定性 step 目录（`--steps-dir`，默认 `./steps` 存在即用）：本机 local 后端直接加载，云端 cloud 后端把它构建进定制 worker 镜像。
- 云端后台批量运行支持并发：`--max-concurrency` 在 cloud 后端同样生效，后端另有每个 run 最多 8 个 worker 的上限。

### 变化

- `--no-report` 改为真的不生成产物：不再注入报告落点，worker 也不生成、不上报产物。
- 命令行帮助、提示、警告、错误与 worker 日志改为直接说明发生了什么、怎么办，不再出现只有维护者能看懂的内部名称。

### 修复

- Nova Act worker 收到停止信号时可能因日志写入重入而崩溃，现已修正。

## [1.3.0] - 2026-08-17

发行重组之前的版本，没有独立发行包：只能从仓库 checkout 运行。
