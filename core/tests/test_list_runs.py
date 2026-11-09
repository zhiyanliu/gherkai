"""RunStore.list_runs 的单测（ADR 0041 决策七「core 端口」「本机实现」「云端实现」）。

本机侧用真目录造 run；云端侧两套：moto 建带列举 GSI 的 runs 表（分区键 status、排序键 run_id、KEYS_ONLY），测与本机同一批
行为与读回形状；moto 造不出的情形（Query 一页不足 Limit 却还有下一页、索引尚未跟上导致的重复键与 STATE 已不在、读回的状态已
不在所请求的分区、未处理键）用只实现列举所需三样的假表测。
"""
from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from gherkai_core.adapters.run_store import ddb as ddb_module
from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore, RunListingIncomplete
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import JobState, RunListing, RunMeta, RunState, Status
from tests.test_stores import _initial_state

_LIST_INDEX = "status-run_id-index"
_TABLE = "gherkai-runs-listing"


def _meta(run_id: str, cli_version: str | None = "1.5.0") -> RunMeta:
    return RunMeta(run_id=run_id, created_at="2026-07-01T00:00:00Z", jobs=(), cli_version=cli_version)


def _make(store, run_id: str, status: Status, *, cli_version: str | None = "1.5.0") -> None:
    """建一个 run，初始运行态的总状态直接设为 status（列举只看读回的状态，不必经生命周期写入推到那里）。"""
    state = dataclasses.replace(_initial_state(run_id, ["a.feature:3"]), status=status)
    store.create_run(_meta(run_id, cli_version), state)


def _ids(rows: list[RunListing]) -> list[str]:
    return [r.run_id for r in rows]


# ============================================================================
# 本机
# ============================================================================


@pytest.fixture
def local_root(tmp_path: Path) -> Path:
    """同一报告落点下：四个终态 run、一个 detached 的 running、一个前台遗留的 pending，外加两样不是 run 的东西。"""
    plain, detached = LocalRunStore(tmp_path), LocalRunStore(tmp_path, detached=True)
    _make(plain, "run-01", Status.PASSED, cli_version="1.4.0")
    _make(plain, "run-02", Status.PASSED)
    _make(plain, "run-03", Status.FAILED)
    _make(plain, "run-04", Status.PASSED)
    _make(detached, "run-05", Status.RUNNING)
    _make(plain, "run-06", Status.PENDING)
    (tmp_path / "not-a-run").mkdir()  # 没有 run_state.json：跳过
    (tmp_path / "stray.txt").write_text("x", encoding="utf-8")  # 落点根下的文件：跳过
    return tmp_path


def test_local_list_runs_non_terminal_unbounded_with_detached_and_header(local_root: Path):
    rows = LocalRunStore(local_root).list_runs([Status.PENDING, Status.RUNNING], limit=None)
    assert _ids(rows) == ["run-06", "run-05"]
    by_id = {r.run_id: r for r in rows}
    assert by_id["run-05"].state.status == Status.RUNNING and by_id["run-05"].detached is True
    assert by_id["run-06"].state.status == Status.PENDING and by_id["run-06"].detached is False
    assert by_id["run-06"].header == (1, "1.5.0")
    assert by_id["run-06"].state.started_at == "2026-07-01T00:00:00Z"  # 读回的是完整运行态


def test_local_list_runs_limit_is_per_status_and_result_is_run_id_descending(local_root: Path):
    store = LocalRunStore(local_root)
    # passed 有 01/02/04 三条，limit=2 取 run_id 最大的两条；failed 只有 03；合起来整体降序
    assert _ids(store.list_runs([Status.PASSED, Status.FAILED], limit=2)) == ["run-04", "run-03", "run-02"]
    assert _ids(store.list_runs([Status.PASSED, Status.FAILED], limit=None)) == ["run-04", "run-03", "run-02", "run-01"]
    assert store.list_runs([Status.PASSED], limit=None)[-1].header == (1, "1.4.0")  # 写出版本照读、不过结构版本闸
    # 重复给出的状态不产生重复行
    assert _ids(store.list_runs([Status.PASSED, Status.PASSED], limit=1)) == ["run-04"]
    assert store.list_runs([], limit=None) == []


def _write_state_raw(root: Path, run_id: str, content: bytes) -> None:
    run_dir = root / run_id
    run_dir.mkdir()
    (run_dir / "run_state.json").write_bytes(content)


def test_local_list_runs_lists_every_unreadable_run_regardless_of_status_and_limit(local_root: Path):
    store = LocalRunStore(local_root)
    _write_state_raw(local_root, "run-07", b"{not json")
    # 状态值本版本不认识（由更新的版本写出）：本机看得到，带 detached 标记
    _write_state_raw(local_root, "run-08", json.dumps(
        {"run_id": "run-08", "status": "paused", "detached": True, "jobs": []}).encode())
    (local_root / "run-08" / "run_meta.json").write_text(
        json.dumps({"schema_version": 2, "cli_version": "9.0.0"}), encoding="utf-8")
    # run 级状态认识、job 状态值不认识
    _write_state_raw(local_root, "run-09", json.dumps(
        {"run_id": "run-09", "status": "passed", "jobs": [{"scope_id": "s", "status": "paused"}]}).encode())
    _write_state_raw(local_root, "run-10", b"\xff\xfe\x00broken")  # 编码不对：同样是内容损坏
    _write_state_raw(local_root, "run-11", b"[1, 2]")  # 形态违约：不是对象

    rows = store.list_runs([Status.PASSED], limit=1)
    # 无法读取的行不参与状态归入与截取：passed 仍取到 run-04 一条，五个无法读取的全部列出
    assert _ids(rows) == ["run-11", "run-10", "run-09", "run-08", "run-07", "run-04"]
    unreadable = {r.run_id: r for r in rows if r.state is None}
    assert set(unreadable) == {"run-07", "run-08", "run-09", "run-10", "run-11"}
    assert unreadable["run-08"].detached is True and unreadable["run-08"].header == (2, "9.0.0")
    assert unreadable["run-07"].detached is False and unreadable["run-07"].header is None  # 没有 run_meta.json
    # 只请求非终态时它们同样列出（找到即列出）
    assert {r.run_id for r in store.list_runs([Status.PENDING], limit=None) if r.state is None} == set(unreadable)


@pytest.mark.parametrize("content", [b"{broken", b"[]", json.dumps({"schema_version": "x"}).encode()])
def test_local_list_runs_reads_unparseable_header_as_none(tmp_path: Path, content: bytes):
    store = LocalRunStore(tmp_path)
    _make(store, "run-01", Status.PASSED)
    (tmp_path / "run-01" / "run_meta.json").write_bytes(content)
    [row] = store.list_runs([Status.PASSED], limit=None)
    assert row.state is not None and row.header is None


def test_local_list_runs_missing_root_is_empty_and_bad_limit_is_rejected(tmp_path: Path):
    assert LocalRunStore(tmp_path / "never-written").list_runs([Status.PASSED], limit=None) == []
    with pytest.raises(ValueError):
        LocalRunStore(tmp_path).list_runs([Status.PASSED], limit=0)


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root 无视文件权限")
def test_local_list_runs_does_not_swallow_access_failures(tmp_path: Path):
    store = LocalRunStore(tmp_path)
    _make(store, "run-01", Status.PASSED)
    meta_path = tmp_path / "run-01" / "run_meta.json"
    meta_path.chmod(0)
    try:
        with pytest.raises(PermissionError):  # 头部读不到是访问失败，不吞成「版本未知」
            store.list_runs([Status.PASSED], limit=None)
    finally:
        meta_path.chmod(0o600)
    root = tmp_path / "locked"
    root.mkdir()
    root.chmod(0)
    try:
        with pytest.raises(PermissionError):  # 报告落点存在但不可读
            LocalRunStore(root).list_runs([Status.PASSED], limit=None)
    finally:
        root.chmod(0o700)


# ============================================================================
# 云端：moto
# ============================================================================


@pytest.fixture
def listing_table(aws):
    """moto 下带列举 GSI 的 runs 表（索引名取构造参数同一个常量）。"""
    return aws["ddb"].create_table(
        TableName=_TABLE,
        KeySchema=[
            {"AttributeName": "run_id", "KeyType": "HASH"},
            {"AttributeName": "item_type", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "run_id", "AttributeType": "S"},
            {"AttributeName": "item_type", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[{
            "IndexName": _LIST_INDEX,
            "KeySchema": [
                {"AttributeName": "status", "KeyType": "HASH"},
                {"AttributeName": "run_id", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "KEYS_ONLY"},
        }],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture
def cloud_runs(listing_table):
    """与本机 fixture 同一组 run（不含两样非 run 的东西）。"""
    plain = DynamoDBRunStore(listing_table, list_index_name=_LIST_INDEX)
    detached = DynamoDBRunStore(listing_table, detached=True, list_index_name=_LIST_INDEX)
    _make(plain, "run-01", Status.PASSED, cli_version="1.4.0")
    _make(plain, "run-02", Status.PASSED)
    _make(plain, "run-03", Status.FAILED)
    _make(plain, "run-04", Status.PASSED)
    _make(detached, "run-05", Status.RUNNING)
    _make(plain, "run-06", Status.PENDING)
    return plain


def test_ddb_list_runs_matches_local_semantics(cloud_runs):
    store = cloud_runs
    rows = store.list_runs([Status.PENDING, Status.RUNNING], limit=None)
    assert _ids(rows) == ["run-06", "run-05"]
    by_id = {r.run_id: r for r in rows}
    assert by_id["run-05"].state.status == Status.RUNNING and by_id["run-05"].detached is True
    assert by_id["run-06"].detached is False and by_id["run-06"].header == (1, "1.5.0")
    assert by_id["run-06"].state == _initial_state("run-06", ["a.feature:3"])  # 读回与 load_run_state 同一转换
    assert by_id["run-06"].state == store.load_run_state("run-06")

    assert _ids(store.list_runs([Status.PASSED, Status.FAILED], limit=2)) == ["run-04", "run-03", "run-02"]
    assert _ids(store.list_runs([Status.PASSED, Status.FAILED], limit=None)) == ["run-04", "run-03", "run-02", "run-01"]
    assert store.list_runs([Status.PASSED], limit=None)[-1].header == (1, "1.4.0")
    assert _ids(store.list_runs([Status.PASSED, Status.PASSED], limit=1)) == ["run-04"]
    assert store.list_runs([], limit=None) == []


def test_ddb_list_runs_projection_keeps_every_run_state_field(listing_table):
    # 运行态的每个字段都有值：读回的投影少取任何一个属性（结束时刻、run 级消息、高水位、job 的会话与抢占时刻），都与 load_run_state 不等
    store = DynamoDBRunStore(listing_table, list_index_name=_LIST_INDEX)
    full = RunState(
        run_id="run-01", status=Status.FAILED,
        jobs={"a.feature:3": JobState(scope_id="a.feature:3", status=Status.FAILED, session_id="sess-1",
                                      claimed_at="2026-07-01T00:00:01Z")},
        started_at="2026-07-01T00:00:00Z", ended_at="2026-07-01T00:05:00Z", high_water_mark=7,
        message="worker 启动失败")
    store.create_run(_meta("run-01"), full)
    [row] = store.list_runs([Status.FAILED], limit=None)
    assert row.state == full
    assert row.state == store.load_run_state("run-01")


def test_ddb_list_runs_marks_unparseable_state_and_header(cloud_runs, listing_table):
    # STATE 的 job 状态值本版本不认识；META 的结构版本不是整数
    listing_table.put_item(Item={"run_id": "run-07", "item_type": "STATE", "status": "passed",
                                 "jobs": {"s": {"status": "paused"}}})
    listing_table.put_item(Item={"run_id": "run-07", "item_type": "META", "schema_version": 3, "cli_version": "9.0.0",
                                 "meta_json": "{}"})
    listing_table.put_item(Item={"run_id": "run-08", "item_type": "STATE", "status": "passed", "jobs": {}})
    listing_table.put_item(Item={"run_id": "run-08", "item_type": "META", "schema_version": "x", "meta_json": "{}"})
    listing_table.put_item(Item={"run_id": "run-09", "item_type": "STATE", "status": "passed", "jobs": {}})  # 没有 META

    rows = {r.run_id: r for r in cloud_runs.list_runs([Status.PASSED], limit=None)}
    assert rows["run-07"].state is None and rows["run-07"].header == (3, "9.0.0")
    assert rows["run-08"].state is not None and rows["run-08"].header is None
    assert rows["run-09"].state is not None and rows["run-09"].header is None
    assert rows["run-04"].state is not None


def test_ddb_list_runs_batches_reads_and_projects_away_meta_json(listing_table, monkeypatch):
    store = DynamoDBRunStore(listing_table, list_index_name=_LIST_INDEX)
    for i in range(60):
        _make(store, f"run-{i:03d}", Status.PENDING)
    client = listing_table.meta.client
    real = client.batch_get_item
    requests = []

    def spy(*, RequestItems):
        requests.append(RequestItems[_TABLE])
        return real(RequestItems=RequestItems)

    monkeypatch.setattr(client, "batch_get_item", spy)
    rows = store.list_runs([Status.PENDING], limit=None)
    assert _ids(rows) == [f"run-{i:03d}" for i in reversed(range(60))]
    assert all(r.header == (1, "1.5.0") for r in rows)
    # 120 个键分两批（每批至多 100），每个 run 的 STATE 与 META 在同一批
    assert [len(r["Keys"]) for r in requests] == [100, 20]
    for r in requests:
        assert r["ConsistentRead"] is True
        assert "meta_json" not in r["ExpressionAttributeNames"].values()
        run_ids = [k["run_id"] for k in r["Keys"]]
        assert all(run_ids.count(rid) == 2 for rid in run_ids)


def test_ddb_list_runs_retries_unprocessed_keys_with_backoff(cloud_runs, listing_table, monkeypatch):
    client = listing_table.meta.client
    real = client.batch_get_item
    calls = []

    def flaky(*, RequestItems):
        """第一次只处理一半的键、其余作为未处理键返回；之后照常。"""
        calls.append(RequestItems[_TABLE])
        if len(calls) > 1:
            return real(RequestItems=RequestItems)
        keys = RequestItems[_TABLE]["Keys"]
        done = real(RequestItems={_TABLE: {**RequestItems[_TABLE], "Keys": keys[: len(keys) // 2]}})
        done["UnprocessedKeys"] = {_TABLE: {"Keys": keys[len(keys) // 2:]}}  # 不回带读取选项：重试须自己带上
        return done

    sleeps = []
    monkeypatch.setattr(client, "batch_get_item", flaky)
    monkeypatch.setattr(ddb_module, "time", SimpleNamespace(sleep=sleeps.append))
    rows = cloud_runs.list_runs([Status.PASSED, Status.FAILED], limit=None)
    assert _ids(rows) == ["run-04", "run-03", "run-02", "run-01"]
    assert all(r.state is not None and r.header is not None for r in rows)
    assert len(calls) == 2 and sleeps == [ddb_module._BATCH_GET_BACKOFF_S]
    assert calls[1]["ConsistentRead"] is True and "ProjectionExpression" in calls[1]


def test_ddb_list_runs_index_missing_or_not_configured_raises(aws, cloud_runs):
    from botocore.exceptions import ClientError

    with pytest.raises(RuntimeError, match="索引名"):
        DynamoDBRunStore(aws["ddb"].Table(_TABLE)).list_runs([Status.PASSED], limit=None)
    # 表上没有这个索引（如 conftest 的基础表）：Query 的 AWS 错误原样抛出，由调用方按读不到这个后端处理
    with pytest.raises(ClientError):
        DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]), list_index_name=_LIST_INDEX).list_runs(
            [Status.PASSED], limit=None)
    with pytest.raises(ValueError):
        cloud_runs.list_runs([Status.PASSED], limit=0)


# ============================================================================
# 云端：假表（moto 造不出的情形）
# ============================================================================


class _FakeTable:
    """只实现列举用到的三样：`name`、`query`、`meta.client.batch_get_item`。

    partitions：{状态值: [run_id…]}（按 run_id 降序返回）；items：{(run_id, item_type): item}；page_size：每页最多几条
    （模拟一页不足 Limit 却还有下一页）；unprocessed：前几次 batch_get_item 把全部键当作未处理返回。
    """

    def __init__(self, partitions: dict[str, list[str]], items: dict, *, page_size: int | None = None,
                 unprocessed: int = 0) -> None:
        self.name = _TABLE
        self._partitions = partitions
        self._items = items
        self._page_size = page_size
        self._unprocessed = unprocessed
        self.queries: list[dict] = []
        self.batches: list[dict] = []
        self.meta = SimpleNamespace(client=SimpleNamespace(batch_get_item=self._batch_get_item))

    def query(self, **kwargs):
        self.queries.append(dict(kwargs))
        assert kwargs["IndexName"] == _LIST_INDEX and kwargs["ScanIndexForward"] is False
        run_ids = sorted(self._partitions.get(kwargs["ExpressionAttributeValues"][":s"], []), reverse=True)
        start = kwargs.get("ExclusiveStartKey", {}).get("offset", 0)
        n = min(x for x in (kwargs.get("Limit"), self._page_size, len(run_ids) - start) if x is not None)
        page = run_ids[start:start + n]
        resp = {"Items": [{"run_id": rid, "item_type": "STATE", "status": "x"} for rid in page]}
        if start + n < len(run_ids):
            resp["LastEvaluatedKey"] = {"offset": start + n}
        return resp

    def _batch_get_item(self, *, RequestItems):
        req = RequestItems[_TABLE]
        keys = req["Keys"]
        assert len(keys) == len({(k["run_id"], k["item_type"]) for k in keys}), "同一请求里有重复的键"
        self.batches.append(req)
        if self._unprocessed > 0:
            self._unprocessed -= 1
            return {"Responses": {_TABLE: []}, "UnprocessedKeys": {_TABLE: {"Keys": keys}}}
        found = [self._items[(k["run_id"], k["item_type"])] for k in keys if (k["run_id"], k["item_type"]) in self._items]
        return {"Responses": {_TABLE: found}, "UnprocessedKeys": {}}


def _state_item(run_id: str, status: str, **extra) -> dict:
    return {"run_id": run_id, "item_type": "STATE", "status": status, "jobs": {}, **extra}


def test_ddb_list_runs_continues_short_pages_until_limit(monkeypatch):
    table = _FakeTable({"passed": [f"r{i}" for i in range(5)]},
                       {(f"r{i}", "STATE"): _state_item(f"r{i}", "passed") for i in range(5)}, page_size=1)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=3)
    assert _ids(rows) == ["r4", "r3", "r2"]
    # 每页只回一条且还有下一页：续读，Limit 随已取条数递减，取够即停（不再读第四页）
    assert [q.get("Limit") for q in table.queries] == [3, 2, 1]
    assert "ExclusiveStartKey" not in table.queries[0] and table.queries[1]["ExclusiveStartKey"] == {"offset": 1}

    table = _FakeTable({"pending": ["r0", "r1", "r2"]},
                       {(f"r{i}", "STATE"): _state_item(f"r{i}", "pending") for i in range(3)}, page_size=2)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING], limit=None)
    assert _ids(rows) == ["r2", "r1", "r0"]
    assert [("Limit" in q) for q in table.queries] == [False, False]  # 不截断：分页读完


def test_ddb_list_runs_dedupes_does_not_refilter_and_skips_vanished_state():
    # 索引传播期间：r2 同时在 pending 与 running 两个分区；r3 在 pending 分区，读回已是 passed；r1 的 STATE 已不在
    table = _FakeTable(
        {"pending": ["r1", "r2", "r3"], "running": ["r2"]},
        {("r2", "STATE"): _state_item("r2", "running", detached=True),
         ("r3", "STATE"): _state_item("r3", "passed"),
         ("r1", "META"): {"run_id": "r1", "item_type": "META", "schema_version": 1, "cli_version": "1.5.0"}})
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING, Status.RUNNING], limit=None)
    assert _ids(rows) == ["r3", "r2"]
    by_id = {r.run_id: r for r in rows}
    assert by_id["r3"].state.status == Status.PASSED  # 不按所请求的状态复筛
    assert by_id["r2"].state.status == Status.RUNNING and by_id["r2"].detached is True
    assert [q["ExpressionAttributeValues"][":s"] for q in table.queries] == ["pending", "running"]  # 按给定顺序查
    [batch] = table.batches
    assert sorted(k["run_id"] for k in batch["Keys"]) == ["r1", "r1", "r2", "r2", "r3", "r3"]  # 先去重再读回
    # 给定顺序与状态值的字典序相反时同样照给定顺序查（不排序、不经集合）
    table = _FakeTable({"pending": ["r1"], "running": ["r2"]}, {})
    DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.RUNNING, Status.PENDING], limit=None)
    assert [q["ExpressionAttributeValues"][":s"] for q in table.queries] == ["running", "pending"]


def test_ddb_list_runs_unknown_run_status_read_back_is_unreadable():
    table = _FakeTable({"running": ["r1"]}, {("r1", "STATE"): _state_item("r1", "paused")})
    [row] = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.RUNNING], limit=None)
    assert row.run_id == "r1" and row.state is None and row.header is None


def test_ddb_list_runs_gives_up_after_bounded_retries(monkeypatch):
    sleeps = []
    monkeypatch.setattr(ddb_module, "time", SimpleNamespace(sleep=sleeps.append))
    table = _FakeTable({"passed": ["r1", "r2"]}, {}, unprocessed=10**6)
    with pytest.raises(RunListingIncomplete) as exc:
        DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=None)
    retries = ddb_module._BATCH_GET_MAX_RETRIES
    assert len(table.batches) == retries + 1  # 首次 + 有界重试
    assert sleeps == [ddb_module._BATCH_GET_BACKOFF_S * 2 ** i for i in range(retries)]  # 退避逐次翻倍
    assert exc.value.missing == 2 and exc.value.table == _TABLE
    assert all(b["ConsistentRead"] is True for b in table.batches)

    # 重试次数之内处理完：照常返回
    sleeps.clear()
    table = _FakeTable({"passed": ["r1"]}, {("r1", "STATE"): _state_item("r1", "passed")}, unprocessed=retries)
    assert _ids(DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=None)) == ["r1"]
    assert len(sleeps) == retries
