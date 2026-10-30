"""worker 自己写 stderr 的出口都经凭据脱敏（ADR 0035 决策 5 的出口清单；与 Midscene worker 的 stderr 出口对称）。

规则本身由 `test_redact.py` 用跨语言用例表 `engines/fixtures/redaction-cases.json` 守；本文件守的是出口接上了规则：
run_scope 的 `log()`、未捕获异常的 fatal 出口（traceback 写出前）、ArtifactUploader 的 `_log`。云端没有 core 的转发层，
worker 的 stderr 原样进 CloudWatch，所以脱敏要在 worker 写出的那一刻完成。Nova Act SDK 自己写的 stdout / stderr 不经这些出口。

样本取用例表里输入与期望不同的条目（即带凭据的输入）：出口写出的文字要含期望的脱敏结果、不含原始输入。另有一条静态差集：
包内引用 `sys.stderr` 的函数只能是上面三处，且每处都调用 `redact_secrets`，新加的出口绕不过去。
"""
from __future__ import annotations

import ast
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

import gherkai_worker_novaact.run_scope as rs
from gherkai_worker_novaact.lib import artifact_upload
from gherkai_worker_novaact.lib.redact import SECRET_MASK, redact_secrets
from gherkai_worker_novaact.user_steps import EX_STEPS_LOAD

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "redaction-cases.json"
CASES = [tuple(c) for c in json.loads(_FIXTURE.read_text(encoding="utf-8"))["cases"]]
SECRET_CASES = [(i, e) for i, e in CASES if i != e]
# 参数化的用例名取它在用例表里的序号（原文很长、还带控制字符，不适合当用例名）
_SECRET_PARAMS = [pytest.param(i, e, id=f"case{n}") for n, (i, e) in enumerate(CASES) if i != e]
_PKG = Path(rs.__file__).resolve().parent


def _assert_redacted(out: str, raw: str, expected: str) -> None:
    assert expected in out, f"应写出脱敏后的 {expected!r}，实际 {out!r}"
    assert raw not in out, f"不应写出原始输入 {raw!r}，实际 {out!r}"


def _plain(sample: str) -> bool:
    """样本能原样嵌进 repr 与单行文本：可打印 ASCII、不含空白、引号与反斜杠（repr 会改写它们）。"""
    return sample.isascii() and sample.isprintable() and not any(c in sample for c in " '\"\\")


def _sample(pred) -> tuple[str, str]:
    return next((i, e) for i, e in SECRET_CASES if i.startswith("https://") and _plain(i) and pred(i))


def test_secret_samples_cover_all_three_rules():
    """防止样本被筛空后出口用例全部空转。"""
    assert any("@" in i for i, _ in SECRET_CASES), "userinfo 样本"
    assert any("x-amz-signature=" in i.lower() for i, _ in SECRET_CASES), "签名参数样本"
    assert any("/remote-endpoint/" in i for i, _ in SECRET_CASES), "设备端点样本"


@pytest.mark.parametrize(("raw", "expected"), _SECRET_PARAMS)
def test_log_redacts_before_writing_stderr(raw, expected, capsys):
    rs.log(f"worker: {raw}")
    out = capsys.readouterr().err
    assert out.startswith("worker: ") and out.endswith("\n"), out
    _assert_redacted(out, raw, expected)


def test_log_call_site_release_failure_message_is_redacted(capsys):
    """真实调用点：释放出错那一行把异常文本原样拼进日志，凭据要在写出时被盖住。"""
    raw, expected = _sample(lambda i: "/remote-endpoint/" in i)
    session = rs._BrowserSession(region="us-east-1", logs_dir=None, sink=None, scope_id="s1", request_name="n")

    def boom():
        raise RuntimeError(f"连接被关闭：{raw}")

    assert session._step("AgentCore 会话", boom) is False
    out = capsys.readouterr().err
    assert "释放出错" in out, out
    _assert_redacted(out, raw, expected)


def test_steps_dir_load_failure_line_is_redacted(monkeypatch, capsys):
    """main() 的 steps 加载失败行：目录路径取自 GHERKAI_STEPS_DIR，路径里带设备端点令牌与隧道令牌参数。"""
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)  # main() 会装 fatal 出口，测试结束还原
    endpoint, _ = _sample(lambda i: "/remote-endpoint/" in i)
    query, _ = _sample(lambda i: "&gherkai_tunnel_token=" in i)
    steps_dir = endpoint.split("amazonaws.com", 1)[1] + "/" + query.rsplit("/", 1)[1]  # 不存在的目录；不含 :// 免得被路径归一化
    monkeypatch.setenv("GHERKAI_STEPS_DIR", steps_dir)
    assert rs.main() == EX_STEPS_LOAD
    out = capsys.readouterr().err
    assert "steps 目录不存在" in out, out
    _assert_redacted(out, steps_dir, redact_secrets(steps_dir))
    assert f"/remote-endpoint/{SECRET_MASK}" in out and f"gherkai_tunnel_token={SECRET_MASK}" in out, out


@pytest.mark.parametrize(("raw", "expected"), _SECRET_PARAMS)
def test_fatal_hook_redacts_traceback(raw, expected, capsys):
    """未捕获异常的 traceback 整段经脱敏：消息与被链接的上游异常里的凭据都被盖住，traceback 的结构照旧。"""
    try:
        try:
            raise OSError(f"上游：{raw}")
        except OSError as inner:
            raise RuntimeError(f"worker 失败：{raw}") from inner
    except RuntimeError as e:
        rs._redacting_excepthook(type(e), e, e.__traceback__)
    out = capsys.readouterr().err
    assert out.startswith("Traceback (most recent call last):"), out
    assert "OSError: 上游：" in out and "RuntimeError: worker 失败：" in out, out
    assert out.count(expected) >= 2, out
    assert raw not in out, out


def test_main_installs_fatal_hook(monkeypatch):
    """fatal 出口在 main() 第一步装上：三条入口（python -m、console script、直接运行模块）都经 main()。"""
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)
    monkeypatch.setenv("GHERKAI_STEPS_DIR", "/nonexistent-gherkai-steps-dir")
    assert rs.main() == EX_STEPS_LOAD
    assert sys.excepthook is rs._redacting_excepthook


def test_fatal_from_real_entry_is_redacted():
    """真入口子进程：未捕获异常由解释器交给 sys.excepthook 写出，这是进程级行为，进程内单测看不到。

    取一个不碰 AWS 的启动期失败：JOB_S3_URI 不是 s3:// 地址时读 job 即抛出，异常文本原样带着这个值。三个样本（userinfo、签名参数、
    设备端点令牌）以空格拼接，各自的脱敏结果互不影响（前提先核）。"""
    picks = [_sample(lambda i: "@" in i),
             _sample(lambda i: "x-amz-signature=" in i.lower()),
             _sample(lambda i: "/remote-endpoint/" in i)]
    raw = " ".join(i for i, _ in picks)
    assert redact_secrets(raw) == " ".join(e for _, e in picks)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("GHERKAI_", "EVENTS_", "ARTIFACT_", "JOB_")) and k != "RUN_ID"}
    env["JOB_S3_URI"] = raw
    proc = subprocess.run([sys.executable, "-m", "gherkai_worker_novaact"], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, env=env, timeout=120)
    assert proc.returncode == 1, proc.stderr
    assert "Traceback (most recent call last):" in proc.stderr and "ValueError: JobSource" in proc.stderr, proc.stderr
    for sample, expected in picks:
        _assert_redacted(proc.stderr, sample, expected)
    assert "u1:p1" not in proc.stderr and "deadbeef" not in proc.stderr and "abcDEF123xyz" not in proc.stderr


def test_fatal_hook_keeps_the_keyboard_interrupt_exit():
    """未捕获的 KeyboardInterrupt 经钩子后仍按 SIGINT 结束（与解释器缺省一致），被链接的上游异常里的凭据照样被盖住。
    退出方式是解释器的真实行为，进程内单测看不到，所以起真子进程。"""
    raw, expected = _sample(lambda i: "@" in i)
    code = ("import os, sys\n"
            "from gherkai_worker_novaact.run_scope import _redacting_excepthook\n"
            "sys.excepthook = _redacting_excepthook\n"
            "try:\n"
            "    raise RuntimeError(os.environ['GHERKAI_TEST_SAMPLE'])\n"
            "except RuntimeError:\n"
            "    raise KeyboardInterrupt()\n")
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120,
                          env={**os.environ, "GHERKAI_TEST_SAMPLE": raw})
    assert proc.returncode == -signal.SIGINT, proc.stderr
    assert "KeyboardInterrupt" in proc.stderr, proc.stderr
    _assert_redacted(proc.stderr, raw, expected)


# ---- 静态差集：包内写 stderr 的函数只能是这三处，且每处都调用 redact_secrets ----

_STDERR_OUTLETS = {
    ("run_scope.py", "log"),
    ("run_scope.py", "_redacting_excepthook"),
    ("lib/artifact_upload.py", "_log"),
}


def _stderr_users() -> tuple[set[tuple[str, str]], list[str]]:
    """返回 (引用 sys.stderr 的 (文件, 函数) 集合, 其它直接写 stderr 的写法清单)。"""
    users: set[tuple[str, str]] = set()
    others: list[str] = []
    for path in sorted(_PKG.rglob("*.py")):
        rel = path.relative_to(_PKG).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        stack: list[str] = []

        class _V(ast.NodeVisitor):
            def _fn(self, node):
                stack.append(node.name)
                self.generic_visit(node)
                stack.pop()

            visit_FunctionDef = visit_AsyncFunctionDef = _fn

            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name) and node.value.id == "sys" and node.attr in ("stderr", "__stderr__"):
                    users.add((rel, stack[-1] if stack else "<module>"))
                self.generic_visit(node)

            def visit_Call(self, node):
                f = node.func
                if isinstance(f, ast.Name) and f.id == "print" and any(k.arg == "file" for k in node.keywords):
                    others.append(f"{rel}:{node.lineno} print(file=...)")
                if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "traceback" \
                        and f.attr.startswith("print_"):
                    others.append(f"{rel}:{node.lineno} traceback.{f.attr}")
                self.generic_visit(node)

            def visit_Import(self, node):
                if any(a.name == "logging" for a in node.names):
                    others.append(f"{rel}:{node.lineno} import logging")
                self.generic_visit(node)

        _V().visit(tree)
    return users, others


def test_stderr_outlets_are_exactly_the_redacting_ones():
    users, others = _stderr_users()
    assert users == _STDERR_OUTLETS, "包内写 stderr 的函数有变化：新出口要经 redact_secrets，并登记进本测试的清单"
    assert others == [], others


@pytest.mark.parametrize(("rel", "func"), sorted(_STDERR_OUTLETS))
def test_each_stderr_outlet_calls_redact_secrets(rel, func):
    tree = ast.parse((_PKG / rel).read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func)
    calls = {c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
    assert "redact_secrets" in calls, f"{rel} 的 {func} 写 stderr 前没有经 redact_secrets"


@pytest.mark.parametrize(("raw", "expected"), _SECRET_PARAMS)
def test_uploader_log_redacts_before_writing_stderr(raw, expected, capsys):
    artifact_upload._log(f"证据截图上传失败：{raw}")
    _assert_redacted(capsys.readouterr().err, raw, expected)
