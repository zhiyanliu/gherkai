# 执行与推进模型导览：run / submit × local / cloud

> 本文讲**机制如何协同工作**（机制），不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。「四种跑法下推进器分别是什么」这类问题的答案散在五六个 ADR 里，本文就是拼合之后的那个横切面。

## 1. 心智模型：两种驱动、同一份 `core`

gherkai 跑一个 run 有**两种驱动模型**，按命令分流：

- **同步驱动（`run`，下称前台）**：CLI 进程内的 `schedule()`（`core/gherkai_core/schedule.py`）全程在线——起 worker、消费事件流、判超时、收结果，一个循环干到底。local 下 CLI 关掉即中止（worker 随事件管道断开而早亡）；cloud 下关掉 CLI 只是放弃收结果——已在跑的 Fargate task 无人 StopTask，会继续跑完并继续计费。
- **无状态驱动（`submit` + `status`，下称后台/后台跑批）**：没有常驻的「调度进程」。核心是一个**纯编排步骤 `reconcile.tick`**（`core/gherkai_core/reconcile.py`；判定与决策是 `gherkai_core.project` 的纯函数，副作用全经注入的 EventLog/RunStore/Launcher）：读全量事件重放 → 算出当前该干什么 → 条件写落库 → 抢占式起下一个 job。**谁都可以来调它推一步**，它自己不记状态、不假设上一步是谁推的——这就是「无状态」的含义。

不管哪种驱动，worker→`core` 的话语只有两条：**事件流**（`scope_started`/`step_done`/… 的逐条事件）+ **进程退出信号**（退出码——不是 worker「说」的，是父进程/平台观察到的；[ADR 0024](../adr/0024-worker-core-protocol.md) 协议）。判定「两件都要」：事件内容完整 ∧ 进程干净终止（防假绿）。两种驱动的差别本质是**有没有人在线守着听**——前台有：schedule 全程在线、听完即用，退出信号由 Engine adapter 当场观察；后台没有常驻听者：事件流被持久化、退出信号也被翻成 `task_exited` 记进同一份日志，于是谁来推进都能纯靠重放这份日志（各组合的物理通道见 §5）。

两种驱动共享同一份 `core`（parse/plan/project/判定模型），但**一个 run 只属于一种驱动**。cloud 档的分界线是 `detached` 标记：cloud `submit` 会在 runs 表的 STATE item 上写它，云端三 Lambda 据它只认领**后台 run**（带 `detached` 标记的），前台 run 的地盘绝不踏进（怎么保证的见 §7）。

local 档没有也不需要这个标记：不存在共享基础设施上的常驻推进器（每个 run 的推进者都是它自己 fork 出来的进程），没有谁需要被挡。

`reconcile.tick` 有**四个宿主**在不同场景下调用它：local 的 per-run 进程（= `submit` 时 `setsid` fork 出的推进进程）、**local** `status --wait` 的接力者（cloud 的 `--wait` 只在检测卡住时 invoke kicker、绝不在本机跑 `tick`——保 status 机器零 ECS 权限，见 §4b）、cloud 的 kicker Lambda、cloud 的 reconciler Lambda。四处跑的是同一份代码，差别只在注入的 adapter（事件从 SQLite 还是 DDB 读、job 用子进程还是 ECS RunTask 起）。

![执行与推进全景：run 的在线循环与 submit 的无状态推进共用同一份 core，只换事件通道与退出观察者](../diagrams/run-execution.svg)

图注：图只画结构与指向——四个宿主分别是谁、四条物理通道各自的载体，真源是上面这几段文字与 §5 的表。**图上的退出信号不表示 worker 自己上报**：退出码是父进程/平台观察到 worker 终止后送到驱动者的，观察者按组合各不相同，对位见 §5 的「退出观察者三对位」。可交互版（缩放 / 聚焦一格 / 追一条路径）：https://zhiyanliu.github.io/gherkai/run-execution.html

> why 与护栏：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（整体设计）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（分层）。

## 2. 四组合一览

|           | **run（前台同步）**                                                                                                                                              | **submit（后台跑批）**                                                                                                                                                                                                                     |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **local** | CLI 进程内 `schedule()`；worker = 本机子进程（fd3 事件流直达）；超时 = schedule 循环内计时到点；CLI 关掉即中止                                                      | **per-run 推进进程**（`setsid` 脱离 CLI）循环调 `tick`；事件旁路落 SQLite；该进程自兼退出观察者；本机需保持开机                                                                                                                               |
| **cloud** | 同一个进程内 `schedule()`，worker 换 Fargate task（job-in 走 S3、事件走 DDB events 表、adapter 轮询读）；云端 Lambda 对这种 run **一律不动作**（no-op；两道闸门，见 §7） | **三 Lambda 事件驱动链**：kicker（冷启动）、reconciler（主推进）、exit-observer（退出观察），事件串起、非调用链（§4b）；提交完关机也能跑完（例外：`--expose-local` 隧道模式下本机须保持开机联网，[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md)） |

顺带钉一个贯穿全文的粒度：**job = scope**——一个 `@scope` 分组就是一个调度/执行单位（上云时坐实，[ADR 0017](../adr/0017-cloud-execution-fargate-over-runtime.md)），§6 超时闹钟的 per-(run,scope) 即 per-job。四格的详细解剖在 §3-§4；横切机制（事件通道/退出观察/超时）在 §5-§6。四格的权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（两种驱动与后台跑批全部决策）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0032](../adr/0032-fargate-execution-environment.md)（Fargate 执行面）。

## 3. 前台 `run` 的一生

```
plan(纯本地) → begin(落 definition + 初始态) → schedule 循环:
  ├─ 按并发闸起 worker(每 scope 一个)
  ├─ 逐行消费 worker 事件流 → ScopeStarted 刷 RUNNING+会话血缘(session id)、每 job 完成落判定(RunPersistence;事件本体不落盘)
  ├─ 静默卡死由心跳兜底、超出 job 超时预算即停 → handle.stop(local=SIGTERM→宽限→SIGKILL;cloud=StopTask)
  └─ 全部收敛 → finalize(终态一次落定)+ RunReport
```

local 与 cloud 在这条路上的差别**只在 Engine adapter**：

- **local**：`SubprocessEngine` spawn 本机 worker 子进程，事件走专用 fd（`EVENTS_FD`，三通道分离：事件/SDK 噪声/诊断各走各的）。
- **cloud**：`FargateEngine` 把 job JSON 放 S3、`RunTask` 起容器；worker 在容器里把事件逐条 PutItem 进 DDB events 表，adapter 这头**轮询 Query** 读回来，同时 `DescribeTasks` 盯着 task 死活。事件读取只扫 worker 的连续 seq 段——events 表里还有另一类「退出记录」item，为什么读端要避开它、谁保证前台 run 撞不上，见 §5 的键空间对照与 §7。

另外两个能力只存在于前台驱动循环、后台跑批**不具备**：`--fail-fast` 早停（以及由它派生的 skipped/aborted 态），以及 `schedule` 里那条 network 瞬时故障的 job 级整批重试通道——但它**今天在 `run` 上并未启用**（`ScheduleOpts.network_retry` 默认 0、CLI 没接这个旋钮），网络抖动的实际处置见 [`verdict-model.md`](./verdict-model.md) §3c、门控与两层分工见 [ADR 0028](../adr/0028-transient-network-ssl-resilience.md)。后台档失败一律隔离、逐 job 各自收敛（[ADR 0026](../adr/0026-schedule-module.md) 失败隔离、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一）。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（worker↔core 协议、三通道、退出码）、[ADR 0026](../adr/0026-schedule-module.md)（调度/心跳/优雅终止）、[ADR 0032](../adr/0032-fargate-execution-environment.md)（Fargate 执行面）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（实时写）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（两层网络重试）。

## 4. 后台跑批 `submit` 的一生

### 4a. local 档：per-run 推进进程

```
submit:plan → 落 definition + 全 pending 初始态 → fork per-run 推进进程(setsid 脱离 CLI)→ CLI 返回 run_id
per-run 进程:run_reconcile_loop 循环调 tick
  ├─ tick 抢到 PENDING job → SubprocessLauncher 起本机 worker
  ├─ worker 的 fd3 原始事件行经 raw_sink 旁路落 SQLite(events 的持久通道)
  ├─ worker 退出 → 本进程 handle.wait() 拿 exitcode 写 task_exited(自兼"平台侧退出观察者")
  └─ 全 job 终态 → tick 收敛并提交(写序见 §4c) → 拆临时物,退出
status [--wait]:只读投影查进度;--wait 还能接力推进——per-run 进程若死,接力者跑同一个 tick 把 run 推到收敛
```

要点：推进进程是 **per-run** 的（一个 run 一个，不是常驻守护）；`setsid` 让它活过 CLI/终端；SQLite 里的事件表结构刻意镜像 DDB events 表（心智对称）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「端到端流程」节的 local 半边。

### 4b. cloud 档：三 Lambda 链

![云端后台跑批的事件级联：提交落库唤醒 kicker，worker 写事件唤醒 reconciler，任务停止经 exit-observer 翻成退出记录后收敛](../diagrams/execution-cloud-cascade.svg)

图注：图画「链怎么跑通」，谁被挡在链外见 §7 那张图。图上画了三个 Lambda 各自的主入口，**没画的两处**：**kicker 的另两个入口**（查进度发现卡住时踢一脚、超时闹钟到点，见下条与 §6），以及退出观察那条路由背后是部署时就建好的常驻订阅、不由谁启动；并发安全的保证见下面几条。

- **kicker**：冷启动器，但不是「只起首批的薄壳」——它与 reconciler 同 code、同权限，跑完整的 `tick`。除 runs 表 Stream 外还有两个入口：`status --wait` 检测卡住时的主动调起（kickoff invoke，卡死救活），以及 job timeout 到点的闹钟调起（§6）。
- **reconciler**：主推进器。worker 每写一批事件，Stream 就触发它跑一次 `tick`——事件既是数据也是「心跳」，推进由事件级联驱动，无轮询常驻。
- **exit-observer**：把 ECS STOPPED 事件翻译成 events 表里的 `task_exited` 记录（cloud 档的「谁看见 worker 死了」）。它的触发面是 IaC 部署时建好的 EventBridge rule（按本 cluster 过滤 ECS task 状态变更 → STOPPED）——**常驻订阅、不由谁「启动」**；三个 Lambda **之间**没有互相启动/调用关系——各自订阅自己的事件源，链条是被事件串起来的；仅有的主动 invoke 都来自 Lambda 之外（`status --wait` 与超时闹钟踢 kicker，见上条与 §6）。
- 多宿主并发安全：`tick` 幂等，job 抢占走 CAS 条件写（PENDING→RUNNING 只有一个赢家）、投影落库走 HWM（投影只前进不后退的水位）与终态条件写——Stream 分片并发触发多个 Lambda 实例、叠加 `status --wait` 踢起的 kicker 调用，全都安全。
- **并发上限：声明随 definition 走，部署侧只留一道 cap**（与超时预算同构：都属 run 的定义）。`run` 与 `submit` 都把 `--max-concurrency` 落进 definition（`RunMeta.max_concurrency`），detached 的推进器一律读 meta——local per-run 进程与 `status --wait` 接力者都以 meta 为准（各自的 flag 只是 meta 无值时的回落，接力不会悄悄改这个 run 的并行度）；同步 `run` 在同进程内直接用 flag（没有通道问题），meta 照落、只为 definition 诚实；cloud 档取 `min(definition 声明, 部署侧 cap)`，cap = reconciler/kicker 的 Lambda env `MAX_CONCURRENCY`（IaC 设，当前 8），闸的是 worker（Fargate task）的并行数、per-run 语义（单 run 内最多几个 job 并行），是**上限、不是真源**——提交侧在 cap 以内说了算；**local 无 cap**。声明超 cap 时不会静默按 cap 跑：`submit --backend cloud` 的 preflight 读推进器 env 比一下，超了就提示「本 run 将按 cap 并行、要更高并发改 IaC」——但**不拦提交**（对比 `REPORT_DIR` 不一致会退 2）。旧 definition（无此值）按 1，与打通前行为一致。为何 cap 归部署方、local 为何无 cap、为何超 cap 只提示不拦——why 见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制四。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一-四、端到端流程、重议闸门）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（三 Lambda 的 IaC/权限/触发面）。

### 4c. 读侧：进度怎么看、结果落在哪

后台驱动的另一半是「怎么观察」。事件流是**写模型**，读模型是它的投影 **RunState**（cloud = runs 表的 STATE item，local = `run_state.json`）——投影只在 `tick` 里落一次，外部读者（`status`、`explain`、未来 WebUI）**都不自己重放事件**（各自读什么、什么时候才有内容，见本节末条）。读这一侧决定的是「读到的有多新、读到什么算数」：

- **`status`（不带 `--wait`）纯只读、零副作用**——看到的新鲜度取决于最近一次 `tick` 是什么时候；它不推进、也不 kickoff。
- **run 级 status 的取值语义**：投影写被钳在 `pending`/`running` 两档——投影里全部 job 仍 pending = `pending`，任一 job 已推进 = `running`；run 级**终态**由 `try_finalize` 一次落定（提交点），**读到终态 = run 已提交**。注意投影落后于抢占一拍：CAS 抢占只改那个 job 的态，run 级要等下一次 `tick` 才翻 `running`——故「run 仍 pending」≠「还没开始推进」；`status` 的「推进可能未启动」提示因此要求 run 级 `pending` **且所有 job 仍 pending** 才打。
- **退出码分层**（CI 接线最易建错心智）：`submit` 的退出码只表示「提交成功与否」、**不是判定**；判定退出码由 `status --wait` 等到终态后给。根因：CLI 脱离后不再有内存里的判定终值——各命令退出码的完整分工见 [`verdict-model.md`](./verdict-model.md) §5（本篇不重复它的表）。

收尾那一侧决定的是「什么时候能读到什么」——写序、由写序推出的读者保证、已终态 run 的两档重入，以及落地之后谁来读。

- **收尾的写序**：三段有序——前两段在同一次 `tick` 里：① 各 job 的判定明细（`jobs/*.json`）从本轮 records 聚合落库 → ② `try_finalize`（CAS）落 run 终态，这一步是**提交点**；③ 提交点之后由宿主写派生的 RunReport（`tick` 返回 done 之后才写，写失败被隔离、不击穿已提交的 run）。三段都幂等，local per-run 进程与 cloud reconciler 共用 `core` 的同一份收尾逻辑。
- **由写序推出的读者保证**：**读到终态 = 判定明细已齐**（它在提交点之前落定）；反过来 RunReport 是提交点之后的派生物，「终态已读到、报告文件却缺」是合法中间态，读者不该拿它当判定真源。落点：local = `--report-dir/<run_id>/`，cloud = S3 桶下 `<report_dir>/<run_id>/`——cloud `submit` 的 `--report-dir` 须与推进器侧一致（提交前探活会比对、不一致退 2），否则「跑完了却在自己给的前缀下找不到结果」。
- **已终态 run 的两档重入**：cloud 档的云端推进器对已提交终态的 run 整体不动作（§7 里 reconciler 的第二道判）——RunReport 若恰在提交点之后没写成，云端不会再自己补写它（判定明细不受影响，见上条）；local 档没有这道闸，`status --wait` 接力会把已终态的 run 再重放一遍、顺手把报告重写出来（本机事件不过期）。
- **落了之后谁来读**：`status` 读投影 RunState（`--json` 时另附 `artifacts` 键给报告 / 判定明细 / 元信息的约定落点，无论终态都给、终态后才真有内容）；`explain` 读**已落库的判定明细**（step 级失败原因与 `kind=evidence` 的证据指针），回答「这步为什么这么判」。两者都受落地时机约束：detached run 的判定明细在提交点才一次性落地，未终态时 `explain` 无可渲染、只提示先用 `status --wait`（同步 `run` 逐 job 落，中途即可见已完成部分）。用法与退出码见 [`docs/user-guide/running-and-results.md`](../user-guide/running-and-results.md)，`--json` 字段见 [`cli-json-contract.md`](./cli-json-contract.md)。

最后一条不对称（**掐得掐不得**）：cloud 的 `--wait` 检测卡住时只是**踢一脚** kicker（fire-and-forget），踢完随时可离场——云端链自己跑完；local 的 `--wait` 接力者一旦接手**就是唯一推进者**，掐掉它 run 就地停摆（已 claim job 的计时也随进程一起丢，靠下次接力恢复）。根因：主推进器的位置不同（云端 Lambda vs 本机进程）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制三：投影钳制与条件写；「命令形态」节：status/退出码）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（终态提交点）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)（决定五：退出码语义）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策三：查询类命令的 `--json` 与 `artifacts`）、[ADR 0042](../adr/0042-step-evidence-and-explain.md)（决策四：`explain` 只读判定明细、不读事件流）。

## 5. 同一条事件流的四条物理通道（横切对照）

§3-§4 按跑法纵切讲完了生命周期；从这节起横过来看跨组合的机制。第一条就是 §1 说的那条事件流——逻辑上它在四个组合里完全同构（同一套事件、同一份解析），物理载体却各不相同：

| 组合         | worker 写到哪                        | 谁读、怎么读                                                                       |
|--------------|--------------------------------------|-----------------------------------------------------------------------------------|
| local run    | 专用 fd（`EVENTS_FD`）                 | CLI 进程 schedule 逐行阻塞读（内存流，不落盘）                                       |
| local submit | 同上 fd                              | per-run 进程读的同时经 `raw_sink` **旁路原样落 SQLite**；`tick` 从 SQLite 全量重放 |
| cloud run    | worker 直接 PutItem 进 DDB events 表 | CLI 进程 `FargateEngine` 轮询 Query（只扫 worker seq 段）                           |
| cloud submit | 同上                                 | events 表 **Stream 触发 reconciler** Lambda；`tick` 从表里全量重放                 |

events 表里有**两个键空间**，同一个 PK 下靠 SK 排序分开（`seq` 是 NUMBER 型 SK，Query 升序读）：

```
PK = run_id#scope_id
  SK = 1, 2, 3 … n     worker 事件本体：每 PK 单写者、连续递增 → 断号检测（判漏读/乱序）只看这一段
  …（大段空号）…
  SK = 保留高位        退出观察者写的 exit 记录：不入 seq 段、不参与断号检测
```

两类 item 按 `item_type` 属性区分（事件本体不带此属性），高位常数与属性名的真源在 `fargate_engine` 的 schema 常量。读端各按形态处理：前台读端（`FargateEngine`）按段界排除 exit 记录；无状态读端（`DdbEventLog.records()`）全 PK 读、按 `item_type` 分流后喂重放；「只问某个 scope 退没退」的超时处置路径走 `has_exit` 单点查。

**退出观察者三对位**（谁看见 worker 死了）：前台 = Engine adapter 自己看（subprocess 的 `proc.wait` / Fargate 的 `DescribeTasks`）；local `submit` = per-run 进程 `handle.wait()`；cloud `submit` = exit-observer Lambda。另有一个例外位：worker 压根没起来（`launch` 抛）时没有平台观察者可看，由 `tick` 自己补一条非 0 哨兵退出记录，下轮按「exit≠0 → error」收敛；不补则该 job 已抢占成 RUNNING 却永无事件与退出记录，整批卡死。

**诊断落哪**（事件流之外的另一条通道）：worker 的 stdout（引擎 SDK 噪声）/ stderr（worker 自己的诊断）默认带 `[worker <scope>:out|err]` 前缀透传到**推进者进程的 stderr**，落点随推进者而变——前台 `run` 直接进终端；本机 `run --quiet` 改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），结束只打一行位置；cloud 档 worker 在云端跑、日志在该 task 的 CloudWatch 日志组，无此文件；local `submit` 的 per-run 推进进程自身的 stdout/stderr 落 `<report-dir>/<run_id>/reconcile.log`，worker 透传行同落其中。判定归因只进 `jobs/*.json` 的 `message`。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（事件协议/DDB 态、三通道）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一：退出记录独立键空间；机制二：两件都要的收敛判据、launch 失败补偿）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策二：`--quiet` 的落点）。

## 6. `job` 超时预算（timeout）：三路同形的兜底

每个 `job` 有超时预算，按**墙钟**（真实流逝时间）计。声明用 `@timeout:N` tag 或 `--default-job-timeout`，随 definition 落在 `Job.timeout_s`（ADR/CONTEXT 里称「job 墙钟预算」）。三条执行路径**各自落实同一形态的兜底**（ADR/code 里称 enforce）：超时 → 停 worker → 归因 `error + timeout`：

| 路径         | 到点机制                                                                                                                                                               | 停法                                                                                                                                                                                         |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 前台 `run`   | schedule 循环内计时到点（deadline）                                                                                                                                      | local=`handle.stop(grace)`（SIGTERM→宽限→SIGKILL）；cloud=`StopTask`（宽限由 task-def `stopTimeout` 决定、不逐次传——上限与取舍见 [ADR 0032](../adr/0032-fargate-execution-environment.md) 结论 4） |
| local submit | per-run 进程 launcher 起 worker 子进程时装的到点计时器（`threading.Timer`，活在 owner 进程内）；进程若中断，计时随之丢——接力者改按库里的 `claimed_at` 起算、每轮推进时复查是否超预算（+固定余量） | 自家 job：`handle.stop(grace)`（协作停同前台 local，grace 取引擎最小宽限）；接力恢复的他人 job：worker 已随 fd3 断管早亡、无 handle 可停，直接记一条 `timed_out` 退出记录收敛 |
| cloud submit | 起 task 时给该 job **定一个一次性到点闹钟**（EventBridge Scheduler one-time；与 §4b exit-observer 的 EventBridge **rule** 同名不同物——那是事件总线订阅、这是独立定时服务） | 到点由 kicker 处置，整条链见下图；另有任意 `tick` 的防御扫作双保险                                                                                                                             |

cloud 路径的超时处置是一条多跳链，时序如下。那个「闹钟」（ADR/code 里叫 arm/武装一个 one-time schedule）是 per-(run,scope) 的短命资源：schedule 名 = `{prefix}job-timeout-<sha1(run_id#scope_id) 摘要>`（前缀走 `gherkai_runtime.names` 命名真源、IaC 的 IAM 资源域同源推导），到点触发即自动删——所以控制台里平时看不到它：

![云端超时兜底链：起 task 时定下的一次性闹钟到点踢 kicker，停掉 worker 后由 exit-observer 写成带超时标记的退出记录，回到既有链收敛](../diagrams/execution-timeout-chain.svg)

图注：本图只画云端这一路「怎么把 worker 停下来」，另两路的到点机制与停法见上表；闹钟的到点 = 起跑那一刻 + 该 job 的墙钟预算。到点那一方**先查这个 job 仍 RUNNING 且没有退出记录才动手**（重复到点、闹钟与防御扫同时命中都无害），`StopTask` 的 reason 里带一个哨兵串，exit-observer 据此把这条退出记录标成超时停的。停下来之后**记成什么态**（超时归因落在哪一档、与 fail-fast 共用哪个字段、按什么优先级定）见 [`verdict-model.md`](./verdict-model.md) §3c（归因优先级图）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节（取舍/归因链/防御扫）、[ADR 0019](../adr/0019-feature-tags-scope-and-engine.md)（`@timeout:` tag）。

## 7. 为什么云端 Lambda 不会抢前台 run

`run --backend cloud` 与 `submit --backend cloud` 共享同一套表和 Lambda——前台 run 照样往两张表里写（definition 落 runs 表、worker 事件落 events 表），Stream 里照样有它的记录——**若无闸门，云端推进器就会被这些记录唤醒、跑来推前台 run**（双开推进器：同一 scope 起两个 task）。两道闸门拦在不同层，判据同源（STATE 上的 `detached` 标记）：

![两道闸门：新 run 落库那一路在订阅侧就滤掉，事件批次与任务停止事件只能进了函数再查这个 run 上的后台标记](../diagrams/execution-detached-gates.svg)

图注：滤得掉的在事件源层就挡下，滤不掉的进 handler 再判——事件批次与任务停止事件上都不带 `detached`，只能回头查这个 run。图上四个判点里只有前两个（新 run 落库、handler 判是后台批次）是本节说的那两道闸门——「该 run 已收尾？」与 exit-observer 那道各防另一件事，见下三条。§4b 那张时序图画「链怎么跑通」，本图画「谁被挡在链外」。

- **kicker**：runs 表 Stream 的事件源 **filter** 写死 `INSERT ∧ detached=true`——前台 run 的 STATE 不带这个标记。
- **reconciler**：`tick` 装配前查 `is_detached`（日志 `skip: run … 不是 submit 提交的后台批次`）；紧跟的第二道判读 run 终态（日志 `skip: run … 已结束，不再改写它的结果`），管的不是本节这件事。这两道都在 reconciler 与 kicker **共用的装配**里，kicker 无论哪个入口（新 run 落库、`status --wait` 救活、超时闹钟到点）都要过——图上这两个判点因此不点 Lambda 名，冷启动那一路画成直达只为看清「谁在哪一层被挡」。
- **exit-observer**：判据同一个 `is_detached`。它不推进，防的是另一件事：无 `body` 的 exit item 混进前台 run 的事件流（前台的退出观察由 Engine adapter 自己做，§5）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（「filter 必须区分写入者」条）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（Stream/filter 资源；events 表那条只滤得掉 TTL 删除，`detached` 那半只能在 handler 内判）。

## 8. 延伸阅读

| 想深入的主题                                                    | 去哪读                                                               |
|-----------------------------------------------------------------|----------------------------------------------------------------------|
| 无状态跑批全部决策/护栏/被拒方案                                | [ADR 0034](../adr/0034-detached-batch-reconciler.md)                 |
| 同步调度器（并发/心跳/失败隔离/优雅终止/事件归约）                | [ADR 0026](../adr/0026-schedule-module.md)                           |
| worker↔core 协议（事件三通道/job 入口 stdin·`JOB_S3_URI`/退出码） | [ADR 0024](../adr/0024-worker-core-protocol.md)                      |
| job 生命周期状态机与严重度排序（severity）                        | [ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)         |
| Fargate 执行面（停止宽限 grace/中断韧性）                         | [ADR 0032](../adr/0032-fargate-execution-environment.md)             |
| 实时持久化接缝（终态提交点 commit point/条件写）                  | [ADR 0030](../adr/0030-realtime-persistence-seam.md)                 |
| 云资源 IaC/命名/提交前探活（preflight）                           | [ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)    |
| 分层总纲（core/runtime/cli/engines）                              | [ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) |
| 判定怎么算出来（四层归约 / 七个状态 / 各命令退出码语义）          | [`verdict-model.md`](./verdict-model.md)                             |
| 产物与证据落在哪、哪一份答哪个问题                                | [`artifacts-and-evidence.md`](./artifacts-and-evidence.md)           |
| 云端后端由哪几个载体拼成、改动要推哪一处                          | [`cloud-backend-carriers.md`](./cloud-backend-carriers.md)           |
| 确定性 step 从写到云端命中的一生                                  | [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) |
