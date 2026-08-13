# Graph Report - yaozhou  (2026-08-13)

## Corpus Check
- 174 files · ~124,892 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2325 nodes · 5534 edges · 133 communities (103 shown, 30 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 462 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d31d320d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_schedule.py
- test_report_store.py
- test_run_step.py
- RunStore
- main
- core/ports.py 接口定义
- wire.py
- test_project.py
- SqliteEventLog
- devDependencies
- test_transient_network.py
- test_interrupt_model.py
- JobState
- FargateEngine
- __main__.py
- JobResult
- agentcore-sigv4.mts
- test_reconcile.py
- ArtifactUploader
- test_stack.py
- test_stores.py
- _Worker
- test_backend_cloud.py
- test_cloud_reconcile.py
- RunResult
- ADR 0016 执行架构：核心库窄腰 + Run 数据模型
- compose.py
- run-scope.ts
- ADR 0034: 无状态跑批（CQRS + reconciler）
- test_conditional_writes.py
- test_compose.py
- test_fargate_engine.py
- _engine
- S3ResultStore
- Status
- scope.py
- RunPersistence 应用服务
- e2e_harness.py
- _FakeEcs
- _attach_traj_refs
- ADR 0025: plan 模块（feature → jobs）
- JobSource
- 代码健康度复盘任务说明
- parse.py
- _stream_record
- _run_step
- Job
- run-scope.test.ts
- build_fargate_engines
- conftest.py
- test_plan.py
- _FakeEcsClient
- _mk_state
- events_wallclock.py
- JobSource
- reconciler.py
- deterministic.ts
- ReportStore.write（整 run 一次写）
- ArtifactUploader
- EventSink
- test_sqlite_event_log.py
- run_scope.py
- e2e_harness 使用说明
- ADR 0018: 通用 step 能力清单
- build_push_workers.py
- events_pk
- .on_event
- fargate_engine.py
- ensure_workflow_definition
- test_argument.py
- gherkai/names.py
- test_deterministic.py
- CloudLauncher
- ADR 0027: RunReport 跨引擎归集索引
- test_event_sink.py
- ecs_task_timing.py
- .write
- _FakeTable
- S3StepArgumentOffloader
- test_lambda_handlers.py
- _spawn_and_wait_ready
- main
- ADR 0003 Qwen3-VL on Bedrock 做 grounding
- schedule._Worker._run_once
- _instruction
- test_job_source.py
- plan
- exit_observer.py
- argument.ts
- _runs_stream_record
- test_timeout_watch_conflict_is_idempotent
- cli/__init__.py
- events_table
- README.md
- ADR 0017: Cloud Execution — Fargate over Runtime
- _prune_empty_dirs
- 权威信息源 REFERENCES
- echo_worker.py
- test_cloud_infra.py
- EventBridgeTimeoutWatch
- ADR 0007 程序化登录 / HITL 逃生舱
- _FakeS3
- Midscene SigV4 自签 fetch 配方
- interrupt_worker.py
- test_starter_run_ids_empty_when_neither
- artifact-upload.test.ts
- ._locked_rmw
- event-sink.test.ts
- build_local_reconcile
- core/wire.py 线序列化
- adapters/__init__.py
- test_extract_missing_env_returns_none
- job_result_from_dict
- 02-agentcore-cdp.ts
- core/__init__.py
- agentcore-sigv4.test.ts
- gherkai
- test_status_wait_cloud_kicker_missing_fails_fast
- 开放性动作导致页面瞬态 flaky
- session_id lineage on scope_started
- .preflight
- novaact
- wikipedia SSL 环境坑
- job-source.test.ts
- .try_claim_job
- _FakeEcs
- build_engines
- test_star_step_keyword_fails_fast
- test_starter_run_ids_from_direct_kick
- event-sink.mts
- test_scan_overdue_timeouts_only_over_budget

## God Nodes (most connected - your core abstractions)
1. `Job` - 108 edges
2. `RunMeta` - 100 edges
3. `RunState` - 92 edges
4. `Status` - 85 edges
5. `JobState` - 74 edges
6. `JobResult` - 72 edges
7. `schedule()` - 63 edges
8. `CollectSink` - 60 edges
9. `Step` - 56 edges
10. `Scenario` - 56 edges

## Surprising Connections (you probably didn't know these)
- `对抗验证（默认怀疑、只留 CONFIRMED）` --conceptually_related_to--> `绿 ≠ 对：证据边界`  [INFERRED]
  docs/code-health-review.md → CLAUDE.md
- `_submit_local()` --calls--> `SqliteEventLog`  [INFERRED]
  cli/cli/__main__.py → core/core/adapters/event_log/sqlite.py
- `_render_status()` --calls--> `run_state_to_dict()`  [INFERRED]
  cli/cli/__main__.py → core/core/serialize.py
- `_status_cloud()` --calls--> `DynamoDBRunStore`  [INFERRED]
  cli/cli/__main__.py → core/core/adapters/run_store/ddb.py
- `_FakeTable` --uses--> `JobResult`  [INFERRED]
  cli/tests/test_backend_cloud.py → core/core/model.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **真跑陷阱集合** — tools_e2e_harness_md_multi_scenario_pitfall, tools_e2e_harness_md_ssl_pitfall, tools_e2e_harness_md_boundary_preflush, tools_e2e_harness_md_interrupt_timings [EXTRACTED 0.80]
- **Retry domain safety: boundary, backoff signal penetration, session leak guard** — docs_adr_0028_transient_network_ssl_resilience_retry_domain_boundary, docs_adr_0028_transient_network_ssl_resilience_backoff, docs_adr_0028_transient_network_ssl_resilience_session_leak_guard, docs_adr_0028_transient_network_ssl_resilience_targetclosederror_stage_rule [EXTRACTED 0.80]
- **tag → scope 分组 → job 调度流** — docs_adr_0019_feature_tags_scope_and_engine_scope_tag, docs_adr_0019_feature_tags_scope_and_engine_engine_tag, docs_adr_0025_plan_module_feature_to_jobs [EXTRACTED 0.80]
- **Store/Engine ports 的 local/cloud 双实装** — core_ports, core_adapters_subprocess_engine, core_adapters_fargate_engine, core_adapters_run_store_local, core_adapters_run_store_ddb, core_adapters_result_store_local, core_adapters_result_store_s3, core_adapters_report_store_local, core_adapters_report_store_s3, cli_compose [EXTRACTED 0.85]
- **通用 step 原语在两引擎间的对称映射与边界** — docs_adr_0018_generic_steps_capability_abstract_primitives, docs_adr_0018_generic_steps_capability_engine_symmetry, docs_adr_0018_generic_steps_capability_negative_verification, docs_adr_0018_generic_steps_capability_phrasing_ambiguity_risk, docs_adr_0018_generic_steps_capability_deterministic_anchor [EXTRACTED 0.85]
- **报告判读流程（sample_valid → n_lost → 时序交叉核对）** — tools_e2e_harness_md_harness_report_json, tools_e2e_harness_md_sample_valid, tools_e2e_harness_md_lost_on_fargate, tools_e2e_harness_md_boundary_preflush [EXTRACTED 0.85]
- **step 派发：默认 AI / URL 分流 / 确定性锚点与角色边界** — docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_default_ai, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_url_autorouting, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_deterministic_scaffold, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_role_boundary [EXTRACTED 0.85]
- **产物→S3 上传流（注入落点→实时/抢传→key 镜像→删本地→ReportRef 穿透）** — docs_adr_0029_injected_s3_target, docs_adr_0029_artifact_uploader, docs_adr_0029_act_boundary_presend, docs_adr_0029_s3_key_mirrors_run_tree, docs_adr_0029_delete_local_after_upload, docs_adr_0027_reportref [EXTRACTED 0.90]
- **无状态跑批：投影 + 推进 + 事件通道 + launcher（ADR 0034）** — core_project, core_reconcile, core_adapters_event_log_sqlite, core_adapters_event_log_ddb, core_adapters_cloud_launcher, docs_adr_0034_detached_batch_reconciler [EXTRACTED 0.90]
- **network_error signal flow: worker whitelist → exit code 80 → typed error → schedule retry** — docs_adr_0028_transient_network_ssl_resilience_is_transient_network, docs_adr_0028_transient_network_ssl_resilience_ex_worker_network, docs_adr_0028_transient_network_ssl_resilience_subprocess_engine_read_events, docs_adr_0028_transient_network_ssl_resilience_workernetworkerror, docs_adr_0028_transient_network_ssl_resilience_schedule_worker_run_once, docs_adr_0028_transient_network_ssl_resilience_schedule_worker_run [EXTRACTED 0.90]
- **plan pipeline: parse → scope grouping → id derivation → Job[]** — docs_adr_0025_plan_module_feature_to_jobs_plan, docs_adr_0025_plan_module_feature_to_jobs_parse, docs_adr_0025_plan_module_feature_to_jobs_scope, docs_adr_0025_plan_module_feature_to_jobs_id_derivation, docs_adr_0025_plan_module_feature_to_jobs_job [EXTRACTED 0.90]
- **稳定指针纪律（跨文档一致约束）** — claude_stable_pointers, claude_reference_direction, claude_journey_staging, claude_adr_status_header, docs_code_health_review_stale_inefficient [EXTRACTED 0.90]
- **三 port 正交：RunStore 控制面 / ResultStore 数据面 / ReportStore 派生视图** — docs_adr_0030_run_store, docs_adr_0030_result_store, docs_adr_0027_reportstore, docs_adr_0030_commit_point [EXTRACTED 0.90]
- **代码复盘三类问题分类学** — docs_code_health_review, docs_code_health_review_dead, docs_code_health_review_stale_inefficient, docs_code_health_review_violates_adr [EXTRACTED 0.95]
- **无状态跑批四机制：独立键空间 / 退出观察者 / HWM 条件写 / CAS 并发闸** — docs_adr_0034_task_exited_keyspace, docs_adr_0034_exit_observer, docs_adr_0034_hwm_conditional_write, docs_adr_0034_cas_concurrency, docs_adr_0034_reconcile_tick [EXTRACTED 0.95]
- **证据边界与验证流程（绿≠对 → 真跑 → 对抗验证）** — claude_green_not_correct, tools_e2e_harness, claude_aws_free_dev, docs_code_health_review_adversarial, docs_code_health_review_graphify_blindspot [INFERRED 0.80]
- **.feature → 分组 → 调度 → 结果落库 流水线** — core_parse, core_scope, core_schedule, core_persist, core_serialize, core_model [INFERRED 0.80]

## Communities (133 total, 30 thin omitted)

### Community 0 - "test_schedule.py"
Cohesion: 0.07
Nodes (116): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 subprocess_engine… (+108 more)

### Community 1 - "test_report_store.py"
Cohesion: 0.05
Nodes (84): _arg_hint(), _cost_bits(), _ms(), plan_to_dict(), Job, 渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…, step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。 dataTable →…, plan 产出 → 机器可读 dict（--json）。复用 core.serialize 的 job 序列化保单一真理源。 (+76 more)

### Community 2 - "test_run_step.py"
Cohesion: 0.06
Nodes (36): captured(), _done(), _FakeNova, _FakeResult, _FakeSink, _Meta, _NavErrorNova, fixture (+28 more)

### Community 3 - "RunStore"
Cohesion: 0.10
Nodes (11): CAS 抢占：仅当该 job 当前是 PENDING 才置 RUNNING，成功返回 True（机制四）。 多个 reconciler 实例并发抢同一…, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale…, 状态机单调条件写：仅当 run 总 status 当前为非终态（pending/running）才写终态，成功 True（机制三）。 挡「已 finalize…, 控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。…, RunStore, EventLog, Launcher, Job (+3 more)

### Community 4 - "main"
Cohesion: 0.16
Nodes (32): main(), _capturing_schedule(), _fake_schedule_factory(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS）， 验证落盘三层产物 + --json…, 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job…, 假 schedule：把传入 opts 存进 opts_box、按指定 status 合成 RunResult（验退出码/参数映射）。, 返回一个替换 compose.build_local_stores 的 fake：产出三个记录调用的 fake store + make_artifacts。 (+24 more)

### Community 5 - "core/ports.py 接口定义"
Cohesion: 0.16
Nodes (17): cli/compose.py 组合根装配, adapters/_boto.py boto3 依赖守卫, adapters/fargate_engine.py, adapters/report_store/local.py, adapters/report_store/s3.py, adapters/result_store/local.py, adapters/result_store/s3.py, adapters/run_store/arg_offload.py (+9 more)

### Community 6 - "wire.py"
Cohesion: 0.06
Nodes (47): _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。 (+39 more)

### Community 7 - "test_project.py"
Cohesion: 0.09
Nodes (57): ScopeStarted, Action, plan_next(), project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, _ev() (+49 more)

### Community 8 - "SqliteEventLog"
Cohesion: 0.07
Nodes (38): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, SqliteEventLog (+30 more)

### Community 9 - "devDependencies"
Cohesion: 0.05
Nodes (38): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-dynamodb, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, author (+30 more)

### Community 10 - "test_transient_network.py"
Cohesion: 0.08
Nodes (29): _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings(), test_presend_ignores_non_html(), test_presend_skips_when_no_sibling_json() (+21 more)

### Community 11 - "test_interrupt_model.py"
Cohesion: 0.07
Nodes (19): captured(), _FakeResult, _FakeSink, _Meta, fixture, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM…, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。 (+11 more)

### Community 12 - "JobState"
Cohesion: 0.11
Nodes (17): _job_state_from_item(), 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。…, 按 scope_id 刷单个 job 的运行态（Map upsert）。run_state.json 不存在则报错（须先 create_run）。, commit point：写总 status + ended_at（各 job 态此前已由 update_job_state 刷过）。, 读回运行态（RunState）；不存在返回 None。, JobState, 单个 job 的控制面运行态（执行后才有）。 (+9 more)

### Community 13 - "FargateEngine"
Cohesion: 0.14
Nodes (14): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+6 more)

### Community 14 - "__main__.py"
Cohesion: 0.13
Nodes (29): ArgumentParser, _build_parser(), _cmd_list_engines(), _cmd_plan(), _cmd_reconcile(), _cmd_run(), _cmd_status(), _cmd_submit() (+21 more)

### Community 15 - "JobResult"
Cohesion: 0.12
Nodes (16): JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的…, 数据面：每 job(=scope) 判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。 local adapter =…, ResultStore, S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…, test_load_all_paginated_preserves_failed_verdict(), test_load_all_paginates_beyond_1000() (+8 more)

### Community 16 - "agentcore-sigv4.mts"
Cohesion: 0.07
Nodes (27): ADR-0010, getBaseUrl(), getRegion(), MODEL, modelSigner_(), ADR-0033, signCdpUpgrade(), sigv4Fetch() (+19 more)

### Community 17 - "test_reconcile.py"
Cohesion: 0.12
Nodes (27): 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher, _job(), _meta(), Job (+19 more)

### Community 18 - "ArtifactUploader"
Cohesion: 0.09
Nodes (22): ArtifactUploader, Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记… (+14 more)

### Community 19 - "test_stack.py"
Cohesion: 0.06
Nodes (42): Cluster, Construct, BackendStack, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED…, 把 Lambda 代码打包到一个目录，返回其路径（Code.from_asset 用）。 内容 = lambdas/*.py（handler）+…, worker 安全组 id——_ssm_network 建的 sg。存引用供 reconciler Lambda 起 task 用同一 sg。, container stopTimeout（秒）：`-c stop_timeout=N` 覆盖，默认 120s。 grace… (+34 more)

### Community 20 - "test_stores.py"
Cohesion: 0.14
Nodes (28): RunStore adapters（ADR 0016）。当前只有 local；未来 ddb。, LocalRunStore, Path, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, RunStore 的本地文件实现（组合根注入；未来 DDB 版换落点/读写）。, 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), from_dict() (+20 more)

### Community 21 - "_Worker"
Cohesion: 0.19
Nodes (9): _heartbeat_wrap(), Event, Job, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…, _Worker (+1 more)

### Community 22 - "test_backend_cloud.py"
Cohesion: 0.20
Nodes (27): _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 不起 worker 的假 schedule：走完 on_event/on_job_complete 实时落库路径（让 adapter 真被调）。, submit cloud 的 preflight 除表/桶/cluster 外还探：本 run 用到引擎的 task-def + 事件驱动链三 Lambda…, preflight 报资源缺（如链上 Lambda 不存在）→ 提交前退 2、不写任何东西。, patch store 钩子 + preflight（默认放行）返回记录调用的 fake（不连真 AWS）。… (+19 more)

### Community 23 - "test_cloud_reconcile.py"
Cohesion: 0.17
Nodes (19): DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, _meta(), _passed_worker_events(), _put_worker_event(), cloud 无状态跑批 core 侧测试（ADR 0034 P4a）：DdbEventLog + CloudLauncher +…, CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。 (+11 more)

### Community 24 - "RunResult"
Cohesion: 0.16
Nodes (24): LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, 一次执行的机器可读汇总判定 = **definition（run_meta）+ 判定（jobs）的显式合成**（ADR 0016/0026）。…, RunResult, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run = commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run… (+16 more)

### Community 25 - "ADR 0016 执行架构：核心库窄腰 + Run 数据模型"
Cohesion: 0.20
Nodes (21): cli/README 组合根说明, CONTEXT.md 领域术语表, ADR 0005 单一共享 .feature, ADR 0006 形态 A 两子工程并列, ADR 0013 跨引擎共享边界, ADR 0014 AI 断言为主 + 投票治抖动, ADR 0015 v1.0 定位柔性冒烟, ADR 0016 执行架构：核心库窄腰 + Run 数据模型 (+13 more)

### Community 26 - "compose.py"
Cohesion: 0.10
Nodes (20): build_local_stores(), _make_lambda_client(), _make_ssm_client(), new_run_id(), now_iso(), 组合根：把抽象的 core 接线到具体的引擎子进程（ADR 0016）。 core 只认 `EngineResolver`（按 engine 名给一个…, 本地文件三层 store + local artifacts descriptor（file:// 完整路径）。 落…, boto3 ssm client（读 subnet/sg 的确定性路径参数）。 (+12 more)

### Community 27 - "run-scope.ts"
Cohesion: 0.10
Nodes (20): ADR-0019, ADR-0026, ADR-0027, ADR-0032, AWS_TRANSIENT_NAMES, AWS_TRANSIENT_STATUS, CONNECT_BACKOFF_MS, interruptSnapshot() (+12 more)

### Community 28 - "ADR 0034: 无状态跑批（CQRS + reconciler）"
Cohesion: 0.11
Nodes (25): adapters/cloud_launcher.py, adapters/event_log/ddb.py, adapters/event_log/sqlite.py, core/errors.py 类型化异常, core/project.py 纯归约投影, core/reconcile.py 推进编排, core/schedule.py 并发调度, ADR 0028 重试分类 (+17 more)

### Community 29 - "test_conditional_writes.py"
Cohesion: 0.11
Nodes (33): _initial(), _meta(), fixture, RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。 (+25 more)

### Community 30 - "test_compose.py"
Cohesion: 0.15
Nodes (15): engine_min_grace(), 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…, resolve_region(), compose（组合根逻辑）单测：不起任何子进程、不烧钱。, test_engine_min_grace_midscene_nonzero_covers_onsignal_budget(), test_engine_min_grace_mixed_run_takes_max(), test_engine_min_grace_nova_covers_act_timeout_plus_margin() (+7 more)

### Community 31 - "test_fargate_engine.py"
Cohesion: 0.15
Nodes (22): _await_engine(), _delayed_stopped_ecs(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env() (+14 more)

### Community 32 - "_engine"
Cohesion: 0.14
Nodes (28): _engine(), _job(), _put_event(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。, worker 发完 scope_done 又非 0 退出（会话释放失败，Midscene cleanupFailed→exit 1）： scope_done…, **option-c 定义行为的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR 0032 结论… (+20 more)

### Community 33 - "S3ResultStore"
Cohesion: 0.17
Nodes (9): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, _s3_result_store() (+1 more)

### Community 34 - "Status"
Cohesion: 0.05
Nodes (54): CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, Status, StepStarted (+46 more)

### Community 35 - "scope.py"
Cohesion: 0.25
Nodes (13): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。 (+5 more)

### Community 36 - "RunPersistence 应用服务"
Cohesion: 0.09
Nodes (24): 注入驱动的 S3 落点（ARTIFACT_S3_BUCKET/PREFIX）, commit-point 写序（数据面先、控制面后）, DDB 单表 META/STATE 两 item, on_job_complete / on_event 回调（JobSink）, Store.preflight() 探活 + 退出码分层, ResultStore（判定真值、S3 后端）, RunPersistence 应用服务, RunState.jobs 改 Map<scope_id> (+16 more)

### Community 37 - "e2e_harness.py"
Cohesion: 0.23
Nodes (12): AWS 资源视为免费（限开发期）, 代码纪律, 绿 ≠ 对：证据边界, 接口诚实优先于改动规模, tools/ 是复用工具库，先翻别重造, build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退… (+4 more)

### Community 38 - "_FakeEcs"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 39 - "_attach_traj_refs"
Cohesion: 0.29
Nodes (8): ArtifactUploader, _attach_traj_refs(), _get_uploader(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：抢传配套 json（ADR 0029）+ reportRefs（ADR 0027…, act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…, _traj_refs()

### Community 40 - "ADR 0025: plan 模块（feature → jobs）"
Cohesion: 0.12
Nodes (19): core/model.py 领域模型, core/parse.py feature 解析, core/scope.py tag 分组与 plan, core/serialize.py 序列化真理源, ADR 0014: Assertion Votes Semantics, ADR 0019: Feature Tags — scope and engine, 同 scope 多 engine 值即报错, @engine:<midscene|novaact> 引擎选择 tag (G2) (+11 more)

### Community 41 - "JobSource"
Cohesion: 0.22
Nodes (4): Job, JobSource, ADR-0016, ADR-0024

### Community 42 - "代码健康度复盘任务说明"
Cohesion: 0.15
Nodes (19): CLAUDE.md — 项目约定, ADR Status 头约定, 沟通约定（中文讨论 / graphify 用英文）, 文档纪律（ADR / CONTEXT）, graphify 知识图谱使用约定, docs/journey/ 是 staging 区, 读者比例决定优化方向, 引用方向单向：Journey→ADR (+11 more)

### Community 43 - "parse.py"
Cohesion: 0.21
Nodes (12): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+4 more)

### Community 44 - "_stream_record"
Cohesion: 0.29
Nodes (7): scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, _stream_record(), test_run_ids_dedup_multi_scope_same_run(), test_run_ids_multi_run(), test_run_ids_scope_with_colon_not_hash(), test_run_ids_single()

### Community 45 - "_run_step"
Cohesion: 0.25
Nodes (9): _collect_traj(), _cost_from_result(), 报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。, 从 act/act_get 结果的 metadata 收集本次 act 的 trajectory **HTML** 路径（ADR 0027）。 Nova 每次…, 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, _run_scenario(), _run_step() (+1 more)

### Community 46 - "Job"
Cohesion: 0.05
Nodes (92): DynamoDBRunStore, _job_state_to_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, 一次性写完整态（= create_run 的两 item 一起 put；语义同 local save_run）。, 读回 definition（从 META item 的 meta_json）；不存在返回 None。, JobState → DDB Map entry（字段集同 serialize；session_id/claimed_at 用 omit-when-…, RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐… (+84 more)

### Community 47 - "run-scope.test.ts"
Cohesion: 0.12
Nodes (9): _events, fakePage, importMod(), testSink, ADR-0014, ADR-0024, ADR-0028, ADR-0029 (+1 more)

### Community 48 - "build_fargate_engines"
Cohesion: 0.18
Nodes (13): build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_ecs_client(), _make_s3_client(), _normalize_prefix(), S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走… (+5 more)

### Community 49 - "conftest.py"
Cohesion: 0.13
Nodes (20): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), fixture, 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -… (+12 more)

### Community 50 - "test_plan.py"
Cohesion: 0.16
Nodes (23): PlanConfig, _plan(), plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 无前驱非连接词的首条 And 同判不出 → PlanError;有前驱的 And 正常继承不受影响。, test_assertion_votes_default_is_one(), test_background_prepended(), test_datatable_and_docstring_argument(), test_engine_conflict_errors() (+15 more)

### Community 51 - "_FakeEcsClient"
Cohesion: 0.17
Nodes (12): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, test_preflight_all_present_returns_none(), test_preflight_missing_chain_lambda_names_prefix() (+4 more)

### Community 52 - "_mk_state"
Cohesion: 0.23
Nodes (12): _args(), _mk_state(), pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、failed/error→1，均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。, test_render_status_json_no_hint() (+4 more)

### Community 53 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 54 - "JobSource"
Cohesion: 0.14
Nodes (8): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层…

### Community 55 - "reconciler.py"
Cohesion: 0.15
Nodes (20): datetime, _build(), _handle_timeout(), handler(), kicker_handler(), _now_iso(), _parse_iso(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。… (+12 more)

### Community 56 - "deterministic.ts"
Cohesion: 0.16
Nodes (14): ADR-0015, _clear(), deterministic(), DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, Entry (+6 more)

### Community 57 - "ReportStore.write（整 run 一次写）"
Cohesion: 0.20
Nodes (11): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, LocalReportStore, manifest.json（薄信封 + report_index）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写）, ResourceUri（带 scheme 的统一指针）, run_id（组合根生成、归集主键） (+3 more)

### Community 58 - "ArtifactUploader"
Cohesion: 0.17
Nodes (6): ArtifactUploader, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0033

### Community 59 - "EventSink"
Cohesion: 0.18
Nodes (7): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。 fd…, test_emit_flushes_each_event(), TextIO

### Community 60 - "test_sqlite_event_log.py"
Cohesion: 0.27
Nodes (10): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, test_append_and_read_back_events(), test_append_idempotent_same_seq(), test_exit_code_none_stored() (+2 more)

### Community 61 - "run_scope.py"
Cohesion: 0.16
Nodes (18): engines/novaact README, _aggregate(), _backoff_interrupted(), _classify_act_error(), _emit_scenario_done_unless_stopped(), _is_transient_client_error(), _is_transient_network(), log() (+10 more)

### Community 62 - "e2e_harness 使用说明"
Cohesion: 0.18
Nodes (13): ADR 0014 AI 断言投票, ADR 0024 worker↔core 协议 / 终止契约, ADR 0025 @scope: tag 分组, ADR 0029 产物→S3 / 边界抢传 / 固有残余, ADR 0032 Fargate 中断丢失量级 + 真容器 grace 校准, e2e_harness 使用说明, 边界抢传（act / scenario 边界）, grace 测量与 SIGKILL 兜底 (+5 more)

### Community 63 - "ADR 0018: 通用 step 能力清单"
Cohesion: 0.15
Nodes (13): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）, 双引擎真实价值 = 可选择/不锁定（交叉验证降级）, ADR 0020: Step 措辞——默认 AI + 确定性锚点脚手架 (+5 more)

### Community 64 - "build_push_workers.py"
Cohesion: 0.22
Nodes (12): _account_id(), build_push(), _ecr_login(), main(), Path, ECR repo 名 = {prefix}{engine}-worker（对齐 names.task_def_name，见 docstring）。, 跑一条命令；dry-run 只打印。失败即抛（subprocess.run check=True）——不吞错、让调用者见真况。, 取当前账户 id（拼 ECR registry host）。dry-run 时用占位符（不真调 AWS）。 (+4 more)

### Community 65 - "events_pk"
Cohesion: 0.22
Nodes (6): 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。, test_events_pk_composite_run_id_scope_id()

### Community 67 - "fargate_engine.py"
Cohesion: 0.15
Nodes (8): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install core[aws]`）；模块 import 不崩、构造时才检。, require_boto3(), DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…

### Community 68 - "ensure_workflow_definition"
Cohesion: 0.21
Nodes (9): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（worker/run_scope.py）与 spike…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 region=None（不再硬编码…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开…, run() (+1 more)

### Community 70 - "gherkai/names.py"
Cohesion: 0.13
Nodes (15): 两层命名：--prefix 批量 + 单资源覆盖, container_name(), default_name(), 资源命名真源（gherkai 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。 **零依赖**（不…, prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…, task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, subnet/sg 的 SSM 参数路径（含 prefix，cli 已知 prefix 拼路径读，无循环——ADR 0033）。 (+7 more)

### Community 71 - "test_deterministic.py"
Cohesion: 0.09
Nodes (16): deterministic, deterministic(), DeterministicConflict, _Entry, match(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 test engineer 用 `@deterministic(pattern)`…, 装饰器：把 handler 按正则 pattern 登记进注册表。 用法（与脚手架 deterministic_steps.py 的真实锚点一致）：… (+8 more)

### Community 72 - "CloudLauncher"
Cohesion: 0.15
Nodes (16): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, _job(), job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…, 无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。, 武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时， 先建的… (+8 more)

### Community 73 - "ADR 0027: RunReport 跨引擎归集索引"
Cohesion: 0.13
Nodes (19): cli README（执行入口皮）, core 执行核心库 README, 被拒方案：materialize 产物拷贝, ADR 0027: RunReport 跨引擎归集索引, ADR 0028: Transient Network/SSL Resilience, Hand-written exponential backoff with _stop.wait, botocore transient/throttled error code tables (inlined), _is_transient_network(e, *, connecting=False) (Python whitelist) (+11 more)

### Community 74 - "test_event_sink.py"
Cohesion: 0.17
Nodes (3): EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud()

### Community 75 - "ecs_task_timing.py"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 78 - "S3StepArgumentOffloader"
Cohesion: 0.15
Nodes (10): _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref… (+2 more)

### Community 79 - "test_lambda_handlers.py"
Cohesion: 0.17
Nodes (14): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, container 缺 exitCode（宽限态）→ None（机制二保守）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, handler 对缺 run_id 的事件返回 skipped（不崩、不误处理别的 cluster 负载）。, _stopped_detail(), test_extract_missing_exitcode_is_none() (+6 more)

### Community 80 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal(), test_worker_runs_until_signaled() (+1 more)

### Community 81 - "main"
Cohesion: 0.24
Nodes (11): match, aggregate(), cumulativeTokens(), isTransientNetwork(), log(), main(), modelConfig(), runScenario() (+3 more)

### Community 82 - "ADR 0003 Qwen3-VL on Bedrock 做 grounding"
Cohesion: 0.36
Nodes (8): ADR 0002 不用 Bedrock GPT-5.5, ADR 0003 Qwen3-VL on Bedrock 做 grounding, ADR 0004 Nova Act 纯 IAM 经 Workflow 鉴权, ADR 0008 Midscene SigV4 自签鉴权, ADR 0009 最大化使用 AWS 硬约束, ADR 0012 planning 复用 Qwen3-VL, 文档健康度复盘任务, SIGV4-FETCH-RECIPE 配方笔记

### Community 83 - "schedule._Worker._run_once"
Cohesion: 0.29
Nodes (8): EX_WORKER_NETWORK = 80 exit code, schedule._heartbeat_wrap (silent-worker timeout fix), ScheduleOpts (network_retry, retry_sleep), schedule._Worker.run (network retry loop), schedule._Worker._run_once, Session leak protection before exit, subprocess_engine._read_events, core.errors.WorkerNetworkError

### Community 84 - "_instruction"
Cohesion: 0.25
Nodes (8): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote()

### Community 85 - "test_job_source.py"
Cohesion: 0.22
Nodes (3): JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。, test_s3_uri_without_key_fails_loud()

### Community 86 - "plan"
Cohesion: 0.33
Nodes (9): FeatureSource, plan(), Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 严格契约：`features` 的 uri 必须互异（uri…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, test_assertion_votes_from_config_propagates_to_all_jobs(), test_cross_file_scope_merge_warns(), test_distinct_uri_ok() (+1 more)

### Community 87 - "exit_observer.py"
Cohesion: 0.32
Nodes (7): _event_log(), _extract(), handler(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。, EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。

### Community 88 - "argument.ts"
Cohesion: 0.39
Nodes (7): argumentText(), buildInstruction(), cleanCell(), StepArgument, ADR-0024, ADR-0024, unquote()

### Community 89 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 92 - "events_table"
Cohesion: 0.67
Nodes (3): events_table(), fixture, events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——P4 单独建，schema 见 ADR 0033/0024。

### Community 94 - "ADR 0017: Cloud Execution — Fargate over Runtime"
Cohesion: 0.33
Nodes (6): ADR 0017: Cloud Execution — Fargate over Runtime, AgentCore Evaluations（LLM-as-Judge，被否）, AgentCore Runtime（长驻 agent 服务）, 批处理 workload shape（run-to-exit）, ECS RunTask / Fargate 执行后端, 15 分钟 idle-kill 计时器与保活 plumbing

### Community 95 - "_prune_empty_dirs"
Cohesion: 0.40
Nodes (5): _prune_empty_dirs(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, test_prune_empty_dirs_keeps_nonempty(), test_prune_empty_dirs_noop_when_missing(), test_prune_empty_dirs_removes_empty_tree()

### Community 96 - "权威信息源 REFERENCES"
Cohesion: 0.40
Nodes (5): CONTEXT.md 事实现状, 权威信息源 REFERENCES, AWS Bedrock / AgentCore 文档, Midscene 官方文档与源码 ground truth, Nova Act SDK 与 AgentCore provider

### Community 97 - "echo_worker.py"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 100 - "ADR 0007 程序化登录 / HITL 逃生舱"
Cohesion: 0.67
Nodes (4): ADR 0001 范围限英文 UI, ADR 0007 程序化登录 / HITL 逃生舱, ADR 0010 双引擎苹果对苹果对标, ADR 0011 AgentCore 浏览器默认 vs 自建

### Community 102 - "Midscene SigV4 自签 fetch 配方"
Cohesion: 0.50
Nodes (4): engines/midscene README, Midscene SigV4 自签 fetch 配方, createOpenAIClient 隔离 ModelConfigManager 坑, sigv4Fetch（最小手建请求签名）

### Community 105 - "artifact-upload.test.ts"
Cohesion: 0.50
Nodes (3): mkLogDir(), tmproot(), ADR-0029

### Community 106 - "._locked_rmw"
Cohesion: 0.25
Nodes (4): 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新…, CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。, HWM 条件写 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。 **run 级 status 钳为…, 状态机单调条件写：仅当当前总 status 为非终态才写终态（机制三，commit 恰一次）。

### Community 108 - "build_local_reconcile"
Cohesion: 0.50
Nodes (4): make_resolver(), dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…

### Community 112 - "job_result_from_dict"
Cohesion: 0.10
Nodes (17): ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, job_result_from_dict(), job_result_to_dict() (+9 more)

### Community 116 - "gherkai"
Cohesion: 0.67
Nodes (4): cli, core, gherkai, iac-aws-backend

### Community 126 - "_FakeEcs"
Cohesion: 0.15
Nodes (7): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

### Community 127 - "build_engines"
Cohesion: 0.19
Nodes (22): build_engines(), load_feature(), Path, 定位仓库根（含 core/ 与 engines/ 的目录）。 从本文件位置上溯：cli/cli/compose.py → cli/ →…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 两个引擎"spawn 子进程 + 讲同一套 ADR…, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导稳定…, repo_root(), Path (+14 more)

### Community 130 - "event-sink.mts"
Cohesion: 0.22
Nodes (5): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0033

## Ambiguous Edges - Review These
- `e2e_harness.py` → `分片深读（按模块耦合分组）`  [AMBIGUOUS]
  docs/code-health-review.md · relation: conceptually_related_to

## Knowledge Gaps
- **154 isolated node(s):** `MODEL`, `ADR-0033`, `ADR-0029`, `ADR-0016`, `ADR-0024` (+149 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `e2e_harness.py` and `分片深读（按模块耦合分组）`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `core 测试说明（单测 + 集成测试）` connect `core/ports.py 接口定义` to `conftest.py`, `Job`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `ADR 0030: 实时写存储接缝` connect `core/ports.py 接口定义` to `ADR 0027: RunReport 跨引擎归集索引`, `RunPersistence 应用服务`, `ADR 0034: 无状态跑批（CQRS + reconciler）`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `Job` connect `Job` to `test_schedule.py`, `test_report_store.py`, `RunStore`, `wire.py`, `test_project.py`, `SqliteEventLog`, `JobState`, `FargateEngine`, `JobResult`, `test_reconcile.py`, `test_stores.py`, `_Worker`, `test_cloud_reconcile.py`, `RunResult`, `test_conditional_writes.py`, `test_fargate_engine.py`, `_engine`, `Status`, `scope.py`, `_FakeEcs`, `test_plan.py`, `test_sqlite_event_log.py`, `fargate_engine.py`, `CloudLauncher`, `plan`, `job_result_from_dict`, `_FakeEcs`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `RunMeta` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunMeta` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 23 INFERRED edges - model-reasoned connections that need verification._