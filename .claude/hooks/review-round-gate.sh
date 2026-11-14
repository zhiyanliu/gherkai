#!/usr/bin/env bash
# Claude Code PreToolUse hook：复核轮闸门（项目级，随仓库入库；.claude/settings.json 挂在 Bash 之前、排在 commit-gate.sh 之后）。
# 做什么：命令里每个 `codex exec` 调用经 `<` 读入的简报，正文提到「复核」或「闭合」时检查一项：不带 resume 的调用要有一行
# 顶格、以 1 到 6 个 # 加空格开头、含「基准」的标题（只认这一种写法），带 resume 的续接轮要有一行同时写出「趋势」与数字；
# 缺了即 exit 2，stderr 指回细则。
# 为什么：细则在 docs/ai-eng/peer-review.md，只在被读到时才在上下文里；上下文压缩之后 agent 凭摘要继续送复核轮，简报缺了
# 基准与趋势，复核循环就没有停下来的依据。所以在送出复核轮这一动作上检查。
# 判断不了即放行：命令里没有字面 `codex exec`、简报不经 `<` 从文件读入（heredoc、here-string、管道）、文件读不到、正文不提
# 复核与闭合、输入 JSON 为空或不合法、切词失败；脚本自身出错也放行，经 additionalContext 提示这次调用未经检查。
# 已知盲区（认不出即放行，不补）：经包装脚本或别名发起、`bash -c '…'` 引号里的调用、简报用相对路径而工作目录不是项目根、
# 路径里带 ~ 或变量（不做展开）；
# 全新上下文的闭合轮缺「趋势」不检查；只查两项有没有，不查写得对不对；只覆盖经 Codex CLI 发起的复核，子代理复核不经过这里。
# 设计理由与被拒方案见 ADR 0046 决策 6。
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
input=$(cat)
case "$input" in *"codex exec"*) ;; *) exit 0 ;; esac  # 先在 shell 里筛一次：整份输入里没有这两个词时不启动 python
command -v python3 >/dev/null 2>&1 || exit 0
IFS= read -r -d '' gate_py <<'PY' || true
import json
import re
import shlex
import sys

OPERATOR_CHARS = "();<>|&\n"
BASELINE = re.compile(r"^#{1,6} .*基准", re.M)
NEEDS = {
    False: "基准段：一行顶格、以 # 加空格开头、含「基准」的标题（如「## 基准：受审对象要做到什么」；缩进的标题不算），标题下写受审对象必须成立的性质",
    True: "趋势：一行同时写出「趋势」与逐轮意见的数目（如「趋势：基准之内的意见 5、3、1 条，逐轮变少、变轻」）",
}


def calls(cmd):
    """按出现顺序列出每个 `codex exec` 调用的（经 `<` 读入的简报路径或 None, 是否带 resume）。"""
    lex = shlex.shlex(cmd.replace("\\\n", " "), posix=True, punctuation_chars=OPERATOR_CHARS)
    lex.whitespace = " \t\r"  # 换行与 ; 一样结束命令，作为运算符切出
    lex.whitespace_split = True
    lex.commenters = ""
    tokens = list(lex)
    out = []
    for i, tok in enumerate(tokens[:-1]):
        if not ((tok == "codex" or tok.endswith("/codex")) and tokens[i + 1] == "exec"):
            continue
        brief, resume = None, False
        for j in range(i + 2, len(tokens)):
            t = tokens[j]
            if t and set(t) <= set(";|&\n)"):
                break  # ; && || | & 换行 ) 结束这条调用；含 < 或 > 的重定向不结束
            if t == "resume":
                resume = True
            elif t == "<" and j + 1 < len(tokens):
                brief = tokens[j + 1]  # 只认单个 <；<< 与 <<< 切出的是另一个词
        out.append((brief, resume))
    return out


def has_item(text, resume):
    if resume:
        return any("趋势" in line and re.search(r"\d", line) for line in text.splitlines())
    return BASELINE.search(text) is not None


try:
    command = json.load(sys.stdin)["tool_input"]["command"]
except Exception:
    sys.exit(0)  # 输入为空或不合法
if not isinstance(command, str) or "codex exec" not in command:
    sys.exit(0)
try:
    found = calls(command)
except ValueError:
    sys.exit(0)  # 切词失败（引号不配对等）
missing = []
for brief, resume in found:
    if brief is None:
        continue
    try:
        with open(brief, encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
    except OSError:
        continue
    if ("复核" in text or "闭合" in text) and not has_item(text, resume):
        missing.append(f"- 简报 {brief}（{'带' if resume else '不带'} resume）缺少{NEEDS[resume]}")
if missing:
    print("复核轮闸门：这一轮复核的简报缺少让复核循环能停下来的内容，补上再送：")
    print("\n".join(missing))
    print("细则见 docs/ai-eng/peer-review.md 第三、四节（基准在第三节「基准内联」条，趋势在第四节「每轮送出下一轮之前看趋势」条）；"
          "本会话上下文压缩之后没有读过它的，先读再送。")
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
  "复核轮闸门这次没能完成检查（退出码 ${rc}），本次调用不阻断，这一轮的简报尚未经过检查：$(printf '%s\n' "$out" | tail -n 20)"
exit 0
