> 类型: 进度总纲

# 移动设备方向：spike 进度总纲

分支 `feat/v1.5-mobile-devices`。本文是跨会话的现场记录：定下的设计、待 spike 回答的问题、spike 的进度与数据。结论成熟后吸收进 ADR（目标维度与 capabilities 2、确定性 step 多实现注册、项目配置文件），本文随后删除。

## 动机

把 gherkai 从 AgentCore 托管的桌面浏览器延伸到 AWS 托管的真机（Device Farm），覆盖设备上的网页与应用；用例、引擎、确定性 step、云端后端、证据链全部复用，设备、模型、凭证、费用仍留在使用方自己的 AWS 账户里。

## 已核的外部事实（2026-09-20 与 2026-10-13）

- Device Farm 只在 us-west-2；按量 0.17 美元每设备分钟或包月槽位；首次 1000 分钟免费；远程访问会话上限 150 分钟不可调；默认并发远程访问 2 台、自动化 5 台，可申请提高。
- 两种使用模式：自动化测试是上传测试包由 Device Farm 的主机执行；远程访问是给一台真机的会话、由外部驾驭。2025-11 起远程访问会话给出托管 Appium 端点（WebDriver over HTTPS）。我们的外部 worker 加事件流的形态只与远程访问同构，自动化模式不走。
- 不给 adb：远程调试与 ssh 公钥字段已退役，adb 只在 Device Farm 自己的测试主机里。Midscene 的 Android 包（adb）用不上，走 Midscene「接任意界面」的接口写 WebDriver 适配器。
- 公共设备 181 台：Apple 75、Samsung 55、Google 43、Xiaomi 6（国际版 ROM）、LG 2；无华为、荣耀、OPPO、vivo。远程访问可用且高可用的 Android 真机含 Redmi Note 13 / 13+（Android 15）、Xiaomi 13 系列、Samsung Galaxy Tab 系列。
- Appium 是开源的 WebDriver 服务器（OpenJS Foundation），驱动 UiAutomator2（Android）与 XCUITest（iOS，经设备上的 WebDriverAgent）；既测应用也测设备浏览器里的网页。
- Midscene 1.15.1：`@midscene/core` 暴露 `AbstractInterface`（截图、尺寸、动作集三件）与 `defineAction*` 一族；Android / iOS 包分别要 adb / WebDriverAgent；1.14 起 iOS 支持网关形态的 WDA 地址。
- 跳板机实例角色对 Device Farm 有写权限（2026-10-13 建项目成功）；spike 项目 `gherkai-spike`。

## 讨论定下的设计（2026-10-13，待 spike 数据后立 ADR）

**三个正交维度**：engine（谁思考，不扩）；device（desktop / android / ios，scenario 级 tag，默认 desktop）；ui_kind（web / app，由起步 step 推出：引号内是地址即网页，等于已绑定的应用别名即启动应用，其余交 AI）。桌面只有 web 是产品范围，不造空位。

**capabilities 升 schema 2**：顶层加 `targets`，每条 `{device, ui_kinds}`；每条确定性 step 带同形 `targets`；`min_grace_s` 留顶层、取各目标最大值。按设备拆的条件：最大值超过 Fargate 120 秒硬顶把 midscene 的 doctor 行连坐成已知差距，或本机默认宽限被明显抬高；拆法是该键改成按设备的对象，读到数当对所有设备生效。目标到句柄的映射不进协议，写进用户指南与 skill。

**core 的改动**：解析 (device, ui_kind)，查 worker 的 `targets`，不支持在 plan 阶段拒绝并列可选；step 在该目标无实现则标注为走 AI（比今天只写一侧的静默降级更安全）。

**确定性 step 多实现注册**：

```ts
deterministic(pattern, {
  playwright: async ({ page }, g) => { ... },
  webdriver: { uiKinds: ["web"], handler: async ({ driver, uiKind, device }, g) => { ... } },
}, meta);
```

键是句柄种类；传单个函数等于只有 `playwright`，老项目零迁移；Python 装饰器同构（字典形态）。设备侧句柄 WebdriverIO，Python 对应 Appium Python Client。

**单测分三档**：网页类用本机下载的 Chrome for Testing 加构造 HTML；应用类用 gherkai 提供的带类型假 driver 加声明式元素树（`@gherkai/worker-midscene/testing`）；handler 保持薄。设备上的 `run --scope` 是验收不是单测，默认由人或 CI 触发，项目约定可放行。录制回放不做。

**项目配置文件** `gherkai.toml`：取值顺序选项 > 环境变量 > 配置文件 > 内建默认；`--config` 或 `GHERKAI_CONFIG`，缺省读当前目录、不存在不算错；节 `[common]`（键名与选项同词）、`[cloud]`、`[devices]`、`[apps]`。只有 CLI 读它。应用别名在 `[apps]` 绑到包或已装包名；Device Farm 项目云端由部署方建并存 SSM，本机后端走选项、环境变量或配置文件。

**设备要求**：feature 里的约束（OS 版本、形态、机型），匹配设备清单而非 worker 能力；速败放 run / submit 前置与 doctor，plan 保持零费用；现在只做 `@device`，要求型 tag 留命名空间。

**分两步**：先设备上的网页，再应用。

## spike 清单

共用检查项，缺一项即日后一个坑：

1. 会话生命周期：建会话到可用的时间；150 分钟上限到 `@timeout` 的映射；主动停止耗时（决定 `min_grace_s`）；并发到 2 台时第三个请求是排队还是报错。
2. Appium 端点鉴权形态与有效期；从 us-east-1 调 us-west-2 的往返延迟。
3. WebDriver 适配器：截图、尺寸、点、滑、输入、按键、返回、主屏、打开地址、启动应用；每个命令往返时间；截图分辨率与 DPR 进 Midscene 后坐标是否对得上。
4. 设备网页：Android Chrome（iOS Safari 其后）跑一个页面，AI 步准确率、每步耗时、token，对比桌面同一页面。
5. 应用：从公网或 S3 装一个开源 app，启动、几步操作与断言；准确率；控件树里确定性 step 能拿到什么。
6. evidence 管线：现有抽取是否零改动可用、截图落盘是否照旧。
7. Device Farm 自带录像与日志的获取方式。
8. 失败形态：设备不可用、app 崩溃、会话中途断、模型 5xx。
9. 费用：设备分钟加模型 token 折成每条 scenario，与桌面对比。
10. 中国场景：依赖国内网络的应用从美国机房出网的表现。
11. 假 driver 要覆盖的 WebdriverIO API 面（由真实 step 用到的方法决定）；Chrome for Testing 的驱动管理是否如预期。
12. Midscene iOS 包的网关 WDA 形态能否对上 Device Farm（顺手验）。

## 进度

- 2026-10-13：权限核过、项目 `gherkai-spike` 已建；spike A 脚本 `engines/midscene/spikes/06-devicefarm-appium.mts`，在跳板机执行了三轮（Redmi Note 13 / Android 15 / Chrome，模型 GPT-5.6 Terra 经 us-east-1 Bedrock）。
- 2026-10-13（续）：同一脚本加平台与场景开关（`DF_PLATFORM`、`SPIKE_SCENARIO`、`DF_APP_URL`），iOS Safari 两台各执行到 6 步全对（iPhone 7 / iOS 15.8.4 三轮、iPhone 17 Pro / iOS 26.3.1 四轮），原生应用（维基百科 Android 客户端）两轮；数据见下两节。
- 2026-10-14：脚本加 `egress`（出网探针）与 `faults`（失败形态）两个场景并接入 worker 的 evidence 抽取；清单第 6、8、9、11、12 项有了实测或结论，第 5 项补了 `appium:app` 安装路线与 iOS 原生应用（AWS 示例 IPA，两台 iPhone 各两轮），第 10 项网络部分量到、应用本体（高德地图）装上但启动即自退。两天共 25 个会话、约 103 设备分钟。

**待做**：设备忙的形态（等遇到）；evidence 上传器与 explain 端对设备产物的整链真跑（抽取已核，上传与阅读未动）；国内网络影响的应用侧量化（要换一个不做环境自检的国内应用）。

## spike A 数据（设备网页，Android Chrome）

**会话生命周期**：PENDING → PREPARING 约 10 秒 → RUNNING 51 到 72 秒；Appium 建连（新 WebDriver 会话）17 到 26 秒；`deleteSession` 约 0.9 秒；StopRemoteAccessSession 到 COMPLETED 74 到 84 秒（API 调用本身即时返回，计费到 COMPLETED）。三轮设备分钟 4.87 / 2.32 / 4.01，按量价约 0.68 / 0.33 / 0.56 美元。

**WebDriver 命令往返**（跳板机 ap-southeast-1 到 us-west-2）：窗口尺寸 0.22 秒、导航 1.0 到 1.8 秒、标题与地址 0.23 到 0.58 秒、找元素 0.3 秒、读文本 0.7 秒、page source（1.6 MB）2.2 秒、getContexts 3.4 秒。**截图是分水岭**：CHROMIUM 上下文 10.4 到 10.8 秒一张（视口图 1080x2176），NATIVE_APP 上下文 0.6 到 1.0 秒一张（整屏 1080x2400）。

**坐标系**：第一轮用视口截图配原生手势，纵向差一个状态栏加地址栏的偏移，AI 的点击全部落空，动作步失败、重规划把 token 烧到 15 万。第三轮改为截图与手势都在 NATIVE_APP、整屏像素坐标、size 不带 dpr（Midscene 1.15.1 对 size 里的 dpr 打警告并忽略），动作全部命中。

**AI 步（第三轮，6 步全部判对）**：断言 7 到 12 秒、每步约 2.8 千 token；动作「点搜索图标」17 秒 / 1.9 万 token，「输入 Playwright 并进词条」29 秒 / 2.9 万 token；刻意为假的断言判否。合计 5.9 万 token。`replanningCycleLimit: 4` 是必须的，否则失败的动作步会无上限重试。

**evidence 原料照旧**：`report/` 下 6 份 `execution.json`、18 张截图、report.html，`log/ai-config.log` 在；`dump.executions` 可读。现有抽取逻辑应可零改动复用，未实跑抽取。

**Device Farm 自带产物**（`list-artifacts --type FILE`）：会话录像 mp4、Appium 服务器日志、logcat、TCP dump，可作额外产物引用。

**适配器要点**：`appium:newCommandTimeout` 必须抬高（默认 60 秒，模型思考期间会被回收）；`url()` 要临时切回 CHROMIUM；WebdriverIO 的 `$()` 严格模式会在页面有两个同名元素时抛错，确定性 step 的写法要用 `$$()` 或更窄选择器。

**设备清单补充**：远程访问可用的 iOS 真机 14 台，iOS 15.0 到 26.6（iPhone 6s / 7 / 11 / 12 / 13 / 14 / 16 / 16 Plus / 17 Pro、iPad 9 / Pro），当天高可用；Pixel 9 系列（Android 15 / 17）与 Pixel Tablet 可用。

## spike A 数据（设备网页，iOS Safari：iPhone 7 / iOS 15.8.4 与 iPhone 17 Pro / iOS 26.3.1）

**会话与建连**：RUNNING 61 到 72 秒，与 Android 同级；Appium 建连差距大：iPhone 7 为 65 秒（WebDriverAgent 在老机器上启动慢），iPhone 17 Pro 为 17 秒。StopRemoteAccessSession 后 iOS 会话在 STOPPING 停留超过 2 分钟（Android 60 到 85 秒到 COMPLETED），计费分钟在 COMPLETED 后才出现（iOS 各轮 1.6 到 5.3 分钟）；worker 只需发出 Stop 即可退出，不必等 COMPLETED。Device Farm 的 Appium 服务端是 2.11.5（`GET /status`）。

**截图与坐标**：iOS 截图不分上下文，都是整屏像素（750x1334、1206x2622），0.3 到 0.8 秒一张，没有 Android 视口截图 10 秒的问题。XCUITest 手势用点不用像素，比例取 `mobile: deviceScreenInfo` 的 `scale`（2 与 3），截图像素除以比例即手势坐标；两台机器动作全部命中。`getWindowRect` 在 iOS 26.3 上两种上下文都报错，不能用它反推比例。

**网页上下文按系统版本分水岭**：iOS 15.8 的 Safari 网页上下文完整可用（导航 1.5 到 1.8 秒、标题与地址 0.2 秒、找元素 0.25 秒、page source 1.8 到 2.0 秒，与 Android 同级）。iOS 26.3 的网页上下文整体不可用：`window/rect`、`title`、`url`、`elements` 都返回 WebKit 远程检查器错误 `'Runtime' domain was not found`（Device Farm 的 appium-xcuitest-driver 对 iOS 26 的检查器协议过旧），`driver.url()` 不报错但页面没动。替代导航是 XCTest 侧的 `mobile: deepLink`（0.3 秒，Safari 打开地址），之后全程只用原生上下文：截图、点、输入都通，6 步全对。**含义**：iOS 26 上 DOM 选择器类的确定性 step 在 Device Farm 现状下做不了，只能原生控件树或 AI；这是 Device Farm 侧版本问题，不是方案问题，设计里要把「网页上下文不可用」当成一种运行时能力缺口处理而不是假定它一定在。

**输入路线**（iOS 没有键码，四条候选在 AI 点开并聚焦搜索框之后逐条实测、经网页上下文读回 value）：

| 路线 | iPhone 7 / iOS 15.8.4 | iPhone 17 Pro / iOS 26.3.1 |
|---|---|---|
| 网页上下文活动元素加 sendKeys（W3C 标准，经远程检查器 type 原子） | 落字，1.3 秒 | 网页上下文不可用，不通 |
| NATIVE_APP 活动元素加 sendKeys（W3C 标准 `GET /element/active` 加 `element/value`） | 报无此元素 | 落字，1.4 秒（读回要靠下一步截图：探针两条路线各打一遍后字段里出现了重复文本） |
| Appium 旧版 `POST /keys`（XCUITest 转 WDA `/wda/keys`） | 不报错、不落字，51 秒（WDA 等键盘超时） | 落字，1.2 秒 |
| W3C 键盘动作（WebdriverIO 的 `keys`） | 不报错、不落字，50 到 53 秒 | 未单测 |
| 谓词 `hasKeyboardFocus == 1` 找元素 | 找不到元素 | 找不到元素 |

`mobile: keys` 只在 iOS 17+ 的 iPad 上有效，没列入。**含义**：标准路线就够、不需要 `/wda/keys`——网页上下文可用时对网页活动元素 sendKeys，不可用时对原生活动元素 sendKeys；两条都是 W3C 的 `element/active` 加 `element/value`，差别只在当时所在的上下文。失败的路线有的不抛错、只耗 50 秒，所以择路要靠会话开头的能力探测（网页上下文是否可用）一次定下，不能在运行期试错回落。

**AI 步**：两台各 6 步全对（iPhone 7 两轮、iPhone 17 Pro 一轮）；iPhone 7 合计 4.0 到 4.8 万 token（动作步 15 到 16 秒 / 1.6 万与 16 到 23 秒 / 1.6 到 2.4 万），iPhone 17 Pro 合计 6.2 万 token（动作步 21 秒 / 2.0 万与 40 秒 / 3.0 万）。两处提示词教训：iOS 26 的 Safari 地址栏在底部，「点击页面顶部的搜索图标」会让模型以「顶部没有」拒做，改成只说搜索图标；输入路线失败时模型会反复重试到重规划上限、再烧 4 万 token，所以路线必须先确定性探明再交给 AI。

**并发**：三个远程访问会话同时 RUNNING（两台 iOS 加一台 Android），另有两个 STOPPING，创建全部被接受；文档写的默认 2 台并发没有在本账号出现，`service-quotas` 查不到 Device Farm 的配额项。worker 侧仍要按「创建会话可能被拒」写重试与排队，上限以账号实测为准。

## spike B 数据（原生应用：维基百科 Android 客户端 50611，Redmi Note 13）

**装应用两条路都通，定下只用 S3 一条**。其一 Device Farm 上传：`CreateUpload`（ANDROID_APP）拿预签名地址 PUT 88 MB 用 7 秒，服务端处理 5.4 秒，`metadata` 给出包名与版本（`org.wikipedia`、50611）、可按名复用；会话 RUNNING 后 `InstallToRemoteAccessSession` 调用 0.2 秒返回，设备上 `isAppInstalled` 11.6 到 17.4 秒后为真，`activateApp` 0.4 到 0.5 秒。其二 `appium:app` 给 https 地址让 Appium 主机下载安装：公网地址（f-droid.org 的 10 MB APK）与 S3 预签名地址（88 MB）配 `appium:autoLaunch: false` 都在建会话时装上（16 与 21 秒含下载），说明 **Device Farm 的 Appium 主机能出公网也能到 S3**。此前两次失败各有别的原因：对 releases.wikimedia.org 报「Download returned empty or failed」是那个源站对主机侧请求的个别表现；不给 `appium:autoLaunch: false` 又没配 appPackage / appActivity 时下载装好了却卡在启动，报「Cannot start the application … adbExec」。**含义**：应用分发走 S3 一条路——CLI 把本地文件按内容哈希放进现有产物桶（QA 机器权限不变），worker 建会话前预签名、交给 `appium:app`；iOS 的签名由 Device Farm 在这条路径上重做（见 iOS 节的未签名与 ad-hoc 变体实测），Device Farm 的上传 API 不引入。约束是单条 Appium 命令 4 分钟上限，S3 到主机实测约 6 MB 每秒；两个平台都要显式给包名或 bundle id、不靠 Appium 猜启动活动。

**不带应用能力的 UiAutomator2 会话可以建**（先连、再装、再启），建连 13 秒；Device Farm 给会话加了 `autoGrantPermissions`、`skipUnlock`、`suppressKillServer`、`printPageSourceOnFindFailure` 等默认能力。

**截图**：应用内 2.0 到 2.2 秒一张（Chrome 会话的原生截图 0.6 到 1.0 秒；桌面启动器上 4.4 到 5.3 秒），`waitForIdleTimeout` 设 0 没有变化，差距另有原因待查；每个 AI 步因此多一到两秒。

**AI 步**：两轮各 8 步，判断全部与真实界面一致。第一轮两条为假是断言写错了（首页顶部没有搜索栏、搜索在底部标签；精确命中「Playwright」打开的是剧作家词条不是软件），第二轮改写后全真。引导页有五页、Skip 在第五页才出现，一条「跳过引导」动作步走了 5 次规划、50 秒、5.2 万 token，`replanningCycleLimit` 4 不够、放到 8；「底部 Search 标签、输入、点 Playwright (software)」动作步 65 到 76 秒、6.5 到 8.7 万 token，途中还自行关掉了一张推广浮层。全轮 12.6 到 14.8 万 token、5.4 到 5.8 设备分钟。原生应用的动作步比网页贵一倍以上：页面长、每轮规划都带整屏截图。

**控件树**：引导页是 Compose（`androidx.compose.ui.platform.ComposeView` 下全是无文本、无 resource-id 的 `android.view.View`），page source 6 KB、只有 `action_bar_root` 与 `android:id/content` 两个 id，确定性 step 在这种页面上拿不到任何锚点。词条页是经典 View：page source 11 KB，有 21 个 resource-id（`page_toolbar_button_search`、`page_save`、`page_find_in_article`、`page_web_view`、`tabsCountText` 等）与工具栏文本（Save、Language、Find in article、Theme、Contents、Search Wikipedia），原生控件层的确定性 step 可按 id 或文本锚定；词条正文在 `page_web_view` 里，上下文列表始终只有 `NATIVE_APP` 与 `WEBVIEW_chrome`（应用自己的 WebView 不可调试、没有网页上下文），正文内容拿不到 DOM。**含义**：原生应用上确定性 step 的可用面取决于被测应用的实现（经典 View 可锚、Compose 无 testTag 不可锚、WebView 正文不可锚），skill 里要把「先看 page source 再决定写不写确定性 step」写成规则。

## spike B 数据（原生应用：iOS，AWS Device Farm 示例应用，iPhone 7 / iOS 15.8.4 与 iPhone 17 Pro / iOS 26.3.1）

iOS 应用只能装 .ipa，App Store 不提供文件，公开可得的只有 AWS 为 Device Farm 发布的示例应用预构建 IPA（aws-device-farm-sample-app-for-ios 仓库 `prebuilt/`，2018 年构建，bundle id `Amazon.AWSDeviceFarmiOSReferenceAppDemoReinvent2018`，标签栏加多种控件的演示页）。**含义**：使用方测 iOS 应用必须自带开发版 IPA，Device Farm 会重签名；两代系统都装得上这个 2018 年的包。

**装与连**：上传 2 MB 用 1.8 秒、处理 5.4 秒；`InstallToRemoteAccessSession` 后 6.1 到 6.3 秒出现在设备上，`activateApp` 1.4 到 1.8 秒。IPA 放 S3、以预签名地址交给 `appium:app`（配 `appium:autoLaunch: false`）在 iPhone 17 Pro 上 3.8 秒装上。签名无关性专门验过：这个 IPA 自带的 provisioning profile 2018 年即过期、只登记了一台设备，照样能装；再把它拆成**完全未签名**与**ad-hoc 签名**（`codesign -s -`，无身份、无 profile）两个变体放 S3 走同一路径，两个都在 3.6 秒内装上并启动到前台（`queryAppState` 为 4）。**结论**：Device Farm 在 Appium 的安装路径上也做重签名，使用方的 IPA 不论怎么签都能装，应用分发只需 S3 一条通路，Device Farm 的上传 API 不必引入。Device Farm 对上传件的保留期是 30 天、日志与录像 400 天（官方数据保留表）。不带 bundleId 的 XCUITest 会话建连只要 1.4 到 1.6 秒（Safari 会话的 17 到 65 秒多在起浏览器与接远程检查器上）。应用内截图 0.3 到 0.6 秒；主屏上 2 到 3.4 秒。

**输入路线在原生应用里不同于 Safari**，且标准路线可用（示例应用 More → Login 页的文本框，确定性探针逐条实测、按元素 value 读回）：

| 路线 | iPhone 7 / iOS 15.8.4 | iPhone 17 Pro / iOS 26.3.1 |
|---|---|---|
| 对已知元素 `element/value`（W3C 标准 sendKeys） | 落字，0.8 秒 | 落字，0.9 秒 |
| `GET /element/active` 加 sendKeys（W3C 标准） | 落字，1.1 秒 | 落字，1.2 秒 |
| Appium 旧版 `POST /keys`（WDA `/wda/keys`） | 落字，1.0 秒 | 落字，1.2 秒 |
| 谓词 `hasKeyboardFocus == 1` 找元素 | 找不到元素 | 找不到元素 |

**含义**：原生应用上输入全走 W3C 标准路线——确定性 step 对自己定位到的元素 sendKeys，AI 步对活动元素 sendKeys，不需要 `/wda/keys`；Safari 网页上的输入才是难点（见下条），差别在第一响应者是原生 UITextField 还是网页内容。

**滚动**：W3C 指针拖动在 iOS 26 的分页视图（UIPageViewController）上不翻页，`mobile: swipe` 两代都翻；适配器的 iOS 滚动首选 `mobile: swipe`。

**AI 步**（第二轮，7 步两台全部判对）：翻十页分页找到文本框并输入，iPhone 7 为 73 秒 / 11.6 万 token，iPhone 17 Pro 为 89 秒 / 13.4 万 token（每翻一页一轮规划，`replanningCycleLimit` 要 12）；打开 Alerts 并触发弹窗 25 秒 / 4.1 万 token；断言步 4 到 6 秒、约 2 到 3 千 token。全轮 16.7 到 18.9 万 token。第一轮失败是我的步骤措辞没按应用结构写（分页点点不翻页、Swipe 在动作集外），不是平台问题。

**控件树**：XCUITest 的 page source 给 `XCUIElementType*` 类型加 `name` / `label`（无障碍标识），示例应用首页 3 到 4 KB、弹窗页 11 到 14 KB，标签、按钮、弹窗标题与 OK 按钮都有名字可锚；上下文只有 `NATIVE_APP`。**含义**：iOS 原生应用的确定性 step 可按无障碍标识或文本锚定，前提同 Android：被测应用给了标识。

## 清单第 6、8 到 12 项（2026-10-14）

**第 6 项 evidence 抽取零改动可用**：spike 脚本直接 import worker 的 `buildEvidence` 与 `executionsLength`（`engines/midscene/src/worker/evidence.mts`），按 worker 的做法在每个 AI 步起点记 `agent.dump.executions` 长度、步末切片喂入。失败形态那一轮三步全部产出 evidence：动作步 4 帧 2 张截图、含 thought 与 actions，`act.error` 带 Midscene 的错误文本；断言步 1 帧 1 张截图；会话被外部 Stop 的那步 1 帧 0 张截图（截图还没来得及落盘，这是事实不是抽取失败）。引用到的截图文件全部存在（`missing_files` 为 0）。原因：抽取只读 SDK 的 dump 结构与 `report/screenshots/` 落盘，不碰浏览器，换成 Appium 界面后 dump 形态不变。消费端也核了：把 iPhone 7 原生应用那轮产出的两份 evidence（29 帧的动作步、判否的断言步）放进一次真实本机运行的产物目录替换对应 step 的文件，`gherkai explain` 文本与 `--json` 两种形态都正常渲染——推理、动作、截图 URI、票数齐全，`evidence_missing` 为空。**含义**：设备 worker 复用 evidence 模块、上传器与 explain 即可，`url` 字段在应用场景填空；未真跑的只剩上传器把设备截图送到 S3 这一段（纯字节上传，与来源无关）。

**第 8 项 失败形态**（Android，Redmi Note 13）：

| 形态 | 制造方式 | 观察 |
|---|---|---|
| 设备不支持远程访问 | 对自动化专用机型调 CreateRemoteAccessSession | API 同步抛 ArgumentException「device does not support remote access」，零设备分钟 |
| 并发超限 / 设备忙 | 对同一机型连发 6 个会话请求 | 前 5 个全部到 RUNNING（同机型至少 5 台，机群没被占满）；第 6 个落在 `PENDING_CONCURRENCY`，message 明说「reached the account level concurrency limit」、排队等槽位而不是报错，Stop 可直接撤回。本账号远程访问并发上限实测为 5；排队的会话在前面的会话到 COMPLETED 后自动转 PREPARING（一次实测排了 6 分钟，STOPPING 中的会话占着槽位）；机型本身被占满（BUSY）当天没遇到 |
| 应用在 AI 步中途被杀 | 步开始 4 秒后 `terminateApp` | 模型从截图看出回到桌面，33 秒后 TaskExecutionError「app exited to the home screen」；后续断言步照常判否；evidence 完整 |
| 模型名错误 | 第二个 Agent 用不存在的模型名 | 15 秒、两次尝试后 TaskExecutionError，内含 Bedrock 的 400「provided model identifier is invalid」，文本可直接进 step 消息 |
| 会话被外部 Stop | 步开始 5 秒后调 StopRemoteAccessSession | 正在执行的 AI 步 8 秒内失败，错误是 ValidationException「Device Farm session is not currently running <会话 ARN>」；之后每个 WebDriver 命令 2.2 秒同样报错；`deleteSession` 报连接已关；再调 Stop 报「Invalid parameter RemoteAccessSession」 |
| 150 分钟上限 | `cap` 场景：每分钟一条命令加一次状态查询，挂满上限 | 会话创建后约 150.4 分钟（RUNNING 后约 149 分钟）命令开始报「The remote access session is shutting down. Please check Device Farm logs」，此时 GetRemoteAccessSession 仍报 RUNNING；一分钟后端点改报 AccessDeniedException「Invalid pre-signed URL」（端点地址随会话作废）；再一分钟 API 到 COMPLETED、result 为 STOPPED，计费 150.29 分钟（从创建算、不从 RUNNING 算）。**含义**：上限按创建时刻计、worker 的会话预算要从 CreateRemoteAccessSession 起算并留出建会话的 60 到 80 秒；「shutting down」与「Invalid pre-signed URL」两条错误文本都唯一对应到期，可直接映射为会话到期类错误 |

**含义**：三类失败的错误文本都可机械区分（ArgumentException / ValidationException 带「not currently running」/ 模型 400），worker 可据此分类成 engine_error 与 network_error 而不是笼统的 failed；外部 Stop 后不要再调 Stop 与 deleteSession 做清理，报错即退出。

**第 9 项 费用折算**（单价：Device Farm 按量 0.17 美元每设备分钟、不计量槽位 250 美元每月、免费 1000 分钟；AgentCore Browser 0.0895 美元每 vCPU 小时加 0.00945 美元每 GB 小时；GPT-5.6 Terra 标准层输入 2.20、输出 13.20 美元每百万 token；Fargate 0.0405 美元每 vCPU 小时加 0.0044 美元每 GB 小时。采集日 2026-10-14）。桌面对照用同一组 6 步在跳板机本机 Midscene worker（1.15.1）上执行：

| 项 | 桌面（AgentCore 形态估算） | Android Chrome 真机 | iOS Safari 真机 | Android 原生应用 | iOS 原生应用 |
|---|---|---|---|---|---|
| 步数与 token | 6 步 5.5 万（动作步 1.9 万与 2.8 万，断言步约 2 千） | 6 步 5.9 万 | 6 步 4.0 到 6.2 万 | 8 步 12.6 到 14.8 万 | 7 步 16.7 到 18.9 万（翻十页那一步占 11.6 到 13.4 万） |
| 墙钟 | 76 秒 | 约 100 秒 | 约 70 到 100 秒 | 约 180 到 200 秒 | 约 130 到 150 秒 |
| 模型费（按 95% 输入估） | 约 0.15 美元 | 约 0.16 美元 | 约 0.11 到 0.17 美元 | 约 0.35 到 0.40 美元 | 约 0.45 到 0.50 美元 |
| 会话费 | 浏览器加 worker 不到 0.01 美元 | 设备分钟 2.0 到 4.5 分钟即 0.34 到 0.77 美元 | 1.6 到 5.3 分钟即 0.28 到 0.90 美元 | 5.4 到 5.8 分钟即 0.92 到 0.98 美元 | 3.2 到 5.2 分钟即 0.55 到 0.88 美元 |
| 每条 scenario 合计 | 约 0.15 美元 | 约 0.5 到 0.9 美元 | 约 0.4 到 1.1 美元 | 约 1.3 到 1.4 美元 | 约 1.0 到 1.4 美元 |

token 与模型费桌面和真机同量级（同一模型、同样靠截图驱动），原生应用贵在动作步要翻页、每轮规划带整屏截图；真机贵出来的另一半是设备分钟，其中会话建立 60 到 72 秒、停止到 COMPLETED 60 到 150 秒是每会话固定开销且计入分钟（FAQ：从准备设备到清理完毕都计）。**含义**：设备会话必须按 scope 复用而不是按 scenario 开（与桌面同策略），固定开销摊到多条 scenario 上才划算；每月每平台设备分钟超过约 1470 分钟（250 除以 0.17）时不计量槽位更便宜，`[devices]` 配置要能选 billingMethod。

**第 10 项 国内网络**（真机侧，Redmi Note 13 Chrome，us-west-2）：设备出网源 IP 落在官方公布的设备地址段 99.78.197.0/29 内。同一台设备顺序打开：维基百科 3.0 秒；百度 31 秒；高德网页版 119 秒；天气网 74 秒；微博 7 秒但落到「Sina Visitor System」反爬页。**含义**：依赖国内后端的应用在美国机群上页面加载慢一到两个量级，`@timeout` 与 Appium 的 `newCommandTimeout` 都要按此放宽，且部分站点按 IP 判定会给机器人页；Device Farm 官方的网络手段只有 deviceProxy（2025-02 新增，公共设备与 iOS 上是否生效无依据）与私有设备加 VPC-ENI 经客户 NAT，没有 VPN。

**高德地图应用本体（17.01.0 正式版，官方 CDN 直链，194 MB，`com.autonavi.minimap`）**：官方下载源只对境内网络开放，APK 由境内网络下载后放到跳板机；Device Farm 上传 19.5 秒、处理 5.4 秒，会话内安装 23 秒。**但应用在这台公共真机上启动即自行退出**：`activateApp` 与按活动名显式启动都返回成功，应用状态轨迹只在启动后短暂到过后台态、随即回到未运行；logcat 里是进程自己正常退出（退出码 0、没有异常栈），启动页到地图主活动都创建过。这是应用侧的环境自检主动退出，不是崩溃，也不是 Device Farm 的安装或启动问题；AI 步随后面对的是桌面，六条判断全部如实判否。**含义**：带环境自检的国内消费级应用在公共真机上可能根本不给测，这是被测应用的限制、要在设计文档里写明「启动后应用自行退出」属于 pre-check 应报的失败形态（应用状态轨迹是判据）；本工具不做任何规避。国内网络影响的量化只取到了真机浏览器那组数据。

**Appium 主机侧出网**（兼核第 5 项的安装路径）：`appium:app` 填 f-droid.org 公网地址与 S3 预签名地址，配 `appium:autoLaunch: false`，两条都下载并安装成功（见 spike B 数据节）。官方文档对托管 Appium 主机的出网与出口 IP 没有说法，这是现场证据；出口 IP 未测——可行的办法只有让主机访问一个自己能看访问日志的 https 端点，用第三方请求记录站的做法被本机的自动模式安全策略拦下、不绕，自建端点（Lambda 函数地址）需要账号里有可用的执行角色，待 owner 决定要不要做。

**替代国内应用：中国天气 9.1.0.14（owner 提供的 APK，包名 `com.hf`，启动活动 `WelcomeActivity`，目标 SDK 34）**：上传 7 秒、处理 5.4 秒、会话内安装 11.7 秒；`activateApp` 与按活动名显式启动都返回成功，系统日志显示启动页进程创建后随即死亡（与高德同一形态：自行退出、无异常栈），应用状态轨迹全程停在「未运行」。两款国内消费级应用在同一台公共真机上同一表现，而维基百科客户端与 AWS 示例应用正常，差别在前者带的第三方 SDK 环境自检（反调试 / 自动化检测）。**含义**：国内消费级应用的线上包基本不可在公共真机上测，使用方得提供关闭自检的测试包（QA 包），这是产品说明里要写明的前提；本工具不做任何规避。官方下载源的脚本抓取对境外一律不开放（中国天气新版、12306、哔哩哔哩都重定向环或 403），APK 只能由境内人工取得。脚本已备好对任意包名的通用步骤组（关弹窗、确认首页、搜索一个词），下一个样本给 APK 即可直接执行。

**第 11 项 假 driver 的 API 面与 Chrome for Testing**：适配器加确定性探针实际用到的 WebdriverIO 面——会话：`status`、`sessionId`、`deleteSession`；上下文：`getContext`、`getContexts`、`switchContext`；画面：`takeScreenshot`、`getWindowRect`、`getPageSource`；手势与按键：`execute("mobile: …")`（Android 的 clickGesture / longClickGesture / type / pressKey / scrollGesture，iOS 的 tap / touchAndHold / pressButton / deepLink / deviceScreenInfo）、`performActions` 加 `releaseActions`、`keys`、原始 `POST /keys`；元素：`$` / `$$`（CSS、`id=`、xpath）、`getText`、`getValue`、`getAttribute`、`click`、`isDisplayed`、`getActiveElement`、`elementSendKeys`、`elementClear`、`getElementAttribute`；网页：`url`、`getUrl`、`getTitle`、`back`；应用：`isAppInstalled`、`activateApp`、`terminateApp`、`updateSettings`。确定性 step 的作者在应用上只会用到元素与上下文那两组加 `getPageSource`，所以假 driver 的最小面是：声明式元素树（class、resource-id / name、text、content-desc、bounds、displayed、enabled）、选择器解析（`id=`、`~` 无障碍 id、`android=` / `-ios predicate string`、xpath 子集）、元素动作改状态（click 触发回调、setValue 写 text）、`waitForDisplayed` 的时间语义、把树渲染成 page source XML；手势类 `execute` 一律不进假 driver（那是 AI 步的事）。Chrome for Testing：WebdriverIO 10 不配 Selenium 服务时自行下载浏览器与驱动，没装 Chrome 的跳板机首次建会话 18 秒（含下载，Chrome 399 MB 加 chromedriver 24 MB），装了 Chrome 的 Mac 用已装浏览器配匹配驱动 6 秒；**缓存落在 `os.tmpdir()`**（`/tmp/chrome`、`/tmp/chromedriver`）而不是 `~/.cache`，重启即丢，单测脚手架要显式给 `cacheDir` 或 `WEBDRIVER_CACHE_DIR`。

**第 12 项 Midscene iOS 包对 Appium 端点**：读 `@midscene/ios@1.15.1` 与 `@midscene/webdriver` 源码并对照 appium 2.11.5 / base-driver 9.11.5 / xcuitest-driver 7.35.1 的路由表（解包在 /tmp 核对），三处硬阻断：连接前先探 `GET /status` 并要求响应含 `sessionId`，Appium 的 `/status` 只有 ready / message / build（Device Farm 端点实测亦如此）；建会话的 caps 里 `automationName` 等不带 `appium:` 前缀，Appium 直接拒；所有手势、按键、启动应用走 `/wda/*` 直连路由，Appium 一律 404、只经 `mobile:` 命令暴露。能通的只有截图、window/rect、actions、元素查找与点击、url。网关模式 `wdaBaseUrl` 保留路径前缀这一点没问题，`sessionId` 可复用。**结论**：不接，继续用自己的 WebdriverIO 适配器；值得借的是逻辑而非传输层——收键盘策略与 DPR 回退算法（截图长边除以窗口长边取整）。

