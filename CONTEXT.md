# Gherkin × (Midscene + Nova Act) × AgentCore 测试框架

一套用 Gherkin 描述测试意图、由两个互相独立的 AI 引擎执行、由 AWS 云端浏览器承载的 UI 自动化测试框架。三层正交，靠 CDP（Chrome DevTools Protocol）串联。

## Language

**引擎 (Engine)**:
一个独立的「AI 大脑 + Playwright 驱动」组合，负责把自然语言意图变成浏览器动作。本项目有两个平级、互不替换的引擎：Midscene 与 Nova Act。
_Avoid_: runner（脚本跑测试的工具，含义太窄）、driver（只指底层 Playwright）

**大脑 / 模型角色 (Brain / Model role)**:
引擎内部做决策的 AI 模型。一个引擎可拆成多个模型角色，最关键的是「视觉定位」这一非可选的主力角色。
_Avoid_: 把「模型」与引擎混为一谈——Nova Act 是引擎不是模型。

**视觉定位 (Grounding)**:
把屏幕截图解析成可点击坐标的能力，是 Midscene 主力大脑的核心职责。英文 UI、小字、非拉丁文字会显著影响其质量。
_Avoid_: 把 grounding 与 planning（规划/推理角色）混用。

**AgentCore 浏览器会话 (AgentCore Browser session)**:
AWS 托管的、隔离的单个云端 Chromium 实例，暴露一个 CDP-over-WebSocket 自动化 endpoint（鉴权用 upgrade 请求上的 header-based SigV4）。一个会话只承载一个自动化客户端——两个引擎需各自一个会话，不共享。
_Avoid_: 把「会话」与「endpoint 种类」混为一谈（§0 旧措辞的错误）。注意此处的 CDP-endpoint SigV4 与 Midscene 调 Bedrock `/openai/v1` 的 SigV4 是两套不同的签名场景，别混。

**穿刺 / Spike**:
一次性、风险优先的最小垂直切片，目的是用最小代价撞通最可能失败的环节、得到「成不成」的认知，而非交付可维护代码。
_Avoid_: 把 spike 与里程碑（M1–M5 的工程推进）混用。

**用例描述层 (Feature)**:
语言无关的 Gherkin `.feature` 文件，描述业务可读的测试意图。同一份 `.feature` 可被两套引擎各自的 runner 加载，step 实现分别用 TS 和 Python。
_Avoid_: 把 feature（意图描述）与 step definition（绑定的执行代码）混用。

**骨架验证用例 (Skeleton case)**:
为证明链路本身活着而刻意挑选稳定、中立、英文、无登录站点（如维基百科）写的探针用例。与「真实业务用例」分开看待，避免把站点不稳定的噪声误判成框架缺陷。
_Avoid_: 把骨架验证用例当成最终交付的业务测试。

**穿刺脚本落点（by-engine）**:
spike 脚本**紧贴各自引擎的语言/依赖环境**，放在对应子工程内、诚实标记可丢弃：
- Midscene（TS）→ `midscene/spikes/`，复用 `midscene/node_modules`（含其配方笔记 `SIGV4-FETCH-RECIPE.md`，与代码同居）。
- Nova Act（Python）→ `novaact/spikes/`，用 `novaact/.venv`。
不设 git 根级 `spikes/`（早期曾有，因布局统一为 by-engine 已撤销）。**引擎内**复用的代码（如 Midscene 的 SigV4，仅 Midscene 的 spike 与 bdd 共用）抽到该引擎的 `lib/`（见 `midscene/lib/agentcore-sigv4.mts`）；这不是跨引擎共享——SigV4 是 Midscene 专属，Nova Act 走 IAM/Workflow 不碰它。跨引擎真正共享的是 `features/`（用例），见 [跨引擎共享边界](./docs/adr/0013-cross-engine-sharing-boundary.md)（ADR 0013）。
_Avoid_: 把某一引擎专属的 spike/文档/代码放到根级或另一引擎目录下；也别误以为引擎内的 `lib/` 是两腿共享。

**确定性断言 vs AI 断言 (Deterministic vs AI assertion)**:
确定性断言用底层 Playwright（`nova.page` / Midscene 的 page）判定，结果可复现；AI 断言用自然语言（`act_get` / `aiAssert`）判定，贴合卖点但非确定性、且每次消耗模型调用。**已定（ADR 0014）：AI 断言为默认主力**（忠于框架卖点），确定性断言退为高保真补充与逃生舱；代价是非确定性，须配套抖动治理（重试/投票/度量）。抖动治理的具体参数与"哪些判定强制走确定性"靠更难用例的数据迭代。
_Avoid_: 把 AI 断言当成"无需治理就可信"——它为主，但必须配抖动监控。

**报告产物模型 (Report artifact model)**:
两条腿的报告形态根本不同（2026-06 实测）：**Midscene 出单一 `report.html`**（落项目内 `midscene_run/report/`，含每步截图+AI 决策+坐标）；**Nova Act 出多个分散的 trajectory HTML**（每次 `act`/`act_get` 一个，默认落系统临时目录 `$TMPDIR/..._nova_act_logs/`，可被系统清理，需 `logs_directory=` 固定到项目内）。这是将来报告统一（M5）必须弥合的差异。
_Avoid_: 笼统说「两腿都出报告」而忽略其形态/落点/生命周期的根本不同。

## 产品形态（v1.0）

**通用 step (Generic step)**:
一组**抽象原语** step（导航 / AI 动作 / AI 布尔·取数·取串·否定断言 / 确定性锚点），任何用例复用，QA 不写代码——场景细节放进引号里的自然语言，不放进 step 措辞。这是"QA 只写 `.feature`、零代码"承诺的唯一载体，**其能力边界 = 产品能力边界**。两腿对称实现（Midscene `aiAct/aiBoolean/aiNumber/aiString` ↔ Nova Act `act/act_get(各 schema)`）。详见 ADR 0018。
_Avoid_: 写绑死具体场景的 step（如"语言版本数量"）——那不是通用 step；把它当成"任意动作都能稳跑"——开放性动作会引入页面瞬态 flaky（ADR 0018）。

**柔性冒烟 (Flexible smoke)**:
v1.0 的核心定位（ADR 0015）——只验证业务**意图是否达成**（流程能否走通），对达成路径上未被点名的视觉/文案/布局变化高度宽容。AI 柔性是差异化核心，与"精确回归（任何差异都报警）"本质对立。
_Avoid_: 把它当精确/像素级回归工具用。

**点名检查 (Explicit check) vs 确定性锚点 (Deterministic anchor)**:
两个不同层（ADR 0020）：
- **点名检查**：QA 想精确核对某项时，直接写**纯人话** `Then "价格是 ¥99"`——仍走**默认 AI 判断**（QA 零代码、无路由关键词）。「能否抓某类变更」取决于 QA 点没点名，不是做不到。
- **确定性锚点**：少数"不容 AI 抖动"的精确检查（URL/DOM），由 **test engineer** 在 `deterministic.steps` 脚手架里写 Playwright 查询，不走 AI、不预置（QA 不碰）。
_Avoid_: 以为"不点名也能抓变更"；把它与 A/B 两种不确定性混为一谈；以为 QA 要学特殊措辞（QA 永远只写人话）。

**两种不确定性 (A: flakiness / B: 柔性吞变更)**:
A = 同一页面 AI 判断飘忽（随机噪声）→ **投票可治**；B = 页面真变了但 AI 柔性照样跑过、不报警（灵敏度不足）→ **投票治不了**，v1.0 接受为已知边界（ADR 0015）。
_Avoid_: 以为"投票能带来确定性"——它只压 A，给不了对变更的灵敏度（B）。

**Run 数据模型 (Run data model)**:
执行的层级（ADR 0016）：**Run ⊃ Job(=Scope) ⊃ Scenario**。Scope = 共享操作上下文的 scenario 分组，是执行单元（scope 内串行、scope 间并行）；Feature 是正交的组织轴。Run 产出两样：**RunResult**（机器可读汇总判定，给退出码/CI/WebUI）与 **RunReport**（人看的归集报告，即原 M5「报告统一」的归宿）。
_Avoid_: 把 Feature 当执行单元；把 Job 当 scenario 粒度（破坏会话依赖）；混淆 RunResult（数据）与 RunReport（报告）。

**执行核心库窄腰 (Core-library narrow waist)**:
真正的窄腰是**执行核心库**（解析 `.feature` → 分组 scope → 调度 → 收集结果），**不是 CLI**（早先措辞修正，见 ADR 0016）。CLI 是核心库的第一个、最薄的前端；WebUI 是另一个前端，**直接调核心、不 shell-out CLI**。CI/skill 通过 CLI 这个皮间接用核心。上层前端与可替换的执行引擎（`Engine` port，本地进程 / Fargate；见下「执行引擎 port」条）都围绕核心库解耦。
_Avoid_: 把逻辑焊死在 CLI `main()` 里；以为"WebUI 要包 CLI"；把"选哪个执行引擎（`Engine`）"当成一锤定终身。
（版本演进 spike→v0.x→v1.0→v1.x→v2.0 见 ADR 0016。）

**执行引擎 port (Engine port)**:
核心库之下真正跑一个 scope 的地方，是一个 **port**（`Engine`，由 `ExecutionBackend` 重命名以对齐「引擎」术语，ADR 0016），由组合根注入。v1.0 的两个 adapter `MidsceneEngine`/`NovaActEngine` **形状一致**：各 spawn 对应语言的 worker 子进程、讲同一套 JSON 协议。演进：v1.0 本地进程（浏览器仍在云端 AgentCore Browser）→ 云端倾向 Fargate/ECS（批处理 shape-fit，ADR 0017；非 AgentCore Runtime）。
_Avoid_: 混淆"浏览器在云端"（spike 已验证）与"执行进程也在云端"（>v1.0）；把它当成"核心 import 引擎"——核心永不 import 引擎，只 spawn worker。

**两腿都子进程 + 薄 worker (Both-legs-subprocess + thin worker)**:
两引擎语言锁死（Midscene 锁 TS、Nova Act acting 锁 Python，ADR 0023 证伪了全 TS 核心），故核心（Python）**对每个 scope spawn 一个 worker 子进程**——两腿对称、核心零引擎依赖。worker = 被 spawn 的进程，一生 = 开 AgentCore 会话 → 按 scope 串行跑 scenarios（每 step 派发成 act/assert）→ 回 JSON → 退出（一次调用 = 一个 job = 一个 scope）。**核心自解析 Gherkin**（单一事实源），worker 只派发不解析——故 cucumber 补丁与 pytest-bdd 路由 hack 退役（ADR 0022）。
_Avoid_: 以为子进程里跑整个 BDD runner（那是被否的 B2）；把 worker（运行时角色）与 engine（领域概念/目录名）混用。

**确定性 step 注册表 (Deterministic step registry)**:
test engineer 扩展确定性锚点的落点：在对应 worker 里登记 `(模式 → handler)`（`@deterministic`）。核心发原始 step 文本，worker 先查注册表命中走精确 handler、未命中落 catch-all 走 AI。匹配放 worker（确定性 handler 引擎特定，碰 Playwright/CDP），核心对 step 语义无知。延续 ADR 0020 角色边界（QA 永不碰）。
_Avoid_: 把匹配放进核心（核心只解析结构+调度，不懂 step 语义）；以为 QA 要写确定性 step。

**Ports 层 (Ports & adapters)**:
核心库把可替换的外部依赖收成独立 port，导出稳定接口；核心只依赖接口。四个 port（ADR 0016）：`Engine`（跑 scope）、`RunStore`（**控制面**：run/job 状态/血缘，频繁读写、撑轮询续跑——DDB 主要服务它）、`ResultStore`（**数据面**：每 scenario 判定/投票/报告指针，追加为主）、`ReportStore`（归集报告产物）。`RunStore` 从原 `ResultStore` 拆出（控制面 vs 数据面访问模式不同）。**具体 adapter 由组合根（CLI main / WebUI bootstrap）注入**，不由 module 内部 env-sniff 自选（后者是本项目踩过的 Midscene `GlobalConfigManager` 反模式）。adapters 按 port 分子目录；v1.0 只写 local adapter，云端再填 DDB/S3/Fargate（ADR 0016）。
_Avoid_: 把多个 port 揉成一个上帝 module；让 port-module 用全局单例自选实现；混淆控制面（RunStore）与数据面（ResultStore）。
