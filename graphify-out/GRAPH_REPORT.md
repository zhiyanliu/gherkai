# Graph Report - .  (2026-09-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 5407 nodes · 12199 edges · 253 communities (198 shown, 55 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 681 edges (avg confidence: 0.59)
- Token cost: 43,346 input · 4,650 output

## Graph Freshness
- Built from commit: `bf0ebbf2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Worker Log Event Formatting
- Lambda Handler Event Tests
- Package Contributor Docs
- CLI Run Wiring Tests
- Cloud Backend CLI Tests
- Result Tree Text Rendering
- Run State Rendering
- Worker Push Deploy Tests
- Worker Image Management
- CLI Test Fixtures
- Plan and Scope Seam
- CLI Command Entrypoints
- Composition Root Helpers
- Step and Scenario Execution
- Deploy Provider Tests
- Cloud Composition Helpers
- Core Adapters Documentation
- CDK Stack Synth Tests
- Scenario Evidence Keys
- Deploy Command Frontend Tests
- DynamoDB Run Store
- Run Definition Domain Model
- Agent Skill Reference Docs
- Report Store Adapters
- Cloud Launcher and EventLog
- Event Records Projection
- Nova Worker Library Setup
- Plan Command CLI Tests
- Resource Naming and Variants
- Nova Act Worker Runtime
- Skill Docs Guardrail Tests
- Deploy CLI Backend Helpers
- Skill Fixture Materialization
- Conditional Write Tests
- Event Wire Serialization
- Reconciler Mechanism Concepts
- Atomic Local Writes
- Interrupt and Signal Handling
- Doctor Self-check Tests
- Worker Event Sink
- Tunnel CLI Wiring Tests
- Result Store Serialization
- Architecture Diagrams
- SSM Path Naming
- Engine Capability Queries
- Reconcile Tick and Report
- Explain Tree Rendering
- Run Persistence Orchestration
- User Docs Guardrails
- Model Spike Scripts
- Midscene Run Scope Worker
- Rich Text UI Presentation
- Nova Worker Process Entry
- Worker Exit Drain Tests
- CDK Backend Stack
- Provider Deploy Commands
- Evidence Schema Builder
- Artifact Upload Tests
- Doc Rules Scan Sources
- Engine Runtime Mechanisms
- Transient Error Detection
- Deploy Provider Discovery
- Cloud Resource Preflight
- Agent Skill ADRs
- Explain Command Tests
- Exit Observer Lambda
- Artifact Uploader (Python)
- S3 Step Argument Offload
- AWS Deploy Provider
- Version Skew Checking
- Lambda Asset Synth Tests
- TypeScript Entry and Hooks
- User Steps Directory Loading
- Fargate Engine Adapter
- S3 Result Store
- Engine Listing and JSON Contract
- TypeScript Build Config
- Runtime Architecture Concepts
- Fargate Engine Tests
- ADR Hygiene Tests
- Explain Dict and Redaction
- Tunnel Host Watchdog
- Project Conventions Docs
- Agent Skill Installer
- Worker Job Source
- Step Argument Assembly
- Detached Reconcile Loop Tests
- SQLite Event Log
- State Projection Tests
- Terminal Color Policy
- Cloud Engine Resolver Build
- Deterministic Step Registry
- AWS Target Resolution
- Event Gap Grace Tests
- Artifact Uploader (TypeScript)
- NPM Dependencies
- Boto3 Adapter Guard
- SQLite Event Log Tests
- CDK Context Cache
- TypeScript Worker IO Edges
- Diagram Build Script
- Deterministic Registry (TS)
- Evidence Collector Tests
- Tunnel Origin Mapping
- Container Engine Wrapper
- Task Definition Revisions
- Container Engine Tests
- Version Stamp Skew Check
- Event Wallclock Analysis
- Release Notes Guardrails
- Run Scope Tests
- Distribution Metadata Checks
- CLI Argument Parser
- Package README Guardrails
- Subprocess Worker Handle
- Container Engine Resolution
- Worker Variant Listing
- CDK Deploy Argv Tests
- Worker Package Manifest
- Artifact Upload & Error Text
- Local Reconcile Rebuild
- Status Rendering & Exit Codes
- Feature File Parsing
- Artifact Pre-Send Uploads
- Architecture Diagrams
- ECS Task Exit Probing
- Advancer IAM Permissions
- Worker Step Arguments
- Deterministic Registry (Python)
- User Step Loading
- Worker Self-Describe Spawn
- Local Detached Reconcile
- Skill Contract Rendering
- User-Facing Text Guardrail
- AWS Client Stubs
- AWS Call Counting Spies
- Wallclock Timestamp Source
- Tunnel Host Orchestration
- Tunnel Provider Seam
- CLI Command Span Extraction
- Verdict Status Aggregation
- Fargate Naming & Wiring
- Worker Signal Interrupt Tests
- Fake Event Sink
- Worker Capabilities Subprocess
- Ngrok Tunnel Implementation
- ECS Task Timing Capture
- Fargate Worker Handle
- Skill Deploy Token Guardrail
- Task Def Stop Timeout
- Subprocess Launcher
- Graph Refresh Script
- Cloud Status Command
- Reconciler Plan Next
- CDK App & Backend Stack
- Container Engine Errors
- Release Notes Rendering
- Run Duration & Claims
- Doc Rules Check
- Fake DynamoDB Table
- Event Keys & Exit Records
- Image Platform Info
- URL Redaction
- Feature Parsing & Scoping
- Report Store Output
- Cloud Store Composition
- Context Glossary Guardrail
- AI Verdict Model Terms
- Run Data & Artifact Terms
- Projected Run Status
- Engine Probe & Inspect
- Artifact Rescue Decisions
- Single-Line Error Text
- Fake S3 Client
- Execution Session Terms
- Echo Test Worker
- Cloud Infra Test Baseline
- Repo Digest Selection
- Presentation Environment Independence
- Built-in Deterministic Steps
- TypeScript Dev Dependencies
- Release Pipeline Jobs
- Tunnel Process Teardown
- Skill Frontmatter Checks
- Event Sequence Gap Handling
- Live Run Revision References
- CDK Destroy Confirmation
- Worker Subnet Selection
- Image Parameter Filtering
- Package Distribution Files
- Repository Metadata
- Registry Self-Description
- Nova Artifact Upload
- Upload Call Recorder
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- Batch Run Advancer Terms
- Backend & Preflight Terms
- Tick Run Isolation
- Container Engine Probe Stub
- Skill Evaluation Isolation Rules
- Architecture Interaction Diagrams
- Build And Test Scripts
- AgentCore CDP Script
- Background Upload Queue
- Run Summary Script
- Pre-commit Hook Setup
- Bedrock AgentCore SDK Dependency
- DynamoDB SDK Dependency
- Tunnel Watch Daemon
- Report Write Failure Fallback
- Feature File Preflight
- Worker Emit Timestamp
- Adapters Implementation Layer
- Provider Module Import Guard
- Container Image Inspection
- Step Match Query
- OpenAI Dependency
- TSX Dependency
- Upload Queue Drain
- Upload Enablement Check
- Assembly Mismatch Fail-Loud
- No-op Local Uploader
- Index Wait Script
- Gherkai Workspace Root
- Runtime Package Version Pin
- CLI Argument Parsing
- Agent Skill
- Machine-Readable Output Contract
- Event Model
- Subprocess Popen Usage
- Cloud Resource Retention Policy
- Fixture Portability Contract
- Trigger Rate Self-Test
- Blocking Hook Checks
- Architecture Layering Diagram
- Run Lifecycle Diagram
- Submit-Time Revision Pinning
- Cloud Worker Identity Topology
- Test Fixtures
- Package Build Smoke CI
- Gherkai Core Package
- AWS Deploy Package
- Gherkai Runtime Package
- NovaAct Worker Package
- Run Metadata
- Base Exception Handling
- Runtime Error Handling
- Runtime Package README

## God Nodes (most connected - your core abstractions)
1. `main()` - 216 edges
2. `Job` - 129 edges
3. `RunState` - 127 edges
4. `RunMeta` - 117 edges
5. `JobState` - 101 edges
6. `Status` - 97 edges
7. `Provider` - 95 edges
8. `JobResult` - 82 edges
9. `Scenario` - 72 edges
10. `Step` - 71 edges

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

## Communities (253 total, 55 thin omitted)

### Community 0 - "Worker Log Event Formatting"
Cohesion: 0.05
Nodes (135): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), _pump_log(), scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。 (+127 more)

### Community 1 - "Lambda Handler Event Tests"
Cohesion: 0.02
Nodes (117): _FakeEcs, _FakeSchedulerClient, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。 (+109 more)

### Community 2 - "Package Contributor Docs"
Cohesion: 0.05
Nodes (116): cli 包 contributor 文档, cloud preflight 次序（skew → 资源 → variant）, 版本 skew 六态闸, gherkai_cli/__main__.py（argparse 前端）, compose.build_local_stores, 柔性冒烟 (flexible smoke test), 柔性漏检, gherkai_core（纯库） (+108 more)

### Community 3 - "CLI Run Wiring Tests"
Cohesion: 0.03
Nodes (109): _capturing_schedule(), _explain_cloud_stores(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), _plan_names(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json… (+101 more)

### Community 4 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 5 - "Result Tree Text Rendering"
Cohesion: 0.05
Nodes (77): RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, render_text(), 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…, skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；…, step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。 (+69 more)

### Community 6 - "Run State Rendering"
Cohesion: 0.04
Nodes (68): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_render_status_pending_run_with_claimed_job_does_not_hint(), test_render_run_state_lists_jobs_and_session_lineage() (+60 more)

### Community 7 - "Worker Push Deploy Tests"
Cohesion: 0.07
Nodes (84): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+76 more)

### Community 8 - "Worker Image Management"
Cohesion: 0.05
Nodes (83): Aws, cleanup_pass(), CleanupOutcome, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+75 more)

### Community 9 - "CLI Test Fixtures"
Cohesion: 0.03
Nodes (78): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), aws(), _fake_aws_creds(), fargate(), 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。 (+70 more)

### Community 10 - "Plan and Scope Seam"
Cohesion: 0.06
Nodes (73): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig, Job (+65 more)

### Community 11 - "CLI Command Entrypoints"
Cohesion: 0.05
Nodes (70): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_explain(), _cmd_list_deterministic(), _cmd_plan(), _cmd_reconcile() (+62 more)

### Community 12 - "Composition Root Helpers"
Cohesion: 0.05
Nodes (68): FeatureSource, build_engines(), load_feature(), prune_empty_dirs(), Path, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env… (+60 more)

### Community 13 - "Step and Scenario Execution"
Cohesion: 0.07
Nodes (51): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+43 more)

### Community 14 - "Deploy Provider Tests"
Cohesion: 0.06
Nodes (63): _argv(), _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，…, 子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。, `--prefix` 在子动词**前**给也必须留住——子 parser 在新 namespace 里解析后整体覆盖回父层，…, 留口子：以退出码 2 结束并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。 (+55 more)

### Community 15 - "Cloud Composition Helpers"
Cohesion: 0.05
Nodes (58): BaseException, check_backend_skew(), _find_worker_spec(), is_botocore_error(), local_artifact_locations(), _make_ecr_client(), _make_ecs_client(), _make_lambda_client() (+50 more)

### Community 16 - "Core Adapters Documentation"
Cohesion: 0.05
Nodes (35): core 包 contributor 文档, adapters/_atomic.py 原子落盘, adapters/_boto.py boto3 依赖守卫, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, adapters/event_log（sqlite / ddb）, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, adapters/report_store（local / s3）, adapters/result_store（local / s3） (+27 more)

### Community 17 - "CDK Stack Synth Tests"
Cohesion: 0.06
Nodes (61): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。 (+53 more)

### Community 18 - "Scenario Evidence Keys"
Cohesion: 0.08
Nodes (51): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), list, parametrize (+43 more)

### Community 19 - "Deploy Command Frontend Tests"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 20 - "DynamoDB Run Store"
Cohesion: 0.06
Nodes (49): DynamoDBRunStore, _job_state_from_item(), _job_state_to_item(), 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→以退出码 2 结束）。 用 `table.load()`（即…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, 一次性写完整态（即 create_run 的两 item 一起 put；语义同 local save_run）。, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。… (+41 more)

### Community 21 - "Run Definition Domain Model"
Cohesion: 0.09
Nodes (51): _explain_job(), 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…, test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), Job, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。, 一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。 (+43 more)

### Community 22 - "Agent Skill Reference Docs"
Cohesion: 0.07
Nodes (55): Midscene 默认模型改为 us.openai.gpt-5.6-terra, Nova Act 默认模型固定为 nova-act-v1.0, skill reference: CLI --json 字段契约, skill reference: 云端后端与 variant 镜像, worker variant 与 push-worker, skill reference: 确定性 step 写法, skill reference: 引擎选择与证据填充差异, agent skill 参考：环境就位与排障 (+47 more)

### Community 23 - "Report Store Adapters"
Cohesion: 0.11
Nodes (51): LocalReportStore, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef (+43 more)

### Community 24 - "Cloud Launcher and EventLog"
Cohesion: 0.07
Nodes (44): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, _FakeStartEngine, _job(), _meta() (+36 more)

### Community 25 - "Event Records Projection"
Cohesion: 0.09
Nodes (51): 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, ScopeStarted, StepStarted, EventRecord, project_full(), 平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。 **不是 worker 的 wire 事件**（不在…, events 表里一条记录的投影输入（ADR 0034）：reconciler 从表全量重放时，每条 record 携带的信息。 worker… (+43 more)

### Community 26 - "Nova Worker Library Setup"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 27 - "Plan Command CLI Tests"
Cohesion: 0.06
Nodes (50): main(), _det_feature(), 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。, 冲突预检（实际运行将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。 (+42 more)

### Community 28 - "Resource Naming and Variants"
Cohesion: 0.07
Nodes (52): ecr_repo_name(), （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…, 引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag…, task_def_name(), worker_image_key(), test_task_def_and_container_name(), test_ecr_repo_name_is_task_def_name() (+44 more)

### Community 29 - "Nova Act Worker Runtime"
Cohesion: 0.06
Nodes (44): ArtifactUploader, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, _act_record(), _attach_evidence(), _attach_traj_refs(), _collect_traj(), _cost_from_result(), _drain_evidence_uploads() (+36 more)

### Community 30 - "Skill Docs Guardrail Tests"
Cohesion: 0.06
Nodes (51): bare_flags(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags() (+43 more)

### Community 31 - "Deploy CLI Backend Helpers"
Cohesion: 0.05
Nodes (44): cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client() (+36 more)

### Community 32 - "Skill Fixture Materialization"
Cohesion: 0.09
Nodes (47): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+39 more)

### Community 33 - "Conditional Write Tests"
Cohesion: 0.08
Nodes (48): _initial(), _meta(), RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+40 more)

### Community 34 - "Event Wire Serialization"
Cohesion: 0.07
Nodes (46): scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, StepSkipped, _argument_to_json(), _cost_from_json(), event_from_json(), event_from_line(), job_to_json(), job_to_line() (+38 more)

### Community 35 - "Reconciler Mechanism Concepts"
Cohesion: 0.05
Nodes (48): CAS(pending→running) 并发闸, CQRS + 无状态 reconciler 机制, detached 顶层标记（推进链只碰 detached run）, events 表（append-only 真值日志）, 退出观察者（平台侧读 exitCode 写 task_exited）, HWM + 状态机单调条件写, job timeout（definition 载体 + 三路推进器各自 enforce）, kicker Lambda（冷启动推进器） (+40 more)

### Community 36 - "Atomic Local Writes"
Cohesion: 0.06
Nodes (38): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index() (+30 more)

### Community 37 - "Interrupt and Signal Handling"
Cohesion: 0.06
Nodes (34): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+26 more)

### Community 38 - "Doctor Self-check Tests"
Cohesion: 0.07
Nodes (42): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+34 more)

### Community 39 - "Worker Event Sink"
Cohesion: 0.06
Nodes (23): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, redact_url_userinfo() (+15 more)

### Community 40 - "Tunnel CLI Wiring Tests"
Cohesion: 0.09
Nodes (41): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。 (+33 more)

### Community 41 - "Result Store Serialization"
Cohesion: 0.08
Nodes (37): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, _argument_from_dict(), _argument_to_dict(), from_dict(), job_from_dict() (+29 more)

### Community 42 - "Architecture Diagrams"
Cohesion: 0.07
Nodes (42): 图：五层全景, 图：一次 run 的主干, 图：确定性 step 注册表全景, 图：确定性 step 的两个真值源, 图：运行时拓扑（README）, 图：run 执行, 图：job 判定结果, 图：判定四层归约 (+34 more)

### Community 43 - "SSM Path Naming"
Cohesion: 0.06
Nodes (37): 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 生效 VPC 取值的 SSM 路径（ADR 0037 决策 6「VPC 取值持久化比对，三态齐全」）。 值形态三种：`default` / `new:<所建…, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_security_groups_path(), ssm_subnets_path() (+29 more)

### Community 44 - "Engine Capability Queries"
Cohesion: 0.06
Nodes (41): engine_min_grace(), match_deterministic(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc() (+33 more)

### Community 45 - "Reconcile Tick and Report"
Cohesion: 0.10
Nodes (35): finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), _done_events(), FakeLauncher, _meta(), Job (+27 more)

### Community 46 - "Explain Tree Rendering"
Cohesion: 0.09
Nodes (38): _add_act(), _add_step(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), explain_tree() (+30 more)

### Community 47 - "Run Persistence Orchestration"
Cohesion: 0.10
Nodes (32): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run 就是 commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的… (+24 more)

### Community 48 - "User Docs Guardrails"
Cohesion: 0.09
Nodes (36): changelog_unreleased(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, _default_model_claims(), _default_model_ids(), parametrize, Path, 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…, owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。 (+28 more)

### Community 49 - "Model Spike Scripts"
Cohesion: 0.07
Nodes (28): ADR-0008, ADR-0010, BASE_URL, main(), makePng(), REGION, BASE_URL, main() (+20 more)

### Community 50 - "Midscene Run Scope Worker"
Cohesion: 0.09
Nodes (36): ADR-0019, ADR-0026, ADR-0027, ADR-0039, agentOpts(), aggregate(), appendReportRef(), artifactFlushRoot() (+28 more)

### Community 51 - "Rich Text UI Presentation"
Cohesion: 0.10
Nodes (33): ADR 0047 CLI 人读输出用 rich 渲染, rich 渲染库, 判定与状态的语义颜色映射, worker 日志前缀颜色（按 job 启动顺序）, NO_COLOR / FORCE_COLOR 颜色开关, _as_text(), _console(), output_width() (+25 more)

### Community 52 - "Nova Worker Process Entry"
Cohesion: 0.07
Nodes (23): worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _capabilities(), main(), 本 worker 的能力声明（`--capabilities` 的 stdout，ADR 0036「5.」）。 `min_grace_s` 是 grace…, _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes() (+15 more)

### Community 53 - "Worker Exit Drain Tests"
Cohesion: 0.11
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 54 - "CDK Backend Stack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 55 - "Provider Deploy Commands"
Cohesion: 0.08
Nodes (17): Path, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点以退出码 2 结束）。… (+9 more)

### Community 56 - "Evidence Schema Builder"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+21 more)

### Community 57 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 58 - "Doc Rules Scan Sources"
Cohesion: 0.12
Nodes (30): ai_side_docs(), classify(), code_comment_files(), comment_units(), diagram_sources(), long_term_docs(), Path, 人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。 内容三类：①规则——内部指代表 FORBIDDEN、口吻表… (+22 more)

### Community 59 - "Engine Runtime Mechanisms"
Cohesion: 0.06
Nodes (33): act 有界返回（per-act timeout）, 被拒方案：asyncio 化消除 greenlet, DynamoDB 共享 events 表（events-out 传输）, 被拒方案：DynamoDB Streams（同步 run 语境）, 引擎经 --capabilities 自报 min_grace_s, 事件流结束信号（内容完整 + 进程终止都要）, EventSink（事件 sink 可注入接口）, exitCode 落值延迟的有界宽限轮询 (+25 more)

### Community 60 - "Transient Error Detection"
Cohesion: 0.12
Nodes (31): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+23 more)

### Community 61 - "Deploy Provider Discovery"
Cohesion: 0.08
Nodes (29): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+21 more)

### Community 62 - "Cloud Resource Preflight"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 63 - "Agent Skill ADRs"
Cohesion: 0.10
Nodes (30): gherkai agent skill 包, SKILL.md（随 CLI wheel 发行的 agent skill）, ADR 0004：Nova Act 经 Workflow 的 IAM 鉴权, ADR 0036：确定性能力自述与发现, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0043 驱动 gherkai 的 agent skill, skill 评测资产（决策七） (+22 more)

### Community 64 - "Explain Command Tests"
Cohesion: 0.10
Nodes (30): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+22 more)

### Community 65 - "Exit Observer Lambda"
Cohesion: 0.09
Nodes (28): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+20 more)

### Community 66 - "Artifact Uploader (Python)"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 67 - "S3 Step Argument Offload"
Cohesion: 0.09
Nodes (21): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore…, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。 (+13 more)

### Community 68 - "AWS Deploy Provider"
Cohesion: 0.10
Nodes (22): Provider, ArgumentParser, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。 (+14 more)

### Community 69 - "Version Skew Checking"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 70 - "Lambda Asset Synth Tests"
Cohesion: 0.11
Nodes (24): make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path, Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。… (+16 more)

### Community 71 - "TypeScript Entry and Hooks"
Cohesion: 0.10
Nodes (14): ADR-0015, fromSource, hookSpec, ADR-0028, ADR-0037, ADR-0022, ADR-0036, ADR-0020 (+6 more)

### Community 72 - "User Steps Directory Loading"
Cohesion: 0.13
Nodes (25): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` 是 env `GHERKAI_STEPS_DIR`…, parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, `_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。, `_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。, 给了目录但不存在就是配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。 (+17 more)

### Community 73 - "Fargate Engine Adapter"
Cohesion: 0.12
Nodes (16): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+8 more)

### Community 74 - "S3 Result Store"
Cohesion: 0.12
Nodes (17): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore, S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…, test_load_all_paginated_preserves_failed_verdict() (+9 more)

### Community 75 - "Engine Listing and JSON Contract"
Cohesion: 0.13
Nodes (22): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…, _assert_documented(), _documented_keys(), _leaf_keys(), _mk() (+14 more)

### Community 76 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 77 - "Runtime Architecture Concepts"
Cohesion: 0.10
Nodes (23): 基础镜像 / variant / 默认指针, 执行核心库窄腰, 核心注入接口 (core ports), 部署 provider, 确定性 step 注册表, 执行引擎 port (engine port), 版本真源 (single version source), steps 目录 / 定制面 (+15 more)

### Community 78 - "Fargate Engine Tests"
Cohesion: 0.13
Nodes (22): _await_engine(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。, 执行 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env() (+14 more)

### Community 79 - "ADR Hygiene Tests"
Cohesion: 0.17
Nodes (20): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。 (+12 more)

### Community 80 - "Explain Dict and Redaction"
Cohesion: 0.13
Nodes (18): explain_to_dict(), 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, Any, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_url_userinfo() (+10 more)

### Community 81 - "Tunnel Host Watchdog"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 82 - "Project Conventions Docs"
Cohesion: 0.17
Nodes (20): 变更记录 (CHANGELOG), --max-concurrency 默认值改为 4, 项目约定 CLAUDE.md, /code-health-review 入口, /doc-health-review 入口, doc-diagram 项目级 skill, 领域术语表 CONTEXT.md, 护栏 (guardrail) (+12 more)

### Community 83 - "Agent Skill Installer"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 84 - "Worker Job Source"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 85 - "Step Argument Assembly"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 86 - "Detached Reconcile Loop Tests"
Cohesion: 0.20
Nodes (19): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。 **真 spawn…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize… (+11 more)

### Community 87 - "SQLite Event Log"
Cohesion: 0.15
Nodes (10): Connection, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。… (+2 more)

### Community 88 - "State Projection Tests"
Cohesion: 0.14
Nodes (19): project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, _passed_events(), 两件都要齐（scope_done 与 exit=0 都齐）→ 终态取 scenario 归约（passed）。, 关键（机制二）：scope_done 说 passed，但 exit_code!=0 → 判 ERROR（防"发完 scope_done 又非0退出"误报）。, SIGKILL 截断 exit=137 → ERROR（实测 payload 带 137，机制二）。, high_water_mark 是所有 scope 的 worker 段 max seq（exit 记录无 seq、不参与）。, 多 scope：HWM 取跨 scope 的全局 max。 (+11 more)

### Community 89 - "Terminal Color Policy"
Cohesion: 0.20
Nodes (15): color_env_override(), 终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…, 环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…, 写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。, stream_is_tty(), use_color(), _clean_env(), _Pipe (+7 more)

### Community 90 - "Cloud Engine Resolver Build"
Cohesion: 0.11
Nodes (19): Engine, build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), make_resolver(), _make_s3_client(), _normalize_prefix(), dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。 (+11 more)

### Community 91 - "Deterministic Step Registry"
Cohesion: 0.16
Nodes (18): deterministic(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 运行（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真 step 命中面与派发一致）。, description/example 必填（ADR 0036：注册即暴露，缺元数据意味着能力不可发现，fail-loud）。, 注册表清单经自述入口出去（ADR 0036「2.」/「5.」）真子进程：`--capabilities` 的 `deterministic_steps`… (+10 more)

### Community 92 - "AWS Target Resolution"
Cohesion: 0.12
Nodes (18): CloudTarget, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`…, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序即链上顺序。, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_aws_identity(), resolve_cloud_target(), _clear_aws_env() (+10 more)

### Community 93 - "Event Gap Grace Tests"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 95 - "NPM Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 96 - "Boto3 Adapter Guard"
Cohesion: 0.13
Nodes (9): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。 把一次 run 的…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。 (+1 more)

### Community 97 - "SQLite Event Log Tests"
Cohesion: 0.17
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 98 - "CDK Context Cache"
Cohesion: 0.15
Nodes (16): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, Path, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按… (+8 more)

### Community 99 - "TypeScript Worker IO Edges"
Cohesion: 0.14
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0032, resolveEventsFd(), Job, JobSource

### Community 100 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 101 - "Deterministic Registry (TS)"
Cohesion: 0.13
Nodes (12): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, Match, matchBatch() (+4 more)

### Community 102 - "Evidence Collector Tests"
Cohesion: 0.15
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, importRunScope(), spyUploader() (+4 more)

### Community 103 - "Tunnel Origin Mapping"
Cohesion: 0.18
Nodes (15): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, TunnelInfo, _job_with(), Job (+7 more)

### Community 104 - "Container Engine Wrapper"
Cohesion: 0.16
Nodes (8): ContainerEngine, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。, 拉镜像（基础镜像同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。, 短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。, 长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。, docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 结构不同）。 `binary`…, test_probe_reports_missing_binary_without_raising()

### Community 105 - "Task Definition Revisions"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 106 - "Container Engine Tests"
Cohesion: 0.18
Nodes (12): _Fake, _inspect_spec(), 容器引擎口子测试（ADR 0038「容器引擎口子」）。 **两层证据，分清边界**： - 大部分用一个**假 docker**（记 argv/stdin 的…, 「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。, **密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。, 假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。, test_inspect_missing_image_is_not_an_error(), test_inspect_other_failure_raises() (+4 more)

### Community 107 - "Version Stamp Skew Check"
Cohesion: 0.15
Nodes (14): _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口前端只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到不等于放过。, _StampSsm, test_check_backend_skew_missing_stamp_warns_not_raises() (+6 more)

### Community 108 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 109 - "Release Notes Guardrails"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 110 - "Run Scope Tests"
Cohesion: 0.13
Nodes (6): ADR-0014, ADR-0031, _events, fakePage, importMod(), testSink

### Community 111 - "Distribution Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 112 - "CLI Argument Parser"
Cohesion: 0.15
Nodes (14): ArgumentParser, _add_selection_flags(), _build_parser(), _cmd_skill_install(), _installed_version(), run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。, 建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…, [使用方] 把包内那份 agent skill 收敛安装到目标目录（行为与判据见 `skill_install` 模块头，ADR 0043 决策三）。… (+6 more)

### Community 113 - "Package README Guardrails"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 114 - "Subprocess Worker Handle"
Cohesion: 0.18
Nodes (10): _join_pumps(), Job, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的…, _read_events(), SubprocessWorkerHandle (+2 more)

### Community 115 - "Container Engine Resolution"
Cohesion: 0.18
Nodes (14): 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, resolve_container_engine(), ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。…, arm 变体真镜像 → 架构判据拒（即 push-worker 以退出码 2 结束那一支）。 用 alpine（小）代替真 worker 镜像：判据只看…, `docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取…, `--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。, test_default_is_docker(), test_env_selects_engine_and_flag_wins() (+6 more)

### Community 116 - "Worker Variant Listing"
Cohesion: 0.14
Nodes (14): list_workers(), _mapped_arn(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 映射 JSON → 它引用的 revision ARN（读不懂 → 不产出）。 **读不懂时产出空** 有安全含义：那条映射保护不了它的…, 版本 skew 前置：block → 以退出码 2 结束（无放行口）；warn/skip → 打一行继续；ok → 静默；**读不到戳（凭证/权限）…, 按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…, _skew_gate() (+6 more)

### Community 117 - "CDK Deploy Argv Tests"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+3 more)

### Community 118 - "Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 119 - "Artifact Upload & Error Text"
Cohesion: 0.19
Nodes (9): CONTENT_TYPES, UPLOAD_TIMEOUT_MS, mkLogDir(), mkShots(), tmproot(), errorText(), oneLineError(), ADR-0042 (+1 more)

### Community 120 - "Local Reconcile Rebuild"
Cohesion: 0.19
Nodes (14): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, 后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。, 对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…, 接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从… (+6 more)

### Community 121 - "Status Rendering & Exit Codes"
Cohesion: 0.15
Nodes (13): _args(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。, test_render_status_json_no_hint() (+5 more)

### Community 122 - "Feature File Parsing"
Cohesion: 0.21
Nodes (12): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+4 more)

### Community 123 - "Artifact Pre-Send Uploads"
Cohesion: 0.23
Nodes (13): Act-Boundary Pre-Send (Level 3), ArtifactUploader（产物落点可注入组件）, S3 Landing Env Injection (ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX), uploader.flush_and_cleanup(dir), uploader.from_env(), Accepted Inherent Residue (Unrescued Artifacts), Delete Local Only On Full Upload Success, Nova _presend_act_siblings (name-derived sibling pre-send) (+5 more)

### Community 124 - "Architecture Diagrams"
Cohesion: 0.22
Nodes (13): Archify Diagram Accessibility & Preset Contract, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Environment Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram (+5 more)

### Community 125 - "ECS Task Exit Probing"
Cohesion: 0.17
Nodes (10): _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped() (+2 more)

### Community 126 - "Advancer IAM Permissions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 127 - "Worker Step Arguments"
Cohesion: 0.21
Nodes (6): ADR-0024, argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 128 - "Deterministic Registry (Python)"
Cohesion: 0.20
Nodes (11): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+3 more)

### Community 129 - "User Step Loading"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 130 - "Worker Self-Describe Spawn"
Cohesion: 0.20
Nodes (9): _ask_worker(), worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…, 定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退出码交调用点。 **继承 RuntimeError…, 继承一份 os.environ、抹掉组合根拥有的那些键（见 `_COMPOSE_OWNED_WORKER_ENV`）——所有注入 env 的起手式。…, spawn 一次某引擎 worker 的**非 job 入口**、收一行 JSON（ADR 0036「4.」/「5.」两个入口的共同机制）。 非 job…, scrubbed_environ(), WorkerNotFoundError, WorkerSelfDescribeError (+1 more)

### Community 131 - "Local Detached Reconcile"
Cohesion: 0.18
Nodes (11): cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。 (+3 more)

### Community 132 - "Skill Contract Rendering"
Cohesion: 0.26
Nodes (11): _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 133 - "User-Facing Text Guardrail"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 134 - "AWS Client Stubs"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 135 - "AWS Call Counting Spies"
Cohesion: 0.18
Nodes (6): CountingEcs, boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。, ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。, 重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…, Spy, test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine()

### Community 136 - "Wallclock Timestamp Source"
Cohesion: 0.20
Nodes (11): now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, _job(), run 级墙钟取数失败不得连坐报告收尾（ADR 0030 决定三：commit point 之后的失败无人重试）。 墙钟是派生指标，取它要在 finalize…, region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…, RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的…, test_build_local_reconcile_reads_steps_dir_from_definition() (+3 more)

### Community 137 - "Tunnel Host Orchestration"
Cohesion: 0.20
Nodes (9): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 138 - "Tunnel Provider Seam"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 139 - "CLI Command Span Extraction"
Cohesion: 0.20
Nodes (10): clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, 一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。, _deploy_spans() (+2 more)

### Community 140 - "Verdict Status Aggregation"
Cohesion: 0.29
Nodes (10): _aggregate (run 级聚合), 退出码基于 run 级 severity, _NON_VERDICT 入口过滤名单, StepResult.shortcircuited (正交布尔), Status.ABORTED (core 派生态), Status.PENDING / RUNNING (生命周期前置态), Status.SKIPPED (core 派生态), step_skipped 独立 wire 事件 (+2 more)

### Community 141 - "Fargate Naming & Wiring"
Cohesion: 0.24
Nodes (10): build_fargate_engines 组合根接线, container 名契约 {engine}-worker, gherkai_runtime.names 命名单一真源, preflight fail-fast 点名 prefix, 产物前缀一致性语义探针, report ⊥ 执行（--no-report 不改执行环境）, subnet/sg ID 走含 prefix 的 SSM 路径, task-def 不焊 region/凭证 (+2 more)

### Community 142 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 143 - "Fake Event Sink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 144 - "Worker Capabilities Subprocess"
Cohesion: 0.20
Nodes (10): _clean_env(), 真子进程 + 真 env：`-m gherkai_worker_novaact --capabilities` 的 `deterministic_steps`…, fail-loud 到进程边界：坏 step 文件 → 自述入口也非 0 退出、stderr 指名文件（不静默给出残缺清单）。, 加载成功也留一行 stderr（文件数 + 目录）：使用方据它分清「目录没被读到」与「pattern 没命中」。, 未注入目录表示使用方没定制，正常路径不打这行（诊断行不许变成人人都看见的噪声）。, 子进程 env：保留 PATH/PYTHONPATH 等运行必需项，剥掉可能干扰的 GHERKAI_* / AWS 落点。, test_broken_steps_dir_makes_capabilities_exit_nonzero(), test_capabilities_subprocess_includes_user_steps() (+2 more)

### Community 145 - "Ngrok Tunnel Implementation"
Cohesion: 0.24
Nodes (9): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。, test_ngrok_binary_missing_reports_install_hint(), test_ngrok_start_spawns_agent_and_reads_log(), test_ngrok_start_timeout_reports_authtoken_hint() (+1 more)

### Community 146 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 147 - "Fargate Worker Handle"
Cohesion: 0.22
Nodes (5): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

### Community 148 - "Skill Deploy Token Guardrail"
Cohesion: 0.25
Nodes (8): _build(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。, test_provider_only_flag_table_is_backed_by_the_real_parser()

### Community 149 - "Task Def Stop Timeout"
Cohesion: 0.31
Nodes (7): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container()

### Community 150 - "Subprocess Launcher"
Cohesion: 0.22
Nodes (6): Event, Job, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, SubprocessLauncher, Timer

### Community 151 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 152 - "Cloud Status Command"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 153 - "Reconciler Plan Next"
Cohesion: 0.29
Nodes (8): Action, plan_next(), reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, 全 pending、max_concurrency=2 → 提议 start 前 2 个。, 所有 job 达终态（无 pending/running）→ 提议 finalize。, test_plan_next_finalize_when_all_terminal(), test_plan_next_starts_up_to_concurrency()

### Community 154 - "CDK App & Backend Stack"
Cohesion: 0.29
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 155 - "Container Engine Errors"
Cohesion: 0.29
Nodes (6): ContainerError, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, UnsupportedContainerEngine

### Community 156 - "Release Notes Rendering"
Cohesion: 0.43
Nodes (7): main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems(), ValueError

### Community 157 - "Run Duration & Claims"
Cohesion: 0.25
Nodes (8): parse_iso(), datetime, detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), test_run_duration_ms_from_run_state_timestamps()

### Community 158 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 160 - "Event Keys & Exit Records"
Cohesion: 0.29
Nodes (5): 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。, test_events_pk_composite_run_id_scope_id()

### Community 161 - "Image Platform Info"
Cohesion: 0.29
Nodes (5): ImageInfo, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。, test_target_platform_judgement()

### Community 162 - "URL Redaction"
Cohesion: 0.29
Nodes (4): RFC-3986, MASK, ADR-0035, CASES

### Community 163 - "Feature Parsing & Scoping"
Cohesion: 0.29
Nodes (7): gherkin-official（Parser + Compiler）, id 派生（稳定 + 可追溯）, Job（scope = 会话边界）, parse seam（藏 gherkin-official）, plan() 接口, scope seam（tag 分组 + engine/timeout 校验）, select 谓词（scenario 筛选）

### Community 164 - "Report Store Output"
Cohesion: 0.29
Nodes (7): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, JobResult 持有 Job、engine 经 property delegate, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 产物拷贝, ReportStore.write（整 run 一次写）, run_id（归集索引主键，组合根生成）

### Community 165 - "Cloud Store Composition"
Cohesion: 0.60
Nodes (6): compose.build_cloud_stores, DynamoDBRunStore, S3ReportStore, S3ResultStore, S3StepArgumentOffloader, Decision 6: cloud adapter persistence form (DDB/S3)

### Community 166 - "Context Glossary Guardrail"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 167 - "AI Verdict Model Terms"
Cohesion: 0.33
Nodes (6): AI 断言 (AI assertion), 引擎模型 (engine model), 判定抖动 (flakiness), 模型家族 (model family), 默认模型锁定 (pinned default model), 票 / 投票 (vote / voting)

### Community 168 - "Run Data & Artifact Terms"
Cohesion: 0.33
Nodes (6): 产物指针 (artifact URI), 派生视图 (derived view), Run 数据模型, 安全点提前上传, step 证据 (step evidence), 判定真值 (verdict truth)

### Community 169 - "Projected Run Status"
Cohesion: 0.33
Nodes (6): projected_run_status(), 投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。…, 全 job pending → pending（run 还没起过任何 job）；任一 job 推进 → running；恒非终态（终态归 finalize）。, 判据只看 job 态：project() 的 run 级 status 是终态聚合值（零事件的全 pending run 也吐 PASSED）， 喂它的…, test_projected_run_status_ignores_aggregate_value_from_project(), test_projected_run_status_pending_only_while_all_jobs_pending()

### Community 170 - "Engine Probe & Inspect"
Cohesion: 0.33
Nodes (4): 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。, _tail()

### Community 171 - "Artifact Rescue Decisions"
Cohesion: 0.33
Nodes (6): 容器盘停即销毁导致的中断产物丢失, 孤儿产物扫盘 reaper（经分析否决）, act/step 安全点提前上传, task role IAM 最小权限, job-in 对象按 tag 的 7 天 lifecycle, job-in 独立前缀 jobs-in/

### Community 172 - "Single-Line Error Text"
Cohesion: 0.33
Nodes (6): _error_text(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…, 隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。, test_error_text_prefers_sdk_message_and_is_single_line(), test_error_text_redacts_before_truncation()

### Community 174 - "Execution Session Terms"
Cohesion: 0.40
Nodes (5): AgentCore 浏览器会话, 协作式停止, 引擎 (engine), 停止宽限期, 隧道暴露 (tunnel exposure)

### Community 175 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 177 - "Repo Digest Selection"
Cohesion: 0.40
Nodes (5): digest_for_repo(), 从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。…, 基础镜像同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def**…, test_digest_none_when_repo_absent_or_empty(), test_digest_picked_by_repo_not_first_entry()

### Community 178 - "Presentation Environment Independence"
Cohesion: 0.40
Nodes (5): aws(), _aws_env(), _presentation_is_environment_independent(), fixture, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。

### Community 179 - "Built-in Deterministic Steps"
Cohesion: 0.40
Nodes (4): deterministic, 确定性 step 脚手架（ADR 0020/0022）—— **本包内建**的示范 step，随 worker 发行。 用途：少数"必须精确、不容 AI…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言…, url_matches()

### Community 180 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 181 - "Release Pipeline Jobs"
Cohesion: 0.50
Nodes (5): release job: gate + build, release job: base image（GHCR）, release job: publish npm, release job: publish PyPI, release job: GitHub Release

### Community 182 - "Tunnel Process Teardown"
Cohesion: 0.40
Nodes (5): 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 183 - "Skill Frontmatter Checks"
Cohesion: 0.50
Nodes (4): _frontmatter_and_body(), 极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。 支持 `key: 单行值`、引号值，以及 `key:…, `name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环…, test_skill_form_limits()

### Community 184 - "Event Sequence Gap Handling"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order()

### Community 185 - "Live Run Revision References"
Cohesion: 0.50
Nodes (4): _non_terminal_statuses(), 未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…, 有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…, _referenced_by_live_run()

### Community 186 - "CDK Destroy Confirmation"
Cohesion: 0.50
Nodes (4): _parse_destroy(), cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。, test_destroy_yes_passes_force_to_cdk_and_is_off_by_default(), Namespace

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

### Community 191 - "Registry Self-Description"
Cohesion: 0.50
Nodes (4): list_registry(), 注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。, test_list_registry_reflects_registrations(), test_loads_recursively_in_sorted_order_and_registers()

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

### Community 201 - "Skill Evaluation Isolation Rules"
Cohesion: 0.67
Nodes (3): 去污染硬规则（CLI 只读记哈希 / 舞台路径随机 / skill 副本仅 with-skill）, 被拒：在仓库内跑评测, 两臂评测法（with-skill vs baseline）

### Community 202 - "Architecture Interaction Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, docs/diagrams/index.html（Pages 交互图入口）, 执行与推进全景交互图（run / submit × local / cloud）

### Community 203 - "Build And Test Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

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
- **302 isolated node(s):** `DeterministicAssertion`, `DeterministicConflict`, `DeterministicCtx`, `DeterministicHandler`, `DeterministicMeta` (+297 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **55 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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