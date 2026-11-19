# 执行与推进模型导览：本机前台、本机后台与云端后台

> 本文讲**机制如何协同工作**，不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。「三种组合下推进器分别是什么」这类问题的答案散在五六个 ADR 里，本文是它们汇总后的横切视图。

## 1. 心智模型：两种驱动、同一份 `core`

gherkai 执行一个 run 有**两种驱动模型**，按命令分流：

- **同步驱动（`run`，下称前台）**：CLI 进程内的 `schedule()`（`core/gherkai_core/schedule.py`）全程在线，在一个循环内完成启动 worker、消费事件流、判定超时、收集结果。前台只有本机后端：`run` 给出云端后端时在开始执行之前以退出码 2 结束，云端后端只经 `submit`（[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 A）。按 Ctrl-C 或向 CLI 发 SIGTERM 时，CLI 的信号处理器只记下中断，`schedule` 轮询到后走与 fail-fast 同一条停止路径：首次中断请求全部 worker 协作停止（向 worker 的进程组发 SIGTERM、宽限到期再 SIGKILL），再次中断时改用零宽限；照常收集结果后，没有启动的 job 由结束写记为 skipped，run 的状态按各 job 的状态得出，以 130 / 143 结束（[ADR 0024](../adr/0024-worker-core-protocol.md) 终止契约「使用方中断」条）。它遵守运行期限：过了期限减 60 秒不再启动 job，到期限时停下运行中的 worker；起 worker 之前先认领，发现这个 run 已被别处记为已结束就停手（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二、五）。CLI 进程被直接结束（如 `kill -9`）时，worker 定期核验所属进程是否存活，发现它已退出即按收到 SIGTERM 收尾并释放会话（同一 ADR「父进程消失视同停止信号」条）。
- **无状态驱动（`submit` + `status`，下称后台/后台运行）**：没有常驻的「调度进程」。核心是一个**纯编排步骤 `reconcile.tick`**（`core/gherkai_core/reconcile.py`；判定与决策是 `gherkai_core.project` 的纯函数，副作用全经注入的 EventLog/RunStore/Launcher）：全量重放事件 → 推算 RunState 并条件写落库（投影只前进、不写 job 终态）→ 为这一轮已有结果的 job 先存判定明细、再写下它们的终态 → 推算当前应执行的动作 → 认领并启动下一个 job，或做到期的结束写。**任何宿主都可以调用它推进一步**：它不保存自身状态、不假设上一步由谁推进，这是「无状态」的含义。它同样遵守运行期限：时刻经宿主注入的时钟取，每一轮按当前时刻判断，过了期限减 60 秒不再认领，认领时算出的截止时刻以期限封顶、随启动交给启动器；已过停止启动的时刻、没有执行中的 job 而余下的 job 都没有启动时，做到期的结束写：没有启动的 job 记 skipped，run 随之成为终态，这次写以写下时没有执行中的 job 为条件（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二）。

不论哪种驱动，worker 与 `core` 之间的回传只有两类：**事件流**（`scope_started`/`step_done`/… 的逐条事件）与**进程退出信号**（退出码由父进程或平台观察得到，不由 worker 上报；[ADR 0024](../adr/0024-worker-core-protocol.md) 协议）。判定要求两者同时成立：事件内容完整且进程干净终止，缺一即不判通过（防假绿）。两种驱动的本质差别在于**有没有在线的接收方**：前台有在线接收方，`schedule` 全程在线、收到事件即处理，退出信号由 Engine adapter 当场观察；后台没有常驻接收方，事件流被持久化、退出信号也被转写成 `task_exited` 记入同一份日志，于是任何宿主都能仅凭重放这份日志推进（各组合的物理通道见 §5）。

两种驱动共享同一份 `core`（parse/plan/project/判定模型），但**一个 run 只属于一种驱动**。分界线是 `detached` 标记：`submit` 建 run 时写它（cloud 写在 runs 表的 STATE item 上，local 写在 run_state.json 顶层、每次写回保留）。前台 run 只在本机后端出现，云端后端的 run 都由 `submit` 提交、都带这个标记。cloud 的推进器是云端三 Lambda（它们对标记的两道判断见 §7）；local 由各 run 自己的 per-run 推进进程或 `status --wait` 的接力者推进，接力者是唯一会碰到别人 run 的一方，它同样只接力带标记的 run，对前台 run 只等待（§7 末段）。

`reconcile.tick` 有**四个宿主**在不同场景下调用它：local 的 per-run 进程（即 `submit` 时 `setsid` fork 出的推进进程）、**local** `status --wait` 的接力者（cloud 的 `--wait` 只在检测到停滞时 invoke kicker，不在本机执行 `tick`，使 status 所在机器无需 ECS 权限，见 §4b）、cloud 的 kicker Lambda、cloud 的 reconciler Lambda。四处执行的是同一份代码，差别只在注入的 adapter（事件从 SQLite 还是 DDB 读、job 以子进程还是 ECS RunTask 启动）。

![执行与推进全景：run 的在线循环与 submit 的无状态推进共用同一份 core，只换事件通道与退出观察者](../diagrams/run-execution.svg)

图注：图只画结构与指向，四个宿主分别是谁、三条物理通道各自的载体，真源是上面几段正文与 §5 的表。**图上的退出信号不表示 worker 自行上报**：退出码由父进程或平台观察到 worker 终止后送达推进器，观察者按组合各不相同，对位见 §5 的「退出观察者三对位」。可交互版（缩放 / 聚焦单个节点 / 追踪一条路径）：https://zhiyanliu.github.io/gherkai/run-execution.html

> why 与护栏：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（整体设计）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（分层）。

## 2. 三种组合一览

|           | **run（前台同步）**                                                                                                                                                        | **submit（后台运行）**                                                                                                                                                                                                                                             |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **local** | CLI 进程内 `schedule()`；worker 是本机子进程（fd3 事件流直达）；超时由 schedule 循环内计时到点；关闭 CLI 即中止                                                            | **per-run 推进进程**（`setsid` 脱离 CLI）循环调用 `tick`；事件旁路落 SQLite；该进程同时担任退出观察者；本机需保持开机                                                                                                                                                  |
| **cloud** | 不支持：`run` 给出云端后端即以退出码 2 结束，云端后端的执行只经 `submit`（[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 A） | **三 Lambda 事件驱动链**：kicker（冷启动）、reconciler（主推进）、exit-observer（退出观察），由事件串接、非调用链（§4b）；提交后关机也能执行至结束（例外：`--expose-local` 隧道模式下本机须保持开机联网，[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md)） |

此处明确一个贯穿全文的粒度：**一个 job 即一个 scope**——一个 `@scope` 分组即一个调度/执行单位（上云后确立，[ADR 0017](../adr/0017-cloud-execution-fargate-over-runtime.md)），§6 超时定时器的 per-(run,scope) 即 per-job。三种组合的详细解剖在 §3-§4，横切机制（事件通道/退出观察/超时）在 §5-§6。三种组合的权威：[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（决策 A：云端后端只支持 `submit`）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（两种驱动与后台运行全部决策）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0032](../adr/0032-fargate-execution-environment.md)（Fargate 执行面）。

## 3. 前台 `run` 的生命周期

```
plan(纯本地) → begin(落 definition + 初始态) → schedule 循环:
  ├─ 按并发闸取 job：已过停止启动的时刻(期限减 60 秒)、已发现 run 被别处结束、或已因 fail-fast / 使用方中断而中止 → 不启动、留在 pending；否则认领(记认领时刻)后启动 worker(每 scope 一个)
  ├─ 逐行消费 worker 事件流 → ScopeStarted 或其前一条非 attempted 的 SessionOpened（桌面 job 在浏览器会话建好后、建连之前发，设备 job 在取设备期间即发）置 RUNNING+会话血缘(session id)、每 job 完成先存判定明细、再写这个 job 的终态(RunPersistence)；事件原始行与退出记录同时落 events.db（--no-report 不写）
  ├─ 静默停滞由心跳检出；墙钟到截止时刻(认领时刻加 job 预算，以运行期限封顶)即停 → handle.stop(SIGTERM→宽限→SIGKILL)
  ├─ 认领被拒、重试之前读到终态或写 job 状态时得知 run 已被别处记为已结束 → 停手：运行中的 worker 按首次仲裁停下，此后不存明细、不写终态，排队的不再启动
  └─ 全部收敛 → schedule 交回执行事实(各 job 的判定、余下的 job 不再启动的来源) → finalize：最后一个 job 的终态写已使 run 成为终态则不再写，否则按来路做结束写(没有启动的 job 记 skipped、run 级写下原因)；读一次运行态、从记录组装汇总 → 文本汇总或 --json、退出码 + RunReport
```

这条路径只有本机后端，Engine adapter 是 `SubprocessEngine`：spawn 本机 worker 子进程，事件走专用 fd（`EVENTS_FD`，三通道分离：事件、SDK 噪声、诊断各占一条）。云端的 `FargateEngine` 只有 `start_scope`（把 job JSON 放 S3、以 `RunTask` 启动容器，启动之后即返回、不等 task 结束），由云端推进器经启动器调用，不进这条路径（[ADR 0034](../adr/0034-detached-batch-reconciler.md)「Engine port 演进」节）。

另有三项能力只存在于前台驱动循环，后台运行**不具备**：`--fail-fast` 早停与使用方中断（Ctrl-C 或 SIGTERM；两者走同一条停止路径，都派生 skipped/aborted 态，见 [ADR 0024](../adr/0024-worker-core-protocol.md) 终止契约「使用方中断」条），以及 `schedule` 中针对 network 瞬时故障的 job 级重试通道（把整个 job 重新执行）——后者**当前在 `run` 上并未启用**（`ScheduleOpts.network_retry` 默认 0，CLI 未暴露该参数），网络抖动的实际处置见 [`verdict-model.md`](./verdict-model.md) §3c，门控与两层分工见 [ADR 0028](../adr/0028-transient-network-ssl-resilience.md)。后台执行下失败一律隔离、逐 job 各自收敛（[ADR 0026](../adr/0026-schedule-module.md) 失败隔离、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一）。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（worker↔core 协议、三通道、退出码）、[ADR 0026](../adr/0026-schedule-module.md)（调度/心跳/优雅终止）、[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（决策 A：前台只有本机后端）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（实时写）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（两层网络重试）。

## 4. 后台运行 `submit` 的生命周期

### 4a. local 后端：per-run 推进进程

```
submit:plan → 落 definition + 全 pending 初始态 → fork per-run 推进进程(setsid 脱离 CLI)→ CLI 返回 run_id
per-run 进程:读回运行定义(读不到可用的运行定义时以结束写把 run 与未结束的 job 都记 error、不生成报告,以退出码 2 退出) → run_reconcile_loop 循环调用 tick
  ├─ tick 认领到 PENDING job(未过停止启动的时刻才认领) → SubprocessLauncher 启动本机 worker,收下这个 job 的截止时刻
  ├─ worker 的 fd3 原始事件行经 raw_sink 旁路落 SQLite(events 的持久通道)
  ├─ 每个执行中的 job 一个检查线程按墙钟比对截止时刻,到点停 worker(§6)
  ├─ worker 退出 → 本进程 handle.wait() 取 exitcode 写 task_exited(本进程同时担任"平台侧退出观察者")
  ├─ 每一轮 tick:job 一有结果即先存判定明细、再写下它的终态,随后才决定认领(写序见 §4c)
  └─ 最后一个 job 的终态写,或到期(已过停止启动的时刻、没有执行中的、余下的都没有启动)的结束写使 run 成为终态 → 生成报告 → 拆除临时资源,退出
status [--wait]:只读投影查进度;--wait 还能接力推进(只对 submit 的 run)——per-run 进程若终止,接力者执行同一个 tick 把 run 推到收敛(过了期限才接力的 run 不再启动 job,原进程认领的 job 判超时后收尾,§6);接力者读不到可用的运行定义时以退出码 2 结束、不写
```

要点：推进进程是 **per-run** 的（一个 run 一个，不是常驻守护进程）；`setsid` 使它在 CLI 与终端退出后继续存在；SQLite 里的事件表结构刻意镜像 DDB events 表（保持心智对称）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「端到端流程」节的 local 半边。

### 4b. cloud 后端：三 Lambda 链

![云端后台运行的事件级联：提交落库唤醒 kicker，worker 写事件唤醒 reconciler，任务停止经 exit-observer 转写为退出记录后收敛](../diagrams/execution-cloud-cascade.svg)

图注：本图画「链如何贯通」，谁被挡在链外见 §7 那张图。图上画了三个 Lambda 各自的主入口，**未画两处**：**kicker 的另两个入口**（查询进度时发现停滞而主动调起、超时定时器到点，见下条与 §6），以及退出观察那条路由背后是部署时即建好的常驻订阅、不由任何一方启动；并发安全的保证见下面几条。

- **kicker**：冷启动器，但不是「只负责启动首批的精简实现」——它与 reconciler 同 code、同权限，执行完整的 `tick`。除 runs 表 Stream 外还有两个入口：`status --wait` 检测到停滞时的主动调起（kickoff invoke，用于从停滞中恢复），以及 job timeout 到点的定时器调起（§6）。
- **reconciler**：主推进器。worker 每写入一批事件，Stream 即触发它执行一次 `tick`——事件既是数据也是「心跳」，推进由事件级联驱动，无常驻轮询。
- **exit-observer**：把 ECS STOPPED 事件翻译成 events 表里的 `task_exited` 记录（即 cloud 后端中观察到 worker 终止的一方）。它的触发面是 IaC 部署时建好的 EventBridge rule（按本 cluster 过滤 ECS task 状态变更 → STOPPED）——**常驻订阅、不由任何一方启动**；三个 Lambda **之间**没有互相启动/调用关系，各自订阅自己的事件源，链条由事件串接；仅有的主动 invoke 都来自 Lambda 之外（`status --wait` 与超时定时器调起 kicker，见上条与 §6）。
- 多宿主并发安全：`tick` 幂等，job 认领走 CAS 条件写（PENDING→RUNNING 只有一个写入方成功；run 已收尾后不再接受新的认领），投影落库走 HWM（投影只前进不后退的水位）与终态条件写；Stream 分片并发触发多个 Lambda 实例，叠加 `status --wait` 调起的 kicker，均安全。
- **并发上限：声明随 definition 传递，部署侧只留一道 cap**（与超时预算同构，二者都属 run 的定义）。`run` 与 `submit` 都把 `--max-concurrency` 落进 definition（`RunMeta.max_concurrency`），detached 的推进器一律读 meta：local per-run 进程与 `status --wait` 接力者都以 meta 为准，各自的 flag 只在 meta 无值时回落，接力不会改变这个 run 的并行度。同步 `run` 在同一进程内直接用 flag（不存在传递通道问题），meta 仍照常写入，只为使 definition 如实记录该值。cloud 后端取 `min(definition 声明, 部署侧 cap)`，cap 取自 reconciler/kicker 的 Lambda env `MAX_CONCURRENCY`（由 IaC 设定，值见 `stack.BackendStack.DEPLOY_SIDE_MAX_CONCURRENCY`），限制的是 worker（Fargate task）的并行数，语义为 per-run（单 run 内最多几个 job 并行），是**上限、不是真源**：cap 以内由提交侧决定；**local 无 cap**。声明超 cap 时不会静默按 cap 执行：`submit --backend cloud` 的 preflight 读取推进器 env 比对，超出即提示「本 run 将按 cap 并行，需要更高并发须改 IaC」，但**不阻断提交**（相比之下 `REPORT_DIR` 不一致会以退出码 2 结束）。旧 definition（无此值）按 1 处理，与该机制接通前的行为一致。为何 cap 归部署方、local 为何无 cap、为何超 cap 只提示不阻断，why 见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制四。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一-四、端到端流程、重议闸门）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（三 Lambda 的 IaC/权限/触发面）。

### 4c. 读侧：进度观察与结果落点

后台驱动的另一半是观察。事件流是**写模型**，读模型是它的投影 **RunState**（cloud 后端下是 runs 表的 STATE item，local 后端下是 `run_state.json`）：后台运行下它只由 `tick` 写（投影、job 的终态与到期的结束写），外部读者（`status`、`explain`、未来的 WebUI）读运行状态时**都不自行重放事件**；唯一的例外是 `explain` 为被中止或出错的 job 归约该 scope 的事件流，补取判定明细里没有的 step 记录，这只是只读视图、不改判定（各自读什么、何时才有内容，见本节末条）。读侧决定的是「读到的数据有多新、读到什么才算定论」：

- **`status`（不带 `--wait`）纯只读、零副作用**：数据新鲜度取决于最近一次 `tick` 的时刻；它不推进，也不 kickoff。
- **run 级 status 的取值语义**：执行期间 run 级只取 `pending`/`running`，且只进不退——认领在同一次写里把 job 与 run 级都置为 `running`；投影不越过 `running`、不写 job 终态，只在把某个 job 写成 `running` 时连带写 `running`，没有这样的 job 时（全部仍 pending，或投影里离开 pending 的 job 在库中都已是终态）不写 run 级、保留库中值；前台 `run` 的 job 第一次离开 pending 时也连带推进 run 级。run 级**终态**由使 run 成为终态的那次写落定：最后一个 job 的终态写（`commit_job_states`），或仍有未结束的 job 时的结束写（`end_run`）；前台 `run` 与后台推进用同一组写入口，**读到终态即 run 已结束、每个 job 都已是终态**；终态之后任何写入口都不再改它（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。由此，对未收尾的 run，读到 run 级 `pending` 即没有 job 离开 pending（规则与前提见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条）。`status` 的「推进可能未启动」提示要求 run 级为 `pending`、**所有 job 仍 pending**（后半条由前半条推出，保留只为防御旧版写者留下的记录），且这个 run 带后台标记（`detached`）时才输出：前台 run 刚建时同样全部 pending，但推进它的是前台进程、`--wait` 不接力，不提示。
- **退出码分层**（CI 接线时最易建立错误心智）：`submit` 的退出码只表示提交是否成功，**不是判定**；判定退出码由 `status --wait` 等到终态后给出。根因是 CLI 脱离后不再持有内存中的判定终值。各命令退出码的完整分工见 [`verdict-model.md`](./verdict-model.md) §5（本篇不重复它的表）。

收尾一侧决定的是「什么时候能读到什么」：写序、由写序推出的读者保证、已终态 run 在两个后端的重入，以及落地之后由谁读取。

- **后台的写序**：一次 `tick` 里依次是：① 投影写（只前进、不越过 `running`、不写 job 终态）→ ② 这一轮已有结果、带认领时刻的各 job 先存判定明细（`jobs/*.json`，出自这一轮读到的同一份事件快照），任一份存不成即抛出，这一轮不写终态、也不认领与做结束写 → ③ 以一次终态写（`commit_job_states`）记下它们的终态，记下最后一个 job 终态的那次写使 run 成为终态 → ④ 推进决策：在这一轮读到的运行态加上 ③ 的作用上认领并启动 pending 的 job；已过停止启动的时刻、没有执行中的 job 而仍有未启动的 job 时改做到期的结束写（`end_run`，没有启动的 job 记 skipped）→ ⑤ 使 run 成为终态的那次写（③ 或 ④ 的结束写）是**提交点**，之后由宿主写入派生的 RunReport（只在 `tick` 报告这一方的写使 run 成为终态之后才写，宿主经 `reconcile.write_report_from_record` 读一次运行态、与判定明细一起组装后生成，读与写的失败都被隔离，不会回退已结束的 run；`tick` 开头读到 run 已是终态，或这一方的写因 run 已被别处结束而写不成时，宿主不写报告）。② 可以重做、覆盖同键（重叠推进时各记录的先后见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三的开头），每个 job 的终态只写成一次，使 run 成为终态的写只有一方写成，⑤ 的报告只由这一方写一次；local per-run 进程与 cloud reconciler 共用 `core` 的同一个推进步骤。读不到可用的运行定义时不经推进步骤：后台推进以结束写把 run 与未结束的 job 都记 `error`，说明是读不到的原因，不存明细、不生成报告。前台 `run` 的写序见 §3：每个 job 结束时先存明细、再写它的终态，余下没有启动的 job 由结束写结束，报告同样由使 run 成为终态的一方从记录生成。
- **由写序推出的读者保证**：**读到一个由执行结果结束的 job 的终态，即它的判定明细已保存**（保存成功之后才写终态，[ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条④「收尾各步的先后与之后会不会变」的 K3；两个推进方重叠推进时的边界见同一条；由结束写结束的 job（没有启动的）没有判定明细，状态与说明只在运行态里，见 [ADR 0030](../adr/0030-realtime-persistence-seam.md) 决定三「commit point 的意义」）；RunReport 则是提交点之后的派生物，「已读到终态、报告文件尚缺」是合法状态（一直缺的情形见同一条的「已获接受的边界」），读者不应把它当判定真源。落点：local 后端下是 `--report-dir/<run_id>/`，cloud 后端下是 S3 桶里的 `<report_dir>/<run_id>/`；cloud `submit` 的 `--report-dir` 须与推进器侧一致（提交前探活会比对，不一致则以退出码 2 结束），否则 run 执行完成后在提交者给出的前缀下找不到结果。
- **已终态 run 在两个后端的重入**：cloud 后端的云端推进器每次调用先读运行态，读到已提交终态即整体不动作（§7 里 reconciler 的第二道判；RunReport 缺失时的处理见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 端到端流程 cloud 一节标着「明确接受的代价」的一句）；local 后端的 `status --wait` 同守两道判断（只接力 submit 的 run、读到已终态不接力）；两个后端的 `tick` 自身也先读运行态，读到已收尾即停止推演，这一步覆盖宿主判断之后、`tick` 读取运行态之前插入的收尾（读取之后才发生的收尾，本轮仍继续处理），本机推进循环随之退出、不写报告；对前台 `run` 正在执行的 run，它只等待到终态、不接力。
- **落地之后由谁读取**：`status` 读投影 RunState（`--json` 时另附 `artifacts` 键，给出报告 / 判定明细 / 元信息的约定落点；各键何时有内容见 [`cli-json-contract.md`](./cli-json-contract.md) 的字段表）；`explain` 读**已落库的判定明细**（step 级失败原因与 `kind=evidence` 的证据指针），回答「这一步为何如此判定」；对 aborted 或 error 且仍有无记录 step 的 job，另从事件流补取已执行完的 step 的记录与证据（[ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策七）。两者都受落地时机约束：两种运行方式都逐 job 落库，每个 job 得出结果的那一轮在写它的终态之前保存它的判定明细，run 还没结束时即可读到已完成的 job（后台推进的步骤、必要契约与已获接受的边界见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条④「收尾各步的先后与之后会不会变」）；`explain` 在各种落地情形下给哪句提示见 [ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策四。用法与退出码见 [`docs/user-guide/running-and-results.md`](../user-guide/running-and-results.md)，`--json` 字段见 [`cli-json-contract.md`](./cli-json-contract.md)。

最后一条不对称（**能否中途终止**）：cloud 的 `--wait` 检测到停滞时只是调起 kicker（fire-and-forget），调起后随时可以离开，云端链会自行执行至结束；local 的 `--wait` 接力者与 per-run 进程执行同一段幂等推进、可以并存，per-run 进程仍在时退出接力者无影响；per-run 进程已终止时接力者**才是唯一推进器**，终止它 run 即就地停止（已 claim job 的计时也随进程一起丢失，由下一次接力恢复）。根因是主推进器的位置不同（云端 Lambda 与本机进程）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制三：投影钳制与条件写、「run 级状态只进不退」条；「命令形态」节：status/退出码）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（终态提交点）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)（决定五：退出码语义）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策三：查询类命令的 `--json` 与 `artifacts`）、[ADR 0042](../adr/0042-step-evidence-and-explain.md)（决策四：`explain` 以判定明细为骨架；决策七：被中止 job 的 step 记录从事件流补取）。

## 5. 同一条事件流的三条物理通道（横切对照）

§3-§4 已按组合纵切给出生命周期，本节起转为横切，考察跨组合的机制。第一条是 §1 提到的那条事件流：逻辑上它在三个组合里完全同构（同一套事件、同一份解析），物理载体却各不相同。

| 组合         | worker 写入何处                      | 读取方与读取方式                                                                     |
|--------------|--------------------------------------|--------------------------------------------------------------------------------------|
| local run    | 专用 fd（`EVENTS_FD`）               | CLI 进程 schedule 逐行阻塞读；同时经 `raw_sink` 旁路原样落 SQLite，并在事件流结束或 worker 被停止后写一条退出记录，库的形态与 local submit 相同（`explain` 补取被中止 job 用；`--no-report` 不写） |
| local submit | 同上 fd                              | per-run 进程读取的同时经 `raw_sink` **旁路原样落 SQLite**；`tick` 从 SQLite 全量重放 |
| cloud submit | worker 直接 PutItem 进 DDB events 表 | events 表 **Stream 触发 reconciler** Lambda；`tick` 从表里全量重放                   |

events 表里有**两个键空间**，在同一个 PK 下靠 SK 排序区分（`seq` 是 NUMBER 型 SK，Query 升序读）：

```
PK = run_id#scope_id
  SK = 1, 2, 3 … n     worker 事件本体：每 PK 单写者、连续递增
  …（大段空号）…
  SK = 保留高位        退出观察者写的 exit 记录：不入 seq 段
```

两类 item 按 `item_type` 属性区分（事件本体不带此属性），高位常数与属性名的真源在 `fargate_engine` 的 schema 常量。读端是无状态的 `DdbEventLog.records()`：读整个 PK、按 `item_type` 分流后交给重放；超时处置路径只需判断某个 scope 是否已退出，用 `has_exit` 做单点查询。

**退出观察者三对位**（谁观察到 worker 终止）：前台由 Engine adapter 自行观察（subprocess 的 `proc.wait`）；local `submit` 下是 per-run 进程的 `handle.wait()`；cloud `submit` 下是 exit-observer Lambda。另有一个例外情形：worker 根本未启动（`launch` 抛异常）时不存在平台侧观察者，由 `tick` 自行补一条退出码未知、带「起 worker 失败」原因的退出记录，并记下失败的那一刻作退出时刻（它晚于这个 job 的截止时刻时投影按超时处理，与前台起 worker 失败的处理相同，见 §6），下一轮按「有退出记录、退出码未知 → error」收敛；若不补写，该 job 已被认领为 RUNNING 却永不会有事件与退出记录，整个 run 停滞。

**诊断的落点**（事件流之外的另一条通道）：worker 的 stdout（引擎 SDK 噪声）与 stderr（worker 自身的诊断）默认带 `[worker <scope>:out|err]` 前缀透传到**推进器进程的 stderr**，落点随推进器而变：前台 `run` 直接输出到终端，加 `--quiet` 时改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），结束时只输出一行路径；cloud 后端 worker 在云端执行，日志在该 task 的 CloudWatch 日志组；local `submit` 的 per-run 推进进程自身的 stdout/stderr 落 `<report-dir>/<run_id>/reconcile.log`，worker 的透传行同落其中。判定归因只写入 `jobs/*.json` 的 `message`。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（事件协议/DDB 态、三通道）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一：退出记录独立键空间；机制二：两件都要的收敛判据、launch 失败补偿）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策二：`--quiet` 的落点）。

## 6. `job` 超时预算（timeout）：三路形态相同的 enforce

每个 `job` 有超时预算，按**墙钟**（真实流逝时间）计。声明方式为 `@timeout:N` tag 或 `--default-job-timeout`，两者都没给时由 plan 按测试目标补缺省（任何目标都有上限 7200 秒、不能关闭超时，设备 scope 另有下限），定值随 definition 落在 `Job.timeout_s`（ADR/CONTEXT 里称「job 墙钟预算」）；取值、覆盖与校验顺序见 [ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节与 [ADR 0051](../adr/0051-device-session-lifecycle-and-app-distribution.md) 决策 2。三条执行路径**各自落实同一形态的 enforce**（enforce 即 ADR 与 code 对这一形态的用词）：到点 → 停止 worker → 记下收场态。三条路径的截止时刻取法相同：认领时刻加预算，与运行期限取较早的一个，都按墙钟比较，两者相等时算预算；起作用的是 job 自己的预算时归因 `error + timeout`，是运行期限时记 `aborted`、没有归因（说明是「这个 run 已超过允许运行的时间，job 被中止」）。后台路径不把起作用的是哪一个记进退出记录，投影时由认领时刻、预算与期限重算（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二）。

| 路径         | 到点机制                                                                                                                                                                                                          | 停止方式                                                                                                                                                                                             |
|--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 前台 `run`   | schedule 循环内按墙钟比较截止时刻：认领时刻加预算，与运行期限取较早的一个（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二）                                                                   | `handle.stop(grace)`（SIGTERM→宽限→SIGKILL） |
| local submit | 截止时刻由 `tick` 在认领时算出（认领时刻加预算，与运行期限取较早的一个）、随启动交给 launcher；per-run 进程为每个执行中的 job 起一个检查线程，每 0.25 秒读一次墙钟（与 `tick` 取认领时刻同一个读取点），过了截止时刻即停，检查持续到 worker 进程退出；worker 在截止时刻之后、下一次检查之前自行退出的，退出记录不带超时标志，投影按它的退出时刻判为超时（见本节表后一段）。该进程若中断，检查随之丢失——接力者按库里的 `claimed_at` 按同一算法重算截止时刻，每轮推进时按墙钟查看别人认领的 job，墙钟严格晚于截止时刻加 10 秒仍无退出记录即判超时。这个条件保证不了不抢先：原进程还在、它停下的 worker 仍在停止宽限内收尾时，接力者同样会补写；补写之后、真实退出之前读到补写那一条的一轮推进按超时存下这个 job 的判定明细、写下它的终态，运行态里的终态此后不再改变。判定明细按 scope_id 保存，原进程与接力者同时推进、其中一方读到的是随后的真实退出时，它存下的明细会覆盖先存的那一份，与运行态里的终态不一致；改法已定、尚未实装（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二「本机接力的改法」） | 本进程启动的 job：`handle.stop(grace)`（协作式停止，同前台 local，grace 取引擎最小宽限）；接力恢复的他人 job：接力者手里没有它的 handle、不停止它，也不核实认领方或 worker 是否已经退出；只要墙钟严格晚于截止时刻加 10 秒、仍没有退出记录，就补写一条结果未知、带 `timed_out` 的退出记录收敛（只在还没有退出记录时写入，见本节表后一段） |
| cloud submit | 启动 task 之前为该 job **设置一个一次性到点定时器**，到点时刻就是 `tick` 交来的截止时刻（EventBridge Scheduler one-time；与 §4b exit-observer 的 EventBridge **rule** 同名不同物：那是事件总线订阅，这是独立定时服务）                                  | 到点由 kicker 处置，整条链见下图；另有任意 `tick` 的防御扫描作为双保险                                                                                                                               |

后台两路的退出记录只记事实，是否按超时处理在投影里判断，以写下这个 job 终态的那一轮的判断为准，规则对两路相同。退出记录带两项：超时标志（`timed_out`，发过超时的停止请求，或接力者、云端处置补写未知退出时已判为超时）与退出时刻（`exited_at`：本机是推进进程看到 worker 退出的那一刻，云端是 task 的执行停止时刻，起 worker 失败时是失败的那一刻；补写的未知退出没有这一项）。投影时带超时标志、或退出时刻晚于由 `claimed_at`、预算与期限算出的截止时刻的，都按超时处理，内容已完整（干净退出且发了 `scope_done`）的照旧不改判。这样 worker 在截止时刻之后、停止请求发出之前自己异常退出时，前台、本机后台与云端后台的判定相同；云端的退出观察者只看得到 task 对象、读不到截止时刻，所以判断放在投影里、不放在写入方。接力者与云端处置补写的未知退出只在这个 job 还没有退出记录时写入（判断与写入是同一次条件写），恰在它查过之后才落下的真实退出记录不会被盖掉；补写之后才到的真实退出照常覆盖补写的那一条。云端处置查到已停止的 task 时写的不是未知退出，而是从 task 对象取得的真实退出（退出时刻取 task 的执行停止时刻，与退出观察者同一算法），与退出观察者的写入一样照常覆盖同一条记录。

cloud 路径的超时处置是一条多跳链，时序如下图。这里的「定时器」（ADR/code 里称 arm 一个 one-time schedule，中文记作「武装」）是 per-(run,scope) 的短生命周期资源：schedule 名为 `{prefix}job-timeout-<sha1(run_id#scope_id) 摘要>`（前缀取 `gherkai_runtime.names` 这一命名真源，IaC 的 IAM 资源域同源推导），到点触发后即自动删除，因此控制台中通常看不到它。

![云端超时 enforce 链：启动 task 时设置的一次性定时器到点调起 kicker，停止 worker 后由 exit-observer 写成带超时标志的退出记录，回到既有链收敛](../diagrams/execution-timeout-chain.svg)

图注：本图只画云端这一路「如何停止 worker」，另两路的到点机制与停止方式见上表；定时器的到点时刻为这个 job 的截止时刻：`claimed_at`（领取该 job 的时刻）加上该 job 的墙钟预算，与运行期限取较早的一个（由 `tick` 在领取时算好），与防御扫描同一算法，设置定时器晚于领取的那段间隔不推后到点。定时服务只承诺分钟精度，可能早于这一刻触发，因此到点的一方**先确认这个 job 仍为 RUNNING 且没有退出记录，再由 `claimed_at`、预算与期限重算截止时刻、复查是否已到**（读到的时刻严格晚于截止时刻才算已到）：已到则执行停止；未到且相差不超过一分钟则等到截止时刻（每次至少等 1 秒），重新确认 job 状态并重读时钟后才执行停止（等待期间时钟被回拨、或读到的恰好是截止时刻而仍未到时，在这次调用的等待额度（至多一分钟，各次等待合计）内接着等，额度用完仍未到则本次不停止）；相差超过一分钟则本次不停止，交给防御扫描（取舍见 [ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节「到点不早于 deadline」条）。重复到点、定时器与防御扫描同时命中均无害。防御扫描在截止时刻之外另加固定余量。`StopTask` 的 reason 里带一个哨兵串，exit-observer 据此把这条退出记录标记为超时停止；哨兵串之后按起作用的是预算还是期限分别写，只供在 ECS 控制台查看。停止之后**记为什么状态**（超时归因落在哪一类、与 fail-fast 共用哪个字段、按什么优先级判定）见 [`verdict-model.md`](./verdict-model.md) §3c（归因优先级图）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节（取舍/归因链/防御扫）、[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「截止时刻与说明」（退出时刻与投影判断）、[ADR 0019](../adr/0019-feature-tags-scope-and-engine.md)（`@timeout:` tag）、[ADR 0051](../adr/0051-device-session-lifecycle-and-app-distribution.md)（决策 2：设备 scope 的缺省墙钟与下限）。

## 7. 云端 Lambda 对后台标记的两道判断

云端后端只有 `submit` 一种执行方式（[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 A），`submit --backend cloud` 建 run 时在 STATE 上写下 `detached` 标记，所以云端的每个 run 都带它。云端推进器按这个标记做两道判断，位于不同层：没有标记的 run 不被推进、不写退出记录；对 `submit` 提交的 run，两道判断恒放行。

![两道判断：新 run 落库这一路在订阅侧即被过滤，事件批次与任务停止事件只能进入函数后再查询该 run 的后台标记](../diagrams/execution-detached-gates.svg)

图注：能在事件源层过滤的即在该层挡下，不能过滤的进入 handler 后再判断——事件批次与任务停止事件上都不带 `detached`，只能反查这个 run。图上四个判点里只有前两个（新 run 落库、handler 判断是不是 submit 提交到后台执行的 run）是本节所说的那两道判断；「该 run 已收尾？」与 exit-observer 那一道各自防范另一件事，见下面三条。§4b 那张时序图画「链如何贯通」，本图画「谁被挡在链外」。

- **kicker**：runs 表 Stream 的事件源 **filter** 固定为 INSERT 且 detached=true。
- **reconciler**：`tick` 装配前查 `is_detached`（日志 `skip: run … 不是 submit 提交到后台执行的 run`）；紧接的第二道判断读 run 终态（日志 `skip: run … 已结束，不再改写它的结果`），针对的不是本节这件事。两道判断都在 reconciler 与 kicker **共用的装配**里，kicker 无论从哪个入口进入（新 run 落库、`status --wait` 检测到停滞后的调起、超时定时器到点）都要经过，因此图上这两个判点不标注 Lambda 名；冷启动那一路画成直达，只为看清「谁在哪一层被挡」。
- **exit-observer**：判据同为 `is_detached`。它不推进，没有标记的 run 它不写退出记录。

本机侧是同一道判断、换了落点：`submit --backend local` 把标记写在 run_state.json 顶层（之后每次写回保留），`status --wait` 的接力者据 `LocalRunStore.is_detached` 分流——不是 submit 的 run 只轮询等待并提示「只等待它结束、不接力推进」，不会与前台 run 的进程双开推进器。等待或接力被 Ctrl-C 打断时以退出码 130 结束、打一句说明，不打回溯。

> 权威：[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（决策 A：云端后端只支持 `submit`）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（Stream/filter 资源；events 表那条只滤得掉 TTL 删除，`detached` 那半只能在 handler 内判）。

## 8. 延伸阅读

| 想深入的主题                                                      | 去哪读                                                                 |
|-------------------------------------------------------------------|------------------------------------------------------------------------|
| 无状态批量运行全部决策/护栏/被拒方案                              | [ADR 0034](../adr/0034-detached-batch-reconciler.md)                   |
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
