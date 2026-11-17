# Claude Code 在本仓库的操作要点

> 随 `CLAUDE.md` 加载，所以每条只写一两句。只记 Claude Code 工具行为引起、与具体机器无关、工具自带说明里没有的教训；工具中立的约定在 [`CLAUDE.md`](../CLAUDE.md) 与 [`docs/ai-eng/`](../docs/ai-eng/README.md)，护栏的分工见 [ADR 0046](../docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md)，各 hook 怎样验证写在它的脚本头。

## Workflow

- 代理因 API 错误或机器休眠失败之后，脚本仍会继续执行后面的阶段，旧任务可能还在运行。重新启动之前先确认旧任务已经结束（任务列表、`journal.jsonl`、各代理记录的修改时间），还在运行的先停掉，再核对并结束它起过的子进程；否则两个 Workflow 同时改一个工作区。
- 重新执行时工作区里留着上一位代理做了一半的改动：简报写明「在其上完成、不回退」。
- `isolation: worktree` 的 worktree 基于仓库的主分支，不是主工作区当前的提交，未提交的改动它也没有：提示里写明基点提交，让代理先 `git reset --keep <提交>` 再动手，产物用补丁交回。结束后用 `git worktree list` 核对并清掉留下的 worktree，否则全仓 grep 出现双份命中。
- 大批条目写成 JSON 文件由代理按组 id 读，`args` 只传元数据。
- 子代理写不出报告类的文件，会被工具层拦下并提示改用文本返回：要留档的结论让它按结构化结果返回，由主会话从 `journal.jsonl` 生成文件。

## Bash

- stdin 是不会结束的管道（前后台一样）：读 stdin 的脚本要显式给输入并结束，不需要输入时接 `< /dev/null`。
- 带中文的 Python 源码不经 heredoc 传给 `python3 -`（出现过「Non-UTF-8 code」）：先写成文件再执行。
- 改文件与 `git commit` 分成两次调用：提交闸门在整条命令执行之前运行，同一条命令里先改后提交，它扫不到新内容。手动核对改动用 `uv run python tools/doc_rules_check.py --uncommitted`（暂存区用 `--staged`），按它的退出码决定是否提交。

## 记忆文件

- `CLAUDE.md` 引入本文的那一行按 ADR 0046 决策 7 的写法约束写：实测 `@` 紧跟在全角冒号之后时本文没有被载入，也没有提示。改过那一行之后起一个无交互的子会话，问它上下文里有没有本文的内容；测试只查写法，不证明已载入。

## hooks

- 在 `.claude/settings.json` 新登记的 hook 下个会话才生效，当前会话里验证不到它。
- 复核轮被发送工具或 hook 拦下时，先读 `docs/ai-eng/peer-review.md` 第三、四节把简报补全，不改写命令形态绕开。
