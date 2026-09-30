# Graph Report - .  (2026-09-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 5343 nodes · 12251 edges · 239 communities (194 shown, 45 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 747 edges (avg confidence: 0.57)
- Token cost: 44,678 input · 4,227 output

## Graph Freshness
- Built from commit: `bf0ebbf2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Run Result Aggregation Tree
- Cloud Backend CLI Tests
- AWS Deploy Provider
- Worker Image Management Tests
- Cloud Store Adapters
- CLI Run Command Tests
- Job Domain Models
- Run State Projection
- Worker Image Lifecycle
- Run State Store
- Container Engine Wrapper
- CLI Docs and ADRs
- Step Execution Dispatch
- SSM Path Naming
- Cloud Resource Resolution
- CLI Entry and Plan
- Run Scheduling Core
- Glossary and Changelog
- Evidence Upload Tests
- Deploy Command Frontend Tests
- Core Protocol Documentation
- Agent Skill Doc Guards
- Nova Act Worker
- CLI Command Handlers
- Nova Worker Constants and Probes
- Typed Errors and Wire Protocol
- Reconciler Orchestration
- CDK Stack Synth Tests
- Step Evidence Records
- Skill Materialization Checks
- User Steps Loading
- Interrupt and Signal Handling
- Explain Rendering
- CDK App and Deploy CLI
- Worker Capability Queries
- Worker Variant Resolution
- Architecture Diagrams
- Doctor Self-Check
- Event Log Adapters
- Test Fixtures and Conftest
- Tunnel CLI Wiring
- Local Result Store
- Doc Rule Helpers
- S3 Store Adapters
- Deterministic Step Registry
- Skill and Packaging Features
- CDK Command Wrapper
- User Doc Guards
- Model Spike Scripts
- Midscene Run Scope
- Event Sink and Redaction
- Cloud Event Drain Tests
- Backend CDK Stack
- Atomic Write and Report Stores
- Local Report Store
- Midscene Evidence Builder
- Artifact Upload Tests
- Boto Guard and Arg Offload
- Engine Runtime Mechanisms
- Transient Error Detection
- Terminal UI Rendering
- Explain Command Tests
- Run Store Adapters
- Fargate Engine Tests
- Plan Parsing Tests
- Lambda Handler Tests
- Cloud Resource Preflight
- Event Formatting
- Artifact Uploader
- Nova Main Fakes
- Engine Composition Root
- Resource Naming Source
- Version Skew Check
- Skill and Release ADRs
- Synth and Lambda Asset Tests
- Project Conventions Glossary
- Midscene Resolve Hooks
- Local Detached Execution
- Fargate Engine Adapter
- Cloud Integration Tests
- TypeScript Config
- Job Source Input
- Log Pump and Redaction
- ADR Hygiene Checks
- Cloud Reconcile Tests
- Reconciler Lambda
- Cloud Launcher
- Tunnel Host Daemon
- Provider Resolution and Doctor
- Skill Install Command
- JSON Contract Guards
- CDK Invocation Fakes
- ECS Timeout Handling Tests
- Backend Version Stamp
- Local Reconcile Loop Tests
- Ngrok Tunnel Provider
- SQLite Event Log
- Task Definition Lineage Cleanup
- Stream Record Parsing Tests
- Safe Point Upload
- Wall Clock Timestamps
- Event Gap & ECS Polling
- Subprocess Engine Adapter Tests
- Worker Deploy CLI
- Artifact Uploader Component
- AWS & Playwright Dependencies
- Job Status Severity Aggregation
- Gherkin Feature Parsing
- Feature Planning Core
- SQLite Event Log
- Event Sink & Job Source
- Diagram Build Script
- Detached Run Mechanisms
- Deterministic Step Registry
- Evidence Collector Tests
- Run Status Rendering
- Result Store & Report Refs
- Job Worker Execution
- Fake Worker Test Doubles
- ECS Exit Code Extraction
- Release Notes Tooling
- Event Wall-Clock Analysis
- Plan CLI Command
- Scenario Selection Filters
- Release Notes Tests
- Deploy CLI Arguments
- Container Engine Errors
- Run Scope Tests
- Distribution Metadata Checks
- CLI Parser Construction
- Package README Guardrails
- Subprocess Worker Handle
- Scope Tag Grouping
- List Workers Command
- Artifact Upload Strategy
- Midscene Package Manifest
- Artifact Upload & Error Text
- Tunnel Provider
- DynamoDB Event Log
- Fargate Worker Handle
- Report Index Collection
- S3 Report Store Tests
- Architecture Diagrams
- Agent Skill Reference Docs
- Exit Observer Lambda
- Skill Deploy Token Tests
- Lambda IAM Permission Tests
- SSM Parameter Set Tests
- Step Argument & Sink Tests
- Skill Contract Rendering
- User-Facing Wording Guard
- CFN/SSM Client Stubs
- Tunnel Host Orchestration
- Lifecycle Status Model
- Worker Signal Interrupt Tests
- Fake Event Sink
- Task Definition Stop Timeout
- ECS Task Timing Script
- Task Definition Cleanup
- Local Subprocess Launcher
- Tunnel Origin Mapping
- E2E Test Harness
- Graph Refresh Script
- Cloud Store Wiring
- Cloud Status Command Tests
- Worker Task Def Resolution
- Naming & Prefix Conventions
- Advancement Channels
- Doc Rules Check
- Deploy Command Frontend
- Fake DynamoDB Table
- Finished Run Idempotence
- URL Redaction
- Report Store Artifacts
- Deploy/Destroy Dispatch
- Context Glossary Tests
- Task List Pagination
- Fake S3 Client
- Echo Test Worker
- Cloud Test Infrastructure
- EventBridge Timeout Watch
- Run ID Extraction
- TypeScript Dev Dependencies
- Release Pipeline Jobs
- Event Sequence Gap Handling
- Worker Subnet Single Source
- Worker Image Version Mappings
- Package Files Manifest
- Repository Metadata
- Nova Artifact Upload
- Upload Call Recorder
- Commit Gate Script
- Derived Sync Script
- Wording Guard Script
- Advancer Glossary Terms
- Backend & Preflight Terms
- Tick Failure Isolation
- Skill Evaluation Method
- Interactive Topology Diagrams
- NPM Scripts
- AgentCore CDP Entry Script
- Background Upload Queue
- Run Summary Script
- Pre-commit Hook Setup
- Bedrock AgentCore SDK Dependency
- DynamoDB Client Dependency
- Tunnel Watchdog Daemon
- Report Write Failure Fallback
- Adapters Implementation Layer
- Local Backend Preflight No-op
- Worker Delete Command Stub
- Timeout Path Single Assembly
- Per-Run Failure Isolation
- Provider Module Import Isolation
- Step Match Query Dispatch
- OpenAI Dependency
- TSX Dependency
- Upload Queue Drain
- Upload Enablement Check
- Fail-loud Config Validation
- No-op Local Uploader
- Index Wait Script
- Gherkai Workspace Root
- Machine-readable Output Contract
- Resource Retention Policy
- Fixture Portability Contract
- Trigger Rate Self-testing
- Hook Write-then-verify Checks
- Architecture Layering Diagram
- Run Lifecycle Diagram
- CI Packaging Smoke Job
- Gherkai Core Package
- AWS Deploy Package
- Gherkai Runtime Package
- NovaAct Worker Package
- Runtime Package README

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
- `artifact_upload.py (Nova uploader module)` --implements--> `ArtifactUploader（产物落点可注入组件）`  [INFERRED]
  artifact_upload.py → docs/adr/0029-engine-artifacts-to-s3.md
- `eval fixture: tunnel-mismatch 待办应用` --conceptually_related_to--> `ADR 0043 驱动 gherkai 的 agent skill`  [AMBIGUOUS]
  cli/skills/gherkai-evals/fixtures/tunnel-mismatch/README.md → docs/adr/0043-agent-skill-for-driving-gherkai.md
- `图：运行时拓扑（README）` --semantically_similar_to--> `五层结构（用例/产品/执行/浏览器/被测应用）`  [AMBIGUOUS] [semantically similar]
  docs/diagrams/readme-runtime-topology.svg → docs/internals/architecture-overview.md
- `图：scenario 到 job` --semantically_similar_to--> `一次 run 的生命周期（parse→分组→begin→驱动→判定归约与报告）`  [AMBIGUOUS] [semantically similar]
  docs/diagrams/writing-features-scenario-to-job.svg → docs/internals/architecture-overview.md
- `ADR 0035 本机应用隧道暴露` --references--> `图：本机应用测试隧道拓扑`  [AMBIGUOUS]
  docs/adr/0035-local-app-testing-via-tunnel.md → docs/diagrams/local-app-testing-tunnel-topology.svg

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **面向 AI agent 的驾驭链：契约 + 证据 + 教材** — docs_adr_0041_agent_facing_cli_affordances_json_contract, docs_adr_0042_step_evidence_and_explain_evidence, docs_adr_0042_step_evidence_and_explain_explain, docs_adr_0043_agent_skill_for_driving_gherkai_skill_md, docs_adr_0043_agent_skill_for_driving_gherkai_derived_copy [EXTRACTED 0.85]
- **AI 断言为主的可靠性纪律（投票 / 确定性 step / 柔性边界）** — docs_adr_0014_ai_first_assertions, docs_adr_0015_v1_positioning_smoke_not_regression, docs_adr_0014_assertion_voting, docs_adr_0015_flexible_leak_vs_flakiness, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold [EXTRACTED 0.85]
- **云端交付：五载体、升级传播顺序与 revision 固定共同决定改动何时生效** — docs_internals_cloud_backend_carriers_five_carriers, docs_internals_cloud_backend_carriers_upgrade_order, docs_internals_cloud_backend_carriers_revision_pinning, docs_internals_cloud_backend_carriers_prefix_environment, docs_internals_deterministic_step_lifecycle_truth_sources [EXTRACTED 0.85]
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
- **detached run 推进的三个触发源与共享 tick** — docs_adr_0034_detached_batch_reconciler_kicker_lambda, docs_adr_0034_detached_batch_reconciler_tick, docs_adr_0034_detached_batch_reconciler_exit_observer, docs_adr_0034_detached_batch_reconciler_events_table, docs_adr_0034_detached_batch_reconciler_runstate [EXTRACTED 0.90]
- **Gherkin tag 配置体系（scope/engine/timeout 三成员，同构的继承/冲突/缺省规则）** — docs_adr_0019_scope_tag, docs_adr_0019_engine_tag, docs_adr_0019_timeout_tag, docs_adr_0019_feature_tags_scope_and_engine, docs_adr_0025_plan_module_feature_to_jobs [EXTRACTED 0.90]
- **docs/internals 主题归属：七篇各拥有一个机制** — docs_internals_readme, docs_internals_architecture_overview, docs_internals_execution_and_reconciliation, docs_internals_verdict_model, docs_internals_artifacts_and_evidence, docs_internals_deterministic_step_lifecycle, docs_internals_cloud_backend_carriers, docs_internals_cli_json_contract [EXTRACTED 0.90]
- **job 生命周期态模型（态集 + severity + 聚合过滤 + 终态真源）** — docs_adr_0031_job_lifecycle_states_and_severity_status_skipped, docs_adr_0031_job_lifecycle_states_and_severity_status_aborted, docs_adr_0031_job_lifecycle_states_and_severity_status_pending_running, docs_adr_0031_job_lifecycle_states_and_severity_non_verdict, docs_adr_0031_job_lifecycle_states_and_severity_terminal_statuses [EXTRACTED 0.90]
- **Showcase Diagrams Sharing Bundled Font Bytes** — docs_diagrams_artifacts_evidence_chain_diagram, docs_diagrams_cloud_backend_carriers_revision_pinning_diagram, docs_diagrams_cloud_backend_upgrade_windows_diagram, docs_diagrams_cloud_delivery_identity_diagram, docs_diagrams_configuration_env_inheritance_diagram, docs_diagrams_deterministic_steps_registry_overview_diagram, docs_diagrams_deterministic_steps_truth_sources_diagram, docs_diagrams_execution_cloud_cascade_diagram, docs_diagrams_execution_detached_gates_diagram, docs_diagrams_execution_timeout_chain_diagram, docs_diagrams_getting_started_component_ownership_diagram, docs_diagrams_jetbrains_mono_embedded_font [EXTRACTED 0.90]
- **Symmetric Uploader Contract Across Nova and Midscene** — docs_adr_0029_engine_artifacts_to_s3_artifact_uploader, docs_adr_0029_engine_artifacts_to_s3_from_env, docs_adr_0029_engine_artifacts_to_s3_to_report_ref, docs_adr_0029_engine_artifacts_to_s3_flush_and_cleanup, docs_adr_0029_engine_artifacts_to_s3_snapshot_report, docs_adr_0029_engine_artifacts_to_s3_snapshot_logs [EXTRACTED 0.90]
- **终止契约三层（逻辑层 / 机制层 / worker 层）** — docs_adr_0026_schedule_module_graceful_termination, docs_adr_0024_worker_core_protocol_termination_contract, docs_adr_0024_worker_core_protocol_flag_only_handler, docs_adr_0024_worker_core_protocol_midscene_handler, docs_adr_0024_worker_core_protocol_grace_constraint [EXTRACTED 0.90]
- **判定计算链：归约层 → 状态 → 归因 → 严重度 → 退出码** — docs_internals_verdict_model_reduction_layers, docs_internals_verdict_model_statuses, docs_internals_verdict_model_error_type, docs_internals_verdict_model_severity, docs_internals_verdict_model_exit_codes [EXTRACTED 0.90]
- **worker 镜像从基础镜像到运行时 revision 的交付链** — docs_adr_0038_worker_image_delivery_base_image, docs_adr_0038_worker_image_delivery_variant, docs_adr_0038_worker_image_delivery_push_worker, docs_adr_0038_worker_image_delivery_default_pointer, docs_adr_0038_worker_image_delivery_explicit_revision, docs_adr_0037_distribution_and_packaging_steps_dir [EXTRACTED 0.90]
- **worker I/O 边缘三条可注入接口** — docs_adr_0024_worker_core_protocol_jobsource, docs_adr_0024_worker_core_protocol_eventsink, docs_adr_0029_engine_artifacts_to_s3_artifact_uploader [EXTRACTED 0.90]
- **Cloud Backend Lifecycle Diagram Group** — docs_diagrams_cloud_backend_carriers_revision_pinning_diagram, docs_diagrams_cloud_backend_upgrade_windows_diagram, docs_diagrams_cloud_delivery_identity_diagram, docs_diagrams_execution_cloud_cascade_diagram [INFERRED 0.60]
- **云端后端版本锁步：skew 闸 + deploy 升级顺序 + variant 重派生** — cli_development_version_skew_gate, cli_development_preflight_order, cli_gherkai_cli_skills_gherkai_references_cloud_backend_variant, cli_gherkai_cli_skills_gherkai_references_setup_and_diagnosis, docs_adr_0037_distribution_and_packaging [INFERRED 0.75]

## Communities (239 total, 45 thin omitted)

### Community 0 - "Run Result Aggregation Tree"
Cohesion: 0.04
Nodes (75): RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, render_text(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…, skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；…, step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。, job 行有分类、message 为 None → 只显分类 `(worker_crashed)`，不打 `(worker_crashed:…, 层级归属（ADR 0047）：原因与产物地址挂在所属 step 下，不挂到 scenario 或 job。 (+67 more)

### Community 1 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 2 - "AWS Deploy Provider"
Cohesion: 0.05
Nodes (90): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _AbsentEngine, _argv(), _parse(), _parse_destroy(), Path, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。… (+82 more)

### Community 3 - "Worker Image Management Tests"
Cohesion: 0.07
Nodes (86): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), datetime, `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。… (+78 more)

### Community 4 - "Cloud Store Adapters"
Cohesion: 0.05
Nodes (79): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, _job_state_from_item(), _job_state_to_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, JobState → DDB Map entry（字段集同 serialize；session_id/claimed_at 用 omit-when-…, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR… (+71 more)

### Community 5 - "CLI Run Command Tests"
Cohesion: 0.05
Nodes (83): _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：运行前先问一次能力自述，worker 非零退出 → 起任何 job 之前以退出码 2 结束（不进 job 级 error）。… (+75 more)

### Community 6 - "Job Domain Models"
Cohesion: 0.06
Nodes (65): _explain_job(), 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…, test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), _boto.py boto3 依赖守卫, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, Job (+57 more)

### Community 7 - "Run State Projection"
Cohesion: 0.07
Nodes (75): ScopeStarted, plan_next(), project(), project_full(), projected_run_status(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与…, 投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。… (+67 more)

### Community 8 - "Worker Image Lifecycle"
Cohesion: 0.05
Nodes (75): Aws, cleanup_pass(), _connect(), current_version_mappings(), _ecr_login(), _error_code(), _find_reusable(), _hours() (+67 more)

### Community 9 - "Run State Store"
Cohesion: 0.05
Nodes (65): run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_render_status_pending_run_with_claimed_job_does_not_hint(), DynamoDBRunStore, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→以退出码 2 结束）。 用 `table.load()`（即…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending… (+57 more)

### Community 10 - "Container Engine Wrapper"
Cohesion: 0.05
Nodes (51): ContainerEngine, digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+43 more)

### Community 11 - "CLI Docs and ADRs"
Cohesion: 0.08
Nodes (67): cli 包 contributor 文档, cloud preflight 次序（skew → 资源 → variant）, 版本 skew 六态闸, gherkai_cli/__main__.py（argparse 前端）, 柔性冒烟 (flexible smoke test), 柔性漏检, gherkai_core（纯库）, gherkai-deploy-aws contributor 手册 (+59 more)

### Community 12 - "Step Execution Dispatch"
Cohesion: 0.07
Nodes (51): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+43 more)

### Community 13 - "SSM Path Naming"
Cohesion: 0.05
Nodes (62): subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), ssm_worker_template_path() (+54 more)

### Community 14 - "Cloud Resource Resolution"
Cohesion: 0.05
Nodes (63): prune_empty_dirs(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`…, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, resolve_aws_identity() (+55 more)

### Community 15 - "CLI Entry and Plan"
Cohesion: 0.05
Nodes (59): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, main(), _det_feature(), 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。 (+51 more)

### Community 16 - "Run Scheduling Core"
Cohesion: 0.20
Nodes (56): 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+48 more)

### Community 17 - "Glossary and Changelog"
Cohesion: 0.06
Nodes (59): 变更记录 CHANGELOG, gherkai CLI README（PyPI 入口页）, agent skill, AgentCore 浏览器会话, AI 断言 (AI assertion), 产物指针 (artifact URI), 协作式停止, 派生视图 (derived view) (+51 more)

### Community 18 - "Evidence Upload Tests"
Cohesion: 0.08
Nodes (48): ArtifactUploader, _error_text(), _get_uploader(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, _done(), _Nova, _NovaRaisesAfterFirstVote, _picks() (+40 more)

### Community 19 - "Deploy Command Frontend Tests"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 前端自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 20 - "Core Protocol Documentation"
Cohesion: 0.06
Nodes (56): artifact_upload.py (Nova uploader module), core 包 contributor 文档, core 测试说明（单测 + 集成测试）, 成本信封（engine 只报原生量、core 只合计）, 流式 JSON Lines 事件流（三级 started/done 对齐）, reportRefs（不透明产物引用，kind 开放标签）, step_skipped 事件（scope 内短路）, 三通道分离传输（EVENTS_FD / stdout / stderr） (+48 more)

### Community 21 - "Agent Skill Doc Guards"
Cohesion: 0.05
Nodes (55): bare_flags(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags() (+47 more)

### Community 22 - "Nova Act Worker"
Cohesion: 0.06
Nodes (49): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _argument_text(), _attach_evidence(), _capabilities(), _clean_cell(), _collect_traj() (+41 more)

### Community 23 - "CLI Command Handlers"
Cohesion: 0.07
Nodes (54): _build_run_meta(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_explain(), _cmd_reconcile(), _cmd_run(), _cmd_skill_install(), _cmd_status() (+46 more)

### Community 24 - "Nova Worker Constants and Probes"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 25 - "Typed Errors and Wire Protocol"
Cohesion: 0.06
Nodes (49): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, _argument_to_json(), _cost_from_json(), event_from_json(), event_from_line() (+41 more)

### Community 26 - "Reconciler Orchestration"
Cohesion: 0.07
Nodes (41): event_log adapters（sqlite / ddb 持久事件通道）, EventLog, finalize_report(), Launcher, Job, Protocol, reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。 `tick(run_id, meta)` 一步推进：读…, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由… (+33 more)

### Community 27 - "CDK Stack Synth Tests"
Cohesion: 0.07
Nodes (49): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler/kicker）都要能读 `/{prefix}backend/*`（ADR 0038「权限面增量·云端推进器」）： 没有… (+41 more)

### Community 28 - "Step Evidence Records"
Cohesion: 0.06
Nodes (49): act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Any, Path (+41 more)

### Community 29 - "Skill Materialization Checks"
Cohesion: 0.09
Nodes (47): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+39 more)

### Community 30 - "User Steps Loading"
Cohesion: 0.07
Nodes (47): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+39 more)

### Community 31 - "Interrupt and Signal Handling"
Cohesion: 0.06
Nodes (33): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+25 more)

### Community 32 - "Explain Rendering"
Cohesion: 0.07
Nodes (44): _add_act(), _add_step(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), explain_to_dict() (+36 more)

### Community 33 - "CDK App and Deploy CLI"
Cohesion: 0.06
Nodes (38): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client(), Exception (+30 more)

### Community 34 - "Worker Capability Queries"
Cohesion: 0.06
Nodes (45): _ask_worker(), engine_min_grace(), local_artifact_locations(), match_deterministic(), Path, query_capabilities(), 继承一份 os.environ、抹掉组合根拥有的那些键（见 `_COMPOSE_OWNED_WORKER_ENV`）——所有注入 env 的起手式。…, spawn 一次某引擎 worker 的**非 job 入口**、收一行 JSON（ADR 0036「4.」/「5.」两个入口的共同机制）。 非 job… (+37 more)

### Community 35 - "Worker Variant Resolution"
Cohesion: 0.08
Nodes (44): _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。, 默认指针不存在（部署没走过 worker 镜像初始化）→ 提示运行 `gherkai deploy`，不猜 `base`。, SSM 无该（引擎，variant）映射 + CLI 与后端同版本 → 引导 push-worker，**不回落默认 variant**。 (+36 more)

### Community 36 - "Architecture Diagrams"
Cohesion: 0.07
Nodes (44): 图：五层全景, 图：一次 run 的主干, 图：证据链, 图：提交时刻固定 revision, 图：云端交付与 worker 身份拓扑, 图：确定性 step 注册表全景, 图：确定性 step 的两个真值源, 图：运行时拓扑（README） (+36 more)

### Community 37 - "Doctor Self-Check"
Cohesion: 0.07
Nodes (42): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+34 more)

### Community 38 - "Event Log Adapters"
Cohesion: 0.08
Nodes (37): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, ScopeDone, StepSkipped, StepStarted (+29 more)

### Community 39 - "Test Fixtures and Conftest"
Cohesion: 0.05
Nodes (41): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), aws(), _fake_aws_creds(), fargate(), moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表… (+33 more)

### Community 40 - "Tunnel CLI Wiring"
Cohesion: 0.09
Nodes (41): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。 (+33 more)

### Community 41 - "Local Result Store"
Cohesion: 0.09
Nodes (30): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+22 more)

### Community 42 - "Doc Rule Helpers"
Cohesion: 0.09
Nodes (37): ai_side_docs(), classify(), clean_flag(), code_comment_files(), CommandSpan, comment_units(), diagram_sources(), extract_command_spans() (+29 more)

### Community 43 - "S3 Store Adapters"
Cohesion: 0.07
Nodes (30): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。 (+22 more)

### Community 44 - "Deterministic Step Registry"
Cohesion: 0.08
Nodes (36): deterministic, clear(), deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match() (+28 more)

### Community 45 - "Skill and Packaging Features"
Cohesion: 0.07
Nodes (38): SKILL.md（随 CLI wheel 发行的 agent skill）, 隧道凭据脱敏（剥 URL userinfo）, --expose-local 与 URL 映射, RunMeta.extra_http_headers 注入通道, worker --capabilities 能力自述入口, CLI list-deterministic --engine, 注册面元数据（description / example 必填）, gherkai deploy（IaC 进 wheel、provider 中立） (+30 more)

### Community 46 - "CDK Command Wrapper"
Cohesion: 0.07
Nodes (26): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), cdk_command(), check_cdk(), check_node(), _make_sts_client(), _node_major(), Path (+18 more)

### Community 47 - "User Doc Guards"
Cohesion: 0.09
Nodes (36): changelog_unreleased(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, _default_model_claims(), _default_model_ids(), parametrize, Path, 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…, owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。 (+28 more)

### Community 48 - "Model Spike Scripts"
Cohesion: 0.07
Nodes (28): ADR-0008, ADR-0010, BASE_URL, main(), makePng(), REGION, BASE_URL, main() (+20 more)

### Community 49 - "Midscene Run Scope"
Cohesion: 0.09
Nodes (36): ADR-0019, ADR-0026, ADR-0027, ADR-0039, agentOpts(), aggregate(), appendReportRef(), artifactFlushRoot() (+28 more)

### Community 50 - "Event Sink and Redaction"
Cohesion: 0.07
Nodes (20): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, redact_url_userinfo(), EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +… (+12 more)

### Community 51 - "Cloud Event Drain Tests"
Cohesion: 0.11
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 52 - "Backend CDK Stack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 53 - "Atomic Write and Report Stores"
Cohesion: 0.09
Nodes (28): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, _fmt_ms() (+20 more)

### Community 54 - "Local Report Store"
Cohesion: 0.18
Nodes (33): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077…, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。 (+25 more)

### Community 55 - "Midscene Evidence Builder"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+21 more)

### Community 56 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 57 - "Boto Guard and Arg Offload"
Cohesion: 0.08
Nodes (21): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3… (+13 more)

### Community 58 - "Engine Runtime Mechanisms"
Cohesion: 0.06
Nodes (33): act 有界返回（per-act timeout）, 被拒方案：asyncio 化消除 greenlet, DynamoDB 共享 events 表（events-out 传输）, 被拒方案：DynamoDB Streams（同步 run 语境）, 引擎经 --capabilities 自报 min_grace_s, 事件流结束信号（内容完整 + 进程终止都要）, EventSink（事件 sink 可注入接口）, exitCode 落值延迟的有界宽限轮询 (+25 more)

### Community 59 - "Transient Error Detection"
Cohesion: 0.12
Nodes (31): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+23 more)

### Community 60 - "Terminal UI Rendering"
Cohesion: 0.12
Nodes (28): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。, 深度优先找第一个 label 含 needle 的节点（测试与诊断用）。, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，… (+20 more)

### Community 61 - "Explain Command Tests"
Cohesion: 0.10
Nodes (31): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+23 more)

### Community 62 - "Run Store Adapters"
Cohesion: 0.09
Nodes (18): RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, Path, 读回运行态（RunState）；不存在返回 None。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新…, CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。 (+10 more)

### Community 63 - "Fargate Engine Tests"
Cohesion: 0.10
Nodes (30): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。 (+22 more)

### Community 64 - "Plan Parsing Tests"
Cohesion: 0.12
Nodes (30): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否…, @scope 的值等于某条**自身已标 @scope** 的 scenario 的 id → 不报错：那条 id 根本没当分组键，不会撞。, 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ PlanError（ADR 0025：标了 tag…, test_assertion_votes_default_is_one() (+22 more)

### Community 65 - "Lambda Handler Tests"
Cohesion: 0.06
Nodes (30): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。, `_build` 的三层 store 全用它自己已建的那批句柄装配——compose 里建句柄的两个钩子在此一次都不该执行。 这条同时是「region… (+22 more)

### Community 66 - "Cloud Resource Preflight"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 67 - "Event Formatting"
Cohesion: 0.13
Nodes (26): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+18 more)

### Community 68 - "Artifact Uploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 69 - "Nova Main Fakes"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。 (+10 more)

### Community 70 - "Engine Composition Root"
Cohesion: 0.08
Nodes (30): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, Path, 某引擎定位链 miss **不连坐**另一个引擎项（ADR 0037 决策 3）：dev 下 midscene 未装是常态， novaact-only 的… (+22 more)

### Community 71 - "Resource Naming Source"
Cohesion: 0.09
Nodes (27): default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…, prefix + 基名（原样拼，prefix 含分隔符由部署方负责）。CDK 与 cli 共用此推导 → 单一事实源。 (+19 more)

### Community 72 - "Version Skew Check"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 73 - "Skill and Release ADRs"
Cohesion: 0.11
Nodes (28): gherkai agent skill 包, ADR 0004：Nova Act 经 Workflow 的 IAM 鉴权, ADR 0036：确定性能力自述与发现, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0043 驱动 gherkai 的 agent skill, skill 评测资产（决策七）, ADR 0044：引擎模型的选择与覆盖 (+20 more)

### Community 74 - "Synth and Lambda Asset Tests"
Cohesion: 0.11
Nodes (24): make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path, Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。… (+16 more)

### Community 75 - "Project Conventions Glossary"
Cohesion: 0.10
Nodes (26): 项目约定 CLAUDE.md, /code-health-review 入口, /doc-health-review 入口, doc-diagram 项目级 skill, 领域术语表 CONTEXT.md, 基础镜像 / variant / 默认指针, 执行核心库窄腰, 核心注入接口 (core ports) (+18 more)

### Community 76 - "Midscene Resolve Hooks"
Cohesion: 0.10
Nodes (14): ADR-0015, fromSource, hookSpec, ADR-0028, ADR-0037, ADR-0022, ADR-0036, ADR-0020 (+6 more)

### Community 77 - "Local Detached Execution"
Cohesion: 0.10
Nodes (25): build_local_reconcile(), cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-… (+17 more)

### Community 78 - "Fargate Engine Adapter"
Cohesion: 0.12
Nodes (16): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+8 more)

### Community 79 - "Cloud Integration Tests"
Cohesion: 0.15
Nodes (24): _ddb_store(), _is_ddb_too_large(), _offloader(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, 真 S3：DynamoDBRunStore 挂 offloader，docString/dataTable 搬真 S3、META 只留指针、读回逐字节还原。, 真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。, 真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛… (+16 more)

### Community 80 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 81 - "Job Source Input"
Cohesion: 0.09
Nodes (11): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+3 more)

### Community 82 - "Log Pump and Redaction"
Cohesion: 0.12
Nodes (20): _pump_log(), 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, Any, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_url_userinfo() (+12 more)

### Community 83 - "ADR Hygiene Checks"
Cohesion: 0.17
Nodes (20): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。 (+12 more)

### Community 84 - "Cloud Reconcile Tests"
Cohesion: 0.16
Nodes (20): DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, _meta(), _passed_worker_events(), _put_worker_event(), cloud 无状态批量运行 core 侧测试（ADR 0034 云端后端）：DdbEventLog + CloudLauncher +…, 多 scope：逐 scope Query 拼全量（不需 GSI）。, reconcile.tick 用 DdbEventLog + DynamoDBRunStore + CloudLauncher（fake… (+12 more)

### Community 85 - "Reconciler Lambda"
Cohesion: 0.14
Nodes (21): _build(), _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节的云端后端一侧）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…, 本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带… (+13 more)

### Community 86 - "Cloud Launcher"
Cohesion: 0.14
Nodes (17): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _job(), CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。, job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…, 无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。, 武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时， 先建的… (+9 more)

### Community 87 - "Tunnel Host Daemon"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 88 - "Provider Resolution and Doctor"
Cohesion: 0.12
Nodes (19): provider_entry_points(), 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。, 按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…, resolve_provider(), _cmd_doctor(), _cmd_list_engines(), _doctor_cloud(), _doctor_provider() (+11 more)

### Community 89 - "Skill Install Command"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 90 - "JSON Contract Guards"
Cohesion: 0.17
Nodes (18): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。, 递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque… (+10 more)

### Community 91 - "CDK Invocation Fakes"
Cohesion: 0.11
Nodes (16): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), cdk(), _CdkWritingContext, _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。 (+8 more)

### Community 92 - "ECS Timeout Handling Tests"
Cohesion: 0.10
Nodes (16): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的…, 仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…, task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录… (+8 more)

### Community 93 - "Backend Version Stamp"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 94 - "Local Reconcile Loop Tests"
Cohesion: 0.20
Nodes (19): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。 **真 spawn…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize… (+11 more)

### Community 95 - "Ngrok Tunnel Provider"
Cohesion: 0.15
Nodes (17): NgrokTunnel, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, TunnelInfo, _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。 (+9 more)

### Community 96 - "SQLite Event Log"
Cohesion: 0.15
Nodes (11): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+3 more)

### Community 97 - "Task Definition Lineage Cleanup"
Cohesion: 0.12
Nodes (17): _describe_revision(), _lineage_tags(), _parse_ts(), _pending_cleanup(), family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, `DescribeTaskDefinition(include=["TAGS"])` → (taskDefinition, tags dict)。, family 的全部 ACTIVE revision（带 tags）。 两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-… (+9 more)

### Community 98 - "Stream Record Parsing Tests"
Cohesion: 0.11
Nodes (19): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events… (+11 more)

### Community 99 - "Safe Point Upload"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…, act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _traj_refs(), _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 100 - "Wall Clock Timestamps"
Cohesion: 0.12
Nodes (19): now_iso(), parse_iso(), datetime, detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的… (+11 more)

### Community 101 - "Event Gap & ECS Polling"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 102 - "Subprocess Engine Adapter Tests"
Cohesion: 0.29
Nodes (17): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried() (+9 more)

### Community 103 - "Worker Deploy CLI"
Cohesion: 0.14
Nodes (9): 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点以退出码 2 结束）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…, flag → CDK context（app/stack 侧读的那四个配置项 + 版本戳）。 `--vpc` 一个 flag…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 解析链的诊断归口：解析得出 → target；失败 → 打一句诊断、返 None（调用点归退出码）。 **每个动作在碰 AWS 之前都要经这一口**：不存在的… (+1 more)

### Community 105 - "AWS & Playwright Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 106 - "Job Status Severity Aggregation"
Cohesion: 0.15
Nodes (11): 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一…, job 生命周期态 + severity 单测（ADR 0031）：skipped/aborted/pending/running、severity…, test_aggregate_all_skipped_no_error_not_misjudged_passed(), test_aggregate_filters_non_verdict(), test_aggregate_running_does_not_pollute_clean_pass() (+3 more)

### Community 107 - "Gherkin Feature Parsing"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 108 - "Feature Planning Core"
Cohesion: 0.19
Nodes (17): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只执行 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次运行哪几条。… (+9 more)

### Community 109 - "SQLite Event Log"
Cohesion: 0.18
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, 端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 110 - "Event Sink & Job Source"
Cohesion: 0.14
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0032, resolveEventsFd(), Job, JobSource

### Community 111 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 112 - "Detached Run Mechanisms"
Cohesion: 0.15
Nodes (17): CAS(pending→running) 并发闸, CQRS + 无状态 reconciler 机制, detached 顶层标记（推进链只碰 detached run）, events 表（append-only 真值日志）, 退出观察者（平台侧读 exitCode 写 task_exited）, HWM + 状态机单调条件写, job timeout（definition 载体 + 三路推进器各自 enforce）, kicker Lambda（冷启动推进器） (+9 more)

### Community 113 - "Deterministic Step Registry"
Cohesion: 0.13
Nodes (12): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, Match, matchBatch() (+4 more)

### Community 114 - "Evidence Collector Tests"
Cohesion: 0.15
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, importRunScope(), spyUploader() (+4 more)

### Community 115 - "Run Status Rendering"
Cohesion: 0.21
Nodes (16): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。 (+8 more)

### Community 116 - "Result Store & Report Refs"
Cohesion: 0.18
Nodes (15): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3(), 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, 单个 step 的归约结果（core 保留 step 级粒度，ADR 0024）。 duration_ms 是 step 墙钟时长（core 用…, ReportRef, ScenarioResult (+7 more)

### Community 117 - "Job Worker Execution"
Cohesion: 0.17
Nodes (10): _heartbeat_wrap(), Event, Job, 单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。, 运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…, _Worker (+2 more)

### Community 118 - "Fake Worker Test Doubles"
Cohesion: 0.18
Nodes (6): FakeWorkerHandle, Event, Job, _NetRaiseEngine, Event, victim job 的 worker：等一个 gate 放行后才抛 WorkerNetworkError（模拟「建连退避期间」被中止/超时后以退出码 80…

### Community 119 - "ECS Exit Code Extraction"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 120 - "Release Notes Tooling"
Cohesion: 0.17
Nodes (14): 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems(), is_botocore_error() (+6 more)

### Community 121 - "Event Wall-Clock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - "Plan CLI Command"
Cohesion: 0.13
Nodes (15): _build_selector(), _cmd_list_deterministic(), _cmd_plan(), _load_and_plan(), _probe_deterministic_dispatch(), plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…, 用例预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…, 把 `--scope` / `--tags` / `--scenario` 组装成 `plan(select=…)` 的谓词；都没给 → None（不筛）。… (+7 more)

### Community 123 - "Scenario Selection Filters"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 124 - "Release Notes Tests"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 125 - "Deploy CLI Arguments"
Cohesion: 0.19
Nodes (9): ArgumentParser, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6； 三者与…, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`… (+1 more)

### Community 126 - "Container Engine Errors"
Cohesion: 0.13
Nodes (9): ContainerError, Exception, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, CleanupOutcome, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看…, CountingEcs, boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。, ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。 (+1 more)

### Community 127 - "Run Scope Tests"
Cohesion: 0.13
Nodes (6): ADR-0014, ADR-0031, _events, fakePage, importMod(), testSink

### Community 128 - "Distribution Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 129 - "CLI Parser Construction"
Cohesion: 0.15
Nodes (14): _add_selection_flags(), _build_parser(), _dist_version(), ArgumentParser, run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。, 建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…, 发行版本字符串（唯一真源是 git tag，经 uv-dynamic-versioning 写进包元数据，ADR 0037 决策 2b；…, _tunnel_providers() (+6 more)

### Community 130 - "Package README Guardrails"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 131 - "Subprocess Worker Handle"
Cohesion: 0.18
Nodes (10): _join_pumps(), Event, Job, Popen, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的… (+2 more)

### Community 132 - "Scope Tag Grouping"
Cohesion: 0.26
Nodes (13): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。 (+5 more)

### Community 133 - "List Workers Command"
Cohesion: 0.14
Nodes (14): list_workers(), _mapped_arn(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 映射 JSON → 它引用的 revision ARN（读不懂 → 不产出）。 **读不懂时产出空** 有安全含义：那条映射保护不了它的…, 按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…, 读戳失败（无凭证/无权限）→ 退出码 2 + 一句人话。 `compose.read_backend_version`…, 建不出 client（这里用不存在的 profile 名）→ 退出码 2 + 一句人话，不吐 botocore 堆栈。… (+6 more)

### Community 134 - "Artifact Upload Strategy"
Cohesion: 0.22
Nodes (14): Act-Boundary Pre-Send (Level 3), ArtifactUploader（产物落点可注入组件）, S3 Landing Env Injection (ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX), uploader.flush_and_cleanup(dir), uploader.from_env(), Accepted Inherent Residue (Unrescued Artifacts), Delete Local Only On Full Upload Success, Nova _presend_act_siblings (name-derived sibling pre-send) (+6 more)

### Community 135 - "Midscene Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 136 - "Artifact Upload & Error Text"
Cohesion: 0.19
Nodes (9): CONTENT_TYPES, UPLOAD_TIMEOUT_MS, mkLogDir(), mkShots(), tmproot(), errorText(), oneLineError(), ADR-0042 (+1 more)

### Community 137 - "Tunnel Provider"
Cohesion: 0.18
Nodes (12): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。 (+4 more)

### Community 138 - "DynamoDB Event Log"
Cohesion: 0.15
Nodes (9): 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, events_pk(), events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。, DDB 侧 reason 属性 omit-when-empty、records() 读回进 TaskExited.reason（观察者落哨兵时的用户可见归因）。, test_ddb_record_exit_reason_roundtrip() (+1 more)

### Community 139 - "Fargate Worker Handle"
Cohesion: 0.15
Nodes (7): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

### Community 140 - "Report Index Collection"
Cohesion: 0.18
Nodes (10): collect_report_index(), local_path_from_uri(), Path, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…, 若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 **公开小工具**（本模块 href…, 遍历 result 树，把每个 ReportRef 投影成一条扁平 index 项（三级，ADR 0027）——**local/s3 共享的单一真理源**。…, _relative_href() (+2 more)

### Community 141 - "S3 Report Store Tests"
Cohesion: 0.31
Nodes (12): _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index(), test_index_html_links_and_summary(), test_index_html_taints_shortcircuited_step() (+4 more)

### Community 142 - "Architecture Diagrams"
Cohesion: 0.22
Nodes (13): Archify Diagram Accessibility & Preset Contract, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Environment Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram (+5 more)

### Community 143 - "Agent Skill Reference Docs"
Cohesion: 0.24
Nodes (12): skill reference: CLI --json 字段契约, skill reference: 云端后端与 variant 镜像, worker variant 与 push-worker, skill reference: 确定性 step 写法, skill reference: 引擎选择与证据填充差异, skill reference: 环境就位与排障, --expose-local 隧道前置与排障, gherkai agent SKILL.md (+4 more)

### Community 144 - "Exit Observer Lambda"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 145 - "Skill Deploy Token Tests"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。 (+3 more)

### Community 146 - "Lambda IAM Permission Tests"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 147 - "SSM Parameter Set Tests"
Cohesion: 0.17
Nodes (12): SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值为 task-def 的 `Ref`（**带 revision** 的 ARN）。…, _ssm_params(), test_prefix_switches_whole_set(), test_ssm_parameter_set_is_exactly_six(), test_ssm_version_parameter_from_context() (+4 more)

### Community 148 - "Step Argument & Sink Tests"
Cohesion: 0.21
Nodes (6): ADR-0024, argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 149 - "Skill Contract Rendering"
Cohesion: 0.26
Nodes (11): _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 150 - "User-Facing Wording Guard"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 151 - "CFN/SSM Client Stubs"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 152 - "Tunnel Host Orchestration"
Cohesion: 0.20
Nodes (9): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 153 - "Lifecycle Status Model"
Cohesion: 0.29
Nodes (10): _aggregate (run 级聚合), 退出码基于 run 级 severity, _NON_VERDICT 入口过滤名单, StepResult.shortcircuited (正交布尔), Status.ABORTED (core 派生态), Status.PENDING / RUNNING (生命周期前置态), Status.SKIPPED (core 派生态), step_skipped 独立 wire 事件 (+2 more)

### Community 154 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 155 - "Fake Event Sink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 156 - "Task Definition Stop Timeout"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 157 - "ECS Task Timing Script"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 158 - "Task Definition Cleanup"
Cohesion: 0.22
Nodes (4): 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 159 - "Local Subprocess Launcher"
Cohesion: 0.22
Nodes (6): Event, Job, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, SubprocessLauncher, Timer

### Community 160 - "Tunnel Origin Mapping"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 161 - "E2E Test Harness"
Cohesion: 0.36
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 162 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 163 - "Cloud Store Wiring"
Cohesion: 0.39
Nodes (8): compose.build_cloud_stores, compose.build_local_stores, DynamoDBRunStore, S3ReportStore, S3ResultStore, S3StepArgumentOffloader, Decision 7: cli cloud backend wiring, preflight and exit-code layering, Decision 6: cloud adapter persistence form (DDB/S3)

### Community 164 - "Cloud Status Command Tests"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 165 - "Worker Task Def Resolution"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 166 - "Naming & Prefix Conventions"
Cohesion: 0.25
Nodes (8): container 名契约 {engine}-worker, gherkai_runtime.names 命名单一真源, preflight fail-fast 点名 prefix, 产物前缀一致性语义探针, report ⊥ 执行（--no-report 不改执行环境）, subnet/sg ID 走含 prefix 的 SSM 路径, 两层命名：prefix 批量默认 + 单资源覆盖, VPC 三种取值 + 公有子网零 NAT

### Community 167 - "Advancement Channels"
Cohesion: 0.32
Nodes (8): detached 标记与两道拦截, 同一条事件流的四条物理通道, exit-observer Lambda（退出观察者）, kicker Lambda（冷启动器）, local per-run 推进进程（setsid 脱离 CLI）, reconcile.tick（无状态编排步骤）, reconciler Lambda（主推进器）, 由 gherkai 注入的环境变量

### Community 168 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 169 - "Deploy Command Frontend"
Cohesion: 0.33
Nodes (6): add_parsers(), _add_provider_flag(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。

### Community 171 - "Finished Run Idempotence"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 172 - "URL Redaction"
Cohesion: 0.29
Nodes (4): RFC-3986, MASK, ADR-0035, CASES

### Community 173 - "Report Store Artifacts"
Cohesion: 0.29
Nodes (7): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, JobResult 持有 Job、engine 经 property delegate, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 产物拷贝, ReportStore.write（整 run 一次写）, run_id（归集索引主键，组合根生成）

### Community 174 - "Deploy/Destroy Dispatch"
Cohesion: 0.33
Nodes (6): _cmd_deploy(), _cmd_destroy(), _deploy_provider(), 取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…, [部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。前端零 IaC 知识。 退出码即 provider…, [部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。

### Community 175 - "Context Glossary Tests"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 176 - "Task List Pagination"
Cohesion: 0.33
Nodes (6): n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。, STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。 ECS…, 目标落在 STOPPED 列表第二页、且没有退出记录 → 仍按 DescribeTasks 落它的真退出码，不臆造超时。, _stopped_filler(), test_handle_timeout_finds_stopped_target_on_second_page(), test_handle_timeout_pages_task_lists_and_batches_describe()

### Community 178 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 181 - "Run ID Extraction"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 182 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 183 - "Release Pipeline Jobs"
Cohesion: 0.50
Nodes (5): release job: gate + build, release job: base image（GHCR）, release job: publish npm, release job: publish PyPI, release job: GitHub Release

### Community 184 - "Event Sequence Gap Handling"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order()

### Community 185 - "Worker Subnet Single Source"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 186 - "Worker Image Version Mappings"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 187 - "Package Files Manifest"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 188 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 189 - "Nova Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 190 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 194 - "Advancer Glossary Terms"
Cohesion: 0.67
Nodes (3): 推进器 (advancer), job 墙钟预算, 无状态批量运行

### Community 195 - "Backend & Preflight Terms"
Cohesion: 0.67
Nodes (3): 执行后端 (backend), 执行方式 (execution mode), 执行前预检 (preflight)

### Community 197 - "Skill Evaluation Method"
Cohesion: 0.67
Nodes (3): 去污染硬规则（CLI 只读记哈希 / 舞台路径随机 / skill 副本仅 with-skill）, 被拒：在仓库内跑评测, 两臂评测法（with-skill vs baseline）

### Community 198 - "Interactive Topology Diagrams"
Cohesion: 0.67
Nodes (3): 云端交付与 worker 身份拓扑交互图, docs/diagrams/index.html（Pages 交互图入口）, 执行与推进全景交互图（run / submit × local / cloud）

### Community 199 - "NPM Scripts"
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
- **292 isolated node(s):** `Job`, `DeterministicAssertion`, `DeterministicConflict`, `DeterministicCtx`, `DeterministicHandler` (+287 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **45 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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