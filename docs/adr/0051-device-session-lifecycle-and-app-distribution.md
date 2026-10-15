# 0051. 设备会话生命周期与应用分发

> **Status:** Accepted（2026-10-15）——定 Device Farm 远程访问会话从获取到收尾的全过程、三个新错误归因类别及 `scope_started` 之前失败的传递、设备目标的 evidence 字段、应用分发通路、隧道鉴权、费用、权限与安全；部分取代 [0035](./0035-local-app-testing-via-tunnel.md) 决策 4（隧道鉴权由地址内嵌凭据改为令牌换 cookie）。测试目标模型、能力自述、驱动适配器分别见 [0048](./0048-test-targets-device-and-ui-kind.md)、[0049](./0049-worker-capabilities-targets-keys.md)、[0052](./0052-appium-interface-adapter-and-platform-differences.md)。

## 背景与问题

设备目标（[0048](./0048-test-targets-device-and-ui-kind.md)）由 AWS Device Farm 的远程访问会话承载：worker 创建会话、拿到托管的 Appium 端点（WebDriver over HTTPS），再由 Midscene 经驱动适配器驾驭真机。这种会话与桌面的 AgentCore 浏览器会话在五处不同，现有规则（[0024](./0024-worker-core-protocol.md)、[0034](./0034-detached-batch-reconciler.md)、[0035](./0035-local-app-testing-via-tunnel.md)）不能原样套用：

- **获取有排队与固定开销**：创建到 Appium 可用要一到两分半钟，超过账号并发上限时会话排队而不是报错；停止后会话还要经过 STOPPING 才到 COMPLETED。
- **硬上限且从创建起算**：单个会话最多 150 分钟、不可调，计费也从创建时刻算。
- **失败形态多出三类**：设备、被测应用或 worker 自检在执行前就判定不可用；获取设备超过预算；会话在执行中途被外部停止或到期。现有错误归因类别集（[0024](./0024-worker-core-protocol.md)）没有对应项，且这些失败大多发生在 `scope_started` 之前，现有协议没有承载它们的位置。
- **端点地址本身是凭证**：Appium 端点与预签名地址把签名放在查询串里，现有脱敏规则（[0035](./0035-local-app-testing-via-tunnel.md) 决策 5）只剥 userinfo。
- **隧道鉴权在 iOS 上不成立**：[0035](./0035-local-app-testing-via-tunnel.md) 决策 4 把凭据内嵌进隧道地址，iOS Safari 不采用这种凭据、改弹系统级鉴权表单。

此外，原生应用要先装到设备上，需要一条应用分发通路；设备分钟是新的计费轴，要进成本可观测性；Device Farm 只在 us-west-2，权限与数据驻留要写明。

## 决策

### 1. 一个 scope 一个远程访问会话

- **做什么**：worker 为每个 scope 创建一个 Device Farm 远程访问会话，会话名带 run_id；拿到会话 ARN 即发 `scope_started`。scenario 之间网页目标重新导航，应用目标先 terminate 再 activate；scope 内状态共享沿用桌面的同一契约（每 scope 一个 worker 进程）。
- **为什么**：每个会话有两段固定开销，都计入设备分钟：取设备开销（创建到 Appium 可用，约 1 到 2.5 分钟，另占墙钟）与停止到 COMPLETED（Android 60 到 85 秒、iOS 超过 2 分钟、最长约 150 秒，不占墙钟）。按 scope 复用才能把它们摊到多条 scenario 上。
- **不做**：不按 scenario 开会话；不跨 scope 或跨 job 复用会话（会话归属与收尾责任必须单一）。

### 2. 时间预算：会话预算从创建起算，job 墙钟预算沿用 0034

- **会话预算**：会话的 150 分钟上限与计费都从 `CreateRemoteAccessSession` 那一刻算，排队中的会话不计费。worker 的会话预算因此从创建起算，并为创建留出余量。
- **`max_session_s`**：worker 在能力自述里声明设备目标的单会话可用时长，由 worker 用 150 分钟减去收尾余量从内部常量算出；桌面条目不带此键，缺键表示不施加会话级上限（键的形态与交集规则归 [0049](./0049-worker-capabilities-targets-keys.md) 决策 4）。scope 的 `@timeout` 缺省以它为上限；job 墙钟预算超过它时，本机后端由执行前预检拒绝（[0048](./0048-test-targets-device-and-ui-kind.md)），云端后端由 worker 自检记 `precheck_failed`（决策 4）。
- **获取预算**：从发起创建到 Appium 会话建好的等待上限，覆盖建会话与排队，只在 worker 内部执行。内建默认值 600 秒，项目配置可覆盖（[0053](./0053-project-config-file.md) 的 `[devices]`）。依据：创建到 RUNNING 实测 Android 51 到 72 秒、iOS 61 到 72 秒，Appium 建连 Android 13 到 26 秒、新 iPhone 17 秒、老 iPhone 65 秒，并发排队实测最长约 6 分钟；三项相加约 8.5 分钟，600 秒给最坏情形留出余量又不至于让排队无限等待。超时归因 `acquire_timeout`（决策 4），不进 [0028](./0028-transient-network-ssl-resilience.md) 的网络重试：排队与机型繁忙不是瞬时网络故障，重试只会延长等待。
- **job 墙钟预算不另立起算点**：沿用 [0034](./0034-detached-batch-reconciler.md)，自推进器启动这个 job 起算；取设备开销（创建、排队、Appium 建连）含在其中，停止到 COMPLETED 只计设备分钟、不占墙钟。用户文档写明每个设备 scope 含约 1 到 2.5 分钟取设备开销。
- **被测站点加载慢由使用方调大 `@timeout`**，工具不自动放宽预算；Appium 命令超时须覆盖慢加载这条归 [0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6。
- **不做**：不改协议为设备另立起算点；不让获取预算与 job 墙钟预算合并成一个值（前者防排队无限等待，后者是用户预算）。

### 3. 排队与创建失败

- 超过账号并发上限时，会话停在 `PENDING_CONCURRENCY` 排队，前面的会话到 COMPLETED 后自动转入准备；STOPPING 中的会话仍占着槽位。worker 把排队当正常等待，计入获取预算。
- 创建请求被拒（限流、机型繁忙）在获取预算内退避重试；只重试 Appium 的 newSession 时不重建远程访问会话（见决策 5）。
- 并发上限以账号实际值为准，不在代码里写死。

### 4. 三个新错误归因类别与 `scope_started` 之前失败的传递

[0024](./0024-worker-core-protocol.md) 的类别集按「随真实失败样本扩充」的规则加三项，[机读输出契约](../internals/cli-json-contract.md)同步加法扩展。

| 形态 | 判据 | 归因 | 处置 |
|---|---|---|---|
| worker 自检不通过 | 目标不受支持，或 job 墙钟预算超过 `max_session_s` | `precheck_failed` | 不建会话，零会话费用退出 |
| 机型不支持远程访问 | 创建时同步抛 ArgumentException | `precheck_failed` | 不产生设备分钟 |
| 应用启动即自退 | 启动后采样应用状态，轨迹回到「未运行」 | `precheck_failed` | 收尾会话 |
| 获取预算耗尽 | 决策 2 | `acquire_timeout` | 撤回会话（Stop） |
| 会话丢失（被外部停止） | `GetRemoteAccessSession` 状态不是 RUNNING | `session_lost` | 当前 step 记 error、余下 step 记 skipped；不再发 Stop；worker 非零退出 |
| 会话到期 | 会话年龄（从创建起算）达到上限 | `session_lost` | 同上 |
| 模型 4xx | Bedrock 返回 4xx | `engine_error` | 沿用现有归因 |
| 应用中途被杀 | 模型从截图判出回到桌面 | 由该 step 的判定给出 | 不另设类别 |

- **三类的处置语义**：`precheck_failed` 表示「没开始测、重试也不会变」，处置是改用例或换测试包；`acquire_timeout` 表示「设备一时拿不到」，处置是稍后重试或提高获取预算；`session_lost` 表示「测到一半设备没了」，判定不完整，job 级不重试、不再发 Stop。三者都不归入 `engine_error` 或 `network_error`，以免误导重试与排障。
- **`scope_started` 之前失败的传递**（`precheck_failed`、`acquire_timeout`）：不新增协议事件。worker 先发 `scope_started`，其 session 字段为 null；再把第一条 scenario 的第一个 step 记为 error 并带该类别，余下 step 记 skipped；然后发 `scope_done`。机读输出契约里这类 scope 的形态因此与普通失败 scope 相同：job 判 error，错误类别挂在第一个 step 上，session 字段为 null 表示从未分到设备。[0049](./0049-worker-capabilities-targets-keys.md) 决策 7 的 worker 自检沿用这条规则。
- **判定靠查状态，不匹配错误文本**：命令失败时 worker 查一次 `GetRemoteAccessSession`。唯一的补充是到期：150 分钟上限到点前后端点已拒绝命令而 API 还要再报约一分钟 RUNNING，所以到期按会话年龄（从创建起算）判定，不等状态翻转。
- **用户可见消息**只说发生了什么、为什么、怎么办，例如「这台设备不支持远程会话，换一台型号后重试」「应用启动后立即自行退出，通常是应用带有运行环境检测；请提供关闭检测的测试包」「在等待时间内没有拿到可用设备，请稍后重试或调大获取设备的等待时间」「设备会话在执行中途结束，本 scope 余下的 step 未执行；可缩短 scope 或检查是否有人手动停止了会话」。

### 5. 取消与收尾的状态表

| 时刻 | 收到取消或出错 | worker 动作 |
|---|---|---|
| 创建请求在途 | 是 | 等 ARN 返回即发 Stop |
| 排队或准备中 | 是 | 发 Stop（排队的会话可直接撤回） |
| Appium 建连失败 | 可重试 | 只重试 newSession，不重建远程访问会话；例外：设备侧拒绝安装驱动辅助包（如厂商 ROM 的 `INSTALL_FAILED_USER_RESTRICTED`）属于这台设备单元的状态，重试同一台无用，改为重建会话换一台，至多一次 |
| 执行中 | SIGTERM | 在安全点结束当前 step，按正常收尾顺序退出 |
| 会话已丢失 | — | 不发 Stop、不调 deleteSession，报错即退出 |
| 正常结束 | — | 先发 `scope_done`，再 deleteSession，再 Stop；不等 COMPLETED |

- **`scope_done` 先于收尾**：判定在 `scope_done` 时已全部产出，收尾的延迟或失败不得影响判定，也不得把一个已完成的 scope 拖成超时。
- **不等 COMPLETED**：Stop 调用即时返回，iOS 会话在 STOPPING 停留超过 2 分钟；计费照算到 COMPLETED，等待只增加墙钟、不省钱。
- **重复 Stop 的报错予以忽略**（会话已停时 Stop 报参数无效）。设备侧收尾只比桌面多 deleteSession 与 Stop 两条即时调用，`min_grace_s` 保持单值（[0049](./0049-worker-capabilities-targets-keys.md)）。

### 6. 泄漏护栏

- worker 退出路径上，凡没发过 `scope_done` 的会话按 ARN 补发一次幂等 Stop。
- `doctor` 列出 Device Farm 项目里所有未到 COMPLETED 的会话（含排队中），供人发现残留。
- **不做回收器**：SIGKILL 等补发不到 Stop 的情况，由 Device Farm 的 150 分钟上限封顶，单个泄漏会话的最坏费用约 25.5 美元（按量单价）；与 [0024](./0024-worker-core-protocol.md) 对 AgentCore 会话「服务端 TTL 封顶、不引入 core 回收组件」同一权衡。

### 7. 设备目标的 evidence 字段

- 复用 [0042](./0042-step-evidence-and-explain.md) 的抽取、schema 与上传器（[0029](./0029-engine-artifacts-to-s3.md)），换成 Appium 界面后 Midscene 的 dump 形态不变。
- **控件摘要表**：设备目标每步由驱动适配器抽取控件摘要表（控件类型、id、文本、无障碍标识）作为 evidence 字段；`explain` 只渲染，不解析控件树。
- **原始控件树**只在 failed / error 步留存，并设大小上限（page source 在应用上可达 MB 级）。
- 应用目标的 `url` 为 null。
- **scope 表头**记实际分到的机型、系统版本、应用版本与会话 ARN。
- **Device Farm 的录像与日志只记会话 ARN**，`explain` 给出控制台链接，不下载进产物。理由三条：下载要在 `scope_done` 后再等到会话 COMPLETED（iOS 最长约 150 秒）之后，收尾易被误判超时；Appium 服务器日志带端点凭证；录像由 Device Farm 自己保留，不必在使用方桶里再留一份。

### 8. 应用分发：S3 单一通路

- **做什么**：CLI 把 `[apps]` 里的本地文件按内容哈希放进应用前缀（云端后端放现有产物桶，本机后端放配置的应用桶，[0053](./0053-project-config-file.md)），Job 只带 S3 键与包名或 bundle id；worker 在 newSession 前对该键预签名（短有效期），交给 `appium:app`，配 `appium:autoLaunch: false`，建好后显式 `activateApp`，并采样应用状态（决策 4 的自退判据）。包名或 bundle id 必须显式给出，不让 Appium 猜启动活动。
- **签名**：iOS 签名由 Device Farm 在这条安装路径上重做；未签名、ad-hoc 签名、profile 已过期的 IPA 都能装并启动到前台。iOS 应用须是使用方自带的开发版 IPA（App Store 不提供文件），怎么签都可用。
- **约束**：单条 Appium 命令 4 分钟上限，S3 到 Appium 主机约 6 MB 每秒，单个安装包的实际上限约 1.4 GB；预签名有效期须覆盖建会话时的下载。
- **生命周期**：应用对象放在独立前缀下，由桶的生命周期规则过期；内容哈希作键使同一安装包不重复上传。
- **不做**：不引入 Device Farm 上传 API（见被拒方案）；不从公网地址安装（源站对 Appium 主机的表现不可控）。

### 9. 费用

- **设备分钟作为原生量进成本信封**（[0024](./0024-worker-core-protocol.md)）：worker 报从创建到发出 Stop 的分钟数；账单另含停止到 COMPLETED 的那段，以账单为准，用户文档写明。core 只合计，不折算货币。
- **计费方式可配**（配置键 `billing-method`，取值 METERED / UNMETERED，对应 Device Farm API 的 `billingMethod`，取值来源归 [0053](./0053-project-config-file.md)）：按量 0.17 美元每设备分钟，不计量槽位 250 美元每月；每平台每月超过约 1470 设备分钟时不计量槽位更便宜。
- 每会话的两段固定开销见决策 1。

### 10. 区域、项目与权限

- Device Farm 只在 us-west-2。云端后端的 Device Farm 项目由 `deploy` 用 SDK 创建、ARN 写进 SSM（与 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 的 SSM 约定一致）；本机后端的项目 ARN 走配置（[0053](./0053-project-config-file.md)）。

| 主体 | 需要的权限 |
|---|---|
| CLI（提交者机器） | 产物桶或应用桶的应用前缀写入；`doctor` 列会话需要项目的会话列举 |
| worker（task role 或本机执行者） | 远程访问会话的创建、查询、停止；设备列举与查询（解析 `[devices]` 的筛选条件）；产物桶或应用桶的应用前缀读取（预签名由它签发） |
| deploy（部署方） | 创建 Device Farm 项目、写 SSM、给 task role 授上述 worker 权限（含设备列举与查询） |

- 本机后端驱动真机时 worker 在 QA 机器上执行，QA 机器须具备 worker 一行的全部权限；用户文档按执行后端分别写明。

### 11. 安全：端点脱敏与数据保留

- **端点是凭证**：Appium 端点与预签名地址的签名在查询串里。[0035](./0035-local-app-testing-via-tunnel.md) 决策 5 的三份脱敏实现加一条规则：签名类查询参数与隧道令牌查询参数（决策 13）的值替换成 `***`；三份共用同一组用例。会话被外部停止时，WebdriverIO 在传输层失败把整条带签名的端点地址拼进错误文本，这条规则必须覆盖这种形态。
- **端点不进任何事件**，也不进 evidence、scope 诊断与日志；WebdriverIO 日志级别固定为 error。验收要求：用一次故意建连失败的真机执行，核对报错文本里的签名已被盖住。
- **不取** Device Farm 的 Appium 服务器日志与 TCP dump（前者带端点凭证，后者含被测应用流量）。
- **数据保留**：公共设备会话结束后 Device Farm 清除应用与数据；录像与日志由 Device Farm 保留 400 天、驻留 us-west-2。写进 user guide 的限制段。

### 12. 命令可能挂住而非报错

iOS 会话没有网页上下文时调 `url` 不报错而是挂住（请求超时后反复重试）。会话侧的要求：WebDriver 客户端的请求超时与重试次数有界且小于 step 预算，挂住的命令以 step error 结束，不得耗尽会话预算；导航以「网页上下文可用」为前提这条规则归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)。

### 13. 隧道鉴权：令牌换 cookie，桌面、Android、iOS 一条路

- **做什么**：CLI 替换进 step 文本的隧道地址改为「原地址附本 run 的访问令牌查询参数」，不再内嵌 userinfo。隧道边缘策略对持有效令牌的请求下发会话 cookie（Secure、HttpOnly、SameSite=None），并 302 到去掉令牌的同一地址；之后边缘只认 cookie，令牌与 cookie 都没有或令牌无效时返回 401，请求到不了本机。令牌按 run 一换、run 内每次显式导航都可重复使用、随隧道关闭失效；cookie 只发隧道域。SameSite 取 None 而不是 Lax：这枚 cookie 只守隧道可达性、不承载被测应用的会话语义，测试浏览器一次性且只访问被测应用及其跳转目标，跨站请求带上它的风险面可接受，换来第三方登录的跨站 POST 回跳零配置可用。
- **为什么统一**：iOS Safari 不采用地址内嵌凭据（被拒方案），iOS 必须换方案；同一方案在桌面与 Android 上同样成立，统一后只有一套鉴权、一套脱敏与一组用例。附带收益：跳转后文档地址不再带 userinfo，[0035](./0035-local-app-testing-via-tunnel.md) 决策 4 记录的「被测应用用绝对地址调 `history.pushState` 时抛 SecurityError」这类隧道模式特有的假失败随之消失，`page.url()` 与失败消息里也不再出现凭据。
- **对隧道服务商的要求**：边缘能按条件（查询参数、cookie）分支，并返回带插值头的自定义响应（`Set-Cookie` 与 `Location` 的值取自请求）。现行服务商 ngrok 的流量策略（CEL 条件表达式加 custom-response 动作）在本项目所用的免费层账号上实测具备这两项；basic-auth 本来也是经同一套策略实现，依赖的类别不变。这是 [0035](./0035-local-app-testing-via-tunnel.md) 决策 1 的隧道服务商接口上新增的能力要求；不具备该能力的服务商不能作为隧道实现，启动隧道时 fail-loud。
- **已知边界**：被测应用清空全部 cookie 后下一次请求得到 401，由下一次带令牌的显式导航恢复；step 代码绕开浏览器直接向隧道域发请求时须自带令牌或 cookie（与凭据内嵌方案下相同）。
- **会话侧**：驱动适配器不感知令牌与 cookie，导航原语只打开 step 文本里的地址（[0052](./0052-appium-interface-adapter-and-platform-differences.md)）；带令牌的地址经决策 11 的出口脱敏，不进事件明文。
- **不变**：[0035](./0035-local-app-testing-via-tunnel.md) 的 URL 映射、隧道生命周期与 `ngrok-skip-browser-warning` 额外请求头照旧；只取代其决策 4 的鉴权方式。

### 14. 前提：国内消费级应用的线上包会自行退出

带第三方环境检测（反调试、自动化检测）的国内消费级应用，其线上包在公共真机上启动即自行退出（进程正常退出、无异常栈）。这是被测应用的限制，不是 Device Farm 的安装或启动问题：gherkai 把它报成 `precheck_failed`，用户文档写明须提供关闭检测的测试包。**不做任何规避。**

## 实测依据

据 Android（Redmi Note 13 / Android 15）与多代 iPhone（iOS 15.8、iOS 18.6、iOS 26.3）上的会话生命周期、故障演练、应用安装与隧道鉴权实测；真机均为从美国出网的公共真机：

| 项 | 数据 | 支撑的决策 |
|---|---|---|
| 创建到 RUNNING | Android 51 到 72 秒；iOS 61 到 72 秒 | 1、2 |
| Appium 建连 | Android 13 到 26 秒；新 iPhone 17 秒，老 iPhone 65 秒 | 1、2 |
| 停止到 COMPLETED | Android 60 到 85 秒；iOS 超过 2 分钟、最长约 150 秒；主动停止时计费算到 COMPLETED | 1、5、9 |
| 上限 | 创建后约 150.4 分钟端点开始拒绝命令、此时 API 仍报 RUNNING，约一分钟后端点报预签名地址失效，再约一分钟到 COMPLETED；计费 150.29 分钟，从创建算、到期强制停止时截在上限处而不算到 COMPLETED | 2、4 |
| 并发 | 同机型连发 6 个请求，前 5 个到 RUNNING，第 6 个进 `PENDING_CONCURRENCY` 排队、Stop 可撤回；一次排队约 6 分钟，STOPPING 中的会话占着槽位；历次实测中未遇到机型被占满（BUSY） | 2、3、5 |
| 机型不支持远程访问 | 创建时同步抛错，零设备分钟 | 4 |
| 外部停止 | 进行中的 AI 步 8 秒内失败；之后每条命令同样报错；deleteSession 报连接已关；再调 Stop 报参数无效；deleteSession 的报错原样带出整条带签名的端点地址 | 4、5、11 |
| 建连时设备拒绝安装驱动辅助包 | 同一机型的某一台设备单元在 newSession 时报 `INSTALL_FAILED_USER_RESTRICTED`（厂商 ROM 的安装限制），换一台单元即正常 | 5 |
| 应用中途被杀 | 模型从截图判出回到桌面，后续断言照常判否，evidence 完整 | 4、7 |
| 国内应用 | 两款国内消费级应用在同一台公共真机上启动即自退，两款海外应用正常 | 4、14 |
| S3 安装 | 88 MB APK 经预签名地址在建会话时装上；未签名与 ad-hoc 签名 IPA 都装上并到前台 | 8 |
| 安装吞吐 | S3 到 Appium 主机约 6 MB 每秒；单条命令上限 4 分钟 | 8 |
| evidence | 换成 Appium 界面后抽取不改即可用，`explain` 两种输出形态都能渲染设备产物 | 7 |
| 无网页上下文时调 `url` | iOS 上挂住、反复重试而不报错 | 12 |
| 地址内嵌凭据 | Android Chrome 约 4 秒加载出本机应用；iOS Safari（15.8 与 18.6）带与不带凭据都停在原页，弹系统级「Sign in」表单，网页上下文看不到；表单可由 XCUITest 填写提交，但鉴权是否成功未证实 | 13 |
| 令牌换 cookie | 桌面 Chromium（Playwright）、Android Chrome 与 iPhone 16 / iOS 18.6 Safari 均通过：带令牌首次导航落在干净地址并加载出本机应用，随后不带令牌的同域导航经 cookie 通过，桌面上跳转后 `history.pushState` 正常；边缘侧四种情形（持有效令牌 302 加 Set-Cookie、只持 cookie 200、两者皆无 401、令牌无效 401）符合预期 | 13 |
| 单价 | 按量 0.17 美元每设备分钟，不计量槽位 250 美元每月，盈亏点约 1470 分钟每平台每月 | 9 |

## 被拒方案（护栏）

- **按 scenario 开会话**：每条 scenario 都付两段固定开销且计费，设备费用成倍上升。
- **Device Farm 上传 API 作为第二条分发通路**：S3 通路已覆盖两个平台与全部签名形态；上传 API 要多一组权限、一份 30 天保留期的副本和第二套状态管理，换不来能力。
- **Device Farm 自动化测试模式**：由 Device Farm 主机执行上传的测试包，与外部 worker 加事件流的形态不同构。
- **默认下载录像与 Appium 日志进产物**：收尾要等到 COMPLETED、日志带端点凭证、多一份数据保留面（决策 7）。
- **收尾等到 COMPLETED**：只增加墙钟、不改计费（决策 5）。
- **建连重试时重建远程访问会话**：每次重建再付固定开销、可能分到另一台设备，scope 内状态也随之丢失。
- **按错误文本分类会话失败**：文本随 SDK 与服务版本漂移；状态查询是真值，到期例外按会话年龄判定（决策 4）。
- **获取超时并入 `precheck_failed`**：两者处置相反，前者稍后重试可能成功，后者重试不会变；合并会误导使用方。
- **为 `scope_started` 之前的失败新增协议事件**：现有事件已能表达（session 字段为 null 加首步 error），新增事件要改 core 与机读输出契约两侧（决策 4）。
- **回收器**：150 分钟原生上限已封顶泄漏费用，回收器要让 core 或组合根新增一个碰 Device Farm 的组件（决策 6）。
- **获取超时进网络重试、或为设备另立墙钟起算点**：见决策 2。
- **隧道凭据内嵌地址（沿用 [0035](./0035-local-app-testing-via-tunnel.md) 决策 4）**：iOS Safari 不采用地址内嵌凭据、改弹原生鉴权表单，网页上下文看不到它；桌面上还会让绝对地址的 `history.pushState` 抛 SecurityError。
- **驱动适配器用 XCUITest 填写 iOS 系统鉴权表单**：鉴权是否成功未证实，把隧道鉴权耦合进 iOS 驱动、每个新会话都要重做（[0052](./0052-appium-interface-adapter-and-platform-differences.md)）。
- **隧道按 Device Farm 公布的设备地址段放行**：取决于服务商套餐，且同一地址段内的其他公共设备使用者同样可达，鉴权强度低于每 run 一换的令牌。
- **对设备目标关闭隧道鉴权**：等于把使用方本机应用在 run 期间向公网开放（[0048](./0048-test-targets-device-and-ui-kind.md)）。
- **额外请求头注入 `Authorization`**：全域广播给页面加载的所有第三方域，泄露面大于 cookie（[0035](./0035-local-app-testing-via-tunnel.md) 已拒）。
- **规避被测应用的环境检测**：超出工具职责，且结果不可信（决策 14）。

## 边界与互链

- 本 ADR 不管目标如何声明、本机后端执行前预检对不受支持目标的拒绝、被测环境可达性结论：归 [0048](./0048-test-targets-device-and-ui-kind.md)；隧道鉴权方案由本 ADR 决策 13 承接。
- `targets` 与 `max_session_s` 的键形态、缺键语义、`min_grace_s`、worker 自检：归 [0049](./0049-worker-capabilities-targets-keys.md)。
- handler 上下文与确定性 step 的测试分层：归 [0050](./0050-deterministic-step-handles-and-testing.md)。
- 驱动适配器、能力探测、导航前提、控件摘要表的抽取方式、Appium 命令超时：归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)。
- `[devices]`（设备选择、`billing-method`、获取预算的覆盖、本机后端的项目 ARN 与应用桶）与 `[apps]`：归 [0053](./0053-project-config-file.md)。
- 沿用并扩展：错误归因类别集与成本信封 [0024](./0024-worker-core-protocol.md)；网络重试 [0028](./0028-transient-network-ssl-resilience.md)；上传器 [0029](./0029-engine-artifacts-to-s3.md)；job 墙钟预算 [0034](./0034-detached-batch-reconciler.md)；URL 映射、隧道生命周期与脱敏规则 [0035](./0035-local-app-testing-via-tunnel.md)；用户可见消息 [0039](./0039-user-facing-surfaces-no-internal-references.md)；evidence [0042](./0042-step-evidence-and-explain.md)。
