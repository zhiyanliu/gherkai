"""ResultStore 两个 adapter 的对拍（本机文件与 moto 上的 S3，不产生真实 AWS 费用）：同一批行为断言，覆盖 ADR 0030 决定三「点名」条
与决定六里定 ResultStore 后端为 S3 的那一条。

- 每次保存一份、带写入方给出的标识：同一个 job 以两个标识各存一份，各自读回、互不影响；同一个标识再存即覆盖；不存在的标识读回 None。
- 落点只由标识构成：本机的文件名与 S3 的键在 `jobs/` 之后都是 `<quote(标识)>.json`，不带 scope_id；scope_id 含 `/`、`:`、空格、汉字，
  以及 200 个字符以上的汉字 scope_id 都能存取（文件名长度与 scope_id 无关）；含 `/` 的标识也只占一段。
- 端口与两个 adapter 都不提供列举；S3 adapter 存、取、取不到都不发列举请求。
物理落点的取法各端不同（本机列 `jobs/` 目录，S3 列前缀），只在测试里用来核对落点，不经 adapter。
S3 一侧另有：键前缀隔离不同的 run；NoSuchKey 之外的读取失败照常抛出。
"""
from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import quote

import pytest

from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.model import JobResult, Status
from gherkai_core.ports import ResultStore
from tests.test_stores import _job_def, _sample_run

_ID_A = "00000000000000a1"
_ID_B = "00000000000000b2"


@dataclass
class _Side:
    """一个 adapter 与核对它的物理落点的办法。names(run_id) 是这个 run 的明细落点下各份的名字（本机为 jobs/ 下的文件名，S3 为键在
    jobs/ 之后的一段），排好序。"""

    store: object
    names: Callable[[str], list[str]]


@pytest.fixture(params=["local", "s3"])
def side(request, tmp_path) -> _Side:
    if request.param == "local":
        root = tmp_path / "runs"

        def local_names(run_id: str) -> list[str]:
            jobs_dir = root / run_id / "jobs"
            return sorted(p.name for p in jobs_dir.iterdir()) if jobs_dir.is_dir() else []

        return _Side(LocalResultStore(root), local_names)
    aws = request.getfixturevalue("aws")
    from gherkai_core.adapters.result_store.s3 import S3ResultStore

    def s3_names(run_id: str) -> list[str]:
        prefix = f"{run_id}/jobs/"
        listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix=prefix)
        return sorted(o["Key"][len(prefix):] for o in listed.get("Contents", []))

    return _Side(S3ResultStore(aws["s3"], aws["bucket"]), s3_names)


def _jr(scope_id: str, status: Status = Status.PASSED, *, session: str | None = None) -> JobResult:
    return JobResult(job=_job_def(scope_id, scope_id, "midscene"), status=status, session_id=session)


# ---------- 每次保存一份、按标识取 ----------

def test_saves_round_trip_by_id_with_the_definition_embedded(side):
    """样例 run 的两份明细各以一个标识存下，按标识读回与存下的相等（自包含：嵌完整的 job 定义）。"""
    r = _sample_run("run-2")
    ids = {jr.scope_id: f"{n:016x}" for n, jr in enumerate(r.details)}
    for jr in r.details:
        side.store.save_job_result("run-2", ids[jr.scope_id], jr)
    for jr in r.details:
        got = side.store.load_job_result("run-2", ids[jr.scope_id])
        assert got == jr
    assert side.store.load_job_result("run-2", ids["features/wiki.feature:6"]).job.scenarios[0].steps[1].text == "搜索 OpenAI"


def test_two_saves_of_one_job_under_two_ids_stay_apart(side):
    """同一个 job 的两份明细（两次执行各得一个结果）以两个标识各存一份：各自读回、互不覆盖，落点下是两份。"""
    first, second = _jr("a", Status.PASSED, session="s-1"), _jr("a", Status.FAILED, session="s-2")
    side.store.save_job_result("run-1", _ID_A, first)
    side.store.save_job_result("run-1", _ID_B, second)
    assert side.store.load_job_result("run-1", _ID_A) == first
    assert side.store.load_job_result("run-1", _ID_B) == second
    assert side.names("run-1") == [f"{_ID_A}.json", f"{_ID_B}.json"]


def test_saving_again_under_the_same_id_overwrites(side):
    """同一个标识再存一次即覆盖（只发生在同一次保存的重试上）：读回的是后存的那一份，落点下仍只有一份。"""
    side.store.save_job_result("run-1", _ID_A, _jr("a", Status.ERROR, session="s-1"))
    later = _jr("a", Status.ERROR, session="s-2")
    side.store.save_job_result("run-1", _ID_A, later)
    assert side.store.load_job_result("run-1", _ID_A) == later
    assert side.names("run-1") == [f"{_ID_A}.json"]


def test_an_id_without_a_detail_reads_none(side):
    """这个标识下没有明细时读回 None：run 下根本没有明细，以及 run 下有别的标识的明细两种情形。"""
    assert side.store.load_job_result("nope", _ID_A) is None
    side.store.save_job_result("run-1", _ID_A, _jr("a"))
    assert side.store.load_job_result("run-1", _ID_B) is None


# ---------- 落点只由标识构成 ----------

@pytest.mark.parametrize("scope_id", ["features/x.feature:7", "a b", "登录场景", "登" * 210],
                         ids=["slash-colon", "space", "chinese", "long-chinese"])
def test_the_name_is_the_id_alone_whatever_the_scope_id(side, scope_id):
    """落点名只由标识构成、与 scope_id 无关：scope_id 含 /、:、空格、汉字，或是 210 个汉字（按 scope_id 编码文件名时会超过文件名长度
    上限）都照常存取，落点下只有 `<标识>.json` 一份。"""
    jr = _jr(scope_id, Status.FAILED, session="s")
    side.store.save_job_result("run-s", _ID_A, jr)
    assert side.names("run-s") == [f"{_ID_A}.json"]
    assert side.store.load_job_result("run-s", _ID_A) == jr


def test_an_id_that_is_not_a_plain_name_stays_one_segment(side):
    """标识按不透明标识符编码成一段：含 / 的值不在 jobs/ 下造出子目录或子前缀，按同一个值读得回。"""
    odd = "x/y z"
    side.store.save_job_result("run-o", odd, _jr("a"))
    assert side.names("run-o") == [quote(odd, safe="") + ".json"]
    assert side.store.load_job_result("run-o", odd) == _jr("a")


# ---------- 不提供列举 ----------

def test_the_port_and_both_adapters_offer_no_listing():
    """ResultStore 端口只有按标识存、按标识取与探活三个方法；两个 adapter 的公开方法与端口一致，没有列举全部明细的读法。"""
    from gherkai_core.adapters.result_store.s3 import S3ResultStore

    def public(cls) -> set[str]:
        return {name for name, _ in inspect.getmembers(cls, inspect.isfunction) if not name.startswith("_")}

    assert public(ResultStore) == {"save_job_result", "load_job_result", "preflight"}
    assert public(LocalResultStore) == public(S3ResultStore) == public(ResultStore)


class _RecordingClient:
    """包住 boto3 的 s3 client，记下 adapter 调用了哪些 client 方法。"""

    def __init__(self, inner) -> None:
        self._inner = inner
        self.calls: list[str] = []

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            self.calls.append(name)
            return attr(*args, **kwargs)
        return call


def test_s3_store_saves_and_reads_without_listing(aws):
    """S3 adapter 存一份、按标识取回、取一个不存在的标识，发出的只有 PutObject 与 GetObject，没有列举请求（读明细不需要
    `s3:ListBucket`）。"""
    from gherkai_core.adapters.result_store.s3 import S3ResultStore

    client = _RecordingClient(aws["s3"])
    store = S3ResultStore(client, aws["bucket"])
    store.save_job_result("run-1", _ID_A, _jr("a"))
    assert store.load_job_result("run-1", _ID_A) == _jr("a")
    assert store.load_job_result("run-1", _ID_B) is None
    assert client.calls == ["put_object", "get_object", "get_object"]


# ---------- S3 一侧 ----------

def test_prefix_isolates_runs(aws):
    """带键前缀时，不同 run 同一个标识的明细各在各的前缀下，互不串。"""
    from gherkai_core.adapters.result_store.s3 import S3ResultStore

    store = S3ResultStore(aws["s3"], aws["bucket"], prefix="tenantX/")
    store.save_job_result("rA", _ID_A, _jr("s", Status.PASSED))
    store.save_job_result("rB", _ID_A, _jr("s", Status.FAILED))
    assert store.load_job_result("rA", _ID_A).status == Status.PASSED
    assert store.load_job_result("rB", _ID_A).status == Status.FAILED
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="tenantX/")
    assert sorted(o["Key"] for o in listed["Contents"]) == [f"tenantX/rA/jobs/{_ID_A}.json", f"tenantX/rB/jobs/{_ID_A}.json"]


def test_s3_load_lets_errors_other_than_no_such_key_through(aws):
    """只有 NoSuchKey 读作 None；别的读取失败照常抛出。没有 `s3:ListBucket` 权限时 S3 对不存在的键回 AccessDenied，那时同样抛出，
    不读作 None。"""
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.result_store.s3 import S3ResultStore

    class _Denying(_RecordingClient):
        def get_object(self, **kwargs):
            raise ClientError({"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "GetObject")

    store = S3ResultStore(_Denying(aws["s3"]), aws["bucket"])
    with pytest.raises(ClientError, match="AccessDenied"):
        store.load_job_result("run-1", _ID_A)
