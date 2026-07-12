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

## 7. 不烧钱 prework（三项均已完成 + 两轮对抗 review，见 §8）

1. **【必做·阻塞中断真跑】✅** `stop_timeout` 改成可配：`stack._resolve_stop_timeout`（默认 120、`-c stop_timeout=N` 覆盖、synth 期非整数/越界 `[1,120]` fail-fast）。测试 18 个（含边界 1/120/121/0/负/bool/float）全绿、synth 验证过。**尚未 `cdk deploy`**（改动在工作树、待 commit 后连真跑时一起 deploy）。
2. **【采数据前置】✅** 独立脚本 `tools/ecs_task_timing.py`（**不改** `_task_exit_code` 的 int|None 契约）：DescribeTasks 抓 `createdAt/startedAt/stoppingAt/executionStoppedAt/stoppedAt/stopCode/stoppedReason`，派生 SIGTERM→退出耗时（`stopping→executionStopped`）；`--stop-timeout` 告知生效值判 SIGKILL 截断、`--wait` 轮询到 STOPPED。
3. **✅** `tools/events_wallclock.py`：从 events 表按 `expires_at-7d` 还原 emit epoch、配对 step_started/step_done 算单 act 墙钟、出 p50/p90/p99；votes>1（MULTI-ACT）自动检测+排除出分布+告警（硬约束）、coarse≤1s 标注。

（其余非阻塞 prework：③错误分类可纯 code+单测；④orphan 恢复设计+moto+task role 加 `s3:ListBucket`；回校 ADR 0032:28 的 botocore 漂移——都可等真跑后或穿插做。）

## 8. 当前精确进度

- **三项 prework 全部完成 + 两轮对抗 review 已过**（workflow 分维度 finder + 对抗验证；round-1 9 CONFIRMED 全修）。改动：`iac_aws_backend/stack.py`+`tests/test_stack.py`（stop_timeout 可配 + 18 测试）、`tools/ecs_task_timing.py`、`tools/events_wallclock.py`（新），文档回校 `docs/adr/0033`（stopTimeout 现状）。
- **待 commit**（尚未提交；最新 commit 仍是 WP2 的 `6e21448`）。
- **下一步**：commit prework → 跑 **run-1**（`wikipedia_assertions --assertion-votes 1 --interrupt none` baseline，见 §6）。run-1 前需先 `cd iac_aws_backend && uv run cdk deploy -c use_default_vpc=true`（把可配的 stopTimeout=120 部署上去；碰真 AWS、用户已授权 deploy）。

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
