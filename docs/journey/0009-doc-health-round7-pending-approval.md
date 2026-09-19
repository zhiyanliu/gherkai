> 类型: 待批报告（批毕落改吸收后删除）

# 文档健康度复盘 · 第七轮 · 待批报告

## 基线

| 项 | 值 |
|---|---|
| 锚点 | dfd867e（第六轮落地，trailer `Doc-Health-Round: 6`）→ HEAD 5a0feda |
| 审计集 | 45 ADR + CONTEXT.md；**动过 40 ADR + CONTEXT**（区间内有提交），**沿用 5 篇**：0006 / 0011 / 0012 / 0013 / 0021（自锚点父提交零命中） |
| 覆盖面 | 19 个文档分片（ADR 10 + CONTEXT + 人读层 8）× 9 个事实族横切 × 1 份 cross-ADR |
| 对抗验证 | 客观 **CONFIRMED 176 条**（分片与事实族原始 verdict + verifier additions 共约 200 项，按「同一处多来源」「同一退役名多落点」合并去重后计）· **REFUTED 7** · **UNCERTAIN 6**（净留 2；1 条经另一族独立核实转客观、3 条转主观/裁定） |
| 提纯审计 | 浮出 53 条提案 → 红线复核 **通过 43**（approve 26 / approve_reduced 17）· **否决 10** |
| 主观发现 | **43 条**（REDUNDANCY / SEDIMENT / TONE 主观面） |
| 请裁定 | 21 项（STALE ③ 类 1 · Status 枚举 3 · 术语与词表 10 · 其它 7） |

沿用说明：0012 / 0013 虽文档未动，但 **code 动了**（0044 换默认模型、f536b5a 升 SDK），故其事实面本轮重审、只有提纯槽沿用上轮具名结论。

---

## 一、请裁定（21 项）

### 1.1 STALE ③ 类：code 偏离已定设计、无 ADR 记录（1 条）

**D1 · 推进器 Lambda 缺 events 表写权限**（`docs/adr/0033`:35 资源清单 10. / `deploy_aws/gherkai_deploy_aws/stack.py`:650）

- 文档与 IaC 一致（events 表**只读**：`self._events_table.grant_read_data(fn)`），但 ADR 0034 有两处 Accepted 机制**必须写** events：机制二推论「launch 失败补偿」（`core/gherkai_core/reconcile.py`:117 `record_exit(scope_id, PLATFORM_FAILED_EXIT)`）与「job timeout」cloud 档（`lambdas/reconciler.py`:189/:202 `record_exit(...)`），落地即 `put_item`（`adapters/event_log/ddb.py`:130）。
- 护栏照不出：moto 与 CDK synth 都不校验 IAM，`test_stack.py` 只断言 exit-observer 一侧的动作集，`test_reconciler_and_kicker_have_the_same_permission_face` 只比两者相等。全绿。
- **复盘方倾向 = 补授权（0034 的设计更合理）**：① code 侧照 exit-observer 那款窄模板加 `iam.PolicyStatement(actions=["dynamodb:PutItem"], resources=[self._events_table.table_arn])`（**不用 `grant_write_data`**，它连带 Update/Delete/BatchWrite、破 0033「动作维度全最小」）；② 0033 资源清单 10. 的「events 表读」改「events 表读 + `PutItem`（launch 失败补偿与超时处置直写退出记录，[0034] 机制二推论 /「job timeout」节；仍不给 Update/Delete）」；③ 加一条按角色归属的动作集断言进 `deploy_aws/tests/test_stack.py`。
- 理由：0034 是 Accepted、两条路径已在 code 里且各有真跑依据（0034:156「不补偿则永停 RUNNING、整批不可恢复 wedge、三触发源都救不回」）；砍机制等于重开 wedge 形态，代价只是给推进器多一个最小动作，与 0033「IAM 最小权限」不冲突（worker task role 仍只有 events PutItem、不碰 runs 表，该红线不动）。
- 移交姊妹任务 `code-health-review` 的 VIOLATES_ADR 条接收。

### 1.2 Status 枚举变更（3 项）

| # | ADR | 建议 | 判据 / 备选 |
|---|---|---|---|
| D2 | 0012 | Accepted → **Partially-superseded-by 0044** | 结构性决策仍是 code 真值（`run-scope.mts` 的 `modelConfig()` 只给 default 槽、不设 `MIDSCENE_PLANNING_MODEL_*`，而该组键在 SDK 1.12.8 仍存在），但决策句钉死的 Qwen3-VL 已非现值；「何时重议」第一条已被 0044:12 的 2026-09 实查满足。备选：维持 Accepted、只把模型名改成「引擎默认模型（现值见 0044）」——不建议，0003 同类模型口径已判 Superseded |
| D3 | 0037 | Accepted → **Partially-superseded-by 0045（范围 = 决策 8 ④）** | 0045 决策五把 changelog 真源从 GitHub Release 正文移到根 `CHANGELOG.md`、各包 `[project.urls] Changelog` 改指它、发布链加一道「本 tag 在 CHANGELOG 有非空节」gate（`release.yml`:71 已实装），而两篇互相零引用。备选：维持 Accepted + 头末一句反向链 + 决策 8 ④ 就地历史注。倾向前者：本仓对「一个子句被反转」的既成处置正是范围限定的 Partial（0041 即此例） |
| D4 | 0005 | 倾向**维持 Accepted**（争议记录） | 决定的可执行内容（被加载的 .feature 是物理同一个文件、放 git 根 `features/`）一字未被反转，:5/:11/:15 三处已历史框定「加载方由双 runner 改为核心」。若 owner 判决定句里「被两套 runner 加载的」这一前提本身属被反转的实现细节 → 改 Partially-superseded-by 0022 + 注「结论存：单一物理共享 .feature；立场变：加载方改为核心库」 |

### 1.3 术语与词表（10 项）

| # | 项 | 现状 | 复盘方倾向 |
|---|---|---|---|
| D5 | 术语批范围：「钉版 / 钉死 / 旋钮」（CONTEXT:27/:285 `_Avoid_`） | 19 个 ADR、71 处；owner 0044 的**标题**即「默认钉版、按引擎 env 覆盖」，而引用方 0004 已被报为要改 → 只改引用方会让引用方比 owner 更规范 | 一次做完 19 篇，**按「术语名 vs 散文」分流**：作为术语名的短语（「默认钉版」「钉死的 id」「覆盖旋钮」「一个旋钮」）改词，纯散文动词（「SDK 版本钉死」「四个 context 旋钮」）按 0045 决策八保留。owner 0044 标题与 :17/:18/:52 同批 |
| D6 | CONTEXT:98 `_Avoid_: 维护者` 过宽 | 同一词条正文又花一句撤销它（「「维护者」不是它的同义词，只指 contributor 中负责发布的一侧」），ADR 0040:28 把它定为独立角色；全仓 33 处里十余处是**正确窄义**（GHCR 基础镜像发布侧） | 在「角色与权限」节给「**维护者 (maintainer)**」立独立词条（= contributor 中负责发布的一侧），并把 contributor 的 `_Avoid_` 收窄为「维护者（当 contributor 的同义词用时）」。否则每轮复盘与护栏都会把那十余处正确用法反复误报 |
| D7 | CONTEXT:238 `_Avoid_: 耗时` | 「耗时」在全仓 25 处作独立概念合法使用（含两页用户文档），而词表里没有可替换的规范词条（定义里指的「墙钟时长」全仓 10 处、无词条） | 从「成本可观测」的 `_Avoid_` 移除「耗时」（它不是「成本」的旧名）；若确要统一「墙钟时长」，先给它立词条再登记 |
| D8 | CONTEXT:85 `_Avoid_` 收裸词「探针」 | 词表自己在 :38 用「失败探针」，ADR 0044:15 同用 | 从 `_Avoid_` 删裸词「探针」（保留「骨架验证用例 / 骨架用例」），或把「失败探针」正名后再登记 |
| D9 | CONTEXT:236「成本可观测」 | 规范术语本身是谓词短语，而定义说它指一种性质；英文名 observability 已是名词 | 改名「成本可观测**性**」；传播面小（code 与文档未把它当字面 token） |
| D10 | CONTEXT:93「使用方」未登记「使用者」/「用户」 | 「使用者」全仓 124 处（0039「使用者向」、0045 读者类名）、「用户」在 ADR 里 150 处成族（0016「非用户档」「面向用户」），词表都未登记 | 登记同义、**不做机械替换**：词条标「**使用方 (consumer，指具体的人时写「使用者」)**」；「用户」整族（含固化复合词「用户文档」）一并定去向 |
| D11 | 「终止契约」（CONTEXT:194 `_Avoid_`，规范名 协作式停止） | 它同时是 0024:148 的**节标题**与 15 处跨 ADR/code 引用锚（含 `core/gherkai_core/ports.py`:46/:50）；所指粒度也不同（契约全文 vs worker 侧约定） | 二选一：(a) 判 `_Avoid_` 登记过宽 → 从词表移除该词、文档不动；(b) 确需统一 → 按 0045 决策八一次改 0024 节标题 + 15 处引用 + code 注释（同 commit）。**不做半程改名**。倾向 (a) |
| D12 | 「成本信封」（CONTEXT:238 `_Avoid_`） | 同上形态：0024 标题 / :15 / :96 / :118 节标题 / :262 + `core/gherkai_core/model.py`:72 | 同 D11，倾向 (a)（「成本信封」指 wire 上 `cost` 子对象的形状契约、「成本可观测」指性质，粒度不同） |
| D13 | 「云端档 / 本机档」= 词表未登记的自造简称 | README 4 处、configuration 2 处、getting-started:48 图注成对定义、图源 `readme-runtime-topology.json` 4 处、internals 3 篇 4 处；同页混用「云端后端」 | 二选一：(a) 统一改「本机后端 / 云端后端」（**须同 commit 改图源并重出 SVG**）；(b) 在 CONTEXT「执行后端」词条里给它一条正式简称。别两套并存 |
| D14 | 「框架」自指本产品 | CONTEXT:3 明写「故称工具不称框架」，但 16 篇 ADR 共 30 处自指（0013 六处、0005 两处最密）；其中至少 3 处指他方框架（0002:19/:25、0003:7），机械替换会改错 | 倾向批：CONTEXT:3 的命名理由在 ADR 面同样成立，人读层已清完、只剩 ADR 会让护栏永远逼近不到。施工约束三条：① 逐处筛掉指他方框架的用法；② Status 头与历史注里的引文保留原句或加「原话」框定；③ 替换词统一「工具 / 工具自身的代码 / 公共设施」 |

### 1.4 其它决策层面（7 项）

| # | 项 | 复盘方倾向 |
|---|---|---|
| D15 | 0016:70/:72 用「Ports & Adapters（六边形架构）」「ports 层」「类比 DAO 层」——四个词都在 CONTEXT:249 `_Avoid_` 上，但它们同时是业界模式名（删了丢掉 AI 读者的理解锚点） | 标题与首句改用词表名、业界名降为一次性括注不再复用：:70 →「## 留口子：核心注入接口（ports），组合根注入」；:72 →「收成一组**核心注入接口**（业界称 ports & adapters 模式，此处只借其形）…」；删「类比 DAO 层」（本项目已由「控制面/数据面」替代，见同文 :76-81） |
| D16 | 里程碑 `M1–M5` 裸编号：0005:13/:26、0010:30/:35/:37、0013:27、0016:46、0027:5 —— 第五/六轮保留它的依据（「CONTEXT 已立里程碑词条」）**已两头失效**（词表重写后无该词条；历史 CONTEXT 也从未定义 M 编号，原文指 v0.x 版本号） | 一次决定：全删坐标（每处仅去编号、结论与 why 一字不损，改法见第四节 S-M1..S-M8），或在 CONTEXT 重立词条。**不要只改 0010 一处** |
| D17 | 0012:14「两个集合不相交…只有 VL 模型」+「何时重议」闸门已被 0044:12 触发 → 是否重开「独立 planner」决策 | 客观部分（加时点框定 + 指针）可直接落（见第二节）。**是否重开 = 人拍板**；倾向**不重开**：拆 planner 多一个模型槽与一处可漂配置面（与 0044 决策 2「一个 env 一个槽」对称性冲突），当前默认模型已兼具推理与视觉、A/B 里 3 遍逐遍稳定，无可观测的规划质量缺口作驱动 |
| D18 | 0042:189「已知缺口」只写「两处」，而 0043:186① 记的第三处（有 step 记录时 explain 文本不打 scope 级判定行）在 0042 侧零痕迹 | 倾向在 0042「已知缺口与重议闸门」加第三条（自包含描述 + 触发信号）、把「两处」改「三处」，0043 那条压成指针——但涉跨 ADR 搬内容（红线），交人拍板。替代改法 = 0042 只加一行指针指 0043（但那会让 0042 依赖 0043 的验证节结构） |
| D19 | `docs/internals/cli-json-contract.md` 的归属：0041 决策五定位为「给使用者/agent 的参考层」，0045 决策一把 internals 整层归「技术文档 / 想懂机理的人」，CLAUDE.md internals 条又立了「只讲 how、立文门槛 = 跨多 ADR 的横切合成」 | 加归属注、**不搬页**：在 0045 决策一「技术文档」行或决策二补一句「`cli-json-contract.md` 是本层唯一的机读字段级参考页，读者含拿 `--json` 写脚本或 skill 的使用者；它是 skill 转换副本的手写源（0041 决策五、0043 决策四），不按机制解读的立文门槛判」。搬页代价远大于收益（源路径被 `tools/render_skill_contract.py` 与三个测试钉着，搬去 user-guide 还与「一个主题一篇 owner」和禁词口吻表打架） |
| D20 | CLAUDE.md:21 kebab-case「唯一例外」清单不闭合：清单已含 docs/ 外文件，但仓库另有 `SKILL.md` ×2（规范规定名、不可改）与 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md` 未登记 | 倾向：例外清单补「`SKILL.md`（agent skill 规范规定名）」，并把首句射程写清（「全 `docs/` 通用；`docs/` 外的 markdown 随所在工具/包的惯例命名」），把代码旁技术笔记显式划到射程外。规则内容属决策、不在复盘里改 |
| D21 | CLAUDE.md:30「维护者要的设计指针留在紧邻注释/docstring」与 0039 那五处同源（指 contributor） | 倾向随 0039 一并把「维护者」改「contributor」（只换角色名、规则一字不动）。因方法限定「CLAUDE.md 只查 DEADLINK / STALE、规则内容不在复盘里改」，请 owner 明确「一并改」或「显式豁免」，免下轮重报 |

---

## 二、可直接改（CONFIRMED 客观类，176 条）

> 每条都经对抗验证（先假定文档对、去 code 找反证）。长证据在括号里。同一处多来源已合并、标「(来源)」。

### 2.1 术语传播批（10 条批次 · 约 60 个落点；退役名作为术语名出现、CONTEXT `_Avoid_` 已登记 → 按 ADR 0045 决策八传播）

> **同一批必须一次做完**（只改一处会造新的跨篇不一致，见方法复盘 R-4）。「钉版/钉死/旋钮」那一批范围过大、单列裁定 D5。

| # | 批 | 落点（全量） | 改法 |
|---|---|---|---|
| 1 | 「跑法」→ 执行方式 / 执行后端 / 四种组合 | 0034:179、0035:3、0035:45、0037:100、0038:87、0038:94、0043:53、0043:119、0045:44 | 按三义落词：0035 两处「四种「跑法 × backend」组合」→「四种「执行方式 × 执行后端」组合」；0034:179「local（两种跑法）」→「（两种执行方式）」；0037:100 / 0038:87 / 0038:94「local 跑法」→「local 后端」；0043:53「唯一跑法」→「唯一的执行方式」、:119「两档的跑法」→「两档的执行方式」；0045:44「四种跑法细节」→「四种组合（执行方式 × 执行后端）的细节」。**0043:143「脚本的跑法」= 纯口语，留** |
| 2 | 「腿」→ 引擎 / 空占位项 | 0032:60（4 处）、0032:63、0033:170、0044:19、0045:38 | 「两腿…」→「两个引擎…」；0033:170「装空腿」→「装**空占位项**」（与 `compose.py`:986 注释同词）；0044:19「Midscene 腿」→「Midscene 引擎」；0045:38「「两腿对称」原则」→「「两个引擎对称」原则」 |
| 3 | 「皮 / 皮层 / 入口皮」→ CLI 前端 / 命令行前端 | 0016（5）、0027（4：3/26/28/169）、0029:84/:104、0030:68、0037:149（4）、0042（3：154/185/215）= 21 处 | 一次改全 5 篇（单改一篇即造新分叉）。0029:84「皮层对 `kind == "evidence"` 的 ref 解引用」→「命令行前端对…」；:104「入口皮」→「命令行前端」；余同 |
| 4 | 「基底」→ 执行环境 | 0028:137、0029:58 | 「因执行基底而异」→「因执行环境而异」（与 0032 标题用词一致） |
| 5 | 「锚点」（指确定性 step）→ 确定性 step | 0015:18、0015:25、0016:210、0022:42、0022:44（2）、0027:147、0036:26、0037:205（4）、0037:222、0038:147 | 0015:18「写了断言锚点」→「写了点名检查」；0015:25「粗粒度走 AI 锚点」→「走 AI 点名检查」；0036:26「engine 侧加/改锚点」→「加/改确定性 step」；0022:42「一个真实 URL 锚点」→「一条真实的 URL 确定性 step」、:44 两处同法；0016:210「内建脚手架锚点」→「内建示范的确定性 step」；0027:147 括注「@deterministic 锚点」→「`@deterministic` 注册的确定性 step」；0037:205 四处 / :222 / 0038:147 同法。**别义 6 处不改**（引用锚点 / 结论锚点 / `#fragment` / changelog 锚点）；**别把裸「锚点」加进 `RETIRED_TERMS_WORDS`**（会误伤那 6 处） |
| 6 | 「推进者」→ 推进器 | 0034:131、0030:150 | 「唯一本机推进者」→「唯一本机**推进器**」。**比较级构词不改**：0034:171/:182「与库中现态取较推进者」是「更推进的那个态」 |
| 7 | 「维护者」→ contributor（窄义保留） | 0039:16/:23/:36/:54/:60、0043:78/:80、CONTRIBUTING:61、docs/ai-eng/README:3、skills/README:3、evals.json:3 | 五处 0039 逐处换（:60 被拒方案只换角色名、理由原样留）；0043:78「由维护者在自己的部署上按需跑」→「由 contributor…」、:80「只有维护者与 AI agent 用」→「只有 contributor 与 contributor 侧 AI agent 用」；CONTRIBUTING:61「维护者与 AI 侧」→「contributor 与 AI 侧」；ai-eng/README:3「维护者也会读」→「人类 contributor 也会读」；skills/README:3 →「contributor 迭代这份 skill 用的评测资产」；evals.json:3 →「只由 contributor 在自己的部署上按需跑」。**十余处正确窄义不动**（GHCR 基础镜像发布侧：0037:36-42/136/138/140/233、0038:7/23、0009:9、0033:183、CONTEXT:273、internals/cloud-backend-carriers:13、engines/*/DEVELOPMENT:126、Dockerfile、workers.py:45） |
| 7b | 「开发者 / developer / 写 step 的人」→ contributor / 测试开发 | CONTRIBUTING:1、0040:34、0038:115 | CONTRIBUTING:1「# 开发者指南」→「# contributor 指南」（同文 :3 自述「本文面向 contributor」）；0040:34 引 0038 旧句「default 画像 = developer 兼…」→「一人兼测试开发与部署方两顶帽子」（0038:14 现文）；0038:115「写 step 的人不需要任何 AWS 写权限」→「**测试开发**不需要…」。**不改**：0009:18 / 0011:17 / 0035:7/:22/:35 指被测应用或开发机的开发者（0040:26 放行） |
| 8 | 「流程冒烟 / 探索性回归」→ 柔性冒烟 | 0015:1（标题） | 标题改「# v1.0 定位：柔性冒烟（只验业务意图达成），不是精确回归」；首段第 5 行点出术语名（「v1.0 的产品定位是**柔性冒烟**——锚定在"精确度光谱"的**最左档**」）。**文件名 slug 不动**（引用锚点，且 smoke-not-regression 与规范名相符） |
| 9 | 「执行档」→ 执行后端 | 0024:168、0024:252 | 「本机执行档 / cloud 档」→「本机后端 / 云端后端」（CONTEXT:116 `_Avoid_: 执行档`） |

### 2.2 ADR 事实面与指针（96 条，按文件）

**docs/adr/0001**（模型口径 5 条，全因 0044 换默认后回填不彻底）
| # | 行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 10 | :14 | STALE | 现在时断言「Midscene 的引擎模型是 Bedrock 上的 Qwen3-VL」（`agentcore-sigv4.mts`:36 = `us.openai.gpt-5.6-terra`；0003 已 Superseded-by 0044） | →「Midscene 的引擎模型是 Bedrock 上的多语种视觉模型（现值与选定依据见 [0044]「现值」），无此声明。」 |
| 11 | :22 | STALE | 「（[0003] 现用 Qwen3-VL）」；更险：当前默认恰属本句所说「被官方点名非拉丁文字定位偏弱」的 GPT-5 系 | 括注 →「（现用模型见 [0044]「现值」：`us.openai.gpt-5.6-terra`，其中文 UI 探针 3/3）」 |
| 12 | :33 | STALE | 中文 UI 量化实测两表（125 票）Midscene 列未标模型，读者当成当前默认（测于 2026-09-09 < 换默认 09-17） | 括注补「Midscene 侧为当时的默认模型 Qwen3-VL；换默认为 GPT-5.6 Terra 后由 [0044]「现值」的 A/B 中文 UI 探针复核、3/3 通过，票数粒度不及本表」 |
| 13 | :63 | CONTRADICTION | 「换默认 = 改常量 + 改 IaC 里 `bedrock:InvokeModel` 的模型 ARN pin 并重新部署」（`stack.py`:405-408 已是 foundation-model/* + inference-profile/* + project/default；0044:45 把「IaC 按模型 pin」列为被拒） | →「换默认 = 改 worker 侧 `DEFAULT_MODEL` 常量并随发版（IaC 的 `bedrock:InvokeModel` 已放到资源类型级、换模型不必重新部署，见 [0044] 决策 2）」，并删括注「（[0003]…段同口径）」（来源：分片 adr-models-auth + 族「版本·模型 ID·依赖锁」） |
| 14 | :67 | STALE | 「README 架构速览的范围句与「怎么写 `.feature`」节」两节名都不存在 | →「根 README「判定由谁做出」节末的语言句与 user guide「编写 `.feature`」页「按引擎选写法」节」 |

**docs/adr/0002 / 0003 / 0007 / 0009 / 0010 / 0011**
| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 15 | 0002:3 | STALE | Status 头末句「非拉丁文字定位弱项**正是** A/B 中文 UI 探针**要验的**」写成待验，A/B 已跑完 | →「…已由 0044 的 A/B 中文 UI 探针复核（GPT-5.6 三变体与 GPT-6 Astra 各 3/3，见 0044「现值」表）」 |
| 16 | 0003:23 | CONTRADICTION | 「**是否换默认按 [0044] 决策 1 的 A/B 定**」+ 复刻已被否的「按模型 pin + 云端部署侧放行」；与本文 Status 头「已改为 gpt-5.6-terra」文件内矛盾 | 整句 →「**默认已据 [0044] 决策 1 的评测集 A/B 换为 GPT-5.6 Terra**，换默认与覆盖的做法见 0044 决策 2。」（与提纯提案 P7 同一处，合并一次改写） |
| 17 | 0007:8 | CONTRADICTION | 「预置 AgentCore 托管 profile…**并复用 session**」与不变量「一个 scope 独占一个会话、不跨 scope 复用」正面冲突（SDK 真值：复用的是服务端登录态，会话每次新起） | →「…（`AgentCoreBrowserSessionProvider(profile=...)` 把 cookie/localStorage 持久化在服务端），让每个新会话启动时由服务端恢复登录态——复用的是服务端登录态，会话本身仍每 scope 一个、不跨 scope 复用（见 CONTEXT「AgentCore 浏览器会话」）」 |
| 18 | 0007:13 | STALE | 「登录代码留到接入真实被测系统时再写」——落点已由 0037 决策 4 定案（归使用方 `steps/`） | 末追加「**落点已定（演进）**：登录这类固定动作走确定性 step，代码归使用方项目的 `steps/` 目录（两引擎的 handler 都拿到 `ctx.page`），本仓库只内建示范、不内建登录 step——见 [0037] 决策 4。」 |
| 19 | 0009:12 | STALE | 战果清单「[0003]：Midscene 的引擎模型选 Bedrock 上的 Qwen3-VL」（AWS 硬约束论点与具体模型名无关） | →「- [0003] / [0044]：Midscene 的引擎模型在 Bedrock 内选（原默认 Qwen3-VL，2026-09 评测集 A/B 后改为 `us.openai.gpt-5.6-terra`），而非 AWS 外的模型。」 |
| 20 | 0009:15 | STALE | 「planning 角色复用 Bedrock 上的 Qwen3-VL 兼任」+ 括注依据「AWS 内「chat-completions + 收图像」的选项只有 VL 模型」已被 0044:12 实查证伪 | 整行 →「- [0012]：planning 角色由 Midscene 的引擎模型兼任（现值见 [0044]），不引入 AWS 外的多模态推理模型作独立 planner（当年依据是「AWS 内『chat-completions + 收图像』的选项只有 VL 模型」；2026-09 实查该集合已扩到 GPT-5.6 / GPT-6 / Kimi，但仍全在 Bedrock 内——离开 AWS 才有的选项按本约束不取，属需另立 ADR 的破例）。」 |
| 21 | 0010:14 | STALE | 「若两针…任何一针的改动都要同步另一针」——「穿刺针」已退役（CONTEXT:289 `_Avoid_`），同文 :5 已改「两个 spike」、此处漏改且改后无先行词 | 「两针 / 一针」→「两个 spike / 任何一个 spike」 |
| 22 | 0010:16 | DEADLINK | 「（见 CONTEXT「确定性断言 vs AI 断言」）」——词表重写已拆成两条独立词条，该标题零命中 | →「（两侧定义见 CONTEXT「AI 断言」与「确定性断言」两条；取舍结论已由 [0014] 落定）」 |
| 23 | 0011:7/:9 | STALE | 自建 custom browser 可定制项清单漏 `--filesystem-configurations`（真值 = `aws bedrock-agentcore-control create-browser help`）；但「2026-06 后新增」无法证实 | :7 括注 →「**两类（2026-06 本账号实查确认；可定制项清单 2026-09 按 `aws bedrock-agentcore-control create-browser help` 复核）**：」；:9 清单末补「、`--filesystem-configurations`（挂 S3 Files / EFS access point 进会话）」 |
| 24 | 0011:13 | CONTRADICTION | 「决定」二与「何时重议」只把「内网应用」导向自建 browser + VPC，而「运行命令那台机器可达」那一档已由 0035 的隧道兑现（仍用系统默认 browser） | 「决定」二后加一行：「  - **边界（演进）**：「内网」里凡**运行命令那台机器可达**的那一档，已由 [0035] 的隧道覆盖（`--expose-local` 的 origin 不限 localhost、目标机器零配置），浏览器仍用系统默认。代价是被测应用经第三方边缘节点暴露成公网地址（随机 URL + basic-auth + 每 run 一换 + 终态即拆）；组织不允许这种暴露、或需自定义证书 / 审计录像 / enterprise policy 时，才是自建 browser 配 VPC 的场合。」+「何时重议」段首句后插「（先读上条「边界（演进）」）」 |

**docs/adr/0008 / 0012**（SDK 1.12.8 升级后的源码内点与机制描述，根因 = f536b5a 未回头校准文档）
| # | 行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 25 | 0008:7 | DEADLINK | 「经核实 `@midscene/core 1.9.8` 源码：…（`service-caller/index.mjs:154-157`）」——装机版 1.12.8，该 index 里 `createOpenAIClient` 零命中（`wc -l` = 6 行 barrel），采纳逻辑搬到 `service-caller/openai-client.mjs` 的 `createAndWrapClient` | →「经核实 `@midscene/core` 源码（首验 1.9.8，装机版 1.12.8 复核仍成立）：…service-caller 会采纳你返回的 OpenAI client（`service-caller/openai-client.mjs` 的 `createAndWrapClient`，采纳返回值那段），底层 OpenAI SDK v6.3.0 支持自定义 `fetch`」（去行号、保血缘） |
| 26 | 0008:12 | CONTRADICTION | 「`MIDSCENE_USE_QWEN3_VL=true`（…**实际 MODEL_CONFIG 与 `SIGV4-FETCH-RECIPE.md` 用的是它**）」——`run-scope.mts`:151-164 给的是 `MIDSCENE_MODEL_FAMILY`，注释明写「取代旧的单一家族硬开关」，测试反向断言其不出现 | 键名部分 →「`MIDSCENE_MODEL_NAME` 与家族键（spike 期是 `MIDSCENE_MODEL_NAME=qwen.qwen3-vl-235b-a22b` + qwen3-vl 的 legacy 开关 `MIDSCENE_USE_QWEN3_VL=true`；现值与家族推断见 [0044] 决策 2，该 legacy 开关已列入其被拒方案）」；「虽是静态值…模型配置一并进代码」的 why 原样保留 |
| 27 | 0008:12 中段 + :31 | STALE | 「注入 `createOpenAIClient` 会让 Agent 切隔离 ModelConfigManager」——1.12.8 的 `agent.js`:921 改三分支，只给 `createOpenAIClient` 走 `AgentScopedModelConfigManager`（委托全局、仍读 env）；`hasCustomConfig` 已 grep 零命中 | :12 中段 →「但我们经 `opts.modelConfig` 给配置即让 Agent 切隔离 ModelConfigManager（隔离态不读 env，详见下「关键实现坑」）」；:31 →「- **关键实现坑**（配方笔记 §7）：给 `opts.modelConfig` 即切隔离 ModelConfigManager——隔离态只读该对象、不读 `overrideAIConfig`/env，故模型配置必须随它一起给。（1.9.8 时给 `createOpenAIClient` 或 `modelConfig` 任一即切隔离；1.12.8 起只给前者会用 `AgentScopedModelConfigManager` 包住全局管理器、仍读 env——本项目两者都给，落在隔离支。）」**与 #47（SIGV4 §7）同源，须同 commit** |
| 28 | 0012:11 | DEADLINK | 「逐行核实**安装的** `@midscene/core@1.9.8` 源码…`llm-planning.js` 的 `plan()`」——装机 1.12.8，该文件不存在，真位置 `ai-model/workflows/planning/standard-planning.js`（机制与结论仍成立） | →「逐行核实源码确认（2026-06 首验 `@midscene/core` 1.9.8，装机版 1.12.8 复核仍成立）：planning 工作流（`ai-model/workflows/planning/standard-planning.mjs`）在两个消息分支都无条件附 `{type:'image_url'}`，`includeLocateInPlanning=false` 不去图、只改 system prompt 与定位解析」 |
| 29 | 0012:14 | STALE | 「能被 Midscene 调用（chat-completions + 收图像）的 Bedrock 模型 = **只有 VL 模型**」已被 0044:12 的 2026-09 实查证伪（客观部分；是否重开 planner 决策见 D17） | 「= 只有 VL 模型」后加「（2026-06 的真值；2026-09 起 Bedrock 上的多模态推理模型如 GPT-5.6 / GPT-6 也能经同一接线收发图文，见 [0044] 背景 2）」；「何时重议」第一条注「该条件已于 2026-09 满足，默认模型本身即多模态推理模型；是否拆独立 planner 尚未重议」 |
| 30 | 0012:18 | STALE | 决策句钉死「planning 复用 Qwen3-VL（`qwen.qwen3-vl-235b-a22b`）」 | →「planning **复用同一个引擎模型**（本 ADR 成文时为 `qwen.qwen3-vl-235b-a22b`，现值见 [0044]），即不设 `MIDSCENE_PLANNING_MODEL_*`，让 default/grounding 模型兼任 planning。」 |
| 31 | 0012:24 | STALE | 「何时重议」第二条举「AWS 外的多模态推理模型（如 OpenAI 原生 gpt-5.x）」——该例已不是「AWS 外才有」 | 例子加时点框定：「（2026-06 的例子是「OpenAI 原生 gpt-5.x」；2026-09 起 GPT-5.6 / GPT-6 在 Bedrock 上已可经现有接线调用，见 [0044] 背景 2——这类模型不再需要离开 AWS，本条只剩「AWS 外独有的模型」这一射程。）」与 #29 的注合并成一处 |

**docs/adr/0013 / 0014 / 0016 / 0019 / 0022**
| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 32 | 0013:18 | STALE | 共享矩阵「模型调用｜OpenAI chat-completions（Qwen3-VL）」括注模型名已非现值（该格承重的是协议差异） | 括注 →「（Bedrock 上的视觉模型，现值见 [0044]）」 |
| 33 | 0014:20 | STALE | 「**当前**仅 1 个对 AI 友好的用例…各 10 次零抖动」快照已被超过（0001 有 125 票、0044 有每模型 9 scenario × 3 遍） | 「当前仅 1 个」→「本 ADR 定稿时只有 1 个」；可选接一条指针「此后抖动数据已累积（见 [0001] / [0044]），结论仍是抖动不是主导风险」。**「不足以反推 AI 断言在难场景可靠」的论证与 [0010] 指针原样保留** |
| 34 | 0014:25 | CONTRADICTION | 「`total==1` 时渲染隐藏投票 tally」写成全局规则，而 `explain` 的 step 行有意总显（`render.py`:382 无条件显） | 末句 →「`total==1` 时 `run` 的人读输出与报告页隐藏投票 tally、`>1` 才显（机器可读层始终保留完整 votes；`explain` 的 step 行有意例外、总显含 `1/1`，见 [0042]）。」 |
| 35 | 0016:39 | STALE | 数据模型表两症：Scenario 行「pass/fail」漏 `error`（同表 Step 行与 :63 都是三态）；「原生报告引用」只挂 Scenario 行，而两引擎都不填 `scenario_done.reportRefs`（已下沉 step 与 scope 级，0027/0042） | 三行齐改：Step 行「pass/fail/error」→「passed/failed/error（+skipped，带 `shortcircuited`）」并补「原生报告引用（两引擎 evidence + Nova 每 act trajectory，见 [0042]/[0027]）」；Scope 行补「原生报告引用（Midscene report + Nova session 汇总）」；Scenario 行「pass/fail」→「passed/failed/error（三态，见 [0024]「`status` 三态」条）」、「原生报告引用」→「原生报告引用（字段保留、当前两引擎都不填——已下沉 step 级与 scope 级，见 [0027]/[0042]）」（来源：族「状态枚举」+ 族「事件类型」） |
| 36 | 0016:125 | STALE | 「`--backend {local,cloud}`…`run`/`submit`/`status` **三个**子命令都有」——真值 5 个（另 explain / doctor） | →「`run`/`submit`/`status` 有，读判定的 `explain` 同形（[0042] 决策四）、`doctor` 也收它但只切换查哪些检查项、不注入 store（[0041] 决策四）——」；其后「backend 须一致」「`plan` 不加」两句不动 |
| 37 | 0016:176 | STALE | 「`--backend cloud --no-report`…**此组合跳过一切云端检查**」——决策 A 下它仍在 Fargate 执行，skew 闸 / events 表·cluster·桶·task-def preflight / variant 解析 / subnet-sg SSM 读取照常 | 该条改为：「…**但决策 A 下它仍在 Fargate 执行**，故云端检查只减 store 那一半：store 侧校验/import/异常 gated 在 `need_cloud = do_report and cloud`、runs 表也只在 `do_report` 时探；版本 skew 闸、events 表/cluster/桶/task-def 的 preflight、worker variant 解析与 subnet/sg 的 SSM 读取照常执行；`--no-report` 在 cloud 档另经 `build_fargate_engines(no_artifacts=True)` 让 worker 不生成/不上报原生产物（[0037] 决策 3）。」 |
| 38 | 0016:204 | STALE | 布局树 `deploy_aws/` 行把模块挂在目录名下、缺 import 名层（其余四成员都给了），读者会拼出不存在的 `deploy_aws/stack.py` | 行内最小插入：「← 发行包 gherkai-deploy-aws：AWS provider（**import 名 `gherkai_deploy_aws/`**：`stack.py`/`app.py`=CDK · `names.py` · `cli.py`=Provider · `lambdas/{reconciler,exit_observer}.py` 作 Lambda asset 原料 · `workers.py`/`container.py`=worker 镜像族与容器引擎口，[0038]）」 |
| 39 | 0016:207 | STALE | midscene worker 花括号清单 6 项漏 `error-text.mts`（真值 7 个非测试模块；它是活模块、`run-scope.mts`:41 与 `evidence.mts`:26 都 import） | 清单补 `error-text`，括注「（失败原因压成一行有界文本，与 Nova 侧 `run_scope._error_text` 对称，[0042]）」。**若提纯提案 P28（折叠引擎叶子）获批，本条并入该提案** |
| 40 | 0019:5 | CONTRADICTION | 开篇「声明**两类**配置元信息」vs 同文 :50「定 `@scope:`/`@engine:`/`@timeout:` **三个** tag 的语义」（`scope.py`:28-30 恰三条前缀） | 首句 →「QA 在 `.feature` 里用 **Gherkin 原生 tag** 声明三类配置元信息：会话作用域（scope，G1）、引擎选择（engine，G2）与 job 墙钟预算（timeout，随 [0034] 加入）。」G1/G2 编号与 H1 标题、文件名不动 |
| 41 | 0022:47 | STALE | 确定性 step 示例块注释「# novaact worker 内」与紧邻上文「写进使用方项目的 `steps/` 目录」矛盾；捕获组用了 code 明确警告过的贪婪 `.+` | 注释 →「# 使用方项目 `steps/*.py` 内（midscene 侧对称、写进 `steps/*.mts`）」；两处 `(?P<pattern>.+)` / `(?P<sel>.+)` → `[^\"]+`（与两引擎内建示范一致）。**别改示例的 step 措辞「当前 URL 匹配」**（假想的使用方 step，不该拉平成内建的「页面地址匹配」） |

**docs/adr/0024 / 0025 / 0027 / 0028**
| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 42 | 0024:122 | STALE | 「两者不会真并发写（per-run 崩了 status 才顶上、串行接替）」+「设计上假定同一时刻至多一个本机进程在推 local run」——`status --wait` 不探活、一律自己推进（`__main__.py`:1550 无条件 `drive_local_reconcile`），两者可并存 | 前提句 →「两者可能同时在推同一个 run（`status --wait` 不探 per-run 进程存活），跨进程写同一 events sink 由 SQLite WAL 写锁串行化、重复推进由 tick 幂等与 job 的 CAS claim 挡住」，删「不会真并发写」与「至多一个本机进程」两句断言（安全性论证原样保留）。**与 #109（CONTEXT:175）同源，须同 commit** |
| 43 | 0024:168 | TONE | 错字：「要**靛** ADR 影响面提醒把 25 s 改成 31 s」 | 「靛」→「靠」 |
| 44 | 0024:195 | STALE | 「两个引擎…**均 `JobSource.from_env().read()`**」——TS 侧是 `fromEnv()`，按 `from_env` 在 midscene 里 grep 零命中；该句排在「非逐字签名」免责句之前 | 末句 →「——两个引擎 `run_scope.py`/`run-scope.mts` 均在 main 早期由注入 env 造出 `JobSource`/`EventSink`，再 `read()` / `emit()`（工厂名随语言惯例：Python `from_env()`、TS `fromEnv()`）。」:199/:200/:203/:235 在免责句射程内、不动 |
| 45 | 0025:14/:23 | STALE | 接口块列 `timeoutS`，:23 又断言「输出 `Job[]` = [0024] 协议输入形状」——`wire.job_to_json` 只序列化 scope/engine/scenarios/assertionVotes，worker 不消费 timeout | :14 行内注补「；属 definition 层、**不进 worker 的 job line**（worker 不消费 timeout，见 [0034]）」；:23 首句 →「**输出 `Job[]` 承载 [0024] 协议输入的全部内容（definition 层的 `timeoutS` 除外，不上线）**」 |
| 46 | 0025:128 | CONTRADICTION | 「留口子不实现」写「feature 级 tag 的更多语义（现仅 `@scope`/`@engine`）」——本模块自己就实现了 `@timeout` 的继承/冲突/非法值校验 | 括注 →「（现仅 `@scope`/`@engine`/`@timeout`）」 |
| 47 | 0027:65 | CONTRADICTION | 「消费端（cli/WebUI）只当 URI 用、不 stat/open。」无限定，与同篇 :26 按层收窄后的表述及 code 矛盾（`compose.read_resource` / `explain` 对 `kind == "evidence"` 解引用） | 末句后接「——**唯一例外**是皮层 `explain` / `compose.read_resource` 对 `kind == "evidence"` 的自有 schema ref 解引用（见上 `ref` 条）。」（只指同篇、不新增 0042 链，保 Status 头「正文两处」计数成立） |
| 48 | 0027:70/:87 | DEADLINK | 两处引「[0016]「worker⊥store」」——0016 全文无该串（真条名 :89「worker 产物持久化 ⊥ store」） | 两处引号内条名 →「worker 产物持久化 ⊥ store」 |
| 49 | 0027:74 | STALE | 「`RunPersistence.finalize` 在 commit point 之后才调 `ReportStore.write`」——RunReport 现有第二个写者（推进器经 `reconcile.finalize_report` 在 CAS 之后写），而 0027 是 RunReport 的 owner ADR、全篇未提 | 该 bullet 末补「（无状态批量运行路径同守此序：RunReport 由推进器在 `try_finalize` CAS **之后**经 `reconcile.finalize_report` 写、同一失败隔离，见 [0030] 决定三与 [0034]）」 |
| 50 | 0028:50 | STALE | 「码集**对齐** botocore 权威常量…判定对齐、无内部 API 依赖」——code 另有一处**有意增补**（`ServiceUnavailable` / `ServiceUnavailableException`，botocore 靠 503 兜、只给码时兜不住），按字面执行「对齐」会删回去 | 条末补括注「（**一处有意偏离**：另补 `ServiceUnavailable`/`ServiceUnavailableException`——botocore 靠 `_TRANSIENT_STATUS_CODES` 的 503 兜它，服务端只给码不给 HTTP 状态时兜不住，故显式列入；勿按「对齐」删回）」 |
| 51 | 0028:62 | STALE | 建连阶段识别只给 Python 签名，Midscene 对称实装未写（读者判不出另一侧有没有） | 后补「**Midscene 对称**：`isTransientNetwork(e, connecting=false)`，建连域按 message 精确匹配 `has been closed`（TS 侧 Playwright 无稳定异常类可 `instanceof`，故按文案而非类型），越过建连域同样不认。」 |
| 52 | 0028:124 | STALE | 「具体 grace/act_timeout 值真跑标定」读作待办——已由 0032「真容器校准结论」标定 | →「具体 grace/act_timeout 值**已真容器标定**（见 [0032]「真容器校准结论」：`stopTimeout=120`、Nova 下限 150、Midscene 下限 31）；此前 10s 远小于任何合理 act_timeout。」 |

**docs/adr/0029 / 0031 / 0032**
| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 53 | 0029:31 | STALE | 组合根职责表只列两项，漏第三项：`--no-report` 时另注 `GHERKAI_NO_ARTIFACTS=1`（两档对称）；读 0029 会以为「注入了落点就必然有上传」 | 该行补「③ `--no-report` 时另注 `GHERKAI_NO_ARTIFACTS=1`（local/cloud 两档对称；**cloud 档 S3 落点照旧注入**）——worker 不产原生产物、也就无可传，与本 ADR 的落点注入正交（[0037] 决策 3）」 |
| 54 | 0029:82 | STALE | 接口形状写 `flush(dir)`，真名 `flush_and_cleanup` / `flushAndCleanup`（同篇 :90 已用真名、自相矛盾；反引号形态会被当符号 grep） | →「`flush_and_cleanup(dir)` / `flushAndCleanup(dir)`」 |
| 55 | 0029:87 | STALE | 「step 内判定现场证据上传失败 → 报错、**worker 非 0 退出**（`engine_error`）」——失败被 `_run_step` 的 except 接住成 `step_done{status:error}`，`main` 正常路径恒 `return 0`；错误类型经 `_is_transient_network` 可判 `network_error` | →「**上传失败即抛、不吞**——落进该 step 的 act 异常分类，step 记 `status=error`（错误类型按 [0032]「上传失败处理」层1 细分：S3 网络瞬时 → `network_error`、AccessDenied 这类配置错 → `engine_error`）；若该 step 本已 error、重建 ref 时上传再失败，则只丢 `reportRefs`、error 事件照发。worker 本身仍正常退出——它是判定现场证据，悬空=报告坏。」 |
| 56 | 0029:105 | STALE | 同症在「第一期实现定论（**已实现**）」节：「上传错误分类 = `engine_error`…上传失败让 worker 可观测（**报 error / 非 0 退出**）」 | →「**上传错误分类 = 不进重试域、不静默吞**：上传失败不进重试域（act 不幂等，[0028]），也绝不静默吞——step 内证据的上传失败落进该 step 的 `status=error`（错误类型细分见 [0032]「上传失败处理」层1）；scope 级 report/summary 的调用点已按同条层2 降 best-effort。worker 退出码不因上传失败改变。」（与 #55 同批、措辞对齐） |
| 57 | 0031:10 | STALE | 定位指针把「severity 单调聚合」说成 0030 的内容——0030 无此机制、code 也从不用 severity 做聚合（防倒退用 `_lifecycle_rank`，其 docstring 明写「与 severity 正交」）；两篇互指形成循环 | →「它怎么被实时落库（`update_job_state`，单写者一次写定该 job 终态）见 [0030]；detached 路径防态倒退用的是生命周期推进序（`project._lifecycle_rank`，pending<running<终态），见 [0034]。」决定二的「比较/单调升级一律用它」护栏不动 |
| 58 | 0031:71 | STALE | `TERMINAL_STATUSES` 引用方清单（以「另有一处取补用法」收尾 = 穷举承诺）漏 `explain` 三处、云端推进器 Lambda「已收尾 run 不再推演」闸门、worker 清理 pass | 括注 →「（CLI `status --wait` 轮询、`status` 退出码判定、`explain` 的「判定明细尚未落地」判断、隧道守护的拆除判据、云端推进器 Lambda 的「已收尾 run 不再推演」跳过判据（`lambdas/reconciler.py`）、worker 清理 pass 的「未终态 run 仍引用」检查——真值集即 `grep -rn TERMINAL_STATUSES`）」 |
| 59 | 0031:106 | STALE | 示意码 `_NON_VERDICT = (…)` 是 tuple，code 是 `frozenset` | →「`_NON_VERDICT: frozenset[Status] = frozenset({Status.SKIPPED, Status.ABORTED, Status.PENDING, Status.RUNNING})`」（局部名 `statuses`→`verdicts` 不必对齐，非契约） |
| 60 | 0031:187 | STALE | touch points 的 cli 行只写 `status`/`--wait`，漏 `explain`（同一枚举差集在本篇内第二次重演） | 末句 →「；`status`/`--wait` 与 `explain` 的终态判定引 `TERMINAL_STATUSES`。」与 #58 同批 |
| 61 | 0032:22 | DEADLINK | 「理由与措辞见 [0029]「act 边界提前上传」条『固有残余』」——『固有残余』是「上传时机」下的**兄弟条**、不在它之下 | →「理由与措辞见 [0029]「上传时机」『固有残余』条，不在此复述。」 |
| 62 | 0032:56 | STALE | 结论 4 写 Nova margin 60→30「留 ~1.5x 余量」，code 与包内文档都记 ~2x（30/15；1.5 只能由 30/21 得出，而 21 s 含本 ADR 结论 2 自己坐实的 ~11 s ECS 记录滞后、subprocess 路径不存在） | →「留 ~2x 余量（收尾预算 = 会话释放 ≤9 s + 截图队列退出档排空 6 s = 15 s；实测 21 s 里的 ~11 s 是结论 2 坐实的 ECS 记录滞后、subprocess 路径不存在，不计入分母）」。`60→30`、`下限 180→150`、Midscene 半边不动 |
| 63 | 0032:56 | STALE | 同行 `MIDSCENE_GRACE_MIN_S` 全仓 grep 零命中（反引号伪装成可查符号），且「两个下限常量…搬进各 worker、数值不变」对 Midscene 不成立（它被拆成六个收尾预算常量之和） | 「**Midscene `MIDSCENE_GRACE_MIN_S`：本次校准判 25 够用**」→「**Midscene 侧 grace 下限：本次校准判 25 s 够用**」；历史注 →「（两个下限当时是组合根 `compose.py` 里的常量；后按 [0024]「引擎自报下限」改由 worker 自报——Nova 续为 `NOVA_ACT_TIMEOUT_S + NOVA_GRACE_MARGIN_S`，Midscene 改为收尾各段预算之和、无单一常量，本次校准的数值不变）」（来源：族「数字类」+ 分片 adr-artifacts-resilience 的 UNCERTAIN 经独立核实转确定） |

**docs/adr/0033**（IaC 与命名契约，11 条；多为复刻期 / 裸 cdk 期残留）
| # | 行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 64 | :28 | STALE | 「可经 CDK context `-c stop_timeout=N` 覆盖」是包化前的裸 cdk 提法、无就地历史注（同节 :56 已用 `gherkai deploy --prefix`；仓库内已无 cdk.json、app 由 provider 现场生成） | →「可经 `gherkai deploy --stop-timeout N` 覆盖（provider 拼成 `-c stop_timeout=`，stack 侧仍读 context）」 |
| 65 | :28 | STALE | 同行「须与 cli `compose.task_def_name` 逐字一致」是复刻双写时代的人工同步契约；今 CDK 与 cli import 同一函数，且 `compose` 早已不在 cli 包 | →「须与命名真源 `gherkai_runtime.names.task_def_name` 一致——CDK 侧 `stack.py` 直接 import 同一函数（不再复刻，见下「两层命名」）」 |
| 66 | :29 | STALE | 资源清单 6.「ECR 仓库（2 个，各承一镜像）」是清单里唯一有名字却不给名的条目（`names.ecr_repo_name` 恒等于 task-def family） | →「6. ECR 仓库（2 个，各承一镜像）：名 = task-def family 名 `{prefix}{engine}-worker`（`names.ecr_repo_name` 恒等于 `task_def_name`，规则见 [0038]「概念模型」）。」 |
| 67 | :48 | DEADLINK | 「清理 runbook 见 `deploy_aws/README.md`「清理」节」——该 README 已按 0045 降为入口页、无此节（真身 `docs/user-guide/cloud-backend.md`:152「拆除与清理」） | →「清理 runbook 见 `docs/user-guide/cloud-backend.md`「拆除与清理」节。」 |
| 68 | :48 | STALE | 同行「`cdk destroy` 后表/桶/ECR **残留、需手动删**」把拆除入口写成裸 cdk（产品入口是 `gherkai destroy`） | 该半句 →「`gherkai destroy` 后表/桶/ECR **残留、需手动删**」（三条 aws cli 命令与 ECR 括注里那处讲 CDK/CFN 自身行为的 `cdk destroy` 不动） |
| 69 | :62 | STALE | 护栏条「若 `cdk deploy -c prefix=prod-` 但 cli 跑时用默认 `gherkai-`」与同节 :56 已改的写法自相打架 | →「若 `gherkai deploy --prefix prod-` 但 cli 跑时用默认 `gherkai-`」 |
| 70 | :76 | DEADLINK | 「（`deploy_aws/README.md`「VPC 三档」节有同一警告）」——入口页无此节（真身 `docs/user-guide/cloud-backend.md`:55，:67 逐字带同一警告） | 括注 →「（`docs/user-guide/cloud-backend.md`「VPC 三档」节有同一警告）」 |
| 71 | :102 | STALE | 「产物前缀一致性（存在性之外**唯一**的语义探针）」——preflight 另有一条：读推进器 `MAX_CONCURRENCY` env、声明超 cap 即提示 | 括注 →「（存在性之外唯一**会致失败**的语义探针，detached `submit` 专属；另有 `MAX_CONCURRENCY` 超 cap 提示、不致失败，见 [0034] 机制四）」 |
| 72 | :103/:104 | STALE | 「`FargateEngine.put_object` 打 `Tagging="gherkai=job-in"`」指了不存在的方法；:103 也漏了 detached 实际走的入口 | :103 →「`FargateEngine` 每 scope `PutObject` 一个 `jobs-in/<quote(scope_id)>.json` 对象（`_put_job_and_run_task`，`run_scope` 与 `start_scope` 共用）」；:104 →「`FargateEngine._put_job_and_run_task` 上传时打」 |
| 73 | :124/:128 | STALE | container 名契约锚在「cli 侧硬假定（`compose.container_name`）」+「CDK 作者读本 ADR、须照此建」——两处都是 CDK 独立工程时代的表述；今 `stack.py`:288 直接调同一函数 | :124 →「这是命名真源 `gherkai_runtime.names.container_name` 定的名，CDK 侧必须兑现，否则 cloud 每个 run 都炸」；:128 末句 →「CDK 侧 `stack.py` 直接调用同一函数（`add_container(names.container_name(engine))`），契约由共享命名真源结构性保证」。「为什么不带 prefix」「为什么是硬契约」与失败形态原样保留 |
| 74 | :127 | STALE | 「cli 的 `FargateEngine`」——它是 core 的执行 adapter（首次落地即在 `core/`，cli 包里无此符号） | →「core 的执行 adapter `FargateEngine`（`core/gherkai_core/adapters/fargate_engine.py`）」 |

**docs/adr/0034 / 0036 / 0037 / 0038**
| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 75 | 0034:139 | STALE | 「同步读端按「每个 item 都是事件行」取 `body`，读到 exit item 即 `KeyError`」当现存后果陈述——实装读端两处已把 SK 上界收在 `EXIT_SK - 1`，该 KeyError 结构上不可达 | 补「；实装的读端已把 worker 段 Query 的 SK 上界收在 `EXIT_SK - 1`（主循环与最终 drain 同一段界），故该 `KeyError` 现结构上不可达」；末句 →「不变量守在**写端**：同步读端的这类排除（现有的 SK 上界、或再加一层「非 `body` item 跳过」）都只是纯加法加固，不替代写端分流。」 |
| 76 | 0034:236 | STALE | 「不必给 `Engine` Protocol 强加 `start_task`」——该方法名全仓不存在，实装名 `start_scope`（同句前半刚写它） | →「不必给 `Engine` Protocol 强加 `start_scope`」 |
| 77 | 0036:56 | STALE | `model_id` 键的来路只给 Nova 的覆盖面、Midscene 写成「它的 Bedrock 模型 id」（读着像无覆盖面），且缺指向现权威 0044 的前向指针（0044 已反向指本条） | →「- `model_id` 是该 worker 起 job 时会用的模型 id——两引擎同律「默认锁定一个具体 id + worker 一侧 env 覆盖」，各自的默认值与覆盖 env 见 [0044] 决策 1/2；`doctor` 据此显示当前模型——覆盖过 env 的机器一眼可见。」（**勿用「钉死/旋钮」**，CONTEXT:27 已登记退役） |
| 78 | 0036:59 | STALE | 消费规则两处不准：① 说「当场核两个身份位」，code 还校验三个载荷键形态且不合契约时**不写缓存**；② 把三种失败都记在 `WorkerSelfDescribeError` 名下，而只有非零退出抛它（类名差别有行为含义） | →「**当场核契约**：两个身份位（`engine` 须等于所问引擎、`schema_version` 须是它认识的版本）+「5.」那几个载荷键的形态，**校验集中在这一处、不散到各消费者**，任一不合即 fail-loud 且**不写缓存**」；末句 →「query 失败一律 fail-loud、不降级、不回落常量：worker 非零退出抛 `WorkerSelfDescribeError`，输出非 JSON / 不合契约抛 `RuntimeError`；`run`/`submit`/`list-deterministic` 两类都退 2，match 查询侧则据类名区分「使用方 steps 加载失败不降级」与「环境问题降级为无标注」（见「4.」）。」 |
| 79 | 0037:73 | CONTRADICTION | 决策 2b「只有 `gherkai-core`（无兄弟 pin）不需要依赖 hook」——`engines/novaact` 同样只 `dynamic = ["version"]`、无 metadata hook；与同篇 2c 表「worker 讲协议、零 core 依赖」自相矛盾 | →「只有 `gherkai-core` 与 `gherkai-worker-novaact`（两者都无兄弟包 pin）不需要依赖 hook、只 `dynamic = ["version"]`」 |
| 80 | 0037:176 | STALE | 决策 8「tag 触发全链」的 gate 只列两项（漏 `release.yml`:71 的「CHANGELOG 有本版节」gate）；④「GitHub Release 作 changelog 锚点（`Changelog` 指它）」已被 0045 决策五反转（五个 pyproject 现指 `blob/HEAD/CHANGELOG.md`） | gate 句后补「（[0045] 决策五另加一道 gate：本 tag 在 `CHANGELOG.md` 必须有非空节）」；④ →「④ changelog 锚点 = 根 `CHANGELOG.md`（[0045] 决策五：各包 `[project.urls] Changelog` 指它、Release 正文由该版节 + 固定 footer 渲染；本 ADR 首版曾以 GitHub Release 正文为锚点、已反转）」。与 D3 的 Status 改动同批 |
| 81 | 0037:187 | STALE | 布局树 `deploy_aws/` 括注模块枚举漏 `workers.py`（push-worker 八步主体）与 `container.py`（0038:119「repo 内碰 docker 的唯一落点」） | 括注 →「（stack.py / app.py / names.py / cli.py=Provider / workers.py + container.py = worker 镜像族命令与容器引擎口子（0038）/ lambdas/ 两个 handler 源作 asset 原料）」 |
| 82 | 0037:212 | STALE | 「README·子 README·CONTEXT·**guides** 与 code 注释里的旧包名…已随各层校准」——`docs/guides/` 已改名 `docs/internals/`（0045 决策二） | →「`docs/internals/`（原 `docs/guides/`）」（同行括注「逐文件到期点见当时的 commit」另有提纯提案 P26） |
| 83 | 0038:37 | STALE | 自称「定制镜像模板（**唯一真源**）」的 Dockerfile 首行钉死 `FROM …:1.4.0`，而规则是「tag 须等于使用方 CLI 版本」（已发行到 v1.4.3；两处使用者面副本都写占位） | →「`FROM ghcr.io/zhiyanliu/gherkai-worker-novaact:<CLI 版本>`」，模板前补半句「基础镜像版本须与使用方 CLI 版本一致（`gherkai --version`）」。**:147 实测项里的 `:1.4.0` 是 v1.4.0 真账户实测的证据引用、属历史框定、不动** |

**docs/adr/0039 / 0040 / 0042 / 0043 / 0044 / 0045**
| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 84 | 0039:33 | STALE | 面二去向表首行称根 README 末尾「「深入了解」一节链 CONTEXT / guides / adr / DEVELOPMENT」——该节名全仓零命中，且 guides / 根 DEVELOPMENT 已改名 | 该格 →「仓库首页（GitHub）：门面 + 30 秒上手（agent 路径优先），末尾「文档」一节以表格指向 user guide 各页，并指 `docs/README.md` 地图（[0045] 决策四）」 |
| 85 | 0039:34 | STALE | 包 README 行「最多末尾一句「设计文档见仓库 docs/adr」」已被 0045 决策三反转（包页只留四样）；护栏拦不住（`\bADR\b` 未开 IGNORECASE，小写 `docs/adr` 不匹配） | 末句 →「…；末尾链 user guide 与 `CHANGELOG.md` 的绝对 URL（[0045] 决策三起：包页只留一句定位 / 装法 / 最小用法 / 这些链接，不再写「设计文档见 docs/adr」）」 |
| 86 | 0039:38 | STALE | 去向表末行两个载体都已不成立：Release 正文不再是 `release.yml` 的 `body:`（改由 `release_notes.py` 从 CHANGELOG 本版节 + footer 渲染）、各包 `Changelog` 不再指 Releases 页 | 该行按 0045 决策五重写（正文 = CHANGELOG 本版节 + `.github/release_body_footer.md`；`Changelog` URL 指 `CHANGELOG.md`；footer 链钉 `blob/vX.Y.Z/`） |
| 87 | 0039:45 | STALE | 护栏描述两处过时：「根与每包都有 `DEVELOPMENT.md`」（根已是 `CONTRIBUTING.md`，与同篇 :35 表行自相矛盾）、「Release 正文（`release.yml` 的 `body: \|` 块）」（测试已改读 footer 模板并反向断言无内联 `body:`）；且现还扫口头语与退役名两张表 | 整条按真值重写（根有 `CONTRIBUTING.md`、每包有 `DEVELOPMENT.md`；footer 模板零禁词零相对链接、链接钉 tag；release.yml 必须仍调 `release_notes.py check`/`render` 且不得有内联 `body: \|`；禁词之外另扫口头语与退役旧名两张表，[0045] 决策六/八） |
| 88 | 0039:68 | STALE | 重议闸门「contributor 内容与 **guides** 一并进站点」 | →「contributor 内容与 `docs/internals/`（原 `docs/guides/`）一并进站点」（不扩到 user-guide——那是 0045 才建的层） |
| 89 | 0040:3 | STALE | Status 头把「README「谁用它」表」当派生视图落点并写「改这里再改那里」——README 已无该表（真身 `docs/user-guide/getting-started.md`:5「按角色选安装形态」）；CONTEXT 侧节名是「角色与权限」 | →「派生视图在 `docs/user-guide/getting-started.md`「按角色选安装形态」表与 `CONTEXT.md`「角色与权限」节词条组，改这里再改那里。」（:63 同句同改，见 #91） |
| 90 | 0040:41 | STALE | 决策 3 把正交轴的派生视图指向「README「上手」的两个旋钮」——README 无「上手」节 | →「「产出什么」由帽子回答，「怎么跑」是另一根轴：执行方式（`run` / `submit`）× 执行后端（`--backend local` / `cloud`）两个独立的选择（使用者视图见 `docs/user-guide/running-and-results.md`）。」**别点该页节名**（实名「两个独立的选择：怎么运行、在哪运行」，易漂） |
| 91 | 0040:63/:91 | DEADLINK | 三处（含 :3）称派生视图为 CONTEXT.md「使用方角色」词条组——该节实名「角色与权限」，全文无此串 | 三处 →「`CONTEXT.md`「角色与权限」节的词条组」 |
| 92 | 0040:90 | STALE | 影响节三项都已不在 README：「安装前加「谁用它」表」「「帽子不是人」一句」（已被 0045 决策六有意反转、护栏 COLLOQUIAL 收了它）「「上手」开头加执行权限表」 | 整条改写为现落点：「用户文档（0045 决策一/二 归位后）：`getting-started.md`「按角色选安装形态」表承载帽子与安装形态、并以产品语言写「一个人可以同时承担多个角色」（隐喻「帽子不是人」按 0045 决策六不进使用者面）；`running-and-results.md`「两个独立的选择」节承载执行权限梯级表（不带 ADR 编号），角色表的「需要什么凭证」列指向它。」 |
| 93 | 0042:202 | TONE | 错字：「当时该下限是 `compose.py` 里的常量、**靛**本条提醒同步」 | 「靛」→「靠」（与 #43 同批） |
| 94 | 0043:20 | STALE | 「个人安装态不入库：`.claude/skills`（**已由 `.claude/*` 忽略**）」——`.gitignore` 现为反白名单三段，实际命中 `.claude/skills/*`；结论仍成立、依据失效 | 括注 →「（由 `.claude/skills/*` 兜底忽略；只有项目级 `doc-diagram/` 被反白名单放行，装进来的 `gherkai/` 仍不入库）」，`.agents/skills` 那半不动 |
| 95 | 0043:45 | CONTRADICTION | 决策三把任务域 C 的角色写成「部署方 / **维护者**」——把 gherkai 的发布侧当成使用方项目里的一顶帽子（skill 自己的角色表只列部署方/测试开发/QA·CI；镜像构建那步归测试开发） | →「（部署方，镜像构建那步是测试开发：`deploy` 交人、基础镜像同步…」 |
| 96 | 0043:79 | STALE | 决策七「资产位置」花括号清单 6 项，漏入库的 `summarize_runs.py` 与 `grader-prompt.md`（同 ADR 下一行列全 8 项、同篇两处不一致） | →「仓库根 `skills/gherkai-evals/` 入库（刻意在 CLI 包的发行树之外，隔离理由见决策一；资产清单与运行方法见下条）」（清单单一事实源留 :80） |
| 97 | 0043:108 | STALE | 「baseline 会读到 skill 想替代的全部原始教材（README、cli/README、**六篇 guides**、ADR…）」——`docs/guides/` 已改名、`docs/internals/` 现 7 篇 | :39/:74 的 `guides` → `docs/internals/`；:108「六篇 guides」→「`docs/internals/` 各篇」（去掉会随篇数漂的计数） |
| 98 | 0044:24 | CONTRADICTION | A/B 表头「每模型 7 个 feature / **9 个 scenario** × 3 遍」与同表「scenario 终态 30 / 0」算术不自洽（真值：`features/` 12 条 scenario、2 条 `@engine:novaact` → Midscene 侧 10，10×3=30） | 表头 →「每模型 7 个 feature / 10 个 scenario × 3 遍（`features/` 共 12 条 scenario，其中 2 条 `@engine:novaact` 不进 Midscene 侧），Kimi 6 遍」。Kimi 格 48+2+6=56 与 6×10=60 差 4，落地时按 A/B 记录确认后注成「56 个终态（4 条因 job 超时未跑到终态）」或只写「6 遍、56 个终态」不做因果断言。**同篇 :13 与 0004:33 的「9 个 Nova scenario」很可能是刻意排除必败的 zh-novaact 探针，勿顺手一起改**；改后建议在 :13 或 :24 一处点明两侧口径差 |
| 99 | 0044:35 | STALE | 「若使用方打开 `MIDSCENE_MODEL_REASONING_ENABLED` 成本会显著上升」——该键全仓只此一处、零消费者；worker 注入 `modelConfig` 后 SDK 走隔离配置**不读 env**（与 0008:31 互相矛盾） | →「reasoning 开关属 SDK 的 `MIDSCENE_MODEL_REASONING_*` 家族，而我们注入 `opts.modelConfig` 后 SDK 走隔离配置、不读 env（[0008]「关键实现坑」），故当前无法由使用方经 env 打开；将来若把它接进 worker 的 modelConfig，成本会显著上升」 |
| 100 | 0044:36 | 措辞 | Accepted ADR 正文两处用任务级指代「本轮」（「CloudTrail `inferenceRegion` 实查本轮全部落在 us-east-2」「本轮实测 global 反而慢约 20%」），与别处的「轮」撞义 | →「…在该批 A/B 里全部落在 us-east-2」「同批实测中 global 反而慢约 20%」 |
| 101 | 0045:21 | STALE | 决策一表把 `docs/ai-eng/` 括注成「REFERENCES 外部一手来源 + 两份 health-review 方法」——真值 5 项（漏 `diagram-authoring.md` 与 `README.md`，而同篇 :67/:33 自己正引用它们） | 括注 →「`docs/ai-eng/`（REFERENCES 外部一手来源 + 可复用方法文档；清单与 owner 见 `docs/ai-eng/README.md`）」——**不再钉份数**（这行已因钉「两份」漂过一次） |
| 102 | 0045:31 | STALE | 决策二 user-guide 页清单 8 项，真值 9 篇（漏 troubleshooting；faq 是 838e4af 后补） | →「- 新建 **`docs/user-guide/`**：从根 README 与各包 README 拆出的叙事与流程，一个主题一篇 owner；页与 owner 归属见 `docs/user-guide/README.md`。」（同一集合已在本文第三处列，改指 owner 表免再漂） |
| 103 | 0045:40/:48/:71 | STALE | 三处角色名前缺半角空格（「不链contributor 侧 AI agent 文档」「由contributor…」「给contributor…」）——「建造者 AI」→新名机械替换残留，同篇其余 6 处都带空格 | 三处各补一个半角空格 |
| 104 | 0045:44 | STALE | 决策四把根 README 上手第二条路写成「然后才是手敲 CLI 的**最小四步**」——README「自己敲命令」块恰三条命令（`plan`/`run`/`explain`），「四步」沿用了旧 README 的编号 | →「…；然后才是手敲 CLI 的最小命令序列（用例预检 → 运行 → 读失败证据）」（不钉步数；另：`getting-started.md`:127 恰有四步，同名不同物，更不该钉） |
| 105 | 0045:44 | STALE | 同行顺序枚举止于「文档去哪读」（漏「注意」「许可证」两节），且「注意事项全部链到 user guide 或 internals」与 README:85-88 就地留两条不符 | 顺序末补「→ 注意（只留费用与首次验证两条，其余链走）→ 许可证」，并把「注意事项全部链到…」改为「注意事项只留费用与首次验证两条，其余链到 user guide 或 internals」 |

### 2.3 CONTEXT.md（5 条；词表项另见 D6-D10）

| # | 行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 106 | :67 | TONE | `**票 / 投票 (vote / Voting)**` 英文名大小写不一致：全表 74 条里非专有名词大写仅此一处（d3b7675 立条时为 `Vote / Voting`，重写只小写了前半） | →「`**票 / 投票 (vote / voting)**`」 |
| 107 | :108 | CONTRADICTION | 「部署方…也是**唯一需要云端写权限**的帽子」——权威 0040:27 明文限定「唯一**因帽子本身**就需要云端写权限的帽子（执行所需权限按决策 3 另算）」；去掉限定后与同节「提交者」「执行权限梯级」两条自相矛盾 | →「负责部署与更新云端后端的帽子，也是唯一因帽子本身就需要云端写权限的帽子（执行用例所需的权限另按执行权限梯级取一档）。不拥有 worker 镜像的构建，只负责推送与注册（见 ADR 0040）。」 |
| 108 | :155 | STALE | 定位参数「查询命令须与**提交命令**逐项一致」把对照对象收成 submit——真值是「产生这个 run 的那条命令」（前台 `run --report-dir out/` 产出的 run，`status`/`explain` 同样要给）；照抄了 CLI help 那句不精确的提示 | 第二句 →「查询命令须与产生这个 run 的那条命令逐项一致（前台同步执行与提交后台执行都算），否则查不到这个 run。」 |
| 109 | :175 | STALE | 接力推进说本机后端「由查询方**亲自推进、离开即停止**」且把接力限定在「后台推进中断或停滞**后**」——`status --wait` 不检查 per-run 进程存活、一律自己也推到终态，两者可并存（今日提交 6d63003 已为 internals 与图做过同一裁定、未回头改词表） | 定义 →「等待终态的查询命令自己把 run 推进到终态的机制，兜住后台推进的停滞与中断。两个执行后端在此本质不对称：本机后端由查询方在本机执行同一段幂等推进、与后台推进进程可并存，仅当后台进程已终止时它才是唯一推进器、离开即停滞；云端后端只需唤醒云端推进链一次（见 ADR 0034）。」**与 #42（0034:122）同批，否则新造 CONTEXT↔ADR 矛盾** |
| 110 | :269 | STALE | worker 定位链「按同版本临时拉取发行包（**后两级仅 Python 引擎**）」——只有第二级（同环境模块）与第四级（uvx 兜底）限 Python，第三级（PATH 上的 worker 命令）两引擎都有（`_WORKER_BIN` 含 midscene；0037:112 明写那是 midscene 的第三级） | 最小改法：「（第二级仅 Python 引擎、第四级仅 Nova Act）」。**若提纯提案 P43 获批，整条枚举退回 ADR 0037、本条自动消解** |

### 2.4 人读层：使用者文档与 README（10 条）

| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 111 | user-guide/running-and-results.md:64 | CONTRADICTION | 「后端记一个版本戳…不一致即退 `2`」——比对是**非对称**的：只有 CLI 新于后端才 block，CLI 旧于后端只提示一行（同仓 cloud-backend.md:131 与 troubleshooting.md:109 都写对了） | 「不一致即退 `2`」→「CLI 比后端**新**时拒绝执行并退 `2`（新 CLI 写的任务定义旧后端读不懂，没有放行选项）；CLI 比后端旧时只打印一行提示、照常执行。」 |
| 112 | user-guide/running-and-results.md:76 | STALE | 反引号里的 `已选/总数` 是自造串（实际输出 `筛选：2/7 scenario（--tags smoke）`，全仓无「已选」） | →「筛掉一部分时命令会打印一行 `筛选：<已选>/<总数> scenario`，后面附上你给的筛选条件」 |
| 113 | user-guide/running-and-results.md:115 | STALE | 退出码表 `explain` 行的 `2` 格枚举漏「CLI 与后端版本不匹配」（`_explain_cloud` 第一道闸就是 skew gate，同表 status 两行都列了它） | `2` 格补「、CLI 与后端版本不匹配」 |
| 114 | user-guide/configuration.md:45 | STALE | 模型家族表后「匹配看的是片段出现在 id 里的**任意位置**，所以带 `us.`/`global.` 前缀的 id 同样命中」——末行 `zai.glm-*v*` 锚首（`/^zai\.glm-.*v/`），带前缀的 glm id 推不出家族、worker 启动即报错 | →「除最后一行外，匹配看的是片段出现在 id 里的任意位置…；最后一行要求 id 以 `zai.glm-` 开头，带前缀的 id 不命中。」（不重复「这时设 `MIDSCENE_MODEL_FAMILY`」——紧接下一句已给处置） |
| 115 | user-guide/configuration.md:88 | CONTRADICTION | 「本机 shell 里的 `GHERKAI_STEPS_DIR` 与 `--steps-dir` 给了只提示一句、不拦截」——云端档只在**显式 flag** 时提示，经 env 或默认 `./steps` 解析出的目录被**静默清零**（writing-deterministic-steps.md:176 写对了） | →「本机 shell 里的 `GHERKAI_STEPS_DIR` 与默认 `./steps` 在云端后端下静默不生效；显式给了 `--steps-dir` 会提示一句、不拦截。」 |
| 116 | user-guide/cloud-backend.md:179 | CONTRADICTION | 退出码 `1` 被单一解释成「CDK 已成功而 worker 镜像步骤失败…重新运行 deploy 幂等收敛」，把 cdk 自身返回码推到「其余」——cdk 失败退的就是 1（实测 cdk 2.1142.0），且本页覆盖的 `gherkai destroy` 根本没有镜像步骤 | 整句 →「`0` 成功；`2` 前置或校验失败，都是你可修的…；`1` 账户可能已被改动，有两种来源：CDK 自身失败（它的报错码多为 `1`，原样透传，原因看上方 cdk 输出），或 CDK 已成功而随后的 worker 镜像步骤失败（带同一组选项重新运行 `gherkai deploy` 幂等收敛）；`gherkai destroy` 没有 worker 镜像步骤，它的 `1` 只会来自 CDK。其余退出码是 cdk 命令自己的返回值，原样透传。」 |
| 117 | README.md:22 | CONTRADICTION + STALE | 「需要 Python 3.13 与 uv、Node ≥ 22，以及一个开通了 Bedrock、AgentCore Browser 与 Nova Act 的 AWS 账户」两症：把各形态的**并集**写成无条件要求（Node 只有本机跑 Midscene worker 或 `deploy` 才需要，与同屏 :16「只提交云端 run 的人装这一个即可」矛盾）；Python 写成单一版本（真值 `>=3.13`，全仓另 7 处都写「≥ 3.13」） | →「需要 Python ≥ 3.13 与 [uv](https://docs.astral.sh/uv/)，以及一个开通了 AgentCore Browser 与所用引擎对应服务（Nova Act 服务 / Bedrock 上的默认模型）的 AWS 账户；在本机运行 Midscene worker 或部署云端后端另需 Node ≥ 22。前置要求与逐步说明见 …」（来源：分片 readme-changelog-pkg + 族「版本·模型 ID·依赖锁」） |
| 118 | README.md:39 | TONE | 「30 秒上手」代码块三行注释错列（`#` 起于 55 / 55 / 52 列；同文件安装块四行一律对齐） | 第 39 行 `gherkai explain <run_id>` 后补 3 个空格，使 `#` 起于第 55 列 |
| 119 | .github/release_body_footer.md:15 | CONTRADICTION + STALE | 升级第 2 步两症：命令是裸 `gherkai deploy`（缺必给的 `--vpc`，多环境团队还须点名 `--prefix`，照抄必退 2 或动错环境）；「两步之间的提交会被拒绝，属预期」没说是谁的提交（只有刚升级的那台部署机被拦，其余成员 CLI 旧于后端只提示） | 整行 →「2. 部署方立刻执行 `gherkai deploy --vpc <与上次相同的档> --prefix <同前缀>`，让云端后端与命令行工具同版本。这两步之间，只有这台刚升级的机器自己的提交与查询会被拒绝（退 2），属预期；团队其他成员不受影响。」 |
| 120 | .github/release_body_footer.md:16 | STALE | 升级第 3 步只让成员「升级各自的 CLI」，漏「在本机运行用例的人须把 Midscene worker 升到同版本」——版本不一致时能力自述契约校验直接退 2；同一 footer 的安装块本就有那条 npm 命令，而这是每版都出现的固定块（缺了每版都缺） | 第 3 步 →「3. 团队其他成员再升级各自的 CLI；在本机运行用例的人同时把 Midscene worker 升到同版本：`npm i -g @gherkai/worker-midscene@{{VERSION}}`。有自定义 worker 镜像 variant 的团队，从新版本的基础镜像重新构建后，用 `gherkai deploy push-worker` 推送一次。」 |

### 2.5 人读层：contributor 文档与索引（19 条）

| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 121 | CONTRIBUTING.md:38 | STALE | 根目录树 `.github/` 展开成 `workflows/{ci,release}.yml`，漏 `pages.yml`（同文件 :137 自己在讲它） | →「workflows/{ci,release,pages}.yml + scripts/ + release_body_footer.md」，括注补「pages.yml = 把 docs/diagrams/ 发到 GitHub Pages」 |
| 122 | CONTRIBUTING.md:39 | CONTRADICTION | 树写 `.claude/` 「其余为个人配置、不入库」，而 `git ls-files .claude` 有 5 项入库（settings.json / hooks/sync-derived.sh / skills/doc-diagram/SKILL.md），同文件 :137/:139 自己称它们「入库」 | 整行 →「├── .claude/  ← Claude Code 项目级资产（入库）：commands/（两条复盘入口）、settings.json + hooks/sync-derived.sh（派生文件同步，见「测试」节）、skills/doc-diagram/（作图入口）；个人配置放 `.claude/settings.local.json`、不入库」 |
| 123 | CONTRIBUTING.md:44 | STALE | `docs/user-guide/` 括注只列 6 类，真值 9 页（漏「写确定性 step」「测本机 / 内网应用」「常见问题」） | →「`user-guide/` ← 使用者文档，一个主题一篇 owner（篇目与 owner 表见 docs/user-guide/README.md）」（不再枚举，免下次再漂） |
| 124 | CONTRIBUTING.md:45 | STALE | `docs/ai-eng/` 枚举漏 `diagram-authoring.md`（同文件 :137 正引用它） | →「README.md（该层入口）+ REFERENCES.md（外部一手来源）+ {doc,code}-health-review.md（两条复盘方法）+ diagram-authoring.md（作图方法）」 |
| 125 | CONTRIBUTING.md:47 | STALE | `docs/diagrams/` 枚举成「图源 JSON + 导出 SVG + index.html」，漏已发布到 Pages 的可交互 HTML（真值 19 json / 19 svg / 3 html） | →「文档里的图：图源 JSON + 导出 SVG + 已发布到 Pages 的可交互 HTML + index.html」 |
| 126 | CONTRIBUTING.md:137 | STALE | 「在 Claude Code 里 `/diagram` 或提到改图即自动加载该方法」——skill 已改名 `doc-diagram`（同句括注里的路径已是新名，命令名没跟；全仓仅此一处） | `/diagram` → `/doc-diagram`（来源：contributor-docs 分片 + meta-indexes 分片 + 族「目录树与模块清单」） |
| 127 | CONTRIBUTING.md:139 | STALE | hook 判据写成 mtime 比较（「`*.json` 比同名 SVG **新**时提醒」）——`sync-derived.sh` 早已改成内容指纹（sha256 对比 SVG 尾部 `gherkai:source-sha256`），ADR 0045 决策七明确否掉 mtime；同文件 :137 自己写「sha256 指纹」 | →「`docs/diagrams/*.json` 的 sha256 与同名 SVG 末尾的图源指纹不符（或 SVG 缺失）时提醒运行 `tools/build_diagrams.mjs`（不自动重建——与 CI 护栏同一指纹判据）」 |
| 128 | cli/DEVELOPMENT.md:18 | STALE | 模块树把两个内部隐藏子命令的隐藏机制写成 `argparse.SUPPRESS`——code 注释明说那样会以「==SUPPRESS==」漏出，实装是「不传 help + 收窄 subparsers 的 metavar」（7649090 只改了 code） | 括注 →「（靠不传 `help` + 收窄 subparsers 的 `metavar` 隐去，**别改用 `argparse.SUPPRESS`**——会以「==SUPPRESS==」漏进 `--help`，理由见 `__main__.py` 该处注释；由 submit 以 setsid fork 启动、不供用户直接调用）」 |
| 129 | cli/DEVELOPMENT.md:54 | STALE | 「仅覆盖表名/桶名时才用 `--ddb-table` / `--s3-bucket`（其余资源仍按 prefix 推导）」——run 另有 `--events-table`/`--cluster`/`--subnet`/`--security-group` 四个覆盖；与 configuration.md:140-145 owner 表直接矛盾 | →「单独覆盖某个资源名或网络参数时才用 `run` 的六个单项覆盖 flag（`--ddb-table`/`--s3-bucket`/`--events-table`/`--cluster`/`--subnet`/`--security-group`；`submit` 只收前两个，其余取部署侧写进后端的值，三个 Lambda 无 flag、恒按 prefix 推导），逐项默认值与对应 SSM 参数见 `docs/user-guide/configuration.md` 的「云端资源名与网络的单项覆盖」表。」 |
| 130 | deploy_aws/README.md:24 | CONTRADICTION | 「`--vpc` 与 `--prefix` **必给**」——`--prefix` 有默认 `gherkai-`（还可用 `AWS_RESOURCE_PREFIX`），只有 `--vpc` 真必给；这份 README 逐字上 PyPI | →「`--vpc` 必给，没有隐式默认；`--prefix` 不给时用默认 `gherkai-`，给了则须与提交侧 `gherkai run` / `submit` 的 `--prefix` 一致。」 |
| 131 | deploy_aws/DEVELOPMENT.md:54 | STALE | 「`typing_extensions` 是 `gherkin-official>=42` 的传递依赖」——仓库声明下限是 `>=31.0.0`（lock 解析 42.0.1），且 31.0.0 就已声明 `typing-extensions>=4`；`>=42` 这个写法全仓无依据 | →「`typing_extensions` 是 `gherkin-official` 的传递依赖（`gherkin/parser_types.py` 无条件 import 它；该库自 31.0.0 —— core 的声明下限 —— 起就声明 `typing-extensions>=4`）」。**同句在 `stack.py`:676 与 `tests/test_lambda_asset.py`:139 的注释里还有两份副本 → 移交 code-health 同批改** |
| 132 | .github/workflows/README.md:8 | CONTRADICTION | 小节标题「## **两条**工作流」，其下表格三行（ci / release / pages；pages.yml 随 archify 图链入库时补了行没改标题） | →「## 三条工作流」；同时 :155「工具链版本在两个 workflow 的 `env:` 里」→「在 `ci.yml` 与 `release.yml` 的 `env:` 里」（pages.yml 无工具链 env） |
| 133 | .github/workflows/README.md:14 | STALE | pages.yml 触发列写「push 改动 `docs/diagrams/**`」，漏 `paths` 里的 `.github/workflows/pages.yml` 自身 | →「push 改动 `docs/diagrams/**` 或 `pages.yml` 自身（只在默认分支部署）/ 手动」 |
| 134 | docs/README.md:3 | CONTRADICTION | 「本仓库的文档按**读者**分三类」，紧随的表四行；同页 :16 又按三类口径写 | 首句 →「本仓库的文档按**读者**分三类；技术文档这一类有两个入口（改代码的 contributor、想懂机理的读者），所以下表有四行。找文档先看自己是谁，再进对应的入口；每个入口页同时是该类的索引与「谁负责讲什么」的表。」表保持四行 |
| 135 | docs/README.md:10 | STALE | 文档地图对 `ai-eng/` 的括注「（外部一手来源、复盘方法）」漏作图方法（d24b90d 只改了 `docs/ai-eng/README.md`） | →「（外部一手来源、复盘与作图方法）」 |
| 136 | docs/ai-eng/README.md:3 | CONTRADICTION | 「ADR / CONTEXT.md / CLAUDE.md 与它同属一类，只是位置固定，**其余归这里**」——同类还有 `.claude/commands/`、`docs/journey/`、`skills/gherkai-evals/`（都不在这里） | →「方法文档与外部来源登记归这里；同类还有触发入口 `.claude/commands/`、过程暂存 `docs/journey/`、skill 评测资产 `skills/gherkai-evals/`，各因位置依赖或归属另在其处（见 ADR 0045 决策一）」 |
| 137 | skills/README.md:3 | — | 见术语批 #7（「维护者」→ contributor） | — |
| 138 | skills/gherkai-evals/evals.json:241 | STALE | job-failure 评测（id 13）把可接受判定写成「error/**aborted**」——fixture 真值是 `error` + `timeout`（`@timeout:20` 触发、全程无 fail-fast），而 ADR 0031 明令超时**不归** aborted；grader 被要求「按字面判」，会放过把判定写成 aborted 的错误汇报 | →「汇报用 job 级结构（scope_id、判定 error 且归因 timeout、原因 message），没有为不存在的失败步编造步号、thought 或截图」；expectations[0] 括注 →「（job 墙钟预算到点，不是某一步的断言判否）」；expected_output 里「被中止」→「墙钟预算到点被停止，判 error、归因 timeout」 |
| 139 | skills/gherkai-evals/evals.json:257 | STALE | eval 14 的 prompt 说「没过的那条说正文里没出现「**图灵**」」——fixture 两条 scenario 的断言都是「词条首段提到了计算机或机器」，「图灵」全 fixture 零命中（该 eval 与 fixture 同批引入、自始即错）；7 条断言里没有「纠正用户复述」这一维，错词只给评分引噪声 | prompt 整句 →「features/zh_terms.feature 两条 scenario 是一模一样的步骤，只是引擎不同。reports/ 里那次跑一条过了一条没过，没过的那条说词条首段没提到计算机或机器，可我打开页面首段明明写着「计算机」。是网站的问题还是我们哪里写错了？」（「首段明明写着计算机」有通过那条的证据 thought 支撑）。断言总数不变，按该文件惯例在 `notes` 追一句本轮尺子变更 |
| 140 | skills/gherkai-evals/grader-prompt.md:11 | STALE | `timing.json` 的内容列成三项（repo_touches / network_calls / skill_copy_touches），漏第四个污染指标 `memory_reads`（`run_evals.py` 落盘四项；ADR 0043 决策七把「被旧会话记忆喂了答案」列为它抓到的真实污染）——评分者看不到这一维 | 括注 →「`timing.json`（repo_touches / network_calls / skill_copy_touches / memory_reads）」。**同款欠列在 `run_evals.py`:13 docstring「另记三个…指标」→ 移交 code-health** |

### 2.6 人读层：internals 与 agent skill（15 条）

| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 141 | internals/architecture-overview.md:42 | CONTRADICTION | 「worker 对核心**只上报**两类信息，即逐条事件…与进程退出信号」——退出信号由父进程/平台观察得出、**永不由 worker 自报**（同页图源 :306、图注、姊妹页 :12、ADR 0034:143、CONTEXT:178 全部反向） | 首句 →「**事件流与退出信号**：核心对一个 worker 只看两类信息——worker 上报的逐条事件（`scope_started` / `step_done` / …），以及由父进程或平台观察到的进程退出信号（**退出永不由 worker 自报**）；判定要求两者同时成立（事件完整 ∧ 进程干净终止）。」后半句不动 |
| 142 | internals/cloud-backend-carriers.md:15 | STALE | 「`version`、`vpc`、`worker-template/<engine>`、`subnets`/`security-groups` 这**四族**是 stack 资源」+「**前四族**随 cdk 事务」——同格自列 5 个名字，`names.py` 与 ADR 0037/0033 都按 5 个独立参数族记 | 「这四族」→「这五族」（并把 `subnets`/`security-groups` 的斜杠改顿号，与同格后半写法齐平）；「前四族随 cdk 事务」→「前五族随 cdk 事务」 |
| 143 | internals/cloud-backend-carriers.md:124 | CONTRADICTION | 延伸阅读把 verdict-model 的主题写成「判定的计算路径（run / job / step **三级**与严重度）」——owner 页 §1 标题即「**四层**归约：票 → step → scenario → job → run」，全仓仅此一处写三级 | →「判定的计算路径（票 → step → scenario → job → run 四层归约与严重度）」 |
| 144 | internals/cli-json-contract.md:49 | STALE | `scenarios[]` 的 `report_refs[]` 注「（同上形状）」——上一表 job 级的 `kind` 是 summary/report，而 scenario 级两引擎都不填、恒为空数组（同页对 step/job 两级都点了填充方，独此级只给形状） | →「`report_refs[]`（形状同上；**当前两引擎都不填 scenario 级产物，恒为空数组**——产物在 step 级与 job 级）」；**改完跑 `tools/render_skill_contract.py` 重渲染 skill 副本、同 commit** |
| 145 | internals/deterministic-step-lifecycle.md:53 | STALE | §2 表两症：`--capabilities` 自述对象键列 4 项（漏 `model_id`，真值 5 键且有消费方 `doctor` 的 `engines.model.<engine>` 行）；调用者列漏 `submit`（`_plan_and_preflight` 两个调用点 = run + submit，其 docstring 正是为 submit 而设） | 键清单补 `model_id`（「该 worker 起 job 时真会用的模型 id，`doctor` 的 `engines.model.<engine>` 行取它」）；调用者格 →「`gherkai list-deterministic`、`doctor` 的 `steps.load.<engine>` 与 `engines.model.<engine>` 两项（同一次自述）、`run` / `submit` 的本机前置（共用 `_plan_and_preflight`；`run` 侧同一次 spawn 兼定 grace 下限）、`doctor --backend cloud` 比对云端停止宽限」 |
| 146 | internals/deterministic-step-lifecycle.md:13 + :103 | STALE | §0 表 ③ 行「三个命令都 spawn 一次瞬时 worker」与 §4 表「`run` 另有一道等价的本机前置」同样漏 `submit`（真值 5 个入口） | :13 发生地 →「`list-deterministic` / `plan` 标注 / `doctor` / `run`·`submit` 的本机前置」，「三个命令都 spawn」→「这些入口都 spawn」；:103 →「`run` / `submit` 另有一道等价的本机前置…（两命令共用 `_plan_and_preflight`）」。三处同批 |
| 147 | internals/verdict-model.md:120 | STALE | §4 表 `TERMINAL_STATUSES` 的「引用方」格以「另有一处**取补**用法」收尾（= 穷举承诺），漏云端推进器 Lambda 的「已收尾 run 不再推演」判——漏引会让已收尾的 run 被重 tick、用过期事件覆盖已落定的判定真值 | 在 `project_full` 之后插一项：「云端推进器 Lambda 的「已收尾的 run 不再推演」跳过判据（`deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`：读到终态即 no-op，见 `execution-and-reconciliation.md`「已终态 run 的两档重入」）」，末句原样保留（来源：internals 分片 + 族「状态枚举与终态」） |
| 148 | internals/verdict-model.md:146 | DEADLINK | 段末指针写「给使用者的口径见 `cloud-backend.md`「**常见错误**」」——该页无此节（实名「退出码与常见错误」） | →「…「退出码与常见错误」」 |
| 149 | skill/SKILL.md:25 | STALE | 「**引号只是书写习惯**：AI 步整段文本**原样**交给模型」——两引擎都先剥掉整段外层双引号与 ASCII 空白（`_unquote` / `unquote`），而同文 §4 正教 agent 把 AI 步整段写在双引号里（剥引号是常态） | 第一个分句 →「**引号只是书写习惯**：AI 步把关键字之后那段文本交给模型（整段被双引号包起来时，外层那对引号会去掉）；确定性 step 的正则匹配的是没去引号的原文——对象是关键字之后的那段文本、引号照留，正则里别写关键字，…」（其后两条写法约束原样保留） |
| 150 | skill/SKILL.md:74 | STALE | §7 cloud 档行说明格写「同一个 run 上这几个值逐字一致…任一处不同即退 2」，而清单含 `--profile`（无任何逐字比对，换同账号同 region 的 profile 名照样查得到）与 `--worker-variant`（查询命令根本不收） | 说明格 →「`--backend` / `--prefix` / `--report-dir` 必须与产生这个 run 的那条命令逐字一致，不一致即退 2 说找不到这个 run；`--region` 要指同一个 region（换了就查不到），`--profile` 换成另一个指向同账号同 region 的 profile 不影响；`--worker-variant` 选云端 worker 镜像上的确定性 step 集，不给用部署侧默认指针」。**flag 格保持原样**（「（仅 `run` / `submit`）」是护栏认的排他声明形态，改写会丢覆盖） |
| 151 | skill/SKILL.md:86/:104 | STALE | §9 失败汇报模板的 job 级分支只列 `error / aborted`，漏 `skipped`（`--fail-fast` 下未启动的 job：零 step 记录、既套不上步级模板也不在现枚举里）；同包契约页自己列了 skipped | :86 →「**没有任何一步判否、只有 job 级的 error / aborted / skipped**（超时、起 worker 失败、网络、被 `--fail-fast` 中止，或中止前根本没启动）→ job 级模板」；:104 模板行 →「判定：<error(<error_type>)\|aborted\|skipped>」 |
| 152 | skill/SKILL.md:117 | STALE | §10「别调小 `--grace`（仅 `run` 有）：云端 `submit` 的对应选项在部署侧…」——cloud 档给**任何**显式 `--grace` 即退 2（不是只拒过小值），且被拒的那条线是 `run --backend cloud`、与 submit 无关（submit 没有该 flag） | →「别调小 `--grace`（仅 `run` 有，且只对本机档；cloud 档给了它即退 2）：云端的停止宽限在部署侧的 `gherkai deploy --stop-timeout`，归部署方」（**保留「仅 `run`」**，护栏按「仅」解析排他声明） |
| 153 | skill/references/cloud-backend.md:29 | CONTRADICTION | 随 wheel 发行的 skill 里有与 #116 同源的错误退出码映射（`1` 单一解释成「镜像步骤失败…重新运行 deploy 收敛」）——装了 skill 的 agent 会在 cdk 真失败时给错处置 | →「- 退出码：0 成功；2 前置 / 校验失败（Node 缺失、VPC 档不符、容器引擎名不认、`push-worker` 架构或版本不符）；1 账户可能已被改动，两种来源——cdk 自身失败（报错码多为 1、原样透传，处置看 cdk 输出），或 cdk 已成功而 worker 镜像步骤失败（重新运行 `gherkai deploy` 幂等收敛）；`destroy` 没有镜像步骤，它的 1 只来自 cdk；其余原样透传 cdk。」与 #116 同批 |
| 154 | skill/references/cloud-backend.md:31 | STALE | 「云端每个 run 的并行 job 数 = min(`--max-concurrency`, 部署侧上限 8)」把 cap 说成对云端两种执行方式都生效——cap 只钳 `submit` 那条线；`run --backend cloud` 的并发由进程内 schedule 直接开、不受钳制（照现文会真开 12 个云端浏览器会话、直接多花钱） | →「`submit --backend cloud` 提交的一个 run，并行 job 数 = min(提交时 `--max-concurrency`, 部署侧上限 8)：超过上限时 `submit` 打印一行提示、本 run 按上限并行。`run --backend cloud` 的并行度就是 `--max-concurrency`，不受这个上限约束。」 |
| 155 | skill/references/cloud-backend.md:88 | DEADLINK | 「命令样例见部署方说明页「**清理**」节」——该页真实标题是「拆除与清理」 | →「命令样例见部署方说明页「拆除与清理」节。」 |

### 2.7 人读层：方法文档与技术笔记（21 条）

| # | 文件:行 | 类 | 问题 | 改法 |
|---|---|---|---|---|
| 156 | ai-eng/doc-health-review.md:85 | STALE **high** | 第一层【强制】取锚点命令 `… \| grep -m1 .` **恒返回 HEAD**（无 trailer 的提交也输出「`%h` + 空格」、非空行即命中）→ 区间退化成「本轮自己那一两个提交」，全部 ADR 都被判「未动、可沿用」，【强制】提纯审计整条失效 | →「`git log --format='%h %(trailers:key=Doc-Health-Round,valueonly)' \| awk 'NF>1{print; exit}'`」，括注点明失败形态「`grep -m1 .` 会命中每一行（无 trailer 的提交也输出 `%h` + 空格），必返回 HEAD」。**本轮实测：原命令 → `5a0feda`（HEAD）；awk 版 → `dfd867e 6`** |
| 157 | ai-eng/code-health-review.md:53 | STALE **high** | 同款缺陷（`Code-Health-Round`）→ `git diff --stat <锚点>..HEAD` 得空 diff、热区全塌成冷区 | 同 #156 改法（awk 版实测 → `bb36eb4 4`）；两处同步改 |
| 158 | ai-eng/doc-health-review.md:49 | DEADLINK | 指「CLAUDE.md 文档纪律「**文档分层与归位**」」——CLAUDE.md 无此条名（现行 :22「文档按读者三分类归位，口吻随类别变」；该串只在 ADR 0045 里） | →「CLAUDE.md 文档纪律「文档按读者三分类归位」」 |
| 159 | ai-eng/doc-health-review.md:43 | STALE | TONE 术语面写「用户文档、skill、包 README **三面**已由护栏 RETIRED_TERMS 机械挡住」——真值四面（另 `docs/diagrams/*.json` 图源，ADR 0045:62 明写「四处同位扫」）；同行技术文档枚举又漏 `.github/workflows/README.md`（0045:22 与本文 :50 都把它算同侧） | →「用户文档、图源（`docs/diagrams/*.json`）、skill、包 README **四面**已由护栏 RETIRED_TERMS 机械挡住（[ADR 0045] 决策六）」；「技术文档（CONTRIBUTING / DEVELOPMENT / internals / `tools/*.md`）」→ 补 `.github/workflows/README.md` |
| 160 | ai-eng/doc-health-review.md:73 | CONTRADICTION | 覆盖范围（全任务对象清单）只列 markdown、漏 `docs/diagrams/*.json` 图源，而 :51 与 :43 都把图源派给本任务，:75 又断言「本任务只管 `.md`」→ 图源成无人区（姊妹任务也不收） | 覆盖范围列表末加一条「`docs/diagrams/*.json`（图源，派生视图；判据侧重见上 internals 条）」；:75 括注「本任务只管 `.md`」→「本任务只管 `.md` 与 `docs/diagrams/*.json` 图源」 |
| 161 | ai-eng/doc-health-review.md:75 | CONTRADICTION | 「明确排除」（自称唯一权威清单）排除「`.claude/` 除 `commands/` 外的部分」并断言「`.claude/skills/`、settings 等…**不入库**」——与同文 :69 把 `.claude/skills/doc-diagram/SKILL.md` 列入覆盖范围互斥，且「不入库」与 git 真值不符 | →「`.claude/` 里未入库的个人项（`settings.local.json`、个人 `skills/`）与 `.agents/`——已入库的项目级 markdown（`.claude/commands/` 两条入口、`.claude/skills/doc-diagram/SKILL.md`）在范围内，见上覆盖范围；入库的 `.claude/settings.json` 与 `.claude/hooks/` 不是 markdown、不在射程；…」（来源：meta-indexes 分片 + 族「目录树与模块清单」） |
| 162 | ai-eng/doc-health-review.md:92 | CONTRADICTION | 提纯审计产出槽写「审计集里每个 **ADR** 一条」，而两行之上把审计集定义为「全部 ADR + CONTEXT」并专门给了 CONTEXT 反向判据 → 按字面执行会漏掉 CONTEXT 的具名记录、「空槽 = 未执行」的牙咬不到它 | →「审计集里每篇一条（全部 ADR + `CONTEXT.md`）」 |
| 163 | ai-eng/code-health-review.md:25 | DEADLINK | 指「CLAUDE.md 文档纪律「悬空指针红线」条（**含其子条「范围含 repo 内 code 注释」**）」——该子条已并入主条正文（现三子条无此名） | 括注 →「（该条正文显式含 repo 内 code 注释与 docstring）」 |
| 164 | ai-eng/code-health-review.md:26 | CONTRADICTION | 「一次性脚本/脚手架本该放 `$CLAUDE_JOB_DIR/tmp` 不入 repo」——CLAUDE.md:35 的约定是系统临时目录 `/tmp`；`$CLAUDE_JOB_DIR/tmp` 这个子目录全仓无依据（e2e_harness 用的是 `harness-runs`）；CLAUDE.md 那处同批已修、这处落单 | →「系统临时目录（`/tmp`）」 |
| 165 | ai-eng/code-health-review.md:73 | CONTRADICTION | 正文出现「**SEDIMENT** 只管措辞」，但 SEDIMENT 不是本文档的类名（本文三类 = DEAD / STALE_INEFFICIENT / VIOLATES_ADR），读者在本文档内查不到定义（随整段逐字复制从姊妹文档带入） | →「这是「动规则」的唯一入口——复盘只按现有规则找问题、不就地改规则，规则本身只在这里凭证据变」（不引用本文档没有的类名；若提纯提案 P39 获批、整段压缩，本条自动作废） |
| 166 | ai-eng/REFERENCES.md:4 | STALE | 「决策与"**事实现状**"以 `CONTEXT.md` + `docs/adr/` 为准」——CONTEXT.md 已于 2026-09-19 重写为严格词表（ADR 0045 决策八：零实现细节、只定术语），不再承载事实现状 | →「> 注意：决策与实装现状以 `docs/adr/` + code 为准（`CONTEXT.md` 只定术语，见 ADR 0045 决策八）——下面是**外部一手来源**，用于查证细节。」 |
| 167 | ai-eng/REFERENCES.md:14 | STALE | 「`createOpenAIClient` 注入点：`@midscene/core .../service-caller/index`」——1.12.8 的该 index 里 `createOpenAIClient` 零命中，采纳点在同目录 `openai-client.js` 的 `createAndWrapClient` | →「`createOpenAIClient` 注入点：`@midscene/core .../ai-model/service-caller/openai-client`（`createAndWrapClient` 里 `await createOpenAIClient(baseOpenAI, openAIOptions)`，经同文件 `createChatClient` 调用；`service-caller/index` 只再导出 `createChatClient` 等符号、不含此回调）（见 ADR 0008）」 |
| 168 | ai-eng/REFERENCES.md:15 | STALE | 括注「（传 createOpenAIClient/modelConfig 即切隔离）」在 1.12.8 只对「给了 `modelConfig`」成立；只给 `createOpenAIClient` 是 agent 作用域包装（委托全局、仍读 env） | →「（传 `modelConfig` 即切隔离——我们的接线同时传 createOpenAIClient 与 modelConfig；1.12.8 起只传 createOpenAIClient 则是 agent 作用域包装、仍读全局，见 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md` §7）」 |
| 169 | ai-eng/REFERENCES.md:16 | DEADLINK | 「planning 无条件附图：`@midscene/core .../ai-model/llm-planning.js`」——装机 1.12.8 无该文件（本节自述「安装的源码（本机 ground truth）」、无版本锚），真位置 `ai-model/workflows/planning/standard-planning.js` | →「planning 无条件附图：`@midscene/core .../ai-model/workflows/planning/standard-planning.js`（`standardPlan()` 两个消息分支都附 `image_url`，`includeLocateInPlanning` 不去图、只改 system prompt 与定位解析；1.9.8 时此逻辑在 `ai-model/llm-planning.js`，见 ADR 0012）」；本节标题后标「（现为 1.12.8）」 |
| 170 | spikes/SIGV4-FETCH-RECIPE.md:15/:58 | DEADLINK | 同一文件混用两种路径基准：:15/:58 用包相对 `src/lib/agentcore-sigv4.mts`（按文件位置解析 = `spikes/src/...`，不存在），:72/:101 用仓库根相对 | :15 →「`engines/midscene/src/lib/agentcore-sigv4.mts`」；:58 →「`engines/midscene/src/worker/run-scope.mts`」；顺带 :109 裸文件名补全 |
| 171 | spikes/SIGV4-FETCH-RECIPE.md:62 | STALE | §1 末模型 id 注释「`{ model: "qwen.qwen3-vl-235b-a22b" }` ← bare id」无「生产已改」注（同文件 :15/:54 对同类分叉都加了 ⚠️ 注）；而 GPT 系须带 `us.`/`global.` 前缀的 profile id | 追加「// ⚠️ spike 期主体是 qwen3-vl 的裸 id；**生产默认模型已改**（`DEFAULT_MODEL` 见 `engines/midscene/src/lib/agentcore-sigv4.mts`、ADR 0044「现值」），GPT 系列须用带 us./global. 前缀的 inference profile id、参数走 max_completion_tokens（ADR 0044 决策 3）。「model 放请求体而非路径、不用 inference-profile ARN」两条与模型无关、仍成立；`-instruct` 那条是 qwen id 命名的坑。」 |
| 172 | spikes/SIGV4-FETCH-RECIPE.md:82 | STALE | §3 失败模式表的 400 一行只列三种成因，漏生产必须处理的那类：Bedrock 不认 `image_url.detail: "original"`（`bedrockCompatBody()` 专为此设、且必须在签名前改）；而 code 注释正把读者指到本文件查失败模式 | 表末加一行：「\| **400「value did not match any expected variant」** \| Bedrock 的 OpenAI 兼容层不认 `image_url.detail: "original"`（OpenAI 原生认它；Midscene 的 gpt-5 / gpt-6 family 适配器对定位请求固定发它、无配置可关） \| 签名**之前**从请求体删掉该字段（签名含 payload hash，签完再改即 403）——见 `agentcore-sigv4.mts` 的 `bedrockCompatBody()` / ADR 0044 决策 3 \|」 |
| 173 | spikes/SIGV4-FETCH-RECIPE.md:119 | STALE | §7「关键坑」引 `agent.js:852-853` + `hasCustomConfig` 三元式 + 「一旦给 `createOpenAIClient`…完全无视 env」——行号（文件现 1002 行，逻辑在 :921）、标识符（全 dist grep 零命中）、语义（三分支）三样全失效；生产两者都给、操作结论不变 | §7 改为版本分层：保留 1.9.8 形态的代码块并标「spike 期读到的形态」，补「**1.12.8 已改三分支**（新增 `AgentScopedModelConfigManager`）：给 `modelConfig` → 隔离；只给 `createOpenAIClient` → 包住 `globalModelConfigManager`、仍读全局 env；都不给 → 全局」，结论句改「**两版下本项目的接线不变**：模型配置随 `opts.modelConfig` 一起给（本项目两者都给 → 落隔离支，隔离态不读 env）」。**与 #27（0008）同源、同 commit** |
| 174 | spikes/SIGV4-FETCH-RECIPE.md:129 | STALE | §7 样例 `modelConfig` 里给 `MIDSCENE_USE_QWEN3_VL: "true"` 作「必须这样给」的照抄样例、无 spike 期注——生产已改 `MIDSCENE_MODEL_FAMILY`，且 SDK 会把该开关映射成 `qwen3-vl`，在 gpt 默认模型下照抄即静默设错 family、两者同给还被当双模式冲突 | 取「保留 spike 原样 + ⚠️ 注」（与本文件 :15/:54 惯例一致）：样例上方加三行注（legacy 开关内部映射为 family `qwen3-vl`；生产已改 `MIDSCENE_MODEL_FAMILY: modelFamily()`，见 `agentcore-sigv4.mts` / ADR 0044 决策 2；默认模型已是 GPT 系，照抄会静默设错 family、同给会被当双模式冲突；此处保留 spike 原样、勿照抄当现状）。**此法下 ADR 0003:14 的括注「（配方里仍是旧写法）」仍为真、不必连带改** |
| 175 | spikes/SIGV4-FETCH-RECIPE.md:137 | STALE | 「### 剩余 — `@aws-sdk/signature-v4` 版本未 pin」作未决遗留项——已是有意决策（ADR 0042 决策六只钉两引擎 SDK；`engines/midscene/DEVELOPMENT.md`:123 明写其余用 `^`），且入库 lock 把它锁在 3.370.0 | 整节 →「### 依赖版本口径\n`@aws-sdk/*` / `@aws-crypto/sha256-js` / `openai` 有意保留 `^`（只两引擎 SDK 钉精确版本，见 ADR 0042 决策六与 `engines/midscene/DEVELOPMENT.md`「SDK 与浏览器驱动锁定精确版本」条）；入库的 `engines/midscene/package-lock.json` 把本地解析锁在 3.370.0（发行的 npm 包与云端基础镜像仍是装包时解析）。」 |
| 176 | tools/e2e_harness.md:53/:72 | DEADLINK | 两处「（见下「**多 scenario 陷阱**」）」指向文中不存在的小节（真身 = 「实际运行陷阱」的第 1 条） | 两处 →「（见下「实际运行陷阱」第 1 条 `@scope:` 分组）」（用内容锚定、不用纯序号，序号会随条目增删漂） |

### 2.8 已驳回（REFUTED，7 条）

| # | 文件:行 | 原报 | 驳回理由 |
|---|---|---|---|
| R1 | docs/adr/0035:56 | 「`--tunnel-ttl` 是显式覆盖**旋钮**」用退役名 | 「旋钮」**不在**退役名词表：`_doc_rules.py`:36 把它收在 `COLLOQUIAL`（管口吻、只约束给人读的文档与产品文案），`RETIRED_TERMS_WORDS` 收的是复合词「版本单旋钮」；CONTEXT 把它登记在两个具体概念的 `_Avoid_` 下（指拿它当那两个概念的名字），而此处是泛指一个 CLI 选项的散文隐喻。239e5a8 的既定口径是「ADR 散文口语按 owner 标准保留」，且它扫过的 ADR 里「旋钮」被成片保留（0037 七处、0033 两处…）。只改这一处会造新的不一致 → 属 D5 的范围裁定 |
| R2 | docs/adr/0026:45 | 「`maxConcurrency` 默认 **4**」没点明 CLI 缺省是 1 | 与 code 无不符：:19 是接口伪代码块、:25 紧接声明「实际实现为 dataclass `ScheduleOpts`」、:86 又强调这些是「`opts`/参数注入、策略由调用方定」，`schedule.py`:110 正是 4；CLI 缺省 1 在它该在的层已写全且一致（running-and-results:84、writing-features:109、architecture-overview:40、ADR 0043:86）。把 CLI 数字搬进 0026 反造第二事实源 |
| R3 | CONTEXT.md:148 | 「执行方式」词条无 ADR 指针 | ADR 0045:78 的形态规则是「句末**至多一个**「见 ADR NNNN」」——指针是上限不是必填；且「执行方式」这个名是词表自己在 239e5a8 里造的，`grep 执行方式 docs/adr/` 在 0034 零命中，前台那半的决策在 0026/0016、后台那半在 0034，**没有单一 ADR 拥有这根轴**。也不存在失效指针，归 DEADLINK 亦不成立 |
| R4 | skills/gherkai-evals/grader-prompt.md:5 | 「把 `summarize_runs.py --json` 的清单当参数传进去」暗示那份 JSON 含 run 目录 | 文档没这么声称，且清单字段足以机械推出全部 run 目录（`eval` = `eval-<id>-<slug>` 目录名原文、`arm`、`runs` = 该臂 timing.json 个数，run 目录名由 `run_evals.py` 固定构造 `run-1..run-N`）；`git log` 显示两文件同作者同提交产出，这句是「工作项清单的来源」而非「run 目录名的来源」 |
| R5 | internals/verdict-model.md:146 | 部署方退出码整段与 user-guide owner 构成完整双写、该压缩 | 判别依据不成立：本页 §5 的 9 行表**本身**就是 user-guide 退出码表的完整平行副本并互留指针，146 不是唯一例外；`internals/README.md` 归属表明写 verdict-model 拥有「退出码按命令分工」→ 部署方退出码在 internals 侧的 owner 就是这一段；且 internals 版是严格超集（含 `push-worker` 推送途中失败仍归 2、`1` 的两种来源），压掉会删掉更准的那份。漂移真因是 user-guide 少一个分支（= #116），修法是补齐 |
| R6 | .github/workflows/README.md:140 | 等索引脚本示例用 `@midscene/web 1.9.8`（旧 pin） | 该版本号按设计就是任意值：同段上一行注释明写「拿**任意已发行**的包版本试（退 0 = 可见）」，脚本验的是「索引可见性」这一机制、与仓库 pin 无关；同段 `packaging 24.2` 同样不是仓库真值。命令仍可运行（npm 实查 1.9.8 元数据在、`WAIT_ATTEMPTS=1` 下退 0）。改成当前 pin 反给本行加一个新的同步义务 |
| R7 | docs/adr/0016:90 等 4 处 | 「用户侧 `--backend cloud`」用非规范前缀 | `_Avoid_` 登记的是完整角色名（「用户侧 AI agent」「用户侧 agent」），不是前缀；「用户」在 ADR 里 150 处成族（同篇 :131「面向用户」、:140「非用户档」、:92「非用户 CLI 旋钮」），单换 4 处会让 0016 变成「用户档 / 使用方档」混用；且 fix 提的替换词「使用方档」全仓零命中 = 新造词。ADR 属 contributor 侧 AI agent 文档、不在 TONE 射程，作 CONTRADICTION 又找不到被违反的词条 → 整族归 D10 |

### 2.9 存疑（UNCERTAIN，2 条净留）

| # | 文件:行 | 存疑点 | 建议 |
|---|---|---|---|
| U1 | docs/adr/0039:20 | 面一「范围」条的用户可见异常类枚举漏 `WorkerSelfDescribeError`——但做差集后发现该括注**远不止漏一项**（`PlanError` / `TunnelError` / `ContainerError` / `UnsupportedContainerEngine` 同样用户可见、同样不在册），即它本就是**示例**而非真值集（与紧邻 :21「这里的枚举只是示例，真值集 = 护栏的 FORBIDDEN 正则」同体例） | 不逐个补类名，改为显式降为示例 + 点出真值集与一个易误判点：「展示给用户的异常文案（**示例**：…；真值集 = 护栏扫的全部非 docstring 字面量，不逐类维护）」，并在下方例外条补半句「注意 `RuntimeError` 子类里也有用户可见的（如 worker 自述失败），本例外只给『永不因用户/使用方输入触发』的契约型异常」。请 owner 定「补示例」还是「维持现状」 |
| U2 | engines/{novaact,midscene}/DEVELOPMENT.md:57/:60 | env 表表头自述覆盖「worker 侧读取（`lib/constants.py` 与 `run_scope.py`）」，按此口径漏 `GHERKAI_STEPS_DIR` 与 `GHERKAI_NO_ARTIFACTS`——但这两项是**跨引擎共用**、按「引擎特定」本在射程外；真正的硬伤只有口径自身不自洽（跨引擎的 `GHERKAI_EXTRA_HTTP_HEADERS` 被收进了「引擎特定」表） | 缩到只修口径词 + 给指针（不扩表、不把 ADR 0024 协议通道 env 写进覆盖面）：表头 →「下表列 worker 侧读取、影响本引擎行为的 env（常量在 `lib/constants.py` 与 `run_scope.py`）；跨引擎共用的 `GHERKAI_STEPS_DIR` / `GHERKAI_NO_ARTIFACTS` 另见本文「使用方 `steps/`」与「报告落点」两节。」两份 DEVELOPMENT 同形改 |

> 另有 4 条原判 UNCERTAIN 经复核转归：0013「框架」自指 → **D14**；CONTRIBUTING:63 `.vscode` 漏列 → **主观 S38**（树本是策展清单、另漏 4 个根级点文件，属编辑判断）；图源「维护者侧」→ **主观 S39**；0032:56 `MIDSCENE_GRACE_MIN_S` → 经族「数字类」独立核实转**客观 #63**。

---

## 三、提纯提案待批（红线复核通过 43 条）

> approve = 照提案落；approve_reduced = 按缩小后改法落（复核员已把误伤的受保护要素挡回）。

| # | 文件:行 | 候选句（摘） | 沉积判据 | 改法 | 复核员一句 |
|---|---|---|---|---|---|
| P1 | 0001:24 | 「中文 UI 首次实测」下两行表 | 两格结论被表后段落与量化实测完整覆盖；表本身不含段落外信息 | **approve_reduced**：删两行表（含表头），改写成一句带出两侧结论后直接接原段落，且**保留「Midscene（当时的引擎模型 Qwen3-VL）」标注** | 提案 fix 里丢了引擎模型标注（证据边界），且其理由「Midscene 那格已被 120 票取代」若照执行会删掉唯一记载「本机中文应用上三步全过」的地方——改法钉死在 fix 文本上 |
| P2 | 0003:23 | 「换默认 = 改常量 + 改 IaC 的 ARN pin 并重新部署…云端还需部署侧放行」 | 已漂的完整重复（0044 决策 2 的第二份副本），三分之二与 IaC 真值相反 | **approve**：整句删、只留指针；**同改动里一并修 0001:63**（它以「同口径」指向本段，删后指针指空） | 候选跨度内无受保护要素；其承载的唯一 why（为何不按模型 pin）在 0044 被拒条与 0033:155 更完整 |
| P3 | 0003:23 | 「建议优先使用 Qwen3.x 系列（推荐序 Qwen3.7 > Qwen3.5 > Qwen3.6）」 | 与 0044 背景 1 同一上游事实的两份完整副本且已漂（装机 SDK 无 qwen3.7） | **approve_reduced**：压成带指针的简短重述，但**保留「不推荐使用」四字**（句尾「（不推荐 ≠ 移除支持）」的反误读护栏以它为先行词） | 权威在 0044（现行选型 ADR）；本文独有的 Bedrock 实查结论原样留 |
| P4 | 0010:30/:35/:37 | 「（即原里程碑 M5）」「（原里程碑 M5）」「M2/M5 接入时应设」 | 纯过程坐标；第五轮否它的依据（CONTEXT 定义过 M1–M5）经真值核实为误读——旧 CONTEXT 第 25 行指的是 v0.x 版本号 | **approve**：三处只删编号；标题措辞回强为「（对跨引擎报告统一关键）」；:37「spike 阶段尚未固定（用例已验证通过即可）」整句留 | 本节承重要素（「不弥合」结论 + 0027 指针 + spike 验收线 why + 2026-06 证据锚）全在候选跨度之外；**M 编号另在 4 处，同批处置见 D16** |
| P5 | 0010:35 | 「只做跨引擎归集索引（`manifest.json` 机器可读 + `index.html` 人可导航入口），链接各自原生产物、不解析融合其内容」 | 0027 决策形态的第二份完整副本（0016:46 还有第三份逐字括注），同文 :41 已再指一次 0027 | **approve**：压成带指针的简短重述，**保留「不解析融合**其内容**」的宾语**与「故这三处差异不必在报告层抹平」收口 | 0027:9 是形态权威、:139 是粒度权威；压后仍属放行形态 |
| P6 | 0035:66 | 「两 worker 各几行改动」 | 施工规模流水；其结构功能（提醒这半边非零改动）由紧随括注承载 | **approve**：→「两个 worker 各有一处注入点」 | 已对 code 核实两侧确各只有一处注入点，改后不随行数增删而漂 |
| P7 | 0020:34 | 括注里「使用方的确定性 step 写进项目 `steps/`（Nova `steps/*.py`、Midscene `steps/*.mts` 或 `*.mjs`，经 `--steps-dir` / env `GHERKAI_STEPS_DIR` 加载…）」 | 扩展名与 flag/env 解析顺序的权威在 0037 决策 4，句内本已链该决策 = 可指针化的第二事实源（同族副本 0015:43 已漏 `.mjs`） | **approve_reduced**：只删三段跨 ADR 枚举，**保留落点句与「进同一张确定性注册表」**（不变量），指针指回句内已有的 0037 决策 4（**不指 Status 头**——那里没有 flag/扩展名） | 原 fix 过删且指针错向：本节主句是「测试开发在确定性脚手架里写 Playwright 查询 step」，落点句正是它的反转注 |
| P8 | 0016:3 | Status 头 [0037] 反转三处的三个「新态」括注 | 三处新态已由正文 :166/:202/:188+:220 完整承载，且本轮核实未漂 = 未漂移的完整重复 | **approve_reduced**：只压三个**新态**括注；**三处旧立场原文与两个在文内定位（「下「cli backend 选择」节 `build_cloud_stores` 条」「「工程布局」树 `cli/` 行」）必须留** | 「gherkai/core 作 path 依赖」在正文已无残留 → 头是本篇唯一记旧世界的地方；Partial 注解要求写清「立场变什么」，旧立场原文正是它的载体 |
| P9 | 0022:82 | 「退役 bdd 时把它从 `bdd/` 移到 `worker/` 同目录（`novaact/worker/deterministic_steps.py`…），worker import 路径相应改」 | 施工节奏 + 两个已不存在的中间态路径（`.ts` 扩展名也已改 `.mts`） | **approve**：删该句、段末收在「…故脚手架是 worker 的**活依赖**、非可删副本（当前落点见上「实现状态」块与 [0037] 决策 3/4）」 | 实装偏差纠正与「活依赖」结论都在被删跨度之前；当前落点另有 :42 承载（两条路径已核在） |
| P10 | 0019:51 + :48 | 「**待 v1.0 核心库**」「## 范围（tag 语义已定 / 调度实现待核心库）」 | 撰文时的施工时态；同 bullet 紧跟的就是两篇已 Accepted ADR 的精确指针，plan/schedule 均已实装、v1.0→v1.4 都已发行 | **approve**：标签 →「**实现在核心库**」；节标题 →「## 范围（本 ADR 定 tag 语义，实现落核心库）」；bullet 正文与两个指针一字不动 | 非历史框定（无「曾/原」框），且 Status 头明写「核心库「调度实现」由 0022 落地」——:48 的「待」反与头相抵 |
| P11 | 0024:54 | 「**传输通道：三通道分离（实现期细化，子进程 worker）**」 | 「实现期细化」是相对 ADR 落盘时点的施工标记；本条 why 独立在 :59（真跑发现 SDK 把进度打进 stdout） | **approve**：括注 →「（限子进程 worker）」，删「实现期细化」 | 「子进程 worker」是必留限定词（三通道分离只对 subprocess 成立，Fargate 态由 :188 换成 DDB）；全仓「实现期细化」仅此一处、不构成指针 |
| P12 | 0027:155 | 「行为与含 AI step 的用例**一致**…产物差异**合理**（确定性 step 本就不产引擎报告）」 | 前半句是节首论点句与第一条 bullet 的重述（why 在 SDK 事实里） | **approve**：缩成「- **验证 Midscene scope 级归集必须用含 AI 的用例**——这不是 walkaround，是…客观事实。」 | 保留的后半句是对测试作者的活约束 + 防「拿确定性用例验归集后判 bug」的反模式护栏 |
| P13 | 0030:7 | 「先在 local adapter 上把「实时写 + commit-point 写序」跑通，云端…作新 adapter 接入」 | 施工次序（分几步），两侧均已实装 | **approve_reduced**：只删分步次序，**保留「这是云端（DDB/S3）落库的前置」这层定位型 why** | 原 fix 把「前置」定位也删了；:9「定位」与 :22 背景讲的是另两个问题面、不等价 |
| P14 | 0031:172 | 「两级都复用 `Status.SKIPPED`…；`shortcircuited` 布尔进一步标出 step 级「为什么没跑」」 | 后半句与 :156-158 的正交轴说明同源且更弱 | **approve_reduced**：只删分号后半句 | 前半句不能删：它是对「表内同值并存」的消歧——:46 明写 job 级 skipped 的严格边界，本篇他处无一处声明「两级语义一致、只是层级不同」，删掉会让实现者怀疑该另开枚举值 |
| P15 | 0042:238 | 「**验证暴露并已吸收的两处**：Nova SDK 异常 str() 多行 repr → 压成一行；Midscene 推理在 `output.thought` → 映射回落」 | :227/:228 零距离完整重复且更详细（多「十几行 repr 加反馈链接」「复跑确认为一行」两个判据）；git 层读证实它是 eb7ab9a 追加的总结层 | **approve**：删整条 | 删后「验证」节四段结构完整；两项内容在映射表 :70/:74 也各有权威表述 |
| P16 | 0042:103 | 「（**v1.4.2** 发版验证时按 ADR 首版口径需再加 `--all` 才展开、被判反直觉后改）」 | 版本坐标属坐标型现场 | **approve**：只删「v1.4.2」三字 | 被拒口径与改因（防未来把 `--step` 的展开收回 `--all` 门后）逐字留住；CHANGELOG 已承载版本↔行为对应 |
| P17 | 0004:16/:18 | :16 标题的 ✅；:18 末句「**ADR 早先标记的"IAM 经 Workflow 能否授权"残余风险——已关闭。**」 | 末句自指一份当前 ADR 里已不存在的风险登记（初版即带此句、被指层全仓无踪）= 对已删层的悬空自指 | **approve_reduced**：只删 :18 末句；**✅ 标题保留** | ✅ 那半否决：`## ✅ 已实测全通（日期，路径）` 是跨 ADR 的证据标题 house style（0005:13 / 0006:18 / 0008:25 同形），与第五轮从 0016 布局树清掉的行尾实装勾 `✅ 已建` 不同形 |
| P18 | 0004:23 | 「**v1.4.2** 发行版在使用方账户首跑…run 到终态 passed，旧名并存」 | 版本号是坐标 | **approve_reduced**：只删「v1.4.2」，**保留「run 到终态 passed」** | 它是判据型边界实测：同篇 :20 把「definition 不存在 → `ResourceNotFoundException`」列为前提，能排除该失败形态的只有「run 真走到终态」 |
| P19 | 0028:132/:134 | 「（如实测 **r1** 连撞 3 次瞬时故障…）」「**实测：r1 3 次重试**」 | `r1` 是批次内 run 标签、全仓无定义处 = 伪装成精确的悬空坐标 | **approve**：→「如实测中曾连撞 3 次、第 4 次成功」「实测：一次 3 连重试（光首个 attempt 的 CDP 超时就 30s）…」 | 判据型数字（3 次 / 30s / ~40s / 249s vs 67s / ~182s）与不变量（建连+重试全在 `scope_started` 之前）全留 |
| P20 | 0029:12 | 「**产物落点由注入驱动、机制上不依赖执行环境**…忠实预演论证不变。」整段 | 与紧随的「决策核心」节（:16 + :20 + :22）四点逐项对应的完整重复，Status 头是第三份 | **approve**：删整段，原位留一句「① 的机制与三态见下「决策核心」。」 | :20 还给了本段没有的理由（「唯一差别是 worker 进程在本地还是容器，对报告链接正确性无影响」），删后无信息损失 |
| P21 | 0029:108 | 「留口子 / 待真做时定」三条的 `~~删除线~~ +（第一期已定，见上）` 记账外壳 | 三个口子都已关闭，外壳只承载「曾是待定 → 现已定」的施工节奏 | **approve_reduced**：去外壳但**逐条保留指向权威的精确指针**（「见上『第一期实现定论』」/「已在 [0032]「上传失败处理」结掉」）、:110 的被拒方案与理由、:112 的「materialize 整体移除（[0027]）」历史框定与末句转正叙述；**节名须容纳 :113 归属转交与 :114 已证实两类**（如「## 已结项、被拒方案与归属转交（护栏）」） | 原 fix 的「每条只留结论一句 + 被拒方案」会连带削掉那三处精确指针；且提案称 :113「仍是真口子」与 0032:24「Fargate 特有韧性 backlog 全部收敛」不合 |
| P22 | 0029:78 | 「下面几点是第一期敲定的定论（「留口子」里对应项已标状态）：」 | 纯过场句 + 写作时的自我核对说明；前半由 :76 标题原样承载 | **approve**：删整行 | 后半指向的正是 P21 要去掉的记账层，删后无悬空 |
| P23 | 0032:28 | 「**实测数据（4 次真跑，2026-07-12，真实 AWS 账户/us-east-1；…）**」里与 :26 标题重复的三项坐标 | 相邻两行原样重复 | **approve**：只留「用例 × 引擎、`--assertion-votes 1`、编排脚本毫秒级抢 `step_started` 窗口发 StopTask」 | 证据自包含性由 :26 标题保住（含 `stopTimeout=120 已 deploy` 前提）；保留的后半正是「中断怎么造出来」的可复核前提 |
| P24 | 0032:32 | 表格首行「4~11s（p99=10.8，**run-1 baseline**）」 | run 序号是坐标 | **approve_reduced**：→「4~11s（p99=10.8，**基线 act 样本**）」 | 「baseline」不是坐标而是取样边界：本行列头是「Nova（3 中断样本）」，削尽会让 p99 被读成中断样本上的统计，而该数字正被结论 3/4 与 :52 当判据引用 |
| P25 | 0033:154 | 「**收窄后真部署真跑验证无 AccessDenied**（两引擎 ×（确定性+AI），Midscene Bedrock **1867 tokens** / Nova act 全 passed…）」 | 1867 是单次真跑的 token 计数 = 坐标型，不支撑本句结论 | **approve_reduced**：只删「1867 tokens」，**保留「Midscene Bedrock / Nova act」这对服务面归属** | 那对服务名是本句与 IAM 表 :148/:149 两行收窄的唯一对应；删掉后「（确定性+AI）全 passed」只剩泛指 |
| P26 | 0034:133 | 节标题「（**均已实装**：机制二/三/四有地基实测支撑，机制一从 [0024] seq 不变量推导…）」 | 零指针的进度状态完整重复（真源 = Status 头「已全部实装」+ 各机制正文的实装交代） | **approve**：删「均已实装：」四字 | 红线十项逐条过关；括注保留的证据归属（哪条有什么支撑）与两个测试名全留；`grep 四个关键机制` 全仓仅此一处、不构成指针 |
| P27 | 0034:234 | 节标题「## Engine port 演进：pull-iterate → 增出 fire-and-forget（**已实装**）」 | 同上族；正文首段自带更精确的实装交代 | **approve**：删「（已实装）」 | code 侧两处引用（`ports.py`:15、`detached.py`:50）只引节名前缀，删括注不产生悬空 |
| P28 | 0037:197 | 节标题「（反向链已落各 Status 头；**本 ADR 翻 Accepted 时标注已同步**）」 | 后半句是纯施工记账，落地状态由 Status 头承担 | **approve**：→「## 对既有 ADR 的影响（反向链已落各 Status 头）」 | 前半句有导航价值（旧 ADR 侧也能查到）、保留；同 species 已于 dfd867e 在 0039 获批删除 |
| P29 | 0037:212 | 「…已随各层校准（**逐文件到期点见当时的 commit**）」 | 不可定位的软指针 + 施工记账（「当时的 commit」对未来读者无从检索） | **approve**：删括注 | 句子主干「已随各层校准」已传达该信息；本行的 `guides` → `docs/internals/` 走客观改（#82） |
| P30 | 0037:184/:185/:186/:189 | 布局树四处「（今 core/）」「（今 cli/）」「（今 gherkai/；…）」「（今 worker/ + lib/ 收进包）」 | 「今」在这棵目标态树里指施工前，今天逐字读成「现在」即与事实相反；其中两处与左栏同名、零信息 | **approve**：删 :184/:186 两处；:185/:189 的「今」→「原」（重命名映射保留，0016/0033 里还有旧目录名） | 已核目标态已实现（根无 `gherkai/`、novaact 下无 `worker/`+`lib/`）；同 species 先例 = dfd867e 删 0037 旧「（当前 `gherkai/gherkai/names.py`）」 |
| P31 | 0040:17 | 「**用户补充的事实：**本地开发时同一个人常在写被测应用代码与对应的 step 代码之间切换…」 | 会话来源标注（谁在对话里补的），对未来读者不承载受保护要素 | **approve_reduced**：只删这五字（含冒号），**不另加「实际画像：」标签** | 「默认画像」已是 0040 决策 2 与 0038 的既定说法，另起近义标签会多一个不在词表里的准术语；背景节相邻两段本就无标签起句 |
| P32 | 0041:30 | 「`worker.log` **38 行**、零 ANSI 颜色码」 | 行数是单次真跑的现场坐标 | **approve_reduced**：→「`worker.log` **收下了那批流水**、零 ANSI 颜色码」（不取「有内容」） | 本句判据功能是「终端只多一行 vs 一整批流水落盘」的对照，排除「文件建了但流水丢了」；降到「有内容」连那行位置提示自身都能满足，判据失效 |
| P33 | 0043:143 | 「**ADR 范围到 0043**、」 | 一次性施工坐标：`CONTRIBUTING.md`:42 现为「0001-0045」，该上界随每篇新 ADR 递增、与本篇决策无因果 | **approve**：删该分句 | 同条其余两项（目录树两行、护栏枚举句）仍是可核落点，本节的审计功能不受损 |
| P34 | 0043:147 | 「；全仓 `uv run pytest` **1197** 通过。」 | 测试总数快照（现已 1357+） | **approve_reduced**：→「；全仓 `uv run pytest` 通过。」（**保留命令**） | 命令是稳定可复核的调用形态、属精确指针；同句「38 用例 / 24 用例」是这两只护栏的规模、与括注断言清单一起构成判据，保留 |
| P35 | 0045:85 | 「（源路径随**本次改名**同步）」+ 中间那句三层一致性机制 | 「本次」是任务时点指代 | **approve_reduced**：只改指代与角色名（「随决策二的 `docs/guides → docs/internals` 改名同步」、「使用者侧 agent」→ 全名），**不压那句一致性机制**、并补一条到 0043 决策四/六的指针 | 压缩被驳：0043 决策四的完整表述含三条转换规则与「为什么不能 link」，本节只留三个要件名、本身已是简短重述且未漂；压后长度几乎相同却丢掉「原始维护的文档 vs skill 引用的知识」这一对照框架（本节骨架） |
| P36 | CONTEXT:269 | worker 定位链四级清单 | 机制细节、权威在 0037 决策 3 与 `compose.py`；本轮 #110 证明这次复述当场就压错了级 | **approve**：定义 →「组合根解析「用什么命令起某个引擎的 worker」的固定优先级顺序，逐级尝试、全部落空即报出带安装指引的错误。开发态与分发态同一条链、不设开发模式特判（见 ADR 0037）。」 | 受保护要素（第 2/4 级的 why、被拒的进程包装层、全 miss 抛结构化异常的不变量）都在 ADR 0037 决策 3 与 `resolve_worker_cmd` docstring 里；fix 保住了「不设开发模式特判」这条不变量 |
| P37 | CONTEXT:144 | 「（清洗会把不同输入映射成同一输出、制造静默撞名）」 | 是 why + 反模式 → 按 CONTEXT 反向判据应搬回 ADR；ADR 0025 已自包含该理由与后果、例证 | **approve**：删括注，定义收到「…核心既不把它解析成路径也不清洗其字符。唯一性由调用方保证；需要安全字符的消费层自行做可逆编码（见 ADR 0025）。」 | 已核 ADR 0025「id 是不透明标识符」段逐字同义地含理由 + 撞名后果 + 两处既成事实，ADR 侧无需补写 |
| P38 | CONTEXT:210 | 「避免在已损坏的环境上继续调用 AI 徒增费用与误导性结论」 | 短路决策的 why（省钱 + 不在损坏环境上产生误导性假失败） | **approve**：定义只留「是什么 + 作用域 + 被跳过的 step 怎么记 + 见 ADR 0031」 | ADR 0031 决定六与 `run-scope.mts` 头注都逐条自包含该理由 |
| P39 | CONTEXT:140 | 第二句「一个 run 产出两样结果：机读的汇总判定与人读的归集索引，后者只链接引擎原生产物、不融合其内容」 | 「只链接、不融合」与「引擎原生产物」条（:226）近逐字同源，前半与 :216/:219 两条各自定义重复 | **approve_reduced**：压成一句规范名联结「其结果面分判定真值与派生视图两条（各自见本表）。」+ 把 ADR 指针移到第一句句末；删逐字重复半句 | 整句删越界：句中两个非规范说法本身就是漂移点，正确处置是换规范名而非抹掉（决策八要求词表用规范名，且这属放行的带指针重述） |
| P40 | CONTEXT:3 | 「交付物共六个——…五个 Python 发行包，Midscene worker 是一个 npm 包」 | 包计数与发行形态是实现细节（skill 格式明写 CONTEXT 应完全不含实现细节），且是枚举型内容 | **approve**：压成「交付物含执行核心库、运行时、命令行、部署 provider 与两个引擎 worker；使用方写 `.feature` 并用命令行执行、不对着它的 API 编程，故称工具不称框架。」 | 定位理由（故称工具不称框架）在候选之外、原样保留；发行形态与计数权威在 0037 与 CONTRIBUTING；两语言这一结构事实另有 :97/:284 两条承载 |
| P41 | CONTEXT:292 | 第二句「回收在推送镜像与部署时顺带执行，没有定时任务（见 ADR 0038）。」 | 讲的是清理 pass 的触发面 = 机制实现细节，非本术语定义 | **approve**：删第二句；并**去掉「两个前置条件」的计数**（ADR 0038 把「仍被某版本 SSM 映射引用」也列为并列前置条件，计数已脆） | 被拒方案与 why 在 ADR 0038「清理 pass」条自包含（含「靠定时任务：多一个常驻资源与凭证面」的否决） |
| P42 | CONTEXT:284 | 「不做兼容矩阵，替代物是执行前的版本一致性比对——命令行新于后端即拒绝执行、无放行口，旧于后端只告警」 | 后半是 skew 三态的操作性行为细则（0037 决策 7 与 `check_version_skew` 的地盘），留在词表即第二事实源 | **approve**：第二句压成「不做兼容矩阵，替代物是执行前的版本一致性比对（见 ADR 0037）。」 | 「不做兼容矩阵」这个被拒方案标记留在词条里；放行口的被拒理由在 0037 决策 7 与其被拒条双处自包含。**顺带印证提案**：实装是 ok/warn/block/skip 四档，词表只写两档、本就不全 |
| P43 | CONTEXT:51 | (a)「故 feature 作者无需写代码，这组原语的能力边界即产品的能力边界」 (b)「但对称只在命题清晰时成立，措辞有歧义时两侧可能给出不同判定」 | (a) 是定位论断（:100 词条已有家）+ ADR 0018 开篇逐字存在 | **approve_reduced**：只删 (a)，**保留压缩后的对称限定**「两个引擎对称实现，措辞有歧义时两侧判定可能分叉（见 ADR 0018）」 | (b) 不批：它是 ADR 0018 定为「对 0010 对称论断的扩展 + 边界修正」的受保护要素，且 0018 专门存档了「据一个误判跳到推翻对称论断」的教训——删掉后词表只剩未加限定的「两个引擎对称」，正是被判为过激的那句 |

### 已驳回（提纯 reject，10 条）

| # | 文件:行 | 候选 | 驳回理由（一句） |
|---|---|---|---|
| X1 | 0036:24 | 「`--capabilities` **不建会话、不读 stdin、零费用**」与 :48 逐字重复 | 12 字、**同句内已带指针「契约见「5.」」**、且未漂 → 红线「只压同一事实多处**完整**重复**且已漂移**」两道闸门一道都不过；git 证实 4fc87a4 是主动新增该指针并有意保留三属性，不存在旧描述层；fix 还会删掉入口名 `--capabilities`（本节标题即「注册表清单是能力自述对象的一个键」）并丢掉决策 2 可行性的 why |
| X2 | 0005:17 | 「同一份 `.feature` 被两套 runner 各自加载、各驱动一个引擎，都通过：」 | 它是三条 bullet 唯一的列表引导句，而标题与它之间插着 :15 整段演进块引用 → 删后 bullet 会被读成「演进注」的展开，而它们实际是 M2 实测证据；丢的正是骨架的框定/次序功能 |
| X3 | 0016:265 | 「（**已越过**：云端 adapter + IaC 在 v1.1 填齐、无状态批量运行 v1.2 已实装…故当初「等填 adapter」的乐观预期对它不成立）」 | 三项受保护要素叠加：Status 头明写「版本切分 v1.1 行与「现在不做」条**回指该注**」（文档自设的回指点）、它是对本句自身前瞻的就地自我纠正（脉络必须紧贴错预期）、「已越过」清单与 v1.1.0/v1.2.0 行不同粒度 |
| X4 | 0017:5 | 「（此句为上云前的原始表述…**已按此倾向落地，见 Status 头与下「何时坐实」的演进注**）」 | 「下「何时坐实」的演进注」指的 :33 是全文唯一记「A/B 实测未做 + 成本孰优至今未量化」的地方，Status 头不覆盖那一面 → fix 是拿准确指针换不准确指针；且括注本身是红线放行的「简短重述 + 指针」，就地防误读 |
| X5 | 0024:168 | 「（原曾 defer 为「动 port 影响两个 adapter」，自述入口机制成型后成本已降到一个 flag。）」 | 它是「让 `Engine` port 自声明 `min_grace_s`」这条**未取路径 + 其代价**在本文的唯一残存记录（:168 主文只回答「为何住 worker 侧」）；code 印证该护栏非空话（`ports.py` 的 `Engine` 至今只有 `run_scope` 且明写「本签名即全部契约」）。提案方自标低置信，按「拿不准即 reject」处置 |
| X6 | 0026:91 | 末句「故此条「schedule 接口/旋钮不变」对无状态批量运行**不成立**，见 [0034]」 | 它与条首 ⚠️ 撤的**不是同一句断言**（⚠️ 引的是 :70 停止机制那层，末句撤的是本条自己加粗的「均在 adapter 内部、schedule 接口不变」并给出作废范围）；位置上紧接「两种驱动模型按命令并存」，承担范围限定的骨架功能 |
| X7 | 0029:48 | 「不用官方 `S3Writer`」的三条理由（对称 / 时序可控 / 错误可观测） | 两半依据都被证伪：:42 括注**根本没有那三条理由**（它给的是两引擎各自的机制名，是论点的落地）；:48 行内三词是决策理由（why，红线绝不删）、已带指针且与 :81 零漂移，且承担结构功能——上一行刚介绍官方通道 `S3Writer`，读者当场要的就是「那为何不用」 |
| X8 | 0030:226 | 「现在做 / 留口子」三条的正文 | 三条都是**带指针的简短重述**（指针就在句内：「落库形态如上…组合根接线见决定七」「详见 [0016]『cli backend 选择』节」），且 :212 自述「这里记三条」→ 提案据以突破红线的「漂移证据」不成立；fix 还会删掉 `S3ResultStore`/`S3ReportStore` 这两个全篇唯一的 code 符号指针与逐决策状态粒度 |
| X9 | 0038:3 | Status 头括注的七项真账户列举 | 「实测项 1-7 清零」中的编号短语即指向 :145「## 实测项」节，七项是该节标题的压缩重述、逐条对得上、未漂 → 正落在方法点名的已知误伤形态；另承载两件不可从别处速读的内容：「真账户」证据等级限定与「多平台镜像缺口定为已知边界、不补校验」的边界决定 |
| X10 | 0042:234 | 「**审查修正（传输落在队列线程内）后再跑一次：Nova 正常完成 2/2…掐在 scope 中途 4/4 张在 S3**」 | 提案前提不实：同句前半覆盖的是 Nova 掐在 scope 末 + Midscene 掐在中途，末句复跑是 **Nova 中途路径的唯一证据**（删了「两引擎中途中断路径都已坐实」即悬空）；「4/4」是「引用数 = 落地数」的完整性比例（判据型）；「审查修正后再跑」是证据有效期限定（前两次跑在修正前的实装上） |

---

## 四、主观发现待批（43 条，S1-S43）

> REDUNDANCY / SEDIMENT / TONE 的主观面。每条 = 原句摘 → 改写句。

### 4.1 使用者面（10 条）

| # | 文件:行 | 原句（摘） | 改写句 / 建议 |
|---|---|---|---|
| S1 | user-guide/configuration.md:3/:116 | 「本页是 gherkai **全部**环境变量与跨命令通用选项的清单」+ 表 9 行 | 表缺 8 类同名多命令项（`--assertion-votes` / `--default-job-timeout` / `--scope` / `--tags` / `--scenario` / `--expose-local` / `--tunnel` / `--max-concurrency` / `--worker-variant`），而表内反收只属 `run` 的 `--grace`/`--quiet`。倾向**补行**（读者到这页正为查「`plan` 收不收 `--assertion-votes`」），并把 :116 改为「下面这些选项在多个**运行类**命令上同名同义（`deploy`/`destroy` 一侧的 `--vpc`、`--stop-timeout`、`--refresh-context`、`--container-engine` 见 cloud-backend.md）」、:3 的「全部…清单」→「环境变量与跨命令选项的清单」；`--max-concurrency` 行只写归属 + 一句指针，别把回落规则抄成第三份 |
| S2 | user-guide/README.md:10 | running-and-results 行主题列只写五条命令 | 补「、`list-engines` / `list-deterministic` / `doctor` 的用途与常用选项」（该页 :3 自述与 :57-59 已 owner 它们，而 README 把 doctor 分给了 getting-started 与 troubleshooting 两行，「doctor 的选项」无处可查）；「退出码」写成「退出码（部署方命令的退出码归云端后端页）」，cloud-backend 行补「`deploy` / `destroy` 的退出码」 |
| S3 | user-guide/troubleshooting.md:66 | 「不需要 AWS 凭证的命令只有 `plan`、`list-engines`、…」七项完整清单 | 与 getting-started.md:61 的逐项相同副本（当前无漂移）。倾向压成带指针的短句：「不需要 AWS 凭证的命令见[开始使用](./getting-started.md#aws-前置)那一条清单（…）；`status --wait` 会接着推进这个 run，那时需要凭证。」清单本体只留 getting-started 一份（owner 表把「AWS 凭证与 region」判给它） |
| S4 | user-guide/troubleshooting.md:13 | 「自检只做读操作：…不产生 **AI** 费用。」 | 同一事实四处三种措辞（getting-started「模型费用」/ 本处「AI 费用」/ running-and-results「模型费用」/ writing-deterministic-steps「**AWS** 费用」）。倾向统一成「不建浏览器会话、不调模型，不产生模型费用」；writing-deterministic-steps:157 的「不产生 AWS 费用」偏强（`doctor --backend cloud` 会发 SSM/DDB/S3/ECS/Lambda 只读调用） |
| S5 | README.md:3 | 「**全部组件**运行在你自己的 AWS 账户内」 | 与同页 :50「本机档（默认）：worker 是本机子进程」冲突（默认形态下 worker 与 CLI 都在使用者机器上）。→「浏览器、模型与云端组件全部运行在你自己的 AWS 账户内，本机不需要安装浏览器。」（保留「没有第三方服务托管」这层意思，交「判定由谁做出」节展开） |
| S6 | core/README.md:37 | 模块表把「自建后台或无状态批量运行要用」的入口列到 `gherkai_core.persist` / `.project` | 漏这条路径真正的编排入口 `gherkai_core.reconcile`（`tick(run_id, meta)`，`project`/`plan_next` 正是被它调用的纯函数）。倾向左列补 `gherkai_core.reconcile`、右列补「以及幂等推进一次 run」；若 owner 要守包页「只许四样」的克制，则至少确认这一行不再暗示 persist/project 就是全部入口 |
| S7 | skill/SKILL.md:86/:105 | 「被 `--fail-fast` **掐停**」 | 比喻式动词，随包发到使用方项目（护栏 FORBIDDEN/COLLOQUIAL 管不到 skill 里这个词）；同族已从人读层清过（b95bf78「掐断→中断」、d3b7675）。→「被 `--fail-fast` **中止**」；:35「别被它带偏」→「按上面那条对齐参数，不要照它只改 `submit`」 |
| S8 | skill/SKILL.md:57/:114 | 「别解析 HTML 报告、别猜产物**路径**」「别猜产物路径：顺判定明细里的 `ref` 走，本机与 S3 两档同律」 | CONTEXT:228「产物指针 (artifact URI)」的 `_Avoid_` 正是「路径、本地路径」，而此处恰在讲「本机与 S3 两档同律」= 踩在该词条要防的误读上。→「别自己拼产物位置：顺判定明细里的 `ref`（产物指针）走，本机与 S3 两档同一形式」 |
| S9 | skill/SKILL.md:61 + references/engines.md:74 | 「**前置检查**不替你发现（它只查本次用到的引擎）」 | 规范名是「执行前预检」（CONTEXT:162，`_Avoid_: 预检、环境自检`）；同一 skill 里另一处已用规范名「用例预检」指 plan → 两个不同机制一个规范一个自造，易混。→ 两处统一「执行前预检」；若判该词对使用者面偏内部，走词表 owner 改名、别在 skill 里造第三个名字 |
| S10 | internals/cloud-backend-carriers.md §5（:81/:90/:92 ×2）+ deterministic-step-lifecycle.md:70 + 图源 2 份（`cloud-backend-carriers-revision-pinning.json` :5/:62/:204、`deterministic-steps-truth-sources.json` :20/:172） | 7 处「提交时刻」 | CONTEXT:184「终态提交点 (commit point)」把「提交时刻」登记在 `_Avoid_`，但此处的「提交」= submit 一个 run，与 commit point 无关（同词两义碰撞）。**倾向收窄词表**（把 `_Avoid_` 改成「提交时刻（指 run 级终态落定那一步）」）而非改 7 处词：此处表达准确、无歧义读法，为规避碰撞全仓改词会让「定义期解析、运行期照抄」这组表述变松。若 owner 反选改词 → **须改图源后跑 `tools/build_diagrams.mjs` 重出 SVG、同 commit** |

### 4.2 contributor 面（13 条）

| # | 文件:行 | 原句（摘） | 改写句 / 建议 |
|---|---|---|---|
| S11 | internals/cli-json-contract.md:187 | `source` 取值「`uvx 兜底拉起（版本 X）`」 | 「兜底拉起」是被 d3b7675 从文档与图源清掉的那批比喻动词之一，此处因**绑着 code 字面量**（`compose.py`:275 的 `source=f"{launcher} 兜底拉起（版本 {v}）"`，会进 `list-engines --json`）而留下。**先改 code**（如「uvx 临时拉取（版本 X）」）再同步本页；本页现状暂按「与 code 一致」保留 → 移交 code-health |
| S12 | internals/artifacts-and-evidence.md:108 | §5 边界表第 3 行把 `--no-report` 机制完整重述一遍（§2 末 bullet 已给全口径） | 两处当前一致，但同一规则的第二份完整副本是后续漂移点（ADR 0037 决策 3 是权威、§5 那行已带该指针）。→「它的含义是「不生成产物」，不是「落到别处」——注入与 env 的完整口径见 §2 末条」 |
| S13 | cli/DEVELOPMENT.md:67-74 | 「文档与文案护栏有六份位于本包的 `tests/`」六条 bullet 各完整重述覆盖范围 | 与根 CONTRIBUTING:124-133 八行护栏表构成第二份完整副本，且**已漂**（漏「根 README 只查零内部指代 / 可达性归 test_user_docs」这层分工、漏 test_user_docs 的图那一半）；本行自己已写「全仓清单见根 CONTRIBUTING.md 的「测试」节」。→ 压成「本包 `tests/` 下有六份文档与文案护栏：…（文件名清单），各自覆盖范围见根 CONTRIBUTING.md「测试」节的护栏表」+ 保留 :76 那条本包独有的操作提示（改契约页后跑 `render_skill_contract.py`）。**保留文件名清单**（「本包有哪六份」是 cli 侧独有信息） |
| S14 | CONTRIBUTING.md:50 | 「`wikipedia_zh.feature` ← 非英文 UI **探针**」 | CONTEXT:85 把裸「探针」登记为「探针用例」的 `_Avoid_`，同文件 :26 用的是规范名「探针用例」。→「非英文 UI 探针用例」。**待 D8（裸「探针」该不该退役）定** |
| S15 | engines/novaact/DEVELOPMENT.md:104 | 「# 只运行本引擎：**2026-09-17 实测 209 passed**」 | 命令注释里挂一次执行的日期 + 通过条数 = 坐标型现场（今日复核仍为真，故只报沉积不报 STALE；每加一条用例即失真）。→「# 只运行本引擎」 |
| S16 | engines/midscene/DEVELOPMENT.md:75 | 「`npm test` # …（**2026-09-17 实测 183 pass / 0 fail**）」 | 同上（今日逐文件数 `test(` = 183，仍为真）。→ 删括注、保留命令转述（那段是 `package.json` 的 `scripts.test` 逐字转述，属有用定位） |
| S17 | core/tests/README.md:38 | 「可在会话里用 `!` 前缀直接执行」+ 代码块内两条命令真带 `! aws …` | `!` 是 Claude Code 会话的 bash 前缀、不是 shell 语法：人复制粘贴进 zsh/bash 会触发历史展开报错，这两条一次性建表建桶命令因此不可照抄（本文件其余代码块都可直抄）。→ 块内去掉 `! `，工具便利说明留在块外一句 |
| S18 | cli/DEVELOPMENT.md:74/:76 | 「文档漏键即**红**」「相等性断言**会红**」 | 以「红」作动词 = 口头语（ADR 0045 决策六：技术文档不允许俏皮与口头语；本仓已清掉「跑」等同类）。→「文档漏键即测试失败」「相等性断言会失败」 |
| S19 | .github/workflows/README.md:124 | 「也是一次没必要的**红叉**」 | 同上。→「也是一次没必要的失败构建」 |
| S20 | core/tests/README.md:31/:53 | 「实测**刷**近 1.5MB 全 ACCEPT」「但用独立资源**最稳**」 | 同上。→「实测写到近 1.5MB 仍全部 ACCEPT」「但用独立资源最可靠」 |
| S21 | ai-eng/REFERENCES.md:3 | 「**抢救自原 `midscene-novaact-prototype-guide.md` §10（该文档已退役）**，并补入本项目实测中用到的关键路径。」 | 被引文件已不在库（`git log -S` 只命中两个早期提交），今日读者无从访问其 §10；本文属 contributor 侧 AI agent 面（优化向密度与精确指针），该句不承载 why/trade-off/被拒方案/不变量（指针已失效）。→ 整行留「> 本文登记本项目实测中用到的外部一手来源与源码内点。」若 owner 认为出身仍有价值，最小改法 = 保留但标明「该文档已删、不可访问」 |
| S22 | tools/e2e_harness.md:9 | 「真 spawn worker、真下发 job（stdin）、真收事件流…」定位段 | 与 `e2e_harness.py` 顶部 docstring 几乎逐字重复，而本文件 :4 刚声明「机制原理…见 docstring，不在此复述（单一事实源）」；**已开始漂**（md 清单有「真 grace 秒数」、docstring 缺；「下发/喂」「网络+凭证／网络/凭证」分叉）。→ 压成带指针的简短重述（保留一句定位 + 「具体覆盖哪几项真实行为见 docstring」）。判断边界：若 owner 认为手册开篇的独立可读性更重要，则反向修法 = 以 md 为权威、给 docstring 补「真 grace 秒数」 |
| S23 | tools/e2e_harness.md:3 | 「**读者：** 后续接手 worker 端到端验证的 **AI tool**（也含人）」 | 「AI tool」非规范名（CONTEXT:125「contributor 侧 AI agent」），且易被读成「被操作的 AI 工具」而非执行者；`tools/*.md` 在 TONE 术语面射程内。→「> **读者：** 后续接手 worker 端到端验证的 contributor 侧 AI agent（也含人）。」 |

### 4.3 方法文档与索引（6 条）

| # | 文件:行 | 原句（摘） | 改写句 / 建议 |
|---|---|---|---|
| S24 | ai-eng/code-health-review.md:73 | 「**方法复盘（落地提交说明里…）**」整段 | 与 doc-health-review.md:136 **逐字重复**（机械比对两文件全部 >60 字的行，完全相同的仅此 1 行），一改必漂一份；本文件 :67 已有同款压缩先例（「待批报告的呈报形式同姊妹任务」）。→「**方法复盘**：写法、内容与退场判据同姊妹任务（见 `doc-health-review.md`「产出与提交」末条），把 trailer 换成 `Code-Health-Round`」（同时解决 #165 的 SEDIMENT 引用） |
| S25 | ai-eng/doc-health-review.md:51 | internals 侧的复盘侧重未点名机械护栏 | 其它每类（用户文档 / contributor / skill）都点了护栏，只 internals 空缺——而 `cli-json-contract.md` 的字段清单恰是全仓唯一「由真值集逐键断言」的文档表（`test_cli_json_contract.py` + `deploy_aws/tests/test_workers.py`）。→ 末尾补「`cli-json-contract.md` 的字段清单已由 … 对真渲染器逐键断言，本任务只查字段**释义**与出现条件」（避免审计员手工对字段表——既耗时又照不出遗漏项） |
| S26 | .claude/skills/doc-diagram/SKILL.md:6 | 入口复述了方法文档的规则与完整命令（`validate --quality showcase` 零告警、`--png` 全式、PNG 自检后删、JSON 与 SVG 同 commit、已发布图连 HTML 入库） | 与 `diagram-authoring.md` 步骤 4/5/7 及 ADR 0045 决策七双写；护栏 `test_diagram_skill_points_at_the_method` 的 docstring 自述「它只指向方法文档与构建脚本，**不复述规则**」→ 当前正文已越过这条自述；两份 health-review 入口的形态是「方法唯一真源在此，本入口不复述要点」一句。→ 压成一句指针 + 保留反模式一句与护栏要求的两个字面量 |
| S27 | ai-eng/doc-health-review.md:89 | 「亲历中正是层数多的长文件把并行审计员撑到停摆**，限读后即过**」 | 「限读后即过」是上一轮的施工节奏尾巴（那一轮改完就好了），对未来执行者无信息；规则与理由由前半完整承载。→ 删这四字 |
| S28 | ai-eng/doc-health-review.md:60 | 「`docs/adr/*.md`（重点，**80% 给 AI 读**）」 | 同一事实在本文三处（:7 价值段、:15 准绳、:60 覆盖范围括注），权威在 :15（CLAUDE.md「读者比例决定优化方向」条是源）。→ :60 括注压成「（重点）」，:7 保留（价值论证的一环） |
| S29 | docs/README.md:5 | 文档地图三列未登记 `docs/diagrams/` | 它是 docs/ 五个子目录之一、装着全部图源与静态图，只在 `internals/README.md`:15 有说明；而 ADR 0045:33 定「`docs/README.md` = 全部文档的地图」。→ 在「想懂机理的技术读者」行第三列末补「配图的图源与静态图在 [`diagrams/`](./diagrams/)（改图与形态见 internals 索引）」（一句即可，规则 owner 是 internals 索引与 0045 决策七） |

### 4.4 ADR 面（10 条）

| # | 文件:行 | 原句（摘） | 改写句 / 建议 |
|---|---|---|---|
| S30 | 0042:214 | 「**文档（反向链逐处列出）**」块：要在 `cli/README.md` 的「退出码节」补一句、`index.html` 描述含 evidence 行、CONTEXT「术语表 kind 枚举」 | 三处落点在 ADR 0045 重组后多已悬空（cli/README 已无退出码节、也无 index.html 描述；CONTEXT 已是严格词表、无「术语表 kind 枚举」）。倾向把整块压成一句「本决策的文档面已落地：使用者面在 user guide 的运行与结果页，机读字段在 internals 的 CLI JSON 契约页，术语在 CONTEXT.md」，保留 :208-213 那批仍指向稳定物的 ADR 反向链。最小改法：只保留「explain 用法」一项、其余两项改写为现落点 |
| S31 | internals/architecture-overview.md:77 + 0037:191 | 「仓库里的 `features/`、`tools/`、`docs/`、`graphify-out/`、`skills/` 都不随包分发」 vs 0037「features/ · tools/ · docs/ · skills/gherkai-evals/ ← 不分发」 | 黑名单式枚举两处已互相漂移（一处有 `graphify-out/` 一处没有、都漏 `.github/`/`.claude/`/`.vscode/`）。→ 改白名单式：internals:77「上表列出的发行物之外的仓库目录（示例用例、工具、文档、知识图、评测资产等）都不随包分发。」；0037:191 保留两条注（build_push_workers.py 退役、评测资产 0043）、枚举改「其余仓库目录一律不分发」。**注**：0037 那棵树标题写明「目标态」且行内有历史框定，改写要避开红线 |
| S32 | 0016:210 | 两个引擎的**文件级**模块清单整份复述 | 与 `engines/*/DEVELOPMENT.md` 双写，而 CONTRIBUTING:66 已把文件级权威定在各包 DEVELOPMENT 并明说「两处并存必然漂移」——本轮 #39（漏 `error-text.mts`）正是这句的实现。→ 只折叠**纯叶子名单**：midscene 支保留 `bin`/`index`/`resolve-hook` 三行原注 + 「`src/worker/`（薄 worker：入口 `run-scope.mts`；`evidence.mts`=step 级机读证据…[0042]）——文件级清单见 `engines/midscene/DEVELOPMENT.md`」；novaact 支压成入口 + 指针并**原样保留**拆分注（含「仅 ai_steps 的进一步拆分仍是留口子」的 defer 决策）。**别按原提案字面执行**（会连带删掉 `index.mts` 的公开 API 契约、`resolve-hook.mts` 的 0037 决策 4 指针） |
| S33 | 0016:207/:210 | 同一条 ADR 0042 指针（「evidence=step 级机读证据抽取/落盘，供 `gherkai explain` 消费」）在相邻五行内逐字重复两遍 | 随 S32 一起落：midscene 支保留完整句、novaact 支简作「`evidence.py`（与 midscene 对称，[0042]）」，或把这条对称性上提到树下说明条里说一次 |
| S34 | CONTRIBUTING.md:63 | 根目录树未登记 `.vscode/settings.json` | 它入库、且承载一条仓库级约定（放行 zh-hans 的 unicodeHighlight，使 ——、·、→、≠、① 不被判同形攻击），全仓文档零处提到它；但该树本就是「有内容的目录 + 主要根文件」的策展清单（另漏 `.gitattributes`/`.gitignore`/`.graphifyignore`/`.python-version`）→ 属「该不该收录」的编辑判断。倾向补一行「├── .vscode/settings.json ← 放行中文排版符号的 unicodeHighlight（真同形字符仍高亮）」（它是那条约定唯一的可发现入口）；备选 = 在树下说明里界定「点文件不列」 |
| S35 | docs/diagrams/cloud-delivery-identity.json:247 | boundary label「发行物（**维护者侧**）」 | 同图节点 label 是「官方基础镜像」、note 写「官方基础镜像与使用方 build 的镜像…」、user-guide 对应格写「官方发布」→ 同一张图两种叫法；但「维护者」在这里是**正确窄义**（基础镜像确由维护者 CI 发 GHCR），宿主页 internals:13 正文也用「维护者 CI」。→ 纯口吻一致性，二选一：(a) 改「发行物（官方侧）」并**重出 SVG/HTML 同 commit**；(b) 不改（与宿主页正文一致更精确）。无论哪边都不要把「维护者」加进 RETIRED_TERMS |
| S36 | 0005:27 | M2 接线坑的 TS 条以现在时写「`midscene` 子工程是 commonjs，故 `engines/midscene/bdd/` 加局部 `package.json` 标 `{"type":"module"}`」+ 要求 `NODE_OPTIONS="--import tsx/esm"` 启动 | 两条均已被 0037 决策 3 反转（整包统一 ESM、bin 在进程内注册 tsx、`bdd/` 已删），同段 Python 条已带就地历史注、唯此条漏。但整节已有两重历史框定（标题「✅ 已实测（M2 起）」+ :15「演进（v1.0）」块）→ 属「框定要不要加细到条级」的判断。倾向补短注：「（当时子工程为 commonjs、`bdd/` 目录尚在；今整包统一 ESM、bin 在进程内注册 tsx，见 [0037] 决策 3）」 |
| S37 | 0010:20 | 对标表头「Nova Act (**nova-act-latest**, 纯 IAM Workflow)」 | 裸用已弃用的别名（ADR 0004「模型版本选择策略」明确弃用它、缺省锁定 `nova-act-v1.0`）；节标题带日期算部分框定，但 0004 的同类历史提及都补了「当时的别名 / 已弃用」注。**两列对称**倾向：不改表头，在表下「信号」句前加一句「表头两列的模型都是当时的默认：Midscene 的 Qwen3-VL、Nova 经别名 `nova-act-latest` 拿到的 GA 模型；今默认分别是 `us.openai.gpt-5.6-terra` 与钉死的 `nova-act-v1.0`，别名已弃用（见 [0044]「现值」、[0004]）。」（只注 Nova 一列会反向暗示 Midscene 那列是现行默认） |
| S38 | 0044:22 | 「现值」段只登记两个默认模型 id、不列换默认时要同步的面 | 两个 id 散在 13 份文档（含 5 份用户文档、2 份随包 skill、2 份 DEVELOPMENT），code 侧有护栏（两引擎单测各断言一次）、**文档侧零机械护栏**；本轮 13 处全一致，靠人工一次改齐。倾向**先加护栏**（交 code-health：断言 user-guide/configuration 与 skill 两份 references 的默认模型 id 等于 code 常量），ADR 只加一句**不含文件枚举**的指针（「换默认的同步面由护栏测试机械保证，新增披露面须一并进护栏」）——**不建议**在 ADR 写逐文件清单（那份清单自身就是新的枚举漂移面） |
| S39 | 0037:228 | 被拒方案「受众（装 AWS 凭证、Docker 的**开发/测试工程师**）能装 uv…」 | 「测试工程师」与已弃用的 test engineer 同义、在 0040 正名体系外（全仓「工程师/开发人员/研发」仅此一处）。倾向改「受众（装 AWS 凭证与容器引擎的测试开发）」（被拒方案的理由与结论一字不动）；也可判不改——此句说的是「市面上会装这类工具的人」这一行业受众、不是项目内的帽子 |

### 4.5 评测资产（4 条）

| # | 文件:行 | 原句（摘） | 改写句 / 建议 |
|---|---|---|---|
| S40 | evals/grader-prompt.md:17 | 污染判据只看 `skill_copy_touches > 0 or repo_touches > 0` | 未把 `memory_reads` 纳入评分者判断面，而 ADR 0043 决策七的史实里，第三轮 baseline 正是被同名舞台路径灌进的旧会话记忆污染、由该指标记账抓到（现 harness 跑前跑后各清会话目录、稳态应恒 0）。倾向**不改 contaminated 定义**（它对齐 `summarize_runs.py` 的口径、跨轮可比），在 Rules 末加一句「若 `timing.json` 的 memory_reads > 0，在 critique 里点出（会话记忆可能越过隔离）」 |
| S41 | evals/grader-prompt.md:13 | 评分者只读命令白名单 = plan / list-deterministic / explain / `<sub> --help` | 漏同样零费用零副作用的 `doctor`（不带 `--prefix`/`--backend cloud`）与 `list-engines`——而 eval 5 的核心断言正是「midscene 判为可用且说出来源」，评分者按现白名单无法独立复核、只能信被测 agent 自己的输出。倾向补这两项（保留对 `status`/`run`/`submit` 的禁令：`status --wait` 会真推进 run） |
| S42 | evals/evals.json:9 | eval 1–7 各带 `"files": ["fixtures/wiki-search"]`，8–16 没有 | 与同条目的 `"fixture"` 重复表达同一事实，且**零消费者**（`run_evals.py`/`materialize.py` 只读 `fixture`）。倾向删 1–7 的 `files` 键（单一事实源 = `fixture`），别反向给 8–16 补齐一份必漂的第二真源；若要保 skill-creator schema 形态兼容 → 16 条全带并在 `notes` 写明「files 仅为 schema 兼容、真值在 fixture」 |
| S43 | evals/evals.json:107 | eval 5 的断言 3 与断言 5 各自要求「指出真跑还缺 AWS region 与凭证」 | 同一表现被计两分，与 `notes` 记的尺子演进方向（复合断言拆条、断言原子化）相反，缺省集 122 条的分母对这一点加权两次。倾向删断言 5 尾句，让它只管「判为可用 + 说出来源 + 不建议无用的 npm 安装」；按惯例在 `notes` 追一句尺子改动（断言总数 122→121、与上一轮不可直接比） |

---

## 五、具名提纯审计记录（审计集 46 篇：45 ADR + CONTEXT）

> 动 = 自锚点父提交（dfd867e^）以来有提交、本轮层读重审；沿用 = 区间零命中、按跨轮沿用规则引上轮具名结论。提案数与第三节 P/X 编号一一对应，机械汇总 = **53 条浮出**。

| ADR | 动/沿用 | 层读史实（一句） | 提案 / 判无依据 |
|---|---|---|---|
| 0001 | 动 | 13 层；三个实质大改层逐层**整体替换**（cab6a8e 的「扩到非英文 UI 的路径」三步整段被 82c0e8e 换成重议闸门，旧节零残留；头里「各 130 票」后被校正为 125，与两表 90+35 算得一致） | 1（P1） |
| 0002 | 动 | 7 层；除初始层外全是 1-8 行小层，正文自初始层几乎逐字未动，变动集中在 Status 头——三次**整行替换**（Accepted→Partially→Superseded），无旧头残留 | 判无：`> 诚实存档（判断反复）` 整块形似施工叙事，但以「教训：只认响应 body，不认 HTTP 状态码」收口 = 可迁移反模式，且同文 :19 的 `UnknownOperationException` 假 200 实测事实的存在理由正是这次踩坑，删叙事该实测即悬空；次险「附带实测事实」两 bullet（gpt-5.5 只在 us-east-1、Responses-only）支撑「完全出局、连可选 planning 都当不了」 |
| 0003 | 动 | 17 层（最长）；**「后层叠加、前层未清」的样本**——2f6fdf8 给「待观察」段接上 0044 的 A/B 出口却把旧流程句留在原位，3860d2c 又在头里宣布默认已换 → 同文件「待 A/B 定」与「已改」两层并存 | 2（P2、P3） |
| 0004 | 动 | 14 层；「模型版本选择策略」是三层叠加（5213b2c 加「待定」→ c925d1d 去「（待定）」并内联 A/B 证据 → 8c745ca 加 0044 指针），**待定层被后层完整替换、无残留**；漏下的是初始层起就带的 ✅ 与「残余风险已关闭」 | 2（P17、P18） |
| 0005 | 动 | 11 层；区间 1 层（239e5a8）三处纯原句内替换、零净增行、无新旧并存 | 1（X2 被否） |
| 0006 | **沿用** | 区间零命中（同写法在 0005/0016/0022/0023 各有命中，作对照）；第五轮层读：窗口内唯一层 40fe732 把「未验证 hedge + 后来的证伪结论」这对双层压成单层，当前文无 hedge 残留 | 判无（沿用）：line 12「工程形态 = 形态 A…不是合成一个引擎、也不是单进程统一 runner」是全文唯一点名两个被拒形态的句子；line 9 末「下述原决策脉络保留。」是把 line 5 框成历史的标记 |
| 0007 | 动 | 3 层；区间 1 层只把「第一根穿刺针」换成「第一个 spike」；三层增长里 layer2 只加 Status 头、正文一字未动 → SEDIMENT 的两个信号结构性缺席 | 判无：全文 15 行逐句过——:5 决策前提（无人值守 vs HITL 冲突）、:8-9 决策本体含不变量「敏感数据不进 AI prompt」、:11 被拒方案 +why（跑到登录步暂停等人牺牲无人值守、CI 跑不了）、:13 有意 defer 的 why（避免登录复杂度污染链路验证）、:15 重议闸门（强 CAPTCHA + 0001 指针） |
| 0008 | 动 | 13 层；只有初始层是大改（+30 行全文骨架）。**关键史实：「剩余风险（spike 第一锤要坐实）」与「✅ 已实测全通」两节在初始层同批写入** → 前者不是被覆盖的残留，层读推翻了「它是沉积」的猜测（第五轮 [P61] 已被否，按「被否的存档不落改」不重提） | 判无：四条要点是 code 仍在执行的不变量（`sigv4Fetch` 逐条对得上）；「退路（Option B）」整段是被拒/备选方案含前置条件；「✅ 已实测全通」三段式各跨一条不同的真实边界，末条「关键实现坑」是「必须用代码初始化 Agent」的直接依据 |
| 0009 | 动 | 区间 2 层：dfd867e **纯追加**「适用面」整段（原四段逐字未动）、239e5a8 一个词；历来是「按自己『决定』段的登记要求末尾纯追加」式增长、无覆盖残留 | 判无：:20「明确的非目标」是反模式护栏——点名「不以离开 AWS 作为默认出路」并给 AWS 内三条改进路径（换 Bedrock 其他模型 / SageMaker 自托管 / 调 grounding 策略），删了这条歧路无人堵；:14 gpt-5.5 括注是唯一阻止把 0002 的排除算进 AWS 硬约束战果的防误读护栏 |
| 0010 | 动 | 11 层；区间 1 层 4 处逐词术语替换、无新增段、无被覆盖未删层；沉积形态 = 「spike 期洞察 + 后期在同段末尾追加已落地注」 | 2（P4、P5） |
| 0011 | **沿用** | 区间零命中（全史 4 层）；第五轮 [P62] 已随 a97f912 落地（删会话坐标前缀），现文 line 8 末句即改后形态 | 判无（沿用）：[P63] 末段收尾句被否——它紧跟负向结论（够不到开发者笔记本）之后阻止读者顺推「所以还得重新调研」，是反模式护栏 |
| 0012 | **沿用** | 区间零命中（全史 4 层，末层只加 Status 头） | 判无（沿用第六轮，其为二次沿用、链底 = 密度基线 ec12b4b 的一句裸清单）。**依据最薄，已点名**：建议下轮若仍未动，补一条本篇自身的内容锚（见第八节）。注：本轮对 0012 另报 Status 与 4 条事实面发现，属纠错面、不进提纯槽 |
| 0013 | **沿用** | 区间零命中；第六轮层读：0cd40d3 与 a90554c 两层都是原句内替换/限定词追加，diff 里旧措辞被就地改写、无被覆盖却留下的旧描述层 | 判无（沿用）：:26 括注「（下述三项各自的承载方式见本节末段）」——末段的逐项映射含非平凡落点「会话生命周期=各 worker 内」，第五轮 P54 以「精确指针 + 承载纠偏功能」驳回；:31 段末是「原前提被 0023 证伪 → 承载方式改核心库 → 结论仍立」的收口且专防「公共设施落核心库 = 引擎代码被共享了」的误读，第五轮 P55 驳回 |
| 0014 | 动 | 区间 3 层：c3d3727 是词表拆出的护栏回填（新插「一票 = 一条 AI 断言的一次布尔判定…tally 不是判定状态」+ 确定性 step 条尾追加边界，两处都是新增陈述、未替换旧句）；239e5a8 5 处原地替换；0f48189 只改 REFERENCES 路径 | 判无：:24「- **已定**：AI 断言为默认方向（本 ADR）。」是「现状与未决」节唯一把「方向已定」与下文三条分层的框定句；:20 的「1 用例 × 10 次零抖动 + **不足以反推**」是内联判据型证据；:27 两个 spike 路径真在库；:17「**不要**用 `aiAssert`（抛错黑盒）做投票」是被拒方案护栏 |
| 0015 | 动 | 区间 2 层：dfd867e 即第六轮落地（把「已知边界」第一条换成指针形态，P1 逐字落地）、239e5a8 8 处原地替换含节标题；两层都是整句原地替换，旧层文字无一残留（现文已无「种类」字样） | 判无：:42「点名精确核对某项（如"价格是 ¥99"）也走这层」承载**断言路由归属**（点名 ∈ 第 1 层默认 AI），正是 0020:40 点名要消除的误读；:49「交给专用工具，不强行塞进本工具」是「何时重议」的反转闸门；:34-37 已是第六轮批准的缩小后状态，再压就失去 v1.0 边界的单点枚举面 |
| 0016 | 动 | 区间 11 层（按「--stat 挑大改层」限读 4 个较大层 + 7 个 1-3 行层的差异，未做全量 `git log -p`）；da5002a 与 239e5a8 全是原地术语替换，a9285d3 是布局树的**加法校准**；11 层合计无「旧描述层 + 新描述层」并存 | 2（P8 通过 / X3 被否） |
| 0017 | 动 | 区间 2 层且各 2 行：c3d3727 在 :5 既有括注**之后**追加「本 ADR 说的「上云」只指执行进程这一级」整段（原句零改动）、239e5a8 逐词替换；最老沉积来自 853d730——Status 头 + :5 括注 + :33 演进块**一次编辑写了三份** | 1（X4 被否） |
| 0018 | 动 | 区间 1 层，4 处「确定性锚点→确定性 step」原地同义替换，无新增段落、无旧层残留 | 判无：:29/:40 的「第一批/第二批」与 ①②④⑤ 圈码经真值重核仍是指向 in-repo 活文件的交叉坐标（`features/wikipedia_robustness.feature`:1/:3/:4/:12 逐字带这些坐标）；原语表 `aiNumber`/`aiString` 两行第六轮已被驳回（语境「含已删项，留作设计史」+ :11 已收敛注），不复议；:38「纠正的过激结论（存档防再犯）…全部收回…教训：先证伪最朴素解释」是反模式存档；:33-37 的 4/4 与诊断三步是判据型内联证据 |
| 0019 | 动 | 区间 1 层（逐词术语）；沉积来自更早的 d88f774 / 853d730（`@timeout:` 一条线的增补：:29-31 两条语义 + :50「三个 tag」），而 :5 开篇与 H1 标题在那两层里**一字未动** → 正是本轮 #40 的成因层 | 1（P10） |
| 0020 | 动 | 区间 2 层：03f9d8c 单行随 feature 文件改名；239e5a8 7 处术语替换（含标题、Status 头三处），逐层确认全是整句原地替换、无叠加；更早的「落地现状」沉积已在第五轮缩小落地（0cd40d3） | 1（P7） |
| 0021 | **沿用** | 区间零命中（全史 4 层）；纯决策史文，全文由 Status 头「下文描述 B1 之前（v0.x）的状态」框住，自密度基线以来一字未动、无新增层可沉积 | 判无（沿用）+ 本轮补内容锚：:21-25「保守回退」节（Unknown/And/But 不收窄、零匹配即回退、⚠ 代价「错误声明关键字的 step 不会被揪出」）是被保留的权衡与已知代价，即便补丁已退役也属决策史核心 |
| 0022 | 动 | 区间 1 层，单行替换（「少量确定性锚点」→「少量确定性 step」），零净增行；沉积来自更早叠加的「实现状态」块与「迁移」段 | 1（P9） |
| 0023 | 动 | 区间 2 层：239e5a8 单句内替换（「服务端是大脑」→「决策在服务端（模型侧）」）、90a9b41 只做全角→ASCII；两层合计零净增行、无被覆盖却残留的旧描述层 | 判无：:26 把 `apiVersion 2025-08-22`/`endpointPrefix nova-act` 的出处判回 0006 的句子（删掉会让未来读者把它们当本 ADR 的实锤、把裁决的高置信误推到这一项）；:18 的语言占比含显式证据边界（约 98.6% Python、零 TS/JS，正是裁决 `NO-STILL-NEEDS-PYTHON` 的直接支撑）；:25 第 1 项的「中置信：文档没写≠一定没有」是 :38 重议条两个触发条件之一的来源；:15「（推断，文档未直用 "block" 字样）」是推断与实据的分界标注 |
| 0024 | 动 | 区间 10 层（~54 行；挑读两组大改）：**内容层** 7092c34 + ba5cf54 把「引擎自报下限」从 defer 落为决策——7092c34 把旧 bullet 整条替换、并就地改写 :165 去掉「组合根算 grace 下限」那一半；**措辞层** 6 个 1-6 行的替换。10 层全是原地整条/逐词替换，**零「后层覆盖前层却没删」的残留**；:168 长到约 1100 字符是两层往同一条 bullet 连续就地扩写的结果 | 2（P11 通过 / X5 被否） |
| 0025 | 动 | 区间 4 层：dfd867e 落地第六轮两条提案（:5 施工序列语换成带链接的边界句、:94 的 `@id:` 第三份压成带双指针的短重述）；a9285d3 条尾追加「CLI 侧已履约」；239e5a8 把「未来若某消费层…」升级为「已是既成事实」+ 两处 code 真值；c3d3727 在 :5 末追加「本模块承担用例预检的解析与校验那半」边界。四层全是原地整句替换或条尾追加、零并存旧层 | 判无：:94 的 `@id:` 第三份**没被删、而是加了指向另两份的双指针** → 现命中红线「带指针的简短重述放行」，本轮不得再当冗余提；:82 与 :59 是自包含血缘描述（零 journey / 零 WP 编号）+ CLAUDE.md 要求留的「曾进坑」护栏（`test_plan.py` 两条 fail-fast 用例已核在）；:34 边角清单是「**不自己写展开**」这条被拒方案的全部支撑证据；:88 条尾是不变量（库契约不因单个调用方履约而变死分支）+ 明写的被接受代价 |
| 0026 | 动 | 区间 2 层且各 2 行：ba5cf54 单句内逐词（「组合根按引擎**算好**传入」→「**向 worker 查自报值后**传入」）、da5002a 口语「跑」；本区间无内容增长、无新增层、零残留 | 1（X6 被否） |
| 0027 | 动 | 24 层，挑读 6 个大改层；**ba2a351 是整段替换式重写**——materialize 的全部施工生平（三档语义表、`s3://` 未实装注、「默认不拷是刻意的」约 20 行）被压成一条「被拒方案」护栏 + 新增「href 相对化」节，旧层零残留；同层还删掉「（封版前收口）」这类自证句。故本篇沉积不在被覆盖层，而在建档期写下、此后无人再审的两处 | 1（P12） |
| 0028 | 动 | 30 层（最长）；区间 2 层。**层叠治理已做过两轮**：e08c571 把「留口子」里那条 20 行的 step 短路 defer 整条删除、改写成上方一条「已实现」条（旧 defer 层零残留），a97f912 又清掉改写时留下的「曾是本 ADR 记的空白」。当前残余只剩一次性 run 标签 | 1（P19） |
| 0029 | 动 | 22 层，挑读 6 个大改层；**eafa48e 第一期上传落地时「留口子 / 待真做时定」三条没删**、改成 `~~删除线~~ +（第一期已定，见上）`，此后历轮（40fe732 / a97f912 / dfd867e）都只动别处 → 该施工记账外壳保留至今；同一「第一期 / 已实现」框定在 :69/:73/:76/:78 叠了四层 | 4（P20、P21、P22 通过 / X7 被否） |
| 0030 | 动 | 25 层，挑读 7 个大改层；**2ed986f 是就地改写层**——把「severity 增量聚合」这个当时的错误现状描述在决定二/三/四逐处换成「按 scope_id 增量刷 job 态」，diff 里每处都是 `-` 后紧跟 `+`、无并列残留（本轮 #57 的成因正是 0031 侧那条反向指针没跟）；决定六/七是各自成节的追加层；唯一叠加式增长在末尾「现在做 / 留口子」节 | 2（P13 通过 / X8 被否） |
| 0031 | 动 | 17 层，挑读 6 层；**015585e 把原「## touch points（实装清单）」整节替换成落点指针表**、并把着色意图的 why 上移到决定二新增的「视觉映射」条 = 上一轮已做过一次结构性提纯（两条不变量原地保住）；e08c571 是整节追加（决定六 + 表 + 判据），与既有节零重叠 | 1（P14） |
| 0032 | 动 | 31 层，挑读 8 层；daf0c07 Draft→Accepted 并新增「真容器校准结论」整节；**284ea49 把 daf0c07 当时写的「进程收尾固定尾巴 ~12s」整段替换为「ECS 记录延迟…跨 4 样本恒定 11.06~11.54s → 坐实为平台侧记录滞后」**（旧归因零残留）；955dc19 同时清掉 daf0c07 留下的 WP-S/WP3-B 坐标（现文 `grep WP-` 为空） | 2（P23、P24） |
| 0033 | 动 | 39 层，区间 7 层；239e5a8 全是**原地整词替换**（基底→基础镜像、在跑 run→运行中 run），a9285d3 在「events 表开 TTL」条尾**原地扩写**三条护栏 + 资源清单 13. 两条 mapping filter = 枚举补齐而非叠加；上轮 P13 已落地（现 :182 与批准改法逐字一致、无残留括注） | 1（P25） |
| 0034 | 动 | 45 层，区间 4 层；a9285d3 最大（流程 ④ 就地扩写出「宿主侧取这个数本身也在失败隔离内」的理由链 + 新增「不变量：已收尾的 run 不再推演」整段，旧描述层被整句替换、无并列残留）；239e5a8 纯新增一段「`project` 的全量重放反转了 [0031] 决定三的一处立场」，方向合规（新 ADR 作权威、0031 侧只留一句反向链）；上轮 P14 已落地 | 2（P26、P27） |
| 0035 | 动 | 10 层，区间 2 层；a9285d3（3+/2-）决策 3 的「表外还有一处就地拆」**整条替换**旧的一句版 + 新增「被接受的代价：「已落库但未交棒」这一格」子条 + 决策 4 末补 owned-env 不变量指针 = 纯加不变量/代价/指针，旧内容原样保留；90a9b41 全角→ASCII、语义零变化 | 1（P6） |
| 0036 | 动 | 11 层，区间 5 层；**4fc87a4 把独立 flag `--list-deterministic` 并入能力自述对象**——「2.」的标题与首段整段重写（旧标题与「dump 成 JSON 数组」的旧世界文字已被替换、无残留），「5.」从行内散文改成 json 块 + 三个 bullet，并新增被拒方案末条；ba5cf54 改编号消重号并补消费侧规则；c925d1d 只给 json 块与 bullet 各加 `model_id` | 1（X1 被否） |
| 0037 | 动 | 42 层，区间 13 层（按 --stat 挑大改层读差异）：239e5a8 56 行词表统一、90a9b41 12 行全角归一、a9285d3 8 行就地扩写 owned env 不变量与「两层声明只贴 deploy」、34cc3af 6 行「锁步」→「`==` 同版本 pin」、0f48189 6 行路径、4fc87a4+03fb3f8 把「三个自述入口」整句替换为「两个非 job 入口」。全部层为整句原地替换或句内追加，被替换的旧句无一残留（现文只剩「两个非 job 入口」这一层） | 3（P28、P29、P30） |
| 0038 | 动 | 区间 5 层；239e5a8 78 行词表统一（逐条 `git show` 确认全为原地替换：基底→基础镜像、在跑 run→运行中 run、版本单旋钮→版本真源）、03f9d8c developer→测试开发、da5002a 去口语动词。五层无一新增描述层、无「后层覆盖前层却留旧层」的痕迹（全篇仅 :17 AWS 事实句里的「在跑的 task」是同词口语形） | 1（X9 被否） |
| 0039 | 动 | 区间 5 层且各 2-7 行：a9285d3 面一三处就地扩写（禁词真值集 = 护栏正则、上传失败不承诺「收尾会再传」、review 抓到的行话入表）；0f48189 Status 头改 Partially-superseded + 表内「根 `DEVELOPMENT.md`」**整行替换**为「根 `CONTRIBUTING.md`」（未留旧行）；c3d3727 句尾追加「跨宿主的内部抽象词同属内部机制名（典型 = 推进器）」。全为原地替换或句内追加、无残留旧描述层；上轮两条提案已随 dfd867e 落地 | 判无（0 提案）：:22「产物上传失败的日志不承诺「收尾会再传」」= 文案不变量 + why（三条提前退出路径只做有界排空、不跑整目录 flush）+ 反模式（曾有收尾日志承诺「scope 末 flush 兜底」而那条路径根本不跑 flush）；:47「护栏管不到的」= 为何仍需人 review 的内联证据（runtime 页面整篇行话、`--grace` 漏标「仅 run」、定位链顺序写反三个实例）+「能正则化就入表」的处置规则；:24「实装时顺带的原则性修正：Nova worker 的信号 handler **曾**在 handler 内 `log()`…」= 带「曾」框定的历史 + 交去 0024 终止契约的精确指针；:15-16 背景计数（五个 Python 包 51 处 / midscene `.mts` 5 处 / 各包 README 11-26 处）= 问题规模的判据型数字，支撑「内部指代确实漏到使用者面」这一前提 |
| 0040 | 动 | 区间 3 层；239e5a8（+17/-17）术语名整行替换，并把决策 3 的「从低到高是一条梯子」改成「四档不构成逐档累加的阶梯」、两条推论里「detached 比同步权限更小」改成「detached 不需要任何 ECS 写权限」；838e4af 追加决策 6 整节；0f48189 被拒方案路径。三层全是整句原地替换或整节追加，`git show` 逐层比对未见「旧描述层 + 新描述层」并存（梯子叙述被彻底替换、无「逐档累加」残留句） | 1（P31） |
| 0041 | 动 | 区间 6 层：c3d3727 纯追加「契约面只覆盖机读输出形状与退出码语义」边界、239e5a8 背景首句角色名、0f48189 两处路径、03fb3f8 把 doctor 的自述入口 `--list-deterministic` 换成 `--capabilities` 并注明清单取 `deterministic_steps`、90a9b41 字符、a9285d3 校准。全部为单行原地替换或纯追加，无一层在旧句旁另起新层；决策一那段最长散文自 eb057cf 定型后未被再改 | 1（P32） |
| 0042 | 动 | 27 层，挑大改层读差异：214db19 Draft 建档 +216；1d10101 + 14f5989 真跑回修 / 对抗审查 18 条；bfc6ed1 + 89cfc8b 把决策一「上传时机」段与闸门条**整段替换**为后台队列形态（无旧层残留）；860722c 新增「已知缺口与重议闸门」节；**c7e7c1d→eb7ab9a→ec0187c→a58cd40→2cf0237 五层把真跑结论逐次内联进验证节 = 典型叠加式增长**（eb7ab9a 那层加的「验证暴露并已吸收的两处」正是把前层句尾的吸收说明再总结一遍，`git log -S` 唯一命中它）。上轮已删该节 Draft 期「待做真跑清单」四条，但这两处同源残留没一起清 | 3（P15、P16 通过 / X10 被否） |
| 0043 | 动 | 区间 15 层（全部 ≤8 行）：dfd867e 落地上轮两条提案（:159/:169 末句「留待下轮」删除、:179 末句按附加约束改写并带 evals.json 的 notes 指针）；5c420d3 追加「同步手段与护栏分工（2026-09-18 补）」hook 条；e11f24f→fb27bd1→d543087→bba18eb 四层逐次追加 v1.4.2 / v1.4.3 云端真跑结论。验证节是**逐轮追加式增长（只加不删）**，但每轮结论按日期与版本框定、无被后层覆盖却留着的旧层 | 2（P33、P34） |
| 0044 | 动 | 7 层（最新 ADR，2026-09-17 起）；8c745ca 新建 +34（四条决策 + 被拒/留口子）；**3860d2c +19 把 A/B 六模型表、成本实测、地理型 vs global 取舍内联进「现值」——这一层本身就是「把证据内联进 Accepted ADR 使其自包含」的动作**；d829dd8 补「推断表两条改不锚首 + 显式 family 不校验的理由」；2f6fdf8 改决策 2「云端只改镜像 ENV、部署侧不动」。全部为新增或整句替换、无被覆盖却留下的旧描述层 | 判无（0 提案）：最险候选 = 「现值」下的六模型 A/B 表与其后三条 bullet（终态 / 三遍不一致数 / 耗时中位与 p90 / token / 中文探针；成本 $0.023 vs $0.054 约 2.3 倍、cache 命中 30%–54%、global 便宜 9% 但慢 20%）**全是判据型数字**（删了「为何默认取 Terra 与地理型 profile」就悬空），属 CLAUDE.md「值得让 ADR 长一点」的自包含证据；坐标型现场（run_id / 逐条命令 / 单次耗时）本就没有，唯一带过程色彩的「本轮」二字按措辞改而非删（见 #100）；次险 = 决策 2 family 推断表七行右列注释（`*` 前导不锚首的解释），是 d829dd8 刻意补的 why、且与 `agentcore-sigv4.mts` 的 code 注释成对 |
| 0045 | 动 | 8 层（本篇在锚点之后建档）：0f48189 建档 +78（决策一至六 + 被拒 + 影响）；838e4af +20/-9 追加决策七整节，并把四处「建造者 AI / 使用者侧的 agent / AI coding agent」整行替换为新角色名；c3d3727 +9 追加决策八；da5002a 决策六写明「口吻由读者决定」并补 code 注释与终端字符串两面；d24b90d 决策七补作图方法单列与图源指纹护栏；d05be3b 决策一/被拒方案加工具手册；239e5a8 决策一标题与表格角色名；b1d6015 skill 改名。**以整节追加为主、替换彻底，未见旧描述层残留**；唯一机械残留是替换未补中英文空格（已作客观 #103） | 1（P35） |
| **CONTEXT.md** | 动 | 59 层；唯一大改层 **924af6f（2026-09-19，372 行，重写为严格词表 74 条六节）**，其余全是 2-25 行增量层。`git show 924af6f^:CONTEXT.md` 对读得到史实：词表一年间靠逐条叠加长成散文式长词条（旧 `_Avoid_` 写整句反模式、词条正文嵌 code 符号、含落盘形状与版本里程碑），此次被整体替换 → 「被后续迭代覆盖却没删的旧描述层」在当前文基本清零；本轮候选全落在**新写层自身**的两种形态：why / trade-off 外溢进定义、从 ADR 压缩进词表的机制枚举。反向教训也在这层：worker 定位链把 ADR 的四级清单压进一句话时**当场压错**（本轮 #110），是「同一机制写两份必漂一份」的现成证据 | 8（P36-P43，全部通过） |

**判无依据质量抽查（复核员意见）**：0007 / 0008 / 0009 / 0014 / 0018 / 0023 / 0025 / 0039 / 0044 九篇均逐句点名 + 定位 + 引原句片段，抽查的 code 真值全部对上（如 0025 的 `quote(scope_id, safe="")` 在 `result_store/local.py`:43/:48、0018 的圈码在 `features/wikipedia_robustness.feature`:1/:3/:4/:12、0044 的 family 推断表与 `MODEL_FAMILY_PATTERNS` 同序同义），**不可移植**。**唯一点名不合格风险：0012**——已是第三代沿用，链条底部（基线 ec12b4b）只有一句裸清单、无内容级近似候选，依据事实上退化成「引用链 + 一字未动」。

---

## 六、事实族横切记录（9 族）

| 族 | 权威位置 | 提及处 | 结论 | CONTEXT 指针 |
|---|---|---|---|---|
| 退出码语义 | 无单一文档权威、按命令切片：code = 各 `_cmd_*` 的 return + `_render_status` + `skill_install.py` + `deploy_aws/cli.py`/`workers.py` 两个模块头；决策散在 0031 决定五 / 0034 / 0041 决策四 / 0042 决策四 / 0036 / 0037 决策 7 / 0030 决定七；文档两个合成 owner = user-guide/running-and-results「退出码」表（部署方指 cloud-backend）+ internals/verdict-model §5 | 约 70（12 份 .md + 4 图源标签 + evals 断言） | **一致**（除 3 条）：使用者表与 internals 全景表逐行对齐且与 code 对得上（run / status / submit / plan / explain / doctor / list-* / skill install 全覆盖）。不一致 = #116（cloud-backend 的 `1` 单一解释）、#153（skill 副本同源同错）、#148（节名）。图源四处只有标签、无字面码 → 零漂移面 | 有词条「机读输出契约」且带 ADR 0041 指针 → 不报 |
| 状态枚举与终态 | code `core/gherkai_core/model.py`（Status 七态 / `_STATUS_SEVERITY` / `_NON_VERDICT` / `_PRE_TERMINAL` / `TERMINAL_STATUSES` 取补）+ `project._aggregate` + `report_store/local._STATUS_COLOR`；决策 0031（决定一/一·补/二/三/五/六）+ 0024「`status` 三态」；人读 owner = internals/verdict-model | 约 60 | **一致**（除 5 条）：七态集合、severity 数值序（-1/0/1/2/3）、两集合定义、wire 三态、skipped/aborted 只出在同步 run 的 fail-fast 路径、run 级 ∈ {passed,failed,error}、六色映射逐项对上。不一致 = #57（0031:10 指向不存在的 severity 聚合）、#147（verdict-model:120 漏 reconciler）、#35（0016:39 Scenario 行漏 error）、#151（SKILL.md 漏 skipped）、#138（evals 断言写成 error/aborted） | 有词条「判定状态与 severity 数值序」+ ADR 0031 指针 → 不报 |
| 事件类型与字段 | code `wire.py`（7 类 `type` 分派 + `job_to_json` 键集）+ `model.py`（7 个事件 dataclass / ErrorType 六值 / Votes / Cost / ReportRef）+ 两引擎 emit 端；决策 0024 输入·输出 jsonc + 「字段语义」节；分支权威 0031 决定四/六、0027、0014、0028、0034 机制一 | 约 55 | **一致**（除 3 条）：事件 7 类（唯二成列清单 0026:76 与 core/DEVELOPMENT:23 都完整）、wire camelCase 键集、cost 子对象 snake_case、errorType 六值、reportRefs 四 kind 与两引擎产出点逐一对上；`task_exited` 全部 20 余处提及都正确区分「平台侧记录、非协议事件」。不一致 = #141（architecture-overview:42 把退出信号说成 worker 上报）、#35（0016:39 报告引用归属）、#45（0025 的 timeoutS 等式） | 有 4 条概念词条（事件流 / 错误归因 / step 短路 / 成本可观测）全带 ADR 指针 → 不报 |
| CLI 子命令与 flag | code `_build_parser()` + `deploy.py::add_parsers` + provider `add_arguments`/`_add_worker_subverbs`；决策 0041 决策一/三/四、0037 决策 6、0038 命令族、0043 决策三、0042 决策四、0034/0035 两隐藏入口；使用者 owner = running-and-results / configuration / cloud-backend | 约 90（含 skill 5 份、图源 4 处） | **一致**（除 4 条）：三轮差集全做（文档 flag ∖ code = 117 命中全是外部工具/worker 入口/明标被拒或未做方案，零幽灵 flag；code ∖ 使用者面 = 只剩两个内部入口与 cdk 的 `--app`；子命令↔flag 成对比对 336 份 .md + 19 图源、真问题零命中）。不一致 = #128（SUPPRESS）、#36（0016:125 三→五）、#129（单项覆盖面）、S1（configuration 跨命令表缺项）。skill 面有走真 parser 的机械护栏（129 passed） | 无词条（词表只收概念、全文零子命令/flag）→ 按决策八不报、也不建议加 |
| 目录树与模块清单 | 两级由 CONTRIBUTING 自定：① 仓库/包级树 = CONTRIBUTING:32-63；② **文件级只在各包 DEVELOPMENT.md**（:66 明写「两处并存必然漂移」）；最终真值 = `git ls-files` / `ls` / 根 pyproject members | 约 45 | **一致**（除 8 条）：六份 DEVELOPMENT 的文件级清单全部通过差集（core 30 个文件零漏零多）、三个 `docs/*/README.md` 索引两向一致、tools 表 6 项、SKILL.md references 4 份、features 7 个、ADR 编号 0001-0045 连续无缺。漂移集中在两类被枚举遗忘的位置：**新加进 `.github/` 与 `.claude/` 的项目级资产**（#121/#122/#132/#133/#161）与 **ADR 里那份「顺手也写到文件级」的副本**（#39/#96/S32）。另 #123/#124/#125 是 CONTRIBUTING 括注漏项 | 无词条 → 不报 |
| 版本·模型 ID·依赖锁 | code 常量（`constants.py::MODEL_ID` / `agentcore-sigv4.mts::DEFAULT_MODEL` + `MODEL_FAMILY_PATTERNS`）+ 六个 pyproject + package.json；决策 0044 决策 1/2/3 + 「现值」、0042 决策六、0037 决策 2b/2c/2d/3；internals:27 明写「真源在代码常量、不在文档」 | 约 70（13 份 .md 带模型 id） | **一致**（除 6 条）：依赖 pin 全族一致（nova-act==3.4.187.0 / @midscene/web 1.12.8 / playwright 1.63.0 / openai ^6.3.0 / gherkin-official>=31.0.0）；Node·Python 下限 14 处一致；家族推断表三份（code / 0044:18 / configuration）行序逐行相同；CI 工具链 env 与真值一致。不一致 = #13/#16（换默认后 IaC 口径未回填）、#131（gherkin-official>=42）、#117（README 并集写成无条件）、#83（模板钉 1.4.0）、S40（0005 TS 条）；另 f536b5a 升 SDK 引出 5 条源码内点失效（#25/#27/#28/#167/#169/#173/#174） | 有 5 条词条（引擎模型 / 模型家族 / 默认模型锁定 / 模型评测集 / 版本真源）全带 ADR 指针、零字面量 → 不报 |
| 命名契约 | code `runtime/gherkai_runtime/names.py`（零依赖纯字符串推导，`ecr_repo_name ≡ task_def_name`）+ `deploy_aws/names.py`（`stack_name` + re-export，真同源无复刻）；唯一 IaC 消费点 `stack.py`；决策 0033「资源清单」+「两层命名」+「container 名约定」、0038「概念模型」+「SSM 参数与命名真源」、0037 决策 6、0029 | 约 60 | **一致**（除 6 条）：实测真值集（python 直调 names.py）与文档逐项对上——两表名 / 桶 / cluster / 三 Lambda / task-def family / container / ECR repo / 日志组 / `{prefix}ecs-stopped` / `{prefix}timeout-scheduler` / `{prefix}job-timeout-<sha1>` / status-index / `BackendStack-<prefix 去尾横线>` / SSM 7 族 / 镜像 tag / 产物子目录；反向差集也无缺（stack.py 三处裸字面量都有登记）。不一致 = #130（--prefix 必给）、#64/#65/#66（0033:28/:29 复刻期表述与 ECR 未给名）、#73/#74（container 契约与 FargateEngine 归属）、#83 | 有 2 条词条（部署前缀 / 基础镜像·variant·默认指针）带 ADR 指针 → 不报 |
| 角色术语 | ADR 0040（决策 1 正名表 / 决策 4 边界矩阵 / 决策 5 单一真源 / 决策 6 两侧 AI agent）；权限主体登记 0033「资源清单」末段 + 0038「权限面增量」；派生视图三处（CONTEXT「角色与权限」节 / getting-started 角色表 / skill cloud-backend 角色表） | 约 180 | **一致**（除 8 条）：用户文档、skill 5 份、六份 DEVELOPMENT、internals 7 篇、4 张图源、Release footer、CHANGELOG 未发布段与 code 文案一律用正名；退役名（提交方 / 建造者 AI / AI coding agent / 技能包 / test engineer）正文零命中。不一致 = 术语批 #7/#7b（维护者 12 处、开发者 3 处）、#89/#90/#91/#92（0040 派生视图指针）、#95（0043 把维护者列进使用方侧）；三份角色表逐格比对未漂、但它们的同步只靠 0040 代价节那个审计点，而**该审计点的落点写错了**（#89） | 有 10 条词条全带 ADR 0040 指针、四组退役名登记齐全（与护栏 `RETIRED_TERMS_WORDS` 单向差集成立）→ 不报；唯一缺口 = 「使用者」未登记（D10） |
| 数字类（超时/宽限/并发/保留期/票数/TTL） | 各子项分立真源：`--default-job-timeout` 300（argparse ×3）/ `NOVA_ACT_TIMEOUT_S` 120（compose 单一真值）/ margin 30 → Nova 下限 150 / `minGraceSeconds()` = 31 / `ScheduleOpts`（4·5.0·0.0·0·0.5）/ CLI 并发与票数 1 / `DEPLOY_SIDE_MAX_CONCURRENCY` 8 / stopTimeout 120 与硬顶 120 / events TTL 与 S3 lifecycle 7 天 / `RETIRE_QUIET_PERIOD` 1h / 隧道 900·3600 / 推进器 2min·256MB / FargateEngine 0.5s·5s·20拍·5拍 / pytest --timeout=60 | 约 120 | **一致**（除 1 条）：逐子项差集全中（含 31 s 的六段预算加总、150 = 120+30、20 拍 ≈ 10 s）。不一致 = #62（0032:56 的 ~1.5x vs code ~2x）+ 同行 #63。**最干净的一层是 internals 与图源**：对本族零字面量、一律指针（「默认值见 `--help`」「cap 常量 = `BackendStack.DEPLOY_SIDE_MAX_CONCURRENCY`」）——建议后续新增派生视图照此办。残余风险：部署侧 cap `8` 在 4 处使用者面是逐字副本（当前未漂），改常量时须同批改 | 有 4 条词条（停止宽限期 / job 墙钟预算 / 票·投票 / 判定抖动）全带 ADR 指针、零数字 → 不报；并发上限·保留期·TTL 三项无词条 → 按决策八不报 |

---

## 七、Status 头与反向链

### 7.1 需改 Status 头（10 篇；枚举变更 3 篇见 D2-D4）

| ADR | 改什么 |
|---|---|
| 0002 | 枚举保持 `Superseded-by 0044`；注解末句「…**正是** A/B 中文 UI 探针**要验的**」→「…已由 0044 的 A/B 中文 UI 探针复核（3/3）」（= 客观 #15） |
| **0012** | **Accepted → Partially-superseded-by 0044**（D2；注解写清「结论存：不设独立 planner 槽、由引擎模型兼任 + 两集合不相交的理由；立场变：兼任者不再是 Qwen3-VL、现值由 0044 定；「何时重议」第一条已于 2026-09 满足并重新评估、结论仍是不拆」） |
| 0019 | 枚举保持 `Partially-superseded-by 0022`；注解首句补 `@timeout:`（「`@scope:`/`@engine:`/`@timeout:` 三个 tag 的**语义不变**…`@timeout:` 随 [0034] 加入本体系」） |
| 0027 | 枚举保持 `Partially-superseded-by 0042`；注解末「（正文两处已就地改写并反向链。）」当前**不成立**（:65 未改写）→ 第一层落 #47 后即成立；若改法上选保留原句，则注解须改「正文三处」并点明第三处 |
| 0033 | 枚举保持 `Partially-superseded-by 0037/0038`；头末补一句 0044 反向链（IAM 表 `bedrock:InvokeModel` 的资源 pin 一条由 0044 放宽，正文两处已就地改写）——只读头的 agent 现在看不出 IAM 一条被放宽 |
| 0035 | 枚举保持；头内「四种「跑法 × backend」组合」→「四种「执行方式 × 执行后端」组合」（术语批 #1） |
| **0037** | **Accepted → Partially-superseded-by 0045（范围 = 决策 8 ④）**（D3；原 Accepted 注解全文保留） |
| 0039 | 枚举保持 `Partially-superseded-by 0045`；注解补两项、改一处：① 面二的读者二分已被 0045 决策一的读者三分类取代（0040:12 逐字写着这句、0039 头没有）；② changelog / Release 正文载体与各包 `Changelog` URL 随 0045 决策五改；③「两条护栏不变」→「两条护栏仍在，扫描面已随 0045 决策五/六/八扩（Release footer 模板、口头语表、退役旧名表）」 |
| 0040 | 枚举保持 Accepted；头内派生视图指针改（= 客观 #89） |
| 0042 | 枚举保持 Accepted；建议按本仓惯例（0030:3 / 0036:3 / 0041:3 同款）追一句后续修订注：决策四的 `--step` 展开口径在发版验证后改为「显式 `--step` 即展开」（正文 :103 已记、头里「六项决策已实装」看不出被动过） |

### 7.2 反向链缺口（10 条）

| # | 加在哪 | 加什么 | 证据 |
|---|---|---|---|
| L1 | 0044「边界与互链」节末 | `- [0003]：被本 ADR 取代的前一代 Midscene 模型选型（其 Status 头已标 Superseded-by 本 ADR）；Bedrock `/openai/v1` 接线契约与被排除替代集仍有效。` | 0003:3 单向指 0044，而 `grep -c 0003 docs/adr/0044-*.md` = **0** |
| L2 | 0044 同节 | `- [0012]：planning 不设独立模型槽、由本 ADR 的默认模型兼任（其 Status 头已改 Partially-superseded-by 本 ADR）。` | `grep -c 0012 docs/adr/0044-*.md` = 0；`run-scope.mts` 的 `modelConfig()` 只有 default 槽 |
| L3 | 0045「对既有文档与 code 的影响」节 | 一行登记它对 0037 决策 8 ④ 的反转（changelog 锚点移到根 CHANGELOG + 新增 gate） | `grep -n 0037 docs/adr/0045-*.md` 零命中（该节现只登记 0039） |
| L4 | 0037:3 + :176 | Status 头按 D3 改；:176 ④ 就地加历史注 + 指 0045（= 客观 #80） | `grep -n 0045 docs/adr/0037-*.md` 零命中 |
| L5 | 0033:3 | 头末补 0044 反向链（见 7.1） | 0033:149/:155 已带 0044 链、头无 |
| L6 | 0010:39（洞察③ 末） | 补边界注：`（对称有边界：命题措辞含歧义时两引擎判定可能分叉，见 [0018]「两个引擎对称（精确化）」条的负向验证）` | 0018:25 自陈是 0010 对称论断的扩展 + 边界修正并给出判定分叉实测，0010 全文零处提 0018 → 单读 0010 会得到**无条件**对称的结论 |
| L7 | 0009:12 该条后 | 补「引擎默认模型的候选集同受本约束界定（[0044] 决策 3：只用 Bedrock OpenAI 兼容端点调得到的模型）」 | `grep -n 0044 docs/adr/0009-*.md` 零命中，而 0044 的候选集筛选完全建立在本约束上 |
| L8 | 0042:187（「已知缺口与重议闸门」节） | 补一条「云端 job 判 error(timeout) 时 explain 文本不打 scope 级判定行（原因只在 `--json` 里）：决策四的可读性缺口，v1.4.3 发版验证观察到。」 | 0043:186① 单向记着并指 0042 决策四，0042 全文零处提 0043。**属跨 ADR 搬内容 → 见 D18** |
| L9 | 0036（范围段或「5.」）·可选 | 一句回指 0025（交割「派发标注那半」使其双向） | 0025:5 显式把该半交割给 0036，而 `grep -c 0025 docs/adr/0036-*.md` = 0 |
| L10 | 0011「决定」二 / 「何时重议」·可选 | 一句边界注（内网里「运行命令那台机器可达」那一档已由 0035 隧道兑现） | 0011:17 引的只是 0035 的 VPC 调研结论（= 客观 #24 的同一处，落 #24 即解） |

### 7.3 连带审计（Accepted / 冻结必自包含）

- `grep -rniI journey docs/adr/*.md CONTEXT.md` → 仅 3 处命中，**全部合法**：0045:21 / :34 把 `docs/journey/` 作为读者类别的归属目录（在定义位置，非指向过程文件）、0039:64「**中文文件名**（journey 曾用）」是反模式的历史举例（无指针、无文件名）。
- `grep -rnE 'WP-[A-Z0-9]|WP[0-9]' docs/adr/*.md CONTEXT.md` → **零命中**（上轮 0032 的 WP-S/WP3-B 已由 955dc19 清掉）。
- 本轮建议翻 Partial 的 0012 / 0037 同样零 journey 引用、零 WP 编号；既有 Accepted 枢纽（0022/0034/0042/0043/0045）复核仍干净。**此项无到期未还的债。**
- `docs/journey/` 目录在本轮开始前**不存在** → 任何指向具体 journey 文件的链接都会是死链，现状零此类链接、方向违规边为空。

### 7.4 枢纽 churn（8 个枢纽，无拆分信号）

| ADR | commit 数 / 行数 | 判定 |
|---|---|---|
| 0016 | 67 / 267 | 分段 churn 核过：「工程布局」段 25 次 vs「数据模型」段 19 次，差额几乎全是全仓横扫（词表传播 c3d3727/239e5a8、口语清理 da5002a、锁步改写 34cc3af、全角归一 90a9b41、各轮 doc-health），两次实质改动都是**被 doc-health 差集查出来的漏项**、非独立演进 → 高内聚总纲，按红线不拆 |
| 0024 | 58 / 263 | 同上，无段级压力 |
| 0034 | 45 / 276 | 同上 |
| 0037 | 42 / 260 | 同上 |
| 0033 | 39 / 188 | 分段核过：「IAM 最小权限」段仅 9 次，**反而低于**「资源清单」19 次与「命名/preflight」19 次 → 最像「被无关 ADR 反复写入」的那段反而最冷。**值得盯**：其「资源清单」末段是编排机器权限的单一登记处（0033 自己写明「别在此重复」），0038 权限增量 / 0040 权限梯级 / 0044 IAM 放宽三个互不相关主题都往这一段写；若再有两三个主题加入，就该按主题独立成篇（权限与身份） |
| 0042 / 0026 / 0022 | 27 / 22 / 19 | 无信号 |

**结构性观察**：本轮唯一的结构漏洞模式出在两个最新的枢纽候选上——**新 ADR 只登记「我影响了谁」，漏登「我取代了谁」**（0044 对 0003/0012 零引用、0045 对 0037 零登记，而两者 Status 头都自陈「反向链已逐处落地」）。0044 补 L1/L2 后将成「引擎模型」主题新枢纽，0045 同理成「文档分层」枢纽；两者体量尚小、无过载迹象。

---

## 八、方法复盘草稿（下一轮开局作第一份待批）

**抓到真问题的规则（点名 + 实例）**
1. 【强制】枚举差集 —— 本轮最高产：`error-text.mts` 漏列（#39）、`TERMINAL_STATUSES` 漏 reconciler（#58/#147）、自述键漏 `model_id`（#145）、`--backend` 三→五（#36）、CONTRIBUTING 四处树/括注漏项（#121/#123/#124/#125）、ECR 未给名（#66）、评测资产漏 2 项（#96）、`timing.json` 漏 `memory_reads`（#140）。这些**在读已列内容时全部隐形**。
2. 【强制】STALE 必对照 code —— 抓到「文档比 code 注释还旧」的教科书形态 #37（0016:176「跳过一切云端检查」，而 `__main__.py` 的注释把校准后的真值写得很准）、以及「文档写了一个从未存在的机制」#57（0031 指 0030 的 severity 单调聚合，两篇互指成环、`git log -S` 证实 code 里从未有过）。
3. 第三层事实族横切 —— 抓到按文件分片必漏的：退出码 `1` 的错误映射在 skill 发行副本里同源同错（#153）、同一行（0016:39）被两个族各报一个不同问题、术语批的跨篇分布（只改一处就造新分叉）。
4. 红线复核 —— 否决 10 条，其中 3 条若照原提案执行会删掉受保护要素（X7 删决策理由、X10 删 Nova 中途路径的唯一证据、X5 删被拒方案护栏）；另 5 条 approve_reduced 挡回误伤（P1 丢引擎模型标注、P7 指针错向、P13 删定位 why、P14 删消歧句、P43 删 0018 的边界修正）。
5. 层读限读纪律（--stat 挑大改层 → 只读该层差异）—— 0016（67 层）/ 0028（30）/ 0042（27）全部未卡顿；且层读本身产出结论：0008 的「剩余风险」节经层读证实与闭合节**同批写入**，推翻了「它是沉积」的猜测（连续两轮阻止同一处误改）。

**零命中 / 全误报**
- journey 引用与裸 WP 编号：46 篇全量**零命中**（连续两轮）。它承担「Accepted 必自包含」的防误伤职责 → 不退场，建议降为第一层末尾一句提示（连带审计跑一次 grep 即可）。
- 引用图孤儿：零命中（多轮如此）。
- 图源字面量漂移：19 份图源零命中（只剩 S10/S35 两处措辞）→「图上只画结构、会漂的字面量留正文」已内化。
- 误报集中在**术语面**：7 条 REFUTED 里 3 条同源（R1 把 COLLOQUIAL 表当 RETIRED_TERMS 表、R7 把完整角色名的 `_Avoid_` 推及其前缀、R3 把「至多一个指针」读成「必须有指针」）。

**执行卡点**
- **取锚点命令本身有 bug**（#156/#157）：`| grep -m1 .` 恒返回 HEAD → 区间退化成「本轮自己那一两个提交」→ 全部 ADR 被判「未动、可沿用」，【强制】提纯审计整条静默失效。本轮靠 verifier 实跑才发现，这是方法自身的 high 级缺陷。
- CONTEXT `_Avoid_` 差集时 `sort -u` 在默认 locale 把 CJK 折叠（110 词塌成 37 词），第一遍漏掉一半退役词命中；BSD `tr` 也切不了多字节分隔符「、」。**假真值集比不做差集更危险——它看着做了。**
- 术语「术语名 vs 散文」的分流判据在 ADR 面反复出现边界争议（R1/R7/D5/D14），三个分片给出三种判断 → 规则不够。
- 0012 的沿用链已第三代，依据退化成「引用链 + 一字未动」（已点名）。

**提议的规则增删改**（下一轮批了才改方法文档）

| # | 增/改 | 内容 | 它防的失败形态 |
|---|---|---|---|
| R-1 | 改 | 第一层「选材」取锚点命令 → `git log --format='%h %(trailers:key=Doc-Health-Round,valueonly)' \| awk 'NF>1{print; exit}'`，并写明「`grep -m1 .` 会命中每一行、必返回 HEAD」；code-health 同步 | 命令静默成功但返回 HEAD → 区间退化 → 全篇判「可沿用」→ 【强制】提纯审计形式满足而实际零执行 |
| R-2 | 增 | 枚举差集条加一句：真值集构造命令**自身要自检条数**（`wc -l` 与 `grep -c` 对账）；CJK 词表差集必须 `LC_ALL=C`，别用 `tr` 切多字节分隔符 | 假真值集（词表塌成三分之一）→ 差集「跑了」却漏掉一半命中，且无任何报错 |
| R-3 | 增 | 第二层 cross-ADR 加机械检查：凡某 ADR 的 Status 头出现 `Superseded-by NNNN` / `Partially-superseded-by NNNN`，NNNN 那篇必须 grep 得到旧编号（两侧差集） | 新 ADR 收口时只写「我影响了谁」、漏登「我取代了谁」——本轮 0044→0003/0012、0045→0037 三处全犯，而两篇头都自陈「反向链已落」 |
| R-4 | 改 | TONE 术语面加分流判据：退役名落在 ADR 散文里时先查它在护栏属哪张表（COLLOQUIAL 只约束人读层 / RETIRED_TERMS 管用词版本）；`_Avoid_` 登记**完整**术语名时不推及其前缀或子串；同一退役名跨多篇时**必须一次做完**（附全量落点） | 本轮三类误报；以及「只改一处造成新的跨篇不一致」（0004 比 owner 0044 更规范、0035 单改一处而 0037/0043 同词留着） |
| R-5 | 改 | 跨轮沿用规则加退场条：同一篇**连续三轮沿用**即须补一条本篇自身的内容锚（点名受保护要素 + 定位），不许纯引用链 | 0012 式依据退化——链底只有一句裸清单，沿用规则养出「纯引用型判无」 |
| R-6 | 增 | 覆盖范围补 `docs/diagrams/*.json`（判据已由「图也是派生视图」条拥有），:75 的「本任务只管 `.md`」同步改 | 图源既非 markdown 也非 code 注释，两侧任务都不收 → 无人区（本轮 #160） |
| R-7 | 降 | journey / 裸 WP 编号检查连续两轮零命中 → 降为第一层末尾一句提示，不再单列步骤（保留其防误伤职责） | —（退场判据触发，但因承担「Accepted 必自包含」故只降不删） |
