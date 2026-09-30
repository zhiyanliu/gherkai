# Graph Report - yaozhou  (2026-09-30)

## Corpus Check
- 337 files · ~540,904 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5349 nodes · 12134 edges · 234 communities (188 shown, 46 thin omitted)
- Extraction: 94% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 661 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5113f8fb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_subprocess_engine.py
- Cloud Backend CLI Tests
- Provider
- test_workers.py
- Status
- test_main.py
- Job
- test_project.py
- workers.py
- test_conditional_writes.py
- ContainerEngine
- ADR 0016 执行架构与分层
- Step Execution Dispatch
- compose.py
- resolve_worker_cmd
- main
- test_schedule.py
- 变更记录 CHANGELOG
- test_evidence.py
- Deploy Command Frontend Tests
- plan() 接口
- test_skill.py
- run_scope.py
- gherkai_cli/__main__.py
- Nova Worker Constants and Probes
- model.py
- build_cloud_stores
- test_stack.py
- _fixture
- Skill Materialization Checks
- test_user_steps.py
- test_interrupt_model.py
- render.py
- cli.py
- query_capabilities
- test_worker_variant.py
- 架构全景（internals）
- _fake_locator
- resolve_cloud_target
- core/tests/conftest.py
- Tunnel CLI Wiring
- RunResult
- Doc Rule Helpers
- S3ResultStore
- Deterministic Step Registry
- SKILL.md（住 CLI 包内、随 wheel 发行的单份内容）
- ._run_cdk
- test_user_docs.py
- Model Spike Scripts
- Midscene Run Scope
- test_event_sink.py
- _engine
- BackendStack
- atomic_write_json
- Local Report Store
- Midscene Evidence Builder
- Artifact Upload Tests
- S3StepArgumentOffloader
- ADR 0028: 瞬时网络/SSL 韧性
- _is_transient_network
- textui.py
- Explain Command Tests
- build_local_stores
- Fargate Engine Tests
- Plan Parsing Tests
- test_lambda_handlers.py
- _FakeEcsClient
- test_argument.py
- Artifact Uploader
- Nova Main Fakes
- test_compose.py
- image_tag
- _release_cmp
- ADR 0043 驱动 gherkai 的 agent skill
- test_lambda_asset.py
- Project Conventions Glossary
- Midscene Resolve Hooks
- test_detached_launcher.py
- FargateEngine
- RunState
- TypeScript Config
- JobSource
- redact_url_userinfo
- test_adr_hygiene.py
- require_boto3
- reconciler.py
- test_cloud_reconcile.py
- test_tunnel_host.py
- _cmd_doctor
- Skill Install Command
- test_cli_json_contract.py
- _CdkWritingContext
- ECS Timeout Handling Tests
- _StampSsm
- gherkai_deploy_aws/names.py
- test_tunnel.py
- SqliteEventLog
- scan_family
- _stream_record
- test_container.py
- resolve_container_engine
- _gap_engine
- cleanup_pass
- _Recorder
- Artifact Uploader Component
- AWS & Playwright Dependencies
- _argv
- Gherkin Feature Parsing
- Feature Planning Core
- Path
- Event Sink & Job Source
- Diagram Build Script
- _FakeProc
- Deterministic Step Registry
- Evidence Collector Tests
- _render_status
- container.py
- ImageInfo
- arg_offload.py
- ECS Exit Code Extraction
- ValueError
- Event Wall-Clock Analysis
- .inspect
- _tagged_feature
- Release Notes Tests
- .add_arguments
- test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine
- Run Scope Tests
- Distribution Metadata Checks
- _build_parser
- Package README Guardrails
- _read_events
- Scope Tag Grouping
- _out
- ArtifactUploader（产物落点可注入组件）
- Midscene Package Manifest
- Artifact Upload & Error Text
- tunnel.py
- events_pk
- .run_scope
- report_store/local.py
- _run_with_refs
- Architecture Diagrams
- gherkai agent SKILL.md
- digest_for_repo
- Skill Deploy Token Tests
- Lambda IAM Permission Tests
- aws
- Step Argument & Sink Tests
- Skill Contract Rendering
- User-Facing Wording Guard
- CFN/SSM Client Stubs
- gherkai_runtime/__init__.py
- test_read_events_ignores_exit_item_on_stopped_drain_path
- Worker Signal Interrupt Tests
- Fake Event Sink
- _StopTimeoutEcs
- ECS Task Timing Script
- _AbsentEngine
- ._pump
- Tunnel Origin Mapping
- E2E Test Harness
- Graph Refresh Script
- compose.build_cloud_stores
- Cloud Status Command Tests
- _seed_run
- build_fargate_engines 组合根接线
- reconcile.tick（无状态编排步骤）
- Doc Rules Check
- .inspect
- Fake DynamoDB Table
- Finished Run Idempotence
- URL Redaction
- Report Store Artifacts
- ArgumentParser
- Context Glossary Tests
- Task List Pagination
- Fake S3 Client
- Echo Test Worker
- Cloud Test Infrastructure
- BaseException
- Run ID Extraction
- TypeScript Dev Dependencies
- Release Pipeline Jobs
- RuntimeError
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
- Adapters Implementation Layer
- Local Backend Preflight No-op
- Worker Delete Command Stub
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
4. `RunMeta` - 119 edges
5. `JobState` - 101 edges
6. `Status` - 98 edges
7. `Provider` - 95 edges
8. `JobResult` - 82 edges
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

## Communities (234 total, 46 thin omitted)

### Community 0 - "test_subprocess_engine.py"
Cohesion: 0.05
Nodes (59): _atomic.py 原子落盘, _boto.py boto3 依赖守卫, report_store（local / s3 ReportStore）, result_store（local / s3 ResultStore）, run_store（local / ddb RunStore）, RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`… (+51 more)

### Community 1 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 2 - "Provider"
Cohesion: 0.06
Nodes (76): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, flag 面全集锁定（枚举型护栏）：三个 context 配置项 flag + AWS 定位二件套 + 两个「前端的中立版的 AWS 精确化」（见 cli…, `--allow-vpc-change` / `--require-approval` **只贴 deploy**（枚举型全集比对，同上条口径）。…, 子动词全集锁定（枚举型护栏）+ **只挂 deploy**。 挂到 destroy 上不是「多个没用的命令」而是危险：前端的 destroy 分派不看… (+68 more)

### Community 3 - "test_workers.py"
Cohesion: 0.08
Nodes (70): _cleanup(), FakeContainer, _mapping(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 一次干净的推送：tag/push 到 ECR ref → 从模板注册 revision（镜像按 digest、血缘 tags 齐）→ 写 SSM 映射。, digest 的唯一来源是 **推送后**那次 inspect，且在多条 `RepoDigests` 里**按本 repo 挑**（GHCR 那条在第一位）。 (+62 more)

### Community 4 - "Status"
Cohesion: 0.04
Nodes (104): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, _job_state_from_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`… (+96 more)

### Community 5 - "test_main.py"
Cohesion: 0.04
Nodes (93): _capturing_schedule(), _explain_cloud_stores(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。 (+85 more)

### Community 6 - "Job"
Cohesion: 0.03
Nodes (118): RunResult → 人看的判定汇总树（job → scenario → step，带时长、成本与报告指针；ADR 0047）。…, render_text(), _explain_job(), 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…, test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；…, step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。 (+110 more)

### Community 7 - "test_project.py"
Cohesion: 0.06
Nodes (77): event_log adapters（sqlite / ddb 持久事件通道）, ScopeStarted, plan_next(), project(), project_full(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→… (+69 more)

### Community 8 - "workers.py"
Cohesion: 0.06
Nodes (74): Aws, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable(), ImageMapping (+66 more)

### Community 9 - "test_conditional_writes.py"
Cohesion: 0.07
Nodes (50): _initial(), _meta(), RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+42 more)

### Community 10 - "ContainerEngine"
Cohesion: 0.16
Nodes (8): ContainerEngine, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。, 拉镜像（基础镜像同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。, 短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。, 长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。, docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 结构不同）。 `binary`…, test_probe_reports_missing_binary_without_raising()

### Community 11 - "ADR 0016 执行架构与分层"
Cohesion: 0.06
Nodes (95): cli 包 contributor 文档, cloud preflight 次序（skew → 资源 → variant）, 版本 skew 六态闸, gherkai_cli/__main__.py（argparse 前端）, compose.build_local_stores, 柔性冒烟 (flexible smoke test), 柔性漏检, core 包 contributor 文档 (+87 more)

### Community 12 - "Step Execution Dispatch"
Cohesion: 0.07
Nodes (51): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+43 more)

### Community 13 - "compose.py"
Cohesion: 0.05
Nodes (57): BaseException, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_worker_template_path(), is_botocore_error(), _make_ecr_client(), _make_ecs_client(), _make_lambda_client(), _make_ssm_client() (+49 more)

### Community 14 - "resolve_worker_cmd"
Cohesion: 0.06
Nodes (34): _ask_worker(), _find_worker_spec(), 一个引擎 worker 的拉起方式即定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂 `SubprocessEngine`；**cwd…, worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…, 定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退出码交调用点。 **继承 RuntimeError…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。 (+26 more)

### Community 15 - "main"
Cohesion: 0.05
Nodes (57): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, main(), _det_feature(), 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。 (+49 more)

### Community 16 - "test_schedule.py"
Cohesion: 0.10
Nodes (91): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。 (+83 more)

### Community 17 - "变更记录 CHANGELOG"
Cohesion: 0.06
Nodes (60): 变更记录 CHANGELOG, gherkai CLI README（PyPI 入口页）, agent skill, AgentCore 浏览器会话, AI 断言 (AI assertion), 产物指针 (artifact URI), 协作式停止, 派生视图 (derived view) (+52 more)

### Community 18 - "test_evidence.py"
Cohesion: 0.07
Nodes (57): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _error_text(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, _done(), _Nova, _NovaRaisesAfterFirstVote, _picks() (+49 more)

### Community 19 - "Deploy Command Frontend Tests"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 前端自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 20 - "plan() 接口"
Cohesion: 0.29
Nodes (7): gherkin-official（Parser + Compiler）, id 派生（稳定 + 可追溯）, Job（scope = 会话边界）, parse seam（藏 gherkin-official）, plan() 接口, scope seam（tag 分组 + engine/timeout 校验）, select 谓词（scenario 筛选）

### Community 21 - "test_skill.py"
Cohesion: 0.05
Nodes (57): bare_flags(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, skill_markdown_files(), _all_command_spans(), _allowed_flags() (+49 more)

### Community 22 - "run_scope.py"
Cohesion: 0.06
Nodes (48): ArtifactUploader, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _attach_traj_refs(), _capabilities(), _collect_traj() (+40 more)

### Community 23 - "gherkai_cli/__main__.py"
Cohesion: 0.05
Nodes (72): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_explain(), _cmd_list_deterministic(), _cmd_plan(), _cmd_reconcile() (+64 more)

### Community 24 - "Nova Worker Constants and Probes"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 25 - "model.py"
Cohesion: 0.04
Nodes (87): 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…, test_index_html_shortcircuit_note_matches_cli_wording(), CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core… (+79 more)

### Community 26 - "build_cloud_stores"
Cohesion: 0.08
Nodes (27): Engine, build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), make_resolver(), _make_s3_client(), _normalize_prefix() (+19 more)

### Community 27 - "test_stack.py"
Cohesion: 0.06
Nodes (60): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。 (+52 more)

### Community 28 - "_fixture"
Cohesion: 0.06
Nodes (52): _presentation_is_environment_independent(), cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities(), events_table(), events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——云端后端测试单独建，schema 见 ADR 0033/0024。, _clean_aws_env(), 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。 (+44 more)

### Community 29 - "Skill Materialization Checks"
Cohesion: 0.09
Nodes (47): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+39 more)

### Community 30 - "test_user_steps.py"
Cohesion: 0.07
Nodes (49): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+41 more)

### Community 31 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (35): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+27 more)

### Community 32 - "render.py"
Cohesion: 0.09
Nodes (36): _add_act(), _add_step(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), explain_tree() (+28 more)

### Community 33 - "cli.py"
Cohesion: 0.06
Nodes (42): cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client() (+34 more)

### Community 34 - "query_capabilities"
Cohesion: 0.06
Nodes (41): engine_min_grace(), match_deterministic(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc() (+33 more)

### Community 35 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (48): aws(), _fake_aws_creds(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。 (+40 more)

### Community 36 - "架构全景（internals）"
Cohesion: 0.06
Nodes (55): skill reference: CLI --json 字段契约, reportRefs（不透明产物引用，kind 开放标签）, ADR 0027 RunReport 归集索引, ADR 0029 引擎产物上传 S3, S3 Key Mirrors Local Run Tree, S3ReportStore (manifest + index only, href==ref), Upload Whole Artifact Directory (Type-Agnostic), ADR 0032 Fargate 执行环境 (+47 more)

### Community 37 - "_fake_locator"
Cohesion: 0.08
Nodes (38): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+30 more)

### Community 38 - "resolve_cloud_target"
Cohesion: 0.09
Nodes (23): CloudTarget, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`…, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序即链上顺序。, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_aws_identity(), resolve_cloud_target(), default_name() (+15 more)

### Community 39 - "core/tests/conftest.py"
Cohesion: 0.12
Nodes (15): aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, 挂了 S3 offload 的 DynamoDBRunStore：RunMeta 的 docString/dataTable 搬 S3、META 只留指针。 (+7 more)

### Community 40 - "Tunnel CLI Wiring"
Cohesion: 0.09
Nodes (41): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。 (+33 more)

### Community 41 - "RunResult"
Cohesion: 0.08
Nodes (35): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, 一次执行的机器可读汇总判定，即 **definition（run_meta）与判定（jobs）的显式合成**（ADR 0016/0026）。…, RunResult, Event (+27 more)

### Community 42 - "Doc Rule Helpers"
Cohesion: 0.09
Nodes (37): ai_side_docs(), classify(), clean_flag(), code_comment_files(), CommandSpan, comment_units(), diagram_sources(), extract_command_spans() (+29 more)

### Community 43 - "S3ResultStore"
Cohesion: 0.19
Nodes (8): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore, 配好的 S3ResultStore（注入 aws fixture 建好的桶），供 ResultStore 对拍测试。, s3_result_store()

### Community 44 - "Deterministic Step Registry"
Cohesion: 0.08
Nodes (36): deterministic, clear(), deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match() (+28 more)

### Community 45 - "SKILL.md（住 CLI 包内、随 wheel 发行的单份内容）"
Cohesion: 0.06
Nodes (46): CAS(pending→running) 并发闸, CQRS + 无状态 reconciler 机制, detached 顶层标记（推进链只碰 detached run）, events 表（append-only 真值日志）, 退出观察者（平台侧读 exitCode 写 task_exited）, HWM + 状态机单调条件写, job timeout（definition 载体 + 三路推进器各自 enforce）, kicker Lambda（冷启动推进器） (+38 more)

### Community 46 - "._run_cdk"
Cohesion: 0.08
Nodes (19): Path, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。 (+11 more)

### Community 47 - "test_user_docs.py"
Cohesion: 0.09
Nodes (38): changelog_unreleased(), prose_lines(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _default_model_claims(), _default_model_ids(), parametrize, Path (+30 more)

### Community 48 - "Model Spike Scripts"
Cohesion: 0.07
Nodes (28): ADR-0008, ADR-0010, BASE_URL, main(), makePng(), REGION, BASE_URL, main() (+20 more)

### Community 49 - "Midscene Run Scope"
Cohesion: 0.09
Nodes (36): ADR-0019, ADR-0026, ADR-0027, ADR-0039, agentOpts(), aggregate(), appendReportRef(), artifactFlushRoot() (+28 more)

### Community 50 - "test_event_sink.py"
Cohesion: 0.06
Nodes (23): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, redact_url_userinfo() (+15 more)

### Community 51 - "_engine"
Cohesion: 0.13
Nodes (30): _engine(), _job(), _put_event(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。, worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。, worker 发完 scope_done 又非 0 退出（会话释放失败，Midscene cleanupFailed→exit 1）： scope_done… (+22 more)

### Community 52 - "BackendStack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 53 - "atomic_write_json"
Cohesion: 0.13
Nodes (20): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+12 more)

### Community 54 - "Local Report Store"
Cohesion: 0.18
Nodes (33): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077…, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。 (+25 more)

### Community 55 - "Midscene Evidence Builder"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+21 more)

### Community 56 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 57 - "S3StepArgumentOffloader"
Cohesion: 0.19
Nodes (8): 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore…, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, S3StepArgumentOffloader, arg_offloader(), 配好的 S3StepArgumentOffloader（注入 aws fixture 建好的桶），供 StepArgument offload 测试。

### Community 58 - "ADR 0028: 瞬时网络/SSL 韧性"
Cohesion: 0.04
Nodes (53): act 有界返回（per-act timeout）, 被拒方案：asyncio 化消除 greenlet, DynamoDB 共享 events 表（events-out 传输）, 被拒方案：DynamoDB Streams（同步 run 语境）, 引擎经 --capabilities 自报 min_grace_s, 事件流结束信号（内容完整 + 进程终止都要）, EventSink（事件 sink 可注入接口）, exitCode 落值延迟的有界宽限轮询 (+45 more)

### Community 59 - "_is_transient_network"
Cohesion: 0.13
Nodes (30): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+22 more)

### Community 60 - "textui.py"
Cohesion: 0.10
Nodes (34): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 树的一个节点：`label` 是字符串或 Text，`add()` 返回子节点以便继续挂。 (+26 more)

### Community 61 - "Explain Command Tests"
Cohesion: 0.10
Nodes (31): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+23 more)

### Community 63 - "Fargate Engine Tests"
Cohesion: 0.10
Nodes (30): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。 (+22 more)

### Community 64 - "Plan Parsing Tests"
Cohesion: 0.12
Nodes (30): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否…, @scope 的值等于某条**自身已标 @scope** 的 scenario 的 id → 不报错：那条 id 根本没当分组键，不会撞。, 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ PlanError（ADR 0025：标了 tag…, test_assertion_votes_default_is_one() (+22 more)

### Community 65 - "test_lambda_handlers.py"
Cohesion: 0.08
Nodes (24): cloud_env(), Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。 (+16 more)

### Community 66 - "_FakeEcsClient"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 67 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 68 - "Artifact Uploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 69 - "Nova Main Fakes"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。 (+10 more)

### Community 70 - "test_compose.py"
Cohesion: 0.05
Nodes (61): build_engines(), check_version_skew(), 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, resolve_network(), resolve_region() (+53 more)

### Community 71 - "image_tag"
Cohesion: 0.17
Nodes (14): image_tag(), worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, parametrize, `gherkai_runtime.names` 的 worker 镜像交付命名（ADR 0038「tag 命名」条：单一真源、同时是单一校验点）。…, variant 本身合法但拼出来超 128 字符 → 报 tag 那一层（两类错误分开报，见 names 里两个正则的注释）。, 版本串首字符非法（归一化只管 `+`/`!`）→ tag 层拒，不静默产出 docker 不认的 ref。, `names` 的读端常量与 `DynamoDBRunStore` 的写端字面量必须逐字一致（ADR 0038 清理 pass 的运行中 run…, test_image_tag_normalizes_epoch() (+6 more)

### Community 72 - "_release_cmp"
Cohesion: 0.15
Nodes (13): is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp(), _release_key(), _variant_miss_hint() (+5 more)

### Community 73 - "ADR 0043 驱动 gherkai 的 agent skill"
Cohesion: 0.10
Nodes (30): gherkai agent skill 包, SKILL.md（随 CLI wheel 发行的 agent skill）, ADR 0004：Nova Act 经 Workflow 的 IAM 鉴权, ADR 0036：确定性能力自述与发现, ADR 0037：发行与打包, ADR 0039：使用者面零内部指代, ADR 0043 驱动 gherkai 的 agent skill, skill 评测资产（决策七） (+22 more)

### Community 74 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (25): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path (+17 more)

### Community 75 - "Project Conventions Glossary"
Cohesion: 0.10
Nodes (26): 项目约定 CLAUDE.md, /code-health-review 入口, /doc-health-review 入口, doc-diagram 项目级 skill, 领域术语表 CONTEXT.md, 基础镜像 / variant / 默认指针, 执行核心库窄腰, 核心注入接口 (core ports) (+18 more)

### Community 76 - "Midscene Resolve Hooks"
Cohesion: 0.10
Nodes (14): ADR-0015, fromSource, hookSpec, ADR-0028, ADR-0037, ADR-0022, ADR-0036, ADR-0020 (+6 more)

### Community 77 - "test_detached_launcher.py"
Cohesion: 0.06
Nodes (62): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, build_local_reconcile(), cleanup_tunnel() (+54 more)

### Community 78 - "FargateEngine"
Cohesion: 0.13
Nodes (16): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+8 more)

### Community 79 - "RunState"
Cohesion: 0.03
Nodes (73): 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_explain_cloud_reads_evidence_from_s3(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), DynamoDBRunStore, _job_state_to_item() (+65 more)

### Community 80 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 81 - "JobSource"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 82 - "redact_url_userinfo"
Cohesion: 0.13
Nodes (18): explain_to_dict(), 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, Any, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_url_userinfo() (+10 more)

### Community 83 - "test_adr_hygiene.py"
Cohesion: 0.19
Nodes (18): _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。, Status 头里点名的取代方编号（只看 superseded-by 之后、到第一个注解分隔符为止那一段）。, 被取代方点了谁，谁就得回指它——机械差集，不靠读。 (+10 more)

### Community 84 - "require_boto3"
Cohesion: 0.17
Nodes (6): 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…

### Community 85 - "reconciler.py"
Cohesion: 0.08
Nodes (34): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+26 more)

### Community 86 - "test_cloud_reconcile.py"
Cohesion: 0.08
Nodes (37): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, _FakeStartEngine, _job() (+29 more)

### Community 87 - "test_tunnel_host.py"
Cohesion: 0.12
Nodes (24): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _job(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。 (+16 more)

### Community 88 - "_cmd_doctor"
Cohesion: 0.08
Nodes (29): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+21 more)

### Community 89 - "Skill Install Command"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 90 - "test_cli_json_contract.py"
Cohesion: 0.13
Nodes (22): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…, _assert_documented(), _documented_keys(), _leaf_keys(), _mk() (+14 more)

### Community 91 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 92 - "ECS Timeout Handling Tests"
Cohesion: 0.10
Nodes (16): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的…, 仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…, task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录… (+8 more)

### Community 93 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 94 - "gherkai_deploy_aws/names.py"
Cohesion: 0.13
Nodes (14): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 生效 VPC 取值的 SSM 路径（ADR 0037 决策 6「VPC 取值持久化比对，三态齐全」）。 值形态三种：`default` / `new:<所建… (+6 more)

### Community 95 - "test_tunnel.py"
Cohesion: 0.19
Nodes (15): NgrokTunnel, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, stop_tunnel(), _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen… (+7 more)

### Community 96 - "SqliteEventLog"
Cohesion: 0.09
Nodes (25): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+17 more)

### Community 97 - "scan_family"
Cohesion: 0.11
Nodes (12): _parse_ts(), family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, family 的全部 ACTIVE revision（带 tags）。 两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-…, tag 里的 ISO 串 / boto3 回来的 datetime → aware UTC datetime；空或读不懂 → None。, RevisionInfo, scan_family(), datetime (+4 more)

### Community 98 - "_stream_record"
Cohesion: 0.12
Nodes (17): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events…, _stream_record() (+9 more)

### Community 99 - "test_container.py"
Cohesion: 0.18
Nodes (12): _Fake, _inspect_spec(), 容器引擎口子测试（ADR 0038「容器引擎口子」）。 **两层证据，分清边界**： - 大部分用一个**假 docker**（记 argv/stdin 的…, 「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。, **密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。, 假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。, test_inspect_missing_image_is_not_an_error(), test_inspect_other_failure_raises() (+4 more)

### Community 100 - "resolve_container_engine"
Cohesion: 0.18
Nodes (14): 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, resolve_container_engine(), ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。…, arm 变体真镜像 → 架构判据拒（即 push-worker 以退出码 2 结束那一支）。 用 alpine（小）代替真 worker 镜像：判据只看…, `docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取…, `--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。, test_default_is_docker(), test_env_selects_engine_and_flag_wins() (+6 more)

### Community 101 - "_gap_engine"
Cohesion: 0.14
Nodes (15): _delayed_stopped_ecs(), _ev_item(), _gap_engine(), 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未… (+7 more)

### Community 102 - "cleanup_pass"
Cohesion: 0.15
Nodes (13): cleanup_pass(), CleanupOutcome, _hours(), _iter_image_params(), _mapped_arn(), _non_terminal_statuses(), 枚举 `worker-image/*` 全部参数（**含所有版本、所有引擎**）→ `(engine, tag, value)`。…, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看… (+5 more)

### Community 103 - "_Recorder"
Cohesion: 0.17
Nodes (10): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+2 more)

### Community 105 - "AWS & Playwright Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 106 - "_argv"
Cohesion: 0.18
Nodes (11): _argv(), _parse_destroy(), Path, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，…, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_destroy_yes_passes_force_to_cdk_and_is_off_by_default() (+3 more)

### Community 107 - "Gherkin Feature Parsing"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 108 - "Feature Planning Core"
Cohesion: 0.19
Nodes (17): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只执行 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次运行哪几条。… (+9 more)

### Community 109 - "Path"
Cohesion: 0.18
Nodes (11): FeatureSource, load_feature(), local_artifact_locations(), prune_empty_dirs(), Path, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 本机后端一个 run 的产物落点（全 file:// URI）：run_meta / run_state / jobs_dir /… (+3 more)

### Community 110 - "Event Sink & Job Source"
Cohesion: 0.14
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0032, resolveEventsFd(), Job, JobSource

### Community 111 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 112 - "_FakeProc"
Cohesion: 0.22
Nodes (6): 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, TunnelInfo, _FakeProc, test_mapped_base_embeds_credentials(), test_mapped_base_without_auth_is_plain_url()

### Community 113 - "Deterministic Step Registry"
Cohesion: 0.13
Nodes (12): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, Match, matchBatch() (+4 more)

### Community 114 - "Evidence Collector Tests"
Cohesion: 0.15
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, importRunScope(), spyUploader() (+4 more)

### Community 115 - "_render_status"
Cohesion: 0.18
Nodes (18): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。 (+10 more)

### Community 116 - "container.py"
Cohesion: 0.29
Nodes (6): ContainerError, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, UnsupportedContainerEngine

### Community 117 - "ImageInfo"
Cohesion: 0.29
Nodes (5): ImageInfo, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。, test_target_platform_judgement()

### Community 118 - "arg_offload.py"
Cohesion: 0.40
Nodes (5): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…

### Community 119 - "ECS Exit Code Extraction"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 120 - "ValueError"
Cohesion: 0.36
Nodes (8): test_value_error_not_transient(), main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems(), ValueError

### Community 121 - "Event Wall-Clock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 122 - ".inspect"
Cohesion: 0.33
Nodes (4): 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。, _tail()

### Community 123 - "_tagged_feature"
Cohesion: 0.17
Nodes (13): _plan_names(), 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature(), test_empty_selection_flag_values_are_rejected() (+5 more)

### Community 124 - "Release Notes Tests"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 125 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 126 - "test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine"
Cohesion: 0.15
Nodes (8): CountingEcs, boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。, ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。, 重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…, 模板没变（deploy 重新运行的常态）→ 一次模板 describe 都不打：判定只用映射里记的模板 ARN。, Spy, test_rederive_does_not_read_the_template_when_nothing_is_stale(), test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine()

### Community 127 - "Run Scope Tests"
Cohesion: 0.13
Nodes (6): ADR-0014, ADR-0031, _events, fakePage, importMod(), testSink

### Community 128 - "Distribution Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 129 - "_build_parser"
Cohesion: 0.15
Nodes (14): ArgumentParser, _add_selection_flags(), _build_parser(), _cmd_skill_install(), _dist_version(), _installed_version(), run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。, 建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何… (+6 more)

### Community 130 - "Package README Guardrails"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 131 - "_read_events"
Cohesion: 0.13
Nodes (14): _join_pumps(), _pump_log(), Event, Job, Popen, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+6 more)

### Community 132 - "Scope Tag Grouping"
Cohesion: 0.26
Nodes (13): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。 (+5 more)

### Community 133 - "_out"
Cohesion: 0.11
Nodes (24): list_workers(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…, _out(), 收集打印文本的 out 替身 → (调用函数, 取全文函数)。, dev 版（`.dev`/`.post`/本地段）**GHCR 上不存在对应基础镜像** → 明确警告 + 跳过基础镜像同步，第 3/4 步照常执行。…, cdk 已成功、机器上没有容器引擎 → 退出码 1 + 「stack 已生效、重新运行幂等收敛」（不是退出码 2：账户已被改过）。 (+16 more)

### Community 134 - "ArtifactUploader（产物落点可注入组件）"
Cohesion: 0.15
Nodes (18): ReportRef {kind, ref, label}, ResourceUri（带 scheme 的统一指针）, Act-Boundary Pre-Send (Level 3), ArtifactUploader（产物落点可注入组件）, 上传成功后删本地（两条护栏）, S3 Landing Env Injection (ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX), uploader.flush_and_cleanup(dir), uploader.from_env() (+10 more)

### Community 135 - "Midscene Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 136 - "Artifact Upload & Error Text"
Cohesion: 0.19
Nodes (9): CONTENT_TYPES, UPLOAD_TIMEOUT_MS, mkLogDir(), mkShots(), tmproot(), errorText(), oneLineError(), ADR-0042 (+1 more)

### Community 137 - "tunnel.py"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 138 - "events_pk"
Cohesion: 0.18
Nodes (9): 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。, _put_worker_event(), DDB 侧 reason 属性 omit-when-empty、records() 读回进 TaskExited.reason（观察者落哨兵时的用户可见归因）。, 模拟 worker PutItem 一条执行事件（含 expires_at=emit_ts+7d，DdbEventLog 据此还原 emit_ts）。, test_ddb_record_exit_reason_roundtrip() (+1 more)

### Community 139 - ".run_scope"
Cohesion: 0.40
Nodes (3): Event, Job, 起一个 worker 运行这个 job，返回 (句柄, ADR 0024 事件流迭代器)。 事件流逐条产出（ADR 0024 流式）；迭代结束表示…

### Community 140 - "report_store/local.py"
Cohesion: 0.12
Nodes (18): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+10 more)

### Community 141 - "_run_with_refs"
Cohesion: 0.21
Nodes (15): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3() (+7 more)

### Community 142 - "Architecture Diagrams"
Cohesion: 0.22
Nodes (13): Archify Diagram Accessibility & Preset Contract, Artifacts Evidence Chain Diagram, Cloud Backend Carriers Revision Pinning Diagram, Cloud Backend Upgrade Windows Diagram, Cloud Delivery Identity Diagram, Configuration Environment Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram (+5 more)

### Community 143 - "gherkai agent SKILL.md"
Cohesion: 0.27
Nodes (11): skill reference: 云端后端与 variant 镜像, worker variant 与 push-worker, skill reference: 确定性 step 写法, skill reference: 引擎选择与证据填充差异, skill reference: 环境就位与排障, --expose-local 隧道前置与排障, gherkai agent SKILL.md, 一步三种执行路径与派发优先级 (+3 more)

### Community 144 - "digest_for_repo"
Cohesion: 0.40
Nodes (5): digest_for_repo(), 从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。…, 基础镜像同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def**…, test_digest_none_when_repo_absent_or_empty(), test_digest_picked_by_repo_not_first_entry()

### Community 145 - "Skill Deploy Token Tests"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。 (+3 more)

### Community 146 - "Lambda IAM Permission Tests"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 147 - "aws"
Cohesion: 0.40
Nodes (5): aws(), _aws_env(), _presentation_is_environment_independent(), 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, fixture

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

### Community 152 - "gherkai_runtime/__init__.py"
Cohesion: 0.29
Nodes (6): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup

### Community 153 - "test_read_events_ignores_exit_item_on_stopped_drain_path"
Cohesion: 0.50
Nodes (4): _put_exit_item(), 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, worker 零事件退出 + exit item 已落：STOPPED 兜底路径（含 _final_drain 强一致终读）同样只读 worker 段。…, test_read_events_ignores_exit_item_on_stopped_drain_path()

### Community 154 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 155 - "Fake Event Sink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 156 - "_StopTimeoutEcs"
Cohesion: 0.17
Nodes (13): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), ecr_repo_name(), 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…, task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, 引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag…, task_def_name() (+5 more)

### Community 157 - "ECS Task Timing Script"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 159 - "._pump"
Cohesion: 0.50
Nodes (3): Event, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, Timer

### Community 160 - "Tunnel Origin Mapping"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 161 - "E2E Test Harness"
Cohesion: 0.36
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 162 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 163 - "compose.build_cloud_stores"
Cohesion: 0.60
Nodes (6): compose.build_cloud_stores, DynamoDBRunStore, S3ReportStore, S3ResultStore, S3StepArgumentOffloader, Decision 6: cloud adapter persistence form (DDB/S3)

### Community 164 - "Cloud Status Command Tests"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 165 - "_seed_run"
Cohesion: 0.09
Nodes (24): 建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…, `_build` 的三层 store 全用它自己已建的那批句柄装配——compose 里建句柄的两个钩子在此一次都不该执行。 这条同时是「region…, definition 声明 ≤ cap → 按 definition 走（打通前云端后端静默忽略提交侧声明，是可用性缺陷）。, definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。, meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。, cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…, 推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。 (+16 more)

### Community 166 - "build_fargate_engines 组合根接线"
Cohesion: 0.24
Nodes (10): build_fargate_engines 组合根接线, container 名契约 {engine}-worker, gherkai_runtime.names 命名单一真源, preflight fail-fast 点名 prefix, 产物前缀一致性语义探针, report ⊥ 执行（--no-report 不改执行环境）, subnet/sg ID 走含 prefix 的 SSM 路径, task-def 不焊 region/凭证 (+2 more)

### Community 167 - "reconcile.tick（无状态编排步骤）"
Cohesion: 0.28
Nodes (9): 收尾写序与提交点（try_finalize）, detached 标记与两道拦截, 同一条事件流的四条物理通道, exit-observer Lambda（退出观察者）, kicker Lambda（冷启动器）, local per-run 推进进程（setsid 脱离 CLI）, reconcile.tick（无状态编排步骤）, reconciler Lambda（主推进器） (+1 more)

### Community 168 - "Doc Rules Check"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 171 - "Finished Run Idempotence"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 172 - "URL Redaction"
Cohesion: 0.29
Nodes (4): RFC-3986, MASK, ADR-0035, CASES

### Community 173 - "Report Store Artifacts"
Cohesion: 0.29
Nodes (7): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, JobResult 持有 Job、engine 经 property delegate, manifest.json（薄信封 + 扁平 report_index）, 被拒方案：materialize 产物拷贝, ReportStore.write（整 run 一次写）, run_id（归集索引主键，组合根生成）

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
- **46 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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