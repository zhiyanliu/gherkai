> **⚠️ 状态：WP3-B 主线已收尾、内容已全部吸收进 ADR，本文件待删（保留仅为审计过渡）。** 真跑数据表 + grace 校准结论 + ~12s=ECS 记录滞后 + 候选解法 A/B/C/D → [0032](../adr/0032-fargate-execution-environment.md)「真容器校准结论」；观测方法学 → `tools/events_wallclock.py`/`ecs_task_timing.py` docstring（自包含）；组合根接线/region-profile → [0016](../adr/0016-execution-architecture-core-lib-run-model.md) 决策 C / [0033](../adr/0033-iac-aws-backend-and-composition-wiring.md)。§6.6 是决策草稿（保留作演进史，以 ADR 0032 为准）。剩 §0-3/6-8 多为过程流水账（会话恢复上下文/施工进度），随删弃。
>
> 类型：会话恢复上下文（临时 staging；WP3-B 推进到稳定态后即删）
> 用途：因主循环反复出现「持续输出 court」故障，reset 新 session 时**第一件事加载本文件**，完整恢复上下文后继续 WP3-B。

# WP3-B 恢复上下文（reset 接手用）

## 0. 最重要的操作纪律（本次故障根因规避）

- **主循环反复出现「持续大量输出 court」的生成故障**：几乎每次「读完文件→准备做分析/规划/写正文长段」时触发，严重打断工作。
- **规避策略（务必遵守）**：
  1. **正文回复保持极短**。不写长篇分析/方案正文——长内容改为写进文件或用 Workflow 子 agent 结构化返回。
  2. **实质调研/方案产出走 Workflow 工具**（子 agent 经 schema 返回，绕开主循环故障）。ultracode 处于 ON，本就该用 Workflow。
  3. **workflow schema 的 property 键必须纯 ASCII**（`^[a-zA-Z0-9_.-]{1,64}$`）——中文键会导致 API 400（历史踩过）。
  4. 若正文又开始重复输出：立刻停止该 tool call，用一两句话报状态即可。
- 沟通/思考**一律中文**（项目 CLAUDE.md 要求）。

## 1. 项目与大目标

- 工作目录：`/Users/lzy/workspace/yaozhou/core`（git 仓库根是 `/Users/lzy/workspace/yaozhou`）。分支 `feat/v1.1-cloud`。
- 大目标：UI 测试框架**执行面上云**——worker 从本地 subprocess → AWS Fargate/ECS 容器。
- WP 进度：WP-S✅ → #7✅ → WP3-A✅ → WP0✅ → WP1✅ → **WP2✅（已 commit `6e21448`）** → **WP3-B（进行中，本文件主题）**。
- 导航总纲：`docs/journey/0000-fargate-cloud-progress.md`（第一份该读的进度文件）。

## 2. 当前任务：WP3-B（Fargate 特有韧性真容器校准）

**设计冻结 ADR = `docs/adr/0032-fargate-execution-environment.md`（Draft）。** 四个待解项：
- ① grace/stopTimeout 真实预算校准（**头号**，必须真跑烧钱标定）
- ② botocore retry vs grace 冲突（**已被 ADR 0029 超前解决**：上传/events 两路都 `max_attempts=0`+短超时，不再吃 grace；ADR 0032:28 描述已漂移待回校）
- ③ 上传错误分类升级 engine_error→network_error（**本质是诊断分类精度**：上传都在 scope_started 之后、越过重试域边界，升级也不会触发重试）
- ④ 孤儿产物恢复（Fargate 查 S3 vs 本地扫盘；**零实现**，且 task role 缺 `s3:ListBucket`）

**核心冲突**：Nova grace 下限 **180s**（`NOVA_ACT_TIMEOUT_S=120` + `NOVA_GRACE_MARGIN_S=60`，见 `cli/cli/compose.py:24-37/88`）> Fargate `stopTimeout` 上限 **120s**。（历史：改前 `stack.py` 是 `stop_timeout=None` = ECS 默认 **30s**，比 120 还小；prework① 已改成 `_resolve_stop_timeout` 默认 120、`-c stop_timeout=` 可配——见 §8。）

## 3. 用户已做的关键决策

- **不在乎 cost**。方向选定：**先做全部 prework（不烧钱）→ 直接连跑真 Fargate run-1 → run-2 → run-3 → 拿数据定 grace 解法 → 回落 ADR 0032**。
- 我（助手）的推荐已被采纳：**不做本地零 token 标定**（它是 subprocess 路径，测不到 Fargate 特有时序，去掉成本后失去意义）；也**不先落 ADR**（真跑后才有真决策取向）。
- AWS 资源**当前保留未 destroy**（用户要自己玩）。账户 `000000000000` / region `us-east-1`。清理命令 `cd iac_aws_backend && uv run cdk destroy -c use_default_vpc=true`（表/桶 RETAIN 需手动删）。

## 4. 调研结论（已完成，来自 workflow，可直接用）

**可观测性判定：能倒推，全走旁路信号（wire event 本身无 timestamp）。三条真值信号：**
- **单 act 墙钟** = events 表 item 的 `expires_at - 604800`（worker emit epoch，1s 分辨率，跨机一致，不受 core 轮询污染）。取同 scope 内相邻 step_started/step_done 之差。**不要用 `RunResult.StepResult.duration_ms`**（Fargate 下含 0.5s 轮询+最终一致抖动）。硬约束：`--assertion-votes 1` 才能拆出单 act（votes>1 会把 N 个 act 合进一个 step_done）。
- **会话释放耗时** = CloudWatch 日志行时间差：`signal received`（`run_scope.py:113`）→ `session shutdown complete`（`run_scope.py:633`），ms 级。**仅协作停止路径才产这两行**（须运行中发 StopTask 触发 SIGTERM）。
- **SIGTERM→退出耗时** = ECS DescribeTasks 的 `stoppingAt`/`executionStoppedAt`/`stoppedAt`（task STOPPED 后才全；当前 `fargate_engine.py:245-256` 只读 lastStatus/exitCode、**丢弃时间字段**）。

**180 的真实构成**：`act_timeout=120`（真跑标定折中，当前默认）+ `margin=60`（保守起点，涵盖单 step 最坏+会话释放+余量，注明「待真跑标定」）。**两者都是保守估计、非实测**——WP3-B 就是压这两个数。

**Fargate 侧 `handle.stop` 忽略 grace 参数**（`fargate_engine.py:57-64` 只发 StopTask），真实 grace 由 task-def `stopTimeout` 决定。故校准落点是 `stack.py`，非任何运行期参数。worker SIGTERM handler 是 **flag-only 软停**（只 set `_stop`、绝不 raise，避免撞 playwright greenlet），退出靠 act 安全点正常 return 退三层 with 释放会话；`stopTimeout` 只决定「多久后 ECS 补 SIGKILL」。

## 5. grace 冲突 4 个候选解法（真跑后定）

- **A｜压 margin**（60→实测会话释放值+小余量，改 `compose.py:27` 单点）。单靠 A 可能仍略>120，需配 B/C。
- **B｜压 act_timeout**（120→run-1 实测 P99 覆盖值，如 90）。牺牲长 act 容忍度（超时 act 被打断、不可重试）。
- **C｜证伪 180**（若 run-2/3 实测「act 中途 SIGTERM→shutdown complete」最坏 ≤120，则直接 `stop_timeout=120` 够用、无需改 act_timeout/margin）。
- **D｜接受 120 硬顶 + SIGKILL**：长 act 泄漏靠 AgentCore `sessionTimeoutSeconds` TTL 兜 + orphan S3 扫描兜产物。不动 act_timeout。

## 6. 真跑计划（3 次）

- **run-1（首跑，最省钱但不在乎 cost 可直接跑）**：`wikipedia_assertions --assertion-votes 1 --interrupt none` baseline，测单 act 墙钟分布，答「180 是否过保守」。无中断、最简单，也是观测方法学验证场。
- **run-2**：AI feature votes=1，**先改 stop_timeout=120 并 deploy**；起 worker→监听 events 表 step_started 出现（act in-flight）→手动 `aws ecs stop-task`，测会话释放墙钟 + DescribeTasks 时间字段。
- **run-3**：最坏档（step_started 后立即 StopTask，逼近 act 起点中断）+ 孤儿验证（`aws s3 ls` 对比应传产物，确认 session_summary.json 154B 等残留）。

## 6.5 真跑实测结果（run-1 + run-2 已跑，2026-07-12，账户 000000000000/us-east-1、stopTimeout 已 deploy=120）

**观测方法学已验证**：events 表 `expires_at-7d` 还原的单 act 墙钟，与 Nova SDK 独立报的 `time_worked_s` **逐 act 吻合**（run-1：墙钟 4/5/11/5s vs worked 4.0/4.6/10.7/5.1s，差 ~0.3-1s=轮询+编组开销）——旁路信号可信、不受 core 轮询污染。`tools/events_wallclock.py`（含 votes>1 MULTI-ACT 检测）+ `tools/ecs_task_timing.py`（DescribeTasks 时间字段派生）真数据上工作正常。

**run-1（baseline，无中断，`wikipedia_assertions --assertion-votes 1` novaact）**：单 act 墙钟分布 **min=4 / p50=5 / p90=9 / p99=10.8 / max=11s**（n=5 干净单 act）。→ **act 正常完成远低于 `NOVA_ACT_TIMEOUT_S=120`（差一个数量级），180 grace 高度过保守**。但这是「顺利路径」样本，非 grace 要覆盖的最坏（act 中途中断），最坏由 run-2 测。

**run-2（SIGTERM 落 AI act 中途，编排脚本自动抢 step_started 窗口）**：
- **关键教训**：act 仅 4-11s，**手动 StopTask 绝对抢不进 act 窗口**（第一次手动尝试落在 scope 已跑完之后，`stopCode=EssentialContainerExited`/exitCode=0/派生负数=无效样本）——必须 events step_started 出现的**毫秒级自动 StopTask**（`run2_orchestrator.py`，job tmp 里）。
- **有效样本时间线**（中断落 step 1 第一个 AI act in-flight，`stopCode=UserInitiated`、`exitCode=0` 干净退出、无 SIGKILL、无泄漏）：
  - StopTask→SIGTERM 送达容器 ≈ **1.1s**（ECS 调度延迟；`stoppingAt` 16:24:03.128 → `signal 15 received` 16:24:04.191）
  - **会话释放（`signal received`→`session shutdown complete`）= 1.65s**（act 到安全点 + 三层 with `__exit__` 释放 AgentCore 会话；CloudWatch 毫秒锚点 08:24:04.191→08:24:05.840）
  - shutdown complete→`executionStoppedAt` ≈ **11.3s**（**ECS 记录滞后、非 worker 耗时**——worker 在 shutdown complete 已退，见 §6.5「~12s 尾巴构成已拆定」）
  - **`stopping→executionStopped`（SIGTERM→退出真实耗时，stopTimeout 校准核心量）= 14.03s**
- **结论**：SIGTERM 落 act 中途，worker 干净退出 **≈14s ≪ stopTimeout=120 ≪ grace 下限 180**。

**run-3（3 个中断样本汇总，覆盖简单 act + 复合多步 act）**：

| 样本 | act 类型 | SIGTERM→退出 | 会话释放(signal→shutdown) | stopCode/exit |
|---|---|---|---|---|
| run-2b | 简单断言 act（中断早） | 14.0s | 1.65s | UserInitiated/0 |
| run-3a | 复合多步 act（`搜索并打开词条`） | 21.3s | 8.96s | UserInitiated/0 |
| run-3b | 复合多步 act（延迟 2s 中断） | 20.5s | 7.15s | UserInitiated/0 |

- **worker 3/3 干净退出**（exitCode=0、UserInitiated、无一 SIGKILL、无会话泄漏、CloudWatch 均见 `signal received`→`session shutdown complete`）——**ADR 0024 flag-only 软停契约在真 Fargate 下成立**。
- **SIGTERM→退出耗时 = 14~21s，两段构成**：① **会话释放（随 act 复杂度变）= 1.6~9s**（act 从中断点跑到安全点 + 三层 with `__exit__` 释放 AgentCore 会话；复合 act 更长）；② **ECS 记录延迟（平台固定，非 worker 耗时）≈ 11~12s**（`shutdown complete` 日志后到 `executionStoppedAt` 的静默——**已坐实是 ECS/Fargate 平台侧从「容器进程退出」到「记录 executionStoppedAt」的固有滞后，不是 worker teardown**，见下证据边界①的结论）。**故真实 SIGTERM→worker 退出比 `stopping→executionStopped` 显示的更快**（worker 在 shutdown complete 那刻已退）。
- **最坏实测 21.3s ≪ 120 ≪ 180**——**候选解法 C（证伪 180）得强支持**。
- **孤儿产物验证（run-3a scope `:9` 中断）**：中断落 step 1 复合 act 中途，worker 到安全点时 step 1 恰好完成（step_done passed）→ **act 边界抢传把 step 1 的 trajectory + trajectory.json 完整救回 S3**（363KB+377KB，ADR 0029 抢传在真 Fargate 下生效）；漏的只有 step 2（断言，未开始）+ `session_summary.json`（scope 末产物、中断时未到）——正是 ADR 0032 记的「固有残余」，可接受。**另一旁证**：中断 scope `:9` 的 worker 后，core schedule 照常起了 scope `:16` 的新 task 跑完（events scopes=2）——**单 scope worker 被停不影响其他 scope**（job=scope 粒度设计成立）。
- **~12s 尾巴构成已拆定 = ECS 记录延迟（非 worker teardown）**：CloudWatch 交叉验证——① `shutdown complete`（worker 最后一行 Python 日志）之后到 `executionStoppedAt` 之间**零 worker 日志**（worker 逻辑已跑完）；② 该静默段时长跨 4 样本高度恒定 **11.32 / 11.54 / 11.53 / 11.06s**，且**跨引擎**（Nova Python worker vs Midscene Node worker，teardown 路径完全不同）都 ~11s——若是 worker 自身 teardown（SDK atexit/boto 连接池），两引擎不可能都恰好 ~11s。**唯一解释 = 与 worker 无关的平台侧固定延迟**（ECS agent 检测容器退出并写时间戳的轮询/机制滞后）。故它是**测量滞后、非真实退出耗时**，真实退出更快、余量更大。
- **证据边界（残留）**：① 未测「数十秒级超长 act」（如慢网/复杂 SPA）——但会话释放随 act 线性增长、加固定 ~12s ECS 记录延迟，即便 act 到安全点要 30s 也才 ~42s，仍 ≪120（且这 ~12s 是测量滞后、真实退出更快）。

**run-4（Midscene 引擎中断，补全两引擎对称，`wikipedia_assertions --default-engine midscene`）**：

| 指标 | Midscene（run-4） | 对照 Nova |
|---|---|---|
| SIGTERM→退出 | **12.4s** | 14~21s |
| 会话释放（signal→shutdown） | **0.2s** | 1.6~9s |
| ECS 记录延迟（shutdown→executionStopped） | ~11s | ~11.5s |
| stopCode/exit | UserInitiated/0 | UserInitiated/0 |
| grace 下限 | `MIDSCENE_GRACE_MIN_S`=25s | 150s |

- **会话释放 0.2s**（vs Nova 1.6~9s）——**印证 ADR 0024 机制不对称**：Midscene Node 单线程事件循环、无 greenlet，`process.on(signal)` handler 作为回调排进事件循环，会话 Stop 几乎瞬时；Nova 要等 act 到安全点（greenlet 不能被打断）故更慢。
- **~11s ECS 记录延迟跨引擎一致**（Nova 11.32~11.54 / Midscene 11.06）——**坐实是平台侧记录 executionStoppedAt 的固有滞后、非 worker teardown**（若是 SDK teardown，Nova/Midscene 完全不同的 teardown 路径不可能都恰好 ~11s；且 shutdown complete 后零 worker 日志）。故它是测量滞后、worker 真实退出更快。
- **孤儿验证（Midscene report 抢传）**：中断落 step 1 之后，report（2.3MB）已被 step_done 安全点抢传上传 S3（ADR 0029 主路径生效）——中断在 step_done 之后故未触发 handler 兜底 snapshot 路径（那只在「首个/当前 act 中途、无 prior step_done」才需要，本次未落那格）。
- **Midscene grace 下限 25s vs 实测 12.4s → 25s 够用、有 ~2x 余量**，无需动。

## 6.6 WP3-B grace 解法决策（决策草稿，已落定 → 最终版见 ADR 0032 结论 4）

> **本节是决策推演草稿、保留作演进史,勿再据它维护**。最终结论已吸收进 ADR 0032「真容器校准结论」结论 4,并经对抗 review 修正了本草稿两处:① 下方 line 114「不同层→冲突不触发」的论证**被 review 推翻**（真相:subprocess 侧满足不变量、Fargate 侧对最坏长 act 结构性接受 SIGKILL+TTL 兜底,非「不冲突」）;② 「固定尾巴」实为 **ECS 记录滞后、非 worker 耗时**（见 §6.5）。以 ADR 0032 为准。

**采候选解法 C（证伪 180）为主 + 温和 A（压 margin）**：
- **`stopTimeout=120` 保留**（已 deploy）——实测最坏 21s，120 有 ~5x 余量，无需动。
- **`NOVA_GRACE_MARGIN_S` 60 可压**：实测「会话释放 + 固定尾巴」最坏 ~21s（含 12s 与 act 无关的固定开销 + ~9s 会话释放）。当前 grace 下限 = `act_timeout(120) + margin(60) = 180`，其中 margin 本意涵盖「单 step 最坏 + 会话释放 + 余量」——实测会话释放侧最坏仅 ~21s，**margin 60→30 都绰绰有余**（留 ~1.5x 余量）。→ grace 下限可从 180 降到 ~150。
- **`NOVA_ACT_TIMEOUT_S=120` 不动**（候选 B 不采）：它是「单 act 允许跑多久」的上界、与中断退出无关；压它会牺牲长 act 容忍度，而实测正常 act 才 4-12s、离 120 很远，没必要动。
- **净效果**：grace 下限 180→150，仍 > stopTimeout 上限 120——**冲突本质未消除**（grace 下限仍 > 120），但 ① 实测证明真实退出只需 21s，120 的 stopTimeout 足够 worker 干净退（SIGKILL 不会触发）；② core 侧 grace enforce 的 150 是「core 等 worker 的耐心」、Fargate 侧 120 是「ECS 补 SIGKILL 的时限」，两者语义不同层——core 等 150 而 Fargate 120 就 SIGKILL，但**实测 worker 21s 就退了、两个阈值都够**，冲突是理论的、非实际触发。**这条要在 ADR 0032 讲清楚**：不是把两个数调到相等，而是实测证明「真实退出 ≪ 两个阈值」使冲突不触发。
- **Midscene 侧（run-4 已验）**：`MIDSCENE_GRACE_MIN_S=25` vs 实测 SIGTERM→退出 12.4s（会话释放仅 0.2s + 12s 固定尾巴）→ **25s 够用、有 ~2x 余量，不动**。压 Nova margin 与 midscene 逻辑正交（`engine_min_grace` 按引擎分支、各取各的），互不影响。
- **仍 defer**：把 Nova `NOVA_GRACE_MARGIN_S` 60→30 的 code 改动 + ADR 0032 落定，作为 WP3-B 收尾的下一步。两引擎中断证据已齐（Nova 3 样本 + Midscene 1 样本），可支撑该决策。

## 7. 不烧钱 prework（三项均已完成 + 两轮对抗 review，见 §8）

1. **【必做·阻塞中断真跑】✅** `stop_timeout` 改成可配：`stack._resolve_stop_timeout`（默认 120、`-c stop_timeout=N` 覆盖、synth 期非整数/越界 `[1,120]` fail-fast）。测试 18 个（含边界 1/120/121/0/负/bool/float）全绿、synth 验证过。**尚未 `cdk deploy`**（改动在工作树、待 commit 后连真跑时一起 deploy）。
2. **【采数据前置】✅** 独立脚本 `tools/ecs_task_timing.py`（**不改** `_task_exit_code` 的 int|None 契约）：DescribeTasks 抓 `createdAt/startedAt/stoppingAt/executionStoppedAt/stoppedAt/stopCode/stoppedReason`，派生 SIGTERM→退出耗时（`stopping→executionStopped`）；`--stop-timeout` 告知生效值判 SIGKILL 截断、`--wait` 轮询到 STOPPED。
3. **✅** `tools/events_wallclock.py`：从 events 表按 `expires_at-7d` 还原 emit epoch、配对 step_started/step_done 算单 act 墙钟、出 p50/p90/p99；votes>1（MULTI-ACT）自动检测+排除出分布+告警（硬约束）、coarse≤1s 标注。

（其余非阻塞 prework：③错误分类可纯 code+单测；④orphan 恢复设计+moto+task role 加 `s3:ListBucket`；回校 ADR 0032:28 的 botocore 漂移——都可等真跑后或穿插做。）

## 8. 当前精确进度

> **WP3-B grace 主线已收尾**——本 journey 使命基本达成，决策已全部吸收进 ADR 0032（Accepted），可考虑归档/清理。

- **prework 三项完成 + 两轮对抗 review**（commit `a30e918`）；ADR 0016/0024 doc-health 回校（`36fd83f`）。
- **stopTimeout=120 已真 deploy**（`BackendStack-gherkai` UPDATE_COMPLETE，两 task-def rev 2 带 `stopTimeout:120`，已 describe-task-definition 核实）。
- **4 次真跑全完成**（run-1 baseline + run-2 简单 act 中断 + run-3a/3b 复合 act 中断 + run-4 Midscene 中断，结果见 §6.5）。
- **grace 解法已落定 + 落回 ADR 0032**：margin 60→30（下限 150）、stopTimeout=120、ACT_TIMEOUT_S/Midscene 25 不动；候选 B 明确否决；「~12s 尾巴 = ECS 记录滞后非 worker 耗时」已拆定。经对抗 review（12 CONFIRMED 全修，含结论 4 从「不同层不冲突」纠正为「Fargate 侧结构性接受 D+TTL」）。相关 commit 见 git log（`f0eac6a` 起）。
- **剩余（非阻塞 backlog，均记 ADR 0032「留口子」）**：退化网络下超时封顶实测、孤儿产物主动扫盘（task role 缺 `s3:ListBucket`）、上传错误分类升级、CI 推 ECR。
- 编排脚本 `run2_orchestrator.py` 在 job tmp（`$CLAUDE_JOB_DIR/tmp`）——一次性实验脚手架、非长期工具（依赖 events step_started 抢窗口的时序）；随 job tmp 清理即可，无需固化。

## 9. 相关文件精确指针

- `cli/cli/compose.py`：`NOVA_ACT_TIMEOUT_S`(24) / `NOVA_GRACE_MARGIN_S`(27) / `MIDSCENE_GRACE_MIN_S`(37) / `engine_min_grace`(77-91)。
- `core/core/schedule.py`：grace enforce(421-425) / `handle.stop` 调用点(389) / `ScheduleOpts`(130-136)。
- `core/core/adapters/fargate_engine.py`：`FargateWorkerHandle.stop` 忽略 grace(57-64) / `_task_exit_code`(245-256) / `_read_events`(轮询,196-243) / `_final_drain`(219-243,已含分页)。
- `core/core/adapters/subprocess_engine.py`：`stop(grace)` 真用 grace(38-46)。
- `engines/novaact/lib/event_sink.py`：`_EVENTS_TTL_S=7*24*60*60`(29) / PutItem 写 `expires_at`(95)。
- `engines/novaact/worker/run_scope.py`：SIGTERM handler `_on_signal`(104-115) / `signal received` log(113) / `session shutdown complete` log(633) / step_started emit(204) / `cost.time_worked_s`(118-125)。
- `engines/novaact/lib/artifact_upload.py`：`Config(connect_timeout=5,read_timeout=10,retries={max_attempts:0})`(63)。
- `iac_aws_backend/stack.py`：`_resolve_stop_timeout`（stopTimeout 可配、默认 `DEFAULT_STOP_TIMEOUT_S=120`、上限 `FARGATE_STOP_TIMEOUT_MAX_S=120`）/ `_one_task_def`（`stop_timeout=Duration.seconds(self.stop_timeout_s)`）/ awslogs LogDriver / task role 权限 `_grant_task_role`（S3 只 Get/Put/AbortMultipartUpload、**无 List**）。
- `tools/ecs_task_timing.py` / `tools/events_wallclock.py`：prework②③ 采数据脚本（见 §7）。
- `docs/adr/0032-fargate-execution-environment.md`：待解项四条（24-30 行）。
- feature 用例：`features/` 下 6 个（`deterministic_anchor`=零 token、`wikipedia_*`=AI）。

## 10. 环境约定（CLAUDE.md + 会话约束）

- Python engines/novaact 用 `.venv`；uv 工程（cli/iac_aws_backend）用 `uv run`、`uv add`，**不裸 pip**。core 测试 `cd core && .venv/bin/python -m pytest`。
- Node engines/midscene 用本地 `npm`、不 `-g`。
- **不 commit `.claude/`**；只删 session 创建的文件。
- commit message 结尾 `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`。改 code 前先落 ADR。commit 前两轮对抗 review（workflow 分维度 finder + 对抗验证）。
- 临时文件放 `$CLAUDE_JOB_DIR/tmp`（本 session 是 `/Users/lzy/.claude/jobs/161b2585/tmp`，新 session 会不同）。
- 工作节奏：每 WP 按「设计冻结（落 ADR）→ 实现 → 两轮对抗 review → commit」。
