# 0049. worker 能力自述增键：`targets`、step 级 `targets` 与 `max_session_s`

> **Status:** Accepted（2026-10-15）——在 [0036](./0036-deterministic-capability-discovery.md) 决策 5 的能力自述对象上增键，`schema_version` 仍为 1；测试目标的声明与拒绝规则归 [0048](./0048-test-targets-device-and-ui-kind.md)。决策 4、5、7 的收尾与传递条文由 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 改写；决策 1、2 加 `requires` 与会话预热支持键。

## 背景与问题

1.5 起一个 scope 的测试目标由两个维度描述：device（desktop / android / ios）与 ui_kind（web / app），声明方式与 core 的处理见 [0048](./0048-test-targets-device-and-ui-kind.md)。core 要在执行前回答三件事，而答案只有 worker 知道：

1. **这个引擎的 worker 能不能执行这个目标**。Midscene 经 Appium 驱动 Device Farm 真机，Nova Act 只驱动 Playwright 浏览器；同一引擎的不同版本、不同镜像也可能不同。
2. **某条确定性 step 在这个目标上有没有实现**。一条 step 可以只注册了桌面浏览器的句柄（[0050](./0050-deterministic-step-handles-and-testing.md)），落到设备目标上就只能走 AI；feature 作者要在 plan 里看到这一点，而不是执行后才发现走了 AI。
3. **这个目标的单次会话最长能持续多久**。Device Farm 远程访问会话有不可调的 150 分钟上限、从创建时刻起算；job 墙钟预算超过它的 job 注定在中途失去设备，应在执行前拒绝。

[0036](./0036-deterministic-capability-discovery.md) 已立「worker 自述是唯一的能力来源、加键不加入口」，本 ADR 定这三个答案、确定性 step 的前提声明（`requires`）与会话预热支持以什么键、什么语义进入自述对象，以及 CLI 侧各消费点如何呈现。

## 决策

### 1. 不升 schema 版本，在 schema 1 上增键

自述对象的增量（未列出的键照旧）：

```jsonc
{
  "schema_version": 1,
  "targets": [
    {"device": "desktop", "ui_kinds": ["web"]},
    {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8880},
    {"device": "ios",     "ui_kinds": ["web", "app"], "max_session_s": 8880}
  ],
  "session_warmup": true,  // 会话预热支持键，取值为布尔
  "deterministic_steps": [
    {"pattern": "...", "description": "...", "example": "...",
     "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"]}]},
    {"pattern": "...", "description": "...", "example": "...",
     "targets": [{"device": "desktop", "ui_kinds": ["web"]},
                 {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]},
                 {"device": "ios",     "ui_kinds": ["web"], "requires": ["web_context"]}]}
  ]
}
```

（`max_session_s` 的数值仅作示意，真值见决策 4。）

- **step 级 `requires`**：`deterministic_steps[*].targets` 的条目可带可选的 `requires`（字符串数组），声明该句柄在这个目标上执行的运行期前提。1.5 只有一个取值 `web_context`（远程访问会话提供可用的网页上下文，探测规则归 [0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 5）。worker 在注册期按封闭集合校验取值；CLI 只核形态（字符串数组），未知取值不拒绝、在各视图中原样显示，以免 CLI 与 worker 的取值集合形成第二事实源。`requires` 不同的条目拆开列出、不聚合进同一条目，因为聚合后无法表达「同一 step 在桌面无前提、在设备上需要网页上下文」。
- **会话预热支持键**：顶层加布尔键 `session_warmup`，语义为「该 worker 支持隧道会话预热」（两个 worker 的键名常量由 engines/fixtures/tunnel-warmup.json 的 `capability_key` 对照钉住）；预热的流程与拒绝点归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13。
- **为什么不升版**：`schema_version` 是 worker↔core 协议版本（与 job 行的 `schemaVersion` 同一个数，[0024](./0024-worker-core-protocol.md)），只在协议出现不兼容变化时递增。上述各键都是新增，既有键 `min_grace_s`、`deterministic_steps` 的条目字段、`model_id` 的含义一律不变；顶层 `targets` 虽为必有键，但 1.5 是第一个带它的版本、1.5 之前的 worker 不在支持范围内，schema 1 的契约就是「必有 `targets`」，升版没有要区分的对象。现行契约校验只核已知键、容忍多余键，故旧 CLI 读新 worker 不受影响；新 CLI 读缺 `targets` 的旧 worker 按版本不一致拒绝（决策 2）。
- **校验位置不变**：新键与旧键一样，在 CLI 侧唯一的自述契约校验处核形态（device 取值属于 desktop / android / ios，`ui_kinds` 非空且属于 web / app，desktop 只允许 web，`max_session_s` 为正有限数，`requires` 为字符串数组，预热键为布尔；唯一性：顶层 `targets` 的 device 不重复（`max_session_s` 按 device 只能有一个值，取最小或取第一条之类的容忍规则会让 CLI 预检与 worker 自检各写一套消歧逻辑），任何位置的 `ui_kinds` 与 `requires` 元素不重复，step 级条目不出现 device、`ui_kinds`、`requires` 三项完全相同的重复），不合契约照旧 fail-loud、不写缓存，不散到 plan、doctor、`list-deterministic` 各自校验。
- **不做**：不新增自述入口，不为目标另开 flag；不把「目标到句柄种类」的映射放进协议（desktop 对应 playwright 句柄、设备对应 webdriver 句柄是 [0050](./0050-deterministic-step-handles-and-testing.md) 的注册规则，消费方不需要据此做判断）。

### 2. 顶层 `targets` 必有；step 级缺键即「只在 desktop / web 上有实现」

- 顶层 `targets` 是必有键：CLI 的契约校验对缺键按「worker 与命令行工具版本不一致」fail-loud，不再把缺键兜成「只有 desktop / web」。1.5 的两个 worker 都显式写出 `targets`；1.5 之前的 worker 不在支持范围内，与 definition 的结构版本（[0037](./0037-distribution-and-packaging.md) 决策 7）和 job 行的 `schemaVersion`（[0024](./0024-worker-core-protocol.md)）同一取向：读端只认当前契约、不为旧写端留缺省。引擎能力矩阵文档的真值集取的是显式值（决策 8）。
- step 条目缺 `targets`：该 step 只在 desktop / web 上有实现。这是使用方 step 未声明目标时的缺省（注册面见 [0050](./0050-deterministic-step-handles-and-testing.md)），不是版本兼容路径，故保留。
- 缺 `max_session_s`：该 worker 对此目标不施加会话级上限，job 只受墙钟预算约束。1.5 的 desktop 条目不带此键（浏览器会话的现有超时行为不在本 ADR 范围内）。
- 缺 `requires`：该句柄在此目标上没有运行期前提。缺会话预热支持键：该 worker 不支持隧道会话预热，本机后端在 `--expose-local` 下于执行前预检中拒绝（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13）。
- **不做**：不把缺 `targets` 解释为「支持全部目标」、「未知、放行」或「只有桌面」。前两者会让旧镜像接到设备 job 或把能力判断推迟到会话建立之后，后者是为不在支持范围内的旧 worker 留的兼容分支。

### 3. step 实际可用目标是句柄声明与 worker `targets` 的交集

- worker 在 `deterministic_steps[*].targets` 里**原样**报出注册时声明的目标（由句柄种类与 `uiKinds`、`devices` 过滤推出，规则归 [0050](./0050-deterministic-step-handles-and-testing.md)），不预先与自己的顶层 `targets` 求交。
- 交集由 CLI 一侧算：实现与契约校验住同一个组合根模块、以纯函数提供（消费点调用时算，不改写缓存的自述对象），plan、`list-deterministic`、doctor 只消费结果、不各自求交或补缺省值。交集是两份结构化声明的集合运算，不涉及 step 文本，与 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「匹配放 worker」的红线相容。交集结果保留每个条目的 `requires`；同一 device 与 ui_kind 只是 `requires` 不同的条目各自成条、不合并（只适用于 step 级；顶层 `targets` 按 device 唯一，见决策 1）。
- **为什么不由 worker 报交集**：声明了但 worker 不支持的目标是测试开发需要看见的信息。典型是 Python steps 目录里写了 webdriver 句柄，而 Nova Act worker 没有设备目标；若 worker 先求交，这条句柄在任何视图里都消失，测试开发无从得知它永远不会被调用。
- `--match-steps` 的输入加关键字、输出加「命中但关键字不符」一态（[0036](./0036-deterministic-capability-discovery.md)、[0050](./0050-deterministic-step-handles-and-testing.md) 决策 1），其余不变：plan 用命中结果里的 `pattern` 关联自述清单中该条目的交集目标，再按 scope 的目标标注；关键字不符的 step 标注为写法错误。跨 step 的命中冲突仍按 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 的模式冲突规则处理，与目标无关；命中的条目在该 scope 目标上没有句柄时，这条 step 标注为走 AI，不顺延到下一条能匹配的 pattern（[0050](./0050-deterministic-step-handles-and-testing.md) 决策 1）。顺延会让同一文本在不同目标上执行语义不同的实现，测试开发从 step 文本看不出实际调用的是哪一条。

### 4. `max_session_s`：目标的单次会话上限，由 worker 从自己的常量算出

- 语义：worker 在该目标上能持有一次会话的最长秒数，计时起点为会话创建时刻（Device Farm 为 CreateRemoteAccessSession 的时刻；计费口径以账单为准，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 7）。
- 取值：Device Farm 的 150 分钟上限减去 worker 收尾所需的余量（deleteSession 与 StopRemoteAccessSession 等释放步骤排在 `scope_done` 之前，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 5），由 worker 内的预算常量算出、不在 CLI 或文档里另写字面量；与 `min_grace_s` 由收尾预算常量算出是同一做法（[0036](./0036-deterministic-capability-discovery.md) 决策 5）。
- 消费：job 墙钟预算（自推进器 claim 这个 job 起算，[0034](./0034-detached-batch-reconciler.md)）超过该目标的 `max_session_s` 时，本机后端在执行前预检里拒绝（[0048](./0048-test-targets-device-and-ui-kind.md)），云端后端由 worker 在建会话前读取 Job 输入携带的 `timeoutS`、与该目标的 `max_session_s` 比较作自检拒绝（决策 7）。设备 scope 的缺省墙钟由 core 的 plan 层给出（[0034](./0034-detached-batch-reconciler.md)「job timeout」节），显式值与 tag 的下限校验也在 core；获取预算与会话生命周期归 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2。会话在 job 启动之后才创建，故墙钟不超过 `max_session_s` 即保证会话寿命不超过上限，不必为设备另立起算点。取设备的开销（创建到 Appium 可用，约 1 到 2.5 分钟）计入墙钟；停止到 COMPLETED 的时间发生在 job 结束之后，只计设备分钟、不占墙钟。
- **按目标给值，不做顶层单值**：同一 worker 的桌面与远程访问会话上限来源不同，顶层单值只能取最小值，会把桌面 job 也限制在设备的上限之内。

### 5. `min_grace_s` 保持顶层单值

- 设备收尾按 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 5 的终结四阶段推导：等在途 Create 10 秒、终结核对 5 秒、释放阶段 25 秒、中断兜底上传 10 秒、排空 6 秒，加事件写出与余量，约 64 秒，低于 Fargate `stopTimeout` 的 120 秒硬上限（[0024](./0024-worker-core-protocol.md)「引擎自报下限」条、[0032](./0032-fargate-execution-environment.md)）；各段上限以网络退化实测校准后定数。worker 不等会话到 COMPLETED。
- 四个阶段的上限与现有各段一起计入 Midscene worker 收尾预算之和，由同一组常量派生，不另设设备专用下限。Midscene 的下限由约 31 秒升到约 64 秒：这不算「本机默认宽限显著提高」——本机宽限只是 SIGTERM 之后等待收尾的上界，worker 收尾完即退出，正常路径与桌面 run 的耗时不受影响；真正的代价只在收尾挂住时多等约半分钟，低于 120 秒的硬顶才是判据。
- **重议条件**：设备收尾的预算之和使 Midscene 的下限超过 120 秒（云端 doctor 的宽限比对会变成可选能力缺失），或本机默认宽限的提高开始影响正常路径的耗时。届时把该键改为按 device 取值的对象，并按 [0036](./0036-deterministic-capability-discovery.md) 的规则递增 `schema_version`，因为那是既有键的语义变化。

### 6. 各消费点的呈现

- **plan**：每个 job 带目标；命中确定性 step 但交集不含该 scope 目标的 step，标注为走 AI，并写明原因（「这条确定性 step 在 Android 网页上没有实现，将由 AI 执行」）。交集条目带 `requires` 时 plan 写明前提（「需要网页上下文；设备不提供时记为错误」）；运行期网页上下文不可用时这类 step 记 error、类别 `capability_unavailable`、不转 AI（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4），探测规则归 [0048](./0048-test-targets-device-and-ui-kind.md) 与 [0052](./0052-appium-interface-adapter-and-platform-differences.md)。
- **`list-deterministic`**：文本表格增加「目标」列，列出交集目标；声明了但该引擎不支持的目标单独注明（「声明了 Android 应用，此引擎不支持」）。文本表格的目标列对带 `requires` 的条目附前提标注（如「需要网页上下文」）。`--json` 每项保留 worker 原样报出的 `targets`，另加 CLI 算出的 `available_targets`（条目保留 `requires`），两者分开，机读消费方无需自己求交；doctor 的目标清单不展示 `requires`。
- **doctor**：engines 段为每个可用引擎增加一行目标清单（required=False，纯展示），带 `max_session_s` 的目标附上分钟数；与模型行同源于同一次自述。
- **不做**：不按目标过滤 `list-deterministic` 的输出（目标列已足够、清单规模小），不在 doctor 里把「不支持设备」当作失败。

### 7. 云端 worker 在建会话前按自己的 `targets` 自检

- 云端后端的提交机器不必装 worker（[0037](./0037-distribution-and-packaging.md) 决策 3），提交机器上的执行前预检无法取得云端镜像的自述，目标判断只能由 worker 侧完成。故 worker 在 job 开始、建立任何会话（浏览器会话或远程访问会话）之前，用与自述同一份 `targets` 核对 Job 携带的目标与墙钟预算（`timeoutS`）：目标不在 `targets` 里，或墙钟预算超过该目标的 `max_session_s`，即记 `precheck_failed`、零会话费用退出。本机后端也执行同一自检，作为执行前预检之外的第二道防线。
- 传递方式沿用 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4 对执行前失败的统一规则：worker 发 `scope_done{status: error, errorType: precheck_failed, message}`，不发 `scope_started`，不发任何 scenario 或 step 事件。错误类别的定义与处置语义（改用例或换测试包）同归 0051。
- 消息形态（产品语言，不带内部指代）：「这个 worker 不支持在 iOS 应用上执行测试（它支持：桌面网页）。请改用支持该目标的引擎，或使用与命令行工具同版本的 worker 镜像。」
- 防止「旧镜像把设备 job 当桌面执行」靠两层：镜像按 CLI 版本解析（[0038](./0038-worker-image-delivery.md) 的 `<版本>-<variant>` tag），1.5 的 CLI 只会解析到 1.5 的镜像；自检覆盖其余情形，例如 variant 基于不一致的基础镜像构建。worker 自检的第一步是核 job 行的 `schemaVersion`（[0024](./0024-worker-core-protocol.md)），命令行工具与 worker 版本不一致时在建会话前以 `precheck_failed` 报出；1.5 之前的 worker 不认识这个键、自检对它无效，这一情形只由版本解析保证；缺版本戳的旧后端见 [0037](./0037-distribution-and-packaging.md) 决策 7 的例外。

### 8. 引擎能力矩阵文档与差集护栏

- user guide 新增 `engines.md`：引擎 × 目标 × 确定性句柄种类 × 默认模型 × 计价公式（只写公式，不写绝对金额，金额随 AWS 定价变动）。
- 真值集是两个 worker 在无环境变量覆盖时的能力自述：目标列对 `targets`，默认模型列对 `model_id`，句柄种类列由目标按 [0050](./0050-deterministic-step-handles-and-testing.md) 的固定规则推出。差集测试逐行对照文档表格与真值集，多一行、少一行、值不符都失败；计价公式列没有机读真值，靠 ADR 与发版文档校准。
- 读者是人，矩阵是派生视图，权威在自述与本 ADR；新增目标时先改 worker 自述，测试会指出文档缺行。

### 9. Nova Act 没有设备路径

Nova Act SDK 驱动的是 Playwright 浏览器（本机或 AgentCore 浏览器会话），不提供 Appium 或真机接入。1.5 的 Nova Act worker 自述 `targets` 只含 desktop / web，设备目标路由到 Nova Act（含它作缺省引擎的情形）时，本机后端由 [0048](./0048-test-targets-device-and-ui-kind.md) 在 plan 与执行前预检中以 FeatureContractError 拒绝，云端后端由 worker 自检记 `precheck_failed`（决策 7）。这一事实由自述表达、由能力矩阵揭示，不在 CLI 里按引擎名硬编码。

## 实测依据

据 Android 与 iOS 真机上逐项的会话生命周期实测：

| 量 | 实测 | 用于 |
|---|---|---|
| 远程访问会话上限的计时起点 | 创建后约 150.4 分钟命令开始报会话关闭，计费 150.29 分钟，从创建算、不从 RUNNING 算 | 决策 4：上限从创建起算 |
| 创建到 RUNNING | Android 51 到 92 秒、iOS 61 到 82 秒（排队中撤回的会话返回体与 Get 都没有 `deviceMinutes` 字段，是否计费以账单为准） | 决策 4：会话在 job 启动之后创建，墙钟覆盖这段开销 |
| Appium 建连 | Android 13 到 26 秒；新 iPhone 5 到 17 秒、老 iPhone 65 秒（老机型上 WebDriverAgent 启动慢） | 同上 |
| deleteSession | 约 0.9 秒；跳过 deleteSession 只 Stop 的会话同样产出录像与日志（Android 两会话） | 决策 5：SIGTERM 路径不调 deleteSession 不损失产物 |
| StopRemoteAccessSession | 调用即时返回；到 COMPLETED 另需 Android 52 到 85 秒、iOS 超过 2 分钟（最长约 150 秒），只计设备分钟、不占墙钟，worker 不必等待 | 决策 4、决策 5 |
| Midscene 现有 `min_grace_s` | 约 31 秒，对比 Fargate `stopTimeout` 硬顶 120 秒 | 决策 5：现有下限的基线；设备收尾按 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 5 推导后升到约 64 秒，仍低于硬顶 |

## 被拒方案（护栏）

- **升到协议版本 2**：各键都是新增，1.5 之前的 worker 不在支持范围内，升版没有要区分的对象、只会迫使 CLI 维护两套解析分支；不符合「只在协议出现不兼容变化时递增」的规则。缺 `targets` 的 worker 由契约校验按版本不一致拒绝，不需要版本号来识别。
- **`min_grace_s` 取各目标最大值或立即拆成按设备的对象**：按终结四阶段推导的设备收尾约 64 秒，仍低于 120 秒硬上限，拆分只增加协议面而不改变任何下限的结论；拆分的条件写在决策 5 的重议条件里。
- **worker 只报交集后的 step 目标**：声明了但不受支持的句柄在所有视图中消失，测试开发得不到「这条句柄永远不会被调用」的信号（决策 3）。
- **CLI 按引擎名硬编码目标支持表**（如「novaact 只有桌面」）：形成自述之外的第二事实源，worker 增减目标时 CLI 静默漂移；与 [0036](./0036-deterministic-capability-discovery.md) 拒绝外置清单文件同理。
- **云端提交时由 CLI 启动镜像查询自述**：提交机器不必装容器引擎与 worker，为一次目标判断引入镜像拉取违背云端后端的前提；worker 侧自检在建会话前完成，同样零会话费用（决策 7）。
- **`--match-steps` 增加目标入参、由 worker 按目标回答**：改动查询协议的输入形态，而 plan 用 `pattern` 关联自述清单即可得到同样结论（决策 3）。

## 边界与互链

- 目标的声明（`@device`、`@app`）、冲突规则、FeatureContractError 的拒绝与 plan 的远程访问会话数：[0048](./0048-test-targets-device-and-ui-kind.md)。
- 句柄种类、`uiKinds` 与 `devices` 过滤、step 级 `targets` 如何从注册推出、命中条目在目标上无句柄时的处理：[0050](./0050-deterministic-step-handles-and-testing.md)。
- 会话的获取预算、`precheck_failed`、`acquire_timeout`、`session_lost`、`release_failed` 等错误类别、执行前失败经 `scope_done` 的传递规则、终结四阶段与收尾次序、会话预热：[0051](./0051-device-session-lifecycle-and-app-distribution.md)；设备 scope 的缺省墙钟与下限校验：[0034](./0034-detached-batch-reconciler.md)「job timeout」节。
- 运行期的能力探测（网页上下文可用性、输入路线等随会话变化的事实）不进自述：自述是不建会话、零费用的静态声明，探测结果写进 scope 诊断，归 [0052](./0052-appium-interface-adapter-and-platform-differences.md)。
- Job 携带目标与设备选择具体值、配置文件解析：[0048](./0048-test-targets-device-and-ui-kind.md)、[0053](./0053-project-config-file.md)。
- 自述入口本身、契约校验集中一处、两个非 job 入口：[0036](./0036-deterministic-capability-discovery.md)；grace 下限的消费与云端宽限比对：[0024](./0024-worker-core-protocol.md)；镜像按版本解析：[0038](./0038-worker-image-delivery.md)。
