"""复核轮闸门 `.claude/hooks/review-round-gate.sh` 的单测（ADR 0046 决策 6）。

用子进程执行脚本、经 stdin 传入 hook 的 JSON，简报放在 tmp_path；按退出码与 stderr 判定放行或拦下。
另核对它在 `.claude/settings.json` 里的登记位置，以及 `.claude/hooks/` 下每个脚本都已登记。
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

BAD = "# 复核简报\n\n请复核下面的改动，结尾一句总判定。\n"
GOOD_FIRST = "# 复核简报\n\n## 基准：受审对象要做到什么\n\n- 性质一\n"
GOOD_RESUME = "闭合轮：上一轮意见是否处置到位。\n\n趋势：基准之内的意见 5、3、1 条，逐轮变少。\n"
UNRELATED = "# 普通任务\n\n请写一个函数。\n"


@pytest.fixture
def briefs(tmp_path):
    """把几份简报写进 tmp_path，返回按名字取路径（已按 shell 规则加引号）的函数。"""
    contents = {"bad": BAD, "first": GOOD_FIRST, "resume": GOOD_RESUME, "unrelated": UNRELATED,
                "both": GOOD_FIRST + GOOD_RESUME, "round#2": BAD}
    for name, text in contents.items():
        (tmp_path / f"{name}.md").write_text(text, encoding="utf-8")
    return lambda name: shlex.quote(str(tmp_path / f"{name}.md"))


def _gate(stdin: str, project: Path, path_prefix: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project),
           "PATH": f"{path_prefix}{os.environ.get('PATH', '')}"}
    return subprocess.run(["bash", str(HOOK)], input=stdin, env=env, capture_output=True, text=True)


def _run(command: str, project: Path, **extra) -> subprocess.CompletedProcess:
    return _gate(json.dumps({"tool_input": {"command": command, **extra}}), project)


@pytest.mark.parametrize(("template", "blocked"), [
    ("( nohup codex exec -s read-only -m m -o out - < {bad} > log 2>&1 & )", True),
    ("( nohup codex exec -s read-only -m m -o out - < {first} > log 2>&1 & )", False),
    ('codex exec resume abc -c sandbox_mode="read-only" -o out - < {bad} > log 2>&1; echo DONE; cat out', True),
    ('codex exec resume abc -c sandbox_mode="read-only" -o out - < {resume} > log 2>&1; echo DONE; cat out', False),
    ("codex exec resume abc -o out - < {first}", True),   # 续接轮只有基准、没有趋势
    ("codex exec -o out - < {resume}", True),             # 不带 resume 的调用只有趋势、没有基准
    ("codex exec resume abc - < {both}", False),
    ("cd /x && codex exec -s read-only -o out - < {bad}", True),
    ("cd /x && codex exec -s read-only -o out - < {first}", False),
    ("codex exec --help; cat < {bad}", False),             # 重定向属于 cat
    ("codex exec --help && cat < {bad}", False),
    ("codex exec --help || cat < {bad}", False),
    ("codex exec --help & cat < {bad}", False),
    ("codex exec --help\ncat < {bad}", False),
    ("(codex exec --help) < {bad}", False),               # 重定向在子 shell 的括号之外
    ("codex exec - < {bad} | tee log", True),
    ("codex exec - <<'EOF'\n请复核这些改动\nEOF", False),  # heredoc
    ("codex exec - <<< {bad}", False),                     # here-string 传入的是路径文本本身
    ("cat {bad} | codex exec -", False),                  # 管道
    ("codex exec -o out '请复核这些改动'", False),        # 没有重定向
    ("codex exec - < {first}; codex exec resume abc - < {bad}", True),
    ("codex exec - < {bad}; codex exec resume abc - < {resume}", True),
    ("codex exec - < {first}; codex exec resume abc - < {resume}", False),
    ("/usr/local/bin/codex exec -s read-only -o out - < {bad}", True),
    ("mycodex exec - < {bad}", False),
    ("codex login < {bad}; codex exec --help", False),     # codex 后面不是 exec
    ("codex exec - <", False),                             # < 后面没有路径
    ("codex exec - < {unrelated}", False),                 # 正文不提复核与闭合
    ("codex exec - < {tmp}/no-such-brief.md", False),      # 文件读不到
    ("codex exec - < {tmp}", False),                       # 路径是目录
    ("codex exec - < {tmp}/round#2.md", True),             # 词中间的井号不是注释，路径完整
    ("codex exec -c '' - < {bad}", True),                  # 空字符串参数不结束这条调用
    ('codex exec - < {bad} "unterminated', False),         # 切词失败
    ("echo 'codex exec - < {bad}'", False),                # 引号里的文本不是调用
    ("bash -c 'codex exec - < {bad}'", False),             # 已登记的盲区
    ("codex  exec - < {bad}", False),                      # 没有字面 `codex exec`
])
def test_gate_decides_by_command_form_and_brief(tmp_path, briefs, template, blocked):
    command = template.format(bad=briefs("bad"), first=briefs("first"), resume=briefs("resume"),
                              both=briefs("both"), unrelated=briefs("unrelated"),
                              tmp=shlex.quote(str(tmp_path)))
    proc = _run(command, tmp_path)
    assert proc.returncode == (2 if blocked else 0), proc.stderr
    assert bool(proc.stderr) == blocked, proc.stderr
    assert proc.stdout == "", proc.stdout  # 没有走到脚本出错的分支


@pytest.mark.parametrize(("text", "resume", "blocked"), [
    ("闭合轮\n\n## 基准\n", False, False),
    ("闭合轮，只确认一处措辞。\n", False, True),           # 只提「闭合」也检查
    ("复核\n\n# 基准\n", False, False),
    ("\ufeff## 基准\n\n请复核\n", False, False),          # 文件开头的 BOM 不影响首行标题
    ("复核\n\n###### 基准\n", False, False),
    ("复核\n\n####### 基准\n", False, True),               # 七个井号不是标题
    ("复核\n\n##基准\n", False, True),                     # 井号后没有空格
    ("复核\n\n  ## 基准\n", False, True),                  # 不在行首
    ("复核\n\n基准：受审对象要做到什么\n", False, True),   # 不是标题
    ("复核\n\n## 受审对象\n\n正文提到基准\n", False, True),
    ("闭合\n\n趋势：意见逐轮变少\n", True, True),          # 趋势一行没有数字
    ("闭合\n\n趋势：意见逐轮变少\n第 3 轮\n", True, True),  # 数字不在同一行
    ("闭合\n\n上一轮 3 条意见，本轮 1 条：趋势收敛\n", True, False),
])
def test_gate_checks_the_item_that_matches_the_call(tmp_path, text, resume, blocked):
    (tmp_path / "brief.md").write_text(text, encoding="utf-8")
    command = "codex exec resume abc - < brief.md" if resume else "codex exec - < brief.md"
    proc = _run(command, tmp_path)  # 相对路径按 CLAUDE_PROJECT_DIR 解析
    assert proc.returncode == (2 if blocked else 0), proc.stderr


def test_brief_with_invalid_utf8_is_still_checked(tmp_path):
    """简报里夹着非 UTF-8 字节时照常检查，不落到脚本出错的放行分支。"""
    (tmp_path / "brief.md").write_bytes(BAD.encode("utf-8") + b"\xff\xfe\n")
    proc = _run("codex exec - < brief.md", tmp_path)
    assert proc.returncode == 2 and proc.stdout == "", proc.stderr


def test_block_message_names_the_brief_the_item_and_the_guide(tmp_path, briefs):
    first = _run(f"codex exec - < {briefs('bad')}", tmp_path)
    assert first.returncode == 2
    assert str(tmp_path / "bad.md") in first.stderr and "不带 resume" in first.stderr
    assert "基准" in first.stderr and "## 基准：" in first.stderr
    assert "docs/ai-eng/peer-review.md 第三、四节" in first.stderr and "上下文压缩之后" in first.stderr
    resumed = _run(f"codex exec - < {briefs('first')}; codex exec resume abc - < {briefs('bad')}", tmp_path)
    assert resumed.returncode == 2
    assert str(tmp_path / "bad.md") in resumed.stderr and str(tmp_path / "first.md") not in resumed.stderr
    assert "带 resume" in resumed.stderr and "趋势：" in resumed.stderr


def test_literal_check_uses_the_command_not_the_whole_input(tmp_path, briefs):
    """shell 的预筛看整段 JSON；只有 tool_input.command 里有字面 `codex exec` 才检查。"""
    proc = _run(f"codex  exec - < {briefs('bad')}", tmp_path, description="codex exec 复核")
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("stdin", [
    "",
    "not json but codex exec",
    '["codex exec"]',
    '{"tool_input": {"command": ["codex exec"]}}',
    '{"tool_input": "codex exec - < brief.md"}',
])
def test_empty_or_malformed_input_passes(tmp_path, stdin):
    (tmp_path / "brief.md").write_text(BAD, encoding="utf-8")
    proc = _gate(stdin, tmp_path)
    assert proc.returncode == 0 and proc.stderr == "" and proc.stdout == ""


@pytest.fixture
def python_recorder(tmp_path):
    """在 PATH 最前面放一个替身 python3：记下被调用过，再转交真正的解释器。"""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    record = tmp_path / "python-called"
    fake = bin_dir / "python3"
    fake.write_text(f'#!/bin/sh\ntouch {shlex.quote(str(record))}\nexec {shlex.quote(sys.executable)} "$@"\n',
                    encoding="utf-8")
    fake.chmod(0o755)
    return f"{bin_dir}{os.pathsep}", record


@pytest.mark.parametrize(("command", "started"), [
    ("git status", False),
    ("echo codex; echo exec", False),
    ("codex exec --help", True),
])
def test_other_commands_do_not_start_python(tmp_path, python_recorder, command, started):
    prefix, record = python_recorder
    proc = _gate(json.dumps({"tool_input": {"command": command}}), tmp_path, path_prefix=prefix)
    assert proc.returncode == 0, proc.stderr
    assert record.exists() == started


def test_missing_python_passes_silently(tmp_path, briefs):
    """PATH 里没有 python3 时直接放行，不报「找不到命令」。"""
    bin_dir = tmp_path / "bin-no-python"
    bin_dir.mkdir()
    for tool in ("cat", "tail"):
        (bin_dir / tool).symlink_to(subprocess.run(["sh", "-c", f"command -v {tool}"], capture_output=True,
                                                   text=True, check=True).stdout.strip())
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), "PATH": str(bin_dir)}
    stdin = json.dumps({"tool_input": {"command": f"codex exec - < {briefs('bad')}"}})
    proc = subprocess.run(["/bin/bash", str(HOOK)], input=stdin, env=env, capture_output=True, text=True)
    assert proc.returncode == 0 and proc.stderr == "" and proc.stdout == ""


def test_script_error_passes_with_a_hint(tmp_path):
    """内嵌 python 抛出异常（这里是路径里的空字符让 open 报 ValueError）时放行，经 additionalContext 提示未经检查。"""
    proc = _run("codex exec - < brief\x00.md", tmp_path)
    assert proc.returncode == 0 and proc.stderr == ""
    context = json.loads(proc.stdout)["hookSpecificOutput"]
    assert context["hookEventName"] == "PreToolUse"
    assert "没能完成检查" in context["additionalContext"] and "尚未经过检查" in context["additionalContext"]
    assert "ValueError" in context["additionalContext"]


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
