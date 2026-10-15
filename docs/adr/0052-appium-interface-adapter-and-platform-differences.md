# 0052. Appium 界面适配与平台差异处理

> **Status:** Accepted（2026-10-15）——定 Midscene worker 在设备目标上的界面适配、平台差异的分层与能力探测；桌面路径行为不变。

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

run-scope 对被测对象只做五件事，收成一个接口，桌面浏览器与设备各一个实现，按 `target.device` 在 scope 开头选一次：

```text
取 agent ／ 取确定性句柄 ／ 导航或启动应用 ／ 读当前地址 ／ 释放
```

- 桌面实现是现有 Playwright 与 AgentCore 浏览器代码的搬移，行为不变，现有测试照常覆盖。
- 设备会话的建立、排队、丢失判定与收尾归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)，本接口的设备实现只调用它。
- 不做：在 run-scope 主流程里按设备写条件分支。两套被测对象的差异一旦漏进主流程，scope 内的 step 循环、短路与 evidence 时序就有两份逻辑。

### 3. 设备模块的划分

设备代码集中在 `engines/midscene/src/device/`，按职责分为六块：

| 职责 | 说明 |
|---|---|
| Device Farm 会话 | 全仓唯一引用 Device Farm SDK 的地方，生命周期契约见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) |
| Appium 建连与上下文切换 | WebdriverIO 客户端、`NATIVE_APP` 与网页上下文的切换 |
| 能力探测 | 决策 5 |
| 驱动适配器 | UiAutomator2 与 XCUITest 各一，按会话回报的 `automationName` 选一次 |
| 界面实现 | 继承 `AbstractInterface`：截图、尺寸、动作原语，原语经驱动适配器下发 |
| 应用启停 | 启动、terminate 加 activate、启动后状态采样 |

设备模块动态加载：桌面路径与 `--capabilities` 不加载 WebdriverIO 与 Device Farm SDK。为什么：能力自述要求零费用、快速返回（[0036](./0036-deterministic-capability-discovery.md)），桌面使用方不应为设备依赖付启动成本。

### 4. 驱动适配器：平台专属命令只在这里出现

适配器把同一组原语翻成各平台的命令，平台专属的 `mobile:` 命令不出现在适配器之外：

| 原语 | Android（UiAutomator2） | iOS（XCUITest） |
|---|---|---|
| 点击 / 长按 | `mobile: clickGesture` / `mobile: longClickGesture` | `mobile: tap` / `mobile: touchAndHold` |
| 滚动 | `mobile: scrollGesture` | `mobile: swipe` |
| 输入 | `mobile: type` | W3C 活动元素 sendKeys（`element/active` 加 `element/value`），所在上下文由探测结果定 |
| 按键 / 主屏 | `mobile: pressKey` | `mobile: pressButton` |
| 坐标单位 | 截图像素 | 点，等于截图像素除以探测得到的比例 |
| 导航 | 网页上下文的 url | 网页上下文的 url；不可用时 `mobile: deepLink` |

- **Android 输入用 `mobile: type`**：W3C 路线在 Android Chrome 上不可靠（见实测依据），而 `mobile: type` 快且 AI 步靠它全部通过。
- **iOS 输入走 W3C 标准路线**：网页上下文可用时对网页活动元素 sendKeys，不可用时对原生活动元素 sendKeys；原生应用里同样走 W3C 路线。不用 Appium 旧版 `POST /keys`（转发到 WebDriverAgent 的 `/wda/keys`）。
- 适配器同时负责从控件树抽取 evidence 的控件摘要表（类型、id、文本、无障碍标识），字段定义与留存规则归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)；两个平台的控件树形态不同，抽取放在适配器里，explain 只渲染。

### 5. 能力探测：每会话一次，结果缓存并写进 scope 诊断

建连后、第一个 step 前执行一次，耗时几秒，结果在会话内缓存、写进 scope 诊断。探测项：

- **网页上下文可用性**（仅网页目标）：只认属于被测对象的网页上下文，即 iOS Safari 的 `WEBVIEW_<pid>` 与 Android Chrome 的 `CHROMIUM`；原生应用会话里出现的 `WEBVIEW_chrome` 不算（那是应用内 WebView，不可调试，拿不到被测内容的 DOM）。上下文出现在列表里还不够，须在短预算内成功执行一条只读命令才算可用。
- **应用目标固定原生上下文**，不探测网页上下文。
- **输入路线**（iOS）：由网页上下文是否可用决定在哪个上下文取活动元素；Android 固定为 `mobile: type`、不探测。
- **坐标比例**：iOS 取 `mobile: deviceScreenInfo` 的 `scale`；Android 为 1。
- **Appium 版本**：取自 `/status`，只记入诊断。

为什么一次定下、不在运行期试错回落：失败的路线有的不抛错，只是空等 50 秒左右；路线失败时模型还会反复重试到重规划上限，额外消耗数万 token。择路必须在交给 AI 之前确定。

网页上下文不可用时的后果：需要 DOM 的确定性 step 记 error 并说明原因、不转 AI，判定规则归 [0048](./0048-test-targets-device-and-ui-kind.md)；导航改走决策 6 的回退路线。

### 6. 固定规则

- **截图与手势都在原生上下文**。Android 网页上下文的截图是视口图、慢一个数量级，且与原生手势的坐标系差一个状态栏加地址栏的偏移；iOS 截图本就不分上下文。
- **AI 步开始前切回原生上下文**；step 结束时会话在原生上下文，这是确定性 step 句柄必须遵守的不变量（句柄上下文与 `withWebContext` 归 [0050](./0050-deterministic-step-handles-and-testing.md)）。
- **滚动**：iOS 用 `mobile: swipe`，Android 用 `scrollGesture`；不用 W3C 指针拖动模拟滚动。
- **导航以「网页上下文可用」为前提**：可用时在网页上下文调 url；iOS 不可用时走 `mobile: deepLink`。iOS 在没有网页上下文时调 url 不报错而是挂住，所以前提必须先判，不能靠超时处理。
- **`appium:newCommandTimeout` 是适配器内部常量，与 step 超时脱钩**。它防的是服务端在模型思考期间回收会话（缺省 60 秒不够），取值要覆盖最长的单次模型思考与慢网页加载（从美国出网的公共真机上，实测页面加载 31 到 119 秒）；被测站点加载慢由使用方调大 `@timeout`，工具不自动放宽 step 预算；step 超时是判定预算，语义不同，联动会让一个小的 `@timeout` 导致会话在思考中途被回收。
- **重规划上限**：设备目标缺省 12，桌面目标行为不变；覆盖走 [0044](./0044-engine-model-selection-and-override.md) 决策 2 的 worker 侧 env 覆盖形态。为什么是 12：原生应用的翻页类动作每翻一页消耗一轮规划，实测需要到 12；必须有限，否则失败的动作步会无上限重试。
- **隧道鉴权不经驱动适配器**：隧道鉴权采用令牌换 cookie（[0051](./0051-device-session-lifecycle-and-app-distribution.md)），导航原语只打开 step 文本里已带本 run 访问令牌的地址，由隧道边缘下发会话 cookie 并跳转；适配器不处理 iOS Safari 的系统鉴权表单，也不感知令牌与 cookie。令牌查询参数的脱敏归 0051，适配器写进诊断与错误文本的地址同样经该出口。

### 7. Midscene 复用边界

- **复用**：`Agent`、`AbstractInterface`、`createDefaultMobileActions` 与 `defineActionsFromInputPrimitives`（动作集定义）、收键盘的决定；规划、报告、dump、token 统计照用 SDK 的，evidence 抽取因此零改动（[0042](./0042-step-evidence-and-explain.md)）。
- **自写**：只有会话管理、传输原语（驱动适配器）、能力探测。
- **依赖**：`@midscene/core` 升为显式依赖，与 `@midscene/web` 锁定同一版本（沿用 [0042](./0042-step-evidence-and-explain.md) 决策六的 SDK 版本锁定）。
- **不接 `@midscene/ios`**：它对 Appium 端点有三处硬阻断（见实测依据）。
- **借规则、不借代码**：DPR 回退规则（截图长边除以窗口长边取整）作为比例探测失败时的回退依据，按其逻辑自写；`@midscene/ios` 的传输层不引入。

### 8. 护栏

- **读取点测试**：系统版本与机型只允许从会话能力对象读取，读取点由测试守住。不扫数字字面量：坐标、超时、比例里的数字与版本号无法区分，扫描只会产生误报、照不出用变量拼出的版本分支。
- **命令契约快照**：两个驱动适配器对每个原语发出的命令（命令名与参数形态）存快照，改动须显式更新快照。
- **真机重新探测工具**：`tools/` 下放一个真机重新探测工具，在真实会话里逐项执行探测与原语，生成能力矩阵并与测试 fixture 做差集。
- **人工触发的真机验收矩阵**：升级 Midscene、WebdriverIO，或 Device Farm 的 Appium 服务端版本变化时，由人触发一轮真机验收：Android 加两代 iOS、网页加应用、故障演练；列入 CONTRIBUTING 的发版后验证项。不进 CI：需要真机会话与模型费用，且失败须人判是平台变化还是用例问题。

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

**网页上下文**：iOS 15.8 的 Safari 网页上下文完整可用，导航、标题、找元素与 Android 同级。iOS 26.3 上 `window/rect`、`title`、`url`、`elements` 均返回检查器错误 `'Runtime' domain was not found`，`url` 调用不报错但页面不动；改用 `mobile: deepLink`（0.3 秒）导航、之后全程原生上下文，6 步全对。iOS 没有网页上下文时调 url 会挂住，请求超时后反复重试。维基百科 Android 客户端的上下文列表始终只有 `NATIVE_APP` 与 `WEBVIEW_chrome`，后者拿不到正文 DOM。

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

**newCommandTimeout**：缺省 60 秒会在模型思考期间被服务端回收；从美国出网的公共真机上，国内网站页面加载实测 31 到 119 秒。

**`@midscene/ios` 对 Appium 端点的三处阻断**（对照 appium 2.11.5 与 xcuitest-driver 7.35.1 的路由表）：连接前要求 `GET /status` 响应带 `sessionId`，而 Appium 的 `/status` 只有 ready、message、build；建会话的 caps 不带 `appium:` 前缀，Appium 直接拒；手势、按键、启动应用走 `/wda/*` 直连路由，Appium 一律 404、只经 `mobile:` 命令暴露。

## 被拒方案（护栏）

- **接 Midscene 的 Android 或 iOS 包**：Android 包要 adb，Device Farm 远程访问不给；iOS 包有上述三处阻断。
- **按系统版本号或机型名分支**：失效根因常在 Device Farm 侧驱动版本，版本分支在驱动升级后静默失效；探测读真实行为。
- **运行期试错、失败再回落到下一条路线**：失败路线常不抛错、空等 50 秒，模型还会在其上消耗重规划轮次。
- **在网页上下文截图，或视口截图配原生手势**：慢一个数量级且坐标系错位。
- **Android 走 W3C 输入路线**：网页活动元素读回为空，原生活动元素指向 WebView 容器。
- **iOS 用旧版 `POST /keys`**：iOS 15.8 Safari 上空等 51 秒且读回为空；标准路线已覆盖全部情形。
- **用 W3C 指针拖动实现 iOS 滚动**：iOS 26 分页视图不翻页。
- **用 `getWindowRect` 反推坐标比例**：iOS 26.3 上报错。
- **把原生应用会话里的 `WEBVIEW_chrome` 当网页上下文**：它不属于被测对象，拿不到被测内容的 DOM。
- **`newCommandTimeout` 随 step 超时联动**：两者语义不同，联动会让小的 `@timeout` 导致会话在模型思考中途被回收。
- **用扫描数字字面量守「不按版本分支」**：误报多且照不出拼接出的版本条件；改为守读取点。
- **在 run-scope 主流程里按设备分支**：被测对象差异漏进 step 循环，形成两份执行逻辑。
- **驱动适配器在首次导航后用 XCUITest 填写 iOS Safari 的系统鉴权表单**：提交后鉴权是否成功未证实，等待与核实只能靠轮询页面状态；它把隧道鉴权耦合进 iOS 驱动、每个新会话都要重做，而令牌换 cookie 对桌面、Android、iOS 是同一条路（[0051](./0051-device-session-lifecycle-and-app-distribution.md)）。

## 边界与互链

- [0048](./0048-test-targets-device-and-ui-kind.md)：device 与 ui_kind 的声明；网页上下文不可用时 DOM 类确定性 step 记 error 的判定；被测环境可达性的结论。
- [0049](./0049-worker-capabilities-targets-keys.md)：worker 能力自述的 `targets` 等键；本 ADR 的探测是会话内运行期能力，不进能力自述。
- [0050](./0050-deterministic-step-handles-and-testing.md)：webdriver 句柄、handler 上下文字段（含 `ctx.device.scale` 与 `withWebContext`）、注册面的 `devices` 过滤字段、原生上下文复原不变量、测试分层。
- [0051](./0051-device-session-lifecycle-and-app-distribution.md)：远程访问会话生命周期、错误类别（`precheck_failed`、`acquire_timeout`、`session_lost`）、evidence 设备字段与控件摘要表的留存、应用分发、隧道鉴权（令牌换 cookie）、安全与脱敏。
- [0053](./0053-project-config-file.md)：设备选择与应用别名的配置。
- [0044](./0044-engine-model-selection-and-override.md)：重规划上限的覆盖形态。
- [0042](./0042-step-evidence-and-explain.md)：evidence 抽取复用与 SDK 版本锁定。
- [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)：薄 worker；本 ADR 的全部内容在 worker 内，core 不感知驱动与上下文。
