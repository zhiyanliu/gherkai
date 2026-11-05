#!/usr/bin/env bash
# Claude Code PreToolUse hook：提交闸门（ADR 0046 三层护栏的第二层，提交粒度；项目级，随仓库入库；.claude/settings.json 挂在 Bash 之前）。
#
# 只拦 `git commit`：按暂存区（index）里将要提交的版本整份扫 tools/doc_rules_check.py --staged、不读工作区（规则同 cli/tests 的护栏），命中即 exit 2 阻断
# 这次提交、把命中行回给 agent。不拦别的命令、不拦 amend 以外的任何 git 子命令；只改了 graphify-out/ 的 amend 自然无命中。
# 与 wording-guard.sh 的分工：那边逐次工具调用只看改动的行（即时反馈），这边在提交前把暂存区里将要提交的版本整份再扫一遍（兜住绕过
# Edit 工具的改法，如脚本批量改文件）。人类 contributor 用同一份规则的闸门是可选的 tools/git-hooks/pre-commit。
# 脚本自身出错（退出码不是 0 或 1）不阻断提交：错误输出经 hookSpecificOutput.additionalContext 作为提示回给 agent，
# 让它知道这次提交未经措辞检查；只有退出码 1（有命中）才阻断。
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

err=$(mktemp "${TMPDIR:-/tmp}/commit-gate.XXXXXX") || exit 0
trap 'rm -f "$err"' EXIT
out=$(uv run --quiet python tools/doc_rules_check.py --staged 2>"$err")
rc=$?
if [ "$rc" -eq 1 ]; then
  {
    echo "提交闸门：暂存区里有措辞护栏命中（ADR 0045 决策六 / 悬空指针红线），先改再提交："
    printf '%s\n' "$out"
  } >&2
  exit 2
fi
if [ "$rc" -ne 0 ]; then
  python3 -c 'import json, sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": sys.argv[1]}}, ensure_ascii=False))' \
    "提交闸门这次没能完成检查（tools/doc_rules_check.py 退出码 ${rc}），本次提交不阻断，暂存的内容尚未经过措辞检查：$(tail -n 20 "$err")"
fi
exit 0
