# gherkai

用 Gherkin 写 UI 自动化测试，让 AI 浏览器代理去跑。你写 `.feature`（自然语言步骤 + 断言），`gherkai` 把它解析成可并发的执行批次，派给你选的 AI 引擎（Midscene / Nova Act）在 AWS 云端浏览器里真实操作页面、判定断言，最后把每条用例的判定、日志与可点开的报告归集成一份结果。两种跑法：**在本机跑**（worker 起在你的机器上、结果落本地目录），或**整批跑在云端**（worker 跑 Fargate 容器、状态与报告落 DynamoDB/S3，提交完就能关掉终端）。

## 安装

```bash
uv tool install gherkai                     # CLI 本体（只提交云端 run 的人装这一条就够）
uv tool install 'gherkai[local]'            # 顺带装上在本机跑 Nova Act 引擎所需的 worker
npm i -g @gherkai/worker-midscene           # 在本机跑 Midscene 引擎的 worker（Node ≥ 22）
uv tool install 'gherkai[deploy-aws]'       # 部署方：要用 gherkai deploy 建/改云端后端（另需 Node ≥ 22 + 容器引擎）
uvx gherkai --version                       # 或者不安装、临时跑一次
pipx install --fetch-python missing gherkai   # 不用 uv 的人：pipx 回落（pipx 默认不下载解释器，本项目要 Python ≥ 3.13；装 extra 写 'gherkai[local]'）
```

需要 Python ≥ 3.13。两个引擎的 worker 是各自独立的程序：Nova Act 走上面的 `[local]` extra，Midscene 是 Node 包走 npm；只用 `--backend cloud` 提交的人两个都不用装（worker 跑在云端）。`gherkai list-engines` 会告诉你当前哪个引擎可用、缺的那个怎么装。

## 前置（AWS）

- AWS 凭证（默认 profile 即可）与 region（`--region`，或 `AWS_REGION` / `AWS_DEFAULT_REGION` / profile 配置），当前验证过的 region 是 `us-east-1`。
- 账号需开通：Bedrock 模型访问（Midscene 用 `qwen.qwen3-vl-235b-a22b`）、AgentCore Browser（`bedrock-agentcore`）、Nova Act（`nova-act` + 模型 `nova-act-latest`）。
- `--backend cloud` 还需要有人先跑过 `gherkai deploy` 把云端后端建好（见下「部署」）；只有用 `--expose-local` 测本机应用时才需要 [ngrok](https://ngrok.com/download) authtoken（免费账号即够，`ngrok config add-authtoken <token>` 或环境变量 `NGROK_AUTHTOKEN`）。

## 上手

```bash
gherkai plan features/checkout.feature                  # 预检：看分组、校验写法与配置，不连云、不花钱
gherkai run  features/checkout.feature                  # 前台真跑（会产生模型调用与浏览器会话费用）
RUN_ID=$(gherkai submit features/*.feature --max-concurrency 2)   # 提交完就走
gherkai status "$RUN_ID" --wait --json                  # 事后轮询到跑完，输出机器可读结果
```

`plan` 不花钱，`run` 每次都花真钱——**先 plan 后 run** 能提前暴露写法冲突、把钱省在真跑之前。`plan` 还会逐步骤标注派发预期（哪些步骤会命中你写的确定性步骤、哪些交给 AI 判定）。

两个旋钮决定一次 run 长什么样：**跑在哪 / 落在哪** 由 `--backend` 定（`local` = worker 跑本机、结果落 `--report-dir`；`cloud` = worker 跑 Fargate 容器、状态落 DynamoDB、判定与报告落 S3）；**用哪个引擎** 在 feature 里逐 scope 标 `@engine:midscene` / `@engine:novaact`，没标的用 `--default-engine`（默认 `novaact`，标了 tag 的不受它影响）。

## 命令

| 命令 | 做什么 |
|---|---|
| `gherkai plan <feature...>` | 预检：分组、校验、逐步骤标注派发预期。不连云、不花钱 |
| `gherkai run <feature...>` | 前台跑完这批：CLI 全程在线，跑完直接给判定与报告 |
| `gherkai submit <feature...>` | 提交完就走：打印一个 `run_id` 后立即退出，后台继续推进 |
| `gherkai status <run_id>` | 查这个 run 的进度/结果；`--wait` 轮询到跑完再返回；到终态时同时打出报告与判定明细的位置（本机路径或 S3） |
| `gherkai list-engines` | 列出可用引擎（缺的那个原地给安装命令） |
| `gherkai list-deterministic --engine <名>` | 列出该引擎支持的确定性步骤（含你自己写的），写 feature 时查着复用 |
| `gherkai deploy` / `gherkai destroy` | 建/改/拆云端后端。只有部署方需要，见下 |

`run` 要求 CLI 全程在线（网断、关机即中止）。`submit` 把「提交」和「收结果」拆开：local 档在本机起一个脱离 CLI 的后台进程推进，cloud 档交给云端推进（提交完真关机也能跑完）。`status --wait` 既是查询也是接力——后台进程崩了或卡住，来查的这条命令会把它续到底。

`status` 的 `--backend` / `--report-dir` / `--prefix`（cloud）必须与 `submit` 时一致，否则查不到这个 run（`--report-dir` 在 cloud 档是后端的报告前缀，默认 `reports`，同样用来拼终态时打出的 S3 位置）。

## `steps/` 目录：你自己的确定性步骤

URL、DOM 这类不容 AI 抖动的检查，可以由你自己写成确定性步骤：在项目里建一个 `steps/` 目录，Nova Act 引擎放 `.py`、Midscene 引擎放 `.mts`（或 `.mjs`），命中的步骤走你的精确实现、不进 AI 判定。目录按 `--steps-dir` > 环境变量 `GHERKAI_STEPS_DIR` > `./steps` 解析。

目录里**任何一个文件加载失败就整批拒跑**（`plan` / `run` / `submit` 都在起第一个 job 之前拒，并转述具体错误），显式给的 `--steps-dir` 不存在也直接退 `2`——静默跳过等于把这些步骤悄悄换回 AI 判定。`--backend cloud` 下这个 flag 不生效（只警告、不拦）：云端 worker 的步骤是烙进镜像的，见下。

## 云端跑哪套步骤：worker 镜像 variant

一个 **variant** = 一套具名的确定性步骤集 = 一个定制 worker 镜像（名字自取，如 `base` / `login` / `checkout-v2`；须合镜像 tag 字符集——字母/数字/下划线开头，其后可含 `.` `-`——不合法在开跑前就报错）。提交时用 `--worker-variant <名>` 选，不给就用后端的默认指针（部署时初始化为 `base` = 零步骤的基底）。提交侧会把这个名字定成本次 run 用的确切镜像，所以 run 期间别人重推同名 variant 不影响正在跑的 run；多人共用一个后端时各推各的、互不覆盖。某个引擎缺这个 variant 会直接退 `2` 并给出修复命令，**不会悄悄回落到默认**（那等于替你换掉一套步骤集）。镜像怎么 build 和推送见 [部署方页面](https://github.com/zhiyanliu/gherkai/blob/HEAD/deploy_aws/README.md)。

## 常用选项（`run` / `submit`）

| flag | 默认 | 说明 |
|---|---|---|
| `--default-engine {novaact,midscene}` | `novaact` | 未标 `@engine` 的 scope 用哪个引擎 |
| `--max-concurrency N` | `1` | 同时在跑的 worker 上限（护成本与配额），须 ≥ 1。云端还受部署侧上限钳制，超出时按上限并行并提示 |
| `--default-job-timeout S` | `300` | 单个 job 的墙钟预算秒（`<=0` 表示不超时）；用例上标 `@timeout:<秒>` 可逐 scope 覆盖。超预算的 job 会被停掉并判 error，本机挂死与云端计费失控都靠它止损 |
| `--assertion-votes N` | `1` | AI 断言跑 N 次取多数票（如 3/5），治判定抖动 |
| `--grace S` | 自动 | 仅 `run`。中止时留给 worker 关闭云端浏览器会话的秒数，不填按引擎自动取（novaact ≈150s、midscene ≈25s）。**给得太小会漏关会话、继续计费**，过小的值在开跑前就报错。云端 `submit` 的对应旋钮在部署侧：`gherkai deploy --stop-timeout` |
| `--steps-dir DIR` | `./steps` | 你自己的确定性步骤目录（见上） |
| `--report-dir DIR` / `--no-report` | `reports` / 关 | 报告落点（每次 run 落 `DIR/<run_id>/`，`status` 查同一个 run 要给同一路径；云端有自己的产物前缀，给了不一致的值会在提交前退 `2` 并点名两侧的值）／一点都不落盘：不归集报告，也不生成引擎自己的报告产物（仅 `run`；Nova Act 的 SDK 轨迹关不掉，它会写进自己的临时目录、不上报） |
| `--expose-local ORIGIN` | — | 把「本机可达」的被测应用经隧道暴露给云端浏览器，值 = feature 里书写的原始地址（如 `http://localhost:3000`）。框架会替换成一次性公网地址（带每 run 一换的用户名口令，跑完即拆）。页面资源全经隧道，ngrok 免费层配额约 1GB/月 + 2 万请求/月，重度使用可能碰顶（表现为 429 或断流）。**用它时本机要保持开机联网到 run 结束**，否则应用不可达、用例会以导航失败告终。云端 `submit` 时隧道另有一个兜底存活时间 `--tunnel-ttl S`（默认按这批用例的预算算，**调小有风险**：到点无条件拆隧道，短于实际时长会让剩下的用例跑成导航失败） |
| `--fail-fast` / `--json` / `--quiet` | 关 | 任一 job 崩就中止整批／只输出机器可读 JSON／不打逐步进度（都仅 `run`；`submit` 只打 `run_id`，进度看 `status`） |
| `--region` / `--profile` | — | AWS region / profile（两种 backend 都用，也喂给 worker） |

**云端专用**（`--backend cloud`）：`--prefix`（默认 `gherkai-`，须与部署时一致；环境变量 `AWS_RESOURCE_PREFIX`）一把决定表/桶/集群等资源名；要单独覆盖就用 `--ddb-table`（`AWS_DDB_TABLE`）/ `--s3-bucket`（`AWS_S3_BUCKET`）/ `--events-table` / `--cluster`；`--worker-variant` 见上；`run` 还可用 `--subnet` / `--security-group` 覆盖网络（不给则读部署时写下的值）。

## 输出与报告

stdout 只放该命令的核心产出（`--json` 的 JSON、人看的文本汇总、列表），进度与诊断全走 stderr——所以 `gherkai run … --json > r.json` 拿到的是纯净 JSON，进度仍在终端可见。每次 `run` 默认在 `reports/<run_id>/` 留一份报告：`index.html` 是可点开的入口（判定明细 + 每个引擎自己的报告产物各一行链接），`manifest.json` 是给 CI/工具消费的清单。

## 退出码

| 码 | 含义 |
|---|---|
| `0` | 成功：`run` 全部通过 / `plan` 这批可跑 / `submit` 已提交 / `status` 查到了（未跑完时只表示查询成功） |
| `1` | 跑完了但有用例失败或出错（断言没过、引擎异常）；云端跑到一半存储不可达也算这一档 |
| `2` | 没跑起来：feature 读不到、写法或参数不合法、引擎 worker 没装、`steps/` 里有文件加载失败、`--steps-dir` 指的目录不存在；云端还包括凭证/region 缺失、`--prefix` 对应的资源不存在或无权限、版本与后端不匹配、请求的 worker variant 没推过 |

分界线是「有没有真的开跑」：开跑前的配置与可达性问题退 `2`，跑到一半的故障退 `1`。`submit` 与 `status` 各答不同的问题——`submit` 的退出码只说「提交成功了吗」（判定此刻还没出），`status` 的退出码只在读到终态时才表判定（通过 `0` / 其余终态 `1` / 查不到这个 run `2`）；CI 想拿 `run` 那样的 0/1 判定码，用 `status --wait`。

## CLI 要和后端同版本

部署时后端记下自己的版本，`--backend cloud` 的每条命令在动任何资源之前先比对：

- **CLI 比后端新 → 直接拒绝（退 `2`），没有强行放行的开关。** 两条出路：① 部署方跑 `gherkai deploy` 把后端升上来；② 用与后端同版本的 CLI 临时跑，不动本机安装：`uvx --from 'gherkai==<后端版本>' gherkai …`。
- CLI 比后端旧 → 只警告不拦，`uv tool upgrade gherkai` 跟上即可。升级就是三步：① 部署方 `uv tool upgrade gherkai`（安装时带的 extras 会沿用）；② 立刻 `gherkai deploy`；③ 其他人再升自己的 CLI（中间窗口里提交会被拒，这是预期）。

## 部署（只有部署方需要）

云端那套后端（DynamoDB 表、S3 桶、ECS 集群与任务定义、推进用的 Lambda、VPC 与安全组）由 `gherkai deploy` 建。它装在单独的 extra 里，团队里只提交 run 的人不必装：

```bash
uv tool install 'gherkai[deploy-aws]'                       # 另需 Node ≥ 22 在 PATH
gherkai deploy --bootstrap                                  # 每个账户 + region 一次性初始化
gherkai deploy --diff --vpc default --prefix gherkai-       # 先看清这次会改什么（不改账户）
gherkai deploy --vpc default --prefix gherkai-              # 真部署
gherkai deploy --synth-only ./out --vpc default             # 只导模板给自己的审批流水线，不让本工具碰账户
gherkai destroy --vpc default --prefix gherkai- --yes       # 拆掉（表/桶/镜像仓库保留、不随之删；--yes 是给脚本/非交互用的）
```

- `--vpc` 必给、**没有隐式默认**（只有 `--bootstrap` 不需要，那是账户级动作）：`default`（账户默认 VPC）/ `new`（本次新建，2 个可用区、零 NAT）/ `vpc-<id>`（复用现有）。**这是真踩过的坑**：漏掉它会合成出「新建整套 VPC + 换掉 worker 安全组」这种危险变更。生效的档记在后端，第二次敲错档会被拒（退 `2`）；确认这确实是你要的网络变更后加 `--allow-vpc-change` 放行一次（本机制之前部署的环境第一次也需要它，先 `--diff` 核对）。
- `--prefix`（默认 `gherkai-`）是全部云资源的命名空间，**须与 `run`/`submit`/`status` 的 `--prefix` 一致**；换 prefix 就是换一套独立环境（`prod-` / `stage-`），闲置成本近零。
- 其他 flag：`--require-approval never|any-change|broadening`（权限变更要不要人过目）、`--stop-timeout`（容器关闭宽限秒，标定 `--grace` 用）、`--refresh-context`（丢弃本机缓存的网络查询结果重查）、`--region` / `--profile`。`--diff` / `--synth-only DIR` / `--bootstrap` 三者互斥，都不给就是真部署。
- worker 镜像的推送与管理（`gherkai deploy push-worker` / `list-workers`）、资源清单与费用见 [部署方页面](https://github.com/zhiyanliu/gherkai/blob/HEAD/deploy_aws/README.md)。

## 遇到问题

`gherkai --help` / `gherkai <命令> --help` 有全部选项，报错都带「怎么办」。项目主页 https://github.com/zhiyanliu/gherkai#readme ，问题反馈 https://github.com/zhiyanliu/gherkai/issues 。

设计文档（架构决策记录）见 https://github.com/zhiyanliu/gherkai/tree/HEAD/docs/adr
