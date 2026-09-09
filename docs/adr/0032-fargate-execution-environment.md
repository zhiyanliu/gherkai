# Fargate 执行环境：容器盘停即销毁逼出的中断丢失、grace、即时上传

> **Status:** Accepted —— `FargateEngine` 执行 adapter 已实装（job-in 走 S3、events-out 走 DDB events 表）；**组合根接线 + IaC 归 [0033](./0033-iac-aws-backend-and-composition-wiring.md)**（已编码+真部署）；**grace/stopTimeout + 中断韧性已真容器标定**（4 次真跑 Nova×3+Midscene×1，见下「真容器校准结论」）。**决策 A（[0016](./0016-execution-architecture-core-lib-run-model.md)）下 Fargate = `--backend cloud` 的执行实态、非可选增强**——用户侧云端档就是跑在 Fargate。本 ADR 收「Fargate/ECS 执行环境**特有**」的问题：容器盘停即销毁的 artifact 中断丢失、grace/stopTimeout 预算、act 粒度即时上传。上传机制本身见 [0029](./0029-engine-artifacts-to-s3.md)（由注入驱动、不绑执行环境、已在 subprocess 预演环境实现，[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 B）；远程事件传输见 [0024](./0024-worker-core-protocol.md)「远程传输演进」；为何倾向 Fargate 见 [0017](./0017-cloud-execution-fargate-over-runtime.md)。

## 定位：只收「执行环境特有」的一条边

云端化的三条正交边（[0029](./0029-engine-artifacts-to-s3.md) 已划；此处「正交」=关注点分解，非用户 CLI 旋钮——用户只有 `--backend` 一个旋钮，[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）里，本 ADR 只管 **③ Fargate 执行环境特有**——即"worker 从本地子进程搬进 ECS 容器"这一步**新引入**的问题。**不重述**上传机制（[0029](./0029-engine-artifacts-to-s3.md)：worker 手动上传、key 镜像 run 树、删本地——已在 subprocess 预演环境做好，Fargate 直接复用）与远程传输（[0024](./0024-worker-core-protocol.md)：job-in 走 S3、events-out 走 DDB events 表（PutItem/Query）、stop→StopTask、退出码→DescribeTasks）。

**核心差异**：subprocess 模式 worker 死了产物还在本地盘（[0028](./0028-transient-network-ssl-resilience.md)「留口子」『卡死现场 trajectory 不自动归集』条：超时被杀 scope 的 trajectory 至少"留在磁盘"、靠 `session_id` 可手动找）；**Fargate 容器盘停即销毁**——这把"干净结束才上传成功"的脆弱性从"可手动补救"升级成"直接丢"。

## 最大风险：中断丢失在 Fargate 下严重升级（真做前头号待解）

**这是 SDK 调查比"能不能传"更要紧的发现。** [0029](./0029-engine-artifacts-to-s3.md) 的上传（第一期=结束批量）挂在"干净结束"路径——Fargate 下 SIGTERM 中途被杀、容器盘随即销毁，产物直接丢：

- **Nova**：per-act 文件在 `_act()` 的 `finally`→`RunInfoCompiler.compile()` 即写盘（非批量、非原子——`.html`/`.json` 分多次 `open` 顺序写，中断可留"孤零 `.html`"）；结束批量上传若在 SIGTERM 后来不及跑完 → 未上传部分随容器盘销毁而丢。
- **Midscene**：report 边跑边 `appendFile`（每 task flush），中断时盘上已是"含已完成 task 的部分有效 html"；但 SIGTERM handler **只做会话 cleanup、不触达 report**（不上传中途 report）→ 中断产物随容器盘销毁而丢。补救（把抢传提前到 step 安全点）见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」+ 下「抢传能力」条。

**丢失量级实测**（subprocess+cloud 预演量化，未加抢传时；Fargate 下即真丢，subprocess 下留本地盘）：Nova `scope_end` 中断丢 **4 份 `_trajectory.json` / ~930KB**（`.html` 靠实时传活着，`.json` 数据载体全靠 scope 末 flush、中断落 flush 前全丢）；Midscene `act`/`between` 中断丢**整份 report ~2.0MB**（act-midway 实测 2094271 字节 ≈ 5 步跑完版 4.68MB 的一半——report 早已增量在盘、丢因是上传点 `destroy` 后太晚，非没生成）。这两个量级（~930KB/~2.0MB，对照 scope 末产物 `session_summary.json` 仅 ~154B）是「中断丢失严重性」与下「抢传能力」设计的量化依据——「抢传后丢失归零」的结论正相对这两个量级才有意义。

**结论倾向**：Fargate 模式**不能纯靠 [0029](./0029-engine-artifacts-to-s3.md) 的"结束批量上传"**，需 **act 边界即时抢传**缩小丢失窗口，且要求 Fargate `stopTimeout`(grace) 足够长。

**抢传能力已提前在 subprocess+cloud 建好并实测验证（为 Fargate 忠实预演，见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」）**——**主路径锚在每个 step_done 安全点**（act 已返回，不在信号 handler 内跑抢传：中断路径对 Nova 会撞 greenlet、见 [0024](./0024-worker-core-protocol.md)，故 Nova 抢传**只**在安全点）：Nova 每 act 返回后传配套 `_trajectory.json`（distinct key 幂等）；Midscene 每 step_done 对增量增长的单份 report.html 做 `snapshotReport`（overwrite 同 key + mtime 去重）。**Midscene 额外在 SIGTERM handler（`interruptSnapshot`）里追加一次 best-effort `snapshotReport`（cleanup 之后、会话释放优先）**——这是「首个/当前 act 中途、无 prior step_done」这格唯一救得回 report 的路径；**Node 事件循环回调能安全 await 一次读盘上传，Nova 因 greenlet 做不到——关键不对称（见 [0024](./0024-worker-core-protocol.md)「Midscene worker」条）**。实测（subprocess+cloud 预演 + 真 Fargate 复验）：安全点抢传 + handler 兜底组合下，scope_end 中断（甚至 SIGKILL 卡死）下 per-act `trajectory.json`/report 丢失归零。仍余 `session_summary.json` 这一 scope 末产物无法被 act 边界抢传覆盖——判定为可接受残余，理由与措辞见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」条『固有残余』，不在此复述。

**真 Fargate 校准（`stopTimeout`/grace 预算 + 中断抢传 + 干净退出）已完成**（4 次真跑，见下「真容器校准结论」）。**抢传能力与真 Fargate 校准分开——抢传已在 subprocess+cloud 预演，真 Fargate 已复验生效。** 孤儿产物主动扫盘 reaper **经分析否决**（Fargate 下物理不成立——没传 S3 的残余随容器盘销毁、查 S3 捞不回，详见下「Fargate 特有问题：处置结论」孤儿 reaper 条）；**退化网络下「超时快速失败、不拖爆 grace」已真验 ✅**（见下「Fargate 特有问题：处置结论」botocore retry 条）。至此 Fargate 特有韧性 backlog 全部收敛（做/真验/否决各有归属）。

## 真容器校准结论（4 次真跑，2026-07-12，真实 AWS 账户/us-east-1、stopTimeout=120 已 deploy）

**实测数据（4 次真跑，2026-07-12，真实 AWS 账户/us-east-1；`wikipedia_assertions`/`wikipedia_robustness` × Nova/Midscene，`--assertion-votes 1`，编排脚本毫秒级抢 events `step_started` 窗口发 StopTask）：**

| 量 | Nova（3 中断样本） | Midscene（1 样本） | 校准对象 |
|---|---|---|---|
| act 正常完成墙钟 | 4~11s（p99=10.8，run-1 baseline） | — | 对照 `NOVA_ACT_TIMEOUT_S`=120 |
| **SIGTERM→退出**（`stopping→executionStopped`） | 14 / 21.3 / 20.5s | 12.4s | 对照 `stopTimeout`=120 |
| 会话释放（`signal received`→`session shutdown complete`） | 1.6 / 9.0 / 7.2s | **0.2s** | 随 act 复杂度 / 引擎模型变 |
| ECS 记录延迟（`shutdown complete`→`executionStopped`） | ~11.5s | ~11s | 平台固定滞后、非 worker 耗时（跨 4 样本恒定 11.06~11.54s、跨引擎一致 → 测量滞后，见结论 2） |
| 退出码 / stopCode | 全 exit 0 / UserInitiated | exit 0 / UserInitiated | 干净退出、无 SIGKILL、无泄漏 |

**四条稳定结论：**

1. **flag-only 软停契约在真 Fargate 成立**：4 次中断真跑（Nova×3+Midscene×1）4/4 干净退出（exit 0、CloudWatch 均见 `signal received`→`session shutdown complete`）——无一被 stopTimeout 补的 SIGKILL 截断、无会话泄漏。[0024](./0024-worker-core-protocol.md) 终止契约得真容器复验。

2. **机制不对称得实测印证**（[0024](./0024-worker-core-protocol.md)「Midscene worker」条预言）：Midscene 会话释放 0.2s（Node 事件循环、signal handler 回调即时跑），Nova 1.6~9s（greenlet 不能被打断、须等 act 到安全点才检测 flag）。SIGTERM→退出的可变部分 = 会话释放段，随 act 复杂度线性增长。**`stopping→executionStopped` 里另有 ~11s 与 act/引擎均无关的固定段**：CloudWatch 证实它是 `shutdown complete`（worker 最后一行日志）之后的**纯静默**（worker 已退），且跨 4 样本恒定 11.06~11.54s、Nova/Midscene 一致——**坐实为 ECS/Fargate 记录 `executionStoppedAt` 的平台侧固有滞后、非 worker teardown**。故 `stopping→executionStopped` 是 worker 真实退出耗时的**上界（含测量滞后）**，真实退出更快。**此 ~11s 滞后是 `FargateEngine._read_events` 每 scope 收尾要吃的固定成本**：读到 scope_done 后仍须等 `DescribeTasks` STOPPED 读 `exitCode`（[0024](./0024-worker-core-protocol.md)「事件流结束信号」条——退出码正确性优先于收尾延迟，「scope_done 即 break 省 11s」被否决），这 ~11s 是收尾一次性延迟、不影响流式期进度（事件早经 Query yield）。

3. **`stopTimeout=120` 校准落定、保留**：最坏实测 SIGTERM→退出 21s ≪ 120，有 ~5x 余量。**适用面注记**：本校准（连同 grace 链路）只在**有人发停止**时生效——三路推进器都有这样的发起者：同步 `run` 的 job 预算到点 `handle.stop`、local detached launcher deadline timer 的 `handle.stop`、cloud detached 超时处置的 `StopTask`（哨兵 reason），外加任何路径上人工的 `StopTask`。job timeout 已是产品级设定、三路各自 enforce——见 [0034](./0034-detached-batch-reconciler.md)「job timeout」节。**做成 CDK context `-c stop_timeout=N` 可配**（`stack._resolve_stop_timeout`，默认 120、synth 期越界 `[1,120]` fail-fast），便于未来再标定；`FargateWorkerHandle.stop` 忽略运行期 grace、真实宽限即由此常量决定。

4. **grace 下限 vs stopTimeout 的冲突：subprocess 侧解决、Fargate 侧对最坏长 act 结构性接受（D+TTL 兜底）**。组合根 `engine_min_grace` 给 Nova 的 grace 下限 = `ACT_TIMEOUT_S+margin`。**要区分两条执行路径**（不能混为「不同层所以不冲突」——那只对 subprocess 成立）：

   - **subprocess 路径（local）**：`SubprocessWorkerHandle.stop` **真用** grace（SIGTERM→等 grace→SIGKILL，退出经 `proc.wait()`、无 ECS 的 ~11s 记录滞后）。压 margin 60→30 后下限 = 120+30 = **150s**，满足 [0024](./0024-worker-core-protocol.md) 不变量 `grace ≥ act_timeout + margin`——最坏长 act（跑满 `ACT_TIMEOUT_S`=120s 才到安全点）+ 会话释放(~9s) ≈ 129s < 150s，能容纳、不泄漏（比 Fargate 侧更宽裕，因无平台记录滞后）。

   - **Fargate 路径（cloud）**：`FargateWorkerHandle.stop` **忽略** grace，真实宽限 = task-def 期 `stopTimeout`、Fargate 平台硬顶 **120s**。这里 `stopTimeout=120 = ACT_TIMEOUT_S`、**margin=0**，**结构上不满足** `grace ≥ act_timeout + margin`。**关键：`ACT_TIMEOUT_S` 是「单次 `nova.act()`/`act_get()` 调用」的墙钟上界，非 step 上界**——flag-only 软停下，SIGTERM 只需等**命中时那一次 in-flight act 调用**跑到安全点（投票 step 的循环每圈顶检测 `_stop` 即 break、不跑完剩余票，见 `run_scope.py`，故不叠加成 N×120）。**故最坏情形 = SIGTERM 落在一次刚开始、会跑满 `ACT_TIMEOUT_S`(120s) 才返回的 act 早期**：Fargate 会在 120s 补 SIGKILL、此时该 act 尚未到安全点 → `cdp_session.__exit__` 跑不完 → 会话释放落空（泄漏，靠 AgentCore `sessionTimeoutSeconds` TTL 兜底，[0024](./0024-worker-core-protocol.md)「已接受代价」）+ act 边界抢传被截断（产物丢——已接受残余，reaper 经分析否决，见下「Fargate 特有问题：处置结论」孤儿 reaper 条）。这本质是**候选解法 D（接受 120 硬顶 + 最坏长 act 的 SIGKILL）**，非「无冲突」。

   **候选解法 B（压 `ACT_TIMEOUT_S` < 120 使 stopTimeout ≥ act_timeout+margin）—— 明确否决（非「暂不采」）**：B 的方向是**让功能护栏（单 act 允许跑多久）去迁就基础设施限制（Fargate stopTimeout 硬顶 120）——本末倒置**。`ACT_TIMEOUT_S` 的语义是「一次 AI act 的合理墙钟上界」，取值应由「act 正常需要多久」决定（是 AI 能力/页面复杂度的函数），**与 Fargate 的 120s 硬顶无关**；为了让不变量在 Fargate 侧成立去压它，会把一个正常需要 100s 的 act 提前打断判超时（不可重试），是拿真实功能损失换一个低频残余的消除。且 `ACT_TIMEOUT_S` 本就 **env 可覆盖**（`NOVA_ACT_TIMEOUT_S`）——真遇到需要更长 act 的场景，是**调这个 env**、而非改 grace/stopTimeout 逻辑。**故 `ACT_TIMEOUT_S=120` 默认不动、且不因 Fargate 冲突而压**。选 D 而非 B 的正面理由：① 触发需「act 跑到 ≥~110s ∧ SIGTERM 恰落其前 ~10s」的低频组合——实测正常 act 仅 4~12s、离 120s 上限一个数量级，真实分布下极罕见；② 代价有 TTL 兜底（泄漏有上界、不会计费失控）；产物大头已由 act 边界抢传保全、残余经权衡接受（reaper 否决，见下「Fargate 特有问题：处置结论」）。

   **实测覆盖边界（诚实声明）**：4 次真跑的 act 均短（正常 4~11s、最坏 SIGTERM→退出 21s ≪ 120），**未撞上上述最坏长 act 情形**——即实测证明的是「典型/短 act 分布下 SIGKILL 不触发」，**非**「任何 act 下都不触发」。最坏长 act 的 Fargate SIGKILL 是**已识别、经权衡接受的结构性残余**（D+兜底），非被实测排除。

   **据此的 code 决策**：Nova `NOVA_GRACE_MARGIN_S` **60→30**（下限 180→150，主要收益在 subprocess 路径满足不变量 + 留 ~1.5x 余量；Fargate 路径 grace 被忽略、此改动不影响其行为）；**`ACT_TIMEOUT_S=120` 不动**（见上②③）；**Midscene `MIDSCENE_GRACE_MIN_S=25` 不动**（实测 12.4s、~2x 余量；Midscene 无 greenlet、会话释放 0.2s，长 act 下也远快于 Nova）。

## Fargate 特有问题：处置结论

- **botocore/aws-sdk 默认 retry 与 grace 冲突（**已解决 + 退化网络真验 ✅**）**：上传/events 两路都已对 grace 封顶，**两腿同一策略 = 关 SDK 重试 + 单次墙钟封顶**：**Nova** 靠 boto `Config`（`retries={"max_attempts": 0}` + `connect_timeout=5`/`read_timeout=10`）；**Midscene** 靠三个 SDK client 的 `maxAttempts: 1`（aws-sdk-js v3 默认 3）+ `AbortSignal.timeout(10s)` 对整个 send 硬性封顶（attempts 关重试、AbortSignal 兜墙钟，两者并存；[0029](./0029-engine-artifacts-to-s3.md) ArtifactUploader / [0024](./0024-worker-core-protocol.md) EventSink / JobSource）。两腿都不吃 grace、快速失败封顶。**退化网络真验（两腿 × 两种退化形态，2026-07）**：直接用两腿各自的超时 Config 造 client、对退化 endpoint 真调掐秒（比跑完整 worker 更聚焦——超时是 boto/Node 层行为、不依赖业务逻辑）：① **connect（黑洞不可路由地址 `10.255.255.1`）**：Nova 5.01s、Midscene 5.02s 快速失败；② **read（本地 TCP 服务器 accept 后不响应）**：Nova 11.00s（read_timeout=10+握手）、Midscene 10.00s（`AbortSignal` 精确 10s）。四条均**快速失败、超时封顶生效、墙钟不叠加**（Nova 因 `max_attempts=0` 无重试可叠；Midscene 真验当时尚未关重试、10.00s 是 `AbortSignal` 到点 abort 掉整个 send 连同其内部重试，故同样非 ×2；此后 Midscene 亦加 `maxAttempts: 1`，AbortSignal 保留作墙钟兜底）、远 < grace(120s)——证「退化网络下不拖爆 grace」（正是本项目亲历「退出被慢上传拖住」要防的）。moto 立即返回测不到此、健康网真跑不触发超时路径，故此真验是该「绿≠对」边界的唯一有效证据。
- **上传失败处理（已实现 ✅，两层）**：原记「上传失败=`engine_error`、诊断精度是否升级 `network_error`」。摸清后落地为两层：
  - **层1 分类（Nova step 内已顺带解决）**：`_run_step` 内 trajectory reportRef 上传失败被其 `except` 捕获、经 `_classify_act_error`→`_is_transient_network` 判——**S3 网络失败（ConnectTimeout/ReadTimeout/EndpointConnection/5xx/ConnectionError）已判 `network_error`**（[0028](./0028-transient-network-ssl-resilience.md) 白名单扩容顺带覆盖，实测确认），只 AccessDenied 这类真配置错才 `engine_error`。上传越过重试域边界（scope_started 之后），升级仅诊断、不触发重试。
  - **层2 降级（本次实现，两腿对称）**：**scope 级 report/summary 上传失败改 best-effort——吞+log、不带该 reportRef、不拖垮已判定的 scope**（Nova `session_summary` 的 `to_report_ref` 调用点 try、Midscene `toReportRef(reportFile)` 调用点 try→不 `throw`→不 fatal exit）。理由：此刻 scope 判定已 emit 完，report/summary 是「锦上添花」（summary 是数字汇总、report 是人看视图），不该因其上传失败（多为 S3 网络瞬时）把已跑完的 scope 拖成 `engine_error`/worker fatal。对齐同文件抢传/flush 的 best-effort，也对齐 [0029](./0029-engine-artifacts-to-s3.md)「判定真值 > 报告产物」的优先级。**与 step 内 trajectory 的强保证不同**（trajectory 是判定现场证据、`to_report_ref` 失败仍抛可观测），故只降级 scope 级两处调用点、不动 `to_report_ref`/`toReportRef` 本身。
- **孤儿产物主动扫盘 reaper（**经分析不实现——Fargate 下物理不成立**，护栏防重进坑）**：曾设想「Engine adapter 中断收尾主动扫盘、Fargate 查 S3 已传哪些、捞回中断残余」。**分析后否决——不是成本问题，是 Fargate 下捞不回**：
  - **物理约束**：Fargate 容器盘**停即销毁**（本 ADR 头号差异）。worker 没传 S3 的残余随盘一起没了——「查 S3」只能确认**已传的**、**捞不回没传的**（S3 上根本不存在、容器盘也销毁了）。reaper 在真会丢的场景（Fargate）里无物可捞。
  - **能传的已不需要 reaper**：Nova trajectory / Midscene report（MB 大头）已被 **act 边界抢传实时传 S3**（真跑验证归零），中断时也在 S3——不靠 reaper。
  - **真正"没传的"残余物理够不着**：`session_summary.json`（~154B，仅 `_stop()` 写、中断时可能连盘都没写）+ 最坏长 act 被 SIGKILL 截断的 in-flight 产物——都是「没传 S3 + 盘销毁」= 物理消失，reaper 无从捞。
  - **subprocess 侧残余留本地盘、能扫回，但那本就不算丢**（[0028](./0028-transient-network-ssl-resilience.md)「留口子」『卡死现场 trajectory』条：留盘、靠 `session_id` 可手动找），不"需要"自动 reaper。
  - **已有兜底足够**：act 边界抢传缩小窗口（大头归零）+ 会话 TTL + `session_id` 手动定位。**故不实现，也不为它扩 task role 的 `s3:ListBucket`**（与 IAM 最小权限收窄一致，[0033](./0033-iac-aws-backend-and-composition-wiring.md)）。
  - **重议闸门**：若未来把 worker 产物落点从「容器盘」改为「持久卷（EFS）/ 实时流式传」使中断残余不随盘销毁 → 那时残余可被事后扫回，reaper 才有物可捞、才重议。当前容器盘模型下，reaper 是伪需求。

## 重议

- 若中断即时上传仍挡不住高频丢产物 → 另议（如云浏览器侧落盘 / 边录边传的流式 sink）。
- 若 workload 形态变化使 Fargate 不再是执行面首选（[0017](./0017-cloud-execution-fargate-over-runtime.md) 翻盘条件）→ 本 ADR 的容器特有假设需重估。
