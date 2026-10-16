# 0051. 设备会话生命周期与应用分发

> **Status:** Accepted（2026-10-15）——定 Device Farm 远程访问会话从设备解析、获取、执行就绪到终结释放的全过程与事件契约（`session_opened` / `session_closed`、`scope_done` 的 scope 级判定）、新增错误类别、终结四阶段与命令结果未知的处置、设备计量、evidence 字段、应用分发、隧道鉴权（令牌换 cookie 加 worker 预热）、区域与权限、脱敏与数据保留。部分取代 [0035](./0035-local-app-testing-via-tunnel.md) 决策 4（隧道鉴权由地址内嵌凭据改为令牌换 cookie）；对 [0024](./0024-worker-core-protocol.md)（事件集、配对规则、成本信封、`sessionId` 语义、Job 输入形状、错误类别集）、[0028](./0028-transient-network-ssl-resilience.md)（core 层重试门槛、幂等依据、只读重试例外、预热失败的传递）、[0034](./0034-detached-batch-reconciler.md)（机制二 `exit==0` 一行、job timeout 节、停止后有界读事件）、[0031](./0031-job-lifecycle-states-and-severity.md)（scenario 级合成 SKIPPED、在途明细规则）、[0049](./0049-worker-capabilities-targets-keys.md)（决策 4、5、7）、[0037](./0037-distribution-and-packaging.md)（决策 6 的 context 闭集、决策 7 的缺戳例外与 definition 格式版本）的点名改写，反向链各落在它们的 Status 头或对应条文。测试目标模型、能力自述、驱动适配器、项目配置分别见 [0048](./0048-test-targets-device-and-ui-kind.md)、[0049](./0049-worker-capabilities-targets-keys.md)、[0052](./0052-appium-interface-adapter-and-platform-differences.md)、[0053](./0053-project-config-file.md)。

## 背景与问题

设备目标（[0048](./0048-test-targets-device-and-ui-kind.md)）由 AWS Device Farm 的远程访问会话承载：worker 创建会话、拿到托管的 Appium 端点（WebDriver over HTTPS），再由 Midscene 经驱动适配器驾驭真机。这种会话与桌面的 AgentCore 浏览器会话在六处不同，现有规则（[0024](./0024-worker-core-protocol.md)、[0028](./0028-transient-network-ssl-resilience.md)、[0034](./0034-detached-batch-reconciler.md)、[0035](./0035-local-app-testing-via-tunnel.md)）不能原样套用：

- **获取有排队、换台与固定开销**：创建到 Appium 可用要一到两分半钟，超过账号并发上限时会话排队而不是报错；某台设备单元可能拒装驱动辅助包而要换一台重建；停止后会话还要经过 STOPPING 才到 COMPLETED。「会话已起」与「被测对象已就绪」之间隔着排队、建连、能力探测、应用启动与隧道预热，`scope_started` 发在哪一点决定了 [0028](./0028-transient-network-ssl-resilience.md) 的重试边界是否成立。
- **硬上限且从创建起算**：单个会话最多 150 分钟、不可调。
- **失败形态多出几类且发生在 `scope_started` 之前**：设备、被测应用或 worker 自检在执行前判定不可用；获取设备超过预算；隧道预热被拒；会话在执行中途被外部停止或到期。现有错误归因类别集（[0024](./0024-worker-core-protocol.md)）没有对应项，现有协议也没有 scope 级失败的载体。
- **释放失败与终止判定耦合**：Stop 失败即会话继续计费到上限；[0034](./0034-detached-batch-reconciler.md) 规定发完 `scope_done` 又非零退出一律 error，现有 Midscene worker 也是先清理再发 `scope_done`，设备会话的收尾顺序必须与两者一致。
- **端点地址本身是凭证**：Appium 端点与预签名地址把签名放在查询串里，现有脱敏规则（[0035](./0035-local-app-testing-via-tunnel.md) 决策 5）只剥 userinfo。
- **隧道鉴权在 iOS 上不成立，且设备浏览器没有注入请求头的通道**：[0035](./0035-local-app-testing-via-tunnel.md) 决策 4 把凭据内嵌进隧道地址，iOS Safari 不采用这种凭据、改弹系统级鉴权表单；决策 4 用请求头绕过隧道服务商警告页的做法在设备浏览器上没有对等物。

此外，原生应用要先装到设备上，需要一条应用分发通路；设备分钟是新的计费轴，要进成本可观测性；Device Farm 只在 us-west-2，权限与数据驻留要写明。

## 决策

### 1. 一个 scope 一个远程访问会话，scenario 之间不复位

- **做什么**：worker 为每个 scope 创建一个 Device Farm 远程访问会话，会话名按决策 3 的规则生成。应用目标在会话建好后安装并启动一次；scenario 之间不重新导航、不重启应用，scope 内状态共享沿用 [0019](./0019-feature-tags-scope-and-engine.md) 的契约（同 scope 的 scenario 串行、共享被测对象的会话与操作状态、允许操作依赖），全部测试目标适用。需要干净起点的用例在 Background 里显式写内建确定性 step「重新启动应用」（只对应用目标注册，实现归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)）；agent skill 的写作规则缺省为多 scenario 的应用 feature 放这一步。
- **为什么**：每个会话有两段固定开销，实测都计入服务商回报的设备分钟：取设备开销（创建到 Appium 可用，约 1 到 2.5 分钟，另占墙钟）与停止到 COMPLETED（Android 约 1 分钟、iOS 最长约 2.5 分钟，不占墙钟）。按 scope 复用才能把它们摊到多条 scenario 上。隐式复位会让同一份 feature 加上 `@device` 后语义静默改变，terminate 加 activate 又不清持久数据、只是半隔离；准备动作失败时也没有 step 可挂。显式 Background step 的失败就是本 scenario 内一个普通 step 的 error，短路只作用于本 scenario。
- **不做**：不按 scenario 开会话；不跨 scope 或跨 job 复用会话（会话归属与收尾责任必须单一）；不在 scenario 之间做任何自动复位。

### 2. 时间预算：会话预算从创建起算，获取预算从进入设备解析起算，job 墙钟沿用 0034

- **会话预算**：会话的 150 分钟上限从 `CreateRemoteAccessSession` 那一刻算。worker 的会话预算因此从创建起算，并为创建留出余量。`max_session_s` 由 worker 从 150 分钟减去收尾余量算出并写进能力自述（[0049](./0049-worker-capabilities-targets-keys.md) 决策 4）。worker 另按会话年龄做后备：年龄达到 `max_session_s` 时当前 step 记 error、余下 step 记 skipped、发 Stop、归因 `session_lost`。
- **获取预算**：从进入设备解析起算（按筛选条件时是首次设备列举，直接给 ARN 时是首次创建请求），止于被测对象就绪（决策 4 的 `scope_started` 时刻）；覆盖筛选与繁忙等待、创建与限流退避、排队、准备、newSession 含应用安装、至多一次换台重建、`activateApp` 与自退采样、能力探测、隧道预热。内建默认 600 秒，项目配置可覆盖（[0053](./0053-project-config-file.md) 的 `[devices]`），上界 3600 秒；跨换台重建不重置，剩余不足 150 秒不再换台。到期归因 `acquire_timeout`，判据型失败归 `precheck_failed`。获取期的瞬时错误在预算内由 worker 手写退避，不进 [0028](./0028-transient-network-ssl-resilience.md) 的网络重试，也不触发 core 的 job 级重试（[0028](./0028-transient-network-ssl-resilience.md) core 层重试门槛加「job 目标不是设备」）：排队与机型繁忙不是瞬时网络故障，core 重拉 worker 会重付取设备开销。默认值依据：创建到 RUNNING 约 1 分钟、Appium 建连 13 到 65 秒、并发排队实测最长约 6 分钟，三项相加约 8.5 分钟，600 秒留出余量又不让排队无限等待；换台重建与繁忙等待下是否够用在实施期校准。
- **job 墙钟预算不另立起算点**：沿用 [0034](./0034-detached-batch-reconciler.md)，自推进器 claim 这个 job 起算；取设备开销含在其中，停止到 COMPLETED 只计设备分钟、不占墙钟。设备 scope 的缺省墙钟由 core 的 plan 层按目标给出（缺省为获取预算加 900 秒，下限为获取预算加 180 秒，设备 scope 不存在「不超时」；覆盖顺序与校验顺序归 [0034](./0034-detached-batch-reconciler.md)「job timeout」节与 [0019](./0019-feature-tags-scope-and-engine.md)），worker 只在建会话前读 Job 携带的墙钟预算与 `max_session_s` 比较作自检（[0049](./0049-worker-capabilities-targets-keys.md) 决策 7），不计时、不自停。
- **单条命令与页面加载的上界归 [0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6 的分层表**：客户端请求超时是单条命令的真实上界，`pageLoad` 只是尽力而为，`newCommandTimeout` 只计命令之间的空闲。被测站点单次加载超过页面加载上限的在 1.5 不受支持，调大 `@timeout` 只解决多次加载累积的墙钟不足。
- **不做**：不改协议为设备另立起算点；不让获取预算与 job 墙钟预算合并成一个值（前者防排队无限等待，后者是用户预算）；不由 worker 维护 job 截止线（worker 不知道 claim 时刻与拉镜像耗时，且会出现两个超时执行面）。

### 3. 设备解析、创建与孤儿防护

- **设备解析**（输入是 [0053](./0053-project-config-file.md) `[devices]` 的 `arn` 或 `os-version`）：完整分页列举公共设备；静态过滤平台、点分段版本族（配置值按点切段，设备版本的前几段完全相等即命中：`18` 命中 `18.x.y`，`18.1` 不命中 `18.10`，写全段即精确匹配）、手机形态（固定，不开放配置）、支持远程访问。首轮零候选再列举一次，仍为零即 `precheck_failed`，消息给出条件与最接近的可用版本；等待期间候选变空不改判。选择规则：在全部匹配候选中先排除 BUSY 与 TEMPORARY_NOT_AVAILABLE，再按版本号高、HIGHLY_AVAILABLE 优于 AVAILABLE、ARN 字典序取第一台；全部繁忙才在获取预算内等待。只写版本前缀时 plan 提示「设备池新增版本时实际分到的版本可能改变，写全版本号可以固定」。直接给 ARN 时不做静态过滤，被同步拒绝（不存在、已下架、不支持远程访问）记 `precheck_failed`。
- **创建与重试**：Device Farm 客户端 `maxAttempts = 1`、每次调用显式请求超时（Create、Get、List 10 秒，Stop 3 秒，终结期 Get 5 秒），重试一律由 worker 在获取预算内手写退避，停止信号可穿透。创建被拒（限流、机型繁忙）在预算内重试；Appium newSession 的瞬时失败只重试 newSession、不重建会话；设备单元拒装驱动辅助包（如厂商 ROM 的 `INSTALL_FAILED_USER_RESTRICTED`）是这台单元的状态，改为重建会话换一台，至多一次，被替换的会话先 Stop。并发上限以账号实际值为准，不在代码里写死；超过上限时会话停在 `PENDING_CONCURRENCY`，worker 把排队当正常等待计入获取预算；STOPPING 中的会话仍占着槽位。
- **会话名**：固定前缀、run_id、scope_id 的安全编码与尝试序号组成，长度封顶 256 字符（实测 256 接受、257 拒绝），编码规则：`gherkai:<run_id>:<scope 哈希>:<尝试序号>:<scope_id 编码>`，scope 哈希为完整 scope_id 的 SHA-256 前 16 位十六进制，scope_id 编码段里 `A-Z a-z 0-9 . _ -` 之外的字符按 UTF-8 字节百分号编码；总长超过 256 时只截 scope_id 编码段（它只供人在控制台辨认），其余四段永不截断。按名列举时 worker 用同一规则重算自己的名字、按整名相等匹配，不按前缀或哈希段匹配；同一 run 内不同 scope 要互认须 64 位哈希与截断后的编码段同时相同。规则在 worker 的设备模块单点实现，worker 列举时按同一规则重算名字。同名会话可以并行创建、名字没有唯一性，所以尝试序号是名字的一部分，按名列举后再按序号对应。
- **结果未知的创建尝试**：Create 请求超时或连接中断时该尝试记为「待核」。待核只能由正面证据消除——按名列举命中，登记进待清理集并发 `session_opened(origin: discovered)`，随后与其他会话一样释放并确认。列举为空不构成排除证据（实测只证明成功返回的 Create 在 1 秒内按名可见，没有证明结果未知的请求在服务端如何处理，也不能排除它在列举之后才出现），所以不设「等多久为空就算没建」的窗口。每次重试前与每条终结路径（正常收尾、SIGTERM、异常退出）都核对一次，核对须在预算内处理分页（`ListRemoteAccessSessions` 带 `nextToken`、无服务端按名过滤），未扫完即视为未核对。终结时仍待核的尝试按决策 5 发 `attempted` 的成对事件并以退出码 1 结束。Create 没有幂等令牌，按名查询是补救不是幂等保证。这是有意的保守：代价是罕见的误报「请核对控制台」，换来不漏报一个可能计费到上限的会话。

### 4. 事件契约：`scope_started` 是执行就绪，会话血缘与计量走 `session_opened` / `session_closed`，执行前失败走 `scope_done` 的 scope 级判定

- **`scope_started` 的含义是「被测对象已就绪，下一事件就是第一个 `scenario_started`」**，每 scope 至多一次。设备目标上须满足：远程访问会话 RUNNING、Appium 会话建好（含至多一次换台重建）、能力探测完成（[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 5）、应用目标已 `activateApp` 且启动采样未回到「未运行」、网页目标的隧道预热已确认（决策 13）。此后不再重建会话、不再重试 newSession。[0028](./0028-transient-network-ssl-resilience.md)「越过 `scope_started` 不再重试建连」原文保留，并在设备上成立。`scope_started.sessionId` 填执行所用的会话 ARN；[0024](./0024-worker-core-protocol.md) 的 `sessionId` 定义放宽为「会话血缘：AgentCore 会话 id 或 Device Farm 远程访问会话 ARN」。
- **成对事件承载会话血缘**（[0024](./0024-worker-core-protocol.md) 事件集的加法扩展）：
  - `session_opened{scopeId, sessionId?, name, origin: created | discovered | attempted, device?{platform, model, osVersion, unit}}`：Create 返回 ARN 后、一切长耗时动作之前发出（`created`）；按名找回的孤儿会话也发（`discovered`，device 可缺）；结果未知且终结时仍未排除的创建尝试也发一条（`attempted`，`sessionId` 为 null、只带会话名），使 worker 知道的待核事实有协议载体。
  - `session_closed{scopeId, sessionId?, name, release: confirmed | unconfirmed, observedS?, providerMinutes?}`：该会话的处置最终结束时发出，每个会话恰一条，不先发 unconfirmed 再补 confirmed。不带「为何停止」的枚举，原因进 worker 日志与 message。
  - 配对键是 `sessionId`，没有时用 `name`。sessionId、name 与 device 对 core 不透明，端点地址不进任何字段。[0024](./0024-worker-core-protocol.md) 的配对规则改为「`scope_started` 是首条执行事件；其前只允许 `session_opened` 与 `session_closed`」。桌面 worker 不发这两种事件，桌面路径零变化。同步路径的 `persist.on_event` 收到 `session_opened` 即把 job 刷成 RUNNING 并带 session_id，收到 `scope_started` 时改写为执行会话的 id；`JobState.session_id` 优先取 `scope_started` 的值，没有时退回最近一条非 `attempted` 的 `session_opened`。`origin: attempted` 的 `session_opened` 不改写 job 已记的 session_id：已有值保留，没有则保持 null，它只作为 `sessions[]` 里 `session_id` 为 null 的一项进入摘要与未确认集；推进器投影（[0034](./0034-detached-batch-reconciler.md) 机制二、三）用同一规则，任何路径都不用 null 覆盖已有的 session_id（DDB 逐属性写入显式 null 同样会擦掉已有值，「未提及属性保留」防不住）。
- **确认停止只认状态**：`GetRemoteAccessSession` 读到 STOPPING 或 COMPLETED，或 Stop 返回体中的状态为两者之一（实测 Stop 约 0.2 秒返回、返回体带 `status: STOPPING`，可直接作确认；对已停会话重复 Stop 报 ArgumentException「Invalid parameter RemoteAccessSession」）。Stop 报任何错误都补查一次状态，不按错误类别推断。
- **执行前失败走 `scope_done{status: error, errorType, message}`**，不发 `scope_started`，不发任何 scenario 或 step 事件。`ScopeDone` 加三个可选字段（同进同出，`status` 只允许 `error`）；判定由 `status` 承载，`errorType` 只回答原因，[0024](./0024-worker-core-protocol.md)「错误归因不是第二根判定轴」原则不变。core 收到 `scope_done.status = error` 后对 definition 中无事件的 scenario 合成 scenario 级 SKIPPED，并对其全部 step 合成 `SKIPPED(shortcircuited=False)`；在途 scenario（有 `scenario_started` 无 `scenario_done`）整条不合成，其未开始的 step 也不合成（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一、三、六的加法）；终结判定的真值表归 [0034](./0034-detached-batch-reconciler.md) 机制二。桌面 worker 在隧道预热失败时也走这条路（决策 13），所以新字段出现在「1.5 CLI 发起、带设备目标或预热地址」的 run 中。
- **错误归因类别**（[0024](./0024-worker-core-protocol.md) 类别集按「随真实失败样本扩充」的规则加项，[机读输出契约](../internals/cli-json-contract.md)同步加法扩展）：

| 形态 | 判据 | 归因 | 处置 |
|---|---|---|---|
| worker 自检不通过 | 目标不受支持，或 job 墙钟预算超过 `max_session_s` | `precheck_failed` | 不建会话，零会话费用退出 |
| 设备解析零候选；指定 ARN 被同步拒绝 | 决策 3 | `precheck_failed` | 不产生设备分钟 |
| 应用对象缺失或不可读 | worker 建会话前的存在性检查 404 / 403（决策 9） | `precheck_failed` | 404 提示重新提交，403 说明是权限问题 |
| 应用启动即自退；换台一次后仍拒装驱动辅助包；newSession 非瞬时失败；安装超过 Appium 单条命令 4 分钟上限 | 启动后采样应用状态回到「未运行」；决策 3 | `precheck_failed` | 收尾会话；message 区分形态 |
| 隧道预热被确定性拒绝 | 预热页面标记 DENIED 或 AUTH REQUIRED（决策 13） | `precheck_failed` | 换设备或浏览器、检查隧道 |
| 隧道预热无法确认 | 预热页面标记 ERROR 或预算内无任何标记，重试耗尽 | `engine_error` | 稍后重试 |
| 获取预算耗尽 | 决策 2 | `acquire_timeout` | 收尾会话 |
| 会话丢失（被外部停止） | `GetRemoteAccessSession` 状态不是 RUNNING | `session_lost` | 当前 step 记 error、本 scenario 余下 step 记 skipped、后续 scenario 由 core 合成 skipped；状态仍 RUNNING 才发 Stop |
| 会话到期 | 会话年龄（从创建起算）达到 `max_session_s`，或端点拒绝命令而 API 仍报 RUNNING | `session_lost` | 同上，发一次幂等 Stop |
| 命令结果未知 | 客户端请求超时或连接中断，且会话仍 RUNNING | `engine_error`，消息写明「可能已执行也可能未执行」 | 本 scenario 短路；下一 scenario 前只读存活探测，失败即 scope 级 error（[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 2 的 scenario 前核对、决策 6） |
| 需要网页上下文的确定性 step 落在不提供它的设备上 | 探测确认不提供 | `capability_unavailable`（step 级，[0052](./0052-appium-interface-adapter-and-platform-differences.md)） | 改写为 AI 断言或换设备 |
| 释放未确认 | 终结时存在 `release: unconfirmed` 的会话或 `attempted` 的尝试 | `release_failed`（core 由配对推出） | 到控制台按会话名核对并手动停止 |
| 模型 4xx | Bedrock 返回 4xx | `engine_error` | 沿用现有归因 |
| 应用中途被杀 | 模型从截图判出回到桌面 | 由该 step 的判定给出 | 不另设类别 |

- **类别的处置语义**：`precheck_failed` 表示「没开始测、重试也不会变」，处置是改用例、换测试包或换设备；`acquire_timeout` 表示「设备一时拿不到」，处置是稍后重试或提高获取预算；`session_lost` 表示「测到一半设备没了」，判定不完整，job 级不重试；`release_failed` 表示「判定可能完整但会话可能仍在计费」，无论最终归因为何 message 都追加提示并列出会话名。不新增 `device_setup_failed` 与 `device_unresponsive`，等真实样本（[0024](./0024-worker-core-protocol.md) 的扩充规则）。
- **判定靠查状态，不匹配错误文本**：命令失败时 worker 查一次 `GetRemoteAccessSession`。到期按会话年龄判定，不等状态翻转：150 分钟上限到点前后端点已拒绝命令而 API 还要再报约一分钟 RUNNING。
- **用户可见消息**只说发生了什么、为什么、怎么办，例如「这台设备不支持远程会话，换一台型号后重试」「应用启动后立即自行退出，通常是应用带有运行环境检测；请提供关闭检测的测试包」「在等待时间内没有拿到可用设备，请稍后重试或调大获取设备的等待时间」「设备会话在执行中途结束，本 scope 余下的 step 未执行；可缩短 scope 或检查是否有人手动停止了会话」「设备会话未能确认停止，可能仍在计费，请在设备控制台核对并手动停止」。

### 5. 收尾顺序、终结四阶段与退出码

- **正常收尾**（与桌面 Midscene worker 现有顺序一致：先释放会话再发 `scope_done`；设备 worker 另把释放结果写进判定，桌面只靠退出码 1 让释放失败可观测）：最后一个 `scenario_done` → `agent.destroy` 与 scope 级报告 → 有界上传 → `deleteSession`（5 秒，不重试，不阻塞 Stop）→ 终结核对（下文阶段 2，正常路径同样执行）→ 释放阶段 → 每会话 `session_closed` → `scope_done` → 排空上传队列 → 退出。判定在 `scope_done` 时产出，但 `scope_done` 排在释放之后：Stop 未确认即 job ERROR、类别 `release_failed`、worker 以 1 退出，与 [0034](./0034-detached-batch-reconciler.md)「发完 `scope_done` 又非零退出一律 error」及 [0024](./0024-worker-core-protocol.md)「释放优先、失败可观测」一致。
- **SIGTERM 与一切异常终结路径按四个阶段执行，各有绝对截止线**（相对进入终结的时刻 t）：
  1. **等在途 Create**（t 到 t + 10 秒）：在途的 Create 返回即登记 ARN；超时则该请求标为「结果未知」。进入本阶段时同时置当前 act 的 `abortSignal`、撤销执行令牌（[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6），正在执行的 step 不发 `step_done`，不发 `scope_done`。
  2. **终结核对**（至多 5 秒，`ListRemoteAccessSessions` 按名列举、含分页）：对全部待核尝试按决策 3 的规则处理；阶段结束仍待核的尝试，各发 `session_opened(origin: attempted, name)` 与 `session_closed(release: unconfirmed, name)`。
  3. **释放阶段**（25 秒，全部待清理会话并行、共享截止线）：每个会话 Stop（3 秒）→ 失败则 Get 补查（5 秒）→ 退避 → 再 Stop 一次 → 再补查；到线即记 `release: unconfirmed`。SIGTERM 路径不调 `deleteSession`（Stop 决定计费，deleteSession 只是 Appium 侧的收尾）。
  4. **事件与产物**：每会话 `session_closed`、中断兜底上传（10 秒）、截图队列排空（6 秒）。
  终结只执行一次：信号重复、超时与信号同时到达这类交叠或重入不重新进入四阶段；真实会话按 ARN 去重、每会话恰一条 `session_closed`，待核尝试按名只发一对 `attempted` 事件。
  `min_grace_s` 由四段推导：10 + 5 + 25 + 10 + 6 加事件写出与余量约 7.5，约 64 秒，低于 Fargate `stopTimeout` 的 120 秒；各段上限以网络退化实测校准后定数（[0049](./0049-worker-capabilities-targets-keys.md) 决策 5）。
- **Stop 规则只有一条**：会话状态仍为 RUNNING 就发一次幂等 Stop（覆盖按年龄到期而 API 仍报 RUNNING 的情形）；已是 STOPPING 或 COMPLETED 则不发 Stop、不调 `deleteSession`。
- **会话丢失序列**：当前 step `step_done{error, session_lost}` → 本 scenario 余下 step `step_skipped`（`shortcircuited=True`）→ `scenario_done{error}` → 后续 scenario 不发事件 → 收尾 → `session_closed` → `scope_done{status: error, errorType: session_lost}`；后续 scenario 由 core 合成 SKIPPED。
- **退出码**：0 表示内容完整且全部会话已确认停止（含执行前失败与 `session_lost`）；1 表示存在未确认停止的会话（含 `attempted` 的尝试）或 worker 自身异常；设备 worker 不使用 80。SIGTERM 收尾成功但没有 `scope_done` 时退出码按上式，判定由推进器的停止原因给出（[0034](./0034-detached-batch-reconciler.md) 机制二）。
- **进程级兜底**：worker 注册 `unhandledRejection` 与 `uncaughtException` 处理器，记录后进入终结四阶段而不是任由进程退出（实测 webdriver 10.0.2 的 newSession 在客户端超时后出现过一次进程直接退出、`finally` 未执行、会话泄漏）。

### 6. 泄漏护栏

- worker 退出路径上，凡没确认释放的会话都经终结四阶段处理；`doctor` 列出 Device Farm 项目里所有未到 COMPLETED 的会话（含排队中），并给出控制台链接与手动停止的命令。
- **不做回收器**：会话生命周期由 worker 独自持有，第二个持有者会与收尾竞争、且单凭列举结果判断不了会话是否仍在使用；SIGKILL 等补发不到 Stop 的情况由 Device Farm 的 150 分钟上限封顶，单个泄漏会话的最坏费用约 25.5 美元（按量单价），还会占住账号的一个并发槽位至多 150 分钟，使后续 run 排队、被连锁报成 `acquire_timeout`。CLI 不增加 Stop 权限。

### 7. 设备计量：只报原生量

- `session_closed.observedS` 是 worker 观察到该会话的时长：起点为 Create 返回时刻（孤儿为列举发现时刻），止点为发出 Stop 或确认其已停止的时刻；缺失记 null，null 不等于 0。`providerMinutes` 保留 AWS 原形 `{total, metered, unmetered}` 快照，可缺。core 把 `observedS` 合计成 job 与 run 级「设备占用时长」（机读键 `device_observed_s`），`observedS` 为 null 的会话不计入合计、另以 `device_observed_missing` 计数，两键同层成对、只在含设备目标时出现；`device_observed_missing` 只计 `origin` 为 `created` 或 `discovered` 的会话，`attempted` 的尝试既不计入合计也不计入该计数、只在 `sessions[]` 里以 `origin` 区分——尝试连会话是否存在都没有证实，与「会话存在但缺计量」是两种事实，混进同一个计数会误导使用方；人读展示把它们标为「结果未知的创建尝试」、不当作缺计量的会话；不折算货币、不估计计费量、不写任何依赖计费起点的断言，用户文档只说明口径不同、以账单为准。[0024](./0024-worker-core-protocol.md)「cost 只挂 `step_done`」改为「`step_done` 与 `session_closed` 各挂各的原生量，每个字段只在一层出现，core 逐字段跨层合计」。
- **计费方式可配**（配置键 `billing-method`，取值 METERED / UNMETERED，对应 Device Farm API 的 `billingMethod`，允许按平台覆盖，取值来源归 [0053](./0053-project-config-file.md)）：按量 0.17 美元每设备分钟，不计量槽位 250 美元每月；每平台每月超过约 1470 设备分钟时不计量槽位更便宜。它是每次创建请求的参数，随 Job 走。

### 8. 设备目标的 evidence 字段

- 复用 [0042](./0042-step-evidence-and-explain.md) 的抽取、schema 与上传器（[0029](./0029-engine-artifacts-to-s3.md)）。只限设备目标的例外：AI step 各状态都产 evidence 并加设备字段；确定性与导航 step 只在 failed / error 时产（`acts: []`）；桌面不变。
- **字段**（schema 1 上加键）：`step_kind`；顶层 `url` 与 `url_missing`（`no_web_context` / `not_applicable` / `timeout` / `error`）；`controls{items[{type, id, text, a11y_id}], total, truncated}` 与 `controls_missing`；`page_source`（独立文件的 URI，走截图的后台上传队列）与 `page_source_truncated`。控件摘要与原始树都只在 failed / error step 上采集，采集有独立短预算、按步累加计入 job 墙钟，失败置空并标原因，不改判定。`explain` 只渲染，不解析控件树。`controls`、`page_source`、`url` 写盘前都经决策 11 的脱敏出口，规则同时覆盖 XML 实体转义形态。
- **scope 表头**由 `session_opened.device` 与 `scope_started.sessionId` 派生，不另立事实源。能力探测结论写入 best-effort 的 `device-session.json`，以 `kind: "device_session"` 作为普通产物链接只挂在 `scope_done` 上，`explain` 只渲染链接、不解析其内容；探测结论同时写进 worker 日志。
- 应用目标的 `url` 为 null。**Device Farm 的录像与日志只记会话 ARN**，`explain` 给出控制台链接，不下载进产物：下载要等到会话 COMPLETED 之后，Appium 服务器日志带端点凭证，录像由 Device Farm 自己保留。

### 9. 应用分发：S3 单一通路

- **做什么**：CLI 把 `[apps]` 里的本地文件按内容哈希放进应用前缀 `apps/<sha256>/<原文件名>`（云端后端放现有产物桶，本机后端放配置的应用桶，[0053](./0053-project-config-file.md)）；Job 的应用条目带完整 S3 位置（桶、键、内容哈希）与包名或 bundle id（[0048](./0048-test-targets-device-and-ui-kind.md)）。worker 在建会话前做存在性检查（task role 对应用前缀有限定 `s3:prefix` 的 `s3:ListBucket`，使缺失返回 404）：404 记 `precheck_failed`「安装包已不在存储桶里，请重新提交」，403 记 `precheck_failed` 并说明是权限问题；再在 newSession 前对该键预签名（短有效期，只需覆盖下载），交给 `appium:app`，配 `appium:autoLaunch: false`，建好后显式 `activateApp` 并采样应用状态。包名或 bundle id 必须显式给出，不让 Appium 猜启动活动。
- **签名**：iOS 签名由 Device Farm 在这条安装路径上重做；未签名、ad-hoc 签名、profile 已过期的 IPA 都能装并启动到前台。iOS 应用须是使用方自带的开发版 IPA。
- **保留承诺（云端后端）**：对象带标签 `gherkai=app`，产物桶按该标签过期 E = 14 天；已提交 run 引用的对象自提交起至少保留 R = 7 天。CLI 复用时按内容哈希 HeadObject：不存在就上传（大包分段上传、带标签）；存在且年龄不超过 E − R 直接复用；超过就同键 CopyObject 刷新（`MetadataDirective=REPLACE` 回写元数据、`TaggingDirective=REPLACE` 回写标签），刷新失败重传，再失败提交失败、不复用快过期的对象。生命周期是否按新创建时间重新计时在实施期核对。本机后端的应用桶归使用方所有，gherkai 不打标签、不刷新、不承诺；SSE-KMS 桶需对应 KMS 权限，写进支持边界。
- **约束**：单条 Appium 命令 4 分钟上限，S3 到 Appium 主机一次实测约 6 MB 每秒，由此推出的下载理论上界约 1.4 GB 只是有前提的估算（安装、iOS 重签与建连可能共用同一条命令的时限，跨区域吞吐未测，实测过的最大包 88 MB）；CLI 对超过 500 MB 的包警告不拦截。
- **不做**：不引入 Device Farm 上传 API（见被拒方案）；不从公网地址安装（源站对 Appium 主机的表现不可控）。

### 10. 区域、项目与权限

- Device Farm 只在 us-west-2，worker 与 Python 侧的 Device Farm 客户端固定该区域（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「region 全可配」的唯一例外）；S3 与 SSM 客户端仍用后端所在区域。
- **调用归属**：worker 的设备模块是执行期唯一调用 Device Farm SDK 的地方（设备列举与查询、会话创建、查询、停止、按名列举）；Python 侧的部署与诊断模块（`gherkai-runtime[aws]`，延迟导入）承担 `deploy` 找回或建立项目、`doctor` 列举会话，不创建、不停止会话；推进器不调 Device Farm。护栏测试：客户端只在这两个模块构造，core 零引用。
- **项目**：只有 `deploy` 子命令在 cdk 之前用 SDK 找回或建立项目 `{prefix}devices`（先读 SSM 参数、再按名称列举；命中多个以退出码 2 结束），ARN 作为命令自派生的 context 交给 stack（[0037](./0037-distribution-and-packaging.md) 决策 6 的闭集加 `device_farm_project`），stack 写 SSM 参数并按权限表给 task role 授权；SSM 已有 ARN 时先调 GetProject 核对：成功即沿用；NotFound（项目被手动删除，拆除手册允许这样做）警告一句后转入按名称列举，命中一个用它、命中多个以退出码 2 结束、没有就建立，新 ARN 经 stack 覆盖 SSM 与授权，旧项目的会话记录与录像已随删除消失，`explain` 指向旧会话的控制台链接随之失效；AccessDenied 走下面的无权限降级；限流、网络等其他错误以退出码 1 结束，不猜测。`diff` 不建立项目，按同一规则只读核对：SSM 有值且 GetProject 成功时沿用，参数不存在、stack 不存在或 NotFound 时以「待建立」占位；`diff`、`--synth-only` 与 `destroy` 读 SSM 遇到其他失败（无凭证、AccessDenied、网络、限流）一律以退出码 2 结束，消息写明读的是哪个 SSM 路径、需要哪些权限——读不到就回落占位，会让 `diff` 把已部署的设备授权显示成删除，误导依据它核对变更的人。唯一例外是 `--synth-only` 在完全没有凭证时回落占位，并在 stderr 警告导出的模板不含设备会话授权、与已部署的 stack 不一致，因为无凭证导出是 [0037](./0037-distribution-and-packaging.md) 决策 6 已有的能力；`destroy` 保留项目（含会话记录与录像，与 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 对承载数据的资源 RETAIN 同一取向），拆除手册写明项目须手动删除。部署方无 Device Farm 权限时：SSM 已有 ARN 则沿用并警告；没有则警告并跳过，云端带设备目标的 run 在提交前因缺 ARN 以退出码 2 结束，消息「部署未启用设备支持」。本机后端的项目 ARN 走配置（[0053](./0053-project-config-file.md)）。
- **权限按动作与资源类型逐项登记在 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 的权限表**（据 AWS 服务授权参考：`ListDevices` 不支持资源级限制；`CreateRemoteAccessSession` 同时需要 `project` 与 `device` 两种资源；会话的查询与停止要同时授本项目前缀下的 `session` 资源与本项目的 `project` 资源（真实角色实测：只授其中一种即被拒，拒绝消息点名另一种）；`ListRemoteAccessSessions` 按 `project`），本 ADR 只记主体与动作：worker 需要设备列举与查询、会话创建、查询、停止、按名列举，以及应用前缀的读取与前缀列举；CLI 需要应用前缀的读、写、分段上传中止与打标签（云端），以及 `doctor` 的会话列举；deploy 需要项目的列举、查询与建立。该表已用按表建立的真实角色逐项核过允许与拒绝（见实测依据）；策略模拟器对会话查询与停止给出了假阳性，权限表的变更以真实角色实测为准、不以模拟器为准。
- 本机后端驱动真机时 worker 在 QA 机器上执行，QA 机器须具备 worker 一行的全部权限；用户文档按执行后端分别写明。

### 11. 安全：端点脱敏与数据保留

- **端点是凭证**：Appium 端点的凭据在路径里（`/remote-endpoint/<令牌>`，没有查询参数），会话交互端点与 S3 预签名地址的签名在查询串里（实测）。[0035](./0035-local-app-testing-via-tunnel.md) 决策 5 的三份脱敏实现为此加两条规则：封闭名单里的签名类查询参数与隧道令牌参数（决策 13）的值替换成 `***`，同时覆盖 XML 实体转义形态（查询串里的 `&` 在控件树属性中写成 `&amp;`）；Appium 端点 `/remote-endpoint/` 之后的令牌段替换成 `***`。名单与匹配形态以 0035 决策 5 为准，三份共用同一组用例，用例收一条按实测结构构造的端点地址作边界样本。会话被外部停止后 `deleteSession` 报 UND_ERR_CLOSED，WebdriverIO 把整条带签名的端点地址拼进错误文本，这条规则必须覆盖这种形态（实测）。
- **端点不进任何事件**，也不进 evidence、scope 诊断与日志；WebdriverIO 日志级别固定为 error。验收要求：用一次故意建连失败的真机执行，核对报错文本里的签名已被盖住。
- **不取** Device Farm 的 Appium 服务器日志与 TCP dump（前者带端点凭证，后者含被测应用流量）。
- **数据保留**：公共设备会话结束后 Device Farm 清除应用与数据；录像与日志由 Device Farm 保留 400 天、驻留 us-west-2，worker 与推进器不删除任何会话（删除会让 `explain` 的控制台链接失效）。用户文档写明保留期、驻留地、控制台删除方法与「使用专用测试账号」的建议；按保留天数清扫已完成会话的 CLI 命令列为后续候选。

### 12. 命令的真实上界与结果未知

单条 WebDriver 命令的真实上界是客户端请求超时，执行期关闭传输层自动重试（webdriver 10.0.2 在客户端超时与多数服务端错误上以原请求体重发，点击与输入会被重复执行），只读原语白名单允许有界重试；iOS 上无网页上下文时 `url` 不报错而是挂住、并阻塞同一客户端的后续命令，所以导航以「网页上下文可用」为前提，探测用的只读命令由自带短超时的独立客户端实例发出。结果未知的命令由会话级命令守卫处置：守卫置标志并中止当前 act，worker 查一次会话状态，非 RUNNING 按 `session_lost`，RUNNING 则当前 step 记 error、类别 `engine_error`、消息写明「可能已执行也可能未执行」，本 scenario 短路，下一 scenario 前只读存活探测；任何层都不补发。分层表、白名单与命令守卫的定义归 [0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6。

### 13. 隧道鉴权：令牌换 cookie，worker 预热一次，桌面、Android、iOS 一条路

- **做什么**：组合根生成每 run 一换的访问令牌 T 与会话 cookie 值 C（各至少 128 位随机串，只写进本 run 的流量策略文件，0600），把「会话预热地址」`https://<隧道主机>/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T` 写进 definition 的 RunMeta（无值省键，core 只搬运），引擎适配器经 env `GHERKAI_SESSION_WARMUP_URL` 注入 worker。worker 在被测对象就绪之前、第一个 scenario 之前对网页目标导航预热地址一次，不按 scenario 重做；应用目标不预热。step 文本只做「origin 到干净隧道地址」的映射，不再内嵌 userinfo，也不附令牌。
- **边缘策略**（在 ngrok 免费层实测的两条硬约束之内：每个策略至多 5 条规则，`remove-headers` 为付费功能）定为 4 条：预热路径凭令牌返回 200 页面并下发 cookie；预热路径其余情形 401；校验路径 `/.well-known/gherkai-tunnel-check` 只凭 cookie 放行、返回 200 空体；其余路径 cookie 不等于 C 则 401，命中即原样转发（校验路径的拒绝也落到这条）。cookie 规格 `__Host-gherkai_tunnel=C; Secure; HttpOnly; Path=/; SameSite=None`，无 Domain、无 Max-Age，撤销靠「隧道关闭、策略消失」加精确等值比对；多个同名 cookie 任一命中即放行；同名查询参数在非预热路径上原样转发。预热响应带 `Cache-Control: no-store` 与 `Referrer-Policy: no-referrer`。不剥离转发给上游的隧道 cookie（付费功能），C 会进入被测应用的访问日志，列为已知边界。SameSite 取 None：这枚 cookie 只守隧道可达性、不承载被测应用的会话语义，测试浏览器一次性且只访问被测应用及其跳转目标，换来第三方登录的跨站 POST 回跳零配置可用（桌面 Chromium、Android Chrome、iOS 15.8 与 18.6 Safari 实测成立）。
- **预热页面有三种可见结果，确认判据三端同一条**：预热页面脚本向校验路径发一次请求，成功则把标题与正文标记改为 READY，得到 401 改为 DENIED，请求失败改为 ERROR；令牌错误时预热路径直接返回 401 页，正文标记 AUTH REQUIRED。worker 不依赖网页上下文：桌面读响应状态与标记，设备在原生控件树里查找标记文本（Safari 与 Chrome 把网页正文暴露为可访问性节点）。归因：READY 即就绪；DENIED 或 AUTH REQUIRED 是确定性拒绝，`precheck_failed`；ERROR 或预算内无任何标记，原地重导航有界重试，耗尽后 `engine_error`。两者都不归 `network_error`（[0028](./0028-transient-network-ssl-resilience.md) 的分类红线：鉴权失败与拿不准的失败不得归瞬时网络故障），桌面也不用退出码 80，一律经 `scope_done{status: error, errorType}` 传递（决策 4）。
- **导航路线由能力探测决定，不按系统版本分支**（[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 5）：网页上下文可用（能在短预算内执行一条只读命令）时走 `url`，不可用时走 `mobile: deepLink`。实测给出两条反例支撑这一原则：iOS 15.8 上 `mobile: deepLink` 不受支持，只能走 `url`；iOS 18.6 上先用 deepLink 再切网页上下文，网页命令全部挂住，改走 `url` 则全部通过；iOS 26.3 网页上下文列得出、切得进但命令挂住，只能走 deepLink。
- **definition 完整性不变量**（[0035](./0035-local-app-testing-via-tunnel.md) 的加法）：隧道模式下 definition 必带「额外请求头」与「会话预热地址」两项；worker 收到额外请求头却没有预热地址即 `precheck_failed`「后端未传递会话预热地址，部署版本可能低于命令行工具，请重新部署」。它把两个既有事实绑成一个完整性判据，不按文本猜测，能抓到旧后端丢字段的部署残缺。为什么不能只靠版本闸门与零判定护栏：正式版无戳旧后端已由 [0037](./0037-distribution-and-packaging.md) 决策 7 的缺戳例外拦在提交前；剩下的是开发版本混搭（skew 检查对非纯净版本跳过比较），这时旧开发版 Lambda 读新 definition 会丢掉会话预热地址，新 worker 在没有预热的情况下执行，导航与地址核对可能在 401 页上通过，判定集非空、零判定护栏抓不到，所以只能在 worker 侧拿两个既有事实做完整性判据拦截。
- **能力与拒绝点**：worker 能力自述加一个键声明支持会话预热（[0049](./0049-worker-capabilities-targets-keys.md)，schema 1 加键）；本机后端在执行前预检里核对，`--expose-local` 下遇不声明的 worker 拒绝；云端依靠按版本解析镜像与 [0037](./0037-distribution-and-packaging.md) 决策 7 的缺戳例外；第三方 worker 的表现是导航得到 401 页，页面正文用产品语言说明「此地址需要测试会话」。
- **为什么统一**：iOS Safari 不采用地址内嵌凭据（被拒方案），iOS 必须换方案；同一方案在桌面与 Android 上同样成立，统一后只有一套鉴权、一套脱敏与一组用例。附带收益：跳转后文档地址不再带 userinfo，[0035](./0035-local-app-testing-via-tunnel.md) 决策 4 记录的「被测应用用绝对地址调 `history.pushState` 时抛 SecurityError」这类假失败随之消失，`page.url()` 与失败消息里也不再出现凭据；地址断言与正则参数不再被令牌污染。
- **对隧道服务商的要求**：边缘能按路径、查询参数与 cookie 精确值分支，并返回带固定头的自定义响应；现行服务商 ngrok 的流量策略在本项目所用的免费层账号上实测具备。不具备该能力的服务商不能作为隧道实现，启动隧道时 fail-loud。四台真机实测都没有出现免费层警告页；若服务商改变行为，设备目标在隧道模式下要求付费层。
- **已知边界**：被测应用在 scope 内下发 `Clear-Site-Data: "cookies"` 后，后续请求 401，1.5 记为已知边界（拆成多个 scope 规避）；step 代码直接向隧道域发请求时须经浏览器上下文的请求通道以共享 cookie；隧道 cookie 会到达被测应用。
- **令牌与 cookie 的残留面**：T 落在 `run_meta.json`（0600）、DDB META、S3 参数卸载对象、流量策略文件、本机 worker 进程环境、云端 RunTask 的 `containerOverrides`、设备录像与 Appium 日志里的预热地址、隧道服务商的流量记录；C 落在流量策略文件、浏览器 cookie 库与被测应用的访问日志。两者随隧道关闭失效。令牌不进 step 文本，`jobs/*.json` 不含秘密。
- **不变**：[0035](./0035-local-app-testing-via-tunnel.md) 的 URL 映射（匹配规则按边界精化，归 0035 决策 2）、隧道生命周期与桌面的 `ngrok-skip-browser-warning` 额外请求头照旧；只取代其决策 4 的鉴权方式。

### 14. 前提：国内消费级应用的线上包会自行退出

带第三方环境检测（反调试、自动化检测）的国内消费级应用，其线上包在公共真机上启动即自行退出（进程正常退出、无异常栈）。这是被测应用的限制，不是 Device Farm 的安装或启动问题：gherkai 把它报成 `precheck_failed`，用户文档写明须提供关闭检测的测试包。**不做任何规避。**

## 实测依据

据 Android（Redmi Note 13 / Android 15）与多代 iPhone（iOS 15.8、iOS 18.6、iOS 26.3）上的会话生命周期、故障演练、应用安装、隧道鉴权、超时语义与会话释放实测；真机均为从美国出网的公共真机；边缘契约在 ngrok 免费层账号上用 curl 与桌面 Chromium（Playwright）核过：

| 项 | 数据 | 支撑的决策 |
|---|---|---|
| 创建到 RUNNING | Android 51 到 92 秒；iOS 61 到 82 秒 | 1、2 |
| Appium 建连 | Android 13 到 26 秒；新 iPhone 5 到 17 秒，老 iPhone 65 秒 | 1、2 |
| 停止到 COMPLETED | Android 52 到 85 秒；iOS 超过 2 分钟、最长约 150 秒；主动停止时服务商回报的设备分钟算到 COMPLETED | 1、5、7 |
| 上限 | 创建后约 150.4 分钟端点开始拒绝命令、此时 API 仍报 RUNNING，约一分钟后端点报预签名地址失效，再约一分钟到 COMPLETED；计费 150.29 分钟 | 2、4 |
| 并发 | 同机型连发 6 个请求，前 5 个到 RUNNING，第 6 个进 `PENDING_CONCURRENCY` 排队、Stop 可撤回；一次排队约 6 分钟，STOPPING 中的会话占着槽位 | 2、3、5 |
| 机型不支持远程访问 | 创建时同步抛错，零设备分钟 | 4 |
| 外部停止 | 进行中的 AI 步 8 秒内失败；之后每条命令同样报错；deleteSession 报连接已关；再调 Stop 报参数无效；deleteSession 的报错原样带出整条带签名的端点地址 | 4、5、11 |
| 建连时设备拒绝安装驱动辅助包 | 同一机型的某一台设备单元在 newSession 时报 `INSTALL_FAILED_USER_RESTRICTED`，换一台单元即正常 | 3 |
| 会话名与同名 | 256 字符接受，257 字符 ValidationException；两条同名会话并行创建都成功；成功返回的 Create 在 1 秒内按名列举可见 | 3 |
| 排队中撤回 | Stop 0.6 秒返回 STOPPING，0.8 秒到 COMPLETED，返回体与 Get 都没有 `deviceMinutes` 字段 | 3、7 |
| Stop 与 Get | 并行 Stop 各约 0.2 秒返回、返回体带 `status: STOPPING`；Get 约 0.2 秒；重复 Stop 报 ArgumentException | 4、5 |
| 有无 deleteSession 的收尾 | 先 deleteSession 再 Stop 的会话 52 秒到 COMPLETED、计 2.16 分钟；只 Stop 的会话 73 秒到 COMPLETED、计 2.48 分钟；两者都产出录像、Appium 服务端日志、Logcat 与 TCP dump（Android 两会话） | 5、8 |
| 应用中途被杀 | 模型从截图判出回到桌面，后续断言照常判否，evidence 完整 | 4、8 |
| 国内应用 | 两款国内消费级应用在同一台公共真机上启动即自退，两款海外应用正常 | 4、14 |
| S3 安装 | 88 MB APK 经预签名地址在建会话时装上；未签名与 ad-hoc 签名 IPA 都装上并到前台 | 9 |
| 安装吞吐 | S3 到 Appium 主机约 6 MB 每秒；单条命令上限 4 分钟 | 9 |
| evidence | 换成 Appium 界面后抽取不改即可用，`explain` 两种输出形态都能渲染设备产物 | 8 |
| 无网页上下文时调 `url` | iOS 上挂住、反复重试而不报错；一条挂住的网页命令阻塞同一客户端上的后续命令（「因上一请求过久而超时」） | 12、13 |
| 边缘契约 | 免费层策略第 6 条规则即拒绝启动，`remove-headers` 报付费功能；4 条规则下 curl 16 项全部符合预期：无 cookie 401、预热路径令牌错 401、预热路径 POST 401、正确令牌 200 且带 Set-Cookie 与 no-store、校验路径凭 cookie 200 否则 401、业务路径 cookie 正确 200 值错 401、多值同名 cookie 其一正确 200、有效 cookie 加同名查询参数 200 且原样转发、有效 cookie 加错令牌访问预热路径 401、POST 业务路径凭 cookie 200、浏览器 UA 不带跳过头直接得到上游页面；上游日志不含 `.well-known` 请求 | 13 |
| 桌面 Chromium | 预热 200 且标题 READY；cookie httpOnly、secure、SameSite None、会话 cookie、无 Domain；业务页 200 且 cookie 到达上游；错令牌 401 页、之后业务页仍 200；从第三方站点提交的跨站 POST 到达上游且带 cookie；`history.pushState` 正常 | 13 |
| 四台真机预热 | READY 在原生控件树中 1 到 2 秒内读到（iOS 26 经 deepLink 0.8 秒，Android 经 `url` 约 2 秒）；业务页 INDEX 且 cookie 到达上游；错令牌 AUTH REQUIRED、之后业务页仍放行；四台都没有警告页；跨站 POST 带 cookie 在 Android、iOS 15.8、iOS 18.6 通过（iOS 26 无可用网页上下文未测）；切到桌面再切回后 cookie 保留在 iOS 15.8 与 18.6 通过（Android 两次探针都没读到业务页标记、未判定） | 13 |
| 导航路线 | iOS 15.8 `mobile: deepLink` 报「当前 Xcode SDK 不支持打开地址」，`url` 通过；iOS 18.6 先 deepLink 再用网页上下文则网页命令全部挂到 120 秒并重试三次，改 `url` 全通；iOS 26.3 网页上下文列得出、切得进、命令挂住，deepLink 通过 | 13 |
| 地址内嵌凭据 | Android Chrome 约 4 秒加载出本机应用；iOS Safari（15.8 与 18.6）带与不带凭据都停在原页，弹系统级「Sign in」表单，网页上下文看不到 | 13 |
| 超时语义 | 同一会话两个 webdriver 10.0.2 客户端实例各自的 `connectionRetryTimeout` 各自生效（3 秒实例 3.0 秒超时，缺省实例完成同一慢导航），两平台相同；Android Chrome `pageLoad` 设 3 秒、10 秒慢页 14.6 秒后才报 timeout；iOS Safari 设置不被反映、`url` 在 3.2 秒返回而页面未加载完；`newCommandTimeout` 15 秒下 25 秒长命令在两平台都正常完成、空闲 20 秒后 `invalid session id`，远程访问会话仍 RUNNING，重新 newSession 5.6 到 17 秒成功 | 2、12 |
| newSession 客户端超时 | 2 秒超时后立即与 75 秒后 `GET /sessions` 均为空（两平台；只说明两个时点无残留）；一次运行中进程在该超时后直接退出、复测未复现 | 3、5 |
| Midscene 1.15.1 对中止的行为 | 假界面在首个动作抛「结果未知」并置 `abortSignal` 后，`aiAct` 15 毫秒内拒绝，之后零动作、零截图（两种模式各一次） | 12 |
| IAM 策略模拟器 | `ListDevices` 于 `*` 允许；`GetDevice` 允许；`CreateRemoteAccessSession` 于本项目加 `device:*` 允许、于其他项目隐式拒绝；会话 Get 于本项目前缀允许、于其他项目拒绝；`ListRemoteAccessSessions` 于本项目允许；未授予的 `DeleteRemoteAccessSession` 拒绝。会话 Get 一项是假阳性，见下一行 | 10 |
| 会话端点结构 | 两次真机会话各取一次：`remoteDriverEndpoint` 形如 `https://devicefarm-interactive-global.us-west-2.api.aws/remote-endpoint/<令牌>`，没有查询参数、不以 `/` 结尾，令牌段约 2440 个字符、只含字母与数字；`interactiveEndpoint`（wss）带 SigV4 预签名查询参数 `X-Amz-Date`、`X-Amz-Credential`、`X-Amz-Algorithm`、`arn`、`X-Amz-SignedHeaders`、`X-Amz-Signature`、`X-Amz-Security-Token`；两者都没有 userinfo。只记录结构与参数名，不记录任何值 | 11 |
| IAM 真实角色闭环 | 按 0033 权限表建 worker、CLI、部署方三个角色，assume 后逐动作正反面共 33 项：只授会话前缀时会话 Get 与 Stop 被拒、拒绝消息点名项目 ARN，其余 31 项与权限表一致；同一会话上的对照显示，Get / Stop 只授会话前缀或只授项目 ARN 都被拒、拒绝消息点名未授的那一种，两种同授全部放行。例外是 assume 时会话名只有一个字符，此时授任一种即放行，这是模拟器与早期隔离探针误判的来源；两个字符起（含 32 位十六进制的 task id 形态与 SDK 缺省形态）一律要求两种同授。应用前缀：带前缀条件的 `ListBucket` 下，缺失键的 HeadObject 回 404、GetObject 回 `NoSuchKey`，前缀外的读写与未授的删除被拒；部署方 `CreateProject` 于 `*` 放行、未授的 `DeleteProject` 被拒 | 9、10 |
| 单价 | 按量 0.17 美元每设备分钟，不计量槽位 250 美元每月，盈亏点约 1470 分钟每平台每月 | 7 |

## 被拒方案（护栏）

- **按 scenario 开会话**：每条 scenario 都付两段固定开销且计费，设备费用成倍上升。
- **scenario 之间隐式复位（网页重新导航、应用 terminate 再 activate）**：反转 [0019](./0019-feature-tags-scope-and-engine.md) 的共享状态契约，同一份 feature 加上 `@device` 后语义静默改变；半隔离（不清持久数据）；准备动作失败没有 step 可挂（决策 1）。
- **拿到会话 ARN 即发 `scope_started`**：排队、建连、换台都发生在 ARN 之后，[0028](./0028-transient-network-ssl-resilience.md) 的重试边界失效，执行前失败还要再发一次；血缘由 `session_opened` 承载后不再需要它（决策 4）。
- **把 0028 的重试域拆成「core 以 `scope_started` 为界、worker 以首个 step 为界」两层**：改写红线、引入第二条边界，core 的重试判据悬空。
- **执行前失败发 session 为 null 的 `scope_started` 并把错误挂在首个 step 上**：出错步骤随 scenario 顺序漂移，伪造一次 `scope_started`，job 级事实放到 step 级（决策 4）。
- **`scope_done` 先于收尾、收尾失败不影响判定**：与 [0034](./0034-detached-batch-reconciler.md) 机制二「发完 `scope_done` 又非零退出一律 error」及 [0024](./0024-worker-core-protocol.md)「释放优先」矛盾，会隐藏计费泄漏（决策 5）。
- **SIGTERM 时在安全点结束当前 step**：Midscene 没有单动作返回上界，宽限一到即 SIGKILL，Stop 发不出去（决策 5）。
- **worker 维护 job 截止线作为 0034 的例外**：worker 不知道 claim 时刻与拉镜像耗时，且出现两个超时执行面（决策 2）。
- **设备 scope 沿用桌面的 300 秒缺省墙钟、只在 plan 输出提示**：job 墙钟从 claim 起算，取设备开销算在里面；获取预算内建默认 600 秒已经超过 300 秒，按缺省提交的设备 job 在设备就绪前就会判超时，提示改变不了结果。改为按目标补缺省（获取预算加 900 秒），下限为获取预算加 180 秒，低于下限以退出码 2 拒绝（决策 2）。
- **族内只在最高版本的设备里选（最高版本全忙就等待，不选同族较低版本）**：最高版本的设备全忙时会把获取预算耗在等待上，最终可能记 `acquire_timeout`，而同族较低版本同样满足使用方写的版本前缀；需要固定版本时写全版本号即精确匹配，只写前缀时 plan 会提示实际分到的版本可能变化（决策 3）。
- **保留没有可触发护栏测试的机制层**：终结四阶段、命令守卫、definition 格式版本各对应一个实测或代码核实过的故障（会话泄漏、晚到命令、旧读端误判），不是防御性堆叠；实施时某一层若没有能触发它的护栏测试，删去该层而不是保留（决策 5、[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 6、[0037](./0037-distribution-and-packaging.md) 决策 7）。
- **`session_opened` 带获取耗时 `acquireMs`**：可由事件时间戳推导，又不是服务商原生量，与「只报原生量」冲突（决策 7）。
- **为开发版本混搭另设拒绝机制**：开发版本混搭不在 [0037](./0037-distribution-and-packaging.md) 的兼容承诺内，为不受支持的组合加机制是额外的设计成本；definition 完整性不变量（决策 13、[0035](./0035-local-app-testing-via-tunnel.md)）不增加成本，又能抓到真实的部署残缺，因此只保留它。
- **按平台常量估计计费量进成本信封**：违反 [0024](./0024-worker-core-protocol.md)「只报原生量」，计费起点与排队是否计费未实测（决策 7）。
- **「等待 W 秒列举为空即视为未创建」消除待核尝试**：实测只覆盖成功返回的 Create，证明不了结果未知的请求在服务端如何处理（决策 3）。
- **新增 `device_setup_failed` 与 `device_unresponsive` 类别**：没有与现有类别处置不同的真实样本，按 [0024](./0024-worker-core-protocol.md) 的扩充规则等样本（决策 4）。
- **Device Farm 上传 API 作为第二条分发通路**：S3 通路已覆盖两个平台与全部签名形态；上传 API 要多一组权限、一份 30 天保留期的副本和第二套状态管理，换不来能力。
- **Device Farm 自动化测试模式**：由 Device Farm 主机执行上传的测试包，与外部 worker 加事件流的形态不同构。
- **默认下载录像与 Appium 日志进产物**：收尾要等到 COMPLETED、日志带端点凭证、多一份数据保留面（决策 8）。
- **收尾等到 COMPLETED**：只增加墙钟、不改计费（决策 5）。
- **建连重试时重建远程访问会话**：每次重建再付固定开销、可能分到另一台设备，scope 内状态也随之丢失；只在设备单元拒装驱动辅助包时换台一次（决策 3）。
- **按错误文本分类会话失败**：文本随 SDK 与服务版本漂移；状态查询是真值，到期按会话年龄判定（决策 4）。
- **获取超时并入 `precheck_failed`**：两者处置相反，前者稍后重试可能成功，后者重试不会变。
- **回收器**：150 分钟原生上限已封顶泄漏费用，第二个会话生命周期持有者会与 worker 的收尾竞争且无法判断会话是否仍在使用（决策 6）。
- **会话结束即删除 Device Farm 会话结果**：与 `explain` 给控制台链接的承诺冲突；清扫由人显式触发的命令列为后续候选（决策 11）。
- **隧道凭据内嵌地址（沿用 0035 决策 4）**：iOS Safari 不采用地址内嵌凭据、改弹原生鉴权表单；桌面上还会让绝对地址的 `history.pushState` 抛 SecurityError（决策 13）。
- **令牌作为查询参数写进 step 文本**：映射器无法区分导航地址与 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 7 的正则参数（令牌拼进正则后 `?` 成为量词），且令牌进入 AI 提示、Midscene 报告、`jobs/*.json` 与设备录像（决策 13）。
- **每个 scenario 前重新预热**：设备上预热是一次导航、会改变页面状态，与决策 1 的「不隐式复位」冲突，每次还要重做路线选择。
- **按系统版本选择导航路线**：iOS 15.8 不支持 deepLink、iOS 18.6 deepLink 后网页上下文挂住、iOS 26.3 只能 deepLink，三者无法用版本号分段表达，能力探测才是判据（决策 13）。
- **剥离转发给上游的隧道 cookie**：ngrok 免费层的付费功能（决策 13）。
- **驱动适配器用 XCUITest 填写 iOS 系统鉴权表单**：鉴权是否成功未证实，把隧道鉴权耦合进 iOS 驱动、每个新会话都要重做。
- **隧道按 Device Farm 公布的设备地址段放行**：取决于服务商套餐，且同一地址段内的其他公共设备使用者同样可达，鉴权强度低于每 run 一换的令牌。
- **对设备目标关闭隧道鉴权**：等于把使用方本机应用在 run 期间向公网开放。
- **额外请求头注入 `Authorization`**：全域广播给页面加载的所有第三方域，泄露面大于 cookie（[0035](./0035-local-app-testing-via-tunnel.md) 已拒），且设备浏览器没有注入请求头的通道。
- **规避被测应用的环境检测**：超出工具职责，且结果不可信（决策 14）。

## 边界与互链

- 本 ADR 不管目标如何声明、本机后端执行前预检对不受支持目标的拒绝、被测环境可达性结论、Job 的 `target` 与 `device_request` 字段形态：归 [0048](./0048-test-targets-device-and-ui-kind.md)；隧道鉴权方案由本 ADR 决策 13 承接。
- `targets` 与 `max_session_s` 的键形态、缺键语义、`min_grace_s` 的推导、会话预热支持键、worker 自检：归 [0049](./0049-worker-capabilities-targets-keys.md)。
- handler 上下文、受命令守卫的 `driver` 代理、确定性 step 的测试分层：归 [0050](./0050-deterministic-step-handles-and-testing.md)。
- 驱动适配器、能力探测与网页上下文身份、导航前提、内建「重新启动应用」step、控件摘要表的抽取方式、超时分层表、只读白名单与命令守卫：归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)。
- `[devices]`（`arn` 或 `os-version`、`billing-method`、获取预算的覆盖、本机后端的项目 ARN 与应用桶）与 `[apps]`：归 [0053](./0053-project-config-file.md)。
- 终结判定的真值表、首次停止原因的仲裁、停止后有界读事件、设备 scope 的缺省墙钟与覆盖顺序：归 [0034](./0034-detached-batch-reconciler.md)；`@timeout` 的设备缺省：归 [0019](./0019-feature-tags-scope-and-engine.md)。
- 沿用并扩展：错误归因类别集、事件集与成本信封 [0024](./0024-worker-core-protocol.md)；网络重试与只读重试例外 [0028](./0028-transient-network-ssl-resilience.md)；上传器 [0029](./0029-engine-artifacts-to-s3.md)；派生态与合成 SKIPPED [0031](./0031-job-lifecycle-states-and-severity.md)；权限表与 region 例外 [0033](./0033-iac-aws-backend-and-composition-wiring.md)；URL 映射、隧道生命周期、脱敏规则与 definition 完整性不变量 [0035](./0035-local-app-testing-via-tunnel.md)；context 闭集、缺戳例外与 definition 格式版本 [0037](./0037-distribution-and-packaging.md)；用户可见消息 [0039](./0039-user-facing-surfaces-no-internal-references.md)；evidence [0042](./0042-step-evidence-and-explain.md)。
