# 0046. contributor 护栏三层：测试兜底、hook 写完即查、CLAUDE.md 只留判据

> **Status:** Accepted（2026-09-20）—— 把 [0039](./0039-user-facing-surfaces-no-internal-references.md) 护栏节、[0045](./0045-documentation-layering-and-placement.md) 决策六 / 八与 CLAUDE.md 文档纪律里能逐行判定的规则统一收进同一份规则源（用户可见字符串字面量的禁词表按 0039 护栏节仍单独存于 `cli/tests/test_user_facing_messages.py`，只由测试层执行），并给 Claude Code 加两道 hook；规则的内容仍各归原 ADR，本 ADR 只定「怎么执行」。

## 背景与问题

CLAUDE.md 里的多数纪律是**正向要求**：「写人读文本前按决策六自查」「取代旧 ADR 时双向改 Status 头」「长期文档不指 journey」。它们靠 agent 读到并记住，而 agent 的记忆不跨会话、别的 contributor（Codex、人、没有个人 memory 的 agent）读到的只是一段散文。2026-09-20 的 code-health 第 5 轮把这一点坐实：owner 在注释与文案里发现三种 ADR 式缩写（符号当谓语、自造二字复合词、「退 N」），全仓清扫出约 1000 处，其中大半是 CLAUDE.md 已经写着「注释一律书面」之后才写进去的；同一轮还发现注释与 docstring 不在任何护栏的扫描面内，退役旧名靠人眼每轮找。写规则的人自己都会再犯，说明**正向提示不是执行机制**。

仓库里已有两种「反向」机制：`cli/tests/` 下的护栏测试（CI 兜底，但只在提交后才红）与项目级 hook `.claude/hooks/sync-derived.sh`（派生文件同步，写完即提醒）。缺的是把它们接成体系：规则一份、三个时刻都用它。

## 决策

**三层，同一份规则源，按能否机械判定分流。**

1. **规则源唯一**：`cli/tests/_doc_rules.py` 存全部逐行可判的规则（内部指代表、口吻表、退役词表、决策六三形态的启发式、悬空指针形态、包页面的相对链接与 Release 固定块里未锁定 tag 的仓库链接）与**扫描面**（用户文档、skill、包页、技术文档、AI 侧文档、图源、code 注释与 docstring、其余 markdown（含 journey，只拦本机坐标）各是一束），并提供 `classify(path)` 与 `scan(kind, path, only_lines)`；`scan` 另有可选参数 `text`，给了就扫它、不读文件（提交闸门借此传入暂存区里的版本）。测试、hook、提交闸门都调它，不各存一份。唯一例外是用户可见字符串字面量的两条规则——禁词表与 markdown 强调记号（成对的 `**…**`）：判据与 markdown 面不同（见 [0039](./0039-user-facing-surfaces-no-internal-references.md) 护栏节），二者单独住在 `cli/tests/test_user_facing_messages.py`，hook 不扫字符串字面量。禁词表扩表时两侧都要过一遍；强调记号那条在 markdown 面没有对应规则（markdown 里 `**` 是正当的强调），只在字面量一侧。
2. **第一层：测试兜底**（CI 与 `uv run pytest`）。每个扫描面一份护栏测试，逐文件参数化、命中即红。除措辞与术语外，把 doc-health 历轮靠人查的形态项也机械化：ADR Status 头与「被取代」链双向、`docs/` 文件名 kebab-case 与编号不复用、journey 首行类型头、长期文档与 AI 侧文档里指向 journey 文件的链接与裸 WP 编号、全仓 markdown（含 journey）与 code 注释里的本机坐标（个人目录下的绝对路径、本地 clone 目录名——写下它的 agent 顺手复制了编辑器里的路径，对别的机器上的 contributor 是悬空的；文件写 repo 相对路径）、CONTEXT 词条形态（术语行 + 至多两句 + 至多一个 ADR 指针 + `_Avoid_` 只列词）。
3. **第二层：hook 写完即查**（只在 Claude Code 里生效，随仓库入库）。
   - PostToolUse（Edit / Write / MultiEdit / Bash 之后）：`tools/doc_rules_check.py --changed`，已跟踪文件**只报本次改动的行**（`git diff -U0 HEAD` 的区间）、未跟踪文件全扫；命中即 `exit 2`，命中行回给 agent、它必须先改再继续。**阻断式而非提醒式**：提醒会被当成噪声滚过去，正是本 ADR 要替换的「正向要求」。**只报改动行**：历史欠账另有测试与复盘兜底，hook 只该报「你刚写的」，否则一次大改动进行中会被旧命中刷屏、逼人关掉它。
   - PreToolUse（`git commit` 之前）：`tools/doc_rules_check.py --staged`，按暂存区（index）里将要提交的版本整份再扫、不读工作区，命中即阻断提交。兜住绕过编辑工具的改法（脚本批量改文件）。取暂存区的版本是因为部分暂存或暂存后又改了工作区时，工作区与这次提交的内容不一致：扫工作区会放行暂存版本里的违规，也会拦下与本次提交无关的未完成改动。
     - **提交内容还没进暂存区的写法扫超集**：PreToolUse 在整条命令执行之前运行，同一条命令里随后才进暂存区的内容不在 `--staged` 的名单上。`commit-gate.sh` 从命令文本识别这几种形态：同一条命令里 `git add`（或同义的 `git stage`）出现在 `git commit` 之前；commit 带 `-a` / `--all`（含 `-am` 这类组合短选项）、`-i` / `--include`、`-o` / `--only`、`--pathspec-from-file`（从文件读入的 pathspec）或尾随 pathspec（含 `--` 之后的）。遇到其一即改为调用 `tools/doc_rules_check.py --uncommitted`，整份扫暂存区、`git diff HEAD --name-only --diff-filter=ACMR` 列出的文件与未跟踪文件（遵守 `.gitignore`）三者的并集，仍排除 `graphify-out/`；暂存区里的文件取暂存的版本，其余取工作区的版本，同一文件两版不同时两版都扫。常规形态（前面没有 `git add`、也不带上述选项与 pathspec 的 `git commit`，含 `git commit -F <msg>` 与 `--amend`）仍只扫暂存区。
     - **超集是补强，不是保证**：它只能扫闸门运行时已经存在的版本，即暂存区里的与工作区里的。覆盖成立的前提是同一条命令满足三条：在把文件纳入提交的那一步（`git add`，或带 `-a`、pathspec 这类选项的 `git commit` 本身）之前不改写它；不用 `git add -f` 加入被 `.gitignore` 忽略的文件；不换 `GIT_INDEX_FILE`。三条都成立时，这几种形态下每个文件提交进去的内容来自暂存版或工作区版之一，超集能覆盖；前提不成立的写法与命令文本认不出的写法列在「边界与已知盲区」，由第一层测试兜底。要保证提交内容本身经过检查，只能在提交用的 index 就位之后检查，即可选的 git pre-commit（第 4 条）：PreToolUse 运行时这份 index 还不存在，从命令文本推断它的内容只能逼近、无法等同，提交闸门因此不承诺这一点。
     - **命令文本的识别**：切词用 shlex；带值的选项（短选项 `-m` / `-F` / `-C` / `-c` / `-t`，长选项如 `--message` / `--file` / `--author` / `--fixup`）的值不当作 pathspec，组合短选项遇到带值的字母即停（`-am` 含 `-a`，`-ma` 是内容为「a」的 `-m`），重定向的目标与注释也不当作 pathspec；触发超集的长选项按前缀匹配，因为 git 接受长选项的唯一前缀（`--incl` 即 `--include`）；带值的长选项只认全名，写成前缀时它的值被当作 pathspec，结果只是扫描范围取大；带目录前缀的 git 可执行文件（如 `/usr/bin/git`）与 `git` 同样识别；含 `git ` 的引号内文本（如 `bash -c '…'` 的参数）递归识别，至多三层嵌套。切词失败（引号不配对，包括 shell 接受、切词器却不认的写法，如 heredoc 正文里的单个撇号）时按超集处理：闸门这时判断不出形态，只扫暂存区可能漏掉要提交的内容，扫超集的最坏情况是多拦下这次提交，而拦下的依据仍是真实命中。这与下文 `doc_rules_check.py` 自身出错时提示后放行是两种情况：工具出错时没有任何检查结果，阻断只会卡住提交、却给不出要改的行；切词失败时检查照常完成、结果可信，只是扫描范围取大。
     - 集合由 `doc_rules_check.py` 的 `--uncommitted` 计算，不在 shell 里拼：文件名的 `-z` 处理、`graphify-out/` 的排除与内容取哪一版都已在 `--staged` 的实现里，shell 再写一份，两份实现会逐渐不一致。
     - 代价与接受理由：工作区里有未提交改动、却不在本次提交里的文件也会被整份扫描，偶尔因此拦下提交。对这次提交而言这是误拦，命中的内容并不在这次提交里。接受这份代价，因为命中本身是真实违规（在测试为绿的基线上，工作区文件里的命中只能来自未提交的改动），改完即可提交，且误拦只在超集形态下发生；「命中即真」（见「边界与已知盲区」）说的是命中行本身违规，不等于被拦下的提交含有违规。`git add <路径> && git commit …` 这类先 add 再 commit 的形态同样按上述超集检查，扫描内容无命中时放行；上一笔提交没有包含全部改动时，留在工作区的文件照样整份扫描，有命中同样先改再提交。
     - 证据（据临时 clone 复现）：对含本机坐标命中的文件，`git add -A && git commit -F <msg>`、`git commit -a`、`git commit -F <msg> <pathspec>` 三种写法在只扫暂存区时都放行，先 add 再单独一条 `git commit` 则阻断。PostToolUse 对这几种写法也无法补救：命令结束时改动已进提交、这些文件相对 HEAD 已无改动，`--changed` 扫不到它们。「命令文本的识别」所列的写法（`git stage`、`--pathspec-from-file`、长选项前缀、`bash -c '…'`、带目录前缀的 git、引号不配对）闸门均改扫超集并阻断；四种认不出或超集覆盖不到的写法（先改写文件再 add 与 commit 的三段式、`git add -f` 加入被忽略的文件、换 `GIT_INDEX_FILE` 提交、`git -C <dir> add` 之后再 `git commit`）闸门均放行。可选的 git pre-commit（第 4 条）运行时 git 已备好提交用的 index（`GIT_INDEX_FILE`），`--staged` 扫的就是提交内容：`-a`、pathspec、`-o` 三种写法与上述四种闸门放行的写法，在启用了它的 clone 里实测均阻断，故它不需要超集。
   - 派生物同步（`sync-derived.sh`）维持提醒式：它做的是自动修复与提示，不是拒绝。
   - 脚本自身出错不阻断：两道 hook 只在 `doc_rules_check.py` 退出码为 1（有命中）时阻断，其余非零退出码（脚本自身出错为 2）一律不阻断，并把工具的错误输出经 `hookSpecificOutput.additionalContext` 作为提示回给 agent，让它知道这次改动或提交未经检查。工具问题不该把编辑卡死，也不该在 agent 不知情时被当成检查已通过。两道 hook 都保留工具的 stderr、不丢弃；`doc_rules_check.py` 把自身的一切故障（git 调用失败、规则模块出错、指定的路径不存在、无法识别的选项等）都归为退出码 2：Python 未捕获异常的默认退出码是 1，与「有命中」是同一个退出码，hook 会阻断、却只给出空的命中列表（据向规则模块注入异常的实测），丢弃 stderr 时连故障原因也看不到。
4. **人类 contributor**：同一份脚本给一个可选的 git pre-commit（`tools/git-hooks/pre-commit`，`git config core.hooksPath tools/git-hooks` 启用）；不启用的仍由 CI 兜底。它在提交用的 index 就位之后运行，是提交之前唯一能保证提交内容本身经过检查的一层（`git commit --no-verify` 跳过它时除外），启用后 agent 在该 clone 里的提交同样经过它。git hook 不随仓库分发、不会自动启用，故只能 opt-in，不能替代第一层。
5. **第三层：CLAUDE.md 只留判据与指针**。凡已被第一、二层机械化的条目，CLAUDE.md 里精化为「判据一句 + 护栏 / hook 指针」，不再复述枚举；留在 CLAUDE.md 里作正向要求的只剩机器判不了的判断型规则——读者比例定压缩方向、绿≠对的证据边界、接口诚实优先于改动规模、AWS 免费的适用期、「改完 code 回头校准文档」的差集习惯。判据：一条规则若能写成「某文件某行命中某正则即错」，它就不该只活在 CLAUDE.md 里。

**加一条规则的顺序**：先在规则所属的 ADR 立决策（口吻 → 0045 决策六；术语 → 0045 决策八；产品文案 → 0039），再在 `_doc_rules.py` 加规则或扩扫描面——测试与 hook 自动接上，不另配；最后看 CLAUDE.md 对应条能否因此精化。操作细节在 CONTRIBUTING.md「护栏三层」段（人读的技术文档，contributor 的入口）。

## 边界与已知盲区

- hook 只在 Claude Code 会话里生效；Codex 与人手编辑靠测试与可选 git hook。
- 提交闸门靠命令文本识别提交与形态，下列写法认不出或超集覆盖不到，由第一层测试兜底；启用了可选 git pre-commit 的 clone 里，这些提交同样经它检查。
  - 命令里没有字面的 `git commit`（`git -C <dir> commit`、`git -c <key>=<value> commit`、git 别名、在脚本内部发起的提交）时闸门不运行。
  - 认不出前面的 add：`git` 与 `add` 之间带全局选项（`git -C <dir> add`、`git -c <key>=<value> add`），以及 `git add` 以外修改暂存区的命令（如 `git mv`、`git apply --cached`、带路径的 `git checkout <commit> -- <path>`），与 `git commit` 写在同一条命令里时仍按常规形态只扫暂存区。
  - 超集的前提不成立：同一条命令先改写文件、再 `git add` 与 `git commit` 的三段式，以及先改写文件、再用 `git commit -a` 或带 pathspec 的 `git commit` 提交，提交的都是闸门运行时还不存在的第三版；`git add -f` 加入的被忽略文件不在超集里（未跟踪文件的列举遵守 `.gitignore`）；`GIT_INDEX_FILE=… git commit` 提交的是另一份 index，闸门读的是默认 index。
- 启发式有形态盲区：等号紧贴英文或全角括号这类非汉字字符、两侧都不留空格、写成 `==` 或跨行时正则不命中（`word= 中文`、`（= X`、`中文=中文`、`恒 == 真`、折行的 `恒 ⏎ = 真`）；模板字符串与 f-string 里的中文不在注释抽取面内。清扫时靠人工宽扫补，护栏不追求零漏报，只保证「命中即真」（低误报）以维持阻断式可接受。
- 定义禁词表与讨论这些词本身的文件（`cli/tests/_doc_rules.py` 的 `SELF_FILES`：各护栏测试与两个工具脚本）整份不扫，其注释与 docstring 的措辞靠复盘时人工检查。
- 「本批 / 这一批 / 整批」在 Lambda 与 Stream 侧注释里指事件批，注释层的退役表去掉这三个词，Run 义的残留交 code-health 复盘人判。
- 判断型规则不进护栏，也不装作能进。

## 被拒方案（护栏）

- **全靠 CLAUDE.md 正向提示**：引入护栏前的一次全仓扫描查出约 1000 处违规，都写在 CLAUDE.md 已有要求之后，且别的 contributor 读不到 agent 的个人 memory。
- **只用 git hook**：git hook 不随仓库分发、不会自动启用，每个 clone 都要各自执行 `git config core.hooksPath tools/git-hooks`；没启用的 clone 里，人与 agent 的提交都不经检查。它也只在提交时运行，给不出写完即查的反馈。故 git hook 只作 opt-in 补充。同理，提交内容还没进暂存区的写法也不靠把提交闸门挪到 git pre-commit 解决：那里 `--staged` 准确，连超集覆盖不到的写法也一并兜住，但只在启用了它的 clone 里生效；项目级 hook 随仓库入库，Claude Code 首次进入仓库时确认一次即对之后的会话生效。
- **提交内容还没进暂存区的写法的其余处理**：①拒绝这类写法、要求先 add 再单独一条 `git commit`——这样闸门运行时提交内容都已在暂存区，先改写文件再纳入提交（含三段式）与 `git add -f` 两种盲区也随之消除；代价是「先 add 再 commit」写在同一条命令里的常见写法得拆成两次调用，`-a` 与 pathspec 这类 git 常规用法也会被拦下、改写法后重试。这是操作成本而非不可解的冲突，但它落在每一次这类提交上，不论内容有无命中；超集只在有命中时才拦，拦下的都是真实命中，故取超集，剩余盲区交给测试层与可选的 git pre-commit；②提交之后再查、有命中再 amend——违规内容已进提交，修正靠 agent 自觉补做，回到正向要求的失败形态；③只登记为盲区——这正是 agent 的常用写法，登记之后照样每次绕过；④所有提交都扫超集——常规形态下（不换 `GIT_INDEX_FILE` 时）暂存区就是这次提交的内容，扩集合多拦下的是与本次提交无关的未完成改动；它能顺带补上少数认不出 add 的写法，但代价落在每一次常规提交上，只该在暂存区不等于提交内容的形态下付。
- **hook 只提醒不阻断**：与正向提示同一失败形态——被滚过去。阻断式的前提是低误报与只报改动行，两者本 ADR 都做了。
- **hook 全文件扫**：改一行报出全文件历史命中，一次清扫进行中会刷屏；改动行判据用 `git diff -U0 HEAD` 直接给出、零成本。
- **规则散在各测试文件里各写一份**：hook 与测试会漂；`_doc_rules.py` 已是既有护栏的单一事实源，扩它而不是复制。
- **把新护栏做成 CLAUDE.md 里更长的清单**：那是把执行机制写回散文；护栏名单归 CONTRIBUTING.md「护栏三层」段，CLAUDE.md 只给一个指针。

## 与既有 ADR 的关系

- [0039](./0039-user-facing-surfaces-no-internal-references.md) 护栏节：产品文案的正则表与「靠 review」那半，本 ADR 不改判据，只把正则表里已收进 `_doc_rules.py` 的那部分（使用者向 markdown 与 skill 的禁词）由提交后 CI 才报前移到写完即查；code 字面量的两条规则（禁词表与 markdown 强调记号）仍只在 `test_user_facing_messages.py`，「靠 review」那半不变，也不进护栏。
- [0045](./0045-documentation-layering-and-placement.md) 决策六 / 八：措辞标准与词表流程仍在那里；本 ADR 是它们的执行层。
- [0043](./0043-agent-skill-for-driving-gherkai.md) 决策六：skill 的产品面护栏并入同一份规则源与 hook。

## 对既有文档与 code 的影响

- 新增：`tools/doc_rules_check.py`、`.claude/hooks/wording-guard.sh`、`.claude/hooks/commit-gate.sh`、`tools/git-hooks/pre-commit`、`cli/tests/test_code_comments.py`、`test_technical_docs.py`、`test_adr_hygiene.py`、`test_context_glossary.py`；`.claude/settings.json` 挂两道新 hook。
- CLAUDE.md：Status 头、journey、悬空指针、文件名、三分类、严格词表、commit 七条各精化为判据 + 护栏指针；CONTRIBUTING 补「护栏三层」段（操作手册）、开发环境里的 opt-in git hook 与工具表两行；CONTEXT 立「护栏」词条。
