"""cli 测试的公共夹具。

**默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-deterministic` 的清单、doctor 的加载
计数、grace 下限全取同一份能力自述对象（`--capabilities`，ADR 0036「5.」/ ADR 0024「引擎自报下限」）。若让每个
用例真去问，用例就依赖「运行测试这台机器装了哪个引擎」——本机装了 Nova 就绿、干净环境以退出码 2 结束（「绿≠对」的经典形态：
结论靠环境、不靠被测逻辑）。故 autouse 只把**自述查询**那一层换成确定性假值，`compose.engine_min_grace` 的
缓存复用、cli 侧的取 max / 退出码 2 分流照真实运行；要验「查不到该怎样」的用例自己 monkeypatch 回去。

替身仍**先过定位链**（真 `resolve_worker_cmd`）：查询本来就以「本机有这个 worker」为前提，跳过这步会把
「本机没装该引擎 → 跳过或退出码 2」那条分支变成测不出来的死路（doctor 的跳过情形正是它），且让本该跳过的用例继续
往下走去碰真 AWS。故只换「问 worker」那一跳、不换「找 worker」那一跳；用例用 `_fake_locator` 之类的替身把
定位链摆成想要的形状，这里跟着它走。

**本机 run 目录**（ADR 0054 决策三、四）同一取向：
- `lock_holder`（autouse）：把 `compose.process_lock_holder` 换成返回测试用的持有者。进程内的 `main(["run", …])`、
  `_inline_children` 线程里的后台推进进程主体，以及用例自己经 `compose.process_lock_holder()` 建 run 的 store，都把生命期锁交给它；
  它在用例结束时关闭收下的描述符，锁随之放开，不在测试进程里一直累积。要看锁的用例请求这个夹具，读它收下的描述符。
- `_host_independent_filesystem_type`（autouse）：把边界检查取文件系统类型的那一步换成本平台清单的第一项，结论不依赖宿主的
  文件系统。带 `real_filesystem` 标记的用例不替换（起真实子进程的用例，子进程里没有这个替换）；本平台不在清单里、或宿主的系统
  临时目录取到的类型不在清单里时跳过，判断不了时照常执行（那多半是取法本身坏了，跳过会把它藏起来）。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from gherkai_core.adapters.run_store import run_dir
from gherkai_runtime import compose

from _fake_worker import fake_query_capabilities


class ClosingLockHolder:
    """测试用的持有者：记下收到的描述符，用例结束时由夹具关闭（锁随之放开）。生产用的持有者没有放开锁的方法。"""

    def __init__(self) -> None:
        self.fds: list[int] = []

    def hold(self, fd: int) -> None:
        self.fds.append(fd)

    def close_all(self) -> None:
        while self.fds:
            try:
                os.close(self.fds.pop())
            except OSError:
                pass


@pytest.fixture(autouse=True)
def lock_holder(monkeypatch):
    holder = ClosingLockHolder()
    monkeypatch.setattr(compose, "process_lock_holder", lambda: holder)
    yield holder
    holder.close_all()


@pytest.fixture(autouse=True)
def _host_independent_filesystem_type(request, monkeypatch):
    if request.node.get_closest_marker("real_filesystem") is not None:
        if sys.platform not in run_dir.ALLOWED_FILESYSTEMS:
            pytest.skip(f"本机后端在 {sys.platform} 上不可用，跳过真实文件系统的用例")
        tmp = request.getfixturevalue("tmp_path")
        check = run_dir.check_report_dir(Path(tmp))
        if check.verdict is run_dir.Boundary.OUTSIDE:
            pytest.skip(f"宿主的系统临时目录 {tmp} 所在的文件系统是 {check.fs_type}，不在本平台的清单里，跳过真实文件系统的用例")
        return
    allowed = run_dir.ALLOWED_FILESYSTEMS.get(sys.platform)
    if allowed:
        monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: allowed[0])


@pytest.fixture(autouse=True)
def _stub_engine_capabilities(monkeypatch):
    monkeypatch.setattr(compose, "query_capabilities", fake_query_capabilities)
    # 进程内缓存跨用例泄漏 → 上一个用例的值（或真 worker 的值）污染下一个；两头都清。
    compose._CAPABILITIES_CACHE.clear()
    yield
    compose._CAPABILITIES_CACHE.clear()


@pytest.fixture(autouse=True)
def _no_real_tunnel_sdk(monkeypatch):
    """**测试从不起真实的隧道**：开发环境与 CI 都装了隧道组件（ngrok 的 SDK），误调用会联网、在 ngrok 账号上建会话。生产代码只经
    `tunnel._import_sdk` 导入 SDK（前置检查与起隧道都经它）：这里把它换成记录调用并抛错的函数，被调用即说明某个用例走到了真实的
    SDK；抛出的 AssertionError 可能被调用方的宽泛异常处理吞掉，所以收尾时另按调用次数判失败。夹具本身不导入 SDK。

    要隧道的用例把假的隧道服务登记进 `tunnel.PROVIDERS`，或经 `NgrokTunnel(load_sdk=...)` / 自己对 `tunnel._import_sdk` 打桩注入假
    SDK（覆盖这里的替身）。同时去掉环境变量 NGROK_AUTHTOKEN：用例的结果不随运行测试的机器有没有令牌而变。"""
    from gherkai_runtime import tunnel

    calls: list[str] = []

    def _guarded_import_sdk():
        calls.append("import")
        raise AssertionError("测试不应导入真实的隧道 SDK：请登记假的隧道服务，或经 NgrokTunnel(load_sdk=...) 注入假 SDK")

    monkeypatch.setattr(tunnel, "_import_sdk", _guarded_import_sdk)
    monkeypatch.delenv("NGROK_AUTHTOKEN", raising=False)
    yield
    if calls:
        pytest.fail(f"用例导入了真实的隧道 SDK（{len(calls)} 次）：请登记假的隧道服务，或经 NgrokTunnel(load_sdk=...) 注入假 SDK")


@pytest.fixture(autouse=True)
def _signal_dispositions_are_restored():
    """入口改动的信号处置在每个用例之后恢复：submit 开始写出 run 标识时把 SIGINT 设为忽略、一直保持到进程退出，两种后台进程的入口
    把 SIGTERM 与 SIGHUP 设为缺省处置。在测试进程里这些入口执行完并不退出，不恢复的话后面的用例收不到 Ctrl-C 的 KeyboardInterrupt，
    靠真实 SIGINT 的用例会一直等下去。"""
    import signal

    saved = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
    yield
    for s, handler in saved.items():
        signal.signal(s, handler if handler is not None else signal.SIG_DFL)


@pytest.fixture(autouse=True)
def _presentation_is_environment_independent(monkeypatch):
    """人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。"""
    from gherkai_runtime import textui
    monkeypatch.setattr(textui, "use_color", lambda: False)
    monkeypatch.setattr(textui, "output_width", lambda: textui.NO_WRAP_WIDTH)
