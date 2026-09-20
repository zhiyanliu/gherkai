# 护栏：怎么加一条规则、hook 怎么工作、本地怎么跑

> 给 contributor 与 contributor 侧 AI agent：三层护栏的决策与理由在 [ADR 0046](../adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md)，规则的内容各归其 ADR（口吻 [0045](../adr/0045-documentation-layering-and-placement.md) 决策六、术语 0045 决策八、产品文案 [0039](../adr/0039-user-facing-surfaces-no-internal-references.md)）。本文只讲操作。

## 一份规则源

`cli/tests/_doc_rules.py` 是唯一的规则与扫描面定义：

| 名字 | 是什么 |
|---|---|
| `FORBIDDEN` | 内部指代（ADR 编号、决策号、内部机制名），产品面禁 |
| `COLLOQUIAL` | 口吻表：口头语、隐喻、量词「档」、决策六形态②的自造复合词（`COINAGES` 是其中可单独用的子表） |
| `RETIRED_TERMS` / `RETIRED_TERMS_IN_CODE` | 词表退役名；后者去掉与 Stream 事件批撞词的「本批 / 整批 / 这一批」，只给注释层用 |
| `SYMBOL_PREDICATE` / `NUMERIC_SHORTHAND` / `ARROW` | 决策六形态①③的启发式：中文字紧邻 `=`、`≠` / `⊆`；「退 N」；箭头（只在用户文档与 skill 正文禁） |
| `DANGLING_JOURNEY` / `BARE_WP` | 悬空指针形态：指向具体 journey 文件的链接、裸 WP 编号 |
| `prose_lines()` / `comment_units()` | markdown 正文抽取（剥代码块与行内代码、可跳 frontmatter）；注释与 docstring 抽取（Python 走 tokenize + ast，TS / JS 遮蔽字符串后取注释，shell / YAML / Dockerfile 取 `#`） |
| `user_docs()` `technical_docs()` `ai_side_docs()` `code_comment_files()` `diagram_sources()` `skill_markdown_files()` `long_term_docs()` | 七个扫描面 |
| `classify(path)` / `scan(kind, path, only_lines)` | 把文件归到扫描面、按该面的规则束扫；测试、hook、闸门都调这两个 |

## 三个时刻

| 时刻 | 入口 | 扫什么 | 命中后 |
|---|---|---|---|
| CI 与 `uv run pytest` | `cli/tests/test_user_docs.py` `test_skill.py` `test_package_readmes.py` `test_technical_docs.py` `test_code_comments.py` `test_adr_hygiene.py` `test_context_glossary.py` `test_user_facing_messages.py` | 各自的扫描面全量 | 测试红 |
| Claude Code 里每次 Edit / Write / MultiEdit / Bash 之后 | `.claude/hooks/wording-guard.sh` → `tools/doc_rules_check.py --changed` | 工作区相对 HEAD 的改动：已跟踪文件只看改动的行，未跟踪文件全扫 | `exit 2`，命中行回给 agent |
| Claude Code 里 `git commit` 之前 | `.claude/hooks/commit-gate.sh` → `tools/doc_rules_check.py --staged` | 暂存文件整份 | `exit 2`，提交被阻断 |
| 人类 contributor 提交前（可选） | `tools/git-hooks/pre-commit`，`git config core.hooksPath tools/git-hooks` 启用 | 同上 | 拒绝提交 |

hook 由入库的 `.claude/settings.json` 挂载；首次进入仓库时 Claude Code 会要求确认一次。`sync-derived.sh`（派生文件同步）仍是提醒式，与这两道阻断式 hook 并列。

## 本地怎么跑

```bash
uv run python tools/doc_rules_check.py --changed              # 我刚改的行有没有命中（hook 跑的就是它）
uv run python tools/doc_rules_check.py --staged               # 暂存区整份（提交闸门跑的就是它）
uv run python tools/doc_rules_check.py docs/internals/x.md    # 指定文件全扫
uv run pytest cli/tests/test_code_comments.py -q              # 某一面的全量护栏
```

输出形态 `路径:行号: 类别 · 原文`；退出码 0 无命中、1 有命中、2 脚本自身出错（hook 对 2 不阻断）。

## 加一条规则

1. 先在规则所属的 ADR 立决策（口吻 → 0045 决策六；术语 → 0045 决策八，先改 `CONTEXT.md` 词表；产品文案 → 0039）。没有决策依据的正则不进护栏。
2. 在 `_doc_rules.py` 里加正则或扩扫描面：固定词进 `COLLOQUIAL` / `RETIRED_TERMS_WORDS`（后者要先在 CONTEXT 某条 `_Avoid_` 登记，`test_retired_terms_are_all_in_the_glossary` 守同源）；新形态的启发式单独命名并在 `scan()` 里挂到对应的面。
3. 把当前命中清零后再加词——护栏当场红是设计，不是 bug。
4. 看 CLAUDE.md 对应条能否因此精化为「判据 + 指针」。

## 豁免与盲区（改规则前先看）

- `SELF_FILES`：定义禁词表、把这些词当数据的文件不扫自己；`COINAGE_DISCUSSION`：讨论自造词本身的三份文档不套形态②。
- 「绿≠对」是 CLAUDE.md 立的判据名，`SYMBOL_PREDICATE` 显式放行；排版学义的「同形字符」与「协同调度」放行。
- 启发式认不出等号一侧是英文、全角括号或跨行的写法（`（= X`、`英文词 = 中文`、折行的 `恒 ⏎ ==`）与模板字符串里的中文；清扫时人工宽扫补，护栏只保证命中即真。
- 注释层不用 `RETIRED_TERMS` 的「批」义三词；Run 义的「整批」残留交 code-health 复盘。
- 代码块、行内代码、机读键名、命令示例里的符号不算（`prose_lines` 剥掉；注释抽取只取注释文本）；表格单元格照扫。
