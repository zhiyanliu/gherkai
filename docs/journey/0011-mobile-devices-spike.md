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
- 2026-10-13（续）：同一脚本加平台与场景开关（`DF_PLATFORM`、`SPIKE_SCENARIO`、`DF_APP_URL`），iOS Safari 两台各执行到 6 步全对（iPhone 7 / iOS 15.8.4 三轮、iPhone 17 Pro / iOS 26.3.1 四轮），原生应用（维基百科 Android 客户端）两轮；数据见下两节。清单第 1、2、3、4、5、6、7 项有了实测，第 8、9、10、11、12 项未动。

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
| 网页上下文活动元素加 sendKeys（远程检查器 type 原子） | 落字，1.3 秒 | 网页上下文不可用，不通 |
| Appium 旧版 `POST /keys`（XCUITest 转 WDA `/wda/keys`，打到第一响应者） | 不报错、不落字，51 秒（WDA 等键盘超时） | 落字，是这台机器上唯一通的路线 |
| W3C 键盘动作（WebdriverIO 的 `keys`） | 不报错、不落字，50 到 53 秒 | 未单测（AI 阶段没轮到） |
| NATIVE_APP 活动元素加 sendKeys | 报无此元素 | 网页上下文探针失败、未单测 |

`mobile: keys` 只在 iOS 17+ 的 iPad 上有效，没列入。**含义**：没有一条路线同时覆盖两代系统，适配器必须按能力探测择路（网页上下文可用则走原子路线，否则走 `/wda/keys`），且失败的路线不抛错、只耗 50 秒，不能靠异常回落，要靠读回或超时判定。

**AI 步**：两台各 6 步全对（iPhone 7 两轮、iPhone 17 Pro 一轮）；iPhone 7 合计 4.0 到 4.8 万 token（动作步 15 到 16 秒 / 1.6 万与 16 到 23 秒 / 1.6 到 2.4 万），iPhone 17 Pro 合计 6.2 万 token（动作步 21 秒 / 2.0 万与 40 秒 / 3.0 万）。两处提示词教训：iOS 26 的 Safari 地址栏在底部，「点击页面顶部的搜索图标」会让模型以「顶部没有」拒做，改成只说搜索图标；输入路线失败时模型会反复重试到重规划上限、再烧 4 万 token，所以路线必须先确定性探明再交给 AI。

**并发**：三个远程访问会话同时 RUNNING（两台 iOS 加一台 Android），另有两个 STOPPING，创建全部被接受；文档写的默认 2 台并发没有在本账号出现，`service-quotas` 查不到 Device Farm 的配额项。worker 侧仍要按「创建会话可能被拒」写重试与排队，上限以账号实测为准。

## spike B 数据（原生应用：维基百科 Android 客户端 50611，Redmi Note 13）

**装应用只有 Device Farm 上传一条路**：`CreateUpload`（ANDROID_APP）拿预签名地址 PUT 88 MB 用 7 秒，服务端处理 5.4 秒，`metadata` 给出包名与版本（`org.wikipedia`、50611）、可按名复用；会话 RUNNING 后 `InstallToRemoteAccessSession` 调用 0.2 秒返回，设备上 `isAppInstalled` 11.6 到 11.7 秒后为真，`activateApp` 0.4 到 0.5 秒。`appium:app` 给公网地址让 Appium 主机自己下载的路线失败：主机报 `Failed to download app … Download returned empty or failed`，Device Farm 的 Appium 主机不出公网；这一轮白耗 1.2 设备分钟。**含义**：`[apps]` 里的应用要由 CLI / worker 先上传成 Device Farm 的 upload（按内容哈希复用），会话内再安装；不能把地址直接塞给 Appium。

**不带应用能力的 UiAutomator2 会话可以建**（先连、再装、再启），建连 13 秒；Device Farm 给会话加了 `autoGrantPermissions`、`skipUnlock`、`suppressKillServer`、`printPageSourceOnFindFailure` 等默认能力。

**截图**：应用内 2.0 到 2.2 秒一张（Chrome 会话的原生截图 0.6 到 1.0 秒；桌面启动器上 4.4 到 5.3 秒），`waitForIdleTimeout` 设 0 没有变化，差距另有原因待查；每个 AI 步因此多一到两秒。

**AI 步**：两轮各 8 步，判断全部与真实界面一致。第一轮两条为假是断言写错了（首页顶部没有搜索栏、搜索在底部标签；精确命中「Playwright」打开的是剧作家词条不是软件），第二轮改写后全真。引导页有五页、Skip 在第五页才出现，一条「跳过引导」动作步走了 5 次规划、50 秒、5.2 万 token，`replanningCycleLimit` 4 不够、放到 8；「底部 Search 标签、输入、点 Playwright (software)」动作步 65 到 76 秒、6.5 到 8.7 万 token，途中还自行关掉了一张推广浮层。全轮 12.6 到 14.8 万 token、5.4 到 5.8 设备分钟。原生应用的动作步比网页贵一倍以上：页面长、每轮规划都带整屏截图。

**控件树**：引导页是 Compose（`androidx.compose.ui.platform.ComposeView` 下全是无文本、无 resource-id 的 `android.view.View`），page source 6 KB、只有 `action_bar_root` 与 `android:id/content` 两个 id，确定性 step 在这种页面上拿不到任何锚点。词条页是经典 View：page source 11 KB，有 21 个 resource-id（`page_toolbar_button_search`、`page_save`、`page_find_in_article`、`page_web_view`、`tabsCountText` 等）与工具栏文本（Save、Language、Find in article、Theme、Contents、Search Wikipedia），原生控件层的确定性 step 可按 id 或文本锚定；词条正文在 `page_web_view` 里，上下文列表始终只有 `NATIVE_APP` 与 `WEBVIEW_chrome`（应用自己的 WebView 不可调试、没有网页上下文），正文内容拿不到 DOM。**含义**：原生应用上确定性 step 的可用面取决于被测应用的实现（经典 View 可锚、Compose 无 testTag 不可锚、WebView 正文不可锚），skill 里要把「先看 page source 再决定写不写确定性 step」写成规则。

**待做**：evidence 抽取真跑（第 6 项）；失败形态（第 8 项）、费用折算（第 9 项）、国内网络应用（第 10 项，待定应用）、假 driver 的 API 面（第 11 项）、Midscene iOS 包的网关 WDA 形态（第 12 项）。
