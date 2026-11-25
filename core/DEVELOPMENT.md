# core 包 —— contributor 文档

同目录的 [`README.md`](./README.md) 是发行包的入口页（逐字发布到 PyPI，只保留定位 / 安装方式 / 最小用法与外链），使用者的用法见 [`docs/user-guide/`](../docs/user-guide/README.md)；本文件面向修改本包的 contributor，不进发行包。

发行名 `gherkai-core` / import 名 `gherkai_core`（ADR 0037 决策 2a「三名分离」）。

窄腰：解析 `.feature` → 分组 scope → 调度 → 收集结果。**零引擎依赖**：核心不 import Midscene / Nova Act，
引擎运行在 worker 子进程中，经 worker↔core JSON 协议与核心通信。

设计见 ADR：
- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / Run 数据模型 / ports
- [0024](../docs/adr/0024-worker-core-protocol.md) worker↔core 协议
- [0025](../docs/adr/0025-plan-module-feature-to-jobs.md) plan 模块（解析 + scope 分组）
- [0026](../docs/adr/0026-schedule-module.md) schedule 模块（并发调度）
- [0027](../docs/adr/0027-runreport-aggregation-index.md) RunReport 归集索引
- [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝 / [0031](../docs/adr/0031-job-lifecycle-states-and-severity.md) job 生命周期态 + severity
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态批量运行 core 侧拆分（project 纯归约投影 + reconcile 推进编排 + event_log 持久事件通道）
- [0048](../docs/adr/0048-test-targets-device-and-ui-kind.md) 测试目标模型（Target / `@device` / `@app`、定义层校验）
- [0051](../docs/adr/0051-device-session-lifecycle-and-app-distribution.md) 远程访问会话生命周期（会话事件、终结四阶段、设备计量与 evidence）
- [0054](../docs/adr/0054-run-deadline-lifetime-lock-and-settling.md) 运行期限、生命期锁与 run 处置（期限规则 `run_deadline`、生命期锁、处置方的试拿、清理暂存目录与报告目录的边界检查 `adapters/run_store/run_dir`、run 级终态不可变、执行方先认领再启动）

## 模块

```
core/gherkai_core/
├── model.py      ← 领域模型：Job / Scenario / Step / 9 类事件（含 step_skipped 短路与 session_opened / session_closed：桌面与设备 job 的 worker 都为每个会话成对发出，ADR 0051 决策 4）/ 判定明细 JobResult→ScenarioResult→StepResult 与从记录组装的 run 结果 RunResult（每个 job 一个 JobOutcome：状态取运行态、有明细的附上明细）/ RunMeta（definition，含 worker_variant·worker_task_defs，ADR 0038）/ Status 七态 / ResourceUri（纯数据）
├── parse.py      ← .feature → 领域模型（基于 gherkin-official Compiler；该库封装在此 seam 之后）
├── scope.py      ← tag 分组 + engine / 测试目标 / timeout 校验 → Job[]；对外 plan(features, config, *, select=None) -> Job[]（select 是 `--scope/--tags/--scenario` 的筛选谓词，筛选只缩小要运行的范围、不增不改，ADR 0041 决策一）；组装之后核一个 run 的规模上限（job 数 `MAX_JOBS_PER_RUN`、scope 与 scenario 标识的字节数 `MAX_ID_BYTES`，两个常量在 model.py，ADR 0025「一个 run 的规模上限」）
├── target.py     ← 测试目标的定义层结构校验 validate_job_definition：字段成对、非空、类型与合法组合；组合根写 definition 之前与推进器读 definition 时各校验一次，违约时抛 DefinitionContractError（ADR 0048 决策 3）
├── serialize.py  ← 领域模型↔dict 的单一序列化真理源（store adapter 复用，ADR 0016/0027）；记录里的时刻（ISO 串）与带时区 datetime 之间的唯一一份解析与写法 instant_from_iso / instant_to_iso；记录「读不出」（内容解析不了）的口径 UNREADABLE_RECORD_ERRORS，列举 run 与处置共用；运行态顶层与 job 条目的模型键集 RUN_STATE_KEYS / JOB_STATE_KEYS，两个 RunStore adapter 据它们分出不认识的键
├── wire.py       ← Job→JSON（core 发给 worker）与 JSON→0024 事件（worker 发回 core）的单向线序列化 + 退出码约定 EX_WORKER_NETWORK/raise_for_worker_exit（子进程 adapter 用它翻译 worker 的退出码，ADR 0028「关键不变量:退出码携带 network 信号」、ADR 0024「字段语义」的退出码约定）；worker↔core 协议的实装处，事件字段的违约（含进运行态的三处 sessionId 的类型与 `MAX_SESSION_ID_BYTES` 长度上限，ADR 0024 sessionId 条）在 event_from_json 一处以 ValueError 报出
├── errors.py     ← core 类型化异常：WorkerExitError（worker 子进程非零退出，带原退出码，ADR 0028「关键不变量:退出码携带 network 信号」；云端的退出码不经它，缺退出码时的平台侧哨兵由退出观察者落，ADR 0034 机制二「退出码缺失」条）及其子类 WorkerNetworkError（network_error 重试分类，ADR 0028）；另有三个 ValueError 子类：UnsupportedDefinitionSchema（definition 结构版本不符，ADR 0037 决策 7）/ DefinitionContractError（definition 结构违约，ADR 0048 决策 3）/ FeatureContractError（feature 写法与配置违约，parse/scope 共用，ADR 0019/0025）；以及 RuntimeError 子类 RunAlreadyEnded（前台收尾时 run 已被别处记为已结束，带读回的运行态、读回失败时为空，ADR 0054 决策五）；FileExistsError 子类 RunAlreadyExists（建 run 时 run 已存在：本机是暂存目录改名成 run 标识时目标已是非空目录，云端是 META 或 STATE 条目已在；调用方判断「run 已存在」只认这个类型，ADR 0054 决策五）；FileNotFoundError 子类 NamedDetailMissing（运行态点名的那一份判定明细读不到，或读到的不属于这个 job；它是 OSError，前台由此落进运行期读写记录失败的出口，ADR 0030 决定三「点名」条）
├── ports.py      ← Engine / WorkerHandle / EngineResolver / Sink / JobSink / RunRecord / RunStore / ResultStore / ReportStore 接口（组合根注入；RunRecord 是调度循环服从记录的认领、重试之前的读与停手信号，ADR 0054 决策五）；**另两个 port（`EventLog` / `Launcher`）定义在 `reconcile.py`**，只服务无状态推进路径（ADR 0034），清点注入面时须同时查看两处，理由见 `ports.py` 模块头
├── schedule.py   ← schedule(run_meta, engines, sink, opts, on_job_complete?, on_event?) -> Execution（同步 run：并发/隔离/超时/优雅停；墙钟与 RunRecord 经 ScheduleOpts 注入，遵守运行期限（ADR 0054 决策二），起 worker 之前先认领、发现 run 已被别处结束即停手（ADR 0054 决策五）；返回执行事实：判出结果的 job、余下的 job 不再启动的来源（停止启动与中止标志登记在一处、只记第一次）与整体墙钟，不含 run 级状态，ADR 0026「接口」）
├── project.py    ← 无状态批量运行纯归约投影（ADR 0034「core 拆分」节）：project(meta, records, baseline)→RunState（照常给出事件推出的各 job 状态、含终态，供 tick 判断哪些 job 已有结果；投影写由两个 RunStore adapter 钳在 running）+ project_full(meta, records, *, claimed_at)→[JobResult]（写 job 终态用：tick 只交给它这一轮要写终态的 job 的记录，给出它们的判定明细；截止时刻由各 job 的认领时刻、预算与期限重算，起作用的是预算记 error 加 timeout、是期限记 aborted，退出记录带超时标志或退出时刻晚于截止时刻的按到点处理（`project` 在基线里读得到认领时刻时用同一条规则），缺认领时刻即报错、仍非终态即抛 NonTerminalSnapshot；不给 run 级状态）+ plan_next(state, max_concurrency, *, past_stop_start)→actions（start / expire；state 是这一轮读到的运行态加上这一轮终态写的作用、按运行定义的次序，不读事件；已过停止启动的时刻不提议启动，没有执行中的 job 而仍有 pending 时提议到期的结束写（ADR 0054 决策二后台推进条「决策」）；零个 job 的 run 没有任何动作）+ reduce_event 与 finalize_job（终结函数与真值表，ADR 0034 机制二；与 schedule 共用同一份归约与终结判定）+ assemble_run_result（从运行态与判定明细组装 RunResult 的唯一一处：前台收尾、`--no-report` 与后台报告共用，ADR 0027「RunResult 的组装只有一处」条）、run_totals（run 级合计，只经它调用）与 run_duration_ms（后台由运行态的起止算 run 级墙钟）
├── run_deadline.py ← 运行期限的规则（ADR 0054 决策二）：停止启动的提前量 60 秒、是否已过停止启动的时刻与期限、job 截止时刻（认领时刻加预算与期限取较早者，两者相等时算预算）；期限加 300 秒 overdue_at 与是否已过它的判断 past_overdue（处置条件之一，ADR 0054 决策六）；到期的说明在 run_status 的说明表；墙钟时刻在 core 里是带时区的 datetime。期限的算式在 runtime 的 `gherkai_runtime.deadline`
├── run_status.py ← run 的状态只由 job 的终态算出（ADR 0031 决定三）：取法 run_status_of；按本格式的模型算出的结束写的说明表 RunEnding / RUN_ENDINGS（各条来路的句子只在这里，结束不结束执行中的 job 是每一行的结构字段 ends_running_jobs）；结束写的 error 变体的几句原因 schema_mismatch_reason / DEFINITION_CONTRACT_REASON / NO_WORKER_IMAGES_REASON 同样在这里，只有云端推进器用，交给 DDB adapter 的 end_run_as_error（error 变体不经本模块的作用函数）；两种使 job 成为终态的写对运行态的作用 ending_applied / commit_applied 与终态写的三种结果 CommitOutcome，两个 RunStore adapter 共用（ADR 0030 决定四）；余下的 job 不再启动的来源 StopSource；没有记录的执行在内存里算运行态的 state_without_record；执行中的写的参数校验 check_running_write
├── reconcile.py  ← 无状态批量运行推进编排（ADR 0034「core 拆分」节与机制三②）：`EventLog` / `Launcher` 两个 port 在此定义（与消费它们的推进器同处；`EventLog` 只有推进步骤用到的两个方法：读全量 `records`，与覆盖同键、可带退出时刻的 `record_exit`；云端超时处置的点查与条件补写直接用 `DdbEventLog`，不在协议上）+ tick(run_id, meta, event_log, run_store, launcher, max_concurrency, *, clock, result_store) -> TickOutcome（继续推进 / 这一方的写使 run 成为终态 / run 已结束而使它成为终态的不是这一方，宿主据此决定是否继续与是否写报告；不交回判定明细，ADR 0034 机制三「run 级状态只进不退」条④；判定存储必传）：时刻经注入的时钟取；先读运行态，读不到即继续推进、已收尾即停止推演；投影写只交这一轮读到的运行态里未结束的 job（ADR 0034 机制三「逐 job 写：内容不变不写，注定不成立的不发」段）；幂等、多触发源、CAS/HWM 条件写；每一轮按逐 job 写序为已有结果、带认领时刻的 job 各生成一个标识、先存判定明细，再以一次 commit_job_states 记下它们的终态并点名各自的那一份（ADR 0030 决定三「点名」条），随后才在这一轮读到的运行态加上终态写的作用上做推进决策（步骤见 ADR 0034 机制三「收尾各步的先后与之后会不会变」）：已过停止启动的时刻不再认领（ADR 0054 决策二），满足到期的条件即做结束写 end_run；启动 job 经注入的 Launcher（core 不 import boto3），截止时刻随启动交出 + generate_report_from_record(run_id, meta, run_store, result_store, report_store, *, created_at)（按传入的 run 标识读运行态、按点名的标识读回各 job 的判定明细（named_details.load_named_details）、组装 RunResult、写 RunReport；任何失败原样抛出、不记日志，处置方据此给出报告是否生成，ADR 0054 决策七「报告」）+ write_report_from_record(meta, run_store, result_store, report_store, *, created_at)（tick 返回这一方使 run 成为终态之后宿主经它调用上一个，按 meta 里的标识；整段失败隔离，被点名的那一份读不到时同样只记一条警告、不生成报告；云端推进器 Lambda 与本机后台推进进程两个宿主共用）
├── persist.py    ← RunPersistence：编排 Store ports 随进度实时落库（逐 job 的提交点：生成标识、先存明细，再以 commit_job_states 写这个 job 的终态并点名那一份，ADR 0030 决定二、决定三；保存连同本机判定存储的退避重试都在落库服务的锁内）；实现 RunRecord（认领并记住认领时刻、此后的 job 状态写带上它，重试之前的读，三处发现汇成的停手信号；停手信号成立之后不存明细、不写终态）；finalize(execution)：本进程的终态写没有使 run 成为终态时按执行事实里的来路做结束写 end_run，本进程使 run 成为终态之后读一次运行态、按点名的标识读回各 job 的判定明细（不用本进程内存里的那一份）、组装 RunResult、写报告，返回 FinalizedRun；run 已被别处结束时不覆盖、不写报告、抛 RunAlreadyEnded（ADR 0054 决策五）；result_without_record 给没有记录的执行（`--no-report`）按同一组作用在内存里组装
├── named_details.py ← 判定明细的点名（ADR 0030 决定三「点名」条）：new_result_id（一次保存一个标识，16 个小写十六进制字符）与读者共用的唯一读法 load_named_details（只读运行态里带标识的 job，按标识取那一份并核对它的 scope_id；被点名而读不到或对不上时抛 NamedDetailMissing）；前台收尾、后台报告与 explain 都经它
├── redact.py     ← 凭据脱敏三条规则（URL userinfo、封闭名单的签名类查询参数与隧道令牌、Device Farm 端点的路径令牌；worker 日志转发、事件解码、CLI 出口共用，ADR 0035 决策 5）；用例与两个 worker 的同文实现共用 `engines/fixtures/redaction-cases.json`
├── termcolor.py  ← 终端颜色开关的统一策略（`NO_COLOR` / `FORCE_COLOR` / `TERM=dumb` / 目标流是否终端）；worker 日志前缀与 runtime 的 textui 共用，ADR 0047
├── device_session.py ← 远程访问会话的呈现辅助：一行设备描述、会话 ARN 对应的 Device Farm 控制台链接；纯函数，报告入口页与 cli 的 render 共用（ADR 0051 决策 8）
└── adapters/
    ├── subprocess_engine.py        ← Engine 实装（local）：spawn worker 子进程 + 读事件流
    ├── fargate_engine.py           ← 云端执行 adapter `FargateEngine`：`start_scope` 以 RunTask 启动 Fargate 容器（task-def 恒为组合根注入的**显式 revision ARN**、绝不 family 名，ADR 0038），job-in 经 S3、events-out 经 DDB（ADR 0024/0032），fire-and-forget，经 `cloud_launcher.py` 接入后台推进（ADR 0034「Engine port 演进」节）；只有 `start_scope`，不读事件、不判退出码
    ├── cloud_launcher.py           ← 无状态批量运行 cloud Launcher（ADR 0034）：经 resolver 选 FargateEngine，调 start_scope 启动 task（fire-and-forget）；起 task 之前把 tick 交来的截止时刻经 `TimeoutWatch.arm(run_id, scope_id, at)`（协议在此定义，实现在 deploy_aws）交给到点触发器，武装失败不阻塞启动
    ├── event_log/{sqlite,ddb}.py   ← 持久事件通道（ADR 0034）：local=SQLite / cloud=DDB events 表，reconciler 从此处全量重放推演；退出记录带退出码、超时标志、原因与退出时刻，DDB 一侧另有云端超时处置用的点查与条件补写（`attribute_not_exists`）；本机库的路径长度上限 `sqlite.DB_PATH_MAX_BYTES`（SQLite 缺省构建的库文件路径上限，报告目录的长度上限由它推出，ADR 0030 决定四「报告目录的路径长度」条）；本机库自 ADR 0042 决策七起同步 run 也写，explain 从两种库补取被中止 job 的 step 记录
    ├── event_log/recording.py      ← 原始事件行记录器（ADR 0042 决策七）：make_raw_sink（一个 scope 的逐行落库回调，runtime 的 SubprocessLauncher 与同步 run 共用）+ EventRecordingEngine（组合根为同步 run 的 SubprocessEngine 加一层包装，把事件行与退出记录旁路落 SqliteEventLog，Engine port 形状不变、schedule 不知情）
    ├── _boto.py                    ← 云端 adapter 共享的 boto3 依赖守卫（boto3 缺失时给出可读报错，ADR 0016 窄腰）
    ├── _atomic.py                  ← 本地 adapter 共享的原子落盘（同目录 tmp + `os.replace` + 显式 mode）：run_state.json / jobs/*.json / 报告三面都有真实并发读者，truncate-then-write 会使读者读到空文件
    ├── run_store/{local,ddb}.py    ← RunStore：本地文件 + DynamoDB（+ jobs_object.py：云端提交记录的 jobs 部分整份是产物桶 definitions/ 下的一个对象，头留在 runs 表；+ 条件写 try_claim_job/project_state（ADR 0034 机制三；ADR 0030 决定四），project_state 只前进、不越过 running、不写 job 终态，只在把某个 job 写成 running 时连带写 run 状态；+ 终态写 commit_job_states 与结束写 end_run，对运行态的作用取自 run_status，DDB 以写入序号为条件整体替换 jobs，改变了 jobs 或 run 状态的写才把写入序号加一（投影的标量一步只写 HWM、不加，投影的逐 job 写只在内容与库中不同时写成），ADR 0030 决定四、决定六；+ 结束写的 error 变体 end_run_as_error 只在 DDB adapter 上、不在端口上，只读写运行态的公共部分、读到的条目原样复制，公共部分读不出抛 RunStateUnreadable（三个整体替换 jobs 的入口读到的写入序号不是整数时同样抛它），ADR 0030 决定四；+ create_run 只在 run 不存在时成立、run 级终态不可变、update_job_state 返回 run 级在这次写时是否仍未结束、本机建 run 之后的各写入口在同一把文件锁内，ADR 0054 决策五；+ 本机 create_run 经 run_dir 建 run（先写进暂存目录、写完改名成 run 标识，不取运行态的短锁），`LocalRunStore` 构造时注入生命期锁的持有者 `lock_holder`，不带的 store 不能建 run；列举与按标识的读写都不认以点开头的名字，读到「不存在」即这个 run 不存在、不先查是否存在再打开，ADR 0030 决定四；+ 本机专属、不在端口上的 probe_run_dir / staging_names / sweep_staging_dir，把报告目录交给 run_dir；+ update_job_state 只收 running、库中没有这个 job 或它已是终态时不写、run 已结束时写不成（DDB 只发一次写，逐属性写条目里的模型键、这次没有值的删去），终态写与库中条目按字段合并，ADR 0030 决定四；+ project_state 的逐 job 写不改写库中已是终态的 job，DDB 的逐 job 写另以 HWM 为条件；+ 改写运行态时原样保留不认识的部分：本机顶层与 job 条目一级（按 scope_id）的附加键带回，DDB 整体替换 jobs 的两个按模型的写入口把读到的条目里不认识的属性并进去，模型键集登记在 serialize 的 RUN_STATE_KEYS / JOB_STATE_KEYS，ADR 0030 决定四；+ 认领计数（只作 status --json 的诊断键，不作任何写的条件），ADR 0034 机制三「run 级状态只进不退」条①；+ STATE 顶层 worker_task_def_arns，供清理 pass 的「运行中 run 引用检查」使用，ADR 0038）
    ├── run_store/run_dir.py        ← 本机 run 目录的存储形态（ADR 0030 决定四，ADR 0054 决策三、四）：名字规则 is_run_name（读写两侧共用，以点开头的名字留给暂存目录）；暂存目录名字的形态 staging_name / is_staging_name（前缀加 16 个小写十六进制字符，建 run 的一方与清理方共用这一处定义）；建 run 的 create_run_dir（先对报告目录做一次边界检查，再建暂存目录、以只读方式打开，对这次打开的描述符做边界检查、取排他的 flock，核对名字仍指向它，写记录，原子改名成 run 标识，把描述符交给持有者；暂存目录建不出、打开时已不存在、已被别的进程持有或拿到锁之后名字已不指向它时换名，至多 `STAGING_ATTEMPTS` 次）；持有者协议 LockHolder 与生产用的 HoldUntilExit（不关闭也不交出描述符，锁随进程退出释放）；边界检查 check_report_dir / check_existing_dir / check_fd（对打开的目录的描述符取文件系统类型 filesystem_type，只放行 `ALLOWED_FILESYSTEMS` 里本平台的类型，判断结果是 BoundaryCheck）；取锁与核对的原语 try_lock / same_dir；处置方的试拿 probe_run_dir（打开 run 目录、对这次打开做边界检查、不阻塞地试拿、持有到块结束，结果是 RunDirProbe；打开得到「不存在」抛 RunDirGone，别的打开失败原样抛出，ADR 0054 决策三「结果的判读」）；清理暂存目录 staging_names / sweep_staging_dir（打开、边界检查、试拿、核对名字仍指向打开的目录，过了才持着锁删去；结果是 StagingSweep，已不是暂存目录时为 None）；本机 adapter 特有的异常 RunDirRejected / LifetimeLockUnavailable（OSError 子类）/ StagingContended / RunDirGone，不放 errors.py
    ├── result_store/{local,s3}.py  ← ResultStore：本地文件 + S3（每次保存一份，文件名或键只由写入方给的标识构成，用哪一份由运行态点名；端口不提供列举，ADR 0030 决定三「点名」条）
    ├── result_store/retrying.py    ← RetryingResultStore：本机推进器的判定存储，在本地文件存储外面套保存失败的退避重试（只对 OSError，按 1、2、4 秒、同一个标识，读与探活原样转交）；由 runtime 的 `compose.local_result_store` 装配，云端不套（ADR 0030 决定三「保存明细失败」条）
    └── report_store/{local,s3}.py  ← ReportStore：本地文件 + S3（manifest+index）
```

各 `__init__.py` 无逻辑，只有包说明与 re-export：`event_log/` 两个实装与 `recording.py` 的 `EventRecordingEngine` / `make_raw_sink` 都 re-export；`run_store/` / `result_store/` / `report_store/` 只 re-export local 类，云端类由消费方按模块路径直接 import。四个子包口径不统一是排版惯例、**不是** import 期约束（云端模块顶层都不 import boto3，守卫在 `_boto.py`），理由见各 `__init__.py` 的 docstring。

云端 adapter（DDB/S3）行为对拍 local，moto 全程 mock 单测（ADR 0030 决定六）；boto3 是可选依赖 `gherkai-core[aws]`（库消费者按需安装；CLI 发行包 `gherkai` 硬依赖 `gherkai-runtime[aws]`，安装它即带入 boto3，ADR 0037 决策 2c）。
组合根按 `--backend {local,cloud}` 注入对应的一套 adapter（装配逻辑在产品本体 `runtime/gherkai_runtime/compose.py` 的 `build_local_stores` / `build_cloud_stores`，cli / Lambda / 未来 WebUI 共用；ADR 0016「演进」节 / 0030 决定七）。

## 运行测试

```bash
uv run pytest -q core/tests   # 仓库根：只运行本包单测
uv run pytest                 # 仓库根：运行全部 workspace 成员（core/runtime/cli/engines/novaact/deploy_aws）
```

根 `pyproject.toml` 的 `addopts` 带 `-m 'not integration' --timeout=60`：标记为 `integration` 的用例默认 deselect
（需连真实 DDB/S3 时，须显式 `-m integration` 并设 `AWS_DDB_TABLE` / `AWS_S3_BUCKET`），60s 超时用于防止用例挂死。
云端 store adapter 的真表/真桶集成测试与一次性建表建桶命令见 [`tests/README.md`](./tests/README.md)。
本机建 run 的用例要传锁的持有者夹具 `lock_holder`；边界检查取文件系统类型的一步由自动夹具替换，带 `real_filesystem` 标记（根
`pyproject.toml` 登记）的用例改用宿主真实的取法，两者同见 [`tests/README.md`](./tests/README.md)。

## 实际执行（运行 .feature）

core 是库，不自带可执行入口。执行 `.feature` 由 CLI 包承担（组合根：读 feature、注入引擎 adapter、渲染结果）：

```bash
uv sync                                                    # 仓库根：一次安装五个 workspace 成员
uv run gherkai run features/wikipedia_generic.feature      # 仓库根
```

这条 feature 首步是内建导航、后两步是 AI step、默认引擎是 `novaact`：实际运行需要 AWS 凭证与 region 就位、账户已开通引擎所需服务；
Midscene 引擎另需先在 `engines/midscene` 下 `npm ci && npm run build`。前置清单见根
[`CONTRIBUTING.md`](../CONTRIBUTING.md)「开发环境」，执行前用 `uv run gherkai doctor` 自检。

contributor 视角的 CLI 细节（模块布局、退出码分层、preflight 次序）见 [`cli/DEVELOPMENT.md`](../cli/DEVELOPMENT.md)；
参与开发的总入口（环境、测试、发布链、文档地图）见根 [`CONTRIBUTING.md`](../CONTRIBUTING.md)，执行与归集的机理解读见
[`docs/internals/`](../docs/internals/README.md)。
