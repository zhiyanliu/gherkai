"""复核轮闸门 `.claude/hooks/review-round-gate.sh` 的单测（ADR 0046 决策 6）。

用子进程执行脚本、经 stdin 传入 hook 的 JSON；按退出码与 stderr 判定放行或拦下。闸门只看命令文本开头是不是直接的
`codex exec` 调用，不读文件，所以命令里出现的简报路径都不必存在。另核对它在 `.claude/settings.json` 里的登记位置，
以及 `.claude/hooks/` 下每个脚本都已登记。
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
from _doc_rules import REPO

HOOK = REPO / ".claude" / "hooks" / "review-round-gate.sh"
SETTINGS = REPO / ".claude" / "settings.json"


def _gate(stdin: str, project: Path, path_prefix: str = "", path: str | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project),
           "PATH": path if path is not None else f"{path_prefix}{os.environ.get('PATH', '')}"}
    return subprocess.run(["/bin/bash", str(HOOK)], input=stdin, env=env, capture_output=True, text=True)


def _run(command: str, project: Path, **extra) -> subprocess.CompletedProcess:
    return _gate(json.dumps({"tool_input": {"command": command, **extra}}), project)


@pytest.mark.parametrize("command", [
    "codex exec -s read-only -o out - < brief.md",
    'codex exec resume abc -c sandbox_mode="read-only" -o out - < brief.md > log 2>&1; cat out',
    "codex exec",                                          # exec 之后是文本结束
    "codex exec\n",
    "  codex exec -s read-only -",
    "\ncodex exec -",
    "( nohup codex exec -s read-only -o out - < brief.md > log 2>&1 & )",
    "(codex exec - < brief.md)",
    "  ( nohup codex exec - < brief.md > log 2>&1 & )",   # 左括号前有空白
    "nohup codex exec - < brief.md &",
    "/usr/local/bin/codex exec - < brief.md",
    "codex exec -m x --help",                              # 只有紧跟在后面的 --help 才算查看帮助
    "(codex exec\n--help) < brief.md",                     # 换行之后的 --help 是另一条命令，前面那条照样送出
    "codex exec\nresume --help",
    "codex exec resume\n--help",
    "codex exec --helpful - < brief.md",                   # 不是 --help
    "~/bin/codex exec -",
    "( nohup /opt/codex/bin/codex exec -o out - < brief.md > log 2>&1 & )",
])
def test_direct_call_at_the_start_is_blocked(tmp_path, command):
    proc = _run(command, tmp_path)
    assert proc.returncode == 2, proc.stderr
    assert proc.stdout == ""
    assert "tools/codex_review.py" in proc.stderr


@pytest.mark.parametrize("command", [
    "cd /x && codex exec - < brief.md",                    # 前面有 cd
    "FOO=1 codex exec - < brief.md",                       # 前面有环境变量赋值
    "echo hi; codex exec - < brief.md",                    # 前面有别的命令
    "echo hi\ncodex exec - < brief.md",
    "echo;/usr/local/bin/codex exec -",
    "true&&/usr/local/bin/codex exec -",
    "codex exec --help",                                 # 查看帮助不是送出复核轮
    "codex exec -h",
    "codex exec resume --help",
    "( nohup /opt/homebrew/bin/codex exec --help | head -20 )",
    "codex exec --help; echo done",
    "#/usr/local/bin/codex exec --help",                 # 注释：井号不是路径里的字符
    "CODEX=/usr/local/bin/codex exec printf EXECUTED",   # 环境变量赋值后由 shell 的 exec 执行别的程序
    "cat|/usr/local/bin/codex exec -",
    "(true)/usr/local/bin/codex exec -",
    "$(/usr/local/bin/codex exec -)",
    "echo>/tmp/codex exec -",                              # 重定向的目标，不是调用
    "cat</tmp/codex exec -",
    "echo 'codex exec - < brief.md'",                      # 引号里
    "bash -c 'codex exec - < brief.md'",
    '"codex" exec -',
    "'/opt/bin/codex exec -'",                             # 整段在单引号里的路径
    '"/opt/bin/codex exec -"',                             # 整段在双引号里的路径
    "nohupcodex exec -",                                   # nohup 之后没有空白
    "cat > brief.md <<'EOF'\ncodex exec - < brief.md\nEOF",  # heredoc 正文里
    "# codex exec - < brief.md\necho done",                # 注释里
    "((codex exec -))",                                    # 两个左括号
    "$(codex exec -)",
    "mycodex exec -",
    "/usr/local/bin/mycodex exec -",
    "codex execute",                                       # exec 之后不是空白
    "codex exec-x",
    "uv run python tools/codex_review.py --round first --brief brief.md --out out.md",
])
def test_other_forms_pass(tmp_path, command):
    proc = _run(command, tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == "" and proc.stdout == ""


def test_block_message_points_to_the_sending_tool_and_the_guide(tmp_path):
    proc = _run("codex exec -o out - < brief.md", tmp_path)
    assert proc.returncode == 2
    assert "复核轮经 tools/codex_review.py 送出，它在执行时检查简报并固定只读沙箱" in proc.stderr
    assert "uv run python tools/codex_review.py --round first --brief <简报> --out <输出文件> [--model" in proc.stderr
    assert ("uv run python tools/codex_review.py --round followup --brief <简报> --out <输出文件> [--resume <会话 id>]"
            in proc.stderr)
    assert "docs/ai-eng/peer-review.md 第三、四节" in proc.stderr and "上下文压缩之后" in proc.stderr


def test_only_the_command_is_checked_not_the_whole_input(tmp_path):
    """shell 的预筛看整段 JSON；判定只看 tool_input.command。"""
    proc = _run("git status", tmp_path, description="codex exec 复核")
    assert proc.returncode == 0 and proc.stderr == "" and proc.stdout == ""


@pytest.mark.parametrize("stdin", [
    "",
    "not json but codex exec",
    '["codex exec"]',
    '{"tool_input": {"command": ["codex exec -"]}}',
    '{"tool_input": "codex exec -"}',
])
def test_empty_or_malformed_input_passes(tmp_path, stdin):
    proc = _gate(stdin, tmp_path)
    assert proc.returncode == 0 and proc.stderr == "" and proc.stdout == ""


def _python_stub(tmp_path: Path, body: str) -> str:
    """在 PATH 最前面放一个替身 python3，返回要加在 PATH 前面的目录。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "python3"
    fake.write_text(f"#!/bin/sh\n{body}\nexec {shlex.quote(sys.executable)} \"$@\"\n", encoding="utf-8")
    fake.chmod(0o755)
    return f"{bin_dir}{os.pathsep}"


@pytest.mark.parametrize(("command", "started"), [
    ("git status", False),
    ("echo codex; echo exec", False),
    ("codex  exec - < brief.md", False),                   # 没有字面 `codex exec`
    ("cd /x && codex exec -", True),
    ("codex exec --help", True),
])
def test_other_commands_do_not_start_python(tmp_path, command, started):
    record = tmp_path / "python-called"
    prefix = _python_stub(tmp_path, f"touch {shlex.quote(str(record))}")
    _gate(json.dumps({"tool_input": {"command": command}}), tmp_path, path_prefix=prefix)
    assert record.exists() == started


def test_missing_python_passes_silently(tmp_path):
    """PATH 里没有 python3 时直接放行，不报「找不到命令」。"""
    bin_dir = tmp_path / "bin-no-python"
    bin_dir.mkdir()
    (bin_dir / "cat").symlink_to(subprocess.run(["sh", "-c", "command -v cat"], capture_output=True,
                                                text=True, check=True).stdout.strip())
    proc = _gate(json.dumps({"tool_input": {"command": "codex exec -"}}), tmp_path, path=str(bin_dir))
    assert proc.returncode == 0 and proc.stderr == "" and proc.stdout == ""


def test_script_error_passes_with_a_hint(tmp_path):
    """检查用的 python 异常退出（替身 python3 第一次被调用时报错退出，之后转交真正的解释器）时放行，
    经 additionalContext 提示这次调用未经检查。"""
    marker = tmp_path / "failed-once"
    prefix = _python_stub(tmp_path, f'if [ ! -e {shlex.quote(str(marker))} ]; then touch {shlex.quote(str(marker))}; '
                                    'echo "Traceback: boom" >&2; exit 1; fi')
    proc = _gate(json.dumps({"tool_input": {"command": "codex exec -"}}), tmp_path, path_prefix=prefix)
    assert proc.returncode == 0 and proc.stderr == ""
    context = json.loads(proc.stdout)["hookSpecificOutput"]
    assert context["hookEventName"] == "PreToolUse"
    assert "没能完成检查（退出码 1）" in context["additionalContext"] and "未经检查" in context["additionalContext"]
    assert "Traceback: boom" in context["additionalContext"]


def test_registered_after_commit_gate_with_timeout():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    groups = [g for g in settings["hooks"]["PreToolUse"] if g.get("matcher") == "Bash"]
    assert len(groups) == 1
    commands = [h["command"] for h in groups[0]["hooks"]]
    names = [c.rsplit("/", 1)[-1] for c in commands]
    assert names.index("review-round-gate.sh") > names.index("commit-gate.sh")
    entry = groups[0]["hooks"][names.index("review-round-gate.sh")]
    assert entry["timeout"] == 30 and entry["type"] == "command"
    assert entry["command"] == '"$CLAUDE_PROJECT_DIR"/.claude/hooks/review-round-gate.sh'


def test_every_hook_script_is_registered():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    registered = {h["command"].rsplit("/", 1)[-1] for groups in settings["hooks"].values()
                  for g in groups for h in g["hooks"]}
    scripts = {p.name for p in (REPO / ".claude" / "hooks").iterdir() if p.is_file()}
    assert "review-round-gate.sh" in scripts
    assert scripts - registered == set()
    assert os.access(HOOK, os.X_OK)
