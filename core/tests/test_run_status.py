"""run 状态的取法与结束写的说明表（ADR 0031 决定三「取法」与「结束写」小节）：纯函数与常量，不经存储。另有没有记录的执行在内存里
算出的运行态（`state_without_record`，ADR 0031 决定五「数据源」）与执行中的写的参数校验（`check_running_write`）。

两个写入口对运行态的作用（`ending_applied`、`commit_applied`）经两个 RunStore adapter 核对，见 test_ending_and_commit_writes.py。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import Job, JobResult, JobState, RunMeta, Scenario, Status, Step
from gherkai_core.run_status import (
    RUN_ENDINGS,
    RunEnding,
    check_running_write,
    definition_unavailable_ending,
    run_status_of,
    state_without_record,
)

P, R = Status.PENDING, Status.RUNNING
OK, FAIL, ERR, SKIP, ABT = Status.PASSED, Status.FAILED, Status.ERROR, Status.SKIPPED, Status.ABORTED


@pytest.mark.parametrize("jobs, expected", [
    # 有 job 未结束：全部是 pending 为 pending，否则为 running（已有 job 离开 pending，含已有终态的）
    ([P], P),
    ([P, P, P], P),
    ([R], R),
    ([P, R], R),
    ([OK, P], R),
    ([ERR, P], R),
    ([ABT, R, P], R),
    # 全部结束：error 先于 failed，failed 先于 aborted 与 skipped，其余为 passed
    ([OK, FAIL, ERR, ABT, SKIP], ERR),
    ([ABT, ERR], ERR),
    ([SKIP, ERR], ERR),
    ([OK, FAIL], FAIL),
    ([ABT, FAIL], FAIL),
    ([SKIP, FAIL], FAIL),
    ([OK, ABT], ABT),
    ([OK, SKIP], ABT),
    ([SKIP, SKIP], ABT),
    ([ABT], ABT),
    ([OK, OK], OK),
    ([OK], OK),
    # 零个 job 为 passed
    ([], OK),
])
def test_run_status_of_follows_the_rule(jobs, expected):
    """取法：有 job 未结束时 run 是前置态（全 pending 为 pending，否则 running）；全部结束时按 error、failed、aborted 或 skipped、
    passed 的次序取第一条成立的；没有执行完（有 skipped 或 aborted）而没有 error 与 failed 的 run 不是 passed。"""
    assert run_status_of(jobs) == expected


@pytest.mark.parametrize("statuses", [[P], [R, OK], [OK, ERR], [], [SKIP], [ABT, OK, FAIL]])
def test_run_status_is_terminal_iff_every_job_is(statuses):
    """run 是终态，当且仅当全部 job 是终态。"""
    from gherkai_core.model import TERMINAL_STATUSES
    assert (run_status_of(statuses) in TERMINAL_STATUSES) == all(s in TERMINAL_STATUSES for s in statuses)


def test_run_status_of_accepts_a_one_pass_iterable():
    """取法只读一遍输入：生成器与列表得出同一结果（调用方常传 `js.status for js in jobs.values()`）。"""
    assert run_status_of(s for s in [OK, P]) == R
    assert run_status_of(s for s in [OK, SKIP]) == ABT


def test_only_the_settle_rows_end_running_jobs():
    """不结束执行中 job 的来路恰是执行方自己到期、fail-fast、使用方中断，它们在说明表里 aborted 一格「不出现」；处置的两行结束执行中的
    job，带 aborted 的说明。说明表里没有运行定义不可用的变体（它由调用方带入原因）。"""
    assert {route for route, ending in RUN_ENDINGS.items() if not ending.ends_running_jobs} == {
        "deadline", "fail-fast", "interrupt"}
    for route in ("deadline", "fail-fast", "interrupt"):
        assert RUN_ENDINGS[route].aborted_message is None
    for route in ("settle-advancer-exited", "settle-past-deadline"):
        assert RUN_ENDINGS[route].aborted_message is not None
    assert not any(ending.definition_unavailable for ending in RUN_ENDINGS.values())


@pytest.mark.parametrize("route", ["settle-advancer-exited", "settle-past-deadline"])
def test_settle_rows_end_every_sentence_with_the_marker(route):
    """处置的两行，各句末尾另加「（已记为已结束）」；去掉它之后与另一条来路共用的句子相同（处置已过期限与执行方自己到期）。"""
    ending = RUN_ENDINGS[route]
    for sentence in (ending.run_message, ending.skipped_message, ending.aborted_message):
        assert sentence.endswith("（已记为已结束）")
    if route == "settle-past-deadline":
        deadline = RUN_ENDINGS["deadline"]
        assert ending.run_message.removesuffix("（已记为已结束）") == deadline.run_message
        assert ending.skipped_message.removesuffix("（已记为已结束）") == deadline.skipped_message


def test_definition_unavailable_ending_carries_only_the_reason():
    """运行定义不可用的变体只带读不到定义的原因：它是 run 级说明，skipped 与 aborted 的说明不给；执行中的 job 同样由它结束。"""
    ending = definition_unavailable_ending("原因")
    assert (ending.run_message, ending.skipped_message, ending.aborted_message) == ("原因", None, None)
    assert (ending.ends_running_jobs, ending.definition_unavailable) == (True, True)


@pytest.mark.parametrize("kwargs", [
    {"run_message": "r", "skipped_message": "s"},  # 不结束执行中 job 的来路
    {"run_message": "r", "skipped_message": "s", "aborted_message": "a", "ends_running_jobs": True},  # 结束它们的来路
    {"run_message": "r", "ends_running_jobs": True, "definition_unavailable": True},  # 运行定义不可用
])
def test_run_ending_accepts_the_three_shapes(kwargs):
    """三种形态都能构造。"""
    assert RunEnding(**kwargs).run_message == "r"


@pytest.mark.parametrize("kwargs", [
    {"run_message": "r"},  # 缺 pending 的说明
    {"run_message": "r", "aborted_message": "a", "ends_running_jobs": True},  # 结束执行中 job 也缺 pending 的说明
    # 带了 aborted 的说明却不结束执行中的 job：这句永远用不上，结束写成立与否也不随它变
    {"run_message": "r", "skipped_message": "s", "aborted_message": "a"},
    # 结束执行中的 job 却没有给它们的说明
    {"run_message": "r", "skipped_message": "s", "ends_running_jobs": True},
    {"run_message": "r", "skipped_message": "s", "ends_running_jobs": True, "definition_unavailable": True},
    {"run_message": "r", "aborted_message": "a", "ends_running_jobs": True, "definition_unavailable": True},
    {"run_message": "r", "definition_unavailable": True},  # 运行定义不可用的变体同样结束执行中的 job
])
def test_run_ending_rejects_other_shapes(kwargs):
    """形态不符即抛 ValueError：aborted 的说明给出与否必须与 ends_running_jobs 一致，运行定义不可用的变体只带 run 级说明、结束执行中
    的 job。"""
    with pytest.raises(ValueError):
        RunEnding(**kwargs)


# ---------- 执行中的写的参数校验 ----------

def test_check_running_write_accepts_only_running():
    """执行中的写只记 running：pending 只由建 run 写下，终态由终态写与结束写写下，其余都是参数错误。"""
    check_running_write(JobState("a", R, session_id="s"))
    for status in (P, OK, FAIL, ERR, SKIP, ABT):
        with pytest.raises(ValueError, match="running"):
            check_running_write(JobState("a", status))


# ---------- 没有记录的执行在内存里算出的运行态 ----------

def _meta(*scope_ids: str) -> RunMeta:
    jobs = tuple(Job(scope_id=s, scope_name=s, engine="novaact", timeout_s=300.0,
                     scenarios=(Scenario(id=f"{s}:1", name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
                 for s in scope_ids)
    return RunMeta(run_id="r", created_at="t0", jobs=jobs, deadline_at="2026-01-01T01:00:00+00:00")


def _result(meta: RunMeta, sid: str, status: Status, session_id: str | None = None) -> JobResult:
    return JobResult(job=next(j for j in meta.jobs if j.scope_id == sid), status=status, session_id=session_id)


@pytest.mark.parametrize("route, first, run_status", [
    ("fail-fast", ERR, ERR),
    ("interrupt", ABT, ABT),
    ("interrupt", ERR, ERR),  # 被中断而有 error 的 run 按取法为 error
    ("deadline", OK, ABT),
])
def test_state_without_record_ends_the_remaining_jobs_by_the_stop_source(route, first, run_status):
    """判出结果的 job 先记为终态（会话取明细里的），余下没有启动的 job 由来路的结束写记 skipped 并带那一行的说明，run 按取法成为
    终态，带 run 级说明与结束时刻；没有认领写，认领时刻为空。"""
    meta = _meta("a", "b", "c")
    state = state_without_record(meta, [_result(meta, "a", first, session_id="s-a")], route, ended_at="t1")
    ending = RUN_ENDINGS[route]
    assert state.jobs["a"] == JobState("a", first, session_id="s-a")
    assert state.jobs["b"] == JobState("b", SKIP, message=ending.skipped_message)
    assert state.jobs["c"] == JobState("c", SKIP, message=ending.skipped_message)
    assert (state.status, state.message, state.ended_at) == (run_status, ending.run_message, "t1")


@pytest.mark.parametrize("route", [None, "deadline", "fail-fast", "interrupt"])
def test_state_without_record_with_every_job_decided_is_the_commit_alone(route):
    """全部 job 都有结果时 run 随终态写成为终态，来路不再起作用：没有 run 级说明，状态按取法给出。"""
    meta = _meta("a", "b")
    state = state_without_record(meta, [_result(meta, "a", OK), _result(meta, "b", FAIL)], route, ended_at="t1")
    assert (state.status, state.message, state.ended_at) == (FAIL, None, "t1")
    assert [js.status for js in state.jobs.values()] == [OK, FAIL]


def test_state_without_record_with_no_result_is_the_ending_alone():
    """一个 job 都没有启动（如已过停止启动的时刻）：结束写把全部 job 记 skipped，run 为 aborted。"""
    meta = _meta("a", "b")
    state = state_without_record(meta, [], "deadline", ended_at="t1")
    assert {js.status for js in state.jobs.values()} == {SKIP}
    assert (state.status, state.message) == (ABT, RUN_ENDINGS["deadline"].run_message)


def test_state_without_record_gives_the_whole_run_state_after_a_fail_fast_stop():
    """一个 job 出错、一个 job 通过之后 fail-fast 停止启动余下的 job：整份运行态逐项与给定的值相同。判出结果的 job 取明细里的状态与
    会话（没有会话的为空），不带 job 级说明；没有启动的 job 记 skipped，带 fail-fast 那一行的说明；run 为 error，带 run 级说明与结束
    时刻。开始时刻、HWM 与认领时刻为空，认领计数为 0。"""
    from gherkai_core.model import RunState

    meta = _meta("a", "b", "c")
    results = [_result(meta, "a", ERR, session_id="s-a"), _result(meta, "b", OK)]
    state = state_without_record(meta, results, "fail-fast", ended_at="t1")
    assert state == RunState(
        run_id="r", status=ERR,
        jobs={
            "a": JobState("a", ERR, session_id="s-a", claimed_at=None, message=None),
            "b": JobState("b", OK, session_id=None, claimed_at=None, message=None),
            "c": JobState("c", SKIP, session_id=None, claimed_at=None, message=RUN_ENDINGS["fail-fast"].skipped_message),
        },
        started_at=None, ended_at="t1", high_water_mark=None, message=RUN_ENDINGS["fail-fast"].run_message, claim_count=0)
    assert list(state.jobs) == ["a", "b", "c"]  # 按运行定义的次序


def test_state_without_record_rejects_inconsistent_execution_facts():
    """参数错误抛 ValueError：仍有 job 没有结果，而执行事实给不出结束它们的来路（为空，或为「已发现 run 被别处结束」；零个 job 的
    run 同样没有任何一次写能使它结束），与有记录时的收尾同一处检查；结果不是终态或不在运行定义里。"""
    meta = _meta("a", "b")
    with pytest.raises(ValueError, match="没有给出可用于结束它们的来路"):
        state_without_record(meta, [_result(meta, "a", OK)], "ended-elsewhere", ended_at="t1")
    with pytest.raises(ValueError, match="没有给出可用于结束它们的来路"):
        state_without_record(meta, [_result(meta, "a", OK)], None, ended_at="t1")
    with pytest.raises(ValueError, match="没有给出可用于结束它们的来路"):
        state_without_record(_meta(), [], None, ended_at="t1")
    with pytest.raises(ValueError):
        state_without_record(meta, [_result(meta, "a", R)], "deadline", ended_at="t1")
    other = _meta("x")
    with pytest.raises(ValueError):
        state_without_record(meta, [_result(other, "x", OK)], "deadline", ended_at="t1")
