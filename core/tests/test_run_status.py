"""run 状态的取法与结束写的说明表（ADR 0031 决定三「取法」与「结束写」小节）：纯函数与常量，不经存储。

两个写入口对运行态的作用（`ending_applied`、`commit_applied`）经两个 RunStore adapter 核对，见 test_ending_and_commit_writes.py。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import Status
from gherkai_core.run_status import RUN_ENDINGS, RunEnding, definition_unavailable_ending, run_status_of

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
