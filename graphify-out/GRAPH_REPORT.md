# Graph Report - yaozhou  (2026-09-20)

## Corpus Check
- 317 files · ~530,075 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5441 nodes · 11651 edges · 339 communities (219 shown, 120 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 785 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7bb127b9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Job
- test_detached_launcher.py
- test_workers.py
- test_backend_cloud.py
- workers.py
- StepDone
- build_engines
- scan_family
- _render_status
- S3StepArgumentOffloader
- ContainerEngine
- test_compose.py
- _run_step
- test_schedule.py
- test_stack.py
- test_deploy_cmd.py
- _RecUploader
- test_evidence.py
- _write_feature
- RunPersistence
- ensure_workflow_definition
- ADR 0016 执行架构 / 组合根注入
- LocalReportStore
- test_tunnel_cli.py
- _fixture
- test_main.py
- ADR 0019 feature tag 的 scope 与引擎路由
- Provider
- test_interrupt_model.py
- test_plan.py
- CONTRIBUTING.md
- test_worker_variant.py
- _out
- test_conditional_writes.py
- RunResult（事件流归约终值）
- query_capabilities
- JobResult
- render.py
- RunState
- test_user_steps.py
- main
- BackendStack
- _ask_worker
- _explain_run
- compose.py
- _is_transient_network
- deterministic.mts
- deterministic.py
- test_artifact_upload.py
- Midscene Worker 开发笔记
- evidence.mts
- ._run_cdk
- _StampSsm
- test_sqlite_event_log.py
- _stream_record
- test_argument.py
- resolve_worker_cmd
- _job
- Path
- _FakeEcs
- build_diagrams.mjs
- build_local_reconcile
- run_scope.py
- Nova worker flag-only 信号 handler
- test_lifecycle_states.py
- test_event_sink.py
- event-sink.mts
- RunMeta
- SqliteEventLog
- test_lambda_asset.py
- deploy.py
- FargateEngine
- SKILL.md 住 cli/gherkai_cli/skills/gherkai/、随 wheel 发行
- test_project.py
- test_cloud_reconcile.py
- ScopeDone
- ._installed_import_source
- compilerOptions
- _Recorder
- test_tunnel_host.py
- test_container.py
- run_evals.py
- test_report_still_written_when_the_run_duration_read_fails
- test_job_source.py
- materialize.py
- Skill Install Command
- test_cli_json_contract.py
- DynamoDB 作 events-out 传输（共享表 + Query 轮询）
- 编写确定性 step
- resolve_container_engine
- test_subprocess_engine.py
- code-health 第 5 轮：待批报告
- gherkai_cli/__main__.py
- ADR 0037 分发与打包
- ._collect
- ArtifactUploader
- sigv4Fetch
- runtime 包 contributor 文档
- dependencies
- main
- test_tunnel.py
- evidence.test.mts
- test_package_readmes.py
- cloud_env
- report_store/local.py
- read_task_def_stop_timeout
- _AbsentEngine
- events_wallclock.py
- test_fargate_engine.py
- _runs_stream_record
- test_skill.py
- 编写 .feature
- _stopped_detail
- ADR 0033 IaC 资源清单与命名契约
- 变更记录
- test_reconcile.py
- _build_parser
- tunnel.py
- reconciler.py
- Midscene Worker Package Manifest
- .add_arguments
- run-scope.test.mts
- check_dist_metadata.py
- _documented_keys
- StepResult
- cleanup_pass
- 无状态 reconciler（CQRS 投影 + 推进）
- Skill Deploy Token Guardrail
- 03-midscene-grounding.ts
- render_skill_contract.py
- test_user_facing_messages.py
- release.yml — 发布全链工作流
- _MissingThenStoppedEcs
- _job_with
- gherkai_runtime/names.py
- user_steps.py
- job-source.mts
- 01-model-sigv4.ts
- artifact-upload.test.mts
- Worker Signal Interrupt Tests
- section
- 文档健康度复盘（全部项目文档）— 任务说明
- 部署与维护云端后端
- ECS Task Timing Capture
- exit_observer.py
- user-steps.mts
- 常见问题
- Graph Refresh Script
- _doc_rules.py
- 运行测试与查看结果
- _FakeEcs
- 测本机或内网里的被测应用
- argument.mts
- 排错
- _SeqEcs
- 权威信息源（自查用）
- Echo Test Worker
- Cloud Test Infrastructure Check
- _ClientError
- _FakeSink
- 05-negative-assertions.ts
- test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine
- user-steps.test.mts
- TypeScript Dev Dependencies
- 开始使用
- @aws-sdk/client-dynamodb
- deterministic.steps.mts
- bin.mts
- start_tunnel_for_jobs
- Worker Image Version Mappings
- user-guide/README.md
- Event Reduction & Short-Circuit
- files
- Repository Metadata
- Worker Artifact Upload
- _Calls
- Skill Evaluation Design
- NPM Scripts
- AgentCore CDP Spike
- ArtifactUploader
- 决策
- 执行与推进模型导览：run / submit × local / cloud
- sync-derived.sh
- contributor 指南
- Adapters Package
- 代码健康度复盘（全部生产代码）— 任务说明
- cli.py
- index.mts
- TSX Dependency
- _FakeTable
- EventBridgeTimeoutWatch
- Job
- Job
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
- wire.py
- detached.py
- agentcore-sigv4.test.mts
- job-source.test.mts
- _events_table_actions
- _seed_worker_ssm
- _cmd_tunnel_watch
- Protocol
- stop_tunnel
- argument.test.mts
- deterministic.test.mts
- error-text.test.mts
- test_lambda_handlers.py
- test_release_notes.py
- runStep
- _tagged_feature
- test_read_events_scope_done_waits_for_stopped_before_reading_exit
- test_finished_run_gate_keys_on_the_committed_run_status_only
- ResourceUri
- _CdkWritingContext
- gherkai CLI 的 `--json` 字段契约
- .records
- check_version_skew
- 判定的计算路径：从单次投票到退出码
- SubprocessLauncher
- 04-planning-probe.ts
- test_user_docs.py
- Job
- Scenario
- test_tick_runs_isolates_defensive_scan_failure
- 云端后端由哪些载体组成：一次改动要传播到哪几处才生效
- 一条确定性 step 的生命周期：从写下正则到云端命中
- _run_with_refs
- ADR-0016
- 架构总览：五层结构、一次 run 的生命周期、包与发行物
- 产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）
- @aws-sdk/client-bedrock-agentcore
- release_body_footer.md
- deterministic_steps.py
- 推进器 (advancer)
- /code-health-review 命令入口
- /doc-health-review 命令入口
- aws
- Step
- openai
- StepArgument
- is_placeholder
- no-artifacts.test.mts
- Template
- ADR-0008
- container.py
- test_artifact_lines_report_write_failure_falls_back_to_a_note
- test_worker_subnets_single_source_across_ssm_and_lambda_env
- stack.py
- ImageInfo
- DEFAULT_MODEL
- MODEL
- MODEL_FAMILY_PATTERNS
- ADR-0033
- ADR-0037
- Job
- ADR-0044
- .inspect
- test_events_stream_mapping_filters_out_ttl_removes
- digest_for_repo
- test_provider_module_does_not_import_aws_cdk
- ADR-0019
- .inspect
- CloudTarget
- ResourceUri
- Protocol
- Scenario
- Step
- StepArgument
- list
- lib/__init__.py
- FeatureSource
- LocalRunStore
- NamedTuple
- ArgumentParser
- RunMeta
- SqliteEventLog
- Exception
- SubprocessEngine
- parametrize
- Job
- fixture
- build_local_stores
- ADR-0026
- ADR-0027
- ADR-0035
- ADR-0039
- CONTENT_TYPES
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0032
- ADR-0033
- ADR-0042
- UPLOAD_TIMEOUT_MS
- AWS_TRANSIENT_NAMES
- .preflight
- AWS_TRANSIENT_STATUS
- BaseException
- _patch_skew
- BROWSER_CLOSE_BUDGET_MS
- CONNECT_BACKOFF_MS
- Path
- INFLIGHT_SETTLE_MS
- Job
- _FakeS3
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
- JobState

## God Nodes (most connected - your core abstractions)
1. `main()` - 215 edges
2. `Job` - 135 edges
3. `RunState` - 120 edges
4. `RunMeta` - 119 edges
5. `JobState` - 100 edges
6. `Status` - 98 edges
7. `Provider` - 94 edges
8. `JobResult` - 81 edges
9. `Scenario` - 74 edges
10. `Step` - 73 edges

## Surprising Connections (you probably didn't know these)
- `README.md — 仓库首页（使用者向）` --conceptually_related_to--> `跑法权限梯 (Execution tiers)`  [INFERRED]
  README.md → CONTEXT.md
- `gherkai agent SKILL.md` --references--> `ADR 0001 范围限定英文 UI`  [AMBIGUOUS]
  cli/gherkai_cli/skills/gherkai/SKILL.md → docs/adr/0001-scope-limited-to-english-ui.md
- `--expose-local 隧道` --conceptually_related_to--> `ADR 0035 经隧道测本机应用`  [INFERRED]
  cli/gherkai_cli/skills/gherkai/SKILL.md → docs/adr/0035-local-app-testing-via-tunnel.md
- `test_build_wires_arg_offloader_so_step_argument_bodies_read_back()` --calls--> `S3StepArgumentOffloader`  [INFERRED]
  deploy_aws/tests/test_lambda_handlers.py → core/gherkai_core/adapters/run_store/arg_offload.py
- `_status_cloud()` --calls--> `DynamoDBRunStore`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/run_store/ddb.py

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

## Communities (339 total, 120 thin omitted)

### Community 0 - "Job"
Cohesion: 0.05
Nodes (83): _explain_job(), 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本/JSON 同律）；命中的 scope 的…, test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), DynamoDBRunStore, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, STATE item 上有没有 `detached` 标记（ADR 0034）：True = 无状态批量运行的 submit 建的 run。… (+75 more)

### Community 1 - "test_detached_launcher.py"
Cohesion: 0.20
Nodes (19): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。 **真 spawn…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize… (+11 more)

### Community 2 - "test_workers.py"
Cohesion: 0.08
Nodes (68): _cleanup(), FakeContainer, _mapping(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 一次干净的推送：tag/push 到 ECR ref → 从模板注册 revision（镜像按 digest、血缘 tags 齐）→ 写 SSM 映射。, digest 的唯一来源 = **推送后**那次 inspect，且在多条 `RepoDigests` 里**按本 repo 挑**（GHCR 那条在第一位）。 (+60 more)

### Community 3 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (101): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：…, `--quiet` 静音这几行（同它静音逐事件进度的口径）；解析本身照做（拿到映射、写 definition）。, 名字不合 tag 字符集 → 入口就退 2（对齐 --max-concurrency 的入口校验惯例）：真零副作用—— 连读戳都没发生。校验点复用… (+93 more)

### Community 4 - "workers.py"
Cohesion: 0.06
Nodes (74): Aws, _connect(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable(), ImageMapping (+66 more)

### Community 5 - "StepDone"
Cohesion: 0.13
Nodes (27): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+19 more)

### Community 6 - "build_engines"
Cohesion: 0.08
Nodes (31): Engine, build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, Path (+23 more)

### Community 7 - "scan_family"
Cohesion: 0.11
Nodes (12): _parse_ts(), family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, family 的全部 ACTIVE revision（带 tags）。 两个坑：**`familyPrefix` 是前缀匹配**（`gherkai-…, tag 里的 ISO 串 / boto3 回来的 datetime → aware UTC datetime；空或读不懂 → None。, RevisionInfo, scan_family(), datetime (+4 more)

### Community 8 - "_render_status"
Cohesion: 0.21
Nodes (16): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在运行、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。 (+8 more)

### Community 9 - "S3StepArgumentOffloader"
Cohesion: 0.05
Nodes (30): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3… (+22 more)

### Community 10 - "ContainerEngine"
Cohesion: 0.16
Nodes (8): ContainerEngine, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。, 拉镜像（基础镜像同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。, 短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。, 长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。, docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 不同形）。 `binary`…, test_probe_reports_missing_binary_without_raising()

### Community 11 - "test_compose.py"
Cohesion: 0.07
Nodes (43): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_cloud_target(), resolve_region(), _clear_aws_env(), _fake_store_ctors() (+35 more)

### Community 12 - "_run_step"
Cohesion: 0.07
Nodes (52): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行执行一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _ActBoom, _done() (+44 more)

### Community 13 - "test_schedule.py"
Cohesion: 0.19
Nodes (57): 执行一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+49 more)

### Community 14 - "test_stack.py"
Cohesion: 0.04
Nodes (29): BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理时的运行中 run 引用检查）：**投影必须含…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**锁定（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新时取值记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值 = task-def 的 `Ref`（**带 revision** 的 ARN）。… (+21 more)

### Community 15 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令行前端测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 前端实例化它；指向现成对象则原样用。, provider 的选项由它自己贴（前端不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 前端自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 16 - "_RecUploader"
Cohesion: 0.08
Nodes (18): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 提前退出路径（其后不 flush）：超时提示说链接可能打不开——不承诺任何后续兜底。, scope 末（其后紧跟整目录 flush）：超时不等于丢，提示只说改由收尾统一上传、不吓人。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只执行到收尾序列）。 (+10 more)

### Community 17 - "test_evidence.py"
Cohesion: 0.07
Nodes (53): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), _error_text(), 异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…, _done(), _Nova, _NovaRaisesAfterFirstVote, _picks() (+45 more)

### Community 18 - "_write_feature"
Cohesion: 0.05
Nodes (56): _capturing_schedule(), _fake_schedule_factory(), Path, 同一个 .feature 传两遍：CLI 按一次算 + 打一行提示，不再撞 core 窄腰的 uri 互异违约退 2 （收集去重是调用方的责任，ADR…, 写法不同、归一后是同一个文件（`demo.feature` 与 `sub/../demo.feature`）→ 同样按一次算： 去重键必须取…, `run` 结束打的三行与 `status` 终态**同一份**（`_print_artifact_lines`）：报告 / 运行元信息 / 判定明细，…, run 与 submit 共享同一段前置（plan → steps 目录 → 本机后端 worker 检查），唯一的输出差别 = 逐 job 明细： run…, --quiet（ADR 0041 决策二）：worker 日志落 <run_dir>/worker.log（--no-report… (+48 more)

### Community 19 - "RunPersistence"
Cohesion: 0.12
Nodes (25): LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。…, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, Event, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run = commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run… (+17 more)

### Community 20 - "ensure_workflow_definition"
Cohesion: 0.06
Nodes (43): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发情形也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二个 spike · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开…, run() (+35 more)

### Community 21 - "ADR 0016 执行架构 / 组合根注入"
Cohesion: 0.10
Nodes (51): core 包 contributor 文档, gherkai-core 用户面 README, ADR 0016 执行架构 / 组合根注入, 决策 A：--backend cloud = 存储上云 + Fargate 执行（单旋钮）, 核心库是窄腰，CLI/WebUI 是可替换薄前端, Ports & Adapters + 组合根注入, Run 数据模型（Step/Scenario/Feature/Scope/Job/Run）, 三层切分：definition / 控制面运行态 / 数据面判定 (+43 more)

### Community 22 - "LocalReportStore"
Cohesion: 0.18
Nodes (33): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 收紧 umask 也必须落 0644——这是「报告写面退回 write_text」的判别式护栏。 `write_text` 的权限随 umask 走（077…, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。 (+25 more)

### Community 23 - "test_tunnel_cli.py"
Cohesion: 0.07
Nodes (45): submit 把 --max-concurrency 落进 definition（推进器读 meta，不靠 flag 通道）。 fork 出的 per-run…, submit 侧同 run：解析一次写进 definition——per-run 进程/接力者从 definition 读回（**不**收 flag，…, test_submit_local_persists_steps_dir_into_definition(), test_submit_local_writes_max_concurrency_into_definition(), test_submit_rejects_max_concurrency_below_one(), _patch_cloud_commit(), _patch_cloud_gates(), _patch_tunnel() (+37 more)

### Community 24 - "_fixture"
Cohesion: 0.04
Nodes (67): Any, cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…, _stub_engine_capabilities(), aws(), _fake_aws_creds(), fargate(), 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表… (+59 more)

### Community 25 - "test_main.py"
Cohesion: 0.05
Nodes (75): _cloud_backend_ok(), _det_feature(), _doctor_cloud_json(), _fake_locator(), _fake_worker_cmd(), _miss(), _no_provider(), cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json… (+67 more)

### Community 26 - "ADR 0019 feature tag 的 scope 与引擎路由"
Cohesion: 0.06
Nodes (56): 穿刺 / Spike, 穿刺脚本落点（by-engine）, ADR 0001 范围限定英文 UI, ADR 0002 Midscene 不用 Bedrock GPT-5.5, ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL, ADR 0004: Nova Act IAM 鉴权经 Workflow, ADR 0005 单一共享 .feature 文件, ADR 0006: 形态 A 两子工程、无编排器 (+48 more)

### Community 27 - "Provider"
Cohesion: 0.05
Nodes (84): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, 留的口子（ADR 0038「命令族」）：**尚未提供**，退 2 说清为什么与将来怎么落。 为何占位而不干脆不给这个子命令：不给的话用户敲了只会得到…, _argv(), _parse(), _parse_destroy(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 取值三态。… (+76 more)

### Community 28 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (35): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 运行结束后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True=中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True=退避中收到停止信号（应停止重连）。 用…, captured() (+27 more)

### Community 29 - "test_plan.py"
Cohesion: 0.05
Nodes (71): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, FeatureSource, plan(), PlanConfig, Job, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario… (+63 more)

### Community 30 - "CONTRIBUTING.md"
Cohesion: 0.07
Nodes (36): CLAUDE.md — 项目约定, 文档纪律（ADR / CONTEXT / journey / guides 分层）, graphify 知识图使用约定, 绿 ≠ 对：识别结论的证据边界, CONTEXT.md — 领域术语表, agent skill (gherkai skill), AgentCore 浏览器会话, 确定性断言 vs AI 断言 (+28 more)

### Community 31 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (46): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。 值 =…, worker_image_key(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。 (+38 more)

### Community 32 - "_out"
Cohesion: 0.11
Nodes (24): _cell(), list_workers(), 定宽列（**按显示宽度补，不按字符数**）：中文表头字符占两列，用 `f"{s:<28}"` 会让整张表歪掉。…, 按引擎列**当前版本**的 variant（tag / digest / 推送时间 / revision）+ 默认指针 + 待清理与孤儿。 「当前版本」=…, _out(), 收集打印文本的 out 替身 → (调用函数, 取全文函数)。, dev 版（`.dev`/`.post`/本地段）**GHCR 上不存在对应基础镜像** → 明确警告 + 跳过基础镜像同步，第 3/4 步照常执行。…, cdk 已成功、机器上没有容器引擎 → 退 1 + 「stack 已生效、重新运行幂等收敛」（不是退 2：账户已被改过）。 (+16 more)

### Community 33 - "test_conditional_writes.py"
Cohesion: 0.08
Nodes (43): _initial(), _meta(), fixture, RunStore 无状态批量运行条件写对拍测试（ADR 0034 机制三/机制四）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。 (+35 more)

### Community 34 - "RunResult（事件流归约终值）"
Cohesion: 0.06
Nodes (43): 原生量成本归约（tokens / time_worked_s）, 墙钟时长归约（duration_ms 四级）, EngineResolver（按 job.engine 解析 Engine）, failFast 与失败隔离, 优雅终止（schedule 只下逻辑「停」指令）, _heartbeat_wrap（静默 worker 存活心跳）, Job.timeout_s 超时兜底, max_concurrency（默认 4） (+35 more)

### Community 35 - "query_capabilities"
Cohesion: 0.08
Nodes (33): engine_min_grace(), query_capabilities(), 查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…, 问该引擎 worker 自报的 grace 下限（ADR 0024「引擎自报下限」，自述契约见 ADR 0036「5.」）。…, _caps_json(), _fake_caps_proc(), 一份合契约的自述对象（五个键，ADR 0036「5.」）；模型 id 不给就按引擎取该引擎真实会自报的那个。, 整份自述对象原样返回（五个键：schema_version / engine / min_grace_s / deterministic_steps /… (+25 more)

### Community 36 - "JobResult"
Cohesion: 0.09
Nodes (24): 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。 (+16 more)

### Community 37 - "render.py"
Cohesion: 0.07
Nodes (39): _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches(), explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…, 读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。…, 没有判定明细可渲染时的输出：人读打一行提示、`--json` 仍只打一个（scopes 为空的）文档。恒退 0。 退 0 而非 2 是刻意的（ADR 0042…, local/cloud 共用的后半段：取判定明细 → 筛 scenario/step → 合成文档 → 打文本或 JSON。 带 `scope_id` 时只… (+31 more)

### Community 38 - "RunState"
Cohesion: 0.04
Nodes (49): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, test_render_status_pending_run_with_claimed_job_does_not_hint(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), _job_state_from_item(), _job_state_to_item() (+41 more)

### Community 39 - "test_user_steps.py"
Cohesion: 0.09
Nodes (36): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, `_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。, `_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。 (+28 more)

### Community 40 - "main"
Cohesion: 0.06
Nodes (47): cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。 `__main__`（argparse 前端）+…, main(), 对照：定位链 miss（运行时没装）plan 仍降级退 0（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。, 给了目录 / 读不了的路径 → 退 2「读 feature 失败」，不是 IsADirectoryError traceback（退码语义 ADR…, 云端后端第一道闸是版本 skew（先于任何云端读）：block → 退 2，且根本没去装 store。, `gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。…, --version 打印「gherkai <发行版本>」并退 0——版本真源是包元数据（git tag → uv-dynamic-versioning），…, test_default_engine_flag_has_choices() (+39 more)

### Community 41 - "BackendStack"
Cohesion: 0.11
Nodes (16): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的取值记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+8 more)

### Community 42 - "_ask_worker"
Cohesion: 0.09
Nodes (22): _ask_worker(), local_artifact_locations(), match_deterministic(), prune_empty_dirs(), Path, RuntimeError, 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`… (+14 more)

### Community 43 - "_explain_run"
Cohesion: 0.08
Nodes (35): _evidence_fixture(), _explain(), _explain_cloud_stores(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。 (+27 more)

### Community 44 - "compose.py"
Cohesion: 0.04
Nodes (69): subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), build_fargate_engines(), cloud_artifact_locations() (+61 more)

### Community 45 - "_is_transient_network"
Cohesion: 0.12
Nodes (31): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+23 more)

### Community 46 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 47 - "deterministic.py"
Cohesion: 0.09
Nodes (32): clear(), deterministic(), DeterministicConflict, _Entry, _hits(), list_registry(), match(), match_batch() (+24 more)

### Community 48 - "test_artifact_upload.py"
Cohesion: 0.10
Nodes (33): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 半注入(有桶缺 NOVA_LOGS_DIR)→ 装配矛盾 fail-loud(静默 no-op 会让产物随容器盘销毁必丢,ADR 0033)。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。 (+25 more)

### Community 49 - "Midscene Worker 开发笔记"
Cohesion: 0.11
Nodes (29): ADR 0002 不用 gpt-5.5 驱动 Midscene, ADR 0003 Midscene grounding 用 Qwen3-VL on Bedrock, ADR 0004 Nova Act 经 Workflow 的 IAM 鉴权, ADR 0008 Midscene Bedrock SigV4 自签, ADR 0010 spike 作 apples-to-apples 基准, ADR 0014 AI 断言投票, ADR 0020 step 措辞默认 AI + 确定性脚手架, ADR 0022 BDD runner 退役、core 解析 + 薄 worker (+21 more)

### Community 50 - "evidence.mts"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct, EvidenceDoc (+21 more)

### Community 51 - "._run_cdk"
Cohesion: 0.08
Nodes (19): Path, 供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。 (+11 more)

### Community 52 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口前端**：CLI / WebUI /…, read_backend_version(), _client_error(), 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。, `ParameterNotFound` → None（决策 7 判「警告不拦」）——若翻成异常，本机制之前部署的所有环境会被锁死。, 凭证/权限/region 类错误照抛——由入口前端归到自己的退出码层，不伪装成「没有戳」。 (+10 more)

### Community 53 - "test_sqlite_event_log.py"
Cohesion: 0.17
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 54 - "_stream_record"
Cohesion: 0.11
Nodes (19): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…, 只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events… (+11 more)

### Community 55 - "test_argument.py"
Cohesion: 0.11
Nodes (21): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。 (+13 more)

### Community 56 - "resolve_worker_cmd"
Cohesion: 0.08
Nodes (26): _find_worker_spec(), 一个引擎 worker 的拉起方式 = 定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, resolve_worker_cmd(), WorkerCmd, parametrize, dev/post/本地段版本**不在 PyPI/npm 上**（ADR 0037 决策 2b 的派生形态）→ 第四级跳过、直接 miss 报安装指引。 否则… (+18 more)

### Community 57 - "_job"
Cohesion: 0.15
Nodes (23): _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。, worker 零事件退出 + exit item 已落：STOPPED 兜底路径（含 _final_drain 强一致终读）同样只读 worker 段。… (+15 more)

### Community 58 - "Path"
Cohesion: 0.19
Nodes (9): _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内执行（NonThreadedExecutor）。 默认的线程池是非…, scope 末：整目录递归上传剩余文件（跳过已传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→… (+1 more)

### Community 59 - "_FakeEcs"
Cohesion: 0.08
Nodes (22): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` = 运行中的 task；`tasks` = 带状态的…, n 个「别的 scope」的已停止 task——用来把 ListTasks 的 STOPPED 列表撑过一页。, 仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, STOPPED task 多于一页时也要定位到运行中的目标：ListTasks 翻页取全、DescribeTasks 每批不超上限、命中即停。 ECS… (+14 more)

### Community 60 - "build_diagrams.mjs"
Cohesion: 0.17
Nodes (15): ADR-0045, args, DEFAULT_DIR, deliver(), dirIdx, exportFrom(), htmlOnly, main() (+7 more)

### Community 61 - "build_local_reconcile"
Cohesion: 0.14
Nodes (18): build_local_reconcile(), LocalRunStore, 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, _job(), region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。 (+10 more)

### Community 62 - "run_scope.py"
Cohesion: 0.06
Nodes (49): ActRecord, ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _attach_traj_refs(), _capabilities(), _collect_traj() (+41 more)

### Community 63 - "Nova worker flag-only 信号 handler"
Cohesion: 0.10
Nodes (20): act 有界返回（per-act timeout）, cdp_session.__exit__ 释放 AgentCore 会话, 建连早期误报 engine_error 根治, errorType 分类, 事件流结束信号 / 存活判定迁移, exitCode 落值延迟的有界宽限轮询, 未来演进：显式 core→worker 控制通道, grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin） (+12 more)

### Community 64 - "test_lifecycle_states.py"
Cohesion: 0.07
Nodes (22): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一… (+14 more)

### Community 65 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 66 - "event-sink.mts"
Cohesion: 0.20
Nodes (7): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, ADR-0033, resolveEventsFd()

### Community 67 - "RunMeta"
Cohesion: 0.05
Nodes (53): RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…, render_text(), render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, 跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。 core 不能 import…, skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；…, step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。, job 行有分类、message 为 None → 只显分类 `(worker_crashed)`，不打 `(worker_crashed:…, test_index_html_shortcircuit_note_matches_cli_wording() (+45 more)

### Community 68 - "SqliteEventLog"
Cohesion: 0.19
Nodes (8): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, SqliteEventLog

### Community 69 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (24): make_stack(), make_template(), Template, synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources() (+16 more)

### Community 70 - "deploy.py"
Cohesion: 0.10
Nodes (23): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+15 more)

### Community 71 - "FargateEngine"
Cohesion: 0.18
Nodes (11): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…, 起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+3 more)

### Community 72 - "SKILL.md 住 cli/gherkai_cli/skills/gherkai/、随 wheel 发行"
Cohesion: 0.07
Nodes (30): URL 映射：feature 写原始地址、组装 job 时替换, worker --list-deterministic dump 模式与 CLI list-deterministic, gherkai doctor 只读自检, cli-json-contract.md 字段契约 + 真值集对照护栏, scenario 筛选 --scope/--tags/--scenario, evidence.json（worker 在 step 边界产的 gherkai 自有 schema）, gherkai explain（判定树 + 证据合成，退出码只用 0/2）, StepResult.message 落进 jobs/*.json (+22 more)

### Community 73 - "test_project.py"
Cohesion: 0.06
Nodes (90): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…, SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, ScopeStarted, StepStarted, Action, EventRecord, _job_status() (+82 more)

### Community 74 - "test_cloud_reconcile.py"
Cohesion: 0.06
Nodes (49): CloudLauncher, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, events_pk() (+41 more)

### Community 75 - "ScopeDone"
Cohesion: 0.10
Nodes (23): NamedTuple, 一次 DescribeTasks 探测的结果——**三个正交事实各自命名**（ADR 0024「exitCode 落值延迟」；前两个见下、第三个…, TaskProbe, ScopeDone, Event, 单个 scope 执行过程中各级起始时间戳 + 暂存的 step 结果（core 算墙钟时长用，ADR 0024）。 从 `schedule._Timing`…, 把单个 worker 事件归约进 JobResult（就地累积，ADR 0024/0026）。 **这是 `schedule._Worker._reduce`…, reduce_event() (+15 more)

### Community 76 - "._installed_import_source"
Cohesion: 0.33
Nodes (4): 把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容 = 本包 `lambdas/` 的 handler…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it()

### Community 77 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 78 - "_Recorder"
Cohesion: 0.12
Nodes (14): cdk(), _clean_aws_env(), _FakeEngine, fixture, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真实运行 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。… (+6 more)

### Community 79 - "test_tunnel_host.py"
Cohesion: 0.11
Nodes (22): gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…, compute_watch_ttl_s(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。… (+14 more)

### Community 80 - "test_container.py"
Cohesion: 0.18
Nodes (12): _Fake, _inspect_spec(), 容器引擎口子测试（ADR 0038「容器引擎口子」）。 **两层证据，分清边界**： - 大部分用一个**假 docker**（记 argv/stdin 的…, 「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。, **密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。, 假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。, test_inspect_missing_image_is_not_an_error(), test_inspect_other_failure_raises() (+4 more)

### Community 81 - "run_evals.py"
Cohesion: 0.18
Nodes (20): collect_outputs(), fail(), load_evals(), main(), materialize(), parse_events(), pollution_metrics(), _purge_session_dir() (+12 more)

### Community 82 - "test_report_still_written_when_the_run_duration_read_fails"
Cohesion: 0.15
Nodes (14): now_iso(), parse_iso(), datetime, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, detached run 的 run 级墙钟（毫秒）= RunState `ended_at` - `started_at`（提交落库到 finalize…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的… (+6 more)

### Community 83 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 84 - "materialize.py"
Cohesion: 0.24
Nodes (22): assert_no_installed_skill(), assert_prepared(), assert_stage_isolated(), _cli_main_digest(), copy_fixture(), fail(), integrity_check(), main() (+14 more)

### Community 85 - "Skill Install Command"
Cohesion: 0.18
Nodes (19): _agents(), _append_pointer(), _ask_pointer(), _converge(), install(), _is_ours(), _packaged_skill_dir(), _print_skill() (+11 more)

### Community 86 - "test_cli_json_contract.py"
Cohesion: 0.17
Nodes (18): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。, 递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque =… (+10 more)

### Community 87 - "DynamoDB 作 events-out 传输（共享表 + Query 轮询）"
Cohesion: 0.11
Nodes (18): DynamoDB 作 events-out 传输（共享表 + Query 轮询）, Engine port（run_scope，不挂 stop）, EventSink（事件出口可注入接口）, events 表键设计 PK=run_id#scope_id / SK=seq, events item TTL 自动过期（expires_at 7 天）, FargateWorkerHandle.stop → StopTask, JobSource（job 入口可注入接口）, 被拒方案：DynamoDB Streams（同步 run 语境） (+10 more)

### Community 88 - "编写确定性 step"
Cohesion: 0.14
Nodes (14): `description` 与 `example` 的作用, handler 拿到什么, `steps/` 目录与查找顺序, 两侧对称地写, 内建的确定性 step, 写之前, 判定与报错, 加载失败的表现 (+6 more)

### Community 89 - "resolve_container_engine"
Cohesion: 0.18
Nodes (14): 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 未实装的名字…, resolve_container_engine(), ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。…, arm 变体真镜像 → 架构判据拒（= push-worker 退 2 那一支）。 用 alpine（小）代替真 worker 镜像：判据只看…, `docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取…, `--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。, test_default_is_docker(), test_env_selects_engine_and_flag_wins() (+6 more)

### Community 90 - "test_subprocess_engine.py"
Cohesion: 0.27
Nodes (18): _engine(), _job(), Job, SubprocessEngine, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr…, _rm(), test_adapter_crash_is_error() (+10 more)

### Community 91 - "code-health 第 5 轮：待批报告"
Cohesion: 0.18
Nodes (10): ① 基线, ② 请裁定（每项带复盘方倾向，编号可一句话回）, ③ 可直接改（CONFIRMED 客观类，本轮已落；按文件组）, ④ 重构 / 主观提案（待批；每条附倾向）, ⑤ 主观发现（口吻 / 已评估不动）, ⑥ 各片覆盖记录（读了什么、怎么核的；详见 workflow 结果）, ⑦ 跨包扫记录, ⑧ 上轮驳回核对与移交接收 (+2 more)

### Community 92 - "gherkai_cli/__main__.py"
Cohesion: 0.07
Nodes (57): _build_run_meta(), _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_explain(), _cmd_list_deterministic(), _cmd_plan(), _cmd_reconcile() (+49 more)

### Community 93 - "ADR 0037 分发与打包"
Cohesion: 0.11
Nodes (30): cli 包 contributor 文档, 版本 skew 六态比对, VPC 档三态比对, skill 参考：CLI --json 字段契约（生成副本）, skill 参考：云端后端分工与 variant 镜像, skill 参考：引擎选择与确定性 step 模板, skill 参考：环境就位与排障, gherkai agent SKILL.md (+22 more)

### Community 94 - "._collect"
Cohesion: 0.32
Nodes (6): local_path_from_uri(), Path, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run…, 把 run 树内的本地产物 ref 转成相对 run_dir 的 href；否则原样返回 ref（ADR 0027 href 相对化）。…, 若 ref 指向本地文件（file:// 或裸路径），返回 Path；远端（http/s3 等）返回 None。 **公开小工具**（本模块 href…, _relative_href()

### Community 96 - "sigv4Fetch"
Cohesion: 0.20
Nodes (6): main(), main(), getRegion(), modelSigner_(), sigv4Fetch(), agentOpts()

### Community 97 - "runtime 包 contributor 文档"
Cohesion: 0.10
Nodes (24): ADR 0016 执行架构 core/lib/run 模型, ADR 0026 schedule 模块契约, ADR 0030 实时持久化接缝, ADR 0034 无状态跑批 reconciler, ADR 0035 经隧道测试本机应用, ADR 0038 worker 镜像交付, AgentCore 云浏览器（本机不装 Chromium）, 镜像必须 --platform linux/amd64 (+16 more)

### Community 98 - "dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 99 - "main"
Cohesion: 0.20
Nodes (6): drainArtifactQueue(), log(), main(), runScenario(), shutdownSequence(), step()

### Community 100 - "test_tunnel.py"
Cohesion: 0.17
Nodes (15): NgrokTunnel, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, TunnelInfo, _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。 (+7 more)

### Community 101 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 102 - "test_package_readmes.py"
Cohesion: 0.15
Nodes (13): parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, GitHub Release 正文 = CHANGELOG.md 本版节 +…, _shipped_readmes() (+5 more)

### Community 103 - "cloud_env"
Cohesion: 0.67
Nodes (3): cloud_env(), fixture, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。

### Community 104 - "report_store/local.py"
Cohesion: 0.07
Nodes (33): atomic_write_json(), atomic_write_text(), Path, 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。…, 把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。, 同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。, ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index() (+25 more)

### Community 105 - "read_task_def_stop_timeout"
Cohesion: 0.25
Nodes (7): 读某 task-def revision 上 worker container 的 `stopTimeout`（秒）= **云端后端真实的停止宽限**。…, read_task_def_stop_timeout(), container_name(), task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…, _StopTimeoutEcs, test_read_task_def_stop_timeout_none_when_unset_or_container_absent(), test_read_task_def_stop_timeout_reads_worker_container()

### Community 107 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 108 - "test_fargate_engine.py"
Cohesion: 0.12
Nodes (27): _engine(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, RunTask 容量不足/子网无 IP 等 → HTTP 200 + 空 tasks + failures。须翻成带 reason 的明确异常，非…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。, 执行 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。 (+19 more)

### Community 109 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 110 - "test_skill.py"
Cohesion: 0.09
Nodes (32): _claimed_flags(), _fixture_files(), _frontmatter_and_body(), _is_ignored(), _parser_nodes(), parametrize, Path, agent skill 的护栏（ADR 0043 决策六；fixture 三条见决策七）。 skill 是**产品面**：它随 wheel 发行、由… (+24 more)

### Community 111 - "编写 .feature"
Cohesion: 0.18
Nodes (11): AI 断言怎么写才稳, Gherkin 写法的支持范围, 一个 step 的三种执行路径, 一个最小的 .feature, 三个有语义的 tag, 什么交给 AI，什么必须精确, 写完先自检, 投票：让 AI 断言判多次取多数 (+3 more)

### Community 112 - "_stopped_detail"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, container 缺 exitCode = 容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, _stopped_detail() (+8 more)

### Community 113 - "ADR 0033 IaC 资源清单与命名契约"
Cohesion: 0.12
Nodes (20): ArtifactUploader 组件（from_env / to_report_ref / flush）, snapshotLogs（scenario 边界 log 抢传）, snapshotReport（Midscene 单引擎增补）, 决定三：commit-point 写序（数据面先、控制面后）, 决定七：Store port 增 preflight() 探活, 决定一·补：pending / running 生命周期前置态, 上传失败处理两层（分类 + scope 级降级）, 组合根接线：build_fargate_engines 切 cloud 执行 (+12 more)

### Community 114 - "变更记录"
Cohesion: 0.10
Nodes (21): [1.3.0] - 2026-08-17, [1.4.0] - 2026-09-08, [1.4.1] - 2026-09-10, [1.4.2] - 2026-09-16, [1.4.3] - 2026-09-16, [Unreleased], 修复, 修复 (+13 more)

### Community 115 - "test_reconcile.py"
Cohesion: 0.07
Nodes (43): finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), BoomLauncher, _done_events(), FakeLauncher, _meta() (+35 more)

### Community 116 - "_build_parser"
Cohesion: 0.08
Nodes (26): _add_selection_flags(), _build_parser(), _cmd_doctor(), _cmd_list_engines(), _cmd_skill_install(), _dist_version(), _doctor_cloud(), _doctor_worker_grace() (+18 more)

### Community 117 - "tunnel.py"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 118 - "reconciler.py"
Cohesion: 0.14
Nodes (16): datetime, _handle_timeout(), handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节的云端后端一侧）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…, 本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带…, 从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch… (+8 more)

### Community 119 - "Midscene Worker Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 120 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 121 - "run-scope.test.mts"
Cohesion: 0.09
Nodes (12): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+4 more)

### Community 122 - "check_dist_metadata.py"
Cohesion: 0.28
Nodes (12): check_skill_payload(), fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。 (+4 more)

### Community 123 - "_documented_keys"
Cohesion: 0.33
Nodes (6): _documented_keys(), 契约页记载的字段名。取「字段表里（任一列）+『顶层…』/『每项…』散文里」的反引号 token， 再按键形状过滤——ADR…, skill 里形如 JSON 键的反引号 token 必须是契约页记载的键，否则显式登记成非键。 挡的是「把 `record_missing` 写成…, test_key_shaped_tokens_are_documented_keys(), collect(), main()

### Community 124 - "StepResult"
Cohesion: 0.18
Nodes (18): _sample_run(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar(), 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, 单个 step 的归约结果（core 保留 step 级粒度，ADR 0024）。 duration_ms = step 墙钟时长（core 用…, ReportRef, ScenarioResult, StepResult (+10 more)

### Community 125 - "cleanup_pass"
Cohesion: 0.15
Nodes (13): cleanup_pass(), CleanupOutcome, _hours(), _iter_image_params(), _mapped_arn(), _non_terminal_statuses(), 枚举 `worker-image/*` 全部参数（**含所有版本、所有引擎**）→ `(engine, tag, value)`。…, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看… (+5 more)

### Community 126 - "无状态 reconciler（CQRS 投影 + 推进）"
Cohesion: 0.20
Nodes (10): 机制四：CAS(pending→running) 控严格并发, events 表（append-only 真值日志，写模型）, 机制二：平台侧退出观察者（从 STOPPED 事件读 exitCode）, 机制三：HWM 条件写 + 状态机单调条件写, job timeout（两层声明 → definition 载体 → 三路推进器 enforce）, kicker Lambda（runs 表 Stream 冷启动）, 无状态 reconciler（CQRS 投影 + 推进）, RunState 物化读视图（唯一写者 = reconciler） (+2 more)

### Community 127 - "Skill Deploy Token Guardrail"
Cohesion: 0.20
Nodes (11): _build(), _deploy_spans(), _nodes(), ArgumentParser, agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…, `cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…, 前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…, 子动词路径 → 该节点声明的 `--flag` 集（`()` = `gherkai <verb>` 本身）。 (+3 more)

### Community 128 - "03-midscene-grounding.ts"
Cohesion: 0.22
Nodes (9): ADR-0010, src/lib/agentcore-sigv4.mts — SigV4 与 region 解析, BASE_URL, MODEL_CONFIG, REGION, ADR-0033, createOpenAIClient 注入点, sigv4Fetch 自定义 fetch (+1 more)

### Community 129 - "render_skill_contract.py"
Cohesion: 0.26
Nodes (11): _assert_clean(), main(), _paragraphs(), RuntimeError, 按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。, 转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。, 源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。, 纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。 (+3 more)

### Community 130 - "test_user_facing_messages.py"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, _scan_midscene(), _scan_python() (+2 more)

### Community 131 - "release.yml — 发布全链工作流"
Cohesion: 0.10
Nodes (25): 使用方 (Consumer) vs contributor, 部署 provider (deploy provider), 部署方 (Deployer), 确定性 step 注册表, 跑法权限梯 (Execution tiers), 点名检查 vs 确定性锚点, feature 作者 (Feature author / QA), 柔性冒烟 (Flexible smoke) (+17 more)

### Community 132 - "_MissingThenStoppedEcs"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在 = 写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 133 - "_job_with"
Cohesion: 0.36
Nodes (8): map_origin_in_jobs(), 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable(), test_map_replaces_step_text_prefix()

### Community 134 - "gherkai_runtime/names.py"
Cohesion: 0.08
Nodes (31): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_worker_template_path(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的… (+23 more)

### Community 135 - "user_steps.py"
Cohesion: 0.13
Nodes (17): steps 加载 fail-loud 不静默降级, src/index.mts — 包公开 API, src/worker/deterministic.mts — 确定性注册表, src/worker/deterministic.steps.mts — 内建脚手架 step, src/worker/user-steps.mts — 使用方 steps 加载, _ensure_ns_package(), _is_step_file(), _module_name() (+9 more)

### Community 136 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 137 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 138 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 139 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 140 - "section"
Cohesion: 0.70
Nodes (4): main(), `## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。, render(), section()

### Community 141 - "文档健康度复盘（全部项目文档）— 任务说明"
Cohesion: 0.13
Nodes (15): Status 头（第二层的配套：枚举、判定与连带审计）, 为什么做（价值）, 产出与提交, 何时做（触发）, 六类问题（分类找）, 已知失败形态（规则的来历，只读）, 执行方法（多轮复盘验证过的最佳路径）, 按文档类型的复盘侧重（用对判据） (+7 more)

### Community 142 - "部署与维护云端后端"
Cohesion: 0.15
Nodes (13): deploy 与 destroy 的选项, VPC 的三种取值, worker 镜像 variant, 前置要求, 后端包含什么, 团队成员需要的最小云端权限, 拆除与清理, 版本与升级 (+5 more)

### Community 143 - "ECS Task Timing Capture"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 144 - "exit_observer.py"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 145 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 146 - "常见问题"
Cohesion: 0.14
Nodes (14): AI 做出的判定能当回归门禁吗？同一条用例会不会今天过、明天不过？, 一个 AWS 账号里能同时运行 stage 和 prod 两套后端吗？, 什么时候该从本机运行换成云端后端？, 几十条用例运行一轮大概多久？能同时执行几条？, 同一批用例在本机和在云端运行，结果会一样吗？, 和 Playwright、Cucumber 是什么关系？现有用例能迁过来吗？, 它在什么浏览器里运行？能测移动端视口，或换成 Firefox、Safari 吗？, 常见问题 (+6 more)

### Community 147 - "Graph Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 148 - "_doc_rules.py"
Cohesion: 0.12
Nodes (20): bare_flags(), clean_flag(), CommandSpan, extract_command_spans(), NamedTuple, Path, 使用者面 markdown 的共享规则与扫描器：多处护栏共用的**单一事实源**。…, 抽出 `gherkai …` 形态的代码跨。行号按跨在原文里的位置算，报错时能直接点到人。 (+12 more)

### Community 149 - "运行测试与查看结果"
Cohesion: 0.20
Nodes (10): 两个独立的选择：怎么运行、在哪运行, 命令, 在 CI 里运行, 常用选项（`run` / `submit`）, 机读输出, 看失败原因：`explain`, 结果在哪, 费用量级 (+2 more)

### Community 150 - "_FakeEcs"
Cohesion: 0.17
Nodes (10): _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped() (+2 more)

### Community 151 - "测本机或内网里的被测应用"
Cohesion: 0.22
Nodes (9): 前置：ngrok 与 authtoken, 存活时间上限：`--tunnel-ttl S`, 安全, 工作方式, 常见故障, 测本机或内网里的被测应用, 用法, 限制 (+1 more)

### Community 152 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 153 - "排错"
Cohesion: 0.15
Nodes (13): 云端后端, 仍未定位到原因时, 先运行 gherkai doctor, 其它以退出码 2 结束的错误, 凭证与 region, 各行查什么, 安装与版本, 引擎与判定 (+5 more)

### Community 154 - "_SeqEcs"
Cohesion: 0.16
Nodes (10): FargateWorkerHandle, 一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error() (+2 more)

### Community 155 - "权威信息源（自查用）"
Cohesion: 0.25
Nodes (8): Agent Skills（见 ADR 0043）, AWS Bedrock / AgentCore, Midscene（任意页加 `.md` 取 markdown）, Nova Act, 发行与打包（见 ADR 0037）, 常用 CLI（本项目实测用到）, 权威信息源（自查用）, 镜像与 ECS 交付（见 ADR 0038）

### Community 156 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 158 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 159 - "_FakeSink"
Cohesion: 0.20
Nodes (4): captured(), _FakeSink, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 160 - "05-negative-assertions.ts"
Cohesion: 0.33
Nodes (5): BASE_URL, Check, MODEL_CONFIG, REGION, ADR-0033

### Community 161 - "test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine"
Cohesion: 0.13
Nodes (10): CountingEcs, boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。, ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。, 架构判据在**任何 ECR/ECS 动作之前**拦下（ADR 0038 步 2：把 Fargate 启动期的 `exec format error` 提前）。…, 重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…, 模板没变（deploy 重新运行的常态）→ 一次模板 describe 都不打：判定只用映射里记的模板 ARN。, Spy, test_arch_mismatch_exits_2_before_touching_ecr_or_ecs() (+2 more)

### Community 162 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 163 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 164 - "开始使用"
Cohesion: 0.22
Nodes (9): AWS 前置, 上手路径一：交给 AI agent, 上手路径二：自己敲命令, 下一步, 安装, 开始使用, 按角色选安装形态, 用 doctor 自检 (+1 more)

### Community 166 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 167 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 168 - "start_tunnel_for_jobs"
Cohesion: 0.40
Nodes (5): 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

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

### Community 175 - "_Calls"
Cohesion: 0.50
Nodes (3): _Calls, upload_file 调用记录：list 元素 = (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。, list

### Community 176 - "Skill Evaluation Design"
Cohesion: 0.67
Nodes (3): ADR 0043 skill 评测设计, 评分子代理提示词模板, skills/ 目录说明

### Community 177 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 179 - "ArtifactUploader"
Cohesion: 0.11
Nodes (13): ArtifactUploader, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 把文件交给后台队列顺序上传（**不阻塞调用方**）；no-op 时直接返回。 调用点在 `step_done` **emit 之后**（ADR 0042…, 有界等队列传完（含在途那一项）：全部处理完 True，超时 False（剩下的交给 flush 兜）。 收尾（scope 末 /…, 队列线程主体：FIFO 逐个传，**绝不因单项失败而死**（死了 = 后面的截图全不传且无人察觉）。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 本机 no-op 路径：截图就在本地，队列/排空都是直接返回（不起线程、不碰 boto3）。 (+5 more)

### Community 180 - "决策"
Cohesion: 0.14
Nodes (14): 0045. 文档分层与归位：按读者三分类、目录归位、包页面降为入口页、每版 changelog、按类别定口吻, 一、读者三分类，使用者侧 AI agent 归用户文档, 七、图统一用 archify：JSON 图源 + 导出 SVG 入库，只有发布到 Pages 的交互版才入库 HTML, 三、包页面降为入口页（反转 0039 面二的「完整操作手册」）, 与 agent skill 的关系（0043 不变）, 二、目录归位, 五、每版 changelog，Release 正文与链接钉 tag, 八、`CONTEXT.md` 是严格词表，术语变更自上而下 (+6 more)

### Community 181 - "执行与推进模型导览：run / submit × local / cloud"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的生命周期, 4. 后台运行 `submit` 的生命周期, 4a. local 后端：per-run 推进进程, 4b. cloud 后端：三 Lambda 链, 4c. 读侧：进度观察与结果落点, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 183 - "contributor 指南"
Cohesion: 0.18
Nodes (11): contributor 指南, Spike（可独立运行的技术验证脚本）, 发布与版本, 在有凭证的机器上验证未发布的工作树, 如何参与, 开发环境（从 checkout 运行）, 文档去哪读, 测试 (+3 more)

### Community 185 - "代码健康度复盘（全部生产代码）— 任务说明"
Cohesion: 0.18
Nodes (11): 三类问题（分类找）, 为什么做（价值）, 产出与提交, 代码健康度复盘（全部生产代码）— 任务说明, 何时做（触发）, 分片深读（可用 workflow 并行）, 对抗验证, 执行方法（本项目跑通的最佳路径） (+3 more)

### Community 186 - "cli.py"
Cohesion: 0.06
Nodes (41): cdk_command(), check_cdk(), check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_ssm_client(), _make_sts_client() (+33 more)

### Community 187 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 195 - "配置：环境变量与通用选项"
Cohesion: 0.18
Nodes (11): AWS 访问与云端资源名, 云端资源名与网络的单项覆盖, 使用者可设的环境变量, 引擎行为, 模型选择, 由 gherkai 注入的环境变量, 跨命令通用选项, 部署机 (+3 more)

### Community 206 - "error-text.mts"
Cohesion: 0.67
Nodes (3): errorText(), ADR-0042, oneLineError()

### Community 208 - "wire.py"
Cohesion: 0.05
Nodes (57): Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上运行一个讲 ADR…, _join_pumps(), _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。 (+49 more)

### Community 209 - "detached.py"
Cohesion: 0.15
Nodes (12): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。 (+4 more)

### Community 212 - "_events_table_actions"
Cohesion: 0.17
Nodes (12): _advancer_stmts(), _events_table_actions(), parametrize, 某角色对 events **表**（不含其 Stream）的全部授权动作。Stream 语句另算：那是事件源订阅，不是表数据面。, 退出观察者对 events 表**只 PutItem**：events 是 append-only 的判定真值日志，观察者只追加 task_exited、…, 两个推进器对 events 表 = **读 + PutItem**，不得有 Update/Delete/BatchWrite。 读：重放该 run…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉… (+4 more)

### Community 213 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 216 - "stop_tunnel"
Cohesion: 0.40
Nodes (5): 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 220 - "test_lambda_handlers.py"
Cohesion: 0.06
Nodes (34): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。 (+26 more)

### Community 221 - "test_release_notes.py"
Cohesion: 0.29
Nodes (9): _mod(), Path, `.github/scripts/release_notes.py` 的行为护栏：gate 的「本 tag 在 CHANGELOG 里有节」与 Release…, 真 CHANGELOG.md 对照真值集：每个已发行 tag `vX.Y.Z` 都要有非空节；`## [Unreleased]` 要在。, test_cli_check_exit_codes(), test_render_pins_links_to_the_tag(), test_repo_changelog_has_every_released_tag_and_unreleased(), test_section_extracts_exactly_one_version() (+1 more)

### Community 222 - "runStep"
Cohesion: 0.50
Nodes (4): cumulativeTokens(), isTransientNetwork(), runStep(), stepCost()

### Community 223 - "_tagged_feature"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号 = 任一命中；重复 --tags = 都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 退 2 并列全部候选（id 标题），别静默运行空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope = 报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>；…, _tagged_feature() (+7 more)

### Community 224 - "test_read_events_scope_done_waits_for_stopped_before_reading_exit"
Cohesion: 0.33
Nodes (6): _delayed_stopped_ecs(), **「scope_done 后轮询等 STOPPED 再读码」的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR…, 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order(), test_read_events_scope_done_waits_for_stopped_before_reading_exit()

### Community 225 - "test_finished_run_gate_keys_on_the_committed_run_status_only"
Cohesion: 0.29
Nodes (7): 已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…, 对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…, 超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…, _report_bytes(), test_finished_run_gate_keys_on_the_committed_run_status_only(), test_finished_run_is_not_reprojected_by_a_late_or_replayed_event(), test_timeout_payload_on_a_finished_run_is_a_noop()

### Community 227 - "_CdkWritingContext"
Cohesion: 0.19
Nodes (13): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, Path, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。 (+5 more)

### Community 228 - "gherkai CLI 的 `--json` 字段契约"
Cohesion: 0.20
Nodes (10): `evidence` 的固定键, gherkai CLI 的 `--json` 字段契约, `gherkai deploy list-workers --json`, `gherkai doctor --json`, `gherkai explain <run_id> [<scope_id>] --json`, `gherkai list-deterministic --engine <名> --json`, `gherkai list-engines --json`, `gherkai plan … --json` (+2 more)

### Community 230 - "check_version_skew"
Cohesion: 0.07
Nodes (29): check_version_skew(), is_pure_release(), PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, _release_cmp() (+21 more)

### Community 231 - "判定的计算路径：从单次投票到退出码"
Cohesion: 0.20
Nodes (10): 1. 四层归约：票 → step → scenario → job → run, 2. 七个状态：含义与处置, 3. 两根正交的轴与 `error_type` 类别集, 3a. `status` × `shortcircuited`, 3b. `error_type`：赋值方与取值, 3c. job 收场态与 `error_type`：归因的优先级, 4. severity：数值序而非字母序；run 级为何不含 skipped/aborted, 5. 退出码：各命令的语义不同 (+2 more)

### Community 232 - "SubprocessLauncher"
Cohesion: 0.20
Nodes (7): Event, Job, SubprocessEngine, 驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, SubprocessLauncher, Timer

### Community 233 - "04-planning-probe.ts"
Cohesion: 0.50
Nodes (3): BASE_URL, main(), ADR-0033

### Community 234 - "test_user_docs.py"
Cohesion: 0.09
Nodes (34): changelog_unreleased(), CHANGELOG 交给退役词表与口头语表扫的部分 = 截到第一个已发行版本节之前。…, _default_model_claims(), _default_model_ids(), parametrize, Path, 仓库内用户文档的护栏：`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`（ADR 0045 决策一 /…, docs/diagrams/<name>.json（图源）与 <name>.svg（导出）成对：缺任一半即漂（HTML 不入库，由 JSON 现场构建）。 (+26 more)

### Community 238 - "云端后端由哪些载体组成：一次改动要传播到哪几处才生效"
Cohesion: 0.25
Nodes (8): 1. 五个载体, 2. 行为归属哪个载体（改动前的定位表）, 3. 一次版本升级的传播顺序，以及顺序为何不可调换, 4. 症状 → 该推哪个载体, 5. `submit` 在提交时刻固定下来的内容, 6. 一个 prefix = 一套环境；多版本并存依靠多 prefix, 7. 延伸阅读, 云端后端由哪些载体组成：一次改动要传播到哪几处才生效

### Community 239 - "一条确定性 step 的生命周期：从写下正则到云端命中"
Cohesion: 0.25
Nodes (8): 0. 全景：四段路径，一张注册表, 1. 派发决策链：一条 step 文本进入 worker 之后, 2. 三个入口，一张表：为什么清单、标注、实际执行不可能分叉, 3. 两个真值源、一个岔口：为什么「改了 steps，云端没变」是设计, 4. 响亮失败：症状 → 原因 → 处置, 5. 两引擎对称，与一处已知缺口, 6. 延伸阅读, 一条确定性 step 的生命周期：从写下正则到云端命中

### Community 240 - "_run_with_refs"
Cohesion: 0.23
Nodes (14): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3() (+6 more)

### Community 242 - "架构总览：五层结构、一次 run 的生命周期、包与发行物"
Cohesion: 0.29
Nodes (7): 1. 全景图, 2. 五层各自的职责, 3. 一次 run 的生命周期, 4. 本机与云端：同一条链的两种载体, 5. 包与发行物, 6. 延伸阅读, 架构总览：五层结构、一次 run 的生命周期、包与发行物

### Community 243 - "产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）"
Cohesion: 0.29
Nodes (7): 1. 五类产物，各回答一个问题, 2. 物理位置：local 与 cloud 是同一棵树的两种载体, 3. 证据链的串接, 4. 一次失败的三步读法, 5. 边界（有意取舍，非遗漏）, 6. 延伸阅读, 产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）

### Community 246 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性 step 脚手架（ADR 0020/0022）—— **本包内建**的示范 step，随 worker 发行。 用途：少数"必须精确、不容 AI…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言…, url_matches()

### Community 250 - "aws"
Cohesion: 0.67
Nodes (3): aws(), _aws_env(), fixture

### Community 254 - "is_placeholder"
Cohesion: 0.29
Nodes (8): is_placeholder(), `<命令>` / `…` / `[<scope_id>]` 这类占位符不是子命令名，解析路径时跳过、不当拼错。, _allowed_flags(), 只认**同一个反引号代码跨**内的 `gherkai <子命令> … --flag` 组合，逐对对照该 subparser 的真 flag 集。…, 裸词序列 → 子命令路径。第一个词不是已知子命令且不是占位符 → None（拼错的子命令）。, 路径上（含各级祖先）声明的 flag 全集——`deploy --prefix p push-worker …` 这种父层给法是合法的。, _resolve(), test_flags_are_attached_to_the_right_subcommand()

### Community 258 - "container.py"
Cohesion: 0.29
Nodes (6): ContainerError, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。, UnsupportedContainerEngine

### Community 260 - "test_worker_subnets_single_source_across_ssm_and_lambda_env"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 261 - "stack.py"
Cohesion: 0.29
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（= `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 262 - "ImageInfo"
Cohesion: 0.29
Nodes (5): ImageInfo, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。, test_target_platform_judgement()

### Community 271 - ".inspect"
Cohesion: 0.33
Nodes (4): 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。, _tail()

### Community 273 - "digest_for_repo"
Cohesion: 0.40
Nodes (5): digest_for_repo(), 从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。…, 基础镜像同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def**…, test_digest_none_when_repo_absent_or_empty(), test_digest_picked_by_repo_not_first_entry()

### Community 277 - "CloudTarget"
Cohesion: 0.50
Nodes (3): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序=链上顺序。

### Community 313 - "_patch_skew"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 同款的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 340 - "JobState"
Cohesion: 0.06
Nodes (78): JobState, 单个 job 的控制面运行态（执行后才有）。, 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), _argument_from_dict(), _argument_to_dict(), from_dict(), job_from_dict() (+70 more)

## Ambiguous Edges - Review These
- `ADR 0001 范围限定英文 UI` → `gherkai agent SKILL.md`  [AMBIGUOUS]
  docs/adr/0001-scope-limited-to-english-ui.md · relation: references
- `成功重试对 RunResult 透明（可观测性缺口）` → `上传成功后删本地`  [AMBIGUOUS]
  docs/adr/0029-engine-artifacts-to-s3.md · relation: conceptually_related_to

## Knowledge Gaps
- **574 isolated node(s):** `1. 心智模型：两种驱动、同一份 `core``, `2. 四组合一览`, `3. 前台 `run` 的生命周期`, `4a. local 后端：per-run 推进进程`, `4b. cloud 后端：三 Lambda 链` (+569 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **120 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ADR 0001 范围限定英文 UI` and `gherkai agent SKILL.md`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `成功重试对 RunResult 透明（可观测性缺口）` and `上传成功后删本地`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `_fixture()` connect `_fixture` to `test_lambda_asset.py`, `S3StepArgumentOffloader`, `deterministic.py`, `_RecUploader`, `test_evidence.py`, `test_interrupt_model.py`, `_FakeSink`?**
  _High betweenness centrality (0.203) - this node is a cross-community bridge._
- **Why does `gherkai-worker-novaact (README)` connect `Midscene Worker 开发笔记` to `deterministic.py`, `user_steps.py`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `Nova Act Worker 开发笔记` connect `Midscene Worker 开发笔记` to `runtime 包 contributor 文档`, `CONTRIBUTING.md`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 27 INFERRED edges - model-reasoned connections that need verification._