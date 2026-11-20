"""静态守护：持生命期锁的进程只经 exec 启动子进程（ADR 0054 决策三「不被子进程继承」与「前提」）。

锁随打开的文件描述走：子进程只要还共用那次打开，持锁的进程被杀之后锁仍在，「拿得到锁即管它的进程已不在」就不成立。锁描述符
由 `os.open` 打开、不可继承（PEP 446），生产用的持有者不交出它，所以风险只在两类写法：fork 而不 exec（子进程带着父进程的全部
描述符）；把描述符变成可继承，再以不关描述符的方式 exec。这里用 AST 扫 core、runtime、cli 三个生产包，逐个点名这些写法：

- 调用或引用 `os.fork`、`os.forkpty`、`pty.fork`；
- 导入或引用 `multiprocessing`、`concurrent.futures` 的进程池（`ProcessPoolExecutor` 与它所在的 `concurrent.futures.process`）；
- 从 `os`、`pty` 一次导入全部名字（`from os import *`）：之后的裸名调用认不出来源；
- `os.set_inheritable` 的第二个参数不是字面量 `False`；
- `os.dup2`（复制出的号缺省可继承），只放行把日志接到标准输入、标准输出、标准错误的 `handoff.redirect_output`；`posix_spawn`
  的 `POSIX_SPAWN_DUP2` 同类；
- `fcntl.fcntl` 的第二个参数不是 `fcntl` 模块的具名常量（数字写的命令认不出是不是复制或改标志），不带 CLOEXEC 的复制
  （`F_DUPFD`），以及 `F_SETFD` 设的值不是 `FD_CLOEXEC`（清掉 CLOEXEC）；
- `subprocess` 与 `asyncio` 起子进程的各入口，以及任何对象上名为 `subprocess_exec`、`subprocess_shell` 的方法（事件循环的
  入口），带 `close_fds`、而值不是字面量 `True`，含按位置传给 `subprocess` 各入口的（收紧项：实测它单独不延长持有）；
- 继承 `subprocess.Popen` 的类：子类可以改掉起子进程时对描述符的处理。

`posix` 模块按 `os` 认（`os` 的这些函数就来自它）。名字经导入别名还原（`import subprocess as _sp`、`from os import fork as f`
都认得出）；没有经导入绑定的局部名不算。扫描看不见、由真实执行覆盖的写法（ADR 0054 决策三）：经 `getattr` 或 `*args`、`**kwargs`
拼出的调用；把函数先赋给变量再调用（如 `inherit = os.set_inheritable`）；经别的模块转手取到的名字（如 `shutil.os.fork`）；经
`ctypes` 调 libc；经 `importlib` 动态导入；C 扩展里的写法。扫描器本身另有逐条的正反用例，扫描面失效（目录不在、放行登记找不到
对应的位置）即失败，不静默空扫。
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = ("core/gherkai_core", "runtime/gherkai_runtime", "cli/gherkai_cli")

# dup2 的放行登记：（仓库相对路径, 所在函数名）。登记项找不到对应的调用时测试失败，过期的登记须删除
DUP2_ALLOWED = {("runtime/gherkai_runtime/handoff.py", "redirect_output")}

_FORK = {"os.fork", "os.forkpty", "pty.fork"}
_PROCESS_POOL = {"concurrent.futures.ProcessPoolExecutor", "concurrent.futures.process"}
_SPAWN_DUP2 = {"os.POSIX_SPAWN_DUP2"}
_NO_STAR_IMPORT = {"os", "pty"}  # 从这些模块一次导入全部名字之后，fork 一类的裸名调用认不出来源
# subprocess 的各入口：它们的位置参数都原样交给 Popen，close_fds 是第 8 个
_SUBPROCESS_ENTRIES = {
    "subprocess.Popen", "subprocess.run", "subprocess.call", "subprocess.check_call", "subprocess.check_output",
}
_CLOSE_FDS_INDEX = 7
_CHILD_ENTRIES = _SUBPROCESS_ENTRIES | {"asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell"}
# 事件循环起子进程的方法：接收者是运行时才有的循环对象，名字经导入还原不出来，所以按方法名认，不论接收者
_LOOP_CHILD_METHODS = {"subprocess_exec", "subprocess_shell"}


def _canonical(name: str) -> str:
    """`posix` 按 `os` 认：`os` 的进程与描述符函数就是从 `posix` 取来的同一批。"""
    if name == "posix" or name.startswith("posix."):
        return "os" + name[len("posix"):]
    return name


@dataclass
class Scan:
    hits: list[str] = field(default_factory=list)
    dup2_sites: set[tuple[str, str | None]] = field(default_factory=set)  # （路径, 所在函数名）
    child_entries: int = 0  # 认出的起子进程调用的个数：扫描面没有失效的旁证


def _is_multiprocessing(name: str) -> bool:
    return name == "multiprocessing" or name.startswith("multiprocessing.")


def _import_aliases(tree: ast.AST) -> dict[str, set[str]]:
    """文件里各处导入绑定的名字到完整名字的映射（函数里的延迟导入也算）。同一个名字在不同处绑到不同对象时都记下。"""
    aliases: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    aliases.setdefault(a.asname, set()).add(_canonical(a.name))
                else:
                    top = a.name.split(".")[0]
                    aliases.setdefault(top, set()).add(_canonical(top))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for a in node.names:
                aliases.setdefault(a.asname or a.name, set()).add(_canonical(f"{node.module}.{a.name}"))
    return aliases


class _Scanner(ast.NodeVisitor):
    def __init__(self, rel: str, tree: ast.AST, scan: Scan) -> None:
        self.rel = rel
        self.aliases = _import_aliases(tree)
        self.scan = scan
        self.functions: list[str] = []
        self._seen: set[tuple[int, str]] = set()

    def _hit(self, node: ast.AST, what: str) -> None:
        if (node.lineno, what) not in self._seen:
            self._seen.add((node.lineno, what))
            self.scan.hits.append(f"{self.rel}:{node.lineno}: {what}")

    def _names(self, node: ast.AST) -> set[str]:
        """表达式经导入别名还原出的完整名字（可能有几个候选）；不是导入绑定的名字返回空集。"""
        if isinstance(node, ast.Name):
            return set(self.aliases.get(node.id, ()))
        if isinstance(node, ast.Attribute):
            return {f"{base}.{node.attr}" for base in self._names(node.value)}
        return set()

    # ---- 所在函数 ----

    def _visit_function(self, node) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    # ---- 类 ----

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for base in node.bases:
            if "subprocess.Popen" in self._names(base):
                self._hit(node, "继承 subprocess.Popen 的类（子类可以改掉起子进程时对描述符的处理）")
        self.generic_visit(node)

    # ---- 导入 ----

    def visit_Import(self, node: ast.Import) -> None:
        for a in node.names:
            if _is_multiprocessing(a.name) or a.name in _PROCESS_POOL:
                self._hit(node, f"导入 {a.name}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level == 0 and node.module:
            if _is_multiprocessing(node.module):
                self._hit(node, f"从 {node.module} 导入")
            for a in node.names:
                if a.name == "*" and _canonical(node.module) in _NO_STAR_IMPORT:
                    self._hit(node, f"从 {node.module} 导入全部名字（之后的裸名调用认不出来源）")
                full = _canonical(f"{node.module}.{a.name}")
                if full in _FORK | _PROCESS_POOL:
                    self._hit(node, f"导入 {full}")

    # ---- 引用 ----

    def _check_reference(self, node: ast.AST) -> None:
        for name in self._names(node):
            if name in _FORK:
                self._hit(node, f"{name}（fork 而不 exec）")
            elif name in _PROCESS_POOL or _is_multiprocessing(name):
                self._hit(node, f"{name}（以 fork 起子进程的执行器）")
            elif name in _SPAWN_DUP2:
                self._hit(node, f"{name}（把描述符复制进子进程）")

    def visit_Name(self, node: ast.Name) -> None:
        self._check_reference(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self._check_reference(node)
        self.generic_visit(node)

    # ---- 调用 ----

    def visit_Call(self, node: ast.Call) -> None:
        names = self._names(node.func)
        if "os.set_inheritable" in names:
            flag = node.args[1] if len(node.args) > 1 else next(
                (k.value for k in node.keywords if k.arg == "inheritable"), None)
            if not (isinstance(flag, ast.Constant) and flag.value is False):
                self._hit(node, "os.set_inheritable 的第二个参数不是 False")
        if "os.dup2" in names:
            site = (self.rel, self.functions[-1] if self.functions else None)
            self.scan.dup2_sites.add(site)
            if site not in DUP2_ALLOWED:
                self._hit(node, "os.dup2（复制出的号缺省可继承）")
        if "fcntl.fcntl" in names:
            cmd = self._names(node.args[1]) if len(node.args) >= 2 else set()
            if not any(n.startswith("fcntl.") and n[len("fcntl."):].isupper() for n in cmd):
                # 数字写的命令（如 0 即 F_DUPFD、2 即 F_SETFD）或变量：认不出是不是复制描述符、改它的标志
                self._hit(node, "fcntl.fcntl 的第二个参数不是 fcntl 模块的具名常量")
            if "fcntl.F_DUPFD" in cmd:
                self._hit(node, "fcntl.fcntl 的 F_DUPFD（不带 CLOEXEC 的复制）")
            if "fcntl.F_SETFD" in cmd:
                value = node.args[2] if len(node.args) > 2 else None
                if value is None or "fcntl.FD_CLOEXEC" not in self._names(value):
                    self._hit(node, "fcntl.fcntl 的 F_SETFD 设的值不是 FD_CLOEXEC")
        entries = sorted(names & _CHILD_ENTRIES)
        if not entries and isinstance(node.func, ast.Attribute) and node.func.attr in _LOOP_CHILD_METHODS:
            entries = [node.func.attr]
        if entries:
            self.scan.child_entries += 1
            for k in node.keywords:
                if k.arg == "close_fds" and not (isinstance(k.value, ast.Constant) and k.value.value is True):
                    self._hit(node, f"{entries[0]} 带 close_fds 而值不是 True")
            positional = node.args[:_CLOSE_FDS_INDEX + 1]
            if (names & _SUBPROCESS_ENTRIES and len(positional) > _CLOSE_FDS_INDEX
                    and not any(isinstance(a, ast.Starred) for a in positional)):
                value = positional[_CLOSE_FDS_INDEX]
                if not (isinstance(value, ast.Constant) and value.value is True):
                    self._hit(node, f"{entries[0]} 按位置传的 close_fds 不是 True")
        self.generic_visit(node)


def scan_source(rel: str, source: str, scan: Scan | None = None) -> Scan:
    scan = scan if scan is not None else Scan()
    tree = ast.parse(source)
    _Scanner(rel, tree, scan).visit(tree)
    return scan


def _scan_production() -> tuple[Scan, int]:
    scan = Scan()
    files = 0
    for root in SCAN_ROOTS:
        base = REPO_ROOT / root
        assert base.is_dir(), f"扫描面失效：{root} 不存在（包搬家了？请更新 SCAN_ROOTS，别让守护静默空扫）"
        for path in sorted(base.rglob("*.py")):
            scan_source(path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"), scan)
            files += 1
    return scan, files


def test_production_code_starts_children_only_through_exec():
    """三个生产包里没有 fork 而不 exec 的写法，也没有把描述符变成可继承的写法；dup2 只在放行登记的那一处。"""
    scan, files = _scan_production()
    assert files > 0 and scan.child_entries > 0, "扫描面失效：没有扫到文件，或一个起子进程的调用都没认出来"
    assert not scan.hits, (
        "持生命期锁的进程启动子进程只经 exec：这些写法会让子进程带着锁描述符活下去，持锁的进程被杀之后锁仍被持有。"
        "改用 subprocess 缺省方式启动，不要把描述符设为可继承：\n  " + "\n  ".join(scan.hits))
    stale = sorted(DUP2_ALLOWED - scan.dup2_sites)
    assert not stale, f"DUP2_ALLOWED 里这些登记已找不到 os.dup2 的调用，请删除：{stale}"


@pytest.mark.parametrize("source", [
    "import os\nos.fork()",
    "import os as _os\n_os.fork()",
    "from os import fork\nfork()",
    "from os import forkpty as fp\nfp()",
    "import pty\npty.fork()",
    "import os\nstart = os.fork",                          # 不调用、只引用也算：可能被当作回调交出去
    "import multiprocessing",
    "import multiprocessing.pool",
    "from multiprocessing import Process",
    "def f():\n    import multiprocessing as mp\n    mp.get_context('fork')",
    "from concurrent.futures import ProcessPoolExecutor",
    "import concurrent.futures\nconcurrent.futures.ProcessPoolExecutor()",
    "from concurrent import futures\nfutures.ProcessPoolExecutor(2)",
    "import concurrent.futures.process",
    "import os\nos.set_inheritable(fd, True)",
    "import os\nos.set_inheritable(fd, flag)",              # 值不是字面量 False 一律不放行
    "import os\nos.set_inheritable(fd, inheritable=True)",
    "import os\nos.dup2(a, b)",
    "import os\ndef redirect_output(fd):\n    os.dup2(fd, 1)",  # 函数名对得上、文件不是登记的那一个
    "import os\nos.posix_spawn(p, a, e, file_actions=[(os.POSIX_SPAWN_DUP2, fd, 5)])",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_DUPFD, 3)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_SETFD, 0)",
    "from fcntl import fcntl, F_SETFD\nfcntl(fd, F_SETFD, 0)",
    "import subprocess\nsubprocess.Popen(cmd, close_fds=False)",
    "import subprocess as _sp\n_sp.run(cmd, close_fds=False)",
    "from subprocess import check_output\ncheck_output(cmd, close_fds=keep)",
    "import asyncio\nasync def f():\n    await asyncio.create_subprocess_exec(cmd, close_fds=False)",
    # posix 按 os 认
    "import posix\nposix.fork()",
    "import posix\nposix.forkpty()",
    "from posix import fork\nfork()",
    "import posix as _px\n_px.set_inheritable(fd, True)",
    "import posix\nposix.dup2(a, b)",
    # 一次导入全部名字
    "from os import *\nfork()",
    "from posix import *",
    "from pty import *",
    # fcntl 的命令不是具名常量
    "import fcntl\nfcntl.fcntl(fd, 0, 3)",                   # 数字写的 F_DUPFD
    "import fcntl\nfcntl.fcntl(fd, 2, 0)",                   # 数字写的 F_SETFD，清掉 CLOEXEC
    "import fcntl\nfcntl.fcntl(fd, cmd, 0)",
    "from fcntl import fcntl\nfcntl(fd, 2, 0)",
    # 事件循环的入口，不论接收者
    "async def f(loop):\n    await loop.subprocess_exec(factory, cmd, close_fds=False)",
    "async def f(self):\n    await self._loop.subprocess_shell(factory, cmd, close_fds=keep)",
    # 继承 Popen
    "import subprocess\nclass P(subprocess.Popen):\n    pass",
    "from subprocess import Popen as _P\nclass Q(_P):\n    pass",
    # 按位置传的 close_fds
    "import subprocess\nsubprocess.Popen(cmd, -1, None, None, None, None, None, False)",
    "import subprocess\nsubprocess.run(cmd, -1, None, None, None, None, None, keep)",
])
def test_scanner_flags_each_forbidden_form(source):
    """每一种被点名的写法（含经导入别名的、延迟导入的）都被认出来。"""
    assert scan_source("cli/gherkai_cli/example.py", source).hits, source


@pytest.mark.parametrize("source", [
    "import os\nos.set_inheritable(fd, False)",
    "import os\nos.dup(fd)",                               # dup 出的号不可继承
    "import subprocess\nsubprocess.Popen(cmd, pass_fds=(w,), start_new_session=True)",
    "import subprocess\nsubprocess.run(cmd, close_fds=True)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 3)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)",
    "def fork():\n    pass\nfork()",                       # 没有经导入绑定的局部名
    "import os\nos.register_at_fork(after_in_child=f)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_GETFL)",
    "import posix\nposix.getpid()",
    "from os import path",
    "async def f(loop):\n    await loop.subprocess_exec(factory, cmd)",
    "import subprocess\nsubprocess.Popen(cmd, -1, None, None, None, None, None, True)",
    "import subprocess\nsubprocess.Popen(*argv)",               # 拼出来的调用看不见，由真实执行覆盖
    "import subprocess\nclass Holder:\n    proc: subprocess.Popen",
])
def test_scanner_passes_allowed_forms(source):
    assert not scan_source("cli/gherkai_cli/example.py", source).hits, source


def test_scanner_allows_dup2_only_in_the_registered_function():
    """dup2 的放行按（文件, 函数）登记：登记的函数里放行，同一文件的别的函数里照样拦。"""
    allowed = "import os\ndef redirect_output(fd):\n    os.dup2(fd, 1)\n"
    rel = "runtime/gherkai_runtime/handoff.py"
    assert not scan_source(rel, allowed).hits
    assert scan_source(rel, allowed + "def other(fd):\n    os.dup2(fd, 2)\n").hits
