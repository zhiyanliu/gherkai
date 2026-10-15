> 类型: 待批报告

# 移动真机支持（1.5）：ADR 0048 到 0053 修订建议（第五版）

来源：自审 16 条、Codex（gpt-6-astra，ultra）六轮同僚复核（第一轮对六篇 ADR；第二轮对本方案第一版；第三轮对第二版列 7 项阻塞；第四轮对第三版判定 4 项闭合、3 项部分闭合、另发现 1 项退化；第五轮对第四版判定 2 项闭合、2 项部分闭合；第六轮对第五版判定全部闭合、设计层面达成共识）、一轮五结点「设计、双视角对抗核验、修订、完备性评审」工作流，以及 §9 的定稿前实测（已完成的结论内联）。第三版处置第三轮的 7 项阻塞（§12），第四版处置第四轮的 4 项并补入实测结论（§13），第五版处置第五轮余下的 2 项（§14）；§13 末尾单列作者与 Codex 意见不一致之处及作者自己的存疑项。Codex 是同僚不是裁判：每条意见都经作者核对代码或 ADR 原文后才采纳，方案由作者负责。原始材料在 `/tmp/codex-review/`（`out.md` 到 `out6.md`、`knot-*.md`）与 `/tmp/measure/`（边缘策略、上游、探针脚本与结果）。本文只记结论、已定项与实测项；批准后吸收进 ADR，随后删除。

## 0. 总判断与取舍判据

六篇 ADR 的技术路线不必推翻：core 与 worker 的分界、S3 单一分发、不接 `@midscene/ios`、三个正交维度、令牌换 cookie 的鉴权路线都站得住。要改的是 0051 的事件契约与收尾顺序（与 0024、0028、0034 和现有 `run-scope.mts` 三向矛盾）、预算分层的对象错位、隧道令牌的载体、scenario 间的隐式复位、evidence 与 0042 的衔接、以及 Job 里服务商形态的承载方式。

修订按三条判据取舍，目标是 1.5 实现时不留臭味、后续演进不被 1.5 的形态锁死：**一个事实只有一个载体、一条规则只在一处定义**；**机制数量最少**，每个新增物都要回答「删掉会失去什么」；**为演进留接缝、不为局部便利留补丁**。协议只做加法，反转旧条文处逐句点名改写旧 ADR，不靠互链。

## 1. 生命周期、终结判定与收尾

落点：0051 决策 1、4、5、6、7、9；0024 事件集、配对规则、成本信封、`sessionId` 语义、Job 输入形状；0028 硬约束原文保留、三处加法；0034 机制二**点名改写**、「job timeout」节一句改写、超时后有界读事件；0049 决策 5 到 7；0031 决定一、二、三、六；0037 决策 7 与 definition 格式版本。

### 1.1 事件与语义

- **`scope_started` 的含义改为「被测对象已就绪，下一事件就是第一个 `scenario_started`」**，每 scope 至多一次。设备目标上须满足：远程访问会话 RUNNING、Appium 会话建好（含至多一次换台重建）、能力探测完成、应用目标已 `activateApp` 且启动采样未回到「未运行」、网页目标的隧道预热已确认（§3）。此后不再重建会话、不再重试 newSession。0028「越过 `scope_started` 不再重试建连」原文保留。
- **新增成对事件承载会话血缘**：`session_opened{scopeId, sessionId?, name, origin: created | discovered | attempted, device?{platform, model, osVersion, unit}}` 在 Create 返回 ARN 后、一切长耗时动作之前发出（`origin: created`）；按名找回的孤儿会话也发（`discovered`，device 可缺）；**结果未知且终结时仍未排除的 Create 尝试也发一条**（`attempted`，`sessionId` 为 null，只带会话名），这样 worker 知道的待核事实有了协议载体，不靠日志。`session_closed{scopeId, sessionId?, name, release: confirmed | unconfirmed, observedS?, providerMinutes?}` 在该会话的处置**最终结束**时发出，每个会话恰一条；配对键是 `sessionId`，没有时用 `name`。不带「为何停止」的枚举。sessionId、name 与 device 对 core 不透明，端点地址不进任何字段。0024 配对规则改为「`scope_started` 是首条执行事件；其前只允许 `session_opened` 与 `session_closed`」。**桌面 worker 不发这两种事件。**
- **确认停止只认状态**：`GetRemoteAccessSession` 读到 STOPPING 或 COMPLETED，或 Stop 返回体中的状态为两者之一（实测 Stop 在约 0.2 秒内返回、返回体带 `status: STOPPING`，可直接作确认；对已停会话重复 Stop 报 ArgumentException「Invalid parameter RemoteAccessSession」）；Stop 报任何错误都补查一次状态。
- **执行前失败走 `scope_done{status: error, errorType, message}`**，不发 `scope_started`，不发任何 scenario 或 step 事件。判定由 `status` 承载，`errorType` 只回答原因（0024 原则原文保留，补一句「scope 级判定由 `scope_done.status` 承载」）。**桌面 worker 在隧道预热失败时也走这条路**（§3），所以新字段出现在「1.5 CLI 发起、带设备目标或预热地址」的 run 中。
- **`sessionId` 的定义**改为「会话血缘：AgentCore 会话 id 或 Device Farm 远程访问会话 ARN」。
- **同步路径的实时读模型**：`persist.on_event` 收到 `session_opened` 即把 job 刷成 RUNNING 并带 session_id，收到 `scope_started` 时改写为执行会话的 id；`JobState.session_id` 优先取 `scope_started`，没有时退回最近一条 `session_opened`。

### 1.2 终结真值表（两条归约路径共用一个终结函数）

`reduce_event` 继续只累积事实；判定由一个终结函数按下表给出，`schedule._run_once` 与 `project._reduce_scope` 都只调它。**输入**：

- `stop_reason ∈ {none, timeout, abort}`：**推进器的主动处置判定**，不论是否实际发出了停止命令。**首次仲裁规则只有一条**：推进器第一次对该 job 作出停止决定的那一刻落定；若此刻 deadline 已过且 fail-fast 标志也已置，取 `timeout`（本 job 自己的预算事实比来自其他 job 的连带中止更具体，也是使用方能直接处置的原因）；`_stop_all` 批量中止时对每个受影响 job 在那一刻按同一规则落定（deadline 未过的记 abort）。同步路径把落定值写进 JobResult，之后任何分支不改写（现状是事件分支先判 timeout、异常与 EOF 分支先判 abort，两处不一致）；无状态路径由推进器在写退出记录时按同一规则写入 `timed_out` 或 fail-fast 标志（含接力者在观察链丢失时直接落的那一种），重放只读记录、不再仲裁。
- 退出信息、`scope_done` 及其 `status`、scenario 判定集、未确认集 U（发过 `session_opened` 而无 `release: confirmed` 的 `session_closed`，按配对键算；`attempted` 的尝试天然在 U 里，因为它永远不会被确认）。

**明细补全与判定分开**：明细只依据已收到的完成事实——收到 `scope_done.status = error` 就对 definition 中既无 `step_started` 也无 `step_skipped` 的 step 合成 `SKIPPED(shortcircuited=False)`、对无事件的 scenario 合成 scenario 级 SKIPPED，**之后到达的 timeout、abort 或非零退出只改变判定与归因，不撤销已合成的明细**。没有收到 `scope_done` 时不合成。**在途明细的显式规则**（写进 0031 决定一，现只定义了 job 级 aborted）：有 `step_started` 无 `step_done` 的 step、有 `scenario_started` 无 `scenario_done` 的 scenario，不合成任何记录，保持缺记录状态，由 `explain` 的 record_missing 表示「有现场可查」。

| 条件（按行序取第一个命中） | 判定 | 归因 |
|---|---|---|
| `stop_reason = timeout` | ERROR | `timeout` |
| `stop_reason = abort` | ABORTED | 无 |
| 退出码非零或未知 | ERROR | U 非空 → `release_failed`；否则 80 → `network_error`，其余 → `engine_error` |
| 退出码 0，无 `scope_done` | ERROR | `engine_error`（0034 原条文） |
| 退出码 0，`scope_done.status = error` | ERROR | U 非空 → `release_failed`，否则 `scope_done.errorType` |
| 退出码 0，`scope_done` 无 status，scenario 判定集为空 | ERROR | `engine_error`，消息「worker 未报告任何 scenario 判定」 |
| 退出码 0，`scope_done` 无 status，判定集非空 | `_aggregate`（原规则） | U 非空（worker 违约）→ ERROR `release_failed` |
| 未退出 | 见过 `session_opened` 或 `scope_started` → RUNNING，否则 PENDING | |

- U 非空时**无论判定为何**，message 追加产品语言提示「设备会话未能确认停止，可能仍在计费，请在设备控制台核对并手动停止」，并列出 U 中各项的会话名（`attempted` 的尝试只有名字可列，这正是使用方到控制台核查时需要的）。
- 第六行是新增护栏：现状 `_aggregate([])` 返回 passed，零 scenario 的 `scope_done` 会被判 PASSED，今天就是一条假绿路径。
- **0034 机制二的 `exit==0` 一行点名改写**：原文「有 `scope_done` → scenario 归约终态」改为「有 `scope_done` → 先看 `scope_done.status`（error 即 ERROR，带其 errorType），再看 scenario 判定集（为空即 ERROR），再 scenario 归约」。0031 决定一补在途明细规则与「SKIPPED 也在 scenario 级出现，只由 core 在 scope 级 error 后合成」；决定三补「合成的 scenario 级 SKIPPED 不喂给 `_aggregate`」；决定六补「`SKIPPED + shortcircuited=False` 只出现在 job 处于 scope 级 error 时」。
- **停止后继续有界消费完整事件流**：schedule 现状是先从迭代器取事件、再查 deadline、再归约，触发超时检查的那条事件本身没有被归约；改为任何停止之后仍把当前事件与后续事件全部归约，直到 EOF 或排空上界（宽限加余量）。无状态路径重放全部已写事件，天然一致。
- **双路径对拍测试**作为实施护栏：同一组事件矩阵（前置 scope 级 error 加退出 0、scope 级 error 后超时、停止后到达的 `session_opened`、未确认的 `session_closed`、timeout 与 abort 同时成立、零 scenario 的 `scope_done`、接力者直接落 `timed_out`）喂给两条路径，判定、归因、明细逐项相等。

### 1.3 收尾顺序、退出码与释放预算

- **正常收尾沿用现有实现，0051 决策 5 的「`scope_done` 先于收尾」反转**：最后一个 `scenario_done` → `agent.destroy` 与 scope 级报告 → 有界上传 → `deleteSession`（5 秒，不重试，不阻塞 Stop）→ **终结核对**（下文阶段 2，正常路径同样执行）→ 释放阶段 → 每会话 `session_closed` → `scope_done` → 排空上传队列 → 退出。「收尾的延迟或失败不得影响判定」一句删除。
- **结果未知的 Create 尝试有明确的生命周期**：Create 请求超时或连接中断时该尝试记为「待核」，带会话名（名字含尝试序号，按名列举后按序号对应）。**待核尝试只能由正面证据消除**：按名列举命中，登记进待清理集并发 `session_opened(origin: discovered)`，随后与其他会话一样释放并确认。列举为空不构成排除证据——实测只证明成功返回的 Create 在 1 秒内可见，没有证明结果未知的请求在服务端如何处理，也不能排除它在列举之后才出现；所以不设「等多久为空就算没建」的窗口。每次重试前与每条终结路径（正常收尾、SIGTERM、异常退出）都做一次核对，核对须在预算内处理分页（`ListRemoteAccessSessions` 带 `nextToken`、无服务端按名过滤），未扫完即视为未核对。终结时仍有待核尝试，或核对失败、未扫完，就为每个待核尝试发 `session_opened(origin: attempted, name)` 与 `session_closed(release: unconfirmed, name)`，退出码 1，message 用产品语言提示按会话名核查。这是有意的保守：代价是罕见的误报「请核对控制台」，换来不漏报一个可能计费到上限的会话。
- **SIGTERM 与一切异常终结路径按四个阶段执行，各有绝对截止线**（相对收到信号或进入终结的时刻 t）：
  1. **等在途 Create**（t 到 t + 10 秒）：在途的 Create 返回即登记 ARN；超时则把该请求标为「结果未知」。
  2. **终结核对**（至多 5 秒，`ListRemoteAccessSessions` 按名列举、含分页）：对全部待核尝试按上一条的生命周期规则处理；本阶段结束时仍有待核尝试即按上一条发 `attempted` 的成对事件。
  3. **释放阶段**（25 秒，全部待清理会话并行、共享截止线）：每个会话 Stop（3 秒）→ 失败则 Get 补查（5 秒）→ 退避 → 再 Stop 一次 → 再补查；到线即记 `release: unconfirmed`。中止当前 act 的 `abortSignal` 在进入阶段 1 时同时置位；SIGTERM 路径不调 `deleteSession`（Stop 决定计费）。
  4. **事件与产物**：每会话 `session_closed`、中断兜底上传（10 秒）、截图队列排空（6 秒）。
  `min_grace_s` = 10 + 5 + 25 + 10 + 6 + 事件写出与余量（约 7.5）≈ 64 秒，低于 Fargate `stopTimeout` 的 120 秒；各段上限以网络退化实测校准后定数。0049 决策 5「增量在秒级以内」改为按上式推导。
- **Create 的孤儿防护**：Device Farm 客户端 `maxAttempts = 1`，由 worker 在获取预算内显式重试；每次重试前，以及上述阶段 2，都按会话名有界列举。会话名由固定前缀、run_id、scope_id 的安全编码与尝试序号组成，长度封顶（实测 name 256 字符接受、257 字符 ValidationException），编码规则写进 0051。实测同名会话可以并行创建，名字没有唯一性，所以尝试序号是名字的一部分、按名列举后还要按序号对应；Create 没有幂等令牌，按名查询只是补救不是幂等保证。
- **退出码**：0 表示内容完整且全部会话已确认停止；1 表示存在未确认停止的会话（含 `attempted` 的待核尝试）或 worker 自身异常；设备 worker 不使用 80。无 ARN 的取消路径（Create 结果未知 → 核对失败 → SIGTERM、无 `scope_done`）因此也能把待核事实带到 core：U 非空，两条归约路径都在 message 里给出会话名。SIGTERM 收尾成功但没有 `scope_done` 时退出码按上式，判定由推进器的 `stop_reason` 给出。
- **会话丢失序列**：当前 step `step_done{error, session_lost}` → 本 scenario 余下 step `step_skipped`（`shortcircuited=True`）→ `scenario_done{error}` → 后续 scenario 不发事件 → 收尾 → `session_closed` → `scope_done{status: error, errorType: session_lost}`；后续 scenario 由 core 合成 SKIPPED。Stop 规则只有一条：会话状态仍为 RUNNING 就发一次幂等 Stop；已是 STOPPING 或 COMPLETED 则不发 Stop、不调 `deleteSession`。

### 1.4 设备分钟、错误类别与协议启用条件

- **设备分钟只报原生量**：`session_closed.observedS` 是 worker 观察到该会话的时长（起点 Create 返回时刻，孤儿为列举发现时刻；止点为发出 Stop 或确认其已停止的时刻），缺失记 null，null 不等于 0。`providerMinutes` 保留 AWS 原形 `{total, metered, unmetered}` 快照，可缺。core 把 `observedS` 合计成 job 与 run 级「设备占用时长」，缺值会话另计数。不写任何依赖计费起点的断言，只说明口径不同、以账单为准。0024「cost 只挂 `step_done`」改为「`step_done` 与 `session_closed` 各挂各的原生量，每个字段只在一层出现，core 逐字段跨层合计」。
- **错误类别**：保留 `precheck_failed`、`acquire_timeout`、`session_lost`；新增 core 派生的 `release_failed` 与 step 级的 `capability_unavailable`（§4）。不新增 `device_setup_failed` 与 `device_unresponsive`。
- **协议启用条件如实写明**。旧读端读到新语义的真实路径有两条，都在本机后端：1.4 的 `status --wait` 接力读取 1.5 写的 definition（旧反序列化丢掉 `target` 与 `device_request`、把设备 job 派发成桌面 job），以及 1.4 CLI 的 `status` / `explain` 读 1.5 的事件（旧事件解析忽略 `scope_done.status`，零 scenario 判 PASSED）。0049 决策 7 原文已写明「1.5 之前的 worker 不认识目标字段，自检对它无效，只由版本解析保证」，第二版「旧 worker 被自检拒」的说法删除。机制：
  - **definition 加整数格式版本 `format`**（`run_meta.json` 与 DDB META），1.5 起写入并在全部读端（提交、接力推进、`status`、`explain`、重放投影）核对：高于自己支持的版本以退出码 2 结束，产品语言提示升级。1.4 读端无法追加这项检查，**同一 report 目录混用 1.4 与 1.5 CLI 读写列为不受支持的组合**，写进用户文档升级说明。
  - 云端：0037 决策 7 的闸门拒绝「CLI 新于后端」且无放行口；后端内部（Lambda 与 worker 镜像）同版本。**缺版本戳的旧后端是一条独立于开发版本的暴露路径**（0037 对缺戳只警告，`push-worker` 同样放行）：正式版新 CLI 加新 worker 配无戳旧后端，旧 Lambda 丢掉预热地址或设备字段，worker 的完整性检查只能把它变成「空判定集加退出 0」，旧归约端仍判 PASSED。处置：0037 决策 7 的「缺戳只警告」加一条例外——**run 带设备目标或会话预热地址时，缺戳即退出码 2**，消息「后端部署早于本功能，请先升级部署」；桌面无隧道的 run 维持只警告，不锁死现存部署。剩余暴露只剩开发版本混搭（闸门对开发版本跳过比对、`push-worker` 沿用此规则）：旧开发版 Lambda 读新 definition 时丢掉预热地址，新 worker 便在没有预热的情况下执行，导航与地址核对可能在 401 页上通过，判定集非空、零判定护栏挡不住。处置两层：**0035 补一条 definition 完整性不变量**——隧道模式下 definition 必带「额外请求头」与「会话预热地址」两项，worker 收到额外请求头却没有预热地址即 `precheck_failed`「后端未传递会话预热地址，部署版本可能低于命令行工具，请重新部署」（额外请求头在隧道模式下恒注入是 0035 决策 4 的既有不变量，这里只是把两项绑成一个完整性判据，不是按文本猜测）；同时开发版本混搭在 0037 本来就不在兼容承诺内，用户文档的升级说明写明。
  - 0037 决策 7 补一句「协议与 definition 的加法扩展各自论证兼容性，不默认由版本闸门保证；definition 格式版本是其中一道」。
- **worker 读墙钟预算只为自检**：0034「job timeout」节改写为「worker 不强制执行 timeout（到点处置全在推进器侧）；唯一读取是建会话前把 Job 携带的墙钟预算与 `max_session_s` 比较作自检，不计时、不自停」。0024 的 worker Job 输入形状加可选 `timeoutS`，只在此一处定义。

## 2. 预算分层、取消与重试

落点：0052 决策 6 放分层表，0051 决策 2、3、12 与 0048 决策 8 改为指向它；0049 决策 4、5、7；0019 `@timeout` 节与 Status 头；0034「job timeout」节的 flag 承诺；0028 硬约束与「关键不变量」节的加法；CLI 的 `--default-job-timeout` 文案与归一化；0050 决策 2 的 `driver` 句柄。

| 层 | 起点 | 执行者 | 覆盖 | 到期归因 | 重试 |
|---|---|---|---|---|---|
| ① job 墙钟 `Job.timeout_s` | 推进器 claim | 推进器 | 拉镜像、获取、执行、收尾 | `timeout` | 设备 job 不参与 core 的 `network_retry` |
| ② 会话上限 `max_session_s` | 发出 Create | 由「① 不超过 ②」的预检或自检保证；worker 另按会话年龄做后备 | 单会话寿命 | 年龄到点：当前 step error、余下 skipped、发 Stop、归 `session_lost` | 不重试、不重建 |
| ③ 获取预算（缺省 600 秒，可配，上界 3600 秒） | 进入设备解析（筛选时首次列举，直接 ARN 时首次 Create） | worker | 筛选与繁忙等待、创建与限流退避、排队、准备、newSession 含安装、至多一次换台重建、`activateApp` 与自退采样、能力探测、隧道预热；止于被测对象就绪 | `acquire_timeout`；判据型失败归 `precheck_failed` | worker 内手写退避，跨重建不重置；剩余不足 150 秒不再换台 |
| ④ Device Farm 单次调用 | 每次调用 | worker | Create、Get、List、Stop | 获取期计入 ③ | `maxAttempts = 1`，请求超时 10 秒（Stop 3 秒，收尾期 Get 5 秒），手写退避，停止信号可穿透 |
| ⑤ newSession 单请求超时 | 发出 newSession | WebDriver 客户端 | 建会话加 `appium:app` 安装 | 计入 ③ | 不小于 4 分钟加 65 秒，以剩余 ③ 封顶；传输层 0 次 |
| ⑥ 执行期单请求超时 | 每个请求 | WebDriver 客户端 | 单条命令 | 结果未知（见下） | 0 次；只读原语白名单重试 1 次 |
| ⑦ W3C `pageLoad`（适配器常量，暂定 150 秒） | 每条导航 | 服务端驱动 | 页面加载 | 服务端回 `timeout`，结果已知 | 不重试 |
| ⑧ `appium:newCommandTimeout` | 上一条命令返回后 | Appium 服务端 | 命令之间的空闲 | 会话被回收，查状态后按 0051 决策 4 归因 | 不适用 |
| ⑨ Midscene 重规划 12 轮、每个 act 累计 5 次动作错误 | 每个 act | Midscene | 次数上限，不是时间上限 | 现有规则 | 不适用 |
| ⑩ 终结四阶段 | 进入终结 | worker | §1.3 的四个阶段与各自截止线 | 释放未确认即 `release_failed` | 见 §1.3 |

不变量：① 不超过 ②；设备 scope 的 ① 不小于 ③ 加最短余量；**⑥ 是单条命令的真实上界，⑦ 只是尽力而为**（实测：Android Chrome 上 `pageLoad` 设 3 秒、10 秒慢页在 14.6 秒后才报 timeout；iOS Safari 上设置不被反映、`url` 在 3.2 秒就返回而页面尚未加载完），⑥ 取 ⑦ 加余量只是为了给服务端先报的机会；⑧ 不小于最长命令间空闲（含单次模型规划）加余量——Android 与 iOS 实测 `newCommandTimeout` 都只计命令之间的空闲、长命令执行期间不计时，第一版那条「对两种计时语义都安全的 max 形式」据此删去；⑤ 到 ⑧ 由适配器显式设定，不依赖 SDK 缺省；同一会话上两个 webdriver 10.0.2 客户端实例各自的 `connectionRetryTimeout` 在两个平台上都各自生效（3 秒的实例 3.0 秒超时、缺省实例完成同一慢导航），建连、执行与探测可以用不同实例设不同超时。

- **删除全部「step 预算」措辞**，不另行定义。0052 决策 6 的「与 step 超时脱钩」改为「与 job 墙钟脱钩」。
- **设备 scope 墙钟预算的覆盖顺序与校验顺序**（写进 0019 `@timeout` 节、0034「job timeout」节与 0053）：
  1. 先按来源取值：`@timeout:N` tag → 显式给出的 `--default-job-timeout`（选项、环境变量、配置文件任一来源，argparse 缺省改为「未指定」哨兵以区分内建 300 与显式 300）→ 目标缺省（设备 scope 为 ③ + 900 秒，桌面为 300 秒）。
  2. **非正的 `--default-job-timeout` 只表示「非设备 scope 不超时」**：设备 scope 在这一步落到目标缺省，不被拒绝。归一化只接受有限数，拒绝 NaN 与 Infinity。
  3. 再做下限校验，**只对 tag 与显式正值**：设备 scope 的值低于 ③ + 180 秒时抛 `FeatureContractError`（退出码 2），消息说明「可能还没拿到设备就被判超时」。目标缺省自身满足下限，不校验。
  `PlanConfig` 加「设备 job 缺省墙钟」与「设备 job 墙钟下限」两个数值由 CLI 算出传入，`_resolve_timeout` 按 scope 的目标选用；0034「所有未标 tag 的 job 使用该 flag」一句据此改写；0019 Status 头的「`@timeout:` 语义不变」同步改。900 与 180 是待校准的缺省策略，不是经验证的预算保证。
- **慢页面**：单次加载超过 ⑦ 的站点在 1.5 不受支持，写进用户指南限制段；调大 `@timeout` 只解决多次加载累积的墙钟不足。0048 决策 8 相应改写。
- **执行期关闭 WebDriver 传输层自动重试**（`connectionRetryCount = 0`）。只读原语白名单（截图、取上下文列表、page source、已确认网页上下文中的**读取地址**、`/status`、`deviceScreenInfo`）由适配器重试 1 次，只对网络错误码与 502、503、504。**0028 硬约束节原位加一句**：「执行期对只读原语的传输层有界重试既不是建连重试也不是 act 重试，不在本节禁令之内」。
- **命令守卫是会话级的，覆盖全部命令入口**：worker 交给 Midscene 适配器、内建导航与确定性 handler（0050 决策 2 的 `ctx.driver`）的都是同一个受守卫的 driver 代理，不暴露裸客户端。守卫维护两件状态：**当前执行令牌**与**结果未知标志**（置位后本 step 内一切有副作用的命令被拒绝，只读白名单放行）。令牌在 step 开始时发出，**在 step 结束、取消或进入终结的那一刻立即撤销**，不等下一 step；带旧令牌或无令牌的调用一律拒绝，覆盖 handler 在 `await` 之后恢复执行、step 结束后保留的引用、以及 SIGTERM 收尾与主执行并存的窗口；收尾自身的调用由生命周期管理方经自己的通道执行，不借执行令牌。实测（§9）表明 Midscene 1.15.1 在适配器抛错并置 `abortSignal` 后立即结束 act、不再发任何动作，所以守卫的必要性来自 handler 与晚到引用，不来自 Midscene 的重新规划；仍保留为纵深防御。0050 决策 2 的 `driver` 定义补「受命令守卫的代理」。
- **worker 进程级兜底**：实测中 webdriver 10.0.2 的 newSession 在客户端 2 秒超时后出现过一次进程直接退出（未处理的异步错误），`finally` 没有机会执行、会话泄漏；复测一次未复现。worker 须注册 `unhandledRejection` 与 `uncaughtException` 处理器，记录后进入终结四阶段而不是任由进程退出；这条写进 0028 的 worker 侧实现要求。
- **结果未知的命令**（客户端超时或连接中断，且不在白名单）：守卫置结果未知标志并中止当前 act 的 `abortSignal`；worker 查一次会话状态：非 RUNNING 按 `session_lost`；RUNNING 则当前 step 记 error、类别 `engine_error`、消息「设备在等待时间内没有回应，这一步可能已执行也可能未执行」，本 scenario 短路；下一条 scenario 前做一次只读存活探测（截图），失败则发 `scope_done{status: error, errorType: engine_error}` 由 core 合成余下 SKIPPED。任何层都不补发。
- **0028 的加法**：「core 层 job 重试」门槛加第三条「job 目标不是设备」；「幂等性依据」末尾补「Device Farm 的 Create 不在可安全重放之列，设备 worker 对它关闭 SDK 自动重试」；「关键不变量」节补「隧道预热失败不是建连失败，不用退出码 80，经 `scope_done` 传递（§3）」。

## 3. 隧道：令牌换 cookie 的完整契约

落点：0051 决策 11、13；0035 决策 1、2、4、5 与不变量、Status 头双向；0052 决策 6；0048 决策 8；0049 能力键；0037 决策 4 的 env 清单；CONTEXT.md「隧道暴露」词条。

- **令牌由 definition 承载、worker 预热（已定）**。组合根生成每 run 一换的令牌 T，写进 definition 新字段「会话预热地址」，无值省键，core 只搬运；引擎适配器经新 env `GHERKAI_SESSION_WARMUP_URL` 注入 worker。worker 在被测对象就绪之前、第一个 scenario 之前对网页目标**导航预热地址一次**，不按 scenario 重做。**导航路线由能力探测决定、不按系统版本分支**（0052 决策 5 的既有原则，实测给出了两条反例支撑它）：网页上下文可用（能在短预算内执行一条只读命令）时走 `url`；不可用时走 `mobile: deepLink`。iOS 15.8 上 `mobile: deepLink` 不受支持（XCTest 报「当前 Xcode SDK 不支持打开地址」），只能走 `url`；iOS 18.6 上先用 deepLink 再切网页上下文，网页命令全部挂住，改走 `url` 则全部通过；iOS 26.3 网页上下文列得出、切得进但命令挂住，只能走 deepLink。应用目标不预热。step 文本只做「origin → 干净隧道地址」映射。
- **预热页面有三种可见结果，确认判据三端同一条**：预热路径凭令牌返回 200 页面并下发 cookie，页面脚本向只凭 cookie 放行的校验路径发一次请求：成功则把标题与正文标记改为 READY；得到 401 改为 DENIED；请求失败改为 ERROR。令牌错误时预热路径直接返回 401 页，正文标记 AUTH REQUIRED。worker 不依赖网页上下文：桌面读响应状态与标记；设备在**原生控件树**里查找标记文本（Safari 与 Chrome 把网页正文暴露为可访问性节点）。**归因**：READY → 就绪；DENIED 或 AUTH REQUIRED → 确定性拒绝，`precheck_failed`（消息：浏览器未接受测试会话 cookie 或令牌无效，换设备或检查隧道）；ERROR 或预算内无任何标记 → 原地重导航有界重试，耗尽后 `engine_error`「未能确认隧道预热」。**两者都不归 `network_error`**（0028 分类红线：鉴权失败与拿不准的失败不得归瞬时网络故障），桌面也不用退出码 80，一律经 `scope_done{status: error, errorType}`（§1.1）。
- **边缘策略在 ngrok 免费层的两条硬约束已实测**：每个策略**至多 5 条规则**（第 6 条即拒绝启动），`remove-headers` 是**付费功能**。因此策略定为 4 条：预热路径凭令牌 200 加 Set-Cookie；预热路径其余情形 401；校验路径凭 cookie 200；其余路径 cookie 不等于 C 则 401（校验路径此时也落到这条）。**不剥离转发给上游的隧道 cookie**（付费功能），C 会进入被测应用的访问日志，列为已知边界：C 每 run 一换、随隧道关闭失效。
- **cookie 规格**：`__Host-gherkai_tunnel=C; Secure; HttpOnly; Path=/; SameSite=None`，无 Domain，无 Max-Age。T 与 C 各是至少 128 位的随机串，只写进本 run 的流量策略文件（0600）。**SameSite 维持 None**，第三方登录的跨站 POST 回跳带 cookie 已在桌面 Chromium、Android Chrome、iOS 15.8 与 18.6 Safari 上实测成立（§9）；iOS 26 无可用网页上下文、无法从第三方页面提交表单，未测。
- **边缘契约实测（curl 16 项全部符合预期）**：无 cookie 401；预热路径令牌错 401；预热路径 POST 401；预热路径 GET 正确令牌 200 且带 `Set-Cookie`、`Cache-Control: no-store`、`Referrer-Policy: no-referrer`；校验路径无 cookie 401、cookie 正确 200、值错 401；业务路径 cookie 正确 200、值错 401、多值同名 cookie 其一正确 200、有效 cookie 加同名查询参数 200 且原样转发；预热路径有效 cookie 加错令牌 401；POST 业务路径 cookie 正确 200；浏览器 UA 不带跳过头且 cookie 正确 → 直接得到上游页面、无警告页；上游日志不含任何 `.well-known` 请求。
- **桌面 Chromium 闭环实测通过**：预热 200、标题变为 READY；cookie 属性 httpOnly、secure、SameSite None、会话 cookie、无 Domain；业务页 200 且 cookie 到达上游；错令牌 401 页；之后业务页仍 200；从第三方站点提交的跨站 POST 到达上游且带 cookie；`history.pushState` 正常。
- **映射规则在 0035 决策 2 原地精化**（修现有 `s.replace(origin, base)` 的子串缺陷）：URL 字符集按 RFC 3986；左边界为串首或非 scheme 字符；右边界为 origin 后最长 URL 字符串 R 为空、或以 `/ ? #` 开头、或全为尾随标点。钉死用例：`http://localhost:3000.evil/` 与 `http://localhost:30001/x` 不命中；`去 http://localhost:3000。`、`Go to http://localhost:3000.`、`(see http://localhost:3000)`、`打开http://localhost:3000/a页面` 命中。step 正文、DocString、表格单元格各自独立套用。
- **能力与拒绝点**：worker 能力自述加一个键声明支持会话预热（schema 1 加键）；本机后端在执行前预检里核对，`--expose-local` 下遇不声明的 worker 拒绝；云端依靠按版本解析镜像；第三方 worker 的表现是导航得到 401 页，页面正文说明原因。
- **点名改写**：0052 决策 6「导航原语只打开 step 文本里已带令牌的地址」、0048 决策 8「URL 映射对 worker 透明」、0035 不变量「worker 对隧道无知」、CONTEXT.md「隧道暴露」词条的「引擎对隧道无知」，统一改为「worker 只做一次预热导航并确认标记，不感知令牌与 cookie 的值」。0035 决策 4 的「`ngrok-skip-browser-warning` 恒注入」保留给桌面；设备浏览器没有注入请求头的通道，四台真机实测都没有出现免费层警告页（§9），条文写成「实测未出现，若服务商改变行为则为设备目标要求付费层」。
- **已知边界**：被测应用在 scope 内下发 `Clear-Site-Data: "cookies"` 后，后续请求 401，1.5 记为已知边界（拆成多个 scope 规避）；step 代码直接向隧道域发请求须经浏览器上下文的请求通道；隧道 cookie 会到达被测应用。
- **数据保留**：令牌不进 step 文本，`jobs/*.json` 不含秘密，不改 0644（它只被 `status` 与 `explain` 读取，0035 决策 5 的括注据此更正）。T 的残留面如实列全：`run_meta.json`（0600）、DDB META、S3 参数卸载对象、流量策略文件、本机 worker 进程环境、云端 RunTask 的 `containerOverrides`（DescribeTasks 可读，CloudTrail 是否记录待核）、设备录像与 Appium 日志里的预热地址、隧道服务商的流量记录；C 的残留面：流量策略文件、浏览器 cookie 库、被测应用的访问日志。T 与 C 随隧道关闭失效。Device Farm 会话结果不自动删除，用户指南写明 400 天保留、us-west-2 驻留、控制台删除方法与「用专用测试账号」的建议；清扫命令列为后续候选（已定）。

## 4. scope 内状态、地址核对、evidence 与网页上下文

落点：0019 `@scope` 词句澄清；0051 决策 1、7；0048 决策 2、6、7；0050 决策 1、2、4；0052 决策 2、5、7；0042 决策一、二、四（只限设备目标的例外）；0027 与 0042 决策五不改动（`device_session` 只是链接）；CONTEXT.md「能力探测」「step 证据」词条。

- **scenario 间不做任何自动复位，全部目标适用**（维持 0019）。0051 决策 1「网页目标重新导航，应用目标先 terminate 再 activate」与 0048 决策 2 末条删除；应用在建会话后启动一次。新增内建确定性 step「重新启动应用」（只注册 `webdriver` 的 `uiKinds: ["app"]` 条目；terminate 加 activate 加启动采样；采样到自退记 error、类别 `engine_error`）；agent skill 写作规则：应用目标的多 scenario feature 缺省在 Background 放此 step；plan 不按 step 文本检测。
- **内建「页面地址匹配」step 的前提显式声明**：`webdriver` 注册条目加可选 `requires: ["web_context"]`（worker 注册期按封闭集合校验，含它时 `uiKinds` 须恰为 `["web"]`；CLI 侧只核形态，未知取值原样显示）；能力自述 step 级 `targets` 加 `requires` 键，不同 `requires` 的条目拆开不聚合；plan 标注「需要网页上下文；设备不提供时记为错误」。运行期：探测确认不提供时不调 handler，step 记 error、类别 `capability_unavailable`；探测出错时记 `engine_error`。设备上任何「读当前地址」先查探测结论，不可用时得到「无地址」，绝不调用 `url`。0048 决策 7 与 0050 决策 1 的「在设备网页上照常可用」改为条件式；写作规则：`@device:android` 网页目标用确定性地址核对，`@device:ios` 网页目标在 1.5 推荐用 AI 断言核对落点。
- **evidence 与 0042 的衔接**（只限设备目标的例外，桌面不变）：AI step 各状态都产，加设备字段；确定性与导航 step 只在 failed / error 时产（`acts: []`）。字段在 schema 1 上加键：`step_kind`、顶层 `url` 与 `url_missing`、`controls{items[{type, id, text, a11y_id}], total, truncated}` 与 `controls_missing`、`page_source`（独立文件的 URI）与 `page_source_truncated`。控件摘要与原始树都只在 failed / error step 上采集（已定）；采集有独立短预算，按步累加并计入 job 墙钟。`evidence.mts` 改为接收一份已采集好的界面快照。`controls`、`page_source`、`url` 写盘前都经 0051 决策 11 的脱敏出口，规则同时覆盖 XML 实体转义形态。0050 决策 4 的「设备目标上含每步的控件信息」同步改为「失败步的控件信息」；CONTEXT.md「step 证据」词条补设备确定性 step 的例外。
- **scope 表头**由 `session_opened.device` 与 `scope_started.sessionId` 派生。探测结论（网页上下文提供与否、候选数、输入路线、坐标比例、Appium 版本）写入 best-effort 的 `device-session.json`，以 `kind: "device_session"` 作为**普通产物链接**只挂在 `scope_done` 上；`explain` 只渲染链接，**不解析其内容**，不新增 schema（0042 决策五与 0027 的「只对自有 evidence schema 解引用」不变）。探测结论同时写进 worker 日志。
- **网页上下文：能力结论与身份分开**。会话内只缓存能力结论与输入路线、坐标比例，不缓存上下文句柄；每次进入网页上下文都重新列出并按类别筛选。**「可用」的判据是能在短预算（5 秒）内执行一条只读命令**，不是列得出或切得进：iOS 26.3 实测列得出 WEBVIEW、切换成功，但任何网页命令都挂到 120 秒客户端超时再重试三次。1.5 过渡规则：只有一个候选且可用才采用；多个候选记 error、类别 `engine_error`；零候选短等待后再列一次，仍为零记 `engine_error`；`fn` 执行中句柄失效直接记 error、不重试。iOS 15.8 与 18.6 上 `mobile: getContexts` 返回每个 WEBVIEW 的标题与地址，是将来放宽多候选规则时的身份依据（候选）。CONTEXT.md「能力探测」词条的「结果缓存在会话内」改为「能力结论缓存在会话内」。
- **0052 决策 2 的界面接缝补三项 step 边界义务与固定顺序**（桌面上三项都是空操作，不定方法名）：`step_started` → step 前核对处于原生上下文 → 执行 → 需要时在网页上下文读地址 → 复原并核对原生上下文（失败则最终判定改为 error、原判定写进 message；命令失败先查会话状态）→ 在原生上下文采集控件摘要（failed / error）→ 产 evidence、发 `step_done` → 后台上传。

## 5. Job 形态、部署与诊断归属、设备解析、应用对象、权限

落点：0048 决策 3；0053 决策 3、4、6；0051 决策 6、8、9、10 与新增「设备解析」决策；0052 决策 3；0033 权限表与 region 条；0037 决策 6 的 context 闭集；CONTEXT.md。

- **Job 两个字段**：`target{device, ui_kind, app?{alias, bucket, key, sha256, app_id}}` 与具名结构 `device_request{provider: "aws-device-farm", device_arn | os_version, billing_method, project_arn, acquire_timeout_s}`。core 由 tag 构造 Job 时只填 `target`（plan 用此形态）；`run` / `submit` 在组合根填入 `device_request`，写 definition 前与读 definition 时各做一次结构校验；取值域校验在 CLI（退出码 2）。**云端 `project_arn` 来自 SSM，缺失时 `run` / `submit` 在提交前以退出码 2 结束**，消息「部署未启用设备支持」。发给 worker 的形态加 `deviceRequest?`、`timeoutS?` 与完整 S3 位置，由一条 Python 到 TS 的往返测试守。`billing_method` 留在 job，允许按平台覆盖；形态过滤由 worker 固定只取手机。
- **Device Farm 调用归属**：worker 的 TS 设备模块是执行期唯一调用处；Python 侧「部署与诊断模块」（`gherkai-runtime[aws]`，延迟导入）承担 deploy 找回或建立项目、`doctor` 列举会话；推进器不调 Device Farm。护栏测试：客户端只在这两个模块构造，core 零引用。Device Farm 客户端固定 us-west-2，0033 加例外。0051 决策 6「不做回收器」的理由改写为「会话生命周期由 worker 独自持有，第二个持有者会与收尾竞争且无法判断会话是否仍在使用；泄漏由 150 分钟上限封顶」。
- **部署**：只有 `deploy` 子命令在 cdk 之前用 SDK 找回或建立项目 `{prefix}devices`（先 SSM、再按名称；命中多个退出码 2）；`diff` 不建立项目，SSM 已有值时沿用、没有时以「待建立」占位。ARN 作为命令自派生的 context 交给 stack（0037 决策 6 闭集加 `device_farm_project`），stack 写 SSM 参数并按下表给 task role 授权；`destroy` 保留项目。部署方无 Device Farm 权限时：SSM 已有 ARN → 沿用并警告；没有 → 警告并跳过，云端设备 job 在提交时被拒。
- **设备解析**移入 0051 新决策，0053 决策 4 只留用户面语义。完整分页列举；静态过滤平台、点分段版本族、手机形态、支持远程访问；首轮零候选再列一次仍为零即 `precheck_failed`；选择规则（已定）：在全部匹配候选中先排除 BUSY 与 TEMPORARY_NOT_AVAILABLE，再按版本号高、HIGHLY_AVAILABLE 优于 AVAILABLE、ARN 字典序取第一台；全部繁忙才等待。`os-version` 按点分段族匹配，必须是 TOML 字符串。获取预算在 0051 决策 2 原位改写为从进入设备解析起算。
- **应用对象**：键 `apps/<sha256>/<原文件名>`；cloud 后端打标签 `gherkai=app`，产物桶按标签过期 E = 14 天，承诺已提交 run 的输入至少保留 R = 7 天；复用时对象年龄超过 E − R 就同键 CopyObject 刷新（`MetadataDirective=REPLACE` 回写元数据、`TaggingDirective=REPLACE` 回写标签），刷新失败重传，再失败提交失败；生命周期是否按新创建时间重新计时在实施期核。本机后端用使用方的桶，不打标签、不承诺；SSE-KMS 桶需对应 KMS 权限，写进支持边界。worker 建会话前做存在性检查：404 记 `precheck_failed`「安装包已不在存储桶里，请重新提交」，403 记 `precheck_failed` 并说明是权限问题。「约 1.4 GB 上限」改为有前提的估算，CLI 对超过 500 MB 的包警告不拦截。0051 决策 8「Job 只带 S3 键」改为「带完整 S3 位置」。
- **权限按动作与资源类型逐项登记进 0033 的唯一权限表**（据 AWS 服务授权参考），0051 决策 10 只留指针与本机后端说明：

| 主体 | 动作 | 资源 |
|---|---|---|
| worker | `devicefarm:ListDevices` | `*`（该动作不支持资源级限制） |
| worker | `devicefarm:GetDevice` | `arn:aws:devicefarm:us-west-2::device:*` |
| worker | `devicefarm:CreateRemoteAccessSession` | 同时列出本项目 ARN 与 `arn:aws:devicefarm:us-west-2::device:*` |
| worker | `devicefarm:GetRemoteAccessSession`、`StopRemoteAccessSession` | `arn:aws:devicefarm:us-west-2:<账号>:session:<项目 id>/*` |
| worker | `devicefarm:ListRemoteAccessSessions` | 本项目 ARN |
| worker | `s3:GetObject`、`s3:ListBucket`（条件 `s3:prefix` 为 `apps/`） | 应用前缀 |
| CLI | `s3:GetObject`、`s3:ListBucket`（前缀条件）、`s3:PutObject`、`s3:AbortMultipartUpload`、`s3:PutObjectTagging`（cloud） | 应用前缀 |
| CLI | `devicefarm:ListRemoteAccessSessions`（doctor） | 本项目 ARN |
| deploy | `devicefarm:ListProjects`、`GetProject`、`CreateProject` | `*` / 本项目 ARN |

  IAM 策略模拟器对上表的允许与拒绝结果见 §9；真实角色的闭环实测需要建一个测试角色，列为实施前置。
- **`project-arn` 与 `app-bucket` 可入库**（已定），跨账号部署用环境变量按环境给出；本机后端下 ARN 账号与当前凭证账号不一致时 CLI 警告不拦截。
- **术语先进 CONTEXT.md**：设备请求、设备解析、获取预算；「远程访问会话」词条的「按创建时刻计费」改为「计费口径以 Device Farm 账单为准」。

## 6. 协议与机读契约变更汇总（全部加法）

- 事件：新增 `session_opened{scopeId, sessionId?, name, origin, device?}`、`session_closed{scopeId, sessionId?, name, release, observedS?, providerMinutes?}`（配对键 `sessionId`，缺省回退 `name`）；`scope_done` 加可选 `status`（只取 `error`）、`errorType`、`message`。只出现在 1.5 CLI 发起、带设备目标或预热地址的 run 中。
- definition：加整数格式版本 `format`；`RunMeta` 加会话预热地址；Job 加 `device_request`；env 加 `GHERKAI_SESSION_WARMUP_URL`。
- worker Job 输入：加 `timeoutS?`、`deviceRequest?`，`target.app` 带完整 S3 位置。
- `sessionId` 语义放宽为会话血缘；cost 可挂 `session_closed`。
- 错误类别集加 `precheck_failed`、`acquire_timeout`、`session_lost`、`capability_unavailable`、`release_failed`（core 派生）。
- `JobResult` 加 `sessions`、`device_observed_s`（含缺值会话计数）；`RunResult` 加 `device_observed_s`；scenario 级可出现合成的 skipped。
- 能力自述（schema 1 加键）：step 级 `targets[].requires`、会话预热支持键。
- evidence（schema 1 加键）：`step_kind`、`url`、`url_missing`、`controls`、`controls_missing`、`page_source`、`page_source_truncated`；reportRefs 加 kind `device_session`（只作链接）。
- 删去的第一版新增物：`acquireMs`；`session_closed` 的原因枚举；`device_session` 的首步挂载与解析契约。

## 7. 两轮审查发现的处置对照（第一轮）

| 发现 | 处置 |
|---|---|
| 自审 #1 `scope_started` 时机 | 采纳，定义为执行就绪，血缘改由 `session_opened` 承载（§1） |
| 自审 #2 执行前失败挂首步 | 采纳，`scope_done` 带 `status` 与 `errorType`，core 合成 SKIPPED（§1） |
| 自审 #3 超时对象错位 | 采纳，分层表加删除「step 预算」（§2） |
| 自审 #4 缺省 None | 前提被纠正；真问题以「plan 层按目标给缺省与下限、设备无不超时、完整覆盖与校验顺序」解决（§2） |
| 自审 #5 SIGTERM 安全点 | 采纳，释放优先、四阶段终结（§1） |
| 自审 #6 设备分钟载体 | 采纳载体，口径只报原生量（§1） |
| 自审 #7 服务商形态渗入 | 部分采纳：具名 `device_request`、筛选算法回 0051；`billing_method` 留 job（§5） |
| 自审 #8 接缝缺生命周期 | 采纳为顺序与失败契约（§4） |
| 自审 #9 iOS 地址核对每次 error | 采纳为 `requires` 声明加 `capability_unavailable`（§4） |
| 自审 #10 筛选规则 | 零候选采纳；版本改点分段族匹配；形态固定只取手机（§5） |
| 自审 #11 cookie 契约 | 采纳并扩为完整契约与负例清单，已 curl 与桌面实测（§3） |
| 自审 #12 令牌残留 | 部分采纳：残留面如实列全；不删会话；`jobs/*.json` 不需 0600（§3） |
| 自审 #13 账号级资源不入库 | 否决，只补跨账号指引（§5） |
| 自审 #14 开发内循环 | 留观察；0050 背景补已知成本与重议条件 |
| 自审 #15 Python 签名定死 | 否决（原文已是「签名随实现定」） |
| 自审 #16 实施期杂项 | 保留承诺期限与 1.4 GB 估算现在改（§5），其余实施期 |
| Codex 第一轮遗漏 1 到 6 | 全部采纳（§1 收尾与退出语义；§2 传输层重试；§4 scenario 复位、evidence、上下文身份；§3 令牌载体与映射规则） |

## 8. owner 拍板项（2026-10-15 owner 接受全部推荐项，以下「推荐」即已定；备选只作被拒方案记录）

1. **隧道令牌载体**：推荐「definition 承载、worker 每 scope 预热一次」；备选「令牌进 step 文本」。
2. **设备分钟口径**：推荐只报原生量；备选按平台常量估计计费量。
3. **新错误类别范围**：推荐五个；备选再加 `device_setup_failed` 与 `device_unresponsive`。
4. **设备缺省墙钟**：推荐「获取预算 + 900 秒，下限获取预算 + 180 秒，低于下限以退出码 2 拒绝，设备 scope 无不超时」，数值实测后校准；备选保持 300 秒只加提示。
5. **版本族内的选择**：推荐先可用后版本高；备选只在最高版本内选。
6. **Device Farm 会话结果清扫命令**：推荐 1.5 只写文档与 `doctor` 列举。
7. **deploy 一律建立 Device Farm 项目**：推荐一律建立、无权限时警告并跳过。
8. **evidence 控件摘要范围**：推荐只在 failed / error step 采集。

## 9. 实测项与结论

**已完成（2026-10-15；设备均为 Device Farm 公共真机：Redmi Note 13 / Android 15、iPhone 7 / iOS 15.8、iPhone 16 / iOS 18.6、iPhone 17 Pro / iOS 26.3）**：
- **边缘契约**：ngrok 免费层每个策略至多 5 条规则（第 6 条报 ERR_NGROK_2264），`remove-headers` 为付费功能（ERR_NGROK_2263）；4 条规则的策略下 curl 矩阵 16 项全部符合 §3 预期；浏览器 UA 不带跳过头的请求直接得到上游页面、无警告页；上游日志不含 `.well-known` 请求。
- **桌面 Chromium（Playwright）闭环**：预热 200 且标题 READY；cookie `__Host-` 前缀被接受，httpOnly、secure、SameSite None、会话 cookie；业务页 200 且 cookie 到达上游；错令牌 401 页；之后业务页仍 200；从第三方站点提交的跨站 POST 到达上游且带 cookie；`pushState` 正常。
- **四台真机的预热闭环**：预热标记 READY 在原生控件树中 1 到 2 秒内读到（iOS 26 经 deepLink 0.8 秒；Android 经 `url` 约 2 秒）；业务页 INDEX 且 cookie 到达上游；错令牌 AUTH REQUIRED、之后业务页仍放行；四台都没有出现 ngrok 警告页。跨站 POST 回跳带 cookie：Android Chrome、iOS 15.8、iOS 18.6 通过（iOS 26 无可用网页上下文、无法从第三方页面提交表单，未测）。切到桌面再切回后 cookie 保留：iOS 15.8 与 18.6 通过；Android 两次都没有读到业务页标记（切回后页面源未更新，是探针观测问题而非 cookie 结论，未判定）。
- **导航路线**：iOS 15.8 上 `mobile: deepLink` 不受支持（「当前 Xcode SDK 不支持打开地址」），`url` 路线通过；iOS 18.6 上先 deepLink 再用网页上下文，网页命令全部挂到 120 秒超时并重试三次，改走 `url` 全部通过；iOS 26.3 网页上下文列得出、切得进、命令挂住，只能走 deepLink。一条网页命令挂住会阻塞同一客户端上的后续命令（「因上一请求过久而超时」），所以探测用的只读命令必须用自己带短超时的客户端实例发出，`Promise.race` 式的放弃不能解除阻塞。
- **网页上下文身份**：`mobile: getContexts` 在 iOS 15.8 与 18.6 上返回每个 WEBVIEW 的标题与地址；`target=_blank` 的脚本点击后仍只有一个 WEBVIEW（Android 始终只有一个 CHROMIUM），多候选形态本轮未复现。
- **Midscene 1.15.1 对中止的行为**（假界面，两种模式各一次）：首个动作抛「结果未知」并置 `abortSignal` 后，`aiAct` 在 15 毫秒内以「task runner is in error state」拒绝，之后零动作、零截图；放行模式同样零动作。
- **webdriver 10.0.2 与 Appium（Android）**：同一会话两个客户端实例各自的 `connectionRetryTimeout` 各自生效（3 秒实例 3.0 秒超时，缺省实例 14.2 秒完成同一慢导航）；`pageLoad` 设 3 秒，10 秒慢页在 14.6 秒后才报 `timeout`，会话仍可用；`newCommandTimeout` 15 秒下 25 秒的长命令正常完成、随后空闲 20 秒后 `invalid session id`，远程访问会话仍 RUNNING，重新 newSession 17 秒成功；newSession 客户端 2 秒超时后立即与 75 秒后 `GET /sessions` 都为空，服务端无残留会话（`GET /appium/sessions` 在该 Appium 版本返回 500）；第一次运行时进程在该超时后直接退出、第二次未复现（§2 的进程级兜底由此而来）。
- **IAM 策略模拟器**对 §5 权限表：`ListDevices` 于 `*` 允许；`GetDevice` 允许；`CreateRemoteAccessSession` 于本项目加 `device:*` 允许、于其他项目隐式拒绝；会话 Get 于本项目前缀允许、于其他项目拒绝；`ListRemoteAccessSessions` 于本项目允许；未授予的 `DeleteRemoteAccessSession` 拒绝。真实角色闭环仍需建测试角色（实施前置）。

- **会话释放（Android，两条同名会话并行，单次）**：成功返回的 Create 在 1 秒内按名列举已见两条（名字不唯一，并行创建都成功；256 字符接受、257 字符拒绝）；排队中撤回：Stop 0.6 秒返回 STOPPING，0.8 秒到 COMPLETED，返回体与 Get 都没有 `deviceMinutes` 字段（只能说字段缺失，是否计费以账单为准）；RUNNING 后并行 Stop 各约 0.2 秒返回、返回体带 `status: STOPPING`，Get 0.2 秒；重复 Stop 报 ArgumentException；Stop 之后 `deleteSession` 报 UND_ERR_CLOSED 且错误文本带整条带签名的端点地址（0051 决策 11 的脱敏对象）；先 `deleteSession` 再 Stop 的会话 52 秒到 COMPLETED、计 2.16 分钟，只 Stop 的会话 73 秒到 COMPLETED、计 2.48 分钟，两者都产出 Video.mp4、Appium 服务端日志、Logcat 与 TCP dump 共 7 个文件——这支持 SIGTERM 路径优先 Stop，不作为所有平台产物无差异的保证。
- **webdriver 10.0.2 与 Appium（iOS 18.6 Safari）**：双实例超时各自生效（3 秒实例 3.0 秒超时，缺省实例 9.2 秒完成）；`pageLoad` 设置不被反映（读回只有 `command` 与 `implicit`），`url` 对 10 秒慢页在 3.2 秒返回而页面未加载完；`newCommandTimeout` 15 秒下 25 秒长命令完成、空闲 20 秒后 `invalid session id`，远程访问会话仍 RUNNING，重新 newSession 5.6 秒；newSession 客户端 2 秒超时后，立即与 75 秒后两个时点 `GET /sessions` 均为空（两平台相同；只说明这两个时点无残留，不说明客户端超时会取消服务端创建）；无未处理异步错误。

**定稿前仍待完成**：
1. **终结真值表的桌面演算与双路径对拍**：按 §1.2 的事件矩阵写出两条归约路径的期望输出，确认无一行互斥；实施时转为护栏测试。这是唯一一项不需要真机的待办，在改写 ADR 0024 与 0034 时同步完成。

**实施期**：双路径对拍的事件矩阵加「先判 abort、收尾期间 deadline 才到仍为 abort」与「无 ARN 的未知 Create 加取消」两行；命令守卫对缓存的元素句柄、提取出的方法与晚到回调的覆盖；iOS 26 上「探测超时 → 恢复原生上下文 → deepLink → READY」整链路；预热验收实际触发拒收 cookie、校验 401、请求失败三个分支；计费起点与排队是否计费、`deviceMinutes` 是否实时累计；claim 到进入设备解析的启动开销；真实设备 scope 的执行耗时分布（校准 900 与 180）；控件摘要与 page source 的采集耗时与字节量；`ListDevices` 的 os 字段格式与 formFactor 取值；UNMETERED 无槽位时 Create 的行为；项目名唯一性与按名找回；S3 同键 CopyObject 刷新后过期是否重新计时；前缀 `ListBucket` 下 HeadObject 缺失键是否稳定 404；`ListRemoteAccessSessions` 返回体是否带签名端点；CloudTrail 的 RunTask 记录是否含 `containerOverrides`；旧执行的晚到命令与事件在下一 scenario 开始之后的表现（命令守卫的实测）。

## 10. 改动落点与次序

逐句点名改写的清单在动笔时按「被反转句子 → 新规则 → 改写位置 → Status 反向链」做差集。已识别的落点：

1. **0051 整篇重写**（决策 1 到 13 全部触及，新增「设备解析」决策，被拒方案同步），连同 0024（事件集、配对规则、成本信封、`sessionId`、Job 输入、类别集）、0028（三处加法）、0034（机制二 `exit==0` 一行、「job timeout」节、flag 承诺、超时后有界读事件）、0049（决策 4 到 7、`requires` 键、预热键）、0031（决定一、三、六）、0037（决策 6 闭集、决策 7 的兼容性论证句与 definition 格式版本）。
2. **隧道**：0051 决策 11、13；0035 决策 1、2、4、5 与不变量、Status 头双向；0052 决策 6；0048 决策 8；0037 决策 4 的 env 清单；CONTEXT.md「隧道暴露」。
3. **运行期语义**：0019 `@scope` 澄清、`@timeout` 设备缺省与 Status 头；0042 决策一、二、四的设备例外；0048 决策 2、6、7；0050 决策 1、2、4；0052 决策 2、5、7；CONTEXT.md「能力探测」「step 证据」。
4. **边界与配置**：0048 决策 3；0053 决策 3、4、6；0052 决策 3；0033 权限表与 region 例外；CONTEXT.md 三条新词与「远程访问会话」。
5. `docs/internals/cli-json-contract.md` 加法扩展；journey 0013 的「实施期要核的点」吸收 §9 实施期清单；本文删除。

## 11. 第二轮复核（对第一版）的处置

| Codex 意见 | 处置 |
|---|---|
| 必须改 1 终结谓词、timeout 与 abort 优先级 | §1.2 真值表；`stop_reason`；点名改写 0034 机制二 |
| 必须改 2 「同版本闸门」不成立 | §1.4 改为 definition 格式版本加如实写明的不受支持组合（第三轮再改） |
| 必须改 3 孤儿防护漏最后一次失败与取消 | §1.3 终结四阶段 |
| 必须改 4 停止后只收 closed；closed 基数 | §1.2、§1.1 |
| 必须改 5 释放预算漏算补查与并行 | §1.3 释放阶段预算（第三轮再补终结核对阶段） |
| 必须改 6 显式正值的覆盖规则缺失 | §2 覆盖与校验顺序（第三轮补非正值） |
| 必须改 7 未启用设备支持与必填 ARN 互斥 | §5 提交时退 2 |
| 必须改 8 预热无可执行判据；设备上无警告页绕过 | §3 三种可见结果；警告页实测（第三轮补归因） |
| 必须改 9 Midscene 计数事实；只读重试与预热要原位写进 0028 | §2、§3 |
| 必须改 10 计量字段无法填写 | §1.4 `observedS` 逐路径定义 |
| 必须改 11 IAM 不能全部收窄到项目 | §5 权限表按动作与资源类型 |
| 必须改 12 点名改写清单遗漏 | §1.2、§4、§5、§10 |
| 建议改 1 到 4 | 全部采纳（§1.1、§5、§3、§5） |
| 可简 1 到 3 | 全部采纳（§6） |
| 实测增补 | 采纳为 §9；S3 刷新验证留实施期 |

## 12. 第三轮复核（对第二版）的 7 项阻塞的处置

| 阻塞 | 核实 | 处置 |
|---|---|---|
| 1 终结判定与明细未分开；接力者直接落 `timed_out` 未纳入；在途明细规则悬空 | 属实（`detached._recover_timed_out_claims` 不发停只记超时；0031 只定义 job 级 aborted） | §1.2：`stop_reason` 定义为推进器判定；明细只依据完成事实、不被之后的停止撤销；在途明细显式规则写进 0031 |
| 2 「只有新 CLI 产设备 job」不能证明旧读端安全；0049 原文与「自检拒旧 worker」相反 | 属实（1.4 `status --wait` 可接力；旧反序列化丢字段；旧事件解析忽略新字段；0049 决策 7 原文） | §1.4：definition 格式版本；两条真实暴露路径如实写明，1.4 读端无法追加检查、列为不受支持组合；删除错误说法 |
| 3 终结 List 未纳入释放截止线 | 属实 | §1.3 四阶段各有绝对截止线，`min_grace_s` 重新推导 |
| 4 非正 flag 对混合目标 run 有两种合法实现 | 属实 | §2：非正值只表示非设备 scope 不超时，设备 scope 落目标缺省；下限校验只对 tag 与显式正值；校验顺序写死 |
| 5 预热拒绝可能不可观测；归 `network_error` 违反 0028 | 属实 | §3：三种可见结果（READY / DENIED / ERROR 加 AUTH REQUIRED）；DENIED 归 `precheck_failed`、无标记归 `engine_error`、不用退出码 80；0028「关键不变量」节相应加法 |
| 6 结果未知的闭锁未覆盖全部命令入口 | 属实（0050 向 handler 暴露 driver） | §2：会话级命令守卫代理，step 令牌加结果未知标志，覆盖 AI、导航、handler |
| 7 `device_session` 的链接与解析未取舍 | 属实 | §4：只作普通链接，`explain` 不解析，不新增 schema，0042 决策五与 0027 不动 |

## 13. 第四轮复核（对第三版）的处置与作者的独立判断

| Codex 第四轮意见 | 核实 | 处置 |
|---|---|---|
| 1 首次仲裁在 timeout 与 abort 同时成立时仍有两种实现；`_stop_all` 的落定位置未定 | 属实（`schedule.py` 两处顺序相反；`_stop_all` 批量中止） | §1.2：同一时刻两者成立取 `timeout`；`_stop_all` 在那一刻按同一规则逐 job 落定；无状态路径由推进器写退出记录时落定，重放不再仲裁 |
| 2 云端开发版本混搭可绕过预热、产生非空 PASSED | 属实（旧开发版 Lambda 丢预热字段；导航与地址核对在 401 页可通过） | §1.4：0035 加 definition 完整性不变量（隧道模式必带额外请求头与预热地址，缺一即 `precheck_failed`）；开发版本混搭本就不在 0037 的兼容承诺内，文档写明 |
| 3 取消与终结没有立即撤销执行令牌 | 属实（handler 在 `await` 后恢复可经原 driver 发命令） | §2：令牌在 step 结束、取消或进入终结时立即撤销；收尾调用走生命周期管理方自己的通道 |
| 4 未知 Create 在成功空命中与正常收尾时无确定处置 | 属实 | §1.3：待核尝试的生命周期（命中登记、或超过可见性窗口 W 且为空才消除）；正常收尾也执行终结核对；未消除即退出 1 |

**作者与 Codex 意见不一致、或作者自己仍存疑之处**（Codex 是同僚不是裁判，这些由作者负责）：

- **Midscene 重新规划会重复执行动作**（Codex 第二、三轮据源码推断）：实测不成立——适配器抛错并置 `abortSignal` 后 Midscene 立即结束 act、零动作。命令守卫因此不以这一点为理由，而以 handler 与晚到引用为理由保留；§2 措辞已改。
- **`newCommandTimeout` 的取值要对「命令执行期间是否计时」两种语义都安全**（第一版预算结点的设计）：Android 实测只计空闲，若 iOS 结果一致，⑧ 的 max 形式可以简化为「最长命令间空闲加余量」，少一条需要解释的保守项。等 iOS 结果。
- **`pageLoad` 作为慢页面的上界**（§2 分层表 ⑦）：Android 实测它晚了 11 秒才生效，所以单条命令的真实上界只能是客户端请求超时 ⑥；⑦ 降为「尽力而为、能早报就早报」。这是作者据实测对自己第二版条文的修正，不来自 Codex。
- **开发版本混搭的防护力度**：Codex 要求给出拒绝机制，作者的判断是「0037 已明确不承诺开发版本兼容」，为它新增机制属于为不受支持的组合付设计成本；只接受了零成本的完整性不变量（它同时能抓到真实的部署残缺），不再多做。
- **仍存疑**：终结四阶段加命令守卫加格式版本，三者让 worker 收尾与 core 读端各多了一层状态机。作者认为每一层都对应一个实测或代码核实过的故障（会话泄漏、晚到命令、旧读端误判），不是防御性堆叠；但实施时若发现任一层没有对应的护栏测试能触发它，应回头删层，而不是保留。
- **仍存疑**：`capability_unavailable` 是 step 级类别，只写进 `StepResult.error_type`，与现有 step 级归因同一处置、不另造 job 级映射（现有代码也没有 step 到 job 的自动提升）；它是 1.5 唯一一个「由注册元数据与探测结论共同决定」的类别，若 iOS 用户普遍改用 AI 断言核对落点，它可能很少出现。保留，等样本。

## 14. 第五轮复核（对第四版）的处置

| Codex 第五轮意见 | 核实 | 处置 |
|---|---|---|
| 缺版本戳的旧后端是独立于开发版本的暴露路径，完整性检查只把非空假绿变成空判定假绿 | 属实（0037 与 `compose` 对缺戳只警告，`push-worker` 放行） | §1.4：带设备目标或预热地址的 run 遇缺戳后端即退出码 2，其余 run 维持只警告 |
| W 加空命中不能证明未创建；一次 List 未处理分页；无 ARN 的取消路径没有待核事实的载体 | 属实（探针只观察了成功返回的 Create；List 带 `nextToken`；U 为空时提示不触发） | §1.1、§1.3：待核只由正面证据消除；核对含分页；终结时仍待核即发 `session_opened(origin: attempted, name)` 与 `session_closed(unconfirmed)`，配对键退回会话名，U 因此非空、提示自然触发 |
| `deviceMinutes` 缺失被写成不计费；跳过 `deleteSession` 与 newSession 无残留被过度推广 | 属实 | §9 三处收窄为观测到的事实 |
| §13 声称存在 step 到 job 的归因映射 | 属实（现有代码只写 `StepResult.error_type`） | §13 改为 step 级类别、不另造映射 |
| 对作者六条不一致与存疑的表态 | 六条全部接受作者判断（其中 `capability_unavailable` 一条附上述纠正） | 记录于此 |
| 实施中要盯住的风险 | 采纳 | 并入 §9 实施期：桌面演算补「先判 abort、收尾期间 deadline 才到仍为 abort」与「无 ARN 的未知 Create 加取消」两行；命令守卫覆盖缓存的元素句柄、提取出的方法与晚到回调；iOS 26 上「探测超时 → 恢复原生上下文 → deepLink → READY」整链路；预热验收实际触发拒收 cookie、校验 401、请求失败三个分支 |

## 15. 第六轮复核（对第五版）：共识

Codex 判定第五轮余下的两项都已闭合，`attempted` 事件加配对键回退会话名的机制可接受、没有净更简的替代；设计层面达成共识，进入 ADR 改写与实施。它列出的四项实施关注点并入 §9 实施期：缺戳闸门在 `run` / `submit` 提交前按完整 run 判断、覆盖混合目标；会话摘要投影中 `attempted` 不得擦掉已有的真实 ARN，展示与计量区分待核尝试与已证实的会话；终结阶段交叠或重入时 `attempted` 只发一对，真实会话按 ARN 去重；§9 的双路径对拍、失效引用守卫、iOS 26 完整恢复链路与预热三个负例按清单落实。

作者的结论与 Codex 一致：按本版改写 ADR 0048 到 0053 并同步修订 0019、0024、0028、0031、0033、0034、0035、0037、0042、0050 后实施，能满足「1.5 实现没有臭味、瑕疵，向优雅演进」的目标；剩余不确定性全部在 §9 实施期清单里，每项都有对应的护栏测试或真机验收。

