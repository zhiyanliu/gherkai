# Graph Report - yaozhou  (2026-10-26)

## Corpus Check
- 362 files · ~583,862 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5967 nodes · 13250 edges · 264 communities (217 shown, 47 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 768 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `42ba21fc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- evidence.py
- test_backend_cloud.py
- test_main.py
- gherkai_runtime/names.py
- Job
- Provider
- test_schedule.py
- test_project.py
- test_workers.py
- test_plan.py
- workers.py
- gherkai_cli/__main__.py
- FeatureSource
- _run_step
- check_version_skew
- main
- test_stack.py
- test_evidence.py
- test_deploy_cmd.py
- test_container.py
- resolve_worker_cmd
- materialize.py
- test_compose.py
- test_reconcile.py
- JobState
- ensure_workflow_definition
- parse.py
- build_cloud_stores
- test_conditional_writes.py
- ADR 0043：驱动 gherkai 的 agent skill
- _stream_record
- test_cloud_reconcile.py
- _RecUploader
- ._run_cdk
- test_worker_variant.py
- query_capabilities
- core/tests/conftest.py
- test_tunnel_cli.py
- 执行与推进模型导览（run/submit × local/cloud）
- gherkai agent skill 主文
- render.py
- atomic_write_json
- cli.py
- test_event_sink.py
- schedule(run_meta, engines, sink, opts)
- _run_with_refs
- 云端后端用户文档
- _StubEcs
- video.py
- reconciler.py
- core 包 contributor 文档
- _FakeResult
- test_user_docs.py
- redact_url_userinfo
- ./run-scope.mjs
- test_interrupt_model.py
- S3ResultStore
- use_color
- BackendStack
- test_report_still_written_when_the_run_duration_read_fails
- LocalReportStore
- minimax_narration.py
- test_fargate_engine.py
- ../lib/agentcore-sigv4.mjs
- Video Material Manifest
- evidence.mts
- Artifact Upload Tests
- _doc_rules.py
- _is_transient_network
- textui.py
- _cmd_doctor
- _explain_run
- _fake_locator
- _FakeEcs
- 06-devicefarm-appium.mts
- gherkai 变更记录 (CHANGELOG)
- run_reconcile_loop
- Artifact Uploader
- arg_offload.py
- _mk_state
- Status
- ADR 0014: AI 优先断言
- user-steps.mts
- test_user_steps.py
- event-sink.mts
- FargateEngine
- test_cli_json_contract.py
- 决策
- test_argument.py
- README Video Specs
- TypeScript Build Config
- stopTimeout=120 / grace 预算校准
- test_lambda_asset.py
- Composition Root Architecture
- test_sqlite_event_log.py
- test_adr_hygiene.py
- test_list_workers_reports_unreachable_aws_without_a_traceback
- Video Material Files
- report_store/local.py
- deterministic
- test_tunnel_host.py
- skill_install.py
- 决策
- Run Store Persistence Ports
- RunPersistence
- _argv
- 决策
- 决策
- CONTRIBUTING.md: contributor 指南
- scope.py
- dependencies
- JobSource
- SqliteEventLog
- Diagram Build Script
- ArtifactUploader
- app.py
- evidence.test.mts
- _tagged_feature
- AppiumInterface
- _FakeTable
- _StampSsm
- Event Wallclock Analysis
- Release Notes Guards
- detached.py
- test_skill.py
- .add_arguments
- run-scope.test.mts
- Dist Metadata Checks
- run_scope.py
- Package README Guards
- _events_table_actions
- Media Conversion Verification
- package.json
- ValueError
- e2e_harness.py
- warmupProbe
- errText
- DynamoDB Events Transport ADR
- _StopTimeoutEcs
- 决策
- wire.py
- ADR 0016: 执行架构 — 核心库与 run 模型
- test_skill_deploy_tokens.py
- reconcile.tick（推进器共享入口）
- Stateless Run Core Model
- ._installed_import_source
- argument.mts
- User-Facing Text Guards
- SubprocessLauncher
- _CdkWritingContext
- 0050. 确定性 step 多句柄注册与测试分层
- _ClientError
- _Recorder
- artifact-upload.test.mts
- cli 包 contributor 文档
- Worker Signal Interrupt Tests
- _FakeSink
- ADR 0043: 随 CLI 发行的 agent skill
- .preflight
- ECS Task Timing Capture
- build_engines
- Artifact Uploader Component
- gemini_image.py
- Graphify Refresh Script
- stop_tunnel
- job-source.mts
- _DeterministicCtx
- Cooperative Stop Design
- _FakeSink
- Doc Rules Check
- cli/tests/conftest.py
- openai
- redact.mts
- Engine Port & Job Planning
- Scope Tag Parsing
- patch-package 补丁 @cucumber+cucumber+13.0.0
- Context Glossary Guards
- _frontmatter_and_body
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- ADR 0024: worker–core 协议
- _fixture
- Fargate/ECS RunTask 执行后端
- @playwright/test
- _error_text
- Echo Test Worker
- Cloud Infra Self-Check
- _patch_skew
- devDependencies
- 移动真机支持（1.5）：实施进度总纲
- test_tunnel.py
- Worker Image Param Mapping
- Gherkin Parse Seam
- files
- Repository Metadata
- Nova Artifact Upload
- Upload Call Recorder
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试
- _color_env_independent
- Architecture Diagrams
- Slide Frame SSIM Checks
- AI step（默认执行路径）
- AgentCore CDP Script
- .feature (Gherkin 用例)
- Background Upload Queue
- Pre-commit Hook Script
- _seed_run
- tunnel.py
- Adapters Package
- user-steps.test.mts
- _cmd_deploy
- summarize_runs.py
- Step Matching & Plan Annotation
- 01-model-sigv4.ts
- agentcore-sigv4.test.mts
- Upload Queue Drain
- Uploader Enabled Check
- Fail-Loud Config Validation
- No-op Local Uploader
- test_detached_launcher.py
- _runs_stream_record
- Index Wait Script
- gherkai Workspace Root
- gherkai：价值与方法（材料索引）
- error-text.mts
- Execution Backend
- Feature Files
- Error Type Classification
- Local Per-Run Advance Process
- ADR 0013: 跨引擎共享边界
- gherkai Core Package
- AWS Deploy Package
- Runtime Package
- NovaAct Worker Package
- _AbsentEngine
- event-sink.test.mts
- cloud_env
- job-source.test.mts
- redact.test.mts
- @midscene/web
- test_worker_subnets_single_source_across_ssm_and_lambda_env
- NgrokTunnel
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- _FakeS3
- test_real_output_has_is_return_false_everywhere_so_we_map_by_name
- BaseException
- RuntimeError
- compose.py
- test_tick_runs_isolates_defensive_scan_failure
- test_provider_module_does_not_import_aws_cdk
- test_lambda_handlers.py
- ./deterministic.mjs
- gherkai_runtime/__init__.py
- EventBridgeTimeoutWatch
- ./deterministic.steps.mjs

## God Nodes (most connected - your core abstractions)
1. `main()` - 217 edges
2. `Job` - 135 edges
3. `RunState` - 127 edges
4. `RunMeta` - 120 edges
5. `Status` - 106 edges
6. `JobState` - 101 edges
7. `Provider` - 100 edges
8. `JobResult` - 84 edges
9. `Scenario` - 73 edges
10. `Step` - 72 edges

## Surprising Connections (you probably didn't know these)
- `--interrupt 中断时机矩阵` --shares_data_with--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `e2e_harness.py（opt-in 手动端到端验证脚本）` --calls--> `plan()`  [EXTRACTED]
  tools/e2e_harness.md → core/gherkai_core/scope.py
- `e2e_harness.py（opt-in 手动端到端验证脚本）` --calls--> `resolve_worker_cmd()`  [EXTRACTED]
  tools/e2e_harness.md → runtime/gherkai_runtime/compose.py
- `render()` --references--> `docs/internals/cli-json-contract.md（机读字段级参考页）`  [EXTRACTED]
  tools/render_skill_contract.py → docs/adr/0045-documentation-layering-and-placement.md
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

## Communities (264 total, 47 thin omitted)

### Community 0 - "evidence.py"
Cohesion: 0.07
Nodes (47): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Any, Path (+39 more)

### Community 1 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 2 - "test_main.py"
Cohesion: 0.04
Nodes (87): _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：运行前先问一次能力自述，worker 非零退出 → 起任何 job 之前以退出码 2 结束（不进 job 级 error）。… (+79 more)

### Community 3 - "gherkai_runtime/names.py"
Cohesion: 0.08
Nodes (32): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_worker_template_path(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的… (+24 more)

### Community 4 - "Job"
Cohesion: 0.04
Nodes (122): RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, render_text(), _explain_cloud_stores(), _explain_job(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的… (+114 more)

### Community 5 - "Provider"
Cohesion: 0.06
Nodes (74): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 留的口子（ADR 0038「命令族」）：**尚未提供**，以退出码 2 结束并说清为什么与将来怎么落。…, _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, flag 面全集锁定（枚举型护栏）：三个 context 配置项 flag + AWS 定位二件套 + 两个「前端的中立版的 AWS 精确化」（见 cli…, `--allow-vpc-change` / `--require-approval` **只贴 deploy**（枚举型全集比对，同上条口径）。… (+66 more)

### Community 6 - "test_schedule.py"
Cohesion: 0.05
Nodes (131): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), _pump_log(), scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+123 more)

### Community 7 - "test_project.py"
Cohesion: 0.05
Nodes (106): SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, 单个 step 的归约结果（core 保留 step 级粒度，ADR 0024）。 duration_ms 是 step 墙钟时长（core 用…, ScenarioResult, ScopeDone, ScopeStarted, StepResult, StepStarted (+98 more)

### Community 8 - "test_workers.py"
Cohesion: 0.06
Nodes (89): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地… (+81 more)

### Community 9 - "test_plan.py"
Cohesion: 0.12
Nodes (30): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否…, @scope 的值等于某条**自身已标 @scope** 的 scenario 的 id → 不报错：那条 id 根本没当分组键，不会撞。, 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ FeatureContractError（ADR 0025：标了…, test_assertion_votes_default_is_one() (+22 more)

### Community 10 - "workers.py"
Cohesion: 0.04
Nodes (97): Aws, cleanup_pass(), CleanupOutcome, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+89 more)

### Community 11 - "gherkai_cli/__main__.py"
Cohesion: 0.04
Nodes (85): _add_selection_flags(), _build_parser(), _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_explain(), _cmd_list_deterministic() (+77 more)

### Community 12 - "FeatureSource"
Cohesion: 0.18
Nodes (19): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只执行 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次运行哪几条。… (+11 more)

### Community 13 - "_run_step"
Cohesion: 0.08
Nodes (54): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+46 more)

### Community 14 - "check_version_skew"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 15 - "main"
Cohesion: 0.05
Nodes (60): main(), _det_feature(), 两个非 job 入口同样加载 steps 目录（ADR 0037 决策 4）→ plan 标注与 list-deterministic 清单反映定制 step。, 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。 (+52 more)

### Community 16 - "test_stack.py"
Cohesion: 0.06
Nodes (60): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。 (+52 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.09
Nodes (42): _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), list, parametrize, Path, step 级机读证据（evidence，ADR 0042 决策一/二/六）单测：映射 / 截图上界 / 目录键 / best-effort 钩子。 纯… (+34 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 19 - "test_container.py"
Cohesion: 0.04
Nodes (58): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+50 more)

### Community 20 - "resolve_worker_cmd"
Cohesion: 0.09
Nodes (23): _find_worker_spec(), 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。, resolve_worker_cmd(), _runtime_version(), 四级全 miss → WorkerNotFoundError 带引擎名 + 该引擎的安装指引 + env 覆写指引（退出码交调用点）。, 第一级 env 覆写最高优先（shlex 拆分）+ 可选配套 _CWD：contributor 指向 repo 内源码/自建 worker 走这里。 (+15 more)

### Community 21 - "materialize.py"
Cohesion: 0.09
Nodes (47): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+39 more)

### Community 22 - "test_compose.py"
Cohesion: 0.06
Nodes (57): preflight_cloud_resources(), prune_empty_dirs(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`…, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK… (+49 more)

### Community 23 - "test_reconcile.py"
Cohesion: 0.08
Nodes (38): ReportStore adapters (local / s3), finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher (+30 more)

### Community 24 - "JobState"
Cohesion: 0.04
Nodes (101): run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, test_render_status_pending_run_with_claimed_job_does_not_hint(), 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, ResultStore adapters (local / s3), LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, RunStore adapters (local / ddb), _job_state_to_item() (+93 more)

### Community 25 - "ensure_workflow_definition"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 26 - "parse.py"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 27 - "build_cloud_stores"
Cohesion: 0.09
Nodes (24): build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), 云端后端一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。 (+16 more)

### Community 28 - "test_conditional_writes.py"
Cohesion: 0.07
Nodes (50): _initial(), _meta(), RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+42 more)

### Community 29 - "ADR 0043：驱动 gherkai 的 agent skill"
Cohesion: 0.08
Nodes (48): _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏）, test_user_docs.py（用户文档与图源护栏）, ADR 0001：范围限定英文 UI, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0041：面向 agent 的 CLI 可操作面, ADR 0043：驱动 gherkai 的 agent skill (+40 more)

### Community 30 - "_stream_record"
Cohesion: 0.09
Nodes (24): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。, 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍… (+16 more)

### Community 31 - "test_cloud_reconcile.py"
Cohesion: 0.05
Nodes (55): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog (+47 more)

### Community 32 - "_RecUploader"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。 (+10 more)

### Community 33 - "._run_cdk"
Cohesion: 0.07
Nodes (21): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), Path, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。… (+13 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (46): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, worker_image_key(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。 (+38 more)

### Community 35 - "query_capabilities"
Cohesion: 0.05
Nodes (53): _ask_worker(), build_local_stores(), engine_min_grace(), local_artifact_locations(), match_deterministic(), Path, RuntimeError, query_capabilities() (+45 more)

### Community 36 - "core/tests/conftest.py"
Cohesion: 0.11
Nodes (17): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。 (+9 more)

### Community 37 - "test_tunnel_cli.py"
Cohesion: 0.08
Nodes (42): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。 (+34 more)

### Community 38 - "执行与推进模型导览（run/submit × local/cloud）"
Cohesion: 0.08
Nodes (44): Archify Diagram Viewer Preset (classic, showcase quality), 五层全景图, 一次 run 的生命周期图, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Env Inheritance Diagram (+36 more)

### Community 39 - "gherkai agent skill 主文"
Cohesion: 0.13
Nodes (20): skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法, skill 参考：引擎选择与确定性 step 模板, skill 参考：环境就位与排障, gherkai agent skill 主文, 评测 fixture：隧道地址不匹配场景, AI 断言 (AI assertion), 基础镜像 / variant / 默认指针 (+12 more)

### Community 40 - "render.py"
Cohesion: 0.08
Nodes (40): _add_act(), _add_step(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), explain_tree() (+32 more)

### Community 41 - "atomic_write_json"
Cohesion: 0.14
Nodes (19): atomic_write_json(), atomic_write_text(), Path, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://…, _page() (+11 more)

### Community 42 - "cli.py"
Cohesion: 0.05
Nodes (45): cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client() (+37 more)

### Community 43 - "test_event_sink.py"
Cohesion: 0.06
Nodes (21): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, redact_url_userinfo() (+13 more)

### Community 44 - "schedule(run_meta, engines, sink, opts)"
Cohesion: 0.06
Nodes (42): 墙钟时长归约（step/scenario/scope/run duration_ms）, EngineResolver（按 job.engine 解析 Engine）, 失败隔离 / failFast 旋钮, 优雅终止：schedule 只调 handle.stop(grace), _heartbeat_wrap（静默 worker 心跳注入）, per-job 墙钟预算 Job.timeout_s 超时兜底, maxConcurrency 并发上限（默认 4）, job 级网络瞬时故障重试（network_retry） (+34 more)

### Community 45 - "_run_with_refs"
Cohesion: 0.18
Nodes (16): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest() (+8 more)

### Community 46 - "云端后端用户文档"
Cohesion: 0.11
Nodes (36): gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce）, kicker Lambda（冷启动器）, reconciler Lambda（主推进器） (+28 more)

### Community 47 - "_StubEcs"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 48 - "video.py"
Cohesion: 0.32
Nodes (17): cues(), digest(), link_chapter_title_track(), packets(), probe(), protected_state(), Path, Confirm the first slide at frame zero, hard cuts, and the closing fade. (+9 more)

### Community 49 - "reconciler.py"
Cohesion: 0.09
Nodes (33): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+25 more)

### Community 50 - "core 包 contributor 文档"
Cohesion: 0.15
Nodes (19): cli/DEVELOPMENT.md, core 包 contributor 文档, core 测试说明（单测 + 集成测试）, 输出契约：流式 JSON Lines 事件流, reportRefs 不透明产物引用, status 三态 passed/failed/error（wire 只传三态）, step_skipped 独立事件（scope 内短路）, 三通道分离传输（EVENTS_FD / stdout / stderr） (+11 more)

### Community 51 - "_FakeResult"
Cohesion: 0.12
Nodes (8): _ActBoom, _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 Nova SDK 的 act 异常：与成功结果一样带 metadata（time_worked_s 已真实计费、trajectory 已写盘）。, RuntimeError

### Community 52 - "test_user_docs.py"
Cohesion: 0.09
Nodes (38): changelog_unreleased(), prose_lines(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _default_model_claims(), _default_model_ids(), parametrize, Path (+30 more)

### Community 53 - "redact_url_userinfo"
Cohesion: 0.13
Nodes (18): explain_to_dict(), 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, Any, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_url_userinfo() (+10 more)

### Community 54 - "./run-scope.mjs"
Cohesion: 0.05
Nodes (51): ADR-0019, ADR-0022, ADR-0026, ADR-0027, ADR-0032, ADR-0035, ADR-0039, ADR-0050 (+43 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.09
Nodes (29): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, _FakeResult (+21 more)

### Community 56 - "S3ResultStore"
Cohesion: 0.16
Nodes (9): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore, 配好的 S3ResultStore（注入 aws fixture 建好的桶），供 ResultStore 对拍测试。 (+1 more)

### Community 57 - "use_color"
Cohesion: 0.18
Nodes (16): 执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。, color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env() (+8 more)

### Community 58 - "BackendStack"
Cohesion: 0.09
Nodes (19): Cluster, Construct, BackendStack, BackendStack._build_lambda_asset, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。 (+11 more)

### Community 59 - "test_report_still_written_when_the_run_duration_read_fails"
Cohesion: 0.14
Nodes (16): now_iso(), parse_iso(), datetime, detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的… (+8 more)

### Community 60 - "LocalReportStore"
Cohesion: 0.18
Nodes (35): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077… (+27 more)

### Community 61 - "minimax_narration.py"
Cohesion: 0.26
Nodes (10): APIError, download_subtitles(), main(), NoRedirect, page_numbers(), post(), Exception, Path (+2 more)

### Community 62 - "test_fargate_engine.py"
Cohesion: 0.05
Nodes (78): _await_engine(), _delayed_stopped_ecs(), _engine(), _engine_with_fake_ecs(), _ev_item(), _gap_engine(), _job(), _put_event() (+70 more)

### Community 63 - "../lib/agentcore-sigv4.mjs"
Cohesion: 0.07
Nodes (29): ADR-0008, ADR-0010, BASE_URL, main(), MODEL_CONFIG, REGION, ADR-0033, BASE_URL (+21 more)

### Community 64 - "Video Material Manifest"
Cohesion: 0.06
Nodes (33): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+25 more)

### Community 65 - "evidence.mts"
Cohesion: 0.09
Nodes (30): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+22 more)

### Community 66 - "Artifact Upload Tests"
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

### Community 70 - "_cmd_doctor"
Cohesion: 0.11
Nodes (21): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+13 more)

### Community 71 - "_explain_run"
Cohesion: 0.10
Nodes (31): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+23 more)

### Community 72 - "_fake_locator"
Cohesion: 0.08
Nodes (38): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+30 more)

### Community 73 - "_FakeEcs"
Cohesion: 0.08
Nodes (22): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的…, n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。, 仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。 ECS… (+14 more)

### Community 74 - "06-devicefarm-appium.mts"
Cohesion: 0.14
Nodes (37): amapSteps(), androidAppTypingProbe(), appSteps(), capProbe(), caps(), connect(), df, Driver (+29 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.19
Nodes (15): gherkai 变更记录 (CHANGELOG), gherkai destroy, --expose-local 隧道模式, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, rich 渲染的人读输出 (+7 more)

### Community 76 - "run_reconcile_loop"
Cohesion: 0.20
Nodes (16): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _now(), 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…, 真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。, max_concurrency=1：两 job 串行推进、都 passed。验 loop 起完一个再起下一个。 (+8 more)

### Community 77 - "Artifact Uploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 78 - "arg_offload.py"
Cohesion: 0.14
Nodes (9): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。… (+1 more)

### Community 79 - "_mk_state"
Cohesion: 0.20
Nodes (14): _args(), _mk_state(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。 (+6 more)

### Community 80 - "Status"
Cohesion: 0.03
Nodes (80): event_log adapters (sqlite / ddb), 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, _job_state_from_item(), commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 状态机单调条件写：仅当总 status 是 pending 或 running 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。… (+72 more)

### Community 81 - "ADR 0014: AI 优先断言"
Cohesion: 0.06
Nodes (54): CLAUDE.md（项目约定）, CONTEXT.md（领域概念与术语）, CONTRIBUTING（contributor 入口）, ADR 0001: 范围限于英文 UI, 概念：Nova Act 中文词语级文本匹配短板, ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码, 概念：Midscene 仅走 chat-completions 接口 (+46 more)

### Community 82 - "user-steps.mts"
Cohesion: 0.11
Nodes (15): 确定性 step 加载失败即拒绝运行, fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037, ADR-0037, collectStepFiles() (+7 more)

### Community 83 - "test_user_steps.py"
Cohesion: 0.07
Nodes (47): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+39 more)

### Community 84 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd()

### Community 85 - "FargateEngine"
Cohesion: 0.06
Nodes (28): FargateEngine, FargateWorkerHandle, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称… (+20 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.15
Nodes (21): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…, _assert_documented(), _documented_keys(), _leaf_keys(), _mk() (+13 more)

### Community 87 - "决策"
Cohesion: 0.10
Nodes (20): 0051. 设备会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034 (+12 more)

### Community 88 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 91 - "stopTimeout=120 / grace 预算校准"
Cohesion: 0.15
Nodes (14): ACT_TIMEOUT_S=120 不压（否决解法 B）, 中断产物丢失风险（容器盘停即销毁）, 孤儿产物扫盘 reaper（经分析否决）, 安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底, 关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）, stopTimeout=120 / grace 预算校准, IAM 最小权限（task role 动作×资源两维收窄）, job-in S3 对象按 tag 的 7 天 lifecycle (+6 more)

### Community 92 - "test_lambda_asset.py"
Cohesion: 0.14
Nodes (21): make_stack(), **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path, Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。…, 没有命令给的工作目录（直接运行 cdk synth）→ 自建 mkdtemp，仍不写仓库。 (+13 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_sqlite_event_log.py"
Cohesion: 0.20
Nodes (14): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。, test_append_and_read_back_events() (+6 more)

### Community 95 - "test_adr_hygiene.py"
Cohesion: 0.19
Nodes (18): _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。, Status 头里点名的取代方编号（只看 superseded-by 之后、到第一个注解分隔符为止那一段）。, 被取代方点了谁，谁就得回指它——机械差集，不靠读。 (+10 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "report_store/local.py"
Cohesion: 0.12
Nodes (18): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+10 more)

### Community 99 - "deterministic"
Cohesion: 0.06
Nodes (51): clear(), deterministic(), DeterministicConflict, DeterministicKeywordMismatch, _Entry, _hits(), list_registry(), match() (+43 more)

### Community 100 - "test_tunnel_host.py"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 101 - "skill_install.py"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 102 - "决策"
Cohesion: 0.13
Nodes (15): 0048. 测试目标：设备与界面类型两个维度、`@device` 与 `@app` 标签、core 的执行前预检, 1. 测试目标由三个正交维度描述：engine、device、ui_kind, 2. 两个 scope 级 tag：`@device` 与 `@app`, 3. core 的三处改动, 4. 目标不受支持时的拒绝：由能力自述决定，消息给出改法, 5. plan 的标注, 6. 运行期网页上下文不可用：声明了前提的确定性 step 记 error，不转 AI, 7. 应用目标上的导航 step 与落点核对规则 (+7 more)

### Community 103 - "Run Store Persistence Ports"
Cohesion: 0.14
Nodes (20): Commit-point Write Order (data plane first), RunStore.create_run(), DDB Single-Table Schema (run_id + item_type), DynamoDBRunStore, Cloud Failure Exit Code Layering, RunStore.finalize_run(), RunState high_water_mark Conditional Write, JobSink Port (+12 more)

### Community 104 - "RunPersistence"
Cohesion: 0.11
Nodes (30): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run 就是 commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。 满足 ADR… (+22 more)

### Community 105 - "_argv"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，…, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 106 - "决策"
Cohesion: 0.13
Nodes (15): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 不升 schema 版本，在 schema 1 上增键, 2. 缺键语义：缺 `targets` 即「只有 desktop / web」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端 worker 在建会话前按自己的 `targets` 自检 (+7 more)

### Community 107 - "决策"
Cohesion: 0.13
Nodes (15): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 7. Midscene 复用边界 (+7 more)

### Community 108 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.18
Nodes (16): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, CONTEXT.md: 领域术语表, 护栏 (guardrail), 版本真源 (single version source), CONTRIBUTING.md: contributor 指南 (+8 more)

### Community 109 - "scope.py"
Cohesion: 0.23
Nodes (14): FeatureContractError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, 用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope… (+6 more)

### Community 110 - "dependencies"
Cohesion: 0.11
Nodes (19): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/client-dynamodb, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies (+11 more)

### Community 111 - "JobSource"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 112 - "SqliteEventLog"
Cohesion: 0.16
Nodes (10): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, SqliteEventLog (+2 more)

### Community 113 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 114 - "ArtifactUploader"
Cohesion: 0.11
Nodes (12): ../lib/artifact-upload.mjs, ArtifactUploader, CONTENT_TYPES, contentTypeFor(), ADR-0016, ADR-0024, ADR-0028, ADR-0029 (+4 more)

### Community 115 - "app.py"
Cohesion: 0.29
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 116 - "evidence.test.mts"
Cohesion: 0.14
Nodes (13): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, importRunScope(), ADR-0042 (+5 more)

### Community 117 - "_tagged_feature"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 120 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 121 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Release Notes Guards"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 123 - "detached.py"
Cohesion: 0.18
Nodes (11): cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。 (+3 more)

### Community 124 - "test_skill.py"
Cohesion: 0.06
Nodes (53): bare_flags(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags() (+45 more)

### Community 125 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 126 - "run-scope.test.mts"
Cohesion: 0.08
Nodes (15): _events, fakePage, gotoCalls, importMod(), ADR-0014, ADR-0020, ADR-0024, ADR-0028 (+7 more)

### Community 127 - "Dist Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 128 - "run_scope.py"
Cohesion: 0.06
Nodes (49): ActRecord, ArtifactUploader, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _attach_traj_refs(), _capabilities() (+41 more)

### Community 129 - "Package README Guards"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 130 - "_events_table_actions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 131 - "Media Conversion Verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 132 - "package.json"
Cohesion: 0.12
Nodes (16): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+8 more)

### Community 133 - "ValueError"
Cohesion: 0.22
Nodes (12): navigate(), deterministic, 内建导航（ADR 0020 第 3 条）：整句为地址的 Given / When step，直接打开，不走 AI。, main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section() (+4 more)

### Community 134 - "e2e_harness.py"
Cohesion: 0.19
Nodes (13): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, 继承一份 os.environ、抹掉组合根拥有的那些键（见 `_COMPOSE_OWNED_WORKER_ENV`）——所有注入 env 的起手式。…, scrubbed_environ(), --interrupt 中断时机矩阵, e2e_harness.py（opt-in 手动端到端验证脚本）, Path, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策… (+5 more)

### Community 135 - "warmupProbe"
Cohesion: 0.38
Nodes (9): navigateTo(), shot(), timeoutsProbe(), usableWebCtx(), warmupCore(), warmupProbe(), warmupUrl(), webCtxOf() (+1 more)

### Community 136 - "errText"
Cohesion: 0.56
Nodes (10): deeplinkCase(), deeplinkProbe(), deeplinkRound2(), deeplinkRound3(), deeplinkRound4(), errText(), foreground(), installApp() (+2 more)

### Community 137 - "DynamoDB Events Transport ADR"
Cohesion: 0.18
Nodes (13): DynamoDB 共享 events 表作 events-out 传输, EventSink（可注入事件出口）, events 表键设计 PK=run_id#scope_id, SK=seq, events item TTL 自动过期（7 天 expires_at）, 读一致性（流式期 EC 游标 + 终读强一致）, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列 (+5 more)

### Community 138 - "_StopTimeoutEcs"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 139 - "决策"
Cohesion: 0.17
Nodes (12): 0053. 项目配置文件 gherkai.toml, 1. 文件定位：只有运行侧 CLI 读它，读出的值解析成具体值随 Job 走, 2. 取值顺序：选项、环境变量、配置文件、内建默认依次优先, 3. 节与键, 4. 设备选择要求显式，筛选的挑选规则确定, 5. 与 ADR 0044 覆盖链的关系：worker 侧覆盖项不进配置文件, 6. 护栏, 决策 (+4 more)

### Community 140 - "wire.py"
Cohesion: 0.05
Nodes (60): _join_pumps(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。 (+52 more)

### Community 141 - "ADR 0016: 执行架构 — 核心库与 run 模型"
Cohesion: 0.09
Nodes (55): gherkai-deploy-aws contributor 手册, 概念：非英文应用用 @engine:midscene 路由, ADR 0011: AgentCore 浏览器 system default vs custom, 系统默认浏览器 aws.browser.v1, 自建 custom browser（create-browser）, ADR 0015: v1 定位——柔性冒烟而非回归, 确定性 step（测试开发按需自建）, 柔性冒烟定位（精确度光谱最左端） (+47 more)

### Community 142 - "test_skill_deploy_tokens.py"
Cohesion: 0.12
Nodes (18): clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, 一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。, _build() (+10 more)

### Community 143 - "reconcile.tick（推进器共享入口）"
Cohesion: 0.20
Nodes (11): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState）, status --wait 接力推进 (+3 more)

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "._installed_import_source"
Cohesion: 0.33
Nodes (4): 把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容是本包 `lambdas/` 的 handler…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it()

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "User-Facing Text Guards"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 148 - "SubprocessLauncher"
Cohesion: 0.22
Nodes (6): Event, Job, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, SubprocessLauncher, Timer

### Community 149 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.18
Nodes (11): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 2. handler 上下文：七个字段与一条不变量, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据 (+3 more)

### Community 151 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 152 - "_Recorder"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+3 more)

### Community 153 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 154 - "cli 包 contributor 文档"
Cohesion: 0.24
Nodes (10): cli 包 contributor 文档, skill 参考：CLI --json 字段契约, gherkai 命令行发行包入口页, agent skill (gherkai skill), 执行核心库窄腰 (core-library narrow waist), 派生视图 (derived view), 机读输出契约 (machine-readable output contract), Run 数据模型 (run data model) (+2 more)

### Community 155 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 156 - "_FakeSink"
Cohesion: 0.22
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。

### Community 157 - "ADR 0043: 随 CLI 发行的 agent skill"
Cohesion: 0.07
Nodes (35): gherkai agent skill 包, 隧道凭据脱敏（剥 URL userinfo）, URL 映射（job 组装时替换 origin 前缀）, worker --capabilities 自述入口, CLI list-deterministic --engine, 注册面元数据（description / example 必填）, CI 发布链与占名（tag 触发全链）, 版本 skew 检查（三态） (+27 more)

### Community 159 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 160 - "build_engines"
Cohesion: 0.08
Nodes (31): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, gherkai-runtime README (PyPI 入口页), Path (+23 more)

### Community 161 - "Artifact Uploader Component"
Cohesion: 0.23
Nodes (12): Act-Boundary Pre-upload, ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX Injection, Artifact Uploader Component, uploader.flush_and_cleanup(dir), Accepted Residual Un-uploaded Artifacts, Scenario-Boundary Log Pre-upload (Midscene only), Midscene uploader.snapshotLogs(logDir, seen, budgetMs), Midscene uploader.snapshotReport(path) (+4 more)

### Community 162 - "gemini_image.py"
Cohesion: 0.33
Nodes (4): HTTPRedirectHandler, NoRedirect, 演示制作规范, 演示制作与媒体工具说明

### Community 163 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 164 - "stop_tunnel"
Cohesion: 0.40
Nodes (5): 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 165 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 166 - "_DeterministicCtx"
Cohesion: 0.33
Nodes (3): _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）与导航原语…, 引擎的导航原语（内建导航条目用它打开地址，ADR 0020 第 3 条）：Nova 用 SDK 的 `go_to_url`。

### Community 167 - "Cooperative Stop Design"
Cohesion: 0.25
Nodes (8): 建连早期误报 engine_error 根治, handler 内零 I/O（只置标志 + 记信号号）, 安全点按「单元完成度」判定丢弃, Nova worker flag-only 协作式停止, 被拒方案：asyncio 化消除 greenlet, 被拒方案：handler raise _Terminated 穿透 with, 泄漏兜底：AgentCore 原生 session TTL, SIGINT（Ctrl-C）纳入 flag-only handler

### Community 168 - "_FakeSink"
Cohesion: 0.18
Nodes (5): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。, fixture

### Community 169 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 170 - "cli/tests/conftest.py"
Cohesion: 0.40
Nodes (4): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities()

### Community 172 - "redact.mts"
Cohesion: 0.40
Nodes (3): MASK, ADR-0035, RFC-3986

### Community 173 - "Engine Port & Job Planning"
Cohesion: 0.33
Nodes (7): Engine port（run_scope → WorkerHandle + Event 迭代器）, FargateEngine adapter, JobSource（可注入 job 入口）, pipe 传输实现 die（worker I/O 边缘必改）, Job（一个 scope = 一个会话边界）, plan 模块（.feature → Job 列表）, select 谓词（scenario 筛选）

### Community 174 - "Scope Tag Parsing"
Cohesion: 0.29
Nodes (7): engine 解析（scope 级）, id 派生（scopeId / scenarioId 关联键）, 一个 scenario 多个 @scope 值 → 报错, scope seam（tag 分组 + engine 校验）, scope 全局命名空间（跨文件合并，撞名 warning）, timeout 解析（@timeout:N → Job.timeoutS）, uri 互异契约（重复 uri → 报错）

### Community 175 - "patch-package 补丁 @cucumber+cucumber+13.0.0"
Cohesion: 0.40
Nodes (5): 默认 AI 判断的裸 When/Then step, 补丁的保守回退策略, patch-package 补丁 @cucumber+cucumber+13.0.0, 精确 pin cucumber 13.0.0 的版本约束, B1 退役清单（cucumber 入口 + 补丁 + bdd conftest）

### Community 176 - "Context Glossary Guards"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 177 - "_frontmatter_and_body"
Cohesion: 0.50
Nodes (4): _frontmatter_and_body(), 极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。 支持 `key: 单行值`、引号值，以及 `key:…, `name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环…, test_skill_form_limits()

### Community 178 - "Graceful Stop Contract"
Cohesion: 0.33
Nodes (6): act 有界返回（per-act timeout）, 引擎经 --capabilities 自报 min_grace_s, FargateWorkerHandle.stop → StopTask, grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, 机制层：Engine adapter / WorkerHandle 把停翻成机制

### Community 179 - "Worker Termination Contract"
Cohesion: 0.33
Nodes (6): 事件流结束信号 / 存活判定迁移, exitCode 落值延迟与 MISSING 第三态, 未来演进：显式 core→worker 控制通道, Midscene worker 有序显式 cleanup handler, 逻辑层：schedule 经 worker 句柄请求停（handle.stop）, 终止契约（core 请求 worker 优雅停止）

### Community 180 - "Package URL Links"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 181 - "ADR 0024: worker–core 协议"
Cohesion: 0.08
Nodes (36): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, URL 形态自动分流（导航不写死动词）, assertionVotes 投票次数, 成本信封：engine 只报原生量、core 只合计, 失败/超时的 step 同样带 cost, 深模块、小接口的协议分层原则, errorType 规范化失败分类 (+28 more)

### Community 182 - "_fixture"
Cohesion: 0.08
Nodes (25): events_table(), events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——云端后端测试单独建，schema 见 ADR 0033/0024。, _clean_aws_env(), 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, _aws_env(), _presentation_is_environment_independent(), 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _fixture() (+17 more)

### Community 183 - "Fargate/ECS RunTask 执行后端"
Cohesion: 0.50
Nodes (4): AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务

### Community 185 - "_error_text"
Cohesion: 0.25
Nodes (8): _error_text(), _one_line(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, 多行文本 → 一行有界原因（首个非空行、折叠空白、先脱敏再封顶 300 字）；`_error_text` 与注册表层面的 error 消息共用。, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…, 隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。, test_error_text_prefers_sdk_message_and_is_single_line(), test_error_text_redacts_before_truncation()

### Community 186 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 188 - "_patch_skew"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 189 - "devDependencies"
Cohesion: 0.22
Nodes (9): @aws-sdk/client-device-farm, devDependencies, @aws-sdk/client-device-farm, @types/node, typescript, webdriverio, @types/node, typescript (+1 more)

### Community 190 - "移动真机支持（1.5）：实施进度总纲"
Cohesion: 0.40
Nodes (4): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）, 实施期要核的点（ADR 已定、实施时顺手验证）, 现场, 移动真机支持（1.5）：实施进度总纲

### Community 191 - "test_tunnel.py"
Cohesion: 0.18
Nodes (15): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, TunnelInfo, _job_with(), Job (+7 more)

### Community 192 - "Worker Image Param Mapping"
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

### Community 196 - "Nova Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 197 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 201 - "移动真机支持（1.5）：实施批次的改动面与先写的护栏测试"
Cohesion: 0.18
Nodes (10): 0. B0-navigation：导航规则与注册面关键字声明（1.4 行为的不兼容变更，自己发）, 1. B1-capabilities：能力自述增键（两个 worker 只声明桌面网页；CLI 唯一校验处与交集；doctor、list-deterministic 呈现）, 2. B5-core-events-termination：core 侧会话事件、scope 级 error、合成 SKIPPED、终结函数与真值表、计量合计、explain 呈现, 3. B2-core-target-job：测试目标与 Job 形态（core 侧 tag 归约、target 两形态、按目标的 timeout、plan 标注与目标拒绝、两个 worker 建会话前自检）, 4. B3-config-submit：项目配置文件、组合根填 device_request、definition 格式版本、CLI 侧应用上传, 5. B4-steps-registry：确定性 step 多句柄注册（targets、requires、driver 代理的注册面）, 6. B7-tunnel：隧道改为令牌换 cookie（桌面先行）、桌面 worker 的预热失败出口、脱敏规则三条, 7. B8-deploy-iac：部署侧：权限、Device Farm 项目找回或建立、SSM、doctor 设备项 (+2 more)

### Community 202 - "_color_env_independent"
Cohesion: 0.67
Nodes (3): _reset_scope_colors(), _color_env_independent(), 本模块的颜色断言不受运行测试的 shell 影响：清掉 NO_COLOR / FORCE_COLOR / TERM=dumb，让「是否终端」成为唯一变量。

### Community 203 - "Architecture Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, gherkai 架构图发布入口页, 执行与推进全景交互图

### Community 204 - "Slide Frame SSIM Checks"
Cohesion: 0.67
Nodes (3): slide_area_ssim_checks, at_31_seconds, first_frame

### Community 205 - "AI step（默认执行路径）"
Cohesion: 0.29
Nodes (8): AI step（默认执行路径）, gherkai 命令行工具发行包, gherkai deploy, gherkai-deploy-aws, Midscene 引擎, Nova Act 引擎, @gherkai/worker-midscene, gherkai-worker-novaact

### Community 207 - ".feature (Gherkin 用例)"
Cohesion: 0.29
Nodes (7): gherkai deploy push-worker / list-workers, 确定性 step, .feature (Gherkin 用例), 导航 step, gherkai plan（用例预检）, @scope 浏览器会话分组, 确定性 step 参考（agent skill）

### Community 210 - "_seed_run"
Cohesion: 0.09
Nodes (24): 建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…, `_build` 的三层 store 全用它自己已建的那批句柄装配——compose 里建句柄的两个钩子在此一次都不该执行。 这条同时是「region…, definition 声明 ≤ cap → 按 definition 走（打通前云端后端静默忽略提交侧声明，是可用性缺陷）。, definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。, meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。, cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…, 推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。 (+16 more)

### Community 211 - "tunnel.py"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 213 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 214 - "_cmd_deploy"
Cohesion: 0.33
Nodes (6): _cmd_deploy(), _cmd_destroy(), _deploy_provider(), 取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…, [部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。前端零 IaC 知识。 退出码即 provider…, [部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。

### Community 217 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 223 - "test_detached_launcher.py"
Cohesion: 0.17
Nodes (20): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, _job(), SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。 **真 spawn…, region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者… (+12 more)

### Community 224 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 227 - "gherkai：价值与方法（材料索引）"
Cohesion: 0.60
Nodes (5): 演示材料索引, 价值与方法 视频章节, 价值与方法 纯口播稿, gherkai：价值与方法（材料索引）, 价值与方法 讲者备注

### Community 228 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 235 - "ADR 0013: 跨引擎共享边界"
Cohesion: 0.23
Nodes (12): ADR 0005: 单一共享 feature 文件, 双语言裂缝（物理约束）, ADR 0006: 形态 A——两个子工程、无编排器, 公共设施落在核心库层（报告归集/会话生命周期/跑批入口）, ADR 0013: 跨引擎共享边界, 跨引擎共享止于 features/（Gherkin 单一事实源）, 薄 worker 子进程（一次调用=一个 scope=一个 job）, 两个引擎都作为子进程 worker、核心语言自由选 Python (+4 more)

### Community 246 - "test_worker_subnets_single_source_across_ssm_and_lambda_env"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 247 - "NgrokTunnel"
Cohesion: 0.24
Nodes (9): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。, test_ngrok_binary_missing_reports_install_hint(), test_ngrok_start_spawns_agent_and_reads_log(), test_ngrok_start_timeout_reports_authtoken_hint() (+1 more)

### Community 257 - "compose.py"
Cohesion: 0.06
Nodes (43): subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), is_botocore_error(), _make_ecr_client() (+35 more)

### Community 269 - "test_lambda_handlers.py"
Cohesion: 0.06
Nodes (38): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。 (+30 more)

### Community 271 - "./deterministic.mjs"
Cohesion: 0.06
Nodes (28): ADR-0025, ADR-0022, ADR-0036, ADR-0037, ./deterministic.mjs, deterministic(), DeterministicAssertion, DeterministicConflict (+20 more)

### Community 277 - "gherkai_runtime/__init__.py"
Cohesion: 0.20
Nodes (9): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 306 - "./deterministic.steps.mjs"
Cohesion: 0.25
Nodes (8): ./deterministic.steps.mjs, ADDRESS_PATTERN, ADR-0020, ADR-0022, ADR-0036, ADR-0037, RFC-3986, WEB_SCHEMES

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
- **606 isolated node(s):** `CONNECT_BACKOFF_MS`, `STOP_SESSION_BUDGET_MS`, `INFLIGHT_SETTLE_MS`, `QUEUE_DRAIN_EXIT_MS`, `BROWSER_CLOSE_BUDGET_MS` (+601 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **47 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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