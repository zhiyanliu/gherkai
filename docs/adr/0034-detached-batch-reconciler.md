# 无状态跑批：CLI 提交 → 事件驱动推进 → 轮询收集（CQRS + reconciler）

> **Status:** Accepted —— **已全部实装、local+cloud 两路端到端真部署真跑通**（落点横跨 core `project`/`reconcile`、cli `submit`/`status`、runtime `detached`、`deploy_aws` 的三 Lambda 与 Stream/EventBridge；真实 AWS 账户/us-east-1 真跑：local submit→per-run 推进→passed，cloud submit→kicker 冷启动→事件驱动链→passed，含卡死救活真验）。纠正 [0016](./0016-execution-architecture-core-lib-run-model.md)「无状态化=加 adapter+换注入、核心不动」对本能力的过强断言（见下「对 0016 的纠正」；0016/0024/0026/0031 已同步标 Partially-superseded-by 本 ADR，0030 标其「重议」条已由本 ADR 落地）。

同步 `run` 是**「CLI 阻塞跑一批」**：组合根同进程 `schedule()` 持 `ThreadPoolExecutor`、`as_completed` 收敛到全批完成才返回。本 ADR 落地的产品项（曾是产品线唯一未做项、非加固）= **「CLI 提交完就走、异步收集」**（[0016](./0016-execution-architecture-core-lib-run-model.md) v1.2 已完成 + [0017](./0017-cloud-execution-fargate-over-runtime.md) batch shape）——新增 `submit`/`status` 命令、同步 `run` 保留不变。本 ADR 定这套无状态跑批的架构、数据模型、并发/写序不变量与被拒方案护栏。

## 定位：产品价值，非加固

- **产品价值**：CI/用户 `submit` 一批用例即可离场（关笔记本、断开），run 在云上自跑到完成、结果异步收集；对照当前必须让 CLI 全程阻塞守着。
- **不做**：常驻调度服务 / WebUI（接口留好，真需要时加 adapter）；跨 run 的批队列编排（每 run 独立）。

## 核心思想：CQRS + 无状态 reconciler

把「CLI 进程持有线程池、阻塞跑完整批」换成「**events 表是唯一真值日志，一个幂等函数被事件唤醒着把整批推完**」：

- **写模型** = events 表（append-only 真值日志，[0024](./0024-worker-core-protocol.md)）。
- **读模型** = `RunState`（物化视图；**外部消费者只读它**）。
- **reconciler 机制**（投影 + 推进）= 纯从 events 推演 `RunState` + 决定启下一个 job。**无状态、幂等**：谁触发、何时触发、并发触发都安全，进程内不留任何调度态。（消歧：此处 reconciler 指 CQRS 的机制角色；同名 Lambda 只是它在 cloud 的宿主之一——kicker 与之同 code，local 的 per-run 进程/接力者跑的也是这份机制。这些宿主统称**推进器**，定义见 CONTEXT。）

**单一读接口不变量**：外部（`status` / 未来 WebUI）**永远只从 `RunState` 读状态**；`events → RunState` 的推演**只在 reconciler 一处**，不散落到各消费者（否则多份推演逻辑必漂移）。这是本设计的骨架原则。

## 数据模型三件套（职责分明）

| | 是什么 | 谁写 | 谁读 |
|---|---|---|---|
| **events 表** | 真值日志 | worker（执行事件）+ **退出观察者**（退出事件） | reconciler |
| **`RunState`** | 物化读视图 | **唯一写者 = reconciler** | 外部（`status`/WebUI）**只读** |
| **ResultStore（jobs/*.json）** | 判定真值的持久副本（events 可重放重建） | reconciler 在 finalize **CAS 之前**从同一份 events 快照落（写序 [0030](./0030-realtime-persistence-seam.md) 决定三） | CI/人（按 scope 取单 job） |
| **RunReport** | 派生产物（永远最后） | reconciler 在 finalize CAS **之后**聚合（[0027](./0027-runreport-aggregation-index.md)），失败隔离 | 人 |

## 命令形态

```
gherkai submit <features> --backend cloud
   → plan → create_run 写 RunMeta+全 pending → 打印 run_id → 退出(0)
     （只写 DDB、不起 task——冷启动交kicker Lambda，见下 cloud 端到端流程；local 则 fork per-run 进程推进）
gherkai status <run_id> [--wait]
   → 不带 --wait：读 RunState 渲染一次（**纯只读、零副作用、不 kickoff/tick**——保「查看」无惊讶 + 只需读权限）。
     读到仍 `pending` 时**只打一句诊断提示**「若已提交较久仍 pending，推进可能未启动，可 `status --wait` 接力」
     ——提示而不自动推进（决定权留用户；救活走 --wait，不给纯查看强加 invoke/起 task 权限）。**local/cloud 两路
     此渲染+提示+退出码逻辑经共享函数（`_render_status`）同一份实现、行为一致**，只 `--wait` 命令示例按后端异
     （local 用 `--report-dir` / cloud 用 `--backend cloud --prefix`）。
   → 带 --wait：轮询到终态；期间接力推进——**local=本机跑 tick 到底 / cloud=invoke kicker Lambda kickoff**
     （机制与「本机是否须跑到底」的不对称见下「推进的三个触发源」）
gherkai run <features>    # 原阻塞皮 = 同进程 schedule() 驱动循环（ThreadPoolExecutor），行为不变
```

`run` 与 `submit`/`status` 是**同一核心（纯归约 + 计划）的两种皮**——兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)「阻塞 vs 非阻塞是调用方的选择、同一核心两种皮」。但**两种皮各有自己的驱动模型、按命令分流**（见下「对 0016 的纠正」）：`run` 走 `schedule()` 的进程内 ThreadPoolExecutor 驱动循环、**不触 `reconcile.tick`**；`submit`/`status` 走无状态 reconciler。故「共享同一 reconciler」只在 `submit`/`status`（连同 kicker/reconciler Lambda——tick 四宿主一份）成立，不含 `run`。

**退出码语义分层**（演进 [0031](./0031-job-lifecycle-states-and-severity.md) 决定五「退出码读内存终值」）：`submit` 退出码 = **提交成功与否**（0=已提交、run_id 已返回；≠run 判定）；判定退出码（PASSED→0 / 其余→1）由 `status --wait` 读到终态时给出。CLI 脱离后不再有「内存 RunResult 终值」，判定退出码只能来自读回的 `RunState`。

## 端到端流程

### cloud（事件驱动，idle 零成本）

```
1. submit(CLI)：plan → create_run 写 RunMeta+全 pending 到 runs 表 → CLI 退出（run_id 已在手）。
   **只写 DDB、不起任何 task**——submit 机器权限面仅「runs 表写 + preflight 只读探活（Describe*/Get*/Head*，含 detached 链三 Lambda 存在性，[0033] preflight 条）」，不碰 ECS RunTask（冷启动由kicker Lambda 做，见下）。
1b. runs 表 Stream（**仅 INSERT 且带 `detached` 标记**）→ [kicker Lambda]：新 run 的 **STATE item 落库即触发**
     （写序契约见下，触发时 definition 必已在库）→ tick 起首批 min(max_concurrency, |jobs|) 个 task（CAS 抢占；
     max_concurrency 随 definition 到达、与部署侧 cap 取 min，见下机制四）。这是纯事件驱动链的**冷启动**（无此步则无 events/无 STOPPED，
     events Stream 永不触发第一次 reconciler）。kicker复用同一 `reconcile.tick`（四宿主一份：
     submit-local / kicker / reconciler / status 接力）。
     **filter 必须区分写入者（code-health 对抗验证逼出——只 filter INSERT 不够）**：同步 `run --backend
     cloud` 的 `RunPersistence.begin → create_run` 同样 INSERT runs 表，会误触发 kicker 对同步 run tick（CAS 抢
     job、RunTask）——与同步 schedule 的进程内执行**双开推进器**（重复起 task、真站点重复操作，moto 复现）。
     解法 = **`detached` 由组合根注入、随 create_run 写成 DDB 顶层标记属性**（`submit` 组合根传 detached=True；
     同步 `run` 不传、item 无此属性），kicker 的 event source filter 匹配 `INSERT ∧ NewImage.detached=true`——
     同步 run 的 INSERT 不命中、Stream 层直接滤掉（零 Lambda 调用，非进 handler 再判）。标记是执行环境属性、
     不进 core 模型（RunState/RunMeta 无此字段——它描述「谁推进这个 run」，非 run 状态本身）。
     **不变量的完整形态 =「推进链的每个云端 handler 只碰 detached run」，Stream filter 只堵得住其中一扇门**：
     events 表 Stream→reconciler 与 EventBridge STOPPED→exit-observer 这两条链，触发面上都区分不出写入者——
     events item / STOPPED 事件里**没有 `detached` 标记**（标记只在 runs 表 STATE item 上），Stream/rule 层无从滤；
     而同步 `run --backend cloud` 与 detached 共用同一张 events 表、同一个 cluster，故它的 worker 事件与 task 停止
     必然打到这两个 handler。**故这两半在 handler 内判**：组合根用 `DynamoDBRunStore.is_detached(run_id)`（只读
     adapter 访问器、读 STATE 顶层标记，**不进 RunStore port**——执行环境属性不进 core）在动手前分流，非 detached
     直接 no-op；判据与 kicker filter 同一真源（同一个标记）。两半的具体故障形态（reconciler 抢 claim/RunTask/
     finalize 与同步 schedule 双开；exit-observer 写的 `task_exited` 无 `body` 属性、被同步路径 events Query 读到
     即 `KeyError`）见下机制一。
     **不变量：标记挂在 `STATE` item 上，且 `create_run` 的写序 `META`→`STATE` 是契约**——kicker 由 STATE 的
     INSERT 触发，故被触发时 META（definition）必已落；若把标记挂 META，kicker 可能在 STATE 落库前就 tick，
     claim/投影全 CCF 空转（`DynamoDBRunStore.create_run` 守此写序）。
2. worker 云上跑（CLI 退出不杀 task，已实测）：PutItem 执行事件(seq 递增)→events 表；上传产物→S3
3. task STOPPED → ECS 自动发 "Task State Change: STOPPED" 事件 → EventBridge
     → [退出观察者 Lambda]（先判 detached，同步 run 的 task 停下不写）：从事件 payload 读 exitCode（实测 4/4 都带，含 SIGKILL=137；缺则落哨兵 255 + reason，见机制二「退出码缺失」条）
       → PutItem 一条 task_exited 事件(独立键空间 + exitCode[+reason]) 到 events 表
4. events 表变化 → DynamoDB Stream → [reconciler Lambda]（先判 detached，非 detached 整体 no-op）：
     ① 读该 run 全量 events → 纯推演完整 RunState
     ② HWM 条件写落 RunState（挡 stale 覆盖）
     ③ running<max_concurrency 且有 pending：CAS(pending→running) 抢一个 → RunTask 启下一个
     ④ 全 job 终态：同一份 events 快照 → 落各 job 判定真值（ResultStore）→ finalize CAS 写总 status（commit point）
        → 聚合 RunReport（派生、失败隔离）。写序 [0030](./0030-realtime-persistence-seam.md) 决定三：CAS 前失败可重试、CAS 后失败无人重试
5. 级联：下一 task STOPPED → 再触发 3-4 → … 直到全 done
```

**idle 时零成本**：无 task 状态变化 = 无事件 = reconciler 零调用（EventBridge/Stream 事件驱动，非定时轮询——[CLAUDE.md「工作方式」：交付物运行成本是设计约束](../../CLAUDE.md)）。

### local（对称，无 ECS/Lambda）

```
submit(CLI) → setsid fork per-run 进程 → CLI 退出
per-run 进程（观察者+reconciler 三合一）：spawn worker 子进程
   · 读 worker 的 fd3 事件流、旁路落本地持久 events sink（SQLite，替易失 FD3 pipe）
   · proc.wait() 拿 exitcode 写 task_exited · 推演写本地 RunState · 启下一个 · 全 done 自退
```

**同一份 core 推演码，两个宿主（Lambda / per-run 进程）各注入自己的 adapter**——local/cloud 对称落到 events 通道：两侧 reconciler 都从持久 events 重放推演，**唯一差别是存储介质**（DDB 表 vs 本地 SQLite）+ **谁把 worker 事件写进该存储**（cloud=worker 自己 PutItem，[0024]；local=per-run 进程读 worker fd3 后旁路落 SQLite）。

**关键：local 的 worker 不改、对 SQLite 无知（实装校准）**——worker 仍讲 [0024](./0024-worker-core-protocol.md) fd3 协议吐原始 JSON 行（引擎无关、两执行环境同一份 worker），SQLite 落库是 per-run 进程侧 `SubprocessLauncher` 读 fd3 时旁路做的（存原始行 + 按到达序赋 worker 段单调 seq）。故「worker 写持久 events 存储」在 local 的准确表述是「per-run 进程代 worker 写」——worker 业务零改，对称性落在「事件最终进了持久可重放存储」这一层，非「worker 自己写哪」。

**per-run 进程内多 worker 并发写同一 SQLite 的串行化（实装处理）**：`max_concurrency>1` 时 per-run 进程并发起多个 worker，每个一个 fd3 读线程往同一 SQLite append。SQLite 单写者——多线程 append 靠 **WAL 模式 + 短事务**串行化（写争锁排队、不丢不乱；每条 append 是独立小事务）。这是 per-run 进程内的线程并发（非跨进程），锁竞争轻、可接受。**跨进程写 events sink 的并发**：正常态只有 per-run 进程一个写者；但 per-run 进程崩后 `status --wait` 接力**会自己 spawn worker、写同一 SQLite events sink**（local 无云端 Lambda 起 worker，接力只能本机顶上——见下「三触发源」的 local/cloud 不对称）。两者不会真并发写（per-run 崩了 status 才顶上、串行接替），且 SQLite WAL 跨进程写锁本就串行化；但设计上假定「同一时刻至多一个本机进程在推 local run」（per-run 或接力的 status，不同时）。

## 推进的三个触发源（都幂等、并发安全）

1. **主力**：cloud=DDB Stream 事件（runs 表 INSERT→kicker 冷启动 / events 表→reconciler 级联推进）/ local=per-run 进程——正常一路推完。
2. **兜底/接力**：`status --wait`——per-run 进程崩、或 Stream 偶发断链/丢投时，人来查即接力推（状态全持久、tick 幂等，断点续）。**local 与 cloud 的接力机制本质不对称（关键，勿混）**：
   - **local 接力 = 本机进程亲自跑 tick**（spawn subprocess worker、读 SQLite、finalize）。**推进全靠这个本机进程**——掐掉即停（local 无云端接管者）。故 local 必须**有本机进程真跑到终态**：要么 submit fork 的 per-run 进程，要么 per-run 崩后 `status --wait` 顶上、且**必须一直 wait 到底**。
   - **cloud 接力 = 检测卡住才异步 fire-and-forget invoke kicker Lambda**（`InvocationType=Event`、不等返回）。**kickoff（秒级）即完成救活**——此后即便退出 `status`，云端 Lambda 链（kicker起首批 → events Stream → reconciler）自接管跑完，**不依赖本机 status 进程存活**。**「检测卡住」= 状态连续 K 轮无变化才踢**（记住上轮 `(status, high_water_mark)`，连续 K 轮不变→判卡住→invoke 一次→重置）——**非每轮无脑踢**：run 正常推进（hwm 在涨/态在变）时一次都不踢，只在真卡住（冷启动丢投卡 pending、或中途丢投卡 running）时踢。避免正常路径下 N 次无效 invoke（kicker tick 发现无 pending 即 no-op、白白重放读 DDB）——对齐「零空转、只在真需要时动」的事件驱动精神（[CLAUDE.md「工作方式」：交付物运行成本是设计约束]，同否决定时器轮询的理由）。检测是纯客户端内存比较、零额外 AWS 调用/权限。保 status 机器零 ECS 权限（起 task 走 Lambda 角色）；Lambda 名从 `--prefix` 推理、用户无感。
   - **一句话**：cloud「kickoff即可离场」/ local「本机必须跑到底」。根因在**主推进器位置**（cloud 云端 Lambda / local 本机进程，见 1.）——三触发源「齐备」是表层对称，「本机是否必须跑到底」才是里层不对称。
3. 三者同时触发也无害——靠下面 CAS + HWM 条件写。**`status` 对 cloud 是可选的查看+崩溃kickoff（非推进链必需环，云端链才是）；对 local，per-run 崩后 status --wait 是唯一本机推进者、此时反而是必需环**。

## 四个关键机制（均已实装：机制二/三/四有地基实测支撑，机制一从 [0024](./0024-worker-core-protocol.md) seq 不变量推导、独立键空间存取由单测覆盖 `test_sqlite_event_log`/`test_cloud_reconcile`）

### 机制一：`task_exited` 用独立键空间（不入 worker 数值 seq 段）

退出观察者**不持有** worker 的 seq 计数器（[0024](./0024-worker-core-protocol.md)：seq 单进程串行自增、无分布式协调）。若 `task_exited` 塞进 worker 的连续数值 seq 段，DDB 最终一致读会算错 max seq → 撞号**覆盖 `scope_done`**（裸 PutItem 无条件写），或造空号让 adapter 断号检测死循环。**故 `task_exited` 用独立键空间**，adapter 的单调 seq/断号检测只跑 worker 的连续 seq 段，退出事件旁挂不入流。**两侧落地形态（实装）**：cloud events 表 SK 是 NUMBER（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 events 表），**字符串前缀（`exit#` 之类）结构上不可行**——护栏记此，别再往 NUMBER SK 上设计前缀；改用**保留高位数值 SK**（`10**18`，worker seq 从 1 递增、永不到它）+ 属性 `item_type='exit'`。local SQLite 用**独立 `exits` 表**（不占 events 表的 `(scope_id, seq)` 键空间）。worker「每 PK 单写者、seq 单进程自增」不变量**原样保留**——events 表只是多了一个**独立键空间**的第二写者（演进 [0024](./0024-worker-core-protocol.md)，见下）。

**独立键空间只对无状态路径的读端存在**：exit item 只有 `pk/seq/item_type/exit_code?/timed_out?/reason?`、**无 `body` 属性**（它不是一条 [0024](./0024-worker-core-protocol.md) 事件行），故只有按 `item_type` 分流的 `DdbEventLog.records()` 认得它；同步 `run --backend cloud` 的读端（`FargateEngine` 的 events Query 轮询与最终 drain，[0024](./0024-worker-core-protocol.md)）按「每个 item 都是事件行」取 `body`，读到 exit item 即 `KeyError`（真跑前以假 events 表实测确认）。**故不变量是「exit item 只许落在 detached run 的 PK 上」**——exit-observer 写之前必须分流 detached（同步 run 的 task 与 detached 共用一个 cluster、必触发同一条 EventBridge rule，见上端到端 cloud 1b 的 handler 侧分流），且这些 item 对同步路径本就是无人消费的垃圾（同步路径不用 `DdbEventLog`）。不变量守在**写端**：同步读端若再加一层「非 `body` item 跳过」只是纯加法加固，不替代写端分流。

### 机制二：退出事件由平台侧观察者提供，从事件 payload 读 exitCode

**退出绝不能 worker 自报**：worker 可能被 SIGKILL 硬杀、或发完 `scope_done` 才在会话释放时非 0 退出——它**没机会**再 PutItem 报告自己的退出。故「进程干净终止」的信号只有平台/父进程看得见：cloud = ECS Task STOPPED 事件；local = per-run 进程 `proc.wait()`。观察者从该信号取 exitCode 写 `task_exited`。

**「两件都要」（[0024](./0024-worker-core-protocol.md) 终止契约）在 reconciler 里成为对事件日志的纯谓词**——但**「内容完整（scope_done）」只对声称成功（exit==0）的进程要求**（真跑 crash worker 逼出的精确化）：

- **`task_exited` 且 exit≠0（崩溃/网络码 80/SIGKILL）→ ERROR 终态，不等 `scope_done`**：worker 崩了根本没机会发 `scope_done`，此时**进程非干净终止本身就是终态信号**。若仍死等 `scope_done`，crash job 永远 RUNNING、reconciler 死循环（真跑 crash worker 复现，回归护栏 `core/tests/test_project.py::test_crash_no_scope_done_nonzero_exit_is_error`）。这一分支也覆盖「发完 scope_done 又非 0 退出」的误报 PASSED（exit≠0 一律 error，不看内容）。
- **`task_exited` 且 exit==0 → 要求 `scope_done`**：干净退出才谈「内容完整」。有 `scope_done` → scenario 归约终态（passed/failed/error）；干净退出却没 `scope_done`（矛盾：进程说成功、内容没发完）→ ERROR（judged error 比死循环安全）。
- **`task_exited` 且退出码未知（观察者没能取到 exitCode）→ ERROR 终态**：STOPPED 事件是观察者的**唯一一次机会**（ECS 不会为补码再发一次事件），「等观察者补」在事件驱动模型里结构上不存在；退出码未知即不可判定为通过，判 error 比无界等待安全（观察者侧落哨兵码，见下「退出码缺失」条）。
- **无 `task_exited`（进程还没终止）→ RUNNING（见了 scope_started）/ PENDING（还没起）**。

即：**进程终止（exit≠0）优先于内容完整判终态**；只有干净退出（exit==0）才回到「scope_done ∧ exit」的两件都要（实现见 `core.project._job_status`）。

**`task_exited` 的判定不设「已见 scope_started」前置**（code-health 对抗验证逼出的精确化）：上表按「有无 task_exited」为一级键——**零事件 + exit==0**（构造期 SIGTERM → flag-only handler 构造完成即 `return 0`，[0024](./0024-worker-core-protocol.md) 设计内行为）与**零事件 + 退出码缺失**（TaskFailedToStart，如镜像拉取失败的 STOPPED 事件无 exitCode，观察者落哨兵）都必须走上表对应分支（两者皆 ERROR），**不得因「没见 scope_started」短路成 PENDING**——PENDING 与已 claim 的 RUNNING 基线单调合并后 job 永停 RUNNING、`plan_next` 既不提议也不 finalize、run 永不收敛（探针复现：4 轮 tick 不推进且 events 不再新增、永不自愈）。回归护栏 `core/tests/test_project.py` 的 exit-without-events 真值表用例。

**launch 失败补偿——「起不来」也是一种进程终止（机制二的推论，code-health 对抗验证逼出）**：CAS 抢占成功后 `launcher.launch(job)` 可能抛异常（RunTask 放置失败/容量不足/task-def 配错/Popen OSError——其中 task-def 名配错是**确定性触发器**、每 job 必炸），此时 job 已被置 RUNNING 却永无 events、无 task_exited（进程根本没起、平台侧观察者无从观察）——若异常裸穿 tick，job 永停 RUNNING、整批不可恢复 wedge，且三触发源都救不回（「状态全持久、断点续」的可恢复性断言被推翻）；cloud 侧 Stream 重试还会因 job 已 running 而「成功」no-op、掩盖故障。**修法 = launch 的宿主（tick）扮演「起不来」这一时刻的退出观察者**：catch 异常 → `event_log.record_exit(scope_id, 非0哨兵码)` → 下轮重放走「exit≠0 → ERROR」既有谓词收敛终态。不发明新状态、不加重试（launch 级重试属 job 级重试的既有留口子）、异常不中断本 tick 其余 job（失败隔离，[0026](./0026-schedule-module.md)）。回归护栏 `core/tests/test_reconcile.py::test_launch_failure_does_not_wedge_run`。

**退出码缺失：观察者落哨兵、不留宽限态（修正）**：本 ADR 最初把「STOPPED 但 exitCode 未落值」定义为有界宽限态（投影保守 RUNNING、观察者"短暂重查 DescribeTasks"兜底），根据是 [0024](./0024-worker-core-protocol.md) 记的 `lastStatus==STOPPED` 与 exitCode 落值非原子。**修正理由（code-health 对抗验证发现）**：①「补码」在事件驱动下没有第二次机会——ECS 对一个 task 只发一次 STOPPED 事件，观察者无 ECS 权限也不该有（薄 handler），所以宽限态在实装里是**无界**的；②容器根本没跑起来的形态（`stopCode=TaskFailedToStart`：拉不到镜像、缺 secret、放置失败）exitCode **必然**缺失，不是延迟而是永不——按旧表判 RUNNING 即 run 永久 wedge、三触发源都救不回。**决定**：观察者对缺 exitCode 的 STOPPED **一律落非 0 哨兵**（与上条 launch 失败补偿同一常量 `PLATFORM_FAILED_EXIT=255`，core 单点定义）并带 `reason`（`stopCode: stoppedReason`，随 `task_exited` 进事件日志、投影进 job message 让用户看到归因）；`_job_status` 对「有退出记录、非超时、退出码未知」判 ERROR（防御：老版本观察者或未知写者仍写 None 时不 wedge）。STOPPED 事件锚在 `stoppedAt`（已过落值窗口），正常退出必带码——实测 H1/H2 见地基实测节；哨兵只在容器没跑过时出现。**真跑坐实（坏镜像 tag 的 detached run）**：task-def 指向不存在的 ECR tag 提交 → STOPPED 事件 `stopCode=TaskFailedToStart`、无 exitCode → 观察者落 255 + reason → reconciler 一轮 tick 判 error 并 finalize，**提交后 2m15s run 到终态**，jobs/*.json 的 message 为「worker 未能启动或未正常结束（平台侧未取到退出码）：TaskFailedToStart: CannotPullContainerError: … not found」；同一场景在修正前的实装下 run 永久 RUNNING。**被拒**：给观察者加 DescribeTasks 重查/延迟重试——要加 ECS IAM 与调度机器，服务的却是一个实测从未出现、且对 TaskFailedToStart 无意义（永不落值）的形态。

### 机制三：`RunState` 投影写带 HWM 条件写（防并发 lost-update）

reconciler 逻辑上是「唯一写者」，**物理上是并发实例**（实测：DDB Stream 按 PK 分片、多 job 触发 2 个并发 Lambda 实例；叠加 `status --wait` 是额外触发源）。并发实例读快照时点不同：实例 A 读到 seq=10 推演 `{running}`，实例 B 读到 seq=20 推演 `{passed}` 先写，A 用旧快照后写会**覆盖终态**（把 `passed` 刷回 `running`，外部看到非单调）。全量重放保证**派生逻辑**幂等、抗乱序，但**不保证跨实例写序**。

**解法 = 两道条件写，各管一类回退，不能只用 HWM**：

- **① HWM 挡 worker 执行事件段内的 stale 覆盖**：`RunState` 带 `high_water_mark`（已处理的 worker 段 max seq）；投影写条件含 `attribute_not_exists OR :hwm >= hwm`，读到更少 worker 事件的 stale 实例写被 `ConditionalCheckFailedException` 挡掉。这管的是「A 读到 seq=10、B 读到 seq=20，A 迟到写覆盖 B」这类**数值 seq 可比**的回退。
- **② 状态机单调条件写挡终态回退（HWM 挡不住的边界，必须单列）**：`task_exited` 走独立键空间、**不带数值 seq**（机制一），故「被 `scope_done`（末 seq=5）触发的投影」与「被 `task_exited` 触发的投影」携带**相同 HWM(=5)**——`task_exited` 恰是把 job 翻终态的那条事件，单靠 HWM(`5>=5` 成立) **挡不住** stale 的 `scope_done` 投影把已 `passed` 的 job 刷回 `running`。**故 job 状态与 run 总 status 的终态转移另加一道单调状态机条件写**：`status ∈ 非终态集` 才允许写（`ConditionExpression` 断言当前非终态；终态 `passed/failed/error` 不可被任何后到的写覆盖）。finalize（run 总 status）同理单独条件写，保证 commit 恰一次、RunReport 触发幂等。

两道条件缺一不可：HWM 管 seq 可比的进度回退，状态机单调管「跨独立键空间事件（task_exited 无 seq）的终态回退」——后者正是 `scope_done`/`task_exited` 这个 finalize 边界的关键守卫。这是 [0030](./0030-realtime-persistence-seam.md)「重议」条预告的「进程外多写者需条件更新」的落地（见下反向链）。

**② 的 job 级半边落地形态（code-health 对抗验证逼出——初版只落了 run 级半边，job 级整体覆盖写曾致：同 HWM 的 stale 投影把已终态 job 刷回 running → 若 run 已 finalize 则读模型永久错乱、且重开机制四的 double-launch 窗口，探针实测 `launched=['a','a']`）**：core 侧 `project` 的 baseline 单调合并是**不充分的缓解**（纯函数管不了跨实例写序），最终守卫必须在 adapter 的写路径——local 在 fcntl 锁内逐 job 按生命周期序（`_lifecycle_rank`：pending<running<终态）与库中现态取较推进者；DDB `put_item` 表达不了 per-key 条件，拆两步：先 `update_item` 条件写标量（HWM+run 级 status 双守，CCF 即整体 stale），再对每个 job 用 `SET jobs.#sid=:js` + 「库中该 job 当前非更推进态」的单元素条件写，被挡的单个 job 静默跳过（正确态已在库）。两步非原子，但每步各自守卫、先标量后 jobs 的次序保证中间态等价于「携带旧 job 视图的合法投影」，下轮重放收敛。顺带：投影写不再携带 `started_at`（`update_item` 天然不碰未提及属性，create_run 落的起点不被抹——曾为整 item `put_item` 之疾）。回归护栏 `core/tests/test_conditional_writes.py` 的同-HWM 终态不回退/claim 不回退/started_at 保留三组对拍用例。**被拒 owner/lease 分布式锁**：0030 曾预告用 lease 保唯一写者——拒，lease 有状态、需续租/故障接管；无状态的 HWM + 状态机乐观条件写即够（写失败即整体重放重试，天然幂等），更轻。

**投影写 run 级 status 钳为 `pending`/`running`、不落终态（实装真跑逼出，衔接 [0030](./0030-realtime-persistence-seam.md) commit point）**：`project` 在全 job 达终态时会聚合出 run 级**终态**，但 `project_state`（投影写）**不能把它落库**——run 级终态是 `try_finalize` 这个 commit point 的**专属**（[0030](./0030-realtime-persistence-seam.md)：finalize 一落=run 已提交）。若投影提前落 run 级终态，紧接着的 `try_finalize`（条件「当前 status ∈ 非终态」）会被**投影自己刚写的终态挡住**、run 永远 finalize 不了。故 `project_state` 落库时**丢弃传入的 run 级值、按投影里的 job 态重算**：**投影内全 job 仍 `pending` → 落 `pending`**（这个 run 还没起过任何 job，status 如实显示「未启动」——正是上文 `status` 命令那句 pending 诊断提示的判据）；**任一 job 已 running 或终态 → 落 `running`**。两端取值都是非终态，commit point 的专属性不受影响；**各 job 态仍是真实态（含终态，供 `plan_next` 判全终态），只 run 级钳**；run 级终态由 `try_finalize` 用 `project` 聚合出的真实终态一次落定。**判据只看 job 态、不读库、也不看传入的 run 级值**：① 传入值是 `_aggregate` 的终态聚合值（滤掉 pending/running，故连全 pending 的 run 也吐 `passed`），拿它做分支等于恒落 `running`、`pending` 半边形同不存在（首版实装即如此，代码健康度复盘逮出这条永不可达的分支）；② DDB 侧的标量条件写发生在 per-job 条件写之前（那一刻库中 job 态还没更新），判据若依赖库就无法与 local 对拍。规则单点实装在 `project.projected_run_status`，cloud DDB 与 local 文件两个 RunStore adapter 共用同一份。**已知诊断窗口（非故障）**：tick 的写序是 project → `project_state` → `try_claim_job`，本 tick 刚 claim 的 job 不在本次落库的投影里——cloud 档下一次投影要等该 worker 真 emit `scope_started`（拉镜像/挂 ENI 常几十秒），窗口内库中 run 级 status 仍 `pending` 而 job 已在起，`status` 的「推进可能未启动」提示会短暂偏保守；窗口随首个事件到达自愈，不值为它把 claim 结果回灌投影（判据会从「只看 job 态」漂成「读库+看时序」）。`project_state` 另加对偶保护：库中已 finalize（run 级终态）则挡投影（不把终态刷回 running）。

### 机制四：CAS(pending→running) 控严格并发

严格 `max_concurrency` 的执行点从 core 内 `ThreadPoolExecutor`（进程内、无 store）**迁到 store 的 CAS 条件写**：起一个 job 前 `CAS(status: pending→running)`，多个触发源并发看到同一 pending job 都想启，**只有条件写成功的那个去 RunTask/spawn**，其余被拒跳过。稳态并发恒 = max_concurrency，不靠任何常驻进程 hold 线程池。core 的 `plan_next` 只**提议**动作，真正的并发闸是 adapter 的 CAS。

**`max_concurrency` 随 definition 走 + 推进器侧 cap**：`RunMeta.max_concurrency` 是 definition 的一部分（载体惯例同 `extra_http_headers`：run 级执行参数、omit-when-None、core 只搬运不消费——消费者是各组合根），`run`/`submit` 都落值。推进器侧取值 = **`min(meta 值, 部署侧 cap)`**：cloud 的 cap = reconciler/kicker Lambda env `MAX_CONCURRENCY`（IaC 设；语义是**部署侧 per-run 上限**——task 跑在部署方 cluster、计入部署方账单，cap 保部署方的总量控制权）；meta 缺失（旧 definition）按 1（与打通前行为一致）。**local（两种跑法）无 cap 层**：worker 与推进进程都跑在提交者自己的机器、以提交者自己的凭证计费——提交者即资源买单方，无第二方需要保护；cap 只存在于「提交者与部署方分离」的 cloud 档。local detached 的 per-run 进程与 `status --wait` 接力者**同读 meta**（flag 仅作 meta 缺失时的回落）——顺带修正一处曾有的不一致：接力者曾用 `status` 自己的 flag 值、可能与 `submit` 时不同。同步 `run` 的 `ScheduleOpts` 仍直用 CLI flag（同进程、无通道问题；meta 照落，保 definition 诚实）。**多 job 并行不引入新并发面**：events 表跨 job 零共享键（PK=run_id#scope_id、每 PK 单写者不变），STATE 的 CAS/HWM/生命周期序条件写本就为多触发源并发设计（机制三/四），local 档 mc>1 早已真跑同一套 core 逻辑。
**曾反其道（决策反转记录）**：此值曾按档分层——cloud 档以 Lambda env 为唯一真源、`submit --max-concurrency` 静默不生效（当时留了「真出现同一部署下不同 run 要不同并发的需求，再议纳入 definition」的口子）。支撑假设「同一部署下各 run 无理由不同」被真实使用证伪：不同 run 的并行度本就随 feature 的 scope 结构不同，「静默不生效」是可用性缺陷、不是可接受边界；原论证里「资源闸属部署方」的正确内核收进 cap 语义。**同族对照**：`--report-dir` vs 推进器 `REPORT_DIR` 从一开始就不留静默分岔——它决定产出写到哪，分岔的后果是「跑完了但用户在自己给的前缀下找不到结果」，preflight 比对两侧、不一致退 2（[0033](./0033-iac-aws-backend-and-composition-wiring.md) preflight 条）；并发这条打通后，完全失效的形态已消除；声明超 cap 时按 cap 执行、提交时 preflight 提示（按 cap 跑是 no-op 分岔→提示即可，对照 `REPORT_DIR` 的退 2——判据 = 分岔后果）。

**「claim 了但 events 还没到」的窗口 → `project` 须以 RunStore 态为基线做单调合并（实装真跑逼出、补入设计）**：CAS 把 job 置 `running` 后、worker 还没 emit `scope_started` 前有一个窗口——此时 `project` 全量重放 events 里**看不到**该 job（无任何事件），会把它算成 `pending`；若投影写就此把它刷回 `pending`，下一个 tick 的 `plan_next` 又会提议 start、CAS（此刻已是 running？不，被刷回 pending 了）又成功 → **重复 launch 同一 job**（真 bug，回归护栏 `core/tests/test_reconcile.py::test_tick_idempotent_no_double_launch`）。故 `project` 除 events 外**接收当前 RunStore 的 `RunState` 作基线**，job 态按生命周期序（`pending < running < 任何终态`）与基线取**较推进者**、单调不倒退：已 claim 的 `running` 不被 events 的 `pending` 覆盖；终态一旦达成不被 `running` 覆盖。这与「全量重放幂等」不冲突——重放仍是纯推演，基线只提供「已 claim」这一 events 之外、却是 RunStore 权威的事实。`reconcile.tick` 在调 `project` 前 `load_run_state` 取基线传入。

## job timeout（产品级设定：两层声明 → definition 载体 → 三路推进器各自 enforce）

**产品语义**：job timeout 是用户对「一个 job 最多跑多久（墙钟，含启动开销）」的预算，属 run 的 definition、与推进方式（同步/detached）无关。此前它只在同步路径实现了一半（`--timeout` 是 ScheduleOpts 运行参数、不进 definition），detached 路径完全没有——local 挂死永 running、cloud task 无限跑、计费失控（经 grace 校准适用面复盘发现，[0032](./0032-fargate-execution-environment.md)「适用面注记」）。

**两层声明、tag 优先**（复刻 `@engine`/`--default-engine` 同构模式，[0019](./0019-feature-tags-scope-and-engine.md) tag 体系扩展）：feature 层 scope 级 `@timeout:N`（秒，N>0，同 scope 声明不一致 → PlanError——同 `@engine` 冲突先例；用例内容决定预算主体、QA/TE 在用例旁声明）+ CLI 层 `--default-job-timeout`（未标 tag 的 job 用它兜底；`<=0`=不超时）。**flag 命名两个前缀都承重**：`default-` 防「误当强制值、被 tag 覆盖时错愕」；`job-` 消歧对象（act 级 `ACT_TIMEOUT_S`/将来可能的 run 级总预算并存，留 `--default-run-timeout` 对称位）。原 `--timeout` 已改名、未留 alias。**先不做**（防过度设计）：run 级总墙钟预算；「CI 强制收紧压过 tag」层（真实冲突出现再议）。

**载体 = definition**：两层在组合根解析定值后固化进 `Job.timeout_s`（None=不超时），随 RunMeta 持久化——推进器只认它，`ScheduleOpts.job_timeout_s` 退役（缺省解析在组合根一次完成，core 不复制两层逻辑）。worker 不消费 timeout（enforce 全在推进器侧，worker 只需继续守 flag-only 停止契约）。

**enforce 统一形态 =「launch 时挂到点回调；到点若未终态则 stop；stop 后走既有退出观察链收敛」**，三路各自落地：

| 推进器 | 到点回调 | stop | 收敛 |
|---|---|---|---|
| 同步 `run`（schedule） | 进程内 per-job deadline（原机制，改读 `job.timeout_s`） | `handle.stop(grace)` | 原路径：error+timeout |
| local detached（per-run 进程） | `SubprocessLauncher` 起 timer 线程 | `handle.stop(engine_min_grace)` + 置本 scope timed_out 标志 | worker 协作退 → `_pump` 写 `task_exited(timed_out=True)` → project 判 ERROR+timeout |
| cloud detached | **EventBridge Scheduler one-time schedule**（claim 后 CreateSchedule，`at = claim+timeout`、`ActionAfterCompletion=DELETE` 自动清）→ 到点 invoke kicker（payload 带 `timeout_scope`） | 仍 running 才动手：`ListTasks(cluster, startedBy=run_id)` **同时列 RUNNING 与 STOPPED**（后者 ECS 保留约 1h）→ `DescribeTasks` 按 overrides env `SCOPE_ID` 匹配（同 exit_observer 提取术）→ 按 task 状态分三路：**在跑** → `StopTask(reason 含哨兵串 gherkai-job-timeout)`；**正在停止**（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不动、等观察者（曾只列 RUNNING、把它判成「无踪」直写 timed_out，与几秒后到达的真退出记录同键互覆——恰在预算点跑完的 passed job 可被终判成 timeout，code-health 对抗验证发现）；**已 STOPPED 而无退出记录**（STOPPED 事件丢投）→ 从 DescribeTasks 的 task 对象用与观察者**同一提取函数**（`exit_from_task`）落真退出记录（同内容、同键幂等）；两个列表都无踪才直写 `timed_out` | worker 协作退 → exit_observer 见 `stoppedReason` 哨兵 → `task_exited(timed_out=True)` → 同上 |

**best-effort 边界**：CreateSchedule 失败不阻塞 launch（保护降级为 tick 防御扫 + status --wait，打日志）；schedule 到点时 job 已终态 → tick no-op（幂等）。

**武装先于 RunTask**：起 task 失败时 tick 会补偿 record_exit，但若补偿也失败（双失败）job 永停 RUNNING——先建的 schedule 到点仍收敛，最后兜底不因 launch 失败缺位；失败 launch 留下的 schedule 到点走 no-op/直接收敛并自动删，零残留。

**`timed_out` 归因链**：`TaskExited.timed_out`（退出记录新字段，独立键空间内的属性、不动键结构）——local 由 launcher 标志传入；cloud 经 **StopTask 的 `reason` 参数原样出现在 STOPPED 事件 `detail.stoppedReason`** 这条现成通道传递（零新键空间/零新事件类型）。`_job_status` 见 timed_out → ERROR，`_reduce_scope` 归因 `error_type="timeout"`——与同步路径归因语义对齐（超时是主动中止、非引擎故障，但按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定一超时记 error+timeout）。

**`JobState.claimed_at`**（`try_claim_job` 时写，机制四扩展）：① local 接力（per-run 崩后 `status --wait`）据此恢复 deadline——自家新 claim 的 job 有 timer；**他人 claim、无 handle** 的 RUNNING job 超预算（+余量）且无退出记录 → 观察链已死（timer 随 owner 进程丢、worker 因 fd3 断管随之早亡）→ 直接 `record_exit(timed_out=True)` 收敛（不与下方被拒方案「处置者直接写 task_exited」冲突：那条拒的是**有活观察链时**绕过它；若 owner 尚活，其 timer 同一 deadline 早已触发、真退出记录同带 timed_out，后到覆盖归因不变）；② cloud tick 的**防御性顺带扫**——任何 tick 对 running 且 `now-claimed_at > timeout` 的 job 走同一超时处置（Scheduler 的双保险：CreateSchedule 失败/schedule 丢失时，后续任何事件触发的 tick 都能补救）；③ status 可显示已跑时长。timeout 从 claim 起算（含拉镜像等启动开销——简单可预期，文档写明）。

**与「idle 零成本」的关系**：one-time schedule 到点即删、无常驻轮询；**bonus**——到点 invoke 本身是一次强制 tick，等于每个 job 至少在 timeout 时刻被推进一次，顺带部分兜住「事件丢投级联断裂」（重议闸门首条的场景）。

**被拒方案（护栏）**：
- 常驻低频 rate rule 轮询——违「idle 零成本」，且粒度粗、空转扫描多。
- 动态 enable/disable rate rule（重议闸门预案挪用）——多 run 并发下 disable 有竞态（A finalize 查「无其他 running」与 B 刚 submit 的 enable 无原子性，交错可致规则停在 disabled、B 失去保护），状态管理复杂度不值。
- 纯 tick 内时长判定（不加时间触发器）——静默 job 无事件 → 永不 tick，盲区恰是最需要超时的场景（卡死）。已作为**防御性补充**保留（见 claimed_at ②），非主机制。
- `JobState` 存 task ARN 供 StopTask——`startedBy=run_id`（≤36 字符）+ DescribeTasks env 匹配已够、改动更窄；ARN 属执行环境句柄、暂不进读模型（真需要时再议）。
- 超时时由处置者直接写 task_exited——进程未退、会与 observer 的真退出记录同 key 相互覆盖；stop 后让既有观察链自然收敛才是单一真源。

## core 拆分（守 [0026](./0026-schedule-module.md)/[0016](./0016-execution-architecture-core-lib-run-model.md) 窄腰红线）

```
core（纯函数，不 import boto3，local/cloud 共用）：
   project(RunMeta, events, baseline RunState) → RunState   # 纯归约，全量重放，幂等抗乱序；与基线按生命周期序单调合并（见上「claim 了但 events 还没到」条）
   project_full(RunMeta, events) → RunResult                # 派生完整结果（报告/产出）用
   plan_next(RunState, max_concurrency) → [Action]  # 纯决策：该启哪些 pending、是否 finalize
adapter/组合根（Lambda handler / per-run 进程，注入具体 client）：
   CAS 写 / RunTask / PutItem(task_exited/finalize) / RunState 落库   # 所有副作用在此层
```

**core 只吐「当前状态」与「建议动作」，绝不持 store、不 import boto3、不依赖执行环境。** Lambda handler 是 cloud 组合根（cold-start 读 env 造 adapter 注入纯 reconciler——**仍是组合根注入，不是 ports 内部 env-sniff 全局单例**，[0016](./0016-execution-architecture-core-lib-run-model.md) 禁的 GlobalConfigManager 反模式要在评审时守住别退化成它）；per-run 进程是 local 组合根。归约码作纯 core 函数被两宿主 import 复用 = 「不复制归约逻辑」的正解。

**时钟也只一份：三宿主（前台 `run` 的 CLI / local per-run 进程 / 推进器 Lambda）落库时间戳一律调 `compose.now_iso()`**，反向解析一律 `compose.parse_iso()`（core 不取时钟——时间戳由组合根算好传进 `tick`/`finalize_report`，[0016](./0016-execution-architecture-core-lib-run-model.md)）。曾各写一份 `_now_iso`、两种 ISO 格式（`isoformat()` 的 `+00:00` vs `strftime` 的 `…Z`），使**同一份 RunState 内** `started_at`（submit 侧写）与 `claimed_at`/`ended_at`（推进器写）格式不同——`status --json` 按 backend 给出不同格式的同名字段，机读消费者被迫兼容两种。「不复制归约逻辑」同理适用于「不复制取时钟」：多宿主同写一份数据结构时，**格式真源必须唯一**。

## Engine port 演进：pull-iterate → 增出 fire-and-forget（已实装）

`Engine.run_scope(job) → (WorkerHandle, Iterator[Event])` 是 **pull 式**（调用方线程迭代事件流；FargateEngine 为满足 `Iterator` 而在线程内轮询 DDB），**同步 `run` 路径仍用它、不变**。无状态路径是 **fire-and-forget**：worker 自写持久 sink、观察者补 `task_exited`、reconciler 读表——不再有「调用方持续迭代」。**实装形态**：`FargateEngine` 增出 `start_scope(job) → task_arn`（只 PutObject job + RunTask、不返事件迭代器）；`run_scope` 与 `start_scope` 共用抽出的 `_put_job_and_run_task`（起 task 单一真源）。**未改 `Engine` Protocol 本身**——`reconcile.Launcher` 是无状态路径专用的注入口（local=`SubprocessLauncher` 起子进程旁路落 SQLite / cloud=`CloudLauncher` 经 resolver 选 FargateEngine 调 `start_scope`），故 core 的 `reconcile.tick` 只认 `Launcher.launch(job)`、对「怎么起」无知，不必给 `Engine` Protocol 强加 `start_task`。**起 task 的能力（subprocess spawn / ECS RunTask）收进注入的 Launcher/Engine，core 绝不 import boto3/ecs**（reconcile.py 只 import core.model/ports/project）。

**`raw_sink` 的定位（local 档 fire-and-forget 的配套，同样不进 port 契约）**：local 无状态路径没有「平台侧 events 表」，事件行由 `SubprocessLauncher` 后台线程从 fd3 旁路落 SQLite——机制是 `SubprocessEngine.run_scope(job, raw_sink=...)` 这个**该 adapter 独有的扩展形参**（读到的每行原始 JSON 解析前回调；`FargateEngine.run_scope` 无此形参）。与 `start_scope` 同理**不上提到 `Engine` Protocol**：它是「local 怎么把行落库」的实现手段，不是所有 adapter 都该有的能力（cloud 侧 worker 自写 DDB，没有对应概念）。**代价与守法**：这使 local 无状态路径**绑死具体 adapter**——故该路径的注入口（`SubprocessLauncher.__init__` 的 resolver、launch 内取到的 engine）**类型标注一律收窄到 `SubprocessEngine`**，让绑死在类型上显形；若标成宽泛的 `Engine`，则「port 契约里没有 raw_sink」这件事被隐藏，换 adapter 只在运行时 `TypeError`（`core/gherkai_core/ports.py` 的 `run_scope` docstring 同处留了这条边界）。

## 对 [0016](./0016-execution-architecture-core-lib-run-model.md) 的纠正：「核心不动」是过强断言

[0016](./0016-execution-architecture-core-lib-run-model.md) 数处（「这样上云…核心与接口不动」条、版本切分 v1.1.0 行、「现在不做」条）断言「无状态化 = 加 adapter + 组合根换注入，核心与接口不动」。**本 ADR 纠正为分层两真值**：

- **(a) store/engine 后端替换**（local↔DDB/S3、subprocess↔Fargate）= 注入、核心不动——[0033](./0033-iac-aws-backend-and-composition-wiring.md) 已真部署真跑证实，**保留**。
- **(b) 无状态提交-收集**（本 ADR）= **驱动模型演进**：同步 `ThreadPoolExecutor` 循环解体为无状态事件驱动 tick、抽纯 `project()`/`plan_next()` 供两宿主复用、可能增 Engine port 形状、严格并发从进程内线程池迁到 store CAS——**核心与接口要动**。这比「只换 adapter」大得多，[0016](./0016-execution-architecture-core-lib-run-model.md)/[0026](./0026-schedule-module.md) 把 (a)(b) 混为一谈、over-claim 了。

存活的是**纯归约器**（`project`），消失的是**同步驱动循环**（ThreadPool/as_completed/abort_flag/fail-fast `_stop_all`/进程内并发闸）——后者在无状态路径重新宿主为 reconciler。同步 `run` 路径仍用现驱动循环（两种驱动模型并存，按命令分流）。

## 地基实测（2026-07-19，真实 AWS 账户/us-east-1；6 个真 Fargate task——其中 4 个构成 H1 退出场景矩阵——+ 真 DDB Streams/条件写；临时 PoC 脚手架验后即清、未入库）

moto 立即返回测不到事件投递/并发时序，健康网真跑不触发这些路径——故下列是「绿≠对」边界的唯一有效证据：

- **H1 事件 payload 带 exitCode（4/4，含最硬的 SIGKILL 截断）**：正常退出 exitCode=0→payload 带 0；缺 job 非 0 退出=1→带 1；StopTask 软停=0→带 0；**忽略 SIGTERM 的 sleeper 被 SIGKILL 硬杀=137→payload 仍带 137**。结论：观察者从 STOPPED 事件读 exitCode 可靠（事件锚在 `stoppedAt`、已过 exitCode 落值窗口）→ 机制二「极薄观察者」成立、机制二兜底降为防御性冗余。
- **H2 延迟**：EventBridge→Lambda 投递 **0.6s**（近瞬时）；但端到端「worker 真停(`executionStoppedAt`)→可归约」= **~27s**，瓶颈全在 ECS 平台 `executionStoppedAt→stoppedAt` 清理开销（STOPPED 事件锚在 `stoppedAt`）。放大了 [0032](./0032-fargate-execution-environment.md) 记的 ~11s 平台滞后。**级联每步有 ~20-30s 固有尾延迟**——对异步跑批可接受，`status --wait` 会有此尾延迟，属已知特性。
- **H3/机制三/四 并发写序（真 DDB）**：HWM 条件写——B 写终态(hwm=20)后 A 用旧快照(hwm=10)迟到写被 `ConditionalCheckFailedException` 挡、终态未被刷回 running；同 hwm 重复写幂等。**DDB Streams 并发度=2**（4 job 触发 2 个并发 Lambda 实例）→ 坐实「并发 reconciler」前提真实、HWM 条件写用得上；**同 PK 严格保序**（每 job seq `[1..5]` 按序到达）。

**已补真验**：`status --wait` 接力 + Stream 丢投 → **已真验**（复现法与结果见「重议闸门」丢投条）；`setsid` local 脱离 → **已真验**（local submit → per-run 进程脱离 CLI 后台推进 → CLI 退出后 status 读到 running/passed）；四机制 → core 单测（`test_reconcile.py`/`test_cloud_reconcile.py`/`test_project.py`）+ local/cloud 端到端真跑覆盖。仍留未做项见下「重议闸门」（如 Stream 长期丢失率的量化、动态定时兜底规则）。

## 被拒方案（护栏，防未来重踩）

- **让 worker 自报退出事件**（省掉平台侧观察者）：拒——worker 可能 SIGKILL/崩溃/发完 scope_done 才退，没机会自报；「进程干净终止」本质只有平台/父进程可见（机制二）。
- **`task_exited` 共享 worker 数值 seq 段**：拒——观察者无 worker 的 seq 计数器，Query-max-then-write 撞号覆盖 `scope_done` / 造空号破断号检测（机制一）。
- **reconciler 靠全量重放天然幂等、投影写不加版本守卫**：拒——并发实例 stale 快照 lost-update 能把 finalized run 刷回 running；全量重放只保证派生幂等、不保证跨实例写序（机制三）。
- **把 CAS+RunTask+PutItem 与归约合成单一 core reconciler 组件**：拒——逼 core 持 store + 依赖执行环境、Engine port 长出启 task 职责，破 [0026](./0026-schedule-module.md) 纯 reducer（core 拆分节）。
- **让每个消费者各自 `project(events)→RunState`（绕过单一 reconciler 写者、如为求新鲜度让 `status` 直接投演 events）**：拒——多份推演逻辑必漂移（同一 events 在 status/WebUI/reconciler 各推一版、口径迟早分叉）；且各消费者写 RunState 会破单写者与 HWM/状态机条件写前提。外部只读 RunState、推演只在 reconciler 一处（「核心思想」单一读接口不变量）。
- **cloud submit 由 CLI 直接起首批 task（冷启动）**：拒（实装初版这么做、后改）——让 submit 机器背 `ecs:RunTask` 权限，与本设计卖点「提交完就走、只需提交那一下的最小权限」相悖：submit 机器权限面越小越好（受限 CI runner / 临时凭证场景）。改由**kicker Lambda** 冷启动（见下），submit 机器权限收窄到只剩「runs 表写 + preflight 只读探活」、无任何 ECS 写/执行权限。
- **runs 表 Stream 直接触发 reconciler（复用同一 Lambda 做冷启动）**：拒——**自触发放大**：reconciler 每次推进都写 runs 表（`project_state` 条件写 + `finalize`），若 runs Stream 触发 reconciler，则它写 runs → 又触发自己 → 每个 run 生命周期空转 N 次（tick 幂等使无害、但持续无效唤醒 + 全量重放读放大）。改用**独立的 kicker Lambda 接 runs Stream**——**注意它不是「薄 Lambda」**（那是退出观察者的形态）：kicker 与 reconciler **同一份 code、同一套装配与权限**，只换 handler 与触发源，起 task 的 tick 同样写 runs 表（`project_state`/`try_claim_job`/`try_finalize`）。故拒的实质**不是「kicker 更轻」，而是「别让主推进器订阅它自己写的表」**；隔成专用 Function 换来的是**触发面干净**：kicker 的 event source mapping 带 `INSERT ∧ NewImage.detached=true` filter（见上端到端 1b——该 filter 是必需项、非「用 filter 补救耦合」），只被「新 detached run 落库」唤醒；reconciler 只被 events Stream 触发（worker 有进展才推进），它自己写的 runs 表 MODIFY 流不叠回任何推进器。kicker 另接 `status --wait` 的直接 invoke kickoff 与 Scheduler 超时到点 payload（见「三触发源」/「job timeout」节），职责是「让 run 动起来」、非「只起首批」。
- **定时器轮询推进**（EventBridge scheduled rule 每 N 秒 tick）：拒——idle 也 fire、空转计费，且要权衡「间隔短=延迟低但费 / 间隔长=省但收尾慢」这个不该存在的取舍。改用 ECS Task State Change + DDB Stream 事件驱动，idle 零调用（端到端流程 cloud）。
- **per-run 推进器也给 cloud**：拒（用户定）——cloud「扣笔记本下班」场景只靠 IaC 部署的事件驱动链，本机不留常驻推进器；per-run 仅 local 用。

## 重议闸门

- **Stream/事件偶发丢投致级联断裂成真痛点** → 加安全网：submit 时 enable、finalize 时 disable 的**动态定时兜底规则**（仅在有活跑批时低频轮询、真 idle 时规则禁用=仍零调用），比常开定时器省。当前靠 `status --wait` 接力兜底，先不做。
  - **cloud 冷启动/中途丢投由 `status --wait` 无感接力兜底（实装真跑遇到、已解决）**：任何事件丢投（首个 runs-INSERT 漏 → 卡 pending、无第二触发源踢；或中途 events 丢投 → 级联断）都由 cloud `status --wait` 兜底——接力机制（检测卡住才踢、kickoff 完即可离场）见上「推进的三个触发源」2. 的 cloud 半。**权限面**：踢 Lambda（非本机 tick）保「status 机器零 ECS 权限」——起 task 走 Lambda 的角色（有 RunTask/PassRole），status 机器只需 `lambda:InvokeFunction`。**kicker 名从 `--prefix` 确定性推理**（`{prefix}kicker`，复用 `names` 单一命名真源、cli↔IaC 同源，ADR 0033）——用户无需配、无感。幂等安全：invoke kicker，正常在跑时 tick 发现无 pending 即 no-op（CAS 挡重复起 / HWM 挡 stale，真 DDB 验过），卡住时救回。**卡死救活已真验（确定性复现）**：临时禁用 kicker 的 runs-Stream event-source-mapping 模拟丢投 → submit 必卡 pending（kicker 收不到 INSERT、无第二触发源）→ `status --wait` invoke kicker kickoff → pending→running→passed 救活、`status --wait` 正常返回。此真验还抓出并修了一个真 bug：kicker 原只认 Stream records 的 event 格式、忽略直接 invoke 的 `{"run_id":...}` payload → status --wait 的 invoke 空转救不了（`runs:[]`）；修为 `_run_ids_from_runs_stream` 兼容两种 event 源（Stream records + 直接 kickoff）。
- **常驻调度服务 / WebUI 真需要** → RunState 读模型 + reconciler 已就位，加 adapter/宿主即可（[0016](./0016-execution-architecture-core-lib-run-model.md)「加 adapter + 换注入」在 (a) 类仍成立）。
- **本地 events sink 选型**：定 **SQLite**（事务 + WAL 单写者串行化，承 per-run 进程内多 fd3 读线程并发 append 不丢不乱；表结构镜像 DDB events：PK=scope_id/SK=seq，与 cloud 心智对称）。被拒 append-only JSONL——虽最简无依赖，但并发读写只能靠 append 原子性 + 容忍半行，无事务保证。**注：条件写不在 events sink 上**——sink 只做幂等 `INSERT OR REPLACE`；local 的 HWM/终态条件写落在 `LocalRunStore` 的 fcntl 原子 RMW（机制三②），那才是「local 复刻 cloud 条件写语义」的落点。
