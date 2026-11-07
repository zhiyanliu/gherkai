"""`tools/doc_rules_check.py` 与提交闸门 `.claude/hooks/commit-gate.sh` 的单测（ADR 0046 决策三：写完即查与提交闸门）。

`--uncommitted` 的扫描集合在临时 git 仓库里构造；命令行入口的退出码直接对本仓库调用；提交闸门按命令形态选哪种模式，
用一个只记录参数的替身 `uv` 核对，不真的扫描。`--staged` 与「指定的 markdown 不存在」两项在 `test_code_comments.py`。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _doc_rules import REPO

GUARD = REPO / "tools" / "doc_rules_check.py"
HOOK = REPO / ".claude" / "hooks" / "commit-gate.sh"


@pytest.fixture
def git_repo(tmp_path, monkeypatch):
    """带一个初始提交的临时仓库；在 git hook 里执行测试时不沿用外层仓库的 GIT_DIR 等变量。"""
    for var in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.delenv(var, raising=False)
    _git(tmp_path, "init", "-q")
    return tmp_path


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
                    "-c", "core.hooksPath=/dev/null", *args], cwd=cwd, check=True, capture_output=True)


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _load_guard_cli():
    spec = importlib.util.spec_from_file_location("doc_rules_check", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_uncommitted_mode_scans_the_union_of_index_working_tree_and_untracked(git_repo, monkeypatch):
    """`--uncommitted` 取暂存区、工作区相对 HEAD 的改动与未跟踪文件的并集：暂存后又改了工作区的文件两版都扫，暂存后在工作区
    删掉的只扫暂存版，两版相同的只扫一次；没有改动的文件、graphify-out/ 与 .gitignore 忽略的文件不在其中。"""
    for rel in ("a.md", "b.md", "c.md", "d.md", "f.md", "graphify-out/g.md"):
        _write(git_repo, rel, "提交的版本\n")
    _write(git_repo, ".gitignore", "ignored.md\n")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-q", "-m", "init")

    _write(git_repo, "a.md", "暂存的版本\n")
    _write(git_repo, "b.md", "暂存后删掉\n")
    _write(git_repo, "f.md", "暂存后未再改\n")
    _write(git_repo, "graphify-out/g.md", "图谱的改动\n")
    _git(git_repo, "add", "a.md", "b.md", "f.md", "graphify-out/g.md")
    _write(git_repo, "a.md", "工作区的版本\n")
    (git_repo / "b.md").unlink()
    _write(git_repo, "c.md", "只在工作区改\n")
    _write(git_repo, "e.md", "未跟踪\n")
    _write(git_repo, "说明.md", "非 ASCII 文件名\n")
    _write(git_repo, "graphify-out/new.md", "未跟踪的图谱文件\n")
    _write(git_repo, "ignored.md", "被忽略\n")

    guard = _load_guard_cli()
    monkeypatch.setattr(guard, "REPO", git_repo)
    assert sorted(guard._uncommitted_targets()) == sorted([
        (git_repo / "a.md", None, "暂存的版本\n"),
        (git_repo / "a.md", None, "工作区的版本\n"),
        (git_repo / "b.md", None, "暂存后删掉\n"),
        (git_repo / "c.md", None, "只在工作区改\n"),
        (git_repo / "e.md", None, "未跟踪\n"),
        (git_repo / "f.md", None, "暂存后未再改\n"),
        (git_repo / "说明.md", None, "非 ASCII 文件名\n"),
    ])


def test_uncommitted_mode_reports_hits_outside_the_index(git_repo):
    """命令行入口端到端：只在工作区改动、尚未暂存的命中，`--staged` 放行而 `--uncommitted` 报出；两版共有的命中只报一次，
    graphify-out/ 里的命中不报。规则与扫描面取自复制进临时仓库的 `_doc_rules.py`。"""
    for rel in ("tools/doc_rules_check.py", "cli/tests/_doc_rules.py"):
        (git_repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, git_repo / rel)
    _write(git_repo, "docs/internals/x.md", "# 标题\n\n干净的正文。\n")
    _write(git_repo, "docs/internals/y.md", "# 标题\n\n干净的正文。\n")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-q", "-m", "init")

    _write(git_repo, "docs/internals/x.md", "# 标题\n\n判据 = 范围\n")
    _write(git_repo, "docs/internals/y.md", "# 标题\n\n结论 = 已知\n")
    _git(git_repo, "add", "docs/internals/y.md")
    _write(git_repo, "docs/internals/y.md", "# 标题\n\n结论 = 已知\n\n补一段干净的正文。\n")
    _write(git_repo, "graphify-out/z.md", "判据 = 范围\n")

    def check(mode: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(git_repo / "tools" / "doc_rules_check.py"), mode],
                              cwd=git_repo, capture_output=True, text=True)

    staged = check("--staged")
    assert staged.returncode == 1 and staged.stdout.splitlines() == [
        "docs/internals/y.md:3: 符号当谓语 · 结论 = 已知"], staged.stdout + staged.stderr
    uncommitted = check("--uncommitted")
    assert uncommitted.returncode == 1, uncommitted.stderr
    assert sorted(uncommitted.stdout.splitlines()) == ["docs/internals/x.md:3: 符号当谓语 · 判据 = 范围",
                                                       "docs/internals/y.md:3: 符号当谓语 · 结论 = 已知"]


@pytest.mark.parametrize("argv", [["--bogus"], ["--uncommited"], ["--staged", "docs/README.md"], ["-x"]])
def test_unrecognized_options_exit_2(argv):
    """拼错的选项与模式加路径的组合以退出码 2 结束：当成路径跳过会以退出码 0 结束，hook 会把它当成检查已通过。"""
    proc = subprocess.run([sys.executable, str(GUARD), *argv], cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 2 and "无法识别的参数" in proc.stderr, proc.stderr


def test_missing_path_exits_2_even_outside_every_scan_face():
    """指定的路径不存在时，不论能否归到某个扫描面都以退出码 2 结束（这里的 `.txt` 不属于任何扫描面）。"""
    proc = subprocess.run([sys.executable, str(GUARD), "no-such-dir/no-such-file.txt"],
                          cwd=REPO, capture_output=True, text=True)
    assert proc.returncode == 2 and "no-such-dir/no-such-file.txt" in proc.stderr, proc.stderr


@pytest.fixture
def gate(tmp_path):
    """在替身项目目录里执行提交闸门：替身 `uv` 把收到的参数写进记录文件，按 FAKE_RC 退出、按 FAKE_OUT 输出命中行。"""
    project = tmp_path / "project"
    (project / "tools").mkdir(parents=True)
    (project / "tools" / "doc_rules_check.py").write_text("", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text('#!/bin/sh\nprintf \'%s\\n\' "$*" > "$RECORD"\nprintf \'%s\' "${FAKE_OUT:-}"\n'
                       'exit "${FAKE_RC:-0}"\n', encoding="utf-8")
    fake_uv.chmod(0o755)
    record = tmp_path / "record"

    def run(command: str, fake_rc: int = 0, fake_out: str = "") -> tuple[subprocess.CompletedProcess, str | None]:
        record.unlink(missing_ok=True)
        env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "RECORD": str(record),
               "CLAUDE_PROJECT_DIR": str(project), "FAKE_RC": str(fake_rc), "FAKE_OUT": fake_out}
        proc = subprocess.run(["bash", str(HOOK)], input=json.dumps({"tool_input": {"command": command}}),
                              env=env, capture_output=True, text=True)
        called = record.read_text(encoding="utf-8").split()[-1] if record.exists() else None
        return proc, called

    return run


@pytest.mark.parametrize(("command", "mode"), [
    ("git commit -F /tmp/msg", "--staged"),
    ("git commit --amend --no-edit", "--staged"),
    ("git commit -ma", "--staged"),
    ("git commit -F msg -- ", "--staged"),
    ("git commit -F msg 2>&1 | tail -5", "--staged"),
    ("git commit -F msg && git log -1", "--staged"),
    ("git commit -F msg\ngit log -1", "--staged"),
    ("git commit -m 'git add 的说明'", "--staged"),
    ("git commit --author 'A <a@example.com>' -F msg", "--staged"),
    ("git commit -uno -F msg", "--staged"),
    ("git commit -F msg  # 提交说明", "--staged"),
    ("git add -A && git commit -F msg", "--uncommitted"),
    ("git stage -A && git commit -F msg", "--uncommitted"),
    ("git add graphify-out && git commit --amend --no-edit", "--uncommitted"),
    ("git commit -F msg; git add graphify-out; git commit --amend --no-edit", "--uncommitted"),
    ("git commit -a", "--uncommitted"),
    ("git commit --all -F msg", "--uncommitted"),
    ("git commit -am 'msg'", "--uncommitted"),
    ("git commit -i -F msg docs/x.md", "--uncommitted"),
    ("git commit --only -F msg docs/x.md", "--uncommitted"),
    ("git commit -F msg docs/x.md", "--uncommitted"),
    ("git commit -mfix docs/x.md", "--uncommitted"),
    ("git commit -F msg -- docs/x.md", "--uncommitted"),
    ("git commit --pathspec-from-file=paths.txt", "--uncommitted"),
    ("git commit --pathspec-fr=paths.txt", "--uncommitted"),
    ("bash -c 'git add -A && git commit -F msg'", "--uncommitted"),
    ("/usr/bin/git commit -a", "--uncommitted"),
    ("/usr/bin/git commit -F msg", "--staged"),
    ("git commit -F - <<'EOF'\n说明里提到 git add\nEOF", "--staged"),
    ("git commit -F msg docs/x.md > /tmp/out 2>&1", "--uncommitted"),
    ("git commit -F msg 2>/dev/null docs/x.md", "--uncommitted"),
    ('git commit -m "unterminated', "--uncommitted"),
    ("git status", None),
    ("git -C sub commit -a", None),
])
def test_commit_gate_picks_the_scan_by_command_form(gate, command, mode):
    """提交内容在闸门运行时还没进暂存区的形态（先 add 再 commit、`-a` / `-i` / `-o`、路径参数）改为调用 `--uncommitted`，
    常规形态仍调用 `--staged`，切词失败按超集处理；命令文本里没有 `git commit` 时不调用检查（`git -C` 属已登记的盲区）。"""
    proc, called = gate(command)
    assert proc.returncode == 0, proc.stderr
    assert called == mode


def test_commit_gate_blocks_on_hits_and_reports_tool_failures(gate):
    """检查有命中（退出码 1）时阻断并回显命中行，超集形态另提示不在本次提交里的文件同样先改；检查自身出错（退出码 2）时
    不阻断，经 additionalContext 告知 agent。"""
    blocked, _ = gate("git commit -a", fake_rc=1, fake_out="docs/x.md:3: 符号当谓语 · 判据 = 范围\n")
    assert blocked.returncode == 2
    assert "docs/x.md:3" in blocked.stderr and "还没有全部进入暂存区" in blocked.stderr
    assert "不在本次提交里时同样先改" in blocked.stderr
    staged, _ = gate("git commit -F msg", fake_rc=1, fake_out="docs/x.md:3: 符号当谓语 · 判据 = 范围\n")
    assert staged.returncode == 2 and "暂存区里有措辞护栏命中" in staged.stderr
    assert "不在本次提交里" not in staged.stderr  # 常规形态下命中的文件都在本次提交里
    failed, called = gate("git commit -F msg", fake_rc=2)
    assert failed.returncode == 0 and called == "--staged"
    context = json.loads(failed.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "没能完成检查" in context and "--staged" in context
