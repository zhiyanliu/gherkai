# 一条确定性 step 的一生：从你写下正则到它在云端命中

> 本文讲**机制如何运转**（机制），不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。确定性 step 的机制被切在五个 ADR 里（注册表在 0022、可发现性在 0036、定制面在 0037、镜像交付在 0038、产物缺口在 0027），而人真正想问的是一条纵向问题——「我写下一个正则，它经过什么才在云端命中？」本文就是那条纵切面。

## 0. 全景：四段路，一张表

一条确定性 step 的一生只有四段，全程围绕**worker 进程里的那张注册表**转：

| 段 | 发生在哪 | 干了什么 |
|---|---|---|
| ① 写 | 你的项目 `steps/*.py`（Nova）/ `steps/*.mts`（Midscene） | `@deterministic(正则, description=…, example=…)` / `deterministic(正则, handler, {description, example})` |
| ② 装 | worker 进程启动的第一件事 | 内建脚手架先注册（模块 import 副作用），再按 env `GHERKAI_STEPS_DIR` 排序递归加载你的文件，叠进**同一张**表 |
| ③ 查 | `list-deterministic` / `plan` 标注 / `doctor` | 三个命令都 spawn 一次瞬时 worker（自述或 match 查询），问的就是这张表 |
| ④ 跑 | worker 派发每个 step | 先查这张表，命中即走你的 handler；不命中才落内建 URL 导航 / AI |

怎么写一个 handler（签名、`ctx` 能拿到什么、正则具名组怎么传参）**不在本文**——看使用者向的 [`docs/user-guide/writing-deterministic-steps.md`](../user-guide/writing-deterministic-steps.md)（Python 与 TypeScript 两侧并排）。本文讲的是这四段之间的接缝（handler 抛异常之后怎么落成判定，见 §1 的映射表）。

![你写的 step 与内建脚手架在 worker 启动时装成同一张注册表，查清单与逐 step 派发问的都是它](../diagrams/deterministic-steps-registry-overview.svg)

图注：三个入口各自的 flag 与输出形状见 §2 表。图上只有走注册表的那条路——派发的第 2 级（内建 URL 导航）不查注册表，故不在此图上（见 §1）。

> 权威：[ADR 0022](../adr/0022-bdd-runner-retired-core-parses-thin-worker.md)（注册表即扩展点）、[ADR 0020](../adr/0020-step-phrasing-default-ai-deterministic-scaffold.md)（默认 AI / 少数派显式、角色边界）、[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 4（`steps/` 定制面）。

## 1. 派发决策链：一条 step 文本进 worker 之后

worker 拿到的只有 `keyword` + 裸 `text`（+可选多行参数）。派发是**三级、短路、无优先级配置**（Nova `run_scope.py` `_run_step`、Midscene `run-scope.mts` `runStep`，同序）：

1. **确定性注册表**：`match(text)` / `matchDeterministic(text)`——用**裸 step 文本**扫全表（不 unquote、不拼多行参数）。命中一条 → 调 handler，**不投票**。
2. **内建 URL 导航**：文本里有引号包裹的 `https?://…`（Nova `_URL_IN_QUOTES` / Midscene `URL_IN_QUOTES`）→ 直接 `go_to_url` / `page.goto`，不问 AI。
3. **AI catch-all**：`Then` → 断言 + N 票；`When`/`Given` → 动作。

命中之后的判定映射（两引擎逐条对齐）：

| handler 的行为 | step 判定 | `error_type` |
|---|---|---|
| 正常返回 | `passed` | — |
| 抛 `AssertionError`（Nova）/ `DeterministicAssertion` 或 `name === "AssertionError"`（Midscene） | `failed` | `assertion_failed` |
| 抛其它异常（含 Nova 的「handler 是 async」→ `TypeError`） | `error` | `engine_error`；两侧都先过瞬时网络白名单（Nova `_classify_act_error` → `_is_transient_network`、Midscene `isTransientNetwork`），命中则细分 `network_error`（细分口径见 [`verdict-model.md`](./verdict-model.md) §3b） |
| 一条 step 命中多条模式 → `DeterministicConflict` | `error` | 同上，冲突模式清单在 `message` 里 |

两处易踩的机制事实：**匹配是未锚定的 `search` / `exec`**（子串匹配，不是整句 `fullmatch`），所以模式写松了既容易误命中、也容易撞出冲突；**第 2 级的 URL 导航不在注册表里**，故它既不出现在 `list-deterministic` 清单、也不会被 `plan` 标注（probe 只问注册表，见 §2），跑起来却确实没花 AI 的钱。

**匹配面只有 worker 一份**：CLI 与 `core` 不持有任何 step 正则——`core` 只发裸 step 文本，命中与否全在 worker 的表里判（此项分工的理由见本节末权威行 ADR 0022「匹配放 worker，不放核心」条）。随之而来的硬事实是两侧正则方言不同（Python `(?P<n>)` vs JS `(?<n>)`），CLI 侧任何「复刻一份匹配」的实现都会在某天对真跑撒谎。

> 权威：[ADR 0022](../adr/0022-bdd-runner-retired-core-parses-thin-worker.md)「设计要点」节「匹配放 worker，不放核心」条与冲突规则、[ADR 0020](../adr/0020-step-phrasing-default-ai-deterministic-scaffold.md) 决定 3（URL 形态自动分流）、[ADR 0024](../adr/0024-worker-core-protocol.md)（worker 收到的 step 形态）。判定语义（`failed` vs `error`、votes）见 [`verdict-model.md`](./verdict-model.md)。

## 2. 三个入口，一张表：为什么清单、标注、真跑不可能分叉

同一个 worker 二进制有三个入口，全部在 `main()` 里**先加载 steps 目录、再分流**（Nova `run_scope.main()` 顶部；Midscene `run-scope.mts` `main()` 的 `await loadUserSteps()`）——加载的位置本身就是契约：

| 入口 | 谁用 | worker 干什么 |
|---|---|---|
| `--capabilities`（自述） | `gherkai list-deterministic`、`doctor` 的 `steps.load.<engine>` 项、`run` 的本机前置（同一次 spawn 兼定 grace 下限）、`doctor --backend cloud` 比对云端停止宽限 | 一个 JSON 对象即退：`deterministic_steps`（`list_registry()` / `listRegistry()`，每项 `pattern` / `description` / `example`）+ `min_grace_s` + `engine` / `schema_version`；先加载 steps 目录，加载失败同样响亮 |
| `--match-steps`（查询） | `gherkai plan` 的派发标注 | stdin 收 step 文本数组 → `match_batch` / `matchBatch` → 一行 JSON 即退 |
| job 模式（无 flag） | `run` / `submit` 真跑 | 建会话、按 §1 派发 |

不可能分叉的两道结构保证：

- **同一张表**：内建脚手架（Nova `deterministic_steps.py` / Midscene `deterministic.steps.mts`）靠模块顶层 import 的副作用注册，你的 `steps/` 靠 `load_user_steps` / `loadUserSteps` 注册，两者写进的是同一个 `_REGISTRY` / `REGISTRY`；三个入口都在加载之后才分流。所以清单里有的、`plan` 标的、真跑派发的，是同一份真值——**没有第二事实源可漂移**（这也是「外置清单文件」被拒的理由，见 ADR 0036 被拒方案）。
- **同一个扫描面**：`match()` 与 `match_batch()` 共用 `_hits()`（Nova）、`match()` 与 `matchBatch()` 共用 `scan()`（Midscene）。两个消费者只在「命中数怎么处置」上分叉（真跑抛 `DeterministicConflict`，预检返回结构化 `{"conflict": [...]}`），匹配语义本身只有一份实现。

`plan` 因此仍然是**零 AWS、零花费、零副作用**，但它确实会起进程：CLI 按引擎分组 step 文本，每个引擎至多 spawn 一次瞬时本地 worker（`compose.match_deterministic` → `compose._ask_worker`，带 `timeout_s` 预算，默认值见 code）。自述入口不建浏览器会话、不碰 AWS、秒级返回——所以「plan 不花钱」的承诺没破，破的只是早期那句「plan 不起 worker」。

文本视图只标少数派：命中标 `← 确定性: <description>`、冲突标 `← ⚠`，走 AI 的**不标**（噪声控制，`render.py` `_dispatch_hint`）。`--json` 的 `deterministic` 键是三态（`null` / 命中 / `conflict`）、且整批省略也有含义——字段级语义见 [`cli-json-contract.md`](./cli-json-contract.md)，本文不重复。冲突在 `plan` 只是 ⚠ + stderr 警告，**退出码仍 0**（改措辞是 feature 作者能做的，修注册表不是）。

> 权威：[ADR 0036](../adr/0036-deterministic-capability-discovery.md)（决策 1-5：元数据必填、清单是自述对象的一个键、CLI 子命令、plan 标注与降级、`--capabilities` 契约）、[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 4（自述入口与 job 模式同样先加载 steps 目录）。

## 3. 两个真值源、一个岔口：为什么「改了 steps，云端没变」是设计

同一件事（「这个 run 用哪套确定性 step」）在两个执行档里由**不同的载体**决定，岔口在提交那一刻：

| 档 | 真值源 | 解析规则与落点字段 |
|---|---|---|
| local（`--backend local`，含 `submit` 的后台推进） | 本机目录 | `--steps-dir` > env `GHERKAI_STEPS_DIR` > `./steps`（相对**提交时** CWD、存在才用），落 `RunMeta.steps_dir` |
| cloud（`--backend cloud`） | **variant 镜像里构建进去的 `/app/steps`** | 解析出各引擎的 task-def revision；`RunMeta.steps_dir` 不写 |

![local 档提交时解析一次目录、路径随定义走；cloud 档把 steps 构建进 variant 镜像，提交侧只解析镜像名](../diagrams/deterministic-steps-truth-sources.svg)

图注：图上那条「读回后注入」只发生在后台推进的两处；同步 `run` 与提交侧是同一个进程，直接用解析出的值、不读回。cloud 那条链在提交之前就完成：镜像由写 steps 的人按模板 build，推送与登记归部署方，两步都不在一次 run 的时间线上。提交侧解析 variant 时的存在性/一致性校验、两档各自的失败形态与提示，见下文与 §4 表。

local 侧三处宿主（同步 `run`、`submit` 的后台推进进程、`status --wait` 接力者，见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) §3 与 §4a）的 CWD 各不相同，所以**解析只能做一次**：谁再解析一次 `./steps`，同一个 run 就会用到两套 step。落点：后台两处读回 `meta.steps_dir`（`detached.build_local_reconcile`），同步 `run` 用提交侧那个值；注入与清同名在 `compose.build_engines` / `_scrubbed_environ`——**每个**宿主建 env 都先清掉自己 shell 里的同名 `GHERKAI_STEPS_DIR`（接力那台机器 export 过只是最易踩的一例），export 越不过 definition，worker 只认这一个 env、不猜 `./steps`。

cloud 侧的关键是**镜像是唯一载体**：你的 `steps/` 靠三行 Dockerfile（模板唯一真源在 [ADR 0038](../adr/0038-worker-image-delivery.md)「概念模型」节）构建进一个 **variant**，由部署方 `gherkai deploy push-worker` 推上去；镜像里已经设好与本机档**同一个** `GHERKAI_STEPS_DIR`，容器里的 worker 装的就是构建进去的那份。提交时 `compose.resolve_worker_variant` 只做三环存在性/一致性校验（三环各查什么、缺哪一环怎么报，见 [`cloud-backend-carriers.md`](./cloud-backend-carriers.md) §5）——**一个字节的 steps 内容都不看**。

由此两条对使用者最要紧的推论：

- **`--backend cloud` 下 `--steps-dir` 不生效**（`_resolve_steps_dir_for_backend`）：路径存在时只打一句提示、definition 里也不写这个字段——本机路径进不了容器；但**路径不是目录仍退 2**（那道校验排在清零之前，两档共用，见下 §4 表）。
- **「我改了 `steps/`，云端跑出来还是老样子」是设计而非 bug**（新写的 step 会静默落 AI、改过的 step 仍按镜像里的老版本跑）：提交侧不比对镜像里 steps 的新旧（那是替使用方判断），改完必须重新 build + `push-worker`。想确认云端那套是什么，唯一诚实的问法是对镜像里的 worker 问——不是对本机问。

variant / 默认指针 / revision / digest 这些载体本身（SSM 键、ECR tag、退休与清理）见 [`cloud-backend-carriers.md`](./cloud-backend-carriers.md) 与 [`docs/user-guide/cloud-backend.md`](../user-guide/cloud-backend.md)。

> 权威：[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 4（解析在组合根、随 definition 持久化、worker 只认 env；cloud 档 steps 构建进镜像）、[ADR 0038](../adr/0038-worker-image-delivery.md)（定制镜像模板、preflight variant 解析、「不比对 steps 内容」的不变量与被拒方案）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)（三个宿主与各自 CWD）。

## 4. 响亮地失败：症状 → 原因 → 怎么办

**本机档**这条链上所有「可能把确定性判定悄悄换成 AI」的口子都被焊成显式失败——因为静默降级的后果是**run 还可能「通过」**（假绿），是本项目最忌的形态。**cloud 档留了一处不焊**：提交侧只解析 variant、不看镜像里 steps 的内容（见 §3），所以本机新写或改了一条确定性 step、忘了重新 build + `push-worker` 就提交 cloud 时，镜像里查不到它 → 这一步静默落回 AI，没有任何显式失败；确认云端那套是什么只能对镜像里的 worker 问。

| 症状 | 原因 | 怎么办 |
|---|---|---|
| 注册时报「缺 description/example」 | 注册即暴露：元数据必填，缺了这条 step 不进能力清单、feature 作者发现不了它 | 补上一句说明 + 一条可抄的 step 文本 |
| worker 起来就非零退出、stderr 点名某个文件 | 目录里**任一**文件 import 失败（语法/依赖错） | 修那个文件；Nova 用 `EX_STEPS_LOAD`（=2）、Midscene 由 `bin.mts` 统一落非零码（有意不是 `80`——那是网络专用码） |
| `--steps-dir` / `GHERKAI_STEPS_DIR` 指的目录不存在 → 退 2 | 明确指了一个地方而那里没东西 = 配置错（`_steps_dir_or_error`） | 指对路径。缺省的 `./steps` 不存在**不算错**——多数项目本就没有确定性 step |
| `plan` 直接退 2、说「使用方 steps 加载失败」 | `plan` 自己的标注探活（`--match-steps`，`_probe_deterministic_dispatch` → `compose.match_deterministic`）撞上 `WorkerSelfDescribeError`；`run` 另有一道等价的本机前置，走 `--capabilities`（`_preflight_worker_runtimes`） | 同上修文件。这是 `plan` 唯一**不降级**的失败：降级成「无标注」等于让人以为那些 step 会走 AI |
| `plan` 只打一行「（标注降级）引擎 X … 无派发标注」，本体照出 | 该引擎运行时没定位到（四级定位链全 miss），属环境问题 | 装那个引擎，或忽略（`plan` 对 miss 一律 best-effort；`run`/`submit`/`list-deterministic` 对同一件事退 2） |
| 某 step 真跑记 `error`，`message` 里列着多条模式 | 一条 step 命中多条模式 | 收紧模式，或改 step 措辞绕开；`plan` 会提前用 ⚠ 标出来 |
| `submit --backend cloud` 退 2，说 variant 解析失败 | 请求的 variant 在该引擎当前版本下没推过 / revision 已清理 / digest 已删 | 让部署方 `push-worker` 推上去；急用可临时 `--worker-variant base`（`gherkai deploy` 已把本版本基底同步成 `base`）。CLI 旧于后端时提示改为「先升 CLI」——推旧版本命名空间的 tag 是原地绕圈 |
| Midscene 报「某文件一条确定性 step 都没注册」 | 双实例守卫：裸 specifier 若解析到第二份包副本，注册会落进 worker 永不读的表 | 确认文件 import 的是 `@gherkai/worker-midscene` 且在顶层调了 `deterministic(...)` |

最后一条值得单独看：Midscene 侧的正确性靠**两道防线**——`bin.mts` 注册的 resolve hook 把裸 specifier 钉到 worker 自身已加载的那个 URL（禁止从 cwd/argv 推算），以及 `user-steps.mts` 的零注册检查把「静默落回 AI」翻成「起不来」。Nova 侧没有这个风险（同进程、绝对包 import 命中同一 module 对象），故也没有这层兜底——这是**有理由的不对称**，不是漏实现。

顺带两条筛选规则（自动加载会跳过的文件，跳过它们是约定而非降级）：Nova 排除 `_*`（供相对 import 的辅助模块）与 `test_*`；Midscene 同样排除 `_*`（同一语义的辅助模块面）与 `*.test.*`，只认 `.mts` / `.mjs`。两侧的 `_` 都判在**路径任一段**上——`_selectors.mts` 与 `_pages/selectors.mts` 同权，辅助模块可按目录分组（被排除的目录整棵不进收集，相对 import 它照旧生效）。想自查当前状态：`gherkai doctor --steps-dir …` 的 `steps.dir` + `steps.load.<engine>` 两项就是这条链的体检（有 steps 目录时 `load.*` 是必修项，没有时降为可选）。

> 权威：[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 4（加载失败 fail-loud、提交侧同样前置、裸 specifier 解析与双实例不变量）、[ADR 0036](../adr/0036-deterministic-capability-discovery.md) 决策 4（`plan` 的降级与例外）、[ADR 0038](../adr/0038-worker-image-delivery.md)（variant 解析 miss 的提示分叉）。

## 5. 两条腿必须对称，与一个诚实的缺口

**对称是要求，不是巧合**：同一份 `.feature` 要能在两个引擎上跑出同样的行为，故注册表 API（`deterministic` + 必填 `description`/`example`）、加载规则（排序递归、fail-loud）、派发三级顺序、判定映射、两个非 job 入口（`--capabilities` / `--match-steps`）的 flag 与输出形状，两侧逐条对齐；各自语言的实现细节（`re` vs `RegExp`、`**groups` vs groups 对象、同步 vs 可 `await`）随语言。跨引擎**不共享 code**——两个 worker 的实现代码各属各引擎，共享面只有 `.feature` 与使用方项目里的 `steps/` 目录约定（两引擎扫同一目录、各取自己的扩展名、正则成对）。

**缺口（已知、非缺陷）**：确定性 step **不产任何产物**。它不调 AI，于是没有 trajectory、没有引擎原生报告页，也不产 `kind=evidence` 的机读证据（Nova `_attach_evidence` 在 `acts` 为空时直接返回；Midscene `stepEvidenceRef` 在「无新 execution 且 prompt 为 null」时返回 null）。后果链：

- 判定**不丢**——RunReport 的判定树、`jobs/*.json`、退出码里，这一步的 `passed`/`failed`/`error` 与时长都在；
- 但「它当时检查了哪个 URL、断言了什么」**不落痕**，一个只含确定性 step 的用例跑出来的报告，人看部分会是空的；
- `gherkai explain` 里这一步的 `evidence_missing` 是 `no_ref`——与「导航步」「AI 跑了但抽取失败」在机读层同码，分不出来。

这个「确定性 step 产物可观测性」的口子是**明确留着**的（让 handler 可选地产一条轻量产物，如当时 URL / 截图 / 检查描述），不是忘了做。证据/产物这一层的全貌见 [`artifacts-and-evidence.md`](./artifacts-and-evidence.md)。

> 权威：[ADR 0013](../adr/0013-cross-engine-sharing-boundary.md)（跨引擎共享止于 `features/` + `steps/` 约定面）、[ADR 0022](../adr/0022-bdd-runner-retired-core-parses-thin-worker.md)（两引擎对称但各自语言）、[ADR 0027](../adr/0027-runreport-aggregation-index.md)（「纯确定性用例 → 空 report_index」节与「留口子」节）、[ADR 0042](../adr/0042-step-evidence-and-explain.md)（证据形态与 `explain`）。

## 6. 延伸阅读

| 想深入的主题 | 去哪读 |
|---|---|
| 怎么写一个 handler（签名、正则、报错语义、带上云） | [`docs/user-guide/writing-deterministic-steps.md`](../user-guide/writing-deterministic-steps.md)（Python 与 TypeScript 两侧并排） |
| 注册表即扩展点、匹配为何在 worker、冲突规则 | [ADR 0022](../adr/0022-bdd-runner-retired-core-parses-thin-worker.md) |
| 默认 AI / 少数派显式、QA 与测试开发的角色边界 | [ADR 0020](../adr/0020-step-phrasing-default-ai-deterministic-scaffold.md)、[ADR 0040](../adr/0040-consumer-role-model-and-terminology.md) |
| 能力自述、`list-deterministic`、`plan` 标注与降级 | [ADR 0036](../adr/0036-deterministic-capability-discovery.md) |
| `steps/` 定制面、加载机制、fail-loud、裸 specifier 解析 | [ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 4 |
| variant 镜像、推送注册、preflight 解析 | [ADR 0038](../adr/0038-worker-image-delivery.md)、[`cloud-backend-carriers.md`](./cloud-backend-carriers.md) |
| `--json` 里 `deterministic` / `list-deterministic` / `doctor` 的字段 | [`cli-json-contract.md`](./cli-json-contract.md) |
| step 判定怎么算（`failed` vs `error`、votes、短路） | [`verdict-model.md`](./verdict-model.md) |
| 产物与证据（谁产什么、落哪、怎么读） | [`artifacts-and-evidence.md`](./artifacts-and-evidence.md) |
| 四种跑法下谁起 worker、definition 怎么随 run 走 | [`execution-and-reconciliation.md`](./execution-and-reconciliation.md) |
