# Graph Report - yaozhou  (2026-10-31)

## Corpus Check
- 439 files · ~758,253 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8846 nodes · 18702 edges · 620 communities (305 shown, 315 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 956 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0eec3adb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- guard.mts
- main
- test_main.py
- stderr-outlets.test.mts
- test_cloud_reconcile.py
- test_provider.py
- test_schedule.py
- Status
- test_workers.py
- test_plan.py
- workers.py
- ScopeStarted
- Provider
- _run_step
- _explain_run
- model.py
- test_stack.py
- test_evidence.py
- test_deploy_cmd.py
- test_container.py
- JobResult
- materialize.py
- _SeqEcs
- _StubEcs
- resolve_or_create_project
- _FakeNovaActClient
- ADR-0008
- test_event_sink.py
- evidence.py
- ADR 0045: 文档分层与归位
- device_reprobe.md
- redact_secrets
- compose.py
- _RecUploader
- test_worker_variant.py
- query_capabilities
- FeatureSource
- test_tunnel_cli.py
- test_tunnel_warmup.py
- CONTRIBUTING.md: contributor 指南
- render.py
- build_engines
- cli.py
- test_user_steps.py
- ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）
- RunStore
- 云端后端用户文档
- test_lambda_asset.py
- SqliteEventLog
- ssm_path
- config.py
- build_fargate_engines
- test_user_docs.py
- _StampSsm
- video.py
- test_interrupt_model.py
- appium.mts
- parametrize
- BackendStack
- guard.test.mts
- _RoundsTable
- check_version_skew
- _engine
- LocalReportStore
- manifest.json
- evidence.mts
- test_artifact_upload.py
- scan
- _is_transient_network
- textui.py
- _Recorder
- test_tunnel.py
- _mk_state
- main
- 06-devicefarm-appium.mts
- gherkai 变更记录 (CHANGELOG)
- run_scope.py
- _FakeEcs
- JobState
- warmupSession
- select
- _ssm_params
- _StderrScan
- gherkai_runtime/names.py
- _FakeEcsClient
- test_cli_json_contract.py
- 决策
- _stop_fails
- README Video Specs
- TypeScript Build Config
- surface.mts
- APP_PRESIGN_EXPIRES_S
- Composition Root Architecture
- test_project_config.py
- test_adr_hygiene.py
- test_compose.py
- Video Material Files
- use_color
- validate_job_definition
- driven
- skill_install.py
- 决策
- Run Store Persistence Ports
- event-sink.mts
- toClassification
- 决策
- 决策
- interface.mts
- test_precheck.py
- dependencies
- test_lambda_handlers.py
- LocalRunStore
- Diagram Build Script
- ArtifactUploader
- test_engines_matrix.py
- evidence.test.mts
- ADR 0043：驱动 gherkai 的 agent skill
- release_notes.py
- app.mts
- test_argument.py
- Event Wallclock Analysis
- Release Notes Guards
- gherkai_cli/__main__.py
- test_skill.py
- test_technical_docs.py
- run-scope.test.mts
- Dist Metadata Checks
- patch-package 补丁 @cucumber+cucumber+13.0.0
- _doc_rules.py
- probe.mts
- Media Conversion Verification
- package.json
- finalize.test.mts
- FargateEngine
- _argv
- render_skill_contract.py
- DynamoDB Events Transport ADR
- Target
- 决策
- tunnel-warmup.test.mts
- minimax_narration.py
- test_skill_deploy_tokens.py
- read_project_arn
- Stateless Run Core Model
- SessionOpened
- argument.mts
- test_user_facing_messages.py
- image_tag
- session.test.mts
- 0050. 确定性 step 多句柄注册与测试分层
- test_capabilities.py
- arg_offload.py
- artifact-upload.test.mts
- ADR-0025
- _runs_stream_record
- engines-matrix.test.mts
- ADR 0041: 面向 agent 的 CLI 能力
- test_devicefarm.py
- ECS Task Timing Capture
- test_definition_schema.py
- Artifact Uploader Component
- deterministic.py
- Graphify Refresh Script
- uiautomator2.mts
- job-source.mts
- read-points.test.mts
- Cooperative Stop Design
- render_traffic_policy
- Doc Rules Check
- test_devicefarm_client_placement.py
- adapters.contract.test.mts
- console_url
- Engine Port & Job Planning
- Scope Tag Parsing
- S3 Key Mirrors Local Run Tree
- Context Glossary Guards
- ADR 0023: Nova Act acting 锁 Python
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions
- ._run_cdk
- session.mts
- DeviceSurface
- test_extract_missing_env_returns_none
- Echo Test Worker
- Cloud Infra Self-Check
- _ClientError
- devDependencies
- 移动真机支持（1.5）：实施进度总纲
- _stopped_detail
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- Gherkin Parse Seam
- files
- Repository Metadata
- test_subprocess_engine.py
- gherkai_worker_novaact/__init__.py
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试
- .on_event
- Architecture Diagrams
- Slide Frame SSIM Checks
- gherkai_deploy_aws/names.py
- AgentCore CDP Script
- test_plan_config_defaults_derive_from_builtin_acquire_budget
- test_plan_select_keeps_target_and_target_based_timeout
- Pre-commit Hook Script
- offlineSelfCheck
- Job
- Adapters Package
- user-steps.test.mts
- test_tunnel_host.py
- .acquireSteps
- Step Matching & Plan Annotation
- cloud_env
- agentcore-sigv4.test.mts
- no-device-deps.test.mts
- test_build_reuses_its_own_handles_and_builds_no_new_client
- 执行与推进模型导览（run/submit × local/cloud）
- test_build_clamps_meta_max_concurrency_to_cap
- precheck.mts
- gemini_image.py
- Index Wait Script
- gherkai Workspace Root
- test_lifecycle_states.py
- error-text.mts
- test_fargate_engine.py
- Execution Backend
- Feature Files
- Error Type Classification
- Local Per-Run Advance Process
- sessionEventSink
- gherkai Core Package
- AWS Deploy Package
- Runtime Package
- NovaAct Worker Package
- session-name.mts
- event-sink.test.mts
- job-source.test.mts
- CONTENT_TYPES
- _Worker
- bin.mts
- _World
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- test_build_defaults_to_one_when_meta_missing
- stopTimeout=120 / grace 预算校准
- _build_parser
- xcuitest.mts
- test_build_reads_session_warmup_url_back_into_worker_env
- 项目约定
- test_stderr_redaction.py
- ADR 0014: AI 优先断言
- wire.py
- warmup.mts
- test_build_without_tunnel_injects_no_warmup_env
- e2e_harness.py
- appium.test.mts
- _role_statements
- runScope
- test_reconcile.py
- register
- _advancer_stmts
- device_reprobe 使用说明（Midscene 设备模块的真机重新探测）
- DeviceFarmSessionBlock
- redact.test.mts
- ensure_app_object
- reconcile.tick（推进器共享入口）
- _error_text
- NgrokTunnel
- AST
- probe.test.mts
- web-context.mts
- test_job_source.py
- _Page
- _FakeSink
- .doRelease
- NamedTuple
- _seed_worker_ssm
- severity 数值序（_STATUS_SEVERITY）
- parametrize
- .constructor
- .navigate
- scan
- app.test.mts
- warmup.test.mts
- TargetSurface
- _fixture
- finalize.mts
- _out
- ADR 0024: worker–core 协议
- ContainerError
- Budget
- device/surface.test.mts
- WebdriverCtx
- openai
- DeterministicCtx
- Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障
- reconciler.py
- AppiumInterface
- DeterministicKeywordMismatch
- web-context.test.mts
- ._pump
- wdio-log.mts
- wdio-log.test.mts
- start_tunnel_for_jobs
- WebdriverApp
- .waitRunning
- .execute
- .actionSpace
- _events_table_actions
- precheck.test.mts
- _DeterministicCtx
- map_origin_in_jobs
- runOnDevice
- runStep
- Fargate/ECS RunTask 执行后端
- deviceFarmApi
- _FakeS3
- ArtifactUploader
- _make_devicefarm_client
- test_finished_run_gate_keys_on_the_committed_run_status_only
- _joined_refs
- desktopFactory
- ArtifactUploader
- diffAgainstFixture
- ReportRef
- Scenario
- Step
- @playwright/test
- StepArgument
- worker/surface.test.mts
- stop_tunnel
- Target
- scripts
- _spawn_and_wait_ready
- DEVICE_SESSION_FILE
- limits.test.mts
- DEVICE_SESSION_REPORT_KIND
- verify_project
- DeviceSessionRecord
- @aws-sdk/client-s3
- @aws-sdk/credential-providers
- @aws-sdk/protocol-http
- ADR-0051
- ADR-0052
- ProviderMinutes
- ScaleSource
- SessionClosedFact
- SessionDeviceInfo
- SessionOpenedFact
- playwright
- tsx
- AdapterEntry
- SessionOrigin
- session-name.test.mts
- SessionRelease
- WebContextRecord
- ADDRESS_PATTERN
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0050
- BaseException
- Exception
- list
- fixtureFor
- _stub_get_not_found
- _all_option_dests
- no-artifacts.test.mts
- ScopeTerminationError
- finishCase
- ADR-0019
- ADR-0026
- ADR-0032
- BUSY_BACKOFF_CAP_MS
- BUSY_BACKOFF_INITIAL_MS
- CONTROLS_MAX_ITEMS
- DEEP_LINK_FOREGROUND_POLL_ATTEMPTS
- DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS
- DELETE_SESSION_TIMEOUT_MS
- DEVICE_FARM_CALL_TIMEOUT_MS
- DEVICE_RELIST_DELAY_MS
- DEVICE_REPLANNING_CYCLE_LIMIT
- DEVICE_WARMUP_ATTEMPTS
- EXEC_REQUEST_TIMEOUT_MS
- FARGATE_STOP_TIMEOUT_CAP_S
- FINALIZE_AWAIT_CREATE_MS
- FINALIZE_GET_TIMEOUT_MS
- FINALIZE_RECONCILE_MS
- FINALIZE_RELEASE_MS
- LAUNCH_SAMPLE_COUNT
- LAUNCH_SAMPLE_INTERVAL_MS
- MAX_SESSION_S
- ADR-0044
- ADR-0048
- devicefarm.py
- ADR-0049
- _CdkWritingContext
- ADR-0051
- ADR-0052
- NEW_COMMAND_TIMEOUT_S
- NEW_SESSION_TIMEOUT_FLOOR_MS
- PAGE_LOAD_TIMEOUT_MS
- PAGE_SOURCE_MAX_BYTES
- PROBE_TIMEOUT_MS
- 输出契约：流式 JSON Lines 事件流
- REPLACE_DEVICE_MIN_REMAINING_MS
- REPLANNING_LIMIT_ENV
- SESSION_CAP_S
- SharedShutdownTailMs
- SNAPSHOT_CAPTURE_BUDGET_MS
- STOP_CALL_TIMEOUT_MS
- WEB_CONTEXT_RELIST_DELAY_MS
- EventBridgeTimeoutWatch
- test_tick_runs_isolates_defensive_scan_failure
- Timers
- recordingSurface
- _capabilities
- fakeUploader
- StepClassification
- ADR-0020
- ADR-0027
- ADR-0028
- ADR-0048
- RFC-3986
- AcquireResult
- AddressReading
- CLASSIFICATION_KEY
- ControlItem
- Controls
- ControlsMissing
- DeviceSurfaceModule
- HandlerCall
- ADR-0039
- ADR-0042
- ADR-0044
- ADR-0050
- DEFAULT_MODEL
- MODEL
- MODEL_FAMILY_PATTERNS
- ADR-0033
- ADR-0037
- ADR-0044
- ADR-0016
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0032
- ADR-0033
- ADR-0042
- ADR-0051
- UPLOAD_TIMEOUT_MS
- CHECK_PATH
- COOKIE_NAME
- EXTRA_HTTP_HEADERS_ENV
- INCOMPLETE_DEFINITION_MESSAGE
- ADR-0028
- ADR-0039
- ADR-0051
- SESSION_WARMUP_KEY
- SESSION_WARMUP_URL_ENV
- TERMINAL_TITLES
- TOKEN_PARAM
- WARMUP_ATTEMPTS
- WARMUP_AUTH_REQUIRED_MESSAGE
- WARMUP_DENIED_MESSAGE
- WARMUP_MARKER_WAIT_MS
- WARMUP_MARKERS
- WARMUP_NAV_TIMEOUT_MS
- WARMUP_PATH
- WARMUP_TITLES
- WarmupDeps
- WarmupFailure
- BUILTIN_KINDS
- BuiltinKind
- DeterministicAssertion
- DeterministicConflict
- DeterministicHandler
- DeterministicHandlers
- DeterministicMeta
- Device
- DEVICES
- Entry
- ENTRY_FIELDS
- EntryHandles
- HANDLER_KINDS
- Keyword
- KEYWORDS
- MatchItem
- MatchProbe
- ADR-0020
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0048
- ADR-0049
- ADR-0050
- ADR-0052
- NormalizedWebdriverEntry
- PLAYWRIGHT_TARGET
- REGISTRY
- RegistryEntry
- Requirement
- REQUIREMENTS
- SelectedHandler
- DeviceNavigate
- ADR-0020
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0048
- ADR-0050
- ADR-0052
- RFC-3986
- WEB_SCHEMES
- StepTarget
- StepTargetKey
- TARGET_DEVICE_ORDER
- UI_KINDS
- UiKind
- WebdriverDevice
- WebdriverEntry
- WebdriverHandler
- Dispatch
- FailureExitDeps
- Job
- MIN_GRACE_MARGIN_MS
- ADR-0014
- ADR-0020
- ADR-0022
- ADR-0024
- ADR-0027
- ADR-0028
- ADR-0029
- ADR-0031
- ADR-0035
- ADR-0036
- ADR-0037
- ADR-0039
- ADR-0042
- ADR-0044
- ADR-0049
- ADR-0050
- ADR-0051
- ADR-0052
- QUEUE_DRAIN_EXIT_MS
- Scenario
- ScopeIo
- ScopeSeam
- ShutdownDeps
- Step
- WORKER_TARGETS
- ADR-0051
- ADR-0052
- ReleaseMode
- ReleaseOutcome
- ReportRef
- ScopeErrorType
- ScopeTermination
- Snapshot
- SnapshotResult
- STEP_ERROR_TYPES
- StepErrorType
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- BROWSER_CLOSE_BUDGET_MS
- CONNECT_BACKOFF_MS
- connectRetriesExhausted
- DesktopAgentOpts
- DesktopSurfaceHooks
- INFLIGHT_SETTLE_MS
- ADR-0020
- ADR-0024
- ADR-0028
- ADR-0035
- ADR-0037
- ADR-0051
- ADR-0052
- STOP_SESSION_BUDGET_MS
- LoadUserStepsDeps
- ADR-0016
- ADR-0028
- ADR-0036
- ADR-0037
- ADR-0051
- STEP_EXTS
- StepFacts
- StepKind
- StepStatus
- SurfaceDeps
- SurfaceFactory
- TentativeVerdict
- UrlMissing
- _WarmupFailureIsScopeTermination

## God Nodes (most connected - your core abstractions)
1. `main()` - 277 edges
2. `Job` - 175 edges
3. `RunMeta` - 143 edges
4. `RunState` - 132 edges
5. `Status` - 114 edges
6. `JobResult` - 109 edges
7. `Provider` - 109 edges
8. `JobState` - 106 edges
9. `Scenario` - 99 edges
10. `Step` - 98 edges

## Surprising Connections (you probably didn't know these)
- `--interrupt 中断时机矩阵` --shares_data_with--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `test_skill.py（skill 产品面与真值护栏）` --references--> `render()`  [EXTRACTED]
  docs/adr/0043-agent-skill-for-driving-gherkai.md → tools/render_skill_contract.py
- `ADR 0043：驱动 gherkai 的 agent skill` --references--> `render()`  [EXTRACTED]
  docs/adr/0043-agent-skill-for-driving-gherkai.md → tools/render_skill_contract.py
- `render()` --references--> `docs/internals/cli-json-contract.md（机读字段级参考页）`  [EXTRACTED]
  tools/render_skill_contract.py → docs/adr/0045-documentation-layering-and-placement.md
- `e2e_harness.py（opt-in 手动端到端验证脚本）` --calls--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **archify 图源到发布的三段流程** — docs_adr_0045_documentation_layering_and_placement_diagram_pipeline, docs_ai_eng_diagram_authoring_task, tools_build_diagrams_build, docs_diagrams_index_page, docs_diagrams_run_execution_diagram [EXTRACTED 0.80]
- **一次失败的三步读法：status → explain → 原生产物** — docs_internals_artifacts_and_evidence, docs_internals_artifacts_and_evidence_verdict_truth, docs_internals_verdict_model, docs_internals_cli_json_contract [EXTRACTED 0.80]
- **演示媒体制作流水线（生图→配音→成片）** — tools_presentations_gemini_image, tools_presentations_minimax_narration, tools_presentations_video, tools_presentations_production [EXTRACTED 0.80]
- **预检到结果的运行流程** — readme_plan, readme_run, readme_submit, readme_status, readme_explain [EXTRACTED 0.80]
- **断言两层 + 抖动/漏检边界** — docs_adr_0015_v1_positioning_smoke_not_regression_default_ai_assertion, docs_adr_0015_v1_positioning_smoke_not_regression_deterministic_step, docs_adr_0015_v1_positioning_smoke_not_regression_named_check, docs_adr_0015_v1_positioning_smoke_not_regression_judgment_flakiness, docs_adr_0015_v1_positioning_smoke_not_regression_flexible_miss [EXTRACTED 0.85]
- **cloud backend 命名/定位契约链（prefix→SSM→preflight→container 名→组合根）** — docs_adr_0033_iac_aws_backend_and_composition_wiring_two_layer_naming, docs_adr_0033_iac_aws_backend_and_composition_wiring_ssm_subnet_sg, docs_adr_0033_iac_aws_backend_and_composition_wiring_preflight, docs_adr_0033_iac_aws_backend_and_composition_wiring_container_name_contract, docs_adr_0033_iac_aws_backend_and_composition_wiring_compose_fargate [EXTRACTED 0.85]
- **contributor 护栏三层共用同一规则源** — cli_tests_doc_rules_rules, tools_doc_rules_check_check, cli_tests_test_user_docs_tests, cli_tests_test_skill_tests, docs_adr_0046_guardrail_layers_tests_hooks_and_lean_claude_md_adr [EXTRACTED 0.85]
- **跨引擎边界：features/ 共享 + 公共设施落核心库** — docs_adr_0013_cross_engine_sharing_boundary, docs_adr_0013_shared_features_boundary, docs_adr_0013_core_library_shared_infrastructure, docs_adr_0023_novaact_acting_python_locked_no_ts_core, docs_adr_0016_execution_architecture_core_lib_run_model [EXTRACTED 0.85]
- **文档与文案纪律的三层护栏及其规则源** — claude_project_conventions, contributing_guide, context_glossary, context_guardrail [EXTRACTED 0.85]
- **Fargate 中断韧性方案组（丢失风险→安全点上传→grace 预算→reaper 否决）** — docs_adr_0032_fargate_execution_environment_interrupt_loss, docs_adr_0032_fargate_execution_environment_safepoint_upload, docs_adr_0032_fargate_execution_environment_stop_timeout, docs_adr_0032_fargate_execution_environment_act_timeout_decision, docs_adr_0032_fargate_execution_environment_orphan_reaper_rejected [EXTRACTED 0.85]
- **Four-Level Artifact Upload Timing Flow** — docs_adr_0029_engine_artifacts_to_s3_upload_timing, docs_adr_0029_engine_artifacts_to_s3_to_report_ref, docs_adr_0029_engine_artifacts_to_s3_flush_and_cleanup, docs_adr_0029_engine_artifacts_to_s3_act_boundary_presend, docs_adr_0029_engine_artifacts_to_s3_scenario_boundary_presend, docs_adr_0029_engine_artifacts_to_s3_residual_artifacts [EXTRACTED 0.85]
- **Midscene 引擎模型选定链（GPT-5.5 出局 → Qwen3-VL → GPT-5.6 Terra）** — docs_adr_0002_midscene_not_driven_by_gpt55, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0044_engine_model_selection_and_override, docs_adr_0002_midscene_not_driven_by_gpt55_chat_completions_requirement [EXTRACTED 0.85]
- **判定由谁做出：底层模型披露** — readme_midscene_engine, readme_nova_act_engine, changelog_midscene_default_model, changelog_nova_model_pinning, readme_doctor [EXTRACTED 0.85]
- **窄腰协议的依赖面（plan / schedule / worker / RunReport 全靠 0024 契约）** — docs_adr_0024_worker_core_protocol, docs_adr_0025_plan_module_feature_to_jobs, docs_adr_0026_schedule_module, docs_adr_0027_runreport_aggregation_index, docs_adr_0022_thin_worker [EXTRACTED 0.85]
- **Planning 兼任决策的约束链（Midscene 必附图 × Bedrock 纯文本拒图 × AWS 硬约束）** — docs_adr_0012_planning_shares_qwen3vl_no_text_planner, docs_adr_0012_disjoint_model_sets, docs_adr_0012_planning_role, docs_adr_0009_maximize_aws_hard_constraint, docs_adr_0044_engine_model_selection_and_override [EXTRACTED 0.85]
- **Run 数据三层切分与单向数据流** — docs_adr_0016_execution_architecture_core_lib_run_model_three_layer_split, docs_adr_0016_execution_architecture_core_lib_run_model_run_meta, docs_adr_0016_execution_architecture_core_lib_run_model_run_state, docs_adr_0016_execution_architecture_core_lib_run_model_job_result, docs_adr_0016_execution_architecture_core_lib_run_model_run_result, docs_adr_0016_execution_architecture_core_lib_run_model_run_persistence [EXTRACTED 0.85]
- **worker 定位链与非 job 自述入口** — runtime_gherkai_runtime_compose_resolve_worker_cmd, runtime_gherkai_runtime_compose_ask_worker, runtime_gherkai_runtime_compose_query_capabilities, runtime_gherkai_runtime_compose_match_deterministic, engines_novaact_gherkai_worker_novaact_run_scope_main [EXTRACTED 0.85]
- **worker I/O 边缘可注入接口（subprocess + Fargate 两态）** — docs_adr_0024_worker_core_protocol_job_source, docs_adr_0024_worker_core_protocol_event_sink, docs_adr_0024_worker_core_protocol_engine_port, docs_adr_0024_worker_core_protocol_pipe_transport_retired, docs_adr_0024_worker_core_protocol_fargate_engine_adapter [EXTRACTED 0.85]
- **AI 断言为主 + 抖动治理纪律（投票/配置/确定性补充）** — docs_adr_0014_ai_first_assertions, docs_adr_0014_ai_assertion_voting, docs_adr_0014_assertion_votes, docs_adr_0014_deterministic_step [EXTRACTED 0.90]
- **产物落点→不透明 ref→归集索引→导航链接的闭环** — docs_adr_0029_engine_artifacts_to_s3_injection_driven_upload, docs_adr_0029_engine_artifacts_to_s3_worker_uploads, docs_adr_0027_runreport_aggregation_index_reportref, docs_adr_0027_runreport_aggregation_index_opaque_rule, docs_adr_0027_runreport_aggregation_index_reportstore, docs_adr_0027_runreport_aggregation_index_make_href [EXTRACTED 0.90]
- **云端后台运行的事件级联与两道 detached 拦截** — docs_internals_execution_and_reconciliation_kicker, docs_internals_execution_and_reconciliation_reconciler, docs_internals_execution_and_reconciliation_exit_observer, docs_internals_execution_and_reconciliation_detached_flag, docs_internals_execution_and_reconciliation_events_keyspace [EXTRACTED 0.90]
- **Commit-Point Realtime Persistence Flow** — docs_adr_0030_realtime_persistence_seam_run_persistence, docs_adr_0030_realtime_persistence_seam_create_run, docs_adr_0030_realtime_persistence_seam_save_job_result, docs_adr_0030_realtime_persistence_seam_update_job_state, docs_adr_0030_realtime_persistence_seam_finalize_run, docs_adr_0030_realtime_persistence_seam_report_store_write_isolation [EXTRACTED 0.90]
- **按读者分层的四个文档入口** — docs_readme, docs_user_guide_readme, docs_internals_readme, contributing, claude, docs_adr_0045_documentation_layering_and_placement [EXTRACTED 0.90]
- **events-out 传输三方案选型收敛** — docs_adr_0024_worker_core_protocol_ddb_events_table, docs_adr_0024_worker_core_protocol_rejected_sqs_fifo, docs_adr_0024_worker_core_protocol_rejected_msk, docs_adr_0024_worker_core_protocol_rejected_ddb_streams [EXTRACTED 0.90]
- **Gherkin tag 配置体系（scope/engine/timeout 同构三件套）** — docs_adr_0019_scope_tag, docs_adr_0019_engine_tag, docs_adr_0019_timeout_tag, docs_adr_0025_plan_module_feature_to_jobs [EXTRACTED 0.90]
- **docs/internals 主题归属表：七篇各拥有一个机制** — docs_internals_readme, docs_internals_architecture_overview, docs_internals_execution_and_reconciliation, docs_internals_verdict_model, docs_internals_artifacts_and_evidence, docs_internals_deterministic_step_lifecycle, docs_internals_cloud_backend_carriers, docs_internals_cli_json_contract [EXTRACTED 0.90]
- **job 判定状态模型扩展（派生态+前置态+severity+过滤+终态集）** — docs_adr_0031_job_lifecycle_states_and_severity_status_skipped, docs_adr_0031_job_lifecycle_states_and_severity_status_aborted, docs_adr_0031_job_lifecycle_states_and_severity_status_pending_running, docs_adr_0031_job_lifecycle_states_and_severity_severity_order, docs_adr_0031_job_lifecycle_states_and_severity_non_verdict, docs_adr_0031_job_lifecycle_states_and_severity_terminal_statuses [EXTRACTED 0.90]
- **网络瞬时故障的分类→退出码→异常→job 重试链路** — docs_adr_0028_transient_network_ssl_resilience_is_transient_network, docs_adr_0028_transient_network_ssl_resilience_network_error, docs_adr_0028_transient_network_ssl_resilience_ex_worker_network, docs_adr_0028_transient_network_ssl_resilience_raise_for_worker_exit, docs_adr_0028_transient_network_ssl_resilience_workernetworkerror, docs_adr_0026_schedule_module_network_retry [EXTRACTED 0.90]
- **核心注入接口（ports）+ 组合根注入装配** — docs_adr_0016_execution_architecture_core_lib_run_model_engine_port, docs_adr_0016_execution_architecture_core_lib_run_model_run_store, docs_adr_0016_execution_architecture_core_lib_run_model_result_store, docs_adr_0016_execution_architecture_core_lib_run_model_report_store, docs_adr_0016_execution_architecture_core_lib_run_model_composition_root, docs_adr_0016_execution_architecture_core_lib_run_model_injection_redline [EXTRACTED 0.90]
- **推一个 git tag 的发布链与其发布闸门** — github_workflows_release_release, readme_gherkai, github_release_body_footer_footer, github_workflows_readme_ci_release_guide, context_single_version_source [EXTRACTED 0.90]
- **schedule 对同一事件流的三级归约（status + 成本 + 墙钟）** — docs_adr_0026_schedule_module_schedule, docs_adr_0026_schedule_module_status_reduction, docs_adr_0026_schedule_module_cost_reduction, docs_adr_0026_schedule_module_duration_reduction, docs_adr_0026_schedule_module_scope_done_gate, docs_adr_0026_schedule_module_step_skipped_reduction [EXTRACTED 0.90]
- **Diagrams sharing the bundled-font and viewer preset rendering contract** — docs_diagrams_artifacts_evidence_chain, docs_diagrams_cloud_backend_carriers_revision_pinning, docs_diagrams_cloud_backend_upgrade_windows, docs_diagrams_cloud_delivery_identity, docs_diagrams_configuration_env_inheritance, docs_diagrams_deterministic_steps_registry_overview, docs_diagrams_deterministic_steps_truth_sources, docs_diagrams_execution_cloud_cascade, docs_diagrams_execution_detached_gates, docs_diagrams_execution_timeout_chain, docs_diagrams_getting_started_component_ownership, docs_diagrams_jetbrains_mono_bundled_font, docs_diagrams_archify_diagram_viewer [EXTRACTED 0.90]
- **skill 评测一轮的资产与流程** — skills_gherkai_evals_materialize_materialize, skills_gherkai_evals_run_evals_run_evals, skills_gherkai_evals_summarize_runs_summarize_runs, skills_gherkai_evals_grader_prompt_grader_prompt, skills_gherkai_evals_evals_dataset [EXTRACTED 0.90]
- **一个 step 的三种执行路径** — readme_ai_step, readme_deterministic_step, readme_navigation_step, readme_gherkin_feature [EXTRACTED 0.90]
- **三层终止契约（逻辑层/机制层/worker 层）** — docs_adr_0024_worker_core_protocol_termination_contract, docs_adr_0024_worker_core_protocol_schedule_stop_request, docs_adr_0024_worker_core_protocol_worker_handle_stop, docs_adr_0024_worker_core_protocol_nova_worker_flag_only, docs_adr_0024_worker_core_protocol_midscene_worker_cleanup [EXTRACTED 0.90]
- **两引擎统一 IAM/SigV4 鉴权（无 bearer key）** — docs_adr_0004_novaact_iam_auth_via_workflow, docs_adr_0008_midscene_bedrock_auth_sigv4_selfsign, docs_adr_0008_create_openai_client, docs_adr_0009_maximize_aws_hard_constraint [EXTRACTED 0.90]
- **Symmetric Uploader Contract Across Two Engines** — docs_adr_0029_engine_artifacts_to_s3_artifact_uploader, docs_adr_0029_engine_artifacts_to_s3_from_env, docs_adr_0029_engine_artifacts_to_s3_to_report_ref, docs_adr_0029_engine_artifacts_to_s3_flush_and_cleanup, docs_adr_0029_engine_artifacts_to_s3_snapshot_report, docs_adr_0029_engine_artifacts_to_s3_snapshot_logs [EXTRACTED 0.90]
- **worker step 派发优先级链（确定性注册表 → URL 导航 → AI catch-all）** — docs_adr_0022_deterministic_registry, docs_adr_0020_url_auto_routing, docs_adr_0020_default_ai_step, docs_adr_0022_thin_worker [EXTRACTED 0.90]
- **「uv run pytest 永不连真 AWS」三重保险** — pyproject_addopts, core_tests_conftest_real_aws, core_tests_conftest_fake_aws_creds, core_tests_test_cloud_integration [EXTRACTED 0.95]
- **detached run 推进的三个触发源（都幂等、并发安全）** — docs_adr_0034_detached_batch_reconciler_kicker_lambda, docs_adr_0034_detached_batch_reconciler_status_relay, docs_adr_0034_detached_batch_reconciler_tick, docs_adr_0034_detached_batch_reconciler_exit_observer [EXTRACTED 0.95]
- **随命令行发行的 agent skill 及其五份参考** — cli_gherkai_cli_skills_gherkai_skill, cli_gherkai_cli_skills_gherkai_references_cli_json_contract, cli_gherkai_cli_skills_gherkai_references_engines, cli_gherkai_cli_skills_gherkai_references_deterministic_steps, cli_gherkai_cli_skills_gherkai_references_setup_and_diagnosis, cli_gherkai_cli_skills_gherkai_references_cloud_backend [EXTRACTED 0.95]
- **无状态 reconciler 的四个关键机制** — docs_adr_0034_detached_batch_reconciler_task_exited_keyspace, docs_adr_0034_detached_batch_reconciler_exit_observer, docs_adr_0034_detached_batch_reconciler_hwm_conditional_write, docs_adr_0034_detached_batch_reconciler_cas_concurrency [EXTRACTED 0.95]
- **Cloud backend and delivery diagram family** — docs_diagrams_cloud_backend_carriers_revision_pinning, docs_diagrams_cloud_backend_upgrade_windows, docs_diagrams_cloud_delivery_identity [INFERRED 0.70]
- **云端一次改动的传播：载体 → 镜像真值源 → 证据落点** — docs_internals_cloud_backend_carriers, docs_internals_cloud_backend_carriers_revision_pinning, docs_internals_deterministic_step_lifecycle_registry, docs_internals_artifacts_and_evidence_evidence_deref [INFERRED 0.70]
- **Execution runtime behaviour diagram family** — docs_diagrams_execution_cloud_cascade, docs_diagrams_execution_detached_gates, docs_diagrams_execution_timeout_chain [INFERRED 0.70]
- **agent 驾驭面：机读输出 + 证据 + 教材 + 文案纪律** — docs_adr_0041_agent_facing_cli_affordances_json_contract, docs_adr_0042_step_evidence_and_explain_explain, docs_adr_0043_agent_skill_for_driving_gherkai_derived_copy, docs_adr_0039_user_facing_surfaces_no_internal_references_message_guardrail [INFERRED 0.80]

## Communities (620 total, 315 thin omitted)

### Community 0 - "guard.mts"
Cohesion: 0.06
Nodes (43): AFTER_RESULT_UNKNOWN_MESSAGE, commandFailedMessage(), CommandGuardArgs, commandGuardFactory, CONNECTION_ERROR_CODES, CONTEXT_SWITCH_COMMANDS, copyOutcome(), Derivation (+35 more)

### Community 1 - "main"
Cohesion: 0.03
Nodes (143): main(), _definition(), _fake_schedule_factory(), _patch_cloud_handles(), _patch_skew(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, status 不解析 variant（ADR 0038）：它只读运行态、不起 task，definition 里的 revision 提交时已定死。 (+135 more)

### Community 2 - "test_main.py"
Cohesion: 0.02
Nodes (210): _capturing_schedule(), _cloud_backend_ok(), _det_feature(), _doctor_cloud_json(), _doctor_devices_cloud(), _fake_locator(), _fake_worker_cmd(), _miss() (+202 more)

### Community 3 - "stderr-outlets.test.mts"
Cohesion: 0.06
Nodes (65): ADR-0035, ADR-0051, ALIAS_ASSIGNMENTS, Bindings, bindingsOf(), CONSOLE_STDERR, DECLARATION_KINDS, describe() (+57 more)

### Community 4 - "test_cloud_reconcile.py"
Cohesion: 0.05
Nodes (56): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog (+48 more)

### Community 5 - "test_provider.py"
Cohesion: 0.04
Nodes (77): _app_context_keys(), _ctx(), _parse(), Path, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装（含闭集护栏）、生成的 cdk.json、cdk 调用、VPC…, 用了 --profile 时，查项目 ARN 的命令带同一个 --profile（与 doctor 的停止命令同一做法），照抄不会落到另一套凭证。, 走**真 parser**、按真实接线顺序拼（前端先声明命令面 flag，provider 再贴自己的选项）——不用 SimpleNamespace 手捏…, 「完全没有凭证」的判据走 boto3 真实的凭证链（不调用 AWS 服务的 API；实例元数据端点的请求由 AWS_EC2_METADATA_DISABLED… (+69 more)

### Community 6 - "test_schedule.py"
Cohesion: 0.10
Nodes (98): 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。, EngineResolver：所有引擎都返回同一个 FakeEngine（测试不区分引擎）。 (+90 more)

### Community 7 - "Status"
Cohesion: 0.03
Nodes (146): test_format_event_renders_session_events_without_endpoints(), SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, _job_state_from_item(), commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, 状态机单调条件写：仅当总 status 是 pending 或 running 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。…, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。…, 判定状态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire… (+138 more)

### Community 8 - "test_workers.py"
Cohesion: 0.07
Nodes (77): aws(), _cleanup(), FakeContainer, _mapping(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 一次干净的推送：tag/push 到 ECR ref → 从模板注册 revision（镜像按 digest、血缘 tags 齐）→ 写 SSM 映射。 (+69 more)

### Community 9 - "test_plan.py"
Cohesion: 0.08
Nodes (47): _cfg(), _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 低于下限的改法要按删掉 tag 后真正接替的来源给：--default-job-timeout 也低于下限时不能只说「删 tag 走缺省」（删了仍被它拒）。, 「任一成员标了即整个 scope 生效」不只看首个成员：带 tag 的成员排在后面也生效。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否… (+39 more)

### Community 10 - "workers.py"
Cohesion: 0.05
Nodes (84): cleanup_pass(), CleanupOutcome, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable(), _hours() (+76 more)

### Community 11 - "ScopeStarted"
Cohesion: 0.06
Nodes (73): scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, ScenarioDone, ScenarioStarted, ScopeDone, ScopeStarted, StepDone, StepSkipped, StepStarted (+65 more)

### Community 12 - "Provider"
Cohesion: 0.05
Nodes (42): _has_aws_credentials(), _make_cfn_client(), _make_ssm_client(), Provider, ArgumentParser, SSM 记录不是合法的项目 ARN 时报错并返回退出码 2，合法返回 None。 这种值只会因手工改动出现（stack…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 解析链的诊断归口：解析得出 → target；失败 → 打一句诊断、返 None（调用点归退出码）。 **每个动作在碰 AWS 之前都要经这一口**：不存在的… (+34 more)

### Community 13 - "_run_step"
Cohesion: 0.06
Nodes (64): _classify_act_error(), 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, 派发执行一个 step，发出 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, _run_scenario(), _run_step(), _ActBoom, _done() (+56 more)

### Community 14 - "_explain_run"
Cohesion: 0.10
Nodes (31): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+23 more)

### Community 15 - "model.py"
Cohesion: 0.04
Nodes (107): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR…, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, 一个 job 开过或尝试过的一个会话（设备是远程访问会话，桌面是 AgentCore 浏览器会话；ADR 0051 决策 4、7）： 由…, 是否已确认停止；attempted 的尝试永远不会被确认（ADR 0034 机制二未确认集 U 的成员判据）。, 从 RunResult 投影出控制面运行态（ADR 0016/0027）。… (+99 more)

### Community 16 - "test_stack.py"
Cohesion: 0.07
Nodes (52): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler / kicker）的角色都不读 SSM 参数：definition 缺 `worker_task_defs` 按定义违约标… (+44 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.08
Nodes (50): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), parametrize, Path (+42 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.05
Nodes (64): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+56 more)

### Community 19 - "test_container.py"
Cohesion: 0.06
Nodes (45): digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。 (+37 more)

### Community 20 - "JobResult"
Cohesion: 0.04
Nodes (87): _device_keys_for_explain(), explain_to_dict(), RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, explain 的人与 agent 可读文本（`explain_to_dict` 的文档渲染为树形摘要，节点文字依 ADR 0042…, 机读文档里 sessions[] 一项的 dict → 具 session_id / device 属性的视图（让 representative_device…, render_explain_text(), render_text() (+79 more)

### Community 21 - "materialize.py"
Cohesion: 0.08
Nodes (53): gherkai agent skill 包, evals.json（评测集与 fixture 索引）, 评分子代理提示词模板, assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture() (+45 more)

### Community 22 - "_SeqEcs"
Cohesion: 0.22
Nodes (5): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

### Community 23 - "_StubEcs"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 24 - "resolve_or_create_project"
Cohesion: 0.18
Nodes (22): project_name(), ProjectResolution, 找回或建立项目 `{prefix}devices`（只供 `deploy` 在 cdk 之前调用，ADR 0051 决策 10「项目」）。…, `resolve_or_create_project` 的结果。`source` 说明 ARN 从哪来：`ssm` 沿用 SSM 里核对过的值，`found`…, 云端 Device Farm 项目名 `{prefix}devices`。, resolve_or_create_project(), _assert_warning(), _enter() (+14 more)

### Community 25 - "_FakeNovaActClient"
Cohesion: 0.09
Nodes (28): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, _fmt_seconds() (+20 more)

### Community 27 - "test_event_sink.py"
Cohesion: 0.05
Nodes (32): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与…, 三条规则依次作用于一段文本；None 原样返回。, redact_secrets() (+24 more)

### Community 28 - "evidence.py"
Cohesion: 0.08
Nodes (39): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Any, Path (+31 more)

### Community 29 - "ADR 0045: 文档分层与归位"
Cohesion: 0.20
Nodes (21): _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏）, test_user_docs.py（用户文档与图源护栏）, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0045: 文档分层与归位, CONTEXT.md 严格词表与术语变更顺序（决策八）, archify 图流程（JSON 图源 + 导出 SVG 入库） (+13 more)

### Community 30 - "device_reprobe.md"
Cohesion: 0.08
Nodes (26): Attempt, Browser, CALL_ORDER, Captured, CaseResult, CaseStatus, ContractCase, ContractFixture (+18 more)

### Community 31 - "redact_secrets"
Cohesion: 0.14
Nodes (18): Any, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则、三份同文实现。 三份同文实现（本文件、Nova worker…, 三条规则依次作用于一段文本；None 原样返回。 `https://u:p@host/x` →…, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_secrets(), parametrize, 凭据脱敏三条规则的单测（ADR 0035 决策 5；0051 决策 11）。 用例表只有一份：`engines/fixtures/redaction-… (+10 more)

### Community 32 - "compose.py"
Cohesion: 0.03
Nodes (68): _ask_worker(), available_targets(), cloud_artifact_locations(), _default_targets(), _is_finite_number(), is_pure_release(), local_artifact_locations(), _make_lambda_client() (+60 more)

### Community 33 - "_RecUploader"
Cohesion: 0.05
Nodes (28): _drain_evidence_uploads(), 收尾：**有界**等 evidence 截图的后台队列传完（ADR 0042 决策一）。best-effort、绝不抛。…, _FakeBrowserClient, _FakeCm, _FakeNovaAct, _install_browser_client(), main_fakes(), _RaisingSink (+20 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.08
Nodes (44): ecr_repo_name(), 引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag…, （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…, task_def_name(), worker_image_key(), test_task_def_and_container_name(), test_ecr_repo_name_is_task_def_name() (+36 more)

### Community 35 - "query_capabilities"
Cohesion: 0.06
Nodes (44): engine_min_grace(), match_deterministic(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, 批量问某引擎 worker「这些 step 各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 items 每项…, _caps_json(), _fake_caps_proc() (+36 more)

### Community 36 - "FeatureSource"
Cohesion: 0.12
Nodes (35): FeatureContractError, 用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig, Job (+27 more)

### Community 37 - "test_tunnel_cli.py"
Cohesion: 0.08
Nodes (47): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, 不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。, 隧道起不来（如 authtoken 缺失）→ 给退出码 2「没开始执行就被拒」，不产生引擎费用。, local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。 (+39 more)

### Community 38 - "test_tunnel_warmup.py"
Cohesion: 0.04
Nodes (54): _clock(), _FakePage, 隧道会话预热（ADR 0051 决策 13；ADR 0035「边界与不变量」）——Nova worker 侧。 纯逻辑部分（三种可见结果的归因、有界重试）用假…, 两种拒绝都是 precheck_failed、不重试，但各给自己的一句：令牌被拒与会话 cookie 未通过校验的处置不同。, 导航抛网络类异常：不向上抛（外层的建连重试域看不到它、不会以退出码 80 收场），有界重试后归 engine_error。, 停止信号（ADR 0024 flag-only）：预热的退避与等标记都看 stop，收到即抛 WarmupStopped——不算失败、不发…, 退避期间（sleep 即 _stop.wait）收到停止信号：下一次导航之前就抛 WarmupStopped——否则还要再等一次最长 30 秒的导航，…, 次序：预热导航 → scope_started → scenario_started → 执行 → scenario_done →… (+46 more)

### Community 39 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.07
Nodes (42): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, cli 包 contributor 文档, skill 参考：CLI --json 字段契约, skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法 (+34 more)

### Community 40 - "render.py"
Cohesion: 0.07
Nodes (46): _add_act(), _add_device_evidence(), _add_step(), _arg_hint(), _cost_bits(), device_session_count(), _dispatch_hint(), _evidence_ref() (+38 more)

### Community 41 - "build_engines"
Cohesion: 0.07
Nodes (38): build_engines(), build_local_stores(), load_feature(), make_resolver(), Path, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。 (+30 more)

### Community 42 - "cli.py"
Cohesion: 0.08
Nodes (29): classify_vpc_state(), _error_code(), _is_credential_error(), _make_hint_clients(), BaseException, Exception, `gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`…, SSM 里记的生效取值 `stored` 是否与本次 `--vpc requested` 一致。 三种取值形态见… (+21 more)

### Community 43 - "test_user_steps.py"
Cohesion: 0.06
Nodes (53): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+45 more)

### Community 44 - "ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）"
Cohesion: 0.09
Nodes (34): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）, 墙钟时长归约（step/scenario/scope/run duration_ms）, EngineResolver（按 job.engine 解析 Engine）, 失败隔离 / failFast 旋钮, 优雅终止：schedule 只调 handle.stop(grace), _heartbeat_wrap（静默 worker 心跳注入） (+26 more)

### Community 45 - "RunStore"
Cohesion: 0.03
Nodes (51): 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, event_log adapters (sqlite / ddb), ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, ResultStore adapters (local / s3), RunStore adapters (local / ddb) (+43 more)

### Community 46 - "云端后端用户文档"
Cohesion: 0.08
Nodes (45): gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce）, kicker Lambda（冷启动器）, reconciler Lambda（主推进器） (+37 more)

### Community 47 - "test_lambda_asset.py"
Cohesion: 0.10
Nodes (27): BackendStack._build_lambda_asset, BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…, BackendStack._worker_subnet_ids, make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources() (+19 more)

### Community 48 - "SqliteEventLog"
Cohesion: 0.08
Nodes (25): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+17 more)

### Community 49 - "ssm_path"
Cohesion: 0.06
Nodes (34): _FakeTable, 假 DDB table 句柄：DynamoDBRunStore…, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_worker_template_path(), is_botocore_error(), _make_ecr_client(), _make_ssm_client(), _no_default_pointer_error() (+26 more)

### Community 50 - "config.py"
Cohesion: 0.06
Nodes (55): AppPlatformConfig, _apps_section(), _billing_method(), ConfigError, DevicePlatformConfig, _devices_section(), DevicesConfig, load_project_config() (+47 more)

### Community 51 - "build_fargate_engines"
Cohesion: 0.11
Nodes (20): build_fargate_engines(), _make_ddb_table(), _make_ecs_client(), boto3 ecs client（FargateEngine RunTask/StopTask/DescribeTasks）。, 每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR…, 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…, read_task_def_stop_timeout() (+12 more)

### Community 52 - "test_user_docs.py"
Cohesion: 0.08
Nodes (44): changelog_unreleased(), final_transcript(), 用户文档里交给口吻表与形态①③启发式扫的部分：CHANGELOG 截到第一个已发行节之前，定稿口播稿整份豁免（空串）， 其余页面全文。截断只保留前缀，故调用方…, CHANGELOG 交给退役词表与口头语表扫的部分，即第一个已发行版本节之前的内容。…, 口播稿是否仍是定稿原文：文件当前 SHA-256 等于同目录 `manifest.json` 所记的值。 定稿原文已配音、已出字幕，改字就得重新配音，故与…, wording_scope(), _default_model_claims(), _default_model_ids() (+36 more)

### Community 53 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 54 - "video.py"
Cohesion: 0.32
Nodes (17): cues(), digest(), link_chapter_title_track(), packets(), probe(), protected_state(), Path, Confirm the first slide at frame zero, hard cuts, and the closing fade. (+9 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (33): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+25 more)

### Community 56 - "appium.mts"
Cohesion: 0.06
Nodes (31): AppiumConnectorOptions, AppiumSessionArgs, AUTOMATION_NAMES, BROWSER_NAMES, CLIENT_TIMEOUTS, clientOptions(), ClientTimeouts, commandFailureKind (+23 more)

### Community 57 - "parametrize"
Cohesion: 0.13
Nodes (19): 云端 Device Farm 项目 ARN 的 SSM 路径（ADR 0051 决策 10、ADR 0033 资源清单第 11 条）。 写者是 stack…, ssm_device_farm_project_path(), _assert_record_read_hint(), parametrize, 读不到 SSM 里的项目记录（无权限、无凭证、网络、限流）→ 以退出码 2 结束，不找回不建立、不调 cdk：不知道记录在不在，就无从…, SSM 记录不是合法的项目 ARN（只会因手工改动出现）→ deploy、diff、--synth-only、destroy 都以退出码 2 结束、不调…, 读不到项目记录 → 以退出码 2 结束、不调 cdk，消息写明读的是哪个 SSM 路径与原异常；处置半句按错误类别：只有无权限才列权限， 无凭证提示配凭证与…, GetProject 的其他失败（限流、服务端、网络）→ diff 以退出码 2 结束、不调 cdk，消息点名 SSM 路径、记录的 ARN 与原异常，… (+11 more)

### Community 58 - "BackendStack"
Cohesion: 0.08
Nodes (21): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, `-c device_farm_project=` 给的项目 ARN；缺省或等于「待建立」占位时返回 None。 值由命令派生、不给…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。 (+13 more)

### Community 59 - "guard.test.mts"
Cohesion: 0.07
Nodes (16): adapterWith(), codeError(), FakeElement, FakeExec, FakeServer, fakeWebDriver(), Harness, inStep() (+8 more)

### Community 60 - "_RoundsTable"
Cohesion: 0.13
Nodes (16): _delayed_stopped_ecs(), _ev_item(), _gap_engine(), 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未… (+8 more)

### Community 61 - "check_version_skew"
Cohesion: 0.12
Nodes (17): check_version_skew(), 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。, 戳缺失表示本机制之前部署的环境 → warn（不拦）+ 提示运行一次 `gherkai deploy` 写入。, 任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。, 未装成包（从源码直接运行）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。, 只比 release 段（决策 7）：位数不同补零后比；同 release 段的 rc 与正式版视作同版本。, `cli_version` 必给（决策 7 比的是「写任务定义那一方」的版本）：不缺省成 gherkai-runtime 的版本—— editable… (+9 more)

### Community 62 - "_engine"
Cohesion: 0.11
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 63 - "LocalReportStore"
Cohesion: 0.06
Nodes (78): atomic_write_json(), atomic_write_text(), Path, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, _fmt_ms(), local_path_from_uri() (+70 more)

### Community 64 - "manifest.json"
Cohesion: 0.06
Nodes (35): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+27 more)

### Community 65 - "evidence.mts"
Cohesion: 0.08
Nodes (36): actionsOf(), buildEvidence(), BuildEvidenceInput, controlItemOf(), deviceKeysOf(), ENGINE, errorTextOf(), EVIDENCE_KIND (+28 more)

### Community 66 - "test_artifact_upload.py"
Cohesion: 0.08
Nodes (38): _Calls, list, ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, `.xml` → application/xml（ADR 0042 决策一，两引擎同规则同步改）：设备目标的原始控件树是 .xml（ADR 0051 决策…, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 半注入(有桶缺 NOVA_LOGS_DIR)→ 装配矛盾 fail-loud(静默 no-op 会让产物随容器盘销毁必丢,ADR 0033)。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。 (+30 more)

### Community 67 - "scan"
Cohesion: 0.07
Nodes (36): _js_comment_raw_lines(), TS / JS 注释的原文（不遮蔽字符串）：`//` 之后的部分，以及 `/* … */` 块内的行。只给本机坐标这类不受字符串干扰的规则用。, 按人读面的规则束扫一个文件，返回 (行号, 类别, 原文)。only_lines 给了就只报这些行（hook 的「只报本次改动的行」）。, scan(), TS / JS 注释里反引号包着的路径也要拦（注释抽取会先遮蔽字符串，本机坐标另按注释原文扫）。, test_machine_coordinate_is_caught_inside_js_comments(), parametrize, Path (+28 more)

### Community 68 - "_is_transient_network"
Cohesion: 0.12
Nodes (31): BaseException, _is_transient_client_error(), _is_transient_network(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是 NovaAct 的… (+23 more)

### Community 69 - "textui.py"
Cohesion: 0.10
Nodes (32): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。 (+24 more)

### Community 70 - "_Recorder"
Cohesion: 0.14
Nodes (12): cdk(), _FakeEngine, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, _Recorder (+4 more)

### Community 71 - "test_tunnel.py"
Cohesion: 0.13
Nodes (18): _gen_secret(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 一条已建立隧道的事实。url / pid / local_origin 可落盘 tunnel.json 供跨进程收尾；warmup_url 含令牌，只进…, 每 run 一换的随机串：128 位、十六进制——不需要 URL 编码，可原样进 CEL 字符串与 cookie 值。 (+10 more)

### Community 72 - "_mk_state"
Cohesion: 0.15
Nodes (18): _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, run 级消息（ADR 0037 决策 7）：文本在状态行下多一行、--json 多一个键；没有消息时两处都没有。退出码不变（error 仍 1）。 (+10 more)

### Community 73 - "main"
Cohesion: 0.11
Nodes (47): main(), StartBrowserSession 的请求名（规则见上）。`attempt` 是尝试序号（非负整数，起始值由调用方定）；`max_length` 缺省取…, session_request_name(), _assert_paired(), _closed(), _job(), _opened(), parametrize (+39 more)

### Community 74 - "06-devicefarm-appium.mts"
Cohesion: 0.05
Nodes (85): ADR-0010, BASE_URL, main(), makePng(), REGION, ADR-0033, BASE_URL, main() (+77 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.09
Nodes (30): gherkai 变更记录 (CHANGELOG), gherkai destroy, --expose-local 隧道模式, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, gherkai deploy push-worker / list-workers (+22 more)

### Community 76 - "run_scope.py"
Cohesion: 0.05
Nodes (49): ActRecord, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _attach_traj_refs(), _BrowserSession, _collect_traj(), _cost_from_result() (+41 more)

### Community 77 - "_FakeEcs"
Cohesion: 0.17
Nodes (10): _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped() (+2 more)

### Community 78 - "JobState"
Cohesion: 0.05
Nodes (74): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), _job_state_to_item(), 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid… (+66 more)

### Community 79 - "warmupSession"
Cohesion: 0.36
Nodes (5): leaveWarmupPage(), oneLine(), waitForMarker(), WarmupPage, warmupSession()

### Community 80 - "select"
Cohesion: 0.27
Nodes (9): availabilityRank(), closestVersion(), compareVersions(), eligible(), matchesVersionFamily(), noMatchingDeviceMessage(), segments(), select() (+1 more)

### Community 81 - "_ssm_params"
Cohesion: 0.20
Nodes (10): SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 带合法项目 ARN 时恰多出一条 `device-farm-project`，值逐字等于传入的 ARN（ADR 0033 资源清单第 11 条、ADR…, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, _ssm_params(), test_ssm_parameter_set_with_device_farm_project_is_exactly_seven(), test_ssm_parameter_set_without_device_farm_project_is_exactly_six() (+2 more)

### Community 83 - "_StderrScan"
Cohesion: 0.10
Nodes (23): Attribute, Call, _calls_redact(), _is_sys_module(), _is_writer(), _Outlet, AST, _qualified() (+15 more)

### Community 84 - "gherkai_runtime/names.py"
Cohesion: 0.09
Nodes (29): default_name(), device_farm_project_id(), device_farm_session_arn_prefix(), job_timeout_schedule_prefix(), _match_device_farm_project_arn(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, 项目 ARN 里 `project:` 之后的项目 id（会话 ARN 以它为前缀段）。形态不对抛 `ValueError`。, 本项目全部远程访问会话的 ARN 通配：`arn:aws:devicefarm:us-west-2:<账户>:session:<项目 id>/*`。形态不对抛… (+21 more)

### Community 85 - "_FakeEcsClient"
Cohesion: 0.17
Nodes (15): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeS3Client, _preflight_cap(), 运行一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。, test_preflight_all_present_returns_none() (+7 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.15
Nodes (23): _assert_check_names_documented(), _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, doctor 本机各段的替身：两个引擎都定位得到、自述带全部键，没有部署 provider。, 项名是 `name` 的**值**，键名护栏照不出它：把按引擎后缀的项名归一成 `<engine>` 形态后逐个核对契约页里写了。 (+15 more)

### Community 87 - "决策"
Cohesion: 0.10
Nodes (20): 0051. 远程访问会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034 (+12 more)

### Community 88 - "_stop_fails"
Cohesion: 0.13
Nodes (17): 按次给 Stop 的异常：第 n 次 Stop 抛 excs[n-1]（None 表示成功），之后都成功。, AgentCore 会话已建起、NovaAct 进入时抛网络错、随后释放会话又抛：释放异常不冒泡、不进建连重试判定；建连失败照常重试，…, 同一窗口里停止信号已置位：不再重试、不发判定事件，退出码 1——释放失败不能被停止分支吞成 0。, 建连期间收到停止信号且建连抛网络错、会话正常释放：这是建连失败不是释放失败——按停止路径以 0 退出、只有这个会话的一对会话事件。 守住「只有释放阶段抛出才记…, 首个会话释放失败、随后建连重试耗尽：退出码 1 而不是 80——泄漏可观测性压过网络分类（ADR 0028），core 不按网络故障重试。, 正常路径（无隧道）释放 AgentCore 会话失败：判定照发（scope_started、scope_done），退出码 1——对称 Midscene 的…, 会话已 Start、取 CDP 连接头撞网络错、Stop 又失败：此前这段藏在 SDK 的上下文管理器 __enter__ 里，Stop…, 同一窗口里 Stop 成功：就是普通的建连失败——重试成功后以 0 退出，不多记释放失败。 (+9 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 91 - "surface.mts"
Cohesion: 0.04
Nodes (46): ADR-0022, ADR-0042, ADR-0044, ACQUIRE_TIMEOUT_MESSAGE, AddressAttempt, AgentFactory, APP_LOCATION_MISSING_MESSAGE, CapabilityProbe (+38 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_project_config.py"
Cohesion: 0.08
Nodes (65): _fake_schedule_factory(), 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job…, ADR 0048 决策 4：假 worker 自述只有桌面网页，标了 @device:android 的 scope 在 plan 与 run…, test_device_target_rejected_by_plan_and_preflight_when_engine_lacks_target(), _android_caps(), _android_env(), _app_project(), _feature() (+57 more)

### Community 95 - "test_adr_hygiene.py"
Cohesion: 0.13
Nodes (26): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, 指向 journey 文件的规则正反例：仓库路径与相对路径（`../`、`./`、行首或标点之后）都命中；目录名本身、别的以 journey… (+18 more)

### Community 96 - "test_compose.py"
Cohesion: 0.04
Nodes (75): _find_worker_spec(), prune_empty_dirs(), Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION… (+67 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "use_color"
Cohesion: 0.18
Nodes (16): 执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。, color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env() (+8 more)

### Community 99 - "validate_job_definition"
Cohesion: 0.38
Nodes (6): _is_positive_number(), _is_text(), Job, 测试目标的定义层结构校验（ADR 0048 决策 3）。 两个时点各核一次：组合根写 definition 之前（run / submit…, definition 里的一个 job 必须是完整形态，否则抛 DefinitionContractError（推进器与 worker…, validate_job_definition()

### Community 100 - "driven"
Cohesion: 0.10
Nodes (8): driven(), _FakeBrowserClient, _FakeCm, _FakeNovaAct, 结构相同的上下文管理器替身（给 with wf 用）。, BrowserClient 的替身：start 记 ("session_start",) 并给出会话 id，stop 记…, main() 的 SDK 面全 fake：job 走 stdin（scenarios 空）、事件进内存 sink、会话与 cdp 的进出记进 trace。返回…, _Sink

### Community 101 - "skill_install.py"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 102 - "决策"
Cohesion: 0.13
Nodes (15): 0048. 测试目标：设备与界面类型两个维度、`@device` 与 `@app` 标签、core 的执行前预检, 1. 测试目标由三个正交维度描述：engine、device、ui_kind, 2. 两个 scope 级 tag：`@device` 与 `@app`, 3. core 的三处改动, 4. 目标不受支持时的拒绝：由能力自述决定，消息给出改法, 5. plan 的标注, 6. 运行期网页上下文不可用：声明了前提的确定性 step 记 error，不转 AI, 7. 应用目标上的导航 step 与落点核对规则 (+7 more)

### Community 103 - "Run Store Persistence Ports"
Cohesion: 0.14
Nodes (20): Commit-point Write Order (data plane first), RunStore.create_run(), DDB Single-Table Schema (run_id + item_type), DynamoDBRunStore, Cloud Failure Exit Code Layering, RunStore.finalize_run(), RunState high_water_mark Conditional Write, JobSink Port (+12 more)

### Community 104 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd()

### Community 106 - "决策"
Cohesion: 0.13
Nodes (15): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 不升 schema 版本，在 schema 1 上增键, 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端 worker 在建会话前按自己的 `targets` 自检 (+7 more)

### Community 107 - "决策"
Cohesion: 0.13
Nodes (15): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 7. Midscene 复用边界 (+7 more)

### Community 108 - "interface.mts"
Cohesion: 0.06
Nodes (24): adapterRegistry(), AppiumInterfaceConfig, decodeXmlEntities(), DeviceAgentArgs, EDGE_SCROLLS, InputContext, keyNameKey(), LONG_PRESS_DEFAULT_MS (+16 more)

### Community 109 - "test_precheck.py"
Cohesion: 0.11
Nodes (27): _num(), precheck_job(), precheck_schema(), precheck_target(), 建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的…, (device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。, 名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。, 秒数的写法：整数值不带小数点（1500 而不是 1500.0），其余按原值；与 Midscene 侧的插值结果一致。 (+19 more)

### Community 110 - "dependencies"
Cohesion: 0.11
Nodes (19): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-device-farm, @aws-sdk/client-dynamodb, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore (+11 more)

### Community 111 - "test_lambda_handlers.py"
Cohesion: 0.06
Nodes (39): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。 (+31 more)

### Community 112 - "LocalRunStore"
Cohesion: 0.04
Nodes (80): RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, Path, 只读 definition 的结构版本与写端 CLI 版本（ADR 0037 决策 7）；run_meta.json 不存在返回 None。, 读回运行态（RunState）；不存在返回 None。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新… (+72 more)

### Community 113 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 115 - "test_engines_matrix.py"
Cohesion: 0.23
Nodes (11): expected_rows(), matrix_rows(), 引擎能力矩阵（docs/user-guide/engines.md）的差集护栏（ADR 0049 决策 8）——Nova 侧与表格结构。 真值集是…, 解析 engines.md 里以「| 引擎 |」开头的那张表：每行 {engine, target, handle, model}。, 由一份自述推出该引擎应有的矩阵行（一行一个目标，按 targets 顺序、ui_kinds 顺序）。, 表里的引擎集合与产品的引擎集合相等：少一个引擎的行、或多出一个不存在的引擎名都失败。, 目标列只能用产品语言名称（render.target_label 产出的那一套）：Midscene 行由 npm 侧按手抄的名称映射核，这里把两侧…, Nova 行逐行对照真子进程的自述（剥掉 NOVA_* / GHERKAI_* / AWS_* 等覆盖，取无覆盖时的默认值）。 (+3 more)

### Community 116 - "evidence.test.mts"
Cohesion: 0.09
Nodes (21): build(), DESKTOP_SNAP, DEVICE_AI_SNAP, dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent (+13 more)

### Community 117 - "ADR 0043：驱动 gherkai 的 agent skill"
Cohesion: 0.20
Nodes (15): ADR 0001：范围限定英文 UI, ADR 0041：面向 agent 的 CLI 可操作面, ADR 0043：驱动 gherkai 的 agent skill, 评测去污染硬规则（CLI 来自仓库外 wheel、skill 副本随机目录、舞台路径随机）, 物化式 fixture 与可搬迁契约, 两臂评测法（with-skill 对 baseline）, ADR 0047：CLI 人读输出用 rich 渲染表格与树, gherkai_runtime.textui（表格 / 树 / 样式单点） (+7 more)

### Community 118 - "release_notes.py"
Cohesion: 0.48
Nodes (6): main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems()

### Community 119 - "app.mts"
Cohesion: 0.08
Nodes (27): APP_LAUNCH_SELF_EXIT_MESSAGE, APP_OBJECT_FORBIDDEN_MESSAGE, APP_OBJECT_MISSING_MESSAGE, APP_RESTART_SELF_EXIT_MESSAGE, APP_STATE, AppControl, appHandle(), AppObjectLocation (+19 more)

### Community 120 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 121 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Release Notes Guards"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 123 - "gherkai_cli/__main__.py"
Cohesion: 0.03
Nodes (159): progress(), 命令行的进度与诊断输出（ADR 0047）：一个函数，供 `__main__` 与各编排模块共用。, 进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `gherkai run ……, cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _available_step_targets(), _build_run_meta(), _build_selector(), _cloud_skew_gate() (+151 more)

### Community 124 - "test_skill.py"
Cohesion: 0.05
Nodes (59): bare_flags(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags() (+51 more)

### Community 125 - "test_technical_docs.py"
Cohesion: 0.36
Nodes (7): parametrize, Path, 技术文档的措辞与悬空指针护栏（ADR 0045 决策一 / 六：CONTRIBUTING、各包…, 正文无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」、不指 journey 文件与 WP 编号（代码块与行内代码不算）。, _rel(), test_scan_face_is_not_empty(), test_technical_doc_uses_written_register()

### Community 126 - "run-scope.test.mts"
Cohesion: 0.06
Nodes (21): ANDROID_WEB, DESKTOP, _events, fakePage, gotoCalls, ADR-0014, ADR-0020, ADR-0024 (+13 more)

### Community 127 - "Dist Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 128 - "patch-package 补丁 @cucumber+cucumber+13.0.0"
Cohesion: 0.33
Nodes (6): 默认 AI 判断的裸 When/Then step, 补丁的保守回退策略, patch-package 补丁 @cucumber+cucumber+13.0.0, ADR 0021: 本地 patch @cucumber/cucumber 按关键字消歧, 精确 pin cucumber 13.0.0 的版本约束, B1 退役清单（cucumber 入口 + 补丁 + bdd conftest）

### Community 129 - "_doc_rules.py"
Cohesion: 0.09
Nodes (37): ai_side_docs(), all_markdown(), classify(), clean_flag(), code_comment_files(), CommandSpan, comment_blocks(), comment_prose_lines() (+29 more)

### Community 130 - "probe.mts"
Cohesion: 0.09
Nodes (30): defaultDeviceParts(), ADR-0051, ADR-0052, applicationLongEdge(), AttemptFailure, DeviceCapabilityProbe, ensureNative(), log() (+22 more)

### Community 131 - "Media Conversion Verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 132 - "package.json"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 133 - "finalize.test.mts"
Cohesion: 0.08
Nodes (13): acquireWithOrphan(), Call, CHOICE, connectionReset(), Emitted, FakeClock, FakeFarm, Handler (+5 more)

### Community 134 - "FargateEngine"
Cohesion: 0.12
Nodes (16): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+8 more)

### Community 135 - "_argv"
Cohesion: 0.07
Nodes (41): _argv(), _context_pairs(), _deploy(), _parse_destroy(), 按动作取 Provider 方法与 args（destroy 走真 destroy parser；synth 给导出目录）。, diff / --synth-only / destroy 不建立项目：SSM 有值即沿用（diff 先用 GetProject 核对、项目还在），交给…, 参数不存在（含 stack 还不存在）→「待建立」占位，仍不建立项目；没有记录也就没有可核对的项目。diff 另提示用于计算变更集的模板不含…, SSM 有记录、GetProject 回 NotFound（项目被手动删除）→ diff 以「待建立」占位并警告：用有权限的凭证 deploy… (+33 more)

### Community 136 - "render_skill_contract.py"
Cohesion: 0.23
Nodes (12): docs/internals/cli-json-contract.md（机读字段级参考页）, _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。 (+4 more)

### Community 137 - "DynamoDB Events Transport ADR"
Cohesion: 0.18
Nodes (13): DynamoDB 共享 events 表作 events-out 传输, EventSink（可注入事件出口）, events 表键设计 PK=run_id#scope_id, SK=seq, events item TTL 自动过期（7 天 expires_at）, 读一致性（流式期 EC 游标 + 终读强一致）, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列 (+5 more)

### Community 138 - "Target"
Cohesion: 0.09
Nodes (45): AppRef, DeviceFarmRequest, 向 AWS Device Farm 要哪台设备（ADR 0048 决策 3）：名字明说服务商、不起中立名；`device_arn` 与…, 应用目标的应用条目（ADR 0048 决策 3）。两个形态：plan 形态只有别名与包名或 bundle id；run / submit 在组合根上传安装包后…, 一个 scope 运行在什么上面（ADR 0048 决策 1）：设备与界面类型；ui_kind 为 app 时带应用条目。缺省即桌面网页。, 机读与 plan 文本共用的紧凑写法（ADR 0048 决策 5 的形态）：`desktop/web`、`android/app:shop`。, Target, _device_request_from_dict() (+37 more)

### Community 139 - "决策"
Cohesion: 0.17
Nodes (12): 0053. 项目配置文件 gherkai.toml, 1. 文件定位：只有运行侧 CLI 读它，读出的值解析成具体值随 Job 走, 2. 取值顺序：选项、环境变量、配置文件、内建默认依次优先, 3. 节与键, 4. 设备选择要求显式，筛选的挑选规则确定, 5. 与 ADR 0044 覆盖链的关系：worker 侧覆盖项不进配置文件, 6. 护栏, 决策 (+4 more)

### Community 140 - "tunnel-warmup.test.mts"
Cohesion: 0.33
Nodes (3): FIXTURE, ADR-0035, ADR-0051

### Community 141 - "minimax_narration.py"
Cohesion: 0.26
Nodes (10): APIError, download_subtitles(), main(), NoRedirect, page_numbers(), post(), Exception, Path (+2 more)

### Community 142 - "test_skill_deploy_tokens.py"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。 (+3 more)

### Community 143 - "read_project_arn"
Cohesion: 0.33
Nodes (6): 从后端区域的 SSM 读项目 ARN（`ssm_path(prefix, DEVICE_FARM_PROJECT_KEY)`，stack 资源写入）。…, read_project_arn(), 读不到不等于没有：其他错误回落「待建立」会让 diff 把已部署的设备授权显示成删除，由调用方决定退出码（ADR 0051 决策 10）。, test_read_project_arn_missing_parameter_is_none(), test_read_project_arn_other_errors_propagate(), test_read_project_arn_returns_stored_value()

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "SessionOpened"
Cohesion: 0.09
Nodes (34): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+26 more)

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "test_user_facing_messages.py"
Cohesion: 0.20
Nodes (13): _docstring_node_ids(), AST, parametrize, 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, 待核尝试一族的禁用形态：「待核尝试」与「记为待核」命中，「待核对」与裸词「待核」不命中。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`… (+5 more)

### Community 148 - "image_tag"
Cohesion: 0.17
Nodes (14): image_tag(), worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, parametrize, `gherkai_runtime.names` 的 worker 镜像交付命名（ADR 0038「tag 命名」条：单一真源、同时是单一校验点）。…, variant 本身合法但拼出来超 128 字符 → 报 tag 那一层（两类错误分开报，见 names 里两个正则的注释）。, 版本串首字符非法（归一化只管 `+`/`!`）→ tag 层拒，不静默产出 docker 不认的 ref。, `names` 的读端常量与 `DynamoDBRunStore` 的写端字面量必须逐字一致（ADR 0038 清理 pass 的运行中 run…, test_image_tag_normalizes_epoch() (+6 more)

### Community 149 - "session.test.mts"
Cohesion: 0.07
Nodes (15): Call, CHOICE, connectionReset(), FAKE_CREDS, FakeClock, FakeFarm, Handler, makeJob() (+7 more)

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.18
Nodes (11): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 2. handler 上下文：七个字段与一条不变量, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据 (+3 more)

### Community 151 - "test_capabilities.py"
Cohesion: 0.14
Nodes (19): _clean_env(), `--capabilities` 自述入口单测（ADR 0036「5.」/ ADR 0024「引擎自报下限」，Nova 侧）。…, 不注入任何 env（旧宿主 / 手动直接运行）：下限仍 ≥ 缺省 act 上界 120 + margin，不退化成小值。, 不读 stdin：stdin 是一根**写端一直开着**的管子——真去读就永远阻塞、这里就 timeout 失败。…, steps 加载失败在这个入口也 fail-loud（ADR 0037 决策 4「两个非 job 入口同样加载 steps」）： 非 0 退出、stderr…, `--list-deterministic` 已删、**不留别名**（ADR 0036 被拒方案末条「每个自述项一个独立 flag」）。 只有真 argv…, 子进程 env：保留运行必需项，剥掉 GHERKAI_* / AWS_* / NOVA_*（含本机 region 与凭证落点）。 剥 AWS…, 键集恰六个，且 `min_grace_s` 是注入的 `NOVA_ACT_TIMEOUT_S` 加 worker 侧 margin（组合根查它当 grace… (+11 more)

### Community 152 - "arg_offload.py"
Cohesion: 0.14
Nodes (12): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, 指针必须是文本（s3:// URI）；别的类型是同版本下的定义违约，不让它变成 urlparse 的裸 AttributeError。, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与… (+4 more)

### Community 153 - "artifact-upload.test.mts"
Cohesion: 0.32
Nodes (6): mkLogDir(), mkShots(), ADR-0029, ADR-0042, ADR-0051, tmproot()

### Community 155 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 156 - "engines-matrix.test.mts"
Cohesion: 0.20
Nodes (7): DEVICE_LABEL, HANDLE_BY_DEVICE, MATRIX, ADR-0049, ADR-0050, Row, UI_KIND_LABEL

### Community 157 - "ADR 0041: 面向 agent 的 CLI 能力"
Cohesion: 0.09
Nodes (27): RunMeta.extra_http_headers（额外请求头注入）, 隧道凭据脱敏（剥 URL userinfo）, worker --capabilities 自述入口, CLI list-deterministic --engine, 注册面元数据（description / example 必填）, CI 发布链与占名（tag 触发全链）, 版本 skew 检查（三态）, steps/ 定制面（随 definition 走 + env 注入） (+19 more)

### Community 158 - "test_devicefarm.py"
Cohesion: 0.15
Nodes (16): list_open_sessions(), OpenSession, 列出项目里所有未到 COMPLETED 的远程访问会话，含排队中的（ADR 0051 决策 6 的泄漏护栏，供 doctor 用）。 翻页列举…, 一个未到 COMPLETED 的远程访问会话（doctor 据此给出控制台链接与停止命令）。`name` 与 `created` 在服务没有返回时为 None。, Python 侧 Device Farm 客户端的行为（ADR 0051 决策 10「项目」「调用归属」、决策 6 的 doctor 列出未结束会话）。 用…, 网络故障：botocore 抛的不是 ClientError，Stubber 排不出这种失败，故用假客户端。, 会话的生命周期只归 worker：本模块只列举，不出现建立或停止会话的调用（ADR 0051 决策 6「不做回收器」）。, _session() (+8 more)

### Community 159 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 160 - "test_definition_schema.py"
Cohesion: 0.24
Nodes (16): parametrize, Path, definition 结构版本闸门（ADR 0037 决策 7）在 CLI 的接线：status / explain /…, 别的版本写出的 run 目录连运行态的形状都不保证：先核结构版本，再读运行态——否则「请升级」会变成一个解析异常。, 本机接力宿主读到同版本下形态违约的提交记录（这里真的从 run_meta.json 删掉一个 job 的 target 键）：CLI 读端有退出码可交，…, 读头阶段的形态违约（结构版本字段不是整数）：三个本机读端都以退出码 2 结束并说明，不是裸异常；运行态不被改动、不写 run 级消息…, 用假 schedule 真实执行一次本机 run，落下结构版本 1 的 run_meta.json；返回 (报告目录, run_id)。, _rewrite_schema() (+8 more)

### Community 161 - "Artifact Uploader Component"
Cohesion: 0.09
Nodes (29): 引擎特有量不进 model（act_count）, JobResult 持有 Job、engine 经 property delegate, href 相对化（local 相对 / cloud 恒等 ref）, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 式产物拷贝, 不透明搬运铁律（model/wire/schedule 永不解引用 ref）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写） (+21 more)

### Community 162 - "deterministic.py"
Cohesion: 0.04
Nodes (77): clear(), _closed_set(), deterministic(), DeterministicConflict, DeterministicKeywordMismatch, _Entry, Handles, Hit (+69 more)

### Community 163 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 164 - "uiautomator2.mts"
Cohesion: 0.09
Nodes (20): ANDROID_KEYCODES, APP_DID_NOT_HANDLE_ADDRESS_MESSAGE, CHROME_PACKAGE, CLEAR_INPUT_KEY_PRESSES, createUiAutomator2Adapter(), DEFAULT_SCROLL_PERCENT, extractAndroidControls(), FOREGROUND_NOT_APP_MESSAGE (+12 more)

### Community 165 - "job-source.mts"
Cohesion: 0.12
Nodes (11): Job, JOB_KEYS, JobApp, JobDeviceRequest, JobSource, JobTargetShape, Missing, ADR-0016 (+3 more)

### Community 166 - "read-points.test.mts"
Cohesion: 0.07
Nodes (43): ASSIGNMENT_OPERATORS, capabilitiesReads(), COMPARISON_OPERATORS, declarationNamed(), deviceFarmClientSites(), deviceSdkValueImports(), EQUALITY_OPERATORS, Exemption (+35 more)

### Community 167 - "Cooperative Stop Design"
Cohesion: 0.25
Nodes (8): 建连早期误报 engine_error 根治, handler 内零 I/O（只置标志 + 记信号号）, 安全点按「单元完成度」判定丢弃, Nova worker flag-only 协作式停止, 被拒方案：asyncio 化消除 greenlet, 被拒方案：handler raise _Terminated 穿透 with, 泄漏兜底：AgentCore 原生 session TTL, SIGINT（Ctrl-C）纳入 flag-only handler

### Community 168 - "render_traffic_policy"
Cohesion: 0.15
Nodes (13): 本 run 的 ngrok 流量策略 YAML（ADR 0051 决策 13）：手写模板替换，不为此引 yaml 依赖——结构固定，令牌与 cookie…, 把文本里每个「作为一个地址出现」的 origin 换成 base：origin 之后的 URL 字符段 R 为空、以 / ? #…, render_traffic_policy(), replace_origin(), parametrize, skipif, ADR 0051 决策 13「边缘策略」：恰 4 条规则（免费层上限 5）、不含 basic-auth 与 remove-headers、Set-Cookie…, ngrok 读的是解析后的结构、不是字面量，所以按 YAML 解析后核：四条规则按序 warmup-ok / warmup-reject / check-ok… (+5 more)

### Community 169 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 170 - "test_devicefarm_client_placement.py"
Cohesion: 0.14
Nodes (20): _import_bindings(), import 绑定的名字到所指对象的完整路径：`import sys as s` 得 s 指 sys，`from sys import stderr as…, Module, _imports_devicefarm_module(), _is_devicefarm_client_call(), _production(), AST, _python_sources() (+12 more)

### Community 171 - "adapters.contract.test.mts"
Cohesion: 0.08
Nodes (17): ADAPTERS, ContractCase, ContractFixture, FIXTURES, FOREGROUND_POLL, HIDE_KEYBOARD, iface(), KEYBOARD_INTERFACES (+9 more)

### Community 172 - "console_url"
Cohesion: 0.24
Nodes (10): device_header_lines(), scope 表头的设备两行（ADR 0051 决策 8）：代表会话的设备描述、会话 ARN 对应的 Device Farm 控制台链接；桌面 job…, test_console_url_only_for_session_arns(), console_url(), device_label(), 远程访问会话的呈现辅助（ADR 0051 决策 8「scope 表头由 session_opened.device 与…, worker 报的设备描述 → 一行人读文本（platform model osVersion，unit 另括注）；没有描述返回 None。, 会话 ARN → Device Farm 控制台的远程访问会话页链接；不是会话 ARN 时返回 None。 路径按控制台「项目 →… (+2 more)

### Community 173 - "Engine Port & Job Planning"
Cohesion: 0.33
Nodes (7): Engine port（run_scope → WorkerHandle + Event 迭代器）, FargateEngine adapter, JobSource（可注入 job 入口）, pipe 传输实现 die（worker I/O 边缘必改）, Job（一个 scope = 一个会话边界）, plan 模块（.feature → Job 列表）, select 谓词（scenario 筛选）

### Community 174 - "Scope Tag Parsing"
Cohesion: 0.29
Nodes (7): engine 解析（scope 级）, id 派生（scopeId / scenarioId 关联键）, 一个 scenario 多个 @scope 值 → 报错, scope seam（tag 分组 + engine 校验）, scope 全局命名空间（跨文件合并，撞名 warning）, timeout 解析（@timeout:N → Job.timeoutS）, uri 互异契约（重复 uri → 报错）

### Community 175 - "S3 Key Mirrors Local Run Tree"
Cohesion: 0.50
Nodes (4): S3 Key Mirrors Local Run Tree, S3ReportStore (no artifact copy, href==ref), Upload Whole Artifact Directory (type-agnostic), S3ReportStore

### Community 176 - "Context Glossary Guards"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条由…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 177 - "ADR 0023: Nova Act acting 锁 Python"
Cohesion: 0.32
Nodes (8): 双语言裂缝（物理约束）, ADR 0006: 形态 A——两个子工程、无编排器, 薄 worker 子进程（一次调用=一个 scope=一个 job）, 两个引擎都作为子进程 worker、核心语言自由选 Python, Nova Act REST API = 客户端驱动的工具调用循环, ADR 0023: Nova Act acting 锁 Python, Python nova-act SDK 的 Playwright/CDP 客户端循环, 全 TS 核心路径（被证伪关闭）

### Community 178 - "Graceful Stop Contract"
Cohesion: 0.33
Nodes (6): act 有界返回（per-act timeout）, 引擎经 --capabilities 自报 min_grace_s, FargateWorkerHandle.stop → StopTask, grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, 机制层：Engine adapter / WorkerHandle 把停翻成机制

### Community 179 - "Worker Termination Contract"
Cohesion: 0.33
Nodes (6): 事件流结束信号 / 存活判定迁移, exitCode 落值延迟与 MISSING 第三态, 未来演进：显式 core→worker 控制通道, Midscene worker 有序显式 cleanup handler, 逻辑层：schedule 经 worker 句柄请求停（handle.stop）, 终止契约（core 请求 worker 优雅停止）

### Community 180 - "Package URL Links"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 181 - "test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions"
Cohesion: 0.40
Nodes (4): _AbsentEngine, 容器引擎替身：`probe()` 说「docker 没装」。, 容器引擎缺失的前置警告只对**纯发行版**成立：dev/post/本地段版本的 worker 镜像步骤本就走不到「基础镜像同步」 （ADR 0038…, test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions()

### Community 182 - "._run_cdk"
Cohesion: 0.07
Nodes (25): cdk_command(), check_cdk(), check_node(), _make_sts_client(), _node_major(), Path, cdk CLI 的调用前缀：PATH 上的 `cdk` 优先，否则 `npx -y aws-cdk@2`（ADR 0037 决策 6）。都没有 → 空列表。, `node --version` 的主版本号；取不到/认不出 → None（**不据此拦**，版本探测失败不该挡住部署）。 (+17 more)

### Community 183 - "session.mts"
Cohesion: 0.07
Nodes (24): ADR-0033, AUTH_ERROR_NAMES, CallBound, CallFailure, CreateResult, DEVICE_FARM_REGION, deviceArnRejectedMessage(), DeviceFarmClientOverrides (+16 more)

### Community 184 - "DeviceSurface"
Cohesion: 0.15
Nodes (3): AppiumSession, DeviceSurface, restoreFailedMessage()

### Community 185 - "test_extract_missing_env_returns_none"
Cohesion: 0.33
Nodes (4): _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 非 gherkai 起的 task（env 无 RUN_ID/SCOPE_ID）→ (None, None, ...)，handler 会跳过。, test_extract_missing_env_returns_none(), test_kicker_timeout_path_skips_tick_when_not_detached()

### Community 186 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 188 - "_ClientError"
Cohesion: 0.08
Nodes (15): _botocore_like(), _Cfn, _ClientError, _DeviceFarmStub, df(), Exception, 解析凭证链本身出错（如 profile 名不存在）不算「完全没有凭证」：不回落占位，照常去读 SSM，读失败按退出码 2 结束，处置半句 提示配凭证与…, `gherkai_runtime.devicefarm` 三个入口的替身，并记下调用。默认：SSM 无记录、diff 核对时记录的项目存在、找回或建立的… (+7 more)

### Community 189 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 190 - "移动真机支持（1.5）：实施进度总纲"
Cohesion: 0.29
Nodes (6): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）, 实施期要核的点（ADR 已定、实施时顺手验证）, 恢复现场, 现场, 移动真机支持（1.5）：实施进度总纲, 遗留项

### Community 191 - "_stopped_detail"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 192 - "test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 193 - "Gherkin Parse Seam"
Cohesion: 0.50
Nodes (4): gherkin-official 第三方库 seam, keyword 判不出 → fail-fast（PlanError）, parse seam（藏 gherkin-official）, step 顺序 = 书写顺序，keyword 只决定派发

### Community 194 - "files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 195 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 196 - "test_subprocess_engine.py"
Cohesion: 0.06
Nodes (60): _join_pumps(), _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 以非零退出码（含被信号强杀的负码）结束时抛错（终结函数按退出码判）。 纯阻塞行读、纯… (+52 more)

### Community 197 - "gherkai_worker_novaact/__init__.py"
Cohesion: 0.16
Nodes (14): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, _presend_act_siblings(), act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, 进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，回归哨兵）。 被…, _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验提前上传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。 (+6 more)

### Community 203 - "Architecture Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, gherkai 架构图发布入口页, 执行与推进全景交互图

### Community 204 - "Slide Frame SSIM Checks"
Cohesion: 0.67
Nodes (3): slide_area_ssim_checks, at_31_seconds, first_frame

### Community 205 - "gherkai_deploy_aws/names.py"
Cohesion: 0.10
Nodes (17): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 生效 VPC 取值的 SSM 路径（ADR 0037 决策 6「VPC 取值持久化比对，三态齐全」）。 值形态三种：`default` / `new:<所建… (+9 more)

### Community 210 - "offlineSelfCheck"
Cohesion: 0.18
Nodes (11): CommandRecorder, contextOf(), diffIsClean(), exerciseSession(), fakeDriver(), isThenable(), offlineAdapter(), offlineSelfCheck() (+3 more)

### Community 211 - "Job"
Cohesion: 0.02
Nodes (165): _explain_job(), 写 definition 之前的结构校验（ADR 0048 决策 3 第一处）：组合根尚未填入设备请求的设备 job 以退出码 2 被拒；桌面 job 放行。, plan 形态的应用条目只有别名与包名两键（位置三项由组合根在提交时填入，ADR 0048 决策 3）。, 执行前预检的第二项目标检查（ADR 0048 决策 3）：job 墙钟预算超过该目标的会话上限即拒绝；桌面条目不带上限不检查。, test_plan_json_app_entry_is_exactly_alias_and_app_id(), test_target_rejections_flag_timeout_over_session_limit(), test_validate_definition_rejects_plan_form_device_job_before_writing(), 把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore… (+157 more)

### Community 213 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 214 - "test_tunnel_host.py"
Cohesion: 0.13
Nodes (21): compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。 (+13 more)

### Community 215 - ".acquireSteps"
Cohesion: 0.11
Nodes (8): acquireErrorMessage(), AdapterRegistry, AppiumConnector, DeviceFarmSessions, GuardFactory, reasonOf(), unsupportedDriverMessage(), warmupErrorMessage()

### Community 219 - "no-device-deps.test.mts"
Cohesion: 0.10
Nodes (19): BIN, DEVICE_DIRS, DEVICE_PACKAGES, DEVICE_SCOPES, deviceLoads(), filePath(), isRunScope(), LIMITS (+11 more)

### Community 221 - "执行与推进模型导览（run/submit × local/cloud）"
Cohesion: 0.08
Nodes (44): Archify Diagram Viewer Preset (classic, showcase quality), 五层全景图, 一次 run 的生命周期图, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Env Inheritance Diagram (+36 more)

### Community 223 - "precheck.mts"
Cohesion: 0.23
Nodes (12): DEVICE_LABEL, ADR-0024, ADR-0049, ADR-0051, precheckJob(), precheckSchema(), precheckTarget(), spaced() (+4 more)

### Community 224 - "gemini_image.py"
Cohesion: 0.33
Nodes (4): HTTPRedirectHandler, NoRedirect, 演示制作规范, 演示制作与媒体工具说明

### Community 227 - "test_lifecycle_states.py"
Cohesion: 0.07
Nodes (22): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerExitError, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity() (+14 more)

### Community 228 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 229 - "test_fargate_engine.py"
Cohesion: 0.13
Nodes (23): _await_engine(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。, 执行 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env() (+15 more)

### Community 235 - "sessionEventSink"
Cohesion: 0.33
Nodes (3): requireName(), sessionEventSink, sessionOpenedEvent()

### Community 240 - "session-name.mts"
Cohesion: 0.12
Nodes (19): AGENTCORE_SESSION_NAME_MAX, decode(), DecodedSessionName, DEVICE_FARM_SESSION_NAME_MAX, encode(), encodedUnits(), matches(), MatchOptions (+11 more)

### Community 245 - "_Worker"
Cohesion: 0.13
Nodes (15): _heartbeat_wrap(), Event, Job, 单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。, 对本 job 落定停止原因并（首次）向 worker 发停止请求；已落定、已返回或内容已完整的直接返回现值。事件循环、异常分支与…, 内容已完整而 deadline 已过：只催 worker 收尾（发停止请求，排空上界从此刻起算），不落定停止原因——判定已成，…, 运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run… (+7 more)

### Community 246 - "bin.mts"
Cohesion: 0.12
Nodes (11): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037, ADR-0051, MASK, ADR-0035 (+3 more)

### Community 247 - "_World"
Cohesion: 0.10
Nodes (8): _check_wire_shape(), _Client, _Cm, _Nova, core/gherkai_core/wire.py 对会话事件的校验逐条重述，外加桌面专属的两条（不带 device，不带 observedS 与…, 假 SDK 的共享状态：每次 Start 依次取 start_plan 的一项（None 成功；异常实例即抛；callable 先调用再成功），会话 id…, _Sink, _World

### Community 249 - "deterministic.test.mts"
Cohesion: 0.20
Nodes (7): BUILTIN, HANDLES_FIXTURE, META, ADR-0020, ADR-0022, ADR-0050, UNTOUCHABLE_CTX

### Community 252 - "stopTimeout=120 / grace 预算校准"
Cohesion: 0.15
Nodes (14): ACT_TIMEOUT_S=120 不压（否决解法 B）, 中断产物丢失风险（容器盘停即销毁）, 孤儿产物扫盘 reaper（经分析否决）, 安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底, 关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）, stopTimeout=120 / grace 预算校准, IAM 最小权限（task role 动作×资源两维收窄）, job-in S3 对象按 tag 的 7 天 lifecycle (+6 more)

### Community 253 - "_build_parser"
Cohesion: 0.08
Nodes (37): platform_label(), ADR 0053 决策 4 的用户可见消息：有该平台的设备 scope，却没有任何来源指定设备。, unspecified_message(), _add_config_flag(), _add_device_flags(), _add_selection_flags(), _build_parser(), _finite_float() (+29 more)

### Community 254 - "xcuitest.mts"
Cohesion: 0.11
Nodes (16): CLEAR_INPUT_BACKSPACES, createXcuitestAdapter(), DEEP_LINK_UNSUPPORTED_MESSAGE, elementIdOf(), extractIosControls(), FINGER_DIRECTION, IOS_KEY_CHARACTERS, ADR-0039 (+8 more)

### Community 256 - "项目约定"
Cohesion: 0.29
Nodes (6): graphify, 代码纪律, 工作方式, 文档纪律, 沟通, 项目约定

### Community 257 - "test_stderr_redaction.py"
Cohesion: 0.07
Nodes (50): _log(), 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…, _assert_redacted(), _package_sources(), _plain(), parametrize, worker 自己写 stderr 的出口都经凭据脱敏（ADR 0035 决策 5 的出口清单；与 Midscene worker 的 stderr…, fatal 出口在 main() 第一步装上：三条入口（python -m、console script、直接运行模块）都经 main()。 (+42 more)

### Community 258 - "ADR 0014: AI 优先断言"
Cohesion: 0.06
Nodes (57): CLAUDE.md（项目约定）, CONTEXT.md（领域概念与术语）, ADR 0001: 范围限于英文 UI, 概念：非英文应用用 @engine:midscene 路由, 概念：Nova Act 中文词语级文本匹配短板, ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码, 概念：Midscene 仅走 chat-completions 接口 (+49 more)

### Community 259 - "wire.py"
Cohesion: 0.05
Nodes (65): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core… (+57 more)

### Community 260 - "warmup.mts"
Cohesion: 0.15
Nodes (18): attempt(), AttemptResult, _BlockIsPort, createDeviceWarmup(), DeviceWarmupArgs, DeviceWarmupBlock, DeviceWarmupDeps, findWarmupMarker() (+10 more)

### Community 262 - "e2e_harness.py"
Cohesion: 0.23
Nodes (11): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, --interrupt 中断时机矩阵, e2e_harness.py（opt-in 手动端到端验证脚本）, Path, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, harness 报告判读要点（sample_valid 先于 n_lost）, run() (+3 more)

### Community 263 - "appium.test.mts"
Cohesion: 0.10
Nodes (13): ACQUIRE_TIMED_OUT, ANDROID_APP, budgetOf(), connector(), connectWith(), FakeClient, fakeWdio(), FakeWdioScript (+5 more)

### Community 264 - "_role_statements"
Cohesion: 0.11
Nodes (26): _all_actions(), _as_list(), _bucket_lifecycle_rules(), parametrize, Template, 产物桶的生命周期规则**全集**恰为 expire-job-in 与 expire-apps 两条（ADR 0033、ADR 0051 决策 9），与…, 某角色全部 policy 语句的原样列表；按 policy 的 Roles 引用里的逻辑 id 片段认角色（如 `TaskRoleMidscene`）。, 带项目 ARN 合成时 Midscene task role 的设备权限逐条对照 ADR 0033 的权限表。… (+18 more)

### Community 265 - "runScope"
Cohesion: 0.16
Nodes (11): createSurface(), drainArtifactQueue(), exitAfterFailure(), log(), main(), runScenario(), runScope(), scopeErrorEvent() (+3 more)

### Community 266 - "test_reconcile.py"
Cohesion: 0.09
Nodes (37): ReportStore adapters (local / s3), finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher (+29 more)

### Community 269 - "_advancer_stmts"
Cohesion: 0.50
Nodes (4): _advancer_stmts(), 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…, test_reconciler_and_kicker_have_the_same_permission_face()

### Community 270 - "device_reprobe 使用说明（Midscene 设备模块的真机重新探测）"
Cohesion: 0.20
Nodes (10): device_reprobe 使用说明（Midscene 设备模块的真机重新探测）, 判读, 前置条件, 定位与适用场景, 离线自检（`--offline`）, 类型检查, 调用, 费用 (+2 more)

### Community 272 - "redact.test.mts"
Cohesion: 0.29
Nodes (4): FIXTURE, ADR-0035, ADR-0051, SECRET_CASES

### Community 273 - "ensure_app_object"
Cohesion: 0.10
Nodes (33): app_object_key(), AppLocation, AppUploadError, ensure_app_object(), _error_code(), BaseException, datetime, Exception (+25 more)

### Community 274 - "reconcile.tick（推进器共享入口）"
Cohesion: 0.17
Nodes (13): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState）, status --wait 接力推进 (+5 more)

### Community 275 - "_error_text"
Cohesion: 0.25
Nodes (8): _error_text(), _one_line(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, 多行文本 → 一行有界原因（首个非空行、折叠空白、先脱敏再封顶 300 字）；`_error_text` 与注册表层面的 error 消息共用。, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…, 隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。, test_error_text_prefers_sdk_message_and_is_single_line(), test_error_text_redacts_before_truncation()

### Community 276 - "NgrokTunnel"
Cohesion: 0.22
Nodes (9): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。, start：agent 命令带日志通道与流量策略文件；策略是四条规则的令牌换 cookie（不是 basic-auth）、文件 0600；预热地址带本次令牌；…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, test_ngrok_binary_missing_reports_install_hint(), test_ngrok_start_spawns_agent_with_policy_and_fresh_secrets() (+1 more)

### Community 278 - "probe.test.mts"
Cohesion: 0.14
Nodes (6): fakeSession(), HERE, ADR-0052, probeWith(), Script, Step

### Community 279 - "web-context.mts"
Cohesion: 0.16
Nodes (13): contextNames(), LocateDeps, locateError(), locateFailure(), locateWebContext(), ADR-0039, ADR-0050, ADR-0052 (+5 more)

### Community 280 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 281 - "_Page"
Cohesion: 0.22
Nodes (4): _Page, _Resp, parametrize, test_agentcore_release_failure_after_warmup_rejection_or_stop_exits_1_with_both_layers_released()

### Community 282 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 286 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, 云端 definition 缺 worker_task_defs 是定义违约（ADR 0037 决策 7 不留兼容分支）：不按默认指针解析、不推进，run 标…, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_marks_run_error_when_definition_lacks_worker_task_defs(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 287 - "severity 数值序（_STATUS_SEVERITY）"
Cohesion: 0.38
Nodes (7): 退出码基于 run 级 severity, _NON_VERDICT 与 _aggregate 入口过滤, severity 数值序（_STATUS_SEVERITY）, Status.ABORTED（core 派生态）, Status.PENDING / RUNNING（生命周期前置态）, Status.SKIPPED（core 派生态）, TERMINAL_STATUSES（终态真源，取补定义）

### Community 294 - "app.test.mts"
Cohesion: 0.17
Nodes (10): FAKE_CREDS, LOC, ADR-0050, ADR-0051, ADR-0052, RFC-3986, recomputeSignature(), SAMPLED (+2 more)

### Community 295 - "warmup.test.mts"
Cohesion: 0.17
Nodes (10): androidTree(), EXEC, FIXTURE, harness(), HarnessOptions, HERE, LOADING, ADR-0051 (+2 more)

### Community 297 - "_fixture"
Cohesion: 0.05
Nodes (50): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload() (+42 more)

### Community 298 - "finalize.mts"
Cohesion: 0.29
Nodes (10): deleteAppiumSession(), emit(), emitAttempted(), finalizeOnce(), ADR-0051, ADR-0052, observedSeconds(), RELEASE_RETRY_DELAY_MS (+2 more)

### Community 299 - "_out"
Cohesion: 0.09
Nodes (31): Aws, _connect(), list_workers(), make_aws(), _pending_cleanup(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 本模块用到的四个 client。**组合根注入**（测试直接塞 moto client），同 compose 的 `_make_*` 惯例。 (+23 more)

### Community 300 - "ADR 0024: worker–core 协议"
Cohesion: 0.06
Nodes (83): cli/DEVELOPMENT.md, CONTRIBUTING（contributor 入口）, core 包 contributor 文档, core 测试说明（单测 + 集成测试）, gherkai-deploy-aws contributor 手册, ADR 0011: AgentCore 浏览器 system default vs custom, 系统默认浏览器 aws.browser.v1, 自建 custom browser（create-browser） (+75 more)

### Community 301 - "ContainerError"
Cohesion: 0.08
Nodes (18): ContainerEngine, ContainerError, Exception, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 多平台索引的目标平台视图（`inspect --platform linux/amd64`）：返回 (os, architecture)，本机没有该平台的内容…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+10 more)

### Community 303 - "device/surface.test.mts"
Cohesion: 0.10
Nodes (10): harness(), HarnessOptions, LOST_BEFORE_START, makeJob(), ADR-0050, ADR-0051, ADR-0052, opened (+2 more)

### Community 308 - "Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障"
Cohesion: 0.33
Nodes (6): 1. 链路一句话, 2. 签名契约：五条决定成败的细节, 3. 失败模式表, 4. 依赖与自检, Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障, 延伸阅读

### Community 309 - "reconciler.py"
Cohesion: 0.08
Nodes (35): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+27 more)

### Community 310 - "AppiumInterface"
Cohesion: 0.23
Nodes (4): AppiumInterface, keyboardNotHiddenLogLine(), locatePoint(), pngSize()

### Community 312 - "web-context.test.mts"
Cohesion: 0.24
Nodes (7): DriverScript, fakeDriver(), ADR-0050, ADR-0052, opened, session(), surfaceWith()

### Community 314 - "._pump"
Cohesion: 0.50
Nodes (3): Event, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, Timer

### Community 315 - "wdio-log.mts"
Cohesion: 0.28
Nodes (7): installWdioLogMasking(), ADR-0051, sameLoggerAsWebdriver(), WDIO_LOG_LEVEL, WDIO_LOGGER, WDIO_MASKING_PATTERNS, wdioLogMaskingInstalled()

### Community 316 - "wdio-log.test.mts"
Cohesion: 0.22
Nodes (4): ENDPOINT_PATH, FIXTURE, ADR-0051, PRESIGNED_SECRETS

### Community 318 - "start_tunnel_for_jobs"
Cohesion: 0.29
Nodes (7): 隧道就绪后的四件产物：映射过的 definition + 隧道模式的额外请求头 + 会话预热地址 + 隧道事实（收尾凭据）。…, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 321 - ".waitRunning"
Cohesion: 0.32
Nodes (3): classifyCallFailure(), isStopped(), minutesOf()

### Community 324 - "_events_table_actions"
Cohesion: 0.33
Nodes (6): _events_table_actions(), 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, test_advancer_events_table_face_is_read_plus_putitem(), test_exit_observer_can_only_putitem_on_events_table()

### Community 325 - "precheck.test.mts"
Cohesion: 0.50
Nodes (3): DESKTOP_ONLY_TARGETS, DEVICE_TARGETS, ADR-0049

### Community 326 - "_DeterministicCtx"
Cohesion: 0.33
Nodes (3): _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）与导航原语…, 引擎的导航原语（内建导航条目用它打开地址，ADR 0020 第 3 条）：Nova 用 SDK 的 `go_to_url`。

### Community 328 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 替换成干净的隧道地址 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_other_jobs_and_original_untouched(), test_map_replaces_docstring_and_datatable_cells_independently() (+1 more)

### Community 329 - "runOnDevice"
Cohesion: 0.40
Nodes (6): log(), main(), parseOptions(), recordingParts(), runOnDevice(), writeMatrix()

### Community 330 - "runStep"
Cohesion: 0.50
Nodes (3): cumulativeTokens(), runStep(), stepCost()

### Community 331 - "Fargate/ECS RunTask 执行后端"
Cohesion: 0.50
Nodes (4): AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务

### Community 336 - "_make_devicefarm_client"
Cohesion: 0.25
Nodes (8): _make_devicefarm_client(), devicefarm 客户端：区域恒为 DEVICE_FARM_REGION，与 profile 或环境变量给的后端区域无关。抽出来供测试替换。, df(), 环境变量与 profile 都把后端区域给成 us-east-1，客户端仍落在 us-west-2。, 真 devicefarm 客户端外包 Stubber，并替换模块的客户端工厂；记录工厂收到的 profile。, ssm(), test_client_region_is_device_farm_region_regardless_of_backend_region(), Stubber

### Community 337 - "test_finished_run_gate_keys_on_the_committed_run_status_only"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 338 - "_joined_refs"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 339 - "desktopFactory"
Cohesion: 0.38
Nodes (7): desktopFactory(), desktopHooks(), desktopSeam(), econnreset(), fakeAgentCore(), fakeBrowser(), surfaceDeps()

### Community 340 - "ArtifactUploader"
Cohesion: 0.08
Nodes (23): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记… (+15 more)

### Community 341 - "diffAgainstFixture"
Cohesion: 0.67
Nodes (3): diffAgainstFixture(), flatten(), formOf()

### Community 347 - "worker/surface.test.mts"
Cohesion: 0.33
Nodes (5): knownFailure, lost, ADR-0051, ADR-0052, unknownResult

### Community 348 - "stop_tunnel"
Cohesion: 0.40
Nodes (5): 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 350 - "scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 351 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 355 - "verify_project"
Cohesion: 0.33
Nodes (6): 用 GetProject 只读核对项目是否还在（供 `diff` 核对 SSM 记录的 ARN，ADR 0051 决策 10「项目」）：在则…, verify_project(), 非 NotFound、非无权限的错误原样抛出：既不当成「项目不存在」，也不当成无权限。, test_verify_project_access_denied_is_classified(), test_verify_project_existing_project_is_true(), test_verify_project_other_client_errors_propagate_unchanged()

### Community 384 - "fixtureFor"
Cohesion: 0.67
Nodes (3): fixtureFiles(), fixtureFor(), loadFixture()

### Community 386 - "_stub_get_not_found"
Cohesion: 0.29
Nodes (7): SSM 值已失效、随后列举被限流：警告在核对出 NotFound 时已经发出，异常照常抛出——事实不随后续失败丢失。, SSM 记录的项目已核对为不存在（NotFound）、随后按名称列举或建立被拒：异常带 `stored_project_missing=True`，…, 项目已被手动删除：返回 False 交给调用方处置。Stubber 只排了 GetProject，任何列举或建立的调用都会因没有排好的响应而失败。, _stub_get_not_found(), test_access_denied_after_the_stored_project_vanished_is_flagged(), test_not_found_warning_is_emitted_before_listing_fails(), test_verify_project_not_found_is_false_without_listing_or_creating()

### Community 387 - "_all_option_dests"
Cohesion: 0.40
Nodes (5): _all_option_dests(), ArgumentParser, parser 及其子 parser 上全部选项字符串与 dest。, `version` 与 `device_farm_project` 由命令派生、有意不给 flag（ADR 0037 决策 6）：手填只会多出写错的机会。…, test_command_derived_context_keys_have_no_flag()

### Community 422 - "devicefarm.py"
Cohesion: 0.16
Nodes (16): NoReturn, AmbiguousProject, DeviceFarmAccessDenied, _error_code(), is_access_denied(), _project_exists(), BaseException, Exception (+8 more)

### Community 424 - "_CdkWritingContext"
Cohesion: 0.21
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 432 - "输出契约：流式 JSON Lines 事件流"
Cohesion: 0.33
Nodes (6): 输出契约：流式 JSON Lines 事件流, reportRefs 不透明产物引用, status 三态 passed/failed/error（wire 只传三态）, step_skipped 独立事件（scope 内短路）, 三通道分离传输（EVENTS_FD / stdout / stderr）, 事件三级 started/done 对齐

### Community 449 - "recordingSurface"
Cohesion: 0.50
Nodes (4): deviceSeam(), fakeDeviceSurface(), recordingSurface(), scopeAgent()

### Community 450 - "_capabilities"
Cohesion: 0.67
Nodes (3): _capabilities(), 本 worker 的能力声明（`--capabilities` 的 stdout，ADR 0036「5.」）。 `min_grace_s` 是 grace…, test_capabilities_declare_session_warmup()

### Community 452 - "fakeUploader"
Cohesion: 0.67
Nodes (3): evidenceHook(), fakeUploader(), scopeIo()

## Ambiguous Edges - Review These
- `终止契约（core 请求 worker 优雅停止）` → `step 顺序 = 书写顺序，keyword 只决定派发`  [AMBIGUOUS]
  docs/adr/0025-plan-module-feature-to-jobs.md · relation: references
- `五层职责切分（用例/产品/执行/浏览器/被测应用）` → `本机应用测试隧道拓扑图`  [AMBIGUOUS]
  docs/diagrams/local-app-testing-tunnel-topology.svg · relation: conceptually_related_to
- `五层职责切分（用例/产品/执行/浏览器/被测应用）` → `README 运行时拓扑图`  [AMBIGUOUS]
  docs/diagrams/readme-runtime-topology.svg · relation: conceptually_related_to
- `架构总览：五层结构、一次 run 的生命周期、包与发行物` → `scenario 到 job 图`  [AMBIGUOUS]
  docs/diagrams/writing-features-scenario-to-job.svg · relation: conceptually_related_to
- `执行与推进模型导览（run/submit × local/cloud）` → `run 执行图`  [AMBIGUOUS]
  docs/diagrams/run-execution.svg · relation: references
- `Cloud Backend Upgrade Windows Diagram` → `Cloud Delivery Identity Diagram`  [AMBIGUOUS]
  docs/diagrams/cloud-backend-upgrade-windows.svg · relation: conceptually_related_to
- `Cloud Delivery Identity Diagram` → `Execution Cloud Cascade Diagram`  [AMBIGUOUS]
  docs/diagrams/execution-cloud-cascade.svg · relation: conceptually_related_to
- `Configuration Env Inheritance Diagram` → `Getting Started Component Ownership Diagram`  [AMBIGUOUS]
  docs/diagrams/getting-started-component-ownership.svg · relation: conceptually_related_to

## Knowledge Gaps
- **1208 isolated node(s):** `背景与问题`, `1. 一个 scope 一个远程访问会话，scenario 之间不复位`, `2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034`, `3. 设备解析、创建与孤儿防护`, `4. 事件契约：`scope_started` 是执行就绪，会话血缘与计量走 `session_opened` / `session_closed`，执行前失败走 `scope_done` 的 scope 级判定` (+1203 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **315 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `终止契约（core 请求 worker 优雅停止）` and `step 顺序 = 书写顺序，keyword 只决定派发`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `五层职责切分（用例/产品/执行/浏览器/被测应用）` and `本机应用测试隧道拓扑图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `五层职责切分（用例/产品/执行/浏览器/被测应用）` and `README 运行时拓扑图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `架构总览：五层结构、一次 run 的生命周期、包与发行物` and `scenario 到 job 图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `执行与推进模型导览（run/submit × local/cloud）` and `run 执行图`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Cloud Backend Upgrade Windows Diagram` and `Cloud Delivery Identity Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Cloud Delivery Identity Diagram` and `Execution Cloud Cascade Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._