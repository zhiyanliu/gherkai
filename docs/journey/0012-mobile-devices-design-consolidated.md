> 类型: 设计稿

# 移动真机支持（1.5）：方案总稿，待拆成 ADR

本文把 spike（journey 0011）之后与 owner 逐条拉齐的决策收成一份总稿，经六视角对抗复盘（60 条发现、49 条经核验保留）修订为第二版。拆成 ADR 0048 到 0053 后本文删除。每条决策写成「做什么、为什么、不做什么」，能直接搬进 ADR；标「待 owner 拍板」的条目见第 9 节。

## 0 总原则

- core 只做模型、协议、调度；设备会话、Appium、Midscene 全在 worker。core 只读 tag，不匹配 step 文本（ADR 0022 红线）。
- 平台差异分三层处理：驱动本身的差异进驱动适配器（UiAutomator2 / XCUITest 各一个，把 Midscene 原语翻成各自的命令）；随环境变化的差异靠会话开头一次能力探测得出；能自动判断的写成带前提的规则。设备代码里不出现系统版本号与机型名，护栏查的是读取点而不是扫数字字面量。
- 不重造 Midscene 已有的轮子：规划、报告、dump、token 统计、动作集定义、收键盘决定都用它的；自写的只有会话管理、传输原语、能力探测。
- 两种 step 作者（人、agent）走同一条路；产品形态不假设 agent 存在；写作期的辅助只进文档与 skill，gherkai 不新造抓取类工具。
- 1.5 的设备引擎只有 Midscene；Nova Act 驱动的是 Playwright 浏览器，没有设备路径。由能力自述表达、由引擎能力矩阵文档揭示。
- 时间语义沿用 ADR 0034：job 墙钟从 claim 起算，不为设备另立起算点；获取设备（建会话、排队）的开销算在墙钟里并写进文档。

## 1 测试目标模型（拟 ADR 0048）

- 三个正交维度：engine（谁思考，不扩）、device（desktop / android / ios）、ui_kind（web / app）。桌面只有 web，不造空位。
- 两个 scope 级 tag，声明、feature 级继承、冲突处理照 ADR 0019 的三条规则：`@device:android` / `@device:ios`（缺省 desktop）；`@app:<别名>`（有则 ui_kind 为 app、别名查 `[apps]`，无则 web）。未知取值与同一 scope 内不一致都报 PlanError。应用由 worker 在建会话后启动，scenario 之间先 terminate 再 activate；不要求「第一步必须是打开」，core 不解析 step 文本。【复盘改动：原「引号内等于别名即启动」方案撤回，它让 core 匹配 step 文本、与 worker 的导航识别形成两份事实源】
- `@engine` 路由到不支持该目标的引擎（含缺省引擎 novaact）→ PlanError，消息给出改法（标 `@engine:midscene` 或改默认引擎）。
- core 改动：plan 解析两个 tag；Job 携带 target（device、ui_kind、应用条目：别名、S3 键、包名或 bundle id）与设备选择的**具体值**（设备 ARN 或筛选条件、billing_method、项目 ARN，由 CLI 从配置解析后写入，云端与 detached 不读配置文件）；执行前预检——目标不在 worker 能力自述里拒绝、墙钟预算超过 `max_session_s` 拒绝；plan 给出将开的设备会话数。
- 某条确定性 step 在该目标没有实现时，plan 标注为走 AI；运行期网页上下文不可用（iOS 26 在 Device Farm 现状下）时，需要 DOM 的确定性 step 记 error 并说明，不转 AI。
- 内建的「页面地址匹配」step 声明 targets 并补 webdriver 实现；skill 的「导航后紧跟确定性落点核对」规则在设备网页上照用，应用目标上改为 AI 断言落点。
- 被测环境可达性：公共真机在美国公网；本机应用经 ADR 0035 隧道可测，隧道地址在 Android Chrome 与 iOS Safari 上的表现写 ADR 前实测；原生应用连私网后端 1.5 不做（需要私有设备加 VPC-ENI），写明。
- 不做：设备要求型 tag（留命名空间）、多设备矩阵、混合流（网页跳应用、应用拉起网页）。

## 2 worker 能力自述增键（拟 ADR 0049）

- 不升 schema 版本（ADR 0036：加键不递增），在 schema 1 上增键：顶层 `targets`，每条 `{device, ui_kinds, max_session_s}`；`deterministic_steps` 每项带同形 `targets`；缺键即「只有 desktop / web」，老 worker 与老 CLI 零迁移。`min_grace_s` 保持单值（设备侧 SIGTERM 收尾只多 deleteSession 与 Stop 两条即时调用）。
- step 实际可用目标是句柄声明与 worker `targets` 的交集；`list-deterministic` 与 plan 按目标标注；doctor 展示 targets。云端 worker 在建会话前按自己的 targets 自检一次，旧镜像不会把设备 job 当桌面执行。
- 人读视图：user guide 新增 `engines.md`，矩阵为引擎 × 目标 × 确定性句柄 × 默认模型 × 计价公式（不写绝对金额），真值集是两个 worker 的能力自述，差集测试守着。

## 3 确定性 step 多实现注册与测试分层（拟 ADR 0050）

- 注册面：`deterministic(pattern, handlers, meta)`，handlers 以句柄种类为键：`playwright`、`webdriver`；`webdriver` 可写成 `{ uiKinds, platforms, handler }`，按 ui_kind 与平台声明式过滤（Android 与 iOS 选择器不同时写两个句柄条目，不在 handler 里 switch）；传单个函数等于只有 `playwright`，老项目零迁移。Python 完全同构（字典形态，`webdriver` 句柄是 Appium Python Client 的 driver），并与 TS 共用一套跨语言 fixture 核注册语义；1.5 没有 Python 设备引擎，这块 API 面靠 fixture 与注册期校验验收。
- handler 上下文六个字段：`driver`、`target`（platform、osVersion、scale）、`uiKind`、`appId`（仅 app 目标）、`log`、`withWebContext(fn)`。不变量：step 结束时会话在原生上下文。文档首推无障碍标识作锚点。
- 测试分层：判定逻辑无 driver 单测；设备网页的 webdriver 句柄可在本机用 WebdriverIO 加 Chrome for Testing 对材料页面离线执行（与桌面同一张选择器表）；定位与行为靠 `run --scope` 真机验收；想离线测原生 driver 层的用 Appium 官方 fake driver 配真实客户端。
- 被拒：gherkai 自带静态假 driver；界面快照抓取功能；任何「先 AI 后硬化」类流程暗示。延后：确定性 step SDK。
- 写作方法（进 skill 与 user guide）：期望只来自需求；材料只定位置、不定期望；动态材料的来源平铺不排序（应用仓库、开发者工具或 Playwright、Appium Inspector 或 WebDriver 客户端接 Device Farm 会话、已有运行的 evidence）；agent 开设备会话须项目约定放行且必须收尾；原生应用上先看控件有没有稳定标识；一条动作步只表达一屏之内的意图。

## 4 设备会话与应用分发（拟 ADR 0051）

- 一个 scope 一个 Device Farm 远程访问会话，会话名带 run_id；拿到会话 ARN 即发 scope_started；scenario 之间网页目标重新导航、应用目标 terminate 加 activate，scope 内状态共享与桌面同一契约。
- 时间：会话计费与 150 分钟上限都从创建时刻算（排队中的会话不计费，实测）；`max_session_s` 进能力自述；`@timeout` 缺省以 `max_session_s` 为上限；获取预算只在 worker 内部执行，超时记为独立错误类别、不进网络重试。
- 失败形态与类别（ADR 0024 的类别集按规则扩充，cli-json-contract 同步）：机型不支持远程访问、应用启动即自退 → 新类别 precheck_failed；会话丢失、到期 → 新类别 session_lost（当前 step 记 error、余下 step 记 skipped、不再发 Stop、worker 非零退出、job 级不重试）；模型 4xx → engine_error；应用中途被杀由模型从截图判出。判定靠查 GetRemoteAccessSession 的状态，不匹配错误文本。
- 取消与收尾的状态表：Create 在途收到取消 → 等 ARN 到手即 Stop；排队中取消 → Stop；建连重试只重试 Appium newSession、不重建会话；重复 Stop 的报错吞掉。正常收尾：先发 scope_done（判定已全部产出），再 deleteSession、Stop，不等 COMPLETED。
- 泄漏护栏：doctor 列出项目里所有未到 COMPLETED 的会话（含排队中）；worker 退出路径上凡没发过 scope_done 的会话按 ARN 补发一次幂等 Stop；不做回收器。
- evidence：复用现有模块与上传器；设备目标每步由驱动适配器抽取锚点表（类型、id、文本、无障碍标识）作为 evidence 字段，explain 只渲染；原始控件树只在 failed / error 步留存并设大小上限；应用目标 `url` 为空。scope 表头记实际分到的机型、系统版本、应用版本。
- 应用分发只有 S3 一条路：CLI 把本地文件按内容哈希放进产物桶，Job 只带 S3 键；worker 在 newSession 前预签名（短有效期）、交给 `appium:app`，配 `appium:autoLaunch: false` 再 `activateApp`，包名或 bundle id 显式给出；启动后采样应用状态。iOS 签名由 Device Farm 在这条路径上重做（未签名与 ad-hoc 变体实测）。约束：单条 Appium 命令 4 分钟上限、S3 到主机约 6 MB 每秒。应用对象的生命周期进桶的生命周期规则。
- 费用：设备分钟作为原生量进成本信封；`billingMethod` 可配；月用量超过约 1470 分钟每平台时不计量槽位更划算；文档写明每个设备 scope 含 1 到 3 分钟取设备开销。
- 权限与资源：Device Farm 只在 us-west-2；项目由 deploy 用 SDK 建、ARN 存 SSM；三方权限表（CLI：S3 上传；worker：会话类 Device Farm 动作加 S3 读；deploy：建项目与授权）；本机后端驱动真机需要 QA 机器具备会话类权限。
- 安全：Appium 端点地址与预签名地址的凭证在查询串里，三份 redact 实现加一条签名查询参数规则并共用用例；端点不进任何事件；WebdriverIO 日志级别固定 error；用一次故意建连失败的真机运行核报错文本被盖住。Device Farm 自带的 Appium 服务器日志、TCP dump 不取；公共设备会话结束后 Device Farm 清除应用与数据，录像与日志由 Device Farm 保留 400 天且在 us-west-2，写进 user guide。
- Device Farm 录像与日志：【待 owner 拍板，见第 9 节】

## 5 Appium 界面适配与平台差异处理（拟 ADR 0052）

- 界面接缝：run-scope 只通过一个接口操作被测对象（取 agent、取确定性句柄、导航或启动应用、读地址、释放），桌面浏览器与设备各一个实现、按 target.device 选一次；桌面实现是现有代码搬家、行为不变。
- 设备模块（`engines/midscene/src/device/`）：Device Farm 会话（唯一引用其 SDK 处）、Appium 建连与上下文切换、能力探测、驱动适配器（UiAutomator2 / XCUITest，按会话回报的 automationName 选一次）、继承 AbstractInterface 的界面实现（截图、尺寸、原语）、应用启停。设备模块动态加载，桌面路径与 `--capabilities` 不碰新依赖。
- 能力探测（每会话一次、几秒、结果缓存并写进 scope 诊断）：应用目标固定原生上下文、不探网页；网页目标只认属于被测对象的网页上下文（iOS Safari 的 `WEBVIEW_<pid>`、Android Chrome 的 `CHROMIUM`，原生应用会话里出现的 `WEBVIEW_chrome` 不算），且一条只读命令短预算内成功才算可用；输入路线（网页上下文可用则网页活动元素 sendKeys，否则原生活动元素 sendKeys，两条都是 W3C 标准路由；Android 的 W3C 路线写 ADR 前实测，否则 Android 用 `mobile: type`）；坐标比例（deviceScreenInfo 的 scale，Android 为 1）；Appium 版本记入诊断。
- 固定规则：截图与手势都在原生上下文；AI 步开始前回到原生上下文；iOS 滚动用 `mobile: swipe`、Android 用 `scrollGesture`；导航用网页上下文的 url，不可用时 iOS 走 `mobile: deepLink`；`appium:newCommandTimeout` 为内部常量、与 step 超时脱钩；重规划上限设备目标默认 12、走 ADR 0044 的覆盖链。
- Midscene 复用边界：Agent、AbstractInterface、`createDefaultMobileActions` / `defineActionsFromInputPrimitives`、收键盘决定；`@midscene/core` 升为显式依赖并与 `@midscene/web` 钉同版本；不接 `@midscene/ios`（连接前要求 `/status` 带 sessionId、caps 不带前缀、手势走 `/wda/*` 直连路由）；借其 DPR 回退规则，不借代码。
- 护栏：版本与机型只允许从会话能力对象读取、读取点有测试守；驱动适配器发出的命令契约快照；`tools/` 下真机重探工具（生成能力矩阵、与 fixture 差集）；升级 Midscene、WebdriverIO 或 Device Farm 的 Appium 变化时由人触发真机验收矩阵（Android 加两代 iOS、网页加应用、故障演练），列入 CONTRIBUTING 的发版后验证项。
- 未来：向上游提 PR 让 `@midscene/webdriver` 支持 Appium 端点，合并后自写界面实现退役；截图缩放降 token 是可选杠杆。

## 6 项目配置文件（拟 ADR 0053）

- `gherkai.toml`，`--config` 或 `GHERKAI_CONFIG`，缺省读当前目录、不存在不算错；只有 CLI 读它，读出的值解析成具体值随 Job 走。取值顺序：选项 > 环境变量 > 配置文件 > 内建默认。
- 节：`[common]`（键名与选项同词）、`[cloud]`、`[devices]`（各平台默认设备：ARN 或平台加系统版本筛选，筛选的挑选顺序与 BUSY 处理写明；billing_method；获取预算；本机后端用的项目 ARN 与应用桶）、`[apps]`（别名 → 本地文件、包名或 bundle id）。
- 设备选择要求显式配置，不自动挑；`--device-arn` 一类选项按取值顺序覆盖。

## 7 文档、skill、术语（documenting 阶段清单）

- user guide：新增 `engines.md`（能力矩阵）与设备主题页（`@device` 与 `@app` 写法、费用含取设备开销、限制：国内消费级应用线上包自退、iOS 26 的 DOM、Compose 无标识、数据驻留 us-west-2 与 400 天）；`writing-deterministic-steps.md` 加 webdriver 句柄与上下文字段、材料规则、验收定位；`configuration.md` 加配置文件；`cloud-backend.md` 加三方权限表与 Device Farm 项目；`troubleshooting.md` 加会话类错误。
- skill：路由表加设备；`references/` 加设备写法；确定性 step 参考按第 3 节改；评测集加设备用例（写 `@device` 用例、写一条 webdriver step、处置 precheck_failed）。
- CONTEXT.md：目标、设备、界面类型、应用别名、远程访问会话、驱动适配器、能力探测；已有词条带浏览器旧描述的一并改写；确定性 step SDK 作延后项立条。校准用差集：ADR 全集与 docs/internals 全层逐条对照。
- CHANGELOG、README 门面一句、ADR 0019 / 0022 / 0024 / 0034 / 0035 / 0036 / 0042 / 0044 的 Status 头与交叉引用。

## 8 写 ADR 前的补测

- Android 输入的 W3C 路线（活动元素 sendKeys）是否落字；不落则 Android 保留 `mobile: type`。
- ADR 0035 隧道地址（带 userinfo）在 Android Chrome 与 iOS Safari 上能否打开本机应用。
- 一次故意建连失败的真机运行，核错误文本里的端点地址被盖住。

## 9 待 owner 拍板

1. **界面类型与应用的声明方式**：显式 `@app:<别名>` tag（推荐，core 只读 tag、一个 scope 一个应用由 PlanError 机械保证），还是沿用「打开 "别名"」由 step 文本推断（违反 0022、两份事实源）。
2. **Device Farm 的录像与日志**：默认不下载、只记会话 ARN 并在 explain 里给控制台链接（推荐，同时消解收尾误判超时、Appium 日志带凭证、数据保留三个问题）；还是在 scope_done 之后多等 1 到 3 分钟下载录像进产物。
3. **job 墙钟起算点**：沿用 0034 从 claim 起算、文档写明含取设备开销（推荐）；还是改协议为设备另立起算点。
