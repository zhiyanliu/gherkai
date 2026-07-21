# 存量提纯专项:全 34 ADR + CONTEXT 密度审计(首轮基线,待批)

> 类型: 复盘报告(主观类提纯提案,逐条待批;批准落改后本轮审计 commit 即「跨轮沿用」的基线锚点)

按 `docs/doc-health-review.md` 第一层【强制】提纯/密度审计执行,首轮=全量深清建基线。
每文件一个独立审计 agent(git 层读增长史 + 逐句密度判),每份提案再过独立红线复核(宁严勿松,拿不准即否决)。

**统计**:35 文件全审(动/没动不适用——首轮全量)。24 文件有提案共 36 条:红线复核 **keep 31 / 否决 5**;**11 文件判无**(依据均内容锚定、可对 git 复核)。
keep 分类:sediment-施工叙事 15 / sediment-旧层未删 6 / redundancy-完整重复 9 / filler-过场 1。

---

## 一、待批提案(31 条)

### 0004-novaact-iam-auth-via-workflow.md

*增长史:4 层迭代；仅初建层 44d915d 写入全部实质内容，后 3 层均为非实质就地校准——5095ec0 目录迁移（novaact/→engines/novaact/ 路径前缀）、06647f6 加 `> Status: Accepted` 头、b5f86fa doc-health 复盘（consumer 名 bdd fixture→worker `run_scope.py`）。无被后层覆盖却未删的旧描述层，全部修正就地替换。*

**#1 [sediment-施工叙事]** 「## ✅ 已实测全通（2026-06-23）节」
- 原文:**新发现的关键前提（grilling 阶段没挖到，实跑撞出）**：`@workflow` 走 IAM 路径时，`workflow_definition_name` 必须指向一个 AWS 侧已注册存在的 workflow definition
- 诊断:前缀「新发现的」+ 括注「（grilling 阶段没挖到，实跑撞出）」是施工过程叙事——描述该前提「何时/如何被发现」（grilling 设计审查阶段漏掉、实跑撞出），不承载任一受保护要素：约束知识本身（definition 必须预先注册、否则 CreateWorkflowRun 报 ResourceNotFoundException 404）完整落在括注之后的正文，删括注论证结构不断。「实跑撞出」的经验性已被本节标题「✅ 已实测全通（2026-06-23）」框定，属重复；「grilling 阶段」是过程阶段指代（分几步/施工节奏，非 why/trade-off/不变量/被拒方案）。git 层读佐证：此括注自 44d915d 初建随文写入（spike 撰写当时），后 3 层从未触碰——是诞生即带的施工括注，非被覆盖旧层。
- 建议:压成「**关键前提**：`workflow_definition_name` 必须指向一个 AWS 侧已注册存在的 workflow definition」——删「新发现的」与整个括注，其后约束正文（含 ResourceNotFoundException/404 与「IAM 鉴权本身此时已通过、仅 definition 不存在」）原样保留。候选改与否走主观类待批。
- 红线复核:安全：仅删「新发现的」+ 发现过程括注（属施工节奏叙事），约束本身、ResourceNotFoundException 404 证据、及关键判据「IAM 已通过·非 AccessDenied·仅 definition 不存在」全部原样保留；「实跑撞出」的经验性被本节标题「已实测全通(2026-06-23)」重复框定，非自包含证据；不触 why/trade-off/不变量/被拒方案/历史框定，git 佐证此括注诞生即带、后 3 层未动，非被覆盖旧层。

### 0005-single-shared-feature-file.md

*增长史:6 层迭代：44d915d 初建（决策+M2 验证段当作当前态）→ 553c79c(v0.x) 骨干重构 M2 段、插入「演进(v0.x)」步风格 note、剥离测试计数与 wikipedia_search.feature 文件名 → 5095ec0 路径改 engines/ 前缀 → 06647f6 加 Status:Accepted 头 + 前置「演进(v1.0)」退役 note（整段框为历史）→ b5f86fa worker glob 具名化 → 75d91d1 死指针翻历史自明。两次大改层为 553c79c 与 06647f6。*

**#2 [sediment-施工叙事]** 「✅ 已实测（M2 起）：同一份 .feature 双 runner 加载，均通过」
- 原文:> 演进（v0.x）：最初的 M2 验证用「专用 step」风格的 `wikipedia_search.feature`（…每用例写 step 代码）；v0.x 验证「通用 step」模式成立后，该专用 step 三件套已退役，改用通用 step 版 `features/wikipedia_generic.feature`（QA 只写 .feature、零 step 代码）。当时的 step 实现 `generic.steps.ts` / `test_generic_steps.py` 已随 BDD runner 一并删除（[0022]…）。下述方言/接线结论在两种风格下同样适用。
- 诊断:该 note 记录「专用 step → 通用 step → 随 BDD runner 删除」的施工生平。0005 的决策是「.feature 物理单一共享」；专用/通用 step 之分与此正交，其决策脉络与被拒理由（绑场景句子非真通用 step、应为抽象原语）归属 ADR 0018。此 note 不承载 0005 自身的任何受保护要素——不是 0005 的 why、trade-off，也不是 0005 决策的被拒方案，而是邻近决策的施工生平。git 证据：note 于 v0.x commit(553c79c) 作文件名调和加入，但同一 commit 已把 M2 正文里的 wikipedia_search.feature 剥离、正文改为泛指「同一份 .feature」——调和目的当场消失；随后 06647f6 前置的「演进(v1.0)」note 已把整个 runner 层粗粒度框定为「已退役、保留作验证脉络」，覆盖了本 note 描述的专用/通用子转折；此后 b5f86fa/75d91d1 只是反复给 note 里的死指针 generic.steps.ts/test_generic_steps.py（三个文件均已实测不存在）打补丁，是沉积层被维护而非被质疑相关性的典型。
- 建议:删除该「演进(v0.x)」note——专用→通用 step 生平归 0018/0022，0005 决策不需要它。若坚持保留「当前用例文件」指针，最多压成一行 `> 当前用例见 features/wikipedia_generic.feature（通用 step 详见 0018）`；但该点亦已被上方 v1.0 note 的「保留验证脉络」覆盖，删净更干净。归主观待批。
- 红线复核:安全：0005 的 why(单一事实源)/trade-off(方言交集)/不变量均在别处独立陈述、不受影响；专用→通用 step 的被拒方案護栏完整存于 0018(line 9/11)；该 note 是邻近决策的历史框定施工生平(非 0005 决策脉络)+死指针(三文件已实测不存在)，且被上方 v1.0 粗粒度退役 note 覆盖，删它论证骨架不断。

### 0006-form-a-two-subprojects-no-orchestrator.md

*增长史:7 层迭代（首轮基线）。2 层大改：L2 (03e0d21, 06-26) 在「已知备用路径」末尾追加 line19『✅ 已实查证伪』证伪子条；L6 (06647f6, 07-02) 加 Status 头 + 「演进」块，框定 Partial-superseded-by 0016/0022。其余 5 层为微调：L3 (5095ec0) engines/ 路径前缀、L4 (53b6fc9) 腿→引擎、L5 (a4ee5e0) 「git 根在 yaozhou/」→「单个 git 仓库根」、L7 (b5f86fa) spike 位置根级 spikes/→engines/*/spikes/ 的 STALE 修。*

**#3 [sediment-旧层未删]** 「已知备用路径（存档，暂不走）」
- 原文:⚠️ **重要不确定性（核实置信度 medium）**：该 REST 服务的能力是否等同于本地 SDK 的 `nova.act()` 自然语言浏览器自动化，**未验证**——很可能是不同抽象层。不要据此认为「TS 能直接平替 Python 版 Nova Act 引擎」。`strands-agents` 已作为依赖在工程内（另一条 MCP/Strands 路径，亦未独立验证）。
- 诊断:git 层读证据：本句为初始 commit 44d915d(06-23) 的『验证前不确定状态』层；其每一点——REST 能力是否等同本地 SDK、是否不同抽象层、TS 能否平替、strands 路径是否可行——均被 3 天后 03e0d21(06-26) 追加、紧贴其下的子条 line19『✅ 已实查证伪』逐一定论覆盖（REST=客户端驱动工具调用循环、浏览器驱动胶水仅 Python SDK 有、Strands TS 亦无 Nova Act 浏览器 tool、结论 NO-STILL-NEEDS-PYTHON、备用路径关闭）。追加 line19 时未回改本句，『未验证 / medium 置信度 / 很可能 / 不要据此认为』的 hedging 遂成被覆盖的旧层。不承载受保护要素：非 why（它是存疑非决策理由）、非『被拒方案的为什么』（为什么被拒由 line19 的实查发现承载）、非历史框定（未用曾/原/已被取代框住，读作 live 警告而非决策脉络）、非 line19 那样的自包含证据（它是证据出现前的 hedge）。骨架测试：删本句后 line19『✅ 已实查证伪…此备用路径关闭』论证结构不断——line19 自含『REST 是什么 + 结论』，不依赖本句成立。
- 建议:压缩（不删整块）。line19 已自包含证伪结论与 0023 指针，最干净是删本句；若要保留『这条路曾被认真调查过』的脉络，压成一句历史设问交给 line19 收口，如「原存疑：该 REST 服务能力是否等同本地 SDK 的 nova.act()（含工程内 strands-agents 的 MCP 路径）——」，去掉 medium 置信度 / 未验证 / 很可能 / 不要据此认为 这些已被 line19 定论的 hedging。红线核对：被拒方案（TS/非-Python REST 路径，lines 15-17）与其为什么被拒（line19 实查发现）均完整保留，护栏不损；line19 证伪结论与 0023 指针原样不动。
- 红线复核:git blame 实证 line18=44d915d(06-23) 验证前 hedge、被紧邻 line19=03e0d21(06-26)「已实查证伪」定论覆盖，属被后续层覆盖的旧描述（本句无曾/原/已被取代框定，历史框定在保留的 line19），非误判；受保护类全保留在别处——被拒方案(REST TS 路径 lines15-17 + Strands 路径「Strands TS 也无 Nova Act tool」line19)、why-rejected(line19 实查发现)、Python-lock 不变量(line19「acting 锁 Python」)、0023 指针均不动，line19 antecedent 实为 line17「理论上 TS 可驱动」故删本句不断链，删的仅是被覆盖 hedge + 非受保护类的 strands 依赖细节。

### 0008-midscene-bedrock-auth-sigv4-selfsign.md

*增长史:6 层迭代：initial(44d915d) 一次成型即含全部实质内容——「剩余风险/第一个实验」计划与「✅ 已实测全通」结果节同 commit 落地；06647f6 补 Status:Accepted 头 + 修 env key(MODEL_FAMILY→USE_QWEN3_VL)；eba7cb5 把 region us-east-1 硬编码改为可配 + 加历史框定。其余 3 层(2a89750/5095ec0/53b6fc9)为 spike 路径与「腿→引擎」术语的 cosmetic 替换，均在原处清替换、无旧层残留。*

**#4 [sediment-施工叙事]** 「第一个实验」
- 原文:**第一个实验**：写好 SigV4 fetch 后，跑一次真实 Midscene `aiTap`/`aiAssert`（本地琐碎页面），一次绿灯即坐实自签接线全链路可用。
- 诊断:这是一条施工计划（「下一步跑个实验坐实接线」），属 CLAUDE.md「施工进度/步骤放对话或 PR」而非 ADR 的稳定决策；不承载 why/trade-off/被拒方案/不变量/精确指针中任一。git 层读证据：它与紧随其后的「✅ 已实测全通」结果节在同一 initial commit(44d915d) 同时落地——施工计划出生即被结果节盖过，是「出生即残留」的沉积；且实际所跑（据结果节：aiAct+断言 on AgentCore 云端浏览器、三段式自检）比这句计划所写（aiTap/aiAssert on 本地琐碎页面）更大且不同，计划句现已是过时噪声。删后论证不断：结果节自述「三段式自检全绿，本 ADR 的承重未知已关闭」，自包含且直接闭合上文「剩余风险」，不依赖此计划句。
- 建议:整句删除。上文「剩余风险」节（含签名要点：init.body AS-IS hash / 覆盖 dummy Authorization / 最小规范头集避免过度签名 / 凭证刷新 / 流式——属设计约束与 why）与下文「已实测全通」结果节均保留不动，风险→闭合的叙事保持完整。
- 红线复核:真沉积：一条前瞻施工计划（非「曾/已被取代」的历史框定），不承载 why/trade-off/被拒方案/不变量/指针；git 核实它与紧随的「已实测全通」同在 44d915d 落地、出生即被盖过，且所写 aiTap/aiAssert@本地页 已被结果节 aiAct+断言@云端浏览器 取代而失准；删后 why 仍在保留的「剩余风险」节、闭合叙事由自包含的「已实测全通」节承接，论证链不断。

### 0010-spike-as-apples-to-apples-benchmark.md

*增长史:6 层增长：44d915d 建（含两张 per-engine 基准数据表 + 对标结论表，重复）→ 553c79c 加「待 backfill」TODO 列表 → 8caac30 flip 成「backfill 状态…✅ 已落地」→ 53b6fc9 纯术语「腿→引擎」→ 06647f6 大改（加 Status 头 + 把两张重复基准数据表合并进单一对标结论表，已做过一次去重提纯）→ eba7cb5 修 [skeleton case] 悬空链接。两次内容大改：8caac30（backfill 待办→已落地）、06647f6（合并重复表 + Status）。*

**#5 [sediment-施工叙事]** 「backfill 状态（spike 遗留项，v1.0 已落地）」
- 原文:## backfill 状态（spike 遗留项，v1.0 已落地）
- **断言对称化 — ✅ 已落地**：… （见 `engines/*/worker/`，ADR 0014/0024）。spike 的 `aiAssert` 抛错式写法未带进 worker。
- **`logs_directory` 固定 — ✅ 已落地**：RunReport 落地后（ADR 0027），cli 经环境变量 `NOVA_LOGS_DIR` 把 Nova trajectory 持久化…
- 诊断:git 层读证据：553c79c 把此节建为「待 backfill」TODO 列表（未来要做的施工计划），8caac30 flip 成「backfill 状态…✅ 已落地」状态。「backfill 状态 / ✅ 已落地 / v1.0」是施工进度状态——CLAUDE.md 文档纪律首条明定「施工进度属实现计划、放对话或 PR」，不属稳定 Accepted ADR。两项的实质决策已在 ADR 0014/0024（对称布尔投票）、0027（NOVA_LOGS_DIR 持久化）及 code（engines/*/worker/）权威承载；与本文「实测洞察」②（logs_directory 落临时目录 + 计划固定）③（断言机制可对称 → 0014 应走对称布尔）构成「发现→计划→完成」同一施工线的三段重复。受保护要素（压缩后须保留、勿删）：唯一非重复的「spike 的 aiAssert 抛错式写法未带进 worker」是 spike→生产的 delta（决策脉络，防 AI 误以为 spike 的 aiAssert 就是生产写法），以及 ADR 0014/0024/0027、NOVA_LOGS_DIR、reports/ 等精确指针。
- 建议:压成一句去掉状态框定的指针，保留 spike→生产 delta 与指针。改后形态例：把整节替换为一行——「spike→生产差异：worker 未沿用 spike 的 aiAssert 抛错式写法，改走对称布尔投票（Midscene aiBoolean ↔ Nova act_get(BOOL_SCHEMA)，见 ADR 0014/0024）；Nova trajectory 已由临时目录改为持久化归集（NOVA_LOGS_DIR，见 ADR 0027）。」——删「backfill 状态 / ✅ 已落地 / v1.0」施工进度框定（该状态属做 backfill 的那些 commit）。归主观类待批。
- 红线复核:安全：git 层证实此节是「发现②③→待 backfill→已落地」施工线的完成态状态（553c79c 建为 TODO、8caac30 flip 为 ✅ 已落地），属施工进度而非 Accepted 决策；action 明确保留了受保护要素——spike→生产 delta（aiAssert 抛错式未带进 worker=被拒方案/决策脉络）与 ADR 0014/0024/0027、NOVA_LOGS_DIR 指针，只删「✅ 已落地/v1.0」施工框定（非「曾/已被X取代」历史框定）；N 次投票是 0014 的不变量、报告落点权衡属 0027，均由指针承载、非 0010 独有 why；内容不跨 ADR 搬。不破任何红线。

### 0015-v1-positioning-smoke-not-regression.md

*增长史:4 层增长：553c79c 建库即含现有全部 6 节（44 行）；2a89750 B轮大改两处——「定位·点名时也能测」bullet 与「v1.0 包含」节（原 2-bullet 非目标清单 → 2 个按角色分的编号断言层 + 加 0020/0018/0019 指针），为整体替换、无旧层残留；53b6fc9 纯术语「人话→自然语言」；06647f6 加 Status:Accepted 头。后两层装饰性，核心结构自建库稳定。*

**#6 [redundancy-完整重复]** 「已知边界（v1.0 明确不做）」
- 原文:- **不主动抓未被点名的变更**（种类 B）：QA 没在 `.feature` 里点名的文案/布局/颜色/非关键元素变化，AI 柔性会照样跑过、不报警。这是最左档定位的必然代价，接受。
- 不做像素级 / DOM 快照式精确回归。
- AI 路径不做**精确色值/像素级坐标**核对…粗粒度颜色（"是不是绿色"）AI 点名可做。
- 诊断:三条 bullet 均为已陈述决策的完整再述、无新增受保护要素：bullet1（种类B/未点名不抓=必然代价·接受）逐字重复「两种不确定性」种类B bullet 与其后段（『v1.0 不解决，作为已知边界接受』『不是 bug，是最左档定位的必然代价』），枚举项亦已见于「定位」bullet1；bullet2（不做像素级/DOM 快照回归）是「定位·不做」bullet 的子集，且丢了后者的 Percy trade-off（『与 AI 柔性本质对立，交给专用工具 Percy』），比原句更弱；bullet3（AI 不做精确色值/坐标、粗粒度可判）重复「关键澄清」表『精确色值』行+『布局挪位』行+末尾加粗行（『粗粒度走 AI 锚点；要精确则用确定性逃生舱，见 0014』）。非漂移（内容与源处一致，故非 STALE）。git 证据：本节自 553c79c 建库即存在，B轮(2a89750)的两处改写未触及它——是原始结构里的重复，非后层覆盖旧层。不属红线保护的『带指针简短重述』：这里是无指针的整段再述。
- 建议:主观待批（非破坏性）：把本节压成回指的简短非目标锚——只留一条承载本 ADR 标题落点的「未点名不抓（种类 B），最左档必然代价，接受」，其余改指针『像素级回归见「定位·不做」（含 Percy 理由）；精确色值/坐标见「关键澄清」表』；或整节删、于定位节末加一句「非目标散见上文各节」。若团队重视『明确不做』清单的独立可检索性可保留本节，但 bullet2 至少应回指 Percy 理由，避免比「定位」节更弱。Percy trade-off 本体在「定位」节、不动。
- 红线复核:三条 bullet 的受保护要素（Percy trade-off 在 line11、种类B『投票治不了/必然代价/接受』在 line29-31、逃生舱 why 在 line20-24）都有本 ADR 内其他未动节的权威原文；提案明确『Percy 本体在定位节不动』并把删项转指针或保留，不跨 ADR、无历史框定误判，且本节是无指针整段再述（真冗余形态、非受保护的带指针简短重述），执行不删任何 why/trade-off/不变量。

### 0016-execution-architecture-core-lib-run-model.md

*增长史:约 34 层增长（初版 553c79c 起，33 次 commit 触及）；大改层：7392ed3（v1.0 三层切分重构，数据模型/store 层大动）、f02c7b9（一次主动压缩「删演进疤痕」）、2ed986f（实时写实现对齐）、728387e（--backend 组合根接线段整块加入）、6aef35a（ADR 0034 演进：Status 头改 Partially-superseded、加 L114 分层注 (a)/(b)）、ec04601（v1.2 已实装真跑通全局校准 + 新增 v1.2.0 版本行）、75d91d1（doc-health 修 16 条：L63 幽灵字段/退出码述改）。近 3 层反复原地重打 L114 分层注与 v1.1/v1.2 版本行同一处，是自指编辑注沉积的热点。*

**#7 [sediment-施工叙事]** 「留口子：Ports & Adapters（组合根注入）——「这样上云…⚠️ 分层注」结尾行（L114）」
- 原文:已作为 v1.2 实装真跑通（[0034]…，见下版本切分 v1.2.0）。本行原把 (a)(b) 混为一谈、over-claim 了 (b)。
- 诊断:末句「本行原把 (a)(b) 混为一谈、over-claim 了 (b)」是对本 ADR 文本自身编辑史的元叙事（这行以前写错了），非系统的决策脉络。反模式警告（无状态化≠只加 adapter）已由同句「核心与接口要动，非「只加 adapter」」+「[0034] 纠正」就地充分承载；此末句不再承载 why/trade-off/被拒方案/不变量/精确指针/骨架——删了 (a)/(b) 分层论证结构不断（骨架测试通过）。git 证据：该末句由 6aef35a（ADR 0034 演进 commit）随分层注一起加入，属该次修订的自我说明，本应留在 commit message（6aef35a 的 message 已记录此校准），而非沉入 ADR；ec04601/75d91d1 两层又原地重打这段却未清此自指注。CLAUDE.md 文档纪律：施工进度/文档如何演进属实现计划、放对话或 PR。
- 建议:删末句「本行原把 (a)(b) 混为一谈、over-claim 了 (b)。」；保留其前的 (a)/(b) 分层 + 「[0034] 纠正」+「已作为 v1.2 实装真跑通（见下版本切分 v1.2.0）」——校准框定与结论完整自包含。
- 红线复核:安全：仅删末句「本行原把 (a)(b) 混为一谈、over-claim 了 (b)」——它是对本行文本自身编辑史的元叙事（属 CLAUDE.md「文档如何演进→放 commit/PR」的 SEDIMENT），非设计脉络。反模式护栏（无状态化≠只加 adapter）已由保留的「核心与接口要动，非「只加 adapter」」+ 现在不做 L226 两处充分承载；[0034] 纠正指针与 v1.2 结论均保留，Status 头/v1.1/现在不做 皆回指 ⚠️ 分层注而非此末句。删后 (a)/(b) 论证链、被拒方案护栏、不变量、精确指针全不破——非历史框定误判（无设计决策被反转，只是文档 over-claim 被校准）。

### 0017-cloud-execution-fargate-over-runtime.md

*增长史:2 层迭代。首层 553c79c（v0.x checkpoint）一次成文全部 6 节（决定性理由/诚实修正/翻盘条件/被否相邻选项/何时坐实）；第二层 06647f6（文档质量复盘）仅在标题下新增一行 `> **Status:** Accepted`，正文零改。无被后层覆盖的旧描述层、无逐层叠加的施工括注——是单次成文的散文，非累积叠加体。*

**#8 [sediment-施工叙事]** 「诚实修正（grilling 挤掉的水分）」
- 原文:## 诚实修正（grilling 挤掉的水分）
- 诊断:括注「grilling 挤掉的水分」是对本 ADR 自身提纯过程（grilling 评审）的来源标注，不承载 why/trade-off/被拒方案/不变量/精确指针/Accepted 内联证据中任一。本节真正的被拒方案护栏——正文首句「初轮调查把 Fargate 优势框大了、真正站得住只有一条半」及三条 ✅run-to-exit/⚠️成本/❌不算数的——由正文承载，与此括注无关；删括注后「诚实修正」标题+正文论证结构不断（骨架测试通过）。git 层读证据：首层 553c79c 成文即带此括注、第二层 06647f6 未动，属一次成文残留而非叠加层——恰是快照式读易放过、需层读才定性为施工来源叙事的沉积。
- 建议:删括注，标题压成「诚实修正」（或「对 Fargate 优势的诚实修正」以保信息量）。正文首句「初轮调查把 Fargate 的优势框大了，经核对真正站得住的只有一条半」是被拒方案护栏、保留不动。
- 红线复核:括注仅是「本 ADR 由 grilling 评审提纯」的施工来源标注（属 SEDIMENT），不承载 why/trade-off/被拒方案/不变量；真正的被拒方案护栏（首句『初轮调查把 Fargate 优势框大了…只有一条半』+ ❌不算数条）提案明示保留、决策链完整；『经核对』已保留了『受过审查』信号，删括注无信息损失，未跨 ADR 搬运、未误伤历史框定。

### 0018-generic-steps-capability.md

*增长史:4 层增长：553c79c 建档（60 行原始全文）→ 53b6fc9 纯术语替换「腿→引擎」（零结构变动）→ 558cc0a 唯一实质改写（把「目标原语清单·待收敛」旧层整段替换为「已收敛(v1.0)」callout + 「含已删项·留作设计史」表头，并删掉 待深化 里已兑现的「归纳绑场景 step」一条）→ 06647f6 加 Status:Accepted 头。关键：558cc0a 是干净替换而非叠加，未留旧描述残层、无施工括注沉积。*

**#9 [filler-过场]** 「开篇段（标题下首段）」
- 原文:本 ADR 固化打磨出的能力清单、两个引擎对称映射、刁钻用例暴露的边界。
- 诊断:该分句逐字回声标题「抽象原语 + 两个引擎对称映射 + 边界发现」，只作 ADR 目录式扫描；而正文四个节标题（通用 step 应是抽象原语 / 刁钻用例暴露的边界 / 实践约束 / 已知风险）已提供同一结构导航。它不承载任何受保护要素——非 why/trade-off/被拒方案/不变量/指针/内联证据；也非骨架：删它论证结构不断（首句已立决策上下文「v0.x 验证 QA 只写.feature、零 step 代码靠通用 step」，末句「generic step 是产品核心——能力边界=产品能力边界」立 why），仅丢一句标题重述。git 层读：此句自 553c79c 建档起原样存活四层未动，是原始过场而非迭代沉积。
- 建议:删去该中间分句，开篇收为两句：决策上下文（v0.x 验证…靠通用 step）+ 产品核心 why（generic step 是产品核心——能力边界=产品能力边界）。TOC 功能由标题与各节标题承担。
- 红线复核:该句是标题的近逐字回声（TOC 式预览），不承载 why/trade-off/被拒方案/不变量，无指针故非受保护「有意重复」，非「曾/已被X取代」历史框定；删后决策上下文（句1）+产品核心 why（句3）俱在、论证链完整，导航由标题与四个节标题承担，骨架不断——不破红线。

### 0020-step-phrasing-default-ai-deterministic-scaffold.md

*增长史:4 层增长：2a89750（v0.x B轮）创建原始形态，实现节生为「改造清单，B 步内」（"B 步内"=过程编号/施工节奏）；03e0d21（v1.0 C轮）实现层被 0022 取代——只把实现节头重贴「v0.x bdd 层/已随 0022 转移」标签、body 施工清单原样留存，同轮加 Status 转移注记 + 决定第3条 URL 自动分流；53b6fc9 纯术语替换（人话→自然语言、腿→引擎）；06647f6（文档复盘）换标准 Status 头 + 确定性锚点节「空脚手架」→「QA 零预设」+ 加「落地现状」层 + 否定断言「暂留」→「已归一」。大改层 = 创建（2a89750）与 C轮（03e0d21，加 URL 分流 + 实现层转移）。*

**#10 [sediment-旧层未删]** 「实现（改造清单，v0.x bdd 层；实现层已随 0022 转移）」
- 原文:## 实现（改造清单，v0.x bdd 层；实现层已随 [0022] 转移）
- Midscene `generic.steps.ts`：`AI 确认 {string}` → `{string}`（默认 AI）；删 `页面地址包含`；新建 `deterministic.steps.ts` 脚手架。
- Nova Act `test_generic_steps.py`：对齐；新建确定性锚点脚手架。
- 诊断:不承载 why/trade-off/被拒方案/不变量——是 v0.x bdd 层的文件级施工清单（Midscene 改哪个文件、Nova Act 对齐、新建脚手架），即 CLAUDE.md 所指「施工生平（曾如何实现）」。Status 头（line 3）已明写「下文『实现（改造清单）』…段属被取代的 v0.x 形态」并指向 0022 = 该层已被 0022 覆盖、只留头注未删 body。git 证据：2a89750 创建时节头即『改造清单，B 步内』（过程编号「B 步内」=施工节奏 SEDIMENT 标记）；03e0d21 实现层被 0022 取代后仅把头重贴为『v0.x bdd 层/已随 0022 转移』、body 施工清单原样留存至今。且 line42-43 的『`AI 确认`→`{string}`；删 `页面地址包含`』与『删除的过时措辞』节 line36-37 完整重复，只换成文件级施工措辞。line45 还含悬空的行号内引『本节 35 行』（实际所指内容在 line36、且不在本节）。
- 建议:删整节。施工生平已被 0022 取代、决策脉络（默认 AI/角色边界/删除措辞）已在上文承载，Status 头已记『实现层已随 0022 转移』作护栏，删后不丢 why/被拒方案。唯一别处未有的是 line45 否定断言归一决定——若保留，折一行进『删除的过时措辞』节（如『否定断言 `确认页面没有` 同归一为无关键词』），其余文件级施工措辞去掉。同步删 Status 头中对『实现（改造清单）』节的指代（该指代随节删除会悬空；同句中『Midscene 靠补丁』指代指向 line16、须保留）。
- 红线复核:安全：该节 line42-44 是文件级施工生平（改哪个文件/对齐/新建脚手架），非 why/trade-off/被拒方案/不变量；决策脉络（默认 AI/角色边界/删除措辞）在上文决策节承载，被取代的历史框定由 Status 头+0022 完整保留（历史框定≠过时未被破坏）。唯一别处未有的 line45 否定断言归一决定，action 已明确折进『删除的过时措辞』节予以保留，故决策不丢；属单 ADR 内重组、非跨 ADR 搬运。（安全前提=执行时确实落实 line45 折入，若裸删整节而不折则会丢该归一决定。）

### 0022-bdd-runner-retired-core-parses-thin-worker.md

*增长史:10 层增长（2026-06-26 创建 docs-only → 2026-07-14 迁移表头修）。大改层集中在两个「状态」块的翻转：d8b8f99 加「注册表尚未落地」块 → 95ed13f 翻成「已落地」；06647f6 加 Status 头+退役清单「待删」块 → c34355d 退役真执行后翻成「已执行」。其余 6 层为维护性微调（53b6fc9 术语腿→引擎/人话→自然语言、5095ec0 目录路径 engines/ 前缀、eba7cb5 Status 头补 0006 反向链、b5f86fa 迁移表头 worker/→lib/·worker/）。核心设计正文（两候选表/决定理由/worker 生命周期/确定性扩展设计要点/对既有 ADR 影响/重议）自创建起结构未动——ADR 是「docs 先行、code 后建」workflow 的产物，churn 几乎全花在追平这两个 flip-block 与实况。*

**#11 [sediment-施工叙事]** 「worker 进程跑什么（一次调用 = 一个 scope = 一个 job）」
- 原文:**开会话**：建一个 AgentCore 浏览器会话（**这段就是现 `generic.steps.ts` 的 Before hook / `nova_ctx` fixture 已跑通的代码**，原样搬进 worker 启动段）。
- 诊断:括注是施工叙事残留：叙述迁移动作「原样搬进 worker 启动段」并用现在时「现 generic.steps.ts / nova_ctx fixture」指向已被物理删除的文件（c34355d 随 0022 退役删除 bdd/ 层，grep 证实二者在 code 中已无定义）。它承载的决策内容「worker 启动时开 AgentCore 会话」已由主干句表达；括注只是「这段代码从哪迁来」的施工生平，且指针已悬空。对照：0016:30 处理同一事实时用历史框定「早期在 BDD 的 generic.steps.ts Before/After、nova_ctx fixture 验证过，BDD 直跑层已由 0022 退役」——本 ADR 这句缺框定、读着像文件仍在，正是未随执行更新的旧层。
- 建议:删括注，主干保留「**开会话**：建一个 AgentCore 浏览器会话。」；若要留会话生命周期归属，压成不指已删文件的「（会话生命周期归 worker 启动段）」。
- 红线复核:安全。括注是施工血缘+现在时悬空指针（find 证实 generic.steps.ts 已删、grep 证实 nova_ctx 已无定义；0016:30/0005:22 已用历史框定承载同一事实），非历史框定（用「现」= 断言文件仍在，正是 STALE）。决策「开会话：建 AgentCore 会话」留在主干句，「丢的是装饰器不是逻辑」的 why 留在『决定：B1』理由4，均不动；action 保留主干并提供不指死文件的生命周期归属替代。无跨 ADR 搬运，理由链完整。

**#12 [sediment-施工叙事]** 「退役清单（B1 删除/作废的东西）」
- 原文:> **状态（已执行）**：v0.x BDD 层**已物理删除**——下列入口文件 + `generic.steps`/`test_generic_steps` 副本已删，`bdd/` 目录连同 `midscene/patches/` 已移除；确定性脚手架…已**迁入 `worker/`**（见下「迁移」）。cucumber/patch-package 依赖 + `postinstall` 从 `midscene/package.json` 删除。全 novaact 目录测试无 collection error（曾因 bdd 层 sys.path 脆弱报错）。
- 诊断:此块是退役施工的完成播报（c34355d 把 commit 内容内联进 ADR），非决策。删什么+为何由下方表格承载（cucumber.mjs/patch/conftest/package.json+generic.steps+test_generic_steps 逐行已列「已删|原因」），脚手架迁向由下方「迁移」段承载（见下指针本身指向它）——块内约 80% 与二者完整重复。唯一独有内容「全 novaact 目录测试无 collection error（曾因 bdd 层 sys.path 脆弱报错）」是施工期副作用 trivia，属「施工进度放 commit/PR」而非 ADR。此块是 06647f6 加的「待删」块经 c34355d 翻成「已执行」的 flip 残留：待删态时它必要（警示决策未执行），执行后即降格为播报。历史事实（v0.x BDD 层曾存在、已退役）值得留一句框定，但不需整段完成播报。
- 建议:压成一句状态框定，如「> **状态**：本清单所列 v0.x BDD 入口层已按此物理删除（`bdd/` + `midscene/patches/` 连同 cucumber/patch-package 依赖），确定性脚手架迁入 `worker/`（见下「迁移」）。」——保留「已退役」历史框定与迁移指针，去掉逐文件重列与 collection-error 施工 trivia。
- 红线复核:安全。此块是退役完成播报，删什么+为何由下方「已删|原因」表逐行承载、迁移方向由「迁移」段承载（二者均不动），块内为完整重复而非带指针简短重述；唯一独有的 collection-error 一句是施工副作用 trivia（属 commit/PR），非 why/trade-off/反模式/不变量，也未被框成被拒方案护栏。action 保留「已物理删除」执行态+「v0.x BDD 已退役」历史框定+迁移指针，仅把整段重列压成指针，符合单一事实源；无跨 ADR 搬运，理由链完整。

### 0024-worker-core-protocol.md

*增长史:33 层增长：首版 03e0d21 落协议契约骨架 → v1.0 多轮打磨；大改层 = 5113c48（cost 模型重构 + 把「删除测试逼出的两处收窄」①cost.tokens下沉②kind删 折叠成单条「收窄」，cost 收窄移进「成本信封」节）、7404bba（Nova flag-only 终止契约 + grace 硬约束整节新增）、73268ac→b04bc7c（远程传输整节：SQS→DDB 选型层被完整替换、三方案被拒护栏重写）、329e94b/cd12b62（存活判定与 subprocess 同构收尾）、6aef35a（0034 受控演进，Status 头 Accepted→Partially-superseded + 三处 ⚠️ 注旁挂）。多数大改是「后层整段替换前层」（尤其传输节 SQS 层被 DDB 层无残留替换），仅 5113c48 的标题折叠留下一处未清指针（见提案）。*

**#13 [sediment-旧层未删]** 「输出（worker → core）：流式 JSON Lines」
- 原文:step 不再带 `kind` 字段：core 靠 `votes` 的**存在与否**区分「AI 断言（纳入抖动汇总）vs 其余」即足够；worker 内部如何派发（导航/动作/确定性）是其实现细节，不进协议（见上「删除测试逼出的两处收窄」②）。
- 诊断:句末指针「见上「删除测试逼出的两处收窄」②」指向一个已被折叠、不复存在的旧结构。git 证据：commit 5113c48 把上方（现 line 15）标题从「删除测试逼出的**两处**收窄」(①cost.tokens 下沉进 evidence ②kind 从顶层删) 收成单条「删除测试逼出的收窄」(只剩 kind)，并把 cost 收窄折进下方「成本信封」节——即「两处」措辞与①②枚举都已被删。但本句的「②」序号指针未随上层改写更新，成为指向被删结构的悬空内部引用（旧描述层残留）。本句承载的决策事实（wire 不带 kind / core 靠 votes 存在与否区分 AI 断言 / 派发是 worker 内部细节）并非新信息，line 15（设计原则·收窄）与 line 107（字段语义·votes：「取代了原 kind 字段」）已完整承载——本句是跨切面第三处重述，且其指针是三处里唯一坏掉的那个。
- 建议:修指针为主：把「见上「删除测试逼出的两处收窄」②」改成指向现标题「见上「删除测试逼出的收窄」」（去掉不存在的②枚举），或直接指「见字段语义·votes」。因决策事实已被 line 15+line 107 承载，亦可把整句压成一句带指针的简短重述：「wire 不带 kind——core 靠 votes 存在与否区分 AI 断言，派发是 worker 内部细节（见字段语义·votes）」。属主观待批：若判定「输出 events 节需保留一处 wire 视角的显式说明」则走前者（仅修指针），若判定纯重复则走后者（压成指针句）。
- 红线复核:提案安全：git 证实 5113c48 已把标题「两处收窄①②」折成「删除测试逼出的收窄」、②枚举确不存在，句末指针是真坏链；主行动仅修指针不删内容，压缩支线也保留了 why（core 靠 votes 区分 AI 断言）+派发内部细节+指针（正是红线2认可的带指针简短重述）。决策与理由另在 line15/107/114 完整承载、历史框定「曾有 kind→删」在 15/107 保留，两支线均不删 why/trade-off/被拒方案/不变量、不跨 ADR。

### 0026-schedule-module.md

*增长史:15 层增长（ae2002e 建立 plan+schedule 设计 → 6aef35a 转 Partially-superseded-by 0034）；大改层：5113c48（cost_usd→原生量+三级时长、事件 4→6 类）、7392ed3（签名 run_id 入参→RunMeta）、2ed986f（sink 落库废止→on_event/on_job_complete 旁路+_NON_VERDICT）、e08c571（事件 6→7 类 step_skipped）、06647f6（加 Status 头+终止段压成转指针）、6aef35a（Partially-superseded-by 0034+两处 ⚠️ 注）。每次语义变更均干净替换旧层、无残留沉积；提纯类的唯一命中是 6aef35a 的两处 ⚠️ 注内容重叠。*

**#14 [redundancy-完整重复]** 「优雅终止（schedule 只下逻辑「停」指令，机制归 adapter）」
- 原文:（**⚠️ 此处「一行不改」限于「停止机制」这一层**——[0034](./0034-detached-batch-reconciler.md) 无状态跑批动的是**驱动循环整体**：CLI 脱离后 `ThreadPoolExecutor`/`as_completed` 同步循环在异步路径解体为事件驱动 reconciler，那不是「换 adapter」能覆盖的，见下 L89 ⚠️ 注。停止机制层与驱动循环层是两回事，本条只管前者。）
- 诊断:此 ⚠️ 注与「现在做/留口子」段的 L89 ⚠️ 注同在 commit 6aef35a 一次生成；L89 是挂在「上云只换 adapter/接口不变」断言正下方的权威完整版（含 abort_flag/_stop_all/project/plan_next 全量机制）。本注的『CLI 脱离后 ThreadPoolExecutor/as_completed 同步循环…解体为事件驱动 reconciler』一句与 L89 完整重复、非跨切面简短重述。承载受保护要素的只是它的『限定「一行不改」范围到停止机制层 + 指向留口子』这一去歧义/骨架功能（删了读者会把本条『一行不改』过度外推）；被重复的机制细节不承载额外决策，且本注已带指针（『见下…⚠️ 注』『本条只管前者』），机制解释本就可指针化交给 L89。
- 建议:压成一句去歧义+指针，把机制细节交还 L89：改为『（**⚠️ 此处「一行不改」限于「停止机制」这一层**——驱动循环整体的演进是另一回事、非「换 adapter」能覆盖，见下「留口子」段 ⚠️ 注。）』（保留去歧义与委派功能，删去与 L89 完整重复的 ThreadPoolExecutor/as_completed→reconciler 机制复述；顺带把易漂移的裸 L89 行号指针换成节名指针）。
- 红线复核:安全：删去的仅是与 L89 权威版完整重复的机制细节（ThreadPoolExecutor/as_completed→reconciler），其 why（CLI 退→循环没人驱动）在 L89 更完整；去歧义功能、"非换 adapter 能覆盖"纠正断言、0034 交叉引用（经节名指针+Status 头保留）全在，无 why/权衡/不变量丢失；且把完整重复转成红线认可的"带指针简短重述"、顺带把易漂移的裸行号指针升级为节名指针，不破任何红线。

### 0027-runreport-aggregation-index.md

*增长史:16 层增长。奠基 8caac30（153 行，ReportRef/run_id/JobResult+engine/materialize opt-in/act 级 reportRef）；7392ed3 三层切分重构（run_id→RunMeta、JobResult 持 Job、manifest 软引用 run_id、去内嵌 to_dict）并一度加「早先曾 X 现 Y」演进疤痕；f02c7b9 压缩删疤痕；0f5f7ad kind 归正产物类型 + Nova 轨迹下沉 step 级；06647f6 加 Status:Accepted 头；ba2a351 大改——materialize 压成被拒方案护栏 + href 相对化 + manifest 删 ref 字段。后期 81fadc8/b04bc7c 仅措辞校准。materialize 生平与演进疤痕已被历轮清理干净（护栏保留），残余沉积集中在施工清单/施工验证语气。*

**#15 [sediment-施工叙事]** 「现在做 / 留口子」
- 原文:**现在做（v1.0）**：上述 `ReportRef` 改造、`run_id`（归位进 `RunMeta` definition）+ 组合根生成、`JobResult` 经持有的 `Job` 取 `engine`、`ReportStore.write` 接口 + `LocalReportStore`（manifest + index）、**两引擎产物对称归位到 run 目录**（…）+ reportRefs（…）、cli 默认生成 RunReport（…）、`href` 相对化（local 相对 / cloud 恒等 ref）、单测 + 两个引擎真 e2e。
- 诊断:此条内容全是「上述……」——把正文已逐节论证的决策（ReportRef 改造、run_id 归位、ReportStore.write、两引擎归位、reportRefs、href 相对化）原样再罗列一遍，是「本轮 v1.0 交付了啥」的施工-scope 清单，末尾「单测 + 两个引擎真 e2e」是纯施工验证语气；不承载新决策/why/trade-off/不变量，仅重述。git 证据：该 bullet 自奠基 8caac30 就在，且几乎每个改 code 的 commit 都被机械重编一次——7392ed3 把「JobResult.engine」改成「经持有的 Job 取 engine」、0f5f7ad 把「act 级 reportRefs」改成「Midscene kind=report / Nova kind=trajectory 下沉 step 级」、ba2a351 删掉「--materialize opt-in / 默认不 materialize」——它是 code scope 的镜像而非稳定决策。对比同节「留口子不实现」半边承载真 deferred 决策（确定性 step 可观测性 + why、按 kind 富渲染 deferred），是应保留的骨架。
- 建议:压成一句、保留「现在做 vs 留口子」这个 scope 对照骨架：如「**现在做（v1.0）**：本 ADR 上述全部决策均已实装（单测 + 两引擎真 e2e 覆盖）。」删掉逐项复述与施工验证尾。「留口子不实现」子节整体保留不动。
- 红线复核:逐项核对：8 个实质条目均在正文各专节完整论证（扩展性契约/run_id/JobResult engine/ReportStore 接口/归位 run 目录/Nova reportRef/cli 默认开/href 相对化），此列表是完整重复的施工-scope 清单、非受保护的带指针简短重述；why/trade-off/不变量全在专节不在此。action 保留「现在做 vs 留口子」对照骨架、压成指针式重述、「留口子不实现」子节整体不动。不删任何受保护要素，不破红线。

**#16 [sediment-施工叙事]** 「ReportStore 接口：整 run 一次写（ResourceUri 收口条）」
- 原文:消费端（cli/WebUI）只当 URI 用、不 stat/open——cli 现把它原样放进 `artifacts.report_index` 并打成可点击的 `file://` 链接。S3ReportStore 落地时零改本签名，验证了这层收口。
- 诊断:本条的决策与 why（为何返回 ResourceUri 而非 Path）已由前文「同一签名容两种落点，否则 S3 adapter 被迫返回 Path 包 s3://（Path 会把 s3://b/x 折成 s3:/b/x，错）」完整承载。「cli 现把它原样放进 artifacts.report_index 并打成可点击的 file:// 链接」是 cli 当前实装细节（属 code 单一事实源，且已越出「ResourceUri 类型收口」这条的主题）；「S3ReportStore 落地时零改本签名，验证了这层收口」是施工-验证语气（proof-of-work），且与第 72 行「S3ReportStore（v1.1 已建）……core 不动」重复陈述同一事实。删掉论证结构不断（why 在前句）。骨架测试：去掉这两句，「为何 ResourceUri」照样立。注意保留的不变量：「消费端只当 URI 用、不 stat/open」是消费端契约，须留。
- 建议:压成：保留「消费端（cli/WebUI）只当 URI 用、不 stat/open」这句消费端契约，删掉其后「cli 现把它原样放进 artifacts.report_index 并打成可点击的 file:// 链接。S3ReportStore 落地时零改本签名，验证了这层收口。」两句施工细节/验证语气。
- 红线复核:why（同一签名容两种落点 / Path 会把 s3://b/x 折成 s3:/b/x）在被删两句之前的句子、不动；关键不变量「消费端只当 URI 用、不 stat/open」action 明确保留。被删两句是 cli 实装细节（code 单一事实源）+「零改本签名验证了收口」的 proof-of-work（且与第 72 行『core 不动』重复）。删后论证链完整，未删 why/trade-off/被拒方案/不变量，不破红线。

### 0031-job-lifecycle-states-and-severity.md

*增长史:6 层增长：e7e4e47 诞生（决定一~五+touch points+留口子）；2ed986f 把决定三「实时增量聚合=现状」STALE 校准为「前向口子」并删掉旧层两条 bullet（no-op/共用severity表）——旧层已被后层完全替换无残留；e08c571 新增决定六（step 级短路）并改写决定一（skipped 下探 step 级）；06647f6 加 Status:Accepted 头、删掉决定二一处 copy-paste 逐字重复（已清）、修 touch-point 行号漂移；6e21448 仅术语「腿→引擎」；6aef35a Status→Partially-superseded-by 0034、决定五数据源补 ⚠️ 脱离路径注。跨迭代已主动清理，无旧描述层沉积。*

**#17 [redundancy-完整重复]** 「决定六：step 级短路——SKIPPED 下探到 step 级 + 正交 shortcircuited 布尔」
- 原文:前者是「job 根本没跑」（无 step 明细）；后者是「job 跑了一半、剩下的 step 被主动跳过」（有 step 明细，标 shortcircuited）。
- 诊断:紧接其上的对照表已用「谁 skip / 有 StepResult 吗」两列给出同一信息（job 级=整个 job 从未 spawn=无 StepResult；step 级=上游 error 后跳过后续 step=有 StepResult、标 shortcircuited）。本句是表格前两列的散文复述，不承载新的 why/不变量/指针；其后「两级都复用 Status.SKIPPED…语义一致」才是非重复的综合结论。骨架测试：删本句后综合句仍引「两级」锚定表格两行，论证结构不断——它仅重述表格已说过的点，不是让论证可跟随的框定/次序骨架。
- 建议:压成一句：删本句（表格已含），保留其后综合句「两级都复用 Status.SKIPPED 表『没跑』，语义一致、只是层级不同；shortcircuited 布尔进一步标出 step 级『为什么没跑』」。
- 红线复核:逐元素可映射到紧邻其上的表格两行（谁 skip / 有 StepResult 吗 / 承载），无新增 why/不变量/指针；保留的综合句（line 163）承载表格没有的语义统一 + shortcircuited 正交轴结论，删后论证骨架不断，属真冗余。

### 0032-fargate-execution-environment.md

*增长史:14 层迭代：e0718d3 拆自 0029 建为 31 行 Draft（定位/最大风险/留口子/重议 四节）→ 81fadc8 加「抢传能力」+「留待真 Fargate」段 → 3021743 Draft→Accepted、新增「真容器校准结论」节（4 真跑表+4 结论）并把「留口子」前两项划掉标 ✅ → 6392546 把「进程收尾固定尾巴」重归因为 ECS 记录滞后（表行+结论 2 重写、subprocess 预算 141→129s）→ 0a2d621 内联「丢失量级实测」+清 journey 引用 → 后续 329e94b/1ae8a8c/7e02737/9bec8b6 逐层把「留口子」剩余 backlog 收成「已解决/否决」。沉积主源＝Draft→Accepted 那次把开放待办改成删除线保留、且「留待真 Fargate」段被反复改写成状态汇总。*

**#18 [sediment-施工叙事]** 「留口子 / 待真做时定（Fargate 特有）」
- 原文:**~~即时上传粒度~~（✅ 已定 + 真跑复验）**：act 边界即时抢传（主路径锚 step_done 安全点 + Midscene handler 兜底），非结束批量——见上「抢传能力」条。真跑复验：Nova trajectory / Midscene report 中断后均救回 S3（见上「真容器校准结论」孤儿验证）。
- 诊断:删除线+✅ 是 Draft 期开放待办被 3021743（Draft→Accepted）就地划掉、未删的施工节奏标记。所述决策（step_done 主路径 + Midscene handler 兜底、非结束批量）与真跑归零结论已在同节上方「抢传能力」段完整承载（该段 81fadc8 引入），本条仅『见上…条』指回，不承载任何独有的 why/trade-off/被拒方案/不变量。
- 建议:删。substance 全在「抢传能力」段；若要保『即时上传粒度这一 backlog 已闭合』的导航价值，压成一句指针『即时上传粒度：见上「抢传能力」条（已定+真跑复验）』。
- 红线复核:全部 substance（step_done 主路径+Midscene handler 兜底、非结束批量、中断后救回 S3）均在同节上方「抢传能力」段承载，本条无独有 why/trade-off/被拒方案/不变量；strikethrough+✅ 属施工节奏标记非决策脉络历史；action 已保留指针选项，不破红线。

**#19 [redundancy-完整重复]** 「留口子 / 待真做时定（Fargate 特有）」
- 原文:**~~grace / stopTimeout 预算~~（✅ 已真容器标定）**：见上「真容器校准结论」。`stopTimeout=120`（可配）；Nova grace 下限 margin 60→30（下限 180→150）；Midscene 25 不动。「grace 下限 > stopTimeout 上限」的关系经实测厘清：**subprocess 侧满足不变量、Fargate 侧对最坏长 act 结构性接受（D+TTL 兜底）**（结论 4…）。历史背景：`handle.stop(grace_period_s)` 运行期参数被 Fargate 忽略…
- 诊断:逐句核对：stopTimeout=120/可配→结论 3；margin 60→30、180→150、Midscene 25 不动→结论 4「据此的 code 决策」；「subprocess 侧满足不变量、Fargate 侧结构性接受（D+TTL 兜底）」＝结论 4 标题原文；「handle.stop 被 Fargate 忽略、真实宽限由 stopTimeout 决定」→结论 3。每一分句都在同节上方「真容器校准结论」出现（同为 3021743 新增），本条无任何独有要素——是同一次 commit 里既加结论节又把旧待办改写成结论摘要而留下的完整重复。
- 建议:删整条。数字与结论全在「真容器校准结论」；如需保 backlog 闭合痕迹，压成一句指针『grace/stopTimeout：见上「真容器校准结论」（已真容器标定）』。
- 红线复核:逐句核对，stopTimeout=120可配/margin 60→30/下限180→150/Midscene 25不动/「subprocess满足不变量·Fargate结构性接受(D+TTL)」/handle.stop 被忽略 全在「真容器校准结论」结论3&4 原样承载（该节不动）；被拒方案 B 也不在本条；完整重复、零独有要素，删/压均不破红线。

**#20 [sediment-旧层未删]** 「留口子 / 待真做时定（Fargate 特有）」
- 原文:## 留口子 / 待真做时定（Fargate 特有）
- 诊断:标题是创建（e0718d3）时的 Draft 期开放-backlog 框定。现该节 5 项全部 ✅ 已定/已实现/已真验或经分析否决（最后一项 9bec8b6 收敛），无一「待真做时定」——标题描述的旧世界已被逐层迭代覆盖却没改，属旧层未删。剩余 3 项（退化网络真验/上传失败处理两层/孤儿 reaper 否决）承载的是处置结论与被拒方案，非留口子。
- 建议:改标题为反映现状的『Fargate 特有问题：处置结论』或『Fargate 特有韧性 backlog（已收敛）』；配合删/压前两条后，本节即成纯处置台账。
- 红线复核:该节 5 项全部已定/实现/真验/否决，无一「待真做时定」，标题是被迭代覆盖的旧层（STALE）；重命名为「处置结论/已收敛」是客观修正，不删任何 why/被拒方案/不变量（reaper否决等仍在节内各条），且「已收敛」选项还保留了 backlog 曾开放的历史框定。

### 0033-iac-aws-backend-and-composition-wiring.md

*增长史:11 层迭代。大改层：WP2(6e21448) Draft→Accepted 且落 CDK 本体（新增 VPC 来源节、去 chromium 二进制、IAM 表扩充、产物两组 env、workflow-definition「已定」）；IAM ARN 收窄(6520093) 重写 IAM 表资源维度 + 删误授 GetAct；job-in lifecycle 定案(f53aaa1) 用「已定+已实现」替换旧「未定/倾向」层。多数 superseding commit 都正确删了前层——仅 _read_ssm_list 空值处理一处例外（旧层未删）。*

**#21 [sediment-旧层未删]** 「subnet/sg 走 SSM（AWS 生成 ID，无字面默认）」
- 原文:**`_read_ssm_list` 空值静默产出空 subnets/sg（判不可达、暂不加固）**：`_read_ssm_list` 用 `[v for v in value.split(",") if v]`，对空串 → `[]` → `resolve_network` 返回空 subnets → 一路漏到 RunTask 才被 ECS 拒（不点名 prefix，破 preflix fail-fast 惯例）。…**触发 = 若真遇到「读了却空」**：顺手在 `_read_ssm_list`/`resolve_network` 对空补 fail-fast 点名 prefix（对齐 preflight 惯例）。低频、非阻塞。
- 诊断:此 bullet 由 commit 0a2d621（7/12 journey 吸收）加入，描述 `_read_ssm_list` 「空值静默产出空/暂不加固」并列出「若真遇到再顺手补 fail-fast」的 backlog。7 天后 commit 3d5f7cd 实装了 fail-fast（code 核实：cli/cli/compose.py:382 `_read_ssm_list` 对空列表 `raise ValueError` 点名 SSM path），并在「VPC 来源」节新增 line 69「cli 读 SSM 空值 fail-fast（低频加固）」描述其已完成——但没删本旧层。本层现直接与现状及 line 69 相反（说「暂不加固/backlog」，实际已加固），其独有的「暂不加固/触发条件」结论已假；「几乎不可达」这一受保护 why 已由 line 69 承载（『空值几乎不可达——只可能来自配置异常』），不构成删本层的护栏。
- 建议:删除本整条 bullet。line 69 已完整覆盖当前状态（fail-fast 已实现、错误点名 SSM path、空值几乎不可达）。若认为本层「真实 SSM StringList 强制参数值最小长度 1、写入期拒空」这一更精确的『为何不可达』依据值得留，可将该半句并入 line 69 的「几乎不可达」括注，但不保留「暂不加固 / backlog 触发」的旧结论。
- 红线复核:确系旧层沉积、删之不破红线：commit 3d5f7cd 已实装 fail-fast（code 核实 compose.py:382 对空 raise ValueError 点名 SSM path），本 bullet「暂不加固/backlog 触发」结论已假、且与 line 69 及现状矛盾（非「曾/已被X取代」的诚实历史框定，是过时态伪装成当前）；全部受保护 why（几乎不可达/只可能来自配置异常、避免 RunTask 才炸的静默失败、preflight 同风格）已由 line 69 完整承载。唯一独有内容『SSM StringList 强制最小长度 1、空值进不来』本身是与 line 69+code（均视空值可达、故才加固）相矛盾的过时断言，非真 why，删之不破线。

### 0034-detached-batch-reconciler.md

*增长史:13 层增长（6aef35a→75d91d1，160→192 行）。大改层：6aef35a 初版设计定稿（先于实现、Status「尚未落 code」）；7d9e9bd 把 cloud 冷启动从「submit 直起首批」改成专用 kicker Lambda（submit 收窄到零 ECS 权限），被拒方案加两条；aba658e/9638ad4/74f0ca6 三层反复打磨 cloud status --wait 接力语义（每轮无脑踢→检测卡住才踢、补 local/cloud「本机是否须跑到底」不对称收口）；ec04601 v1.2 全局校准，Status 头「设计定稿/尚未落 code」→「已实装真跑通」、正文未落地口吻全改；75d91d1 doc-health 清施工编号 P3/P3a/P3b/P4d→自明事件描述（这层已把大部分裸过程坐标翻成「实装真跑逼出」的自包含 lineage，故正文的「逼出」型血缘属受保护证据、非沉积）。*

**#22 [redundancy-完整重复]** 「地基实测」
- 原文:节标题「…+ 真 DDB Streams/条件写；临时 PoC 脚手架验后即清、未入库）」与正文首句「…唯一有效证据（临时 PoC 脚手架验后即清、未入库）：」
- 诊断:「临时 PoC 脚手架验后即清、未入库」在节标题与正文首句相隔两行逐字重复，自初版 6aef35a 即并存、13 层从未清理。两处都不承载对方没有的受保护要素——同一事实（PoC 脚手架未入库）说两遍，非带指针的简短重述。
- 建议:删正文首句里的括注（节标题保留即可）。改后正文首句：「moto 立即返回测不到事件投递/并发时序，健康网真跑不触发这些路径——故下列是「绿≠对」边界的唯一有效证据：」
- 红线复核:两处逐字相同、无漂移，body 括注是无指针的裸重复而非受保护的『带指针简短重述』；删 body 一份后事实仍存于节标题，body 句的 load-bearing 部分（moto 测不到→绿≠对唯一证据）未动，不删任何 why/不变量/精确指针。

**#23 [sediment-施工叙事]** 「地基实测（施工期已补真验段）」
- 原文:**施工期已补真验（原「地基实测」时未覆盖的）**：`status --wait` 接力 + Stream 丢投 → **已真验**…；`setsid` local 脱离 → **已真验**…；四机制 → core 单测…+ local/cloud 端到端真跑覆盖。
- 诊断:括注「原「地基实测」时未覆盖的」叙述构建时序——地基实测快照当时没覆盖、施工期后补。对已全部实装的 Accepted ADR，「这些路径已真验」是受保护证据，但「何时补的（相对地基实测那次）」是施工序，不承载 why/trade-off/不变量。ec04601 把上一版「实测未覆盖（诚实标定）」翻成「施工期已补真验」时保留了这层时序框。段内真验内容（setsid 脱离/丢投救活/四机制单测）是自包含证据、保留。
- 建议:压掉时序括注，标题改为陈述当前已验证事实。改后开头：「**已补真验**：`status --wait` 接力 + Stream 丢投 → 已真验…」——去掉「（原「地基实测」时未覆盖的）」，其余证据列表原样。
- 红线复核:『原地基实测时未覆盖』是相对里程碑快照的施工时序沉积（何时补），非受保护的『旧世界决策脉络』历史框定，也非 why/trade-off/不变量；证据内容（造卡 pending 救活/setsid 脱离/四机制单测）自包含且原样保留，『已补真验』陈述当前真值、诚实性（仍留未做项）不减。

### CONTEXT.md

*增长史:23 层迭代（44d915d 初版术语表 → v0.x 两次 checkpoint → v1.0 大改重排 5113c48/7392ed3 奠定现代术语条 → 压缩大改 f02c7b9 opus 审计 -4.4% 删演进疤痕 → 术语统一 53b6fc9「腿→引擎」全改 → 连锁失败读法条被 e08c571 完全重写覆盖 2a96c97 旧层 → Fargate/backend 多次追加 → v1.2 无状态跑批 ec04601 在 Ports 段尾追加一层）；主要大改 = f02c7b9 压缩、e08c571 连锁失败条整段替换、ec04601 v1.2 追加。*

**#24 [sediment-旧层未删]** 「Ports 层 (Ports & adapters)」
- 原文:未发明 ADR 有意 defer 的字段（jobId/起止/续跑读取面待真实需求逼出）……「续跑/轮询读取面」由此定型：外部只读 RunState……不再是「待逼出」。
- 诊断:同一行内自相矛盾的旧描述层：前半 defer 清单仍把「续跑读取面」列为「待真实需求逼出」，后半 v1.2 追加句却明说「续跑/轮询读取面」由此定型、不再是「待逼出」。git 证据：ec04601 只在行尾追加了整句 v1.2 定型描述，却没回头把「续跑读取面」从 defer 括注里删掉——正是「被后续迭代覆盖却没删的旧描述层」。此片段不承载 why/trade-off/被拒方案，纯属过时状态残留。
- 建议:从 defer 括注删「续跑读取面」→「（jobId/起止待真实需求逼出）」，把 defer 清单与后半「已定型」层拉齐（后半句权威、保留不动）。
- 红线复核:真属同行内自相矛盾的旧状态残留：defer 括注的「续跑读取面待逼出」是现在时态断言，被同句后半 v1.2 权威层「由此定型…不再是『待逼出』」直接否定；无『曾/原』历史框定、非有意重复。删该项后 YAGNI 决策(未发明 defer 字段)仍由 jobId/起止 承载，不触 why/权衡/被拒方案/不变量。

**#25 [sediment-施工叙事]** 「执行核心库窄腰 (Core-library narrow waist)」
- 原文:真正的窄腰是执行核心库（…），不是 CLI（早先措辞修正，见 ADR 0016）。
- 诊断:「早先措辞修正」是施工叙事括注，只记录「构建过程中曾改过措辞」这一事件，不承载受保护要素：为何核心库是窄腰由句身+「见 ADR 0016」指针承载；被拒方案「CLI 是窄腰」已由句中「不是 CLI」明确护住。git 证据：自 7392ed3 v1.0 重排即带此括注，f02c7b9 压缩轮删了同类『§0 旧措辞的错误』却漏删这条，属残留。精确指针「见 ADR 0016」受保护须留。
- 建议:压成「（见 ADR 0016）」，删施工叙事「早先措辞修正」、保留指针。
- 红线复核:「早先措辞修正」是对文档自身措辞史的施工元注释(被后续覆盖的旧描述层)，非领域决策脉络；被拒方案『CLI 是窄腰』由保留的「不是 CLI」护住、why 由句身+保留指针「见 ADR 0016」承载，删后论证结构不断。

### 0028-transient-network-ssl-resilience.md

*增长史:19 层:首层建骨架,此后逐轮把真跑暴露的缺口从「defer 留口子」改写成「已实现/已根治」并 append 回同一节,累积施工轮次坐标与一处 SDK 事实完整重复。*

**#26 [sediment-施工叙事]** 「现在做/留口子(各已实现条的标题括注)」
- 原文:**静默 worker 超时根治(后续轮,真跑暴露)** … **会话血缘随首事件回传(同轮)** … **Midscene SIGTERM 会话泄漏两窗口已根治(后续轮)**
- 诊断:「后续轮」「同轮」是相对首版之后的施工轮次坐标(=commit 节奏),对未来读者是悬空过程指代(「哪一轮」无锚)。git 证据:随 c0eee99/57d14b5 等逐轮把 defer 改写为「已根治」时逐层 append。「真跑暴露」是自包含事件描述(合法证据锚),不动。
- 建议:删「(后续轮)」「(同轮)」,保「(真跑暴露)」与状态词。
- 红线复核:「后续轮/同轮」是施工轮次坐标(SEDIMENT),删之不触 why/trade-off/不变量;「真跑暴露」证据框定与「已根治」状态词均保留。

**#27 [sediment-施工叙事]** 「现在做/留口子 → scope 内 step 级短路条」
- 原文:**scope 内 step 级短路(已实现,[0031] 决定六)**:曾是本 ADR 记的空白(下面「留口子」里最初记的 defer)——上游 step error 后…
- 诊断:「曾是本 ADR 记的空白…」是文档条目自身的搬迁史(原记于「留口子」子列、实现后上移),不带 why、对理解当前短路决策零贡献。git 证据:2a96c97 记 defer,e08c571 实现后改写上移,该从句是搬迁自指残留。
- 建议:删该从句,直接陈述现状(问题现象+「修复归 worker 非 core」的 why 在其后正文原样保留)。
- 红线复核:删的是「defer→实现」施工叙事(状态已在标题「已实现」);问题现象与 why 在后文原样保留,且其回指的「留口子里 defer」已近悬空。

**#28 [redundancy-完整重复]** 「残留缺口 → SDK 硬限制子条」
- 原文:**SDK 硬限制(不因决策改变的事实)**:Nova 的 `get_session_id()` 要 `with NovaAct.__enter__` 成功后才拿得到,而会话在 `__enter__` **内部**就已建立、开始计费。
- 诊断:此 SDK 事实在同一段落上文已逐字级完整陈述。git 证据:上文句来自 a01ed41,本子条来自 7404bba 追加,两层各留一份完整副本、非带指针简短重述。
- 建议:前半改「见上」回指,只留增量结论(worker 拿不到→上报只能提前到 __enter__ 返回后→窗口能缩小无法消除→真正消除需 SDK early hook/CloudWatch,超范围)。
- 红线复核:同节上文近逐字重复且无指针;改「见上」属单一事实源,增量结论全保留,TTL 兜底另有出处。

### 0029-engine-artifacts-to-s3.md

*增长史:拆自 0028/Fargate ADR 后逐层叠加:混合两级时机、抢传四级、重定位为「注入驱动」——每次重定位都在新章节把「三态注入策略」再复述一遍。*

**#29 [redundancy-完整重复]** 「决策核心:上传由注入的 S3 落点驱动」
- 原文:变的只是**组合根按什么注入**:用户侧 `--backend cloud` 强制注入(盘会销毁)、`--backend local` 不注入(同机可读);`subprocess+注入落点` 作内部预演也走注入路径。
- 诊断:紧邻其上的三个 bullet 已逐条列明同一三态、更详尽。git 证据:b04bc7c 重定位时逐节重述三态,此处即重复层。前半「触发判据只有一个=有没有注入」(不变量)与句末 0016 指针不动。
- 建议:删中间三态重列,改「变的只是组合根按什么注入(见上三态)」;保留不变量句与 0016 指针。
- 红线复核:上方三 bullet 更详尽,重列无增量;不变量句与指针即该句载荷,压缩属单一事实源。

### 0030-realtime-persistence-seam.md

*增长史:159 行诞生后:压缩轮改双注入点、加决定六/七、0034 演进加决定八+重议——留下「为何 RUNNING 走 on_event」与「0034 兑现留口子」两处各自的完整重复层。*

**#30 [redundancy-完整重复]** 「决定二(注块)」
- 原文:理由是并发不变量(见决定三末):sink 被 schedule 的 sink_lock 串行化,若把 RUNNING 的磁盘写塞进 sink,会把它串进所有 worker 的进度显示临界区。故 on_event 独立、在 sink_lock **之外**调。
- 诊断:决定三内同名 blockquote 是该论证的权威所在、逐点更全;本注块已带「见决定三末」指针却仍复述全论证。git 证据:2ed986f 同时在决定二加注、决定三立权威 blockquote,两处自此并存。
- 建议:压成简述+指针,论证正文只留决定三一处。
- 红线复核:权威论证与被拒方案(装饰 sink)完整留在决定三,链条不断。

**#31 [redundancy-完整重复]** 「现在做/留口子(HWM 条)」
- 原文:无状态跑批下 reconciler 跨进程/跨 Lambda 并发直写 `RunState`,此「留口子」被兑现——用 `high_water_mark` 条件写(非 owner/lease,更轻)+ finalize 单独条件写保 commit 恰一次。
- 诊断:同 commit(6aef35a)新增的「重议」条已完整给出同机制(含 DDB 实测血缘)。句末「续跑/部分重跑的 attempt 维度仍留口子(0034 未涉及)」是仍开的口子,须留。
- 建议:压成状态项+指针,机制细节只留「重议」;顺修该条头「设计定稿、尚未落 code」与 Status/重议「已落地」的矛盾(STALE)。
- 红线复核:机制在「重议」更全,被拒方案(非 lease)与实测证据留在重议,attempt 口子保留;注意压缩时状态项须随指针取「已落地」。

---

## 二、红线复核否决的 5 条(不落改,存档供校准)

- **0013-cross-engine-sharing-boundary.md** [sediment-施工叙事]:引擎内复用（如 `engines/midscene/lib/agentcore-sigv4.mts` 被 Midscene 的 spike 与 worker 共用）是健康的，但那是**引擎内**，不是…
  - 否决理由:括注是「勿混」这一反模式的真实发生实例（此混淆确曾在 CONTEXT 犯下并订正），承载反模式实例价值、对 AI 读者有信号；且用「曾/已更正」历史框定措辞。删它触「绝不删反模式」红线边缘，提案自认价值可辩、属拿不准 → 宁严勿松否决，交人定夺不擅删。

- **0014-ai-first-assertions.md** [filler-过场]:Midscene 取结构化全家族可选：`aiBoolean / aiNumber / aiString / aiQuery<T> / aiAsk`。…
  - 否决理由:触红线22：该句是「Midscene结构化全家族」这一事实的完整重复（REFERENCES.md/0010/0018 各有）且未漂移（与code一致，0018更把aiNumber/aiString落成对称提取决策），红线只允许压『完整重复且已漂移』的；此句还把line16投票所用aiBoolean定位进非抛错家族、反衬aiAssert被拒方案，属强化item1权衡框定的有意重复。删除有破红线风险，宁严勿松否决（如需可走提案②承载化，不删）。

- **0032-fargate-execution-environment.md** [sediment-施工叙事]:**真 Fargate 校准（`stopTimeout`/grace 预算 + 中断抢传 + 干净退出）已完成**（4 次真跑，见下「真容器校准结论」）。… 孤儿产物主动扫盘 reaper **经分析…
  - 否决理由:拟删的「孤儿 reaper 经分析否决（…详见下条）」是被拒方案的带指针简短重述——正是红线「有意重复（带指针简短重述）≠冗余」明文保护的可读性设计，且与头号风险(容器盘停即销毁)主题同源；「backlog 全部收敛（做/真验/否决各有归属）」是收束该风险叙事的框定句。拿不准是否属可删沉积，宁严勿松否决。

- **0034-detached-batch-reconciler.md** [redundancy-完整重复]:踢 Lambda（非本机 tick）保「status 机器零 ECS 权限」：起 task 走 Lambda 的角色（有 RunTask/PassRole），status 机器只需 `lambda:I…
  - 否决理由:触红线。指针目标「三触发源」cloud 侧（96 行）只有『status 机器零 ECS 权限 / Lambda 名从 --prefix 推理』的粗述，缺本条独有的具体 IAM 权限（RunTask/PassRole、lambda:InvokeFunction）、`{prefix}kicker`+复用 names 单一命名真源的 why、及对 ADR 0033 的跨 ADR 精确指针；压成指针指向更稀薄处=删 why+删精确指针，非合法单一事实源指针化。

- **CONTEXT.md** [sediment-施工叙事]:RunReport（人看的归集索引，原 M5「报告统一」的归宿，v1.0 已实现：…）…
  - 否决理由:触『历史框定≠过时』红线：用「原…的归宿」明确历史框定，「报告统一」承载 RunReport 的原始设计目标(决策脉络/why)；且 M1–M5 是本文件(line25-26)在用的概念、非悬空 journey/WP 指针，删之不修任何 DEADLINK。提案自认『较弱/偏主观』并给出搁置选项——宁严勿松否决。

---

## 三、判无的 11 个文件(依据均内容锚定)

### 0001-scope-limited-to-english-ui.md
- 增长史:3 层迭代、零层结构性改写正文：44d915d 一次写就标题+两段正文（内容与今日一致，仅「这条腿」）→ 53b6fc9 纯文案替换「腿→引擎」（不动结构）→ 06647f6 仅补一行 `> **Status:** Accepted`。正文自创建起从未被覆盖重写，无旧描述残层、无逐层叠加的施工括注。
- 判无锚定:最险成候选的是正文段末「两个引擎能并存的前提就是英文界面。」——它紧接前句「Nova Act 引擎仅支持英文」+「这是一条承重假设」，读来像把「英文是前提」再说一遍、险被判 REDUNDANCY 完整重复；留它是因为它是本 ADR 存在理由的关键不变量（双引擎并存 ⟺ 英文界面，红线护栏「关键不变量」），删了则第二段「Nova Act 作废→卖点垮一半」的因果失去支点。第二处险成候选的是末句「——届时应另立新 ADR 取代本条，而非小修小补。」，语气上近似过场收尾、险判 filler，留它是因为「而非小修小补」是一条被拒方案护栏（未来改动禁走小修小补）。git 史实佐证无沉积可删：3 commit 中正文只在创建时写过一次，后两次分别是「腿→引擎」纯文案替换与加 Status 头，无任何被后续覆盖却留下的旧层。

### 0002-midscene-not-driven-by-gpt55.md
- 增长史:2 层增长：44d915d（Initial checkpoint）一次性写全正文 25 行；06647f6（Status 头体系）唯一改动是在开头补 `> **Status:** Accepted` 一行、正文一字未动。无「后层覆盖前层的旧描述层」，无逐层叠加的施工括注——SEDIMENT 作为「构建累积函数」在此文件没有形成材料的机会。
- 判无锚定:最险成候选的是「核心事实」节末的『诚实存档（本 ADR 的判断反复）：Responses-only → 中途误判为"支持 chat-completions"（被假 200 骗）→ 实测纠正回不支持…』一句——它叙述了一段判断反复时间线，表面像施工叙事（判断反复的过程节奏），本应报 SEDIMENT。但它被两个受保护要素留下：(1) 该句以可复用反模式/教训收尾『只认响应 body，不认 HTTP 状态码；web 核实 ≠ 账号实证』（红线护栏「反模式」），而前半的反复叙事正是这条教训的具体接地（删了叙事，教训就悬空失去「为何得出此戒」的支撑）；(2) 它是 Accepted ADR 内联的自包含证据——正文核心结论「gpt-5.5 不支持 chat-completions」反直觉（AWS 曾返回假 200），此块解释了为何该结论可信（一度被假 200 骗、实测纠正），属「值得让 ADR 长一点」的内联证据。git 史实进一步坐实非沉积：2 层增长、正文在 44d915d 一次成文、唯一后层 06647f6 只前置了 Status 头，零旧描述层被覆盖、零施工括注叠加。

### 0003-midscene-grounding-qwen3vl-bedrock.md
- 增长史:6 层增长：初始 44d915d（19 行）→ 2a89750 & 5095ec0 两次仅原地改 recipe 路径串（目录扁平化 + v1.0 迁移）→ 06647f6 加 Status 头并改 env key（MIDSCENE_MODEL_FAMILY→MIDSCENE_USE_QWEN3_VL）→ 后两层 eba7cb5、75d91d1 均对第一段 region 描述做整段重写（先「项目统一 us-east-1」→「spike 用 us-east-1 + region 全可配」，再讲清 us-east-1/us-west-2 归属消矛盾并加 0012 回链）。所有重写都是原地替换、无旧层残留。
- 判无锚定:git 层读：region 段经 eba7cb5、75d91d1 两次整段重写且均原地替换——eba7cb5 结尾的「下方历史实测记录中的 us-west-2 是当时核实所用」尾句在 75d91d1 被整合进「唯 qwen3-vl chat-completions 的最初协议坐实在 us-west-2」子句，旧层无残留，非「覆盖未删」的沉积。最险成候选的具体句是第一段「唯 qwen3-vl chat-completions 的最初协议坐实在 `us-west-2`（06-22，见下方历史实测记录）」——它与文末「已在本账号实测（2026-06-22）…us-west-2…HTTP 200」的 region/日期表面重复，本可判 REDUNDANCY 完整重复；但它是带内部指针（「见下方历史实测记录」）的简短重述，作用是讲清 us-east-1/us-west-2 region 归属、消解本 ADR 早期版本的内部矛盾（75d91d1 主观类明列「region us-east-1 vs us-west-2 冲突→讲清归属」），命中红线护栏「有意重复（带指针简短重述）」，故留、不提案删。其余每句各承载唯一受保护要素：段首「承接 [0002]」+「Qwen3-VL 235B」是决策本身、「planning 也复用…见 0012」是带指针跨切面重述、「region 全可配…fail-loud、不兜 east——见 0016 决策 C/0033」是不变量+精确指针；「> 注：字段被接受≠成功视觉应答（占位图被 sanitize 拒为 400）」是护栏式 caveat+内联证据；「被排除的替代」整段是被拒方案；「接线要点」三条是与直觉相悖的不变量/gotcha；「已在本账号实测（2026-06-22）…HTTP 200」是 Accepted 内联证据；「未实测项…按 [0009] 在 AWS 内寻找改进」是 open question+决策+指针。

### 0007-programmatic-login-hitl-as-escape-hatch.md
- 增长史:2 层增长、无内容层被覆盖：44d915d 初始一次成形全部 13 行正文（motivation/决定/为什么不 HITL/spike/范围前提），06647f6（Status 头体系那轮）对本文件仅新增一行 `> **Status:** Accepted`、正文一字未动。故不存在「被后续迭代覆盖却没删的旧描述层」，也无逐层叠加的施工括注——SEDIMENT 的两个典型信号在 git 层面结构性缺席。
- 判无锚定:全文 6 行正文逐句均承载受保护要素，无一条可压：line 5 是 why（无人值守/可重复 vs HITL 天然冲突的定调 motivation）；line 7 首 bullet 是决策本身 + 精确指针（`nova.page`、`AgentCoreBrowserSessionProvider(profile=...)`）+ 不变量（「敏感数据不进 AI prompt」）；line 9 是 HITL 降级决策；line 11「为什么不是把 HITL 当一等公民」是被拒方案 + trade-off（红线明确保护）；line 15「范围前提」含指向 0001 的精确指针 + 重议 HITL 的触发条件（决策脉络）。唯一带施工叙事气味、最险成 SEDIMENT 候选的是 line 13 spike 段「第一根穿刺针用无登录站点（维基百科），完全不碰认证……登录代码留到接入真实被测系统时再写」——但它留下不是因为「差不多」：它承载 (a) 有意 defer 决策「本 ADR 只定方向，登录代码留到……再写」（正合 Accepted「有意 defer 但决策不变」）与 (b) 设计 why「避免登录复杂度污染链路验证」，属「为何这样设计」而非「分几步/施工节奏/过程编号」，故按 SEDIMENT 留/删边界判留。加之 git 层读证实（见 growth_summary）：本文件正文自 44d915d 一次成形后从未被后续层覆盖，无旧描述层残留、无叠加括注，沉积无处可藏。

### 0009-maximize-aws-hard-constraint.md
- 增长史:3 层迭代、零大改：初始 checkpoint（44d915d）一次性以 12 行落地全部内容，后两层仅术语统一（53b6fc9「两条腿」→「两个引擎」纯文案）与补 Status 头（06647f6），无内容叠加、无旧描述层被覆盖残留——born-fully-formed。
- 判无锚定:git 层读证实零沉积：3 层增长中初始层即完整成形，第 2 层纯替换术语（两条腿→两个引擎）、第 3 层只加 Status 头，无一层覆盖或叠加于前层的旧描述之上，故无「被后续迭代覆盖却没删的旧层」可清。最险成候选的是第 12 段 gpt-5.5 括注（「它在 Bedrock 内、但不支持 chat-completions，见 0002，与本 AWS 约束无关」）：形似离题填充，实为约束边界澄清——防读者把 gpt-5.5 的排除误归因于本 AWS 硬约束，且带指针指向 0002，属精确指针+被拒方案辨析，受保护故留。「明确的非目标」段（即便实测 AWS 内方案更差也不以离开 AWS 为默认出路）看似与「决定」段重复，实为预先框定未来 trade-off 的立场，非重述而是延伸不变量，不砍。

### 0011-agentcore-browser-system-default-vs-custom.md
- 增长史:2 层增长、无大改层：layer1（44d915d Initial checkpoint）一次性建全 13 行正文；layer2（06647f6 文档质量复盘）仅在首行后插入 `> **Status:** Accepted` 一行、正文一字未改。沉积机制（旧描述层被覆盖未删 / 逐层叠加施工括注）在此文根本没发生。
- 判无锚定:git 层读证实：本文 2 层增长中 layer2 只加 Status 头、正文零改（diff 仅 +2 行 `> **Status:** Accepted`），故无「被后层覆盖的旧描述层」也无累积括注，快照即全部真值。逐句判后有两处险成候选但均因具名要素留下：(1)「何时重议」节的「大概率要从 aws.browser.v1 切到自建 browser 配 VPC」一句表面与「决定」第二 bullet（内网/VPC 时切自建、重点 --network-configuration）重复，险判 REDUNDANCY——留下因它服务的是不同结构功能「留作未来需求的指针」（触发重议→另立/更新 ADR 的过程信号，非当下决策规则本身），且属护栏保护的「带指针的简短重述」、git 证实无漂移；(2)「自建 custom browser」bullet 列出 --enterprise-policies/--execution-role-arn/--browser-signing 三个决定正文未再引用的 flag，险判 filler——留下因这是「2026-06 本账号实查确认」的 Accepted 内联证据，且在「系统默认 vs 自建」这一 ADR 主命题下，穷举 custom 能力清单正是「为何值得切自建」这一 trade-off 的事实基座（--recording/--certificates 已被「何时重议」引用为审计录像/自定义证书），删之伤前瞻完整性。末句「与 [0007] 一样，都属接真实系统阶段才落地的事」是指向稳定 ADR 的精确交叉引用，受保护。

### 0012-planning-shares-qwen3vl-no-text-planner.md
- 增长史:4 层：首 commit（44d915d）即整篇生出（为什么不是/决定/何时重议/探针 四节齐全，26 行），后 3 层无一动内容——2a89750 与 5095ec0 各改探针那一行的路径串（midscene/spikes/midscene-sigv4/→midscene/spikes/→engines/midscene/spikes/），06647f6 加 `> **Status:** Accepted` 头；即「诞生即定稿」型，无旧描述层被后层覆盖而残留、无逐层叠加的施工括注。
- 判无锚定:全篇逐句皆承载受保护要素，且 git 层读证实无沉积：这是「诞生即定稿」型 ADR——首 commit 44d915d 一次写全，后 3 层仅两次修探针路径串 + 一次加 Status 头，没有任何内容层被覆盖而残留（沉积的典型温床此处根本没发生）。最险成候选的是「为什么不是」节首句「最初设想：planning 不需要视觉，可挑一个 Bedrock 上推理强的纯文本模型（性价比更高）」——它形如「先想 X 后被实测 Y 推翻」的施工叙事句式，极易被误当 SEDIMENT 删掉；但它是被拒方案连同其动机（性价比）的框定，受红线护栏「反模式/被拒方案」保护，删了则整个「实测证伪」论证失去被反驳的对象。其余如「实测证伪（2026-06-23，本账号）」及点 1/点 2 里 `@midscene/core@1.9.8` 逐行核实、四个纯文本模型 + 400 错误码，均为 Accepted ADR 内联的自包含证据；「何时重议」两条是决策反转条件（trade-off）；探针节是精确指针。故零候选。

### 0019-feature-tags-scope-and-engine.md
- 增长史:6 层迭代（2026-06-24 建库 → 07-02 Status 头标准化），无一层留旧描述残留：首建时带「B 步做到哪 / 留给 C」过程编号与「已验证（B 步）」，第 2 层（03e0d21）即就地译为「语义已定 / 待 v1.0 核心库」「已验证（v0.x）」——SEDIMENT 的经典靶子（施工过程编号）在第二层被主动清掉；后续 4 层均为就地改写（补 0025/0026 指针、RunResult「未定→已定」校准、腿→引擎术语统一、Status 头体系），非叠加式堆积。
- 判无锚定:三处险成候选均因具名受保护要素留下。① 「已验证（v0.x，2026-06）」整节描述两套 runner（cucumber --tags / pytest-bdd conftest 转 marker）的旧消费机制——已被 0022「核心自解析」取代，快照读极易判为「被后续迭代覆盖却没删的旧描述层」（SEDIMENT）；但它受【历史框定】保护：节标题显式 v0.x 日期锚定，且 Status 头明写「下文『已验证』段描述的两套 runner 消费机制是 v0.x 形态」，同时作为「两个引擎可解析」决策的【内联实测证据】，属护栏「历史记录≠过时」，不删。② @engine 节第 27 行「双引擎交叉验证 = v1.0 不做（见下『双引擎的真实价值』）」看似与下方整节「双引擎的真实价值」完整重复，实为【有意重复=带指针的简短重述】（此处一句+见下指针，下方才是完整 trade-off 分析），属护栏保护模式、非 REDUNDANCY。③ 第 54 行「再次印证 [0005]：同一份 tag，两套 runner 各用各的方式消费」是跨 ADR 的【精确指针+简短重述】，非可删过场。git 史实佐证：6 层全为就地改写，若有 B/C 施工编号残留本会是本轮首个提案，但它在第 2 层已被译为稳定表述。

### 0021-local-cucumber-patch-step-keyword-disambiguation.md
- 增长史:4 层迭代、无大改层：2a89750（v0.x B轮）创建即五段定型全文（问题/方案/保守回退/版本约束&升级/重议，35 行），后续三层均为校准非扩写——03e0d21 加「⚠️基本作废」头、5095ec0 把升级命令路径 midscene→engines/midscene 校准、06647f6 把作废头标准化为 `Status: Superseded-by 0022`；无残留旧描述层、无逐层叠加的施工括注。
- 判无锚定:git 层读到的史实：4 层增长中主体一次成型（2a89750 创建即含五段），后续三次改动（03e0d21 加作废头 / 5095ec0 校升级命令路径 midscene→engines/midscene / 06647f6 作废头标准化为 Superseded-by 0022）全是正确校准，无被后层覆盖却留下的旧描述层、无逐层叠加的施工括注——沉积维度零命中。密度维度唯一险成候选：「版本约束 & 升级」段第 31 行升级重生成三步（改版本号→npx patch-package 重生成→提交新 .patch）+ 第 32 行 grep 验证补丁已生效，在补丁已 Superseded 退役后偏 operational how-to、险判过场；但因与第 29 行「必须精确 pin 13.0.0，否则 patch-package 静默跳过、无报错退回 ambiguous」构成同一「patch 绑版本」不变量+gotcha 的两面（受保护：不变量/why），且整段处于 Status 头「下文描述 B1 之前 v0.x 状态」的历史框定保护伞下（红线：历史框定不删），判留。此外「保守回退」段的「⚠️代价：错误声明关键字的 step 不会被揪出，可接受但记录在案」是明确 trade-off、「重议」段「退路是回到带关键词措辞」是被拒方案护栏，均受保护。

### 0023-novaact-acting-python-locked-no-ts-core.md
- 增长史:4 层迭代、无一层结构大改：03e0d21（v1.0 C 轮）生成即 36 行近完整成形；后 3 层全是表层微调——53b6fc9 纯术语 find-replace「两腿→两个引擎」、06647f6 只加了一行 `> Status: Accepted`、81fadc8 只把证据锚点措辞「本次→本 ADR」清理。git 层读证实：诞生即成熟，无旧描述层被后层覆盖却残留、无逐层叠加的施工括注。
- 判无锚定:最险成候选是「由此定下的核心语言原则」整节：它重述「两个引擎都子进程 + 核心选 Python」并两次指向 [0016]（标题「落地见 0016」+ 段尾「详见 0016」），险判 redundancy-带指针的完整重复；但它承载本 ADR 的决策收束因果链（Nova Act 锁 Python 这一证伪 → 必有一个引擎跨进程 → 刻意消除不对称 → 核心语言变低风险自由选择）+ 决策本身，且以「详见 0016」作简短指针而非搬完整副本，受「决策本身 + 有意重复（带指针简短重述）」保护而留。第二处险成候选是实查结论首条 bullet 里的括注「仓库语言占比来自先前调查、本 ADR 未复验：约 98.6% Python，零 TS/JS」，险判 filler 括注，但它是 Accepted ADR 的内联自包含证据且诚实标注了证据边界（未复验），受「Accepted 内联证据」保护。git 史实佐证零沉积：4 层增长中后 3 层均为术语/Status/锚点的表层替换，无任何被覆盖旧层残留、无施工叙事括注可删。

### 0025-plan-module-feature-to-jobs.md
- 增长史:9 层:首层全文一次成型,后 8 层均 1-9 行替换/精化,全是替换型编辑、旧层被覆盖即删,无叠加沉积。
- 判无锚定:最典型的 gherkin 版本描述层:d8b8f99 写「novaact worker 的 venv 另装 29.0.0」→ 75d91d1 完整替换成「novaact 子工程不依赖 gherkin-official」,旧描述零残留,是「后层完全替换前层」的干净迭代。险成候选:第三方库 seam 节末括注(区分本 seam vs 0024 Engine port 的决策边界澄清+精确指针,留);test cases 节(标题明写「护栏,本模块强制」的测试契约=决策本身,非重复,留)。
