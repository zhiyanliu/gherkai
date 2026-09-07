"""_run_step 派发分支 + 投票多数票数学单测（ADR 0024/0014/0028）。

与 Midscene 引擎 run-scope.test.ts **对称**：纯逻辑、注 fake nova、不连 AWS、不烧钱。
覆盖 v1.0 最核心、最易回归的派发逻辑——四条互斥分支 + 投票判定 yes>votes_n/2 + 异常网络分类。
事件经注入的 fake sink（_FakeSink，fixture `captured`）收集读回——sink 作参数注入 _run_step/_run_scenario
（对称 Midscene testSink；ADR 0024 I/O 边缘可注入接口，此前 emit 是模块级、迁移后可注 fake 打桩）。
"""
import pytest

from gherkai_worker_novaact import run_scope as rs


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

    def act(self, instr, timeout=None):  # timeout：ADR 0024 act 有界返回（worker 传 ACT_TIMEOUT_S）
        self.calls.append(("act", instr))
        self.last_timeout = timeout
        if self._act_raises:
            raise self._act_raises
        return _FakeResult(True)

    def act_get(self, instr, schema, timeout=None):  # timeout：同上
        self.calls.append(("act_get", instr))
        self.last_timeout = timeout
        v = self._seq[self._i] if self._i < len(self._seq) else False
        tw = self._tw[self._i] if self._tw and self._i < len(self._tw) else None
        self._i += 1
        return _FakeResult(v, tw=tw)


class _FakeSink:
    """假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like
    （__iter__/索引/clear）——作 sink 传进 _run_step/_run_scenario，同时供 `_done(sink)`/`for e in sink` 断言。"""
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
    def clear(self):
        self._evts.clear()


@pytest.fixture
def captured():
    """假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。"""
    return _FakeSink()


def _step(keyword, text, index=0):
    return {"index": index, "keyword": keyword, "text": text}


def _done(evts):
    return next(e for e in evts if e["type"] == "step_done")


# ---- 派发分支 ----
def test_given_url_goes_to_nav_no_ai(captured):
    nova = _FakeNova()
    r = rs._run_step(nova, "sc:0", _step("Given", '打开 "https://example.com"'), 1, captured)
    assert r == "passed"
    assert nova.calls == [("go_to_url", "https://example.com")]  # 不浪费 AI
    assert _done(captured).get("votes") is None  # 确定性导航无 votes


def test_when_natural_language_goes_to_act(captured):
    nova = _FakeNova()
    r = rs._run_step(nova, "sc:0", _step("When", '"搜索 OpenAI"'), 1, captured)
    assert r == "passed"
    assert nova.calls[0][0] == "act"
    assert _done(captured).get("votes") is None  # 动作步无 votes


# ---- 投票多数票数学（ADR 0014 边界）----
def test_then_votes1_single_yes_passed(captured):
    nova = _FakeNova(bool_seq=[True])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 1, captured)
    assert r == "passed"
    assert _done(captured)["votes"] == {"yes": 1, "total": 1}


def test_then_votes3_majority_2of3_passed(captured):
    nova = _FakeNova(bool_seq=[True, False, True])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)
    assert r == "passed"  # yes=2 > 3/2=1.5
    assert _done(captured)["votes"] == {"yes": 2, "total": 3}


def test_then_votes3_only_1of3_failed(captured):
    nova = _FakeNova(bool_seq=[True, False, False])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)
    assert r == "failed"  # yes=1 不 > 1.5
    ev = _done(captured)
    assert ev["status"] == "failed" and ev["errorType"] == "assertion_failed"


def test_then_votes2_tie_failed(captured):
    nova = _FakeNova(bool_seq=[True, False])
    r = rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 2, captured)
    assert r == "failed"  # yes=1 不 > 2/2=1，平票算失败（对称 Midscene，ADR 0028 有意设计）


# ---- act 中途网络瞬时失败 → error/network_error（ADR 0028 act 中途分类，对称 Midscene）----
def test_act_transient_network_is_network_error(captured):
    import socket
    nova = _FakeNova(act_raises=ConnectionError("reset"))
    r = rs._run_step(nova, "sc:0", _step("When", '"做事"'), 1, captured)
    assert r == "error"
    ev = _done(captured)
    assert ev["status"] == "error" and ev["errorType"] == "network_error"
    # gaierror EAI_AGAIN 也算瞬时（对齐建连路径分类）
    nova2 = _FakeNova(act_raises=socket.gaierror(socket.EAI_AGAIN, "temp"))
    captured.clear()
    assert rs._run_step(nova2, "sc:0", _step("When", '"做事"'), 1, captured) == "error"
    assert _done(captured)["errorType"] == "network_error"


def test_act_non_network_is_engine_error(captured):
    nova = _FakeNova(act_raises=ValueError("AI boom"))
    r = rs._run_step(nova, "sc:0", _step("When", '"做事"'), 1, captured)
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
    rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)
    ev = _done(captured)
    assert ev["cost"] == {"time_worked_s": 6.0}  # 1+2+3，非旧逻辑的 3.0（只算最后一票）


# ---- step 级 trajectory reportRefs（ADR 0027 下沉）：本 step 的 act 轨迹挂进该 step 的 step_done ----
class _TrajResult:
    """带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。"""
    def __init__(self, value, path):
        self.matches_schema = True
        self.parsed_response = value
        self.metadata = type("M", (), {"time_worked_s": None, "trajectory_file_path": path})()


class _TrajNova:
    def __init__(self, paths):
        self._paths = list(paths)
        self._i = 0
    def act_get(self, instr, schema, timeout=None):
        p = self._paths[self._i]; self._i += 1
        return _TrajResult(True, p)
    def act(self, instr, timeout=None):
        return _TrajResult(True, self._paths[0])


def test_step_done_carries_step_level_trajectory_refs(captured):
    # AI 动作步：本 step 的 act 轨迹挂进 step_done.reportRefs（kind=trajectory）
    nova = _TrajNova(["/logs/sess/act_0_trajectory.json"])
    rs._run_step(nova, "sc:0", _step("When", '"做事"'), 1, captured)
    ev = _done(captured)
    assert ev["reportRefs"][0]["kind"] == "trajectory"
    assert ev["reportRefs"][0]["ref"] == "file:///logs/sess/act_0_trajectory.json"  # .html 不存在→回退 json


def test_then_votes_multiple_trajectories_on_one_step(captured):
    # N 票 AI 断言：每票一个 act 轨迹，都挂本 step（一个 step 多个 trajectory，label 编号）
    nova = _TrajNova(["/logs/act_0_trajectory.json", "/logs/act_1_trajectory.json", "/logs/act_2_trajectory.json"])
    rs._run_step(nova, "sc:0", _step("Then", '"对吗"'), 3, captured)
    refs = _done(captured)["reportRefs"]
    assert len(refs) == 3  # 三票三个轨迹，都挂这一个 step
    assert refs[0]["label"] == "trajectory 1" and refs[2]["label"] == "trajectory 3"


def test_deterministic_and_url_steps_have_no_traj_refs(captured):
    # 确定性导航步不调 act → 无 trajectory、step_done 不带 reportRefs
    nova = _FakeNova()
    rs._run_step(nova, "sc:0", _step("Given", '打开 "https://example.com"'), 1, captured)
    assert "reportRefs" not in _done(captured)


# ---- scope 内 step 短路（ADR 0031 决定六 / 0028）：_run_scenario 上游 error 后跳过后续、发 step_skipped ----
class _NavErrorNova:
    """go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。"""
    def __init__(self, nav_raises):
        self._nav_raises = nav_raises
        self.act_calls = 0
        self.act_get_calls = 0
    def go_to_url(self, url):
        raise self._nav_raises
    def act(self, instr, timeout=None):
        self.act_calls += 1
        return _FakeResult(True)
    def act_get(self, instr, schema, timeout=None):
        self.act_get_calls += 1
        return _FakeResult(True)


def test_run_scenario_shortcircuits_after_error(captured):
    # 上游 step（导航）error → 后续 step 不调 AI（省钱）、发 step_skipped。判据锁 status==error。
    nova = _NavErrorNova(ConnectionError("SSL reset"))
    steps = [
        _step("Given", '打开 "https://broken.example"', 0),  # 导航失败 → error
        _step("When", '"在页面上操作"', 1),                    # 应被短路（不调 act）
        _step("Then", '"页面有预期内容"', 2),                   # 应被短路（不调 act_get）
    ]
    statuses = rs._run_scenario(nova, "sc:0", steps, votes_n=1, sink=captured)
    # 上游 error 后：AI 一次没调（省钱、不在损坏环境上跑）
    assert nova.act_calls == 0 and nova.act_get_calls == 0
    # step 1/2 发 step_skipped（独立事件，非 step_done）
    skipped = [e for e in captured if e["type"] == "step_skipped"]
    assert [e["stepIndex"] for e in skipped] == [1, 2]
    assert all("status" not in e for e in skipped)  # step_skipped 无 status 字段
    # 被短路步不进 statuses → 不参与 _aggregate；scenario 判定由那个 error step 决定
    assert statuses == ["error"]
    assert rs._aggregate(statuses) == "error"


def test_run_scenario_no_shortcircuit_when_all_pass(captured):
    # 反向护栏：无 error 时不短路——每步照跑、无 step_skipped 事件。
    nova = _FakeNova(bool_seq=[True])
    steps = [_step("When", '"做事A"', 0), _step("Then", '"对吗"', 1)]
    statuses = rs._run_scenario(nova, "sc:0", steps, votes_n=1, sink=captured)
    assert statuses == ["passed", "passed"]
    assert [e for e in captured if e["type"] == "step_skipped"] == []


def test_run_scenario_failed_does_not_shortcircuit(captured):
    # 判据锁 status==error（不是 failed）：一个 failed 的断言步**不**短路后续——
    # failed 是业务结论、环境没坏，后续步该照跑（只有 error=执行故障才短路）。
    nova = _FakeNova(bool_seq=[False, True])  # 第一个 Then failed，第二个 Then passed
    steps = [_step("Then", '"对吗A"', 0), _step("Then", '"对吗B"', 1)]
    statuses = rs._run_scenario(nova, "sc:0", steps, votes_n=1, sink=captured)
    assert statuses == ["failed", "passed"]  # failed 不触发短路，第二步照跑
    assert [e for e in captured if e["type"] == "step_skipped"] == []
