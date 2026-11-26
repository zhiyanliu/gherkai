# 执行与推进模型导览：本机前台、本机后台与云端后台

> 本文讲**机制如何协同工作**，不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。「三种组合下推进器分别是什么」这类问题的答案散在五六个 ADR 里，本文是它们汇总后的横切视图。

## 1. 心智模型：两种驱动、同一份 `core`

gherkai 执行一个 run 有**两种驱动模型**，按命令分流：

- **同步驱动（`run`，下称前台）**：CLI 进程内的 `schedule()`（`core/gherkai_core/schedule.py`）全程在线，在一个循环内完成启动 worker、消费事件流、判定超时、收集结果。前台只有本机后端：`run` 给出云端后端时在开始执行之前以退出码 2 结束，云端后端只经 `submit`（[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 A）。按 Ctrl-C 或向 CLI 发 SIGTERM 时，CLI 的信号处理器只记下中断，`schedule` 轮询到后走与 fail-fast 同一条停止路径：首次中断请求全部 worker 协作停止（向 worker 的进程组发 SIGTERM、宽限到期再 SIGKILL），再次中断时改用零宽限；照常收集结果后，没有启动的 job 由结束写记为 skipped，run 的状态按各 job 的状态得出，以 130 / 143 结束（[ADR 0024](../adr/0024-worker-core-protocol.md) 终止契约「使用方中断」条）。它遵守运行期限：过了期限减 60 秒不再启动 job，到期限时停下运行中的 worker；起 worker 之前先认领，发现这个 run 已被别处记为已结束就停手（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二、五）。CLI 进程被直接结束（如 `kill -9`）时，worker 定期核验所属进程是否存活，发现它已退出即按收到 SIGTERM 收尾并释放会话（同一 ADR「父进程消失视同停止信号」条）；这个 run 的记录停在未结束，经处置结束（§4d）。
- **无状态驱动（`submit` + `status`，下称后台/后台运行）**：没有常驻的「调度进程」。核心是一个**纯编排步骤 `reconcile.tick`**（`core/gherkai_core/reconcile.py`；判定与决策是 `gherkai_core.project` 的纯函数，副作用全经注入的 EventLog/RunStore/Launcher）：全量重放事件 → 推算 RunState 并条件写落库（投影只前进、不写 job 终态）→ 为这一轮已有结果的 job 先存判定明细、再写下它们的终态 → 推算当前应执行的动作 → 认领并启动下一个 job，或做到期的结束写。**任何宿主都可以调用它推进一步**：它不保存自身状态、不假设上一步由谁推进，这是「无状态」的含义。它同样遵守运行期限：时刻经宿主注入的时钟取，每一轮按当前时刻判断，过了期限减 60 秒不再认领，认领时算出的截止时刻以期限封顶、随启动交给启动器；已过停止启动的时刻、没有执行中的 job 而余下的 job 都没有启动时，做到期的结束写：没有启动的 job 记 skipped，run 随之成为终态，这次写以写下时没有执行中的 job 为条件（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二）。

不论哪种驱动，worker 与 `core` 之间的回传只有两类：**事件流**（`scope_started`/`step_done`/… 的逐条事件）与**进程退出信号**（退出码由父进程或平台观察得到，不由 worker 上报；[ADR 0024](../adr/0024-worker-core-protocol.md) 协议）。判定要求两者同时成立：事件内容完整且进程干净终止，缺一即不判通过（防假绿）。两种驱动的本质差别在于**有没有在线的接收方**：前台有在线接收方，`schedule` 全程在线、收到事件即处理，退出信号由 Engine adapter 当场观察；后台没有常驻接收方，事件流被持久化、退出信号也被转写成 `task_exited` 记入同一份日志，于是任何宿主都能仅凭重放这份日志推进（各组合的物理通道见 §5）。

两种驱动共享同一份 `core`（parse/plan/project/判定模型），但**一个 run 只属于一种驱动**。`submit` 建 run 时写下 `detached` 标记（cloud 写在 runs 表的 STATE item 上，local 写在 run_state.json 顶层、每次写回保留），它只作描述（`list-runs --json` 的 `detached`），两个后端的任何判断都不读它。前台 run 只在本机后端出现，云端后端的 run 都由 `submit` 提交。cloud 的推进器是两个推进 Lambda，它们的各个入口先过同一道闸（§7）。local 的 run 只由建它的那个进程推进：前台是执行 `run` 的进程，后台是 per-run 推进进程；它从建 run 起持有 run 目录上的生命期锁直到退出，本机任何时刻至多一个推进器（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策三、[ADR 0034](../adr/0034-detached-batch-reconciler.md)「推进器与触发源」）。它没写终态就退出时没有别的一方接着推进，这个 run 只能经处置结束（§4d）；本机的 `detached` 标记只作描述，不参与任何判断（§7 末段）。

`reconcile.tick` 有**三个宿主**在不同场景下调用它：local 的 per-run 进程（即 `submit` 以新会话启动的本机后台推进进程）、cloud 的 kicker Lambda、cloud 的 reconciler Lambda。`status --wait` 在两个后端都不执行 `tick`：local 的只等待、条件成立时处置（§4d），cloud 的在检测到停滞时调用 kicker，kicker 不认这一载荷、只记一行日志，不推进（§4b）。三处执行的是同一份代码，差别只在注入的 adapter（事件从 SQLite 还是 DDB 读、job 以子进程还是 ECS RunTask 启动）。

![执行与推进全景：run 的在线循环与 submit 的无状态推进共用同一份 core，只换事件通道与退出观察者](../diagrams/run-execution.svg)

图注：图只画结构与指向，三个宿主分别是谁、三条物理通道各自的载体，真源是上面几段正文与 §5 的表。**图上的退出信号不表示 worker 自行上报**：退出码由父进程或平台观察到 worker 终止后送达推进器，观察者按组合各不相同，对位见 §5 的「退出观察者三对位」。可交互版（缩放 / 聚焦单个节点 / 追踪一条路径）：https://zhiyanliu.github.io/gherkai/run-execution.html

> why 与护栏：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（整体设计）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（分层）。

## 2. 三种组合一览

|           | **run（前台同步）**                                                                                                                                                        | **submit（后台运行）**                                                                                                                                                                                                                                             |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **local** | CLI 进程内 `schedule()`；worker 是本机子进程（fd3 事件流直达）；超时由 schedule 循环内计时到点；关闭 CLI 即中止，停住的 run 经处置结束（§4d）                                  | **per-run 推进进程**（`submit` 以新会话启动、脱离 CLI）自己建 run，再循环调用 `tick`；事件旁路落 SQLite；该进程同时担任退出观察者，带 `--expose-local` 时也是隧道的宿主；本机需保持开机，它退出之后 run 经处置结束（§4d） |
| **cloud** | 不支持：`run` 给出云端后端即以退出码 2 结束，云端后端的执行只经 `submit`（[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 A） | **三 Lambda 事件驱动链**：kicker（冷启动）、reconciler（主推进）、exit-observer（退出观察），由事件串接、非调用链（§4b）；提交后关机也能执行至结束（例外：`--expose-local` 隧道模式下隧道由本机的隧道守护进程持有，本机须保持开机联网，[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md)） |

此处明确一个贯穿全文的粒度：**一个 job 即一个 scope**——一个 `@scope` 分组即一个调度/执行单位（上云后确立，[ADR 0017](../adr/0017-cloud-execution-fargate-over-runtime.md)），§6 超时定时器的 per-(run,scope) 即 per-job。三种组合的详细解剖在 §3-§4，横切机制（事件通道/退出观察/超时）在 §5-§6。三种组合的权威：[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（决策 A：云端后端只支持 `submit`）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（两种驱动与后台运行全部决策）、[ADR 0026](../adr/0026-schedule-module.md)（同步 schedule）、[ADR 0032](../adr/0032-fargate-execution-environment.md)（Fargate 执行面）。

## 3. 前台 `run` 的生命周期

```
plan(纯本地) → begin 建 run(先查报告目录,在暂存目录上取锁、写定义与全 pending 初始态,再改名成 run 标识) → schedule 循环:
  ├─ 按并发闸取 job：已过停止启动的时刻(期限减 60 秒)、已发现 run 被别处结束、或已因 fail-fast / 使用方中断而中止 → 不启动、留在 pending；否则认领(记认领时刻)后启动 worker(每 scope 一个)
  ├─ 逐行消费 worker 事件流 → ScopeStarted 或其前一条非 attempted 的 SessionOpened（桌面 job 在浏览器会话建好后、建连之前发，设备 job 在取设备期间即发）置 RUNNING+会话血缘(session id)、每 job 完成先存判定明细、再写这个 job 的终态(RunPersistence)；事件原始行与退出记录同时落 events.db（--no-report 不写）
  ├─ 静默停滞由心跳检出；墙钟到截止时刻(认领时刻加 job 预算，以运行期限封顶)即停 → handle.stop(SIGTERM→宽限→SIGKILL)
  ├─ 认领被拒、重试之前读到终态或写 job 状态时得知 run 已被别处记为已结束 → 停手：运行中的 worker 按首次仲裁停下，此后不存明细、不写终态，排队的不再启动
  └─ 全部收敛 → schedule 交回执行事实(各 job 的判定、余下的 job 不再启动的来源) → finalize：最后一个 job 的终态写已使 run 成为终态则不再写，否则按来路做结束写(没有启动的 job 记 skipped、run 级写下原因)；读一次运行态、从记录组装汇总 → 文本汇总或 --json、退出码 + RunReport
```

起好隧道之后，前台 `run` 就装上执行期间用的那个只记标志的中断处理器（进入命令时已被设为忽略的信号不装、保持忽略），一直到命令结束，结束时先把标准输出写完并刷新、再恢复：begin 那一段（建 run、打开 worker 日志、建事件库）与装配引擎期间按下的 Ctrl-C（或收到的 SIGTERM）只记下、不打断其中的任何一步，解释器里没有中断引起的异常。它在两处看这个标志：建 run 之前看到即不建 run、什么都没留下，一句「没有开始执行」；启动第一个 job 之前（打出「开始运行」那一行之前）看到时 run 已建成，不启动任何 job，本进程持着生命期锁、就是推进器，由它自己以说明表「使用方中断」那一行做结束写（全部 job 还是 pending、记 skipped），写成之后生成报告、说这个 run 已因中断记为已结束，结束写失败时说明没有 job 开始执行、这个 run 停在未结束，并给出把它记为已结束的 `settle-runs` 整条命令；退出码都按信号取，SIGINT 为 130、SIGTERM 为 143（[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md) 决策 3「前台 `run`」、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。

这条路径只有本机后端，Engine adapter 是 `SubprocessEngine`：spawn 本机 worker 子进程，事件走专用 fd（`EVENTS_FD`，三通道分离：事件、SDK 噪声、诊断各占一条）。云端的 `FargateEngine` 只有 `start_scope`（把 job JSON 放 S3、以 `RunTask` 启动容器，启动之后即返回、不等 task 结束），由云端推进器经启动器调用，不进这条路径（[ADR 0034](../adr/0034-detached-batch-reconciler.md)「Engine port 演进」节）。给了 `--expose-local` 时，begin 之前先取创建时刻、起隧道并把 job 文本里的 origin 换成公网地址：隧道是本进程里的一个会话，本进程怎样退出它都随之消失，正常路径上经 atexit 关闭（[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md) 决策 3「前台 `run`」）。

另有三项能力只存在于前台驱动循环，后台运行**不具备**：`--fail-fast` 早停与使用方中断（Ctrl-C 或 SIGTERM；两者走同一条停止路径，都派生 skipped/aborted 态，见 [ADR 0024](../adr/0024-worker-core-protocol.md) 终止契约「使用方中断」条），以及 `schedule` 中针对 network 瞬时故障的 job 级重试通道（把整个 job 重新执行）——后者**当前在 `run` 上并未启用**（`ScheduleOpts.network_retry` 默认 0，CLI 未暴露该参数），网络抖动的实际处置见 [`verdict-model.md`](./verdict-model.md) §3c，门控与两层分工见 [ADR 0028](../adr/0028-transient-network-ssl-resilience.md)。后台执行下失败一律隔离、逐 job 各自收敛（[ADR 0026](../adr/0026-schedule-module.md) 失败隔离、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一）。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（worker↔core 协议、三通道、退出码）、[ADR 0026](../adr/0026-schedule-module.md)（调度/心跳/优雅终止）、[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（决策 A：前台只有本机后端）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（实时写）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（两层网络重试）。

## 4. 后台运行 `submit` 的生命周期

### 4a. local 后端：per-run 推进进程

```
submit:plan 与各项检查 → 补全 job(账号比对、设备请求、安装包上传) → 以新会话启动 per-run 推进进程,经它的标准输入交出建 run 所需的输入 → 等回报 → 输出 run_id 后返回
per-run 进程:取创建时刻 → 起隧道(给了 --expose-local 时) → 生成运行定义 → 查 submit 是否还在(已不在即不建 run、退出) → 建 run(先查报告目录,在暂存目录上取锁、写定义与全 pending 初始态,再改名成 run 标识) → 装配、打开 reconcile.log → 回报 submit → run_reconcile_loop 循环调用 tick(用自己生成的那份运行定义,不从记录读回)
  ├─ tick 认领到 PENDING job(未过停止启动的时刻才认领) → SubprocessLauncher 启动本机 worker,收下这个 job 的截止时刻
  ├─ worker 的 fd3 原始事件行经 raw_sink 旁路落 SQLite(events 的持久通道)
  ├─ 每个执行中的 job 一个检查线程按墙钟比对截止时刻,到点停 worker(§6)
  ├─ worker 退出 → 本进程 handle.wait() 取 exitcode 写 task_exited(本进程同时担任"平台侧退出观察者")
  ├─ 每一轮 tick:job 一有结果即先存判定明细、再写下它的终态,随后才决定认领(写序见 §4c)
  └─ 最后一个 job 的终态写,或到期(已过停止启动的时刻、没有执行中的、余下的都没有启动)的结束写使 run 成为终态 → 生成报告 → 关闭隧道会话(有隧道时),退出
status [--wait]:只读运行态查进度;--wait 只等待,每轮做一次处置(§4d),不执行 tick、不认领、不起 worker;per-run 进程不在了,run 只能经处置结束
```

要点：推进进程是 **per-run** 的（一个 run 一个，不是常驻守护进程）；以新会话启动使它在 CLI 与终端退出后继续存在；一个本机 run 从建立到结束都在这一个进程里，步骤与次序同前台 `run`；SQLite 里的事件表结构刻意镜像 DDB events 表（保持心智对称）。submit 与它之间的交接（一行一条的消息、对端还在不在的判据）在 `gherkai_runtime.handoff`：回报之前它的输出接在 submit 的标准错误上、不启动子进程，回报之后改接 `reconcile.log`；起隧道、建 run 或装配失败时回报原因，submit 以退出码 2 结束。它在 run 未结束时退出的各个出口（读写记录失败、事件库出错、记录写下之后准备执行用的文件失败）都在说明里给出把这个 run 记为已结束的 `settle-runs` 整条命令，前台 `run` 在同样的出口给同一句，只有「重新执行」与「重新提交」之别；因运行态解析不了而退出的给的是 `settle-runs` 对 `unreadable` 的那一句（处置方也不结束它）。submit 在回报之前读到它退出时不知道 run 标识，给不带 run 标识的那一条（它同时清理暂存目录）（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策八「管它的进程退出而 run 未结束的出口」）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「端到端流程」节的 local 半边、[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md) 决策 3「本机 `submit`」（建 run 的次序、交接与一方先退出时各怎样）。

### 4b. cloud 后端：三 Lambda 链

![云端后台运行的事件级联：提交落库唤醒 kicker，worker 写事件唤醒 reconciler，任务停止经 exit-observer 转写为退出记录后收敛](../diagrams/execution-cloud-cascade.svg)

图注：本图画「链如何贯通」，各入口先过的那道闸与 run 结束之后的清扫见 §7 那张图。图上画了三个 Lambda 各自的主入口，**未画两处**：**kicker 的另几个入口**（使 run 成为终态的那次写触发的清扫、job 超时定时器到点、run 的两次定时触发到点，见下条与 §6、§7），以及退出观察那条路由背后是部署时即建好的常驻订阅、不由任何一方启动；并发安全的保证见下面几条。

- **kicker**：冷启动器，但不是「只负责启动首批的精简实现」——它与 reconciler 同 code、同权限，执行完整的 `tick`。runs 表 Stream 上有两条过滤：STATE 条目的新建（过闸之后先建这个 run 的两次 run 级定时触发，再做首轮推进、启动首批 task，§7），与使 run 成为终态的那次写（过闸之后只清扫，§7）；它按流记录的种类分辨两者，不按读到的状态。另有两类定时器调起：job timeout 到点（§6），与 run 的期限那一次、期限加 300 秒那一次（§7）。只认这几种载荷，别的（如 `status --wait` 检测到停滞时发来的只带 run 标识的载荷）记一行日志、正常返回、不推进。
- **reconciler**：主推进器。worker 每写入一批事件，Stream 即触发它执行一次 `tick`——事件既是数据也是「心跳」，推进由事件级联驱动，无常驻轮询。
- **exit-observer**：把 ECS STOPPED 事件翻译成 events 表里的 `task_exited` 记录（即 cloud 后端中观察到 worker 终止的一方）。它的触发面是 IaC 部署时建好的 EventBridge rule（按本 cluster 过滤 ECS task 状态变更 → STOPPED）——**常驻订阅、不由任何一方启动**；三个 Lambda **之间**没有互相启动/调用关系，各自订阅自己的事件源，链条由事件串接；仅有的主动 invoke 都来自 Lambda 之外（job 超时定时器与 run 的两次定时触发调起 kicker，见上条与 §6、§7）。
- **带 `--expose-local` 时的隧道守护进程**：推进全在云端，持有隧道的是本机的一个进程：submit 另以新会话启动本机的隧道守护进程（隐藏子命令 `_tunnel_watch`，主体 `tunnel_host.hold_tunnel_for_cloud_run`）。它起隧道、经回报管道交回公网地址与预热地址；submit 建 run 之前查一次它还在不在，建 run 之后经它的标准输入交出 run 的标识；它每 5 秒读一次 run 的状态，到终态或到运行期限加 300 秒（按墙钟）关闭会话、退出。它不推进 run，也不在上面三个 Lambda 的链上（[ADR 0035](../adr/0035-local-app-testing-via-tunnel.md) 决策 3「云端 `submit`」）。
- 多宿主并发安全：`tick` 幂等，job 认领走 CAS 条件写（PENDING→RUNNING 只有一个写入方成功；run 已收尾后不再接受新的认领），投影落库走 HWM（投影只前进不后退的水位）与终态条件写；Stream 分片并发触发多个 Lambda 实例，叠加定时器调起的 kicker，均安全。一批流记录里每个 run 各自处理：一个 run 的处理失败（读写记录、结束写、清扫）不打断同批别的 run，全部处理完之后有失败才让这次调用失败、由流把这次投递的记录重新投递一遍（重试时已做过的再做一遍，各步幂等）；报告生成与防御性超时扫描的失败隔离在调用之内，运行态读不出不算失败、只记日志。
- **并发上限：声明随 definition 传递，部署侧只留一道 cap**（与超时预算同构，二者都属 run 的定义）。`run` 与 `submit` 都把 `--max-concurrency` 落进 definition（`RunMeta.max_concurrency`），后台的推进器一律按 definition：local per-run 进程用的是它自己生成的那份（值由 submit 经标准输入交来）。同步 `run` 在同一进程内直接用 flag（不存在传递通道问题），meta 仍照常写入，只为使 definition 如实记录该值。cloud 后端取 `min(definition 声明, 部署侧 cap)`，cap 取自 reconciler/kicker 的 Lambda env `MAX_CONCURRENCY`（由 IaC 设定，值见 `stack.BackendStack.DEPLOY_SIDE_MAX_CONCURRENCY`），限制的是 worker（Fargate task）的并行数，语义为 per-run（单 run 内最多几个 job 并行），是**上限、不是真源**：cap 以内由提交侧决定；**local 无 cap**。声明超 cap 时不会静默按 cap 执行：`submit --backend cloud` 的 preflight 读取推进器 env 比对，超出即提示「本 run 将按 cap 并行，需要更高并发须改 IaC」，但**不阻断提交**（相比之下 `REPORT_DIR` 不一致会以退出码 2 结束）。旧 definition（无此值）按 1 处理，与该机制接通前的行为一致。为何 cap 归部署方、local 为何无 cap、为何超 cap 只提示不阻断，why 见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制四。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一-四、端到端流程、重议闸门）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（三 Lambda 的 IaC/权限/触发面）。

### 4c. 读侧：进度观察与结果落点

后台驱动的另一半是观察。事件流是**写模型**，读模型是它的投影 **RunState**（cloud 后端下是 runs 表的 STATE item，local 后端下是 `run_state.json`）：后台运行下它只由 `tick` 写（投影、job 的终态与到期的结束写），外部读者（`status`、`explain`、未来的 WebUI）读运行状态时**都不自行重放事件**；唯一的例外是 `explain` 为被中止或出错的 job 归约该 scope 的事件流，补取判定明细里没有的 step 记录，这只是只读视图、不改判定（各自读什么、何时才有内容，见本节末条）。读侧决定的是「读到的数据有多新、读到什么才算定论」：

- **`status`（不带 `--wait`）纯只读、零副作用**：数据新鲜度取决于最近一次 `tick` 的时刻；它不推进，也不 kickoff。
- **run 级 status 的取值语义**：执行期间 run 级只取 `pending`/`running`，且只进不退——认领在同一次写里把 job 与 run 级都置为 `running`；投影不越过 `running`、不写 job 终态，只在把某个 job 写成 `running` 时连带写 `running`，没有这样的 job 时（全部仍 pending，或投影里离开 pending 的 job 在库中都已是终态）不写 run 级、保留库中值；前台 `run` 的 job 第一次离开 pending 时也连带推进 run 级。run 级**终态**由使 run 成为终态的那次写落定：最后一个 job 的终态写（`commit_job_states`），或仍有未结束的 job 时的结束写（`end_run`）；前台 `run` 与后台推进用同一组写入口，**读到终态即 run 已结束、每个 job 都已是终态**；终态之后任何写入口都不再改它（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。由此，对未收尾的 run，读到 run 级 `pending` 即没有 job 离开 pending（规则与前提见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条）。云端后端下 `status` 的「推进可能未启动」提示要求 run 级为 `pending`、**所有 job 仍 pending**（后半条由前半条推出，保留只为防御旧版写者留下的记录），且这个 run 带后台标记（`detached`）时才输出。本机后端不给这句提示：本机的 run 只由建它的进程推进，没有可唤醒的一方，它不在了时出口是处置（§4d）。
- **退出码分层**（CI 接线时最易建立错误心智）：`submit` 的退出码只表示提交是否成功，**不是判定**；判定退出码由 `status --wait` 等到终态后给出。根因是 CLI 脱离后不再持有内存中的判定终值。各命令退出码的完整分工见 [`verdict-model.md`](./verdict-model.md) §5（本篇不重复它的表）。

收尾一侧决定的是「什么时候能读到什么」：写序、由写序推出的读者保证、已终态 run 在两个后端的重入，以及落地之后由谁读取。

- **后台的写序**：一次 `tick` 里依次是：① 投影写（只前进、不越过 `running`、不写 job 终态；只交这一轮读到的运行态里还没有结束的 job，云端逐个 job 写、内容与库中相同的不写）→ ② 这一轮已有结果、带认领时刻的各 job 各生成一个标识、先存一份判定明细（`jobs/<标识>.json`，出自这一轮读到的同一份事件快照），任一份存不成即抛出，这一轮不写终态、也不认领与做结束写（本机推进器的判定存储在保存失败时先按 1、2、4 秒退避重试，同一个标识，仍失败才抛出；云端由流的重试或之后的触发再做）→ ③ 以一次终态写（`commit_job_states`）记下它们的终态，各点名自己那一份明细（`result_id`），记下最后一个 job 终态的那次写使 run 成为终态 → ④ 推进决策：在这一轮读到的运行态加上 ③ 的作用上认领并启动 pending 的 job；已过停止启动的时刻、没有执行中的 job 而仍有未启动的 job 时改做到期的结束写（`end_run`，没有启动的 job 记 skipped）→ ⑤ 使 run 成为终态的那次写（③ 或 ④ 的结束写）是**提交点**，之后由宿主写入派生的 RunReport（只在 `tick` 返回这一方的写使 run 成为终态之后才写，宿主经 `reconcile.write_report_from_record` 读一次运行态、按其中点名的标识读回各 job 的判定明细、组装后生成，读与写的失败都被隔离，不会回退已结束的 run；`tick` 开头读到 run 已是终态，或这一方的写因 run 已被别处结束而写不成时，宿主不写报告）。② 可以重做，每次保存都是带新标识的另一份、不覆盖已有的明细；重叠推进时后到的一方遇到库中已是终态的 job 不改写它，它存下的那一份没被点名、不被读（各记录的先后见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三的开头）。每个 job 的终态只写成一次，使 run 成为终态的写只有一方写成，⑤ 的报告只由这一方写一次；local per-run 进程与 cloud reconciler 共用 `core` 的同一个推进步骤。云端推进器读不到可用的运行定义时不经推进步骤：以结束写的 error 变体把 run 与未结束的 job 都记 `error`，说明是读不到的原因，不存明细、不生成报告（这个变体只读写运行态里各版本共用的那几项，job 条目里的其余内容原样复制）；local per-run 进程用自己生成的运行定义、不从记录读回，没有这一情形。前台 `run` 的写序见 §3：每个 job 结束时先存明细、再写它的终态，余下没有启动的 job 由结束写结束，报告同样由使 run 成为终态的一方从记录生成。
- **由写序推出的读者保证**：**读到一个由执行结果结束的 job 的终态，即它点名的那一份判定明细已保存**（保存成功之后才写终态，[ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条④「收尾各步的先后与之后会不会变」的 K3；两个推进方重叠推进时的边界见同一条；由结束写结束的 job（没有启动的）没有判定明细，状态与说明只在运行态里，见 [ADR 0030](../adr/0030-realtime-persistence-seam.md) 决定三「commit point 的意义」）；RunReport 则是提交点之后的派生物，「已读到终态、报告文件尚缺」是合法状态（一直缺的情形见同一条的「已获接受的边界」），读者不应把它当判定真源。落点：local 后端下是 `--report-dir/<run_id>/`，cloud 后端下是 S3 桶里的 `<report_dir>/<run_id>/`；cloud `submit` 的 `--report-dir` 须与推进器侧一致（提交前探活会比对，不一致则以退出码 2 结束），否则 run 执行完成后在提交者给出的前缀下找不到结果。
- **已终态 run 在两个后端的重入**：cloud 后端的云端推进器每次调用先过闸、读运行态，读到已提交终态即只清扫这个 run 仍在执行的 task、不推演（§7；RunReport 缺失时的处理见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 端到端流程 cloud 一节标着「明确接受的代价」的一句）；local 后端只有建它的那个进程推进，没有重入的推进方，处置方读到已终态即给出 `already_finished`、不打开 run 目录（§4d）；两个后端的 `tick` 自身也先读运行态，读到已收尾即停止推演，这一步覆盖宿主判断之后、`tick` 读取运行态之前插入的收尾（读取之后才发生的收尾，本轮仍继续处理；本机是处置方插进来的结束写），本机推进循环随之退出、不写报告。
- **落地之后由谁读取**：`status` 读投影 RunState（`--json` 时另附 `artifacts` 键，给出报告 / 判定明细 / 元信息的约定落点；各键何时有内容见 [`cli-json-contract.md`](./cli-json-contract.md) 的字段表）；`explain` 读**运行态点名的那一份判定明细**（step 级失败原因与 `kind=evidence` 的证据指针；先读运行态、按各 job 的标识取，不列举存放处），回答「这一步为何如此判定」；对 aborted 或 error 且仍有无记录 step 的 job，另从事件流补取已执行完的 step 的记录与证据（[ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策七）。两者都受落地时机约束：两种运行方式都逐 job 落库，每个 job 得出结果的那一轮在写它的终态之前保存它的判定明细，run 还没结束时即可读到已完成的 job（后台推进的步骤、必要契约与已获接受的边界见 [ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条④「收尾各步的先后与之后会不会变」）；`explain` 在各种落地情形下给哪句提示见 [ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策四。用法与退出码见 [`docs/user-guide/running-and-results.md`](../user-guide/running-and-results.md)，`--json` 字段见 [`cli-json-contract.md`](./cli-json-contract.md)。

最后一条不对称（**推进器不在了之后谁来收尾**）：cloud 的推进器是后端自己，`--wait` 随时可以离开，云端链会自行执行至结束（`--wait` 检测到停滞时发给 kicker 的调用不再推进，§4b）；推进链断开、run 停住时，后端在期限加 300 秒那一次定时触发里把它记为已结束（后端到期结束，§7）；local 的 `--wait` 从不推进，随时可以离开，per-run 进程（或前台 `run` 的进程）已不在时，它与 `settle-runs` 都只能把这个 run 记为已结束（§4d），执行中的 job 记 `aborted`、没有启动的记 `skipped`，不接着执行。根因是主推进器的位置不同（云端 Lambda 与本机进程）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制三：投影钳制与条件写、「run 级状态只进不退」条；「命令形态」节：status/退出码）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（终态提交点）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)（决定五：退出码语义）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策三：查询类命令的 `--json` 与 `artifacts`）、[ADR 0042](../adr/0042-step-evidence-and-explain.md)（决策四：`explain` 以判定明细为骨架；决策七：被中止 job 的 step 记录从事件流补取）。

### 4d. 本机的 run 处置：`settle-runs` 与等待中的 `status --wait`

本机的推进器（前台 `run` 的进程、per-run 推进进程）没写终态就退出时，run 停在 `pending` 或 `running`，没有常驻的一方去结束它。出口是 run 处置：别的一方以结束写把它结束。入口有两个，`settle-runs` 与等待中的 `status --wait`；判定与动作只在 runtime 的 `gherkai_runtime.settle` 一处，两个入口都调它，前台与后台的 run 不分开处理（不读 `detached` 标记）。

一次处置的次序（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策八「处置的次序」）：

```
读一次提交记录:结构版本不是本版本认的 → other_version;读得出 → 记下 deadline_at;读不出(不存在、不是 JSON 对象、定义违约) → 期限读不出
读运行态(不碰锁):解析不了 → unreadable;已是终态 → already_finished(不打开 run 目录、不做边界检查、不试拿)
只读打开 run 目录 → 对这次打开的描述符做边界检查(不过 → unsupported_filesystem) → 不阻塞地试拿生命期锁
判定(取一次墙钟,结束时刻用同一个读数):拿到 → advancer_exited;已严格晚于 deadline_at + 300 秒 → past_deadline;
        被持有 → lock_held;锁不可用 → undetermined
advancer_exited / past_deadline 才往下:结束写(end_run,短锁 .runstate.lock 内的条件写:run 未结束才写成)
  → 写成的一方按 run 目录的名字生成报告(失败隔离,「报告是否生成」作为结构化结果交给入口)
关闭描述符:锁随之放开,所以锁持有到报告生成之后
```

- **结束写记什么**：取说明表处置的两行（`run_status.RUN_ENDINGS` 的 `settle-advancer-exited` 与 `settle-past-deadline`，各句末尾带「（已记为已结束）」），运行态里 `running` 的 job 记 `aborted`、`pending` 的记 `skipped`；这两行结束执行中的 job，不带「写下时没有 `running` 的 job」的条件（[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。不推演事件、不读事件库、不停任何执行：留下的 worker 靠核验所属进程自行退出，被暂停的推进器恢复之后在下一次写时发现 run 已结束而停手（认领被拒、执行中的写返回 `False`、终态写得到 `ALREADY_ENDED`）。
- **先查后做之间的变化由结束写裁定**：只有结束写改记录，它自带 run 未结束的条件，所以前面各步读到的都只是判定依据。推进器在这之间写下终态、或两个处置方同时处置时，只有一方写成，另一方得到 `already_finished`；一方拿到锁、另一方因锁被它持有而按期限判断时，记下的是先写成的那一方的判定。读运行态之后任一步遇到「不存在」（打开 run 目录、读提交记录、结束写时这个名字下已没有目录或文件），都按这个名字下已没有 run 处理。
- **期限的比较**只有一处算法：`run_deadline.past_overdue`（严格晚于 `overdue_at`，即期限加 `OVERDUE_MARGIN_S`），隧道的边缘到点拒绝取同一个时刻。
- **两个入口怎样用结果**：`settle-runs` 逐个列出，跳过不改变退出码；不给 run 标识时先由 `settle.unfinished_run_ids` 列出全部未结束与运行态读不出的 run，再逐个处置，列举之后消失的略过。这两段循环（逐个处置、逐个清理暂存目录）在命令行一侧的 `settle-runs` 里，不在 `gherkai_runtime.settle`：每一项之前看一次中断的标志，已处理的部分与列举出的 run 是命令自己记下的；只有不给 run 标识、列举完成而列出的 run 为零时，人读输出才说没有未结束的 run。等待中的 `status --wait` 每轮做一次处置，只在等得到头的两种情形下接着等：锁被持有，或期限读得出（至多等到期限加 300 秒）。`settled` 即在标准错误说明一句、照不带 `--wait` 的 `status` 渲染；`already_finished` 直接渲染；`unsupported_filesystem`、`unreadable`（说明与不带 `--wait` 的 `status` 同一句）与「锁不可用而期限读不出」的 `undetermined` 以退出码 2 结束、不等待；其余（`lock_held`，期限读得出的 `undetermined`）继续等待，等待中的说明按结构化的原因与错误码去重、每种只说一次。开始等待之前另过一次版本闸，只拦结构版本不认的提交记录。
- **中断**：两个入口在开始处理之前装上只记标志的中断处理器（与前台 `run` 起好隧道之后装的同一个；进入命令时已被设为忽略的信号不装、保持忽略），到命令结束时先把标准输出写完并刷新、再恢复（先恢复 SIGTERM、后恢复 SIGINT）；Ctrl-C 与 SIGTERM 只记下、不打断正在做的处置、清理或输出。`settle-runs` 在列举之后与每一项之前看标志（给了 run 标识时在那一次处置之前看），看到即不再做下一项，输出只做一次、先输出已处理的部分再说明；等待中的 `status --wait` 在每次处置之后看，等待的间隔分成不超过 0.2 秒的小段、每段之前看一次，说明按这次处置的结果给出（本命令写成了就说已记为已结束），不按阶段猜测；退出码按信号取。只有让命令少做了事的中断才改变结果：`settle-runs` 记下循环是否因标志停过、还有没处理的项，最后一项期间或输出期间才收到的中断不给停止的说明、不改变退出码；`status --wait` 显示期间才收到的同样不改变显示与退出码。写不出输出（读的一方一直不读）或结束写在等运行态的短锁时，中断只被记下、不起作用，只有 SIGKILL 能结束命令（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」里「其它局限」）。
- **清理暂存目录**（只在 `settle-runs` 不给 run 标识时，处理完 run 之后）：`run_dir.staging_names` 列出名字是暂存目录形态的条目（前缀之后恰好 16 位小写十六进制，`run_dir.is_staging_name`，与建 run 一方的 `run_dir.staging_name` 同一处定义），逐个交给 `run_dir.sweep_staging_dir`：`lstat` 必须是真实目录（文件、符号链接不碰）→ 只读打开（已不在即不列出，别的失败记 `unopenable`）→ 边界检查 → 试拿（被持有记 `held`，锁不可用记 `lock_unavailable`）→ 拿到锁之后核对名字仍指向打开的那个目录（核对不过即已改名成 run 或被换掉，不删、不列出）→ `--dry-run` 到此放开锁，否则持着锁删去（中途出错记 `remove_failed`，下一次接着删）。各种跳过都不改变退出码。

输出、退出码与各句说明见用户指南[运行测试与查看结果](../user-guide/running-and-results.md)「结束停住的 run」，`--json` 字段见 [`cli-json-contract.md`](./cli-json-contract.md)「`gherkai settle-runs`」一节。这个版本的 `settle-runs` 只接本机后端；云端的 `status --wait` 检测到停滞时仍调用 kicker，kicker 不认这一载荷、不推进（§4b）。

> 权威：[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md)（决策三：生命期锁、暂存目录与清理协议；决策四：边界检查；决策六：可以处置的条件；决策七：处置做什么；决策八：处置方、入口、次序、中断与出口）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)（决定三「结束写」小节与说明表、决定五：退出码）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)「推进器与触发源」与被拒方案「本机接力，及其改法」（为什么本机没有别的一方接着推进）；code：`gherkai_runtime.settle`、`core/gherkai_core/adapters/run_store/run_dir.py`（探查与清理）、`LocalRunStore.probe_run_dir` / `staging_names` / `sweep_staging_dir`。

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

两类 item 按 `item_type` 属性区分（事件本体不带此属性），高位常数与属性名的真源在 `fargate_engine` 的 schema 常量。读端是无状态的 `DdbEventLog.records()`：读整个 PK、按 `item_type` 分流后交给重放；云端的 job 到点停止只需判断某个 scope 是否已退出，直接用 `DdbEventLog.has_exit` 做单点查询（它不在 `EventLog` 协议上，协议只有 `records` 与 `record_exit`）。

**退出观察者三对位**（谁观察到 worker 终止）：前台由 Engine adapter 自行观察（subprocess 的 `proc.wait`）；local `submit` 下是 per-run 进程的 `handle.wait()`；cloud `submit` 下是 exit-observer Lambda。另有一个例外情形：worker 根本未启动（`launch` 抛异常）时不存在平台侧观察者，由 `tick` 自行补一条退出码未知、带「起 worker 失败」原因的退出记录，并记下失败的那一刻作退出时刻（它晚于这个 job 的截止时刻时投影按超时处理，与前台起 worker 失败的处理相同，见 §6），下一轮按「有退出记录、退出码未知 → error」收敛；若不补写，该 job 已被认领为 RUNNING 却永不会有事件与退出记录，整个 run 停滞。

**诊断的落点**（事件流之外的另一条通道）：worker 的 stdout（引擎 SDK 噪声）与 stderr（worker 自身的诊断）默认带 `[worker <scope>:out|err]` 前缀透传到**推进器进程的 stderr**，落点随推进器而变：前台 `run` 直接输出到终端，加 `--quiet` 时改落 `<report-dir>/<run_id>/worker.log`（`--no-report` 时落系统临时目录），结束时只输出一行路径；cloud 后端 worker 在云端执行，日志在该 task 的 CloudWatch 日志组；local `submit` 的 per-run 推进进程回报 submit 之后的 stdout/stderr 落 `<report-dir>/<run_id>/reconcile.log`（回报之前接在 submit 的标准错误上），worker 的透传行同落其中。判定归因只写入判定明细的 `message`。

> 权威：[ADR 0024](../adr/0024-worker-core-protocol.md)（事件协议/DDB 态、三通道）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（机制一：退出记录独立键空间；机制二：两件都要的收敛判据、launch 失败补偿）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md)（决策二：`--quiet` 的落点）。

## 6. `job` 超时预算（timeout）：三路形态相同的 enforce

每个 `job` 有超时预算，按**墙钟**（真实流逝时间）计。声明方式为 `@timeout:N` tag 或 `--default-job-timeout`，两者都没给时由 plan 按测试目标补缺省（任何目标都有上限 7200 秒、不能关闭超时，设备 scope 另有下限），定值随 definition 落在 `Job.timeout_s`（ADR/CONTEXT 里称「job 墙钟预算」）；取值、覆盖与校验顺序见 [ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节与 [ADR 0051](../adr/0051-device-session-lifecycle-and-app-distribution.md) 决策 2。三条执行路径**各自落实同一形态的 enforce**（enforce 即 ADR 与 code 对这一形态的用词）：到点 → 停止 worker → 记下收场态。三条路径的截止时刻取法相同：认领时刻加预算，与运行期限取较早的一个，都按墙钟比较，两者相等时算预算；起作用的是 job 自己的预算时归因 `error + timeout`，是运行期限时记 `aborted`、没有归因（说明是「这个 run 已超过允许运行的时间，job 被中止」）。后台路径不把起作用的是哪一个记进退出记录，投影时由认领时刻、预算与期限重算（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二）。

| 路径         | 到点机制                                                                                                                                                                                                          | 停止方式                                                                                                                                                                                             |
|--------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 前台 `run`   | schedule 循环内按墙钟比较截止时刻：认领时刻加预算，与运行期限取较早的一个（[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二）                                                                   | `handle.stop(grace)`（SIGTERM→宽限→SIGKILL） |
| local submit | 截止时刻由 `tick` 在认领时算出（认领时刻加预算，与运行期限取较早的一个）、随启动交给 launcher；per-run 进程为每个执行中的 job 起一个检查线程，每 0.25 秒读一次墙钟（与 `tick` 取认领时刻同一个读取点），过了截止时刻即停，检查持续到 worker 进程退出；worker 在截止时刻之后、下一次检查之前自行退出的，退出记录不带超时标志，投影按它的退出时刻判为超时（见本节表后一段）。该进程若中断，检查随之丢失，也没有别的一方接着计时：执行中的 job 留在 `running`，run 停住，被处置时记 `aborted`（§4d） | `handle.stop(grace)`（协作式停止，同前台 local，grace 取引擎最小宽限） |
| cloud submit | 启动 task 之前为该 job **设置一个一次性到点定时器**，到点时刻就是 `tick` 交来的截止时刻（EventBridge Scheduler one-time；与 §4b exit-observer 的 EventBridge **rule** 同名不同物：那是事件总线订阅，这是独立定时服务）                                  | 到点由 kicker 处置，整条链见下图；另有任意 `tick` 的防御扫描作为双保险，run 的期限那一次定时触发再对全部执行中的 job 做一遍（§7）                                                                     |

后台两路的退出记录只记事实，是否按超时处理在投影里判断，以写下这个 job 终态的那一轮的判断为准，规则对两路相同。退出记录带两项：超时标志（`timed_out`，发过超时的停止请求，或云端的 job 到点停止补写未知退出时已判为超时）与退出时刻（`exited_at`：本机是推进进程看到 worker 退出的那一刻，云端是 task 的执行停止时刻，起 worker 失败时是失败的那一刻；补写的未知退出没有这一项）。投影时带超时标志、或退出时刻晚于由 `claimed_at`、预算与期限算出的截止时刻的，都按超时处理，内容已完整（干净退出且发了 `scope_done`）的照旧不改判。这样 worker 在截止时刻之后、停止请求发出之前自己异常退出时，前台、本机后台与云端后台的判定相同；云端的退出观察者只看得到 task 对象、读不到截止时刻，所以判断放在投影里、不放在写入方。云端的 job 到点停止补写的未知退出只在这个 job 还没有退出记录时写入（判断与写入是同一次条件写），恰在它查过之后才落下的真实退出记录不会被盖掉；补写之后才到的真实退出照常覆盖补写的那一条。它查到已停止的 task 时写的不是未知退出，而是从 task 对象取得的真实退出（退出时刻取 task 的执行停止时刻，与退出观察者同一算法），与退出观察者的写入一样照常覆盖同一条记录。

cloud 路径的超时处置是一条多跳链，时序如下图。这里的「定时器」（ADR/code 里称 arm 一个 one-time schedule，中文记作「武装」）是 per-(run,scope) 的短生命周期资源：建在部署专用的 schedule group `{prefix}schedules` 里，名字不带 prefix，为 `job-timeout-<sha1(run_id#scope_id) 摘要>`（group 名与名字都取 `gherkai_runtime.names` 这一命名真源，IaC 按这个 group 授 IAM 资源域，同源推导），到点触发后即自动删除，因此控制台中通常看不到它；拆除部署时 group 连同其中还没有到点的定时器一并删除。

![云端超时 enforce 链：启动 task 时设置的一次性定时器到点调起 kicker，停止 worker 后由 exit-observer 写成带超时标志的退出记录，回到既有链收敛](../diagrams/execution-timeout-chain.svg)

图注：本图只画云端这一路「如何停止 worker」，另两路的到点机制与停止方式见上表；定时器的到点时刻为这个 job 的截止时刻：`claimed_at`（领取该 job 的时刻）加上该 job 的墙钟预算，与运行期限取较早的一个（由 `tick` 在领取时算好），与防御扫描同一算法，设置定时器晚于领取的那段间隔不推后到点。定时服务只承诺分钟精度，可能早于这一刻触发，因此到点的一方**先确认这个 job 仍为 RUNNING 且没有退出记录，再由 `claimed_at`、预算与期限重算截止时刻、复查是否已到**（读到的时刻严格晚于截止时刻才算已到）：已到则执行停止；未到且相差不超过一分钟则等到截止时刻（每次至少等 1 秒），重新确认 job 状态并重读时钟后才执行停止（等待期间时钟被回拨、或读到的恰好是截止时刻而仍未到时，在这次调用的等待额度（至多一分钟，各次等待合计）内接着等，额度用完仍未到则本次不停止）；相差超过一分钟则本次不停止，交给防御扫描与 run 的两次定时触发（取舍见 [ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节「到点不早于 deadline」条）。这段等待（`lambdas/reconciler.py` 的 `_wait_past`）由 job 到点停止与 run 的两次定时触发共用，各自传入要等到的时刻（§7）。重复到点、定时器与防御扫描同时命中均无害。防御扫描在截止时刻之外另加固定余量。`StopTask` 的 reason 里带一个哨兵串，exit-observer 据此把这条退出记录标记为超时停止；哨兵串之后按起作用的是预算还是期限分别写，只供在 ECS 控制台查看。停止之后**记为什么状态**（超时归因落在哪一类、与 fail-fast 共用哪个字段、按什么优先级判定）见 [`verdict-model.md`](./verdict-model.md) §3c（归因优先级图）。

> 权威：[ADR 0034](../adr/0034-detached-batch-reconciler.md)「job timeout」节（取舍/归因链/防御扫）、[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「截止时刻与说明」（退出时刻与投影判断）、[ADR 0019](../adr/0019-feature-tags-scope-and-engine.md)（`@timeout:` tag）、[ADR 0051](../adr/0051-device-session-lifecycle-and-app-distribution.md)（决策 2：设备 scope 的缺省墙钟与下限）。

## 7. 云端后端各入口共用的闸、run 的两次定时触发与 run 结束之后的清扫

云端后端的两个推进 Lambda 有几个入口：reconciler 处理 events 表流的记录，kicker 处理 runs 表流上的两种记录（STATE 条目的新建、使 run 成为终态的那次写）、job 到点停止的触发与 run 的两次定时触发（期限那一次、期限加 300 秒那一次）。每个入口先对涉及的每个 run 过同一道闸，再做各自的事；同一种情形在各入口得到同一种处理，判断只在 `lambdas/reconciler.py` 的 `_gate` 一处。闸不看后台执行标记：`submit` 照样把它写在 STATE 上，它只作描述（`list-runs --json` 的 `detached`），触发过滤与各入口都不读它。

![云端后端各入口先过同一道闸：先读运行态，再读提交记录的头，都可用才推进；读不出只记日志，不存在、已结束、记录不可用与推进之后已结束都清扫](../diagrams/execution-backend-gate.svg)

图注：图上画的是一个 run 在闸里的走向，入口有哪几个见上一段；§4b 那张时序图画「链如何贯通」。图上没画的几处：按后端的格式读运行态其余部分读不出时，与第一步读不出同样只记日志；以结束写的 error 变体结束之前，别的写方已先使 run 成为终态时，同样清扫，记录保持先结束它的那一方的结果；job 到点停止的入口过闸之后，先做到点停止再推进一步（§6）；STATE 条目新建的入口过闸之后先建两次 run 级定时触发、再推进；两次 run 级定时触发过闸之后各做各的，期限加 300 秒那一次不推进、交给处置，它遇到运行态读不出时另有一条按时间清扫的路（见下「run 的两次定时触发」）。

- **第一步，运行态**：强一致读 STATE，先只看各版本共用的那几项（run 与 job 的状态、写入序号等；`DynamoDBRunStore.read_state_common`）。不存在即清扫（run 标识不复用，没有要保护的记录），不读提交记录；已结束即清扫，同样不读提交记录：迟到与重放的事件、到点时已结束的 job 都在这里只清扫、不推演；读不出即记一行日志，不写、不推进、也不清扫：分不清 run 是否已结束，清扫可能停掉仍在执行的任务。
- **第二步，提交记录的头**（run 未结束时）：强一致读头、不取 jobs 对象（`read_head`）。头不在、记录格式版本不是整数或不是后端的，以结束写的 error 变体结束这个 run（未结束的 job 与 run 都记 `error`，只写各版本共用的那几项，不生成报告），之后清扫；是后端的格式时按它读运行态的其余部分，再取 jobs 对象、读整份运行定义（`meta_from_head`，头只读这一次），定义违约、jobs 对象已不在（取它得到「键不存在」）或缺任务定义修订同样以 error 变体结束、清扫。取 jobs 对象得到别的错误（如拒绝访问）不算记录不可用，原样抛出，由之后的触发再读。
- **第三步，装配并推进一步**：只有过了前两步的 run 才装配起 task 用的部分并调 `reconcile.tick`。这一方的写使 run 成为终态时先生成报告、再清扫；run 已被别处结束时只清扫；仍未结束时做防御性超时扫描，等下一次触发。kicker 收到使 run 成为终态的那次写时，过闸读到已结束即清扫，不推进。
- **清扫**（`_sweep`）：按启动时带的 run 标识列出这个 run 期望状态为运行中的任务（翻页取全），逐个停掉，其中某个任务的停止请求失败时其余照常停掉，再把这个 run 记为这一次的失败、由重试再停；停止说明里不带超时的标记，退出观察者不会把这次退出记成超时。清扫不改动 runs 表，可以重复执行。每次停掉的是这一次列得出的任务：启动调用还没返回、刚启动还列不出来的任务这一次漏掉，由之后带到这个 run 的调用停下。run 由结束写结束时还在上传最后产物的任务也会被停下，产物可能不完整。
- **run 的两次定时触发**：每个云端 run 有两次一次性定时触发，与 job 到点停止的触发同一机制、同一个执行角色、同一个 schedule group，名字是 `run-timer-` 加 `sha1(run_id#种类)` 的摘要，触发之后自动删除；载荷是 `{run_id, run_timer}`，`run_timer` 为 `deadline` 或 `overdue`。三种定时触发到点之后都先重读墙钟确认已过它的时刻，不以收到触发为证据；没过就在这次调用里等（共用 `_wait_past`：至多一分钟、每次至少 1 秒，可等的上界是 Lambda 剩余时间减去之后要做的事的预留），额度用完仍未过的这一次不动手。
  - **建立**（`_arm_run_timers`）：kicker 收到 STATE 条目的新建、过闸之后各自建两次，然后做首轮推进。期限那一次的时刻是 `deadline_at` 截去小数秒，期限加 300 秒那一次是那个时刻之后的第一个整分钟（两个时刻由 core 的 `run_deadline.deadline_of` 与 `overdue_at` 算出）；建立之前读一次墙钟，不晚于它的那一次不建（期限已过时首轮推进即做到期的结束写，那一次没有可做的事）。同名已存在视为已建；建不成（含推进 Lambda 缺目标函数与执行角色的配置）不挡首轮推进，推进之后把这条记录记为失败、由流重试。闸给出不存在、读不出、已结束或以 error 变体结束了它时不建。
  - **期限那一次**（`_on_deadline`）：过闸、等到严格晚于期限，读一次运行态：不存在或已结束即清扫；未结束时对整个 run 列一次 task（运行中与已停止的都翻页取全），对执行中、没有退出记录的 job 逐个做 job 到点停止的三路停止（§6），然后强制推进一次，这次推进不做防御性超时扫描。某个 job 停不下时其余照常、推进照常，推进之后让这次调用失败、由 AWS 的重试再调用。
  - **期限加 300 秒那一次**（`_on_overdue`，后端到期结束）：过闸（不存在、已结束、别的格式写出或运行定义不可用时闸已处理并清扫），之后调 runtime 的 `settle.settle_run`，处置目标是 `settle.cloud_target` 的云端形态（没有锁），判定与等待中的 `status --wait`、`settle-runs` 是同一处；说明取结束写说明表里「已过期限加 300 秒」那一行，执行中的 job 记 `aborted`、没有启动的记 `skipped`，写成之后生成报告。结果是还在期限加 300 秒之内时等到那时再处置一次。不推进。得到结果之后清扫：写成或读到已结束当场清扫，其余（如处置时运行态读不出）确认已过期限加 300 秒之后清扫。运行态读不出时不处置，只读提交记录头里的记录格式版本与期限（`SubmissionHead.deadline`），记录格式版本是后端的、确认已过之后清扫，头不在或读不出期限只记日志。报告没有生成时，日志带上原因的类别。
  - **先后与重复**：两次是彼此独立的调用，可能晚到、重复到达、先后颠倒。期限加 300 秒那一次先结束了 run，期限那一次随后到达只清扫；同一次触发到达两次时，处置由写入序号裁定、只有一方写成，三路停止由条件写裁定，推进幂等。
- **一批记录里各 run 各自处理**（`_each_run`）：一个 run 的处理失败（读写记录、结束写、建 run 级定时触发、清扫、job 到点停止与期限那一次的停止、后端到期结束时处置的读写）不打断同批别的 run，全部处理完之后有失败才让这次调用失败、由流重新投递（定时触发的调用只带一个 run，由 AWS 的重试再调用）；报告生成、防御性超时扫描与为 job 建到点触发的失败隔离在调用之内，运行态读不出不算失败。
- **不走这道闸的**：exit-observer 不读 runs 表（执行角色只有 events 表的 `PutItem`，env 只有 events 表名与区域），凡带 run 与 scope 标识的任务停止都写退出记录，它只追加事实、不推进（[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md) 资源清单 10.）。用户一侧的处置方没有 ECS 的权限、不清扫，它们的结束写经 runs 表流带起 kicker 的清扫。

本机侧没有这道闸：`submit --backend local` 照样把后台执行标记写在 run_state.json 顶层（之后每次写回保留），本机的任何判断都不读它。本机的 run 只由建它的那个进程推进，worker 是它的子进程；`status --wait` 与 `settle-runs` 对前台与后台的 run 做同一种处置（§4d）。

> 权威：[ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md) 决策九（第 1 条「定时触发」，第 2 条「结束之后清扫」，「落实时，后端各入口先过同一道闸」一段）与决策八「能处置的只有」一条（判定只在 `settle.settle_run` 一处）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（端到端 cloud 1b「触发过滤不看后台执行标记」、4. 的闸与机制三「不经推进步骤的收尾」、「job timeout」节「到点不早于 deadline」条②：共用的等待）、[ADR 0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)（资源清单 13.：两表的流与两个事件源映射的过滤；资源清单 15.：一次性定时触发的 group、名字、表达式与载荷；资源清单 12.：推进 Lambda 的时长约束）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节说明表（后端到期结束的说明）。

## 8. 延伸阅读

| 想深入的主题                                                      | 去哪读                                                                 |
|-------------------------------------------------------------------|------------------------------------------------------------------------|
| 无状态批量运行全部决策/护栏/被拒方案                              | [ADR 0034](../adr/0034-detached-batch-reconciler.md)                   |
| 运行期限、生命期锁与 run 处置（含暂存目录的清理）                 | [ADR 0054](../adr/0054-run-deadline-lifetime-lock-and-settling.md)     |
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
