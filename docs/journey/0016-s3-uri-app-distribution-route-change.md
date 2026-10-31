> 类型: 调查记录

# 移动真机支持（1.5）：应用分发改走 `s3://` 加项目角色的触点清单与待拍板问题

> 状态（2026-10-31 晚）：owner 倾向改走 `s3://` 加项目角色，但「安装方式」与「`appium:version`」两项决定要当面讨论后再定；在此之前**不动** ADR 0051 决策 9、10 与相关代码，也不开新的实质工作。本文是讨论材料与接手现场：事实、触点、问题与建议。吸收去向：决定后进 ADR 0051（决策 9、10、实测依据、被拒方案）、0033（资源清单与权限表）、0052（决策 3、8）、0053（本机后端前提）与 CONTEXT.md，吸收完即删。

## 1. 已确认的事实

- **Android 应用目标安装失败的根因已修正并提交**（ADR 0051 决策 9、实测依据「应用标识能力与下载」行；ADR 0052 决策 3）：`appium:app` 与 `appium:appPackage` 同发时 Device Farm 端点跳过下载却改写路径。修正后 Pixel 8a 与 iPhone 14 的应用目标经 `tools/device_reprobe.mts` 按生产路径重走通过。Codex 第 75 到 77 轮已闭合。
- **`s3://` 加项目角色两平台实测可用**（ADR 0051 实测依据「S3 URI 加执行角色」行）：角色信任 `devicefarm.amazonaws.com`、最长会话 9000 秒、只授 `apps/*` 的 `s3:GetObject`；Appium 服务端 2 与 3 都装成；桶在 us-east-1、Device Farm 在 us-west-2 跨区域无碍；无角色时 Android 报「Cannot access an S3 URI without an IAM role」（iOS 无角色、角色缺权限两种报错文本未测）。
- **官方契约**（Device Farm 开发者指南「Interacting with the device using Appium」「Access AWS resources using an IAM Execution Role」「Supported features and versions」）：远程地址形态只有公网 HTTPS 与 `s3://`；本机路径不支持；`installApp` 在不支持命令清单里；角色须与调用方同账号、信任 `devicefarm.amazonaws.com`、最长会话不短于项目 job timeout（默认 150 分钟），设置它的调用方要 `iam:PassRole`；远程访问会话 API 没有角色字段，只能继承项目级配置；`appium:version` 是建会话的 `configuration.parameters`，可选 2 或 3，两者都支持全部 Android 与 iOS 15 以上，iOS 27 起必须显式给、否则旧设备默认 2。
- **现行预签名路线仍可用**：去掉 `appium:appPackage` 后预签名地址同样装成；它在官方契约里属于「公网 HTTPS 地址」的形态。

## 2. 讨论材料

**`appium:version`**：Device Farm 会话参数，选该会话主机上运行的 Appium 服务端大版本。实测传 3 得到 3.1.0，能力集在 2 与 3 下都能建连。建议一律显式传、值先定 `"2"`：1.5 的适配器、探测、超时与耗时基线都在 2.11.5 上校准；Appium 3 删除了一批旧版端点（worker 应用启停用的 `activate_app` / `terminate_app` / `app_state` 跨平台端点在风险名单上，需改走 `mobile:` 扩展命令），未审计前不切；显式传 2 同时满足 iOS 27 的硬要求、不受「预选版本可能变化」影响。升 3 作为独立后续：审计端点清单、真机核一轮、ADR 0052 决策 8 的触发条件改为覆盖「2.x 次版本变化」与「主动切 3」两种。worker 目前不传此参数，iOS 27 设备会被拒。

**`appium:appPackage`**：UiAutomator2 的能力，值是被测应用的包名，作用是告诉驱动被测应用是哪个（没有安装包时据此启动与等待）。来历：10 月中 spike 发现不带包名与活动名时 Wikipedia 的自动启动失败（启动器 intent 匹配多个活动），记的办法是「关自动启动，或给齐包名与活动名」；落生产时两样都做了，包名一项属于保险式叠加。Device Farm 端点把它当成「用已安装应用」路线的信号而跳过下载，10 月 14 日成功的请求恰好没带。现在包名只作 `activateApp` / `terminateApp` / `queryAppState` / DeepLink 的命令参数。

## 3. 触点清单（改走 `s3://` 时要动的面；按子系统；指针为 repo 相对路径）

### 3.1 Midscene worker（engines/midscene/src/device）

| 位置 | 现状 | 改动 |
|---|---|---|
| `app.mts` 模块头第 2 步、节标题「存在性检查与预签名」、`AppObjectStore.presign`、`presignAppObject`、`s3AppObjectStore().presign`、`PRESIGN_INTERCEPT` / `UNSIGNED_PAYLOAD` / `InterceptedRequest` / `presignGetObject` / `escapeQueryPart` / `formatUrl`、导入 `GetObjectCommand` / `SignatureV4` / `Sha256` / `APP_PRESIGN_EXPIRES_S` | 预签名的全部符号 | 全删；存储端口只留 `head`；`s3://<bucket>/<key>` 由桶与键拼出、不发 I/O（放 app.mts 还是接缝待定）。`APP_OBJECT_FORBIDDEN_MESSAGE` 说的是 worker 身份，仍准确 |
| `limits.mts` `APP_PRESIGN_EXPIRES_S` 与文件头单位说明 | 3600 秒 | 删；文件头去掉「S3 预签名」。`appium:version` 若作常量，不属于预算类，放 session.mts |
| `surface.mts` 导入、`ConnectRequest.appUrl` 说明、`acquireSteps` 第 1 步（校验与 HEAD）与循环内的预签名调用、`DeviceFarmSessions` 端口（五方法）、`DeviceParts.appStore` | 每轮循环重做预签名；预签名异常落 `engine_error` | 地址拼接挪到循环外；GetProject 核对角色放第 1 步 HEAD 之后、循环之前（零会话费用），经新端口方法返回 Outcome 才能归 `precheck_failed`；`appUrl` 语义改为非凭证 |
| `appium.mts` `newSessionCapabilities` docstring 与模块头「端点与预签名地址是凭证」、`newSessionFailureKind` / `newSessionRejectedMessage` | 代码逻辑不变；S3 角色类报错会落 rejected 并套用「请换一台设备」 | 去掉「预签名」措辞；为角色类报错文本加标记与专用消息（文本待实测） |
| `session.mts` `DeviceFarmApi`（五种调用）、`createRemoteAccessSession` 的 `configuration`、`sendCreate` 的 input、`create` 的拒绝分类 | 只传 `billingMethod` | 加 `parameters: {"appium:version": "2"}`；加 `getProject(projectArn, abortSignal)` 读 `executionRoleArn`（SDK 3.1150.0 有 `GetProjectCommand`，`Project.executionRoleArn`）；注释与测试标题「五种」改六种；因设备上没有所选版本被拒的归因（指定 ARN 时会误报成设备 ARN 问题）待定 |
| `lib/job-source.mts` `JobApp` / `JobDeviceRequest` / `JOB_KEYS` | 已带 bucket、key、projectArn | 不改（除非 `appium:version` 由 Job 下发） |
| `parts.mts` 缺省装配 | `s3AppObjectStore()`、`createDeviceFarmSessions(env)` | 不改 |
| 测试：`app.test.mts` 预签名整节与辅助函数；`surface.test.mts` 假 `appStore.presign`、`appium.connect:…:presigned` 记号、次序断言；`appium.test.mts` `PRESIGNED` 样本与消息不含签名的断言；`session.test.mts` `FakeFarm` 入参、Create 请求体 deepEqual、「五种调用」用例；`web-context.test.mts` / `guard.test.mts` 的假 parts 与 `appUrl`；`wdio-log.test.mts` 的预签名样本（测通用掩码，可留） | 都假定预签名 | 改为 `s3://` 形态；加 GetProject 的假方法与次序断言；可加「Cannot access an S3 URI without an IAM role」的分类用例 |
| `lib/redact.mts` `QUERY_SECRET`、`lib/agentcore-sigv4.mts` 与 package.json 的 `@aws-sdk/signature-v4` / `@aws-crypto/sha256-js` / `@aws-sdk/protocol-http` | 通用脱敏与 AgentCore 签名仍在用 | 不改、不删 |

### 3.2 deploy 与权限（deploy_aws、runtime、iac）

| 位置 | 现状 | 改动 |
|---|---|---|
| `runtime/gherkai_runtime/devicefarm.py` `resolve_or_create_project` / `verify_project` / `_project_exists` | CreateProject 只传 name；GetProject 返回体被丢弃 | UpdateProject（或 CreateProject 带 `executionRoleArn`）只能写在这里（`runtime/tests/test_devicefarm_client_placement.py` 护栏）；暴露 `executionRoleArn` 供 deploy / diff / doctor 核对 |
| `deploy_aws/gherkai_deploy_aws/cli.py` `Provider.deploy` 次序、`_resolve_device_farm_project_for_deploy`、`_device_farm_denied_warning` 的权限串、`diff` / `destroy` / `_stored_device_farm_project` | 项目在 cdk 之前解析；cdk 之后只有 worker 镜像步骤（退出码 1、重跑收敛）；无权限警告列三项动作；destroy 保留项目、删 SSM 参数 | UpdateProject 放 cdk 之后；权限串加 `devicefarm:UpdateProject` 与对角色的 `iam:PassRole`；被拒时的降级或退出、已有别的角色时覆盖与否（Q2、Q3）；diff 若要看见角色需 `verify_project` 返回字段 |
| `deploy_aws/gherkai_deploy_aws/stack.py` `_task_definitions`（现 7 个 IAM 角色，含确定性命名先例 `{prefix}timeout-scheduler`）、`_grant_midscene_devices`（恰 6 个 devicefarm 动作）、`_grant_task_role`（整桶 GetObject）、`_storage`（产物桶 SSE-S3）、`_ssm_device_farm` | 无信任 `devicefarm.amazonaws.com` 的角色 | 新增角色（信任、`max_session_duration` 9000 秒、`s3:GetObject` 到 `arn:aws:s3:::{prefix}artifacts/apps/*`）；worker 核对角色则加 `devicefarm:GetProject`（项目 ARN）；task role 的 GetObject 保留（HeadObject 要它）；桶是 SSE-S3、角色不需 kms |
| `deploy_aws/tests/test_stack.py`（角色数 7、devicefarm 授权逐条锁定、SSM 全集）、`test_provider.py`（context 闭集） | 按现状锁定 | 角色数、授权行、新角色的信任主体 / 时长 / 资源断言；角色 ARN 若经 context 或 SSM 传递则改闭集或全集 |
| `deploy_aws/DEVELOPMENT.md` SSM 参数族条、Midscene 设备权限条、模块分工表 | 无角色 | 同步 |

### 3.3 CLI、本机后端、doctor、agent skill

| 位置 | 现状 | 改动 |
|---|---|---|
| `cli/gherkai_cli/device_selection.py`、`submission.py`（`complete_local_definition` 「仅有的两步 AWS 操作」）、`__main__.py` `_add_device_flags` help | 本机路径零 AWS 前置；项目与桶三层来源 | 按 Q5：不加提交时核对；help 可加一句前提 |
| `__main__.py` `_cmd_doctor` 本机段、`_doctor_devices` 云端段（devices.project、devices.sessions 两行） | 本机不做设备检查、承诺不需要凭证；云端不看角色 | 按 Q5：云端加一行报告项目是否配角色（提交者权限加 GetProject）；同步 `docs/user-guide/troubleshooting.md` 行表与 `cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md` 项名枚举（受 `cli/tests/test_skill.py` 护栏） |
| `runtime/gherkai_runtime/app_upload.py`、`names.py` | 使用方桶、`apps/` 前缀、us-west-2 常量 | 不改；角色策略资源由 `APP_OBJECT_PREFIX` 推出 |
| `cli/gherkai_cli/skills/gherkai/references/engines.md`「设备选择」条、`setup-and-diagnosis.md` precheck_failed 条 | 无角色前提 | 加前提与症状 |

### 3.4 用户文档与词表

| 位置 | 现状 | 改动 |
|---|---|---|
| `docs/user-guide/configuration.md` `[devices]` 与 `[apps]` 段 | 无角色、IAM、KMS 说明 | 写本机应用目标前提：项目配角色（信任、9000 秒、`apps/*` 的 GetObject、同账号、设置需 PassRole）、信任与权限策略模板、UpdateProject 命令；SSE-KMS 桶角色还需解密权限（未实测） |
| `docs/user-guide/cloud-backend.md` 部署机凭证范围、「后端包含什么」、拆除与清理、排障表 | 部署方只列 ListProjects / GetProject / CreateProject | 加 UpdateProject 与对角色的 PassRole、降级说明、角色生命周期（随 stack 删除、项目保留而悬空、同 prefix 重部署复原） |
| `docs/user-guide/troubleshooting.md`、`running-and-results.md` 权限梯级表、`getting-started.md` 开通表、`local-app-testing.md` 脱敏说明「S3 预签名地址」 | 无角色症状与前提 | 加症状行；本机设备与应用目标前提选一页落位；脱敏措辞改为泛指带签名的地址 |
| `CONTEXT.md` | 无「应用桶」「安装包读取角色」词条；「执行角色」已被 ECS task execution role 占用 | 按 Q7 立条，冲突形态进 `_Avoid_` |

### 3.5 ADR 原文

| 位置 | 改动 |
|---|---|
| 0051 背景「端点地址本身是凭证」条、决策 3「创建与重试」（加 `appium:version`）、决策 4 错误表（新增「项目未配角色 / 角色读不到对象」形态）、决策 9 全部（地址形态、前提、签名条措辞限定、KMS 主体、吞吐数据注明路线、「不做」加预签名）、决策 10（角色由谁建、UpdateProject 时机与失败处置、diff、destroy、本机后端、权限登记加主体与动作）、决策 11 两处「预签名地址」措辞、实测依据「上限」行指代、「S3 安装」「安装吞吐」行注明预签名路线、「S3 URI 加执行角色」行补支撑决策 10、新增 UpdateProject / PassRole 的真实角色闭环行、被拒方案加「预签名 HTTPS」并重写「上传 API」条理由 | 原地改写（Q8），Status 头不动 |
| 0052 决策 3（地址形态；`appium:version` 不是能力集、要说明区别）、决策 5「Appium 版本取自 /status」加注请求的主版本、决策 8 验收触发条件 | 同步 |
| 0033 资源清单 IAM 小节加角色条目（措辞与第 9 条 ECS execution role 区分）、「设备目标增量」部署方加 UpdateProject 与 PassRole、task role 表加 GetProject（若核对）、GetObject 行用途补 HeadObject、RETAIN 段写角色生命周期、Status 摘要 | 同步；新增行按 0033 的规矩用真实角色重做闭环 |
| 0035 决策 5 动机与规则 ② 的两处理由（删「预签名地址」、「诊断预签名地址过期」） | 规则与名单不动，只改理由 |
| 0053 决策 3 本机后端条加角色前提、`[apps]` 括注改为与 0051 决策 9 一致的理由（命令参数）、边界互链 0051 条的「预签名」 | 同步；`[apps]` 括注这一处与路线无关、属旧描述漂移，可随本批先改 |
| 0048 Job 字段、0042 evidence 脱敏注释、0016 / 0029 的报告预签名 | 不改 |

## 4. 待拍板问题（附建议）

1. **云端角色由谁建、归谁管**：(a) BackendStack 资源随 stack 销毁；(b) stack 资源但 RETAIN；(c) cdk 之前用 SDK 建。建议 (a) 加确定性命名（如 `{prefix}devicefarm-app-reader`）：悬空指向在同 prefix 重部署时自动复原，拆除须知加一句。
2. **UpdateProject 时机与失败处置**：只能在 cdk 之后。建议权限被拒走降级（警告写明缺 `devicefarm:UpdateProject` / `iam:PassRole` 与后果，退出码 0）；限流与 5xx 同 worker 镜像步骤（退出码 1、重跑收敛）；项目已配同一 ARN 时不发调用。
3. **项目上已有别的角色**：建议覆盖并警告列出被替换的 ARN（`{prefix}devices` 归 deploy 管理、配置收敛到期望值）。
4. **worker 建会话前是否 GetProject 核对角色**：建议核对，只对应用目标、放 HEAD 之后，缺角色归 `precheck_failed`、消息按后端分流；GetProject 自身失败尽力而为（记日志、跳过、交 newSession 兜底）；角色配了但权限不对由 newSession 报错文本归类、专用消息指向角色权限。代价：Midscene task role 与本机 QA 机器加 `devicefarm:GetProject`。
5. **本机后端如何配角色**：建议只给文档与模板；提交时不加核对（0053 被拒方案继续成立）；本机 `doctor` 维持不需凭证；云端 `doctor` 加一行报告角色。
6. **`appium:version` 取值与位置**：建议写死 `"2"`、放 Device Farm 会话块常量、两种目标一律传；升 3 作独立后续。
7. **术语**：建议「安装包读取角色」（Device Farm 代为读取安装包时扮演的 IAM 角色，配在 Device Farm 项目上），`_Avoid_` 执行角色、Device Farm 角色；顺手立「应用桶」。
8. **ADR 改写方式**：建议原地改写 0051 决策 9、10 与 0033 相关段；「预签名 HTTPS」进被拒方案，理由按选择性口径（地址是凭证、三层脱敏与有效期校准、下载身份与 worker 身份耦合、官方契约里只是「公网 HTTPS 地址」的巧合形态）；「上传 API」条理由重写（留 30 天副本与第二套状态管理）。

## 5. 施工期要实测再定

- iOS 无角色、角色缺 `s3:GetObject` 时 newSession 的报错文本（归类与文案依据）。
- 信任策略加 `aws:SourceAccount` 条件 Device Farm 是否支持。
- 建会话的调用方（task role、本机 QA 机器）是否也需要对角色的 `iam:PassRole`（用受限角色核）。
- 键里有空格、括号、非 ASCII 时 `s3://` 地址原样还是百分号编码（原样失败则要决定 CLI 上传时规范文件名）。
- 新权限行（UpdateProject、PassRole、GetProject）按 0033 的规矩用真实角色重做闭环；设置角色后再次 deploy 的幂等性。
- 吞吐在 `s3://` 路线下重测一次（现有 6 MB 每秒是预签名路线数据）。

## 6. 不依赖这两项决定、已收尾的事

- Android 应用目标修正（code 与 docs 各两笔加闭合两笔）已提交，Codex 第 75 到 77 轮闭合；全量 npm test 760 通过。
- 真机复验：修正后的生产路径在 Pixel 8a（Android 14）与 iPhone 14（iOS 18.6）应用目标上通过。
- 对照实验的临时资源：us-west-2 临时桶已删、临时角色策略收回只剩应用桶；vfy-devices 项目上仍挂着对照用的临时角色（UpdateProject 不接受空串、CLI 清不掉），路线定了随 deploy 侧接管或在控制台清。
- 待 push：本轮全部提交尚未 push，由 owner 决定。

## 7. 未做（等决定）

- ADR 0051 决策 9、10 与 0033、0052、0053 的路线改写；worker 与 deploy 代码；用户文档与词表；`appium:version` 的传入。
- 真机验收矩阵其余各行（故障演练、预热失败分支、CLI 端到端、Swipe 取舍、等待 RUNNING 期间外部停止）。
