# 执行与推进模型导览：run / submit × local / cloud

> 本文讲**机制如何协同工作**，不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。「四种跑法下推进器分别是什么」这类问题的答案散在五六个 ADR 里，本文是它们汇总后的横切视图。

## 1. 心智模型：两种驱动、同一份 `core`

gherkai 执行一个 run 有**两种驱动模型**，按命令分流：

- **同步驱动（`run`，下称前台）**：CLI 进程内的 `schedule()`（`core/gherkai_core/schedule.py`）全程在线，在一个循环内完成启动 worker、消费事件流、判定超时、收集结果。local 档关闭 CLI 即中止（worker 随事件管道断开而退出）；cloud 档关闭 CLI 只是放弃接收结果——已在运行的 Fargate task 没有调用方发起 StopTask，会运行至结束并持续计费。
- **无状态驱动（`submit` + `status`，下称后台/后台跑批）**：没有常驻的「调度进程」。核心是一个**纯编排步骤 `reconcile.tick`**（`core/gherkai_core/reconcile.py`；判定与决策是 `gherkai_core.project` 的纯函数，副作用全经注入的 EventLog/RunStore/Launcher）：全量重放事件 → 推算当前应执行的动作 → 条件写落库 → 抢占启动下一个 job。**任何宿主都可以调用它推进一步**：它不保存自身状态、不假设上一步由谁推进，这是「无状态」的含义。

不论哪种驱动，worker 与 `core` 之间的回传只有两类：**事件流**（`scope_started`/`step_done`/… 的逐条事件）与**进程退出信号**（退出码由父进程或平台观察得到，不由 worker 上报；[ADR 0024](../adr/0024-worker-core-protocol.md) 协议）。判定要求两者同时成立：事件内容完整 ∧ 进程干净终止，缺一即不判通过（防假绿）。两种驱动的本质差别在于**有没有在线的接收方**：前台有在线接收方，`schedule` 全程在线、收到事件即处理，退出信号由 Engine adapter 当场观察；后台没有常驻接收方，事件流被持久化、退出信号也被转写成 `task_exited` 记入同一份日志，于是任何宿主都能仅凭重放这份日志推进（各组合的物理通道见 §5）。

两种驱动共享同一份 `core`（parse/plan/project/判定模型），但**一个 run 只属于一种驱动**。cloud 档的分界线是 `detached` 标记：cloud `submit` 会在 runs 表的 STATE item 上写它，云端三 Lambda 据它只认领**带 `detached` 标记的后台 run**，不介入前台 run（保证手段见 §7）。

local 档没有也不需要这个标记：不存在共享基础设施上的常驻推进器（每个 run 的推进者都是由它自身 fork 出的进程），无需拦截任何一方。

`reconcile.tick` 有**四个宿主**在不同场景下调用它：local 的 per-run 进程（= `submit` 时 `setsid` fork 出的推进进程）、**local** `status --wait` 的接力者（cloud 的 `--wait` 只在检测到停滞时 invoke kicker，不在本机执行 `tick`，使 status 所在机器无需 ECS 权限，见 §4b）、cloud 的 kicker Lambda、cloud 的 reconciler Lambda。四处执行的是同一份代码，差别只在注入的 adapter（事件从 SQLite 还是 DDB 读、job 以子进程还是 ECS RunTask 启动）。

![执行与推进全景：run 的在线循环与 submit 的无状态推进共用同一份 core，只换事件通道与退出观察者](../diagrams/run-execution.svg)

图注：图只画结构与指向，四个宿主分别是谁、四条物理通道各自的载体，真源是上面几段正文与 §5 的表。**图上的退出信号不表示 worker 自行上报**：退出码由父进程或平台观察到 worker 终止后送达驱动者，观察者按组合各不相同，对位见 §5 的「退出观察者三对位」。可交互版（缩放 / 聚焦单个节点 / 追踪一条路径）：https://zhiyanliu.github.io/gherkai/run-execution.html

> why 与护栏：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（整体设计）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（分层）。

## 2. 四组合一览

|           | **run（前台同步）**                                                                                                                                                        | **submit（后台跑批）**                                                                                                                                                                                                                                             |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **local** | CLI 进程内 `schedule()`；worker = 本机子进程（fd3 事件流直达）；超时 = schedule 循环内计时到点；关闭 CLI 即中止                                                            | **per-run 推进进程**（`setsid` 脱离 CLI）循环调用 `tick`；事件旁路落 SQLite；该进程自兼退出观察者；本机需保持开机                                                                                                                                                  |
| **cloud** | 同一个进程内 `schedule()`，worker 改为 Fargate task（job-in 走 S3、事件走 DDB events 表、adapter 轮询读）；云端 Lambda 对这种 run **一律不动作**（no-op；两道闸门，见 §7） | **三 Lambda 事件驱动链**：kicker（冷启动）、reconciler（主推进）、exit-observer（退出观察），由事件串接、非调用链（§4b）；提交后关机也能执行至结束（例外：`--expose-local` 隧道模式下本机须保持开机联网，[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md)） |

此处明确一个贯穿全文的粒度：**job = scope**——一个 `@scope` 分组即一个调度/执行单位（上云后确立，[ADR 0017](../adr/0017-cloud-execution-fargate-over-runtime.md)），§6 超时闹钟的 per-(run,scope) 即 per-job。四种组合的详细解剖在 §3-§4，横切机制（事件通道/退出观察/超时）在 §5-§6。四种组合的权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（两种驱动与后台跑批全部决策）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0032](../adr/0032-fargate-execution-environment.md)（Fargate 执行面）。

## 3. 前台 `run` 的生命周期

```
plan(纯本地) → begin(落 definition + 初始态) → schedule 循环:
  ├─ 按并发闸启动 worker(每 scope 一个)
  ├─ 逐行消费 worker 事件流 → ScopeStarted 置 RUNNING+会话血缘(session id)、每 job 完成落判定(RunPersistence;事件本体不落盘)
  ├─ 静默停滞由心跳检出、超出 job 超时预算即停 → handle.stop(local=SIGTERM→宽限→SIGKILL;cloud=StopTask)
  └─ 全部收敛 → finalize(终态一次落定)+ RunReport
```

local 与 cloud 在这条路径上的差别**只在 Engine adapter**：

- **local**：`SubprocessEngine` spawn 本机 worker 子进程，事件走专用 fd（`EVENTS_FD`，三通道分离：事件、SDK 噪声、诊断各占一条）。
- **cloud**：`FargateEngine` 把 job JSON 放 S3、以 `RunTask` 启动容器；worker 在容器内把事件逐条 PutItem 进 DDB events 表，adapter 侧**轮询 Query** 读回，同时以 `DescribeTasks` 监测 task 存活。事件读取只扫 worker 的连续 seq 段——events 表里还有另一类「退出记录」item，读端为什么要避开它、由谁保证前台 run 不会读到它，见 §5 的键空间对照与 §7。

另有两项能力只存在于前台驱动循环，后台跑批**不具备**：`--fail-fast` 早停（及由它派生的 skipped/aborted 态），以及 `schedule` 中针对 network 瞬时故障的 job 级整批重试通道——后者**当前在 `run` 上并未启用**（`ScheduleOpts.network_retry` 默认 0，CLI 未暴露该参数），网络抖动的实际处置见 [`verdict-model.md`](./verdict-model.md) §3c，门控与两层分工见 [ADR 0028](../adr/0028-transient-network-ssl-resilience.md)。后台档失败一律隔离、逐 job 各自收敛（[ADR 0026](../adr/0026-schedule-module.md) 失败隔离、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一）。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（worker↔core 协议、三通道、退出码）、[ADR 0026](../adr/0026-schedule-module.md)（调度/心跳/优雅终止）、[ADR 0032](../adr/0032-fargate-execution-environment.md)（Fargate 执行面）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（实时写）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（两层网络重试）。

## 4. 后台跑批 `submit` 的生命周期

### 4a. local 档：per-run 推进进程

```
submit:plan → 落 definition + 全 pending 初始态 → fork per-run 推进进程(setsid 脱离 CLI)→ CLI 返回 run_id
per-run 进程:run_reconcile_loop 循环调用 tick
  ├─ tick 抢占到 PENDING job → SubprocessLauncher 启动本机 worker
  ├─ worker 的 fd3 原始事件行经 raw_sink 旁路落 SQLite(events 的持久通道)
  ├─ worker 退出 → 本进程 handle.wait() 取 exitcode 写 task_exited(自兼"平台侧退出观察者")
  └─ 全 job 终态 → tick 收敛并提交(写序见 §4c) → 拆除临时资源,退出
status [--wait]:只读投影查进度;--wait 还能接力推进——per-run 进程若终止,接力者执行同一个 tick 把 run 推到收敛
```

要点：推进进程是 **per-run** 的（一个 run 一个，不是常驻守护进程）；`setsid` 使它在 CLI 与终端退出后继续存在；SQLite 里的事件表结构刻意镜像 DDB events 表（保持心智对称）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「端到端流程」节的 local 半边。

### 4b. cloud 档：三 Lambda 链

![云端后台跑批的事件级联：提交落库唤醒 kicker，worker 写事件唤醒 reconciler，任务停止经 exit-observer 转写为退出记录后收敛](../diagrams/execution-cloud-cascade.svg)

图注：本图画「链如何贯通」，谁被挡在链外见 §7 那张图。图上画了三个 Lambda 各自的主入口，**未画两处**：**kicker 的另两个入口**（查询进度时发现停滞而主动调起、超时闹钟到点，见下条与 §6），以及退出观察那条路由背后是部署时即建好的常驻订阅、不由任何一方启动；并发安全的保证见下面几条。

- **kicker**：冷启动器，但不是「只负责启动首批的精简实现」——它与 reconciler 同 code、同权限，执行完整的 `tick`。除 runs 表 Stream 外还有两个入口：`status --wait` 检测到停滞时的主动调起（kickoff invoke，用于从停滞中恢复），以及 job timeout 到点的闹钟调起（§6）。
- **reconciler**：主推进器。worker 每写入一批事件，Stream 即触发它执行一次 `tick`——事件既是数据也是「心跳」，推进由事件级联驱动，无常驻轮询。
- **exit-observer**：把 ECS STOPPED 事件翻译成 events 表里的 `task_exited` 记录（即 cloud 档中观察到 worker 终止的一方）。它的触发面是 IaC 部署时建好的 EventBridge rule（按本 cluster 过滤 ECS task 状态变更 → STOPPED）——**常驻订阅、不由任何一方启动**；三个 Lambda **之间**没有互相启动/调用关系，各自订阅自己的事件源，链条由事件串接；仅有的主动 invoke 都来自 Lambda 之外（`status --wait` 与超时闹钟调起 kicker，见上条与 §6）。
- 多宿主并发安全：`tick` 幂等，job 抢占走 CAS 条件写（PENDING→RUNNING 只有一个写入方成功），投影落库走 HWM（投影只前进不后退的水位）与终态条件写；Stream 分片并发触发多个 Lambda 实例，叠加 `status --wait` 调起的 kicker，均安全。
- **并发上限：声明随 definition 传递，部署侧只留一道 cap**（与超时预算同构，二者都属 run 的定义）。`run` 与 `submit` 都把 `--max-concurrency` 落进 definition（`RunMeta.max_concurrency`），detached 的推进器一律读 meta：local per-run 进程与 `status --wait` 接力者都以 meta 为准，各自的 flag 只在 meta 无值时回落，接力不会改变这个 run 的并行度。同步 `run` 在同一进程内直接用 flag（不存在传递通道问题），meta 仍照常写入，只为使 definition 如实记录该值。cloud 档取 `min(definition 声明, 部署侧 cap)`，cap = reconciler/kicker 的 Lambda env `MAX_CONCURRENCY`（由 IaC 设定，当前 8），限制的是 worker（Fargate task）的并行数，语义为 per-run（单 run 内最多几个 job 并行），是**上限、不是真源**：cap 以内由提交侧决定；**local 无 cap**。声明超 cap 时不会静默按 cap 执行：`submit --backend cloud` 的 preflight 读取推进器 env 比对，超出即提示「本 run 将按 cap 并行，需要更高并发须改 IaC」，但**不阻断提交**（相比之下 `REPORT_DIR` 不一致会退 2）。旧 definition（无此值）按 1 处理，与该机制接通前的行为一致。为何 cap 归部署方、local 为何无 cap、为何超 cap 只提示不阻断，why 见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制四。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一-四、端到端流程、重议闸门）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（三 Lambda 的 IaC/权限/触发面）。

### 4c. 读侧：进度观察与结果落点

后台驱动的另一半是观察。事件流是**写模型**，读模型是它的投影 **RunState**（cloud = runs 表的 STATE item，local = `run_state.json`）：投影只在 `tick` 里写一次，外部读者（`status`、`explain`、未来的 WebUI）**都不自行重放事件**（各自读什么、何时才有内容，见本节末条）。读侧决定的是「读到的数据有多新、读到什么才算定论」：

- **`status`（不带 `--wait`）纯只读、零副作用**：数据新鲜度取决于最近一次 `tick` 的时刻；它不推进，也不 kickoff。
- **run 级 status 的取值语义**：投影写入被钳在 `pending`/`running` 两档——投影里全部 job 仍 pending 为 `pending`，任一 job 已推进为 `running`；run 级**终态**由 `try_finalize` 一次落定（提交点），**读到终态即 run 已提交**。投影比抢占滞后一轮：CAS 抢占只改该 job 的状态，run 级要到下一次 `tick` 才转为 `running`，因此「run 仍 pending」不等于「尚未开始推进」；`status` 的「推进可能未启动」提示据此要求 run 级为 `pending` **且所有 job 仍 pending** 时才输出。
- **退出码分层**（CI 接线时最易建立错误心智）：`submit` 的退出码只表示提交是否成功，**不是判定**；判定退出码由 `status --wait` 等到终态后给出。根因是 CLI 脱离后不再持有内存中的判定终值。各命令退出码的完整分工见 [`verdict-model.md`](./verdict-model.md) §5（本篇不重复它的表）。

收尾一侧决定的是「什么时候能读到什么」：写序、由写序推出的读者保证、已终态 run 的两档重入，以及落地之后由谁读取。

- **收尾的写序**：三段有序，前两段在同一次 `tick` 里：① 各 job 的判定明细（`jobs/*.json`）由本轮 records 聚合落库 → ② `try_finalize`（CAS）落 run 终态，这一步是**提交点**；③ 提交点之后由宿主写入派生的 RunReport（在 `tick` 返回 done 之后才写，写失败被隔离，不会回退已提交的 run 终态）。三段均幂等，local per-run 进程与 cloud reconciler 共用 `core` 的同一份收尾逻辑。
- **由写序推出的读者保证**：**读到终态即判定明细已完整落库**（它在提交点之前落定）；RunReport 则是提交点之后的派生物，「已读到终态、报告文件尚缺」是合法中间态，读者不应把它当判定真源。落点：local = `--report-dir/<run_id>/`，cloud = S3 桶下 `<report_dir>/<run_id>/`；cloud `submit` 的 `--report-dir` 须与推进器侧一致（提交前探活会比对，不一致退 2），否则 run 执行完成后在提交方给出的前缀下找不到结果。
- **已终态 run 的两档重入**：cloud 档的云端推进器对已提交终态的 run 整体不动作（§7 里 reconciler 的第二道判）——RunReport 若在提交点之后写入失败，云端不会补写（判定明细不受影响，见上条）；local 档没有这道闸门，`status --wait` 接力会把已终态的 run 重放一次并重新写出报告（本机事件不过期）。
- **落地之后由谁读取**：`status` 读投影 RunState（`--json` 时另附 `artifacts` 键，给出报告 / 判定明细 / 元信息的约定落点，无论是否终态都会给出，终态后才有内容）；`explain` 读**已落库的判定明细**（step 级失败原因与 `kind=evidence` 的证据指针），回答「这一步为何如此判定」。两者都受落地时机约束：detached run 的判定明细在提交点一次性落地，未到终态时 `explain` 无可渲染内容，只提示先用 `status --wait`（同步 `run` 逐 job 落库，中途即可读到已完成部分）。用法与退出码见 [`docs/user-guide/running-and-results.md`](../user-guide/running-and-results.md)，`--json` 字段见 [`cli-json-contract.md`](./cli-json-contract.md)。

最后一条不对称（**能否中途终止**）：cloud 的 `--wait` 检测到停滞时只是调起 kicker（fire-and-forget），调起后随时可以离开，云端链会自行执行至结束；local 的 `--wait` 接力者一旦接手**就是唯一推进者**，终止它 run 即就地停止（已 claim job 的计时也随进程一起丢失，由下一次接力恢复）。根因是主推进器的位置不同（云端 Lambda 与本机进程）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制三：投影钳制与条件写；「命令形态」节：status/退出码）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（终态提交点）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)（决定五：退出码语义）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策三：查询类命令的 `--json` 与 `artifacts`）、[ADR 0042](../adr/0042-step-evidence-and-explain.md)（决策四：`explain` 只读判定明细、不读事件流）。

## 5. 同一条事件流的四条物理通道（横切对照）

§3-§4 已按跑法纵切给出生命周期，本节起转为横切，考察跨组合的机制。第一条是 §1 提到的那条事件流：逻辑上它在四个组合里完全同构（同一套事件、同一份解析），物理载体却各不相同。

| 组合         | worker 写入何处                      | 读取方与读取方式                                                                     |
|--------------|--------------------------------------|--------------------------------------------------------------------------------------|
| local run    | 专用 fd（`EVENTS_FD`）               | CLI 进程 schedule 逐行阻塞读（内存流，不落盘）                                       |
| local submit | 同上 fd                              | per-run 进程读取的同时经 `raw_sink` **旁路原样落 SQLite**；`tick` 从 SQLite 全量重放 |
| cloud run    | worker 直接 PutItem 进 DDB events 表 | CLI 进程 `FargateEngine` 轮询 Query（只扫 worker seq 段）                            |
| cloud submit | 同上                                 | events 表 **Stream 触发 reconciler** Lambda；`tick` 从表里全量重放                   |

events 表里有**两个键空间**，在同一个 PK 下靠 SK 排序区分（`seq` 是 NUMBER 型 SK，Query 升序读）：

```
PK = run_id#scope_id
  SK = 1, 2, 3 … n     worker 事件本体：每 PK 单写者、连续递增 → 断号检测（判漏读/乱序）仅针对这一段
  …（大段空号）…
  SK = 保留高位        退出观察者写的 exit 记录：不入 seq 段、不参与断号检测
```

两类 item 按 `item_type` 属性区分（事件本体不带此属性），高位常数与属性名的真源在 `fargate_engine` 的 schema 常量。读端按形态各自处理：前台读端（`FargateEngine`）按段界排除 exit 记录；无状态读端（`DdbEventLog.records()`）读整个 PK、按 `item_type` 分流后交给重放；超时处置路径只需判断某个 scope 是否已退出，用 `has_exit` 做单点查询。

**退出观察者三对位**（谁观察到 worker 终止）：前台 = Engine adapter 自行观察（subprocess 的 `proc.wait` / Fargate 的 `DescribeTasks`）；local `submit` = per-run 进程的 `handle.wait()`；cloud `submit` = exit-observer Lambda。另有一个例外情形：worker 根本未启动（`launch` 抛异常）时不存在平台侧观察者，由 `tick` 自行补一条非 0 哨兵退出记录，下一轮按「exit≠0 → error」收敛；若不补写，该 job 已被抢占为 RUNNING 却永不会有事件与退出记录，整批停滞。

**诊断的落点**（事件流之外的另一条通道）：worker 的 stdout（引擎 SDK 噪声）与 stderr（worker 自身的诊断）默认带 `[worker <scope>:out|err]` 前缀透传到**推进者进程的 stderr**，落点随推进者而变：前台 `run` 直接输出到终端；本机 `run --quiet` 改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），结束时只输出一行路径；cloud 档 worker 在云端执行，日志在该 task 的 CloudWatch 日志组，无此文件；local `submit` 的 per-run 推进进程自身的 stdout/stderr 落 `<report-dir>/<run_id>/reconcile.log`，worker 的透传行同落其中。判定归因只写入 `jobs/*.json` 的 `message`。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（事件协议/DDB 态、三通道）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一：退出记录独立键空间；机制二：两件都要的收敛判据、launch 失败补偿）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策二：`--quiet` 的落点）。

## 6. `job` 超时预算（timeout）：三路同形的 enforce

每个 `job` 有超时预算，按**墙钟**（真实流逝时间）计。声明方式为 `@timeout:N` tag 或 `--default-job-timeout`，随 definition 落在 `Job.timeout_s`（ADR/CONTEXT 里称「job 墙钟预算」）。三条执行路径**各自落实同一形态的 enforce**（enforce 即 ADR 与 code 对这一形态的用词）：超时 → 停止 worker → 归因 `error + timeout`。

| 路径         | 到点机制                                                                                                                                                                                                          | 停止方式                                                                                                                                                                                             |
|--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 前台 `run`   | schedule 循环内计时到点（deadline）                                                                                                                                                                               | local=`handle.stop(grace)`（SIGTERM→宽限→SIGKILL）；cloud=`StopTask`（宽限由 task-def `stopTimeout` 决定、不逐次传入——上限与取舍见 [ADR 0032](../adr/0032-fargate-execution-environment.md) 结论 4） |
| local submit | per-run 进程的 launcher 在启动 worker 子进程时装配的到点计时器（`threading.Timer`，存在于 owner 进程内）；该进程若中断，计时随之丢失——接力者改按库里的 `claimed_at` 起算、每轮推进时复查是否超出预算（+固定余量） | 本进程启动的 job：`handle.stop(grace)`（协作式停止，同前台 local，grace 取引擎最小宽限）；接力恢复的他人 job：worker 已随 fd3 断管退出、无 handle 可停，直接记一条 `timed_out` 退出记录收敛          |
| cloud submit | 启动 task 时为该 job **设置一个一次性到点闹钟**（EventBridge Scheduler one-time；与 §4b exit-observer 的 EventBridge **rule** 同名不同物：那是事件总线订阅，这是独立定时服务）                                    | 到点由 kicker 处置，整条链见下图；另有任意 `tick` 的防御扫描作为双保险                                                                                                                               |

cloud 路径的超时处置是一条多跳链，时序如下图。这里的「闹钟」（ADR/code 里称 arm 一个 one-time schedule，中文记作「武装」）是 per-(run,scope) 的短生命周期资源：schedule 名 = `{prefix}job-timeout-<sha1(run_id#scope_id) 摘要>`（前缀取 `gherkai_runtime.names` 这一命名真源，IaC 的 IAM 资源域同源推导），到点触发后即自动删除，因此控制台中通常看不到它。

![云端超时 enforce 链：启动 task 时设置的一次性闹钟到点调起 kicker，停止 worker 后由 exit-observer 写成带超时标记的退出记录，回到既有链收敛](../diagrams/execution-timeout-chain.svg)

图注：本图只画云端这一路「如何停止 worker」，另两路的到点机制与停止方式见上表；闹钟的到点时刻 = 启动时刻 + 该 job 的墙钟预算。到点的一方**先确认这个 job 仍为 RUNNING 且没有退出记录才执行停止**（重复到点、闹钟与防御扫描同时命中均无害），`StopTask` 的 reason 里带一个哨兵串，exit-observer 据此把这条退出记录标记为超时停止。停止之后**记为什么状态**（超时归因落在哪一档、与 fail-fast 共用哪个字段、按什么优先级判定）见 [`verdict-model.md`](./verdict-model.md) §3c（归因优先级图）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节（取舍/归因链/防御扫）、[ADR 0019](../adr/0019-feature-tags-scope-and-engine.md)（`@timeout:` tag）。

## 7. 云端 Lambda 为何不介入前台 run

`run --backend cloud` 与 `submit --backend cloud` 共享同一套表和 Lambda：前台 run 同样向两张表写入（definition 落 runs 表、worker 事件落 events 表），Stream 里同样有它的记录。**若无闸门，云端推进器会被这些记录唤醒并推进前台 run**（形成双推进器：同一 scope 启动两个 task）。两道闸门位于不同层，判据同源（STATE 上的 `detached` 标记）：

![两道闸门：新 run 落库这一路在订阅侧即被过滤，事件批次与任务停止事件只能进入函数后再查询该 run 的后台标记](../diagrams/execution-detached-gates.svg)

图注：能在事件源层过滤的即在该层挡下，不能过滤的进入 handler 后再判断——事件批次与任务停止事件上都不带 `detached`，只能反查这个 run。图上四个判点里只有前两个（新 run 落库、handler 判断是否为后台批次）是本节所说的那两道闸门；「该 run 已收尾？」与 exit-observer 那一道各自防范另一件事，见下面三条。§4b 那张时序图画「链如何贯通」，本图画「谁被挡在链外」。

- **kicker**：runs 表 Stream 的事件源 **filter** 固定为 `INSERT ∧ detached=true`，前台 run 的 STATE 不带这个标记。
- **reconciler**：`tick` 装配前查 `is_detached`（日志 `skip: run … 不是 submit 提交的后台批次`）；紧接的第二道判断读 run 终态（日志 `skip: run … 已结束，不再改写它的结果`），针对的不是本节这件事。两道判断都在 reconciler 与 kicker **共用的装配**里，kicker 无论从哪个入口进入（新 run 落库、`status --wait` 检测到停滞后的调起、超时闹钟到点）都要经过，因此图上这两个判点不标注 Lambda 名；冷启动那一路画成直达，只为看清「谁在哪一层被挡」。
- **exit-observer**：判据同为 `is_detached`。它不推进，防范的是另一件事：无 `body` 的 exit item 混入前台 run 的事件流（前台的退出观察由 Engine adapter 自行完成，§5）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（「filter 必须区分写入者」条）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（Stream/filter 资源；events 表那条只滤得掉 TTL 删除，`detached` 那半只能在 handler 内判）。

## 8. 延伸阅读

| 想深入的主题                                                      | 去哪读                                                                 |
|-------------------------------------------------------------------|------------------------------------------------------------------------|
| 无状态跑批全部决策/护栏/被拒方案                                  | [ADR 0034](../adr/0034-detached-batch-reconciler.md)                   |
| 同步调度器（并发/心跳/失败隔离/优雅终止/事件归约）                | [ADR 0026](../adr/0026-schedule-module.md)                             |
| worker↔core 协议（事件三通道/job 入口 stdin·`JOB_S3_URI`/退出码） | [ADR 0024](../adr/0024-worker-core-protocol.md)                        |
| job 生命周期状态机与严重度排序（severity）                        | [ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)           |
| Fargate 执行面（停止宽限 grace/中断韧性）                         | [ADR 0032](../adr/0032-fargate-execution-environment.md)               |
| 实时持久化接缝（终态提交点 commit point/条件写）                  | [ADR 0030](../adr/0030-realtime-persistence-seam.md)                   |
| 云资源 IaC/命名/提交前探活（preflight）                           | [ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)      |
| 分层总纲（core/runtime/cli/engines）                              | [ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)   |
| 判定如何算出（四层归约 / 七个状态 / 各命令退出码语义）            | [`verdict-model.md`](./verdict-model.md)                               |
| 产物与证据的落点、哪一份答哪个问题                                | [`artifacts-and-evidence.md`](./artifacts-and-evidence.md)             |
| 云端后端由哪些载体组成、改动要推到哪一处                          | [`cloud-backend-carriers.md`](./cloud-backend-carriers.md)             |
| 一条确定性 step 从写下到云端命中的生命周期                        | [`deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) |
