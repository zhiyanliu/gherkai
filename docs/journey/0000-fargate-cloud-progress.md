# Fargate 云端执行化：进度总纲 + task breakdown

> **⚠️ 状态：Fargate 上云主线（WP-S→#7→WP0→WP1→WP2→WP3-A→WP3-B）已全部完成、决策全落 ADR，本文件待删（保留仅为审计过渡）。** 「已确立的重要事实/取舍」诸条 → [0024](../adr/0024-worker-core-protocol.md)（软停非即时/asyncio 被拒/session TTL/机制不对称）+ [0029](../adr/0029-engine-artifacts-to-s3.md)（抢传不对称）；backlog 诸条 → [0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（task-def preflight / job-in 生命周期 / SSM 空值 / RETAIN / IAM 标定）+ [0029](../adr/0029-engine-artifacts-to-s3.md)（traces.json 类型无关化）+ [0032](../adr/0032-fargate-execution-environment.md)（超时封顶）+ [0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 C（profile-only 真验边界）。task breakdown 状态表/commit 号/工作节奏为过程记录，随删弃（git history 存底）。**唯一未做的产品项 = 无状态跑批（CLI 提交→轮询→脱离 run），见 [0016](../adr/0016-execution-architecture-core-lib-run-model.md) v1.1「待做」+ [0017](../adr/0017-cloud-execution-fargate-over-runtime.md)。**
>
> **类型：** Journey / 进度导航（**跨 WP 的计划状态**，非某次调查的证据——特定调查证据见 0001+）。
> **为何存在：** task 系统跨 compact/会话会丢；本文件入仓、是 compact 后接手工作的**第一份该读的**——一眼看到全局进度、各 WP 状态、指向哪份 ADR/证据。
> **维护：** 每完成一个 WP / 有新决策落 ADR，回来更新本文件的状态表 + 指针。**只记状态与导航，不记实现细节**（细节在 ADR/各专项 Journey/code）。

## 大目标

把 UI 测试框架的**执行面**搬上云：worker 从本地 subprocess → AWS Fargate/ECS 容器。
现状：存储面（RunStore→DDB、Result/Report→S3）+ 产物面（引擎产物→S3）+ **执行面（`--backend cloud` ⇒ FargateEngine，worker 跑 Fargate 容器）均已上云 + 真部署真跑验证**（WP2 完成）。默认档仍 local subprocess；cloud 档全链路上云。Fargate 特有的中断/grace 韧性真容器校准（WP3-B）**已完成**（4 次真跑标定，落 ADR 0032）。

## 两条正交轴（贯穿全局，勿混）

- **Engine adapter**（按执行环境分）：SubprocessEngine（local）/ FargateEngine（cloud，WP1 建 adapter + WP2 组合根接线，均已真跑）。
- **Engine worker**（按 AI 引擎分）：novaact（Python）/ midscene（TS）。
- **worker 引擎逻辑不按执行环境分**；worker 的 **I/O 边缘**（job 入口 / 事件 sink / 产物落点）才是随执行环境变的、应抽象成可注入接口（ADR 0016 组合根注入 / 0024 远程传输演进）。

## task breakdown + 状态

| WP | 内容 | 状态 | 落点/证据 |
|---|---|---|---|
| **WP-S** | 中断丢失实测预演 + 抢传验证（Fargate 中断韧性的事实前置） | ✅ 完成 | [journey/0001](./0001-wps-interruption-loss-spike.md)（5 发现、8 格数据、抢传验证、Midscene 补救方向） |
| **#7** | 修 Nova SIGTERM 中断模型（flag-only + act timeout + grace enforce）——WP0 入口条件、独立现有生产 bug | ✅ 完成（commit `7404bba`） | ADR 0024 终止契约 / 0028 / 0026 / 0032；证据 0001。三层测试 + 真跑验证 hung=false |
| **WP0** | worker I/O 边缘抽象成可注入接口（JobSource 读 stdin↔S3、EventSink 写 EVENTS_FD↔events-out）；纯重构、零行为变化；对称已有 ArtifactUploader。emit 合理不对称：Midscene async（为 aws-sdk-js 预留）/ Nova 同步（greenlet+boto3、不撞 0024 asyncio 否决） | ✅ 完成（commit `452d6bc`，两轮 review 已过） | ADR 0024「I/O 边缘可注入接口」条；范本 ArtifactUploader（0029）；真跑：Midscene(wikipedia)/Nova(example.com) baseline 完整事件流+scope_done+exit 0+三通道分离；依赖 #7✅ |
| **WP1** | Fargate 传输层：**events-out 定为 DynamoDB**（worker PutItem / core Query 轮询，非 SQS/MSK——选型经三方案查证收敛、ADR 0024 已改）。切分 4 子步：**S1**✅ events 表 schema + wire（PK=run_id#scope_id/SK=seq，并进 S2）→ **S2**✅ FargateEngine adapter（PutObject job + RunTask/StopTask/DescribeTasks + Query 增量迭代器 + 强一致终读；moto 编排测 + 退出码纯单测）→ **S3**✅ 两个引擎 worker EventSink DDB 态（PutItem，替 WP0 的 SQS 守卫）+ JobSource S3 态；run_id 经 RunTask overrides 注入 worker（adapter 侧）→ **S4**✅ schedule 零改（存活/退出码在 adapter 迭代器里）、仅 2 处注释校准为 engine 无关。**组合根接线（build_engines 接 FargateEngine + run_id/task 配置构造注入）归 WP2**。3 决策（A cloud=Fargate 执行 / B subprocess+注入云存储 降内部预演 / C Fargate 配置走 CLI 参数）落 ADR 0016 | ✅ 完成（4 commit `fee6cea`/`d4e4321`/`3f83040`/`b04bc7c`）：S2/S3/S4 + 3 决策 ADR + region/profile 贯通（两轮对抗 review：WP1 主体 11 CONFIRMED + region/profile 子块 8 CONFIRMED，含真跑抓出「profile 注 Fargate 致命」「AgentCore region=None 崩」两 major 并修）。core 176/cli 66/nova 97/midscene 81 全绿。**组合根接线归 WP2** | ADR 0024（events-out=DDB + 被拒护栏）+ 0016（3 决策 + region/profile 决策 C「正确非对称」）；code：core/core/adapters/fargate_engine.py + 两个引擎 lib/event_sink+job_source + cli compose.resolve_region；依赖 WP0✅ |
| **WP2** | **`iac_aws_backend` CDK 工程建齐 `--backend cloud` 全部 AWS 资源** + **组合根接 FargateEngine**（设计冻结见 ADR 0033）。**已全部实现 + 真部署真跑验证**（✅ 已 commit `6e21448`）：① 接线（build_fargate_engines 按 job.engine 选 `{prefix}{engine}-worker` task-def、注 artifact_s3/region/SDK落点env 不注 profile + `--backend cloud` 切 FargateEngine，决策 A 落 CLI、report⊥执行正交 + 两层命名 `--prefix` + subnet/sg 走 SSM + preflight fail-fast 点名 prefix + Midscene region 全可配惰性化 + 两个引擎 events TTL expires_at=now+7d）；② **CDK 工程本体**（`iac_aws_backend/`：2 DDB 表 + 1 S3 桶 + cluster + 2 task-def/2 ECR + IAM 分立 task role 最小权限 + execution role + VPC 三档可指定 + SSM；synth + 9 断言测试）；③ **2 Dockerfile**（Nova python3.13 / Midscene node22，**不装 chromium 二进制**——connectOverCDP 连云浏览器真跑证实）。**真部署验证**（账户 000000000000/us-east-1、默认 VPC）：两个引擎 ×（确定性 + AI）真跑 `--backend cloud` 全 passed，产出物三处全核对（RunStore STATE / events seq 单调+TTL / ResultStore+Report+job-in S3 布局）；AI step 真调模型（Midscene Bedrock 1863 tokens / Nova act）+ report/trajectory 真上传 S3 | ✅ 完成（commit `6e21448`） | **ADR 0033**（IaC + 接线主决策，已按真跑校准）+ 0024 TTL + 0016 决策 A/C；依赖 WP1✅ |
| **WP3-A** | 中断抢传落生产：两个引擎 act 边界即时上传（Nova 抢配套 trajectory.json / Midscene 提前 report 抢传）+ Midscene scenario 边界 log 抢传（第四级）+ 两个引擎上传套超时（退出时间有界护栏）——**不依赖 Fargate**（ADR 0029、subprocess+cloud 就做、Fargate 忠实预演），和 #7 中断主题连续 | ✅ 完成（commit `aaeb2e8` 起 5 个：核心 + harness + 文档校准 + CLAUDE.md 纪律；两轮对抗 review 已过） | ADR 0029（上传时机四级 + 固有残余 + 超时）；真跑验证：Nova trajectory 救回、Midscene report+scenario log 救回（多 scenario 中断落 scenario2、scenario1 log 已进 S3）；证据 0001 |
| **WP3-B** | Fargate 特有韧性：grace/stopTimeout 真校准 + botocore retry vs grace 实测 + 错误分类升级 + 孤儿产物恢复（Fargate 查 S3）——**必须等真 Fargate** | ✅ 完成（4 次真跑标定：margin 60→30/下限 150、stopTimeout=120、结论 4 澄清 Fargate 侧 D+TTL 兜底；余退化网络实测/孤儿主动扫盘为非阻塞 backlog） | ADR 0032（Accepted，真容器校准结论）；依赖 WP1+WP2 真容器 |

## 已冻结的关键设计（ADR 索引，真做各 WP 前必读对应条）

- **ADR 0024**「远程传输演进」：port 抽象 survive、pipe 传输 die；job-in→S3（RunTask overrides 8192 上限塞不下，传 `JOB_S3_URI` 小指针）、**events-out→DynamoDB events 表**（worker PutItem / core Query PK=run_id#scope_id 轮询增量拉，**非 SQS/MSK**——选型经三方案查证收敛，被拒护栏在该 ADR）、stop→StopTask、退出码→DescribeTasks。**终止契约**：两个引擎会话释放契约 + Nova flag-only（#7 已实现）+ act 有界返回 + grace 硬约束（core enforce）+ 两条被拒护栏（raise 模型 / asyncio 化）。
- **ADR 0032**（Accepted）：Fargate 执行环境特有——容器盘停即销毁的中断丢失、grace/stopTimeout 预算、act 粒度即时抢传。已真容器校准（4 次真跑）。
- **ADR 0033**（Accepted，已真部署验证）：`iac_aws_backend` CDK 工程（建 `--backend cloud` 全部 AWS 资源）+ 组合根接 FargateEngine。两层命名（prefix 批量默认 + 单资源覆盖，正交无特判）、subnet/sg 走 SSM、preflight fail-fast 点名 prefix、VPC 三档可指定、2 镜像分立（**不装 chromium 二进制**——connectOverCDP 连云浏览器）、task-def 不焊 region/凭证、container 名 `{engine}-worker`（CDK↔cli 硬契约）、IAM 最小权限（动作集经真跑逐个暴露标定）、产物上传需注两组 env（ARTIFACT_S3_* + SDK 落点 NOVA_LOGS_DIR/MIDSCENE_RUN_DIR，缺一即 no-op 丢产物）。已按真跑校准。
- **ADR 0029**（Accepted）：产物→S3 上传，由注入驱动、已在 subprocess 预演环境实现、是 Fargate 忠实预演（预演定位=决策 B）。Midscene 抢传补救方向见 0001。
- **ADR 0016**：core 纯库/窄腰/组合根注入/worker 引擎逻辑不按执行环境分——所有 WP 的架构红线。**3 决策权威声明在「cli backend 选择」节**：A `--backend cloud`=存储上云+Fargate 执行（单旋钮、不暴露正交，含被拒护栏）/ B subprocess+注入云存储 降为内部预演（e2e_harness、非用户档）/ C Fargate 配置走 CLI 参数（对称 `--table`）。
- **ADR 0026**：schedule 纯 reducer、对引擎无知。

## 已确立的重要事实/取舍（防重新调研）

- **Nova 中断只能软停、非即时**（act 靠 SDK per-act timeout 有界返回，act 不幂等使即时打断无语义收益）——ADR 0024 / 0001。
- **asyncio 消除 greenlet 技术可行但被拒**（~5x 代价 + 建连侧 SDK 无 async provider 根不掉 + 仍需叠 flag-only）——ADR 0024 被拒护栏。
- **孤儿会话不做 core reaper**，靠 AgentCore 原生 session TTL（sessionTimeoutSeconds，默认 1h、可收紧）兜底——ADR 0024「已接受代价」。
- **Midscene 无 greenlet 卡死风险**（Node 单线程事件循环），#7 只改 Nova——ADR 0024 终止契约。
- **两个引擎抢传不对称**：Nova 每 act 独立 trajectory（distinct key 幂等）；Midscene 单份增长 report（overwrite 同 key、带宽/粒度取舍 + uploader 幂等守卫冲突 + agent 引用上提）——WP3 须单独设计，见 0001。

## backlog（已评估、暂不做、留触发条件防未来重新推导）

- **preflight 不探 task-def 存在性**：`preflight_cloud_resources` 探 events 表/runs 表/桶/cluster，但**不探 task-def**（`{prefix}{engine}-worker`）。故 task-def 名维度的 prefix 配错 / CDK 未建 task-def 时，preflight 放行、跑到 RunTask 才炸（退 1、错误不点名 prefix）。**暂不加探**：CDK 本体未编码、task-def 尚不存在，现在加 DescribeTaskDefinition 探测无对象；且 task-def 名已与 ADR/code 对齐（`novaact-worker`/`midscene-worker`、container 名护栏已记 ADR 0033）。**触发 = CDK 落地后**——届时评估把 task-def 纳入 preflight「执行必需恒探」档（对齐 events 表/cluster），或确认 RunTask 失败信息够用。

- **`_read_ssm_list` 空值静默产出空 subnets/sg**（不可达加固）：`[v for v in value.split(",") if v]` 对空串 → `[]`，resolve_network 返回空 subnets → 一路到 RunTask 才被 ECS 拒（不点名 prefix）。**不可达**：真实 SSM 强制参数值最小长度 1、写入期拒空，CDK 空 StringList 部署期即被拒。**触发 = 若真遇到空 SSM 值**——顺手在 `_read_ssm_list`/`resolve_network` 对「读了却空」补 fail-fast 点名 prefix（对齐 preflight 惯例）。低频、非阻塞。

- **~~WP0 的 EventSink `EVENTS_SQS_URL` 守卫待改 DDB~~（✅ WP1-S3 已兑现）**：WP0 曾给两个引擎 EventSink 留 `EVENTS_SQS_URL` fail-loud 占位守卫。WP1-S3 已把两个引擎（Nova/Midscene 各 lib + test）换成 DDB 态真实现（`PutItem`、判据 `EVENTS_DDB_TABLE`+`RUN_ID`/`SCOPE_ID`），JobSource 同步换成 S3 态（`JOB_S3_URI`+GetObject）。grep 全净、无 SQS 残留（run-scope.ts 一处 SQS 注释也随手改掉了）。

- **~~events DynamoDB 表 IaC 归 WP2~~（✅ WP2 CDK 已建 + 真部署）**：`iac_aws_backend` 的 `EventsTable`（PK=pk/SK=seq/开 expires_at TTL）已真 deploy、`aws dynamodb describe-table` 核对 schema+TTL ENABLED。runs 表/S3 桶同批建（收编原「假定已存在」）。

- **Fargate job-in 的 S3 对象生命周期未定**：`FargateEngine.run_scope` 每 scope `PutObject` 一个 `{prefix}{scope_id}.json` job 指针对象（因 RunTask overrides 8192 上限塞不下含 feature 的 job），**当前无清理**。对称 ADR 0029 的 cloud 收尾 `_prune_empty_dirs`，这些 job 对象应有归宿。倾向 **S3 lifecycle/TTL 自动过期**（免 core 碰清理、对齐 events 表 TTL 心智），而非组合根收尾删。**触发 = WP2 真接线时定。**

- **两个引擎 EventSink DDB 态的「超时真封顶退出」跨真实边界未真跑核验**（绿≠对）：现单测（Nova MagicMock 塞 `_client`、Midscene 塞 `client`）只验 PutItem 的 Item 形状（pk/seq/body）——mock 内够。**剩两条**依赖 mock 之外的真实网络时序、绿测试不构成证据：① Midscene `AbortSignal.timeout(PUT_TIMEOUT_MS)` 是否真 abort 在途 PutItem；② Nova boto `Config(connect/read/max_attempts=0)` 是否真快速失败封顶。moto 立即返回、永不触发超时，测不了。**触发 = e2e_harness 扩展驱动真 DDB emit + 注入慢/退化网络（或 WP3-B 真容器）**——本项目亲历「退出被慢上传拖住」正是这类。（**原第③条「跨 API 层编组同构」已 fix**：`test_read_events_midscene_lowlevel_marshalling_and_numeric_seq_order` 用 Midscene 低层 `{N:String(seq)}` 线格式写 events 表、验 core Query 数值保序读出——探针证实 moto 对 DDB Number 排序/比较+跨层编组保真，属可 moto 真验、非被 mock 掉的时序。）

- **`--region`/`--profile` 贯通 worker 已实现（ADR 0016 决策 C，region 与 profile 是「正确的非对称」）**：
  - **region**：组合根 `compose.resolve_region` 落实成**具体字符串**（`--region`>`AWS_REGION`>`AWS_DEFAULT_REGION`>**profile config**）→ subprocess env + `FargateEngine` overrides + store 三处同源。**profile config 回落是关键**——Nova worker 的 AgentCore `validate_region` 不吃 profile config、要显式 region 字符串，不落实则 profile-only 用户 worker `InvalidRegionError` 崩（每 run 必经）。Nova `REGION` 去硬编码 east → None 时 fail-loud。
  - **profile**：`--profile`>`AWS_PROFILE`，**仅 subprocess 注入**（继承本机 `~/.aws`、profile 名合法）；**`FargateEngine` 绝不注入**——容器无 `~/.aws`/用 task role，注入 profile 名会 `ProfileNotFound` 盖过 task role（真跑证实，非「无害」）。这是二次 review 抓出的两个 major（profile 注 Fargate 致命 + AgentCore region=None 崩）修正后的定论。
  - 单测已锁：compose（override_env / none_preserve / 两个引擎补建对称 / midscene 不补建边界 / `resolve_region` 4 级链含 profile-config 回落）+ fargate（注 region 从不注 profile / None 不注）。
  - **e2e 真验状态**：② Fargate 容器内 task role 凭证真生效（不注 profile 后）——**✅ WP2 真部署真跑验证**（两个引擎 AI 真跑通、连 AgentCore/调模型全靠 task role，无 profile）。① profile-only 场景 worker 真 respect profile-region——**仍待**（真跑用的是显式 region 注入路径、没走 profile-config 回落那条；`resolve_region` 单测用 fake Session 锁了逻辑）。**触发 = 专门跑 profile-only（不给 --region/AWS_REGION、只配 profile）一次**。
  - **待补覆盖（minor）**：`__main__` 的 `resolved_profile = --profile or AWS_PROFILE` 优先级链无经 `main()` 的 e2e 断言（region 链已由 `resolve_region` 单测覆盖；profile 那行是 trivial `or`、且 `resolved_profile` 下游喂 store/worker 都测了）——**触发 = WP2 组合根接线时顺带补**。

- **Nova act 边界抢传类型无关化**：现 `_presend_act_siblings` 靠**硬编码文件名反推**（`.html`→`_trajectory.json`），对同 act 目录的第三个兄弟 `_traces.json`、及未来 SDK 新增的任何 per-act 文件**天生瞎**。治本 = 从 `trajectory_file_path` 取 act 目录、walk 全兄弟抢传（对齐 scope 末 flush「不按类型挑、抗 SDK 升级」）。**暂不做**：`_traces.json` 在 AgentCore backend 恒不产（`step.trace=None`）、眼下救 0 字节（YAGNI）。**触发条件**：换非-AgentCore backend、或 SDK 升级填了 `step.trace` / 新增 per-act 文件时再做。详见 ADR 0029「固有残余」条 `act_*_traces.json` 细目。

- **IAM task role 动作面靠真跑逐个暴露、非 grep 推全（绿≠对实证）**：WP2 真跑 Nova/AI 时逐轮报 AccessDenied 才补齐——nova-act 侧 `UpdateWorkflowRun`/`CreateSession`/`CreateAct`/`UpdateAct`/`GetAct`/`InvokeActStep`、AgentCore 侧 `CreateBrowserProfile`/`List`/`Get`/`SaveBrowserSessionProfile`/`ConnectBrowserAutomationStream`/`ConnectBrowserLiveViewStream`（SDK 内部调用面远比 lib 里 grep 到的大）。**已补齐、两个引擎 ×（确定性+AI）真跑通过**。**残留待做**：① 资源 ARN 仍用 `*`，真跑标定后收窄（属运维加固、非阻塞）；② Midscene 可能有未被 example.com 用例触发的动作（更复杂用例真跑时再暴露）。见 ADR 0033 IAM 表。

- **CDK 真部署已就绪、资源当前保留未 destroy**：`iac_aws_backend` 已 bootstrap + deploy 到账户 000000000000/us-east-1（默认 VPC、零 NAT），两个引擎镜像已 build&push ECR。**资源当前保留**（用户要自己玩）——DDB PAY_PER_REQUEST + S3 + 空闲 cluster/ECR 闲置几乎不计费，成本只在真跑时（Fargate + 模型 token）。清理：`cd iac_aws_backend && uv run cdk destroy -c use_default_vpc=true`，表/桶 RETAIN 需手动删。**真部署待补**：CI 构建推 ECR 流水线（现手动 build&push）、`cdk.context.json` 已 gitignore（含账户 AZ 缓存）。

- **术语统一「腿」→「引擎」已全库清零**：历史口语简称「腿」（两腿/每腿/本腿/X 那腿/单腿/跨腿）全库 30 文件 114 处统一改为「引擎」相关表述（CONTEXT.md 正式术语 = 引擎 Engine），AgentCore 特例改「AgentCore 那条路径」（非引擎、是浏览器承载层）。grep 全净、全套测试绿。

## 工作节奏（约定）

每个 WP 按「**设计冻结（落 ADR）→ 实现 → 两轮对抗 review（doc + code，workflow 分维度 finder + 对抗验证）→ commit**」走。改 code 前先落 ADR（CLAUDE.md 纪律）。commit 前两轮 review。
