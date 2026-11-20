"""判定明细的点名（`named_details`，ADR 0030 决定三「点名」条）：标识的形态，与读者唯一的读法 `load_named_details` 的各个分支。

- `new_result_id`：16 个小写十六进制字符，各次生成互不相同。
- `load_named_details`：只读带标识的 job、按标识取，没带标识的一次都不读；结果按 scope_id 给出、次序同给出的 jobs；被点名而这个标识下
  没有明细，或读回的那一份属于另一个 job，都抛 `NamedDetailMissing`（OSError 的子类，带 run、scope、标识与读到的 scope）；判定存储的
  别的读取失败原样抛出。读不到与读错 job 两个分支在本机文件与 moto 上的 S3 两个 adapter 上各核一遍。
"""
from __future__ import annotations

import re

import pytest

from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.errors import NamedDetailMissing
from gherkai_core.model import JobResult, JobState, Status
from gherkai_core.named_details import load_named_details, new_result_id
from tests.test_stores import _job_def


def _jr(scope_id: str, status: Status = Status.PASSED) -> JobResult:
    return JobResult(job=_job_def(scope_id, scope_id, "midscene"), status=status)


class _CountingStore:
    """内存里的判定存储，记下每次按标识读的调用。"""

    def __init__(self, saved: dict[tuple[str, str], JobResult] | None = None, *, fail_with: BaseException | None = None):
        self.saved = dict(saved or {})
        self.fail_with = fail_with
        self.loads: list[tuple[str, str]] = []

    def save_job_result(self, run_id: str, result_id: str, job: JobResult) -> None:
        self.saved[(run_id, result_id)] = job

    def load_job_result(self, run_id: str, result_id: str) -> JobResult | None:
        self.loads.append((run_id, result_id))
        if self.fail_with is not None:
            raise self.fail_with
        return self.saved.get((run_id, result_id))

    def preflight(self) -> None: ...


# ---------- 标识 ----------

def test_new_result_id_is_sixteen_lowercase_hex_characters():
    """标识只用小写字母与数字（本机文件名可能落在不区分大小写的文件系统上），长 16 个字符（64 位随机数）。"""
    for _ in range(200):
        assert re.fullmatch(r"[0-9a-f]{16}", new_result_id())


def test_new_result_ids_do_not_repeat():
    """各次生成互不相同：一千次生成没有重复（64 位随机数下碰撞概率约 3e-14）。"""
    ids = [new_result_id() for _ in range(1000)]
    assert len(set(ids)) == len(ids)


# ---------- 只读被点名的 ----------

def test_reads_only_named_jobs_by_their_ids_in_the_given_order():
    """只有带标识的 job 被读、按各自的标识读；由结束写结束的（终态、没有标识）与未结束的 job 一次都不读、不在结果里。结果按 scope_id
    给出，次序同给出的 jobs。存储里同一个 job 另有一份没被点名的明细，读到的仍是被点名的那一份。"""
    named_b, named_a = _jr("b", Status.FAILED), _jr("a", Status.PASSED)
    store = _CountingStore({("r", "00000000000000b1"): named_b, ("r", "00000000000000a1"): named_a,
                            ("r", "00000000000000a2"): _jr("a", Status.ERROR)})
    jobs = [JobState("b", Status.FAILED, result_id="00000000000000b1"),
            JobState("c", Status.ABORTED, message="执行这个 run 的 gherkai 进程已退出（已记为已结束）"),
            JobState("d", Status.RUNNING),
            JobState("a", Status.PASSED, result_id="00000000000000a1")]
    got = load_named_details("r", jobs, store)
    assert got == {"b": named_b, "a": named_a}
    assert list(got) == ["b", "a"]
    assert store.loads == [("r", "00000000000000b1"), ("r", "00000000000000a1")]


def test_jobs_without_ids_read_nothing():
    """没有一个 job 带标识（全部由结束写结束，或还没有 job 结束）：一次都不读，结果为空。"""
    store = _CountingStore()
    jobs = [JobState("a", Status.SKIPPED, message="说明"), JobState("b", Status.PENDING)]
    assert load_named_details("r", jobs, store) == {}
    assert load_named_details("r", [], store) == {}
    assert store.loads == []


# ---------- 被点名而读不到 ----------

def test_a_named_detail_that_is_not_there_raises_named_detail_missing():
    """被点名的标识下没有明细：抛 NamedDetailMissing，带 run、scope 与标识，读到的 scope 为空；它是 FileNotFoundError 与 OSError 的
    子类（前台收尾由此落进读写记录失败的出口）。"""
    store = _CountingStore({("r", "00000000000000a1"): _jr("a")})
    jobs = [JobState("a", Status.PASSED, result_id="00000000000000a1"), JobState("b", Status.FAILED, result_id="00000000000000b1")]
    with pytest.raises(NamedDetailMissing) as raised:
        load_named_details("r", jobs, store)
    e = raised.value
    assert isinstance(e, FileNotFoundError) and isinstance(e, OSError)
    assert (e.run_id, e.scope_id, e.result_id, e.found_scope_id) == ("r", "b", "00000000000000b1", None)
    assert "b" in str(e) and "00000000000000b1" in str(e) and "可能已被删除" in str(e)


def test_a_named_detail_of_another_job_raises_named_detail_missing():
    """运行态里 a 的标识指向的那一份属于 b（运行记录被改动过）：不把 b 的明细附到 a 上，抛 NamedDetailMissing，读到的 scope 为 b。"""
    store = _CountingStore({("r", "00000000000000b1"): _jr("b")})
    with pytest.raises(NamedDetailMissing) as raised:
        load_named_details("r", [JobState("a", Status.PASSED, result_id="00000000000000b1")], store)
    e = raised.value
    assert (e.scope_id, e.result_id, e.found_scope_id) == ("a", "00000000000000b1", "b")
    assert "属于 job b" in str(e)


@pytest.mark.parametrize("error", [PermissionError(13, "Permission denied"), ValueError("内容损坏")],
                         ids=["PermissionError", "ValueError"])
def test_other_read_failures_pass_through_unchanged(error):
    """判定存储的别的读取失败（权限、内容损坏）原样抛出，不改写成 NamedDetailMissing。"""
    store = _CountingStore(fail_with=error)
    with pytest.raises(type(error)) as raised:
        load_named_details("r", [JobState("a", Status.PASSED, result_id="00000000000000a1")], store)
    assert raised.value is error and not isinstance(raised.value, NamedDetailMissing)


# ---------- 两个 adapter 上的读不到与读错 job ----------

@pytest.fixture(params=["local", "s3"])
def result_store(request, tmp_path):
    if request.param == "local":
        return LocalResultStore(tmp_path / "runs")
    aws = request.getfixturevalue("aws")
    from gherkai_core.adapters.result_store.s3 import S3ResultStore
    return S3ResultStore(aws["s3"], aws["bucket"])


def test_named_details_read_back_from_either_adapter(result_store):
    """两个 adapter 上：存下的两份按运行态里的标识读回；同一个 job 另一份没被点名的明细不被读到。"""
    a_named, a_other, b_named = _jr("a", Status.PASSED), _jr("a", Status.ERROR), _jr("b", Status.FAILED)
    result_store.save_job_result("r", "00000000000000a1", a_named)
    result_store.save_job_result("r", "00000000000000a2", a_other)
    result_store.save_job_result("r", "00000000000000b1", b_named)
    jobs = [JobState("a", Status.PASSED, result_id="00000000000000a1"), JobState("b", Status.FAILED, result_id="00000000000000b1"),
            JobState("c", Status.SKIPPED, message="说明")]
    assert load_named_details("r", jobs, result_store) == {"a": a_named, "b": b_named}


def test_a_missing_named_detail_raises_on_either_adapter(result_store):
    """两个 adapter 上：被点名的那一份不在（本机文件不存在、S3 回 NoSuchKey）都抛 NamedDetailMissing。"""
    result_store.save_job_result("r", "00000000000000a1", _jr("a"))
    with pytest.raises(NamedDetailMissing) as raised:
        load_named_details("r", [JobState("b", Status.PASSED, result_id="00000000000000b1")], result_store)
    assert (raised.value.scope_id, raised.value.found_scope_id) == ("b", None)


def test_a_named_detail_of_another_job_raises_on_either_adapter(result_store):
    """两个 adapter 上：标识指向的那一份属于别的 job 时抛 NamedDetailMissing，读到的 scope 是那一份的。"""
    result_store.save_job_result("r", "00000000000000b1", _jr("b"))
    with pytest.raises(NamedDetailMissing) as raised:
        load_named_details("r", [JobState("a", Status.PASSED, result_id="00000000000000b1")], result_store)
    assert raised.value.found_scope_id == "b"


def test_a_detail_deleted_after_it_was_named_raises_on_the_local_store(tmp_path):
    """本机：被点名的那一份存下之后被外部删除，读者按运行态读时抛 NamedDetailMissing，不当作这个 job 没有明细。"""
    store = LocalResultStore(tmp_path / "runs")
    store.save_job_result("r", "00000000000000a1", _jr("a"))
    (tmp_path / "runs" / "r" / "jobs" / "00000000000000a1.json").unlink()
    with pytest.raises(NamedDetailMissing):
        load_named_details("r", [JobState("a", Status.PASSED, result_id="00000000000000a1")], store)
