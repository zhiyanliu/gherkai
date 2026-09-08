# Graph Report - yaozhou  (2026-09-07)

## Corpus Check
- 199 files · ~161,082 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2951 nodes · 6561 edges · 216 communities (137 shown, 79 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 483 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `27509691`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CloudLauncher
- raise_for_worker_exit
- test_run_step.py
- ScopeStarted
- test_plan.py
- test_stack.py
- RunState
- test_schedule.py
- Job
- .create_run
- test_user_steps.py
- test_cloud_reconcile.py
- _is_transient_network
- build_engines
- dependencies
- fixture
- gherkai_cli/__main__.py
- test_conditional_writes.py
- main
- test_artifact_upload.py
- test_reconcile.py
- 03-midscene-grounding.ts
- parse.py
- test_backend_cloud.py
- exit_observer.py
- test_fargate_engine.py
- resolve_worker_cmd
- StepArgument
- JobState
- RunPersistence
- model.py
- RunResult
- 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel
- reconciler.py
- StepResult
- ADR 0034 — Detached Batch Reconciler
- FargateEngine
- run-scope.mts
- compose.py
- run_scope.py
- preflight_cloud_resources
- gherkai_runtime/names.py
- 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器
- test_s3_report_store.py
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
- {prefix}cluster + Fargate task definitions
- project
- subprocess_engine.py
- test_tunnel_cli.py
- e2e_harness 使用说明
- fargate_engine.py
- test_sqlite_event_log.py
- test_event_sink.py
- build_push_workers.py
- _mk_state
- 0038. worker 镜像交付：基底、variant 与推送注册
- test_cloud_integration.py
- JobSource
- LocalRunStore
- 0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询
- test_argument.py
- S3StepArgumentOffloader
- event-sink.mts
- ADR 0027: RunReport 跨引擎归集索引
- render.py
- parametrize
- test_project.py
- ecs_task_timing.py
- RunPersistence 应用服务
- run-scope.test.mts
- JobResult
- Job
- ADR 0003 Qwen3-VL on Bedrock 做 grounding
- schedule._Worker._run_once
- main
- _TrajNova
- Job
- test_detached_launcher.py
- SqliteEventLog
- ensure_workflow_definition
- Job
- ADR 0017: Cloud Execution — Fargate over Runtime
- _FakeS3
- _FakeEcs
- echo_worker.py
- test_cloud_infra.py
- ArtifactUploader
- _SeqEcs
- 权威信息源 REFERENCES
- Midscene SigV4 自签 fetch 配方
- test_submit_local_exits_2_when_worker_runtime_missing
- gherkai
- _FakeTable
- 02-agentcore-cdp.ts
- gherkai_worker_novaact/__init__.py
- .project_state
- cli/__main__.py（argparse 皮 + 退出码）
- test_report_store.py
- test_tunnel.py
- _FakeEcs
- _presend_act_siblings
- package.json
- DynamoDB stream event source mappings
- gherkai-runtime
- S3ResultStore
- test_lambda_handlers.py
- 开放性动作导致页面瞬态 flaky
- session_id lineage on scope_started
- ADR 0030 实时落库接缝
- deterministic_steps.py
- tunnel.py
- iac_aws_backend CDK 工程
- prefix contract
- {prefix}artifacts S3 bucket
- agentcore-sigv4.mts
- wikipedia SSL 环境坑
- deterministic.py
- _FakeResult
- Job
- _det_feature
- test_final_drain_paginates_across_last_evaluated_key
- fixture
- tunnel_host.py
- Scenario
- gherkai-core
- 分发与打包施工进度总纲（ADR 0037 / 0038 落地）
- user_steps.py
- stop_tunnel
- BaseException
- resolve_cloud_target
- _runs_stream_record
- adapters/__init__.py
- test_interrupt_model.py
- _FakeSink
- gherkai_core/__init__.py
- _reconcile_lambdas (stack wiring)
- README.md
- _stream_record
- cloud_env
- _FakeSink
- JobSource
- user-steps.mts
- .preflight
- 成本可观测（engine 只报原生量、core 不折美元）
- test_starter_run_ids_empty_when_neither
- Ports 层（Engine/RunStore/ResultStore/ReportStore）
- 报告产物模型 / RunReport 归集索引
- plan_next
- BaseException
- ResourceUri
- 05-negative-assertions.ts
- argument.mts
- user-steps.test.mts
- WorkerNotFoundError
- Job
- Job
- Job
- Job
- Popen
- Job
- Job
- Job
- Job
- 01-model-sigv4.ts
- Scenario
- Step
- StepArgument
- Job
- Step
- StepArgument
- parametrize
- Job
- test_scan_overdue_timeouts_only_over_budget
- bin.mts
- devDependencies
- Job
- StepArgument
- artifact-upload.test.mts
- EventBridgeTimeoutWatch
- test_build_cap_defaults_to_one_when_env_absent
- iac_aws_backend README
- files
- repository
- index.mts
- resolve-hook.mts
- event-sink.test.mts
- test_compose.py
- scripts
- agentcore-sigv4.test.mts
- job-source.test.mts
- _isolate
- @aws-sdk/client-bedrock-agentcore
- @aws-sdk/client-dynamodb
- openai
- tsx
- argument.test.mts
- deterministic.test.mts
- test_kicker_timeout_path_skips_tick_when_not_detached
- Path
- Path
- engines/novaact README
- Exception
- fixture
- Popen
- Exception
- gherkai-worker-novaact

## God Nodes (most connected - your core abstractions)
1. `Job` - 130 edges
2. `RunMeta` - 101 edges
3. `RunState` - 95 edges
4. `main()` - 92 edges
5. `Status` - 80 edges
6. `JobState` - 79 edges
7. `JobResult` - 67 edges
8. `schedule()` - 63 edges
9. `Scenario` - 62 edges
10. `Step` - 62 edges

## Surprising Connections (you probably didn't know these)
- `通用 step（QA 零代码的唯一载体）` --conceptually_related_to--> `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md → docs/adr/0019-feature-tags-scope-and-engine.md
- `_runtime_version()` --calls--> `_dist_version()`  [INFERRED]
  runtime/gherkai_runtime/compose.py → cli/gherkai_cli/__main__.py
- `_load_and_plan()` --calls--> `plan()`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/scope.py
- `_load_and_plan()` --calls--> `PlanConfig`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/scope.py
- `_cmd_submit()` --calls--> `JobState`  [INFERRED]
  cli/gherkai_cli/__main__.py → core/gherkai_core/model.py

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

## Communities (216 total, 79 thin omitted)

### Community 0 - "CloudLauncher"
Cohesion: 0.13
Nodes (16): CloudLauncher, cloud Launcher：按 job.engine 选 FargateEngine（经注入的…, _FakeStartEngine, CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。, job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…, 无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。, 武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时， 先建的…, start_scope 抛异常：arm 已先行（schedule 在，双失败兜底生效）、异常照常冒泡（tick 靠它触发 launch 失败补偿… (+8 more)

### Community 1 - "raise_for_worker_exit"
Cohesion: 0.25
Nodes (8): raise_for_worker_exit(), worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。 80 →…, 码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…, test_raise_for_worker_exit_maps_codes_with_fargate_label(), 码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 /…, 两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。, test_raise_for_worker_exit_label_names_the_transport_field(), test_raise_for_worker_exit_maps_codes()

### Community 2 - "test_run_step.py"
Cohesion: 0.19
Nodes (27): _classify_act_error(), 派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。…, 把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…, _run_step(), _done(), _FakeNova, _run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。 与 Midscene 引擎 run-scope.test.ts…, 注入 fake：act_get 按布尔序列逐票回；act/go_to_url 记调用。act 可设异常模拟中途失败。 tw_seq：每票… (+19 more)

### Community 3 - "ScopeStarted"
Cohesion: 0.10
Nodes (27): SqliteEventLog（ADR 0034）：local 无状态跑批的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…, ScopeStarted, Action, _aggregate(), EventRecord, _job_status(), project_full(), 纯归约投影（ADR 0034）：events → JobResult/RunState，无 I/O、无执行编排、不 import boto3。… (+19 more)

### Community 4 - "test_plan.py"
Cohesion: 0.07
Nodes (56): PlanError, feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…, ParsedScenario, parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…, FeatureSource, plan(), PlanConfig, scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine 校验 → Job[]。 对外入口… (+48 more)

### Community 5 - "test_stack.py"
Cohesion: 0.05
Nodes (51): Cluster, Construct, BackendStack, worker task 落哪些 subnet——「优先公有子网、无则回落私有」这条契约的**唯一落点**（ADR 0033）。 三个消费者必须恒等（都喂同一个…, task role 最小权限（ADR 0033 IAM 表，按动作×资源收窄）。两个引擎共享的 + 各引擎特有的。, 事件驱动推进链（ADR 0034 端到端 cloud 流程）： - **退出观察者 Lambda**：EventBridge ECS Task STOPPED…, 把 Lambda 代码打包到一个目录，返回其路径（Code.from_asset 用）。 内容 = lambdas/*.py（handler）+…, worker 安全组 id——_ssm_network 建的 sg。存引用供 reconciler Lambda 起 task 用同一 sg。 (+43 more)

### Community 6 - "RunState"
Cohesion: 0.07
Nodes (29): 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…, 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire…, RunState, Status, RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。 为什么是 core…, run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。 满足 ADR…, Engine, EngineResolver (+21 more)

### Community 7 - "test_schedule.py"
Cohesion: 0.05
Nodes (140): format_event(), Event, 单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…, test_format_event_omits_scope_id(), test_format_event_single_vote_hides_tally(), test_format_event_step_done_with_votes_and_cost(), core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…, worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`… (+132 more)

### Community 8 - "Job"
Cohesion: 0.06
Nodes (69): DynamoDBRunStore, 探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。 用 `table.load()`（=…, CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending…, STATE item 上有没有 `detached` 标记（ADR 0034）：True = 无状态跑批的 submit 建的 run。 **adapter-…, RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。, 读回 definition（RunMeta）；不存在返回 None。, Job, step 的多行参数（DataTable / DocString），由 parse 从 pickle 重映射成自有形状（ADR 0025）。 不透传… (+61 more)

### Community 9 - ".create_run"
Cohesion: 0.12
Nodes (15): _job_state_from_item(), _job_state_to_item(), RunState, 按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。 #sid…, commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。, 状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。, 一次性写完整态（= create_run 的两 item 一起 put；语义同 local save_run）。, 读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。… (+7 more)

### Community 10 - "test_user_steps.py"
Cohesion: 0.12
Nodes (28): load_user_steps(), 加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…, _clean_env(), parametrize, 使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…, 给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。, 使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。, 真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。… (+20 more)

### Community 11 - "test_cloud_reconcile.py"
Cohesion: 0.10
Nodes (29): DdbEventLog, 退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…, cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…, 读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…, 从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…, 单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…, events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…, events_pk() (+21 more)

### Community 12 - "_is_transient_network"
Cohesion: 0.12
Nodes (32): _is_transient_client_error(), _is_transient_network(), BaseException, boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。, 是否网络/SSL 瞬时故障（可重试，ADR 0028）。 白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与…, _client_error(), _is_transient_network 单测（ADR 0028）：白名单瞬时识别 + 异常链遍历 + gaierror errno 细分。 重点护住…, 按名兜底（playwright 私有路径 import 失败时）也必须在**链内**命中——曾只查最外层 e, 而真实故障链最外层是… (+24 more)

### Community 13 - "build_engines"
Cohesion: 0.08
Nodes (30): Engine, FeatureSource, build_engines(), load_feature(), make_resolver(), 每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 no_artifacts（`--no-…, dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。, 读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导… (+22 more)

### Community 14 - "dependencies"
Cohesion: 0.12
Nodes (17): @aws-crypto/sha256-js, @aws-sdk/client-s3, @aws-sdk/credential-providers, @aws-sdk/protocol-http, @aws-sdk/signature-v4, dependencies, @aws-crypto/sha256-js, @aws-sdk/client-s3 (+9 more)

### Community 16 - "gherkai_cli/__main__.py"
Cohesion: 0.07
Nodes (52): ArgumentParser, _build_parser(), _cmd_list_deterministic(), _cmd_list_engines(), _cmd_plan(), _cmd_reconcile(), _cmd_run(), _cmd_status() (+44 more)

### Community 17 - "test_conditional_writes.py"
Cohesion: 0.11
Nodes (32): _initial(), _meta(), RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…, 关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。, 同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。, 关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…, 机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。, 投影写不抹 create_run 落的 started_at（曾为 ddb put_item 整 item 覆盖之疾，对拍 local）。 (+24 more)

### Community 18 - "main"
Cohesion: 0.07
Nodes (68): main(), _capturing_schedule(), _fake_schedule_factory(), _fake_worker_cmd(), Path, cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS）， 验证落盘三层产物 + --json…, 造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job…, 假 schedule：把传入 opts 存进 opts_box、按指定 status 合成 RunResult（验退出码/参数映射）。 (+60 more)

### Community 19 - "test_artifact_upload.py"
Cohesion: 0.08
Nodes (29): ArtifactUploader, _extra_args(), Path, 产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…, scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmtree 整目录（ADR 0029）。 no-op（未注入落点）→…, upload_file 的 ExtraArgs（两处上传共用，避免第三处漂移）：仅在有映射时带 ContentType。, 按注入的 S3 落点上传产物、生成 report ref。无落点配置时是 no-op（报 file://、不上传）。 组合根经 env 注入（ADR…, 从组合根注入的 env 造。无 `ARTIFACT_S3_BUCKET` → no-op uploader（报 file://）。 (+21 more)

### Community 20 - "test_reconcile.py"
Cohesion: 0.11
Nodes (28): EventLog, Launcher, Protocol, 事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的 events 由…, 起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。 local = 起 subprocess worker（事件旁路落 SQLite…, 推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…, tick(), _done_events() (+20 more)

### Community 21 - "03-midscene-grounding.ts"
Cohesion: 0.29
Nodes (6): ADR-0010, BASE_URL, main(), MODEL_CONFIG, REGION, ADR-0033

### Community 22 - "parse.py"
Cohesion: 0.23
Nodes (11): _index_ast_lines(), _map_argument(), parse_feature(), parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…, pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…, pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…, 解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是…, pickle step type → 派发关键字（Given/When/Then）。type='Unknown' 一律 fail-fast。 Compiler… (+3 more)

### Community 23 - "test_backend_cloud.py"
Cohesion: 0.11
Nodes (43): _fake_schedule_factory(), _patch_cloud_handles(), Path, cli --backend cloud 接线层测试（ADR 0016「cli backend 选择」/ 0030 决定七 / 0033 IaC+接线）。…, 不起 worker 的假 schedule：走完 on_event/on_job_complete 实时落库路径（让 adapter 真被调）。, submit cloud 的 preflight 除表/桶/cluster 外还探：本 run 用到引擎的 task-def + 事件驱动链三 Lambda…, 非默认 --report-dir 也要交给 preflight 比对（否则提交侧/推进侧前缀静默分裂、结果落别处）。, preflight 报资源缺（如链上 Lambda 不存在）→ 提交前退 2、不写任何东西。 (+35 more)

### Community 24 - "exit_observer.py"
Cohesion: 0.19
Nodes (11): iac_aws_backend Stack（ADR 0033）：`--backend cloud` 需要的全部 AWS 资源。 一套 stack 建齐（可按…, _event_log(), _extract(), handler(), _is_detached(), 退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…, 从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…, 本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。… (+3 more)

### Community 25 - "test_fargate_engine.py"
Cohesion: 0.11
Nodes (45): _delayed_stopped_ecs(), _engine(), _job(), _put_event(), _put_exit_item(), FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…, worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。, 模拟 worker：往 events 表 PutItem 一条事件（PK=run_id#scope_id, SK=seq, body=JSON line）。 (+37 more)

### Community 26 - "resolve_worker_cmd"
Cohesion: 0.07
Nodes (30): _find_worker_spec(), _is_pure_release(), 一个引擎 worker 的拉起方式 = 定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂…, 版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…, 按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…, `find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。, 本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（源码直跑）→ None。, resolve_worker_cmd() (+22 more)

### Community 28 - "JobState"
Cohesion: 0.10
Nodes (43): test_render_run_state_lists_jobs_and_session_lineage(), test_render_run_state_shows_ended_at_when_terminal(), 读回 definition（从 META item 的 meta_json）；不存在返回 None。, JobState, 单个 job 的控制面运行态（执行后才有）。, 从 RunResult 投影出控制面运行态（ADR 0016/0027）。…, run_state_from_result(), from_dict() (+35 more)

### Community 29 - "RunPersistence"
Cohesion: 0.09
Nodes (29): ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。, LocalResultStore, Path, ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。, 把单个 JobResult 落盘成 <root>/<run_id>/jobs/<encoded_scope_id>.json（追加，写面）。, 读回单个 JobResult（读回面）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。, 探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。 (+21 more)

### Community 30 - "model.py"
Cohesion: 0.09
Nodes (31): CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate…, LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…, S3ResultStore（ADR 0030 决定六 / 0016 三层选型）：ResultStore port 的 S3 实装。 数据面判定真值——每个…, DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。 对拍 `LocalRunStore`…, LocalRunStore（ADR 0016 控制面 / 0027 落点对齐）：落 run 的 definition + 运行态，可读回。 三层切分（ADR…, 领域模型：worker↔core 协议（ADR 0024）+ plan 产出（ADR 0025）的纯数据结构。 无逻辑、无 I/O——只是 core…, _argument_from_dict(), _argument_to_dict() (+23 more)

### Community 31 - "RunResult"
Cohesion: 0.09
Nodes (22): ReportStore adapters（ADR 0027）。当前只有 local；未来 s3。, collect_report_index(), _fmt_ms(), _local_path(), Path, ResourceUri, LocalReportStore（ADR 0027）：把一次 run 的报告产物归集成本地一份自包含目录。 产出…, 遍历 result 树投影 report_index（复用共享 collect_report_index）。 make_href：把落在 run… (+14 more)

### Community 32 - "0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel"
Cohesion: 0.08
Nodes (24): 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel, 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条, 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵, 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra, 2d. `requires-python >=3.13` 维持, 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）, 决策 1：交付物按打包技术划分，worker 运行时是硬核, 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first (+16 more)

### Community 33 - "reconciler.py"
Cohesion: 0.17
Nodes (17): _build(), _handle_timeout(), handler(), kicker_handler(), reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…, 防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…, cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher +…, 从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch… (+9 more)

### Community 34 - "StepResult"
Cohesion: 0.19
Nodes (17): cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。 __main__（argparse 皮）+…, render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。, _sample_run(), test_render_text_annotates_shortcircuited_step(), test_render_text_nests_and_shows_cost_and_duration(), test_render_text_no_annotation_on_plain_failed(), test_render_text_shows_step_level_report_refs(), test_to_dict_shape_and_no_dollar() (+9 more)

### Community 35 - "ADR 0034 — Detached Batch Reconciler"
Cohesion: 0.26
Nodes (19): CLAUDE.md 项目约定, cli README（最薄前端/组合根皮）, CONTEXT.md 领域术语表, 执行核心库窄腰（概念）, 通用 step（QA 零代码的唯一载体）, Run 数据模型 Run⊃Job(=Scope)⊃Scenario⊃Step, 连锁失败读法（error → 后续 step 短路跳过）, core README（执行核心库窄腰） (+11 more)

### Community 36 - "FargateEngine"
Cohesion: 0.16
Nodes (12): FargateEngine, Event, fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…, 起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…, Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…, task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…, DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR…, 轮询 DescribeTasks 直到拿到确定的 exitCode——scope_done 后读退出码用（ADR 0024「事件流结束信号」）。… (+4 more)

### Community 37 - "run-scope.mts"
Cohesion: 0.08
Nodes (23): ADR-0014, ADR-0019, ADR-0020, ADR-0022, ADR-0024, ADR-0026, ADR-0027, ADR-0028 (+15 more)

### Community 38 - "compose.py"
Cohesion: 0.08
Nodes (32): build_cloud_stores(), build_fargate_engines(), is_botocore_error(), _make_ddb_table(), _make_ecs_client(), _make_lambda_client(), _make_s3_client(), _make_ssm_client() (+24 more)

### Community 39 - "run_scope.py"
Cohesion: 0.08
Nodes (29): ArtifactUploader, worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…, _attach_traj_refs(), _backoff_interrupted(), _collect_traj(), _cost_from_result(), _DeterministicCtx, _get_uploader() (+21 more)

### Community 40 - "preflight_cloud_resources"
Cohesion: 0.15
Nodes (16): preflight_cloud_resources(), fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…, _FakeDdbClient, _FakeEcsClient, _FakeLambdaClient, _FakeS3Client, _preflight_cap(), 跑一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。 (+8 more)

### Community 41 - "gherkai_runtime/names.py"
Cohesion: 0.13
Nodes (16): 资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…, subnet ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "subnets") 的便捷形式）。, sg ID 列表的 SSM 路径（= gherkai_runtime.names.ssm_path(prefix, "security-groups")…, ssm_security_groups_path(), ssm_subnets_path(), container_name(), default_name(), job_timeout_schedule_prefix() (+8 more)

### Community 42 - "0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器"
Cohesion: 0.20
Nodes (10): 0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器, 1. `TunnelProvider` 可插拔口子（`gherkai-runtime` 组合根共享层），首个实现 = ngrok, 2. URL 映射：feature 写原始地址，组装 job 时替换, 3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态, 4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）, 决策, 背景与问题, 被拒/被缓方案（护栏） (+2 more)

### Community 43 - "test_s3_report_store.py"
Cohesion: 0.19
Nodes (14): ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ReportStore, S3ReportStore 对拍测试（ADR 0030 决定六 / 0027 / 0029）：与 LocalReportStore 同一批行为断言，moto…, 把 write() 返回的 s3:// ResourceUri 取回对象正文（测试侧读内容用）。, _read_manifest(), _read_s3(), test_empty_report_refs_still_valid_index() (+6 more)

### Community 44 - "query_deterministic"
Cohesion: 0.09
Nodes (24): _ask_worker(), build_local_stores(), match_deterministic(), prune_empty_dirs(), Path, query_deterministic(), worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…, spawn 一次某引擎 worker 的**自述入口**、收一行 JSON（ADR 0036 决策 2/4 的共同机制）。 自述入口不建会话、不读 job、零… (+16 more)

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
Nodes (15): DeterministicAssertion, DeterministicConflict, DeterministicCtx, DeterministicHandler, DeterministicMeta, Entry, match, matchBatch() (+7 more)

### Community 54 - "{prefix}cluster + Fargate task definitions"
Cohesion: 0.50
Nodes (4): Worker ECR repositories, {prefix}cluster + Fargate task definitions, EventBridge rule {prefix}ecs-stopped, Per-engine task roles + shared execution role

### Community 55 - "project"
Cohesion: 0.11
Nodes (37): project(), 从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…, _exit(), _meta(), _passed_events(), 两件都要齐（scope_done ∧ exit=0）→ 终态取 scenario 归约（passed）。, 关键（机制二）：scope_done 说 passed，但 exit_code!=0 → 判 ERROR（防"发完 scope_done 又非0退出"误报）。, SIGKILL 截断 exit=137 → ERROR（实测 payload 带 137，机制二）。 (+29 more)

### Community 56 - "subprocess_engine.py"
Cohesion: 0.09
Nodes (21): _pump_log(), Event, 子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…, 逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…, 把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…, 一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。, 阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的…, Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。 (+13 more)

### Community 57 - "test_tunnel_cli.py"
Cohesion: 0.13
Nodes (22): _patch_tunnel(), Path, --expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。…, _tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。…, --ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。, plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。, --tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。, --tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮 即… (+14 more)

### Community 58 - "e2e_harness 使用说明"
Cohesion: 0.18
Nodes (13): ADR 0014 AI 断言投票, ADR 0024 worker↔core 协议 / 终止契约, ADR 0025 @scope: tag 分组, ADR 0029 产物→S3 / 边界抢传 / 固有残余, ADR 0032 Fargate 中断丢失量级 + 真容器 grace 校准, e2e_harness 使用说明, 边界抢传（act / scenario 边界）, grace 测量与 SIGKILL 兜底 (+5 more)

### Community 59 - "fargate_engine.py"
Cohesion: 0.13
Nodes (12): 云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 所有云端 adapter（存储侧…, 缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…, require_boto3(), DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态跑批的 EventLog——从 DDB events 表读全量重放 + 写…, Fargate Engine adapter（ADR 0024「远程传输演进」/ 0026 机制层）：在 ECS Fargate 上跑一个讲 ADR 0024…, S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。 把一次 run 的…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选… (+4 more)

### Community 60 - "test_sqlite_event_log.py"
Cohesion: 0.23
Nodes (12): _log(), SqliteEventLog 测试（ADR 0034 P3）：持久事件通道往返 + 与 project 联通。 存原始 JSON 行→读回解析成…, 退出记录走独立键空间（机制一）：不占 events 的 seq，records() 里 kind='exit'。, has_exit 只看本 scope 的退出记录（对位 DdbEventLog.has_exit）：worker 事件不算、别的 scope 不串扰。, exitCode 宽限态（None）可存（机制二兜底）。, 同 (scope,seq) 重写幂等（重放/重试无副作用，镜像 DDB PutItem 幂等）。, test_append_and_read_back_events(), test_append_idempotent_same_seq() (+4 more)

### Community 61 - "test_event_sink.py"
Cohesion: 0.09
Nodes (10): EventSink, 事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…, 按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…, 从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…, 吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…, EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…, DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。, test_ddb_mode_missing_run_or_scope_id_fails_loud() (+2 more)

### Community 62 - "build_push_workers.py"
Cohesion: 0.22
Nodes (12): _account_id(), build_push(), _ecr_login(), main(), Path, ECR repo 名 = {prefix}{engine}-worker（对齐 gherkai_runtime.names.task_def_name，见…, 跑一条命令；dry-run 只打印。失败即抛（subprocess.run check=True）——不吞错、让调用者见真况。, 取当前账户 id（拼 ECR registry host）。dry-run 时用占位符（不真调 AWS）。 (+4 more)

### Community 63 - "_mk_state"
Cohesion: 0.23
Nodes (12): _args(), _mk_state(), pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。, running → 不提示（在跑、正常）。退出码 0。, 终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。, --wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。, --json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。, test_render_status_json_no_hint() (+4 more)

### Community 64 - "0038. worker 镜像交付：基底、variant 与推送注册"
Cohesion: 0.11
Nodes (19): 0038. worker 镜像交付：基底、variant 与推送注册, `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）, `push-worker` 流程, SSM 参数与命名真源, 不变量, 与版本升级的交互, 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）, 多版本与多环境 (+11 more)

### Community 65 - "test_cloud_integration.py"
Cohesion: 0.17
Nodes (19): _ddb_store(), _is_ddb_too_large(), 云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…, 真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。, 真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。, 真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛…, 真 DDB（2026）空串行为的回归基线：finalize 写 ended_at=""（顶层标量 SET）、update 写 session_id=""…, 给真表/真桶造一个本次运行专属的 run_id，避免多次跑撞名（无随机源，用递增计数）。 跨进程靠 it- 前缀 + fixture… (+11 more)

### Community 66 - "JobSource"
Cohesion: 0.11
Nodes (9): JobSource, job 入口（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。 对称 Midscene 的…, 按注入的 env 读一个 scope 的 job。subprocess 态：json.loads(sys.stdin.readline())；S3…, 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 非空 → S3 态；无/空串 → stdin 态。 `or…, 读并解析一个 job（返回 dict，非流）。subprocess 态：stdin 首行 JSON（同步 readline、不等 EOF）。 S3…, s3://bucket/key → GetObject → json.loads。惰性建 client + 超时（对称…, JobSource 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态读 stdin 首行 JSON。 此前内联在…, s3://bucket(无 key 段)→ fail-loud(对称 midscene;放行会晚一步在 GetObject 报模糊参数错)。 (+1 more)

### Community 67 - "LocalRunStore"
Cohesion: 0.09
Nodes (17): RunStore adapters（ADR 0016）。当前只有 local；未来 ddb。, LocalRunStore, Path, 探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。, 在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新…, CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。, HWM 条件写 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。 **run 级 status 钳为…, 状态机单调条件写：仅当当前总 status 为非终态才写终态（机制三，commit 恰一次）。 (+9 more)

### Community 68 - "0036. 确定性能力暴露：worker 自述注册表，CLI 按引擎查询"
Cohesion: 0.10
Nodes (20): ADR 0018: 通用 step 能力清单, 抽象原语式通用 step, 确定性锚点原语（URL/DOM）, 两个引擎对称映射（提取路径对称）, 负向验证（该红能红）, AI 断言对措辞歧义敏感（已知风险）, ADR 0020: Step 措辞——默认 AI + 确定性锚点脚手架, 默认 AI 判断（裸 When/Then 无路由关键词） (+12 more)

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
Cohesion: 0.11
Nodes (20): href 相对化（local 相对 / cloud 恒等 ref）, index.html（判定明细树 + 产物导航）, LocalReportStore, manifest.json（薄信封 + report_index）, 被拒方案：materialize 产物拷贝, ReportRef {kind, ref, label}, ReportStore.write（整 run 一次写）, ResourceUri（带 scheme 的统一指针） (+12 more)

### Community 73 - "render.py"
Cohesion: 0.19
Nodes (13): _arg_hint(), _cost_bits(), _dispatch_hint(), _ms(), RunResult, 渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…, plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。 dispatch（可选，ADR 0036…, step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。 (+5 more)

### Community 75 - "test_project.py"
Cohesion: 0.18
Nodes (14): projected_run_status(), 平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。 **不是 worker 的 wire 事件**（不在…, 投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。…, TaskExited, gherkai_core.project 纯投影测试（ADR 0034）：project(records)→RunState 的「两件都要」谓词 + HWM…, 超时处置的 stop → ERROR，不论 exit_code 形态（SIGKILL 137 / 协作退 0 / 未落值 None—— None 平时是保守…, 归因 error_type="timeout"（对齐同步路径，[0031] 决定一）——即使内容完整（scope_done 都到了） 也以超时为根因、覆盖…, 全 job pending → pending（run 还没起过任何 job）；任一 job 推进 → running；恒非终态（终态归 finalize）。 (+6 more)

### Community 76 - "ecs_task_timing.py"
Cohesion: 0.33
Nodes (9): capture(), _delta_s(), _describe(), _ecs(), _iso(), main(), _print_human(), boto3 返回的 datetime → ISO 字符串（缺省 None）。 (+1 more)

### Community 77 - "RunPersistence 应用服务"
Cohesion: 0.22
Nodes (9): commit-point 写序（数据面先、控制面后）, DDB 单表 META/STATE 两 item, on_job_complete / on_event 回调（JobSink）, Store.preflight() 探活 + 退出码分层, ResultStore（判定真值、S3 后端）, RunPersistence 应用服务, RunState.jobs 改 Map<scope_id>, RunStore（create_run/update_job_state/finalize_run） (+1 more)

### Community 78 - "run-scope.test.mts"
Cohesion: 0.11
Nodes (11): _events, fakePage, importMod(), ADR-0014, ADR-0024, ADR-0028, ADR-0029, ADR-0031 (+3 more)

### Community 79 - "JobResult"
Cohesion: 0.10
Nodes (23): JobResult, 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有…, Event, 把单个 worker 事件归约进 JobResult（就地累积，ADR 0024/0026）。 **这是 `schedule._Worker._reduce`…, reduce_event(), _heartbeat_wrap(), Event, 单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。 (+15 more)

### Community 81 - "ADR 0003 Qwen3-VL on Bedrock 做 grounding"
Cohesion: 0.36
Nodes (8): ADR 0002 不用 Bedrock GPT-5.5, ADR 0003 Qwen3-VL on Bedrock 做 grounding, ADR 0004 Nova Act 纯 IAM 经 Workflow 鉴权, ADR 0008 Midscene SigV4 自签鉴权, ADR 0009 最大化使用 AWS 硬约束, ADR 0012 planning 复用 Qwen3-VL, 文档健康度复盘任务, SIGV4-FETCH-RECIPE 配方笔记

### Community 82 - "schedule._Worker._run_once"
Cohesion: 0.29
Nodes (8): EX_WORKER_NETWORK = 80 exit code, schedule._heartbeat_wrap (silent-worker timeout fix), ScheduleOpts (network_retry, retry_sleep), schedule._Worker.run (network retry loop), schedule._Worker._run_once, Session leak protection before exit, subprocess_engine._read_events, core.errors.WorkerNetworkError

### Community 83 - "main"
Cohesion: 0.24
Nodes (11): aggregate(), cumulativeTokens(), isTransientNetwork(), log(), main(), modelConfig(), runScenario(), runStep() (+3 more)

### Community 84 - "_TrajNova"
Cohesion: 0.33
Nodes (3): 带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。, _TrajNova, _TrajResult

### Community 86 - "test_detached_launcher.py"
Cohesion: 0.06
Nodes (51): datetime, LocalRunStore, now_iso(), parse_iso(), `now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…, **唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…, build_local_reconcile(), _paths() (+43 more)

### Community 87 - "SqliteEventLog"
Cohesion: 0.17
Nodes (9): Connection, Path, 某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。, 本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。, 追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。, 写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…, 单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。, 读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用… (+1 more)

### Community 88 - "ensure_workflow_definition"
Cohesion: 0.10
Nodes (25): Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…, worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…, ensure_workflow_definition(), Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…, 确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…, main(), A · 负向用例（expect-failure 探针）：验证"该红能红"——Nova Act 引擎。 对标…, 第二根穿刺针 · Nova Act 引擎 —— 对标 Midscene 引擎（ADR 0010 苹果对苹果）。 用例（与 Midscene 同）：打开… (+17 more)

### Community 90 - "ADR 0017: Cloud Execution — Fargate over Runtime"
Cohesion: 0.33
Nodes (6): ADR 0017: Cloud Execution — Fargate over Runtime, AgentCore Evaluations（LLM-as-Judge，被否）, AgentCore Runtime（长驻 agent 服务）, 批处理 workload shape（run-to-exit）, ECS RunTask / Fargate 执行后端, 15 分钟 idle-kill 计时器与保活 plumbing

### Community 92 - "_FakeEcs"
Cohesion: 0.15
Nodes (9): FargateWorkerHandle, 一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…, 请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…, _engine_with_fake_ecs(), _FakeEcs, 构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…, test_probe_task_not_stopped(), test_probe_task_stopped_but_exit_code_null() (+1 more)

### Community 93 - "echo_worker.py"
Cohesion: 0.60
Nodes (4): emit(), main(), _on_sigterm(), 测试用假 worker：读 stdin 的 job JSON，吐预设 ADR 0024 事件到 stdout。 不接任何真引擎——只验证子进程 adapter…

### Community 95 - "ArtifactUploader"
Cohesion: 0.17
Nodes (6): ArtifactUploader, ADR-0016, ADR-0024, ADR-0028, ADR-0029, ADR-0033

### Community 96 - "_SeqEcs"
Cohesion: 0.28
Nodes (7): _await_engine(), 按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。, _SeqEcs, _stopped_resp(), test_await_exit_code_null_beyond_grace_settles_as_error(), test_await_exit_code_null_then_nonzero_landed_preserved(), test_await_exit_code_waits_out_null_then_reads_landed_code()

### Community 97 - "权威信息源 REFERENCES"
Cohesion: 0.50
Nodes (4): 权威信息源 REFERENCES, AWS Bedrock / AgentCore 文档, Midscene 官方文档与源码 ground truth, Nova Act SDK 与 AgentCore provider

### Community 98 - "Midscene SigV4 自签 fetch 配方"
Cohesion: 0.50
Nodes (4): engines/midscene README, Midscene SigV4 自签 fetch 配方, createOpenAIClient 隔离 ModelConfigManager 坑, sigv4Fetch（最小手建请求签名）

### Community 99 - "test_submit_local_exits_2_when_worker_runtime_missing"
Cohesion: 0.18
Nodes (10): _miss(), 定位链全 miss 的结构化异常（带该引擎安装指引），仿 compose.resolve_worker_cmd 的抛出物。, run 的分叉：定位链 miss → 打安装指引 + 退 2，**且在 spawn/落库之前**——不进 job 级 engine_error…, submit local 同 run（per-run 进程在本机 spawn worker）：提交前退 2、不 fork、不落库——否则「提交成功」…, submit 侧同 run：解析一次写进 definition——per-run 进程/接力者从 definition 读回（**不**收 flag，…, test_list_deterministic_text_and_json(), test_run_exits_2_before_spawn_when_worker_runtime_missing(), test_submit_local_exits_2_when_worker_runtime_missing() (+2 more)

### Community 104 - ".project_state"
Cohesion: 0.50
Nodes (3): HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…, _lifecycle_rank(), 生命周期推进序（ADR 0034，仅用于 project 的单调合并、防态倒退）：pending < running < 任何终态。 与…

### Community 106 - "test_report_store.py"
Cohesion: 0.28
Nodes (22): LocalReportStore, ReportStore 的本地文件实现（组合根注入；S3 版只换落点/链接前缀）。, 原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…, ReportRef, _jr(), Path, LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。, 测试 helper：JobResult 持有 Job（definition）+ 判定字段。 (+14 more)

### Community 107 - "test_tunnel.py"
Cohesion: 0.20
Nodes (14): map_origin_in_jobs(), NgrokTunnel, 把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…, ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…, _fake_popen_writing_log(), tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…, 日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。, fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None=不写，覆盖超时路径）。 (+6 more)

### Community 108 - "_FakeEcs"
Cohesion: 0.14
Nodes (10): _FakeEcs, list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。, 仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…, 到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。, 退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。, task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…, test_handle_timeout_converges_directly_when_task_gone(), test_handle_timeout_noop_when_exit_in_flight() (+2 more)

### Community 109 - "_presend_act_siblings"
Cohesion: 0.27
Nodes (12): _presend_act_siblings(), act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的 配套…, _make_act_pair(), act 边界抢传单测（ADR 0029「act 边界抢传」，为 Fargate 预演——subprocess+cloud 先建好并验证）。 验…, 记录 to_report_ref 被调的路径（验抢传）；enabled 可控 no-op。, 造一对 act 产物（.html + 配套 _trajectory.json），返回 (html 路径, json 路径)。, _SpyUploader, test_presend_all_act_siblings() (+4 more)

### Community 110 - "package.json"
Cohesion: 0.14
Nodes (13): bin, gherkai-worker-midscene, description, engines, node, exports, homepage, license (+5 more)

### Community 111 - "DynamoDB stream event source mappings"
Cohesion: 0.67
Nodes (3): DynamoDB stream event source mappings, {prefix}events DynamoDB table, {prefix}runs DynamoDB table

### Community 113 - "S3ResultStore"
Cohesion: 0.19
Nodes (8): ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…, s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…, 把单个 JobResult 存成一个 S3 对象（写面，追加语义=同 key 覆盖，幂等）。, 读回单个 JobResult（按键取，无需查询）；不存在返回 None。, 读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…, 探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。, S3ResultStore, JobResult

### Community 114 - "test_lambda_handlers.py"
Cohesion: 0.07
Nodes (32): Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…, ② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…, 同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。, 构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。, Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…, 超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…, definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。, definition 声明 > cap → 钳到 cap：task 烧部署方账单，部署侧保留总量控制权（cap 语义）。 (+24 more)

### Community 119 - "deterministic_steps.py"
Cohesion: 0.40
Nodes (4): deterministic, 确定性锚点脚手架（ADR 0020/0022）—— **本包内建**的示范锚点，随 worker 发行。 用途：少数"必须精确、不容 AI 抖动"的断言（如…, 确定性 URL 断言：当前页 URL 须匹配给定正则（精确、不走 AI）。 .feature 写法（test engineer 约定的带关键词措辞，与 QA…, url_matches()

### Community 120 - "tunnel.py"
Cohesion: 0.14
Nodes (14): _gen_auth(), make_tunnel(), Exception, 隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…, 按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。, 隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。, 一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。, 替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——… (+6 more)

### Community 124 - "agentcore-sigv4.mts"
Cohesion: 0.21
Nodes (11): BASE_URL, main(), ADR-0033, getBaseUrl(), getRegion(), MODEL, modelSigner_(), ADR-0033 (+3 more)

### Community 126 - "deterministic.py"
Cohesion: 0.18
Nodes (12): clear(), DeterministicConflict, _Entry, _hits(), match_batch(), Exception, 确定性 step 注册表（ADR 0022）——Nova 引擎。 test engineer 用 `@deterministic(pattern)`…, 批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与… (+4 more)

### Community 127 - "_FakeResult"
Cohesion: 0.14
Nodes (7): _aggregate(), _FakeResult, _Meta, _NavErrorNova, 模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…, go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。, test_run_scenario_shortcircuits_after_error()

### Community 129 - "_det_feature"
Cohesion: 0.17
Nodes (12): _det_feature(), plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。, 冲突预检（真跑将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。, 标注 best-effort：引擎环境未装/查询失败 → 无标注 + stderr 警告，plan 核心输出不受影响。, plan 的分叉与 run/submit **相反**（ADR 0037 决策 3 明示 + ADR 0036 决策 4）：保持 best-effort…, 三个自述入口同样加载 steps 目录（ADR 0037 决策 4）→ plan 标注与 list-deterministic 清单反映定制 step。, test_plan_and_list_deterministic_pass_steps_dir_to_worker(), test_plan_annotates_deterministic_hits() (+4 more)

### Community 132 - "tunnel_host.py"
Cohesion: 0.20
Nodes (9): gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…, 隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…, 隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。, 起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…, start_tunnel_for_jobs(), TunnelSetup, provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。, test_start_tunnel_for_jobs_maps_and_injects_headers() (+1 more)

### Community 135 - "分发与打包施工进度总纲（ADR 0037 / 0038 落地）"
Cohesion: 0.33
Nodes (6): 关键中间结论 / 待办, 决定记录（施工中拍的、不改 ADR 的实施细节）, 分发与打包施工进度总纲（ADR 0037 / 0038 落地）, 当前状态, 施工次序（0037「落地次序」，此处只记进度）, 阶段 1 的批次

### Community 136 - "user_steps.py"
Cohesion: 0.20
Nodes (11): _ensure_ns_package(), _is_step_file(), _module_name(), Exception, Path, 加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…, 使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…, 文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅… (+3 more)

### Community 137 - "stop_tunnel"
Cohesion: 0.29
Nodes (7): cleanup_tunnel(), 收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。, 收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。, stop_tunnel(), **真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…, test_ngrok_agent_detaches_from_cli_process_group(), test_stop_tunnel_idempotent_on_dead_pid()

### Community 139 - "resolve_cloud_target"
Cohesion: 0.24
Nodes (10): CloudTarget, 一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…, 无状态跑批事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序＝链上顺序。, 把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…, resolve_cloud_target(), _clear_aws_env(), test_resolve_cloud_target_default_prefix_when_nothing_given(), test_resolve_cloud_target_derives_all_names_from_prefix() (+2 more)

### Community 140 - "_runs_stream_record"
Cohesion: 0.40
Nodes (5): ① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。, Stream records + 直接 run_id 并存时都提取（健壮）。, _runs_stream_record(), test_starter_run_ids_both_sources(), test_starter_run_ids_from_runs_stream()

### Community 142 - "test_interrupt_model.py"
Cohesion: 0.11
Nodes (22): _emit_scenario_done_unless_stopped(), scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。…, scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。 返回 True＝中止（调用方应停止本…, _run_scenario(), _FakeResult, _Meta, flag-only 中断模型单测（ADR 0024 终止契约）。 锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM…, 记录 act/act_get 收到的 timeout；act_get 按布尔序列回。 (+14 more)

### Community 143 - "_FakeSink"
Cohesion: 0.17
Nodes (7): captured(), _FakeSink, fixture, 每个用例前后清 _stop（模块级单例，避免用例间串扰）。, 假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。, _reset_stop()

### Community 147 - "_stream_record"
Cohesion: 0.15
Nodes (13): scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。, 同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…, 对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。, 推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…, 同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。, _stream_record(), test_reconciler_noop_for_non_detached_run(), test_reconciler_ticks_detached_run() (+5 more)

### Community 148 - "cloud_env"
Cohesion: 0.67
Nodes (3): cloud_env(), fixture, moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。

### Community 149 - "_FakeSink"
Cohesion: 0.18
Nodes (5): captured(), _FakeSink, fixture, 假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…, 假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。

### Community 150 - "JobSource"
Cohesion: 0.22
Nodes (4): Job, JobSource, ADR-0016, ADR-0024

### Community 151 - "user-steps.mts"
Cohesion: 0.25
Nodes (8): collectStepFiles(), loadUserSteps(), LoadUserStepsDeps, ADR-0016, ADR-0028, ADR-0036, ADR-0037, STEP_EXTS

### Community 157 - "plan_next"
Cohesion: 0.17
Nodes (13): plan_next(), 据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…, _ev(), 全 pending、max_concurrency=2 → 提议 start 前 2 个。, 已有 1 个 running、max_concurrency=2 → 只补 1 个 pending。, 有 running 时不 finalize（即使有别的 pending 也优先补并发、不收尾）。, 会话已起（scope_started）、进程还没终止（无 task_exited）→ RUNNING（在跑）。, 干净退出（exit=0）却没发完 scope_done（内容不完整）→ ERROR（矛盾态，不死循环，P3b crash 修正）。 (+5 more)

### Community 160 - "05-negative-assertions.ts"
Cohesion: 0.29
Nodes (6): BASE_URL, Check, main(), MODEL_CONFIG, REGION, ADR-0033

### Community 161 - "argument.mts"
Cohesion: 0.43
Nodes (6): argumentText(), buildInstruction(), cleanCell(), ADR-0024, StepArgument, unquote()

### Community 162 - "user-steps.test.mts"
Cohesion: 0.29
Nodes (4): BIN, ADR-0036, ADR-0037, TSX_LOADER

### Community 163 - "WorkerNotFoundError"
Cohesion: 0.33
Nodes (4): 定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退码交调用点。 **继承 RuntimeError…, 定位链 miss 的引擎腿（`build_engines` 的兜底，ADR 0037 决策 3）：一用即抛 WorkerNotFoundError。…, _UnavailableEngine, WorkerNotFoundError

### Community 173 - "01-model-sigv4.ts"
Cohesion: 0.40
Nodes (5): BASE_URL, main(), makePng(), REGION, ADR-0033

### Community 183 - "bin.mts"
Cohesion: 0.33
Nodes (5): fromSource, hookSpec, ADR-0024, ADR-0028, ADR-0037

### Community 184 - "devDependencies"
Cohesion: 0.40
Nodes (5): devDependencies, @types/node, typescript, @types/node, typescript

### Community 187 - "artifact-upload.test.mts"
Cohesion: 0.50
Nodes (3): mkLogDir(), ADR-0029, tmproot()

### Community 190 - "iac_aws_backend README"
Cohesion: 0.50
Nodes (4): ADR 0016 — Composition Root Shared Layer, ADR 0024 — Synchronous Run Query Polling, iac_aws_backend README, VPC/subnets/security-groups + SSM parameters

### Community 191 - "files"
Cohesion: 0.50
Nodes (4): files, dist, LICENSE, README.md

### Community 192 - "repository"
Cohesion: 0.50
Nodes (4): repository, directory, type, url

### Community 193 - "index.mts"
Cohesion: 0.50
Nodes (3): ADR-0022, ADR-0036, ADR-0037

### Community 196 - "test_compose.py"
Cohesion: 0.11
Nodes (24): engine_min_grace(), 把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…, 按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…, resolve_region(), midscene_env_cmd(), novaact_env_cmd(), _preflight_report_dir(), fixture (+16 more)

### Community 197 - "scripts"
Cohesion: 0.67
Nodes (3): scripts, build, test

### Community 200 - "_isolate"
Cohesion: 0.67
Nodes (3): _isolate(), fixture, 注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。

## Ambiguous Edges - Review These
- `通用 step（QA 零代码的唯一载体）` → `ADR 0019 用 Gherkin tag 声明 scope 与 engine`  [AMBIGUOUS]
  CONTEXT.md · relation: conceptually_related_to

## Knowledge Gaps
- **295 isolated node(s):** `现状实测（本 ADR 的证据基座，均可复现；施工后成为历史快照）`, `业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）`, `决策总览`, `决策 1：交付物按打包技术划分，worker 运行时是硬核`, `2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条` (+290 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **79 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `通用 step（QA 零代码的唯一载体）` and `ADR 0019 用 Gherkin tag 声明 scope 与 engine`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Job` connect `Job` to `CloudLauncher`, `ScopeStarted`, `test_plan.py`, `tunnel_host.py`, `RunState`, `test_schedule.py`, `test_cloud_reconcile.py`, `test_conditional_writes.py`, `test_reconcile.py`, `test_fargate_engine.py`, `JobState`, `RunPersistence`, `model.py`, `StepResult`, `FargateEngine`, `fargate_engine.py`, `test_sqlite_event_log.py`, `test_cloud_integration.py`, `test_project.py`, `JobResult`, `test_detached_launcher.py`, `_FakeEcs`, `_SeqEcs`, `test_report_store.py`, `test_tunnel.py`, `_FakeEcs`, `tunnel.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `core 测试说明（单测 + 集成测试）` connect `S3StepArgumentOffloader` to `test_cloud_integration.py`, `ADR 0034 — Detached Batch Reconciler`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `ADR 0030: 实时写存储接缝` connect `ADR 0034 — Detached Batch Reconciler` to `ADR 0027: RunReport 跨引擎归集索引`, `RunPersistence 应用服务`, `S3StepArgumentOffloader`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `Job` (e.g. with `CloudLauncher` and `FargateEngine`) actually correct?**
  _`Job` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `RunMeta` (e.g. with `_cmd_run()` and `_cmd_submit()`) actually correct?**
  _`RunMeta` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `RunState` (e.g. with `_cmd_submit()` and `_mk_state()`) actually correct?**
  _`RunState` has 24 INFERRED edges - model-reasoned connections that need verification._