# Graph Report - yaozhou  (2026-09-09)

## Corpus Check
- 227 files · ~203,265 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4036 nodes · 9049 edges · 231 communities (164 shown, 67 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 600 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8e03284a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- JobResult
- Job
- Worker Image Management
- Cloud Backend CLI Tests
- CLI Run Entry Tests
- S3ResultStore
- Container Worker Push Tests
- Container Engine Adapter
- test_reconcile.py
- Provider
- RunState
- _FakeEcsClient
- StepDone
- test_stack.py
- compose.py
- Status
- Deploy Command Shell
- test_schedule.py
- test_stores.py
- test_worker_variant.py
- run_scope.py
- test_cloud_reconcile.py
- test_plan.py
- _engine
- Execution Architecture Decisions
- Artifact S3 Upload
- test_lifecycle_states.py
- cli.py
- RunPersistence
- core/DEVELOPMENT.md
- 六、具名提纯审计记录（审计集 40 ADR + CONTEXT = 41 份）
- gherkai_runtime/names.py
- test_project.py
- test_run_step.py
- Nova Engine Probes
- test_conditional_writes.py
- deterministic.py
- ._run_cdk
- test_interrupt_model.py
- _is_transient_network
- BackendStack
- agentcore-sigv4.mts
- test_user_steps.py
- test_lambda_asset.py
- test_lambda_handlers.py
- _stream_record
- Domain Glossary
- test_compose.py
- run-scope.mts
- ._guard_vpc_spec
- reconciler.py
- gherkai_worker_novaact/__init__.py
- _progress
- Packaging & Distribution ADR
- TypeScript Config
- test_job_source.py
- Tunnel CLI Tests
- test_deterministic.py
- test_event_sink.py
- Deploy Docs
- FargateEngine
- Cloud Test Fixtures
- user-steps.mts
- reconcile.tick（无状态推进一步，四宿主共用）
- 代码健康度复盘任务说明
- user_steps.py
- Step Argument Assembly
- WorkerNotFoundError
- Backend Version Stamp
- Worker Image ADR
- _classify_act_error
- Tunnel Host Watchdog
- test_package_readmes.py
- _deploy_provider
- run-scope.test.mts
- JS Dependencies
- gherkai deploy push-worker（八步流程）
- deterministic.mts
- test_subprocess_engine.py
- Cloud Store Composition
- _scenario_to_json
- Event Wallclock Analysis
- .add_arguments
- CDK Invocation Tests
- Deploy Provider Discovery
- _render_status
- tunnel.py
- deterministic_steps.py
- _CdkWritingContext
- Timeout Handling Tests
- NPM Package Manifest
- test_tunnel.py
- _FakeEcs
- _resolve_steps_dir
- LocalReportStore
- 0039. 用户可见面不带内部指代：产品文案与文档分层
- check_version_skew
- _FakeResult
- Release & CI Setup
- CLI Contributor Docs
- test_wire.py
- _argv
- ECS Exit Observer Extraction
- Execution & Progression Model Guide
- Worker Package Dev Notes
- S3StepArgumentOffloader
- Fake Event Sink Fixtures
- test_user_facing_messages.py
- AWS Client Stubs (CFN/SSM)
- ArtifactUploader
- 开发笔记（contributor）
- _DeterministicCtx
- Nova Act Worker README
- Fake Sink Test Doubles
- CI & Release Workflows
- AWS Deploy Contributor Guide
- test_provider.py
- 一、提纯提案待批（40 条；approve_reduced 的请按「复核缩小后的改法」落）
- Task Definition Cleanup
- ADR 0035 Local App Tunnel
- Worker Signal Interrupt Tests
- ECS Task Timing Script
- events_table
- render.py
- 0040. 使用方角色模型与术语
- ADR 0036 Deterministic Capability
- Dist Metadata Check
- map_origin_in_jobs
- Graphify Refresh Script
- _isolate
- stop_tunnel
- Contributor Entry Docs
- event-sink.mts
- Fake DynamoDB Table
- SqliteEventLog
- ADR-0033
- Runtime Package README
- argument.mts
- ADR 0018 Common Steps
- test_kicker_timeout_path_builds_once
- exit_observer.py
- Fake S3 Client
- Echo Test Worker
- Cloud Test Infra Selfcheck
- test_build_takes_meta_max_concurrency_under_cap
- TypeScript Dev Dependencies
- test_fargate_engine.py
- Skew Gate Test Patching
- Core Package Docs
- test_read_events_scope_done_waits_for_stopped_before_reading_exit
- Live Run Revision References
- Worker Subnet Single Source
- AWS Client Call Spy
- NPM Package Files
- Repository Metadata
- Runtime Contributor Docs
- deterministic.steps.mts
- Cloud Env Fixture
- AWS Env Fixture
- Fargate Engine Wiring
- NPM Scripts
- AgentCore CDP Spike
- JobSource
- Bedrock AgentCore SDK
- DynamoDB SDK
- Run Meta Spy
- Adapters Package Init
- test_build_raises_when_legacy_definition_unresolvable
- Core Package Init
- test_handler_skips_when_no_run_id
- gherkai_cli/__main__.py
- Unimplemented Delete Worker
- Revision Lineage Tags
- artifact-upload.test.mts
- ADR Language Split Decisions
- OpenAI Dependency
- tsx Dependency
- Index Wait Script
- Workspace Package Identity
- Argument Parser
- _seed_worker_ssm
- Run Result
- Run Result
- Job Result
- Run Meta
- Run Result
- Job Result
- Run Meta
- Run Result
- Run Meta
- Run Meta
- Subprocess Engine
- Knowledge Graph Output
- Version Single Source
- Worker-Core Protocol
- ADR 0007 Login Escape Hatch
- ADR 0008 SigV4 Auth
- ADR 0012 Planning Model Reuse
- ADR 0014 AI Assertion Voting
- Flaky Page Transient Actions
- Retired Cucumber Patch ADR
- DynamoDB Run Store
- Engine Resolver
- Path
- Shared Gherkin Feature Files
- Job Sink
- Local Run Store
- Test Parametrization
- Gherkai Core Package
- AWS Deployment Package
- Gherkai Runtime Package
- NovaAct Worker Package
- Report Store
- Result Store
- Run State
- Run Store Interface
- Run Metadata
- Subprocess Engine
- Sink Interface
- SQLite Event Log
- Status Enum
- start_tunnel_for_jobs
- act 边界即时抢传
- Exception
- BaseException
- _runs_stream_record
- 文档健康度复盘第五轮 — 待批报告
- _FakeSchedulerClient

## God Nodes (most connected - your core abstractions)
1. `main()` - 137 edges
2. `Job` - 117 edges
3. `RunMeta` - 107 edges
4. `RunState` - 104 edges
5. `Status` - 93 edges
6. `JobState` - 85 edges
7. `Provider` - 80 edges
8. `JobResult` - 72 edges
9. `schedule()` - 63 edges
10. `Scenario` - 62 edges

## Surprising Connections (you probably didn't know these)
- `worker_cmd()` --calls--> `resolve_worker_cmd()`  [INFERRED]
  tools/e2e_harness.py → runtime/gherkai_runtime/compose.py
- `run()` --calls--> `job_to_line()`  [INFERRED]
  tools/e2e_harness.py → core/gherkai_core/wire.py
- `_UnavailableEngine` --uses--> `Engine`  [INFERRED]
  runtime/gherkai_runtime/compose.py → core/gherkai_core/ports.py
- `WorkerNotFoundError` --uses--> `Engine`  [INFERRED]
  runtime/gherkai_runtime/compose.py → core/gherkai_core/ports.py
- `WorkerResolution` --uses--> `Engine`  [INFERRED]
  runtime/gherkai_runtime/compose.py → core/gherkai_core/ports.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **健康度复盘体系（code / doc 分工 + 外部来源自查）** — docs_code_health_review, docs_doc_health_review, docs_references, docs_doc_health_review_purification_audit [EXTRACTED 0.80]
- **cloud 后台跑批事件驱动链（kicker → worker → events → reconciler → exit-observer）** — docs_adr_0034_kicker, docs_adr_0034_reconciler_lambda, docs_adr_0034_exit_observer, docs_adr_0033_backend_stack, docs_adr_0033_build_fargate_engines [EXTRACTED 0.85]
- **core ports 的 adapter 族（组合根注入）** — core_gherkai_core_ports, core_gherkai_core_adapters_subprocess_engine, core_gherkai_core_adapters_fargate_engine, core_gherkai_core_adapters_cloud_launcher, runtime_gherkai_runtime_compose [EXTRACTED 0.85]
- **AWS 后端供给流程（VPC 档比对 + worker 镜像 variant + 版本戳）** — deploy_aws_readme, deploy_aws_readme_vpc_tiers, deploy_aws_readme_version_stamp, deploy_aws_readme_push_worker [EXTRACTED 0.85]
- **通用 step 原语在两引擎间的对称映射与边界** — docs_adr_0018_generic_steps_capability_abstract_primitives, docs_adr_0018_generic_steps_capability_engine_symmetry, docs_adr_0018_generic_steps_capability_negative_verification, docs_adr_0018_generic_steps_capability_phrasing_ambiguity_risk, docs_adr_0018_generic_steps_capability_deterministic_anchor [EXTRACTED 0.85]
- **v1.0 核心三模块流水线：协议 → plan → schedule → RunReport** — docs_adr_0024_worker_core_protocol_streaming_events, docs_adr_0025_plan_module_feature_to_jobs_plan, docs_adr_0026_schedule_module_schedule, docs_adr_0027_runreport_aggregation_index_run_report [EXTRACTED 0.85]
- **版本单旋钮贯穿分发链（git tag → 包/镜像 tag/SSM 戳 → skew → variant 解析）** — docs_adr_0037_uv_workspace, docs_adr_0037_skew_check, docs_adr_0037_gherkai_deploy, docs_adr_0038_image_tag, docs_adr_0038_variant, docs_adr_0038_default_pointer [EXTRACTED 0.85]
- **Ports & Adapters：四个 port 由组合根注入具体 adapter** — docs_adr_0016_execution_architecture_core_lib_run_model_engine_port, docs_adr_0016_execution_architecture_core_lib_run_model_run_store, docs_adr_0016_execution_architecture_core_lib_run_model_result_store, docs_adr_0016_execution_architecture_core_lib_run_model_report_store, docs_adr_0016_execution_architecture_core_lib_run_model_composition_root_injection [EXTRACTED 0.90]
- **实时写落库链：on_job_complete → ResultStore → RunStore → ReportStore（commit point）** — docs_adr_0030_realtime_persistence_seam_job_sink, docs_adr_0030_realtime_persistence_seam_run_persistence, docs_adr_0030_realtime_persistence_seam_commit_point, docs_adr_0016_execution_architecture_core_lib_run_model_result_store, docs_adr_0016_execution_architecture_core_lib_run_model_run_store, docs_adr_0016_execution_architecture_core_lib_run_model_report_store [EXTRACTED 0.90]
- **版本单旋钮驱动的发布链** — _github_workflows_release_build, _github_workflows_release_pypi, _github_workflows_release_npm, _github_workflows_release_images, _github_workflows_release_release, context_single_version_knob [EXTRACTED 0.90]
- **无状态跑批推进流（events → tick → launcher）** — core_gherkai_core_project, core_gherkai_core_reconcile, core_gherkai_core_adapters_cloud_launcher, deploy_aws_gherkai_deploy_aws_lambdas_reconciler, deploy_aws_gherkai_deploy_aws_lambdas_exit_observer, runtime_gherkai_runtime_detached, context_advancer [EXTRACTED 0.90]
- **无状态跑批四机制协同（独立键空间 / 平台侧退出观察 / 条件写 / CAS 并发闸）** — docs_adr_0034_task_exited, docs_adr_0034_exit_observer, docs_adr_0034_hwm_conditional_write, docs_adr_0034_cas_claim, docs_adr_0034_tick [EXTRACTED 0.90]

## Communities (231 total, 67 thin omitted)

### Community 0 - "JobResult"
Cohesion: 0.04
Nodes (54): Ports 层（Engine/RunStore/ResultStore/ReportStore/EventLog/Launcher）, JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, 一次执行的机器可读汇总判定 = **definition（run_meta）+ 判定（jobs）的显式合成**（ADR 0016/0026）。…, RunResult, Engine, EngineResolver, JobSink (+46 more)

### Community 1 - "Job"
Cohesion: 0.06
Nodes (71): CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, Job, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。, 一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。, 一个 job = 一个 scope = 一个会话边界 = schedule 交给单个 worker 的活（ADR 0016/0024/0025）。 (+63 more)

### Community 2 - "Worker Image Management"
Cohesion: 0.05
Nodes (93): Aws, _cell(), cleanup_pass(), CleanupOutcome, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+85 more)

### Community 3 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (93): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, local run 的 definition 不带这两个字段（omit-when-None，ADR 0038「local 档不写」）。, 后端默认指针本身是个非法 variant 名（部署侧写坏）→ 退 2 并点名那个 SSM 参数，不冒 traceback。 显式 `--worker-…, patch store 钩子 + preflight（默认放行）+ 版本 skew 闸 + worker variant 闸（都默认放行）返回记录调用的… (+85 more)

### Community 4 - "CLI Run Entry Tests"
Cohesion: 0.05
Nodes (88): main(), _capturing_schedule(), _det_feature(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json… (+80 more)

### Community 5 - "S3ResultStore"
Cohesion: 0.19
Nodes (7): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore

### Community 6 - "Container Worker Push Tests"
Cohesion: 0.07
Nodes (76): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+68 more)

### Community 7 - "Container Engine Adapter"
Cohesion: 0.04
Nodes (54): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+46 more)

### Community 8 - "test_reconcile.py"
Cohesion: 0.10
Nodes (30): EventLog, Launcher, Job, Protocol, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 local = 起 subprocess worker（事件旁路落 SQLite…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick() (+22 more)

### Community 9 - "Provider"
Cohesion: 0.09
Nodes (41): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _parse(), 留口子：退 2 并说清「押后的是回收策略」，而不是让人只看到 argparse 的 invalid choice。, CLI 皮没交版本 → 本包自报 dist 版本（`==` lockstep pin 成同一个，不引入第二个真源）。, 凭证/权限/网络故障 → 退 2 + 一句话（对用户是「先修凭证」，与 Node 缺失同一档），不抛 traceback。, 走**真 parser**、按真实接线顺序拼（皮先声明命令面 flag，provider 再贴自己的旋钮）——不用 SimpleNamespace 手捏…, cdk 成功 → 接着跑 worker 镜像第 2/3/4 步（第 1 步随 cdk 事务，ADR 0038）。 (+33 more)

### Community 10 - "RunState"
Cohesion: 0.04
Nodes (88): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), LocalRunStore, Path, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新… (+80 more)

### Community 11 - "_FakeEcsClient"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 12 - "StepDone"
Cohesion: 0.11
Nodes (41): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+33 more)

### Community 13 - "test_stack.py"
Cohesion: 0.06
Nodes (59): make_template(), Template, Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳… (+51 more)

### Community 14 - "compose.py"
Cohesion: 0.05
Nodes (56): subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "subnets") 的便捷形式）。, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, ssm_subnets_path(), ssm_version_path(), _find_worker_spec(), is_botocore_error(), is_pure_release(), _make_ecr_client() (+48 more)

### Community 15 - "Status"
Cohesion: 0.05
Nodes (39): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与… (+31 more)

### Community 16 - "Deploy Command Shell"
Cohesion: 0.07
Nodes (44): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 __main__（argparse 皮）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+36 more)

### Community 17 - "test_schedule.py"
Cohesion: 0.22
Nodes (48): 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+40 more)

### Community 18 - "test_stores.py"
Cohesion: 0.05
Nodes (82): render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, _sample_run(), test_render_text_annotates_shortcircuited_step(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_no_annotation_on_plain_failed(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar(), LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个… (+74 more)

### Community 19 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (51): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。 值 =…, worker_image_key(), aws(), _fake_aws_creds(), _push_image(), fixture, worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest/模板 ARN 供打印。 (+43 more)

### Community 20 - "run_scope.py"
Cohesion: 0.09
Nodes (30): ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_traj_refs(), _backoff_interrupted(), _collect_traj(), _cost_from_result(), _get_uploader(), log() (+22 more)

### Community 21 - "test_cloud_reconcile.py"
Cohesion: 0.07
Nodes (42): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。… (+34 more)

### Community 22 - "test_plan.py"
Cohesion: 0.07
Nodes (57): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig, Job (+49 more)

### Community 23 - "_engine"
Cohesion: 0.12
Nodes (32): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+24 more)

### Community 24 - "Execution Architecture Decisions"
Cohesion: 0.07
Nodes (41): 决策 A：cli --backend {local,cloud} 单旋钮, compose.build_local_stores / build_cloud_stores, 组合根注入（选实现不由 module 自选）, 核心库窄腰 core/（解析→分组→调度→收集，零引擎依赖）, 决策 B：subprocess + 注入云存储 = 内部预演手段, 决策 C：Fargate/region/profile 配置走 CLI 参数注入, Engine port（run_scope(job) → 事件流）, FargateEngine（云端执行 adapter） (+33 more)

### Community 25 - "Artifact S3 Upload"
Cohesion: 0.08
Nodes (29): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→…, upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。 (+21 more)

### Community 26 - "test_lifecycle_states.py"
Cohesion: 0.09
Nodes (18): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), FakeWorkerHandle, Event (+10 more)

### Community 27 - "cli.py"
Cohesion: 0.07
Nodes (31): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, _error_code(), _make_cfn_client(), _make_ssm_client(), _make_sts_client(), _node_major(), Exception (+23 more)

### Community 28 - "RunPersistence"
Cohesion: 0.09
Nodes (30): ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+22 more)

### Community 29 - "core/DEVELOPMENT.md"
Cohesion: 0.21
Nodes (31): gherkai CLI 使用者页面, adapters/_boto.py 依赖守卫, core 测试说明（单测 vs 集成）, 绿≠对 Verification Escalation, ADR 0004 Nova Act IAM 鉴权, ADR 0005 用例描述层用单一共享 .feature, ADR 0011 AgentCore 浏览器：默认 vs 自建, ADR 0013 跨引擎共享边界止于 features/ (+23 more)

### Community 30 - "六、具名提纯审计记录（审计集 40 ADR + CONTEXT = 41 份）"
Cohesion: 0.05
Nodes (38): CONTEXT.md · proposal（6 提案）, docs/adr/0001-scope-limited-to-english-ui.md · proposal（2 提案）, docs/adr/0002-midscene-not-driven-by-gpt55.md · none（0 提案）, docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md · none（0 提案）, docs/adr/0004-novaact-iam-auth-via-workflow.md · proposal（2 提案）, docs/adr/0005-single-shared-feature-file.md · none（0 提案）, docs/adr/0006-form-a-two-subprojects-no-orchestrator.md · none（0 提案）, docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md · proposal（2 提案） (+30 more)

### Community 31 - "gherkai_runtime/names.py"
Cohesion: 0.08
Nodes (31): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_worker_template_path(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, 模板 revision ARN 的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。写者 = stack 资源。 (+23 more)

### Community 32 - "test_project.py"
Cohesion: 0.05
Nodes (84): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, ScopeStarted, Action, _aggregate(), EventRecord (+76 more)

### Community 33 - "test_run_step.py"
Cohesion: 0.18
Nodes (24): 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, _run_step(), _done(), _FakeNova, _run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。 与 Midscene 引擎 run-scope.test.ts…, 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。, 注入 fake：act_get 按布尔序列逐票回；act/go_to_url 记调用。act 可设异常模拟中途失败。 tw_seq：每票…, _step() (+16 more)

### Community 34 - "Nova Engine Probes"
Cohesion: 0.10
Nodes (25): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+17 more)

### Community 35 - "test_conditional_writes.py"
Cohesion: 0.09
Nodes (39): _initial(), _meta(), fixture, RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。 (+31 more)

### Community 36 - "deterministic.py"
Cohesion: 0.15
Nodes (14): clear(), DeterministicConflict, _Entry, _hits(), list_registry(), match_batch(), 确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+6 more)

### Community 37 - "._run_cdk"
Cohesion: 0.11
Nodes (16): cdk_command(), check_node(), Path, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…, 凡要合成 app 的动作（deploy / diff / synth / destroy）都必须有 `--vpc`（无隐式默认，ADR 0037 决策 6）；… (+8 more)

### Community 38 - "test_interrupt_model.py"
Cohesion: 0.10
Nodes (24): _aggregate(), _emit_scenario_done_unless_stopped(), scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…, _run_scenario(), _FakeResult, _Meta, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM… (+16 more)

### Community 39 - "_is_transient_network"
Cohesion: 0.14
Nodes (28): _is_transient_network(), 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是…, 造一个 botocore ClientError（response 里带 Error.Code /…, _target_closed(), test_agentcore_permanent_wrapping_chain_not_transient() (+20 more)

### Community 40 - "BackendStack"
Cohesion: 0.10
Nodes (17): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+9 more)

### Community 41 - "agentcore-sigv4.mts"
Cohesion: 0.20
Nodes (12): BASE_URL, main(), makePng(), REGION, main(), main(), getBaseUrl(), getRegion() (+4 more)

### Community 42 - "test_user_steps.py"
Cohesion: 0.12
Nodes (28): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。, 真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。… (+20 more)

### Community 43 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (25): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, make_stack(), **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), fixture, Path (+17 more)

### Community 44 - "test_lambda_handlers.py"
Cohesion: 0.09
Nodes (21): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。, definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。, meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。 (+13 more)

### Community 45 - "_stream_record"
Cohesion: 0.15
Nodes (13): scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, _stream_record(), test_reconciler_noop_for_non_detached_run(), test_reconciler_ticks_detached_run() (+5 more)

### Community 46 - "Domain Glossary"
Cohesion: 0.09
Nodes (27): CONTEXT.md 领域术语表, 推进器 advancer, AgentCore 浏览器会话, 确定性断言 vs AI 断言, 两个引擎都子进程 + 薄 worker, 执行核心库窄腰, 成本可观测, 部署 provider（gherkai.deploy entry point） (+19 more)

### Community 47 - "test_compose.py"
Cohesion: 0.04
Nodes (75): build_engines(), engine_min_grace(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 no_artifacts（`--no-…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。 (+67 more)

### Community 48 - "run-scope.mts"
Cohesion: 0.08
Nodes (34): ADR-0014, ADR-0019, ADR-0020, ADR-0022, ADR-0026, ADR-0027, ADR-0031, ADR-0032 (+26 more)

### Community 49 - "._guard_vpc_spec"
Cohesion: 0.15
Nodes (9): 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 **不做版本 skew…, flag → CDK context（app/stack 侧读的那四个旋钮 + 版本戳）。 `--vpc` 一个 flag 摊成两个旋钮：`default`…, deploy 前的 VPC 档比对。放行 → None；拦 → 退出码（2）。 只在 deploy 前跑（见 `diff`/`destroy` 的…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR… (+1 more)

### Community 50 - "reconciler.py"
Cohesion: 0.12
Nodes (21): _build(), EventBridgeTimeoutWatch, _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING… (+13 more)

### Community 51 - "gherkai_worker_novaact/__init__.py"
Cohesion: 0.16
Nodes (12): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, 进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，回归哨兵）。 被…, _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings() (+4 more)

### Community 52 - "_progress"
Cohesion: 0.16
Nodes (21): _cmd_run(), _cmd_submit(), _load_and_plan(), _preflight_worker_runtimes(), _progress(), `_resolve_steps_dir` + cloud 档清零（ADR 0037 决策 4）：cloud 档 steps…, 本次 plan 用到的各引擎：worker 运行时能否定位 + （给了 steps 目录时）能否完成自述（ADR 0037 决策 3/4）。 - 定位链四级全…, plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。 成功返回 `Job[]`；任一前置失败返回**退出码… (+13 more)

### Community 53 - "Packaging & Distribution ADR"
Cohesion: 0.08
Nodes (24): 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel, 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条, 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵, 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra, 2d. `requires-python >=3.13` 维持, 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）, 决策 1：交付物按打包技术划分，worker 运行时是硬核, 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first (+16 more)

### Community 54 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 55 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 56 - "Tunnel CLI Tests"
Cohesion: 0.13
Nodes (22): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+14 more)

### Community 57 - "test_deterministic.py"
Cohesion: 0.16
Nodes (19): deterministic(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。, description/example 必填（ADR 0036：注册即暴露，缺元数据 = 能力不可发现，fail-loud）。, --list-deterministic 自述模式（ADR 0036）真子进程：不读 stdin、输出 JSON、含脚手架真锚点。 (+11 more)

### Community 58 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 59 - "Deploy Docs"
Cohesion: 0.12
Nodes (20): worker 镜像：基底 / variant / 默认指针, gherkai-deploy-aws, gherkai deploy push-worker, 后端版本戳与三步升级, VPC 三档与四态档位比对, VPC 三档, 安装与前置, 帮助 (+12 more)

### Community 60 - "FargateEngine"
Cohesion: 0.14
Nodes (14): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+6 more)

### Community 61 - "Cloud Test Fixtures"
Cohesion: 0.13
Nodes (20): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), fixture, 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -… (+12 more)

### Community 62 - "user-steps.mts"
Cohesion: 0.13
Nodes (9): ADR-0037, ADR-0022, ADR-0036, collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, STEP_EXTS, BIN (+1 more)

### Community 63 - "reconcile.tick（无状态推进一步，四宿主共用）"
Cohesion: 0.12
Nodes (19): _aggregate（run 级 status 聚合）, _NON_VERDICT 过滤名单, StepResult.shortcircuited（正交布尔）, Status enum（加 SKIPPED/ABORTED/PENDING/RUNNING）, _STATUS_SEVERITY 数值序, StepSkipped 事件（step 级短路）, TERMINAL_STATUSES（终态真源，取补）, stopTimeout=120 / grace 预算标定 (+11 more)

### Community 64 - "代码健康度复盘任务说明"
Cohesion: 0.13
Nodes (19): Lambda handler 入口（lambdas/）, ADR 0001 框架范围限定为英文 UI, ADR 0002 不用 gpt-5.5, ADR 0003 Qwen3-VL 定位, ADR 0009 最大化使用 AWS 是硬前提, ADR 0010 spike 作对标基准, ADR 0024 engine 只报原生量、core 不折美元, ADR 0026 纯 reducer 不臆断因果 (+11 more)

### Community 65 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 66 - "Step Argument Assembly"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 67 - "WorkerNotFoundError"
Cohesion: 0.08
Nodes (27): _ask_worker(), build_local_stores(), match_deterministic(), prune_empty_dirs(), Path, RuntimeError, query_deterministic(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。… (+19 more)

### Community 68 - "Backend Version Stamp"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, "version")`，由 stack 资源随部署事务写入，ADR 0037 决策 6）。…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。 (+10 more)

### Community 69 - "Worker Image ADR"
Cohesion: 0.11
Nodes (19): 0038. worker 镜像交付：基底、variant 与推送注册, `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）, `push-worker` 流程, SSM 参数与命名真源, 不变量, 与版本升级的交互, 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）, 多版本与多环境 (+11 more)

### Community 70 - "_classify_act_error"
Cohesion: 0.22
Nodes (9): BaseException, _classify_act_error(), _is_transient_client_error(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, test_classify_guardrail(), test_classify_network_beats_sdk_type(), test_classify_timeout() (+1 more)

### Community 71 - "Tunnel Host Watchdog"
Cohesion: 0.15
Nodes (18): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, Σ(各 job 预算) + 启动余量——求和对任何并发取值都是保守上界（ADR 0034 机制四）。 (+10 more)

### Community 72 - "test_package_readmes.py"
Cohesion: 0.12
Nodes (16): CLAUDE.md 项目约定, 代码纪律（绿≠对 / 接口诚实）, 文档纪律（ADR / CONTEXT / journey / guides）, 工作方式（tools/ 复用、AWS 开发期免费）, parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, contributor 内容有明确去处（不是被删掉）：根目录与每个包目录各一份 DEVELOPMENT.md。 (+8 more)

### Community 73 - "_deploy_provider"
Cohesion: 0.33
Nodes (6): _cmd_deploy(), _cmd_destroy(), _deploy_provider(), 取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…, [部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。皮零 IaC 知识。 退出码即 provider…, [部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。

### Community 74 - "run-scope.test.mts"
Cohesion: 0.11
Nodes (8): fromSource, hookSpec, ADR-0024, ADR-0028, _events, fakePage, importMod(), testSink

### Community 75 - "JS Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 76 - "gherkai deploy push-worker（八步流程）"
Cohesion: 0.12
Nodes (19): BackendStack 资源清单（DDB/S3/ECS/IAM/SSM/Lambda）, 两层命名：prefix 批量默认 + 单资源覆盖, preflight fail-fast（探资源存在性、点名 prefix）, task role IAM 最小权限（动作 × 资源两维收窄）, VPC 来源三档（复用/默认/建新，零 NAT）, RunMeta.extra_http_headers（额外请求头通道）, 隧道宿主三形态 + TTL 兜底, TunnelProvider 口子（首个实现 ngrok） (+11 more)

### Community 77 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 78 - "test_subprocess_engine.py"
Cohesion: 0.22
Nodes (18): Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。, SubprocessEngine, _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, _rm() (+10 more)

### Community 79 - "Cloud Store Composition"
Cohesion: 0.14
Nodes (16): build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…, boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。 (+8 more)

### Community 80 - "_scenario_to_json"
Cohesion: 0.33
Nodes (6): _argument_to_json(), Scenario, Step, StepArgument, _scenario_to_json(), _step_to_json()

### Community 81 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 82 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 83 - "CDK Invocation Tests"
Cohesion: 0.13
Nodes (12): cdk(), _clean_aws_env(), _FakeEngine, fixture, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。… (+4 more)

### Community 84 - "Deploy Provider Discovery"
Cohesion: 0.16
Nodes (13): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。, 按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,… (+5 more)

### Community 85 - "_render_status"
Cohesion: 0.17
Nodes (18): _cmd_status(), cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…, 渲染 RunState + pending 诊断提示 + 退出码——**local/cloud 共享一份**（保两路一致，ADR 0034）。 state…, [无状态跑批] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run…, _render_status(), _status_cloud(), _args(), _mk_state() (+10 more)

### Community 86 - "tunnel.py"
Cohesion: 0.15
Nodes (12): 本地应用暴露 / 隧道（--expose-local）, gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…, _gen_auth(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。 (+4 more)

### Community 87 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。 用途：少数"必须精确、不容 AI 抖动"的断言（如…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言…, url_matches()

### Community 88 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 89 - "Timeout Handling Tests"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 90 - "NPM Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 91 - "test_tunnel.py"
Cohesion: 0.15
Nodes (16): NgrokTunnel, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, TunnelInfo, _fake_popen_writing_log(), _FakeProc, tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。… (+8 more)

### Community 92 - "_FakeEcs"
Cohesion: 0.15
Nodes (7): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

### Community 93 - "_resolve_steps_dir"
Cohesion: 0.50
Nodes (4): _cmd_list_deterministic(), 解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认…, 按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern 语义（ADR…, _resolve_steps_dir()

### Community 94 - "LocalReportStore"
Cohesion: 0.06
Nodes (65): ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。, collect_report_index(), _fmt_ms(), _local_path(), LocalReportStore, Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出… (+57 more)

### Community 95 - "0039. 用户可见面不带内部指代：产品文案与文档分层"
Cohesion: 0.15
Nodes (13): 产品文案禁内部指代（AST 护栏）, README / DEVELOPMENT 按读者分层, ADR 0039: 用户可见面不带内部指代, 0039. 用户可见面不带内部指代：产品文案与文档分层, 代价与权衡, 决策, 对既有文档与 code 的影响, 护栏 (+5 more)

### Community 96 - "check_version_skew"
Cohesion: 0.09
Nodes (22): check_version_skew(), variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `_is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, _release_cmp(), _release_key(), _variant_miss_hint() (+14 more)

### Community 97 - "_FakeResult"
Cohesion: 0.15
Nodes (6): _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, test_run_scenario_shortcircuits_after_error()

### Community 98 - "Release & CI Setup"
Cohesion: 0.15
Nodes (13): 1. PyPI 占名（先于一切）, 2. PyPI trusted publisher × 5（只有真发行的五个需要）, 3. npm trusted publisher（免 token，无 secret）, 4. GHCR：首次推送后把两个 package 改成 public, 5. 仓库本身必须是 public, CI 与发布链（`.github/`）, `release.yml` 的 job 图与重跑语义, TestPyPI 演练（推正式 tag 之前排一次） (+5 more)

### Community 99 - "CLI Contributor Docs"
Cohesion: 0.17
Nodes (12): cli 包 —— contributor 文档, plan 的实现细节, RunReport 内部, VPC 档比对（三态）, 为何拆 `submit` / `status`, 从 checkout 跑, 实时落库, 模块 (+4 more)

### Community 100 - "test_wire.py"
Cohesion: 0.06
Nodes (43): 执行引擎 port（Engine）, _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+35 more)

### Community 101 - "_argv"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证， 不会跑…, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 102 - "ECS Exit Observer Extraction"
Cohesion: 0.17
Nodes (12): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, container 缺 exitCode（宽限态）→ None（机制二保守）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, _stopped_detail(), test_exit_observer_records_exit_for_detached_run(), test_exit_observer_skips_non_detached_run() (+4 more)

### Community 103 - "Execution & Progression Model Guide"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的一生, 4. 后台跑批 `submit` 的一生, 4a. local 档：per-run 推进进程, 4b. cloud 档：三 Lambda 链, 4c. 读侧：进度怎么看、结果落在哪, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 104 - "Worker Package Dev Notes"
Cohesion: 0.17
Nodes (12): 从本 checkout 跑, 使用方 `steps/` 的加载（实现要点）, 依赖分类（踩过的坑）, 包身份, 容器镜像（维护者向）, 布局, 开发笔记（contributor）, 执行形态：薄 worker（cucumber 已退役） (+4 more)

### Community 105 - "S3StepArgumentOffloader"
Cohesion: 0.19
Nodes (7): 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, S3StepArgumentOffloader

### Community 106 - "Fake Event Sink Fixtures"
Cohesion: 0.17
Nodes (7): captured(), _FakeSink, fixture, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。, _reset_stop()

### Community 107 - "test_user_facing_messages.py"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, _scan_midscene(), _scan_python() (+2 more)

### Community 108 - "AWS Client Stubs (CFN/SSM)"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 109 - "ArtifactUploader"
Cohesion: 0.17
Nodes (6): ADR-0016, ADR-0033, ArtifactUploader, ADR-0024, ADR-0028, ADR-0029

### Community 110 - "开发笔记（contributor）"
Cohesion: 0.18
Nodes (11): 容器镜像（维护者向）, 开发笔记（contributor）, 执行形态：薄 worker（pytest-bdd 已退役）, 报告落点, 环境, 相关 ADR, 确定性 step：内建脚手架 vs 使用方的 `steps/`, 跑 spike（可独立跑，不进 wheel） (+3 more)

### Community 112 - "Nova Act Worker README"
Cohesion: 0.18
Nodes (11): gherkai-worker-novaact README, 定制 worker 镜像携带 steps 到云端, 纯 IAM 鉴权与显式 region, 响亮失败策略（不静默降级）, Nova Act trajectory 产物, Worker 四级定位链 (novaact), Nova Act Worker Process, e2e_harness 使用说明 (+3 more)

### Community 113 - "Fake Sink Test Doubles"
Cohesion: 0.18
Nodes (5): captured(), _FakeSink, fixture, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 114 - "CI & Release Workflows"
Cohesion: 0.33
Nodes (10): ci.yml 工作流, CI 与发布链说明, release.yml 发布链, release build job（gate + uv build）, release images job（GHCR 基底镜像）, release npm job（@gherkai/worker-midscene）, release pypi job（attest + uv publish）, release GitHub Release job (+2 more)

### Community 115 - "AWS Deploy Contributor Guide"
Cohesion: 0.20
Nodes (10): gherkai-deploy-aws — contributor 手册, Lambda 打包（`stack._build_lambda_asset`）, worker 镜像命令族, 事件驱动推进（无状态跑批）, 包定位与发现面, 命名真源, 本地验证（不碰 AWS）, 模块布局 (+2 more)

### Community 116 - "test_provider.py"
Cohesion: 0.10
Nodes (25): classify_vpc_state(), 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, SSM 里记的生效档 `stored` 是否 == 本次 `--vpc requested`。 三档形态见…, vpc_spec_matches(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, flag 面全集钉死（枚举型护栏）：三个 context 旋钮 flag + AWS 定位二件套 + 两个「皮的中立版的 AWS 精确化」（见 cli…, 子动词全集钉死（枚举型护栏）+ **只挂 deploy**。 挂到 destroy 上不是「多个没用的命令」而是危险：皮的 destroy 分派不看… (+17 more)

### Community 117 - "一、提纯提案待批（40 条；approve_reduced 的请按「复核缩小后的改法」落）"
Cohesion: 0.10
Nodes (20): CONTEXT.md, docs/adr/0004-novaact-iam-auth-via-workflow.md, docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md, docs/adr/0011-agentcore-browser-system-default-vs-custom.md, docs/adr/0014-ai-first-assertions.md（单独 agent 审计，独立复核 approve_reduced）, docs/adr/0016-execution-architecture-core-lib-run-model.md, docs/adr/0017-cloud-execution-fargate-over-runtime.md, docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md (+12 more)

### Community 118 - "Task Definition Cleanup"
Cohesion: 0.20
Nodes (5): datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 119 - "ADR 0035 Local App Tunnel"
Cohesion: 0.20
Nodes (10): 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器, 1. `TunnelProvider` 可插拔口子（`gherkai-runtime` 组合根共享层），首个实现 = ngrok, 2. URL 映射：feature 写原始地址，组装 job 时替换, 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态, 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）, 决策, 背景与问题, 被拒/被缓方案（护栏） (+2 more)

### Community 120 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 121 - "ECS Task Timing Script"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 122 - "events_table"
Cohesion: 0.67
Nodes (3): events_table(), fixture, events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——P4 单独建，schema 见 ADR 0033/0024。

### Community 123 - "render.py"
Cohesion: 0.13
Nodes (19): _cmd_plan(), _probe_deterministic_dispatch(), plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…, plan 预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…, _arg_hint(), _cost_bits(), _dispatch_hint(), _ms() (+11 more)

### Community 124 - "0040. 使用方角色模型与术语"
Cohesion: 0.20
Nodes (10): 0040. 使用方角色模型与术语, 代价, 决策 1：四顶帽子与正名, 决策 2：帽子不是人, 决策 3：执行是正交轴——跑法权限梯, 决策 4：边界矩阵, 决策 5：术语单一真源与立新角色的门槛, 影响 (+2 more)

### Community 125 - "ADR 0036 Deterministic Capability"
Cohesion: 0.22
Nodes (9): 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询, 1. 注册面扩元数据（暴露的前提）, 2. worker 自述：`--list-deterministic` dump 模式, 3. CLI 子命令 `list-deterministic --engine <name>`, 4. plan 命中标注：「我写的这句会不会命中」, 决策, 背景与问题, 被拒方案（护栏） (+1 more)

### Community 126 - "Dist Metadata Check"
Cohesion: 0.39
Nodes (8): fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。, wheel_metadata()

### Community 127 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 128 - "Graphify Refresh Script"
Cohesion: 0.28
Nodes (8): GRAPHIFY_API_TIMEOUT, GRAPHIFY_BEDROCK_MODEL, GRAPHIFY_LLM_TEMPERATURE, GRAPHIFY_MAX_OUTPUT_TOKENS, PYTHONHASHSEED, graphify_refresh.sh script, step(), usage()

### Community 129 - "_isolate"
Cohesion: 0.67
Nodes (3): _isolate(), fixture, 注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。

### Community 130 - "stop_tunnel"
Cohesion: 0.29
Nodes (7): cleanup_tunnel(), 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 131 - "Contributor Entry Docs"
Cohesion: 0.25
Nodes (8): Spike（可独立跑的技术验证脚本）, 发布与版本, 开发环境（从 checkout 跑）, 开发者指南（contributor 入口）, 文档去哪读, 测试, 现状与版本线, 目录结构

### Community 132 - "event-sink.mts"
Cohesion: 0.32
Nodes (3): ADR-0034, EventSink, resolveEventsFd()

### Community 134 - "SqliteEventLog"
Cohesion: 0.09
Nodes (21): Connection, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。 (+13 more)

### Community 135 - "ADR-0033"
Cohesion: 0.11
Nodes (11): ADR-0010, BASE_URL, MODEL_CONFIG, REGION, BASE_URL, main(), BASE_URL, Check (+3 more)

### Community 136 - "Runtime Package README"
Cohesion: 0.29
Nodes (6): gherkai-runtime, 主要入口, 安装, 最小用法：在本机跑完一批, 注意, 相关

### Community 137 - "argument.mts"
Cohesion: 0.53
Nodes (5): argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 138 - "ADR 0018 Common Steps"
Cohesion: 0.33
Nodes (6): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）

### Community 140 - "exit_observer.py"
Cohesion: 0.27
Nodes (9): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+1 more)

### Community 142 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 145 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 146 - "test_fargate_engine.py"
Cohesion: 0.14
Nodes (22): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env(), _stopped_resp() (+14 more)

### Community 147 - "Skew Gate Test Patching"
Cohesion: 0.50
Nodes (4): _patch_skew(), --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_wait_cloud_kicker_missing_fails_fast()

### Community 148 - "Core Package Docs"
Cohesion: 0.50
Nodes (4): core 包 —— contributor 文档, 实际执行（跑 .feature）, 模块, 跑测试

### Community 149 - "test_read_events_scope_done_waits_for_stopped_before_reading_exit"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), **option-c 定义行为的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR 0032 结论…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_scope_done_waits_for_stopped_before_reading_exit()

### Community 150 - "Live Run Revision References"
Cohesion: 0.50
Nodes (4): _non_terminal_statuses(), 未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…, 有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…, _referenced_by_live_run()

### Community 151 - "Worker Subnet Single Source"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 153 - "NPM Package Files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 154 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 155 - "Runtime Contributor Docs"
Cohesion: 0.50
Nodes (4): runtime 包 —— contributor 文档, 从 checkout 跑 / 测试, 模块, 相关 ADR

### Community 156 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 157 - "Cloud Env Fixture"
Cohesion: 0.67
Nodes (3): cloud_env(), fixture, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。

### Community 158 - "AWS Env Fixture"
Cohesion: 0.67
Nodes (3): aws(), _aws_env(), fixture

### Community 159 - "Fargate Engine Wiring"
Cohesion: 0.67
Nodes (3): build_fargate_engines（组合根接线）, container 名契约 {engine}-worker, 两个 worker 镜像（Nova / Midscene 各一）

### Community 160 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 162 - "JobSource"
Cohesion: 0.25
Nodes (3): ADR-0016, Job, JobSource

### Community 170 - "gherkai_cli/__main__.py"
Cohesion: 0.11
Nodes (23): _build_parser(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_list_engines(), _cmd_reconcile(), _cmd_tunnel_watch(), _dist_version(), _installed_version() (+15 more)

### Community 180 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 222 - "start_tunnel_for_jobs"
Cohesion: 0.29
Nodes (7): 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 227 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 228 - "文档健康度复盘第五轮 — 待批报告"
Cohesion: 0.33
Nodes (5): 三、UNCERTAIN（1 条，方法文档范围枚举，请裁定）, 二、主观发现待批（5 条）, 五、对抗验证驳回的客观发现（8 条，存档）, 四、红线复核否决的提纯提案（26 条，存档不落改）, 文档健康度复盘第五轮 — 待批报告

### Community 232 - "_FakeSchedulerClient"
Cohesion: 0.29
Nodes (5): _FakeSchedulerClient, create_schedule 记录器（含 exceptions.ConflictException 形状，兼容 boto3 client 异常访问路径）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, test_timeout_watch_conflict_is_idempotent(), test_timeout_watch_creates_one_time_schedule()

## Knowledge Gaps
- **421 isolated node(s):** `ADR-0029`, `ADR-0016`, `ADR-0024`, `ADR-0033`, `ADR-0028` (+416 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **67 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Status` connect `Status` to `JobResult`, `Job`, `Worker Image Management`, `Fake DynamoDB Table`, `SqliteEventLog`, `test_reconcile.py`, `RunState`, `StepDone`, `Fake S3 Client`, `test_schedule.py`, `test_stores.py`, `test_fargate_engine.py`, `test_cloud_reconcile.py`, `test_lifecycle_states.py`, `RunPersistence`, `test_project.py`, `test_conditional_writes.py`, `reconciler.py`, `Tunnel Host Watchdog`, `test_subprocess_engine.py`, `Timeout Handling Tests`, `_FakeEcs`, `LocalReportStore`, `test_wire.py`, `_FakeSchedulerClient`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `test_act_non_network_is_engine_error()` connect `test_run_step.py` to `BackendStack`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `schedule()` connect `test_schedule.py` to `JobResult`, `Job`, `test_project.py`, `BackendStack`, `StepDone`, `test_subprocess_engine.py`, `test_lifecycle_states.py`, `RunPersistence`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `RunMeta` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunMeta` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `Status` (e.g. with `_FakeS3` and `_FakeTable`) actually correct?**
  _`Status` has 41 INFERRED edges - model-reasoned connections that need verification._