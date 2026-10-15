# 0052. Appium 界面适配与平台差异处理

> **Status:** Accepted（2026-10-15）——定 Midscene worker 在设备目标上的界面适配、平台差异的分层、能力探测与网页上下文身份、超时分层表、命令守卫与结果未知的处置、隧道预热的执行；桌面路径行为不变。决策 2、3、4、5、6、7 随 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 的事件契约与收尾顺序同日改写（接缝的 step 顺序与失败契约、能力结论与上下文句柄分开、分层表取代单条 `newCommandTimeout` 规则、evidence 只在失败步采集）。

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

run-scope 对被测对象只做五件事，另承担三项 step 边界义务，收成一个接口，桌面浏览器与设备各一个实现，按 `target.device` 在 scope 开头选一次：

```text
取 agent ／ 取确定性句柄 ／ 导航或启动应用 ／ 释放 ／ 预热
step 前核对 ／ step 后复原并核对 ／ 采集界面快照
```

- 桌面实现是现有 Playwright 与 AgentCore 浏览器代码的搬移，行为不变，现有测试照常覆盖；三项 step 边界义务在桌面上都是空操作，只有「采集界面快照」在 AI step 上取 `page.url()`。原先单列的「读当前地址」并入快照采集。
- **单个 step 的固定顺序与失败契约**（接缝契约的一部分，不预先指定方法名）：
  1. 发 `step_started`；
  2. **step 前核对**：确认会话处在原生上下文（一次读取），不在就切回；切回失败时本 step 记 error、类别 `engine_error`，不执行 handler 或 AI。它防止上一条 scenario 的残留上下文被带进来——scope 内短路只作用于本 scenario，scenario 之间又没有自动复位（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 1）；
  3. **执行**确定性 handler、导航或 AI，得到暂定判定；
  4. **在网页上下文读地址**：仅当本 step 要产 evidence、目标是网页、能力结论为「提供」时才读，按决策 5 重新定位、受短预算约束，读取失败（含多候选、零候选）只把 `url` 置 null、`url_missing` 记原因。放在复原之前，使整个 step 末只有一次「回到原生上下文」；
  5. **复原并核对**：确认会话回到原生上下文；失败则最终判定改为 `error`、原判定写进 message（「原判定为 passed/failed；之后未能切回原生界面，后续 step 的截图坐标会错位」），类别 `engine_error`；命令失败先查会话状态，会话丢失则归 `session_lost`；
  6. **在原生上下文采集控件摘要**（只在 failed / error 时，加原始控件树）：best-effort、不改判定，唯一例外是采集中发现会话丢失（按 0051 决策 4 处置）；
  7. 产 evidence、发 `step_done`；截图与原始树进入后台上传队列。
  失败归级：执行前失败（会话、安装、首次启动、启动采样、能力探测出错以外的部分、隧道预热）归 scope 级，走 `scope_done{status: error, errorType}`（0051 决策 4）；能力探测的单项失败不算执行前失败，记为「探测出错」（决策 5）；scenario 级没有准备动作，用例自己写的 Background step 按普通 step 归因；step 级是上面第 2、3、5 步的失败与第 6 步发现的会话丢失。
- 设备会话的建立、排队、丢失判定与收尾归 [0051](./0051-device-session-lifecycle-and-app-distribution.md)，本接口的设备实现只调用它；预热的执行见决策 6。
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
| 应用启停 | 安装后启动一次、启动后状态采样；内建确定性 step「重新启动应用」（只对应用目标注册：terminate 加 activate 加启动采样，采样到自退记 error、类别 `engine_error`） |
| 隧道预热 | 按探测结论选路线导航预热地址一次，在原生控件树里确认标记（决策 6） |

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
| 导航 | 探测结论为「提供」时在网页上下文调 `url`，「不提供」与「探测出错」都走 `mobile: deepLink` | 同左；路线由探测而非系统版本决定——实测 iOS 15.8 不支持 `mobile: deepLink`、iOS 26.3 只能 deepLink、iOS 18.6 先 deepLink 再用网页上下文会让网页命令全部挂住 |

- **Android 输入用 `mobile: type`**：W3C 路线在 Android Chrome 上不可靠（见实测依据），而 `mobile: type` 快且 AI 步靠它全部通过。
- **iOS 输入走 W3C 标准路线**：网页上下文可用时对网页活动元素 sendKeys，不可用时对原生活动元素 sendKeys；原生应用里同样走 W3C 路线。不用 Appium 旧版 `POST /keys`（转发到 WebDriverAgent 的 `/wda/keys`）。
- 适配器同时负责从控件树抽取 evidence 的控件摘要表（类型、id、文本、无障碍标识），只在判为 failed / error 的 step 上抽取（原始控件树同时留存），字段定义与留存规则归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8；两个平台的控件树形态不同，抽取放在适配器里，explain 只渲染。

### 5. 能力探测：每会话一次，能力结论缓存、上下文句柄每次重新定位

建连后、第一个 step 前执行一次，耗时几秒；**只缓存能力结论**（提供 / 不提供 / 探测出错）与输入路线、坐标比例，**不缓存上下文句柄**；结论写进 scope 诊断文件 `device-session.json`（以普通产物链接挂 `scope_done`，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8）与 worker 日志。探测项：

- **网页上下文可用性**（仅网页目标）：只认属于被测对象的网页上下文，即 iOS Safari 的 `WEBVIEW_<pid>` 与 Android Chrome 的 `CHROMIUM`；原生应用会话里出现的 `WEBVIEW_chrome` 不算（那是应用内 WebView，不可调试，拿不到被测内容的 DOM）。**「可用」的判据是能在短预算（5 秒）内成功执行一条只读命令**，列得出、切得进都不算：iOS 26.3 实测列得出 WEBVIEW、切换成功，但任何网页命令都挂到客户端超时。探测用的只读命令由**自带短超时的独立客户端实例**发出——一条挂住的网页命令会阻塞同一客户端上的后续命令，`Promise.race` 式的放弃解除不了阻塞。探测在短预算内做一次有界重试以区分瞬时故障与确认不提供。归类按证据性质：重试后候选仍为零，或有候选、切得进但只读命令在有界重试后仍失败或超时而原生上下文的只读命令正常（iOS 26.3 属于这种），都算确认「不提供」；只有无法区分设备能力的情形——列上下文的调用本身失败、传输层错误、原生只读命令也失败的会话异常——才算「探测出错」（其中会话丢失归 `session_lost`）。两种结论下导航都不走 `url`。
- **当前上下文的身份是动态事实，每次进入网页上下文都重新定位**（`withWebContext` 入口、设备上的导航、地址读取）：列出上下文、按类别筛选，再确定被测页面。1.5 的过渡规则：只有一个候选且可用才采用；多个候选时拒绝歧义，本 step 记 error、类别 `engine_error`，消息「设备上有多个网页页面，无法确定被测页面」；零候选短等待后再列一次，仍为零记 `engine_error`，能力结论不因此翻转；`fn` 执行中句柄失效直接记 error、不在 `fn` 内重试（`fn` 可能已有副作用）。为 evidence 读地址（决策 2 第 4 步）时，多候选与零候选都不改 step 判定，只把 `url` 置 null、`url_missing` 记 `error`（超时记 `timeout`），能力结论不翻转；记 step error 的只有 `withWebContext` 入口与设备上的导航。跨站导航后上下文名可能改变，每次重新定位已覆盖。实测 iOS 15.8 与 18.6 上 `mobile: getContexts` 返回每个 WEBVIEW 的标题与地址，是将来放宽多候选规则时的身份依据；实测中 `target=_blank` 的脚本点击后仍只有一个 WEBVIEW（Android 始终只有一个 `CHROMIUM`），多候选形态未复现，候选数写进诊断以积累样本。重议条件：多候选在 iOS Safari 或 Android Chrome 上成为常态，或找到可靠的前台页判据。同一路线内有界地重新定位同一目标不算「失败后换路线」。
- **应用目标固定原生上下文**，不探测网页上下文。
- **输入路线**（iOS）：由网页上下文是否可用决定在哪个上下文取活动元素；Android 固定为 `mobile: type`、不探测。
- **坐标比例**：iOS 取 `mobile: deviceScreenInfo` 的 `scale`；Android 为 1。
- **Appium 版本**：取自 `/status`，只记入诊断。

为什么一次定下、不在运行期试错回落：失败的路线有的不抛错，只是空等 50 秒左右；路线失败时模型还会反复重试到重规划上限，额外消耗数万 token。择路必须在交给 AI 之前确定。

网页上下文不可用时的后果：声明了 `requires: ["web_context"]` 的确定性 step 不调 handler，记 error、类别 `capability_unavailable`（探测确认不提供）或 `engine_error`（探测出错，消息「未能确认设备是否提供网页上下文」），不转 AI，注册元数据与判定规则归 [0048](./0048-test-targets-device-and-ui-kind.md) 与 [0050](./0050-deterministic-step-handles-and-testing.md)；设备上任何「读当前地址」先查探测结论，不可用时直接得到「无地址」，绝不调用 `url`；导航改走决策 6 的 deepLink 路线。

### 6. 固定规则

- **截图与手势都在原生上下文**。Android 网页上下文的截图是视口图、慢一个数量级，且与原生手势的坐标系差一个状态栏加地址栏的偏移；iOS 截图本就不分上下文。
- **AI 步开始前切回原生上下文**；step 结束时会话在原生上下文，这是确定性 step 句柄必须遵守的不变量（句柄上下文与 `withWebContext` 归 [0050](./0050-deterministic-step-handles-and-testing.md)）；决策 2 的 step 前核对与复原核对把它变成接缝的义务。
- **滚动**：iOS 用 `mobile: swipe`，Android 用 `scrollGesture`；不用 W3C 指针拖动模拟滚动。
- **导航以「网页上下文可用」为前提**：可用时在网页上下文调 url；不可用时走 `mobile: deepLink`。没有可用网页上下文时调 url 不报错而是挂住，所以前提必须先判，不能靠超时处理。
- **超时分层表**（设备目标的全部时间上界与重试许可都在这一张表里；[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2、12 与 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 8 指向本表）：

  | 层 | 起点 | 执行者 | 覆盖 | 到期归因 | 重试 |
  |---|---|---|---|---|---|
  | ① job 墙钟 `Job.timeout_s` | 推进器 claim | 推进器 | 拉镜像、获取、执行、收尾 | `timeout` | 设备 job 不参与 core 的 `network_retry` |
  | ② 会话上限 `max_session_s` | 发出 Create | 由「① 不超过 ②」的预检或自检保证；worker 另按会话年龄做后备 | 单会话寿命 | 年龄到点：当前 step error、余下 skipped、发 Stop、归 `session_lost` | 不重试、不重建 |
  | ③ 获取预算（缺省 600 秒，可配，上界 3600 秒） | 进入设备解析 | worker | 筛选与繁忙等待、创建与限流退避、排队、准备、newSession 含安装、至多一次换台重建、`activateApp` 与自退采样、能力探测、隧道预热；止于被测对象就绪 | `acquire_timeout`；判据型失败归 `precheck_failed` | worker 内手写退避，跨重建不重置；剩余不足 150 秒不再换台 |
  | ④ Device Farm 单次调用 | 每次调用 | worker | Create、Get、List、Stop | 获取期计入 ③ | `maxAttempts = 1`，请求超时 10 秒（Stop 3 秒，终结期 Get 5 秒），手写退避，停止信号可穿透 |
  | ⑤ newSession 单请求超时 | 发出 newSession | WebDriver 客户端（建连实例） | 建会话加 `appium:app` 安装 | 计入 ③ | 不小于 4 分钟加 65 秒，以剩余 ③ 封顶；传输层 0 次 |
  | ⑥ 执行期单请求超时 | 每个请求 | WebDriver 客户端（执行实例） | 单条命令，**它是单条命令的真实上界** | 结果未知（见下） | 0 次；只读原语白名单重试 1 次 |
  | ⑦ W3C `pageLoad`（适配器常量，暂定 150 秒） | 每条导航 | 服务端驱动 | 页面加载，**只是尽力而为** | 服务端回 `timeout` 时结果已知 | 不重试；单次加载超过它的站点在 1.5 不受支持，调大 `@timeout` 只解决多次加载累积的墙钟不足 |
  | ⑧ `appium:newCommandTimeout` | 上一条命令返回后 | Appium 服务端 | 命令之间的空闲（两平台实测长命令执行期间不计时） | 会话被回收，查状态后按 0051 决策 4 归因 | 不适用 |
  | ⑨ Midscene 重规划 12 轮、每个 act 累计 5 次动作错误 | 每个 act | Midscene | 次数上限，不是时间上限 | 现有规则 | 不适用 |
  | ⑩ 终结四阶段 | 进入终结 | worker | 0051 决策 5 的四个阶段与各自截止线 | 释放未确认即 `release_failed` | 见 0051 决策 5 |

  不变量：① 不超过 ②；设备 scope 的 ① 不小于 ③ 加最短余量；⑥ 大于 ⑦ 加余量，只是为了给服务端先报的机会——实测 Android Chrome 上 `pageLoad` 设 3 秒、10 秒慢页在 14.6 秒后才报 timeout，iOS Safari 上设置不被反映、`url` 在 3.2 秒返回而页面未加载完，所以 ⑦ 不能当上界；⑧ 不小于最长命令间空闲（含单次模型规划）加余量；⑤ 到 ⑧ 由适配器显式设定，不依赖 SDK 缺省；同一会话上建连、执行、探测用不同的客户端实例设不同超时（实测两个实例各自的 `connectionRetryTimeout` 各自生效）。重规划上限缺省 12（原生应用的翻页类动作每翻一页消耗一轮规划，实测需要到 12；必须有限），桌面目标行为不变，覆盖走 [0044](./0044-engine-model-selection-and-override.md) 决策 2 的 worker 侧 env 覆盖形态。不存在「step 预算」：Midscene 没有可控的单 act 时间上限，`abortSignal` 只在规划轮之间生效。
- **执行期关闭传输层自动重试**：执行实例 `connectionRetryCount = 0`（webdriver 10.0.2 在客户端超时与多数服务端错误上以原请求体重发，点击与输入会被重复执行）。只读原语白名单——截图、取上下文列表、page source、已确认网页上下文中的读取地址（不含导航）、`/status`、`deviceScreenInfo`——由适配器重试 1 次，只对网络错误码与 502、503、504，按原语列、不按 HTTP 方法判。
- **命令守卫**：会话级的 driver 代理，交给 Midscene 适配器、内建导航与确定性 handler（[0050](./0050-deterministic-step-handles-and-testing.md) 决策 2 的 `ctx.driver`）的都是它。守卫维护两件状态：**当前执行令牌**（step 开始时发出，**在 step 结束、取消或进入终结的那一刻立即撤销**，不等下一 step；带旧令牌或无令牌的调用一律拒绝，覆盖 handler 在 `await` 之后恢复执行、step 结束后保留的引用、以及 SIGTERM 收尾与主执行并存的窗口；收尾自身的调用由生命周期管理方经自己的通道执行）与**结果未知标志**（置位后本 step 内一切有副作用的命令被拒绝，只读白名单放行）。实测 Midscene 1.15.1 在适配器抛错并置 `abortSignal` 后立即结束 act、不再发任何动作，所以守卫的必要性来自 handler 与晚到引用，保留为纵深防御。
- **结果未知的命令**（客户端超时或连接中断，且不在白名单）：守卫置结果未知标志并中止当前 act 的 `abortSignal`；worker 查一次会话状态，非 RUNNING 按 `session_lost`，RUNNING 则当前 step 记 error、类别 `engine_error`、消息「设备在等待时间内没有回应，这一步可能已执行也可能未执行」，本 scenario 短路；下一条 scenario 前做一次只读存活探测（截图），失败则发 `scope_done{status: error, errorType: engine_error}` 由 core 合成余下 SKIPPED。任何层都不补发。
- **隧道预热由适配器执行一次，不感知令牌与 cookie 的值**：在能力探测之后、`scope_started` 之前，按探测结论选路线（可用网页上下文走 `url`，否则 `mobile: deepLink`）导航 worker 收到的预热地址，在原生控件树里查找页面标记（READY / DENIED / ERROR / AUTH REQUIRED），归因规则归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13；适配器不处理 iOS Safari 的系统鉴权表单。预热地址与设备端点写进诊断与错误文本时同样经 0051 决策 11 的脱敏出口。

### 7. Midscene 复用边界

- **复用**：`Agent`、`AbstractInterface`、`createDefaultMobileActions` 与 `defineActionsFromInputPrimitives`（动作集定义）、收键盘的决定；规划、报告、dump、token 统计照用 SDK 的。evidence 的 dump 映射函数不改即可用；evidence 模块的输入改为接收一份已采集好的界面快照（地址、控件摘要、原始树路径与各自的缺失原因），模块保持纯映射、不发 WebDriver 命令（[0042](./0042-step-evidence-and-explain.md)、[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8）。
- **自写**：决策 3 列出的八块设备模块全部自写（Device Farm 会话、Appium 建连与上下文切换、命令守卫、能力探测、驱动适配器、界面实现（在复用的 `AbstractInterface` 之上）、应用启停、隧道预热），划分以决策 3 为准。
- **依赖**：`@midscene/core` 升为显式依赖，与 `@midscene/web` 锁定同一版本（沿用 [0042](./0042-step-evidence-and-explain.md) 决策六的 SDK 版本锁定）。
- **不接 `@midscene/ios`**：它对 Appium 端点有三处硬阻断（见实测依据）。
- **借规则、不借代码**：DPR 回退规则（截图长边除以窗口长边取整）作为比例探测失败时的回退依据，按其逻辑自写；`@midscene/ios` 的传输层不引入。

### 8. 护栏

- **读取点测试**：系统版本与机型只允许从会话能力对象读取，读取点由测试守住。不扫数字字面量：坐标、超时、比例里的数字与版本号无法区分，扫描只会产生误报、照不出用变量拼出的版本分支。
- **命令契约快照**：两个驱动适配器对每个原语发出的命令（命令名与参数形态）存快照，改动须显式更新快照。
- **命令守卫的护栏测试**：带旧令牌的调用、结果未知后的有副作用调用、缓存的元素句柄与晚到的异步回调都必须被拒绝；只读白名单放行。
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

**网页上下文**：iOS 15.8 的 Safari 网页上下文完整可用，导航、标题、找元素与 Android 同级。iOS 26.3 的网页命令在实测中出现两种失败形态：一种是 `window/rect`、`title`、`url`、`elements` 立即返回检查器错误 `'Runtime' domain was not found`、`url` 不报错但页面不动；另一种是 WEBVIEW 列得出、切得进，但任何网页命令都挂到 120 秒客户端超时。两种都说明网页上下文不可用，判据因此定为短预算内成功执行一条只读命令（决策 5）；改用 `mobile: deepLink`（0.3 秒）导航、之后全程原生上下文，6 步全对。iOS 没有可用网页上下文时调 url 会挂住，请求超时后反复重试，并阻塞同一客户端上的后续命令（「因上一请求过久而超时」）。iOS 15.8 与 18.6 上 `mobile: getContexts` 返回每个 WEBVIEW 的标题与地址；`target=_blank` 的脚本点击后仍只有一个 WEBVIEW，Android 始终只有一个 `CHROMIUM`。维基百科 Android 客户端的上下文列表始终只有 `NATIVE_APP` 与 `WEBVIEW_chrome`，后者拿不到正文 DOM。

**导航路线**：iOS 15.8 上 `mobile: deepLink` 报「当前 Xcode SDK 不支持打开地址」，`url` 路线通过；iOS 18.6 上先 deepLink 再切网页上下文，网页命令全部挂到 120 秒超时并重试三次，改走 `url` 则全部通过；iOS 26.3 只能 deepLink。

**超时语义**（Android Chrome 与 iOS 18.6 Safari）：同一会话上两个 webdriver 10.0.2 客户端实例各自的 `connectionRetryTimeout` 各自生效（3 秒实例 3.0 秒超时，缺省实例完成同一慢导航）；Android `pageLoad` 设 3 秒、10 秒慢页 14.6 秒后才报 timeout，会话仍可用；iOS `pageLoad` 设置不被反映，`url` 在 3.2 秒返回而页面未加载完；`newCommandTimeout` 15 秒下 25 秒长命令在两平台都正常完成、空闲 20 秒后 `invalid session id`，远程访问会话仍 RUNNING，重新 newSession 5.6 到 17 秒成功；newSession 客户端 2 秒超时后立即与 75 秒后服务端都无残留会话（两个时点）。

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

**newCommandTimeout**：缺省 60 秒会在模型思考期间被服务端回收；它只计命令之间的空闲（见上「超时语义」）。从美国出网的公共真机上，国内网站页面加载实测 31 到 119 秒。

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
- **`newCommandTimeout` 随 job 墙钟预算联动**：两者语义不同，联动会让小的 `@timeout` 导致会话在模型思考中途被回收。
- **`newCommandTimeout` 取 max(单请求超时, 最长命令间空闲) 的保守公式**：两平台实测它只计命令之间的空闲，长命令执行期间不计时，保守项没有依据。
- **用 W3C `pageLoad` 作单条命令的真实上界**：Android 上晚 11 秒才生效、iOS 上设置不被反映，只能作尽力而为；上界是客户端请求超时。
- **执行期沿用传输层自动重试**：webdriver 10.0.2 以原请求体重发，点击与输入会被重复执行。
- **只靠抛异常阻止结果未知后的重复执行**：handler 在 `await` 后恢复、step 结束后保留的引用都绕得过异常，须有会话级命令守卫。
- **探测用 `Promise.race` 放弃挂住的只读命令**：放弃不解除同一客户端上的队列阻塞，须用自带短超时的独立实例。
- **先 deepLink 再用网页上下文、或按系统版本选路线**：iOS 18.6 上前者让网页命令全部挂住，iOS 15.8 根本不支持 deepLink、iOS 26.3 只能 deepLink，路线只能由探测决定。
- **用扫描数字字面量守「不按版本分支」**：误报多且照不出拼接出的版本条件；改为守读取点。
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
