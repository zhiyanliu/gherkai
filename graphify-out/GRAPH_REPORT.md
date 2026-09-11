# Graph Report - yaozhou  (2026-09-11)

## Corpus Check
- 243 files · ~241,639 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 4693 nodes · 9701 edges · 346 communities (218 shown, 128 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 532 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `015d9e65`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _Worker
- model.py
- workers.py
- test_backend_cloud.py
- main
- test_stores.py
- test_workers.py
- ContainerEngine
- tick
- Provider
- evidence.py
- preflight_cloud_resources
- Job
- test_stack.py
- gherkai_runtime/names.py
- render.py
- test_deploy_cmd.py
- test_schedule.py
- DynamoDBRunStore
- test_worker_variant.py
- run_scope.py
- test_container.py
- _progress
- _engine
- Execution Architecture Decisions
- evidence.mts
- _FakeResult
- app.py
- RunPersistence
- core/DEVELOPMENT.md
- conftest.py
- fargate_engine.py
- test_project.py
- _run_step
- Nova Engine Probes
- test_conditional_writes.py
- subprocess_engine.py
- ._run_cdk
- test_interrupt_model.py
- _is_transient_network
- BackendStack
- SqliteEventLog
- test_user_steps.py
- test_lambda_asset.py
- test_lambda_handlers.py
- report_store/local.py
- CONTEXT.md 领域术语表
- _ask_worker
- main
- test_plan.py
- reconciler.py
- build_engines
- LocalRunStore
- Packaging & Distribution ADR
- TypeScript Config
- test_event_sink.py
- test_tunnel_cli.py
- test_deterministic.py
- test_job_source.py
- deploy_aws/README.md
- FargateEngine
- _tagged_feature
- user-steps.mts
- reconcile.tick（无状态推进一步，四宿主共用）
- check_node
- RunStore
- test_argument.py
- _ssm_params
- schedule.py
- Worker Image ADR
- _MissingThenStoppedEcs
- test_tunnel_host.py
- test_package_readmes.py
- require_boto3
- run-scope.test.mts
- JS Dependencies
- gherkai deploy push-worker（八步流程）
- deterministic.mts
- tunnel.py
- test_cloud_reconcile.py
- _StampSsm
- Event Wallclock Analysis
- .add_arguments
- _Recorder
- deploy.py
- _render_status
- container.py
- deterministic_steps.py
- resolve_container_engine
- _FakeEcs
- NPM Package Manifest
- test_tunnel.py
- 判定是怎么算出来的：从一票到退出码
- _engine_with_fake_ecs
- LocalReportStore
- 0039. 用户可见面不带内部指代：产品文案与文档分层
- check_version_skew
- test_finalize_writes_verdicts_before_commit_point
- Release & CI Setup
- CLI Contributor Docs
- test_wire.py
- wire.py
- _stopped_detail
- Execution & Progression Model Guide
- Worker Package Dev Notes
- _explain_run
- 0042. step 级机读证据（evidence）与 `gherkai explain`
- test_user_facing_messages.py
- _ClientError
- ArtifactUploader
- 开发笔记（contributor）
- _cmd_status
- Nova Act Worker README
- Fake Sink Test Doubles
- CI & Release Workflows
- AWS Deploy Contributor Guide
- cli.py
- test_sqlite_event_log.py
- _StubEcs
- ADR 0035 Local App Tunnel
- Worker Signal Interrupt Tests
- ECS Task Timing Script
- StepResult
- test_artifact_upload.py
- 0040. 使用方角色模型与术语
- ADR 0036 Deterministic Capability
- Dist Metadata Check
- _job_with
- Graphify Refresh Script
- ArtifactUploader
- evidence.test.mts
- 开发者指南（contributor 入口）
- event-sink.mts
- S3StepArgumentOffloader
- JobState
- agentcore-sigv4.mts
- Runtime Package README
- argument.mts
- ADR 0018 Common Steps
- _UnavailableEngine
- deterministic.py
- Fake S3 Client
- Echo Test Worker
- Cloud Test Infra Selfcheck
- test_evidence.py
- TypeScript Dev Dependencies
- test_fargate_engine.py
- _presend_act_siblings
- Path
- build_fargate_engines
- user_steps.py
- Worker Subnet Single Source
- arg_offload.py
- NPM Package Files
- Repository Metadata
- _patch_skew
- deterministic.steps.mts
- parse_feature
- aws
- scope.py
- NPM Scripts
- AgentCore CDP Spike
- job-source.mts
- Bedrock AgentCore SDK
- DynamoDB SDK
- build_local_reconcile
- Adapters Package Init
- compose.py
- Core Package Init
- test_detached_launcher.py
- _stream_record
- ._installed_import_source
- build_fargate_engines（组合根接线）
- artifact-upload.test.mts
- ADR Language Split Decisions
- OpenAI Dependency
- tsx Dependency
- Index Wait Script
- Workspace Package Identity
- _AbsentEngine
- _seed_run
- fixture
- _CdkWritingContext
- Job Result
- Run Meta
- Run Result
- exit_observer.py
- plan
- ReportStore
- Run Meta
- WorkerHandle
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
- _explain_emit
- Engine Resolver
- _fake_locator
- Shared Gherkin Feature Files
- Job Sink
- test_s3_report_store.py
- test_compose.py
- Gherkai Core Package
- AWS Deployment Package
- Gherkai Runtime Package
- NovaAct Worker Package
- Report Store
- test_cli_json_contract.py
- _FakeTable
- 03-midscene-grounding.ts
- _RecUploader
- Subprocess Engine
- Sink Interface
- FargateWorkerHandle
- 05-negative-assertions.ts
- gherkai CLI 的 `--json` 字段契约
- parametrize
- parametrize
- Job
- 决策
- gherkai_cli/__init__.py
- e2e_harness.py
- Path
- gherkai_cli/__main__.py
- Job
- ADR-0020
- ImageInfo
- Job
- digest_for_repo
- Job
- Job
- test_provider_module_does_not_import_aws_cdk
- Popen
- scenario_key
- Job
- Protocol
- no-artifacts.test.mts
- ResultStore
- Job
- Scenario
- Step
- ADR-0022
- ADR-0026
- raise_for_worker_exit
- Job
- ADR-0027
- JobResult
- JobState
- RunResult
- RunState
- Status
- Protocol
- Exception
- ADR-0035
- novaact/DEVELOPMENT.md
- _FakeSchedulerClient
- start_tunnel_for_jobs
- _delayed_stopped_ecs
- JobResult
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- CONNECT_BACKOFF_MS
- S3ReportStore
- ADR-0014
- RunResult
- Event
- fixture
- ADR-0024
- CloudTarget
- datetime
- Exception
- RunMeta
- Path
- RuntimeError
- test_run_state_timestamps_share_one_format
- detached.py
- _isolate
- SubprocessLauncher
- cloud_env
- list_workers
- ADR-0028
- ReportRef
- Spy
- runtime 包 —— contributor 文档
- EventBridgeTimeoutWatch
- fixture
- ResourceUri
- Template
- ADR-0029
- RunMeta
- LocalRunStore
- .inspect
- RuntimeError
- .preflight
- ArgumentParser
- Event
- RunMeta
- artifact_upload.py
- Job
- _Calls
- RunState
- ADR-0031
- parametrize
- Scenario
- Step
- StepArgument
- RunMeta
- Job
- ADR-0032
- ADR-0036
- ADR-0037
- ADR-0042
- ADR-0019
- 云端后端由哪些载体拼成：一次改动要传播到哪几处才生效
- core 包 —— contributor 文档
- BaseException
- list
- Scenario
- ShutdownDeps
- Step
- _argv
- 一条确定性 step 的一生：从你写下正则到它在云端命中
- test_explain_cloud_reads_evidence_from_s3
- ._read_s3
- _spy_run_meta
- 产物与证据地理：跑完了东西在哪、哪一份答哪个问题（local × cloud）
- test_star_step_keyword_fails_fast
- test_leading_and_keyword_fails_fast
- ADR 0024 worker↔core 协议
- test_bucket_without_logs_dir_fails_loud
- BoomLauncher
- EventLog
- parametrize
- Launcher
- .delete_worker
- test_target_closed_by_name_fallback_hits_inside_chain

## God Nodes (most connected - your core abstractions)
1. `main()` - 171 edges
2. `Provider` - 83 edges
3. `schedule()` - 61 edges
4. `CollectSink` - 59 edges
5. `FakeEngine` - 56 edges
6. `Job` - 55 edges
7. `RunMeta` - 55 edges
8. `JobState` - 54 edges
9. `FakeResolver` - 53 edges
10. `_job()` - 49 edges

## Surprising Connections (you probably didn't know these)
- `_status_cloud()` --calls--> `DynamoDBRunStore`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/run_store/ddb.py
- `_build()` --calls--> `DynamoDBRunStore`  [INFERRED]
  deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py → core/gherkai_core/adapters/run_store/ddb.py
- `build_cloud_stores()` --calls--> `DynamoDBRunStore`  [INFERRED]
  runtime/gherkai_runtime/compose.py → core/gherkai_core/adapters/run_store/ddb.py
- `_cmd_run()` --calls--> `RunMeta`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/model.py
- `_cmd_submit()` --calls--> `RunMeta`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/model.py

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

## Communities (346 total, 128 thin omitted)

### Community 0 - "_Worker"
Cohesion: 0.19
Nodes (10): _heartbeat_wrap(), Event, JobResult, Status, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…, 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在… (+2 more)

### Community 1 - "model.py"
Cohesion: 0.06
Nodes (87): _explain_job(), 多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本/JSON 同律）；命中的 scope 的…, test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact(), Job, JobState, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。… (+79 more)

### Community 2 - "workers.py"
Cohesion: 0.06
Nodes (70): Aws, current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable(), ImageMapping, init_default_pointer() (+62 more)

### Community 3 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (93): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, local run 的 definition 不带这两个字段（omit-when-None，ADR 0038「local 档不写」）。, 后端默认指针本身是个非法 variant 名（部署侧写坏）→ 退 2 并点名那个 SSM 参数，不冒 traceback。 显式 `--worker-…, patch store 钩子 + preflight（默认放行）+ 版本 skew 闸 + worker variant 闸（都默认放行）返回记录调用的… (+85 more)

### Community 4 - "main"
Cohesion: 0.05
Nodes (98): main(), _capturing_schedule(), _det_feature(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用）， 验证落盘三层产物 + --json…, --quiet（ADR 0041 决策二）：worker 日志落 <run_dir>/worker.log（--no-report… (+90 more)

### Community 5 - "test_stores.py"
Cohesion: 0.07
Nodes (59): S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, JobResult (+51 more)

### Community 6 - "test_workers.py"
Cohesion: 0.07
Nodes (80): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+72 more)

### Community 7 - "ContainerEngine"
Cohesion: 0.16
Nodes (8): ContainerEngine, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。, 拉镜像（基底同步用）。`platform` 给了就显式指定，避免在 arm Mac 上拉到 arm 变体。, 短命令：捕输出、失败即抛（**stderr 不直通**——login 的失败要能包进我们的文案里）。, 长命令（push/pull）：stdio 直通、只看返回码。进度条对用户有价值，捕下来反而是把它憋住。, docker CLI 的五动词薄壳（子进程调用；不用 SDK——多一个依赖、且 podman 的 SDK 不同形）。 `binary`…, test_probe_reports_missing_binary_without_raising()

### Community 8 - "tick"
Cohesion: 0.12
Nodes (29): RunMeta, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), _done_events(), FakeLauncher, _meta(), RunMeta, reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。 用真… (+21 more)

### Community 9 - "Provider"
Cohesion: 0.07
Nodes (62): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, flag 面全集钉死（枚举型护栏）：三个 context 旋钮 flag + AWS 定位二件套 + 两个「皮的中立版的 AWS 精确化」（见 cli…, 子动词全集钉死（枚举型护栏）+ **只挂 deploy**。 挂到 destroy 上不是「多个没用的命令」而是危险：皮的 destroy 分派不看…, 子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。 (+54 more)

### Community 10 - "evidence.py"
Cohesion: 0.08
Nodes (44): Any, act_evidence(), _actions(), ActRecord, _calls(), _decode_data_url(), _kwargs(), Path (+36 more)

### Community 11 - "preflight_cloud_resources"
Cohesion: 0.15
Nodes (16): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), 跑一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。 (+8 more)

### Community 13 - "test_stack.py"
Cohesion: 0.04
Nodes (17): BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler/kicker）都要能读 `/{prefix}backend/*`（ADR 0038「权限面增量·云端推进器」）： 没有…, IAM 资源 ARN 已收窄（ADR 0033）——回归护栏：防将来改回 * 或踩 account=aws 陷阱。 收窄依据 = AWS SAR…, reconciler/kicker 的 `MAX_CONCURRENCY` = **部署侧 per-run cap**（非并发真源——真源是… (+9 more)

### Community 14 - "gherkai_runtime/names.py"
Cohesion: 0.07
Nodes (34): 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_worker_template_path(), gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…, container_name(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix() (+26 more)

### Community 15 - "render.py"
Cohesion: 0.10
Nodes (27): _act_lines(), _arg_hint(), _cost_bits(), _dispatch_hint(), _evidence_ref(), explain_step_expands(), _ms(), _one_line() (+19 more)

### Community 16 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (47): _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。, 皮自己的命令面 flag（`--require-approval` / `--allow-vpc-change`）也落在同一个 args 上给… (+39 more)

### Community 17 - "test_schedule.py"
Cohesion: 0.05
Nodes (129): format_event(), 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。, SubprocessEngine (+121 more)

### Community 18 - "DynamoDBRunStore"
Cohesion: 0.08
Nodes (25): DynamoDBRunStore, _job_state_from_item(), _job_state_to_item(), JobState, RunMeta, RunState, Status, DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`… (+17 more)

### Community 19 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (51): （引擎，镜像 tag）→ revision 映射的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。 值 =…, worker_image_key(), aws(), _fake_aws_creds(), _push_image(), fixture, worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。 (+43 more)

### Community 20 - "run_scope.py"
Cohesion: 0.07
Nodes (38): ActRecord, ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _act_record(), _attach_evidence(), _attach_traj_refs(), _collect_traj(), _cost_from_result() (+30 more)

### Community 21 - "test_container.py"
Cohesion: 0.18
Nodes (12): _Fake, _inspect_spec(), 容器引擎口子测试（ADR 0038「容器引擎口子」）。 **两层证据，分清边界**： - 大部分用一个**假 docker**（记 argv/stdin 的…, 「本地没这个镜像」是正常分叉（调用方给专属提示），不是异常。, **密码绝不进 argv**（同机任何进程 `ps` 可见，ECR 令牌 12 小时有效）——`--password-stdin`。, 假 docker 的把手：`engine` 是指着 shim 的 ContainerEngine，`calls` 读回它收到了什么。, test_inspect_missing_image_is_not_an_error(), test_inspect_other_failure_raises() (+4 more)

### Community 22 - "_progress"
Cohesion: 0.09
Nodes (36): _build_selector(), _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_list_deterministic(), _cmd_plan(), _cmd_run(), _cmd_submit(), _load_and_plan() (+28 more)

### Community 23 - "_engine"
Cohesion: 0.12
Nodes (34): _engine(), _job(), _put_event(), _put_exit_item(), worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。, 预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。, exit item 与 worker 事件同 PK 共存：主循环只读 worker 段、正常产出并按退出码收敛，不碰无 body 的 exit item。 (+26 more)

### Community 24 - "Execution Architecture Decisions"
Cohesion: 0.07
Nodes (41): 决策 A：cli --backend {local,cloud} 单旋钮, compose.build_local_stores / build_cloud_stores, 组合根注入（选实现不由 module 自选）, 核心库窄腰 core/（解析→分组→调度→收集，零引擎依赖）, 决策 B：subprocess + 注入云存储 = 内部预演手段, 决策 C：Fargate/region/profile 配置走 CLI 参数注入, Engine port（run_scope(job) → 事件流）, FargateEngine（云端执行 adapter） (+33 more)

### Community 25 - "evidence.mts"
Cohesion: 0.09
Nodes (29): actionsOf(), buildEvidence(), BuildEvidenceInput, errorTextOf(), EVIDENCE_KIND, EVIDENCE_SCHEMA_VERSION, EvidenceAct, EvidenceDoc (+21 more)

### Community 26 - "_FakeResult"
Cohesion: 0.12
Nodes (8): _ActBoom, _FakeResult, _Meta, _NavErrorNova, RuntimeError, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, 模拟 Nova SDK 的 act 异常：与成功结果一样带 metadata（time_worked_s 已真实计费、trajectory 已写盘）。

### Community 27 - "app.py"
Cohesion: 0.25
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（= `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 28 - "RunPersistence"
Cohesion: 0.08
Nodes (36): ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, LocalResultStore, JobResult, Path, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。 (+28 more)

### Community 29 - "core/DEVELOPMENT.md"
Cohesion: 0.31
Nodes (15): core 测试说明（单测 vs 集成）, 绿≠对 Verification Escalation, ADR 0011 AgentCore 浏览器：默认 vs 自建, ADR 0016 执行架构, ADR 0025: plan 模块（.feature → job 列表）, ADR 0026 schedule 契约, ADR 0030 实时写接缝, ADR 0033 IaC 与装配 (+7 more)

### Community 30 - "conftest.py"
Cohesion: 0.15
Nodes (18): arg_offloader(), aws(), ddb_run_store(), ddb_run_store_offload(), _fake_aws_creds(), fargate(), fixture, 云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -… (+10 more)

### Community 31 - "fargate_engine.py"
Cohesion: 0.15
Nodes (10): adapters/_boto.py 依赖守卫, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, events_pk(), Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, 一次 DescribeTasks 探测的结果——**三个正交事实各自命名**（ADR 0024「exitCode 落值延迟」；前两个见下、第三个…, events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。, TaskProbe (+2 more)

### Community 32 - "test_project.py"
Cohesion: 0.05
Nodes (105): DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, scope 内短路事件（ADR 0031 决定六 / 0024）：上游 step error 后，worker 跳过本 step、不调 AI。…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, ScopeStarted, Status, StepSkipped, StepStarted (+97 more)

### Community 33 - "_run_step"
Cohesion: 0.11
Nodes (40): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory + evidence reportRefs），返回…, scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_scenario(), _run_step(), _done(), _FakeNova (+32 more)

### Community 34 - "Nova Engine Probes"
Cohesion: 0.10
Nodes (25): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+17 more)

### Community 35 - "test_conditional_writes.py"
Cohesion: 0.10
Nodes (42): _initial(), _meta(), RunMeta, RunState, RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。… (+34 more)

### Community 36 - "subprocess_engine.py"
Cohesion: 0.14
Nodes (14): 执行引擎 port（Engine）, _join_pumps(), _pump_log(), Job, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker… (+6 more)

### Community 37 - "._run_cdk"
Cohesion: 0.09
Nodes (16): Path, 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。… (+8 more)

### Community 38 - "test_interrupt_model.py"
Cohesion: 0.06
Nodes (35): _aggregate(), _backoff_interrupted(), _emit_scenario_done_unless_stopped(), _on_signal(), SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。 绝不…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…, 建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True=退避中收到停止信号（应停止重连）。 用…, captured() (+27 more)

### Community 39 - "_is_transient_network"
Cohesion: 0.16
Nodes (25): _is_transient_network(), 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 造一个 botocore ClientError（response 里带 Error.Code /…, _target_closed(), test_agentcore_permanent_wrapping_chain_not_transient(), test_agentcore_startfailed_wrapping_chain_is_transient() (+17 more)

### Community 40 - "BackendStack"
Cohesion: 0.11
Nodes (16): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+8 more)

### Community 41 - "SqliteEventLog"
Cohesion: 0.16
Nodes (10): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+2 more)

### Community 42 - "test_user_steps.py"
Cohesion: 0.12
Nodes (28): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。, 真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。… (+20 more)

### Community 43 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (25): make_stack(), make_template(), Template, synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources() (+17 more)

### Community 44 - "test_lambda_handlers.py"
Cohesion: 0.09
Nodes (24): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, Stream records + 直接 run_id 并存时都提取（健壮）。, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。 (+16 more)

### Community 45 - "report_store/local.py"
Cohesion: 0.11
Nodes (19): ReportStore adapters（ADR 0027）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…, collect_report_index(), _fmt_ms(), local_path_from_uri(), Path, RunResult, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run… (+11 more)

### Community 46 - "CONTEXT.md 领域术语表"
Cohesion: 0.08
Nodes (28): CONTEXT.md 领域术语表, 推进器 advancer, AgentCore 浏览器会话, 确定性断言 vs AI 断言, 两个引擎都子进程 + 薄 worker, 执行核心库窄腰, 成本可观测, 部署 provider（gherkai.deploy entry point） (+20 more)

### Community 47 - "_ask_worker"
Cohesion: 0.14
Nodes (12): _ask_worker(), local_artifact_locations(), match_deterministic(), Path, worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…, 定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退码交调用点。 **继承 RuntimeError…, spawn 一次某引擎 worker 的**自述入口**、收一行 JSON（ADR 0036 决策 2/4 的共同机制）。 自述入口不建会话、不读 job、零…, 批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker… (+4 more)

### Community 48 - "main"
Cohesion: 0.16
Nodes (10): cumulativeTokens(), drainArtifactQueue(), isTransientNetwork(), log(), main(), runScenario(), runStep(), shutdownSequence() (+2 more)

### Community 49 - "test_plan.py"
Cohesion: 0.17
Nodes (21): _plan(), plan 模块 test cases（ADR 0025 护栏）：parse + scope 分组 + engine 校验 + id 派生。, test_assertion_votes_default_is_one(), test_background_prepended(), test_datatable_and_docstring_argument(), test_engine_conflict_errors(), test_engine_default(), test_engine_inherited_within_scope() (+13 more)

### Community 50 - "reconciler.py"
Cohesion: 0.13
Nodes (21): finalize_report(), done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…, _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING… (+13 more)

### Community 51 - "build_engines"
Cohesion: 0.08
Nodes (30): Engine, FeatureSource, build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。 (+22 more)

### Community 52 - "LocalRunStore"
Cohesion: 0.06
Nodes (36): RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…, _atomic_write_json(), LocalRunStore, JobState, Path, RunMeta, RunState, Status (+28 more)

### Community 53 - "Packaging & Distribution ADR"
Cohesion: 0.08
Nodes (24): 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel, 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条, 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵, 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra, 2d. `requires-python >=3.13` 维持, 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）, 决策 1：交付物按打包技术划分，worker 运行时是硬核, 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first (+16 more)

### Community 54 - "TypeScript Config"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 55 - "test_event_sink.py"
Cohesion: 0.10
Nodes (9): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud(), test_emit_flushes_each_event() (+1 more)

### Community 56 - "test_tunnel_cli.py"
Cohesion: 0.13
Nodes (22): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+14 more)

### Community 57 - "test_deterministic.py"
Cohesion: 0.14
Nodes (21): deterministic(), list_registry(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。 (+13 more)

### Community 58 - "test_job_source.py"
Cohesion: 0.13
Nodes (7): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。, test_s3_uri_without_key_fails_loud()

### Community 59 - "deploy_aws/README.md"
Cohesion: 0.12
Nodes (20): worker 镜像：基底 / variant / 默认指针, gherkai-deploy-aws, gherkai deploy push-worker, 后端版本戳与三步升级, VPC 三档与四态档位比对, VPC 三档, 安装与前置, 帮助 (+12 more)

### Community 60 - "FargateEngine"
Cohesion: 0.18
Nodes (11): FargateEngine, Event, Job, Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR… (+3 more)

### Community 61 - "_tagged_feature"
Cohesion: 0.14
Nodes (15): _plan_names(), 一个 --tags 值内逗号 = 任一命中；重复 --tags = 都要命中；@ 可省。, --scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。, 筛空 → 退 2 并列全部候选（id 标题），别静默跑空批。, run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。, 纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是…, --scope = 报告里的 scope_id：named scope 的名字选中整个 scope（两条都跑），未标 scope 的用 <文件>:<行>； 与…, _tagged_feature() (+7 more)

### Community 62 - "user-steps.mts"
Cohesion: 0.11
Nodes (12): fromSource, hookSpec, ADR-0028, ADR-0037, ADR-0022, ADR-0036, collectStepFiles(), loadUserSteps() (+4 more)

### Community 63 - "reconcile.tick（无状态推进一步，四宿主共用）"
Cohesion: 0.12
Nodes (19): _aggregate（run 级 status 聚合）, _NON_VERDICT 过滤名单, StepResult.shortcircuited（正交布尔）, Status enum（加 SKIPPED/ABORTED/PENDING/RUNNING）, _STATUS_SEVERITY 数值序, StepSkipped 事件（step 级短路）, TERMINAL_STATUSES（终态真源，取补）, stopTimeout=120 / grace 预算标定 (+11 more)

### Community 64 - "check_node"
Cohesion: 0.14
Nodes (13): cdk_command(), check_node(), _make_sts_client(), _node_major(), boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…, `gherkai doctor` 的 provider 段（ADR 0041 决策四）：部署方工具链**只读**自检——Node ≥ 22、cdk…, cdk CLI 的调用前缀：PATH 上的 `cdk` 优先，否则 `npx -y aws-cdk@2`（ADR 0037 决策 6）。都没有 → 空列表。 (+5 more)

### Community 65 - "RunStore"
Cohesion: 0.14
Nodes (9): JobState, RunMeta, RunState, Status, CAS 抢占：仅当该 job 当前是 PENDING 才置 RUNNING，成功返回 True（机制四）。 多个 reconciler 实例并发抢同一…, HWM 条件写整个 RunState：仅当 state.high_water_mark ≥ 库中记录的 hwm 才写，成功 True（机制三）。 stale…, 状态机单调条件写：仅当 run 总 status 当前为非终态（pending/running）才写终态，成功 True（机制三）。 挡「已 finalize…, 控制面：一次 run 的 **definition（RunMeta）+ 运行态（RunState）**，不存判定明细（ADR 0016 三层切分）。… (+1 more)

### Community 66 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 67 - "_ssm_params"
Cohesion: 0.12
Nodes (17): _advancer_stmts(), SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新档记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值 = task-def 的 `Ref`（**带 revision** 的 ARN）。…, 某推进器执行角色上的全部 policy 语句（规范化成可比字符串）。剔掉 event source mapping 自动加的 Stream 读语句——…, 两个推进器**权限面同一份**（ADR 0034：同一套装配与权限，只换 handler 与触发源）。按角色归属逐条比对——曾各写一段、 单侧摘掉…, _ssm_params() (+9 more)

### Community 68 - "schedule.py"
Cohesion: 0.26
Nodes (11): Engine, EngineResolver, JobSink, ports 层（ADR 0016 六边形架构）：核心只依赖这些接口，具体 adapter 由组合根注入。 四个 port（关注点拆开，不揉成上帝…, 执行引擎 port（ADR 0016）。 schedule 经此起 worker；adapter 形状一致（spawn node 子进程 / spawn…, Sink, _Heartbeat, schedule 模块（ADR 0026）：Job[] → 并发跑 → 收流式事件 → RunResult。 job 间并行（maxConcurrency… (+3 more)

### Community 69 - "Worker Image ADR"
Cohesion: 0.11
Nodes (19): 0038. worker 镜像交付：基底、variant 与推送注册, `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）, `push-worker` 流程, SSM 参数与命名真源, 不变量, 与版本升级的交互, 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）, 多版本与多环境 (+11 more)

### Community 70 - "_MissingThenStoppedEcs"
Cohesion: 0.14
Nodes (14): _ev_item(), _gap_engine(), _MissingThenStoppedEcs, 裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。, 洞在宽限后仍在 = 写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。, 前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。, 无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…, 瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。 (+6 more)

### Community 71 - "test_tunnel_host.py"
Cohesion: 0.12
Nodes (22): RunState, compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。 (+14 more)

### Community 72 - "test_package_readmes.py"
Cohesion: 0.15
Nodes (13): 文档纪律（ADR / CONTEXT / journey / guides）, 使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…, GitHub Release 正文 = Releases 页面，且是各包 pyproject `[project.urls] Changelog`…, contributor 内容有明确去处（不是被删掉）：根目录与每个包目录各一份 DEVELOPMENT.md。, 根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归 DEVELOPMENT.md）。…, pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…, release.yml 里 `body: |` 块标量的正文。不引 yaml 库（dev 依赖里没有它、别为一条护栏引入）：按缩进收块。, _release_bodies() (+5 more)

### Community 73 - "require_boto3"
Cohesion: 0.20
Nodes (5): 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…

### Community 74 - "run-scope.test.mts"
Cohesion: 0.11
Nodes (11): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+3 more)

### Community 75 - "JS Dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 76 - "gherkai deploy push-worker（八步流程）"
Cohesion: 0.12
Nodes (19): BackendStack 资源清单（DDB/S3/ECS/IAM/SSM/Lambda）, 两层命名：prefix 批量默认 + 单资源覆盖, preflight fail-fast（探资源存在性、点名 prefix）, task role IAM 最小权限（动作 × 资源两维收窄）, VPC 来源三档（复用/默认/建新，零 NAT）, RunMeta.extra_http_headers（额外请求头通道）, 隧道宿主三形态 + TTL 兜底, TunnelProvider 口子（首个实现 ngrok） (+11 more)

### Community 77 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 78 - "tunnel.py"
Cohesion: 0.18
Nodes (11): 本地应用暴露 / 隧道（--expose-local）, _gen_auth(), 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。 (+3 more)

### Community 79 - "test_cloud_reconcile.py"
Cohesion: 0.06
Nodes (50): CloudLauncher, Job, CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。… (+42 more)

### Community 80 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, BACKEND_VERSION_KEY)`，由 stack 资源随部署事务写入，ADR…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 凭证/权限/region 类错误照抛——由入口皮归到自己的退出码层，不伪装成「没有戳」。, 读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。 (+10 more)

### Community 81 - "Event Wallclock Analysis"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 82 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 83 - "_Recorder"
Cohesion: 0.13
Nodes (12): cdk(), _clean_aws_env(), _FakeEngine, fixture, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。… (+4 more)

### Community 84 - "deploy.py"
Cohesion: 0.10
Nodes (21): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, 把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。 (+13 more)

### Community 85 - "_render_status"
Cohesion: 0.18
Nodes (18): 渲染 RunState + pending 诊断提示 + 终态产物位置 + 退出码——**local/cloud 共享一份**（保两路一致，ADR…, _render_status(), _args(), _mk_state(), run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…, 终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。, pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。 (+10 more)

### Community 86 - "container.py"
Cohesion: 0.16
Nodes (10): ContainerError, Exception, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 报错里带的引擎输出：去空白 + 只留尾部（docker 的失败原因在最后几行，前面全是层进度）。, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, 要求了本期未实装的容器引擎（ADR 0038：只 docker）。 (+2 more)

### Community 87 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。 用途：少数"必须精确、不容 AI 抖动"的断言（如…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（测试开发约定的带关键词措辞，与 QA 的纯自然语言…, url_matches()

### Community 88 - "resolve_container_engine"
Cohesion: 0.18
Nodes (14): 选容器引擎：`--container-engine` > env `GHERKAI_CONTAINER_ENGINE` > `docker`。 本期外的名字…, resolve_container_engine(), ADR 0038 步 2 那条事实：**本地 build、从未推过的镜像 `RepoDigests` 为空** → 推送前拿不到 digest。…, arm 变体真镜像 → 架构判据拒（= push-worker 退 2 那一支）。 用 alpine（小）代替真 worker 镜像：判据只看…, `docker tag` 到 ECR ref **不会**产生 registry digest（只有 push 才会）——第二次确认「推送后才取…, `--container-engine podman` **不静默回落 docker**：回落会让人以为自己验过 podman 路径（ADR 0038）。, test_default_is_docker(), test_env_selects_engine_and_flag_wins() (+6 more)

### Community 89 - "_FakeEcs"
Cohesion: 0.10
Nodes (16): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器。`task_arns` = 在跑的 task；`tasks` = 带状态的…, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…, task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录… (+8 more)

### Community 90 - "NPM Package Manifest"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 91 - "test_tunnel.py"
Cohesion: 0.13
Nodes (20): NgrokTunnel, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, stop_tunnel(), TunnelInfo, _fake_popen_writing_log() (+12 more)

### Community 92 - "判定是怎么算出来的：从一票到退出码"
Cohesion: 0.20
Nodes (10): 1. 四层归约：一票 → step → scenario → job → run, 2. 七个状态：含义与「我该做什么」, 3. 两根正交的轴，和 `error_type` 家族, 3a. `status` × `shortcircuited`, 3b. `error_type`：谁在赋、赋什么, 3c. 两个常被问的分类边界, 4. severity：不是字母序；以及 run 级为什么没有 skipped/aborted, 5. 退出码：每条命令回答的是**不同的问题** (+2 more)

### Community 93 - "_engine_with_fake_ecs"
Cohesion: 0.17
Nodes (10): _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…, 持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。, test_await_exit_code_missing_task_beyond_grace_raises(), test_probe_task_missing_is_a_third_state_not_running(), test_probe_task_not_stopped() (+2 more)

### Community 94 - "LocalReportStore"
Cohesion: 0.19
Nodes (35): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, ScenarioResult, _jr(), JobResult, Path, RunResult, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。 (+27 more)

### Community 95 - "0039. 用户可见面不带内部指代：产品文案与文档分层"
Cohesion: 0.20
Nodes (10): 0039. 用户可见面不带内部指代：产品文案与文档分层, 代价与权衡, 决策, 对既有文档与 code 的影响, 护栏, 背景与问题, 被拒方案（护栏，防未来重踩）, 重议闸门 (+2 more)

### Community 96 - "check_version_skew"
Cohesion: 0.08
Nodes (26): check_version_skew(), variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…, PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `_is_pure_release`…, 比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, _release_cmp(), _release_key(), _variant_miss_hint() (+18 more)

### Community 97 - "test_finalize_writes_verdicts_before_commit_point"
Cohesion: 0.22
Nodes (5): _OrderRecordingRunStore, LocalRunStore, 全 done 的 tick：ResultStore 各 job 判定真值**先**落，再 try_finalize（ADR 0030…, _RecordingResultStore, test_finalize_writes_verdicts_before_commit_point()

### Community 98 - "Release & CI Setup"
Cohesion: 0.15
Nodes (13): 1. PyPI 占名（先于一切）, 2. PyPI trusted publisher × 5（只有真发行的五个需要）, 3. npm trusted publisher（免 token，无 secret）, 4. GHCR：首次推送后把两个 package 改成 public, 5. 仓库本身必须是 public, CI 与发布链（`.github/`）, `release.yml` 的 job 图与重跑语义, TestPyPI 演练（推正式 tag 之前排一次） (+5 more)

### Community 99 - "CLI Contributor Docs"
Cohesion: 0.17
Nodes (12): cli 包 —— contributor 文档, plan 的实现细节, RunReport 内部, VPC 档比对（三态）, 为何拆 `submit` / `status`, 从 checkout 跑, 实时落库, 模块 (+4 more)

### Community 100 - "test_wire.py"
Cohesion: 0.17
Nodes (19): event_from_json(), event_from_line(), Event, JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。 事件通道随形态而异：子进程态 =…, worker 事件通道一行（子进程态 = EVENTS_FD 的 fd；Fargate 态 = DDB events 表 body）→ model.Event。, wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。, 80 是跨语言约定值（两个引擎 worker 各自硬编码）——改这个数即改协议，须同步两 worker。, test_event_from_line() (+11 more)

### Community 101 - "wire.py"
Cohesion: 0.15
Nodes (16): _argument_to_json(), _cost_from_json(), job_to_json(), job_to_line(), ReportRef, StepArgument, wire 协议（ADR 0024）：core↔worker 的 JSON 序列化层 + 退出码约定。 core 把 Job 序列化成 JSON 喂…, Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。 (+8 more)

### Community 102 - "_stopped_detail"
Cohesion: 0.12
Nodes (16): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, container 缺 exitCode = 容器没跑起来（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…, 同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…, 连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, _stopped_detail() (+8 more)

### Community 103 - "Execution & Progression Model Guide"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的一生, 4. 后台跑批 `submit` 的一生, 4a. local 档：per-run 推进进程, 4b. cloud 档：三 Lambda 链, 4c. 读侧：进度怎么看、结果落在哪, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 104 - "Worker Package Dev Notes"
Cohesion: 0.17
Nodes (12): 从本 checkout 跑, 使用方 `steps/` 的加载（实现要点）, 依赖分类（踩过的坑）, 包身份, 容器镜像（维护者向）, 布局, 开发笔记（contributor）, 执行形态：薄 worker（cucumber 已退役） (+4 more)

### Community 105 - "_explain_run"
Cohesion: 0.11
Nodes (27): _evidence_fixture(), _explain(), _explain_run(), 在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真…, 文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、 短路旁注只在…, --json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing； 有记录但没挂…, --scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三档，可重复且彼此为或。, --step 单给退 2（步号没有归属）；命中的 scenario 都没有第 N 步 → 退 2 并列出候选 id 与步数； 正常时只渲染每条命中… (+19 more)

### Community 106 - "0042. step 级机读证据（evidence）与 `gherkai explain`"
Cohesion: 0.14
Nodes (14): 0042. step 级机读证据（evidence）与 `gherkai explain`, 一、evidence：worker 在 step 边界产一份 gherkai 自有 schema 的机读证据，挂 step 级 ReportRef（kind=`evidence`）, 三、`StepResult` 补 `message`，进 `jobs/*.json`, 不做 / 延后, 二、evidence 是 best-effort，对判定零影响——这是对既有规则开的一个具名例外, 五、与 [0027](./0027-runreport-aggregation-index.md) 的关系：铁律不破，一条消费端规则按层收窄，一个留口子用对的方式填上, 六、SDK 格式漂移的防线, 决策 (+6 more)

### Community 107 - "test_user_facing_messages.py"
Cohesion: 0.24
Nodes (11): AST, 代码纪律（绿≠对 / 接口诚实）, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, _scan_midscene() (+3 more)

### Community 108 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 109 - "ArtifactUploader"
Cohesion: 0.11
Nodes (10): ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0032, ADR-0033, ADR-0042, ArtifactUploader (+2 more)

### Community 110 - "开发笔记（contributor）"
Cohesion: 0.18
Nodes (11): 容器镜像（维护者向）, 开发笔记（contributor）, 执行形态：薄 worker（pytest-bdd 已退役）, 报告落点, 环境, 相关 ADR, 确定性 step：内建脚手架 vs 使用方的 `steps/`, 跑 spike（可独立跑，不进 wheel） (+3 more)

### Community 111 - "_cmd_status"
Cohesion: 0.25
Nodes (8): _cmd_reconcile(), _cmd_status(), [无状态跑批] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run…, cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…, per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR…, `--max-concurrency` 入口校验（对齐 `--tunnel-ttl`/`--grace`/`--assertion-votes`…, _status_cloud(), _validate_max_concurrency()

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
Cohesion: 0.09
Nodes (26): classify_vpc_state(), _error_code(), _make_cfn_client(), _make_ssm_client(), Exception, `gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`…, 三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…, `--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6； 三档与… (+18 more)

### Community 117 - "test_sqlite_event_log.py"
Cohesion: 0.20
Nodes (14): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exit_code=None（退出码未知，仅超时处置直写时出现）可存、读回仍是 None——投影侧判 ERROR、不是宽限态（ADR 0034…, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, reason（平台侧归因串，port 对称 DDB）随退出记录落库、records() 读回；不传则 None。, test_append_and_read_back_events() (+6 more)

### Community 118 - "_StubEcs"
Cohesion: 0.11
Nodes (12): _pending_cleanup(), family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, 已退休（带 retired-at）与孤儿（带血缘 tags、不在任何版本的映射里）——清理 pass 的候选，列出来才可解释 「为什么 family 里…, RevisionInfo, datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。 (+4 more)

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
Cohesion: 0.16
Nodes (21): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。…, render_run_state(), render_text(), RunResult, render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。, skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没跑」只在 message，人读文本必须显； 且…, step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。 (+13 more)

### Community 123 - "test_artifact_upload.py"
Cohesion: 0.11
Nodes (29): ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-…, key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。, 队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。, 造 uploader + 塞 mock s3 client（记录 upload_file 调用）。 `fail_keys`：该 key…, 永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。, drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。, 线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。, upload_file 必带 TransferConfig(use_threads=False)（ADR 0042 决策一）：否则传输落在… (+21 more)

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

### Community 129 - "ArtifactUploader"
Cohesion: 0.11
Nodes (13): ArtifactUploader, 是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。, 把文件交给后台队列顺序上传（**不阻塞调用方**）；no-op 档直接返回。 调用点在 `step_done` **emit 之后**（ADR 0042…, 有界等队列传完（含在途那一项）：全部处理完 True，超时 False（剩下的交给 flush 兜）。 收尾（scope 末 /…, 队列线程主体：FIFO 逐个传，**绝不因单项失败而死**（死了 = 后面的截图全不传且无人察觉）。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。, 本机 no-op 档：截图就在本地，队列/排空都是直接返回（不起线程、不碰 boto3）。 (+5 more)

### Community 130 - "evidence.test.mts"
Cohesion: 0.14
Nodes (12): build(), dumpAgent(), exec(), fileRef(), FIXTURE, fixtureAgent, ADR-0042, spyUploader() (+4 more)

### Community 131 - "开发者指南（contributor 入口）"
Cohesion: 0.25
Nodes (8): Spike（可独立跑的技术验证脚本）, 发布与版本, 开发环境（从 checkout 跑）, 开发者指南（contributor 入口）, 文档去哪读, 测试, 现状与版本线, 目录结构

### Community 132 - "event-sink.mts"
Cohesion: 0.22
Nodes (6): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0032, resolveEventsFd()

### Community 133 - "S3StepArgumentOffloader"
Cohesion: 0.24
Nodes (6): 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, 把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。, 就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…, 就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…, S3StepArgumentOffloader

### Community 135 - "agentcore-sigv4.mts"
Cohesion: 0.16
Nodes (13): BASE_URL, main(), makePng(), REGION, BASE_URL, main(), getBaseUrl(), getRegion() (+5 more)

### Community 136 - "Runtime Package README"
Cohesion: 0.29
Nodes (6): gherkai-runtime, 主要入口, 安装, 最小用法：在本机跑完一批, 注意, 相关

### Community 137 - "argument.mts"
Cohesion: 0.21
Nodes (6): ADR-0024, argumentText(), buildInstruction(), cleanCell(), StepArgument, unquote()

### Community 138 - "ADR 0018 Common Steps"
Cohesion: 0.33
Nodes (6): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）

### Community 139 - "_UnavailableEngine"
Cohesion: 0.25
Nodes (5): ConflictException, exceptions, Exception, 某引擎这次装配不出来时的「一用即抛」空腿——两档共用（local: ADR 0037 决策 3；cloud: ADR 0038）。 存在的理由：两个…, _UnavailableEngine

### Community 140 - "deterministic.py"
Cohesion: 0.16
Nodes (13): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+5 more)

### Community 142 - "Echo Test Worker"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 144 - "test_evidence.py"
Cohesion: 0.11
Nodes (38): _done(), _Nova, _picks(), list, Path, step 级机读证据（evidence，ADR 0042 决策一/二/六）单测：映射 / 截图上界 / 目录键 / best-effort 钩子。 纯…, n 帧的合成 trajectory：thought_at 里的帧带 think call，每帧都有可解的 data URL 图。, fake nova：act/act_get 回带 trajectory 路径的结果；act_raises 时抛（模拟 act 中途失败）。 (+30 more)

### Community 145 - "TypeScript Dev Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 146 - "test_fargate_engine.py"
Cohesion: 0.15
Nodes (20): _await_engine(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, _final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…, 终读是强一致读，其中的断号无从补、只记警告（不等、不停）。, MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。, 跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。, _spy_run_task_env(), _stopped_resp() (+12 more)

### Community 147 - "_presend_act_siblings"
Cohesion: 0.16
Nodes (14): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, _presend_act_siblings(), act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…, 进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，回归哨兵）。 被…, _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。 (+6 more)

### Community 148 - "Path"
Cohesion: 0.19
Nodes (9): _extra_args(), Path, 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 run_dir 的 POSIX 路径）。, reportRef 指向的文件 → 实时上传（不删、记 _uploaded）、报 s3://；no-op 时报 file://。 失败原样抛（worker 记…, **只算 ref、不上传**：返回该文件将来（scope 末 flush 后）会有的那个 ref，与 `to_report_ref` 逐字一致。 给…, 传一个文件、失败**重试一次**；成功 True（并记进已传集合）、两次都失败 False（不抛）。 队列与 flush 共用（key 规则与…, boto3 传输配置：`use_threads=False` → 传输在调用线程内跑（NonThreadedExecutor）。 默认的线程池是非…, scope 末：整目录递归上传剩余文件（跳过已传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→… (+1 more)

### Community 149 - "build_fargate_engines"
Cohesion: 0.12
Nodes (18): build_cloud_stores(), build_fargate_engines(), cloud_artifact_locations(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), cloud 档一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…, S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。 (+10 more)

### Community 150 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 151 - "Worker Subnet Single Source"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 152 - "arg_offload.py"
Cohesion: 0.29
Nodes (6): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…, has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…

### Community 153 - "NPM Package Files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 154 - "Repository Metadata"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 155 - "_patch_skew"
Cohesion: 0.25
Nodes (8): _patch_skew(), cloud status 到终态打出与 `run --backend cloud` 同款的位置行（s3:// 报告与判定明细、ddb:// 元信息）， 落点按…, status --json 附加 artifacts（ADR 0041 决策三）：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。, --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_cloud_json_includes_artifact_locations(), test_status_cloud_terminal_prints_s3_and_ddb_locations(), test_status_wait_cloud_kicker_missing_fails_fast()

### Community 156 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 157 - "parse_feature"
Cohesion: 0.18
Nodes (14): _index_ast_lines(), _map_argument(), parse_feature(), ParsedScenario, StepArgument, parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:… (+6 more)

### Community 158 - "aws"
Cohesion: 0.67
Nodes (3): aws(), _aws_env(), fixture

### Community 159 - "scope.py"
Cohesion: 0.26
Nodes (12): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…, 从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where = 出错时的定位（scenario id，即…, 解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…, 解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。, 解析一个 scope 的 job 墙钟预算：与 _resolve_engine 同构（ADR 0019 @timeout）。 缺省用 default；任一标了…, _resolve_engine() (+4 more)

### Community 160 - "NPM Scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 162 - "job-source.mts"
Cohesion: 0.20
Nodes (5): Job, JobSource, ADR-0016, ADR-0024, ADR-0032

### Community 165 - "build_local_reconcile"
Cohesion: 0.16
Nodes (16): LocalRunStore, build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, _job(), region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。 (+8 more)

### Community 167 - "compose.py"
Cohesion: 0.06
Nodes (53): subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…, sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, SECURITY_GROUPS_KEY)…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), is_botocore_error(), is_pure_release() (+45 more)

### Community 169 - "test_detached_launcher.py"
Cohesion: 0.21
Nodes (17): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _echo_resolver(), _now(), SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。 **真 spawn echo_worker…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…, 按 WORKER_MODE 起 echo_worker 的 SubprocessEngine，包成 resolver（所有 engine 名都映射到它）。 (+9 more)

### Community 170 - "_stream_record"
Cohesion: 0.13
Nodes (15): 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events…, _stream_record(), test_reconciler_noop_for_non_detached_run() (+7 more)

### Community 171 - "._installed_import_source"
Cohesion: 0.33
Nodes (4): 把 Lambda 代码摊到一个目录，返回其路径（`Code.from_asset` 用）。 内容 = 本包 `lambdas/` 的 handler…, 当前 venv 里某个 import 名的源路径（`find_spec`）——Lambda asset 的复制源，见…, 漏一项 → fail-fast 点名它。静默漏了的后果是 Lambda 运行期 ImportError，要到真起 run 才暴露。, test_missing_dependency_fails_loud_naming_it()

### Community 172 - "build_fargate_engines（组合根接线）"
Cohesion: 0.67
Nodes (3): build_fargate_engines（组合根接线）, container 名契约 {engine}-worker, 两个 worker 镜像（Nova / Midscene 各一）

### Community 173 - "artifact-upload.test.mts"
Cohesion: 0.38
Nodes (5): mkLogDir(), mkShots(), ADR-0029, ADR-0042, tmproot()

### Community 180 - "_seed_run"
Cohesion: 0.10
Nodes (21): 建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…, definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。, definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。, meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。, cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…, 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。 (+13 more)

### Community 182 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 186 - "exit_observer.py"
Cohesion: 0.23
Nodes (11): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+3 more)

### Community 187 - "plan"
Cohesion: 0.26
Nodes (13): FeatureSource, plan(), PlanConfig, Job, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…, plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。, 整组被筛掉的 scope 里的 tag 冲突不拦本次迭代（空组在解析 engine/timeout 之前跳过）； 但「一个 scenario 多个…, test_assertion_votes_from_config_propagates_to_all_jobs() (+5 more)

### Community 188 - "ReportStore"
Cohesion: 0.25
Nodes (5): ResourceUri, RunResult, 归集报告产物为一份**派生只读导航视图**（RunReport，ADR 0027）：manifest.json + index.html。 纯派生：可从…, 从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回…, ReportStore

### Community 191 - "WorkerHandle"
Cohesion: 0.25
Nodes (5): Event, 一个在跑的 worker 的句柄（schedule 持有，用于 stop）。 不暴露进程/信号细节——「怎么停」的机制藏在 adapter 内部（ADR…, 请求优雅停止：adapter 内部翻成具体机制；worker 收到后停会话、退出（ADR 0024 终止契约）。, 起一个 worker 跑这个 job，返回 (句柄, ADR 0024 事件流迭代器)。 事件流逐条产出（ADR 0024 流式）；迭代结束 = worker…, WorkerHandle

### Community 202 - "_explain_emit"
Cohesion: 0.14
Nodes (16): _cmd_explain(), _explain_cloud(), _explain_emit(), _explain_empty(), _explain_read_evidence(), _explain_scenario_matches(), explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…, 读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。… (+8 more)

### Community 204 - "_fake_locator"
Cohesion: 0.13
Nodes (22): _fake_locator(), _no_provider(), 把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。, local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；…, 装了 deploy-aws extra → 经 provider 接缝调它的 doctor(args)，required 项失败让整体退 2。, 凭证探针抛 → aws.identity 必修失败、backend 标未查（可选）、退 2；不去碰后端。, region 解析不出 → aws.region 必修失败、后端标未查，不会把 NoRegionError 误诊成「prefix 配错」。, --profile 打错在 resolve_cloud_target 就炸（读 profile config）→ 与探针失败同一句诊断、退 2，不冒… (+14 more)

### Community 207 - "test_s3_report_store.py"
Cohesion: 0.33
Nodes (9): S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index(), test_index_html_links_and_summary(), test_manifest_shape(), test_s3_href_not_relativized_kept_as_ref() (+1 more)

### Community 208 - "test_compose.py"
Cohesion: 0.04
Nodes (72): engine_min_grace(), _find_worker_spec(), prune_empty_dirs(), query_deterministic(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…, 一个引擎 worker 的拉起方式 = 定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。 (+64 more)

### Community 214 - "test_cli_json_contract.py"
Cohesion: 0.20
Nodes (17): _assert_documented(), _documented_keys(), _leaf_keys(), _mk(), `--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/guides/cli-…, 手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…, explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。, 递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque =… (+9 more)

### Community 216 - "03-midscene-grounding.ts"
Cohesion: 0.33
Nodes (5): ADR-0010, BASE_URL, main(), MODEL_CONFIG, REGION

### Community 217 - "_RecUploader"
Cohesion: 0.09
Nodes (15): _FakeCdp, _FakeNovaAct, _install_provider(), main_fakes(), 记录 drain / flush 调用的假上传器（顺序与超时参数都是契约）。, 把 main() 的 SDK 面全 fake 掉（job 走 stdin、scenarios 空 → 只跑到收尾序列）。, 正常完成：先有界排空队列（30s）、再整目录 flush（flush 只兜漏网的）。顺序反了就等于没有队列。, 协作停：三层 with 已退出（会话已释放）之后才排空，用退出档预算；不 flush（中断产物留本地）。 会话释放的两个 __exit__ 也进同一条… (+7 more)

### Community 220 - "FargateWorkerHandle"
Cohesion: 0.22
Nodes (5): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs

### Community 221 - "05-negative-assertions.ts"
Cohesion: 0.33
Nodes (5): BASE_URL, Check, main(), MODEL_CONFIG, REGION

### Community 222 - "gherkai CLI 的 `--json` 字段契约"
Cohesion: 0.20
Nodes (10): `evidence` 的固定键, gherkai CLI 的 `--json` 字段契约, `gherkai deploy list-workers --json`, `gherkai doctor --json`, `gherkai explain <run_id> [<scope_id>] --json`, `gherkai list-deterministic --engine <名> --json`, `gherkai list-engines --json`, `gherkai plan … --json` (+2 more)

### Community 226 - "决策"
Cohesion: 0.20
Nodes (10): 0041. 面向 AI agent 驾驭的 CLI 能力：scenario 筛选、静默落盘、JSON 覆盖补齐、doctor 自检、JSON 契约, 一、scenario 筛选：`--scope` / `--tags` / `--scenario`，run / plan / submit 三命令同形, 三、JSON 覆盖补齐：查询类命令都有机读形态, 二、`--quiet` 把 worker 日志落盘, 五、JSON 字段契约文档 + 护栏, 决策, 四、`doctor`：一个入口、按组件分组, 影响 (+2 more)

### Community 228 - "e2e_harness.py"
Cohesion: 0.33
Nodes (8): build_job(), Path, 复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…, worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…, run(), snapshot_disk(), snapshot_s3(), worker_cmd()

### Community 230 - "gherkai_cli/__main__.py"
Cohesion: 0.11
Nodes (27): ArgumentParser, _add_selection_flags(), _build_parser(), _cmd_doctor(), _cmd_list_engines(), _cmd_tunnel_watch(), _dist_version(), _doctor_cloud() (+19 more)

### Community 233 - "ImageInfo"
Cohesion: 0.29
Nodes (5): ImageInfo, `inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…, `linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。, 是否 linux/amd64（ADR 0038 固定架构）。, test_target_platform_judgement()

### Community 235 - "digest_for_repo"
Cohesion: 0.40
Nodes (5): digest_for_repo(), 从 `RepoDigests` 里挑出**本仓库**那条的 digest（`sha256:<hex>`）；没有 → None。…, 基底同步先 pull 过 GHCR → `RepoDigests` 多条；**取第一条就会把 GHCR 的 digest 写进 task-def** （ECR…, test_digest_none_when_repo_absent_or_empty(), test_digest_picked_by_repo_not_first_entry()

### Community 242 - "scenario_key"
Cohesion: 0.25
Nodes (8): `<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…, scenario_key(), 转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了 = evidence 静默互相覆盖。, 同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。, test_scenario_key_does_not_use_display_name(), test_scenario_key_is_deterministic_and_escapes_separators(), test_scenario_key_no_collision_after_escaping(), test_scenario_key_survives_non_ascii_and_empty_ids()

### Community 246 - "ResultStore"
Cohesion: 0.32
Nodes (3): JobResult, 数据面：每 job(=scope) 判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。 local adapter =…, ResultStore

### Community 252 - "raise_for_worker_exit"
Cohesion: 0.25
Nodes (8): raise_for_worker_exit(), worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, test_raise_for_worker_exit_maps_codes_with_fargate_label(), 码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 /…, 两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。, test_raise_for_worker_exit_label_names_the_transport_field(), test_raise_for_worker_exit_maps_codes()

### Community 263 - "novaact/DEVELOPMENT.md"
Cohesion: 0.12
Nodes (28): Lambda handler 入口（lambdas/）, ADR 0001 框架范围限定为英文 UI, ADR 0002 不用 gpt-5.5, ADR 0003 Qwen3-VL 定位, ADR 0004 Nova Act IAM 鉴权, ADR 0005 用例描述层用单一共享 .feature, ADR 0009 最大化使用 AWS 是硬前提, ADR 0010 spike 作对标基准 (+20 more)

### Community 264 - "_FakeSchedulerClient"
Cohesion: 0.29
Nodes (5): _FakeSchedulerClient, create_schedule 记录器（含 exceptions.ConflictException 形状，兼容 boto3 client 异常访问路径）。, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, test_timeout_watch_conflict_is_idempotent(), test_timeout_watch_creates_one_time_schedule()

### Community 265 - "start_tunnel_for_jobs"
Cohesion: 0.29
Nodes (7): 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers(), test_start_tunnel_for_jobs_propagates_tunnel_error()

### Community 266 - "_delayed_stopped_ecs"
Cohesion: 0.50
Nodes (4): _delayed_stopped_ecs(), 最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…, 假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…, test_read_events_gap_within_grace_waits_and_fills_in_order()

### Community 271 - "S3ReportStore"
Cohesion: 0.22
Nodes (7): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, 配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。, s3_report_store(), test_prefix_lands_under_prefix()

### Community 277 - "CloudTarget"
Cohesion: 0.50
Nodes (3): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态跑批事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序＝链上顺序。

### Community 283 - "test_run_state_timestamps_share_one_format"
Cohesion: 0.17
Nodes (12): datetime, now_iso(), parse_iso(), **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, detached run 的 run 级墙钟（毫秒）= RunState `ended_at` − `started_at`（提交落库到 finalize…, run_duration_ms(), 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的… (+4 more)

### Community 284 - "detached.py"
Cohesion: 0.18
Nodes (11): cleanup_tunnel(), drive_local_reconcile(), _paths(), 无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…, local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。, local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。 (+3 more)

### Community 285 - "_isolate"
Cohesion: 0.67
Nodes (3): _isolate(), fixture, 注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。

### Community 286 - "SubprocessLauncher"
Cohesion: 0.22
Nodes (7): 唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…, test_opening_a_v140_shaped_db_adds_the_reason_column(), local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, SubprocessLauncher, SqliteEventLog, SubprocessEngine

### Community 287 - "cloud_env"
Cohesion: 0.67
Nodes (3): cloud_env(), moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。, fixture

### Community 288 - "list_workers"
Cohesion: 0.09
Nodes (25): _cell(), cleanup_pass(), CleanupOutcome, _hours(), _iter_image_params(), list_workers(), _mapped_arn(), _non_terminal_statuses() (+17 more)

### Community 292 - "runtime 包 —— contributor 文档"
Cohesion: 0.50
Nodes (4): runtime 包 —— contributor 文档, 从 checkout 跑 / 测试, 模块, 相关 ADR

### Community 306 - "artifact_upload.py"
Cohesion: 0.50
Nodes (3): _log(), 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, 诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…

### Community 308 - "_Calls"
Cohesion: 0.50
Nodes (3): _Calls, list, upload_file 调用记录：list 元素 = (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。

### Community 323 - "云端后端由哪些载体拼成：一次改动要传播到哪几处才生效"
Cohesion: 0.25
Nodes (8): 1. 五个载体, 2. 行为住在哪个载体上（动手前先定位）, 3. 一次版本升级的传播顺序，以及为什么不能倒过来, 4. 症状 → 该推哪个载体, 5. `submit` 在提交那一刻钉死了什么, 6. 一个 prefix = 一套环境；多版本并存靠多 prefix, 7. 延伸阅读, 云端后端由哪些载体拼成：一次改动要传播到哪几处才生效

### Community 324 - "core 包 —— contributor 文档"
Cohesion: 0.50
Nodes (4): core 包 —— contributor 文档, 实际执行（跑 .feature）, 模块, 跑测试

### Community 330 - "_argv"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证， 不会跑…, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 331 - "一条确定性 step 的一生：从你写下正则到它在云端命中"
Cohesion: 0.25
Nodes (8): 0. 全景：四段路，一张表, 1. 派发决策链：一条 step 文本进 worker 之后, 2. 三个入口，一张表：为什么清单、标注、真跑不可能分叉, 3. 两个真值源、一个岔口：为什么「改了 steps，云端没变」是设计, 4. 响亮地失败：症状 → 原因 → 怎么办, 5. 两条腿必须对称，与一个诚实的缺口, 6. 延伸阅读, 一条确定性 step 的一生：从你写下正则到它在云端命中

### Community 332 - "test_explain_cloud_reads_evidence_from_s3"
Cohesion: 0.50
Nodes (4): _explain_cloud_stores(), 假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。, cloud 档：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。, test_explain_cloud_reads_evidence_from_s3()

### Community 333 - "._read_s3"
Cohesion: 0.25
Nodes (5): 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, test_value_error_not_transient(), ValueError

### Community 335 - "产物与证据地理：跑完了东西在哪、哪一份答哪个问题（local × cloud）"
Cohesion: 0.29
Nodes (7): 1. 五类东西，各答一个问题, 2. 物理地理：local 与 cloud 是同一棵树的两种载体, 3. 证据链怎么串起来, 4. 一次失败，按三步读, 5. 诚实的边界（都是有意接受的取舍，不是遗漏）, 6. 延伸阅读, 产物与证据地理：跑完了东西在哪、哪一份答哪个问题（local × cloud）

### Community 338 - "ADR 0024 worker↔core 协议"
Cohesion: 0.31
Nodes (14): CLAUDE.md 项目约定, 工作方式（tools/ 复用、AWS 开发期免费）, gherkai CLI 使用者页面, ADR 0017: 云端执行选 Fargate, ADR 0024 worker↔core 协议, ADR 0027 报告聚合, ADR 0028 瞬时网络/SSL 韧性, ADR 0029 产物上传 S3 (+6 more)

### Community 340 - "BoomLauncher"
Cohesion: 0.33
Nodes (4): BoomLauncher, launch 必抛的 fake（RunTask 放置失败/task-def 配错/Popen OSError 的抽象）。, launch 抛异常 → 补偿记非0退出 → 下轮判 ERROR 收敛，run 不 wedge（ADR 0034 机制二推论）。, test_launch_failure_does_not_wedge_run()

### Community 342 - "parametrize"
Cohesion: 0.50
Nodes (4): test_shipped_readme_is_for_users_only(), 裸 `@scope:` / `@engine:` / `@timeout:`（空值）→ PlanError（ADR 0025：标了 tag…, test_bare_tag_without_value_errors_with_location(), parametrize

## Knowledge Gaps
- **457 isolated node(s):** `背景`, `一、evidence：worker 在 step 边界产一份 gherkai 自有 schema 的机读证据，挂 step 级 ReportRef（kind=`evidence`）`, `二、evidence 是 best-effort，对判定零影响——这是对既有规则开的一个具名例外`, `三、`StepResult` 补 `message`，进 `jobs/*.json``, `四、`gherkai explain <run_id> [<scope_id>]`：把 evidence 与判定树合成一份「哪步、问什么、看见什么、为什么」的文本或 JSON` (+452 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **128 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `test_exception_path_drains_and_still_raises()` connect `_RecUploader` to `test_evidence.py`, `run_scope.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `NonTerminalSnapshot` connect `test_project.py` to `model.py`, `test_stores.py`, `test_evidence.py`, `test_schedule.py`, `StepResult`, `RunPersistence`, `LocalReportStore`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `main()` connect `run_scope.py` to `Nova Engine Probes`, `_RecUploader`, `test_interrupt_model.py`, `_is_transient_network`, `test_user_steps.py`, `deterministic.py`, `test_deterministic.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Provider` (e.g. with `_AbsentEngine` and `_CdkWritingContext`) actually correct?**
  _`Provider` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `schedule()` (e.g. with `.on_job_complete()` and `test_adapter_crash_is_error()`) actually correct?**
  _`schedule()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `CollectSink` (e.g. with `WorkerNetworkError` and `Job`) actually correct?**
  _`CollectSink` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `FakeEngine` (e.g. with `WorkerNetworkError` and `Job`) actually correct?**
  _`FakeEngine` has 7 INFERRED edges - model-reasoned connections that need verification._