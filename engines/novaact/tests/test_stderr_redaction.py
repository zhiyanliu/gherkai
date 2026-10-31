"""worker 自己写 stderr 的出口都经凭据脱敏（ADR 0035 决策 5 的出口清单；与 Midscene worker 的 stderr 出口对称）。

规则本身由 `test_redact.py` 用跨语言用例表 `engines/fixtures/redaction-cases.json` 守；本文件守的是出口接上了规则：
run_scope 的 `log()`、未捕获异常的 fatal 出口（traceback 写出前）、ArtifactUploader 的 `_log`。云端没有 core 的转发层，
worker 的 stderr 原样进 CloudWatch，所以脱敏要在 worker 写出的那一刻完成。Nova Act SDK 自己写的 stdout / stderr 不经这些出口。

样本取用例表里输入与期望不同的条目（即带凭据的输入）：出口写出的文字要含期望的脱敏结果、不含原始输入。另有一条静态差集：
包内能写到 stderr 的出口只能是上面三处，且每处自己调用 `redact_secrets`；新加的出口只要用的是静态差集一节开头注释所列的写法
就会被判出。静态检查只核对能直接解析到的引用，已知无法识别的写法列在那段注释里，不穷尽。出口按模块路径加类名与函数名标识，
类里同名的方法不并入模块级的函数。
"""
from __future__ import annotations

import ast
import functools
import json
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
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
    """未捕获的 KeyboardInterrupt 经钩子后仍按 SIGINT 结束（与解释器缺省一致），被链接的上游异常里的凭据仍被脱敏处理。
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


@pytest.mark.parametrize(("raw", "expected"), _SECRET_PARAMS)
def test_uploader_log_redacts_before_writing_stderr(raw, expected, capsys):
    artifact_upload._log(f"证据截图上传失败：{raw}")
    _assert_redacted(capsys.readouterr().err, raw, expected)


# ---- 静态差集：包内写 stderr 的出口恰为这三处，且每处自己调用 redact_secrets ----
#
# 出口按「模块相对路径加类名与函数名的点分路径」标识，类里同名的方法、嵌套函数与 lambda 各是一个出口，逐一检查它自己的函数体
# （不含嵌套定义）里有没有 redact_secrets 的调用。计入出口的写法：经 import 别名或模块属性取到的 sys.stderr 与 sys.__stderr__
# （`import sys as s`、`from sys import stderr as e`、`getattr(sys, "stderr")` 都算）；带 file= 的 print（静态分析未必能确定目标流，
# 一律计入）；对文件描述符 2 的 os.write、os.writev、os.fdopen、io.FileIO 与 open（含 io.open）；调用 sys.excepthook 或
# sys.__excepthook__。logging、traceback.print_*、warnings.warn 绕过这些出口直接写 stderr；星号导入、把 sys 模块当作值使用、
# 动态导入（__import__、importlib.import_module 与 importlib.__import__，不论导入什么都算）、以常量键 "sys" 从 sys.modules 取 sys、
# 读取 sys.__dict__、同一个名字在文件内由 import 绑定到不同对象（本检查解析 import 时不区分作用域、整个文件共用一张表；与 print、
# open、getattr、__import__ 同名而所指不是该内建函数也算）、类体内的 import（名字成为类属性，经 self 一类的实例访问时追踪不到，
# 不论导入什么都算）、把上面计入出口的写函数（print、os.write 一类的文件描述符写函数、sys.excepthook 与 sys.__excepthook__）当作值
# 使用（赋给变量、作为参数或返回值、放进容器、取它的属性，凡不是直接调用都算，此后经别的名字调用时核对不了实参），这几种静态分析
# 无法追踪。以上两类无法登记为出口，出现即报。拒绝用例在真实源码的内存副本上做一处改动，再交给同一套检查。已知无法识别的写法
# （不穷尽）：文件描述符来自变量（含 os.dup(2) 的结果）、print 以外经 stream= 一类参数传入的流、在模块里以赋值或 def 重新绑定
# redact_secrets 这个名字、子进程继承的 stderr、经 getattr 以 stderr 与 __stderr__ 之外的常量名取成员、把 sys 之外的模块或上面
# 写函数以外的库函数当作值使用这类间接取法（如 `getattr(sys, "__excepthook__")`、`getattr(os, "write")`、`m = os`、
# `f = __import__`、`p = traceback.print_exc`、`w = warnings.warn`）；检查的是出口自己调用了 redact_secrets，不核对脱敏后的值
# 是否流到写出处，写出结果由上面的运行期用例逐处核对。

_STDERR_OUTLETS = {
    ("run_scope.py", "log"),
    ("run_scope.py", "_redacting_excepthook"),
    ("lib/artifact_upload.py", "_log"),
}

_UNREGISTERED = "未登记的出口"
_GONE = "登记的出口不再写 stderr"
_DUPLICATE = "同一路径定义了多次"
_UNREDACTED = "出口自己没有调用 redact_secrets"
_UNREGISTRABLE = "无法登记的写法"


@functools.cache
def _package_sources() -> dict[str, str]:
    """包内全部 .py 的源码，键是相对包目录的路径。"""
    return {p.relative_to(_PKG).as_posix(): p.read_text(encoding="utf-8") for p in sorted(_PKG.rglob("*.py"))}


_PKG_NAME = rs.__package__
_REDACT = f"{redact_secrets.__module__}.{redact_secrets.__name__}"
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
_BUILTINS = frozenset({"print", "open", "getattr", "__import__"})
_STDERR_ATTRS = frozenset({"stderr", "__stderr__"})
_EXCEPTHOOKS = frozenset({"excepthook", "__excepthook__"})
_FD_WRITERS = frozenset({"os.write", "os.writev", "os.fdopen", "builtins.open", "io.open", "io.FileIO"})
_DYNAMIC_IMPORTS = frozenset({"builtins.__import__", "importlib.import_module", "importlib.__import__"})
_BYPASS_MODULES = frozenset({"logging"})
_BYPASS_CALLS = ("traceback.print_", "warnings.warn", "warnings.showwarning")


@dataclass(frozen=True)
class _Outlet:
    rel: str
    qualname: str           # 类名与函数名的点分路径，模块顶层记 <module>
    lineno: int             # 定义所在行，模块顶层记 0
    forms: tuple[str, ...]  # 认出的写法，带行号
    redacts: bool           # 它自己的函数体（不含嵌套定义）里调用了 redact_secrets


def _import_bindings(rel: str, tree: ast.Module) -> tuple[dict[str, str], list[str]]:
    """import 绑定的名字到所指对象的完整路径：`import sys as s` 得 s 指 sys，`from sys import stderr as e` 得 e 指
    sys.stderr，相对导入按文件所在的包展开。整个文件共用一张表、不区分作用域，函数里的 import 也算进来。

    同一个名字在文件内绑定到不同对象时（两处 import 所指不同，或与 print、open、getattr、__import__ 同名而所指不是该内建函数），
    表里的一项无法代表各处的引用，取哪一项都可能把写 stderr 的那一处认成别的对象而漏掉：这个名字不进表，另作为无法登记的写法
    返回（第二项，每条带最早那处 import 的行号）。进表的名字在文件内所指唯一；与它同名的局部变量会被当作它所指的对象，这种误认
    本身只会多报：局部变量的值由赋值处的表达式取得，那个表达式照常检查。"""
    package = ".".join([_PKG_NAME, *rel.split("/")[:-1]])
    bound: dict[str, dict[str, int]] = {}  # 每个名字所指的各个对象，以及各自最早那处 import 的行号

    def bind(name: str, target: str, lineno: int) -> None:
        lines = bound.setdefault(name, {})
        lines[target] = min(lineno, lines.get(target, lineno))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.partition(".")[0]
                bind(a.asname or root, a.name if a.asname else root, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")
                base = ".".join([*parts[:len(parts) - node.level + 1], *([node.module] if node.module else [])])
            for a in node.names:
                if a.name != "*":
                    bind(a.asname or a.name, f"{base}.{a.name}", node.lineno)
    names: dict[str, str] = {}
    conflicts: list[str] = []
    for name, lines in sorted(bound.items(), key=lambda item: min(item[1].values())):
        targets = set(lines) | ({f"builtins.{name}"} if name in _BUILTINS else set())
        if len(targets) == 1:
            names[name] = targets.pop()
        else:
            conflicts.append(f"{min(lines.values())} 名字 {name} 在文件内可能指向不同对象：{'、'.join(sorted(targets))}")
    return names, conflicts


def _qualified(node: ast.AST, names: dict[str, str]) -> str | None:
    """Name 或 Attribute 链的完整路径。链根是 import 绑定的名字或几个内建函数时才有，局部变量与表达式的值返回 None。"""
    attrs: list[str] = []
    while isinstance(node, ast.Attribute):
        attrs.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    root = names.get(node.id) or (f"builtins.{node.id}" if node.id in _BUILTINS else None)
    return ".".join([root, *reversed(attrs)]) if root else None


def _sys_member(q: str | None) -> str | None:
    """路径形如 sys.<名字> 时返回那个名字；经别的模块属性取到的 sys 也算（如 run_scope.sys.stderr）。"""
    head, _, last = (q or "").rpartition(".")
    return last if head == "sys" or head.endswith(".sys") else None


def _is_sys_module(q: str | None) -> bool:
    return q is not None and (q == "sys" or q.endswith(".sys"))


def _is_writer(q: str | None) -> bool:
    """计入出口的写函数（直接调用时由 visit_Call 核对实参）：print、_FD_WRITERS 里的函数、sys.excepthook 与 sys.__excepthook__。"""
    return q == "builtins.print" or q in _FD_WRITERS or _sys_member(q) in _EXCEPTHOOKS


def _writes_fd2(call: ast.Call) -> bool:
    """第一个参数（或 fd= / file=）是整数字面量 2。"""
    first = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg in ("fd", "file")), None)
    return isinstance(first, ast.Constant) and type(first.value) is int and first.value == 2


def _calls_redact(scope: ast.AST, names: dict[str, str]) -> bool:
    """作用域自己的语句与表达式里有 redact_secrets 的调用；不进入嵌套的函数、类与 lambda。"""
    todo = list(ast.iter_child_nodes(scope))
    while todo:
        node = todo.pop()
        if isinstance(node, ast.Call) and _qualified(node.func, names) == _REDACT:
            return True
        if not isinstance(node, _SCOPES):
            todo.extend(ast.iter_child_nodes(node))
    return False


class _StderrScan(ast.NodeVisitor):
    """扫一个文件：按作用域记下能写到 stderr 的写法，另记无法登记为出口的写法。"""

    def __init__(self, rel: str, tree: ast.Module):
        self.rel = rel
        self.names, conflicts = _import_bindings(rel, tree)
        self.parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        self.stack: list[tuple[ast.AST, str]] = [(tree, "<module>")]
        self.hits: dict[ast.AST, tuple[str, list[str]]] = {}
        self.bypasses: list[str] = conflicts
        self.visit(tree)

    def outlets(self) -> list[_Outlet]:
        return [_Outlet(self.rel, qual, getattr(scope, "lineno", 0), tuple(forms), _calls_redact(scope, self.names))
                for scope, (qual, forms) in self.hits.items()]

    def _hit(self, node: ast.AST, form: str) -> None:
        scope, qual = self.stack[-1]
        self.hits.setdefault(scope, (qual, []))[1].append(f"{node.lineno} {form}")

    def _scope(self, node) -> None:
        outer = self.stack[-1][1]
        name = "<lambda>" if isinstance(node, ast.Lambda) else node.name
        self.stack.append((node, name if outer == "<module>" else f"{outer}.{name}"))
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = visit_Lambda = _scope

    def _getattr_on_sys(self, call: ast.AST) -> str | None:
        """`getattr(sys, "<常量名>")` 时返回那个名字。"""
        if isinstance(call, ast.Call) and _qualified(call.func, self.names) == "builtins.getattr" \
                and len(call.args) >= 2 and _is_sys_module(_qualified(call.args[0], self.names)) \
                and isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
            return call.args[1].value
        return None

    def _keyed_by_sys(self, node: ast.AST) -> bool:
        """`sys.modules["sys"]` 或 `sys.modules.get("sys")` 一类：下标或方法调用的第一个参数是常量 "sys"。"""
        parent = self.parents.get(node)
        key = None
        if isinstance(parent, ast.Subscript) and parent.value is node:
            key = parent.slice
        elif isinstance(parent, ast.Attribute) and isinstance(call := self.parents.get(parent), ast.Call) \
                and call.func is parent and call.args:
            key = call.args[0]
        return isinstance(key, ast.Constant) and key.value == "sys"

    def _reference(self, node: ast.Name | ast.Attribute) -> None:
        q = _qualified(node, self.names)
        member = _sys_member(q)
        if member in _STDERR_ATTRS:
            self._hit(node, q)
        elif member == "modules" and self._keyed_by_sys(node):
            self.bypasses.append(f"{node.lineno} 经 sys.modules 取 sys")
        elif member == "__dict__":
            self.bypasses.append(f"{node.lineno} 读取 sys.__dict__")
        elif _is_sys_module(q) and isinstance(node.ctx, ast.Load):
            parent = self.parents.get(node)
            as_base = isinstance(parent, ast.Attribute) and parent.value is node
            if not as_base and not (self._getattr_on_sys(parent) is not None and parent.args[0] is node):
                self.bypasses.append(f"{node.lineno} 把 sys 模块当作值使用")
        elif _is_writer(q) and isinstance(node.ctx, ast.Load):
            # 不是被直接调用（赋给变量、作为参数或返回值、放进容器、取它的属性）：此后经别的名字调用时核对不了实参
            parent = self.parents.get(node)
            if not (isinstance(parent, ast.Call) and parent.func is node):
                self.bypasses.append(f"{node.lineno} 把 {q} 当作值使用")

    def visit_Name(self, node: ast.Name) -> None:
        self._reference(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self._reference(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        q = _qualified(node.func, self.names)
        if self._getattr_on_sys(node) in _STDERR_ATTRS:
            self._hit(node, f"getattr(sys, {node.args[1].value!r})")
        elif q == "builtins.print" and any(k.arg in ("file", None) for k in node.keywords):
            self._hit(node, "print(file=...)")
        elif q in _FD_WRITERS and _writes_fd2(node):
            self._hit(node, f"{q}(2, ...)")
        elif _sys_member(q) in _EXCEPTHOOKS:
            self._hit(node, f"{q}(...)")
        elif q in _DYNAMIC_IMPORTS:
            self.bypasses.append(f"{node.lineno} 动态导入 {q}")
        elif q is not None and q.startswith(_BYPASS_CALLS):
            self.bypasses.append(f"{node.lineno} {q}")
        self.generic_visit(node)

    def _class_body_import(self, node: ast.Import | ast.ImportFrom) -> None:
        """类体内的 import 把名字绑定成类属性，经 self 一类的实例访问时链根不是 import 绑定的名字、追踪不到；不论导入什么都报。
        所在作用域是类即算，包括类体里 if、try 之下的 import；方法体里的 import 不算。"""
        if isinstance(self.stack[-1][0], ast.ClassDef):
            self.bypasses.append(f"{node.lineno} 类体内的 {ast.unparse(node)}")

    def visit_Import(self, node: ast.Import) -> None:
        self._class_body_import(node)
        self.bypasses += [f"{node.lineno} import {a.name}" for a in node.names
                          if a.name.partition(".")[0] in _BYPASS_MODULES]

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self._class_body_import(node)
        if node.level == 0 and (node.module or "").partition(".")[0] in _BYPASS_MODULES:
            self.bypasses.append(f"{node.lineno} from {node.module} import ...")
        if any(a.name == "*" for a in node.names):
            self.bypasses.append(f"{node.lineno} from {'.' * node.level}{node.module or ''} import *")


def _scan_stderr(sources: dict[str, str]) -> tuple[list[_Outlet], list[tuple[str, str]]]:
    """返回 (出口清单, 无法登记的写法清单)；出口按文件与定义行排序。"""
    outlets: list[_Outlet] = []
    bypasses: list[tuple[str, str]] = []
    for rel, text in sorted(sources.items()):
        scan = _StderrScan(rel, ast.parse(text))
        outlets += scan.outlets()
        bypasses += [(rel, what) for what in scan.bypasses]
    return sorted(outlets, key=lambda o: (o.rel, o.lineno)), bypasses


def _stderr_violations(sources: dict[str, str]) -> list[tuple[str, str, str]]:
    """对照登记清单的全部违例，每条是 (类别, 文件, 出口路径或写法)；真实的包应为空。"""
    outlets, bypasses = _scan_stderr(sources)
    keys = [(o.rel, o.qualname) for o in outlets]
    v = [(_UNREGISTERED, rel, q) for rel, q in sorted(set(keys) - _STDERR_OUTLETS)]
    v += [(_GONE, rel, q) for rel, q in sorted(_STDERR_OUTLETS - set(keys))]
    v += [(_DUPLICATE, rel, q) for rel, q in sorted({k for k in keys if keys.count(k) > 1})]
    v += [(_UNREDACTED, o.rel, o.qualname) for o in outlets if not o.redacts]
    v += [(_UNREGISTRABLE, rel, what) for rel, what in bypasses]
    return v


def _with(rel: str, old: str | None, new: str) -> dict[str, str]:
    """真实包源码的内存副本，只改一个文件：old 为 None 时把 new 追加到文件末尾，否则把恰好出现一次的 old 换成 new。"""
    sources = dict(_package_sources())
    text = sources[rel]
    if old is None:
        sources[rel] = f"{text}\n\n{new}"
    else:
        assert text.count(old) == 1, f"{rel} 里应恰有一处 {old!r}：源码改过就同步更新这条用例"
        sources[rel] = text.replace(old, new)
    return sources


def test_stderr_outlets_are_exactly_the_redacting_ones():
    """正向对照：真实的包里写 stderr 的出口恰为登记的三处，各自调用 redact_secrets，也没有无法登记的写法。"""
    outlets, others = _scan_stderr(_package_sources())
    assert {(o.rel, o.qualname) for o in outlets} == _STDERR_OUTLETS, \
        f"包内写 stderr 的出口有变化：新出口要经 redact_secrets，并登记进本测试的清单。现有 {outlets}"
    assert len(outlets) == len(_STDERR_OUTLETS), outlets
    assert all(o.redacts for o in outlets), outlets
    assert others == [], others
    assert _stderr_violations(_package_sources()) == []


@pytest.mark.parametrize(("rel", "func"), sorted(_STDERR_OUTLETS))
def test_each_stderr_outlet_calls_redact_secrets(rel, func):
    """登记的每处出口在包里恰有一个定义，且它自己的函数体里调用 redact_secrets。"""
    outlets, _ = _scan_stderr(_package_sources())
    mine = [o for o in outlets if (o.rel, o.qualname) == (rel, func)]
    assert len(mine) == 1, mine
    assert mine[0].redacts, f"{rel} 的 {func} 写 stderr 前没有自己调用 redact_secrets"


_NEW_OUTLETS = [
    pytest.param("run_scope.py", "import sys as _s\n\ndef _warn(msg):\n    _s.stderr.write(msg)\n",
                 "_warn", id="import-sys-as"),
    pytest.param("run_scope.py", "from sys import stderr\n\ndef _warn(msg):\n    stderr.write(msg)\n",
                 "_warn", id="from-sys-import-stderr"),
    pytest.param("run_scope.py", "from sys import stderr as _e\n\ndef _warn(msg):\n    _e.write(msg)\n",
                 "_warn", id="from-sys-import-stderr-as"),
    pytest.param("lib/job_source.py", "from sys import __stderr__ as _e\n\ndef _warn(msg):\n    _e.write(msg)\n",
                 "_warn", id="from-sys-import-dunder-stderr-as"),
    pytest.param("lib/job_source.py", "def _warn(msg):\n    sys.__stderr__.write(msg)\n",
                 "_warn", id="sys-dunder-stderr"),
    pytest.param("run_scope.py", "def _warn(msg):\n    getattr(sys, 'stderr').write(msg)\n",
                 "_warn", id="getattr-constant"),
    pytest.param("evidence.py", "import gherkai_worker_novaact.run_scope as _rs\n\ndef _warn(msg):\n"
                 "    _rs.sys.stderr.write(msg)\n", "_warn", id="module-attribute"),
    pytest.param("run_scope.py", "def _warn(msg, out):\n    print(msg, file=out)\n",
                 "_warn", id="print-file"),
    pytest.param("run_scope.py", "def _warn(msg):\n    os.write(2, msg.encode())\n",
                 "_warn", id="os-write-fd2"),
    pytest.param("evidence.py", "from os import write as _w\n\ndef _warn(msg):\n    _w(2, msg.encode())\n",
                 "_warn", id="from-os-import-write-as"),
    pytest.param("evidence.py", "def _warn(msg):\n    with open(2, 'w', closefd=False) as f:\n        f.write(msg)\n",
                 "_warn", id="open-fd2"),
    pytest.param("evidence.py", "import io\n\ndef _warn(msg):\n    io.FileIO(2, 'w', closefd=False).write(msg.encode())\n",
                 "_warn", id="io-fileio-fd2"),
    pytest.param("run_scope.py", "def _warn(msg):\n    sys.__excepthook__(RuntimeError, RuntimeError(msg), None)\n",
                 "_warn", id="excepthook-call"),
    pytest.param("run_scope.py", "class _Probe:\n    def log(self, msg):\n        sys.stderr.write(msg)\n",
                 "_Probe.log", id="method-named-log"),
    pytest.param("lib/artifact_upload.py", "class _Probe:\n    def _log(self, msg):\n"
                 "        sys.stderr.write(redact_secrets(msg))\n", "_Probe._log", id="method-named-_log-redacting"),
    pytest.param("run_scope.py", "def _outer():\n    def log(msg):\n        sys.stderr.write(msg)\n    return log\n",
                 "_outer.log", id="nested-function-named-log"),
]


@pytest.mark.parametrize(("rel", "snippet", "qualname"), _NEW_OUTLETS)
def test_unregistered_outlet_is_rejected(rel, snippet, qualname):
    """包里新加一处写 stderr 的函数（别名写法、类内同名方法、嵌套函数），即使它自己经脱敏，也要先登记进清单才能通过。"""
    violations = _stderr_violations(_with(rel, None, snippet))
    assert (_UNREGISTERED, rel, qualname) in violations, violations


_STRIPPED = [
    pytest.param("run_scope.py", 'sys.stderr.write(f"{redact_secrets(msg)}\\n")', 'sys.stderr.write(f"{msg}\\n")',
                 "log", id="log"),
    pytest.param("run_scope.py", "real.write(redact_secrets(buf.getvalue()))", "real.write(buf.getvalue())",
                 "_redacting_excepthook", id="excepthook"),
    pytest.param("lib/artifact_upload.py", 'sys.stderr.write(f"{redact_secrets(msg)}\\n")',
                 'sys.stderr.write(f"{msg}\\n")', "_log", id="uploader-log"),
    pytest.param("run_scope.py", 'sys.stderr.write(f"{redact_secrets(msg)}\\n")',
                 '_unused = lambda: redact_secrets(msg)\n    sys.stderr.write(f"{msg}\\n")', "log",
                 id="log-redacts-only-inside-a-lambda"),
]


@pytest.mark.parametrize(("rel", "old", "new", "qualname"), _STRIPPED)
def test_registered_outlet_without_its_own_redact_call_is_rejected(rel, old, new, qualname):
    """已登记的出口去掉 redact_secrets，或只在它内部的 lambda 里调用，都要判出。"""
    violations = _stderr_violations(_with(rel, old, new))
    assert (_UNREDACTED, rel, qualname) in violations, violations


def test_redefined_outlet_is_checked_separately():
    """模块末尾再定义一个同名的 log：两个定义各自检查，重复定义与未脱敏的那一个都要判出。"""
    violations = _stderr_violations(_with("run_scope.py", None, "def log(msg):\n    sys.stderr.write(msg)\n"))
    assert (_DUPLICATE, "run_scope.py", "log") in violations, violations
    assert (_UNREDACTED, "run_scope.py", "log") in violations, violations


_BYPASSES = [
    pytest.param("import logging\n", id="import-logging"),
    pytest.param("import logging.handlers\n", id="import-logging-submodule"),
    pytest.param("from logging import getLogger\n", id="from-logging-import"),
    pytest.param("import traceback as _tb\n\ndef _warn():\n    _tb.print_exc()\n", id="traceback-alias"),
    pytest.param("from traceback import print_exception\n\ndef _warn(e):\n    print_exception(e)\n",
                 id="from-traceback-import"),
    pytest.param("import warnings\n\ndef _warn(msg):\n    warnings.warn(msg)\n", id="warnings-warn"),
    pytest.param("from sys import *\n", id="star-import-from-sys"),
    pytest.param("_s = sys\n", id="sys-module-as-value"),
    pytest.param("def _warn(msg):\n    __import__('sys').stderr.write(msg)\n", id="dunder-import"),
    pytest.param("import importlib\n\ndef _warn(msg):\n    importlib.import_module('sys').stderr.write(msg)\n",
                 id="importlib-import-module"),
    pytest.param("from importlib import import_module as _im\n\ndef _warn(msg):\n    _im('sys').stderr.write(msg)\n",
                 id="from-importlib-import-module-as"),
    pytest.param("def _warn(msg):\n    sys.modules['sys'].stderr.write(msg)\n", id="sys-modules-subscript"),
    pytest.param("def _warn(msg):\n    sys.modules.get('sys').stderr.write(msg)\n", id="sys-modules-get"),
    pytest.param("def _warn(msg):\n    sys.__dict__['stderr'].write(msg)\n", id="sys-dunder-dict"),
]


@pytest.mark.parametrize("snippet", _BYPASSES)
def test_unregistrable_stderr_writer_is_rejected(snippet):
    """绕过出口直接写 stderr 的库调用与静态分析无法追踪的 sys 引用，出现即判出。"""
    violations = _stderr_violations(_with("run_scope.py", None, snippet))
    assert any(kind == _UNREGISTRABLE and rel == "run_scope.py" for kind, rel, _ in violations), violations


_INDIRECT_WRITERS = [
    pytest.param("class _Probe:\n    import sys as _m\n\n    def warn(self, msg):\n        self._m.stderr.write(msg)\n",
                 "类体内的 import sys as _m", id="import-in-class-body"),
    pytest.param("class _Probe:\n    from sys import stderr as _e\n\n    def warn(self, msg):\n        self._e.write(msg)\n",
                 "类体内的 from sys import stderr as _e", id="from-import-in-class-body"),
    pytest.param("class _Probe:\n    if True:\n        import sys as _m\n\n    def warn(self, msg):\n"
                 "        self._m.stderr.write(msg)\n", "类体内的 import sys as _m", id="import-in-class-body-under-if"),
    pytest.param("def _warn(msg):\n    w = os.write\n    w(2, msg.encode())\n", "把 os.write 当作值使用",
                 id="os-write-assigned"),
    pytest.param("def _warn(msg, out):\n    p = print\n    p(msg, file=out)\n", "把 builtins.print 当作值使用",
                 id="print-assigned"),
    pytest.param("def _warn(msg):\n    h = sys.__excepthook__\n    h(RuntimeError, RuntimeError(msg), None)\n",
                 "把 sys.__excepthook__ 当作值使用", id="excepthook-assigned"),
    pytest.param("def _opener():\n    return open\n", "把 builtins.open 当作值使用", id="open-returned"),
    pytest.param("import functools\n\ndef _warn(msgs, out):\n    list(map(functools.partial(print, file=out), msgs))\n",
                 "把 builtins.print 当作值使用", id="print-passed-as-argument"),
    pytest.param("def _warn(msg):\n    _writers = [os.write]\n    _writers[0](2, msg.encode())\n",
                 "把 os.write 当作值使用", id="os-write-in-container"),
    pytest.param("def _warn(msg, out):\n    print.__call__(msg, file=out)\n", "把 builtins.print 当作值使用",
                 id="print-attribute"),
]


@pytest.mark.parametrize(("snippet", "reason"), _INDIRECT_WRITERS)
def test_indirect_writer_is_rejected(snippet, reason):
    """写 stderr 的对象经类属性或变量间接取用时，静态分析核对不了写出的实参，出现即判出：类体内的 import 绑定成类属性、
    经实例访问；写函数赋给变量、作为参数或返回值、放进容器或取它的属性。"""
    violations = _stderr_violations(_with("run_scope.py", None, snippet))
    assert any(kind == _UNREGISTRABLE and rel == "run_scope.py" and what.endswith(reason)
               for kind, rel, what in violations), violations


def test_direct_writer_calls_and_method_imports_are_accepted():
    """直接调用写函数且目标不是 stderr、给 sys.excepthook 赋值、方法体里的 import，都不算间接取用。"""
    snippet = ("class _Probe:\n    def buffer(self):\n        import io\n        return io.StringIO()\n\n"
               "def _a(path, hook):\n    print(path)\n    open(path).close()\n    sys.excepthook = hook\n")
    assert _stderr_violations(_with("run_scope.py", None, snippet)) == []


_CONFLICTING_IMPORTS = [
    pytest.param("def _warn(msg):\n    import sys as _m\n    _m.stderr.write(msg)\n\n"
                 "def _buffer():\n    import io as _m\n    return _m.StringIO()\n", "_m", id="sys-then-io-as-same-alias"),
    pytest.param("def _buffer():\n    import io as _m\n    return _m.StringIO()\n\n"
                 "def _warn(msg):\n    import sys as _m\n    _m.stderr.write(msg)\n", "_m", id="io-then-sys-as-same-alias"),
    pytest.param("def _read(path):\n    from codecs import open\n    return open(path).read()\n\n"
                 "def _warn(msg):\n    with open(2, 'w', closefd=False) as f:\n        f.write(msg)\n",
                 "open", id="import-named-like-builtin-open"),
]


@pytest.mark.parametrize(("snippet", "name"), _CONFLICTING_IMPORTS)
def test_import_name_bound_to_different_objects_is_rejected(snippet, name):
    """同一个名字在文件内由 import 绑定到不同对象（含与 open 一类内建函数同名而所指不同）：各处引用指哪一个无法静态确定，
    出现即判出。前两条里写 stderr 且未脱敏的是 sys 那一处，第三条是经内建 open 写文件描述符 2 的那一处。"""
    violations = _stderr_violations(_with("run_scope.py", None, snippet))
    assert any(kind == _UNREGISTRABLE and rel == "run_scope.py" and f"名字 {name} 在文件内可能指向不同对象" in what
               for kind, rel, what in violations), violations


def test_import_name_bound_to_the_same_object_twice_is_accepted():
    """同一个名字在不同函数里重复绑定到同一个对象不算冲突；相对导入按所在的包展开后与绝对导入比较。"""
    snippet = ("def _a():\n    import io as _m\n    return _m.StringIO()\n\n"
               "def _b():\n    import io as _m\n    return _m.BytesIO()\n\n"
               "def _c(msg):\n    from .lib.redact import redact_secrets\n    return redact_secrets(msg)\n")
    assert _stderr_violations(_with("run_scope.py", None, snippet)) == []
