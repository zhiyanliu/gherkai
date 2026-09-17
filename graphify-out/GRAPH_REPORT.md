# Graph Report - yaozhou  (2026-09-17)

## Corpus Check
- 273 files · ~280,384 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5025 nodes · 11424 edges · 271 communities (184 shown, 87 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 719 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e73bef05`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Job
- JobState
- test_workers.py
- test_backend_cloud.py
- workers.py
- test_main.py
- _build_parser
- _tagged_feature
- test_project.py
- _fixture
- test_container.py
- test_lifecycle_states.py
- _run_step
- test_schedule.py
- test_stack.py
- test_deploy_cmd.py
- test_cloud_reconcile.py
- test_evidence.py
- test_artifact_lines_report_write_failure_falls_back_to_a_note
- run_scope.py
- ensure_workflow_definition
- test_cloud_integration.py
- LocalReportStore
- test_tunnel_cli.py
- test_reconcile.py
- _fake_locator
- ADR 0016 执行架构 / 组合根注入
- test_provider.py
- test_interrupt_model.py
- Status
- 权威信息源（自查用）REFERENCES
- test_worker_variant.py
- test_skill.py
- RunState
- RunResult（事件流归约终值）
- ADR 0033 IaC 资源清单与命名契约
- model.py
- render.py
- JobResult
- test_user_steps.py
- main
- BackendStack
- test_lambda_handlers.py
- _explain_run
- RunPersistence
- _is_transient_network
- deterministic.mts
- deterministic.py
- Artifact Upload Tests
- Midscene Worker 开发笔记
- evidence.mts
- ._run_cdk
- test_sqlite_event_log.py
- _engine_with_fake_ecs
- test_plan.py
- _FakeEcsClient
- build_fargate_engines
- test_fargate_engine.py
- Artifact Uploader (Python)
- _RecUploader
- test_report_still_written_when_the_run_duration_read_fails
- main
- gherkai_runtime/names.py
- ADR 0029 引擎产物上传 S3
- report_store/local.py
- test_event_sink.py
- event-sink.mts
- @gherkai/worker-midscene (README)
- reconciler.py
- test_lambda_asset.py
- deploy.py
- FargateEngine
- _MissingThenStoppedEcs
- _FakeEcs
- atomic_write_json
- test_argument.py
- 05-negative-assertions.ts
- TypeScript Config
- 执行与推进模型导览
- test_tunnel_host.py
- _StubEcs
- Eval Harness Runner
- build_engines
- ADR 0042: step 证据与 explain
- Skill Stage Materialization
- Skill Install Command
- test_cli_json_contract.py
- _stream_record
- JobSource
- ADR 0028 瞬时网络/SSL 韧性
- gherkai_runtime/__init__.py
- _FakeS3
- SqliteEventLog
- ADR 0037 分发与打包
- RunStore
- ArtifactUploader
- Spy
- runtime/compose.py — 组合根/引擎注册表
- dependencies
- _StampSsm
- S3StepArgumentOffloader
- evidence.test.mts
- README & Docs Guardrails
- _Recorder
- @aws-sdk/client-dynamodb
- check_version_skew
- map_origin_in_jobs
- events_wallclock.py
- _render_status
- parse.py
- parametrize
- user_steps.py
- FeatureSource
- compose.py
- test_subprocess_engine.py
- query_capabilities
- _read_events
- ._resolve_target
- _CdkWritingContext
- Midscene Worker Package Manifest
- Provider
- run-scope.test.mts
- Distribution Metadata Checks
- exit_observer.py
- gherkai_cli/__main__.py
- _doc_rules.py
- ADR 0001 范围限定英文 UI
- Skill Deploy Token Guardrail
- 03-midscene-grounding.ts
- Skill Contract Rendering
- test_user_facing_messages.py
- release.yml — 发布全链工作流
- scope.py
- CONTENT_TYPES
- _ClientError
- _FakeProc
- job-source.mts
- _stopped_detail
- artifact-upload.test.mts
- Worker Signal Interrupt Tests
- _FakeSink
- tunnel_host.py
- test_tunnel.py
- ECS Task Timing Capture
- _await_engine
- user-steps.mts
- build_local_reconcile
- Graph Refresh Script
- Doc Flag Path Validation
- test_detached_launcher.py
- Nova worker flag-only 信号 handler
- Contract Key Documentation Check
- argument.mts
- parse_iso
- _argv
- _run_with_refs
- Echo Test Worker
- Cloud Test Infrastructure Check
- _det_feature
- e2e_harness.py
- RunResult
- CountingEcs
- user-steps.test.mts
- TypeScript Dev Dependencies
- Skill Frontmatter Validation
- _patch_skew
- deterministic.steps.mts
- bin.mts
- cli.py
- Worker Image Version Mappings
- _seed_worker_ssm
- Event Reduction & Short-Circuit
- Package File Manifest
- Repository Metadata
- Worker Artifact Upload
- Upload Call Recorder
- Skill Evaluation Design
- NPM Scripts
- AgentCore CDP Spike
- Background Upload Queue
- RevisionInfo
- test_local_result_store_atomic.py
- SubprocessLauncher
- test_finished_run_gate_keys_on_the_committed_run_status_only
- Adapters Package
- _runs_stream_record
- _FakeTable
- index.mts
- TSX Dependency
- Upload Queue Drain
- Uploader Enabled Check
- Uploader Config Fail-Loud
- No-op Local Uploader
- Index Wait Script
- Workspace Root Package
- test_final_drain_paginates_across_last_evaluated_key
- Planning Model Decision
- Exit Code Layering
- Preflight Ordering
- Read Consistency Strategy
- GherkAI Core Module
- AWS Deployment Package
- GherkAI Runtime
- NovaAct Worker Service
- resolve-hook.mts
- error-text.mts
- event-sink.test.mts
- gherkai_deploy_aws/names.py
- _AbsentEngine
- agentcore-sigv4.test.mts
- job-source.test.mts
- _advancer_stmts
- .preflight
- test_raise_for_worker_exit_maps_codes_with_fargate_label
- test_kicker_timeout_path_builds_once
- @aws-sdk/client-bedrock-agentcore
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- test_final_drain_logs_real_holes_under_consistent_read
- test_await_exit_code_transient_missing_then_stopped_reads_code
- test_kicker_timeout_path_skips_tick_when_not_detached
- test_build_defaults_to_one_when_meta_missing
- test_extract_missing_env_returns_none
- test_qwen_model_id_matches_the_midscene_worker_source
- no-artifacts.test.mts
- ADR-0019
- _gap_engine
- ADR-0020
- _cmd_tunnel_watch
- ADR-0022
- ADR-0026
- ADR-0027
- ADR-0032
- openai
- ADR-0035
- MODEL
- test_compose.py
- ADR-0033
- ADR-0037
- ADR-0016
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0032
- ADR-0033
- ADR-0042
- UPLOAD_TIMEOUT_MS
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- BROWSER_CLOSE_BUDGET_MS
- CONNECT_BACKOFF_MS
- INFLIGHT_SETTLE_MS
- Job
- MIN_GRACE_MARGIN_MS
- ADR-0014
- ADR-0024
- ADR-0028
- ADR-0029
- test_worker_subnets_single_source_across_ssm_and_lambda_env
- ADR-0031
- ADR-0036
- ADR-0037
- ADR-0042
- QUEUE_DRAIN_EXIT_MS
- Scenario
- ShutdownDeps
- Step
- STOP_SESSION_BUDGET_MS
- detached.py

## God Nodes (most connected - your core abstractions)
1. `main()` - 214 edges
2. `Job` - 134 edges
3. `RunState` - 126 edges
4. `RunMeta` - 119 edges
5. `Status` - 106 edges
6. `JobState` - 100 edges
7. `Provider` - 93 edges
8. `JobResult` - 83 edges
9. `Scenario` - 73 edges
10. `Step` - 72 edges

## Surprising Connections (you probably didn't know these)
- `gherkai agent SKILL.md` --references--> `ADR 0001 范围限定英文 UI`  [AMBIGUOUS]
  cli/gherkai_cli/skills/gherkai/SKILL.md → docs/adr/0001-scope-limited-to-english-ui.md
- `--expose-local 隧道` --conceptually_related_to--> `ADR 0035 经隧道测本机应用`  [INFERRED]
  cli/gherkai_cli/skills/gherkai/SKILL.md → docs/adr/0035-local-app-testing-via-tunnel.md
- `README.md — 仓库首页（使用者向）` --conceptually_related_to--> `跑法权限梯 (Execution tiers)`  [INFERRED]
  README.md → CONTEXT.md
- `_status_cloud()` --calls--> `DynamoDBRunStore`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/run_store/ddb.py
- `_is_detached()` --calls--> `DynamoDBRunStore`  [INFERRED]
  deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py → core/gherkai_core/adapters/run_store/ddb.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **文档/代码健康度复盘方法对（含分工与纪律源）** — docs_doc_health_review, docs_code_health_review, claude, context, docs_references [EXTRACTED 0.80]
- **双引擎可对标基准与 AI 断言可靠性** — docs_adr_0010_spike_as_apples_to_apples_benchmark, docs_adr_0001_scope_limited_to_english_ui, docs_adr_0014_ai_first_assertions, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0027_runreport_aggregation_index [EXTRACTED 0.80]
- **AWS 硬约束下的模型/鉴权选型链** — docs_adr_0009_maximize_aws_hard_constraint, docs_adr_0002_midscene_not_driven_by_gpt55, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0004_novaact_iam_auth_via_workflow, docs_adr_0008_midscene_bedrock_auth_sigv4_selfsign, docs_adr_0012_planning_shares_qwen3vl_no_text_planner [EXTRACTED 0.85]
- **run 级执行参数随 definition 走的载体惯例（omit-when-None、core 只搬运）** — docs_adr_0035_local_app_testing_via_tunnel_extra_http_headers, docs_adr_0037_distribution_and_packaging_steps_dir, docs_adr_0038_worker_image_delivery_variant, docs_adr_0034_detached_batch_reconciler_job_timeout [EXTRACTED 0.85]
- **三条去污染硬规则与隔离面护栏** — docs_adr_0043_agent_skill_for_driving_gherkai_decontamination_rules, docs_adr_0043_agent_skill_for_driving_gherkai_isolation_surface, docs_adr_0043_agent_skill_for_driving_gherkai_materialize_py, docs_adr_0043_agent_skill_for_driving_gherkai_summarize_runs_py, docs_adr_0043_agent_skill_for_driving_gherkai_eval_results [EXTRACTED 0.85]
- **执行栈：窄腰核心 + ports + 薄 worker + 推进器** — context_core_narrow_waist, context_ports_layer, context_engine_port, context_thin_worker, context_advancer, context_deterministic_step_registry [EXTRACTED 0.85]
- **Gherkin Tag Configuration System (scope/engine/timeout → plan/schedule)** — docs_adr_0019_feature_tags_scope_and_engine_scope_tag, docs_adr_0019_feature_tags_scope_and_engine_engine_tag, docs_adr_0019_feature_tags_scope_and_engine_timeout_tag, docs_adr_0025_plan_module_feature_to_jobs, docs_adr_0026_schedule_module [EXTRACTED 0.85]
- **优雅终止分层：schedule 下逻辑停 → handle → adapter 机制 → worker 会话清理** — docs_adr_0026_schedule_module_graceful_termination, docs_adr_0026_schedule_module_workerhandle, docs_adr_0026_schedule_module_job_timeout, docs_adr_0026_schedule_module_fail_fast, docs_adr_0028_transient_network_ssl_resilience_session_leak_protection [EXTRACTED 0.85]
- **Midscene → Bedrock SigV4 自签鉴权链路** — engines_midscene_lib_agentcore_sigv4, engines_midscene_spikes_sigv4_fetch, engines_midscene_spikes_create_openai_client, engines_midscene_worker_run_scope, adr_0008, adr_0003 [EXTRACTED 0.85]
- **plan 流水线：feature → parse → scope → Job** — docs_adr_0025_plan_module_feature_to_jobs_plan, docs_adr_0025_plan_module_feature_to_jobs_parse, docs_adr_0025_plan_module_feature_to_jobs_scope, docs_adr_0025_plan_module_feature_to_jobs_job, docs_adr_0025_plan_module_feature_to_jobs_id_derivation [EXTRACTED 0.85]
- **两引擎共有的使用方 steps 加载与 fail-loud 契约** — engines_midscene_worker_user_steps, engines_novaact_gherkai_worker_novaact_user_steps, concept_fail_loud_steps_loading, concept_deterministic_step, adr_0037 [EXTRACTED 0.85]
- **判定模型：状态、短路与聚合归约** — context_verdict_states, context_shortcircuit, context_run_data_model, docs_guides_verdict_model [EXTRACTED 0.85]
- **面向 AI agent 的三层：命令面能力 → 机读证据 → 随包发行的 skill 教材** — docs_adr_0041_agent_facing_cli_affordances, docs_adr_0042_step_evidence_and_explain, docs_adr_0043_agent_skill_for_driving_gherkai, docs_adr_0041_agent_facing_cli_affordances_json_contract, docs_adr_0043_agent_skill_for_driving_gherkai_transform_copy [EXTRACTED 0.90]
- **AI 断言纪律：对称布尔投票 + 确定性逃生舱 + 定位边界** — docs_adr_0014_ai_first_assertions, docs_adr_0014_ai_first_assertions_assertion_votes, docs_adr_0015_v1_positioning_smoke_not_regression, docs_adr_0015_v1_positioning_smoke_not_regression_deterministic_escape_hatch, docs_adr_0015_v1_positioning_smoke_not_regression_uncertainty_a_b [EXTRACTED 0.90]
- **产物指针链：worker 报 ref → 不透明搬运 → ReportStore 归集 → index.html 可点链接** — docs_adr_0029_engine_artifacts_to_s3_worker_upload, docs_adr_0027_runreport_aggregation_index_reportref, docs_adr_0027_runreport_aggregation_index_opaque_transport_rule, docs_adr_0027_runreport_aggregation_index_reportstore, docs_adr_0027_runreport_aggregation_index_make_href, docs_adr_0027_runreport_aggregation_index_index_html [EXTRACTED 0.90]
- **契约页 → 确定性转换副本 → 护栏链** — docs_guides_cli_json_contract, docs_adr_0043_agent_skill_for_driving_gherkai_render_skill_contract, docs_adr_0043_agent_skill_for_driving_gherkai_skill, docs_adr_0043_agent_skill_for_driving_gherkai_test_skill [EXTRACTED 0.90]
- **Core↔Worker Execution Waist (parse → schedule → worker events → RunReport)** — docs_adr_0024_worker_core_protocol, docs_adr_0025_plan_module_feature_to_jobs, docs_adr_0026_schedule_module, docs_adr_0027_runreport_aggregation_index, docs_adr_0022_bdd_runner_retired_core_parses_thin_worker_b1, docs_adr_0016_execution_architecture_core_lib_run_model [EXTRACTED 0.90]
- **无状态跑批的四个关键机制共同保证并发安全与收敛** — docs_adr_0034_detached_batch_reconciler_task_exited, docs_adr_0034_detached_batch_reconciler_exit_observer, docs_adr_0034_detached_batch_reconciler_hwm, docs_adr_0034_detached_batch_reconciler_cas, docs_adr_0034_detached_batch_reconciler_reconciler [EXTRACTED 0.90]
- **events-out 传输选型（DDB 选定 vs 三方案被拒）** — docs_adr_0024_worker_core_protocol_ddb_events_transport, docs_adr_0024_worker_core_protocol_rejected_sqs_fifo, docs_adr_0024_worker_core_protocol_rejected_msk, docs_adr_0024_worker_core_protocol_rejected_ddb_streams [EXTRACTED 0.90]
- **两臂评测一轮的资产与顺序** — docs_adr_0043_agent_skill_for_driving_gherkai_materialize_py, docs_adr_0043_agent_skill_for_driving_gherkai_run_evals_py, docs_adr_0043_agent_skill_for_driving_gherkai_summarize_runs_py, docs_adr_0043_agent_skill_for_driving_gherkai_grader_prompt, docs_adr_0043_agent_skill_for_driving_gherkai_evals_json, docs_adr_0043_agent_skill_for_driving_gherkai_fixtures [EXTRACTED 0.90]
- **发布全链：一个 git tag 派生全部交付物版本** — github_workflows_release_build, github_workflows_release_pypi, github_workflows_release_npm, github_workflows_release_images, github_workflows_release_gh_release, context_single_version_knob [EXTRACTED 0.90]
- **schedule 三级归约（status + 原生量成本 + 墙钟时长）** — docs_adr_0026_schedule_module_status_reduction, docs_adr_0026_schedule_module_cost_reduction, docs_adr_0026_schedule_module_duration_reduction, docs_adr_0026_schedule_module_runresult, docs_adr_0026_schedule_module_step_skipped_reduction [EXTRACTED 0.90]
- **终止契约三层（逻辑层 / 机制层 / worker 层）** — docs_adr_0024_worker_core_protocol_termination_contract, docs_adr_0024_worker_core_protocol_schedule_stop_layer, docs_adr_0024_worker_core_protocol_worker_handle_subprocess, docs_adr_0024_worker_core_protocol_fargate_worker_handle_stop, docs_adr_0024_worker_core_protocol_nova_flag_only_handler, docs_adr_0024_worker_core_protocol_midscene_cleanup_handler [EXTRACTED 0.90]

## Communities (271 total, 87 thin omitted)

### Community 0 - "Job"
Cohesion: 0.06
Nodes (70): _explain_job(), 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本/JSON 同律）；命中的 scope 的…, test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), DynamoDBRunStore, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。 (+62 more)

### Community 1 - "JobState"
Cohesion: 0.05
Nodes (66): RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, Path, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR…, 读回 definition（RunMeta）；不存在返回 None。, 读回运行态（RunState）；不存在返回 None。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。 (+58 more)

### Community 2 - "test_workers.py"
Cohesion: 0.06
Nodes (92): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), datetime, `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。… (+84 more)

### Community 3 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就退 2（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 4 - "workers.py"
Cohesion: 0.04
Nodes (95): Aws, _cell(), cleanup_pass(), CleanupOutcome, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+87 more)

### Community 5 - "test_main.py"
Cohesion: 0.05
Nodes (83): _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 退 2、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：跑前先问一次能力自述，worker 非零退出 → 起任何 job 之前退 2（不进 job 级 error）。… (+75 more)

### Community 6 - "_build_parser"
Cohesion: 0.09
Nodes (24): _add_selection_flags(), _build_parser(), _cmd_doctor(), _cmd_list_engines(), _cmd_skill_install(), _dist_version(), _doctor_cloud(), _doctor_worker_grace() (+16 more)

### Community 7 - "_tagged_feature"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号 = 任一命中；重复 --tags = 都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 退 2 并列全部候选（id 标题），别静默跑空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope = 报告里的 scope_id：named scope 的名字选中整个 scope（两条都跑），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 8 - "test_project.py"
Cohesion: 0.06
Nodes (78): ScopeStarted, plan_next(), project(), project_full(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, finalize_report() (+70 more)

### Community 9 - "_fixture"
Cohesion: 0.04
Nodes (67): Any, aws(), _fake_aws_creds(), fargate(), moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表…, 连真 DDB/S3 的句柄（真表/桶名读环境变量），供集成测试。**没设环境变量就 skip**（不误连、不报错）。 需你先建好真表 + 真桶（见…, 硬隔离：设假凭证 + 固定 region，绝不误连真 AWS（moto 官方推荐套装）。autouse=每个测试都先生效。 **对…, 在 moto mock 下建好 DDB 表 + S3 桶，产出 (boto3 resource/client, 名字) 供云端 adapter 测试注入。 表… (+59 more)

### Community 10 - "test_container.py"
Cohesion: 0.05
Nodes (54): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+46 more)

### Community 11 - "test_lifecycle_states.py"
Cohesion: 0.09
Nodes (18): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), FakeWorkerHandle, Event (+10 more)

### Community 12 - "_run_step"
Cohesion: 0.07
Nodes (51): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+43 more)

### Community 13 - "test_schedule.py"
Cohesion: 0.17
Nodes (62): AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, Votes, 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver (+54 more)

### Community 14 - "test_stack.py"
Cohesion: 0.06
Nodes (62): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 建新档记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK… (+54 more)

### Community 15 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 皮自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 16 - "test_cloud_reconcile.py"
Cohesion: 0.07
Nodes (46): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写… (+38 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.08
Nodes (49): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), list, parametrize (+41 more)

### Community 19 - "run_scope.py"
Cohesion: 0.06
Nodes (48): ArtifactUploader, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_evidence(), _attach_traj_refs(), _capabilities(), _collect_traj(), _cost_from_result() (+40 more)

### Community 20 - "ensure_workflow_definition"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 21 - "test_cloud_integration.py"
Cohesion: 0.15
Nodes (24): _ddb_store(), _is_ddb_too_large(), _offloader(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, 真 S3：DynamoDBRunStore 挂 offloader，docString/dataTable 搬真 S3、META 只留指针、读回逐字节还原。, 真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。, 真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛… (+16 more)

### Community 22 - "LocalReportStore"
Cohesion: 0.18
Nodes (35): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077… (+27 more)

### Community 23 - "test_tunnel_cli.py"
Cohesion: 0.09
Nodes (39): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。 (+31 more)

### Community 24 - "test_reconcile.py"
Cohesion: 0.12
Nodes (31): 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), _done_events(), FakeLauncher, _meta(), Job, reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。 用真…, job 非0退出（机制二）→ 该 job error → run finalize 为 error。 (+23 more)

### Community 25 - "_fake_locator"
Cohesion: 0.07
Nodes (42): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+34 more)

### Community 26 - "ADR 0016 执行架构 / 组合根注入"
Cohesion: 0.07
Nodes (55): ADR 0004: Nova Act IAM 鉴权经 Workflow, ADR 0005 单一共享 .feature 文件, ADR 0006: 形态 A 两子工程、无编排器, ADR 0010: spike 作同题基准, ADR 0013 跨引擎共享边界, 跨引擎共享止于 features/（+ 使用方 steps/ 约定面）, ADR 0014 AI 优先断言与投票, 对称布尔投票治抖动（assertion_votes） (+47 more)

### Community 27 - "test_provider.py"
Cohesion: 0.07
Nodes (58): _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, 子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。, `--prefix` 在子动词**前**给也必须留住——子 parser 在新 namespace 里解析后整体覆盖回父层，…, 留口子：退 2 并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。, CLI 皮没交版本 → 本包自报 dist 版本（`==` 同版本 pin 成同一个，不引入第二个真源）。, 走**真 parser**、按真实接线顺序拼（皮先声明命令面 flag，provider 再贴自己的旋钮）——不用 SimpleNamespace 手捏… (+50 more)

### Community 28 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (35): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True=中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True=退避中收到停止信号（应停止重连）。 用…, captured() (+27 more)

### Community 29 - "Status"
Cohesion: 0.09
Nodes (29): 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, Status, EngineResolver, JobSink, 状态机单调条件写：仅当 run 总 status 当前为非终态（pending/running）才写终态，成功 True（机制三）。 挡「已 finalize…, Sink, _aggregate(), Event (+21 more)

### Community 30 - "权威信息源（自查用）REFERENCES"
Cohesion: 0.07
Nodes (40): CLAUDE.md — 项目约定, /code-health-review 命令入口, /doc-health-review 命令入口, 文档纪律（ADR / CONTEXT / journey / guides 分层）, graphify 知识图使用约定, 绿 ≠ 对：识别结论的证据边界, CONTEXT.md — 领域术语表, agent skill (gherkai skill) (+32 more)

### Community 31 - "test_worker_variant.py"
Cohesion: 0.08
Nodes (44): _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。, 默认指针不存在（部署没走过 worker 镜像初始化）→ 提示跑 `gherkai deploy`，不猜 `base`。, SSM 无该（引擎，variant）映射 + CLI 与后端同版本 → 引导 push-worker，**不回落默认 variant**。 (+36 more)

### Community 32 - "test_skill.py"
Cohesion: 0.12
Nodes (20): skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, skill_markdown_files(), _all_command_spans(), _claimed_flags(), _parser_nodes(), agent skill 的护栏（ADR 0043 决策六；fixture 三条见决策七）。 skill 是**产品面**：它随 wheel 发行、由…, 扫描面为空即红：目录搬家 / 后缀写错不能让下面几条静默变绿。, 成对比对的扫描面也不能空：一条 `gherkai …` 都抽不到，说明抽取器与写法脱节了。 (+12 more)

### Community 33 - "RunState"
Cohesion: 0.08
Nodes (48): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, cloud 档「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要跑得通， 否则落回 local…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_render_status_pending_run_with_claimed_job_does_not_hint(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal() (+40 more)

### Community 34 - "RunResult（事件流归约终值）"
Cohesion: 0.11
Nodes (23): 原生量成本归约（tokens / time_worked_s）, 墙钟时长归约（duration_ms 四级）, EngineResolver（按 job.engine 解析 Engine）, RunMeta（run definition: run_id + created_at + jobs）, RunResult（事件流归约终值）, schedule(run_meta, engines, sink, opts, ...), index.html（判定明细树 + 产物导航）, JobResult 持有 Job（engine/scope_id property delegate） (+15 more)

### Community 35 - "ADR 0033 IaC 资源清单与命名契约"
Cohesion: 0.07
Nodes (42): submit / status 拆分与接力, DynamoDB 作 events-out 传输（共享表 + Query 轮询）, 事件流结束信号 / 存活判定迁移, exitCode 落值延迟的有界宽限轮询, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列, 红线：worker 只直写 events 表、绝不碰 RunState (+34 more)

### Community 36 - "model.py"
Cohesion: 0.04
Nodes (91): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate… (+83 more)

### Community 37 - "render.py"
Cohesion: 0.07
Nodes (39): _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches(), explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…, 读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。…, 没有判定明细可渲染时的输出：人读打一行提示、`--json` 仍只打一个（scopes 为空的）文档。恒退 0。 退 0 而非 2 是刻意的（ADR 0042…, local/cloud 共用的后半段：取判定明细 → 筛 scenario/step → 合成文档 → 打文本或 JSON。 带 `scope_id` 时只… (+31 more)

### Community 38 - "JobResult"
Cohesion: 0.06
Nodes (48): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。 (+40 more)

### Community 39 - "test_user_steps.py"
Cohesion: 0.09
Nodes (38): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), _isolate(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, `_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。, `_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。 (+30 more)

### Community 40 - "main"
Cohesion: 0.06
Nodes (46): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 `__main__`（argparse 皮）+ `render`（表层渲染）+…, main(), 对照：定位链 miss（运行时没装）plan 仍降级退 0（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 退 2「读 feature 失败」，不是 IsADirectoryError traceback（退码语义 ADR…, cloud 档第一道闸是版本 skew（先于任何云端读）：block → 退 2，且根本没去装 store。, --version 打印「gherkai <发行版本>」并退 0——版本真源是包元数据（git tag → uv-dynamic-versioning），…, test_default_engine_flag_has_choices(), test_explain_cloud_blocks_on_version_skew_before_any_cloud_read() (+38 more)

### Community 41 - "BackendStack"
Cohesion: 0.10
Nodes (18): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+10 more)

### Community 42 - "test_lambda_handlers.py"
Cohesion: 0.07
Nodes (28): cloud_env(), Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。 (+20 more)

### Community 43 - "_explain_run"
Cohesion: 0.11
Nodes (28): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三档，可重复且彼此为或。, --step 单给退 2（步号没有归属）；命中的 scenario 都没有第 N 步 → 退 2 并列出候选 id 与步数； 正常时只渲染每条命中… (+20 more)

### Community 44 - "RunPersistence"
Cohesion: 0.10
Nodes (28): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, Event, RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。 为什么是 core…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run… (+20 more)

### Community 45 - "_is_transient_network"
Cohesion: 0.10
Nodes (35): _error_text(), _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, SDK 异常的 str() 是多行 repr（真跑暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message 首行、折叠空白、封顶。 (+27 more)

### Community 46 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 47 - "deterministic.py"
Cohesion: 0.08
Nodes (36): deterministic, clear(), deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match() (+28 more)

### Community 48 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 49 - "Midscene Worker 开发笔记"
Cohesion: 0.08
Nodes (36): ADR 0002 不用 gpt-5.5 驱动 Midscene, ADR 0003 Midscene grounding 用 Qwen3-VL on Bedrock, ADR 0004 Nova Act 经 Workflow 的 IAM 鉴权, ADR 0008 Midscene Bedrock SigV4 自签, ADR 0010 spike 作 apples-to-apples 基准, ADR 0014 AI 断言投票, ADR 0016 执行架构 core/lib/run 模型, ADR 0020 step 措辞默认 AI + 确定性脚手架 (+28 more)

### Community 50 - "evidence.mts"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct, EvidenceDoc (+21 more)

### Community 51 - "._run_cdk"
Cohesion: 0.16
Nodes (10): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), Path, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, 凡要合成 app 的动作（deploy / diff / synth / destroy）都必须有 `--vpc`（无隐式默认，ADR 0037 决策 6：…, 生成的 `cdk.json` 里的 `app`：用**当前解释器**跑本包的 CDK app。 必须是 `sys.executable`、不是裸… (+2 more)

### Community 52 - "test_sqlite_event_log.py"
Cohesion: 0.20
Nodes (14): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。, test_append_and_read_back_events() (+6 more)

### Community 53 - "_engine_with_fake_ecs"
Cohesion: 0.25
Nodes (8): _engine_with_fake_ecs(), DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null(), test_probe_task_stopped_with_exit_code()

### Community 54 - "test_plan.py"
Cohesion: 0.12
Nodes (30): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串 = 两组派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否…, @scope 的值等于某条**自身已标 @scope** 的 scenario 的 id → 不报错：那条 id 根本没当分组键，不会撞。, 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ PlanError（ADR 0025：标了 tag…, test_assertion_votes_default_is_one() (+22 more)

### Community 55 - "_FakeEcsClient"
Cohesion: 0.15
Nodes (16): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), 跑一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。 (+8 more)

### Community 56 - "build_fargate_engines"
Cohesion: 0.08
Nodes (23): build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), 读某 task-def revision 上 worker container 的 `stopTimeout`（秒）= **cloud 档真实的停止宽限**。…, cloud 档一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。 (+15 more)

### Community 57 - "test_fargate_engine.py"
Cohesion: 0.11
Nodes (45): _delayed_stopped_ecs(), _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。 (+37 more)

### Community 58 - "Artifact Uploader (Python)"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内跑（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 59 - "_RecUploader"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只跑到收尾序列）。 (+10 more)

### Community 60 - "test_report_still_written_when_the_run_duration_read_fails"
Cohesion: 0.20
Nodes (11): now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, _job(), run 级墙钟取数失败不得连坐报告收尾（ADR 0030 决定三：commit point 之后的失败无人重试）。 墙钟是派生指标，取它要在 finalize…, region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…, RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的…, test_build_local_reconcile_reads_steps_dir_from_definition() (+3 more)

### Community 61 - "main"
Cohesion: 0.14
Nodes (11): agentOpts(), cumulativeTokens(), drainArtifactQueue(), isTransientNetwork(), log(), main(), runScenario(), runStep() (+3 more)

### Community 62 - "gherkai_runtime/names.py"
Cohesion: 0.09
Nodes (26): default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…, prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。 (+18 more)

### Community 63 - "ADR 0029 引擎产物上传 S3"
Cohesion: 0.08
Nodes (32): Engine port（run_scope，不挂 stop）, EventSink（事件出口可注入接口）, events 表键设计 PK=run_id#scope_id / SK=seq, events item TTL 自动过期（expires_at 7 天）, FargateWorkerHandle.stop → StopTask, 未来演进：显式 core→worker 控制通道, JobSource（job 入口可注入接口）, Midscene worker 有序显式 cleanup handler (+24 more)

### Community 64 - "report_store/local.py"
Cohesion: 0.12
Nodes (18): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+10 more)

### Community 65 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 66 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd()

### Community 67 - "@gherkai/worker-midscene (README)"
Cohesion: 0.22
Nodes (11): AgentCore 云浏览器（本机不装 Chromium）, 确定性 step, 镜像必须 --platform linux/amd64, 纯 IAM 鉴权（无 API key）, src/index.mts — 包公开 API, @gherkai/worker-midscene (README), src/worker/deterministic.mts — 确定性注册表, src/worker/deterministic.steps.mts — 内建脚手架 step (+3 more)

### Community 68 - "reconciler.py"
Cohesion: 0.11
Nodes (23): _build(), EventBridgeTimeoutWatch, _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)… (+15 more)

### Community 69 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (25): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path (+17 more)

### Community 70 - "deploy.py"
Cohesion: 0.15
Nodes (15): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+7 more)

### Community 71 - "FargateEngine"
Cohesion: 0.15
Nodes (14): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+6 more)

### Community 72 - "_MissingThenStoppedEcs"
Cohesion: 0.10
Nodes (12): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, _MissingThenStoppedEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。 (+4 more)

### Community 73 - "_FakeEcs"
Cohesion: 0.10
Nodes (16): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` = 在跑的 task；`tasks` = 带状态的…, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…, task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录… (+8 more)

### Community 74 - "atomic_write_json"
Cohesion: 0.13
Nodes (20): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+12 more)

### Community 75 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 76 - "05-negative-assertions.ts"
Cohesion: 0.12
Nodes (13): main(), BASE_URL, main(), ADR-0033, BASE_URL, Check, main(), MODEL_CONFIG (+5 more)

### Community 77 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 78 - "执行与推进模型导览"
Cohesion: 0.20
Nodes (19): 推进器 (advancer), job 墙钟预算 (job timeout), 产物与证据地理, CLI --json 字段契约, 云端后端的五个载体, 确定性 step 的一生, 三级短路派发链（注册表 → 内建 URL 导航 → AI）, worker 进程内的确定性注册表（唯一匹配面） (+11 more)

### Community 79 - "test_tunnel_host.py"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 80 - "_StubEcs"
Cohesion: 0.22
Nodes (4): 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 81 - "Eval Harness Runner"
Cohesion: 0.18
Nodes (20): collect_outputs(), fail(), load_evals(), main(), materialize(), parse_events(), pollution_metrics(), _purge_session_dir() (+12 more)

### Community 82 - "build_engines"
Cohesion: 0.06
Nodes (40): build_engines(), load_feature(), local_artifact_locations(), make_resolver(), prune_empty_dirs(), Path, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导… (+32 more)

### Community 83 - "ADR 0042: step 证据与 explain"
Cohesion: 0.07
Nodes (39): URL 映射：feature 写原始地址、组装 job 时替换, ADR 0039 用户可见面不带内部指代：产品文案与文档分层, 禁词表与相对链接护栏（_doc_rules 共享常量）, README / DEVELOPMENT 按读者分层, ADR 0041: 面向 agent 的 CLI 可用性, gherkai doctor 只读自检, cli-json-contract.md 字段契约 + 真值集对照护栏, --quiet 把 worker 日志落盘 (+31 more)

### Community 84 - "Skill Stage Materialization"
Cohesion: 0.27
Nodes (20): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+12 more)

### Community 85 - "Skill Install Command"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.17
Nodes (18): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/guides/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。, 递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque =… (+10 more)

### Community 87 - "_stream_record"
Cohesion: 0.11
Nodes (19): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events… (+11 more)

### Community 88 - "JobSource"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 89 - "ADR 0028 瞬时网络/SSL 韧性"
Cohesion: 0.12
Nodes (19): failFast 与失败隔离, 优雅终止（schedule 只下逻辑「停」指令）, _heartbeat_wrap（静默 worker 存活心跳）, Job.timeout_s 超时兜底, max_concurrency（默认 4）, job 级网络重试（network_retry，默认 0）, ScheduleOpts（并发/隔离/grace/重试/心跳旋钮）, WorkerHandle.stop(gracePeriod) (+11 more)

### Community 90 - "gherkai_runtime/__init__.py"
Cohesion: 0.40
Nodes (3): cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的跑前检查、`list-…, _stub_engine_capabilities(), gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…

### Community 92 - "SqliteEventLog"
Cohesion: 0.16
Nodes (10): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, SqliteEventLog (+2 more)

### Community 93 - "ADR 0037 分发与打包"
Cohesion: 0.11
Nodes (32): cli 包 contributor 文档, 版本 skew 六态比对, VPC 档三态比对, skill 参考：CLI --json 字段契约（生成副本）, skill 参考：云端后端分工与 variant 镜像, skill 参考：引擎选择与确定性 step 模板, skill 参考：环境就位与排障, gherkai agent SKILL.md (+24 more)

### Community 94 - "RunStore"
Cohesion: 0.04
Nodes (43): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, Engine, Event, Job, Protocol, ports 层（ADR 0016 六边形架构）：核心的主要注入口在此（另两个见末段），具体 adapter 由组合根注入。 四个… (+35 more)

### Community 97 - "runtime/compose.py — 组合根/引擎注册表"
Cohesion: 0.24
Nodes (10): worker 定位链, src/bin.mts — worker 唯一入口, src/resolve-hook.mts — 裸 specifier 解析钩子, runtime/compose.py — 组合根/引擎注册表, compose.build_engines, compose.build_fargate_engines, compose.check_backend_skew, compose.resolve_worker_cmd — worker 四级定位链 (+2 more)

### Community 98 - "dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 99 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 100 - "S3StepArgumentOffloader"
Cohesion: 0.04
Nodes (45): 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。 (+37 more)

### Community 101 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 102 - "README & Docs Guardrails"
Cohesion: 0.14
Nodes (15): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录与每个包目录各一份 DEVELOPMENT.md。, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归 DEVELOPMENT.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, release.yml 里 `body: |` 块标量的正文。不引 yaml 库（dev 依赖里没有它、别为一条护栏引入）：按缩进收块。, GitHub Release 正文 = Releases 页面，且是各包 pyproject `[project.urls] Changelog`… (+7 more)

### Community 103 - "_Recorder"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 退 2 且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前退 2。 **不能落到 cdk…, _Recorder (+3 more)

### Community 105 - "check_version_skew"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 106 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 107 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 108 - "_render_status"
Cohesion: 0.21
Nodes (16): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。 (+8 more)

### Community 109 - "parse.py"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 110 - "parametrize"
Cohesion: 0.17
Nodes (15): _fixture_files(), _is_ignored(), parametrize, Path, 零内部指代：skill 落在使用方项目里，ADR 编号 / 决策号 / 内部机制名对那边的 agent 是噪声。, markdown 相对链接一律禁：出 skill 的（`](../…)`）在安装态必死；skill 内的（`](references/x.md)`）虽活，…, 指本仓库的 URL 只用 `blob/HEAD/` / `tree/HEAD/` / `tree/v…/`（裸仓库首页不指内容，也放行）：…, 提交前抓漏：磁盘上 `fixtures/**` 每个文件都在 `git ls-files` 里（干净克隆上恒绿，不是 CI 的唯一防线—— 行为式… (+7 more)

### Community 111 - "user_steps.py"
Cohesion: 0.18
Nodes (13): steps 加载 fail-loud 不静默降级, src/worker/user-steps.mts — 使用方 steps 加载, _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >… (+5 more)

### Community 112 - "FeatureSource"
Cohesion: 0.19
Nodes (17): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只跑 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次跑哪几条。… (+9 more)

### Community 113 - "compose.py"
Cohesion: 0.05
Nodes (54): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_worker_template_path(), _find_worker_spec(), is_botocore_error(), _make_ecr_client(), _make_ecs_client(), _make_lambda_client(), _make_ssm_client() (+46 more)

### Community 114 - "test_subprocess_engine.py"
Cohesion: 0.29
Nodes (17): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried() (+9 more)

### Community 115 - "query_capabilities"
Cohesion: 0.07
Nodes (36): engine_min_grace(), match_deterministic(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc() (+28 more)

### Community 116 - "_read_events"
Cohesion: 0.15
Nodes (12): _join_pumps(), _pump_log(), Event, Job, Popen, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+4 more)

### Community 117 - "._resolve_target"
Cohesion: 0.17
Nodes (8): 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…, flag → CDK context（app/stack 侧读的那四个旋钮 + 版本戳）。 `--vpc` 一个 flag 摊成两个旋钮：`default`…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本单旋钮）。 优先 CLI 皮交进来的 `args.version`（=…

### Community 118 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 119 - "Midscene Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 120 - "Provider"
Cohesion: 0.10
Nodes (22): Provider, ArgumentParser, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。 (+14 more)

### Community 121 - "run-scope.test.mts"
Cohesion: 0.10
Nodes (11): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+3 more)

### Community 122 - "Distribution Metadata Checks"
Cohesion: 0.28
Nodes (12): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。 (+4 more)

### Community 123 - "exit_observer.py"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 124 - "gherkai_cli/__main__.py"
Cohesion: 0.06
Nodes (63): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_deploy(), _cmd_destroy(), _cmd_explain(), _cmd_list_deterministic() (+55 more)

### Community 125 - "_doc_rules.py"
Cohesion: 0.21
Nodes (11): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, Path, 使用者面 markdown 的共享规则与扫描器：多处护栏共用的**单一事实源**。…, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。 (+3 more)

### Community 126 - "ADR 0001 范围限定英文 UI"
Cohesion: 0.12
Nodes (22): ADR 0001 范围限定英文 UI, ADR 0002 Midscene 不用 Bedrock GPT-5.5, ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL, ADR 0007 程序化登录，HITL 仅作调试逃生舱, ADR 0008: Midscene→Bedrock SigV4 自签鉴权, ADR 0009 最大化使用 AWS 是硬前提, ADR 0011 AgentCore 浏览器：默认 vs 自建, ADR 0012 planning 复用 Qwen3-VL、不引独立文本规划器 (+14 more)

### Community 127 - "Skill Deploy Token Guardrail"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 皮 + provider 拼出的真 parser。皮那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` = `gherkai <verb>` 本身）。 (+3 more)

### Community 128 - "03-midscene-grounding.ts"
Cohesion: 0.14
Nodes (14): ADR-0010, src/lib/agentcore-sigv4.mts — SigV4 与 region 解析, BASE_URL, main(), makePng(), REGION, ADR-0033, BASE_URL (+6 more)

### Community 129 - "Skill Contract Rendering"
Cohesion: 0.26
Nodes (11): _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 130 - "test_user_facing_messages.py"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 131 - "release.yml — 发布全链工作流"
Cohesion: 0.11
Nodes (22): 使用方 (Consumer) vs contributor, 部署 provider (deploy provider), 部署方 (Deployer), 确定性 step 注册表, 跑法权限梯 (Execution tiers), 点名检查 vs 确定性锚点, feature 作者 (Feature author / QA), 柔性冒烟 (Flexible smoke) (+14 more)

### Community 132 - "scope.py"
Cohesion: 0.26
Nodes (13): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where = 出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。 (+5 more)

### Community 134 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 135 - "_FakeProc"
Cohesion: 0.12
Nodes (15): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——… (+7 more)

### Community 136 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 137 - "_stopped_detail"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode = 容器没跑起来（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 138 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 139 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 140 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 141 - "tunnel_host.py"
Cohesion: 0.25
Nodes (8): 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 142 - "test_tunnel.py"
Cohesion: 0.19
Nodes (15): NgrokTunnel, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, stop_tunnel(), _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen… (+7 more)

### Community 143 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 144 - "_await_engine"
Cohesion: 0.60
Nodes (5): _await_engine(), _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 145 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 146 - "build_local_reconcile"
Cohesion: 0.21
Nodes (12): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。, 对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/cloud 档）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…, 接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从…, _seed_for_build() (+4 more)

### Community 147 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 148 - "Doc Flag Path Validation"
Cohesion: 0.29
Nodes (8): is_placeholder(), `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, _allowed_flags(), 只认**同一个反引号代码跨**内的 `gherkai <子命令> … --flag` 组合，逐对对照该 subparser 的真 flag 集。…, 裸词序列 → 子命令路径。第一个词不是已知子命令且不是占位符 → None（拼错的子命令）。, 路径上（含各级祖先）声明的 flag 全集——`deploy --prefix p push-worker …` 这种父层给法是合法的。, _resolve(), test_flags_are_attached_to_the_right_subcommand()

### Community 149 - "test_detached_launcher.py"
Cohesion: 0.20
Nodes (19): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。 **真 spawn echo_worker…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize… (+11 more)

### Community 150 - "Nova worker flag-only 信号 handler"
Cohesion: 0.13
Nodes (15): act 有界返回（per-act timeout）, cdp_session.__exit__ 释放 AgentCore 会话, 建连早期误报 engine_error 根治, errorType 分类, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, handler 内零 I/O（只置标志 + 记信号号）, ScheduleOpts.min_grace_s（core 只校验关系）, 组合根单一 NOVA_ACT_TIMEOUT_S 常量 (+7 more)

### Community 151 - "Contract Key Documentation Check"
Cohesion: 0.33
Nodes (6): _documented_keys(), 契约页记载的字段名。取「字段表里（任一列）+『顶层…』/『每项…』散文里」的反引号 token， 再按键形状过滤——ADR…, skill 里形如 JSON 键的反引号 token 必须是契约页记载的键，否则显式登记成非键。 挡的是「把 `record_missing` 写成…, test_key_shaped_tokens_are_documented_keys(), collect(), main()

### Community 152 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 153 - "parse_iso"
Cohesion: 0.25
Nodes (8): parse_iso(), datetime, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, detached run 的 run 级墙钟（毫秒）= RunState `ended_at` - `started_at`（提交落库到 finalize…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), test_run_duration_ms_from_run_state_timestamps()

### Community 154 - "_argv"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证， 不会跑…, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 155 - "_run_with_refs"
Cohesion: 0.31
Nodes (12): _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index(), test_index_html_links_and_summary(), test_index_html_taints_shortcircuited_step() (+4 more)

### Community 156 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 158 - "_det_feature"
Cohesion: 0.17
Nodes (12): _det_feature(), plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。, 冲突预检（真跑将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。, 标注 best-effort：引擎环境未装/查询失败 → 无标注 + stderr 警告，plan 核心输出不受影响。, plan 的分叉与 run/submit **相反**（ADR 0037 决策 3 明示 + ADR 0036 决策 4）：保持 best-effort…, 两个非 job 入口同样加载 steps 目录（ADR 0037 决策 4）→ plan 标注与 list-deterministic 清单反映定制 step。, test_plan_and_list_deterministic_pass_steps_dir_to_worker(), test_plan_annotates_deterministic_hits() (+4 more)

### Community 159 - "e2e_harness.py"
Cohesion: 0.33
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 160 - "RunResult"
Cohesion: 0.11
Nodes (29): RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…, render_text(), _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, cloud 档：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import… (+21 more)

### Community 162 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 163 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 164 - "Skill Frontmatter Validation"
Cohesion: 0.50
Nodes (4): _frontmatter_and_body(), 极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。 支持 `key: 单行值`、引号值，以及 `key:…, `name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环…, test_skill_form_limits()

### Community 165 - "_patch_skew"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 同款的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 166 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 167 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 168 - "cli.py"
Cohesion: 0.06
Nodes (40): cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_ssm_client(), _make_sts_client() (+32 more)

### Community 169 - "Worker Image Version Mappings"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 170 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 171 - "Event Reduction & Short-Circuit"
Cohesion: 0.50
Nodes (4): job 归约的 scope_done 内容完整前置, status 三级归约（scenario→job→run）, step_skipped 归约（scope 内短路）, scope 内 step 级短路（worker 侧）

### Community 172 - "Package File Manifest"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 173 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 174 - "Worker Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 175 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素 = (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 176 - "Skill Evaluation Design"
Cohesion: 0.67
Nodes (3): ADR 0043 skill 评测设计, 评分子代理提示词模板, skills/ 目录说明

### Community 177 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 180 - "RevisionInfo"
Cohesion: 0.50
Nodes (3): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo

### Community 181 - "test_local_result_store_atomic.py"
Cohesion: 0.38
Nodes (6): _big_job_result(), LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 跑到一半时读…, ~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。, 判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。, test_concurrent_reader_never_sees_torn_job_result(), test_job_result_file_stays_readable_by_others()

### Community 182 - "SubprocessLauncher"
Cohesion: 0.18
Nodes (8): Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, Event, Job, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, SubprocessLauncher, Timer

### Community 183 - "test_finished_run_gate_keys_on_the_committed_run_status_only"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后跑完的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 185 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 187 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 206 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 208 - "gherkai_deploy_aws/names.py"
Cohesion: 0.13
Nodes (14): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, CloudFormation stack 名（= `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 生效 VPC 档的 SSM 路径（ADR 0037 决策 6「VPC 档持久化比对，三态齐全」）。 值形态三档：`default` / `new:<所建… (+6 more)

### Community 212 - "_advancer_stmts"
Cohesion: 0.40
Nodes (5): _advancer_stmts(), Template, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…, test_reconciler_and_kicker_have_the_same_permission_face()

### Community 228 - "_gap_engine"
Cohesion: 0.20
Nodes (11): _ev_item(), _gap_engine(), 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 洞在宽限后仍在 = 写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。, 「连续 MISSING」的连续性被有进展的轮次打断：事件/空轮交替、空轮都探到 MISSING，累计 3 次但从不连续 2 次， 宽限 1…, test_read_events_gap_beyond_grace_is_skipped_with_warning() (+3 more)

### Community 238 - "test_compose.py"
Cohesion: 0.06
Nodes (51): 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_cloud_target(), resolve_region(), resolve_worker_cmd(), _clear_aws_env(), _fake_store_ctors() (+43 more)

### Community 260 - "test_worker_subnets_single_source_across_ssm_and_lambda_env"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 275 - "detached.py"
Cohesion: 0.15
Nodes (12): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。 (+4 more)

## Ambiguous Edges - Review These
- `ADR 0001 范围限定英文 UI` → `gherkai agent SKILL.md`  [AMBIGUOUS]
  docs/adr/0001-scope-limited-to-english-ui.md · relation: references
- `成功重试对 RunResult 透明（可观测性缺口）` → `上传成功后删本地`  [AMBIGUOUS]
  docs/adr/0029-engine-artifacts-to-s3.md · relation: conceptually_related_to

## Knowledge Gaps
- **322 isolated node(s):** `背景`, `决策`, `被拒 / 留口子`, `边界与互链`, `Job` (+317 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **87 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0001 范围限定英文 UI` and `gherkai agent SKILL.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `成功重试对 RunResult 透明（可观测性缺口）` and `上传成功后删本地`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `deterministic()` connect `deterministic.py` to `BackendStack`, `_run_step`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `gherkai-worker-novaact (README)` connect `@gherkai/worker-midscene (README)` to `Midscene Worker 开发笔记`, `deterministic.py`, `user_steps.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `_fixture()` connect `_fixture` to `RunState`, `test_workers.py`, `S3StepArgumentOffloader`, `test_lambda_asset.py`, `_Recorder`, `test_user_steps.py`, `test_lambda_handlers.py`, `_FakeSink`, `deterministic.py`, `test_evidence.py`, `gherkai_runtime/__init__.py`, `_RecUploader`, `test_interrupt_model.py`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 53 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 33 INFERRED edges - model-reasoned connections that need verification._