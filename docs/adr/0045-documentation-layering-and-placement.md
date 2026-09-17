# 0045. 文档分层与归位：按读者三分类、目录归位、包页面降为入口页、每版 changelog、按类别定口吻

> **Status:** Accepted（2026-09-17）—— 本 ADR 是 CLAUDE.md 文档纪律「文档分层与归位」条的决策与理由所在；反转 [0039](./0039-user-facing-surfaces-no-internal-references.md) 面二「各包 README = 完整操作手册」为「入口页」（0039 Status 头已同步）；skill 与文档的关系维持 [0043](./0043-agent-skill-for-driving-gherkai.md) 决策四不变。

## 背景与问题

文档是门面：技术读者、使用者、AI 工具都从文档进入。v1.4.3 时的文档面有五个结构性问题，它们互相放大：

1. **根 README 同时是仓库门面和用户手册**（206 行：能做什么 / 架构 / 披露 / 前置 / 谁用它 / 安装 / 上手四步 / 写 feature / agent / 注意 / 深入），第一次打开的人找不到「30 秒内我该做什么」；agent 路径在第 177 行，而使用这类工具的人多数已在用 AI 工具。
2. **各包 README 各自是完整手册**（[0039](./0039-user-facing-surfaces-no-internal-references.md) 面二的口径），于是重复由纪律约束而非结构消灭：cli README 的上手与根 README 平行，两引擎 README 里「怎么写确定性 step」是两段近乎逐句对称的文字，改一处漏一处。
3. **`docs/guides/` 与「用户指南」撞名**，它实际是给想懂机理的人的横切解读层，不是用户指南。
4. **建造者 AI 的工作文档散在 `docs/` 根**（两份 health-review 方法、REFERENCES），与 ADR / CONTEXT 同类却没有归位。
5. **Release 正文是固定模板**，每版内容相同、只换版本号；文档链接用 `blob/HEAD/`，装到手的版本与链到的文档可能不是同一版。另有口吻混杂：同事间的口头语与隐喻（「角色是帽子不是人」）进了使用者页面。

## 决策

### 一、读者三分类，用户侧 agent 归用户文档

| 类 | 读者 | 内容 | 位置 |
|---|---|---|---|
| **建造者 AI** | 构建本工具的 AI coding agent（约 80% 读者，[CLAUDE.md](../../CLAUDE.md) 文档纪律「读者比例决定优化方向」条） | ADR、`CONTEXT.md`、`CLAUDE.md`、`.claude/commands/`、`docs/ai-eng/`（REFERENCES 外部一手来源 + 两份 health-review 方法）、`docs/journey/` | ADR / CONTEXT / CLAUDE.md 位置固定（工具有位置依赖）；方法文档与 REFERENCES 归 `docs/ai-eng/` |
| **技术文档** | contributor；想懂机理的技术人员 | contributor：根 `CONTRIBUTING.md` + 各包 `DEVELOPMENT.md` + `.github/workflows/README.md`；机理：`docs/internals/`（原 `docs/guides/`） | DEVELOPMENT 留包旁（见被拒方案） |
| **用户文档** | 使用者，以及**使用者侧的 AI agent** | `docs/user-guide/`（叙事主页）、根 `README.md`（门面）、各包 `README.md`（入口页，逐字上 PyPI / npm）、GitHub Release 正文、agent skill（[0043](./0043-agent-skill-for-driving-gherkai.md)） | 新建 `docs/user-guide/`，其余原位改写 |

使用者侧的 agent 读的是产品说明（skill），它是用户文档的一种形态，不与建造者 AI 混类——两者的写法相反：前者产品语言、零内部指代（[0039](./0039-user-facing-surfaces-no-internal-references.md)），后者高密度、精确指针。

### 二、目录归位

- `docs/guides/` → **`docs/internals/`**：内容与判据不变（只讲 how、权威在 ADR + code、立文门槛），只改名消撞名。
- `docs/doc-health-review.md`、`docs/code-health-review.md`、`docs/REFERENCES.md` → **`docs/ai-eng/`**：目录含义 = 「建造者 AI 的工作文档，除去 ADR / CONTEXT 两根位置固定的柱子」，`docs/README.md` 地图写明这层关系。命名按读者而非内容，因为 REFERENCES 不是方法（`methods/` 装不下它）。
- 新建 **`docs/user-guide/`**：从根 README 与各包 README 拆出的叙事与流程——上手、写 `.feature`、写确定性 step（双引擎并排一篇）、跑与看结果（命令 / 退出码 / 报告 / 成本）、测本机应用、云端后端部署（原 deploy_aws README 的操作部分）、配置（env 旋钮：模型、region、grace…）、常见问题。
- 根 `DEVELOPMENT.md` → **`CONTRIBUTING.md`**（GitHub 在 PR / issue 界面自动链接该名；内容 = 如何参与：环境、测试、发布链、文档地图）。**各包 `DEVELOPMENT.md` 留原位**（见被拒方案）。
- **`docs/README.md` = 全部文档的地图**（按读者分类、每类去哪、权威在哪）；`docs/internals/README.md`、`docs/user-guide/README.md`、`docs/ai-eng/README.md` 各是本子类的索引兼 **owner 表**（一个主题只有一篇是 owner，其余只链不讲）。
- ADR、CONTEXT.md、CLAUDE.md、`docs/journey/` 不动。

### 三、包页面降为入口页（反转 0039 面二的「完整操作手册」）

各包 `README.md`（逐字上 PyPI / npm）只留四样：**一句定位、装法、最小用法、绝对 URL 指向 GitHub 上的 user guide 与本包相关页**。叙事、流程、选项细节全部归 `docs/user-guide/`。两引擎的「怎么写确定性 step」合成 user-guide 里**一篇双引擎并排**的页面（Python 与 TypeScript 逐项对照，这正是「两腿对称」原则的文档形状），包页只留 import 路径、一行示例与链接。

理由：重复从「靠 owner 表约束」变成「结构上不存在」——包页没有可与 user guide 重复的内容。代价：从 PyPI / npm 页读到细节要跳转一次；接受，仓库开源、链接即到。护栏：`cli/tests/test_package_readmes.py` 仍守零内部指代、零相对链接、每包一份 DEVELOPMENT（根改为 CONTRIBUTING）；新增 `cli/tests/test_user_docs.py` 守 user-guide / 根 README / CHANGELOG 的零内部指代、相对链接可达、不链建造者 AI 文档、owner 表与目录两向差集；`cli/tests/test_release_notes.py` 守「每个已发行 tag 在 CHANGELOG 有非空节」与 Release 正文钉 tag。

### 四、根 README = 门面 + 30 秒上手，agent 路径优先

顺序：一段定位（这是什么、给谁、跑在哪） → 安装 → **上手两条路，agent 先**（`gherkai skill install` + 「告诉 agent 你要测什么」；然后才是手敲 CLI 的最小四步） → 精简架构图（什么跑在哪、费用从哪来） → 「判定由谁做出」披露节（[0044](./0044-engine-model-selection-and-override.md)）→ 文档去哪读（指 `docs/README.md`）。完整架构图、四种跑法细节、写法、CI 集成、注意事项全部链到 user guide 或 internals。

### 五、每版 changelog，Release 正文与链接钉 tag

- 根 **`CHANGELOG.md`**（Keep a Changelog 形态），每版一节、使用者语言（新增 / 变化 / 修复 / 升级须知——如默认模型换代、需重跑 `gherkai deploy`），**发版前**由建造者 AI 从该版 commit 提炼、人审。
- 发布链 gate **校验本 tag 在 CHANGELOG 里有节**，缺则发版失败——changelog 从「记得写」变成「不写发不出」。
- GitHub Release 正文 = 该节正文 + 固定的装法 / 升级块（`.github/release_body_footer.md`，`.github/scripts/release_notes.py` 渲染）；块里指向仓库文档的链接**钉 `blob/vX.Y.Z/`**，每版说明与它链到的文档永远互相匹配，不随 HEAD 漂。**各包 README 里的链接仍指 `blob/HEAD/`**：它们是静态文件、随 wheel / tarball 逐字发出，钉 tag 要在构建期替换（见被拒方案）；包页只是入口、指向的是长期稳定的页面名，HEAD 可接受。各包 pyproject 的 `Changelog` URL 改指 `CHANGELOG.md`。
- 被拒：GitHub 自动生成 release notes——本仓库无 PR 流、commit 信息是工程语言，生成物对使用者无用（`generate_release_notes: false`）。
- 被拒：构建期替换包页链接为钉 tag——要给五个 wheel 与一个 npm 包各加一道 README 改写步骤，换来的只是入口页链接不随 HEAD 漂；入口页本身不承载会随版本变的细节，收益不抵复杂度。

### 六、按类别定口吻

- **用户文档**（user-guide、根 README、包页、Release 正文、skill）：产品说明口吻——陈述句、任务导向、术语统一、每句有动词；不用隐喻、同事口头语、内部俏皮话（「角色是帽子不是人」「版本要自己钉」属此类）；参照主流云服务文档的写法。
- **技术文档**（CONTRIBUTING / DEVELOPMENT / internals）：技术说明口吻——允许术语与密度，不允许俏皮；internals 保叙事。
- **建造者 AI 文档**（ADR / CONTEXT / 方法文档）：维持既有高密度、单一事实源、精确指针的约定。
- doc-health 方法对使用者向文档加一个**口吻 / 可读性**维度（属主观类，出报告待批），防回潮。

## 与 agent skill 的关系（0043 不变）

skill 正文与 references 是为使用者侧 agent **新写**的内容、不是任何用户文档的复制；只有 `references/cli-json-contract.md` 由 `docs/internals/cli-json-contract.md` 经 `tools/render_skill_contract.py` 确定性渲染（源路径随本次改名同步）。「原始维护的文档」与「skill 引用的知识」的一致性由三层保：手写源唯一、渲染器只做登记过的替换、`cli/tests/test_skill.py` 断言副本等于渲染结果；其余 references 由同一测试对着 argparse 与真值集核。文档重组因此不影响 skill 的有效性。

## 被拒方案（护栏）

- **新造「codebase 说明」文档类**——仓库说明拆三层已够：根 README 门面留「仓库里有什么」一段、目录与模块细节归 CONTRIBUTING / DEVELOPMENT、文档地图归 `docs/README.md`。
- **把各包 DEVELOPMENT 吸收进 `docs/`**——它讲「怎么在这个包里干活」，不是机理（internals）；搬走丢局部性（contributor 打开包目录就该看到它），且不进发行包本就无需与 README 同处 PyPI 语义。
- **`docs/ops/` 作方法文档目录名**——`ops` 在工程语境是运维（本项目真有 deploy 这条运维线），撞义。
- **包页维持完整手册、靠 owner 表约束重复**——纪律约束的重复迟早漂，结构消灭一次解决。
- **搬 CONTEXT.md / CLAUDE.md / ADR**——有工具位置依赖，收益为零。
- **用户文档保留隐喻与口头语「更亲切」**——对第一次打开页面的使用者是负担，主流产品文档无此写法。

## 对既有文档与 code 的影响

- 路径改动：`docs/guides → docs/internals`；`docs/{doc,code}-health-review.md`、`docs/REFERENCES.md` → `docs/ai-eng/`；根 `DEVELOPMENT.md → CONTRIBUTING.md`。指针同步点：`CLAUDE.md`（文档纪律三条 + kebab-case 例外清单）、`.claude/commands/*`、`tools/render_skill_contract.py` 的源路径、`cli/tests/test_skill.py` 与 `cli/tests/test_cli_json_contract.py`、`deploy_aws/tests/test_workers.py` 的契约页路径、各 DEVELOPMENT / README 里的相对链接、ADR 内指向 guides / REFERENCES 的指针。
- 新增：`docs/README.md`、`docs/user-guide/**`、`docs/ai-eng/README.md`、`docs/internals/architecture-overview.md`、`CHANGELOG.md`、`.github/scripts/release_notes.py` + `.github/release_body_footer.md`（gate 的 changelog 校验、Release 正文渲染）、护栏 `cli/tests/test_user_docs.py` / `cli/tests/test_release_notes.py`；doc-health 方法加 TONE 类（第六类）并按新分类改写覆盖范围与侧重。
- 0039 Status 头改 Partially-superseded-by 0045（面二「完整操作手册」被反转；面一与护栏不变）；CLAUDE.md 文档纪律「README / DEVELOPMENT 分层」条改写为「文档分层与归位」并指本 ADR。
