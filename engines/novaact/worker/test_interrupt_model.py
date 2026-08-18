"""flag-only 中断模型单测（ADR 0024 终止契约）。

锁两条曾致命的中断反模式的修复（见 ADR 0024 被拒方案）：建连早期 SIGTERM 误报 engine_error；signal handler raise 撞 playwright greenlet 切换区致死循环卡死。

与 test_run_step.py 同风格：纯逻辑、注 fake nova、不连 AWS、不烧钱、不真起子进程。
覆盖 flag-only 改造引入的新行为，防回归到会撞 greenlet 卡死的 raise 模型：
- handler 只置 _stop 标志、绝不 raise（根因：handler raise 撞 playwright greenlet 切换区致死循环卡死，见 ADR 0024 被拒方案）。
- SIGTERM/SIGINT 共用同一 flag-only handler（Ctrl-C 也协作式停）。
- act/act_get 传 timeout=ACT_TIMEOUT_S（act 有界返回，让标志位有限时间被检测）。
- scenario 循环 / 投票循环收到 _stop → 协作式停（正常 break/return，不 raise 穿透）。
- 退避用 _stop.wait（可被 set 唤醒），而非 time.sleep。
"""
import signal
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_scope as rs


@pytest.fixture(autouse=True)
def _reset_stop():
    """每个用例前后清 _stop（模块级单例，避免用例间串扰）。"""
    rs._stop.clear()
    yield
    rs._stop.clear()


class _FakeSink:
    """假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。"""
    def __init__(self):
        self._evts = []
    def emit(self, obj):
        self._evts.append(obj)
    def __iter__(self):
        return iter(self._evts)
    def __getitem__(self, i):
        return self._evts[i]
    def __len__(self):
        return len(self._evts)


@pytest.fixture
def captured():
    """假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。"""
    return _FakeSink()


def _step(keyword, text, index=0):
    return {"index": index, "keyword": keyword, "text": text}


class _Meta:
    def __init__(self):
        self.time_worked_s = None
        self.trajectory_file_path = None


class _FakeResult:
    def __init__(self, value=True):
        self.matches_schema = True
        self.parsed_response = value
        self.metadata = _Meta()


class _RecordNova:
    """记录 act/act_get 收到的 timeout；act_get 按布尔序列回。"""
    def __init__(self, bool_seq=(True,)):
        self._seq = list(bool_seq)
        self._i = 0
        self.act_timeouts = []
        self.act_get_timeouts = []
        self.act_get_calls = 0

    def go_to_url(self, url):
        pass

    def act(self, instr, timeout=None):
        self.act_timeouts.append(timeout)
        return _FakeResult(True)

    def act_get(self, instr, schema, timeout=None):
        self.act_get_calls += 1
        self.act_get_timeouts.append(timeout)
        v = self._seq[self._i] if self._i < len(self._seq) else True
        self._i += 1
        return _FakeResult(v)


# ---- handler flag-only：只置标志、绝不 raise（根治 handler raise 撞 greenlet 切换区致死循环卡死，见 ADR 0024 被拒方案）----
def test_signal_handler_only_sets_flag_never_raises():
    # 直接调**真** handler rs._on_signal（模块级函数、可 import 调，非闭包）：验它只置 _stop、绝不 raise
    # （raise 会撞 playwright greenlet 切换区致死循环卡死，见 ADR 0024 被拒方案）。signal handler 签名 (signum, frame)。
    assert not rs._stop.is_set()
    rs._on_signal(signal.SIGTERM, None)  # 真调 handler，不抛
    assert rs._stop.is_set()             # handler 置了标志


def test_sigterm_and_sigint_both_installed_as_flag_only(monkeypatch):
    # main() 应给 SIGTERM + SIGINT 都装 flag-only handler（Ctrl-C 原走默认 KeyboardInterrupt 同样撞 greenlet）。
    # 拦截 signal.signal 记录注册的 (signum, handler)，跑到装 handler 那步即可（不真建连）。
    installed = {}
    monkeypatch.setattr(rs.signal, "signal", lambda s, h: installed.__setitem__(s, h))
    # 让 main 在装完 handler 后、真干活前停下：stdin 给个 job，但 ensure_workflow_definition 打桩抛已知信号
    monkeypatch.setattr(rs.sys, "stdin", type("S", (), {"readline": staticmethod(lambda: '{"scope":{"id":"x"},"scenarios":[]}')})())

    class _Stop(Exception):
        pass

    def _boom(*a, **k):
        raise _Stop()
    monkeypatch.setattr(rs, "ensure_workflow_definition", _boom)
    try:
        rs.main()
    except _Stop:
        pass
    assert signal.SIGTERM in installed and signal.SIGINT in installed
    # 两个信号共用同一个 flag-only handler；调用它只置标志、不抛
    installed[signal.SIGTERM](signal.SIGTERM, None)
    assert rs._stop.is_set()
    installed[signal.SIGINT](signal.SIGINT, None)  # 再调不抛


# ---- act 有界返回：worker 给每个 act/act_get 传 timeout=ACT_TIMEOUT_S ----
def test_act_called_with_timeout(captured):
    nova = _RecordNova()
    rs._run_step(nova, "sc:0", _step("When", '"做事"'), 1, captured)
    assert nova.act_timeouts == [rs.ACT_TIMEOUT_S]  # 动作 act 传了 timeout


def test_act_get_called_with_timeout(captured):
    nova = _RecordNova(bool_seq=[True, True, True])
    rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)  # 3 票
    assert nova.act_get_timeouts == [rs.ACT_TIMEOUT_S] * 3  # 每票都传 timeout


# ---- 投票循环 _stop 检查：中途收到停止信号 → 不再投后续票、且不 emit 误导性 step_done ----
def test_vote_loop_stops_before_any_vote(captured):
    nova = _RecordNova(bool_seq=[True, True, True])
    rs._stop.set()  # 进 _run_step 前已置位 → 投票循环第一轮顶部即 break
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)
    assert nova.act_get_calls == 0          # 一票都没投（停止信号在循环顶生效）
    assert r == "aborted"                   # 返回 aborted（非 passed/failed）
    # 关键：**不 emit 任何 step_done**——否则会把「从未执行的断言」误标成 failed(0/3)、污染 RunReport
    assert not any(e["type"] == "step_done" for e in captured)


def test_vote_loop_stops_midway_no_bogus_verdict(captured):
    # votes_n=3、投了 1 票(True)后置位 → 若旧逻辑会用 votes=[True]/分母3 算出 failed(1/3) 并 emit——那是把
    # 外部中止伪装成断言失败（核心 failure_scenario）。修复后应：不 emit step_done、返回 aborted。
    nova = _RecordNova(bool_seq=[True, True, True])

    orig_act_get = nova.act_get
    def _act_get_then_stop(instr, schema, timeout=None):
        r = orig_act_get(instr, schema, timeout=timeout)
        rs._stop.set()  # 第一票投完就置位 → 第二轮循环顶 break，votes=[True] 不完整
        return r
    nova.act_get = _act_get_then_stop

    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)
    assert nova.act_get_calls == 1          # 只投了 1 票（第二轮顶部 _stop break）
    assert r == "aborted"                   # 不是 failed——中止非断言判定
    assert not any(e["type"] == "step_done" for e in captured)  # 不 emit bogus 的 assertion_failed(1/3)


def test_vote_loop_full_votes_then_stop_still_emits(captured):
    # 判据是「票不完整」而非「此刻 _stop」（ADR 0024「安全点丢弃没跑完的单元的判定，但不丢弃已成的执行事实」）：
    # votes_n=1（默认）时最常见的形态就是停止信号落在唯一那次 act_get 期间、而 act 已带回判定——verdict 与
    # 已真实发生的 time_worked_s（计费量）都是执行事实，须照常 emit（对称 When/Given 分支），交上层安全点退出。
    # 护栏防回归成「标志位一置就丢弃投满票的判定」：那会让该 step 的 verdict 与时长一起静默消失、run 级合计低报。
    nova = _RecordNova(bool_seq=[True])

    orig_act_get = nova.act_get
    def _act_get_then_stop(instr, schema, timeout=None):
        r = orig_act_get(instr, schema, timeout=timeout)
        r.metadata.time_worked_s = 3.5  # 这段时长真的烧了，不该随中止蒸发
        rs._stop.set()                  # 停止信号落在唯一那票的 act 期间（act 正常返回带回判定）
        return r
    nova.act_get = _act_get_then_stop

    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 1, captured)
    assert r == "passed"                        # 不是 aborted——票已投满，判定是执行事实
    done = [e for e in captured if e["type"] == "step_done"]
    assert len(done) == 1
    assert done[0]["status"] == "passed" and done[0]["votes"] == {"yes": 1, "total": 1}
    assert done[0]["cost"] == {"time_worked_s": 3.5}  # 真金白银的时长随事件报出


# ---- scenario 循环 _stop 检查：正常 break、不发 step_skipped（区别于 error 短路）----
def test_run_scenario_stops_on_flag_no_step_skipped(captured):
    nova = _RecordNova()
    rs._stop.set()  # 置位 → scenario 循环第一 step 前即 break
    steps = [_step("When", '"a"', 0), _step("When", '"b"', 1)]
    statuses = rs._run_scenario(nova, "sc:0", steps, 1, captured)
    assert statuses == []  # 一步没跑
    assert nova.act_timeouts == []  # 确认没调 act
    assert not any(e["type"] == "step_skipped" for e in captured)  # 停止不发 step_skipped（那是 error 短路语义）


def test_run_scenario_stops_midway(captured):
    # 跑了第一步后置位 → 第二步前 break
    nova = _RecordNova()
    steps = [_step("When", '"a"', 0), _step("When", '"b"', 1)]

    orig = rs._run_step
    calls = []

    def _wrap(n, sid, st, v, sink):
        calls.append(st["index"])
        r = orig(n, sid, st, v, sink)
        rs._stop.set()  # 第一步跑完就置位
        return r

    import unittest.mock as m
    with m.patch.object(rs, "_run_step", _wrap):
        rs._run_scenario(nova, "sc:0", steps, 1, captured)
    assert calls == [0]  # 只跑了第一步，第二步被 _stop break 掉
    assert not any(e["type"] == "step_skipped" for e in captured)


# ---- scenario_done 出口 + 中止护栏：中途 _stop → 不 emit（不把没跑完的 scenario 标成假 passed）----
def test_scenario_done_emitted_when_not_stopped(captured):
    # 正常完成（_stop 未置）：emit scenario_done、带聚合判定；返 False（继续跑后续 scenario）。
    aborted = rs._emit_scenario_done_unless_stopped(captured, "sc:0", ["passed", "passed"])
    assert aborted is False
    done = [e for e in captured if e["type"] == "scenario_done"]
    assert len(done) == 1 and done[0]["status"] == "passed" and done[0]["scenarioId"] == "sc:0"


def test_scenario_done_suppressed_when_stopped(captured):
    # 中途中止（_stop 置位，statuses 只含中止前的部分 step）：**不 emit** scenario_done（否则 _aggregate(["passed"])
    # 会把没跑完的 scenario 标成确定 passed，假阳性），返 True 让 _run_session 停。（ADR 0031/0024「worker 不越权标注」）
    rs._stop.set()
    aborted = rs._emit_scenario_done_unless_stopped(captured, "sc:0", ["passed"])
    assert aborted is True
    assert not any(e["type"] == "scenario_done" for e in captured)  # 关键：中止不留假 verdict


def test_scenario_done_suppressed_even_with_zero_statuses(captured):
    # 极端：中止发生在首 step 前（statuses=[]）→ _aggregate([])=="passed" 更是纯假阳性 → 同样不 emit。
    rs._stop.set()
    aborted = rs._emit_scenario_done_unless_stopped(captured, "sc:0", [])
    assert aborted is True
    assert not any(e["type"] == "scenario_done" for e in captured)


# ---- 建连退避 _backoff_interrupted：收到停止信号即唤醒返回 True（驱动 run_scope 真退避路径）----
def test_backoff_interrupted_wakes_on_stop():
    # 驱动 run_scope 的**真** _backoff_interrupted（内部 _stop.wait）——非 stdlib Event.wait 同义反复：
    # 若有人把它改回 time.sleep(backoff)，set 标志后本函数会睡满 backoff、dt 不会 <1s，本测试红。
    import threading
    rs._stop.clear()
    threading.Timer(0.05, rs._stop.set).start()
    t0 = time.monotonic()
    interrupted = rs._backoff_interrupted(0)  # attempt 0 → backoff 0.5s；被 set 唤醒应 ~0.05s 返回 True
    dt = time.monotonic() - t0
    assert interrupted is True  # 退避中收到停止信号 → True（调用方据此 break、不再重连）
    assert dt < 0.4             # 远小于 backoff(0.5s)，证明被唤醒而非睡满


def test_backoff_interrupted_times_out_without_stop():
    # 无停止信号 → 睡满 backoff、返回 False（调用方据此继续下一 attempt）。用最短 backoff（attempt 0=0.5s）。
    rs._stop.clear()
    t0 = time.monotonic()
    interrupted = rs._backoff_interrupted(0)
    dt = time.monotonic() - t0
    assert interrupted is False  # 没被唤醒 → False
    assert dt >= 0.5             # 睡满了 backoff（attempt 0 = 0.5s）


# ---- 无残留：模块不再定义 _Terminated/_NetworkExhausted（防回归到 raise 模型）----
def test_raise_model_classes_removed():
    assert not hasattr(rs, "_Terminated"), "flag-only 后不应再有 _Terminated（raise 模型已废弃，见 ADR 0024 被拒方案）"
    assert not hasattr(rs, "_NetworkExhausted"), "flag-only 后不应再有 _NetworkExhausted"
