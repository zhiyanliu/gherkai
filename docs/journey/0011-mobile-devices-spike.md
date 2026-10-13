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

- 2026-10-13：权限核过、项目 `gherkai-spike` 已建；spike A 脚本 `engines/midscene/spikes/06-devicefarm-appium.mts`，在跳板机跑了三轮（Redmi Note 13 / Android 15 / Chrome，模型 GPT-5.6 Terra 经 us-east-1 Bedrock）。

## spike A 数据（设备网页，Android Chrome）

**会话生命周期**：PENDING → PREPARING 约 10 秒 → RUNNING 51 到 72 秒；Appium 建连（新 WebDriver 会话）17 到 26 秒；`deleteSession` 约 0.9 秒；StopRemoteAccessSession 到 COMPLETED 74 到 84 秒（API 调用本身即时返回，计费到 COMPLETED）。三轮设备分钟 4.87 / 2.32 / 4.01，按量价约 0.68 / 0.33 / 0.56 美元。

**WebDriver 命令往返**（跳板机 ap-southeast-1 到 us-west-2）：窗口尺寸 0.22 秒、导航 1.0 到 1.8 秒、标题与地址 0.23 到 0.58 秒、找元素 0.3 秒、读文本 0.7 秒、page source（1.6 MB）2.2 秒、getContexts 3.4 秒。**截图是分水岭**：CHROMIUM 上下文 10.4 到 10.8 秒一张（视口图 1080x2176），NATIVE_APP 上下文 0.6 到 1.0 秒一张（整屏 1080x2400）。

**坐标系**：第一轮用视口截图配原生手势，纵向差一个状态栏加地址栏的偏移，AI 的点击全部落空，动作步失败、重规划把 token 烧到 15 万。第三轮改为截图与手势都在 NATIVE_APP、整屏像素坐标、size 不带 dpr（Midscene 1.15.1 对 size 里的 dpr 打警告并忽略），动作全部命中。

**AI 步（第三轮，6 步全部判对）**：断言 7 到 12 秒、每步约 2.8 千 token；动作「点搜索图标」17 秒 / 1.9 万 token，「输入 Playwright 并进词条」29 秒 / 2.9 万 token；刻意为假的断言判否。合计 5.9 万 token。`replanningCycleLimit: 4` 是必须的，否则失败的动作步会无上限重试。

**evidence 原料照旧**：`report/` 下 6 份 `execution.json`、18 张截图、report.html，`log/ai-config.log` 在；`dump.executions` 可读。现有抽取逻辑应可零改动复用，未实跑抽取。

**Device Farm 自带产物**（`list-artifacts --type FILE`）：会话录像 mp4、Appium 服务器日志、logcat、TCP dump，可作额外产物引用。

**适配器要点**：`appium:newCommandTimeout` 必须抬高（默认 60 秒，模型思考期间会被回收）；`url()` 要临时切回 CHROMIUM；WebdriverIO 的 `$()` 严格模式会在页面有两个同名元素时抛错，确定性 step 的写法要用 `$$()` 或更窄选择器。

**设备清单补充**：远程访问可用的 iOS 真机以 iPhone XR / X / SE（iOS 15 到 16）为主，另有 iPhone Air（iOS 26.3.1）；Pixel 9 系列（Android 15 / 17）与 Pixel Tablet 可用。

**待做**：iOS Safari 一轮；原生应用一轮（spike B，需定一个开源 APK 与一个依赖国内网络的应用）；并发到 2 台时第三个请求的表现；evidence 抽取真跑。
