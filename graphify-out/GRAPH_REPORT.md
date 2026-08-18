# Graph Report - yaozhou  (2026-08-18)

## Corpus Check
- 182 files · ~140,810 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2583 nodes · 6052 edges · 166 communities (116 shown, 50 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 523 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `015585e5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_schedule.py
- DdbEventLog
- test_detached_launcher.py
- test_run_step.py
- test_plan.py
- test_stack.py
- test_artifact_upload.py
- test_project.py
- DynamoDBRunStore
- Job
- model.py
- test_cloud_reconcile.py
- test_transient_network.py
- test_lambda_handlers.py
- devDependencies
- test_interrupt_model.py
- __main__.py
- RunState
- main
- ArtifactUploader
- test_reconcile.py
- agentcore-sigv4.mts
- compose.py
- test_backend_cloud.py
- test_report_store.py
- _engine
- test_tunnel_host.py
- NgrokTunnel
- JobState
- RunPersistence
- test_stores.py
- ValueError
- RunMeta
- reconciler.py
- test_fargate_engine.py
- ADR 0034 — Detached Batch Reconciler
- FargateEngine
- run-scope.ts
- _FakeEcsClient
- run_scope.py
- build_engines
- gherkai/names.py
- 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器
- StepArgument
- ArtifactUploader
- ADR 0031 job 生命周期态 skipped/aborted + severity 数值序
- _Worker
- exit_observer.py
- deterministic.ts
- run-scope.test.ts
- events_wallclock.py
- S3ResultStore
- ADR 0022 BDD runner 退役 + 薄 worker
- test_job_source.py
- {prefix}cluster + Fargate task definitions
- S3ReportStore
- wire.py
- test_tunnel_cli.py
- e2e_harness 使用说明
- _FakeEcs
- TaskExited
- test_event_sink.py
- build_push_workers.py
- _mk_state
- ScopeStarted
- now_iso
- test_argument.py
- CloudTarget
- 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询
- test_s3_report_store.py
- conftest.py
- event-sink.mts
- ReportStore.write（整 run 一次写）
- Popen
- _spawn_and_wait_ready
- _FakeTable
- ecs_task_timing.py
- RunPersistence 应用服务
- JobSource
- render.py
- _SeqEcs
- ADR 0003 Qwen3-VL on Bedrock 做 grounding
- schedule._Worker._run_once
- _FakeProc
- argument.ts
- _stopped_detail
- test_compose.py
- test_error_without_reduce_message_gets_default_attribution
- ensure_workflow_definition
- RunResult
- ADR 0017: Cloud Execution — Fargate over Runtime
- _FakeS3
- test_read_events_ignores_exit_item_on_stopped_drain_path
- echo_worker.py
- test_cloud_infra.py
- artifact-upload.test.ts
- projected_run_status
- 权威信息源 REFERENCES
- Midscene SigV4 自签 fetch 配方
- event-sink.test.ts
- gherkai
- EventSink
- 02-agentcore-cdp.ts
- job-source.test.ts
- interrupt_worker.py
- gherkai/__init__.py
- cli/__init__.py
- adapters/__init__.py
- test_status_wait_cloud_kicker_missing_fails_fast
- agentcore-sigv4.test.ts
- core/__init__.py
- DynamoDB stream event source mappings
- subprocess_engine.py
- test_kicker_timeout_path_builds_once
- test_scan_overdue_timeouts_only_over_budget
- 开放性动作导致页面瞬态 flaky
- session_id lineage on scope_started
- ADR 0030 实时落库接缝
- test_deterministic.py
- StepArgument
- iac_aws_backend CDK 工程
- prefix contract
- {prefix}artifacts S3 bucket
- novaact
- wikipedia SSL 环境坑
- cloud_env
- test_sqlite_event_log.py
- JobResult
- test_wire.py
- Protocol
- test_starter_run_ids_empty_when_neither
- test_timeout_watch_conflict_is_idempotent
- ResourceUri
- StepArgument
- main
- parametrize
- test_extract_missing_env_returns_none
- test_handler_skips_when_no_run_id
- _FakeEcs
- tunnel_host.py
- tunnel.py
- _run_step
- write_tunnel_file
- .load_run_meta
- S3StepArgumentOffloader
- test_s3_result_store.py
- StepArgument
- stop_tunnel
- _runs_stream_record
- EventBridgeTimeoutWatch
- test_tunnel.py
- raise_for_worker_exit
- ArtifactUploader（from_env/to_report_ref/flush）
- _instruction
- _is_transient_network
- iac_aws_backend README
- .on_event
- .preflight
- result_store/__init__.py
- .__init__
- .preflight
- .finalize
- .launch
- ._pump
- _reconcile_lambdas (stack wiring)

## God Nodes (most connected - your core abstractions)
1. `Job` - 116 edges
2. `RunMeta` - 104 edges
3. `RunState` - 101 edges
4. `Status` - 87 edges
5. `JobState` - 82 edges
6. `JobResult` - 72 edges
7. `main()` - 70 edges
8. `schedule()` - 63 edges
9. `Scenario` - 61 edges
10. `Step` - 61 edges

## Surprising Connections (you probably didn't know these)
- `通用 step（QA 零代码的唯一载体）` --conceptually_related_to--> `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md → docs/adr/0019-feature-tags-scope-and-engine.md
- `_event_log()` --calls--> `DdbEventLog`  [INFERRED]
  lambdas/exit_observer.py → core/core/adapters/event_log/ddb.py
- `_build()` --calls--> `DdbEventLog`  [INFERRED]
  lambdas/reconciler.py → core/core/adapters/event_log/ddb.py
- `_build()` --calls--> `CloudLauncher`  [INFERRED]
  lambdas/reconciler.py → core/core/adapters/cloud_launcher.py
- `CloudTarget` --uses--> `SubprocessEngine`  [INFERRED]
  gherkai/gherkai/compose.py → core/core/adapters/subprocess_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **真跑陷阱集合** — tools_e2e_harness_md_multi_scenario_pitfall, tools_e2e_harness_md_ssl_pitfall, tools_e2e_harness_md_boundary_preflush, tools_e2e_harness_md_interrupt_timings [EXTRACTED 0.80]
- **Retry domain safety: boundary, backoff signal penetration, session leak guard** — docs_adr_0028_transient_network_ssl_resilience_retry_domain_boundary, docs_adr_0028_transient_network_ssl_resilience_backoff, docs_adr_0028_transient_network_ssl_resilience_session_leak_guard, docs_adr_0028_transient_network_ssl_resilience_targetclosederror_stage_rule [EXTRACTED 0.80]
- **同步 run 流水线：解析 → scope 分组 → 调度 → spawn 薄 worker → 归约落库** — core_core_parse, core_core_scope, core_core_schedule, core_core_persist, cli_cli___main__, gherkai_gherkai_compose, engines_midscene_worker_run_scope, engines_novaact_worker_run_scope [EXTRACTED 0.85]
- **通用 step 原语在两引擎间的对称映射与边界** — docs_adr_0018_generic_steps_capability_abstract_primitives, docs_adr_0018_generic_steps_capability_engine_symmetry, docs_adr_0018_generic_steps_capability_negative_verification, docs_adr_0018_generic_steps_capability_phrasing_ambiguity_risk, docs_adr_0018_generic_steps_capability_deterministic_anchor [EXTRACTED 0.85]
- **报告判读流程（sample_valid → n_lost → 时序交叉核对）** — tools_e2e_harness_md_harness_report_json, tools_e2e_harness_md_sample_valid, tools_e2e_harness_md_lost_on_fargate, tools_e2e_harness_md_boundary_preflush [EXTRACTED 0.85]
- **step 派发：默认 AI / URL 分流 / 确定性锚点与角色边界** — docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_default_ai, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_url_autorouting, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_deterministic_scaffold, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_role_boundary [EXTRACTED 0.85]
- **产物→S3 上传流（注入落点→实时/抢传→key 镜像→删本地→ReportRef 穿透）** — docs_adr_0029_injected_s3_target, docs_adr_0029_artifact_uploader, docs_adr_0029_act_boundary_presend, docs_adr_0029_s3_key_mirrors_run_tree, docs_adr_0029_delete_local_after_upload, docs_adr_0027_reportref [EXTRACTED 0.90]
- **无状态跑批：events 真值日志 → 纯投影 → 幂等 tick → 三触发源推进** — core_core_project, core_core_reconcile, core_core_adapters_event_log_ddb, core_core_adapters_event_log_sqlite, lambdas_kicker, lambdas_reconciler, lambdas_exit_observer, gherkai_gherkai_detached, cli_cli___main__ [EXTRACTED 0.90]
- **network_error signal flow: worker whitelist → exit code 80 → typed error → schedule retry** — docs_adr_0028_transient_network_ssl_resilience_is_transient_network, docs_adr_0028_transient_network_ssl_resilience_ex_worker_network, docs_adr_0028_transient_network_ssl_resilience_subprocess_engine_read_events, docs_adr_0028_transient_network_ssl_resilience_workernetworkerror, docs_adr_0028_transient_network_ssl_resilience_schedule_worker_run_once, docs_adr_0028_transient_network_ssl_resilience_schedule_worker_run [EXTRACTED 0.90]
- **四个 port 与其 local/cloud adapter 共同实现「组合根注入」六边形架构** — core_core_ports, core_core_adapters_subprocess_engine, core_core_adapters_fargate_engine, core_core_adapters_run_store_ddb, core_core_adapters_result_store_s3, core_core_adapters_report_store_local, gherkai_gherkai_compose [EXTRACTED 0.90]
- **三 port 正交：RunStore 控制面 / ResultStore 数据面 / ReportStore 派生视图** — docs_adr_0030_run_store, docs_adr_0030_result_store, docs_adr_0027_reportstore, docs_adr_0030_commit_point [EXTRACTED 0.90]

## Communities (166 total, 50 thin omitted)

### Community 0 - "test_schedule.py"
Cohesion: 0.06
Nodes (121): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), 成本可观测（engine 只报原生量、core 不折美元）, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在… (+113 more)

### Community 1 - "DdbEventLog"
Cohesion: 0.10
Nodes (24): DdbEventLog, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, events_pk(), events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。 (+16 more)

### Community 2 - "test_detached_launcher.py"
Cohesion: 0.12
Nodes (31): build_local_reconcile(), _paths(), 无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按… (+23 more)

### Community 3 - "test_run_step.py"
Cohesion: 0.07
Nodes (33): captured(), _done(), _FakeNova, _FakeResult, _FakeSink, _Meta, _NavErrorNova, fixture (+25 more)

### Community 4 - "test_plan.py"
Cohesion: 0.06
Nodes (67): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, _index_ast_lines(), _map_argument(), parse_feature(), ParsedScenario, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子… (+59 more)

### Community 5 - "test_stack.py"
Cohesion: 0.06
Nodes (49): Cluster, Construct, BackendStack, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED…, 把 Lambda 代码打包到一个目录，返回其路径（Code.from_asset 用）。 内容 = lambdas/*.py（handler）+…, worker 安全组 id——_ssm_network 建的 sg。存引用供 reconciler Lambda 起 task 用同一 sg。 (+41 more)

### Community 6 - "test_artifact_upload.py"
Cohesion: 0.15
Nodes (15): _Calls, ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, upload_file 调用记录：list 元素 = (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。, 半注入(有桶缺 NOVA_LOGS_DIR)→ 装配矛盾 fail-loud(静默 no-op 会让产物随容器盘销毁必丢,ADR 0033)。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用；fail_keys 里的 key 抛错）。, test_bucket_without_logs_dir_fails_loud(), test_content_type_suffix_match_is_case_insensitive(), test_flush_failure_swallowed_but_dir_kept() (+7 more)

### Community 7 - "test_project.py"
Cohesion: 0.09
Nodes (56): plan_next(), project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, _ev(), _exit(), _meta(), _passed_events() (+48 more)

### Community 8 - "DynamoDBRunStore"
Cohesion: 0.06
Nodes (42): DynamoDBRunStore, _job_state_to_item(), 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。 (+34 more)

### Community 9 - "Job"
Cohesion: 0.11
Nodes (42): Job, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。, 一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。, 一个 job = 一个 scope = 一个会话边界 = schedule 交给单个 worker 的活（ADR 0016/0024/0025）。, Scenario, Step, StepArgument (+34 more)

### Community 10 - "model.py"
Cohesion: 0.16
Nodes (19): render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。, _sample_run(), test_render_text_annotates_shortcircuited_step(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_no_annotation_on_plain_failed(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar(), 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core… (+11 more)

### Community 11 - "test_cloud_reconcile.py"
Cohesion: 0.11
Nodes (23): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, events_table(), _FakeStartEngine, _job(), fixture (+15 more)

### Community 12 - "test_transient_network.py"
Cohesion: 0.05
Nodes (44): _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings(), test_presend_ignores_non_html(), test_presend_skips_when_no_sibling_json() (+36 more)

### Community 13 - "test_lambda_handlers.py"
Cohesion: 0.12
Nodes (21): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带… (+13 more)

### Community 14 - "devDependencies"
Cohesion: 0.05
Nodes (38): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-dynamodb, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, author (+30 more)

### Community 15 - "test_interrupt_model.py"
Cohesion: 0.07
Nodes (20): captured(), _FakeResult, _FakeSink, _Meta, fixture, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM…, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。 (+12 more)

### Community 16 - "__main__.py"
Cohesion: 0.11
Nodes (35): ArgumentParser, _build_parser(), _cmd_list_deterministic(), _cmd_list_engines(), _cmd_plan(), _cmd_reconcile(), _cmd_run(), _cmd_status() (+27 more)

### Community 17 - "RunState"
Cohesion: 0.08
Nodes (40): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…, RunState, run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。 满足 ADR…, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale… (+32 more)

### Community 18 - "main"
Cohesion: 0.10
Nodes (46): main(), _capturing_schedule(), _det_feature(), _fake_schedule_factory(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS）， 验证落盘三层产物 + --json…, 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job…, 假 schedule：把传入 opts 存进 opts_box、按指定 status 合成 RunResult（验退出码/参数映射）。 (+38 more)

### Community 19 - "ArtifactUploader"
Cohesion: 0.14
Nodes (14): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→…, upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。 (+6 more)

### Community 20 - "test_reconcile.py"
Cohesion: 0.12
Nodes (26): 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher, _meta(), Job, reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。 用真… (+18 more)

### Community 21 - "agentcore-sigv4.mts"
Cohesion: 0.07
Nodes (27): ADR-0010, getBaseUrl(), getRegion(), MODEL, modelSigner_(), ADR-0033, signCdpUpgrade(), sigv4Fetch() (+19 more)

### Community 22 - "compose.py"
Cohesion: 0.10
Nodes (25): cli/__main__.py（argparse 皮 + 退出码）, build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_ecs_client(), _make_lambda_client(), make_resolver(), _make_s3_client() (+17 more)

### Community 23 - "test_backend_cloud.py"
Cohesion: 0.15
Nodes (33): _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 不起 worker 的假 schedule：走完 on_event/on_job_complete 实时落库路径（让 adapter 真被调）。, submit cloud 的 preflight 除表/桶/cluster 外还探：本 run 用到引擎的 task-def + 事件驱动链三 Lambda…, 非默认 --report-dir 也要交给 preflight 比对（否则提交侧/推进侧前缀静默分裂、结果落别处）。, preflight 报资源缺（如链上 Lambda 不存在）→ 提交前退 2、不写任何东西。 (+25 more)

### Community 24 - "test_report_store.py"
Cohesion: 0.28
Nodes (23): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。 (+15 more)

### Community 25 - "_engine"
Cohesion: 0.14
Nodes (30): _engine(), _job(), _put_event(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。, worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。, worker 发完 scope_done 又非 0 退出（会话释放失败，Midscene cleanupFailed→exit 1）： scope_done… (+22 more)

### Community 26 - "test_tunnel_host.py"
Cohesion: 0.15
Nodes (18): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, Σ(各 job 预算) + 启动余量——cloud 档并发恒 1（ADR 0034），求和是保守上界。 (+10 more)

### Community 27 - "NgrokTunnel"
Cohesion: 0.24
Nodes (9): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None=不写，覆盖超时路径）。, test_ngrok_binary_missing_reports_install_hint(), test_ngrok_start_spawns_agent_and_reads_log(), test_ngrok_start_timeout_reports_authtoken_hint() (+1 more)

### Community 28 - "JobState"
Cohesion: 0.07
Nodes (38): LocalRunStore, Path, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新…, CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。, HWM 条件写 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。 **run 级 status 钳为…, 状态机单调条件写：仅当当前总 status 为非终态才写终态（机制三，commit 恰一次）。, RunStore 的本地文件实现（组合根注入；未来 DDB 版换落点/读写）。 (+30 more)

### Community 29 - "RunPersistence"
Cohesion: 0.27
Nodes (19): LocalResultStore, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, RunPersistence, _jr(), _meta(), RunPersistence 应用服务直测（ADR 0030）：脱离 cli/schedule，用 fake store 直接验 core 层不变量。…, 钉死「两面分离」（ADR 0016 三层切分 + 0030）——用户实测会困惑的点： job 处于 RUNNING 时，控制面 run_state.json… (+11 more)

### Community 30 - "test_stores.py"
Cohesion: 0.09
Nodes (42): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, RunStore adapters（ADR 0016）。当前只有 local；未来 ddb。, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR…, 读回 definition（RunMeta）；不存在返回 None。, _argument_from_dict(), _argument_to_dict(), from_dict() (+34 more)

### Community 31 - "ValueError"
Cohesion: 0.12
Nodes (17): test_classify_unknown_falls_back_engine_error(), test_value_error_not_transient(), is_botocore_error(), _make_ssm_client(), BaseException, boto3 ssm client（读 subnet/sg 的确定性路径参数）。, 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK… (+9 more)

### Community 32 - "RunMeta"
Cohesion: 0.06
Nodes (40): Ports 层（Engine/RunStore/ResultStore/ReportStore）, _job_state_from_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, RunMeta, Status (+32 more)

### Community 33 - "reconciler.py"
Cohesion: 0.12
Nodes (22): finalize_artifacts(), done 后聚合判定真值 + RunReport（幂等；ADR 0034 收尾，对齐同步 run 路径产物）。 tick 的 try_finalize 只写…, datetime, parse_iso(), `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, _build(), _handle_timeout(), handler() (+14 more)

### Community 34 - "test_fargate_engine.py"
Cohesion: 0.17
Nodes (17): _delayed_stopped_ecs(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env(), test_final_drain_paginates_across_last_evaluated_key() (+9 more)

### Community 35 - "ADR 0034 — Detached Batch Reconciler"
Cohesion: 0.28
Nodes (17): CLAUDE.md 项目约定, cli README（最薄前端/组合根皮）, CONTEXT.md 领域术语表, 执行核心库窄腰（概念）, 通用 step（QA 零代码的唯一载体）, Run 数据模型 Run⊃Job(=Scope)⊃Scenario⊃Step, core README（执行核心库窄腰）, ADR 0016 执行架构：核心库窄腰 + Run 数据模型 + ports (+9 more)

### Community 36 - "FargateEngine"
Cohesion: 0.20
Nodes (10): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+2 more)

### Community 37 - "run-scope.ts"
Cohesion: 0.09
Nodes (22): ADR-0019, ADR-0026, ADR-0027, ADR-0032, ADR-0035, AWS_TRANSIENT_NAMES, AWS_TRANSIENT_STATUS, CONNECT_BACKOFF_MS (+14 more)

### Community 38 - "_FakeEcsClient"
Cohesion: 0.17
Nodes (12): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, test_preflight_all_present_returns_none(), test_preflight_missing_chain_lambda_names_prefix() (+4 more)

### Community 39 - "run_scope.py"
Cohesion: 0.16
Nodes (19): ArtifactUploader, engines/novaact README, _aggregate(), _attach_traj_refs(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _get_uploader(), log() (+11 more)

### Community 40 - "build_engines"
Cohesion: 0.11
Nodes (32): build_engines(), build_local_stores(), load_feature(), match_deterministic(), Path, query_deterministic(), 定位仓库根（含 core/ 与 engines/ 的目录）。 从本文件位置上溯：gherkai/gherkai/compose.py → gherkai/ →…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 两个引擎"spawn 子进程 + 讲同一套 ADR… (+24 more)

### Community 41 - "gherkai/names.py"
Cohesion: 0.14
Nodes (14): default_name(), job_timeout_schedule_prefix(), 资源命名真源（gherkai 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。 **零依赖**（不…, prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。, job timeout schedule 的名字空间前缀 `{prefix}job-timeout-`（其后接 run+scope 摘要段）。 **含尾部…, subnet/sg 的 SSM 参数路径（含 prefix，cli 已知 prefix 拼路径读，无循环——ADR 0033）。, ssm_path(), 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai.names`（真同源）**。 曾因「CDK… (+6 more)

### Community 42 - "0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器"
Cohesion: 0.18
Nodes (10): 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器, 1. `TunnelProvider` 可插拔口子（gherkai 组合根层），首个实现 = ngrok, 2. URL 映射：feature 写原始地址，组装 job 时替换, 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态, 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）, 决策, 背景与问题, 被拒/被缓方案（护栏） (+2 more)

### Community 44 - "ArtifactUploader"
Cohesion: 0.17
Nodes (6): ArtifactUploader, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0033

### Community 45 - "ADR 0031 job 生命周期态 skipped/aborted + severity 数值序"
Cohesion: 0.16
Nodes (16): 连锁失败读法（error → 后续 step 短路跳过）, 被拒方案：materialize 产物拷贝, ADR 0027: RunReport 跨引擎归集索引, ADR 0028: Transient Network/SSL Resilience, Hand-written exponential backoff with _stop.wait, botocore transient/throttled error code tables (inlined), _is_transient_network(e, *, connecting=False) (Python whitelist), isTransientNetwork (Node/Midscene whitelist) (+8 more)

### Community 46 - "_Worker"
Cohesion: 0.15
Nodes (12): Event, 把单个 worker 事件归约进 JobResult（就地累积，ADR 0024/0026）。 **这是 `schedule._Worker._reduce`…, reduce_event(), _heartbeat_wrap(), Event, Job, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error… (+4 more)

### Community 47 - "exit_observer.py"
Cohesion: 0.27
Nodes (9): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+1 more)

### Community 48 - "deterministic.ts"
Cohesion: 0.12
Nodes (22): ADR-0015, _clear(), deterministic(), DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta (+14 more)

### Community 49 - "run-scope.test.ts"
Cohesion: 0.12
Nodes (10): _events, fakePage, importMod(), testSink, ADR-0014, ADR-0024, ADR-0028, ADR-0029 (+2 more)

### Community 50 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 51 - "S3ResultStore"
Cohesion: 0.21
Nodes (7): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, test_prefix_isolates_runs()

### Community 52 - "ADR 0022 BDD runner 退役 + 薄 worker"
Cohesion: 0.15
Nodes (15): ADR 0001 范围限英文 UI, ADR 0005 单一共享 .feature, ADR 0006 形态 A 两子工程并列, ADR 0007 程序化登录 / HITL 逃生舱, ADR 0010 双引擎苹果对苹果对标, ADR 0011 AgentCore 浏览器默认 vs 自建, ADR 0013 跨引擎共享边界, ADR 0014 AI 断言为主 + 投票治抖动 (+7 more)

### Community 53 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 54 - "{prefix}cluster + Fargate task definitions"
Cohesion: 0.50
Nodes (4): Worker ECR repositories, {prefix}cluster + Fargate task definitions, EventBridge rule {prefix}ecs-stopped, Per-engine task roles + shared execution role

### Community 55 - "S3ReportStore"
Cohesion: 0.10
Nodes (12): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install core[aws]`）；模块 import 不崩、构造时才检。, require_boto3(), S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。 把一次 run 的…, ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore (+4 more)

### Community 56 - "wire.py"
Cohesion: 0.12
Nodes (19): Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, 一次 DescribeTasks 探测的结果——**两个正交事实各自命名**（ADR 0024「exitCode 落值延迟」）： -…, TaskProbe, _argument_to_json(), _cost_from_json(), job_to_json(), job_to_line(), Job (+11 more)

### Community 57 - "test_tunnel_cli.py"
Cohesion: 0.12
Nodes (23): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+15 more)

### Community 58 - "e2e_harness 使用说明"
Cohesion: 0.18
Nodes (13): ADR 0014 AI 断言投票, ADR 0024 worker↔core 协议 / 终止契约, ADR 0025 @scope: tag 分组, ADR 0029 产物→S3 / 边界抢传 / 固有残余, ADR 0032 Fargate 中断丢失量级 + 真容器 grace 校准, e2e_harness 使用说明, 边界抢传（act / scenario 边界）, grace 测量与 SIGKILL 兜底 (+5 more)

### Community 59 - "_FakeEcs"
Cohesion: 0.22
Nodes (5): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…

### Community 60 - "TaskExited"
Cohesion: 0.12
Nodes (14): Connection, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。 (+6 more)

### Community 61 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 62 - "build_push_workers.py"
Cohesion: 0.22
Nodes (12): _account_id(), build_push(), _ecr_login(), main(), Path, ECR repo 名 = {prefix}{engine}-worker（对齐 gherkai.names.task_def_name，见…, 跑一条命令；dry-run 只打印。失败即抛（subprocess.run check=True）——不吞错、让调用者见真况。, 取当前账户 id（拼 ECR registry host）。dry-run 时用占位符（不真调 AWS）。 (+4 more)

### Community 63 - "_mk_state"
Cohesion: 0.23
Nodes (12): _args(), _mk_state(), pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。, test_render_status_json_no_hint() (+4 more)

### Community 64 - "ScopeStarted"
Cohesion: 0.12
Nodes (24): ScopeStarted, Action, _aggregate(), EventRecord, _job_status(), project_full(), Job, 纯归约投影（ADR 0034）：events → JobResult/RunState，无 I/O、无执行编排、不 import boto3。… (+16 more)

### Community 67 - "CloudTarget"
Cohesion: 0.24
Nodes (10): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态跑批事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序＝链上顺序。, 把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_cloud_target(), _clear_aws_env(), test_resolve_cloud_target_default_prefix_when_nothing_given(), test_resolve_cloud_target_derives_all_names_from_prefix() (+2 more)

### Community 68 - "0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询"
Cohesion: 0.10
Nodes (20): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）, ADR 0020: Step 措辞——默认 AI + 确定性锚点脚手架, 默认 AI 判断（裸 When/Then 无路由关键词） (+12 more)

### Community 69 - "test_s3_report_store.py"
Cohesion: 0.31
Nodes (10): S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index(), test_index_html_links_and_summary(), test_index_html_taints_shortcircuited_step(), test_manifest_shape() (+2 more)

### Community 70 - "conftest.py"
Cohesion: 0.12
Nodes (22): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), fixture, 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -… (+14 more)

### Community 71 - "event-sink.mts"
Cohesion: 0.22
Nodes (6): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0033, resolveEventsFd()

### Community 72 - "ReportStore.write（整 run 一次写）"
Cohesion: 0.22
Nodes (10): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, LocalReportStore, manifest.json（薄信封 + report_index）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写）, ResourceUri（带 scheme 的统一指针）, run_id（组合根生成、归集主键） (+2 more)

### Community 74 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 76 - "ecs_task_timing.py"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 77 - "RunPersistence 应用服务"
Cohesion: 0.22
Nodes (9): commit-point 写序（数据面先、控制面后）, DDB 单表 META/STATE 两 item, on_job_complete / on_event 回调（JobSink）, Store.preflight() 探活 + 退出码分层, ResultStore（判定真值、S3 后端）, RunPersistence 应用服务, RunState.jobs 改 Map<scope_id>, RunStore（create_run/update_job_state/finalize_run） (+1 more)

### Community 78 - "JobSource"
Cohesion: 0.22
Nodes (4): Job, JobSource, ADR-0016, ADR-0024

### Community 79 - "render.py"
Cohesion: 0.17
Nodes (15): _arg_hint(), _cost_bits(), _dispatch_hint(), _ms(), plan_to_dict(), Job, 渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…, plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。 dispatch（可选，ADR 0036… (+7 more)

### Community 80 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 81 - "ADR 0003 Qwen3-VL on Bedrock 做 grounding"
Cohesion: 0.36
Nodes (8): ADR 0002 不用 Bedrock GPT-5.5, ADR 0003 Qwen3-VL on Bedrock 做 grounding, ADR 0004 Nova Act 纯 IAM 经 Workflow 鉴权, ADR 0008 Midscene SigV4 自签鉴权, ADR 0009 最大化使用 AWS 硬约束, ADR 0012 planning 复用 Qwen3-VL, 文档健康度复盘任务, SIGV4-FETCH-RECIPE 配方笔记

### Community 82 - "schedule._Worker._run_once"
Cohesion: 0.29
Nodes (8): EX_WORKER_NETWORK = 80 exit code, schedule._heartbeat_wrap (silent-worker timeout fix), ScheduleOpts (network_retry, retry_sleep), schedule._Worker.run (network retry loop), schedule._Worker._run_once, Session leak protection before exit, subprocess_engine._read_events, core.errors.WorkerNetworkError

### Community 83 - "_FakeProc"
Cohesion: 0.22
Nodes (6): 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, TunnelInfo, _FakeProc, test_mapped_base_embeds_credentials(), test_mapped_base_without_auth_is_plain_url()

### Community 84 - "argument.ts"
Cohesion: 0.39
Nodes (7): argumentText(), buildInstruction(), cleanCell(), StepArgument, ADR-0024, ADR-0024, unquote()

### Community 85 - "_stopped_detail"
Cohesion: 0.17
Nodes (12): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, container 缺 exitCode（宽限态）→ None（机制二保守）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, _stopped_detail(), test_exit_observer_records_exit_for_detached_run(), test_exit_observer_skips_non_detached_run() (+4 more)

### Community 86 - "test_compose.py"
Cohesion: 0.10
Nodes (26): engine_min_grace(), prune_empty_dirs(), 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, resolve_region(), _preflight_report_dir(), compose（组合根逻辑）单测：不起任何子进程、不烧钱。 (+18 more)

### Community 88 - "ensure_workflow_definition"
Cohesion: 0.21
Nodes (9): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（worker/run_scope.py）与 spike…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开…, run() (+1 more)

### Community 89 - "RunResult"
Cohesion: 0.11
Nodes (20): 报告产物模型 / RunReport 归集索引, ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。, collect_report_index(), _fmt_ms(), _local_path(), Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出… (+12 more)

### Community 90 - "ADR 0017: Cloud Execution — Fargate over Runtime"
Cohesion: 0.33
Nodes (6): ADR 0017: Cloud Execution — Fargate over Runtime, AgentCore Evaluations（LLM-as-Judge，被否）, AgentCore Runtime（长驻 agent 服务）, 批处理 workload shape（run-to-exit）, ECS RunTask / Fargate 执行后端, 15 分钟 idle-kill 计时器与保活 plumbing

### Community 92 - "test_read_events_ignores_exit_item_on_stopped_drain_path"
Cohesion: 0.50
Nodes (4): _put_exit_item(), 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, worker 零事件退出 + exit item 已落：STOPPED 兜底路径（含 _final_drain 强一致终读）同样只读 worker 段。…, test_read_events_ignores_exit_item_on_stopped_drain_path()

### Community 93 - "echo_worker.py"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 95 - "artifact-upload.test.ts"
Cohesion: 0.50
Nodes (3): mkLogDir(), tmproot(), ADR-0029

### Community 96 - "projected_run_status"
Cohesion: 0.50
Nodes (4): projected_run_status(), 投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。…, 全 job pending → pending（run 还没起过任何 job）；任一 job 推进 → running；恒非终态（终态归 finalize）。, test_projected_run_status_pending_only_while_all_jobs_pending()

### Community 97 - "权威信息源 REFERENCES"
Cohesion: 0.50
Nodes (4): 权威信息源 REFERENCES, AWS Bedrock / AgentCore 文档, Midscene 官方文档与源码 ground truth, Nova Act SDK 与 AgentCore provider

### Community 98 - "Midscene SigV4 自签 fetch 配方"
Cohesion: 0.50
Nodes (4): engines/midscene README, Midscene SigV4 自签 fetch 配方, createOpenAIClient 隔离 ModelConfigManager 坑, sigv4Fetch（最小手建请求签名）

### Community 100 - "gherkai"
Cohesion: 0.67
Nodes (4): cli, core, gherkai, iac-aws-backend

### Community 111 - "DynamoDB stream event source mappings"
Cohesion: 0.67
Nodes (3): DynamoDB stream event source mappings, {prefix}events DynamoDB table, {prefix}runs DynamoDB table

### Community 112 - "subprocess_engine.py"
Cohesion: 0.11
Nodes (14): _pump_log(), Event, Job, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的… (+6 more)

### Community 119 - "test_deterministic.py"
Cohesion: 0.06
Nodes (30): deterministic, deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match(), match_batch() (+22 more)

### Community 126 - "cloud_env"
Cohesion: 0.67
Nodes (3): cloud_env(), fixture, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。

### Community 127 - "test_sqlite_event_log.py"
Cohesion: 0.23
Nodes (12): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, test_append_and_read_back_events(), test_append_idempotent_same_seq() (+4 more)

### Community 128 - "JobResult"
Cohesion: 0.12
Nodes (8): 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的…, 数据面：每 job(=scope) 判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。 local adapter =…, ResultStore

### Community 129 - "test_wire.py"
Cohesion: 0.17
Nodes (19): event_from_json(), event_from_line(), Event, JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。 事件通道随形态而异：子进程态 =…, worker 事件通道一行（子进程态 = EVENTS_FD 的 fd；Fargate 态 = DDB events 表 body）→ model.Event。, wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。, 80 是跨语言约定值（两个引擎 worker 各自硬编码）——改这个数即改协议，须同步两 worker。, test_event_from_line() (+11 more)

### Community 135 - "main"
Cohesion: 0.24
Nodes (11): aggregate(), cumulativeTokens(), isTransientNetwork(), log(), main(), modelConfig(), runScenario(), runStep() (+3 more)

### Community 139 - "_FakeEcs"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 140 - "tunnel_host.py"
Cohesion: 0.25
Nodes (8): 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 141 - "tunnel.py"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 142 - "_run_step"
Cohesion: 0.17
Nodes (10): _collect_traj(), _cost_from_result(), _DeterministicCtx, 报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。, 从 act/act_get 结果的 metadata 收集本次 act 的 trajectory **HTML** 路径（ADR 0027）。 Nova 每次…, 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+2 more)

### Community 144 - ".load_run_meta"
Cohesion: 0.29
Nodes (6): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…, 读回 definition（从 META item 的 meta_json）；不存在返回 None。

### Community 145 - "S3StepArgumentOffloader"
Cohesion: 0.24
Nodes (6): 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, S3StepArgumentOffloader

### Community 146 - "test_s3_result_store.py"
Cohesion: 0.29
Nodes (8): S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…, test_load_all_paginated_preserves_failed_verdict(), test_load_all_paginates_beyond_1000(), test_load_all_stable_order(), test_save_load_round_trip(), test_scope_id_with_slash_not_subprefix(), _job_def(), Job

### Community 148 - "stop_tunnel"
Cohesion: 0.29
Nodes (7): cleanup_tunnel(), 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 149 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 151 - "test_tunnel.py"
Cohesion: 0.33
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 152 - "raise_for_worker_exit"
Cohesion: 0.25
Nodes (8): raise_for_worker_exit(), worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, test_raise_for_worker_exit_maps_codes_with_fargate_label(), 码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 /…, 两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。, test_raise_for_worker_exit_label_names_the_transport_field(), test_raise_for_worker_exit_maps_codes()

### Community 153 - "ArtifactUploader（from_env/to_report_ref/flush）"
Cohesion: 0.25
Nodes (8): act 边界抢传（snapshot / step_done 安全点）, ArtifactUploader（from_env/to_report_ref/flush）, 删本地（上传成功确认后整目录删）, ADR 0029: engine artifact→S3（worker 上传）, 注入驱动的 S3 落点（ARTIFACT_S3_BUCKET/PREFIX）, 固有残余（session_summary/log/traces 不救）, S3 key 镜像本地 run 树, 上传必须套超时（退出时间有界）

### Community 154 - "_instruction"
Cohesion: 0.25
Nodes (8): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote()

### Community 155 - "_is_transient_network"
Cohesion: 0.38
Nodes (7): _classify_act_error(), _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…

### Community 156 - "iac_aws_backend README"
Cohesion: 0.50
Nodes (4): ADR 0016 — Composition Root Shared Layer, ADR 0024 — Synchronous Run Query Polling, iac_aws_backend README, VPC/subnets/security-groups + SSM parameters

## Ambiguous Edges - Review These
- `通用 step（QA 零代码的唯一载体）` → `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md · relation: conceptually_related_to

## Knowledge Gaps
- **180 isolated node(s):** `背景与问题`, `调研结论（内联，自包含）`, `1. `TunnelProvider` 可插拔口子（gherkai 组合根层），首个实现 = ngrok`, `2. URL 映射：feature 写原始地址，组装 job 时替换`, `3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **50 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `通用 step（QA 零代码的唯一载体）` and `ADR 0019 用 Gherkin tag 声明 scope 与 engine`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Job` connect `Job` to `JobResult`, `test_schedule.py`, `test_wire.py`, `test_detached_launcher.py`, `test_plan.py`, `test_project.py`, `DynamoDBRunStore`, `model.py`, `test_cloud_reconcile.py`, `tunnel_host.py`, `tunnel.py`, `_FakeEcs`, `RunState`, `test_s3_result_store.py`, `test_reconcile.py`, `test_report_store.py`, `_engine`, `NgrokTunnel`, `JobState`, `RunPersistence`, `test_stores.py`, `RunMeta`, `test_fargate_engine.py`, `FargateEngine`, `_Worker`, `wire.py`, `_FakeEcs`, `TaskExited`, `ScopeStarted`, `_SeqEcs`, `_FakeProc`, `subprocess_engine.py`, `test_sqlite_event_log.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `Status` connect `RunMeta` to `test_schedule.py`, `JobResult`, `test_wire.py`, `test_detached_launcher.py`, `test_project.py`, `DynamoDBRunStore`, `Job`, `model.py`, `test_cloud_reconcile.py`, `_FakeEcs`, `RunState`, `test_s3_result_store.py`, `test_reconcile.py`, `EventBridgeTimeoutWatch`, `test_report_store.py`, `test_tunnel_host.py`, `JobState`, `RunPersistence`, `test_stores.py`, `test_fargate_engine.py`, `_Worker`, `wire.py`, `_FakeEcs`, `TaskExited`, `ScopeStarted`, `test_s3_report_store.py`, `_FakeTable`, `_SeqEcs`, `_FakeS3`, `projected_run_status`, `test_sqlite_event_log.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `RunMeta` connect `RunMeta` to `JobResult`, `test_schedule.py`, `DdbEventLog`, `test_detached_launcher.py`, `test_project.py`, `DynamoDBRunStore`, `Job`, `model.py`, `test_cloud_reconcile.py`, `_FakeEcs`, `__main__.py`, `.load_run_meta`, `RunState`, `test_reconcile.py`, `test_report_store.py`, `JobState`, `RunPersistence`, `test_stores.py`, `_Worker`, `TaskExited`, `ScopeStarted`, `test_sqlite_event_log.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `RunMeta` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunMeta` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 23 INFERRED edges - model-reasoned connections that need verification._