"""运行期限的规则（ADR 0054 决策二）：停止启动的提前量 60 秒、「已过」取严格晚于、job 截止时刻取认领时刻加预算与期限中较早的
一个（相等算预算），以及记录里的时刻与 core 里的墙钟类型（带时区的 datetime）之间的解析与写法。

纯函数直测，绿即够：结论只靠这里的比较与算术，不依赖时钟、进程或存储的真实行为。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core import run_deadline as rd
from gherkai_core.errors import DefinitionContractError
from gherkai_core.model import RunMeta
from gherkai_core.serialize import instant_from_iso, instant_to_iso, run_meta_from_dict, run_meta_to_dict

UTC = timezone.utc
DEADLINE = datetime(2026, 11, 15, 10, 0, 0, tzinfo=UTC)
S = timedelta(seconds=1)


def test_stop_start_is_sixty_seconds_before_the_deadline():
    assert rd.STOP_START_LEAD_S == 60.0
    assert rd.stop_start_at(DEADLINE) == datetime(2026, 11, 15, 9, 59, 0, tzinfo=UTC)


@pytest.mark.parametrize("now, past", [
    (DEADLINE - 61 * S, False),
    (DEADLINE - 60 * S, False),  # 恰在停止启动的时刻：还没有「已过」
    (DEADLINE - 60 * S + timedelta(microseconds=1), True),
    (DEADLINE + 3600 * S, True),
])
def test_past_stop_start_is_strictly_after_the_stop_start_time(now, past):
    assert rd.past_stop_start(now, DEADLINE) is past


@pytest.mark.parametrize("now, past", [
    (DEADLINE - S, False),
    (DEADLINE, False),
    (DEADLINE + timedelta(microseconds=1), True),
])
def test_past_deadline_is_strictly_after_the_deadline(now, past):
    assert rd.past_deadline(now, DEADLINE) is past


def test_comparisons_hold_across_time_zones():
    """同一个时刻换个时区写，结论不变：比较的是时刻，不是字面。"""
    east8 = timezone(timedelta(hours=8))
    assert rd.past_stop_start(datetime(2026, 11, 15, 17, 59, 30, tzinfo=east8), DEADLINE) is True
    assert rd.past_deadline(datetime(2026, 11, 15, 17, 59, 30, tzinfo=east8), DEADLINE) is False


def test_naive_wall_clock_is_rejected_rather_than_compared():
    """不带时区的时刻不能与期限比较：Python 抛 TypeError，误注入的时钟不会悄悄得出结论。"""
    with pytest.raises(TypeError):
        rd.past_stop_start(datetime(2026, 11, 15, 9, 59, 30), DEADLINE)


def test_job_cutoff_is_the_budget_when_it_ends_before_the_deadline():
    claimed = DEADLINE - 1000 * S
    assert rd.job_cutoff(claimed, 300.0, DEADLINE) == rd.JobCutoff(at=claimed + 300 * S, by="budget")


def test_job_cutoff_is_capped_by_the_deadline():
    claimed = DEADLINE - 100 * S
    assert rd.job_cutoff(claimed, 300.0, DEADLINE) == rd.JobCutoff(at=DEADLINE, by="deadline")


def test_job_cutoff_equal_to_the_deadline_counts_as_the_budget():
    """认领时刻加预算恰等于期限：算 job 自己的预算到点，超时说明仍是预算那一句。"""
    claimed = DEADLINE - 300 * S
    assert rd.job_cutoff(claimed, 300.0, DEADLINE) == rd.JobCutoff(at=DEADLINE, by="budget")


def test_job_cutoff_keeps_sub_second_budgets():
    claimed = DEADLINE - 10 * S
    got = rd.job_cutoff(claimed, 2.5, DEADLINE)
    assert got == rd.JobCutoff(at=claimed + timedelta(seconds=2.5), by="budget")


def _meta(deadline_at: str) -> RunMeta:
    return RunMeta(run_id="r", created_at="2026-11-15T08:00:00+00:00", jobs=(), deadline_at=deadline_at)


def test_deadline_of_reads_the_definition_into_an_aware_datetime():
    got = rd.deadline_of(_meta("2026-11-15T18:00:00+08:00"))
    assert got == DEADLINE and got.tzinfo is not None


@pytest.mark.parametrize("bad", ["2026-11-15T10:00:00", "不是时刻", ""])
def test_deadline_of_and_the_definition_reader_reject_the_same_values(bad):
    """执行方取期限与读 definition 时的校验共用一处解析：读端拒绝的值，deadline_of 同样拒绝。"""
    with pytest.raises(ValueError):
        rd.deadline_of(_meta(bad))
    d = run_meta_to_dict(_meta("2026-11-15T10:00:00+00:00"))
    d["deadline_at"] = bad
    with pytest.raises(DefinitionContractError, match="deadline_at 须为带时区的 ISO 时刻"):
        run_meta_from_dict(d)


def test_instant_parse_and_write_round_trip_in_utc():
    east8 = timezone(timedelta(hours=8))
    t = datetime(2026, 11, 15, 18, 0, 0, 123456, tzinfo=east8)
    written = instant_to_iso(t)
    assert written == "2026-11-15T10:00:00.123456+00:00"
    assert instant_from_iso(written) == t
    assert instant_to_iso(instant_from_iso(written)) == written


@pytest.mark.parametrize("bad", [None, 1731664800, "2026-11-15T10:00:00", "x"])
def test_instant_from_iso_rejects_values_that_are_not_aware_iso_strings(bad):
    with pytest.raises(ValueError):
        instant_from_iso(bad)


def test_instant_to_iso_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="须带时区"):
        instant_to_iso(datetime(2026, 11, 15, 10, 0, 0))


def test_system_wall_clock_is_aware_utc():
    now = rd.system_wall_clock()
    assert now.utcoffset() == timedelta(0)
    assert abs((now - datetime.now(UTC)).total_seconds()) < 5
