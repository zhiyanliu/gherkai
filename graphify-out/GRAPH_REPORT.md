# Graph Report - yaozhou  (2026-10-09)

## Corpus Check
- 350 files · ~547,186 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5678 nodes · 12580 edges · 266 communities (200 shown, 66 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 752 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a124e104`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_schedule.py
- test_lambda_handlers.py
- ADR 0016 执行架构与分层
- test_main.py
- Cloud Backend CLI Tests
- Job
- WorkerSelfDescribeError
- test_workers.py
- workers.py
- build_cloud_stores
- test_plan.py
- gherkai_cli/__main__.py
- build_local_reconcile
- _run_step
- Provider
- _StampSsm
- _fake_locator
- test_stack.py
- test_evidence.py
- Deploy Command Frontend Tests
- gherkai《价值与方法》讲者备注
- RunState
- 用户指南：配置（环境变量与通用选项）
- LocalReportStore
- test_cloud_reconcile.py
- test_project.py
- Nova Worker Library Setup
- main
- test_worker_variant.py
- run_scope.py
- test_skill.py
- cli.py
- Skill Fixture Materialization
- test_conditional_writes.py
- test_subprocess_engine.py
- ADR 0041 面向 agent 的 CLI 可用性
- atomic_write_json
- test_interrupt_model.py
- evidence.py
- test_event_sink.py
- test_tunnel_cli.py
- test_argument.py
- 架构全景（internals）
- compose.py
- query_capabilities
- scope.py
- render.py
- RunPersistence
- test_user_docs.py
- ../lib/agentcore-sigv4.mjs
- ./run-scope.mjs
- textui.py
- _RecUploader
- test_fargate_engine.py
- BackendStack
- _FakeEcsClient
- evidence.mts
- Artifact Upload Tests
- _doc_rules.py
- ADR 0028: 瞬时网络/SSL 韧性
- _is_transient_network
- _cmd_doctor
- test_compose.py
- ADR 0043 驱动 gherkai 的 agent skill
- _explain
- reconciler.py
- Artifact Uploader (Python)
- Status
- .add_arguments
- Version Skew Checking
- test_lambda_asset.py
- user-steps.mts
- test_user_steps.py
- FargateEngine
- RunStore
- test_cli_json_contract.py
- TypeScript Build Config
- test_stores.py
- _engine_with_fake_ecs
- test_adr_hygiene.py
- redact_url_userinfo
- test_tunnel_host.py
- contributor 指南 CONTRIBUTING.md
- skill_install.py
- JobSource
- ._run_cdk
- test_detached_launcher.py
- manifest.json
- report_store/local.py
- use_color
- gherkai_runtime/names.py
- deterministic.py
- reconcile.tick（无状态编排步骤）
- _gap_engine
- ArtifactUploader
- NPM Dependencies
- 演示制作规范
- test_sqlite_event_log.py
- _CdkWritingContext
- event-sink.mts
- Diagram Build Script
- deterministic.mts
- evidence.test.mts
- map_origin_in_jobs
- test_container.py
- _StubEcs
- readme_video
- _FakeEcs
- Event Wallclock Analysis
- Release Notes Guardrails
- run-scope.test.mts
- Distribution Metadata Checks
- _build_parser
- Package README Guardrails
- _stream_record
- _run_with_refs
- test_list_workers_reports_unreachable_aws_without_a_traceback
- _Recorder
- Worker Package Manifest
- artifact-upload.test.mts
- .deploy
- _mk_state
- gherkai《价值与方法》五分钟版口播
- ArtifactUploader（产物落点可注入组件）
- Architecture Diagrams
- test_final_drain_paginates_across_last_evaluated_key
- Advancer IAM Permissions
- argument.mts
- video.py
- 03-midscene-grounding.ts
- files
- minimax_narration.py
- parse.py
- User-Facing Text Guardrail
- AWS Client Stubs
- test_provider_module_does_not_import_aws_cdk
- FeatureSource
- verification
- _stopped_detail
- test_skill_deploy_tokens.py
- job-source.mts
- Fargate Naming & Wiring
- Worker Signal Interrupt Tests
- Fake Event Sink
- DynamoDB 共享 events 表（events-out 传输）
- _error_text
- ECS Task Timing Capture
- e2e_harness.py
- exit_observer.py
- _StopTimeoutEcs
- _ssm_params
- Graph Refresh Script
- Cloud Status Command
- parse_iso
- _seed_worker_ssm
- user-steps.test.mts
- ValueError
- test_finished_run_gate_keys_on_the_committed_run_status_only
- Doc Rules Check
- Fake DynamoDB Table
- _MissingThenStoppedEcs
- deterministic.steps.mts
- redact.mts
- ADR 0030 实时写接缝
- Report Store Output
- package_urls
- Context Glossary Guardrail
- AI Verdict Model Terms
- Run Data & Artifact Terms
- 01-model-sigv4.ts
- bin.mts
- model.py
- agentcore-sigv4.test.mts
- Fake S3 Client
- Execution Session Terms
- Echo Test Worker
- Cloud Infra Test Baseline
- NoRedirect
- 演示制作与媒体工具
- index.mts
- TypeScript Dev Dependencies
- Release Pipeline Jobs
- resolve-hook.mts
- test_handle_timeout_finds_stopped_target_on_second_page
- error-text.mts
- event-sink.test.mts
- gherkai_cli/__main__.py（argparse 前端）
- Worker Subnet Selection
- Image Parameter Filtering
- Package Distribution Files
- Repository Metadata
- _runs_stream_record
- Nova Artifact Upload
- Upload Call Recorder
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- Batch Run Advancer Terms
- Backend & Preflight Terms
- _frontmatter_and_body
- _AbsentEngine
- Skill Evaluation Isolation Rules
- Architecture Interaction Diagrams
- Build And Test Scripts
- AgentCore CDP Script
- Background Upload Queue
- Run Summary Script
- Pre-commit Hook Setup
- Bedrock AgentCore SDK Dependency
- DynamoDB SDK Dependency
- ._pump
- _await_engine
- Feature File Preflight
- job-source.test.mts
- Adapters Implementation Layer
- test_tick_runs_isolates_defensive_scan_failure
- redact.test.mts
- slide_area_ssim_checks
- Step Match Query
- OpenAI Dependency
- TSX Dependency
- Upload Queue Drain
- Upload Enablement Check
- Assembly Mismatch Fail-Loud
- No-op Local Uploader
- Index Wait Script
- Gherkai Workspace Root
- test_tunnel.py
- test_reconcile.py
- Agent Skill
- Machine-Readable Output Contract
- test_starter_run_ids_from_direct_kick
- build_local_stores
- Cloud Resource Retention Policy
- Fixture Portability Contract
- Trigger Rate Self-Test
- Blocking Hook Checks
- Architecture Layering Diagram
- Run Lifecycle Diagram
- Submit-Time Revision Pinning
- Cloud Worker Identity Topology
- _fixture
- Package Build Smoke CI
- Gherkai Core Package
- AWS Deploy Package
- Gherkai Runtime Package
- NovaAct Worker Package
- test_raise_for_worker_exit_maps_codes_with_fargate_label
- Runtime Package README
- test_final_drain_logs_real_holes_under_consistent_read
- test_await_exit_code_transient_missing_then_stopped_reads_code
- docs/presentations/README.md
- chapters.md
- value-method/README.md
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- .delete_worker
- test_build_takes_meta_max_concurrency_under_cap
- 05-negative-assertions.ts
- test_build_raises_when_legacy_definition_unresolvable
- .preflight
- ../lib/artifact-upload.mjs

## God Nodes (most connected - your core abstractions)
1. `main()` - 216 edges
2. `Job` - 135 edges
3. `RunState` - 127 edges
4. `RunMeta` - 120 edges
5. `Status` - 106 edges
6. `JobState` - 101 edges
7. `Provider` - 95 edges
8. `JobResult` - 84 edges
9. `Scenario` - 73 edges
10. `Step` - 72 edges

## Surprising Connections (you probably didn't know these)
- `eval fixture: tunnel-mismatch 待办应用` --conceptually_related_to--> `ADR 0043 驱动 gherkai 的 agent skill`  [AMBIGUOUS]
  cli/skills/gherkai-evals/fixtures/tunnel-mismatch/README.md → docs/adr/0043-agent-skill-for-driving-gherkai.md
- `图：运行时拓扑（README）` --semantically_similar_to--> `五层结构（用例/产品/执行/浏览器/被测应用）`  [AMBIGUOUS] [semantically similar]
  docs/diagrams/readme-runtime-topology.svg → docs/internals/architecture-overview.md
- `图：scenario 到 job` --semantically_similar_to--> `一次 run 的生命周期（parse→分组→begin→驱动→判定归约与报告）`  [AMBIGUOUS] [semantically similar]
  docs/diagrams/writing-features-scenario-to-job.svg → docs/internals/architecture-overview.md
- `ADR 0035 本机应用隧道暴露` --references--> `图：本机应用测试隧道拓扑`  [AMBIGUOUS]
  docs/adr/0035-local-app-testing-via-tunnel.md → docs/diagrams/local-app-testing-tunnel-topology.svg
- `worker variant 与 push-worker` --conceptually_related_to--> `ADR 0038 worker 镜像交付`  [INFERRED]
  cli/gherkai_cli/skills/gherkai/references/cloud-backend.md → docs/adr/0038-worker-image-delivery.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **面向 AI agent 的驾驭链：契约 + 证据 + 教材** — docs_adr_0041_agent_facing_cli_affordances_json_contract, docs_adr_0042_step_evidence_and_explain_evidence, docs_adr_0042_step_evidence_and_explain_explain, docs_adr_0043_agent_skill_for_driving_gherkai_skill_md, docs_adr_0043_agent_skill_for_driving_gherkai_derived_copy [EXTRACTED 0.85]
- **AI 断言为主的可靠性纪律（投票 / 确定性 step / 柔性边界）** — docs_adr_0014_ai_first_assertions, docs_adr_0015_v1_positioning_smoke_not_regression, docs_adr_0014_assertion_voting, docs_adr_0015_flexible_leak_vs_flakiness, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold [EXTRACTED 0.85]
- **核心库窄腰的执行分层：ports 注入、engine port 交出 scope、每 scope 一个薄 worker** — context_core_library_narrow_waist, context_core_ports, context_engine_port, context_thin_worker, context_run_data_model, context_deterministic_step_registry [EXTRACTED 0.85]
- **确定性 step 的单一真值面：注册表、派发链、三入口与响亮失败** — docs_internals_deterministic_step_lifecycle_registry, docs_internals_deterministic_step_lifecycle_dispatch_chain, docs_internals_deterministic_step_lifecycle_truth_sources, docs_internals_deterministic_step_lifecycle_loud_failure [EXTRACTED 0.85]
- **Midscene 引擎模型选型脉络（AWS 内约束下的取舍）** — docs_adr_0002_midscene_not_driven_by_gpt55, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0044_engine_model_selection_and_override, docs_adr_0009_maximize_aws_hard_constraint, docs_adr_0012_planning_shares_qwen3vl_no_text_planner [EXTRACTED 0.85]
- **Fargate 中断韧性一揽（提前上传 + grace 预算 + 解法 D + reaper 否决）** — docs_adr_0032_fargate_execution_environment_interrupt_loss, docs_adr_0032_fargate_execution_environment_safepoint_upload, docs_adr_0032_fargate_execution_environment_stop_timeout, docs_adr_0032_fargate_execution_environment_solution_d, docs_adr_0032_fargate_execution_environment_orphan_reaper_rejected [EXTRACTED 0.85]
- **Four-Level Upload Timing Flow and Residue** — docs_adr_0029_engine_artifacts_to_s3_upload_timing, docs_adr_0029_engine_artifacts_to_s3_act_boundary_presend, docs_adr_0029_engine_artifacts_to_s3_scenario_boundary_presend, docs_adr_0029_engine_artifacts_to_s3_upload_timeout, docs_adr_0029_engine_artifacts_to_s3_inherent_residue [EXTRACTED 0.85]
- **CDK↔cli 命名契约链（prefix / 真源 / container 名 / SSM / preflight）** — docs_adr_0033_iac_aws_backend_and_composition_wiring_two_layer_naming, docs_adr_0033_iac_aws_backend_and_composition_wiring_names_source, docs_adr_0033_iac_aws_backend_and_composition_wiring_container_name, docs_adr_0033_iac_aws_backend_and_composition_wiring_ssm_subnet_sg, docs_adr_0033_iac_aws_backend_and_composition_wiring_preflight [EXTRACTED 0.85]
- **step 派发流水线（抽象原语 → 默认 AI / 确定性注册表 / URL 导航 → 协议事件）** — docs_adr_0018_abstract_primitives, docs_adr_0020_default_ai_step, docs_adr_0020_deterministic_scaffold, docs_adr_0020_url_autodispatch, docs_adr_0022_deterministic_registry, docs_adr_0024_worker_core_protocol [EXTRACTED 0.85]
- **reconcile.tick 的多个宿主（同一份代码、不同注入 adapter）** — docs_internals_execution_and_reconciliation_reconcile_tick, docs_internals_execution_and_reconciliation_per_run_process, docs_internals_execution_and_reconciliation_kicker, docs_internals_execution_and_reconciliation_reconciler [EXTRACTED 0.85]
- **v1.0 核心三模块流水线（协议→plan→schedule→RunReport）** — docs_adr_0024_worker_core_protocol, docs_adr_0025_plan_module_feature_to_jobs, docs_adr_0026_schedule_module, docs_adr_0027_runreport_aggregation_index [EXTRACTED 0.85]
- **agent skill 包：SKILL.md 与五份分域 reference** — cli_gherkai_cli_skills_gherkai_skill, cli_gherkai_cli_skills_gherkai_references_engines, cli_gherkai_cli_skills_gherkai_references_deterministic_steps, cli_gherkai_cli_skills_gherkai_references_cloud_backend, cli_gherkai_cli_skills_gherkai_references_setup_and_diagnosis, cli_gherkai_cli_skills_gherkai_references_cli_json_contract [EXTRACTED 0.90]
- **B1 转向：核心自解析带来的连带退役与实现层转移** — docs_adr_0022_bdd_runner_retired_core_parses_thin_worker, docs_adr_0021_local_cucumber_patch_step_keyword_disambiguation, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold, docs_adr_0019_feature_tags_scope_and_engine, docs_adr_0016_execution_architecture_core_lib_run_model [EXTRACTED 0.90]
- **云端后台运行的三 Lambda 事件级联链** — docs_internals_execution_and_reconciliation_kicker, docs_internals_execution_and_reconciliation_reconciler, docs_internals_execution_and_reconciliation_exit_observer, docs_internals_execution_and_reconciliation_reconcile_tick, docs_internals_execution_and_reconciliation_detached_flag [EXTRACTED 0.90]
- **云端事件链自我驱动（kicker / reconciler / exit-observer）** — deploy_aws_gherkai_deploy_aws_stack, deploy_aws_gherkai_deploy_aws_lambdas_reconciler, deploy_aws_gherkai_deploy_aws_lambdas_exit_observer, core_gherkai_core_reconcile, docs_adr_0034_detached_batch_reconciler [EXTRACTED 0.90]
- **core 窄腰执行管线：解析→分组→调度/推进→归集** — core_gherkai_core_parse, core_gherkai_core_scope, core_gherkai_core_schedule, core_gherkai_core_project, core_gherkai_core_reconcile, core_gherkai_core_persist [EXTRACTED 0.90]
- **detached run 推进的三个触发源与共享 tick** — docs_adr_0034_detached_batch_reconciler_kicker_lambda, docs_adr_0034_detached_batch_reconciler_tick, docs_adr_0034_detached_batch_reconciler_exit_observer, docs_adr_0034_detached_batch_reconciler_events_table, docs_adr_0034_detached_batch_reconciler_runstate [EXTRACTED 0.90]
- **Gherkin tag 配置体系（scope/engine/timeout 三成员，同构的继承/冲突/缺省规则）** — docs_adr_0019_scope_tag, docs_adr_0019_engine_tag, docs_adr_0019_timeout_tag, docs_adr_0019_feature_tags_scope_and_engine, docs_adr_0025_plan_module_feature_to_jobs [EXTRACTED 0.90]
- **docs/internals 主题归属：七篇各拥有一个机制** — docs_internals_readme, docs_internals_architecture_overview, docs_internals_execution_and_reconciliation, docs_internals_verdict_model, docs_internals_artifacts_and_evidence, docs_internals_deterministic_step_lifecycle, docs_internals_cloud_backend_carriers, docs_internals_cli_json_contract [EXTRACTED 0.90]
- **job 生命周期态模型（态集 + severity + 聚合过滤 + 终态真源）** — docs_adr_0031_job_lifecycle_states_and_severity_status_skipped, docs_adr_0031_job_lifecycle_states_and_severity_status_aborted, docs_adr_0031_job_lifecycle_states_and_severity_status_pending_running, docs_adr_0031_job_lifecycle_states_and_severity_non_verdict, docs_adr_0031_job_lifecycle_states_and_severity_terminal_statuses [EXTRACTED 0.90]
- **人读输出渲染面：textui 单点与三个消费方** — runtime_gherkai_runtime_textui, cli_gherkai_cli_main, cli_gherkai_cli_render, deploy_aws_gherkai_deploy_aws_workers, core_gherkai_core_termcolor [EXTRACTED 0.90]
- **Showcase Diagrams Sharing Bundled Font Bytes** — docs_diagrams_artifacts_evidence_chain_diagram, docs_diagrams_cloud_backend_carriers_revision_pinning_diagram, docs_diagrams_cloud_backend_upgrade_windows_diagram, docs_diagrams_cloud_delivery_identity_diagram, docs_diagrams_configuration_env_inheritance_diagram, docs_diagrams_deterministic_steps_registry_overview_diagram, docs_diagrams_deterministic_steps_truth_sources_diagram, docs_diagrams_execution_cloud_cascade_diagram, docs_diagrams_execution_detached_gates_diagram, docs_diagrams_execution_timeout_chain_diagram, docs_diagrams_getting_started_component_ownership_diagram, docs_diagrams_jetbrains_mono_embedded_font [EXTRACTED 0.90]
- **Symmetric Uploader Contract Across Nova and Midscene** — docs_adr_0029_engine_artifacts_to_s3_artifact_uploader, docs_adr_0029_engine_artifacts_to_s3_from_env, docs_adr_0029_engine_artifacts_to_s3_to_report_ref, docs_adr_0029_engine_artifacts_to_s3_flush_and_cleanup, docs_adr_0029_engine_artifacts_to_s3_snapshot_report, docs_adr_0029_engine_artifacts_to_s3_snapshot_logs [EXTRACTED 0.90]
- **终止契约三层（逻辑层 / 机制层 / worker 层）** — docs_adr_0026_schedule_module_graceful_termination, docs_adr_0024_worker_core_protocol_termination_contract, docs_adr_0024_worker_core_protocol_flag_only_handler, docs_adr_0024_worker_core_protocol_midscene_handler, docs_adr_0024_worker_core_protocol_grace_constraint [EXTRACTED 0.90]
- **判定计算链：归约层 → 状态 → 归因 → 严重度 → 退出码** — docs_internals_verdict_model_reduction_layers, docs_internals_verdict_model_statuses, docs_internals_verdict_model_error_type, docs_internals_verdict_model_severity, docs_internals_verdict_model_exit_codes [EXTRACTED 0.90]
- **worker 镜像从基础镜像到运行时 revision 的交付链** — docs_adr_0038_worker_image_delivery_base_image, docs_adr_0038_worker_image_delivery_variant, docs_adr_0038_worker_image_delivery_push_worker, docs_adr_0038_worker_image_delivery_default_pointer, docs_adr_0038_worker_image_delivery_explicit_revision, docs_adr_0037_distribution_and_packaging_steps_dir [EXTRACTED 0.90]
- **worker I/O 边缘三条可注入接口** — docs_adr_0024_worker_core_protocol_jobsource, docs_adr_0024_worker_core_protocol_eventsink, docs_adr_0029_engine_artifacts_to_s3_artifact_uploader [EXTRACTED 0.90]
- **云端后端的五个独立更新载体** — docs_internals_cloud_backend_carriers_cloudformation_stack, docs_internals_cloud_backend_carriers_lambda_asset, docs_internals_cloud_backend_carriers_base_image, docs_internals_cloud_backend_carriers_variant_image, docs_internals_cloud_backend_carriers_ssm_parameters [EXTRACTED 0.95]
- **Cloud Backend Lifecycle Diagram Group** — docs_diagrams_cloud_backend_carriers_revision_pinning_diagram, docs_diagrams_cloud_backend_upgrade_windows_diagram, docs_diagrams_cloud_delivery_identity_diagram, docs_diagrams_execution_cloud_cascade_diagram [INFERRED 0.60]
- **云端后端版本锁步：skew 闸 + deploy 升级顺序 + variant 重派生** — cli_development_version_skew_gate, cli_development_preflight_order, cli_gherkai_cli_skills_gherkai_references_cloud_backend_variant, cli_gherkai_cli_skills_gherkai_references_setup_and_diagnosis, docs_adr_0037_distribution_and_packaging [INFERRED 0.75]

## Communities (266 total, 66 thin omitted)

### Community 0 - "test_schedule.py"
Cohesion: 0.07
Nodes (107): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), RuntimeError, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError (+99 more)

### Community 1 - "test_lambda_handlers.py"
Cohesion: 0.06
Nodes (30): cloud_env(), Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。 (+22 more)

### Community 2 - "ADR 0016 执行架构与分层"
Cohesion: 0.06
Nodes (87): cli 包 contributor 文档, cloud preflight 次序（skew → 资源 → variant）, 版本 skew 六态闸, 柔性冒烟 (flexible smoke test), 柔性漏检, core 测试说明（单测 + 集成测试）, gherkai-deploy-aws contributor 手册, gherkai-deploy-aws 发行包入口页 (+79 more)

### Community 3 - "test_main.py"
Cohesion: 0.04
Nodes (96): _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：运行前先问一次能力自述，worker 非零退出 → 起任何 job 之前以退出码 2 结束（不进 job 级 error）。… (+88 more)

### Community 4 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 5 - "Job"
Cohesion: 0.04
Nodes (101): explain_to_dict(), 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, render_text(), _evidence_fixture(), _explain_cloud_stores(), _explain_job(), _explain_run() (+93 more)

### Community 6 - "WorkerSelfDescribeError"
Cohesion: 0.09
Nodes (20): _ask_worker(), load_feature(), local_artifact_locations(), match_deterministic(), Path, RuntimeError, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`… (+12 more)

### Community 7 - "test_workers.py"
Cohesion: 0.06
Nodes (89): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地… (+81 more)

### Community 8 - "workers.py"
Cohesion: 0.04
Nodes (97): Aws, cleanup_pass(), CleanupOutcome, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+89 more)

### Community 9 - "build_cloud_stores"
Cohesion: 0.09
Nodes (24): build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), 云端后端一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。 (+16 more)

### Community 10 - "test_plan.py"
Cohesion: 0.12
Nodes (30): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否…, @scope 的值等于某条**自身已标 @scope** 的 scenario 的 id → 不报错：那条 id 根本没当分组键，不会撞。, 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ PlanError（ADR 0025：标了 tag…, test_assertion_votes_default_is_one() (+22 more)

### Community 11 - "gherkai_cli/__main__.py"
Cohesion: 0.05
Nodes (77): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_deploy(), _cmd_destroy(), _cmd_explain(), _cmd_list_deterministic() (+69 more)

### Community 12 - "build_local_reconcile"
Cohesion: 0.09
Nodes (27): make_resolver(), dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, build_local_reconcile(), cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status… (+19 more)

### Community 13 - "_run_step"
Cohesion: 0.07
Nodes (51): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+43 more)

### Community 14 - "Provider"
Cohesion: 0.06
Nodes (83): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _argv(), _parse(), _parse_destroy(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，… (+75 more)

### Community 15 - "_StampSsm"
Cohesion: 0.15
Nodes (14): _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口前端只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到不等于放过。, _StampSsm, test_check_backend_skew_missing_stamp_warns_not_raises() (+6 more)

### Community 16 - "_fake_locator"
Cohesion: 0.08
Nodes (38): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+30 more)

### Community 17 - "test_stack.py"
Cohesion: 0.07
Nodes (49): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler/kicker）都要能读 `/{prefix}backend/*`（ADR 0038「权限面增量·云端推进器」）： 没有… (+41 more)

### Community 18 - "test_evidence.py"
Cohesion: 0.08
Nodes (50): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), list, parametrize (+42 more)

### Community 19 - "Deploy Command Frontend Tests"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 20 - "gherkai《价值与方法》讲者备注"
Cohesion: 0.05
Nodes (43): gherkai《价值与方法》讲者备注, 口播正文, 口播正文, 口播正文, 口播正文, 口播正文, 口播正文, 口播正文 (+35 more)

### Community 21 - "RunState"
Cohesion: 0.03
Nodes (126): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_render_status_pending_run_with_claimed_job_does_not_hint(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal() (+118 more)

### Community 22 - "用户指南：配置（环境变量与通用选项）"
Cohesion: 0.07
Nodes (53): skill reference: CLI --json 字段契约, skill reference: 云端后端与 variant 镜像, worker variant 与 push-worker, skill reference: 确定性 step 写法, skill reference: 引擎选择与证据填充差异, agent skill 参考：环境就位与排障, 隧道模式 --expose-local, CLI 与后端版本不一致的闸门 (+45 more)

### Community 23 - "LocalReportStore"
Cohesion: 0.19
Nodes (33): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。 (+25 more)

### Community 24 - "test_cloud_reconcile.py"
Cohesion: 0.07
Nodes (45): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写… (+37 more)

### Community 25 - "test_project.py"
Cohesion: 0.05
Nodes (94): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, ScopeDone, ScopeStarted, StepStarted, Action (+86 more)

### Community 26 - "Nova Worker Library Setup"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 27 - "main"
Cohesion: 0.04
Nodes (65): main(), _det_feature(), _plan_names(), 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。 (+57 more)

### Community 28 - "test_worker_variant.py"
Cohesion: 0.08
Nodes (44): _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。, 默认指针不存在（部署没走过 worker 镜像初始化）→ 提示运行 `gherkai deploy`，不猜 `base`。, SSM 无该（引擎，variant）映射 + CLI 与后端同版本 → 引导 push-worker，**不回落默认 variant**。 (+36 more)

### Community 29 - "run_scope.py"
Cohesion: 0.06
Nodes (46): ArtifactUploader, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_evidence(), _attach_traj_refs(), _capabilities(), _collect_traj(), _cost_from_result() (+38 more)

### Community 30 - "test_skill.py"
Cohesion: 0.06
Nodes (53): bare_flags(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags() (+45 more)

### Community 31 - "cli.py"
Cohesion: 0.06
Nodes (37): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client(), _make_sts_client() (+29 more)

### Community 32 - "Skill Fixture Materialization"
Cohesion: 0.09
Nodes (47): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+39 more)

### Community 33 - "test_conditional_writes.py"
Cohesion: 0.07
Nodes (50): _initial(), _meta(), RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+42 more)

### Community 34 - "test_subprocess_engine.py"
Cohesion: 0.12
Nodes (30): _pump_log(), scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, _scope_color(), SubprocessEngine, _engine(), _job() (+22 more)

### Community 35 - "ADR 0041 面向 agent 的 CLI 可用性"
Cohesion: 0.05
Nodes (52): CAS(pending→running) 并发闸, CQRS + 无状态 reconciler 机制, detached 顶层标记（推进链只碰 detached run）, events 表（append-only 真值日志）, 退出观察者（平台侧读 exitCode 写 task_exited）, HWM + 状态机单调条件写, job timeout（definition 载体 + 三路推进器各自 enforce）, kicker Lambda（冷启动推进器） (+44 more)

### Community 36 - "atomic_write_json"
Cohesion: 0.13
Nodes (20): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+12 more)

### Community 37 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (33): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+25 more)

### Community 38 - "evidence.py"
Cohesion: 0.08
Nodes (41): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Any, Path (+33 more)

### Community 39 - "test_event_sink.py"
Cohesion: 0.06
Nodes (23): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, redact_url_userinfo() (+15 more)

### Community 40 - "test_tunnel_cli.py"
Cohesion: 0.09
Nodes (41): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。 (+33 more)

### Community 41 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 42 - "架构全景（internals）"
Cohesion: 0.07
Nodes (42): 图：五层全景, 图：一次 run 的主干, 图：证据链, 图：确定性 step 注册表全景, 图：确定性 step 的两个真值源, 图：运行时拓扑（README）, 图：run 执行, 图：job 判定结果 (+34 more)

### Community 43 - "compose.py"
Cohesion: 0.05
Nodes (56): subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), ssm_worker_template_path() (+48 more)

### Community 44 - "query_capabilities"
Cohesion: 0.07
Nodes (36): engine_min_grace(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc(), parametrize, dev/post/本地段版本**不在 PyPI/npm 上**（ADR 0037 决策 2b 的派生形态）→ 第四级跳过、直接 miss 报安装指引。 否则… (+28 more)

### Community 45 - "scope.py"
Cohesion: 0.21
Nodes (15): PlanError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope… (+7 more)

### Community 46 - "render.py"
Cohesion: 0.09
Nodes (38): _add_act(), _add_step(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), explain_tree() (+30 more)

### Community 47 - "RunPersistence"
Cohesion: 0.11
Nodes (26): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+18 more)

### Community 48 - "test_user_docs.py"
Cohesion: 0.09
Nodes (38): changelog_unreleased(), prose_lines(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _default_model_claims(), _default_model_ids(), parametrize, Path (+30 more)

### Community 49 - "../lib/agentcore-sigv4.mjs"
Cohesion: 0.13
Nodes (18): ADR-0008, main(), BASE_URL, main(), ADR-0033, ../lib/agentcore-sigv4.mjs, bedrockCompatBody(), DEFAULT_MODEL (+10 more)

### Community 50 - "./run-scope.mjs"
Cohesion: 0.06
Nodes (50): ADR-0019, ADR-0026, ADR-0027, ADR-0039, ADR-0037, ./run-scope.mjs, agentOpts(), aggregate() (+42 more)

### Community 51 - "textui.py"
Cohesion: 0.11
Nodes (30): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。, 深度优先找第一个 label 含 needle 的节点（测试与诊断用）。, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，… (+22 more)

### Community 52 - "_RecUploader"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。 (+10 more)

### Community 53 - "test_fargate_engine.py"
Cohesion: 0.11
Nodes (43): _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。 (+35 more)

### Community 54 - "BackendStack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 55 - "_FakeEcsClient"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 56 - "evidence.mts"
Cohesion: 0.09
Nodes (30): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+22 more)

### Community 57 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 58 - "_doc_rules.py"
Cohesion: 0.12
Nodes (30): ai_side_docs(), classify(), code_comment_files(), comment_units(), diagram_sources(), long_term_docs(), Path, 人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。 内容三类：①规则——内部指代表 FORBIDDEN、口吻表… (+22 more)

### Community 59 - "ADR 0028: 瞬时网络/SSL 韧性"
Cohesion: 0.06
Nodes (38): act 有界返回（per-act timeout）, 被拒方案：asyncio 化消除 greenlet, 引擎经 --capabilities 自报 min_grace_s, Nova flag-only 信号 handler, grace 硬约束与护栏, handler 内零 I/O（只置标志）, Midscene 有序显式 cleanup handler, 泄漏兜底：AgentCore session TTL（不引入 core reaper） (+30 more)

### Community 60 - "_is_transient_network"
Cohesion: 0.15
Nodes (27): _is_transient_network(), 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是…, 造一个 botocore ClientError（response 里带 Error.Code /…, _target_closed(), test_agentcore_permanent_wrapping_chain_not_transient() (+19 more)

### Community 61 - "_cmd_doctor"
Cohesion: 0.11
Nodes (21): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+13 more)

### Community 62 - "test_compose.py"
Cohesion: 0.04
Nodes (79): build_engines(), _find_worker_spec(), prune_empty_dirs(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION… (+71 more)

### Community 63 - "ADR 0043 驱动 gherkai 的 agent skill"
Cohesion: 0.12
Nodes (26): gherkai agent skill 包, SKILL.md（随 CLI wheel 发行的 agent skill）, ADR 0004：Nova Act 经 Workflow 的 IAM 鉴权, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0043 驱动 gherkai 的 agent skill, skill 评测资产（决策七）, ADR 0045 文档分层与归位 (+18 more)

### Community 64 - "_explain"
Cohesion: 0.10
Nodes (21): _explain(), 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；…, 显式 --step 点名的那一步即展开证据（点名就是想看），不必再给 --all；默认视图对同一 passed 步仍不展开。, --all 也展开 passed step；--full 逐 frame 全文（省略计数消失、无推理的 frame 也现身）。, detached run 未终态时零判定明细（全 job 终态才一次性落）→ 退出码 0 + 一行提示；--json 不打提示、 stdout… (+13 more)

### Community 65 - "reconciler.py"
Cohesion: 0.11
Nodes (23): _build(), EventBridgeTimeoutWatch, _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个…, 超时处置（ADR 0034「job timeout」节的云端后端一侧）：仍 running 才动手——ListTasks(startedBy=run_id)… (+15 more)

### Community 66 - "Artifact Uploader (Python)"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 67 - "Status"
Cohesion: 0.04
Nodes (40): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。 (+32 more)

### Community 68 - ".add_arguments"
Cohesion: 0.19
Nodes (9): ArgumentParser, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6； 三者与…, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`… (+1 more)

### Community 69 - "Version Skew Checking"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 70 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (24): make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path, Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。… (+16 more)

### Community 71 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 72 - "test_user_steps.py"
Cohesion: 0.07
Nodes (49): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+41 more)

### Community 73 - "FargateEngine"
Cohesion: 0.12
Nodes (16): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+8 more)

### Community 74 - "RunStore"
Cohesion: 0.08
Nodes (14): adapters/event_log（sqlite / ddb）, 控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。…, CAS 抢占：仅当该 job 当前是 PENDING 才置 RUNNING，成功返回 True（机制四）。 多个 reconciler 实例并发抢同一…, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale…, 状态机单调条件写：仅当 run 总 status 当前为非终态（pending/running）才写终态，成功 True（机制三）。 挡「已 finalize…, RunStore, EventLog, Launcher (+6 more)

### Community 75 - "test_cli_json_contract.py"
Cohesion: 0.13
Nodes (22): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…, _assert_documented(), _documented_keys(), _leaf_keys(), _mk() (+14 more)

### Community 76 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 77 - "test_stores.py"
Cohesion: 0.04
Nodes (80): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore (+72 more)

### Community 78 - "_engine_with_fake_ecs"
Cohesion: 0.25
Nodes (8): _engine_with_fake_ecs(), DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null(), test_probe_task_stopped_with_exit_code()

### Community 79 - "test_adr_hygiene.py"
Cohesion: 0.19
Nodes (18): _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。, Status 头里点名的取代方编号（只看 superseded-by 之后、到第一个注解分隔符为止那一段）。, 被取代方点了谁，谁就得回指它——机械差集，不靠读。 (+10 more)

### Community 80 - "redact_url_userinfo"
Cohesion: 0.16
Nodes (15): Any, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_url_userinfo(), parametrize, 隧道凭据脱敏的规则单测（ADR 0035 决策 5）。…, 规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉。 (+7 more)

### Community 81 - "test_tunnel_host.py"
Cohesion: 0.09
Nodes (29): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, start_tunnel_for_jobs() (+21 more)

### Community 82 - "contributor 指南 CONTRIBUTING.md"
Cohesion: 0.06
Nodes (47): 变更记录 (CHANGELOG), --max-concurrency 默认值改为 4, Midscene 默认模型改为 us.openai.gpt-5.6-terra, Nova Act 默认模型固定为 nova-act-v1.0, 项目约定 CLAUDE.md, /code-health-review 入口, /doc-health-review 入口, doc-diagram 项目级 skill (+39 more)

### Community 83 - "skill_install.py"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 84 - "JobSource"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 85 - "._run_cdk"
Cohesion: 0.08
Nodes (24): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), cdk_command(), check_cdk(), check_node(), _node_major(), Path, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC… (+16 more)

### Community 86 - "test_detached_launcher.py"
Cohesion: 0.14
Nodes (26): now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, Job, per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, run_reconcile_loop(), SubprocessLauncher, _echo_resolver() (+18 more)

### Community 87 - "manifest.json"
Cohesion: 0.06
Nodes (33): brand_pronunciation, caption_count, caption_sha256, caption_source, deck_file, deck_sha256, duration, emotion (+25 more)

### Community 88 - "report_store/local.py"
Cohesion: 0.12
Nodes (18): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+10 more)

### Community 89 - "use_color"
Cohesion: 0.19
Nodes (16): color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env(), _Pipe (+8 more)

### Community 90 - "gherkai_runtime/names.py"
Cohesion: 0.09
Nodes (27): default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…, prefix + 基名（原样拼，prefix 含分隔符由部署方负责）。CDK 与 cli 共用此推导 → 单一事实源。 (+19 more)

### Community 91 - "deterministic.py"
Cohesion: 0.08
Nodes (36): deterministic, clear(), deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match() (+28 more)

### Community 92 - "reconcile.tick（无状态编排步骤）"
Cohesion: 0.32
Nodes (8): 收尾写序与提交点（try_finalize）, detached 标记与两道拦截, 同一条事件流的四条物理通道, exit-observer Lambda（退出观察者）, kicker Lambda（冷启动器）, local per-run 推进进程（setsid 脱离 CLI）, reconcile.tick（无状态编排步骤）, reconciler Lambda（主推进器）

### Community 93 - "_gap_engine"
Cohesion: 0.17
Nodes (13): _delayed_stopped_ecs(), _ev_item(), _gap_engine(), 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+5 more)

### Community 95 - "NPM Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 96 - "演示制作规范"
Cohesion: 0.25
Nodes (7): 修改与验收, 口播、字幕与视频, 定位与方法, 溯源与保存规则, 演示制作规范, 表达边界, 视觉与页面

### Community 97 - "test_sqlite_event_log.py"
Cohesion: 0.15
Nodes (18): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, 端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。 (+10 more)

### Community 98 - "_CdkWritingContext"
Cohesion: 0.19
Nodes (13): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, Path, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。 (+5 more)

### Community 99 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd()

### Community 100 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 101 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 102 - "evidence.test.mts"
Cohesion: 0.14
Nodes (13): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, importRunScope(), ADR-0042 (+5 more)

### Community 103 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 104 - "test_container.py"
Cohesion: 0.04
Nodes (58): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+50 more)

### Community 105 - "_StubEcs"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 106 - "readme_video"
Cohesion: 0.08
Nodes (24): readme_video, anonymous_playback, audio_samples_and_timestamps_preserved, bytes, caption_bar_height, caption_boundary_frames_checked, caption_count, caption_font (+16 more)

### Community 107 - "_FakeEcs"
Cohesion: 0.10
Nodes (16): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的…, 仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…, task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录… (+8 more)

### Community 108 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 109 - "Release Notes Guardrails"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 110 - "run-scope.test.mts"
Cohesion: 0.09
Nodes (13): _events, fakePage, importMod(), ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031 (+5 more)

### Community 111 - "Distribution Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 112 - "_build_parser"
Cohesion: 0.13
Nodes (16): _add_selection_flags(), _build_parser(), _cmd_skill_install(), _dist_version(), _installed_version(), ArgumentParser, run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。, 建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何… (+8 more)

### Community 113 - "Package README Guardrails"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 114 - "_stream_record"
Cohesion: 0.11
Nodes (19): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events… (+11 more)

### Community 115 - "_run_with_refs"
Cohesion: 0.16
Nodes (18): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077…, _run_with_refs(), test_report_files_keep_explicit_mode_under_tight_umask(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto… (+10 more)

### Community 117 - "_Recorder"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+3 more)

### Community 118 - "Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 119 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 120 - ".deploy"
Cohesion: 0.14
Nodes (9): 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点以退出码 2 结束）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…, flag → CDK context（app/stack 侧读的那四个配置项 + 版本戳）。 `--vpc` 一个 flag…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 解析链的诊断归口：解析得出 → target；失败 → 打一句诊断、返 None（调用点归退出码）。 **每个动作在碰 AWS 之前都要经这一口**：不存在的… (+1 more)

### Community 121 - "_mk_state"
Cohesion: 0.20
Nodes (14): _args(), _mk_state(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。 (+6 more)

### Community 122 - "gherkai《价值与方法》五分钟版口播"
Cohesion: 0.12
Nodes (15): gherkai《价值与方法》五分钟版口播, 第 10 页, 第 11 页, 第 12 页, 第 13 页, 第 14 页, 第 1 页, 第 2 页 (+7 more)

### Community 123 - "ArtifactUploader（产物落点可注入组件）"
Cohesion: 0.15
Nodes (18): ReportRef {kind, ref, label}, ResourceUri（带 scheme 的统一指针）, Act-Boundary Pre-Send (Level 3), ArtifactUploader（产物落点可注入组件）, 上传成功后删本地（两条护栏）, S3 Landing Env Injection (ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX), uploader.flush_and_cleanup(dir), uploader.from_env() (+10 more)

### Community 124 - "Architecture Diagrams"
Cohesion: 0.22
Nodes (13): Archify Diagram Accessibility & Preset Contract, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Environment Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram (+5 more)

### Community 126 - "Advancer IAM Permissions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 127 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 128 - "video.py"
Cohesion: 0.15
Nodes (28): cues(), digest(), link_chapter_title_track(), packets(), probe(), protected_state(), Path, Confirm the first slide at frame zero, hard cuts, and the closing fade. (+20 more)

### Community 129 - "03-midscene-grounding.ts"
Cohesion: 0.33
Nodes (5): ADR-0010, BASE_URL, MODEL_CONFIG, REGION, ADR-0033

### Community 130 - "files"
Cohesion: 0.09
Nodes (22): bytes, sha256, files, chapters.md, gherkai-value-method-v12-materials.zip, gherkai-value-method-v12.mp4, gherkai-value-method-v12.pptx, gherkai-value-method-v12.srt (+14 more)

### Community 131 - "minimax_narration.py"
Cohesion: 0.26
Nodes (10): APIError, download_subtitles(), main(), NoRedirect, page_numbers(), post(), Exception, Path (+2 more)

### Community 132 - "parse.py"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 133 - "User-Facing Text Guardrail"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 134 - "AWS Client Stubs"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 136 - "FeatureSource"
Cohesion: 0.19
Nodes (17): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只执行 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次运行哪几条。… (+9 more)

### Community 137 - "verification"
Cohesion: 0.14
Nodes (14): verification, audio_and_subtitle_samples_and_timestamps_preserved, bookends, caption_count, caption_text_and_timing_match_video, chapters_unchanged, complete_decode, minimum_slide_ssim (+6 more)

### Community 138 - "_stopped_detail"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 139 - "test_skill_deploy_tokens.py"
Cohesion: 0.12
Nodes (18): clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, 一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。, _build() (+10 more)

### Community 140 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 141 - "Fargate Naming & Wiring"
Cohesion: 0.24
Nodes (10): build_fargate_engines 组合根接线, container 名契约 {engine}-worker, gherkai_runtime.names 命名单一真源, preflight fail-fast 点名 prefix, 产物前缀一致性语义探针, report ⊥ 执行（--no-report 不改执行环境）, subnet/sg ID 走含 prefix 的 SSM 路径, task-def 不焊 region/凭证 (+2 more)

### Community 142 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 143 - "Fake Event Sink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 144 - "DynamoDB 共享 events 表（events-out 传输）"
Cohesion: 0.22
Nodes (9): DynamoDB 共享 events 表（events-out 传输）, 被拒方案：DynamoDB Streams（同步 run 语境）, 事件流结束信号（内容完整 + 进程终止都要）, EventSink（事件 sink 可注入接口）, exitCode 落值延迟的有界宽限轮询, FargateEngine adapter, 被拒方案：MSK（Kafka）, worker 进程内自增 seq（单写者不变量） (+1 more)

### Community 145 - "_error_text"
Cohesion: 0.22
Nodes (9): _error_text(), _is_transient_client_error(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…, 隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。, test_error_text_prefers_sdk_message_and_is_single_line() (+1 more)

### Community 146 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 147 - "e2e_harness.py"
Cohesion: 0.36
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 148 - "exit_observer.py"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 149 - "_StopTimeoutEcs"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 150 - "_ssm_params"
Cohesion: 0.17
Nodes (12): SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。…, _ssm_params(), test_prefix_switches_whole_set(), test_ssm_parameter_set_is_exactly_six(), test_ssm_version_parameter_from_context() (+4 more)

### Community 151 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 152 - "Cloud Status Command"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 153 - "parse_iso"
Cohesion: 0.25
Nodes (8): parse_iso(), datetime, detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), test_run_duration_ms_from_run_state_timestamps()

### Community 154 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 155 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 156 - "ValueError"
Cohesion: 0.27
Nodes (10): test_value_error_not_transient(), main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems(), 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值… (+2 more)

### Community 157 - "test_finished_run_gate_keys_on_the_committed_run_status_only"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 158 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 160 - "_MissingThenStoppedEcs"
Cohesion: 0.10
Nodes (12): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, _MissingThenStoppedEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。 (+4 more)

### Community 161 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 162 - "redact.mts"
Cohesion: 0.40
Nodes (3): RFC-3986, MASK, ADR-0035

### Community 163 - "ADR 0030 实时写接缝"
Cohesion: 0.08
Nodes (31): compose.build_cloud_stores, compose.build_local_stores, DynamoDBRunStore, S3ReportStore, S3ResultStore, S3StepArgumentOffloader, ADR 0025 plan 模块（解析 + scope 分组）, gherkin-official（Parser + Compiler） (+23 more)

### Community 164 - "Report Store Output"
Cohesion: 0.29
Nodes (7): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, JobResult 持有 Job、engine 经 property delegate, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 产物拷贝, ReportStore.write（整 run 一次写）, run_id（归集索引主键，组合根生成）

### Community 165 - "package_urls"
Cohesion: 0.33
Nodes (6): package_urls, package-core-link, package-deploy-link, package-midscene-link, package-novaact-link, package-runtime-link

### Community 166 - "Context Glossary Guardrail"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 167 - "AI Verdict Model Terms"
Cohesion: 0.33
Nodes (6): AI 断言 (AI assertion), 引擎模型 (engine model), 判定抖动 (flakiness), 模型家族 (model family), 默认模型锁定 (pinned default model), 票 / 投票 (vote / voting)

### Community 168 - "Run Data & Artifact Terms"
Cohesion: 0.33
Nodes (6): 产物指针 (artifact URI), 派生视图 (derived view), Run 数据模型, 安全点提前上传, step 证据 (step evidence), 判定真值 (verdict truth)

### Community 169 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 170 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 171 - "model.py"
Cohesion: 0.05
Nodes (62): core 包 contributor 文档, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, _join_pumps(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core… (+54 more)

### Community 174 - "Execution Session Terms"
Cohesion: 0.40
Nodes (5): AgentCore 浏览器会话, 协作式停止, 引擎 (engine), 停止宽限期, 隧道暴露 (tunnel exposure)

### Community 175 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 178 - "演示制作与媒体工具"
Cohesion: 0.29
Nodes (6): 制作资料, 按页配音, 演示制作与媒体工具, 生图, 网页字幕版, 视频画面与字幕更新

### Community 179 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 180 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 181 - "Release Pipeline Jobs"
Cohesion: 0.50
Nodes (5): release job: gate + build, release job: base image（GHCR）, release job: publish npm, release job: publish PyPI, release job: GitHub Release

### Community 183 - "test_handle_timeout_finds_stopped_target_on_second_page"
Cohesion: 0.33
Nodes (6): n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。, STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。 ECS…, 目标落在 STOPPED 列表第二页、且没有退出记录 → 仍按 DescribeTasks 落它的真退出码，不臆造超时。, _stopped_filler(), test_handle_timeout_finds_stopped_target_on_second_page(), test_handle_timeout_pages_task_lists_and_batches_describe()

### Community 184 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 186 - "gherkai_cli/__main__.py（argparse 前端）"
Cohesion: 0.67
Nodes (3): gherkai_cli/__main__.py（argparse 前端）, gherkai_core（纯库）, ci job: pytest（全 workspace 成员）

### Community 187 - "Worker Subnet Selection"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 188 - "Image Parameter Filtering"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 189 - "Package Distribution Files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 190 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 191 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 192 - "Nova Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 193 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 197 - "Batch Run Advancer Terms"
Cohesion: 0.67
Nodes (3): 推进器 (advancer), job 墙钟预算, 无状态批量运行

### Community 198 - "Backend & Preflight Terms"
Cohesion: 0.67
Nodes (3): 执行后端 (backend), 执行方式 (execution mode), 执行前预检 (preflight)

### Community 199 - "_frontmatter_and_body"
Cohesion: 0.50
Nodes (4): _frontmatter_and_body(), 极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。 支持 `key: 单行值`、引号值，以及 `key:…, `name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环…, test_skill_form_limits()

### Community 201 - "Skill Evaluation Isolation Rules"
Cohesion: 0.67
Nodes (3): 去污染硬规则（CLI 只读记哈希 / 舞台路径随机 / skill 副本仅 with-skill）, 被拒：在仓库内跑评测, 两臂评测法（with-skill vs baseline）

### Community 202 - "Architecture Interaction Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, docs/diagrams/index.html（Pages 交互图入口）, 执行与推进全景交互图（run / submit × local / cloud）

### Community 203 - "Build And Test Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 210 - "._pump"
Cohesion: 0.50
Nodes (3): Event, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, Timer

### Community 211 - "_await_engine"
Cohesion: 0.60
Nodes (5): _await_engine(), _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 217 - "slide_area_ssim_checks"
Cohesion: 0.67
Nodes (3): slide_area_ssim_checks, at_31_seconds, first_frame

### Community 227 - "test_tunnel.py"
Cohesion: 0.09
Nodes (30): _gen_auth(), make_tunnel(), NgrokTunnel, Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。 (+22 more)

### Community 228 - "test_reconcile.py"
Cohesion: 0.06
Nodes (45): Connection, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。 (+37 more)

### Community 243 - "_fixture"
Cohesion: 0.05
Nodes (49): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), _reset_scope_colors(), arg_offloader(), aws(), ddb_run_store() (+41 more)

### Community 265 - "05-negative-assertions.ts"
Cohesion: 0.29
Nodes (6): BASE_URL, Check, main(), MODEL_CONFIG, REGION, ADR-0033

### Community 293 - "../lib/artifact-upload.mjs"
Cohesion: 0.20
Nodes (10): ../lib/artifact-upload.mjs, CONTENT_TYPES, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0032, ADR-0033 (+2 more)

## Ambiguous Edges - Review These
- `ADR 0035 本机应用隧道暴露` → `图：本机应用测试隧道拓扑`  [AMBIGUOUS]
  docs/diagrams/local-app-testing-tunnel-topology.svg · relation: references
- `ADR 0012 planning 复用引擎模型、不引独立文本规划器` → `ADR 0013 跨引擎共享边界`  [AMBIGUOUS]
  docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md · relation: semantically_similar_to
- `ci job: midscene worker（npm）` → `skill reference: 引擎选择与证据填充差异`  [AMBIGUOUS]
  .github/workflows/ci.yml · relation: conceptually_related_to
- `eval fixture: tunnel-mismatch 待办应用` → `ADR 0043 驱动 gherkai 的 agent skill`  [AMBIGUOUS]
  cli/skills/gherkai-evals/fixtures/tunnel-mismatch/README.md · relation: conceptually_related_to
- `五层结构（用例/产品/执行/浏览器/被测应用）` → `图：运行时拓扑（README）`  [AMBIGUOUS]
  docs/diagrams/readme-runtime-topology.svg · relation: semantically_similar_to
- `一次 run 的生命周期（parse→分组→begin→驱动→判定归约与报告）` → `图：scenario 到 job`  [AMBIGUOUS]
  docs/diagrams/writing-features-scenario-to-job.svg · relation: semantically_similar_to
- `执行与推进模型导览：run / submit × local / cloud` → `图：run 执行`  [AMBIGUOUS]
  docs/diagrams/run-execution.svg · relation: references

## Knowledge Gaps
- **526 isolated node(s):** `commit-gate.sh script`, `PATH`, `sync-derived.sh script`, `PATH`, `wording-guard.sh script` (+521 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **66 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0035 本机应用隧道暴露` and `图：本机应用测试隧道拓扑`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `ADR 0012 planning 复用引擎模型、不引独立文本规划器` and `ADR 0013 跨引擎共享边界`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `ci job: midscene worker（npm）` and `skill reference: 引擎选择与证据填充差异`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `eval fixture: tunnel-mismatch 待办应用` and `ADR 0043 驱动 gherkai 的 agent skill`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `五层结构（用例/产品/执行/浏览器/被测应用）` and `图：运行时拓扑（README）`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `一次 run 的生命周期（parse→分组→begin→驱动→判定归约与报告）` and `图：scenario 到 job`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `执行与推进模型导览：run / submit × local / cloud` and `图：run 执行`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._