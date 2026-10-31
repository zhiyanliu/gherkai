# 0052. Appium 界面适配与平台差异处理

> **Status:** Accepted（2026-10-15）——定 Midscene worker 在设备目标上的界面适配、平台差异的分层、能力探测与网页上下文身份、超时分层表、命令守卫与结果未知的处置、会话预热的执行；界面接缝的桌面实现是原有桌面代码的搬移，桌面路径除 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4 的会话事件（及其带来的会话名与 `release_failed` 判定）与决策 5 的终结事件门控（停止信号之后不再发 step、scenario 与 scope 级事件）外行为不变。

## 背景与问题

Device Farm 远程访问会话对外只给一个托管 Appium 端点（WebDriver over HTTPS），不给 adb，也不直通设备上的 WebDriverAgent。Midscene 的 Android 包依赖 adb，iOS 包依赖直连 WebDriverAgent，两者都接不上这个端点；Midscene 另有「接任意界面」的接口（`@midscene/core` 的 `AbstractInterface`：截图、尺寸、动作集），可以在其上自写一层 Appium 适配。

适配层要处理的平台差异多且不稳定：Android（UiAutomator2）与 iOS（XCUITest）的手势、输入、滚动、坐标单位各不相同；网页上下文与原生上下文在截图速度与坐标系上不同；同一条路线在一代系统上可用、在另一代上失效，而失效的原因常在 Device Farm 侧的驱动版本，不在系统本身。若把这些差异写成按系统版本号与机型名的分支，每次 Device Farm 升级驱动都会让分支静默失效。本 ADR 定下差异放在哪一层、怎么判定、复用 Midscene 到哪里为止，以及守住这些决定的护栏。

## 决策

### 1. 平台差异分三层处理，设备代码不出现系统版本号与机型名

- **驱动本身的差异**进驱动适配器（UiAutomator2 与 XCUITest 各一个），把 Midscene 的原语翻成各自的命令。
- **随环境变化的差异**由会话开头的一次能力探测得出（决策 5），不按版本号推断。
- **能自动判断的差异**写成带前提的固定规则（决策 6），前提写在规则里。
- 系统版本与机型只从会话能力对象读取、只用于诊断与 evidence 记录，不作分支条件。为什么：实测中 iOS 26 网页上下文失效的根因是 Device Farm 的 appium-xcuitest-driver 对新检查器协议过旧，驱动升级后同一系统版本的行为会变；探测读的是当时的真实行为，版本号读的是推测。

### 2. 界面接缝：run-scope 只通过一个接口操作被测对象

run-scope 对被测对象只做五件事，另承担四项边界义务（一项 scenario 级、三项 step 级），收成一个接口，桌面浏览器与设备各一个实现，按 `target.device` 在 scope 开头选一次：

```text
取 agent ／ 取确定性句柄 ／ 导航或启动应用 ／ 释放 ／ 预热
scenario 前核对 ／ step 前核对 ／ step 后复原并核对 ／ 采集界面快照
```

- 桌面实现是现有 Playwright 与 AgentCore 浏览器代码的搬移，除会话事件与终结事件门控（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4、5）外行为不变，现有测试照常覆盖；四项边界义务在桌面上都是空操作（scenario 前核对恒返回「继续」），只有「采集界面快照」在 AI step 上取 `page.url()`。原先单列的「读当前地址」并入快照采集。
- **scenario 前核对**：从第二条 scenario 起，每条发 `scenario_started` 之前调用一次，只返回「继续」或「scope 终止」（带 errorType 与 message）。第一条之前不调用：被测对象刚就绪，结果未知标志不可能已置位，获取预算的上界也远低于 `max_session_s`，`scope_started` 之后紧跟第一个 `scenario_started` 的保证（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4）因此不变。返回终止时 run-scope 发 `scope_done{status: error, errorType, message}`，这条与后续 scenario 不再发事件，由 core 合成 SKIPPED（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4）；放在 `scenario_started` 之前，是因为在途 scenario 不合成（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一）。设备实现做两件事：上一条 scenario 里发生过结果未知（命令守卫置过结果未知标志；标志只在 step 内有效，所以设备实现另记一个 scenario 级的「发生过结果未知」记录）时，经生命周期通道在原生上下文截图一次作存活探测（受决策 6 探测客户端的超时约束），探测失败不直接定类别，先查一次会话状态再分流：非 RUNNING 归 `session_lost`，RUNNING 归 `engine_error`；会话年龄已达 `max_session_s` 时直接返回终止、归 `session_lost`，不为让第一个 step 报错而开一条 scenario。step 中途发现的会话丢失与年龄到点仍走下面的 step 级失败契约。run-scope 只多一个无条件调用与一个通用的「scope 终止」出口，这个出口 step 级会话丢失收尾时同样要用，主流程仍无设备分支。
- **单个 step 的固定顺序与失败契约**（接缝契约的一部分，不预先指定方法名）：
  1. 发 `step_started`；
  2. **step 前核对**：确认会话处在原生上下文（一次读取），不在就切回；切回失败时本 step 记 error、类别 `engine_error`，不执行 handler 或 AI。它防止上一条 scenario 的残留上下文被带进来——scope 内短路只作用于本 scenario，scenario 之间又没有自动复位（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 1）；
  3. **执行**确定性 handler、导航或 AI，得到暂定判定；
  4. **在网页上下文读地址**：仅当本 step 要产 evidence、目标是网页、能力结论为「提供」时才读，按决策 5 重新定位、受读地址的 15 秒采集预算约束（与控件树的采集预算各自计时，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8），读取失败（含多候选、零候选）只把 `url` 置 null、`url_missing` 记原因。「是否产 evidence」按第 3 步的暂定判定决定：AI step 一律产，确定性 step 与导航 step 只在暂定判定为 failed 或 error 时产。第 5 步复原失败把判定改成 error 的 step，若此前因暂定判定为 passed 没有读地址，evidence 写 `url` 为 null、`url_missing` 为 `error`，不补读。为什么按暂定判定：最终判定要到第 5 步之后才知道，而为每个确定性 step 预先读一次地址等于每步多切一次上下文。放在复原之前，使整个 step 末只有一次「回到原生上下文」；
  5. **复原并核对**：确认会话回到原生上下文；失败则最终判定改为 `error`、原判定写进 message（「原判定为 passed/failed；之后未能切回原生界面，后续 step 的截图坐标会错位」），类别 `engine_error`；命令失败先查会话状态，会话丢失则归 `session_lost`。本 step 发生过结果未知（决策 6）时，暂定判定已是 error，message 以结果未知的整句（「设备在等待时间内没有回应，这一步可能已执行也可能未执行」）开头，复原失败的信息追加在其后；
  6. **在原生上下文采集控件摘要**（只在 failed / error 时，加原始控件树）：best-effort、不改判定，唯一例外是采集中发现会话丢失（按 0051 决策 4 处置）；
  7. 产 evidence、发 `step_done`；截图与原始树进入后台上传队列。evidence 的 `step_kind`（`ai` / `deterministic` / `navigation`）由命中的注册表条目上的标记判别：内建导航条目带导航标记，run-scope 据此记 `navigation`；使用方 handler 在内部自己调用导航不算导航 step，仍记 `deterministic`。判别靠条目数据而不靠匹配句式，主流程不因此多出按 step 种类或按设备的分支。
  失败归级：执行前失败（会话、安装、首次启动、启动采样、能力探测出错以外的部分、会话预热）归 scope 级，走 `scope_done{status: error, errorType}`（0051 决策 4）；能力探测的单项失败不算执行前失败，记为「探测出错」（决策 5）；坐标比例在回退之后仍无法确定不属于单项失败，是执行前失败（决策 5）；scenario 级没有准备动作，用例自己写的 Background step 按普通 step 归因；step 级是上面第 2、3、5 步的失败与第 6 步发现的会话丢失。
- **生命周期通道**：step 前核对、step 后复原与核对、界面快照的采集（含读当前上下文、切回 `NATIVE_APP`、截图、page source 与第 4 步的读地址）、scenario 前核对、会话预热与终结四阶段，都是接缝的设备实现以生命周期管理方的身份经自己的通道执行，不经执行令牌与结果未知标志（决策 6）。为什么：这些动作的时机由本条的顺序契约固定，不会出现晚到引用；而它们恰好发生在令牌已撤销或结果未知标志已置位之后（如结果未知后的复原需要切换上下文，切换不在只读白名单里），经守卫执行就会被自己拒绝。
- 远程访问会话的建立、排队、丢失判定与收尾归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)，本接口的设备实现只调用它；预热的执行见决策 6。
- 不做：在 run-scope 主流程里按设备写条件分支。两套被测对象的差异一旦漏进主流程，scope 内的 step 循环、短路与 evidence 时序就有两份逻辑；顺序写进接缝契约后，桌面与设备的 step 循环只有一份。

### 3. 设备模块的划分

设备代码集中在 `engines/midscene/src/device/`，按职责分为八块：

| 职责 | 说明 |
|---|---|
| Device Farm 会话 | 执行期唯一调用 Device Farm SDK 的地方（设备列举与查询、会话创建、查询、停止、按名列举），生命周期契约见 [0051](./0051-device-session-lifecycle-and-app-distribution.md)；部署与诊断时的项目找回与建立、`doctor` 的会话列举由 Python 侧的部署与诊断模块承担，它不创建、不停止会话（0051 决策 10），护栏测试断言客户端只在这两个模块构造 |
| Appium 建连与上下文切换 | WebdriverIO 客户端（建连、执行、探测三类用途各自的实例与超时，见决策 6）、`NATIVE_APP` 与网页上下文的切换与重新定位 |
| 命令守卫 | 会话级的 driver 代理，worker 交给 Midscene 适配器、内建导航与确定性 handler 的都是它，不暴露裸客户端；维护执行令牌与结果未知标志（决策 6） |
| 能力探测 | 决策 5 |
| 驱动适配器 | UiAutomator2 与 XCUITest 各一，按会话回报的 `automationName` 选一次 |
| 界面实现 | 继承 `AbstractInterface`：截图、尺寸、动作原语，原语经驱动适配器下发 |
| 应用启停 | 安装后启动一次、启动后状态采样；向句柄上下文暴露 `app.restart()`（只在应用目标上有值：terminate 加 activate 加启动采样，采样到自退抛错、step 记 error、类别 `engine_error`；[0050](./0050-deterministic-step-handles-and-testing.md) 决策 2），供使用方自写的重启 step 调用——产品不内置有措辞的 step（[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 第 2 条） |
| 会话预热 | 按探测结论选路线导航预热地址一次，在原生控件树里确认标记（决策 6） |

newSession 的能力集由「Appium 建连与上下文切换」块单点组装：网页目标带 `browserName`（Android 为 Chrome，iOS 为 Safari）；应用目标带 `appium:app`（安装包的预签名地址，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 9）、`appium:autoLaunch: false` 与 `appium:noReset: true`，Android 应用目标另带 `appium:appPackage`（取目标的应用标识，让驱动识别被测应用；是否还需 `appActivity` 由真机验收核对，决策 8）；两种目标都带 `appium:newCommandTimeout`（决策 6 的 ⑧）。应用目标关掉自动启动与重置，是因为启动由 worker 显式 `activateApp` 并做启动采样（0051 决策 9），不让 Appium 在建会话时按自己的缺省启动或重置被测应用。

设备模块动态加载：桌面路径与 `--capabilities` 不加载 WebdriverIO 与 Device Farm SDK。为什么：能力自述要求零费用、快速返回（[0036](./0036-deterministic-capability-discovery.md)），桌面使用方不应为设备依赖付启动成本。

### 4. 驱动适配器：平台专属命令只在这里出现

适配器把同一组原语翻成各平台的命令，平台专属的 `mobile:` 命令不出现在适配器之外：

| 原语 | Android（UiAutomator2） | iOS（XCUITest） |
|---|---|---|
| 点击 / 长按 | `mobile: clickGesture` / `mobile: longClickGesture` | `mobile: tap` / `mobile: touchAndHold` |
| 滚动 | `mobile: scrollGesture` | `mobile: swipe` |
| 输入 | `mobile: type`；清空输入框为连发若干次 `mobile: pressKey` 退格键（keycode 67） | W3C 活动元素 sendKeys（`element/active` 加 `element/value`），所在上下文由探测结果定；回车、退格与清空也归这一行，经活动元素 sendKeys 发控制字符（回车 `\n`、退格 `\b`，清空为若干个 `\b`） |
| 按键 / 系统键 | `mobile: pressKey`（含回车 66、退格 67、返回 4、主屏 3）；向模型注册返回与主屏两个系统动作 | `mobile: pressButton` 只用于主屏（`home`）；iOS 没有系统返回键，不向模型注册返回动作 |
| 收起键盘 | WebdriverIO 的 `hideKeyboard`（Appium 跨平台端点 `POST /session/:id/appium/device/hide_keyboard`，不是 `mobile:` 命令），不带参数 | 同左；固定在原生上下文发出，输入上下文为网页时也不切入网页上下文 |
| 坐标单位 | 截图像素 | 点，等于截图像素除以探测得到的比例 |
| 导航 | 网页目标：探测结论为「提供」时在网页上下文调 `url`，「不提供」与「探测出错」都走 `mobile: deepLink` 交给系统浏览器。应用目标：`mobile: deepLink` 带 package 交给被测应用，发命令前按 RFC 3986 校验地址字符（驱动经 `adb shell am start -d` 传地址，`; ' ( )` 与非 URI 字符会让命令出错或截断，[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7）；命令成功后核对前台包名 | 网页目标同左，路线由探测而非系统版本决定（实测见「导航路线」）。应用目标：`mobile: deepLink` 带 bundleId，地址不经 shell、原样送达，成功只表示已送达且应用在前台 |

- **Android 输入用 `mobile: type`**：W3C 路线在 Android Chrome 上不可靠（见实测依据），而 `mobile: type` 快且 AI 步靠它全部通过。
- **iOS 输入走 W3C 标准路线**：网页上下文可用时对网页活动元素 sendKeys，不可用时对原生活动元素 sendKeys；原生应用里同样走 W3C 路线。不用 Appium 旧版 `POST /keys`（转发到 WebDriverAgent 的 `/wda/keys`）。回车与退格是键盘输入而不是物理按键，`mobile: pressButton` 只接受物理按键名，所以它们与清空一起走活动元素 sendKeys 的控制字符，和文本输入共用同一条已探测的路线。iOS 上没有映射的键名（Tab、Escape 等）记 `capability_unavailable`，不猜测替代路线。
- **收起键盘两平台同一条路线**：两个适配器都只发一条不带参数的 WebdriverIO `hideKeyboard`，不经 `mobile:` 命令，也不在多条收起路线之间试错（被拒方案「运行期试错、失败再回落」）。Appium 2.11.5 的基础路由提供这个端点，两个驱动都实现它；xcuitest-driver 7.35.1 的源码把这条命令标为 deprecated，实现仍在，转发给 WebDriverAgent 的收键盘命令。iOS 上不论输入上下文是网页还是原生，都在原生上下文发出：软键盘是系统界面，不在网页上下文里。原语只负责发命令、失败原样抛出，怎样处置由界面实现决定（决策 7）。驱动实际怎样收起、有没有副作用列入真机验收矩阵（决策 8）；按驱动源码，键盘未显示时两平台都直接返回成功，Android 先发 ESC 键，1 秒内键盘仍在再发返回键，再过 1 秒仍在即报错；iOS 点按标识或标签恰为 `done` 的键，收不起时约 3 秒后报错。Appium 服务端升级时由真机重新探测工具核对这条端点仍被接受（决策 8）。
- **适配器导出原语函数与只读 `mobile:` 命令名集合**（如 `deviceScreenInfo`、`activeAppInfo`）。命令守卫的只读白名单中 `mobile:` 形态的条目、能力探测与会话预热都只调用适配器导出的函数与集合，不自己拼 `mobile:` 命令；`mobile:` 字面量只出现在设备模块的 `adapters/` 目录下（护栏见决策 8）。
- 适配器同时负责从控件树抽取 evidence 的控件摘要表（类型、id、文本、无障碍标识），只在判为 failed / error 的 step 上抽取（原始控件树同时留存），字段定义与留存规则归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8；两个平台的控件树形态不同，抽取放在适配器里，explain 只渲染。

### 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位

建连后、第一个 step 前执行一次，耗时几秒；**只缓存能力结论**（提供 / 不提供 / 探测出错）与输入路线、坐标比例，**不缓存上下文句柄**；结论写进 scope 诊断文件 `device-session.json`（以普通产物链接挂 `scope_done`，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8）与 worker 日志。探测项：

- **网页上下文可用性**（仅网页目标）：只认属于被测对象的网页上下文，即 iOS Safari 的 `WEBVIEW_<pid>`（也接受其后带 `.<页号>` 的形态：两种命名都只指 Safari 里的页面，属于同一类别；真机验收中 iOS 15.8、18.6、26.3 出现的都是 `WEBVIEW_<pid>.1`，不带页号的形态仍一并接受，因为驱动可能给出另一种）与 Android Chrome 的 `CHROMIUM`；原生应用会话里出现的 `WEBVIEW_chrome` 不算（那是应用内 WebView，不可调试，拿不到被测内容的 DOM）。**「可用」的判据是能在短预算（15 秒，决策 6 分层表 ⑪）内成功执行一条只读命令**，列得出、切得进都不算：逐条路线实测中，iOS 26.3 列得出 WEBVIEW、切换成功，网页命令却立即返回检查器错误或挂到客户端超时（实测依据「网页上下文」）。探测用的只读命令由**自带短超时的独立客户端实例**发出——一条挂住的网页命令会阻塞同一客户端上的后续命令，`Promise.race` 式的放弃解除不了阻塞。探测在短预算内做一次有界重试以区分瞬时故障与确认不提供。归类按证据性质：重试后候选仍为零，或有候选、两次尝试都切得进、只读命令两次都失败且最后一次不是传输层错误（是超时或服务端报错），而原生上下文的只读命令正常，都算确认「不提供」（逐条路线实测中 iOS 26.3 切换成功、网页命令立即返回检查器错误的样本属于这种；网页命令挂住的样本能否落到这里，取决于重试时列上下文与切入能否在 ⑪ 内返回，而服务端对同一会话串行执行（见本条后文），它们会排在仍挂着的那条命令之后）；只读命令只失败过一次、另一次失败在列上下文或切入时，不够这条证据。只有无法区分设备能力的情形才算「探测出错」（其中会话丢失归 `session_lost`）：切入在重试之后仍失败（从未执行到只读命令）、列上下文的调用本身失败、最后一次失败是传输层错误（连接层错误码、HTTP 502 / 503 / 504，或既没有错误码也没有状态码的失败）、多个候选无法确定被测页面、原生只读命令也失败的会话异常。两种结论下导航都不走 `url`。真机验收中 iOS 26.3 归「探测出错」：切入网页上下文本身在服务端挂住约 150 秒才返回，当前 15 秒的探测超时先于这次切入返回而到期，失败落在切入一环而不是只读命令；需要网页上下文的 step 因此记 `engine_error` 而不是 `capability_unavailable`，`url_missing` 记 `error` 而不是 `no_web_context`，导航同样走 deepLink。iOS 15.8 与 18.6 的切入 0.2 秒，探测结论为「提供」。「重试后零候选即不提供」的前提是刚建好、尚未导航的 Safari / Chrome 会话已经列得出网页上下文候选；真机验收中已测的 Android Chrome 与 iOS 15.8、18.6、26.3 Safari 会话都满足（Android 为 `CHROMIUM`，iOS 三代都是 `WEBVIEW_<pid>.1`）。这一前提可能随驱动版本变化，仍列在真机验收矩阵里（决策 8）；若将来网页上下文本可用的设备因零候选被判成「不提供」，探测改为先经探测实例导航预热地址、再列上下文。独立实例只解除客户端一侧的阻塞：Appium 服务端对同一会话的命令串行执行，iOS 26.3 上探测实例的切入挂住期间，执行实例发出的原生只读命令曾被延迟约 105 秒。原生一侧的核对因此经执行实例发出，它的超时是单条命令的真实上界（⑥），串行带来的等待不会让原生命令被误判为失败；这段等待计入获取预算 ③。
- **当前上下文的身份是动态事实，每次进入网页上下文都重新定位**（`withWebContext` 入口、设备上的导航、地址读取）：列出上下文、按类别筛选，再确定被测页面。1.5 的过渡规则：只有一个候选且可用才采用；多个候选时拒绝歧义，本 step 记 error、类别 `engine_error`，消息「设备上有多个网页页面，无法确定被测页面」；零候选等待 2 秒（实施期校准、真机验收后可调）后再列一次，仍为零记 `engine_error`，能力结论不因此翻转；`fn` 执行中句柄失效直接记 error、不在 `fn` 内重试（`fn` 可能已有副作用）。为 evidence 读地址（决策 2 第 4 步）时，多候选与零候选都不改 step 判定，只把 `url` 置 null、`url_missing` 记 `error`（超时记 `timeout`），能力结论不翻转；记 step error 的只有 `withWebContext` 入口与设备上的导航。跨站导航后上下文名可能改变，每次重新定位已覆盖。实测 iOS 15.8 与 18.6 上 `mobile: getContexts` 返回每个 WEBVIEW 的标题与地址，是将来放宽多候选规则时的身份依据；实测中 `target=_blank` 的脚本点击后仍只有一个 WEBVIEW（Android 始终只有一个 `CHROMIUM`），多候选形态未复现，候选数写进诊断以积累样本。重议条件：多候选在 iOS Safari 或 Android Chrome 上成为常态，或找到可靠的前台页判据。同一路线内有界地重新定位同一目标不算「失败后换路线」。
- **应用目标固定原生上下文**，不探测网页上下文；应用目标上的 handler 调用 `withWebContext` 记 error、类别 `capability_unavailable`（应用目标没有网页上下文，重试不会变，处置是改用原生界面上的操作或改写为 AI 步）。声明 `requires: ["web_context"]` 的条目在注册期只能落在网页目标上（[0050](./0050-deterministic-step-handles-and-testing.md) 决策 1），这条归类兜住没有声明前提却调用它的 handler。
- **输入路线**（iOS）：由网页上下文是否可用决定在哪个上下文取活动元素；Android 固定为 `mobile: type`、不探测。
- **坐标比例**：iOS 取 `mobile: deviceScreenInfo` 的 `scale`；它失败时回退为截图长边除以窗口长边、取整，窗口长边取原生 page source 里 `XCUIElementTypeApplication` 节点宽与高中的较大者（真机的根节点是不带属性的 `AppiumAUT`，Application 是它的第一个子节点，按标签名找、不取根节点）；回退也失败时按执行前失败归 `engine_error`，消息「无法确定坐标比例」。不调 `getWindowRect`（iOS 26.3 上两种上下文都报错，见被拒方案）。Android 恒为 1。比例没有可用的缺省值：猜错的比例会让每个 iOS 手势都落空，所以确定不了就不进入执行。
- **Appium 版本**：取自 `/status`，只记入诊断。
- **DeepLink 支持**（仅应用目标）：不预先探测，首次 `mobile: deepLink` 遇到 WebDriverAgent「不支持打开地址」类报错即记为「不提供」并缓存到会话（[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7）；只缓存能力否定，地址被拒与结果未知不进缓存。这是「一次定下」的惰性例外：预先探测要么多开一次应用，要么没有可用的只读命令。

为什么一次定下、不在运行期试错回落：失败的路线有的不抛错，只是空等 50 秒左右；路线失败时模型还会反复重试到重规划上限，额外消耗数万 token。择路必须在交给 AI 之前确定。

网页上下文不可用时的后果：声明了 `requires: ["web_context"]` 的确定性 step 不调 handler，记 error、类别 `capability_unavailable`（探测确认不提供）或 `engine_error`（探测出错，消息「未能确认设备是否提供网页上下文」），不转 AI，注册元数据与判定规则归 [0048](./0048-test-targets-device-and-ui-kind.md) 与 [0050](./0050-deterministic-step-handles-and-testing.md)；设备上任何「读当前地址」先查探测结论，不可用时直接得到「无地址」，绝不调用 `url`：evidence 的 `url` 为 null，`url_missing` 在确认不提供时记 `no_web_context`、探测本身出错时记 `error`（字段取值归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8）；导航改走决策 6 的 deepLink 路线。

### 6. 固定规则

- **截图与手势都在原生上下文**。Android 网页上下文的截图是视口图、慢一个数量级，且与原生手势的坐标系差一个状态栏加地址栏的偏移；iOS 截图本就不分上下文。
- **AI 步开始前切回原生上下文**；step 结束时会话在原生上下文，这是确定性 step 句柄必须遵守的不变量（句柄上下文与 `withWebContext` 归 [0050](./0050-deterministic-step-handles-and-testing.md)）；决策 2 的 step 前核对与复原核对把它变成接缝的义务。
- **滚动**：iOS 用 `mobile: swipe`，Android 用 `scrollGesture`；不用 W3C 指针拖动模拟滚动。
- **网页目标的导航以「网页上下文可用」为前提**：可用时在网页上下文调 url；不可用时走 `mobile: deepLink` 交给系统浏览器。没有可用网页上下文时调 url 不报错而是挂住，所以前提必须先判，不能靠超时处理。应用目标不探测网页上下文，导航固定为带 package / bundleId 的 `mobile: deepLink`（决策 4、[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7）。
- **超时分层表**（设备目标的全部时间上界与重试许可都在这一张表里；[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2、12 与 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 8 指向本表）：

  | 层 | 起点 | 执行者 | 覆盖 | 到期归因 | 重试 |
  |---|---|---|---|---|---|
  | ① job 墙钟 `Job.timeout_s` | 推进器 claim | 推进器 | 拉镜像、获取、执行、收尾 | `timeout` | 设备 job 不参与 core 的 `network_retry` |
  | ② 会话上限 `max_session_s` | 发出 Create | 由「① 不超过 ②」的预检或自检保证；worker 另按会话年龄做后备 | 单会话寿命 | 年龄到点：当前 step error、余下 skipped、发 Stop、归 `session_lost` | 不重试、不重建 |
  | ③ 获取预算（缺省 600 秒，可配，上界 3600 秒） | 进入设备解析 | worker | 筛选与繁忙等待、创建与限流退避、排队、准备、newSession 含安装、至多一次换台重建、`activateApp` 与自退采样、能力探测、会话预热；止于被测对象就绪 | `acquire_timeout`；判据型失败归 `precheck_failed` | worker 内手写退避，跨重建不重置；剩余不足 150 秒不再换台 |
  | ④ Device Farm 单次调用 | 每次调用 | worker | Create、Get、List、Stop | 获取期计入 ③ | `maxAttempts = 1`，请求超时 10 秒（Stop 3 秒，终结期 Get 5 秒），手写退避，停止信号可穿透 |
  | ⑤ newSession 单请求超时（不小于 4 分钟加 65 秒，封顶优先） | 发出 newSession | WebDriver 客户端（建连实例） | 建会话加 `appium:app` 安装 | 计入 ③；被剩余 ③ 封顶后到期归 `acquire_timeout`；未被封顶的超时视为瞬时失败，预算允许时只重试 newSession 一次，否则 `acquire_timeout`（0051 决策 3） | 传输层 0 次 |
  | ⑥ 执行期单请求超时（180 秒，实施期校准、真机验收后可调） | 每个请求 | WebDriver 客户端（执行实例） | 单条命令，**它是单条命令的真实上界** | 结果未知（见下） | 0 次；只读原语白名单重试 1 次 |
  | ⑦ W3C `pageLoad`（设备模块常量，暂定 150 秒） | 每条导航 | 服务端驱动 | 页面加载，**只是尽力而为** | 服务端回 `timeout` 时结果已知 | 不重试；单次加载超过它的站点在 1.5 不受支持，调大 `@timeout` 只解决多次加载累积的墙钟不足 |
  | ⑧ `appium:newCommandTimeout`（900 秒，实施期校准、真机验收后可调） | 上一条命令返回后 | Appium 服务端 | 命令之间的空闲（两平台实测长命令执行期间不计时） | 会话被回收，查状态后按 0051 决策 4 归因 | 不适用 |
  | ⑨ Midscene 重规划 12 轮、每个 act 累计 5 次动作错误 | 每个 act | Midscene | 次数上限，不是时间上限 | 现有规则 | 不适用 |
  | ⑩ 终结四阶段 | 进入终结 | worker | 0051 决策 5 的四个阶段与各自截止线 | 释放未确认即 `release_failed` | 见 0051 决策 5 |
  | ⑪ 探测实例单请求超时（15 秒，真机验收后可调） | 每个请求 | WebDriver 客户端（探测实例） | 能力探测里网页上下文的列举、切入与只读命令，`/status` 与设备屏幕信息；scenario 前核对的存活截图 | 能力探测的请求计入 ③，到期的那一环按决策 5 归类，两种否定结论下导航都走 deepLink；scenario 前存活截图在获取预算停止之后发出，计入 ①（执行期），失败按决策 2 的 scenario 前核对归因 | 传输层 0 次；网页上下文在探测内有界重试一次（决策 5）；存活截图属只读白名单（连接层错误与 502 / 503 / 504 重试 1 次，超时不重试） |

  ⑪ 的取值：它在判定路径上，到点即换路线（探测出错或不提供，导航改走 deepLink），所以取实测最慢值的数倍。实测最慢的单次上下文切换是 Android Chrome 的 3.6 秒，15 秒约为它的四倍，正常的切换不会被它截断而误判成探测出错；iOS 15.8 与 18.6 的上下文命令都在 1 秒内。iOS 26.3 的切入网页上下文在服务端挂住约 150 秒才返回，当前 15 秒的探测超时会先于这次切入返回而到期，按探测出错处理、导航走 deepLink（实测依据「上下文切换与采集耗时」）。evidence 的采集预算不在本表：它们只影响证据的完整程度，到点只置空字段，归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8。

  不变量：① 不超过 ②；设备 scope 的 ① 不小于 ③ 加最短余量；⑤ 封顶优先——剩余 ③ 小于 4 分钟加 65 秒时 newSession 以剩余 ③ 为超时，此时安装未完成归 `acquire_timeout`，换台条件仍是剩余 ③ 不少于 150 秒（0051 决策 3）；⑥ 大于 ⑦ 加余量（180 秒对 150 秒），只是为了给服务端先报的机会——实测 Android Chrome 上 `pageLoad` 设 3 秒、10 秒慢页在 14.6 秒后才报 timeout，iOS Safari 上设置不被反映、`url` 在 3.2 秒返回而页面未加载完，所以 ⑦ 不能当上界；⑧ 不小于最长命令间空闲（含单次模型规划）加余量；⑤ 到 ⑧ 由「Appium 建连与上下文切换」块显式设定（决策 3），不依赖 SDK 缺省；同一会话上建连、执行、探测用不同的客户端实例设不同超时。实例的超时并非完全独立：据 webdriver 10.0.2 源码，它按会话 id 共享一个 undici 连接池，连接池的超时取第一个对该会话发命令的实例的值，之后其它实例的有效超时是自身与它的较小值；实测「两个实例的 `connectionRetryTimeout` 各自生效」是在长超时实例先发命令的顺序下得到的。所以不变量是：建起该会话连接池的那条会话命令，无论由哪个实例发出，都必须采用执行期单请求超时 ⑥。为此建会话之后、能力探测之前，第一条会话命令由执行实例发出（它在会发会话命令的实例中超时最长）；建连实例的 newSession 不带会话 id、不进连接池，但有一处例外：据 webdriverio 10.0.2 源码，`remote()` 在推不出移动端上下文的移动网页会话上（即 iOS Safari；Android Chrome 推得出 `CHROMIUM`、应用目标推得出 `NATIVE_APP`，都不发），返回之前还会由建连实例读一次当前上下文，这条请求先于执行实例建起连接池；建连实例被剩余 ③ 封顶时超时可能远小于 ⑥，整个会话里执行实例的长命令都会被提前切断。修正方式：newSession 返回之后、`remote()` 返回之前，经 `remote()` 的修饰函数把建连实例此后的单请求超时改成执行实例的值，使连接池无论由谁建起，超时都与执行实例相同。这一顺序与这项修正都由测试在真实的 webdriver 客户端上锁定。收尾顺序：`deleteSession` 之后同一会话上的命令都只会失败，而据 webdriver 10.0.2 源码，DELETE 返回时该会话共享的连接池被关闭，关闭会等在途请求完成，不中止它们；所以正常收尾先结束 Midscene 侧（`destroy`），确认执行实例已没有在途命令，再 `deleteSession`。重规划上限缺省 12（原生应用的翻页类动作每翻一页消耗一轮规划，实测需要到 12；必须有限），桌面目标行为不变，覆盖走 [0044](./0044-engine-model-selection-and-override.md) 决策 2 的 worker 侧 env 覆盖形态。不存在「step 预算」：Midscene 没有可控的单 act 时间上限，`abortSignal` 只在规划轮之间生效。
- **执行期关闭传输层自动重试**：执行实例 `connectionRetryCount = 0`（webdriver 10.0.2 在客户端超时与多数服务端错误上以原请求体重发，点击与输入会被重复执行）。只读原语白名单——截图、取上下文列表、page source、已确认网页上下文中的读取地址（不含导航）、前台应用查询（`getCurrentPackage` / `mobile: activeAppInfo`）、`/status`、`deviceScreenInfo`——由设备模块重试 1 次，按原语列、不按 HTTP 方法判。可重试的只有两类：连接层错误（`ECONNRESET`、`ECONNREFUSED`、`EPIPE`、`UND_ERR_SOCKET`、`UND_ERR_CLOSED` 这类错误码；实现另含域名解析与路由失败 `EHOSTUNREACH`、`ENETUNREACH`、`ENOTFOUND`、`EAI_AGAIN`，这类错误发生时请求多半尚未发出，有副作用的命令同样按保守处理记结果未知）与 HTTP 502、503、504；一切超时（含 webdriver 自身的 `ETIMEDOUT` 客户端超时）与 500 都不重试——超时重发会把等待再延长一个 ⑥，挂住的命令重发通常仍挂住；500 是服务端已处理并报错，不是传输故障。状态码经 webdriver 客户端的 `transformResponse` 钩子记到这次请求的选项对象上，webdriver 10.0.2 抛出的错误经 `opts` 引用同一个对象，由此读回（据 webdriver 10.0.2 源码，服务端非 2xx 时抛出的错误只带错误名与消息，不带状态码）。白名单命令超时或重试后仍失败时先查一次会话状态：非 RUNNING 归 `session_lost`，RUNNING 归 `engine_error`；只读命令没有副作用，不置结果未知标志。
- **命令守卫**：会话级的 driver 代理，交给 Midscene 适配器、内建导航与确定性 handler（[0050](./0050-deterministic-step-handles-and-testing.md) 决策 2 的 `ctx.driver`）的都是它。守卫维护两件状态：**当前执行令牌**（step 开始时发出，**在 step 结束、取消或进入终结的那一刻立即撤销**，不等下一 step；带旧令牌或无令牌的调用一律拒绝，覆盖 handler 在 `await` 之后恢复执行、step 结束后保留的引用、以及 SIGTERM 收尾与主执行并存的窗口）与**结果未知标志**（置位后本 step 内一切有副作用的命令被拒绝，只读白名单放行）。两件状态只约束 handler、内建导航与 AI（经 Midscene 适配器）发出的命令；决策 2 列出的生命周期通道（step 前核对、复原与核对、界面快照、scenario 前核对、会话预热、终结四阶段）由生命周期管理方经自己的通道执行，不经令牌与标志。实测 Midscene 1.15.1 在适配器抛错并置 `abortSignal` 后立即结束 act、不再发任何动作，所以守卫的必要性来自 handler 与晚到引用，保留为纵深防御。
- **执行异常的归类由守卫带给 runStep**：守卫在抛出前把归类（`session_lost`、`engine_error`、`capability_unavailable`）连同类型标记挂到异常对象上，runStep 的通用异常分类先认这个标记，认到即按它归类。设备路径的执行异常因此不会被瞬时网络判定归成 `network_error`（WebdriverIO 的 `ECONNRESET`、`UND_ERR_CLOSED` 在设备上意味着结果未知或会话丢失，设备路径没有 `network_error` 出口，[0028](./0028-transient-network-ssl-resilience.md)）；不带标记的异常（桌面路径的全部异常）沿用现有的 `isTransientNetwork` 判定，桌面行为不变。获取期（获取预算覆盖的准备阶段，含会话预热）抛出而未带归类的异常同样不进 `network_error`：获取预算已到期时归 `acquire_timeout`；Appium 会话已建成的，先查一次会话状态，不是 RUNNING 归 `session_lost`（消息用准备阶段的那句），RUNNING 或查不到归 `engine_error`；其余按执行前失败归 `engine_error`，都经 `scope_done{status: error}` 传递（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4）。执行窗口里 handler 与 AI 自己抛出、没有带归类的非断言异常，由设备接缝在 execute 出口挂 `engine_error`，断言异常不挂。接缝形状不变：标记是异常对象上的数据，主流程只多认一个通用标记，不按设备分支。
- **结果未知的命令**（客户端超时、连接中断，或 HTTP 502、503、504，且不在白名单；网关一侧的这三种状态码说明请求可能已到达设备而回应丢失，与服务端已处理并报错的 500 不同，有副作用的命令据此不补发、按结果未知处置）：守卫置结果未知标志并中止当前 act 的 `abortSignal`；worker 查一次会话状态，非 RUNNING 按 `session_lost`，RUNNING 则当前 step 记 error、类别 `engine_error`、消息「设备在等待时间内没有回应，这一步可能已执行也可能未执行」（复原失败等后续信息追加在这句之后，决策 2 第 5 步），本 scenario 短路；下一条 scenario 前经生命周期通道在原生上下文做一次只读存活探测（截图，即决策 2 的 scenario 前核对），失败先查会话状态，非 RUNNING 发 `scope_done{status: error, errorType: session_lost}`、否则发 `scope_done{status: error, errorType: engine_error}`，由 core 合成余下 SKIPPED。任何层都不补发。
- **会话预热由设备模块的「会话预热」块执行一次（决策 3），不感知令牌与 cookie 的值**：在能力探测之后、`scope_started` 之前，按探测结论选路线（可用网页上下文走 `url`，否则 `mobile: deepLink`）导航 worker 收到的预热地址，在原生控件树里查找页面标记（READY / DENIED / ERROR / AUTH REQUIRED），归因规则归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13；预热不处理 iOS Safari 的系统鉴权表单。预热导航以执行实例的单请求超时 ⑥ 为上界，不套用桌面预热的 30 秒导航超时：单条命令的上界只能由客户端实例的请求超时给出，另设 30 秒要么为预热再开一个实例，要么用放弃式等待（被拒方案「探测用 `Promise.race`」同理）。导航超时计一次 ERROR 尝试，之后原地重导航，尝试次数与桌面预热共用同一常量（3 次，实施期校准、真机验收后可调）。预热发生在 `scope_started` 之前、尚无执行令牌，经生命周期通道执行，不经命令守卫。预热地址与设备端点写进诊断与错误文本时同样经 0051 决策 11 的脱敏出口。

### 7. Midscene 复用边界

- **复用**：`Agent`、`AbstractInterface`、`defineActionsFromInputPrimitives`（动作集定义）、收键盘的决定（见下面「收键盘」条）；规划、报告、dump、token 统计照用 SDK 的。evidence 的 dump 映射函数不改即可用；evidence 模块的输入改为接收一份已采集好的界面快照（地址、控件摘要、原始树路径与各自的缺失原因），模块保持纯映射、不发 WebDriver 命令（[0042](./0042-step-evidence-and-explain.md)、[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8）。
- **动作集只经 `defineActionsFromInputPrimitives` 定义**：传 `includeSwipe: false`，系统动作经 `systemActions` 显式给出——Android 注册返回与主屏，iOS 只注册主屏（决策 4）。不用 `createDefaultMobileActions`：在 1.15.1 里它只是前者的薄包装，固定转传尺寸、休眠与 `systemActions`，不转传 `includeSwipe`，因而 Swipe 动作总会注册；类型上它还要求完整的移动端原语集（双击、拖放与 `touch.swipe` 都是必填）。除 Swipe 之外，它不提供前者没有的东西，两者注册出的其余动作相同。关掉 Swipe，是让滚动与翻页类意图只有一条路线、统一经 Scroll 动作走决策 6 的滚动规则：Swipe 动作需要一条按起止坐标拖动的原语，而实测验证过的翻页路线只有决策 6 的两条滚动命令（W3C 指针拖动在 iOS 26 分页视图上不翻页）。SDK 只在 `systemActions` 给了配置时才把系统键注册成动作，不给则返回与主屏都对模型不可见，所以必须显式给出。模型在没有 Swipe 动作时能否用 Scroll 完成横向翻页（引导页、轮播），由真机验收矩阵的同名一行确认（决策 8），不另做单独的真机 spike：动作清单不含 Swipe、系统键按平台注册，这两项已由命令契约测试离线核对；模型在没有 Swipe 时怎样规划只能在真机上观测，单独的 spike 要另起一个真会话，回答的问题与矩阵那一行相同。若模型不能用 Scroll 完成横向翻页，改为注册 Swipe，原语由驱动适配器的滑动命令实现，并回写本条。
- **收键盘**：收不收沿用 Midscene 的决定。Input 动作带来的 `autoDismissKeyboard` 恰为 `true` 时（SDK 给模型的参数说明是只在用例要求时才给），界面实现在点按目标、清空与输入都完成后，调一次驱动适配器的收起键盘原语（决策 4）；为 `false`、没有给、只要求取得焦点，或动作走清空模式时不调。收起键盘是尽力动作：失败只记一行 worker 诊断日志（「worker: 输入完成后未能收起软键盘（不影响这一步的判定）：」后接脱敏后的一行错误文本），不传出异常、不重试，也不改这一步的判定；例外是经命令守卫发出时遇到的会话丢失与结果未知，守卫已记在执行窗口的判定上并中止当前动作，不因这里不传出异常而被掩盖；其余失败（守卫查到会话仍为 RUNNING，或没能查到会话状态）只进这行日志。日志出口由缺省装配从部件环境接上，即 worker 的诊断日志出口（写出时脱敏，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 11）；设备 Agent 工厂把它设为必填：漏接时这类失败既不报错、也不留记录，必填让漏接在编译期就失败。不转交 Midscene 的 `keyboardDismissStrategy`：它是 Midscene 自带设备实现（Android、鸿蒙）的设备级选项，决定先按 ESC 还是先按返回键，两条都是按键路线，Input 动作本身也不传它；本界面实现只有决策 4 的一条收起路线，收起方式由驱动决定。
- **自写**：决策 3 列出的八块设备模块全部自写（Device Farm 会话、Appium 建连与上下文切换、命令守卫、能力探测、驱动适配器、界面实现（在复用的 `AbstractInterface` 之上）、应用启停、会话预热），划分以决策 3 为准。
- **依赖**：`@midscene/core` 升为显式依赖，与 `@midscene/web` 锁定同一版本（沿用 [0042](./0042-step-evidence-and-explain.md) 决策六的 SDK 版本锁定）。`webdriverio` 精确锁定为 10.0.2（它只供注册面类型声明时曾用范围版本），理由同 0042 决策六（本 ADR 的超时、重试与连接池共享结论都依赖这一版本的源码行为），升级即触发决策 8 的真机验收。`@wdio/logger` 同样精确锁定为 10.0.0、随 webdriver 10.0.2 同锁同升：凭据掩码经它的 `setMaskingPatterns` 按 logger 名设置（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 11），掩码 API 的形态与按捕获组替换的语义都是这一版本的行为，而它正是 webdriver 10.0.2 精确依赖的版本；掩码装在模块级状态上，worker 与 webdriver 必须解析到同一份 `@wdio/logger`，建 WebdriverIO 实例之前核对，分成两份即报错、不在没有掩码的情况下建 Appium 会话。
- **不接 `@midscene/ios`**：它对 Appium 端点有三处硬阻断（见实测依据）。
- **借规则、不借代码**：DPR 回退规则（截图长边除以窗口长边取整）作为比例探测失败时的回退依据，按其逻辑自写；窗口长边的来源是原生 page source 里 `XCUIElementTypeApplication` 节点的宽高，不是 `getWindowRect`（决策 5）；`@midscene/ios` 的传输层不引入。

### 8. 护栏

- **读取点测试**：系统版本与机型只允许从会话能力对象读取，读取点由测试守住。不扫数字字面量：坐标、超时、比例里的数字与版本号无法区分，扫描只会产生误报、照不出用变量拼出的版本分支。护栏只约束设备模块里决定适配行为的代码（驱动适配器、能力探测、界面实现、命令守卫）；三类读取不构成按版本或机型的适配分支，显式豁免：设备选择的输入（Device Farm 会话块按设备列举结果的系统版本与机型筛选设备）、协议载荷（`session_opened` 的 `device` 字段与就绪日志里的同一份设备描述、Job 设备请求里的 `osVersion`）、句柄上下文的透传（确定性 step 注册面对 webdriver 句柄的类型声明，以及界面接缝的设备实现把会话回报的系统版本原样填进句柄上下文）。豁免按声明逐处列出，不按整个文件；除设备选择的输入外，豁免声明与读取点所在的声明里读出的值只能原样透传，护栏按白名单判：到达的去处是对象字段的值、数组元素、不带标签的模板插值、变量或字段的初值、单独成句的赋值（外面带括号、类型断言或非空断言也算，护栏先剥掉这些包装再判是不是赋值，如 `(v = x);`、`(v ??= x);`）、返回值（含箭头函数的表达式体）才算透传；作条件判断真假、与 null / undefined 作相等或不等比较（`==`、`!=`、`===`、`!==`，对方带括号或断言也算）是存在性判断，也允许。括号、类型断言（`as`、尖括号写法与 `satisfies`）、非空断言、条件表达式的两个分支、`??` / `||` / `&&`（结果就是某个操作数本身）与赋值表达式（它的值就是写入的值；`=` 左侧是写入目标、不算读取）不改变取值，护栏穿过它们沿外层再判。其余写法一律按适配分支报红：在它上面取属性或调方法、让它参与运算（一元运算含数值转换与 `!`、算术、字符串拼接、位运算、算术与位运算的复合赋值、`typeof`）、与非空值比较、与 null / undefined 作相等或不等之外的比较（大小比较、`in`、`instanceof`）、按它 switch 或用作 case 标签、用作下标、交给函数处理（含 `new` 与带标签的模板），以及白名单之外的写法（如 for-of 遍历、单独成句的读取）。这些声明中带函数体的，每一处都在真实源码上注入非透传写法核对一次，必须报红。经变量、数组、对象或模板中转之后的分支护栏识别不了，与不扫数字字面量同一边界；赋值表达式的值直接用作 switch 判别式或与非空值比较（如 `switch (v = x)`）不算中转，照样报红。另有一条结构差集：会话能力对象只在「Appium 建连与上下文切换」块读取，读取点因此只有那一处。测试文件不在扫描范围内。
- **动态加载的护栏**：WebdriverIO（含 webdriver 与 `@wdio/` 下的包）与 Device Farm SDK 的值 import 只出现在设备模块内；`import type` 一律豁免，因为它在编译期擦除、运行期不加载，桌面路径与 `--capabilities` 的零加载不受影响。
- **命令契约快照**：两个驱动适配器对每个原语发出的命令（命令名与参数形态，含 iOS 回车、退格与清空经 sendKeys 发出的控制字符、Android 清空的退格键序列，以及两平台收起键盘的命令（iOS 两种输入上下文下都不切入网页上下文））存快照，改动须显式更新快照。另由测试守住 `mobile:` 字面量只出现在设备模块的 `adapters/` 目录下（决策 4）。
- **命令守卫的护栏测试**：带旧令牌的调用、结果未知后的有副作用调用、缓存的元素句柄、从代理提取出的方法引用（解构或先取后调）与晚到的异步回调都必须被拒绝；只读白名单放行。
- **预热与探测的验收**：预热验收的三个失败分支（边缘拒收 cookie、校验 401、请求失败）各实际触发一次；iOS 26 上「探测超时 → 恢复原生上下文 → deepLink → READY」整链路在真机验收矩阵里单列一行，这一行同时观测探测实例的网页命令挂住期间执行实例的原生命令延迟多少（服务端是否串行，决策 5），以及每次尝试失败在哪一环（列上下文、切入或只读命令，真机重新探测工具逐次记下；失败的一环决定归「探测出错」还是「不提供」，决策 5）。矩阵另列四行：刚建好、尚未导航的 Safari / Chrome 会话是否已有网页上下文候选（决策 5 的零候选前提）；没有 Swipe 动作时模型能否用 Scroll 完成横向翻页（决策 7）；Android 应用目标的能力集是否还需要 `appium:appActivity`（决策 3）；输入后收起键盘（决策 4、7）：键盘已显示时两平台能否收起，含 iOS 网页输入上下文下在原生上下文发出的命令能否收起 Safari 的键盘；键盘未显示时驱动是否报错与耗时，报错时 worker 日志恰为一行、判定不变；Android 上 ESC 无效时驱动补发的返回键是否把 Chrome 或被测应用带回上一页；iOS 键盘上没有标识或标签恰为 `done` 的键时能否收起。
- **真机重新探测工具**：`tools/` 下放一个真机重新探测工具，在真实会话里逐项执行探测与原语，生成能力矩阵并与测试 fixture 做差集。工具是 `tools/device_reprobe.mts`，用法与判读见同目录的 `device_reprobe.md`。
- **人工触发的真机验收矩阵**：升级 Midscene、WebdriverIO，或 Device Farm 的 Appium 服务端版本变化时，由人触发一轮真机验收：Android 加两代 iOS、网页加应用、故障演练；列入 CONTRIBUTING 的发版后验证项。不进 CI：需要远程访问会话与模型费用，且失败须人判是平台变化还是用例问题。

### 9. 未来方向（不在 1.5 范围）

- 向上游提 PR，让 `@midscene/webdriver` 支持 Appium 端点；合并后自写的界面实现退役，适配器只留平台差异部分。
- 截图缩放降低 token 是可选的成本手段，需另行评估对定位准确率的影响。

## 实测依据

据一台 Android（Redmi Note 13 / Android 15）与三台 iPhone（iPhone 7 / iOS 15.8.4、iPhone 16 / iOS 18.6、iPhone 17 Pro / iOS 26.3.1）上逐条路线的实测，Device Farm 的 Appium 服务端为 2.11.5。

**截图与坐标**：

| 项 | 观察 |
|---|---|
| Android 网页上下文截图 | 10.4 到 10.8 秒一张，视口图 1080x2176 |
| Android 原生上下文截图 | 0.6 到 1.0 秒一张，整屏 1080x2400 |
| 视口截图配原生手势 | 纵向偏移一个状态栏加地址栏，AI 点击全部落空，重规划使 token 增加到约 15 万；改为截图与手势都在原生上下文后动作全部命中 |
| iOS 截图 | 不分上下文，均为整屏像素，0.3 到 0.8 秒一张 |
| iOS 手势单位 | 点；`deviceScreenInfo` 的 `scale` 为 2 与 3，截图像素除以比例后动作全部命中 |
| `getWindowRect` | iOS 26.3 上两种上下文都报错，不能用于反推比例 |
| Midscene 1.15.1 | 对尺寸里的 dpr 打警告并忽略 |

**网页上下文**：iOS 15.8 的 Safari 网页上下文完整可用，导航、标题、找元素与 Android 同级。iOS 26.3 的网页命令在实测中出现两种失败形态：一种是 `window/rect`、`title`、`url`、`elements` 立即返回检查器错误 `'Runtime' domain was not found`、`url` 不报错但页面不动；另一种是 WEBVIEW 列得出、切得进，但任何网页命令都挂到 120 秒客户端超时。两种都说明网页上下文不可用，判据因此定为短预算内成功执行一条只读命令（决策 5）；改用 `mobile: deepLink`（0.3 秒）导航、之后全程原生上下文，6 步全对。真机验收中 iOS 26.3 出现第三种：切入网页上下文本身在服务端挂住约 150 秒才返回，探测在切入一环超时、归探测出错，之后恢复原生上下文、经 deepLink 导航，预热确认到 READY。iOS 没有可用网页上下文时调 url 会挂住，请求超时后反复重试，并阻塞同一客户端上的后续命令（「因上一请求过久而超时」）。iOS 15.8 与 18.6 上 `mobile: getContexts` 返回每个 WEBVIEW 的标题与地址；`target=_blank` 的脚本点击后仍只有一个 WEBVIEW，Android 始终只有一个 `CHROMIUM`。维基百科 Android 客户端的上下文列表始终只有 `NATIVE_APP` 与 `WEBVIEW_chrome`，后者拿不到正文 DOM。真机验收中，刚建好、尚未导航的 Android Chrome 与 iOS 15.8、18.6、26.3 Safari 会话都已列得出网页上下文候选，Android 为 `CHROMIUM`，iOS 三代都是 `WEBVIEW_<pid>.1`；iOS 15.8 与 18.6 切入 0.2 秒，探测结论为「提供」。

**导航路线**：iOS 15.8 上 `mobile: deepLink` 报「当前 Xcode SDK 不支持打开地址」，`url` 路线通过；iOS 18.6 上先 deepLink 再切网页上下文，网页命令全部挂到 120 秒超时并重试三次，改走 `url` 则全部通过；iOS 26.3 只能 deepLink。

**DeepLink**（应用目标；Android 15 维基百科客户端与 Chrome，iOS 15.8、18.6、26.3 用注册了自定义 scheme 的未签名示例包与 Safari）：Android 指定 package 时能处理的链接 1 秒内打开目标页，后台与冷启动同样；应用不处理的主机或路径时命令报「unable to resolve Intent」、不离开被测应用；不指定 package 时系统交给 Chrome。驱动经 `adb shell am start -d` 传地址：含 `; ' ( ) | < >` 的地址命令出错，`|` 与 `;` 让命令截断后部分执行（报错的同时打开了截断的地址），`+ % [ ] { } & = # ! * $ , ~` 与已百分号编码的字符逐字送达（以 Chrome 回显页的 `location.href` 对比标准化原值；其中 `{ }` 不在 RFC 3986 字符集内，发命令前的校验仍拒收，[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7），`mobile: startActivity` 同样经 shell、同样出错，单引号包裹地址会把驱动加的反斜杠留在地址里。iOS 18.6 与 26.3 指定 bundleId 时已注册 scheme 的链接 0.3 秒到前台，后台与冷启动同样，地址不经 shell、含括号引号与 `;` 的地址原样送达（Safari 回显核对）；Device Farm 重签后 Info.plist 注册的 scheme 保留；未注册的 scheme 与无关的 https 地址命令照样成功、应用照样到前台，应用是否跳转外部不可观测。iOS 15.8 带 bundleId 时 2.4 秒报 WebDriverAgent「The current Xcode SDK does not support opening of URLs with given application」，不带时命令挂住（4 次 120 秒客户端超时，481 秒）。Device Farm 公共设备上系统「地图」被禁止启动，不能当被测对象。

**超时语义**（Android Chrome 与 iOS 18.6 Safari）：同一会话上两个 webdriver 10.0.2 客户端实例各自的 `connectionRetryTimeout` 各自生效（缺省实例先发命令、3 秒实例后发；3 秒实例 3.0 秒超时，缺省实例完成同一慢导航）；Android `pageLoad` 设 3 秒、10 秒慢页 14.6 秒后才报 timeout，会话仍可用；iOS `pageLoad` 设置不被反映，`url` 在 3.2 秒返回而页面未加载完；`newCommandTimeout` 15 秒下 25 秒长命令在两平台都正常完成、空闲 20 秒后 `invalid session id`，远程访问会话仍 RUNNING，重新 newSession 5.6 到 17 秒成功；newSession 客户端 2 秒超时后立即与 75 秒后服务端都无残留会话（两个时点）。

**上下文切换与采集耗时**（Appium 2.11.5；开发期从新加坡经约 170 毫秒往返访问 us-west-2 的设备测得，云端 worker 在 us-east-1、离设备更近，本机 worker 可能更远，探测超时与采集预算都按最慢的环境取值）：Android 14 Chrome 上列举上下文 3.5 秒、切入网页上下文 3.6 秒、切回原生 3.5 秒、导航含页面加载 8.1 秒，读一次地址要三次上下文往返、超过 10 秒，原生控件树 0.8 秒；iOS 15.8（iPhone 7）上下文命令各 0.2 秒、读地址 1.1 秒、原生控件树 19 秒；iOS 18.6 各项都在 1 秒内；iOS 26.3 切入网页上下文在服务端挂住约 150 秒才返回，挂住期间执行实例发出的原生只读命令被延迟约 105 秒（服务端对同一会话串行执行），之后原生控件树 3.6 秒。据此定决策 6 分层表 ⑪ 的 15 秒与 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8 的两段采集预算（读地址 15 秒、控件树 30 秒）。

**Midscene 1.15.1 对中止的行为**：假界面在首个动作抛「结果未知」并置 `abortSignal` 后，`aiAct` 15 毫秒内以「task runner is in error state」拒绝，之后零动作、零截图（放行与拒绝两种模式各一次）。

**输入路线**（读回校验）：

| 路线 | Android Chrome | Android 原生应用 | iOS 15.8 Safari | iOS 26.3 Safari | iOS 原生应用（两代） |
|---|---|---|---|---|---|
| 网页活动元素 sendKeys | 11 秒且读回为空 | 不适用 | 读回一致，1.3 秒 | 网页上下文不可用 | 不适用 |
| 原生活动元素 sendKeys | 报 invalid element state（活动元素是 WebView 容器） | 读回一致，0.6 秒 | 报无此元素 | 读回一致，1.4 秒 | 读回一致，1.1 到 1.2 秒 |
| `mobile: type` | 1.6 秒，AI 步全部通过 | 读回一致，1.6 秒 | 不适用 | 不适用 | 不适用 |
| 旧版 `POST /keys` | 未采用 | 未采用 | 不报错、读回为空，51 秒 | 读回一致，1.2 秒 | 读回一致，1.0 到 1.2 秒 |
| W3C 键盘动作 | 未采用 | 未采用 | 不报错、读回为空，50 到 53 秒 | 未测 | 未测 |

`hasKeyboardFocus == 1` 谓词在两代 iOS 上都找不到元素；`mobile: keys` 只在 iOS 17 以上的 iPad 有效，未列入。输入路线失败时模型反复重试到重规划上限，多消耗约 4 万 token。

**滚动**：W3C 指针拖动在 iOS 26 的分页视图上不翻页，`mobile: swipe` 两代都翻。

**iOS Safari 的系统鉴权表单**：iOS 15.8 与 18.6 上，带与不带内嵌凭据的隧道地址都停在原页面，原生截图显示 Safari 弹出系统级登录表单，网页上下文看不到它。表单可由 XCUITest 按类型找到文本框与安全文本框、填值并点按登录按钮（约 11 秒），但提交后未见页面加载，鉴权是否成功未证实。

**重规划上限**：不设上限时失败的动作步无限重试；五页引导页的「跳过引导」用了 5 轮规划，上限 4 不够；iOS 示例应用翻十页找文本框需要到 12。

**newCommandTimeout**：缺省 60 秒会在模型思考期间被服务端回收；它只计命令之间的空闲（见上「超时语义」）。

**页面加载**：从美国出网的公共真机上，国内网站页面加载实测 31 到 119 秒（对照决策 6 分层表的 W3C `pageLoad`）。

**`@midscene/ios` 对 Appium 端点的三处阻断**（对照 appium 2.11.5 与 xcuitest-driver 7.35.1 的路由表）：连接前要求 `GET /status` 响应带 `sessionId`，而 Appium 的 `/status` 只有 ready、message、build；建会话的 caps 不带 `appium:` 前缀，Appium 直接拒；手势、按键、启动应用走 `/wda/*` 直连路由，Appium 一律 404、只经 `mobile:` 命令暴露。

## 被拒方案（护栏）

- **接 Midscene 的 Android 或 iOS 包**：Android 包要 adb，Device Farm 远程访问不给；iOS 包有上述三处阻断。
- **按系统版本号或机型名分支**：失效根因常在 Device Farm 侧驱动版本，版本分支在驱动升级后静默失效；探测读真实行为。
- **运行期试错、失败再回落到下一条路线**：失败路线常不抛错、空等 50 秒，模型还会在其上消耗重规划轮次。
- **在网页上下文截图，或视口截图配原生手势**：慢一个数量级且坐标系错位。
- **Android 走 W3C 输入路线**：网页活动元素读回为空，原生活动元素指向 WebView 容器。
- **iOS 用旧版 `POST /keys`**：iOS 15.8 Safari 上空等 51 秒且读回为空；标准路线已覆盖全部情形。
- **用 W3C 指针拖动实现 iOS 滚动**：iOS 26 分页视图不翻页。
- **为 Swipe 的取舍单独做一次真机 spike**：动作清单与系统键的注册已由命令契约测试离线核对，剩下的「模型能否用 Scroll 完成横向翻页」只能在真机上观测；单独的 spike 要另起一个真会话，回答的问题与真机验收矩阵的同名一行相同，并入矩阵后没有少验证任何一项（决策 7）。
- **用 `getWindowRect` 反推坐标比例，包括把它作为比例回退的窗口尺寸来源**：iOS 26.3 上两种上下文都报错；回退所需的窗口长边改取原生 page source 里 `XCUIElementTypeApplication` 节点宽与高的较大值（决策 5）。
- **把原生应用会话里的 `WEBVIEW_chrome` 当网页上下文**：它不属于被测对象，拿不到被测内容的 DOM。
- **`newCommandTimeout` 随 job 墙钟预算联动**：两者语义不同，联动会让小的 `@timeout` 导致会话在模型思考中途被回收。
- **`newCommandTimeout` 取 max(单请求超时, 最长命令间空闲) 的保守公式**：两平台实测它只计命令之间的空闲，长命令执行期间不计时，保守项没有依据。
- **用 W3C `pageLoad` 作单条命令的真实上界**：Android 上晚 11 秒才生效、iOS 上设置不被反映，只能作尽力而为；上界是客户端请求超时。
- **执行期沿用传输层自动重试**：webdriver 10.0.2 以原请求体重发，点击与输入会被重复执行。
- **只靠抛异常阻止结果未知后的重复执行**：handler 在 `await` 后恢复、step 结束后保留的引用都绕得过异常，须有会话级命令守卫。
- **探测用 `Promise.race` 放弃挂住的只读命令**：放弃不解除同一客户端上的队列阻塞，须用自带短超时的独立实例。
- **先 deepLink 再用网页上下文、或按系统版本选路线**：iOS 18.6 上前者让网页命令全部挂住，iOS 15.8 根本不支持 deepLink、iOS 26.3 只能 deepLink，路线只能由探测决定。
- **用扫描数字字面量守「不按版本分支」**：误报多且照不出拼接出的版本条件；改为守读取点。
- **读取点护栏按用法逐条列黑名单**：没列出的写法会按透传放行（如一元数值转换用作 switch 判别式、拼接结果用作 case 标签），所以改为只列透传的去处（决策 8）。
- **读取点护栏把与 null / undefined 的一切比较都算存在性判断**：大小比较会把两侧转成数值，`x > null` 等同于拿版本号与 0 比较，构成按版本的分支；只有相等与不等比较只判断有没有值（决策 8）。
- **读取点护栏遇到赋值一律判为透传**：赋值表达式的值会流向外层，按它 switch 或拿它与非空值比较（如 `switch (v = x)`、`if ((v = x) === "26")`）都会被放行；赋值只在单独成句时算透传，其余沿外层再判（决策 8）。
- **在 run-scope 主流程里按设备分支**：被测对象差异漏进 step 循环，形成两份执行逻辑。
- **驱动适配器在首次导航后用 XCUITest 填写 iOS Safari 的系统鉴权表单**：提交后鉴权是否成功未证实，等待与核实只能靠轮询页面状态；它把隧道鉴权耦合进 iOS 驱动、每个新会话都要重做，而令牌换 cookie 对桌面、Android、iOS 是同一条路（[0051](./0051-device-session-lifecycle-and-app-distribution.md)）。

## 边界与互链

- [0048](./0048-test-targets-device-and-ui-kind.md)：device 与 ui_kind 的声明；网页上下文不可用时 DOM 类确定性 step 记 error 的判定；被测环境可达性的结论。
- [0049](./0049-worker-capabilities-targets-keys.md)：worker 能力自述的 `targets` 等键；本 ADR 的探测是会话内运行期能力，不进能力自述。
- [0050](./0050-deterministic-step-handles-and-testing.md)：webdriver 句柄、handler 上下文字段（含受命令守卫的 `ctx.driver`、`ctx.device.scale` 与 `withWebContext`）、注册面的 `devices` 过滤字段与 `requires` 声明、原生上下文复原不变量、测试分层。
- [0051](./0051-device-session-lifecycle-and-app-distribution.md)：远程访问会话生命周期与事件契约、错误类别（`precheck_failed`、`acquire_timeout`、`session_lost`、`capability_unavailable`、`release_failed`）、终结四阶段、evidence 设备字段与控件摘要表的留存、应用分发、隧道鉴权（令牌换 cookie 加预热）、安全与脱敏。
- [0053](./0053-project-config-file.md)：设备选择与应用别名的配置。
- [0044](./0044-engine-model-selection-and-override.md)：重规划上限的覆盖形态。
- [0042](./0042-step-evidence-and-explain.md)：evidence 抽取复用与 SDK 版本锁定。
- [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)：薄 worker；本 ADR 的全部内容在 worker 内，core 不感知驱动与上下文。
