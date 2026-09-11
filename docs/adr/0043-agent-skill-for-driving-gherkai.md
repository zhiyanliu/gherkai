# 0043. 驾驭 gherkai 的 agent skill：住 CLI 包内、随 wheel 发行、内容单份、引用文档为确定性转换的副本

> **Status:** Draft（施工中；翻 Accepted 的审计点：skill-creator 评测循环至少跑完一轮并把结果内联到「验证」节、护栏全部落地、影响面列出的每处反向链已落——含 0041 Status 头改 Partially-superseded-by 0043）

## 背景

[0041](./0041-agent-facing-cli-affordances.md) 与 [0042](./0042-step-evidence-and-explain.md) 把命令面做成了 agent 能驾驭的形态（筛选 flag、`--quiet`、查询类命令的 `--json`、`doctor`、`explain`、JSON 字段契约）。缺的是**教材**：一个 AI coding agent（Claude Code、Codex 或别的）拿到一个使用 gherkai 的项目，怎么知道该先 `plan` 再 `run`、失败了读 `explain` 而不是解析 HTML、什么时候该把一句断言改成确定性 step、Nova 与 Midscene 怎么选、`submit` 退 0 不代表通过。这些知识今天散在 README、六篇 guides 和 `--help` 里，agent 每次都要重新拼，而且拼错的方向是固定的（拿 README 当手册照抄、把退出码当判定、去读 trajectory HTML）。

Agent Skills 是现成的载体：Claude Code、Codex CLI、Cursor 等都认同一份 `SKILL.md`（frontmatter `name` + `description` 触发，正文按需加载，`references/` 与 `scripts/` 作按需资源）；`npx skills add <owner/repo>` 会扫仓库里约定的 skill 容器目录（仓库根、`skills/`、各 agent 的 `*/skills/` 等，每个容器有深度上限，容器外要给直指路径或 `--full-depth`），把命中的 skill 装进七十多种 agent 各自的目录。skill-creator 给出的写法约束也明确：正文 500 行内、三级渐进披露、`description` 承担全部「何时用」且要偏「pushy」、解释 why 而不是堆 MUST、配 with-skill 对 baseline 的评测循环与 description 触发优化。

本 ADR 决定 skill 住哪、内容怎么单源、怎么装到使用方项目、与 docs 的关系、怎么评测，以及护栏。

## 决策

### 一、skill 真身住 CLI 包内 `cli/gherkai_cli/skills/gherkai/`，随 wheel 天然带走；不单开 repo、不放仓库根、不用 force-include

- 目录 = Agent Skills 标准布局：`SKILL.md` + `references/` +（按需）`scripts/`。**只放发行内容**——评测资产另立仓库根 `skills/gherkai-evals/`（决策七），结果工作区 `skills/gherkai-workspace/`（gitignore）。理由：两条安装腿都是**整目录递归拷贝**（包内拷 / `npx skills` 的拷贝与软链都先整棵树落地），排除名单由安装器硬编码、使用方无法配置，唯一可靠的隔离手段是不把评测放进被拷的目录；Agent Skills 规范也明说 skill 目录可含任意文件、宿主不替你剪。
- **为什么住包内而不是仓库根**：hatchling 对包目录内的非 `.py` 文件默认收进 sdist 与 wheel，editable（uv workspace）开发态也在同一路径——运行期定位一律 `importlib.resources.files("gherkai_cli") / "skills" / "gherkai"`，dev 与发行同一条路径、**不设仓库根回落**（对齐 [0037](./0037-distribution-and-packaging.md) 决策 3「不设 dev 模式特判」）。**踩坑护栏**：wheel target 的 `force-include` 引用项目根之外的路径（`../skills/gherkai`），在 `uv build`（默认先出 sdist、再从 sdist 解包目录构 wheel）下必 `FileNotFoundError` 硬失败——CI 与发布链跑的正是无 flag 的 `uv build --all-packages`（实测复现）；只写 sdist target 的 force-include 能过，但 `uv build --wheel` 与 editable 树里该目录不存在、成静默漏文件。故不用 force-include。
- **理由（住主仓库）**：skill 教的是命令面，命令面随 CLI 版本变；同仓同 tag 才锁得住一致，也才能上护栏（skill 里出现的每个子命令 / flag / JSON 键逐条对照 argparse 与契约页）。单独 repo 只多一条发行轨与一处必漂的版本。npm 侧的 worker 包不带 skill（skill 教的是 CLI，不是引擎）。
- 个人安装态不入库：`.claude/skills`（已由 `.claude/*` 忽略）、`.agents/skills`（已由 `.agents/` 忽略）；dogfood 时用决策三的安装命令装进本仓库自己，跑评测前先移走（决策七的隔离前置）。

### 二、内容只有一份：`SKILL.md` 就是工具无关的核心；「适配」只剩装到哪与一行指针

Claude Code 读 `.claude/skills/<name>/SKILL.md`（项目级）或 `~/.claude/skills/`；Codex 读 `.agents/skills/<name>/SKILL.md`（仓库级，自 CWD 向上扫到项目根）与 `~/.agents/skills/`（用户级），`~/.codex/skills` 是保留的向后兼容旧位、`.codex/skills` 官方从未列出——都不用；`npx skills` 装 Codex 时项目级落的也是 `.agents/skills/`。三者吃的是**同一份文件**。不写第二份 AGENTS.md 版内容：Codex 的隐式触发同样只看 frontmatter 的 `description`（显式是 `$gherkai`），skill 的发现不依赖 AGENTS.md；使用方项目 `AGENTS.md` / `CLAUDE.md` 里那一行「驾驭 gherkai 用 skill `gherkai`」是成本近零的兜底提示、顺带告诉人可以显式调，不是发现或触发的必要条件——真正决定命中率的是 `description`（决策七）。这一行由安装命令打印出来让人贴，不是 skill 内容。

### 三、安装面两条，文档推荐第一条

1. **`gherkai skill install [--agent claude-code|codex|all] [--dir <项目根>|--global] [--print]`**：从包内拷到目标目录。`--agent` 缺省 `claude-code`（→ `.claude/skills/gherkai/`）；`codex` → `.agents/skills/gherkai/`（`--global` 时分别 `~/.claude/skills/` / `~/.agents/skills/`）；`--print` 把 SKILL.md 打到 stdout 供管道。**语义是整目录收敛、不是幂等覆盖**：先删目标 skill 目录再整份写入，装完目录逐字节等于包内那份，跨版本升级不留旧 reference；删前只认「含 `.gherkai-skill-version` 标记、或本就为空 / 不存在」的目录，否则退 2 报「这个目录不像是本命令装的，先自己挪走」（防 `--dir` 打错整掉用户目录）。标记值 = 已安装发行版本（[0037](./0037-distribution-and-packaging.md) 决策 7 的同一取法）；源码直跑取不到 → 标记记「版本未知」、安装照常完成（不拒装，与 0037「取不到就跳过比较」的分叉一致；禁止把 `--version` 显示用的占位串写进标记）。结束打印该往 `AGENTS.md` / `CLAUDE.md` 贴的那一行。退出码 0 / 2。parser 形态：`skill` 用普通嵌套 subparser、子动词 `required=True`（裸 `gherkai skill` 由 argparse 报错退 2）；不套 `deploy` 的 `set_defaults` 间接层——那是为 provider 中立设的，`skill` 无 provider。**推荐它的理由**：离线可用、版本自动对齐（不用人手抄版本号、不会钉错）——装的 skill 永远等于装的 CLI 版本。
2. **`npx skills add https://github.com/zhiyanliu/gherkai/tree/<ref>/cli/gherkai_cli/skills/gherkai`**（`--agent claude-code|codex`）：给不想多敲一条 gherkai 命令的人。skill 不在 `npx skills` 的默认容器目录里，故用官方支持的直指路径形态；`<ref>` = `HEAD` 拿默认分支最新（可能比装的 CLI 新），= `v<版本>` 即钉到 CLI 版本（tag 名 = `v` + `gherkai --version`）。两条代价写进 README：不钉 tag 时可能比 CLI 新；Codex 用户级落点与本命令分叉（`npx` 写 `~/.codex/skills/`，本命令写 `~/.agents/skills/`）。

Claude 的 plugin marketplace 只覆盖 Claude、仪式更多，现阶段不做（见被拒方案）；将来要做也是在这份 SKILL.md 外面包一层。

### 四、skill 与 docs 的关系：不 link、确定性转换出副本；正文是新内容不是复述

**本条反转 [0041](./0041-agent-facing-cli-affordances.md) 决策五「skill 只链接契约页、不复制字段表」**——手写源仍是唯一事实源，反转的只是「复制即第二事实源」这一判断：有生成器与护栏的副本不是第二事实源。

- **为什么不能 link**：skill 的消费现场是使用方项目里的一份拷贝，`../../docs/...` 相对链接指向的目录不存在；GitHub 绝对 URL 要联网，且指向默认分支上的 docs、可能比使用方装的 CLI 新。Agent Skills 的做法就是 skill 目录自带 `references/`。
- **副本 = 确定性转换，不是 `cp`**：`docs/guides/cli-json-contract.md` 是唯一**手写**源；`references/cli-json-contract.md` 由入库的生成器渲染，转换规则是稳定契约、逐条列举：① 剥掉头部「定位 / 权威在 code / 护栏」引用块与姊妹页导航段，换成一句产品语言（「本页讲 `--json` 各命令输出有哪些字段、什么意思、何时出现」）；② 正文里指向仓库内文件的指针改成 `gherkai <子命令> --help` 或 `https://github.com/zhiyanliu/gherkai/blob/HEAD/<path>` 绝对 URL；③ 禁词按一张入库的显式映射表改写（如「定位链」→ 产品语言），命中未登记禁词即红。护栏断言 `transform(源) == 入库副本`——仍是「改了源没同步就红」，也仍然否掉「手工维护副本」。契约页的键覆盖护栏继续只对源页断言。契约页头部加一句「驾驭本工具的 AI agent 请装 skill；本页有转换副本随 CLI 发行」。
- **`SKILL.md` 正文**是给 agent 的新文档（操作模型），docs 里没有等价物、不算重复；它与 README 有事实重叠（flag 名、退出码），读者不同写法不同，漂移由护栏挡。guides 给人、skill 给 agent，同一机制两边各有一份是**按读者分层**，不是双源。
- GitHub 上 docs 的绝对 URL 可留作**次级**指针，形态按 [0039](./0039-user-facing-surfaces-no-internal-references.md) 面二的发行物约定用 `blob/HEAD/`（不绑分支名 / tag）；版本一致性靠「装的 skill == 装的 CLI」（决策三）保证，不靠 URL 钉版本——也正因 `HEAD` 的 docs 可能比装的 CLI 新，它只能作次级指针。

### 五、内容重心：agent 的操作模型，不是复述 `--help`

`SKILL.md` 正文（形态上限见决策六）按这个骨架写，具体措辞由 skill-creator 循环迭代；正文不出现 ADR 编号与内部机制名（决策六），下面括注的 ADR 只是本文的权威指针：

1. **心智模型**：feature 里的 step 有两种跑法——默认 AI（自然语言、Nova / Midscene 执行）与确定性 step（测试开发注册的精确代码，命中即走代码）；两者边界（精确检查、可复现、要快 → 确定性；模糊 / 一次性 / 页面变化多 → AI）；scope / tag 语义（`@scope` = 一条会话一个 job，`@engine`、`@timeout`，普通 tag 归 `--tags`）。
2. **引擎怎么选**：Midscene 对被测 UI 语言不限；Nova Act 的支持范围是英文 UI——非英文页上导航与页面级语义断言可用，但「正文里是否出现某个词」这类断言会稳定判否（系统性、投票治不了）。诊断规则：Nova 档下非英文页面的断言判否先排查引擎语言面、别先当被测应用的 bug；三条出路 = `@engine:midscene` 路由 / 断言改写成页面级语义陈述 / 文本与结构检查改成确定性 step。`--default-engine` 与 `@engine` tag；`list-engines` 看本机装了什么。evidence 的 **schema** 两引擎同形（读法一套、`explain` 通吃），但**填充**有系统性引擎差（frame 级 `url` 只有 Nova 给值、`time_worked_s` 只有 Nova 报、act 抛错时 Nova 侧 `frames` 为空而 Midscene 侧仍在）——是引擎事实不是抽取失败，别把 `null` / 空数组读成「没导航 / 没跑 / 证据坏了」，判有没有记录看 `record_missing` / `evidence_missing`。（[0001](./0001-scope-limited-to-english-ui.md)、[0042](./0042-step-evidence-and-explain.md)）
3. **local 与 cloud、run 与 submit 的选法**：本机 `run` 是前台同步（退出码即判定）；`submit` 是无状态跑批（退 0 只表提交成功，判定看 `status --wait`）；`status` / `explain` 的 `--backend` / `--report-dir` / `--prefix` 须与 `submit` 时逐字一致，否则退 2 说未找到 run；cloud 档先 `doctor --prefix` 自检、部署是部署方的事、版本 skew 退 2 怎么办、variant 与 `--worker-variant`。**被测应用在本机时**：浏览器在云端、`localhost` 不可达，唯一跑法 = `--expose-local <feature 里书写的原始 origin>`（`run` 与 `submit` 都有），feature 照写原始地址；需 ngrok authtoken；本机须保持开机联网到 run 终态（这是「提交完关机也跑完」的唯一例外）；`--tunnel-ttl` 调小会在 run 未完时无条件拆隧道。
4. **工作循环**：`doctor` → `plan`（看派发标注与筛选结果）→ `run` / `submit` → 判定 → 失败先 `explain`（读原因、thought、截图 URI），需要更多再 `--json` 或 `jobs/*.json`，别解析 HTML 报告、别猜产物路径 → 精确检查改成确定性 step：写完先 `list-deterministic` / `plan` 自查，`steps/` 里任一文件加载失败会让 `plan` / `run` / `submit` 在起第一个 job 前整批拒跑退 2（错误点名文件与异常）——先修那个文件、不是怀疑 feature；同一 feature 要在两个引擎上跑时正则两侧成对、只写一侧则另一引擎上这一步悄悄换回 AI 判定且前置检查不替你发现（它只查本次用到的引擎），`list-deterministic --engine` 各查一遍 → 用 `--scope`（值 = `--json` / `jobs/*.json` 里的 `scope_id`，重跑失败 job 最直接）/ `--scenario` / `--tags` 收窄重跑；三个 flag 的组合语义与「筛空退 2 并列全部候选」照 [0041](./0041-agent-facing-cli-affordances.md) 决策一逐条写进 skill。
5. **机读读法**：`--json` 字段去 `references/cli-json-contract.md`；`message` 恒为「为何不是 passed」；`record_missing` 与 `evidence_missing` 的分工；`aborted_hint` 的含义。
6. **成本与超时旋钮，按「谁有这个 flag」分组**：共用（`run` + `submit`）= `--default-engine` / `--assertion-votes` / `--default-job-timeout` / `--max-concurrency` / `--steps-dir` / `--report-dir` / `--scope` `--tags` `--scenario`；仅 `run` = `--fail-fast` / `--json` / `--quiet` / `--no-report` / `--grace`（`submit` 无 `--json`，run_id 走 stdout，进度与判定看 `status --json`）；仅 `submit` = `--tunnel-ttl`。各管什么、什么时候动。
7. **退出码分流**：`run` 的退出码即判定（0 全通过 / 1 跑起来了但有失败或出错 / 2 没跑起来）；`status` **只有读到终态才表判定**（通过 0 / 其余终态 1），未达终态一律退 0、只表示「查到了」——要判定必须 `status --wait`（它同时是接力：后台推进卡住时由这条命令续到底），`status` 的 2 只表示查不到这个 run（cloud 档还含云端读不到、版本不匹配）；`submit` / `plan` / `explain` / `doctor` 只表做成没做成（0 / 2），`explain` 哪怕用例全红也退 0；CI 该接哪一条。（[0031](./0031-job-lifecycle-states-and-severity.md)）
8. **别做的事**（每条带为什么）：别把 `submit` 退 0 当通过；别把不带 `--wait` 的 `status` 退 0 当通过；别解析 HTML 报告或 SDK 原生 trajectory；别猜产物路径、顺 `ref` 走；cloud 改了 steps 不推镜像等于没改；别只写一侧的确定性 step；`--grace` 别调小（仅 `run`；云端 `submit` 的对应旋钮在部署侧 `gherkai deploy --stop-timeout`）。

`references/`：`cli-json-contract.md`（转换副本）；`engines.md`（两引擎的选择依据与语言限制、evidence 字段的引擎填充差异清单、确定性 step 写法入口与响亮失败读法、两侧正则的对称约定、各自 README 的 `blob/HEAD/` 绝对 URL）；`cloud.md`（部署方 / 使用方分工、`submit`–`status`–`explain --backend cloud` 一条线、skew 与 variant 的处置、`--expose-local` 例外）。是否需要 `scripts/`，由评测循环里「多个测试用例是否重复手写同一个 helper」决定（skill-creator 的判据），初版不带。

### 六、护栏：skill 是产品面，同受 0039 约束，且与 CLI 真值逐项对照

全部落在 `cli/tests/test_skill.py`（skill 文案是 markdown，`test_user_facing_messages.py` 的 `PY_ROOTS` 加一个无 `.py` 的目录会静默空扫，故不走那条路；`skill install` 自身的提示 / 错误是 Python 字面量，由它的现有扫描面自动覆盖）：

- **产品面文案**：按行扫 `cli/gherkai_cli/skills/gherkai/**/*.md`（含转换副本——转换后它本就不含内部指代，无例外）：禁词表与相对链接正则从 `cli/tests/test_package_readmes.py` 抽成共享常量模块、两处同源（禁词用更严的 `\bADR\b`）；**链接形态**：不得出现 `](../…)` / `](./…)` / `](foo.md)` 这类仓库相对链接（安装态是拷贝，必死），跨文件只许指 `references/` 内的同级文件或绝对 URL；`github.com/zhiyanliu/gherkai` URL 只允许 `blob/HEAD/` / `tree/HEAD/` / `tree/v…/` 形态。扫描面为空即红（目录搬家 / 后缀写错不能静默通过）。
- **命令面真值，成对比对**：从 skill 文本抽 `(子命令, flag)` 组合，对照该子命令 subparser 的 `_actions`（递归遍历主 parser 的 `_actions` 与 `_SubParsersAction.choices`，走 argparse 私有 API——先例 = `deploy_aws/tests/test_provider.py` 的全集护栏），flag 挂错子命令即红；反引号 JSON 键对照契约页。`gherkai deploy …` 那批 token 归 provider 侧：放 `deploy_aws/tests/`、用 `Provider().add_arguments(parser)` 建真 parser 比对（皮的 parser 里 provider=None 时它们不存在），`cli/tests` 对 deploy 段显式跳过、不 import provider（免把 jsii / node 的 import 代价拖进皮的单测）。
- **转换副本**：`transform(docs/guides/cli-json-contract.md) == references/cli-json-contract.md`，且转换用到的禁词映射表命中未登记词即红。
- **目录白名单**：`cli/gherkai_cli/skills/gherkai/` 下只允许 `SKILL.md`、`references/`、（按需）`scripts/`、`assets/`，其它文件 / 目录即红（挡评测资产悄悄长回来）；构出的 wheel 内含 `gherkai_cli/skills/gherkai/**` 且不含 `evals`（发布链 `check_dist_metadata.py` 同侧加一项）。
- **形态**（规范硬约束的本地复刻，不引外部校验器）：`name` 匹配 `^[a-z0-9]+(-[a-z0-9]+)*$`、1–64 字符、**等于目录名**（安装目标目录名由它派生）；`description` 非空且 ≤ 1024 字符（description 优化循环天然把它写长，这条是刹车）；正文 ≤ 500 行**且** ≤ 12000 字符（行数管结构、字符数管上下文成本；超了往 `references/` 挪，不压行）；不做 frontmatter 字段白名单（各宿主有合法扩展键）。
- **不复述可调数字**：超时、grace、票数默认值一律「见 `--help`」，与 guides 同律。

### 七、评测与迭代：按 skill-creator 循环，缺省集零条真 AWS，舞台在仓库外

- **资产位置**：`skills/gherkai-evals/{evals.json, fixtures/}` 入库（skill 目录的兄弟位，skill-creator 的脚本按路径参数取 eval-set、不要求在 skill 目录内）；结果工作区 `skills/gherkai-workspace/` gitignore。`.gitignore` 的派生品规则（`**/reports/`、`*.log`、`screenshots/`、`*.report.html`）会静默吞掉 fixture 里真跑产出的文件，且是**部分**吞（Nova 的 evidence 截图不在规则内）——比全缺更难发现：在这些规则之后为 `skills/gherkai-evals/fixtures/**` 开反白名单，**紧随其后重新收紧密钥规则**（`.env`、`*.pem`、`*.key`、`credentials`）；护栏断言 `evals.json` 引用到的每个 fixture 路径都被 `git ls-files` 跟踪。
- **fixture 可搬迁契约**：入库 fixture 里不得出现产出机器的绝对路径。取**物化式**：`jobs/*.json` / `evidence.json` 里的本机指针存成占位符 `file://{{FIXTURE_ROOT}}/…`，评测前由小脚本替换成舞台目录的绝对路径；截图裁成极小占位字节。断言级护栏：物化后 `explain --json` 里每个展开 step 的 `evidence_missing` 必须为 null，否则评测本身算失败——证据读失败被吞成 `evidence_missing`、`explain` 恒退 0 是既定取舍，没这条断言，fixture 坏掉的表现就是「全绿但两臂都看不到 thought / 截图」。
- **隔离面**：**舞台**（被测项目）与**工作区**（结果）分开。物化脚本把 `fixtures/<case>` 拷到仓库外一次性目录（如 `$TMPDIR/gherkai-eval-<id>/`）当「使用方项目」，subagent 提示里只给这个目录、不给任何仓库路径；两臂都以独立进程 `claude -p` 跑、cwd = 舞台（进程内 subagent 只是提示级隔离：仍继承父会话 cwd、能读仓库、吃项目 `CLAUDE.md`），with-skill 臂只多给包内 skill 路径，保证两臂唯一变量是 skill。前置断言：舞台及其上溯路径与用户级目录下没有已装的 `gherkai` skill，命中即拒跑（dogfood 安装态与评测互斥，跑评测前移走）。两臂共用同一条 CLI 调用方式（`uv run --project <repo> gherkai …` 或舞台 `bin/` 里的 shim 前置 PATH），清掉 `AWS_PROFILE` / `AWS_REGION` 让本机段结论确定；fixture 的确定性 step 一律 novaact（随 `gherkai[local]` 进同一 venv；midscene 要 npm 全局包、缺失即退 2）。
- **缺省集零条真 AWS**：每条任务只靠 fixture + `plan` / `explain` / `doctor`（不给 `--prefix`、不给 `--backend cloud`，云端项按设计标「未查」）/ `list-deterministic` 完成，断言只读 fixture 与本机命令输出。云端任务单列进 **opt-in 集**（`evals.json` 显式标记、缺省跳过）——「提交到云端并等结果」必然发真 AWS 调用。
- **提示写法两条硬约束**：① 每条提示嵌 fixture 里的具体坐标（feature 文件名、失败 scenario 的 step 原文、run 目录名）加一句背景，写成使用者真会打出的话，不写「把这条断言改成精确检查」这类抽象句式——抽象提示测不出触发也测不出执行；② 一步就能答完的提问不作为 eval——agent 只在任务自己搞不定时才去查 skill，这类提示两臂双双不消费 skill、delta 是假零。若某条 eval 的两臂均未消费 skill，判为无效样本、重写后再跑、不计入通过率。
- **可核断言**（例）：用了 `plan` 再 `run`；失败后调 `explain` 而非读 HTML；用 `--json` 取字段而非正则 stdout；对 `submit` 与非终态 `status` 退 0 的解读正确；改确定性 step 写在 `steps/` 并对两个引擎各 `list-deterministic --engine` 查一遍。
- **description 优化**：20 条应触发 / 不应触发查询（近似误触发为主）跑 skill-creator 的 `run_loop.py`（`claude -p`，`--model` 传本会话模型），取 held-out 最优；产物入库前过决策六的 ≤ 1024 字符护栏。首轮结果（with-skill 对 baseline 的断言通过率、人审反馈、触发命中率 train / held-out）内联进「验证」节后翻 Accepted。

## 被拒方案

- **单独 `gherkai-skill` repo**：多一条发行轨，skill 与 CLI 版本必漂，护栏无法跨仓对照真值。
- **仓库根 `skills/gherkai/` 作真身、hatch force-include 打进 wheel**：跨根 force-include 在 `uv build` 的 sdist→wheel 链下硬失败；只写 sdist target 又让 `uv build --wheel` 与 editable 树静默无 skill。
- **仓库根放一份生成镜像换 `npx skills add owner/repo --skill gherkai` 短命令**：git 里多一棵镜像树、多一条相等性护栏，换来的只是省一段 URL；直指路径形态官方支持、且能钉 tag。skills.sh 一类目录若将来成为真实需求再议（见「不做 / 延后」）。
- **Claude plugin marketplace 作为主发行面**：只覆盖 Claude、需 `.claude-plugin/marketplace.json` 一套仪式；Agent Skills 标准已让一份 SKILL.md 通吃。
- **AGENTS.md 里放一份 Codex 版内容**：双源必漂；Codex 原生读 SKILL.md，AGENTS.md 只该有一行指针。
- **skill 用相对链接 / GitHub URL 指 docs**：安装态是拷贝、相对路径断；URL 要联网且指向默认分支、可能比装的 CLI 新。
- **契约页副本 = 字节拷贝**：会把 ADR 指代、禁词表里的内部机制名、三条指向姊妹 guide 的死相对链接原样发到使用方项目——正是决策四自己给出的「不能 link」的理由；改确定性转换。
- **手工维护 references 副本**：无护栏的重复迟早漂。
- **评测放 skill 目录内（skill-creator 默认布局）**：两条安装腿都会把 fixtures 推给使用方、打进 wheel；hatch 的 exclude 对 force-include 无效、`npx skills` 无任何排除钩子。
- **在仓库内跑评测**：baseline 会读到 skill 想替代的全部原始教材（README、cli/README、六篇 guides、ADR，还有自动注入的 `CLAUDE.md`），dogfood 装的 `.claude/skills/gherkai` 还会自动进 baseline 的技能列表，两头都把 delta 变成无意义数字；真实使用方项目只有 `--help`。
- **在 skill 里教 SDK 原生产物格式**：0042 已用 evidence + `explain` 取代。
- **把 README 整份塞进 skill**：README 是给人的操作手册，agent 要的是操作模型与决策规则。
- **`.codex/skills` 作 Codex 落点**：官方从未列出、挂在项目配置层要走信任流程；标准位是 `.agents/skills`。
- **安装命令用文件清单做幂等覆盖**：清单是为「与用户自有文件共存」设的复杂度，skill 目录是独占命名空间，整目录收敛更简单且跨版本收敛。

## 不做 / 延后

- `doctor` 加一项「已装 skill 的版本是否等于 CLI」（读 `.gherkai-skill-version`；「版本未知」态跳过比对；dev 树里该值是 `uv sync` 时的快照、只对发行版安装有判定意义）：等安装命令真用起来再定形态。
- `skill uninstall`：目前 `rm -rf` 即可；评测前置需要它时再加。
- `scripts/`：等评测显示测试用例反复手写同一 helper 再收进来。
- 仓库根镜像 / 发布到 skills.sh 一类目录：等使用方需求。
- 引擎专属 skill 拆分（`gherkai-novaact` / `gherkai-midscene`）：evidence **schema** 同形、引擎差异有界且一页 reference 列得完，不拆。

## 影响面

**code**

- 新目录 `cli/gherkai_cli/skills/gherkai/`（`SKILL.md`、`references/{cli-json-contract.md, engines.md, cloud.md}`）；`skills/gherkai-evals/{evals.json, fixtures/, materialize.py}`；`tools/render_skill_contract.py`（契约页 → 副本的确定性转换，含禁词映射表）；`.gitignore` 加 `skills/*-workspace/` 与 fixture 反白名单 + 密钥收紧行。
- `cli/gherkai_cli/__main__.py`：`skill install` 子命令（嵌套 subparser、子动词必填）；新模块 `cli/gherkai_cli/skill_install.py`（`importlib.resources` 定位、整目录收敛、标记文件、`--print`）。`cli/pyproject.toml` 不需要 force-include。
- 测试：`cli/tests/test_skill.py`（产品面文案与链接形态、命令面成对真值、转换副本相等、目录白名单、形态四条、安装命令行为含跨版本收敛、fixture 路径受 git 跟踪）；`deploy_aws/tests/` 加 provider 侧 token 对照；禁词 / 相对链接常量从 `cli/tests/test_package_readmes.py` 抽成共享模块；`check_dist_metadata.py` 加 wheel 内含 skill 且不含 evals 的检查。

**文档（反向链逐处列出，Accepted 前逐条核）**

- [0041](./0041-agent-facing-cli-affordances.md)：决策五「skill 只链接它，不复制字段表」改为「唯一手写源仍在 docs、不进发行包；skill 带一份确定性转换的副本随 CLI 发行（为何不能 link、转换与护栏见 0043 决策四）」；「影响」节那条前向指代改为指向 0043 决策五、删掉工作循环的复述；Status 头在本 ADR 翻 Accepted 时改 `Partially-superseded-by 0043`，限定范围 = 决策五该子句被反转、其余五项不变。
- [0037](./0037-distribution-and-packaging.md)（扩展、Status 不动）：「决策总览」CLI 行注「含随 wheel 带的 `skills/gherkai` 包数据（0043）」；「工程布局」树补 `cli/gherkai_cli/skills/` 与根 `skills/gherkai-evals/`（不分发）。
- [0039](./0039-user-facing-surfaces-no-internal-references.md)（扩展、Status 不动）：面二四层表加第五行（`cli/gherkai_cli/skills/gherkai/**`；去向 = 随 CLI wheel 发行、由 `skill install` 拷进使用方项目 / agent 目录；链接只用绝对 URL），正文「四层」改「五层」；「护栏」节补 `cli/tests/test_skill.py` 这只 markdown 扫描器。
- [0001](./0001-scope-limited-to-english-ui.md)（扩展、Status 不动）：「影响」节承载语言口径的面加 skill 的 `references/engines.md`。
- `CLAUDE.md`：代码纪律「产品面文案不带内部指代」的条件加「以及随发行包发到使用方项目的 markdown（agent skill）」；文档纪律「README / DEVELOPMENT 分层」的使用者向枚举加「随包发行的 skill 内容」，两处指本 ADR。
- `docs/REFERENCES.md` 新开「Agent Skills」节：规范（frontmatter 字段与上限）、vercel-labs `skills` CLI README（容器目录与直指路径）、Codex skills 文档（`.agents/skills` 位）、skill-creator 位置。
- 根 `README.md` 加「让 AI agent 驾驭」一节（两条安装路径、次选路径不钉 tag 时的版本代价与钉 tag 模板）；`cli/README.md` 加 `skill install` 行；`docs/guides/cli-json-contract.md` 头部加 skill 指引与「有转换副本随 CLI 发行」；`docs/guides/README.md` 末句 skill 指向本目录；`DEVELOPMENT.md` 目录树与 ADR 范围；`CONTEXT.md` 术语加 skill。

## 验证（Accepted 前必做，结论内联到此处）

- 护栏全绿：产品面文案与链接形态、命令面成对真值、转换副本相等、目录白名单、形态四条、fixture 受 git 跟踪。
- 打包：`uv build --all-packages` 全绿且 wheel 内含 `gherkai_cli/skills/gherkai/**`、不含 `evals`；editable 树上 `gherkai skill install --print` 输出与包内文件一致。
- `skill install` dogfood：`--agent all` 装进本仓库后 `git status` 干净；重复安装与「模拟上一版多出一个 reference 后再装」都收敛到与包内逐字节相等；对非本命令所装的目录退 2。
- 手工核一次 `skills-ref validate`（规范校验器），确认本地复刻的形态检查同口径；不进 pytest。
- skill-creator 循环首轮：每条 eval 的 with-skill 对 baseline 断言通过率与人审反馈；无效样本（两臂均未消费 skill）的处理记录；description 优化前后的触发命中率（train / held-out）。
- `npx skills add https://github.com/zhiyanliu/gherkai/tree/<tag>/cli/gherkai_cli/skills/gherkai` 在一台干净目录里装一次、目录布局符合预期；在装了 skill 的干净项目里试一次隐式触发。
