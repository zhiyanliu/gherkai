# Claude Code 在本仓库的操作要点

> 只记 Claude Code 工具行为引起、与具体机器无关的教训。分工与规则见 [ADR 0046](../docs/adr/0046-guardrail-layers-tests-hooks-and-lean-claude-md.md) 与 CONTRIBUTING「护栏三层」段；工具中立的约定在 [`CLAUDE.md`](../CLAUDE.md) 与 [`docs/ai-eng/`](../docs/ai-eng/README.md)。

## Workflow（多子代理编排）

- `scriptPath` 传工具返回的脚本路径（会话 scripts 目录）或有读取权限的文件；大批条目宜写成 JSON 文件由 agent 按组 id 读，`args` 只传元数据。
- 逐 agent 的返回值查运行目录的 `journal.jsonl`：`started` 行记 agentId（可带 label），`result` 行的 `result` 字段记返回值；完成通知里的结果可能被截短。
- 子代理因鉴权或网络故障失败：同一会话内先停掉旧运行，再用同一 `scriptPath` 与 `args` 加 `resumeFromRunId` 重跑，调用序列里最长不变前缀的完成项取缓存、其余重跑；仍在同一工作目录且改动尚在时，重跑的修补员会看到上一位留下的部分改动，简报要写明「在其上完成、不回退」（隔离 worktree 重建后不保证继承）。
- 带 `isolation: worktree` 的 workflow 结束后 `.claude/worktrees/` 可能留下 worktree，`git worktree list` 核对、`git worktree remove` 清掉，否则全仓 grep 出现双份命中。

## Bash 工具

- Bash 工具的 stdin 是不会结束的管道（前后台一样）：读 stdin 的脚本要显式给输入并结束，确定无需输入时接 `< /dev/null`。
- 经 heredoc 传给 `python3 -` 的中文源码出现过「Non-UTF-8 code」：先写成 UTF-8 文件再执行。
- 改文件与 `git commit` 分成两次调用：提交闸门 hook 在整条命令执行之前运行，同一条命令里先改后提交，闸门扫不到新内容（ADR 0046 已记的盲区）。手动核对改动直接运行 `uv run python tools/doc_rules_check.py --uncommitted`，按它的退出码决定是否提交；过滤输出时保留原退出码。

## hooks

- `hooks/commit-gate.sh` 读 stdin 里的工具调用 JSON，空输入按「没有 git commit」放行：`< /dev/null` 只能让它结束，不能用来核对改动；验证 hook 行为要提供含 `tool_input.command`（且含字面 `git commit`）的 JSON 并结束输入。
- `hooks/review-round-gate.sh` 只对命令文本里有字面 `codex exec` 的 Bash 调用做事，读经 `<` 给出的简报文件；被它拦下时先读 `docs/ai-eng/peer-review.md` 第三、四节，再给简报补上「基准」标题或「趋势」一行，不要改写命令形态绕开它。验证它的行为同样要提供含 `tool_input.command` 的 JSON 并结束输入。
