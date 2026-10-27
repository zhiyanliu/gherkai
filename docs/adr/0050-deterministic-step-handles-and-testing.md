# 0050. 确定性 step 多句柄注册与测试分层

> **Status:** Accepted（2026-10-15）——部分取代 [0036](./0036-deterministic-capability-discovery.md) 决策 1 的注册面签名（handler 位置从单个函数改为按句柄种类分键，单函数写法保持有效），扩展 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 的注册表；匹配语义、元数据必填、角色边界不变。决策 1、2、4 随 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 的修订同日改写：条目可声明前提 `requires`，`ctx.driver` 是受命令守卫的代理，已有运行的 evidence 只在失败步含控件信息。

## 背景与问题

确定性 step 至今只有一种执行对象：桌面浏览器里的 Playwright `page`。注册面是 `deterministic(pattern, handler, meta)`，handler 拿 `ctx.page` 操作页面（Python 侧是同构的装饰器）。测试目标扩到真机之后（目标模型见 [0048](./0048-test-targets-device-and-ui-kind.md)），同一句 step 文本面对的可能是 Android Chrome 里的网页、iOS Safari 里的网页、Android 或 iOS 上的原生应用，执行对象变成 Appium 会话（WebdriverIO 客户端）。由此有四个问题要定：

- **一条 step 怎样在多个目标上各有实现**，且「这条 step 在哪些目标上有实现」能在执行前被 CLI 知道（plan 标注、能力自述的 `targets`，见 [0049](./0049-worker-capabilities-targets-keys.md)），而不是到运行期才在 handler 里发现「这个平台我不会」。
- **handler 拿到什么**：设备会话有原生与网页两种上下文，截图与手势只在原生上下文可靠（[0052](./0052-appium-interface-adapter-and-platform-differences.md)），handler 若切到网页上下文后不切回，下一个 AI 步会在错误的上下文里截图与点击。
- **设备上的确定性 step 怎样测**：桌面上作者可以在本机打开浏览器调试，真机只能经 Device Farm 远程访问会话获得，每次都有取设备的等待与设备分钟费用。
- **作者怎样写出可靠的设备 step**：原生应用上能否定位到控件取决于被测应用的实现，作者需要可执行的判据，而不是「先让 AI 执行一遍再把它固化」这类会把观察到的行为当成期望的流程。

## 决策

### 1. 注册面：handler 位置按句柄种类分键

TS 注册面改为 `deterministic(pattern, handlers, meta)`，`handlers` 以句柄种类为键：

```ts
deterministic("^页面显示「(?<text>[^」]+)」$", {
  playwright: async ({ page }, g) => { /* 桌面浏览器 */ },
  webdriver: [
    { uiKinds: ["web"], devices: ["android", "ios"], handler: async (ctx, g) => { /* 设备网页 */ } },
    { uiKinds: ["app"], devices: ["android"], handler: async (ctx, g) => { /* resource-id 定位 */ } },
    { uiKinds: ["app"], devices: ["ios"], handler: async (ctx, g) => { /* 无障碍标识定位 */ } },
  ],
}, { description: "…", example: "…" });
```

- **两种句柄**：`playwright`（桌面浏览器，含义与现状相同）与 `webdriver`（设备会话，WebdriverIO 客户端）。`webdriver` 可写成单个条目或条目数组，每个条目用 `uiKinds`（取值 `web` / `app`）与 `devices`（取值 `android` / `ios`，与测试目标的 device 维度同名同值）声明适用范围、缺省为全部取值。
- **声明式过滤，不在 handler 里分支**：Android 与 iOS 的选择器不同时写两个条目，不在一个 handler 里按设备 `switch`。理由：适用范围必须在执行前可知，worker 才能从注册表推出每条 step 的 `targets` 写进能力自述，plan 才能逐目标标注「确定性」或「走 AI」；藏在 handler 里的分支对注册表不可见，未覆盖的平台只会在运行期以 error 暴露。
- **单函数写法保持有效**：`handlers` 传单个函数等价于只有 `playwright`，已有项目的 `steps/` 目录不需要任何改动。
- **注册期校验**（违反即加载失败，按 [0037](./0037-distribution-and-packaging.md) 决策 4 的加载失败处理）：未知句柄种类、`uiKinds` 或 `devices` 的未知取值、同一条 step 的两个 `webdriver` 条目覆盖同一个（设备，界面类型）组合。最后一条防止「两个实现谁生效」的歧义，与 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 对模式冲突的处理同理。
- **step 的 `targets` 由句柄推出**：`playwright` 对应 desktop / web，每个 `webdriver` 条目对应其 `devices` 与 `uiKinds` 的全部组合（两个数组各自独立、覆盖它们的笛卡尔积；要排除某个组合就拆成两个条目）；按（设备, 前提）聚合成一条、界面类型收进 `ui_kinds`。**写出顺序固定**：设备按 desktop → android → ios，`ui_kinds` 按 web → app，同一设备下无 `requires` 的条目在前、有的按取值字典序——这条顺序规则只管自述输出，不参与匹配与派发；要它是因为两个 worker 的自述要逐字节一致（跨语言 fixture 整段相等断言）、CLI 缓存与展示不应随作者的书写顺序变，与 `keywords` 自述按 Given / When / Then 固定序同理。实际可用目标再与 worker 自身的 `targets` 取交集，规则与呈现归 [0049](./0049-worker-capabilities-targets-keys.md)。目标上没有句柄的 step 由 plan 标注为走 AI，网页上下文在运行期不可用时的 error 处理归 [0048](./0048-test-targets-device-and-ui-kind.md)。
- **跨 step 的命中与目标无关**：一段 step 文本命中哪些 pattern，仍按 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 的模式冲突规则判定（最多命中一条、多条即冲突报错），判定时不看当前目标；句柄条目的过滤只在命中之后起作用。命中的那条 step 在当前目标上没有句柄时，这段文本走 AI，不顺延到下一条能匹配的 pattern。理由：顺延会让同一段文本在不同目标上匹配到不同 pattern、执行不同语义的 handler，而 plan 与能力自述按 pattern 关联目标，顺延后两者都对不上实际派发。
- **条目可声明前提 `requires`**（可选，字符串数组，1.5 只有 `web_context`）：含 `web_context` 的条目在探测确认设备不提供网页上下文时不被调用、step 记 error 并带类别 `capability_unavailable`（规则归 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 6）。注册期按封闭集合校验取值，未知取值加载失败；含 `web_context` 时 `uiKinds` 必须恰为 `["web"]`（应用目标固定原生上下文，前提没有定义）。推出能力自述时，`requires` 不同的条目拆成不同的 step 级 `targets` 条目、不聚合（[0049](./0049-worker-capabilities-targets-keys.md)）。Python 侧字段与校验同构，纳入跨语言 fixture。
- **条目可声明适用关键字 `keywords`**（可选，Given / When / Then 的子集，缺省全部）：step 文本命中模式但关键字不在集合内时，step 记 error、消息说明「这条写法只在 … 下有意义」，不转 AI、不顺延到别的模式。1.5 只有内建导航条目用它（Given / When，[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 第 3 条）；使用方条目也可声明，如只在 Then 下有意义的核对。注册期校验取值属于封闭集合。
- **注册表里唯一的内建条目是导航**（模式 = 去掉关键字后整句为一个地址，加不加引号都匹配；`playwright` 句柄打开 http(s)，`webdriver` 句柄在应用目标上经 DeepLink 交给被测应用、在网页目标上按能力探测择路，[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7、[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 4）。曾内置的「页面地址匹配」step 已退役（0020 第 2 条）：精确核对地址由使用方自写，设备网页目标上的这类条目声明 `requires: ["web_context"]`，示范进用户指南与 `steps/` 模板。使用方条目若也匹配裸地址，按 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 的冲突规则报错。

**Python 完全同构**：同一组键与条目字段，取字典形态，`webdriver` 句柄拿到的 `driver` 是 Appium Python Client 的 driver；装饰器写法与现状相同、等价于只有 `playwright`。多句柄形态是普通函数调用 `deterministic(pattern, handlers, *, description, example, keywords=None)`，`handlers` 为 `{"playwright": fn, "webdriver": [{"ui_kinds": [...], "devices": [...], "requires": [...], "handler": fn}, …]}`，条目字段按 Python 惯例取 snake_case（与协议面的 `ui_kinds` 同词，不在一个文件里混两种命名）；键名、条目语义、校验规则与 TS 逐项一致，只是字段名方言不同。跨语言 fixture 用协议面的 snake_case 写条目字段，TS 侧测试做一次字段名方言映射（与正则具名组 `(?P<` 到 `(?<` 的方言替换同类）。两侧共用一套跨语言 fixture（同一组注册输入，断言推出的 `targets` 与校验结果相同）来核对注册语义。1.5 没有 Python 设备引擎（Nova Act 驱动的是 Playwright 浏览器，没有设备路径），这块 API 面由 fixture 与注册期校验验收，不以真机执行为前提。

### 2. handler 上下文：七个字段与一条不变量

`webdriver` 句柄的 `ctx` 只有七个字段：

| 字段 | 含义 |
|---|---|
| `driver` | 受命令守卫的 WebdriverIO 客户端代理（Python 侧为 Appium Python Client 的 driver）：step 结束、取消或进入终结后，经旧引用发出的调用被拒绝；命令结果未知后，本 step 内有副作用的命令被拒绝（守卫归 [0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6） |
| `device` | `{ platform, osVersion, scale }`：平台（取值与 device 维度相同，`android` 或 `ios`）、会话回报的系统版本、坐标比例（iOS 取设备报告的 scale，Android 为 1）。字段不叫 `target`，避免与 Job 携带的测试目标同名 |
| `uiKind` | `web` 或 `app` |
| `appId` | 包名或 bundle id，只在 app 目标上有值 |
| `app` | 只在 app 目标上有值，唯一方法 `restart()`：terminate 加 activate 加启动采样，采样到应用自退即抛错（原语归 [0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 3）。它替代了曾计划内置的「重新启动应用」step：产品不内置有措辞的 step（[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 第 2 条），需要干净起点的项目在 `steps/` 里写一条调用它的 step，模板给出 |
| `log` | 写进本 step 诊断的日志函数 |
| `withWebContext(fn)` | 每次重新定位属于被测对象的网页上下文（不缓存句柄，[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 5），切入后执行 `fn`，结束（含抛错）后切回原生上下文；多个候选或零候选时抛错、不猜 |

- `WebdriverCtx` 的类型随注册面一起发布（`driver` 以类型引用 WebdriverIO 客户端；发布的类型声明引用它，使用方做类型检查时要能解析到，故 webdriverio 随注册面列为 Midscene 包的依赖——设备模块落地后它本来就是运行期依赖），实现随设备模块落地；在那之前桌面 worker 对设备目标上的 webdriver 句柄不会派发（设备 job 在建会话前自检被拒，[0049](./0049-worker-capabilities-targets-keys.md) 决策 7）。
- **不变量：step 结束时会话处在原生上下文。** 截图与手势都在原生上下文执行，AI 步开始前也会回到原生上下文（[0052](./0052-appium-interface-adapter-and-platform-differences.md)）；handler 若自行 `switchContext` 不切回，后果是下一步截图坐标错位、点击全部落空。`withWebContext` 是切换上下文的推荐方式；handler 直接调用 `switchContext` 时，worker 在 step 结束后核对并复原，复原失败记 error。
- **网页上下文只认属于被测对象的那个**（判定规则归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)）。会话开头的能力探测确认设备不提供网页上下文时，声明了 `requires: ["web_context"]` 的条目不被调用、step 记 error（类别 `capability_unavailable`），消息说明当前设备不提供网页上下文、建议改用 AI 步或换设备；探测出错（无法确认设备是否提供）时同样不调用，类别记 `engine_error`（规则归 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 6）。没有声明却调用 `withWebContext` 的 handler 由它按同一规则抛出。两种情况都不转 AI。
- **不提供的内容**：不暴露 Device Farm 会话、端点地址、应用的 S3 位置，也不提供「当前是不是 iOS 26」一类判断函数；设备差异由条目过滤表达，版本差异由能力探测在 worker 内处理。

**写进作者文档的输入与定位事实**（据 Android 与 iOS 真机上逐条路线的实测，详见「实测依据」）：

- 原生应用上，对自己定位到的元素调用 `setValue` / `addValue`（W3C 元素 sendKeys）：Android 与 iOS 原生应用实测都可靠（Android 0.3 秒，iOS 0.8 到 0.9 秒，读回一致）。handler 不需要、也不应调用 `mobile: type`、`/wda/keys` 这类按平台区分的输入原语，那些只出现在驱动适配器里、服务于 AI 步对活动元素的输入。
- 设备网页上的输入在 `withWebContext` 内对定位到的元素操作；对「活动元素」输入的路线在 Android Chrome 上不可靠，handler 不依赖活动元素。
- 首推的定位依据是无障碍标识（iOS 的 `name` / `label`、Android 的 content-desc）与 resource-id；WebdriverIO 的 `$()` 在页面有多个同名元素时报错，选择器要足够窄或改用 `$$()`。
- 原生应用里的 WebView 正文与没有测试标识的 Compose 界面拿不到可用的控件信息，这类界面上的核对交给 AI 断言。

### 3. 测试分层

| 层 | 测什么 | 怎么执行 | 需要真机 |
|---|---|---|---|
| 判定逻辑单测 | 从读到的值得出结论的纯逻辑（文本比较、数值换算、列表核对） | 普通单元测试，不构造 driver | 否 |
| 设备网页句柄离线执行 | 设备网页的 `webdriver` 句柄对材料页面的定位与判定 | 本机 WebdriverIO 加 Chrome for Testing 打开同一份材料页面；与桌面句柄共用一张选择器表 | 否 |
| 真机验收 | 定位在真实应用与真实系统上是否成立、行为是否符合需求 | `run --scope` 收窄到相关 scenario，在 Device Farm 上执行 | 是 |
| 原生 driver 层离线（可选） | 想离线核对原生选择器与命令序列的作者 | Appium 官方 fake driver 配真实 WebdriverIO 客户端 | 否 |

- **handler 保持薄**：读值与操作留在 handler，判定抽成纯函数，第一层就能覆盖大部分逻辑。
- **离线执行要固定缓存目录**：WebdriverIO 在未配 Selenium 服务时自行下载 Chrome for Testing 与驱动，缓存缺省位于系统临时目录、系统重启后丢失；脚手架与文档要求显式指定缓存目录（`cacheDir` 或 `WEBDRIVER_CACHE_DIR`）。
- **真机验收是验收，不是单元测试**：缺省由人或 CI 触发；agent 能否自行开设备会话由项目约定决定（见决策 4）。
- **已接受代价与重议条件**：真机验收这一层每次都要经过取设备的等待（约 1 到 2.5 分钟）并按设备分钟计费，1.5 不为它提供加速路径，靠前两层离线测试把大部分迭代挡在真机之外。出现以下任一信号时重新讨论内循环加速：使用方反馈真机验收占了设备 step 写作耗时的主要部分；离线层覆盖不了的原生应用 step 成为设备 step 的多数。候选方案须守 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 1 的会话归属单一与收尾责任单一（不跨 scope 或跨 job 复用会话），例如本机模拟器层，或由作者在 gherkai 之外自行持有的调试会话。
- 本 ADR 的分层只针对使用方写的确定性 step；worker 自身的驱动适配器与设备模块的护栏归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)。

### 4. 写作方法（进 user guide 与 agent skill）

两种 step 作者（人与 agent）走同一条路；以下规则写进 `writing-deterministic-steps.md` 与 skill 的确定性 step 参考，gherkai 不为写作期另造工具。

- **期望只来自需求**：step 断言什么由需求文档、验收标准、用例本身决定。
- **材料只定位置，不定期望**：页面源、控件树、截图、已有运行的 evidence 用来找到元素在哪、叫什么，不用来决定「应该显示什么」。
- **动态材料的来源平铺列出、不排先后**：应用仓库的源码与测试标识；桌面上的开发者工具或 Playwright；Appium Inspector 或 WebDriver 客户端连上一个 Device Farm 远程访问会话；已有运行留下的 evidence（设备目标上判为 failed 或 error 的 step 含控件摘要与原始控件树，字段归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 8）。
- **agent 自行开设备会话须项目约定放行**，且无论成败都必须收尾（停止会话），因为设备会话按分钟计费、有并发上限。
- **原生应用上先看控件有没有稳定标识**，再决定写不写确定性 step；没有标识就写 AI 步，不用坐标或层级位置拼凑定位。
- **一条动作步只表达一屏之内的意图**：跨多屏的长流程拆成多步。这条同时约束 AI 步——实测中跨五页引导或十页分页的单条动作步需要 5 到 12 轮规划，token 与失败面都随之放大。

### 5. 延后：确定性 step SDK

为设备 step 提供常用定位与等待的辅助函数（如按无障碍标识或 resource-id 查找、等待可见）暂不提供：待使用方的设备 step 积累出重复写法后再定接口；在此之前文档给示例代码，不发布 API 面，避免过早固化一套以后要兼容的接口。

## 实测依据

据 Device Farm 上 Android（Redmi Note 13 / Android 15，Chrome 与维基百科客户端）与 iOS（iOS 15.8 与 iOS 26.3 两台 iPhone，Safari 与 AWS 示例应用）的逐条路线实测；只列与 step 作者相关的判据。

**输入路线**：

| 路线 | Android 网页 | iOS 15.8 网页 | iOS 26.3 网页 | Android 原生应用 | iOS 原生应用（两个版本） |
|---|---|---|---|---|---|
| 对已定位元素 W3C sendKeys | 未单独测 | — | — | 读回一致，0.3 秒 | 读回一致，0.8 到 0.9 秒 |
| 网页上下文活动元素 sendKeys | 11 秒，读回为空 | 读回一致，1.3 秒 | 网页上下文不可用 | — | — |
| 原生上下文活动元素 sendKeys | 报 invalid element state（活动元素是 WebView 容器） | 报无此元素 | 读回一致，1.4 秒 | 读回一致，0.6 秒 | 读回一致，1.1 到 1.2 秒 |
| W3C 键盘动作 | — | 不报错、读回为空，50 到 53 秒 | 未测 | — | — |
| UiAutomator2 `mobile: type` | 1.6 秒，AI 步全部通过 | — | — | 读回一致，1.6 秒 | — |

表中「—」表示该处未测或不适用。两个判据：失败的路线有的不抛错、只耗 50 秒左右，所以选路线必须在会话开头确定、不能在运行期试错回落（归驱动适配器）；原生应用上对已定位元素输入在 Android 与两个 iOS 版本上都可靠，这是确定性 step 应走的路线。

**可定位性**：

| 界面 | 控件信息 | 结论 |
|---|---|---|
| Android 经典 View（维基百科词条页） | page source 11 KB，21 个 resource-id 与工具栏文本 | 可按 id 或文本定位 |
| Android Compose（维基百科引导页） | 6 KB，只有 2 个容器 id，其余节点无文本、无 id | 不可定位 |
| Android 应用内 WebView 正文 | 上下文只有 `NATIVE_APP` 与应用自身不可调试的 `WEBVIEW_chrome` | 正文拿不到 DOM |
| iOS 原生（示例应用） | `XCUIElementType*` 带 `name` / `label`，标签、按钮、弹窗都有名字 | 可按无障碍标识定位 |
| iOS 26.3 Safari | 网页上下文的标题、地址、元素查找都返回检查器错误 | DOM 类 step 不可用 |

**离线执行**：Chrome for Testing 首次建会话含下载约 18 秒（浏览器约 400 MB），机器已装 Chrome 时约 6 秒；缓存缺省在系统临时目录。

**作者实际用到的 WebdriverIO 面**：确定性 step 在应用上只用到元素组（查找、读文本与属性、点击、输入、可见性等待）、上下文组与 `getPageSource`；手势类 `mobile:` 命令全部是 AI 步的事。这是拒绝自带假 driver 的依据之一：需要模拟的面虽小，但选择器解析与等待语义要与真实 Appium 一致才有意义。

## 被拒方案（护栏）

- **gherkai 自带静态假 driver**（声明式元素树、选择器解析子集、把树渲染成 page source）——它是对 Appium 选择器与等待语义的第二份模拟，Appium 或驱动升级时会静默漂移，作者在假 driver 上通过、真机上失败；要维护的面还会随作者用到的 API 增长。Appium 官方 fake driver 由上游维护、配真实客户端，已能满足离线核对的需求。
- **界面快照抓取功能**（gherkai 提供命令抓取设备界面或控件树供写作参考）——现成工具（Appium Inspector、开发者工具、已有运行的 evidence）已覆盖；自造抓取工具要承担会话开销与凭证处理，还会把作者引向「照着当前界面写期望」。
- **任何「先 AI 后硬化」类流程暗示**（先用 AI 步执行一遍，再把 AI 观察到的结果固化为确定性 step）——会把被测应用当前的行为当成期望，缺陷随之被固化为通过条件；与「期望只来自需求」直接冲突。文档与 skill 里不出现这类建议。
- **在一个 handler 里按设备或版本分支**——见决策 1：适用范围对注册表不可见，plan 与能力自述无从标注；系统版本号也会散进使用方代码。
- **step 作者在 handler 里自选输入原语**（`mobile: type`、`/wda/keys`）——平台差异会漏进使用方代码；对已定位元素的 W3C 输入已够用。
- **录制回放**——录下的是坐标与时序，对机型、系统版本、界面改版都脆弱，与确定性 step「按稳定标识定位」的立足点相反。

## 边界与互链

- **目标模型、`@device` 与 `@app` tag、plan 标注规则、网页上下文不可用时记 error**：[0048](./0048-test-targets-device-and-ui-kind.md)。
- **能力自述的 `targets` 键、step 级 `targets` 的交集规则与 `list-deterministic` / doctor 呈现**：[0049](./0049-worker-capabilities-targets-keys.md)。本 ADR 只规定 step 的目标如何从句柄推出。
- **设备会话的创建与收尾、事件契约、evidence 的设备字段、应用分发**：[0051](./0051-device-session-lifecycle-and-app-distribution.md)。
- **驱动适配器、能力探测（含输入路线选择）、网页上下文的重新定位、命令守卫与结果未知的处置、适配器侧护栏**：[0052](./0052-appium-interface-adapter-and-platform-differences.md)。
- **项目配置文件里的设备与应用别名**：[0053](./0053-project-config-file.md)。
- 匹配语义（worker 侧、core 对 step 语义无知）、元数据必填、使用方 `steps/` 目录的加载与失败处理不变：[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)、[0036](./0036-deterministic-capability-discovery.md)、[0037](./0037-distribution-and-packaging.md)。确定性 step 与 AI 断言的分工不变：[0014](./0014-ai-first-assertions.md)、[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)。
