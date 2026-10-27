# Graph Report - yaozhou  (2026-10-27)

## Corpus Check
- 392 files · ~636,956 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 7016 nodes · 14731 edges · 424 communities (257 shown, 167 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1354 edges (avg confidence: 0.73)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9266ff18`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- main
- test_backend_cloud.py
- test_main.py
- JobResult
- Job
- Provider
- schedule
- test_project.py
- test_workers.py
- test_plan.py
- workers.py
- ADR 0014: AI 优先断言
- ._run_cdk
- _run_step
- report_store/local.py
- model.py
- test_stack.py
- _Nova
- test_deploy_cmd.py
- test_container.py
- test_cloud_reconcile.py
- materialize.py
- DynamoDBRunStore
- scan_family
- test_report_store.py
- test_capabilities.py
- ADR-0008
- evidence.py
- test_conditional_writes.py
- ADR 0043：驱动 gherkai 的 agent skill
- submission.py
- _fixture
- preflight_cloud_resources
- _RecUploader
- test_worker_variant.py
- query_capabilities
- FargateEngine
- test_tunnel_cli.py
- skill_markdown_files
- CONTRIBUTING.md: contributor 指南
- render.py
- _ask_worker
- cli.py
- redact_secrets
- ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）
- main
- 云端后端用户文档
- test_compose.py
- _render_status
- _explain_run
- device_selection.py
- test_render.py
- test_user_docs.py
- test_lambda_asset.py
- no-artifacts.test.mts
- test_interrupt_model.py
- ._run_once
- _FakeNovaActClient
- BackendStack
- test_star_step_keyword_fails_fast
- _cmd_run
- ValueError
- test_fargate_engine.py
- build_cloud_stores
- Video Material Manifest
- evidence.mts
- test_artifact_upload.py
- _doc_rules.py
- _is_transient_network
- textui.py
- scope.py
- Path
- test_evidence.py
- test_stores.py
- 06-devicefarm-appium.mts
- gherkai 变更记录 (CHANGELOG)
- serialize.py
- ArtifactUploader
- test_detached_launcher.py
- tunnel-warmup.mts
- _resolve_steps_dir
- _read_events
- user-steps.mts
- test_user_steps.py
- event-sink.mts
- test_termcolor.py
- test_cli_json_contract.py
- 决策
- event_from_json
- README Video Specs
- TypeScript Build Config
- config.py
- _StampSsm
- Composition Root Architecture
- test_project_config.py
- test_adr_hygiene.py
- build_engines
- Video Material Files
- DdbEventLog
- deterministic.py
- redact_secrets
- skill_install.py
- 决策
- Run Store Persistence Ports
- cleanup_pass
- image_tag
- 决策
- 决策
- test_termination_parity.py
- precheck_target
- dependencies
- test_lambda_handlers.py
- _presend_act_siblings
- Diagram Build Script
- ArtifactUploader
- test_engines_matrix.py
- evidence.test.mts
- test_event_sink.py
- _SeqEcs
- _NetRaiseEngine
- .create_run
- Event Wallclock Analysis
- Release Notes Guards
- e2e_harness.py
- test_skill.py
- .add_arguments
- run-scope.test.mts
- Dist Metadata Checks
- JobState
- Package README Guards
- _events_table_actions
- Media Conversion Verification
- package.json
- ContainerError
- _MissingThenStoppedEcs
- _FakeSink
- plan
- DynamoDB Events Transport ADR
- constants.py
- 决策
- ScopeStarted
- _cmd_doctor
- test_skill_deploy_tokens.py
- test_s3_report_store.py
- Stateless Run Core Model
- EventSink
- argument.mts
- User-Facing Text Guards
- project.py
- S3StepArgumentOffloader
- 0050. 确定性 step 多句柄注册与测试分层
- atomic_write_json
- run_scope.py
- artifact-upload.test.mts
- test_tunnel.py
- Worker Signal Interrupt Tests
- engines-matrix.test.mts
- ADR 0043: 随 CLI 发行的 agent skill
- tunnel-warmup.test.mts
- ECS Task Timing Capture
- test_definition_schema.py
- Artifact Uploader Component
- tunnel_warmup.py
- Graphify Refresh Script
- reconcile.tick（推进器共享入口）
- job-source.mts
- test_tunnel_host.py
- Cooperative Stop Design
- test_error_step_also_enqueues_only_after_emit
- Doc Rules Check
- tunnel.py
- openai
- redact.mts
- Engine Port & Job Planning
- Scope Tag Parsing
- 执行与推进模型导览（run/submit × local/cloud）
- Context Glossary Guards
- main
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- JobResult
- container_name
- RunState
- @playwright/test
- test_reconcile.py
- Echo Test Worker
- Cloud Infra Self-Check
- _tagged_feature
- devDependencies
- 移动真机支持（1.5）：实施进度总纲
- stopTimeout=120 / grace 预算校准
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- Gherkin Parse Seam
- files
- Repository Metadata
- test_subprocess_engine.py
- _FakeResult
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试
- _FakeEcs
- Architecture Diagrams
- Slide Frame SSIM Checks
- artifact_upload.py
- AgentCore CDP Script
- _Calls
- RunResult
- Pre-commit Hook Script
- _CdkWritingContext
- .peek_definition_header
- Adapters Package
- user-steps.test.mts
- watch_run_and_stop_tunnel
- scan
- Step Matching & Plan Annotation
- deterministic
- agentcore-sigv4.test.mts
- DeterministicCtx
- DeterministicKeywordMismatch
- .enqueue
- test_provider_module_does_not_import_aws_cdk
- precheck.mts
- Path
- Index Wait Script
- gherkai Workspace Root
- ResourceUri
- error-text.mts
- Execution Backend
- Feature Files
- Error Type Classification
- Local Per-Run Advance Process
- .drain
- gherkai Core Package
- AWS Deploy Package
- Runtime Package
- NovaAct Worker Package
- RuntimeError
- event-sink.test.mts
- Popen
- job-source.test.mts
- redact.test.mts
- .on_event
- JobResult
- .enabled
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- TaskExited
- RunResult
- test_bucket_without_logs_dir_fails_loud
- test_noop_uploader_enqueue_and_drain_are_immediate
- errors.py
- test_stale_projection_never_regresses_terminal_job_on_real_ddb
- compose.py
- Scenario
- Step
- StepArgument
- NgrokTunnel
- Status
- test_finalize_missing_run_fails
- test_lifecycle_states.py
- run-scope.mts
- Scenario
- Step
- fixture
- test_leading_and_keyword_fails_fast
- ssm_path
- index.mts
- _documented_keys
- ensure_app_object
- Job
- DEFAULT_MODEL
- MODEL
- MODEL_FAMILY_PATTERNS
- ADR-0033
- ADR-0037
- ADR-0044
- ADR 0037: 分发与打包
- CONTENT_TYPES
- ADR-0016
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0032
- ADR-0033
- ADR-0042
- UPLOAD_TIMEOUT_MS
- .delete_worker
- SqliteEventLog
- plan_next
- ADR 0023: Nova Act acting 锁 Python
- RuntimeError
- BaseException
- Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障
- cli/tests/conftest.py
- ADR 0024: worker–core 协议
- test_run_and_submit_exit_2_before_spawn_when_user_steps_fail
- exceptions
- NonTerminalSnapshot
- WebdriverCtx
- _cmd_list_engines
- RFC-3986
- ._installed_import_source
- _FakeCdp
- reconciler.py
- @aws-sdk/client-dynamodb
- Event
- Path
- Any
- finalize_job
- _FakeS3
- projected_run_status
- .__init__
- render_traffic_policy
- ArgumentParser
- parametrize
- gherkai：价值与方法（材料索引）
- Job
- Path
- fixture
- precheck.test.mts
- WebdriverApp
- StepArgument
- Fargate/ECS RunTask 执行后端
- severity 数值序（_STATUS_SEVERITY）
- url_matches.py
- replace_origin
- Exception
- runStep
- RunMeta
- deterministic
- PlanConfig
- _joined_refs
- _explain_emit
- _AbsentEngine
- RuntimeError
- settings.py
- test_ecr_repos_have_no_lifecycle_rules_and_are_retained
- unspecified_message
- gherkai_cli/__main__.py
- list
- RunMeta
- Job
- Job
- Target
- Protocol
- ResourceUri
- datetime
- JobResult
- test_worker_template_arn_is_not_injected_into_any_lambda_env
- ValueError
- _cmd_deploy
- Target
- RunResult
- RunState
- Template
- RuntimeError
- _DeterministicCtx
- RunResult
- ADR-0025
- test_device_job_network_error_is_not_retried
- test_timeout_wins_over_abort_when_deadline_already_passed_on_every_branch
- test_fail_fast_stops_running_workers_from_main_thread_without_heartbeat
- parametrize
- Job
- ADR-0052
- ProjectConfig
- DeterministicAssertion
- _out
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
- ADDRESS_PATTERN
- ADR-0020
- ADR-0022
- ADR-0036
- ADR-0037
- ADR-0048
- WEB_SCHEMES
- ADR-0037
- ADR-0049
- ADR-0050
- NormalizedWebdriverEntry
- PLAYWRIGHT_TARGET
- REGISTRY
- RegistryEntry
- @midscene/web
- Requirement
- REQUIREMENTS
- SelectedHandler
- StepTarget
- StepTargetKey
- TARGET_DEVICE_ORDER
- UI_KINDS
- UiKind
- WebdriverDevice
- WebdriverEntry
- WebdriverHandler

## God Nodes (most connected - your core abstractions)
1. `main()` - 272 edges
2. `Provider` - 100 edges
3. `Job` - 94 edges
4. `schedule()` - 85 edges
5. `RunState` - 78 edges
6. `CollectSink` - 76 edges
7. `FakeEngine` - 73 edges
8. `JobState` - 70 edges
9. `RunMeta` - 69 edges
10. `Scenario` - 68 edges

## Surprising Connections (you probably didn't know these)
- `--interrupt 中断时机矩阵` --shares_data_with--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `e2e_harness.py（opt-in 手动端到端验证脚本）` --calls--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `render()` --references--> `docs/internals/cli-json-contract.md（机读字段级参考页）`  [EXTRACTED]
  tools/render_skill_contract.py → docs/adr/0045-documentation-layering-and-placement.md
- `e2e_harness.py（opt-in 手动端到端验证脚本）` --calls--> `resolve_worker_cmd()`  [EXTRACTED]
  tools/e2e_harness.md → runtime/gherkai_runtime/compose.py
- `scenario 到 job 图` --conceptually_related_to--> `架构总览：五层结构、一次 run 的生命周期、包与发行物`  [AMBIGUOUS]
  docs/diagrams/writing-features-scenario-to-job.svg → docs/internals/architecture-overview.md

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

## Communities (424 total, 167 thin omitted)

### Community 0 - "main"
Cohesion: 0.05
Nodes (56): main(), --version 打印「gherkai <发行版本>」并以退出码 0 结束——版本真源是包元数据（git tag → uv-dynamic-…, 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, 命中了确定性 step、但它在该 scope 的目标上没有实现（句柄声明与 worker 支持的交集不含该目标，ADR 0049 决策 3、6；0050 决策…, ADR 0048 决策 5：引擎自述支持 Android 时，plan 显示 target=android/web、远程访问会话数 1，--json 里… (+48 more)

### Community 1 - "test_backend_cloud.py"
Cohesion: 0.04
Nodes (109): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), _patch_skew(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, status 不解析 variant（ADR 0038）：它只读运行态、不起 task，definition 里的 revision 提交时已定死。, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：… (+101 more)

### Community 2 - "test_main.py"
Cohesion: 0.03
Nodes (142): _capturing_schedule(), _cloud_backend_ok(), _det_feature(), _doctor_cloud_json(), _fake_locator(), _fake_schedule_factory(), _miss(), _no_provider() (+134 more)

### Community 3 - "JobResult"
Cohesion: 0.06
Nodes (35): _device_keys_for_explain(), 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。 (+27 more)

### Community 4 - "Job"
Cohesion: 0.04
Nodes (93): _explain_job(), 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…, 两个填完入口（ADR 0048 决策 3）：没有设备请求的设备 job 在本机与云端入口都以退出码 2 被拒，校验在入口内部、调用方不另调。, 写 definition 之前的结构校验（ADR 0048 决策 3 第一处）：组合根尚未填入设备请求的设备 job 以退出码 2 被拒；桌面 job 放行。, plan 形态的应用条目只有别名与包名两键（位置三项由组合根在提交时填入，ADR 0048 决策 3）。, 执行前预检的第二项目标检查（ADR 0048 决策 3）：job 墙钟预算超过该目标的会话上限即拒绝；桌面条目不带上限不检查。, test_complete_definition_entry_points_run_the_pre_write_check() (+85 more)

### Community 5 - "Provider"
Cohesion: 0.05
Nodes (94): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _argv(), cdk(), _FakeEngine, _parse(), _parse_destroy(), Path (+86 more)

### Community 6 - "schedule"
Cohesion: 0.12
Nodes (82): RunMeta, 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+74 more)

### Community 7 - "test_project.py"
Cohesion: 0.06
Nodes (76): EventRecord, project(), project_full(), RunMeta, RunResult, events 表里一条记录的投影输入（ADR 0034）：reconciler 从表全量重放时，每条 record 携带的信息。 worker…, 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与… (+68 more)

### Community 8 - "test_workers.py"
Cohesion: 0.08
Nodes (70): _cleanup(), FakeContainer, _mapping(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 一次干净的推送：tag/push 到 ECR ref → 从模板注册 revision（镜像按 digest、血缘 tags 齐）→ 写 SSM 映射。, digest 的唯一来源是 **推送后**那次 inspect，且在多条 `RepoDigests` 里**按本 repo 挑**（GHCR 那条在第一位）。 (+62 more)

### Community 9 - "test_plan.py"
Cohesion: 0.09
Nodes (43): _cfg(), _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 低于下限的改法要按删掉 tag 后真正接替的来源给：--default-job-timeout 也低于下限时不能只说「删 tag 走缺省」（删了仍被它拒）。, 「任一成员标了即整个 scope 生效」不只看首个成员：带 tag 的成员排在后面也生效。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否… (+35 more)

### Community 10 - "workers.py"
Cohesion: 0.06
Nodes (72): Aws, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable(), ImageMapping (+64 more)

### Community 11 - "ADR 0014: AI 优先断言"
Cohesion: 0.06
Nodes (55): CLAUDE.md（项目约定）, CONTEXT.md（领域概念与术语）, ADR 0001: 范围限于英文 UI, 概念：非英文应用用 @engine:midscene 路由, 概念：Nova Act 中文词语级文本匹配短板, ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码, 概念：Midscene 仅走 chat-completions 接口 (+47 more)

### Community 12 - "._run_cdk"
Cohesion: 0.06
Nodes (26): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), _make_hint_clients(), Path, 「缺 --vpc」提示专用的短超时句柄：纯参数错误不该被网络拖住（连不上即放弃、不重试）。 与 `_make_cfn_client` /…, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2… (+18 more)

### Community 13 - "_run_step"
Cohesion: 0.08
Nodes (54): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_step(), _ActBoom, _done(), _FakeNova, _run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。 与 Midscene 引擎 run-scope.test.ts… (+46 more)

### Community 14 - "report_store/local.py"
Cohesion: 0.09
Nodes (27): device_header_lines(), scope 表头的设备两行（ADR 0051 决策 8）：代表会话的设备描述、会话 ARN 对应的 Device Farm 控制台链接；桌面 job…, test_console_url_only_for_session_arns(), ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出… (+19 more)

### Community 15 - "model.py"
Cohesion: 0.04
Nodes (70): 机读文档里 sessions[] 一项的 dict → 具 session_id / device 属性的视图（让 representative_device…, _SessionView, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, ReportStore adapters (local / s3), ResultStore adapters (local / s3), ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path (+62 more)

### Community 16 - "test_stack.py"
Cohesion: 0.04
Nodes (27): BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。…, 两个推进器（reconciler / kicker）的角色都不读 SSM 参数：definition 缺 `worker_task_defs` 按定义违约标… (+19 more)

### Community 17 - "_Nova"
Cohesion: 0.17
Nodes (23): ArtifactUploader, _get_uploader(), _done(), _Nova, parametrize, Path, fake nova：act/act_get 回带 trajectory 路径的结果；act_raises 时抛（模拟 act 中途失败）。, evidence.json 的即时上传失败也只丢 ref（to_report_ref 的「失败即抛」契约不动，兜法在调用方）。 只让… (+15 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 19 - "test_container.py"
Cohesion: 0.04
Nodes (57): ContainerEngine, digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 多平台索引的目标平台视图（`inspect --platform linux/amd64`）：返回 (os, architecture)，本机没有该平台的内容…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。 (+49 more)

### Community 20 - "test_cloud_reconcile.py"
Cohesion: 0.10
Nodes (27): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, _job(), _meta(), cloud 无状态批量运行 core 侧测试（ADR 0034 云端后端）：DdbEventLog + CloudLauncher +… (+19 more)

### Community 21 - "materialize.py"
Cohesion: 0.09
Nodes (47): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+39 more)

### Community 22 - "DynamoDBRunStore"
Cohesion: 0.09
Nodes (18): DynamoDBRunStore, _job_state_from_item(), _job_state_to_item(), JobState, Status, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。 (+10 more)

### Community 23 - "scan_family"
Cohesion: 0.15
Nodes (12): _parse_ts(), _pending_cleanup(), family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, family 的全部 ACTIVE revision（带 tags）。 两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-…, tag 里的 ISO 串 / boto3 回来的 datetime → aware UTC datetime；空或读不懂 → None。, 已退休（带 retired-at）与孤儿（带血缘 tags、不在任何版本的映射里）——清理 pass 的候选，列出来才可解释 「为什么 family 里…, RevisionInfo (+4 more)

### Community 24 - "test_report_store.py"
Cohesion: 0.13
Nodes (48): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3(), 层级归属（ADR 0047）：原因与产物地址挂在所属 step 下，不挂到 scenario 或 job。, test_render_text_shows_step_level_report_refs(), test_run_tree_attaches_reason_and_refs_under_their_step(), LocalReportStore (+40 more)

### Community 25 - "test_capabilities.py"
Cohesion: 0.14
Nodes (19): _clean_env(), `--capabilities` 自述入口单测（ADR 0036「5.」/ ADR 0024「引擎自报下限」，Nova 侧）。…, 不注入任何 env（旧宿主 / 手动直接运行）：下限仍 ≥ 缺省 act 上界 120 + margin，不退化成小值。, 不读 stdin：stdin 是一根**写端一直开着**的管子——真去读就永远阻塞、这里就 timeout 失败。…, steps 加载失败在这个入口也 fail-loud（ADR 0037 决策 4「两个非 job 入口同样加载 steps」）： 非 0 退出、stderr…, `--list-deterministic` 已删、**不留别名**（ADR 0036 被拒方案末条「每个自述项一个独立 flag」）。 只有真 argv…, 子进程 env：保留运行必需项，剥掉 GHERKAI_* / AWS_* / NOVA_*（含本机 region 与凭证落点）。 剥 AWS…, 键集恰六个，且 `min_grace_s` 是注入的 `NOVA_ACT_TIMEOUT_S` 加 worker 侧 margin（组合根查它当 grace… (+11 more)

### Community 27 - "evidence.py"
Cohesion: 0.09
Nodes (35): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Any, Path (+27 more)

### Community 28 - "test_conditional_writes.py"
Cohesion: 0.09
Nodes (44): _initial(), _meta(), RunMeta, RunState, RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。… (+36 more)

### Community 29 - "ADR 0043：驱动 gherkai 的 agent skill"
Cohesion: 0.08
Nodes (48): _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏）, test_user_docs.py（用户文档与图源护栏）, ADR 0001：范围限定英文 UI, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0041：面向 agent 的 CLI 可操作面, ADR 0043：驱动 gherkai 的 agent skill (+40 more)

### Community 30 - "submission.py"
Cohesion: 0.08
Nodes (36): progress(), 命令行的进度与诊断输出（ADR 0047）：一个函数，供 `__main__` 与各编排模块共用。, 进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `gherkai run ……, account_of(), ARN 的账号段（项目 ARN 的第五段）。, config_layers(), identity_layers(), `compose.resolve_aws_identity` 的配置文件层（region / profile 排在环境变量之后，ADR 0053 决策 2）。 (+28 more)

### Community 31 - "_fixture"
Cohesion: 0.07
Nodes (36): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。 (+28 more)

### Community 32 - "preflight_cloud_resources"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 33 - "_RecUploader"
Cohesion: 0.09
Nodes (19): _drain_evidence_uploads(), 收尾：**有界**等 evidence 截图的后台队列传完（ADR 0042 决策一）。best-effort、绝不抛。…, _FakeNovaAct, _install_provider(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 零 evidence（单例还没造）→ 直接返回；且**不在退出路径上现造上传器**（半注入会 fail-loud 抛）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。 (+11 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.06
Nodes (56): default_name(), ecr_repo_name(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…, （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, prefix + 基名（原样拼，prefix 含分隔符由部署方负责）。CDK 与 cli 共用此推导 → 单一事实源。, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称… (+48 more)

### Community 35 - "query_capabilities"
Cohesion: 0.06
Nodes (45): engine_min_grace(), _is_finite_number(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, 有限的 int / float（bool 单独挡；超出 float 范围的大整数按「不是有限数」处理，不让 math.isfinite 的…, targets 数组的形态校验（ADR 0049 决策 1）：顶层 targets 必有（缺键由调用方按版本不一致拒绝），step 级只在键存在时调用；显式…, _validate_targets() (+37 more)

### Community 36 - "FargateEngine"
Cohesion: 0.16
Nodes (13): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+5 more)

### Community 37 - "test_tunnel_cli.py"
Cohesion: 0.08
Nodes (46): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, 不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。, 隧道起不来（如 authtoken 缺失）→ 给退出码 2「没开始执行就被拒」，不产生引擎费用。, local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里预热地址的令牌是 `***`、判定消息里的… (+38 more)

### Community 38 - "skill_markdown_files"
Cohesion: 0.12
Nodes (18): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。 (+10 more)

### Community 39 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.07
Nodes (43): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, cli 包 contributor 文档, skill 参考：CLI --json 字段契约, skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法 (+35 more)

### Community 40 - "render.py"
Cohesion: 0.07
Nodes (53): _cmd_plan(), 用例预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…, _add_act(), _add_device_evidence(), _add_step(), _arg_hint(), _cost_bits(), device_session_count() (+45 more)

### Community 41 - "_ask_worker"
Cohesion: 0.08
Nodes (23): _ask_worker(), build_local_stores(), local_artifact_locations(), match_deterministic(), prune_empty_dirs(), Path, worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。… (+15 more)

### Community 42 - "cli.py"
Cohesion: 0.05
Nodes (48): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client() (+40 more)

### Community 43 - "redact_secrets"
Cohesion: 0.17
Nodes (12): 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则，与…, 三条规则依次作用于一段文本；None 原样返回。, redact_secrets(), parametrize, 凭据脱敏三条规则的单测（Nova worker 的那份实现，ADR 0035 决策 5；0051 决策 11）。…, 规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉。, 前一个字段的地址不带 @、后一个字段里有 @：匹配停在引号处，不跨字段吞掉内容。 (+4 more)

### Community 44 - "ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）"
Cohesion: 0.09
Nodes (34): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）, 墙钟时长归约（step/scenario/scope/run duration_ms）, EngineResolver（按 job.engine 解析 Engine）, 失败隔离 / failFast 旋钮, 优雅终止：schedule 只调 handle.stop(grace), _heartbeat_wrap（静默 worker 心跳注入） (+26 more)

### Community 45 - "main"
Cohesion: 0.06
Nodes (38): _capabilities(), main(), 本 worker 的能力声明（`--capabilities` 的 stdout，ADR 0036「5.」）。 `min_grace_s` 是 grace…, test_sigterm_and_sigint_both_installed_as_flag_only(), _clock(), driven(), _FakeCdp, _FakeNovaAct (+30 more)

### Community 46 - "云端后端用户文档"
Cohesion: 0.10
Nodes (39): gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce）, kicker Lambda（冷启动器）, reconciler Lambda（主推进器） (+31 more)

### Community 47 - "test_compose.py"
Cohesion: 0.04
Nodes (77): check_version_skew(), Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`，再缺取配置文件的 profile（ADR 0053 决策…, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_aws_identity() (+69 more)

### Community 48 - "_render_status"
Cohesion: 0.17
Nodes (20): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。 (+12 more)

### Community 49 - "_explain_run"
Cohesion: 0.10
Nodes (31): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+23 more)

### Community 50 - "device_selection.py"
Cohesion: 0.09
Nodes (30): ProjectConfig, 读出来的项目配置。`path` 为 None 表示没有配置文件（缺省位置不存在不算错，决策 1），四节都为空。 `common` / `cloud` 的值保持…, 路径类值相对配置文件所在目录绝对化（决策 2）；没有配置文件时原样返回（不该被调到，保险起见）。, 给 plan 层的纯数据表：别名 → 平台 → 包名或 bundle id（core 据此核对 @app，不带文件路径）。, acquire_timeout_for(), _arn_kind(), billing_method_for(), build_device_request() (+22 more)

### Community 51 - "test_render.py"
Cohesion: 0.09
Nodes (39): explain_to_dict(), format_event(), RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, render_run_state(), render_text() (+31 more)

### Community 52 - "test_user_docs.py"
Cohesion: 0.09
Nodes (38): changelog_unreleased(), prose_lines(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _default_model_claims(), _default_model_ids(), parametrize, Path (+30 more)

### Community 53 - "test_lambda_asset.py"
Cohesion: 0.12
Nodes (23): make_stack(), make_template(), Template, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path (+15 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (36): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用… (+28 more)

### Community 56 - "._run_once"
Cohesion: 0.17
Nodes (12): is_device_job(), job 的测试目标是否为设备（判据取 Job 上的目标字段；目标字段落地前所有 job 都是桌面网页，恒 False）。, _heartbeat_wrap(), Event, 单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。, 对本 job 落定停止原因并（首次）向 worker 发停止请求；已落定、已返回或内容已完整的直接返回现值。事件循环、异常分支与…, 内容已完整而 deadline 已过：只催 worker 收尾（发停止请求，排空上界从此刻起算），不落定停止原因——判定已成，…, 运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error… (+4 more)

### Community 57 - "_FakeNovaActClient"
Cohesion: 0.21
Nodes (14): worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, _FakeNovaActClient, _patch(), ensure_workflow_definition 单测（ADR 0004 create-if-not-exists）：串行 +…, nova-act client 替身：get 按 `exists` 决定是否 404，create 按 `create_error` 决定抛什么。, 并发赢家已建（409）→ 'exists' 且不抛，使 create-if-not-exists 的幂等在并发下也成立（ADR 0004）。 (+6 more)

### Community 58 - "BackendStack"
Cohesion: 0.09
Nodes (20): Cluster, Construct, BackendStack, BackendStack._build_lambda_asset, BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个… (+12 more)

### Community 60 - "_cmd_run"
Cohesion: 0.09
Nodes (28): _build_run_meta(), _cloud_worker_variant_gate(), _cmd_run(), _cmd_skill_install(), _cmd_submit(), _installed_version(), _plan_and_preflight(), _preflight_worker_runtimes() (+20 more)

### Community 61 - "ValueError"
Cohesion: 0.05
Nodes (49): DefinitionContractError, definition 的结构违约（ADR 0048 决策 3）：非桌面目标没有设备请求、应用条目不完整、设备请求字段不成对等。 写 definition…, JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称… (+41 more)

### Community 62 - "test_fargate_engine.py"
Cohesion: 0.08
Nodes (53): _delayed_stopped_ecs(), _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。 (+45 more)

### Community 63 - "build_cloud_stores"
Cohesion: 0.08
Nodes (28): build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_ecs_client(), _make_s3_client(), _normalize_prefix(), 读一个 `ResourceUri` 的字节（`file://`、裸路径、`s3://`）——**前端层解引用产物 ref 的唯一入口**（ADR 0042… (+20 more)

### Community 64 - "Video Material Manifest"
Cohesion: 0.06
Nodes (33): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+25 more)

### Community 65 - "evidence.mts"
Cohesion: 0.09
Nodes (30): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+22 more)

### Community 66 - "test_artifact_upload.py"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 67 - "_doc_rules.py"
Cohesion: 0.12
Nodes (30): ai_side_docs(), classify(), code_comment_files(), comment_units(), diagram_sources(), long_term_docs(), Path, 人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。 内容三类：①规则——内部指代表 FORBIDDEN、口吻表… (+22 more)

### Community 68 - "_is_transient_network"
Cohesion: 0.12
Nodes (31): BaseException, _is_transient_client_error(), _is_transient_network(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+23 more)

### Community 69 - "textui.py"
Cohesion: 0.12
Nodes (28): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。, 深度优先找第一个 label 含 needle 的节点（测试与诊断用）。, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，… (+20 more)

### Community 70 - "scope.py"
Cohesion: 0.23
Nodes (15): FeatureContractError, 用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/target/timeout 校验 → Job[]。…, 解析一个 scope 的测试目标（ADR 0048 决策 2）：@device 与 @app 各按 engine 同样的三条规则归约（任一成员标了即整个…, 解析一个 scope 的 job 墙钟预算（ADR 0019 @timeout；覆盖与校验顺序归 ADR 0034「job timeout」节、0051 决策…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。 (+7 more)

### Community 71 - "Path"
Cohesion: 0.12
Nodes (18): _cmd_reconcile(), _cmd_status(), _definition_contract_message(), _definition_schema_gate(), `--max-concurrency` 入口校验（对齐 `--tunnel-ttl`/`--grace`/`--assertion-votes`…, definition 结构版本不等于本 CLI 支持的那一个时给使用方的整句（ADR 0037 决策 7）：说清谁写的、两边各第几版、怎么办。, status / explain 读任何别的东西之前先核 definition 的结构版本（ADR 0037 决策 7）。`header` 是…, [无状态批量运行] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-… (+10 more)

### Community 72 - "test_evidence.py"
Cohesion: 0.17
Nodes (21): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _picks(), step 级机读证据（evidence，ADR 0042 决策一/二/六）单测：映射 / 截图上界 / 目录键 / best-effort 钩子。 纯…, n 帧的合成 trajectory：thought_at 里的帧带 think call，每帧都有可解的 data URL 图。, 转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了就会让 evidence 静默互相覆盖。, 同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。, 隧道凭据不进 evidence（ADR 0035 决策 5）：step 文本、act 指令、frame 地址、thought、消息里的 userinfo… (+13 more)

### Community 73 - "test_stores.py"
Cohesion: 0.04
Nodes (91): DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, JobState, Path, RunMeta, RunState (+83 more)

### Community 74 - "06-devicefarm-appium.mts"
Cohesion: 0.06
Nodes (80): ADR-0010, BASE_URL, main(), makePng(), REGION, ADR-0033, BASE_URL, main() (+72 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.09
Nodes (30): gherkai 变更记录 (CHANGELOG), gherkai destroy, --expose-local 隧道模式, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, gherkai deploy push-worker / list-workers (+22 more)

### Community 76 - "serialize.py"
Cohesion: 0.05
Nodes (57): AppRef, DeviceFarmRequest, 向 AWS Device Farm 要哪台设备（ADR 0048 决策 3）：名字明说服务商、不起中立名；`device_arn` 与…, 应用目标的应用条目（ADR 0048 决策 3）。两个形态：plan 形态只有别名与包名或 bundle id；run / submit 在组合根上传安装包后…, 一个 scope 运行在什么上面（ADR 0048 决策 1）：设备与界面类型；ui_kind 为 app 时带应用条目。缺省即桌面网页。, 机读与 plan 文本共用的紧凑写法（ADR 0048 决策 5 的形态）：`desktop/web`、`android/app:shop`。, Target, _argument_from_dict() (+49 more)

### Community 77 - "ArtifactUploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 78 - "test_detached_launcher.py"
Cohesion: 0.05
Nodes (70): Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, LocalRunStore, now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, build_local_reconcile(), cleanup_tunnel(), drive_local_reconcile() (+62 more)

### Community 79 - "tunnel-warmup.mts"
Cohesion: 0.08
Nodes (26): CHECK_PATH, COOKIE_NAME, EXTRA_HTTP_HEADERS_ENV, INCOMPLETE_DEFINITION_MESSAGE, ADR-0028, ADR-0039, ADR-0051, oneLine() (+18 more)

### Community 80 - "_resolve_steps_dir"
Cohesion: 0.33
Nodes (6): _cmd_list_deterministic(), 解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认…, `_resolve_steps_dir` + 云端后端清零（ADR 0037 决策 4）：云端后端 steps…, 按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern 语义（ADR…, _resolve_steps_dir(), _resolve_steps_dir_for_backend()

### Community 81 - "_read_events"
Cohesion: 0.11
Nodes (18): _join_pumps(), _pump_log(), Event, Job, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 以非零退出码（含被信号强杀的负码）结束时抛错（终结函数按退出码判）。 纯阻塞行读、纯…, scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+10 more)

### Community 82 - "user-steps.mts"
Cohesion: 0.11
Nodes (15): 确定性 step 加载失败即拒绝运行, fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037, ADR-0037, collectStepFiles() (+7 more)

### Community 83 - "test_user_steps.py"
Cohesion: 0.06
Nodes (54): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+46 more)

### Community 84 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0016, ADR-0024, ADR-0032, ADR-0033, ADR-0034, EventSink, resolveEventsFd()

### Community 85 - "test_termcolor.py"
Cohesion: 0.18
Nodes (16): 执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。, color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env() (+8 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.14
Nodes (22): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), RunResult, `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）；桌面与设备… (+14 more)

### Community 87 - "决策"
Cohesion: 0.10
Nodes (20): 0051. 设备会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034 (+12 more)

### Community 88 - "event_from_json"
Cohesion: 0.05
Nodes (62): _argument_to_json(), _cost_from_json(), _device_request_to_json(), event_from_json(), event_from_line(), job_to_json(), job_to_line(), Event (+54 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 91 - "config.py"
Cohesion: 0.23
Nodes (22): AppPlatformConfig, _apps_section(), _billing_method(), ConfigError, DevicePlatformConfig, _devices_section(), DevicesConfig, load_project_config() (+14 more)

### Community 92 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_project_config.py"
Cohesion: 0.09
Nodes (55): _android_caps(), _android_env(), _app_project(), _feature(), _no_match(), _plan_json(), Exception, parametrize (+47 more)

### Community 95 - "test_adr_hygiene.py"
Cohesion: 0.19
Nodes (18): _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。, Status 头里点名的取代方编号（只看 superseded-by 之后、到第一个注解分隔符为止那一段）。, 被取代方点了谁，谁就得回指它——机械差集，不靠读。 (+10 more)

### Community 96 - "build_engines"
Cohesion: 0.07
Nodes (35): Engine, FeatureSource, build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。 (+27 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "DdbEventLog"
Cohesion: 0.06
Nodes (35): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), DdbEventLog, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。… (+27 more)

### Community 99 - "deterministic.py"
Cohesion: 0.04
Nodes (75): deterministic, clear(), _closed_set(), deterministic(), DeterministicConflict, DeterministicKeywordMismatch, _Entry, Handles (+67 more)

### Community 100 - "redact_secrets"
Cohesion: 0.14
Nodes (18): Any, 工具自产文字里的凭据脱敏（ADR 0035 决策 5；ADR 0051 决策 11）：三条规则、三份同文实现。 三份同文实现（本文件、Nova worker…, 三条规则依次作用于一段文本；None 原样返回。 `https://u:p@host/x` →…, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_secrets(), parametrize, 凭据脱敏三条规则的单测（ADR 0035 决策 5；0051 决策 11）。 用例表只有一份：`engines/fixtures/redaction-… (+10 more)

### Community 101 - "skill_install.py"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 102 - "决策"
Cohesion: 0.13
Nodes (15): 0048. 测试目标：设备与界面类型两个维度、`@device` 与 `@app` 标签、core 的执行前预检, 1. 测试目标由三个正交维度描述：engine、device、ui_kind, 2. 两个 scope 级 tag：`@device` 与 `@app`, 3. core 的三处改动, 4. 目标不受支持时的拒绝：由能力自述决定，消息给出改法, 5. plan 的标注, 6. 运行期网页上下文不可用：声明了前提的确定性 step 记 error，不转 AI, 7. 应用目标上的导航 step 与落点核对规则 (+7 more)

### Community 103 - "Run Store Persistence Ports"
Cohesion: 0.14
Nodes (20): Commit-point Write Order (data plane first), RunStore.create_run(), DDB Single-Table Schema (run_id + item_type), DynamoDBRunStore, Cloud Failure Exit Code Layering, RunStore.finalize_run(), RunState high_water_mark Conditional Write, JobSink Port (+12 more)

### Community 104 - "cleanup_pass"
Cohesion: 0.10
Nodes (17): cleanup_pass(), CleanupOutcome, _hours(), _iter_image_params(), _mapped_arn(), _non_terminal_statuses(), 枚举 `worker-image/*` 全部参数（**含所有版本、所有引擎**）→ `(engine, tag, value)`。…, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看… (+9 more)

### Community 105 - "image_tag"
Cohesion: 0.17
Nodes (14): image_tag(), worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, parametrize, `gherkai_runtime.names` 的 worker 镜像交付命名（ADR 0038「tag 命名」条：单一真源、同时是单一校验点）。…, variant 本身合法但拼出来超 128 字符 → 报 tag 那一层（两类错误分开报，见 names 里两个正则的注释）。, 版本串首字符非法（归一化只管 `+`/`!`）→ tag 层拒，不静默产出 docker 不认的 ref。, `names` 的读端常量与 `DynamoDBRunStore` 的写端字面量必须逐字一致（ADR 0038 清理 pass 的运行中 run…, test_image_tag_normalizes_epoch() (+6 more)

### Community 106 - "决策"
Cohesion: 0.13
Nodes (15): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 不升 schema 版本，在 schema 1 上增键, 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端 worker 在建会话前按自己的 `targets` 自检 (+7 more)

### Community 107 - "决策"
Cohesion: 0.13
Nodes (15): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 7. Midscene 复用边界 (+7 more)

### Community 108 - "test_termination_parity.py"
Cohesion: 0.10
Nodes (25): 设备会话处置结束（ADR 0051 决策 4、7）：每个会话恰一条；release 是否确认停止；observed_s 是 worker 观察到的占用秒数…, SessionClosed, 合成明细与判定分开（ADR 0034 机制二）：scope 级 error 合成 SKIPPED 之后 worker 非零退出且已过 deadline /…, 超时处置后 worker 收 SIGTERM 走收尾、发出 session_closed(confirmed)：core 停止后继续消费到 EOF，U…, test_synthesized_details_survive_sync_path_timeout_and_abort(), test_tail_events_after_stop_are_still_reduced_and_release_confirmed(), _Clock, _closed() (+17 more)

### Community 109 - "precheck_target"
Cohesion: 0.10
Nodes (26): _num(), precheck_job(), precheck_schema(), precheck_target(), 建会话前的自检（ADR 0049 决策 7；ADR 0024「job 行的结构版本与固定键集」）：先核 job 行的…, (device, ui_kind) → 「桌面网页」「iOS 应用」这类名称（产品语言，与命令行工具的呈现同一口径）。, 名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」），全中文的名称原样；与命令行工具同一规则。, 秒数的写法：整数值不带小数点（1500 而不是 1500.0），其余按原值；与 Midscene 侧的插值结果一致。 (+18 more)

### Community 110 - "dependencies"
Cohesion: 0.11
Nodes (18): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js (+10 more)

### Community 111 - "test_lambda_handlers.py"
Cohesion: 0.02
Nodes (123): cloud_env(), _FakeEcs, fixture, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。 (+115 more)

### Community 112 - "_presend_act_siblings"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…, act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _traj_refs(), _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 113 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 115 - "test_engines_matrix.py"
Cohesion: 0.09
Nodes (26): _available_step_targets(), _probe_deterministic_dispatch(), plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…, plan 标注用：该引擎每条确定性 step 实际可用的目标（声明与 worker 支持目标的交集，ADR 0049 决策 3），按模式索引。…, 把名称嵌进中文句子时，拉丁字母开头或结尾处补一个空格（「在 Android 网页上」而不是「在Android 网页上」）；全中文的名称原样。, (device, ui_kind) → 「桌面网页」「Android 应用」这类名称；未知取值原样拼出（自述形态由组合根校验，这里只呈现）。, 前提清单 → 「需要网页上下文」；未知取值按「需要 <取值>」原样显示（ADR 0049 决策 1：CLI 不另立取值集合）。, 一组目标条目 → 「桌面网页、Android 网页（需要网页上下文）」；带 max_session_s 的条目按分钟附会话上限（doctor 用）；… (+18 more)

### Community 116 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 117 - "test_event_sink.py"
Cohesion: 0.15
Nodes (3): EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud()

### Community 118 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 119 - "_NetRaiseEngine"
Cohesion: 0.18
Nodes (6): FakeWorkerHandle, Event, Job, _NetRaiseEngine, Event, victim job 的 worker：等一个 gate 放行后才抛 WorkerNetworkError（模拟「建连退避期间」被中止/超时后以退出码 80…

### Community 120 - ".create_run"
Cohesion: 0.21
Nodes (8): RunMeta, RunState, run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。 **写序…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, 一次性写完整态（即 create_run 的两 item 一起 put；语义同 local save_run）。, 读回 definition（从 META item 的 meta_json）；不存在返回 None。, RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐…, _state_scalars()

### Community 121 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Release Notes Guards"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 123 - "e2e_harness.py"
Cohesion: 0.20
Nodes (13): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, build_job(), --interrupt 中断时机矩阵, e2e_harness.py（opt-in 手动端到端验证脚本）, Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策… (+5 more)

### Community 124 - "test_skill.py"
Cohesion: 0.08
Nodes (34): _claimed_flags(), _fixture_files(), _frontmatter_and_body(), _is_ignored(), _parser_nodes(), parametrize, Path, agent skill 的护栏（ADR 0043 决策六；fixture 三条见决策七）。 skill 是**产品面**：它随 wheel 发行、由… (+26 more)

### Community 125 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 126 - "run-scope.test.mts"
Cohesion: 0.08
Nodes (17): _events, fakePage, gotoCalls, importMod(), ADR-0014, ADR-0020, ADR-0024, ADR-0028 (+9 more)

### Community 127 - "Dist Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 128 - "JobState"
Cohesion: 0.07
Nodes (39): JobState, 单个 job 的控制面运行态（执行后才有）。, _ddb_store(), _is_ddb_too_large(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, 真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。, 真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛… (+31 more)

### Community 129 - "Package README Guards"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 130 - "_events_table_actions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉… (+4 more)

### Community 131 - "Media Conversion Verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 132 - "package.json"
Cohesion: 0.12
Nodes (16): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+8 more)

### Community 133 - "ContainerError"
Cohesion: 0.12
Nodes (11): ContainerError, Exception, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, CountingEcs, boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。, ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。, 重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…, 模板没变（deploy 重新运行的常态）→ 一次模板 describe 都不打：判定只用映射里记的模板 ARN。 (+3 more)

### Community 134 - "_MissingThenStoppedEcs"
Cohesion: 0.11
Nodes (17): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢… (+9 more)

### Community 135 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 136 - "plan"
Cohesion: 0.18
Nodes (17): FeatureSource, plan(), core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, select 不变量扩到目标（ADR 0041 决策一经 0025）：筛掉带 tag 的成员后，Job.target 与按目标得出的 timeout_s…, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只执行 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次运行哪几条。…, 整组被筛掉的 scope 里的 tag 冲突不拦本次迭代（空组在解析 engine/timeout 之前跳过）； 但「一个 scenario 多个… (+9 more)

### Community 137 - "DynamoDB Events Transport ADR"
Cohesion: 0.18
Nodes (13): DynamoDB 共享 events 表作 events-out 传输, EventSink（可注入事件出口）, events 表键设计 PK=run_id#scope_id, SK=seq, events item TTL 自动过期（7 天 expires_at）, 读一致性（流式期 EC 游标 + 终读强一致）, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列 (+5 more)

### Community 138 - "constants.py"
Cohesion: 0.20
Nodes (7): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开…, run(), workflow

### Community 139 - "决策"
Cohesion: 0.17
Nodes (12): 0053. 项目配置文件 gherkai.toml, 1. 文件定位：只有运行侧 CLI 读它，读出的值解析成具体值随 Job 走, 2. 取值顺序：选项、环境变量、配置文件、内建默认依次优先, 3. 节与键, 4. 设备选择要求显式，筛选的挑选规则确定, 5. 与 ADR 0044 覆盖链的关系：worker 侧覆盖项不进配置文件, 6. 护栏, 决策 (+4 more)

### Community 140 - "ScopeStarted"
Cohesion: 0.12
Nodes (40): test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, ScenarioDone, ScenarioStarted (+32 more)

### Community 141 - "_cmd_doctor"
Cohesion: 0.11
Nodes (21): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+13 more)

### Community 142 - "test_skill_deploy_tokens.py"
Cohesion: 0.12
Nodes (19): is_placeholder(), `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, _allowed_flags(), 只认**同一个反引号代码跨**内的 `gherkai <子命令> … --flag` 组合，逐对对照该 subparser 的真 flag 集。…, 裸词序列 → 子命令路径。第一个词不是已知子命令且不是占位符 → None（拼错的子命令）。, 路径上（含各级祖先）声明的 flag 全集——`deploy --prefix p push-worker …` 这种父层给法是合法的。, _resolve(), test_flags_are_attached_to_the_right_subcommand() (+11 more)

### Community 143 - "test_s3_report_store.py"
Cohesion: 0.17
Nodes (14): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3() (+6 more)

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "EventSink"
Cohesion: 0.22
Nodes (6): EventSink, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, test_emit_flushes_each_event(), TextIO

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "User-Facing Text Guards"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 148 - "project.py"
Cohesion: 0.08
Nodes (49): apply_device_metering(), device_metering(), _find_session(), Event, JobResult, 纯归约投影（ADR 0034）：events → JobResult/RunState，无 I/O、无执行编排、不 import boto3。…, 把单个 worker 事件归约进 JobResult（就地累积，ADR 0024/0026）。 **这是 `schedule._Worker._reduce`…, scope 级 error 后的明细补全（ADR 0051 决策 4；0031 决定一、六）：对 definition 中**零事件**的 scenario… (+41 more)

### Community 149 - "S3StepArgumentOffloader"
Cohesion: 0.12
Nodes (17): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, 指针必须是文本（s3:// URI）；别的类型是同版本下的定义违约，不让它变成 urlparse 的裸 AttributeError。, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与… (+9 more)

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.18
Nodes (11): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 2. handler 上下文：七个字段与一条不变量, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据 (+3 more)

### Community 151 - "atomic_write_json"
Cohesion: 0.15
Nodes (18): atomic_write_json(), atomic_write_text(), Path, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://…, _page(), 共享原子落盘助手（`gherkai_core.adapters._atomic`）的通用性质：并发读者只看到完整内容、权限按声明、失败不留 tmp。 三个… (+10 more)

### Community 152 - "run_scope.py"
Cohesion: 0.06
Nodes (45): ActRecord, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _argument_text(), _attach_evidence(), _clean_cell(), _collect_traj() (+37 more)

### Community 153 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 154 - "test_tunnel.py"
Cohesion: 0.18
Nodes (16): map_origin_in_jobs(), Job, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 把 job 文本中的 origin 替换成干净的隧道地址 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, stop_tunnel(), _job_with(), Job, tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。… (+8 more)

### Community 155 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 156 - "engines-matrix.test.mts"
Cohesion: 0.20
Nodes (7): DEVICE_LABEL, HANDLE_BY_DEVICE, MATRIX, ADR-0049, ADR-0050, Row, UI_KIND_LABEL

### Community 157 - "ADR 0043: 随 CLI 发行的 agent skill"
Cohesion: 0.06
Nodes (43): gherkai agent skill 包, RunMeta.extra_http_headers（额外请求头注入）, 隧道凭据脱敏（剥 URL userinfo）, URL 映射（job 组装时替换 origin 前缀）, worker --capabilities 自述入口, CLI list-deterministic --engine, 注册面元数据（description / example 必填）, CI 发布链与占名（tag 触发全链） (+35 more)

### Community 158 - "tunnel-warmup.test.mts"
Cohesion: 0.33
Nodes (3): FIXTURE, ADR-0035, ADR-0051

### Community 159 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 160 - "test_definition_schema.py"
Cohesion: 0.15
Nodes (22): parametrize, Path, definition 结构版本闸门（ADR 0037 决策 7）在 CLI 的接线：status / explain /…, 缺戳例外的接线：谓词为真的 run / submit 遇无版本戳后端以退出码 2 结束、资源检查一次不做；谓词为假（纯桌面）只警告放行。 谓词本身在…, 别的版本写出的 run 目录连运行态的形状都不保证：先核结构版本，再读运行态——否则「请升级」会变成一个解析异常。, 本机接力宿主读到同版本下形态违约的提交记录（这里真的从 run_meta.json 删掉一个 job 的 target 键）：CLI 读端有退出码可交，…, 读头阶段的形态违约（结构版本字段不是整数）：三个本机读端都以退出码 2 结束并说明，不是裸异常；运行态不被改动、不写 run 级消息…, 云端两个读端读 META 头时的形态违约（结构版本字段不是整数）：以退出码 2 结束并说明，不是裸异常；之后不再读运行态。 (+14 more)

### Community 161 - "Artifact Uploader Component"
Cohesion: 0.09
Nodes (29): 引擎特有量不进 model（act_count）, JobResult 持有 Job、engine 经 property delegate, href 相对化（local 相对 / cloud 恒等 ref）, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 式产物拷贝, 不透明搬运铁律（model/wire/schedule 永不解引用 ref）, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写） (+21 more)

### Community 162 - "tunnel_warmup.py"
Cohesion: 0.31
Nodes (9): _one_line(), Exception, 隧道会话预热（ADR 0051 决策 13）：worker 在第一个 scenario 之前对预热地址导航一次换到会话 cookie，并按页面的可见结果归因。…, 预热期间收到停止信号（ADR 0024 flag-only 协作停）：调用方按停止路径收尾，不算失败、不发 scope_done。, 对 `page` 导航预热地址、等页面标题落成四个标记之一；返回 None 表示就绪，否则返回归因与产品语言的消息。 `page` 是 Playwright…, _wait_for_marker(), warmup_session(), WarmupFailure (+1 more)

### Community 163 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 164 - "reconcile.tick（推进器共享入口）"
Cohesion: 0.20
Nodes (11): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState）, status --wait 接力推进 (+3 more)

### Community 165 - "job-source.mts"
Cohesion: 0.13
Nodes (10): Job, JOB_KEYS, JobApp, JobDeviceRequest, JobSource, JobTargetShape, Missing, ADR-0024 (+2 more)

### Community 166 - "test_tunnel_host.py"
Cohesion: 0.15
Nodes (19): compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的四件产物：映射过的 definition + 隧道模式的额外请求头 + 会话预热地址 + 隧道事实（收尾凭据）。…, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, start_tunnel_for_jobs(), TunnelSetup, _job() (+11 more)

### Community 167 - "Cooperative Stop Design"
Cohesion: 0.25
Nodes (8): 建连早期误报 engine_error 根治, handler 内零 I/O（只置标志 + 记信号号）, 安全点按「单元完成度」判定丢弃, Nova worker flag-only 协作式停止, 被拒方案：asyncio 化消除 greenlet, 被拒方案：handler raise _Terminated 穿透 with, 泄漏兜底：AgentCore 原生 session TTL, SIGINT（Ctrl-C）纳入 flag-only handler

### Community 168 - "test_error_step_also_enqueues_only_after_emit"
Cohesion: 0.12
Nodes (8): _NovaRaisesAfterFirstVote, 记 emit 与 enqueue 的**先后**（顺序即契约：判定绝不等截图字节）。, 第一票正常回（带 trajectory → 有截图可入队），第二票抛——把 except 出口逼成「有截图的 error step」。, except 出口（step 记 error）同守 emit→enqueue 序：三条出口共用一个收尾出口，不许有一条漏掉这层顺序。, _Result, test_error_step_also_enqueues_only_after_emit(), _TracingSink, list

### Community 169 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 170 - "tunnel.py"
Cohesion: 0.17
Nodes (14): _gen_secret(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 一条已建立隧道的事实。url / pid / local_origin 可落盘 tunnel.json 供跨进程收尾；warmup_url 含令牌，只进…, 每 run 一换的随机串：128 位、十六进制——不需要 URL 编码，可原样进 CEL 字符串与 cookie 值。 (+6 more)

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
Nodes (44): Archify Diagram Viewer Preset (classic, showcase quality), 五层全景图, 一次 run 的生命周期图, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Env Inheritance Diagram (+36 more)

### Community 176 - "Context Glossary Guards"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 177 - "main"
Cohesion: 0.20
Nodes (12): aggregate(), artifactFlushRoot(), drainArtifactQueue(), interruptSnapshot(), log(), main(), makeGuardedCleanup(), minGraceSeconds() (+4 more)

### Community 178 - "Graceful Stop Contract"
Cohesion: 0.33
Nodes (6): act 有界返回（per-act timeout）, 引擎经 --capabilities 自报 min_grace_s, FargateWorkerHandle.stop → StopTask, grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, 机制层：Engine adapter / WorkerHandle 把停翻成机制

### Community 179 - "Worker Termination Contract"
Cohesion: 0.33
Nodes (6): 事件流结束信号 / 存活判定迁移, exitCode 落值延迟与 MISSING 第三态, 未来演进：显式 core→worker 控制通道, Midscene worker 有序显式 cleanup handler, 逻辑层：schedule 经 worker 句柄请求停（handle.stop）, 终止契约（core 请求 worker 优雅停止）

### Community 180 - "Package URL Links"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 182 - "container_name"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 185 - "test_reconcile.py"
Cohesion: 0.09
Nodes (36): event_log adapters (sqlite / ddb), EventLog, Launcher, Job, Protocol, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 本机后端下起 subprocess worker（事件旁路落 SQLite EventLog…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034… (+28 more)

### Community 186 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 188 - "_tagged_feature"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 189 - "devDependencies"
Cohesion: 0.29
Nodes (7): @aws-sdk/client-device-farm, devDependencies, @aws-sdk/client-device-farm, @types/node, typescript, @types/node, typescript

### Community 190 - "移动真机支持（1.5）：实施进度总纲"
Cohesion: 0.40
Nodes (4): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）, 实施期要核的点（ADR 已定、实施时顺手验证）, 现场, 移动真机支持（1.5）：实施进度总纲

### Community 191 - "stopTimeout=120 / grace 预算校准"
Cohesion: 0.18
Nodes (12): ACT_TIMEOUT_S=120 不压（否决解法 B）, 孤儿产物扫盘 reaper（经分析否决）, 关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）, stopTimeout=120 / grace 预算校准, IAM 最小权限（task role 动作×资源两维收窄）, job-in S3 对象按 tag 的 7 天 lifecycle, preflight fail-fast（探资源存在性、错误点名 prefix）, 产物前缀一致性探针（--report-dir vs Lambda REPORT_DIR） (+4 more)

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
Cohesion: 0.11
Nodes (39): 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的…, _assert_process_gone(), _engine(), _job(), _kill_quietly(), _mode_job(), 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, fail-fast 对多个仍在运行的真子进程：先全部落定再并行发停止请求。关掉心跳，victim 的线程阻塞在管道读上、看不到 abort_flag，… (+31 more)

### Community 197 - "_FakeResult"
Cohesion: 0.15
Nodes (5): _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。

### Community 201 - "移动真机支持（1.5）：实施批次的改动面与先写的护栏测试"
Cohesion: 0.18
Nodes (10): 0. B0-navigation：导航规则与注册面关键字声明（1.4 行为的不兼容变更，自己发）, 1. B1-capabilities：能力自述增键（两个 worker 只声明桌面网页；CLI 唯一校验处与交集；doctor、list-deterministic 呈现）, 2. B5-core-events-termination：core 侧会话事件、scope 级 error、合成 SKIPPED、终结函数与真值表、计量合计、explain 呈现, 3. B2-core-target-job：测试目标与 Job 形态（core 侧 tag 归约、target 两形态、按目标的 timeout、plan 标注与目标拒绝、两个 worker 建会话前自检）, 4. B3-config-submit：项目配置文件、组合根填 device_request、definition 格式版本、CLI 侧应用上传, 5. B4-steps-registry：确定性 step 多句柄注册（targets、requires、driver 代理的注册面）, 6. B7-tunnel：隧道改为令牌换 cookie（桌面先行）、桌面 worker 的预热失败出口、脱敏规则三条, 7. B8-deploy-iac：部署侧：权限、Device Farm 项目找回或建立、SSM、doctor 设备项 (+2 more)

### Community 202 - "_FakeEcs"
Cohesion: 0.17
Nodes (10): _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped() (+2 more)

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

### Community 210 - "_CdkWritingContext"
Cohesion: 0.10
Nodes (15): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。 (+7 more)

### Community 211 - ".peek_definition_header"
Cohesion: 0.50
Nodes (3): 只取 META item 顶层的结构版本与写端 CLI 版本（ADR 0037 决策 7）；item 不存在返回 None，没有该属性读作 0。…, META 顶层的 schema_version 属性 → 整数：缺读作 0（早于结构版本号的写端）；DDB 把数值还成 Decimal，须为整数值； bool…, _schema_version_attr()

### Community 213 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 214 - "watch_run_and_stop_tunnel"
Cohesion: 0.18
Nodes (12): RunState, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道…, 把 compose._make_ddb_table 换成吐固定 RunState 序列的 fake（states 用尽后复用最后一个）。, _state() (+4 more)

### Community 223 - "precheck.mts"
Cohesion: 0.23
Nodes (12): DEVICE_LABEL, ADR-0024, ADR-0049, ADR-0051, precheckJob(), precheckSchema(), precheckTarget(), spaced() (+4 more)

### Community 228 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 249 - "deterministic.test.mts"
Cohesion: 0.33
Nodes (4): HANDLES_FIXTURE, META, ADR-0022, ADR-0050

### Community 251 - "TaskExited"
Cohesion: 0.33
Nodes (4): SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, 平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。 **不是 worker 的 wire 事件**（不在…, TaskExited

### Community 255 - "errors.py"
Cohesion: 0.12
Nodes (17): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, definition 的结构版本不是本读端认的那一个（ADR 0037 决策 7）。…, UnsupportedDefinitionSchema, WorkerExitError, WorkerNetworkError (+9 more)

### Community 256 - "test_stale_projection_never_regresses_terminal_job_on_real_ddb"
Cohesion: 0.32
Nodes (8): 真表上本次运行专属的 run_id，并登记自清理（多次执行不撞名、不留垃圾）。, 真 DDB 的机制四 CAS：两个推进器抢同一个 pending job，**恰一个**成功（另一个见条件失败）。 两个 store…, 真 DDB 的机制三②：终态 job 不被 stale 投影刷回 running——两道闸各验一遍。 - 同 HWM（task_exited 无数值…, _real_run_id(), _real_store(), test_claim_is_exclusive_on_real_ddb(), test_stale_projection_never_regresses_terminal_job_on_real_ddb(), integration

### Community 257 - "compose.py"
Cohesion: 0.04
Nodes (55): datetime, available_targets(), CloudTarget, _default_targets(), _find_worker_spec(), is_pure_release(), _make_lambda_client(), new_run_id() (+47 more)

### Community 261 - "NgrokTunnel"
Cohesion: 0.22
Nodes (9): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。, start：agent 命令带日志通道与流量策略文件；策略是四条规则的令牌换 cookie（不是 basic-auth）、文件 0600；预热地址带本次令牌；…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, test_ngrok_binary_missing_reports_install_hint(), test_ngrok_start_spawns_agent_with_policy_and_fresh_secrets() (+1 more)

### Community 264 - "test_lifecycle_states.py"
Cohesion: 0.10
Nodes (12): 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _Heartbeat, schedule 模块（ADR 0026）：Job[] → 并发运行 → 收流式事件 → RunResult。 job 间并行（maxConcurrency…, 存活心跳哨兵（schedule 私有，ADR 0028）：worker 活着但暂时没吐事件时，_heartbeat_wrap 注入它， 让 _run_once…, 内存假 Engine（测试夹具，ADR 0026「接口是测试面」）。 直接在进程内吐预设的 ADR 0024 事件流，不 spawn 子进程、不连…, job 生命周期态 + severity 单测（ADR 0031）：skipped/aborted/pending/running、severity…, test_pending_running_have_no_severity() (+4 more)

### Community 265 - "run-scope.mts"
Cohesion: 0.06
Nodes (34): ADR-0014, ADR-0019, ADR-0020, ADR-0022, ADR-0026, ADR-0027, ADR-0029, ADR-0031 (+26 more)

### Community 268 - "fixture"
Cohesion: 0.25
Nodes (8): _reset_scope_colors(), _color_env_independent(), 本模块的颜色断言不受运行测试的 shell 影响：清掉 NO_COLOR / FORCE_COLOR / TERM=dumb，让「是否终端」成为唯一变量。, aws(), _aws_env(), _presentation_is_environment_independent(), 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, fixture

### Community 270 - "ssm_path"
Cohesion: 0.05
Nodes (44): _FakeTable, 假 DDB table 句柄：DynamoDBRunStore…, subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_security_groups_path(), ssm_subnets_path() (+36 more)

### Community 271 - "index.mts"
Cohesion: 0.40
Nodes (4): ADR-0022, ADR-0036, ADR-0037, ADR-0050

### Community 272 - "_documented_keys"
Cohesion: 0.33
Nodes (6): _documented_keys(), 契约页记载的字段名。取「字段表里（任一列）+『顶层…』/『每项…』散文里」的反引号 token， 再按键形状过滤——ADR…, skill 里形如 JSON 键的反引号 token 必须是契约页记载的键，否则显式登记成非键。 挡的是「把 `record_missing` 写成…, test_key_shaped_tokens_are_documented_keys(), collect(), main()

### Community 273 - "ensure_app_object"
Cohesion: 0.10
Nodes (32): app_object_key(), AppLocation, AppUploadError, ensure_app_object(), _error_code(), BaseException, datetime, Exception (+24 more)

### Community 282 - "ADR 0037: 分发与打包"
Cohesion: 0.14
Nodes (29): ADR 0005: 单一共享 feature 文件, ADR 0011: AgentCore 浏览器 system default vs custom, 系统默认浏览器 aws.browser.v1, 自建 custom browser（create-browser）, ADR 0015: v1 定位——柔性冒烟而非回归, 确定性 step（测试开发按需自建）, tunnel.py（--expose-local 隧道 provider）, tunnel_host.py（隧道宿主编排 + 守护 TTL） (+21 more)

### Community 293 - "SqliteEventLog"
Cohesion: 0.09
Nodes (24): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, SqliteEventLog (+16 more)

### Community 294 - "plan_next"
Cohesion: 0.40
Nodes (5): Action, plan_next(), RunState, reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…

### Community 295 - "ADR 0023: Nova Act acting 锁 Python"
Cohesion: 0.32
Nodes (8): 双语言裂缝（物理约束）, ADR 0006: 形态 A——两个子工程、无编排器, 薄 worker 子进程（一次调用=一个 scope=一个 job）, 两个引擎都作为子进程 worker、核心语言自由选 Python, Nova Act REST API = 客户端驱动的工具调用循环, ADR 0023: Nova Act acting 锁 Python, Python nova-act SDK 的 Playwright/CDP 客户端循环, 全 TS 核心路径（被证伪关闭）

### Community 296 - "RuntimeError"
Cohesion: 0.33
Nodes (7): _error_text(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…, 隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。, test_error_text_prefers_sdk_message_and_is_single_line(), test_error_text_redacts_before_truncation(), RuntimeError

### Community 298 - "Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障"
Cohesion: 0.33
Nodes (6): 1. 链路一句话, 2. 签名契约：五条决定成败的细节, 3. 失败模式表, 4. 依赖与自检, Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障, 延伸阅读

### Community 299 - "cli/tests/conftest.py"
Cohesion: 0.40
Nodes (5): _presentation_is_environment_independent(), fixture, cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities()

### Community 300 - "ADR 0024: worker–core 协议"
Cohesion: 0.06
Nodes (64): cli/DEVELOPMENT.md, CONTRIBUTING（contributor 入口）, core 包 contributor 文档, core 测试说明（单测 + 集成测试）, gherkai-deploy-aws contributor 手册, ADR 0016: 执行架构 — 核心库与 run 模型, AgentCore Evaluations（去优先级的相邻选项）, ADR 0017: 云端执行选 Fargate (+56 more)

### Community 301 - "test_run_and_submit_exit_2_before_spawn_when_user_steps_fail"
Cohesion: 0.33
Nodes (6): _fake_worker_cmd(), steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：运行前先问一次能力自述，worker 非零退出 → 起任何 job 之前以退出码 2 结束（不进 job 级 error）。…, _steps_dir_with_file(), test_plan_exits_2_when_user_steps_fail_to_load(), test_run_and_submit_exit_2_before_spawn_when_user_steps_fail()

### Community 302 - "exceptions"
Cohesion: 0.50
Nodes (4): ConflictException, exceptions, Exception, ResourceNotFoundException

### Community 305 - "_cmd_list_engines"
Cohesion: 0.50
Nodes (4): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…

### Community 307 - "._installed_import_source"
Cohesion: 0.33
Nodes (4): 把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容是本包 `lambdas/` 的 handler…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it()

### Community 308 - "_FakeCdp"
Cohesion: 0.33
Nodes (3): _FakeCdp, main_fakes(), 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。

### Community 309 - "reconciler.py"
Cohesion: 0.07
Nodes (33): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+25 more)

### Community 314 - "finalize_job"
Cohesion: 0.13
Nodes (21): _aggregate(), finalize_job(), _job_status(), _lifecycle_rank(), Job, SessionRecord, Status, 终结函数的输出：job 的判定、归因与消息。 (+13 more)

### Community 316 - "projected_run_status"
Cohesion: 0.40
Nodes (5): projected_run_status(), 投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。…, 全 job pending → pending（run 还没起过任何 job）；任一 job 推进 → running；恒非终态（终态归 finalize）。, test_projected_run_status_pending_only_while_all_jobs_pending(), JobState

### Community 317 - ".__init__"
Cohesion: 0.40
Nodes (4): Job, EngineResolver, Lock, Sink

### Community 318 - "render_traffic_policy"
Cohesion: 0.33
Nodes (6): 本 run 的 ngrok 流量策略 YAML（ADR 0051 决策 13）：手写模板替换，不为此引 yaml 依赖——结构固定，令牌与 cookie…, render_traffic_policy(), ADR 0051 决策 13「边缘策略」：恰 4 条规则（免费层上限 5）、不含 basic-auth 与 remove-headers、Set-Cookie…, ngrok 读的是解析后的结构、不是字面量，所以按 YAML 解析后核：四条规则按序 warmup-ok / warmup-reject / check-ok…, test_traffic_policy_has_four_rules_cookie_spec_and_markers(), test_traffic_policy_parses_as_yaml_with_rule_order_statuses_and_gate_semantics()

### Community 321 - "gherkai：价值与方法（材料索引）"
Cohesion: 0.60
Nodes (5): 演示材料索引, 价值与方法 视频章节, 价值与方法 纯口播稿, gherkai：价值与方法（材料索引）, 价值与方法 讲者备注

### Community 329 - "Fargate/ECS RunTask 执行后端"
Cohesion: 0.50
Nodes (4): AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务

### Community 330 - "severity 数值序（_STATUS_SEVERITY）"
Cohesion: 0.38
Nodes (7): 退出码基于 run 级 severity, _NON_VERDICT 与 _aggregate 入口过滤, severity 数值序（_STATUS_SEVERITY）, Status.ABORTED（core 派生态）, Status.PENDING / RUNNING（生命周期前置态）, Status.SKIPPED（core 派生态）, TERMINAL_STATUSES（终态真源，取补定义）

### Community 331 - "url_matches.py"
Cohesion: 0.50
Nodes (3): deterministic, 示范用确定性 step（Nova Act 侧）：断言当前页面地址匹配给定正则。 这是 `steps/` 目录的模板：复制进你的项目后按需改措辞与判定。与…, url_matches()

### Community 332 - "replace_origin"
Cohesion: 0.50
Nodes (4): 把文本里每个「作为一个地址出现」的 origin 换成 base：origin 之后的 URL 字符段 R 为空、以 / ? #…, replace_origin(), parametrize, test_replace_origin_boundaries()

### Community 334 - "runStep"
Cohesion: 0.50
Nodes (5): appendReportRef(), cumulativeTokens(), isTransientNetwork(), runStep(), stepCost()

### Community 337 - "PlanConfig"
Cohesion: 0.67
Nodes (3): PlanConfig, PlanConfig 自带的设备缺省与下限按内建获取预算 600 推出（加 900 / 加 180，ADR 0051 决策 2）；桌面缺省 300。, test_plan_config_defaults_derive_from_builtin_acquire_budget()

### Community 338 - "_joined_refs"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 339 - "_explain_emit"
Cohesion: 0.13
Nodes (18): _cloud_skew_gate(), _cmd_explain(), _definition_header_gate(), _explain_cloud(), _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches() (+10 more)

### Community 343 - "settings.py"
Cohesion: 0.14
Nodes (22): apply_project_config(), configurable_keys(), convert_config_value(), find_option_action(), _is_repeatable(), option_actions(), option_origin(), ArgumentParser (+14 more)

### Community 348 - "unspecified_message"
Cohesion: 0.40
Nodes (5): platform_label(), ADR 0053 决策 4 的用户可见消息：有该平台的设备 scope，却没有任何来源指定设备。, unspecified_message(), run / submit：有设备 scope 的平台没有任何来源指定设备，在提交前以退出码 2 结束（ADR 0053 决策 4「不自动挑设备」）。, require_device_selections()

### Community 352 - "gherkai_cli/__main__.py"
Cohesion: 0.10
Nodes (28): ArgumentParser, _add_config_flag(), _add_device_flags(), _add_selection_flags(), _build_parser(), _build_selector(), _cmd_tunnel_watch(), _dist_version() (+20 more)

### Community 368 - "_cmd_deploy"
Cohesion: 0.33
Nodes (6): _cmd_deploy(), _cmd_destroy(), _deploy_provider(), 取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…, [部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。前端零 IaC 知识。 退出码即 provider…, [部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。

### Community 375 - "_DeterministicCtx"
Cohesion: 0.33
Nodes (3): _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）与导航原语…, 引擎的导航原语（内建导航条目用它打开地址，ADR 0020 第 3 条）：Nova 用 SDK 的 `go_to_url`。

### Community 392 - "_out"
Cohesion: 0.11
Nodes (24): list_workers(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…, _out(), --json 下 stdout 只留一个 JSON 文档：skew 提示 / 读失败诊断走 err（stderr），文本输出行为不变。, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。, dev 版（`.dev`/`.post`/本地段）**GHCR 上不存在对应基础镜像** → 明确警告 + 跳过基础镜像同步，第 3/4 步照常执行。… (+16 more)

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
- **683 isolated node(s):** `StepArgument`, `Row`, `Job`, `JobApp`, `JobDeviceRequest` (+678 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **167 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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