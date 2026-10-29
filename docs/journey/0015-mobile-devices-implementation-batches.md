> 类型: 调查记录

# 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试

由实施规划 workflow 在 2026-10-16 产出：每个批次一个规划者，读点名的 ADR 与代码，给出改动面、先写的测试、依赖、真跑核对与易错点；规划者提出的设计缺口经逐条对抗复核，成立的已补进 ADR（见 journey 0013 现场）。次序与进度在 journey 0013；本文是各批的施工底稿，实施时按代码现状校准，批次完成后删去对应一节，全部完成后删除本文。行号与符号以产出当时的代码为准。


## 7. B8-deploy-iac：部署侧：权限、Device Farm 项目找回或建立、SSM、doctor 设备项

规模 M。


**依赖**

- B3-config-submit：提交侧从 SSM（names.DEVICE_FARM_PROJECT_KEY）读项目 ARN，写进 device_request.project_arn，缺值时以退出码 2 结束并提示「部署未启用设备支持」；方向上是 B3 消费 B8 的命名常量。doctor 在本机后端时要取项目 ARN，依赖 B3 的 gherkai.toml / GHERKAI_DEVICE_FARM_PROJECT_ARN 解析结果（0053）
- B1-capabilities：doctor 目标清单这一行要用 query_capabilities 返回的 targets / max_session_s（已校验形态）
- B6-midscene-device：不是接口依赖，而是端到端验收依赖。task role 授权是否够，要等 worker 的设备模块（列举、建会话、查询、停止、按名列举，以及应用存在性检查）真跑过才能确认

**改动面**

- `runtime/gherkai_runtime/names.py` · 模块级常量（与 SUBNETS_KEY / VPC_KEY 并列）：补齐 Device Farm 命名单点（SSM 相对键 DEVICE_FARM_PROJECT_KEY="device-farm-project" 已存在，全路径经 ssm_path）：新增项目基名 BASE_DEVICE_FARM_PROJECT="devices"（项目名 default_name(prefix, 它) 即 `{prefix}devices`）、固定区域常量 DEVICE_FARM_REGION="us-west-2"、「待建立」占位值常量，以及纯函数 device_farm_project_id(arn) 和 device_farm_session_arn_prefix(project_arn)（得到 arn:aws:devicefarm:us-west-2:<账户>:session:<项目 id>/*）。stack、provider、doctor、提交侧都只引用这些常量，调用点不写裸字面量（与 0038「SSM 参数与命名真源」同一纪律）（0051 决策 10「项目」；0033 资源清单 11.；0038 SSM 命名真源）
- `deploy_aws/gherkai_deploy_aws/names.py` · re-export 列表 + ssm_* 便捷函数：re-export 上面新增的常量与函数；加 ssm_device_farm_project_path(prefix)，形状与 ssm_vpc_path 相同，供 stack 写、provider 读（0051 决策 10；0033 资源清单 11.）
- `runtime/gherkai_runtime/devicefarm.py（新模块）` · 部署与诊断用的 Device Farm 客户端模块（`gherkai-runtime[aws]`，boto3 函数内延迟导入）：Python 侧唯一构造 devicefarm 客户端的地方，客户端恒用 region_name=DEVICE_FARM_REGION，凭证沿用调用方的 profile。提供以下函数：read_project_arn(ssm, prefix)，从后端区域的 SSM 读，ParameterNotFound 时返回 None；resolve_or_create_project(prefix, profile, stored_arn)，SSM 有值时先用 GetProject 核对，再按名翻页 ListProjects，命中多个抛专用异常，零个则 CreateProject；list_open_sessions(project_arn, profile)，翻页 ListRemoteAccessSessions，过滤掉状态为 COMPLETED 的会话，返回 arn、name、status、created，用于 doctor 拼控制台链接和停止命令。不创建也不停止会话。权限错误单独分类成一种异常（AccessDenied），供 deploy 降级（0051 决策 10「调用归属」「项目」；0051 决策 6（doctor 列未完成会话）；0033 部署方 ListProjects/CreateProject 于 *、GetProject 于项目 ARN）
- `deploy_aws/gherkai_deploy_aws/cli.py` · Provider.build_context：context 闭集加 device_farm_project。build_context 保持纯推导：ARN 由调用方先解析好再传入（新增一个关键字参数，或者让 _run_cdk 把解析结果放在 args 的私有属性上），不在 build_context 里做 IO。值为 None 时这个键不进 context，或者给占位常量，两者在 stack 里等价（0037 决策 6 context 闭集加 device_farm_project；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/cli.py` · Provider.deploy（_guard_vpc_spec 之后、_run_cdk 之前新加一步 _resolve_device_farm_project_for_deploy）：放在工具链闸、容器引擎、--vpc、VPC 三态之后，cdk 之前。先读 SSM，再调 runtime.devicefarm.resolve_or_create_project：同名项目命中多个时以退出码 2 结束；遇到 AccessDenied 时，SSM 有 ARN 就沿用并打一条警告，没有就警告后跳过（context 不带 ARN）；其余错误按前置失败处理，以退出码 2 结束。文案按 0039 只说发生了什么、为什么、怎么办，不出现 ADR 编号。解析结果交给 _run_cdk 和 build_context（0051 决策 10「项目」与无权限降级；0033「设备目标增量」部署方行）
- `deploy_aws/gherkai_deploy_aws/cli.py` · Provider.diff / synth_only / destroy（经 _run_cdk）：这三个动作不建立项目：只读 SSM 现值，没有值时传占位值。读 SSM 失败时怎么处理见 open_questions。diff 的 docstring 要写明「待建立」时变更集里看不到 Device Farm 授权（0037 决策 6（diff 不建立、synth-only 与 destroy 取 SSM 现值或占位）；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/cli.py` · 模块头 docstring「Provider 负责」「退出码」两段：职责清单加「deploy 在 cdk 之前找回或建立 Device Farm 项目」；退出码 2 的情形加「同名项目命中多个」（0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · BackendStack.__init__ 新增 _resolve_device_farm_project()：读 try_get_context("device_farm_project")。缺失或等于占位值时 self.device_farm_project_arn=None，不报错（这一点与 _resolve_version 相反，app 不 fail-fast）。非占位的值要过 ARN 形态校验，必须是 arn:aws:devicefarm:us-west-2:<12 位>:project:<id>，不合法即在 synth 期报错，因为拼出错的 session 前缀只会表现为运行期 AccessDenied（0037 决策 6（缺少或占位不 fail-fast）；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · 新增 _ssm_device_farm()（与 _ssm_deployment_stamp 并列）：ARN 不为 None 时写 StringParameter，路径为 ssm_device_farm_project_path(prefix)，作为 stack 资源，随部署事务同生死、随 destroy 删除（项目本身由 SDK 建立、不归 stack 管，所以 destroy 不删项目）；ARN 为 None 时不建这个参数（0033 资源清单 11.；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · _grant_task_role 的 elif engine == "midscene" 分支：只在 ARN 不为 None 时，给 Midscene task role 加以下几条 statement，区域段一律写字面量 us-west-2，不用 self.region。① devicefarm:ListDevices，资源 *，单独一条 statement。② GetDevice，资源 arn:aws:devicefarm:us-west-2::device:*。③ CreateRemoteAccessSession，同一条 statement 里列项目 ARN 和 device:*。④ Get/StopRemoteAccessSession，同一条里列 session:<项目 id>/* 和项目 ARN，两种都要。⑤ ListRemoteAccessSessions，资源为项目 ARN。⑥ s3:ListBucket，资源为桶 ARN，条件按 spike 实测形态写 StringLike s3:prefix ["apps/*"]。现有两个引擎共享的 GetObject（资源 {bucket}/*）已经覆盖 apps/*，不必重复授。Nova 的 role 不加任何 devicefarm 动作，也不加 ListBucket（0033 task role 表 devicefarm / apps 行；0051 决策 9（ListBucket 把 403 变 404）、决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · _storage 的 ArtifactsBucket lifecycle_rules：加规则 expire-apps：tag_filters {"gherkai": "app"}，expiration 14 天（E=14）。与现有 expire-job-in 并列，规则 id 用常量（0051 决策 9 保留承诺（E=14 天））
- `deploy_aws/gherkai_deploy_aws/stack.py / app.py` · 模块头 docstring（资源清单、context 配置项）：stack 头的 SSM 部署戳清单加 device-farm-project；app 头的 context 清单加 device_farm_project（由命令派生，可缺省）（0037 决策 6）
- `cli/gherkai_cli/__main__.py` · _doctor_cloud 末尾，新增 _doctor_devices(target, add)：读 SSM 的项目 ARN：没有值时加一行「部署未启用设备支持」，required=False。有值时调 runtime.devicefarm.list_open_sessions，列出未到 COMPLETED 的会话（含排队中），每条附控制台链接和 `aws devicefarm stop-remote-access-session --region us-west-2 --arn …` 停止命令；没有权限时单独一行说明。runtime.devicefarm 在函数内导入，CLI --help 不拉 boto3（0051 决策 6 泄漏护栏（doctor 列出）；0033 CLI 的 ListRemoteAccessSessions）
- `cli/gherkai_cli/deploy.py` · destroy 子命令的 description（约第 169 行）：保留清单加 Device Farm 项目（含会话记录与录像），并给出手动删除命令（0033 RETAIN 段；0051 决策 10）
- `docs/user-guide/cloud-backend.md + docs/adr/0038（SSM 命名真源常量清单）` · 「拆除与清理」节；0038「键名常量」枚举：拆除手册加 `aws devicefarm delete-project --region us-west-2 --arn <项目 ARN>`；0038 常量清单补上 DEVICE_FARM_PROJECT_KEY（按差集对照 names.py），SSM 参数族表加一行，写者为 stack 资源（0033 RETAIN 段；0038 SSM 命名真源；CLAUDE.md 文档校准）

**先写的护栏测试**

- `deploy_aws/tests/test_stack.py`：SSM 参数全集按 context 分两种情形锁定：不带 device_farm_project 或带占位值时，仍是现有 6 条（改写 test_ssm_parameter_set_is_exactly_six）；带合法 ARN 时恰为 7 条，多出的那条值等于传入的 ARN（0033 资源清单 11.；0037 决策 6）
- `deploy_aws/tests/test_stack.py`：带 ARN 合成时 Midscene task role 的权限：ListDevices 只出现在资源为 "*" 的 statement；Get/StopRemoteAccessSession 所在 statement 的 Resource 同时含 session:<id>/* 和项目 ARN（缺一种即失败，这是模拟器假阳性留下的护栏）；CreateRemoteAccessSession 同时含项目 ARN 和 device:*；GetDevice 的设备 ARN 账户段为空；所有 devicefarm ARN 的区域段都是 us-west-2，夹具的 REGION=us-east-1 正好用来反证没有误用 self.region；ListBucket 带 StringLike s3:prefix apps/*（0033 task role 表 devicefarm / apps 行；0051 决策 10）
- `deploy_aws/tests/test_stack.py`：两个引擎的 role 分开：Nova task role 的策略里没有任何 devicefarm: 动作，也没有 s3:ListBucket；不带 ARN 合成时整个模板没有任何 devicefarm: 动作。在 test_task_role_resource_arns_narrowed 里补一条：只能用 * 的动作恰好是 AgentCore 4 个加 ListDevices，对应 0033 写的「这 5 个」（0033「两个引擎 task role 分立」「风险收在两道」）
- `deploy_aws/tests/test_stack.py`：非占位但形态不合法的 device_farm_project（区域不对、不是 project 资源）在 synth 期抛 ValueError；缺失或占位不抛（0037 决策 6（缺少或占位不 fail-fast））
- `deploy_aws/tests/test_stack.py`：产物桶 lifecycle 规则恰为 expire-job-in 和 expire-apps 两条，后者 TagFilters 为 gherkai=app、过期 14 天（0051 决策 9）
- `deploy_aws/tests/test_provider.py`：context 闭集差集护栏：build_context 可能产出的键集合，等于 stack.py/app.py 源码里所有 try_get_context("…") 字面量的集合，即 {prefix, version, vpc_id, use_default_vpc, stop_timeout, device_farm_project}，并断言 device_farm_project 不是任何 argparse flag（0037 决策 6 flag 面与 context 对齐、闭集）
- `deploy_aws/tests/test_provider.py`：deploy 编排顺序与分支（用 stub 掉的 devicefarm 模块）：VPC 三态拦下时零次 devicefarm 调用；同名项目命中多个时以退出码 2 结束且不调 cdk；AccessDenied 且 SSM 有值时 cdk argv 带该 ARN 并打警告；AccessDenied 且 SSM 无值时 argv 不带 device_farm_project（或带占位）且打警告；diff、synth、destroy 永不调用 CreateProject。现有 cdk 夹具要同时把 devicefarm 和 SSM 读 stub 掉，否则现有测试会直连真 AWS（0051 决策 10「项目」与降级）
- `runtime/tests（或 cli/tests）新增 test_devicefarm_client_placement.py`：差集护栏：Python 源码里 client("devicefarm" 只出现在 runtime/gherkai_runtime/devicefarm.py；core/ 零引用；推进器 Lambda 源零引用；构造客户端时的 region 引用 names.DEVICE_FARM_REGION（0051 决策 10「调用归属」护栏测试）
- `runtime/tests 新增 test_devicefarm.py（botocore Stubber 或 moto）`：resolve_or_create_project 的情形：SSM 有值且 GetProject 成功时直接用，不 List；按名翻页（带 nextToken）时零个就 Create、一个就复用、多个抛异常；list_open_sessions 过滤掉 COMPLETED、保留 PENDING 等排队态；构造的客户端区域恒为 us-west-2，与传入的后端区域无关（0051 决策 10；0051 决策 6）
- `cli/tests/test_doctor*.py`：SSM 无项目 ARN 时出一行「未启用设备支持」，required=False，退出码不变；有未完成会话时 detail 含会话 ARN、us-west-2 停止命令和控制台链接；文本过 test_user_facing_messages 的内部指代护栏（0051 决策 6；ADR 0039）

**完整性审查补认领**

- 红线测试补：SSM 参数缺失与无凭证、拒绝、网络、限流分开处置；只有完全无凭证的 --synth-only 可占位并警告；旧 ARN NotFound 后零、一、多个命中三种结果；无凭证且无 region 时仍能离线导出。
- 护栏测试：Device Farm 客户端在 Python 侧只在 runtime 的设备模块构造，core 不引用它（TS 侧的同类断言归 B6）。0051 决策 10。
- SSM 值失效时 deploy 的 GetProject 核对、diff / --synth-only / destroy 的读失败处置（本轮补进 0051 决策 10 与 0037 决策 6）。

**真跑或对抗核查才算数的结论**

- 真部署后，用 Midscene task role 的真实凭证（在容器内，或按同一份 CDK 产出的策略 assume）把 worker 的全部设备动作正反面走一遍。0033 明写「尚未经真部署后的 task role 端到端验证」；CDK 会合并或改写 statement、拼 Fn::Join，合成出的策略不等于 spike 手写的 JSON，单测只能比对形态
- 会话 Get/Stop 的两种资源同授要在真 task 上再确认一次（ECS task role 的调用者身份由 ECS 签发，不经探针的 AssumeRole）：同授放行、只授一种被拒。探针验证时 assume 之后先核对调用者身份，会话名至少两个字符
- CDK 生成的 ListBucket 条件（StringLike s3:prefix apps/*）下，缺失键的 HeadObject 回 404、无权限回 403，在部署后的真实桶上复核
- deploy 的项目生命周期跑一整轮真账户：首次部署建立项目，再次部署经 SSM 复用，destroy 后项目还在、SSM 参数被删，同 prefix 重新部署时按名找回同一个项目；后端在 us-east-1 时，Device Farm 调用落在 us-west-2、SSM 落在后端区域
- 部署方没有 Device Farm 权限时，真实报错码的形态（AccessDeniedException 还是别的），决定降级分类写得对不对；mock 给不出真实错误码
- doctor 对真实排队中或运行中的会话：ListRemoteAccessSessions 返回的状态取值，以及控制台链接格式（会话 ARN 到控制台 URL 的拼法）实际能打开
- 只授本项目时，访问别的项目的会话被拒，在部署后的 role 上反证
- 版本错位：新 CLI 写入带 target/device_request 的 RunMeta，若被旧版 cloud Lambda 推进器读（旧 job_from_dict 忽略未知键），设备 job 会被当作桌面 job 静默起桌面 worker。要在真部署上确认 CLI 与后端版本不一致时有拦截（版本一致性检查覆盖这条路径），或者确认这一路不可达。单测证明不了
- Fargate 路径：带 target/deviceRequest/timeoutS 的 job 行经 S3 PutObject 后，由真实 Midscene 与 Nova 镜像的 JobSource 读回，旧字段行为不变（Nova 遇到多出的 timeoutS 键不出错）。至少用 tools/e2e_harness.py 真跑一次桌面 job，确认加了 timeoutS 后两引擎行为与之前一致
- 开发版本混搭的完整性不变量：用不传预热地址的旧 reconciler 与新 worker 组合，确认 worker 发出 precheck_failed，而不是在 401 页上把导航和地址断言判成通过
- 0035 决策 5 待实施期核实的一项：云端 RunTask 的 containerOverrides 带着预热地址，CloudTrail 的 RunTask 事件是否记录 overrides 里的 env 值；task 停止后约 1 小时内经 ecs:DescribeTasks 读到它的实际窗口

**易错点**

最容易做错的有三件。

① Get/StopRemoteAccessSession 必须在同一条 statement 里同时列会话前缀和项目 ARN，所有 devicefarm ARN 的区域段都要写死 us-west-2，不能沿用 _grant_task_role 现有的 `region = self.region` 习惯。测试夹具 REGION=us-east-1，护栏测试正好用它反证；资源少一种、或区域跟着 self.region 走，模拟器会判允许，真实角色却被拒。

② build_context 要保持纯推导，项目的找回或建立放在 deploy 里 VPC 三态之后、cdk 之前，而且只有 deploy 走这一步，diff、synth、destroy 绝不能调 CreateProject。现有 test_provider 的 cdk 夹具只 stub 了 subprocess 和四步，加入 Device Farm 和 SSM 读之后必须一并 stub，否则现有测试会直连真 AWS，这条在仓库里踩过一次。runtime.devicefarm 必须在函数内导入，否则会破坏「--help 不拉 boto3/aws_cdk」的护栏测试。

另外，无权限降级只针对 AccessDenied，限流、网络等其他错误不能悄悄跳过，否则一次偶发错误就会让 stack 删掉 Midscene 的 Device Farm 授权，而且只有设备 run 运行时才会暴露。


## 8. B6-midscene-device：Midscene worker 设备模块（接缝、命令守卫、能力探测、适配器、终结四阶段、evidence）

规模 L。

**顺带闭合的桌面项（第 6 批复核留下、ADR 0028 记为「目前未做」）**：两个桌面 worker 在 StartBrowserSession 返回后发 `session_opened`（core 侧归约该事件的能力 B5 已落），把建连耗尽时 core 侧血缘为空的窗口关掉；设备会话本就在这一批发同一事件，桌面与设备在此汇合。Nova 退出 NovaAct 那段无预算的边界（看门狗 Stop）owner 暂不做，仍留在 ADR 0028 已知边界里。


**依赖**

- B1-capabilities：--capabilities 输出 targets 与 max_session_s、会话预热支持键，以及建会话前的 targets 自检函数（B6 提供 device/limits 的常量，B1 消费；自检失败时调用 B6 新增的 scope_done{status:error} 出口）
- B2-core-target-job：Job 的 target{device, ui_kind, app{alias,bucket,key,sha256,app_id}}、device_request{provider, device_arn|os_version, billing_method, project_arn, acquire_timeout_s}、timeoutS 的线上形态，以及 Python 到 TS 的字段往返 fixture
- B4-steps-registry：webdriver 句柄种类、uiKinds 与 devices 过滤、requires 封闭集，以及按 (device, ui_kind) 匹配并返回条目及其 requires 的 match API；B6 构造它定义的 ctx 七字段
- B5-core-events-termination：core 认 session_opened、session_closed、ScopeDone 的 status/errorType/message 三个新字段，新错误类别（precheck_failed、acquire_timeout、session_lost、capability_unavailable、release_failed），新配对规则与合成 SKIPPED；B6 发事件的形状以 B5 的 wire.py 为准
- B7-tunnel：env GHERKAI_SESSION_WARMUP_URL 的注入、预热页的标记字符串、令牌参数名 gherkai_tunnel_token，以及三份脱敏实现共用的规则与用例（签名类参数集合）
- B8-deploy-iac：真跑依赖 task role 的 Device Farm 权限、应用前缀的 s3:ListBucket（使缺失返回 404）、project ARN 写进 SSM
- B3-config-submit：只在端到端真跑应用目标时需要，即 CLI 把应用上传到 apps/<sha256>/ 并填 device_request

**改动面**

- `engines/midscene/package.json（及 package-lock.json）` · dependencies / devDependencies：@aws-sdk/client-device-farm 从 devDependencies 移到 dependencies（现状只在 devDependencies，供 spike 用；webdriverio 已在 B4 移入 dependencies）；新增 @midscene/core 显式依赖，版本锁定为 1.15.1，与 @midscene/web 同版本。锁文件按 DEVELOPMENT 的规定用 npm 10 重算（npx npm@10 install --package-lock-only）（0052 决策 7（依赖）、决策 3（动态加载的前提））
- `engines/midscene/src/device/limits.mts（新，轻量、不 import 任何 SDK）` · 设备预算常量：放终结四阶段常量（等在途 Create 10s、终结核对 5s、释放 25s、Stop 3s、终结期 Get 5s）、Device Farm 单次调用超时（Create/Get/List 10s）、获取预算缺省 600s、上界 3600s、换台下限 150s、会话上限 150min 与由它推出的 max_session_s、newSession 下限（4min+65s）、pageLoad 150s、执行期请求超时、探测短预算 5s。--capabilities 与 minGraceSeconds 只 import 这个文件，保证不加载 webdriverio 与 Device Farm SDK（0052 决策 6 分层表、0051 决策 2、5，0049 决策 4、5）
- `engines/midscene/src/worker/run-scope.mts` · main()：把建连、Agent、清理收成界面接缝（新的 TargetSurface 接口）：现有 connect()、stopSession()、cleanupRun()、makeGuardedCleanup 包装、BedrockAgentCoreClient 和 chromium.connectOverCDP 原样搬进桌面实现（如 worker/surface-desktop.mts），行为不变。接缝提供五个操作（取 agent、取确定性句柄、导航或启动应用、释放、预热）和三项 step 边界义务（step 前核对、step 后复原并核对、采集界面快照）。scope 开头按 job.target.device 选一次实现；设备实现用 `await import("../device/surface.mjs")` 动态加载。主流程里不写任何按设备的条件分支（0052 决策 2、3）
- `engines/midscene/src/worker/run-scope.mts` · interface Job（同步 lib/job-source.mts 的 Job）：加 target{device, ui_kind, app?{alias,bucket,key,sha256,app_id}}、device_request{provider, device_arn|os_version, billing_method, project_arn, acquire_timeout_s}、可选 timeoutS。两处重复的 Job 类型合成一份（也可以从共享类型文件 import）（0048 决策（Job 携带目标）、0051 决策 2）
- `engines/midscene/src/worker/run-scope.mts` · main()：执行前失败的出口（新）：现状：建连阶段的异常一律 throw，由 bin 打 fatal 后退出码 1，网络重试耗尽时退出码 80。新增 scope 级失败出口：发 scope_done{status:'error', errorType, message}，不发 scope_started，不发任何 scenario 或 step 事件，会话确认释放后以 0 退出。它覆盖这几种失败：自检不通过、收到额外请求头却没有 GHERKAI_SESSION_WARMUP_URL（桌面同样适用）、设备解析零候选、应用对象 404 或 403、启动即自退、获取超时、会话预热被拒或无法确认。之前允许出现的只有 session_opened 与 session_closed。设备路径不使用 EX_WORKER_NETWORK（80）；桌面建连重试与 80 照旧（0051 决策 4、5（退出码）、13（完整性不变量），0049 决策 7）
- `engines/midscene/src/worker/run-scope.mts` · runScenario / runStep 的签名与 step 内顺序：参数 (agent: PlaywrightAgent, page) 改为接缝对象。runStep 按 7 步固定顺序执行：①step_started；②surface.preStep()，失败记 engine_error、不调 handler 也不调 AI；③执行（确定性 handler 拿 surface 给的句柄，现状写死的 `hit.handler({ page }, groups)` 改掉；URL_IN_QUOTES 导航改成 surface.navigate，不再直接 page.goto）；④按条件读地址；⑤surface.restore()，失败时判定改为 error，原判定写进 message；⑥只在 failed 或 error 时采控件摘要；⑦产 evidence、发 step_done，然后把截图与原始树入队。桌面实现的三项义务都是空操作，只有快照在 AI step 上取 page.url()。所有 step 的 step_kind 取 ai / deterministic / navigation 之一。确定性 handler 声明了 requires:['web_context'] 而探测结论为「不提供」或「探测出错」时，不调 handler，分别记 capability_unavailable 和 engine_error（0052 决策 2、5（后果段）、6（固定规则），0050 决策 2，0051 决策 8）
- `engines/midscene/src/worker/run-scope.mts` · main() 的 scenario 循环：加 scope 级终止状态：发生 session_lost（按会话状态判定或按年龄到期）时，序列为当前 step 记 error、本 scenario 余下 step 发 step_skipped、发 scenario_done{error}，后续 scenario 一律不发事件，最后发 scope_done{status:error, errorType:session_lost}。结果未知之后，下一条 scenario 开始前（scenario_started 之前）做一次截图存活探测，失败就发 scope_done{status:error, errorType:engine_error}。现状循环会无条件跑完全部 scenario（0051 决策 4、5（会话丢失序列），0052 决策 6（结果未知））
- `engines/midscene/src/worker/run-scope.mts` · agentOpts / cumulativeTokens / stepCost：类型从 PlaywrightAgent 放宽到 @midscene/core 的 Agent。agentOpts 拆成两份：forceChromeSelectRendering 只给桌面；设备 Agent 的重规划上限缺省 12，可按 0044 决策 2 的 worker 侧 env 覆盖，桌面行为不变。generateReport 和 persistExecutionDump 两端同真同假的约束保留（0052 决策 6（⑨ 重规划）、决策 7（复用 Agent），0044 决策 2）
- `engines/midscene/src/worker/run-scope.mts` · minGraceSeconds / shutdownSequence / onSignal / 进程级兜底：minGraceSeconds 改为由 device/limits 的四段常量和 UPLOAD_TIMEOUT_MS、QUEUE_DRAIN_EXIT_MS、MIN_GRACE_MARGIN_MS 一起推出，结果约 64s（口径见 open_questions）。设备路径的 SIGTERM 收尾换成终结四阶段：置 act 的 abortSignal 并撤销执行令牌、等在途 Create、终结核对、并行释放、发 session_closed、兜底上传与排空；SIGTERM 路径不调 deleteSession；终结只进入一次。新增 unhandledRejection 与 uncaughtException 处理器，记录后进入终结。正常收尾的顺序为：agent.destroy → 报告上传 → deleteSession（5s） → 终结核对 → 释放 → session_closed → scope_done（reportRefs 带 kind:'device_session' 的 device-session.json） → 排空（0051 决策 5，0049 决策 5）
- `engines/midscene/src/worker/run-scope.mts` · log()：现状 log() 直接写 stderr、不脱敏，而 WebdriverIO 的 UND_ERR_CLOSED 会把带签名的端点地址写进错误文本。改为输出前一律经脱敏出口。bin.mts 的 `worker fatal:` 输出同样处理（0051 决策 11）
- `engines/midscene/src/lib/redact.mts` · redactUrlUserinfo（新增规则 ②，建议改名为统一的脱敏出口）：保留 userinfo 规则，新增一条：签名类查询参数与 gherkai_tunnel_token 的值替换成 ***，覆盖 `&` 与 `&amp;` 两种分隔形态。与 core redact.py、Nova lib/redact.py 共用同一组用例。调用点 event-sink.emit、evidence.writeEvidence、error-text.oneLineError、log、device-session.json、page_source 写盘全部改调新出口（0051 决策 11，0035 决策 5）
- `engines/midscene/src/worker/evidence.mts` · StepEvidenceInput / BuildEvidenceInput / EvidenceDoc / stepEvidenceRef：输入里的 `page: {url()}` 换成界面快照 `snapshot{url, url_missing, controls?, controls_missing?, page_source_path?, page_source_truncated?, step_kind?}`，模块保持纯映射、不发 WebDriver 命令。EvidenceDoc 只在设备目标上加 step_kind、顶层 url/url_missing、controls/controls_missing、page_source/page_source_truncated，桌面输出不变。stepEvidenceRef 的跳过规则（无 execution 且无 prompt 就返回 null）加一个设备例外：确定性与导航 step 在 failed 或 error 时也产 evidence，此时 acts 为 []。page_source 文件的 URI 用 refFor 算，字节进 screenshots 回传列表、走后台队列。写盘改用新的脱敏出口（0051 决策 8，0052 决策 7（evidence 输入），0042 决策一）
- `engines/midscene/src/worker/error-text.mts` · oneLineError：redactUrlUserinfo 换成新的脱敏出口，顺序保持「先脱敏再截断」（截断可能切在查询参数中间）（0051 决策 11）
- `engines/midscene/src/lib/artifact-upload.mts` · ArtifactUploader（基本不改）：page_source 文件复用 refFor 加 enqueue，device-session.json 复用 toReportRef。不新增上传时机，只核对 page_source 进入整目录 flush 的根（0051 决策 8）
- `engines/midscene/src/device/session.mts（新）` · Device Farm 会话：执行期唯一构造 DeviceFarmClient 的地方：region 固定 us-west-2，maxAttempts=1，每次调用显式 abortSignal 超时。负责设备列举（完整分页、静态过滤、版本族按点分段匹配、排除 BUSY 与 TEMPORARY_NOT_AVAILABLE、排序）、Create、Get、Stop、按名 List（带 nextToken）。获取预算内手写退避，停止信号可穿透。维护待清理集与待核尝试；只有按名列举命中才能消除待核。Stop 规则只有一条：仍是 RUNNING 才发 Stop，确认只认 STOPPING 或 COMPLETED，Stop 报错就补查一次 Get。发 session_opened 与 session_closed，带 observedS 和 providerMinutes。会话年龄到达 max_session_s 时触发后备路径。可复用 spike 里的 startSession、stopSession、releaseProbe 原语，但要去掉其中的 15 分钟和 5 分钟轮询字面量（0052 决策 3，0051 决策 2、3、4、5、7、10）
- `engines/midscene/src/device/session-name.mts（新）` · 会话名编解码：格式 `gherkai:<run_id>:<sha256(scope_id) 前 16 位十六进制>:<尝试序号>:<scope_id 百分号编码>`。总长上限 256，超长只截最后一段；按整名相等匹配（0051 决策 3）
- `engines/midscene/src/device/appium.mts（新）` · Appium 建连与上下文切换：建连、执行、探测各用一个 WebdriverIO 实例，超时分别设置：建连实例的 newSession 超时不小于 4min+65s、以剩余获取预算封顶、传输层 0 次重试；执行实例 connectionRetryCount=0；探测实例自带 5s 短超时。logLevel 固定为 error。caps 显式设 newCommandTimeout、appium:autoLaunch:false，应用目标设 appium:app 为预签名地址。网页上下文每次重新定位：只认 WEBVIEW_<pid> 与 CHROMIUM，单候选才采用，多候选或零候选按决策 5 处置。提供 withWebContext 和读当前上下文。newSession 的瞬时失败只重试 newSession；拒装驱动辅助包时换一台重建，至多一次（0052 决策 3、5、6，0051 决策 3、9）
- `engines/midscene/src/device/guard.mts（新）` · 命令守卫：会话级的 driver 代理（Proxy），交给 Midscene 界面、内建导航与确定性 handler 的都是它，不暴露裸客户端。维护执行令牌：step 开始时发出，step 结束、取消或进入终结时立即撤销。维护结果未知标志：置位后本 step 内一切有副作用的命令被拒绝，只读白名单放行。白名单按原语列（截图、上下文列表、page source、已确认网页上下文中的读地址、/status、deviceScreenInfo），只对网络错误码与 502、503、504 重试 1 次。结果未知时置标志、abort 当前 act，再查一次会话状态：非 RUNNING 归 session_lost，RUNNING 归 engine_error 并使用 ADR 规定的消息。元素句柄、解构出的方法、晚到的回调同样受令牌约束（0052 决策 6（命令守卫、结果未知、执行期关闭重试），0051 决策 12，0050 决策 2）
- `engines/midscene/src/device/probe.mts（新）` · 能力探测：建连后、预热前执行一次。网页上下文（只对网页目标）判为三类：提供、不提供、探测出错。判据是在 5s 预算内经独立探测实例成功执行一条只读命令，有界重试一次，按证据性质归类。spike 里的 usableWebCtx 用 Promise.race，这正是 ADR 拒绝的方案，不能照搬。另外取 iOS 输入路线、坐标比例（iOS 读 deviceScreenInfo.scale，失败时按截图长边除以窗口长边取整回退；Android 为 1）、/status 的 Appium 版本、候选数。只缓存结论，不缓存句柄；结论写进 device-session.json 与 worker 日志（0052 决策 5、7（DPR 回退规则自写））
- `engines/midscene/src/device/adapters/uiautomator2.mts 与 xcuitest.mts（新）` · 驱动适配器：按会话回报的 automationName 选一次。原语映射照 0052 决策 4 的表：点击、长按、滚动用 mobile: swipe 与 scrollGesture，不用 W3C 指针拖动；输入在 Android 用 mobile: type，iOS 对活动元素 sendKeys，所在上下文由探测定，不用 POST /keys；按键与主屏；iOS 坐标按点（像素除以比例）；导航按探测结论走 url 或 mobile: deepLink。从控件树抽取控件摘要 items[{type,id,text,a11y_id}]、total、truncated，只在 failed 或 error 时调用。`mobile:` 命令不得出现在这两个文件之外。spike 里 AppiumInterface 的 typingRoutes 多路线试错与 swipe 回落都不能保留（ADR 拒绝运行期试错回落）（0052 决策 1、4、6）
- `engines/midscene/src/device/interface.mts（新）` · 界面实现：AppiumInterface extends AbstractInterface：实现截图（原生上下文）、尺寸、defineActionsFromInputPrimitives 动作集，原语全部经适配器与守卫下发。系统版本与机型只经唯一的会话能力读取点进入诊断。spike 里的 class AppiumInterface 是原型，要去掉其中的 PLATFORM、SCENARIO 全局分支（0052 决策 3、7）
- `engines/midscene/src/device/app.mts（新）` · 应用启停：建会话前对应用键做存在性检查，404 与 403 都记 precheck_failed，消息不同；对键预签名。建好后 activateApp 并采样应用状态，回到「未运行」即 precheck_failed。为句柄上下文的 `app.restart()` 提供 terminate、activate、采样三个原语，采样到自退记 engine_error（0052 决策 3，0051 决策 9、14）
- `engines/midscene/src/device/warmup.mts（新）与桌面实现中的预热` · 会话预热：设备上按探测结论选 url 或 deepLink，导航 GHERKAI_SESSION_WARMUP_URL 一次，再在原生 page source 里找标记：READY 即就绪；DENIED 或 AUTH REQUIRED 归 precheck_failed；ERROR 或无任何标记时原地重导航、有界重试，耗尽归 engine_error，永不归 network_error。桌面用 page.goto 读响应状态与标记。预热地址只经脱敏出口进入诊断。可复用 spike 的 navigateTo、waitMarkers、nativeMarkers 结构（0052 决策 6（预热），0051 决策 13）
- `engines/midscene/src/device/surface.mts（新）` · 设备侧接缝实现：串起解析 → Create → 等 RUNNING → 存在性检查与预签名 → newSession → activateApp 与采样 → 探测 → 预热，全程受获取预算约束，到期归 acquire_timeout；完成后 run-scope 才发 scope_started，sessionId 填会话 ARN。实现 step 前核对、复原核对（命令失败先查会话状态）、快照（按条件读地址；在原生上下文取控件与 page_source）、取确定性句柄 ctx{driver, device{platform,osVersion,scale}, uiKind, appId, app{restart}, log, withWebContext}（0052 决策 2，0051 决策 4，0050 决策 2）
- `engines/midscene/src/worker/deterministic.steps.mts` · 内建导航条目加 webdriver 句柄：应用目标经 DeepLink（0048 决策 7），网页目标按能力探测择路（0052 决策 4）；不注册「重新启动应用」与「页面地址匹配」（产品不内置有措辞的 step，0020 第 2 条），两者的示范进 steps/ 模板，重启经 ctx.app.restart()（0050 决策 1、2）
- `tools/（新，真机重新探测工具）` · 如 tools/device_reprobe.mts 或 .py 包装：在真实会话里逐项执行探测与原语，生成能力矩阵，并与 adapter 和 probe 测试 fixture 做差集。这是长期资产，注释守悬空指针红线（0052 决策 8）
- `engines/midscene/DEVELOPMENT.md、CONTRIBUTING.md` · 真机验收矩阵、设备模块说明：写明人工触发的真机验收矩阵：Android 加两代 iOS、网页加应用、故障演练、iOS 26 整链路单列一行，列为发版后验证项。DEVELOPMENT 补设备模块的划分与动态加载约定（0052 决策 8）

**先写的护栏测试**

- `engines/midscene/src/device/guard.test.mts`：用假 driver 断言以下调用都被拒：带旧令牌的调用、step 结束后保留的代理引用、解构或先取后调的方法引用、缓存的元素句柄、await 之后晚到的回调、进入终结后的调用、结果未知置位后的有副作用命令（click、type、execute('mobile: tap')）。只读白名单在结果未知后仍放行；白名单只对网络错误码与 502、503、504 重试 1 次，对超时和 500 不重试；有副作用的命令任何情况都不补发（0052 决策 6、8（命令守卫护栏））
- `engines/midscene/src/device/adapters/adapters.contract.test.mts（加快照 fixture）`：两个适配器对每个原语（tap、longPress、scroll、typeText、keyboardPress、home、navigate 的两条路线）发出的命令名与参数形态和快照完全一致；iOS 坐标是像素除以比例；Android 输入只发 mobile: type；iOS 不发 POST /keys，也不用 W3C 指针拖动（0052 决策 4、8（命令契约快照））
- `engines/midscene/src/device/read-points.test.mts`：差集护栏：在 src/device 与 src/worker 下 grep，`mobile:` 只出现在 adapters/ 下；系统版本与机型字段（platformVersion、osVersion、deviceModel 等）只在会话能力读取模块里读，且读出的值只流向诊断；new DeviceFarmClient 只出现在 device/session.mts；src/ 中 webdriverio 与 client-device-farm 的静态 import 只出现在 src/device/ 下（0052 决策 1、3、8（读取点），0051 决策 10）
- `engines/midscene/src/device/probe.test.mts`：归类真值表（假 driver）：重试后候选仍为零 → 不提供；有候选、切得进，只读命令超时而原生只读命令正常 → 不提供；列上下文本身失败或传输层错误 → 探测出错；原生只读命令也失败 → 先查会话状态，丢失则归 session_lost；原生应用会话里出现 WEBVIEW_chrome 不算候选；应用目标不探测网页上下文。另断言探测使用独立的短超时客户端实例，而不是 Promise.race；比例读取失败时按 DPR 回退规则计算（0052 决策 5）
- `engines/midscene/src/device/web-context.test.mts`：withWebContext 与设备上的导航：多候选与零候选（短等待后再列一次）都记 engine_error，并使用 ADR 原文消息，能力结论不翻转；fn 执行中句柄失效不在 fn 内重试。为 evidence 读地址时，多候选或零候选只把 url 置 null，url_missing 记 error 或 timeout，step 判定不变；能力结论为「不提供」时绝不调用 url（0052 决策 5）
- `engines/midscene/src/worker/run-scope.test.mts（新增 step 顺序契约组）`：用记录调用序列的假接缝断言：step_started → preStep → 执行 → 读地址（只在要产 evidence、目标是网页、结论为「提供」时） → restore → 控件采集（只在 failed 或 error） → evidence → step_done → enqueue。preStep 失败时 handler 与 AI 都不被调用，记 engine_error；restore 失败时最终判定为 error，原判定写进 message；restore 期间会话丢失归 session_lost；requires:web_context 遇「不提供」记 capability_unavailable、遇「探测出错」记 engine_error，都不调 handler、不转 AI。桌面接缝下的事件流与现有测试逐字节一致（回归）（0052 决策 2，0050 决策 1、2）
- `engines/midscene/src/worker/run-scope.test.mts（事件序列与退出码组）`：执行前失败：scope_started 之前只有 session_opened 与 session_closed，然后发 scope_done{status:'error', errorType}，没有任何 scenario 或 step 事件，退出码 0。session_lost：当前 step error、余下 step_skipped（shortcircuited）、scenario_done error，后续 scenario 零事件，最后 scope_done{status:error, errorType:session_lost}。结果未知后存活探测失败：下一条 scenario 不发 scenario_started，先查会话状态，非 RUNNING 发 scope_done{error, session_lost}、否则发 scope_done{error, engine_error}。设备路径的退出码只会是 0 或 1，永不出现 80；有 unconfirmed 会话或 attempted 尝试时退出码为 1。收到额外请求头却没有预热地址：桌面与设备都记 precheck_failed（0051 决策 4、5，0052 决策 6，0051 决策 13）
- `engines/midscene/src/device/finalize.test.mts`：假时钟下断言：四个阶段各自的截止线；SIGTERM 路径不调 deleteSession；正常路径的顺序为 destroy → 上传 → deleteSession → 核对 → 释放 → session_closed → scope_done → 排空；每个真实会话按 ARN 去重、恰有一条 session_closed，不会先 unconfirmed 再补 confirmed；待核尝试只发一对 attempted 事件；信号重复到达、超时与信号交叠时只进入一次四阶段；只有状态为 RUNNING 才发 Stop；Stop 报错后补查 Get；确认只认 STOPPING 或 COMPLETED；进入终结的那一刻撤销令牌并 abort act（0051 决策 5）
- `engines/midscene/src/device/session.test.mts`：版本族匹配：'18' 命中 18.x.y，'18.1' 不命中 18.10，写全段即精确匹配。选择顺序：先排除 BUSY 与 TEMPORARY_NOT_AVAILABLE，再按版本号降序、HIGHLY_AVAILABLE 优先、ARN 字典序。零候选重列一次仍为零 → precheck_failed，消息带最接近的可用版本。Create 结果未知只能由按名列举命中来消除，列举为空不构成排除；分页没扫完视为未核对。换台至多一次，剩余预算不足 150s 不再换台，被替换的会话先 Stop。observedS 的起止点正确，缺失记 null 而不是 0（0051 决策 3、7）
- `engines/midscene/src/device/session-name.test.mts`：名字格式与段序正确；scope 哈希是 SHA-256 前 16 位十六进制；A-Z a-z 0-9 . _ - 之外的字符按 UTF-8 字节百分号编码；总长超过 256 时只截最后一段，其余四段永不截断；按整名相等匹配，同一 run 内不同 scope 不互认（0051 决策 3）
- `engines/midscene/src/worker/redact.test.mts（共用跨语言 fixture，与 core 和 Nova 同一组用例）`：签名类查询参数与 gherkai_tunnel_token 的值被替换成 ***，`&` 与 `&amp;` 两种形态都覆盖；UND_ERR_CLOSED 错误文本里的整条端点地址被盖住；userinfo 旧用例不回归；经 log()、event-sink、evidence、device-session.json、page_source 五个出口的输出都不含签名（0051 决策 11，0035 决策 5）
- `engines/midscene/src/worker/no-device-deps.test.mts`：起子进程执行 --capabilities 与桌面 job（用 --import 钩子记录被解析的 specifier），断言 webdriverio、@aws-sdk/client-device-farm、src/device/*（limits.mts 除外）都没有被加载；min_grace_s 由常量推出、约 64 且小于 120；max_session_s 由常量推出（0052 决策 3（动态加载），0049 决策 4、5）
- `engines/midscene/src/device/warmup.test.mts`：标记归因：READY 即就绪；DENIED 或 AUTH REQUIRED 归 precheck_failed；ERROR 或预算内无标记时有界重试，耗尽归 engine_error；任何情形都不归 network_error。导航路线由探测结论决定。标记字符串与隧道侧预热页模板共用同一份 fixture（0051 决策 13，0052 决策 6）
- `engines/midscene/src/worker/evidence.test.mts（加组）`：传入快照时设备键正确落位；设备上 failed 或 error 的确定性与导航 step 产出 acts:[]，step_kind 正确，passed 的不产；桌面 evidence 不出现任何新键（与现有 fixture 逐字节一致）；page_source 的 URI 由 refFor 算出，路径进入回传的入队列表（0051 决策 8，0042 决策一）

**完整性审查补认领**

- 应用目标上的导航 step（0048 决策 7，deepLink spike 已定）：导航判据为 Given / When 后整句是一个地址，应用目标接受任意 scheme；Android 发命令前按 RFC 3986 校验并拦 ; ' ( )，deepLink 带 package，报 unable to resolve Intent 记 capability_unavailable，成功后轮询前台包名；iOS 带 bundleId、成功即已送达；首次遇到 WebDriverAgent 不支持打开地址即缓存为设备不支持；前台应用查询进只读白名单。护栏测试：字符集校验用例（含 | ; 截断风险的字符）、三种失败情形的归类、缓存只记能力否定。
- 红线测试补：scenario 前核对在第一条 scenario 前不调用、年龄恰到边界、探测成功后下一条照常执行、失败按会话状态分流 session_lost / engine_error；释放与 session_closed 先于 scope_done；安装包 HeadObject 回 404 或 403 时 Create 零调用（存在性检查必须排在建会话之前）。
- 设备模块的两条护栏测试：系统版本与机型只经会话能力对象的唯一读取点进入；两个驱动适配器的命令契约快照。Device Farm 客户端只在 TS 设备模块构造的断言。0052 决策 8、0051 决策 10。
- 接缝第四项边界义务「scenario 前核对」（本轮补进 0052 决策 2）。
- 真跑核对：一次故意建连失败的真机执行，核对报错文本里的路径令牌与签名已被盖住。0051 决策 11。

**真跑或对抗核查才算数的结论**

- 全新会话、尚未导航时的探测时机：iOS 15.8、18.6 Safari 与 Android Chrome 刚建好会话时是否已有 WEBVIEW_<pid> 或 CHROMIUM 候选。若首次导航前候选为零，探测会把 iOS 15.8 判成「不提供」，转去走它不支持的 deepLink，导致预热失败。这一点 mock 证明不了
- iOS 26 整条链路：探测超时 → 恢复原生上下文 → deepLink → READY，在真机验收矩阵里单列一行
- 预热三个失败分支各真实触发一次：边缘拒收 cookie、校验 401、请求失败
- 执行实例 connectionRetryCount=0 时，真实点击或输入在客户端超时后不被重复执行；结果未知处置后的截图存活探测；多个客户端实例的超时在同一会话上各自生效
- Midscene 1.15.1 用真实的 Agent 加自写 AppiumInterface 时，适配器抛错并置 abortSignal 后，act 立即结束、零后续动作（spike 只用假界面验过）
- SIGTERM 落在各阶段的表现：Create 在途、PENDING_CONCURRENCY 排队、释放中网络退化；终结四阶段在 Fargate stopTimeout 下能否收完，约 64s 是否够用，要在网络退化条件下校准
- 进程级兜底：newSession 客户端超时触发 unhandledRejection 后能进入终结，会话不泄漏
- 脱敏：故意建连失败一次、外部 Stop 一次（制造 UND_ERR_CLOSED），核对 stderr、事件、evidence、device-session.json 中的签名都已盖住
- session_lost 的两条路径：外部停止会话；会话年龄后备（可在测试构建里注入较小的年龄上限），以及 150 分钟边界上端点拒绝命令而 API 仍报 RUNNING 的情形
- 应用分发：预签名 S3 地址配 appium:app 加 autoLaunch:false，再 activateApp、采样，以及换台重建；task role 下 HeadObject 缺失键返回 404
- 获取预算 600s 在并发排队与换台重建下是否够用，实施期校准
- --capabilities 在容器镜像里不加载设备依赖、启动耗时不回退
- 桌面路径在接缝搬移和新增桌面预热之后，用 tools/e2e_harness.py 在本机与云端各真跑一次，对照事件与 evidence 无回归
- 真机验收矩阵：Android 加两代 iOS，网页加应用，加故障演练

**易错点**

最容易做错的四件事：
（1）桌面接缝必须是现有代码的原样搬移。makeGuardedCleanup 的重入语义、建连重试与退出码 80、cleanup 先于提前上传、排空的顺序，都要用现有 run-scope 测试与真跑回归钉住。设备差异只能落在接缝实现里，不能在 runStep 或 scenario 循环里写 `if (device)`。桌面唯一的新行为是预热，以及「有额外请求头却没有预热地址」时记 precheck_failed，它会走新的 scope_done{status:error} 出口，不再走 throw 退出码 1。
（2）spike 06 的原语可以借，但其中三处正是 ADR 的被拒方案，照抄就会违背决策：usableWebCtx 用 Promise.race 放弃挂住的命令；typingRoutes 和 iosSendKeys 在运行期多路线试错回落；scroll 在 mobile: swipe 失败后回落到 W3C 指针拖动。此外 PLATFORM 与 SCENARIO 全局分支、logLevel 'warn'、缺省的传输层重试也都要去掉。命令守卫必须是 Midscene 界面、导航与 handler 拿到的唯一句柄；令牌在 step 结束或进入终结的那一刻撤销，不能等到下一个 step。
（3）动态加载与常量分层：--capabilities 要输出由设备常量推出的 max_session_s 与 min_grace_s，所以这些常量必须放在不 import 任何 SDK 的 limits 模块里，否则「能力自述零依赖」会被悄悄打破。Device Farm SDK 现在仍在 devDependencies，要移到 dependencies（webdriverio 已在 B4 移入），并用 npm 10 重算锁文件。
（4）log() 现在不脱敏，而 WebdriverIO 会把整条带签名的端点地址写进错误文本。stderr、bin 的 fatal 行、device-session.json、page_source 都要经同一个脱敏出口。参数名集合待定（见 open_questions），三份实现要同步改。

另外两点：
- 「真实 IAM 角色闭环」在最近一次提交（3739ce5）里已经按表建角色逐项核过。本批真跑前还剩一项要复核：经 worker 代码路径走一遍 HeadObject 缺失键返回 404 与预签名。
- 建议先写 guard、session-name、probe、step 顺序这四组测试，再动 run-scope；open_questions 第一条（scenario 前钩子）会改变接缝形状，最好在开工前定下来。

