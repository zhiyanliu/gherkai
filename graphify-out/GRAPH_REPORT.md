# Graph Report - yaozhou  (2026-09-08)

## Corpus Check
- 214 files · ~193,896 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3803 nodes · 8422 edges · 235 communities (170 shown, 65 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 488 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c306afc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CloudLauncher
- wire.py
- test_run_step.py
- test_worker_variant.py
- test_plan.py
- BackendStack
- test_cloud_reconcile.py
- schedule
- gherkai_worker_novaact/__init__.py
- test_stack.py
- test_user_steps.py
- test_workers.py
- _is_transient_network
- test_schedule.py
- dependencies
- Provider
- fargate_engine.py
- test_conditional_writes.py
- main
- test_artifact_upload.py
- test_reconcile.py
- 03-midscene-grounding.ts
- RunResult
- test_backend_cloud.py
- kicker Lambda（冷启动起首批 job）
- test_fargate_engine.py
- test_compose.py
- run_store/ddb.py
- RunState
- test_sqlite_event_log.py
- model.py
- build_engines
- 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel
- FargateEngine
- test_deploy_cmd.py
- ADR 0034 — Detached Batch Reconciler
- subprocess_engine.py
- main
- compose.py
- run_scope.py
- _FakeEcsClient
- workers.py
- 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器
- schedule.py
- query_deterministic
- ADR 0028: Transient Network/SSL Resilience
- 执行与推进模型导览：run / submit × local / cloud
- compilerOptions
- deterministic.steps.mts
- test_deterministic.py
- events_wallclock.py
- test_tunnel_host.py
- ADR 0022 BDD runner 退役 + 薄 worker
- deterministic.mts
- ._run_cdk
- test_project.py
- _StubEcs
- test_tunnel_cli.py
- e2e_harness 使用说明
- ._resolve_target
- Job
- test_event_sink.py
- test_user_facing_messages.py
- gherkai_runtime/names.py
- 0038. worker 镜像交付：基底、variant 与推送注册
- _SeqEcs
- test_job_source.py
- test_lambda_handlers.py
- 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询
- test_argument.py
- S3StepArgumentOffloader
- event-sink.mts
- ADR 0027: RunReport 跨引擎归集索引
- render.py
- reconciler.py
- test_cloud_integration.py
- ecs_task_timing.py
- RunPersistence 应用服务
- run-scope.test.mts
- _FakeEcs
- _FakeTable
- ADR 0003 Qwen3-VL on Bedrock 做 grounding
- schedule._Worker._run_once
- _stopped_detail
- _progress
- cloud_env
- test_detached_launcher.py
- test_timeout_watch_conflict_is_idempotent
- ensure_workflow_definition
- _FakeEcs
- ADR 0017: Cloud Execution — Fargate over Runtime
- _FakeS3
- test_tick_runs_isolates_a_run_whose_worker_revision_cannot_be_resolved
- echo_worker.py
- test_cloud_infra.py
- ArtifactUploader
- SqliteEventLog
- 权威信息源 REFERENCES
- Midscene SigV4 自签 fetch 配方
- deploy.py
- gherkai
- ADR 0018: 通用 step 能力清单
- 02-agentcore-cdp.ts
- _StampSsm
- EventBridgeTimeoutWatch
- cli/__main__.py（argparse 皮 + 退出码）
- test_report_store.py
- test_tunnel.py
- build_fargate_engines
- _render_status
- package.json
- _referenced_by_live_run
- gherkai-runtime
- Status
- aws
- 开放性动作导致页面瞬态 flaky
- session_id lineage on scope_started
- ADR 0030 实时落库接缝
- CI 与发布链（`.github/`）
- events_table
- _Recorder
- exit_observer.py
- gherkai-deploy-aws
- agentcore-sigv4.mts
- wikipedia SSL 环境坑
- _spawn_and_wait_ready
- _FakeResult
- map_origin_in_jobs
- gherkai_cli/__main__.py
- _ClientError
- main
- gherkai_runtime/__init__.py
- tunnel.py
- gherkai-core
- 分发与打包施工进度总纲（ADR 0037 / 0038 落地）
- _cmd_status
- stop_tunnel
- test_worker_subnets_single_source_across_ssm_and_lambda_env
- test_subprocess_engine.py
- _seed_worker_ssm
- adapters/__init__.py
- test_interrupt_model.py
- _NetRaiseEngine
- gherkai_core/__init__.py
- test_lifecycle_states.py
- README.md
- .add_arguments
- test_final_drain_paginates_across_last_evaluated_key
- _FakeSink
- JobSource
- user-steps.mts
- cli.py
- 成本可观测（engine 只报原生量、core 不折美元）
- _CdkWritingContext
- Ports 层（Engine/RunStore/ResultStore/ReportStore）
- 报告产物模型 / RunReport 归集索引
- .delete_worker
- _stream_record
- _argv
- 05-negative-assertions.ts
- argument.mts
- user-steps.test.mts
- WorkerNetworkError
- _submit_local
- _ssm_params
- deterministic.py
- test_container.py
- resolve_network
- _patch_skew
- user_steps.py
- wait_for_index.sh
- _FakeSink
- 01-model-sigv4.ts
- events_pk
- stack.py
- _spy_run_meta
- build_local_reconcile
- detached.py
- deterministic_steps.py
- 04-planning-probe.ts
- CloudTarget
- _UnavailableEngine
- bin.mts
- devDependencies
- _isolate
- @aws-sdk/client-bedrock-agentcore
- artifact-upload.test.mts
- test_handler_skips_when_no_run_id
- test_provider_module_does_not_import_aws_cdk
- openai
- files
- repository
- index.mts
- resolve-hook.mts
- event-sink.test.mts
- Event
- scripts
- agentcore-sigv4.test.mts
- job-source.test.mts
- fixture
- ADR-0019
- @aws-sdk/client-dynamodb
- SubprocessLauncher
- tsx
- argument.test.mts
- deterministic.test.mts
- test_run_state_timestamps_share_one_format
- test_lambda_asset.py
- gherkai-deploy-aws
- ADR-0026
- ADR-0027
- ADR-0032
- ADR-0035
- engines/novaact README
- AWS_TRANSIENT_NAMES
- AWS_TRANSIENT_STATUS
- CONNECT_BACKOFF_MS
- Job
- gherkai-worker-novaact
- ADR-0014
- ADR-0020
- ADR-0022
- ADR-0024
- ADR-0028
- ADR-0029
- ADR-0031
- ADR-0036
- ADR-0037
- Scenario
- ShutdownDeps
- Step
- RuntimeError
- _runs_stream_record
- ContainerError

## God Nodes (most connected - your core abstractions)
1. `main()` - 137 edges
2. `Job` - 109 edges
3. `RunState` - 96 edges
4. `RunMeta` - 95 edges
5. `Provider` - 80 edges
6. `JobState` - 79 edges
7. `Status` - 75 edges
8. `JobResult` - 65 edges
9. `schedule()` - 62 edges
10. `Scenario` - 62 edges

## Surprising Connections (you probably didn't know these)
- `通用 step（QA 零代码的唯一载体）` --conceptually_related_to--> `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md → docs/adr/0019-feature-tags-scope-and-engine.md
- `_cmd_submit()` --calls--> `stop_tunnel()`  [INFERRED]
  cli/gherkai_cli/__main__.py → runtime/gherkai_runtime/tunnel.py
- `_submit_local()` --calls--> `SqliteEventLog`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/event_log/sqlite.py
- `_render_status()` --calls--> `run_state_to_dict()`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/serialize.py
- `_status_cloud()` --calls--> `DynamoDBRunStore`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/adapters/run_store/ddb.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **真跑陷阱集合** — tools_e2e_harness_md_multi_scenario_pitfall, tools_e2e_harness_md_ssl_pitfall, tools_e2e_harness_md_boundary_preflush, tools_e2e_harness_md_interrupt_timings [EXTRACTED 0.80]
- **Retry domain safety: boundary, backoff signal penetration, session leak guard** — docs_adr_0028_transient_network_ssl_resilience_retry_domain_boundary, docs_adr_0028_transient_network_ssl_resilience_backoff, docs_adr_0028_transient_network_ssl_resilience_session_leak_guard, docs_adr_0028_transient_network_ssl_resilience_targetclosederror_stage_rule [EXTRACTED 0.80]
- **通用 step 原语在两引擎间的对称映射与边界** — docs_adr_0018_generic_steps_capability_abstract_primitives, docs_adr_0018_generic_steps_capability_engine_symmetry, docs_adr_0018_generic_steps_capability_negative_verification, docs_adr_0018_generic_steps_capability_phrasing_ambiguity_risk, docs_adr_0018_generic_steps_capability_deterministic_anchor [EXTRACTED 0.85]
- **报告判读流程（sample_valid → n_lost → 时序交叉核对）** — tools_e2e_harness_md_harness_report_json, tools_e2e_harness_md_sample_valid, tools_e2e_harness_md_lost_on_fargate, tools_e2e_harness_md_boundary_preflush [EXTRACTED 0.85]
- **step 派发：默认 AI / URL 分流 / 确定性锚点与角色边界** — docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_default_ai, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_url_autorouting, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_deterministic_scaffold, docs_adr_0020_step_phrasing_default_ai_deterministic_scaffold_role_boundary [EXTRACTED 0.85]
- **产物→S3 上传流（注入落点→实时/抢传→key 镜像→删本地→ReportRef 穿透）** — docs_adr_0029_injected_s3_target, docs_adr_0029_artifact_uploader, docs_adr_0029_act_boundary_presend, docs_adr_0029_s3_key_mirrors_run_tree, docs_adr_0029_delete_local_after_upload, docs_adr_0027_reportref [EXTRACTED 0.90]
- **network_error signal flow: worker whitelist → exit code 80 → typed error → schedule retry** — docs_adr_0028_transient_network_ssl_resilience_is_transient_network, docs_adr_0028_transient_network_ssl_resilience_ex_worker_network, docs_adr_0028_transient_network_ssl_resilience_subprocess_engine_read_events, docs_adr_0028_transient_network_ssl_resilience_workernetworkerror, docs_adr_0028_transient_network_ssl_resilience_schedule_worker_run_once, docs_adr_0028_transient_network_ssl_resilience_schedule_worker_run [EXTRACTED 0.90]
- **三 port 正交：RunStore 控制面 / ResultStore 数据面 / ReportStore 派生视图** — docs_adr_0030_run_store, docs_adr_0030_result_store, docs_adr_0027_reportstore, docs_adr_0030_commit_point [EXTRACTED 0.90]

## Communities (235 total, 65 thin omitted)

### Community 0 - "CloudLauncher"
Cohesion: 0.13
Nodes (18): CloudLauncher, Job, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, _job(), CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。, job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…, 无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。 (+10 more)

### Community 1 - "wire.py"
Cohesion: 0.09
Nodes (36): SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, _argument_to_json(), _cost_from_json(), event_from_json(), event_from_line(), job_to_json(), job_to_line(), Event (+28 more)

### Community 2 - "test_run_step.py"
Cohesion: 0.13
Nodes (31): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_step(), _done(), _FakeNova, _run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。 与 Midscene 引擎 run-scope.test.ts…, 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。 (+23 more)

### Community 3 - "test_worker_variant.py"
Cohesion: 0.07
Nodes (49): aws(), _fake_aws_creds(), _push_image(), fixture, worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…, 不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest/模板 ARN 供打印。, 显式 `--worker-variant` 走该 variant，与默认指针无关（默认指针只是缺省值）。, 一个 run 一个 variant 名、跨引擎同名（ADR 0038）——按本 run 用到的引擎逐个解析。 (+41 more)

### Community 4 - "test_plan.py"
Cohesion: 0.07
Nodes (56): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, FeatureSource, plan(), PlanConfig, Job, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine 校验 → Job[]。 对外入口…, core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 严格契约：`features` 的 uri 必须互异（uri… (+48 more)

### Community 5 - "BackendStack"
Cohesion: 0.10
Nodes (16): Cluster, Construct, BackendStack, 后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…, 建/取 VPC，**并把生效的档记进 `self._vpc_spec`**（写 SSM 供下次 deploy 三态比对，ADR 0037 决策 6）。…, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 把「这次部署是什么版本、落在哪个 VPC」写成 **stack 资源**（不是命令事后 `put_parameter`）。 **为何是 stack… (+8 more)

### Community 6 - "test_cloud_reconcile.py"
Cohesion: 0.20
Nodes (18): DdbEventLog, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, _meta(), _passed_worker_events(), _put_worker_event(), cloud 无状态跑批 core 侧测试（ADR 0034 P4a）：DdbEventLog + CloudLauncher +…, 多 scope：逐 scope Query 拼全量（不需 GSI）。, reconcile.tick 用 DdbEventLog + DynamoDBRunStore + CloudLauncher（fake… (+10 more)

### Community 7 - "schedule"
Cohesion: 0.19
Nodes (49): RunMeta, 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的…, schedule(), ScheduleOpts, CollectSink, FakeEngine, FakeResolver, 按 job.scope_id → 预设事件流（或行为）吐事件。 behaviors: scope_id -> 一个 callable(job) ->… (+41 more)

### Community 8 - "gherkai_worker_novaact/__init__.py"
Cohesion: 0.16
Nodes (14): gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…, _presend_act_siblings(), act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…, 进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，回归哨兵）。 被…, _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。 (+6 more)

### Community 9 - "test_stack.py"
Cohesion: 0.07
Nodes (47): make_template(), Template, BackendStack 合成断言测试（ADR 0033/0037 决策 6）：纯本地 synth、不碰 AWS。 用 CDK…, runs 表按 `status` 的 GSI（ADR 0038 清理安全阀）：**投影必须含 `worker_task_def_arns`**。 过滤表达式…, GSI 只加在 runs 表上（events 表按 pk/seq 读，加索引白花钱）——枚举型护栏，防将来顺手加错表。, ECR **不设任何 lifecycle 规则**（ADR 0038 护栏，被拒方案「ECR 加 untagged 过期 lifecycle」）。 重推同名…, 模板 revision ARN **不进任何 Lambda 的 env**（ADR 0038 被拒方案「缺字段时回落模板 revision」）。 曾短暂注入过…, 两个推进器（reconciler/kicker）都要能读 `/{prefix}backend/*`（ADR 0038「权限面增量·云端推进器」）： 没有… (+39 more)

### Community 10 - "test_user_steps.py"
Cohesion: 0.12
Nodes (28): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。, 真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。… (+20 more)

### Community 11 - "test_workers.py"
Cohesion: 0.07
Nodes (76): _cleanup(), FakeContainer, _mapping(), _out(), _push(), `push-worker` 八步 / `deploy` 三步 / 清理 pass / `list-workers` 测试（ADR 0038）。…, 容器引擎替身。**只有 push 过的 ref 才有 `repo_digests`**——照抄真 docker 的行为（见 container 模块头： 本地…, 收集打印文本的 out 替身 → (调用函数, 取全文函数)。 (+68 more)

### Community 12 - "_is_transient_network"
Cohesion: 0.12
Nodes (31): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+23 more)

### Community 13 - "test_schedule.py"
Cohesion: 0.14
Nodes (38): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), Cost, AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。 (+30 more)

### Community 14 - "dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 15 - "Provider"
Cohesion: 0.08
Nodes (58): Provider, AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。, _parse(), parametrize, `Provider` 测试（ADR 0037 决策 6）：flag 面、context 拼装、生成的 cdk.json、cdk 调用、VPC 档三态。…, flag 面全集钉死（枚举型护栏）：三个 context 旋钮 flag + AWS 定位二件套 + 两个「皮的中立版的 AWS 精确化」（见 cli…, 子动词全集钉死（枚举型护栏）+ **只挂 deploy**。 挂到 destroy 上不是「多个没用的命令」而是危险：皮的 destroy 分派不看…, 子动词 subparser **不可 required=True**：deploy 的默认动作是真部署，裸 `gherkai deploy` 必须照样过。 (+50 more)

### Community 16 - "fargate_engine.py"
Cohesion: 0.14
Nodes (10): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, 一次 DescribeTasks 探测的结果——**两个正交事实各自命名**（ADR 0024「exitCode 落值延迟」）： -…, TaskProbe, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如… (+2 more)

### Community 17 - "test_conditional_writes.py"
Cohesion: 0.09
Nodes (39): _initial(), _meta(), fixture, RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。 (+31 more)

### Community 18 - "main"
Cohesion: 0.05
Nodes (88): main(), _capturing_schedule(), _det_feature(), _fake_schedule_factory(), _fake_worker_cmd(), _miss(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS）， 验证落盘三层产物 + --json… (+80 more)

### Community 19 - "test_artifact_upload.py"
Cohesion: 0.08
Nodes (29): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→…, upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。 (+21 more)

### Community 20 - "test_reconcile.py"
Cohesion: 0.15
Nodes (24): 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), _done_events(), FakeLauncher, _meta(), Job, reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。 用真…, job 非0退出（机制二）→ 该 job error → run finalize 为 error。 (+16 more)

### Community 21 - "03-midscene-grounding.ts"
Cohesion: 0.29
Nodes (6): ADR-0010, BASE_URL, main(), MODEL_CONFIG, REGION, ADR-0033

### Community 22 - "RunResult"
Cohesion: 0.09
Nodes (32): ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。, 一次执行的机器可读汇总判定 = **definition（run_meta）+ 判定（jobs）的显式合成**（ADR 0016/0026）。…, RunResult, Event (+24 more)

### Community 23 - "test_backend_cloud.py"
Cohesion: 0.05
Nodes (93): _definition(), _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, local run 的 definition 不带这两个字段（omit-when-None，ADR 0038「local 档不写」）。, 后端默认指针本身是个非法 variant 名（部署侧写坏）→ 退 2 并点名那个 SSM 参数，不冒 traceback。 显式 `--worker-…, patch store 钩子 + preflight（默认放行）+ 版本 skew 闸 + worker variant 闸（都默认放行）返回记录调用的… (+85 more)

### Community 25 - "test_fargate_engine.py"
Cohesion: 0.11
Nodes (45): _delayed_stopped_ecs(), _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。 (+37 more)

### Community 26 - "test_compose.py"
Cohesion: 0.05
Nodes (62): check_version_skew(), engine_min_grace(), 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, 按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…, 比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict ∈ ok/warn/block/skip（ADR 0037 决策…, resolve_cloud_target() (+54 more)

### Community 27 - "run_store/ddb.py"
Cohesion: 0.12
Nodes (16): _job_state_from_item(), _job_state_to_item(), RunMeta, Status, DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。 (+8 more)

### Community 28 - "RunState"
Cohesion: 0.05
Nodes (73): `status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…, render_run_state(), test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), RunStore adapters（ADR 0016）。当前只有 local；未来 ddb。, LocalRunStore, Path, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR… (+65 more)

### Community 29 - "test_sqlite_event_log.py"
Cohesion: 0.23
Nodes (12): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, test_append_and_read_back_events(), test_append_idempotent_same_seq() (+4 more)

### Community 30 - "model.py"
Cohesion: 0.05
Nodes (62): render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。, _sample_run(), test_render_text_annotates_shortcircuited_step(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_no_annotation_on_plain_failed(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar(), CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate… (+54 more)

### Community 31 - "build_engines"
Cohesion: 0.08
Nodes (29): Engine, build_engines(), load_feature(), make_resolver(), 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…, 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 no_artifacts（`--no-…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, Path (+21 more)

### Community 32 - "0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel"
Cohesion: 0.08
Nodes (24): 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel, 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条, 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵, 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra, 2d. `requires-python >=3.13` 维持, 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）, 决策 1：交付物按打包技术划分，worker 运行时是硬核, 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first (+16 more)

### Community 33 - "FargateEngine"
Cohesion: 0.20
Nodes (10): FargateEngine, Event, Job, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR… (+2 more)

### Community 34 - "test_deploy_cmd.py"
Cohesion: 0.07
Nodes (44): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 __main__（argparse 皮）+…, _FakeEP, _patch_eps(), parametrize, `gherkai deploy` / `gherkai destroy` 的命令皮测试（ADR 0037 决策 6）：provider 发现三分叉 +…, provider 装了但加载炸（半装/版本不匹配）→ 退 2 + 点名 entry point，不让 traceback 裸奔。…, entry point 指向**类**（真 provider 就是 `…cli:Provider`）→ 皮实例化它；指向现成对象则原样用。, provider 的旋钮由它自己贴（皮不认识 `--vpc`），解析结果原样进 provider 拿到的 args。 (+36 more)

### Community 35 - "ADR 0034 — Detached Batch Reconciler"
Cohesion: 0.25
Nodes (19): CLAUDE.md 项目约定, cli README（最薄前端/组合根皮）, CONTEXT.md 领域术语表, 执行核心库窄腰（概念）, 通用 step（QA 零代码的唯一载体）, Run 数据模型 Run⊃Job(=Scope)⊃Scenario⊃Step, 连锁失败读法（error → 后续 step 短路跳过）, core README（执行核心库窄腰） (+11 more)

### Community 36 - "subprocess_engine.py"
Cohesion: 0.16
Nodes (11): _pump_log(), Event, Job, Popen, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。 (+3 more)

### Community 37 - "main"
Cohesion: 0.19
Nodes (9): cumulativeTokens(), isTransientNetwork(), log(), main(), runScenario(), runStep(), shutdownSequence(), stepCost() (+1 more)

### Community 38 - "compose.py"
Cohesion: 0.05
Nodes (60): subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "subnets") 的便捷形式）。, sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "security-groups")…, 后端版本戳的 SSM 路径（ADR 0037 决策 6「版本戳」/ 决策 7 skew 比对读侧）。, 引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…, ssm_security_groups_path(), ssm_subnets_path(), ssm_version_path(), ssm_worker_template_path() (+52 more)

### Community 39 - "run_scope.py"
Cohesion: 0.09
Nodes (28): ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_traj_refs(), _backoff_interrupted(), _collect_traj(), _cost_from_result(), _get_uploader(), log() (+20 more)

### Community 40 - "_FakeEcsClient"
Cohesion: 0.12
Nodes (22): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), _preflight_report_dir() (+14 more)

### Community 41 - "workers.py"
Cohesion: 0.05
Nodes (89): Aws, _cell(), cleanup_pass(), current_version_mappings(), _describe_revision(), _ecr_login(), _error_code(), _find_reusable() (+81 more)

### Community 42 - "0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器"
Cohesion: 0.20
Nodes (10): 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器, 1. `TunnelProvider` 可插拔口子（`gherkai-runtime` 组合根共享层），首个实现 = ngrok, 2. URL 映射：feature 写原始地址，组装 job 时替换, 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态, 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）, 决策, 背景与问题, 被拒/被缓方案（护栏） (+2 more)

### Community 43 - "schedule.py"
Cohesion: 0.12
Nodes (16): _Heartbeat, _heartbeat_wrap(), Job, Status, schedule 模块（ADR 0026）：Job[] → 并发跑 → 收流式事件 → RunResult。 job 间并行（maxConcurrency…, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。, 跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…, 单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run… (+8 more)

### Community 44 - "query_deterministic"
Cohesion: 0.07
Nodes (28): 读回 definition（从 META item 的 meta_json）；不存在返回 None。, _ask_worker(), build_local_stores(), match_deterministic(), prune_empty_dirs(), Path, query_deterministic(), 自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。… (+20 more)

### Community 45 - "ADR 0028: Transient Network/SSL Resilience"
Cohesion: 0.20
Nodes (11): ADR 0028: Transient Network/SSL Resilience, Hand-written exponential backoff with _stop.wait, botocore transient/throttled error code tables (inlined), _is_transient_network(e, *, connecting=False) (Python whitelist), isTransientNetwork (Node/Midscene whitelist), network_error ErrorType Classification, Retry Domain Boundary = before scope_started emit, Known debt: engine SSL classification asymmetry (+3 more)

### Community 46 - "执行与推进模型导览：run / submit × local / cloud"
Cohesion: 0.17
Nodes (12): 1. 心智模型：两种驱动、同一份 `core`, 2. 四组合一览, 3. 前台 `run` 的一生, 4. 后台跑批 `submit` 的一生, 4a. local 档：per-run 推进进程, 4b. cloud 档：三 Lambda 链, 4c. 读侧：进度怎么看、结果落在哪, 5. 同一条事件流的四条物理通道（横切对照） (+4 more)

### Community 47 - "compilerOptions"
Cohesion: 0.08
Nodes (23): compilerOptions, declaration, esModuleInterop, exactOptionalPropertyTypes, forceConsistentCasingInFileNames, lib, module, moduleResolution (+15 more)

### Community 48 - "deterministic.steps.mts"
Cohesion: 0.33
Nodes (5): ADR-0015, ADR-0020, ADR-0022, ADR-0036, ADR-0037

### Community 49 - "test_deterministic.py"
Cohesion: 0.14
Nodes (21): deterministic(), list_registry(), match(), 装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…, 注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。, 在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…, 确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑（从 repo 根）：uv run pytest -q…, --match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。 (+13 more)

### Community 50 - "events_wallclock.py"
Cohesion: 0.20
Nodes (15): _acts_from_scope(), analyze(), _emit_epoch(), main(), _percentile(), _print_human(), _query_by_pk(), 线性插值分位数（q∈[0,1]）。sorted_vals 非空、已升序。 (+7 more)

### Community 51 - "test_tunnel_host.py"
Cohesion: 0.15
Nodes (18): compute_watch_ttl_s(), 按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…, cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…, watch_run_and_stop_tunnel(), _patch_run_store(), tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…, 读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。, Σ(各 job 预算) + 启动余量——求和对任何并发取值都是保守上界（ADR 0034 机制四）。 (+10 more)

### Community 52 - "ADR 0022 BDD runner 退役 + 薄 worker"
Cohesion: 0.15
Nodes (15): ADR 0001 范围限英文 UI, ADR 0005 单一共享 .feature, ADR 0006 形态 A 两子工程并列, ADR 0007 程序化登录 / HITL 逃生舱, ADR 0010 双引擎苹果对苹果对标, ADR 0011 AgentCore 浏览器默认 vs 自建, ADR 0013 跨引擎共享边界, ADR 0014 AI 断言为主 + 投票治抖动 (+7 more)

### Community 53 - "deterministic.mts"
Cohesion: 0.11
Nodes (15): ADR-0020, ADR-0022, ADR-0036, DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta (+7 more)

### Community 54 - "._run_cdk"
Cohesion: 0.11
Nodes (14): cdk_command(), _make_sts_client(), Path, boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。, 销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…, 只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…, 导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…, `cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。… (+6 more)

### Community 55 - "test_project.py"
Cohesion: 0.06
Nodes (84): HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, ScopeStarted, StepStarted, Action, EventRecord, _job_status(), _lifecycle_rank(), plan_next() (+76 more)

### Community 56 - "_StubEcs"
Cohesion: 0.20
Nodes (5): datetime, 最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。, 孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。, _StubEcs, test_cleanup_deletes_an_old_orphan()

### Community 57 - "test_tunnel_cli.py"
Cohesion: 0.13
Nodes (22): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+14 more)

### Community 58 - "e2e_harness 使用说明"
Cohesion: 0.18
Nodes (13): ADR 0014 AI 断言投票, ADR 0024 worker↔core 协议 / 终止契约, ADR 0025 @scope: tag 分组, ADR 0029 产物→S3 / 边界抢传 / 固有残余, ADR 0032 Fargate 中断丢失量级 + 真容器 grace 校准, e2e_harness 使用说明, 边界抢传（act / scenario 边界）, grace 测量与 SIGKILL 兜底 (+5 more)

### Community 59 - "._resolve_target"
Cohesion: 0.17
Nodes (8): 供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。, `gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…, `gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。, 解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。…, cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 **不做版本 skew…, flag → CDK context（app/stack 侧读的那四个旋钮 + 版本戳）。 `--vpc` 一个 flag 摊成两个旋钮：`default`…, prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…, 写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本单旋钮）。 优先 CLI 皮交进来的 `args.version`（=…

### Community 60 - "Job"
Cohesion: 0.06
Nodes (74): DynamoDBRunStore, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, STATE item 上有没有 `detached` 标记（ADR 0034）：True = 无状态跑批的 submit 建的 run。 **adapter-…, RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。, Job, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传…, 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。… (+66 more)

### Community 61 - "test_event_sink.py"
Cohesion: 0.08
Nodes (12): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, _DeterministicCtx, 传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +… (+4 more)

### Community 62 - "test_user_facing_messages.py"
Cohesion: 0.27
Nodes (10): AST, _docstring_node_ids(), 护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…, module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。, 去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…, 五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。, _scan_midscene(), _scan_python() (+2 more)

### Community 63 - "gherkai_runtime/names.py"
Cohesion: 0.09
Nodes (28): container_name(), default_name(), ecr_repo_name(), image_tag(), job_timeout_schedule_prefix(), 资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…, 镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…, prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。 (+20 more)

### Community 64 - "0038. worker 镜像交付：基底、variant 与推送注册"
Cohesion: 0.11
Nodes (19): 0038. worker 镜像交付：基底、variant 与推送注册, `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）, `push-worker` 流程, SSM 参数与命名真源, 不变量, 与版本升级的交互, 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）, 多版本与多环境 (+11 more)

### Community 65 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 66 - "test_job_source.py"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 67 - "test_lambda_handlers.py"
Cohesion: 0.07
Nodes (26): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, _build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。, 防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。, definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。 (+18 more)

### Community 68 - "0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询"
Cohesion: 0.22
Nodes (9): 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询, 1. 注册面扩元数据（暴露的前提）, 2. worker 自述：`--list-deterministic` dump 模式, 3. CLI 子命令 `list-deterministic --engine <name>`, 4. plan 命中标注：「我写的这句会不会命中」, 决策, 背景与问题, 被拒方案（护栏） (+1 more)

### Community 69 - "test_argument.py"
Cohesion: 0.15
Nodes (19): _argument_text(), _clean_cell(), _instruction(), step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。, 单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构 → | 转义成…, 把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。 -…, 喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。, _unquote() (+11 more)

### Community 70 - "S3StepArgumentOffloader"
Cohesion: 0.07
Nodes (34): has_pointers(), _iter_arguments(), StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…, 按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。, 遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…, meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…, 把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。 (+26 more)

### Community 71 - "event-sink.mts"
Cohesion: 0.22
Nodes (6): ADR-0034, EventSink, ADR-0016, ADR-0024, ADR-0033, resolveEventsFd()

### Community 72 - "ADR 0027: RunReport 跨引擎归集索引"
Cohesion: 0.09
Nodes (23): ADR 0020: Step 措辞——默认 AI + 确定性锚点脚手架, 默认 AI 判断（裸 When/Then 无路由关键词）, URL 形态自动分流（含 URL → 确定性导航）, href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, LocalReportStore, manifest.json（薄信封 + report_index）, 被拒方案：materialize 产物拷贝 (+15 more)

### Community 73 - "render.py"
Cohesion: 0.17
Nodes (15): _arg_hint(), _cost_bits(), _dispatch_hint(), _ms(), plan_to_dict(), Job, 渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…, plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。 dispatch（可选，ADR 0036… (+7 more)

### Community 74 - "reconciler.py"
Cohesion: 0.15
Nodes (19): _build(), _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…, 本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带… (+11 more)

### Community 75 - "test_cloud_integration.py"
Cohesion: 0.17
Nodes (19): _ddb_store(), _is_ddb_too_large(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, 真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。, 真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛…, 真 DDB（2026）空串行为的回归基线：finalize 写 ended_at=""（顶层标量 SET）、update 写 session_id=""…, 给真表/真桶造一个本次运行专属的 run_id，避免多次跑撞名（无随机源，用递增计数）。 跨进程靠 it- 前缀 + fixture… (+11 more)

### Community 76 - "ecs_task_timing.py"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 77 - "RunPersistence 应用服务"
Cohesion: 0.22
Nodes (9): commit-point 写序（数据面先、控制面后）, DDB 单表 META/STATE 两 item, on_job_complete / on_event 回调（JobSink）, Store.preflight() 探活 + 退出码分层, ResultStore（判定真值、S3 后端）, RunPersistence 应用服务, RunState.jobs 改 Map<scope_id>, RunStore（create_run/update_job_state/finalize_run） (+1 more)

### Community 78 - "run-scope.test.mts"
Cohesion: 0.11
Nodes (10): _events, fakePage, ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031, ADR-0036 (+2 more)

### Community 79 - "_FakeEcs"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 81 - "ADR 0003 Qwen3-VL on Bedrock 做 grounding"
Cohesion: 0.36
Nodes (8): ADR 0002 不用 Bedrock GPT-5.5, ADR 0003 Qwen3-VL on Bedrock 做 grounding, ADR 0004 Nova Act 纯 IAM 经 Workflow 鉴权, ADR 0008 Midscene SigV4 自签鉴权, ADR 0009 最大化使用 AWS 硬约束, ADR 0012 planning 复用 Qwen3-VL, 文档健康度复盘任务, SIGV4-FETCH-RECIPE 配方笔记

### Community 82 - "schedule._Worker._run_once"
Cohesion: 0.29
Nodes (8): EX_WORKER_NETWORK = 80 exit code, schedule._heartbeat_wrap (silent-worker timeout fix), ScheduleOpts (network_retry, retry_sleep), schedule._Worker.run (network retry loop), schedule._Worker._run_once, Session leak protection before exit, subprocess_engine._read_events, core.errors.WorkerNetworkError

### Community 83 - "_stopped_detail"
Cohesion: 0.17
Nodes (12): 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, 同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。, 对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。, container 缺 exitCode（宽限态）→ None（机制二保守）。, stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…, _stopped_detail(), test_exit_observer_records_exit_for_detached_run(), test_exit_observer_skips_non_detached_run() (+4 more)

### Community 84 - "_progress"
Cohesion: 0.12
Nodes (29): _cloud_skew_gate(), _cloud_worker_variant_gate(), _cmd_list_deterministic(), _cmd_plan(), _cmd_run(), _cmd_submit(), _load_and_plan(), _preflight_worker_runtimes() (+21 more)

### Community 85 - "cloud_env"
Cohesion: 0.67
Nodes (3): cloud_env(), fixture, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。

### Community 86 - "test_detached_launcher.py"
Cohesion: 0.23
Nodes (16): per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…, run_reconcile_loop(), _job(), _now(), SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。 **真 spawn echo_worker…, 接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…, echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…, 真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。 (+8 more)

### Community 88 - "ensure_workflow_definition"
Cohesion: 0.10
Nodes (25): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+17 more)

### Community 89 - "_FakeEcs"
Cohesion: 0.15
Nodes (9): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null() (+1 more)

### Community 90 - "ADR 0017: Cloud Execution — Fargate over Runtime"
Cohesion: 0.33
Nodes (6): ADR 0017: Cloud Execution — Fargate over Runtime, AgentCore Evaluations（LLM-as-Judge，被否）, AgentCore Runtime（长驻 agent 服务）, 批处理 workload shape（run-to-exit）, ECS RunTask / Fargate 执行后端, 15 分钟 idle-kill 计时器与保活 plumbing

### Community 93 - "echo_worker.py"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 95 - "ArtifactUploader"
Cohesion: 0.17
Nodes (6): ADR-0028, ADR-0029, ArtifactUploader, ADR-0016, ADR-0024, ADR-0033

### Community 96 - "SqliteEventLog"
Cohesion: 0.17
Nodes (9): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+1 more)

### Community 97 - "权威信息源 REFERENCES"
Cohesion: 0.50
Nodes (4): 权威信息源 REFERENCES, AWS Bedrock / AgentCore 文档, Midscene 官方文档与源码 ground truth, Nova Act SDK 与 AgentCore provider

### Community 98 - "Midscene SigV4 自签 fetch 配方"
Cohesion: 0.50
Nodes (4): engines/midscene README, Midscene SigV4 自签 fetch 配方, createOpenAIClient 隔离 ModelConfigManager 坑, sigv4Fetch（最小手建请求签名）

### Community 99 - "deploy.py"
Cohesion: 0.16
Nodes (13): add_parsers(), _add_provider_flag(), provider_entry_points(), ArgumentParser, `gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…, `--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。, 已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。, 按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,… (+5 more)

### Community 101 - "ADR 0018: 通用 step 能力清单"
Cohesion: 0.25
Nodes (8): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）, 确定性锚点脚手架（deterministic.steps）, 角色边界：QA 零代码 / test engineer 建锚点

### Community 103 - "_StampSsm"
Cohesion: 0.15
Nodes (18): check_backend_skew(), 读后端版本戳 SSM 参数（`ssm_path(prefix, "version")`，由 stack 资源随部署事务写入，ADR 0037 决策 6）。…, 读后端版本戳 + 判 skew 一步到位（ADR 0037 决策 7）——**编排住产品本体、不住入口皮**：CLI / WebUI /…, read_backend_version(), _client_error(), 读戳 + 判定一步到位（编排住产品本体，入口皮只翻退出码）。, 凭证/权限类读错误原样抛（调用方归到自己的退出码层），不吞成「放行」——block 无放行口，读不到≠放过。, 假 ssm：读版本戳参数。`value=None` 模拟 `ParameterNotFound`（本机制之前部署的环境）。 (+10 more)

### Community 106 - "test_report_store.py"
Cohesion: 0.07
Nodes (62): ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。, collect_report_index(), _fmt_ms(), _local_path(), LocalReportStore, Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出… (+54 more)

### Community 107 - "test_tunnel.py"
Cohesion: 0.17
Nodes (15): NgrokTunnel, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, TunnelInfo, _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。 (+7 more)

### Community 108 - "build_fargate_engines"
Cohesion: 0.16
Nodes (14): build_cloud_stores(), build_fargate_engines(), _make_ddb_table(), _make_s3_client(), _normalize_prefix(), S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。, boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…, boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。 (+6 more)

### Community 109 - "_render_status"
Cohesion: 0.23
Nodes (14): 渲染 RunState + pending 诊断提示 + 退出码——**local/cloud 共享一份**（保两路一致，ADR 0034）。 state…, _render_status(), _args(), _mk_state(), pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。 (+6 more)

### Community 110 - "package.json"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 111 - "_referenced_by_live_run"
Cohesion: 0.50
Nodes (4): _non_terminal_statuses(), 未到终态的 run 级 status 全集（`Status` - `TERMINAL_STATUSES`，至少含 `pending`）。 **从 core…, 有未到终态的 run 引用这个 revision 吗？—— **走 status GSI 的 Query + `contains` 过滤，绝不 Scan**。…, _referenced_by_live_run()

### Community 113 - "Status"
Cohesion: 0.06
Nodes (31): 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, Status, Engine, EngineResolver, JobSink, Event, Job, Protocol (+23 more)

### Community 114 - "aws"
Cohesion: 0.67
Nodes (3): aws(), _aws_env(), fixture

### Community 119 - "CI 与发布链（`.github/`）"
Cohesion: 0.15
Nodes (13): 1. PyPI 占名（先于一切）, 2. PyPI trusted publisher × 5（只有真发行的五个需要）, 3. npm token → repo secret `NPM_TOKEN`, 4. GHCR：首次推送后把两个 package 改成 public, 5. 仓库本身必须是 public, CI 与发布链（`.github/`）, `release.yml` 的 job 图与重跑语义, TestPyPI 演练（推正式 tag 之前排一次） (+5 more)

### Community 120 - "events_table"
Cohesion: 0.67
Nodes (3): events_table(), fixture, events 表（PK=pk/SK=seq，同 conftest 的 runs 表不同）——P4 单独建，schema 见 ADR 0033/0024。

### Community 121 - "_Recorder"
Cohesion: 0.13
Nodes (12): cdk(), _clean_aws_env(), _FakeEngine, fixture, 把 AWS/前缀相关 env 清干净：解析链会读它们（`compose.resolve_cloud_target`），开发机上的值会让断言飘。, `subprocess.run` 替身：记下 argv/cwd/env，返回给定 returncode。, 容器引擎替身（`probe()` 说「可用」）——deploy 前的容器引擎前置不该在单测里真跑 docker。, 把 Node 前置、cdk 定位、容器引擎与 worker 镜像四步都打桩掉，只留「拼出的 argv/env」这一层给断言。… (+4 more)

### Community 122 - "exit_observer.py"
Cohesion: 0.27
Nodes (9): _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…, 构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。 (+1 more)

### Community 123 - "gherkai-deploy-aws"
Cohesion: 0.15
Nodes (13): gherkai-deploy-aws, Lambda 打包（`stack._build_lambda_asset`）, prefix 契约（关键）, VPC 三档 + 档比对（踩过的坑，别放松）, worker 镜像：基底 / variant / 默认指针（ADR [0038](../docs/adr/0038-worker-image-delivery.md)）, 事件驱动推进（无状态跑批，ADR 0034）, 定制镜像模板（三行，gherkai 不拥有构建）, 建什么 (+5 more)

### Community 124 - "agentcore-sigv4.mts"
Cohesion: 0.33
Nodes (8): getBaseUrl(), getRegion(), MODEL, modelSigner_(), ADR-0033, ADR-0037, signCdpUpgrade(), sigv4Fetch()

### Community 126 - "_spawn_and_wait_ready"
Cohesion: 0.24
Nodes (9): parametrize, Popen, 进程级真信号回归哨兵（ADR 0024 flag-only 中断模型）。 补上 test_interrupt_model.py（拦 signal.signal…, spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。, 真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。, 反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。, _spawn_and_wait_ready(), test_worker_cooperative_stop_on_signal() (+1 more)

### Community 127 - "_FakeResult"
Cohesion: 0.17
Nodes (5): _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。

### Community 128 - "map_origin_in_jobs"
Cohesion: 0.31
Nodes (9): map_origin_in_jobs(), Job, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, _job_with(), Job, StepArgument, test_map_leaves_non_matching_urls_untouched(), test_map_replaces_docstring_and_datatable() (+1 more)

### Community 129 - "gherkai_cli/__main__.py"
Cohesion: 0.11
Nodes (23): _build_parser(), _cmd_deploy(), _cmd_destroy(), _cmd_list_engines(), _cmd_tunnel_watch(), _deploy_provider(), _dist_version(), _installed_version() (+15 more)

### Community 130 - "_ClientError"
Cohesion: 0.18
Nodes (5): _Cfn, _ClientError, Exception, botocore ClientError 的形状替身（`response["Error"]["Code"]` + 文案）——本包按鸭子类型读它。, _Ssm

### Community 131 - "main"
Cohesion: 0.39
Nodes (8): fail(), main(), member_dist_names(), normalize(), Path, 发行名 → 产物文件名里的形态（PEP 503 规范化后 `-`/`.` 变 `_`，见 PEP 427/625）。, 真值集：workspace 成员目录 → 其 `[project] name`（发行名）。, wheel_metadata()

### Community 132 - "gherkai_runtime/__init__.py"
Cohesion: 0.20
Nodes (9): gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 133 - "tunnel.py"
Cohesion: 0.22
Nodes (9): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。, 生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。, TunnelError (+1 more)

### Community 135 - "分发与打包施工进度总纲（ADR 0037 / 0038 落地）"
Cohesion: 0.22
Nodes (9): 关键中间结论 / 待办, 决定记录（施工中拍的、不改 ADR 的实施细节）, 分发与打包施工进度总纲（ADR 0037 / 0038 落地）, 当前状态, 施工次序（0037「落地次序」，此处只记进度）, 阶段 1 的批次, 阶段 2 记录, 阶段 3/4 记录 (+1 more)

### Community 136 - "_cmd_status"
Cohesion: 0.25
Nodes (8): _cmd_reconcile(), _cmd_status(), cloud status：读 DDB RunState 渲染。--wait 则无感接力兜底——**检测卡住才** invoke kicker Lambda 做…, per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR…, `--max-concurrency` 入口校验（对齐 `--tunnel-ttl`/`--grace`/`--assertion-votes`…, [无状态跑批] 查 run 进度/结果。 - local：读文件 RunState；--wait 则本机接力 tick 到终态（三触发源之一，per-run…, _status_cloud(), _validate_max_concurrency()

### Community 137 - "stop_tunnel"
Cohesion: 0.29
Nodes (7): cleanup_tunnel(), 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 138 - "test_worker_subnets_single_source_across_ssm_and_lambda_env"
Cohesion: 0.50
Nodes (4): _joined_refs(), 从模板值（Fn::Join）取出被拼接的资源 Ref 序列。SSM StringList 与 Lambda env 的 Join 形态不同 （分隔符一个在…, subnet 选取（公有优先、无则回落私有）只有一处落点 `_worker_subnet_ids`：写给 cli 读的 SSM 与…, test_worker_subnets_single_source_across_ssm_and_lambda_env()

### Community 139 - "test_subprocess_engine.py"
Cohesion: 0.28
Nodes (16): 内存假 Engine（测试夹具，ADR 0026「接口是测试面」）。 直接在进程内吐预设的 ADR 0024 事件流，不 spawn 子进程、不连…, _engine(), _job(), Job, 子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…, _rm(), test_adapter_crash_is_error(), test_adapter_network_error_with_schedule_classified_and_retried() (+8 more)

### Community 140 - "_seed_worker_ssm"
Cohesion: 0.25
Nodes (8): 把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。, definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…, definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。, kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。, _seed_worker_ssm(), test_build_falls_back_to_default_pointer_for_legacy_definition(), test_build_uses_definition_worker_task_defs_verbatim(), test_kicker_uses_definition_worker_task_defs()

### Community 142 - "test_interrupt_model.py"
Cohesion: 0.11
Nodes (23): _aggregate(), _emit_scenario_done_unless_stopped(), scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…, _run_scenario(), _FakeResult, _Meta, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM… (+15 more)

### Community 143 - "_NetRaiseEngine"
Cohesion: 0.16
Nodes (7): FakeWorkerHandle, Event, Job, _AbortProbeEngine, _NetRaiseEngine, Event, victim job 的 worker：等一个 gate 放行后才抛 WorkerNetworkError（模拟「建连退避期间」被中止/超时后退 80）。…

### Community 145 - "test_lifecycle_states.py"
Cohesion: 0.15
Nodes (11): 终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。, severity(), _aggregate(), 终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一…, job 生命周期态 + severity 单测（ADR 0031）：skipped/aborted/pending/running、severity…, test_aggregate_all_skipped_no_error_not_misjudged_passed(), test_aggregate_filters_non_verdict(), test_aggregate_running_does_not_pollute_clean_pass() (+3 more)

### Community 147 - ".add_arguments"
Cohesion: 0.23
Nodes (7): ArgumentParser, 把 provider 特有 flag 挂上 CLI 给的 parser。…, 这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。, 这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…, `push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…, `--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。, 子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…

### Community 149 - "_FakeSink"
Cohesion: 0.18
Nodes (5): captured(), _FakeSink, fixture, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 150 - "JobSource"
Cohesion: 0.22
Nodes (4): Job, JobSource, ADR-0016, ADR-0024

### Community 151 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 152 - "cli.py"
Cohesion: 0.07
Nodes (34): check_node(), classify_vpc_state(), _error_code(), _make_cfn_client(), _make_ssm_client(), _node_major(), Exception, `gherkai deploy` 的 AWS provider（entry point group `gherkai.deploy` 的 `aws`… (+26 more)

### Community 154 - "_CdkWritingContext"
Cohesion: 0.24
Nodes (11): context_cache_path(), CDK 环境查询缓存（`cdk.context.json`）的持久化位置：`$XDG_CACHE_HOME`（缺省…, _cache_env(), _CdkWritingContext, `subprocess.run` 替身：像真 cdk 做过 from_lookup 那样，在 cwd 写下 `cdk.context.json`；并记下进…, 工作目录一次性 → 若每次空着进去，cdk 会对缺失的 lookup 值先用占位 VPC 预合成一遍（触发模板校验 warning、 多一轮查询）。缓存按…, cdk 退非零也存回：查到的 lookup 值本身是对的，deploy 因别的原因失败不该让下次重查一遍。, test_context_cache_is_per_prefix() (+3 more)

### Community 158 - "_stream_record"
Cohesion: 0.15
Nodes (13): scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, _stream_record(), test_reconciler_noop_for_non_detached_run(), test_reconciler_ticks_detached_run() (+5 more)

### Community 159 - "_argv"
Cohesion: 0.15
Nodes (13): _argv(), _parse_destroy(), Path, 用户给**相对** DIR：必须钉成绝对路径再交 cdk——cdk 子进程 cwd 是随后被删的临时工作目录，相对路径…, cdk destroy 在非 TTY 下拒绝无确认的销毁（真跑撞到）；`--yes` = `--force`，不给则让 cdk 自己问。, bootstrap 走显式 `aws://<account>/<region>`、不带 `--app`——cdk 有显式环境又无 app 时直奔凭证， 不会跑…, test_bootstrap_needs_no_vpc_and_never_loads_the_app(), test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() (+5 more)

### Community 160 - "05-negative-assertions.ts"
Cohesion: 0.29
Nodes (6): BASE_URL, Check, main(), MODEL_CONFIG, REGION, ADR-0033

### Community 161 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 162 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 163 - "WorkerNetworkError"
Cohesion: 0.15
Nodes (12): RuntimeError, core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…, WorkerNetworkError, raise_for_worker_exit(), worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, test_raise_for_worker_exit_maps_codes_with_fargate_label() (+4 more)

### Community 164 - "_submit_local"
Cohesion: 0.50
Nodes (4): local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。, _submit_local(), local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。, write_tunnel_file()

### Community 165 - "_ssm_params"
Cohesion: 0.15
Nodes (13): Template, SSM 参数**全集**钉死（枚举型护栏）：网络 2（subnets/security-groups，cli resolve_network 读） + 部署戳…, 模板里全部 SSM 参数：Name → Properties。Name 恒是字面量（路径由 prefix 纯推导、无 token）。, 建新档记 `new:<所建 vpc-id>`——**带出 id 才可回溯核对**（ADR 0037 决策 6）。 id 是部署期才有值的 CDK…, 每引擎一个 `worker-template/<engine>` 参数，值 = task-def 的 `Ref`（**带 revision** 的 ARN）。…, _ssm_params(), test_prefix_switches_whole_set(), test_ssm_parameter_set_is_exactly_six() (+5 more)

### Community 166 - "deterministic.py"
Cohesion: 0.18
Nodes (12): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 test engineer 用 `@deterministic(pattern)`…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+4 more)

### Community 167 - "test_container.py"
Cohesion: 0.05
Nodes (49): ContainerEngine, digest_for_repo(), ImageInfo, 容器引擎口子（ADR 0038「容器引擎口子」）：worker 镜像交付碰容器引擎的**唯一落点**。 **只五个动词**：`inspect`（存在 +…, 引擎可用吗？可用 → None；不可用 → 给人看的一句（**不抛**，同 `cli.check_node` 的口径）。 两级：PATH…, 本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…, 登录 registry。**密码经 stdin**（`--password-stdin`）——绝不进 argv（见模块头）。, 推镜像。**输出直通用户终端**（层进度条要能看见——推一个 worker 镜像是分钟级的事）。 (+41 more)

### Community 168 - "resolve_network"
Cohesion: 0.25
Nodes (8): 读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…, Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…, _read_ssm_list(), resolve_network(), test_resolve_network_empty_ssm_fails_fast(), test_resolve_network_explicit_overrides_skip_ssm(), test_resolve_network_partial_override_reads_only_missing(), test_resolve_network_reads_ssm_when_missing()

### Community 169 - "_patch_skew"
Cohesion: 0.50
Nodes (4): _patch_skew(), --wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 退 2，不再吞掉死等…, 把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。 两处都得…, test_status_wait_cloud_kicker_missing_fails_fast()

### Community 170 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 172 - "_FakeSink"
Cohesion: 0.17
Nodes (7): captured(), _FakeSink, fixture, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。, _reset_stop()

### Community 173 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 174 - "events_pk"
Cohesion: 0.18
Nodes (7): 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, events_pk(), events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。, test_events_pk_composite_run_id_scope_id()

### Community 175 - "stack.py"
Cohesion: 0.25
Nodes (5): main(), CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。…, CloudFormation stack 名（= `app.py` 给 `BackendStack` 的 construct id，CDK 据此定 stack…, stack_name(), BackendStack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按 prefix…

### Community 177 - "build_local_reconcile"
Cohesion: 0.24
Nodes (10): build_local_reconcile(), 从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…, 落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。, 并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…, 对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。, 对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/cloud 档）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…, _seed_for_build(), test_build_local_reconcile_falls_back_to_flag_when_meta_missing() (+2 more)

### Community 178 - "detached.py"
Cohesion: 0.33
Nodes (4): events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, _paths(), 无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…, local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。

### Community 179 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。 用途：少数"必须精确、不容 AI 抖动"的断言（如…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（test engineer 约定的带关键词措辞，与 QA…, url_matches()

### Community 180 - "04-planning-probe.ts"
Cohesion: 0.50
Nodes (3): BASE_URL, main(), ADR-0033

### Community 181 - "CloudTarget"
Cohesion: 0.50
Nodes (3): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态跑批事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序＝链上顺序。

### Community 182 - "_UnavailableEngine"
Cohesion: 0.33
Nodes (3): Exception, 某引擎这次装配不出来时的「一用即抛」空腿——两档共用（local: ADR 0037 决策 3；cloud: ADR 0038）。 存在的理由：两个…, _UnavailableEngine

### Community 183 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 184 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 185 - "_isolate"
Cohesion: 0.67
Nodes (3): _isolate(), fixture, 注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。

### Community 187 - "artifact-upload.test.mts"
Cohesion: 0.50
Nodes (3): mkLogDir(), ADR-0029, tmproot()

### Community 191 - "files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 192 - "repository"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 193 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 197 - "scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 203 - "SubprocessLauncher"
Cohesion: 0.18
Nodes (7): Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。, worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。, SubprocessEngine, Job, local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…, 驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…, SubprocessLauncher

### Community 207 - "test_run_state_timestamps_share_one_format"
Cohesion: 0.18
Nodes (11): now_iso(), parse_iso(), datetime, `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, 接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…, _recover_timed_out_claims(), _echo_resolver() (+3 more)

### Community 208 - "test_lambda_asset.py"
Cohesion: 0.11
Nodes (25): make_stack(), synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。…, **带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，…, asset_dir(), _fake_installed_sources(), _patch_sources(), fixture, Path (+17 more)

### Community 246 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 247 - "ContainerError"
Cohesion: 0.14
Nodes (10): ContainerError, Exception, 容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…, CleanupOutcome, family 里的一个 ACTIVE revision + 它的 tags。, 带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。, 一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。供 `list-workers`/测试读。, RevisionInfo (+2 more)

## Ambiguous Edges - Review These
- `通用 step（QA 零代码的唯一载体）` → `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md · relation: conceptually_related_to

## Knowledge Gaps
- **307 isolated node(s):** `背景与问题`, `概念模型`, `命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）`, ``push-worker` 流程`, ``gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）` (+302 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **65 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `通用 step（QA 零代码的唯一载体）` and `ADR 0019 用 Gherkin tag 声明 scope 与 engine`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `schedule()` connect `schedule` to `schedule.py`, `test_subprocess_engine.py`, `test_schedule.py`, `test_interrupt_model.py`, `test_lifecycle_states.py`, `model.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `_aggregate()` connect `test_interrupt_model.py` to `schedule.py`, `run_scope.py`, `schedule`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `DynamoDBRunStore` connect `Job` to `S3StepArgumentOffloader`, `compose.py`, `_cmd_status`, `EventBridgeTimeoutWatch`, `reconciler.py`, `test_cloud_integration.py`, `query_deterministic`, `build_fargate_engines`, `fargate_engine.py`, `test_conditional_writes.py`, `test_tunnel_host.py`, `CloudTarget`, `_UnavailableEngine`, `test_project.py`, `exit_observer.py`, `run_store/ddb.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `RunState` (e.g. with `LocalRunStore` and `RunPersistence`) actually correct?**
  _`RunState` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `RunMeta` (e.g. with `LocalRunStore` and `RunPersistence`) actually correct?**
  _`RunMeta` has 26 INFERRED edges - model-reasoned connections that need verification._