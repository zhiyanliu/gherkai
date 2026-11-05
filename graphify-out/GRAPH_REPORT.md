# Graph Report - yaozhou  (2026-11-05)

## Corpus Check
- 450 files · ~924,764 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 9465 nodes · 19449 edges · 611 communities (337 shown, 274 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 1298 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `22bcb800`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- guard.mts
- test_backend_cloud.py
- gherkai_runtime/names.py
- stderr-outlets.test.mts
- test_project.py
- _World
- test_schedule.py
- test_main.py
- test_workers.py
- test_plan.py
- workers.py
- _engine
- _argv
- _run_step
- preflight_cloud_resources
- StepDone
- test_stack.py
- test_evidence.py
- test_deploy_cmd.py
- test_container.py
- ③ 可直接改（CONFIRMED 客观类 571 条，按文件分组；已随本报告落改，逐字改法以同批 diff 为准）
- Path
- Status
- _explain_run
- ArtifactUploader
- ensure_workflow_definition
- ADR-0008
- gherkai_cli/__main__.py
- evidence.py
- ADR 0045: 文档分层与归位
- device_reprobe.md
- resolve_worker_cmd
- 二、code / 配置 / 注释上的客观漂移（83 条，经对抗验证 CONFIRMED，文档复盘不改 code）
- _RecUploader
- test_worker_variant.py
- query_capabilities
- 06-devicefarm-appium.mts
- test_tunnel_cli.py
- ADR 0014: AI 优先断言
- CONTRIBUTING.md: contributor 指南
- main
- parametrize
- cli.py
- test_user_steps.py
- _StampSsm
- LocalRunStore
- Provider
- main
- serialize.py
- atomic_write_json
- device_selection.py
- gherkai_runtime/__init__.py
- test_user_docs.py
- test_cloud_reconcile.py
- video.py
- test_interrupt_model.py
- appium.mts
- textui.py
- BackendStack
- guard.test.mts
- settings.py
- .toUser
- _StderrScan
- DeviceSurface
- manifest.json
- evidence.mts
- test_artifact_upload.py
- _doc_rules.py
- _is_transient_network
- report_store/local.py
- JobSource
- test_devicefarm.py
- build_engines
- main
- sigv4Fetch
- gherkai 变更记录 (CHANGELOG)
- submission.py
- Guard
- RunState
- warmupSession
- select
- test_stores.py
- test_detached_launcher.py
- log
- _presend_act_siblings
- parametrize
- test_cli_json_contract.py
- 决策
- wire.py
- README Video Specs
- TypeScript Build Config
- AppiumInterface
- limits.mts
- Composition Root Architecture
- test_project_config.py
- test_adr_hygiene.py
- test_fargate_engine.py
- Video Material Files
- _run_with_refs
- 03-midscene-grounding.ts
- arg_offload.py
- skill_install.py
- 决策
- Run Store Persistence Ports
- event-sink.mts
- deterministic
- 决策
- 决策
- interface.mts
- test_precheck.py
- dependencies
- .add_arguments
- plan
- Diagram Build Script
- ArtifactUploader
- _FakeSink
- evidence.test.mts
- ADR 0043：驱动 gherkai 的 agent skill
- release_notes.py
- app.mts
- gherkai_deploy_aws/names.py
- Event Wallclock Analysis
- Release Notes Guards
- RuntimeError
- test_skill.py
- deterministic.py
- run-scope.test.mts
- Dist Metadata Checks
- Target
- test_tunnel_warmup.py
- probe.mts
- Media Conversion Verification
- package.json
- finalize.test.mts
- ADR 0024: worker–core 协议
- SubprocessWorkerHandle
- render_skill_contract.py
- DynamoDB Events Transport ADR
- Path
- 决策
- tunnel-warmup.test.mts
- minimax_narration.py
- test_skill_deploy_tokens.py
- ._run_cdk
- Stateless Run Core Model
- test_deterministic.py
- argument.mts
- test_user_facing_messages.py
- S3ResultStore
- session.test.mts
- 0050. 确定性 step 多句柄注册与测试分层
- xcuitest.test.mts
- use_color
- artifact-upload.test.mts
- config.py
- test_lambda_asset.py
- engines-matrix.test.mts
- test_lifecycle_states.py
- e2e_harness.py
- ECS Task Timing Capture
- test_definition_schema.py
- ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）
- render.py
- Graphify Refresh Script
- uiautomator2.mts
- job-source.mts
- read-points.test.mts
- Cooperative Stop Design
- image_tag
- Doc Rules Check
- test_devicefarm_client_placement.py
- adapters.contract.test.mts
- _release_cmp
- Engine Port & Job Planning
- Scope Tag Parsing
- reconcile.tick（推进器共享入口）
- Context Glossary Guards
- container_name
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- _render_status
- _print_artifact_lines
- session.mts
- AppiumSession
- exerciseSession
- Echo Test Worker
- Cloud Infra Self-Check
- _ClientError
- devDependencies
- 移动真机支持（1.5）：实施进度总纲
- FargateEngine
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- Gherkin Parse Seam
- files
- Repository Metadata
- test_subprocess_engine.py
- .doRelease
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- _job_def
- compose.py
- Architecture Diagrams
- Slide Frame SSIM Checks
- _ssm_params
- AgentCore CDP Script
- ② 请裁定（28 条发现聚成 17 个决策项，编号可一句话回；code 侧条目同时移交 code-health）
- _installed_version
- Pre-commit Hook Script
- core/tests/test_redact.py
- SqliteEventLog
- Adapters Package
- user-steps.test.mts
- test_tunnel.py
- .acquireSteps
- Step Matching & Plan Annotation
- build_fargate_engines
- agentcore-sigv4.test.mts
- no-device-deps.test.mts
- WorkerNetworkError
- 云端后端用户文档
- _role_statements
- precheck.mts
- gemini_image.py
- Index Wait Script
- gherkai Workspace Root
- _StubEcs
- error-text.mts
- ContainerError
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
- surface-desktop.mts
- job-source.test.mts
- CONTENT_TYPES
- test_lambda_handlers.py
- bin.mts
- _Worker
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- ⑦ 事实族横切记录（18 族）
- run_scope.py
- test_argument.py
- xcuitest.mts
- Path
- 项目约定
- RunState
- .run_scope
- ADR 0044: 引擎模型选择与覆盖
- warmup.mts
- Artifact Uploader Component
- RunMeta
- appium.test.mts
- desktopFactory
- runScope
- test_event_log_recording.py
- Job
- test_report_store.py
- _Recorder
- device_reprobe 使用说明（Midscene 设备模块的真机重新探测）
- DeviceFarmSessionBlock
- user-steps.mts
- ensure_app_object
- browser-session-timeout.test.mts
- test_engines_matrix.py
- _FakeResult
- detached.py
- probe.test.mts
- web-context.mts
- .actionSpace
- runStep
- run_evals.py
- _FakeSink
- parse_iso
- Event
- Job
- events_pk
- interface.test.mts
- _UnavailableEngine
- read_project_arn
- .navigate
- list_open_sessions
- .execute
- app.test.mts
- warmup.test.mts
- TargetSurface
- _presentation_is_environment_independent
- finalize.mts
- .__init__
- _MissingThenStoppedEcs
- app_upload.py
- .warmup
- device/surface.test.mts
- WebdriverCtx
- scan
- Template
- register
- parent-watchdog.test.mts
- reconciler.py
- _all_option_dests
- openai
- web-context.test.mts
- _interrupt_prompt
- parent-watchdog.mts
- wdio-log.mts
- wdio-log.test.mts
- cli/tests/conftest.py
- ADR 0011: AgentCore 浏览器 system default vs custom
- CapabilityProbe
- severity 数值序（_STATUS_SEVERITY）
- .waitRunning
- DeterministicCtx
- AppiumInterface
- DeterministicKeywordMismatch
- precheck.test.mts
- check_node
- list_registry
- _build_parser
- WebdriverApp
- deviceFarmApi
- test_compose.py
- no-artifacts.test.mts
- patch-package 补丁 @cucumber+cucumber+13.0.0
- ScopeTerminationError
- ADR-0019
- test_sqlite_event_log.py
- test_code_comments.py
- test_provider.py
- _FakeNovaAct
- _ClientError
- ADR-0025
- ADR-0026
- @playwright/test
- DEVICE_SESSION_FILE
- worker/surface.test.mts
- DEVICE_SESSION_REPORT_KIND
- Job
- scripts
- _spawn_and_wait_ready
- DeviceSessionRecord
- limits.test.mts
- ADR-0051
- ADR-0052
- ProviderMinutes
- @aws-sdk/client-s3
- @aws-sdk/credential-providers
- @aws-sdk/protocol-http
- ScaleSource
- SessionClosedFact
- SessionDeviceInfo
- SessionOpenedFact
- SessionOrigin
- JobResult
- SessionRelease
- playwright
- tsx
- _FakeEcs
- WebContextRecord
- session-name.test.mts
- image_token_probe.mts
- DeterministicKeywordMismatch
- deterministic.steps.mts
- _InterruptState
- test_technical_docs.py
- ._pump
- deterministic_steps.py
- ADR 0013: 跨引擎共享边界
- test_warmup_page_script_classifies_only_401_as_denied
- test_run_status_agrees_between_schedule_and_project_full
- scenario_key
- browser_session_timeout_s
- .preflight
- _Clock
- _FakeTable
- parametrize
- trigger_eval.py
- .hideKeyboard
- test_plan_config_defaults_derive_from_builtin_acquire_budget
- _TrajNova
- ArgumentParser
- NamedTuple
- url_matches.py
- deploy.py
- BaseException
- test_report_files_keep_explicit_mode_under_tight_umask
- build_local_stores
- _isolated_aws_env
- test_module_never_creates_or_stops_sessions
- deterministic
- _events_table_actions
- unspecified_message
- RunMeta
- RunState
- RunMeta
- 输出契约：流式 JSON Lines 事件流
- Job
- 文档健康度复盘 · 第九轮 · 待批报告
- _advancer_stmts
- RunMeta
- test_stderr_redaction.py
- RunResult
- parametrize
- Path
- _joined_refs
- doc-health 第九轮移交 code-health 的输入：code 侧客观发现与「改 code、ADR 不动」的裁定
- CloudTarget
- _delayed_stopped_ecs
- devicefarm.py
- _Calls
- JobState
- ScopeDone
- SessionRecord
- parseXmlTree
- ACQUIRE_INTERRUPTED_MESSAGE
- ACQUIRE_TIMEOUT_MESSAGE
- AddressAttempt
- ADR 0043: 随 CLI 发行的 agent skill
- AgentFactory
- APP_LOCATION_MISSING_MESSAGE
- ConnectOutcome
- ConnectRequest
- DeviceChoice
- DeviceParts
- DevicePartsEnv
- DevicePartsFactory
- DeviceSurfaceOptions
- FinalizeHooks
- HANDLER_KIND_MISMATCH_MESSAGE
- HELPER_REJECTED_AGAIN_MESSAGE
- HELPER_REJECTED_NO_TIME_MESSAGE
- LIVENESS_FAILED_MESSAGE
- ADR-0039
- Timers
- ADR-0042
- ADR-0044
- ADR-0050
- ADR-0051
- ADR-0052
- Outcome
- PRE_STEP_FAILED_MESSAGE
- ProbeConclusion
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0050
- surface.mts
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
- AdapterEntry
- Status
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
- ADR-0032
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
- runOnDevice
- ReadyState
- RemoteSession
- Path
- RESTORE_FAILED_TAIL
- .attempt
- RunningSession
- verify_project
- SESSION_LOST_BEFORE_START_MESSAGE
- diffAgainstFixture
- SESSION_LOST_MESSAGE
- fixtureFor
- SurfaceConfig
- WEB_CONTEXT_ON_APP_MESSAGE
- WEB_CONTEXT_PROBE_ERROR_MESSAGE
- WEB_CONTEXT_UNAVAILABLE_MESSAGE
- WebContextVerdict
- BaseException
- datetime
- WindowOutcome
- 执行与推进模型导览（run/submit × local/cloud）
- JobResult
- RunResult
- RunState
- SqliteEventLog
- RuntimeError
- SubprocessEngine
- Exception
- Job
- RunMeta
- Exception
- parametrize
- Path
- Popen

## God Nodes (most connected - your core abstractions)
1. `main()` - 290 edges
2. `Job` - 165 edges
3. `RunMeta` - 132 edges
4. `RunState` - 119 edges
5. `③ 可直接改（CONFIRMED 客观类 571 条，按文件分组；已随本报告落改，逐字改法以同批 diff 为准）` - 115 edges
6. `Provider` - 109 edges
7. `Status` - 107 edges
8. `JobResult` - 106 edges
9. `schedule()` - 106 edges
10. `JobState` - 100 edges

## Surprising Connections (you probably didn't know these)
- `--interrupt 中断时机矩阵` --shares_data_with--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `e2e_harness.py（opt-in 手动端到端验证脚本）` --calls--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `test_skill.py（skill 产品面与真值护栏）` --references--> `render()`  [EXTRACTED]
  docs/adr/0043-agent-skill-for-driving-gherkai.md → tools/render_skill_contract.py
- `ADR 0043：驱动 gherkai 的 agent skill` --references--> `render()`  [EXTRACTED]
  docs/adr/0043-agent-skill-for-driving-gherkai.md → tools/render_skill_contract.py
- `render()` --references--> `docs/internals/cli-json-contract.md（机读字段级参考页）`  [EXTRACTED]
  tools/render_skill_contract.py → docs/adr/0045-documentation-layering-and-placement.md

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

## Communities (611 total, 274 thin omitted)

### Community 0 - "guard.mts"
Cohesion: 0.07
Nodes (31): AFTER_RESULT_UNKNOWN_MESSAGE, CommandGuardArgs, commandGuardFactory, CONNECTION_ERROR_CODES, CONTEXT_SWITCH_COMMANDS, copyOutcome(), Derivation, FINALIZING_COMMAND_MESSAGE (+23 more)

### Community 1 - "test_backend_cloud.py"
Cohesion: 0.04
Nodes (119): _definition(), _fake_schedule_factory(), _FakeS3, _patch_cloud_handles(), _patch_skew(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, **戳只读一次**：skew 闸读的那个戳原样喂给 variant 解析（提示语要按 skew 分叉，ADR 0038）—— 不再为提示语二次读同一个 SSM… (+111 more)

### Community 2 - "gherkai_runtime/names.py"
Cohesion: 0.07
Nodes (38): Match, project_name(), 云端 Device Farm 项目名 `{prefix}devices`。, default_name(), device_farm_interactive_endpoint_resource(), device_farm_project_id(), device_farm_session_arn_prefix(), job_timeout_schedule_prefix() (+30 more)

### Community 3 - "stderr-outlets.test.mts"
Cohesion: 0.06
Nodes (66): ALIAS_ASSIGNMENTS, Bindings, bindingsOf(), CONSOLE_STDERR, DECLARATION_KINDS, describe(), destructuredKey(), dynamicImportSpecifier() (+58 more)

### Community 4 - "test_project.py"
Cohesion: 0.06
Nodes (78): plan_next(), project(), project_full(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, _ev(), _exit() (+70 more)

### Community 5 - "_World"
Cohesion: 0.08
Nodes (11): _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）与导航原语…, 引擎的导航原语（内建导航条目用它打开地址，ADR 0020 第 3 条）：Nova 用 SDK 的 `go_to_url`。, _check_wire_shape(), _Client, _Cm, _Nova, core/gherkai_core/wire.py 对会话事件的校验逐条重述，外加桌面专属的两条（不带 device，不带 observedS 与… (+3 more)

### Community 6 - "test_schedule.py"
Cohesion: 0.09
Nodes (108): 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。, EngineResolver：所有引擎都返回同一个 FakeEngine（测试不区分引擎）。 (+100 more)

### Community 7 - "test_main.py"
Cohesion: 0.02
Nodes (137): _cloud_backend_ok(), _det_feature(), _doctor_cloud_json(), _doctor_devices_cloud(), _fake_locator(), _fake_worker_cmd(), _miss(), _no_provider() (+129 more)

### Community 8 - "test_workers.py"
Cohesion: 0.06
Nodes (94): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, --json 下 stdout 只留一个 JSON 文档：skew 提示 / 读失败诊断走 err（stderr），文本输出行为不变。 (+86 more)

### Community 9 - "test_plan.py"
Cohesion: 0.08
Nodes (47): _cfg(), _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 低于下限的改法要按删掉 tag 后真正接替的来源给：--default-job-timeout 也低于下限时不能只说「删 tag 走缺省」（删了仍被它拒）。, 「任一成员标了即整个 scope 生效」不只看首个成员：带 tag 的成员排在后面也生效。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否… (+39 more)

### Community 10 - "workers.py"
Cohesion: 0.04
Nodes (94): Aws, cleanup_pass(), _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable() (+86 more)

### Community 11 - "_engine"
Cohesion: 0.11
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 12 - "_argv"
Cohesion: 0.08
Nodes (39): _argv(), _context_pairs(), _deploy(), _parse_destroy(), 按动作取 Provider 方法与 args（destroy 走真 destroy parser；synth 给导出目录）。, diff / --synth-only / destroy 不建立项目：SSM 有值即沿用（diff 先用 GetProject 核对、项目还在），交给…, 参数不存在（含 stack 还不存在）→「待建立」占位，仍不建立项目；没有记录也就没有可核对的项目。diff 另提示用于计算变更集的模板不含…, SSM 有记录、GetProject 回 NotFound（项目被手动删除）→ diff 以「待建立」占位并警告：用有权限的凭证 deploy… (+31 more)

### Community 13 - "_run_step"
Cohesion: 0.10
Nodes (51): _classify_act_error(), _cost_from_result(), 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, 报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。, 派发执行一个 step，发出 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, _run_step(), _done(), _FakeNova (+43 more)

### Community 14 - "preflight_cloud_resources"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 15 - "StepDone"
Cohesion: 0.08
Nodes (37): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+29 more)

### Community 16 - "test_stack.py"
Cohesion: 0.04
Nodes (21): _bucket_lifecycle_rules(), BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, 产物桶的生命周期规则**全集**恰为 expire-job-in 与 expire-apps 两条（ADR 0033、ADR 0051 决策 9），与…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler / kicker）的角色都不读 SSM 参数：definition 缺 `worker_task_defs` 按定义违约标… (+13 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.09
Nodes (46): ArtifactUploader, _get_uploader(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), list, parametrize (+38 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 前端自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 19 - "test_container.py"
Cohesion: 0.06
Nodes (45): digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。 (+37 more)

### Community 20 - "③ 可直接改（CONFIRMED 客观类 571 条，按文件分组；已随本报告落改，逐字改法以同批 diff 为准）"
Cohesion: 0.02
Nodes (115): ③ 可直接改（CONFIRMED 客观类 571 条，按文件分组；已随本报告落改，逐字改法以同批 diff 为准）, `CHANGELOG.md`（12）, `CLAUDE.md`（1）, `cli/DEVELOPMENT.md`（9）, `cli/gherkai_cli/skills/gherkai/references/cloud-backend.md`（4）, `cli/gherkai_cli/skills/gherkai/references/deterministic-steps.md`（2）, `cli/gherkai_cli/skills/gherkai/references/engines.md`（8）, `cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md`（6） (+107 more)

### Community 21 - "Path"
Cohesion: 0.17
Nodes (26): 终态真源不漂移（ADR 0031 决定一·补末条）：三处消费方全引…, test_terminal_status_consumers_use_core_single_source(), 交互 HTML 只对发布到 Pages 的图入库：git 跟踪的每个 <name>.html 必须有同名图源，且在 index.html 里有链接 （发布由…, test_published_interactive_html_is_tracked_and_indexed(), Path, assert_no_installed_skill(), assert_prepared(), assert_stage_isolated() (+18 more)

### Community 22 - "Status"
Cohesion: 0.03
Nodes (191): RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, render_text(), 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…, 跨包措辞护栏（ADR 0051 决策 4 / 0031 决定六）：scope 级 error 后合成的…, 设备 job（ADR 0051 决策 7；0034 机制二 U 集）：设备占用时长与缺计量会话数、未确认停止的会话名、结果未知的创建尝试单独标；桌面 job… (+183 more)

### Community 23 - "_explain_run"
Cohesion: 0.05
Nodes (57): _events_db_with_unfinished_scenario(), _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。 (+49 more)

### Community 24 - "ArtifactUploader"
Cohesion: 0.11
Nodes (13): ArtifactUploader, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 把文件交给后台队列顺序上传（**不阻塞调用方**）；no-op 时直接返回。 调用点在 `step_done` **emit 之后**（ADR 0042…, 有界等队列传完（含在途那一项）：全部处理完 True，超时 False（剩下的交给 flush 兜）。 收尾（scope 末 /…, 队列线程主体：FIFO 逐个传，**绝不因单项失败而死**（死了意味着后面的截图全不传且无人察觉）。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 本机 no-op 路径：截图就在本地，队列/排空都是直接返回（不起线程、不碰 boto3）。 (+5 more)

### Community 25 - "ensure_workflow_definition"
Cohesion: 0.06
Nodes (46): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, _fmt_seconds(), 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+38 more)

### Community 27 - "gherkai_cli/__main__.py"
Cohesion: 0.04
Nodes (91): _available_step_targets(), _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_doctor(), _cmd_explain(), _cmd_list_deterministic() (+83 more)

### Community 28 - "evidence.py"
Cohesion: 0.07
Nodes (48): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Any, Path (+40 more)

### Community 29 - "ADR 0045: 文档分层与归位"
Cohesion: 0.20
Nodes (21): _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏）, test_user_docs.py（用户文档与图源护栏）, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0045: 文档分层与归位, CONTEXT.md 严格词表与术语变更顺序（决策八）, archify 图流程（JSON 图源 + 导出 SVG 入库） (+13 more)

### Community 30 - "device_reprobe.md"
Cohesion: 0.08
Nodes (25): Attempt, Browser, CALL_ORDER, Captured, CaseResult, CaseStatus, ContractCase, ContractFixture (+17 more)

### Community 31 - "resolve_worker_cmd"
Cohesion: 0.06
Nodes (33): _ask_worker(), _find_worker_spec(), 一个引擎 worker 的拉起方式即定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂 `SubprocessEngine`；**cwd…, worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…, 定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退出码交调用点。 **继承 RuntimeError…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。 (+25 more)

### Community 32 - "二、code / 配置 / 注释上的客观漂移（83 条，经对抗验证 CONFIRMED，文档复盘不改 code）"
Cohesion: 0.04
Nodes (49): `cli/gherkai_cli/__main__.py`（11）, `cli/gherkai_cli/render.py`（1）, `cli/pyproject.toml`（1）, `cli/tests/test_main.py`（2）, `core/gherkai_core/adapters/_atomic.py`（1）, `core/gherkai_core/adapters/event_log/sqlite.py`（2）, `core/gherkai_core/adapters/subprocess_engine.py`（1）, `core/gherkai_core/errors.py`（1） (+41 more)

### Community 33 - "_RecUploader"
Cohesion: 0.06
Nodes (23): _drain_evidence_uploads(), 收尾：**有界**等 evidence 截图的后台队列传完（ADR 0042 决策一）。best-effort、绝不抛。…, _FakeBrowserClient, _install_browser_client(), _RaisingSink, 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 零 evidence（单例还没造）→ 直接返回；且**不在退出路径上现造上传器**（半注入会 fail-loud 抛）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。 (+15 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (47): ecr_repo_name(), 引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag…, （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…, task_def_name(), worker_image_key(), test_ecr_repo_name_is_task_def_name(), aws() (+39 more)

### Community 35 - "query_capabilities"
Cohesion: 0.05
Nodes (53): engine_min_grace(), _is_finite_number(), match_deterministic(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, 有限的 int / float（bool 单独挡；超出 float 范围的大整数按「不是有限数」处理，不让 math.isfinite 的…, targets 数组的形态校验（ADR 0049 决策 1）：顶层 targets 必有（缺键由调用方按版本不一致拒绝），step 级只在键存在时调用；显式… (+45 more)

### Community 36 - "06-devicefarm-appium.mts"
Cohesion: 0.16
Nodes (22): caps(), connect(), df, Driver, MARKERS, nativeMarkers(), navigateTo(), PLATFORM (+14 more)

### Community 37 - "test_tunnel_cli.py"
Cohesion: 0.08
Nodes (47): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, 不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。, 隧道起不来（如 authtoken 缺失）→ 给退出码 2「没开始执行就被拒」，不产生引擎费用。, local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。 (+39 more)

### Community 38 - "ADR 0014: AI 优先断言"
Cohesion: 0.08
Nodes (33): CLAUDE.md（项目约定）, CONTEXT.md（领域概念与术语）, CONTRIBUTING（contributor 入口）, ADR 0001: 范围限于英文 UI, 概念：非英文应用用 @engine:midscene 路由, 概念：Nova Act 中文词语级文本匹配短板, ADR 0007: 程序化登录，HITL 作逃生口, ADR 0010: spike 作为对等基准 (+25 more)

### Community 39 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.07
Nodes (42): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, cli 包 contributor 文档, skill 参考：CLI --json 字段契约, skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法 (+34 more)

### Community 40 - "main"
Cohesion: 0.21
Nodes (33): amapSteps(), androidAppTypingProbe(), appSteps(), capProbe(), deeplinkCase(), deeplinkProbe(), deeplinkRound2(), deeplinkRound3() (+25 more)

### Community 42 - "cli.py"
Cohesion: 0.07
Nodes (33): BaseException, _error_code(), _has_aws_credentials(), _is_credential_error(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client(), Exception (+25 more)

### Community 43 - "test_user_steps.py"
Cohesion: 0.06
Nodes (53): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+45 more)

### Community 44 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 45 - "LocalRunStore"
Cohesion: 0.05
Nodes (62): LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR… (+54 more)

### Community 46 - "Provider"
Cohesion: 0.06
Nodes (58): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 留的口子（ADR 0038「命令族」）：**尚未提供**，以退出码 2 结束并说清为什么与将来怎么落。…, _AbsentEngine, _parse(), 用了 --profile 时，查项目 ARN 的命令带同一个 --profile（与 doctor 的停止命令同一做法），照抄不会落到另一套凭证。, 走**真 parser**、按真实接线顺序拼（前端先声明命令面 flag，provider 再贴自己的选项）——不用 SimpleNamespace 手捏…, 别的前端（或编程式调用）没给 `--allow-vpc-change` 时**fail-closed**：取值不符照拦、不因缺 flag 就放行。 (+50 more)

### Community 47 - "main"
Cohesion: 0.03
Nodes (106): main(), _capturing_schedule(), _interrupting_schedule_factory(), miss 只连坐**用到它**的 run：novaact-only 的 run 在 midscene 未装（dev 常态）下照常运行并以退出码 0 结束。…, 记录 build_engines 收到的 kwargs（仍调真实实现，保 cmd/env 接线真实）。 每次调用都断言带了 run id：同步 run…, `--steps-dir` → ①绝对化后注给 worker（build_engines 的 steps_dir → env…, 末级默认 `./steps`（相对**提交时** CWD）：存在才用、不存在则 None（「没这个目录」是多数项目的常态）。 None 时…, 显式给的（flag/env）不是目录 → 以退出码 2 结束，**不静默忽略**：忽略等于把该目录里的确定性 step 悄悄换成 AI 判定、run… (+98 more)

### Community 48 - "serialize.py"
Cohesion: 0.05
Nodes (57): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, RunStore adapters (local / ddb), _argument_from_dict() (+49 more)

### Community 49 - "atomic_write_json"
Cohesion: 0.13
Nodes (20): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+12 more)

### Community 50 - "device_selection.py"
Cohesion: 0.09
Nodes (32): ProjectConfig, 读出来的项目配置。`path` 为 None 表示没有配置文件（缺省位置不存在不算错，决策 1），四节都为空。 `common` / `cloud` 的值保持…, 路径类值相对配置文件所在目录绝对化（决策 2）；没有配置文件时原样返回（不该被调到，保险起见）。, 给 plan 层的纯数据表：别名 → 平台 → 包名或 bundle id（core 据此核对 @app，不带文件路径）。, acquire_timeout_for(), _arn_kind(), billing_method_for(), build_device_request() (+24 more)

### Community 51 - "gherkai_runtime/__init__.py"
Cohesion: 0.09
Nodes (29): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的四件产物：映射过的 definition + 隧道模式的额外请求头 + 会话预热地址 + 隧道事实（收尾凭据）。…, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, start_tunnel_for_jobs() (+21 more)

### Community 52 - "test_user_docs.py"
Cohesion: 0.06
Nodes (48): changelog_unreleased(), CHANGELOG 交给退役词表与口头语表扫的部分，即第一个已发行版本节之前的内容。…, _absolute(), _default_model_claims(), _default_model_ids(), _link_targets(), 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`、演示材料…, 提取器本身的护栏：同僚复核三轮列出的漏网与误报形态都要按 CommonMark 的渲染结果判——会渲染成链接的提出来，不会渲染成链接的不提。 (+40 more)

### Community 53 - "test_cloud_reconcile.py"
Cohesion: 0.06
Nodes (49): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写… (+41 more)

### Community 54 - "video.py"
Cohesion: 0.32
Nodes (17): cues(), digest(), link_chapter_title_track(), packets(), probe(), protected_state(), Path, Confirm the first slide at frame zero, hard cuts, and the closing fade. (+9 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.04
Nodes (61): _aggregate(), _attach_evidence(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _emit_step_done(), _on_signal(), _pid_alive(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不… (+53 more)

### Community 56 - "appium.mts"
Cohesion: 0.06
Nodes (31): AppiumConnectorOptions, AppiumSessionArgs, AUTOMATION_NAMES, BROWSER_NAMES, CLIENT_TIMEOUTS, clientOptions(), ClientTimeouts, commandFailureKind (+23 more)

### Community 57 - "textui.py"
Cohesion: 0.11
Nodes (30): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。, 深度优先找第一个 label 含 needle 的节点（测试与诊断用）。, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，… (+22 more)

### Community 58 - "BackendStack"
Cohesion: 0.09
Nodes (19): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, `-c device_farm_project=` 给的项目 ARN；缺省或等于「待建立」占位时返回 None。 值由命令派生、不给…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。 (+11 more)

### Community 59 - "guard.test.mts"
Cohesion: 0.07
Nodes (16): adapterWith(), codeError(), FakeElement, FakeExec, FakeServer, fakeWebDriver(), Harness, inStep() (+8 more)

### Community 60 - "settings.py"
Cohesion: 0.14
Nodes (21): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, apply_project_config(), configurable_keys(), convert_config_value(), find_option_action(), _is_repeatable(), option_actions(), option_origin() (+13 more)

### Community 61 - ".toUser"
Cohesion: 0.36
Nodes (6): key(), isDataLeaf(), isObjectLike(), isPlainContainer(), isPlainData(), isThenable()

### Community 62 - "_StderrScan"
Cohesion: 0.10
Nodes (23): Attribute, Call, _calls_redact(), _is_sys_module(), _is_writer(), _Outlet, AST, _qualified() (+15 more)

### Community 64 - "manifest.json"
Cohesion: 0.06
Nodes (35): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+27 more)

### Community 65 - "evidence.mts"
Cohesion: 0.08
Nodes (36): actionsOf(), buildEvidence(), BuildEvidenceInput, controlItemOf(), deviceKeysOf(), ENGINE, errorTextOf(), EVIDENCE_KIND (+28 more)

### Community 66 - "test_artifact_upload.py"
Cohesion: 0.09
Nodes (35): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, `.xml` → application/xml（ADR 0042 决策一，两引擎同规则同步改）：设备目标的原始控件树是 .xml（ADR 0051 决策…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 半注入(有桶缺 NOVA_LOGS_DIR)→ 装配矛盾 fail-loud(静默 no-op 会让产物随容器盘销毁必丢,ADR 0033)。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。 (+27 more)

### Community 67 - "_doc_rules.py"
Cohesion: 0.05
Nodes (64): ai_side_docs(), all_markdown(), bare_flags(), classify(), clean_flag(), CommandSpan, comment_blocks(), comment_prose_lines() (+56 more)

### Community 68 - "_is_transient_network"
Cohesion: 0.14
Nodes (28): _is_transient_network(), 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是 NovaAct 的…, 造一个 botocore ClientError（response 里带 Error.Code /…, _target_closed(), test_agentcore_permanent_wrapping_chain_not_transient() (+20 more)

### Community 69 - "report_store/local.py"
Cohesion: 0.16
Nodes (11): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…, 若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 **公开小工具**（本模块 href… (+3 more)

### Community 70 - "JobSource"
Cohesion: 0.09
Nodes (11): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, Workflow 的 with 外壳：进入照常（失败即抛，此时没有会话）；退出时 SDK 要向 Nova Act 服务更新工作流运行的状态，这一次 RPC…, _WorkflowGuard (+3 more)

### Community 71 - "test_devicefarm.py"
Cohesion: 0.18
Nodes (27): 找回或建立项目 `{prefix}devices`（只供 `deploy` 在 cdk 之前调用，ADR 0051 决策 10「项目」）。…, resolve_or_create_project(), _assert_warning(), _enter(), _project(), parametrize, Python 侧 Device Farm 客户端的行为（ADR 0051 决策 10「项目」「调用归属」、决策 6 的 doctor 列出未结束会话）。 用…, SSM 值已失效时恰发出一句警告（点名旧 ARN 与要找的名称）；没有 SSM 值时一句都不发。 (+19 more)

### Community 72 - "build_engines"
Cohesion: 0.05
Nodes (48): Engine, FeatureSource, build_engines(), build_local_event_log(), events_db_path(), load_feature(), local_artifact_locations(), make_resolver() (+40 more)

### Community 73 - "main"
Cohesion: 0.10
Nodes (49): main(), StartBrowserSession 的请求名（规则见上）。`attempt` 是尝试序号（非负整数，起始值由调用方定）；`max_length` 缺省取…, session_request_name(), _assert_paired(), _closed(), _job(), _opened(), parametrize (+41 more)

### Community 74 - "sigv4Fetch"
Cohesion: 0.09
Nodes (17): BASE_URL, main(), makePng(), REGION, ADR-0033, BASE_URL, main(), ADR-0033 (+9 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.09
Nodes (30): gherkai 变更记录 (CHANGELOG), gherkai destroy, --expose-local 隧道模式, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, gherkai deploy push-worker / list-workers (+22 more)

### Community 76 - "submission.py"
Cohesion: 0.09
Nodes (32): progress(), 命令行的进度与诊断输出（ADR 0047）：一个函数，供 `__main__` 与各编排模块共用。, 进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `gherkai run ……, account_of(), ARN 的账号段（项目 ARN 的第五段）。, config_layers(), identity_layers(), `compose.resolve_aws_identity` 的配置文件层（region / profile 排在环境变量之后，ADR 0053 决策 2）。 (+24 more)

### Community 77 - "Guard"
Cohesion: 0.17
Nodes (6): commandFailedMessage(), ExecutionWindow, failure(), Guard, lostFailure(), rejected()

### Community 78 - "RunState"
Cohesion: 0.02
Nodes (144): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端：补取经 compose.build_cloud_event_log（events 表 Query）；表读不到或缺权限时只在 aborted_hint…, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_explain_cloud_recovers_from_events_table_and_reports_missing_permission() (+136 more)

### Community 79 - "warmupSession"
Cohesion: 0.36
Nodes (5): leaveWarmupPage(), oneLine(), waitForMarker(), WarmupPage, warmupSession()

### Community 80 - "select"
Cohesion: 0.27
Nodes (9): availabilityRank(), closestVersion(), compareVersions(), eligible(), matchesVersionFamily(), noMatchingDeviceMessage(), segments(), select() (+1 more)

### Community 81 - "test_stores.py"
Cohesion: 0.09
Nodes (36): dict → RunMeta。第一步核结构版本（不等于本读端支持的即抛…, run_meta_from_dict(), _is_positive_number(), _is_text(), Job, 测试目标的定义层结构校验（ADR 0048 决策 3）。 两个时点各核一次：组合根写 definition 之前（run / submit…, definition 里的一个 job 必须是完整形态，否则抛 DefinitionContractError（推进器与 worker…, validate_job_definition() (+28 more)

### Community 82 - "test_detached_launcher.py"
Cohesion: 0.07
Nodes (54): LocalRunStore, now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, build_local_reconcile(), RunMeta, SqliteEventLog, SubprocessEngine, per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。… (+46 more)

### Community 83 - "log"
Cohesion: 0.10
Nodes (23): _leave_warmup_page(), _one_line(), Exception, 隧道会话预热（ADR 0051 决策 13）：worker 在第一个 scenario 之前对预热地址导航一次换到会话 cookie，并按页面的可见结果归因。…, 预热期间收到停止信号（ADR 0024 flag-only 协作停）：调用方按停止路径收尾，不算失败、不发 scope_done。, 对 `page` 导航预热地址、等页面标题落成四个标记之一；返回 None 表示就绪，否则返回归因与产品语言的消息。 `page` 是 Playwright…, 就绪后离开预热页到 about:blank：令牌不留在当前文档地址（Nova Act 每步规划请求带当前地址、确定性 step 能读 page.url）。…, _wait_for_marker() (+15 more)

### Community 84 - "_presend_act_siblings"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 添加到 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…, act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _traj_refs(), _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 85 - "parametrize"
Cohesion: 0.10
Nodes (23): 云端 Device Farm 项目 ARN 的 SSM 路径（ADR 0051 决策 10、ADR 0033 资源清单第 11 条）。 写者是 stack…, ssm_device_farm_project_path(), parametrize, `gherkai_deploy_aws.names` 的 Device Farm 与安装包命名：re-export 与产品本体是同一个对象，SSM…, test_device_farm_and_app_names_are_reexported_from_runtime(), test_ssm_device_farm_project_path_is_the_shared_key(), _assert_record_read_hint(), parametrize (+15 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.15
Nodes (23): _assert_check_names_documented(), _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, doctor 本机各段的替身：两个引擎都定位得到、自述带全部键，没有部署 provider。, 项名是 `name` 的**值**，键名护栏照不出它：把按引擎后缀的项名归一成 `<engine>` 形态后逐个核对契约页里写了。 (+15 more)

### Community 87 - "决策"
Cohesion: 0.10
Nodes (20): 0051. 远程访问会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034 (+12 more)

### Community 88 - "wire.py"
Cohesion: 0.03
Nodes (80): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, 把 SubprocessEngine 的原始事件行与退出记录旁路落 SqliteEventLog（ADR 0042 决策七、ADR 0034）。…, SqliteEventLog（ADR 0034；ADR 0042 决策七起同步 run 也写）：本机后端的持久事件通道。 worker 事件（原始 ADR…, FargateWorkerHandle (+72 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 91 - "AppiumInterface"
Cohesion: 0.25
Nodes (4): AppiumInterface, elementId(), iosTypingProbe(), pngSize()

### Community 92 - "limits.mts"
Cohesion: 0.05
Nodes (37): ADR-0044, ADR-0049, ADR-0051, ADDRESS_CAPTURE_BUDGET_MS, APP_PRESIGN_EXPIRES_S, BUSY_BACKOFF_CAP_MS, BUSY_BACKOFF_INITIAL_MS, CONTROLS_CAPTURE_BUDGET_MS (+29 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_project_config.py"
Cohesion: 0.07
Nodes (68): _fake_schedule_factory(), 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job…, ADR 0048 决策 4：假 worker 自述只有桌面网页，标了 @device:android 的 scope 在 plan 与 run…, test_device_target_rejected_by_plan_and_preflight_when_engine_lacks_target(), _android_caps(), _android_env(), _app_project(), _feature() (+60 more)

### Community 95 - "test_adr_hygiene.py"
Cohesion: 0.12
Nodes (28): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, 指向 journey 文件的规则正反例：仓库路径与相对路径（`../`、`./`、行首或标点之后）都命中；目录名本身、别的以 journey… (+20 more)

### Community 96 - "test_fargate_engine.py"
Cohesion: 0.10
Nodes (30): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。 (+22 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "_run_with_refs"
Cohesion: 0.16
Nodes (18): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, s3_report_store(), _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto… (+10 more)

### Community 99 - "03-midscene-grounding.ts"
Cohesion: 0.21
Nodes (11): ADR-0010, BASE_URL, main(), mean(), MODEL_CONFIG, REGION, tokenDelta(), tokenTotals() (+3 more)

### Community 100 - "arg_offload.py"
Cohesion: 0.11
Nodes (16): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, 指针必须是文本（s3:// URI）；别的类型是同版本下的定义违约，不让它变成 urlparse 的裸 AttributeError。, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与… (+8 more)

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

### Community 105 - "deterministic"
Cohesion: 0.16
Nodes (20): deterministic(), Hit, match(), 注册一条确定性 step。两种写法： 装饰器（等价于只有 playwright 句柄）： @deterministic(r'页面地址匹配…, 命中结果：命中条目的句柄集合与具名组。句柄要再经 select_handler 按当前目标取——命中与目标无关（ADR 0050 决策 1）。, 在注册表里找命中 text 的唯一条目。 返回 Hit 或 None（未命中走 AI）。命中多条 → DeterministicConflict； 命中一条但…, 命中之后按当前目标取句柄（ADR 0050 决策 1）：desktop/web 取 playwright；设备目标取覆盖这个（设备, 界面类型）组合的那条…, select_handler() (+12 more)

### Community 106 - "决策"
Cohesion: 0.13
Nodes (15): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 不升 schema 版本，在 schema 1 上增键, 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端 worker 在建会话前按自己的 `targets` 自检 (+7 more)

### Community 107 - "决策"
Cohesion: 0.12
Nodes (16): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 7. Midscene 复用边界 (+8 more)

### Community 108 - "interface.mts"
Cohesion: 0.06
Nodes (23): adapterRegistry(), AppiumInterfaceConfig, DeviceAgentArgs, DISMISS_KEYBOARD_ACTION, EDGE_SCROLLS, InputContext, KEYBOARD_NOT_DISMISSED_PREFIX, keyNameKey() (+15 more)

### Community 109 - "test_precheck.py"
Cohesion: 0.10
Nodes (30): _num(), precheck_job(), precheck_schema(), precheck_target(), 建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的…, (device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。, 名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。, 秒数的写法：整数值不带小数点（1500 而不是 1500.0），其余按原值；与 Midscene 侧的插值结果一致。 (+22 more)

### Community 110 - "dependencies"
Cohesion: 0.11
Nodes (19): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-device-farm, @aws-sdk/client-dynamodb, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore (+11 more)

### Community 111 - ".add_arguments"
Cohesion: 0.19
Nodes (9): ArgumentParser, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6； 三者与…, 把 provider 特有 flag 注册到 CLI 提供的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：目前只支持 docker，其它名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`… (+1 more)

### Community 112 - "plan"
Cohesion: 0.11
Nodes (38): FeatureContractError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, 用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig (+30 more)

### Community 113 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 115 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 116 - "evidence.test.mts"
Cohesion: 0.10
Nodes (21): build(), DESKTOP_SNAP, DEVICE_AI_SNAP, dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent (+13 more)

### Community 117 - "ADR 0043：驱动 gherkai 的 agent skill"
Cohesion: 0.20
Nodes (15): ADR 0001：范围限定英文 UI, ADR 0041：面向 agent 的 CLI 可操作面, ADR 0043：驱动 gherkai 的 agent skill, 评测去污染硬规则（CLI 来自仓库外 wheel、skill 副本随机目录、舞台路径随机）, 物化式 fixture 与可搬迁契约, 两臂评测法（with-skill 对 baseline）, ADR 0047：CLI 人读输出用 rich 渲染表格与树, gherkai_runtime.textui（表格 / 树 / 样式单点） (+7 more)

### Community 118 - "release_notes.py"
Cohesion: 0.48
Nodes (6): main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems()

### Community 119 - "app.mts"
Cohesion: 0.07
Nodes (30): APP_LAUNCH_SELF_EXIT_MESSAGE, APP_OBJECT_FORBIDDEN_MESSAGE, APP_OBJECT_MISSING_MESSAGE, APP_RESTART_SELF_EXIT_MESSAGE, APP_STATE, AppControl, appHandle(), AppObjectCheck (+22 more)

### Community 120 - "gherkai_deploy_aws/names.py"
Cohesion: 0.22
Nodes (7): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, ssm_worker_template_path(), stack_name()

### Community 121 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Release Notes Guards"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 124 - "test_skill.py"
Cohesion: 0.05
Nodes (58): is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags(), _claimed_flags(), _documented_keys() (+50 more)

### Community 125 - "deterministic.py"
Cohesion: 0.11
Nodes (22): _closed_set(), _Entry, Handles, _hits(), match_batch(), _normalize_handlers(), _normalize_keywords(), 确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →… (+14 more)

### Community 126 - "run-scope.test.mts"
Cohesion: 0.05
Nodes (28): ANDROID_WEB, DESKTOP, deviceSeam(), _events, evidenceHook(), fakeDeviceSurface(), fakePage, fakeUploader() (+20 more)

### Community 127 - "Dist Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 128 - "Target"
Cohesion: 0.15
Nodes (13): AppRef, 应用目标的应用条目（ADR 0048 决策 3）。两个形态：plan 形态只有别名与包名或 bundle id；run / submit 在组合根上传安装包后…, 一个 scope 运行在什么上面（ADR 0048 决策 1）：设备与界面类型；ui_kind 为 app 时带应用条目。缺省即桌面网页。, 机读与 plan 文本共用的紧凑写法（ADR 0048 决策 5 的形态）：`desktop/web`、`android/app:shop`。, Target, Target, target 恒为对象（桌面网页也写 desktop/web，ADR 0048 决策 3 / 0037 决策 7）。形态不对（不是对象、缺 device /…, _target_from_dict() (+5 more)

### Community 129 - "test_tunnel_warmup.py"
Cohesion: 0.03
Nodes (83): _Page, _Resp, _clock(), driven(), _FakeBrowserClient, _FakeCm, _FakeNovaAct, _FakePage (+75 more)

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

### Community 134 - "ADR 0024: worker–core 协议"
Cohesion: 0.07
Nodes (72): cli/DEVELOPMENT.md, core 包 contributor 文档, _fake_aws_creds(), 硬隔离：设假凭证 + 固定 region，绝不误连真 AWS（moto 官方推荐套装）。autouse 表示每个测试都先生效。 **对…, core 测试说明（单测 + 集成测试）, ADR 0015: v1 定位——柔性冒烟而非回归, 确定性 step（测试开发按需自建）, ADR 0016: 执行架构 — 核心库与 run 模型 (+64 more)

### Community 135 - "SubprocessWorkerHandle"
Cohesion: 0.20
Nodes (6): 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层），信号都发给 worker…, worker 进程的退出码，仍在运行为 None（poll，不等待）。同步 run 的事件记录器据此写退出记录（ADR 0042 决策七）。, 进程组里是否还有成员。先回收已退出的组长（僵尸组长仍算成员）；无法确认时按仍在处理，到期照常强杀。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的…, SubprocessWorkerHandle, Popen

### Community 136 - "render_skill_contract.py"
Cohesion: 0.23
Nodes (12): docs/internals/cli-json-contract.md（机读字段级参考页）, _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。 (+4 more)

### Community 137 - "DynamoDB Events Transport ADR"
Cohesion: 0.18
Nodes (13): DynamoDB 共享 events 表作 events-out 传输, EventSink（可注入事件出口）, events 表键设计 PK=run_id#scope_id, SK=seq, events item TTL 自动过期（7 天 expires_at）, 读一致性（流式期 EC 游标 + 终读强一致）, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列 (+5 more)

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

### Community 143 - "._run_cdk"
Cohesion: 0.06
Nodes (31): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), cdk_command(), check_cdk(), context_cache_path(), _make_sts_client(), Path, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR… (+23 more)

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "test_deterministic.py"
Cohesion: 0.14
Nodes (16): clear(), _handles_fixture(), _isolate(), 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 运行（从 repo 根）：uv run pytest -q…, 注册表清单经自述入口出去（ADR 0036「2.」/「5.」）真子进程：`--capabilities` 的 `deterministic_steps`…, 内建导航模式的跨语言对拍（ADR 0020 第 3 条）：同一组文本在两引擎上命中结果与 url 组一致，用例集只有一份…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真 step 命中面与派发一致）。, fixture 的 handlers 是协议面方言（snake_case 与 Python 同词；<fn> 占位）：换成 Python 注册面的形态。 (+8 more)

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "test_user_facing_messages.py"
Cohesion: 0.20
Nodes (13): _docstring_node_ids(), AST, parametrize, 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, 待核尝试一族的禁用形态：「待核尝试」与「记为待核」命中，「待核对」与裸词「待核」不命中。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`… (+5 more)

### Community 148 - "S3ResultStore"
Cohesion: 0.07
Nodes (25): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore, arg_offloader() (+17 more)

### Community 149 - "session.test.mts"
Cohesion: 0.07
Nodes (15): Call, CHOICE, connectionReset(), FAKE_CREDS, FakeClock, FakeFarm, Handler, makeJob() (+7 more)

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.18
Nodes (11): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 2. handler 上下文：七个字段与一条不变量, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据 (+3 more)

### Community 151 - "xcuitest.test.mts"
Cohesion: 0.18
Nodes (13): app(), attrs(), button(), DONE_RECT, FIXTURES, keyboard(), KEYBOARD_RECT, ADR-0052 (+5 more)

### Community 152 - "use_color"
Cohesion: 0.18
Nodes (16): 执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。, color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env() (+8 more)

### Community 153 - "artifact-upload.test.mts"
Cohesion: 0.32
Nodes (6): mkLogDir(), mkShots(), ADR-0029, ADR-0042, ADR-0051, tmproot()

### Community 154 - "config.py"
Cohesion: 0.21
Nodes (23): AppPlatformConfig, _apps_section(), _billing_method(), ConfigError, DevicePlatformConfig, _devices_section(), DevicesConfig, load_project_config() (+15 more)

### Community 155 - "test_lambda_asset.py"
Cohesion: 0.09
Nodes (30): BackendStack._build_lambda_asset, BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, BackendStack._worker_subnet_ids, make_stack(), make_template(), Template, synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。… (+22 more)

### Community 156 - "engines-matrix.test.mts"
Cohesion: 0.20
Nodes (7): DEVICE_LABEL, HANDLE_BY_DEVICE, MATRIX, ADR-0049, ADR-0050, Row, UI_KIND_LABEL

### Community 157 - "test_lifecycle_states.py"
Cohesion: 0.14
Nodes (14): 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 状态归约（唯一一份，schedule 与本模块两条路径共用，ADR 0031 决定三、ADR 0034「不复制归约逻辑」）。 先滤掉…, job 生命周期态 + severity 单测（ADR 0031）：skipped/aborted/pending/running、severity…, test_aggregate_all_aborted_is_aborted(), test_aggregate_all_skipped_no_error_is_skipped_not_passed(), test_aggregate_empty_verdict_set_precedence() (+6 more)

### Community 158 - "e2e_harness.py"
Cohesion: 0.23
Nodes (11): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, --interrupt 中断时机矩阵, e2e_harness.py（opt-in 手动端到端验证脚本）, Path, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, harness 报告判读要点（sample_valid 先于 n_lost）, run() (+3 more)

### Community 159 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 160 - "test_definition_schema.py"
Cohesion: 0.15
Nodes (22): parametrize, Path, definition 结构版本闸门（ADR 0037 决策 7）在 CLI 的接线：status / explain /…, 缺戳例外的接线：谓词为真的 run / submit 遇无版本戳后端以退出码 2 结束、资源检查一次不做；谓词为假（纯桌面）只警告放行。 谓词本身在…, 别的版本写出的 run 目录连运行态的形状都不保证：先核结构版本，再读运行态——否则「请升级」会变成一个解析异常。, 本机接力宿主读到同版本下形态违约的提交记录（这里真的从 run_meta.json 删掉一个 job 的 target 键）：CLI 读端有退出码可交，…, 读头阶段的形态违约（结构版本字段不是整数）：三个本机读端都以退出码 2 结束并说明，不是裸异常；运行态不被改动、不写 run 级消息…, 云端两个读端读 META 头时的形态违约（结构版本字段不是整数）：以退出码 2 结束并说明，不是裸异常；之后不再读运行态。 (+14 more)

### Community 161 - "ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）"
Cohesion: 0.09
Nodes (34): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）, 墙钟时长归约（step/scenario/scope/run duration_ms）, EngineResolver（按 job.engine 解析 Engine）, 失败隔离 / failFast 旋钮, 优雅终止：schedule 只调 handle.stop(grace), _heartbeat_wrap（静默 worker 心跳注入） (+26 more)

### Community 162 - "render.py"
Cohesion: 0.06
Nodes (61): _add_act(), _add_device_evidence(), _add_step(), _arg_hint(), _cost_bits(), device_header_lines(), device_session_count(), _dispatch_hint() (+53 more)

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

### Community 168 - "image_tag"
Cohesion: 0.15
Nodes (15): image_tag(), worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, parametrize, `gherkai_runtime.names` 的 worker 镜像交付命名（ADR 0038「tag 命名」条：单一真源、同时是单一校验点）。…, variant 本身合法但拼出来超 128 字符 → 报 tag 那一层（两类错误分开报，见 names 里两个正则的注释）。, 版本串首字符非法（归一化只管 `+`/`!`）→ tag 层拒，不静默产出 docker 不认的 ref。, `names` 的读端常量与 `DynamoDBRunStore` 的写端字面量必须逐字一致（ADR 0038 清理 pass 的运行中 run…, test_image_tag_normalizes_epoch() (+7 more)

### Community 169 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 170 - "test_devicefarm_client_placement.py"
Cohesion: 0.17
Nodes (18): _imports_devicefarm_module(), _is_devicefarm_client_call(), _production(), AST, Module, _python_sources(), 差集护栏：Python 侧的 Device Farm 客户端只在 `gherkai_runtime.devicefarm` 构造（ADR 0051 决策…, `<任意>.client("devicefarm", …)`、`client(service_name="devicefarm")`、botocore 会话的… (+10 more)

### Community 171 - "adapters.contract.test.mts"
Cohesion: 0.07
Nodes (19): ADAPTERS, ContractCase, ContractFixture, FIXTURES, FOREGROUND_POLL, HIDE_METHODS, iface(), IOS_HIDE_KEYBOARD (+11 more)

### Community 172 - "_release_cmp"
Cohesion: 0.15
Nodes (13): is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp(), _release_key(), _variant_miss_hint() (+5 more)

### Community 173 - "Engine Port & Job Planning"
Cohesion: 0.33
Nodes (7): Engine port（run_scope → WorkerHandle + Event 迭代器）, FargateEngine adapter, JobSource（可注入 job 入口）, pipe 传输实现 die（worker I/O 边缘必改）, Job（一个 scope = 一个会话边界）, plan 模块（.feature → Job 列表）, select 谓词（scenario 筛选）

### Community 174 - "Scope Tag Parsing"
Cohesion: 0.29
Nodes (7): engine 解析（scope 级）, id 派生（scopeId / scenarioId 关联键）, 一个 scenario 多个 @scope 值 → 报错, scope seam（tag 分组 + engine 校验）, scope 全局命名空间（跨文件合并，撞名 warning）, timeout 解析（@timeout:N → Job.timeoutS）, uri 互异契约（重复 uri → 报错）

### Community 175 - "reconcile.tick（推进器共享入口）"
Cohesion: 0.18
Nodes (12): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState）, status --wait 接力推进 (+4 more)

### Community 176 - "Context Glossary Guards"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条由…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 177 - "container_name"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 178 - "Graceful Stop Contract"
Cohesion: 0.33
Nodes (6): act 有界返回（per-act timeout）, 引擎经 --capabilities 自报 min_grace_s, FargateWorkerHandle.stop → StopTask, grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, 机制层：Engine adapter / WorkerHandle 把停翻成机制

### Community 179 - "Worker Termination Contract"
Cohesion: 0.33
Nodes (6): 事件流结束信号 / 存活判定迁移, exitCode 落值延迟与 MISSING 第三态, 未来演进：显式 core→worker 控制通道, Midscene worker 有序显式 cleanup handler, 逻辑层：schedule 经 worker 句柄请求停（handle.stop）, 终止契约（core 请求 worker 优雅停止）

### Community 180 - "Package URL Links"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 181 - "_render_status"
Cohesion: 0.17
Nodes (20): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。 (+12 more)

### Community 182 - "_print_artifact_lines"
Cohesion: 0.50
Nodes (4): _print_artifact_lines(), 产物落点三行（报告 / 运行元信息 / 判定明细）→ stderr：**`run` 结束与 `status` 终态共用这一份**…, 报告写入被隔离（落点表里没有 report_index 键，ADR 0030 决定三）→ 报告那行给「写失败」提示， 既不打裸…, test_artifact_lines_report_write_failure_falls_back_to_a_note()

### Community 183 - "session.mts"
Cohesion: 0.07
Nodes (25): ADR-0033, ADR-0039, APPIUM_SERVER_MAJOR_VERSION, AUTH_ERROR_NAMES, CallBound, CallFailure, CreateResult, DEVICE_FARM_REGION (+17 more)

### Community 185 - "exerciseSession"
Cohesion: 0.15
Nodes (14): collapse(), CommandRecorder, contextOf(), diffIsClean(), exerciseSession(), failureLine(), fakeDriver(), finishCase() (+6 more)

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
Cohesion: 0.40
Nodes (4): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总）, 恢复现场, 移动真机支持（1.5）：实施进度总纲, 遗留项

### Community 191 - "FargateEngine"
Cohesion: 0.15
Nodes (13): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+5 more)

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
Cohesion: 0.05
Nodes (73): _join_pumps(), _pump_log(), Event, Job, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 以非零退出码（含被信号强杀的负码）结束时抛错（终结函数按退出码判）。 纯阻塞行读、纯… (+65 more)

### Community 201 - "_job_def"
Cohesion: 0.15
Nodes (22): job_from_dict(), job_to_dict(), Job, Job(definition) → dict（双向，RunMeta 落盘）。键集固定（ADR 0037 决策 7）：timeout_s 不超时写…, dict → Job（键集固定，缺任一键即定义违约）。validate=True 时按 ADR 0048 决策 3 做推进器读 definition…, S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…, test_load_all_paginated_preserves_failed_verdict(), test_load_all_paginates_beyond_1000() (+14 more)

### Community 202 - "compose.py"
Cohesion: 0.04
Nodes (63): subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), available_targets(), _default_targets() (+55 more)

### Community 203 - "Architecture Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, gherkai 架构图发布入口页, 执行与推进全景交互图

### Community 204 - "Slide Frame SSIM Checks"
Cohesion: 0.67
Nodes (3): slide_area_ssim_checks, at_31_seconds, first_frame

### Community 205 - "_ssm_params"
Cohesion: 0.14
Nodes (14): SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 带合法项目 ARN 时恰多出一条 `device-farm-project`，值逐字等于传入的 ARN（ADR 0033 资源清单第 11 条、ADR…, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, _ssm_params(), test_prefix_switches_whole_set(), test_ssm_parameter_set_with_device_farm_project_is_exactly_seven() (+6 more)

### Community 207 - "② 请裁定（28 条发现聚成 17 个决策项，编号可一句话回；code 侧条目同时移交 code-health）"
Cohesion: 0.11
Nodes (19): ② 请裁定（28 条发现聚成 17 个决策项，编号可一句话回；code 侧条目同时移交 code-health）, D01 plan 不预告 requires 前提（0048 决策 6 / 0049 决策 6 vs plan 实装）, D02 模板 task-def 没设 runtimePlatform（0038 概念模型 vs stack 实装）, D04 抖动率汇总未实装（0014 决策 / 0024 四处「纳入抖动汇总」）, D05 提前返回路径跳过设备计量（0051 决策 7 / 契约页 vs schedule）, D06 Nova 三条提前退出路径的提示措辞与 0039 面一不变量不一致, D07 0045 决策一的 AI 侧文档范围与护栏扫描面不一致, D08 导航引号不配对的处置（0020 vs 两引擎模式） (+11 more)

### Community 208 - "_installed_version"
Cohesion: 0.21
Nodes (12): _cmd_skill_install(), _doctor_cloud(), _doctor_devices(), _doctor_worker_grace(), _doctor_worker_variants(), _installed_version(), doctor 的 `backend.worker.grace` 行：引擎 worker 自报的最短收尾宽限 vs 云端 task-def 的停止宽限。…, 给**契约比对**用的版本（skew 三态 / worker variant 解析 / 交 provider 写版本戳，ADR 0037 决策… (+4 more)

### Community 210 - "core/tests/test_redact.py"
Cohesion: 0.14
Nodes (18): Any, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则、三份同文实现。 三份同文实现（本文件、Nova worker…, 三条规则依次作用于一段文本；None 原样返回。 `https://u:p@host/x` →…, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_secrets(), parametrize, 凭据脱敏三条规则的单测（ADR 0035 决策 5；0051 决策 11）。 用例表只有一份：`engines/fixtures/redaction-… (+10 more)

### Community 211 - "SqliteEventLog"
Cohesion: 0.16
Nodes (10): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+2 more)

### Community 213 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 214 - "test_tunnel.py"
Cohesion: 0.07
Nodes (44): _gen_secret(), make_tunnel(), map_origin_in_jobs(), NgrokTunnel, Exception, Job, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 本 run 的 ngrok 流量策略 YAML（ADR 0051 决策 13）：手写模板替换，不为此引 yaml 依赖——结构固定，令牌与 cookie… (+36 more)

### Community 215 - ".acquireSteps"
Cohesion: 0.15
Nodes (4): AdapterRegistry, AppiumConnector, DeviceFarmSessions, GuardFactory

### Community 217 - "build_fargate_engines"
Cohesion: 0.08
Nodes (24): build_cloud_event_log(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), 读一个 `ResourceUri` 的字节（`file://`、裸路径、`s3://`）——**前端层解引用产物 ref 的唯一入口**（ADR 0042…, 每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR… (+16 more)

### Community 219 - "no-device-deps.test.mts"
Cohesion: 0.10
Nodes (19): BIN, DEVICE_DIRS, DEVICE_PACKAGES, DEVICE_SCOPES, deviceLoads(), filePath(), isRunScope(), LIMITS (+11 more)

### Community 220 - "WorkerNetworkError"
Cohesion: 0.14
Nodes (9): RuntimeError, worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerExitError, WorkerNetworkError, FakeWorkerHandle, Event, Job (+1 more)

### Community 221 - "云端后端用户文档"
Cohesion: 0.08
Nodes (46): gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce）, kicker Lambda（冷启动器）, reconciler Lambda（主推进器） (+38 more)

### Community 222 - "_role_statements"
Cohesion: 0.15
Nodes (20): _all_actions(), _as_list(), IAM 资源 ARN 已收窄（ADR 0033）——回归护栏：防将来改回 * 或踩 account=aws 陷阱。 收窄依据是 AWS SAR…, 某角色全部 policy 语句的原样列表；按 policy 的 Roles 引用里的逻辑 id 片段认角色（如 `TaskRoleMidscene`）。, 带项目 ARN 合成时 Midscene task role 的设备权限逐条对照 ADR 0033 的权限表。…, 应用存在性检查的 `s3:ListBucket`：资源是产物桶本身，条件 `StringLike` `s3:prefix` 为 `apps/*`（ADR…, 两个引擎 task role 分立（ADR 0033）：设备目标只由 Midscene 执行，Nova 的 role 带项目 ARN 合成时也零 Device…, 不带项目 ARN 或带「待建立」占位合成时，整个模板零 Device Farm 动作，两个 task role 都没有 ListBucket（ADR 0037… (+12 more)

### Community 223 - "precheck.mts"
Cohesion: 0.23
Nodes (12): DEVICE_LABEL, ADR-0024, ADR-0049, ADR-0051, precheckJob(), precheckSchema(), precheckTarget(), spaced() (+4 more)

### Community 224 - "gemini_image.py"
Cohesion: 0.33
Nodes (4): HTTPRedirectHandler, NoRedirect, 演示制作规范, 演示制作与媒体工具说明

### Community 227 - "_StubEcs"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 228 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 229 - "ContainerError"
Cohesion: 0.07
Nodes (22): ContainerEngine, ContainerError, Exception, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 多平台索引的目标平台视图（`inspect --platform linux/amd64`）：返回 (os, architecture)，本机没有该平台的内容…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+14 more)

### Community 235 - "sessionEventSink"
Cohesion: 0.33
Nodes (3): requireName(), sessionEventSink, sessionOpenedEvent()

### Community 240 - "session-name.mts"
Cohesion: 0.12
Nodes (19): AGENTCORE_SESSION_NAME_MAX, decode(), DecodedSessionName, DEVICE_FARM_SESSION_NAME_MAX, encode(), encodedUnits(), matches(), MatchOptions (+11 more)

### Community 242 - "surface-desktop.mts"
Cohesion: 0.09
Nodes (21): desktopSeam(), AWS_TRANSIENT_NAMES, AWS_TRANSIENT_STATUS, BROWSER_CLOSE_BUDGET_MS, BROWSER_SESSION_TIMEOUT, browserSessionTimeoutS(), CONNECT_BACKOFF_MS, connectRetriesExhausted (+13 more)

### Community 245 - "test_lambda_handlers.py"
Cohesion: 0.02
Nodes (120): cloud_env(), _FakeEcs, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。 (+112 more)

### Community 246 - "bin.mts"
Cohesion: 0.12
Nodes (11): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037, ADR-0051, MASK, ADR-0035 (+3 more)

### Community 247 - "_Worker"
Cohesion: 0.17
Nodes (10): _heartbeat_wrap(), Event, 单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。, 对本 job 落定停止原因并（首次）向 worker 发停止请求；已落定、已返回或内容已完整的直接返回现值。事件循环、异常分支与…, 内容已完整而 deadline 已过：只催 worker 收尾（发停止请求，排空上界从此刻起算），不落定停止原因——判定已成，…, 运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 使用方再次中断（ADR 0024 终止契约）：零宽限的停止请求——子进程 adapter 即对 worker 的进程组发 SIGKILL，Fargate… (+2 more)

### Community 249 - "deterministic.test.mts"
Cohesion: 0.20
Nodes (7): BUILTIN, HANDLES_FIXTURE, META, ADR-0020, ADR-0022, ADR-0050, UNTOUCHABLE_CTX

### Community 251 - "⑦ 事实族横切记录（18 族）"
Cohesion: 0.11
Nodes (19): ⑦ 事实族横切记录（18 族）, F01 · inconsistent, F02 · inconsistent, F03 · inconsistent, F04 · inconsistent, F05 · inconsistent, F06 · inconsistent, F07 · inconsistent (+11 more)

### Community 252 - "run_scope.py"
Cohesion: 0.04
Nodes (52): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与… (+44 more)

### Community 253 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 254 - "xcuitest.mts"
Cohesion: 0.06
Nodes (34): ACCESSORY_DISMISS_BUTTON_QUERY, ACCESSORY_TOOLBAR_MAX_GAP, adjacentAbove(), CLEAR_INPUT_BACKSPACES, createXcuitestAdapter(), DEEP_LINK_UNSUPPORTED_MESSAGE, DISMISS_CONTROL_AMBIGUOUS_MESSAGE, DISMISS_CONTROL_VANISHED_MESSAGE (+26 more)

### Community 255 - "Path"
Cohesion: 0.19
Nodes (9): _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非…, scope 末：整目录递归上传剩余文件（跳过已传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→… (+1 more)

### Community 256 - "项目约定"
Cohesion: 0.29
Nodes (6): graphify, 代码纪律, 工作方式, 文档纪律, 沟通, 项目约定

### Community 258 - ".run_scope"
Cohesion: 0.11
Nodes (14): _ExitRecorder, make_raw_sink(), 一个 scope 的原始事件行落库回调。闭包持 seq，读 fd3 的线程内单线程递增、无竞态。, 一个 job 的退出记录只写一次：事件迭代结束（含非零退出码的异常）或 stop 完成时，谁先到谁写。 唯一的例外是用真码覆盖未知码：stop…, 包住 worker 句柄：stop 完成后补写退出记录（schedule 主动停止时事件迭代器被放弃、不会自然结束）。其余成员原样转发。, _recording_events(), _RecordingHandle, test_make_raw_sink_is_the_shared_writer() (+6 more)

### Community 259 - "ADR 0044: 引擎模型选择与覆盖"
Cohesion: 0.10
Nodes (29): ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码, 概念：Midscene 仅走 chat-completions 接口, ADR 0003: VL 模型选型, ADR 0003: Midscene grounding 用 Qwen3-VL on Bedrock, Model qwen.qwen3-vl-235b-a22b (Bedrock ON_DEMAND), Region 解析顺序（--region > AWS_REGION > AWS_DEFAULT_REGION > profile）, NOVA_MODEL_ID opt-in 环境变量旋钮 (+21 more)

### Community 260 - "warmup.mts"
Cohesion: 0.15
Nodes (18): attempt(), AttemptResult, _BlockIsPort, createDeviceWarmup(), DeviceWarmupArgs, DeviceWarmupBlock, DeviceWarmupDeps, findWarmupMarker() (+10 more)

### Community 261 - "Artifact Uploader Component"
Cohesion: 0.09
Nodes (29): 引擎特有量不进 model（act_count）, JobResult 持有 Job、engine 经 property delegate, href 相对化（local 相对 / cloud 恒等 ref）, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 式产物拷贝, 不透明搬运铁律（model/wire/schedule 永不解引用 ref）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写） (+21 more)

### Community 262 - "RunMeta"
Cohesion: 0.03
Nodes (77): event_log adapters (sqlite / ddb), ReportStore adapters (local / s3), ResultStore adapters (local / s3), 读回 definition（RunMeta）；不存在返回 None。, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。…, RunMeta, Engine, EngineResolver (+69 more)

### Community 263 - "appium.test.mts"
Cohesion: 0.10
Nodes (13): ACQUIRE_TIMED_OUT, ANDROID_APP, budgetOf(), connector(), connectWith(), FakeClient, fakeWdio(), FakeWdioScript (+5 more)

### Community 264 - "desktopFactory"
Cohesion: 0.38
Nodes (7): desktopFactory(), desktopHooks(), desktopSeam(), econnreset(), fakeAgentCore(), fakeBrowser(), surfaceDeps()

### Community 265 - "runScope"
Cohesion: 0.16
Nodes (11): createSurface(), drainArtifactQueue(), exitAfterFailure(), log(), main(), runScenario(), runScope(), scopeErrorEvent() (+3 more)

### Community 266 - "test_event_log_recording.py"
Cohesion: 0.12
Nodes (16): EventRecordingEngine, 给 SubprocessEngine 包一层：run_scope 时把该 job 的原始事件行与退出记录落 SqliteEventLog，其余原样转发。 只包…, 原始事件行记录器（ADR 0042 决策七）：同步 run 经 EventRecordingEngine 把 worker 事件行落…, stop 的 SIGKILL 兜底与二次中断都是发出即返回、不等内核回收，此刻 poll 还看不到码：记录器带超时 wait 一次取真码；…, stop 的强杀分支返回时码仍未就位、有界 wait 也没等到：先按未知码写；随后 schedule 排空事件流读到带码的 WorkerExitError，…, 停止线程按未知码写、落库中途被挂起，事件线程同时拿到真码：两次写入串行、真码后写——终值是真码，不会被恢复的停止线程覆盖成未知码。, 假装是 SubprocessEngine：run_scope(job, raw_sink) 把几行原始事件喂给 raw_sink，返回可控的句柄与事件迭代器。, worker 以非零退出码结束：按异常携带的退出码写退出记录并原样抛给调用方；schedule 主动 stop：停止完成后记（迭代器被放弃时不记），只记一次。 (+8 more)

### Community 267 - "Job"
Cohesion: 0.03
Nodes (120): _device_keys_for_explain(), explain_to_dict(), 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, explain 的人与 agent 可读文本（`explain_to_dict` 的文档渲染为树形摘要，节点文字依 ADR 0042…, render_explain_text(), Prepared, run / submit 共享前置的产物：全部已解析、零 AWS 的输入。下游按字段取，不往 argparse 的 Namespace 上挂状态。, _explain_job() (+112 more)

### Community 268 - "test_report_store.py"
Cohesion: 0.20
Nodes (31): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。, 测试 helper：RunResult 由 RunMeta(definition) 与判定 jobs 合成。run_meta.jobs 取自各 jr.job。 (+23 more)

### Community 269 - "_Recorder"
Cohesion: 0.14
Nodes (12): cdk(), _FakeEngine, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, _Recorder (+4 more)

### Community 270 - "device_reprobe 使用说明（Midscene 设备模块的真机重新探测）"
Cohesion: 0.18
Nodes (11): device_reprobe 使用说明（Midscene 设备模块的真机重新探测）, 判读, 前置条件, 定位与适用场景, 离线自检（`--offline`）, 类型检查, 耗时判读, 调用 (+3 more)

### Community 272 - "user-steps.mts"
Cohesion: 0.12
Nodes (13): FIXTURE, ADR-0035, ADR-0051, SECRET_CASES, collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016 (+5 more)

### Community 273 - "ensure_app_object"
Cohesion: 0.14
Nodes (24): AppLocation, ensure_app_object(), 保证安装包在桶里且（managed 时）保留承诺成立，返回它的 S3 位置与内容哈希（填进 Job 的应用条目，ADR 0048 决策 3）。, _file(), _observer_gone(), Path, 安装包上传与复用（ADR 0051 决策 9）：键按内容哈希、404 上传（managed 带标签）、年龄在复用窗口内复用、超窗同键刷新、刷新失败重传、…, boto3 的 upload_file 把 ClientError 包成自己的 S3UploadFailedError（不是 botocore 异常）：404… (+16 more)

### Community 275 - "test_engines_matrix.py"
Cohesion: 0.12
Nodes (21): 把名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」而不是「在Android 网页上」）；全中文的名称原样。, (device, ui_kind) → 「桌面网页」「Android 应用」这类名称；未知取值原样拼出（自述形态由组合根校验，这里只呈现）。, 前提清单 → 「需要网页上下文」；未知取值按「需要 <取值>」原样显示（ADR 0049 决策 1：CLI 不另立取值集合）。, 一组目标条目 → 「桌面网页、Android 网页（需要网页上下文）」；带 max_session_s 的条目按分钟附会话上限（doctor 用）；…, requires_label(), spaced(), target_label(), targets_label() (+13 more)

### Community 276 - "_FakeResult"
Cohesion: 0.12
Nodes (9): _ActBoom, _FakeResult, _Meta, _NavErrorNova, RuntimeError, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 Nova SDK 的 act 异常：与成功结果一样带 metadata（time_worked_s 已真实计费、trajectory 已写盘）。 (+1 more)

### Community 277 - "detached.py"
Cohesion: 0.18
Nodes (11): cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在…, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。 (+3 more)

### Community 278 - "probe.test.mts"
Cohesion: 0.14
Nodes (6): fakeSession(), HERE, ADR-0052, probeWith(), Script, Step

### Community 279 - "web-context.mts"
Cohesion: 0.16
Nodes (13): contextNames(), LocateDeps, locateError(), locateFailure(), locateWebContext(), ADR-0039, ADR-0050, ADR-0052 (+5 more)

### Community 280 - ".actionSpace"
Cohesion: 0.19
Nodes (3): DeviceAdapter, dismissKeyboardDescription(), SystemButton

### Community 281 - "runStep"
Cohesion: 0.50
Nodes (3): cumulativeTokens(), runStep(), stepCost()

### Community 282 - "run_evals.py"
Cohesion: 0.20
Nodes (18): collect_outputs(), fail(), load_evals(), main(), materialize(), parse_events(), pollution_metrics(), _purge_session_dir() (+10 more)

### Community 283 - "_FakeSink"
Cohesion: 0.22
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。

### Community 284 - "parse_iso"
Cohesion: 0.25
Nodes (8): datetime, parse_iso(), detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), test_run_duration_ms_from_run_state_timestamps()

### Community 287 - "events_pk"
Cohesion: 0.29
Nodes (5): 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。, test_events_pk_composite_run_id_scope_id()

### Community 290 - "read_project_arn"
Cohesion: 0.33
Nodes (6): 从后端区域的 SSM 读项目 ARN（`ssm_path(prefix, DEVICE_FARM_PROJECT_KEY)`，stack 资源写入）。…, read_project_arn(), 读不到不等于没有：其他错误回落「待建立」会让 diff 把已部署的设备授权显示成删除，由调用方决定退出码（ADR 0051 决策 10）。, test_read_project_arn_missing_parameter_is_none(), test_read_project_arn_other_errors_propagate(), test_read_project_arn_returns_stored_value()

### Community 292 - "list_open_sessions"
Cohesion: 0.15
Nodes (14): list_open_sessions(), _make_devicefarm_client(), OpenSession, 列出项目里所有未到 COMPLETED 的远程访问会话，含排队中的（ADR 0051 决策 6 的泄漏护栏，供 doctor 用）。 翻页列举…, devicefarm 客户端：区域恒为 DEVICE_FARM_REGION，与 profile 或环境变量给的后端区域无关。抽出来供测试替换。, 一个未到 COMPLETED 的远程访问会话（doctor 据此给出控制台链接与停止命令）。`name` 与 `created` 在服务没有返回时为 None。, df(), 环境变量与 profile 都把后端区域给成 us-east-1，客户端仍落在 us-west-2。 (+6 more)

### Community 293 - ".execute"
Cohesion: 0.29
Nodes (3): CommandGuard, DeviceWarmup, executionFailure()

### Community 294 - "app.test.mts"
Cohesion: 0.16
Nodes (13): crossRegionStore(), FAKE_CREDS, LOC, ADR-0050, ADR-0051, ADR-0052, RFC-3986, offlineClient() (+5 more)

### Community 295 - "warmup.test.mts"
Cohesion: 0.17
Nodes (10): androidTree(), EXEC, FIXTURE, harness(), HarnessOptions, HERE, LOADING, ADR-0051 (+2 more)

### Community 298 - "finalize.mts"
Cohesion: 0.29
Nodes (10): deleteAppiumSession(), emit(), emitAttempted(), finalizeOnce(), ADR-0051, ADR-0052, observedSeconds(), RELEASE_RETRY_DELAY_MS (+2 more)

### Community 299 - ".__init__"
Cohesion: 0.40
Nodes (3): EngineResolver, Lock, Sink

### Community 300 - "_MissingThenStoppedEcs"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 301 - "app_upload.py"
Cohesion: 0.10
Nodes (19): app_object_key(), AppUploadError, _BucketRegionObserver, _error_code(), _events(), BaseException, datetime, Exception (+11 more)

### Community 303 - "device/surface.test.mts"
Cohesion: 0.10
Nodes (10): harness(), HarnessOptions, LOST_BEFORE_START, makeJob(), ADR-0050, ADR-0051, ADR-0052, opened (+2 more)

### Community 309 - "reconciler.py"
Cohesion: 0.09
Nodes (29): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+21 more)

### Community 310 - "_all_option_dests"
Cohesion: 0.40
Nodes (5): _all_option_dests(), ArgumentParser, parser 及其子 parser 上全部选项字符串与 dest。, `version` 与 `device_farm_project` 由命令派生、有意不给 flag（ADR 0037 决策 6）：手填只会多出写错的机会。…, test_command_derived_context_keys_have_no_flag()

### Community 312 - "web-context.test.mts"
Cohesion: 0.24
Nodes (7): DriverScript, fakeDriver(), ADR-0050, ADR-0052, opened, session(), surfaceWith()

### Community 313 - "_interrupt_prompt"
Cohesion: 0.50
Nodes (4): _interrupt_prompt(), 使用方中断的两级提示（ADR 0024 终止契约「使用方中断」条）。本机后端：首次协作停止、再次整组强杀；云端后端：worker 是 Fargate 任务，…, 两级提示按后端措辞：本机说宽限秒数与「立即结束 worker」；云端说宽限由部署配置决定、再次中断只重发停止请求；第二级都指向控制台。, test_interrupt_prompts_by_backend_and_level()

### Community 314 - "parent-watchdog.mts"
Cohesion: 0.29
Nodes (6): ADR-0024, ownerPidFromEnv(), PARENT_PID_ENV, PARENT_POLL_MS, ParentWatchdogDeps, startParentWatchdog()

### Community 315 - "wdio-log.mts"
Cohesion: 0.28
Nodes (7): installWdioLogMasking(), ADR-0051, sameLoggerAsWebdriver(), WDIO_LOG_LEVEL, WDIO_LOGGER, WDIO_MASKING_PATTERNS, wdioLogMaskingInstalled()

### Community 316 - "wdio-log.test.mts"
Cohesion: 0.22
Nodes (4): ENDPOINT_PATH, FIXTURE, ADR-0051, PRESIGNED_SECRETS

### Community 317 - "cli/tests/conftest.py"
Cohesion: 0.40
Nodes (3): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。

### Community 318 - "ADR 0011: AgentCore 浏览器 system default vs custom"
Cohesion: 0.40
Nodes (5): ADR 0011: AgentCore 浏览器 system default vs custom, 系统默认浏览器 aws.browser.v1, 自建 custom browser（create-browser）, @engine:<midscene|novaact> 引擎选择 tag, @timeout:<N> job 墙钟预算 tag

### Community 320 - "severity 数值序（_STATUS_SEVERITY）"
Cohesion: 0.32
Nodes (8): 退出码基于 run 级 severity, _NON_VERDICT 与 _aggregate 入口过滤, severity 数值序（_STATUS_SEVERITY）, Status.ABORTED（core 派生态）, Status.PENDING / RUNNING（生命周期前置态）, Status.SKIPPED（core 派生态）, step 级短路：step_skipped 事件 + shortcircuited 布尔, TERMINAL_STATUSES（终态真源，取补定义）

### Community 321 - ".waitRunning"
Cohesion: 0.32
Nodes (3): classifyCallFailure(), isStopped(), minutesOf()

### Community 323 - "AppiumInterface"
Cohesion: 0.20
Nodes (5): AppiumInterface, autoDismissKeyboardDescription(), pngSize(), PrimitiveContext, withAutoDismissDescription()

### Community 325 - "precheck.test.mts"
Cohesion: 0.50
Nodes (3): DESKTOP_ONLY_TARGETS, DEVICE_TARGETS, ADR-0049

### Community 326 - "check_node"
Cohesion: 0.25
Nodes (7): check_node(), _node_major(), `node --version` 的主版本号；取不到/认不出 → None（**不据此拦**，版本探测失败不该挡住部署）。, Node 前置：缺失/过低 → 返回给人看的一句话；OK → None。**不抛 traceback**（ADR 0037 决策 6）。 为何必查：`aws-…, `gherkai doctor` 的 provider 段（ADR 0041 决策四）：部署方工具链**只读**自检——Node ≥ 22、cdk…, test_node_too_old_is_rejected(), test_unparseable_node_version_does_not_block()

### Community 328 - "list_registry"
Cohesion: 0.29
Nodes (7): list_registry(), 注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。, 注册表语义的跨语言对拍（ADR 0050 决策 1、0022 冲突规则）：同一组注册输入，两侧清单的 keywords 与 match_batch…, 条目可声明适用关键字（ADR 0050 决策 1）：封闭集合、非空、不重复，自述按规范顺序给出。, test_keywords_declaration_normalized_and_validated(), test_list_registry_reflects_registrations(), test_registry_cross_engine_fixture()

### Community 329 - "_build_parser"
Cohesion: 0.18
Nodes (14): _add_config_flag(), _add_device_flags(), _add_selection_flags(), _build_parser(), _finite_float(), ArgumentParser, `--default-job-timeout` 的类型转换（ADR 0034「job timeout」节②）：只收有限数。`float()` 会收下 nan…, run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。 (+6 more)

### Community 333 - "test_compose.py"
Cohesion: 0.05
Nodes (66): fixture, check_version_skew(), prune_empty_dirs(), Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`，再缺取配置文件的 profile（ADR 0053 决策… (+58 more)

### Community 335 - "patch-package 补丁 @cucumber+cucumber+13.0.0"
Cohesion: 0.40
Nodes (5): 默认 AI 判断的裸 When/Then step, 补丁的保守回退策略, patch-package 补丁 @cucumber+cucumber+13.0.0, 精确 pin cucumber 13.0.0 的版本约束, B1 退役清单（cucumber 入口 + 补丁 + bdd conftest）

### Community 338 - "test_sqlite_event_log.py"
Cohesion: 0.17
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 339 - "test_code_comments.py"
Cohesion: 0.19
Nodes (12): code_comment_files(), parametrize, Path, repo 内 code 注释与 docstring 的措辞与悬空指针护栏（ADR 0045 决策六：注释与 docstring 是人读层；ADR 0046…, 注释与 docstring：无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」、不指 journey 文件与 WP 编号。, 形态①③的启发式扫剥掉行内代码后的注释：反引号里的 `job = 范围` 是代码、不报，正文里的等号照报； 其余规则仍扫注释原文，反引号里的 journey…, docstring 里围栏代码块中的 `job = 范围` 是代码示例、不报；围栏闭合之后的正文照报。, _rel() (+4 more)

### Community 340 - "test_provider.py"
Cohesion: 0.05
Nodes (58): classify_vpc_state(), SSM 里记的生效取值 `stored` 是否与本次 `--vpc requested` 一致。 三种取值形态见…, 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, vpc_spec_matches(), _app_context_keys(), _cache_env(), _CdkWritingContext, _clean_aws_env() (+50 more)

### Community 341 - "_FakeNovaAct"
Cohesion: 0.18
Nodes (5): _FakeCm, _FakeNovaAct, main_fakes(), 结构相同的上下文管理器替身（给 with wf 用）。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。

### Community 347 - "worker/surface.test.mts"
Cohesion: 0.33
Nodes (5): knownFailure, lost, ADR-0051, ADR-0052, unknownResult

### Community 350 - "scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 351 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 373 - "image_token_probe.mts"
Cohesion: 0.20
Nodes (11): engineRequire, image_token_probe：截图缩放后的图片 token 探针, main(), ADR-0052, OpenAIClient, parseArgs(), promptTokens(), { resizeBase64ImageToJpeg, imageInfoOfBase64 } (+3 more)

### Community 374 - "DeterministicKeywordMismatch"
Cohesion: 0.33
Nodes (5): DeterministicConflict, DeterministicKeywordMismatch, Exception, 一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。 冲突清单只经 message 传（派发侧把异常文本并入…, step 文本命中了一条确定性模式，但当前关键字不在该条目声明的 `keywords` 里（ADR 0050 决策 1）。 派发侧据此记 error、不转…

### Community 375 - "deterministic.steps.mts"
Cohesion: 0.12
Nodes (11): ADR-0020, ADR-0022, ADR-0036, ADR-0037, ADR-0048, ADR-0050, RFC-3986, ADDRESS_PATTERN (+3 more)

### Community 376 - "_InterruptState"
Cohesion: 0.25
Nodes (3): _InterruptState, 本机 run 的中断标志（ADR 0024 终止契约「使用方中断」条）：SIGINT / SIGTERM 的处理器只记次数与首个信号号、零 I/O；…, 装处理器，返回原处理器供 restore；非主线程（不能装信号处理器）或平台没有该信号时跳过那一个。

### Community 377 - "test_technical_docs.py"
Cohesion: 0.33
Nodes (8): technical_docs(), parametrize, Path, 技术文档的措辞与悬空指针护栏（ADR 0045 决策一 / 六：CONTRIBUTING、各包…, 正文无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」、不指 journey 文件与 WP 编号（代码块与行内代码不算）。, _rel(), test_scan_face_is_not_empty(), test_technical_doc_uses_written_register()

### Community 378 - "._pump"
Cohesion: 0.50
Nodes (3): Event, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, Timer

### Community 380 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, navigate(), 确定性 step 脚手架（ADR 0020/0022）—— 本包随 worker 发行的注册表内容：**只有内建导航一条**。 机制（ADR…, 内建导航（ADR 0020 第 3 条）：整句为地址的 Given / When step，直接打开，不走 AI。

### Community 381 - "ADR 0013: 跨引擎共享边界"
Cohesion: 0.23
Nodes (12): ADR 0005: 单一共享 feature 文件, 双语言裂缝（物理约束）, ADR 0006: 形态 A——两个子工程、无编排器, 公共设施落在核心库层（报告归集/会话生命周期/跑批入口）, ADR 0013: 跨引擎共享边界, 跨引擎共享止于 features/（Gherkin 单一事实源）, 薄 worker 子进程（一次调用=一个 scope=一个 job）, 两个引擎都作为子进程 worker、核心语言自由选 Python (+4 more)

### Community 382 - "test_warmup_page_script_classifies_only_401_as_denied"
Cohesion: 0.29
Nodes (7): 把文本里每个「作为一个地址出现」的 origin 换成 base：origin 之后的 URL 字符段 R 为空、以 / ? #…, replace_origin(), parametrize, skipif, 预热页脚本的分类（ADR 0051 决策 13）：校验响应 200 → READY；只有 401 → DENIED（确定性拒绝、worker 归…, test_replace_origin_boundaries(), test_warmup_page_script_classifies_only_401_as_denied()

### Community 383 - "test_run_status_agrees_between_schedule_and_project_full"
Cohesion: 0.67
Nodes (3): parametrize, 两条路径共用同一个 _aggregate：同一组 job 事件分别经同步 schedule 与无状态 project_full，run 级 status 相同。, test_run_status_agrees_between_schedule_and_project_full()

### Community 384 - "scenario_key"
Cohesion: 0.25
Nodes (8): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), 转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了就会让 evidence 静默互相覆盖。, 同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。, test_scenario_key_does_not_use_display_name(), test_scenario_key_is_deterministic_and_escapes_separators(), test_scenario_key_no_collision_after_escaping(), test_scenario_key_survives_non_ascii_and_empty_ids()

### Community 385 - "browser_session_timeout_s"
Cohesion: 0.50
Nodes (4): browser_session_timeout_s(), job 的墙钟预算（秒，可为小数）→ 会话超时秒数：向上取整加余量、夹在服务允许的区间；预算为空时返回 None（不传、保持服务默认）。, 取值规则与 Midscene 桌面 worker 对拍（engines/fixtures/browser-session-…, test_browser_session_timeout_matches_shared_fixture()

### Community 387 - "_Clock"
Cohesion: 0.15
Nodes (10): Event, 事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收…, parametrize, 没有 deadline 的 job 被 fail-fast 中止后卡死不退出：排空上界同样起作用（靠心跳醒来），不挂死，判 ABORTED。, 合成明细与判定分开（ADR 0034 机制二）：scope 级 error 合成 SKIPPED 之后 worker 非零退出且已过 deadline /…, test_drain_bound_applies_without_deadline_under_fail_fast(), test_synthesized_details_survive_sync_path_timeout_and_abort(), _Clock (+2 more)

### Community 390 - "trigger_eval.py"
Cohesion: 0.46
Nodes (7): fail(), main(), one(), Path, 用哪个 gherkai 装 skill：优先仓库外那套；它被 `--prepare-cli` 剥掉了包内 skill 时回落到仓库 `.venv`。…, 运行一条查询，返回（是否触发, 前几次工具名）。, resolve_installer()

### Community 391 - ".hideKeyboard"
Cohesion: 0.29
Nodes (4): isNoDismissControlError(), keyboardNotDismissedMessage(), keyboardNotHiddenLogLine(), locatePoint()

### Community 393 - "_TrajNova"
Cohesion: 0.33
Nodes (3): 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。, _TrajNova, _TrajResult

### Community 396 - "url_matches.py"
Cohesion: 0.50
Nodes (3): deterministic, 示范用确定性 step（Nova Act 侧）：断言当前页面地址匹配给定正则。 这是 `steps/` 目录的模板：复制进你的项目后按需改措辞与判定。与…, url_matches()

### Community 397 - "deploy.py"
Cohesion: 0.09
Nodes (23): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+15 more)

### Community 404 - "_events_table_actions"
Cohesion: 0.33
Nodes (6): _events_table_actions(), 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, test_advancer_events_table_face_is_read_plus_putitem(), test_exit_observer_can_only_putitem_on_events_table()

### Community 405 - "unspecified_message"
Cohesion: 0.40
Nodes (5): platform_label(), ADR 0053 决策 4 的用户可见消息：有该平台的设备 scope，却没有任何来源指定设备。, unspecified_message(), run / submit：有设备 scope 的平台没有任何来源指定设备，在提交前以退出码 2 结束（ADR 0053 决策 4「不自动挑设备」）。, require_device_selections()

### Community 409 - "输出契约：流式 JSON Lines 事件流"
Cohesion: 0.33
Nodes (6): 输出契约：流式 JSON Lines 事件流, reportRefs 不透明产物引用, status 三态 passed/failed/error（wire 只传三态）, step_skipped 独立事件（scope 内短路）, 三通道分离传输（EVENTS_FD / stdout / stderr）, 事件三级 started/done 对齐

### Community 411 - "文档健康度复盘 · 第九轮 · 待批报告"
Cohesion: 0.25
Nodes (8): ⑩ 同僚复核与分歧裁决附录, ① 基线, ④ 提纯提案待批（红线复核通过 96 条；approve_reduced 用缩小后改法；reject 40 条存档不列）, ⑤ 主观发现待批（156 条：STALE 5、SEDIMENT 15、REDUNDANCY 30、TONE 104、DEADLINK 1、CONTRADICTION 1）, ⑥ 具名提纯审计记录（审计集 54 篇）, ⑧ Status 头与反向链、引用图、文件名, ⑨ 方法复盘草稿（下一轮开局作第一份待批）, 文档健康度复盘 · 第九轮 · 待批报告

### Community 412 - "_advancer_stmts"
Cohesion: 0.50
Nodes (4): _advancer_stmts(), 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…, test_reconciler_and_kicker_have_the_same_permission_face()

### Community 414 - "test_stderr_redaction.py"
Cohesion: 0.06
Nodes (54): _log(), 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, _assert_redacted(), _import_bindings(), _package_sources(), _plain(), Module (+46 more)

### Community 418 - "_joined_refs"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 419 - "doc-health 第九轮移交 code-health 的输入：code 侧客观发现与「改 code、ADR 不动」的裁定"
Cohesion: 0.50
Nodes (3): doc-health 第九轮移交 code-health 的输入：code 侧客观发现与「改 code、ADR 不动」的裁定, 一、裁定为「改 code、ADR 不动」的设计偏离（VIOLATES_ADR）, 三、第九轮落地时顺手改过的 code 文件（已随「code 连带」提交，code-health 只需知悉）

### Community 420 - "CloudTarget"
Cohesion: 0.50
Nodes (3): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序即链上顺序。

### Community 421 - "_delayed_stopped_ecs"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order()

### Community 422 - "devicefarm.py"
Cohesion: 0.14
Nodes (18): NoReturn, AmbiguousProject, DeviceFarmAccessDenied, _error_code(), is_access_denied(), _project_exists(), ProjectResolution, BaseException (+10 more)

### Community 423 - "_Calls"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 428 - "parseXmlTree"
Cohesion: 0.67
Nodes (3): decodeXmlEntities(), parseXmlTree(), scanXmlElements()

### Community 432 - "ADR 0043: 随 CLI 发行的 agent skill"
Cohesion: 0.05
Nodes (50): gherkai agent skill 包, ACT_TIMEOUT_S=120 不压（否决解法 B）, 中断产物丢失风险（容器盘停即销毁）, 孤儿产物扫盘 reaper（经分析否决）, 安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底, 关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）, stopTimeout=120 / grace 预算校准, IAM 最小权限（task role 动作×资源两维收窄） (+42 more)

### Community 461 - "surface.mts"
Cohesion: 0.05
Nodes (39): ADR-0027, ADR-0028, AcquireResult, AddressReading, attachClassification(), CLASSIFICATION_KEY, ControlItem, Controls (+31 more)

### Community 588 - "runOnDevice"
Cohesion: 0.33
Nodes (7): log(), main(), parseOptions(), recordingParts(), runOnDevice(), saveMaterial(), writeMatrix()

### Community 593 - ".attempt"
Cohesion: 0.47
Nodes (3): Lifecycle, probeFacts(), valueOf()

### Community 595 - "verify_project"
Cohesion: 0.14
Nodes (12): 用 GetProject 只读核对项目是否还在（供 `diff` 核对 SSM 记录的 ARN，ADR 0051 决策 10「项目」）：在则…, verify_project(), 网络故障：botocore 抛的不是 ClientError，Stubber 排不出这种失败，故用假客户端。, 项目已被手动删除：返回 False 交给调用方处置。Stubber 只排了 GetProject，任何列举或建立的调用都会因没有排好的响应而失败。, 非 NotFound、非无权限的错误原样抛出：既不当成「项目不存在」，也不当成无权限。, test_network_error_propagates_without_listing(), test_verify_project_access_denied_is_classified(), test_verify_project_existing_project_is_true() (+4 more)

### Community 597 - "diffAgainstFixture"
Cohesion: 0.60
Nodes (5): diffAgainstFixture(), flatten(), formOf(), isCapabilityUnavailable(), unavailableCaseCheck()

### Community 599 - "fixtureFor"
Cohesion: 0.67
Nodes (3): fixtureFiles(), fixtureFor(), loadFixture()

### Community 614 - "执行与推进模型导览（run/submit × local/cloud）"
Cohesion: 0.07
Nodes (52): gherkai-deploy-aws contributor 手册, AgentCore Evaluations（去优先级的相邻选项）, AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, ADR 0017: 云端执行选 Fargate, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务, ADR 0032: Fargate 执行环境 (+44 more)

## Ambiguous Edges - Review These
- `终止契约（core 请求 worker 优雅停止）` → `step 顺序 = 书写顺序，keyword 只决定派发`  [AMBIGUOUS]
  docs/adr/0025-plan-module-feature-to-jobs.md · relation: references
- `Cloud Backend Upgrade Windows Diagram` → `Cloud Delivery Identity Diagram`  [AMBIGUOUS]
  docs/diagrams/cloud-backend-upgrade-windows.svg · relation: conceptually_related_to
- `Cloud Delivery Identity Diagram` → `Execution Cloud Cascade Diagram`  [AMBIGUOUS]
  docs/diagrams/execution-cloud-cascade.svg · relation: conceptually_related_to
- `Configuration Env Inheritance Diagram` → `Getting Started Component Ownership Diagram`  [AMBIGUOUS]
  docs/diagrams/getting-started-component-ownership.svg · relation: conceptually_related_to
- `五层职责切分（用例/产品/执行/浏览器/被测应用）` → `本机应用测试隧道拓扑图`  [AMBIGUOUS]
  docs/diagrams/local-app-testing-tunnel-topology.svg · relation: conceptually_related_to
- `五层职责切分（用例/产品/执行/浏览器/被测应用）` → `README 运行时拓扑图`  [AMBIGUOUS]
  docs/diagrams/readme-runtime-topology.svg · relation: conceptually_related_to
- `架构总览：五层结构、一次 run 的生命周期、包与发行物` → `scenario 到 job 图`  [AMBIGUOUS]
  docs/diagrams/writing-features-scenario-to-job.svg · relation: conceptually_related_to
- `执行与推进模型导览（run/submit × local/cloud）` → `run 执行图`  [AMBIGUOUS]
  docs/diagrams/run-execution.svg · relation: references

## Knowledge Gaps
- **1452 isolated node(s):** `CommandGuardArgs`, `Derivation`, `ReadOnlyMobileCommands`, `AppiumInterfaceConfig`, `DeviceAgentArgs` (+1447 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **274 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `终止契约（core 请求 worker 优雅停止）` and `step 顺序 = 书写顺序，keyword 只决定派发`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Cloud Backend Upgrade Windows Diagram` and `Cloud Delivery Identity Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Cloud Delivery Identity Diagram` and `Execution Cloud Cascade Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Configuration Env Inheritance Diagram` and `Getting Started Component Ownership Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `五层职责切分（用例/产品/执行/浏览器/被测应用）` and `本机应用测试隧道拓扑图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `五层职责切分（用例/产品/执行/浏览器/被测应用）` and `README 运行时拓扑图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `架构总览：五层结构、一次 run 的生命周期、包与发行物` and `scenario 到 job 图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._