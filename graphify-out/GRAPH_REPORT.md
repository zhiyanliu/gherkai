# Graph Report - yaozhou  (2026-10-29)

## Corpus Check
- 392 files · ~684,184 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 7251 nodes · 16053 edges · 396 communities (240 shown, 156 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 950 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5f6d5716`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _MissingThenStoppedEcs
- test_backend_cloud.py
- test_main.py
- RunStore
- deterministic.py
- test_provider.py
- test_schedule.py
- ScopeStarted
- test_workers.py
- test_plan.py
- workers.py
- ADR 0014: AI 优先断言
- ._run_cdk
- _run_step
- JobResult
- ③ 可直接改（CONFIRMED 客观类 310 条，按文件分组；已随本报告落改）
- test_stack.py
- test_evidence.py
- test_deploy_cmd.py
- test_container.py
- test_cloud_reconcile.py
- materialize.py
- _render_status
- _StubEcs
- _write_feature
- _FakeNovaActClient
- ADR-0008
- S3StepArgumentOffloader
- RunState
- ADR 0045: 文档分层与归位
- serialize.py
- redact_secrets
- ensure_app_object
- _RecUploader
- test_worker_variant.py
- query_capabilities
- LocalReportStore
- test_tunnel_cli.py
- ④ 提纯提案待批（红线复核通过 114 条；approve_reduced 用缩小后改法）
- CONTRIBUTING.md: contributor 指南
- render.py
- gherkai_cli/__main__.py
- cli.py
- test_event_sink.py
- ADR 0024: worker–core 协议
- submission.py
- 运行测试与查看结果
- test_lambda_asset.py
- _FakeEcsClient
- compose.py
- device_selection.py
- Target
- test_user_docs.py
- LocalRunStore
- video.py
- test_interrupt_model.py
- .__init__
- main
- BackendStack
- deploy.py
- test_termination_parity.py
- run_scope.py
- _engine
- atomic_write_json
- manifest.json
- evidence.mts
- test_artifact_upload.py
- test_code_comments.py
- _is_transient_network
- textui.py
- test_job_source.py
- test_tunnel.py
- ADR 0043：驱动 gherkai 的 agent skill
- StepDone
- 06-devicefarm-appium.mts
- gherkai 变更记录 (CHANGELOG)
- test_compose.py
- ArtifactUploader
- test_sqlite_event_log.py
- tunnel-warmup.mts
- _fixture
- _release_cmp
- Midscene 引擎开发笔记（contributor）
- test_user_steps.py
- render_skill_contract.py
- test_termcolor.py
- test_cli_json_contract.py
- 决策
- wire.py
- README Video Specs
- TypeScript Build Config
- config.py
- minimax_narration.py
- Composition Root Architecture
- test_project_config.py
- test_adr_hygiene.py
- build_engines
- Video Material Files
- ssm_path
- deterministic
- user_steps.py
- skill_install.py
- 决策
- Run Store Persistence Ports
- event-sink.mts
- S3ReportStore
- 决策
- 决策
- _Clock
- test_precheck.py
- dependencies
- test_lambda_handlers.py
- read_backend_version
- Diagram Build Script
- ArtifactUploader
- test_engines_matrix.py
- evidence.test.mts
- resolve_worker_cmd
- ValueError
- _Worker
- _presend_act_siblings
- Event Wallclock Analysis
- Release Notes Guards
- FeatureSource
- test_skill.py
- Provider
- run-scope.test.mts
- Dist Metadata Checks
- gemini_image.py
- _doc_rules.py
- _events_table_actions
- Media Conversion Verification
- package.json
- _CdkWritingContext
- FargateEngine
- _pump_log
- _FakeEcs
- DynamoDB Events Transport ADR
- _hits
- 决策
- tunnel-warmup.test.mts
- validate_job_definition
- test_skill_deploy_tokens.py
- test_stores.py
- Stateless Run Core Model
- _Recorder
- argument.mts
- User-Facing Text Guards
- Status
- test_run_and_submit_reject_non_finite_default_job_timeout
- 0050. 确定性 step 多句柄注册与测试分层
- S3ResultStore
- Fargate/ECS RunTask 执行后端
- artifact-upload.test.mts
- deterministic
- _AbsentEngine
- engines-matrix.test.mts
- ADR 0041: 面向 agent 的 CLI 能力
- scan
- ECS Task Timing Capture
- test_definition_schema.py
- Artifact Uploader Component
- subprocess_engine.py
- Graphify Refresh Script
- reconcile.tick（推进器共享入口）
- job-source.mts
- JobState
- Cooperative Stop Design
- render_traffic_policy
- Doc Rules Check
- classify_vpc_state
- openai
- redact.mts
- Engine Port & Job Planning
- Scope Tag Parsing
- 执行与推进模型导览（run/submit × local/cloud）
- Context Glossary Guards
- ADR 0023: Nova Act acting 锁 Python
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- warmupSession
- test_fargate_engine.py
- _print_artifact_lines
- @playwright/test
- test_reconcile.py
- Echo Test Worker
- Cloud Infra Self-Check
- _ClientError
- devDependencies
- 移动真机支持（1.5）：实施进度总纲
- stopTimeout=120 / grace 预算校准
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- Gherkin Parse Seam
- files
- Repository Metadata
- ScheduleOpts
- _add_device_flags
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
- events_pk
- Job
- Adapters Package
- user-steps.test.mts
- gherkai_runtime/__init__.py
- _DeterministicCtx
- Step Matching & Plan Annotation
- ADR-0025
- agentcore-sigv4.test.mts
- EventBridgeTimeoutWatch
- gherkai_runtime/names.py
- .enqueue
- precheck.mts
- runStep
- Index Wait Script
- gherkai Workspace Root
- WebdriverApp
- error-text.mts
- test_registry_dump_via_capabilities_real_subprocess
- Execution Backend
- Feature Files
- Error Type Classification
- Local Per-Run Advance Process
- .drain
- gherkai Core Package
- AWS Deploy Package
- Runtime Package
- NovaAct Worker Package
- format_event
- event-sink.test.mts
- _read_events
- job-source.test.mts
- redact.test.mts
- CollectSink
- test_address_pattern_cross_engine_fixture
- .enabled
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- test_worker_match_steps_mode_real_subprocess
- _delayed_stopped_ecs
- test_bucket_without_logs_dir_fails_loud
- test_noop_uploader_enqueue_and_drain_are_immediate
- ⑦ 事实族横切记录（13 族）
- 项目约定
- _FakeTable
- no-artifacts.test.mts
- ValueError
- NamedTuple
- Job
- RuntimeError
- Job
- Template
- main
- ADR-0019
- ADR-0026
- ADR-0027
- ADR-0052
- 文档健康度复盘 · 第八轮 · 待批报告
- index.mts
- DEFAULT_MODEL
- test_app_upload.py
- MODEL
- MODEL_FAMILY_PATTERNS
- ADR-0033
- ADR-0037
- ADR-0044
- CONTENT_TYPES
- ADR-0016
- ADR 0037: 分发与打包
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0032
- ADR-0033
- ADR-0042
- UPLOAD_TIMEOUT_MS
- DeterministicAssertion
- DeterministicConflict
- DeterministicHandler
- DeterministicHandlers
- RunPersistence
- DeterministicMeta
- test_argument.py
- Device
- DEVICES
- ADR 0016: 执行架构 — 核心库与 run 模型
- ContainerError
- Entry
- ENTRY_FIELDS
- WebdriverCtx
- _FakeSink
- RFC-3986
- EntryHandles
- HANDLER_KINDS
- reconciler.py
- @aws-sdk/client-dynamodb
- Keyword
- KEYWORDS
- MatchItem
- MatchProbe
- test_tunnel_warmup.py
- ADR-0020
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0048
- ADR-0049
- ADR-0050
- NormalizedWebdriverEntry
- PLAYWRIGHT_TARGET
- precheck.test.mts
- REGISTRY
- map_origin_in_jobs
- RegistryEntry
- url_matches.py
- Requirement
- REQUIREMENTS
- SelectedHandler
- _joined_refs
- ADDRESS_PATTERN
- ADR-0020
- ADR-0022
- ADR-0036
- settings.py
- ADR-0037
- _FakeS3
- ADR-0048
- WEB_SCHEMES
- StepTarget
- StepTargetKey
- TARGET_DEVICE_ORDER
- _spawn_and_wait_ready
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
- test_fail_fast_stops_running_workers_from_main_thread_without_heartbeat
- QUEUE_DRAIN_EXIT_MS
- Scenario
- ShutdownDeps
- Step
- deterministic_steps.py
- STOP_SESSION_BUDGET_MS
- WORKER_TARGETS
- BaseException
- list
- test_provider_module_does_not_import_aws_cdk
- _out
- @midscene/web

## God Nodes (most connected - your core abstractions)
1. `main()` - 274 edges
2. `Job` - 178 edges
3. `RunMeta` - 142 edges
4. `RunState` - 132 edges
5. `Status` - 114 edges
6. `JobState` - 106 edges
7. `JobResult` - 105 edges
8. `Provider` - 100 edges
9. `③ 可直接改（CONFIRMED 客观类 310 条，按文件分组；已随本报告落改）` - 100 edges
10. `Scenario` - 98 edges

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

## Communities (396 total, 156 thin omitted)

### Community 0 - "_MissingThenStoppedEcs"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 1 - "test_backend_cloud.py"
Cohesion: 0.04
Nodes (109): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), _patch_skew(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, status 不解析 variant（ADR 0038）：它只读运行态、不起 task，definition 里的 revision 提交时已定死。, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：… (+101 more)

### Community 2 - "test_main.py"
Cohesion: 0.03
Nodes (119): _cloud_backend_ok(), _det_feature(), _doctor_cloud_json(), _evidence_fixture(), _explain(), _fake_locator(), _fake_worker_cmd(), _miss() (+111 more)

### Community 3 - "RunStore"
Cohesion: 0.07
Nodes (18): Engine, EngineResolver, JobSink, Event, Job, Protocol, 核心注入接口（ADR 0016，业界称 ports & adapters）：核心的主要注入口在此（另两个见末段），具体 adapter 由组合根注入。 四个…, 控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。… (+10 more)

### Community 4 - "deterministic.py"
Cohesion: 0.10
Nodes (23): _closed_set(), DeterministicConflict, DeterministicKeywordMismatch, _Entry, Handles, Hit, _hits(), _normalize_handlers() (+15 more)

### Community 5 - "test_provider.py"
Cohesion: 0.06
Nodes (62): _argv(), _parse(), `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，…, 子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。, `--prefix` 在子动词**前**给也必须留住——子 parser 在新 namespace 里解析后整体覆盖回父层，…, 留口子：以退出码 2 结束并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。, CLI 前端没交版本 → 本包自报 dist 版本（`==` 同版本 pin 成同一个，不引入第二个真源）。 (+54 more)

### Community 6 - "test_schedule.py"
Cohesion: 0.13
Nodes (68): 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), FakeEngine, FakeResolver, EngineResolver：所有引擎都返回同一个 FakeEngine（测试不区分引擎）。, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, test_fail_fast_queued_job_is_skipped(), _job() (+60 more)

### Community 7 - "ScopeStarted"
Cohesion: 0.07
Nodes (77): ScopeStarted, EventRecord, plan_next(), project(), project_full(), events 表里一条记录的投影输入（ADR 0034）：reconciler 从表全量重放时，每条 record 携带的信息。 worker…, 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与… (+69 more)

### Community 8 - "test_workers.py"
Cohesion: 0.07
Nodes (77): aws(), _cleanup(), FakeContainer, _mapping(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 一次干净的推送：tag/push 到 ECR ref → 从模板注册 revision（镜像按 digest、血缘 tags 齐）→ 写 SSM 映射。 (+69 more)

### Community 9 - "test_plan.py"
Cohesion: 0.07
Nodes (53): _cfg(), _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 低于下限的改法要按删掉 tag 后真正接替的来源给：--default-job-timeout 也低于下限时不能只说「删 tag 走缺省」（删了仍被它拒）。, PlanConfig 自带的设备缺省与下限按内建获取预算 600 推出（加 900 / 加 180，ADR 0051 决策 2）；桌面缺省 300。, 「任一成员标了即整个 scope 生效」不只看首个成员：带 tag 的成员排在后面也生效。, select 不变量扩到目标（ADR 0041 决策一经 0025）：筛掉带 tag 的成员后，Job.target 与按目标得出的 timeout_s… (+45 more)

### Community 10 - "workers.py"
Cohesion: 0.05
Nodes (84): cleanup_pass(), CleanupOutcome, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable(), _hours() (+76 more)

### Community 11 - "ADR 0014: AI 优先断言"
Cohesion: 0.05
Nodes (61): CLAUDE.md（项目约定）, CONTEXT.md（领域概念与术语）, ADR 0001: 范围限于英文 UI, 概念：非英文应用用 @engine:midscene 路由, 概念：Nova Act 中文词语级文本匹配短板, ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码, 概念：Midscene 仅走 chat-completions 接口 (+53 more)

### Community 12 - "._run_cdk"
Cohesion: 0.07
Nodes (21): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), Path, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。… (+13 more)

### Community 13 - "_run_step"
Cohesion: 0.06
Nodes (64): _classify_act_error(), 派发执行一个 step，发出 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+56 more)

### Community 14 - "JobResult"
Cohesion: 0.06
Nodes (64): device_header_lines(), _device_keys_for_explain(), explain_to_dict(), RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, explain 的人与 agent 可读文本（`explain_to_dict` 的文档渲染为树形摘要，节点文字依 ADR 0042…, scope 表头的设备两行（ADR 0051 决策 8）：代表会话的设备描述、会话 ARN 对应的 Device Farm 控制台链接；桌面 job…, render_explain_text() (+56 more)

### Community 15 - "③ 可直接改（CONFIRMED 客观类 310 条，按文件分组；已随本报告落改）"
Cohesion: 0.02
Nodes (100): ③ 可直接改（CONFIRMED 客观类 310 条，按文件分组；已随本报告落改）, `CHANGELOG.md`（2 条）, `CLAUDE.md`（1 条）, `cli/DEVELOPMENT.md`（9 条）, `cli/gherkai_cli/skills/gherkai/references/cloud-backend.md`（4 条）, `cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md`（2 条）, `cli/gherkai_cli/skills/gherkai/SKILL.md`（3 条）, `cli/tests/test_adr_hygiene.py`（1 条） (+92 more)

### Community 16 - "test_stack.py"
Cohesion: 0.04
Nodes (31): BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。… (+23 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.08
Nodes (52): ArtifactUploader, `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _get_uploader(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks() (+44 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 前端自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 19 - "test_container.py"
Cohesion: 0.06
Nodes (45): digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。 (+37 more)

### Community 20 - "test_cloud_reconcile.py"
Cohesion: 0.08
Nodes (40): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, _FakeStartEngine, _job(), _meta() (+32 more)

### Community 21 - "materialize.py"
Cohesion: 0.08
Nodes (53): gherkai agent skill 包, evals.json（评测集与 fixture 索引）, 评分子代理提示词模板, assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture() (+45 more)

### Community 22 - "_render_status"
Cohesion: 0.17
Nodes (20): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。 (+12 more)

### Community 23 - "_StubEcs"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 24 - "_write_feature"
Cohesion: 0.04
Nodes (72): 缺戳例外的接线：谓词为真的 run / submit 遇无版本戳后端以退出码 2 结束、资源检查一次不做；谓词为假（纯桌面）只警告放行。 谓词本身在…, test_missing_stamp_blocks_runs_that_require_it_before_resource_preflight(), _capturing_schedule(), _fake_schedule_factory(), Path, miss 只连坐**用到它**的 run：novaact-only 的 run 在 midscene 未装（dev 常态）下照常运行并以退出码 0 结束。…, submit local 同 run（per-run 进程在本机 spawn worker）：提交前以退出码 2 结束、不…, 记录 build_engines 收到的 kwargs（仍调真实实现，保 cmd/env 接线真实）。 (+64 more)

### Community 25 - "_FakeNovaActClient"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 27 - "S3StepArgumentOffloader"
Cohesion: 0.04
Nodes (50): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, 指针必须是文本（s3:// URI）；别的类型是同版本下的定义违约，不让它变成 urlparse 的裸 AttributeError。, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与… (+42 more)

### Community 28 - "RunState"
Cohesion: 0.07
Nodes (60): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…, RunState, _initial(), _meta() (+52 more)

### Community 29 - "ADR 0045: 文档分层与归位"
Cohesion: 0.20
Nodes (21): _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏）, test_user_docs.py（用户文档与图源护栏）, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0045: 文档分层与归位, CONTEXT.md 严格词表与术语变更顺序（决策八）, archify 图流程（JSON 图源 + 导出 SVG 入库） (+13 more)

### Community 30 - "serialize.py"
Cohesion: 0.08
Nodes (41): S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, _argument_from_dict(), _argument_to_dict(), _definition_error(), _device_keys(), _device_request_from_dict(), job_from_dict(), job_result_from_dict() (+33 more)

### Community 31 - "redact_secrets"
Cohesion: 0.14
Nodes (18): Any, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则、三份同文实现。 三份同文实现（本文件、Nova worker…, 三条规则依次作用于一段文本；None 原样返回。 `https://u:p@host/x` →…, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_secrets(), parametrize, 凭据脱敏三条规则的单测（ADR 0035 决策 5；0051 决策 11）。 用例表只有一份：`engines/fixtures/redaction-… (+10 more)

### Community 32 - "ensure_app_object"
Cohesion: 0.17
Nodes (18): app_object_key(), AppLocation, AppUploadError, ensure_app_object(), _error_code(), BaseException, datetime, Exception (+10 more)

### Community 33 - "_RecUploader"
Cohesion: 0.05
Nodes (24): _FakeBrowserClient, _FakeCm, _FakeNovaAct, _install_browser_client(), main_fakes(), _RaisingSink, 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。 (+16 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.08
Nodes (42): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, worker_image_key(), aws(), _fake_aws_creds(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。 (+34 more)

### Community 35 - "query_capabilities"
Cohesion: 0.06
Nodes (48): engine_min_grace(), _is_finite_number(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, 有限的 int / float（bool 单独挡；超出 float 范围的大整数按「不是有限数」处理，不让 math.isfinite 的…, targets 数组的形态校验（ADR 0049 决策 1）：顶层 targets 必有（缺键由调用方按版本不一致拒绝），step 级只在键存在时调用；显式…, _validate_targets() (+40 more)

### Community 36 - "LocalReportStore"
Cohesion: 0.07
Nodes (63): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), LocalReportStore, Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出… (+55 more)

### Community 37 - "test_tunnel_cli.py"
Cohesion: 0.08
Nodes (47): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, 不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。, 隧道起不来（如 authtoken 缺失）→ 给退出码 2「没开始执行就被拒」，不产生引擎费用。, local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。 (+39 more)

### Community 38 - "④ 提纯提案待批（红线复核通过 114 条；approve_reduced 用缩小后改法）"
Cohesion: 0.06
Nodes (36): 0003（1 条）, 0008（1 条）, 0012（1 条）, 0015（1 条）, 0016（5 条）, 0019（1 条）, 0020（1 条）, 0022（3 条） (+28 more)

### Community 39 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.07
Nodes (42): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, cli 包 contributor 文档, skill 参考：CLI --json 字段契约, skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法 (+34 more)

### Community 40 - "render.py"
Cohesion: 0.06
Nodes (57): plan 标注用的一句（产品语言）：原样展示 ARN 或筛选条件与来源；未指定时说明 run / submit 会拒绝。, plan --json 的 `devices.<平台>`：指定一台时 `{arn, source}`，按版本挑选时 `{os_version,…, selection_label(), selection_to_dict(), _cmd_plan(), 用例预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…, _add_act(), _add_device_evidence() (+49 more)

### Community 41 - "gherkai_cli/__main__.py"
Cohesion: 0.04
Nodes (95): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_doctor(), _cmd_explain(), _cmd_list_deterministic(), _cmd_reconcile() (+87 more)

### Community 42 - "cli.py"
Cohesion: 0.05
Nodes (43): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, cdk_command(), check_cdk(), check_node(), _error_code(), _make_cfn_client(), _make_hint_clients() (+35 more)

### Community 43 - "test_event_sink.py"
Cohesion: 0.06
Nodes (21): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与…, 三条规则依次作用于一段文本；None 原样返回。, redact_secrets() (+13 more)

### Community 44 - "ADR 0024: worker–core 协议"
Cohesion: 0.05
Nodes (61): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, URL 形态自动分流（导航不写死动词）, assertionVotes 投票次数, 成本信封：engine 只报原生量、core 只合计, 失败/超时的 step 同样带 cost, 深模块、小接口的协议分层原则, errorType 规范化失败分类 (+53 more)

### Community 45 - "submission.py"
Cohesion: 0.08
Nodes (35): progress(), 命令行的进度与诊断输出（ADR 0047）：一个函数，供 `__main__` 与各编排模块共用。, 进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `gherkai run ……, app_entries(), cloud_app_locations(), cloud_device_requests(), complete_cloud_definition(), complete_local_definition() (+27 more)

### Community 46 - "运行测试与查看结果"
Cohesion: 0.09
Nodes (43): gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce）, kicker Lambda（冷启动器）, reconciler Lambda（主推进器） (+35 more)

### Community 47 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (23): 把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容是本包 `lambdas/` 的 handler…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path, Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。…, 没有命令给的工作目录（直接运行 cdk synth）→ 自建 mkdtemp，仍不写仓库。 (+15 more)

### Community 48 - "_FakeEcsClient"
Cohesion: 0.13
Nodes (18): build_cloud_stores(), _normalize_prefix(), preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, 云端三层 store（RunStore→DDB、Result/ReportStore→S3）+ cloud artifacts…, _FakeDdbClient, _FakeEcsClient (+10 more)

### Community 49 - "compose.py"
Cohesion: 0.04
Nodes (65): available_targets(), build_fargate_engines(), cloud_artifact_locations(), _default_targets(), is_botocore_error(), _make_ddb_table(), _make_ecr_client(), _make_ecs_client() (+57 more)

### Community 50 - "device_selection.py"
Cohesion: 0.11
Nodes (27): account_of(), acquire_timeout_for(), _arn_kind(), billing_method_for(), build_device_request(), check_device_arn(), check_project_arn(), DeviceSelection (+19 more)

### Community 51 - "Target"
Cohesion: 0.09
Nodes (32): AppRef, DeviceFarmRequest, 向 AWS Device Farm 要哪台设备（ADR 0048 决策 3）：名字明说服务商、不起中立名；`device_arn` 与…, 应用目标的应用条目（ADR 0048 决策 3）。两个形态：plan 形态只有别名与包名或 bundle id；run / submit 在组合根上传安装包后…, 一个 scope 运行在什么上面（ADR 0048 决策 1）：设备与界面类型；ui_kind 为 app 时带应用条目。缺省即桌面网页。, 机读与 plan 文本共用的紧凑写法（ADR 0048 决策 5 的形态）：`desktop/web`、`android/app:shop`。, Target, _device_request_to_dict() (+24 more)

### Community 52 - "test_user_docs.py"
Cohesion: 0.07
Nodes (44): changelog_unreleased(), 用户文档里交给口吻表与形态①③启发式扫的部分：CHANGELOG 截到第一个已发行节之前，定稿口播稿整份豁免（空串）， 其余页面全文。截断只保留前缀，故调用方…, CHANGELOG 交给退役词表与口头语表扫的部分，即第一个已发行版本节之前的内容。…, wording_scope(), _default_model_claims(), _default_model_ids(), parametrize, Path (+36 more)

### Community 53 - "LocalRunStore"
Cohesion: 0.03
Nodes (102): Connection, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。 (+94 more)

### Community 54 - "video.py"
Cohesion: 0.32
Nodes (17): cues(), digest(), link_chapter_title_track(), packets(), probe(), protected_state(), Path, Confirm the first slide at frame zero, hard cuts, and the closing fade. (+9 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (34): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+26 more)

### Community 56 - ".__init__"
Cohesion: 0.50
Nodes (3): EngineResolver, Lock, Sink

### Community 57 - "main"
Cohesion: 0.05
Nodes (61): main(), _plan_names(), --version 打印「gherkai <发行版本>」并以退出码 0 结束——版本真源是包元数据（git tag → uv-dynamic-…, 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。 (+53 more)

### Community 58 - "BackendStack"
Cohesion: 0.08
Nodes (24): Cluster, Construct, BackendStack, BackendStack._build_lambda_asset, BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个… (+16 more)

### Community 59 - "deploy.py"
Cohesion: 0.11
Nodes (19): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+11 more)

### Community 60 - "test_termination_parity.py"
Cohesion: 0.12
Nodes (23): 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, 平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。 **不是 worker 的 wire 事件**（不在…, TaskExited, _closed(), _comparable(), _job() (+15 more)

### Community 61 - "run_scope.py"
Cohesion: 0.04
Nodes (49): ActRecord, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, _leave_warmup_page(), _one_line(), Exception, 隧道会话预热（ADR 0051 决策 13）：worker 在第一个 scenario 之前对预热地址导航一次换到会话 cookie，并按页面的可见结果归因。…, 预热期间收到停止信号（ADR 0024 flag-only 协作停）：调用方按停止路径收尾，不算失败、不发 scope_done。, 对 `page` 导航预热地址、等页面标题落成四个标记之一；返回 None 表示就绪，否则返回归因与产品语言的消息。 `page` 是 Playwright… (+41 more)

### Community 62 - "_engine"
Cohesion: 0.11
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 63 - "atomic_write_json"
Cohesion: 0.13
Nodes (21): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ReportStore adapters (local / s3), ResultStore adapters (local / s3) (+13 more)

### Community 64 - "manifest.json"
Cohesion: 0.06
Nodes (35): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+27 more)

### Community 65 - "evidence.mts"
Cohesion: 0.09
Nodes (30): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+22 more)

### Community 66 - "test_artifact_upload.py"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 67 - "test_code_comments.py"
Cohesion: 0.19
Nodes (12): code_comment_files(), parametrize, Path, repo 内 code 注释与 docstring 的措辞与悬空指针护栏（ADR 0045 决策六：注释与 docstring 是人读层；ADR 0046…, 注释与 docstring：无口头语 / 自造复合词、无退役旧名、不把 = 当谓语、不写「退 N」、不指 journey 文件与 WP 编号。, 形态①③的启发式扫剥掉行内代码后的注释：反引号里的 `job = 范围` 是代码、不报，正文里的等号照报； 其余规则仍扫注释原文，反引号里的 journey…, docstring 里围栏代码块中的 `job = 范围` 是代码示例、不报；围栏闭合之后的正文照报。, _rel() (+4 more)

### Community 68 - "_is_transient_network"
Cohesion: 0.09
Nodes (41): BaseException, 账号比对是辅助提示（ADR 0053 决策 3）：凭证 / 网络类失败（botocore）只提示一句、继续；别的异常是程序错误，原样上抛、不吞。, test_account_check_only_swallows_credential_and_network_failures(), _error_text(), _is_transient_client_error(), _is_transient_network(), _one_line(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。 (+33 more)

### Community 69 - "textui.py"
Cohesion: 0.11
Nodes (29): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。, 深度优先找第一个 label 含 needle 的节点（测试与诊断用）。, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，… (+21 more)

### Community 70 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 71 - "test_tunnel.py"
Cohesion: 0.09
Nodes (29): _gen_secret(), make_tunnel(), NgrokTunnel, Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。 (+21 more)

### Community 72 - "ADR 0043：驱动 gherkai 的 agent skill"
Cohesion: 0.20
Nodes (15): ADR 0001：范围限定英文 UI, ADR 0041：面向 agent 的 CLI 可操作面, ADR 0043：驱动 gherkai 的 agent skill, 评测去污染硬规则（CLI 来自仓库外 wheel、skill 副本随机目录、舞台路径随机）, 物化式 fixture 与可搬迁契约, 两臂评测法（with-skill 对 baseline）, ADR 0047：CLI 人读输出用 rich 渲染表格与树, gherkai_runtime.textui（表格 / 树 / 样式单点） (+7 more)

### Community 73 - "StepDone"
Cohesion: 0.15
Nodes (31): test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, ScenarioDone, ScenarioStarted, StepDone (+23 more)

### Community 74 - "06-devicefarm-appium.mts"
Cohesion: 0.06
Nodes (80): ADR-0010, BASE_URL, main(), makePng(), REGION, ADR-0033, BASE_URL, main() (+72 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.09
Nodes (30): gherkai 变更记录 (CHANGELOG), gherkai destroy, --expose-local 隧道模式, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, gherkai deploy push-worker / list-workers (+22 more)

### Community 76 - "test_compose.py"
Cohesion: 0.04
Nodes (73): check_version_skew(), prune_empty_dirs(), Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`，再缺取配置文件的 profile（ADR 0053 决策…, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。… (+65 more)

### Community 77 - "ArtifactUploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 78 - "test_sqlite_event_log.py"
Cohesion: 0.15
Nodes (18): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, 端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。 (+10 more)

### Community 79 - "tunnel-warmup.mts"
Cohesion: 0.08
Nodes (22): ADR-0028, ADR-0039, CHECK_PATH, COOKIE_NAME, EXTRA_HTTP_HEADERS_ENV, INCOMPLETE_DEFINITION_MESSAGE, ADR-0051, SESSION_WARMUP_KEY (+14 more)

### Community 80 - "_fixture"
Cohesion: 0.04
Nodes (65): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), aws(), _fake_aws_creds(), fargate(), moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表… (+57 more)

### Community 81 - "_release_cmp"
Cohesion: 0.15
Nodes (13): is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp(), _release_key(), _variant_miss_hint() (+5 more)

### Community 82 - "Midscene 引擎开发笔记（contributor）"
Cohesion: 0.10
Nodes (18): worker 镜像 variant 与默认指针, 确定性 step 加载失败即拒绝运行, Midscene 引擎开发笔记（contributor）, 容器镜像必须 --platform linux/amd64, fromSource, hookSpec, ADR-0024, ADR-0028 (+10 more)

### Community 83 - "test_user_steps.py"
Cohesion: 0.08
Nodes (42): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` 是 env `GHERKAI_STEPS_DIR`…, _clean_env(), _isolate(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, `_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。, `_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。 (+34 more)

### Community 84 - "render_skill_contract.py"
Cohesion: 0.23
Nodes (12): docs/internals/cli-json-contract.md（机读字段级参考页）, _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。 (+4 more)

### Community 85 - "test_termcolor.py"
Cohesion: 0.25
Nodes (10): 执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。, _clean_env(), _Pipe, 终端颜色开关的统一策略（gherkai_core.termcolor，ADR 0047）：环境变量优先于目标流是否终端，非空语义同 no-color.org。, test_broken_stream_counts_as_not_tty(), test_force_color_enables_on_pipe(), test_no_color_non_empty_wins_over_tty(), test_stream_decides_when_no_env() (+2 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.15
Nodes (21): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…, _assert_documented(), _documented_keys(), _leaf_keys(), _mk() (+13 more)

### Community 87 - "决策"
Cohesion: 0.10
Nodes (20): 0051. 远程访问会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034 (+12 more)

### Community 88 - "wire.py"
Cohesion: 0.04
Nodes (74): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, NamedTuple, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR… (+66 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 91 - "config.py"
Cohesion: 0.14
Nodes (27): AppPlatformConfig, _apps_section(), _billing_method(), ConfigError, DevicePlatformConfig, _devices_section(), DevicesConfig, load_project_config() (+19 more)

### Community 92 - "minimax_narration.py"
Cohesion: 0.26
Nodes (10): APIError, download_subtitles(), main(), NoRedirect, page_numbers(), post(), Exception, Path (+2 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_project_config.py"
Cohesion: 0.07
Nodes (64): _build_parser(), 建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…, _tunnel_providers(), `--steps-dir` 的 help 在 run/submit 两处是同一个常量（曾字节级抄两份）：措辞改一处即两处生效。…, test_run_and_submit_share_one_steps_dir_help_text(), _android_caps(), _android_env(), _app_project() (+56 more)

### Community 95 - "test_adr_hygiene.py"
Cohesion: 0.13
Nodes (26): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, 全仓 markdown（含 journey 与工具说明，原文含行内代码）不写本机坐标：个人目录下的绝对路径、本地 clone 目录名只在产出机器上… (+18 more)

### Community 96 - "build_engines"
Cohesion: 0.06
Nodes (45): _ask_worker(), build_engines(), load_feature(), local_artifact_locations(), make_resolver(), match_deterministic(), Path, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导… (+37 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "ssm_path"
Cohesion: 0.13
Nodes (16): subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), ssm_worker_template_path() (+8 more)

### Community 99 - "deterministic"
Cohesion: 0.09
Nodes (41): clear(), deterministic(), list_registry(), match(), match_batch(), 注册一条确定性 step。两种写法： 装饰器（等价于只有 playwright 句柄）： @deterministic(r'页面地址匹配…, 注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。, 在注册表里找命中 text 的唯一条目。 返回 Hit 或 None（未命中走 AI）。命中多条 → DeterministicConflict； 命中一条但… (+33 more)

### Community 100 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

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

### Community 105 - "S3ReportStore"
Cohesion: 0.06
Nodes (25): ResourceUri, ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把 manifest.json + index.html 写到 `s3://bucket/<prefix><run_id>/`，返回 index.html 的…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, s3_report_store(), test_prefix_lands_under_prefix() (+17 more)

### Community 106 - "决策"
Cohesion: 0.13
Nodes (15): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 不升 schema 版本，在 schema 1 上增键, 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端 worker 在建会话前按自己的 `targets` 自检 (+7 more)

### Community 107 - "决策"
Cohesion: 0.13
Nodes (15): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 7. Midscene 复用边界 (+7 more)

### Community 108 - "_Clock"
Cohesion: 0.13
Nodes (13): Event, 事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收…, 排空上界从停止请求时刻起算：真 stop() 阻塞消耗的宽限不再额外加进上界。假 stop() 把时钟推进很多，正确实现随后第一次心跳检查就到点； 若从…, 没有 deadline 的 job 被 fail-fast 中止后卡死不退出：排空上界同样起作用（靠心跳醒来），不挂死，判 ABORTED。, 事件流中的普通异常（解析失败 / sink 抛错）后仍向 worker 发停止请求（别留孤儿进程）；起 worker 失败以退出码未知进终结函数：…, fail-fast 批量中止：先对全部运行中的 worker 落定停止原因、再发停止请求。真 stop() 会阻塞到宽限到点，边落定边停会让前一个…, test_drain_bound_applies_without_deadline_under_fail_fast(), test_drain_bound_counts_from_stop_request_not_after_blocking_stop() (+5 more)

### Community 109 - "test_precheck.py"
Cohesion: 0.11
Nodes (27): _num(), precheck_job(), precheck_schema(), precheck_target(), 建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的…, (device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。, 名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。, 秒数的写法：整数值不带小数点（1500 而不是 1500.0），其余按原值；与 Midscene 侧的插值结果一致。 (+19 more)

### Community 110 - "dependencies"
Cohesion: 0.11
Nodes (19): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js (+11 more)

### Community 111 - "test_lambda_handlers.py"
Cohesion: 0.02
Nodes (112): _FakeEcs, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认… (+104 more)

### Community 112 - "read_backend_version"
Cohesion: 0.15
Nodes (16): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口前端只翻退出码）。 (+8 more)

### Community 113 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 115 - "test_engines_matrix.py"
Cohesion: 0.11
Nodes (23): _available_step_targets(), _probe_deterministic_dispatch(), plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…, plan 标注用：该引擎每条确定性 step 实际可用的目标（声明与 worker 支持目标的交集，ADR 0049 决策 3），按模式索引。…, 把名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」而不是「在Android 网页上」）；全中文的名称原样。, (device, ui_kind) → 「桌面网页」「Android 应用」这类名称；未知取值原样拼出（自述形态由组合根校验，这里只呈现）。, 前提清单 → 「需要网页上下文」；未知取值按「需要 <取值>」原样显示（ADR 0049 决策 1：CLI 不另立取值集合）。, 一组目标条目 → 「桌面网页、Android 网页（需要网页上下文）」；带 max_session_s 的条目按分钟附会话上限（doctor 用）；… (+15 more)

### Community 116 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 117 - "resolve_worker_cmd"
Cohesion: 0.07
Nodes (32): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, _find_worker_spec(), 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, resolve_worker_cmd(), 四级全 miss → WorkerNotFoundError 带引擎名 + 该引擎的安装指引 + env 覆写指引（退出码交调用点）。, 第一级 env 覆写最高优先（shlex 拆分）+ 可选配套 _CWD：contributor 指向 repo 内源码/自建 worker 走这里。 (+24 more)

### Community 118 - "ValueError"
Cohesion: 0.36
Nodes (8): test_value_error_not_transient(), main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems(), ValueError

### Community 119 - "_Worker"
Cohesion: 0.23
Nodes (8): _heartbeat_wrap(), Event, 单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。, 对本 job 落定停止原因并（首次）向 worker 发停止请求；已落定、已返回或内容已完整的直接返回现值。事件循环、异常分支与…, 内容已完整而 deadline 已过：只催 worker 收尾（发停止请求，排空上界从此刻起算），不落定停止原因——判定已成，…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…, _Worker

### Community 120 - "_presend_act_siblings"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…, act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _traj_refs(), _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 121 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Release Notes Guards"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 123 - "FeatureSource"
Cohesion: 0.09
Nodes (45): FeatureContractError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, 用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。…, _index_ast_lines(), _map_argument(), parse_feature(), ParsedScenario, StepArgument (+37 more)

### Community 124 - "test_skill.py"
Cohesion: 0.04
Nodes (66): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 一个 `gherkai …` 代码跨的拆解结果。 `words` 是 `gherkai` 之后、第一个 flag…, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。 (+58 more)

### Community 125 - "Provider"
Cohesion: 0.08
Nodes (26): Provider, ArgumentParser, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。 (+18 more)

### Community 126 - "run-scope.test.mts"
Cohesion: 0.07
Nodes (17): _events, fakePage, gotoCalls, ADR-0014, ADR-0020, ADR-0024, ADR-0028, ADR-0029 (+9 more)

### Community 127 - "Dist Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 128 - "gemini_image.py"
Cohesion: 0.33
Nodes (4): HTTPRedirectHandler, NoRedirect, 演示制作规范, 演示制作与媒体工具说明

### Community 129 - "_doc_rules.py"
Cohesion: 0.06
Nodes (51): ai_side_docs(), all_markdown(), classify(), comment_blocks(), comment_prose_lines(), comment_units(), _consecutive_runs(), diagram_sources() (+43 more)

### Community 130 - "_events_table_actions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉… (+4 more)

### Community 131 - "Media Conversion Verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 132 - "package.json"
Cohesion: 0.12
Nodes (16): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+8 more)

### Community 133 - "_CdkWritingContext"
Cohesion: 0.16
Nodes (15): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, Path, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按… (+7 more)

### Community 134 - "FargateEngine"
Cohesion: 0.16
Nodes (13): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+5 more)

### Community 135 - "_pump_log"
Cohesion: 0.25
Nodes (8): _pump_log(), scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, _scope_color(), worker 日志逐行转发时盖住隧道凭据（ADR 0035 决策 5）：写 log_sink 与写本进程 stderr 两条分支都要盖。 直接喂…, test_pump_log_colors_prefix_only_when_policy_says_so(), test_pump_log_masks_tunnel_credentials_in_sink_and_stderr(), test_scope_colors_assigned_in_order_without_collision_and_stable()

### Community 136 - "_FakeEcs"
Cohesion: 0.15
Nodes (7): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

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
Nodes (3): ADR-0035, FIXTURE, ADR-0051

### Community 141 - "validate_job_definition"
Cohesion: 0.22
Nodes (13): _is_positive_number(), _is_text(), Job, definition 里的一个 job 必须是完整形态，否则抛 DefinitionContractError（推进器与 worker…, validate_job_definition(), _ios_app_job(), parametrize, 写前校验（ADR 0048 决策 3）：应用条目五项逐项缺失、空值、错类型都拒绝——直接调校验函数，不只经读端。 (+5 more)

### Community 142 - "test_skill_deploy_tokens.py"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。 (+3 more)

### Community 143 - "test_stores.py"
Cohesion: 0.10
Nodes (45): 读回 definition（RunMeta）；不存在返回 None。, 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), from_dict(), RunResult → 朴素 dict（机器可读：CI / WebUI / manifest 消费）。 normalize（ADR 0016…, 朴素 dict → RunResult。与 to_dict 往返一致（round-trip 单测护栏）。 def 唯一真值在…, RunMeta → dict（run_meta.json / DDB META 的 meta_json）。键集固定、不适用写 null（ADR 0037 决策…, dict → RunMeta。第一步核结构版本（不等于本读端支持的即抛… (+37 more)

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "_Recorder"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+3 more)

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "User-Facing Text Guards"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 148 - "Status"
Cohesion: 0.04
Nodes (102): test_format_event_renders_session_events_without_endpoints(), LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, 判定状态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, 远程访问会话打开（ADR 0051 决策 4 / 0024「会话事件」）：Create 返回 ARN…, 远程访问会话处置结束（ADR 0051 决策 4、7）：每个会话恰一条；release 是否确认停止；observed_s 是 worker 观察到的占用秒数… (+94 more)

### Community 149 - "test_run_and_submit_reject_non_finite_default_job_timeout"
Cohesion: 0.40
Nodes (5): parametrize, 三处 --default-job-timeout 各自声明：run 与 submit 对 nan / inf 同样以退出码 2 结束（argparse 层）。, 设备选择接在 run / submit 的共享前置里（ADR 0053 决策 4）：没有任何来源指定设备的设备 job 在这里以退出码 2…, test_cloud_run_and_submit_reject_device_job_in_shared_prestep_before_touching_cloud(), test_run_and_submit_reject_non_finite_default_job_timeout()

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.18
Nodes (11): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 2. handler 上下文：七个字段与一条不变量, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据 (+3 more)

### Community 151 - "S3ResultStore"
Cohesion: 0.23
Nodes (6): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore

### Community 152 - "Fargate/ECS RunTask 执行后端"
Cohesion: 0.50
Nodes (4): AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务

### Community 153 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 156 - "engines-matrix.test.mts"
Cohesion: 0.20
Nodes (7): DEVICE_LABEL, HANDLE_BY_DEVICE, MATRIX, ADR-0049, ADR-0050, Row, UI_KIND_LABEL

### Community 157 - "ADR 0041: 面向 agent 的 CLI 能力"
Cohesion: 0.09
Nodes (25): RunMeta.extra_http_headers（额外请求头注入）, 隧道凭据脱敏（剥 URL userinfo）, worker --capabilities 自述入口, CLI list-deterministic --engine, 注册面元数据（description / example 必填）, CI 发布链与占名（tag 触发全链）, 版本 skew 检查（三态）, steps/ 定制面（随 definition 走 + env 注入） (+17 more)

### Community 159 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 160 - "test_definition_schema.py"
Cohesion: 0.15
Nodes (21): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, parametrize, Path, definition 结构版本闸门（ADR 0037 决策 7）在 CLI 的接线：status / explain /…, 别的版本写出的 run 目录连运行态的形状都不保证：先核结构版本，再读运行态——否则「请升级」会变成一个解析异常。, 本机接力宿主读到同版本下形态违约的提交记录（这里真的从 run_meta.json 删掉一个 job 的 target 键）：CLI 读端有退出码可交，…, 读头阶段的形态违约（结构版本字段不是整数）：三个本机读端都以退出码 2 结束并说明，不是裸异常；运行态不被改动、不写 run 级消息…, 云端两个读端读 META 头时的形态违约（结构版本字段不是整数）：以退出码 2 结束并说明，不是裸异常；之后不再读运行态。 (+13 more)

### Community 161 - "Artifact Uploader Component"
Cohesion: 0.09
Nodes (29): 引擎特有量不进 model（act_count）, JobResult 持有 Job、engine 经 property delegate, href 相对化（local 相对 / cloud 恒等 ref）, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 式产物拷贝, 不透明搬运铁律（model/wire/schedule 永不解引用 ref）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写） (+21 more)

### Community 162 - "subprocess_engine.py"
Cohesion: 0.21
Nodes (10): 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, _reset_scope_colors(), color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color() (+2 more)

### Community 163 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 164 - "reconcile.tick（推进器共享入口）"
Cohesion: 0.17
Nodes (13): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState）, status --wait 接力推进 (+5 more)

### Community 165 - "job-source.mts"
Cohesion: 0.12
Nodes (11): Job, JOB_KEYS, JobApp, JobDeviceRequest, JobSource, JobTargetShape, Missing, ADR-0016 (+3 more)

### Community 166 - "JobState"
Cohesion: 0.07
Nodes (44): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_explain_cloud_reads_evidence_from_s3(), _job_state_to_item(), 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid… (+36 more)

### Community 167 - "Cooperative Stop Design"
Cohesion: 0.25
Nodes (8): 建连早期误报 engine_error 根治, handler 内零 I/O（只置标志 + 记信号号）, 安全点按「单元完成度」判定丢弃, Nova worker flag-only 协作式停止, 被拒方案：asyncio 化消除 greenlet, 被拒方案：handler raise _Terminated 穿透 with, 泄漏兜底：AgentCore 原生 session TTL, SIGINT（Ctrl-C）纳入 flag-only handler

### Community 168 - "render_traffic_policy"
Cohesion: 0.15
Nodes (13): 本 run 的 ngrok 流量策略 YAML（ADR 0051 决策 13）：手写模板替换，不为此引 yaml 依赖——结构固定，令牌与 cookie…, 把文本里每个「作为一个地址出现」的 origin 换成 base：origin 之后的 URL 字符段 R 为空、以 / ? #…, render_traffic_policy(), replace_origin(), parametrize, skipif, ADR 0051 决策 13「边缘策略」：恰 4 条规则（免费层上限 5）、不含 basic-auth 与 remove-headers、Set-Cookie…, ngrok 读的是解析后的结构、不是字面量，所以按 YAML 解析后核：四条规则按序 warmup-ok / warmup-reject / check-ok… (+5 more)

### Community 169 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 170 - "classify_vpc_state"
Cohesion: 0.25
Nodes (8): classify_vpc_state(), SSM 里记的生效取值 `stored` 是否与本次 `--vpc requested` 一致。 三种取值形态见…, 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, vpc_spec_matches(), parametrize, test_classify_four_states(), test_classify_stack_absent_is_first_deploy_even_without_param(), test_vpc_spec_matches()

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
Cohesion: 0.09
Nodes (43): Archify Diagram Viewer Preset (classic, showcase quality), 五层全景图, 一次 run 的生命周期图, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Env Inheritance Diagram (+35 more)

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

### Community 181 - "warmupSession"
Cohesion: 0.36
Nodes (6): leaveWarmupPage(), oneLine(), waitForMarker(), warmupErrorMessage(), WarmupPage, warmupSession()

### Community 182 - "test_fargate_engine.py"
Cohesion: 0.10
Nodes (30): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。 (+22 more)

### Community 183 - "_print_artifact_lines"
Cohesion: 0.50
Nodes (4): _print_artifact_lines(), 产物落点三行（报告 / 运行元信息 / 判定明细）→ stderr：**`run` 结束与 `status` 终态共用这一份**…, 报告写入被隔离（落点表里没有 report_index 键，ADR 0030 决定三）→ 报告那行给「写失败」提示， 既不打裸…, test_artifact_lines_report_write_failure_falls_back_to_a_note()

### Community 185 - "test_reconcile.py"
Cohesion: 0.07
Nodes (44): event_log adapters (sqlite / ddb), EventLog, finalize_report(), Launcher, Job, Protocol, reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。 `tick(run_id, meta)` 一步推进：读…, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由… (+36 more)

### Community 186 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 188 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 189 - "devDependencies"
Cohesion: 0.29
Nodes (7): @aws-sdk/client-device-farm, devDependencies, @aws-sdk/client-device-farm, @types/node, typescript, @types/node, typescript

### Community 190 - "移动真机支持（1.5）：实施进度总纲"
Cohesion: 0.40
Nodes (4): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）, 实施期要核的点（ADR 已定、实施时顺手验证）, 现场, 移动真机支持（1.5）：实施进度总纲

### Community 191 - "stopTimeout=120 / grace 预算校准"
Cohesion: 0.15
Nodes (14): ACT_TIMEOUT_S=120 不压（否决解法 B）, 中断产物丢失风险（容器盘停即销毁）, 孤儿产物扫盘 reaper（经分析否决）, 安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底, 关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）, stopTimeout=120 / grace 预算校准, IAM 最小权限（task role 动作×资源两维收窄）, job-in S3 对象按 tag 的 7 天 lifecycle (+6 more)

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

### Community 196 - "ScheduleOpts"
Cohesion: 0.11
Nodes (40): Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的…, ScheduleOpts, _assert_process_gone(), _engine(), _job(), _kill_quietly() (+32 more)

### Community 197 - "_add_device_flags"
Cohesion: 0.29
Nodes (7): _add_config_flag(), _add_device_flags(), _add_selection_flags(), ArgumentParser, run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。, 设备目标的选项（ADR 0053 决策 4）：按平台分开的设备 ARN（一个 run 可同时含 Android 与 iOS 的 scope）；run /…, 七个读项目配置文件的子命令共用（ADR 0053 决策 1）。

### Community 201 - "移动真机支持（1.5）：实施批次的改动面与先写的护栏测试"
Cohesion: 0.18
Nodes (10): 0. B0-navigation：导航规则与注册面关键字声明（1.4 行为的不兼容变更，自己发）, 1. B1-capabilities：能力自述增键（两个 worker 只声明桌面网页；CLI 唯一校验处与交集；doctor、list-deterministic 呈现）, 2. B5-core-events-termination：core 侧会话事件、scope 级 error、合成 SKIPPED、终结函数与真值表、计量合计、explain 呈现, 3. B2-core-target-job：测试目标与 Job 形态（core 侧 tag 归约、target 两形态、按目标的 timeout、plan 标注与目标拒绝、两个 worker 建会话前自检）, 4. B3-config-submit：项目配置文件、组合根填 device_request、definition 格式版本、CLI 侧应用上传, 5. B4-steps-registry：确定性 step 多句柄注册（targets、requires、driver 代理的注册面）, 6. B7-tunnel：隧道改为令牌换 cookie（桌面先行）、桌面 worker 的预热失败出口、脱敏规则三条, 7. B8-deploy-iac：部署侧：权限、Device Farm 项目找回或建立、SSM、doctor 设备项 (+2 more)

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

### Community 210 - "events_pk"
Cohesion: 0.29
Nodes (5): 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。, test_events_pk_composite_run_id_scope_id()

### Community 211 - "Job"
Cohesion: 0.04
Nodes (93): _explain_job(), 两个填完入口（ADR 0048 决策 3）：没有设备请求的设备 job 在本机与云端入口都以退出码 2 被拒，校验在入口内部、调用方不另调。, 写 definition 之前的结构校验（ADR 0048 决策 3 第一处）：组合根尚未填入设备请求的设备 job 以退出码 2 被拒；桌面 job 放行。, plan 形态的应用条目只有别名与包名两键（位置三项由组合根在提交时填入，ADR 0048 决策 3）。, 执行前预检的第二项目标检查（ADR 0048 决策 3）：job 墙钟预算超过该目标的会话上限即拒绝；桌面条目不带上限不检查。, test_complete_definition_entry_points_run_the_pre_write_check(), test_plan_json_app_entry_is_exactly_alias_and_app_id(), test_target_rejections_flag_timeout_over_session_limit() (+85 more)

### Community 213 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 214 - "gherkai_runtime/__init__.py"
Cohesion: 0.09
Nodes (29): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的四件产物：映射过的 definition + 隧道模式的额外请求头 + 会话预热地址 + 隧道事实（收尾凭据）。…, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, start_tunnel_for_jobs() (+21 more)

### Community 215 - "_DeterministicCtx"
Cohesion: 0.33
Nodes (3): _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）与导航原语…, 引擎的导航原语（内建导航条目用它打开地址，ADR 0020 第 3 条）：Nova 用 SDK 的 `go_to_url`。

### Community 220 - "gherkai_runtime/names.py"
Cohesion: 0.07
Nodes (34): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。… (+26 more)

### Community 223 - "precheck.mts"
Cohesion: 0.23
Nodes (12): DEVICE_LABEL, ADR-0024, ADR-0049, ADR-0051, precheckJob(), precheckSchema(), precheckTarget(), spaced() (+4 more)

### Community 224 - "runStep"
Cohesion: 0.50
Nodes (4): cumulativeTokens(), isTransientNetwork(), runStep(), stepCost()

### Community 228 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 240 - "format_event"
Cohesion: 0.50
Nodes (4): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id()

### Community 242 - "_read_events"
Cohesion: 0.18
Nodes (10): _join_pumps(), Event, Job, Popen, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 以非零退出码（含被信号强杀的负码）结束时抛错（终结函数按退出码判）。 纯阻塞行读、纯…, 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的… (+2 more)

### Community 245 - "CollectSink"
Cohesion: 0.07
Nodes (28): RuntimeError, worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerExitError, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), CollectSink (+20 more)

### Community 249 - "deterministic.test.mts"
Cohesion: 0.33
Nodes (4): HANDLES_FIXTURE, META, ADR-0022, ADR-0050

### Community 252 - "_delayed_stopped_ecs"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order()

### Community 255 - "⑦ 事实族横切记录（13 族）"
Cohesion: 0.14
Nodes (14): ⑦ 事实族横切记录（13 族）, F01 F01 退出码语义, F02 F02 状态枚举与终态（Status 七态、severity 序、_NON_VERDICT / _PRE_TERMINAL / TERMINAL_STATUSES、job 收场态、RUNNING / PENDING 触发、run 级聚合与钳制）, F03 F03 事件类型与字段（worker↔core 事件集、事件字段、errorType 类别集、job 行键集、会话事件派生的 sessions[] 键）, F04 F04 CLI 子命令与 flag（gherkai 与 gherkai deploy）, F05 F05 目录树与模块清单, F06 F06 版本 · 模型 ID · 依赖锁 · 运行时版本要求, F07 F07 命名契约（prefix、SSM 路径、表名、镜像 tag、ECR 仓名、task-def、stack 名、Device Farm 与应用前缀） (+6 more)

### Community 256 - "项目约定"
Cohesion: 0.29
Nodes (6): graphify, 代码纪律, 工作方式, 文档纪律, 沟通, 项目约定

### Community 265 - "main"
Cohesion: 0.15
Nodes (7): agentOpts(), drainArtifactQueue(), log(), main(), runScenario(), shutdownSequence(), step()

### Community 270 - "文档健康度复盘 · 第八轮 · 待批报告"
Cohesion: 0.17
Nodes (12): ① 基线, ② 请裁定（19 项，编号可一句话回）, 5.1 口吻与术语（TONE，引原句 + 改写句）, 5.2 冗余与沉积（REDUNDANCY / SEDIMENT，顺带发现；提纯主战场见第四节）, 5.3 `docs/journey/` 生命周期审计, ⑤ 主观发现待批（88 条：TONE 49、REDUNDANCY / SEDIMENT 36、journey 生命周期 3）, ⑥ 具名提纯审计记录（审计集 54 篇）, ⑧ Status 头与反向链、引用图、文件名 (+4 more)

### Community 271 - "index.mts"
Cohesion: 0.40
Nodes (4): ADR-0022, ADR-0036, ADR-0037, ADR-0050

### Community 273 - "test_app_upload.py"
Cohesion: 0.17
Nodes (15): _ClientError, _file(), Exception, Path, 安装包上传与复用（ADR 0051 决策 9）：键按内容哈希、404 上传（managed 带标签）、年龄在复用窗口内复用、超窗同键刷新、刷新失败重传、…, boto3 的 upload_file 把 ClientError 包成自己的 S3UploadFailedError（不是 botocore 异常）：404…, 假 S3 client：head 按预设返回或抛；记录 upload_file / copy_object 的入参；可让它们失败。, _S3 (+7 more)

### Community 282 - "ADR 0037: 分发与打包"
Cohesion: 0.09
Nodes (44): ADR 0005: 单一共享 feature 文件, ADR 0011: AgentCore 浏览器 system default vs custom, 系统默认浏览器 aws.browser.v1, 自建 custom browser（create-browser）, ADR 0015: v1 定位——柔性冒烟而非回归, 确定性 step（测试开发按需自建）, tunnel.py（--expose-local 隧道 provider）, tunnel_host.py（隧道宿主编排 + 守护 TTL） (+36 more)

### Community 295 - "RunPersistence"
Cohesion: 0.09
Nodes (35): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+27 more)

### Community 297 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 300 - "ADR 0016: 执行架构 — 核心库与 run 模型"
Cohesion: 0.10
Nodes (38): cli/DEVELOPMENT.md, CONTRIBUTING（contributor 入口）, core 包 contributor 文档, core 测试说明（单测 + 集成测试）, gherkai-deploy-aws contributor 手册, ADR 0016: 执行架构 — 核心库与 run 模型, AgentCore Evaluations（去优先级的相邻选项）, ADR 0017: 云端执行选 Fargate (+30 more)

### Community 301 - "ContainerError"
Cohesion: 0.08
Nodes (18): ContainerEngine, ContainerError, Exception, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 多平台索引的目标平台视图（`inspect --platform linux/amd64`）：返回 (os, architecture)，本机没有该平台的内容…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+10 more)

### Community 305 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 309 - "reconciler.py"
Cohesion: 0.08
Nodes (35): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+27 more)

### Community 315 - "test_tunnel_warmup.py"
Cohesion: 0.03
Nodes (86): _capabilities(), main(), 本 worker 的能力声明（`--capabilities` 的 stdout，ADR 0036「5.」）。 `min_grace_s` 是 grace…, test_sigterm_and_sigint_both_installed_as_flag_only(), _clock(), driven(), _FakeBrowserClient, _FakeCm (+78 more)

### Community 328 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 替换成干净的隧道地址 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_other_jobs_and_original_untouched(), test_map_replaces_docstring_and_datatable_cells_independently() (+1 more)

### Community 331 - "url_matches.py"
Cohesion: 0.50
Nodes (3): deterministic, 示范用确定性 step（Nova Act 侧）：断言当前页面地址匹配给定正则。 这是 `steps/` 目录的模板：复制进你的项目后按需改措辞与判定。与…, url_matches()

### Community 338 - "_joined_refs"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 343 - "settings.py"
Cohesion: 0.20
Nodes (17): apply_project_config(), configurable_keys(), convert_config_value(), find_option_action(), _is_repeatable(), option_actions(), ArgumentParser, 项目配置文件合成进命令行选项（ADR 0053 决策 2、3、6）：七个运行侧命令在 parse_args 之后、分派之前经… (+9 more)

### Community 351 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 383 - "test_fail_fast_stops_running_workers_from_main_thread_without_heartbeat"
Cohesion: 0.33
Nodes (5): 运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 设备 job 的建连失败不做 job 级重试（ADR 0051 决策 2）：同样的零 step_done network_error，桌面 job 重试、设备…, fail-fast：主线程的 _stop_all 对仍在运行的 worker 当场落定并发停止请求，不依赖该 worker 自己的心跳检查（这里关掉心跳、…, test_device_job_network_error_is_not_retried(), test_fail_fast_stops_running_workers_from_main_thread_without_heartbeat()

### Community 388 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): navigate(), deterministic, 确定性 step 脚手架（ADR 0020/0022）—— 本包随 worker 发行的注册表内容：**只有内建导航一条**。 机制（ADR…, 内建导航（ADR 0020 第 3 条）：整句为地址的 Given / When step，直接打开，不走 AI。

### Community 398 - "_out"
Cohesion: 0.09
Nodes (31): Aws, _connect(), list_workers(), make_aws(), _pending_cleanup(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 本模块用到的四个 client。**组合根注入**（测试直接塞 moto client），同 compose 的 `_make_*` 惯例。 (+23 more)

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
- **857 isolated node(s):** `SESSION_WARMUP_URL_ENV`, `EXTRA_HTTP_HEADERS_ENV`, `SESSION_WARMUP_KEY`, `WARMUP_PATH`, `CHECK_PATH` (+852 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **156 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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