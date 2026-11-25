# Graph Report - yaozhou  (2026-11-25)

## Corpus Check
- 514 files · ~1,102,575 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 31 file(s) not represented in the graph (top: (none) 17, .feature 7, .xml 6)

## Summary
- 15132 nodes · 36255 edges · 595 communities (357 shown, 238 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 3034 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `005bfbd4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- guard.mts
- test_backend_cloud.py
- test_run_deadline.py
- stderr-outlets.test.mts
- _cleanup
- _InterruptState
- test_schedule.py
- CommitOutcome
- run_dir.py
- pytest
- workers.py
- _FakeEcs
- _seed_run
- _run_step
- test_status_group.py
- test_s3_result_store.py
- test_stack.py
- initial_run_state
- test_deploy_cmd.py
- test_a_cutoff_decided_before_the_exit_marks_the_exit_as_timed_out
- query_capabilities
- test_codex_usage.py
- test_list_runs.py
- os
- ArtifactUploader
- ensure_workflow_definition
- core/tests/conftest.py
- gherkai_cli/__main__.py
- _seed_run
- CONTRIBUTING（contributor 入口）
- device_reprobe.mts
- test_workers_real_aws.py
- test_abort_flag_records_only_the_first_cause_under_concurrent_set
- ._invoke_cdk
- test_worker_variant.py
- _status
- test_termination_parity.py
- Job
- test_terminal.py
- gherkai agent skill 主文
- test_app_upload.py
- textui.py
- test_user_steps.py
- test_settle.py
- test_ddb_error_ending.py
- test_project.py
- test_stores.py
- 实装
- _patch_skew
- _verb_call
- test_precheck.py
- test_run_dir.py
- JobState
- test_definition_schema.py
- test_interrupt_model.py
- appium.mts
- test_lifecycle_states.py
- codex_usage.py
- guard.test.mts
- ._guard_vpc_spec
- 架构总览：五层结构、一次 run 的生命周期、包与发行物
- ._run_once
- DeviceSurface
- manifest.json
- evidence.mts
- test_artifact_upload.py
- _RecUploader
- _is_transient_network
- main
- plan
- LocalRunStore
- test_compose.py
- resolve_worker_cmd
- time
- gherkai 变更记录 (CHANGELOG)
- main
- core/tests/test_redact.py
- test_cloud_integration.py
- ../lib/tunnel-warmup.mjs
- test_cloud_reconcile.py
- use_color
- test_skill_deploy_tokens.py
- json
- test_user_docs.py
- finalize.test.mts
- handoff.py
- workers_real_aws/conftest.py
- _parse
- README Video Specs
- TypeScript Build Config
- evidence.test.mts
- ../device/limits.mjs
- Composition Root Architecture
- test_project_config.py
- test_engines_matrix.py
- subprocess
- Video Material Files
- skill_install.py
- _StampSsm
- test_ddb_capacity.py
- test_event_bounds.py
- 决策
- Run Store Persistence Ports
- test_detached_launcher.py
- test_codex_review.py
- 决策
- 决策
- interface.mts
- AppiumInterface
- _call_with_timeout
- app.mts
- codex_usage.py
- build_diagrams.mjs
- ArtifactUploader
- 06-devicefarm-appium.mts
- _fake_locator
- _state
- with
- _stream_record
- test_adr_hygiene.py
- pathlib
- test_reconcile.py
- test_tunnel_cli.py
- test_skill.py
- RunPersistence
- run-scope.test.mts
- test_provider.py
- 实装
- InlineChildren
- probe.mts
- Media Conversion Verification
- package.json
- Boundary
- run_scope.py
- _fake_gherkai
- JobSource
- DynamoDB Events Transport ADR
- xcuitest.test.mts
- 决策
- ArtifactUploader
- test_atomic_write.py
- devicefarm.py
- main
- Stateless Run Core Model
- test_evidence.py
- argument.mts
- test_user_facing_messages.py
- _settle_sentences
- session.test.mts
- 0050. 确定性 step 多句柄注册与测试分层
- test_review_round_gate.py
- LocalResultStore
- deploy
- preflight_cloud_resources
- report_dir_too_long
- ref_node_assert
- test_settle_runs.py
- run_reconcile_loop
- _role_statements
- .commit_job_states
- _build_parser
- ddb_capacity.py
- Graphify Refresh Script
- shutil
- job-source.mts
- read-points.test.mts
- Cooperative Stop Design
- S3StepArgumentOffloader
- .on_job_complete
- test_doc_rules_check.py
- adapters.contract.test.mts
- test_wire.py
- Engine Port & Job Planning
- Scope Tag Parsing
- test_sqlite_event_log.py
- agentcore-sigv4.mts
- log
- Graceful Stop Contract
- Worker Termination Contract
- Package URL Links
- tunnel.py
- test_persist.py
- session.mts
- DeviceSurface
- test_drain_bound_applies_before_deadline_under_fail_fast
- _Deleted
- Artifact Uploader Component
- doc_rules_check.py
- test_lambda_asset.py
- _settle_sentences
- _create
- test_report_dir_length_commands.py
- Gherkin Parse Seam
- exerciseSession
- _StderrScan
- event-bounds.mts
- ProcessEvents
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- container_name
- 逐条
- Architecture Diagrams
- Slide Frame SSIM Checks
- SubprocessWorkerHandle
- test_devicefarm_client_placement.py
- env
- _load_and_plan
- web-context.mts
- test_fargate_engine.py
- app.test.mts
- SqliteEventLog
- DeviceFarmSessions
- Step Matching & Plan Annotation
- EventLog
- tunnel_host.py
- no-device-deps.test.mts
- test_tunnel.py
- test_container.py
- _recording
- precheck.mts
- _explain_run
- Index Wait Script
- gherkai Workspace Root
- _StubEcs
- write_report_from_record
- compose.py
- Execution Backend
- Feature Files
- Error Type Classification
- Local Per-Run Advance Process
- .finalize
- gherkai Core Package
- AWS Deploy Package
- Runtime Package
- NovaAct Worker Package
- assemble_run_result
- 03-midscene-grounding.ts
- surface-desktop.mts
- test_writing_the_mapping_is_followed_by_removing_retired_at_from_the_new_revision
- sys
- session-name.mts
- test_stderr_redaction.py
- test_package_readmes.py
- app_upload.py
- jobs
- test_names_worker.py
- job_entry_store
- device_reprobe 使用说明（Midscene 设备模块的真机重新探测）
- Bundled JetBrains Mono WOFF2 Subsets
- xcuitest.mts
- _Recorder
- 项目约定
- .execute
- with
- npm
- uiautomator2.mts
- ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）
- test_both_reports_come_from_the_same_snapshot_even_when_a_request_completes_after_the_command_returns
- appium.test.mts
- test_event_log_recording.py
- runScope
- deterministic.py
- CONTRIBUTING.md: contributor 指南
- serialize.py
- test_devicefarm.py
- test_release_notes.py
- deploy.py
- stopTimeout=120 / grace 预算校准
- check_dist_metadata.py
- test_report_dir_in_output.py
- ci.yml
- .preStep
- error-text.mts
- image-gate
- _definition_header_gate
- User Guide 入口
- test_lambda_handlers.py
- _all_option_dests
- 逐条
- _assert_usage_error
- image-gate
- include
- warmup.mts
- _stopped_detail
- DriverAdapter
- _wire_capture
- test_settle_runs.py
- steps
- test_workers.py
- test_a_record_failure_that_comes_with_an_interrupt_ends_as_the_failure
- _FakeSink
- test_plan_target_check_degrades_when_capabilities_unavailable
- commit_applied
- test_load_definition_only_logs_when_the_error_ending_finds_the_run_state_unreadable
- _Store
- 推进权与状态投影：ADR 写回的结果与实装线索
- device/surface.test.mts
- reconciler.py
- warmup.test.mts
- image_token_probe：截图缩放后的图片 token 探针
- ./deterministic.mjs
- _FakeSchedulerClient
- test_both_advancers_get_the_same_non_empty_worker_subnets
- e2e_harness.py
- TargetSurface
- LazyDdb
- pipe_results
- parent-watchdog.mts
- ._invoke_cdk
- test_compose.py
- test_handle_timeout_finds_stopped_target_on_second_page
- _DeviceFarmStub
- .from_env
- severity 数值序（_STATUS_SEVERITY）
- _FakeProvider
- test_ctrl_c_before_the_settle_of_a_given_run_changes_nothing
- jobs
- LockHolder
- runtime/tests/conftest.py
- staging_names
- test_account_check_only_swallows_credential_and_network_failures
- register
- bin.mts
- _SpyRunStore
- node
- _Party
- build
- images
- _BucketRegionObserver
- .attempt
- test_main.py
- _variant_miss_hint
- 逐条
- Fargate/ECS RunTask 执行后端
- codex_review.py
- skipif
- on
- test_session_events_reject_unknown_enums_and_missing_pairing_key
- diffAgainstFixture
- 移动真机支持（1.5）：实施进度总纲
- _ExitRecorder
- _StubHandle
- _staging
- tunnel.py（--expose-local 隧道 provider）
- S3 Key Mirrors Local Run Tree
- test_interrupt_process.py
- 成本信封：engine 只报原生量、core 只合计
- WebdriverCtx
- _fake_store_ctors
- AdaptedEcs
- sleep.mts
- RunState 物化读视图
- parametrize
- match
- 产品文案护栏（AST 扫禁词表）
- RunStateWriteContended
- test_wire.py
- DeterministicCtx
- listRegistry
- _DeviceFarmStub
- progress
- ./deterministic.steps.mjs
- _IncClock
- _StagedCreator
- Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障
- 逐条
- _make_devicefarm_client
- test_finalize_end_write_refused_and_the_read_back_failing_raises_the_read_failure
- _ForkingCreator
- render_skill_contract.py
- release_notes.py
- _FastClock
- _FakeSdk
- test_list_workers_json_keys_match_contract_doc
- test_context_glossary.py
- test_finalize_after_the_stop_signal_still_reports_ended_elsewhere_when_the_read_back_fails
- _FlakySaves
- _Child
- _Fd0
- test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions
- test_snapshot_sees_what_the_real_run_store_writes_until_the_run_finishes
- 词表与退役词
- 行为文档（随所改行为的实装批同一提交改）
- _BoundedReads
- _interrupt_prompt
- TerminalStore
- test_status_wait_ctrl_c_while_showing_the_run_does_not_change_the_result
- _index_ast_lines
- test_each_save_takes_its_own_id_and_the_terminal_write_names_it
- test_launch_failure_isolated_other_job_completes
- test_load_definition_logs_the_diagnosis_before_reraising_a_failed_error_ending
- default_name
- run_store
- .save_job_result
- _OrderRecordingRunStore
- image_gate.sh
- 收尾
- test_the_report_follows_the_given_run_identifier_not_the_one_in_the_definition
- config.py
- _every_field_filled
- AdapterRegistry
- AppiumConnector
- CapabilityProbe
- DeviceFinalizer
- GuardFactory
- ADR-0019
- ADR-0026
- ADR-0027
- ACQUIRE_INTERRUPTED_MESSAGE
- ACQUIRE_TIMEOUT_MESSAGE
- ADR 0043: 随 CLI 发行的 agent skill
- AddressAttempt
- AgentFactory
- APP_LOCATION_MISSING_MESSAGE
- APP_PREPARE_TIMEOUT_MESSAGE
- ConnectOutcome
- ConnectRequest
- DeviceChoice
- DeviceParts
- DevicePartsEnv
- DevicePartsFactory
- DeviceSurfaceOptions
- FinalizeHooks
- FINALIZING_ACQUIRE_MESSAGE
- HANDLER_KIND_MISMATCH_MESSAGE
- HELPER_REJECTED_AGAIN_MESSAGE
- HELPER_REJECTED_NO_TIME_MESSAGE
- LIVENESS_FAILED_MESSAGE
- ADR-0022
- ADR-0039
- ADR-0042
- ADR-0044
- gherkai_runtime/__init__.py
- _mk_state
- 决策
- test_tick_runs_writes_the_report_from_the_record_when_its_tick_commits
- ADR-0050
- surface.mts
- test_cli_json_contract.py
- gherkai_deploy_aws/names.py
- _advancer_stmts
- instant_to_iso
- ADR-0051
- ADR-0052
- Outcome
- _FakeTime
- review-round-gate.sh
- 输入契约：一个 scope 的 Job（展开后的有序 step）
- PRE_STEP_FAILED_MESSAGE
- ProbeConclusion
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- test_build_reuses_its_own_handles_and_builds_no_new_client
- ReadyState
- RemoteSession
- RESTORE_FAILED_TAIL
- harness.py
- RunningSession
- Holder
- SESSION_LOST_BEFORE_START_MESSAGE
- SESSION_LOST_MESSAGE
- cloud_env
- SurfaceConfig
- 推进权与状态投影：实装线索逐条对到 code 的摸底
- CountingEcs
- .call
- WEB_CONTEXT_ON_APP_MESSAGE
- _RecordingTunnel
- build_fargate_engines
- WEB_CONTEXT_PROBE_ERROR_MESSAGE
- WEB_CONTEXT_UNAVAILABLE_MESSAGE
- WebContextVerdict
- _signal_inside_end_run
- WindowOutcome
- Dispatch
- FailureExitDeps
- Job
- MIN_GRACE_MARGIN_MS
- ADR-0014
- ADR-0020
- ADR-0022
- ADR-0024
- ADR-0028
- ADR-0029
- navigate
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
- _FakeRecord
- Scenario
- ScopeIo
- _import_bindings
- test_launch_failure_after_the_cutoff_projects_as_timeout
- ScopeSeam
- ShutdownDeps
- Step
- WORKER_TARGETS
- ADR 0024: worker–core 协议

## God Nodes (most connected - your core abstractions)
1. `main()` - 411 edges
2. `Status` - 382 edges
3. `JobState` - 276 edges
4. `RunState` - 208 edges
5. `LocalRunStore` - 188 edges
6. `Job` - 180 edges
7. `schedule()` - 170 edges
8. `RunMeta` - 157 edges
9. `JobResult` - 147 edges
10. `FakeEngine` - 145 edges

## Surprising Connections (you probably didn't know these)
- `线索没有覆盖的改动点` --references--> `_run_ids_from_runs_stream()`  [INFERRED]
  docs/journey/0021-run-ownership-implementation-clue-map.md → deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py
- `查看-6（mixed，S）` --references--> `check_report_dir()`  [INFERRED]
  docs/journey/0021-run-ownership-implementation-clue-map.md → core/gherkai_core/adapters/run_store/run_dir.py
- `小结` --references--> `load_named_details()`  [INFERRED]
  docs/journey/0021-run-ownership-implementation-clue-map.md → core/gherkai_core/named_details.py
- `查看-7（code，L）` --references--> `load_named_details()`  [INFERRED]
  docs/journey/0021-run-ownership-implementation-clue-map.md → core/gherkai_core/named_details.py
- `查看-4（code，M）` --references--> `past_overdue()`  [INFERRED]
  docs/journey/0021-run-ownership-implementation-clue-map.md → core/gherkai_core/run_deadline.py

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

## Communities (595 total, 238 thin omitted)

### Community 0 - "guard.mts"
Cohesion: 0.05
Nodes (44): AFTER_RESULT_UNKNOWN_MESSAGE, commandFailedMessage(), CommandGuardArgs, commandGuardFactory, CONNECTION_ERROR_CODES, CONTEXT_SWITCH_COMMANDS, copyOutcome(), createCommandGuard() (+36 more)

### Community 1 - "test_backend_cloud.py"
Cohesion: 0.02
Nodes (77): _clear_resource_env(), _cloud_submit_argv(), _deadline_offset_s(), _definition(), _FakeS3, _FakeTable, _FakeTunnelService, _forbid_run_steps() (+69 more)

### Community 2 - "test_run_deadline.py"
Cohesion: 0.06
Nodes (35): job_cutoff(), JobCutoff, overdue_at(), past_deadline(), past_overdue(), past_stop_start(), stop_start_at(), _meta() (+27 more)

### Community 3 - "stderr-outlets.test.mts"
Cohesion: 0.06
Nodes (65): ALIAS_ASSIGNMENTS, Bindings, bindingsOf(), CONSOLE_STDERR, DECLARATION_KINDS, describe(), destructuredKey(), dynamicImportSpecifier() (+57 more)

### Community 4 - "_cleanup"
Cohesion: 0.04
Nodes (51): _after_mapping_reread(), _cleanup(), _final_check_pass(), _held_push(), HookedDdb, HookedEcs, HookedSsm, _put_state() (+43 more)

### Community 5 - "_InterruptState"
Cohesion: 0.06
Nodes (11): _cmd_settle_runs(), _emit_settle_runs(), _flush_stdout(), _InterruptState, _run_state_unreadable(), _settle_access_failure(), _settle_runs_body(), _settle_runs_main() (+3 more)

### Community 6 - "test_schedule.py"
Cohesion: 0.05
Nodes (101): schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, test_fail_fast_inflight_job_is_aborted(), stop_hook(), test_fail_fast_queued_job_is_skipped() (+93 more)

### Community 7 - "CommitOutcome"
Cohesion: 0.04
Nodes (69): _item_at_failed_condition(), _job_state_from_item(), _run_state_from_item(), _run_status_assignment(), _unknown_job_attrs(), _write_seq_increment(), CommitOutcome, test_commit_rejected_by_the_write_seq_names_the_same_id_after_rereading() (+61 more)

### Community 8 - "run_dir.py"
Cohesion: 0.05
Nodes (37): _status_line(), test_adr_has_standard_status_head(), test_superseded_links_are_bidirectional(), _claim_staging(), create_run_dir(), _darwin_fs_type(), _darwin_fstatfs(), filesystem_type() (+29 more)

### Community 9 - "pytest"
Cohesion: 0.06
Nodes (54): _cfg(), _outline(), _plan(), _scope_feature(), test_assertion_votes_default_is_one(), test_background_prepended(), test_bare_tag_without_value_errors_with_location(), test_datatable_and_docstring_argument() (+46 more)

### Community 10 - "workers.py"
Cohesion: 0.03
Nodes (63): Aws, cleanup_pass(), CleanupOutcome, _clear_retired_at_after_mapping(), _connect(), current_version_mappings(), _describe_revision(), _ecr_login() (+55 more)

### Community 11 - "_FakeEcs"
Cohesion: 0.06
Nodes (25): _Clock, _FakeEcs, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_converges_from_describe_keeps_timeout_attribution_of_own_stop(), test_handle_timeout_converges_from_describe_when_task_already_stopped(), test_handle_timeout_disposes_at_once_when_deadline_passed(), test_handle_timeout_does_not_loop_forever_when_the_clock_stays_at_the_cutoff(), test_handle_timeout_does_not_stop_when_the_wait_quota_runs_out_before_the_cutoff() (+17 more)

### Community 12 - "_seed_run"
Cohesion: 0.06
Nodes (24): test_list_runs_json_keys_are_documented(), _cloud_list_runs_env(), make_table(), _list_runs_json(), _seed_listing_fixture(), _seed_run(), _table_row(), test_list_runs_cloud_checks_skew_then_index_then_lists_ongoing_before_finished() (+16 more)

### Community 13 - "_run_step"
Cohesion: 0.05
Nodes (44): _classify_act_error(), _run_scenario(), _run_step(), _ActBoom, _done(), _FakeNova, _FakeResult, _Meta (+36 more)

### Community 14 - "test_status_group.py"
Cohesion: 0.07
Nodes (33): _assert_corresponds(), _claim(), _commit_ending_failed(), _commit_open(), _drop_group(), _end_with(), end(), _expected_group() (+25 more)

### Community 15 - "test_s3_result_store.py"
Cohesion: 0.08
Nodes (8): S3ResultStore, result_store(), _RecordingClient, side(), _Side, test_prefix_isolates_runs(), test_s3_load_lets_errors_other_than_no_such_key_through(), test_s3_store_saves_and_reads_without_listing()

### Community 16 - "test_stack.py"
Cohesion: 0.05
Nodes (50): make_template(), _ssm_params(), test_advancer_roles_hold_no_ssm_read(), test_artifacts_bucket_job_in_lifecycle(), test_artifacts_bucket_private(), test_ecr_repos_have_no_lifecycle_rules_and_are_retained(), test_ecs_stopped_eventbridge_rule(), test_events_stream_mapping_filters_out_ttl_removes() (+42 more)

### Community 17 - "initial_run_state"
Cohesion: 0.09
Nodes (15): initial_run_state(), events_db_path(), now_iso(), assemble_local_run(), _job(), _refuse_child_processes(), test_advance_local_run_refuses_a_definition_without_concurrency(), test_advance_local_run_stops_when_saves_keep_failing() (+7 more)

### Community 18 - "test_deploy_cmd.py"
Cohesion: 0.06
Nodes (25): _FakeEP, _patch_eps(), _StubProvider, test_cli_does_not_import_aws_cdk(), test_cli_version_is_handed_to_provider(), test_command_face_flags_reach_provider(), test_dispatch_maps_command_face_to_provider_method(), test_entry_point_class_gets_instantiated() (+17 more)

### Community 19 - "test_a_cutoff_decided_before_the_exit_marks_the_exit_as_timed_out"
Cohesion: 0.08
Nodes (15): _by_thread(), _CapturingReports, _echo_resolver(), _foreground_result(), _ParkedChecks, stop_due(), _run_in_thread(), test_a_cutoff_decided_before_the_exit_marks_the_exit_as_timed_out() (+7 more)

### Community 20 - "query_capabilities"
Cohesion: 0.05
Nodes (33): engine_min_grace(), match_deterministic(), query_capabilities(), _caps_json(), _fake_caps_proc(), test_ask_worker_cwd_not_a_directory_is_unavailable(), test_ask_worker_no_payload_entry_does_not_inherit_stdin(), test_ask_worker_non_executable_override_is_unavailable() (+25 more)

### Community 21 - "test_codex_usage.py"
Cohesion: 0.14
Nodes (21): call(), complete(), meta(), run(), started(), test_compaction_is_marked_on_the_round_and_the_root_reading(), test_continuation_segment_is_part_of_the_root_thread(), test_default_scope_covers_active_and_archived_sessions() (+13 more)

### Community 22 - "test_list_runs.py"
Cohesion: 0.04
Nodes (57): DynamoDBRunStore, read_page(), _listed_from_live(), status_group(), RunListing, cloud_runs(), _FakeTable, _ids() (+49 more)

### Community 23 - "os"
Cohesion: 0.05
Nodes (47): close_quietly(), open_log(), peer_closed(), read_line(), wait_readable(), write_all(), _assert_both_ends_released(), _channel() (+39 more)

### Community 24 - "ArtifactUploader"
Cohesion: 0.10
Nodes (8): ArtifactUploader, _extra_args(), _log(), test_noop_preserves_bare_path_no_symlink_resolve(), test_noop_reports_file_uri_and_no_delete(), test_noop_uploader_enqueue_and_drain_are_immediate(), test_ref_for_noop_reports_same_file_uri_as_report_ref(), test_s3_client_has_bounded_timeouts_and_no_retry()

### Community 25 - "ensure_workflow_definition"
Cohesion: 0.04
Nodes (29): _leave_warmup_page(), _one_line(), _wait_for_marker(), warmup_session(), WarmupFailure, WarmupStopped, ensure_workflow_definition(), _error_text() (+21 more)

### Community 26 - "core/tests/conftest.py"
Cohesion: 0.10
Nodes (12): arg_offloader(), aws(), ClosingLockHolder, ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), _host_independent_filesystem_type() (+4 more)

### Community 27 - "gherkai_cli/__main__.py"
Cohesion: 0.03
Nodes (67): _advance_store_failure_notice(), _advance_submitted(), _build_run_meta(), _close_owned(), _cloud_skew_gate(), _cloud_submit_interrupted(), _cloud_target(), _cloud_worker_variant_gate() (+59 more)

### Community 28 - "_seed_run"
Cohesion: 0.08
Nodes (11): _seed_run(), _seed_worker_ssm(), test_build_cap_defaults_to_one_when_env_absent(), test_build_clamps_meta_max_concurrency_to_cap(), test_build_defaults_to_one_when_meta_missing(), test_build_hands_the_deployed_fargate_config_to_the_worker_task(), test_build_reads_session_warmup_url_back_into_worker_env(), test_build_takes_meta_max_concurrency_under_cap() (+3 more)

### Community 29 - "CONTRIBUTING（contributor 入口）"
Cohesion: 0.08
Nodes (54): CLAUDE.md（项目约定）, Bash, Claude Code 在本仓库的操作要点, hooks, Workflow, 记忆文件, _doc_rules.py（逐行可判规则与扫描面的唯一源）, test_skill.py（skill 产品面与真值护栏） (+46 more)

### Community 30 - "device_reprobe.mts"
Cohesion: 0.05
Nodes (27): Attempt, Browser, CALL_ORDER, Captured, CaseResult, CaseStatus, ContractCase, ContractFixture (+19 more)

### Community 31 - "test_workers_real_aws.py"
Cohesion: 0.06
Nodes (53): _env(), _injected_mirror(), _insert_positions(), _load_module(), _names(), _outcomes(), _phases_by_case(), _probe_residue() (+45 more)

### Community 33 - "._invoke_cdk"
Cohesion: 0.06
Nodes (15): Provider, test_a_bad_profile_exits_2_at_the_entry_not_a_traceback(), test_app_command_uses_current_interpreter_and_module(), test_bootstrap_without_resolvable_region_exits_2(), test_contributed_flag_surface_is_exactly_the_provider_specific_set(), test_delete_worker_is_a_documented_placeholder(), test_generated_cdk_json_carries_app_and_feature_flags_verbatim(), test_provider_doctor_reports_toolchain() (+7 more)

### Community 34 - "test_worker_variant.py"
Cohesion: 0.04
Nodes (39): worker_image_key(), aws(), _client_error(), _describe_error(), _Failing, _FailingEcs, _fake_aws_creds(), _PagedListing (+31 more)

### Community 35 - "_status"
Cohesion: 0.07
Nodes (28): _bytes(), _create(), _jobs(), _polls(), _status(), test_local_status_does_not_resolve_the_aws_identity(), test_settle_runs_names_a_lock_that_cannot_be_taken(), flock() (+20 more)

### Community 36 - "test_termination_parity.py"
Cohesion: 0.05
Nodes (33): result_without_record(), EventRecord, TaskExited, test_projection_clamps_the_terminal_run_status_from_project(), _boom_stateless(), _boom_sync(), _Clock, _closed() (+25 more)

### Community 37 - "Job"
Cohesion: 0.03
Nodes (69): test_reconcile_entry_reads_its_input_from_stdin_and_reports_a_tunnel_failure(), _state_scalars(), RunAlreadyExists, Job, RunMeta, Scenario, Step, StepArgument (+61 more)

### Community 38 - "test_terminal.py"
Cohesion: 0.04
Nodes (48): SessionRecord, apply_device_metering(), _cutoff_from_claim(), device_metering(), finalize_job(), _find_session(), is_device_job(), NonTerminalSnapshot (+40 more)

### Community 39 - "gherkai agent skill 主文"
Cohesion: 0.11
Nodes (24): skill 参考：CLI --json 字段契约, skill 参考：云端后端分工与 variant 交付, skill 参考：确定性 step 的写法, skill 参考：引擎选择与确定性 step 模板, skill 参考：环境就位与排障, gherkai agent skill 主文, AI 断言 (AI assertion), 基础镜像 / variant / 默认指针 (+16 more)

### Community 40 - "test_app_upload.py"
Cohesion: 0.15
Nodes (14): AppLocation, ensure_app_object(), _file(), _observer_gone(), _S3, _S3Redirecting, test_403_on_head_is_a_permission_error_and_other_errors_propagate(), test_ensure_app_object_returns_the_last_signing_region_and_unregisters_on_every_path() (+6 more)

### Community 42 - "textui.py"
Cohesion: 0.08
Nodes (20): _cmd_list_deterministic(), target_cell(), _as_text(), _console(), output_width(), plain(), render_table(), render_tree() (+12 more)

### Community 43 - "test_user_steps.py"
Cohesion: 0.06
Nodes (30): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), UserStepsError, _clean_env(), _isolate(), _step_file() (+22 more)

### Community 44 - "test_settle.py"
Cohesion: 0.02
Nodes (68): Engine, EngineResolver, JobSink, ReportStore, RunRecord, RunStore, Sink, WorkerHandle (+60 more)

### Community 45 - "test_ddb_error_ending.py"
Cohesion: 0.07
Nodes (21): _is_integral_number(), RunStateUnreadable, _create(), _key(), other(), _raw(), _record(), _set() (+13 more)

### Community 46 - "test_project.py"
Cohesion: 0.05
Nodes (60): Status, Action, plan_next(), platform_exit_reason(), project(), _detail(), _ev(), _exit() (+52 more)

### Community 47 - "test_stores.py"
Cohesion: 0.02
Nodes (94): RetryingResultStore, _header_from_item(), _job_state_to_item(), _schema_version_attr(), NamedDetailMissing, AppRef, DeviceFarmRequest, Target (+86 more)

### Community 48 - "实装"
Cohesion: 0.03
Nodes (91): device_header_lines(), explain_to_dict(), _ms(), render_explain_text(), render_text(), run_tree(), session_lines(), test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact() (+83 more)

### Community 49 - "_patch_skew"
Cohesion: 0.04
Nodes (13): _patch_skew(), test_status_cloud_artifacts_follow_the_given_table_bucket_and_report_dir(), test_status_cloud_exits_2_when_the_definition_header_read_hits_an_aws_error(), test_status_cloud_exits_2_when_the_first_state_read_hits_an_aws_error(), test_status_cloud_json_includes_artifact_locations(), test_status_cloud_pending_hint_offers_relay_only_for_detached_runs_and_stays_quiet_when_the_marker_is_unreadable(), test_status_cloud_pending_run_with_a_claimed_job_does_not_hint(), test_status_cloud_terminal_prints_s3_and_ddb_locations() (+5 more)

### Community 50 - "_verb_call"
Cohesion: 0.07
Nodes (19): ssm_device_farm_project_path(), _assert_record_read_hint(), _cli_version_verb_call(), test_deploy_other_device_farm_errors_exit_1_without_guessing(), test_deploy_unreadable_project_record_exits_2_without_resolving(), test_diff_exits_2_when_verifying_the_recorded_project_fails_otherwise(), test_malformed_project_record_exits_2_and_names_the_parameter(), test_missing_cli_version_exits_2_without_cdk_or_aws() (+11 more)

### Community 51 - "test_precheck.py"
Cohesion: 0.10
Nodes (17): _num(), precheck_job(), precheck_schema(), precheck_target(), _spaced(), supported_label(), target_label(), _capabilities() (+9 more)

### Community 52 - "test_run_dir.py"
Cohesion: 0.04
Nodes (63): LockState, probe_run_dir(), RunDirProbe, StagingSweep, sweep_staging_dir(), _acquired_within(), _built_run(), _make_staging() (+55 more)

### Community 53 - "JobState"
Cohesion: 0.03
Nodes (79): render_run_state(), test_explain_named_scope_still_running_while_the_run_is_running_says_not_landed(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), JobState, RunState, _all_pending_after_a_claim(), _all_pending_before_any_claim() (+71 more)

### Community 54 - "test_definition_schema.py"
Cohesion: 0.09
Nodes (17): _as_detached_run_in_progress(), _drop_a_target_key(), _release_on_the_second_poll(), _rewrite_schema(), _seed_local_run(), test_background_advancer_advances_the_definition_it_generated_without_reading_it_back(), assemble_then_damage(), test_cloud_status_and_explain_peek_meta_header_before_state() (+9 more)

### Community 55 - "test_interrupt_model.py"
Cohesion: 0.04
Nodes (40): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), _start_parent_watchdog(), _watch_parent(), captured(), _FakeResult (+32 more)

### Community 56 - "appium.mts"
Cohesion: 0.05
Nodes (30): AppiumConnectorOptions, AppiumSessionArgs, AUTOMATION_NAMES, BROWSER_NAMES, CLIENT_TIMEOUTS, clientOptions(), ClientTimeouts, CommandFailureKind (+22 more)

### Community 57 - "test_lifecycle_states.py"
Cohesion: 0.08
Nodes (11): severity(), _aggregate(), FakeWorkerHandle, _NetRaiseEngine, test_aggregate_reduces_the_three_worker_states(), test_aggregate_rejects_empty_input_and_states_outside_the_three(), test_pending_running_have_no_severity(), test_severity_full_chain() (+3 more)

### Community 58 - "codex_usage.py"
Cohesion: 0.13
Nodes (20): _catalog(), _context_cell(), _default_sessions_dirs(), _figures(), _locate(), main(), _order_segments(), _pad() (+12 more)

### Community 59 - "guard.test.mts"
Cohesion: 0.06
Nodes (17): adapterWith(), codeError(), FakeElement, FakeExec, FakeServer, fakeWebDriver(), Harness, harness() (+9 more)

### Community 60 - "._guard_vpc_spec"
Cohesion: 0.05
Nodes (19): cdk_command(), check_cdk(), check_node(), _error_code(), _has_aws_credentials(), _is_credential_error(), _make_cfn_client(), _make_hint_clients() (+11 more)

### Community 61 - "架构总览：五层结构、一次 run 的生命周期、包与发行物"
Cohesion: 0.06
Nodes (75): ADR 0001: 范围限于英文 UI, 概念：非英文应用用 @engine:midscene 路由, 概念：Nova Act 中文词语级文本匹配短板, ADR 0002: Midscene 不由 GPT-5.5 驱动, 概念：只认响应 body、不认 HTTP 状态码, 概念：Midscene 仅走 chat-completions 接口, ADR 0003: VL 模型选型, ADR 0003: Midscene grounding 用 Qwen3-VL on Bedrock (+67 more)

### Community 62 - "._run_once"
Cohesion: 0.06
Nodes (5): _AbortFlag, _EndedElsewhere, _heartbeat_wrap(), _note_not_retried(), _Worker

### Community 63 - "DeviceSurface"
Cohesion: 0.13
Nodes (3): AcquireBudget, Budget, reasonOf()

### Community 64 - "manifest.json"
Cohesion: 0.06
Nodes (35): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+27 more)

### Community 65 - "evidence.mts"
Cohesion: 0.07
Nodes (36): actionsOf(), buildEvidence(), BuildEvidenceInput, controlItemOf(), deviceKeysOf(), ENGINE, errorTextOf(), EVIDENCE_KIND (+28 more)

### Community 66 - "test_artifact_upload.py"
Cohesion: 0.08
Nodes (23): _Calls, _shots(), test_concurrent_report_ref_and_queue_share_uploaded_set(), test_content_type_suffix_match_is_case_insensitive(), test_drain_is_bounded_returns_false_while_item_in_flight(), test_drain_timeout_abandons_queue_silently(), test_enqueue_uploads_in_background_with_same_key_as_ref_for(), test_evidence_screenshot_and_json_content_types() (+15 more)

### Community 67 - "_RecUploader"
Cohesion: 0.05
Nodes (16): _drain_evidence_uploads(), _FakeBrowserClient, _FakeNovaAct, _install_browser_client(), _RaisingSink, _RecUploader, test_drain_logs_one_line_when_not_fully_drained(), test_drain_noop_when_uploader_never_used() (+8 more)

### Community 68 - "_is_transient_network"
Cohesion: 0.11
Nodes (26): _is_transient_client_error(), _is_transient_network(), _client_error(), _target_closed(), test_agentcore_permanent_wrapping_chain_not_transient(), test_agentcore_startfailed_wrapping_chain_is_transient(), test_client_error_5xx_status_is_transient(), test_client_error_throttling_is_transient() (+18 more)

### Community 69 - "main"
Cohesion: 0.02
Nodes (69): main(), test_run_help_describes_only_the_local_backend(), test_run_help_is_available_with_cloud_backend_on_the_command_line(), test_run_without_a_feature_on_the_local_backend_is_reported_by_argument_parsing(), _det_feature(), _fake_worker_cmd(), test_assertion_votes_help_states_the_range(), test_cloud_submit_rejects_device_job_in_shared_prestep_before_touching_cloud() (+61 more)

### Community 70 - "plan"
Cohesion: 0.06
Nodes (32): FeatureContractError, parse_feature(), ParsedScenario, _scenario_line_and_example_line(), _step_keyword(), _check_run_size(), _fallback_after_tag_removed(), FeatureSource (+24 more)

### Community 71 - "LocalRunStore"
Cohesion: 0.04
Nodes (51): end_it(), script_a(), LocalRunStore, run_state_from_dict(), run_state_to_dict(), test_concurrent_reader_never_sees_torn_run_state(), _CloseAtOnce, _meta() (+43 more)

### Community 72 - "test_compose.py"
Cohesion: 0.05
Nodes (31): build_engines(), _env(), _inject_aws(), build_local_event_log(), load_feature(), make_resolver(), _name_too_long(), gherkai-runtime README (PyPI 入口页) (+23 more)

### Community 73 - "resolve_worker_cmd"
Cohesion: 0.04
Nodes (24): _ask_worker(), _leg(), _find_worker_spec(), resolve_worker_cmd(), _runtime_version(), scrubbed_environ(), _UnavailableEngine, WorkerCmd (+16 more)

### Community 74 - "time"
Cohesion: 0.05
Nodes (52): _pump_log(), _reset_scope_colors(), _scope_color(), SubprocessEngine, _assert_process_gone(), _color_env_independent(), _engine(), _grandchild_pid() (+44 more)

### Community 75 - "gherkai 变更记录 (CHANGELOG)"
Cohesion: 0.09
Nodes (28): gherkai destroy, 停止宽限下限由引擎 worker 报告, --max-concurrency 默认值 4, Midscene 默认模型 us.openai.gpt-5.6-terra, Nova Act 固定模型版本 nova-act-v1.0, gherkai deploy push-worker / list-workers, rich 渲染的人读输出, AI step（默认执行路径） (+20 more)

### Community 76 - "main"
Cohesion: 0.02
Nodes (61): _clock(), driven(), stub(), _FakeBrowserClient, _FakeCm, _FakeNovaAct, _FakePage, _Resp (+53 more)

### Community 77 - "core/tests/test_redact.py"
Cohesion: 0.11
Nodes (11): _explain_without_detail(), explain_without_detail_to_dict(), redact_deep(), redact_secrets(), test_fixture_covers_all_three_rules(), test_json_field_boundary_is_not_crossed(), test_none_passes_through(), test_redact_deep_recurses_values_and_leaves_keys_and_non_strings() (+3 more)

### Community 78 - "test_cloud_integration.py"
Cohesion: 0.09
Nodes (22): _ddb_store(), _is_ddb_too_large(), _raw_state(), _real_run(), _s3_result_store(), _set_entry_attr(), test_ddb_claim_advances_run_and_is_rejected_after_the_run_ends_real(), test_ddb_empty_string_scalar_and_map_entry_real() (+14 more)

### Community 79 - "../lib/tunnel-warmup.mjs"
Cohesion: 0.09
Nodes (24): EXTRA_HTTP_HEADERS_ENV, INCOMPLETE_DEFINITION_MESSAGE, leaveWarmupPage(), ADR-0028, ADR-0039, ADR-0051, reasonOf(), SESSION_WARMUP_KEY (+16 more)

### Community 80 - "test_cloud_reconcile.py"
Cohesion: 0.02
Nodes (52): require_boto3(), CloudLauncher, TimeoutWatch, DdbEventLog, events_pk(), FargateEngine, instant_to_iso(), job_to_line() (+44 more)

### Community 81 - "use_color"
Cohesion: 0.16
Nodes (11): color_env_override(), stream_is_tty(), use_color(), _clean_env(), _Pipe, test_broken_stream_counts_as_not_tty(), test_force_color_enables_on_pipe(), test_no_color_non_empty_wins_over_tty() (+3 more)

### Community 82 - "test_skill_deploy_tokens.py"
Cohesion: 0.11
Nodes (9): _rel(), test_scan_face_is_not_empty(), test_technical_doc_uses_written_register(), _build(), _deploy_spans(), _nodes(), walk(), test_deploy_flags_are_attached_to_the_right_subverb() (+1 more)

### Community 83 - "json"
Cohesion: 0.08
Nodes (30): collect(), main(), main(), NoRedirect, APIError, download_subtitles(), main(), NoRedirect (+22 more)

### Community 84 - "test_user_docs.py"
Cohesion: 0.06
Nodes (24): _absolute(), _default_model_claims(), _default_model_ids(), _link_targets(), walk(), _rel(), test_changelog_uses_absolute_links_only(), test_default_model_ids_match_the_engine_constants() (+16 more)

### Community 85 - "finalize.test.mts"
Cohesion: 0.06
Nodes (23): deleteAppiumSession(), emit(), emitAttempted(), finalizeOnce(), ADR-0051, ADR-0052, observedSeconds(), RELEASE_RETRY_DELAY_MS (+15 more)

### Community 86 - "handoff.py"
Cohesion: 0.09
Nodes (21): AdvancerInput, AdvancerReport, _decode(), decode_advancer_input(), decode_advancer_report(), decode_watch_input(), decode_watch_report(), _encode() (+13 more)

### Community 87 - "workers_real_aws/conftest.py"
Cohesion: 0.11
Nodes (15): env_region(), _parse(), _problem_line(), problems(), pytest_configure(), pytest_runtest_logreport(), pytest_runtest_makereport(), pytest_runtest_protocol() (+7 more)

### Community 88 - "_parse"
Cohesion: 0.05
Nodes (45): _argv(), _context_pairs(), _deploy(), _guard(), _parse(), _record_target_resolutions(), _stub_backend(), test_asset_dir_env_points_into_the_work_dir() (+37 more)

### Community 89 - "README Video Specs"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 90 - "TypeScript Build Config"
Cohesion: 0.11
Nodes (17): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+9 more)

### Community 91 - "evidence.test.mts"
Cohesion: 0.09
Nodes (21): build(), DESKTOP_SNAP, DEVICE_AI_SNAP, dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent (+13 more)

### Community 92 - "../device/limits.mjs"
Cohesion: 0.05
Nodes (38): ADDRESS_CAPTURE_BUDGET_MS, APP_PRESIGN_EXPIRES_S, BUSY_BACKOFF_CAP_MS, BUSY_BACKOFF_INITIAL_MS, CONTROLS_CAPTURE_BUDGET_MS, CONTROLS_MAX_ITEMS, DEEP_LINK_FOREGROUND_POLL_ATTEMPTS, DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS (+30 more)

### Community 93 - "Composition Root Architecture"
Cohesion: 0.11
Nodes (23): build_cloud_stores（云端三 store 装配）, build_engines（SubprocessEngine 注册表）, build_fargate_engines（云端执行引擎接线点）, build_local_stores（本地三 store 装配）, cli/gherkai_cli（纯皮：argparse + 渲染 + 分派）, compose.py（可复用组合根 / 引擎注册表）, 执行核心库 core/（窄腰，零引擎依赖）, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单一选项） (+15 more)

### Community 94 - "test_project_config.py"
Cohesion: 0.05
Nodes (57): _android_caps(), _android_env(), _app_project(), _app_run_with_another_project_elsewhere(), _assert_submitted_device_and_app_values(), _feature(), _no_match(), _plan_json() (+49 more)

### Community 95 - "test_engines_matrix.py"
Cohesion: 0.23
Nodes (5): expected_rows(), matrix_rows(), test_matrix_lists_exactly_the_two_engines(), test_matrix_rows_for_novaact_match_the_worker_self_description(), test_matrix_target_names_are_the_product_labels()

### Community 96 - "subprocess"
Cohesion: 0.09
Nodes (23): _docker_ok(), _clean_env(), test_broken_steps_dir_makes_capabilities_exit_nonzero(), test_capabilities_shape_and_min_grace_from_injected_act_timeout(), test_default_min_grace_covers_act_timeout_default(), test_does_not_read_stdin(), test_list_deterministic_flag_no_longer_recognized(), test_min_grace_tracks_both_env_knobs() (+15 more)

### Community 97 - "Video Material Files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 98 - "skill_install.py"
Cohesion: 0.17
Nodes (8): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill()

### Community 99 - "_StampSsm"
Cohesion: 0.15
Nodes (11): check_backend_skew(), read_backend_version(), _client_error(), _StampSsm, test_check_backend_skew_missing_stamp_warns_not_raises(), test_check_backend_skew_propagates_read_errors(), test_check_backend_skew_reads_stamp_then_judges(), test_read_backend_version_blank_value_is_none() (+3 more)

### Community 100 - "test_ddb_capacity.py"
Cohesion: 0.07
Nodes (11): _report_lines(), test_a_gsi_query_with_total_reports_its_units_as_unsplit_not_as_the_table(), test_a_malformed_request_still_gets_the_sdk_validation_error(), test_a_request_whose_response_has_no_consumed_capacity_is_marked_and_not_counted_as_zero(), test_a_response_with_some_index_detail_but_no_table_entry_reports_the_rest_as_unsplit(), test_a_write_with_total_that_also_writes_an_index_reports_its_units_as_unsplit(), test_an_exception_whose_response_has_an_unexpected_shape_is_raised_unchanged(), test_requests_from_other_threads_and_separately_built_sessions_are_recorded() (+3 more)

### Community 101 - "test_event_bounds.py"
Cohesion: 0.06
Nodes (43): bound_event(), bound_text(), utf8_bytes(), _where(), EventSink, redact_secrets(), _emit_step_done(), _logs() (+35 more)

### Community 102 - "决策"
Cohesion: 0.13
Nodes (15): 0048. 测试目标：设备与界面类型两个维度、`@device` 与 `@app` 标签、core 的执行前预检, 1. 测试目标由三个正交维度描述：engine、device、ui_kind, 2. 两个 scope 级 tag：`@device` 与 `@app`, 3. core 的三处改动, 4. 目标不受支持时的拒绝：由能力自述决定，消息给出改法, 5. plan 的标注, 6. 运行期网页上下文不可用：声明了前提的确定性 step 记 error，不转 AI, 7. 应用目标上的导航 step 与落点核对规则 (+7 more)

### Community 103 - "Run Store Persistence Ports"
Cohesion: 0.14
Nodes (20): Commit-point Write Order (data plane first), RunStore.create_run(), DDB Single-Table Schema (run_id + item_type), DynamoDBRunStore, Cloud Failure Exit Code Layering, RunStore.finalize_run(), RunState high_water_mark Conditional Write, JobSink Port (+12 more)

### Community 104 - "test_detached_launcher.py"
Cohesion: 0.09
Nodes (15): _assembled(), _def(), _one_hour_later(), _RecordingReports, test_assembly_goes_through_resolve_aws_identity(), test_assembly_host_env_steps_dir_does_not_leak(), test_assembly_injects_run_id_to_both_engines(), test_assembly_no_steps_dir_when_definition_has_none() (+7 more)

### Community 105 - "test_codex_review.py"
Cohesion: 0.17
Nodes (28): _brief(), _case_insensitive(), env(), _record(), _run(), _stdin_for(), test_appendix_follows_the_brief_bytes_and_the_brief_file_is_unchanged(), test_disposition_line_is_the_name_a_colon_and_one_of_the_values() (+20 more)

### Community 106 - "决策"
Cohesion: 0.08
Nodes (21): 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`, 1. 增键不给 worker 协议版本加号，在既有版本上增键, 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」, 3. step 实际可用目标是句柄声明与 worker `targets` 的交集, 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出, 5. `min_grace_s` 保持顶层单值, 6. 各消费点的呈现, 7. 云端提交时按镜像的能力核对，worker 在建会话前按自己的 `targets` 再自检 (+13 more)

### Community 107 - "决策"
Cohesion: 0.12
Nodes (17): 0052. Appium 界面适配与平台差异处理, 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名, 2. 界面接缝：run-scope 只通过一个接口操作被测对象, 3. 设备模块的划分, 4. 驱动适配器：平台专属命令只在这里出现, 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位, 6. 固定规则, 8. 护栏 (+9 more)

### Community 108 - "interface.mts"
Cohesion: 0.05
Nodes (35): AdapterEntry, adapterRegistry(), AppiumInterfaceConfig, autoDismissKeyboardDescription(), decodeXmlEntities(), descendantsOf(), DeviceAgentArgs, DISMISS_KEYBOARD_ACTION (+27 more)

### Community 109 - "AppiumInterface"
Cohesion: 0.12
Nodes (10): 7. Midscene 复用边界, AppiumInterface, createAppiumInterface(), DeviceAdapter, dismissKeyboardDescription(), isNoDismissControlError(), keyboardNotDismissedMessage(), keyboardNotHiddenLogLine() (+2 more)

### Community 110 - "_call_with_timeout"
Cohesion: 0.11
Nodes (12): _call_with_timeout(), _late(), _target(), _CallState, _CallTimedOut, test_call_with_timeout_hands_a_late_result_to_on_late_exactly_once(), fn(), on_late() (+4 more)

### Community 111 - "app.mts"
Cohesion: 0.05
Nodes (38): @aws-sdk/client-s3@^3.1074.0, APP_LAUNCH_SELF_EXIT_MESSAGE, APP_OBJECT_FORBIDDEN_MESSAGE, APP_OBJECT_MISSING_MESSAGE, APP_RESTART_SELF_EXIT_MESSAGE, APP_STATE, AppControl, appHandle() (+30 more)

### Community 112 - "codex_usage.py"
Cohesion: 0.10
Nodes (14): BadLine, _complete_objects(), load(), main(), _parse_line(), _scan_string(), _sessions(), _short() (+6 more)

### Community 113 - "build_diagrams.mjs"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 114 - "ArtifactUploader"
Cohesion: 0.12
Nodes (16): CONTENT_TYPES, contentTypeFor(), DEVICE_SESSION_BASENAME, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0032 (+8 more)

### Community 115 - "06-devicefarm-appium.mts"
Cohesion: 0.10
Nodes (59): amapSteps(), androidAppTypingProbe(), AppiumInterface, appSteps(), capProbe(), caps(), connect(), deeplinkCase() (+51 more)

### Community 116 - "_fake_locator"
Cohesion: 0.03
Nodes (48): fake(), _cloud_backend_ok(), _doctor_cloud_json(), _doctor_devices_cloud(), _every_row_checked(), _fake_locator(), _no_provider(), _provider_with_doctor() (+40 more)

### Community 117 - "_state"
Cohesion: 0.04
Nodes (38): WatchEnd, _BlockedStore, _Clock, _ClockedWait, _Daemon, _input(), _real_clock(), _Script (+30 more)

### Community 118 - "with"
Cohesion: 0.06
Nodes (33): with, body_path, build-args, cache, cache-dependency-glob, cache-dependency-path, context, enable-cache (+25 more)

### Community 119 - "_stream_record"
Cohesion: 0.08
Nodes (15): _report_bytes(), _stream_record(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_reconciler_noop_for_non_detached_run(), test_reconciler_ticks_detached_run(), test_reconciler_writes_timestamps_in_compose_clock_format(), test_run_ids_dedup_multi_scope_same_run() (+7 more)

### Community 120 - "test_adr_hygiene.py"
Cohesion: 0.10
Nodes (15): prose_lines(), _adrs(), _imports_tool_notes(), _rel(), _superseders(), test_ai_side_docs_avoid_coined_compounds(), test_ai_side_docs_take_only_tracked_skills(), test_claude_md_import_line_follows_the_writing_constraint() (+7 more)

### Community 121 - "pathlib"
Cohesion: 0.05
Nodes (38): ai_side_docs(), all_markdown(), changelog_unreleased(), classify(), code_comment_files(), comment_blocks(), comment_prose_lines(), comment_units() (+30 more)

### Community 122 - "test_reconcile.py"
Cohesion: 0.08
Nodes (45): tick(), TickOutcome, Clock, _committed_two_job_run(), _done_events(), _FailsOnSecondSave, FakeLauncher, _initial() (+37 more)

### Community 123 - "test_tunnel_cli.py"
Cohesion: 0.02
Nodes (109): advanced(), _assert_ended_by_the_interrupt(), _at_or_inside(), _break_assembly(), _break_reconcile_log(), Clock, _cloud_submit_argv(), _ended_by_the_interrupt_line() (+101 more)

### Community 124 - "test_skill.py"
Cohesion: 0.04
Nodes (38): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), is_placeholder(), skill_markdown_files(), _all_command_spans(), _allowed_flags() (+30 more)

### Community 125 - "RunPersistence"
Cohesion: 0.09
Nodes (11): spy_persistence(), RunPersistence, test_a_result_handed_over_while_the_claim_is_being_refused_is_not_saved(), refusing_claim(), test_begin_on_an_existing_run_raises_run_already_exists_and_changes_nothing(), test_on_event_only_attempted_sessions_write_nothing(), test_on_event_runs_only_on_scope_started(), test_on_event_session_opened_sets_running_and_never_writes_none_session_id() (+3 more)

### Community 126 - "run-scope.test.mts"
Cohesion: 0.04
Nodes (39): abortableAgent(), ANDROID_WEB, DESKTOP, desktopFactory(), desktopHooks(), desktopSeam(), deviceSeam(), econnreset() (+31 more)

### Community 127 - "test_provider.py"
Cohesion: 0.06
Nodes (26): classify_vpc_state(), vpc_spec_matches(), _app_context_keys(), _ctx(), _parse_destroy(), _target(), test_bare_deploy_still_parses_with_subverbs_present(), test_build_context_does_no_io() (+18 more)

### Community 128 - "实装"
Cohesion: 0.05
Nodes (34): check_running_write(), ending_applied(), ending_of_stop(), run_status_of(), RunEnding, schema_mismatch_reason(), _settled(), state_without_record() (+26 more)

### Community 129 - "InlineChildren"
Cohesion: 0.05
Nodes (14): inline_children(), InlineChild, InlineChildren, guarded(), _Proc, _RoutedStream, SpawnBeforeReport, _feature() (+6 more)

### Community 130 - "probe.mts"
Cohesion: 0.14
Nodes (26): applicationLongEdge(), AttemptFailure, ensureNative(), execScreenshot(), firstApplication(), log(), lostOutcome(), ADR-0052 (+18 more)

### Community 131 - "Media Conversion Verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 132 - "package.json"
Cohesion: 0.05
Nodes (49): bin, gherkai-worker-midscene, dependencies, @aws-crypto/sha256-js@^5.2.0, @aws-sdk/client-device-farm@^3.1150.0, @aws-sdk/client-dynamodb@^3.1081.0, @aws-sdk/credential-providers@^3.1074.0, @aws-sdk/protocol-http@^3.370.0 (+41 more)

### Community 133 - "Boundary"
Cohesion: 0.09
Nodes (18): Boundary, BoundaryCheck, check_existing_dir(), check_fd(), check_report_dir(), _close_in_child(), HoldUntilExit, test_check_existing_dir_judges_the_directory_itself_and_reads_a_missing_one_as_none() (+10 more)

### Community 134 - "run_scope.py"
Cohesion: 0.04
Nodes (36): _act_record(), _argument_text(), _attach_evidence(), _attach_traj_refs(), _clean_cell(), _collect_traj(), _cost_from_result(), _DeterministicCtx (+28 more)

### Community 135 - "_fake_gherkai"
Cohesion: 0.10
Nodes (15): _fake_gherkai(), _paths(), test_a_failed_request_with_a_table_name_that_is_not_a_string_still_appears_in_the_text_report(), fake_main(), test_a_report_path_taken_while_the_command_runs_is_not_overwritten(), test_a_report_that_cannot_be_written_changes_nothing_and_does_not_stop_the_other(), test_a_usage_error_ends_before_the_command_runs(), test_an_empty_last_evaluated_key_means_there_is_no_next_page() (+7 more)

### Community 136 - "JobSource"
Cohesion: 0.16
Nodes (7): JobSource, test_empty_s3_uri_treated_as_unset(), test_read_parses_first_line_json_from_stdin(), test_read_takes_only_first_line_not_eof(), test_s3_state_getobject(), test_s3_uri_must_be_s3_scheme(), test_s3_uri_without_key_fails_loud()

### Community 137 - "DynamoDB Events Transport ADR"
Cohesion: 0.18
Nodes (13): DynamoDB 共享 events 表作 events-out 传输, EventSink（可注入事件出口）, events 表键设计 PK=run_id#scope_id, SK=seq, events item TTL 自动过期（7 天 expires_at）, 读一致性（流式期 EC 游标 + 终读强一致）, 被拒方案：DynamoDB Streams（同步 run 语境）, 被拒方案：MSK（Kafka）, 被拒方案：SQS FIFO per-run 队列 (+5 more)

### Community 138 - "xcuitest.test.mts"
Cohesion: 0.16
Nodes (14): app(), attrs(), button(), DONE_RECT, FIXTURES, key(), keyboard(), KEYBOARD_RECT (+6 more)

### Community 139 - "决策"
Cohesion: 0.17
Nodes (12): 0053. 项目配置文件 gherkai.toml, 1. 文件定位：只有运行侧 CLI 读它，读出的值解析成具体值随 Job 走, 2. 取值顺序：选项、环境变量、配置文件、内建默认依次优先, 3. 节与键, 4. 设备选择要求显式，筛选的挑选规则确定, 5. 与 ADR 0044 覆盖链的关系：worker 侧覆盖项不进配置文件, 6. 护栏, 决策 (+4 more)

### Community 141 - "test_atomic_write.py"
Cohesion: 0.10
Nodes (14): atomic_write_json(), atomic_write_text(), hit_vanished_dir(), _write_then_replace(), ReportStore adapters (local / s3), ResultStore adapters (local / s3), RunStore adapters (local / ddb), _page() (+6 more)

### Community 142 - "devicefarm.py"
Cohesion: 0.08
Nodes (15): AmbiguousProject, DeviceFarmAccessDenied, _error_code(), is_access_denied(), list_open_sessions(), OpenSession, _project_exists(), _raise_classified() (+7 more)

### Community 143 - "main"
Cohesion: 0.05
Nodes (55): main(), session_request_name(), _assert_paired(), _check_wire_shape(), _Client, _closed(), _Cm, _job() (+47 more)

### Community 144 - "Stateless Run Core Model"
Cohesion: 0.21
Nodes (12): detached.py（local 无状态批量运行宿主）, EventLog port（无状态推进的写模型）, Job（提交给执行面的单元 = Scope）, JobResult（持有 Job 的判定结果）, Launcher port（CAS 抢占后起一个 job）, project.py（events → RunState/JobResult 纯归约投影）, reconcile.py（无状态推进 tick）, RunMeta（definition：前置身份 + Job[]） (+4 more)

### Community 145 - "test_evidence.py"
Cohesion: 0.04
Nodes (64): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), read_trajectory(), scenario_key() (+56 more)

### Community 146 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 147 - "test_user_facing_messages.py"
Cohesion: 0.06
Nodes (27): _assigned_names(), _docstring_node_ids(), _mts_emphasis_hits(), _mts_files(), _python_emphasis_hits(), _python_files(), _report_dir_sentences(), _scan_mts() (+19 more)

### Community 148 - "_settle_sentences"
Cohesion: 0.03
Nodes (48): selection_label(), selection_to_dict(), _available_step_targets(), _cmd_plan(), _plan_capabilities(), _probe_deterministic_dispatch(), _add_act(), _add_device_evidence() (+40 more)

### Community 149 - "session.test.mts"
Cohesion: 0.08
Nodes (18): assertCommonClassification(), Call, CHOICE, connectionReset(), FAKE_CREDS, FakeClock, FakeFarm, Handler (+10 more)

### Community 150 - "0050. 确定性 step 多句柄注册与测试分层"
Cohesion: 0.20
Nodes (10): 0050. 确定性 step 多句柄注册与测试分层, 1. 注册面：handler 位置按句柄种类分键, 3. 测试分层, 4. 写作方法（进 user guide 与 agent skill）, 5. 延后：确定性 step SDK, 决策, 实测依据, 背景与问题 (+2 more)

### Community 151 - "test_review_round_gate.py"
Cohesion: 0.17
Nodes (13): _gate(), _python_stub(), _run(), test_block_message_points_to_the_sending_tool_and_the_guide(), test_direct_call_at_the_start_is_blocked(), test_empty_or_malformed_input_passes(), test_every_hook_script_is_registered(), test_missing_python_passes_silently() (+5 more)

### Community 152 - "LocalResultStore"
Cohesion: 0.09
Nodes (11): LocalResultStore, _now(), _setup(), test_a_failed_save_is_retried_with_the_same_id_and_the_terminal_state_names_it(), test_crash_worker_finalizes_error(), test_grace_query_failure_never_spawns_a_worker(), test_job_timeout_stops_worker_and_attributes_timeout(), test_loop_ends_normally_when_the_record_read_for_the_report_fails() (+3 more)

### Community 153 - "deploy"
Cohesion: 0.07
Nodes (26): concurrency, cancel-in-progress, group, environment, if, permissions, runs-on, steps (+18 more)

### Community 154 - "preflight_cloud_resources"
Cohesion: 0.09
Nodes (19): check_run_list_index(), preflight_cloud_resources(), _describe_only_table(), _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap() (+11 more)

### Community 155 - "report_dir_too_long"
Cohesion: 0.12
Nodes (12): report_dir_too_long(), ReportDirNameTooLong, ReportDirPathTooLong, _path_of(), test_a_level_of_one_hundred_chinese_characters_is_answered_by_the_filesystem(), test_a_name_too_long_right_under_an_existing_dir_is_rejected(), test_a_name_too_long_under_a_parent_that_does_not_exist_yet_is_rejected(), test_an_existing_report_dir_and_short_new_levels_pass() (+4 more)

### Community 156 - "ref_node_assert"
Cohesion: 0.03
Nodes (47): ADR-0024, fixture, ADR-0024, BUILTIN, HANDLES_FIXTURE, META, ADR-0020, ADR-0022 (+39 more)

### Community 157 - "test_settle_runs.py"
Cohesion: 0.11
Nodes (18): _full_pipe(), _read_all(), _signal_while_writing_the_output(), test_run_writes_its_whole_summary_while_the_handler_is_installed(), test_settle_runs_writes_its_whole_output_while_the_handler_is_installed(), test_status_wait_writes_its_whole_display_while_the_handler_is_installed(), _child_env(), _cli() (+10 more)

### Community 158 - "run_reconcile_loop"
Cohesion: 0.09
Nodes (7): advance_local_run(), _ExitOrCutoff, LocalAdvancer, run_reconcile_loop(), SubprocessLauncher, test_loop_ends_on_a_run_ended_by_a_settling_ending_without_report(), test_report_is_generated_from_the_record_after_the_commit()

### Community 159 - "_role_statements"
Cohesion: 0.09
Nodes (18): _all_actions(), _as_list(), _bucket_lifecycle_rules(), _events_table_actions(), _role_statements(), _statements_with(), _task_role_wildcard_actions(), test_advancer_events_table_face_is_read_plus_putitem() (+10 more)

### Community 160 - ".commit_job_states"
Cohesion: 0.09
Nodes (8): _atomic_write_json(), _extras(), _job_extras(), mutate(), write(), mutate(), mutate(), _lifecycle_rank()

### Community 161 - "_build_parser"
Cohesion: 0.07
Nodes (20): _add_config_flag(), _add_device_flags(), _add_selection_flags(), _build_parser(), _finite_float(), _positive_int(), _tunnel_providers(), apply_project_config() (+12 more)

### Community 162 - "ddb_capacity.py"
Cohesion: 0.07
Nodes (24): _capacity_entries(), _cell(), _create_and_write(), _fmt(), json_report(), _line(), main(), _outcome_text() (+16 more)

### Community 163 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 164 - "shutil"
Cohesion: 0.13
Nodes (23): watch_log_path(), test_watch_log_path_is_in_the_system_temp_dir(), assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail() (+15 more)

### Community 165 - "job-source.mts"
Cohesion: 0.08
Nodes (17): ADR-0016, ADR-0032, ADR-0034, EventSink, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd() (+9 more)

### Community 166 - "read-points.test.mts"
Cohesion: 0.07
Nodes (43): ASSIGNMENT_OPERATORS, capabilitiesReads(), COMPARISON_OPERATORS, declarationNamed(), deviceFarmClientSites(), deviceSdkValueImports(), EQUALITY_OPERATORS, Exemption (+35 more)

### Community 167 - "Cooperative Stop Design"
Cohesion: 0.25
Nodes (8): 建连早期误报 engine_error 根治, handler 内零 I/O（只置标志 + 记信号号）, 安全点按「单元完成度」判定丢弃, Nova worker flag-only 协作式停止, 被拒方案：asyncio 化消除 greenlet, 被拒方案：handler raise _Terminated 穿透 with, 泄漏兜底：AgentCore 原生 session TTL, SIGINT（Ctrl-C）纳入 flag-only handler

### Community 168 - "S3StepArgumentOffloader"
Cohesion: 0.08
Nodes (11): has_pointers(), _iter_arguments(), _ref(), S3StepArgumentOffloader, _shape_error(), test_restore_translates_argument_and_pointer_shape_errors_into_contract_errors(), build_cloud_event_log(), build_cloud_run_list_store() (+3 more)

### Community 169 - ".on_job_complete"
Cohesion: 0.15
Nodes (15): _execution(), _meta(), _methods(), _state(), test_ended_run_tells_whether_this_process_made_the_run_terminal(), test_finalize_after_the_last_terminal_write_ended_the_run_does_not_use_the_stop_source(), test_finalize_end_write_refused_while_a_job_is_still_running_is_an_internal_error(), test_finalize_end_write_refused_without_a_run_state_is_not_reported_as_ended() (+7 more)

### Community 170 - "test_doc_rules_check.py"
Cohesion: 0.11
Nodes (13): gate(), run(), _git(), git_repo(), _load_guard_cli(), test_commit_gate_blocks_on_hits_and_reports_tool_failures(), test_commit_gate_picks_the_scan_by_command_form(), test_missing_path_exits_2_even_outside_every_scan_face() (+5 more)

### Community 171 - "adapters.contract.test.mts"
Cohesion: 0.05
Nodes (29): ADAPTERS, ContractCase, ContractFixture, FIXTURES, flatten(), FOREGROUND_POLL, guarded(), HIDE_METHODS (+21 more)

### Community 172 - "test_wire.py"
Cohesion: 0.04
Nodes (80): format_event(), test_format_event_omits_scope_id(), test_format_event_renders_session_events_without_endpoints(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, ScenarioDone, ScenarioStarted (+72 more)

### Community 173 - "Engine Port & Job Planning"
Cohesion: 0.33
Nodes (7): Engine port（run_scope → WorkerHandle + Event 迭代器）, FargateEngine adapter, JobSource（可注入 job 入口）, pipe 传输实现 die（worker I/O 边缘必改）, Job（一个 scope = 一个会话边界）, plan 模块（.feature → Job 列表）, select 谓词（scenario 筛选）

### Community 174 - "Scope Tag Parsing"
Cohesion: 0.29
Nodes (7): engine 解析（scope 级）, id 派生（scopeId / scenarioId 关联键）, 一个 scenario 多个 @scope 值 → 报错, scope seam（tag 分组 + engine 校验）, scope 全局命名空间（跨文件合并，撞名 warning）, timeout 解析（@timeout:N → Job.timeoutS）, uri 互异契约（重复 uri → 报错）

### Community 175 - "test_sqlite_event_log.py"
Cohesion: 0.11
Nodes (12): _log(), _path_of_exactly(), test_a_database_path_of_exactly_the_limit_opens_with_this_interpreters_sqlite(), test_append_and_read_back_events(), test_append_idempotent_same_seq(), test_every_call_closes_its_connection(), test_exit_code_none_stored(), test_exit_record_independent_keyspace() (+4 more)

### Community 176 - "agentcore-sigv4.mts"
Cohesion: 0.17
Nodes (14): main(), bedrockCompatBody(), DEFAULT_MODEL, getBaseUrl(), getRegion(), MODEL, MODEL_FAMILY_PATTERNS, modelSigner_() (+6 more)

### Community 177 - "log"
Cohesion: 0.06
Nodes (14): update_item(), browser_session_timeout_s(), _BrowserSession, _run(), _enqueue_evidence_shots(), log(), _run_session(), _StartUnresolved (+6 more)

### Community 178 - "Graceful Stop Contract"
Cohesion: 0.33
Nodes (6): act 有界返回（per-act timeout）, 引擎经 --capabilities 自报 min_grace_s, FargateWorkerHandle.stop → StopTask, grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）, 机制层：Engine adapter / WorkerHandle 把停翻成机制

### Community 179 - "Worker Termination Contract"
Cohesion: 0.33
Nodes (6): 事件流结束信号 / 存活判定迁移, exitCode 落值延迟与 MISSING 第三态, 未来演进：显式 core→worker 控制通道, Midscene worker 有序显式 cleanup handler, 逻辑层：schedule 经 worker 句柄请求停（handle.stop）, 终止契约（core 请求 worker 优雅停止）

### Community 180 - "Package URL Links"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 181 - "tunnel.py"
Cohesion: 0.07
Nodes (13): _cannot_load(), _gen_secret(), _import_sdk(), _load_sdk(), sub(), _close_late(), _one_line(), replace_origin() (+5 more)

### Community 182 - "test_persist.py"
Cohesion: 0.12
Nodes (17): _job(), _job_files(), _jr(), _local(), test_aborted_job_preserves_session_id_through_realtime_write(), test_aborted_with_none_session_does_not_resurrect_but_documents_edge(), test_claim_rejected_after_the_run_ended_elsewhere_raises_the_stop_signal(), test_claim_writes_the_claim_time_and_later_job_writes_keep_it() (+9 more)

### Community 183 - "session.mts"
Cohesion: 0.05
Nodes (45): APPIUM_SERVER_MAJOR_VERSION, AUTH_ERROR_NAMES, availabilityRank(), CallBound, CallFailure, classifyCallFailure(), classifyCreateFailure(), closestVersion() (+37 more)

### Community 185 - "test_drain_bound_applies_before_deadline_under_fail_fast"
Cohesion: 0.08
Nodes (13): test_abort_then_clean_eof_is_aborted_not_passed(), crash_gen(), test_attempted_session_without_arn_plus_abort_stays_aborted_and_lists_the_attempt(), crash_gen(), test_drain_bound_applies_before_deadline_under_fail_fast(), crash_gen(), test_fail_fast_first_then_ended_elsewhere_keeps_the_fail_fast_message(), crash_gen() (+5 more)

### Community 186 - "_Deleted"
Cohesion: 0.09
Nodes (11): _client_error(), _Deleted, _deny_describe_of(), deny(), _ecs_deleting_on_register(), _UnlistedEcs, deny(), 与 moto 不同的地方 (+3 more)

### Community 187 - "Artifact Uploader Component"
Cohesion: 0.23
Nodes (12): Act-Boundary Pre-upload, ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX Injection, Artifact Uploader Component, uploader.flush_and_cleanup(dir), Accepted Residual Un-uploaded Artifacts, Scenario-Boundary Log Pre-upload (Midscene only), Midscene uploader.snapshotLogs(logDir, seen, budgetMs), Midscene uploader.snapshotReport(path) (+4 more)

### Community 188 - "doc_rules_check.py"
Cohesion: 0.27
Nodes (6): _changed_lines(), _git(), _names(), _staged_targets(), _uncommitted_targets(), _working_tree_targets()

### Community 189 - "test_lambda_asset.py"
Cohesion: 0.09
Nodes (15): BackendStack, BackendStack._build_lambda_asset, BackendStack._worker_subnet_ids, make_stack(), asset_dir(), _fake_installed_sources(), _patch_sources(), test_asset_imports_with_only_stdlib_beside_it() (+7 more)

### Community 190 - "_settle_sentences"
Cohesion: 0.04
Nodes (33): _allowed_filesystems_text(), _filesystem_rejected_message(), _local_wait_interrupted_notice(), _report_dir_too_long_message(), _run_not_found(), _schema_mismatch_message(), _settled_but_not_shown(), _settled_notice() (+25 more)

### Community 191 - "_create"
Cohesion: 0.06
Nodes (36): _claim(), _create(), _done(), _session_by_job_write(), _session_by_projection(), test_a_job_write_after_an_end_run_changes_nothing(), test_a_job_write_for_a_job_outside_the_run_writes_nothing(), test_a_job_write_replaces_the_model_keys_of_its_entry() (+28 more)

### Community 192 - "test_report_dir_length_commands.py"
Cohesion: 0.14
Nodes (10): _everything_under(), _path_of(), _six_commands(), test_a_layer_of_one_hundred_hanzi_passes_on_apfs(), test_a_name_too_long_for_the_filesystem_is_refused(), test_a_report_dir_exactly_at_the_limit_works_end_to_end(), test_cloud_backend_and_no_report_are_not_checked(), test_six_commands_refuse_a_report_dir_one_byte_over_the_limit_in_real_processes() (+2 more)

### Community 193 - "Gherkin Parse Seam"
Cohesion: 0.50
Nodes (4): gherkin-official 第三方库 seam, keyword 判不出 → fail-fast（PlanError）, parse seam（藏 gherkin-official）, step 顺序 = 书写顺序，keyword 只决定派发

### Community 194 - "exerciseSession"
Cohesion: 0.14
Nodes (22): collapse(), CommandRecorder, contextOf(), diffIsClean(), exerciseSession(), failureLine(), fakeDriver(), finishCase() (+14 more)

### Community 195 - "_StderrScan"
Cohesion: 0.10
Nodes (7): _calls_redact(), _is_sys_module(), _is_writer(), _qualified(), _StderrScan, _sys_member(), _writes_fd2()

### Community 196 - "event-bounds.mts"
Cohesion: 0.21
Nodes (12): boundEvent(), boundText(), charStart(), DEVICE_FIELD_MAX_BYTES, DEVICE_FIELDS, MESSAGE_EVENTS, MESSAGE_MAX_BYTES, ADR-0024 (+4 more)

### Community 201 - "container_name"
Cohesion: 0.21
Nodes (7): read_task_def_stop_timeout(), _worker_container_stop_timeout(), container_name(), _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 202 - "逐条"
Cohesion: 0.09
Nodes (22): 收尾-1（adr，S）, 收尾-2（mixed，M）, 补-2（code，S）, 补-3（mixed，M）, 补-4（mixed，S）, 补-5（adr，S）, 补-8（mixed，M）, 补-9（doc，S） (+14 more)

### Community 203 - "Architecture Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, gherkai 架构图发布入口页, 执行与推进全景交互图

### Community 204 - "Slide Frame SSIM Checks"
Cohesion: 0.67
Nodes (3): slide_area_ssim_checks, at_31_seconds, first_frame

### Community 206 - "test_devicefarm_client_placement.py"
Cohesion: 0.17
Nodes (10): _imports_devicefarm_module(), _is_devicefarm_client_call(), _production(), _python_sources(), test_client_region_is_the_device_farm_region_constant(), test_core_and_lambdas_never_touch_device_farm(), test_devicefarm_client_is_constructed_only_in_the_runtime_module(), test_import_does_not_pull_boto3() (+2 more)

### Community 207 - "env"
Cohesion: 0.22
Nodes (19): steps, DIGEST, ENGINE, IMAGE, OWNER, REPO_NAME, VERSION, steps (+11 more)

### Community 208 - "_load_and_plan"
Cohesion: 0.17
Nodes (8): acquire_timeout_for(), _build_selector(), _scenario_hit(), select(), _load_and_plan(), _run_cloud_backend_message(), _selection_label(), option_origin()

### Community 210 - "web-context.mts"
Cohesion: 0.10
Nodes (18): contextNameOf(), contextNames(), LocateDeps, locateError(), locateFailure(), locateWebContext(), ADR-0039, ADR-0050 (+10 more)

### Community 211 - "test_fargate_engine.py"
Cohesion: 0.16
Nodes (19): _engine(), _job(), _spy_run_task(), _start_and_capture_env(), test_artifact_injection_kwargs_are_mandatory(), test_events_pk_composite_run_id_scope_id(), test_fargate_engine_offers_only_start_scope_and_no_engine_port(), test_start_scope_injects_artifact_s3_env() (+11 more)

### Community 213 - "app.test.mts"
Cohesion: 0.10
Nodes (18): DEVICE_SESSION_FILE, DEVICE_SESSION_REPORT_KIND, DeviceSessionRecord, ADR-0051, ADR-0052, ProviderMinutes, requireName(), ScaleSource (+10 more)

### Community 214 - "SqliteEventLog"
Cohesion: 0.14
Nodes (4): make_raw_sink(), SqliteEventLog, test_make_raw_sink_is_the_shared_writer(), test_records_reads_events_and_exits_from_one_snapshot()

### Community 217 - "EventLog"
Cohesion: 0.23
Nodes (4): event_log adapters (sqlite / ddb), EventLog, _launch(), Launcher

### Community 218 - "tunnel_host.py"
Cohesion: 0.06
Nodes (26): 小结, 逐条, 隧道（0035）与两种 `submit` 的新流程, 隧道-3（mixed，L）, _bounded_wait_s(), hold_tunnel_for_cloud_run(), map_jobs_to_tunnel(), _one_line() (+18 more)

### Community 219 - "no-device-deps.test.mts"
Cohesion: 0.06
Nodes (28): busyBackoffMs(), flushTree(), mkLogDir(), mkShots(), ADR-0029, ADR-0039, ADR-0042, ADR-0051 (+20 more)

### Community 220 - "test_tunnel.py"
Cohesion: 0.03
Nodes (62): make_tunnel(), map_origin_in_jobs(), NgrokTunnel, normalize_origin(), _reject(), policy_instant(), render_traffic_policy(), TunnelError (+54 more)

### Community 221 - "test_container.py"
Cohesion: 0.04
Nodes (32): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, resolve_container_engine(), _tail(), UnsupportedContainerEngine, _containerd_image_store() (+24 more)

### Community 222 - "_recording"
Cohesion: 0.10
Nodes (5): _recording(), load_run_state(), test_begin_writes_all_pending_initial_state(), test_on_job_complete_rejects_a_non_terminal_result_and_writes_nothing(), replace()

### Community 223 - "precheck.mts"
Cohesion: 0.21
Nodes (12): DEVICE_LABEL, ADR-0024, ADR-0049, ADR-0051, precheckJob(), precheckSchema(), precheckTarget(), spaced() (+4 more)

### Community 224 - "_explain_run"
Cohesion: 0.04
Nodes (40): _events_db_with_unfinished_scenario(), _evidence_fixture(), _explain(), _explain_cloud_stores(), _explain_job(), _explain_run(), _explain_two_job_run(), fake_build() (+32 more)

### Community 227 - "_StubEcs"
Cohesion: 0.12
Nodes (6): _mature_stub(), _StubEcs, test_cleanup_deletes_a_mature_candidate_on_the_stub(), test_cleanup_does_not_count_a_per_item_delete_failure_as_reclaimed(), test_cleanup_reports_a_delete_error_after_deregister_as_not_retryable(), test_cleanup_reports_a_deregister_error_as_retryable()

### Community 228 - "write_report_from_record"
Cohesion: 0.11
Nodes (8): write_report_from_record(), _Report, __init__(), test_generating_the_report_raises_each_failure_as_it_is_and_logs_nothing(), test_overlapping_advancers_each_commit_a_part_and_exactly_one_commits_the_run(), _run(), go(), test_report_generation_failures_are_isolated()

### Community 229 - "compose.py"
Cohesion: 0.03
Nodes (43): _aws_error_code(), make_artifacts(), cloud_run_list_location(), CloudTarget, _default_targets(), describe_revision_or_none_if_unlisted(), is_botocore_error(), _is_finite_number() (+35 more)

### Community 235 - ".finalize"
Cohesion: 0.13
Nodes (7): passing_schedule(), RunAlreadyEnded, FinalizedRun, Execution, test_finalize_after_the_stop_signal_still_reports_ended_elsewhere_when_the_run_state_is_gone(), test_found_ended_during_execution_stores_nothing_more_and_finalize_raises(), 小结

### Community 240 - "assemble_run_result"
Cohesion: 0.14
Nodes (12): assemble_run_result(), run_duration_ms(), run_totals(), generate_report_from_record(), _device_job(), _job(), totals(), test_run_totals_device_keys_follow_the_definition_when_the_verdict_list_is_incomplete() (+4 more)

### Community 241 - "03-midscene-grounding.ts"
Cohesion: 0.06
Nodes (33): ADR-0010, ADR-0012, @aws-sdk/client-bedrock-agentcore@^3.1074.0, openai@^6.3.0, playwright@1.63.0, BASE_URL, main(), makePng() (+25 more)

### Community 242 - "surface-desktop.mts"
Cohesion: 0.06
Nodes (31): ADR-0020, ADR-0028, ADR-0035, ADR-0037, ADR-0051, ADR-0052, ADR-0033, ADR-0044 (+23 more)

### Community 243 - "test_writing_the_mapping_is_followed_by_removing_retired_at_from_the_new_revision"
Cohesion: 0.07
Nodes (18): after_enumeration(), aws(), _aws_env(), _change_on_final_check(), on_describe(), Clock, _fail_default_pointer(), _failing_default_pointer_put() (+10 more)

### Community 244 - "sys"
Cohesion: 0.09
Nodes (20): emit(), main(), _on_sigterm(), capture(), _delta_s(), _describe(), _ecs(), _iso() (+12 more)

### Community 245 - "session-name.mts"
Cohesion: 0.14
Nodes (14): AGENTCORE_SESSION_NAME_MAX, DEVICE_FARM_SESSION_NAME_MAX, encode(), encodedUnits(), ADR-0024, ADR-0037, ADR-0051, RFC-3986 (+6 more)

### Community 246 - "test_stderr_redaction.py"
Cohesion: 0.07
Nodes (26): _assert_redacted(), _Outlet, _package_sources(), _plain(), _sample(), _scan_stderr(), _stderr_violations(), test_direct_writer_calls_and_method_imports_are_accepted() (+18 more)

### Community 247 - "test_package_readmes.py"
Cohesion: 0.13
Nodes (8): _hits(), test_every_package_dir_has_a_development_md(), test_github_release_body_is_for_users_only(), test_package_page_rules_catch_each_form(), test_package_summaries_are_for_users_only(), test_release_footer_rules_catch_unpinned_links(), test_root_readme_is_for_users_only(), test_shipped_readme_is_for_users_only()

### Community 248 - "app_upload.py"
Cohesion: 0.12
Nodes (7): app_object_key(), AppUploadError, _error_code(), _events(), reuse_window(), sha256_of_file(), _upload()

### Community 249 - "jobs"
Cohesion: 0.14
Nodes (13): concurrency, cancel-in-progress, group, env, NODE_VERSION, PYTHON_VERSION, UV_VERSION, jobs (+5 more)

### Community 250 - "test_names_worker.py"
Cohesion: 0.05
Nodes (30): ssm_worker_template_path(), device_farm_interactive_endpoint_resource(), device_farm_session_arn_prefix(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), _match_device_farm_project_arn(), prefix_max_len() (+22 more)

### Community 251 - "job_entry_store"
Cohesion: 0.16
Nodes (10): job_entry_store(), entry(), key_of(), path(), set_entry_key(), raw_run_store(), edit(), path() (+2 more)

### Community 252 - "device_reprobe 使用说明（Midscene 设备模块的真机重新探测）"
Cohesion: 0.05
Nodes (35): 0051. 远程访问会话生命周期与应用分发, 10. 区域、项目与权限, 11. 安全：端点脱敏与数据保留, 12. 命令的真实上界与结果未知, 14. 前提：国内消费级应用的线上包会自行退出, 1. 一个 scope 一个远程访问会话，scenario 之间不复位, 2. 时间预算：会话预算从创建起算，获取预算从 worker 开始准备设备起算，job 墙钟沿用 0034, 3. 设备解析、创建与孤儿防护 (+27 more)

### Community 253 - "Bundled JetBrains Mono WOFF2 Subsets"
Cohesion: 0.27
Nodes (13): Archify Diagram Viewer Preset (classic, showcase quality), Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Env Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram (+5 more)

### Community 254 - "xcuitest.mts"
Cohesion: 0.06
Nodes (34): ACCESSORY_DISMISS_BUTTON_QUERY, ACCESSORY_TOOLBAR_MAX_GAP, adjacentAbove(), CLEAR_INPUT_BACKSPACES, createXcuitestAdapter(), DEEP_LINK_UNSUPPORTED_MESSAGE, DISMISS_CONTROL_AMBIGUOUS_MESSAGE, DISMISS_CONTROL_VANISHED_MESSAGE (+26 more)

### Community 255 - "_Recorder"
Cohesion: 0.08
Nodes (14): context_cache_path(), _cache_env(), cdk(), _CdkWritingContext, _FakeEngine, _Recorder, test_cdk_returncode_is_passed_through(), test_context_cache_is_per_prefix() (+6 more)

### Community 256 - "项目约定"
Cohesion: 0.29
Nodes (6): graphify, 代码纪律, 工作方式, 文档纪律, 沟通, 项目约定

### Community 257 - ".execute"
Cohesion: 0.25
Nodes (3): CommandGuard, DeviceWarmup, executionFailure()

### Community 258 - "with"
Cohesion: 0.15
Nodes (13): with, cache, cache-dependency-glob, cache-dependency-path, enable-cache, fetch-depth, if-no-files-found, name (+5 more)

### Community 259 - "npm"
Cohesion: 0.15
Nodes (13): npm, pypi, if, name, needs, permissions, runs-on, id-token (+5 more)

### Community 260 - "uiautomator2.mts"
Cohesion: 0.09
Nodes (20): ANDROID_KEYCODES, APP_DID_NOT_HANDLE_ADDRESS_MESSAGE, CHROME_PACKAGE, CLEAR_INPUT_KEY_PRESSES, createUiAutomator2Adapter(), DEFAULT_SCROLL_PERCENT, extractAndroidControls(), FOREGROUND_NOT_APP_MESSAGE (+12 more)

### Community 261 - "ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）"
Cohesion: 0.06
Nodes (51): ADR 0016: 执行架构与核心库 run 模型, ADR 0019: feature tags、scope 与 engine, ADR 0026: schedule 模块（job 间并发调度 + 失败隔离 + 优雅终止）, 墙钟时长归约（step/scenario/scope/run duration_ms）, EngineResolver（按 job.engine 解析 Engine）, 失败隔离 / failFast 旋钮, 优雅终止：schedule 只调 handle.stop(grace), _heartbeat_wrap（静默 worker 心跳注入） (+43 more)

### Community 262 - "test_both_reports_come_from_the_same_snapshot_even_when_a_request_completes_after_the_command_returns"
Cohesion: 0.25
Nodes (5): ddb(), test_both_reports_come_from_the_same_snapshot_even_when_a_request_completes_after_the_command_returns(), fake_main(), hold(), unwritable_dir()

### Community 263 - "appium.test.mts"
Cohesion: 0.05
Nodes (26): @wdio/logger@10.0.0, ACQUIRE_TIMED_OUT, ANDROID_APP, budgetOf(), connector(), connectWith(), FakeClient, fakeWdio() (+18 more)

### Community 264 - "test_event_log_recording.py"
Cohesion: 0.21
Nodes (7): EventRecordingEngine, _job(), _StubEngine, test_recording_engine_appends_raw_lines_with_arrival_seq_and_forwards_the_rest(), test_recording_engine_overwrites_an_unknown_exit_code_with_the_real_one_from_the_event_stream(), test_recording_engine_writes_the_exit_record_on_nonzero_exit_and_on_stop(), test_recording_handle_waits_briefly_for_the_exit_code_when_stop_returns_before_the_process_is_reaped()

### Community 265 - "runScope"
Cohesion: 0.14
Nodes (12): cumulativeTokens(), drainArtifactQueue(), exitAfterFailure(), log(), main(), runScenario(), runScope(), runStep() (+4 more)

### Community 266 - "deterministic.py"
Cohesion: 0.04
Nodes (45): clear(), _closed_set(), deterministic(), register(), DeterministicConflict, DeterministicKeywordMismatch, _Entry, Handles (+37 more)

### Community 267 - "CONTRIBUTING.md: contributor 指南"
Cohesion: 0.18
Nodes (16): /code-health-review 入口, /doc-health-review 入口, CLAUDE.md: 项目约定（沟通/文档/代码纪律/工作方式）, doc-diagram 项目级 skill, 执行核心库窄腰 (core-library narrow waist), CONTEXT.md: 领域术语表, 护栏 (guardrail), 版本真源 (single version source) (+8 more)

### Community 268 - "serialize.py"
Cohesion: 0.04
Nodes (36): _device_keys_for_explain(), DefinitionContractError, UnsupportedDefinitionSchema, JobOutcome, _argument_from_dict(), _argument_to_dict(), _deadline_at_from_dict(), definition_from_json() (+28 more)

### Community 269 - "test_devicefarm.py"
Cohesion: 0.08
Nodes (30): project_name(), ProjectResolution, resolve_or_create_project(), verify_project(), _assert_warning(), _enter(), _project(), _stub_get_not_found() (+22 more)

### Community 270 - "test_release_notes.py"
Cohesion: 0.19
Nodes (9): _check(), _mod(), test_cli_check_exit_codes(), test_render_pins_links_to_the_tag(), test_repo_changelog_has_every_released_tag_and_unreleased(), test_repo_readme_pins_skill_install_to_changelog_top_version(), test_section_extracts_exactly_one_version(), test_section_missing_or_empty_is_an_error() (+1 more)

### Community 271 - "deploy.py"
Cohesion: 0.09
Nodes (9): add_parsers(), _add_provider_flag(), provider_entry_points(), resolve_provider(), _cmd_deploy(), _cmd_destroy(), _deploy_provider(), _peek_deploy_provider() (+1 more)

### Community 272 - "stopTimeout=120 / grace 预算校准"
Cohesion: 0.15
Nodes (14): ACT_TIMEOUT_S=120 不压（否决解法 B）, 中断产物丢失风险（容器盘停即销毁）, 孤儿产物扫盘 reaper（经分析否决）, 安全点（step_done/act 边界）提前上传 + SIGTERM handler 兜底, 关 SDK 重试 + 单次墙钟封顶（不拖爆 grace）, stopTimeout=120 / grace 预算校准, IAM 最小权限（task role 动作×资源两维收窄）, job-in S3 对象按 tag 的 7 天 lifecycle (+6 more)

### Community 273 - "check_dist_metadata.py"
Cohesion: 0.18
Nodes (8): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), sdist_whitelists(), skill_source_files(), wheel_metadata()

### Community 274 - "test_report_dir_in_output.py"
Cohesion: 0.05
Nodes (30): _disk_full(), _no_wait_save_retry(), _stage_a_finished_job(), test_background_advancer_exits_1_with_one_sentence_when_saving_the_detail_keeps_failing(), advance_from_half_way(), test_run_interrupt_during_a_save_retry_that_fails_exits_by_the_storage_failure(), signal_then_disk_full(), fail_once() (+22 more)

### Community 275 - "ci.yml"
Cohesion: 0.18
Nodes (10): concurrency, cancel-in-progress, group, env, NODE_VERSION, PYTHON_VERSION, UV_VERSION, name (+2 more)

### Community 278 - "error-text.mts"
Cohesion: 0.29
Nodes (6): errorText(), ADR-0042, oneLineError(), W_EDGES, W_ONLY, W_RUN

### Community 279 - "image-gate"
Cohesion: 0.18
Nodes (11): name, needs, permissions, runs-on, image-gate, release, contents, name (+3 more)

### Community 280 - "_definition_header_gate"
Cohesion: 0.14
Nodes (13): _definition_contract_message(), _definition_header_gate(), _definition_schema_gate(), 小结, 查看-3（mixed，M）, 查看-4（code，M）, 查看-5（mixed，M）, 查看-6（mixed，S） (+5 more)

### Community 281 - "User Guide 入口"
Cohesion: 0.11
Nodes (45): gherkai 变更记录 (CHANGELOG), --expose-local 隧道模式, gherkai-deploy-aws README (AWS 部署 provider), detached 标记（后台 run 分界线）, 同一条事件流的四条物理通道, events 表的两个键空间（seq 段与退出记录）, exit-observer Lambda（退出观察）, job 超时预算（三路同形态 enforce） (+37 more)

### Community 282 - "test_lambda_handlers.py"
Cohesion: 0.06
Nodes (20): _described(), _detail_with_times(), _exit_item(), _iso_z(), _runs_stream_record(), test_exit_from_task_reads_one_exit_time_from_the_event_and_from_describe_tasks(), test_exit_from_task_skips_a_time_string_without_a_time_zone(), test_extract_missing_env_returns_none() (+12 more)

### Community 285 - "逐条"
Cohesion: 0.17
Nodes (12): 行为文档-10（doc，M）, 行为文档-16（doc，M）, 行为文档-17（doc，S）, 行为文档-19（doc，S）, 行为文档-2（doc，L）, 行为文档-4（doc，S）, 行为文档-5（doc，M）, 行为文档-6（mixed，M） (+4 more)

### Community 286 - "_assert_usage_error"
Cohesion: 0.29
Nodes (4): _assert_usage_error(), test_a_report_target_that_is_not_a_plain_file_is_rejected_before_the_command_runs(), test_an_existing_report_that_cannot_be_removed_is_a_usage_error_and_the_command_does_not_run(), test_two_paths_that_name_the_same_file_through_an_alias_are_a_usage_error()

### Community 287 - "image-gate"
Cohesion: 0.20
Nodes (10): name, needs, runs-on, strategy, artifact, engine, image-gate, include (+2 more)

### Community 288 - "include"
Cohesion: 0.22
Nodes (10): strategy, strategy, artifact, context, engine, index, package, include (+2 more)

### Community 289 - "warmup.mts"
Cohesion: 0.18
Nodes (16): attempt(), AttemptResult, createDeviceWarmup(), DeviceWarmupDeps, findWarmupMarker(), leaveWarmupPage(), MARKER_ORDER, ADR-0028 (+8 more)

### Community 290 - "_stopped_detail"
Cohesion: 0.12
Nodes (9): _stopped_detail(), test_exit_from_task_is_shared_by_observer_and_timeout_handler(), test_exit_observer_records_exit_for_detached_run(), test_exit_observer_skips_non_detached_run(), test_extract_missing_exitcode_becomes_platform_sentinel_with_reason(), test_extract_missing_exitcode_without_any_reason_still_gets_sentinel(), test_extract_nonzero_exit(), test_extract_run_scope_exit() (+1 more)

### Community 292 - "_wire_capture"
Cohesion: 0.29
Nodes (5): fake_main(), _seed(), test_a_caller_that_asks_for_consumed_capacity_keeps_its_own_setting_and_response(), test_adds_the_parameter_records_each_request_and_leaves_the_response_as_the_caller_expects(), _wire_capture()

### Community 293 - "test_settle_runs.py"
Cohesion: 0.07
Nodes (17): _alive(), _hold_dir(), holders(), _lock_state(), _run_endings(), sigint_ignored(), _sigint_right_after_restoring_it(), test_ctrl_c_while_printing_the_result_lets_the_output_finish_once() (+9 more)

### Community 294 - "steps"
Cohesion: 0.39
Nodes (9): steps, ENGINE, steps, steps, steps, env, name, run (+1 more)

### Community 295 - "test_workers.py"
Cohesion: 0.04
Nodes (68): _at(), _failing_mapping_put(), FakeContainer, _mapping(), _out(), _push(), seed_backend(), _share_with_old_version() (+60 more)

### Community 296 - "test_a_record_failure_that_comes_with_an_interrupt_ends_as_the_failure"
Cohesion: 0.29
Nodes (3): _signal_after_listing(), list_runs(), test_a_record_failure_that_comes_with_an_interrupt_ends_as_the_failure()

### Community 298 - "test_plan_target_check_degrades_when_capabilities_unavailable"
Cohesion: 0.25
Nodes (3): test_plan_shows_device_target_and_session_count_when_engine_supports_it(), no_match(), test_plan_target_check_degrades_when_capabilities_unavailable()

### Community 299 - "commit_applied"
Cohesion: 0.12
Nodes (5): _recording_build_local_stores(), commit_job_states(), end_run(), commit_applied(), _committed()

### Community 300 - "test_load_definition_only_logs_when_the_error_ending_finds_the_run_state_unreadable"
Cohesion: 0.13
Nodes (8): _claimed_detached_run(), test_build_ends_the_run_with_the_error_ending_when_definition_lacks_worker_task_defs(), test_load_definition_only_logs_when_the_error_ending_finds_the_run_state_unreadable(), end_run_as_error(), load_run_meta(), test_task_exiting_on_its_own_is_judged_by_its_exit_time_through_the_real_tick(), test_timeout_handling_keeps_an_exit_record_written_while_it_lists_tasks(), list_tasks()

### Community 301 - "_Store"
Cohesion: 0.17
Nodes (4): any_store(), _Store, load_run_state(), load_run_state()

### Community 302 - "推进权与状态投影：ADR 写回的结果与实装线索"
Cohesion: 0.18
Nodes (11): owner 定的写回口径, owner 的裁定与落实, 另一家模型核落到位, 各批用时与轮数, 实装之前的一批：Status 头清理, 推进权与状态投影：ADR 写回的结果与实装线索, 现在做不了、到时机要做的事项, 留下的问题与缺省 (+3 more)

### Community 303 - "device/surface.test.mts"
Cohesion: 0.06
Nodes (13): ADR-0051, APP_PREPARE_TIMEOUT, HANGING_VARIANTS, harness(), HarnessOptions, LOST_BEFORE_START, makeJob(), ADR-0050 (+5 more)

### Community 304 - "reconciler.py"
Cohesion: 0.05
Nodes (33): _event_log(), _extract(), handler(), _is_detached(), EventBridgeTimeoutWatch, exit_from_task(), _handle_timeout(), _check() (+25 more)

### Community 305 - "warmup.test.mts"
Cohesion: 0.04
Nodes (32): webdriverio@10.0.2, ADR-0044, ADR-0052, fakeSession(), HERE, ADR-0052, probeWith(), Script (+24 more)

### Community 306 - "image_token_probe：截图缩放后的图片 token 探针"
Cohesion: 0.50
Nodes (3): image_token_probe：截图缩放后的图片 token 探针, 读数, 运行

### Community 307 - "./deterministic.mjs"
Cohesion: 0.04
Nodes (43): ADR-0025, BUILTIN_KINDS, BuiltinKind, DeterministicAssertion, DeterministicHandler, DeterministicHandlers, DeterministicMeta, Device (+35 more)

### Community 308 - "_FakeSchedulerClient"
Cohesion: 0.15
Nodes (7): _FakeSchedulerClient, exceptions, ConflictException, test_timeout_watch_at_is_the_given_cutoff(), test_timeout_watch_conflict_is_idempotent(), test_timeout_watch_creates_one_time_schedule(), test_timeout_watch_name_is_exactly_64_chars_at_prefix_limit()

### Community 309 - "test_both_advancers_get_the_same_non_empty_worker_subnets"
Cohesion: 0.25
Nodes (4): _advancer_env(), _joined_refs(), test_both_advancers_get_the_same_non_empty_worker_subnets(), test_both_advancers_get_the_worker_security_group()

### Community 310 - "e2e_harness.py"
Cohesion: 0.16
Nodes (11): ADR 0025 @scope: tag 分组, ADR 0032 Fargate 中断丢失量级与真容器 grace 校准, --interrupt 中断时机矩阵, e2e_harness.py（opt-in 手动端到端验证脚本）, harness 报告判读要点（sample_valid 先于 n_lost）, run(), do_kill(), _watchdog() (+3 more)

### Community 312 - "LazyDdb"
Cohesion: 0.17
Nodes (3): LazyDdb, call(), wait_table_active()

### Community 313 - "pipe_results"
Cohesion: 0.40
Nodes (4): pipe_results(), direct(), wrapped(), _spawn()

### Community 314 - "parent-watchdog.mts"
Cohesion: 0.29
Nodes (6): ADR-0024, ownerPidFromEnv(), PARENT_PID_ENV, PARENT_POLL_MS, ParentWatchdogDeps, startParentWatchdog()

### Community 316 - "test_compose.py"
Cohesion: 0.04
Nodes (50): check_version_skew(), nova_act_timeout_s(), resolve_aws_identity(), resolve_cloud_target(), resolve_region(), _clear_aws_env(), fresh_caps_cache(), fresh_nova_timeout() (+42 more)

### Community 317 - "test_handle_timeout_finds_stopped_target_on_second_page"
Cohesion: 0.33
Nodes (3): _stopped_filler(), test_handle_timeout_finds_stopped_target_on_second_page(), test_handle_timeout_pages_task_lists_and_batches_describe()

### Community 318 - "_DeviceFarmStub"
Cohesion: 0.13
Nodes (4): _clean_aws_env(), _DeviceFarmStub, df(), _Ssm

### Community 319 - ".from_env"
Cohesion: 0.33
Nodes (3): test_bucket_without_logs_dir_fails_loud(), test_from_env_enabled_when_bucket_set(), test_from_env_noop_when_no_bucket()

### Community 320 - "severity 数值序（_STATUS_SEVERITY）"
Cohesion: 0.32
Nodes (8): 退出码基于 run 级 severity, _NON_VERDICT 与 _aggregate 入口过滤, severity 数值序（_STATUS_SEVERITY）, Status.ABORTED（core 派生态）, Status.PENDING / RUNNING（生命周期前置态）, Status.SKIPPED（core 派生态）, step 级短路：step_skipped 事件 + shortcircuited 布尔, TERMINAL_STATUSES（终态真源，取补定义）

### Community 322 - "test_ctrl_c_before_the_settle_of_a_given_run_changes_nothing"
Cohesion: 0.14
Nodes (7): _count_settles(), settle_run(), sleep(), test_ctrl_c_before_the_settle_of_a_given_run_changes_nothing(), test_status_wait_ctrl_c_while_waiting_stops_within_one_slice(), on_poll(), test_status_wait_record_failure_that_comes_with_an_interrupt_ends_as_the_failure()

### Community 323 - "jobs"
Cohesion: 0.29
Nodes (7): name, runs-on, jobs, build-smoke, python, name, runs-on

### Community 325 - "runtime/tests/conftest.py"
Cohesion: 0.21
Nodes (4): ClosingLockHolder, _host_independent_filesystem_type(), lock_holder(), _no_real_tunnel_sdk()

### Community 326 - "staging_names"
Cohesion: 0.15
Nodes (7): is_run_name(), is_staging_name(), staging_names(), test_every_generated_staging_name_has_the_recognized_shape(), test_is_run_name(), test_is_staging_name_accepts_only_the_generated_shape(), test_staging_names_lists_only_the_shape_and_reads_a_missing_root_as_empty()

### Community 329 - "register"
Cohesion: 0.33
Nodes (6): closedSet(), deterministic(), normalizeHandlers(), normalizeKeywords(), register(), registerBuiltin()

### Community 330 - "bin.mts"
Cohesion: 0.10
Nodes (15): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037, ADR-0051, ADR-0037, engineRequire (+7 more)

### Community 331 - "_SpyRunStore"
Cohesion: 0.17
Nodes (7): _CountingEventLog, _meta(), _SpyRunStore, test_all_done_after_the_deadline_ends_by_the_terminal_write(), load_run_state(), test_no_writes_and_no_event_reads_in_a_round_that_cannot_read_the_run_state(), 测-4（test，M）

### Community 332 - "node"
Cohesion: 0.33
Nodes (6): run, node, defaults, name, runs-on, working-directory

### Community 333 - "_Party"
Cohesion: 0.08
Nodes (15): lingering_party_threads(), _parties(), _Party, _party_under_broad_except(), target(), _PartyStopped, test_aborted_party_held_under_a_broad_except_issues_no_further_call_and_has_ended(), test_hold_timeout_does_not_let_a_party_under_a_broad_except_go_on() (+7 more)

### Community 334 - "build"
Cohesion: 0.33
Nodes (6): name, outputs, permissions, runs-on, build, version

### Community 335 - "images"
Cohesion: 0.33
Nodes (6): name, needs, permissions, runs-on, images, packages

### Community 336 - "_BucketRegionObserver"
Cohesion: 0.15
Nodes (4): _BucketRegionObserver, _ClientError, _Request, test_bucket_region_observer_records_the_signing_region_of_the_last_request()

### Community 337 - ".attempt"
Cohesion: 0.47
Nodes (3): Lifecycle, probeFacts(), valueOf()

### Community 338 - "test_main.py"
Cohesion: 0.01
Nodes (151): _assert_identity_error(), _assert_left_running(), _capturing_schedule(), _deadline_mid_run(), script_a(), _deadline_offset_s(), _detail_files(), _end_locally() (+143 more)

### Community 339 - "_variant_miss_hint"
Cohesion: 0.15
Nodes (7): is_pure_release(), _release_cmp(), _release_key(), _variant_miss_hint(), test_pure_release_predicate(), test_variant_miss_hint_offers_push_and_base_fallback(), test_variant_miss_hint_older_cli_only_guides_upgrade()

### Community 341 - "逐条"
Cohesion: 0.25
Nodes (8): 小结, 注释-2（code，S）, 注释-5（code，M）, 注释-8（mixed，S）, 注释-9（mixed，S）, 线索没有覆盖的改动点, 逐条, 随实装改写的 code 注释（指针已处理，行为描述待改）

### Community 342 - "Fargate/ECS RunTask 执行后端"
Cohesion: 0.50
Nodes (4): AgentCore Runtime（被否的执行面选项）, 批处理 workload shape 判据, Fargate/ECS RunTask 执行后端, 翻盘条件：workload 变长驻服务

### Community 343 - "codex_review.py"
Cohesion: 0.26
Nodes (6): codex_args(), _fail(), _is_the_brief(), main(), missing_marks(), with_appendix()

### Community 344 - "skipif"
Cohesion: 0.18
Nodes (5): test_settle_runs_stops_at_a_record_it_cannot_read_and_keeps_what_it_did(), test_settle_runs_that_cannot_list_does_not_say_there_is_nothing(), test_settle_runs_that_stops_before_settling_any_listed_run_does_not_say_there_is_nothing(), test_status_without_wait_exits_2_when_the_record_cannot_be_read(), test_darwin_read_back_that_fails_the_sanity_check_cannot_be_judged()

### Community 345 - "on"
Cohesion: 0.40
Nodes (5): on, pull_request, push, workflow_dispatch, branches

### Community 347 - "diffAgainstFixture"
Cohesion: 0.60
Nodes (5): diffAgainstFixture(), flatten(), formOf(), isCapabilityUnavailable(), unavailableCaseCheck()

### Community 348 - "移动真机支持（1.5）：实施进度总纲"
Cohesion: 0.18
Nodes (7): documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总）, 移动真机支持（1.5）：实施进度总纲, 遗留项, 写回时去掉的注释指针：实装跟上之后加回, 写回时核过一遍的（151）, 没有核过的（126）, 语义一致随实装核对：范围与清单

### Community 351 - "_staging"
Cohesion: 0.22
Nodes (8): _fail_opening_the_staging_directory(), open_(), _staging(), mkdir(), mkdir(), open_(), mkdir(), mkdir()

### Community 353 - "S3 Key Mirrors Local Run Tree"
Cohesion: 0.50
Nodes (4): S3 Key Mirrors Local Run Tree, S3ReportStore (no artifact copy, href==ref), Upload Whole Artifact Directory (type-agnostic), S3ReportStore

### Community 354 - "test_interrupt_process.py"
Cohesion: 0.24
Nodes (3): _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal(), test_worker_runs_until_signaled()

### Community 356 - "WebdriverCtx"
Cohesion: 0.33
Nodes (3): 2. handler 上下文：七个字段与一条不变量, WebdriverApp, WebdriverCtx

### Community 357 - "_fake_store_ctors"
Cohesion: 0.20
Nodes (4): _fake_store_ctors(), _rec(), test_build_cloud_stores_builds_handles_when_not_injected(), test_build_cloud_stores_uses_injected_handles_without_building_clients()

### Community 361 - "parametrize"
Cohesion: 0.07
Nodes (23): test_bare_wp_rule_shape(), test_dangling_journey_rule_shape(), test_machine_coordinate_rule_shape(), _row(), _settle(), _staging(), _state(), test_a_real_sigint_just_before_the_output_still_prints_what_was_done() (+15 more)

### Community 362 - "match"
Cohesion: 0.22
Nodes (7): DeterministicConflict, DeterministicKeywordMismatch, isMatchItem(), match(), matchBatch(), MatchInputError, scan()

### Community 364 - "RunStateWriteContended"
Cohesion: 0.22
Nodes (3): RunListingIncomplete, RunStateWriteContended, RunListIndexUnavailable

### Community 365 - "test_wire.py"
Cohesion: 0.07
Nodes (26): _join_pumps(), _read_events(), WorkerNetworkError, StepSkipped, _argument_to_json(), _device_request_to_json(), event_from_line(), job_to_json() (+18 more)

### Community 369 - "_DeviceFarmStub"
Cohesion: 0.10
Nodes (9): _botocore_like(), _Cfn, _ClientError, test_deploy_relays_the_not_found_warning_even_when_resolution_then_fails(), test_guard_unexpected_read_error_exits_2_not_traceback(), boom(), test_stack_not_found_detection_needs_both_code_and_text(), describe_stacks() (+1 more)

### Community 372 - "progress"
Cohesion: 0.03
Nodes (49): progress(), resolve_local_app_bucket(), _aws_identity(), _check_report_dir_boundary(), _check_tunnel_prerequisites(), _cmd_run(), _cmd_status(), _cmd_status_body() (+41 more)

### Community 375 - "./deterministic.steps.mjs"
Cohesion: 0.07
Nodes (21): ADR-0053, ADDRESS_PATTERN, DeviceNavigate, ADR-0020, ADR-0022, ADR-0036, ADR-0037, ADR-0048 (+13 more)

### Community 378 - "Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障"
Cohesion: 0.25
Nodes (9): 1. 链路一句话, 2. 签名契约：五条决定成败的细节, 3. 失败模式表, 4. 依赖与自检, Midscene 调 Bedrock 的 SigV4 自签：签什么、不签什么、怎么排障, 延伸阅读, createSurface(), modelConfig() (+1 more)

### Community 379 - "逐条"
Cohesion: 0.22
Nodes (9): 小结, 测-10（test，M）, 测-11（test，L）, 测-12（test，M）, 测-2（test，M）, 测-8（test，S）, 测试, 线索没有覆盖的改动点 (+1 more)

### Community 380 - "_make_devicefarm_client"
Cohesion: 0.22
Nodes (4): _make_devicefarm_client(), df(), _isolated_aws_env(), ssm()

### Community 383 - "render_skill_contract.py"
Cohesion: 0.21
Nodes (7): docs/internals/cli-json-contract.md（机读字段级参考页）, _assert_clean(), main(), _paragraphs(), render(), transform(), TransformError

### Community 384 - "release_notes.py"
Cohesion: 0.39
Nodes (4): main(), render(), section(), skill_install_tag_problems()

### Community 387 - "test_list_workers_json_keys_match_contract_doc"
Cohesion: 0.29
Nodes (4): _documented_keys(), _sections(), test_list_workers_json_keys_match_contract_doc(), leaf_keys()

### Community 388 - "test_context_glossary.py"
Cohesion: 0.47
Nodes (3): _entries(), test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 389 - "test_finalize_after_the_stop_signal_still_reports_ended_elsewhere_when_the_read_back_fails"
Cohesion: 0.33
Nodes (3): test_finalize_after_the_stop_signal_still_reports_ended_elsewhere_when_the_read_back_fails(), test_finalize_read_failure_after_the_run_ended_propagates_without_a_report(), failing_read()

### Community 395 - "test_snapshot_sees_what_the_real_run_store_writes_until_the_run_finishes"
Cohesion: 0.40
Nodes (3): _defined_job(), test_snapshot_sees_what_the_real_run_store_writes_until_the_run_finishes(), create()

### Community 396 - "词表与退役词"
Cohesion: 0.40
Nodes (5): 小结, 线索没有覆盖的改动点, 词表-1（mixed，M）, 词表与退役词, 逐条

### Community 397 - "行为文档（随所改行为的实装批同一提交改）"
Cohesion: 0.40
Nodes (4): 小结, 线索没有覆盖的改动点, 行为文档（随所改行为的实装批同一提交改）, process_lock_holder()

### Community 402 - "_index_ast_lines"
Cohesion: 0.67
Nodes (3): _index_ast_lines(), record(), record_children()

### Community 406 - "default_name"
Cohesion: 0.50
Nodes (3): default_name(), test_default_name_prefix_original_concat(), test_project_name_is_prefix_plus_base()

### Community 411 - "收尾"
Cohesion: 0.67
Nodes (3): 小结, 收尾, 线索没有覆盖的改动点

### Community 414 - "config.py"
Cohesion: 0.07
Nodes (30): AppPlatformConfig, _apps_section(), _billing_method(), ConfigError, DevicePlatformConfig, _devices_section(), DevicesConfig, load_project_config() (+22 more)

### Community 432 - "ADR 0043: 随 CLI 发行的 agent skill"
Cohesion: 0.05
Nodes (46): gherkai agent skill 包, 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志）, 退出观察者（ECS STOPPED → task_exited）, job timeout（两层声明 → definition 载体 → 三路 enforce）, kicker Lambda（冷启动推进器）, plan_next（纯决策：该启哪些 pending、是否 finalize）, project（纯归约：events + baseline → RunState） (+38 more)

### Community 456 - "gherkai_runtime/__init__.py"
Cohesion: 0.13
Nodes (8): ClosingLockHolder, _host_independent_filesystem_type(), lock_holder(), _no_real_tunnel_sdk(), _presentation_is_environment_independent(), _signal_dispositions_are_restored(), _stub_engine_capabilities(), fake_query_capabilities()

### Community 457 - "_mk_state"
Cohesion: 0.17
Nodes (9): _args(), _mk_state(), test_render_status_json_no_hint(), test_render_status_prints_the_given_hint_only_without_wait_and_json(), test_render_status_running_no_hint(), test_render_status_shows_run_level_message_in_text_and_json(), test_render_status_terminal_no_hint_and_exitcode(), test_render_status_terminal_prints_artifact_locations() (+1 more)

### Community 458 - "决策"
Cohesion: 0.14
Nodes (14): 0054. 运行期限、生命期锁与 run 处置：每个 run 遵守由 job 预算推出的期限；本机 run 由持有生命期锁的进程推进，死活由锁回答；run 结束之后记录不变、不再接受新的认领；管它的进程不在了、或已过期限加 300 秒的 run 可由处置方结束, 一、定位与范围, 七、处置做什么, 三、生命期锁：加在 run 目录上, 五、终态不可变，执行方服从记录：run 结束之后不再接受新的认领, 六、死活的判断与处置的条件, 决策, 十、job 的墙钟预算有一个产品定的上限 (+6 more)

### Community 459 - "test_tick_runs_writes_the_report_from_the_record_when_its_tick_commits"
Cohesion: 0.33
Nodes (3): _StateStub, _stub_tick_runs_host(), test_tick_runs_branches_on_tick_outcome()

### Community 461 - "surface.mts"
Cohesion: 0.05
Nodes (43): AcquireResult, AddressReading, attachClassification(), CLASSIFICATION_KEY, ControlItem, Controls, ControlsMissing, DeviceSurfaceModule (+35 more)

### Community 463 - "test_cli_json_contract.py"
Cohesion: 0.07
Nodes (26): build_device_request(), _assert_check_names_documented(), _assert_documented(), _assert_list_runs_value_types(), _device_selections(), _documented_keys(), _mk(), _plan_form() (+18 more)

### Community 464 - "gherkai_deploy_aws/names.py"
Cohesion: 0.12
Nodes (6): main(), ssm_version_path(), stack_name(), test_device_farm_and_app_names_are_reexported_from_runtime(), test_ssm_device_farm_project_path_is_the_shared_key(), test_version_context_is_required()

### Community 467 - "instant_to_iso"
Cohesion: 0.10
Nodes (18): _committable(), instant_from_iso(), _job_cutoff(), test_tick_runs_writes_the_report_from_the_record_when_its_tick_commits(), compute_deadline_at(), local_per_job_tail_s(), run_times(), RunTimes (+10 more)

### Community 471 - "_FakeTime"
Cohesion: 0.04
Nodes (38): WorkerExitError, _FakeTime, _JumpSink, _outcome(), _rm_at(), _StopWindowTime, test_cutoff_is_the_earlier_of_budget_and_run_deadline(), test_deadline_passed_at_the_moment_of_decision_wins_over_ended_elsewhere() (+30 more)

### Community 473 - "输入契约：一个 scope 的 Job（展开后的有序 step）"
Cohesion: 0.50
Nodes (4): assertionVotes 投票次数, {id, name} 双标识, 输入契约：一个 scope 的 Job（展开后的有序 step）, votes 只记 tally 不记 per-vote 序列

### Community 478 - "test_build_reuses_its_own_handles_and_builds_no_new_client"
Cohesion: 0.33
Nodes (3): test_build_reuses_its_own_handles_and_builds_no_new_client(), test_tick_runs_isolates_defensive_scan_failure(), _boom()

### Community 484 - "harness.py"
Cohesion: 0.06
Nodes (39): after_each_test(), aws(), _aws_env(), _batch_put(), _client_config(), _conftest(), _delete_repo(), _delete_ssm() (+31 more)

### Community 497 - "推进权与状态投影：实装线索逐条对到 code 的摸底"
Cohesion: 0.12
Nodes (16): 删除过程文档之前找到、ADR 里还没有的内容, 判定明细点名与落库写序, 小结, 小结, 小结, 报告, 推进权与状态投影：实装线索逐条对到 code 的摸底, 本机推进器、生命期锁与边界检查 (+8 more)

### Community 512 - "build_fargate_engines"
Cohesion: 0.13
Nodes (7): build_fargate_engines(), cloud_artifact_locations(), _normalize_prefix(), test_fargate_engines_carry_session_warmup_url_in_extra_env_only_when_given(), test_fargate_engines_leave_run_id_to_the_engine_adapter(), test_engine_absent_from_mapping_gets_throwing_placeholder(), test_worker_task_defs_is_required()

### Community 516 - "_signal_inside_end_run"
Cohesion: 0.09
Nodes (14): ensure(), _signal_inside_end_run(), end_run(), _signal_inside_sweep(), sweep(), test_settle_runs_keeps_an_ignored_sigint_ignored(), test_settle_runs_with_sigint_ignored_still_records_sigterm(), test_sigterm_during_a_settle_is_handled_like_ctrl_c_and_exits_143() (+6 more)

### Community 570 - "_FakeRecord"
Cohesion: 0.04
Nodes (19): _StartsStopped, _StopStart, _FakeRecord, test_claim_failure_is_a_persistence_failure(), a_gen(), test_claim_rejected_concurrently_keeps_the_other_queued_job_unclaimed(), test_claim_rejected_for_one_job_stops_the_other_running_job(), a_gen() (+11 more)

### Community 579 - "test_launch_failure_after_the_cutoff_projects_as_timeout"
Cohesion: 0.12
Nodes (10): _at(), BoomLauncher, _claimed(), launch(), test_cutoff_is_capped_by_the_run_deadline(), test_launch_failure_after_the_cutoff_projects_as_timeout(), test_launch_failure_records_unknown_exit_with_the_same_reason_as_the_foreground(), test_replan_counts_the_jobs_claimed_earlier_in_the_round() (+2 more)

### Community 614 - "ADR 0024: worker–core 协议"
Cohesion: 0.08
Nodes (95): cli/DEVELOPMENT.md, cli 包 contributor 文档, gherkai 命令行发行包入口页, agent skill (gherkai skill), 无状态批量运行 (stateless batch execution), core 包 contributor 文档, core 测试说明（单测 + 集成测试）, gherkai-deploy-aws contributor 手册 (+87 more)

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
- **500 isolated node(s):** `AdapterRegistry`, `AddressAttempt`, `AgentFactory`, `AppiumConnector`, `CapabilityProbe` (+495 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 6876 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **238 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Midscene 引擎开发笔记（contributor）` connect `架构总览：五层结构、一次 run 的生命周期、包与发行物` to `ADR 0024: worker–core 协议`, `bin.mts`, `User Guide 入口`, `device_reprobe 使用说明（Midscene 设备模块的真机重新探测）`, `CONTRIBUTING（contributor 入口）`?**
  _High betweenness centrality (0.181) - this node is a cross-community bridge._
- **Are the 308 inferred relationships involving `Status` (e.g. with `_build_parser()` and `_cmd_list_runs()`) actually correct?**
  _`Status` has 308 INFERRED edges - model-reasoned connections that need verification._
- **What connects `AdapterRegistry`, `AddressAttempt`, `AgentFactory` to the rest of the system?**
  _500 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `guard.mts` be split into smaller, more focused modules?**
  _Cohesion score 0.0539906103286385 - nodes in this community are weakly interconnected._
- **Why does `tsx` connect `package.json` to `bin.mts`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `终止契约（core 请求 worker 优雅停止）` and `step 顺序 = 书写顺序，keyword 只决定派发`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `Cloud Backend Upgrade Windows Diagram` and `Cloud Delivery Identity Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._