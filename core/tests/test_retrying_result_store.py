"""本机推进器的判定存储：保存失败时退避重试（`RetryingResultStore`，ADR 0030 决定三「保存明细失败」条）。

- 失败一次之后成功：等 1 秒，两次尝试用同一个标识，明细存下。
- 一直失败：共四次尝试，依次等 1、2、4 秒，抛出最后那个 OSError；每次失败留一句警告。
- 只对 OSError 重试，别的异常原样抛出、不等待。
- 读与探活原样转交。
等待经注入的 sleep 记下、不真等；被包住的判定存储是记录调用的替身，另有一条套在真实的本机文件存储上。
"""
from __future__ import annotations

import logging

import pytest

from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.adapters.result_store.retrying import SAVE_RETRY_DELAYS_S, RetryingResultStore
from gherkai_core.model import JobResult, Status
from tests.test_stores import _job_def

_ID = "00000000000000a1"


def _jr(scope_id: str = "a") -> JobResult:
    return JobResult(job=_job_def(scope_id, scope_id, "midscene"), status=Status.PASSED)


class _FlakyStore:
    """记下每次保存的 (run_id, result_id, scope_id)；前几次保存依次抛 failures 里的异常，用完之后存成功。"""

    def __init__(self, failures: list[BaseException] = ()) -> None:
        self.failures = list(failures)
        self.saves: list[tuple[str, str, str]] = []
        self.saved: dict[tuple[str, str], JobResult] = {}
        self.loads: list[tuple[str, str]] = []
        self.preflights = 0

    def save_job_result(self, run_id: str, result_id: str, job: JobResult) -> None:
        self.saves.append((run_id, result_id, job.scope_id))
        if self.failures:
            raise self.failures.pop(0)
        self.saved[(run_id, result_id)] = job

    def load_job_result(self, run_id: str, result_id: str) -> JobResult | None:
        self.loads.append((run_id, result_id))
        return self.saved.get((run_id, result_id))

    def preflight(self) -> None:
        self.preflights += 1


def test_the_default_delays_are_one_two_and_four_seconds():
    assert SAVE_RETRY_DELAYS_S == (1.0, 2.0, 4.0)


def test_one_failure_then_success_waits_one_second_and_keeps_the_id(caplog):
    """第一次保存失败、第二次成功：等 1 秒，两次尝试的标识都是调用方给出的那一个，明细存下；留一句警告。"""
    inner = _FlakyStore([OSError(28, "No space left on device")])
    slept: list[float] = []
    store = RetryingResultStore(inner, sleep=slept.append)
    with caplog.at_level(logging.WARNING, logger="gherkai_core.adapters.result_store.retrying"):
        store.save_job_result("run-1", _ID, _jr())
    assert slept == [1.0]
    assert inner.saves == [("run-1", _ID, "a"), ("run-1", _ID, "a")]
    assert inner.saved == {("run-1", _ID): _jr()}
    assert len(caplog.records) == 1 and "1 秒后重试" in caplog.records[0].getMessage()


def test_persistent_failure_tries_four_times_and_raises_the_last_error(caplog):
    """一直失败：首次加三次重试共四次尝试，三次重试之前依次等 1、2、4 秒，抛出的是第四次的 OSError；前三次失败各留一句警告，
    之后不再等待。"""
    errors = [OSError(28, f"第 {n} 次") for n in range(1, 5)]
    inner = _FlakyStore(errors)
    slept: list[float] = []
    store = RetryingResultStore(inner, sleep=slept.append)
    with caplog.at_level(logging.WARNING, logger="gherkai_core.adapters.result_store.retrying"):
        with pytest.raises(OSError) as raised:
            store.save_job_result("run-1", _ID, _jr())
    assert raised.value is errors[3]
    assert slept == [1.0, 2.0, 4.0]
    assert [rid for _run, rid, _sid in inner.saves] == [_ID] * 4
    assert inner.saved == {}
    assert len(caplog.records) == 3


@pytest.mark.parametrize("error", [ValueError("形态不对"), TypeError("参数不对"), KeyboardInterrupt()],
                         ids=["ValueError", "TypeError", "KeyboardInterrupt"])
def test_errors_other_than_oserror_are_not_retried(error):
    """别的异常是 code 的缺陷（或使用方中断），原样抛出：只尝试一次，不等待。"""
    inner = _FlakyStore([error])
    slept: list[float] = []
    store = RetryingResultStore(inner, sleep=slept.append)
    with pytest.raises(type(error)):
        store.save_job_result("run-1", _ID, _jr())
    assert slept == [] and len(inner.saves) == 1


def test_reads_and_preflight_are_passed_through():
    """读与探活原样转交给被包住的判定存储，不重试、不等待：读到的就是它给出的（含读不到时的 None）。"""
    inner = _FlakyStore()
    slept: list[float] = []
    store = RetryingResultStore(inner, sleep=slept.append)
    store.save_job_result("run-1", _ID, _jr())
    assert store.load_job_result("run-1", _ID) == _jr()
    assert store.load_job_result("run-1", "00000000000000b2") is None
    store.preflight()
    assert inner.loads == [("run-1", _ID), ("run-1", "00000000000000b2")]
    assert inner.preflights == 1 and slept == []


def test_retry_over_the_local_store_writes_one_file_under_the_given_id(tmp_path, monkeypatch):
    """套在真实的本机文件存储上：第一次写入抛 OSError（替换掉原子写那一步），重试写成，jobs/ 下只有 `<标识>.json` 一个文件，读回即
    存下的那一份。"""
    import gherkai_core.adapters.result_store.local as local_mod

    real_write = local_mod.atomic_write_json
    calls: list[str] = []

    def failing_once(path, obj, **kwargs):
        calls.append(path.name)
        if len(calls) == 1:
            raise OSError(28, "No space left on device")
        real_write(path, obj, **kwargs)

    monkeypatch.setattr(local_mod, "atomic_write_json", failing_once)
    slept: list[float] = []
    store = RetryingResultStore(LocalResultStore(tmp_path / "runs"), sleep=slept.append)
    store.save_job_result("run-1", _ID, _jr())
    assert calls == [f"{_ID}.json", f"{_ID}.json"] and slept == [1.0]
    assert sorted(p.name for p in (tmp_path / "runs" / "run-1" / "jobs").iterdir()) == [f"{_ID}.json"]
    assert store.load_job_result("run-1", _ID) == _jr()
