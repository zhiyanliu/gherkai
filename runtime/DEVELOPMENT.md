# runtime 包 —— contributor 文档

同目录的 [`README.md`](./README.md) 是发行包的入口页（逐字发布到 PyPI，只保留定位 / 安装方式 / 最小用法与外链），使用者的用法见 [`docs/user-guide/`](../docs/user-guide/README.md)；本文件面向修改本包的 contributor，不进发行包。

发行名 `gherkai-runtime` / import 名 `gherkai_runtime`（ADR 0037 决策 2a「三名分离」；发行名 `gherkai` 归 CLI 包）。

`cli`、部署 provider `deploy_aws`（含其中的 Lambda handler `gherkai_deploy_aws/lambdas/`）与未来 WebUI 的**共同地基**（ADR 0016「演进」节）：本包持有产品级知识——两个引擎的注册与拉起、
云资源命名、run 的装配与推进；各入口只做参数解析与呈现。依赖方向：`入口 → gherkai_runtime → gherkai_core`
（窄腰红线不变：引擎知识不进 core）。

## 模块

包内十个模块（`__init__.py` 只有包说明、无逻辑）：

- `compose.py` —— 组合根/引擎注册表，按职责分四组：
  - **worker 拉起**：`resolve_worker_cmd`（四级 worker 定位链，ADR 0037 决策 3——env 覆写 `GHERKAI_WORKER_<ENGINE>_CMD`（+ 可选
    `_CWD`）> 同 venv `-m`（仅 Python 引擎）> PATH 上 `gherkai-worker-<engine>` > `uvx` 按版本临时拉起（**仅 novaact**；
    midscene 无本级，理由见下）；解析结果是 `WorkerCmd`，四级均未命中时抛 `WorkerNotFoundError`，交由调用点分叉）/
    `is_pure_release`（版本是否为纯发行版，第四级的门槛之一；部署 provider 判断是否同步基础镜像时也用它）/ `build_engines`（local 后端）/
    `build_fargate_engines`（cloud 后端，只由推进器 Lambda 调用，ADR 0016 决策 C；接受**显式 task-def revision ARN** 的映射，ADR 0038）/ `make_resolver`（把引擎映射包成 core 要的
    `EngineResolver`）。注入 worker 的 env 由本模块独占（`GHERKAI_STEPS_DIR` / `GHERKAI_NO_ARTIFACTS` / `GHERKAI_EXTRA_HTTP_HEADERS` /
    `GHERKAI_SESSION_WARMUP_URL` / `RUN_ID`：前四个有值显式注入、无值显式清除，`RUN_ID` 是 `build_engines` 的必给参数、恒注入；`scrubbed_environ` 继承 `os.environ` 并先清除这些键，是每次注入的起点，
    `tools/e2e_harness.py` 也复用它）。`nova_act_timeout_s` 是 Nova 单 act 上界（注入的 `NOVA_ACT_TIMEOUT_S`）的单一取值点：惰性取值并缓存，
    坏值抛 `ValueError`；两个 builder 遇到坏值时把 Nova 那一项装配为一用即抛的占位项，只用 Midscene 的 run 不受影响。
  - **worker 的两个非 job 入口**（ADR 0036「4.」「5.」）：`query_capabilities`（spawn `worker --capabilities` 读取自述对象——
    steps 加载结果 / 确定性 step 清单 / grace 下限 / 模型 id / 支持的测试目标（顶层 `targets`，缺键按版本不一致拒绝）/ 会话预热支持键 `session_warmup`（`SESSION_WARMUP_KEY`）；契约校验全在此、不合契约不写缓存；进程内按「引擎 + steps
    目录」缓存；`engine_min_grace` 从中取下限，Nova 查询时注入 `NOVA_ACT_TIMEOUT_S` 使两端同源）与 `match_deterministic`
    （spawn `worker --match-steps` 做 plan 标注，plan 先取自述核过协议版本才发）。两者共用 `_ask_worker` 中的一份 spawn 与诊断实现；失败按成因分三类、
    各一个异常类，调用点据类分叉、不解析消息（ADR 0036「5.」末段）：worker 已启动但非零退出（最常见的成因是使用方 `steps/` 加载失败）抛
    `WorkerSelfDescribeError`；自述取到了、与命令行工具不兼容（身份位或载荷键不合契约，含协议版本不等；除 `engine` 身份位指错引擎那一项外，诊断都以
    `VERSION_MISMATCH_ADVICE` 那一句结尾）抛 `WorkerIncompatibleError`；取不到（起不来、超时、输出不是合法 JSON）抛 `WorkerUnavailableError`，定位不到的
    `WorkerNotFoundError` 是它的子类。前两类在各调用点都不降级（命令以退出码 2 结束，doctor 记为失败项），只有 `plan` 对取不到降级。自述对象里测试目标的读取与取交集由同组的纯函数提供（`worker_targets` / `step_targets`（step 未声明目标时视为只在桌面网页上有实现）/ `available_targets`·`unsupported_targets`（声明目标与支持目标的交集、差集）/ `target_supported`·`target_session_limit`，ADR 0049 决策 2、3），plan / list-deterministic / doctor / 执行前预检只调用这些函数、不各自取交集。
  - **存储与云端目标装配**：`build_local_stores`（关键字参数 `lock_holder` 原样交给 core 的 `LocalRunStore`：推进这个 run 的进程，即前台
    `run` 与本机后台推进进程，传 `process_lock_holder()`，查询命令不传，拿到的 RunStore 不能建 run）/ `process_lock_holder`（建 run 的进程用的生命期锁
    持有者，返回 core 的 `run_dir.HoldUntilExit`：收下的描述符不关闭也不交出，锁随进程退出释放；「从建 run 起持锁到进程退出」是组合根对进程的
    装配决定，所以由这里给出，ADR 0054 决策三「持锁的描述符」、ADR 0030 决定四；每次调用新建一个，调用方不依赖是不是同一个实例）/
    `build_cloud_stores` / `local_result_store`（本机推进器用的判定存储：本地文件存储外面套 core 的 `RetryingResultStore`，保存失败按 1、2、4 秒退避重试；`build_local_stores` 与 `detached.assemble_local_run` 都经它装配，云端的组合根不套，ADR 0030 决定三「保存明细失败」条）/ `resolve_cloud_target`（返回 `CloudTarget`：云资源的完整名称 +
    region/profile 一处解析）/ `resolve_aws_identity`（profile 与 region 解析链的唯一实现，`resolve_cloud_target` 与本机后台宿主共用）/
    `resolve_region` / `read_device_farm_project`（读 SSM 记录的云端 Device Farm 项目 ARN，参数不存在时返回
    None）/ `preflight_cloud_resources`（提交前的资源存在性检查）/ `probe_aws_identity`（供 doctor 使用）/ `is_botocore_error`（入口据此把云端故障归到
    自己的退出码层）/ `read_resource`（`file://` 与 `s3://` 同一读入口）/ `local_artifact_locations`·`cloud_artifact_locations`（产物落点清单）/
    `events_db_path`·`build_local_event_log`·`build_cloud_event_log`（一个 run 的事件流落点与两个后端的读取入口）/
    `build_cloud_run_list_store`（`list-runs` 用的只读云端 RunStore：先经 `check_run_list_index` 按 DescribeTable 的 `IndexStatus` 判列举所读的状态分组索引
    是否就绪，缺失、`CREATING`、`DELETING` 与不认识的状态抛 `RunListIndexUnavailable`（消息是给使用方的整句），`ACTIVE` 与 `UPDATING` 放行；
    就绪检查只在这条装配路径上，不并入 `preflight_cloud_resources`，ADR 0041 决策七）/ `local_run_list_location`·`cloud_run_list_location`
    （`list-runs` 所查落点的单点，`--json` 顶层与空清单提示都从这里取值，与 `cloud_artifact_locations` 同一做法）。只有
    `build_cloud_run_list_store` 把列举索引名（`names.RUNS_STATUS_GROUP_GSI`）注入 `DynamoDBRunStore`（core 不认 runtime 的命名真源）；`build_cloud_stores` 得到的 store 不能列举，列举只经过做了就绪检查的那一条装配路径。
  - **版本与 variant**：`check_version_skew`·`check_backend_skew`（四个状态常量 `SKEW_OK` / `SKEW_WARN` / `SKEW_BLOCK` /
    `SKEW_SKIP`；六种比对结果（其中「后端没有版本戳」一种另有例外：带设备目标或给了 `--expose-local` 的 run（由 `run_requires_backend_stamp(jobs, tunneled=…)` 在生成运行定义之前判定）判为
    `SKEW_BLOCK`，ADR 0051 决策 13）如何映射到这四态、逐态措辞见 [`cli/DEVELOPMENT.md`](../cli/DEVELOPMENT.md) 的版本 skew 一节；ADR 0037 决策 7）/ `read_backend_version`
    （读后端版本戳，缺失时返回 None）/ `resolve_worker_variant`（提交侧解析 variant → 各引擎 revision，结果为 `WorkerResolution`；失败抛 `WorkerVariantError`，消息本身是给使用方看的整句）/
    `read_worker_default`（部署级默认 variant 指针，doctor 也读它）/ `read_task_def_stop_timeout`（doctor cloud 侧读该 revision 上
    worker container 的 `stopTimeout`，作 grace 下限比对的对照值；没设或 task-def 里找不到该 container 时为 None）/ `new_run_id`·`now`·`now_iso`（run_id 与时钟：`now` 是
    唯一的墙钟读取点，前台 `run` 把它作为调度循环的墙钟注入，`now_iso` 是它的记录写法；读回记录里的时刻用 core 的
    `serialize.instant_from_iso`）/
    `load_feature`（入口共用的工具函数）。
- `detached.py` —— local 无状态批量运行宿主（ADR 0034）：`SubprocessLauncher`（起 worker、旁路落事件与退出记录；构造时注入墙钟，
  每个执行中的 job 一个检查线程按墙钟比对 tick 交来的截止时刻、到点按停止宽限停 worker，ADR 0054 决策二）+ `run_reconcile_loop`
  （本机推进循环，后台推进进程与 `status --wait` 接力共用；`clock` 与判定存储必传，组合根传 `compose.now` 与经 `compose.local_result_store` 装配的判定存储；按 `tick` 返回的 `TickOutcome` 分支，只在这一方的写使 run 成为终态时经 core 的 `reconcile.write_report_from_record` 从记录生成报告（读运行态、按点名的标识读回判定明细），读运行态、读明细与写报告的失败都被隔离；run 级墙钟由 core 的 `project.run_duration_ms` 从运行态的起止算出）+
  `assemble_local_run`（按传入的运行定义装配推进一个 run 所需的各部分：事件库、RunStore、启动器、判定存储与报告存储，结果是 `LocalAdvancer`；
  不启动子进程，后台推进进程在回报 `submit` 之前调用它；装配出的 RunStore 不带锁的持有者、不能建 run，后台推进进程在调用它之前已经建好 run）+ `advance_local_run`（后台推进进程推进一个 run：用它自己生成的那份运行定义，
  不从记录读回，ADR 0035 决策 3「本机 `submit`」）+ `build_local_reconcile`·`drive_local_reconcile`（`status --wait` 接力：从记录读回运行
  定义之后经 `assemble_local_run` 装配、再推进；读不到可用的运行定义时抛异常、什么都不写）+ 接力判超时 `_recover_timed_out_claims`（别人认领的 job，墙钟严格晚于
  截止时刻加固定余量 `_RECOVERY_MARGIN_S`（10 秒）仍无退出记录即判超时；补写的未知退出经 `record_timed_out_if_absent`，只在这个 job
  还没有退出记录时写入；这个条件保证不了不抢在认领方催停的 worker 收尾之前补写；现行设计里管它的进程不在了的 run 不续、
  由别的一方结束，这段接力随实装删除，见 ADR 0054 决策六）。`_pump` 写退出记录时只记事实：超时标志只由检查线程置，退出时刻是拿到退出码之后读一次注入的墙钟；
  worker 在截止时刻之后自己退出时是否按超时处理由 core 的投影判断
- `deadline.py` —— 运行期限的算式（ADR 0054 决策二）：`compute_deadline_at` 在建 run 时由创建时刻、各 job 的墙钟预算与每 job 尾段算出
  `deadline_at`，写进运行定义；每 job 尾段在本机后端取 `local_per_job_tail_s`（`2 × G + 10` 秒，G 为停止宽限），在云端后端取
  `CLOUD_PER_JOB_TAIL_S`（210 秒，由超时触发的调度精度 60 秒、Fargate 停止宽限上限 120 秒与事件链尾延迟约 30 秒组成，最后一项是经验值、
  不是硬上界）；一次性余量 `STARTUP_MARGIN_S` 为 900 秒。`run_times` 由创建时刻那一次读数算出建 run 用到的各个时刻（`RunTimes`：创建
  时刻与它的记录写法、运行期限、隧道边缘的到点时刻即期限加 300 秒），前台 `run`、本机后台推进进程与云端 `submit` 都经它取
- `devicefarm.py` —— 部署与诊断用的 Device Farm 客户端（ADR 0051 决策 10「调用归属」「项目」、决策 6）：`project_name`（项目名 `{prefix}devices`）/ `read_project_arn`（从后端区域的 SSM 读项目 ARN，ssm client 由调用方注入）/ `resolve_or_create_project`（供 `deploy` 在 cdk 之前找回或建立项目；记录的项目已不存在时经 `warn` 回调立即发出警告）/ `verify_project`（供 `diff` 用 GetProject 只读核对 SSM 记录的项目：存在为 True，NotFound 为 False，不按名称列举、不建立）/ `list_open_sessions`（供 `doctor` 列出未到 COMPLETED 的会话）/ `is_access_denied`（provider 判定读 SSM 失败是否为无权限，与本模块共用一份错误码集合）；无权限归为 `DeviceFarmAccessDenied`（记录的项目已不存在而找回或新建又被拒时带 `stored_project_missing`）、同名项目多于一个归为 `AmbiguousProject`，其余 botocore 异常原样抛出。Python 侧唯一构造 devicefarm 客户端的地方，区域恒为 `names.DEVICE_FARM_REGION`（构造点、区域与延迟导入的护栏在 `tests/test_devicefarm_client_placement.py`）；不创建、不停止会话（护栏在 `tests/test_devicefarm.py`）
- `app_upload.py` —— 安装包上传到 S3 应用前缀（ADR 0051 决策 9）：按内容哈希定键、managed 桶打标签与按保留承诺同键刷新、本机应用桶只做存在性复用；s3 client 由调用方注入
- `names.py` —— 资源命名真源（零依赖；`deploy_aws/gherkai_deploy_aws/names.py` 直接 re-export 后再加 provider 特有常量，
  避免复刻）：资源名（含 Device Farm 项目名与固定区域 `DEVICE_FARM_REGION`）/ SSM 路径 / Device Farm 项目 ARN 校验与会话 ARN 前缀、交互端点资源的推导（task role 授权用）/ 安装包在产物桶里的键前缀、标签与过期和保留天数（`APP_OBJECT_*`，IaC 与上传侧共用）/ 引擎产物子目录名 `ARTIFACT_SUBDIR` / ECR repo 名 / 血缘 tag 键 / worker 镜像 tag（`image_tag` 是 PEP 440 → docker tag 字符集的
  **唯一归一化与校验点**，ADR 0038）
- `tunnel.py` —— 隧道 provider（ADR 0035；鉴权按 ADR 0051 决策 13）：`TunnelProvider` 两个入口，前置检查 `check_prerequisites`（真正导入一次
  SDK、查环境变量 `NGROK_AUTHTOKEN`）与起隧道 `start(local_origin, *, closes_at, timeout_s)`。`NgrokTunnel` 经 ngrok 官方 Python SDK 在宿主进程里
  建会话（不启动 ngrok 可执行文件，隧道事实里没有进程号）：每个 run 生成访问令牌与会话 cookie 值、渲染五条规则的流量策略（最前面一条在到点
  时刻之后一律拒绝）、给出会话预热地址；SDK 建立监听的调用在守护线程里执行、按 `START_TIMEOUT_S` 放弃等待，迟到建成的监听由那个线程关闭；
  `TunnelInfo.close()` 关闭会话（可重复调用、按 `CLOSE_TIMEOUT_S` 放弃等待、失败不外抛）。模块顶层不导入 SDK，前置检查与起隧道都经
  `_load_sdk` 导入（ADR 0037 决策 2c），测试的自动夹具对其中的 `_import_sdk` 打桩 + job 文本里 origin 的带边界替换（`replace_origin` /
  `map_origin_in_jobs`，
  替换成干净的隧道地址；core 对隧道无知、worker 只做一次预热导航）；边缘契约常量中，预热路径、校验路径、令牌参数名与 cookie 名只在本模块持有，
  页面标题与正文标记与两个 worker 中消费它们的那份同值（Nova 只持标题，Midscene 持标题与正文标记），由 `engines/fixtures/tunnel-warmup.json` 对拍
- `tunnel_host.py` —— 隧道**宿主**编排（ADR 0035 决策 3）：`start_tunnel_for_jobs`（起隧道再映射 definition，映射失败时先关闭会话；前台 `run`
  与本机后台推进进程用它）与 `map_jobs_to_tunnel`（映射与隧道模式下恒同时给出的额外请求头 `TUNNEL_EXTRA_HTTP_HEADERS`；云端 `submit` 拿到
  守护进程回报的地址之后直接调用它）；会话预热地址在 `TunnelInfo.warmup_url`（经 `TunnelSetup.info` 取得）。云端 `submit` 的隧道守护进程的
  主体 `hold_tunnel_for_cloud_run`（起隧道、回报、等 run 的标识、轮询到终态或到点时刻、关闭会话；隐藏子命令 `_tunnel_watch` 的入口在 cli）
  与它的轮询 `watch_cloud_run`（间隔 `WATCH_POLL_INTERVAL_S`，到点时刻即运行期限加 300 秒、按墙钟判断；每次读在一个守护线程里进行，轮询分段
  等它的结果，一次读不返回时照样在到点时刻结束；读不到与读失败按情形的种类记一句）
- `handoff.py` —— `submit` 与它启动的两种后台进程（本机后台推进进程、云端隧道守护进程）之间的交接协议（ADR 0035 决策 3）：四种消息
  （`AdvancerInput` / `AdvancerReport` / `WatchInput` / `WatchReport`，各为一行 JSON）与编解码；原始描述符的读写（`read_line` / `write_all` /
  `wait_readable` / `close_quietly`，以及对端还在不在的判据 `peer_closed`：对一条由对端独占写端的管道的读端做一次非阻塞读）；回报之后把输出
  改接日志（`open_log` / `redirect_output`）与守护进程日志的落点 `watch_log_path`；`WatchChannel` 是云端 `submit` 一侧持有守护进程两个描述符
  的句柄。只依赖标准库与 core，两端的入口在 cli
- `textui.py` —— 人读输出的呈现件（ADR 0047）：`render_table` / `render_tree` / `TreeNode` / `status_text` / `styled` / `plain`
  与 re-export 的 `Text`；框线、宽度（终端宽度或不折行的名义宽度）、哪些列可折行、颜色开关（`use_color`：环境变量 `NO_COLOR` /
  `FORCE_COLOR` / `TERM=dumb` 的判定取自 `gherkai_core.termcolor`、与 worker 日志前缀共用一份，本模块再看标准输出是否为终端）与状态色映射 `STATUS_STYLE` 都由本模块提供；cli 与部署 provider 只经本模块使用 rich

## 从 checkout 运行 / 测试

```bash
uv sync                          # 仓库根：一次安装五个 workspace 成员 core/runtime/cli/engines/novaact/deploy_aws（editable）
uv run pytest -q runtime/tests   # 仓库根：只运行本包单测（`uv run pytest` 不带路径 = 覆盖全部成员）
```

`uv sync` 按根依赖装上本包的 `tunnel` 组件（ngrok 的 Python SDK，ADR 0037 决策 2c）；真实执行带 `--expose-local` 的命令另要设环境变量
`NGROK_AUTHTOKEN`，不需要 ngrok 可执行文件。单测从不起真实隧道：`tests/conftest.py` 的自动夹具把 `tunnel._import_sdk` 换成一被调用即让
用例失败的函数、并去掉 `NGROK_AUTHTOKEN`；要用假 SDK 的用例经 `NgrokTunnel(load_sdk=...)` 注入。交接协议的用例用真实的 `os.pipe`
与线程，`redirect_output` 这类改接本进程描述符的在子进程里验证。

本机建 run 的用例同在 `tests/conftest.py`：夹具 `lock_holder` 是测试用的持有者，要建 run 的 `LocalRunStore` 与 `build_local_stores`
传入它，它在用例结束时关闭收下的描述符（生产用的持有者没有放开锁的方法）；自动夹具把边界检查取文件系统类型的一步换成本平台清单的
第一项，结论不依赖宿主的文件系统，带 `real_filesystem` 标记的用例不替换、用宿主真实的取法。规则与 core 的测试夹具相同。

`build_cloud_stores` 与云端各入口（提交前检查、variant 解析、版本戳读取等）的 boto3 import 惰性收敛在 `_make_*` 钩子内：**纯 local 路径绝不
触发该 import**（ADR 0016 窄腰 / 0030）。`build_fargate_engines` 不建句柄：`ecs` / `s3` 由推进器 Lambda 建好传入。修改这些函数时须保持 `import boto3` 不上移到模块顶层。`devicefarm.py` 同理：boto3 只在 `_make_devicefarm_client` 内 import，CLI 与 deploy 的 `--help` 不为它拉起 AWS SDK。

worker 定位链第四级（`uvx`）与 fd 传递的相互作用是实际运行得出的约束：`uvx` 穿透 fd3，`npx -y` 会替换 fd
并导致事件全部丢失（因此 midscene 无第四级）。细节与实测证据见 `resolve_worker_cmd` 的 docstring 与 ADR 0037 决策 3。

## 相关 ADR

- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / 组合根注入 /「演进」节（本包为何从 cli 拆出）
- [0024](../docs/adr/0024-worker-core-protocol.md) worker 与 core 的协议（单 act 上界注入、引擎自报 grace 下限、`RUN_ID` 注入）
- [0026](../docs/adr/0026-schedule-module.md) schedule 契约（engines 注入形状）
- [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝（两套 store 装配复用同一写序）
- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) 云端资源清单与命名契约
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态批量运行（`detached` 宿主、推进触发源、job timeout）
- [0035](../docs/adr/0035-local-app-testing-via-tunnel.md) 隧道暴露本机应用（`tunnel` / `tunnel_host` / `handoff`）
- [0036](../docs/adr/0036-deterministic-capability-discovery.md) 确定性能力自述
- [0037](../docs/adr/0037-distribution-and-packaging.md) 分发与打包（三名分离、worker 定位链、版本 skew）
- [0038](../docs/adr/0038-worker-image-delivery.md) worker 镜像交付（variant → 显式 revision、镜像 tag 归一化）
- [0047](../docs/adr/0047-cli-human-readable-tables-with-rich.md) 人读输出的表格、树与状态颜色（`textui`）
- [0049](../docs/adr/0049-worker-capabilities-targets-keys.md) 能力自述的测试目标键（`compose` 的 targets 契约校验与交集）
- [0051](../docs/adr/0051-device-session-lifecycle-and-app-distribution.md) 远程访问会话的生命周期与应用分发（`app_upload` 的应用前缀与保留承诺、`devicefarm` 的项目找回与会话列举）
- [0053](../docs/adr/0053-project-config-file.md) 项目配置文件（region / profile 解析链里的配置文件层）
- [0054](../docs/adr/0054-run-deadline-lifetime-lock-and-settling.md) 运行期限与生命期锁（`deadline` 的算式与建 run 的各个时刻、`compose.process_lock_holder`）

参与开发的总入口（环境、测试、发布链、文档地图）见根 [`CONTRIBUTING.md`](../CONTRIBUTING.md)；执行与推进的机理解读见
[`docs/internals/`](../docs/internals/README.md)。
