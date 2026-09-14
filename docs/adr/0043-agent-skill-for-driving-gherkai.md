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

1. **`gherkai skill install [--agent claude-code|codex|all] [--dir <项目根>|--global] [--print]`**：从包内拷到目标目录。`--agent` 缺省 `claude-code`（→ `.claude/skills/gherkai/`）；`codex` → `.agents/skills/gherkai/`（`--global` 时分别 `~/.claude/skills/` / `~/.agents/skills/`）；`--print` 把 SKILL.md 打到 stdout 供管道。**语义是整目录收敛、不是幂等覆盖**：先删目标 skill 目录、整份写入包内那份、再写 `.gherkai-skill-version` 标记；**装完目录 = 包内那份 + 该标记**（标记只存在于安装态、包内不得有，决策六白名单据此不列它），跨版本升级不留旧 reference；删前只认「含 `.gherkai-skill-version` 标记、或本就为空 / 不存在」的目录，否则退 2 报「这个目录不像是本命令装的，先自己挪走」（防 `--dir` 打错整掉用户目录）。标记值 = 已安装发行版本（[0037](./0037-distribution-and-packaging.md) 决策 7 的同一取法）；源码直跑取不到 → 标记记「版本未知」、安装照常完成（不拒装，与 0037「取不到就跳过比较」的分叉一致；禁止把 `--version` 显示用的占位串写进标记）。结束**问一次**要不要把「驾驭 gherkai 用 skill `gherkai`」那一行追加进使用方的 `AGENTS.md` / `CLAUDE.md`（yes 即追加、幂等不重复；非交互用 `--pointer yes|no`，缺省 no 只打印那一行）。退出码 0 / 2。parser 形态：`skill` 用普通嵌套 subparser、子动词 `required=True`（裸 `gherkai skill` 由 argparse 报错退 2）；不套 `deploy` 的 `set_defaults` 间接层——那是为 provider 中立设的，`skill` 无 provider。**推荐它的理由**：离线可用、版本自动对齐（不用人手抄版本号、不会钉错）——装的 skill 永远等于装的 CLI 版本。
2. **`npx skills add https://github.com/zhiyanliu/gherkai/tree/<ref>/cli/gherkai_cli/skills/gherkai`**（`--agent claude-code|codex`）：给不想多敲一条 gherkai 命令的人。skill 不在 `npx skills` 的默认容器目录里，故用官方支持的直指路径形态；`<ref>` = `HEAD` 拿默认分支最新（可能比装的 CLI 新），= `v<版本>` 即钉到 CLI 版本（tag 名 = `v` + `gherkai --version`）。三条代价写进 README：不钉 tag 时可能比 CLI 新；Codex 用户级落点与本命令分叉（`npx` 写 `~/.codex/skills/`，本命令写 `~/.agents/skills/`）；`npx` 装出的目录没有版本标记，之后改用 `gherkai skill install` 会按自护判据退 2、要人先挪走（防误删的有意后果）。

Claude 的 plugin marketplace 只覆盖 Claude、仪式更多，现阶段不做（见被拒方案）；将来要做也是在这份 SKILL.md 外面包一层。

### 四、skill 与 docs 的关系：不 link、确定性转换出副本；正文是新内容不是复述

**本条反转 [0041](./0041-agent-facing-cli-affordances.md) 决策五「skill 只链接契约页、不复制字段表」**——手写源仍是唯一事实源，反转的只是「复制即第二事实源」这一判断：有生成器与护栏的副本不是第二事实源。

- **为什么不能 link**：skill 的消费现场是使用方项目里的一份拷贝，`../../docs/...` 相对链接指向的目录不存在；GitHub 绝对 URL 要联网，且指向默认分支上的 docs、可能比使用方装的 CLI 新。Agent Skills 的做法就是 skill 目录自带 `references/`。
- **副本 = 确定性转换，不是 `cp`**：`docs/guides/cli-json-contract.md` 是唯一**手写**源；`references/cli-json-contract.md` 由入库的生成器渲染，转换规则是稳定契约、逐条列举：① 剥掉头部「定位 / 权威在 code / 护栏」引用块与姊妹页导航段，换成一句产品语言（「本页讲 `--json` 各命令输出有哪些字段、什么意思、何时出现」）；② 正文里指向仓库内文件的指针改成 `gherkai <子命令> --help` 或 `https://github.com/zhiyanliu/gherkai/blob/HEAD/<path>` 绝对 URL；③ 禁词按一张入库的显式映射表改写（如「定位链」→ 产品语言），命中未登记禁词即红。护栏断言 `transform(源) == 入库副本`——仍是「改了源没同步就红」，也仍然否掉「手工维护副本」。契约页的键覆盖护栏继续只对源页断言。契约页头部加一句「驾驭本工具的 AI agent 请装 skill；本页有转换副本随 CLI 发行」。
- **`SKILL.md` 正文**是给 agent 的新文档（操作模型），docs 里没有等价物、不算重复；它与 README 有事实重叠（flag 名、退出码），读者不同写法不同，漂移由护栏挡。guides 给人、skill 给 agent，同一机制两边各有一份是**按读者分层**，不是双源。
- GitHub 上 docs 的绝对 URL 可留作**次级**指针，形态按 [0039](./0039-user-facing-surfaces-no-internal-references.md) 面二的发行物约定用 `blob/HEAD/`（不绑分支名 / tag）；版本一致性靠「装的 skill == 装的 CLI」（决策三）保证，不靠 URL 钉版本——也正因 `HEAD` 的 docs 可能比装的 CLI 新，它只能作次级指针。

### 五、内容重心：一个 skill 入口、三个任务域、按域拆 references；正文是 agent 的操作模型，不是复述 `--help`

**三个任务域，一个入口**。使用方与 gherkai 打交道有三类事：**A 用它做测试**（QA / 测试开发：写 feature 与 steps、`plan`、`run` / `submit`、`status`、`explain`、收窄重跑、汇报——高频，skill 存在的理由）；**B 环境就位与排障**（同一批人卡住时：装 CLI 与引擎 worker、`doctor`、`list-engines` 与 worker 定位、AWS 凭证 / region、ngrok、版本 skew 怎么办——低频但阻塞，与 A 是连续体）；**C 云端后端交付**（部署方 / 维护者：`deploy` 交人、基底同步、variant 镜像 build + `push-worker`、`list-workers`、升级顺序、多环境 prefix、清理——另一种角色，IAM 相关由人执行、agent 辅助）。另有横切的**机读消费**（CI 接退出码与 `--json`、取产物），是 A / B 共用的读法、归契约副本。A 与 C 有一条真实交接：本机写好的确定性 step 要进云端必须 `push-worker`，skill 要把这条线画出来。**做成一个 skill、按域拆 references**（skill-creator 的多域组织形状：`SKILL.md` = 共享心智模型 + 路由 + 最高频的 A 工作流，`references/<域>.md` 各一份、agent 只读相关的）：三域共享同一套词汇与版本、一条 description；A → B → C 是连续体，一个 run 因 skew 退 2 时 agent 要无缝走到 C 的知识，拆开反而要它自判切哪个；两档触发面已覆盖 C（部署方项目无 `.feature`、但显式提 gherkai）。**拆成多个 skill 的重议闸门**（可测）：`description` 装不下三域的触发语境（1024 字符硬上限），或正文超形态上限（决策六），或评测显示跨域误路由。

**定位**：skill 教 agent 替使用者把整条工作跑通——从需求与被测应用的信息**写出** feature 与必要的 steps 代码，到本机 / cloud 两档的执行、判定、排障与收窄重跑；不是只给建议。**触发面**（写进 `description`）：项目里有 `.feature` 且 gherkai 在场（装了 CLI / 有 gherkai 式 `steps/` / 文档提到）→ 提到测试意图即触发；没有 `.feature` → 只在显式提到 gherkai 时触发；纯 Cucumber / Playwright 项目（有它们自己的 step definitions 或配置）不接管——触发查询集的负例按这类 near-miss 出。**语言**：正文中文（与 CLI 输出、README 同侧），`description` 末尾加一行英文触发词，防英文提示下漏触发。skill 名 `gherkai`（= 目录名）。

`SKILL.md` 正文（形态上限见决策六）按这个骨架写，具体措辞由 skill-creator 循环迭代；正文不出现 ADR 编号与内部机制名（决策六），下面括注的 ADR 只是本文的权威指针：

1. **心智模型**：feature 里的 step 有两种跑法——默认 AI（自然语言、Nova / Midscene 执行）与确定性 step（测试开发注册的精确代码，命中即走代码）；两者边界（精确检查、可复现、要快 → 确定性；模糊 / 一次性 / 页面变化多 → AI）；scope / tag 语义（`@scope` = 一条会话一个 job，`@engine`、`@timeout`，普通 tag 归 `--tags`）。
2. **引擎怎么选**：Midscene 对被测 UI 语言不限；Nova Act 的支持范围是英文 UI——非英文页上导航与页面级语义断言可用，但「正文里是否出现某个词」这类断言会稳定判否（系统性、投票治不了）。诊断规则：Nova 档下非英文页面的断言判否先排查引擎语言面、别先当被测应用的 bug；三条出路 = `@engine:midscene` 路由 / 断言改写成页面级语义陈述 / 文本与结构检查改成确定性 step。`--default-engine` 与 `@engine` tag；`list-engines` 看本机装了什么。evidence 的 **schema** 两引擎同形（读法一套、`explain` 通吃），但**填充**有系统性引擎差（frame 级 `url` 只有 Nova 给值、`time_worked_s` 只有 Nova 报、act 抛错时 Nova 侧 `frames` 为空而 Midscene 侧仍在）——是引擎事实不是抽取失败，别把 `null` / 空数组读成「没导航 / 没跑 / 证据坏了」，判有没有记录看 `record_missing` / `evidence_missing`。（[0001](./0001-scope-limited-to-english-ui.md)、[0042](./0042-step-evidence-and-explain.md)）
3. **local 与 cloud、run 与 submit 的选法**：本机 `run` 是前台同步（退出码即判定）；`submit` 是无状态跑批（退 0 只表提交成功，判定看 `status --wait`）；cloud 链 = `doctor --prefix` → `plan` → `submit` → `status --wait` → `explain --backend cloud`——`plan` 不依赖后端、两档都先跑，但它的确定性标注问的是**本机** steps，云端真跑用的是 variant 镜像里那份，标注只代表本机视图（改了 steps 要 `push-worker`）；`status` / `explain` 的 `--backend` / `--report-dir` / `--prefix` 须与 `submit` 时逐字一致，否则退 2 说未找到 run；cloud 档先 `doctor --prefix` 自检；**部署云端后端（`gherkai deploy`）是部署方的事、agent 不自己跑**（改 AWS 资源与 IAM，本项目一直由人执行）——skill 教 agent 用 `doctor` 判「缺什么」、把该跑的命令与前置交给人；`push-worker`（推定制 variant 镜像，不改 IAM）agent 可以跑；版本 skew 退 2 怎么办、variant 与 `--worker-variant`。**被测应用在本机时**：浏览器在云端、`localhost` 不可达，唯一跑法 = `--expose-local <feature 里书写的原始 origin>`（`run` / `submit` / `plan` 三处都收；`plan` 只在输出里标注该 origin 将在真跑时经隧道替换、自己不起隧道），feature 照写原始地址；需 ngrok authtoken；本机须保持开机联网到 run 终态（这是「提交完关机也跑完」的唯一例外）；`--tunnel-ttl` 调小会在 run 未完时无条件拆隧道。
4. **编写 feature 与 steps**（从需求与应用信息生成，不只修改）：怎么写对本工具友好的 Gherkin——`Given` 引号内 URL 走导航步、AI 步写成页面级语义陈述而非词匹配、一条 scenario 多大合适、UI 语言与引擎的关系（骨架 2）、`@scope` / `@engine` / `@timeout` 的用法与何时该分 scope；什么时候该配确定性 step（精确检查、可复现、要快）、两引擎的最小模板与元数据（`description` / `example` 必填）、写完用 `plan` 看标注与 `list-deterministic` 核对；从被测应用的代码 / 文档 / 页面取信息时优先取稳定的语义（标题、可见文案、流程结果）而非实现细节。
5. **工作循环**：`doctor` → `plan`（看派发标注与筛选结果）→ `run` / `submit` → 判定 → 失败先 `explain`（读原因、thought、截图 URI），需要更多再 `--json` 或 `jobs/*.json`，别解析 HTML 报告、别猜产物路径 → 精确检查改成确定性 step：写完先 `list-deterministic` / `plan` 自查，`steps/` 里任一文件加载失败会让 `plan` / `run` / `submit` 在起第一个 job 前整批拒跑退 2（错误点名文件与异常）——先修那个文件、不是怀疑 feature；同一 feature 要在两个引擎上跑时正则两侧成对、只写一侧则另一引擎上这一步悄悄换回 AI 判定且前置检查不替你发现（它只查本次用到的引擎），`list-deterministic --engine` 各查一遍 → 用 `--scope`（值 = `--json` / `jobs/*.json` 里的 `scope_id`，重跑失败 job 最直接）/ `--scenario` / `--tags` 收窄重跑；三个 flag 的组合语义与「筛空退 2 并列全部候选」照 [0041](./0041-agent-facing-cli-affordances.md) 决策一逐条写进 skill。
6. **机读读法**：`--json` 字段去 `references/cli-json-contract.md`；`message` 恒为「为何不是 passed」；`record_missing` 与 `evidence_missing` 的分工；`aborted_hint` 的含义。
7. **成本与超时旋钮，按「谁有这个 flag」分组**：共用（`run` + `submit`）= `--default-engine` / `--assertion-votes` / `--default-job-timeout` / `--max-concurrency` / `--steps-dir` / `--report-dir` / `--scope` `--tags` `--scenario`；仅 `run` = `--fail-fast` / `--quiet` / `--no-report` / `--grace`；仅 `submit` = `--tunnel-ttl`；`--json` 另说：`run` 有、`submit` 没有（run_id 走 stdout，进度与判定看 `status --json`），查询类命令各自有（骨架 5）。各管什么、什么时候动。
8. **退出码分流**：`run` 的退出码即判定（0 全通过 / 1 跑起来了但有失败或出错 / 2 没跑起来）；`status` **只有读到终态才表判定**（通过 0 / 其余终态 1），未达终态一律退 0、只表示「查到了」——要判定必须 `status --wait`（它同时是接力：后台推进卡住时由这条命令续到底），`status` 的 2 只表示查不到这个 run（cloud 档还含云端读不到、版本不匹配）；`submit` / `plan` / `explain` / `doctor` 只表做成没做成（0 / 2），`explain` 哪怕用例全红也退 0；CI 该接哪一条。（[0031](./0031-job-lifecycle-states-and-severity.md)）
9. **失败汇报模板**：agent 向人汇报时按固定小结构——哪步（scenario / step 文本）、判定与原因（`message`）、模型看见了什么（thought 一句 + 截图地址）、建议动作（改断言写法 / 改确定性 step / 换引擎 / 被测应用的问题），让人一眼能定夺。
10. **别做的事**（每条带为什么）：别把 `submit` 退 0 当通过；别把不带 `--wait` 的 `status` 退 0 当通过；别解析 HTML 报告或 SDK 原生 trajectory；别猜产物路径、顺 `ref` 走；cloud 改了 steps 不推镜像等于没改；别只写一侧的确定性 step；`--grace` 别调小（仅 `run`；云端 `submit` 的对应旋钮在部署侧 `gherkai deploy --stop-timeout`）。

`references/`（按域）：`cli-json-contract.md`（转换副本，机读消费）；`engines.md`（两引擎的选择依据与语言限制、evidence 字段的引擎填充差异清单、确定性 step 的**最小模板**（Nova = Python、Midscene = TS，含 `description` / `example` 元数据，离线也能写）与响亮失败读法、两侧正则的对称约定、完整写法指向各自 README 的 `blob/HEAD/` 绝对 URL）；`setup-and-diagnosis.md`（域 B：安装 CLI 与引擎 worker 的几条路、`doctor` 各段怎么读、`list-engines` 与 worker 定位、凭证 / region、ngrok 前置、skew 退 2 的处置）；`cloud-backend.md`（域 C：部署方 / 使用方分工、`deploy` 交人与前置清单、`submit`–`status`–`explain --backend cloud` 一条线、variant 与 `push-worker`、`list-workers`、升级传播顺序、多环境 prefix、A→C 的交接、`--expose-local` 例外）。正文里 A 的工作流内联，B / C 只留路由句与指针。是否需要 `scripts/`，由评测循环里「多个测试用例是否重复手写同一个 helper」决定（skill-creator 的判据），初版不带。

### 六、护栏：skill 是产品面，同受 0039 约束，且与 CLI 真值逐项对照

全部落在 `cli/tests/test_skill.py`（skill 文案是 markdown，`test_user_facing_messages.py` 的 `PY_ROOTS` 加一个无 `.py` 的目录会静默空扫，故不走那条路；`skill install` 自身的提示 / 错误是 Python 字面量，由它的现有扫描面自动覆盖）：

- **产品面文案与指针形态**：按行扫 `cli/gherkai_cli/skills/gherkai/**/*.md`（含转换副本——转换后它本就不含内部指代，无例外）：禁词表与相对链接正则从 `cli/tests/test_package_readmes.py` 抽成共享常量模块、两处同源（禁词用更严的 `\bADR\b`）。**跨文件指针一律写反引号裸路径**（`references/engines.md`，随 skill-creator 惯例；agent 读的是路径不是超链接）；markdown 相对链接一律禁——`](../…)` / `](./…)` / `](foo.md)` / `](references/foo.md)` 全红：出 skill 的相对链接在安装态必死，skill 内的虽活但统一禁掉才能与 `test_package_readmes.py` 共享同一份正则；markdown 链接只用绝对 URL，`github.com/zhiyanliu/gherkai` 只允许 `blob/HEAD/` / `tree/HEAD/` / `tree/v…/` 形态。扫描面为空即红（目录搬家 / 后缀写错不能静默通过）。
- **命令面真值，成对比对**：只认 `gherkai <子命令> …` 与 `--flag` 出现在**同一个反引号代码跨**内的组合，对照该子命令 subparser 的 `_actions`（递归遍历主 parser 的 `_actions` 与 `_SubParsersAction.choices`，走 argparse 私有 API——先例 = `deploy_aws/tests/test_provider.py` 的全集护栏），flag 挂错子命令即红；散落的裸 `--flag` 只做「存在于全集」的弱断言。**排他性反向断言**：skill 里「仅 <子命令>」形态段落列出的 flag 必须在真值集里只属该子命令（`(run, --json)` 存在、成对比对必绿，排他错误对它是隐形的）。`deploy` / `destroy` 段**按 flag 来源分刀**：皮自己声明的中立 flag（`--provider` / `--diff` / `--synth-only` / `--bootstrap` / `--require-approval` / `--allow-vpc-change`）在 provider 未加载时也在主 parser 上，仍在 `cli/tests` 比对；provider 贴的旋钮与子动词（`--prefix` / `--vpc` / `--stop-timeout` / `--region` / `--profile`、`push-worker` / `list-workers`）在 provider=None 时不存在，放 `deploy_aws/tests/`，parser 按真实接线顺序建：`prog` 末段为 `deploy` 或 `destroy`（provider 按 prog 末段决定贴什么）+ 先贴皮的中立 flag + `Provider().add_arguments(parser)`（同 `deploy_aws/tests/test_provider.py::_parse`）；`cli/tests` 对这批显式跳过、不 import provider——provider 住 `[deploy-aws]` optional extra、只有部署方装（[0037](./0037-distribution-and-packaging.md) 决策 6），皮的测试不该强依赖它。
- **JSON 键对照**：参与比对的 token = 匹配 `^[a-z][a-z0-9_]*$` 且不含 `-` `/` `.` `@` 的反引号 token，减去一张入库豁免表（引擎名、状态值、目录名等；命中未登记的非键即红，逼人显式登记）；真值集取契约页字段表首列的键或复用渲染器真键集，不取契约页全页反引号超集（它有意混入 flag 与路径）。
- **转换副本**：`transform(docs/guides/cli-json-contract.md) == references/cli-json-contract.md`，且转换用到的禁词映射表命中未登记词即红。
- **目录白名单与 wheel 内容**：`cli/gherkai_cli/skills/gherkai/` 下只允许 `SKILL.md`、`references/`、（按需）`scripts/`，其它文件 / 目录即红（挡评测资产悄悄长回来；`.gherkai-skill-version` 是安装态产物、不在此列）。**wheel 内 `gherkai_cli/skills/gherkai/` 的文件集逐条等于源目录的文件集**（源侧按文件系统遍历取、排除 `__pycache__/` 与 `*.pyc`，不用 `git ls-files`），落在 `.github/scripts/check_dist_metadata.py`（CI 打包 smoke 与发布 gate 共用同一份）。理由：hatchling 默认认从项目根向上找到的第一份 `.gitignore`（即 `cli/.gitignore`，今含 `reports/`），命中的路径静默不进 sdist / wheel，`git add -f` 强跟踪也救不回来——「文件受 git 跟踪」式护栏对这一格无效，只有集合相等能抓。
- **形态**（规范硬约束的本地复刻，不引外部校验器）：`name` 匹配 `^[a-z0-9]+(-[a-z0-9]+)*$`、1–64 字符、**等于目录名**（安装目标目录名由它派生）；`description` 非空且 ≤ 1024 字符（description 优化循环天然把它写长，这条是刹车）；正文 ≤ 500 行**且** ≤ 12000 字符（行数管结构、字符数管上下文成本；超了往 `references/` 挪，不压行）；不做 frontmatter 字段白名单（各宿主有合法扩展键）。
- **不复述可调数字**：超时、grace、票数默认值一律「见 `--help`」，与 guides 同律。

### 七、评测与迭代：按 skill-creator 循环，缺省集零条真 AWS，舞台在仓库外

- **谁的东西**：评测是 **contributor 侧的开发期资产**——skill-creator 循环是我们迭代 SKILL.md 质量的手段；不随 skill 发行、使用方接触不到也不会跑；opt-in 的云端评测由维护者在自己的部署上按需跑。
- **资产位置**：仓库根 `skills/gherkai-evals/{evals.json, trigger-eval.json, fixtures/, materialize.py}` 入库（刻意在 CLI 包的发行树之外，隔离理由见决策一）。**位置有意偏离 skill-creator 默认布局**（它把行为评测放 skill 目录内 `evals/evals.json`、`files` 相对 skill 根）：`evals.json` 由 agent 按 skill-creator 的 schema 消费、没有脚本读它，位置无技术约束，本 ADR 里其 fixture 路径相对 `skills/gherkai-evals/`；`trigger-eval.json` 是 description 优化的触发查询集（20 条应触发 / 不应触发，near-miss 负例是有成本的人工资产，故入库），由 `run_loop.py --eval-set <path>` 按路径取。结果工作区 `skills/gherkai-workspace/` gitignore。
- **`.gitignore`**：派生品段（见 `.gitignore` 该段，`**/reports/`、`*.log`、`screenshots/`、`*.report.html` 等）会静默吞掉 fixture 里真跑产出的文件，且是**部分**吞（Nova 的 evidence 截图不在规则内）——比全缺更难发现。在派生品段之后为 `skills/gherkai-evals/fixtures/**` 开反白名单，**紧随其后把反白名单之前的密钥规则全部重列**（当前 = `.env`、`.env.*`、`!.env.example`、`*.pem`、`*.key`、`.aws/`、`credentials`——含那条放行示例文件的反规则，否则 fixture 里的 `.env.example` 会被新加的 `.env.*` 吞掉；以 `.gitignore` 密钥块为准、改动时逐条对照）。护栏取**行为式**：对 `fixtures/_probe/…` 这类无需真实存在的路径跑 `git check-ignore -v --no-index`，断言派生品形态（`reports/x.json`、`screenshots/y.jpg`、`a.log`、`a.report.html`）**未被忽略**、密钥形态（`.env`、`.env.local`、`z.pem`、`z.key`、`.aws/config`、`credentials`）**仍被忽略**——两向都测才挡住「新规则排到反白名单之后」与「收紧句被删」两种回归；再加一条「磁盘 `fixtures/**` 每个文件都在 `git ls-files` 里」作提交前抓漏（干净克隆上恒绿，不是 CI 的唯一防线）。
- **fixture 可搬迁契约**（物化式；权衡见下）：入库 fixture 里不得出现产出机器的绝对路径，逐文件列覆盖面：`run_meta.json` 的 `steps_dir`（提交侧恒绝对化、接力会读回注给引擎）、`jobs/*.json` 的 `report_refs[].ref`、`evidence.json` 的 `acts[].frames[].screenshot`——三处存成占位符 `file://{{FIXTURE_ROOT}}/…`，评测前由 `materialize.py` 替换成舞台目录的绝对路径；`manifest.json` / `index.html` 只带相对化的 `href`、天然可搬（前提 = 录制时产物落在 run 树内，录后确认无绝对 href）。**录制约束**：录 fixture 时 feature 一律用相对路径调用——`scope_id` / `scenario_id` = `<给的 feature 路径>:<行号>`，绝对路径会同时进 JSON 字段与 `jobs/<urlencode(scope_id)>.json` 文件名，占位符救不了文件名。**文件集**：至少 `run_meta.json` + `run_state.json`（`explain` 读不到 run_state 直接退 2）+ `jobs/*.json` + 被引用到的 evidence 与截图（裁成极小占位字节）；`worker.log` / `reconcile.log` 不入库（含绝对路径、对评测无用，反白名单会把它们从 `*.log` 里救回来，须显式排除）。**兜底护栏**：扫 `fixtures/**` 的文本文件，出现不以 `{{FIXTURE_ROOT}}` 开头的绝对路径即红（逐文件枚举总会漏新字段，这条按不变量兜）。
- **物化后的完整性断言**（只挡物化真会造成的缺口，不把合法态判坏）：`explain --json` 里所有有记录的 step（`record_missing` 为 false）其 `evidence_missing` 不得为 `unreadable` / `unsupported_schema`（这两码 = 占位符没替对、路径错、字节被吞）；`no_ref` 是合法态——确定性 step、引号内 URL 导航 step 本就不产、`record_missing` 的 step 恒为 `no_ref`（[0042](./0042-step-evidence-and-explain.md) 决策四），不算 fixture 坏；至少一条 step 拿到非空 `evidence`；对每份 evidence 的 `acts[].frames[].screenshot` 非 null 的 `file://` 地址逐个 stat 文件存在且非空——截图缺失在 `explain --json` 里没有任何信号（它只读 evidence.json 自身），这条才是「全绿但两臂看不到截图」的真护栏。
- **为什么是物化式而不是程序化生成**：仓库里有现成公开组合根（`compose.build_local_stores`）能在舞台里现造 run 目录，绝对路径按构造正确、零派生品入库、上面三条护栏一并消失；代价是 fixture 数据变成 Python 构造代码、耦合 `gherkai_core` 的 model 与 serialize，人肉 review 不如直读 JSON。选物化式是为「fixture 可直读、可 diff、与真跑产出同形」；`run_meta` / `run_state` / `jobs` / `evidence.json` 改为生成这条路已评估、列入被拒方案留护栏。
- **缺省集零条真 AWS，只执行 `plan` / `explain` / `doctor` / `list-deterministic`，不执行 `run` / `submit`**：本机 `run` 同样起云端浏览器会话与模型调用（两引擎的本机 worker 都连 AgentCore），且 fixture 里的被测地址不可达、技术上也跑不通；`doctor` 不给 `--prefix`、不给 `--backend cloud`（云端项按设计标「未查」）。真执行 `run` / `submit` 的任务单列进 **opt-in 集**（`evals.json` 显式标记、缺省跳过）。
- **隔离面**：**舞台**（被测项目）与**工作区**（结果）分开。`materialize.py` 把 `fixtures/<case>` 拷到仓库外一次性目录（如 `$TMPDIR/gherkai-eval-<id>/`）当「使用方项目」；提示里只给两条路径——舞台目录，以及（with-skill 臂）包内 skill 路径——**不给 skill 想替代的原始教材路径**（根 README / `cli/README.md` / `docs/guides/` / `docs/adr/`）与仓库根；两臂都以独立进程 `claude -p` 跑、cwd = 舞台（进程内 subagent 只是提示级隔离：仍继承父会话 cwd、能读仓库、吃项目 `CLAUDE.md`）。内容有效性由两臂 delta 量，description 触发命中率由触发集另量——with-skill 臂不装进发现位、只在提示给路径，不是遗漏。前置断言：舞台及其上溯路径与用户级目录下没有已装的 `gherkai` skill，命中即拒跑（dogfood 安装态与评测互斥，跑评测前移走）。**CLI 调用方式**：首选舞台 `bin/gherkai` shim 前置 PATH（指向 `<repo>/.venv/bin/gherkai`）；`uv run --project <repo> --no-sync --frozen gherkai …` 只作 shim 不可用时的回落——它把仓库根绝对路径交到 baseline 手里，与「在仓库内跑评测」同一漏洞，此时 baseline 纯度靠提示约束、delta 偏保守；整轮评测内环境冻结、不隐式改 lock、不依赖网络。**AWS 环境由臂内层声明**：shim 里 `unset AWS_PROFILE AWS_REGION AWS_DEFAULT_REGION`、并把 `AWS_CONFIG_FILE` / `AWS_SHARED_CREDENTIALS_FILE` 指向舞台里的空文件再 exec CLI——只在启动器父进程 unset 无效（宿主用户级 Claude Code settings 的 `env` 块会给新会话重新注入），空配置文件盖住 profile 里的 region 回落；目的是让本机段输出跨机器一致（一旦被测 agent 自发打 `--prefix`，有无 region 走到 `doctor` 的不同分支）。**引擎可用性**：harness 对两臂对称注入 `GHERKAI_WORKER_MIDSCENE_CMD`（指向仓库内已构建的 `engines/midscene/dist/bin.mjs`，走 compose 定位链的 env 级），两侧 `list-deterministic` 都真能查、零 npm 零网络；env 由 harness 设、不进提示，仍只有 skill 一个变量；评测提示与工具白名单**禁止任何安装类操作**（`npm i`、`uv tool install`、`pip install`）——安装只会发生在读到安装指引的那一臂，会把「改了本机、要联网、第二轮环境已变」引进对照实验。
- **提示写法两条硬约束**：① 每条提示嵌 fixture 里的具体坐标（feature 文件名、失败 scenario 的 step 原文、run 目录名）加一句背景，写成使用者真会打出的话，不写「把这条断言改成精确检查」这类抽象句式——抽象提示测不出触发也测不出执行；② 一步就能答完的提问不作为 eval——agent 只在任务自己搞不定时才去查 skill，这类提示 with-skill 臂也不消费 skill、delta 是假零。若某条 eval 的 with-skill 臂未消费 skill，判为无效样本、重写后再跑、不计入通过率。
- **可核断言，按集归属**：缺省集 = 给一段需求 + 应用信息时写出的 feature 能过 `plan`（tag 合法、导航步走确定性标注、AI 步为页面级陈述）且配套确定性 step 在 `list-deterministic` 里可见；产出的命令序列里 `plan` 先于 `run`（或对「为何先 plan」的解释正确，不真跑）；失败后调 `explain` 而非读 HTML；用 `--json` 取字段而非正则 stdout；对 `submit` 与非终态 `status` 退 0 的解读正确（只核解读、不执行）；改确定性 step 写在 `steps/` 并对两个引擎各 `list-deterministic --engine` 查一遍（midscene 侧靠上面的 env 注入可查）。opt-in 集 = 真执行 `run` / `submit` 后的判定读法与云端路径。
- **description 优化**：`trigger-eval.json` 跑 skill-creator 的 `run_loop.py`（`claude -p`，`--model` 传本会话模型），取 held-out 最优；产物入库前过决策六的 ≤ 1024 字符护栏。首轮结果（with-skill 对 baseline 的断言通过率、人审反馈、触发命中率 train / held-out）内联进「验证」节后翻 Accepted。

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
- **fixture 纯程序化生成**（在舞台里用 `compose.build_local_stores` 现造 run 目录）：零派生品入库、绝对路径按构造正确，但 fixture 变成 Python 构造代码、耦合 core 的 model 与 serialize、review 不直观；取物化式，理由见决策七。
- **安装命令用文件清单做幂等覆盖**：清单是为「与用户自有文件共存」设的复杂度，skill 目录是独占命名空间，整目录收敛更简单且跨版本收敛。

## 不做 / 延后

- `doctor` 加一项「已装 skill 的版本是否等于 CLI」（读 `.gherkai-skill-version`；「版本未知」态跳过比对；dev 树里该值是 `uv sync` 时的快照、只对发行版安装有判定意义）：等安装命令真用起来再定形态。
- `skill uninstall`：目前 `rm -rf` 即可；评测前置需要它时再加。
- `scripts/`：等评测显示测试用例反复手写同一 helper 再收进来；`assets/`（模板 / 图标类、skill 往使用方项目产出的资源文件）同理——本 skill 不产这类文件，它教 agent 操作 CLI 与改 feature / steps（本机与 cloud 两档的跑法都在 scope 内；决策七缺省集不执行 `run` / `submit` 是评测手段、不是能力边界），真要用时先进白名单再开。
- 仓库根镜像 / 发布到 skills.sh 一类目录：等使用方需求。
- 引擎专属 skill 拆分（`gherkai-novaact` / `gherkai-midscene`）：evidence **schema** 同形、引擎差异有界且一页 reference 列得完，不拆。
- 按任务域拆成多个 skill（测试 / 排障 / 部署）：现为一个入口三份 reference，拆分只在决策五的重议闸门触发时做。

## 影响面

**code**

- 新目录 `cli/gherkai_cli/skills/gherkai/`（`SKILL.md`、`references/{cli-json-contract.md, engines.md, setup-and-diagnosis.md, cloud-backend.md}`）；仓库根 `skills/gherkai-evals/{evals.json, trigger-eval.json, fixtures/, materialize.py}`（不分发）；`tools/render_skill_contract.py`（契约页 → 副本的确定性转换，含禁词映射表）；`.gitignore` 加 `skills/*-workspace/`、fixture 反白名单与其后的密钥块重列。
- `cli/gherkai_cli/__main__.py`：`skill install` 子命令（嵌套 subparser、子动词必填）；新模块 `cli/gherkai_cli/skill_install.py`（`importlib.resources` 定位、整目录收敛、标记文件、`--print`）。`cli/pyproject.toml` 不需要 force-include。
- 测试：`cli/tests/test_skill.py`（产品面文案与指针形态、命令面成对真值与排他断言、JSON 键对照、转换副本相等、目录白名单、形态四条、安装命令行为含跨版本收敛、fixture 的 ignore 行为式断言与 git 跟踪、fixture 绝对路径不变量）；`deploy_aws/tests/` 加 provider 侧 token 对照（prog 末段 + 中立 flag + provider）；禁词 / 相对链接常量从 `cli/tests/test_package_readmes.py` 抽成共享模块；`.github/scripts/check_dist_metadata.py`（CI 打包 smoke 与发布 gate 共用）加一项「wheel 内 skill 文件集 == 源目录文件集、不含评测资产」，其 docstring 的断言清单同步。

**文档（反向链逐处列出，Accepted 前逐条核）**

- [0041](./0041-agent-facing-cli-affordances.md)：决策五「skill 只链接它，不复制字段表」改为「唯一手写源仍在 docs、不进发行包；skill 带一份确定性转换的副本随 CLI 发行（为何不能 link、转换与护栏见 0043 决策四）」；「影响」节那条前向指代改为指向 0043 决策五、删掉工作循环的复述；Status 头两处：「agent skill（另立）」改指 0043；本 ADR 翻 Accepted 时改 `Partially-superseded-by 0043`，限定范围 = 决策五「skill 只链接它，不复制字段表」这一子句被反转，决策一–四与决策五其余部分不变。
- [0037](./0037-distribution-and-packaging.md)（扩展、Status 不动）：「决策总览」CLI 行注「含随 wheel 带的 `skills/gherkai` 包数据（0043）」、末行不分发枚举加根 `skills/`（评测资产）；「工程布局」树补 `cli/gherkai_cli/skills/` 与根 `skills/gherkai-evals/`。
- [0039](./0039-user-facing-surfaces-no-internal-references.md)（扩展、Status 不动）：面二表新增一行（`cli/gherkai_cli/skills/gherkai/**`；去向 = 随 CLI wheel 发行、由 `skill install` 拷进使用方项目 / agent 目录；链接只用绝对 URL），并把表前「四层只差去向与链接形态」改为不数数的说法（表已含 Release 正文一行，钉数字必再漂）；「护栏」节补 `cli/tests/test_skill.py` 这只 markdown 扫描器。
- [0016](./0016-execution-architecture-core-lib-run-model.md)（扩展、Status 不动）：v1.4.0 完成线里「claude/ai skills 暴露」一项改为工具中立措辞并补权威指针到本 ADR；本 ADR 翻 Accepted 时同步该项完成状态。
- [0001](./0001-scope-limited-to-english-ui.md)（扩展、Status 不动）：「影响」节承载语言口径的面加 skill 的 `references/engines.md`。
- `CLAUDE.md`：代码纪律「产品面文案不带内部指代」的条件加「以及随发行包发到使用方项目的 markdown（agent skill）」；文档纪律「README / DEVELOPMENT 分层」的使用者向枚举加「随包发行的 skill 内容」，两处指本 ADR。
- `docs/REFERENCES.md` 新开「Agent Skills」节：规范（frontmatter 字段与上限）、vercel-labs `skills` CLI README（容器目录、直指路径、安装位）、Codex skills 文档（`.agents/skills` 位）、skill-creator 位置。
- 根 `README.md` 加「让 AI agent 驾驭」一节（两条安装路径、次选路径不钉 tag 时的版本代价与钉 tag 模板）；`cli/README.md` 加 `skill install` 行；`docs/guides/cli-json-contract.md` 头部加 skill 指引与「有转换副本随 CLI 发行」；`docs/guides/README.md` 末句 skill 指向本目录。
- 根 `DEVELOPMENT.md`：目录树（`cli/gherkai_cli/` 行加 `skills/gherkai/`、新增根 `skills/gherkai-evals/`）、ADR 范围到 0043、测试节的护栏枚举句补 `cli/tests/test_skill.py`（按实况改写，它不只扫文案）；`cli/DEVELOPMENT.md`：模块树的子命令枚举加 `skill`、模块行加 `skill_install.py`、「跑测试」节加 `test_skill.py` 与 `tools/render_skill_contract.py` 的跑法；`CONTEXT.md` 术语加 skill。

## 验证（Accepted 前必做，结论内联到此处）

- 护栏全绿：产品面文案与指针形态、命令面成对真值与排他断言、JSON 键对照、转换副本相等、目录白名单、形态四条、fixture 的 ignore 行为式断言与绝对路径不变量。
- 打包：`uv build --all-packages` 全绿且 wheel 内 `gherkai_cli/skills/gherkai/` 文件集等于源目录、不含评测资产；editable 树上 `gherkai skill install --print` 输出与包内文件一致。
- `skill install` dogfood：`--agent all` 装进本仓库后 `git status` 干净；重复安装与「模拟上一版多出一个 reference 后再装」都收敛到除 `.gherkai-skill-version` 外与包内逐字节相等；对非本命令所装的目录退 2。
- 手工核一次 `skills-ref validate`（规范校验器），确认本地复刻的形态检查同口径；不进 pytest。
- skill-creator 循环首轮：每条 eval 的 with-skill 对 baseline 断言通过率与人审反馈；无效样本（两臂均未消费 skill）的处理记录；description 优化前后的触发命中率（train / held-out）。
- `npx skills add https://github.com/zhiyanliu/gherkai/tree/<tag>/cli/gherkai_cli/skills/gherkai` 在一台干净目录里装一次、目录布局符合预期；在装了 skill 的干净项目里试一次隐式触发。
