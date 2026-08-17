# cli — 执行核心库的命令行皮（argparse + render）

`core/` 是纯库（零引擎依赖、不碰文件系统）。**cli 是它的第一张皮**：解析参数 → 经产品本体
`gherkai.compose` 读 `.feature`、装配引擎与 Store adapter 注入给 core → 把 `RunResult` 渲染给人或 CI 看。
WebUI 将来是另一张皮，**直接调 core、复用产品本体 `gherkai`（compose 等组合根逻辑所在的平级包，ADR 0016「演进」节）**，不经本 cli。

设计见 [ADR 0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)（执行架构 / 组合根注入）；
无状态跑批（`submit`/`status` 的「提交完就走 → 事件驱动推进 → 轮询收集」）见 [ADR 0034](../docs/adr/0034-detached-batch-reconciler.md)。

## 模块

```
cli/
├── __main__.py   ← argparse 皮：run/submit/status/plan/list-engines/list-deterministic 解析 → 调 gherkai.compose/core → 注入 RunPersistence 实时落库 → 调 render；定义退出码
└── render.py     ← 表层渲染：0024 事件 → 进度行；RunResult → 文本汇总 / JSON
```

组合根逻辑（compose/detached/names）住在平级的产品本体包 `gherkai/`（曾在本包内、被 Lambda/iac 的真实代价逼出抽包，ADR 0016「演进」节）：那是任何前端都要的接线，
后者只是 argparse + 标准 IO。

**实时落库**：`run` 不是「跑完才一次性落盘」——`__main__` 注入 core 的 `RunPersistence`
（组合根注入三个 Store adapter），run 开始即写 definition + 初始全 pending 态，每个 scope 起跑刷
RUNNING、完成即落该 scope 判定真值，最后 `finalize` 写总状态（commit point）。`--no-report` 时跳过整条落库
（裸跑、零落盘逃生舱）。

落哪由 `--backend` 定：默认 `local`（文件落 `--report-dir`）；`--backend cloud` 让组合根改注入 DynamoDB/S3
adapter、复用同一条 `RunPersistence`，把状态落 DynamoDB、判定真值与报告落 S3（表/桶需预先建好）。见下『选项』表与『跑』小节。未来 WebUI 复用同一套 `gherkai.compose` 装配，cli 这张皮的接线不变。

## 跑（会烧真 AWS 钱：模型调用 + AgentCore 会话）

```bash
cd cli
uv sync                                            # 装环境（gherkai/core 作 path 依赖）

# 跑一个 feature（默认引擎 novaact，默认 max-concurrency=1）
uv run python -m cli run ../features/wikipedia_generic.feature

# 未标 @engine 的 scope 默认走 Midscene 引擎、放开并发、JSON 输出
uv run python -m cli run ../features/wikipedia_generic.feature \
  --default-engine midscene --max-concurrency 2 --json

# 预检 .feature（不烧钱）：看 scope/job 分组、校验配置（@scope/@engine 冲突等），不真跑。
# 每个 step 还标注派发预期（← 确定性: … / 默认 AI 不标；worker 自述命中，ADR 0036——
# 起本地瞬时 worker 子进程做 match 查询，零 AWS 零花费；引擎环境未装则自动降级为无标注）
uv run python -m cli plan ../features/wikipedia_generic.feature
uv run python -m cli plan ../features/*.feature --json     # 机器可读分组

# 列可用引擎及其 spawn 命令（不烧钱）
uv run python -m cli list-engines

# 列指定引擎支持的确定性 step（worker 注册表自述，写 feature 时查询复用；不烧钱，ADR 0036）
uv run python -m cli list-deterministic --engine midscene      # --json 可选；默认 --engine novaact

# 云端落库：状态 → DynamoDB、判定结果与报告 → S3（表/桶需预先建好；云端后端才需装 boto3）
uv sync --extra aws                                # 装 boto3（仅 --backend cloud 需要）
uv run python -m cli run ../features/wikipedia_generic.feature \
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
cd cli

# ── local：submit 立即返回 run_id（后台 per-run 进程推进），事后再来收 ──
RUN_ID=$(uv run python -m cli submit ../features/wikipedia_generic.feature --max-concurrency 2)
# submit 提交完就走：本机 fork 一个脱离 CLI 的 per-run 进程跑推进循环，CLI 打完 run_id 即退

uv run python -m cli status "$RUN_ID"                # 查一次进度/结果（只读，不推进）
uv run python -m cli status "$RUN_ID" --wait         # 轮询到终态才返回（per-run 进程崩了/慢了，本命令接力推进到底）
uv run python -m cli status "$RUN_ID" --wait --json  # 同上，输出机器可读 RunState

# ── cloud：submit 只把 definition 落 DDB，之后云端 Lambda 链推进（提交完真关机也跑完）──
RUN_ID=$(uv run python -m cli submit ../features/wikipedia_generic.feature --backend cloud --prefix gherkai-)
uv run python -m cli status "$RUN_ID" --backend cloud --prefix gherkai- --wait
# cloud --wait 检测到卡住（连续几轮状态不变）才 invoke kicker Lambda 踢一脚接力，正常推进时不打扰
```

**为何拆**：`run` 要求 CLI 全程在线（网断/关机即中止）；`submit` 提交完就走——local 由脱离 CLI 的 per-run 进程推进、
cloud 由云端 Lambda 事件驱动链推进（submit 机器无 ECS 写/执行权限——仅 preflight 的只读探活，可立即关机）。`status` 事后查/收集：`--wait` 是三个推进触发源
之一（人来查即接力），保证「推进即使中断、也能被查询者续到底」（ADR 0034）。`status` 的 `--backend`/`--report-dir`/`--prefix`
须与提交时的 `submit` 一致（否则查不到）。

## 退出码

- `0` —— RunResult 总状态 passed
- `1` —— 跑完了但有 failed/error（断言没过 / 引擎异常）；`--backend cloud` 下若 run 已开跑、中途 DynamoDB/S3 不可达（如桶被删）也退 `1`
- `2` —— 没跑成：feature 读不到、plan 配置矛盾（PlanError）、参数非法（如 `--assertion-votes < 1`）、或无子命令；`--backend cloud` 还没开跑就被拒（缺 boto3、或 `--prefix` 拼出的表/桶/cluster/task-def 不存在·无权限·凭证/region 缺——运行前 preflight 点名 prefix fail-fast）

> cloud 失败分层的切分线 = run 是否已真正开跑：起 worker 前的配置/可达问题退 `2`，跑到一半的云端故障退 `1`。

### submit / status 的退出码分层（无状态跑批，ADR 0034）

`submit` 与 `status` 各自的退出码衡量的是**不同的事**——`run` 一条命令里揉在一起的「提交 + 判定」被拆开了：

- **`submit`：退出码 = 提交成功与否，不是 run 的判定。**
  - `0` —— 已成功提交（local：per-run 进程已 fork、run_id 已打印；cloud：definition 已落 DDB，云端链接管）。
  - `2` —— 没提交成：feature 读不到 / plan 配置矛盾（同 `run`）；cloud 还缺 boto3、或 preflight 不过（表/桶/cluster/本 run 用到引擎的 task-def/事件驱动链三 Lambda——链上任一 Lambda 缺则提交会成功但 run 永不推进，故挡在提交前）、或 `create_run` 时云端不可达。
  - 判定结果（PASSED / FAILED / …）**此刻还没出**，要用 `status` 去查。
- **`status`：查询本身成功即 `0`；判定退出码只在读到终态时给出。**
  - `0` —— run 达终态 `PASSED`；**或**未达终态（`pending`/`running`）时的一次查询（查到了就算成功，非 `--wait` 不评判）。
  - `1` —— run 达终态但非 `PASSED`（`failed`/`error`/`skipped`/`aborted`）。配 `--wait` 时即「轮询到终态后按判定给退出码」——CI 想拿 `run` 那样的 0/1 判定码，用 `status --wait`。
  - `2` —— 查不到该 run（`--report-dir`/`--prefix`/`--ddb-table` 与 `submit` 不一致？）；cloud 读 DDB 时云端不可达；`--wait` 接力要 invoke 的 kicker Lambda 不存在（prefix 配错/CDK 未部署——接力对象缺失，死等无意义、点名 prefix 退出）。

> 一句话：`submit` 退出码答「提交成功了吗」，`status --wait` 退出码答「这个 run 判定过没过」（PASSED→`0` / 其余终态→`1`）——`run` 的 0/1 判定语义在拆分后落到了 `status --wait` 上。

## 输出：stdout = 数据 / stderr = 进度

遵循 Unix 惯例：**stdout 只放该命令的核心产出**（`--json` 的 JSON 文档 / 人看的文本汇总 / `list-engines` 列表），**stderr 放所有进度诊断**（plan、逐事件、run_id、RunReport 落点、worker 透传日志）。故：

- `cli run … --json > r.json` —— `r.json` 是纯净 JSON（进度仍在终端可见、不污染文件）
- `cli run … > summary.txt` —— `summary.txt` 是纯净文本汇总

## 选项（`run`）

| flag | 默认 | 说明 |
|---|---|---|
| `features...` | — | 一个或多个 `.feature` 路径（位置参数） |
| `--default-engine` | `novaact` | 未标 `@engine` 的 scope 用的默认引擎（标了 `@engine:` 的按 tag 走） |
| `--assertion-votes` | `1` | AI 断言（`Then`）投票次数（默认 1=单次判定）；调高（如 3/5）启用抖动检测：跑 N 次取多数票。须 ≥1 |
| `--max-concurrency` | `1` | 同时在跑的 worker 上限（护真实成本/配额） |
| `--default-job-timeout` | `300` | job 墙钟超时秒的缺省值（`<=0` 不超时）。两层声明：标了 `@timeout:N` tag 的 scope 按 tag 走（同 scope 声明不一致 → `PlanError`）、未标的用本缺省——同 `@engine`/`--default-engine` 模式。tag 语义见 ADR 0019，两层设计取舍与三路 enforce 见 ADR 0034「job timeout」节 |
| `--grace` | 自动 | 中止 run 时等 worker 收尾（关云端会话、免继续计费）的秒数，超时才强杀。不填按引擎自动取够用值（`novaact` 150s、`midscene` 25s）；填太小会开跑前报错（强杀漏关会话＝烧钱）。 |
| `--expose-local` | — | 把「本机可达」的被测应用经隧道暴露给云端浏览器（ADR 0035）：值 = feature 中书写的原始 origin（如 `http://localhost:3000`，也可是局域网地址）。框架起隧道并把 job 文本中该前缀替换为公网 URL（含每 run 一换的 basic-auth 凭据，终态即拆）。需已配 ngrok authtoken（`NGROK_AUTHTOKEN`） |
| `--tunnel` | `ngrok` | `--expose-local` 用的隧道 provider（当前唯一 ngrok；免费层配额 1GB/月+2 万请求/月，重度使用可能碰顶） |
| `--fail-fast` | off | 任一 job 崩则中止整批 |
| `--json` | off | 只输出机器可读 JSON（CI/WebUI 消费） |
| `--quiet` | off | 不打逐事件进度（仍打文本汇总） |
| `--report-dir` | `reports` | RunReport 归集落点；每次 run 落 `DIR/<run_id>/` |
| `--no-report` | off | 跳过 RunReport 归集（逃生舱：CI 只看退出码/JSON、或调试不想落盘） |
| `--backend {local,cloud}` | `local` | 落库后端：local=文件落 `--report-dir`；cloud=状态落 DynamoDB、判定结果与报告落 S3（表/桶需预先建好） |
| `--prefix` | `gherkai-` | [cloud] 资源名前缀：批量决定表/桶/cluster/task-def 默认名，**须与 CDK（`iac_aws_backend`）部署用的 prefix 一致**；多环境（prod-/stage-）切换用它。兜底 `AWS_RESOURCE_PREFIX` |
| `--ddb-table` | `{prefix}runs` | [cloud] RunStore DynamoDB 表名（分区键 run_id + 排序键 item_type）；覆盖 prefix 默认；兜底 `AWS_DDB_TABLE` |
| `--s3-bucket` | `{prefix}artifacts` | [cloud] S3 桶名（存判定结果与报告）；覆盖 prefix 默认；兜底 `AWS_S3_BUCKET` |
| `--events-table` | `{prefix}events` | [cloud] events DynamoDB 表名（worker PutItem 目标，events-out）；覆盖 prefix 默认 |
| `--cluster` | `{prefix}cluster` | [cloud] ECS cluster 名（Fargate 执行）；覆盖 prefix 默认 |
| `--subnet` | SSM | [cloud] Fargate 子网 ID（可多次给）；不给则读 SSM `/{prefix}backend/subnets`（CDK 写的生成 ID） |
| `--security-group` | SSM | [cloud] Fargate 安全组 ID（可多次给）；不给则读 SSM `/{prefix}backend/security-groups` |
| `--region` | — | AWS region（local+cloud 均用；解析链 `--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > profile 配置；喂 store + worker） |
| `--profile` | — | AWS profile（local+cloud 均用；`--profile` > `AWS_PROFILE`；喂 store + subprocess worker） |

> `--backend cloud` 需 boto3（可选 extra，纯 local 不装）：`uv sync --extra aws`（或 `pip install cli[aws]`）。
> cloud 下缺配置 / 缺 boto3 / 表桶预检失败 → 退出码 `2`；run 已开跑后 DynamoDB/S3 中途不可达 → 退出码 `1`。

## 选项（`submit`）

提交一批 feature 后台跑、立即返回 run_id（提交完就走，ADR 0034）。云端资源相关 flag（`--prefix`/`--ddb-table`/…）语义同 `run`，此处不复述、见上表。

| flag | 默认 | 说明 |
|---|---|---|
| `features...` | — | 一个或多个 `.feature` 路径（位置参数） |
| `--default-engine` | `novaact` | 未标 `@engine` 的 scope 用的默认引擎 |
| `--assertion-votes` | `1` | AI 断言（`Then`）投票次数（默认 1=单次判定） |
| `--max-concurrency` | `1` | 同时在跑的 worker 上限（local：喂给后台 per-run 推进进程） |
| `--default-job-timeout` | `300` | job 墙钟超时秒缺省（`<=0` 不超时）；标了 `@timeout:N` 的 scope 按 tag 走——语义同 `run` 表，「提交完就走」时的挂死/烧钱止损 |
| `--expose-local` / `--tunnel` | — / `ngrok` | 语义同 `run` 表；submit 后隧道由后台进程持有——local=per-run 进程、cloud=隧道守护进程（轮询终态即拆+TTL 兜底）。**本机需保持开机联网直到 run 终态**（关机=隧道断=测试以导航失败告终，ADR 0035） |
| `--report-dir` | `reports` | [local] 归集报告落点；`status` 查时须给同一路径 |
| `--backend {local,cloud}` | `local` | local=本机 per-run 进程推进；cloud=Fargate + 云端 Lambda 事件驱动链推进（提交完真关机也跑完） |
| `--prefix` | `gherkai-` | [cloud] 资源名前缀（须与 CDK 部署一致）；`status` 查时须给同一 prefix。兜底 `AWS_RESOURCE_PREFIX` |
| `--ddb-table` / `--s3-bucket` / `--events-table` / `--cluster` | `{prefix}…` | [cloud] 覆盖各 prefix 默认名（语义同 `run` 表） |
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
| `--max-concurrency` | `1` | [local `--wait`] 接力推进的并发上限 |
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
