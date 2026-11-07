# 0039. 用户可见面不带内部指代：产品文案与文档分层

> **Status:** Partially-superseded-by 0045 ——面二里「各包 README = 完整操作手册」被 [0045](./0045-documentation-layering-and-placement.md) 决策三反转为「入口页」（叙事归 `docs/user-guide/`）；面二的读者二分（使用者向 / contributor 向）亦被 0045 决策一的读者三分类取代；changelog 与 Release 正文的载体、各包 `[project.urls] Changelog` URL 随 0045 决策五改。面一（产品文案零内部指代）不变；两条护栏仍在，扫描面已随 0045 决策五 / 六 / 八扩（Release footer 模板、口头语表、退役旧名表）。原文：Accepted（2026-09-09）—— 两面均已实装并有护栏：产品文案面（`cli/tests/test_user_facing_messages.py`）、文档面（`cli/tests/test_package_readmes.py`；随包发行的 agent skill 那一层另由 `cli/tests/test_skill.py` 扫）。本 ADR 是 CLAUDE.md 代码纪律「产品面文案不带内部指代」与文档纪律「README / DEVELOPMENT 分层」两条约定的决策与理由所在；约定文件只留规则与指针。

## 背景与问题

项目的设计知识全部以 ADR 编号、决策号与一套内部机制名（不变量 / 定位链 / 被拒方案 / 重议闸门 / 实测项 / 接缝契约 / 组合根 / 皮…）组织，这对写代码与写 ADR 的人是高效的索引。但 v1.4.0 首发前后暴露出它漏到了**使用者能看到的面**上：

- **产品文案**：`--help`、提示、警告、错误、worker/Lambda 日志里带着「（定位链四级全 miss，ADR 0037 决策 3）」「（ADR 0037 决策 6 三态）」这类尾注。AST 扫描生产代码的非 docstring 字符串字面量，五个 Python 包命中 51 处、midscene 的 `.mts` 5 处。使用者手里没有仓库，这些既读不懂也查不到，还挤掉了「怎么办」的位置。
- **包页面**：六个发行包的 PyPI / npm 长描述就是各包目录的 `README.md`（pyproject `readme` / npm `files`），而它们一直按 contributor 文档写：ADR 提及 11-26 处不等、模块布局、运行测试、spike、从 checkout 运行，且满是 `../docs/adr/…` 相对链接——在 PyPI/npm 页面上全是死链。pyproject / package.json 的 `description`（页顶 Summary 一行）同样写着「组合根……（ADR 0016）」。根 `README.md`（仓库首页）亦以 ADR 编号组织叙事。

用户的判断（本 ADR 的起点，用户自己先改了一条 `compose.py` 文案）：**给用户看的东西不该带内部指代**。

## 决策

**一条原则、两个面**：凡使用者能看到的文字——终端输出/日志、仓库首页、发行包页面——只说**发生了什么、为什么（产品语言一句）、怎么办**；ADR 编号、决策号、内部机制名、内部函数名、「见模块头/接缝契约」这类指针**留给 contributor**，住在紧邻的代码注释、docstring、contributor 文档里。判据 = 「装了包 / 点开仓库首页、没读过 ADR 的人看得懂且用得上」。**跨宿主的内部抽象词同属这里说的内部机制名**（典型 = 「推进器」：角色词、没有一个符号覆盖全部宿主，定义见 CONTEXT.md 词条、机制见 [0034](./0034-detached-batch-reconciler.md)）——两个面一律改说使用者能指认的具体命令、组件或位置（后端 / 云端 / 进程）。

### 面一：产品文案（代码里的字符串）

- 范围：argparse help/description/epilog、`print`/stderr、CLI 的进度提示、provider 的输出、警告、展示给用户的异常文案（`WorkerVariantError` / `WorkerCommandError` / `WorkerNotFoundError` / 校验用户输入的 `ValueError`）、Lambda 日志行、worker stderr。
- 不写：`ADR NNNN`、`决策 N`/`决定 N`、内部机制名（示例：不变量 / 定位链 / 被拒方案 / 重议闸门 / 实测项 / 接缝契约 / 模块头 / 组合根装配 / 窄腰）、内部函数名、分层行话（皮 / provider 侧作代码层义）、施工与失败语义行话（示例：preflight / per-run / best-effort / 抢传）。**这里的枚举只是示例，真值集 = 护栏 `cli/tests/test_user_facing_messages.py` 的 `FORBIDDEN` 正则**（每条禁词对应的产品语言替代写在该正则的旁注里）——表随新犯的词按同一判据扩，不必每加一词回头改本 ADR。
- **不写 markdown 强调记号**（成对的 `**…**`）：终端与日志不渲染 markdown，人读输出的呈现层也不解析标记语法、不用加粗（[0047](./0047-cli-human-readable-tables-with-rich.md)），使用者看到的是原样的星号。需要强调时改用措辞：以「注意：」开头、单独成句或另起一行。这类星号曾在八处用户可见字符串里出现（argparse 的 help 与 description、stderr 上的提示与错误），靠人工复核逐处发现并不可靠，故由护栏机械判定（见下护栏节第一条）。反引号包住的命令、选项与路径不在此列：它在纯文本里同样标出「这段照原样输入」，不经渲染也读得懂。
- **产物上传失败的日志不承诺「收尾会再传」**（文案不变量，两引擎措辞一致）：只说「什么没能上传 + 不影响什么」。「稍后/收尾会重试」在提前退出的三条路径（停止信号 / 网络耗尽 / 异常）上是假的——那些路径只对上传队列做有界排空、不跑整目录 flush（机制见 [0029](./0029-engine-artifacts-to-s3.md)「上传必须套超时」与 [0042](./0042-step-evidence-and-explain.md) 决策一）。同类保证若只活在某一个引擎的上传器注释里，另一个引擎迟早写反——曾有收尾日志承诺「scope 末 flush 兜底」而它所在的那条路径根本不跑 flush，故判据落在本 ADR、两引擎文案长期一致。**唯一例外（两引擎一致）**：收尾排空超时的那句可以说「剩余的改由收尾统一上传」，但只许出现在调用点已声明**其后紧跟整目录 flush** 的那条路径上（scope 正常结束的那一处；Nova `_drain_evidence_uploads(flush_follows=True)`、Midscene `drainArtifactQueue(…, flushFollows=true)`，参数必传、新调用点必须显式声明）；停止信号 / 网络耗尽 / 异常三条提前退出路径仍只说「已放弃 + 不影响什么」。判据：在那条路径上承诺为真——排空超时置的放弃标志只约束队列线程，整目录 flush 不受它约束，且 evidence 落在 flush 根内；含糊成统一的「链接可能打不开」反倒在会 flush 的路径上是假的悲观警告，违「只说发生了什么」。
- 搬家规则：被删掉的指针若对 contributor 有价值，进紧邻注释或 docstring；docstring/注释**不在**本约束范围、鼓励保留 ADR 指针。
- 例外：只在内部 API 被误用时才触发的契约型异常（`ValueError`/`RuntimeError`，永不因用户输入触发）可留一句点名内部符号的短诊断，但同样不写 ADR/决策字样。
- Nova worker 的信号 handler 内不写日志，「收到信号」的文案改由安全点补打：该 handler 曾直接 `log()`，这不只是文案问题，还引发了 stderr `BufferedWriter` 重入崩溃（细节在 [0024](./0024-worker-core-protocol.md) 终止契约）。

### 面二：文档分层（README / DEVELOPMENT 成对）

按**读者**切文件而非按目录切：使用者向 = 根 `README.md` + 各包 `README.md`；contributor 向 = 根 `CONTRIBUTING.md` + 各包 `DEVELOPMENT.md`。使用者向只写「这是什么、装法、用法、配置、退出码/错误怎么办」，不写 ADR 编号/决策号/内部机制名/目录结构/开发环境/测试/spike/发布流程/设计叙事；这些全归 contributor 向并带 ADR 指针。各层只差**去向与链接形态**：

| 文件 | 去向 | 链接 |
|---|---|---|
| 根 `README.md` | 仓库首页（GitHub）：门面 + 30 秒上手（agent 路径优先），「文档」一节以表格指向 user guide 各页，并指 `docs/README.md` 地图（[0045](./0045-documentation-layering-and-placement.md) 决策四） | 相对链接可（GitHub 渲染） |
| 各包 `README.md`（`cli/` `core/` `runtime/` `deploy_aws/` `engines/novaact/` `engines/midscene/`） | **逐字上 PyPI / npm 页面**（pyproject `readme` / npm `files`）；改动随**下一个 tag** 才生效——PyPI 已发版本的长描述不可改 | **只用绝对 URL**（页面上相对链接全是死链；仓库内文件用 `https://github.com/zhiyanliu/gherkai/blob/HEAD/<path>`，`HEAD` 跟默认分支、不绑分支名）；末尾链 user guide 与 `CHANGELOG.md` 的绝对 URL（[0045](./0045-documentation-layering-and-placement.md) 决策三起：包页只留一句定位 / 装法 / 最小用法 / 这些链接，不再写「设计文档见 docs/adr」） |
| 根 `CONTRIBUTING.md` | contributor 入口：版本线叙事、目录结构、从 checkout 运行、测试、spike、发布与版本、各包 DEVELOPMENT 索引、纪律/术语/ADR 指针 | 相对链接 |
| 各包 `DEVELOPMENT.md` | 该包 contributor 文档：模块布局、从 checkout 运行、测试、contributor 踩坑（真踩过的坑一条不丢）；**不进发行包**（wheel 本就不含，sdist 按 hatch 白名单 `include` 只收源码目录与 README / LICENSE / pyproject） | 相对链接 |
| agent skill（`cli/gherkai_cli/skills/gherkai/**`：`SKILL.md` + `references/`） | 随 CLI wheel 发行、由 `gherkai skill install` 拷进使用方项目或用户级 agent 目录（[0043](./0043-agent-skill-for-driving-gherkai.md)）——**使用者面**，读者是 agent，安装态没有仓库上下文 | **只用绝对 URL**（相对链接在安装态必死）；跨文件指针写反引号裸路径（如 `references/engines.md`）；零 ADR / 决策号 / 内部机制名 |
| GitHub Release 正文（由 `.github/scripts/release_notes.py` 从 `CHANGELOG.md` 本版节 + `.github/release_body_footer.md` 渲染） | Releases 页面——**使用者面**，没有仓库上下文；各包 pyproject `[project.urls] Changelog` 改指根 `CHANGELOG.md`（[0045](./0045-documentation-layering-and-placement.md) 决策五反转了 [0037](./0037-distribution-and-packaging.md) 决策 8 ④ 的「Release 正文作 changelog 锚点」） | 只用绝对 URL（同包 README）：`CHANGELOG.md` 全文只写绝对 URL（仓库内文件用 `blob/HEAD/<path>`），渲染脚本不改写链接，护栏见 `cli/tests/test_user_docs.py`（被拒的链接改写方案见「被拒方案」）；footer 里指向仓库文档的链接钉 `blob/vX.Y.Z/`；升级/用法细节指 user guide，不写 ADR/决策号（首发正文曾漏一处「见 ADR 0037 决策 7」，已在 GitHub 上手工修正） |

页顶 Summary（pyproject / package.json 的 `description`）同属包页面，同一规则。搬家不是删：从使用者向文件移出的每条事实与踩坑，必须在对应 DEVELOPMENT.md 里找得到。

### 护栏

markdown 护栏共用的规则源 `cli/tests/_doc_rules.py` 另接入写完即查的 hook 与提交闸门，见 [0046](./0046-guardrail-layers-tests-hooks-and-lean-claude-md.md)；code 字面量的两条规则（禁词表与 markdown 强调记号）仍独立住在 `cli/tests/test_user_facing_messages.py`（见下第一条）。

- `cli/tests/test_user_facing_messages.py`：AST 扫五个生产包全部**非 docstring** 字符串字面量 + midscene `.mts` 去注释后按行扫；`features/steps/` 的确定性 step 模板两种语言都扫（Python 字面量与 `.mts` 去注释后的行）：用户文档让使用方把模板复制进自己的项目，其中的字面量随之成为使用方看到的文字。禁词表含 ADR 编号 / 决策·决定编号 / 内部机制名 / 内部函数名与 construct 名 / 施工与失败语义行话，另收口头语、量词「档」与退役旧名（[0045](./0045-documentation-layering-and-placement.md) 决策六 / 八；真值集是该文件的 `FORBIDDEN`，见面一）；Python 与 TS 同一张表（曾因 TS 表更松漏掉一处「组合根装配错误」）。**这张表只管 code 字面量**，与使用者向 markdown 那张（`cli/tests/_doc_rules.py`，见下三条）**不同源**：code 面扩了词不会自动传导到包页面 / skill，同一个词可能在 code 里被拦、在使用者向 markdown 里仍在（如 `preflight`）——扩表时两侧都要过一遍。
  - **markdown 强调记号**（面一）在同一批文件上判定，判定单位是单个字符串字面量：只对字面量的内容匹配，字面量之外的代码不进判定面。形态：两组 `**` 之间夹着一段不含星号、不跨行、首尾都不是空白或 `/` 的文字。排除项各有来由：脱敏掩码（代码里的 `***`、`***@`，以及 `****` 这类纯星号串）只有一串连续的星号，没有夹在两组星号之间的文字，故只由星号组成的字面量不论多长都不命中；首尾的空白排除与 markdown 自身的规则一致（`**` 后面紧跟空白时不开启强调、前面紧挨空白时不结束强调），字面量里写出的 `2 ** n` 这类表达式因此不命中；glob 与 XCUITest 类链查询里的 `**/` 路径段紧挨 `/`。
  - `.mts` 侧逐个字面量判定，取代原规则「去注释后按整行判定」（原规则列入被拒方案）：对整份源码做一遍词法扫描，按出现顺序识别字符串字面量（单引号、双引号、模板字符串）、注释与正则字面量，再对每个字面量单独匹配。整行判定会把相邻两个字面量之间的代码当成强调正文：`const masks = ["***", "***"];` 里两个合法掩码之间的 `", "` 恰好满足形态，被判为强调。字面量与注释必须在同一遍里识别，不能先去注释、再抽字面量：字面量与正则字面量里的 `//`、`/*`、`*/` 是内容、不是注释，注释里的引号也不开启字面量；先按 `//` 与 `/* */` 删注释，会把 `"https://x"` 之后同一行的内容整段删掉、漏判其后的 `"**注意**"`，也会把 XCUITest 类链查询 `` `**/${A}/**/${B}` `` 里的 `/**/` 当成块注释删掉。模板字符串按整个字面量判定，`${…}` 处代入与 Python 侧相同的普通文字字符，其中的表达式不进判定面（嵌套在里面的字面量照样单独判定）；代码里的幂运算符同样在判定面之外，不留空格的 `a**b**c` 也不会误命中。正则字面量与除号按前一个记号区分：前一个记号是标识符（`return`、`typeof`、`case` 这类其后接表达式的关键字除外）、数字、字面量、`)` 或 `]` 时视作除号，其余情形视作正则字面量的开头；关键字若按标识符处理，`return /"/.test(s)` 这类写法里的正则会被当成除号，其中的引号随之开启一个并不存在的字面量。这是词法上的启发式，不解析 TypeScript 语法。
  - Python 侧的字面量取自 AST，f-string 按整串判定：`f"**{name}**"` 这种两组星号分在插值两侧的写法，逐个常量段判定时会漏掉。插值处代入一个普通文字字符（如 `x`），代入空串会让它变成纯星号串、被当作掩码放过。这一代入是启发式：插值的运行时值无法静态确定，`f"**{chr(42)}**"` 实际只有五颗星，代入后成为 `**x**`、被误判为强调。同一个字面量里两串星号之间夹着文字或插值（`"ab***cd***"`、`f"{a}***{b}***"`，`.mts` 的模板字符串同理）时，形态与 `***强调***` 无从区分，同样命中。这几类情形走下文的受控例外登记，不为它们放宽正则。
  - 承诺的范围：在当前扫描面上零误报，已知的反例由形态测试逐条固定（两个掩码同在一行、字面量里的 `//` 与 `/**/`、含引号的正则字面量（含紧跟在 `return` 之后的）、插值代入造成的误判），不是普遍保证。核对数据（按本设计对扫描面逐个字面量核对）：清理前那一版代码恰好命中那八处（都在 Python 字面量里），清理后零命中；`.mts` 侧清理前后两版都是零命中，掩码、幂运算符与 `**/` 均不命中，脱敏用的正则里只含一个撇号或一个双引号的字符类被正确跳过，`"https://"` 与类链查询里的 `/**/` 原样保留在字面量内。
  - 已知盲区：用 `+` 拼接出成对星号的写法（每个字面量单独判定，两段各只有一组星号）与成对星号分在两行的多行字符串（形态不跨行）不命中。
  - 它是一条单独的正则、配单独的测试函数，不并入 `FORBIDDEN`：它管格式、不管用词，失败提示与改法都不同（删掉星号、改用措辞强调）；使用者向 markdown 那侧也没有对应规则（markdown 里 `**` 是正当的强调），并入后上面「扩表时两侧都要过一遍」那句会误指向它。
  - 它不进 `cli/tests/_doc_rules.py`：那里的扫描面是 markdown、注释与 docstring，`**` 在三者里都是正当的强调；字面量抽取只有本测试需要；写完即查的 hook 不扫字符串字面量（[0046](./0046-guardrail-layers-tests-hooks-and-lean-claude-md.md) 决策一），放进规则源也不会让它更早被拦下。
  - 例外：在本测试里按文件与常量名登记并注明理由，只收两种情形：确有只写进 markdown 文件、不到终端与日志的字面量需要强调（注明写入去处）；字面量的运行时值不含强调，只是被上述启发式误判（注明运行时的实际形态）。字面量不在赋值语句里时先提成具名常量再登记，例外因此只落在那一个字面量上；登记项找不到对应的字面量时测试失败，过期的登记须删除。目前没有需要登记的字面量。
- `cli/tests/test_package_readmes.py`：根 README 零禁词，禁词之外另扫口头语与退役旧名两张表（[0045](./0045-documentation-layering-and-placement.md) 决策六 / 八）；进包的六份 README 与 Release 正文的固定块 `.github/release_body_footer.md` 同属包页面，走 `_doc_rules.scan("package-page", …)`，规则束是用户文档的整套规则（内部指代、口头语、退役旧名、符号当谓语、「退 N」、正文箭头、悬空指针）再加零相对链接（正则 `](../` `](./` `](x.md`），固定块先代入占位符样例值再扫、另要求仓库链接锁定 tag（不带 `blob/HEAD/`）；pyproject / package.json `description` 零禁词，根有 `CONTRIBUTING.md`、每包有 `DEVELOPMENT.md`，且 `release.yml` 必须仍调 `release_notes.py check`/`render`、不得有内联 `body: |`；扫描面路径缺失即失败（包搬家 / workflow 改形态不许让护栏变绿）。
- `cli/tests/test_skill.py`：随 wheel 发行的 agent skill 的 markdown 扫描器——同一禁词表与相对链接正则（共享常量 `cli/tests/_doc_rules.py`），另对照 CLI argparse 真值与契约页键名（[0043](./0043-agent-skill-for-driving-gherkai.md) 决策六）。
- `cli/tests/test_user_docs.py`：`CHANGELOG.md` 全文只许绝对 URL（按链接目标判断，行内与引用式都算；Release 正文直接截取本版节、不改写链接，见面二表 Release 行）；它守的用户文档面其余规则，判据在 [0045](./0045-documentation-layering-and-placement.md) 决策三 / 六。
- **护栏管不到的**：正则抓不住的行话（皮 / 装配 / 唯一真源 / 产品本体层）与「使用者读得懂吗」的判断，靠 review——两轮对抗核验都在这一类抓到过遗漏（runtime 页面整篇行话、`--grace` 漏标「仅 run」、定位链顺序写反）。**review 抓到的行话只要能正则化就入表、不留在这一类**：上传与收尾的失败语义那族（best-effort / 抢传 / flush 兜底 / 不带 ref）曾在两引擎 worker 日志各留过几行、全靠人眼 review 才发现，此后已入表；留在这一类的是词形不固定、只能靠读的那些。

## 代价与权衡

- **双份文档**：每个包两份 markdown，改机制时要同时看使用者向与 contributor 向两处；换来的是两类读者各自拿到对的东西，且包页面不再暴露实现细节。
- **延迟生效**：包 README / Summary 的改动要等下一个 tag 才上 PyPI/npm（1.4.0 页面即带着 contributor 文档发出去了，不可改）——发版前把这两处也当作发布物核对。
- **禁词的误伤面**：正则对中文机制名是逐词匹配，「组合根」在 Summary 里也被禁——这是有意的（它对使用者同样是行话）；契约型异常的例外条给了内部符号一个口子，不至于把开发者诊断也拉平成人话。
- **文案变短了**：去掉「为什么」的长尾注后，个别文案失去了对 contributor 的自解释；由紧邻注释补回，对使用者反而更短更准。

## 被拒方案（护栏，防未来重踩）

- **把 contributor README 直接当 PyPI / npm 长描述**（v1.4.0 首发时的实态）：页面满是 ADR 编号、模块树、跑测试说明与相对死链，装了包的人看不懂也用不上。
- **只把根 README 分层、包 README 不动**：包页面恰是最多「没有仓库的人」看到的面，不能例外。
- **文案里保留 ADR 指针「给 contributor 看」**：contributor 有仓库、有注释、有 docstring，不需要借用户的终端传话；用户终端只有用户在看。
- **用环境变量/详细模式切换是否显示内部指代**：两套文案等于两倍维护，且默认面仍会漏。
- **字面量里出现 `**` 即判错、不要求成对**：脱敏掩码、glob 的 `**/` 与字面量里写出的 `2 ** n` 都会被误拦；护栏要在扫描面上零误报才可接受。
- **`.mts` 侧去注释后按整行判定**：相邻两个字面量之间的代码会被当成强调正文，`const masks = ["***", "***"];` 被判为强调；先按 `//` 与 `/* */` 删注释又会删掉字面量内部形如注释的内容（`"https://x"` 之后同一行整段丢失）。故在一遍词法扫描里识别字面量与注释，逐个判定字面量。
- **用 TypeScript 编译器抽取 `.mts` 的字面量**：判定会更精确，但 `uv run pytest` 就要先装好 midscene 包的 npm 依赖，CI 的 pytest 任务也要多装一份；这条规则只需要分清字面量、注释与正则字面量，词法扫描足够，启发式的边界写明在护栏节。
- **让终端输出解析 markdown、把 `**` 显示成加粗**：呈现层刻意不解析标记语法、不用加粗（[0047](./0047-cli-human-readable-tables-with-rich.md)），管道、重定向与日志里也照样是原样的星号。
- **单份 README、分「使用者」「开发者」两节**：PyPI/npm 拿的是整份文件，节切分挡不住 contributor 内容上页面；分文件才能让「进包」这条线物理成立。
- **包 README 用相对链接指 `../docs/…`**：PyPI/npm 页面上全是死链；用 `blob/HEAD/` 的绝对 URL。
- **在 Release 渲染脚本里把 CHANGELOG 的相对链接改写成绝对 URL**：多一层转换只服务一个消费者（Release 正文），CHANGELOG 在 GitHub 上也是人读的用户面；改为 CHANGELOG 全文只写绝对 URL（`blob/HEAD/<path>`）。
- **中文文件名**（journey 曾用）：文件名是引用锚点，要在 URL/终端/grep 里稳定可打——文档文件名一律英文 kebab（CLAUDE.md 文档纪律）。

## 重议闸门

- 有了文档站点（如 mkdocs）→ 包 README 可缩成「装法 + 站点链接」，contributor 内容与 `docs/internals/`（原 `docs/guides/`）一并进站点；本 ADR 的分层原则不变、载体变。
- 国际化（英文文案/文档）→ 禁词表与护栏需按语言各立一份；原则不变。
- 若某类内部机制名成为使用者也需要理解的产品概念（如「variant」「默认指针」已是），从禁词表移出并进 CONTEXT/包 README 解释——判据仍是「使用者需要它才能用对」。

## 对既有文档与 code 的影响

- CLAUDE.md：代码纪律「产品面文案不带内部指代」与文档纪律当时的「README / DEVELOPMENT 分层」条（现为「文档按读者三分类归位」条，[0045](./0045-documentation-layering-and-placement.md)）两条压回规则 + 判据 + 护栏 + 指向本 ADR。
- [0037](./0037-distribution-and-packaging.md) 被拒方案里「contributor README 当长描述」一条改为指向本 ADR。
