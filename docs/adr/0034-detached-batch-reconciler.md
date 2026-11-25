# 无状态批量运行：CLI 提交 → 事件驱动推进 → 轮询收集（CQRS + reconciler）

> **Status:** Partially-superseded-by 0051 —— [0051](./0051-device-session-lifecycle-and-app-distribution.md) 改写三处：机制二 `exit==0` 一行（先看 `scope_done.status` 与 scenario 判定集，终结判定收进两条归约路径共用的终结函数与真值表）、「job timeout」节的 worker 消费条与 `--default-job-timeout` 的 flag 承诺（worker 建会话前读墙钟预算作自检；设备 scope 有目标缺省与下限）、停止后的事件消费（停止后仍有界归约完整事件流）。纠正 [0016](./0016-execution-architecture-core-lib-run-model.md)「无状态化=加 adapter+换注入、核心不动」对本能力的过强断言（见下「对 0016 的纠正」；0016/0024/0026/0031 已标 Partially-superseded-by 本 ADR，0030 标其「重议」条已由本 ADR 落地）。这一篇描述的设计有一部分尚未实装，code 跟上之前，实际行为以 code 为准。

同步 `run` 是**「CLI 阻塞跑一批」**：组合根同进程 `schedule()` 持 `ThreadPoolExecutor`、以 `wait(FIRST_COMPLETED)` 逐个收集完成的 job、全批完成才返回。本 ADR 落地的产品项（曾是产品线唯一未做项、非加固）= **「CLI 提交完就走、异步收集」**（[0016](./0016-execution-architecture-core-lib-run-model.md) v1.2 已完成 + [0017](./0017-cloud-execution-fargate-over-runtime.md) batch shape）——新增 `submit`/`status` 命令、同步 `run` 保留不变。本 ADR 定这套无状态批量运行的架构、数据模型、并发/写序不变量与被拒方案护栏。

## 定位：产品价值，非加固

- **产品价值**：CI/用户 `submit` 一批用例即可离场（关笔记本、断开），run 在云上自跑到完成、结果异步收集；对照当前必须让 CLI 全程阻塞守着。
- **不做**：常驻调度服务 / WebUI（接口留好，真需要时加 adapter）；跨 run 的批队列编排（每 run 独立）。

## 核心思想：CQRS + 无状态 reconciler

把「CLI 进程持有线程池、阻塞跑完整批」换成「**events 表记下执行事实，一个幂等函数被事件唤醒着把整批推完，运行态是状态的权威**」：

- **写模型** = events 表（append-only 的执行事实日志，[0024](./0024-worker-core-protocol.md)）。
- **读模型** = `RunState`：job 与 run 状态的权威（[0030](./0030-realtime-persistence-seam.md) 决定三），**外部消费者只读它**。
- **reconciler 机制**（投影 + 推进）= 从 events 推进 `RunState` + 决定启下一个 job：投影只前进，不写 job 终态，已写下的终态不被迟到的事件改动（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补）；job 的终态按逐 job 的写序写下（[0030](./0030-realtime-persistence-seam.md) 决定三）；结束写不经事件（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。**无状态、幂等**：进程内不留任何调度态；本机只有持锁的推进器推进，云端多次调用可以重叠，由条件写保证安全（见下「推进器与触发源」与机制三）。（消歧：此处 reconciler 指 CQRS 的机制角色；同名 Lambda 只是它在 cloud 的宿主之一——kicker 与之同 code，local 的后台推进进程跑的也是这份机制。这些宿主与前台执行 `run` 的进程统称**推进器**，定义见 CONTEXT。）

**单一读接口不变量**：外部（`status` / `list-runs` / 未来 WebUI）**永远只从 `RunState` 读状态**；`events → RunState` 的推演**只在 reconciler 一处**，不散落到各消费者（否则多份推演逻辑必漂移）。这是本设计的骨架原则。

## 数据模型三件套（职责分明）

| | 是什么 | 谁写 | 谁读 |
|---|---|---|---|
| **events 表** | 执行事实日志 | worker（执行事件）+ **退出观察者**（退出事件） | reconciler；`explain` 补取已执行的 step（[0042](./0042-step-evidence-and-explain.md) 决策七） |
| **`RunState`** | job 与 run 状态的权威（[0030](./0030-realtime-persistence-seam.md) 决定三） | 推进器；结束写的写者另有处置方（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八） | 外部（`status`/`list-runs`/WebUI）**只读** |
| **ResultStore** | 判定明细，由 job 的终态点名（[0030](./0030-realtime-persistence-seam.md) 决定三） | 推进器在写下这个 job 的终态之前保存（写序 [0030](./0030-realtime-persistence-seam.md) 决定三） | `explain` 与报告，读之前先从运行态取被点名的标识（[0030](./0030-realtime-persistence-seam.md) 决定三） |
| **RunReport** | 派生产物（永远最后） | 使 run 成为终态的写入方从记录生成（[0027](./0027-runreport-aggregation-index.md)），失败隔离 | 人 |

运行态另带一个后台执行标记，只作描述、不参与任何判断（见下端到端 cloud 1b「触发过滤不看后台执行标记」）。

## 命令形态

```
gherkai submit <features> [--backend local|cloud]
gherkai status <run_id> [--wait]
gherkai list-runs [--status S]… [--limit N]
gherkai settle-runs [run_id] …    # 形态见 0054 决策八
gherkai run <features>            # 阻塞皮：同进程 schedule() 驱动循环（ThreadPoolExecutor），只有本机后端
```

各命令写什么：

| 命令 | 写 |
|---|---|
| `run` | 建 run、认领、job 的执行中与终态、自己到期与 fail-fast、使用方中断时的结束写、报告 |
| `run --no-report` | 不写记录、不拿锁，同一套规则在内存里给出结果 |
| `submit --backend local` | 启动后台推进进程、经标准输入把它的输入一次交给它，由它生成运行定义、建 run 并推进；自己不拿锁、不建 run、不推进，转述它回报的结果（次序与回报见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」里「本机 `submit`」一条） |
| `submit --backend cloud` | 建 run；不推进 |
| 本机后台推进进程、云端 Lambda（`kicker`、`reconciler`） | 本机后台推进进程另拿锁、建 run（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三「谁在何时拿」）；认领、job 的执行中与终态、自己到期的结束写、报告；云端退出观察者只写退出记录，后端到期结束属于处置（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条） |
| `status --wait`、`settle-runs` | 处置条件成立时做结束写与报告；不认领、不启动、不投影。本机的 `settle-runs` 不给 run 标识时另删去建 run 中断留下的暂存目录（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三「谁在何时试拿」） |
| `list-runs`、不带 `--wait` 的 `status`、`explain` | 只读，不碰锁 |

报告只由使 run 成为终态的写入方生成（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」）。结束写见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节，处置的条件与入口见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、八，锁见 0054 决策三。`run` 只有本机后端，云端后端只支持 `submit`（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）。

- **`submit`**：云端为 plan → `create_run` 写 RunMeta 与全 pending → 打印 run_id → 退出，只写 runs 表与产物桶里这个 run 的 jobs 对象（提交记录在云端的存放形态见 [0030](./0030-realtime-persistence-seam.md) 决定六；用例带设备安装包时另上传安装包）、不起 task，冷启动交 kicker Lambda（见下 cloud 端到端流程）。本机为 plan 与补全运行定义 → 以新会话启动后台推进进程、经标准输入把它的全部输入一次交给它 → 后台推进进程生成运行定义、建 run（写 RunMeta 与全 pending）、回报结果 → `submit` 输出结果并退出；这个 run 从建立到结束都由那个后台推进进程用它自己生成的那份运行定义推进（见下 local 一节）。给了 `--expose-local` 时两种后端各在哪一步起隧道，见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」。
- **不带 `--wait` 的 `status`**：读 RunState 渲染一次（**纯只读、零副作用、不碰锁、不 tick**——保「查看」无惊讶 + 只需读权限）；提示只看记录与期限（写法同 `list-runs`，[0041](./0041-agent-facing-cli-affordances.md) 决策七）。**local/cloud 两路此渲染+提示+退出码逻辑经共享函数（`_render_status`）同一份实现、行为一致**，只命令示例按后端异（local 用 `--report-dir` / cloud 用 `--backend cloud --prefix`；查询命令的定位参数须与产生 run 的命令一致，规则与理由归 [0041](./0041-agent-facing-cli-affordances.md) 决策六）。
- **带 `--wait` 的 `status`**：轮询到终态；只盯到终态、处置条件成立时处置（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八），不认领、不推进，云端也不调用 kicker（见下「推进器与触发源」）。
- **`list-runs`**：列出一个后端里的 run（全部非终态 run 与最近 N 条终态 run），状态只从 RunState 读、零副作用；定位旗标与 status 相同，设计见 [0041](./0041-agent-facing-cli-affordances.md) 决策七。

`run` 与 `submit`+`status` 是**同一核心（纯归约 + 计划）的两种皮**——兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)「阻塞 vs 非阻塞是调用方的选择、同一核心两种皮」。但**两种皮各有自己的驱动模型、按命令分流**（见下「对 0016 的纠正」）：`run` 走 `schedule()` 的进程内 ThreadPoolExecutor 驱动循环、**不触 `reconcile.tick`**；`submit` 提交的 run 由无状态 reconciler 推进。故「共享同一 reconciler」只在 `submit` 提交的 run（本机后台推进进程与 kicker/reconciler Lambda——tick 三个宿主一份）成立，不含 `run`。

**退出码**：各命令的退出码见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定五。

## 端到端流程

### cloud（事件驱动，idle 零成本）

```
1. submit(CLI)：plan → create_run 先把 RunMeta 的 jobs 对象写进产物桶、再把 RunMeta 的头与全 pending 写到 runs 表（形态与次序见 [0030](./0030-realtime-persistence-seam.md) 决定六）→ CLI 退出（run_id 已在手）。
   **只写 runs 表与 jobs 对象（设备安装包另上传 S3）、不起任何 task**——submit 机器没有任何 ECS 写/执行权限，不碰 ECS RunTask（完整权限面以 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」末段的编排进程角色为唯一登记处；preflight 探针见其 preflight 条；冷启动由kicker Lambda 做，见下）。
1b. runs 表 Stream（**STATE 条目的新建**）→ [kicker Lambda]：新 run 的 **STATE item 落库即触发**
     （写序契约见下，触发时 definition 必已写成；事件源映射在部署中新建或更新的那一刻可能漏投这条记录，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」里「其它局限」）→ 过闸（下 4.）→ 这个 run 的两次 run 级定时触发各自尝试建立 → tick 起首批
     min(max_concurrency, |jobs|) 个 task（认领；max_concurrency 随 definition 到达、与部署侧 cap 取 min，见下机制四）。
     这是纯事件驱动链的**冷启动**（无此步则无 events/无 STOPPED，events Stream 永不触发第一次 reconciler）。
     定时触发先建、后推进，建不成不挡首轮推进，有建不成的在推进之后记为这条记录的失败、由流重试（次序的理由、两次的时刻与各做什么见
     [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条）。kicker 的过滤另命中使 run 成为终态的那次写：这次调用过闸、
     只清扫仍在执行的 task（0054 决策九第 2 条）。kicker 按流记录的种类（新建或修改）分辨这两种写，不按读到的状态分辨
     （理由见 0054 被拒方案「按读到的状态决定建不建 run 级触发」）。
     kicker 复用同一 `reconcile.tick`（三个宿主一份：本机后台推进进程 / kicker / reconciler）。
     **触发过滤不看后台执行标记**：云端的 run 都由 `submit` 提交、都由后端推进（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A），
     kicker 的 event source filter 按条目与写的种类匹配（两条过滤的写法见 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 13），
     reconciler 与退出观察者也不据标记分流。后台执行标记（这个 run 是否由 `submit` 提交）由组合根注入、随 `create_run` 写在运行态上：
     云端是 STATE 条目的顶层属性，本机是 `run_state.json` 的顶层键（此后每次写回原样保留，[0030](./0030-realtime-persistence-seam.md) 决定四「改写运行态时原样保留不认识的部分」条的 local 一项）。
     它只作描述：只进 `list-runs --json` 的 `detached` 键（[0041](./0041-agent-facing-cli-affordances.md) 决策七），不参与任何判断，
     处置不分前台与后台（0054 决策八）。它是执行环境属性、不进 core 模型（RunState/RunMeta 无此字段），
     读出它的只有 adapter 的列举（`RunListing.detached`）。
     **不变量：kicker 由 STATE 条目的新建触发，`create_run` 的写序 jobs 对象→`META`→`STATE` 是契约**——故被触发时 jobs 对象与 META（合起来是 definition）
     必已落（jobs 对象一侧的前提：S3 对写成的对象给出强一致的读，官方文档写明）；
     过滤若匹配 META 的新建，kicker 可能在 STATE 落库前就 tick，claim/投影全 CCF 空转（`DynamoDBRunStore.create_run` 守此写序）。
2. worker 云上跑（CLI 退出不杀 task，已实测）：PutItem 执行事件(seq 递增)→events 表；上传产物→S3
3. task STOPPED → ECS 自动发 "Task State Change: STOPPED" 事件 → EventBridge
     → [退出观察者 Lambda]：从事件 payload 读 exitCode（实测 4/4 都带，含 SIGKILL=137；缺则落哨兵 255 + reason，见机制二「退出码缺失」条）
       → PutItem 一条 task_exited 事件(独立键空间 + exitCode[+reason]) 到 events 表
4. events 表变化 → DynamoDB Stream → [reconciler Lambda]（**后端各入口共用的一道闸**，各分支与例外只在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时」一段写全，这里不转述；
     过闸之后不推进的两种收尾见下「已收尾的 run 不再推演」与「不经推进步骤的收尾」，其余推进）：
     ① 读该 run 全量 events → 纯推演完整 RunState
     ② HWM 条件写落 RunState（挡 stale 覆盖；投影写只前进、不越过 running、不写 job 终态，见机制三）
     ③ 这一轮已有结果的 job 按 [0030](./0030-realtime-persistence-seam.md) 决定三的逐 job 写序落库：先存明细，再以写入序号为条件写下它们的终态（机制三②）；记下最后一个 job 终态的那次写使 run 成为终态
     ④ 在这一轮读到的运行态加上③的作用上决策：running<max_concurrency 且有 pending：CAS(pending→running) 认领一个 → RunTask 启下一个（同一条条件写使 run 状态随之为 running；run 已结束后不再接受新认领，此前已成功的认领不由此撤销，见机制三「run 级状态只进不退」条①；停止认领之后不认领；认领之后还要建这个 job 的定时触发、上传 job 输入才发出 RunTask，启动请求可能晚于期限，这样的 job 按到期时还在执行处理，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 1 条与后台推进条）；停止认领之后没有 running、仍有 pending 时做到期的结束写，条件见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 3 条（以写入序号为条件，机制三②）
     报告由使 run 成为终态的写入方（③的终态写或④的结束写）生成（[0027](./0027-runreport-aggregation-index.md)），派生、失败隔离：生成在终态写之后、失败无人重试，为生成而读记录的那一次同样在隔离之内，不记为这条记录的失败——记为失败只会让流按批重试，重试的调用读到 run 已结束只清扫、补不回报告（下「已收尾的 run 不再推演」）；生成之后这次调用当场清扫（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条）
     **不变量：已收尾的 run 不再推演——run 已是终态时，云端推进器不推演、不投影、不认领、不存明细，只清扫它仍在执行的 task**
     （[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九；判在读 definition 之前：省掉强一致读 META 与取回 jobs 对象的那次 S3 请求）。
     理由：run 到终态之后运行态的任何写都不成立，执行方得知 run 已结束之后也不再存明细（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）；
     推演只会白读事件与运行定义，且 events 表开 TTL（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「events 表开 TTL」条）之后重算的结果也是错的：
     过期后 worker 事件已被删、只剩永不过期的退出记录，重算得「每个 job 都 error、零 scenario」。
     推进步骤自身这一轮读到终态也即返回（机制三「run 级状态只进不退」条④）；本闸判在读 definition 之前，保留它的理由见该条「为何放在 tick、不放在宿主」。
     挡的触发面：迟到重投、手工重放同一批 Stream 记录、到点停止与 run 级定时触发的 payload（与「job timeout」节「到点时 job 已终态 → tick no-op」同源），
     对已结束的 run 都只清扫；运行态已不存在的 run 同样只清扫（run 标识带随机尾、不复用，没有要保护的记录）。结束时仍在执行的 task 交给清扫：结束写结束了仍有 job 在执行的 run（含运行定义不可用时的
     error 变体，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节；别的格式写出、未结束的 run 同样由 error 变体结束，之后清扫，
     0054 决策九「落实时」一段），以及认领成功而启动迟到、在结束之后才起来的 task
     （task 的启动不随记录分出先后，见机制三「run 级状态只进不退」条①）；清扫由哪些调用带来、什么情形下没有人停，见 0054 决策九第 2 条
     与「边界与已知局限」里「run 到终态之后各组合下还会发生什么」表。**明确接受的代价**：从此没有「重 tick 一个已
     收尾的 run 来补写丢失报告」这条路——残余窗口 = 使 run 成为终态的那次写之后、推进器 2 分钟执行上限用尽那一瞬，此时 RunReport
     将永久缺失（判定明细在终态写之前已落、由终态点名，不受影响；报告是派生产物，宁缺不错）。
     这道闸是 handler 内的先读后判、不是原子的（别的实例可能在这次读之后才使 run 成为终态）。写级的保证是 run 到终态之后
     运行态的任何写都不成立（0054 决策五）；tick 自身读到终态的 baseline 即停止推演（机制三「run 级状态只进不退」条④）。
     分工：闸省掉整轮推演（含读 definition）；tick 的判停接住闸之后、tick 读 baseline 之前插入的终态；条件写挡下更晚的写。
     此前已成功的认领不由这几道撤销：认领与启动 task 是分开的两步，结束可能插在中间（机制三「run 级状态只进不退」条①）。
5. 级联：下一 task STOPPED → 再触发 3-4 → … 直到全 done
```

**idle 时零成本**：无 task 状态变化 = 无事件 = reconciler 零调用（EventBridge/Stream 事件驱动，非定时轮询——[CLAUDE.md「工作方式」：交付物运行成本是设计约束](../../CLAUDE.md)）。

### local（对称，无 ECS/Lambda）

```
submit(CLI)：plan 与补全运行定义 → 以新会话（setsid）启动后台推进进程（启动方式不把当前目录放进模块搜索路径，0037 决策 3），经它的标准输入一次交给它全部输入、另给一条回报管道 → 等到回报 → 输出结果并退出
后台推进进程（观察者+reconciler 合一）：取创建时刻 → 起隧道（给了 --expose-local 时）→ 生成运行定义 → 查 submit 是否还在
   → 建 run（含边界检查；在暂存目录上取锁，写好运行定义与运行态之后改名成 run 标识，0054 决策三、四）
   → 装配推进所需的各部分（含建事件库）→ 打开 reconcile.log → 回报结果（各步见 0035 决策 3「本机 submit」一条）
   → 用内存里的这份运行定义推进到 run 结束：spawn worker 子进程
   · 读 worker 的 fd3 事件流、旁路落本地持久 events sink（SQLite，替易失 FD3 pipe）
   · proc.wait() 拿 exitcode 写 task_exited · 按墙钟检查各 job 的截止时刻、到点停 worker · 推演写本地 RunState · 记下已有结果的 job 的终态 · 启下一个 · tick 返回 `COMMITTED` 或 `ENDED` 即退出（机制三「run 级状态只进不退」条④）
```

本机 `submit` 提交的 run 从建立到结束都在后台推进进程这一个进程里，与前台执行 `run` 的进程步骤与次序相同；它在哪一步取生命期锁、持有到何时，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三「谁在何时拿」。它的全部输入由 `submit` 按解析后的值经标准输入一次交来，它不读配置文件；推进用的是它自己生成、留在内存里的那份运行定义，不从记录读回，写进 run 目录的那份供 `status`、`explain` 等读取。后台推进进程收到哪些输入、在建 run 之前之后各做哪几步、回报的内容、`submit` 的输出与退出码，以及 `submit` 或后台推进进程在回报之前、之后退出时各怎样，见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」里「本机 `submit`」一条。被拒方案：后台推进进程建 run 之后从记录读回运行定义再推进——记录就是它自己刚写下的那份，读回得不到新的信息，只多出一种本机独有的失败（读不懂自己写下的记录）和为它另设的结束写；前台 `run` 同样不读回，两个本机推进器在这一点上相同。

**同一份 core 推演代码，两个宿主（Lambda / 后台推进进程）各注入自己的 adapter**——local/cloud 对称落到 events 通道：两侧 reconciler 都从持久 events 重放推演，**唯一差别是存储介质**（DDB 表 vs 本地 SQLite）+ **谁把 worker 事件写进该存储**（cloud=worker 自己 PutItem，[0024](./0024-worker-core-protocol.md)；local=后台推进进程读 worker fd3 后旁路落 SQLite）。

**关键：local 的 worker 不改、对 SQLite 无知（实装校准）**——worker 仍讲 [0024](./0024-worker-core-protocol.md) fd3 协议吐原始 JSON 行（引擎无关、两执行环境同一份 worker），SQLite 落库是后台推进进程侧 `SubprocessLauncher` 读 fd3 时旁路做的（存原始行 + 按到达序赋 worker 段单调 seq）。故「worker 写持久 events 存储」在 local 的准确表述是「后台推进进程代 worker 写」——worker 业务零改，对称性落在「事件最终进了持久可重放存储」这一层，非「worker 自己写哪」。

**后台推进进程内多 worker 并发写同一 SQLite 的串行化（实装处理）**：`max_concurrency>1` 时后台推进进程并发起多个 worker，每个一个 fd3 读线程往同一 SQLite append。SQLite 单写者——多线程 append 靠 **WAL 模式 + 短事务**串行化（写争锁排队、不丢不乱；每条 append 是独立小事务）。这是进程内的线程并发（非跨进程），锁竞争轻、可接受。**跨进程写 events sink**：只有持锁的推进器写（本机的 run 至多一个推进器，见下「推进器与触发源」），没有第二个进程起 worker、写同一个 events sink。

**读端快照不变量（实装处理）**：`SqliteEventLog.records()` 在单个读事务内读 events 与 exits 两表，两者出自同一份快照。WAL 下自动提交模式的每条 SELECT 各取一个快照，分两次读可能读到某 scope 的退出记录、却漏掉写端在它之前提交的 `scope_done`；投影按「退出码 0、无 `scope_done`」把该 job 判成 ERROR，错判即随这个 job 的终态写下，终态只写一次、无从纠正。tick 写下各 job 终态所用的判定出自本 tick 已读的同一份 records（逐 job 的写序，[0030](./0030-realtime-persistence-seam.md) 决定三），本条保证那份 records 自身前后一致。回归护栏 `core/tests/test_sqlite_event_log.py::test_records_reads_events_and_exits_from_one_snapshot`。

## 推进器与触发源

1. **本机后端的 run 任何时刻至多一个推进器**：前台是执行 `run` 的进程，后台是 `submit` 启动的后台推进进程，都持有它的生命期锁（何时取、持有到何时见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三「谁在何时拿」）。认领、启动 job、写 job 的执行中与终态只由它做，结束写（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）由它或处置方做。本机 worker 是推进器的子进程，生死系在它身上。
2. **云端允许多次 Lambda 调用重叠推进同一个 run**。入口有两个，每一步写带条件（机制三）：`reconciler` 接 events 表流；`kicker` 接 runs 表流上的两条过滤（STATE 条目的新建；使 run 成为终态的那次写，写法见 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 13）与三类一次性定时触发（job 到点，见下「job timeout」节；run 的期限与期限加 300 秒，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条）。`kicker` 只认三种载荷：流记录、job 到点的 `{run_id, timeout_scope}`、run 级定时触发的 `{run_id, run_timer}`（`run_timer` 为 `deadline` 或 `overdue`）；其余载荷（含只带 `run_id` 的）记一行日志、正常返回、不推进，不抛出：抛出会让异步调用重试一个没有意义的载荷。`status --wait` 不调用 `kicker`：唤醒推进的只有流与定时触发，它只盯到终态、处置条件成立时处置（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）。不把推进入口收成一个、也不按 run 串行排队（见被拒方案）。
3. **推进器中断时**：本机推进器的进程退出之后，这个 run 不续，只能由处置方结束（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、七；本机没有常驻的处置方，见 0054 决策八），推进器自己因读写记录失败退出时，说明里给出结束它要用的 `settle-runs` 命令（0054 决策八「管它的进程退出而 run 未结束的出口」一条）；云端一次调用失败时，流的重试与之后的触发可以接着推进（一批流记录里各 run 各自处理，一个 run 的失败不打断同批别的 run，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条）；推进链断开的 run 怎样结束见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条（含前提）。

理由：推进权只有一个持有者（本机是持锁的推进器，云端是后端自己），谁在推进就不需要从外面推断。允许查询命令在推进器之外接着推进，就得从外面判断推进器是否还在、是否已收尾完，而这两类外部推断都不成立：凭时钟加一段时长的推断三次失守（被拒方案「本机接力，及其改法」），凭对方进程的信息核对身份在 Linux 上不断出现新的反例（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 被拒方案「读对方进程的信息」）。本机由锁把死活交给内核回答（0054 决策三）；云端没有本机进程，推进器只有后端，多次调用重叠时各记录靠条件写分出先后（机制三），不需要判断谁还在。

## 四个关键机制（机制二/三/四有地基实测支撑，机制一从 [0024](./0024-worker-core-protocol.md) seq 不变量推导、独立键空间存取由单测覆盖 `test_sqlite_event_log`/`test_cloud_reconcile`）

### 机制一：`task_exited` 用独立键空间（不入 worker 数值 seq 段）

退出观察者**不持有** worker 的 seq 计数器（[0024](./0024-worker-core-protocol.md)：seq 单进程串行自增、无分布式协调）。若 `task_exited` 塞进 worker 的连续数值 seq 段，DDB 最终一致读会算错 max seq → 撞号**覆盖 `scope_done`**（裸 PutItem 无条件写），或造空号让 adapter 断号检测死循环。**故 `task_exited` 用独立键空间**，adapter 的单调 seq/断号检测只跑 worker 的连续 seq 段，退出事件旁挂不入流。**两侧落地形态（实装）**：cloud events 表 SK 是 NUMBER（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 events 表），**字符串前缀（`exit#` 之类）结构上不可行**——护栏记此，别再往 NUMBER SK 上设计前缀；改用**保留高位数值 SK**（`10**18`，worker seq 从 1 递增、永不到它）+ 属性 `item_type='exit'`；这一认法归 run 记录格式版本；退出观察者不读 runs 表、按后端自己的格式写，数据版本不同时不保证对方读得出（[0037](./0037-distribution-and-packaging.md) 决策 7「三个号各管什么」「写读次序」）。local SQLite 用**独立 `exits` 表**（不占 events 表的 `(scope_id, seq)` 键空间）。worker「每 PK 单写者、seq 单进程自增」不变量**原样保留**——events 表只是多了一个**独立键空间**的第二写者（演进 [0024](./0024-worker-core-protocol.md)，见下）。

**读 events 表的一方按 `item_type` 分流**：exit item 只有 `pk/seq/item_type/exit_code?/timed_out?/reason?/exited_at?`、**无 `body` 属性**（它不是一条 [0024](./0024-worker-core-protocol.md) 事件行），按「每个 item 都是事件行」取 `body` 的读法读到它即 `KeyError`。events 表的读者都经按 `item_type` 分流的 `DdbEventLog.records()`：推进步骤，以及 `explain` 对云端 run 的补取（[0042](./0042-step-evidence-and-explain.md) 决策七）。

### 机制二：退出事件由平台侧观察者提供，从事件 payload 读 exitCode

**退出绝不能 worker 自报**：worker 可能被 SIGKILL 硬杀、或发完 `scope_done` 才在会话释放时非 0 退出——它**没机会**再 PutItem 报告自己的退出。故「进程干净终止」的信号只有平台/父进程看得见：cloud = ECS Task STOPPED 事件；local = 后台推进进程 `proc.wait()`。观察者从该信号取 exitCode 写 `task_exited`。

**「两件都要」（[0024](./0024-worker-core-protocol.md) 终止契约）在 reconciler 里成为对事件日志的纯谓词**——但**「内容完整（scope_done）」只对声称成功（exit==0）的进程要求**（真跑 crash worker 逼出的精确化）：

- **`task_exited` 且 exit≠0（崩溃/网络故障退出码 80/SIGKILL）→ ERROR 终态，不等 `scope_done`**：worker 崩了根本没机会发 `scope_done`，此时**进程非干净终止本身就是终态信号**。若仍死等 `scope_done`，crash job 停在 RUNNING、推进器写不下它的终态（真跑 crash worker 复现，回归护栏 `core/tests/test_project.py::test_crash_no_scope_done_nonzero_exit_is_error`）。这一分支也覆盖「发完 scope_done 又非 0 退出」的误报 PASSED（exit≠0 一律 error，不看内容；唯推进器已主动中止的 job 按下「终结函数与真值表」先判 timeout 或 aborted）。
- **`task_exited` 且 exit==0 → 要求 `scope_done`**：干净退出才谈「内容完整」。有 `scope_done` → 先看 `scope_done.status`（为 error 即 ERROR，归因按下表：未确认集非空为 `release_failed`、否则取其 `errorType`；它承载 worker 报告的执行前失败与执行中途的会话丢失，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4），再看 scenario 判定集（为空即 ERROR，消息「worker 未报告任何 scenario 判定」——否则 `_aggregate([])` 把零 scenario 的 `scope_done` 判成 PASSED），再 scenario 归约终态（passed/failed/error）；干净退出却没 `scope_done`（矛盾：进程说成功、内容没发完）→ ERROR（判 error 比让 job 停在 RUNNING 安全）。完整的判定顺序见下「终结函数与真值表」。
- **`task_exited` 且退出码未知（观察者没能取到 exitCode）→ ERROR 终态**：STOPPED 事件是观察者的**唯一一次机会**（ECS 不会为补齐退出码再发一次事件），「等观察者补」在事件驱动模型里结构上不存在；退出码未知即不可判定为通过，判 error 比无界等待安全（观察者侧落哨兵退出码，见下「退出码缺失」条）。
- **无 `task_exited`（进程还没终止）→ RUNNING（见了非 `attempted` 的 `session_opened` 或 `scope_started`）/ PENDING（还没起）**：建了会话的 scope 在 `scope_started` 之前先发 `session_opened`（桌面在 StartBrowserSession 返回后、设备在 Create 返回后，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4），设备在取设备期间、桌面在建连与会话预热期间 job 即算 RUNNING；只有 `attempted` 的 `session_opened` 不算 RUNNING。

即：**进程终止（exit≠0）优先于内容完整判终态**；只有干净退出（exit==0）才回到「scope_done ∧ exit」的两件都要（实现见终结函数 `core.project.finalize_job`）。推进器的主动停止判定（超时、fail-fast 中止）又优先于两者，完整顺序见下「终结函数与真值表」。

**`task_exited` 的判定不设「已见 scope_started」前置**（code-health 对抗验证逼出的精确化）：上表按「有无 task_exited」为一级键——**零事件 + exit==0**（构造期 SIGTERM → flag-only handler 构造完成即 `return 0`，[0024](./0024-worker-core-protocol.md) 设计内行为）与**零事件 + 退出码缺失**（TaskFailedToStart，如镜像拉取失败的 STOPPED 事件无 exitCode，观察者落哨兵）都必须走上表对应分支（两者皆 ERROR），**不得因「没见 scope_started」短路成 PENDING**——PENDING 与已 claim 的 RUNNING 基线单调合并后 job 停在 RUNNING、推进步骤写不下它的终态（探针复现：4 轮 tick 不推进且 events 不再新增）。回归护栏 `core/tests/test_project.py` 的 exit-without-events 真值表用例。

**launch 失败补偿——「起不来」也是一种进程终止（机制二的推论，code-health 对抗验证逼出）**：认领成功后 `launcher.launch(job, cutoff_at=…)`（`cutoff_at` 是 tick 由认领时刻、job 预算与运行期限算出的截止时刻，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条）可能抛异常（RunTask 放置失败/容量不足/task-def 配错/Popen OSError——其中 task-def 名配错是**确定性触发器**、每 job 必炸），此时 job 已被置 RUNNING 却永无 events、无 task_exited（进程根本没起、平台侧观察者无从观察）——若异常裸穿 tick，job 停在 RUNNING，之后任何一次推进都记不下它起不来这件事（「状态全持久、断点续」的可恢复性断言被推翻）；cloud 侧 Stream 重试还会因 job 已 running 而「成功」no-op、掩盖故障。**修法 = launch 的宿主（tick）扮演「起不来」这一时刻的退出观察者**：catch 异常 → 再取一次时刻 → `event_log.record_exit(scope_id, None, reason="起 worker 失败：<异常文本>", exited_at=<这一刻>)` → 下轮重放经终结函数收敛终态（退出码未知判 ERROR；退出时刻晚于这个 job 的截止时刻的，投影按超时交给终结函数，见「job timeout」节「`timed_out` 归因链」条）。补偿只记事实、不带 `timed_out`。交给终结函数的输入与同步路径（`schedule` 起 worker 失败时：退出码未知、同一句原因、按同一个判断决定是否记超时）相同，两条路径对同一个启动异常给出同一句说明（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「时刻」；不写平台失败的哨兵退出码 255：那会让说明比同步路径多一段平台归因的前缀）；RunTask 放置失败的归因、引擎这次装配不出来时给出的指引因此到达使用方；traceback 另由 tick 以 warning 级记日志，供排障。退出观察者取不到退出码时写哨兵（下条），两者是不同的写法。不发明新状态、不加重试（launch 级重试属 job 级重试的既有留口子）、异常不中断本 tick 其余 job（失败隔离，[0026](./0026-schedule-module.md)）。回归护栏 `core/tests/test_reconcile.py::test_launch_failure_does_not_wedge_run`、`::test_launch_failure_records_unknown_exit_with_the_same_reason_as_the_foreground`、`::test_launch_failure_after_the_cutoff_projects_as_timeout` 与 `core/tests/test_termination_parity.py::test_launch_failure_agrees_between_the_foreground_and_the_advancer`。

**退出码缺失：观察者落哨兵、不留宽限态（修正）**：本 ADR 最初把「STOPPED 但 exitCode 未落值」定义为有界宽限态（投影保守 RUNNING、观察者"短暂重查 DescribeTasks"兜底），根据是 [0024](./0024-worker-core-protocol.md) 记的 `lastStatus==STOPPED` 与 exitCode 落值非原子。**修正理由（code-health 对抗验证发现）**：①补齐退出码在事件驱动下没有第二次机会——ECS 对一个 task 只发一次 STOPPED 事件，观察者无 ECS 权限也不该有（薄 handler），所以宽限态在实装里是**无界**的；②容器根本没跑起来的形态（`stopCode=TaskFailedToStart`：拉不到镜像、缺 secret、放置失败）exitCode **必然**缺失，不是延迟而是永不——按旧表判 RUNNING 即 run 永久 wedge、之后的推进都救不回。**决定**：观察者对缺 exitCode 的 STOPPED **一律落非 0 哨兵**（常量 `PLATFORM_FAILED_EXIT=255`，core 单点定义；上条 launch 失败补偿不写它、记退出码未知）并带 `reason`（`stopCode: stoppedReason`，随 `task_exited` 进事件日志、投影进 job message 让用户看到归因）；终结函数 `finalize_job` 对「有退出记录、非超时、退出码未知」判 ERROR（防御：老版本观察者或未知写者仍写 None 时不 wedge）。STOPPED 事件锚在 `stoppedAt`（已过落值窗口），正常退出必带退出码——实测 H1/H2 见地基实测节；哨兵只在容器没跑过时出现。**真跑坐实（坏镜像 tag 的 detached run）**：task-def 指向不存在的 ECR tag 提交 → STOPPED 事件 `stopCode=TaskFailedToStart`、无 exitCode → 观察者落 255 + reason → reconciler 一轮 tick 判 error 并 finalize，**run 在有界时间内到终态**，判定明细的 message 带出观察者落的归因「TaskFailedToStart: CannotPullContainerError: … not found」（当时的前缀措辞已改写，现行文案见 `project.finalize_job` 的 255 分支）；同一场景在修正前的实装下 run 永久 RUNNING。**被拒**：给观察者加 DescribeTasks 重查/延迟重试——要加 ECS IAM 与调度机器，服务的却是一个实测从未出现、且对 TaskFailedToStart 无意义（永不落值）的形态。

#### 终结函数与真值表

**两条归约路径共用一个终结函数**（`core.project.finalize_job`）：同步路径（`schedule` 的每 job 驱动）与无状态路径（`project` 的 `_reduce_scope`）都只调它，事件归约本身继续只累积事实、不下判定——判定逻辑分两处写必然漂移（同步路径曾在事件分支先判 timeout、异常与 EOF 分支先判 abort，两处顺序相反）。输入：

- **`stop_reason ∈ {none, timeout, abort}`**：推进器的主动停止判定，不论是否实际发出了停止命令。**首次仲裁规则只有一条**：推进器第一次对该 job 作出停止决定的那一刻落定；若此刻 deadline 已过，即使整批中止标志也已置（来源是 fail-fast、使用方中断或发现 run 已被别处记为已结束，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二，三者同一规则），也取 timeout（本 job 的截止时刻已到这一事实比整批的连带中止更具体，也是使用方能直接处理的原因）。`_stop_all` 批量中止时，对每个受影响的 job 在那一刻按同一规则当场落定（deadline 未过的记 abort）。同步路径把落定值写进 JobResult，之后任何分支不改写。**内容完整后不再仲裁**：已干净退出且发了 `scope_done` 的 job 不受停止原因约束——判定已成，收尾拖过预算只该让它有界，不该改写结论（否则同一事实依 deadline 后、EOF 前有没有恰好来一次心跳而得出不同判定）。同步路径收到 `scope_done` 后不再落定停止原因：deadline 到点只向 worker 发停止请求并设排空上界，fail-fast 的批量中止不打断它的释放阶段、`_stop_all` 对它不落定；无状态路径按超时交来的退出（带 `timed_out`，或 `exited_at` 晚于截止时刻）遇到 `scope_done` 加退出码 0 时同样不改判，两条路径由终结函数的同一条件保证。非零退出或退出码未知不算内容完整（进程终止优先于内容完整），照常受前三行约束。无状态路径没有 fail-fast（`submit` 不提供该选项），`stop_reason` 只可能是 none 或 timeout，由投影从退出记录得出：记录带 `timed_out`（来源两个：job 到点停止后经观察链写入的退出记录、cloud 的 job 到点停止在两个 task 列表都无踪时补写的记录（见「job timeout」节）），或记录的退出时刻 `exited_at` 严格晚于这个 job 的截止时刻（worker 在截止时刻之后、停止请求发出之前自行退出；tick 的 launch 失败补偿在截止时刻之后才失败，见上「launch 失败补偿」条），都取 timeout。写入方只记事实，重放不再仲裁，判断只在投影里做一次（见「job timeout」节「`timed_out` 归因链」条）。两条路径的 deadline 都是以运行期限封顶的截止时刻（算法在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条）。起作用的是 job 的预算还是运行期限，是终结函数的另一项输入，只看截止时刻、不看说明（说明只是描述，[0031](./0031-job-lifecycle-states-and-severity.md) 决定一）：两者分走真值表的两行，预算截断为 ERROR 加 `timeout`，期限截断为 ABORTED、无归因（状态语义在 0031 决定一）；内容完整不改判的规则对两者原样适用。起作用的是哪一个不进退出记录，无状态路径在投影时由运行态里的认领时刻、预算与期限重算（写 job 终态所用的快照里有记录的 job 都须带认领时刻，0054 决策二后台推进条「快照」）。fail-fast 的批量中止在无状态路径重新宿主为 reconciler 的动作后（本 ADR 留口子），`stop_reason` 才会出现 abort，终结函数与真值表已含该行、不需改。
- **退出信息**（退出码，或未知）、**`scope_done` 及其 `status`**、**scenario 判定集**。
- **未确认集 U**：发过 `session_opened` 而没有 `release: confirmed` 的 `session_closed` 的会话，按配对键（`sessionId`，没有时用会话名）计算；`origin: attempted` 的尝试永远不会被确认，天然在 U 里（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4、5）。

| 条件（按行序取第一个命中） | 判定 | 归因 |
|---|---|---|
| `stop_reason = timeout` 且内容不完整，起作用的截止时刻是 job 的预算 | ERROR | `timeout` |
| `stop_reason = timeout` 且内容不完整，起作用的截止时刻是运行期限 | ABORTED | 无 |
| `stop_reason = abort` 且内容不完整 | ABORTED | 无 |
| 退出码非零或未知 | ERROR | U 非空为 `release_failed`；否则退出码 80 为 `network_error`，其余为 `engine_error`。消息保留退出原因；先报了 scope 级 error 再非零退出的，保留 worker 报的那句 |
| 退出码 0，无 `scope_done` | ERROR | `engine_error` |
| 退出码 0，`scope_done.status = error` | ERROR | U 非空为 `release_failed`，否则取 `scope_done.errorType` |
| 退出码 0，`scope_done` 无 status，scenario 判定集为空 | ERROR | `engine_error`，消息「worker 未报告任何 scenario 判定」 |
| 退出码 0，`scope_done` 无 status，判定集非空 | `_aggregate`（原规则） | U 非空（worker 违约）时改判 ERROR、`release_failed` |
| 未退出 | 见过非 `attempted` 的 `session_opened` 或 `scope_started` 为 RUNNING，否则 PENDING（只有 `attempted` 的 `session_opened` 不算 RUNNING） | |

「内容完整」= 退出码 0 且收到 `scope_done`（见上「内容完整后不再仲裁」）。

- **明细补全与判定分开**：明细只依据已收到的完成事实。收到 `scope_done.status = error` 即对 definition 中无事件的 scenario 合成 scenario 级 SKIPPED 及其全部 step 的 `SKIPPED(shortcircuited=False)`；在途 scenario 整条不合成（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一、三、六）；之后到达的 timeout、abort 或非零退出只改变判定与归因，不撤销已合成的明细。没有收到 `scope_done` 时不合成；在途明细（有 `step_started` 无 `step_done` 的 step、有 `scenario_started` 无 `scenario_done` 的 scenario）不合成任何记录，保持缺记录状态，由 `explain` 表示「有现场可查」。
- **U 非空时无论判定为何**，job message 追加产品语言提示，按 job 的目标是否为设备二选一（桌面 worker 也发会话事件，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4、7）：设备 job 为「远程访问会话未能确认停止，可能仍在计费，请在设备控制台核对并手动停止」，桌面 job 为「AgentCore 浏览器会话未能确认停止，可能仍在计费，请在 Amazon Bedrock AgentCore 控制台核对并手动停止」（归因改为 `release_failed` 的行保留原因消息，提示追加在后），并列出 U 中各项的会话名，`attempted` 的尝试标为「结果未知的创建尝试」、与「已创建但未确认停止」的会话分开列（尝试只有名字可列，这正是使用方到控制台核对时需要的）。
- **停止后继续有界消费完整事件流**：推进器作出停止决定后，仍把触发该决定的当前事件与后续事件全部归约，直到 EOF 或排空上界。同步路径曾先从迭代器取事件、再查 deadline、再归约，触发超时检查的那条事件本身没有被归约，停止后到达的 `session_closed` 也会丢失，使 U 算错；无状态路径重放全部已写事件，天然满足。
  - **排空上界取首次停止请求时刻加停止宽限 `grace_period_s`、再加余量 `DRAIN_MARGIN_S`（5 s）**：从请求时刻起算，`handle.stop` 自身的阻塞计入其中、不另加；内容已完整、deadline 才到的 job 从催收尾（`hurry_exit`）的那一刻起算。同步路径只有本机后端（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）：`SubprocessWorkerHandle.stop` 对 worker 进程组发 SIGTERM、等 grace、到期对整组 SIGKILL，进程退出即事件流 EOF；这段等待由停止机制自身封顶，停止后的等待预算就是 grace，`ScheduleOpts` 不另设等待预算。余量 `DRAIN_MARGIN_S` 住 core。**超出预算仍可能漏观测**：到点时还没到达的 `session_closed` 不计入，该会话记为未确认；没等到 EOF 的 job 退出码记为未知；两者都按本节既有规则进终结函数。会话是否真的泄漏不由这一侧兜底：桌面的 AgentCore 浏览器会话由 [0032](./0032-fargate-execution-environment.md) 结论 4 已接受的硬杀与会话 TTL 兜底承接，设备的远程访问会话由 Device Farm 的 150 分钟上限封顶（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 6「不做回收器」条）。
  - **停止调用自身也有界**：`SubprocessWorkerHandle.stop` 最多阻塞 grace 加对两条输出转发线程（stdout、stderr）各一次的有界等待（每条 0.5 s，合计至多 1 s），落在等待预算加余量之内；它的阻塞计入等待预算（预算从请求时刻起算），阻塞超出预算时同样按上文「超出预算仍可能漏观测」处理。终结处不无条件再阻塞：补发停止请求只在事件流没有正常结束（排空上界到点退出、或普通异常后 worker 可能仍在运行）时才做，事件流已到 EOF 或已拿到退出码的 job 不再补发。理由：事件流已结束说明 worker 已经退出，再发一次停止请求不改变任何事实，只会把 job 的结束再推迟一次停止调用的阻塞。
- **双路径对拍是实施护栏**：同一组事件矩阵（前置 scope 级 error 加退出 0、scope 级 error 后超时（内容完整：判定按 scope 级 error、合成明细不撤销）、停止后到达的 `session_opened`、未确认的 `session_closed`、零 scenario 的 `scope_done`、cloud tick 对无踪 task 补写 `timed_out`、期限截断与预算截断（起作用的截止时刻分别是运行期限与 job 的预算：前者 ABORTED、无归因，后者 ERROR、`timeout`）、无 ARN 的未知 Create 加取消、已记真实 ARN 后到达的 `attempted` `session_opened`（job 的 session_id 不变、`sessions[]` 多出一项 null、两个计量键都不计它）、只有 `attempted` 的 `session_opened`（未退出时两条路径都为 PENDING）、worker 在截止时刻之后或之前以非零退出码自行退出与内容完整而退出时刻晚于截止时刻（无状态一侧的退出记录只带 `exited_at`、不带 `timed_out`））输入两条路径，判定、归因与明细逐项相等；含 abort 的行（timeout 与 abort 同时成立、先判 abort 而收尾期间 deadline 才到仍为 abort）只输入同步路径，fail-fast 宿主到无状态路径后再加入共同矩阵。

### 机制三：重叠推进下各记录的先后（RunState 条件写为主）

云端的多次调用可以重叠推进同一个 run（「推进器与触发源」第 2 条），各记录靠下面这些分出先后：

- **提交记录**：头（META 条目）只在不存在时写，之后不变；jobs 对象每次建 run 写在新生成的键下、带「键不存在才写」的条件，不覆盖别的对象，写下之后不变；同一个 run 标识的两次建 run 由建 run 的几次条件写裁定：两次的 jobs 对象键相同时，后到的一方在 jobs 对象的条件写就被挡下，键不同时由头的条件写裁定（形态与建 run 的次序见 [0030](./0030-realtime-persistence-seam.md) 决定六「建 run 是条件写」条）。
- **运行态条目**：建 run 要求不存在；认领要求 job 为 `pending` 且 run 未结束；投影的每一次写（标量一步与逐 job 的各次写）都要求库中 HWM 不大于这次投影的 HWM 且 run 未结束，逐 job 的写另要求库中该 job 不比投影更推进，且这次写提及的字段（状态，以及投影带了时的会话、认领时刻）至少一项与库中此刻的值不同，写入的 job 态不越过 `running`（下「② 的 job 级半边落地形态」段）；记下 job 终态与结束写要求写入序号等于读到的值（下②）。每个 job 的终态与 run 的终态各至多写成一次（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补、决定三），条件写不保证最终写成。
- **判定明细**：写不带条件，用哪一份由 job 的终态点名（[0030](./0030-realtime-persistence-seam.md) 决定三）。
- **报告的生成方**：只有使 run 成为终态的那次写的写入方，这样的写至多一次；所含判定由记录确定（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」、[0030](./0030-realtime-persistence-seam.md) 决定三）。
- **退出记录**：观察到的退出与启动失败的补写覆盖同键，补写的未知退出只在没有记录时写入，之间按最后一次写为准；job 终态写下之后的变化不被采用，两者可能长期不一致，以运行态为准。
- **定时触发**：按确定的名字建立，已存在即视为已建。

本机的 run 至多一个推进器，处置方可能与它同时写（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、八）；本机建 run 之后的各写入口在 `.runstate.lock` 内读改写、按锁内读到的整份运行态计算（下②），建 run 不取这把锁：运行定义与运行态先写进暂存目录，写完才原子改名成 run 标识（[0030](./0030-realtime-persistence-seam.md) 决定四）。所以下面讲的并发实例只出在云端。

云端的 reconciler **物理上是并发实例**（实测：DDB Stream 按 PK 分片、多 job 触发 2 个并发 Lambda 实例）。并发实例读快照时点不同：实例 A 读到 seq=10 推演 `{running}`，实例 B 读到 seq=20 推演 `{passed}` 先写，A 用旧快照后写会**覆盖终态**（把 `passed` 刷回 `running`，外部看到非单调）。全量重放保证**派生逻辑**幂等、抗乱序，但**不保证跨实例写序**。

**解法 = 两道条件写，各管一类回退，不能只用 HWM**：

- **① HWM 挡 worker 执行事件段内的 stale 覆盖**：`RunState` 带 `high_water_mark`（已处理的 worker 段 max seq）；投影的每一次写（DDB 的标量一步与逐 job 的各次写，下「② 的 job 级半边落地形态」段）条件都含 `attribute_not_exists OR :hwm >= hwm`，HWM 小于库中值的 stale 实例的写被 `ConditionalCheckFailedException` 挡掉。这管的是「A 读到 seq=10、B 读到 seq=20，A 迟到写覆盖 B」这类**数值 seq 可比**的回退。
- **② job 终态只写一次：记下 job 终态的写与结束写以写入序号为条件（HWM 挡不住的边界，必须单列）**：`task_exited` 走独立键空间、**不带数值 seq**（机制一），故「被 `scope_done`（末 seq=5）触发的投影」与「被 `task_exited` 触发的投影」携带**相同 HWM(=5)**——单靠 HWM(`5>=5` 成立) **挡不住** stale 的投影把已终态的 job 刷回 `running`。所以投影只前进、**不越过 `running`、不写 job 终态**；job 的终态只写一次，迟到的结果不被采用（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补），由记下 job 终态的写写下（逐 job 的写序在 [0030](./0030-realtime-persistence-seam.md) 决定三）。
  - **云端**：运行态条目带写入序号，改变了整体替换所写内容（`jobs` 与 run 状态）的写在同一次写里把它加一，不改变这些内容的写不加（各写入口加不加见 [0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条）；记下 job 终态的写与结束写以「序号等于读到的值」为条件，写不成即重读再算，且对 `jobs` 整体替换（替换的内容由这一次读到的运行态算出，终态写给出的 job 按字段与读到的条目合并，[0030](./0030-realtime-persistence-seam.md) 决定四）；认领与投影沿用各自的条件（见上）（属性、两个写入口的步骤与重读的次数上限见 0030 决定六同一条）。**本机**：建 run 之后的各写入口在 `.runstate.lock` 内读改写，按锁内读到的整份运行态计算。两侧都在同一次写里按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法写 run 状态（投影写怎样落这一条见下「投影写的 run 状态」段）；run 到终态之后运行态的任何写都不成立（规则与理由在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五，端口的写入口在 [0030](./0030-realtime-persistence-seam.md) 决定四）。
  - **理由**：两个调用各记一个 job 的终态、各自读到对方的 job 未结束时，不加条件会留下「全部 job 已结束、run 仍为 `running`」；按 job 逐个加条件，表达式随 job 数增长，放弃（实测逐个路径写在两百多个 job 时超长）。真实 DynamoDB 上在写入层核过（未经产品代码）：整体替换的表达式长度与 job 数无关（50、300、1000 个 job 的样本都写得成），上限由单条记录的大小上限决定（下面的条目大小）；两个进程以同一序号并发写，每次恰有一个写成，另一个重读重算后写成、恰有一方使 run 成为终态；不加条件时逐个路径写留下上述情形、整体替换丢掉另一方的终态。整体替换只以写入序号为条件，所以改变了整体替换所写内容的写都要把序号加一：一次改变了这些内容而不加一的写若落在另一个调用读运行态之后、那个调用整体替换之前，就会被那次整体替换盖掉（例如运行中的 job 换台重建之后更新的代表会话，见下「生命周期序单调不等于字段单调」条）。不改变这些内容的写没有可被盖掉的东西，不必加（各写入口按这条原则加不加，见上一条所指的 0030 决定六）。
    **条目大小**（真实的表上实测，整体替换 `jobs` 的写，条目形态照 `_job_state_to_item`）：一条记录装得下的最大 job 数为桌面会话（约 26 字节）、scope 标识 40 字节 2589 个，设备会话 170 字节、scope 标识 40 字节 1354 个，设备会话、scope 标识 100 字节 1130 个，桌面会话、scope 标识 255 字节 1096 个，设备会话、scope 标识 255 字节 791 个；1000 个 job 在会话 64 字节、scope 标识 255 字节时已装不下。由这五格的可装数反推（单条记录的上限 409,600 字节除以可装数，再减去两个标识的字节数，五格都落在 92.1 到 92.8 字节之间），终态条目约为 scope 标识字节数加会话标识字节数加 92 字节（含点名明细的标识，[0030](./0030-realtime-persistence-seam.md) 决定三）。约 300KB 的条目写成一次消耗 294 个写单位。由结束写结束的 job 另带一句 job 级说明（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节；处置两行的句子按 UTF-8 计 84 到 87 字节，error 变体约 220 字节；error 变体的原因句拼进取自记录的值（写出版本、记录格式版本数、worker 协议版本数），这些值都按字节截断，句子的长度因此有上界），它落在结束这类 run 必须写成的那一次写上：建 run 时每个 job 条目只有状态，记录建得成、推进得了，结束写却可能超出单条记录的大小上限。超出时 DynamoDB 拒绝这次写，错误不是条件不成立，adapter 原样抛出、不重读，运行态不变；没有一方能结束这个 run，它留在 `live` 分组，它引用的 revision 不被回收。所以一个 run 的 job 数与两个标识的长度各有上限：job 数与 scope 标识在计划阶段检查（[0025](./0025-plan-module-feature-to-jobs.md)「一个 run 的规模上限」），会话标识的上限在 worker 协议里（[0024](./0024-worker-core-protocol.md)「输出」节「字段语义」的 `sessionId` 条）；按上面的反推式推算，上限之内结束写装得下（推算见 0025 同一节），最宽一格的整条结束写在真实的表上还没有核过（下实测项）。
  - **实测项**：已核（真实的表）：条目大小与装得下的 job 数（上「理由」），投影逐 job 写的条件表达式（下「② 的 job 级半边落地形态」段），本机测试用的替身（moto）对这些写法给出的结果与真实的表相同。余下的实装时以真实环境核：终态之后到达的退出记录、前台终态写、投影都不改变记录，两个 adapter 对拍；整体替换 `jobs` 的两个按模型的写入口（记下 job 终态的写与按本格式的模型算出的结束写）经产品代码在真实的表上各写一次，读到的条目带一个不认识的属性，写下之后它原样在、各已知键取这次算出的值（并入的做法此前只在测试替身上核过，[0030](./0030-realtime-persistence-seam.md) 决定四「改写运行态时原样保留不认识的部分」条）；经 Lambda 的代码在真 DynamoDB 上重做上述并发，只有一方生成报告；500 个 job、scope 标识与会话标识都取 255 字节、20 个执行中、其余各取可达的最宽形态（由执行结果结束、带会话标识、认领时刻与点名明细的标识）时，处置的结束写与 error 变体的结束写（取记录格式版本不合的那一句，取自记录的各个值都取满截断的上界）都整条写成（不成立时调低会话标识的上限，不另设分支）。不测全部执行中：那要求并发不小于 job 数，在部署侧的并发上限（`stack.py` 的 `DEPLOY_SIDE_MAX_CONCURRENCY`，现为 20；机制四「`max_concurrency` 随 definition 走 + 推进器侧 cap」）之下到不了，测它得出的结论不对应能出现的记录。

两道条件缺一不可：HWM 管 seq 可比的进度回退，投影的每一次写都带它（逐 job 的写为何也要带，见下「② 的 job 级半边落地形态」段）；②管终态：投影不越过 `running`，终态只由以写入序号为条件的写写下一次——后者正是 `scope_done`/`task_exited` 这个边界的关键守卫。这是 [0030](./0030-realtime-persistence-seam.md)「重议」条预告的「进程外多写者需条件更新」的落地（0030 的 Status 头与其「重议」条已回指本 ADR）。

**② 的 job 级半边落地形态（code-health 对抗验证逼出——job 级整体覆盖写曾致：同 HWM 的 stale 投影把已终态 job 刷回 running → 若 run 已结束则读模型永久错乱、且重开机制四的 double-launch 窗口，探针实测 `launched=['a','a']`）**：core 侧 `project` 的 baseline 单调合并是**不充分的缓解**（纯函数管不了跨实例写序），最终守卫必须在 adapter 的写路径，投影写的 job 态不越过 `running`——local 在文件锁内一次读改写：库中 HWM 大于这次投影的 HWM 或 run 已结束即整体不写，否则逐 job 按生命周期序（`_lifecycle_rank`：pending<running<终态）与库中现态取较推进者，投影里的终态按 `running` 比、按 `running` 写（库中已是终态的 job 不被投影改动）；DDB `put_item` 表达不了 per-key 条件，拆两步，先标量、后逐 job：先 `update_item` 条件写标量，只推进 HWM、不写 run 状态，条件是库中 HWM 不大于这次投影的 HWM 且 run 未结束（CCF 即整体 stale，不发逐 job 写）；再对每个 job 用**逐属性** `SET jobs.#sid.status/.session_id/.claimed_at` 做一次条件写（写入的状态同样钳在 `running`），条件是库中 HWM 不大于这次投影的 HWM（与标量一步同一道闸）、库中该 job 当前不比投影更推进、这次写提及的字段（状态，以及投影带了时的会话、认领时刻）至少一项与库中此刻的值不同，且 run 未结束，被挡的单个 job 静默跳过，不区分是哪一项条件挡下的（库中该 job 已更推进、HWM 已被更新的投影越过、run 已结束，这次写都不该落下；内容与库中相同，这次写不必落下；job 不在 Map 里同样 CCF 跳过、不臆造）。「至少一项不同」对可能缺失的属性写成显式的 `attribute_not_exists(jobs.#sid.session_id) OR jobs.#sid.session_id <> :sess`（认领时刻同理），不依赖缺失属性的比较怎样求值。真实的表上核过（嵌套在 `jobs.<scope>.` 下的属性）：属性不存在时 `<>` 与显式形式都判为成立、`=` 判为不成立，属性存在且相等时都不成立；三项都相同时不写、序号不变，库中缺会话与认领时刻而投影带了时写成、序号加一，再发一遍不写，job 不在 Map 里不写；本机测试用的替身（moto）对这些写法给出的结果与真实的表完全相同。逐 job 的写也带 HWM 的条件，因为标量一步之后、逐 job 的各次写之间，HWM 更高的投影可能完成标量写并写下同一个 job 的新值（如执行中 job 的另一个代表会话）；这次投影的逐 job 写若只看等级与 run 未结束，会把旧值写回，留下「库中 HWM 是新的、job 字段来自旧投影」。写入序号挡得住之后以序号为条件的整体替换，挡不住这类不以序号为条件的逐 job 写。库中 HWM 被更高的投影越过之后，这次投影余下的逐 job 写都被这一条挡下。这道条件只分得出 HWM 不同的投影：HWM 是所有 scope 的 worker 段 max seq，而 seq 只在一个 scope 内递增（[0024](./0024-worker-core-protocol.md)「表键设计」条），后读的投影多读到的事件 seq 都不超过先读那次的 HWM 时，两次投影带相同的 HWM，先读那次余下的逐 job 写照样写成，可能把同等级的旧字段写回（如执行中 job 先前的代表会话）。这时库中是先读那次的 job 视图，与下文两步之间的中间态同类。投影把这个 job 记为 `running` 时，这一次写同时把 run 状态写成 `running`，与认领同一种形态（下「run 级状态只进不退」条①）；投影里仍是 `pending` 的 job 的写不涉及 run 状态。两步各自加不加写入序号见 [0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条。两步非原子，但每步各自守卫、先标量后 jobs 的次序保证中间态等价于「携带旧 job 视图的合法投影」，下轮重放收敛。由此 job 被投影记为 `running` 与 run 状态成为 `running` 出自同一次写，没有 run 级领先于 job 级的中间态；不在 job Map 里的 scope 的写被条件挡下，也不写 run 状态；run 在两步之间结束时，后面的逐 job 写因 run 未结束的条件不成立而写不成。顺带：`update_item` 天然不碰未提及属性 → **投影没带的属性一律保留**：`started_at`（create_run 落）不被抹（曾为整 item `put_item` 之疾）；`claimed_at`（只由 `try_claim_job` 落库、事件推演不出）与 `session_id` 也不被抹——故逐属性而非整 entry：曾整 entry 覆盖时一次不带 baseline 的投影就会静默抹掉 `claimed_at`（timeout 起算点丢失），现在正确性不再依赖「调用方总传 baseline」这个调用约定。回归护栏 `core/tests/test_conditional_writes.py`（local/ddb parametrize 对拍）：投影里的终态 job 落成 `running` / 同-HWM 终态不回退 / claim 不回退 / started_at 保留 / 带与不带 baseline 的 claimed_at·session_id 保留 / definition 外 scope 不臆造。逐 job 写的 HWM 条件须有回归护栏（moto 一侧，两步之间的交错只在 DDB 上存在）：一次投影的标量写成功之后，HWM 更高的投影写下同一个执行中 job 的另一个代表会话，前者余下的逐 job 写不改变它。标量一步不写 run 状态、不加写入序号同样由 moto 一侧守：它的请求不带 `status`、`status_group` 与 `write_seq`。**被拒 owner/lease 分布式锁**：0030 曾预告用 lease 保唯一写者——拒，lease 有状态、需续租/故障接管；无状态的 HWM 与写入序号的乐观条件写即够（写失败即重读重算，天然幂等），更轻。

**逐 job 写：内容不变不写，注定不成立的不发（交付物运行成本）**：投影的逐 job 写守三条规则，`RunStore.project_state` 签名不变、不加参数，local adapter 的合并不改。
- **内容与库中相同不写**：即上段条件里的「这次写提及的字段至少一项与库中此刻的值不同」（写法与真实的表上的核对见上段）。条件不成立即不写、写入序号不变，写成才加一（上文②）。
- **这一轮读到的运行态里已是终态的 job 不发写**：推进步骤（`reconcile.tick`）只把 baseline 里未结束的 job 交给 `project_state`。终态条目只写一次、之后不变（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补），对它的逐 job 写条件注定不成立（库中该 job 比投影更推进），跳过不改变结果。两个 adapter 都保留投影没带的 job（DDB 不提及的条目原样保留；local 从库中现态出发、只合并投影带了的 job），对拍口径不变。
- **投影里 pending、没有会话与认领时刻的 job 不发写**：DDB adapter 第二步对投影里 `status` 为 `pending`、`session_id` 与 `claimed_at` 都为空的 job 不发 `update_item`。这类 job 的写只提及状态（`jobs.#sid.status = :pending`，不涉及 run 状态），条件既要求库中该 job 为 `pending`（不比投影更推进），又要求状态与库中不同，两者不能同时成立，写注定被挡下。所以跳过与发出结果相同，依据只在写表达式本身，与调用方是否传 baseline、库中现值如何都无关，上段「正确性不再依赖调用方总传 baseline」照旧成立。判据带上两个字段为空，是为了让「注定不成立」只凭写表达式即可证明：投影一旦带了会话或认领时刻，这次写就可能有效果，照常发出。local 侧的逐 job 合并对这类 job 本就得出库中原值（库中更推进则保留；同为 pending 时空字段回填库中值），而它在锁内把整份状态一次写回，写入次数不随 job 数增长、也没有按请求计的费用，不需要同样跳过；同一输入序列在两个 adapter 上的落库结果仍逐项相等。
- **费用与竞争**：job Map 挂在同一个 STATE item 上。DynamoDB 对 `UpdateItem` 按更新前后整个 item 中较大者计费（每 1 KB 一个写入单位，向上取整；部署的表是按需模式，单位即写请求单位 WRU），只改一个属性也按整项计；条件不成立的写同样计费，按库中现有 item 的大小计、至少 1（官方文档；真实的表上条件不成立的写在响应里不带消耗）。一次投影的写入开销因此约为「发出的逐 job 写的次数乘以 STATE item 的 KB 数」，两个因子都随 job 数增长（条目大小与写成一次的实测消耗见上文②「条目大小」）。省费用的是不发注定不成立的写：并发闸较小时（`max_concurrency` 不给即按 1，见下「`max_concurrency` 随 definition 走」段）job 依次执行，run 前半程的投影里多数 job 仍为 pending、后半程多数已是终态，这两类写全部没有效果却按整项计费；部署到目标环境后这笔费用由交付物长期承担，属于设计约束。「内容与库中相同不写」不省费用：执行中 job 内容不变的写由写成改为条件不成立，计费相同。它省的是竞争：内容不变的写若照样把序号加一，记终态的一方会被这类写挤掉、重读再算。据替身上两个线程固定先后的交错复现（说明竞争的来源，不是频度）：12 个 job 的 run 上，一方每次读运行态之后、整体替换之前另一方落下一次内容不变的投影写，前者 11 次尝试全部被挡、抛出 `RunStateWriteContended`。重读的次数上限维持现值（[0030](./0030-realtime-persistence-seam.md) 决定六「重读的次数有上限」一项）。
- **生命周期序单调不等于字段单调**：投影只约束等级（`pending < running`，不越过 `running`），同等级之间的覆盖照常发生：运行中的 job 在代表会话锁定之前，换台重建后到的 `session_opened` 会把代表会话从一个会话改为另一个（取值优先级见 [0024](./0024-worker-core-protocol.md)「输出」节的会话血缘条）。HWM 条件只挡下 HWM 小于库中值的投影；HWM 相同的两次投影可以出自先后不同的读取，覆盖的一方读到的不一定更新（上「② 的 job 级半边落地形态」段）。所以库中值相对任意一次读到的 baseline 并不是「只会更推进」，下面第一个被拒方案正是建在这个前提上。
- **被拒方案：给 `project_state` 加可选参数 `baseline` 作为减少写入的提示，跳过投影与 baseline 逐字段相同的 job**。并发实例 A 以强一致读取 baseline 之后，实例 B 以不高于 A 的 HWM 写入同等级而字段不同的值（另一个代表会话；B 的 HWM 高于 A 时，A 的写本就被 HWM 条件挡下，跳过与否结果相同）；A 的投影与它的 baseline 相同，于是跳过，库中留下 B 的值，而不跳过时 A 的写会按本次投影覆盖。结果由「以本次投影为准」变成「以 baseline 为准」，写入的语义重新依赖调用方传入的 baseline。强一致读只保证读到读取那一刻的最新值，挡不住读与写之间同等级的覆盖。local 侧若忽略这个参数、照常合并，同一输入序列在两个 adapter 上的落库结果就会不同，`test_conditional_writes.py` 两侧对拍这道回归护栏的前提随之失效。
- **被拒方案：由 reconcile 先算差集、只把有变化的 job 传给 `project_state`**：差集要拿投影与读到的 baseline 比，跳过与 baseline 相同的 job，于是落入上一个被拒方案的前提：并发实例在读与写之间写入同等级而字段不同的值时，结果由「以本次投影为准」变成「以 baseline 为准」。
- **上面三条规则不落入这两条被拒方案的前提**：「内容与库中相同不写」比较的是写那一刻库中的值，不是 baseline：并发实例在读与写之间写入同等级而字段不同的值时，这次写照样落下、按本次投影覆盖，「以本次投影为准」不变；已是终态的 job 不发写，靠的是终态不可变（baseline 里的终态在库中此后仍是那个终态），不是「与 baseline 相同」；pending 一类的跳过只凭写表达式。
- **被拒方案：投影写一律加写入序号**（内容不变的写也加）：记终态的一方被内容不变的写挤掉重读（上「费用与竞争」条的复现），挡下它的写并没有可被整体替换盖掉的内容。
- **被拒方案：只调高重读的次数上限或加长退避**：不去掉竞争的来源，只拉长调用时长、多出读写。
- **回归护栏**：`core/tests/test_conditional_writes.py` 的两侧对拍：投影 job 为 pending 且无会话、无认领时刻，库中该 job 分别为 pending、已 claim 的 running、终态、不在 Map 里，两个 adapter 的落库结果都等于投影前库中该 job 的值（不在 Map 里时仍不在）；并发实例在读与写之间写入同等级而字段不同的值之后，本次投影照样落下。DDB 侧（moto）：内容与库中相同的投影之后写入序号不变；库中缺会话、认领时刻而投影带了时写成、序号加一；上面那条两线程反例在重读的次数之内提交成功；标量写成功的前提下一次 `project_state` 发出的 `update_item` 次数为标量写一次加未跳过的 job 数（标量写条件不成立时直接返回 False、不发逐 job 写，单列一例断言次数为一）。推进步骤一侧（`core/tests/test_reconcile.py`）：baseline 里已是终态的 job 不交给 `project_state`。

**投影写的 run 状态按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法给出**：run 的状态字段没有自己的写入逻辑，每次改变 job 状态的写在同一次写里按取法写 run 状态。投影写不越过 `running`，所以它写下的 run 状态只会是 `running`：把一个 job 写成 `running` 的写之后（库中这个 job 原是 `pending` 或 `running`），这个 job 未结束、也不是 `pending`，取法给出 `running`；没有把任何 job 写成 `running` 的投影（投影里全部仍为 `pending`，或离开 `pending` 的 job 在库中都已是终态）不改变任何 job 的状态，也就不写 run 状态、库中值原样留下（库中值是 `create_run` 落的 `pending`，或此前某次认领、投影写下的 `running`，见下「run 级状态只进不退」条）。这两条都是取法的推论，不是另立的规则；run 的终态只随记下最后一个 job 终态的写或结束写写下（上文②）。投影不对整份 jobs 重算取法：全部 job 都已是终态而 run 未结束的记录（只会出自端口之外的改动）上，重算会写下没有结束时刻的终态。所以两端的落法都是「这次投影把某个 job 写成 `running` 时，同一次写把 run 状态写成 `running`，否则不写」，不对整份 jobs 重算取法：DDB 在把 job 写成 `running` 的那一次逐 job 写里同时写 run 状态（上文「② 的 job 级半边落地形态」段），local 在锁内一次写回时按同一条决定写不写（上文②）。两端都不看投影传入的 run 级值，同一调用顺序下落库结果相同；零个 job、投影里全部仍为 `pending`、投影里离开 `pending` 的 job 在库中都已是终态这三种情形，两端写下的 run 状态都与库中原值相同。run 已结束时投影写不成立（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。

**run 级状态只进不退：job 离开 pending 的那一次写，使未结束的 run 已是 `running`**：
- **规则**：由 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法推出——任何把一个 job 从 `pending` 写成 `running` 或终态的写，在同一次写里按取法写 run 状态，未结束的 run 由此已是 `running`；此后 run 状态只走向终态、不退回 `pending`。run 由此与 job 同一生命周期序（`pending < running < 终态`），在 run 级守两段：`running` 不退回 `pending`、终态之后不再有写。本条承重的只有一个方向：由规则的逆否，对未结束的 run，读到 run 级 `pending` 即没有有效 job（在该 run 的 job Map 里的 job）离开 `pending`。
- **动因**：run 状态若不随 job 离开 pending 的那一次写落下，`list-runs` 的状态列与 job 列矛盾（云端一次实测读到 run 级 `pending` 而 job 已 `running`，[0041](./0041-agent-facing-cli-affordances.md) 决策七实测项），`--status running` 漏列、`--status pending` 多列，0041 决策七「CLI 的合并」依赖的「run 只从 pending 走向 running」在写级不成立；拿认领之前读到的 baseline 写全 pending 投影的并发实例，还会把已写成 `running` 的 run 级改回 `pending`（认领不改 HWM，同 HWM 或更高 HWM 都过得了 HWM 守卫；local 与 moto 两个 adapter 上都复现：认领后再写一份全 pending、同 HWM 的投影，run 级回到 `pending` 而 job 仍为 `running`）。
- **① 认领 `try_claim_job`**：一条条件写同时置 job 与 run 状态。DDB 为 `SET jobs.#sid.#st = :running, #st = :running, #cc = if_not_exists(#cc, :zero) + :one[, jobs.#sid.claimed_at = :ca]`（顶层 `#st` 与 `jobs.#sid.#st` 路径不重叠，同一更新表达式可同时写），写入序号同样加一（上文②），条件 `jobs.#sid.#st = :pending AND #st IN (:pending, :running)`；local 在跨进程文件锁内判同样两个条件、一次写回。`#cc` 是认领计数：认领成功时在同一次写里加一、缺属性按 0 起算，认领失败不改它；它只作 `status --json` 的诊断键（成功认领的次数），不作任何写的条件。条件不成立返回 False、本次不起 task：已被别的推进器抢走、job 不在 Map 里、run 已结束三种原因不区分，三种都不该由这次认领起 task（STATE 不存在时同样返回 False）。一次写；HWM 不变。这条条件给出的承诺是：**run 已结束后不再接受新认领；此前已成功的认领不由此条件撤销**。本机只有持锁的推进器认领，这条条件在本机只作防御，在云端多次调用重叠时起作用（机制四）。
  - **task 的启动不随记录分出先后**：认领与启动 task 是分开的两步（tick 在认领成功之后才调 `launcher.launch`），认领成功之后、启动调用完成之前 run 被结束时（到期的结束写、处置、后端到期结束），task 仍会启动；之后由谁停它、什么情形下没有人停，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」里「run 到终态之后各组合下还会发生什么」表的「检查已通过、启动还没有完成的 job」一行。已落定的记录不受它影响：在途实例本轮的写在 run 结束之后都不成立（0054 决策五），它存下的明细不被点名（[0030](./0030-realtime-persistence-seam.md) 决定三）；此后读到既有终态的 tick 不再推演这个 task 的事件与退出记录（端到端 cloud 4. 的闸与下「④ tick 的完成语义」）。不为这一交错另加保护：启动前再读一次 run 状态，读与启动之间同样可能插入结束，挡不住；要原子地挡住，须把认领与启动合成一次不可分的操作，而启动是对外部平台（ECS RunTask、本机起进程）的调用，不能纳入 store 的条件写。
  - 前台执行在每个 job 第一次起 worker 之前做同一个认领（经落库服务，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）：认领被拒即发现 run 已被别处记为已结束，这个 job 不启动、在跑的 job 被停下；认领与起 worker 之间同样不可原子化，留下的窗口见 0054「边界与已知局限」。
- **② 投影 `project_state`**：run 状态的取值见上「投影写的 run 状态」段；DDB 的两步写法、各步的条件、run 状态随哪一次写写下见上文「② 的 job 级半边落地形态」段，写入序号见 [0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条；local 在锁内按整份运行态一次写回（上文②）。投影不越过 `running`、不写 job 终态；HWM 的含义是已处理的 worker 段 max seq。
- **③ 前台的 job 状态写：执行中的 `update_job_state` 与终态的 `commit_job_states`**（[0030](./0030-realtime-persistence-seam.md) 决定三、四）：执行中的写只写 `running`，终态写只写终态，两者写入的 job 态都不是 `pending`，都连同 run 状态一起写，取值按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三。条件：STATE 存在且 run 未结束（`attribute_exists(run_id) AND #st IN (:pending, :running)`）；`update_job_state` 另以库中有这个 job 且它未结束为条件（`jobs.#sid.#st IN (:pending, :running)`，与 run 的条件在同一次 `update_item` 里），库中已是终态或不在 Map 里的 job 不被它写下，run 仍未结束时照样返回 True（[0030](./0030-realtime-persistence-seam.md) 决定四）；记下 job 终态的写（`commit_job_states`）另以写入序号为条件（上文②）。run 已结束时写不成立（`update_job_state` 返回 False，`commit_job_states` 返回 `ALREADY_ENDED`）：调用方据此发现 run 已被别处记为已结束、发出停手信号（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）；STATE 不存在时转 `FileNotFoundError`。local 在同一次读改写里判（在文件锁内，与建 run 之后的其它写入口互斥，0054 决策五），返回值取锁内读到的 run 状态。判据是「写入的 job 态非 pending」：前台起 worker 的 job 先经①的认领离开 `pending`（0054 决策五），此后的写是 `running` 或终态；没有启动的 job 不经这两个入口，由结束写结束（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。每次非 pending 的写都带 run 状态、不在调用方记「是否第一次」：规则落在 adapter 的写表达式里，调用方无需额外状态。前台推进器被强制结束或宿主失联时，留下的 run 停在 `running`（已有 job 离开 pending 的）或 `pending`（还没有的），只能由处置方结束（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、七；本机没有常驻的处置方，见 0054 决策八）。
- **④ tick 的完成语义**（core `reconcile.tick`，结果就是 `reconcile.TickOutcome`，不交回判定明细）：tick 先读库中运行态（baseline），run 已是终态即停止推演，不投影、不认领、不存明细、不读事件。tick 的结果区分三种——**继续推进**（`CONTINUE`）、**这一方的写使 run 成为终态**（`COMMITTED`）、**run 已结束而使它成为终态的不是这一方**（`ENDED`：读到既有终态，或这一方的写因 run 已被别处结束而写不成：终态写返回 `ALREADY_ENDED`，或到期的结束写未写成、重读到终态）。后两种都让宿主结束对这个 run 的推进（本机循环退出、后台推进进程随之退出；云端这次调用当场清扫，`COMMITTED` 在生成报告之后，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条）；只有 `COMMITTED` 触发报告生成，报告从记录生成（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」），明细由宿主按运行态里点名的标识读回，推进步骤不交回明细：这一次推进交给终态写的明细里可能有终态由别的推进方写下、这次写跳过的 job，按标识读回才与记录一致；新增的读只有使 run 成为终态的那一次推进写下终态的 job（至多为并发上限个），较早轮次写下终态的本来就要读回。到期的结束写因写下时有执行中的 job 而未写成、重读到 run 仍未结束时返回继续推进；终态写在 run 未结束时写成，或抛错不写（云端重读的次数用尽、超出单条记录的大小上限，见下「收尾各步的先后与之后会不会变」第 6 步与 [0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条），不返回未写成。区分三种而不是返回一个布尔值：宿主要知道这一轮是不是由自己使 run 成为终态（只有这一方生成报告），也要知道 run 已被别处结束、该停止推进；本机循环能结束靠的是 tick 返回「run 已结束」，不依赖哪些写者存在。读序：先读 baseline 再读事件，已结束时省掉全量事件读；插在两次读之间的认领不在 baseline 里：认领在同一次写里写下 `running` 与认领时刻，所以这个 job 在 baseline 与决策用的运行态里都是 `pending`、不带认领时刻，本轮不为它存明细、不写终态（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「快照」），只多提议一次被认领条件挡下的 start；已过停止认领的时刻、又没有别的执行中的 job 时，还多一次写不成的到期结束写（写下时库中它是 `running`），重读之后返回继续推进；插在两次读之间的事件只让本轮推演比 baseline 更新，按生命周期序合并照常。读到 baseline 之后才插入的终态不在判停之内：本轮的写在 run 结束之后都不成立（0054 决策五），本轮返回哪种结果见下「收尾各步的先后与之后会不会变」的步骤。
  - **为何放在 tick、不放在宿主**：宿主在调 tick 之前另读一次 run 级，检查与 tick 读 baseline 之间插入的终态只有 tick 自己的读看得到；放在 tick 里，判停用的就是本轮推演所用的同一份 baseline，不另加读，两个宿主共用一份判据（报告收尾曾在两个宿主各写一份、后合并进 core `reconcile.write_report_from_record`，同一理由）。云端各入口共用的闸保留：它判在读 definition 之前，省掉强一致读 META 与取回 jobs 对象的那次 S3 请求，tick 内的判停管不到这一段。
  - **代价**：使 run 成为终态的一方在这次写之后、生成报告之前中断时，RunReport 缺失，别的一方不补写。这与上文端到端 cloud 4.「明确接受的代价」是同一取舍（报告是派生产物，宁缺不错），本机同样适用。同一类还有云端条件写的响应丢失：终态写或结束写已在服务端生效，响应没有回到这一方，SDK 重发时被写入序号的条件挡下，adapter 重读到终态，按 run 已被别处结束返回（终态写为 `ALREADY_ENDED`，结束写为未写成）；这一方返回 `ENDED`、不生成报告，没有一方得知自己使 run 成为终态，报告缺失。本机在锁内一次读改写，没有这一情形。
  - **收尾各步的先后与之后会不会变**（后台推进的步骤、必要契约、已获接受的边界，以及字段定义与读取规则的出处；别处写这些时引用本条的步骤、K1 到 K3 或下列出处，不另写概括；逐 job 的写序只在 [0030](./0030-realtime-persistence-seam.md) 决定三写全）：
    - **步骤**。主体都是这一轮推进（一次 `reconcile.tick`）。别的推进器或处置方可以落在任意两步之间，各记录之间的先后见本节开头，本条不另作概括。
      1. 取时刻，读运行态（`load_run_state`）。读不到运行态即返回继续推进（`CONTINUE`），不读事件、不写任何东西：这一轮的认领、投影与结束写都写不成，终态写会报错。本次读到终态即返回「run 已结束」（`TickOutcome.ENDED`），读到之后不再读事件、投影、认领，也不存明细。
      2. 读事件（`EventLog.records`），推演、投影写（投影只前进、不越过 `running`、不写 job 终态）。
      3. 写下这一轮已有结果的各 job 的终态，按 [0030](./0030-realtime-persistence-seam.md) 决定三的逐 job 写序（这一轮的快照要满足的条件见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「快照」）。这一轮可以写终态的 job 合成一次终态写（[0030](./0030-realtime-persistence-seam.md) 决定四；云端每次写按整个 STATE 条目计费）：每个 job 各生成一个标识、存下一份明细，这次终态写点名各自的那一份；云端被写入序号挡下、重读再算时用的仍是这组终态与标识（[0030](./0030-realtime-persistence-seam.md) 决定三「被点名的那一份」条）。其中任一份明细存不成即原样抛出，这一遍（从读运行态起算；同一轮的重做是另一遍，见第 4 步）一个终态都不写、也不认领与做结束写，这一遍已存下明细的 job 一并留在 `running`、存下的那几份不被点名，下一轮重存再写（本机按 [0030](./0030-realtime-persistence-seam.md) 决定三「保存明细失败」条重试，用尽即退出）。重做那一遍存不成时，第一遍已写下的终态与已做的认领不收回：终态只写一次，没有调用方依赖「抛出即什么都没有推进」。这次写使 run 成为终态即第 5 步，run 已被别处结束即第 6 步。
      4. 推进决策（`plan_next`）在这一轮读到的运行态加上第 3 步终态写的作用（`run_status.commit_applied`）上作出，jobs 按运行定义的次序排列（机制四）：认领并启动 job，或满足 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 3 条时做到期的结束写（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。有认领因已过停止认领的时刻而没有做时，这一轮从上面第 1 项起重做一次，按已过停止认领再决策（只重做一次，见 `tick` 的 docstring）；第一遍记下的终态已在重新读到的运行态里，不再存、再写。先写终态、后决策的理由：决策只有一处、只看一份状态，即这一轮读到的运行态加上这一轮终态写的作用，最后一个执行中的 job 得出结果的那一轮就能判出「没有执行中的 job」、腾出它占的并发位，不必等下一次触发；判定存储写不进的那一轮不启动新的 job。代价是启动下一个 job 要等这一轮的保存与终态写做完。
      5. 这一方的写使 run 成为终态：返回 `COMMITTED`；宿主（本机 `detached.run_reconcile_loop`，云端 `_tick_runs`）从记录生成报告（`reconcile.write_report_from_record(meta, run_store, result_store, report_store, created_at=…)`：读运行态、按点名的标识读回明细、组装 RunResult、写报告，整段在失败隔离之内，[0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条），随后结束对这个 run 的推进。
      6. 这一方的写没有使 run 成为终态。终态写返回 `ALREADY_ENDED`：run 已被别处结束，返回「run 已结束」（`ENDED`），不另读。到期的结束写返回未写成：重读运行态，已结束返回 `ENDED`，未结束（写下时有执行中的 job）返回继续推进（`CONTINUE`）。返回 `ENDED` 时宿主不生成报告、结束对这个 run 的推进。云端这两个写入口重读再算的次数用尽时抛错、不写（[0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条），这一轮按写不进运行态失败。其余情形同样返回继续推进，云端宿主随后做防御扫（「job timeout」节 `JobState.claimed_at` 条②），宿主等下一轮。

      云端宿主在调用推进步骤之前先过后端各入口共用的闸（上文端到端 cloud 4.，各分支只在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时」一段写全）：运行态不存在或已结束即不调用、只清扫，读不出即记日志、不调用，run 由别的格式写出或运行定义不可用即做 error 变体、不调用（下「不经推进步骤的收尾」）。
    - **必要契约**（别处引用时写编号）：
      - **K1**。对象：一个 run 的运行态（run 的 `status`、`message`、`ended_at` 与各 job 的记录）。内容：run 经端口的写入口成为终态之后不再改变。前提：写入经端口的写入口（规则与理由在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五，端口的写入口在 [0030](./0030-realtime-persistence-seam.md) 决定四）；不含绕过端口直接改存储。依赖方：`status`、`list-runs` 与 `status --wait` 把读到的终态当作定论（判定退出码、处置时不动已结束的 run），前台执行者据 job 写的返回值停手（上文③），K2。现有用例（断言的是现在 code 的写法，实装时随写法一起改），都在本机文件与 moto 两个 adapter 上对拍：`core/tests/test_ending_and_commit_writes.py`（`test_only_the_first_of_two_end_runs_lands`、`test_end_run_on_an_ended_run_changes_nothing`）；`core/tests/test_conditional_writes.py`（`test_claim_rejected_on_finalized_run_leaves_state_unchanged`、`test_writes_rejected_by_the_ended_run_alone`、`test_finalized_run_keeps_message_against_later_projection_and_claim`、`test_create_run_on_an_existing_run_fails_and_changes_nothing`）；本条实测项 4（真 DDB，断言留在 `core/tests/test_cloud_integration.py`）。
      - **K2**。对象：RunReport 里的 run 状态与各 job 判定。内容：出自记录（运行态与各 job 被点名的明细），由使 run 成为终态的写入方在这次写之后生成。前提：后台推进的报告只由收到 `COMMITTED` 的宿主生成；run 到终态之后运行态与被点名的明细都不再变（K1、[0030](./0030-realtime-persistence-seam.md) 决定三）。依赖方：读报告的人与 CI，报告与 `status`、`explain` 一致（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」）。现有用例（断言的是现在 code 的写法，实装时随写法一起改）：`core/tests/test_reconcile.py`（`test_commit_lost_to_another_advancer_ends_without_a_result`）；`runtime/tests/test_detached_launcher.py`（`test_loop_ends_without_report_when_its_commit_is_lost`、`test_loop_does_not_rewrite_the_report_of_a_committed_run`）；`deploy_aws/tests/test_lambda_handlers.py`（`test_tick_runs_branches_on_tick_outcome`）。
      - **K3**。对象：一个 job 的判定明细保存与它的终态写。内容：保存失败时这个 job 这次不写终态。前提：无额外前提，推进步骤的判定存储是必传的，两个宿主都装配它。依赖方：读到由执行结果结束的 job 的终态即取用它点名的明细的读者（[0030](./0030-realtime-persistence-seam.md) 决定三）；保存失败之后的重试与处理见 0030 决定三。现有用例（断言的是现在 code 的写法，实装时随写法一起改）：`core/tests/test_reconcile.py`（`test_verdict_write_failure_fails_tick_before_commit_and_retry_heals`、`test_later_verdict_write_failure_leaves_the_run_uncommitted`）。

      报告只由使 run 成为终态的一方生成，规则在 [0027](./0027-runreport-aggregation-index.md)，不列为本条的契约。
    - **已获接受的边界**（只列出处，内容以出处为准）：
      - 重叠推进时退出记录与终态的不一致：本节开头列表的「退出记录」一条。
      - 终态写之后的中断：上文端到端 cloud 4. 标着「**明确接受的代价**」的一句；本机的同一取舍见上文④的「代价」一条。
      - 报告写入的失败隔离：上文「数据模型三件套」表 RunReport 一行。
      - 不经推进步骤的收尾：下面这一条。
    - 不经推进步骤的收尾：云端推进器读不到可用的运行定义时（记录格式版本不是后端的、定义违约、缺任务定义修订、运行定义记下的 worker 协议版本不是后端的，以及提交记录已被删去或它的 jobs 对象已不在；各分支见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时」一段）不经推进步骤，直接做结束写的 error 变体。jobs 对象已不在凭哪种错误认出、取回时别的错误怎样处理，见 [0030](./0030-realtime-persistence-seam.md) 决定六「jobs 对象取不到时」一项。error 变体只写运行态的公共部分：每个未结束的 job 记 `error`，run 随之为 `error`（写法与几种原因的说法见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节），这一写不存明细、不点名。这一写之后不生成报告：报告按运行定义逐个列出 job（[0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条），读不到运行定义就组装不出。run 级说明从 `list-runs` 看得到，`status` 能显示这个 run 时也看得到（别的格式写出的 run，只有记录格式版本与它相同的命令行工具的 `status` 能显示，记录格式版本不同的 `list-runs` 按公共部分列出它，[0037](./0037-distribution-and-packaging.md) 决策 7「后端遇到别的格式写出的 run」的「此后」条）。这一写只由云端推进器做，它每次调用都从记录读回运行定义；本机的两个推进器（前台 `run` 的进程、`submit` 启动的后台推进进程）推进用的是自己生成的那份、不从记录读回（上文 local 一节），没有这一情形。只读的查询命令读不到运行定义时以退出码 2 结束、不写（0037 决策 7）；处置方读到记录格式版本与本机不同的 run 时不处置（给出 `other_version`），提交记录不存在或内容不合法时只剩试拿锁一条（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、八），云端用户一侧的处置方取不到 jobs 对象时不处置（两侧怎样归类及理由见 0030 决定六「jobs 对象取不到时」一项），都不做这一写。理由：读不懂运行定义的一方未必是这个 run 的推进器，读不懂可能只因为它的记录格式版本与写出这份记录的不同，这个 run 的推进器可能仍在正常推进。到期的结束写在一个 job 都没有启动时同样没有任何明细，报告照常由使 run 成为终态的一方生成（[0027](./0027-runreport-aggregation-index.md)）。
    - **字段定义与读取规则**（不在本条转述）：`artifacts` 各键何时出现、表示什么，以 [`docs/internals/cli-json-contract.md`](../internals/cli-json-contract.md) 的字段表为唯一出处（`run --json` 一节的 `artifacts` 与 `report_index` 两行、`status --json` 一节的 `artifacts` 一行）；`explain` 读什么、何时给哪句提示，以 [0042](./0042-step-evidence-and-explain.md) 决策四为出处。
  - **回归护栏**：baseline 已结束时 tick 返回「run 已结束」（`ENDED`，读到既有终态），不调 launcher、不写 result_store、不发投影写、不读事件；终态紧接在读 baseline 之后（本轮投影写之前）插入时本轮的写都不成立、不起 task，下一轮读到既有终态、返回「run 已结束」（以上 `core/tests/test_reconcile.py`）；本机循环对已结束的 run 结束且不生成报告，对已提交终态、事件完整的 run 也不重写报告（`runtime/tests/test_detached_launcher.py`）；终态写因 run 已被别处结束而写不成时返回「run 已结束」、不生成报告（core 与 runtime 两侧）；云端 `_tick_runs` 三种结果各自的处理由替身 tick 守（`deploy_aws/tests/test_lambda_handlers.py`：真实 handler 先过闸，只有竞争交错才走到「run 已结束」这一支）。直接断言 tick 返回值或用替身替换 tick 的测试（`core/tests/test_reconcile.py`、`core/tests/test_cloud_reconcile.py`、`deploy_aws/tests/test_lambda_handlers.py`）都按三种结果断言。
- **三个失败形态各自的解法**：
  - **终态被复活**：认领若不带「run 未结束」的条件，会把已结束的 run 改回 `running` 并起 task。保护放在认领的同一条条件写里（run 状态为 `pending` 或 `running`），把「已结束的 run 不再接受新认领」从 handler 的先读后判（见上端到端 cloud 4. 的闸）补成写级保证，并由「run 到终态之后运行态的任何写都不成立」（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）推广到每个写入口；此前已成功的认领不由它撤销（见上①）。
  - **旧投影撤销**：由②「全 pending 不写 run 级」解决，不改 HWM 守卫、不改 run 未结束的条件，也不借 HWM 表示认领（见下被拒方案）。
  - **run 在两次写之间结束**：每一处 run 级 `running` 写都在同一条写的条件里带 `#st IN (:pending, :running)`——①是一条写；②的 run 级只在把 job 写成 `running` 的那次逐 job 写里，这次写带同一条件（上文「② 的 job 级半边落地形态」段）；③是一次写、带同一条件。本机建 run 之后的各写入口都在同一把文件锁内一次完成，没有「两次写之间」；③写不成时前台执行者据返回值发出停手信号（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。
- **两端对拍口径**：相同初态、合法输入、按同一调用顺序逐个调用完成之后，两个 adapter 的落库结果逐项相等，含 run 级。口径不扩成任意并发交错或部分失败下的原子等价：DDB 投影两阶段之间的中间态、逐 job 写失败后等待重试的状态都不在对拍之内。`core/tests/test_conditional_writes.py` 的两侧参数化覆盖：认领成功后 run 级为 `running`；认领不存在的 job 失败、run 级不变；run 级已是 `running` 时再认领另一个 pending job 成功；已结束的 run 上认领返回 False，run 级、`ended_at`、`message`、job 态与 `claimed_at` 都不变；认领之后再写全 pending、同 HWM 与更高 HWM 的投影，run 级仍为 `running`、HWM 按条件前进；全 pending 投影写在全 pending 的库上，run 级仍为 `pending`；零个 job 的 run 上的投影、投影里离开 `pending` 的 job 在库中都已是终态时，run 级与库中原值相同；投影里的终态 job 落成 `running`。前台实时写同一文件另有参数化对拍：`running` 的 job 写之后 run 级为 `running`；未建记录时写 job 报错；返回值在 run 未结束时为 True、已结束时为 False；写入 `pending` 或终态是参数错误；库中已是终态的 job 不被它改写、不在 Map 里的 job 不被它写下，返回值照样按 run 给出（两侧对拍在 `core/tests/test_ending_and_commit_writes.py`）。DDB 侧另断言 run 未结束时 `update_job_state` 发出一次 `update_item`；投影的写入次数见上「逐 job 写：内容不变不写，注定不成立的不发」段的回归护栏。同一文件另对拍：对已有的 run 再建被拒、不改任何东西；认领计数建 run 时为 0、只在认领成功时加一，其它写入口不改它，缺键读作 0；本机各写入口之后顶层附加键原样保留（[0030](./0030-realtime-persistence-seam.md) 决定四「改写运行态时原样保留不认识的部分」条的 local 一项）。终态不可变与写入序号的规则（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五、上文②）的两侧对拍须覆盖：run 已结束时写 job 写不成、运行态不变，DDB 侧同样只发一次 `update_item`；云端改变了整体替换所写内容的写把写入序号加一、内容不变的投影写不加，以序号为条件的终态写与结束写只在库中序号等于读到的值时写成，读之后落下的、改变了这些内容的写挡住它（moto 一侧，`core/tests/test_ddb_write_seq.py`；本机由锁内按整份运行态计算，同一调用顺序下两端落库结果相同，两端对拍在 `core/tests/test_ending_and_commit_writes.py`）。
- **对 `list-runs` 的影响**：0041 决策七「CLI 的合并」依据「run 只从 `live` 分组走向终态分组」：runs 表用状态分组索引（[0030](./0030-realtime-persistence-seam.md) 决定六），非终态 run 同在一个 `live` 分组，`pending` 到 `running` 的换值不改变成员资格；终态不被改写、端口没有整体覆盖运行态的写（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。GSI 成员资格的传播边界见 0041 决策七。
- **成本**：本条不增加基表写入：run 状态随认领、投影与前台 job 写在同一次写里写下，写入序号与认领计数同样随这些写落下（条件不成立的写同样按 item 大小计费，见上「逐 job 写：内容不变不写，注定不成立的不发」段）。记下 job 终态的写与结束写在写之前各有一次强一致读整个 STATE（读量按 item 大小计），条件不成立时每次重读再算多一次读与一次写（②）。索引写：在 run 未结束期间，至少一个有效 job 离开 `pending` 的 run，其 `pending` 到 `running` 的换值恰一次；在任何 job 离开 `pending` 之前由结束写结束的 run 没有这次换值；能保证的只是至多一次。这次换值在以 `status` 为分区键的 GSI 上会让每个索引各多一次删旧项与写新项；runs 表用状态分组索引（[0030](./0030-realtime-persistence-seam.md) 决定六），换值不改变索引键与投影属性，按官方的 GSI 写入规则不产生索引写（已在部署出的索引上实测：认领、前台 job 写与把 run 级写成 `running` 的投影对它都计 0，[0038](./0038-worker-image-delivery.md) 实测项 8），一个 run 的索引写只有建 run 与成为终态时换分组。run 级已是 `running` 时的同值写不改变索引键与投影属性，不产生索引写：已在真 DDB 上核过，含经 adapter 的认领、前台 job 写与两种投影（见实测项 6）。**对 worker revision 清理的影响**：清理的引用检查读状态分组索引的 `live` 分组（[0038](./0038-worker-image-delivery.md)「不变量」清理 pass 条），`pending` 到 `running` 的换值不改变分组，不产生换键的间隙；以 `status` 为索引键时，换值时索引删旧项与写新项哪个先可见没有承诺，按 `pending`、`running` 两个分区查询的清理可能两次都落在间隙里、漏掉这个 run，进而注销它在用的 revision。新建 run 的索引项须在静默期之内可见；`gherkai:retired-at` 表示 revision 从何时起不被任何映射引用、静默期一律从它起算。协议的细节与剩余的风险见 0038 该条。
- **被拒方案**：
  - **读侧归一**（`status` / `list-runs` 读到 run 级 `pending` 而有 job 非 pending 时显示 `running`）：即读取时派生状态，拒绝的理由见 [0030](./0030-realtime-persistence-seam.md) 决定三被拒方案「读取时派生状态」。
  - **借 HWM 表示认领**（认领时抬高 HWM，让认领之前的旧投影被挡）：会挡下合法的投影：`task_exited` 没有数值 seq（机制一），被退出记录触发的投影携带的 HWM 与认领前相同，被抬高的 HWM 挡下。此外 HWM 的含义从「已处理的 worker 段 max seq」被污染为兼作认领标记，两个量被混成一个。
  - **维持现状**（run 状态等下一次投影才换成 `running`，把认领后的这段时间当诊断窗口接受）：`list-runs` 的过滤与 0041 决策七的合并在这段时间里都会出错，并发旧投影的回退也不随首个事件消失，不是会自愈的窗口。
  - **把认领结果并入本次投影**（tick 认领成功之后，把该 job 的 `running` 合进内存中的投影、再写一次投影）：这样做不必新增读库；拒绝的理由在写入本身。认领与补写投影是两次写，两次之间读到的仍是「job 已 running、run 级 pending」，补写之前中断则这一状态留到下一次投影；每次成功认领多一次写，按 STATE item 大小计费；它只改本实例的这一次投影，挡不住别的实例拿认领之前的 baseline 写出的旧投影把 run 级写回 `pending`（那仍要靠②）。认领写自身连同 run 级一起写，一次写同时消除窗口与中断残留。
  - **投影全 pending 时在标量那一步写 run 级 `pending`，以 `#st = :pending` 为条件**：条件不成立时整次被挡，HWM 也写不进去，返回 False 多出第三种含义（stale、已收尾之外又加「已 running」）。标量那一步只推进 HWM、不写 run 状态（上文「② 的 job 级半边落地形态」段），不改条件，也不多出一次被挡而计费的写。
  - **由 `RunPersistence` 在第一个 job 离开 pending 时另调一次「标记 run 运行中」**：两次写之间要么现出被禁止的一侧（先写 job），要么在调用方另记「是否第一次」并给端口加一个方法；规则放在 adapter 的写表达式里，所有调用方一致得到保证。
  - **`begin` 时就把 run 级写成 `running`**：run 级 `pending` 在两条路径上的含义（还没有 job 离开 pending）就此分叉，前台刚建记录、worker 还没起来的 run 也读作已在执行。
- **实测项**（真实环境执行，均已核）：
  1. 本机前台 `run`（已核）：run 建立后 `list-runs` 读到 run 级 `pending`、job `pending`；第一个 job 离开 pending 后，run 级与 job 同为 `running`，直到结束转为 `passed`。
  2. 前台 `run` 执行中被 SIGKILL。本机（已核）：留下的 run 停在 `running`、job `running`、不带 detached 标记，`list-runs` 按非终态列出，`--status running` 列出它、`--status pending` 为空，`status` 同样显示 `running`。
  3. 云端 `submit`（已核）：提交一个两 job 的 run，从提交起以强一致读连续读 STATE 直到收尾（约两百次）。第一个 job 被认领的那一次读，run 级已是 `running`，此时 job 带认领时刻而还没有会话，另一个 job 仍 `pending`；全程没有读到 run 级 `pending` 而某个 job 已不是 `pending` 的组合；收尾为 `passed`。本机 `submit` 的对应观察：提交后第一次读清单，run 级已是 `running` 而两个 job 一个 `running`、一个仍 `pending`。
  4. 终态不被复活（已核）：真 DDB 上对带 pending job 的已收尾（error）run 调认领，返回 False，整份运行态（run 级、结束时刻、原因、job 态与认领时刻）读回与调用前相同。这些断言作为真 DDB 集成用例留在 `core/tests/test_cloud_integration.py`。
  5. 并发旧投影不回退（已核）：真 DDB 上认领之后写全 pending、同 HWM 与更高 HWM 的投影，run 级保持 `running`，HWM 按条件前进，已认领的 job 仍为 `running`（同为集成用例）。
  6. 同值写不产生索引写（已核）。在与 runs 表键结构及两个索引定义相同的按需临时表上以 `ReturnConsumedCapacity=INDEXES` 取每次更新的写入消耗，按「基表／两个索引」记录。
     - 直接构造的三种写形态：只改 jobs（run 级仍为 `pending`）为 1.0／0／0；run 级 `pending` 到 `running` 并改 jobs 为 1.0／2.0／2.0；run 级写同值 `running` 并改 jobs 为 1.0／0／0。
     - 经 adapter 的真实调用：第一次认领（run 级由 `pending` 换为 `running`）为 1.0／2.0／2.0；run 级已是 `running` 时再认领一个 job、前台 `update_job_state`、全 pending 的投影（只推进 HWM）、非全 pending 的投影（实测时标量写同值 `running`，逐 job 写）每次更新都是 1.0／0／0；收尾换值为 1.0／2.0／2.0。
     - 由此，同值写不产生索引写，换值时每个索引一次删旧项加一次写新项（各 2.0），与上「成本」所依的计费规则一致。

### 机制四：CAS(pending→running) 控严格并发

严格 `max_concurrency` 的执行点从 core 内 `ThreadPoolExecutor`（进程内、无 store）**迁到 store 的 CAS 条件写**：起一个 job 前 `CAS(status: pending→running)`，云端多次调用重叠、看到同一 pending job 都想启时，**只有条件写成功的那个去 RunTask**，其余被拒跳过；本机只有持锁的推进器认领（「推进器与触发源」第 1 条），这条条件写在本机只作防御。同一条条件写还断言 run 未结束、并使 run 状态随之为 `running`（机制三「run 级状态只进不退」条①）：run 已结束后不再接受新认领；此前已成功的认领不由此撤销（认领与启动 task 分两步，结束可能插在中间）。稳态并发恒 = max_concurrency，不靠任何常驻进程 hold 线程池。core 的 `plan_next` 只**提议**动作，真正的并发闸是 adapter 的 CAS。**提议按运行定义的次序取 pending 的前缀**：重叠的调用读到同一段 pending 时提议的是同一批 job，在认领条件上相撞、只有一方写成，并发才不超过上限；运行态里 jobs 的次序取决于存储（DynamoDB 的 Map 不保证次序，本机 JSON 与 moto 保留插入次序，单测照不出差别），按它取前缀时两个重叠的调用会各认领一个不同的 job。所以推进步骤把交给 `plan_next` 的运行态按运行定义的次序重排，不依赖存储给出的次序。

**`max_concurrency` 随 definition 走 + 推进器侧 cap**：`RunMeta.max_concurrency` 是 definition 的一部分（载体惯例同 `extra_http_headers`：run 级执行参数、无值为 null——必有键，[0037](./0037-distribution-and-packaging.md) 决策 7——core 只搬运不消费、消费者是各组合根），`run`/`submit` 都落值。推进器侧取值 = **`min(meta 值, 部署侧 cap)`**：cloud 的 cap = reconciler/kicker Lambda env `MAX_CONCURRENCY`（IaC 设；语义是**部署侧 per-run 上限**——task 跑在部署方 cluster、计入部署方账单，cap 保部署方的总量控制权）；meta 值为 null（提交侧没有给）按 1（与打通前行为一致）。**local（两种执行方式）无 cap 层**：worker 与推进进程都跑在发起 run 的本机、以本机凭证计费——资源买单方就是发起 run 的一方，无第二方需要保护；cap 只存在于「提交者与部署方分离」的 cloud 后端。local 的后台推进进程取它自己生成的运行定义里的值，这个值由 `submit` 解析之后经输入交来、恒有值，没有回落。同步 `run` 的 `ScheduleOpts` 仍直用 CLI flag（同进程、无通道问题；meta 照落，保 definition 诚实）。**多 job 并行不引入新并发面**：events 表跨 job 零共享键（PK=run_id#scope_id、每 PK 单写者不变），STATE 的认领、HWM 与写入序号条件写本就为云端多次调用重叠设计（机制三/四），local 后端 mc>1 早已真跑同一套 core 逻辑。
**曾反其道（决策反转记录）**：此值曾按后端分层——cloud 后端以 Lambda env 为唯一真源、`submit --max-concurrency` 静默不生效（当时留了「真出现同一部署下不同 run 要不同并发的需求，再议纳入 definition」的口子）。支撑假设「同一部署下各 run 无理由不同」被真实使用证伪：不同 run 的并行度本就随 feature 的 scope 结构不同，「静默不生效」是可用性缺陷、不是可接受边界；原论证里「资源闸属部署方」的正确内核收进 cap 语义。**同族对照**：`--report-dir` vs 推进器 `REPORT_DIR` 从一开始就不留静默分岔——它决定产出写到哪，分岔的后果是「跑完了但用户在自己给的前缀下找不到结果」，preflight 比对两侧、不一致退 2（[0033](./0033-iac-aws-backend-and-composition-wiring.md) preflight 条）；并发这条打通后，完全失效的形态已消除；声明超 cap 时按 cap 执行、提交时 preflight 提示（按 cap 跑是 no-op 分岔→提示即可，对照 `REPORT_DIR` 的退 2——判据 = 分岔后果）。

**「claim 了但 events 还没到」的窗口 → `project` 须以 RunStore 态为基线做单调合并（实装真跑逼出、补入设计）**：CAS 把 job 置 `running` 后、worker 还没 emit `scope_started` 前有一个窗口——此时 `project` 全量重放 events 里**看不到**该 job（无任何事件），会把它算成 `pending`；若投影写就此把它刷回 `pending`，下一个 tick 的 `plan_next` 又会提议 start、CAS 又成功 → **重复 launch 同一 job**（真 bug，回归护栏 `core/tests/test_reconcile.py::test_tick_idempotent_no_double_launch`）。故 `project` 除 events 外**接收当前 RunStore 的 `RunState` 作基线**，job 态按生命周期序（`pending < running < 任何终态`）与基线取**较推进者**、单调不倒退：已 claim 的 `running` 不被 events 的 `pending` 覆盖；终态一旦达成不被 `running` 覆盖。这与「全量重放幂等」不冲突——重放仍是纯推演，基线只提供「已 claim」这一 events 之外、却是 RunStore 权威的事实。`reconcile.tick` 在调 `project` 前 `load_run_state` 取基线传入。

## job timeout（产品级设定：两层声明 → definition 载体 → 三路推进器各自 enforce）

**产品语义**：job timeout 是用户对「一个 job 最多跑多久（墙钟，含启动开销）」的预算，属 run 的 definition、与推进方式（同步/detached）无关。**从 claim 起算、起 task 的时间计入预算（2026-11-01 复议维持）**：预算回答的是「一个 job 最多占多久资源」，从 claim 起算对使用方最可预测（实测云端 claim 到 worker 进入设备解析约 34 秒，两个样本，含 Fargate 任务启动与 worker 启动），也与设备目标按获取预算补缺省与下限的推导一致（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2）；被拒方案是改为从 worker 首个事件起算——推进器与超时定时器要多认一个时刻，收益只是几十秒。用户文档写明并建议给起 task 留余量。此前它只在同步路径实现了一半（`--timeout` 是 ScheduleOpts 运行参数、不进 definition），detached 路径完全没有——local 挂死永 running、cloud task 无限跑、计费失控（经 grace 校准适用面复盘发现，[0032](./0032-fargate-execution-environment.md)「适用面注记」）。**job 到点停止**：执行中的 job 到了起作用的截止时刻（算法见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条），被推进器停下。它是 job 级的停止，与结束一个 run 的 run 处置（0054 决策六）是两回事。停下之后按起作用的截止时刻判：是 job 自己的预算时记 `error`、归因 `timeout`；是运行期限时记 `aborted`、不算超时（状态语义见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定一，真值表见机制二「终结函数与真值表」）；内容已完整的 job 不改判（同一处）。

**两层声明、tag 优先**（复刻 `@engine`/`--default-engine` 同构模式，[0019](./0019-feature-tags-scope-and-engine.md) tag 体系扩展）：feature 层 scope 级 `@timeout:N`（秒，N>0，同 scope 声明不一致 → FeatureContractError——同 `@engine` 冲突先例；用例内容决定预算主体、feature 作者或测试开发在用例旁声明）+ CLI 层 `--default-job-timeout`。**覆盖顺序与校验顺序**（设备 scope 的缺省与下限见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2）：① 按来源取值：`@timeout:N` tag → 显式给出的 `--default-job-timeout`（命令行选项或配置文件任一来源，本项没有环境变量层；argparse 缺省为「未指定」哨兵，以区分内建 300 与显式给出的 300）→ 目标缺省（设备 scope 为获取预算加 900 秒，桌面为 300 秒）；② 非正的 `--default-job-timeout` 对任何目标都表示取产品上限 7200 秒、不被拒绝（没有「不超时」这一取值，上限与理由见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策十）；归一化只接受有限数，拒绝 NaN 与 Infinity；③ 上下限校验只对 tag 与显式正值解析出的有效预算：任何目标超过上限时抛 FeatureContractError、以退出码 2 结束；设备 scope 的值低于获取预算加 180 秒时同样抛 FeatureContractError，消息说明可能还没拿到设备就被判超时；被 tag 盖住、没有生效的显式缺省不校验；目标缺省自身在上下限之内、不校验。900 与 180 是待校准的缺省策略，不是经验证的预算保证。**flag 命名两个前缀都承重**：`default-` 防「误当强制值、被 tag 覆盖时错愕」；`job-` 消歧对象（act 级 `ACT_TIMEOUT_S`/将来可能的 run 级总预算并存，留 `--default-run-timeout` 对称位）。原 `--timeout` 已改名、未留 alias。**先不做**（防过度设计）：使用者单独配置的 run 级总墙钟预算；「CI 强制收紧压过 tag」层（真实冲突出现再议）。每个 run 另有一个由各 job 预算推出、建 run 时写进 definition 的运行期限 `deadline_at`，它不是使用者配置的预算（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二）；三路都遵守它：各 job 的截止时刻以它封顶（算法见 0054 决策二第 2 条）；停止认领与到期的结束写见 0054 决策二第 1、3 条（结束写的写法见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节，后台推进怎样取时刻与快照的要求见 0054 决策二后台推进条）。

**载体 = definition**：两层声明与目标缺省在组合根（及 core 的 plan 层，按目标选用缺省与下限）解析定值后固化进 `Job.timeout_s`（恒为有限正数，运行定义读端把空预算当作定义违约拒绝，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策十），随 RunMeta 持久化——推进器只认它，`ScheduleOpts.job_timeout_s` 退役（两层声明的解析仍只在一处）。worker 不强制执行 timeout（job 到点停止全在推进器侧，worker 只需继续守 flag-only 停止契约）；对预算只有两处读取：建会话前把 Job 携带的墙钟预算（[0024](./0024-worker-core-protocol.md) worker 输入的 `timeoutS`）与能力自述的 `max_session_s` 比较作自检（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2），以及桌面 worker 按它设定 AgentCore 浏览器会话的服务端存活上限（[0024](./0024-worker-core-protocol.md) 泄漏兜底条）；两处都不计时、不自停。

**enforce 统一形态 =「launch 时挂到点回调；到点若未终态则 stop；stop 后走既有退出观察链收敛」**，三路各自落地：

| 推进器 | 到点回调 | stop | 收敛 |
|---|---|---|---|
| 同步 `run`（schedule） | 进程内 per-job 截止时刻：取起作用的截止时刻（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条），按注入的墙钟比较 | `handle.stop(grace)` | 原路径：按起作用的截止时刻判，预算为 error+timeout，期限为 aborted（机制二真值表） |
| local 后台推进进程 | `SubprocessLauncher` 为每个执行中的 job 起一个检查线程，按短间隔读注入的墙钟（与推进步骤取认领时刻的是同一个读取点 `compose.now`），严格晚于 tick 交来的起作用的截止时刻（0054 决策二第 2 条）即停，只停一次；检查持续到 worker 进程退出，关了事件通道却不退出的 worker 同样被停下 | `handle.stop(engine_min_grace)` + 置本 scope timed_out 标志 | worker 协作退 → `_pump` 写 `task_exited(timed_out=True, exited_at=<看到退出的那一刻>)` → project 按起作用的截止时刻判（预算为 ERROR+timeout，期限为 ABORTED）；worker 在截止时刻之后、下一次检查之前自行退出时，`_pump` 不比较截止时刻、退出记录不带 timed_out，投影按 `exited_at` 晚于截止时刻判超时（与前台终结之前的那次检查同一判断，内容完整的同样不改判；见下「`timed_out` 归因链」） |
| cloud 后台 | **EventBridge Scheduler one-time schedule**（claim 后、起 task 之前 CreateSchedule，`at` 取 tick 交来的起作用的截止时刻（0054 决策二第 2 条，带秒），`ActionAfterCompletion=DELETE` 自动清；schedule group 与名字见 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 15）→ 到点 invoke kicker（payload 带 `timeout_scope`） | 仍 running 且 deadline 已到才动手（未到时怎样，见下「到点不早于 deadline」条②）：`ListTasks(cluster, startedBy=run_id)` **同时列 RUNNING 与 STOPPED**（后者 ECS 保留约 1h；按启动标识再带期望状态，两类都列得出，已核，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 实测项 27）→ `DescribeTasks` 按 overrides env `SCOPE_ID` 匹配（同 exit_observer 提取术）→ 按 task 状态分三路：**在跑** → `StopTask(reason 含哨兵串 gherkai-job-timeout)`；**正在停止**（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不动、等观察者（曾只列 RUNNING、把它判成「无踪」直写 timed_out，与几秒后到达的真退出记录同键互覆——恰在预算点跑完的 passed job 可被终判成 timeout，code-health 对抗验证发现）；**已 STOPPED 而无退出记录**（STOPPED 事件丢投）→ 从 DescribeTasks 的 task 对象用与观察者**同一提取函数**（`exit_from_task`）落真退出记录（含 task 的执行停止时刻；同内容、同键幂等）；两个列表都无踪才补写一条带 `timed_out` 的未知退出（只在还没有退出记录时成立的条件写） | worker 协作退 → exit_observer 见 `stoppedReason` 哨兵 → `task_exited(timed_out=True, exited_at=<执行停止时刻>)` → 同上；task 在截止时刻之后、停止请求发出之前自行退出时没有哨兵，观察者只记退出码与执行停止时刻，由投影按 `exited_at` 判超时 |

**到点不早于 deadline（Scheduler 只承诺分钟精度）**：Scheduler 文档写明所有 schedule 类型以 60 秒精度触发目标，指定 `1:00` 时在 `1:00:00` 到 `1:00:59` 之间触发（未设 flexible time window），`at()` 里的秒数不在承诺之内。带秒的 deadline 因此可能在它所在那一分钟的开头就触发、最多早约 59 秒；停止若只看 job 是否仍 running，job 实际可用的墙钟就会比预算短最多约一分钟。cloud 一路因此在停止的一侧复查 deadline，「不早于 deadline」不依赖 Scheduler 的秒级表现（local 与同步两路在本进程内按墙钟检查，没有这一偏差）。本节以下的 deadline 都指 job 的截止时刻（`run_deadline.job_cutoff`，算法见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条）：
- ① **schedule 的触发时刻取 deadline 本身**：tick 在认领时由认领时刻、预算与期限算出，经 `launch(job, cutoff_at=…)` 交给 CloudLauncher、原样交给 `TimeoutWatch.arm`，带秒、不取整，到点触发器自己不由预算推算。起算点是 claim 时刻而不是 arm 时刻，与本节「产品语义」段的「从 claim 起算」及防御扫同一算法，arm 晚于 claim 的那段间隔不会推后到点；写进运行态的认领时刻与算截止时刻用的是同一个值，停止的一侧读回重算得出的时刻与触发时刻相同。按文档语义，触发落在 deadline 所在的那一分钟内，早于或晚于 deadline 都不足 60 秒；这说的是触发时刻，invoke 到达 Lambda 与停止本身的耗时另计（见 ③）。
- ② **job 到点停止先复查 deadline**：job 已不在 running 或其退出记录已在时照常 no-op、不等待；仍 running 时由运行态里的 `claimed_at`、`Job.timeout_s` 与运行期限按同一算法重算 deadline 复查，未到则等待剩余时间，等完重新读取 job 状态与墙钟，仍 running 且已到 deadline 才进入上表的三路停止：发出停止之前必须有一次读到已过 deadline。「已到」「已过」都指读到的墙钟严格晚于 deadline，与本机检查线程、投影比较退出时刻的取法相同；每次等待至少是一个固定的短时长（1 秒）：恰好等于 deadline 时剩余为零、只差不到一秒时剩余很小，按剩余时长等待会让循环空转，而每次醒来都要重读 job 状态与退出记录；代价是停止最多晚不到一秒，不会提前。等完读到的仍不晚于 deadline（等待期间系统时钟被回拨，或恰好读到 deadline 本身）时在同一份等待额度内接着等，额度在第一次等待之前定下（取值见下），各次等待之和不超过它，累计按请求等待的秒数、不按墙钟之差；额度用完仍没到的这一次不停止，与剩余超过上界同一出口（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「截止时刻与说明」）。这段等待（额度在第一次等待之前定下、每次至少 1 秒、累计按请求等待的秒数）由 job 到点停止与 run 的两次定时触发共用，各自传入要等到的时刻（0054 决策九第 1 条）。等待只在 Scheduler 早于 deadline 触发时发生；按文档精度触发时剩余时间至多约 59 秒，正是文档精度之内的提前量。等待上界取 60 秒，落在推进器 Lambda 的超时（`stack.py` 的 `_advancer_function`，2 分钟）之内（这个超时另须小于停止认领的提前量加 300 秒，约束与理由在 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 12）；等待另受本次调用剩余时间的约束：临睡前（复查读取之后）按剩余时间减去停止与 tick 的预留算出还能等多久，不够等到 deadline 的同样按剩余超过上界处理，慢读取不会把停止挤出调用预算。剩余时间超过上界（Scheduler 早于其文档精度）时不等待、不停止，打一行诊断日志，保护降级为防御扫与 run 的两次到期定时触发（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条），与下文「best-effort 边界」条里 CreateSchedule 失败时的降级相同，宁可不停止也不提前停止（理由见 ③）。`JobState` 缺 `claimed_at`、或它读不出、不带时区时无从复查，按已到处理。防御扫只对已过 deadline 加余量的 job 调用停止，复查直接通过。
- ③ **代价与边界**：job 到点停止晚于 deadline 的推迟由三段组成：Scheduler 的调度精度分量（在那一分钟内偏晚的部分，不到 60 秒，有文档上界）、Scheduler 异步 invoke Lambda 的排队与启动、停止本身对 ECS 的几次调用，后两段没有文档上界（Scheduler 文档只对触发精度给出 60 秒，异步 invoke 到达 Lambda 与停止本身的耗时不在承诺之内）；一次 submit 真跑里 invoke 到达 Lambda 时已出 `at()` 所在的那一分钟，到点复查已过 deadline、随即 StopTask，没有早停，与这一判断相符；job 相应多占这段墙钟及其计费；等待只发生在 Scheduler 早于 deadline 触发而 job 仍在运行时，这时 job 离 deadline 已不足一分钟、几乎占满了整段 Fargate 预算（等待期间自行结束的，等完重读状态即 no-op）；每次至多约一分钟的 Lambda 时长计入部署方的运行成本，相对这段 Fargate 用量很小。job 墙钟预算是保护、不是承诺：停止晚于预算点不违背它，早于预算点则截断使用方预算之内的正常执行，故宁晚勿早。防御扫（claimed_at ②）的余量是经验值：覆盖调度精度分量加一次停止的常态耗时，让主机制在常态下先停止，不是上界；两者先后颠倒也无害（停止幂等、复查后才动手）。云端每 job 尾段 210 秒里「超时触发的调度精度，60 秒」那一段（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「尾段与余量是预算的取值」一段）对应调度精度分量，记账不变。

**best-effort 边界**：CreateSchedule 失败不阻塞 launch（保护降级为 tick 防御扫与 run 的两次到期定时触发，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条；打日志）；schedule 到点时 job 已终态 → tick no-op（幂等）。

**武装先于 RunTask**：起 task 失败时 tick 会补偿 record_exit，但若补偿也失败（双失败）job 会停在 RUNNING——先建的 schedule 到点仍使它收敛，最后兜底不因 launch 失败缺位；失败 launch 留下的 schedule 到点走 no-op/直接收敛并自动删，零残留。

**`timed_out` 归因链**：退出记录（`TaskExited`，独立键空间内的属性、不动键结构）带两项与超时有关的事实，写入方只记事实、不比较截止时刻，是否按超时处理只在投影里判断一次（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「截止时刻与说明」）。
- **`timed_out`：发过超时的停止请求，或补写时已判为超时**，不兼管「退出时已过截止时刻」。local 由 launcher 传入（检查线程到点停止时置的标志）；cloud 经 **StopTask 的 `reason` 参数原样出现在 STOPPED 事件 `detail.stoppedReason`** 这条现成通道传递（零新键空间/零新事件类型）；归因只认 reason 开头的哨兵串，哨兵串之后按起作用的是 job 预算、运行期限还是重算不出截止时刻（缺认领时刻）分别写，只给看 ECS 控制台的人读。来源两个：job 到点停止后经观察链写入的退出记录；cloud 的 job 到点停止（到点触发、run 的期限那一次、tick 的防御性超时扫描）在 RUNNING 与 STOPPED 两个 task 列表都无踪时补写的未知退出（见上执行方式表）。这条补写只在这个 job 还没有退出记录时写入，「没有」的判断与写入是同一次条件写（PutItem 带 `attribute_not_exists`），条件不成立即当作别的写入方已经写了、不报错，观察到的退出不被未知退出盖掉；其余写入方（观察到的退出、launch 失败补偿、cloud 按 task 对象的补写）照旧覆盖同键，补写之后才到的真实退出覆盖补写的那一条。
- **`exited_at`：退出时刻**（带时区；记录里是 UTC 的 ISO 串，经 `serialize.instant_to_iso` 写、`instant_from_iso` 读；云端属性没有值时不写）。local 是后台推进进程看到 worker 退出的那一刻（`_pump` 拿到退出码之后读一次注入的墙钟，与检查线程、推进步骤取认领时刻是同一个读取点）；cloud 是 task 对象里的执行停止时刻 `executionStoppedAt`，没有时取 `stoppedAt`（观察者从 STOPPED 事件 detail 的 ISO 串取，串经 `serialize.instant_from_iso` 严格解析，不带时区或读不出的串当作该字段没有值、按次序取下一个字段；job 到点停止从 DescribeTasks 的 datetime 取，不带时区的 datetime 按 UTC；同一个 task 两处取到同一个值，同键先后写入内容不变）；tick 的 launch 失败补偿是失败的那一刻（机制二「launch 失败补偿」条）。补写的未知退出没有可观察的退出时刻，本机同步 run 的记录器不记，这两种不带。
- **判断只在投影里**（`project._reduce_scope`，`project` 与 `project_full` 共用）：退出记录带 `timed_out`，或 `exited_at` 严格晚于这个 job 的截止时刻（由认领时刻、预算与期限经 `run_deadline.job_cutoff` 算出，与前台同一算法），都按超时交给终结函数，由起作用的截止时刻决定走真值表的哪一行；没有 `exited_at` 的只看 `timed_out`。每轮的无状态投影读不出基线里的认领时刻时同样只看 `timed_out`（投影写只推进到 `running`、不写 job 终态；写终态时快照里有记录的 job 都带认领时刻，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二后台推进条「快照」）。worker 在截止时刻之后、停止请求发出之前自行退出时，本机后台与云端后台由此得到与前台终结之前那次检查相同的判定。不让写入方各自比较：截止时刻要由运行态里的认领时刻与运行定义算出，cloud 的退出观察者只看 task 对象、读不到它们；判断放在各执行方式共用的投影里，规则只有一份。

两项都只记「是否超时」的依据：起作用的是预算还是期限不进退出记录，投影时由运行态里的认领时刻、预算与期限重算（同一条）。终结函数据此取 `stop_reason = timeout`，起作用的是预算时判 ERROR 并归因 `timeout`，是期限时判 ABORTED、无归因（内容完整的干净退出除外，见机制二「终结函数与真值表」）——与同步路径一致（超时是主动中止、非引擎故障，理由见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定一）。

**`JobState.claimed_at`**（`try_claim_job` 时写，机制四扩展）：① 截止时刻的起算点：各执行方由它、`Job.timeout_s` 与运行期限按同一算法算出这个 job 的截止时刻（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条），后台在投影与停止之前由运行态读回重算；`claimed_at` 缺失、读不出或不带时区的 job 没有起算点，按各处既有的「缺这个时刻」分支处理；② cloud tick 的**防御性顺带扫**——除 run 的期限那一次定时触发带来的强制推进之外（它已对全部执行中的 job 做过 job 到点停止，再扫只会按 job 逐个列 task，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条），每次 tick 对 running 且当前时刻已过 deadline（由运行态里的 `claimed_at`、预算与运行期限按同一算法重算）加余量的 job 走同一 job 到点停止，`claimed_at` 缺失或读不出的不碰（余量让 Scheduler 主机制先停止、避开与在途 STOPPED 观察链的竞态，非正确性参数，值见 `lambdas/reconciler.py` 的 `_DEFENSIVE_TIMEOUT_MARGIN_S`；这一扫是 Scheduler 的双保险：CreateSchedule 失败/schedule 丢失时，后续任何事件触发的 tick 都能补救）；③ status 可显示已跑时长。timeout 从 claim 起算、含启动开销（规则与理由见本节「产品语义」段）。

**与「idle 零成本」的关系**：one-time schedule 到点即删、无常驻轮询；**bonus**——到点 invoke 本身是一次强制 tick：建成了到点触发的 job 另有一次按它的截止时刻安排的推进（到达的推迟见上「到点不早于 deadline」条 ③，建不成时见「best-effort 边界」），顺带部分兜住「事件丢投级联断裂」（重议闸门首条的场景）。

**被拒方案（护栏）**：
- 常驻低频 rate rule 轮询——违「idle 零成本」，且粒度粗、空转扫描多。
- 动态 enable/disable rate rule（重议闸门预案挪用）——多 run 并发下 disable 有竞态（A finalize 查「无其他 running」与 B 刚 submit 的 enable 无原子性，交错可致规则停在 disabled、B 失去保护），状态管理复杂度不值。
- 纯 tick 内时长判定（不加时间触发器）——静默 job 不出事件，到它的截止时刻就没有 tick，盲区恰是最需要超时的场景（卡死）。已作为**防御性补充**保留（见 claimed_at ②），非主机制。
- `JobState` 存 task ARN 供 StopTask——`startedBy=run_id`（≤36 字符）+ DescribeTasks env 匹配已够、改动更窄；ARN 属执行环境句柄、暂不进读模型（真需要时再议）。
- job 到点停止时由停止方直接写 task_exited——进程未退、会与 observer 的真退出记录同 key 相互覆盖；stop 后让既有观察链自然收敛才是单一真源。
- `at` 保留带秒的 deadline 且到点不复查——接受最多早约 59 秒的停止，会截断预算之内的正常执行，预算贴近实际耗时的 job 被误判为超时，与预算是使用方给出的上界、定位为保护相悖。
- schedule 的触发时刻向上取整到整分钟、到点再复查——同样不早，但把取整与 Scheduler 调度精度引入的推迟分量从不到 60 秒放大到不到 2 分钟（取整推迟与那一分钟内的偏晚两段叠加；异步投递与停止耗时另计，两案相同）。取整后按文档精度触发总在 deadline 之后，复查的等待在文档精度之内永远用不上；取整多出的只是 Scheduler 早于其文档精度时仍可能等完再停止，而那种情形下不取整的方案已由复查保证不提前停止、交由防御扫兜底。用常态路径上翻倍的推迟分量换文档之外情形的这点覆盖，不值。

## core 拆分（守 [0026](./0026-schedule-module.md)/[0016](./0016-execution-architecture-core-lib-run-model.md) 窄腰红线）

```
core（纯函数，不 import boto3，local/cloud 共用）：
   project(RunMeta, events, baseline RunState) → RunState   # 纯归约，全量重放，幂等抗乱序；与基线按生命周期序单调合并（见上「claim 了但 events 还没到」条）；照常给出事件推出的终态，供推进步骤判断哪些 job 已有结果，投影写由 adapter 钳在 running（机制三②）
   project_full(RunMeta, events, 各 job 认领时刻) → [JobResult]   # 写 job 终态用：这一轮要写终态的各 job 的完整判定明细，按起作用的截止时刻分开判定；run 状态不在其中，由终态写按 0031 决定三的取法写下
   plan_next(RunState, max_concurrency, 是否已过停止认领) → [Action]  # 纯决策：该启哪些 pending、是否做到期的结束写；RunState 是这一轮读到的运行态加上这一轮终态写的作用（run_status.commit_applied），jobs 按运行定义的次序；动作只有认领启动与到期的结束写两种
adapter/组合根（Lambda handler / 后台推进进程，注入具体 client）：
   条件写（认领 / 投影 / job 终态写 / 结束写）/ RunTask / PutItem(task_exited) / 判定明细保存   # 所有副作用在此层
```

**core 只吐「当前状态」与「建议动作」，绝不持 store、不 import boto3、不依赖执行环境。** Lambda handler 是 cloud 组合根（cold-start 读 env 造 adapter 注入纯 reconciler——**仍是组合根注入，不是 ports 内部 env-sniff 全局单例**，[0016](./0016-execution-architecture-core-lib-run-model.md) 禁的 GlobalConfigManager 反模式要在评审时守住别退化成它）；后台推进进程是 local 组合根。归约代码作纯 core 函数被两宿主 import 复用 = 「不复制归约逻辑」的正解。

**时钟也只一份：三宿主（前台 `run` 的 CLI / local 后台推进进程 / 推进器 Lambda）落库时间戳一律调 `compose.now_iso()`**，反向解析一律 `serialize.instant_from_iso()`（严格，不带时区的时刻即报错；core 不读系统时钟——`tick` 经组合根注入的时钟（`compose.now`）取时刻、写进记录时经 `serialize.instant_to_iso`，`write_report_from_record` 的报告时刻由宿主传入，[0016](./0016-execution-architecture-core-lib-run-model.md)）。`now_iso()` 是同一读取点 `compose.now()`（带时区的 UTC datetime）的记录写法，写法本身是 `serialize.instant_to_iso`：前台 `run` 把 `compose.now` 作为调度循环的墙钟注入（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二），认领时刻由落库服务按 `instant_to_iso` 写进运行态，与 `now_iso()` 写出的其它时间戳同一形态。曾各写一份 `_now_iso`、两种 ISO 格式（`isoformat()` 的 `+00:00` vs `strftime` 的 `…Z`），使**同一份 RunState 内** `started_at`（submit 侧写）与 `claimed_at`/`ended_at`（推进器写）格式不同——`status --json` 按 backend 给出不同格式的同名字段，机读消费者被迫兼容两种。「不复制归约逻辑」同理适用于「不复制取时钟」：多宿主同写一份数据结构时，**格式真源必须唯一**。读回也只有一份：解析在 core 的 `serialize.instant_from_iso`，runtime 不另留容 `…Z` 后缀、把不带时区的串原样放行的宽松解析（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二：带时区的时刻值与记录写法之间的解析与写出各只有一处）。不留宽松的第二份：放行的不带时区的时刻一参与比较就报错，或按运行它的机器的时区被读成另一个时刻。这一条管的是参与比较与判断的读回；`list-runs` 人读表格把时刻换成本机时区显示的那一处（`render._local_time_label`）另有一份容错解析，解析不了原样显示，不参与比较。后台各处（推进步骤写终态所用的快照、云端到点复查与防御扫、run 级墙钟）读到读不出或不带时区的时刻时，按各自现有的「缺这个时刻」分支处理，不抛给使用者；云端到点复查与防御扫的时钟同样取 `compose.now`。

## Engine port 演进：pull-iterate → 增出 fire-and-forget

`Engine.run_scope(job) → (WorkerHandle, Iterator[Event])` 是 **pull 式**（调用方线程迭代事件流），**同步 `run` 路径用它**；同步 `run` 只有本机后端（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A），用的是 `SubprocessEngine`。无状态路径是 **fire-and-forget**：worker 自写持久 sink、观察者补 `task_exited`、reconciler 读表——不再有「调用方持续迭代」。**实装形态**：`FargateEngine` 只有 `start_scope(job) → task_arn`（只 PutObject job + RunTask、不返事件迭代器）：云端只有无状态路径（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A），不需要 pull 式入口。**未改 `Engine` Protocol 本身**——`reconcile.Launcher` 是无状态路径专用的注入口（local=`SubprocessLauncher` 起子进程旁路落 SQLite / cloud=`CloudLauncher` 经 resolver 选 FargateEngine 调 `start_scope`），故 core 的 `reconcile.tick` 只认 `Launcher.launch(job, cutoff_at=…)`、对「怎么起」无知，不必给 `Engine` Protocol 强加 `start_scope`。**起 task 的能力（subprocess spawn / ECS RunTask）收进注入的 Launcher/Engine，core 绝不 import boto3/ecs**（reconcile.py 只 import 标准库与 core 自身的模块）。

**`raw_sink` 的定位（local 后端落事件流的配套，同样不进 port 契约）**：local 没有「平台侧 events 表」，事件行由 `SubprocessLauncher` 后台线程（detached）或 `EventRecordingEngine`（同步 `run`，[0042](./0042-step-evidence-and-explain.md) 决策七）从 fd3 旁路落 SQLite——机制是 `SubprocessEngine.run_scope(job, raw_sink=...)` 这个**该 adapter 独有的扩展形参**（读到的每行原始 JSON 解析前回调；`FargateEngine` 没有 `run_scope`）。与 `start_scope` 同理**不上提到 `Engine` Protocol**：它是「local 怎么把行落库」的实现手段，不是所有 adapter 都该有的能力（cloud 侧 worker 自写 DDB，没有对应概念）。**代价与守法**：这使 local 无状态路径**绑死具体 adapter**——故该路径的注入口（`SubprocessLauncher.__init__` 的 resolver、launch 内取到的 engine）**类型标注一律收窄到 `SubprocessEngine`**，让绑死在类型上显形；若标成宽泛的 `Engine`，则「port 契约里没有 raw_sink」这件事被隐藏，换 adapter 只在运行时 `TypeError`（`core/gherkai_core/ports.py` 的 `run_scope` docstring 同处留了这条边界）。

## 对 [0016](./0016-execution-architecture-core-lib-run-model.md) 的纠正：「核心不动」是过强断言

[0016](./0016-execution-architecture-core-lib-run-model.md) 数处（「这样上云…核心与接口不动」条、版本切分 v1.1.0 行、「现在不做」条）断言「无状态化 = 加 adapter + 组合根换注入，核心与接口不动」。**本 ADR 纠正为分层两真值**：

- **(a) store/engine 后端替换**（local↔DDB/S3、subprocess↔Fargate）= 注入、核心不动——[0033](./0033-iac-aws-backend-and-composition-wiring.md) 已真部署真跑证实，**保留**。
- **(b) 无状态提交-收集**（本 ADR）= **驱动模型演进**：同步 `ThreadPoolExecutor` 循环解体为无状态事件驱动 tick、抽纯 `project()`/`plan_next()` 供两宿主复用、可能增 Engine port 形状、严格并发从进程内线程池迁到 store CAS——**核心与接口要动**。这比「只换 adapter」大得多，[0016](./0016-execution-architecture-core-lib-run-model.md)/[0026](./0026-schedule-module.md) 把 (a)(b) 混为一谈、over-claim 了。

存活的是**纯归约器**（`project`），消失的是**同步驱动循环**（ThreadPool/`wait(FIRST_COMPLETED)`/abort_flag/fail-fast `_stop_all`/进程内并发闸）——后者在无状态路径重新宿主为 reconciler，其中 fail-fast 的 `_stop_all` 尚未宿主（`submit` 不提供该选项，`stop_reason` 在该路径只有 none / timeout，见机制二），[0028](./0028-transient-network-ssl-resilience.md) 的 job 级 network 重试（`_Worker.run` 的重试循环）也未宿主（同步路径下它默认关、CLI 不暴露，所以两条路径的实际行为一致：都不做 job 级重试）。同步 `run` 路径仍用现驱动循环（两种驱动模型并存，按命令分流）。

## 地基实测（2026-07-19，真实 AWS 账户/us-east-1；6 个真 Fargate task——其中 4 个构成 H1 退出场景矩阵——+ 真 DDB Streams/条件写）

moto 立即返回测不到事件投递/并发时序，健康网真跑不触发这些路径——故下列是「绿≠对」边界的唯一有效证据：

- **H1 事件 payload 带 exitCode（4/4，含最硬的 SIGKILL 截断）**：正常退出 exitCode=0→payload 带 0；缺 job 非 0 退出=1→带 1；StopTask 软停=0→带 0；**忽略 SIGTERM 的 sleeper 被 SIGKILL 硬杀=137→payload 仍带 137**。结论：观察者从 STOPPED 事件读 exitCode 可靠（事件锚在 `stoppedAt`、已过 exitCode 落值窗口）→ 机制二「极薄观察者」成立；缺退出码时重查 DescribeTasks 的兜底整体被拒（见机制二「退出码缺失：观察者落哨兵、不留宽限态」条），缺退出码一律落非 0 哨兵 + `reason`。
- **H2 延迟**：EventBridge→Lambda 投递 **0.6s**（近瞬时）；但端到端「worker 真停(`executionStoppedAt`)→可归约」= **~27s**，瓶颈全在 ECS 平台 `executionStoppedAt→stoppedAt` 清理开销（STOPPED 事件锚在 `stoppedAt`）。放大了 [0032](./0032-fargate-execution-environment.md) 记的 ~11s 平台滞后。**级联每步有 ~20-30s 固有尾延迟**——对异步跑批可接受，`status --wait` 会有此尾延迟，属已知特性。
- **H3/机制三/四 并发写序（真 DDB）**：HWM 条件写——B 写终态(hwm=20)后 A 用旧快照(hwm=10)迟到写被 `ConditionalCheckFailedException` 挡、终态未被刷回 running；同 hwm 重复写幂等。**DDB Streams 并发度=2**（4 job 触发 2 个并发 Lambda 实例）→ 坐实「并发 reconciler」前提真实、HWM 条件写用得上；**同 PK 严格保序**（每 job seq `[1..5]` 按序到达）。

**已补真验**：`setsid` local 脱离 → **已真验**（local submit → 后台推进进程脱离 CLI 后台推进 → CLI 退出后 status 读到 running/passed）；四机制 → core 单测（`test_reconcile.py`/`test_cloud_reconcile.py`/`test_project.py`）+ local/cloud 端到端真跑覆盖。仍留未做项见下「重议闸门」（如 Stream 长期丢失率的量化、动态定时兜底规则）。

## 被拒方案（护栏，防未来重踩）

- **让 worker 自报退出事件**（省掉平台侧观察者）：拒——worker 可能 SIGKILL/崩溃/发完 scope_done 才退，没机会自报；「进程干净终止」本质只有平台/父进程可见（机制二）。
- **`task_exited` 共享 worker 数值 seq 段**：拒——观察者无 worker 的 seq 计数器，Query-max-then-write 撞号覆盖 `scope_done` / 造空号破断号检测（机制一）。
- **reconciler 靠全量重放天然幂等、投影写不加版本守卫**：拒——并发实例 stale 快照 lost-update 能把 finalized run 刷回 running；全量重放只保证派生幂等、不保证跨实例写序（机制三）。
- **把 CAS+RunTask+PutItem 与归约合成单一 core reconciler 组件**：拒——逼 core 持 store + 依赖执行环境、Engine port 长出启 task 职责，破 [0026](./0026-schedule-module.md) 纯 reducer（core 拆分节）。
- **让每个消费者各自 `project(events)→RunState`（绕过 reconciler 这一处推演、如为求新鲜度让 `status` 直接投演 events）**：拒——多份推演逻辑必漂移（同一 events 在 status/WebUI/reconciler 各推一版、口径迟早分叉）；且各消费者写 RunState 会破 HWM 与写入序号条件写的前提（机制三）。外部只读 RunState、推演只在 reconciler 一处（「核心思想」单一读接口不变量）。
- **cloud submit 由 CLI 直接起首批 task（冷启动）**：拒（实装初版这么做、后改）——让 submit 机器背 `ecs:RunTask` 权限，与本设计卖点「提交完就走、只需提交那一下的最小权限」相悖：submit 机器权限面越小越好（受限 CI runner / 临时凭证场景）。改由**kicker Lambda** 冷启动（见下），submit 机器权限面收窄到没有任何 ECS 写/执行权限（完整清单见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」末段）。
- **runs 表 Stream 直接触发 reconciler（复用同一 Lambda 做冷启动）**：拒——**自触发放大**：reconciler 每次推进都写 runs 表（认领、投影与终态写），若 runs Stream 触发 reconciler，则它写 runs → 又触发自己 → 每个 run 生命周期空转 N 次（tick 幂等使无害、但持续无效唤醒 + 全量重放读放大）。改用**独立的 kicker Lambda 接 runs Stream**——**注意它不是「薄 Lambda」**（那是退出观察者的形态）：kicker 与 reconciler **同一份 code、同一套装配与权限**，只换 handler 与触发源，起 task 的 tick 同样写 runs 表（`project_state`/`try_claim_job`/终态写）。故拒的实质**不是「kicker 更轻」，而是「别让主推进器订阅它自己写的表」**；隔成专用 Function 换来的是**触发面干净**：kicker 的 event source mapping 带过滤（见上端到端 1b，写法在 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 13——过滤是必需项、非「用 filter 补救耦合」），只被 STATE 条目的新建与使 run 成为终态的那次写唤醒；reconciler 只被 events Stream 触发（worker 有进展才推进），它自己写的 runs 表 MODIFY 流不叠回任何推进器。kicker 另接 Scheduler 的定时触发（job 到点停止与 run 的到期定时触发，见「job timeout」节与 0054 决策九），职责是「让 run 动起来」、非「只起首批」。
- **定时器轮询推进**（EventBridge scheduled rule 每 N 秒 tick）：拒——idle 也 fire、空转计费，且要权衡「间隔短=延迟低但费 / 间隔长=省但收尾慢」这个不该存在的取舍。改用 ECS Task State Change + DDB Stream 事件驱动，idle 零调用（端到端流程 cloud）。
- **per-run 推进器也给 cloud**：拒（用户定）——cloud「扣笔记本下班」场景只靠 IaC 部署的事件驱动链，本机不留常驻推进器；后台推进进程只在 local。
- **本机接力，及其改法**（本机 `status --wait` 在后台推进进程不在时接手推进：别人认领、没有退出记录的 job，过了它的截止时刻加一段时长就补写未知退出；改法是凭进程核对判断认领方是否还在）：拒——推进器唯一之后没有可接力的对象，管它的进程不在了的 run 只能由处置结束（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、七）。凭时钟加一段时长推断认领方已经收尾完的做法三次失守：固定 10 秒比各引擎的停止宽限短，认领方在截止时刻催停、worker 仍在停止宽限内协作收尾时接力方照样补写，补写之后、真实退出之前读到补写的那一轮推进按超时写下这个 job 的终态；改为墙钟超过「截止时刻加两倍停止宽限加 10 秒」，墙钟在宽限内前跳时条件立刻成立，合盖休眠之后恢复即是；再改为接力方从自己观察到已过截止时刻起按单调时钟等满这段时长，一次只被接力方看到的短暂前跳加上不撤销的首次观察，使接力方在认领方刚发出停止时就补写（后两种都用真实的 worker 与停止信号复现）。三次是同一种结构：接力方只凭自己看到的时钟读数，推断认领方要么不在了、要么已经收尾完，手里没有来自对方的证据；把时长再放宽、或看到墙钟回拨就重新计时，都还是这种结构——认领方被暂停之后在这段时长快满时恢复并催停，接力方照样紧接着补写。改看认领方的进程是否还在（随认领记下进程标识、再核对），对方进程的信息在 Linux 上不断出现新的反例（0054 被拒方案「读对方进程的信息」）。生命期锁把死活交给内核回答（0054 决策三），推进器又只有一个，接力也就无从谈起。
- **云端按 run 串行的队列**：拒——各触发源都要改投到按 run 分组的队列，多一个组件与一跳延迟，还挡不住 `status --wait`、`settle-runs` 这类不经队列的写者，条件写仍要保留。
- **把云端的推进入口收成一个**：拒——同一个函数的多次调用照样并发（流按分片并发，定时触发与退出观察各自唤醒），挡不住重叠；两个入口各过滤自己的触发面。

## 重议闸门

- **Stream/事件偶发丢投致级联断裂成真痛点** → 加安全网：submit 时 enable、run 结束时 disable 的**动态定时兜底规则**（仅在有活跑批时低频轮询、真 idle 时规则禁用=仍零调用），比常开定时器省。当前推进链断开的 run 怎样结束见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条（含前提），动态定时兜底规则先不做。加这条规则时它调用 kicker 须用 kicker 认得的载荷（「推进器与触发源」第 2 条），只带 `run_id` 的载荷只记日志、不推进。
- **常驻调度服务 / WebUI 真需要** → RunState 读模型 + reconciler 已就位，加 adapter/宿主即可（[0016](./0016-execution-architecture-core-lib-run-model.md)「加 adapter + 换注入」在 (a) 类仍成立）。
- **本地 events sink 选型**：定 **SQLite**（事务 + WAL 单写者串行化，承后台推进进程内多 fd3 读线程并发 append 不丢不乱；表结构镜像 DDB events：PK=scope_id/SK=seq，与 cloud 心智对称）。被拒 append-only JSONL——虽最简无依赖，但并发读写只能靠 append 原子性 + 容忍半行，无事务保证。**注：条件写不在 events sink 上**——sink 只做幂等 `INSERT OR REPLACE`；local 建 run 之后的条件写落在 `LocalRunStore` 在 `.runstate.lock`（`flock` 短锁）内按整份运行态的读改写（机制三②），那才是「local 复刻 cloud 条件写语义」的落点。
- **设备目标不另立起算点**：Device Farm 会话的创建与排队计入自推进器启动 job 起算的墙钟，获取预算只在 worker 内部执行，见 [0051](./0051-device-session-lifecycle-and-app-distribution.md)。
- **已确认镜像存在、同一 digest 的拉取仍偶发失败再次出现 → 评估是否有界重试**：观察（2026-11，开发后端，根因未确定）：一次两个 job 的 `submit` 里，一个 job 的 Fargate task 以 `TaskFailedToStart` 结束（`CannotPullContainerError`，按 digest 解析镜像返回 not found），同一个 run 的另一个 job 同一时刻按同一 digest 拉取成功；该镜像在 ECR 里是单个 OCI image manifest、一直存在，仓库没有生命周期策略；退出观察 Lambda 近 30 天的日志里仅此一次，之后同一用例重新执行，两个 job 都通过。现有观察不足以确定原因；它不是 worker 镜像清理与 runs 表索引协议的实测项（[0038](./0038-worker-image-delivery.md) 实测项 8 到 10），这里只记观察与闸门。现行做法不变：缺退出码的 STOPPED 落哨兵、job 判 error、不重试（上「退出码缺失」条；launch 级重试属 job 级重试的既有留口子，上「launch 失败补偿」条）。本闸门只针对镜像确实存在、同一 digest 的拉取仍偶发失败的情形；镜像引用写错、镜像不在仓库里等配置问题不在其内，按现行做法判 error。再次出现时，先收集能区分原因的现场（同一 digest 其它 task 的拉取结果、ECR 侧对该次拉取的记录），确认镜像存在之后，再评估是否对这类拉取失败做有界重试。
