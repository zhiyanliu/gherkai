# Graph Report - yaozhou  (2026-08-13)

## Corpus Check
- 170 files · ~119,705 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2249 nodes · 4662 edges · 141 communities (107 shown, 34 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 845 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5952042c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- schedule
- LocalReportStore
- test_run_step.py
- wire.py
- test_main.py
- parse_feature
- .load_run_state
- project
- LocalRunStore
- devDependencies
- test_transient_network.py
- test_interrupt_model.py
- DynamoDBRunStore
- test_compose.py
- __main__.py
- _Worker
- sigv4Fetch
- tick
- ArtifactUploader
- test_stack.py
- serialize.py
- model.py
- test_backend_cloud.py
- DdbEventLog
- RunPersistence
- ADR 0016 执行架构：核心库窄腰 + Run 数据模型
- _engine
- run-scope.ts
- ArtifactUploader（from_env/to_report_ref/flush）
- test_conditional_writes.py
- Engine
- BackendStack
- scope.py
- FargateEngine
- WorkerNetworkError
- S3StepArgumentOffloader
- RunPersistence 应用服务
- run_reconcile_loop
- compose.py
- ResourceUri
- ADR 0025: plan 模块（feature → jobs）
- JobSource
- 代码健康度复盘任务说明
- render.py
- test_lambda_handlers.py
- project.py
- Scenario
- run-scope.test.ts
- core/model.py 领域模型
- conftest.py
- test_plan.py
- JobResult
- names.py
- events_wallclock.py
- _FakeEcs
- Status
- deterministic.ts
- ReportStore.write（整 run 一次写）
- ArtifactUploader
- 文档纪律（ADR / CONTEXT）
- S3ResultStore
- run_scope.py
- e2e_harness 使用说明
- ADR 0018: 通用 step 能力清单
- build_push_workers.py
- build_cloud_stores
- _FakeDdbClient
- require_boto3
- workflow_setup.py
- test_argument.py
- Job
- deterministic.py
- _run_step
- _is_transient_network(e, *, connecting=False) (Python whitelist)
- test_event_sink.py
- ecs_task_timing.py
- load_feature
- JobState
- RunState
- _read_events
- _spawn_and_wait_ready
- Path
- ADR 0003 Qwen3-VL on Bedrock 做 grounding
- schedule._Worker._run_once
- _instruction
- test_deterministic.py
- SqliteEventLog
- e2e_harness.py
- argument.ts
- _is_transient_network
- step 级短路：step_skipped + shortcircuited 布尔
- test_sqlite_event_log.py
- Protocol
- reconcile.py
- ADR 0017: Cloud Execution — Fargate over Runtime
- reconciler.py
- 权威信息源 REFERENCES
- echo_worker.py
- test_cloud_infra.py
- core/tests/test_subprocess_engine.py
- ADR 0007 程序化登录 / HITL 逃生舱
- deterministic
- Midscene SigV4 自签 fetch 配方
- interrupt_worker.py
- ADR 0034: 无状态跑批（CQRS + reconciler）
- _put_event
- _job_def
- StepArgument
- cli/__init__.py
- event_log/__init__.py
- adapters/__init__.py
- report_store/__init__.py
- result_store/__init__.py
- run_store/__init__.py
- core/__init__.py
- Protocol
- cli
- core/wire.py 线序列化
- 开放性动作导致页面瞬态 flaky
- session_id lineage on scope_started
- iac-aws-backend
- novaact
- wikipedia SSL 环境坑
- StepArgument
- StepArgument
- test_fargate_engine.py
- build_local_reconcile
- EventSink
- CloudLauncher
- EventSink
- events_pk
- BaseException
- JobState
- RunMeta
- RunState
- test_read_events_scope_done_waits_for_stopped_before_reading_exit
- RunState
- EngineResolver
- Path
- BaseException

## God Nodes (most connected - your core abstractions)
1. `schedule()` - 61 edges
2. `Job` - 56 edges
3. `CollectSink` - 56 edges
4. `FakeEngine` - 53 edges
5. `JobResult` - 51 edges
6. `FakeResolver` - 50 edges
7. `_job()` - 43 edges
8. `_rm()` - 43 edges
9. `RunResult` - 40 edges
10. `project()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `test_format_event_omits_scope_id()` --calls--> `ScopeDone`  [INFERRED]
  cli/tests/test_render.py → core/core/model.py
- `build_local_reconcile()` --calls--> `LocalReportStore`  [INFERRED]
  cli/cli/detached.py → core/core/adapters/report_store/local.py
- `build_local_reconcile()` --calls--> `LocalResultStore`  [INFERRED]
  cli/cli/detached.py → core/core/adapters/result_store/local.py
- `_tick_runs()` --calls--> `finalize_artifacts()`  [INFERRED]
  lambdas/reconciler.py → core/core/reconcile.py
- `_tick_runs()` --calls--> `tick()`  [INFERRED]
  lambdas/reconciler.py → core/core/reconcile.py

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

## Communities (141 total, 34 thin omitted)

### Community 0 - "schedule"
Cohesion: 0.20
Nodes (50): RunMeta, RunResult, 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver (+42 more)

### Community 1 - "LocalReportStore"
Cohesion: 0.06
Nodes (69): collect_report_index(), _fmt_ms(), _local_path(), LocalReportStore, Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。  产出 <report_root>/<run_id>, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+61 more)

### Community 2 - "test_run_step.py"
Cohesion: 0.06
Nodes (35): 两个 adapter 各来一遍（对拍）。local 用 tmp_path；ddb 用 moto aws fixture。, run_store(), captured(), _done(), _FakeNova, _FakeResult, _FakeSink, _Meta (+27 more)

### Community 3 - "wire.py"
Cohesion: 0.08
Nodes (57): test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…, ScenarioDone, ScenarioStarted (+49 more)

### Community 4 - "test_main.py"
Cohesion: 0.08
Nodes (38): _args(), _capturing_schedule(), _fake_schedule_factory(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS），  验证落盘三层产物 + --json 输出形状, 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job, 假 schedule：把传入 opts 存进 opts_box、按指定 status 合成 RunResult（验退出码/参数映射）。, 返回一个替换 compose.build_local_stores 的 fake：产出三个记录调用的 fake store + make_artifacts。 (+30 more)

### Community 5 - "parse_feature"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是…, pickle step type → 派发关键字（Given/When/Then）。type='Unknown' 一律 fail-fast。 Compiler… (+8 more)

### Community 6 - ".load_run_state"
Cohesion: 0.11
Nodes (15): JobState, RunMeta, RunState, Status, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新…, CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）。, HWM 条件写 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。 **run 级 status 钳为…, 状态机单调条件写：仅当当前总 status 为非终态才写终态（机制三，commit 恰一次）。 (+7 more)

### Community 7 - "project"
Cohesion: 0.10
Nodes (49): ScopeStarted, project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, _ev(), _exit(), _meta(), _passed_events(), RunMeta (+41 more)

### Community 8 - "LocalRunStore"
Cohesion: 0.17
Nodes (23): LocalRunStore, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, RunStore 的本地文件实现（组合根注入；未来 DDB 版换落点/读写）。, from_dict(), RunResult → 朴素 dict（机器可读：CI / WebUI / manifest 消费）。 normalize（ADR 0016…, 朴素 dict → RunResult。与 to_dict 往返一致（round-trip 单测护栏）。 def 唯一真值在…, to_dict(), Path (+15 more)

### Community 9 - "devDependencies"
Cohesion: 0.05
Nodes (37): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-dynamodb, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, author (+29 more)

### Community 10 - "test_transient_network.py"
Cohesion: 0.05
Nodes (31): 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在… (+23 more)

### Community 11 - "test_interrupt_model.py"
Cohesion: 0.08
Nodes (18): captured(), _FakeResult, _FakeSink, _Meta, flag-only 中断模型单测（ADR 0024 终止契约）。  锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。 (+10 more)

### Community 12 - "DynamoDBRunStore"
Cohesion: 0.10
Nodes (21): DynamoDBRunStore, _job_state_from_item(), _job_state_to_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending… (+13 more)

### Community 13 - "test_compose.py"
Cohesion: 0.08
Nodes (14): Path, compose（组合根逻辑）单测：不起任何子进程、不烧钱。, test_build_engines_artifact_s3_alone_makes_env_nonnull(), test_build_engines_injects_artifact_dirs_symmetrically(), test_build_engines_injects_artifact_s3_env_symmetrically(), test_build_engines_midscene_no_rebuild_when_no_region_profile(), test_build_engines_no_artifact_s3_env_has_no_s3_keys(), test_build_engines_no_dirs_midscene_env_none() (+6 more)

### Community 14 - "__main__.py"
Cohesion: 0.09
Nodes (43): ArgumentParser, build_local_stores(), default_name(), new_run_id(), now_iso(), preflight_cloud_resources(), 生成一个 run_id（组合根职责，ADR 0027）。 对调用方不透明，只保证「可排序（时间戳前缀）+ 抗碰撞（随机尾）」。格式是 compose…, manifest created_at 时间戳（组合根取时钟，core 不取，ADR 0027）。 (+35 more)

### Community 15 - "_Worker"
Cohesion: 0.15
Nodes (13): _heartbeat_wrap(), EngineResolver, Event, Job, JobResult, Status, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error… (+5 more)

### Community 16 - "sigv4Fetch"
Cohesion: 0.12
Nodes (24): ADR-0010, getBaseUrl(), getRegion(), modelSigner_(), signCdpUpgrade(), sigv4Fetch(), ADR-0033, BASE_URL (+16 more)

### Community 17 - "tick"
Cohesion: 0.08
Nodes (34): EventLog, Launcher, Job, RunMeta, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 local = 起 subprocess worker（事件旁路落 SQLite…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick() (+26 more)

### Community 18 - "ArtifactUploader"
Cohesion: 0.07
Nodes (32): ArtifactUploader, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→… (+24 more)

### Community 19 - "test_stack.py"
Cohesion: 0.12
Nodes (30): BackendStack 合成断言测试（ADR 0033）：纯本地 synth、不碰 AWS。  用 CDK assertions.Template 断言关键契, IAM 资源 ARN 已收窄（ADR 0033）——回归护栏：防将来改回 * 或踩 account=aws 陷阱。      收窄依据 = AWS SAR re, _template(), test_artifacts_bucket_job_in_lifecycle(), test_artifacts_bucket_private(), test_ecs_stopped_eventbridge_rule(), test_events_table_has_stream(), test_events_table_seq_is_number_type() (+22 more)

### Community 20 - "serialize.py"
Cohesion: 0.17
Nodes (20): _argument_from_dict(), _argument_to_dict(), job_from_dict(), job_result_from_dict(), job_result_to_dict(), job_to_dict(), Job, Scenario (+12 more)

### Community 21 - "model.py"
Cohesion: 0.12
Nodes (15): 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, RunMeta, Status, RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。 为什么是 core…, ports 层（ADR 0016 六边形架构）：核心只依赖这些接口，具体 adapter 由组合根注入。 四个 port（关注点拆开，不揉成上帝…, CAS 抢占：仅当该 job 当前是 PENDING 才置 RUNNING，成功返回 True（机制四）。 多个 reconciler 实例并发抢同一… (+7 more)

### Community 22 - "test_backend_cloud.py"
Cohesion: 0.13
Nodes (27): _fake_schedule_factory(), _FakeS3, _FakeTable, _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。  **, 不起 worker 的假 schedule：走完 on_event/on_job_complete 实时落库路径（让 adapter 真被调）。, 假 DDB table 句柄：DynamoDBRunStore 吃它（put_item/update_item/get_item/load/meta.clien (+19 more)

### Community 23 - "DdbEventLog"
Cohesion: 0.17
Nodes (18): DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, events_table(), _job(), _meta(), _passed_worker_events(), cloud 无状态跑批 core 侧测试（ADR 0034 P4a）：DdbEventLog + CloudLauncher + reconcile.tick( (+10 more)

### Community 24 - "RunPersistence"
Cohesion: 0.17
Nodes (21): LocalResultStore, Path, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。  数据面（追加为主）：一次 run 的每个 Jo, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, RunPersistence, _jr() (+13 more)

### Community 25 - "ADR 0016 执行架构：核心库窄腰 + Run 数据模型"
Cohesion: 0.20
Nodes (21): cli/README 组合根说明, CONTEXT.md 领域术语表, ADR 0005 单一共享 .feature, ADR 0006 形态 A 两子工程并列, ADR 0013 跨引擎共享边界, ADR 0014 AI 断言为主 + 投票治抖动, ADR 0015 v1.0 定位柔性冒烟, ADR 0016 执行架构：核心库窄腰 + Run 数据模型 (+13 more)

### Community 26 - "_engine"
Cohesion: 0.17
Nodes (19): _engine(), _job(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。, RunTask 容量不足/子网无 IP 等 → HTTP 200 + 空 tasks + failures。须翻成带 reason 的明确异常，非 IndexE, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env(), test_handle_stop_calls_stop_task() (+11 more)

### Community 27 - "run-scope.ts"
Cohesion: 0.09
Nodes (30): ADR-0014, ADR-0019, ADR-0020, ADR-0022, ADR-0026, ADR-0027, ADR-0031, ADR-0032 (+22 more)

### Community 28 - "ArtifactUploader（from_env/to_report_ref/flush）"
Cohesion: 0.22
Nodes (9): act 边界抢传（snapshot / step_done 安全点）, ArtifactUploader（from_env/to_report_ref/flush）, 删本地（上传成功确认后整目录删）, 固有残余（session_summary/log/traces 不救）, S3 key 镜像本地 run 树, 上传必须套超时（退出时间有界）, grace / stopTimeout 预算（真容器标定）, 容器盘停即销毁的中断产物丢失 (+1 more)

### Community 29 - "test_conditional_writes.py"
Cohesion: 0.14
Nodes (28): _initial(), _meta(), RunMeta, RunState, RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。 (+20 more)

### Community 30 - "Engine"
Cohesion: 0.16
Nodes (11): Engine, EngineResolver, Event, Job, 一个在跑的 worker 的句柄（schedule 持有，用于 stop）。 不暴露进程/信号细节——「怎么停」的机制（SIGTERM→宽限→SIGKILL…, 请求优雅停止：adapter 内部翻成具体机制；worker 收到后停会话、退出（ADR 0024 终止契约）。, 执行引擎 port（ADR 0016）。 schedule 经此起 worker；adapter 形状一致（spawn node / spawn python…, 起一个 worker 跑这个 job，返回 (句柄, ADR 0024 事件流迭代器)。 事件流逐条产出（ADR 0024 流式）；迭代结束 = worker… (+3 more)

### Community 31 - "BackendStack"
Cohesion: 0.15
Nodes (10): Cluster, Construct, BackendStack, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED…, 把 Lambda 代码打包到一个目录，返回其路径（Code.from_asset 用）。 内容 = lambdas/*.py（handler）+…, worker 安全组 id——_ssm_network 建的 sg。存引用供 reconciler Lambda 起 task 用同一 sg。, container stopTimeout（秒）：`-c stop_timeout=N` 覆盖，默认 120s。 grace… (+2 more)

### Community 32 - "scope.py"
Cohesion: 0.23
Nodes (12): PlanError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope… (+4 more)

### Community 33 - "FargateEngine"
Cohesion: 0.15
Nodes (13): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+5 more)

### Community 34 - "WorkerNetworkError"
Cohesion: 0.08
Nodes (21): worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 subprocess_engine…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), FakeWorkerHandle, Event, Job, 内存假 Engine（测试夹具，ADR 0026「接口是测试面」）。  直接在进程内吐预设的 ADR 0024 事件流，不 spawn 子进程、不连 Agent (+13 more)

### Community 35 - "S3StepArgumentOffloader"
Cohesion: 0.18
Nodes (9): _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3 指, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id, scenario_i, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。          按「哪个 _r, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。 (+1 more)

### Community 36 - "RunPersistence 应用服务"
Cohesion: 0.14
Nodes (15): commit-point 写序（数据面先、控制面后）, DDB 单表 META/STATE 两 item, on_job_complete / on_event 回调（JobSink）, Store.preflight() 探活 + 退出码分层, ResultStore（判定真值、S3 后端）, RunPersistence 应用服务, RunState.jobs 改 Map<scope_id>, RunStore（create_run/update_job_state/finalize_run） (+7 more)

### Community 37 - "run_reconcile_loop"
Cohesion: 0.12
Nodes (21): EngineResolver, Job, RunMeta, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。 now_iso_fn：注入时间源（组合根传…, run_reconcile_loop(), SubprocessLauncher (+13 more)

### Community 38 - "compose.py"
Cohesion: 0.06
Nodes (37): container_name(), engine_min_grace(), _make_lambda_client(), _make_ssm_client(), 组合根：把抽象的 core 接线到具体的引擎子进程（ADR 0016）。 core 只认 `EngineResolver`（按 engine 名给一个…, boto3 ssm client（读 subnet/sg 的确定性路径参数）。, boto3 lambda client（cloud status --wait 接力 invoke kicker Lambda 做 kickoff，ADR…, 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值… (+29 more)

### Community 40 - "ADR 0025: plan 模块（feature → jobs）"
Cohesion: 0.15
Nodes (15): ADR 0014: Assertion Votes Semantics, ADR 0019: Feature Tags — scope and engine, 同 scope 多 engine 值即报错, @engine:<midscene|novaact> 引擎选择 tag (G2), @scope:<name> 会话作用域 tag (G1), 两套 runner 各自消费 tag（cucumber --tags / pytest-bdd conftest marker）, ADR 0025: plan 模块（feature → jobs）, gherkin-official 41.0.0 (Parser, Compiler) (+7 more)

### Community 41 - "JobSource"
Cohesion: 0.17
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0024

### Community 42 - "代码健康度复盘任务说明"
Cohesion: 0.16
Nodes (17): CLAUDE.md — 项目约定, AWS 资源视为免费（限开发期）, 代码纪律, 沟通约定（中文讨论 / graphify 用英文）, graphify 知识图谱使用约定, 绿 ≠ 对：证据边界, 接口诚实优先于改动规模, 读者比例决定优化方向 (+9 more)

### Community 43 - "render.py"
Cohesion: 0.15
Nodes (16): _arg_hint(), _cost_bits(), format_event(), _ms(), plan_to_dict(), Event, Job, 渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。  core 产出纯数据（RunResult、 (+8 more)

### Community 44 - "test_lambda_handlers.py"
Cohesion: 0.07
Nodes (34): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler _run_ids_from_st, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug：     原启动器只认, Stream records + 直接 run_id 并存时都提取（健壮）。, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode（宽限态）→ None（机制二保守）。, 非本框架起的 task（env 无 RUN_ID/SCOPE_ID）→ (None, None, ...)，handler 会跳过。 (+26 more)

### Community 45 - "project.py"
Cohesion: 0.15
Nodes (20): _aggregate(), _job_status(), _lifecycle_rank(), Event, Job, JobResult, Status, 纯归约投影（ADR 0034）：events → JobResult/RunState，无 I/O、无执行编排、不 import boto3。… (+12 more)

### Community 46 - "Scenario"
Cohesion: 0.11
Nodes (30): 读回 definition（从 META item 的 meta_json）；不存在返回 None。, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。, 一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。, Scenario, Step, StepArgument, run_meta_from_dict() (+22 more)

### Community 47 - "run-scope.test.ts"
Cohesion: 0.12
Nodes (9): _events, fakePage, importMod(), testSink, ADR-0014, ADR-0024, ADR-0028, ADR-0029 (+1 more)

### Community 48 - "core/model.py 领域模型"
Cohesion: 0.13
Nodes (14): LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR…, core/model.py 领域模型, core/parse.py feature 解析, core/serialize.py 序列化真理源, DynamoDBRunStore 对拍测试（ADR 0030 决定六）：与 LocalRunStore 同一批行为断言，moto mock、不烧真 AWS。…, detached 组合根的 create_run 在 STATE item 落 detached=true 标记;默认(同步 run)不落（ADR 0034…, test_detached_flag_on_state_item(), test_realtime_write_lifecycle() (+6 more)

### Community 49 - "conftest.py"
Cohesion: 0.11
Nodes (17): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), 云端 adapter 测试基建（ADR 0030 决定六）。  **两类测试、两套 fixture**（见 tests/README.md）： - **单测（默, 配好的 S3StepArgumentOffloader（注入 aws fixture 建好的桶），供 StepArgument offload 测试。 (+9 more)

### Community 50 - "test_plan.py"
Cohesion: 0.15
Nodes (27): FeatureSource, plan(), PlanConfig, Job, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 严格契约：`features` 的 uri 必须互异（uri…, _plan(), plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。 (+19 more)

### Community 51 - "JobResult"
Cohesion: 0.14
Nodes (8): 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, JobSink, 数据面：每 job(=scope) 判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。 local adapter =…, ResultStore

### Community 52 - "names.py"
Cohesion: 0.12
Nodes (13): container_name(), default_name(), 资源命名（ADR 0033 两层命名）——**必须与 cli `compose.py` 的命名规则逐字一致**。  单一事实源风险点（ADR 0033 护栏）：, prefix + 基名（原样拼）。对齐 cli `compose.default_name`。, task-def family 名 `{prefix}{engine}-worker`（带 prefix）。对齐 cli `compose.task_def_n, task-def 内 container 元素名 `{engine}-worker`（**不带 prefix**，ADR 0033 硬契约）。      cli, subnet ID 列表的 SSM 路径（含 prefix）。对齐 cli `compose.ssm_path(prefix, "subnets")`。, sg ID 列表的 SSM 路径（含 prefix）。对齐 cli `compose.ssm_path(prefix, "security-groups")`。 (+5 more)

### Community 53 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 54 - "_FakeEcs"
Cohesion: 0.14
Nodes (8): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe 次数驱动，测, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, test_run_scope_puts_job_to_s3()

### Community 56 - "deterministic.ts"
Cohesion: 0.21
Nodes (12): ADR-0015, _clear(), deterministic(), DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, Entry (+4 more)

### Community 57 - "ReportStore.write（整 run 一次写）"
Cohesion: 0.25
Nodes (9): href 相对化（local 相对 / cloud 恒等 ref）, LocalReportStore, manifest.json（薄信封 + report_index）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写）, ResourceUri（带 scheme 的统一指针）, run_id（组合根生成、归集主键）, RunReport（归集索引，不融合内容） (+1 more)

### Community 58 - "ArtifactUploader"
Cohesion: 0.13
Nodes (9): ArtifactUploader, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0033, mkLogDir(), tmproot() (+1 more)

### Community 59 - "文档纪律（ADR / CONTEXT）"
Cohesion: 0.60
Nodes (6): ADR Status 头约定, 文档纪律（ADR / CONTEXT）, docs/journey/ 是 staging 区, 引用方向单向：Journey→ADR, 指针只指稳定物，不指会话上下文, 问题分类 STALE_INEFFICIENT（过时/低效）

### Community 60 - "S3ResultStore"
Cohesion: 0.17
Nodes (8): S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。  数据面判定真值——每个 j, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍 LocalResult, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。          **必须翻页**：list_objects_v2 单页硬上限, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, test_prefix_isolates_runs()

### Community 61 - "run_scope.py"
Cohesion: 0.16
Nodes (19): ArtifactUploader, engines/novaact README, _aggregate(), _attach_traj_refs(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _get_uploader(), log() (+11 more)

### Community 62 - "e2e_harness 使用说明"
Cohesion: 0.18
Nodes (13): ADR 0014 AI 断言投票, ADR 0024 worker↔core 协议 / 终止契约, ADR 0025 @scope: tag 分组, ADR 0029 产物→S3 / 边界抢传 / 固有残余, ADR 0032 Fargate 中断丢失量级 + 真容器 grace 校准, e2e_harness 使用说明, 边界抢传（act / scenario 边界）, grace 测量与 SIGKILL 兜底 (+5 more)

### Community 63 - "ADR 0018: 通用 step 能力清单"
Cohesion: 0.15
Nodes (13): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）, 双引擎真实价值 = 可选择/不锁定（交叉验证降级）, ADR 0020: Step 措辞——默认 AI + 确定性锚点脚手架 (+5 more)

### Community 64 - "build_push_workers.py"
Cohesion: 0.20
Nodes (13): 2 镜像（Nova / Midscene 各一）, _account_id(), build_push(), _ecr_login(), main(), Path, ECR repo 名 = {prefix}{engine}-worker（对齐 names.task_def_name，见 docstring）。, 跑一条命令；dry-run 只打印。失败即抛（subprocess.run check=True）——不吞错、让调用者见真况。 (+5 more)

### Community 65 - "build_cloud_stores"
Cohesion: 0.20
Nodes (12): build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_ecs_client(), _make_s3_client(), _normalize_prefix(), S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走… (+4 more)

### Community 66 - "_FakeDdbClient"
Cohesion: 0.23
Nodes (6): _FakeDdbClient, _FakeEcsClient, _FakeS3Client, test_preflight_all_present_returns_none(), test_preflight_missing_cluster_detected(), test_preflight_missing_events_table_names_prefix()

### Community 67 - "require_boto3"
Cohesion: 0.17
Nodes (6): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。  所有云端 adapter（存储侧 DynamoD, 缺 boto3 时抛带组件名的友好 ImportError（`pip install core[aws]`）；模块 import 不崩、构造时才检。, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。         prefix：可选 key, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…

### Community 68 - "workflow_setup.py"
Cohesion: 0.20
Nodes (7): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（worker/run_scope.py）与 spike…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。  @workflow, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。      region=None（不, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。  对标 midscene/spikes/05-negati, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。  用例（与 Midscene 同）：打开 wik

### Community 70 - "Job"
Cohesion: 0.09
Nodes (23): render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。, _sample_run(), test_format_event_omits_scope_id(), test_render_text_annotates_shortcircuited_step(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_no_annotation_on_plain_failed(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar() (+15 more)

### Community 71 - "deterministic.py"
Cohesion: 0.20
Nodes (9): deterministic(), DeterministicConflict, _Entry, match(), 确定性 step 注册表（ADR 0022）——Nova 引擎。  test engineer 用 `@deterministic(pattern)` 把「正则, 装饰器：把 handler 按正则 pattern 登记进注册表。      用法（与脚手架 deterministic_steps.py 的真实锚点一致）：, 一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。, 在注册表里找命中 text 的唯一 handler。      返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 → (+1 more)

### Community 72 - "_run_step"
Cohesion: 0.17
Nodes (11): _collect_traj(), _cost_from_result(), _DeterministicCtx, 报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。, 从 act/act_get 结果的 metadata 收集本次 act 的 trajectory **HTML** 路径（ADR 0027）。 Nova 每次…, 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+3 more)

### Community 73 - "_is_transient_network(e, *, connecting=False) (Python whitelist)"
Cohesion: 0.20
Nodes (10): Hand-written exponential backoff with _stop.wait, botocore transient/throttled error code tables (inlined), _is_transient_network(e, *, connecting=False) (Python whitelist), isTransientNetwork (Node/Midscene whitelist), network_error ErrorType Classification, Retry Domain Boundary = before scope_started emit, Known debt: engine SSL classification asymmetry, Step-level short-circuit within scope (step_skipped) (+2 more)

### Community 74 - "test_event_sink.py"
Cohesion: 0.17
Nodes (3): EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud()

### Community 75 - "ecs_task_timing.py"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 76 - "load_feature"
Cohesion: 0.33
Nodes (6): load_feature(), Path, 定位仓库根（含 core/ 与 engines/ 的目录）。 从本文件位置上溯：cli/cli/compose.py → cli/ →…, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导稳定…, repo_root(), FeatureSource

### Community 77 - "JobState"
Cohesion: 0.14
Nodes (10): _mk_state(), JobState, 单个 job 的控制面运行态（执行后才有）。, 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), Event, run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。 满足 ADR…, 事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收… (+2 more)

### Community 78 - "RunState"
Cohesion: 0.13
Nodes (27): 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…, RunState, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale…, _ddb_store(), _is_ddb_too_large(), _offloader(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。  *, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。 (+19 more)

### Community 79 - "_read_events"
Cohesion: 0.16
Nodes (10): _pump_log(), Event, Job, Popen, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的… (+2 more)

### Community 80 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal(), test_worker_runs_until_signaled() (+1 more)

### Community 82 - "ADR 0003 Qwen3-VL on Bedrock 做 grounding"
Cohesion: 0.36
Nodes (8): ADR 0002 不用 Bedrock GPT-5.5, ADR 0003 Qwen3-VL on Bedrock 做 grounding, ADR 0004 Nova Act 纯 IAM 经 Workflow 鉴权, ADR 0008 Midscene SigV4 自签鉴权, ADR 0009 最大化使用 AWS 硬约束, ADR 0012 planning 复用 Qwen3-VL, 文档健康度复盘任务, SIGV4-FETCH-RECIPE 配方笔记

### Community 83 - "schedule._Worker._run_once"
Cohesion: 0.29
Nodes (8): EX_WORKER_NETWORK = 80 exit code, schedule._heartbeat_wrap (silent-worker timeout fix), ScheduleOpts (network_retry, retry_sleep), schedule._Worker.run (network retry loop), schedule._Worker._run_once, Session leak protection before exit, subprocess_engine._read_events, core.errors.WorkerNetworkError

### Community 84 - "_instruction"
Cohesion: 0.25
Nodes (8): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote()

### Community 86 - "SqliteEventLog"
Cohesion: 0.11
Nodes (15): Connection, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, Path, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。  worker 事件（原始 ADR 0024 JSON 行 + wor, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。 (+7 more)

### Community 87 - "e2e_harness.py"
Cohesion: 0.53
Nodes (5): Path, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 88 - "argument.ts"
Cohesion: 0.50
Nodes (6): ADR-0024, argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 89 - "_is_transient_network"
Cohesion: 0.38
Nodes (7): BaseException, _classify_act_error(), _is_transient_client_error(), _is_transient_network(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…

### Community 90 - "step 级短路：step_skipped + shortcircuited 布尔"
Cohesion: 0.13
Nodes (15): index.html（判定明细树 + 产物导航）, 注入驱动的 S3 落点（ARTIFACT_S3_BUCKET/PREFIX）, 退出码基于 run 级 severity, severity 数值序 + _NON_VERDICT 过滤, step 级短路：step_skipped + shortcircuited 布尔, Status.PENDING / RUNNING（前置态）, Status.SKIPPED / ABORTED（core 派生态）, build_fargate_engines（组合根接 FargateEngine） (+7 more)

### Community 91 - "test_sqlite_event_log.py"
Cohesion: 0.23
Nodes (12): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。  存原始 JSON 行→读回解析成 Event、, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, 端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。, test_append_and_read_back_events(), test_append_idempotent_same_seq() (+4 more)

### Community 93 - "reconcile.py"
Cohesion: 0.18
Nodes (11): Action, plan_next(), project_full(), RunMeta, RunResult, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与…, reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→… (+3 more)

### Community 94 - "ADR 0017: Cloud Execution — Fargate over Runtime"
Cohesion: 0.33
Nodes (6): ADR 0017: Cloud Execution — Fargate over Runtime, AgentCore Evaluations（LLM-as-Judge，被否）, AgentCore Runtime（长驻 agent 服务）, 批处理 workload shape（run-to-exit）, ECS RunTask / Fargate 执行后端, 15 分钟 idle-kill 计时器与保活 plumbing

### Community 95 - "reconciler.py"
Cohesion: 0.19
Nodes (14): _build(), handler(), kicker_handler(), _now_iso(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 提取 kicker 要 tick 的 run_id 集。两种 event 源（kicker 同时服务两者）： ① runs 表…, 对每个 run tick 一步；done 则聚合收尾。reconciler（events Stream）与 kicker（runs Stream）共用。, events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及 run… (+6 more)

### Community 96 - "权威信息源 REFERENCES"
Cohesion: 0.40
Nodes (5): CONTEXT.md 事实现状, 权威信息源 REFERENCES, AWS Bedrock / AgentCore 文档, Midscene 官方文档与源码 ground truth, Nova Act SDK 与 AgentCore provider

### Community 97 - "echo_worker.py"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。  不接任何真引擎——只验证子进程 adapter

### Community 99 - "core/tests/test_subprocess_engine.py"
Cohesion: 0.34
Nodes (15): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。  用 tests/fixtures/echo_worker.py 当真子进程 sp, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried(), test_adapter_network_exit_maps_to_network_error() (+7 more)

### Community 100 - "ADR 0007 程序化登录 / HITL 逃生舱"
Cohesion: 0.67
Nodes (4): ADR 0001 范围限英文 UI, ADR 0007 程序化登录 / HITL 逃生舱, ADR 0010 双引擎苹果对苹果对标, ADR 0011 AgentCore 浏览器默认 vs 自建

### Community 101 - "deterministic"
Cohesion: 0.50
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— 给 TEST ENGINEER（会写代码的角色），不是 QA。 用途：少数"必须精确、不容 AI…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（test engineer 约定的带关键词措辞，与 QA…, url_matches()

### Community 102 - "Midscene SigV4 自签 fetch 配方"
Cohesion: 0.50
Nodes (4): engines/midscene README, Midscene SigV4 自签 fetch 配方, createOpenAIClient 隔离 ModelConfigManager 坑, sigv4Fetch（最小手建请求签名）

### Community 104 - "ADR 0034: 无状态跑批（CQRS + reconciler）"
Cohesion: 0.19
Nodes (20): cli README（执行入口皮）, adapters/cloud_launcher.py, adapters/event_log/ddb.py, adapters/event_log/sqlite.py, core/project.py 纯归约投影, core 执行核心库 README, core/reconcile.py 推进编排, core/schedule.py 并发调度 (+12 more)

### Community 105 - "_put_event"
Cohesion: 0.21
Nodes (12): _put_event(), 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, worker 发完 scope_done 又非 0 退出（会话释放失败，Midscene cleanupFailed→exit 1）：     scope_do, scope_done 后 exit 80（网络专用码，ADR 0028）→ 翻 WorkerNetworkError（与 subprocess/STOPPED, 假 ecs：describe_tasks 恒返回 STOPPED + 给定 exitCode——scope_done 路径读退出码用。      **必须换假, _stopped_ecs(), test_read_events_incremental_across_polls(), test_read_events_midscene_lowlevel_marshalling_and_ascending_read() (+4 more)

### Community 106 - "_job_def"
Cohesion: 0.27
Nodes (8): S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto mock、不烧真, test_load_all_paginated_preserves_failed_verdict(), test_load_all_paginates_beyond_1000(), test_load_all_stable_order(), test_save_load_round_trip(), test_scope_id_with_slash_not_subprefix(), _job_def(), Job

### Community 126 - "test_fargate_engine.py"
Cohesion: 0.32
Nodes (11): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。  **证据边界分流（CLAUDE.md「绿, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code(), test_probe_task_not_stopped() (+3 more)

### Community 127 - "build_local_reconcile"
Cohesion: 0.14
Nodes (13): build_engines(), make_resolver(), 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 两个引擎"spawn 子进程 + 讲同一套 ADR…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, build_local_reconcile(), _paths(), local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-… (+5 more)

### Community 128 - "EventSink"
Cohesion: 0.22
Nodes (6): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。 fd…, test_emit_flushes_each_event(), TextIO

### Community 129 - "CloudLauncher"
Cohesion: 0.29
Nodes (5): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。, test_cloud_launcher_calls_start_scope()

### Community 130 - "EventSink"
Cohesion: 0.18
Nodes (5): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0033

### Community 131 - "events_pk"
Cohesion: 0.29
Nodes (6): 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。, _put_worker_event(), 模拟 worker PutItem 一条执行事件（含 expires_at=emit_ts+7d，DdbEventLog 据此还原 emit_ts）。, test_events_pk_composite_run_id_scope_id()

### Community 136 - "test_read_events_scope_done_waits_for_stopped_before_reading_exit"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), **option-c 定义行为的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR 0032 结论 2），_await_e, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。, test_read_events_scope_done_waits_for_stopped_before_reading_exit()

## Ambiguous Edges - Review These
- `e2e_harness.py` → `分片深读（按模块耦合分组）`  [AMBIGUOUS]
  docs/code-health-review.md · relation: conceptually_related_to

## Knowledge Gaps
- **137 isolated node(s):** `ADR-0029`, `ADR-0016`, `ADR-0024`, `ADR-0033`, `ADR-0028` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `e2e_harness.py` and `分片深读（按模块耦合分组）`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ADR 0029: engine artifact→S3（worker 上传）` connect `ADR 0034: 无状态跑批（CQRS + reconciler）` to `run-scope.ts`, `ArtifactUploader（from_env/to_report_ref/flush）`, `run_scope.py`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `ADR 0030: 实时写存储接缝` connect `ADR 0034: 无状态跑批（CQRS + reconciler）` to `RunPersistence 应用服务`, `compose.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `ADR 0033: iac_aws_backend + 组合根接线` connect `ADR 0034: 无状态跑批（CQRS + reconciler）` to `build_push_workers.py`, `step 级短路：step_skipped + shortcircuited 布尔`, `RunPersistence 应用服务`, `Midscene SigV4 自签 fetch 配方`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `schedule()` (e.g. with `.on_job_complete()` and `ValueError`) actually correct?**
  _`schedule()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Job` (e.g. with `_job()` and `_sample_run()`) actually correct?**
  _`Job` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `CollectSink` (e.g. with `WorkerNetworkError` and `Job`) actually correct?**
  _`CollectSink` has 52 INFERRED edges - model-reasoned connections that need verification._