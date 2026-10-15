> 类型: 进度总纲

# 移动真机支持（1.5）：实施进度总纲

分支 `feat/v1.5-mobile-devices`。设计已定稿为 ADR 0048 到 0053（2026-10-15），spike 与方案总稿两份 journey 随之删除；本文只记实施阶段的现场：做到哪、下一步、documenting 清单。实施完成后删除。

## 现场

- 2026-10-15：ADR 0048 到 0053 写成并通过复审；CONTEXT.md 词表加目标、界面类型、应用别名、远程访问会话、驱动适配器、能力探测、确定性 step SDK 七条，旧词条三条改写；ADR 0019 / 0035 / 0036 的 Status 头标部分取代，0022 / 0024 / 0034 / 0042 / 0044 加互链。spike 脚本 `engines/midscene/spikes/06-devicefarm-appium.mts` 保留为真机能力探测的雏形，实施时演化成 `tools/` 下的真机重新探测工具。
- 2026-10-15（续）：定稿后的专家复审与 Codex 同僚复核发现 0051 的事件契约与收尾顺序、预算分层、隧道令牌载体、scenario 间复位、evidence 衔接、Job 形态六处要改。修订方案经六轮同僚复核达成共识、定稿前实测（边缘契约、桌面与四台真机的预热闭环、导航路线、网页上下文身份、Midscene 中止行为、webdriver 超时语义、会话释放、IAM 策略模拟）全部完成，结论已内联进各 ADR 的实测依据。
- 2026-10-15（续二）：按修订方案改写 ADR 完成：0051 整篇重写（决策 1 到 14，新增设备解析与命令守卫、result-unknown、隧道令牌换 cookie）；0024 / 0028 / 0034 / 0031 / 0049 / 0037 就地改写被反转句并加 Status 反向链；0035 / 0052 / 0048 / 0050 / 0053 / 0042 / 0019 / 0033 / 0027 / 0025 按条改写；CONTEXT.md 加设备请求、设备解析、获取预算三条，改隧道暴露、远程访问会话、能力探测、step 证据四条；`docs/internals/cli-json-contract.md` 加法扩展（会话列表、设备计量、新错误类别、`run_meta` 的格式版本与会话预热地址、Job 的 `target` 与 `device_request`、evidence 的设备键、`list-deterministic` 的目标两键、doctor 的设备两项）。修订方案 journey 吸收后删除。
- 实施尚未开始。建议次序：0049（能力自述增键，零风险、可独立发）→ 0048 与 0053（core 的 tag 解析、Job 字段、配置文件）→ 0050（注册面）→ 0051 与 0052（worker 设备模块）→ 文档与 skill。

## documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）

新页：

- user guide：`engines.md`（引擎能力矩阵，差集测试守）；设备主题页（`@device` 与 `@app` 写法、应用别名、设备选择与 `gherkai.toml` 的 `[devices]`、费用含取设备开销与口径以账单为准、限制：国内消费级应用线上包自退、iOS 26 的 DOM、Compose 无标识、数据驻留 us-west-2 与 400 天）。
- docs/internals：设备会话与 Appium 适配的机理解读一篇（权威指回 0051 / 0052）；`docs/internals/README.md` 登记新篇。`cli-json-contract.md` 的加法扩展已随 ADR 改写完成，实施时按真渲染器样例核对、补护栏夹具。

既有用户文档的触点（按页列，每页都要补 1.5 的新内容，不只是新页）：

- `writing-features.md`：「三个有语义的 tag」改为五个，加 `@device` / `@app` 的写法、组合规则与缺省；`@timeout` 加「缺省按目标、设备 scope 有下限」；「按引擎选写法」旁加「按目标选写法」（导航后落点核对按 Android 网页 / iOS 网页 / 应用分写，设备上 scenario 之间不复位、需要时用内建「重新启动应用」step）；「写完先自检」提 plan 对目标的标注。
- `running-and-results.md`：常用选项加 `--android-device-arn` / `--ios-device-arn` / `--device-farm-project-arn` / `--app-bucket` / `--config`，以及 `--default-job-timeout` 对设备 scope 的语义（非正值不等于不超时、低于下限被拒）；退出码加 definition 格式版本不匹配与设备缺项的 2；「结果在哪」加会话列表、设备占用时长与 `device_session` 链接；explain 节加设备证据（失败的确定性与导航 step 也有证据、控件摘要、原始控件树）；「费用量级」加设备分钟。
- `getting-started.md`：doctor 自检加 `targets.<engine>` / `devices.project` / `devices.sessions` 三行的读法；「AWS 前置」加 Device Farm（只在 us-west-2、首次 deploy 建项目、权限指 cloud-backend）。
- `troubleshooting.md`：「各行查什么」加上述三行；隧道节改为令牌换 cookie 的故障形态（预热失败的消息与处置）；新增设备节：会话类错误与五个新错误类别（`precheck_failed` / `acquire_timeout` / `session_lost` / `release_failed` 为 job 级，`capability_unavailable` 为 step 级）。
- `configuration.md`：「配置生效的四个位置」改为五个（加 `gherkai.toml`：路径基准、`--config`、与选项和环境变量的优先序）；环境变量表加 `GHERKAI_ANDROID_DEVICE_ARN` / `GHERKAI_IOS_DEVICE_ARN` / `GHERKAI_DEVICE_FARM_PROJECT_ARN` / `GHERKAI_APP_BUCKET`；「由 gherkai 注入的环境变量」加 `GHERKAI_SESSION_WARMUP_URL`；「跨命令通用选项」加 `--config`。
- `cloud-backend.md`：「后端包含什么」加 Device Farm 项目；「首次部署」加项目的找回或建立与部署方无权限时的降级；「团队成员需要的最小云端权限」加三方权限表（提交者、部署方、worker）；「拆除与清理」加项目保留与手动删除命令；「费用」加设备分钟；「退出码与常见错误」加「部署未启用设备支持」。
- `local-app-testing.md`：「工作方式」加 worker 预热一步；「安全」改为令牌换 cookie（含 cookie 会到达被测应用访问日志的残余）；「限制」加设备浏览器依赖服务商不弹警告页、免费层策略规则数；「常见故障」加预热失败的三个分支。
- `writing-deterministic-steps.md`：「注册一条 step」加 `targets` 与 `requires`；「handler 拿到什么」加 webdriver 句柄与上下文六字段；「内建的确定性 step」加「页面地址匹配」的设备实现与「重新启动应用」；「在本机核对」加 `list-deterministic` 的 `targets` / `available_targets`；「两侧对称地写」加设备目标的对称要求；材料规则与验收定位（0050 决策 4）。
- `faq.md`：改写「它在什么浏览器里运行？能测移动端视口，或换成 Firefox、Safari 吗？」（真机经 Device Farm，Safari 即 iOS 真机 Safari）；加「测真机要多少钱、必须用 AWS 吗」。
- `docs/user-guide/README.md`：索引登记 `engines.md` 与设备主题页。
- 包入口页：`engines/midscene/README.md` 加设备支持一段（Appium、Device Farm）；`deploy_aws/README.md` 加 Device Farm 项目与权限一句；`cli/README.md` 与根 `README.md` 门面各一句。
- CHANGELOG 与 1.5 的 Release 正文。

其它读者的文档：

- skill：路由表加设备；`references/` 加设备写法；确定性 step 参考按 0050 决策 4 改（期望来自需求、材料只定位置、来源平铺、agent 开会话须项目约定、长流程拆步）；评测集加设备用例（写 `@device` 用例、写一条 webdriver step、处置 precheck_failed）；不出现「先 AI 后硬化」类流程暗示。
- CONTRIBUTING：发版后验证项加真机验收矩阵；`tools/` 的真机重新探测工具使用方法。

## 实施期要核的点（ADR 已定、实施时顺手验证）

- 0051 决策 13 的边缘策略由 gherkai 的隧道实现生成后，在三种浏览器上各走一次（设计阶段已用手写策略文件验过）。
- 0051 决策 11 的脱敏：一次故意建连失败的真机执行，核报错文本里的签名与令牌已被盖住。
- 0049 决策 8 的差集测试在 CI 里如何取得两个 worker 的能力自述（直接调起 `--capabilities`，或各 worker 自测同步维护的快照）。
- 0034 终结真值表的双路径对拍测试：事件矩阵在设计阶段的行之外加「先判 abort、收尾期间 deadline 才到仍为 abort」与「无 ARN 的未知 Create 加取消」两行。
- 0052 决策 6 命令守卫的实测：对缓存的元素句柄、提取出的方法与晚到回调的覆盖；旧执行的晚到命令与事件在下一 scenario 开始之后的表现。
- iOS 26 上「探测超时 → 恢复原生上下文 → deepLink → READY」整链路。
- 预热验收的三个失败分支实际触发：拒收 cookie、校验 401、请求失败。
- 计费：起点、排队是否计费、`deviceMinutes` 是否实时累计；claim 到进入设备解析的启动开销；真实设备 scope 的执行耗时分布（校准 0051 决策 2 的 900 秒与 180 秒）。
- 控件摘要与 page source 的采集耗时与字节量。
- Device Farm 接口形态：`ListDevices` 的 os 字段格式与 formFactor 取值；UNMETERED 无槽位时 Create 的行为；项目名唯一性与按名找回；`ListRemoteAccessSessions` 返回体是否带签名端点。
- S3 同键 CopyObject 刷新后过期是否重新计时；前缀 `ListBucket` 下 HeadObject 缺失键是否稳定 404。
- CloudTrail 的 RunTask 记录是否含 `containerOverrides`（0035 决策 5 的不脱敏清单依据）。
- 真实 IAM 角色闭环：按 0033 权限表建测试角色各走一次（设计阶段只做了策略模拟）。
