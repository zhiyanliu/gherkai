# 云端后端由哪些载体组成：一次改动要传播到哪几处才生效

> 本文讲**机制如何协同工作**（机制），不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。`--backend cloud` 的后端不是一个整体，而是五个各自独立更新的载体；任何单个 ADR 只覆盖其中一个侧面，「已升版本 / 已做改动，云端行为却未变」的原因要横切 0033 / 0037 / 0038 / 0034 / 0042 才能完整回答。

本文只回答「改动要落到哪几处」。**推进链本身**（谁推进 run、事件经哪条通道、超时如何处置、云端 Lambda 为何不接管前台 run）见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)，本文不重复。

## 1. 五个载体

| 载体 | 内容 | 更新者 | 生效时机 | 名称 / 真源 |
|---|---|---|---|---|
| **CloudFormation stack** | 全部资源与其形态：runs 表（另带 `status-index` 稀疏 GSI）与 events 表（另带 TTL），两表都开 Stream；artifacts 桶（含 job-in 的按 tag 过期规则）；ECS cluster；每引擎一个 **task-def 模板 revision** 与一个 ECR repo；三个 Lambda + EventBridge rule + 两条 Stream 事件源；IAM 角色；VPC/子网/安全组；以及随事务写的几族 SSM 参数 | `gherkai deploy`（组装 context → 由 cdk CLI 启动 `gherkai_deploy_aws.app` 合成 → `cdk deploy`） | 变更集应用完即生效；**回滚时随事务一起回滚**（版本戳与模板不留错值） | stack 名 = `names.stack_name(prefix)`（provider 专有，与 `LAMBDA_ASSET_DIR_ENV` 同在 `deploy_aws/gherkai_deploy_aws/names.py`）；云资源名全经 `gherkai_runtime.names` 由 `--prefix` 推导 |
| **三个 Lambda 的部署 asset** | `lambdas/` 的 handler 源（`reconciler.py` 一份两个入口 + `exit_observer.py`）+ `BackendStack.LAMBDA_ASSET_PACKAGES` 逐项**从当前 venv 已安装位置复制**的 import 包（含 `gherkai_core` / `gherkai_runtime`）。boto3 由 Lambda runtime 自带 | 同一条 `gherkai deploy`（asset 由 `stack._build_lambda_asset()` 在本次部署时复制到临时目录） | asset 内容变 → CDK 算出的 asset hash 变 → 本次 deploy 的变更集包含三个函数的代码更新 | `stack.BackendStack.LAMBDA_ASSET_PACKAGES`；落点经 env `names.LAMBDA_ASSET_DIR_ENV` 从命令进程传给 cdk 启动的 app 进程 |
| **官方基础镜像** | 同版本 worker 包 + SDK 运行时 + 协议层，**零使用方内容**（`engines/*/Dockerfile`） | 发布方的 CI 按 tag 发到 GHCR（`workers.GHCR_BASE_IMAGE`） | 在 GHCR 就位**之后**，仍需 `gherkai deploy` 第 2 步 pull→push 进本账户的 ECR 才在云端可用；**运行时不直连 GHCR** | `ghcr.io/…/gherkai-worker-<engine>:<版本>` |
| **使用方的 variant 镜像** | 基础镜像 + 使用方 `COPY` 进去的确定性 step 目录（`GHERKAI_STEPS_DIR`）；**云端执行哪套 step 由镜像决定**，不由提交侧 `--steps-dir` 决定 | 使用方自行 build（gherkai 不拥有构建）+ `gherkai deploy push-worker`（推 ECR、从模板注册 revision、写 SSM 映射） | 写完 SSM 映射后，**下一次提交**解析到新 revision；已在运行的 run 不切换（见 §5） | ECR tag = `names.image_tag(CLI 版本, variant)`；repo 名 = `names.ecr_repo_name` |
| **SSM 参数** | `version`（后端版本戳）、`vpc`（生效 VPC 档）、`worker-template/<engine>`（模板 revision ARN）、`subnets`、`security-groups` 这五族是 **stack 资源**；`worker-image/<engine>/<tag>`（映射 JSON）、`worker-default`（默认 variant 指针）这两族由命令 `put_parameter` 写 | 前五族随 cdk 事务；后两族由 `push-worker` / `deploy` 的第 2-4 步写 | `put_parameter` 即生效（**覆盖语义、最后写者赢**） | 路径全经 `names.ssm_path(prefix, key)`，键名常量在 `gherkai_runtime.names` |

![官方基础镜像与使用方 build 的镜像如何进入本账户的 ECR、挂在哪个 task-def revision 上、由哪些指针指向，以及旧 revision 何时允许回收](../diagrams/cloud-delivery-identity.svg)

图注（云端交付与 worker 身份拓扑）：上表五行在图上各有落点；图只画从属与指向，每个载体的生效时机以上表第 4 列为完整口径。图上的 SSM 镜像映射按版本分键（见 §6）：升级更换版本命名空间后，自定义 variant 必须重推——§3 第 ③ 步与 §4「默认 variant 在新版本尚无镜像」那一行同出于此根因。本图只画交付与身份，不画推进链与事件通道，后者见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)。可交互版（缩放 / 聚焦单个节点 / 追踪一条路径）：https://zhiyanliu.github.io/gherkai/cloud-delivery-identity.html

三条容易出错的载体边界：

- **模板 revision 与 variant revision 是两回事**：模板由 stack 创建（承载 cpu/memory/两个 role/日志组/`runtimePlatform`/`stopTimeout`），镜像栏为 `latest` 占位、**永不被 RunTask**；每个（引擎，variant）另有一个从模板复制、镜像栏替换为 `repo@sha256:<digest>` 的 revision，实际起 task 用的是后者。
- **数据类资源不随 `gherkai destroy` 删**（两表、桶、两个 ECR repo 都是 `RETAIN`）；而 `worker-image/*` 与 `worker-default` 不是 stack 资源（由命令 `put_parameter` 写），`destroy` 同样不清除它们。同一 prefix 重建后这两族参数的原值仍在，记录的仍是上一套 stack 时期的 revision / 模板 ARN。
- **asset 的来源是发起这次部署的那个 venv**，不是仓库相对路径，也不联网安装：dev 版部署得到的就是本机当前的那份 code。清单漏一个传递依赖，后果是 Lambda 运行期 `ImportError`（清单完整性由 `deploy_aws/tests/test_lambda_asset.py` 的「剥掉 site-packages 真 import」那条用例保证）。

> 权威：[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（资源清单/两层命名/IAM/preflight）、[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 6（部署形态、asset 来源、版本戳、VPC 档）、[ADR 0038](../adr/0038-worker-image-delivery.md)（概念模型、SSM 参数真源表）；code：`deploy_aws/gherkai_deploy_aws/stack.py`、`.../cli.py`、`.../names.py`（provider 专有名：stack 名 / asset 落点 env）、`runtime/gherkai_runtime/names.py`（共享命名纯函数）。

## 2. 行为归属哪个载体（改动前的定位表）

| 改动内容 | 归属载体 | 未更新该载体的后果 |
|---|---|---|
| `core` 的判定/投影/序列化（`jobs/*.json` 的字段、状态聚合、RunReport 形态） | **前台 `run`**：提交者本机的 CLI；**`submit`**：Lambda asset 里那份 `gherkai_core`（云端 `jobs/*.json` 由 reconciler 投影产出） | 本机 `run` 立即生效，云端 `submit` 不生效：同一次改动在两条路径上表现不一致，这类不一致最易被误判为 bug |
| `runtime` 的组合根装配（`build_fargate_engines` 的 job-in 前缀、注入的 env、container 名） | 同上：本机 CLI + Lambda asset | 前台 cloud run 与 detached submit 起出的 task 形态分叉 |
| worker 侧的 step 执行、证据抽取、收尾排空、确定性 step 注册表 | **worker 镜像** | 云端执行的仍是旧行为（例如没有 `kind=evidence` 的证据），本机 `run --backend local` 已是新行为 |
| 使用方自写的确定性 step | **worker 镜像**（构建进镜像；云端不读提交侧 `--steps-dir`，传入该参数只警告、不拦截） | 云端执行的仍是镜像里那套旧 step |
| 资源形态：cpu/memory、`stopTimeout`、日志保留、GSI、Stream filter、IAM | **stack** | 资源未变更；且已有 variant 的 revision 仍由旧模板派生（见 §4「重派生」条） |
| 部署侧 per-run 并发 cap、产物前缀 `REPORT_DIR`、子网/安全组 | **stack**（两个推进器 Lambda 的 env；cap 常量 = `BackendStack.DEPLOY_SIDE_MAX_CONCURRENCY`） | 提交侧 preflight 即时提示：超 cap 只警告，`REPORT_DIR` 不一致直接退 2 |
| 后端版本戳、默认 variant 指针 | **SSM** | 提交侧 skew 判定失真 / 默认 variant 解析不到（见 §4） |

> 权威：[ADR 0042](../adr/0042-step-evidence-and-explain.md)「交付链」条（同一个改动的两条交付路径：Lambda asset vs worker 镜像）、[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 4（steps 目录约定）、[ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制四（cap 归部署方）；step 集如何被发现与命中见 [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md)，证据落点见 [`artifacts-and-evidence.md`](./artifacts-and-evidence.md)，`--json` 字段清单见 [`cli-json-contract.md`](./cli-json-contract.md)。

## 3. 一次版本升级的传播顺序，以及顺序为何不可调换

```
① uv tool upgrade gherkai            # 升 CLI（[deploy-aws] extra 沿用）
② gherkai deploy                      # stack + Lambda asset + 新版本基础镜像同步成 base + 重派生 + 清理
③ gherkai deploy push-worker …        # 有自定义 variant 时：基于新版本基础镜像重新 build 再推
```

**只能按此方向的原因**：后端由 CLI 的 `[deploy-aws]` extra 部署，版本戳的值就是**发起这次部署的那个 CLI 的版本**（CLI 的命令行入口层把 `args.version` 交给 provider，provider 组装成 `-c version=`，stack 的 `_resolve_version` 缺它即 fail-fast、不回落本包自报版本）。因此「先升后端再升 CLI」在物理上不可执行：deploy 命令本身就是那份 CLI。

**①→② 之间的提交会被拒绝，这是预期行为**：提交侧四个 cloud 入口（`run` / `submit` / `status` / `explain`）都先经过 `compose.check_backend_skew`，CLI 新于后端 → `SKEW_BLOCK` → 退 2、**无放行口**；② 执行完即恢复。不希望改动本机安装的部署方可以用 `uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy` 先升级后端。

**③ 不能提前到 ② 之前**：镜像 tag 含 CLI 版本（`names.image_tag`），提前推送等于推入一个后端尚不解析的版本命名空间。`push-worker` / `list-workers` 各自带同一道 skew 闸（`workers._skew_gate`）拦截此情形：CLI 新于后端时退 2，并输出一行以「不放行的理由：」开头的说明。`gherkai deploy` 的四步**有意不做**这道前置——它本身就是修改版本戳的动作，前置放在 cdk 之前会拦住自己、放在 cdk 之后则恒真。

**② 内部的顺序同样固定**：第 1 步（把模板 revision ARN 登记进 SSM）是 **stack 资源**、随 cdk 事务；第 2/3/4 步在 cdk 之后执行。故 cdk 成功而后三步失败 → 退 **1** 且提示「stack 已生效；重新运行 `gherkai deploy` 幂等收敛」——归并为 2（语义是「什么都没发生」）会误导。

操作步骤与命令样例不在本文重复，见 [`docs/user-guide/cloud-backend.md`](../user-guide/cloud-backend.md)（版本与升级、worker 镜像 variant 两节）。

> 权威：[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 7（版本真源、skew 三态与操作规则）、[ADR 0038](../adr/0038-worker-image-delivery.md)「与版本升级的交互」「命令族」；code：`runtime/gherkai_runtime/compose.py` 的 `check_version_skew` / `check_backend_skew`、`deploy_aws/gherkai_deploy_aws/workers.py` 的 `_skew_gate` / `run_deploy_steps`。

## 4. 症状 → 该推哪个载体

| 症状 | 缺的那一步 | 判据位置 |
|---|---|---|
| 任何 cloud 命令直接退 2「本机 CLI 新于后端」 | ② 未执行（stack 未重新部署 → 版本戳仍是旧值） | `compose.SKEW_BLOCK` 分支 |
| 云端 `submit` 的判定明细缺新字段（如 step 级 `message`），同版本本机 `run` 却有 | ② 未执行（**Lambda asset** 未重新上传；云端 `jobs/*.json` 由 asset 里那份 `gherkai_core` 投影产出） | [ADR 0042](../adr/0042-step-evidence-and-explain.md)「交付链」条 |
| 云端执行完没有证据 / step 行为仍是旧的 | ③ 未执行（**worker 镜像**未重新推送；发行版经 ② 的基础镜像同步，dev 树经 `push-worker`） | 同上 |
| 退 2「默认 variant `X` 在新版本尚无镜像」 | ③ 未执行。**默认指针不随升级重置**（它记录的是团队意图，`init_default_pointer` 在参数已存在时不改动）：指针仍指向 `X`，而 `<新版本>-X` 尚未推送 | `workers.init_default_pointer`；提示语在 `compose._variant_miss_hint` |
| 退 2「读不到 worker task-def 模板（SSM `worker-template/<engine>`）」 | 本 prefix 从未执行过 `gherkai deploy`（或上次部署所用的 CLI 版本尚无镜像机制） | `workers._template_arn` |
| `deploy` 调整了 cpu / `stopTimeout`，但 variant 仍以旧配置运行 | ② 的第 4 步（重派生）未完成：revision 是不可变快照、不继承模板变更 | `workers.rederive_variants`（按模板 ARN 判定、幂等；`pushed_at` 保留原值，镜像内容不变） |
| 提交退 2「产物前缀不一致」 | 推进器 Lambda 的 `REPORT_DIR` 与提交侧 `--report-dir` 不同（前者 IaC 有意不注入、由 handler 缺省供给） | `compose.preflight_cloud_resources` |
| `deploy` 退 1 并提示「stack 已生效，但同步基础镜像要 pull/push——deploy 的机器需要容器引擎」 | ② 的第 2 步未执行：纯发行版要求部署机具备容器引擎，探活失败即**硬失败**，第 3/4 步与清理 pass 均未执行——安装后重新运行 `gherkai deploy`（幂等收敛）。非纯发行版不探测容器引擎，第 2 步整步跳过并输出一条警告，第 3/4 步照常执行 | `workers.run_deploy_steps`（探活分支退 1）/ `workers.sync_base`（非纯发行版跳过；判据 `compose.is_pure_release`）；cdk 前那句预告在 `cli.Provider.deploy` |
| `list-workers` 里 revision 比 variant 多 | 正常现象：已退休 / 孤儿 revision 正等待清理 pass（见 §5），`_pending_cleanup` 逐条列出原因 | `workers.list_workers` |

`gherkai doctor --backend cloud --prefix …` 是这张表的只读版：一次性输出身份、后端版本比对、资源与三个 Lambda、报告前缀一致性、默认 variant 指针与**逐引擎的 revision 解析**（即上表「默认 variant 在新版本尚无镜像」那行的只读探针，至少一个引擎解析成功即算通过），以及部署工具链（Node / cdk / 容器引擎）。

> 权威：[ADR 0038](../adr/0038-worker-image-delivery.md)（四步、preflight、`--set-default` 只警告不拦）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md) 决策四（`doctor` 的 provider 段）。

## 5. `submit` 在提交时刻固定下来的内容

cloud 提交是**定义期解析、运行期照抄**，这是「重推 variant 不影响正在运行的 run」的全部根据：

1. preflight 把 `--worker-variant`（缺省 = 默认指针）解析成**本 run 用到的每个引擎**的 task-def revision，三环校验：SSM 有当前版本的映射 → 该 revision 仍 `ACTIVE` → 该 digest 在 ECR 中仍存在（三相时序见下图）；任一环缺失即退 2，**绝不回落**默认指针 / family 最新 ACTIVE / 模板 revision。
2. 解析结果写进 definition：`RunMeta.worker_variant`（人读）+ `RunMeta.worker_task_defs`（引擎 → revision ARN），同一批 ARN 另以扁平形式写入 runs 表 STATE item 的顶层属性 `worker_task_def_arns`。
3. 云端推进器（kicker / reconciler）与前台 `run` 的 `FargateEngine` 一律**照 definition 起 task**，用显式 revision、永不用 family 取最新；revision 的镜像栏是 `repo@sha256:<digest>`。
4. definition 里没有 `worker_task_defs` 的老 run（引入该机制前提交的、或旧 CLI 提交到新后端的）走**兼容路径**：按后端当前默认指针解析，并在 CloudWatch 输出一行 `worker-compat:`，其中标明 variant / 版本 / 引擎。解析失败时只跳过该 run（events Stream 一批含多个 run，向外抛异常会让整批重投后丢弃）。

![提交时刻把 variant 解析为本 run 每个引擎的显式 revision 并写入 run 记录；之后重推同名 variant 只产生新 digest、新 revision 与新映射，起 task 仍照定义使用提交时固定的那一个](../diagrams/cloud-backend-carriers-revision-pinning.svg)

图注（提交时刻固定 revision）：图上的「云端起 task 侧」= 正文第 3 条的云端推进器（kicker / reconciler 两个 Lambda）；那条回读边属于**云端侧**，即两个推进 Lambda 从 definition 读回那批 revision 再起 task。前台 `run --backend cloud` 不回读，它直接使用本进程 preflight 解析出的同一批（与写进 definition 的同源，`--no-report` 时不生成 run 记录），固定的效果相同。三环解析的完整判据（缺任一环即拒、绝不回落）见上面第 1 条；definition 里没有那两个字段的老 run 走上面第 4 条的兼容路径，图上不画。两张图的分工：§1 那张画**静态从属**（镜像挂在哪个 revision、由谁指向），本图画**时间先后**（提交时刻 / run 运行期间被重推 / 之后起 task）；推进链与事件通道两张图都不画，见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)。

第 3 条的正确性有两道配套护栏，都在回收侧：

- **ECR 仓库不设任何 lifecycle 规则**：正在运行的 run 的旧 revision 按 digest 指向被重推后转为 untagged 的那一层，因此这两个 repo 上**不得添加 untagged 过期规则**；随之而来的 untagged 层增长是已知的存储成本（该决策的理由与代价记录见本节末权威行的 ADR 0038）。
- **删 revision 要满足清理的两个前置条件**（机会式清理 pass，挂在 `push-worker` 末步与 `deploy` 第 4 步末，**无定时任务**）：退休满 `workers.RETIRE_QUIET_PERIOD`（值见该常量）**且**无未到终态的 run 引用它。引用判定走 runs 表 `status-index` GSI 的 `Query` + `contains(worker_task_def_arns, :arn)`——GSI 必须 `INCLUDE` 这个属性，不投影则恒不匹配、运行中 run 引用检查静默失效。任一条不满足则留到下次 pass（滞留无害：`ACTIVE` 但无人引用）。**已知盲区**：`run --backend cloud --no-report` 不写 STATE item，其 revision 引用对运行中 run 引用检查不可见。

> 权威：[ADR 0038](../adr/0038-worker-image-delivery.md)「不变量」「运行时与 preflight」（含被拒方案：RunTask 传 family、缺字段回落模板、ECR untagged 过期规则）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（definition 随 run 走、宿主只读回）；code：`compose.resolve_worker_variant` / `resolve_default_worker_task_defs`、`workers.cleanup_pass`、`core/gherkai_core/adapters/run_store/ddb.py` 的 `create_run`。

## 6. 一个 prefix = 一套环境；多版本并存依靠多 prefix

**一个部署（一个 prefix）在任一时刻只有一个后端版本**：Lambda 代码、模板 revision、SSM 版本戳都是单份，同一 prefix 内不做双版本并行。多版本 / 多团队并存的做法是**按 prefix 部署成多套环境**（`prod-` / `stage-`）。prefix 是全部云资源与全部 SSM 路径的命名空间，stack 名也随它推导（`names.stack_name`）；闲置成本近零（事件驱动、无常驻组件），额外开销只有一份 ECR 存储。

两条配套事实：

- **两侧 prefix 必须一致**：部署侧与提交侧走的是**同一条解析链** `compose.resolve_cloud_target`（flag > `AWS_RESOURCE_PREFIX` > `names.DEFAULT_PREFIX`），CDK 建出的名就是提交侧推导的默认名；不一致时 preflight 报出 prefix 并退 2。
- **variant 按版本隔离，不等于「多版本同时运行」**：SSM 键含版本（`worker-image/<engine>/<版本>-<variant>`），旧版本的映射保留为历史、不参与当前版本解析（`workers.current_version_mappings` 接收一次枚举好的参数序列，只取当前版本前缀的条目）。

前台 `run --backend cloud` 与 detached `submit --backend cloud` **共用同一套表、桶、cluster、task-def 与三个 Lambda**，分流依据是 STATE 上的 `detached` 标记（kicker 在 Stream filter 层过滤，reconciler / exit-observer 在 handler 内判定），故一套 prefix 可同时服务两种执行方式而互不干扰；两道拦截的细节见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) §7。

> 权威：[ADR 0038](../adr/0038-worker-image-delivery.md)「多版本与多环境」、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)「两层命名」、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（`detached` 标记与 filter）。

## 7. 延伸阅读

| 想深入的主题 | 去哪读 |
|---|---|
| 部署命令的全部 flag、VPC 的三种取值、权限清单、`destroy` 后的残留 | [`docs/user-guide/cloud-backend.md`](../user-guide/cloud-backend.md) |
| worker 镜像交付全部决策/护栏/被拒方案 | [ADR 0038](../adr/0038-worker-image-delivery.md) |
| 分发形态、`gherkai deploy` 的 provider 接缝、版本真源与 skew | [ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 6-7 |
| 云资源 IaC / 命名 / IAM / preflight | [ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md) |
| Fargate 执行面：`stopTimeout` ↔ `deploy --stop-timeout`（默认值与 Fargate 硬上限见 `stack.BackendStack` 的两个常量与 `--help`）、grace 预算、中断韧性 | [ADR 0032](../adr/0032-fargate-execution-environment.md)（真容器校准结论 3-4） |
| 事件驱动推进链、超时定时器、投影与提交点 | [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)、[ADR 0034](../adr/0034-detached-batch-reconciler.md) |
| 判定的计算路径（票 → step → scenario → job → run 四层归约与严重度） | [`verdict-model.md`](./verdict-model.md) |
| 产物与证据的落点、S3 key 布局 | [`artifacts-and-evidence.md`](./artifacts-and-evidence.md) |
| 一条确定性 step 的生命周期（云端为何依据镜像而非 `--steps-dir`） | [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) |
| `--json` 字段清单（含 `run_meta.worker_variant` / `worker_task_defs`、`list-workers --json`） | [`cli-json-contract.md`](./cli-json-contract.md) |
