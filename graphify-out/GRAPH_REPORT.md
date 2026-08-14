# Graph Report - yaozhou  (2026-08-14)

## Corpus Check
- 178 files · ~128,807 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2360 nodes · 5578 edges · 142 communities (113 shown, 29 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 471 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `32e3e6b2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_schedule.py
- _Worker
- test_detached_launcher.py
- test_run_step.py
- test_plan.py
- test_stack.py
- test_project.py
- require_boto3
- test_cloud_integration.py
- Job
- test_stores.py
- test_cloud_reconcile.py
- test_transient_network.py
- test_lambda_handlers.py
- devDependencies
- test_interrupt_model.py
- __main__.py
- test_conditional_writes.py
- main
- ArtifactUploader
- test_reconcile.py
- agentcore-sigv4.mts
- compose.py
- test_backend_cloud.py
- test_report_store.py
- _engine
- job_result_from_dict
- test_tunnel.py
- subprocess_engine.py
- RunPersistence
- DynamoDBRunStore
- test_wire.py
- CloudLauncher
- reconciler.py
- test_fargate_engine.py
- ADR 0034 — Detached Batch Reconciler
- FargateEngine
- run-scope.ts
- _FakeEcsClient
- run_scope.py
- build_engines
- test_compose.py
- 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器
- JobResult
- ArtifactUploader
- ADR 0031 job 生命周期态 skipped/aborted + severity 数值序
- RunState
- exit_observer.py
- deterministic.ts
- run-scope.test.ts
- events_wallclock.py
- test_lifecycle_states.py
- ADR 0024 核心↔worker 协议
- JobSource
- {prefix}cluster + Fargate task definitions
- report_store/local.py
- deterministic.py
- test_tunnel_cli.py
- e2e_harness 使用说明
- _FakeEcs
- RunResult
- ensure_workflow_definition
- build_push_workers.py
- _mk_state
- RunMeta
- test_event_sink.py
- test_argument.py
- scope.py
- ADR 0018: 通用 step 能力清单
- test_s3_report_store.py
- conftest.py
- event-sink.mts
- ReportStore.write（整 run 一次写）
- test_subprocess_engine.py
- _spawn_and_wait_ready
- resolve_network
- ecs_task_timing.py
- RunPersistence 应用服务
- JobSource
- render.py
- test_job_source.py
- ADR 0003 Qwen3-VL on Bedrock 做 grounding
- schedule._Worker._run_once
- ArtifactUploader（from_env/to_report_ref/flush）
- argument.ts
- _instruction
- ssm_path
- serialize.py
- ADR 0022 BDD runner 退役 + 薄 worker
- S3ResultStore
- ADR 0017: Cloud Execution — Fargate over Runtime
- _FakeS3
- _FakeResult
- echo_worker.py
- test_cloud_infra.py
- artifact-upload.test.ts
- EventBridgeTimeoutWatch
- 权威信息源 REFERENCES
- Midscene SigV4 自签 fetch 配方
- event-sink.test.ts
- gherkai
- iac_aws_backend README
- 02-agentcore-cdp.ts
- job-source.test.ts
- interrupt_worker.py
- _FakeSink
- gherkai/names.py
- adapters/__init__.py
- EventLog
- agentcore-sigv4.test.ts
- core/__init__.py
- DynamoDB stream event source mappings
- _reconcile_lambdas (stack wiring)
- _SeqEcs
- StepDone
- 开放性动作导致页面瞬态 flaky
- session_id lineage on scope_started
- ADR 0030 实时落库接缝
- test_deterministic.py
- _run_step
- iac_aws_backend CDK 工程
- prefix contract
- {prefix}artifacts S3 bucket
- novaact
- wikipedia SSL 环境坑
- _TrajNova
- deterministic
- _is_transient_network
- _prune_empty_dirs
- load_feature
- ValueError
- .on_event
- .preflight
- handler
- finalize_artifacts
- Event
- Scenario
- Step
- StepArgument
- Exception
- StepArgument

## God Nodes (most connected - your core abstractions)
1. `Job` - 112 edges
2. `RunMeta` - 101 edges
3. `RunState` - 93 edges
4. `Status` - 85 edges
5. `JobState` - 75 edges
6. `JobResult` - 72 edges
7. `schedule()` - 63 edges
8. `CollectSink` - 60 edges
9. `Step` - 58 edges
10. `Scenario` - 58 edges

## Surprising Connections (you probably didn't know these)
- `通用 step（QA 零代码的唯一载体）` --conceptually_related_to--> `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md → docs/adr/0019-feature-tags-scope-and-engine.md
- `_load_and_plan()` --calls--> `plan()`  [INFERRED]
  cli/cli/__main__.py → core/core/scope.py
- `_load_and_plan()` --calls--> `PlanConfig`  [INFERRED]
  cli/cli/__main__.py → core/core/scope.py
- `_cmd_submit()` --calls--> `stop_tunnel()`  [INFERRED]
  cli/cli/__main__.py → gherkai/gherkai/tunnel.py
- `_submit_local()` --calls--> `write_tunnel_file()`  [INFERRED]
  cli/cli/__main__.py → gherkai/gherkai/detached.py

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

## Communities (142 total, 29 thin omitted)

### Community 0 - "test_schedule.py"
Cohesion: 0.20
Nodes (54): 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+46 more)

### Community 1 - "_Worker"
Cohesion: 0.19
Nodes (9): _heartbeat_wrap(), Event, Job, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…, _Worker (+1 more)

### Community 2 - "test_detached_launcher.py"
Cohesion: 0.08
Nodes (36): EngineResolver, build_local_reconcile(), _parse_iso(), _paths(), Job, 无状态跑批的 cli 侧接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。 now_iso_fn：注入时间源（组合根传…, 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的… (+28 more)

### Community 3 - "test_run_step.py"
Cohesion: 0.22
Nodes (16): _done(), _FakeNova, _run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。 与 Midscene 引擎 run-scope.test.ts…, 注入 fake：act_get 按布尔序列逐票回；act/go_to_url 记调用。act 可设异常模拟中途失败。 tw_seq：每票…, _step(), test_act_transient_network_is_network_error(), test_deterministic_and_url_steps_have_no_traj_refs(), test_given_url_goes_to_nav_no_ai() (+8 more)

### Community 4 - "test_plan.py"
Cohesion: 0.09
Nodes (41): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 严格契约：`features` 的 uri 必须互异（uri…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, _plan(), plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。 (+33 more)

### Community 5 - "test_stack.py"
Cohesion: 0.06
Nodes (42): Cluster, Construct, BackendStack, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED…, 把 Lambda 代码打包到一个目录，返回其路径（Code.from_asset 用）。 内容 = lambdas/*.py（handler）+…, worker 安全组 id——_ssm_network 建的 sg。存引用供 reconciler Lambda 起 task 用同一 sg。, container stopTimeout（秒）：`-c stop_timeout=N` 覆盖，默认 120s。 grace… (+34 more)

### Community 6 - "test_project.py"
Cohesion: 0.07
Nodes (63): _FakeTable, 假 DDB table 句柄：DynamoDBRunStore…, ScopeStarted, plan_next(), project(), project_full(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与… (+55 more)

### Community 7 - "require_boto3"
Cohesion: 0.08
Nodes (14): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install core[aws]`）；模块 import 不崩、构造时才检。, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,… (+6 more)

### Community 8 - "test_cloud_integration.py"
Cohesion: 0.15
Nodes (23): 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, S3StepArgumentOffloader, _ddb_store(), _is_ddb_too_large(), _offloader(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：DdbRunStore 挂 offloader，docString/dataTable 搬真 S3、META 只留指针、读回逐字节还原。, 真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。 (+15 more)

### Community 9 - "Job"
Cohesion: 0.10
Nodes (41): Job, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。, 一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。, 一个 job = 一个 scope = 一个会话边界 = schedule 交给单个 worker 的活（ADR 0016/0024/0025）。, Scenario, Step, StepArgument (+33 more)

### Community 10 - "test_stores.py"
Cohesion: 0.14
Nodes (29): 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), from_dict(), RunResult → 朴素 dict（机器可读：CI / WebUI / manifest 消费）。 normalize（ADR 0016…, 朴素 dict → RunResult。与 to_dict 往返一致（round-trip 单测护栏）。 def 唯一真值在…, to_dict(), test_realtime_write_lifecycle(), test_save_load_round_trip() (+21 more)

### Community 11 - "test_cloud_reconcile.py"
Cohesion: 0.06
Nodes (42): Connection, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。 (+34 more)

### Community 12 - "test_transient_network.py"
Cohesion: 0.07
Nodes (29): _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings(), test_presend_ignores_non_html(), test_presend_skips_when_no_sibling_json() (+21 more)

### Community 13 - "test_lambda_handlers.py"
Cohesion: 0.05
Nodes (46): _FakeEcs, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, Stream records + 直接 run_id 并存时都提取（健壮）。, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。 (+38 more)

### Community 14 - "devDependencies"
Cohesion: 0.05
Nodes (38): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-dynamodb, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, author (+30 more)

### Community 15 - "test_interrupt_model.py"
Cohesion: 0.07
Nodes (19): captured(), _FakeResult, _FakeSink, _Meta, fixture, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM…, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。 (+11 more)

### Community 16 - "__main__.py"
Cohesion: 0.11
Nodes (34): ArgumentParser, _build_parser(), _cmd_list_engines(), _cmd_plan(), _cmd_reconcile(), _cmd_run(), _cmd_status(), _cmd_submit() (+26 more)

### Community 17 - "test_conditional_writes.py"
Cohesion: 0.12
Nodes (30): _initial(), _meta(), RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+22 more)

### Community 18 - "main"
Cohesion: 0.15
Nodes (33): main(), _capturing_schedule(), _fake_schedule_factory(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS）， 验证落盘三层产物 + --json…, 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job…, 假 schedule：把传入 opts 存进 opts_box、按指定 status 合成 RunResult（验退出码/参数映射）。, 返回一个替换 compose.build_local_stores 的 fake：产出三个记录调用的 fake store + make_artifacts。 (+25 more)

### Community 19 - "ArtifactUploader"
Cohesion: 0.09
Nodes (22): ArtifactUploader, Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记… (+14 more)

### Community 20 - "test_reconcile.py"
Cohesion: 0.13
Nodes (26): 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher, _meta(), Job, reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。 用真… (+18 more)

### Community 21 - "agentcore-sigv4.mts"
Cohesion: 0.07
Nodes (27): ADR-0010, getBaseUrl(), getRegion(), MODEL, modelSigner_(), ADR-0033, signCdpUpgrade(), sigv4Fetch() (+19 more)

### Community 22 - "compose.py"
Cohesion: 0.10
Nodes (25): Engine, build_cloud_stores(), build_fargate_engines(), build_local_stores(), _make_ddb_table(), _make_ecs_client(), _make_lambda_client(), make_resolver() (+17 more)

### Community 23 - "test_backend_cloud.py"
Cohesion: 0.16
Nodes (31): _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 不起 worker 的假 schedule：走完 on_event/on_job_complete 实时落库路径（让 adapter 真被调）。, submit cloud 的 preflight 除表/桶/cluster 外还探：本 run 用到引擎的 task-def + 事件驱动链三 Lambda…, preflight 报资源缺（如链上 Lambda 不存在）→ 提交前退 2、不写任何东西。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等… (+23 more)

### Community 24 - "test_report_store.py"
Cohesion: 0.24
Nodes (27): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。 (+19 more)

### Community 25 - "_engine"
Cohesion: 0.14
Nodes (28): _engine(), _job(), _put_event(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。, worker 发完 scope_done 又非 0 退出（会话释放失败，Midscene cleanupFailed→exit 1）： scope_done…, **option-c 定义行为的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR 0032 结论… (+20 more)

### Community 26 - "job_result_from_dict"
Cohesion: 0.09
Nodes (19): ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, job_result_from_dict(), job_result_to_dict() (+11 more)

### Community 27 - "test_tunnel.py"
Cohesion: 0.08
Nodes (34): Exception, cleanup_tunnel(), 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。, _gen_auth(), make_tunnel(), map_origin_in_jobs(), NgrokTunnel, Job (+26 more)

### Community 28 - "subprocess_engine.py"
Cohesion: 0.13
Nodes (13): _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。 (+5 more)

### Community 29 - "RunPersistence"
Cohesion: 0.18
Nodes (22): LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run = commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, RunPersistence, _jr() (+14 more)

### Community 30 - "DynamoDBRunStore"
Cohesion: 0.11
Nodes (13): DynamoDBRunStore, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。, fixture, 两个 adapter 各来一遍（对拍）。local 用 tmp_path；ddb 用 moto aws fixture。 (+5 more)

### Community 31 - "test_wire.py"
Cohesion: 0.10
Nodes (30): _argument_to_json(), event_from_json(), event_from_line(), job_to_json(), job_to_line(), Event, Job, Scenario (+22 more)

### Community 32 - "CloudLauncher"
Cohesion: 0.11
Nodes (18): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。, job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…, 无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。 (+10 more)

### Community 33 - "reconciler.py"
Cohesion: 0.19
Nodes (16): datetime, _build(), _handle_timeout(), kicker_handler(), _now_iso(), _parse_iso(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING… (+8 more)

### Community 34 - "test_fargate_engine.py"
Cohesion: 0.16
Nodes (18): _delayed_stopped_ecs(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env(), test_final_drain_paginates_across_last_evaluated_key() (+10 more)

### Community 35 - "ADR 0034 — Detached Batch Reconciler"
Cohesion: 0.28
Nodes (17): CLAUDE.md 项目约定, cli README（最薄前端/组合根皮）, CONTEXT.md 领域术语表, 执行核心库窄腰（概念）, 通用 step（QA 零代码的唯一载体）, Run 数据模型 Run⊃Job(=Scope)⊃Scenario⊃Step, core README（执行核心库窄腰）, ADR 0016 执行架构：核心库窄腰 + Run 数据模型 + ports (+9 more)

### Community 36 - "FargateEngine"
Cohesion: 0.14
Nodes (14): FargateEngine, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR…, 轮询 DescribeTasks 直到拿到确定的 exitCode——scope_done 后读退出码用（ADR 0024「事件流结束信号」）。… (+6 more)

### Community 37 - "run-scope.ts"
Cohesion: 0.09
Nodes (31): ADR-0014, ADR-0019, ADR-0020, ADR-0022, ADR-0024, ADR-0026, ADR-0027, ADR-0028 (+23 more)

### Community 38 - "_FakeEcsClient"
Cohesion: 0.17
Nodes (12): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, test_preflight_all_present_returns_none(), test_preflight_missing_chain_lambda_names_prefix() (+4 more)

### Community 39 - "run_scope.py"
Cohesion: 0.16
Nodes (19): ArtifactUploader, engines/novaact README, _aggregate(), _attach_traj_refs(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _get_uploader(), log() (+11 more)

### Community 40 - "build_engines"
Cohesion: 0.22
Nodes (20): build_engines(), Path, 定位仓库根（含 core/ 与 engines/ 的目录）。 从本文件位置上溯：cli/cli/compose.py → cli/ →…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 两个引擎"spawn 子进程 + 讲同一套 ADR…, repo_root(), Path, extra_http_headers（ADR 0035 决策 4）→ 两 worker env 注…, test_build_engines_artifact_s3_alone_makes_env_nonnull() (+12 more)

### Community 41 - "test_compose.py"
Cohesion: 0.15
Nodes (15): engine_min_grace(), 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…, resolve_region(), compose（组合根逻辑）单测：不起任何子进程、不烧钱。, test_engine_min_grace_midscene_nonzero_covers_onsignal_budget(), test_engine_min_grace_mixed_run_takes_max(), test_engine_min_grace_nova_covers_act_timeout_plus_margin() (+7 more)

### Community 42 - "0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器"
Cohesion: 0.18
Nodes (10): 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器, 1. `TunnelProvider` 可插拔口子（gherkai 组合根层），首个实现 = ngrok, 2. URL 映射：feature 写原始地址，组装 job 时替换, 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态, 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）, 决策, 背景与问题, 被拒/被缓方案（护栏） (+2 more)

### Community 43 - "JobResult"
Cohesion: 0.15
Nodes (14): JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的…, S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…, test_load_all_paginated_preserves_failed_verdict(), test_load_all_paginates_beyond_1000(), test_load_all_stable_order(), test_prefix_isolates_runs() (+6 more)

### Community 44 - "ArtifactUploader"
Cohesion: 0.17
Nodes (6): ArtifactUploader, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0033

### Community 45 - "ADR 0031 job 生命周期态 skipped/aborted + severity 数值序"
Cohesion: 0.16
Nodes (16): 连锁失败读法（error → 后续 step 短路跳过）, 被拒方案：materialize 产物拷贝, ADR 0027: RunReport 跨引擎归集索引, ADR 0028: Transient Network/SSL Resilience, Hand-written exponential backoff with _stop.wait, botocore transient/throttled error code tables (inlined), _is_transient_network(e, *, connecting=False) (Python whitelist), isTransientNetwork (Node/Midscene whitelist) (+8 more)

### Community 46 - "RunState"
Cohesion: 0.08
Nodes (27): 一次性写完整态（= create_run 的两 item 一起 put；语义同 local save_run）。, RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐…, run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。 **写序…, _state_scalars(), RunStore adapters（ADR 0016）。当前只有 local；未来 ddb。, LocalRunStore, Path, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR… (+19 more)

### Community 47 - "exit_observer.py"
Cohesion: 0.32
Nodes (7): _event_log(), _extract(), handler(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。, EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。

### Community 48 - "deterministic.ts"
Cohesion: 0.16
Nodes (15): ADR-0015, _clear(), deterministic(), DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, Entry (+7 more)

### Community 49 - "run-scope.test.ts"
Cohesion: 0.12
Nodes (9): _events, fakePage, importMod(), testSink, ADR-0014, ADR-0024, ADR-0028, ADR-0029 (+1 more)

### Community 50 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 51 - "test_lifecycle_states.py"
Cohesion: 0.08
Nodes (24): 成本可观测（engine 只报原生量、core 不折美元）, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 subprocess_engine…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一… (+16 more)

### Community 52 - "ADR 0024 核心↔worker 协议"
Cohesion: 0.29
Nodes (8): ADR 0001 范围限英文 UI, ADR 0007 程序化登录 / HITL 逃生舱, ADR 0010 双引擎苹果对苹果对标, ADR 0011 AgentCore 浏览器默认 vs 自建, ADR 0014 AI 断言为主 + 投票治抖动, ADR 0015 v1.0 定位柔性冒烟, ADR 0024 核心↔worker 协议, ADR 0029 引擎产物上 S3

### Community 53 - "JobSource"
Cohesion: 0.20
Nodes (6): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…

### Community 54 - "{prefix}cluster + Fargate task definitions"
Cohesion: 0.50
Nodes (4): Worker ECR repositories, {prefix}cluster + Fargate task definitions, EventBridge rule {prefix}ecs-stopped, Per-engine task roles + shared execution role

### Community 55 - "report_store/local.py"
Cohesion: 0.10
Nodes (19): 报告产物模型 / RunReport 归集索引, ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。, collect_report_index(), _fmt_ms(), _local_path(), Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出… (+11 more)

### Community 56 - "deterministic.py"
Cohesion: 0.25
Nodes (7): DeterministicConflict, _Entry, match(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 test engineer 用 `@deterministic(pattern)`…, 一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…

### Community 57 - "test_tunnel_cli.py"
Cohesion: 0.13
Nodes (19): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 守护：轮询到 run 终态 → 拆隧道退出（ADR 0035 决策 3 cloud 档）。, run 永不终态（查询一直异常）→ TTL 到点拆隧道自杀（防 ngrok 进程泄漏）。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, run --expose-local：job 文本中 origin 前缀 → 凭据内嵌隧道 URL；skip 头进 RunMeta（ADR 0035 决策…, 不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。 (+11 more)

### Community 58 - "e2e_harness 使用说明"
Cohesion: 0.18
Nodes (13): ADR 0014 AI 断言投票, ADR 0024 worker↔core 协议 / 终止契约, ADR 0025 @scope: tag 分组, ADR 0029 产物→S3 / 边界抢传 / 固有残余, ADR 0032 Fargate 中断丢失量级 + 真容器 grace 校准, e2e_harness 使用说明, 边界抢传（act / scenario 边界）, grace 测量与 SIGKILL 兜底 (+5 more)

### Community 59 - "_FakeEcs"
Cohesion: 0.22
Nodes (5): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…

### Community 60 - "RunResult"
Cohesion: 0.16
Nodes (18): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 __main__（argparse 皮）+…, RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…, render_text(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。, _sample_run(), test_render_text_annotates_shortcircuited_step(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_no_annotation_on_plain_failed() (+10 more)

### Community 61 - "ensure_workflow_definition"
Cohesion: 0.21
Nodes (9): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（worker/run_scope.py）与 spike…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 region=None（不再硬编码…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开…, run() (+1 more)

### Community 62 - "build_push_workers.py"
Cohesion: 0.22
Nodes (12): _account_id(), build_push(), _ecr_login(), main(), Path, ECR repo 名 = {prefix}{engine}-worker（对齐 names.task_def_name，见 docstring）。, 跑一条命令；dry-run 只打印。失败即抛（subprocess.run check=True）——不吞错、让调用者见真况。, 取当前账户 id（拼 ECR registry host）。dry-run 时用占位符（不真调 AWS）。 (+4 more)

### Community 63 - "_mk_state"
Cohesion: 0.23
Nodes (12): _args(), _mk_state(), pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、failed/error→1，均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。, test_render_status_json_no_hint() (+4 more)

### Community 64 - "RunMeta"
Cohesion: 0.06
Nodes (45): Ports 层（Engine/RunStore/ResultStore/ReportStore）, _job_state_from_item(), _job_state_to_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。…, JobState → DDB Map entry（字段集同 serialize；session_id/claimed_at 用 omit-when-… (+37 more)

### Community 65 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 67 - "scope.py"
Cohesion: 0.13
Nodes (25): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, _index_ast_lines(), _map_argument(), parse_feature(), ParsedScenario, StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-… (+17 more)

### Community 68 - "ADR 0018: 通用 step 能力清单"
Cohesion: 0.18
Nodes (11): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）, ADR 0020: Step 措辞——默认 AI + 确定性锚点脚手架, 默认 AI 判断（裸 When/Then 无路由关键词） (+3 more)

### Community 69 - "test_s3_report_store.py"
Cohesion: 0.23
Nodes (14): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3() (+6 more)

### Community 70 - "conftest.py"
Cohesion: 0.12
Nodes (22): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), fixture, 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -… (+14 more)

### Community 71 - "event-sink.mts"
Cohesion: 0.22
Nodes (5): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0033

### Community 72 - "ReportStore.write（整 run 一次写）"
Cohesion: 0.22
Nodes (10): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, LocalReportStore, manifest.json（薄信封 + report_index）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写）, ResourceUri（带 scheme 的统一指针）, run_id（组合根生成、归集主键） (+2 more)

### Community 73 - "test_subprocess_engine.py"
Cohesion: 0.34
Nodes (15): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried(), test_adapter_network_exit_maps_to_network_error() (+7 more)

### Community 74 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal(), test_worker_runs_until_signaled() (+1 more)

### Community 75 - "resolve_network"
Cohesion: 0.20
Nodes (10): _make_ssm_client(), boto3 ssm client（读 subnet/sg 的确定性路径参数）。, 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, _read_ssm_list(), resolve_network(), test_resolve_network_empty_ssm_fails_fast(), test_resolve_network_explicit_overrides_skip_ssm() (+2 more)

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
Cohesion: 0.13
Nodes (16): cli/__main__.py（argparse 皮 + 退出码）, _arg_hint(), _cost_bits(), format_event(), _ms(), plan_to_dict(), Event, Job (+8 more)

### Community 80 - "test_job_source.py"
Cohesion: 0.22
Nodes (3): JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。, test_s3_uri_without_key_fails_loud()

### Community 81 - "ADR 0003 Qwen3-VL on Bedrock 做 grounding"
Cohesion: 0.36
Nodes (8): ADR 0002 不用 Bedrock GPT-5.5, ADR 0003 Qwen3-VL on Bedrock 做 grounding, ADR 0004 Nova Act 纯 IAM 经 Workflow 鉴权, ADR 0008 Midscene SigV4 自签鉴权, ADR 0009 最大化使用 AWS 硬约束, ADR 0012 planning 复用 Qwen3-VL, 文档健康度复盘任务, SIGV4-FETCH-RECIPE 配方笔记

### Community 82 - "schedule._Worker._run_once"
Cohesion: 0.29
Nodes (8): EX_WORKER_NETWORK = 80 exit code, schedule._heartbeat_wrap (silent-worker timeout fix), ScheduleOpts (network_retry, retry_sleep), schedule._Worker.run (network retry loop), schedule._Worker._run_once, Session leak protection before exit, subprocess_engine._read_events, core.errors.WorkerNetworkError

### Community 83 - "ArtifactUploader（from_env/to_report_ref/flush）"
Cohesion: 0.25
Nodes (8): act 边界抢传（snapshot / step_done 安全点）, ArtifactUploader（from_env/to_report_ref/flush）, 删本地（上传成功确认后整目录删）, ADR 0029: engine artifact→S3（worker 上传）, 注入驱动的 S3 落点（ARTIFACT_S3_BUCKET/PREFIX）, 固有残余（session_summary/log/traces 不救）, S3 key 镜像本地 run 树, 上传必须套超时（退出时间有界）

### Community 84 - "argument.ts"
Cohesion: 0.39
Nodes (7): argumentText(), buildInstruction(), cleanCell(), StepArgument, ADR-0024, ADR-0024, unquote()

### Community 85 - "_instruction"
Cohesion: 0.25
Nodes (8): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote()

### Community 86 - "ssm_path"
Cohesion: 0.29
Nodes (7): subnet/sg 的 SSM 参数路径（含 prefix，cli 已知 prefix 拼路径读，无循环——ADR 0033）。, ssm_path(), 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai.names`（真同源）**。 曾因「CDK…, subnet ID 列表的 SSM 路径（= gherkai.names.ssm_path(prefix, "subnets") 的便捷形式）。, sg ID 列表的 SSM 路径（= gherkai.names.ssm_path(prefix, "security-groups") 的便捷形式）。, ssm_security_groups_path(), ssm_subnets_path()

### Community 87 - "serialize.py"
Cohesion: 0.21
Nodes (11): 读回 definition（从 META item 的 meta_json）；不存在返回 None。, 读回 definition（RunMeta）；不存在返回 None。, _argument_from_dict(), _argument_to_dict(), job_from_dict(), core 领域模型 ↔ 朴素 dict（单一序列化真理源，ADR 0027/0016）。 序列化的是 core 的领域模型，故属 core——cli 的…, run_meta_from_dict(), _scenario_def_from_dict() (+3 more)

### Community 88 - "ADR 0022 BDD runner 退役 + 薄 worker"
Cohesion: 0.33
Nodes (7): ADR 0005 单一共享 .feature, ADR 0006 形态 A 两子工程并列, ADR 0013 跨引擎共享边界, ADR 0021 cucumber 本地补丁（已退役）, ADR 0022 BDD runner 退役 + 薄 worker, ADR 0023 Nova Act acting 锁 Python, features/ 共享 .feature 用例

### Community 89 - "S3ResultStore"
Cohesion: 0.17
Nodes (9): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, _s3_result_store() (+1 more)

### Community 90 - "ADR 0017: Cloud Execution — Fargate over Runtime"
Cohesion: 0.33
Nodes (6): ADR 0017: Cloud Execution — Fargate over Runtime, AgentCore Evaluations（LLM-as-Judge，被否）, AgentCore Runtime（长驻 agent 服务）, 批处理 workload shape（run-to-exit）, ECS RunTask / Fargate 执行后端, 15 分钟 idle-kill 计时器与保活 plumbing

### Community 92 - "_FakeResult"
Cohesion: 0.15
Nodes (6): _FakeResult, _Meta, _NavErrorNova, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, test_run_scenario_shortcircuits_after_error()

### Community 93 - "echo_worker.py"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 95 - "artifact-upload.test.ts"
Cohesion: 0.50
Nodes (3): mkLogDir(), tmproot(), ADR-0029

### Community 97 - "权威信息源 REFERENCES"
Cohesion: 0.50
Nodes (4): 权威信息源 REFERENCES, AWS Bedrock / AgentCore 文档, Midscene 官方文档与源码 ground truth, Nova Act SDK 与 AgentCore provider

### Community 98 - "Midscene SigV4 自签 fetch 配方"
Cohesion: 0.50
Nodes (4): engines/midscene README, Midscene SigV4 自签 fetch 配方, createOpenAIClient 隔离 ModelConfigManager 坑, sigv4Fetch（最小手建请求签名）

### Community 100 - "gherkai"
Cohesion: 0.67
Nodes (4): cli, core, gherkai, iac-aws-backend

### Community 101 - "iac_aws_backend README"
Cohesion: 0.50
Nodes (4): ADR 0016 — Composition Root Shared Layer, ADR 0024 — Synchronous Run Query Polling, iac_aws_backend README, VPC/subnets/security-groups + SSM parameters

### Community 105 - "_FakeSink"
Cohesion: 0.18
Nodes (5): captured(), _FakeSink, fixture, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 106 - "gherkai/names.py"
Cohesion: 0.18
Nodes (9): container_name(), default_name(), 资源命名真源（gherkai 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。 **零依赖**（不…, prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…, task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, task_def_name(), iac_aws_backend Stack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按… (+1 more)

### Community 108 - "EventLog"
Cohesion: 0.22
Nodes (6): EventLog, Launcher, Job, Protocol, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 local = 起 subprocess worker（事件旁路落 SQLite…

### Community 111 - "DynamoDB stream event source mappings"
Cohesion: 0.67
Nodes (3): DynamoDB stream event source mappings, {prefix}events DynamoDB table, {prefix}runs DynamoDB table

### Community 113 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 114 - "StepDone"
Cohesion: 0.08
Nodes (52): test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, Cost (+44 more)

### Community 119 - "test_deterministic.py"
Cohesion: 0.22
Nodes (3): _isolate(), fixture, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑：cd engines/novaact && .venv/bin/python…

### Community 120 - "_run_step"
Cohesion: 0.17
Nodes (11): _collect_traj(), _cost_from_result(), _DeterministicCtx, 报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。, 从 act/act_get 结果的 metadata 收集本次 act 的 trajectory **HTML** 路径（ADR 0027）。 Nova 每次…, 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+3 more)

### Community 126 - "_TrajNova"
Cohesion: 0.25
Nodes (5): 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。, test_step_done_carries_step_level_trajectory_refs(), test_then_votes_multiple_trajectories_on_one_step(), _TrajNova, _TrajResult

### Community 127 - "deterministic"
Cohesion: 0.33
Nodes (6): deterministic, deterministic(), 装饰器：把 handler 按正则 pattern 登记进注册表。 用法（与脚手架 deterministic_steps.py 的真实锚点一致）：…, 确定性锚点脚手架（ADR 0020/0022）—— 给 TEST ENGINEER（会写代码的角色），不是 QA。 用途：少数"必须精确、不容 AI…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（test engineer 约定的带关键词措辞，与 QA…, url_matches()

### Community 128 - "_is_transient_network"
Cohesion: 0.38
Nodes (7): _classify_act_error(), _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…

### Community 129 - "_prune_empty_dirs"
Cohesion: 0.40
Nodes (5): _prune_empty_dirs(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, test_prune_empty_dirs_keeps_nonempty(), test_prune_empty_dirs_noop_when_missing(), test_prune_empty_dirs_removes_empty_tree()

### Community 130 - "load_feature"
Cohesion: 0.40
Nodes (5): FeatureSource, load_feature(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导稳定…, test_load_feature_outside_repo_uses_absolute(), test_load_feature_uri_relative_to_repo()

### Community 131 - "ValueError"
Cohesion: 0.50
Nodes (4): test_act_non_network_is_engine_error(), test_classify_unknown_falls_back_engine_error(), test_value_error_not_transient(), ValueError

### Community 134 - "handler"
Cohesion: 0.50
Nodes (4): handler(), 从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch…, events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及 run…, _run_ids_from_stream()

## Ambiguous Edges - Review These
- `通用 step（QA 零代码的唯一载体）` → `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md · relation: conceptually_related_to

## Knowledge Gaps
- **168 isolated node(s):** `背景与问题`, `调研结论（内联，自包含）`, `1. `TunnelProvider` 可插拔口子（gherkai 组合根层），首个实现 = ngrok`, `2. URL 映射：feature 写原始地址，组装 job 时替换`, `3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态` (+163 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `通用 step（QA 零代码的唯一载体）` and `ADR 0019 用 Gherkin tag 声明 scope 与 engine`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Job` connect `Job` to `test_schedule.py`, `_Worker`, `test_detached_launcher.py`, `test_plan.py`, `test_project.py`, `test_cloud_integration.py`, `test_stores.py`, `test_cloud_reconcile.py`, `test_lambda_handlers.py`, `test_conditional_writes.py`, `test_reconcile.py`, `test_report_store.py`, `_engine`, `job_result_from_dict`, `test_tunnel.py`, `subprocess_engine.py`, `RunPersistence`, `DynamoDBRunStore`, `test_wire.py`, `CloudLauncher`, `test_fargate_engine.py`, `FargateEngine`, `JobResult`, `test_lifecycle_states.py`, `_FakeEcs`, `RunResult`, `RunMeta`, `scope.py`, `test_subprocess_engine.py`, `serialize.py`, `EventLog`, `_SeqEcs`, `StepDone`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `Status` connect `RunMeta` to `test_schedule.py`, `_Worker`, `test_detached_launcher.py`, `test_project.py`, `test_cloud_integration.py`, `Job`, `test_stores.py`, `test_cloud_reconcile.py`, `test_lambda_handlers.py`, `test_conditional_writes.py`, `test_reconcile.py`, `test_report_store.py`, `job_result_from_dict`, `RunPersistence`, `DynamoDBRunStore`, `test_wire.py`, `CloudLauncher`, `test_fargate_engine.py`, `JobResult`, `RunState`, `test_lifecycle_states.py`, `_FakeEcs`, `test_s3_report_store.py`, `test_subprocess_engine.py`, `serialize.py`, `_FakeS3`, `EventBridgeTimeoutWatch`, `_SeqEcs`, `StepDone`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `RunMeta` connect `RunMeta` to `test_schedule.py`, `_Worker`, `test_detached_launcher.py`, `test_project.py`, `test_cloud_integration.py`, `Job`, `test_stores.py`, `test_cloud_reconcile.py`, `test_lambda_handlers.py`, `__main__.py`, `test_conditional_writes.py`, `test_reconcile.py`, `test_report_store.py`, `RunPersistence`, `DynamoDBRunStore`, `CloudLauncher`, `RunState`, `test_lifecycle_states.py`, `RunResult`, `test_subprocess_engine.py`, `serialize.py`, `EventLog`, `StepDone`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `RunMeta` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunMeta` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 23 INFERRED edges - model-reasoned connections that need verification._