# cli — 执行核心库的命令行皮（argparse + render）

发行名 `gherkai` / import 名 `gherkai_cli` / 命令 `gherkai`（ADR 0037 决策 2a「三名分离」）。

`core/` 是纯库（零引擎依赖、不碰文件系统）。**cli 是它的第一张皮**：解析参数 → 经产品本体
`gherkai_runtime.compose` 读 `.feature`、装配引擎与 Store adapter 注入给 core → 把 `RunResult` 渲染给人或 CI 看。
WebUI 将来是另一张皮，**直接调 core、复用产品本体 `gherkai_runtime`（compose 等组合根逻辑所在的平级包 `runtime/`，ADR 0016「演进」节）**，不经本 cli。

设计见 [ADR 0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)（执行架构 / 组合根注入）；
无状态跑批（`submit`/`status` 的「提交完就走 → 事件驱动推进 → 轮询收集」）见 [ADR 0034](../docs/adr/0034-detached-batch-reconciler.md)。

## 模块

```
cli/gherkai_cli/
├── __main__.py   ← argparse 皮：run/submit/status/plan/list-engines/list-deterministic/deploy/destroy 解析 → 调 gherkai_runtime.compose/gherkai_core → 注入 RunPersistence 实时落库 → 调 render；定义退出码
├── deploy.py     ← deploy/destroy 的命令面 + 部署 provider 发现（entry point group `gherkai.deploy`）；**零 IaC 知识**、不 import aws_cdk（ADR 0037 决策 6）
└── render.py     ← 表层渲染：0024 事件 → 进度行；RunResult → 文本汇总 / JSON；RunState → status 视图
```

组合根逻辑（compose/detached/names/tunnel/tunnel_host）住在平级的产品本体包 `runtime/gherkai_runtime/`（曾在本包内、被 Lambda/iac 的真实代价逼出抽包，ADR 0016「演进」节）：那是任何前端都要的接线，
后者只是 argparse + 标准 IO。

**实时落库**：`run` 不是「跑完才一次性落盘」——`__main__` 注入 core 的 `RunPersistence`
（组合根注入三个 Store adapter），run 开始即写 definition + 初始全 pending 态，每个 scope 起跑刷
RUNNING、完成即落该 scope 判定真值，最后 `finalize` 写总状态（commit point）。`--no-report` 时跳过整条落库
（裸跑、零落盘逃生舱）。

落哪由 `--backend` 定：默认 `local`（文件落 `--report-dir`）；`--backend cloud` 让组合根改注入 DynamoDB/S3
adapter、复用同一条 `RunPersistence`，把状态落 DynamoDB、判定真值与报告落 S3（表/桶需预先建好——由 `gherkai deploy` 供给，见下『部署』节）。见下『选项』表与『跑』小节。未来 WebUI 复用同一套 `gherkai_runtime.compose` 装配，cli 这张皮的接线不变。

## 跑（会烧真 AWS 钱：模型调用 + AgentCore 会话）

下面都从**仓库根**键入（feature 路径相对当前目录解析）：

```bash
uv sync                                            # 一次装齐五个 workspace 成员：core/runtime/cli/engines/novaact/deploy_aws（editable，单一根 uv.lock）

# 跑一个 feature（默认引擎 novaact，默认 max-concurrency=1）
uv run gherkai run features/wikipedia_generic.feature

# 未标 @engine 的 scope 默认走 Midscene 引擎、放开并发、JSON 输出
uv run gherkai run features/wikipedia_generic.feature \
  --default-engine midscene --max-concurrency 2 --json

# 预检 .feature（不烧钱）：看 scope/job 分组、校验配置（@scope/@engine 冲突等），不真跑。
# 每个 step 还标注派发预期（← 确定性: … / 默认 AI 不标；worker 自述命中，ADR 0036——
# 起本地瞬时 worker 子进程做 match 查询，零 AWS 零花费；引擎环境未装则自动降级为无标注）
uv run gherkai plan features/wikipedia_generic.feature
uv run gherkai plan features/*.feature --json     # 机器可读分组

# 列可用引擎、它们的 spawn 命令与命中的定位链级别（不烧钱；某引擎未装则原地打安装指引，ADR 0037 决策 3）
uv run gherkai list-engines

# 列指定引擎支持的确定性 step（worker 注册表自述，写 feature 时查询复用；不烧钱，ADR 0036）
uv run gherkai list-deterministic --engine midscene      # --json 可选；默认 --engine novaact
# 清单/标注都含**你自己的** step：自述入口同样加载 steps 目录（默认 ./steps，或 --steps-dir 指定）
uv run gherkai list-deterministic --steps-dir ./my-steps

# 云端落库：状态 → DynamoDB、判定结果与报告 → S3（表/桶由 `gherkai deploy` 供给；boto3 随 CLI 一起装，无额外步骤）
uv run gherkai run features/wikipedia_generic.feature \
  --backend cloud --ddb-table ui-test-runs --s3-bucket ui-test-artifacts-<你的后缀>
# 兜底：也可用 AWS_DDB_TABLE / AWS_S3_BUCKET 环境变量代替这两个 flag
# 凭证/region 走 boto3 默认链；可加 --profile / --region 覆盖
```

> 一次性建表/建桶命令（`aws dynamodb create-table` / `aws s3 mb`，分区键 run_id + 排序键 item_type、按量计费）见
> [`core/tests/README.md`](../core/tests/README.md) 的「一次性：建真表 + 真桶」一节——cli 云端后端与集成测试用同一套表/桶 schema。

**先 `plan` 后 `run`**：`run` 每次真烧 AWS 钱，`plan` 是纯本地预检——验证 feature 写法、确认
scope/job 分组与 engine 路由符合预期、提前暴露 `PlanError`（uri 冲突 / 同 scope 多 engine 等），
都不连云、不花钱。退出码 0=可跑 / 2=配置错。

> 文本模式对 DataTable/DocString 多行参数只标注尺寸（`+dataTable(行×列)` / `+docString(N 行)`）保持紧凑；
> 要核对参数**完整内容**用 `--json`（携带 content/rows 全文）。

未标 `@engine` 的 scope 用 `--default-engine` 指定的默认引擎；标了 `@engine:` 的按 tag 走、不受此 flag 影响。

## 无状态跑批：submit（提交完就走）+ status（轮询/接力收集）

`run` 是同步阻塞（起 worker → 守着推进 → 跑完才退，CLI 全程在线）。`submit`/`status` 把这条拆成两截
（提交完就走 → 事件驱动推进 → 事后轮询收集），CLI 不必守着：见 [ADR 0034](../docs/adr/0034-detached-batch-reconciler.md)。

```bash
# ── local：submit 立即返回 run_id（后台 per-run 进程推进），事后再来收 ──
RUN_ID=$(uv run gherkai submit features/wikipedia_generic.feature --max-concurrency 2)
# submit 提交完就走：本机 fork 一个脱离 CLI 的 per-run 进程跑推进循环，CLI 打完 run_id 即退

uv run gherkai status "$RUN_ID"                # 查一次进度/结果（只读，不推进）
uv run gherkai status "$RUN_ID" --wait         # 轮询到终态才返回（per-run 进程崩了/慢了，本命令接力推进到底）
uv run gherkai status "$RUN_ID" --wait --json  # 同上，输出机器可读 RunState

# ── cloud：submit 只把 definition 落 DDB，之后云端 Lambda 链推进（提交完真关机也跑完）──
RUN_ID=$(uv run gherkai submit features/wikipedia_generic.feature --backend cloud --prefix gherkai-)
uv run gherkai status "$RUN_ID" --backend cloud --prefix gherkai- --wait
# cloud --wait 检测到卡住（连续几轮状态不变）才 invoke kicker Lambda 踢一脚接力，正常推进时不打扰
```

**为何拆**：`run` 要求 CLI 全程在线（网断/关机即中止）；`submit` 提交完就走——local 由脱离 CLI 的 per-run 进程推进、
cloud 由云端 Lambda 事件驱动链推进（submit 机器无 ECS 写/执行权限——仅 preflight 的只读探活，可立即关机）。`status` 事后查/收集：`--wait` 是三个推进触发源
之一（人来查即接力），保证「推进即使中断、也能被查询者续到底」（ADR 0034）。`status` 须与 `submit` 用同一组定位参数——
见下『选项（`status`）』表引言。

## 部署（`gherkai deploy`）——只有部署方需要

云端那套后端（DynamoDB 两表 / S3 桶 / ECS cluster + task-def / 无状态跑批的 Lambda 链 / VPC 与安全组）由
`gherkai deploy` 供给。**IaC 装在一个独立的 provider 包里**，经 extra 隔离——只有**部署方**装它，
团队里只提交 run 的人不必背 CDK 与 Node：

```bash
uv tool install 'gherkai[deploy-aws]'    # 部署方（或开发树里 uv sync 即已带）
uv tool install gherkai                  # 只提交 run 的人：裸装即可 --backend cloud
```

**前置：Node ≥ 22 在 PATH**（与 worker 的 `engines.node` 同一下限）。Python 版 CDK 是 jsii 绑定、import 即起
node 子进程，cdk CLI 本身也是 npm 物；PATH 上有 `cdk` 就用它，没有则 `npx -y aws-cdk@2` 兜底。

```bash
# 首次：账户+region 初始化一次（未初始化就 deploy，报错会指回这里）
uv run gherkai deploy --bootstrap                                # 账户级、不合成 stack，不需要 --vpc

# 看清这次会改什么（尤其网络/IAM）——不改账户
uv run gherkai deploy --diff --vpc default --prefix gherkai-

# 真部署（IAM 变更要人过目就加 --require-approval broadening）
uv run gherkai deploy --vpc default --prefix gherkai-

# 逃生舱：只导模板给自己的审批/发布流水线，不让本工具碰账户
uv run gherkai deploy --synth-only ./out --vpc default

# 拆掉（表/桶/ECR 是 RETAIN、不随之删，见 ADR 0033）
uv run gherkai destroy --vpc default --prefix gherkai-   # 非交互/脚本加 --yes（cdk 在无 TTY 时拒绝无确认销毁）
```

`--diff` / `--synth-only DIR` / `--bootstrap` 三者互斥，都不给 = 真部署。命令面还有 `--require-approval MODE`
（透传 provider 的权限变更审批档）与下面的 `--allow-vpc-change`。装了多个 provider（当前只有 aws 一个）时
`--provider <名>` 必给；装一个时不必给；一个都没装则报「装 `gherkai[deploy-aws]`」并退 `2`。

### 三个旋钮

| flag | 默认 | 说明 |
|---|---|---|
| `--prefix` | `gherkai-` | 全部云资源的命名空间。**须与 `run`/`submit` 的 `--prefix` 一致**；换 prefix 就是换一套独立环境（prod-/stage-），闲置成本近零 |
| `--vpc` | **必给、无隐式默认**（`--bootstrap` 除外） | VPC 来源三档：`default`（账户默认 VPC）/ `new`（本 stack 新建，2-AZ 零 NAT）/ `vpc-<id>`（复用现有 VPC） |
| `--stop-timeout` | provider 默认 | worker container 的 SIGTERM→SIGKILL 宽限秒（标定 `run --grace` 用） |
| `--refresh-context` | 关 | 丢弃本机缓存的 CDK 环境查询结果（VPC/子网/AZ）重新查询；默认复用缓存（见 `deploy_aws/README.md`） |

`--vpc` **不给隐式默认是有意的**：漏了它会合成「新建整套 VPC + 替换 WorkerSg」这种危险变更集——真踩过的坑。

### VPC 档比对（三态）

只强制显式给值挡不住「第二次 deploy 敲错档」，所以生效的档会记在后端。deploy 前比对：

| 情形 | 行为 |
|---|---|
| stack 不存在（真首次部署） | 放行 |
| 后端没有记录、但 stack 已存在（本机制之前部署的环境） | 退 `2`——先 `--diff` 核对变更集，再带 `--allow-vpc-change` 放行一次 |
| 有记录且与 `--vpc` 一致 | 放行 |
| 有记录但与 `--vpc` 不一致 | 退 `2`（确认这确实是你要的网络变更后，用 `--allow-vpc-change` 放行） |

### 版本 skew：CLI 与后端必须同版本

deploy 会把自己的版本写成后端的版本戳，`run`/`submit`/`status --backend cloud` 在**任何资源预检之前**先比它
（先比版本是有意的：skew 的修复动作正好也把资源补齐，先报「表不存在」只会让人白查一圈 `--prefix`）：

| 比对结果 | 行为 |
|---|---|
| 同版本 | 放行、不打扰 |
| **CLI 新于后端** | 退 `2`，**没有放行 flag**。两条出路：① 部署方 `gherkai deploy` 把后端升上来；② 临时用与后端同版本的 CLI、不动本机安装：`uvx --from 'gherkai==<后端版本>' gherkai …` |
| CLI 旧于后端 | 警告不拦（`uv tool upgrade gherkai` 跟上） |
| 后端没有版本戳（早于本机制的部署） | 警告不拦 + 提示部署方跑一次 `gherkai deploy` 写入 |
| 任一侧是开发版（含 `.dev`/`.post`/`+`） | 跳过比对、警告一句（dev 版逐提交前进，逐字比会把每次都判成 skew） |

**不设放行口是刻意的**：放行等于让新 CLI 写的任务定义进旧后端读，后果不可知且静默；用 `uvx` 按版本临时跑
零成本。**升级即三步**（版本是一个旋钮，`gherkai` 与后端被 `==` 钉在同版本，没有「先升后端再升 CLI」这种次序）：
① `uv tool upgrade 'gherkai[deploy-aws]'`；② 立刻 `gherkai deploy`（中间窗口里提交侧会退 `2`，这是预期）；
③ 非部署者等这两步做完再升自己的 CLI。

设计与取舍（为什么 IaC 进 wheel、为什么 provider 中立、为什么没有放行口）见
[ADR 0037](../docs/adr/0037-distribution-and-packaging.md) 决策 6/7；资源清单与命名契约见
[ADR 0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)。

## worker 镜像 variant：云端跑哪套确定性 step 集

local 档的确定性 step 就在你机器上（`--steps-dir`）；cloud 档的 worker 跑在 Fargate 容器里，**step 烙在镜像里**。
一个 **variant** = 一套具名的 step 集 = 一个定制镜像（名字自取：`base`/`login`/`checkout-v2`），提交时用
`--worker-variant <名>` 选；不给就用**部署级的默认指针**（`gherkai deploy` 初始化为 `base` = 零 step 的基底）。
多人共用一个后端时各推各的 variant、互不覆盖。

```bash
uv run gherkai run    features/x.feature --backend cloud --worker-variant login
uv run gherkai submit features/x.feature --backend cloud --worker-variant login   # 缺省 = 默认指针
```

提交侧 preflight 会把这个名字解析成**本 run 用到的每个引擎**的精确 task-def revision，写进这个 run 的
definition——所以一个 run 内镜像固定（期间别人重推同名 variant 不影响在跑的 run），并在放行时每引擎打一行
`<engine>: variant … · digest … · revision …`（`--quiet` 静音）。**次序是刻意的：版本 skew → 资源存在性 →
variant 解析**（skew 的修复动作 `gherkai deploy` 本身就是重推镜像的前置，反过来先报「variant 没推」会让人白推一轮）。
某引擎缺该 variant 就退 `2` 并给出修复命令，**不静默回落到默认**（那等于替你换掉一套 step 集）。

**镜像的 build 与推送不在这张皮里**：build 是你自己的容器活（三行 Dockerfile 模板），推送与注册归部署方
（`gherkai deploy push-worker`）——见 [`deploy_aws/README.md`](../deploy_aws/README.md)，设计与被拒方案见
[ADR 0038](../docs/adr/0038-worker-image-delivery.md)。

## 退出码

- `0` —— RunResult 总状态 passed
- `1` —— 跑完了但有 failed/error（断言没过 / 引擎异常）；`--backend cloud` 下若 run 已开跑、中途 DynamoDB/S3 不可达（如桶被删）也退 `1`
- `2` —— 没跑成：feature 读不到、plan 配置矛盾（PlanError）、参数非法（如 `--assertion-votes < 1`）、或无子命令；**本 run 用到的引擎的 worker 运行时定位不到**（四级定位链全 miss，报错自带该引擎的安装命令，ADR 0037 决策 3）、或 **`steps/` 目录里有文件加载失败**（worker 自述入口非零退出，CLI 转述其诊断；`plan`/`run`/`submit` 一律在起任何 job 前拒，ADR 0037 决策 4——`submit` 同样在提交前拒，不会让你「提交成功」后每个 job 都 error）；`--steps-dir` / env `GHERKAI_STEPS_DIR` 指的目录不存在；`--backend cloud` 还没开跑就被拒（缺 boto3、**版本 skew 判 block**（CLI 新于后端，无放行口，见上『部署』节）、`--prefix` 拼出的表/桶/cluster/task-def 不存在·无权限·凭证/region 缺——运行前 preflight 点名 prefix fail-fast、或 **worker 镜像 variant 解析不了**（请求的 variant 在本 run 某个引擎上没推过 / 后端没有默认指针 / 解析到的 revision 已退休或镜像被删 / `--worker-variant` 名字不合镜像 tag 字符集——见上『worker 镜像 variant』节，**不回落默认**））；`deploy`/`destroy` 的没有可用部署 provider（没装 `gherkai[deploy-aws]` / 装了但加载失败）、或 **VPC 档与后端记录不符**（见上『部署』节）

> cloud 失败分层的切分线 = run 是否已真正开跑：起 worker 前的配置/可达问题退 `2`，跑到一半的云端故障退 `1`。

### submit / status 的退出码分层（无状态跑批，ADR 0034）

`submit` 与 `status` 各自的退出码衡量的是**不同的事**——`run` 一条命令里揉在一起的「提交 + 判定」被拆开了：

- **`submit`：退出码 = 提交成功与否，不是 run 的判定。**
  - `0` —— 已成功提交（local：per-run 进程已 fork、run_id 已打印；cloud：definition 已落 DDB，云端链接管）。
  - `2` —— 没提交成：feature 读不到 / plan 配置矛盾（同 `run`）；cloud 还缺 boto3、或 preflight 不过（表/桶/cluster/本 run 用到引擎的 task-def/事件驱动链三 Lambda——链上任一 Lambda 缺则提交会成功但 run 永不推进，故挡在提交前；**worker 镜像 variant 解析不了**同理挡在提交前——definition 里没有 revision 云端推进器就起不了 task）、或 `create_run` 时云端不可达。
  - 判定结果（PASSED / FAILED / …）**此刻还没出**，要用 `status` 去查。
- **`status`：查询本身成功即 `0`；判定退出码只在读到终态时给出。**
  - `0` —— run 达终态 `PASSED`；**或**未达终态（`pending`/`running`）时的一次查询（查到了就算成功，非 `--wait` 不评判）。
  - `1` —— run 达终态但非 `PASSED`（`failed`/`error`/`skipped`/`aborted`）。配 `--wait` 时即「轮询到终态后按判定给退出码」——CI 想拿 `run` 那样的 0/1 判定码，用 `status --wait`。
  - `2` —— 查不到该 run（`--report-dir`/`--prefix`/`--ddb-table` 与 `submit` 不一致？）；cloud 读 DDB 时云端不可达；`--wait` 接力要 invoke 的 kicker Lambda 不存在（prefix 配错/后端未部署——接力对象缺失，死等无意义、点名 prefix 退出）。

> 一句话：`submit` 退出码答「提交成功了吗」，`status --wait` 退出码答「这个 run 判定过没过」（PASSED→`0` / 其余终态→`1`）——`run` 的 0/1 判定语义在拆分后落到了 `status --wait` 上。

## 输出：stdout = 数据 / stderr = 进度

遵循 Unix 惯例：**stdout 只放该命令的核心产出**（`--json` 的 JSON 文档 / 人看的文本汇总 / `list-engines` 列表），**stderr 放所有进度诊断**（plan、逐事件、run_id、RunReport 落点、worker 透传日志）。故：

- `gherkai run … --json > r.json` —— `r.json` 是纯净 JSON（进度仍在终端可见、不污染文件）
- `gherkai run … > summary.txt` —— `summary.txt` 是纯净文本汇总

## 选项（`run`）

| flag | 默认 | 说明 |
|---|---|---|
| `features...` | — | 一个或多个 `.feature` 路径（位置参数） |
| `--default-engine` | `novaact` | 未标 `@engine` 的 scope 用的默认引擎（标了 `@engine:` 的按 tag 走） |
| `--assertion-votes` | `1` | AI 断言（`Then`）投票次数（默认 1=单次判定）；调高（如 3/5）启用抖动检测：跑 N 次取多数票。须 ≥1 |
| `--max-concurrency` | `1` | 同时在跑的 worker 上限（护真实成本/配额）。须 ≥1（`<=0` 会让 run 永远起不了 job、卡死在 pending，开跑前报错） |
| `--default-job-timeout` | `300` | job 墙钟超时秒的缺省值（`<=0` 不超时）。两层声明：标了 `@timeout:N` tag 的 scope 按 tag 走（同 scope 声明不一致 → `PlanError`）、未标的用本缺省——同 `@engine`/`--default-engine` 模式。tag 语义见 ADR 0019，两层设计取舍与三路 enforce 见 ADR 0034「job timeout」节 |
| `--grace` | 自动 | 中止 run 时等 worker 收尾（关云端会话、免继续计费）的秒数，超时才强杀。不填按引擎自动取够用值（`novaact` 150s、`midscene` 25s）；填太小会开跑前报错（强杀漏关会话＝烧钱）。 |
| `--expose-local` | — | 把「本机可达」的被测应用经隧道暴露给云端浏览器（ADR 0035）：值 = feature 中书写的原始 origin（如 `http://localhost:3000`，也可是局域网地址）。框架起隧道并把 job 文本中该前缀替换为公网 URL（含每 run 一换的 basic-auth 凭据，终态即拆）。需已配 ngrok authtoken（`NGROK_AUTHTOKEN`） |
| `--tunnel` | `ngrok` | `--expose-local` 用的隧道 provider（当前唯一 ngrok；免费层配额 1GB/月+2 万请求/月，重度使用可能碰顶） |
| `--fail-fast` | off | 任一 job 崩则中止整批 |
| `--json` | off | 只输出机器可读 JSON（CI/WebUI 消费） |
| `--quiet` | off | 不打逐事件进度（仍打文本汇总） |
| `--report-dir` | `reports` | RunReport 归集落点；每次 run 落 `DIR/<run_id>/` |
| `--no-report` | off | 跳过 RunReport 归集，且**不生成引擎原生产物**（Midscene 不出 report；Nova SDK 的 trajectory 关不掉、由 SDK 写进其自身临时目录、不上报），RunResult 里也不会出现任何产物路径——真「不生成 report」（ADR 0037 决策 3）。逃生舱：CI 只看退出码/JSON、或调试不想落盘。 |
| `--steps-dir` | `./steps`（存在才用） | 你自己的确定性 step 目录（ADR 0037 决策 4）：worker 启动时排序递归加载其中的 step 定义文件、注册进确定性注册表（两引擎扫同一目录，各取自己的扩展名：`.py` / `.mts`·`.mjs`）。解析顺序 `--steps-dir` > env `GHERKAI_STEPS_DIR` > `./steps`；**显式给的目录不存在直接退 2**（静默跳过等于把这些 step 悄悄换成 AI 判定）。值绝对化后写进 run 的 definition，本机后台推进/接力的进程读回同一份。[cloud] 不生效——云端 worker 的 steps 烙在定制镜像里（给了只警告、不拦；云端选哪套 step 用下面的 `--worker-variant`） |
| `--backend {local,cloud}` | `local` | 落库后端：local=文件落 `--report-dir`；cloud=状态落 DynamoDB、判定结果与报告落 S3（表/桶需预先建好） |
| `--prefix` | `gherkai-` | [cloud] 资源名前缀：批量决定表/桶/cluster/task-def 默认名，**须与 `gherkai deploy --prefix` 一致**；多环境（prod-/stage-）切换用它。兜底 `AWS_RESOURCE_PREFIX` |
| `--ddb-table` | `{prefix}runs` | [cloud] RunStore DynamoDB 表名（分区键 run_id + 排序键 item_type）；覆盖 prefix 默认；兜底 `AWS_DDB_TABLE` |
| `--s3-bucket` | `{prefix}artifacts` | [cloud] S3 桶名（存判定结果与报告）；覆盖 prefix 默认；兜底 `AWS_S3_BUCKET` |
| `--events-table` | `{prefix}events` | [cloud] events DynamoDB 表名（worker PutItem 目标，events-out）；覆盖 prefix 默认 |
| `--cluster` | `{prefix}cluster` | [cloud] ECS cluster 名（Fargate 执行）；覆盖 prefix 默认 |
| `--worker-variant` | 部署级默认指针 | [cloud] 云端 worker 镜像 variant（= 一套具名的确定性 step 集，见上『worker 镜像 variant』节）。不给则用后端的默认指针（`gherkai deploy` 初始化为 `base`）；提交侧 preflight 解析成各引擎的精确 task-def revision 写进 definition，缺映射即退 `2`、不回落。名字须合镜像 tag 字符集（字母数字下划线开头，其后可含 `.` `-`），不合法在开跑前就报错。local 忽略（给了打一行提示） |
| `--subnet` | SSM | [cloud] Fargate 子网 ID（可多次给）；不给则读 SSM `/{prefix}backend/subnets`（`gherkai deploy` 写的生成 ID） |
| `--security-group` | SSM | [cloud] Fargate 安全组 ID（可多次给）；不给则读 SSM `/{prefix}backend/security-groups` |
| `--region` | — | AWS region（local+cloud 均用；解析链 `--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置；喂 store + worker） |
| `--profile` | — | AWS profile（local+cloud 均用；`--profile` > `AWS_PROFILE`；喂 store + subprocess worker） |

> `--backend cloud` 需 boto3——**装 CLI 即已带**：发行包 `gherkai` 硬依赖 `gherkai-runtime[aws]`
> （已被 ADR 0037 决策 2c 反转：原为「cli 主依赖不含 boto3、cloud 走可选 extra」，库层 `gherkai-core[aws]` /
> `gherkai-runtime[aws]` extra 保留给库消费者），故无须额外安装步骤。code 层不变量不变：**local 路径绝不
> import boto3**（惰性 import 收在 compose 的 `_make_*` 钩子里）。
> cloud 下缺配置 / 缺 boto3（只单装库层、未带 `[aws]` 时才可能）/ 表桶预检失败 → 退出码 `2`；run 已开跑后 DynamoDB/S3 中途不可达 → 退出码 `1`。

## 选项（`submit`）

提交一批 feature 后台跑、立即返回 run_id（提交完就走，ADR 0034）。云端资源相关 flag（`--prefix`/`--ddb-table`/…）语义同 `run`，此处不复述、见上表。

| flag | 默认 | 说明 |
|---|---|---|
| `features...` | — | 一个或多个 `.feature` 路径（位置参数） |
| `--default-engine` | `novaact` | 未标 `@engine` 的 scope 用的默认引擎 |
| `--assertion-votes` | `1` | AI 断言（`Then`）投票次数（默认 1=单次判定） |
| `--max-concurrency` | `1` | 同时在跑的 worker 上限。随提交的任务定义（definition）生效，两档都有效：local 喂后台 per-run 进程与 `status --wait` 接力者；cloud 受部署侧上限约束（kicker/reconciler Lambda 的 env `MAX_CONCURRENCY`，IaC 设、当前 8——task 烧部署方账单，故留一道上限；声明超上限时 submit 的 preflight 会提示「本 run 将按上限并行」，不拦提交）。local 无此上限（worker 跑在你自己的机器、烧你自己的凭证）。须 ≥1（同 `run`）|
| `--default-job-timeout` | `300` | job 墙钟超时秒缺省（`<=0` 不超时）；标了 `@timeout:N` 的 scope 按 tag 走——语义同 `run` 表，「提交完就走」时的挂死/烧钱止损 |
| `--expose-local` / `--tunnel` | — / `ngrok` | 语义同 `run` 表；submit 后隧道由后台进程持有——local=per-run 进程、cloud=隧道守护进程（轮询终态即拆+TTL 兜底）。**本机需保持开机联网直到 run 终态**（关机=隧道断=测试以导航失败告终，ADR 0035） |
| `--tunnel-ttl` | 按 definition 算 | [cloud + `--expose-local`] 隧道守护进程的兜底 TTL 秒（须 > 0，否则退 2）。默认 = 各 job 预算之和 + 启动余量（submit 会打印生效值）；**调小有风险**——TTL 到点无条件拆隧道，短于实际 run 时长会让剩余 job 在应用不可达下跑成导航失败（ADR 0035 决策 3） |
| `--steps-dir` | `./steps`（存在才用） | 语义同 `run` 表。**值随 definition 走**：后台 per-run 进程与 `status --wait` 接力者从 definition 读回（它们的当前目录与你提交时不同，不会重新去猜 `./steps`），故同一个 run 三个推进者用的是同一套确定性 step |
| `--report-dir` | `reports` | 归集报告落点；`status` 查时须给同一路径。[cloud] 产物前缀由 kicker/reconciler Lambda 的 `REPORT_DIR` 决定（IaC 侧配，缺省 `reports`）——给了不一致的值，preflight 直接退 `2` 并点名两侧值（否则跑完了却在你给的前缀下找不到结果） |
| `--backend {local,cloud}` | `local` | local=本机 per-run 进程推进；cloud=Fargate + 云端 Lambda 事件驱动链推进（提交完真关机也跑完） |
| `--prefix` | `gherkai-` | [cloud] 资源名前缀（须与 `gherkai deploy --prefix` 一致）；`status` 查时须给同一 prefix。兜底 `AWS_RESOURCE_PREFIX` |
| `--ddb-table` / `--s3-bucket` / `--events-table` / `--cluster` | `{prefix}…` | [cloud] 覆盖各 prefix 默认名（语义同 `run` 表） |
| `--worker-variant` | 部署级默认指针 | [cloud] 语义同 `run` 表。**值随 definition 走**：解析出的各引擎 revision 写进 definition，云端推进器（kicker/reconciler）照它起 task ⇒ 整个 run 期间镜像固定 |
| `--region` / `--profile` | — | AWS region/profile（喂 store + worker，同 `run`） |

> `submit` 不收 `--subnet`/`--security-group`——cloud submit 只写 runs 表、不碰 SSM/ECS（ADR 0034）；Fargate 网络由 IaC 注给 reconciler/kicker Lambda 的 env。

> `submit` 无 `--json`/`--quiet`/`--wait`——它只把 run_id 打到 stdout 就退；进度/结果留给 `status`（含 `--json`）。

## 选项（`status`）

查一个 run 的进度/结果（`--wait` 轮询到终态再返回）。`--backend`/`--report-dir`(local)/`--prefix`(cloud) 须与 `submit` 时一致，否则查不到（退 `2`）。

| flag | 默认 | 说明 |
|---|---|---|
| `run_id` | — | `submit` 返回的 run_id（位置参数） |
| `--backend {local,cloud}` | `local` | 须与 `submit` 一致 |
| `--report-dir` | `reports` | [local] run 落点（须与 `submit` 一致） |
| `--wait` | off | 轮询到 run 达终态再返回：local 本机接力 tick 推进；cloud 检测到卡住才 invoke kicker Lambda 踢一脚接力 |
| `--max-concurrency` | `1` | [local `--wait`] 接力推进的并发上限**回落值**——run 的 definition 带值时以它为准（接力不改这个 run 的并行度）|
| `--json` | off | 输出机器可读 RunState（不打人读的诊断提示） |
| `--prefix` | `gherkai-` | [cloud] 资源名前缀（定位 DDB RunState + 推理 kicker Lambda 名）。兜底 `AWS_RESOURCE_PREFIX` |
| `--ddb-table` | `{prefix}runs` | [cloud] RunStore DDB 表名（覆盖 prefix 默认）；兜底 `AWS_DDB_TABLE` |
| `--region` / `--profile` | — | AWS region/profile |

### RunReport（每次 run 的应得产物，默认生成）

每次 `run` **默认**把这次执行归集成一份 RunReport 到 `reports/<run_id>/`：
- `manifest.json` —— 机器可读（CI/WebUI 消费）：薄信封（run_id 等）+ 各引擎原生报告产物的扁平清单。
  判定/时长/成本**不在此**——用 `run_id` 到 `ResultStore`（`jobs/*.json`）取判定真值；`index.html` 才含判定明细。
- `index.html` —— 人可导航入口：判定明细树 + 每个原生产物（Midscene html / Nova trajectory）一行链接，
  点开看**原样**产物。RunReport 只索引/链接、**不解析融合**产物内容；新引擎报任意 `kind` 零改 core。

index 链接指向产物**原位**（local 相对链接——产物就在 `reports/<run_id>/` 树内、目录可整体搬走/发同事；cloud 为 `s3://`）；跳过归集见 `--no-report`。
