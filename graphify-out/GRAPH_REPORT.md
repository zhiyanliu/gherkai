# Graph Report - .  (2026-09-09)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3928 nodes · 8983 edges · 238 communities (171 shown, 67 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 599 edges (avg confidence: 0.55)
- Token cost: 36,634 input · 3,685 output

## Graph Freshness
- Built from commit: `6fa277ed`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Engine Ports & Adapters
- Worker Image Push Workflow
- Cloud Backend CLI Tests
- CLI Run Entry Tests
- Run Result Verdict Model
- SQLite Event Log & Projection
- DynamoDB RunStore Conditional Writes
- Run State Rendering & Boto Guard
- Container Push Tests
- Render & ReportStore Local
- Container Engine Adapter
- AWS Deploy Provider CLI
- Cloud Launcher & DDB EventLog
- Deploy Command Shell Tests
- Run Schedule Orchestration
- Backend Stack Synth Assertions
- Worker Variant Resolution
- CDK App & Deploy CLI
- Execution Architecture Decisions
- Artifact S3 Upload
- Composition Root Wiring
- Terminal Status Aggregation
- Reconcile Ports & Tick
- CDK Command Orchestration
- Event Formatting & Cost Model
- Conditional Write Contract Tests
- Nova Act Worker Package
- ADR Index & Dev Docs
- Resource Naming Source
- Worker Command Resolution
- ResultStore Local/S3
- Nova Workflow Setup & Probes
- Step Dispatch & Error Mapping
- S3 ReportStore & Subprocess Engine
- Fargate Event Drain & Exit Codes
- Transient Error Classification
- Cloud Resource Preflight Fakes
- Run Persistence Orchestration
- TypeScript Spike Probes
- Backend Stack Constructs
- Worker Interrupt Model
- User Steps Directory Loading
- Stack Synth Fixtures
- Engine Resolver Building
- Domain Glossary
- Lambda Handler Event Parsing
- Midscene Worker Run Scope
- Reconciler Lambda & Timeouts
- CLI Main Entry
- Packaging & Distribution ADR
- TypeScript Compiler Config
- Job Source Input
- Tunnel CLI Wiring Tests
- Fargate Engine Adapter
- Plan Parsing Tests
- Deterministic Step Registry
- Worker Event Sink
- CLI Run/Submit Commands
- Deploy AWS README
- Wire Protocol Serialization
- Cloud Adapter Test Fixtures
- Fargate Engine Unit Tests
- Midscene TS Hooks & ADRs
- Status Model & Concurrency Gates
- Plan Command & Rendering
- Step Argument Assembly
- Local Stores & Deterministic Query
- Backend Version Stamp Check
- Worker Image Delivery ADR
- Midscene Job Source TS
- Tunnel Host TTL Watchdog
- Project Conventions & README Guards
- Status Command Rendering
- Midscene TS Tests
- Node Dependencies
- SQLite Event Log Store
- Backend Infra Feature Set
- Midscene Deterministic Registry
- Detached Launcher Reconcile
- Subprocess Engine Integration
- Version Skew Check
- Reconcile Loop Integration
- Event Wallclock Analysis
- Job Serialization & E2E Harness
- Provider Flag Wiring
- CDK Invocation Test Fixtures
- Act Boundary Presend Upload
- Cloud Store Composition
- Deploy Provider Discovery
- Local Tunnel Exposure
- S3 ResultStore
- Subprocess Worker Handle
- CDK Context Cache
- Job Timeout Handling
- Reconciler Concurrency Cap
- Midscene Package Manifest
- Cloud Target Resolution
- Ngrok Tunnel Provider
- S3 Argument Offload
- SQLite Event Log Tests
- _stopped_detail
- CDK SSM Parameter Guardrails
- User-Facing Text Policy (ADR 0039)
- Deterministic Step Registry
- Nova Act Test Doubles
- Publishing Prerequisites Checklist
- CLI Package Contributor Docs
- Foundational ADR Principles
- Execution Model Guide (run/submit)
- Nova Worker Dev Notes
- User Steps Directory Loader
- Fake Event Sink Fixtures
- Internal-Pointer AST Guardrail
- Feature Planning to Jobs
- CloudFormation/SSM Client Stubs
- Artifact Uploader
- Midscene Worker Dev Notes
- Worker READMEs and Harness Docs
- Fake Sink Test Fixtures
- CI and Release Workflows
- AWS Deploy Contributor Manual
- Exit Observer Lambda
- Task Definition Cleanup
- Local App Tunneling (ADR 0035)
- Worker Signal Interrupt Tests
- ECS Task Timing Script
- Deterministic Capability Exposure
- Dist Metadata Check Script
- Timestamp and Clock Utilities
- Tunnel Origin URL Mapping
- Worker Exit Code Translation
- Worker Task Def Resolution
- Developer Guide Index
- TypeScript Event Sink
- Fake DynamoDB Table
- Environment and Version Resolution
- Midscene Worker Integration Docs
- Trajectory Artifact Test Doubles
- Subprocess Worker Launcher
- Tunnel Setup for Jobs
- Runtime Package README
- Deploy/Destroy CLI Commands
- Scenario JSON Serialization
- Generic Step Capability ADR
- Step Argument Handling (TS)
- Fargate Network Resolution
- Local Detached Run Wiring
- Tunnel Info Model
- Fake S3 Client
- Fargate Worker Handle
- Echo Test Worker
- Cloud Test Infrastructure Checks
- Kicker Run ID Extraction
- Built-in Deterministic Anchors
- TypeScript Dev Dependencies
- Tunnel Cleanup
- AWS Test Fixtures (moto)
- List Deterministic CLI Command
- Version Skew Test Patches
- Core Package Contributor Docs
- Scope Done vs ECS Stopped
- Lambda Dependency Bundling
- Live Run Reference Check
- Worker Subnet Single Source
- AWS Client Spy
- NPM Package Files
- Package Repository Metadata
- Runtime Contributor Docs
- Worker Command Fixtures
- Event Observer Hook
- Cloud Env Fixture
- AWS Env Fixture
- Fargate Engine Composition
- NPM Scripts
- AgentCore CDP Spike
- Registry Isolation Fixture
- Pure Release Version Check
- DynamoDB SDK Dependency
- S3 SDK Dependency
- Run Meta Spy
- Adapters Package Init
- Core Package Init
- Unknown Step Keyword Failure
- Leading And Keyword Failure
- Delete Worker Placeholder
- Revision Lineage Tags
- Exit Item Test Setup
- Per-Run Failure Isolation
- Missing Task Env Handling
- Provider Import Isolation
- Architecture ADR References
- Direct Kick Invocation
- OpenAI Dependency
- tsx Dependency
- Index Wait Script
- Workspace Root Package
- Argument Parser
- Base Exception
- Run Result Objects
- Run Result Objects
- Job Result Objects
- Run Metadata
- Run Result Objects
- Job Result Objects
- Run Metadata
- Run Result Objects
- Run Metadata
- Run Metadata
- Subprocess Execution Engine
- Programmatic Login & HITL
- Midscene SigV4 Auth
- Qwen3-VL Planning Reuse
- AI Assertions with Voting
- Page Transient Flakiness
- Retired Cucumber Patch
- DynamoDB Run Storage
- Engine Resolution
- Exception Handling
- Shared Gherkin Features
- Job Sink Interface
- Local Run Storage
- Test Parametrization
- Core Library Package
- AWS Deployment Package
- Runtime Package
- NovaAct Worker Package
- Report Storage
- Result Storage
- Run State Model
- Run Store Interface
- Run Metadata
- Subprocess Execution Engine
- Sink Interface
- SQLite Event Log
- Status Enum
- Idempotent Timeout Arming
- Kicker Timeout No-Op Path

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
- `_FakeEcs` --uses--> `Job`  [INFERRED]
  deploy_aws/tests/test_lambda_handlers.py → core/gherkai_core/model.py
- `SubprocessLauncher` --uses--> `Job`  [INFERRED]
  runtime/gherkai_runtime/detached.py → core/gherkai_core/model.py
- `TunnelSetup` --uses--> `Job`  [INFERRED]
  runtime/gherkai_runtime/tunnel_host.py → core/gherkai_core/model.py
- `NgrokTunnel` --uses--> `Job`  [INFERRED]
  runtime/gherkai_runtime/tunnel.py → core/gherkai_core/model.py
- `TunnelError` --uses--> `Job`  [INFERRED]
  runtime/gherkai_runtime/tunnel.py → core/gherkai_core/model.py

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

## Communities (238 total, 67 thin omitted)

### Community 0 - "Engine Ports & Adapters"
Cohesion: 0.05
Nodes (84): 执行引擎 port（Engine）, adapters/_boto.py 依赖守卫, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, PlanError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非… (+76 more)

### Community 1 - "Worker Image Push Workflow"
Cohesion: 0.05
Nodes (93): Aws, _cell(), cleanup_pass(), CleanupOutcome, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code() (+85 more)

### Community 2 - "Cloud Backend CLI Tests"
Cohesion: 0.05
Nodes (93): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, local run 的 definition 不带这两个字段（omit-when-None，ADR 0038「local 档不写」）。, 后端默认指针本身是个非法 variant 名（部署侧写坏）→ 退 2 并点名那个 SSM 参数，不冒 traceback。 显式 `--worker-…, patch store 钩子 + preflight（默认放行）+ 版本 skew 闸 + worker variant 闸（都默认放行）返回记录调用的… (+85 more)

### Community 3 - "CLI Run Entry Tests"
Cohesion: 0.05
Nodes (88): main(), _capturing_schedule(), _det_feature(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json… (+80 more)

### Community 4 - "Run Result Verdict Model"
Cohesion: 0.05
Nodes (61): test_render_text_annotates_shortcircuited_step(), test_render_text_no_annotation_on_plain_failed(), Ports 层（Engine/RunStore/ResultStore/ReportStore/EventLog/Launcher）, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, 一次执行的机器可读汇总判定 = **definition（run_meta）+ 判定（jobs）的显式合成**（ADR 0016/0026）。…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire… (+53 more)

### Community 5 - "SQLite Event Log & Projection"
Cohesion: 0.06
Nodes (85): SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, ScopeStarted, StepSkipped, StepStarted, Action, EventRecord, _job_status() (+77 more)

### Community 6 - "DynamoDB RunStore Conditional Writes"
Cohesion: 0.05
Nodes (73): DynamoDBRunStore, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, STATE item 上有没有 `detached` 标记（ADR 0034）：True = 无状态跑批的 submit 建的 run。 **adapter-…, RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。, LocalRunStore (+65 more)

### Community 7 - "Run State Rendering & Boto Guard"
Cohesion: 0.04
Nodes (56): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), has_pointers() (+48 more)

### Community 8 - "Container Push Tests"
Cohesion: 0.07
Nodes (76): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+68 more)

### Community 9 - "Render & ReportStore Local"
Cohesion: 0.07
Nodes (66): render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, _sample_run(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar(), ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。, collect_report_index(), _fmt_ms() (+58 more)

### Community 10 - "Container Engine Adapter"
Cohesion: 0.05
Nodes (54): ContainerEngine, ContainerError, digest_for_repo(), ImageInfo, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：… (+46 more)

### Community 11 - "AWS Deploy Provider CLI"
Cohesion: 0.07
Nodes (69): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _argv(), _parse(), _parse_destroy(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, flag 面全集钉死（枚举型护栏）：三个 context 旋钮 flag + AWS 定位二件套 + 两个「皮的中立版的 AWS 精确化」（见 cli… (+61 more)

### Community 12 - "Cloud Launcher & DDB EventLog"
Cohesion: 0.06
Nodes (47): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project… (+39 more)

### Community 13 - "Deploy Command Shell Tests"
Cohesion: 0.07
Nodes (44): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 __main__（argparse 皮）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+36 more)

### Community 14 - "Run Schedule Orchestration"
Cohesion: 0.23
Nodes (47): 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->…, 收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。 (+39 more)

### Community 15 - "Backend Stack Synth Assertions"
Cohesion: 0.07
Nodes (46): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler/kicker）都要能读 `/{prefix}backend/*`（ADR 0038「权限面增量·云端推进器」）： 没有… (+38 more)

### Community 16 - "Worker Variant Resolution"
Cohesion: 0.07
Nodes (46): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。 值 =…, worker_image_key(), _push_image(), worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest/模板 ARN 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。, 只探本 run 用到的引擎（对齐既有 task-def preflight 判据）——另一引擎没镜像也不拦。 (+38 more)

### Community 17 - "CDK App & Deploy CLI"
Cohesion: 0.06
Nodes (40): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_ssm_client(), _node_major() (+32 more)

### Community 18 - "Execution Architecture Decisions"
Cohesion: 0.07
Nodes (41): 决策 A：cli --backend {local,cloud} 单旋钮, compose.build_local_stores / build_cloud_stores, 组合根注入（选实现不由 module 自选）, 核心库窄腰 core/（解析→分组→调度→收集，零引擎依赖）, 决策 B：subprocess + 注入云存储 = 内部预演手段, 决策 C：Fargate/region/profile 配置走 CLI 参数注入, Engine port（run_scope(job) → 事件流）, FargateEngine（云端执行 adapter） (+33 more)

### Community 19 - "Artifact S3 Upload"
Cohesion: 0.08
Nodes (29): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→…, upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。 (+21 more)

### Community 20 - "Composition Root Wiring"
Cohesion: 0.08
Nodes (40): is_botocore_error(), _make_ecr_client(), _make_ecs_client(), _make_lambda_client(), _make_ssm_client(), new_run_id(), _no_default_pointer_error(), BaseException (+32 more)

### Community 21 - "Terminal Status Aggregation"
Cohesion: 0.08
Nodes (22): RuntimeError, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一…, FakeWorkerHandle (+14 more)

### Community 22 - "Reconcile Ports & Tick"
Cohesion: 0.09
Nodes (32): EventLog, Launcher, Job, Protocol, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 local = 起 subprocess worker（事件旁路落 SQLite…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick() (+24 more)

### Community 23 - "CDK Command Orchestration"
Cohesion: 0.07
Nodes (22): cdk_command(), _make_sts_client(), Path, boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。, 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer… (+14 more)

### Community 24 - "Event Formatting & Cost Model"
Cohesion: 0.13
Nodes (35): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+27 more)

### Community 25 - "Conditional Write Contract Tests"
Cohesion: 0.10
Nodes (36): _initial(), _meta(), RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+28 more)

### Community 26 - "Nova Act Worker Package"
Cohesion: 0.08
Nodes (30): ArtifactUploader, gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_traj_refs(), _backoff_interrupted(), _collect_traj(), _cost_from_result(), _get_uploader() (+22 more)

### Community 27 - "ADR Index & Dev Docs"
Cohesion: 0.25
Nodes (26): ADR 0005 用例描述层用单一共享 .feature, ADR 0013 跨引擎共享边界止于 features/, ADR 0015 v1.0 定位：流程冒烟非精确回归, ADR 0016 执行架构, ADR 0017: 云端执行选 Fargate, ADR 0019 feature 标签定 scope 与引擎, ADR 0020 step 措辞与角色边界, ADR 0022 薄 worker (+18 more)

### Community 28 - "Resource Naming Source"
Cohesion: 0.07
Nodes (32): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_worker_template_path(), gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…, default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。… (+24 more)

### Community 29 - "Worker Command Resolution"
Cohesion: 0.08
Nodes (32): engine_min_grace(), _find_worker_spec(), 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…, resolve_worker_cmd(), parametrize, compose（组合根逻辑）单测：不起任何子进程、零费用。 (+24 more)

### Community 30 - "ResultStore Local/S3"
Cohesion: 0.10
Nodes (28): LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, _argument_from_dict(), _argument_to_dict(), job_from_dict() (+20 more)

### Community 31 - "Nova Workflow Setup & Probes"
Cohesion: 0.10
Nodes (25): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+17 more)

### Community 32 - "Step Dispatch & Error Mapping"
Cohesion: 0.16
Nodes (31): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+23 more)

### Community 33 - "S3 ReportStore & Subprocess Engine"
Cohesion: 0.07
Nodes (22): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。, SubprocessEngine, _ask_worker() (+14 more)

### Community 34 - "Fargate Event Drain & Exit Codes"
Cohesion: 0.13
Nodes (30): _engine(), _job(), _put_event(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。, worker 零事件退出 + exit item 已落：STOPPED 兜底路径（含 _final_drain 强一致终读）同样只读 worker 段。…, worker 干净退出（exitCode 0）但没发 scope_done：drain 后正常终止、不抛。 (+22 more)

### Community 35 - "Transient Error Classification"
Cohesion: 0.12
Nodes (31): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+23 more)

### Community 36 - "Cloud Resource Preflight Fakes"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 37 - "Run Persistence Orchestration"
Cohesion: 0.14
Nodes (24): ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run = commit…, 编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。 生命周期：begin（run…, 每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。 skipped 的… (+16 more)

### Community 38 - "TypeScript Spike Probes"
Cohesion: 0.09
Nodes (23): ADR-0010, BASE_URL, main(), makePng(), REGION, BASE_URL, main(), MODEL_CONFIG (+15 more)

### Community 39 - "Backend Stack Constructs"
Cohesion: 0.11
Nodes (15): Cluster, Construct, BackendStack, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack…, 事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED… (+7 more)

### Community 40 - "Worker Interrupt Model"
Cohesion: 0.12
Nodes (21): _aggregate(), _emit_scenario_done_unless_stopped(), scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…, _FakeResult, _Meta, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM…, handler 里绝不做 I/O：信号落在主线程正写 stderr 的瞬间，handler 再写 stderr 会撞 BufferedWriter 的非重入锁…, 记录 act/act_get 收到的 timeout；act_get 按布尔序列回。 (+13 more)

### Community 41 - "User Steps Directory Loading"
Cohesion: 0.12
Nodes (28): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。, 真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。… (+20 more)

### Community 42 - "Stack Synth Fixtures"
Cohesion: 0.11
Nodes (24): BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…, make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), fixture (+16 more)

### Community 43 - "Engine Resolver Building"
Cohesion: 0.08
Nodes (28): build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 no_artifacts（`--no-…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, Path, 某引擎定位链 miss **不连坐**另一条腿（ADR 0037 决策 3）：dev 下 midscene 未装是常态， novaact-only 的 run… (+20 more)

### Community 44 - "Domain Glossary"
Cohesion: 0.09
Nodes (27): CONTEXT.md 领域术语表, 推进器 advancer, AgentCore 浏览器会话, 确定性断言 vs AI 断言, 两个引擎都子进程 + 薄 worker, 执行核心库窄腰, 成本可观测, 部署 provider（gherkai.deploy entry point） (+19 more)

### Community 45 - "Lambda Handler Event Parsing"
Cohesion: 0.11
Nodes (23): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带… (+15 more)

### Community 46 - "Midscene Worker Run Scope"
Cohesion: 0.11
Nodes (26): ADR-0019, ADR-0026, ADR-0027, ADR-0032, ADR-0035, aggregate(), AWS_TRANSIENT_NAMES, AWS_TRANSIENT_STATUS (+18 more)

### Community 47 - "Reconciler Lambda & Timeouts"
Cohesion: 0.12
Nodes (21): _build(), EventBridgeTimeoutWatch, _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING… (+13 more)

### Community 48 - "CLI Main Entry"
Cohesion: 0.11
Nodes (23): _build_parser(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_list_engines(), _cmd_reconcile(), _cmd_tunnel_watch(), _dist_version(), _installed_version() (+15 more)

### Community 49 - "Packaging & Distribution ADR"
Cohesion: 0.08
Nodes (24): 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel, 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条, 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵, 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra, 2d. `requires-python >=3.13` 维持, 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）, 决策 1：交付物按打包技术划分，worker 运行时是硬核, 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first (+16 more)

### Community 50 - "TypeScript Compiler Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 51 - "Job Source Input"
Cohesion: 0.09
Nodes (11): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层… (+3 more)

### Community 52 - "Tunnel CLI Wiring Tests"
Cohesion: 0.13
Nodes (22): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+14 more)

### Community 53 - "Fargate Engine Adapter"
Cohesion: 0.14
Nodes (14): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+6 more)

### Community 54 - "Plan Parsing Tests"
Cohesion: 0.17
Nodes (21): _plan(), parametrize, plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, test_assertion_votes_default_is_one(), test_background_prepended(), test_datatable_and_docstring_argument(), test_engine_conflict_errors(), test_engine_inherited_within_scope() (+13 more)

### Community 55 - "Deterministic Step Registry"
Cohesion: 0.14
Nodes (21): deterministic(), list_registry(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。 (+13 more)

### Community 56 - "Worker Event Sink"
Cohesion: 0.10
Nodes (9): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud(), test_emit_flushes_each_event() (+1 more)

### Community 57 - "CLI Run/Submit Commands"
Cohesion: 0.16
Nodes (21): _cmd_run(), _cmd_submit(), _load_and_plan(), _preflight_worker_runtimes(), _progress(), `_resolve_steps_dir` + cloud 档清零（ADR 0037 决策 4）：cloud 档 steps…, 本次 plan 用到的各引擎：worker 运行时能否定位 + （给了 steps 目录时）能否完成自述（ADR 0037 决策 3/4）。 - 定位链四级全…, plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。 成功返回 `Job[]`；任一前置失败返回**退出码… (+13 more)

### Community 58 - "Deploy AWS README"
Cohesion: 0.12
Nodes (21): worker 镜像：基底 / variant / 默认指针, gherkai-deploy-aws, gherkai deploy push-worker, 后端版本戳与三步升级, VPC 三档与四态档位比对, VPC 三档, 安装与前置, 帮助 (+13 more)

### Community 59 - "Wire Protocol Serialization"
Cohesion: 0.14
Nodes (20): _cost_from_json(), event_from_json(), Event, JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。 事件通道随形态而异：子进程态 =…, _report_refs_from_json(), _votes_from_json(), wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。, 80 是跨语言约定值（两个引擎 worker 各自硬编码）——改这个数即改协议，须同步两 worker。 (+12 more)

### Community 60 - "Cloud Adapter Test Fixtures"
Cohesion: 0.13
Nodes (20): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), fixture, 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -… (+12 more)

### Community 61 - "Fargate Engine Unit Tests"
Cohesion: 0.16
Nodes (20): _await_engine(), _engine_with_fake_ecs(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env(), _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error() (+12 more)

### Community 62 - "Midscene TS Hooks & ADRs"
Cohesion: 0.12
Nodes (11): ADR-0015, ADR-0037, ADR-0022, ADR-0036, ADR-0020, collectStepFiles(), loadUserSteps(), LoadUserStepsDeps (+3 more)

### Community 63 - "Status Model & Concurrency Gates"
Cohesion: 0.11
Nodes (21): _aggregate（run 级 status 聚合）, _NON_VERDICT 过滤名单, StepResult.shortcircuited（正交布尔）, Status enum（加 SKIPPED/ABORTED/PENDING/RUNNING）, _STATUS_SEVERITY 数值序, StepSkipped 事件（step 级短路）, TERMINAL_STATUSES（终态真源，取补）, stopTimeout=120 / grace 预算标定 (+13 more)

### Community 64 - "Plan Command & Rendering"
Cohesion: 0.13
Nodes (19): _cmd_plan(), _probe_deterministic_dispatch(), plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…, plan 预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…, _arg_hint(), _cost_bits(), _dispatch_hint(), _ms() (+11 more)

### Community 65 - "Step Argument Assembly"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 66 - "Local Stores & Deterministic Query"
Cohesion: 0.11
Nodes (20): build_local_stores(), match_deterministic(), prune_empty_dirs(), Path, query_deterministic(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 查询某引擎 worker 的确定性能力清单（ADR 0036）：spawn `worker --list-deterministic` 收 JSON。…, 批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker… (+12 more)

### Community 67 - "Backend Version Stamp Check"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, "version")`，由 stack 资源随部署事务写入，ADR 0037 决策 6）。…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。 (+10 more)

### Community 68 - "Worker Image Delivery ADR"
Cohesion: 0.11
Nodes (19): 0038. worker 镜像交付：基底、variant 与推送注册, `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）, `push-worker` 流程, SSM 参数与命名真源, 不变量, 与版本升级的交互, 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）, 多版本与多环境 (+11 more)

### Community 69 - "Midscene Job Source TS"
Cohesion: 0.12
Nodes (7): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0016, Job, JobSource

### Community 70 - "Tunnel Host TTL Watchdog"
Cohesion: 0.15
Nodes (18): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, Σ(各 job 预算) + 启动余量——求和对任何并发取值都是保守上界（ADR 0034 机制四）。 (+10 more)

### Community 71 - "Project Conventions & README Guards"
Cohesion: 0.12
Nodes (17): CLAUDE.md 项目约定, 代码纪律（绿≠对 / 接口诚实）, 文档纪律（ADR / CONTEXT / journey / guides）, 工作方式（tools/ 复用、AWS 开发期免费）, gherkai CLI 使用者页面, parametrize, Path, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md… (+9 more)

### Community 72 - "Status Command Rendering"
Cohesion: 0.17
Nodes (18): _cmd_status(), cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…, 渲染 RunState + pending 诊断提示 + 退出码——**local/cloud 共享一份**（保两路一致，ADR 0034）。 state…, [无状态跑批] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run…, _render_status(), _status_cloud(), _args(), _mk_state() (+10 more)

### Community 73 - "Midscene TS Tests"
Cohesion: 0.12
Nodes (9): mkLogDir(), tmproot(), ADR-0014, ADR-0029, ADR-0031, _events, fakePage, importMod() (+1 more)

### Community 74 - "Node Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-bedrock-agentcore (+9 more)

### Community 75 - "SQLite Event Log Store"
Cohesion: 0.17
Nodes (9): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+1 more)

### Community 76 - "Backend Infra Feature Set"
Cohesion: 0.13
Nodes (17): BackendStack 资源清单（DDB/S3/ECS/IAM/SSM/Lambda）, 两层命名：prefix 批量默认 + 单资源覆盖, preflight fail-fast（探资源存在性、点名 prefix）, task role IAM 最小权限（动作 × 资源两维收窄）, VPC 来源三档（复用/默认/建新，零 NAT）, RunMeta.extra_http_headers（额外请求头通道）, --list-deterministic dump 模式 / CLI 子命令, --match-steps 批量匹配 + plan 命中标注 (+9 more)

### Community 77 - "Midscene Deterministic Registry"
Cohesion: 0.13
Nodes (12): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, Match, matchBatch() (+4 more)

### Community 78 - "Detached Launcher Reconcile"
Cohesion: 0.20
Nodes (16): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, _job(), SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。 **真 spawn echo_worker…, region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。 (+8 more)

### Community 79 - "Subprocess Engine Integration"
Cohesion: 0.34
Nodes (15): _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried(), test_adapter_network_exit_maps_to_network_error() (+7 more)

### Community 80 - "Version Skew Check"
Cohesion: 0.12
Nodes (16): check_version_skew(), 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。, 戳缺失 = 本机制之前部署的环境 → warn（不拦）+ 提示跑一次 `gherkai deploy` 写入。, 任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。, 未装成包（源码直跑）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。, 只比 release 段（决策 7）：位数不同补零后比；同 release 段的 rc 与正式版视作同版本。, `cli_version` 必给（决策 7 比的是「写任务定义那一方」的版本）：不缺省成 gherkai-runtime 的版本—— editable… (+8 more)

### Community 81 - "Reconcile Loop Integration"
Cohesion: 0.18
Nodes (16): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…, 按 WORKER_MODE 起 echo_worker 的 SubprocessEngine，包成 resolver（所有 engine 名都映射到它）。, 真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。 (+8 more)

### Community 82 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 83 - "Job Serialization & E2E Harness"
Cohesion: 0.18
Nodes (14): job_to_json(), job_to_line(), Job, Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。, Job → 单行 JSON 字符串（写 worker stdin）。, test_job_to_json_assertion_votes_passthrough(), build_job(), Path (+6 more)

### Community 84 - "Provider Flag Wiring"
Cohesion: 0.19
Nodes (9): ArgumentParser, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6； 三档与…, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`… (+1 more)

### Community 85 - "CDK Invocation Test Fixtures"
Cohesion: 0.13
Nodes (12): cdk(), _clean_aws_env(), _FakeEngine, fixture, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。… (+4 more)

### Community 86 - "Act Boundary Presend Upload"
Cohesion: 0.25
Nodes (12): _presend_act_siblings(), act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…, _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings() (+4 more)

### Community 87 - "Cloud Store Composition"
Cohesion: 0.15
Nodes (15): build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…, boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。 (+7 more)

### Community 88 - "Deploy Provider Discovery"
Cohesion: 0.16
Nodes (13): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。, 按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,… (+5 more)

### Community 89 - "Local Tunnel Exposure"
Cohesion: 0.18
Nodes (11): 本地应用暴露 / 隧道（--expose-local）, _gen_auth(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。 (+3 more)

### Community 90 - "S3 ResultStore"
Cohesion: 0.19
Nodes (7): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore

### Community 91 - "Subprocess Worker Handle"
Cohesion: 0.16
Nodes (10): _pump_log(), Event, Job, Popen, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的… (+2 more)

### Community 92 - "CDK Context Cache"
Cohesion: 0.19
Nodes (13): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, Path, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。 (+5 more)

### Community 93 - "Job Timeout Handling"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 94 - "Reconciler Concurrency Cap"
Cohesion: 0.14
Nodes (14): 建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。, definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。, meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。, cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…, 缺字段且 SSM 也解析不出 → 抛，**不回落 family 最新 ACTIVE、不回落模板 revision**（ADR 0038 被拒方案）。, _seed_run() (+6 more)

### Community 95 - "Midscene Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 96 - "Cloud Target Resolution"
Cohesion: 0.18
Nodes (14): 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_cloud_target(), resolve_region(), _clear_aws_env(), test_resolve_cloud_target_default_prefix_when_nothing_given(), test_resolve_cloud_target_derives_all_names_from_prefix(), test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven() (+6 more)

### Community 97 - "Ngrok Tunnel Provider"
Cohesion: 0.23
Nodes (12): NgrokTunnel, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None=不写，覆盖超时路径）。, test_ngrok_agent_detaches_from_cli_process_group() (+4 more)

### Community 98 - "S3 Argument Offload"
Cohesion: 0.19
Nodes (7): 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, S3StepArgumentOffloader

### Community 99 - "SQLite Event Log Tests"
Cohesion: 0.23
Nodes (12): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, test_append_and_read_back_events(), test_append_idempotent_same_seq() (+4 more)

### Community 100 - "_stopped_detail"
Cohesion: 0.17
Nodes (12): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, container 缺 exitCode（宽限态）→ None（机制二保守）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, _stopped_detail(), test_exit_observer_records_exit_for_detached_run(), test_exit_observer_skips_non_detached_run() (+4 more)

### Community 101 - "CDK SSM Parameter Guardrails"
Cohesion: 0.15
Nodes (13): Template, SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新档记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值 = task-def 的 `Ref`（**带 revision** 的 ARN）。…, _ssm_params(), test_prefix_switches_whole_set(), test_ssm_parameter_set_is_exactly_six() (+5 more)

### Community 102 - "User-Facing Text Policy (ADR 0039)"
Cohesion: 0.15
Nodes (13): 产品文案禁内部指代（AST 护栏）, README / DEVELOPMENT 按读者分层, ADR 0039: 用户可见面不带内部指代, 0039. 用户可见面不带内部指代：产品文案与文档分层, 代价与权衡, 决策, 对既有文档与 code 的影响, 护栏 (+5 more)

### Community 103 - "Deterministic Step Registry"
Cohesion: 0.18
Nodes (12): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 test engineer 用 `@deterministic(pattern)`…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+4 more)

### Community 104 - "Nova Act Test Doubles"
Cohesion: 0.17
Nodes (5): _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。

### Community 105 - "Publishing Prerequisites Checklist"
Cohesion: 0.15
Nodes (13): 1. PyPI 占名（先于一切）, 2. PyPI trusted publisher × 5（只有真发行的五个需要）, 3. npm trusted publisher（免 token，无 secret）, 4. GHCR：首次推送后把两个 package 改成 public, 5. 仓库本身必须是 public, CI 与发布链（`.github/`）, `release.yml` 的 job 图与重跑语义, TestPyPI 演练（推正式 tag 之前排一次） (+5 more)

### Community 106 - "CLI Package Contributor Docs"
Cohesion: 0.17
Nodes (12): cli 包 —— contributor 文档, plan 的实现细节, RunReport 内部, VPC 档比对（三态）, 为何拆 `submit` / `status`, 从 checkout 跑, 实时落库, 模块 (+4 more)

### Community 107 - "Foundational ADR Principles"
Cohesion: 0.22
Nodes (14): Lambda handler 入口（lambdas/）, ADR 0001 框架范围限定为英文 UI, ADR 0002 不用 gpt-5.5, ADR 0003 Qwen3-VL 定位, ADR 0009 最大化使用 AWS 是硬前提, ADR 0010 spike 作对标基准, ADR 0011 AgentCore 浏览器：默认 vs 自建, ADR 0024 engine 只报原生量、core 不折美元 (+6 more)

### Community 108 - "Execution Model Guide (run/submit)"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的一生, 4. 后台跑批 `submit` 的一生, 4a. local 档：per-run 推进进程, 4b. cloud 档：三 Lambda 链, 4c. 读侧：进度怎么看、结果落在哪, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 109 - "Nova Worker Dev Notes"
Cohesion: 0.17
Nodes (12): 从本 checkout 跑, 使用方 `steps/` 的加载（实现要点）, 依赖分类（踩过的坑）, 包身份, 容器镜像（维护者向）, 布局, 开发笔记（contributor）, 执行形态：薄 worker（cucumber 已退役） (+4 more)

### Community 110 - "User Steps Directory Loader"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 111 - "Fake Event Sink Fixtures"
Cohesion: 0.17
Nodes (7): captured(), _FakeSink, fixture, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。, _reset_stop()

### Community 112 - "Internal-Pointer AST Guardrail"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, _scan_midscene(), _scan_python() (+2 more)

### Community 113 - "Feature Planning to Jobs"
Cohesion: 0.27
Nodes (11): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 严格契约：`features` 的 uri 必须互异（uri…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, test_assertion_votes_from_config_propagates_to_all_jobs(), test_cross_file_scope_merge_warns() (+3 more)

### Community 114 - "CloudFormation/SSM Client Stubs"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 116 - "Midscene Worker Dev Notes"
Cohesion: 0.18
Nodes (11): 容器镜像（维护者向）, 开发笔记（contributor）, 执行形态：薄 worker（pytest-bdd 已退役）, 报告落点, 环境, 相关 ADR, 确定性 step：内建脚手架 vs 使用方的 `steps/`, 跑 spike（可独立跑，不随包发行） (+3 more)

### Community 117 - "Worker READMEs and Harness Docs"
Cohesion: 0.18
Nodes (11): gherkai-worker-novaact README, 定制 worker 镜像携带 steps 到云端, 纯 IAM 鉴权与显式 region, 响亮失败策略（不静默降级）, Nova Act trajectory 产物, Worker 四级定位链 (novaact), Nova Act Worker Process, e2e_harness 使用说明 (+3 more)

### Community 118 - "Fake Sink Test Fixtures"
Cohesion: 0.18
Nodes (5): captured(), _FakeSink, fixture, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 119 - "CI and Release Workflows"
Cohesion: 0.33
Nodes (10): ci.yml 工作流, CI 与发布链说明, release.yml 发布链, release build job（gate + uv build）, release images job（GHCR 基底镜像）, release npm job（@gherkai/worker-midscene）, release pypi job（attest + uv publish）, release GitHub Release job (+2 more)

### Community 120 - "AWS Deploy Contributor Manual"
Cohesion: 0.20
Nodes (10): gherkai-deploy-aws — contributor 手册, Lambda 打包（`stack._build_lambda_asset`）, worker 镜像命令族, 事件驱动推进（无状态跑批）, 包定位与发现面, 命名真源, 本地验证（不碰 AWS）, 模块布局 (+2 more)

### Community 121 - "Exit Observer Lambda"
Cohesion: 0.27
Nodes (9): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+1 more)

### Community 122 - "Task Definition Cleanup"
Cohesion: 0.20
Nodes (5): datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 123 - "Local App Tunneling (ADR 0035)"
Cohesion: 0.20
Nodes (10): 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器, 1. `TunnelProvider` 可插拔口子（`gherkai-runtime` 组合根共享层），首个实现 = ngrok, 2. URL 映射：feature 写原始地址，组装 job 时替换, 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态, 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）, 决策, 背景与问题, 被拒/被缓方案（护栏） (+2 more)

### Community 124 - "Worker Signal Interrupt Tests"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 125 - "ECS Task Timing Script"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 126 - "Deterministic Capability Exposure"
Cohesion: 0.22
Nodes (9): 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询, 1. 注册面扩元数据（暴露的前提）, 2. worker 自述：`--list-deterministic` dump 模式, 3. CLI 子命令 `list-deterministic --engine <name>`, 4. plan 命中标注：「我写的这句会不会命中」, 决策, 背景与问题, 被拒方案（护栏） (+1 more)

### Community 127 - "Dist Metadata Check Script"
Cohesion: 0.39
Nodes (8): fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。, wheel_metadata()

### Community 128 - "Timestamp and Clock Utilities"
Cohesion: 0.22
Nodes (9): now_iso(), parse_iso(), datetime, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的… (+1 more)

### Community 129 - "Tunnel Origin URL Mapping"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 130 - "Worker Exit Code Translation"
Cohesion: 0.25
Nodes (8): raise_for_worker_exit(), worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, test_raise_for_worker_exit_maps_codes_with_fargate_label(), 码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 /…, 两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。, test_raise_for_worker_exit_label_names_the_transport_field(), test_raise_for_worker_exit_maps_codes()

### Community 131 - "Worker Task Def Resolution"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 132 - "Developer Guide Index"
Cohesion: 0.25
Nodes (8): Spike（可独立跑的技术验证脚本）, 发布与版本, 开发环境（从 checkout 跑）, 开发者指南（contributor 入口）, 文档去哪读, 测试, 现状与版本线, 目录结构

### Community 133 - "TypeScript Event Sink"
Cohesion: 0.32
Nodes (3): ADR-0034, EventSink, resolveEventsFd()

### Community 135 - "Environment and Version Resolution"
Cohesion: 0.29
Nodes (5): 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…, _read_ssm_list(), ValueError

### Community 136 - "Midscene Worker Integration Docs"
Cohesion: 0.25
Nodes (7): GHERKAI_STEPS_DIR env contract, @gherkai/worker-midscene README, AgentCore cloud browser (CDP), Deterministic step (user-authored), Qwen3-VL 235B on Bedrock (grounding model), createOpenAIClient injection, sigv4Fetch custom fetch

### Community 137 - "Trajectory Artifact Test Doubles"
Cohesion: 0.33
Nodes (3): 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。, _TrajNova, _TrajResult

### Community 138 - "Subprocess Worker Launcher"
Cohesion: 0.29
Nodes (4): Job, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, SubprocessLauncher

### Community 139 - "Tunnel Setup for Jobs"
Cohesion: 0.29
Nodes (7): 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 140 - "Runtime Package README"
Cohesion: 0.29
Nodes (6): gherkai-runtime, 主要入口, 安装, 最小用法：在本机跑完一批, 注意, 相关

### Community 141 - "Deploy/Destroy CLI Commands"
Cohesion: 0.33
Nodes (6): _cmd_deploy(), _cmd_destroy(), _deploy_provider(), 取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…, [部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。皮零 IaC 知识。 退出码即 provider…, [部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。

### Community 142 - "Scenario JSON Serialization"
Cohesion: 0.33
Nodes (6): _argument_to_json(), Scenario, Step, StepArgument, _scenario_to_json(), _step_to_json()

### Community 143 - "Generic Step Capability ADR"
Cohesion: 0.33
Nodes (6): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）

### Community 144 - "Step Argument Handling (TS)"
Cohesion: 0.53
Nodes (5): argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 145 - "Fargate Network Resolution"
Cohesion: 0.33
Nodes (6): Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, resolve_network(), test_resolve_network_empty_ssm_fails_fast(), test_resolve_network_explicit_overrides_skip_ssm(), test_resolve_network_partial_override_reads_only_missing(), test_resolve_network_reads_ssm_when_missing()

### Community 146 - "Local Detached Run Wiring"
Cohesion: 0.33
Nodes (5): _paths(), 无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, write_tunnel_file()

### Community 147 - "Tunnel Info Model"
Cohesion: 0.33
Nodes (5): 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, TunnelInfo, test_mapped_base_embeds_credentials(), test_mapped_base_without_auth_is_plain_url()

### Community 149 - "Fargate Worker Handle"
Cohesion: 0.40
Nodes (3): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…

### Community 150 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 152 - "Kicker Run ID Extraction"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 153 - "Built-in Deterministic Anchors"
Cohesion: 0.40
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。 用途：少数"必须精确、不容 AI 抖动"的断言（如…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（test engineer 约定的带关键词措辞，与 QA…, url_matches()

### Community 154 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 155 - "Tunnel Cleanup"
Cohesion: 0.40
Nodes (5): cleanup_tunnel(), 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 156 - "AWS Test Fixtures (moto)"
Cohesion: 0.40
Nodes (5): aws(), _fake_aws_creds(), fixture, 硬隔离：假凭证 + 固定 region，绝不误连真 AWS（同 core/tests/conftest.py 的套装）。, moto 下的 ssm / ecs / ecr 三个 client（本 ADR 解析路径要读的全部 AWS 面）。

### Community 157 - "List Deterministic CLI Command"
Cohesion: 0.50
Nodes (4): _cmd_list_deterministic(), 解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认…, 按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern 语义（ADR…, _resolve_steps_dir()

### Community 158 - "Version Skew Test Patches"
Cohesion: 0.50
Nodes (4): _patch_skew(), --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_wait_cloud_kicker_missing_fails_fast()

### Community 159 - "Core Package Contributor Docs"
Cohesion: 0.50
Nodes (4): core 包 —— contributor 文档, 实际执行（跑 .feature）, 模块, 跑测试

### Community 160 - "Scope Done vs ECS Stopped"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), **option-c 定义行为的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR 0032 结论…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_scope_done_waits_for_stopped_before_reading_exit()

### Community 161 - "Lambda Dependency Bundling"
Cohesion: 0.50
Nodes (3): 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it()

### Community 162 - "Live Run Reference Check"
Cohesion: 0.50
Nodes (4): _non_terminal_statuses(), 未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…, 有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…, _referenced_by_live_run()

### Community 163 - "Worker Subnet Single Source"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 165 - "NPM Package Files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 166 - "Package Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 167 - "Runtime Contributor Docs"
Cohesion: 0.50
Nodes (4): runtime 包 —— contributor 文档, 从 checkout 跑 / 测试, 模块, 相关 ADR

### Community 168 - "Worker Command Fixtures"
Cohesion: 0.50
Nodes (4): midscene_env_cmd(), novaact_env_cmd(), fixture, 定位链第一级钉死一个假 novaact cmd：自述用例只验「组合根怎么拼命令/收结果」，不依赖本机装了什么。

### Community 170 - "Cloud Env Fixture"
Cohesion: 0.67
Nodes (3): cloud_env(), fixture, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。

### Community 171 - "AWS Env Fixture"
Cohesion: 0.67
Nodes (3): aws(), _aws_env(), fixture

### Community 172 - "Fargate Engine Composition"
Cohesion: 0.67
Nodes (3): build_fargate_engines（组合根接线）, container 名契约 {engine}-worker, 两个 worker 镜像（Nova / Midscene 各一）

### Community 173 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 175 - "Registry Isolation Fixture"
Cohesion: 0.67
Nodes (3): _isolate(), fixture, 注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。

### Community 176 - "Pure Release Version Check"
Cohesion: 0.67
Nodes (3): is_pure_release(), 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, test_pure_release_predicate()

## Knowledge Gaps
- **324 isolated node(s):** `StepArgument`, `Check`, `Job`, `Scenario`, `ShutdownDeps` (+319 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **67 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Status` connect `Run Result Verdict Model` to `Engine Ports & Adapters`, `Worker Image Push Workflow`, `SQLite Event Log & Projection`, `DynamoDB RunStore Conditional Writes`, `Fake DynamoDB Table`, `Run State Rendering & Boto Guard`, `Render & ReportStore Local`, `Subprocess Worker Launcher`, `Cloud Launcher & DDB EventLog`, `Run Schedule Orchestration`, `Fake S3 Client`, `Terminal Status Aggregation`, `Reconcile Ports & Tick`, `Event Formatting & Cost Model`, `Conditional Write Contract Tests`, `ResultStore Local/S3`, `Run Persistence Orchestration`, `Reconciler Lambda & Timeouts`, `Wire Protocol Serialization`, `Fargate Engine Unit Tests`, `Tunnel Host TTL Watchdog`, `Subprocess Engine Integration`, `Job Timeout Handling`, `SQLite Event Log Tests`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `schedule()` connect `Run Schedule Orchestration` to `Run Result Verdict Model`, `Run Persistence Orchestration`, `Environment and Version Resolution`, `Run State Rendering & Boto Guard`, `Subprocess Engine Integration`, `Terminal Status Aggregation`, `Event Formatting & Cost Model`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `RunMeta` connect `Run State Rendering & Boto Guard` to `Engine Ports & Adapters`, `Timestamp and Clock Utilities`, `Run Result Verdict Model`, `SQLite Event Log & Projection`, `DynamoDB RunStore Conditional Writes`, `Render & ReportStore Local`, `Subprocess Worker Launcher`, `Cloud Launcher & DDB EventLog`, `Run Schedule Orchestration`, `Reconcile Ports & Tick`, `Event Formatting & Cost Model`, `Conditional Write Contract Tests`, `ResultStore Local/S3`, `Run Persistence Orchestration`, `CLI Run/Submit Commands`, `Detached Launcher Reconcile`, `Subprocess Engine Integration`, `Reconcile Loop Integration`, `Job Timeout Handling`, `Reconciler Concurrency Cap`, `SQLite Event Log Tests`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `RunMeta` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunMeta` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `RunState` (e.g. with `DynamoDBRunStore` and `LocalRunStore`) actually correct?**
  _`RunState` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `Status` (e.g. with `_FakeS3` and `_FakeTable`) actually correct?**
  _`Status` has 41 INFERRED edges - model-reasoned connections that need verification._