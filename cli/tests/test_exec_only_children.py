"""静态守护：持生命期锁的进程只经 exec 启动子进程（ADR 0054 决策三「不被子进程继承」与「前提」）。

锁随打开的文件描述走：子进程只要还共用那次打开，持锁的进程被杀之后锁仍在，「拿得到锁即管它的进程已不在」就不成立。锁描述符
由 `os.open` 打开、不可继承（PEP 446），生产用的持有者不交出它，所以风险只在两类写法：fork 之后不立即 exec（子进程带着父进程的全部
描述符，`preexec_fn` 也属于这一类：它在 fork 之后、关描述符与 exec 之前执行 Python 代码）；把描述符变成可继承，再以不关描述符的
方式 exec。起进程与改描述符的接口是一个开放的面，逐个点名危险写法总有没点到的直接写法，所以这里按放行清单写：只放行认得的入口、
参数与名字，清单之外的一律报出，新的用法先进清单（ADR 0054「被拒方案」里「静态测试按拒绝清单写」一条）。用 AST 扫 core、runtime、
cli 三个生产包，规则四条：

- **不一次导入全部名字**：`from X import *` 不出现（任何模块，含相对导入），之后的裸名调用认不出来源。
- **起进程只经两组入口**：`subprocess` 的 `SUBPROCESS_ENTRIES`，`asyncio` 的 `ASYNCIO_ENTRIES` 与任何对象上名为
  `subprocess_exec`、`subprocess_shell` 的方法（事件循环的入口，接收者是运行时才有的对象，所以按方法名认）。标准库里别的起进程的
  接口引用即报，不论有没有调用（可能被当作回调交出去）：`OTHER_SPAWN_NAMES` 里的函数与 `os.spawn` 开头的各函数；
  `OTHER_SPAWN_MODULES` 里的模块（含子模块）导入即报；`concurrent.futures` 的进程池同样在 `OTHER_SPAWN_NAMES` 里。
- **起进程的参数**：`preexec_fn` 不出现、或是字面量 `None`，按关键字传的在任何调用上都查、不论接收者；按位置传给 `subprocess`
  各入口的第 7 个参数同样查，它之前有展开的参数（`*args`）时定位不到，报出。`close_fds` 不出现、或是字面量 `True`（收紧项：实测它
  单独不延长持有），含按位置传给 `subprocess` 各入口的第 8 个参数。两组入口上展开的关键字参数（`**kwargs`）报出：认不出里面
  有没有这两个参数。继承 `subprocess.Popen` 的类报出：子类可以改掉起子进程时对描述符的处理。
- **描述符**：`os.set_inheritable` 的第二个参数须是字面量 `False`；`os.dup2`（复制出的号缺省可继承）只在 `DUP2_ALLOWED` 登记的
  那一处；`fcntl` 模块只放行 `FCNTL_ALLOWED` 里的名字（取锁的函数、`fcntl` 本身与它的命令和标志常量），清单之外的名字引用或经
  `from fcntl import` 导入即报；`fcntl.fcntl` 的第二个参数须是 `FCNTL_COMMANDS` 里的具名常量（带 CLOEXEC 的复制、读写描述符标志
  与状态标志），`F_SETFD` 设的值须是 `FD_CLOEXEC`。

`posix` 模块按 `os` 认（`os` 的这些函数就来自它）。名字经导入别名还原（`import subprocess as _sp`、`from os import fork as f`
都认得出）；没有经导入绑定的局部名不算。扫描看不见、由真实执行覆盖的写法（ADR 0054 决策三）：经 `getattr` 拼出的调用，
两组入口之外的调用里展开的参数（转手调用入口的包装）；把函数先赋给变量再调用（如 `inherit = os.set_inheritable`）；经别的模块转手
取到的名字（如 `shutil.os.fork`、`subprocess._posixsubprocess`）；经 `ctypes` 调 libc；经 `importlib` 动态导入；C 扩展里的写法。
扫描器本身另有逐条的正反用例，扫描面失效（目录不在、放行登记找不到对应的位置、一个起子进程的调用都没认出来）即失败，不静默空扫。
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

# 放行的起进程入口。subprocess 的各入口把位置参数原样交给 Popen：preexec_fn 是第 7 个、close_fds 是第 8 个（下标从 0 起）
SUBPROCESS_ENTRIES = frozenset({
    "subprocess.Popen", "subprocess.run", "subprocess.call", "subprocess.check_call", "subprocess.check_output",
    "subprocess.getoutput", "subprocess.getstatusoutput",
})
ASYNCIO_ENTRIES = frozenset({"asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell"})
LOOP_CHILD_METHODS = frozenset({"subprocess_exec", "subprocess_shell"})
_PREEXEC_FN_INDEX = 6
_CLOSE_FDS_INDEX = 7

# 标准库里别的起进程的接口：这些名字（含其下的属性）引用即报；os.spawn 开头的各函数另按前缀认
OTHER_SPAWN_NAMES = frozenset({
    "os.fork", "os.forkpty", "os.system", "os.popen", "os.posix_spawn", "os.posix_spawnp", "os.startfile",
    "concurrent.futures.ProcessPoolExecutor", "concurrent.futures.process",
})
OTHER_SPAWN_PREFIXES = ("os.spawn",)
# 导入即报的模块（含子模块）
OTHER_SPAWN_MODULES = frozenset({"pty", "multiprocessing", "_posixsubprocess"})

# fcntl 模块放行的名字：取锁的两个函数，fcntl 本身，它放行的命令，以及取锁与设标志用的常量
FCNTL_COMMANDS = frozenset({"F_DUPFD_CLOEXEC", "F_GETFD", "F_SETFD", "F_GETFL", "F_SETFL"})
FCNTL_ALLOWED = frozenset({"flock", "lockf", "fcntl", "LOCK_SH", "LOCK_EX", "LOCK_NB", "LOCK_UN", "FD_CLOEXEC"}) | FCNTL_COMMANDS


def _canonical(name: str) -> str:
    """`posix` 按 `os` 认：`os` 的进程与描述符函数就是从 `posix` 取来的同一批。"""
    if name == "posix" or name.startswith("posix."):
        return "os" + name[len("posix"):]
    return name


def _under(name: str, base: str) -> bool:
    return name == base or name.startswith(base + ".")


def _other_spawn(name: str) -> bool:
    """name 是不是标准库里放行入口之外的起进程接口（或它下面的属性、所在的模块）。"""
    return (any(_under(name, b) for b in OTHER_SPAWN_NAMES | OTHER_SPAWN_MODULES)
            or name.startswith(OTHER_SPAWN_PREFIXES))


def _fcntl_not_allowed(name: str) -> bool:
    """name 是 `fcntl` 模块里放行清单之外的名字。只看模块下的第一层：`fcntl.fcntl.__doc__` 按 `fcntl` 认。"""
    if not name.startswith("fcntl."):
        return False
    return name.split(".")[1] not in FCNTL_ALLOWED


def _is_constant(node: ast.AST | None, value: object) -> bool:
    return isinstance(node, ast.Constant) and node.value is value


@dataclass
class Scan:
    hits: list[str] = field(default_factory=list)
    dup2_sites: set[tuple[str, str | None]] = field(default_factory=set)  # （路径, 所在函数名）
    child_entries: int = 0  # 认出的起子进程调用的个数：扫描面没有失效的旁证


def _import_aliases(tree: ast.AST) -> dict[str, set[str]]:
    """文件里各处导入绑定的名字到完整名字的映射（函数里的延迟导入也算）。同一个名字在不同处绑到不同对象时都记下。相对导入不还原。"""
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
                if a.name != "*":
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
            name = _canonical(a.name)
            if _other_spawn(name):
                self._hit(node, f"导入 {a.name}（起进程只经 subprocess 与 asyncio 的入口）")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        source = "." * node.level + (node.module or "")
        if any(a.name == "*" for a in node.names):
            self._hit(node, f"从 {source} 导入全部名字（之后的裸名调用认不出来源）")
        if node.level != 0 or not node.module:
            return
        module = _canonical(node.module)
        if _other_spawn(module):
            self._hit(node, f"从 {node.module} 导入（起进程只经 subprocess 与 asyncio 的入口）")
        for a in node.names:
            if a.name == "*":
                continue
            full = f"{module}.{a.name}"
            if _other_spawn(full):
                self._hit(node, f"导入 {full}（起进程只经 subprocess 与 asyncio 的入口）")
            if _fcntl_not_allowed(full):
                self._hit(node, f"导入 {full}（不在 fcntl 的放行清单里）")

    # ---- 引用 ----

    def _check_reference(self, node: ast.AST) -> None:
        for name in self._names(node):
            if _other_spawn(name):
                self._hit(node, f"{name}（起进程只经 subprocess 与 asyncio 的入口）")
            if _fcntl_not_allowed(name):
                self._hit(node, f"{name}（不在 fcntl 的放行清单里）")

    def visit_Name(self, node: ast.Name) -> None:
        self._check_reference(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self._check_reference(node)
        self.generic_visit(node)

    # ---- 调用 ----

    def _check_descriptor_calls(self, node: ast.Call, names: set[str]) -> None:
        if "os.set_inheritable" in names:
            flag = node.args[1] if len(node.args) > 1 else next(
                (k.value for k in node.keywords if k.arg == "inheritable"), None)
            if not _is_constant(flag, False):
                self._hit(node, "os.set_inheritable 的第二个参数不是 False")
        if "os.dup2" in names:
            site = (self.rel, self.functions[-1] if self.functions else None)
            self.scan.dup2_sites.add(site)
            if site not in DUP2_ALLOWED:
                self._hit(node, "os.dup2（复制出的号缺省可继承）")
        if "fcntl.fcntl" in names:
            located = len(node.args) >= 2 and not any(isinstance(a, ast.Starred) for a in node.args[:2])
            cmd = self._names(node.args[1]) if located else set()
            if not any(n.startswith("fcntl.") and n[len("fcntl."):] in FCNTL_COMMANDS for n in cmd):
                # 数字写的命令（如 0 即 F_DUPFD、2 即 F_SETFD）、变量或清单之外的常量：认不出是不是复制描述符、改它的标志
                self._hit(node, "fcntl.fcntl 的第二个参数不是放行的命令常量")
            if "fcntl.F_SETFD" in cmd:
                value = node.args[2] if len(node.args) > 2 else None
                if value is None or "fcntl.FD_CLOEXEC" not in self._names(value):
                    self._hit(node, "fcntl.fcntl 的 F_SETFD 设的值不是 FD_CLOEXEC")

    def _check_child_arguments(self, node: ast.Call, names: set[str]) -> None:
        # preexec_fn 按关键字传的在任何调用上都查：接收者可能是转手调用入口的包装（如 functools.partial）
        for k in node.keywords:
            if k.arg == "preexec_fn" and not _is_constant(k.value, None):
                self._hit(node, "带 preexec_fn 而值不是 None（它在 fork 之后、exec 之前执行 Python 代码）")
        entries = sorted(names & (SUBPROCESS_ENTRIES | ASYNCIO_ENTRIES))
        if not entries and isinstance(node.func, ast.Attribute) and node.func.attr in LOOP_CHILD_METHODS:
            entries = [node.func.attr]
        if not entries:
            return
        self.scan.child_entries += 1
        for k in node.keywords:
            if k.arg is None:
                self._hit(node, f"{entries[0]} 带展开的关键字参数，认不出里面有没有 preexec_fn 或 close_fds")
            elif k.arg == "close_fds" and not _is_constant(k.value, True):
                self._hit(node, f"{entries[0]} 带 close_fds 而值不是 True")
        if not names & SUBPROCESS_ENTRIES:
            return
        head = node.args[:_PREEXEC_FN_INDEX + 1]
        if any(isinstance(a, ast.Starred) for a in head):
            self._hit(node, f"{entries[0]} 的第 7 个参数之前有展开的参数，定位不到按位置传的 preexec_fn")
            return
        if len(node.args) > _PREEXEC_FN_INDEX and not _is_constant(node.args[_PREEXEC_FN_INDEX], None):
            self._hit(node, f"{entries[0]} 按位置传的 preexec_fn 不是 None")
        positional = node.args[:_CLOSE_FDS_INDEX + 1]
        if len(positional) > _CLOSE_FDS_INDEX and not any(isinstance(a, ast.Starred) for a in positional):
            if not _is_constant(positional[_CLOSE_FDS_INDEX], True):
                self._hit(node, f"{entries[0]} 按位置传的 close_fds 不是 True")

    def visit_Call(self, node: ast.Call) -> None:
        names = self._names(node.func)
        self._check_descriptor_calls(node, names)
        self._check_child_arguments(node, names)
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
    """三个生产包里起进程只经放行的入口、不带 preexec_fn 与 close_fds=False，没有把描述符变成可继承的写法，没有一次导入全部名字；
    dup2 只在放行登记的那一处，fcntl 只用放行清单里的名字。"""
    scan, files = _scan_production()
    assert files > 0 and scan.child_entries > 0, "扫描面失效：没有扫到文件，或一个起子进程的调用都没认出来"
    assert not scan.hits, (
        "持生命期锁的进程启动子进程只经 exec：这些写法会让子进程带着锁描述符活下去，持锁的进程被杀之后锁仍被持有，或者扫描认不出"
        "它的来源。改用 subprocess 缺省方式启动，不要把描述符设为可继承；确实要用清单之外的接口的，先在 ADR 0054 决策三里定下，"
        "再改这里的放行清单：\n  " + "\n  ".join(scan.hits))
    stale = sorted(DUP2_ALLOWED - scan.dup2_sites)
    assert not stale, f"DUP2_ALLOWED 里这些登记已找不到 os.dup2 的调用，请删除：{stale}"


@pytest.mark.parametrize("source", [
    # 放行入口之外的起进程接口：fork 与进程池
    "import os\nos.fork()",
    "import os as _os\n_os.fork()",
    "from os import fork\nfork()",
    "from os import forkpty as fp\nfp()",
    "import os\nos.forkpty()",
    "import os\nstart = os.fork",                          # 不调用、只引用也算：可能被当作回调交出去
    "import multiprocessing",
    "import multiprocessing.pool",
    "from multiprocessing import Process",
    "def f():\n    import multiprocessing as mp\n    mp.get_context('fork')",
    "from concurrent.futures import ProcessPoolExecutor",
    "import concurrent.futures\nconcurrent.futures.ProcessPoolExecutor()",
    "from concurrent import futures\nfutures.ProcessPoolExecutor(2)",
    "import concurrent.futures.process",
    # 放行入口之外的起进程接口：os 的其余各函数，pty 与 _posixsubprocess 模块
    "import os\nos.system('ls')",
    "import os\nrun_shell = os.system",
    "from os import system as sh",
    "import os\nos.popen('ls')",
    "import os\nos.spawnv(os.P_WAIT, path, argv)",
    "from os import spawnlp\nspawnlp(os.P_WAIT, 'ls', 'ls')",
    "import os\nos.posix_spawn(path, argv, env)",
    "import os\nos.posix_spawn(p, a, e, file_actions=[(os.POSIX_SPAWN_DUP2, fd, 5)])",
    "import os\nos.posix_spawnp(path, argv, env)",
    "import os\nos.startfile(path)",
    "import pty",
    "import pty\npty.fork()",
    "from pty import spawn",
    "import _posixsubprocess",
    "from _posixsubprocess import fork_exec",
    # posix 按 os 认
    "import posix\nposix.fork()",
    "import posix\nposix.forkpty()",
    "from posix import fork\nfork()",
    "import posix\nposix.system('ls')",
    "import posix as _px\n_px.set_inheritable(fd, True)",
    "import posix\nposix.dup2(a, b)",
    # 一次导入全部名字（任何模块，含相对导入）
    "from os import *\nfork()",
    "from posix import *",
    "from pty import *",
    "from fcntl import *\nfcntl(fd, F_SETFD, 0)",
    "from subprocess import *\nPopen(cmd, close_fds=False)",
    "from json import *",
    "from os.path import *",
    "from . import *",
    "from .helpers import *",
    # preexec_fn：按关键字传的在任何调用上都查，按位置传给 subprocess 各入口的第 7 个参数同样查
    "import subprocess, signal\nsubprocess.Popen(cmd, preexec_fn=signal.pause)",
    "import subprocess\nsubprocess.Popen(cmd, preexec_fn=hook)",
    "import subprocess\nsubprocess.run(cmd, preexec_fn=lambda: None)",
    "import subprocess\nsubprocess.Popen(cmd, -1, None, None, None, None, hook)",
    "import subprocess as _sp\n_sp.check_output(cmd, -1, None, None, None, None, lambda: None, True)",
    "import asyncio, os\nasync def f():\n    await asyncio.create_subprocess_exec(cmd, preexec_fn=os.setsid)",
    "async def f(loop):\n    await loop.subprocess_exec(factory, cmd, preexec_fn=hook)",
    "self.spawn(cmd, preexec_fn=hook)",
    "import functools, subprocess\nfunctools.partial(subprocess.Popen, preexec_fn=hook)",
    "import subprocess\nsubprocess.Popen(*argv)",               # 第 7 个参数之前有展开的参数：定位不到
    "import subprocess\nsubprocess.call(cmd, *rest)",
    "import subprocess\nsubprocess.Popen(cmd, **opts)",          # 展开的关键字参数：认不出里面有没有 preexec_fn、close_fds
    "import subprocess as _sp\n_sp.run(cmd, check=True, **opts)",
    "import asyncio\nasync def f():\n    await asyncio.create_subprocess_exec(cmd, **opts)",
    "async def f(loop):\n    await loop.subprocess_shell(factory, cmd, **opts)",
    # 描述符：设为可继承、dup2
    "import os\nos.set_inheritable(fd, True)",
    "import os\nos.set_inheritable(fd, flag)",              # 值不是字面量 False 一律不放行
    "import os\nos.set_inheritable(fd, inheritable=True)",
    "import os\nos.dup2(a, b)",
    "import os\ndef redirect_output(fd):\n    os.dup2(fd, 1)",  # 函数名对得上、文件不是登记的那一个
    # fcntl：放行清单之外的名字，命令不是放行的具名常量，清掉 CLOEXEC
    "import fcntl\nfcntl.ioctl(fd, request)",
    "import fcntl as _f\n_f.ioctl(fd, request)",
    "from fcntl import ioctl",
    "import fcntl\ncmd = fcntl.F_DUPFD",
    "from fcntl import F_DUP2FD",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_DUPFD, 3)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_DUP2FD, 5)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.LOCK_EX)",           # 放行清单里的名字，但不是放行的命令
    "import fcntl\nfcntl.fcntl(fd, fcntl.FD_CLOEXEC)",
    "import fcntl\nfcntl.fcntl(fd, 0, 3)",                   # 数字写的 F_DUPFD
    "import fcntl\nfcntl.fcntl(fd, 2, 0)",                   # 数字写的 F_SETFD，清掉 CLOEXEC
    "import fcntl\nfcntl.fcntl(fd, cmd, 0)",
    "from fcntl import fcntl\nfcntl(fd, 2, 0)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_SETFD, 0)",
    "from fcntl import fcntl, F_SETFD\nfcntl(fd, F_SETFD, 0)",
    # close_fds：各入口与事件循环的方法，按关键字或按位置
    "import subprocess\nsubprocess.Popen(cmd, close_fds=False)",
    "import subprocess as _sp\n_sp.run(cmd, close_fds=False)",
    "from subprocess import check_output\ncheck_output(cmd, close_fds=keep)",
    "import asyncio\nasync def f():\n    await asyncio.create_subprocess_exec(cmd, close_fds=False)",
    "async def f(loop):\n    await loop.subprocess_exec(factory, cmd, close_fds=False)",
    "async def f(self):\n    await self._loop.subprocess_shell(factory, cmd, close_fds=keep)",
    "import subprocess\nsubprocess.Popen(cmd, -1, None, None, None, None, None, False)",
    "import subprocess\nsubprocess.run(cmd, -1, None, None, None, None, None, keep)",
    # 继承 Popen
    "import subprocess\nclass P(subprocess.Popen):\n    pass",
    "from subprocess import Popen as _P\nclass Q(_P):\n    pass",
])
def test_scanner_flags_each_form_outside_the_allowlist(source):
    """放行清单之外的每一种写法（含经导入别名的、延迟导入的）都被认出来。"""
    assert scan_source("cli/gherkai_cli/example.py", source).hits, source


@pytest.mark.parametrize("source", [
    "import os\nos.set_inheritable(fd, False)",
    "import os\nos.dup(fd)",                               # dup 出的号不可继承
    "import subprocess\nsubprocess.Popen(cmd, pass_fds=(w,), start_new_session=True)",
    "import subprocess\nsubprocess.run(cmd, close_fds=True)",
    "import subprocess\nsubprocess.Popen(cmd, preexec_fn=None)",
    "self.spawn(cmd, preexec_fn=None)",
    "import subprocess\nsubprocess.Popen(cmd, -1, None, None, None, None, None, True)",
    "import subprocess\nsubprocess.getoutput(cmd)",
    "import subprocess\nsubprocess.getstatusoutput(cmd)",
    "import subprocess\nsubprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)",
    "import asyncio\nasync def f():\n    await asyncio.create_subprocess_exec(cmd, stdout=asyncio.subprocess.PIPE)",
    "async def f(loop):\n    await loop.subprocess_exec(factory, cmd)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 3)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_GETFD)",
    "import fcntl\nfcntl.fcntl(fd, fcntl.F_GETFL)",
    "import fcntl, os\nfcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)",
    "import fcntl\nfcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)",
    "import fcntl\nfcntl.lockf(fd, fcntl.LOCK_SH)",
    "from fcntl import flock, LOCK_EX, LOCK_UN\nflock(fd, LOCK_EX)\nflock(fd, LOCK_UN)",
    "def fork():\n    pass\nfork()",                       # 没有经导入绑定的局部名
    "import os\nos.register_at_fork(after_in_child=f)",
    "import posix\nposix.getpid()",
    "from os import path",
    "from . import compose",
    "from .run_dir import create_run_dir",
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
