#!/usr/bin/env bash
# Claude Code PostToolUse hook：人读文本的措辞与悬空指针护栏，写完即查（ADR 0046 三层护栏的第二层；项目级，随仓库入库；
# .claude/settings.json 挂在 Edit / Write / MultiEdit / Bash 之后，与 sync-derived.sh 并列）。
#
# 做什么：对工作区相对 HEAD 的改动运行 tools/doc_rules_check.py --changed——已跟踪文件**只看本次改动的行**、未跟踪文件全扫，
# 规则与扫描面同 cli/tests 的护栏（单一事实源 cli/tests/_doc_rules.py）。命中即 exit 2：stderr 回给 agent，它必须先改
# 再继续，不靠它记得 CLAUDE.md 里的正向要求。
# 为什么只看改动的行：历史欠账另有测试与复盘兜底；hook 只该报「你刚写的」，否则一次大改动进行中会被旧命中刷屏。
# 边界：只在 Claude Code 里生效；人手编辑与 Codex 由 uv run pytest 的同名护栏兜底，可选再挂 tools/git-hooks/pre-commit。
# 脚本自身出错（退出码 2）不阻断：工具问题不该把编辑卡死。
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
export PATH="$PATH:$HOME/.local/bin"
cat >/dev/null
command -v uv >/dev/null 2>&1 || exit 0
[ -f tools/doc_rules_check.py ] || exit 0

out=$(uv run --quiet python tools/doc_rules_check.py --changed 2>/dev/null)
rc=$?
if [ "$rc" -eq 1 ]; then
  {
    echo "措辞护栏命中了本次改动的行（判据与替换口径见 ADR 0045 决策六；悬空指针见 CLAUDE.md 文档纪律）——先改完再继续："
    printf '%s\n' "$out"
  } >&2
  exit 2
fi
exit 0
