# 0048. 测试目标：设备与界面类型两个维度、`@device` 与 `@app` 标签、core 的执行前预检

> **Status:** Accepted（2026-10-15）——1.5 移动真机支持的入口篇：定义测试目标模型与 core 一侧的全部改动，部分取代 [0019](./0019-feature-tags-scope-and-engine.md) 的「三个语义 tag」表述（tag 体系扩为五个）；worker 能力自述、确定性 step 句柄、设备会话、Appium 适配、项目配置文件分别见 0049 到 0053。

## 背景与问题

到 1.4 为止，被测对象只有一种：AgentCore 托管的桌面浏览器里的网页。scope 是会话边界，engine 是会话归属（[0019](./0019-feature-tags-scope-and-engine.md)），二者之外没有「在哪种设备上、测哪种界面」的概念；确定性 step 只有 Playwright 一种实现，worker 也只会开浏览器会话。

1.5 把被测对象延伸到 AWS Device Farm 托管的 Android 与 iOS 真机，覆盖设备浏览器里的网页与原生应用。由此产生四个必须先定的问题：

- 「测哪里」怎样在用例里声明，并与 scope、engine 的既有规则一致；
- core 对 step 语义无知（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 红线），目标信息只能来自结构化声明，不能从 step 文本推断；
- 引擎与确定性 step 对目标的支持是参差的（Nova Act 驱动的是 Playwright 浏览器，没有设备路径；一条确定性 step 可能只写了桌面实现），不支持时要在花钱之前、以清楚的方式拒绝或标注；
- 云端与后台推进的 job 不在 CLI 进程里执行，设备选择这类取值必须随 job 走。

## 决策

### 1. 测试目标由三个正交维度描述：engine、device、ui_kind

| 维度 | 取值 | 回答的问题 | 声明方式 |
|---|---|---|---|
| engine | `novaact` / `midscene`（不扩） | 谁来思考 | `@engine:`（[0019](./0019-feature-tags-scope-and-engine.md)） |
| device | `desktop` / `android` / `ios` | 在哪种设备上 | `@device:`，不标即 `desktop` |
| ui_kind | `web` / `app` | 测网页还是原生应用 | `@app:` 的有无 |

- device 与 ui_kind 合称**目标**（target）。合法组合是 `desktop/web`、`android/web`、`android/app`、`ios/web`、`ios/app`；桌面只有 web，不为桌面应用预留空位（产品范围外，留空位只会让每个消费方多处理一种永不出现的组合）。
- engine 不因设备而分叉：同一个 `midscene` 引擎既驱动桌面浏览器也驱动真机，平台差异全部收在 worker 内部（[0052](./0052-appium-interface-adapter-and-platform-differences.md)）。core 只做模型、协议、调度，设备会话、Appium、Midscene 全在 worker。

### 2. 两个 scope 级 tag：`@device` 与 `@app`

- `@device:android` / `@device:ios`：声明设备。不标即桌面。
- `@app:<别名>`：声明本 scope 测原生应用，别名在项目配置文件的 `[apps]` 节里绑定到应用文件与包名或 bundle id（[0053](./0053-project-config-file.md)）。不标即 web。
- 声明、继承与冲突完全照 [0019](./0019-feature-tags-scope-and-engine.md) 给 `@engine:` 定的三条：scope 内任一 scenario 标了即整个 scope 生效；feature 级 tag 由其下 scenario 继承；同一 scope 内取值不一致即 FeatureContractError，不静默取其一。原因与 engine 相同：一个 scope 共享一个会话，「既在 Android 上又在 iOS 上」「同一会话里是两个应用」在物理上自相矛盾。
- 以下情形同样报 FeatureContractError（产品语言加退出码 2，与现有用例契约违约的呈现一致）：`@device:` 取值不在 `android` / `ios` 之内；`@app:` 出现在桌面目标上；`@app:` 的别名在 `[apps]` 里查不到；`@app:` 的别名在 `[apps]` 里没有该 scope 所在平台的条目（如别名只绑定了 Android 应用，却用在 `@device:ios` 的 scope 上）。
- 应用的启动由 worker 在建立设备会话后执行，scenario 之间先 terminate 再 activate（会话生命周期归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)）。用例**不需要**写「打开某应用」作为第一步；写了也只是一条普通的 AI 动作步，core 不解析它。

### 3. core 的三处改动

**解析。** plan 模块在既有的 `@scope` / `@engine` / `@timeout` 之外解析 `@device` 与 `@app`，按第 2 条的规则归约到 scope，得出每个 job 的目标。core 只读 tag，不匹配 step 文本。

**Job 携带目标与设备选择的具体值。** job 的定义新增两组字段：

- target：`device`、`ui_kind`，ui_kind 为 app 时再带应用条目（别名、应用文件在产物桶里的 S3 键、包名或 bundle id）；
- 设备选择：设备 ARN 或筛选条件、`billing_method`、Device Farm 项目 ARN、获取预算（默认值见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2）；本机后端另带安装包所在的应用桶名（[0053](./0053-project-config-file.md)）。

这些值由 CLI 在组装 run 时从选项、环境变量与项目配置文件解析成**具体值**写入（取值顺序见 [0053](./0053-project-config-file.md)），之后的任何推进器（本机后台进程、云端 Lambda、Fargate 上的 worker）都只读 job 里的值、不读配置文件。理由与 [0035](./0035-local-app-testing-via-tunnel.md) 把额外请求头放进 run 定义相同：后台与云端推进器和 CLI 不在同一进程、甚至不在同一台机器，配置文件与环境变量传不过去；definition 自包含也让同一个 run 在任何推进器上得出相同的设备选择。应用文件的上传与 S3 键的生成归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)。

**本机后端的执行前预检增加两项目标检查。** 依据是 worker 的能力自述（增键规则归 [0049](./0049-worker-capabilities-targets-keys.md)）：

- 目标不在该引擎 worker 声明的 `targets` 里，拒绝执行；
- job 墙钟预算超过该目标的 `max_session_s`，拒绝执行。`max_session_s` 不等于 Device Farm 远程访问会话的 150 分钟上限，而是由 worker 用 150 分钟减去收尾余量算出（[0049](./0049-worker-capabilities-targets-keys.md) 决策 4）；桌面条目不带此键，表示不施加会话级上限。缺省预算如何以 `max_session_s` 为上限归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)。

两项都在建立任何设备会话之前完成，故不产生费用。cloud 后端在提交前只有 plan 标注，执行时由 worker 在建会话前自检同样两项，不满足即记 `precheck_failed`（[0049](./0049-worker-capabilities-targets-keys.md) 决策 7、[0051](./0051-device-session-lifecycle-and-app-distribution.md)），同样不产生会话费用。

job 墙钟预算的语义沿用 [0034](./0034-detached-batch-reconciler.md)：自推进器启动这个 job 起算，不为设备另立起算点；取设备开销（创建到 Appium 可用，约 1 到 2.5 分钟）计在墙钟预算之内，停止到会话结束的收尾时间只计设备分钟、不占墙钟（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2）。

### 4. 目标不受支持时的拒绝：由能力自述决定，消息给出改法

- 引擎是否支持某目标，core 不内置任何引擎名到目标的对照，只看能力自述。Nova Act 的 worker 不声明设备目标（缺 `targets` 键即只有 `desktop/web`，[0049](./0049-worker-capabilities-targets-keys.md)），因而「标了 `@device` 却没标 `@engine`」会落到缺省引擎 novaact 并被拒绝。这是 1.5 最常见的写法错误，消息必须直接给出两种改法，示意：

  > 场景 `features/checkout.feature:3` 所在的 scope 要求在 Android 设备上执行，但它使用的引擎 novaact 不支持设备。请在这个 scope 的任一场景上加 `@engine:midscene`，或用 `--default-engine midscene` 更改默认引擎。

- 本机后端上，该拒绝在 plan 与执行前预检两处出现，归类为 FeatureContractError：是用例声明的目标与所选引擎矛盾，改法在用例或命令行上，不在环境上。plan 按 [0036](./0036-deterministic-capability-discovery.md) 的降级规则查询能力自述；查询失败时该引擎的 job 只给警告、不判定，最终由执行前预检拒绝。
- cloud 后端上，提交前只有 plan 标注；执行时由 worker 自检，目标不受支持记 `precheck_failed`，零会话费用退出（[0049](./0049-worker-capabilities-targets-keys.md) 决策 7、[0051](./0051-device-session-lifecycle-and-app-distribution.md)）。消息给出的改法与上面相同。

### 5. plan 的标注

- 每个 job 行显示目标（如 `android/app:shop`）。
- 汇总给出这次 run 将开的设备会话数（一个设备 scope 一个会话，[0051](./0051-device-session-lifecycle-and-app-distribution.md)）。plan 不写金额：单价随计费方式与区域变化，费用模型归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)；会话数是 feature 作者能直接控制的量。
- 某条确定性 step 在该目标上没有实现（它的句柄声明与 worker `targets` 的交集里没有这个目标，[0050](./0050-deterministic-step-handles-and-testing.md)），plan 把它标注为走 AI。这比 1.4 的情形更安全：1.4 里只写了一侧引擎实现的 step 会在另一引擎上静默落到 AI，现在落到 AI 之前就可见。

### 6. 运行期网页上下文不可用：需要 DOM 的确定性 step 记 error，不转 AI

- 网页上下文在部分设备与系统版本上运行期才知道是否可用（探测归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)）；现状是 iOS 26 的 Safari 在 Device Farm 当前提供的 Appium 驱动下网页上下文整体不可用。
- 此时 plan 已标注为确定性的、需要 DOM 的 step 记 error，消息说明「这台设备上取不到网页内容，确定性检查无法执行」与可选做法（换系统版本、改写为 AI 断言）。**不转 AI**：plan 的标注是 feature 作者读到的契约，运行期悄悄换成 AI 判定会改变判定依据而不留痕，属于静默降级。

### 7. 内建「页面地址匹配」step 与落点核对规则

- 内建的 `Then 页面地址匹配 "<正则>"` 声明 targets，并补上 webdriver 实现，在设备网页目标上照常可用。
- skill 与用户指南的「导航后紧跟一条确定性落点核对」规则在设备网页上照用；应用目标没有页面地址（evidence 的 `url` 为 null），这条规则在应用目标上改为一条 AI 断言核对落点。

### 8. 被测环境可达性

- Device Farm 只在 us-west-2，被测对象由从美国出网的公共真机访问，出网地址落在 Device Farm 公布的设备地址段内。依赖国内后端的被测对象加载会慢一到两个数量级，部分站点按来源地址返回反爬页（数据见「实测依据」）。工具不自动放宽预算：Appium 的 `newCommandTimeout` 须覆盖实测 31 到 119 秒的页面加载（[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6），被测站点本身加载慢由使用方调大 `@timeout`（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2）。用户指南写明这一前提。
- **设备网页经隧道暴露可测本机应用**（[0035](./0035-local-app-testing-via-tunnel.md)）：URL 映射发生在组装 job 时、对 worker 透明，设备目标不改这一点。隧道鉴权对桌面、Android、iOS 统一为「令牌换 cookie」一条路，已在桌面 Chromium、Android Chrome 与 iPhone 16（iOS 18.6）Safari 上验证；鉴权方案、已知边界、对隧道服务商的要求与脱敏归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)。
- **原生应用连本机或私网后端，1.5 不支持。** 隧道暴露只替换 step 文本里的地址，应用自己的后端地址打包在应用里，工具不改写应用；让公共真机进入使用方私网需要私有设备加 VPC-ENI，不在 1.5 范围内。用户指南写明这一限制。

### 9. 不做

- **设备要求型 tag**（系统版本、形态、机型这类约束写进 feature）：不做，`@device:` 之下的取值命名空间为它保留。设备选择现阶段是项目配置的事（[0053](./0053-project-config-file.md)），把它写进用例会让同一份用例在不同项目里含义不同。
- **多设备矩阵**（一份用例自动在多台设备或两个平台上各执行一次）：不做。一个 scope 一个目标；要覆盖两个平台就写两个 scope。矩阵会把设备分钟成倍放大，而成本由 feature 作者显式控制更合适。
- **混合流**（网页跳转到应用、应用拉起网页）：不做。它要求一个 scope 内 ui_kind 可变，与「一个 scope 一个目标」冲突，且上下文归属的判定在两个平台上都不可靠。

## 实测依据

以下数据来自 Device Farm 公共真机上按目标逐项进行的实测（Android 为 Redmi Note 13 / Android 15 与 Chrome；iOS 为 iPhone 7 / iOS 15.8、iPhone 16 / iOS 18.6 与 iPhone 17 Pro / iOS 26.3；桌面为 Playwright 驱动的 Chromium），支撑第 2、6、8、9 条。

| 事实 | 数据 | 支撑的决策 |
|---|---|---|
| iOS 网页上下文按系统版本分化 | iOS 15.8 的 Safari 网页上下文完整可用（导航 1.5 到 1.8 秒、找元素约 0.25 秒）；iOS 26.3 的 `title` / `url` / `elements` 全部返回 WebKit 远程检查器错误，导航只能改走原生侧的 deepLink | 第 6 条：网页上下文是运行期能力缺口，不能假定存在 |
| 没有网页上下文时导航命令挂住 | iOS 会话没有网页上下文时调 `url` 不报错，而是反复超时重试 | 第 6 条：需要 DOM 的 step 必须以探测结果为前提，记 error 而非等待 |
| 浏览器经隧道访问本机应用 | 「令牌换 cookie」在桌面 Chromium、Android Chrome 与 iPhone 16（iOS 18.6）Safari 上均通过，边缘侧四种请求情形的响应均符合预期；地址内嵌凭据在 iOS Safari（15.8 与 18.6）上不被采用、改弹系统级鉴权表单 | 第 8 条：设备网页目标可经隧道测本机应用，鉴权方案统一（详见 [0051](./0051-device-session-lifecycle-and-app-distribution.md)） |
| 国内后端对从美国出网的公共真机的可达性 | 同一台真机顺序打开：维基百科 3.0 秒，百度 31 秒，天气网 74 秒，高德网页版 119 秒；微博 7 秒但落到反爬页 | 第 8 条：可达性与时长是被测环境的前提，要写进用户指南 |
| 原生应用里的网页内容 | Android 原生应用会话的上下文列表只有原生上下文与应用内不可调试的 WebView，正文取不到 DOM | 第 2 条与第 9 条：ui_kind 由声明决定，不从运行期上下文推断；不做混合流 |

## 被拒方案（护栏）

- **从 step 文本推断 ui_kind 与应用**（双引号内是地址即网页、等于已绑定别名即启动应用）：被拒。它让 core 匹配 step 文本，违反 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 的「匹配放 worker」红线；同时与 worker 的导航识别构成两份事实源，二者对同一句话的判断会漂移。显式 `@app:` 让「一个 scope 一个应用」由 FeatureContractError 机械保证。
- **要求「第一步必须是打开应用」**：被拒。这是用 step 文本承载配置，core 要么解析它（同上），要么无法校验；应用由 worker 在会话建立后启动即可，用例保持只写测试意图。
- **`@device` 作 scenario 级属性**：被拒。scope 是会话边界，同一 scope 内的 scenario 共享一台设备，设备只能是 scope 级属性，与 engine 同理。
- **core 内置「哪个引擎支持哪个目标」的对照**：被拒。这是第二份事实源，新增引擎或 worker 版本变化时必然漂移；能力自述已是唯一的能力来源（[0036](./0036-deterministic-capability-discovery.md)）。
- **目标不受支持时静默改用另一个引擎**：被拒。scope 的引擎是用例声明的事实，替用户换引擎会改变判定方式与费用，且对用户不可见。
- **确定性 step 在目标上无实现时拒绝整个 run**：被拒。缺省走 AI 是 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 的默认哲学，plan 标注已让降级可见；拒绝会迫使测试开发为每个目标补齐所有 step 才能开始测试。
- **运行期网页上下文不可用时转 AI**：被拒，理由见第 6 条。
- **推进器在执行时读取项目配置文件**：被拒。推进器读不到使用方机器上的文件，且会让同一个 run 前后不一致，见 [0053](./0053-project-config-file.md)。
- **对设备目标关闭隧道鉴权**：被拒。隧道地址是公网地址，关闭鉴权等于把使用方本机应用在 run 期间向公网开放；统一的鉴权方案见 [0051](./0051-device-session-lifecycle-and-app-distribution.md)。

## 边界与互链

- 本篇定目标模型、tag 语义、core 的解析、job 字段、执行前预检的目标检查与 plan 标注；不定下列内容：
  - 能力自述的 `targets` / step 级 `targets` / `max_session_s` 键与缺键语义、doctor 与 `list-deterministic` 的呈现、引擎能力矩阵：[0049](./0049-worker-capabilities-targets-keys.md)。
  - 确定性 step 的多句柄注册、句柄按 ui_kind 与平台的过滤、handler 上下文、测试分层：[0050](./0050-deterministic-step-handles-and-testing.md)。
  - 设备会话的生命周期、获取预算、错误类别 `precheck_failed` / `acquire_timeout` / `session_lost` 及其在 `scope_started` 之前的传递、隧道鉴权、应用分发、费用、权限与安全：[0051](./0051-device-session-lifecycle-and-app-distribution.md)。
  - 驱动适配器、会话开头的能力探测（含网页上下文是否可用）、设备上的导航与输入：[0052](./0052-appium-interface-adapter-and-platform-differences.md)。
  - `gherkai.toml` 的节与键、取值顺序、`[apps]` 与 `[devices]`：[0053](./0053-project-config-file.md)。
- tag 体系的声明、继承、冲突三条规则仍以 [0019](./0019-feature-tags-scope-and-engine.md) 为准，本篇只是把它扩到两个新 tag。
- job 墙钟预算的起算与强制执行以 [0034](./0034-detached-batch-reconciler.md) 为准；FeatureContractError 的呈现与 plan 的零费用承诺以 [0025](./0025-plan-module-feature-to-jobs.md) 与 [0036](./0036-deterministic-capability-discovery.md) 为准。
- 隧道暴露的 URL 映射以 [0035](./0035-local-app-testing-via-tunnel.md) 为准；隧道鉴权由 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 部分取代 0035 决策 4。本篇只记录设备网页目标经隧道的可达性结论。
