# Graph Report - yaozhou  (2026-10-30)

## Corpus Check
- 396 files · ~646,045 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 7356 nodes · 16441 edges · 425 communities (251 shown, 174 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 991 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `89868429`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _gap_engine
- test_backend_cloud.py
- test_main.py
- Job
- test_cloud_reconcile.py
- Provider
- test_schedule.py
- ScopeStarted
- test_workers.py
- test_plan.py
- workers.py
- ADR 0014: AI 优先断言
- ._run_cdk
- _run_step
- _explain_run
- test_stores.py
- test_stack.py
- test_evidence.py
- test_deploy_cmd.py
- test_container.py
- LocalRunStore
- materialize.py
- _render_status
- _StubEcs
- test_devicefarm.py
- ensure_workflow_definition
- ADR-0008
- JobState
- RunState
- ADR 0045: 文档分层与归位
- test_termination_parity.py
- redact_secrets
- test_compose.py
- _RecUploader
- test_worker_variant.py
- query_capabilities
- LocalReportStore
- test_tunnel_cli.py
- test_tunnel_warmup.py
- CONTRIBUTING.md: contributor 指南
- render.py
- gherkai_cli/__main__.py
- cli.py
- main
- ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）
- submission.py
- 云端后端用户文档
- test_lambda_asset.py
- _FakeEcsClient
- ssm_path
- config.py
- test_cloud_integration.py
- test_user_docs.py
- test_detached_launcher.py
- video.py
- test_interrupt_model.py
- _fixture
- main
- BackendStack
- serialize.py
- plan_tree
- redact_secrets
- test_fargate_engine.py
- report_store/local.py
- manifest.json
- evidence.mts
- test_artifact_upload.py
- scan
- _is_transient_network
- textui.py
- JobSource
- test_tunnel.py
- _fake_locator
- devicefarm.py
- 06-devicefarm-appium.mts
- gherkai 变更记录 (CHANGELOG)
- _run_with_refs
- ArtifactUploader
- atomic_write_json
- warmupSession
- _color_env_independent
- Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障
- user-steps.mts
- test_user_steps.py
- test_names_device_farm.py
- use_color
- test_cli_json_contract.py
- 决策
- wire.py
- README Video Specs
- TypeScript Build Config
- test_argument.py
- deploy.py
- Composition Root Architecture
- test_project_config.py
- test_adr_hygiene.py
- build_engines
- Video Material Files
- gherkai_deploy_aws/names.py
- deterministic
- driven
- skill_install.py
- 决策
- Run Store Persistence Ports
- event-sink.mts
- test_sqlite_event_log.py
- 决策
- 决策
- FeatureSource
- test_precheck.py
- dependencies
- test_lambda_handlers.py
- _StampSsm
- Diagram Build Script
- ArtifactUploader
- test_engines_matrix.py
- evidence.test.mts
- ADR 0043：驱动 gherkai 的 agent skill
- release_notes.py
- _stop_fails
- _presend_act_siblings
- Event Wallclock Analysis
- Release Notes Guards
- ensure_app_object
- test_skill.py
- .add_arguments
- run-scope.test.mts
- Dist Metadata Checks
- compose.py
- _doc_rules.py
- parametrize
- Media Conversion Verification
- package.json
- _FakeResult
- FargateEngine
- reconcile.tick（推进器共享入口）
- render_skill_contract.py
- DynamoDB Events Transport ADR
- _hits
- 决策
- tunnel-warmup.test.mts
- minimax_narration.py
- test_skill_deploy_tokens.py
- S3StepArgumentOffloader
- Stateless Run Core Model
- _Recorder
- argument.mts
- test_user_facing_messages.py
- Status
- CONTENT_TYPES
- 0050. 确定性 step 多句柄注册与测试分层
- test_capabilities.py
- parse.py
- artifact-upload.test.mts
- deterministic
- check_version_skew
- engines-matrix.test.mts
- ADR 0035: 本地应用经隧道测试
- scan
- ECS Task Timing Capture
- test_definition_schema.py
- Artifact Uploader Component
- _read_events
- Graphify Refresh Script
- SubprocessEngine
- job-source.mts
- require_boto3
- Cooperative Stop Design
- render_traffic_policy
- Doc Rules Check
- test_devicefarm_client_placement.py
- openai
- redact.mts
- Engine Port & Job Planning
- Scope Tag Parsing
- 执行与推进模型导览（run/submit × local/cloud）
- Context Glossary Guards
- ADR 0037: 分发与打包
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- settings.py
- _engine_with_fake_ecs
- _require
- @playwright/test
- test_reconcile.py
- Echo Test Worker
- Cloud Infra Self-Check
- _ClientError
- devDependencies
- 移动真机支持（1.5）：实施进度总纲
- _CdkWritingContext
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- Gherkin Parse Seam
- files
- Repository Metadata
- test_subprocess_engine.py
- user_steps.py
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试
- DeterministicCtx
- Architecture Diagrams
- Slide Frame SSIM Checks
- artifact_upload.py
- AgentCore CDP Script
- _Calls
- DeterministicKeywordMismatch
- Pre-commit Hook Script
- deterministic.py
- Scenario
- Adapters Package
- user-steps.test.mts
- test_tunnel_host.py
- severity 数值序（_STATUS_SEVERITY）
- Step Matching & Plan Annotation
- ADR-0025
- agentcore-sigv4.test.mts
- verify_project
- gherkai_runtime/names.py
- .enqueue
- precheck.mts
- gemini_image.py
- Index Wait Script
- gherkai Workspace Root
- WebdriverApp
- error-text.mts
- _job_def
- Execution Backend
- Feature Files
- Error Type Classification
- Local Per-Run Advance Process
- .drain
- gherkai Core Package
- AWS Deploy Package
- Runtime Package
- NovaAct Worker Package
- _make_devicefarm_client
- event-sink.test.mts
- constants.py
- job-source.test.mts
- redact.test.mts
- test_lifecycle_states.py
- _explain_emit
- .enabled
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- _pump_log
- local_path_from_uri
- test_bucket_without_logs_dir_fails_loud
- test_noop_uploader_enqueue_and_drain_are_immediate
- ._installed_import_source
- 项目约定
- ._grant_task_role
- _UnavailableEngine
- Engine
- _argv
- read_project_arn
- e2e_harness.py
- default_name
- _role_statements
- ADR-0019
- _await_engine
- gherkai：价值与方法（材料索引）
- test_provider.py
- _advancer_stmts
- CloudTarget
- index.mts
- .preflight
- test_app_upload.py
- test_palette_excludes_verdict_and_default_colors
- _presentation_is_environment_independent
- WarmupFailureError
- test_registry_dump_via_capabilities_real_subprocess
- test_address_pattern_cross_engine_fixture
- test_worker_match_steps_mode_real_subprocess
- test_module_never_creates_or_stops_sessions
- Template
- ADR-0026
- ADR-0027
- ADR-0052
- deterministic_steps.py
- DEFAULT_MODEL
- no-artifacts.test.mts
- MODEL
- MODEL_FAMILY_PATTERNS
- ADR-0033
- ADR-0037
- ADR-0044
- ADR-0016
- ADR-0024
- ADR-0028
- run_scope.py
- ADR-0029
- test_list_workers_reports_unreachable_aws_without_a_traceback
- ADR 0024: worker–core 协议
- ContainerError
- ADR-0032
- ADR-0033
- WebdriverCtx
- _FakeSink
- RFC-3986
- Fargate/ECS RunTask 执行后端
- ADR-0042
- reconciler.py
- @aws-sdk/client-dynamodb
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
- precheck.test.mts
- WARMUP_DENIED_MESSAGE
- map_origin_in_jobs
- WARMUP_MARKER_WAIT_MS
- WARMUP_MARKERS
- url_matches.py
- WARMUP_NAV_TIMEOUT_MS
- WARMUP_PATH
- WARMUP_TITLES
- WarmupDeps
- WarmupFailure
- test_worker_subnets_single_source_across_ssm_and_lambda_env
- DeterministicAssertion
- DeterministicConflict
- DeterministicHandler
- DeterministicHandlers
- DeterministicMeta
- _FakeS3
- Device
- DEVICES
- Entry
- ENTRY_FIELDS
- EntryHandles
- _spawn_and_wait_ready
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
- NormalizedWebdriverEntry
- PLAYWRIGHT_TARGET
- REGISTRY
- RegistryEntry
- Requirement
- REQUIREMENTS
- SelectedHandler
- ADDRESS_PATTERN
- ADR-0020
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0048
- WEB_SCHEMES
- StepTarget
- StepTargetKey
- TARGET_DEVICE_ORDER
- UI_KINDS
- UiKind
- WebdriverDevice
- WebdriverEntry
- WebdriverHandler
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- BROWSER_CLOSE_BUDGET_MS
- CONNECT_BACKOFF_MS
- FailureExitDeps
- INFLIGHT_SETTLE_MS
- Job
- MIN_GRACE_MARGIN_MS
- ADR-0014
- ADR-0020
- ADR-0022
- ADR-0024
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
- ADR-0048
- ADR-0049
- ADR-0050
- ADR-0051
- QUEUE_DRAIN_EXIT_MS
- Scenario
- ShutdownDeps
- Step
- STOP_SESSION_BUDGET_MS
- WORKER_TARGETS
- BaseException
- AST
- @midscene/web

## God Nodes (most connected - your core abstractions)
1. `main()` - 275 edges
2. `Job` - 174 edges
3. `RunMeta` - 140 edges
4. `RunState` - 132 edges
5. `Status` - 114 edges
6. `JobState` - 106 edges
7. `Provider` - 106 edges
8. `JobResult` - 105 edges
9. `Scenario` - 98 edges
10. `Step` - 97 edges

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

## Communities (425 total, 174 thin omitted)

### Community 0 - "_gap_engine"
Cohesion: 0.18
Nodes (11): _delayed_stopped_ecs(), _ev_item(), _gap_engine(), 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 「连续 MISSING」的连续性被有进展的轮次打断：事件/空轮交替、空轮都探到 MISSING，累计 3 次但从不连续 2 次， 宽限 1… (+3 more)

### Community 1 - "test_backend_cloud.py"
Cohesion: 0.04
Nodes (107): _fake_schedule_factory(), _patch_cloud_handles(), _patch_skew(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, status 不解析 variant（ADR 0038）：它只读运行态、不起 task，definition 里的 revision 提交时已定死。, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。 (+99 more)

### Community 2 - "test_main.py"
Cohesion: 0.03
Nodes (114): _capturing_schedule(), _fake_worker_cmd(), _miss(), _plan_names(), parametrize, Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, 定位链全 miss 的结构化异常（带该引擎安装指引），仿 compose.resolve_worker_cmd 的抛出物。 (+106 more)

### Community 3 - "Job"
Cohesion: 0.04
Nodes (100): _device_keys_for_explain(), explain_to_dict(), format_event(), Event, RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, explain 的人与 agent 可读文本（`explain_to_dict` 的文档渲染为树形摘要，节点文字依 ADR 0042… (+92 more)

### Community 4 - "test_cloud_reconcile.py"
Cohesion: 0.06
Nodes (49): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project… (+41 more)

### Community 5 - "Provider"
Cohesion: 0.05
Nodes (63): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 留的口子（ADR 0038「命令族」）：**尚未提供**，以退出码 2 结束并说清为什么与将来怎么落。…, _AbsentEngine, _parse(), parametrize, GetProject 的其他失败（限流、服务端、网络）→ diff 以退出码 2 结束、不调 cdk，消息点名 SSM 路径、记录的 ARN 与原异常，…, 走**真 parser**、按真实接线顺序拼（前端先声明命令面 flag，provider 再贴自己的选项）——不用 SimpleNamespace 手捏… (+55 more)

### Community 6 - "test_schedule.py"
Cohesion: 0.08
Nodes (122): AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, ScenarioDone, ScenarioStarted, StepDone, Votes, Event, 事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收…, 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的… (+114 more)

### Community 7 - "ScopeStarted"
Cohesion: 0.07
Nodes (78): ScopeStarted, EventRecord, plan_next(), project(), project_full(), events 表里一条记录的投影输入（ADR 0034）：reconciler 从表全量重放时，每条 record 携带的信息。 worker…, 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与… (+70 more)

### Community 8 - "test_workers.py"
Cohesion: 0.06
Nodes (93): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), datetime, `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。… (+85 more)

### Community 9 - "test_plan.py"
Cohesion: 0.09
Nodes (43): _cfg(), _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 低于下限的改法要按删掉 tag 后真正接替的来源给：--default-job-timeout 也低于下限时不能只说「删 tag 走缺省」（删了仍被它拒）。, 「任一成员标了即整个 scope 生效」不只看首个成员：带 tag 的成员排在后面也生效。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否… (+35 more)

### Community 10 - "workers.py"
Cohesion: 0.04
Nodes (99): Aws, cleanup_pass(), _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable() (+91 more)

### Community 11 - "ADR 0014: AI 优先断言"
Cohesion: 0.06
Nodes (52): CLAUDE.md（项目约定）, CONTEXT.md（领域概念与术语）, CONTRIBUTING（contributor 入口）, ADR 0001: 范围限于英文 UI, 概念：非英文应用用 @engine:midscene 路由, 概念：Nova Act 中文词语级文本匹配短板, ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码 (+44 more)

### Community 12 - "._run_cdk"
Cohesion: 0.06
Nodes (29): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), cdk_command(), check_cdk(), Path, cdk CLI 的调用前缀：PATH 上的 `cdk` 优先，否则 `npx -y aws-cdk@2`（ADR 0037 决策 6）。都没有 → 空列表。, cdk CLI 前置：PATH 上既无 `cdk` 也无 `npx` → 返回给人看的一句话；能定位 → None。 与 `check_node()`…, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），再找回或建立 Device Farm 项目（ADR 0051 决策 10），… (+21 more)

### Community 13 - "_run_step"
Cohesion: 0.08
Nodes (56): _classify_act_error(), 派发执行一个 step，发出 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+48 more)

### Community 14 - "_explain_run"
Cohesion: 0.09
Nodes (32): _evidence_fixture(), _explain(), _explain_job(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。 (+24 more)

### Community 15 - "test_stores.py"
Cohesion: 0.07
Nodes (62): 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), from_dict(), RunResult → 朴素 dict（机器可读：CI / WebUI / manifest 消费）。 normalize（ADR 0016…, 朴素 dict → RunResult。与 to_dict 往返一致（round-trip 单测护栏）。 def 唯一真值在…, RunMeta → dict（run_meta.json / DDB META 的 meta_json）。键集固定、不适用写 null（ADR 0037 决策…, dict → RunMeta。第一步核结构版本（不等于本读端支持的即抛…, run_meta_from_dict() (+54 more)

### Community 16 - "test_stack.py"
Cohesion: 0.04
Nodes (27): BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler / kicker）的角色都不读 SSM 参数：definition 缺 `worker_task_defs` 按定义违约标… (+19 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.07
Nodes (53): ArtifactUploader, `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _get_uploader(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks() (+45 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 前端自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 19 - "test_container.py"
Cohesion: 0.06
Nodes (45): digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。 (+37 more)

### Community 20 - "LocalRunStore"
Cohesion: 0.07
Nodes (29): RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, Path, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR…, 读回运行态（RunState）；不存在返回 None。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新… (+21 more)

### Community 21 - "materialize.py"
Cohesion: 0.08
Nodes (53): gherkai agent skill 包, evals.json（评测集与 fixture 索引）, 评分子代理提示词模板, assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture() (+45 more)

### Community 22 - "_render_status"
Cohesion: 0.17
Nodes (20): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。 (+12 more)

### Community 23 - "_StubEcs"
Cohesion: 0.22
Nodes (4): 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 24 - "test_devicefarm.py"
Cohesion: 0.17
Nodes (27): project_name(), 找回或建立项目 `{prefix}devices`（只供 `deploy` 在 cdk 之前调用，ADR 0051 决策 10「项目」）。…, 云端 Device Farm 项目名 `{prefix}devices`。, resolve_or_create_project(), _assert_warning(), _enter(), _project(), parametrize (+19 more)

### Community 25 - "ensure_workflow_definition"
Cohesion: 0.12
Nodes (21): worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, ConflictException, exceptions (+13 more)

### Community 27 - "JobState"
Cohesion: 0.04
Nodes (49): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_explain_cloud_reads_evidence_from_s3(), DynamoDBRunStore, _job_state_from_item() (+41 more)

### Community 28 - "RunState"
Cohesion: 0.07
Nodes (59): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…, RunState, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale…, _initial() (+51 more)

### Community 29 - "ADR 0045: 文档分层与归位"
Cohesion: 0.20
Nodes (21): _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏）, test_user_docs.py（用户文档与图源护栏）, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0045: 文档分层与归位, CONTEXT.md 严格词表与术语变更顺序（决策八）, archify 图流程（JSON 图源 + 导出 SVG 入库） (+13 more)

### Community 30 - "test_termination_parity.py"
Cohesion: 0.08
Nodes (49): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, 远程访问会话打开（ADR 0051 决策 4 / 0024「会话事件」）：Create 返回 ARN…, SessionOpened (+41 more)

### Community 31 - "redact_secrets"
Cohesion: 0.14
Nodes (18): Any, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则、三份同文实现。 三份同文实现（本文件、Nova worker…, 三条规则依次作用于一段文本；None 原样返回。 `https://u:p@host/x` →…, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_secrets(), parametrize, 凭据脱敏三条规则的单测（ADR 0035 决策 5；0051 决策 11）。 用例表只有一份：`engines/fixtures/redaction-… (+10 more)

### Community 32 - "test_compose.py"
Cohesion: 0.04
Nodes (75): prune_empty_dirs(), Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`，再缺取配置文件的 profile（ADR 0053 决策…, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_aws_identity() (+67 more)

### Community 33 - "_RecUploader"
Cohesion: 0.05
Nodes (28): _drain_evidence_uploads(), 收尾：**有界**等 evidence 截图的后台队列传完（ADR 0042 决策一）。best-effort、绝不抛。…, _FakeBrowserClient, _FakeCm, _FakeNovaAct, _install_browser_client(), main_fakes(), _RaisingSink (+20 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.08
Nodes (42): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, worker_image_key(), aws(), _fake_aws_creds(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。 (+34 more)

### Community 35 - "query_capabilities"
Cohesion: 0.06
Nodes (45): engine_min_grace(), _is_finite_number(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, 有限的 int / float（bool 单独挡；超出 float 范围的大整数按「不是有限数」处理，不让 math.isfinite 的…, targets 数组的形态校验（ADR 0049 决策 1）：顶层 targets 必有（缺键由调用方按版本不一致拒绝），step 级只在键存在时调用；显式…, _validate_targets() (+37 more)

### Community 36 - "LocalReportStore"
Cohesion: 0.18
Nodes (33): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077…, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。 (+25 more)

### Community 37 - "test_tunnel_cli.py"
Cohesion: 0.08
Nodes (47): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, 不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。, 隧道起不来（如 authtoken 缺失）→ 给退出码 2「没开始执行就被拒」，不产生引擎费用。, local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。 (+39 more)

### Community 38 - "test_tunnel_warmup.py"
Cohesion: 0.09
Nodes (28): _clock(), _FakePage, 隧道会话预热（ADR 0051 决策 13；ADR 0035「边界与不变量」）——Nova worker 侧。 纯逻辑部分（三种可见结果的归因、有界重试）用假…, 两种拒绝都是 precheck_failed、不重试，但各给自己的一句：令牌被拒与会话 cookie 未通过校验的处置不同。, 导航抛网络类异常：不向上抛（外层的建连重试域看不到它、不会以退出码 80 收场），有界重试后归 engine_error。, 停止信号（ADR 0024 flag-only）：预热的退避与等标记都看 stop，收到即抛 WarmupStopped——不算失败、不发…, 退避期间（sleep 即 _stop.wait）收到停止信号：下一次导航之前就抛 WarmupStopped——否则还要再等一次最长 30 秒的导航，…, 预热失败后释放会话出错：不进建连重试域（不重建会话）、归因不被覆盖、scope_done 照发、退出码 1 让泄漏可观测 （ADR 0051 决策 5 与… (+20 more)

### Community 39 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.07
Nodes (42): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, cli 包 contributor 文档, skill 参考：CLI --json 字段契约, skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法 (+34 more)

### Community 40 - "render.py"
Cohesion: 0.08
Nodes (41): _add_act(), _add_device_evidence(), _add_step(), _cost_bits(), _evidence_ref(), _explain_session_lines(), explain_step_expands(), explain_tree() (+33 more)

### Community 41 - "gherkai_cli/__main__.py"
Cohesion: 0.04
Nodes (90): _build_run_meta(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_doctor(), _cmd_explain(), _cmd_list_deterministic(), _cmd_list_engines(), _cmd_reconcile() (+82 more)

### Community 42 - "cli.py"
Cohesion: 0.07
Nodes (32): check_node(), _error_code(), _has_aws_credentials(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client(), _make_sts_client(), _node_major() (+24 more)

### Community 43 - "main"
Cohesion: 0.06
Nodes (34): worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _capabilities(), main(), 本 worker 的能力声明（`--capabilities` 的 stdout，ADR 0036「5.」）。 `min_grace_s` 是 grace…, test_sigterm_and_sigint_both_installed_as_flag_only(), 次序：预热导航 → scope_started → scenario_started → 执行 → scenario_done →…, 预热途中收到停止信号：正常 return 释放会话、不发任何事件、退出码 0——与 scenario 边界的协作停走同一条路径（ADR 0024 flag-…, 预热被拒、释放会话出错、同时停止信号已置位：停止路径不发事件，但退出码仍是 1——释放失败不能被停止分支的 return 0 吞掉 （ADR 0051 决策… (+26 more)

### Community 44 - "ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）"
Cohesion: 0.06
Nodes (51): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）, 墙钟时长归约（step/scenario/scope/run duration_ms）, EngineResolver（按 job.engine 解析 Engine）, 失败隔离 / failFast 旋钮, 优雅终止：schedule 只调 handle.stop(grace), _heartbeat_wrap（静默 worker 心跳注入） (+43 more)

### Community 45 - "submission.py"
Cohesion: 0.09
Nodes (33): progress(), 进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `gherkai run ……, identity_layers(), `compose.resolve_aws_identity` 的配置文件层（region / profile 排在环境变量之后，ADR 0053 决策 2）。, app_entries(), cloud_app_locations(), cloud_device_requests(), complete_cloud_definition() (+25 more)

### Community 46 - "云端后端用户文档"
Cohesion: 0.10
Nodes (40): gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce）, kicker Lambda（冷启动器）, reconciler Lambda（主推进器） (+32 more)

### Community 47 - "test_lambda_asset.py"
Cohesion: 0.12
Nodes (23): make_stack(), make_template(), Template, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path (+15 more)

### Community 48 - "_FakeEcsClient"
Cohesion: 0.15
Nodes (16): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), 运行一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。 (+8 more)

### Community 49 - "ssm_path"
Cohesion: 0.06
Nodes (36): _FakeTable, 假 DDB table 句柄：DynamoDBRunStore…, subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path() (+28 more)

### Community 50 - "config.py"
Cohesion: 0.07
Nodes (52): AppPlatformConfig, _apps_section(), _billing_method(), ConfigError, DevicePlatformConfig, _devices_section(), DevicesConfig, load_project_config() (+44 more)

### Community 51 - "test_cloud_integration.py"
Cohesion: 0.12
Nodes (28): 连真 DDB/S3 的句柄（真表/桶名读环境变量），供集成测试。**没设环境变量就 skip**（不误连、不报错）。 需你先建好真表 + 真桶（见…, real_aws(), core 测试说明（单测 + 集成测试）, _ddb_store(), _is_ddb_too_large(), _offloader(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。 (+20 more)

### Community 52 - "test_user_docs.py"
Cohesion: 0.08
Nodes (44): changelog_unreleased(), final_transcript(), 用户文档里交给口吻表与形态①③启发式扫的部分：CHANGELOG 截到第一个已发行节之前，定稿口播稿整份豁免（空串）， 其余页面全文。截断只保留前缀，故调用方…, CHANGELOG 交给退役词表与口头语表扫的部分，即第一个已发行版本节之前的内容。…, 口播稿是否仍是定稿原文：文件当前 SHA-256 等于同目录 `manifest.json` 所记的值。 定稿原文已配音、已出字幕，改字就得重新配音，故与…, wording_scope(), _default_model_claims(), _default_model_ids() (+36 more)

### Community 53 - "test_detached_launcher.py"
Cohesion: 0.04
Nodes (79): Connection, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。 (+71 more)

### Community 54 - "video.py"
Cohesion: 0.32
Nodes (17): cues(), digest(), link_chapter_title_track(), packets(), probe(), protected_state(), Path, Confirm the first slide at frame zero, hard cuts, and the closing fade. (+9 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.07
Nodes (28): _backoff_interrupted(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured(), _FakeResult, _FakeSink, _Meta (+20 more)

### Community 56 - "_fixture"
Cohesion: 0.05
Nodes (55): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), aws(), fargate(), moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表…, 在 moto mock 下建好 DDB 表 + S3 桶，产出 (boto3 resource/client, 名字) 供云端 adapter 测试注入。 表… (+47 more)

### Community 57 - "main"
Cohesion: 0.04
Nodes (69): main(), _det_feature(), --version 打印「gherkai <发行版本>」并以退出码 0 结束——版本真源是包元数据（git tag → uv-dynamic-…, plan 的分叉与 run/submit **相反**（ADR 0037 决策 3 明示 + ADR 0036 决策 4）：保持 best-effort…, 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。… (+61 more)

### Community 58 - "BackendStack"
Cohesion: 0.09
Nodes (19): Cluster, Construct, BackendStack, BackendStack._build_lambda_asset, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, `-c device_farm_project=` 给的项目 ARN；缺省或等于「待建立」占位时返回 None。 值由命令派生、不给…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个… (+11 more)

### Community 59 - "serialize.py"
Cohesion: 0.09
Nodes (43): plan 形态的应用条目只有别名与包名两键（位置三项由组合根在提交时填入，ADR 0048 决策 3）。, test_plan_json_app_entry_is_exactly_alias_and_app_id(), AppRef, DeviceFarmRequest, 向 AWS Device Farm 要哪台设备（ADR 0048 决策 3）：名字明说服务商、不起中立名；`device_arn` 与…, 应用目标的应用条目（ADR 0048 决策 3）。两个形态：plan 形态只有别名与包名或 bundle id；run / submit 在组合根上传安装包后…, 一个 scope 运行在什么上面（ADR 0048 决策 1）：设备与界面类型；ui_kind 为 app 时带应用条目。缺省即桌面网页。, 机读与 plan 文本共用的紧凑写法（ADR 0048 决策 5 的形态）：`desktop/web`、`android/app:shop`。 (+35 more)

### Community 60 - "plan_tree"
Cohesion: 0.09
Nodes (28): DeviceSelection, plan 标注用的一句（产品语言）：原样展示 ARN 或筛选条件与来源；未指定时说明 run / submit 会拒绝。, plan --json 的 `devices.<平台>`：指定一台时 `{arn, source}`，按版本挑选时 `{os_version,…, 某个平台选哪台设备：`arn` 指定一台，`os_version` 按系统版本族挑选（二者恰一）。`source` 是产品语言的来源说明，进提示与 plan…, selection_label(), selection_to_dict(), _build_selector(), _cmd_plan() (+20 more)

### Community 61 - "redact_secrets"
Cohesion: 0.05
Nodes (32): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与…, 三条规则依次作用于一段文本；None 原样返回。, redact_secrets() (+24 more)

### Community 62 - "test_fargate_engine.py"
Cohesion: 0.09
Nodes (51): _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。 (+43 more)

### Community 63 - "report_store/local.py"
Cohesion: 0.13
Nodes (19): device_header_lines(), scope 表头的设备两行（ADR 0051 决策 8）：代表会话的设备描述、会话 ARN 对应的 Device Farm 控制台链接；桌面 job…, test_console_url_only_for_session_arns(), ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, _fmt_ms(), LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 渲染一行的「原因」片段——job 行与 step 行共用同一份，**别再造第三种样式**。 两分支口径同 render_text（有分类 → err…, 渲染入口页——**local/s3 共享的渲染真理源**（公开名：同包 `s3.py` 是第二个消费者，两 adapter 出一致的入口页）。… (+11 more)

### Community 64 - "manifest.json"
Cohesion: 0.06
Nodes (35): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+27 more)

### Community 65 - "evidence.mts"
Cohesion: 0.09
Nodes (30): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+22 more)

### Community 66 - "test_artifact_upload.py"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 67 - "scan"
Cohesion: 0.09
Nodes (28): _js_comment_raw_lines(), TS / JS 注释的原文（不遮蔽字符串）：`//` 之后的部分，以及 `/* … */` 块内的行。只给本机坐标这类不受字符串干扰的规则用。, 按人读面的规则束扫一个文件，返回 (行号, 类别, 原文)。only_lines 给了就只报这些行（hook 的「只报本次改动的行」）。, scan(), TS / JS 注释里反引号包着的路径也要拦（注释抽取会先遮蔽字符串，本机坐标另按注释原文扫）。, test_machine_coordinate_is_caught_inside_js_comments(), parametrize, Path (+20 more)

### Community 68 - "_is_transient_network"
Cohesion: 0.12
Nodes (31): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是 NovaAct 的… (+23 more)

### Community 69 - "textui.py"
Cohesion: 0.11
Nodes (30): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。, 深度优先找第一个 label 含 needle 的节点（测试与诊断用）。, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，… (+22 more)

### Community 70 - "JobSource"
Cohesion: 0.08
Nodes (12): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）与导航原语… (+4 more)

### Community 71 - "test_tunnel.py"
Cohesion: 0.09
Nodes (32): _gen_secret(), make_tunnel(), NgrokTunnel, Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。 (+24 more)

### Community 72 - "_fake_locator"
Cohesion: 0.05
Nodes (56): _cloud_backend_ok(), _doctor_cloud_json(), _doctor_devices_cloud(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, doctor 云端段末尾的设备支持两行（`backend.devices.project` /…, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；… (+48 more)

### Community 73 - "devicefarm.py"
Cohesion: 0.10
Nodes (24): BaseException, NoReturn, AmbiguousProject, DeviceFarmAccessDenied, _error_code(), list_open_sessions(), OpenSession, _project_exists() (+16 more)

### Community 74 - "06-devicefarm-appium.mts"
Cohesion: 0.05
Nodes (85): ADR-0010, BASE_URL, main(), makePng(), REGION, ADR-0033, BASE_URL, main() (+77 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.09
Nodes (30): gherkai 变更记录 (CHANGELOG), gherkai destroy, --expose-local 隧道模式, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, gherkai deploy push-worker / list-workers (+22 more)

### Community 76 - "_run_with_refs"
Cohesion: 0.16
Nodes (19): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, s3_report_store(), _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。 (+11 more)

### Community 77 - "ArtifactUploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 78 - "atomic_write_json"
Cohesion: 0.12
Nodes (21): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+13 more)

### Community 79 - "warmupSession"
Cohesion: 0.36
Nodes (5): leaveWarmupPage(), oneLine(), waitForMarker(), WarmupPage, warmupSession()

### Community 80 - "_color_env_independent"
Cohesion: 0.67
Nodes (3): _reset_scope_colors(), _color_env_independent(), 本模块的颜色断言不受运行测试的 shell 影响：清掉 NO_COLOR / FORCE_COLOR / TERM=dumb，让「是否终端」成为唯一变量。

### Community 81 - "Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障"
Cohesion: 0.33
Nodes (6): 1. 链路一句话, 2. 签名契约：五条决定成败的细节, 3. 失败模式表, 4. 依赖与自检, Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障, 延伸阅读

### Community 82 - "user-steps.mts"
Cohesion: 0.11
Nodes (15): 确定性 step 加载失败即拒绝运行, fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037, ADR-0037, collectStepFiles() (+7 more)

### Community 83 - "test_user_steps.py"
Cohesion: 0.08
Nodes (42): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` 是 env `GHERKAI_STEPS_DIR`…, _clean_env(), _isolate(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, `_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。, `_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。 (+34 more)

### Community 84 - "test_names_device_farm.py"
Cohesion: 0.11
Nodes (21): Match, device_farm_project_id(), device_farm_session_arn_prefix(), _match_device_farm_project_arn(), 项目 ARN 里 `project:` 之后的项目 id（会话 ARN 以它为前缀段）。形态不对抛 `ValueError`。, 本项目全部远程访问会话的 ARN 通配：`arn:aws:devicefarm:us-west-2:<账户>:session:<项目 id>/*`。形态不对抛…, 项目 ARN 形态校验：须是 `arn:aws:devicefarm:us-west-2:<12 位账户>:project:<项目…, validate_device_farm_project_arn() (+13 more)

### Community 85 - "use_color"
Cohesion: 0.18
Nodes (16): 执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。, color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env() (+8 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.14
Nodes (24): _assert_check_names_documented(), _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, doctor 本机各段的替身：两个引擎都定位得到、自述带全部键，没有部署 provider。, 项名是 `name` 的**值**，键名护栏照不出它：把按引擎后缀的项名归一成 `<engine>` 形态后逐个核对契约页里写了。 (+16 more)

### Community 87 - "决策"
Cohesion: 0.10
Nodes (20): 0051. 远程访问会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034 (+12 more)

### Community 88 - "wire.py"
Cohesion: 0.05
Nodes (68): SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, Cost, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…, _argument_to_json(), _cost_from_json(), _device_request_to_json(), event_from_json() (+60 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 91 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 92 - "deploy.py"
Cohesion: 0.10
Nodes (21): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+13 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_project_config.py"
Cohesion: 0.06
Nodes (76): _add_config_flag(), _add_device_flags(), _add_selection_flags(), _build_parser(), ArgumentParser, run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。, 建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…, 设备目标的选项（ADR 0053 决策 4）：按平台分开的设备 ARN（一个 run 可同时含 Android 与 iOS 的 scope）；run /… (+68 more)

### Community 95 - "test_adr_hygiene.py"
Cohesion: 0.14
Nodes (24): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, 全仓 markdown（含 journey 与工具说明，原文含行内代码）不写本机坐标：个人目录下的绝对路径、本地 clone 目录名只在产出机器上… (+16 more)

### Community 96 - "build_engines"
Cohesion: 0.08
Nodes (33): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, gherkai-runtime README (PyPI 入口页), Path (+25 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "gherkai_deploy_aws/names.py"
Cohesion: 0.10
Nodes (18): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, 云端 Device Farm 项目 ARN 的 SSM 路径（ADR 0051 决策 10、ADR 0033 资源清单第 11 条）。 写者是 stack…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, 生效 VPC 取值的 SSM 路径（ADR 0037 决策 6「VPC 取值持久化比对，三态齐全」）。 值形态三种：`default` / `new:<所建…, ssm_device_farm_project_path(), ssm_vpc_path() (+10 more)

### Community 99 - "deterministic"
Cohesion: 0.09
Nodes (41): clear(), deterministic(), list_registry(), match(), match_batch(), 注册一条确定性 step。两种写法： 装饰器（等价于只有 playwright 句柄）： @deterministic(r'页面地址匹配…, 注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。, 在注册表里找命中 text 的唯一条目。 返回 Hit 或 None（未命中走 AI）。命中多条 → DeterministicConflict； 命中一条但… (+33 more)

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

### Community 105 - "test_sqlite_event_log.py"
Cohesion: 0.08
Nodes (26): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore, 配好的 S3ResultStore（注入 aws fixture 建好的桶），供 ResultStore 对拍测试。, s3_result_store() (+18 more)

### Community 106 - "决策"
Cohesion: 0.13
Nodes (15): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 不升 schema 版本，在 schema 1 上增键, 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端 worker 在建会话前按自己的 `targets` 自检 (+7 more)

### Community 107 - "决策"
Cohesion: 0.13
Nodes (15): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 7. Midscene 复用边界 (+7 more)

### Community 108 - "FeatureSource"
Cohesion: 0.11
Nodes (38): FeatureContractError, 用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig, Job (+30 more)

### Community 109 - "test_precheck.py"
Cohesion: 0.11
Nodes (27): _num(), precheck_job(), precheck_schema(), precheck_target(), 建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的…, (device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。, 名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。, 秒数的写法：整数值不带小数点（1500 而不是 1500.0），其余按原值；与 Midscene 侧的插值结果一致。 (+19 more)

### Community 110 - "dependencies"
Cohesion: 0.11
Nodes (19): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js (+11 more)

### Community 111 - "test_lambda_handlers.py"
Cohesion: 0.02
Nodes (120): cloud_env(), _FakeEcs, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。 (+112 more)

### Community 112 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 113 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 115 - "test_engines_matrix.py"
Cohesion: 0.13
Nodes (19): _available_step_targets(), _probe_deterministic_dispatch(), plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…, plan 标注用：该引擎每条确定性 step 实际可用的目标（声明与 worker 支持目标的交集，ADR 0049 决策 3），按模式索引。…, 把名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」而不是「在Android 网页上」）；全中文的名称原样。, (device, ui_kind) → 「桌面网页」「Android 应用」这类名称；未知取值原样拼出（自述形态由组合根校验，这里只呈现）。, spaced(), target_label() (+11 more)

### Community 116 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 117 - "ADR 0043：驱动 gherkai 的 agent skill"
Cohesion: 0.20
Nodes (15): ADR 0001：范围限定英文 UI, ADR 0041：面向 agent 的 CLI 可操作面, ADR 0043：驱动 gherkai 的 agent skill, 评测去污染硬规则（CLI 来自仓库外 wheel、skill 副本随机目录、舞台路径随机）, 物化式 fixture 与可搬迁契约, 两臂评测法（with-skill 对 baseline）, ADR 0047：CLI 人读输出用 rich 渲染表格与树, gherkai_runtime.textui（表格 / 树 / 样式单点） (+7 more)

### Community 118 - "release_notes.py"
Cohesion: 0.48
Nodes (6): main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems()

### Community 119 - "_stop_fails"
Cohesion: 0.12
Nodes (19): parametrize, 按次给 Stop 的异常：第 n 次 Stop 抛 excs[n-1]（None 表示成功），之后都成功。, AgentCore 会话已建起、NovaAct 进入时抛网络错、随后释放会话又抛：释放异常不冒泡、不进建连重试判定；建连失败照常重试，…, 同一窗口里停止信号已置位：不再重试、不发事件，退出码 1——释放失败不能被停止分支吞成 0。, 建连期间收到停止信号且建连抛网络错、会话正常释放：这是建连失败不是释放失败——按停止路径以 0 退出、零事件。 守住「只有释放阶段抛出才记…, 首个会话释放失败、随后建连重试耗尽：退出码 1 而不是 80——泄漏可观测性压过网络分类（ADR 0028），core 不按网络故障重试。, 正常路径（无隧道）释放 AgentCore 会话失败：判定照发（scope_started、scope_done），退出码 1——对称 Midscene 的…, 会话已 Start、取 CDP 连接头撞网络错、Stop 又失败：此前这段藏在 SDK 的上下文管理器 __enter__ 里，Stop… (+11 more)

### Community 120 - "_presend_act_siblings"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…, act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _traj_refs(), _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 121 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Release Notes Guards"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 123 - "ensure_app_object"
Cohesion: 0.17
Nodes (18): app_object_key(), AppLocation, AppUploadError, ensure_app_object(), _error_code(), BaseException, datetime, Exception (+10 more)

### Community 124 - "test_skill.py"
Cohesion: 0.04
Nodes (66): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), is_placeholder(), NamedTuple, skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 一个 `gherkai …` 代码跨的拆解结果。 `words` 是 `gherkai` 之后、第一个 flag… (+58 more)

### Community 125 - ".add_arguments"
Cohesion: 0.19
Nodes (9): ArgumentParser, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6； 三者与…, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`… (+1 more)

### Community 126 - "run-scope.test.mts"
Cohesion: 0.05
Nodes (28): agentOpts(), cumulativeTokens(), drainArtifactQueue(), isTransientNetwork(), log(), main(), runScenario(), runStep() (+20 more)

### Community 127 - "Dist Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 128 - "compose.py"
Cohesion: 0.04
Nodes (59): available_targets(), build_fargate_engines(), cloud_artifact_locations(), _default_targets(), _find_worker_spec(), is_pure_release(), _make_ddb_table(), _make_ecs_client() (+51 more)

### Community 129 - "_doc_rules.py"
Cohesion: 0.09
Nodes (37): ai_side_docs(), all_markdown(), classify(), code_comment_files(), comment_blocks(), comment_prose_lines(), comment_units(), _consecutive_runs() (+29 more)

### Community 130 - "parametrize"
Cohesion: 0.11
Nodes (18): _bucket_lifecycle_rules(), _events_table_actions(), parametrize, 产物桶的生命周期规则**全集**恰为 expire-job-in 与 expire-apps 两条（ADR 0033、ADR 0051 决策 9），与…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 带合法项目 ARN 时恰多出一条 `device-farm-project`，值逐字等于传入的 ARN（ADR 0033 资源清单第 11 条、ADR…, 非占位但形态不合法的项目 ARN 在合成期抛 ValueError（ADR 0037 决策 6）：拼错的会话前缀只会在运行期表现为 AccessDenied。, 缺省或「待建立」占位不 fail-fast（与 version 相反，ADR 0037 决策 6）：部署方没有 Device Farm… (+10 more)

### Community 131 - "Media Conversion Verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 132 - "package.json"
Cohesion: 0.12
Nodes (16): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+8 more)

### Community 133 - "_FakeResult"
Cohesion: 0.12
Nodes (8): _ActBoom, _FakeResult, _Meta, _NavErrorNova, RuntimeError, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 Nova SDK 的 act 异常：与成功结果一样带 metadata（time_worked_s 已真实计费、trajectory 已写盘）。

### Community 134 - "FargateEngine"
Cohesion: 0.16
Nodes (13): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+5 more)

### Community 135 - "reconcile.tick（推进器共享入口）"
Cohesion: 0.17
Nodes (13): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState）, status --wait 接力推进 (+5 more)

### Community 136 - "render_skill_contract.py"
Cohesion: 0.23
Nodes (12): docs/internals/cli-json-contract.md（机读字段级参考页）, _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。 (+4 more)

### Community 137 - "DynamoDB Events Transport ADR"
Cohesion: 0.18
Nodes (13): DynamoDB 共享 events 表作 events-out 传输, EventSink（可注入事件出口）, events 表键设计 PK=run_id#scope_id, SK=seq, events item TTL 自动过期（7 天 expires_at）, 读一致性（流式期 EC 游标 + 终读强一致）, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列 (+5 more)

### Community 138 - "_hits"
Cohesion: 0.40
Nodes (6): _hits(), parametrize, Path, GitHub Release 正文由 CHANGELOG.md 本版节与 `.github/release_body_footer.md`…, test_github_release_body_is_for_users_only(), test_shipped_readme_is_for_users_only()

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

### Community 143 - "S3StepArgumentOffloader"
Cohesion: 0.06
Nodes (37): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, 指针必须是文本（s3:// URI）；别的类型是同版本下的定义违约，不让它变成 urlparse 的裸 AttributeError。, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与… (+29 more)

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "_Recorder"
Cohesion: 0.12
Nodes (15): cdk(), _clean_aws_env(), _FakeEngine, fixture, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。 (+7 more)

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "test_user_facing_messages.py"
Cohesion: 0.27
Nodes (10): _docstring_node_ids(), AST, 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 148 - "Status"
Cohesion: 0.03
Nodes (137): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, FargateWorkerHandle, NamedTuple, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, 一次 DescribeTasks 探测的结果——**三个正交事实各自命名**（ADR 0024「exitCode 落值延迟」；前两个见下、第三个…, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称… (+129 more)

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.18
Nodes (11): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 2. handler 上下文：七个字段与一条不变量, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据 (+3 more)

### Community 151 - "test_capabilities.py"
Cohesion: 0.14
Nodes (19): _clean_env(), `--capabilities` 自述入口单测（ADR 0036「5.」/ ADR 0024「引擎自报下限」，Nova 侧）。…, 不注入任何 env（旧宿主 / 手动直接运行）：下限仍 ≥ 缺省 act 上界 120 + margin，不退化成小值。, 不读 stdin：stdin 是一根**写端一直开着**的管子——真去读就永远阻塞、这里就 timeout 失败。…, steps 加载失败在这个入口也 fail-loud（ADR 0037 决策 4「两个非 job 入口同样加载 steps」）： 非 0 退出、stderr…, `--list-deterministic` 已删、**不留别名**（ADR 0036 被拒方案末条「每个自述项一个独立 flag」）。 只有真 argv…, 子进程 env：保留运行必需项，剥掉 GHERKAI_* / AWS_* / NOVA_*（含本机 region 与凭证落点）。 剥 AWS…, 键集恰六个，且 `min_grace_s` 是注入的 `NOVA_ACT_TIMEOUT_S` 加 worker 侧 margin（组合根查它当 grace… (+11 more)

### Community 152 - "parse.py"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 153 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 155 - "check_version_skew"
Cohesion: 0.12
Nodes (17): check_version_skew(), 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。, 戳缺失表示本机制之前部署的环境 → warn（不拦）+ 提示运行一次 `gherkai deploy` 写入。, 任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。, 未装成包（从源码直接运行）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。, 只比 release 段（决策 7）：位数不同补零后比；同 release 段的 rc 与正式版视作同版本。, `cli_version` 必给（决策 7 比的是「写任务定义那一方」的版本）：不缺省成 gherkai-runtime 的版本—— editable… (+9 more)

### Community 156 - "engines-matrix.test.mts"
Cohesion: 0.20
Nodes (7): DEVICE_LABEL, HANDLE_BY_DEVICE, MATRIX, ADR-0049, ADR-0050, Row, UI_KIND_LABEL

### Community 157 - "ADR 0035: 本地应用经隧道测试"
Cohesion: 0.06
Nodes (40): ADR 0011: AgentCore 浏览器 system default vs custom, 系统默认浏览器 aws.browser.v1, 自建 custom browser（create-browser）, tunnel.py（--expose-local 隧道 provider）, tunnel_host.py（隧道宿主编排 + 守护 TTL）, @engine:<midscene|novaact> 引擎选择 tag, @timeout:<N> job 墙钟预算 tag, ADR 0035: 本地应用经隧道测试 (+32 more)

### Community 159 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 160 - "test_definition_schema.py"
Cohesion: 0.15
Nodes (22): parametrize, Path, definition 结构版本闸门（ADR 0037 决策 7）在 CLI 的接线：status / explain /…, 缺戳例外的接线：谓词为真的 run / submit 遇无版本戳后端以退出码 2 结束、资源检查一次不做；谓词为假（纯桌面）只警告放行。 谓词本身在…, 别的版本写出的 run 目录连运行态的形状都不保证：先核结构版本，再读运行态——否则「请升级」会变成一个解析异常。, 本机接力宿主读到同版本下形态违约的提交记录（这里真的从 run_meta.json 删掉一个 job 的 target 键）：CLI 读端有退出码可交，…, 读头阶段的形态违约（结构版本字段不是整数）：三个本机读端都以退出码 2 结束并说明，不是裸异常；运行态不被改动、不写 run 级消息…, 云端两个读端读 META 头时的形态违约（结构版本字段不是整数）：以退出码 2 结束并说明，不是裸异常；之后不再读运行态。 (+14 more)

### Community 161 - "Artifact Uploader Component"
Cohesion: 0.23
Nodes (12): Act-Boundary Pre-upload, ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX Injection, Artifact Uploader Component, uploader.flush_and_cleanup(dir), Accepted Residual Un-uploaded Artifacts, Scenario-Boundary Log Pre-upload (Midscene only), Midscene uploader.snapshotLogs(logDir, seen, budgetMs), Midscene uploader.snapshotReport(path) (+4 more)

### Community 162 - "_read_events"
Cohesion: 0.18
Nodes (10): _join_pumps(), Event, Job, Popen, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 以非零退出码（含被信号强杀的负码）结束时抛错（终结函数按退出码判）。 纯阻塞行读、纯…, 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的… (+2 more)

### Community 163 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 164 - "SubprocessEngine"
Cohesion: 0.17
Nodes (12): Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, _assert_process_gone(), _kill_quietly(), 等 pid 文件里出现至少 n 行（孙进程由它自己登记，可能比父进程晚一点）；到时返回当前已有的。, 强杀后事件管道仍不 EOF（孙进程持有写端）：reader 线程永远读不到 EOF，schedule 只能在排空上界到点结束消费、按退出码未知…, 内容完整（scope_done 已到）后 worker 挂死且无视 SIGTERM：deadline 到点催停 → 宽限耗尽 SIGKILL → 管道…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr… (+4 more)

### Community 165 - "job-source.mts"
Cohesion: 0.12
Nodes (11): Job, JOB_KEYS, JobApp, JobDeviceRequest, JobSource, JobTargetShape, Missing, ADR-0016 (+3 more)

### Community 166 - "require_boto3"
Cohesion: 0.17
Nodes (6): 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…

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
Cohesion: 0.17
Nodes (18): AST, Module, _imports_devicefarm_module(), _is_devicefarm_client_call(), _production(), _python_sources(), 差集护栏：Python 侧的 Device Farm 客户端只在 `gherkai_runtime.devicefarm` 构造（ADR 0051 决策…, `<任意>.client("devicefarm", …)`、`client(service_name="devicefarm")`、botocore 会话的… (+10 more)

### Community 172 - "redact.mts"
Cohesion: 0.33
Nodes (4): MASK, ADR-0035, ADR-0051, SECRET_MASK

### Community 173 - "Engine Port & Job Planning"
Cohesion: 0.33
Nodes (7): Engine port（run_scope → WorkerHandle + Event 迭代器）, FargateEngine adapter, JobSource（可注入 job 入口）, pipe 传输实现 die（worker I/O 边缘必改）, Job（一个 scope = 一个会话边界）, plan 模块（.feature → Job 列表）, select 谓词（scenario 筛选）

### Community 174 - "Scope Tag Parsing"
Cohesion: 0.29
Nodes (7): engine 解析（scope 级）, id 派生（scopeId / scenarioId 关联键）, 一个 scenario 多个 @scope 值 → 报错, scope seam（tag 分组 + engine 校验）, scope 全局命名空间（跨文件合并，撞名 warning）, timeout 解析（@timeout:N → Job.timeoutS）, uri 互异契约（重复 uri → 报错）

### Community 175 - "执行与推进模型导览（run/submit × local/cloud）"
Cohesion: 0.08
Nodes (45): cli/DEVELOPMENT.md, gherkai-deploy-aws contributor 手册, Archify Diagram Viewer Preset (classic, showcase quality), 五层全景图, 一次 run 的生命周期图, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram (+37 more)

### Community 176 - "Context Glossary Guards"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条由…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 177 - "ADR 0037: 分发与打包"
Cohesion: 0.09
Nodes (37): ADR 0005: 单一共享 feature 文件, 双语言裂缝（物理约束）, ADR 0006: 形态 A——两个子工程、无编排器, 公共设施落在核心库层（报告归集/会话生命周期/跑批入口）, ADR 0013: 跨引擎共享边界, 跨引擎共享止于 features/（Gherkin 单一事实源）, ADR 0015: v1 定位——柔性冒烟而非回归, 默认 AI 判断断言层（QA 零代码） (+29 more)

### Community 178 - "Graceful Stop Contract"
Cohesion: 0.33
Nodes (6): act 有界返回（per-act timeout）, 引擎经 --capabilities 自报 min_grace_s, FargateWorkerHandle.stop → StopTask, grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, 机制层：Engine adapter / WorkerHandle 把停翻成机制

### Community 179 - "Worker Termination Contract"
Cohesion: 0.33
Nodes (6): 事件流结束信号 / 存活判定迁移, exitCode 落值延迟与 MISSING 第三态, 未来演进：显式 core→worker 控制通道, Midscene worker 有序显式 cleanup handler, 逻辑层：schedule 经 worker 句柄请求停（handle.stop）, 终止契约（core 请求 worker 优雅停止）

### Community 180 - "Package URL Links"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 181 - "settings.py"
Cohesion: 0.12
Nodes (23): 命令行的进度与诊断输出（ADR 0047）：一个函数，供 `__main__` 与各编排模块共用。, cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, apply_project_config(), config_layers(), configurable_keys(), convert_config_value(), find_option_action(), _is_repeatable() (+15 more)

### Community 182 - "_engine_with_fake_ecs"
Cohesion: 0.25
Nodes (8): _engine_with_fake_ecs(), DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null(), test_probe_task_stopped_with_exit_code()

### Community 183 - "_require"
Cohesion: 0.23
Nodes (12): _argument_from_dict(), _argument_to_dict(), Scenario, Step, StepArgument, 固定键集的读法：键必须在（值可为 null），缺键按定义违约报——不再用缺省值兜（那是结构版本号之前的兼容手法）。, step 的多行参数（可省：无参数的 step 不带 argument 键，契约页如此登记）；有则 kind 与对应正文键必在，不补空值。, _require() (+4 more)

### Community 185 - "test_reconcile.py"
Cohesion: 0.09
Nodes (35): 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher, _job(), _meta(), _OrderRecordingRunStore (+27 more)

### Community 186 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 188 - "_ClientError"
Cohesion: 0.11
Nodes (9): _Cfn, _ClientError, _DeviceFarmStub, df(), Exception, `gherkai_runtime.devicefarm` 三个入口的替身，并记下调用。默认：SSM 无记录、diff 核对时记录的项目存在、找回或建立的…, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, Device Farm 与项目记录读取一律打桩（autouse：现有 cdk 用例不经此就会直连真 SSM 与 Device Farm，仓库踩过一次同类坑）。… (+1 more)

### Community 189 - "devDependencies"
Cohesion: 0.29
Nodes (7): @aws-sdk/client-device-farm, devDependencies, @aws-sdk/client-device-farm, @types/node, typescript, @types/node, typescript

### Community 190 - "移动真机支持（1.5）：实施进度总纲"
Cohesion: 0.29
Nodes (6): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）, 实施期要核的点（ADR 已定、实施时顺手验证）, 恢复现场, 现场, 移动真机支持（1.5）：实施进度总纲, 遗留项

### Community 191 - "_CdkWritingContext"
Cohesion: 0.21
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

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
Cohesion: 0.20
Nodes (24): _engine(), _job(), _mode_job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, fail-fast 对多个仍在运行的真子进程：先全部落定再并行发停止请求。关掉心跳，victim 的线程阻塞在管道读上、看不到 abort_flag，…, 同一 handle 的两次 stop 重叠（主线程的批量停与 worker 线程收尾时的幂等停）：都正常返回、不抛，进程被回收。, 内容完整后收尾拖过预算、被催停后协作以 0 退出：判定按内容（PASSED），不记超时（ADR 0034 机制二「内容完整后不再仲裁」）。 (+16 more)

### Community 197 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 201 - "移动真机支持（1.5）：实施批次的改动面与先写的护栏测试"
Cohesion: 0.50
Nodes (3): 7. B8-deploy-iac：部署侧：权限、Device Farm 项目找回或建立、SSM、doctor 设备项, 8. B6-midscene-device：Midscene worker 设备模块（接缝、命令守卫、能力探测、适配器、终结四阶段、evidence）, 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试

### Community 203 - "Architecture Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, gherkai 架构图发布入口页, 执行与推进全景交互图

### Community 204 - "Slide Frame SSIM Checks"
Cohesion: 0.67
Nodes (3): slide_area_ssim_checks, at_31_seconds, first_frame

### Community 205 - "artifact_upload.py"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 207 - "_Calls"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 210 - "deterministic.py"
Cohesion: 0.10
Nodes (23): _closed_set(), DeterministicConflict, DeterministicKeywordMismatch, _Entry, Handles, Hit, _hits(), _normalize_handlers() (+15 more)

### Community 211 - "Scenario"
Cohesion: 0.08
Nodes (46): 两个填完入口（ADR 0048 决策 3）：没有设备请求的设备 job 在本机与云端入口都以退出码 2 被拒，校验在入口内部、调用方不另调。, 写 definition 之前的结构校验（ADR 0048 决策 3 第一处）：组合根尚未填入设备请求的设备 job 以退出码 2 被拒；桌面 job 放行。, 执行前预检的第二项目标检查（ADR 0048 决策 3）：job 墙钟预算超过该目标的会话上限即拒绝；桌面条目不带上限不检查。, test_complete_definition_entry_points_run_the_pre_write_check(), test_target_rejections_flag_timeout_over_session_limit(), test_validate_definition_rejects_plan_form_device_job_before_writing(), step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。 (+38 more)

### Community 213 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 214 - "test_tunnel_host.py"
Cohesion: 0.09
Nodes (29): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的四件产物：映射过的 definition + 隧道模式的额外请求头 + 会话预热地址 + 隧道事实（收尾凭据）。…, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, start_tunnel_for_jobs() (+21 more)

### Community 215 - "severity 数值序（_STATUS_SEVERITY）"
Cohesion: 0.32
Nodes (8): 退出码基于 run 级 severity, _NON_VERDICT 与 _aggregate 入口过滤, severity 数值序（_STATUS_SEVERITY）, Status.ABORTED（core 派生态）, Status.PENDING / RUNNING（生命周期前置态）, Status.SKIPPED（core 派生态）, step 级短路：step_skipped 事件 + shortcircuited 布尔, TERMINAL_STATUSES（终态真源，取补定义）

### Community 219 - "verify_project"
Cohesion: 0.17
Nodes (10): 用 GetProject 只读核对项目是否还在（供 `diff` 核对 SSM 记录的 ARN，ADR 0051 决策 10「项目」）：在则…, verify_project(), 网络故障：botocore 抛的不是 ClientError，Stubber 排不出这种失败，故用假客户端。, 项目已被手动删除：返回 False 交给调用方处置。Stubber 只排了 GetProject，任何列举或建立的调用都会因没有排好的响应而失败。, 非 NotFound、非无权限的错误原样抛出：既不当成「项目不存在」，也不当成无权限。, test_verify_project_access_denied_is_classified(), test_verify_project_network_error_propagates(), test_verify_project_not_found_is_false_without_listing_or_creating() (+2 more)

### Community 220 - "gherkai_runtime/names.py"
Cohesion: 0.07
Nodes (34): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_worker_template_path(), 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), ecr_repo_name(), image_tag(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。… (+26 more)

### Community 223 - "precheck.mts"
Cohesion: 0.23
Nodes (12): DEVICE_LABEL, ADR-0024, ADR-0049, ADR-0051, precheckJob(), precheckSchema(), precheckTarget(), spaced() (+4 more)

### Community 224 - "gemini_image.py"
Cohesion: 0.33
Nodes (4): HTTPRedirectHandler, NoRedirect, 演示制作规范, 演示制作与媒体工具说明

### Community 228 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 229 - "_job_def"
Cohesion: 0.31
Nodes (8): S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…, test_load_all_paginated_preserves_failed_verdict(), test_load_all_paginates_beyond_1000(), test_load_all_stable_order(), test_prefix_isolates_runs(), test_save_load_round_trip(), test_scope_id_with_slash_not_subprefix(), _job_def()

### Community 240 - "_make_devicefarm_client"
Cohesion: 0.20
Nodes (10): _make_devicefarm_client(), devicefarm 客户端：区域恒为 DEVICE_FARM_REGION，与 profile 或环境变量给的后端区域无关。抽出来供测试替换。, df(), _isolated_aws_env(), fixture, 环境变量与 profile 都把后端区域给成 us-east-1，客户端仍落在 us-west-2。, 不读本机的 AWS 配置与凭证：假凭证、空配置文件，后端区域给 us-east-1（用来反证客户端没有跟着后端区域走）。, 真 devicefarm 客户端外包 Stubber，并替换模块的客户端工厂；记录工厂收到的 profile。 (+2 more)

### Community 242 - "constants.py"
Cohesion: 0.28
Nodes (7): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, _fmt_seconds(), 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开…, 取 act / act_get 的返回值或其抛出的异常上 metadata.time_worked_s；没有则返回 None。 失败的 act…, run(), _time_worked_s(), workflow

### Community 245 - "test_lifecycle_states.py"
Cohesion: 0.05
Nodes (28): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerExitError, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity() (+20 more)

### Community 246 - "_explain_emit"
Cohesion: 0.25
Nodes (8): _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches(), explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…, 读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。…, 没有判定明细可渲染时的输出：人读打一行提示、`--json` 仍只打一个（scopes 为空的）文档。恒以退出码 0 结束。 退出码 0 而非 2…, local/cloud 共用的后半段：取判定明细 → 筛 scenario/step → 合成文档 → 打文本或 JSON。 带 `scope_id` 时只…

### Community 249 - "deterministic.test.mts"
Cohesion: 0.33
Nodes (4): HANDLES_FIXTURE, META, ADR-0022, ADR-0050

### Community 251 - "_pump_log"
Cohesion: 0.25
Nodes (8): _pump_log(), scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, _scope_color(), worker 日志逐行转发时盖住隧道凭据（ADR 0035 决策 5）：写 log_sink 与写本进程 stderr 两条分支都要盖。 直接喂…, test_pump_log_colors_prefix_only_when_policy_says_so(), test_pump_log_masks_tunnel_credentials_in_sink_and_stderr(), test_scope_colors_assigned_in_order_without_collision_and_stable()

### Community 252 - "local_path_from_uri"
Cohesion: 0.40
Nodes (5): local_path_from_uri(), Path, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…, 若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 **公开小工具**（本模块 href…, _relative_href()

### Community 255 - "._installed_import_source"
Cohesion: 0.33
Nodes (4): 把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容是本包 `lambdas/` 的 handler…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it()

### Community 256 - "项目约定"
Cohesion: 0.29
Nodes (6): graphify, 代码纪律, 工作方式, 文档纪律, 沟通, 项目约定

### Community 257 - "._grant_task_role"
Cohesion: 0.47
Nodes (3): task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, Midscene task role 的设备目标权限，逐条对应 ADR 0033 task role 权限表的 devicefarm 与应用前缀各行（ADR…, Role

### Community 258 - "_UnavailableEngine"
Cohesion: 0.33
Nodes (3): Exception, 某引擎这次装配不出来时的「一用即抛」空占位项——两个后端共用（local: ADR 0037 决策 3；cloud: ADR 0038）。 存在的理由：两个…, _UnavailableEngine

### Community 259 - "Engine"
Cohesion: 0.07
Nodes (26): Engine, Event, Job, 执行引擎 port（ADR 0016）。 schedule 经此起 worker；adapter 形状一致（spawn node 子进程 / spawn…, 起一个 worker 运行这个 job，返回 (句柄, ADR 0024 事件流迭代器)。 事件流逐条产出（ADR 0024 流式）；迭代结束表示…, _ask_worker(), local_artifact_locations(), match_deterministic() (+18 more)

### Community 260 - "_argv"
Cohesion: 0.08
Nodes (39): _argv(), _context_pairs(), _deploy(), _parse_destroy(), 只有 diff 核对：--synth-only 与 destroy 直接沿用 SSM 现值，即使记录的项目其实已不存在也不调 GetProject、不警告。, GetProject 无权限 → diff 与 deploy 同一降级：按记录里的项目计算变更集（cdk context 带该…, 完全没有凭证时只有 --synth-only 可回落占位；diff 与 destroy 照常去读、读失败以退出码 2 结束。, 完全没有凭证（也没有 region）时 --synth-only 照样离线导出：项目取「待建立」占位，并在 stderr 警告导出的模板不含远程… (+31 more)

### Community 261 - "read_project_arn"
Cohesion: 0.33
Nodes (6): 从后端区域的 SSM 读项目 ARN（`ssm_path(prefix, DEVICE_FARM_PROJECT_KEY)`，stack 资源写入）。…, read_project_arn(), 读不到不等于没有：其他错误回落「待建立」会让 diff 把已部署的设备授权显示成删除，由调用方决定退出码（ADR 0051 决策 10）。, test_read_project_arn_missing_parameter_is_none(), test_read_project_arn_other_errors_propagate(), test_read_project_arn_returns_stored_value()

### Community 262 - "e2e_harness.py"
Cohesion: 0.23
Nodes (11): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, --interrupt 中断时机矩阵, e2e_harness.py（opt-in 手动端到端验证脚本）, Path, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, harness 报告判读要点（sample_valid 先于 n_lost）, run() (+3 more)

### Community 263 - "default_name"
Cohesion: 0.33
Nodes (6): default_name(), job_timeout_schedule_prefix(), prefix + 基名（原样拼，prefix 含分隔符由部署方负责）。CDK 与 cli 共用此推导 → 单一事实源。, job timeout schedule 的名字空间前缀 `{prefix}job-timeout-`（其后接 run+scope 摘要段）。 **含尾部…, test_default_name_prefix_original_concat(), test_project_name_is_prefix_plus_base()

### Community 264 - "_role_statements"
Cohesion: 0.16
Nodes (18): _all_actions(), _as_list(), IAM 资源 ARN 已收窄（ADR 0033）——回归护栏：防将来改回 * 或踩 account=aws 陷阱。 收窄依据是 AWS SAR…, 某角色全部 policy 语句的原样列表；按 policy 的 Roles 引用里的逻辑 id 片段认角色（如 `TaskRoleMidscene`）。, 带项目 ARN 合成时 Midscene task role 的设备权限逐条对照 ADR 0033 的权限表。…, 应用存在性检查的 `s3:ListBucket`：资源是产物桶本身，条件 `StringLike` `s3:prefix` 为 `apps/*`（ADR…, 两个引擎 task role 分立（ADR 0033）：设备目标只由 Midscene 执行，Nova 的 role 带项目 ARN 合成时也零 Device…, 不带项目 ARN 或带「待建立」占位合成时，整个模板零 Device Farm 动作，两个 task role 都没有 ListBucket（ADR 0037… (+10 more)

### Community 266 - "_await_engine"
Cohesion: 0.60
Nodes (5): _await_engine(), _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 267 - "gherkai：价值与方法（材料索引）"
Cohesion: 0.60
Nodes (5): 演示材料索引, 价值与方法 视频章节, 价值与方法 纯口播稿, gherkai：价值与方法（材料索引）, 价值与方法 讲者备注

### Community 268 - "test_provider.py"
Cohesion: 0.05
Nodes (50): classify_vpc_state(), SSM 里记的生效取值 `stored` 是否与本次 `--vpc requested` 一致。 三种取值形态见…, 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, vpc_spec_matches(), _all_option_dests(), _app_context_keys(), _ctx(), ArgumentParser (+42 more)

### Community 269 - "_advancer_stmts"
Cohesion: 0.50
Nodes (4): _advancer_stmts(), 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…, test_reconciler_and_kicker_have_the_same_permission_face()

### Community 270 - "CloudTarget"
Cohesion: 0.50
Nodes (3): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序即链上顺序。

### Community 271 - "index.mts"
Cohesion: 0.40
Nodes (4): ADR-0022, ADR-0036, ADR-0037, ADR-0050

### Community 273 - "test_app_upload.py"
Cohesion: 0.17
Nodes (15): _ClientError, _file(), Exception, Path, 安装包上传与复用（ADR 0051 决策 9）：键按内容哈希、404 上传（managed 带标签）、年龄在复用窗口内复用、超窗同键刷新、刷新失败重传、…, boto3 的 upload_file 把 ClientError 包成自己的 S3UploadFailedError（不是 botocore 异常）：404…, 假 S3 client：head 按预设返回或抛；记录 upload_file / copy_object 的入参；可让它们失败。, _S3 (+7 more)

### Community 285 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): navigate(), deterministic, 确定性 step 脚手架（ADR 0020/0022）—— 本包随 worker 发行的注册表内容：**只有内建导航一条**。 机制（ADR…, 内建导航（ADR 0020 第 3 条）：整句为地址的 Given / When step，直接打开，不走 AI。

### Community 297 - "run_scope.py"
Cohesion: 0.05
Nodes (42): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, _aggregate(), _attach_evidence(), _BrowserSession, _collect_traj(), _cost_from_result(), _emit_scenario_done_unless_stopped(), _emit_step_done() (+34 more)

### Community 300 - "ADR 0024: worker–core 协议"
Cohesion: 0.06
Nodes (71): core 包 contributor 文档, ADR 0016: 执行架构 — 核心库与 run 模型, ADR 0017: 云端执行选 Fargate, ADR 0019: feature tag 的范围与引擎路由, @scope:<name> 会话作用域 tag, assertionVotes 投票次数, 成本信封：engine 只报原生量、core 只合计, 失败/超时的 step 同样带 cost (+63 more)

### Community 301 - "ContainerError"
Cohesion: 0.07
Nodes (22): ContainerEngine, ContainerError, Exception, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 多平台索引的目标平台视图（`inspect --platform linux/amd64`）：返回 (os, architecture)，本机没有该平台的内容…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+14 more)

### Community 305 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 307 - "Fargate/ECS RunTask 执行后端"
Cohesion: 0.50
Nodes (4): AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务

### Community 309 - "reconciler.py"
Cohesion: 0.07
Nodes (40): ReportStore adapters (local / s3), finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。… (+32 more)

### Community 328 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 替换成干净的隧道地址 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_other_jobs_and_original_untouched(), test_map_replaces_docstring_and_datatable_cells_independently() (+1 more)

### Community 331 - "url_matches.py"
Cohesion: 0.50
Nodes (3): deterministic, 示范用确定性 step（Nova Act 侧）：断言当前页面地址匹配给定正则。 这是 `steps/` 目录的模板：复制进你的项目后按需改措辞与判定。与…, url_matches()

### Community 338 - "test_worker_subnets_single_source_across_ssm_and_lambda_env"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 351 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

## Ambiguous Edges - Review These
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
- `终止契约（core 请求 worker 优雅停止）` → `step 顺序 = 书写顺序，keyword 只决定派发`  [AMBIGUOUS]
  docs/adr/0025-plan-module-feature-to-jobs.md · relation: references

## Knowledge Gaps
- **699 isolated node(s):** `背景与问题`, `1. 一个 scope 一个远程访问会话，scenario 之间不复位`, `2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034`, `3. 设备解析、创建与孤儿防护`, `4. 事件契约：`scope_started` 是执行就绪，会话血缘与计量走 `session_opened` / `session_closed`，执行前失败走 `scope_done` 的 scope 级判定` (+694 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **174 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

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
- **What is the exact relationship between `Configuration Env Inheritance Diagram` and `Getting Started Component Ownership Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._