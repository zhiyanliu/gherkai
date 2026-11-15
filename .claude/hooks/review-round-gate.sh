#!/usr/bin/env bash
# Claude Code PreToolUse hook：复核轮闸门（项目级，随仓库入库；.claude/settings.json 挂在 Bash 之前、排在 commit-gate.sh 之后）。
# 做什么：Bash 命令文本以直接的 `codex exec` 调用开头时拦下（exit 2），stderr 指向 tools/codex_review.py：复核轮经它送出，
# 它在执行时读真实的简报文件检查固定标记，并固定只读沙箱。
# 怎样算开头：一个锚定在命令文本开头的正则，允许前导空白、一个左括号、nohup，然后是 `codex` 或以 `/codex` 结尾的路径（路径只由字母、数字与 `_ . / ~ + -` 组成），
# 后接一个空格与 `exec`。只认这一种写法，因为它是送出复核轮的习惯写法；别的位置（cd 或环境变量赋值之后、别的命令之后、
# 引号、heredoc 与注释里）在执行之前从命令文本认不准，认不准就不认、一律放行。不切词，不读任何文件。
# 查看帮助不拦：`codex exec` 或 `codex exec resume` 后面在同一行上紧跟 `--help` 或 `-h` 的调用不会送出任何东西
# （隔着换行的不算：换行之后是另一条命令）。
# 其余放行：命令文本里没有字面 `codex exec`（整份输入里都没有时不启动 python）、PATH 里没有 python3、输入 JSON 为空或
# 不合法；脚本自身出错也放行，经 additionalContext 提示这次调用未经检查。
# 已知盲区：不在开头的直接调用、经包装脚本或别名的调用；只在 Claude Code 里生效。设计理由见 ADR 0046 决策 6。
# 验证本脚本的行为时提供含 tool_input.command 的 JSON 并结束输入：空输入一律放行，退出码 0 不说明拦截生效（stdin 不结束就一直等）。
set -u
input=$(cat)
case "$input" in *"codex exec"*) ;; *) exit 0 ;; esac  # 整份输入里没有字面 `codex exec` 时不启动 python
command -v python3 >/dev/null 2>&1 || exit 0
IFS= read -r -d '' gate_py <<'PY' || true
import json, re, sys
DIRECT = re.compile(r"""\s*\(?\s*(?:nohup\s+)?(?:[\w./~+-]*/)?codex exec(?=\s|\Z)(?!(?:[ \t]+resume)?[ \t]+(?:--help|-h)(?=\s|\Z|[;|&)]))""")
try:
    command = json.load(sys.stdin)["tool_input"]["command"]
except Exception:
    sys.exit(0)  # 输入为空或不合法
if isinstance(command, str) and DIRECT.match(command):
    print("复核轮闸门：复核轮经 tools/codex_review.py 送出，它在执行时检查简报并固定只读沙箱。用法：\n"
          "  首轮：uv run python tools/codex_review.py --round first --brief <简报> --out <输出文件> [--model <模型>] [--effort <推理强度>]\n"
          "  后续轮：uv run python tools/codex_review.py --round followup --brief <简报> --out <输出文件> [--resume <会话 id>] [--model <模型>] [--effort <推理强度>]\n"
          "简报的写法见 docs/ai-eng/peer-review.md 第三、四节，Codex CLI 上的做法见第五节；本会话上下文压缩之后没有读过它的，先读再送。")
    sys.exit(2)
PY
out=$(printf '%s' "$input" | python3 -c "$gate_py" 2>&1)
rc=$?
[ "$rc" -eq 0 ] && exit 0
if [ "$rc" -eq 2 ]; then
  printf '%s\n' "$out" >&2
  exit 2
fi
python3 -c 'import json, sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": sys.argv[1]}}, ensure_ascii=False))' \
  "复核轮闸门这次没能完成检查（退出码 ${rc}），本次调用不阻断，未经检查：$(printf '%s\n' "$out" | tail -n 20)"
exit 0
