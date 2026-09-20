# Graph Report - yaozhou  (2026-09-20)

## Corpus Check
- 325 files · ~532,056 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5059 nodes · 11643 edges · 223 communities (183 shown, 40 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 729 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d005a57b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Job
- CLI Entry Wiring Tests
- Cloud Backend CLI Tests
- test_stores.py
- AWS Worker Image Management
- test_project.py
- Worker Image Tests
- evidence.py
- Container Engine Adapter
- Deploy Provider Interface
- _FakeEcs
- Status
- test_compose.py
- compose.py
- Skill Doc Flag Guardrails
- CDK Stack Synth Tests
- Deploy Command Frontend
- test_reconcile.py
- Nova Act Benchmarks & Setup
- query_capabilities
- CLI Plan Command Behavior
- test_worker_variant.py
- _Nova
- test_schedule.py
- Conditional Write Contract Tests
- Submit & Tunnel CLI Wiring
- Deploy CLI Doctor Checks
- test_interrupt_model.py
- User Guide Configuration Docs
- _run_step
- StepDone
- run_scope.py
- Skill Materialization Checks
- _engine
- Provider Deploy Subverbs
- test_cloud_reconcile.py
- test_lambda_handlers.py
- Engine Spike Scripts
- TypeScript Worker Run Scope
- Architecture Overview Diagrams
- User Docs Guardrails
- BackendStack
- LocalReportStore
- RunPersistence
- _build_parser
- test_explain_cloud_reads_evidence_from_s3
- test_lifecycle_states.py
- wire.py
- SqliteEventLog
- Deterministic Step Resolution (TS)
- Evidence Schema (TS)
- Artifact Upload Tests
- Doc Scanning Rules
- WorkerSelfDescribeError
- Plan Parsing Tests
- render.py
- gherkai_runtime/names.py
- TS Artifact & Event Sink
- Python Artifact Uploader
- _RecUploader
- Lambda Asset Build
- Version Skew Checking
- Explain Command Tests
- FargateEngine
- Architecture ADRs (Core)
- _is_transient_network
- gherkai_cli/__main__.py
- Doctor Self-Check Tests
- test_user_steps.py
- resolve_worker_cmd
- S3ResultStore
- reconciler.py
- _FakeEcsClient
- report_store/local.py
- TypeScript Build Config
- test_event_sink.py
- Atomic File Writes
- test_s3_report_store.py
- build_local_reconcile
- ADR Hygiene Checks
- _MissingThenStoppedEcs
- Tunnel & Capability ADRs
- Docs & Terminology ADRs
- tunnel.py
- Tunnel Host TTL Watch
- Contributor Guardrail Docs
- _render_status
- Agent Skill Install
- JSON Field Contract Tests
- JobSource
- Step Argument Assembly
- Detached Launcher Tests
- Reconciler Stream Tests
- deterministic.py
- Safe-Point Trajectory Upload
- Subprocess Engine Adapter
- Subprocess Engine Tests
- TS Artifact Uploader
- NPM Dependencies
- .offload
- Feature File Parsing
- Plan Job Generation
- Diagram Build Script
- AWS Architecture ADRs
- Evidence Collector Tests
- Nova SDK Test Doubles
- Changelog & Skill Docs
- Task Definition Revisions
- ECS Task Exit Extraction
- _StampSsm
- Event Wallclock Analysis
- cli/DEVELOPMENT.md
- Scenario Selection Flags
- Run Scope Tests
- Distribution Metadata Checks
- Explain Command
- Package README Guardrails
- _SeqEcs
- Scope Tag Resolution
- CDK Destroy/Bootstrap CLI
- CDK Invocation Tests
- Architecture Diagram Exports
- Worker Package Manifest
- build_cloud_stores
- ArgumentParser
- Provider CLI Flags
- Artifact Upload & Shutdown
- Release Notes Automation
- test_sqlite_event_log.py
- Subprocess Engine Launcher
- test_fargate_engine.py
- Exit Observer Lambda
- Skill Deploy Token Checks
- Advancer IAM Permissions
- test_error_step_also_enqueues_only_after_emit
- _FakeEcs
- test_tunnel.py
- Skill Contract Rendering
- User-Facing Text Guardrails
- CDK Context Cache
- AWS Client Stubs
- Artifact Upload Tests (TS)
- _FakeCdp
- Release Notes Tests
- Worker Signal Interrupt Tests
- Fake Event Sink
- EventBridgeTimeoutWatch
- ECS Task Timing Capture
- AWS Deploy Package Docs
- Schedule & Retry ADRs
- Detached Run Orchestration
- Report Aggregation & Status
- Worker Bin & Step Loading
- _StopTimeoutEcs
- Tunnel Host Orchestration
- Origin URL Mapping
- End-to-End Test Harness
- Graphify Refresh Script
- Cloud Status Command
- CDK App & Backend Stack
- Worker Revision Resolution
- test_evidence.py
- detached.py
- Doc Rules Checker
- Fake DynamoDB Table
- ValueError
- Finished Run Idempotency
- Context Glossary Checks
- Core Package Docs
- Report Store & Manifest
- DynamoDB Storage Design
- _delayed_stopped_ecs
- Verdict Evidence Glossary
- _fixture
- Fake S3 Client
- Echo Test Worker
- Cloud Test Infrastructure
- Counting ECS Spy
- _cmd_tunnel_watch
- Plan Module Seams
- Run Persistence & Preflight
- TypeScript Dev Dependencies
- Job Sink Primitives
- Worker Subnet Selection
- Image Parameter Mapping
- Package Files Metadata
- Repository Metadata
- test_artifact_lines_report_write_failure_falls_back_to_a_note
- Worker Artifact Upload
- Upload Call Recorder
- Command Span Parsing
- Timeout Scan Isolation
- Missing Container Engine Stub
- NPM Scripts
- AgentCore CDP Script
- Background Upload Queue
- Run Summarization Script
- Pre-commit Hook
- Bedrock AgentCore SDK
- DynamoDB SDK Client
- Adapter Implementations Layer
- Local File Backend Preflight
- ref_to_dict
- Provider Module Import Isolation
- AWS Client Error Messaging
- OpenAI Dependency
- tsx Dependency
- Bounded Queue Drain
- Log Upload Enablement
- Fail-Loud Config Validation
- Local No-Op Uploader
- Gherkai Workspace Root
- Derived Files Sync Hook
- Wording Guard Hook
- Architecture Layers Diagram
- Run Lifecycle Diagram
- Artifacts Evidence Chain Diagram
- Cloud Backend Upgrade Diagram
- Gherkai Core Package
- AWS Deployment Package
- Gherkai Runtime Package
- NovaAct Worker Package

## God Nodes (most connected - your core abstractions)
1. `main()` - 215 edges
2. `Job` - 134 edges
3. `RunState` - 127 edges
4. `RunMeta` - 118 edges
5. `Status` - 106 edges
6. `JobState` - 101 edges
7. `Provider` - 95 edges
8. `JobResult` - 83 edges
9. `Scenario` - 73 edges
10. `Step` - 72 edges

## Surprising Connections (you probably didn't know these)
- `docs/code-health-review.md（命令入口所指）` --semantically_similar_to--> `代码健康度复盘任务说明`  [AMBIGUOUS] [semantically similar]
  .claude/commands/code-health-review.md → docs/ai-eng/code-health-review.md
- `docs/doc-health-review.md（命令入口所指）` --semantically_similar_to--> `文档健康度复盘任务说明`  [AMBIGUOUS] [semantically similar]
  .claude/commands/doc-health-review.md → docs/ai-eng/doc-health-review.md
- `RunPersistence` --references--> `判定真值 (verdict truth)`  [EXTRACTED]
  core/gherkai_core/persist.py → CONTEXT.md
- `tick()` --implements--> `无状态批量运行 (stateless batch execution)`  [EXTRACTED]
  core/gherkai_core/reconcile.py → CONTEXT.md
- `skill 副本：--json 字段契约` --semantically_similar_to--> `CLI JSON 契约页（手写源）`  [EXTRACTED] [semantically similar]
  cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md → docs/internals/cli-json-contract.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **--expose-local 隧道暴露本机应用的完整流程** — docs_user_guide_local_app_testing, docs_user_guide_local_app_testing_tunnel_ttl, docs_user_guide_local_app_testing_security, runtime_development_tunnel, docs_user_guide_writing_features_sensitive_info [EXTRACTED 0.80]
- **文档与代码健康度复盘的姊妹任务体系** — docs_ai_eng_doc_health_review, docs_ai_eng_code_health_review, docs_ai_eng_readme, docs_adr_0045_documentation_layering_and_placement, context, claude [EXTRACTED 0.80]
- **面向 AI agent 的操作面：筛选与静默、doctor、机读契约、evidence/explain、skill** — docs_adr_0041_scenario_selection, docs_adr_0041_doctor, docs_adr_0041_json_contract, docs_adr_0042_evidence_schema, docs_adr_0042_explain_command, docs_adr_0043_skill_in_cli_package [EXTRACTED 0.85]
- **AI 断言哲学链：默认 AI + 投票治抖动 + 确定性 step 按需兜底** — docs_adr_0014_ai_first_assertions, docs_adr_0015_v1_positioning_smoke_not_regression, docs_adr_0018_generic_steps_capability, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold, docs_adr_0014_vote_flakiness_governance [EXTRACTED 0.85]
- **Archify Classic/Showcase SVG Export Preset** — docs_diagrams_cloud_delivery_identity, docs_diagrams_configuration_env_inheritance, docs_diagrams_deterministic_steps_registry_overview, docs_diagrams_deterministic_steps_truth_sources, docs_diagrams_execution_cloud_cascade, docs_diagrams_execution_detached_gates, docs_diagrams_execution_timeout_chain, docs_diagrams_getting_started_component_ownership, docs_diagrams_local_app_testing_tunnel_topology, docs_diagrams_readme_runtime_topology, docs_diagrams_run_execution, docs_diagrams_archify_diagram_style [EXTRACTED 0.85]
- **产物→S3 链：注入落点 → uploader 四级上传 → 不透明 ref 归集** — docs_adr_0029_engine_artifacts_to_s3_uploader, docs_adr_0029_engine_artifacts_to_s3_upload_timing, docs_adr_0027_runreport_aggregation_index_reportref, docs_adr_0032_fargate_execution_environment_adr, docs_adr_0033_iac_aws_backend_and_composition_wiring_build_fargate_engines [EXTRACTED 0.85]
- **双语言裂缝与跨引擎边界：两引擎都子进程、核心选 Python** — docs_adr_0013_cross_engine_sharing_boundary, docs_adr_0023_novaact_acting_python_locked_no_ts_core, docs_adr_0016_execution_architecture_core_lib_run_model, docs_adr_0024_io_edge_ports [EXTRACTED 0.85]
- **run/submit × local/cloud 四组合的推进机制** — docs_internals_execution_and_reconciliation_schedule, docs_internals_execution_and_reconciliation_reconcile_tick, docs_internals_execution_and_reconciliation_event_channels, docs_internals_execution_and_reconciliation_detached_gates, docs_internals_execution_and_reconciliation_commit_point [EXTRACTED 0.85]
- **Midscene 引擎模型选型与接线链（AWS 内约束下的演进）** — docs_adr_0002_midscene_not_driven_by_gpt55, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0008_midscene_bedrock_auth_sigv4_selfsign, docs_adr_0012_planning_shares_qwen3vl_no_text_planner, docs_adr_0009_maximize_aws_hard_constraint [EXTRACTED 0.85]
- **判定流水：四层归约 → 状态与归因 → severity → 退出码** — docs_internals_verdict_model_four_layer_reduction, docs_internals_verdict_model_status_set, docs_internals_verdict_model_job_outcome_priority, docs_internals_verdict_model_severity, docs_internals_verdict_model_exit_codes [EXTRACTED 0.85]
- **worker 自述面：capabilities / steps 目录 / 清单查询 / plan 标注** — docs_adr_0036_capabilities_entry, docs_adr_0036_registry_metadata, docs_adr_0036_list_deterministic, docs_adr_0036_plan_annotation, docs_adr_0037_steps_dir_convention [EXTRACTED 0.85]
- **随命令行发行的 agent skill 及其 reference 集** — cli_gherkai_cli_skills_gherkai_skill, cli_gherkai_cli_skills_gherkai_references_cli_json_contract, cli_gherkai_cli_skills_gherkai_references_cloud_backend, cli_gherkai_cli_skills_gherkai_references_engines, cli_gherkai_cli_skills_gherkai_references_setup_and_diagnosis, cli_gherkai_cli_skill_install, context_agent_skill [EXTRACTED 0.90]
- **B1 转向：核心自解析 Gherkin + 薄 worker + cucumber 补丁退役** — docs_adr_0022_bdd_runner_retired_core_parses_thin_worker, docs_adr_0021_local_cucumber_patch_step_keyword_disambiguation, docs_adr_0016_execution_architecture_core_lib_run_model, docs_adr_0024_worker_core_protocol, docs_adr_0022_deterministic_registry [EXTRACTED 0.90]
- **v1.0 核心三模块流水线：plan → schedule → 归集报告** — docs_adr_0025_plan_module_feature_to_jobs_plan, docs_adr_0026_schedule_module_schedule, docs_adr_0027_runreport_aggregation_index_reportstore, docs_adr_0030_realtime_persistence_seam_runpersistence [EXTRACTED 0.90]
- **无状态批量运行的四机制协同（独立键空间/条件写/CAS/超时）** — docs_adr_0034_detached_batch_reconciler_task_exited, docs_adr_0034_detached_batch_reconciler_hwm, docs_adr_0034_detached_batch_reconciler_cas, docs_adr_0034_detached_batch_reconciler_job_timeout, docs_adr_0034_detached_batch_reconciler_project [EXTRACTED 0.90]
- **确定性 step 在两个引擎上对称注册与加载** — docs_user_guide_writing_deterministic_steps, docs_user_guide_writing_deterministic_steps_registration, docs_user_guide_writing_deterministic_steps_steps_dir, engines_novaact_development_user_steps, engines_midscene_development_user_steps [EXTRACTED 0.90]
- **docs/internals 七篇构成机制层的主题归属表** — docs_internals_readme, docs_internals_architecture_overview, docs_internals_execution_and_reconciliation, docs_internals_verdict_model, docs_internals_artifacts_and_evidence, docs_internals_deterministic_step_lifecycle, docs_internals_cloud_backend_carriers, docs_internals_cli_json_contract [EXTRACTED 0.90]
- **一个 tag 驱动的发布链（gate → PyPI → npm → GHCR → Release）** — github_workflows_release, github_scripts_check_dist_metadata, github_scripts_wait_for_index, github_scripts_release_notes, changelog, github_release_body_footer, context_single_version_source [EXTRACTED 0.90]
- **worker 镜像交付链：基础镜像 → variant → revision → 默认指针 → 清理** — docs_adr_0038_base_image, docs_adr_0038_variant, docs_adr_0038_push_worker, docs_adr_0038_task_def_revision, docs_adr_0038_default_pointer, docs_adr_0038_cleanup_pass [EXTRACTED 0.90]
- **Execution Flow Diagram Set** — docs_diagrams_run_execution, docs_diagrams_execution_timeout_chain, docs_diagrams_execution_detached_gates, docs_diagrams_execution_cloud_cascade [INFERRED 0.70]
- **环境变量从 shell 经组合根注入到本机与云端 worker** — docs_user_guide_configuration, docs_user_guide_configuration_injected_env, runtime_development_compose, engines_novaact_development, engines_midscene_development [INFERRED 0.80]

## Communities (223 total, 40 thin omitted)

### Community 0 - "Job"
Cohesion: 0.04
Nodes (128): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _explain_job(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact() (+120 more)

### Community 1 - "CLI Entry Wiring Tests"
Cohesion: 0.04
Nodes (102): _capturing_schedule(), _cloud_backend_ok(), _doctor_cloud_json(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json… (+94 more)

### Community 2 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 3 - "test_stores.py"
Cohesion: 0.04
Nodes (92): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, Path, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 (+84 more)

### Community 4 - "AWS Worker Image Management"
Cohesion: 0.04
Nodes (97): Aws, _cell(), cleanup_pass(), CleanupOutcome, _connect(), current_version_mappings(), _describe_revision(), _ecr_login() (+89 more)

### Community 5 - "test_project.py"
Cohesion: 0.06
Nodes (85): 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, ScopeStarted, Action, EventRecord, NonTerminalSnapshot, plan_next() (+77 more)

### Community 6 - "Worker Image Tests"
Cohesion: 0.06
Nodes (89): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地… (+81 more)

### Community 7 - "evidence.py"
Cohesion: 0.08
Nodes (39): Any, act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Path (+31 more)

### Community 8 - "Container Engine Adapter"
Cohesion: 0.04
Nodes (56): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+48 more)

### Community 9 - "Deploy Provider Interface"
Cohesion: 0.06
Nodes (74): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 留的口子（ADR 0038「命令族」）：**尚未提供**，以退出码 2 结束并说清为什么与将来怎么落。…, _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, flag 面全集锁定（枚举型护栏）：三个 context 配置项 flag + AWS 定位二件套 + 两个「前端的中立版的 AWS 精确化」（见 cli…, `--allow-vpc-change` / `--require-approval` **只贴 deploy**（枚举型全集比对，同上条口径）。… (+66 more)

### Community 10 - "_FakeEcs"
Cohesion: 0.08
Nodes (22): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的…, n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。, 仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。 ECS… (+14 more)

### Community 11 - "Status"
Cohesion: 0.04
Nodes (84): render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…, skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；…, step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。, job 行有分类、message 为 None → 只显分类 `(worker_crashed)`，不打 `(worker_crashed:…, test_index_html_shortcircuit_note_matches_cli_wording(), test_job_line_with_error_type_but_no_message_has_no_orphan_colon(), test_render_text_annotates_shortcircuited_step() (+76 more)

### Community 12 - "test_compose.py"
Cohesion: 0.05
Nodes (64): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`… (+56 more)

### Community 13 - "compose.py"
Cohesion: 0.05
Nodes (58): subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), ssm_worker_template_path() (+50 more)

### Community 14 - "Skill Doc Flag Guardrails"
Cohesion: 0.05
Nodes (61): bare_flags(), clean_flag(), extract_command_spans(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。 (+53 more)

### Community 15 - "CDK Stack Synth Tests"
Cohesion: 0.06
Nodes (60): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。 (+52 more)

### Community 16 - "Deploy Command Frontend"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 17 - "test_reconcile.py"
Cohesion: 0.07
Nodes (45): 无状态批量运行 (stateless batch execution), EventLog, finalize_report(), Launcher, Job, Protocol, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 本机后端下起 subprocess worker（事件旁路落 SQLite EventLog… (+37 more)

### Community 18 - "Nova Act Benchmarks & Setup"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 19 - "query_capabilities"
Cohesion: 0.08
Nodes (33): engine_min_grace(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc(), 一份合契约的自述对象（五个键，ADR 0036「5.」）；模型 id 不给就按引擎取该引擎真实会自报的那个。, 整份自述对象原样返回（五个键：schema_version / engine / min_grace_s / deterministic_steps /… (+25 more)

### Community 20 - "CLI Plan Command Behavior"
Cohesion: 0.06
Nodes (50): main(), _det_feature(), 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。, 冲突预检（实际运行将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。 (+42 more)

### Community 21 - "test_worker_variant.py"
Cohesion: 0.08
Nodes (44): _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。, 默认指针不存在（部署没走过 worker 镜像初始化）→ 提示运行 `gherkai deploy`，不猜 `base`。, SSM 无该（引擎，variant）映射 + CLI 与后端同版本 → 引导 push-worker，**不回落默认 variant**。 (+36 more)

### Community 22 - "_Nova"
Cohesion: 0.17
Nodes (23): ArtifactUploader, _get_uploader(), _done(), _Nova, parametrize, Path, fake nova：act/act_get 回带 trajectory 路径的结果；act_raises 时抛（模拟 act 中途失败）。, evidence.json 的即时上传失败也只丢 ref（to_report_ref 的「失败即抛」契约不动，兜法在调用方）。 只让… (+15 more)

### Community 23 - "test_schedule.py"
Cohesion: 0.21
Nodes (51): 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+43 more)

### Community 24 - "Conditional Write Contract Tests"
Cohesion: 0.07
Nodes (50): _initial(), _meta(), RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+42 more)

### Community 25 - "Submit & Tunnel CLI Wiring"
Cohesion: 0.07
Nodes (46): submit 把 --max-concurrency 落进 definition（推进器读 meta，不靠 flag 通道）。 fork 出的 per-run…, submit 侧同 run：解析一次写进 definition——per-run 进程/接力者从 definition 读回（**不**收 flag，…, test_submit_local_persists_steps_dir_into_definition(), test_submit_local_writes_max_concurrency_into_definition(), test_submit_rejects_max_concurrency_below_one(), _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel() (+38 more)

### Community 26 - "Deploy CLI Doctor Checks"
Cohesion: 0.05
Nodes (45): cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client() (+37 more)

### Community 27 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (33): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+25 more)

### Community 28 - "User Guide Configuration Docs"
Cohesion: 0.08
Nodes (48): 配置：环境变量与通用选项, 由 gherkai 注入的环境变量, 模型选择（默认模型与家族推断）, 常见问题, 开始使用, AWS 前置（凭证、region、服务开通）, 用 doctor 自检, 上手路径一：交给 AI agent（skill install） (+40 more)

### Community 29 - "_run_step"
Cohesion: 0.10
Nodes (43): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+35 more)

### Community 30 - "StepDone"
Cohesion: 0.12
Nodes (35): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+27 more)

### Community 31 - "run_scope.py"
Cohesion: 0.09
Nodes (28): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _capabilities(), _collect_traj(), _cost_from_result(), _drain_evidence_uploads() (+20 more)

### Community 32 - "Skill Materialization Checks"
Cohesion: 0.11
Nodes (42): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+34 more)

### Community 33 - "_engine"
Cohesion: 0.11
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 34 - "Provider Deploy Subverbs"
Cohesion: 0.07
Nodes (21): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), Path, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。… (+13 more)

### Community 35 - "test_cloud_reconcile.py"
Cohesion: 0.04
Nodes (64): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog (+56 more)

### Community 36 - "test_lambda_handlers.py"
Cohesion: 0.05
Nodes (41): cloud_env(), Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, Stream records + 直接 run_id 并存时都提取（健壮）。, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick… (+33 more)

### Community 37 - "Engine Spike Scripts"
Cohesion: 0.07
Nodes (28): ADR-0008, ADR-0010, BASE_URL, main(), makePng(), REGION, BASE_URL, main() (+20 more)

### Community 38 - "TypeScript Worker Run Scope"
Cohesion: 0.08
Nodes (37): ADR-0019, ADR-0026, ADR-0027, ADR-0035, ADR-0039, agentOpts(), aggregate(), appendReportRef() (+29 more)

### Community 39 - "Architecture Overview Diagrams"
Cohesion: 0.10
Nodes (38): 图：job 收场态判定（有序短路四问）, 图：判定四层归约（worker 侧汇总 / core 侧归约）, 图：scenario 到 job 的分组, 架构总览：五层结构、一次 run 的生命周期、包与发行物, 同一条链的两种载体（--backend local / cloud 只替换 adapter）, 五层职责划分（用例 / 产品 / 执行 / 浏览器 / 被测应用）, 一次 run 的生命周期主干（parse → scope 分组 → begin → 驱动 → 判定归约与报告）, 产物与证据：产物落在哪、哪一份回答哪个问题 (+30 more)

### Community 40 - "User Docs Guardrails"
Cohesion: 0.09
Nodes (36): changelog_unreleased(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, _default_model_claims(), _default_model_ids(), parametrize, Path, 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…, owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。 (+28 more)

### Community 41 - "BackendStack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 42 - "LocalReportStore"
Cohesion: 0.15
Nodes (44): _sample_run(), test_to_dict_shape_and_no_dollar(), LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, 单个 step 的归约结果（core 保留 step 级粒度，ADR 0024）。 duration_ms 是 step 墙钟时长（core 用…, ReportRef, ScenarioResult (+36 more)

### Community 43 - "RunPersistence"
Cohesion: 0.17
Nodes (21): Event, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run 就是 commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, 事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收…, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的…, RunPersistence, _jr(), _meta() (+13 more)

### Community 44 - "_build_parser"
Cohesion: 0.08
Nodes (26): ArgumentParser, _add_selection_flags(), _build_parser(), _cmd_doctor(), _cmd_list_engines(), _cmd_skill_install(), _dist_version(), _doctor_cloud() (+18 more)

### Community 45 - "test_explain_cloud_reads_evidence_from_s3"
Cohesion: 0.50
Nodes (4): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3()

### Community 46 - "test_lifecycle_states.py"
Cohesion: 0.08
Nodes (21): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), FakeWorkerHandle, Event (+13 more)

### Community 47 - "wire.py"
Cohesion: 0.08
Nodes (42): scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, StepSkipped, _argument_to_json(), event_from_json(), event_from_line(), job_to_json(), job_to_line(), Event (+34 more)

### Community 48 - "SqliteEventLog"
Cohesion: 0.17
Nodes (9): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+1 more)

### Community 49 - "Deterministic Step Resolution (TS)"
Cohesion: 0.07
Nodes (19): ADR-0015, ADR-0037, ADR-0022, ADR-0036, DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler (+11 more)

### Community 50 - "Evidence Schema (TS)"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+21 more)

### Community 51 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 52 - "Doc Scanning Rules"
Cohesion: 0.12
Nodes (30): ai_side_docs(), classify(), code_comment_files(), comment_units(), diagram_sources(), long_term_docs(), Path, 人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。 内容三类：①规则——内部指代表 FORBIDDEN、口吻表… (+22 more)

### Community 53 - "WorkerSelfDescribeError"
Cohesion: 0.09
Nodes (22): _ask_worker(), build_local_stores(), local_artifact_locations(), match_deterministic(), prune_empty_dirs(), Path, RuntimeError, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。… (+14 more)

### Community 54 - "Plan Parsing Tests"
Cohesion: 0.12
Nodes (30): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, 未标 scope 的 scenario 拿自己的 id 当 scope_id；@scope 标成同一个字符串，两组就派生出同一个 scope_id。…, named 在前、未标在后同样报错——判定不依赖遍历顺序。 曾用一张 key→bool 边表记「是否…, @scope 的值等于某条**自身已标 @scope** 的 scenario 的 id → 不报错：那条 id 根本没当分组键，不会撞。, 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ PlanError（ADR 0025：标了 tag…, test_assertion_votes_default_is_one() (+22 more)

### Community 55 - "render.py"
Cohesion: 0.09
Nodes (32): _act_lines(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), _ms(), _one_line() (+24 more)

### Community 56 - "gherkai_runtime/names.py"
Cohesion: 0.08
Nodes (28): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight… (+20 more)

### Community 57 - "TS Artifact & Event Sink"
Cohesion: 0.09
Nodes (15): ADR-0034, ADR-0024, CONTENT_TYPES, UPLOAD_TIMEOUT_MS, EventSink, ADR-0016, ADR-0032, resolveEventsFd() (+7 more)

### Community 58 - "Python Artifact Uploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 59 - "_RecUploader"
Cohesion: 0.11
Nodes (15): _FakeNovaAct, _install_provider(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 正常完成：先有界排空队列（30s）、再整目录 flush（flush 只兜漏网的）。顺序反了就等于没有队列。, 协作停：三层 with 已退出（会话已释放）之后才排空，用退出段预算；不 flush（中断产物留本地）。 会话释放的两个 __exit__ 也进同一条…, 异常退出路径（第三条）：会话已起后才炸 → 先释放会话（两个 __exit__）、再排空一次，异常仍原样冒泡。 (+7 more)

### Community 60 - "Lambda Asset Build"
Cohesion: 0.11
Nodes (25): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path (+17 more)

### Community 61 - "Version Skew Checking"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 62 - "Explain Command Tests"
Cohesion: 0.11
Nodes (28): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。, --step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；… (+20 more)

### Community 63 - "FargateEngine"
Cohesion: 0.12
Nodes (16): FargateEngine, Event, Job, NamedTuple, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。… (+8 more)

### Community 64 - "Architecture ADRs (Core)"
Cohesion: 0.15
Nodes (28): ADR 0001 UI 语言支持范围按引擎划分, ADR 0005 用例写在单一共享 .feature 文件, ADR 0006 形态 A：两子工程并列，暂不上编排器, ADR 0007 程序化登录，HITL 仅作逃生舱, ADR 0010 两引擎 spike 做成苹果对苹果基准, ADR 0013: 跨引擎共享的边界, ADR 0014 AI 优先的断言, 投票治判定抖动（assertion_votes） (+20 more)

### Community 65 - "_is_transient_network"
Cohesion: 0.11
Nodes (33): _error_text(), _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, _client_error() (+25 more)

### Community 66 - "gherkai_cli/__main__.py"
Cohesion: 0.06
Nodes (58): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_deploy(), _cmd_destroy(), _cmd_list_deterministic(), _cmd_plan() (+50 more)

### Community 67 - "Doctor Self-Check Tests"
Cohesion: 0.11
Nodes (26): _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 装了 deploy-aws extra → 经 provider 接缝调它的 doctor(args)，required 项失败让整体以退出码 2 结束。, 凭证探针抛 → aws.identity 必修失败、backend 标未查（可选）、以退出码 2 结束；不去碰后端。, region 解析不出 → aws.region 必修失败、后端标未查，不会把 NoRegionError 误诊成「prefix 配错」。, --profile 打错在 resolve_cloud_target 就炸（读 profile config）→ 与探针失败同一句诊断、以退出码 2… (+18 more)

### Community 68 - "test_user_steps.py"
Cohesion: 0.07
Nodes (47): _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +… (+39 more)

### Community 69 - "resolve_worker_cmd"
Cohesion: 0.08
Nodes (26): _find_worker_spec(), 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。, resolve_worker_cmd(), _runtime_version(), parametrize, dev/post/本地段版本**不在 PyPI/npm 上**（ADR 0037 决策 2b 的派生形态）→ 第四级跳过、直接 miss 报安装指引。 否则… (+18 more)

### Community 70 - "S3ResultStore"
Cohesion: 0.10
Nodes (20): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ResultStore, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。 (+12 more)

### Community 71 - "reconciler.py"
Cohesion: 0.14
Nodes (17): _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节的云端后端一侧）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…, 本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带…, 从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch… (+9 more)

### Community 72 - "_FakeEcsClient"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 73 - "report_store/local.py"
Cohesion: 0.12
Nodes (17): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+9 more)

### Community 74 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 75 - "test_event_sink.py"
Cohesion: 0.10
Nodes (9): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud(), test_emit_flushes_each_event() (+1 more)

### Community 76 - "Atomic File Writes"
Cohesion: 0.13
Nodes (20): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+12 more)

### Community 77 - "test_s3_report_store.py"
Cohesion: 0.17
Nodes (14): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。, S3ReportStore, S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3() (+6 more)

### Community 78 - "build_local_reconcile"
Cohesion: 0.19
Nodes (14): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, 后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。, 对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…, 接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从… (+6 more)

### Community 79 - "ADR Hygiene Checks"
Cohesion: 0.17
Nodes (20): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。 (+12 more)

### Community 80 - "_MissingThenStoppedEcs"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 81 - "Tunnel & Capability ADRs"
Cohesion: 0.14
Nodes (22): ADR 0011 AgentCore 浏览器层：默认 vs 自建, ADR 0034 无状态批量运行的事件链, --expose-local 与 job 组装期 URL 前缀替换, RunMeta.extra_http_headers 与 ngrok-skip-browser-warning 注入, ADR 0035 经隧道测试本地应用, 隧道生命周期按宿主分三形态, TunnelProvider 可插拔口子（首实现 ngrok）, TTL 按 definition 计算（compute_watch_ttl_s） (+14 more)

### Community 82 - "Docs & Terminology ADRs"
Cohesion: 0.12
Nodes (22): ADR 0027 run 报告归集索引, 产品文案零内部指代（禁词表 + AST 扫描护栏）, README / DEVELOPMENT 按读者分层, ADR 0039: 用户可见面不带内部指代：产品文案与文档分层, ADR 0040: 使用方角色模型与术语, 执行权限梯级（执行方式 × 执行后端正交轴）, 四顶帽子（feature 作者 / 测试开发 / 部署方 / contributor）, ADR 0041 面向 agent 的 CLI 能力 (+14 more)

### Community 83 - "tunnel.py"
Cohesion: 0.16
Nodes (11): _gen_auth(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+3 more)

### Community 84 - "Tunnel Host TTL Watch"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 85 - "Contributor Guardrail Docs"
Cohesion: 0.23
Nodes (18): /code-health-review 命令入口, /doc-health-review 命令入口, .claude/hooks/commit-gate.sh, CONTEXT.md 严格词表, 护栏 (guardrail), ADR 0039 用户面零内部指代, ADR 0043 驱动 gherkai 的 agent skill, ADR 0045 文档分层与归位 (+10 more)

### Community 86 - "_render_status"
Cohesion: 0.21
Nodes (16): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。 (+8 more)

### Community 87 - "Agent Skill Install"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 88 - "JSON Field Contract Tests"
Cohesion: 0.17
Nodes (18): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。, 递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque… (+10 more)

### Community 89 - "JobSource"
Cohesion: 0.09
Nodes (11): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+3 more)

### Community 90 - "Step Argument Assembly"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 91 - "Detached Launcher Tests"
Cohesion: 0.20
Nodes (19): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。 **真 spawn…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize… (+11 more)

### Community 92 - "Reconciler Stream Tests"
Cohesion: 0.11
Nodes (19): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events… (+11 more)

### Community 93 - "deterministic.py"
Cohesion: 0.08
Nodes (36): deterministic, clear(), deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match() (+28 more)

### Community 94 - "Safe-Point Trajectory Upload"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：安全点提前上传配套 json（ADR 0029）+ reportRefs（ADR…, act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _traj_refs(), _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 95 - "Subprocess Engine Adapter"
Cohesion: 0.15
Nodes (13): _join_pumps(), _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。… (+5 more)

### Community 96 - "Subprocess Engine Tests"
Cohesion: 0.29
Nodes (17): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried() (+9 more)

### Community 98 - "NPM Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 100 - "Feature File Parsing"
Cohesion: 0.15
Nodes (16): _index_ast_lines(), _map_argument(), parse_feature(), StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是… (+8 more)

### Community 101 - "Plan Job Generation"
Cohesion: 0.19
Nodes (17): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。, 撞名检测在施加 select 之前：收窄到只执行 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次运行哪几条。… (+9 more)

### Community 102 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 103 - "AWS Architecture ADRs"
Cohesion: 0.24
Nodes (17): ADR 0002 Midscene 不用 Bedrock GPT-5.5, ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL, ADR 0004 Nova Act 纯 IAM 鉴权（经 Workflow）, ADR 0008 Midscene→Bedrock 走进程内 SigV4 自签, ADR 0009 最大化使用 AWS 是硬前提, ADR 0012 Planning 由引擎模型兼任，不引独立 planner, ADR 0028 瞬时网络/SSL 韧性, ADR 0033 IaC AWS 后端与组合装配 (+9 more)

### Community 104 - "Evidence Collector Tests"
Cohesion: 0.15
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, importRunScope(), spyUploader() (+4 more)

### Community 105 - "Nova SDK Test Doubles"
Cohesion: 0.12
Nodes (8): _ActBoom, _FakeResult, _Meta, _NavErrorNova, RuntimeError, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 Nova SDK 的 act 异常：与成功结果一样带 metadata（time_worked_s 已真实计费、trajectory 已写盘）。

### Community 106 - "Changelog & Skill Docs"
Cohesion: 0.17
Nodes (15): skill 副本：云端后端分工与 variant, skill 副本：引擎选择与确定性 step 模板, skill 副本：环境就位与排障, gherkai agent skill（SKILL.md）, gherkai 命令行发行包入口页, agent skill (gherkai skill), AI 断言 (AI assertion), 确定性 step (deterministic step) (+7 more)

### Community 107 - "Task Definition Revisions"
Cohesion: 0.12
Nodes (10): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, 真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…, _StubEcs (+2 more)

### Community 108 - "ECS Task Exit Extraction"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 109 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 110 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 111 - "cli/DEVELOPMENT.md"
Cohesion: 0.14
Nodes (15): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+7 more)

### Community 112 - "Scenario Selection Flags"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 以退出码 2 结束并列出全部候选（id 标题），别静默运行空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 113 - "Run Scope Tests"
Cohesion: 0.13
Nodes (6): ADR-0014, ADR-0031, _events, fakePage, importMod(), testSink

### Community 114 - "Distribution Metadata Checks"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 115 - "Explain Command"
Cohesion: 0.16
Nodes (14): _cmd_explain(), _explain_cloud(), _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches(), explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…, 读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。… (+6 more)

### Community 116 - "Package README Guardrails"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 117 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 118 - "Scope Tag Resolution"
Cohesion: 0.26
Nodes (13): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。 (+5 more)

### Community 119 - "CDK Destroy/Bootstrap CLI"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，…, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 120 - "CDK Invocation Tests"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+3 more)

### Community 121 - "Architecture Diagram Exports"
Cohesion: 0.22
Nodes (14): Archify Diagram Export Style (JetBrains Mono embedded subsets), 云端载体 revision 钉定导出 SVG, 云端交付与 worker 身份拓扑交互图, Configuration Environment Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram, Execution Cloud Cascade Diagram, Execution Detached Gates Diagram (+6 more)

### Community 122 - "Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 123 - "build_cloud_stores"
Cohesion: 0.09
Nodes (24): build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), 云端后端一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。 (+16 more)

### Community 125 - "Provider CLI Flags"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 126 - "Artifact Upload & Shutdown"
Cohesion: 0.17
Nodes (13): 优雅终止（schedule 只下 handle.stop 逻辑指令）, ReportRef {kind, ref, label}, ADR 0029: engine artifact → S3（注入驱动）, 删本地（以上传成功确认为前提、整目录删）, 上传必须套超时（退出时间有界）, 上传时机四级（实时 ref / scope 末 flush / act 边界 / scenario 边界）, uploader 组件（from_env/to_report_ref/flush_and_cleanup）, ACT_TIMEOUT_S 不压（拒候选解法 B） (+5 more)

### Community 127 - "Release Notes Automation"
Cohesion: 0.26
Nodes (10): 版本真源 (single version source), GitHub Release 正文固定块, main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, render(), section(), wait_for_index.sh script, ci.yml 工作流 (+2 more)

### Community 128 - "test_sqlite_event_log.py"
Cohesion: 0.17
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 129 - "Subprocess Engine Launcher"
Cohesion: 0.18
Nodes (8): Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, Event, Job, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, SubprocessLauncher, Timer

### Community 130 - "test_fargate_engine.py"
Cohesion: 0.11
Nodes (26): _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。 (+18 more)

### Community 131 - "Exit Observer Lambda"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 132 - "Skill Deploy Token Checks"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。 (+3 more)

### Community 133 - "Advancer IAM Permissions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 134 - "test_error_step_also_enqueues_only_after_emit"
Cohesion: 0.12
Nodes (8): _NovaRaisesAfterFirstVote, list, 记 emit 与 enqueue 的**先后**（顺序即契约：判定绝不等截图字节）。, 第一票正常回（带 trajectory → 有截图可入队），第二票抛——把 except 出口逼成「有截图的 error step」。, except 出口（step 记 error）同守 emit→enqueue 序：三条出口共用一个收尾出口，不许有一条漏掉这层顺序。, _Result, test_error_step_also_enqueues_only_after_emit(), _TracingSink

### Community 135 - "_FakeEcs"
Cohesion: 0.22
Nodes (5): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…

### Community 136 - "test_tunnel.py"
Cohesion: 0.16
Nodes (18): make_tunnel(), NgrokTunnel, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, stop_tunnel(), _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。… (+10 more)

### Community 137 - "Skill Contract Rendering"
Cohesion: 0.26
Nodes (11): _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 138 - "User-Facing Text Guardrails"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 139 - "CDK Context Cache"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 140 - "AWS Client Stubs"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 141 - "Artifact Upload Tests (TS)"
Cohesion: 0.24
Nodes (7): mkLogDir(), mkShots(), tmproot(), errorText(), oneLineError(), ADR-0042, ADR-0029

### Community 142 - "_FakeCdp"
Cohesion: 0.33
Nodes (3): _FakeCdp, main_fakes(), 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。

### Community 143 - "Release Notes Tests"
Cohesion: 0.29
Nodes (9): _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」与 Release…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag(), test_repo_changelog_has_every_released_tag_and_unreleased(), test_section_extracts_exactly_one_version() (+1 more)

### Community 144 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 145 - "Fake Event Sink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 147 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 148 - "AWS Deploy Package Docs"
Cohesion: 0.25
Nodes (9): gherkai-deploy-aws contributor 手册, gherkai-deploy-aws 包入口页 (PyPI 长描述), ADR 0032 Fargate 执行环境, 版本升级的传播顺序（升 CLI → deploy → push-worker）, 退出码按命令分工, 云端后端用户指南, 团队成员需要的最小云端权限（submit vs run --backend cloud）, 升级三步之间的两段降级窗口 (+1 more)

### Community 149 - "Schedule & Retry ADRs"
Cohesion: 0.25
Nodes (9): ADR 0025: plan 模块 — .feature → job 列表, ADR 0026: schedule 模块 — 并发调度/失败隔离/优雅终止, _heartbeat_wrap（静默 worker 超时兜底）, schedule(run_meta, engines, sink, opts) -> RunResult, 三级归约（status + 原生量成本 + 墙钟）, ADR 0028: 网络/SSL 瞬时错误两层重试, EX_WORKER_NETWORK = 80（带外退出码信号）, network_error 分类（白名单具体瞬时类型） (+1 more)

### Community 150 - "Detached Run Orchestration"
Cohesion: 0.22
Nodes (9): ScheduleOpts（并发/隔离/grace/重试/心跳旋钮）, CAS(pending→running) 控严格并发, detached 标记（Stream filter + handler 分流）, HWM + 状态机单调条件写, job timeout（definition 载体 + 三路 enforce）, kicker Lambda（冷启动 + 接力 kickoff）, project / plan_next（纯归约 + 纯决策）, submit / status --wait 命令形态 (+1 more)

### Community 151 - "Report Aggregation & Status"
Cohesion: 0.28
Nodes (9): ADR 0027: RunReport 跨引擎归集索引, scope 内 step 级短路, ADR 0030: 实时写存储接缝, ADR 0031: job 生命周期态 skipped/aborted + severity, _aggregate 入口过滤 _NON_VERDICT, severity 数值序, Status enum 扩展（skipped/aborted/pending/running）, step_skipped 事件 + StepResult.shortcircuited (+1 more)

### Community 152 - "Worker Bin & Step Loading"
Cohesion: 0.25
Nodes (7): fromSource, hookSpec, ADR-0028, collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, STEP_EXTS

### Community 153 - "_StopTimeoutEcs"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 154 - "Tunnel Host Orchestration"
Cohesion: 0.25
Nodes (8): 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 155 - "Origin URL Mapping"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 156 - "End-to-End Test Harness"
Cohesion: 0.36
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 157 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 158 - "Cloud Status Command"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 159 - "CDK App & Backend Stack"
Cohesion: 0.29
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 160 - "Worker Revision Resolution"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 161 - "test_evidence.py"
Cohesion: 0.14
Nodes (23): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _picks(), step 级机读证据（evidence，ADR 0042 决策一/二/六）单测：映射 / 截图上界 / 目录键 / best-effort 钩子。 纯…, n 帧的合成 trajectory：thought_at 里的帧带 think call，每帧都有可解的 data URL 图。, 转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了就会让 evidence 静默互相覆盖。, 同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message… (+15 more)

### Community 162 - "detached.py"
Cohesion: 0.15
Nodes (13): cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。 (+5 more)

### Community 163 - "Doc Rules Checker"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 165 - "ValueError"
Cohesion: 0.40
Nodes (4): 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…, _read_ssm_list(), ValueError

### Community 166 - "Finished Run Idempotency"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 167 - "Context Glossary Checks"
Cohesion: 0.47
Nodes (4): _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries()

### Community 168 - "Core Package Docs"
Cohesion: 0.33
Nodes (6): 基础镜像 / variant / 默认指针, 执行核心库窄腰 (core-library narrow waist), adapters/fargate_engine（cloud Engine 实装）, core 包 contributor 文档, gherkai-core 发行包入口页, core 测试说明（单测 vs 集成）

### Community 169 - "Report Store & Manifest"
Cohesion: 0.40
Nodes (6): href 相对化（local 相对 / cloud 恒等 ref）, manifest.json（薄信封 + 扁平 report_index）, ReportStore.write(run_id, result), run_id（归集主键，生成权在组合根）, commit point 写序（数据面先、控制面后）, ADR 0034: 无状态批量运行（CQRS + reconciler）

### Community 170 - "DynamoDB Storage Design"
Cohesion: 0.33
Nodes (6): DDB 单表 + META/STATE 两 item, StepArgument S3 offload（content_ref/rows_ref）, RunState.jobs 改 Map<scope_id>, ADR 0033: iac_aws_backend CDK + 组合根接 FargateEngine, events 表 TTL（expires_at，7 天）, IAM 最小权限（动作 × 资源两维收窄）

### Community 171 - "_delayed_stopped_ecs"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order()

### Community 172 - "Verdict Evidence Glossary"
Cohesion: 0.40
Nodes (5): skill 副本：--json 字段契约, 派生视图 (derived view), step 证据 (step evidence), 判定真值 (verdict truth), adapters/_atomic（原子落盘）

### Community 173 - "_fixture"
Cohesion: 0.06
Nodes (40): cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, _stub_engine_capabilities(), arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate() (+32 more)

### Community 175 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 179 - "Plan Module Seams"
Cohesion: 0.40
Nodes (5): id 派生（scenarioId/scopeId 不透明、不 normalize）, parse seam（藏 gherkin-official）, plan(features, config, select) -> Job[], scope seam（tag 分组 + engine/timeout 校验）, select 谓词（scenario 筛选）

### Community 180 - "Run Persistence & Preflight"
Cohesion: 0.40
Nodes (5): on_job_complete / on_event 回调注入点, Store.preflight() 探活, RunPersistence 应用服务（persist.py）, 两层命名（--prefix 批量默认 + 单资源覆盖）, preflight fail-fast（点名 prefix）

### Community 181 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 182 - "Job Sink Primitives"
Cohesion: 0.50
Nodes (3): Job, Lock, Sink

### Community 183 - "Worker Subnet Selection"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 184 - "Image Parameter Mapping"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 185 - "Package Files Metadata"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 186 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 188 - "Worker Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 189 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 190 - "Command Span Parsing"
Cohesion: 0.67
Nodes (3): CommandSpan, NamedTuple, 一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…

### Community 193 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

## Ambiguous Edges - Review These
- `云端载体 revision 钉定导出 SVG` → `云端交付与 worker 身份拓扑交互图`  [AMBIGUOUS]
  docs/diagrams/index.html · relation: conceptually_related_to
- `云端交付与 worker 身份拓扑交互图` → `Execution Cloud Cascade Diagram`  [AMBIGUOUS]
  docs/diagrams/execution-cloud-cascade.svg · relation: conceptually_related_to
- `Configuration Environment Inheritance Diagram` → `Getting Started Component Ownership Diagram`  [AMBIGUOUS]
  docs/diagrams/getting-started-component-ownership.svg · relation: conceptually_related_to
- `Local App Testing Tunnel Topology Diagram` → `README Runtime Topology Diagram`  [AMBIGUOUS]
  docs/diagrams/readme-runtime-topology.svg · relation: conceptually_related_to
- `一次 run 的生命周期主干（parse → scope 分组 → begin → 驱动 → 判定归约与报告）` → `图：scenario 到 job 的分组`  [AMBIGUOUS]
  docs/diagrams/writing-features-scenario-to-job.svg · relation: conceptually_related_to
- `代码健康度复盘任务说明` → `docs/code-health-review.md（命令入口所指）`  [AMBIGUOUS]
  .claude/commands/code-health-review.md · relation: semantically_similar_to
- `文档健康度复盘任务说明` → `docs/doc-health-review.md（命令入口所指）`  [AMBIGUOUS]
  .claude/commands/doc-health-review.md · relation: semantically_similar_to

## Knowledge Gaps
- **234 isolated node(s):** `LoadUserStepsDeps`, `Check`, `Job`, `Scenario`, `ShutdownDeps` (+229 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `云端载体 revision 钉定导出 SVG` and `云端交付与 worker 身份拓扑交互图`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `云端交付与 worker 身份拓扑交互图` and `Execution Cloud Cascade Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Configuration Environment Inheritance Diagram` and `Getting Started Component Ownership Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Local App Testing Tunnel Topology Diagram` and `README Runtime Topology Diagram`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `一次 run 的生命周期主干（parse → scope 分组 → begin → 驱动 → 判定归约与报告）` and `图：scenario 到 job 的分组`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `代码健康度复盘任务说明` and `docs/code-health-review.md（命令入口所指）`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `文档健康度复盘任务说明` and `docs/doc-health-review.md（命令入口所指）`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._