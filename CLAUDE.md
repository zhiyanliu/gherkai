# 项目约定

## 沟通

- 沟通、讨论一律用中文；思考过程也用中文。
- 在使用 `graphify` 工具时只用英文。

## 文档纪律（ADR / CONTEXT 等）

- **`docs/adr/` 是 ADR 的存放处**：ADR 记稳定决策（what/why/trade-off）、按主题归位；施工进度（步骤/commit 节奏）属实现计划，放对话或 PR；任务跨会话时放 `docs/journey/`（见下 journey 条）。
- 改 code 前先把设计决策落进 ADR——"不实现"≠"不设计"；**改完后回头校准受影响的 ADR/CONTEXT/README，别只落新决策、留旧描述漂移**（文档陈旧多半源于此）。**校准枚举型内容（目录树 / flag 表 / 模块清单 / 字段·事件类型列表 / 交叉引用 / 编号范围）必须逐条对照真值集（`ls` / grep / argparse），不能靠读——「读着没问题」是「绿≠对」的文档版：只覆盖已写出的、照不出遗漏项（遗漏项在读已列内容时是隐形的）。**
- 精简文档时不删决策理由、权衡、反模式；**移除某功能/方案时同理——删其施工生平（曾如何实现/分几步），但留一条「被拒方案+为什么」护栏，防未来重复进坑。**
- **读者比例决定优化方向**：ADR/CONTEXT 主要给 AI coding agent 读（约 80%）→ 优化向信息密度、单一事实源、精确指针，冗余=噪声、敢压；README 主要给人读 → 保叙事、不激进压缩。据此定"压缩 vs 保留"。
- **ADR Status 头**：每个 ADR 开头带一行 `> **Status:** Accepted / Superseded-by NNNN / Partially-superseded-by NNNN / Draft / Historical`。新增 ADR 必带；当某 ADR 取代/反转旧 ADR 时，**同步更新旧 ADR 的 Status 头**（反向链），别只在新 ADR 里单向记。
- **指针只指稳定物，不指会话上下文**：文档里的交叉引用指向文档自身的节/条或 code 里稳定存在的符号（如「见上『会话血缘回传』条」）；**别写只在当前对话/任务里成立的指代**（如「#1 修复」「本轮那个 bug」「WP3-A」）——对未来读者是悬空引用，且伪装成精确、比模糊表述更坑。带任务上下文写文档时最易犯。**判据 = 文档寿命**：本约束管 ADR/CONTEXT/README 等长期文档；`docs/journey/`（暂时 staging 区，见下条）里**可用**任务/WP 编号——它是过程坐标、吸收进 ADR 时会翻译成稳定表述。
- **引用方向单向：Journey→ADR，绝不反向**（稳定物不依赖易变物）。长期文档（ADR/CONTEXT/README）**及 repo 内 code 注释**引用会被吸收后删除的 journey（见下条）迟早悬空，撞上条「指针只指稳定物」；反之 journey 引 ADR 自然正确。**code 注释同受此约束**（注释随 code 长期存在、被未来 AI/人消费，同属稳定物；repo 内注释一律守——「一次性脚本不进 repo」见「工作方式」）——注释引 ADR/稳定符号、不引 journey、不用裸 WP 编号。故「Journey 吸收进 ADR」= 把结论**连同支撑证据/数据内联**进 ADR 使其自包含（证据是「为何这样设计」的上下文，既帮读 ADR 的 AI 也帮 review 的人，值得让 ADR 长一点），**非** ADR 留指针指回 journey；需留血缘时用**自包含的事件描述**（如「据中断丢失实测预演」）替代 journey 链接——**注意 WP 编号（WP-S/WP3-B…）本身也是指向 journey 时间线的悬空指针**（上条「指针只指稳定物」已禁裸 WP 编号入长期文档），故血缘描述**不能用 WP 编号**、要翻成对未来读者自明的表述。**唯一例外、绑死 Status 头**：Draft ADR 施工中、证据尚未吸收完，可暂留 journey 引用作过程标记——但这是 **Draft→Accepted 前必清的债**（翻 Status 时即审计点，把证据内联、去引用）；**Accepted/冻结的 ADR 必自包含**。
- **`docs/journey/` 是任务推进的 staging 区，不是永久文档**：存当前工作的**过程**产物（进度/调查/探索/复盘）。**建不建，判据 = 过程信息有没有对话之外的读者**（对话上下文跨会话不可靠——截断/压缩/换 agent）：①下个会话/接手的 AI 要**恢复现场** → 进度总纲（做到哪、关键中间结论、下一步）、后续批次还要引用的调查记录；②人要**异步 review** → 待批报告（批毕即删）；没有这样的读者（单次会话内闭环）→ **不建**，过程留对话、别为小任务造文件。生命周期 = staging → 内容吸收进 ADR（决策）/ code（实现）/ commit（过程记录）→ 可删或归档；**任务收尾即审计点**（该吸收的吸收、吸收完即删）。**不苛求永久文档的严谨，只求「准确反映当前状态 + 导航有用」**：状态变了就改（别留旧态漂移）、别当永久建筑维护。文档内首行 `> 类型:` 头声明子类型（进度总纲/调查记录/…）——**不给它设计类型缩写**（journey 是异质集合、又是暂存，精确类型学是 ADR（结论、长期、要精确引用）才需要的严谨）。与 ADR 的对称在**寿命层**（journey 记过程/暂时 vs ADR 记结论/永久），非缩写层。
- **`docs/guides/` 是给人（使用者/contributor）的阅读理解层（派生视图）**：凡帮人理解系统如何工作的**解释性文档**都归此——机制横切解读、数据流叙事、阅读路径等；README 停在鸟瞰与上手、ADR 按决策切片为 AI 检索优化，人要的成体系理解两者都给不出，此层补位。判据三条：**只讲 how、不复述 why**（决策理由/权衡/被拒方案留 ADR，guide 只给指针）；**权威在 ADR+code，新决策绝不先落 guide**（冲突以权威为准；每篇头部声明此定位、正文带权威指针）；**立文门槛 = README 给不到的深度 + 单个 ADR 直读给不出的理解视角**（典型 = 跨多个 ADR 才拼得出全貌的横切合成），不做逐 ADR 人话翻译。
- **文档文件名 = 英文小写连字符标题（kebab-case），全 `docs/` 通用**：`docs/adr/` 与 `docs/journey/` 带四位编号前缀 `NNNN-`（两个目录各自独立编号、只增不复用），`docs/guides/` 及其它文档不编号；文件名不用中文、不用空格/下划线/大写。**唯一例外 = 约定俗成的全大写索引/入口文件**（`README.md`、`CONTEXT.md`、`CLAUDE.md`、`docs/REFERENCES.md`、各包 `DEVELOPMENT.md`），它们靠通行惯例被人一眼认出，保持原名。文件名是引用锚点、要在 URL/终端/grep 里稳定可打，中文标题放文档首行 `#` 即可。
- **README / DEVELOPMENT 分层：按读者切文件，成对存在**。使用者向 = 根 `README.md` + 各包 `README.md`；contributor 向 = 根 `DEVELOPMENT.md` + 各包 `DEVELOPMENT.md`。**共用一条内容规则**：使用者向只写「这是什么、装法、用法、配置、退出码/错误怎么办」，**不写** ADR 编号/决策号/内部机制名/目录结构/开发环境/测试/spike/发布流程/设计叙事；这些全归 contributor 向，并带 ADR 指针。判据 = 「装了包 / 点开仓库首页、没读过 ADR 的人看得懂且用得上」——与代码纪律「产品面文案不带内部指代」同一原则。四层只差**去向与链接形态**：

  | 文件 | 去向 | 链接 |
  |---|---|---|
  | 根 `README.md` | 仓库首页；末尾「深入了解」一节链 CONTEXT / guides / adr / DEVELOPMENT | 相对链接可（GitHub 渲染） |
  | 各包 `README.md`（`cli/` `core/` `runtime/` `deploy_aws/` `engines/*`） | 逐字上 PyPI / npm 页面（pyproject `readme` / npm `files`）；**改动随下一个 tag 才生效** | **只用绝对 URL**（页面上相对链接全是死链）；最多末尾一句「设计文档见仓库 docs/adr」 |
  | 根 `DEVELOPMENT.md` | contributor 入口：版本线、目录结构、从 checkout 跑、测试、spike、发布、各包 DEVELOPMENT 索引 | 相对链接 |
  | 各包 `DEVELOPMENT.md` | 该包 contributor 文档：模块布局、从 checkout 跑、测试、维护者踩坑；**不进 sdist / wheel** | 相对链接 |

  护栏 = `cli/tests/test_package_readmes.py`：使用者向文件与 pyproject / package.json 的 `description` 零内部指代，包 README 零相对链接，根与每包都有 `DEVELOPMENT.md`。

## 代码纪律

- **写/改 code 前对照相关 ADR 的已定决策、契约、不变量**——逐步叠加式开发最易偏离设计；先确认没违背相关 ADR 的红线（散见各 ADR，勿在此复述以免漂移），再动。
- **绿 ≠ 对：识别结论的证据边界** 单测 /「跑绿」只覆盖 mock 之内的世界；凡结论依赖 mock 之外的**真实行为**——进程/信号、并发时序（greenlet/事件循环）、真实 IO 与网络超时、第三方 SDK 的落盘/退出时机——绿测试**不构成证据**，须真跑或对抗核查才算数。**判据**：问「这结论要成立，靠的是我写的逻辑，还是被 mock 掉的那部分真实行为？」——后者→升级验证（真跑 / 独立追问 / 对抗审查），别拿绿当已证。**别过度**：纯逻辑、mock 内的结论，绿即够，无差别真跑/开对抗只是浪费——这条的价值在**分流**，不在"一律怀疑"。（本项目亲历：假阳性测试、SIGKILL 挂死、抢传实际没生效、退出被慢上传拖住——全部单测绿、全部真跑/追问才暴露。）（要真跑验证 worker 时，`tools/e2e_harness.py` 是打通真实边界的现成工具——先翻 `tools/` 的惯例见「工作方式」。）
- **产品面文案不带内部指代** 凡能到用户终端/日志的文字——`--help`、提示、警告、错误、worker/Lambda 日志——**不写** ADR 编号、决策号、「不变量/定位链/被拒方案/重议闸门/实测项」这类内部机制名、内部函数名或「见模块头/接缝契约」；使用者手里没有仓库，这些是噪声甚至误导。文案只说**发生了什么、为什么（产品语言一句）、怎么办**；维护者要的设计指针留在紧邻的注释/docstring。护栏 = `cli/tests/test_user_facing_messages.py`（生产代码全部非 docstring 字符串字面量 AST 扫描 + midscene `.mts` 去注释按行扫）；包页面那一面由「README 分三层」条与 `cli/tests/test_package_readmes.py` 管。
- **接口诚实优先于改动规模：别为省测试改动扭曲生产接口** 「更干净的接口」与「最小改动规模（少动现有测试/调用点）」冲突时，选诚实的接口——测试为设计服务，不是设计迁就测试（与「绿≠对」同源工程观：绿/省事都不等于对）。

## 工作方式

- **`tools/` 是复用工具库，真跑/验证/诊断前先翻一眼、别重造**：做端到端真跑、跨真实边界验证、时序/数据诊断这类活前，先看 `tools/` 有没有现成的（AI 的默认倾向是从头搭脚本、易重复造轮子且可能搭错）。**`tools/` 里的都是长期资产**——真正一次性的脚本/脚手架放 `$CLAUDE_JOB_DIR/tmp`、不入库（入了 `tools/` 即视为长期、注释守文档纪律）。
- **AWS 资源视为免费（限开发期）**：设计、调研、验证、测试等开发环节按「资源免费」处理——用对任务最有帮助的方式做，省 AWS $ 不是决策变量、更不是不真跑的理由（与「绿≠对·别过度」不冲突：那条省的是 effort，$ 不进「浪费」衡量）。免费≠空转：用完随手停 task/清资源。**交付物的运行成本不免费**：部署到目标环境后持续烧的 AWS 是设计约束，做架构/方案时须纳入权衡。判据=谁持续买单：开发期我们自己为把事做对烧，放开；运行期目标环境为交付物长期付，应省则省。

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:

- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
