# 变更记录

本文件按发行版记录 gherkai 对使用者可见的变化：新增的命令与选项、行为与默认值的调整、修复的问题，以及升级时需要执行的动作。每个发行版在这里都有一节，GitHub Release 的正文取自对应的一节。每个版本的 Release 页（1.4.0 起）见 [GitHub Releases](https://github.com/zhiyanliu/gherkai/releases)。

全部发行包同号发布：命令行工具、两个引擎 worker 与云端后端须装同一个版本。命令与选项的完整说明见[用户指南](./docs/user-guide/README.md)，环境变量总表见[配置](./docs/user-guide/configuration.md)。

格式沿用 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [Unreleased]

### 变化

- Midscene 引擎的默认模型改为 `us.openai.gpt-5.6-terra`（OpenAI GPT-5.6 Terra，经 Amazon Bedrock 调用）。在同一批用例上重复运行，它的判定稳定不抖动，并且比原默认模型 `qwen.qwen3-vl-235b-a22b` 快约三成、少用约四分之一 token；调用请求已按 Bedrock 对 GPT 系模型的要求调整。费用相应上升：一条 5 步左右的 scenario 约 5 美分，原默认模型约 2 美分（以你账户的 AWS 账单为准），量级与口径见[跑测试与看结果](./docs/user-guide/running-and-results.md)。该模型经 Bedrock 跨区推理调用，Midscene 的 AI step 模型调用在美国境内三个 region（us-east-1 / us-east-2 / us-west-2）处理；浏览器会话与产物仍在你选的 region，Nova Act 引擎不变。
- Nova Act 引擎的默认模型改为固定的 `nova-act-v1.0`，不再使用跟随最新 GA 版本的别名。同一条断言在不同模型版本上可能翻转，固定版本让结果可复现；换模型只随 gherkai 发版，并在本文件里点明。
- 两个引擎的模型都可用环境变量覆盖：Nova Act 侧 `NOVA_MODEL_ID`；Midscene 侧 `MIDSCENE_MODEL_ID`，模型家族一般由模型 id 自动识别，识别不出时 worker 启动即报错并要求补 `MIDSCENE_MODEL_FAMILY`。本机 local 后端在 shell 里设置即生效；云端 cloud 后端把变量写进定制 worker 镜像。
- `gherkai doctor` 新增一行，显示本机各引擎 worker 实际会用的模型（`--json` 里是 `engines` 段的 `model.<engine>`），在 shell 里设过覆盖变量的机器可以直接核对；云端 worker 的模型写在定制镜像里，不在这一行显示。
- 云端 worker 现在可以调用 Bedrock 上的模型与你账户里的跨区推理入口，不再限定单一模型：换模型只需改定制 worker 镜像里的环境变量，不必重新部署后端。
- 两个引擎的第三方依赖改为固定精确版本：Midscene 侧 `@midscene/web` 升到 1.12.8、Playwright 1.63.0，Nova Act 侧 `nova-act` 3.4.187.0。此前声明的是版本范围，不同时间安装的机器会取到不同版本。
- Midscene 引擎的 token 用量改用引擎 SDK 公开的累计计数，元素定位时的区域搜索调用也计入。同一条用例的报告用量会比此前略高，是统计范围更全，不是模型消耗变多。
- `gherkai deploy` 结束时改为逐行说明默认 worker 镜像 variant 与 worker 运行配置的更新结果，例如「已保留默认 worker 镜像 variant `base`」「各 variant 的 worker 运行配置已是最新」。
- 仓库首页新增「判定由谁做出」一节，列出两个引擎各自使用的模型与服务、版本策略、查看与更换方式，以及费用来源。
- 文档重组：面向使用者的完整说明集中到 [`docs/user-guide/`](./docs/user-guide/README.md)；各发行包在 PyPI / npm 上的页面改为入口页，只留定位、装法、最小用法与指向用户指南的链接；本文件是新增的变更记录。

### 修复

- Midscene 引擎每个 run 在日志里打出的一段 `Execution context was destroyed` 报错栈已消除（关闭了对云端浏览器无意义的一项 SDK 渲染开关）。
- 引擎无法回答能力查询时的提示改为先给出 worker 自己的报错原文，常见成因（版本不一致、模型配置不对）只在原文没有说明原因时补充。

### 升级须知

- 在本机 local 后端跑用例的机器上，把命令行工具与你的用例用到的引擎 worker 升到同一版本（`uv tool upgrade gherkai`；Midscene worker 另跑 `npm i -g @gherkai/worker-midscene@<CLI 版本>`），新的默认模型随 worker 一起升级；版本不一致会在跑前检查时退 2。安装形态见[开始使用](./docs/user-guide/getting-started.md)。
- 部署方须重新执行 `gherkai deploy`：新的默认模型在新版本的 worker 基底镜像里，放宽后的模型调用权限也随部署更新。有自定义 worker 镜像 variant 的团队，从新版本的基底镜像重新构建后用 `gherkai deploy push-worker` 推送一次。升级步骤见[云端后端](./docs/user-guide/cloud-backend.md)。
- 想继续用原来的 Midscene 模型：把 `MIDSCENE_MODEL_ID` 设为 `qwen.qwen3-vl-235b-a22b`（本机 local 后端设在 shell 里，云端 cloud 后端写进定制镜像的环境变量）。

## [1.4.3] - 2026-09-16

### 变化

- 停止 worker 的宽限秒数下限改由引擎 worker 自己报告：本机 local 后端不给 `--grace` 就按 run 里用到的各引擎报出的最短宽限取值，通常是分钟量级（只用 Midscene 引擎的 run 更短），给出小于该下限的值直接退 2。宽限过短会让正在进行的 AI 操作被强制杀掉、云端浏览器会话泄漏。
- `--backend cloud` 不再接受显式 `--grace`：云端 worker 的停止宽限由部署侧的 `gherkai deploy --stop-timeout` 决定，给了这个选项直接退 2，且不会产生任何云端调用。
- `gherkai doctor --backend cloud` 新增一行，把引擎 worker 报出的最短宽限与云端任务定义的停止宽限做比对；不足时提示可以调高部署侧的 `--stop-timeout`。
- 本机跑之前，命令行工具会先向用到的每个引擎 worker 查询一次它的能力与最短宽限。worker 与命令行工具版本不一致时，命令几秒内退 2 并提示升级该引擎的 worker，不再等到超时。
- `gherkai explain --scenario <SEL> --step N` 点名的那一步一律展开证据，通过的 step 也展开，不必再加 `--all`。
- `gherkai deploy` 少给 `--vpc` 时的提示改为直接说明三档各是什么；后端记着上次部署用的档时，提示里直接给出沿用它的写法。

### 升级须知

- 在本机 local 后端跑用例的机器上，命令行工具与你的用例用到的引擎 worker 要升到同一版本；版本不一致会在跑前检查时退 2（没用到的引擎不受影响）。

## [1.4.2] - 2026-09-16

### 新增

- `gherkai explain <run_id>`：读出失败那一步的证据——AI 的推理、当时页面截图的位置、断言票数与页面地址。`--scenario` / `--step` 收窄范围，`--all` 连通过的 step 也展开，`--full` 逐段全文，`--json` 输出机读结构。
- `gherkai doctor`：一条命令自检环境——引擎是否装好、`steps/` 能否加载；加 `--backend cloud --prefix <前缀>` 连带查 AWS 凭证、region 与云端后端。
- `gherkai skill install`：把驾驭 gherkai 的 agent 技能装进项目（或用户级）的 agent 目录，`--agent` 支持 `claude-code` / `codex` / `all`。技能随命令行工具一起发行。
- 筛选与机读选项补齐：`plan` / `run` / `submit` 支持 `--scenario`（按 `<文件>:<行号>`、行号或标题片段选）与 `--scope`（按 scope_id 精确选整个 scope）；查询类命令都有 `--json`；`--quiet` 不打逐事件进度，本机 worker 日志改落 `<report-dir>/<run_id>/worker.log` 并只打一行位置。
- 判定明细与报告里每个 step 带一行原因（`message`）：说明它为什么不是 `passed`，通过的 step 为 null。

### 变化

- AI step 的截图改为运行期后台上传：每步完成即入队上传，不必等 scope 收尾；收尾时最多等待固定时长让剩余上传完成，失败重试一次。run 被中途停止时，已跑完 step 的截图仍会上传到产物桶，但不会进判定明细——`gherkai explain` 会在该 job 上提示这一点。
- `gherkai status` 在 run 到达终态时打出报告与判定明细的位置；建议加 `--wait` 继续等到终态的提示只在所有 job 仍未开跑时出现。
- `explain` 的文本输出统一用机读字段名作前缀（`message:` / `thought:` / `screenshot:` / `error:`），与 `--json` 的字段一致。
- `@scope` 的取值与另一个未标 `@scope` 的 scenario 自动生成的 scope_id 相同时，`plan` / `run` / `submit` 直接报错并给出位置，不再让两个 scope 使用同一个 scope_id。
- Nova Act 引擎在你账户里自动创建的 workflow definition 改名为 `gherkai-worker`；无需手动迁移，云端按新名自动建出。

### 移除

- `gherkai submit` 去掉 `--events-table` 与 `--cluster`：这两个资源名一律按 `--prefix` 推导。
- `gherkai destroy` 去掉 `--allow-vpc-change` 与 `--require-approval`：这条命令从不使用它们，此前给了会被静默忽略，现在直接退 2。

### 修复

- 本机 local 后端的判定明细与报告文件改为原子写入，边跑边读不会读到写了一半的内容。
- `submit` 起了隧道、后台进程还没接管就失败时，隧道会被立即拆掉，不再残留。
- `explain` 在判定明细还没落地时的提示带上各后端定位 run 的选项。
- `gherkai skill install` 读到非 UTF-8 的目标文件时退 2 并说明真正的原因。

## [1.4.1] - 2026-09-10

### 变化

- 失败或超时的 AI step 同样报出它消耗的时间与用量，此前这部分统计整块丢失。
- 后台跑批的报告带上 run 级总时长。
- 被测界面的语言支持范围写进文档：Midscene 引擎不限语言（中文界面上的操作与 AI 断言与英文同级可靠）；Nova Act 引擎的支持范围是英文界面——它在中文页面上能操作、能判页面级语义，但「正文里是否出现某个中文词」这类断言会稳定判否。非英文应用请用 `@engine:midscene` 路由。
- worker 镜像 variant 解析失败时的提示补上第二条出路：先用 `--worker-variant base` 跑。
- 各发行包在 PyPI / npm 上的说明页改为面向使用者，开发相关内容移到仓库内。

### 修复

- 云端 worker 未能启动时（例如拉不到镜像、缺少密钥），后台 run 会永久停在 `running`。现在会落到 `error` 终态，并在 `message` 里给出容器的停止原因。
- 云端 job 到达超时预算时的处置：正在停止中的任务不再被当作查不到而直接判超时，恰在预算点前跑完的 job 也不会被误判为超时。
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

- 发行包：命令行工具 `gherkai`（PyPI）、本机 Nova Act worker `gherkai-worker-novaact`（随 `gherkai[local]` 装）、本机 Midscene worker `@gherkai/worker-midscene`（npm）、云端部署 provider `gherkai-deploy-aws`（随 `gherkai[deploy-aws]` 装）、库层 `gherkai-core` 与 `gherkai-runtime`；worker 基底镜像发布到 `ghcr.io/zhiyanliu/gherkai-worker-novaact` 与 `ghcr.io/zhiyanliu/gherkai-worker-midscene`。各包同号发布，`gherkai --version` 查看版本。
- `gherkai deploy` / `gherkai destroy`：一条命令建起或拆掉云端后端（运行状态表、产物桶、cluster、任务定义、Lambda 函数、VPC）。`--vpc` 三档（`default` / `new` / `vpc-<id>`）必给；`--diff` 只看变更集、`--synth-only` 只导出模板、`--bootstrap` 只做账户初始化；`--stop-timeout` 设 worker 容器的停止宽限。非交互场景用 `gherkai destroy --yes`。
- `gherkai deploy push-worker` / `list-workers`：把一套 `steps/` 构建成定制 worker 镜像、推成一个具名 variant，并查看各引擎当前的 variant、镜像 digest 与默认指针；提交时用 `--worker-variant` 选。
- 使用方自己的确定性 step 目录（`--steps-dir`，默认 `./steps` 存在即用）：本机 local 后端直接加载，云端 cloud 后端把它构建进定制 worker 镜像。
- 云端后台跑批支持并发：`--max-concurrency` 在 cloud 后端同样生效，后端另有每个 run 最多 8 个 worker 的上限。

### 变化

- `--no-report` 改为真的不生成产物：不再注入报告落点，worker 也不生成、不上报产物。
- 命令行帮助、提示、警告、错误与 worker 日志改为直接说明发生了什么、怎么办，不再出现只有维护者能看懂的内部名称。

### 修复

- Nova Act worker 收到停止信号时可能因日志写入重入而崩溃，现已修正。

## [1.3.0] - 2026-08-17

发行重组之前的版本，没有独立发行包：只能从仓库 checkout 运行。
