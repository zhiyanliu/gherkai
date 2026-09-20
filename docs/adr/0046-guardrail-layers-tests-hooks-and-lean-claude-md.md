# 0046. contributor 护栏三层：测试兜底、hook 写完即查、CLAUDE.md 只留判据

> **Status:** Accepted（2026-09-20）—— 把 [0039](./0039-user-facing-surfaces-no-internal-references.md) 护栏节、[0045](./0045-documentation-layering-and-placement.md) 决策六 / 八与 CLAUDE.md 文档纪律里能逐行判定的规则统一收进同一份规则源，并给 Claude Code 加两道 hook；规则的内容仍各归原 ADR，本 ADR 只定「怎么执行」。

## 背景与问题

CLAUDE.md 里的多数纪律是**正向要求**：「写人读文本前按决策六自查」「取代旧 ADR 时双向改 Status 头」「长期文档不指 journey」。它们靠 agent 读到并记住，而 agent 的记忆不跨会话、别的 contributor（Codex、人、没有个人 memory 的 agent）读到的只是一段散文。2026-09-20 的 code-health 第 5 轮把这一点坐实：owner 在注释与文案里发现三种 ADR 式缩写（符号当谓语、自造二字复合词、「退 N」），全仓清扫出约 1000 处，其中大半是 CLAUDE.md 已经写着「注释一律书面」之后才写进去的；同一轮还发现注释与 docstring 不在任何护栏的扫描面内，退役旧名靠人眼每轮找。写规则的人自己都会再犯，说明**正向提示不是执行机制**。

仓库里已有两种「反向」机制：`cli/tests/` 下的护栏测试（CI 兜底，但只在提交后才红）与项目级 hook `.claude/hooks/sync-derived.sh`（派生文件同步，写完即提醒）。缺的是把它们接成体系：规则一份、三个时刻都用它。

## 决策

**三层，同一份规则源，按能否机械判定分流。**

1. **规则源唯一**：`cli/tests/_doc_rules.py` 存全部逐行可判的规则（内部指代表、口吻表、退役词表、决策六三形态的启发式、悬空指针形态）与**扫描面**（用户文档、skill、包页、技术文档、AI 侧文档、图源、code 注释与 docstring 各是一束），并提供 `classify(path)` 与 `scan(kind, path, only_lines)`。测试、hook、提交闸门都调它，不各存一份。
2. **第一层：测试兜底**（CI 与 `uv run pytest`）。每个扫描面一份护栏测试，逐文件参数化、命中即红。除措辞与术语外，把 doc-health 历轮靠人查的形态项也机械化：ADR Status 头与「被取代」链双向、`docs/` 文件名 kebab-case 与编号不复用、journey 首行类型头、长期文档与 AI 侧文档里指向 journey 文件的链接与裸 WP 编号、CONTEXT 词条形态（术语行 + 至多两句 + 至多一个 ADR 指针 + `_Avoid_` 只列词）。
3. **第二层：hook 写完即查**（只在 Claude Code 里生效，随仓库入库）。
   - PostToolUse（Edit / Write / MultiEdit / Bash 之后）：`tools/doc_rules_check.py --changed`，已跟踪文件**只报本次改动的行**（`git diff -U0 HEAD` 的区间）、未跟踪文件全扫；命中即 `exit 2`，命中行回给 agent、它必须先改再继续。**阻断式而非提醒式**：提醒会被当成噪声滚过去，正是本 ADR 要替换的「正向要求」。**只报改动行**：历史欠账另有测试与复盘兜底，hook 只该报「你刚写的」，否则一次大改动进行中会被旧命中刷屏、逼人关掉它。
   - PreToolUse（`git commit` 之前）：`tools/doc_rules_check.py --staged`，暂存文件整份再扫，命中即阻断提交。兜住绕过编辑工具的改法（脚本批量改文件）。
   - 派生物同步（`sync-derived.sh`）维持提醒式：它做的是自动修复与提示，不是拒绝。
   - 脚本自身出错（退出码 2）不阻断：工具问题不该把编辑卡死。
4. **人类 contributor**：同一份脚本给一个可选的 git pre-commit（`tools/git-hooks/pre-commit`，`git config core.hooksPath tools/git-hooks` 启用）；不启用的仍由 CI 兜底。git hook 不随仓库分发，故只能 opt-in，不能替代第一层。
5. **第三层：CLAUDE.md 只留判据与指针**。凡已被第一、二层机械化的条目，CLAUDE.md 里精化为「判据一句 + 护栏 / hook 指针」，不再复述枚举；留在 CLAUDE.md 里作正向要求的只剩机器判不了的判断型规则——读者比例定压缩方向、绿≠对的证据边界、接口诚实优先于改动规模、AWS 免费的适用期、「改完 code 回头校准文档」的差集习惯。判据：一条规则若能写成「某文件某行命中某正则即错」，它就不该只活在 CLAUDE.md 里。

**加一条规则的顺序**：先在规则所属的 ADR 立决策（口吻 → 0045 决策六；术语 → 0045 决策八；产品文案 → 0039），再在 `_doc_rules.py` 加规则或扩扫描面——测试与 hook 自动接上，不另配；最后看 CLAUDE.md 对应条能否因此精化。操作细节在 CONTRIBUTING.md「护栏三层」段（人读的技术文档，contributor 的入口）。

## 边界与已知盲区

- hook 只在 Claude Code 会话里生效；Codex 与人手编辑靠测试与可选 git hook。
- 启发式有形态盲区：等号一侧是英文、全角括号或跨行时正则不命中（`（= X`、`英文词 = 中文`、折行的 `恒 ⏎ ==`）；模板字符串与 f-string 里的中文不在注释抽取面内。清扫时靠人工宽扫补，护栏不追求零漏报，只保证「命中即真」（低误报）以维持阻断式可接受。
- 「本批 / 整批」在 Lambda 与 Stream 侧注释里指事件批，注释层的退役表去掉这三个词，Run 义的残留交 code-health 复盘人判。
- 判断型规则不进护栏，也不装作能进。

## 被拒方案（护栏）

- **全靠 CLAUDE.md 正向提示**：本轮约 1000 处违规都写在 CLAUDE.md 已有要求之后，且别的 contributor 读不到 agent 的个人 memory。
- **只用 git hook**：不随仓库分发、只对人有效，Claude Code 的 Bash 提交也绕不过它但拿不到即时反馈；故 git hook 只作 opt-in 补充。
- **hook 只提醒不阻断**：与正向提示同一失败形态——被滚过去。阻断式的前提是低误报与只报改动行，两者本 ADR 都做了。
- **hook 全文件扫**：改一行报出全文件历史命中，一次清扫进行中会刷屏；改动行判据用 `git diff -U0 HEAD` 直接给出、零成本。
- **规则散在各测试文件里各写一份**：hook 与测试会漂；`_doc_rules.py` 已是四份护栏的单一事实源，扩它而不是复制。
- **把新护栏做成 CLAUDE.md 里更长的清单**：那是把执行机制写回散文；护栏名单归 CONTRIBUTING.md「护栏三层」段，CLAUDE.md 只给一个指针。

## 与既有 ADR 的关系

- [0039](./0039-user-facing-surfaces-no-internal-references.md) 护栏节：产品文案的正则表与「靠 review」那半，本 ADR 不改判据，只把「靠 review」的那部分前移到写完即查。
- [0045](./0045-documentation-layering-and-placement.md) 决策六 / 八：措辞标准与词表流程仍在那里；本 ADR 是它们的执行层。
- [0043](./0043-agent-skill-for-driving-gherkai.md) 决策六：skill 的产品面护栏并入同一份规则源与 hook。

## 对既有文档与 code 的影响

- 新增：`tools/doc_rules_check.py`、`.claude/hooks/wording-guard.sh`、`.claude/hooks/commit-gate.sh`、`tools/git-hooks/pre-commit`、`cli/tests/test_code_comments.py`、`test_technical_docs.py`、`test_adr_hygiene.py`、`test_context_glossary.py`；`.claude/settings.json` 挂两道新 hook。
- CLAUDE.md：Status 头、journey、悬空指针、文件名、三分类、严格词表、commit 六条各精化为判据 + 护栏指针；CONTRIBUTING 补「护栏三层」段（操作手册）、开发环境里的 opt-in git hook 与工具表两行；CONTEXT 立「护栏」词条。
