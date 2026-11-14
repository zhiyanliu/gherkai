"""`tools/codex_review.py` 的单测（ADR 0046 决策 6）：简报缺固定标记或读不到时 codex 一次都不被调用、退出码 2、提示可读；
通过时传给 codex 的参数与两种调用形态逐项一致，标准输入是简报全文，日志落在指定文件，退出码原样传回。

用子进程执行工具；替身 codex 放在临时目录、经 PATH 排在最前面，它记下收到的参数与标准输入，按 `-o` 写出输出文件，
往 stdout 打印一行 `session id:`、往 stderr 打印一行，再按环境变量给出的退出码结束。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from _doc_rules import REPO

TOOL = REPO / "tools" / "codex_review.py"

BAD = "# 复核简报\n\n请复核下面的改动，结尾一句总判定。\n"
GOOD_FIRST = "# 复核简报\n\n## 基准：受审对象要做到什么\n\n- 性质一\n"
GOOD_RESUME = "闭合轮：上一轮意见是否处置到位。\n\n趋势：基准之内的意见 5、3、1 条，逐轮变少。\n"

FAKE_CODEX = """\
import json, os, signal, sys
args = sys.argv[1:]
data = sys.stdin.buffer.read()
with open(os.environ["FAKE_CODEX_RECORD"], "w", encoding="utf-8") as f:
    json.dump({"args": args, "stdin": data.decode("latin-1")}, f)
if "-o" in args:
    with open(args[args.index("-o") + 1], "w", encoding="utf-8") as f:
        f.write("复核意见\\n")
if os.environ.get("FAKE_CODEX_SESSION", "1") == "1":
    print("session id: 0199-abc")
print("替身 codex 的 stderr", file=sys.stderr)
sys.stdout.flush()
if os.environ.get("FAKE_CODEX_SIGNAL"):
    os.kill(os.getpid(), signal.SIGTERM)
sys.exit(int(os.environ.get("FAKE_CODEX_RC", "0")))
"""


@pytest.fixture
def env(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "codex"
    fake.write_text(f"#!{sys.executable}\n{FAKE_CODEX}", encoding="utf-8")
    fake.chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "FAKE_CODEX_RECORD": str(tmp_path / "record.json")}


def _brief(tmp_path: Path, text: str | bytes) -> Path:
    path = tmp_path / "brief.md"
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


def _run(env: dict, *args: str, **extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], env={**env, **extra}, capture_output=True, text=True)


def _record(tmp_path: Path) -> dict | None:
    path = tmp_path / "record.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@pytest.mark.parametrize(("text", "resume", "passes"), [
    (GOOD_FIRST, False, True),
    (BAD, False, False),
    (GOOD_RESUME, True, True),
    (BAD, True, False),
    (GOOD_FIRST, True, False),                             # 续接轮只有基准、没有趋势
    (GOOD_RESUME, False, False),                           # 不带 resume 的轮次只有趋势、没有基准
    (GOOD_FIRST + GOOD_RESUME, True, True),
    ("# 基准\n", False, True),
    ("###### 基准\n", False, True),
    ("####### 基准\n", False, False),                     # 七个井号不是标题
    ("##基准\n", False, False),                            # 井号后没有空格
    ("  ## 基准\n", False, False),                         # 不在行首
    ("基准：受审对象要做到什么\n", False, False),          # 不是标题
    ("## 受审对象\n\n正文提到基准\n", False, False),
    ("\ufeff## 基准\n", False, True),                 # 文件开头的 BOM 不影响首行标题
    ("复核简报\r## 基准\r", False, True),            # 只用 CR 换行：标题在行首，算有
    ("# 复核简报\r正文提到基准\r", False, False),     # 只用 CR 换行：基准不在标题行里，算缺
    ("# 复核简报\r\n## 基准\r\n", False, True),      # CRLF 换行
    ("趋势：意见逐轮变少\n", True, False),                 # 趋势一行没有数字
    ("趋势：意见逐轮变少\n第 3 轮\n", True, False),        # 数字不在同一行
    ("上一轮 3 条意见，本轮 1 条：趋势收敛\n", True, True),
    ("普通任务，请写一个函数。\n", False, False),          # 不判断是不是复核简报，一律检查
])
def test_marks_decide_whether_codex_is_called(tmp_path, env, text, resume, passes):
    brief = _brief(tmp_path, text)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out), *(["--resume", "sid"] if resume else []))
    assert proc.returncode == (0 if passes else 2), proc.stderr
    assert (_record(tmp_path) is not None) == passes
    assert Path(f"{out}.log").exists() == passes


@pytest.mark.parametrize(("resume", "item", "example"), [
    (False, "缺少基准段", "## 基准："),
    (True, "缺少趋势", "趋势："),
])
def test_missing_mark_message_names_the_item_the_example_and_the_guide(tmp_path, env, resume, item, example):
    brief = _brief(tmp_path, BAD)
    proc = _run(env, "--brief", str(brief), "--out", str(tmp_path / "out.md"), *(["--resume", "sid"] if resume else []))
    assert proc.returncode == 2 and proc.stdout == ""
    assert str(brief) in proc.stderr and item in proc.stderr and example in proc.stderr
    assert ("（带 --resume）" if resume else "（不带 --resume）") in proc.stderr
    assert "docs/ai-eng/peer-review.md 第三、四节" in proc.stderr and "上下文压缩之后没有读过它的，先读再送" in proc.stderr
    assert "本轮没有送出" in proc.stderr


@pytest.mark.parametrize("target", ["no-such-brief.md", "."])
def test_unreadable_brief_is_a_usage_error(tmp_path, env, target):
    brief = tmp_path / target
    proc = _run(env, "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 2 and proc.stdout == ""
    assert f"简报 {brief} 读不到" in proc.stderr and "本轮没有送出" in proc.stderr
    assert _record(tmp_path) is None


def test_first_round_call_form_stdin_log_and_output(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    record = _record(tmp_path)
    assert record["args"] == ["exec", "-s", "read-only", "-o", str(out), "-"]
    assert record["stdin"].encode("latin-1") == GOOD_FIRST.encode("utf-8")
    log = Path(f"{out}.log").read_text(encoding="utf-8")
    assert "session id: 0199-abc" in log and "替身 codex 的 stderr" in log
    assert proc.stdout == f"session id: 0199-abc\n{out}\n"
    assert out.read_text(encoding="utf-8") == "复核意见\n"


def test_first_round_passes_model_and_effort(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out), "--model", "m1", "--effort", "ultra")
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path)["args"] == ["exec", "-s", "read-only", "-m", "m1", "-c", 'model_reasoning_effort="ultra"',
                                         "-o", str(out), "-"]


def test_resume_call_form_and_explicit_log(tmp_path, env):
    brief = _brief(tmp_path, GOOD_RESUME)
    out, log = tmp_path / "out.md", tmp_path / "round-2.log"
    proc = _run(env, "--brief", str(brief), "--out", str(out), "--resume", "0199-abc", "--log", str(log),
                "--model", "m1", "--effort", "ultra")
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path)["args"] == ["exec", "resume", "0199-abc", "-c", 'sandbox_mode="read-only"',
                                         "-m", "m1", "-c", 'model_reasoning_effort="ultra"', "-o", str(out), "-"]
    assert "替身 codex 的 stderr" in log.read_text(encoding="utf-8")
    assert not Path(f"{out}.log").exists()


def test_resume_without_model_and_effort(tmp_path, env):
    brief = _brief(tmp_path, GOOD_RESUME)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out), "--resume", "0199-abc")
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path)["args"] == ["exec", "resume", "0199-abc", "-c", 'sandbox_mode="read-only"',
                                         "-o", str(out), "-"]


def test_brief_bytes_are_passed_unchanged(tmp_path, env):
    """BOM 与非法字节只在检查时容忍，传给 codex 的仍是文件的原始字节。"""
    raw = "\ufeff## 基准\n".encode("utf-8") + b"\xff\xfe\n"
    brief = _brief(tmp_path, raw)
    proc = _run(env, "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path)["stdin"].encode("latin-1") == raw


@pytest.mark.parametrize(("extra", "rc"), [
    ({"FAKE_CODEX_RC": "3"}, 3),
    ({"FAKE_CODEX_RC": "2"}, 2),
    ({"FAKE_CODEX_SIGNAL": "1"}, 128 + 15),
])
def test_exit_code_is_passed_through(tmp_path, env, extra, rc):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out), **extra)
    assert proc.returncode == rc
    assert _record(tmp_path) is not None and proc.stdout.endswith(f"{out}\n")


def test_without_session_line_only_the_output_path_is_printed(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out), FAKE_CODEX_SESSION="0")
    assert proc.returncode == 0 and proc.stdout == f"{out}\n"


def test_missing_codex_is_a_usage_error(tmp_path, env):
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, "--brief", str(brief), "--out", str(out), PATH=str(empty))
    assert proc.returncode == 2 and proc.stdout == ""
    assert "PATH 里找不到 codex" in proc.stderr
    assert not Path(f"{out}.log").exists()


def test_unwritable_log_is_a_usage_error(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    log = tmp_path / "no-such-dir" / "round.log"
    proc = _run(env, "--brief", str(brief), "--out", str(tmp_path / "out.md"), "--log", str(log))
    assert proc.returncode == 2 and f"日志文件 {log} 无法写入" in proc.stderr
    assert _record(tmp_path) is None
