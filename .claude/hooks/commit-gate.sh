#!/usr/bin/env bash
# Claude Code PreToolUse hook：提交闸门（ADR 0046 三层护栏的第二层，提交粒度；项目级，随仓库入库；.claude/settings.json 挂在 Bash 之前）。
#
# 只拦 `git commit`：对暂存区里的文件全扫 tools/doc_rules_check.py --staged（规则同 cli/tests 的护栏），命中即 exit 2 阻断
# 这次提交、把命中行回给 agent。不拦别的命令、不拦 amend 以外的任何 git 子命令；只改了 graphify-out/ 的 amend 自然无命中。
# 与 wording-guard.sh 的分工：那边逐次工具调用只看改动的行（即时反馈），这边在提交前把暂存文件整份再扫一遍（兜住绕过
# Edit 工具的改法，如脚本批量改文件）。人类 contributor 用同一份规则的闸门是可选的 tools/git-hooks/pre-commit。
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
export PATH="$PATH:$HOME/.local/bin"
input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c 'import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    print("")' 2>/dev/null)
case "$cmd" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac
command -v uv >/dev/null 2>&1 || exit 0
[ -f tools/doc_rules_check.py ] || exit 0

out=$(uv run --quiet python tools/doc_rules_check.py --staged 2>/dev/null)
rc=$?
if [ "$rc" -eq 1 ]; then
  {
    echo "提交闸门：暂存区里有措辞护栏命中（ADR 0045 决策六 / 悬空指针红线），先改再提交："
    printf '%s\n' "$out"
  } >&2
  exit 2
fi
exit 0
