"""RunStore.list_runs 的单测（ADR 0041 决策七「core 端口」「本机实现」「云端实现」）。

本机侧用真目录造 run；云端侧两套：moto 建带状态分组索引的 runs 表（分区键 status_group、排序键 run_id、投影 INCLUDE
worker_task_def_arns，与部署侧同一形态），测与本机同一批行为与读回形状，无法读取的行不占名额、非终态按读回的状态归入另有两端
参数化对拍；moto 造不出的情形（Query 一页不足 Limit 却还有下一页、按页补读的逐页续读、索引尚未跟上导致的重复键与 STATE 已不在、
读回的状态已不在所请求的状态、未处理键）用只实现列举所需三样的假表测。
"""
from __future__ import annotations

import dataclasses
import errno
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

_LIST_INDEX = "status_group-run_id-index"
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


@pytest.mark.parametrize("bad", [
    {"started_at": 1731225600},                  # 起始时刻是数字
    {"ended_at": ["2026-07-01T00:05:00Z"]},      # 结束时刻是数组
    {"message": {"text": "m"}},                  # run 级 message 是对象
    {"jobs": [{"scope_id": "s", "status": 3}]},  # job 状态值不合法
])
def test_local_list_runs_lists_wrongly_typed_state_fields_as_unreadable(tmp_path: Path, bad: dict):
    # 清单要输出的字段类型不对：列为无法读取，人读表格与 --json 都不会带出非字符串的值；提交记录头部照读
    store = LocalRunStore(tmp_path)
    _make(store, "run-01", Status.PASSED)
    state = {"run_id": "run-01", "status": "passed", "started_at": "2026-07-01T00:00:00Z", "jobs": [], **bad}
    (tmp_path / "run-01" / "run_state.json").write_text(json.dumps(state), encoding="utf-8")
    [row] = store.list_runs([Status.PASSED], limit=None)
    assert row.state is None and row.header == (1, "1.5.0")
    # 无法读取的行不参与状态归入：只请求非终态时它同样列出
    assert _ids(store.list_runs([Status.PENDING], limit=None)) == ["run-01"]


@pytest.mark.parametrize("content", [b"{broken", b"[]", json.dumps({"schema_version": "x"}).encode(),
                                     # 写端版本不是字符串：读作版本未知，不把数字转成版本串
                                     json.dumps({"schema_version": 1, "cli_version": 150}).encode(),
                                     json.dumps({"schema_version": 1, "cli_version": 1.5}).encode()])
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


@pytest.mark.parametrize("error", [PermissionError, FileNotFoundError, NotADirectoryError, "ELOOP"])
def test_local_list_runs_raises_when_an_entry_cannot_be_inspected(tmp_path: Path, monkeypatch, error):
    """判断条目是不是目录时的权限错误原样抛出（不当作「不是目录」跳过）；列出之后被删掉的条目（stat 报不存在）跳过；
    穿过文件的符号链接（ENOTDIR）与链接环（ELOOP）同样原样抛出——契约只跳过枚举后消失的条目，其余访问失败由 CLI 以退出码 2 结束。"""
    store = LocalRunStore(tmp_path)
    _make(store, "run-01", Status.PASSED)
    _make(store, "run-02", Status.PASSED)
    blocked = os.fspath(tmp_path / "run-02")
    real_stat = os.stat

    def stat(path, *args, **kwargs):
        if os.fspath(path) == blocked:
            if error == "ELOOP":
                raise OSError(errno.ELOOP, "injected", blocked)
            raise error({PermissionError: 13, FileNotFoundError: 2, NotADirectoryError: 20}[error], "injected", blocked)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", stat)
    # Python 3.14 起 Path.is_dir 把任何 OSError 都读作「不是目录」：换成这一语义，让本用例在各版本上都能区分显式 stat 与 is_dir
    monkeypatch.setattr(Path, "is_dir", lambda self, **kwargs: os.path.isdir(self))
    if error is FileNotFoundError:
        assert _ids(store.list_runs([Status.PASSED], limit=None)) == ["run-01"]
    else:
        with pytest.raises(OSError):
            store.list_runs([Status.PASSED], limit=None)


def test_local_list_runs_keeps_rows_with_null_message_and_empty_jobs(tmp_path: Path):
    """历史运行态的合法形态不被类型校验误判：message 与 ended_at 显式为 null、jobs 为空映射或空列表，都能读出、不是不可读行。"""
    store = LocalRunStore(tmp_path)
    for rid, jobs in (("run-01", {}), ("run-02", [])):
        _make(store, rid, Status.PASSED)
        path = tmp_path / rid / "run_state.json"
        d = json.loads(path.read_text(encoding="utf-8"))
        d.update(message=None, ended_at=None, jobs=jobs)
        path.write_text(json.dumps(d), encoding="utf-8")
    rows = store.list_runs([Status.PASSED], limit=None)
    assert _ids(rows) == ["run-02", "run-01"]
    assert all(r.state is not None and r.state.status == Status.PASSED and r.state.message is None and r.state.ended_at is None for r in rows)


# ============================================================================
# 云端：moto
# ============================================================================


@pytest.fixture
def listing_table(aws):
    """moto 下带状态分组索引的 runs 表（索引名取构造参数同一个常量）。"""
    return aws["ddb"].create_table(
        TableName=_TABLE,
        KeySchema=[
            {"AttributeName": "run_id", "KeyType": "HASH"},
            {"AttributeName": "item_type", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "run_id", "AttributeType": "S"},
            {"AttributeName": "item_type", "AttributeType": "S"},
            {"AttributeName": "status_group", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[{
            "IndexName": _LIST_INDEX,
            "KeySchema": [
                {"AttributeName": "status_group", "KeyType": "HASH"},
                {"AttributeName": "run_id", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "INCLUDE", "NonKeyAttributes": ["worker_task_def_arns"]},
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
    # 运行态的每个字段都有值：读回的投影少取任何一个属性（结束时刻、run 级消息、高水位、job 的会话与认领时刻），都与 load_run_state 不等
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
    listing_table.put_item(Item=_state_item("run-07", "passed", jobs={"s": {"status": "paused"}}))
    listing_table.put_item(Item={"run_id": "run-07", "item_type": "META", "schema_version": 3, "cli_version": "9.0.0",
                                 "meta_json": "{}"})
    listing_table.put_item(Item=_state_item("run-08", "passed"))
    listing_table.put_item(Item={"run_id": "run-08", "item_type": "META", "schema_version": "x", "meta_json": "{}"})
    listing_table.put_item(Item=_state_item("run-09", "passed"))  # 没有 META

    rows = {r.run_id: r for r in cloud_runs.list_runs([Status.PASSED], limit=None)}
    assert rows["run-07"].state is None and rows["run-07"].header == (3, "9.0.0")
    assert rows["run-08"].state is not None and rows["run-08"].header is None
    assert rows["run-09"].state is not None and rows["run-09"].header is None
    assert rows["run-04"].state is not None


def test_ddb_list_runs_lists_wrongly_typed_fields_as_unreadable_and_unknown_version(cloud_runs, listing_table):
    # 数值属性读回是 Decimal、Map 读回是 dict：都不是字符串，清单不带出它们（Decimal 连 json.dumps 都过不去）
    from decimal import Decimal

    meta = {"item_type": "META", "schema_version": 1, "cli_version": "1.5.0", "meta_json": "{}"}
    for run_id, extra in (("run-07", {"started_at": 1731225600}), ("run-08", {"message": {"text": "m"}}),
                          ("run-09", {"jobs": {"s": {"status": 3}}})):
        listing_table.put_item(Item={**_state_item(run_id, "passed"), **extra})
        listing_table.put_item(Item={"run_id": run_id, **meta})
    listing_table.put_item(Item=_state_item("run-10", "passed"))
    listing_table.put_item(Item={"run_id": "run-10", **meta, "cli_version": Decimal("1.5")})

    rows = {r.run_id: r for r in cloud_runs.list_runs([Status.PASSED], limit=None)}
    for run_id in ("run-07", "run-08", "run-09"):
        assert rows[run_id].state is None and rows[run_id].header == (1, "1.5.0")
    assert rows["run-10"].state is not None and rows["run-10"].header is None  # 写出版本未知，不把数字转成版本串


@pytest.mark.parametrize("backend", ["local", "ddb"])
def test_explicit_null_schema_version_is_contract_violation_but_missing_key_reads_zero(request, tmp_path: Path, backend):
    """头部的结构版本：缺键读作 0（早于结构版本号的写端），显式 null 是定义违约——两端同一口径。清单里违约的头部读作 None，
    缺键的照读 (0, 写端版本)；`peek_definition_header` 对违约抛 DefinitionContractError。"""
    from gherkai_core.errors import DefinitionContractError

    if backend == "local":
        store = LocalRunStore(tmp_path)
        for run_id in ("run-01", "run-02"):
            _make(store, run_id, Status.PASSED)
        (tmp_path / "run-01" / "run_meta.json").write_text(
            json.dumps({"schema_version": None, "cli_version": "1.5.0"}), encoding="utf-8")
        (tmp_path / "run-02" / "run_meta.json").write_text(json.dumps({"cli_version": "1.5.0"}), encoding="utf-8")
    else:
        table = request.getfixturevalue("listing_table")
        store = DynamoDBRunStore(table, list_index_name=_LIST_INDEX)
        for run_id in ("run-01", "run-02"):
            _make(store, run_id, Status.PASSED)
        table.put_item(Item={"run_id": "run-01", "item_type": "META", "schema_version": None, "cli_version": "1.5.0",
                             "meta_json": "{}"})
        table.put_item(Item={"run_id": "run-02", "item_type": "META", "cli_version": "1.5.0", "meta_json": "{}"})
    rows = {r.run_id: r for r in store.list_runs([Status.PASSED], limit=None)}
    assert rows["run-01"].state is not None and rows["run-01"].header is None
    assert rows["run-02"].header == (0, "1.5.0")
    with pytest.raises(DefinitionContractError, match="schema_version 须为整数"):
        store.peek_definition_header("run-01")
    assert store.peek_definition_header("run-02") == (0, "1.5.0")


def _two_ended_store(request, tmp_path: Path, monkeypatch, backend: str):
    """两端同一组造数手段：返回 (store, 造一个可读的 passed run, 造一个无法读取的 passed run, 云端的调用记录或 None)。
    无法读取的 run 指 run 级状态认识（仍在 passed 分组里）而 job 状态值本版本不认识；提交记录头部照常写下。云端的调用记录收集每次
    Query 的 Limit 与每次 BatchGetItem 读回的 run_id。"""
    bad_jobs = [{"scope_id": "s", "status": "paused"}]
    if backend == "local":
        store = LocalRunStore(tmp_path)

        def unreadable(run_id: str) -> None:
            _make(store, run_id, Status.PASSED)
            (tmp_path / run_id / "run_state.json").write_text(
                json.dumps({"run_id": run_id, "status": "passed", "jobs": bad_jobs}), encoding="utf-8")

        return store, lambda run_id: _make(store, run_id, Status.PASSED), unreadable, None
    table = request.getfixturevalue("listing_table")
    store = DynamoDBRunStore(table, list_index_name=_LIST_INDEX)

    def unreadable(run_id: str) -> None:
        _make(store, run_id, Status.PASSED)
        table.put_item(Item=_state_item(run_id, "passed", jobs={"s": {"status": "paused"}}))

    calls = SimpleNamespace(limits=[], batches=[])
    real_query, client = table.query, table.meta.client
    real_batch = client.batch_get_item

    def query(**kwargs):
        calls.limits.append(kwargs.get("Limit"))
        return real_query(**kwargs)

    def batch_get_item(*, RequestItems):
        calls.batches.append(sorted({k["run_id"] for k in RequestItems[_TABLE]["Keys"]}, reverse=True))
        return real_batch(RequestItems=RequestItems)

    monkeypatch.setattr(table, "query", query)
    monkeypatch.setattr(client, "batch_get_item", batch_get_item)
    return store, lambda run_id: _make(store, run_id, Status.PASSED), unreadable, calls


@pytest.mark.parametrize("backend", ["local", "ddb"])
@pytest.mark.parametrize("layout, limit, expected, limits, batches", [
    # 最新一条无法读取、次新可读：坏行照常列出、不占名额，可读的仍取到一条，更旧的一条不读
    ("URR", 1, ["r3", "r2"], [1, 1], [["r3"], ["r2"]]),
    # 连续多条无法读取之后才有可读行：按还差的条数续取，凑满两条可读的即停，最旧的一条不读
    ("UUURRR", 2, ["r6", "r5", "r4", "r3", "r2"], [2, 2, 1], [["r6", "r5"], ["r4", "r3"], ["r2"]]),
    # 可读行不足 limit、分组读完：列出全部，只查一次
    ("UR", 5, ["r2", "r1"], [5], [["r2", "r1"]]),
])
def test_list_runs_unreadable_rows_do_not_take_the_limit_on_both_backends(
        request, tmp_path: Path, monkeypatch, backend, layout, limit, expected, limits, batches):
    """名额只给可读的 run，两端同一规则（ADR 0041 决策七「本机与云端的不对称」「云端实现」）。layout 自左到右是 run_id 从新到旧，
    U 是无法读取的行、R 是可读的行。云端取的键数至多为 limit 加上凑满之前遇到的无法读取的行数，每页按还差的条数取键。"""
    store, readable, unreadable, calls = _two_ended_store(request, tmp_path, monkeypatch, backend)
    kinds = {f"r{i}": kind for i, kind in enumerate(reversed(layout), start=1)}
    for run_id, kind in kinds.items():
        (unreadable if kind == "U" else readable)(run_id)
    rows = store.list_runs([Status.PASSED], limit=limit)
    assert _ids(rows) == expected
    assert all((r.state is None) == (kinds[r.run_id] == "U") and r.header == (1, "1.5.0") for r in rows)
    if calls is not None:
        assert calls.limits == limits
        assert calls.batches == batches


def _non_terminal_store(request, tmp_path: Path, monkeypatch, backend: str):
    """两端同一组 run：pending 三条、running 两条、passed 一条，run_id 交错。返回 (store, 云端每次 Query 的参数或 None)。"""
    layout = {"r1": Status.PENDING, "r2": Status.RUNNING, "r3": Status.PASSED, "r4": Status.PENDING,
              "r5": Status.RUNNING, "r6": Status.PENDING}
    if backend == "local":
        store, queries = LocalRunStore(tmp_path), None
    else:
        table = request.getfixturevalue("listing_table")
        store, queries = DynamoDBRunStore(table, list_index_name=_LIST_INDEX), []
        real_query = table.query
        monkeypatch.setattr(table, "query", lambda **kw: queries.append(kw) or real_query(**kw))
    for run_id, status in layout.items():
        _make(store, run_id, status)
    return store, queries


@pytest.mark.parametrize("backend", ["local", "ddb"])
@pytest.mark.parametrize("statuses, limit, expected", [
    ([Status.PENDING], None, [("r6", "pending"), ("r4", "pending"), ("r1", "pending")]),
    ([Status.RUNNING], None, [("r5", "running"), ("r2", "running")]),
    ([Status.PENDING, Status.RUNNING], None,
     [("r6", "pending"), ("r5", "running"), ("r4", "pending"), ("r2", "running"), ("r1", "pending")]),
    ([Status.RUNNING, Status.PENDING], 1, [("r6", "pending"), ("r5", "running")]),
    ([Status.PENDING, Status.RUNNING], 2, [("r6", "pending"), ("r5", "running"), ("r4", "pending"), ("r2", "running")]),
    ([Status.RUNNING], 1, [("r5", "running")]),
])
def test_list_runs_non_terminal_statuses_are_told_apart_by_read_back_status_on_both_backends(
        request, tmp_path: Path, monkeypatch, backend, statuses, limit, expected):
    """非终态按读回的状态归入所请求的状态，两端结果相同（ADR 0041 决策七「core 端口」的例外、「云端实现」）。云端不论请求的是
    pending、running 还是两者，查的都是同一个 live 分组，每次 Query 都只按分组属性取键、走状态分组索引。"""
    store, queries = _non_terminal_store(request, tmp_path, monkeypatch, backend)
    rows = store.list_runs(statuses, limit=limit)
    assert [(r.run_id, r.state.status.value) for r in rows] == expected
    if queries is not None:
        assert queries and all(q["IndexName"] == _LIST_INDEX and q["KeyConditionExpression"] == "#sg = :g"
                               and q["ExpressionAttributeNames"] == {"#sg": "status_group"}
                               and q["ExpressionAttributeValues"] == {":g": "live"} for q in queries)
        if limit is None:
            assert len(queries) == 1  # 一个分组、一页读完：两个非终态合成一次查询


def test_ddb_list_runs_finds_a_non_terminal_status_unknown_to_this_version_in_live(cloud_runs, listing_table):
    # 更新的版本写出的、本版本不认识的非终态值，沿用同一分组规则写进 live：云端也找得到，列为无法读取；不认识的终态值在自己的
    # 分组里，不在任何被查分组之内
    listing_table.put_item(Item=_state_item("run-07", "paused", status_group="live"))
    listing_table.put_item(Item=_state_item("run-08", "archived", status_group="archived"))
    rows = cloud_runs.list_runs([Status.PENDING], limit=None)
    assert [(r.run_id, r.state is None) for r in rows] == [("run-07", True), ("run-06", False)]
    assert "run-08" not in _ids(cloud_runs.list_runs(list(Status), limit=None))


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
    # 表上没有这个索引：Query 的 AWS 错误原样抛出，由调用方按读不到这个后端处理
    with pytest.raises(ClientError):
        DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]), list_index_name="no-such-index").list_runs(
            [Status.PASSED], limit=None)
    with pytest.raises(ValueError):
        cloud_runs.list_runs([Status.PASSED], limit=0)


# ============================================================================
# 云端：假表（moto 造不出的情形）
# ============================================================================


class _FakeTable:
    """只实现列举用到的三样：`name`、`query`、`meta.client.batch_get_item`。

    partitions：{状态分组: [run_id…]}（按 run_id 降序返回）；items：{(run_id, item_type): item}；page_size：每页最多几条
    （模拟一页不足 Limit 却还有下一页）；unprocessed：前几次 batch_get_item 把全部键当作未处理返回；empty_last_cursor：末页的
    LastEvaluatedKey 给空字典而不是省略（同样表示没有下一页）。拿空游标再查时按分组开头处理，所以分页不在空游标上结束时会一直
    重读；`query` 超过 _MAX_QUERIES 次即判定分页没有结束，让这类缺陷以失败而不是挂起暴露。
    """

    _MAX_QUERIES = 50

    def __init__(self, partitions: dict[str, list[str]], items: dict, *, page_size: int | None = None,
                 unprocessed: int = 0, empty_last_cursor: bool = False) -> None:
        self.name = _TABLE
        self._partitions = partitions
        self._items = items
        self._page_size = page_size
        self._unprocessed = unprocessed
        self._empty_last_cursor = empty_last_cursor
        self.queries: list[dict] = []
        self.batches: list[dict] = []
        self.meta = SimpleNamespace(client=SimpleNamespace(batch_get_item=self._batch_get_item))

    def query(self, **kwargs):
        self.queries.append(dict(kwargs))
        assert len(self.queries) <= self._MAX_QUERIES, "分页没有结束"
        # 查的是状态分组索引，键条件只按分组属性（不按 status）
        assert kwargs["IndexName"] == _LIST_INDEX and kwargs["ScanIndexForward"] is False
        assert kwargs["KeyConditionExpression"] == "#sg = :g" and kwargs["ExpressionAttributeNames"] == {"#sg": "status_group"}
        run_ids = sorted(self._partitions.get(kwargs["ExpressionAttributeValues"][":g"], []), reverse=True)
        start = kwargs.get("ExclusiveStartKey", {}).get("offset", 0)
        n = min(x for x in (kwargs.get("Limit"), self._page_size, len(run_ids) - start) if x is not None)
        page = run_ids[start:start + n]
        resp = {"Items": [{"run_id": rid, "item_type": "STATE", "status": "x"} for rid in page]}
        if start + n < len(run_ids):
            resp["LastEvaluatedKey"] = {"offset": start + n}
        elif self._empty_last_cursor:
            resp["LastEvaluatedKey"] = {}
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
    """直接写入的 STATE item：状态值本版本认识时由写端同一个派生函数带上分组属性（moto 的索引只收带它的 item），不认识时由调用方
    在 extra 里给出。"""
    group = {"status_group": ddb_module.status_group(Status(status))} if status in {s.value for s in Status} else {}
    return {"run_id": run_id, "item_type": "STATE", "status": status, "jobs": {}, **group, **extra}


def test_ddb_list_runs_continues_short_pages_until_limit(monkeypatch):
    table = _FakeTable({"passed": [f"r{i}" for i in range(5)]},
                       {(f"r{i}", "STATE"): _state_item(f"r{i}", "passed") for i in range(5)}, page_size=1)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=3)
    assert _ids(rows) == ["r4", "r3", "r2"]
    # 每页只回一条且还有下一页：续读，Limit 随已取条数递减，取够即停（不再读第四页）
    assert [q.get("Limit") for q in table.queries] == [3, 2, 1]
    assert "ExclusiveStartKey" not in table.queries[0] and table.queries[1]["ExclusiveStartKey"] == {"offset": 1}

    table = _FakeTable({"live": ["r0", "r1", "r2"]},
                       {(f"r{i}", "STATE"): _state_item(f"r{i}", "pending") for i in range(3)}, page_size=2)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING], limit=None)
    assert _ids(rows) == ["r2", "r1", "r0"]
    assert [("Limit" in q) for q in table.queries] == [False, False]  # 不截断：分页读完


def _unreadable_item(run_id: str) -> dict:
    return _state_item(run_id, "passed", jobs={"s": {"status": "paused"}})


def test_ddb_list_runs_refills_across_pages_after_unreadable_rows():
    # 每页只回一条：r5、r4 无法读取，r3、r2、r1 可读，limit=2。逐页读回、解析，名额未满就带着续读起点取下一页
    items = {(r, "STATE"): _unreadable_item(r) for r in ("r5", "r4")}
    items.update({(r, "STATE"): _state_item(r, "passed") for r in ("r3", "r2", "r1")})
    table = _FakeTable({"passed": ["r1", "r2", "r3", "r4", "r5"]}, items, page_size=1)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=2)
    assert _ids(rows) == ["r5", "r4", "r3", "r2"]
    assert [q["Limit"] for q in table.queries] == [2, 2, 2, 1]  # 每次按还差的可读条数取键
    assert [q.get("ExclusiveStartKey") for q in table.queries] == [None, {"offset": 1}, {"offset": 2}, {"offset": 3}]
    # 读回的 run 数等于 limit 加上途中遇到的无法读取的行数，r1 不读
    assert [sorted({k["run_id"] for k in b["Keys"]}) for b in table.batches] == [["r5"], ["r4"], ["r3"], ["r2"]]


@pytest.mark.parametrize("empty_last_cursor", [False, True])
def test_ddb_list_runs_stops_when_partition_ends_with_only_unreadable_rows(empty_last_cursor):
    # 一页全是无法读取的行、没有下一页（游标省略或为空字典）：名额未满也到此为止，只查一次
    table = _FakeTable({"passed": ["r1", "r2"]}, {(r, "STATE"): _unreadable_item(r) for r in ("r1", "r2")},
                       empty_last_cursor=empty_last_cursor)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=3)
    assert _ids(rows) == ["r2", "r1"] and all(r.state is None for r in rows)
    assert len(table.queries) == 1 and len(table.batches) == 1


def test_ddb_list_runs_refill_counts_runs_already_read_in_an_earlier_status():
    # 索引传播期间 r2 同时在 live 与 passed 分组，读回是可读的 passed：在 live 分组里列出、不计入 running 的名额；passed 分组里
    # 它不再读回，但照样占名额，r1 不查不读
    table = _FakeTable({"live": ["r2"], "passed": ["r1", "r2"]},
                       {(r, "STATE"): _state_item(r, "passed") for r in ("r1", "r2")})
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.RUNNING, Status.PASSED], limit=1)
    assert _ids(rows) == ["r2"]
    assert [(q["ExpressionAttributeValues"][":g"], q["Limit"]) for q in table.queries] == [("live", 1), ("passed", 1)]
    [batch] = table.batches
    assert sorted(k["run_id"] for k in batch["Keys"]) == ["r2", "r2"]


def test_ddb_list_runs_refill_skips_rows_whose_state_vanished_before_read_back():
    # 每页只回一条：r4 在索引里、读回时 STATE 已不在（item 已删，索引尚未跟上），它不列出、也不占名额，按原条数续取下一页
    table = _FakeTable({"passed": ["r1", "r2", "r3", "r4"]},
                       {(r, "STATE"): _state_item(r, "passed") for r in ("r1", "r2", "r3")}, page_size=1)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=2)
    assert _ids(rows) == ["r3", "r2"]
    assert [q["Limit"] for q in table.queries] == [2, 2, 1]
    assert [sorted({k["run_id"] for k in b["Keys"]}) for b in table.batches] == [["r4"], ["r3"], ["r2"]]


def test_ddb_list_runs_refill_reads_a_partition_of_only_unreadable_rows_to_the_end():
    # 分组里全是无法读取的行、分成三页：名额一直未满，逐页续读到末页为止，三条都列出
    table = _FakeTable({"passed": ["r1", "r2", "r3"]}, {(r, "STATE"): _unreadable_item(r) for r in ("r1", "r2", "r3")},
                       page_size=1)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=2)
    assert _ids(rows) == ["r3", "r2", "r1"] and all(r.state is None for r in rows)
    assert [q["Limit"] for q in table.queries] == [2, 2, 2]


def test_ddb_list_runs_refill_retries_per_page_and_counts_only_the_failing_page(monkeypatch):
    """按页补读时每页各自读回：某一页的未处理键在重试次数之内处理完，结果与不重试时相同；某一页重试耗尽时立即停下，报的未读回数
    只含这一页的 run，此前各页已完整读回的不计，后续各页不再查。"""
    monkeypatch.setattr(ddb_module, "time", SimpleNamespace(sleep=lambda s: None))
    retries = ddb_module._BATCH_GET_MAX_RETRIES
    items = {(r, "STATE"): _state_item(r, "passed") for r in ("r1", "r2", "r3")}
    items[("r4", "STATE")] = _unreadable_item("r4")

    def table_failing_on(run_id: str, failures: int) -> _FakeTable:
        # 每页一条，按读回请求里的 run 认出是哪一页：含 run_id 的请求前 failures 次把全部键当作未处理返回
        table = _FakeTable({"passed": ["r1", "r2", "r3", "r4"]}, items, page_size=1)
        real = table.meta.client.batch_get_item
        left = [failures]

        def batch_get_item(*, RequestItems):
            keys = RequestItems[_TABLE]["Keys"]
            if left[0] > 0 and any(k["run_id"] == run_id for k in keys):
                left[0] -= 1
                table.batches.append(RequestItems[_TABLE])
                return {"Responses": {_TABLE: []}, "UnprocessedKeys": {_TABLE: {"Keys": keys}}}
            return real(RequestItems=RequestItems)

        table.meta.client.batch_get_item = batch_get_item
        return table

    # 第二页（r3）的未处理键在重试次数之内处理完
    table = table_failing_on("r3", retries)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=2)
    assert _ids(rows) == ["r4", "r3", "r2"] and rows[0].state is None
    assert len(table.queries) == 3

    table = table_failing_on("r3", 10**6)
    with pytest.raises(RunListingIncomplete) as exc:
        DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=2)
    assert exc.value.missing == 1
    assert len(table.queries) == 2  # 第二页重试耗尽：第三页不再查


@pytest.mark.parametrize("limit", [None, 5])
def test_ddb_list_runs_empty_partition_with_empty_cursor_returns_nothing(limit):
    # 分组没有结果、末页游标还是空字典：返回空清单、只查一次、不发 BatchGetItem
    table = _FakeTable({"live": []}, {}, empty_last_cursor=True)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING], limit=limit)
    assert rows == [] and len(table.queries) == 1 and table.batches == []


@pytest.mark.parametrize("limit", [None, 5])
@pytest.mark.parametrize("page_size, queries", [(2, 2), (None, 1)])
def test_ddb_list_runs_empty_cursor_ends_pagination(page_size, queries, limit):
    # 末页的游标是空字典：分页到此结束。分两页时只续读一次；一页就有全部结果时不再请求。截不截断都一样
    table = _FakeTable({"live": ["r0", "r1", "r2"]},
                       {(f"r{i}", "STATE"): _state_item(f"r{i}", "pending") for i in range(3)},
                       page_size=page_size, empty_last_cursor=True)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING], limit=limit)
    assert _ids(rows) == ["r2", "r1", "r0"]
    assert len(table.queries) == queries
    assert all(q.get("ExclusiveStartKey") != {} for q in table.queries)


def test_ddb_list_runs_dedupes_does_not_refilter_and_skips_vanished_state():
    # 索引传播期间：r2 刚收尾，同时在 live 与 passed 两个分组；r3 在 live 分组，读回已是 passed；r1 的 STATE 已不在
    table = _FakeTable(
        {"live": ["r1", "r2", "r3"], "passed": ["r2"]},
        {("r2", "STATE"): _state_item("r2", "passed", detached=True),
         ("r3", "STATE"): _state_item("r3", "passed"),
         ("r1", "META"): {"run_id": "r1", "item_type": "META", "schema_version": 1, "cli_version": "1.5.0"}})
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING, Status.PASSED], limit=None)
    assert _ids(rows) == ["r3", "r2"]
    by_id = {r.run_id: r for r in rows}
    assert by_id["r3"].state.status == Status.PASSED  # live 分组里读回已到终态：照常列出、不复筛
    assert by_id["r2"].state.status == Status.PASSED and by_id["r2"].detached is True
    assert [q["ExpressionAttributeValues"][":g"] for q in table.queries] == ["live", "passed"]
    [batch] = table.batches
    assert sorted(k["run_id"] for k in batch["Keys"]) == ["r1", "r1", "r2", "r2", "r3", "r3"]  # 先去重再读回


def test_ddb_list_runs_queries_live_once_first_then_ended_groups_in_the_given_order():
    # 两个非终态合成对 live 分组的一次查询，不论给出几个、排在哪里；终态分组按给出的顺序，不排序、不经集合
    table = _FakeTable({"live": ["r1"], "failed": ["r2"], "passed": ["r3"]}, {})
    DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs(
        [Status.FAILED, Status.RUNNING, Status.PASSED, Status.PENDING], limit=None)
    assert [q["ExpressionAttributeValues"][":g"] for q in table.queries] == ["live", "failed", "passed"]
    table = _FakeTable({"failed": ["r2"]}, {})
    DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.FAILED], limit=3)
    assert [q["ExpressionAttributeValues"][":g"] for q in table.queries] == ["failed"]  # 没请求非终态：不查 live


@pytest.mark.parametrize("limit, limits", [(None, [None]), (1, [1, 1, 1])])
def test_ddb_list_runs_live_rows_read_back_as_ended_are_listed_without_taking_a_quota(limit, limits):
    """live 分组里读回已到终态的行（索引尚未跟上收尾）照常列出、不计入任何非终态的名额；读回为未被请求的非终态的行不列出。
    每页只回一条：r3 读回 running（未被请求），r2 读回 passed，r1 读回 pending，只请求 pending、limit=1 时要读到 r1 才凑满。"""
    table = _FakeTable({"live": ["r1", "r2", "r3"]},
                       {("r3", "STATE"): _state_item("r3", "running"), ("r2", "STATE"): _state_item("r2", "passed"),
                        ("r1", "STATE"): _state_item("r1", "pending")}, page_size=1 if limit else None)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING], limit=limit)
    assert [(r.run_id, r.state.status) for r in rows] == [("r2", Status.PASSED), ("r1", Status.PENDING)]
    assert [q.get("Limit") for q in table.queries] == limits


def test_ddb_list_runs_live_quota_is_per_requested_status_and_rows_past_it_are_not_listed():
    """两个非终态都请求、limit=1：每页的键数是各状态还差的条数之和；pending 凑满之后的 pending 行不列出（与本机每个状态只取前
    limit 条一致），running 凑满即停，更旧的一条不查不读。"""
    states = {"r5": "pending", "r4": "pending", "r3": "running", "r2": "pending", "r1": "running"}
    table = _FakeTable({"live": list(states)}, {(r, "STATE"): _state_item(r, st) for r, st in states.items()})
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING, Status.RUNNING], limit=1)
    assert [(r.run_id, r.state.status) for r in rows] == [("r5", Status.PENDING), ("r3", Status.RUNNING)]
    assert [q["Limit"] for q in table.queries] == [2, 1]
    assert [sorted({k["run_id"] for k in b["Keys"]}, reverse=True) for b in table.batches] == [["r5", "r4"], ["r3"]]


def test_ddb_list_runs_live_unreadable_and_vanished_rows_do_not_take_a_quota():
    """live 分组按页补读时，无法读取的行照常列出、读回时 STATE 已不在的行跳过，两者都不占所请求非终态的名额：每页只回一条，
    只请求 pending、limit=1 时要读到 r2 才凑满，r1 不查不读。"""
    table = _FakeTable({"live": ["r1", "r2", "r3", "r4"]},
                       {("r4", "STATE"): _state_item("r4", "pending", jobs={"s": {"status": "paused"}}),
                        ("r2", "STATE"): _state_item("r2", "pending"), ("r1", "STATE"): _state_item("r1", "pending")},
                       page_size=1)
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING], limit=1)
    assert [(r.run_id, r.state is None) for r in rows] == [("r4", True), ("r2", False)]
    assert [q["Limit"] for q in table.queries] == [1, 1, 1]


@pytest.mark.parametrize("limit", [None, 1])
def test_ddb_list_runs_row_found_in_a_requested_ended_group_is_listed_even_if_live_withheld_it(limit):
    # r1 同时在 live 与 passed 分组（索引尚未跟上），读回为 running：经 live 找到时它是未被请求的非终态、不列出，但它也是经所请求的
    # passed 分组找到的，不复筛、照常列出；截不截断结果相同，且只读回一次
    table = _FakeTable({"live": ["r1"], "passed": ["r1"]}, {("r1", "STATE"): _state_item("r1", "running")})
    rows = DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PENDING, Status.PASSED], limit=limit)
    assert [(r.run_id, r.state.status) for r in rows] == [("r1", Status.RUNNING)]
    assert len(table.batches) == 1


def test_ddb_list_runs_unknown_run_status_read_back_is_unreadable():
    table = _FakeTable({"live": ["r1"]}, {("r1", "STATE"): _state_item("r1", "paused")})
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


@pytest.mark.parametrize("processed_in_failing_batch, missing", [(0, 70), (20, 50)])
def test_ddb_list_runs_incomplete_counts_the_batches_never_sent(monkeypatch, processed_in_failing_batch, missing):
    """多批读回时第二批重试耗尽：报的未读回数含这一批剩下的 run 与没有发出的第三批，第一批已完整读回、不计。
    120 个 run 共 240 个键，按每批 100 个键分三批（50、50、20 个 run）；第二批第一次只处理前若干个 run 的键、其余一直未处理。"""
    monkeypatch.setattr(ddb_module, "time", SimpleNamespace(sleep=lambda s: None))
    run_ids = [f"r{i:03d}" for i in range(120)]
    table = _FakeTable({"passed": run_ids}, {(r, "STATE"): _state_item(r, "passed") for r in run_ids})

    def batch_get_item(*, RequestItems):
        req = RequestItems[_TABLE]
        table.batches.append(req)
        keys = req["Keys"]
        if len(table.batches) == 1:  # 第一批完整读回
            return {"Responses": {_TABLE: [table._items[(k["run_id"], k["item_type"])] for k in keys
                                           if (k["run_id"], k["item_type"]) in table._items]}, "UnprocessedKeys": {}}
        done = keys[:2 * processed_in_failing_batch] if len(table.batches) == 2 else []
        return {"Responses": {_TABLE: [table._items[(k["run_id"], k["item_type"])] for k in done
                                       if (k["run_id"], k["item_type"]) in table._items]},
                "UnprocessedKeys": {_TABLE: {"Keys": keys[len(done):]}}}

    table.meta.client.batch_get_item = batch_get_item
    with pytest.raises(RunListingIncomplete) as exc:
        DynamoDBRunStore(table, list_index_name=_LIST_INDEX).list_runs([Status.PASSED], limit=None)
    assert exc.value.missing == missing
    assert f"仍有 {missing} 个 run 没有读回" in str(exc.value)
    assert len(table.batches) == 1 + ddb_module._BATCH_GET_MAX_RETRIES + 1  # 第三批没有发出
