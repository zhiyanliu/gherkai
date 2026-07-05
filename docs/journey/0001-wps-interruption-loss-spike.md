# WP-S 中断丢失实测预演：Nova greenlet 卡死 + 两腿产物丢失

> **类型：** Journey / 调查证据（**非 ADR**）。记"我们实测发现了什么、证据是什么、结论指向哪"，供后续处理这些问题时作单一事实源。**不记决策**——决策待真处理时落进相应 ADR（候选：0024 终止契约、0032 中断韧性）。
> **日期：** 2026-07-04　**背景：** Fargate 化 breakdown 的 WP-S（中断丢失实测预演），见任务 WP-S。
> **栈：** subprocess+cloud（真 AgentCore 会话 + 真 S3），是 Fargate 的忠实预演（[ADR 0029](../adr/0029-engine-artifacts-to-s3.md)）。

## 为什么做这个 spike

Fargate 化前，[ADR 0032](../adr/0032-fargate-execution-environment.md) 把"容器盘停即销毁的中断丢失"列为**头号待解项**，但它是"待实测"状态。WP-S 用现有 subprocess+cloud 栈预演中断（subprocess 下盘不销毁、可观测），量化：中断时丢多少产物、SIGTERM→干净退出要多久（grace 预算）、以及"加抢传能救回多少"。**盘销毁本身是已知结论无须实测**；真正待测的是"SIGTERM 落下时上传/清理来不来得及"这条时序，subprocess 测得到。

## 实测方法

- harness（`$CLAUDE_JOB_DIR/tmp/wps_harness.py`，spike 产物、不入仓）忠实复现 `SubprocessEngine` adapter 的 spawn 环境：自建 events pipe + `EVENTS_FD`、注入 `NOVA_LOGS_DIR`/`MIDSCENE_RUN_DIR` + `ARTIFACT_S3_BUCKET`/`ARTIFACT_S3_PREFIX`。
- job 用真实 `core.scope.plan` + `wire.job_to_line` 生成（不手搓 JSON，防 schema 漂移）。靶 feature = `wikipedia_assertions`（单 scope 5 step，含建连/AI 动作/AI 断言，跑约 110s）。
- 按事件时机外部 `kill -TERM` 命中 4 个中断点，中断后快照"盘上有什么 vs S3 有什么"，差集 = **Fargate 盘销毁时会丢的**。并测 grace 秒数（SIGTERM→worker 退出实测耗时）。
- spike 专用桶 `yaozhou-spike-wps-000000000000`（隔离，跑完可删）。

## 数据表（引擎 × 中断时机）

baseline（不中断，Nova）：5 step 全跑完 → scope 末 flush 上传 9 文件（4 act ×（html+json）+ session_summary，~1.9MB）→ rmtree 删本地，**盘零残留、S3 完整**。符合 [ADR 0029](../adr/0029-engine-artifacts-to-s3.md) 两级上传（reportRef 实时传 + 剩余 scope 末 flush）。这是差集的分母。

| 引擎 | 中断时机 | exit | grace(s) | hung | 盘→S3 丢失 | 关键现象 |
|---|---|---|---|---|---|---|
| Nova | connect（建连早期） | **1** | 0.13 | no | 0 | **发现 #1**：`Workflow()` 构造期 SIGTERM 落在 `try/except _Terminated` 之外 → 裸 traceback → exit 1 → adapter 归 `engine_error`（误报） |
| Nova | act（mid-act） | **-9** | 20.2 | **yes** | 0 | **发现 #2**：greenlet 无限切换死循环、100% CPU、进程永不自退，只能 SIGKILL 兜底 |
| Nova | between（step 边界） | 0 | 4.6 | no | 0 | ✅ 干净退、三层 with `__exit__` 跑完、会话释放 |
| Nova | scope_end（flush 前） | 0 | 2.5 | no | **4 文件 / 930 KB** | **发现 #3**：中断落在 emit scope_done + flush 前 → flush 不跑 → 全部 `_trajectory.json` 丢（`.html` 靠实时传活下来） |
| Midscene | connect | 0 | 1.9 | no | 0 | ✅ 干净退 |
| Midscene | act（mid-act） | 0 | 3.4 | no | **5 文件 / 2.0 MB** | **发现 #4**：`agent.destroy()` 前中断 → report 尚未 finalize/上传 → **整个 2MB `playwright-*.html` 报告丢** + log |
| Midscene | between | 0 | 3.4 | no | **5 文件 / 2.0 MB** | 同 #4（destroy 前） |
| Midscene | scope_end | 0 | 3.4 | no | 13 文件 / 38 KB | **发现 #5**：SIGTERM handler 是 `process.on("SIGTERM", async)` **软停、不抢占主流程** → 主流程跑完 destroy+传 report+emit scope_done（t+3s）才收尾 → report 抢在前面传成功，只丢 `.log` |

## 五个发现

### 发现 #2（最重）：Nova mid-act SIGTERM 概率性 greenlet 死循环 —— 现有生产 bug

**现象**：SIGTERM 落在 nova `act()` 执行途中（playwright 同步 API 的 greenlet 切换途中），worker 卡进 `greenlet::UserGreenlet::g_switch` / `check_switch_allowed` / `find_main_greenlet_in_lineage` 无限循环，100% CPU，永不自退，只能等 SIGKILL（实测复现 2 次，`sample` 采样确认栈帧）。

**根因（机制层，据 greenlet C++ 源码 + CPython signal 文档 + 业界旁证）**：CPython 信号只在主线程字节码边界"凭空"抛异常 + greenlet 的 `g_switchstack` 有一段**非可重入、无异常安全**的关键区。SIGTERM handler `raise _Terminated()` 的异步异常若恰好落在该关键区，撕裂 greenlet 状态机（`switching_thread_state` 停在中间态、`_main_greenlet`/started 缓存与实际不符、父链落脚点丢失）。**为何死转（无兜底）**：`check_switch_allowed`→`find_main_greenlet_in_lineage` 沿 `_parent` 链找 main greenlet、`g_switch` 的 `target=target->parent()` 循环，二者终止都依赖 lineage/started/`_main_greenlet` 自洽；而 `g_switch` 循环**没有"状态不自洽即退出"的兜底**，半切换态下无落脚点 → 原地空转（= 采样到的三个栈帧无限循环的直接原因）。**旁证（加固"结构性、业界公认反模式"）**：playwright-python #1968（标 not-planned）/#1843/#3031、greenlet #495（shutdown 崩溃）/#518（switch 持临界区死锁）；反证：gevent 用 `gevent.signal_handler` 走协作式回调、从不"在 handler 里 raise"。

**是现有生产 bug（不是 spike 独有），三条触发路径**（code 行号锚点见「证据出处」节）：
- **超时**：`--timeout` 默认 300s；schedule 心跳兜底（0.5s）保证 deadline 到点 ~0.5s 内触发 `_stop()`→SIGTERM，**无须 worker 吐事件**。act 跑超 300s 时 SIGTERM 必落 mid-act。这是超时的正常语义。
- **fail-fast**：`_stop_all()`→`w._stop()` 由主线程对所有在跑 worker 直接下发 SIGTERM，不看 sibling 此刻在干嘛 → 正在 mid-act 的 sibling 立即中招。
- **Ctrl-C**：`Popen` 未加 `start_new_session`，worker 与 cli 同进程组，终端 SIGINT 直达 worker；worker 只装 SIGTERM handler、**没装 SIGINT handler** → 默认处理 mid-act 抛 `KeyboardInterrupt`（同类 BaseException 异步 raise）。

**校准（不夸大）**：**不是每次 mid-act SIGTERM 必卡**——异步异常须恰好落在 `g_switchstack` 非可重入关键区才撕裂状态机（落别处则 `_Terminated` 正常冒泡、`__exit__` 跑完、会话干净释放）。准确表述：**以非零、结构性反复、当前未量化的概率触发**；一旦触发即不可恢复。**触发率未量化**（决定"多久泄漏一个会话"）。

**后果链（code 确证）**：卡死 → `proc.wait(grace)` 必超时（无论 grace 多大，无限循环不自退）→ `proc.kill()` SIGKILL → 三层 with `__exit__` 全跳过 → **AgentCore 浏览器会话服务端存活继续计费**（手动 `nova.close()` 都关不掉、何况 SIGKILL 连它都不走，[ADR 0024](../adr/0024-worker-core-protocol.md) 终止契约节明写）→ core 侧**无 reaper**（全仓 grep `stop_browser|delete_session|reap` 零命中）→ 仅在 RunStore 留 `session_id` 血缘（不消费、不回收）→ **每次命中 = 一个泄漏烧钱的孤儿会话，直到 AWS 服务端 TTL 兜底**；grace 窗口内还 100% CPU 空占一核。**注：退出码语义不被此路径污染**——SIGKILL 尾路径不经 `_read_events` 的 rc 检查（`subprocess_engine.py:100-122`），超时 job 的 ABORTED/ERROR 归类在 schedule 主侧判定仍正确（与发现 #1 的 connect 早期误报 engine_error 不同，那是 try 外裸 traceback 走了 rc 检查）。

**"grace 够不够"在此场景无意义**：卡死是无限循环，任何有限 grace 只决定"白等多久再 SIGKILL"，终点恒为 SIGKILL + 会话泄漏。

### 发现 #3 / #4：两腿都有严重中断丢失，但形态不同

- **Nova（#3）**：reportRef 文件（act `.html`）实时传（step_done 那刻），**剩余 `_trajectory.json` 全靠 scope 末 flush**。中断落 flush 前 → 全部 trajectory.json 丢（实测 scope_end 丢 930KB，全是 `.json` 数据载体；`.html` 渲染页活着）。
- **Midscene（#4）**：report 是**增量写盘**（跑中已在盘上），但 `uploader.toReportRef(agent.reportFile)` 只在 `agent.destroy()` 之后调一次。中断落 destroy 前 → **整个 `playwright-*.html` 报告丢**。**关键校准（盘上残留实测印证）**：中断时盘上**已有截至最后一个已返回 AI 调用的合法可打开报告**（act-midway 中断实测 2094271 字节，为 5 步跑完版 4.68MB 的约一半——1 步 vs 5 步）——即"report 早就在盘上、只是不全"，丢的原因**不是"没生成"，而是"上传点（destroy 后）太晚"**。补救方向（与 Nova 对称、把抢传点提前到 step 安全点）见下「Midscene 补救方向」节。

subprocess 下这些"没传的"还留本地（[ADR 0028](../adr/0028-transient-network-ssl-resilience.md) #3 可手动找）；**Fargate 盘销毁 = 直接丢**。这就是 [ADR 0032](../adr/0032-fargate-execution-environment.md) 头号待解项的量化证据。

### 发现 #5：两腿中断模型根本不同（对 WP3 设计是核心输入）

- **Nova = 同步 raise**：`_on_sigterm` 直接 `raise _Terminated()`（BaseException 穿透 `except Exception`），指望冒泡触发三层 with `__exit__`。**抢占正在跑的主流程**——正因如此才会撞 greenlet 关键区卡死。
- **Midscene = 异步软停**：`process.on("SIGTERM", async …)` 不打断正在跑的 `main()`，主流程自然跑完（destroy→传 report→scope_done）后 handler 才收尾。**不抢占、不卡死**，但"软"意味着 mid-act 的 kill 要等当前 act 跑完（实测 scope_end 格 kill 后主流程又跑了 3s 才停）。

### 发现 #1：Nova 建连早期 SIGTERM 误报 engine_error

`Workflow()` 构造（`main()` 早期）在 `try/except _Terminated` 之外，此处 SIGTERM → handler raise 无人 catch → 裸 traceback + exit 1 → adapter 当异常退出归 `engine_error`。此刻无会话泄漏（会话还没起），但退出码语义错（应是 aborted/干净退，却成 engine_error）。Fargate 下启动早期被 StopTask 会同样误报。

## 抢传验证（实测证实 act 边界抢传有效）

在 Nova `_run_step` 的每个 step_done 安全点（act 已返回、不在 greenlet 切换途中）加实验探针（`WPS_PRESEND_JSON=1` 开关，已回滚不入仓）：对该 act 配套 `_trajectory.json` 也调 `_uploader.to_report_ref` 实时传（幂等记账、scope 末 flush 自动跳过）。复跑 scope_end 中断对比：

| 场景 | 中断结局 | flush 是否跑 | 丢失 |
|---|---|---|---|
| 无探针（对照，`scope_end-r2`） | 干净退（grace 2.5s） | 中断落 flush 前、**未跑** | **4 文件 / 930 KB**（全部 trajectory.json） |
| 有探针（`scope_end-presend`） | **恰好撞 greenlet 卡死 → SIGKILL**（最严酷） | SIGKILL 强杀、**绝无机会跑** | **0**（S3 已全 8 文件：4 act ×(html+json)） |

**关键**：有探针那次**恰好也触发了 greenlet 卡死**（`hung=true`、exit -9）——最严酷场景（worker 卡死、SIGKILL、flush 绝无机会、`__exit__` 全跳过），**却零丢失**。因为每步的 json 在 act 边界就已抢传，scope 末 flush 根本不需要跑。这实测证实：**act 边界抢传有效，且不依赖优雅停**——它在卡死发生前就已完成，正是"锚 act 边界 vs 锚中断路径"的本质区别（中断路径抢传遇卡死就没了）。

（附带证据：同样的 scope_end 时机，对照组干净退、探针组卡死——同一中断点一次干净一次卡死，是发现 #2「概率性」的额外佐证。）

## 结论指向（**方向判断，非决策**；决策待处理时落 ADR）

> **落实状态（回填）**：下列方向判断中，#2「中断模型改 flag-only」+ act 有界返回 + grace 上调已作为**决策落进 ADR 0024/0028** 并**在 Nova worker 实现**（`run_scope.py` flag-only handler、per-act timeout；两条被拒护栏见 ADR 0024：raise 模型 / asyncio 化）——故 #2 里「拟…待重估」的措辞是调查当时的方向快照，现已闭合。#3 孤儿 reaper **未采纳**（改用 AgentCore session TTL 兜底，见 ADR 0024「已接受代价」）。#1 抢传归 WP3（未做）。以下各条保留为调查当时的方向记录。

1. **"SIGTERM handler 里抢传"对 Nova 结构性走不通，"act 边界抢传"实测有效**：抢传代码若挂在 raise 之后的 `__exit__`/handler 里，raise 本身卡死就到不了抢传；而锚在 act 边界安全点则在卡死前就完成（上「抢传验证」实测：SIGKILL 卡死场景仍零丢失）。[ADR 0032](../adr/0032-fargate-execution-environment.md) 现在对 Midscene 写的"中断路径读 reportFile 抢传"倾向需据此重估——**抢传动作必须锚在 act 边界的安全点**（两次 act 之间、切换的安全落脚点），不能锚在中断路径。这是"signal handler raise 中断 greenlet 同步调用"这一业界公认反模式的直接后果，**无法靠改 raise 时机/异常类型修复**。
2. **中断模型倾向**：handler 从"raise 异常"改为"置停止标志（async-signal-safe，可选写自管道）+ 在 act 边界安全点主动检查优雅退出"；单 act 时长上限交给引擎自带 timeout（在切换安全点抛，不经异步信号）；进程级 SIGKILL / StopTask 看门狗保留为"已卡死"的最后兜底（会话泄漏是其固有代价）。**⚠️ 动摇既有 ADR**：[ADR 0024](../adr/0024-worker-core-protocol.md)「终止契约」节现记的 Nova 机制正是"handler `raise _Terminated` → 三层 with `__exit__`"（并把"不在 handler sys.exit"记为反模式），而发现 #2 判定"handler 里 raise"本身是卡死根因——本方向拟以"置停止标志"取代它。真落时须同步更新 0024 该节 + Status 头（此处只标"该决策被本调查动摇、待重估"，不越 scope 记决策，与本文对 0032:18 的处理对称）。
3. **孤儿会话 reaper**：core 侧可用 RunStore 已记的 `session_id` 调 `StopBrowserSession` 回收，兜住"SIGKILL 后会话仍泄漏"的残余。独立于中断模型的补偿控制。
4. **对 Fargate 的加重**：subprocess 下 SIGKILL 是有效兜底（进程死、本地盘产物还在）；Fargate 下 `stopTimeout`（≤120s 常量）对 greenlet 卡死同样无意义（worker 永不自退），且盘销毁使"可手动补救"退路消失、产物直接丢。严重性从"成本/可观测的已知代价"升级为"数据丢失"。

## Midscene 补救方向（SDK 深挖 + 盘上残留实测交叉印证；供 WP3 单独设计）

**分叉已定（SDK 源码确证，非推测；@midscene/core 1.9.8，行号随 SDK 升级漂、以符号为准）**：Midscene report 是**增量 append 边跑边写盘**——构造时定路径（`agent.js:890-897`）→ 首个 AI task 写完整自包含 HTML 模板（`report-generator.js:151-153`）→ 每步 append dump（`:157`）→ SDK 的 `onTaskUpdate` hook 每步 `await flush()`（`agent.js:879`）。`destroy()` 只做冗余 finalize（把 last execution 再 append 一遍、靠读取侧去重），**不做正文批量生成**。**故 `aiAct/aiBoolean` 返回时（= step_done 安全点），该步 dump 已落盘且 flush 完毕**——盘上永远是"截至最后一个已返回 AI 调用"的合法可打开报告（act-midway 中断实测 2094271 字节 ≈ 5 步跑完版 4.68MB 的一半）。**~2MB 单文件成因**：`generateReport:true`（`run-scope.ts:249`）是增量写盘总开关（false → `nullReportGenerator` 永不落盘，`report-generator.js:64`）；worker 未传 outputFormat → `screenshotMode='inline'`（`report-generator.js:71`）截图内联进单 HTML——这也是"每步重传整份"带宽重的根因。

**"全丢"真因在 worker 不抢，非 SDK 缺产物**：SIGTERM handler（`run-scope.ts:209-223`）只清会话就 `process.exit`、不碰 report；catch/finally 不 flush 不传；`toReportRef(reportFile)` 只在 `destroy()` 之后调一次（`run-scope.ts:303-306`）。Fargate 盘销毁 → 盘上那份合法 partial HTML 随之蒸发。

**方向 A（主推）：每 step_done 安全点增量抢传**——与 Nova"锚安全点、幂等抢传"心智对称。中断（含 SIGKILL 硬杀在下一 act 中途）时 S3 已有"上一步为止"版本，**损失窗口收敛到至多一个 in-flight act**。带宽敏感时降粒度为 **A'（scenario_done 抢传）** 或节流（每 K 步 / T 秒）。**抢传源两选**：① 读盘上 `reportFile`；② `agent.reportHTMLString()`（`agent.js:195-197`）从内存 dump 同步拼完整 HTML、**不碰盘、不需 destroy**（另有 `writeOutActionDumps` `agent.js:198-205`，但本身不 await flush）。**为何必须锚 step_done、不能 act 中途抢**：act 中途 `readFileSync` 可能撞上 `appendFile`（`report-generator.js:157`）写到一半的截断尾；step_done 处 hook 已 `await flush()`（`agent.js:879`）、act 已返回，读到的是干净一致文件（选 ② reportHTMLString 天然避开半写风险）。**方向 B（handler 内兜底抢传）仅作廉价补充**——软停下 handler 读不到 act 中途状态，长-act-被-SIGKILL 场景救不回，不能替代 A。**被拒方向 D**：每步存 dump JSON 事后重建 report / 周期性 destroy 重建——report 本就增量落盘、盘上现成有合法 HTML，事后重建是重复造轮子（防未来重进坑）。

**Midscene 独有、Nova 没有的三个实现缺口（WP3 须单独解）**：
1. **单文件单调增长 vs 每-act 独立文件**：Nova 每 act 产**新** trajectory.json（distinct key 天然幂等、累积不覆盖）；Midscene 是**一份**不断变大的 HTML，抢传 = 反复 **overwrite 同一 S3 key**（overwrite-latest，最新即最全）。带宽模型 = 每次传整份增长文件 ≠ Nova 小文件累加。
2. **uploader 幂等守卫直接冲突**：`toReportRef` 的 `uploaded` 守卫（`artifact-upload.mts:74`）专挡"同路径重传"，与增量抢传相悖 → WP3 须加一条绕守卫的 snapshot 上传路径（暴露 `uploadOne`/独立方法，S3 同 key 覆盖）；**不能复用 `flushAndCleanup`**——它成功后 `rmSync` 删整目录，中途抢传会误删本地/打断在跑的 main。
3. **agent 引用作用域 + reportFile 空窗**：`agent` 是 `main()` 局部，模块级 handler 看不到；须上提引用，并处理 `reportFile` 在首个 task 更新前为 `undefined` 的窗口。

（对称心智：两腿都是"上传锚 step 安全点、不等结束"；不对称点全在 Midscene 的"单份大文件增量"性质。）

## 待进一步验证

- **greenlet 卡死触发率**：每次 mid-act SIGTERM 命中关键区的概率（决定泄漏频度/紧急度）。当前只确认"可复现、结构性反复"，未统计命中率。
- **Midscene 增量抢传带宽实测**：方向 A 每步重传整份增长 report 的累计 egress（几十步 scope 可能几十 MB）——粒度/节流取舍待真做时量。
- **act 边界抢传的有效性**：WP-S 抢传验证改测"act 返回后即传"能否把 scope_end 那批 trajectory.json / Midscene report 救回（原计划的"中断路径抢传"已被机制判定走不通、放弃）。
- **Ctrl-C（SIGINT）**：机制同类（BaseException 异步 raise），需实测确认 SIGINT 直达 worker + 默认处理 mid-act unwind 是否同样撞 greenlet 陷阱。

## 证据出处

- harness / 各格 log：spike 临时产物、不入仓、不可复取——**数据以本文表格为准**（字节/文件/grace 已内联，自包含）。
- greenlet 卡死采样：`sample` 采到 `g_switch`/`check_switch_allowed`/`find_main_greenlet_in_lineage` 循环栈帧。
- 结论经"code 路径核查 + greenlet 机制核查 + 严重性综合"三方对抗核验得出（关键结论已内联本文正文）。

### code 锚点（Nova / 生产路径，均入仓 git 可跟踪；行号随 code 演进，以符号为准）

- **生产 SIGTERM 触发路径**：
  - 超时：`core/core/schedule.py:244`（deadline 查）→ `:246`（_stop）→ `:380`（handle.stop→grace）→ `core/core/adapters/subprocess_engine.py:42`（terminate）；心跳兜底 `schedule.py:58-108`（`:94` q.get、`:96` yield HEARTBEAT、`:135` 0.5s），保证 deadline 到点 ~0.5s 内触发、不需 worker 吐事件；`--timeout` 默认 300s（`cli/cli/__main__.py:48`）。
  - fail-fast：`schedule.py:441`（_stop_all）→ `:423`（w._stop）；`:251` abort_flag 冗余触点。
  - Ctrl-C：`subprocess_engine.py:73-88`（Popen 无 `start_new_session`，worker 与 cli 同进程组，SIGINT 直达；worker 未装 SIGINT handler）。
- **Nova worker 中断处理（改造前现场，行号为发现 #2 当时的旧 raise 结构、已随 flag-only 改造失效）**：旧 `run_scope.py` SIGTERM handler raise `_Terminated`、`_Terminated`/`_NetworkExhausted` 继承 BaseException 穿透 `except Exception`、三层 with（cdp_session/NovaAct/Workflow）、`except _Terminated` 干净退点。**flag-only 落实后**这套 raise 结构已删（`_Terminated`/`_NetworkExhausted` 移除、handler 改模块级 `_on_signal` 只置 `_stop`），当前实现见 ADR 0024「终止契约」+ code（以符号为准，勿引旧行号）。
- **grace 预算基准（对照 grace 表列，WP-S 实测时的值）**：实测时 cli `--grace` 默认 **10.0s**、`ScheduleOpts` 默认 **5.0s**。表中实测 grace（干净退 2.5-4.6s、卡死 20.2s 兜底）应对照此预算读。**注（flag-only 落实后已变）**：这两个默认值经 review 发现对 Nova 恒违约（10/5 « act_timeout 120），已改为「按引擎推导的下限」（Nova ≈ act_timeout+margin、core enforce grace≥下限），详见 [ADR 0024](../adr/0024-worker-core-protocol.md)「grace 硬约束」条——此处 10/5 是实测当时的历史值、勿引作当前默认。
- **SDK 锚点（Midscene，@midscene/core 1.9.8，在 gitignore 的 node_modules、行号随 SDK 升级漂、以符号为准）**：见下「Midscene 补救方向」内引。
