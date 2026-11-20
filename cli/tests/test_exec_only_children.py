"""静态守护：持生命期锁的进程只经 exec 启动子进程（ADR 0054 决策三「不被子进程继承」与「前提」）。

锁随打开的文件描述走：子进程只要还共用那次打开，持锁的进程被杀之后锁仍在，「拿得到锁即管它的进程已不在」就不成立。锁描述符
由 `os.open` 打开、不可继承（PEP 446），生产用的持有者不交出它，所以风险只在两类写法：fork 而不 exec（子进程带着父进程的全部
描述符）；把描述符变成可继承，再以不关描述符的方式 exec。这里用 AST 扫 core、runtime、cli 三个生产包，逐个点名这些写法：

- 调用或引用 `os.fork`、`os.forkpty`、`pty.fork`；
- 导入或引用 `multiprocessing`、`concurrent.futures` 的进程池（`ProcessPoolExecutor` 与它所在的 `concurrent.futures.process`）；
- `os.set_inheritable` 的第二个参数不是字面量 `False`；
- `os.dup2`（复制出的号缺省可继承），只放行把日志接到标准输入、标准输出、标准错误的 `handoff.redirect_output`；`posix_spawn`
  的 `POSIX_SPAWN_DUP2` 同类；
- `fcntl.fcntl` 的不带 CLOEXEC 的复制（`F_DUPFD`），以及 `F_SETFD` 设的值不是 `FD_CLOEXEC`（清掉 CLOEXEC）；
- `subprocess` 与 `asyncio` 起子进程的各入口带 `close_fds`、而值不是字面量 `True`（收紧项：实测它单独不延长持有）。

名字经导入别名还原（`import subprocess as _sp`、`from os import fork as f` 都认得出）；没有经导入绑定的局部名不算。C 扩展里的
写法与经 `getattr`、`**kwargs` 拼出的调用扫描看不见，由真实执行覆盖（ADR 0054 决策三）。扫描器本身另有逐条的正反用例，扫描面
失效（目录不在、放行登记找不到对应的位置）即失败，不静默空扫。
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
_CHILD_ENTRIES = {
    "subprocess.Popen", "subprocess.run", "subprocess.call", "subprocess.check_call", "subprocess.check_output",
    "asyncio.create_subprocess_exec", "asyncio.create_subprocess_shell",
}


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
                    aliases.setdefault(a.asname, set()).add(a.name)
                else:
                    top = a.name.split(".")[0]
                    aliases.setdefault(top, set()).add(top)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for a in node.names:
                aliases.setdefault(a.asname or a.name, set()).add(f"{node.module}.{a.name}")
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
                full = f"{node.module}.{a.name}"
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
        if "fcntl.fcntl" in names and len(node.args) >= 2:
            cmd = self._names(node.args[1])
            if "fcntl.F_DUPFD" in cmd:
                self._hit(node, "fcntl.fcntl 的 F_DUPFD（不带 CLOEXEC 的复制）")
            if "fcntl.F_SETFD" in cmd:
                value = node.args[2] if len(node.args) > 2 else None
                if value is None or "fcntl.FD_CLOEXEC" not in self._names(value):
                    self._hit(node, "fcntl.fcntl 的 F_SETFD 设的值不是 FD_CLOEXEC")
        if names & _CHILD_ENTRIES:
            self.scan.child_entries += 1
            for k in node.keywords:
                if k.arg == "close_fds" and not (isinstance(k.value, ast.Constant) and k.value.value is True):
                    self._hit(node, f"{sorted(names & _CHILD_ENTRIES)[0]} 带 close_fds 而值不是 True")
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
])
def test_scanner_passes_allowed_forms(source):
    assert not scan_source("cli/gherkai_cli/example.py", source).hits, source


def test_scanner_allows_dup2_only_in_the_registered_function():
    """dup2 的放行按（文件, 函数）登记：登记的函数里放行，同一文件的别的函数里照样拦。"""
    allowed = "import os\ndef redirect_output(fd):\n    os.dup2(fd, 1)\n"
    rel = "runtime/gherkai_runtime/handoff.py"
    assert not scan_source(rel, allowed).hits
    assert scan_source(rel, allowed + "def other(fd):\n    os.dup2(fd, 2)\n").hits
