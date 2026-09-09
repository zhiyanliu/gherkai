# Graph Report - yaozhou  (2026-09-09)

## Corpus Check
- 228 files · ~200,582 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4069 nodes · 8581 edges · 282 communities (177 shown, 105 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 415 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `105c7042`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ScheduleOpts
- Job
- workers.py
- test_backend_cloud.py
- main
- test_lifecycle_states.py
- Container Worker Push Tests
- test_container.py
- test_reconcile.py
- Provider
- serialize.py
- preflight_cloud_resources
- Job
- test_stack.py
- gherkai_runtime/names.py
- test_schedule.py
- test_deploy_cmd.py
- schedule
- model.py
- test_worker_variant.py
- run_scope.py
- CloudLauncher
- scope.py
- test_fargate_engine.py
- Execution Architecture Decisions
- Artifact S3 Upload
- project.py
- app.py
- RunPersistence
- core/DEVELOPMENT.md
- test_stores.py
- fargate_engine.py
- project
- test_run_step.py
- Nova Engine Probes
- test_conditional_writes.py
- deterministic.py
- ._run_cdk
- test_interrupt_model.py
- _is_transient_network
- BackendStack
- test_sqlite_event_log.py
- test_user_steps.py
- test_lambda_asset.py
- test_lambda_handlers.py
- _stream_record
- CONTEXT.md 领域术语表
- query_deterministic
- main
- test_plan.py
- reconciler.py
- gherkai_worker_novaact/__init__.py
- test_projected_run_status_pending_only_while_all_jobs_pending
- Packaging & Distribution ADR
- TypeScript Config
- test_job_source.py
- test_tunnel_cli.py
- test_deterministic.py
- test_event_sink.py
- deploy_aws/README.md
- FargateEngine
- S3StepArgumentOffloader
- user-steps.mts
- reconcile.tick（无状态推进一步，四宿主共用）
- test_cloud_reconcile.py
- user_steps.py
- Step Argument Assembly
- build_local_reconcile
- _StampSsm
- Worker Image ADR
- SqliteEventLog
- test_tunnel_host.py
- test_package_readmes.py
- _cmd_list_engines
- run-scope.test.mts
- JS Dependencies
- gherkai deploy push-worker（八步流程）
- deterministic.mts
- test_subprocess_engine.py
- build_fargate_engines
- report_store/local.py
- Event Wallclock Analysis
- .add_arguments
- CDK Invocation Tests
- deploy.py
- _args
- tunnel.py
- deterministic_steps.py
- _CdkWritingContext
- _FakeEcs
- NPM Package Manifest
- test_tunnel.py
- _DeterministicCtx
- _FakeEcs
- LocalReportStore
- 0039. 用户可见面不带内部指代：产品文案与文档分层
- check_version_skew
- _FakeResult
- Release & CI Setup
- CLI Contributor Docs
- test_wire.py
- _ssm_params
- _stopped_detail
- Execution & Progression Model Guide
- Worker Package Dev Notes
- BaseException
- Fake Event Sink Fixtures
- test_user_facing_messages.py
- AWS Client Stubs (CFN/SSM)
- ArtifactUploader
- 开发笔记（contributor）
- test_s3_report_store.py
- Nova Act Worker README
- Fake Sink Test Doubles
- CI & Release Workflows
- AWS Deploy Contributor Guide
- cli.py
- start_tunnel_for_jobs
- Task Definition Cleanup
- ADR 0035 Local App Tunnel
- Worker Signal Interrupt Tests
- ECS Task Timing Script
- StepResult
- render_plan_text
- 0040. 使用方角色模型与术语
- ADR 0036 Deterministic Capability
- Dist Metadata Check
- _job_with
- Graphify Refresh Script
- _isolate
- stop_tunnel
- Contributor Entry Docs
- event-sink.mts
- RunStore
- SubprocessEngine
- agentcore-sigv4.mts
- Runtime Package README
- ADR-0024
- ADR 0018 Common Steps
- _FakeSchedulerClient
- exit_observer.py
- Fake S3 Client
- Echo Test Worker
- Cloud Test Infra Selfcheck
- RuntimeError
- TypeScript Dev Dependencies
- _SeqEcs
- 代码健康度复盘任务说明
- Core Package Docs
- _TrajNova
- _referenced_by_live_run
- Worker Subnet Single Source
- ContainerError
- NPM Package Files
- Repository Metadata
- Runtime Contributor Docs
- deterministic.steps.mts
- cloud_env
- AWS Env Fixture
- Fargate Engine Wiring
- NPM Scripts
- AgentCore CDP Spike
- job-source.mts
- Bedrock AgentCore SDK
- DynamoDB SDK
- test_run_state_timestamps_share_one_format
- Adapters Package Init
- compose.py
- Core Package Init
- test_detached_launcher.py
- .preflight
- .delete_worker
- classify_vpc_state
- artifact-upload.test.mts
- ADR Language Split Decisions
- OpenAI Dependency
- tsx Dependency
- Index Wait Script
- Workspace Package Identity
- Argument Parser
- _seed_run
- e2e_harness.py
- reconcile.py
- Job Result
- Run Meta
- Run Result
- EventBridgeTimeoutWatch
- ADR-0033
- _patch_skew
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
- raise_for_worker_exit
- Engine Resolver
- events_table
- Shared Gherkin Feature Files
- Job Sink
- Local Run Store
- test_compose.py
- Gherkai Core Package
- AWS Deployment Package
- Gherkai Runtime Package
- NovaAct Worker Package
- Report Store
- Result Store
- _FakeTable
- 03-midscene-grounding.ts
- Run Metadata
- Subprocess Engine
- Sink Interface
- SQLite Event Log
- 05-negative-assertions.ts
- fixture
- parametrize
- test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions
- BaseException
- subprocess_engine.py
- gherkai_cli/__init__.py
- ._installed_import_source
- .records
- gherkai_cli/__main__.py
- detached.py
- _runs_stream_record
- .record_exit
- test_final_drain_paginates_across_last_evaluated_key
- test_provider_module_does_not_import_aws_cdk
- _cmd_tunnel_watch
- Job
- Job
- Popen
- act 边界即时抢传
- Job
- Protocol
- no-artifacts.test.mts
- Job
- Job
- Scenario
- Step
- Engine
- FeatureSource
- Path
- Job
- Event
- JobResult
- JobState
- RunResult
- RunState
- Status
- Protocol
- Exception
- ADR-0019
- ADR-0020
- ADR-0022
- ADR-0026
- ADR-0027
- ADR-0032
- ADR-0035
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- CONNECT_BACKOFF_MS
- ADR-0014
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0031
- ADR-0036
- ADR-0037
- Scenario
- ShutdownDeps
- Step

## God Nodes (most connected - your core abstractions)
1. `main()` - 141 edges
2. `Provider` - 82 edges
3. `Job` - 69 edges
4. `schedule()` - 62 edges
5. `CollectSink` - 60 edges
6. `RunState` - 58 edges
7. `FakeEngine` - 56 edges
8. `FakeResolver` - 53 edges
9. `RunMeta` - 52 edges
10. `Scenario` - 50 edges

## Surprising Connections (you probably didn't know these)
- `_build()` --calls--> `CloudLauncher`  [INFERRED]
  deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py → core/gherkai_core/adapters/cloud_launcher.py
- `_event_log()` --calls--> `DdbEventLog`  [INFERRED]
  deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py → core/gherkai_core/adapters/event_log/ddb.py
- `_build()` --calls--> `DdbEventLog`  [INFERRED]
  deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py → core/gherkai_core/adapters/event_log/ddb.py
- `_submit_local()` --calls--> `SqliteEventLog`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/event_log/sqlite.py
- `_timeout_built()` --calls--> `SqliteEventLog`  [INFERRED]
  deploy_aws/tests/test_lambda_handlers.py → core/gherkai_core/adapters/event_log/sqlite.py

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

## Communities (282 total, 105 thin omitted)

### Community 0 - "ScheduleOpts"
Cohesion: 0.10
Nodes (27): EngineResolver, JobSink, Event, ports 层（ADR 0016 六边形架构）：核心只依赖这些接口，具体 adapter 由组合根注入。 四个 port（关注点拆开，不揉成上帝…, 一个在跑的 worker 的句柄（schedule 持有，用于 stop）。 不暴露进程/信号细节——「怎么停」的机制藏在 adapter 内部（ADR…, 请求优雅停止：adapter 内部翻成具体机制；worker 收到后停会话、退出（ADR 0024 终止契约）。, 起一个 worker 跑这个 job，返回 (句柄, ADR 0024 事件流迭代器)。 事件流逐条产出（ADR 0024 流式）；迭代结束 = worker…, Sink (+19 more)

### Community 1 - "Job"
Cohesion: 0.09
Nodes (51): 一次性写完整态（= create_run 的两 item 一起 put；语义同 local save_run）。, RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐…, run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。 **写序…, _state_scalars(), Job, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。…, 一个 Gherkin step（已由 Compiler 展开、插值后的形状，ADR 0024/0025）。 (+43 more)

### Community 2 - "workers.py"
Cohesion: 0.05
Nodes (89): Aws, _cell(), cleanup_pass(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable() (+81 more)

### Community 3 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (93): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, local run 的 definition 不带这两个字段（omit-when-None，ADR 0038「local 档不写」）。, 后端默认指针本身是个非法 variant 名（部署侧写坏）→ 退 2 并点名那个 SSM 参数，不冒 traceback。 显式 `--worker-…, patch store 钩子 + preflight（默认放行）+ 版本 skew 闸 + worker variant 闸（都默认放行）返回记录调用的… (+85 more)

### Community 4 - "main"
Cohesion: 0.05
Nodes (94): main(), _capturing_schedule(), _det_feature(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json… (+86 more)

### Community 5 - "test_lifecycle_states.py"
Cohesion: 0.09
Nodes (17): RuntimeError, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), FakeWorkerHandle, Event, Job (+9 more)

### Community 6 - "Container Worker Push Tests"
Cohesion: 0.07
Nodes (76): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+68 more)

### Community 7 - "test_container.py"
Cohesion: 0.05
Nodes (49): ContainerEngine, digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+41 more)

### Community 8 - "test_reconcile.py"
Cohesion: 0.14
Nodes (26): RunMeta, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), _done_events(), FakeLauncher, _meta(), Job, reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。 用真… (+18 more)

### Community 9 - "Provider"
Cohesion: 0.07
Nodes (64): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _argv(), _parse(), _parse_destroy(), `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, flag 面全集钉死（枚举型护栏）：三个 context 旋钮 flag + AWS 定位二件套 + 两个「皮的中立版的 AWS 精确化」（见 cli…, 子动词全集钉死（枚举型护栏）+ **只挂 deploy**。 挂到 destroy 上不是「多个没用的命令」而是危险：皮的 destroy 分派不看… (+56 more)

### Community 10 - "serialize.py"
Cohesion: 0.07
Nodes (45): S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, JobResult (+37 more)

### Community 11 - "preflight_cloud_resources"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 13 - "test_stack.py"
Cohesion: 0.07
Nodes (47): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler/kicker）都要能读 `/{prefix}backend/*`（ADR 0038「权限面增量·云端推进器」）： 没有… (+39 more)

### Community 14 - "gherkai_runtime/names.py"
Cohesion: 0.09
Nodes (26): default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…, prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。, 引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称… (+18 more)

### Community 15 - "test_schedule.py"
Cohesion: 0.16
Nodes (35): Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…, ScenarioDone, ScenarioStarted, ScopeDone, StepDone (+27 more)

### Community 16 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 皮自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 17 - "schedule"
Cohesion: 0.19
Nodes (45): RunMeta, RunResult, 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->… (+37 more)

### Community 18 - "model.py"
Cohesion: 0.06
Nodes (52): DynamoDBRunStore, _job_state_from_item(), _job_state_to_item(), DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending… (+44 more)

### Community 19 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (47): aws(), _fake_aws_creds(), _push_image(), fixture, worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。 (+39 more)

### Community 20 - "run_scope.py"
Cohesion: 0.10
Nodes (27): ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_traj_refs(), _backoff_interrupted(), _collect_traj(), _cost_from_result(), _get_uploader(), log() (+19 more)

### Community 21 - "CloudLauncher"
Cohesion: 0.11
Nodes (19): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, _job(), CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。, job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job… (+11 more)

### Community 22 - "scope.py"
Cohesion: 0.10
Nodes (34): PlanError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, _index_ast_lines(), _map_argument(), parse_feature(), ParsedScenario, StepArgument (+26 more)

### Community 23 - "test_fargate_engine.py"
Cohesion: 0.11
Nodes (45): _delayed_stopped_ecs(), _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。 (+37 more)

### Community 24 - "Execution Architecture Decisions"
Cohesion: 0.07
Nodes (41): 决策 A：cli --backend {local,cloud} 单旋钮, compose.build_local_stores / build_cloud_stores, 组合根注入（选实现不由 module 自选）, 核心库窄腰 core/（解析→分组→调度→收集，零引擎依赖）, 决策 B：subprocess + 注入云存储 = 内部预演手段, 决策 C：Fargate/region/profile 配置走 CLI 参数注入, Engine port（run_scope(job) → 事件流）, FargateEngine（云端执行 adapter） (+33 more)

### Community 25 - "Artifact S3 Upload"
Cohesion: 0.08
Nodes (29): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→…, upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。 (+21 more)

### Community 26 - "project.py"
Cohesion: 0.09
Nodes (32): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…, _aggregate(), EventRecord, _job_status(), _lifecycle_rank(), project_full() (+24 more)

### Community 27 - "app.py"
Cohesion: 0.25
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（= `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 28 - "RunPersistence"
Cohesion: 0.08
Nodes (36): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, JobResult, Path, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。 (+28 more)

### Community 29 - "core/DEVELOPMENT.md"
Cohesion: 0.23
Nodes (29): core 测试说明（单测 vs 集成）, 绿≠对 Verification Escalation, ADR 0004 Nova Act IAM 鉴权, ADR 0005 用例描述层用单一共享 .feature, ADR 0011 AgentCore 浏览器：默认 vs 自建, ADR 0013 跨引擎共享边界止于 features/, ADR 0015 v1.0 定位：流程冒烟非精确回归, ADR 0016 执行架构 (+21 more)

### Community 30 - "test_stores.py"
Cohesion: 0.05
Nodes (60): RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, JobState, Path, RunMeta, RunState, Status (+52 more)

### Community 31 - "fargate_engine.py"
Cohesion: 0.20
Nodes (9): 执行引擎 port（Engine）, adapters/_boto.py 依赖守卫, events_pk(), Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, 一次 DescribeTasks 探测的结果——**两个正交事实各自命名**（ADR 0024「exitCode 落值延迟」）： -…, events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。, TaskProbe, test_events_pk_composite_run_id_scope_id() (+1 more)

### Community 32 - "project"
Cohesion: 0.08
Nodes (59): ScopeStarted, project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, _ev(), _exit(), _job(), _meta(), _passed_events() (+51 more)

### Community 33 - "test_run_step.py"
Cohesion: 0.15
Nodes (33): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+25 more)

### Community 34 - "Nova Engine Probes"
Cohesion: 0.10
Nodes (25): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+17 more)

### Community 35 - "test_conditional_writes.py"
Cohesion: 0.10
Nodes (36): _initial(), _meta(), RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+28 more)

### Community 36 - "deterministic.py"
Cohesion: 0.16
Nodes (13): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+5 more)

### Community 37 - "._run_cdk"
Cohesion: 0.07
Nodes (24): provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…, readonly_flag_conflict(), cdk_command(), _make_sts_client(), Path, boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。, 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC… (+16 more)

### Community 38 - "test_interrupt_model.py"
Cohesion: 0.10
Nodes (24): _aggregate(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…, _FakeResult, _Meta, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM… (+16 more)

### Community 39 - "_is_transient_network"
Cohesion: 0.13
Nodes (30): BaseException, _is_transient_client_error(), _is_transient_network(), boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+22 more)

### Community 40 - "BackendStack"
Cohesion: 0.11
Nodes (15): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+7 more)

### Community 41 - "test_sqlite_event_log.py"
Cohesion: 0.18
Nodes (16): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, 端到端：SQLite records() → project() 推出正确终态（两件都要齐 → passed）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。 (+8 more)

### Community 42 - "test_user_steps.py"
Cohesion: 0.12
Nodes (28): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。, 真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。… (+20 more)

### Community 43 - "test_lambda_asset.py"
Cohesion: 0.12
Nodes (23): make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), fixture, Path (+15 more)

### Community 44 - "test_lambda_handlers.py"
Cohesion: 0.10
Nodes (19): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。, 兼容路径解析不出的 run 只跳过它自己、不连坐同批其它 run：events Stream 一个 batch 含多个 run，抛出去 = ESM… (+11 more)

### Community 45 - "_stream_record"
Cohesion: 0.13
Nodes (15): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events…, _stream_record(), test_reconciler_noop_for_non_detached_run() (+7 more)

### Community 46 - "CONTEXT.md 领域术语表"
Cohesion: 0.08
Nodes (28): CONTEXT.md 领域术语表, 推进器 advancer, AgentCore 浏览器会话, 确定性断言 vs AI 断言, 两个引擎都子进程 + 薄 worker, 执行核心库窄腰, 成本可观测, 部署 provider（gherkai.deploy entry point） (+20 more)

### Community 47 - "query_deterministic"
Cohesion: 0.16
Nodes (15): _ask_worker(), match_deterministic(), Path, query_deterministic(), spawn 一次某引擎 worker 的**自述入口**、收一行 JSON（ADR 0036 决策 2/4 的共同机制）。 自述入口不建会话、不读 job、零…, 查询某引擎 worker 的确定性能力清单（ADR 0036）：spawn `worker --list-deterministic` 收 JSON。…, 批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…, 自述入口同样加载 steps 目录（ADR 0037 决策 4）→ steps_dir 经 env 注入，故 list-deterministic 的清单… (+7 more)

### Community 48 - "main"
Cohesion: 0.18
Nodes (9): cumulativeTokens(), isTransientNetwork(), log(), main(), runScenario(), runStep(), shutdownSequence(), stepCost() (+1 more)

### Community 49 - "test_plan.py"
Cohesion: 0.13
Nodes (28): PlanConfig, _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, `*` 步骤 type='Unknown'（gherkin 实测）→ PlanError,不静默兜底成 Given（假绿方向的错标）。, 无前驱非连接词的首条 And 同判不出 → PlanError;有前驱的 And 正常继承不受影响。, test_assertion_votes_default_is_one(), test_assertion_votes_from_config_propagates_to_all_jobs() (+20 more)

### Community 50 - "reconciler.py"
Cohesion: 0.14
Nodes (20): datetime, _build(), _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING… (+12 more)

### Community 51 - "gherkai_worker_novaact/__init__.py"
Cohesion: 0.16
Nodes (12): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, 进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，回归哨兵）。 被…, _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings() (+4 more)

### Community 53 - "Packaging & Distribution ADR"
Cohesion: 0.08
Nodes (24): 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel, 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条, 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵, 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra, 2d. `requires-python >=3.13` 维持, 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）, 决策 1：交付物按打包技术划分，worker 运行时是硬核, 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first (+16 more)

### Community 54 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 55 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 56 - "test_tunnel_cli.py"
Cohesion: 0.13
Nodes (22): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+14 more)

### Community 57 - "test_deterministic.py"
Cohesion: 0.14
Nodes (21): deterministic(), list_registry(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。 (+13 more)

### Community 58 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 59 - "deploy_aws/README.md"
Cohesion: 0.12
Nodes (20): worker 镜像：基底 / variant / 默认指针, gherkai-deploy-aws, gherkai deploy push-worker, 后端版本戳与三步升级, VPC 三档与四态档位比对, VPC 三档, 安装与前置, 帮助 (+12 more)

### Community 60 - "FargateEngine"
Cohesion: 0.18
Nodes (10): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+2 more)

### Community 61 - "S3StepArgumentOffloader"
Cohesion: 0.05
Nodes (38): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。 (+30 more)

### Community 62 - "user-steps.mts"
Cohesion: 0.11
Nodes (12): fromSource, hookSpec, ADR-0028, ADR-0037, ADR-0022, ADR-0036, collectStepFiles(), loadUserSteps() (+4 more)

### Community 63 - "reconcile.tick（无状态推进一步，四宿主共用）"
Cohesion: 0.11
Nodes (21): _aggregate（run 级 status 聚合）, _NON_VERDICT 过滤名单, StepResult.shortcircuited（正交布尔）, Status enum（加 SKIPPED/ABORTED/PENDING/RUNNING）, _STATUS_SEVERITY 数值序, StepSkipped 事件（step 级短路）, TERMINAL_STATUSES（终态真源，取补）, stopTimeout=120 / grace 预算标定 (+13 more)

### Community 64 - "test_cloud_reconcile.py"
Cohesion: 0.12
Nodes (24): DdbEventLog, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, _meta(), _passed_worker_events(), _put_worker_event(), RunMeta, cloud 无状态跑批 core 侧测试（ADR 0034 P4a）：DdbEventLog + CloudLauncher +… (+16 more)

### Community 65 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 66 - "Step Argument Assembly"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 67 - "build_local_reconcile"
Cohesion: 0.17
Nodes (15): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, _job(), region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。, 使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env… (+7 more)

### Community 68 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, "version")`，由 stack 资源随部署事务写入，ADR 0037 决策 6）。…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。 (+10 more)

### Community 69 - "Worker Image ADR"
Cohesion: 0.11
Nodes (19): 0038. worker 镜像交付：基底、variant 与推送注册, `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）, `push-worker` 流程, SSM 参数与命名真源, 不变量, 与版本升级的交互, 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）, 多版本与多环境 (+11 more)

### Community 70 - "SqliteEventLog"
Cohesion: 0.19
Nodes (8): Connection, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, SqliteEventLog, Path

### Community 71 - "test_tunnel_host.py"
Cohesion: 0.15
Nodes (18): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, Σ(各 job 预算) + 启动余量——求和对任何并发取值都是保守上界（ADR 0034 机制四）。 (+10 more)

### Community 72 - "test_package_readmes.py"
Cohesion: 0.12
Nodes (17): CLAUDE.md 项目约定, 代码纪律（绿≠对 / 接口诚实）, 文档纪律（ADR / CONTEXT / journey / guides）, 工作方式（tools/ 复用、AWS 开发期免费）, gherkai CLI 使用者页面, parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md… (+9 more)

### Community 74 - "run-scope.test.mts"
Cohesion: 0.11
Nodes (10): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+2 more)

### Community 75 - "JS Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 76 - "gherkai deploy push-worker（八步流程）"
Cohesion: 0.13
Nodes (17): BackendStack 资源清单（DDB/S3/ECS/IAM/SSM/Lambda）, 两层命名：prefix 批量默认 + 单资源覆盖, preflight fail-fast（探资源存在性、点名 prefix）, task role IAM 最小权限（动作 × 资源两维收窄）, VPC 来源三档（复用/默认/建新，零 NAT）, RunMeta.extra_http_headers（额外请求头通道）, --list-deterministic dump 模式 / CLI 子命令, --match-steps 批量匹配 + plan 命中标注 (+9 more)

### Community 77 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 78 - "test_subprocess_engine.py"
Cohesion: 0.34
Nodes (15): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried(), test_adapter_network_exit_maps_to_network_error() (+7 more)

### Community 79 - "build_fargate_engines"
Cohesion: 0.14
Nodes (16): build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…, boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。 (+8 more)

### Community 80 - "report_store/local.py"
Cohesion: 0.11
Nodes (20): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), _local_path(), Path, ReportRef, ResourceUri, RunResult (+12 more)

### Community 81 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 82 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 83 - "CDK Invocation Tests"
Cohesion: 0.13
Nodes (12): cdk(), _clean_aws_env(), _FakeEngine, fixture, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。… (+4 more)

### Community 84 - "deploy.py"
Cohesion: 0.11
Nodes (19): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+11 more)

### Community 85 - "_args"
Cohesion: 0.23
Nodes (12): _args(), _mk_state(), pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。, test_render_status_json_no_hint() (+4 more)

### Community 86 - "tunnel.py"
Cohesion: 0.15
Nodes (12): 本地应用暴露 / 隧道（--expose-local）, gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…, _gen_auth(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。 (+4 more)

### Community 87 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。 用途：少数"必须精确、不容 AI 抖动"的断言（如…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言…, url_matches()

### Community 88 - "_CdkWritingContext"
Cohesion: 0.17
Nodes (14): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, Path, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。 (+6 more)

### Community 89 - "_FakeEcs"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 90 - "NPM Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 91 - "test_tunnel.py"
Cohesion: 0.17
Nodes (15): NgrokTunnel, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, TunnelInfo, _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。 (+7 more)

### Community 93 - "_FakeEcs"
Cohesion: 0.15
Nodes (9): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null() (+1 more)

### Community 94 - "LocalReportStore"
Cohesion: 0.21
Nodes (29): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, _jr(), JobResult, Path, RunResult, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。 (+21 more)

### Community 95 - "0039. 用户可见面不带内部指代：产品文案与文档分层"
Cohesion: 0.15
Nodes (13): 产品文案禁内部指代（AST 护栏）, README / DEVELOPMENT 按读者分层, ADR 0039: 用户可见面不带内部指代, 0039. 用户可见面不带内部指代：产品文案与文档分层, 代价与权衡, 决策, 对既有文档与 code 的影响, 护栏 (+5 more)

### Community 96 - "check_version_skew"
Cohesion: 0.08
Nodes (26): check_version_skew(), variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `_is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, _release_cmp(), _release_key(), _variant_miss_hint() (+18 more)

### Community 97 - "_FakeResult"
Cohesion: 0.17
Nodes (5): _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。

### Community 98 - "Release & CI Setup"
Cohesion: 0.15
Nodes (13): 1. PyPI 占名（先于一切）, 2. PyPI trusted publisher × 5（只有真发行的五个需要）, 3. npm trusted publisher（免 token，无 secret）, 4. GHCR：首次推送后把两个 package 改成 public, 5. 仓库本身必须是 public, CI 与发布链（`.github/`）, `release.yml` 的 job 图与重跑语义, TestPyPI 演练（推正式 tag 之前排一次） (+5 more)

### Community 99 - "CLI Contributor Docs"
Cohesion: 0.17
Nodes (12): cli 包 —— contributor 文档, plan 的实现细节, RunReport 内部, VPC 档比对（三态）, 为何拆 `submit` / `status`, 从 checkout 跑, 实时落库, 模块 (+4 more)

### Community 100 - "test_wire.py"
Cohesion: 0.09
Nodes (35): _argument_to_json(), _cost_from_json(), event_from_json(), event_from_line(), job_to_json(), job_to_line(), Event, ReportRef (+27 more)

### Community 101 - "_ssm_params"
Cohesion: 0.15
Nodes (13): Template, SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新档记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值 = task-def 的 `Ref`（**带 revision** 的 ARN）。…, _ssm_params(), test_prefix_switches_whole_set(), test_ssm_parameter_set_is_exactly_six() (+5 more)

### Community 102 - "_stopped_detail"
Cohesion: 0.14
Nodes (14): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, container 缺 exitCode = 容器没跑起来（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, _stopped_detail(), test_exit_observer_records_exit_for_detached_run() (+6 more)

### Community 103 - "Execution & Progression Model Guide"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的一生, 4. 后台跑批 `submit` 的一生, 4a. local 档：per-run 推进进程, 4b. cloud 档：三 Lambda 链, 4c. 读侧：进度怎么看、结果落在哪, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 104 - "Worker Package Dev Notes"
Cohesion: 0.17
Nodes (12): 从本 checkout 跑, 使用方 `steps/` 的加载（实现要点）, 依赖分类（踩过的坑）, 包身份, 容器镜像（维护者向）, 布局, 开发笔记（contributor）, 执行形态：薄 worker（cucumber 已退役） (+4 more)

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
Cohesion: 0.16
Nodes (7): ADR-0028, ADR-0029, ArtifactUploader, ADR-0016, ADR-0024, ADR-0032, ADR-0033

### Community 110 - "开发笔记（contributor）"
Cohesion: 0.18
Nodes (11): 容器镜像（维护者向）, 开发笔记（contributor）, 执行形态：薄 worker（pytest-bdd 已退役）, 报告落点, 环境, 相关 ADR, 确定性 step：内建脚手架 vs 使用方的 `steps/`, 跑 spike（可独立跑，不进 wheel） (+3 more)

### Community 111 - "test_s3_report_store.py"
Cohesion: 0.19
Nodes (15): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, _run_with_refs(), S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest() (+7 more)

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

### Community 116 - "cli.py"
Cohesion: 0.08
Nodes (28): check_node(), _error_code(), _make_cfn_client(), _make_ssm_client(), _node_major(), Exception, `gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`…, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6； 三档与… (+20 more)

### Community 117 - "start_tunnel_for_jobs"
Cohesion: 0.29
Nodes (7): 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

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

### Community 122 - "StepResult"
Cohesion: 0.10
Nodes (34): _cost_bits(), format_event(), _ms(), plan_to_dict(), Event, RunResult, RunState, 渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core… (+26 more)

### Community 123 - "render_plan_text"
Cohesion: 0.33
Nodes (6): _arg_hint(), _dispatch_hint(), plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。 dispatch（可选，ADR 0036…, step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。, step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。 dataTable →…, render_plan_text()

### Community 124 - "0040. 使用方角色模型与术语"
Cohesion: 0.20
Nodes (10): 0040. 使用方角色模型与术语, 代价, 决策 1：四顶帽子与正名, 决策 2：帽子不是人, 决策 3：执行是正交轴——跑法权限梯, 决策 4：边界矩阵, 决策 5：术语单一真源与立新角色的门槛, 影响 (+2 more)

### Community 125 - "ADR 0036 Deterministic Capability"
Cohesion: 0.22
Nodes (9): 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询, 1. 注册面扩元数据（暴露的前提）, 2. worker 自述：`--list-deterministic` dump 模式, 3. CLI 子命令 `list-deterministic --engine <name>`, 4. plan 命中标注：「我写的这句会不会命中」, 决策, 背景与问题, 被拒方案（护栏） (+1 more)

### Community 126 - "Dist Metadata Check"
Cohesion: 0.39
Nodes (8): fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。, wheel_metadata()

### Community 127 - "_job_with"
Cohesion: 0.36
Nodes (8): map_origin_in_jobs(), 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable(), test_map_replaces_step_text_prefix()

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
Cohesion: 0.22
Nodes (6): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, resolveEventsFd()

### Community 133 - "RunStore"
Cohesion: 0.05
Nodes (34): Engine, JobResult, JobState, ResourceUri, RunMeta, RunResult, RunState, Status (+26 more)

### Community 134 - "SubprocessEngine"
Cohesion: 0.18
Nodes (7): Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。, SubprocessEngine, Job, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, SubprocessLauncher

### Community 135 - "agentcore-sigv4.mts"
Cohesion: 0.48
Nodes (6): getBaseUrl(), getRegion(), MODEL, modelSigner_(), signCdpUpgrade(), sigv4Fetch()

### Community 136 - "Runtime Package README"
Cohesion: 0.29
Nodes (6): gherkai-runtime, 主要入口, 安装, 最小用法：在本机跑完一批, 注意, 相关

### Community 137 - "ADR-0024"
Cohesion: 0.21
Nodes (6): ADR-0024, argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 138 - "ADR 0018 Common Steps"
Cohesion: 0.33
Nodes (6): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）

### Community 139 - "_FakeSchedulerClient"
Cohesion: 0.20
Nodes (8): ConflictException, exceptions, _FakeSchedulerClient, create_schedule 记录器（含 exceptions.ConflictException 形状，兼容 boto3 client 异常访问路径）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, test_timeout_watch_conflict_is_idempotent(), test_timeout_watch_creates_one_time_schedule(), Exception

### Community 140 - "exit_observer.py"
Cohesion: 0.27
Nodes (9): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+1 more)

### Community 142 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 145 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 146 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 147 - "代码健康度复盘任务说明"
Cohesion: 0.13
Nodes (19): Lambda handler 入口（lambdas/）, ADR 0001 框架范围限定为英文 UI, ADR 0002 不用 gpt-5.5, ADR 0003 Qwen3-VL 定位, ADR 0009 最大化使用 AWS 是硬前提, ADR 0010 spike 作对标基准, ADR 0024 engine 只报原生量、core 不折美元, ADR 0026 纯 reducer 不臆断因果 (+11 more)

### Community 148 - "Core Package Docs"
Cohesion: 0.50
Nodes (4): core 包 —— contributor 文档, 实际执行（跑 .feature）, 模块, 跑测试

### Community 149 - "_TrajNova"
Cohesion: 0.33
Nodes (3): 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。, _TrajNova, _TrajResult

### Community 150 - "_referenced_by_live_run"
Cohesion: 0.50
Nodes (4): _non_terminal_statuses(), 未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…, 有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…, _referenced_by_live_run()

### Community 151 - "Worker Subnet Single Source"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 152 - "ContainerError"
Cohesion: 0.14
Nodes (10): ContainerError, Exception, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, CleanupOutcome, family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看…, RevisionInfo (+2 more)

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

### Community 157 - "cloud_env"
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

### Community 162 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 165 - "test_run_state_timestamps_share_one_format"
Cohesion: 0.18
Nodes (11): now_iso(), parse_iso(), datetime, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), _echo_resolver() (+3 more)

### Community 167 - "compose.py"
Cohesion: 0.05
Nodes (60): subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "subnets") 的便捷形式）。, sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "security-groups")…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), ssm_worker_template_path() (+52 more)

### Community 169 - "test_detached_launcher.py"
Cohesion: 0.24
Nodes (15): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _now(), SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。 **真 spawn echo_worker…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…, 真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。, max_concurrency=1：两 job 串行推进、都 passed。验 loop 起完一个再起下一个。 (+7 more)

### Community 172 - "classify_vpc_state"
Cohesion: 0.20
Nodes (10): classify_vpc_state(), 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, SSM 里记的生效档 `stored` 是否 == 本次 `--vpc requested`。 三档形态见…, vpc_spec_matches(), parametrize, test_classify_four_states(), test_classify_stack_absent_is_first_deploy_even_without_param(), test_vpc_accepts_three_dossiers() (+2 more)

### Community 180 - "_seed_run"
Cohesion: 0.10
Nodes (21): 建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…, definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。, definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。, meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。, cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…, 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。 (+13 more)

### Community 181 - "e2e_harness.py"
Cohesion: 0.33
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 182 - "reconcile.py"
Cohesion: 0.11
Nodes (15): Action, plan_next(), reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。…, 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, EventLog, finalize_artifacts(), Launcher, Job (+7 more)

### Community 187 - "ADR-0033"
Cohesion: 0.20
Nodes (7): BASE_URL, main(), makePng(), REGION, BASE_URL, main(), ADR-0033

### Community 188 - "_patch_skew"
Cohesion: 0.50
Nodes (4): _patch_skew(), --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_wait_cloud_kicker_missing_fails_fast()

### Community 202 - "raise_for_worker_exit"
Cohesion: 0.25
Nodes (8): raise_for_worker_exit(), worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, test_raise_for_worker_exit_maps_codes_with_fargate_label(), 码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 /…, 两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。, test_raise_for_worker_exit_label_names_the_transport_field(), test_raise_for_worker_exit_maps_codes()

### Community 204 - "events_table"
Cohesion: 0.67
Nodes (3): events_table(), fixture, events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——P4 单独建，schema 见 ADR 0033/0024。

### Community 208 - "test_compose.py"
Cohesion: 0.04
Nodes (80): fixture, parametrize, build_engines(), engine_min_grace(), is_pure_release(), load_feature(), prune_empty_dirs(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。… (+72 more)

### Community 216 - "03-midscene-grounding.ts"
Cohesion: 0.33
Nodes (5): ADR-0010, BASE_URL, main(), MODEL_CONFIG, REGION

### Community 221 - "05-negative-assertions.ts"
Cohesion: 0.33
Nodes (5): BASE_URL, Check, main(), MODEL_CONFIG, REGION

### Community 224 - "test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions"
Cohesion: 0.40
Nodes (4): _AbsentEngine, 容器引擎替身：`probe()` 说「docker 没装」。, 容器引擎缺失的前置警告只对**纯发行版**成立：dev/post/本地段版本的 worker 镜像步骤本就走不到「同步基底」 （ADR 0038…, test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions()

### Community 226 - "subprocess_engine.py"
Cohesion: 0.17
Nodes (10): _pump_log(), Event, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的…, _read_events() (+2 more)

### Community 228 - "._installed_import_source"
Cohesion: 0.40
Nodes (4): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it(), RuntimeError

### Community 230 - "gherkai_cli/__main__.py"
Cohesion: 0.08
Nodes (52): _build_parser(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_list_deterministic(), _cmd_plan(), _cmd_reconcile(), _cmd_run(), _cmd_status() (+44 more)

### Community 231 - "detached.py"
Cohesion: 0.25
Nodes (6): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, _paths(), 无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, write_tunnel_file()

### Community 232 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

## Knowledge Gaps
- **375 isolated node(s):** `Check`, `StepArgument`, `Job`, `Job`, `Scenario` (+370 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **105 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `is_botocore_error()` connect `compose.py` to `_is_transient_network`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `PlanError` connect `scope.py` to `test_run_step.py`, `test_plan.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `_is_transient_network()` connect `_is_transient_network` to `test_run_step.py`, `run_scope.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Provider` (e.g. with `UnsupportedContainerEngine` and `_AbsentEngine`) actually correct?**
  _`Provider` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `Job` (e.g. with `_sample_run()` and `test_render_text_annotates_shortcircuited_step()`) actually correct?**
  _`Job` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `CollectSink` (e.g. with `WorkerNetworkError` and `Job`) actually correct?**
  _`CollectSink` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Check`, `StepArgument`, `Job` to the rest of the system?**
  _375 weakly-connected nodes found - possible documentation gaps or missing edges._