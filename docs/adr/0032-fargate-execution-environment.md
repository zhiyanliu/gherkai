# Fargate 执行环境：容器盘停即销毁逼出的中断丢失、grace、即时上传

> **Status:** Accepted —— `FargateEngine` 执行 adapter 已实装（job-in 走 S3、events-out 走 DDB events 表）；**组合根接线 + IaC 归 [0033](./0033-iac-aws-backend-and-composition-wiring.md)**（已编码+真部署）；**grace/stopTimeout + 中断韧性已真容器标定**（4 次真跑 Nova×3+Midscene×1，见下「真容器校准结论」）。**决策 A（[0016](./0016-execution-architecture-core-lib-run-model.md)）下 Fargate = `--backend cloud` 的执行实态、非可选增强**——用户侧云端档就是跑在 Fargate。本 ADR 收「Fargate/ECS 执行环境**特有**」的问题：容器盘停即销毁的 artifact 中断丢失、grace/stopTimeout 预算、act 粒度即时上传。上传机制本身见 [0029](./0029-engine-artifacts-to-s3.md)（由注入驱动、不绑执行环境、已在 subprocess 预演环境实现，[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 B）；远程事件传输见 [0024](./0024-worker-core-protocol.md)「远程传输演进」；为何倾向 Fargate 见 [0017](./0017-cloud-execution-fargate-over-runtime.md)。

## 定位：只收「执行环境特有」的一条边

云端化的三条正交边（[0029](./0029-engine-artifacts-to-s3.md) 已划；此处「正交」=关注点分解，非用户 CLI 旋钮——用户只有 `--backend` 一个旋钮，[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）里，本 ADR 只管 **③ Fargate 执行环境特有**——即"worker 从本地子进程搬进 ECS 容器"这一步**新引入**的问题。**不重述**上传机制（[0029](./0029-engine-artifacts-to-s3.md)：worker 手动上传、key 镜像 run 树、删本地——已在 subprocess 预演环境做好，Fargate 直接复用）与远程传输（[0024](./0024-worker-core-protocol.md)：job-in 走 S3、events-out 走 DDB events 表（PutItem/Query）、stop→StopTask、退出码→DescribeTasks）。

**核心差异**：subprocess 模式 worker 死了产物还在本地盘（[0028](./0028-transient-network-ssl-resilience.md)「留口子」『卡死现场 trajectory 不自动归集』条：超时被杀 scope 的 trajectory 至少"留在磁盘"、靠 `session_id` 可手动找）；**Fargate 容器盘停即销毁**——这把"干净结束才上传成功"的脆弱性从"可手动补救"升级成"直接丢"。

## 最大风险：中断丢失在 Fargate 下严重升级（真做前头号待解）

**这是 SDK 调查比"能不能传"更要紧的发现。** [0029](./0029-engine-artifacts-to-s3.md) 的上传（第一期=结束批量）挂在"干净结束"路径——Fargate 下 SIGTERM 中途被杀、容器盘随即销毁，产物直接丢：

- **Nova**：per-act 文件在 `_act()` 的 `finally`→`RunInfoCompiler.compile()` 即写盘（非批量、非原子——`.html`/`.json` 分多次 `open` 顺序写，中断可留"孤零 `.html`"）；结束批量上传若在 SIGTERM 后来不及跑完 → 未上传部分随容器盘销毁而丢。
- **Midscene**：report 边跑边 `appendFile`（每 task flush），中断时盘上已是"含已完成 task 的部分有效 html"；但 SIGTERM handler **只做会话 cleanup、不触达 report**（不上传中途 report）→ 中断产物随容器盘销毁而丢。补救（把抢传提前到 step 安全点）见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」+ 下「抢传能力」条。

**结论倾向**：Fargate 模式**不能纯靠 [0029](./0029-engine-artifacts-to-s3.md) 的"结束批量上传"**，需 **act 边界即时抢传**缩小丢失窗口，且要求 Fargate `stopTimeout`(grace) 足够长。

**抢传能力已提前在 subprocess+cloud 建好并实测验证（为 Fargate 忠实预演，见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」）**——**主路径锚在每个 step_done 安全点**（act 已返回，不在信号 handler 内跑抢传：中断路径对 Nova 会撞 greenlet、见 [0024](./0024-worker-core-protocol.md)，故 Nova 抢传**只**在安全点）：Nova 每 act 返回后传配套 `_trajectory.json`（distinct key 幂等）；Midscene 每 step_done 对增量增长的单份 report.html 做 `snapshot`（overwrite 同 key + mtime 去重）。**Midscene 额外在 SIGTERM handler 里追加一次 best-effort `snapshot`（cleanup 之后、会话释放优先）**——这是「首个/当前 act 中途、无 prior step_done」这格唯一救得回 report 的路径；**Node 事件循环回调能安全 await 一次读盘上传，Nova 因 greenlet 做不到——关键不对称（见 [0024](./0024-worker-core-protocol.md)「Midscene worker」条）**。实测（WP-S subprocess+cloud 预演 + WP3-B 真 Fargate 复验）：安全点抢传 + handler 兜底组合下，scope_end 中断（甚至 SIGKILL 卡死）下 per-act `trajectory.json`/report 丢失归零。仍余 `session_summary.json` 这一 scope 末产物无法被 act 边界抢传覆盖——判定为可接受残余，理由与措辞见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」条『固有残余』，不在此复述。

**真 Fargate 校准（`stopTimeout`/grace 预算 + 中断抢传 + 干净退出）已完成**（4 次真跑，见下「真容器校准结论」）。**抢传能力与真 Fargate 校准分开——抢传已在 subprocess+cloud 预演，真 Fargate 已复验生效。** 仍留待的只剩：上传幂等/可续传在**退化网络**下实测（真跑用的是健康网络）、孤儿产物恢复的**主动扫盘实现**（Fargate 查 S3 已传哪些 vs subprocess 本地扫目录——当前靠 act 边界抢传缩小窗口，未做主动 reaper）。

## 真容器校准结论（4 次真跑，2026-07-12，账户 000000000000/us-east-1、stopTimeout=120 已 deploy）

**实测数据（4 次真跑，2026-07-12，账户 000000000000/us-east-1；`wikipedia_assertions`/`wikipedia_robustness` × Nova/Midscene，`--assertion-votes 1`，编排脚本毫秒级抢 events `step_started` 窗口发 StopTask）：**

| 量 | Nova（3 中断样本） | Midscene（1 样本） | 校准对象 |
|---|---|---|---|
| act 正常完成墙钟 | 4~11s（p99=10.8，run-1 baseline） | — | 对照 `NOVA_ACT_TIMEOUT_S`=120 |
| **SIGTERM→退出**（`stopping→executionStopped`） | 14 / 21.3 / 20.5s | 12.4s | 对照 `stopTimeout`=120 |
| 会话释放（`signal received`→`session shutdown complete`） | 1.6 / 9.0 / 7.2s | **0.2s** | 随 act 复杂度 / 引擎模型变 |
| 进程收尾固定尾巴 | ~12s | ~12s | ECS 记录 + 进程退出的引擎无关开销 |
| 退出码 / stopCode | 全 exit 0 / UserInitiated | exit 0 / UserInitiated | 干净退出、无 SIGKILL、无泄漏 |

**四条稳定结论：**

1. **flag-only 软停契约在真 Fargate 成立**：4 次中断真跑（Nova×3+Midscene×1）4/4 干净退出（exit 0、CloudWatch 均见 `signal received`→`session shutdown complete`）——无一被 stopTimeout 补的 SIGKILL 截断、无会话泄漏。[0024](./0024-worker-core-protocol.md) 终止契约得真容器复验。

2. **机制不对称得实测印证**（[0024](./0024-worker-core-protocol.md)「Midscene worker」条预言）：Midscene 会话释放 0.2s（Node 事件循环、signal handler 回调即时跑），Nova 1.6~9s（greenlet 不能被打断、须等 act 到安全点才检测 flag）。SIGTERM→退出的可变部分 = 会话释放段，随 act 复杂度线性增长；固定 ~12s 尾巴两引擎一致、与 act 无关。

3. **`stopTimeout=120` 校准落定、保留**：最坏实测 SIGTERM→退出 21s ≪ 120，有 ~5x 余量。**做成 CDK context `-c stop_timeout=N` 可配**（`stack._resolve_stop_timeout`，默认 120、synth 期越界 `[1,120]` fail-fast），便于未来再标定；`FargateWorkerHandle.stop` 忽略运行期 grace、真实宽限即由此常量决定。

4. **grace 下限 vs stopTimeout 的冲突：subprocess 侧解决、Fargate 侧对最坏长 act 结构性接受（D+TTL 兜底）**。组合根 `engine_min_grace` 给 Nova 的 grace 下限 = `ACT_TIMEOUT_S+margin`。**要区分两条执行路径**（不能混为「不同层所以不冲突」——那只对 subprocess 成立）：

   - **subprocess 路径（local）**：`SubprocessWorkerHandle.stop` **真用** grace（SIGTERM→等 grace→SIGKILL），core 等满 grace 下限才杀。压 margin 60→30 后下限 = 120+30 = **150s**，满足 [0024](./0024-worker-core-protocol.md) 不变量 `grace ≥ act_timeout + margin`——最坏长 act（跑满 `ACT_TIMEOUT_S`=120s 才到安全点）+ 会话释放(~9s) + 固定尾巴(~12s) ≈ 141s < 150s，能容纳、不泄漏。

   - **Fargate 路径（cloud）**：`FargateWorkerHandle.stop` **忽略** grace，真实宽限 = task-def 期 `stopTimeout`、Fargate 平台硬顶 **120s**。这里 `stopTimeout=120 = ACT_TIMEOUT_S`、**margin=0**，**结构上不满足** `grace ≥ act_timeout + margin`——**故对「SIGTERM 落在一个会跑满 ~120s 才返回的 act 早期」这一最坏情形，Fargate 会在 120s 补 SIGKILL、此时 act 尚未到安全点 → `cdp_session.__exit__` 跑不完 → 会话释放落空（泄漏，靠 AgentCore `sessionTimeoutSeconds` TTL 兜底，[0024](./0024-worker-core-protocol.md)「已接受代价」）+ act 边界抢传被截断（产物丢，归下「孤儿产物恢复」backlog）**。这本质是**候选解法 D（接受 120 硬顶 + 最坏长 act 的 SIGKILL）**，非「无冲突」。

   **为何仍接受、不采 B（压 `ACT_TIMEOUT_S` < 120 使 stopTimeout ≥ act_timeout+margin）**：① 触发需「act 跑到 ≥~110s ∧ SIGTERM 恰落其前 ~10s」的低频组合——实测正常 act 仅 4~12s、离 120s 上限一个数量级，真实分布下极罕见；② 代价有 TTL + orphan backlog 两层兜底（泄漏有上界、非无限烧钱）；③ 压 `ACT_TIMEOUT_S` 会牺牲长 act 容忍度（长 act 被提前打断、不可重试），代价更实。**故 `ACT_TIMEOUT_S=120` 不动**。

   **实测覆盖边界（诚实声明）**：4 次真跑的 act 均短（正常 4~11s、最坏 SIGTERM→退出 21s ≪ 120），**未撞上上述最坏长 act 情形**——即实测证明的是「典型/短 act 分布下 SIGKILL 不触发」，**非**「任何 act 下都不触发」。最坏长 act 的 Fargate SIGKILL 是**已识别、经权衡接受的结构性残余**（D+兜底），非被实测排除。

   **据此的 code 决策**：Nova `NOVA_GRACE_MARGIN_S` **60→30**（下限 180→150，主要收益在 subprocess 路径满足不变量 + 留 ~1.5x 余量；Fargate 路径 grace 被忽略、此改动不影响其行为）；**`ACT_TIMEOUT_S=120` 不动**（见上②③）；**Midscene `MIDSCENE_GRACE_MIN_S=25` 不动**（实测 12.4s、~2x 余量；Midscene 无 greenlet、会话释放 0.2s，长 act 下也远快于 Nova）。

## 留口子 / 待真做时定（Fargate 特有）

- **~~即时上传粒度~~（✅ 已定 + 真跑复验）**：act 边界即时抢传（主路径锚 step_done 安全点 + Midscene handler 兜底），非结束批量——见上「抢传能力」条。真跑复验：Nova trajectory / Midscene report 中断后均救回 S3（见上「真容器校准结论」孤儿验证）。
- **~~grace / stopTimeout 预算~~（✅ 已真容器标定）**：见上「真容器校准结论」。`stopTimeout=120`（可配）；Nova grace 下限 margin 60→30（下限 180→150）；Midscene 25 不动。「grace 下限 > stopTimeout 上限」的关系经实测厘清：**subprocess 侧满足不变量、Fargate 侧对最坏长 act 结构性接受（D+TTL 兜底）**（结论 4，非「不同层所以不冲突」）。历史背景：`handle.stop(grace_period_s)` 运行期参数被 Fargate 忽略（`FargateWorkerHandle.stop` 只发 StopTask），真实宽限由 task-def 期 `stopTimeout` 决定（[0024](./0024-worker-core-protocol.md) 已记）。
- **botocore/aws-sdk 默认 retry 与 grace 冲突（**部分解决**）**：上传/events 两路已 `max_attempts=0`+短超时（[0029](./0029-engine-artifacts-to-s3.md) ArtifactUploader / [0024](./0024-worker-core-protocol.md) EventSink 的 `Config`），不吃 grace、快速失败封顶——不再走 SDK 默认 retry。**仍待**：这套「超时真封顶退出」只在健康网络真跑复验过（21s 干净退），**退化/慢网络下是否真快速失败、不拖爆 grace**未真验（moto/健康网测不到——须注入慢/退化网络，或用 `tools/e2e_harness.py` 扩展驱动真 DDB emit）。
- **上传错误分类升级（诊断精度，非阻塞）**：[0029](./0029-engine-artifacts-to-s3.md) 第一期上传失败=`engine_error`、不进重试域；是否细分 `network_error` 属**诊断分类精度**——上传都在 scope_started 之后、越过重试域边界，升级也不触发重试。
- **孤儿产物恢复（**主动扫盘未实现**）**：当前靠 act 边界抢传缩小丢失窗口（真跑验证残余仅 `session_summary.json` + 未开始的后续 step；另**最坏长 act 被 Fargate SIGKILL** 时的 in-flight act 产物截断亦归此，见结论 4）。[0028](./0028-transient-network-ssl-resilience.md)「留口子」『卡死现场 trajectory 不自动归集』条记的"中断收尾扫盘"在 Fargate 下变成"查 S3 已传哪些"——属 Engine adapter 的中断收尾职责，**尚零实现**，且 task role 缺 `s3:ListBucket`。

## 重议

- 若中断即时上传仍挡不住高频丢产物 → 另议（如云浏览器侧落盘 / 边录边传的流式 sink）。
- 若 workload 形态变化使 Fargate 不再是执行面首选（[0017](./0017-cloud-execution-fargate-over-runtime.md) 翻盘条件）→ 本 ADR 的容器特有假设需重估。
