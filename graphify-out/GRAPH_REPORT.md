# Graph Report - yaozhou  (2026-09-30)

## Corpus Check
- 337 files · ~540,847 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5288 nodes · 11679 edges · 303 communities (200 shown, 103 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 773 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2f7874d5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Job
- test_main.py
- test_backend_cloud.py
- StepResult
- workers.py
- test_project.py
- test_workers.py
- gherkai_deploy_aws/names.py
- ContainerEngine
- _FakeSink
- Any
- RunResult
- RunState
- compose.py
- test_skill.py
- test_stack.py
- test_deploy_cmd.py
- test_reconcile.py
- ensure_workflow_definition
- query_capabilities
- main
- test_worker_variant.py
- test_evidence.py
- test_schedule.py
- test_conditional_writes.py
- test_tunnel_cli.py
- ._run_cdk
- test_interrupt_model.py
- User Guide Configuration Docs
- _run_step
- test_lifecycle_states.py
- run_scope.py
- materialize.py
- test_fargate_engine.py
- .deploy
- _AbsentEngine
- test_container.py
- sigv4Fetch
- test_argument.py
- 判定的计算路径：从单次投票到退出码
- User Docs Guardrails
- BackendStack
- LocalReportStore
- redact_url_userinfo
- gherkai_runtime/names.py
- resolve_container_engine
- JobState
- StepDone
- test_sqlite_event_log.py
- deterministic.mts
- evidence.mts
- Artifact Upload Tests
- _doc_rules.py
- test_compose.py
- test_plan.py
- render.py
- scan_family
- event-sink.mts
- Python Artifact Uploader
- test_event_sink.py
- test_lambda_asset.py
- _fake_locator
- _explain_run
- FargateEngine
- ADR 0024 worker/core 协议
- _is_transient_network
- gherkai_cli/__main__.py
- ._connect
- test_user_steps.py
- fargate_engine.py
- _argv
- test_cloud_reconcile.py
- _FakeEcsClient
- S3ReportStore
- TypeScript Build Config
- build_engines
- LocalRunStore
- NgrokTunnel
- _cmd_doctor
- ADR Hygiene Checks
- _MissingThenStoppedEcs
- ADR 0038 worker 镜像交付
- ADR 0037 分发与包化
- ScopeStarted
- test_tunnel_host.py
- CONTRIBUTING.md
- _render_status
- Agent Skill Install
- test_cli_json_contract.py
- JobSource
- atomic_write_json
- gherkai_worker_novaact/__init__.py
- test_lambda_handlers.py
- test_deterministic.py
- test_subprocess_engine.py
- _engine_with_fake_ecs
- _StopTimeoutEcs
- TS Artifact Uploader
- NPM Dependencies
- _RecUploader
- cli.py
- deterministic.py
- Diagram Build Script
- container.py
- evidence.test.mts
- user_steps.py
- CHANGELOG.md
- cleanup_pass
- ImageInfo
- _StampSsm
- Event Wallclock Analysis
- tunnel_host.py
- subprocess_engine.py
- run-scope.test.mts
- check_dist_metadata.py
- _clean_env
- Package README Guardrails
- event_from_json
- Provider
- Path
- _Recorder
- Architecture Diagram Exports
- Worker Package Manifest
- _presend_act_siblings
- cli/tests/conftest.py
- .add_arguments
- Artifact Upload & Shutdown
- check_version_skew
- .inspect
- digest_for_repo
- aws
- .delete_worker
- Skill Deploy Token Checks
- Advancer IAM Permissions
- 确定性 step 的写法：从「能注册」到「稳、可诊断、可维护」
- _error_text
- test_tunnel.py
- Skill Contract Rendering
- User-Facing Text Guardrails
- 0047. CLI 人读输出：清单用表格、层级用树、状态上语义颜色，统一由 rich 渲染
- AWS Client Stubs
- artifact-upload.test.mts
- Status
- README.md
- Worker Signal Interrupt Tests
- _CdkWritingContext
- tunnel.py
- ECS Task Timing Capture
- _FakeTable
- Schedule & Retry ADRs
- Detached Run Orchestration
- Report Aggregation & Status
- user-steps.mts
- test_s3_report_store.py
- exit_observer.py
- Path
- ValueError
- Graphify Refresh Script
- deterministic_steps.py
- textui.py
- .inspect
- ._pump
- Path
- Doc Rules Checker
- list_registry
- _await_engine
- redact.mts
- _fixture
- CONTENT_TYPES
- Report Store & Manifest
- DynamoDB Storage Design
- _patch_skew
- job-source.mts
- release.yml 发布链
- 03-midscene-grounding.ts
- Echo Test Worker
- Cloud Test Infrastructure
- test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine
- test_release_notes.py
- Plan Module Seams
- Run Persistence & Preflight
- TypeScript Dev Dependencies
- test_local_result_store_atomic.py
- Worker Subnet Selection
- test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration
- Package Files Metadata
- Repository Metadata
- ADR 0035 经隧道测试本地应用
- Worker Artifact Upload
- Upload Call Recorder
- 05-negative-assertions.ts
- datetime
- argument.mts
- NPM Scripts
- AgentCore CDP Script
- Background Upload Queue
- Run Summarization Script
- Pre-commit Hook
- Bedrock AgentCore SDK
- DynamoDB SDK Client
- Adapter Implementations Layer
- user-steps.test.mts
- redact.test.mts
- deterministic.steps.mts
- 01-model-sigv4.ts
- bin.mts
- agentcore-sigv4.test.mts
- list_workers
- OpenAI Dependency
- tsx Dependency
- Bounded Queue Drain
- Log Upload Enablement
- Fail-Loud Config Validation
- Local No-Op Uploader
- Gherkai Workspace Root
- sync-derived.sh
- wording-guard.sh
- Architecture Layers Diagram
- Run Lifecycle Diagram
- Artifacts Evidence Chain Diagram
- Cloud Backend Upgrade Diagram
- Gherkai Core Package
- AWS Deployment Package
- Gherkai Runtime Package
- NovaAct Worker Package
- runStep
- index.mts
- resolve-hook.mts
- error-text.mts
- event-sink.test.mts
- no-artifacts.test.mts
- job-source.test.mts
- ADR-0008
- main
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- _FakeS3
- stop_tunnel
- S3StepArgumentOffloader
- DEFAULT_MODEL
- MODEL
- MODEL_FAMILY_PATTERNS
- ADR-0033
- ADR-0037
- ADR-0044
- ADR-0016
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0032
- ADR-0033
- ADR-0042
- UPLOAD_TIMEOUT_MS
- Popen
- Scenario
- ArgumentParser
- Step
- StepArgument
- BaseException
- list
- _Worker
- 04-planning-probe.ts
- CommandSpan
- .preflight
- ADR-0014
- ADR-0019
- ADR-0020
- ADR-0022
- ADR-0024
- ADR-0026
- ADR-0027
- ADR-0028
- ADR-0029
- ADR-0031
- ADR-0035
- ADR-0036
- ADR-0037
- ADR-0039
- ADR-0042
- ADR-0044
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- BROWSER_CLOSE_BUDGET_MS
- CONNECT_BACKOFF_MS
- INFLIGHT_SETTLE_MS
- Job
- MIN_GRACE_MARGIN_MS
- QUEUE_DRAIN_EXIT_MS
- Scenario
- ShutdownDeps
- Step
- STOP_SESSION_BUDGET_MS
- datetime
- Exception
- RunMeta
- Event
- Job
- RunResult

## God Nodes (most connected - your core abstractions)
1. `main()` - 216 edges
2. `RunState` - 118 edges
3. `Job` - 113 edges
4. `RunMeta` - 107 edges
5. `JobState` - 101 edges
6. `Status` - 97 edges
7. `Provider` - 95 edges
8. `JobResult` - 71 edges
9. `Scenario` - 66 edges
10. `Step` - 65 edges

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

## Communities (303 total, 103 thin omitted)

### Community 0 - "Job"
Cohesion: 0.04
Nodes (84): DynamoDBRunStore, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→以退出码 2 结束）。 用 `table.load()`（即…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, 一次性写完整态（即 create_run 的两 item 一起 put；语义同 local save_run）。, 读回 definition（从 META item 的 meta_json）；不存在返回 None。, STATE item 上有没有 `detached` 标记（ADR 0034）：True 表示无状态批量运行的 submit 建的 run。…, RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。, run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。 **写序… (+76 more)

### Community 1 - "test_main.py"
Cohesion: 0.04
Nodes (95): _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), _plan_names(), cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：运行前先问一次能力自述，worker 非零退出 → 起任何 job 之前以退出码 2 结束（不进 job 级 error）。… (+87 more)

### Community 2 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 3 - "StepResult"
Cohesion: 0.12
Nodes (32): RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…, render_text(), _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, 云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的…, test_explain_cloud_reads_evidence_from_s3(), test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact() (+24 more)

### Community 4 - "workers.py"
Cohesion: 0.06
Nodes (72): datetime, Aws, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable() (+64 more)

### Community 5 - "test_project.py"
Cohesion: 0.08
Nodes (61): plan_next(), project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, _ev(), _exit(), _meta(), _passed_events() (+53 more)

### Community 6 - "test_workers.py"
Cohesion: 0.06
Nodes (83): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+75 more)

### Community 7 - "gherkai_deploy_aws/names.py"
Cohesion: 0.13
Nodes (14): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, CloudFormation stack 名（即 `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 生效 VPC 取值的 SSM 路径（ADR 0037 决策 6「VPC 取值持久化比对，三态齐全」）。 值形态三种：`default` / `new:<所建… (+6 more)

### Community 8 - "ContainerEngine"
Cohesion: 0.16
Nodes (8): ContainerEngine, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。, 拉镜像（基础镜像同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。, 短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。, 长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。, docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 结构不同）。 `binary`…, test_probe_reports_missing_binary_without_raising()

### Community 9 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 11 - "RunResult"
Cohesion: 0.04
Nodes (68): 核心注入接口 (core ports), adapters/subprocess_engine（local Engine 实装）, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, 一次执行的机器可读汇总判定，即 **definition（run_meta）与判定（jobs）的显式合成**（ADR 0016/0026）。… (+60 more)

### Community 12 - "RunState"
Cohesion: 0.12
Nodes (28): 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…, RunState, run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。 满足 ADR…, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale…, _ddb_store(), _is_ddb_too_large(), _offloader(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。… (+20 more)

### Community 13 - "compose.py"
Cohesion: 0.06
Nodes (52): build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), is_botocore_error(), _make_ddb_table(), _make_ecr_client(), _make_ecs_client(), _make_lambda_client() (+44 more)

### Community 14 - "test_skill.py"
Cohesion: 0.05
Nodes (61): bare_flags(), clean_flag(), extract_command_spans(), is_placeholder(), skill 目录下全部 markdown（含契约副本——转换后它本就不含内部指代，无例外）。, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。, 代码跨里出现的全部 `--flag`（含 `gherkai …` 跨内的），→ (flag, 行号, 跨原文)。弱断言用。, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。 (+53 more)

### Community 15 - "test_stack.py"
Cohesion: 0.06
Nodes (60): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。 (+52 more)

### Community 16 - "test_deploy_cmd.py"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 以退出码 2 结束并点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 17 - "test_reconcile.py"
Cohesion: 0.07
Nodes (43): 无状态批量运行 (stateless batch execution), EventLog, finalize_report(), Launcher, Job, Protocol, reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。 `tick(run_id, meta)` 一步推进：读…, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由… (+35 more)

### Community 18 - "ensure_workflow_definition"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 19 - "query_capabilities"
Cohesion: 0.05
Nodes (50): _ask_worker(), build_local_stores(), engine_min_grace(), local_artifact_locations(), match_deterministic(), Path, RuntimeError, query_capabilities() (+42 more)

### Community 20 - "main"
Cohesion: 0.05
Nodes (59): main(), _det_feature(), 对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码语义见…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。, 冲突预检（实际运行将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。 (+51 more)

### Community 21 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (49): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。 值是…, worker_image_key(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。 (+41 more)

### Community 22 - "test_evidence.py"
Cohesion: 0.08
Nodes (51): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _done(), _Nova, _NovaRaisesAfterFirstVote, _picks(), parametrize, Path (+43 more)

### Community 23 - "test_schedule.py"
Cohesion: 0.22
Nodes (48): 执行一次 run（RunMeta 即 definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+40 more)

### Community 24 - "test_conditional_writes.py"
Cohesion: 0.08
Nodes (48): _initial(), _meta(), RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+40 more)

### Community 25 - "test_tunnel_cli.py"
Cohesion: 0.09
Nodes (41): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, run --json 的输出脱敏、落盘的 run 定义保留明文（ADR 0035 决策 5）。 stdout 里 step 文本与判定消息的隧道地址都是…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。 (+33 more)

### Community 26 - "._run_cdk"
Cohesion: 0.08
Nodes (22): cdk_command(), check_cdk(), check_node(), _node_major(), Path, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer… (+14 more)

### Community 27 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (33): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True 表示中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True 表示退避中收到停止信号（应停止重连）。 用…, captured() (+25 more)

### Community 28 - "User Guide Configuration Docs"
Cohesion: 0.08
Nodes (48): 配置：环境变量与通用选项, 由 gherkai 注入的环境变量, 模型选择（默认模型与家族推断）, 常见问题, 开始使用, AWS 前置（凭证、region、服务开通）, 用 doctor 自检, 上手路径一：交给 AI agent（skill install） (+40 more)

### Community 29 - "_run_step"
Cohesion: 0.07
Nodes (51): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+43 more)

### Community 30 - "test_lifecycle_states.py"
Cohesion: 0.08
Nodes (23): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一… (+15 more)

### Community 31 - "run_scope.py"
Cohesion: 0.11
Nodes (28): ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_evidence(), _attach_traj_refs(), _capabilities(), _collect_traj(), _cost_from_result(), _drain_evidence_uploads() (+20 more)

### Community 32 - "materialize.py"
Cohesion: 0.17
Nodes (29): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+21 more)

### Community 33 - "test_fargate_engine.py"
Cohesion: 0.09
Nodes (49): _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。 (+41 more)

### Community 34 - ".deploy"
Cohesion: 0.14
Nodes (9): 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点以退出码 2 结束）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…, flag → CDK context（app/stack 侧读的那四个配置项 + 版本戳）。 `--vpc` 一个 flag…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 解析链的诊断归口：解析得出 → target；失败 → 打一句诊断、返 None（调用点归退出码）。 **每个动作在碰 AWS 之前都要经这一口**：不存在的… (+1 more)

### Community 36 - "test_container.py"
Cohesion: 0.18
Nodes (12): _Fake, _inspect_spec(), 容器引擎口子测试（ADR 0038「容器引擎口子」）。 **两层证据，分清边界**： - 大部分用一个**假 docker**（记 argv/stdin 的…, 「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。, **密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。, 假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。, test_inspect_missing_image_is_not_an_error(), test_inspect_other_failure_raises() (+4 more)

### Community 37 - "sigv4Fetch"
Cohesion: 0.20
Nodes (6): main(), main(), getRegion(), modelSigner_(), sigv4Fetch(), agentOpts()

### Community 38 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令由去引号的 step 自然语言与（可选）多行参数拼成（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 39 - "判定的计算路径：从单次投票到退出码"
Cohesion: 0.08
Nodes (47): gherkai-deploy-aws contributor 手册, gherkai-deploy-aws 包入口页 (PyPI 长描述), ADR 0032 Fargate 执行环境, 图：job 收场态判定（有序短路四问）, 图：判定四层归约（worker 侧汇总 / core 侧归约）, 图：scenario 到 job 的分组, 架构总览：五层结构、一次 run 的生命周期、包与发行物, 同一条链的两种载体（--backend local / cloud 只替换 adapter） (+39 more)

### Community 40 - "User Docs Guardrails"
Cohesion: 0.09
Nodes (36): changelog_unreleased(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, _default_model_claims(), _default_model_ids(), parametrize, Path, 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…, owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。 (+28 more)

### Community 41 - "BackendStack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源是发起这次部署的命令（`gherkai deploy`…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 42 - "LocalReportStore"
Cohesion: 0.18
Nodes (36): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077… (+28 more)

### Community 43 - "redact_url_userinfo"
Cohesion: 0.12
Nodes (20): _pump_log(), 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, Any, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, 递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。, redact_deep(), redact_url_userinfo() (+12 more)

### Community 44 - "gherkai_runtime/names.py"
Cohesion: 0.08
Nodes (32): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…, ssm_worker_template_path(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的… (+24 more)

### Community 45 - "resolve_container_engine"
Cohesion: 0.18
Nodes (14): 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, resolve_container_engine(), ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。…, arm 变体真镜像 → 架构判据拒（即 push-worker 以退出码 2 结束那一支）。 用 alpine（小）代替真 worker 镜像：判据只看…, `docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取…, `--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。, test_default_is_docker(), test_env_selects_engine_and_flag_wins() (+6 more)

### Community 46 - "JobState"
Cohesion: 0.04
Nodes (93): 云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功， 否则落回本机后端、报「未找到…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。 (+85 more)

### Community 47 - "StepDone"
Cohesion: 0.11
Nodes (39): format_event(), 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。… (+31 more)

### Community 48 - "test_sqlite_event_log.py"
Cohesion: 0.17
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 49 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 50 - "evidence.mts"
Cohesion: 0.09
Nodes (30): actionsOf(), buildEvidence(), BuildEvidenceInput, ENGINE, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct (+22 more)

### Community 51 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 52 - "_doc_rules.py"
Cohesion: 0.12
Nodes (30): ai_side_docs(), classify(), code_comment_files(), comment_units(), diagram_sources(), long_term_docs(), Path, 人读文本的规则、扫描面与抽取器：护栏三层共用的**单一事实源**（ADR 0046）。 内容三类：①规则——内部指代表 FORBIDDEN、口吻表… (+22 more)

### Community 53 - "test_compose.py"
Cohesion: 0.04
Nodes (68): _find_worker_spec(), prune_empty_dirs(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`… (+60 more)

### Community 54 - "test_plan.py"
Cohesion: 0.06
Nodes (59): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, _plan(), parametrize (+51 more)

### Community 55 - "render.py"
Cohesion: 0.07
Nodes (42): _add_act(), _add_step(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), explain_tree() (+34 more)

### Community 56 - "scan_family"
Cohesion: 0.18
Nodes (11): _parse_ts(), _pending_cleanup(), family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, family 的全部 ACTIVE revision（带 tags）。 两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-…, tag 里的 ISO 串 / boto3 回来的 datetime → aware UTC datetime；空或读不懂 → None。, 已退休（带 retired-at）与孤儿（带血缘 tags、不在任何版本的映射里）——清理 pass 的候选，列出来才可解释 「为什么 family 里…, RevisionInfo (+3 more)

### Community 57 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0016, ADR-0032, ADR-0034, EventSink, ADR-0024, ADR-0033, resolveEventsFd()

### Community 58 - "Python Artifact Uploader"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 59 - "test_event_sink.py"
Cohesion: 0.06
Nodes (23): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, 隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…, `https://u:p@host/x` → `https://***@host/x`；None 原样返回。, redact_url_userinfo() (+15 more)

### Community 60 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (25): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path (+17 more)

### Community 61 - "_fake_locator"
Cohesion: 0.07
Nodes (42): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+34 more)

### Community 62 - "_explain_run"
Cohesion: 0.10
Nodes (31): _evidence_fixture(), _explain(), _explain_job(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。 (+23 more)

### Community 63 - "FargateEngine"
Cohesion: 0.16
Nodes (13): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+5 more)

### Community 64 - "ADR 0024 worker/core 协议"
Cohesion: 0.15
Nodes (28): ADR 0001 UI 语言支持范围按引擎划分, ADR 0005 用例写在单一共享 .feature 文件, ADR 0006 形态 A：两子工程并列，暂不上编排器, ADR 0007 程序化登录，HITL 仅作逃生舱, ADR 0010 两引擎 spike 做成苹果对苹果基准, ADR 0013: 跨引擎共享的边界, ADR 0014 AI 优先的断言, 投票治判定抖动（assertion_votes） (+20 more)

### Community 65 - "_is_transient_network"
Cohesion: 0.15
Nodes (27): _is_transient_network(), 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是…, 造一个 botocore ClientError（response 里带 Error.Code /…, _target_closed(), test_agentcore_permanent_wrapping_chain_not_transient() (+19 more)

### Community 66 - "gherkai_cli/__main__.py"
Cohesion: 0.04
Nodes (86): ArgumentParser, _add_selection_flags(), _build_parser(), _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_deploy() (+78 more)

### Community 67 - "._connect"
Cohesion: 0.15
Nodes (6): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。

### Community 68 - "test_user_steps.py"
Cohesion: 0.13
Nodes (25): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` 是 env `GHERKAI_STEPS_DIR`…, parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, `_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。, `_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。, 给了目录但不存在就是配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。 (+17 more)

### Community 69 - "fargate_engine.py"
Cohesion: 0.17
Nodes (9): 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), NamedTuple, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, 一次 DescribeTasks 探测的结果——**三个正交事实各自命名**（ADR 0024「exitCode 落值延迟」；前两个见下、第三个…, events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。, TaskProbe (+1 more)

### Community 70 - "_argv"
Cohesion: 0.18
Nodes (11): _argv(), _parse_destroy(), Path, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证，…, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（实际运行撞到）；`--yes` 等同于 `--force`，不给则让 cdk 自己问。, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_destroy_yes_passes_force_to_cdk_and_is_off_by_default() (+3 more)

### Community 71 - "test_cloud_reconcile.py"
Cohesion: 0.05
Nodes (63): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, _FakeStartEngine, _job(), _meta() (+55 more)

### Community 72 - "_FakeEcsClient"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 73 - "S3ReportStore"
Cohesion: 0.09
Nodes (22): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+14 more)

### Community 74 - "TypeScript Build Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 75 - "build_engines"
Cohesion: 0.08
Nodes (30): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, Path, 某引擎定位链 miss **不连坐**另一个引擎项（ADR 0037 决策 3）：dev 下 midscene 未装是常态， novaact-only 的… (+22 more)

### Community 76 - "LocalRunStore"
Cohesion: 0.04
Nodes (80): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, SqliteEventLog, _atomic_write_json(), LocalRunStore, Path, 读回运行态（RunState）；不存在返回 None。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。 (+72 more)

### Community 77 - "NgrokTunnel"
Cohesion: 0.24
Nodes (9): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。, test_ngrok_binary_missing_reports_install_hint(), test_ngrok_start_spawns_agent_and_reads_log(), test_ngrok_start_timeout_reports_authtoken_hint() (+1 more)

### Community 78 - "_cmd_doctor"
Cohesion: 0.09
Nodes (25): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+17 more)

### Community 79 - "ADR Hygiene Checks"
Cohesion: 0.17
Nodes (20): prose_lines(), markdown 的正文行：剥掉围栏代码块、行内反引号代码，可选剥掉 YAML frontmatter；行号与原文一致。…, _adrs(), parametrize, Path, ADR、journey 与长期文档的机械卫生项（CLAUDE.md 文档纪律里能逐行判定的那几条，此前每轮 doc-health 靠人查）。 - 每篇 ADR…, 长期文档只指稳定物：不链具体的 journey 文件、不写裸 WP 编号（代码块与行内代码不算）。, AI 侧文档口吻放开，但决策六形态②的自造复合词全仓不用（歧义不是效率）；讨论这些词本身的文档除外。 (+12 more)

### Community 80 - "_MissingThenStoppedEcs"
Cohesion: 0.09
Nodes (21): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _delayed_stopped_ecs(), _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。 (+13 more)

### Community 81 - "ADR 0038 worker 镜像交付"
Cohesion: 0.24
Nodes (17): ADR 0002 Midscene 不用 Bedrock GPT-5.5, ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL, ADR 0004 Nova Act 纯 IAM 鉴权（经 Workflow）, ADR 0008 Midscene→Bedrock 走进程内 SigV4 自签, ADR 0009 最大化使用 AWS 是硬前提, ADR 0012 Planning 由引擎模型兼任，不引独立 planner, ADR 0028 瞬时网络/SSL 韧性, ADR 0033 IaC AWS 后端与组合装配 (+9 more)

### Community 82 - "ADR 0037 分发与包化"
Cohesion: 0.08
Nodes (37): ADR 0027 run 报告归集索引, RunMeta.extra_http_headers 与 ngrok-skip-browser-warning 注入, worker --capabilities 能力自述入口, ADR 0036 确定性能力自述, CLI list-deterministic --engine, plan 命中标注与 --match-steps 批量匹配, 确定性 step 注册必带 description/example 元数据, ADR 0037 分发与包化 (+29 more)

### Community 83 - "ScopeStarted"
Cohesion: 0.09
Nodes (31): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, ScopeStarted, StepStarted, Action (+23 more)

### Community 84 - "test_tunnel_host.py"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 85 - "CONTRIBUTING.md"
Cohesion: 0.15
Nodes (23): /code-health-review 命令入口, /doc-health-review 命令入口, PATH, commit-gate.sh script, _entries(), `CONTEXT.md` 严格词表的形态护栏（ADR 0045 决策八；CLAUDE.md 文档纪律「CONTEXT.md 是严格词表」条）。 词条 =…, test_each_entry_is_term_definition_and_avoid_words(), test_glossary_has_entries() (+15 more)

### Community 86 - "_render_status"
Cohesion: 0.13
Nodes (23): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。 (+15 more)

### Community 87 - "Agent Skill Install"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 88 - "test_cli_json_contract.py"
Cohesion: 0.11
Nodes (25): _cmd_list_engines(), _probe_engines(), 两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…, 列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…, explain_to_dict(), 把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…, _assert_documented(), _documented_keys() (+17 more)

### Community 89 - "JobSource"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 90 - "atomic_write_json"
Cohesion: 0.11
Nodes (22): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+14 more)

### Community 91 - "gherkai_worker_novaact/__init__.py"
Cohesion: 0.20
Nodes (6): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…, 进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，回归哨兵）。 被…, `--no-report` 即真不生成（ADR 0037 决策 3）：env GHERKAI_NO_ARTIFACTS=1 时 worker…, 有 metadata.trajectory_file_path 也不收集——否则 step_done 会带 reportRef、RunResult…, test_flag_reads_env(), test_trajectory_collection_is_skipped_under_no_artifacts()

### Community 92 - "test_lambda_handlers.py"
Cohesion: 0.03
Nodes (110): _FakeEcs, Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认… (+102 more)

### Community 93 - "test_deterministic.py"
Cohesion: 0.16
Nodes (18): deterministic(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 运行（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真 step 命中面与派发一致）。, description/example 必填（ADR 0036：注册即暴露，缺元数据意味着能力不可发现，fail-loud）。, 注册表清单经自述入口出去（ADR 0036「2.」/「5.」）真子进程：`--capabilities` 的 `deterministic_steps`… (+10 more)

### Community 94 - "test_subprocess_engine.py"
Cohesion: 0.23
Nodes (20): _engine(), _job(), Job, RunMeta, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, pump 线程必须**先于**写 stdin 起：job JSON >64KB（DocString）× worker 读 stdin 前先吐 >64KB…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr…, _rm() (+12 more)

### Community 95 - "_engine_with_fake_ecs"
Cohesion: 0.25
Nodes (8): _engine_with_fake_ecs(), DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null(), test_probe_task_stopped_with_exit_code()

### Community 96 - "_StopTimeoutEcs"
Cohesion: 0.27
Nodes (8): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container(), test_task_def_and_container_name()

### Community 98 - "NPM Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 99 - "_RecUploader"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。 (+10 more)

### Community 100 - "cli.py"
Cohesion: 0.08
Nodes (28): classify_vpc_state(), _error_code(), _make_cfn_client(), _make_hint_clients(), _make_ssm_client(), _make_sts_client(), Exception, `gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`… (+20 more)

### Community 101 - "deterministic.py"
Cohesion: 0.20
Nodes (11): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+3 more)

### Community 102 - "Diagram Build Script"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 103 - "container.py"
Cohesion: 0.29
Nodes (6): ContainerError, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, UnsupportedContainerEngine

### Community 104 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 105 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 106 - "CHANGELOG.md"
Cohesion: 0.09
Nodes (26): skill 副本：--json 字段契约, skill 副本：云端后端分工与 variant, skill 副本：引擎选择与确定性 step 模板, skill 副本：环境就位与排障, gherkai agent skill（SKILL.md）, gherkai 命令行发行包入口页, agent skill (gherkai skill), AI 断言 (AI assertion) (+18 more)

### Community 107 - "cleanup_pass"
Cohesion: 0.09
Nodes (18): cleanup_pass(), CleanupOutcome, _hours(), _iter_image_params(), _mapped_arn(), _non_terminal_statuses(), 枚举 `worker-image/*` 全部参数（**含所有版本、所有引擎**）→ `(engine, tag, value)`。…, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看… (+10 more)

### Community 108 - "ImageInfo"
Cohesion: 0.29
Nodes (5): ImageInfo, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。, test_target_platform_judgement()

### Community 109 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 110 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q 在 [0,1] 内）。sorted_vals 非空、已升序。 (+7 more)

### Community 111 - "tunnel_host.py"
Cohesion: 0.20
Nodes (9): gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 112 - "subprocess_engine.py"
Cohesion: 0.09
Nodes (22): _join_pumps(), Event, Job, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的… (+14 more)

### Community 113 - "run-scope.test.mts"
Cohesion: 0.09
Nodes (12): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+4 more)

### Community 114 - "check_dist_metadata.py"
Cohesion: 0.25
Nodes (14): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 真值集：源目录的文件系统遍历（**不用 `git ls-files`**——见模块 docstring 断言 4 的理由： 受不受 git 跟踪与进不进…, 断言 4：wheel 内 skill 文件集 == 源目录文件集，且 wheel 里不含评测资产。 (+6 more)

### Community 115 - "_clean_env"
Cohesion: 0.20
Nodes (10): _clean_env(), 真子进程 + 真 env：`-m gherkai_worker_novaact --capabilities` 的 `deterministic_steps`…, fail-loud 到进程边界：坏 step 文件 → 自述入口也非 0 退出、stderr 指名文件（不静默给出残缺清单）。, 加载成功也留一行 stderr（文件数 + 目录）：使用方据它分清「目录没被读到」与「pattern 没命中」。, 未注入目录表示使用方没定制，正常路径不打这行（诊断行不许变成人人都看见的噪声）。, 子进程 env：保留 PATH/PYTHONPATH 等运行必需项，剥掉可能干扰的 GHERKAI_* / AWS 落点。, test_broken_steps_dir_makes_capabilities_exit_nonzero(), test_capabilities_subprocess_includes_user_steps() (+2 more)

### Community 116 - "Package README Guardrails"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 117 - "event_from_json"
Cohesion: 0.08
Nodes (40): _argument_to_json(), _cost_from_json(), event_from_json(), event_from_line(), job_to_json(), Event, wire 协议（ADR 0024）：core↔worker 的 JSON 序列化层 + 退出码约定。 core 把 Job 序列化成 JSON 喂…, JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。 事件通道随形态而异：子进程态下是专用… (+32 more)

### Community 118 - "Provider"
Cohesion: 0.06
Nodes (78): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。…, flag 面全集锁定（枚举型护栏）：三个 context 配置项 flag + AWS 定位二件套 + 两个「前端的中立版的 AWS 精确化」（见 cli…, `--allow-vpc-change` / `--require-approval` **只贴 deploy**（枚举型全集比对，同上条口径）。…, 子动词全集锁定（枚举型护栏）+ **只挂 deploy**。 挂到 destroy 上不是「多个没用的命令」而是危险：前端的 destroy 分派不看… (+70 more)

### Community 120 - "_Recorder"
Cohesion: 0.17
Nodes (10): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 以退出码 2 结束且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前以退出码 2 结束。 **不能落到…, _Recorder (+2 more)

### Community 121 - "Architecture Diagram Exports"
Cohesion: 0.22
Nodes (14): Archify Diagram Export Style (JetBrains Mono embedded subsets), 云端载体 revision 钉定导出 SVG, 云端交付与 worker 身份拓扑交互图, Configuration Environment Inheritance Diagram, Deterministic Steps Registry Overview Diagram, Deterministic Steps Truth Sources Diagram, Execution Cloud Cascade Diagram, Execution Detached Gates Diagram (+6 more)

### Community 122 - "Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 123 - "_presend_act_siblings"
Cohesion: 0.25
Nodes (12): _presend_act_siblings(), act 边界的安全点提前上传（ADR 0029 上传时机第三级，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的…, _make_act_pair(), act 边界安全点提前上传单测（ADR 0029 上传时机第三级，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验提前上传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings() (+4 more)

### Community 124 - "cli/tests/conftest.py"
Cohesion: 0.40
Nodes (5): _presentation_is_environment_independent(), fixture, cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。, _stub_engine_capabilities()

### Community 125 - ".add_arguments"
Cohesion: 0.19
Nodes (9): ArgumentParser, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三种取值，**无隐式默认**（ADR 0037 决策 6； 三者与…, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`… (+1 more)

### Community 126 - "Artifact Upload & Shutdown"
Cohesion: 0.17
Nodes (13): 优雅终止（schedule 只下 handle.stop 逻辑指令）, ReportRef {kind, ref, label}, ADR 0029: engine artifact → S3（注入驱动）, 删本地（以上传成功确认为前提、整目录删）, 上传必须套超时（退出时间有界）, 上传时机四级（实时 ref / scope 末 flush / act 边界 / scenario 边界）, uploader 组件（from_env/to_report_ref/flush_and_cleanup）, ACT_TIMEOUT_S 不压（拒候选解法 B） (+5 more)

### Community 127 - "check_version_skew"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 128 - ".inspect"
Cohesion: 0.33
Nodes (4): 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。, _tail()

### Community 129 - "digest_for_repo"
Cohesion: 0.40
Nodes (5): digest_for_repo(), 从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。…, 基础镜像同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def**…, test_digest_none_when_repo_absent_or_empty(), test_digest_picked_by_repo_not_first_entry()

### Community 130 - "aws"
Cohesion: 0.40
Nodes (5): aws(), _aws_env(), _presentation_is_environment_independent(), fixture, 人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。

### Community 132 - "Skill Deploy Token Checks"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。 (+3 more)

### Community 133 - "Advancer IAM Permissions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, Template, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表只有 **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——… (+4 more)

### Community 134 - "确定性 step 的写法：从「能注册」到「稳、可诊断、可维护」"
Cohesion: 0.20
Nodes (9): 1 先判该不该写成确定性 step, 2 一条 step 的四个部分, 3 等待与判定：四条规则, 4 组织：判定逻辑与注册分离, 5 本地零费用核对与单测, 6 改一条已在用的 step, 7 症状速查, 8 修完怎么汇报 (+1 more)

### Community 135 - "_error_text"
Cohesion: 0.22
Nodes (9): BaseException, _error_text(), _is_transient_client_error(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…, 隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。, test_error_text_prefers_sdk_message_and_is_single_line() (+1 more)

### Community 136 - "test_tunnel.py"
Cohesion: 0.18
Nodes (15): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, TunnelInfo, _job_with(), Job (+7 more)

### Community 137 - "Skill Contract Rendering"
Cohesion: 0.26
Nodes (11): _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 138 - "User-Facing Text Guardrails"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 139 - "0047. CLI 人读输出：清单用表格、层级用树、状态上语义颜色，统一由 rich 渲染"
Cohesion: 0.33
Nodes (5): 0047. CLI 人读输出：清单用表格、层级用树、状态上语义颜色，统一由 rich 渲染, 不做 / 延后, 决策, 影响面, 背景与问题

### Community 140 - "AWS Client Stubs"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 141 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 142 - "Status"
Cohesion: 0.04
Nodes (42): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, has_pointers(), _iter_arguments() (+34 more)

### Community 144 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 145 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 146 - "tunnel.py"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 147 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 149 - "Schedule & Retry ADRs"
Cohesion: 0.25
Nodes (9): ADR 0025: plan 模块 — .feature → job 列表, ADR 0026: schedule 模块 — 并发调度/失败隔离/优雅终止, _heartbeat_wrap（静默 worker 超时兜底）, schedule(run_meta, engines, sink, opts) -> RunResult, 三级归约（status + 原生量成本 + 墙钟）, ADR 0028: 网络/SSL 瞬时错误两层重试, EX_WORKER_NETWORK = 80（带外退出码信号）, network_error 分类（白名单具体瞬时类型） (+1 more)

### Community 150 - "Detached Run Orchestration"
Cohesion: 0.22
Nodes (9): ScheduleOpts（并发/隔离/grace/重试/心跳旋钮）, CAS(pending→running) 控严格并发, detached 标记（Stream filter + handler 分流）, HWM + 状态机单调条件写, job timeout（definition 载体 + 三路 enforce）, kicker Lambda（冷启动 + 接力 kickoff）, project / plan_next（纯归约 + 纯决策）, submit / status --wait 命令形态 (+1 more)

### Community 151 - "Report Aggregation & Status"
Cohesion: 0.28
Nodes (9): ADR 0027: RunReport 跨引擎归集索引, scope 内 step 级短路, ADR 0030: 实时写存储接缝, ADR 0031: job 生命周期态 skipped/aborted + severity, _aggregate 入口过滤 _NON_VERDICT, severity 数值序, Status enum 扩展（skipped/aborted/pending/running）, step_skipped 事件 + StepResult.shortcircuited (+1 more)

### Community 152 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 153 - "test_s3_report_store.py"
Cohesion: 0.31
Nodes (10): S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index(), test_index_html_links_and_summary(), test_index_html_taints_shortcircuited_step(), test_manifest_shape() (+2 more)

### Community 154 - "exit_observer.py"
Cohesion: 0.27
Nodes (9): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+1 more)

### Community 155 - "Path"
Cohesion: 0.13
Nodes (24): local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。…, _submit_local(), 终态真源不漂移（ADR 0031 决定一·补末条）：三处消费方全引…, test_terminal_status_consumers_use_core_single_source(), Path, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, write_tunnel_file(), collect_outputs() (+16 more)

### Community 156 - "ValueError"
Cohesion: 0.27
Nodes (10): test_value_error_not_transient(), main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, 文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。, render(), section(), skill_install_tag_problems(), 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值… (+2 more)

### Community 157 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 158 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性 step 脚手架（ADR 0020/0022）—— **本包内建**的示范 step，随 worker 发行。 用途：少数"必须精确、不容 AI…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言…, url_matches()

### Community 159 - "textui.py"
Cohesion: 0.12
Nodes (28): _as_text(), _console(), output_width(), plain(), 人读输出的呈现件（ADR 0047）：表格、树、语义颜色，cli 与 deploy provider 两个前端包共用。 - 表格给「多行同结构」的清单，树给…, 层级结构 → 带引导线的多行文本（末尾不带换行）。不折行：长的地址、原因、推理文本保持一行、由终端自行软换行，…, `NO_COLOR` 为非空值或 `TERM=dumb` → 不上色；`FORCE_COLOR` 为非空值 → 上色（如 `| less…, 表格用的宽度：标准输出是终端时取其实际列数（取不到时 80；窄终端也按实际列数，让 rich 自行收窄），否则不折行。 (+20 more)

### Community 161 - "._pump"
Cohesion: 0.50
Nodes (3): Event, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, Timer

### Community 163 - "Doc Rules Checker"
Cohesion: 0.54
Nodes (7): _changed_lines(), _git(), main(), Path, 工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。, _staged_targets(), _working_tree_targets()

### Community 164 - "list_registry"
Cohesion: 0.50
Nodes (4): list_registry(), 注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。, test_list_registry_reflects_registrations(), test_loads_recursively_in_sorted_order_and_registers()

### Community 165 - "_await_engine"
Cohesion: 0.60
Nodes (5): _await_engine(), _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 166 - "redact.mts"
Cohesion: 0.40
Nodes (3): RFC-3986, MASK, ADR-0035

### Community 167 - "_fixture"
Cohesion: 0.03
Nodes (83): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。 (+75 more)

### Community 169 - "Report Store & Manifest"
Cohesion: 0.40
Nodes (6): href 相对化（local 相对 / cloud 恒等 ref）, manifest.json（薄信封 + 扁平 report_index）, ReportStore.write(run_id, result), run_id（归集主键，生成权在组合根）, commit point 写序（数据面先、控制面后）, ADR 0034: 无状态批量运行（CQRS + reconciler）

### Community 170 - "DynamoDB Storage Design"
Cohesion: 0.33
Nodes (6): DDB 单表 + META/STATE 两 item, StepArgument S3 offload（content_ref/rows_ref）, RunState.jobs 改 Map<scope_id>, ADR 0033: iac_aws_backend CDK + 组合根接 FargateEngine, events 表 TTL（expires_at，7 天）, IAM 最小权限（动作 × 资源两维收窄）

### Community 171 - "_patch_skew"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 相同的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 172 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 173 - "release.yml 发布链"
Cohesion: 0.38
Nodes (6): 版本真源 (single version source), GitHub Release 正文固定块, wait_for_index.sh script, ci.yml 工作流, CI 与发布链说明, release.yml 发布链

### Community 174 - "03-midscene-grounding.ts"
Cohesion: 0.33
Nodes (5): ADR-0010, BASE_URL, MODEL_CONFIG, REGION, ADR-0033

### Community 175 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 177 - "test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine"
Cohesion: 0.15
Nodes (8): CountingEcs, boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。, ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。, 重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…, `list-workers` 的全量枚举（待清理对账用的映射集 + 各引擎当前版本的 variant）只执行一次、两个引擎共用。…, Spy, test_list_workers_enumerates_ssm_once_for_all_engines(), test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine()

### Community 178 - "test_release_notes.py"
Cohesion: 0.21
Nodes (14): _check(), _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」（ADR 0045…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, 真 README / user guide 对照真值集：skill 安装命令钉的 tag 等于 CHANGELOG 顶部已发行版本（发版前两处同一次改）。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag() (+6 more)

### Community 179 - "Plan Module Seams"
Cohesion: 0.40
Nodes (5): id 派生（scenarioId/scopeId 不透明、不 normalize）, parse seam（藏 gherkin-official）, plan(features, config, select) -> Job[], scope seam（tag 分组 + engine/timeout 校验）, select 谓词（scenario 筛选）

### Community 180 - "Run Persistence & Preflight"
Cohesion: 0.40
Nodes (5): on_job_complete / on_event 回调注入点, Store.preflight() 探活, RunPersistence 应用服务（persist.py）, 两层命名（--prefix 批量默认 + 单资源覆盖）, preflight fail-fast（点名 prefix）

### Community 181 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 182 - "test_local_result_store_atomic.py"
Cohesion: 0.38
Nodes (6): _big_job_result(), LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 运行到一半时读…, ~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。, 判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。, test_concurrent_reader_never_sees_torn_job_result(), test_job_result_file_stays_readable_by_others()

### Community 183 - "Worker Subnet Selection"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 184 - "test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 185 - "Package Files Metadata"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 186 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 187 - "ADR 0035 经隧道测试本地应用"
Cohesion: 0.38
Nodes (7): ADR 0011 AgentCore 浏览器层：默认 vs 自建, ADR 0034 无状态批量运行的事件链, --expose-local 与 job 组装期 URL 前缀替换, ADR 0035 经隧道测试本地应用, 隧道生命周期按宿主分三形态, TunnelProvider 可插拔口子（首实现 ngrok）, TTL 按 definition 计算（compute_watch_ttl_s）

### Community 188 - "Worker Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 189 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素是 (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 190 - "05-negative-assertions.ts"
Cohesion: 0.33
Nodes (5): BASE_URL, Check, MODEL_CONFIG, REGION, ADR-0033

### Community 192 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 193 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 201 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 203 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 204 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 205 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 207 - "list_workers"
Cohesion: 0.20
Nodes (10): _cell(), list_workers(), _pushed_at_human(), 推送时间的人读形态：`2026-09-29T07:09:14.961520+00:00` → `2026-09-29 07:09`（换算到 UTC、到分钟）。…, 定宽列（**按显示宽度补，不按字符数**）：中文表头字符占两列，用 `f"{s:<28}"` 会让整张表歪掉。…, 按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。…, 读戳失败（无凭证/无权限）→ 退出码 2 + 一句人话。 `compose.read_backend_version`…, 建不出 client（这里用不存在的 profile 名）→ 退出码 2 + 一句人话，不吐 botocore 堆栈。… (+2 more)

### Community 226 - "runStep"
Cohesion: 0.50
Nodes (4): cumulativeTokens(), isTransientNetwork(), runStep(), stepCost()

### Community 229 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 231 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 236 - "main"
Cohesion: 0.20
Nodes (6): drainArtifactQueue(), log(), main(), runScenario(), shutdownSequence(), step()

### Community 243 - "stop_tunnel"
Cohesion: 0.40
Nodes (5): 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 244 - "S3StepArgumentOffloader"
Cohesion: 0.11
Nodes (17): 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore…, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, S3StepArgumentOffloader, ConflictException, exceptions (+9 more)

### Community 268 - "_Worker"
Cohesion: 0.17
Nodes (10): _heartbeat_wrap(), Event, Job, 单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。, 运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…, _Worker (+2 more)

### Community 269 - "04-planning-probe.ts"
Cohesion: 0.50
Nodes (3): BASE_URL, main(), ADR-0033

### Community 270 - "CommandSpan"
Cohesion: 0.67
Nodes (3): CommandSpan, NamedTuple, 一个 `gherkai …` 代码跨的拆解结果。 `words` = `gherkai` 之后、第一个 flag…

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
- **329 isolated node(s):** `背景与问题`, `决策`, `影响面`, `不做 / 延后`, `LoadUserStepsDeps` (+324 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **103 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

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