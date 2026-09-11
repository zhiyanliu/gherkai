# 0043. 驾驭 gherkai 的 agent skill：住主仓库、CLI 内置安装、内容单份、引用文档为生成副本

> **Status:** Draft（施工中；翻 Accepted 的审计点：skill-creator 评测循环至少跑完一轮并把结果内联到「验证」节、护栏全部落地、影响面反向链已落）

## 背景

[0041](./0041-agent-facing-cli-affordances.md) 与 [0042](./0042-step-evidence-and-explain.md) 把命令面做成了 agent 能驾驭的形态（筛选 flag、`--quiet`、查询类命令的 `--json`、`doctor`、`explain`、JSON 字段契约）。缺的是**教材**：一个 AI coding agent（Claude Code、Codex 或别的）拿到一个使用 gherkai 的项目，怎么知道该先 `plan` 再 `run`、失败了读 `explain` 而不是解析 HTML、什么时候该把一句断言改成确定性 step、Nova 与 Midscene 怎么选、`submit` 退 0 不代表通过。这些知识今天散在 README、六篇 guides 和 `--help` 里，agent 每次都要重新拼，而且拼错的方向是固定的（拿 README 当手册照抄、把退出码当判定、去读 trajectory HTML）。

Agent Skills 是现成的载体：Claude Code、Codex CLI、Cursor 等都认同一份 `SKILL.md`（frontmatter `name` + `description` 触发，正文按需加载，`references/` 与 `scripts/` 作按需资源），`npx skills add <owner/repo>` 能把仓库里任意含 `SKILL.md` 的目录装进七十多种 agent 的对应目录。skill-creator 给出的写法约束也明确：正文 500 行内、三级渐进披露、`description` 承担全部「何时用」且要偏「pushy」、解释 why 而不是堆 MUST、配 with-skill 对 baseline 的评测循环与 description 触发优化。

本 ADR 决定 skill 住哪、内容怎么单源、怎么装到使用方项目、与 docs 的关系、怎么评测，以及护栏。

## 决策

### 一、skill 住主仓库 `skills/gherkai/`，与 CLI 同 tag 发行；不单开 repo

- 目录 = Agent Skills 标准布局：`skills/gherkai/SKILL.md` + `references/` + `evals/`（评测定义）+（按需）`scripts/`。受 git 管理；`.claude/skills` / `.agents/skills` / `.codex/skills` 仍是个人安装态、继续 gitignore，dogfood 时用下面的安装命令装进本仓库自己。
- 理由：skill 教的是命令面，命令面随 CLI 版本变；同仓同 tag 才锁得住一致，也才能上护栏（skill 里出现的每个子命令 / flag / JSON 键逐条对照 argparse 与契约页）。`npx skills` 认子目录路径，「单独 repo 更好装」不成立；单独 repo 只多一条发行轨与一处必漂的版本。
- 与 [0037](./0037-distribution-and-packaging.md) 的关系：skill 是 `gherkai` CLI 包的**包数据**（wheel 内带一份 `skills/gherkai/**` 的拷贝，hatch `force-include` 把仓库根的 `skills/gherkai` 映射进 `gherkai_cli` 包内），故安装态 = 使用方装的 CLI 版本；npm 侧的 worker 包不带 skill（skill 教的是 CLI，不是引擎）。

### 二、内容只有一份：`SKILL.md` 就是工具无关的核心；「适配」只剩装到哪与一行指针

Claude Code 读 `.claude/skills/<name>/SKILL.md`，Codex 读 `.codex/skills/<name>/SKILL.md`（项目级）或 `~/.codex/skills/`，`npx skills` 还会用 `.agents/skills/` 作共享位——三者吃的是**同一份文件**。不写第二份 AGENTS.md 版内容；Codex 侧只在使用方项目的 `AGENTS.md`（Claude 侧同理 `CLAUDE.md`）加**一行**「驾驭 gherkai 用 skill `gherkai`」的指针，因为 Codex 对项目级 skill 的主动触发不够稳、有一行提及会好得多。这一行是安装命令打印出来让人贴的，不是 skill 内容。

### 三、安装面两条，文档推荐第一条

1. **`gherkai skill install [--agent claude-code|codex|agents|all] [--dir <项目根>|--global] [--print]`**：从包内拷贝到目标目录（`--agent` 缺省 `claude-code`；`--global` 装到用户级目录；`--print` 把 SKILL.md 打到 stdout 供管道），幂等覆盖，写一个 `.gherkai-skill-version` 标记（值 = CLI 版本），结束打印该往 `AGENTS.md` / `CLAUDE.md` 加的那一行。退出码 0 / 2（目标不可写、`--agent` 无效）。**装的 skill 永远等于装的 CLI 版本**、离线可用，这是「skill 紧贴命令面」的场景最该保的东西。
2. **`npx skills add zhiyanliu/gherkai --skill gherkai`**：零成本兼得，给不想多敲一条命令的人；代价是拿到仓库 HEAD 的 skill，可能比他装的 CLI 新。README 里作为次选写明这层代价。

Claude 的 plugin marketplace 只覆盖 Claude、仪式更多，现阶段不做（见被拒方案）；将来要做也是在这份 SKILL.md 外面包一层。

### 四、skill 与 docs 的关系：不 link、生成副本；正文是新内容不是复述

- **为什么不能 link**：skill 的消费现场是使用方项目里的一份拷贝，`../../docs/...` 相对链接指向的目录不存在；GitHub 绝对 URL 要联网且得钉到使用方装的 CLI 版本。Agent Skills 的做法就是 skill 目录自带 `references/`。
- **规则**：需要**逐字**进 skill 的事实表（今天只有 JSON 字段契约 `docs/guides/cli-json-contract.md`）在 docs 里那份是唯一**手写**源，`skills/gherkai/references/cli-json-contract.md` 是**生成的派生副本**、进 git（npx 路径要文件真实存在），护栏断言两者字节相等——改了源没同步就红。契约页头部反向加一句「驾驭本工具的 AI agent 请装 skill」。
- **`SKILL.md` 正文**是给 agent 的新文档（操作模型），docs 里没有等价物、不算重复；它与 README 有事实重叠（flag 名、退出码），读者不同写法不同，漂移由护栏挡。guides 是给人的、skill 是给 agent 的，同一机制两边各有一份是**按读者分层**，不是双源；skill 里不出现 ADR 编号与内部机制名（见决策六）。
- GitHub 上 docs 的绝对 URL 可留作次级指针（钉 tag），不承担主链接职责。

### 五、内容重心：agent 的操作模型，不是复述 `--help`

`SKILL.md` 正文（500 行内）按这个骨架写，具体措辞由 skill-creator 循环迭代：

1. **心智模型**：feature 里的 step 有两种跑法——默认 AI（自然语言、Nova / Midscene 执行）与确定性 step（测试开发注册的精确代码，命中即走代码）；两者边界（精确检查、可复现、要快 → 确定性；模糊 / 一次性 / 页面变化多 → AI）；scope / tag 语义（`@scope` = 一条会话一个 job，`@engine`、`@timeout`，普通 tag 归 `--tags`）。
2. **引擎怎么选**：Nova Act 限英文 UI、Midscene 中文 UI 可用；`--default-engine` 与 `@engine` tag；`list-engines` 看本机装了什么；两引擎证据形态的差别对 agent 无感（evidence 同形）。
3. **local 与 cloud、run 与 submit 的选法**：本机 `run` 是前台同步（退出码即判定）；`submit` 是无状态跑批（退 0 只表提交成功，判定看 `status --wait`）；cloud 档先 `doctor --prefix` 自检、部署是部署方的事、版本 skew 退 2 怎么办、variant 与 `--worker-variant`。
4. **工作循环**：`doctor` → `plan`（看派发标注与筛选结果）→ `run` / `submit` → 判定 → 失败先 `explain`（读原因、thought、截图 URI），需要更多再 `--json` 或 `jobs/*.json`，别解析 HTML 报告、别猜产物路径 → 精确检查改成确定性 step（指到两引擎包 README 的写法、`list-deterministic` 验证、`plan` 看标注）→ 用 `--scope` / `--scenario` / `--tags` 收窄重跑。
5. **机读读法**：`--json` 字段去 `references/cli-json-contract.md`；`message` 恒为「为何不是 passed」；`record_missing` 与 `evidence_missing` 的分工；`aborted_hint` 的含义。
6. **成本与超时旋钮**：`--assertion-votes`、`--default-job-timeout`、`--max-concurrency`、`--fail-fast`、`--quiet`、`--no-report` 各管什么、什么时候动。
7. **退出码分流**：`run` / `status` 表判定（0 / 1 / 2），`submit` / `plan` / `explain` / `doctor` 只表做成没做成（0 / 2）；CI 该接哪一条。
8. **别做的事**（每条带为什么）：别把 `submit` 退 0 当通过；别解析 HTML 报告或 SDK 原生 trajectory；别猜产物路径、顺 `ref` 走；cloud 改了 steps 不推镜像等于没改；`--grace` 别调小。

`references/`：`cli-json-contract.md`（生成副本）；`engines.md`（两引擎的选择依据、语言限制、各自 README 的 URL、确定性 step 写法入口）；`cloud.md`（部署方 / 使用方分工、`submit`–`status`–`explain --backend cloud` 一条线、skew 与 variant 的处置）。是否需要 `scripts/`，由评测循环里「多个测试用例是否重复手写同一个 helper」决定（skill-creator 的判据），初版不带。

### 六、护栏：skill 是产品面，同受 0039 约束，且与 CLI 真值逐项对照

- **产品面文案**：skill 全文（含 references 里手写的两篇）不出现 ADR 编号、决策号、内部机制名——它给使用方的 agent 读，与 README 同侧（[0039](./0039-user-facing-surfaces-no-internal-references.md)）；把 `skills/gherkai/**` 加进 `cli/tests/test_user_facing_messages.py` 的扫描根（生成副本 `cli-json-contract.md` 例外——它是 contributor 向 guide 的镜像，允许 ADR 编号；护栏对该文件只查字节相等）。
- **命令面真值**：测试从 SKILL.md 与手写 references 里抽出所有 `gherkai <子命令>` 与 `--flag` 形态的 token，逐个对照 argparse（复用 0041 决策五护栏的取材方式）；抽出的反引号 JSON 键对照契约页——skill 提到不存在的 flag 或键即红。
- **生成副本相等**：`references/cli-json-contract.md == docs/guides/cli-json-contract.md`。
- **形态**：frontmatter 有 `name` 与 `description`、正文 ≤ 500 行、`description` 含「何时用」的触发语境；`.gherkai-skill-version` 由安装命令写、不入库。
- **不复述可调数字**：超时、grace、票数默认值一律「见 `--help`」，与 guides 同律。

### 七、评测与迭代：按 skill-creator 循环，且不花 AWS 钱

- `skills/gherkai/evals/evals.json` 入库，收 3–5 条真实口吻的任务提示（例：「这个 feature 跑失败了，告诉我哪步为什么」「把这条断言改成精确检查」「提交到云端并等结果」「帮我看看这台机器能不能跑 cloud」）；每条配可核断言（用了 `plan` 再 `run`；失败后调了 `explain` 而非读 HTML；用 `--json` 取字段而非正则 stdout；对 `submit` 退 0 的解读正确；改确定性 step 时写在 `steps/` 并用 `list-deterministic` 验证）。
- **评测不依赖 AWS**：`evals/fixtures/` 入库一个真跑产出的小型本机 run 目录（含 evidence、截图裁掉字节只留极小占位）与一个带确定性 step 的样例项目；任务用 `plan` / `explain` / `doctor`（本机段）/ `list-deterministic` 即可完成，真 AWS 的用例最多一条且标 opt-in。工作区 `skills/gherkai-workspace/` gitignore。
- with-skill 对 baseline（无 skill）由 subagent 并行跑，评分 + `generate_review.py` 人审视图 + `aggregate_benchmark`；description 用 20 条应触发 / 不应触发查询（近似误触发为主）跑 `run_loop.py`（`claude -p`）优化，取 held-out 最优。首轮结果内联进「验证」节后翻 Accepted。

## 被拒方案

- **单独 `gherkai-skill` repo**：多一条发行轨，skill 与 CLI 版本必漂，护栏无法跨仓对照真值；`npx skills` 认子目录，可装性不是理由。
- **Claude plugin marketplace 作为主发行面**：只覆盖 Claude、需 `.claude-plugin/marketplace.json` 一套仪式；Agent Skills 标准已让一份 SKILL.md 通吃，marketplace 只在有 Claude 专属需求时再包一层。
- **AGENTS.md 里放一份 Codex 版内容**：双源必漂；Codex 已原生读 SKILL.md，AGENTS.md 只该有一行指针。
- **skill 用相对链接 / GitHub URL 指 docs**：安装态是拷贝、相对路径断；URL 要联网且版本对不上。
- **手工维护 references 副本**：无护栏的重复迟早漂；用生成 + 字节相等测试。
- **在 skill 里教 SDK 原生产物格式**：0042 已用 evidence + `explain` 取代，skill 只教 `explain` 与契约字段。
- **把 README 整份塞进 skill**：README 是给人的操作手册，agent 要的是操作模型与决策规则；塞进去既超 500 行又把「何时该做什么」淹没。
- **评测用真 AWS 跑**：慢、贵、不稳，with-skill 对 baseline 的差异会被网络与模型抖动淹没；fixture 驱动即可覆盖循环的全部步骤。

## 不做 / 延后

- `doctor` 加一项「已装 skill 的版本是否等于 CLI」（读 `.gherkai-skill-version`）：便宜且有用，但等安装命令真用起来再定形态。
- `scripts/`：等评测显示测试用例反复手写同一 helper 再收进来。
- 发布到 skills.sh 一类目录 / registry：等使用方需求。
- 引擎专属 skill 拆分（`gherkai-novaact` / `gherkai-midscene`）：evidence 已同形、引擎差异一页 reference 装得下，不拆。

## 影响面

- 新目录 `skills/gherkai/`（`SKILL.md`、`references/{cli-json-contract.md, engines.md, cloud.md}`、`evals/{evals.json, fixtures/}`）；`.gitignore` 加 `skills/*-workspace/`。
- `cli/pyproject.toml`：hatch `force-include` 带入 `skills/gherkai`；`cli/gherkai_cli/__main__.py`：`skill install` 子命令；新模块 `cli/gherkai_cli/skill_install.py`。
- 测试：`cli/tests/test_skill.py`（命令面真值、副本相等、形态、安装命令）；`cli/tests/test_user_facing_messages.py` 扫描根加 `skills/gherkai`。
- 文档：根 `README.md` 加「让 AI agent 驾驭」一节（两条安装路径、次选的版本代价）；`cli/README.md` 加 `skill install` 行；`docs/guides/cli-json-contract.md` 头部加 skill 指引与「本页有生成副本」提示；`docs/guides/README.md` 末句 skill 指向本目录；`DEVELOPMENT.md` 目录树与 ADR 范围；`CONTEXT.md` 术语加 skill；[0041](./0041-agent-facing-cli-affordances.md) Status 头「agent skill（另立）」改指本 ADR。

## 验证（Accepted 前必做，结论内联到此处）

- 护栏全绿：命令面真值、副本相等、形态、产品面文案。
- `gherkai skill install` 在本仓库 dogfood：装进 `.claude/skills/gherkai/`，Claude Code 能触发；`--print` 输出与文件一致；重复安装幂等。
- skill-creator 循环首轮：每条 eval 的 with-skill 对 baseline 断言通过率与人审反馈；description 优化前后的触发命中率（train / held-out）。
- `npx skills add` 路径在一台干净目录里装一次、目录布局符合预期。
