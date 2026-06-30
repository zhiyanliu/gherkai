"""_run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。

与 Midscene 腿 run-scope.test.ts **对称**：纯逻辑、注 fake nova、不连 AWS、不烧钱。
覆盖 v1.0 最核心、最易回归的派发逻辑——四条互斥分支 + 投票判定 yes>votes_n/2 + 异常网络分类。
emit 是模块级函数，monkeypatch 成捕获器读回事件。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_scope as rs


class _Meta:
    def __init__(self, tw):
        self.time_worked_s = tw
        self.trajectory_file_path = None  # _collect_traj 取它，None 即不收


class _FakeResult:
    """模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+ metadata（成本/trajectory）。"""
    def __init__(self, value: bool, tw=None):
        self.matches_schema = True
        self.parsed_response = value
        self.metadata = _Meta(tw) if tw is not None else None


class _FakeNova:
    """注入 fake：act_get 按布尔序列逐票回；act/go_to_url 记调用。act 可设异常模拟中途失败。
    tw_seq：每票 time_worked_s（测成本累加），None 则该票无成本。"""
    def __init__(self, bool_seq=(), act_raises=None, tw_seq=None):
        self._seq = list(bool_seq)
        self._tw = list(tw_seq) if tw_seq else None
        self._i = 0
        self.calls = []
        self._act_raises = act_raises

    def go_to_url(self, url):
        self.calls.append(("go_to_url", url))

    def act(self, instr):
        self.calls.append(("act", instr))
        if self._act_raises:
            raise self._act_raises
        return _FakeResult(True)

    def act_get(self, instr, schema):
        self.calls.append(("act_get", instr))
        v = self._seq[self._i] if self._i < len(self._seq) else False
        tw = self._tw[self._i] if self._tw and self._i < len(self._tw) else None
        self._i += 1
        return _FakeResult(v, tw=tw)


@pytest.fixture
def captured(monkeypatch):
    """monkeypatch 模块级 emit，收集事件到 list 供断言。"""
    evts = []
    monkeypatch.setattr(rs, "emit", lambda obj: evts.append(obj))
    return evts


def _step(keyword, text, index=0):
    return {"index": index, "keyword": keyword, "text": text}


def _done(evts):
    return next(e for e in evts if e["type"] == "step_done")


# ---- 派发分支 ----
def test_given_url_goes_to_nav_no_ai(captured):
    nova = _FakeNova()
    r = rs._run_step(nova, "sc:0", _step("Given", '打开 "https://example.com"'), [], 1)
    assert r == "passed"
    assert nova.calls == [("go_to_url", "https://example.com")]  # 不浪费 AI
    assert _done(captured).get("votes") is None  # 确定性导航无 votes


def test_when_natural_language_goes_to_act(captured):
    nova = _FakeNova()
    r = rs._run_step(nova, "sc:0", _step("When", '"搜索 OpenAI"'), [], 1)
    assert r == "passed"
    assert nova.calls[0][0] == "act"
    assert _done(captured).get("votes") is None  # 动作步无 votes


# ---- 投票多数票数学（ADR 0014 边界）----
def test_then_votes1_single_yes_passed(captured):
    nova = _FakeNova(bool_seq=[True])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), [], 1)
    assert r == "passed"
    assert _done(captured)["votes"] == {"yes": 1, "total": 1}


def test_then_votes3_majority_2of3_passed(captured):
    nova = _FakeNova(bool_seq=[True, False, True])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), [], 3)
    assert r == "passed"  # yes=2 > 3/2=1.5
    assert _done(captured)["votes"] == {"yes": 2, "total": 3}


def test_then_votes3_only_1of3_failed(captured):
    nova = _FakeNova(bool_seq=[True, False, False])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), [], 3)
    assert r == "failed"  # yes=1 不 > 1.5
    ev = _done(captured)
    assert ev["status"] == "failed" and ev["errorType"] == "assertion_failed"


def test_then_votes2_tie_failed(captured):
    nova = _FakeNova(bool_seq=[True, False])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), [], 2)
    assert r == "failed"  # yes=1 不 > 2/2=1，平票算失败（对称 Midscene，ADR 0028 有意设计）


# ---- act 中途网络瞬时失败 → error/network_error（本会话刚加分类，对称 Midscene）----
def test_act_transient_network_is_network_error(captured):
    import socket
    nova = _FakeNova(act_raises=ConnectionError("reset"))
    r = rs._run_step(nova, "sc:0", _step("When", '"做事"'), [], 1)
    assert r == "error"
    ev = _done(captured)
    assert ev["status"] == "error" and ev["errorType"] == "network_error"
    # gaierror EAI_AGAIN 也算瞬时（对齐建连路径分类）
    nova2 = _FakeNova(act_raises=socket.gaierror(socket.EAI_AGAIN, "temp"))
    captured.clear()
    assert rs._run_step(nova2, "sc:0", _step("When", '"做事"'), [], 1) == "error"
    assert _done(captured)["errorType"] == "network_error"


def test_act_non_network_is_engine_error(captured):
    nova = _FakeNova(act_raises=ValueError("AI boom"))
    r = rs._run_step(nova, "sc:0", _step("When", '"做事"'), [], 1)
    assert r == "error"
    assert _done(captured)["errorType"] == "engine_error"


# ---- _classify_act_error：SDK 异常树细分（ADR 0024 errorType 细化）----
def test_classify_timeout():
    from nova_act.types.act_errors import ActTimeoutError
    # __new__ 绕过 SDK 构造参数（只测 isinstance 映射，不跑 SDK 逻辑）
    e = ActTimeoutError.__new__(ActTimeoutError)
    assert rs._classify_act_error(e) == "timeout"


def test_classify_guardrail():
    from nova_act.types.act_errors import ActGuardrailsError
    e = ActGuardrailsError.__new__(ActGuardrailsError)
    assert rs._classify_act_error(e) == "guardrail"


def test_classify_network_beats_sdk_type():
    # 网络瞬时优先于 SDK 类型（ConnectionError 即便也是某 SDK 子类，先判 network）
    assert rs._classify_act_error(ConnectionError("reset")) == "network_error"


def test_classify_unknown_falls_back_engine_error():
    assert rs._classify_act_error(ValueError("boom")) == "engine_error"
    from nova_act.types.act_errors import ActError
    assert rs._classify_act_error(ActError.__new__(ActError)) == "engine_error"  # 未细分的 ActError → engine_error


# ---- time_worked_s 成本：多票按累加合计全 N 票（对称 Midscene，修只算最后一票的欠计）----
def test_then_votes3_cost_sums_all_votes(captured):
    nova = _FakeNova(bool_seq=[True, True, True], tw_seq=[1.0, 2.0, 3.0])  # 三票各 1/2/3 秒
    rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), [], 3)
    ev = _done(captured)
    assert ev["cost"] == {"time_worked_s": 6.0}  # 1+2+3，非旧逻辑的 3.0（只算最后一票）
