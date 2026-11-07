#!/usr/bin/env bash
# Claude Code PreToolUse hook：提交闸门（ADR 0046 三层护栏的第二层，提交粒度；项目级，随仓库入库；.claude/settings.json 挂在 Bash 之前）。
#
# 只拦命令文本里带 `git commit` 的 Bash 调用，按要提交的内容整份扫 tools/doc_rules_check.py（规则同 cli/tests 的护栏），
# 命中即 exit 2 阻断这次提交、把命中行回给 agent；不拦别的命令。扫哪一组文件由命令的形态决定：
# - 常规形态（前面没有 `git add`、也不带下述选项与路径参数的 `git commit`，含 `git commit -F <msg>` 与 `--amend`）：
#   `--staged`，按暂存区（index）里将要提交的版本扫、不读工作区。
# - 提交内容在闸门运行时还没进暂存区的形态：同一条命令里 `git add`（或同义的 `git stage`）出现在 `git commit` 之前，
#   或 commit 带 `-a` / `--all`、`-i` / `--include`、`-o` / `--only`、`--pathspec-from-file`、路径参数（含 `--` 之后的）。
#   PreToolUse 在整条命令执行之前运行，这些内容不在暂存区的名单上，改为调用 `--uncommitted`：暂存区、工作区相对 HEAD 的
#   改动与未跟踪文件的并集（graphify-out/ 除外）。工作区里不属于本次提交的文件有命中时同样阻断，命中都是真实违规，先改再提交；
#   graphify 回填写法 `git add graphify-out && git commit --amend --no-edit` 在工作区只剩 graphify-out/ 的改动时照常放行。
# 形态由下面的 python3 片段用 shlex 切词识别：带值的选项（`-m` / `-F` / `-C` / `-c` / `-t` 与对应的长选项）的值不当成路径参数，
# 组合短选项遇到带值的字母即停（`-am` 含 `-a`，`-ma` 是内容为「a」的 `-m`）；`bash -c '…'` 这类引号里的命令文本递归识别。
# 切词失败（如引号不配对）时按超集处理：闸门判断不出形态，只扫暂存区可能漏掉要提交的内容；扫超集的最坏情况是多拦下这次
# 提交，而拦下的依据仍是真实命中。
# 超集是补强，不是保证：它只能扫闸门运行时已经存在的版本，即暂存区里的与工作区里的。覆盖成立的前提是同一条命令在把文件
# 纳入提交的那一步（`git add`，或带 `-a`、路径参数这类选项的 `git commit` 本身）之前不改写它，不用 `git add -f` 加入被
# .gitignore 忽略的文件，也不换 GIT_INDEX_FILE。识别依据只有命令文本，下列写法认不出或超集覆盖不到，闸门放行，由测试层
# 兜底（完整清单见 ADR 0046「边界与已知盲区」）：
# - 认不出的写法：命令里没有字面 `git commit`（如 `git -C <dir> commit`、git 别名）时闸门不运行；`git` 与 `add` 之间带
#   全局选项的 add（如 `git -C <dir> add`），以及 `git add` 以外改动暂存区的命令（如 `git mv`、`git apply --cached`），
#   与 `git commit` 写在同一条命令里时仍按常规形态只扫暂存区。
# - 超集的前提不成立的写法：同一条命令先改写文件，再 `git add` 与 `git commit`，或再用 `git commit -a`、带路径参数的
#   `git commit` 提交，提交的是闸门运行时还不存在的版本；`git add -f` 加入的被忽略文件不在超集里（未跟踪文件的列举
#   遵守 .gitignore）；`GIT_INDEX_FILE=… git commit` 提交的是另一份 index，闸门读的是默认 index。
# 要保证提交内容本身经过检查，只能在提交用的 index 就位之后检查：PreToolUse 运行时这份 index 还不存在，这一层由可选的
# tools/git-hooks/pre-commit 承担（人类 contributor 用的也是它，规则相同）；启用了它的 clone 里，上述写法的提交同样经它检查。
# 与 wording-guard.sh 的分工：那边逐次工具调用只看改动的行（即时反馈），这边在提交前把要提交的内容整份再扫一遍（兜住绕过
# Edit 工具的改法，如脚本批量改文件）。
# 脚本自身出错（退出码不是 0 或 1）不阻断提交：错误输出经 hookSpecificOutput.additionalContext 作为提示回给 agent，
# 让它知道这次提交未经措辞检查；只有退出码 1（有命中）才阻断。
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
export PATH="$PATH:$HOME/.local/bin"
input=$(cat)
IFS= read -r -d '' form_py <<'PY' || true
import json
import shlex
import sys

VALUE_SHORT = "mFCct"   # 带值的短选项：值是同一个词的剩余部分，没有剩余时是下一个词
ATTACHED_SHORT = "Su"   # 值可选的短选项：值只能紧贴在后面，同一个词的剩余部分都是值
TRIGGER_SHORT = "aio"   # -a / -i / -o
TRIGGER_LONG = ("--all", "--include", "--only", "--pathspec-from-file")  # git 接受唯一前缀，按前缀匹配
VALUE_LONG = {"--message", "--file", "--reuse-message", "--reedit-message", "--template", "--author", "--date",
              "--cleanup", "--fixup", "--squash", "--trailer"}
OPERATOR_CHARS = "();<>|&\n"


def split(cmd):
    lex = shlex.shlex(cmd.replace("\\\n", " "), posix=True, punctuation_chars=OPERATOR_CHARS)
    lex.whitespace = " \t\r"  # 换行与 ; 一样分隔命令，作为运算符切出
    lex.whitespace_split = True
    lex.commenters = ""       # 井号只在词首才起注释，由 commit_args 按词判断
    return list(lex)


def is_operator(tok):
    return tok != "" and all(c in OPERATOR_CHARS for c in tok)


def commit_args(tokens, j):
    """从 `git commit` 之后的第 j 个词起读到这条命令结束，返回（是否命中超集形态, 结束处的下标）。"""
    trigger = False
    after_dashes = False
    while j < len(tokens):
        tok = tokens[j]
        if is_operator(tok):
            if "<" in tok or ">" in tok:
                j += 2  # 重定向：连同其目标一起跳过
                continue
            break
        if tok.startswith("#"):  # 注释：跳到行尾
            while j < len(tokens) and not (is_operator(tokens[j]) and "\n" in tokens[j]):
                j += 1
            break
        if after_dashes:
            trigger = True
        elif tok == "--":
            after_dashes = True
        elif tok.startswith("--"):
            name = tok.split("=", 1)[0]
            if any(full.startswith(name) for full in TRIGGER_LONG):
                trigger = True
            elif name in VALUE_LONG and "=" not in tok:
                j += 1
        elif tok.startswith("-") and len(tok) > 1:
            for k, c in enumerate(tok[1:], 1):
                if c in TRIGGER_SHORT:
                    trigger = True
                elif c in VALUE_SHORT:
                    if k == len(tok) - 1:
                        j += 1
                    break
                elif c in ATTACHED_SHORT:
                    break
        elif not (tok.isdigit() and j + 1 < len(tokens) and tokens[j + 1][:1] in ("<", ">")):
            trigger = True  # 路径参数；`2>&1` 里的文件描述符编号除外
        j += 1
    return trigger, j


def events(cmd, depth=0):
    """按出现顺序列出命令里的 ("add", None) 与 ("commit", 是否带超集选项或路径参数)。"""
    tokens = split(cmd)
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        is_git = tok == "git" or tok.endswith("/git")  # 也认带目录前缀的 git 可执行文件路径
        if is_git and i + 1 < len(tokens) and tokens[i + 1] in ("add", "stage"):
            out.append(("add", None))
            i += 2
            continue
        if is_git and i + 1 < len(tokens) and tokens[i + 1] == "commit":
            trigger, i = commit_args(tokens, i + 2)
            out.append(("commit", trigger))
            continue
        if "git " in tok and not is_operator(tok) and depth < 3:
            out.extend(events(tok, depth + 1))
        i += 1
    return out


def mode(cmd):
    if "git commit" not in cmd:
        return "skip"
    try:
        seen_add = False
        for kind, trigger in events(cmd):
            if kind == "add":
                seen_add = True
            elif seen_add or trigger:
                return "--uncommitted"
        return "--staged"
    except Exception:  # 切词失败（引号不配对等）
        return "--uncommitted"


try:
    command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    command = ""
print(mode(command if isinstance(command, str) else ""))
PY
mode=$(printf '%s' "$input" | python3 -c "$form_py" 2>/dev/null)
hint=""
case "$mode" in
  --staged) found="暂存区里有措辞护栏命中" ;;
  --uncommitted)
    found="这条命令要提交的内容在检查时还没有全部进入暂存区，已整份扫描暂存区、工作区改动与未跟踪文件，其中有措辞护栏命中"
    hint="（命中的文件不在本次提交里时同样先改）" ;;
  *) exit 0 ;;
esac
command -v uv >/dev/null 2>&1 || exit 0
[ -f tools/doc_rules_check.py ] || exit 0

err=$(mktemp "${TMPDIR:-/tmp}/commit-gate.XXXXXX") || exit 0
trap 'rm -f "$err"' EXIT
out=$(uv run --quiet python tools/doc_rules_check.py "$mode" 2>"$err")
rc=$?
if [ "$rc" -eq 1 ]; then
  {
    echo "提交闸门：${found}（ADR 0045 决策六 / 悬空指针红线），先改再提交${hint}："
    printf '%s\n' "$out"
  } >&2
  exit 2
fi
if [ "$rc" -ne 0 ]; then
  python3 -c 'import json, sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": sys.argv[1]}}, ensure_ascii=False))' \
    "提交闸门这次没能完成检查（tools/doc_rules_check.py ${mode} 退出码 ${rc}），本次提交不阻断，这次提交的内容尚未经过措辞检查：$(tail -n 20 "$err")"
fi
exit 0
