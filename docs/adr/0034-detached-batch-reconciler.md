# 无状态跑批：CLI 提交 → 事件驱动推进 → 轮询收集（CQRS + reconciler）

> **Status:** Accepted —— **已全部实装、local+cloud 两路端到端真部署真跑通**（core `project`/`reconcile` + cli `submit`/`status`/`detached` + `lambdas/` 三 Lambda + `iac_aws_backend` Stream/EventBridge 均落 code；账户 000000000000/us-east-1 真跑：local submit→per-run 推进→passed，cloud submit→kicker 冷启动→事件驱动链→passed，含卡死救活真验）。纠正 [0016](./0016-execution-architecture-core-lib-run-model.md)「无状态化=加 adapter+换注入、核心不动」对本能力的过强断言（见下「对 0016 的纠正」；0016/0024/0026/0031 已同步标 Partially-superseded-by 本 ADR，0030 标其「重议」条已由本 ADR 落地）。

同步 `run` 是**「CLI 阻塞跑一批」**：组合根同进程 `schedule()` 持 `ThreadPoolExecutor`、`as_completed` 收敛到全批完成才返回。本 ADR 落地的产品项（曾是产品线唯一未做项、非加固）= **「CLI 提交完就走、异步收集」**（[0016](./0016-execution-architecture-core-lib-run-model.md) v1.2 已完成 + [0017](./0017-cloud-execution-fargate-over-runtime.md) batch shape）——新增 `submit`/`status` 命令、同步 `run` 保留不变。本 ADR 定这套无状态跑批的架构、数据模型、并发/写序不变量与被拒方案护栏。

## 定位：产品价值，非加固

- **产品价值**：CI/用户 `submit` 一批用例即可离场（关笔记本、断开），run 在云上自跑到完成、结果异步收集；对照当前必须让 CLI 全程阻塞守着。
- **不做**：常驻调度服务 / WebUI（接口留好，真需要时加 adapter）；跨 run 的批队列编排（每 run 独立）。

## 核心思想：CQRS + 无状态 reconciler

把「CLI 进程持有线程池、阻塞跑完整批」换成「**events 表是唯一真值日志，一个幂等函数被事件唤醒着把整批推完**」：

- **写模型** = events 表（append-only 真值日志，[0024](./0024-worker-core-protocol.md)）。
- **读模型** = `RunState`（物化视图；**外部消费者只读它**）。
- **reconciler**（投影器 + 推进器）= 纯从 events 推演 `RunState` + 决定启下一个 job。**无状态、幂等**：谁触发、何时触发、并发触发都安全，进程内不留任何调度态。

**单一读接口不变量**：外部（`status` / 未来 WebUI）**永远只从 `RunState` 读状态**；`events → RunState` 的推演**只在 reconciler 一处**，不散落到各消费者（否则多份推演逻辑必漂移）。这是本设计的骨架原则。

## 数据模型三件套（职责分明）

| | 是什么 | 谁写 | 谁读 |
|---|---|---|---|
| **events 表** | 真值日志 | worker（执行事件）+ **退出观察者**（退出事件） | reconciler |
| **`RunState`** | 物化读视图 | **唯一写者 = reconciler** | 外部（`status`/WebUI）**只读** |
| **RunReport** | 派生产物（永远最后） | reconciler 在 `finalize` 时聚合（[0027](./0027-runreport-aggregation-index.md)） | 人 |

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
gherkai run <features>    # 原阻塞皮 = submit + 同进程 status --wait，行为不变
```

`run` 是 `submit`+`status --wait` 的**组合皮、非另一套代码**——兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)「阻塞 vs 非阻塞是调用方的选择、同一核心两种皮」。三命令共享同一 reconciler。

**退出码语义分层**（演进 [0031](./0031-job-lifecycle-states-and-severity.md) 决定五「退出码读内存终值」）：`submit` 退出码 = **提交成功与否**（0=已提交、run_id 已返回；≠run 判定）；判定退出码（PASSED→0 / 其余→1）由 `status --wait` 读到终态时给出。CLI 脱离后不再有「内存 RunResult 终值」，判定退出码只能来自读回的 `RunState`。

## 端到端流程

### cloud（事件驱动，idle 零成本）

```
1. submit(CLI)：plan → create_run 写 RunMeta+全 pending 到 runs 表 → CLI 退出（run_id 已在手）。
   **只写 DDB、不起任何 task**——submit 机器权限面仅「runs 表写 + preflight」，不碰 ECS RunTask（冷启动由kicker Lambda 做，见下）。
1b. runs 表 Stream（**仅 INSERT**）→ [kicker Lambda]：新 run 的 definition 落库即触发 → tick 起首批
     min(max_concurrency, |jobs|) 个 task（CAS 抢占）。这是纯事件驱动链的**冷启动**（无此步则无 events/无 STOPPED，
     events Stream 永不触发第一次 reconciler）。kicker复用同一 `reconcile.tick`（四宿主一份：submit-local / kicker /
     reconciler / status 接力）。
2. worker 云上跑（CLI 退出不杀 task，已实测）：PutItem 执行事件(seq 递增)→events 表；上传产物→S3
3. task STOPPED → ECS 自动发 "Task State Change: STOPPED" 事件 → EventBridge
     → [退出观察者 Lambda]：从事件 payload 读 exitCode（实测 4/4 都带，含 SIGKILL=137）
       → PutItem 一条 task_exited 事件(独立键空间 + exitCode) 到 events 表
4. events 表变化 → DynamoDB Stream → [reconciler Lambda]：
     ① 读该 run 全量 events → 纯推演完整 RunState
     ② HWM 条件写落 RunState（挡 stale 覆盖）
     ③ running<max_concurrency 且有 pending：CAS(pending→running) 抢一个 → RunTask 启下一个
     ④ 全 job 终态：finalize(写总 status) + 聚合 RunReport
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

**关键：local 的 worker 不改、对 SQLite 无知（施工 P3 校准）**——worker 仍讲 [0024](./0024-worker-core-protocol.md) fd3 协议吐原始 JSON 行（引擎无关、两执行环境同一份 worker），SQLite 落库是 per-run 进程侧 `SubprocessLauncher` 读 fd3 时旁路做的（存原始行 + 按到达序赋 worker 段单调 seq）。故「worker 写持久 events 存储」在 local 的准确表述是「per-run 进程代 worker 写」——worker 业务零改，对称性落在「事件最终进了持久可重放存储」这一层，非「worker 自己写哪」。

**per-run 进程内多 worker 并发写同一 SQLite 的串行化（施工 P3 处理）**：`max_concurrency>1` 时 per-run 进程并发起多个 worker，每个一个 fd3 读线程往同一 SQLite append。SQLite 单写者——多线程 append 靠 **WAL 模式 + 短事务**串行化（写争锁排队、不丢不乱；每条 append 是独立小事务）。这是 per-run 进程内的线程并发（非跨进程），锁竞争轻、可接受。**跨进程写 events sink 的并发**：正常态只有 per-run 进程一个写者；但 per-run 进程崩后 `status --wait` 接力**会自己 spawn worker、写同一 SQLite events sink**（local 无云端 Lambda 起 worker，接力只能本机顶上——见下「三触发源」的 local/cloud 不对称）。两者不会真并发写（per-run 崩了 status 才顶上、串行接替），且 SQLite WAL 跨进程写锁本就串行化；但设计上假定「同一时刻至多一个本机进程在推 local run」（per-run 或接力的 status，不同时）。

## 推进的三个触发源（都幂等、并发安全）

1. **主力**：cloud=DDB Stream 事件 / local=per-run 进程——正常一路推完。
2. **兜底/接力**：`status --wait`——per-run 进程崩、或 Stream 偶发断链/丢投时，人来查即接力推（状态全持久、tick 幂等，断点续）。**local 与 cloud 的接力机制本质不对称（关键，勿混）**：
   - **local 接力 = 本机进程亲自跑 tick**（spawn subprocess worker、读 SQLite、finalize）。**推进全靠这个本机进程**——掐掉即停（local 无云端接管者）。故 local 必须**有本机进程真跑到终态**：要么 submit fork 的 per-run 进程，要么 per-run 崩后 `status --wait` 顶上、且**必须一直 wait 到底**。
   - **cloud 接力 = 检测卡住才异步 fire-and-forget invoke kicker Lambda**（`InvocationType=Event`、不等返回）。**kickoff（秒级）即完成救活**——此后即便退出 `status`，云端 Lambda 链（kicker起首批 → events Stream → reconciler）自接管跑完，**不依赖本机 status 进程存活**。**「检测卡住」= 状态连续 K 轮无变化才踢**（记住上轮 `(status, high_water_mark)`，连续 K 轮不变→判卡住→invoke 一次→重置）——**非每轮无脑踢**：run 正常推进（hwm 在涨/态在变）时一次都不踢，只在真卡住（冷启动丢投卡 pending、或中途丢投卡 running）时踢。避免正常路径下 N 次无效 invoke（kicker tick 发现无 pending 即 no-op、白白重放读 DDB）——对齐「零空转、只在真需要时动」的事件驱动精神（[CLAUDE.md「工作方式」：交付物运行成本是设计约束]，同否决定时器轮询的理由）。检测是纯客户端内存比较、零额外 AWS 调用/权限。保 status 机器零 ECS 权限（起 task 走 Lambda 角色）；Lambda 名从 `--prefix` 推理、用户无感。
   - **一句话**：cloud「kickoff即可离场」/ local「本机必须跑到底」。根因在**主推进器位置**（cloud 云端 Lambda / local 本机进程，见 1.）——三触发源「齐备」是表层对称，「本机是否必须跑到底」才是里层不对称。
3. 三者同时触发也无害——靠下面 CAS + HWM 条件写。**`status` 对 cloud 是可选的查看+崩溃kickoff（非推进链必需环，云端链才是）；对 local，per-run 崩后 status --wait 是唯一本机推进者、此时反而是必需环**。

## 四个关键机制（均已实装：机制二/三/四有地基实测支撑，机制一从 [0024](./0024-worker-core-protocol.md) seq 不变量推导、独立键空间存取由单测覆盖 `test_sqlite_event_log`/`test_cloud_reconcile`）

### 机制一：`task_exited` 用独立键空间（不入 worker 数值 seq 段）

退出观察者**不持有** worker 的 seq 计数器（[0024](./0024-worker-core-protocol.md)：seq 单进程串行自增、无分布式协调）。若 `task_exited` 塞进 worker 的连续数值 seq 段，DDB 最终一致读会算错 max seq → 撞号**覆盖 `scope_done`**（裸 PutItem 无条件写），或造空号让 adapter 断号检测死循环。**故 `task_exited` 用独立键空间**（SK 前缀 `exit#` 或独立 item_type），adapter 的单调 seq/断号检测只跑 worker 的连续 seq 段，退出事件旁挂不入流。worker「每 PK 单写者、seq 单进程自增」不变量**原样保留**——events 表只是多了一个**独立键空间**的第二写者（演进 [0024](./0024-worker-core-protocol.md)，见下）。

### 机制二：退出事件由平台侧观察者提供，从事件 payload 读 exitCode

**退出绝不能 worker 自报**：worker 可能被 SIGKILL 硬杀、或发完 `scope_done` 才在会话释放时非 0 退出——它**没机会**再 PutItem 报告自己的退出。故「进程干净终止」的信号只有平台/父进程看得见：cloud = ECS Task STOPPED 事件；local = per-run 进程 `proc.wait()`。观察者从该信号取 exitCode 写 `task_exited`。

**「两件都要」（[0024](./0024-worker-core-protocol.md) 终止契约）在 reconciler 里成为对事件日志的纯谓词**——但**「内容完整（scope_done）」只对声称成功（exit==0）的进程要求**（施工 P3b 真跑 crash worker 逼出的精确化）：

- **`task_exited` 且 exit≠0（崩溃/网络码 80/SIGKILL）→ ERROR 终态，不等 `scope_done`**：worker 崩了根本没机会发 `scope_done`，此时**进程非干净终止本身就是终态信号**。若仍死等 `scope_done`，crash job 永远 RUNNING、reconciler 死循环（P3b `test_crash_worker` 复现）。这一分支也覆盖「发完 scope_done 又非 0 退出」的误报 PASSED（exit≠0 一律 error，不看内容）。
- **`task_exited` 且 exit==0 → 要求 `scope_done`**：干净退出才谈「内容完整」。有 `scope_done` → scenario 归约终态（passed/failed/error）；干净退出却没 `scope_done`（矛盾：进程说成功、内容没发完）→ ERROR（judged error 比死循环安全）。
- **`task_exited` 且 exitCode 未落值（None，宽限态）→ 保守 RUNNING**（等观察者补 exitCode，机制二兜底、ADR 0032 落值延迟）。
- **无 `task_exited`（进程还没终止）→ RUNNING（见了 scope_started）/ PENDING（还没起）**。

即：**进程终止（exit≠0）优先于内容完整判终态**；只有干净退出（exit==0）才回到「scope_done ∧ exit」的两件都要（实现见 `core.project._job_status`）。

**exitCode 落值延迟兜底（防御性冗余）**：[0024](./0024-worker-core-protocol.md) 记 `lastStatus==STOPPED` 与 exitCode 落值非原子、`(True,None)` 是有界宽限态。**但 STOPPED 事件锚在 `stoppedAt`（task 完全清理完、已过 exitCode 落值窗口），故观察者从事件 payload 读 exitCode 可靠——实测见下 H1/H2**（数字集中在地基实测节，不在此复述）。仍保留一条廉价兜底（payload 缺 exitCode 则短暂重查 DescribeTasks / 重试）防未来平台行为变——**留而不依赖**，非 load-bearing。

### 机制三：`RunState` 投影写带 HWM 条件写（防并发 lost-update）

reconciler 逻辑上是「唯一写者」，**物理上是并发实例**（实测：DDB Stream 按 PK 分片、多 job 触发 2 个并发 Lambda 实例；叠加 `status --wait` 是额外触发源）。并发实例读快照时点不同：实例 A 读到 seq=10 推演 `{running}`，实例 B 读到 seq=20 推演 `{passed}` 先写，A 用旧快照后写会**覆盖终态**（把 `passed` 刷回 `running`，外部看到非单调）。全量重放保证**派生逻辑**幂等、抗乱序，但**不保证跨实例写序**。

**解法 = 两道条件写，各管一类回退，不能只用 HWM**：

- **① HWM 挡 worker 执行事件段内的 stale 覆盖**：`RunState` 带 `high_water_mark`（已处理的 worker 段 max seq）；投影写条件含 `attribute_not_exists OR :hwm >= hwm`，读到更少 worker 事件的 stale 实例写被 `ConditionalCheckFailedException` 挡掉。这管的是「A 读到 seq=10、B 读到 seq=20，A 迟到写覆盖 B」这类**数值 seq 可比**的回退。
- **② 状态机单调条件写挡终态回退（HWM 挡不住的边界，必须单列）**：`task_exited` 走独立键空间、**不带数值 seq**（机制一），故「被 `scope_done`（末 seq=5）触发的投影」与「被 `task_exited` 触发的投影」携带**相同 HWM(=5)**——`task_exited` 恰是把 job 翻终态的那条事件，单靠 HWM(`5>=5` 成立) **挡不住** stale 的 `scope_done` 投影把已 `passed` 的 job 刷回 `running`。**故 job 状态与 run 总 status 的终态转移另加一道单调状态机条件写**：`status ∈ 非终态集` 才允许写（`ConditionExpression` 断言当前非终态；终态 `passed/failed/error` 不可被任何后到的写覆盖）。finalize（run 总 status）同理单独条件写，保证 commit 恰一次、RunReport 触发幂等。

两道条件缺一不可：HWM 管 seq 可比的进度回退，状态机单调管「跨独立键空间事件（task_exited 无 seq）的终态回退」——后者正是 `scope_done`/`task_exited` 这个 finalize 边界的关键守卫。这是 [0030](./0030-realtime-persistence-seam.md)「重议」条预告的「进程外多写者需条件更新」的落地（见下反向链）。local SQLite 用 `UPDATE...WHERE hwm <= :hwm AND status NOT IN (终态)` 复刻两道条件。**被拒 owner/lease 分布式锁**：0030 曾预告用 lease 保唯一写者——拒，lease 有状态、需续租/故障接管；无状态的 HWM + 状态机乐观条件写即够（写失败即整体重放重试，天然幂等），更轻。

**投影写 run 级 status 钳为 `running`/`pending`、不落终态（施工 P3a 逼出，衔接 [0030](./0030-realtime-persistence-seam.md) commit point）**：`project` 在全 job 达终态时会聚合出 run 级**终态**，但 `project_state`（投影写）**不能把它落库**——run 级终态是 `try_finalize` 这个 commit point 的**专属**（[0030](./0030-realtime-persistence-seam.md)：finalize 一落=run 已提交）。若投影提前落 run 级终态，紧接着的 `try_finalize`（条件「当前 status ∈ 非终态」）会被**投影自己刚写的终态挡住**、run 永远 finalize 不了。故 `project_state` 落库时把 run 级 status 钳为 `running`（非 `pending` 时）——**各 job 态仍是真实态（含终态，供 `plan_next` 判全终态），只 run 级钳**；run 级终态由 `try_finalize` 用 `project` 聚合出的真实终态一次落定。`project_state` 另加对偶保护：库中已 finalize（run 级终态）则挡投影（不把终态刷回 running）。cloud DDB 与 local SQLite 对称实现此钳制。

### 机制四：CAS(pending→running) 控严格并发

严格 `max_concurrency` 的执行点从 core 内 `ThreadPoolExecutor`（进程内、无 store）**迁到 store 的 CAS 条件写**：起一个 job 前 `CAS(status: pending→running)`，多个触发源并发看到同一 pending job 都想启，**只有条件写成功的那个去 RunTask/spawn**，其余被拒跳过。稳态并发恒 = max_concurrency，不靠任何常驻进程 hold 线程池。core 的 `plan_next` 只**提议**动作，真正的并发闸是 adapter 的 CAS。

**「claim 了但 events 还没到」的窗口 → `project` 须以 RunStore 态为基线做单调合并（施工 P3a 逼出，补入设计）**：CAS 把 job 置 `running` 后、worker 还没 emit `scope_started` 前有一个窗口——此时 `project` 全量重放 events 里**看不到**该 job（无任何事件），会把它算成 `pending`；若投影写就此把它刷回 `pending`，下一个 tick 的 `plan_next` 又会提议 start、CAS（此刻已是 running？不，被刷回 pending 了）又成功 → **重复 launch 同一 job**（真 bug，P3a `test_tick_idempotent` 复现）。故 `project` 除 events 外**接收当前 RunStore 的 `RunState` 作基线**，job 态按生命周期序（`pending < running < 任何终态`）与基线取**较推进者**、单调不倒退：已 claim 的 `running` 不被 events 的 `pending` 覆盖；终态一旦达成不被 `running` 覆盖。这与「全量重放幂等」不冲突——重放仍是纯推演，基线只提供「已 claim」这一 events 之外、却是 RunStore 权威的事实。`reconcile.tick` 在调 `project` 前 `load_run_state` 取基线传入。

## core 拆分（守 [0026](./0026-schedule-module.md)/[0016](./0016-execution-architecture-core-lib-run-model.md) 窄腰红线）

```
core（纯函数，不 import boto3，local/cloud 共用）：
   project(events) → RunState/RunResult          # 纯归约，全量重放，幂等抗乱序
   plan_next(RunState, max_concurrency) → [Action]  # 纯决策：该启哪些 pending、是否 finalize
adapter/组合根（Lambda handler / per-run 进程，注入具体 client）：
   CAS 写 / RunTask / PutItem(task_exited/finalize) / RunState 落库   # 所有副作用在此层
```

**core 只吐「当前状态」与「建议动作」，绝不持 store、不 import boto3、不依赖执行环境。** Lambda handler 是 cloud 组合根（cold-start 读 env 造 adapter 注入纯 reconciler——**仍是组合根注入，不是 ports 内部 env-sniff 全局单例**，[0016](./0016-execution-architecture-core-lib-run-model.md) 禁的 GlobalConfigManager 反模式要在评审时守住别退化成它）；per-run 进程是 local 组合根。归约码作纯 core 函数被两宿主 import 复用 = 「不复制归约逻辑」的正解。

## Engine port 演进：pull-iterate → 增出 fire-and-forget（已实装）

`Engine.run_scope(job) → (WorkerHandle, Iterator[Event])` 是 **pull 式**（调用方线程迭代事件流；FargateEngine 为满足 `Iterator` 而在线程内轮询 DDB），**同步 `run` 路径仍用它、不变**。无状态路径是 **fire-and-forget**：worker 自写持久 sink、观察者补 `task_exited`、reconciler 读表——不再有「调用方持续迭代」。**实装形态**：`FargateEngine` 增出 `start_scope(job) → task_arn`（只 PutObject job + RunTask、不返事件迭代器）；`run_scope` 与 `start_scope` 共用抽出的 `_put_job_and_run_task`（起 task 单一真源）。**未改 `Engine` Protocol 本身**——`reconcile.Launcher` 是无状态路径专用的注入口（local=`SubprocessLauncher` 起子进程旁路落 SQLite / cloud=`CloudLauncher` 经 resolver 选 FargateEngine 调 `start_scope`），故 core 的 `reconcile.tick` 只认 `Launcher.launch(job)`、对「怎么起」无知，不必给 `Engine` Protocol 强加 `start_task`。**起 task 的能力（subprocess spawn / ECS RunTask）收进注入的 Launcher/Engine，core 绝不 import boto3/ecs**（reconcile.py 只 import core.model/ports/project）。

## 对 [0016](./0016-execution-architecture-core-lib-run-model.md) 的纠正：「核心不动」是过强断言

[0016](./0016-execution-architecture-core-lib-run-model.md) 三处（L114/210/225）断言「无状态化 = 加 adapter + 组合根换注入，核心与接口不动」。**本 ADR 纠正为分层两真值**：

- **(a) store/engine 后端替换**（local↔DDB/S3、subprocess↔Fargate）= 注入、核心不动——[0033](./0033-iac-aws-backend-and-composition-wiring.md) 已真部署真跑证实，**保留**。
- **(b) 无状态提交-收集**（本 ADR）= **驱动模型演进**：同步 `ThreadPoolExecutor` 循环解体为无状态事件驱动 tick、抽纯 `project()`/`plan_next()` 供两宿主复用、可能增 Engine port 形状、严格并发从进程内线程池迁到 store CAS——**核心与接口要动**。这比「只换 adapter」大得多，[0016](./0016-execution-architecture-core-lib-run-model.md)/[0026](./0026-schedule-module.md) 把 (a)(b) 混为一谈、over-claim 了。

存活的是**纯归约器**（`project`），消失的是**同步驱动循环**（ThreadPool/as_completed/abort_flag/fail-fast `_stop_all`/进程内并发闸）——后者在无状态路径重新宿主为 reconciler。同步 `run` 路径仍用现驱动循环（两种驱动模型并存，按命令分流）。

## 地基实测（2026-07-19，账户 000000000000/us-east-1；6 个真 Fargate task——其中 4 个构成 H1 退出场景矩阵——+ 真 DDB Streams/条件写；临时 PoC 脚手架验后即清、未入库）

moto 立即返回测不到事件投递/并发时序，健康网真跑不触发这些路径——故下列是「绿≠对」边界的唯一有效证据（临时 PoC 脚手架验后即清、未入库）：

- **H1 事件 payload 带 exitCode（4/4，含最硬的 SIGKILL 截断）**：正常退出 exitCode=0→payload 带 0；缺 job 非 0 退出=1→带 1；StopTask 软停=0→带 0；**忽略 SIGTERM 的 sleeper 被 SIGKILL 硬杀=137→payload 仍带 137**。结论：观察者从 STOPPED 事件读 exitCode 可靠（事件锚在 `stoppedAt`、已过 exitCode 落值窗口）→ 机制二「极薄观察者」成立、机制二兜底降为防御性冗余。
- **H2 延迟**：EventBridge→Lambda 投递 **0.6s**（近瞬时）；但端到端「worker 真停(`executionStoppedAt`)→可归约」= **~27s**，瓶颈全在 ECS 平台 `executionStoppedAt→stoppedAt` 清理开销（STOPPED 事件锚在 `stoppedAt`）。放大了 [0032](./0032-fargate-execution-environment.md) 记的 ~11s 平台滞后。**级联每步有 ~20-30s 固有尾延迟**——对异步跑批可接受，`status --wait` 会有此尾延迟，属已知特性。
- **H3/机制三/四 并发写序（真 DDB）**：HWM 条件写——B 写终态(hwm=20)后 A 用旧快照(hwm=10)迟到写被 `ConditionalCheckFailedException` 挡、终态未被刷回 running；同 hwm 重复写幂等。**DDB Streams 并发度=2**（4 job 触发 2 个并发 Lambda 实例）→ 坐实「并发 reconciler」前提真实、HWM 条件写用得上；**同 PK 严格保序**（每 job seq `[1..5]` 按序到达）。

**施工期已补真验（原「地基实测」时未覆盖的）**：`status --wait` 接力 + Stream 丢投 → **已真验**（禁用 kicker 的 runs-Stream mapping 确定性造卡 pending → status --wait invoke kicker kickoff → 救活 passed，见「重议闸门」丢投条）；`setsid` local 脱离 → **已真验**（local submit → per-run 进程脱离 CLI 后台推进 → CLI 退出后 status 读到 running/passed）；四机制 → core 单测（`test_reconcile.py`/`test_cloud_reconcile.py`/`test_project.py`）+ local/cloud 端到端真跑覆盖。仍留未做项见下「重议闸门」（如 level Stream 长期丢失率的量化、动态定时兜底规则）。

## 被拒方案（护栏，防未来重踩）

- **让 worker 自报退出事件**（省掉平台侧观察者）：拒——worker 可能 SIGKILL/崩溃/发完 scope_done 才退，没机会自报；「进程干净终止」本质只有平台/父进程可见（机制二）。
- **`task_exited` 共享 worker 数值 seq 段**：拒——观察者无 worker 的 seq 计数器，Query-max-then-write 撞号覆盖 `scope_done` / 造空号破断号检测（机制一）。
- **reconciler 靠全量重放天然幂等、投影写不加版本守卫**：拒——并发实例 stale 快照 lost-update 能把 finalized run 刷回 running；全量重放只保证派生幂等、不保证跨实例写序（机制三）。
- **把 CAS+RunTask+PutItem 与归约合成单一 core reconciler 组件**：拒——逼 core 持 store + 依赖执行环境、Engine port 长出启 task 职责，破 [0026](./0026-schedule-module.md) 纯 reducer（core 拆分节）。
- **让每个消费者各自 `project(events)→RunState`（绕过单一 reconciler 写者、如为求新鲜度让 `status` 直接投演 events）**：拒——多份推演逻辑必漂移（同一 events 在 status/WebUI/reconciler 各推一版、口径迟早分叉）；且各消费者写 RunState 会破单写者与 HWM/状态机条件写前提。外部只读 RunState、推演只在 reconciler 一处（「核心思想」单一读接口不变量）。
- **cloud submit 由 CLI 直接起首批 task（冷启动）**：拒（施工 P4d 初版这么做、后改）——让 submit 机器背 `ecs:RunTask` 权限，与本设计卖点「提交完就走、只需提交那一下的最小权限」相悖：submit 机器权限面越小越好（受限 CI runner / 临时凭证场景）。改由**kicker Lambda** 冷启动（见下），submit 机器权限收窄到只剩「runs 表写 + preflight」、不碰 ECS。
- **runs 表 Stream 直接触发 reconciler（复用同一 Lambda 做冷启动）**：拒——**自触发放大**：reconciler 每次推进都写 runs 表（`project_state` 条件写 + `finalize`），若 runs Stream 触发 reconciler，则它写 runs → 又触发自己 → 每个 run 生命周期空转 N 次（tick 幂等使无害、但持续无效唤醒 + 全量重放读放大）。用 Stream `INSERT`-only filter 能压，但那是「用 filter 补救本可避免的耦合」。改用**专用kicker Lambda**（只被 runs Stream 的 INSERT 触发、只起首批、**不写 runs 表**）——职责单一、无自触发，与退出观察者「专用薄 Lambda」同模式。reconciler 只被 events Stream 触发（worker 有进展才推进），两触发源职责不交叉。
- **定时器轮询推进**（EventBridge scheduled rule 每 N 秒 tick）：拒——idle 也 fire、空转烧钱，且要权衡「间隔短=延迟低但费 / 间隔长=省但收尾慢」这个不该存在的取舍。改用 ECS Task State Change + DDB Stream 事件驱动，idle 零调用（端到端流程 cloud）。
- **per-run 推进器也给 cloud**：拒（用户定）——cloud「扣笔记本下班」场景只靠 IaC 部署的事件驱动链，本机不留常驻推进器；per-run 仅 local 用。

## 重议闸门

- **level Stream/事件偶发丢投致级联断裂成真痛点** → 加安全网：submit 时 enable、finalize 时 disable 的**动态定时兜底规则**（仅在有活跑批时低频轮询、真 idle 时规则禁用=仍零调用），比常开定时器省。当前靠 `status --wait` 接力兜底，先不做。
  - **cloud 冷启动/中途丢投由 `status --wait` 无感接力兜底（施工 P4d 真跑遇到、已解决）**：任何事件丢投（首个 runs-INSERT 漏 → 卡 pending、无第二触发源踢；或中途 events 丢投 → 级联断）都由 cloud `status --wait` 兜底——它**检测卡住（状态连续 K 轮无变化）才** invoke kicker Lambda kickoff（**异步 fire-and-forget、秒级一脚即救活**，之后云端链自接管、可退出 status，见上「三触发源」cloud 侧；正常推进时不踢、避免无效 invoke）。踢 Lambda（非本机 tick）保「status 机器零 ECS 权限」：起 task 走 Lambda 的角色（有 RunTask/PassRole），status 机器只需 `lambda:InvokeFunction`。**kicker 名从 `--prefix` 确定性推理**（`{prefix}kicker`，复用 `names` 单一命名真源、cli↔IaC 同源，ADR 0033）——用户无需配、无感。幂等安全：invoke kicker，正常在跑时 tick 发现无 pending 即 no-op（CAS 挡重复起 / HWM 挡 stale，P2/P3 真 DDB 验），卡住时救回。故三触发源在 cloud 完整齐备：kicker（冷启动）/ reconciler（events Stream 主推进）/ `status --wait`（人工接力 kickoff）——**触发源齐备度与 local 对称，但「本机是否必须跑到底」不对称**（cloud kickoff 完可离场 / local 须本机跑到终态，见上「三触发源」2.）。**卡死救活已真验（施工确定性复现）**：临时禁用 kicker 的 runs-Stream event-source-mapping 模拟丢投 → submit 必卡 pending（kicker 收不到 INSERT、无第二触发源）→ `status --wait` invoke kicker kickoff → pending→running→passed 救活、`status --wait` 正常返回。此真验还抓出并修了一个真 bug：kicker 原只认 Stream records 的 event 格式、忽略直接 invoke 的 `{"run_id":...}` payload → status --wait 的 invoke 空转救不了（`runs:[]`）；修为 `_run_ids_from_runs_stream` 兼容两种 event 源（Stream records + 直接 kickoff）。
- **常驻调度服务 / WebUI 真需要** → RunState 读模型 + reconciler 已就位，加 adapter/宿主即可（[0016](./0016-execution-architecture-core-lib-run-model.md)「加 adapter + 换注入」在 (a) 类仍成立）。
- **本地 events sink 选型**：定 **SQLite**（表结构镜像 DDB events：PK=scope_id/SK=seq；`UPDATE...WHERE` 让 local 复刻 HWM 条件写、与 cloud 心智对称）。被拒 append-only JSONL——虽最简无依赖，但并发读写只能靠 append 原子性 + 容忍半行，无事务保证、无法复刻条件写逻辑。
