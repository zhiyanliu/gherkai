"""运行期限的算式（ADR 0054 决策二）：一次性余量 900 秒，加上各 job 的墙钟预算与每 job 尾段之和；尾段本机取 2G + 10、云端取 210。"""
from __future__ import annotations

from datetime import datetime

import pytest

from gherkai_core.model import Job
from gherkai_runtime import compose, deadline, tunnel_host


def _job(sid: str, timeout_s: float) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact", scenarios=(), timeout_s=timeout_s)


def _offset_s(created_at: str, deadline_at: str) -> float:
    return (datetime.fromisoformat(deadline_at) - datetime.fromisoformat(created_at)).total_seconds()


def test_margins_reuse_the_tunnel_ttl_values():
    """一次性余量与隧道存活时间上限的同值，云端每 job 尾段直接复用它的每 job 余量（210 秒）。"""
    assert deadline.STARTUP_MARGIN_S == 900.0 == tunnel_host.CLOUD_STARTUP_MARGIN_S
    assert deadline.CLOUD_PER_JOB_TAIL_S == tunnel_host.CLOUD_PER_JOB_MARGIN_S == 210.0
    assert deadline.local_per_job_tail_s(31.0) == 72.0
    assert deadline.local_per_job_tail_s(150.0) == 310.0


def test_deadline_sums_budgets_and_per_job_tails_without_concurrency_discount():
    created = "2026-11-15T08:00:00.123456+00:00"
    jobs = [_job("a", 300.0), _job("b", 1500.0), _job("c", 7200.0)]
    got = deadline.compute_deadline_at(created, jobs, per_job_tail_s=deadline.CLOUD_PER_JOB_TAIL_S)
    assert _offset_s(created, got) == 900 + (300 + 1500 + 7200) + 3 * 210
    local = deadline.compute_deadline_at(created, jobs, per_job_tail_s=deadline.local_per_job_tail_s(150.0))
    assert _offset_s(created, local) == 900 + (300 + 1500 + 7200) + 3 * 310


def test_deadline_is_written_in_the_same_form_as_created_at():
    """与 compose.now_iso 同一写法（带微秒与 +00:00 的 UTC 时刻），别的机器读到的是同一个时刻。"""
    created = compose.now_iso()
    got = deadline.compute_deadline_at(created, [_job("a", 300.0)], per_job_tail_s=210.0)
    parsed = datetime.fromisoformat(got)
    assert parsed.utcoffset().total_seconds() == 0 and got.endswith("+00:00")
    assert _offset_s(created, got) == 1410.0
    # 别的时区写出的创建时刻也换算成 UTC
    assert deadline.compute_deadline_at("2026-11-15T16:00:00+08:00", [], per_job_tail_s=210.0) == "2026-11-15T08:15:00+00:00"


def test_record_instants_read_by_the_core_rules_round_trip_in_the_same_form():
    """组合根写下的时刻（创建时刻、算出的期限）经 core 的解析与写法往返不变：执行方比较的是同一个时刻，认领时刻写回记录时与
    `now_iso` 同一写法。"""
    from gherkai_core.model import RunMeta
    from gherkai_core.run_deadline import deadline_of
    from gherkai_core.serialize import instant_from_iso, instant_to_iso

    created = compose.now_iso()
    got = deadline.compute_deadline_at(created, [_job("a", 300.0)], per_job_tail_s=210.0)
    for written in (created, got):
        assert instant_to_iso(instant_from_iso(written)) == written
    meta = RunMeta(run_id="r", created_at=created, jobs=(_job("a", 300.0),), deadline_at=got)
    assert (deadline_of(meta) - instant_from_iso(created)).total_seconds() == 1410.0


def test_created_at_without_timezone_is_rejected():
    with pytest.raises(ValueError, match="须带时区"):
        deadline.compute_deadline_at("2026-11-15T08:00:00", [_job("a", 300.0)], per_job_tail_s=210.0)
