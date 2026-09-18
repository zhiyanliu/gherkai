# Graph Report - yaozhou  (2026-09-18)

## Corpus Check
- 316 files · ~524,520 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5356 nodes · 11782 edges · 308 communities (211 shown, 97 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 747 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `09c81a53`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Job
- JobResult
- test_workers.py
- test_backend_cloud.py
- workers.py
- test_main.py
- _fixture
- RunResult
- test_lifecycle_states.py
- evidence.py
- test_container.py
- test_compose.py
- _run_step
- test_schedule.py
- test_stack.py
- test_deploy_cmd.py
- DdbEventLog
- _Nova
- _FakeEcs
- test_argument.py
- ensure_workflow_definition
- ADR 0016 执行架构 / 组合根注入
- LocalReportStore
- test_tunnel_cli.py
- test_reconcile.py
- _fake_locator
- ADR 0019 feature tag 的 scope 与引擎路由
- test_provider.py
- test_interrupt_model.py
- test_plan.py
- CONTRIBUTING.md
- test_worker_variant.py
- _doc_rules.py
- test_conditional_writes.py
- RunResult（事件流归约终值）
- WorkerNotFoundError
- StepDone
- render.py
- JobState
- test_user_steps.py
- main
- BackendStack
- run_scope.py
- _explain_run
- compose.py
- _is_transient_network
- deterministic.mts
- deterministic.py
- Artifact Upload Tests
- Midscene Worker 开发笔记
- evidence.mts
- ._run_cdk
- test_cloud_reconcile.py
- 常见问题
- main
- _FakeEcsClient
- .bootstrap
- test_fargate_engine.py
- Artifact Uploader (Python)
- _RecUploader
- build_diagrams.mjs
- _stream_record
- test_subprocess_engine.py
- Nova worker flag-only 信号 handler
- atomic_write_json
- test_event_sink.py
- event-sink.mts
- build_engines
- reconciler.py
- test_lambda_asset.py
- deploy.py
- FargateEngine
- SKILL.md 住 cli/gherkai_cli/skills/gherkai/、随 wheel 发行
- test_detached_launcher.py
- require_boto3
- report_store/local.py
- test_project.py
- TypeScript Config
- _Recorder
- test_tunnel_host.py
- _StubEcs
- Eval Harness Runner
- DynamoDB 作 events-out 传输（共享表 + Query 轮询）
- JobSource
- Skill Stage Materialization
- Skill Install Command
- test_cli_json_contract.py
- ADR 0033 IaC 资源清单与命名契约
- _read_events
- _FakeProc
- map_origin_in_jobs
- RunPersistence
- _progress
- ADR 0037 分发与打包
- Status
- ArtifactUploader
- sigv4Fetch
- runtime 包 contributor 文档
- dependencies
- _StampSsm
- test_tunnel.py
- evidence.test.mts
- test_package_readmes.py
- _await_engine
- test_finished_run_gate_keys_on_the_committed_run_status_only
- _release_cmp
- _AbsentEngine
- events_wallclock.py
- _render_status
- _seed_worker_ssm
- test_skill.py
- _CdkWritingContext
- _tagged_feature
- build_fargate_engines
- 变更记录
- query_capabilities
- _ClientError
- gherkai_runtime/__init__.py
- _FakeSchedulerClient
- Midscene Worker Package Manifest
- Provider
- run-scope.test.mts
- Distribution Metadata Checks
- _argv
- gherkai_cli/__main__.py
- ._guard_vpc_spec
- 无状态 reconciler（CQRS 投影 + 推进）
- Skill Deploy Token Guardrail
- 03-midscene-grounding.ts
- render_skill_contract.py
- test_user_facing_messages.py
- release.yml — 发布全链工作流
- _MissingThenStoppedEcs
- _patch_skew
- gherkai_runtime/names.py
- @gherkai/worker-midscene (README)
- job-source.mts
- _print_artifact_lines
- artifact-upload.test.mts
- Worker Signal Interrupt Tests
- _cmd_submit
- 文档健康度复盘（全部项目文档）— 任务说明
- test_cloud_integration.py
- ECS Task Timing Capture
- exit_observer.py
- user-steps.mts
- 编写确定性 step
- Graph Refresh Script
- is_placeholder
- 部署与维护云端后端
- test_local_result_store_atomic.py
- Contract Key Documentation Check
- argument.mts
- 排错
- SqliteEventLog
- 权威信息源（自查用）
- Echo Test Worker
- Cloud Test Infrastructure Check
- _Worker
- _FakeS3
- _engine_with_fake_ecs
- CountingEcs
- user-steps.test.mts
- TypeScript Dev Dependencies
- Skill Frontmatter Validation
- 01-model-sigv4.ts
- deterministic.steps.mts
- bin.mts
- openai
- Worker Image Version Mappings
- user-guide/README.md
- Event Reduction & Short-Circuit
- files
- Repository Metadata
- Worker Artifact Upload
- Upload Call Recorder
- Skill Evaluation Design
- NPM Scripts
- AgentCore CDP Spike
- Background Upload Queue
- 决策
- 执行与推进模型导览：run / submit × local / cloud
- sync-derived.sh
- 开发者指南
- Adapters Package
- 代码健康度复盘（全部生产代码）— 任务说明
- CONTENT_TYPES
- index.mts
- TSX Dependency
- Upload Queue Drain
- Uploader Enabled Check
- Uploader Config Fail-Loud
- No-op Local Uploader
- Index Wait Script
- Workspace Root Package
- 配置：环境变量与通用选项
- Planning Model Decision
- Exit Code Layering
- Preflight Ordering
- Read Consistency Strategy
- GherkAI Core Module
- AWS Deployment Package
- GherkAI Runtime
- NovaAct Worker Service
- resolve-hook.mts
- error-text.mts
- event-sink.test.mts
- RevisionInfo
- ValueError
- agentcore-sigv4.test.mts
- job-source.test.mts
- _advancer_stmts
- Spy
- .preflight
- test_s3_report_store.py
- cli.py
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- test_lambda_handlers.py
- test_release_notes.py
- parametrize
- Path
- _stopped_detail
- ._pump
- cloud_env
- test_final_drain_paginates_across_last_evaluated_key
- gherkai CLI 的 `--json` 字段契约
- test_raise_for_worker_exit_maps_codes_with_fargate_label
- test_final_drain_logs_real_holes_under_consistent_read
- 判定的计算路径：从单次投票到退出码
- test_await_exit_code_transient_missing_then_stopped_reads_code
- test_provider_module_does_not_import_aws_cdk
- test_user_docs.py
- Exception
- test_evidence.py
- _presend_act_siblings
- 云端后端由哪些载体组成：一次改动要传播到哪几处才生效
- 一条确定性 step 的生命周期：从写下正则到云端命中
- @aws-sdk/client-dynamodb
- _FakeTable
- 架构总览：五层结构、一次 run 的生命周期、包与发行物
- 产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）
- @aws-sdk/client-bedrock-agentcore
- release_body_footer.md
- test_error_step_also_enqueues_only_after_emit
- 推进器 (advancer)
- /code-health-review 命令入口
- /doc-health-review 命令入口
- no-artifacts.test.mts
- _FakeResult
- ._resolve_target
- 编写 .feature
- ADR-0008
- ADR-0019
- ADR-0026
- ADR-0027
- ADR-0035
- DEFAULT_MODEL
- test_worker_subnets_single_source_across_ssm_and_lambda_env
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
- _submit_local
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- BROWSER_CLOSE_BUDGET_MS
- CONNECT_BACKOFF_MS
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
- ADR-0036
- ADR-0037
- ADR-0042
- ADR-0044
- QUEUE_DRAIN_EXIT_MS
- Scenario
- ShutdownDeps
- Step
- STOP_SESSION_BUDGET_MS
- _explain_emit
- 跑测试与看结果
- 开始使用
- ArgumentParser
- _FakeSink
- 测本机或内网里的被测应用
- ArtifactUploader 组件（from_env / to_report_ref / flush）
- RuntimeError

## God Nodes (most connected - your core abstractions)
1. `main()` - 214 edges
2. `Job` - 130 edges
3. `RunState` - 122 edges
4. `RunMeta` - 114 edges
5. `Status` - 100 edges
6. `JobState` - 96 edges
7. `Provider` - 93 edges
8. `JobResult` - 81 edges
9. `Scenario` - 69 edges
10. `Step` - 68 edges

## Surprising Connections (you probably didn't know these)
- `README.md — 仓库首页（使用者向）` --conceptually_related_to--> `跑法权限梯 (Execution tiers)`  [INFERRED]
  README.md → CONTEXT.md
- `gherkai agent SKILL.md` --references--> `ADR 0001 范围限定英文 UI`  [AMBIGUOUS]
  cli/gherkai_cli/skills/gherkai/SKILL.md → docs/adr/0001-scope-limited-to-english-ui.md
- `--expose-local 隧道` --conceptually_related_to--> `ADR 0035 经隧道测本机应用`  [INFERRED]
  cli/gherkai_cli/skills/gherkai/SKILL.md → docs/adr/0035-local-app-testing-via-tunnel.md
- `_status_cloud()` --calls--> `DynamoDBRunStore`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/run_store/ddb.py
- `_is_detached()` --calls--> `DynamoDBRunStore`  [INFERRED]
  deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py → core/gherkai_core/adapters/run_store/ddb.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **双引擎可对标基准与 AI 断言可靠性** — docs_adr_0010_spike_as_apples_to_apples_benchmark, docs_adr_0001_scope_limited_to_english_ui, docs_adr_0014_ai_first_assertions, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0027_runreport_aggregation_index [EXTRACTED 0.80]
- **AWS 硬约束下的模型/鉴权选型链** — docs_adr_0009_maximize_aws_hard_constraint, docs_adr_0002_midscene_not_driven_by_gpt55, docs_adr_0003_midscene_grounding_qwen3vl_bedrock, docs_adr_0004_novaact_iam_auth_via_workflow, docs_adr_0008_midscene_bedrock_auth_sigv4_selfsign, docs_adr_0012_planning_shares_qwen3vl_no_text_planner [EXTRACTED 0.85]
- **run 级执行参数随 definition 走的载体惯例（omit-when-None、core 只搬运）** — docs_adr_0035_local_app_testing_via_tunnel_extra_http_headers, docs_adr_0037_distribution_and_packaging_steps_dir, docs_adr_0038_worker_image_delivery_variant, docs_adr_0034_detached_batch_reconciler_job_timeout [EXTRACTED 0.85]
- **三条去污染硬规则与隔离面护栏** — docs_adr_0043_agent_skill_for_driving_gherkai_decontamination_rules, docs_adr_0043_agent_skill_for_driving_gherkai_isolation_surface, docs_adr_0043_agent_skill_for_driving_gherkai_materialize_py, docs_adr_0043_agent_skill_for_driving_gherkai_summarize_runs_py, docs_adr_0043_agent_skill_for_driving_gherkai_eval_results [EXTRACTED 0.85]
- **执行栈：窄腰核心 + ports + 薄 worker + 推进器** — context_core_narrow_waist, context_ports_layer, context_engine_port, context_thin_worker, context_advancer, context_deterministic_step_registry [EXTRACTED 0.85]
- **Gherkin Tag Configuration System (scope/engine/timeout → plan/schedule)** — docs_adr_0019_feature_tags_scope_and_engine_scope_tag, docs_adr_0019_feature_tags_scope_and_engine_engine_tag, docs_adr_0019_feature_tags_scope_and_engine_timeout_tag, docs_adr_0025_plan_module_feature_to_jobs, docs_adr_0026_schedule_module [EXTRACTED 0.85]
- **优雅终止分层：schedule 下逻辑停 → handle → adapter 机制 → worker 会话清理** — docs_adr_0026_schedule_module_graceful_termination, docs_adr_0026_schedule_module_workerhandle, docs_adr_0026_schedule_module_job_timeout, docs_adr_0026_schedule_module_fail_fast, docs_adr_0028_transient_network_ssl_resilience_session_leak_protection [EXTRACTED 0.85]
- **Midscene → Bedrock SigV4 自签鉴权链路** — engines_midscene_lib_agentcore_sigv4, engines_midscene_spikes_sigv4_fetch, engines_midscene_spikes_create_openai_client, engines_midscene_worker_run_scope, adr_0008, adr_0003 [EXTRACTED 0.85]
- **plan 流水线：feature → parse → scope → Job** — docs_adr_0025_plan_module_feature_to_jobs_plan, docs_adr_0025_plan_module_feature_to_jobs_parse, docs_adr_0025_plan_module_feature_to_jobs_scope, docs_adr_0025_plan_module_feature_to_jobs_job, docs_adr_0025_plan_module_feature_to_jobs_id_derivation [EXTRACTED 0.85]
- **两引擎共有的使用方 steps 加载与 fail-loud 契约** — engines_midscene_worker_user_steps, engines_novaact_gherkai_worker_novaact_user_steps, concept_fail_loud_steps_loading, concept_deterministic_step, adr_0037 [EXTRACTED 0.85]
- **面向 AI agent 的三层：命令面能力 → 机读证据 → 随包发行的 skill 教材** — docs_adr_0041_agent_facing_cli_affordances, docs_adr_0042_step_evidence_and_explain, docs_adr_0043_agent_skill_for_driving_gherkai, docs_adr_0041_agent_facing_cli_affordances_json_contract, docs_adr_0043_agent_skill_for_driving_gherkai_transform_copy [EXTRACTED 0.90]
- **AI 断言纪律：对称布尔投票 + 确定性逃生舱 + 定位边界** — docs_adr_0014_ai_first_assertions, docs_adr_0014_ai_first_assertions_assertion_votes, docs_adr_0015_v1_positioning_smoke_not_regression, docs_adr_0015_v1_positioning_smoke_not_regression_deterministic_escape_hatch, docs_adr_0015_v1_positioning_smoke_not_regression_uncertainty_a_b [EXTRACTED 0.90]
- **产物指针链：worker 报 ref → 不透明搬运 → ReportStore 归集 → index.html 可点链接** — docs_adr_0029_engine_artifacts_to_s3_worker_upload, docs_adr_0027_runreport_aggregation_index_reportref, docs_adr_0027_runreport_aggregation_index_opaque_transport_rule, docs_adr_0027_runreport_aggregation_index_reportstore, docs_adr_0027_runreport_aggregation_index_make_href, docs_adr_0027_runreport_aggregation_index_index_html [EXTRACTED 0.90]
- **Core↔Worker Execution Waist (parse → schedule → worker events → RunReport)** — docs_adr_0024_worker_core_protocol, docs_adr_0025_plan_module_feature_to_jobs, docs_adr_0026_schedule_module, docs_adr_0027_runreport_aggregation_index, docs_adr_0022_bdd_runner_retired_core_parses_thin_worker_b1, docs_adr_0016_execution_architecture_core_lib_run_model [EXTRACTED 0.90]
- **无状态跑批的四个关键机制共同保证并发安全与收敛** — docs_adr_0034_detached_batch_reconciler_task_exited, docs_adr_0034_detached_batch_reconciler_exit_observer, docs_adr_0034_detached_batch_reconciler_hwm, docs_adr_0034_detached_batch_reconciler_cas, docs_adr_0034_detached_batch_reconciler_reconciler [EXTRACTED 0.90]
- **events-out 传输选型（DDB 选定 vs 三方案被拒）** — docs_adr_0024_worker_core_protocol_ddb_events_transport, docs_adr_0024_worker_core_protocol_rejected_sqs_fifo, docs_adr_0024_worker_core_protocol_rejected_msk, docs_adr_0024_worker_core_protocol_rejected_ddb_streams [EXTRACTED 0.90]
- **两臂评测一轮的资产与顺序** — docs_adr_0043_agent_skill_for_driving_gherkai_materialize_py, docs_adr_0043_agent_skill_for_driving_gherkai_run_evals_py, docs_adr_0043_agent_skill_for_driving_gherkai_summarize_runs_py, docs_adr_0043_agent_skill_for_driving_gherkai_grader_prompt, docs_adr_0043_agent_skill_for_driving_gherkai_evals_json, docs_adr_0043_agent_skill_for_driving_gherkai_fixtures [EXTRACTED 0.90]
- **发布全链：一个 git tag 派生全部交付物版本** — github_workflows_release_build, github_workflows_release_pypi, github_workflows_release_npm, github_workflows_release_images, github_workflows_release_gh_release, context_single_version_knob [EXTRACTED 0.90]
- **schedule 三级归约（status + 原生量成本 + 墙钟时长）** — docs_adr_0026_schedule_module_status_reduction, docs_adr_0026_schedule_module_cost_reduction, docs_adr_0026_schedule_module_duration_reduction, docs_adr_0026_schedule_module_runresult, docs_adr_0026_schedule_module_step_skipped_reduction [EXTRACTED 0.90]
- **终止契约三层（逻辑层 / 机制层 / worker 层）** — docs_adr_0024_worker_core_protocol_termination_contract, docs_adr_0024_worker_core_protocol_schedule_stop_layer, docs_adr_0024_worker_core_protocol_worker_handle_subprocess, docs_adr_0024_worker_core_protocol_fargate_worker_handle_stop, docs_adr_0024_worker_core_protocol_nova_flag_only_handler, docs_adr_0024_worker_core_protocol_midscene_cleanup_handler [EXTRACTED 0.90]

## Communities (308 total, 97 thin omitted)

### Community 0 - "Job"
Cohesion: 0.05
Nodes (82): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), _explain_job(), cloud 档「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要跑得通， 否则落回 local…, 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本/JSON 同律）；命中的 scope 的…, test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(), test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), test_render_run_state_lists_jobs_and_session_lineage() (+74 more)

### Community 1 - "JobResult"
Cohesion: 0.06
Nodes (43): 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。 (+35 more)

### Community 2 - "test_workers.py"
Cohesion: 0.06
Nodes (92): aws(), _cleanup(), FakeContainer, _mapping(), _out(), _push(), datetime, `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。… (+84 more)

### Community 3 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就退 2（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 4 - "workers.py"
Cohesion: 0.04
Nodes (95): Aws, _cell(), cleanup_pass(), CleanupOutcome, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+87 more)

### Community 5 - "test_main.py"
Cohesion: 0.04
Nodes (92): _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, steps 文件加载失败（worker 自述非零退出）→ plan 退 2、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。, run / submit：跑前先问一次能力自述，worker 非零退出 → 起任何 job 之前退 2（不进 job 级 error）。… (+84 more)

### Community 6 - "_fixture"
Cohesion: 0.06
Nodes (35): cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的跑前检查、`list-…, _stub_engine_capabilities(), aws(), _fake_aws_creds(), fargate(), 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表…, 连真 DDB/S3 的句柄（真表/桶名读环境变量），供集成测试。**没设环境变量就 skip**（不误连、不报错）。 需你先建好真表 + 真桶（见… (+27 more)

### Community 7 - "RunResult"
Cohesion: 0.11
Nodes (30): RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…, render_text(), _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, cloud 档：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import… (+22 more)

### Community 8 - "test_lifecycle_states.py"
Cohesion: 0.06
Nodes (29): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。 (+21 more)

### Community 9 - "evidence.py"
Cohesion: 0.08
Nodes (39): Any, act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Path (+31 more)

### Community 10 - "test_container.py"
Cohesion: 0.05
Nodes (54): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+46 more)

### Community 11 - "test_compose.py"
Cohesion: 0.04
Nodes (68): check_version_skew(), 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, resolve_cloud_target(), resolve_network() (+60 more)

### Community 12 - "_run_step"
Cohesion: 0.10
Nodes (43): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+35 more)

### Community 13 - "test_schedule.py"
Cohesion: 0.15
Nodes (69): ScenarioDone, ScenarioStarted, 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver (+61 more)

### Community 14 - "test_stack.py"
Cohesion: 0.06
Nodes (63): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。 (+55 more)

### Community 15 - "test_deploy_cmd.py"
Cohesion: 0.06
Nodes (48): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 `__main__`（argparse 皮）+ `render`（表层渲染）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+40 more)

### Community 16 - "DdbEventLog"
Cohesion: 0.08
Nodes (29): DdbEventLog, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, events_pk(), events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。, _meta() (+21 more)

### Community 17 - "_Nova"
Cohesion: 0.19
Nodes (21): ArtifactUploader, _get_uploader(), _done(), _Nova, parametrize, Path, fake nova：act/act_get 回带 trajectory 路径的结果；act_raises 时抛（模拟 act 中途失败）。, evidence.json 的即时上传失败也只丢 ref（to_report_ref 的「失败即抛」契约不动，兜法在调用方）。 只让… (+13 more)

### Community 18 - "_FakeEcs"
Cohesion: 0.10
Nodes (16): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` = 在跑的 task；`tasks` = 带状态的…, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…, task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录… (+8 more)

### Community 19 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 20 - "ensure_workflow_definition"
Cohesion: 0.06
Nodes (44): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+36 more)

### Community 21 - "ADR 0016 执行架构 / 组合根注入"
Cohesion: 0.10
Nodes (52): ADR 0016 执行架构 / 组合根注入, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单旋钮）, 核心库是窄腰，CLI/WebUI 是可替换薄前端, Ports & Adapters + 组合根注入, Run 数据模型（Step/Scenario/Feature/Scope/Job/Run）, 三层切分：definition / 控制面运行态 / 数据面判定, ADR 0017: 云执行选 Fargate, ADR 0024 worker↔core 协议 (+44 more)

### Community 22 - "LocalReportStore"
Cohesion: 0.18
Nodes (36): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077… (+28 more)

### Community 23 - "test_tunnel_cli.py"
Cohesion: 0.09
Nodes (39): _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。 (+31 more)

### Community 24 - "test_reconcile.py"
Cohesion: 0.09
Nodes (38): finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher, _job() (+30 more)

### Community 25 - "_fake_locator"
Cohesion: 0.07
Nodes (42): _cloud_backend_ok(), _doctor_cloud_json(), _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。, 两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。 跳过而非失败：下限是 worker… (+34 more)

### Community 26 - "ADR 0019 feature tag 的 scope 与引擎路由"
Cohesion: 0.09
Nodes (38): 穿刺 / Spike, 穿刺脚本落点（by-engine）, ADR 0005 单一共享 .feature 文件, ADR 0006: 形态 A 两子工程、无编排器, ADR 0010: spike 作同题基准, ADR 0013 跨引擎共享边界, 跨引擎共享止于 features/（+ 使用方 steps/ 约定面）, ADR 0014 AI 优先断言与投票 (+30 more)

### Community 27 - "test_provider.py"
Cohesion: 0.07
Nodes (54): _parse(), `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, 子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。, `--prefix` 在子动词**前**给也必须留住——子 parser 在新 namespace 里解析后整体覆盖回父层，…, 留口子：退 2 并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。, CLI 皮没交版本 → 本包自报 dist 版本（`==` 同版本 pin 成同一个，不引入第二个真源）。, 走**真 parser**、按真实接线顺序拼（皮先声明命令面 flag，provider 再贴自己的旋钮）——不用 SimpleNamespace 手捏…, 凭证/权限/网络故障 → 退 2 + 一句话（对用户是「先修凭证」，与 Node 缺失同一档），不抛 traceback。 (+46 more)

### Community 28 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (33): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True=中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True=退避中收到停止信号（应停止重连）。 用…, captured() (+25 more)

### Community 29 - "test_plan.py"
Cohesion: 0.06
Nodes (72): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig, Job (+64 more)

### Community 30 - "CONTRIBUTING.md"
Cohesion: 0.07
Nodes (36): CLAUDE.md — 项目约定, 文档纪律（ADR / CONTEXT / journey / guides 分层）, graphify 知识图使用约定, 绿 ≠ 对：识别结论的证据边界, CONTEXT.md — 领域术语表, agent skill (gherkai skill), AgentCore 浏览器会话, 确定性断言 vs AI 断言 (+28 more)

### Community 31 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (46): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。 值 =…, worker_image_key(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。 (+38 more)

### Community 32 - "_doc_rules.py"
Cohesion: 0.12
Nodes (20): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, Path, 使用者面 markdown 的共享规则与扫描器：多处护栏共用的**单一事实源**。…, `--scope=<id>，` → `--scope`；不是 flag 则 None。`--` 单独出现（参数分隔符）不算 flag。 (+12 more)

### Community 33 - "test_conditional_writes.py"
Cohesion: 0.09
Nodes (42): _initial(), _meta(), RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+34 more)

### Community 34 - "RunResult（事件流归约终值）"
Cohesion: 0.06
Nodes (43): 原生量成本归约（tokens / time_worked_s）, 墙钟时长归约（duration_ms 四级）, EngineResolver（按 job.engine 解析 Engine）, failFast 与失败隔离, 优雅终止（schedule 只下逻辑「停」指令）, _heartbeat_wrap（静默 worker 存活心跳）, Job.timeout_s 超时兜底, max_concurrency（默认 4） (+35 more)

### Community 35 - "WorkerNotFoundError"
Cohesion: 0.08
Nodes (24): _ask_worker(), build_local_stores(), local_artifact_locations(), match_deterministic(), prune_empty_dirs(), Path, RuntimeError, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。… (+16 more)

### Community 36 - "StepDone"
Cohesion: 0.03
Nodes (91): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, FargateWorkerHandle, NamedTuple, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024… (+83 more)

### Community 37 - "render.py"
Cohesion: 0.10
Nodes (29): _act_lines(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), _ms(), _one_line() (+21 more)

### Community 38 - "JobState"
Cohesion: 0.04
Nodes (81): _job_state_from_item(), _job_state_to_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, JobState → DDB Map entry（字段集同 serialize；session_id/claimed_at 用 omit-when-…, RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐…, run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。 **写序… (+73 more)

### Community 39 - "test_user_steps.py"
Cohesion: 0.07
Nodes (49): steps 加载 fail-loud 不静默降级, src/worker/user-steps.mts — 使用方 steps 加载, _ensure_ns_package(), _is_step_file(), load_user_steps(), _module_name(), Exception, Path (+41 more)

### Community 40 - "main"
Cohesion: 0.06
Nodes (48): main(), _det_feature(), 对照：定位链 miss（运行时没装）plan 仍降级退 0（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 退 2「读 feature 失败」，不是 IsADirectoryError traceback（退码语义 ADR…, cloud 档第一道闸是版本 skew（先于任何云端读）：block → 退 2，且根本没去装 store。, plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。, 冲突预检（真跑将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。, 标注 best-effort：引擎环境未装/查询失败 → 无标注 + stderr 警告，plan 核心输出不受影响。 (+40 more)

### Community 41 - "BackendStack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 42 - "run_scope.py"
Cohesion: 0.09
Nodes (28): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _capabilities(), _collect_traj(), _cost_from_result(), _drain_evidence_uploads() (+20 more)

### Community 43 - "_explain_run"
Cohesion: 0.11
Nodes (28): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三档，可重复且彼此为或。, --step 单给退 2（步号没有归属）；命中的 scenario 都没有第 N 步 → 退 2 并列出候选 id 与步数； 正常时只渲染每条命中… (+20 more)

### Community 44 - "compose.py"
Cohesion: 0.07
Nodes (43): _find_worker_spec(), _make_ecr_client(), _make_ecs_client(), _make_lambda_client(), _make_ssm_client(), new_run_id(), _no_default_pointer_error(), parse_iso() (+35 more)

### Community 45 - "_is_transient_network"
Cohesion: 0.10
Nodes (35): _error_text(), _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, SDK 异常的 str() 是多行 repr（真跑暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message 首行、折叠空白、封顶。 (+27 more)

### Community 46 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 47 - "deterministic.py"
Cohesion: 0.07
Nodes (40): deterministic, src/index.mts — 包公开 API, src/worker/deterministic.mts — 确定性注册表, src/worker/deterministic.steps.mts — 内建脚手架 step, clear(), deterministic(), DeterministicConflict, _Entry (+32 more)

### Community 48 - "Artifact Upload Tests"
Cohesion: 0.10
Nodes (31): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+23 more)

### Community 49 - "Midscene Worker 开发笔记"
Cohesion: 0.12
Nodes (25): ADR 0002 不用 gpt-5.5 驱动 Midscene, ADR 0003 Midscene grounding 用 Qwen3-VL on Bedrock, ADR 0004 Nova Act 经 Workflow 的 IAM 鉴权, ADR 0008 Midscene Bedrock SigV4 自签, ADR 0010 spike 作 apples-to-apples 基准, ADR 0014 AI 断言投票, ADR 0020 step 措辞默认 AI + 确定性脚手架, ADR 0022 BDD runner 退役、core 解析 + 薄 worker (+17 more)

### Community 50 - "evidence.mts"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct, EvidenceDoc (+21 more)

### Community 51 - "._run_cdk"
Cohesion: 0.16
Nodes (10): context_cache_path(), Path, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, 凡要合成 app 的动作（deploy / diff / synth / destroy）都必须有 `--vpc`（无隐式默认，ADR 0037 决策 6：…, 生成的 `cdk.json` 里的 `app`：用**当前解释器**跑本包的 CDK app。 必须是 `sys.executable`、不是裸…, 在临时工作目录生成 `cdk.json`（ADR 0037 决策 6）——**不再有入库的 cdk.json**：它曾假定自己躺在 monorepo… (+2 more)

### Community 52 - "test_cloud_reconcile.py"
Cohesion: 0.13
Nodes (20): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, _job(), cloud 无状态跑批 core 侧测试（ADR 0034 P4a）：DdbEventLog + CloudLauncher +…, CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。 (+12 more)

### Community 53 - "常见问题"
Cohesion: 0.14
Nodes (14): AI 做出的判定能当回归门禁吗？同一条用例会不会今天过、明天不过？, 一个 AWS 账号里能同时跑 stage 和 prod 两套后端吗？, 什么时候该从本机跑换成云端后端？, 几十条用例跑一轮大概多久？能同时跑几条？, 同一批用例在本机跑和在云端跑，结果会一样吗？, 和 Playwright、Cucumber 是什么关系？现有用例能迁过来吗？, 它在什么浏览器里跑？能测移动端视口，或换成 Firefox、Safari 吗？, 常见问题 (+6 more)

### Community 54 - "main"
Cohesion: 0.16
Nodes (10): cumulativeTokens(), drainArtifactQueue(), isTransientNetwork(), log(), main(), runScenario(), runStep(), shutdownSequence() (+2 more)

### Community 55 - "_FakeEcsClient"
Cohesion: 0.15
Nodes (16): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), 跑一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。 (+8 more)

### Community 56 - ".bootstrap"
Cohesion: 0.15
Nodes (12): cdk_command(), check_cdk(), check_node(), `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…, `gherkai doctor` 的 provider 段（ADR 0041 决策四）：部署方工具链**只读**自检——Node ≥ 22、cdk…, Node 与 cdk CLI 两个前置：缺 → 打一句话、退 2；齐 → None。 `deploy` / `bootstrap` / `_run_cdk`…, cdk CLI 的调用前缀：PATH 上的 `cdk` 优先，否则 `npx -y aws-cdk@2`（ADR 0037 决策 6）。都没有 → 空列表。, cdk CLI 前置：PATH 上既无 `cdk` 也无 `npx` → 返回给人看的一句话；能定位 → None。 与 `check_node()`… (+4 more)

### Community 57 - "test_fargate_engine.py"
Cohesion: 0.12
Nodes (41): _engine(), _job(), _put_event(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。, worker 零事件退出 + exit item 已落：STOPPED 兜底路径（含 _final_drain 强一致终读）同样只读 worker 段。… (+33 more)

### Community 58 - "Artifact Uploader (Python)"
Cohesion: 0.13
Nodes (17): ArtifactUploader, _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内跑（NonThreadedExecutor）。 默认的线程池是非… (+9 more)

### Community 59 - "_RecUploader"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只跑到收尾序列）。 (+10 more)

### Community 60 - "build_diagrams.mjs"
Cohesion: 0.17
Nodes (13): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+5 more)

### Community 61 - "_stream_record"
Cohesion: 0.11
Nodes (19): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events… (+11 more)

### Community 62 - "test_subprocess_engine.py"
Cohesion: 0.20
Nodes (21): Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, SubprocessEngine, _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, pump 线程必须**先于**写 stdin 起：job JSON >64KB（DocString）× worker 读 stdin 前先吐 >64KB…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr… (+13 more)

### Community 63 - "Nova worker flag-only 信号 handler"
Cohesion: 0.10
Nodes (20): act 有界返回（per-act timeout）, cdp_session.__exit__ 释放 AgentCore 会话, 建连早期误报 engine_error 根治, errorType 分类, 事件流结束信号 / 存活判定迁移, exitCode 落值延迟的有界宽限轮询, 未来演进：显式 core→worker 控制通道, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin） (+12 more)

### Community 64 - "atomic_write_json"
Cohesion: 0.11
Nodes (22): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ResourceUri, 归集出 <root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 file://… (+14 more)

### Community 65 - "test_event_sink.py"
Cohesion: 0.10
Nodes (9): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud(), test_emit_flushes_each_event() (+1 more)

### Community 66 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd()

### Community 67 - "build_engines"
Cohesion: 0.08
Nodes (30): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, Path, 某引擎定位链 miss **不连坐**另一条腿（ADR 0037 决策 3）：dev 下 midscene 未装是常态， novaact-only 的 run… (+22 more)

### Community 68 - "reconciler.py"
Cohesion: 0.11
Nodes (21): _build(), EventBridgeTimeoutWatch, _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)… (+13 more)

### Community 69 - "test_lambda_asset.py"
Cohesion: 0.12
Nodes (23): make_stack(), **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), Path, Lambda asset 构建测试（ADR 0037 决策 6「Lambda asset 来源」）：纯本地、不联网、不碰 AWS。…, 没有命令给的工作目录（裸跑 cdk synth）→ 自建 mkdtemp，仍不写仓库。 (+15 more)

### Community 70 - "deploy.py"
Cohesion: 0.10
Nodes (23): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+15 more)

### Community 71 - "FargateEngine"
Cohesion: 0.18
Nodes (11): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+3 more)

### Community 72 - "SKILL.md 住 cli/gherkai_cli/skills/gherkai/、随 wheel 发行"
Cohesion: 0.07
Nodes (30): URL 映射：feature 写原始地址、组装 job 时替换, worker --list-deterministic dump 模式与 CLI list-deterministic, gherkai doctor 只读自检, cli-json-contract.md 字段契约 + 真值集对照护栏, scenario 筛选 --scope/--tags/--scenario, evidence.json（worker 在 step 边界产的 gherkai 自有 schema）, gherkai explain（判定树 + 证据合成，退出码只用 0/2）, StepResult.message 落进 jobs/*.json (+22 more)

### Community 73 - "test_detached_launcher.py"
Cohesion: 0.06
Nodes (57): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, now_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, build_local_reconcile(), cleanup_tunnel(), drive_local_reconcile(), _paths(), Job (+49 more)

### Community 74 - "require_boto3"
Cohesion: 0.17
Nodes (6): 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…

### Community 75 - "report_store/local.py"
Cohesion: 0.12
Nodes (18): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。… (+10 more)

### Community 76 - "test_project.py"
Cohesion: 0.07
Nodes (73): ScopeStarted, EventRecord, plan_next(), project(), project_full(), events 表里一条记录的投影输入（ADR 0034）：reconciler 从表全量重放时，每条 record 携带的信息。 worker…, 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, 从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。 与… (+65 more)

### Community 77 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 78 - "_Recorder"
Cohesion: 0.15
Nodes (11): cdk(), _FakeEngine, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。…, `GHERKAI_CONTAINER_ENGINE=podman` → 退 2 且**不调 cdk**：纯参数问题，账户一个字节都不该动…, 有 node、`cdk` 与 `npx` 都定位不到（如装了 nodejs 没装 npm）：`deploy` 在读后端之前退 2。 **不能落到 cdk…, _Recorder (+3 more)

### Community 79 - "test_tunnel_host.py"
Cohesion: 0.13
Nodes (20): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道… (+12 more)

### Community 80 - "_StubEcs"
Cohesion: 0.22
Nodes (4): 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 81 - "Eval Harness Runner"
Cohesion: 0.18
Nodes (20): collect_outputs(), fail(), load_evals(), main(), materialize(), parse_events(), pollution_metrics(), _purge_session_dir() (+12 more)

### Community 82 - "DynamoDB 作 events-out 传输（共享表 + Query 轮询）"
Cohesion: 0.11
Nodes (18): DynamoDB 作 events-out 传输（共享表 + Query 轮询）, Engine port（run_scope，不挂 stop）, EventSink（事件出口可注入接口）, events 表键设计 PK=run_id#scope_id / SK=seq, events item TTL 自动过期（expires_at 7 天）, FargateWorkerHandle.stop → StopTask, JobSource（job 入口可注入接口）, 被拒方案：DynamoDB Streams（同步 run 语境） (+10 more)

### Community 83 - "JobSource"
Cohesion: 0.09
Nodes (11): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+3 more)

### Community 84 - "Skill Stage Materialization"
Cohesion: 0.27
Nodes (20): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+12 more)

### Community 85 - "Skill Install Command"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.17
Nodes (18): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。, 递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque =… (+10 more)

### Community 87 - "ADR 0033 IaC 资源清单与命名契约"
Cohesion: 0.09
Nodes (30): ADR 0001 范围限定英文 UI, ADR 0002 Midscene 不用 Bedrock GPT-5.5, ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL, ADR 0004: Nova Act IAM 鉴权经 Workflow, ADR 0007 程序化登录，HITL 仅作调试逃生舱, ADR 0008: Midscene→Bedrock SigV4 自签鉴权, ADR 0009 最大化使用 AWS 是硬前提, ADR 0011 AgentCore 浏览器：默认 vs 自建 (+22 more)

### Community 88 - "_read_events"
Cohesion: 0.15
Nodes (12): _join_pumps(), _pump_log(), Event, Job, Popen, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+4 more)

### Community 89 - "_FakeProc"
Cohesion: 0.14
Nodes (12): _gen_auth(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+4 more)

### Community 90 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 91 - "RunPersistence"
Cohesion: 0.14
Nodes (24): LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, Event, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, 事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收… (+16 more)

### Community 92 - "_progress"
Cohesion: 0.10
Nodes (27): _build_selector(), _cmd_list_deterministic(), _cmd_plan(), _cmd_reconcile(), _cmd_status(), _load_and_plan(), _plan_and_preflight(), _preflight_worker_runtimes() (+19 more)

### Community 93 - "ADR 0037 分发与打包"
Cohesion: 0.11
Nodes (32): cli 包 contributor 文档, 版本 skew 六态比对, VPC 档三态比对, skill 参考：CLI --json 字段契约（生成副本）, skill 参考：云端后端分工与 variant 镜像, skill 参考：引擎选择与确定性 step 模板, skill 参考：环境就位与排障, gherkai agent SKILL.md (+24 more)

### Community 94 - "Status"
Cohesion: 0.05
Nodes (44): commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, Status, RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。 为什么是 core…, Engine, EngineResolver (+36 more)

### Community 96 - "sigv4Fetch"
Cohesion: 0.10
Nodes (14): main(), BASE_URL, main(), ADR-0033, BASE_URL, Check, main(), MODEL_CONFIG (+6 more)

### Community 97 - "runtime 包 contributor 文档"
Cohesion: 0.15
Nodes (17): ADR 0016 执行架构 core/lib/run 模型, ADR 0026 schedule 模块契约, ADR 0030 实时持久化接缝, ADR 0034 无状态跑批 reconciler, ADR 0035 经隧道测试本机应用, worker 定位链, runtime/compose.py — 组合根/引擎注册表, compose.build_engines (+9 more)

### Community 98 - "dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 99 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 100 - "test_tunnel.py"
Cohesion: 0.16
Nodes (18): make_tunnel(), NgrokTunnel, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, stop_tunnel(), _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。… (+10 more)

### Community 101 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 102 - "test_package_readmes.py"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归 DEVELOPMENT.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 103 - "_await_engine"
Cohesion: 0.60
Nodes (5): _await_engine(), _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 104 - "test_finished_run_gate_keys_on_the_committed_run_status_only"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后跑完的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 105 - "_release_cmp"
Cohesion: 0.15
Nodes (13): is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp(), _release_key(), _variant_miss_hint() (+5 more)

### Community 107 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 108 - "_render_status"
Cohesion: 0.18
Nodes (18): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。 (+10 more)

### Community 109 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 110 - "test_skill.py"
Cohesion: 0.10
Nodes (28): _claimed_flags(), _fixture_files(), _is_ignored(), _parser_nodes(), agent skill 的护栏（ADR 0043 决策六；fixture 三条见决策七）。 skill 是**产品面**：它随 wheel 发行、由…, 零内部指代：skill 落在使用方项目里，ADR 编号 / 决策号 / 内部机制名对那边的 agent 是噪声。, markdown 相对链接一律禁：出 skill 的（`](../…)`）在安装态必死；skill 内的（`](references/x.md)`）虽活，…, 指本仓库的 URL 只用 `blob/HEAD/` / `tree/HEAD/` / `tree/v…/`（裸仓库首页不指内容，也放行）：… (+20 more)

### Community 111 - "_CdkWritingContext"
Cohesion: 0.28
Nodes (9): _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix(), test_context_cache_is_saved_after_the_run_and_seeded_into_the_next_fresh_work_dir(), test_context_cache_survives_a_failed_cdk_run() (+1 more)

### Community 112 - "_tagged_feature"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号 = 任一命中；重复 --tags = 都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 退 2 并列全部候选（id 标题），别静默跑空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope = 报告里的 scope_id：named scope 的名字选中整个 scope（两条都跑），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 113 - "build_fargate_engines"
Cohesion: 0.10
Nodes (19): build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _normalize_prefix(), 读某 task-def revision 上 worker container 的 `stopTimeout`（秒）= **cloud 档真实的停止宽限**。…, cloud 档一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走… (+11 more)

### Community 114 - "变更记录"
Cohesion: 0.10
Nodes (21): [1.3.0] - 2026-08-17, [1.4.0] - 2026-09-08, [1.4.1] - 2026-09-10, [1.4.2] - 2026-09-16, [1.4.3] - 2026-09-16, [Unreleased], 修复, 修复 (+13 more)

### Community 115 - "query_capabilities"
Cohesion: 0.07
Nodes (36): engine_min_grace(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc(), parametrize, dev/post/本地段版本**不在 PyPI/npm 上**（ADR 0037 决策 2b 的派生形态）→ 第四级跳过、直接 miss 报安装指引。 否则… (+28 more)

### Community 116 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 117 - "gherkai_runtime/__init__.py"
Cohesion: 0.20
Nodes (9): gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 118 - "_FakeSchedulerClient"
Cohesion: 0.20
Nodes (8): ConflictException, exceptions, _FakeSchedulerClient, create_schedule 记录器（含 exceptions.ConflictException 形状，兼容 boto3 client 异常访问路径）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, test_timeout_watch_conflict_is_idempotent(), test_timeout_watch_creates_one_time_schedule(), Exception

### Community 119 - "Midscene Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 120 - "Provider"
Cohesion: 0.10
Nodes (22): Provider, ArgumentParser, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。 (+14 more)

### Community 121 - "run-scope.test.mts"
Cohesion: 0.09
Nodes (12): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+4 more)

### Community 122 - "Distribution Metadata Checks"
Cohesion: 0.28
Nodes (12): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。 (+4 more)

### Community 123 - "_argv"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证， 不会跑…, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 124 - "gherkai_cli/__main__.py"
Cohesion: 0.07
Nodes (42): ArgumentParser, _add_selection_flags(), _build_parser(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_doctor(), _cmd_list_engines(), _cmd_run() (+34 more)

### Community 125 - "._guard_vpc_spec"
Cohesion: 0.13
Nodes (14): classify_vpc_state(), _make_cfn_client(), _make_ssm_client(), 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, boto3 cloudformation client（`DescribeStacks` 探 stack 是否已存在）。, boto3 ssm client（读生效 VPC 档参数）。, 给缺 `--vpc` 的提示配「怎么办」：环境已存在 → 报后端记录的上次那一档；无记录 → 说明要给当初那一档； stack 不在 →…, deploy 前的 VPC 档比对。放行 → None；拦 → 退出码（2）。 只在 deploy 前跑（见 `diff`/`destroy` 的… (+6 more)

### Community 126 - "无状态 reconciler（CQRS 投影 + 推进）"
Cohesion: 0.20
Nodes (10): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志，写模型）, 机制二：平台侧退出观察者（从 STOPPED 事件读 exitCode）, 机制三：HWM 条件写 + 状态机单调条件写, job timeout（两层声明 → definition 载体 → 三路推进器 enforce）, kicker Lambda（runs 表 Stream 冷启动）, 无状态 reconciler（CQRS 投影 + 推进）, RunState 物化读视图（唯一写者 = reconciler） (+2 more)

### Community 127 - "Skill Deploy Token Guardrail"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 皮 + provider 拼出的真 parser。皮那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` = `gherkai <verb>` 本身）。 (+3 more)

### Community 128 - "03-midscene-grounding.ts"
Cohesion: 0.18
Nodes (11): ADR-0010, src/bin.mts — worker 唯一入口, src/lib/agentcore-sigv4.mts — SigV4 与 region 解析, src/resolve-hook.mts — 裸 specifier 解析钩子, BASE_URL, MODEL_CONFIG, REGION, ADR-0033 (+3 more)

### Community 129 - "render_skill_contract.py"
Cohesion: 0.26
Nodes (11): RuntimeError, _assert_clean(), main(), _paragraphs(), 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 130 - "test_user_facing_messages.py"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 131 - "release.yml — 发布全链工作流"
Cohesion: 0.10
Nodes (25): 使用方 (Consumer) vs contributor, 部署 provider (deploy provider), 部署方 (Deployer), 确定性 step 注册表, 跑法权限梯 (Execution tiers), 点名检查 vs 确定性锚点, feature 作者 (Feature author / QA), 柔性冒烟 (Flexible smoke) (+17 more)

### Community 132 - "_MissingThenStoppedEcs"
Cohesion: 0.12
Nodes (17): _delayed_stopped_ecs(), _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 洞在宽限后仍在 = 写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。… (+9 more)

### Community 133 - "_patch_skew"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 同款的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 134 - "gherkai_runtime/names.py"
Cohesion: 0.08
Nodes (31): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_worker_template_path(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的… (+23 more)

### Community 135 - "@gherkai/worker-midscene (README)"
Cohesion: 0.28
Nodes (9): ADR 0038 worker 镜像交付, AgentCore 云浏览器（本机不装 Chromium）, 确定性 step, 镜像必须 --platform linux/amd64, 纯 IAM 鉴权（无 API key）, engines/midscene/Dockerfile — worker 基底镜像, @gherkai/worker-midscene (README), engines/novaact/Dockerfile — worker 基底镜像 (+1 more)

### Community 136 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 137 - "_print_artifact_lines"
Cohesion: 0.50
Nodes (4): _print_artifact_lines(), 产物落点三行（报告 / 运行元信息 / 判定明细）→ stderr：**`run` 结束与 `status` 终态共用这一份**…, 报告写入被隔离（落点表里没有 report_index 键，ADR 0030 决定三）→ 报告那行给「写失败」提示， 既不打裸…, test_artifact_lines_report_write_failure_falls_back_to_a_note()

### Community 138 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 139 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 140 - "_cmd_submit"
Cohesion: 0.29
Nodes (7): _build_run_meta(), _cmd_submit(), `--expose-local` 的 argparse 侧接线：编排在 `gherkai_runtime.tunnel_host`（ADR 0035 决策…, 组装 definition（ADR 0016/0027）：新 run_id + 创建时刻 + plan 产出的 jobs + run 级执行参数。 `run`…, [无状态跑批] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id → 立即退出。…, _setup_tunnel(), RunMeta

### Community 141 - "文档健康度复盘（全部项目文档）— 任务说明"
Cohesion: 0.14
Nodes (14): Status 头（第二层的配套：枚举、判定与连带审计；头本身是每个 ADR 开头一行）, 为什么做（价值）, 产出与提交, 何时做（触发）, 六类问题（分类找）, 执行方法（多轮复盘验证过的最佳路径）, 按文档类型的复盘侧重（用对判据）, 文档健康度复盘（全部项目文档）— 任务说明 (+6 more)

### Community 142 - "test_cloud_integration.py"
Cohesion: 0.05
Nodes (47): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore…, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。 (+39 more)

### Community 143 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 144 - "exit_observer.py"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 145 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 146 - "编写确定性 step"
Cohesion: 0.14
Nodes (14): `description` 与 `example` 的作用, handler 拿到什么, `steps/` 目录与查找顺序, 两侧对称地写, 内建的确定性 step, 写之前, 判定与报错, 加载失败的表现 (+6 more)

### Community 147 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 148 - "is_placeholder"
Cohesion: 0.29
Nodes (8): is_placeholder(), `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, _allowed_flags(), 只认**同一个反引号代码跨**内的 `gherkai <子命令> … --flag` 组合，逐对对照该 subparser 的真 flag 集。…, 裸词序列 → 子命令路径。第一个词不是已知子命令且不是占位符 → None（拼错的子命令）。, 路径上（含各级祖先）声明的 flag 全集——`deploy --prefix p push-worker …` 这种父层给法是合法的。, _resolve(), test_flags_are_attached_to_the_right_subcommand()

### Community 149 - "部署与维护云端后端"
Cohesion: 0.15
Nodes (13): deploy 与 destroy 的选项, VPC 三档, worker 镜像 variant, 前置要求, 后端包含什么, 团队成员需要的最小云端权限, 拆除与清理, 版本与升级 (+5 more)

### Community 150 - "test_local_result_store_atomic.py"
Cohesion: 0.38
Nodes (6): _big_job_result(), LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 跑到一半时读…, ~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。, 判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。, test_concurrent_reader_never_sees_torn_job_result(), test_job_result_file_stays_readable_by_others()

### Community 151 - "Contract Key Documentation Check"
Cohesion: 0.33
Nodes (6): _documented_keys(), 契约页记载的字段名。取「字段表里（任一列）+『顶层…』/『每项…』散文里」的反引号 token， 再按键形状过滤——ADR…, skill 里形如 JSON 键的反引号 token 必须是契约页记载的键，否则显式登记成非键。 挡的是「把 `record_missing` 写成…, test_key_shaped_tokens_are_documented_keys(), collect(), main()

### Community 152 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 153 - "排错"
Cohesion: 0.15
Nodes (13): 云端后端, 仍未定位到原因时, 先跑 gherkai doctor, 其它以退出码 2 结束的错误, 凭证与 region, 各行查什么, 安装与版本, 引擎与判定 (+5 more)

### Community 154 - "SqliteEventLog"
Cohesion: 0.09
Nodes (24): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, SqliteEventLog (+16 more)

### Community 155 - "权威信息源（自查用）"
Cohesion: 0.25
Nodes (8): Agent Skills（见 ADR 0043）, AWS Bedrock / AgentCore, Midscene（任意页加 `.md` 取 markdown）, Nova Act, 发行与打包（见 ADR 0037）, 常用 CLI（本项目实测用到）, 权威信息源（自查用）, 镜像与 ECS 交付（见 ADR 0038）

### Community 156 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 158 - "_Worker"
Cohesion: 0.17
Nodes (10): _heartbeat_wrap(), Event, Job, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…, _Worker (+2 more)

### Community 160 - "_engine_with_fake_ecs"
Cohesion: 0.25
Nodes (8): _engine_with_fake_ecs(), DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null(), test_probe_task_stopped_with_exit_code()

### Community 162 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 163 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 164 - "Skill Frontmatter Validation"
Cohesion: 0.50
Nodes (4): _frontmatter_and_body(), 极简 frontmatter 解析（不引 yaml：dev 依赖里没有，为一条护栏引一个包不值）。 支持 `key: 单行值`、引号值，以及 `key:…, `name` 形态且等于目录名（安装目标目录名由它派生）；`description` 非空 ≤ 1024（description 优化循环…, test_skill_form_limits()

### Community 165 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 166 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 167 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 169 - "Worker Image Version Mappings"
Cohesion: 0.50
Nodes (4): _image_param(), `_iter_image_params` 那种 `(engine, tag, value)` 三元组（不过 SSM，直接喂筛选函数）。, `current_version_mappings` 吃**已枚举好**的参数序列：只留本引擎 + 本版本的、按 variant 名排序，…, test_current_version_mappings_filters_one_engine_and_version_out_of_a_shared_enumeration()

### Community 171 - "Event Reduction & Short-Circuit"
Cohesion: 0.50
Nodes (4): job 归约的 scope_done 内容完整前置, status 三级归约（scenario→job→run）, step_skipped 归约（scope 内短路）, scope 内 step 级短路（worker 侧）

### Community 172 - "files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 173 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 174 - "Worker Artifact Upload"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 175 - "Upload Call Recorder"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素 = (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 176 - "Skill Evaluation Design"
Cohesion: 0.67
Nodes (3): ADR 0043 skill 评测设计, 评分子代理提示词模板, skills/ 目录说明

### Community 177 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 180 - "决策"
Cohesion: 0.15
Nodes (13): 0045. 文档分层与归位：按读者三分类、目录归位、包页面降为入口页、每版 changelog、按类别定口吻, 一、读者三分类，用户侧 agent 归用户文档, 七、图统一用 archify：JSON 图源 + 导出 SVG 入库，只有发布到 Pages 的交互版才入库 HTML, 三、包页面降为入口页（反转 0039 面二的「完整操作手册」）, 与 agent skill 的关系（0043 不变）, 二、目录归位, 五、每版 changelog，Release 正文与链接钉 tag, 六、按类别定口吻 (+5 more)

### Community 181 - "执行与推进模型导览：run / submit × local / cloud"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的生命周期, 4. 后台跑批 `submit` 的生命周期, 4a. local 档：per-run 推进进程, 4b. cloud 档：三 Lambda 链, 4c. 读侧：进度观察与结果落点, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 183 - "开发者指南"
Cohesion: 0.18
Nodes (11): Spike（可独立运行的技术验证脚本）, 发布与版本, 在有凭证的机器上验证未发布的工作树, 如何参与, 开发环境（从 checkout 跑）, 开发者指南, 文档去哪读, 测试 (+3 more)

### Community 185 - "代码健康度复盘（全部生产代码）— 任务说明"
Cohesion: 0.18
Nodes (11): 三类问题（分类找）, 为什么做（价值）, 产出与提交, 代码健康度复盘（全部生产代码）— 任务说明, 何时做（触发）, 分片深读（可用 workflow 并行）, 对抗验证, 执行方法（本项目跑通的最佳路径） (+3 more)

### Community 187 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 195 - "配置：环境变量与通用选项"
Cohesion: 0.18
Nodes (11): AWS 访问与云端资源名, 云端资源名与网络的单项覆盖, 使用者可设的环境变量, 引擎行为, 模型选择, 由 gherkai 注入的环境变量, 跨命令通用选项, 部署机 (+3 more)

### Community 206 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 208 - "RevisionInfo"
Cohesion: 0.50
Nodes (3): family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, RevisionInfo

### Community 209 - "ValueError"
Cohesion: 0.13
Nodes (16): 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, render(), section(), is_botocore_error(), _make_s3_client(), BaseException (+8 more)

### Community 212 - "_advancer_stmts"
Cohesion: 0.40
Nodes (5): _advancer_stmts(), Template, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…, test_reconciler_and_kicker_have_the_same_permission_face()

### Community 215 - "test_s3_report_store.py"
Cohesion: 0.20
Nodes (13): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index() (+5 more)

### Community 216 - "cli.py"
Cohesion: 0.07
Nodes (31): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, _error_code(), _make_sts_client(), _node_major(), Exception, `gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`…, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6； 三档与… (+23 more)

### Community 220 - "test_lambda_handlers.py"
Cohesion: 0.06
Nodes (36): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, Stream records + 直接 run_id 并存时都提取（健壮）。, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。 (+28 more)

### Community 221 - "test_release_notes.py"
Cohesion: 0.29
Nodes (9): _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」与 Release…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag(), test_repo_changelog_has_every_released_tag_and_unreleased(), test_section_extracts_exactly_one_version() (+1 more)

### Community 224 - "_stopped_detail"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode = 容器没跑起来（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 225 - "._pump"
Cohesion: 0.50
Nodes (3): Event, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, Timer

### Community 226 - "cloud_env"
Cohesion: 0.67
Nodes (3): cloud_env(), moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。, fixture

### Community 228 - "gherkai CLI 的 `--json` 字段契约"
Cohesion: 0.20
Nodes (10): `evidence` 的固定键, gherkai CLI 的 `--json` 字段契约, `gherkai deploy list-workers --json`, `gherkai doctor --json`, `gherkai explain <run_id> [<scope_id>] --json`, `gherkai list-deterministic --engine <名> --json`, `gherkai list-engines --json`, `gherkai plan … --json` (+2 more)

### Community 231 - "判定的计算路径：从单次投票到退出码"
Cohesion: 0.20
Nodes (10): 1. 四层归约：票 → step → scenario → job → run, 2. 七个状态：含义与处置, 3. 两根正交的轴与 `error_type` 类别集, 3a. `status` × `shortcircuited`, 3b. `error_type`：赋值方与取值, 3c. job 收场态与 `error_type`：归因的优先级, 4. severity：数值序而非字母序；run 级为何不含 skipped/aborted, 5. 退出码：各命令的语义不同 (+2 more)

### Community 234 - "test_user_docs.py"
Cohesion: 0.15
Nodes (20): parametrize, Path, 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…, 导出的 SVG 末尾带 `gherkai:source-sha256=<sha256(json)>` 指纹（tools/build_diagrams.mjs…, 作图入口 = 项目级 skill `.claude/skills/diagram/SKILL.md`，它只指向方法文档 docs/ai-…, owner 表（docs/user-guide/README.md）与目录里的页一一对应：两向差集。, docs/diagrams/<name>.json（图源）与 <name>.svg（导出）成对：缺任一半即漂（HTML 不入库，由 JSON 现场构建）。, 交互 HTML 只对发布到 Pages 的图入库：git 跟踪的每个 <name>.html 必须有同名图源，且在 index.html 里有链接 （发布 =… (+12 more)

### Community 236 - "test_evidence.py"
Cohesion: 0.16
Nodes (21): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _picks(), step 级机读证据（evidence，ADR 0042 决策一/二/六）单测：映射 / 截图上界 / 目录键 / best-effort 钩子。 纯…, n 帧的合成 trajectory：thought_at 里的帧带 think call，每帧都有可解的 data URL 图。, 转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了 = evidence 静默互相覆盖。, 同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。, 零 evidence（单例还没造）→ 直接返回；且**不在退出路径上现造上传器**（半注入会 fail-loud 抛）。 (+13 more)

### Community 237 - "_presend_act_siblings"
Cohesion: 0.18
Nodes (16): _attach_traj_refs(), _presend_act_siblings(), 本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。 一个…, 把本 step 的 trajectory 挂上 step_done 事件：抢传配套 json（ADR 0029）+ reportRefs（ADR 0027…, act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…, _traj_refs(), _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验… (+8 more)

### Community 238 - "云端后端由哪些载体组成：一次改动要传播到哪几处才生效"
Cohesion: 0.25
Nodes (8): 1. 五个载体, 2. 行为归属哪个载体（改动前的定位表）, 3. 一次版本升级的传播顺序，以及顺序为何不可调换, 4. 症状 → 该推哪个载体, 5. `submit` 在提交时刻固定下来的内容, 6. 一个 prefix = 一套环境；多版本并存依靠多 prefix, 7. 延伸阅读, 云端后端由哪些载体组成：一次改动要传播到哪几处才生效

### Community 239 - "一条确定性 step 的生命周期：从写下正则到云端命中"
Cohesion: 0.25
Nodes (8): 0. 全景：四段路径，一张注册表, 1. 派发决策链：一条 step 文本进入 worker 之后, 2. 三个入口，一张表：为什么清单、标注、真跑不可能分叉, 3. 两个真值源、一个岔口：为什么「改了 steps，云端没变」是设计, 4. 响亮失败：症状 → 原因 → 处置, 5. 两引擎对称，与一处已知缺口, 6. 延伸阅读, 一条确定性 step 的生命周期：从写下正则到云端命中

### Community 242 - "架构总览：五层结构、一次 run 的生命周期、包与发行物"
Cohesion: 0.29
Nodes (7): 1. 全景图, 2. 五层各自的职责, 3. 一次 run 的生命周期, 4. 本机与云端：同一条链的两种载体, 5. 包与发行物, 6. 延伸阅读, 架构总览：五层结构、一次 run 的生命周期、包与发行物

### Community 243 - "产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）"
Cohesion: 0.29
Nodes (7): 1. 五类产物，各回答一个问题, 2. 物理位置：local 与 cloud 是同一棵树的两种载体, 3. 证据链的串接, 4. 一次失败的三步读法, 5. 边界（有意取舍，非遗漏）, 6. 延伸阅读, 产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）

### Community 246 - "test_error_step_also_enqueues_only_after_emit"
Cohesion: 0.11
Nodes (10): _NovaRaisesAfterFirstVote, list, 记 emit 与 enqueue 的**先后**（顺序即契约：判定绝不等截图字节）。, 确定性 / URL 导航 step 不产 evidence → 一次入队都不该有（队列里不许有幻影文件）。, 第一票正常回（带 trajectory → 有截图可入队），第二票抛——把 except 出口逼成「有截图的 error step」。, except 出口（step 记 error）同守 emit→enqueue 序：三条出口共用一个收尾出口，不许有一条漏掉这层顺序。, _Result, test_error_step_also_enqueues_only_after_emit() (+2 more)

### Community 251 - "_FakeResult"
Cohesion: 0.12
Nodes (8): _ActBoom, _FakeResult, _Meta, _NavErrorNova, RuntimeError, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 Nova SDK 的 act 异常：与成功结果一样带 metadata（time_worked_s 已真实计费、trajectory 已写盘）。

### Community 252 - "._resolve_target"
Cohesion: 0.17
Nodes (8): 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…, flag → CDK context（app/stack 侧读的那四个旋钮 + 版本戳）。 `--vpc` 一个 flag 摊成两个旋钮：`default`…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本单旋钮）。 优先 CLI 皮交进来的 `args.version`（=…

### Community 253 - "编写 .feature"
Cohesion: 0.18
Nodes (11): AI 断言怎么写才稳, Gherkin 写法的支持范围, 一个 step 的三种执行方式, 一个最小的 .feature, 三个有语义的 tag, 什么交给 AI，什么必须精确, 写完先自检, 投票：让 AI 断言判多次取多数 (+3 more)

### Community 260 - "test_worker_subnets_single_source_across_ssm_and_lambda_env"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 275 - "_submit_local"
Cohesion: 0.50
Nodes (4): local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。…, _submit_local(), local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, write_tunnel_file()

### Community 300 - "_explain_emit"
Cohesion: 0.16
Nodes (14): _cmd_explain(), _explain_cloud(), _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches(), explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…, 读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。… (+6 more)

### Community 301 - "跑测试与看结果"
Cohesion: 0.20
Nodes (10): 两个独立的选择：怎么跑、跑在哪, 命令, 在 CI 里跑, 常用选项（`run` / `submit`）, 机读输出, 看失败原因：`explain`, 结果在哪, 费用量级 (+2 more)

### Community 302 - "开始使用"
Cohesion: 0.22
Nodes (9): AWS 前置, 上手路径一：交给 AI agent, 上手路径二：自己敲命令, 下一步, 安装, 开始使用, 按角色选安装形态, 用 doctor 预检 (+1 more)

### Community 304 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 305 - "测本机或内网里的被测应用"
Cohesion: 0.22
Nodes (9): 前置：ngrok 与 authtoken, 存活时间上限：`--tunnel-ttl S`, 安全, 工作方式, 常见故障, 测本机或内网里的被测应用, 用法, 限制 (+1 more)

### Community 306 - "ArtifactUploader 组件（from_env / to_report_ref / flush）"
Cohesion: 0.50
Nodes (5): ArtifactUploader 组件（from_env / to_report_ref / flush）, snapshotLogs（scenario 边界 log 抢传）, snapshotReport（Midscene 单引擎增补）, 上传失败处理两层（分类 + scope 级降级）, 组合根接线：build_fargate_engines 切 cloud 执行

## Ambiguous Edges - Review These
- `成功重试对 RunResult 透明（可观测性缺口）` → `上传成功后删本地`  [AMBIGUOUS]
  docs/adr/0029-engine-artifacts-to-s3.md · relation: conceptually_related_to
- `ADR 0001 范围限定英文 UI` → `gherkai agent SKILL.md`  [AMBIGUOUS]
  docs/adr/0001-scope-limited-to-english-ui.md · relation: references

## Knowledge Gaps
- **562 isolated node(s):** `如何参与`, `现状与版本线`, `目录结构`, `开发环境（从 checkout 跑）`, `在有凭证的机器上验证未发布的工作树` (+557 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **97 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `成功重试对 RunResult 透明（可观测性缺口）` and `上传成功后删本地`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `ADR 0001 范围限定英文 UI` and `gherkai agent SKILL.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `gherkai-worker-novaact (README)` connect `@gherkai/worker-midscene (README)` to `Midscene Worker 开发笔记`, `deterministic.py`, `test_user_steps.py`?**
  _High betweenness centrality (0.159) - this node is a cross-community bridge._
- **Why does `Nova Act Worker 开发笔记` connect `Midscene Worker 开发笔记` to `runtime 包 contributor 文档`, `CONTRIBUTING.md`, `@gherkai/worker-midscene (README)`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `deterministic()` connect `deterministic.py` to `ValueError`, `_run_step`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Are the 56 inferred relationships involving `Job` (e.g. with `_explain_job()` and `test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()`) actually correct?**
  _`Job` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `RunState` (e.g. with `_cmd_submit()` and `_explain_run()`) actually correct?**
  _`RunState` has 40 INFERRED edges - model-reasoned connections that need verification._