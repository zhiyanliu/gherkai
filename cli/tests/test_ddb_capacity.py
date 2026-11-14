"""`tools/ddb_capacity.py` 的单测：在 moto 上核对它给 DynamoDB 请求加上 ReturnConsumedCapacity、逐条记下、不改调用方看到的
响应、命令的结果原样传出、报告只写进文件；合计逻辑用合成的 ConsumedCapacity 核对。

moto 返回的 ConsumedCapacity 不完整（不分表与索引、数值不是服务端的真实读数），所以凡是数值的断言都喂合成的响应形态，
只以工具自身的拆分与累加逻辑为准；moto 只用来证明参数确实发到了请求里、请求确实被逐条记下。

被包裹命令的 stdout、stderr 与退出码与直接执行时相同，这一点依赖解释器刷新标准流的时机、管道与文件大小限制下写入失败的真实行为，
进程内的替身证明不了：另在子进程里把两个流接到读端已关闭的管道、只读若干字节就关闭的接收端、同一个管道、受文件大小
限制的文件与不同编码的管道，比较替身命令直接执行与经本工具执行的退出码、stdout 字节与 stderr 字节。未捕获异常的
traceback 经本工具执行时多出几层调用栈（见工具模块头的局限一节），所以抛异常的情形只在 traceback 写不出的设置下比较。
报告路径不可写的对照用存在但不可写的目录：不存在的目录、符号链接、设备、FIFO 等目标在执行之前即为用法错误，命令不执行，
不在对照之列，另在真实文件系统的临时目录里逐一核对。
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import boto3
import botocore.client
import pytest
from _doc_rules import REPO
from moto import mock_aws

TOOL = REPO / "tools" / "ddb_capacity.py"
TABLE = "cap-runs"
INDEX = "status_group-run_id-index"


def _load():
    spec = importlib.util.spec_from_file_location("ddb_capacity", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ddb_capacity = _load()


@pytest.fixture
def ddb(monkeypatch):
    for var, value in (("AWS_ACCESS_KEY_ID", "t"), ("AWS_SECRET_ACCESS_KEY", "t"),
                       ("AWS_DEFAULT_REGION", "us-east-1"), ("AWS_REGION", "us-east-1")):
        monkeypatch.setenv(var, value)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        client = boto3.client("dynamodb", region_name="us-east-1")
        client.create_table(
            TableName=TABLE,
            KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"},
                       {"AttributeName": "item_type", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"},
                                  {"AttributeName": "item_type", "AttributeType": "S"},
                                  {"AttributeName": "status_group", "AttributeType": "S"}],
            GlobalSecondaryIndexes=[{
                "IndexName": INDEX,
                "KeySchema": [{"AttributeName": "status_group", "KeyType": "HASH"},
                              {"AttributeName": "run_id", "KeyType": "RANGE"}],
                "Projection": {"ProjectionType": "KEYS_ONLY"},
            }],
            BillingMode="PAY_PER_REQUEST")
        yield client


def _wire_capture(client) -> list[tuple[str, dict]]:
    """记下每个 DynamoDB 请求实际发出的请求体（经 botocore 的 before-call 事件，在本工具加参数之后）。"""
    sent: list[tuple[str, dict]] = []

    def capture(model, params, **_):
        sent.append((model.name, json.loads(params["body"] or b"{}")))

    client.meta.events.register("before-call.dynamodb", capture)
    return sent


def _seed(client, n: int = 3) -> None:
    for i in range(n):
        client.put_item(TableName=TABLE, Item={"run_id": {"S": f"r{i}"}, "item_type": {"S": "STATE"},
                                               "status_group": {"S": "live"}})


def test_adds_the_parameter_records_each_request_and_leaves_the_response_as_the_caller_expects(ddb):
    sent = _wire_capture(ddb)
    original = botocore.client.BaseClient._make_api_call
    recorder = ddb_capacity.Recorder()
    with recorder.installed():
        _seed(ddb, 3)
        resp = ddb.query(TableName=TABLE, IndexName=INDEX, Limit=2,
                         KeyConditionExpression="status_group = :g", ExpressionAttributeValues={":g": {"S": "live"}})
        got = ddb.get_item(TableName=TABLE, Key={"run_id": {"S": "r0"}, "item_type": {"S": "STATE"}})
        ddb.describe_table(TableName=TABLE)   # 不带该参数的操作：原样发出，记下但没有消耗
    assert botocore.client.BaseClient._make_api_call is original   # 退出后已还原

    # 支持该参数的请求都带上了它；不支持的（DescribeTable）没有被加
    assert [(op, body.get("ReturnConsumedCapacity")) for op, body in sent] == (
        [("PutItem", "INDEXES")] * 3 + [("Query", "INDEXES"), ("GetItem", "INDEXES"), ("DescribeTable", None)])
    # 调用方没有要这个字段：交还的响应里没有它
    assert "ConsumedCapacity" not in resp and "ConsumedCapacity" not in got
    assert resp["Count"] == 2 and "LastEvaluatedKey" in resp

    recs = recorder.records
    assert [r["seq"] for r in recs] == [1, 2, 3, 4, 5, 6]
    assert [r["op"] for r in recs] == ["PutItem"] * 3 + ["Query", "GetItem", "DescribeTable"]
    assert all(r["tables"] == [TABLE] for r in recs)
    query = recs[3]
    assert (query["index"], query["limit"], query["count"], query["more"], query["added_by_tool"]) == (
        INDEX, 2, 2, True, True)
    assert recs[4]["count"] == 1
    assert "capacity" not in recs[5] and recs[5]["added_by_tool"] is False and recs[5]["capacity_applicable"] is False
    agg = ddb_capacity.totals(recs)
    assert agg["not_applicable"] == 1 and agg["requests"] == 6


def test_requests_from_other_threads_and_separately_built_sessions_are_recorded(ddb):
    """补丁打在 botocore 的客户端基类上：命令在别的线程里、或另建 session / boto3 resource 发出的请求同样记到。"""
    import threading

    recorder = ddb_capacity.Recorder()
    with recorder.installed():
        other = boto3.session.Session(region_name="us-east-1")
        worker = threading.Thread(target=lambda: other.client("dynamodb").scan(TableName=TABLE))
        worker.start()
        worker.join()
        other.resource("dynamodb").Table(TABLE).put_item(Item={"run_id": "r9", "item_type": "STATE"})
    assert [(r["op"], r["added_by_tool"]) for r in recorder.records] == [("Scan", True), ("PutItem", True)]


def test_a_caller_that_asks_for_consumed_capacity_keeps_its_own_setting_and_response(ddb):
    sent = _wire_capture(ddb)
    recorder = ddb_capacity.Recorder()
    with recorder.installed():
        resp = ddb.scan(TableName=TABLE, ReturnConsumedCapacity="TOTAL")
    assert sent == [("Scan", {"TableName": TABLE, "ReturnConsumedCapacity": "TOTAL"})]
    assert recorder.records[0]["added_by_tool"] is False
    assert recorder.records[0]["return_consumed_capacity"] == "TOTAL"
    # moto 给不给 ConsumedCapacity 不作断言；给了就必须原样留给调用方
    assert ("ConsumedCapacity" in resp) == bool(recorder.records[0].get("capacity"))
    assert ("ConsumedCapacity" in resp) != bool(recorder.records[0].get("capacity_missing"))


def test_a_request_whose_response_has_no_consumed_capacity_is_marked_and_not_counted_as_zero(ddb):
    """调用方自己给了 NONE：响应里没有消耗字段，这一条标为「未返回消耗」，不当作零并入合计，合计处注明未计入几条。"""
    recorder = ddb_capacity.Recorder()
    with recorder.installed():
        ddb.get_item(TableName=TABLE, Key={"run_id": {"S": "r0"}, "item_type": {"S": "STATE"}},
                     ReturnConsumedCapacity="NONE")
    rec = recorder.records[0]
    assert rec["added_by_tool"] is False and rec["capacity_missing"] is True and "capacity" not in rec
    agg = ddb_capacity.totals(recorder.records)
    assert (agg["counted"], agg["without_capacity"], agg["errors"], agg["not_applicable"]) == (0, 1, 0, 0)
    out = io.StringIO()
    ddb_capacity.report(recorder.records, out)
    text = out.getvalue()
    assert "未返回消耗（消耗未知，未计入合计）" in text
    assert "全部：读 0，写 0（另有 1 个请求的消耗未知、未计入：失败 0 个，未返回消耗 1 个）" in text, text


def test_a_failed_request_is_recorded_with_its_error_code_and_still_raised(ddb):
    recorder = ddb_capacity.Recorder()
    with recorder.installed(), pytest.raises(ddb.exceptions.ResourceNotFoundException):
        ddb.get_item(TableName="no-such-table", Key={"run_id": {"S": "x"}, "item_type": {"S": "STATE"}})
    assert recorder.records == [{
        "op": "GetItem", "tables": ["no-such-table"], "index": None, "limit": None, "consistent_read": None,
        "return_consumed_capacity": "INDEXES", "added_by_tool": True, "capacity_applicable": True,
        "error": "ResourceNotFoundException", "seq": 1}]
    agg = ddb_capacity.totals(recorder.records)
    assert (agg["errors"], agg["counted"]) == (1, 0)


def test_the_patch_is_removed_after_the_block_even_when_it_raises():
    original = botocore.client.BaseClient._make_api_call
    with pytest.raises(RuntimeError), ddb_capacity.Recorder().installed():
        assert botocore.client.BaseClient._make_api_call is not original
        raise RuntimeError("boom")
    assert botocore.client.BaseClient._make_api_call is original


# ── 合计逻辑：喂合成的 ConsumedCapacity ──────────────────────────────────────


def test_capacity_split_separates_table_and_indexes_and_falls_back_by_operation_kind():
    indexes = {"TableName": "t", "CapacityUnits": 3.0, "ReadCapacityUnits": 3.0,
               "Table": {"CapacityUnits": 1.0, "ReadCapacityUnits": 1.0},
               "GlobalSecondaryIndexes": {"g": {"CapacityUnits": 2.0, "ReadCapacityUnits": 2.0}}}
    assert ddb_capacity._capacity_entries("Query", indexes) == [
        {"table": "t", "read": 3.0, "write": 0.0, "table_read": 1.0, "table_write": 0.0,
         "indexes": {"g": {"kind": "gsi", "read": 2.0, "write": 0.0}}, "unsplit_read": 0.0, "unsplit_write": 0.0}]
    # 只有 CapacityUnits：读操作归读、写操作归写；没有 Table 一项时表本身的消耗未知（None，不是 0），整体数字记为未细分
    scan = ddb_capacity._capacity_entries("Scan", {"TableName": "t", "CapacityUnits": 0.5})[0]
    assert (scan["read"], scan["table_read"], scan["unsplit_read"], scan["unsplit_write"]) == (0.5, None, 0.5, 0.0)
    put = ddb_capacity._capacity_entries("PutItem", {"TableName": "t", "CapacityUnits": 2.0,
                                                     "GlobalSecondaryIndexes": {"g": {"CapacityUnits": 1.0}}})[0]
    assert (put["write"], put["table_write"], put["indexes"]["g"]["write"], put["unsplit_write"]) == (
        2.0, None, 1.0, 1.0)
    # 只报了索引、没有 Table 一项，且整体数字全部落在索引上：表本身未知，未细分为 0
    gsi_only = ddb_capacity._capacity_entries(
        "Query", {"TableName": "t", "CapacityUnits": 0.5, "GlobalSecondaryIndexes": {"g": {"CapacityUnits": 0.5}}})[0]
    assert (gsi_only["table_read"], gsi_only["indexes"]["g"]["read"], gsi_only["read"], gsi_only["unsplit_read"]) == (
        None, 0.5, 0.5, 0.0)
    # 批量操作的列表形态：每张表一项
    batch = ddb_capacity._capacity_entries("BatchGetItem", [{"TableName": "a", "CapacityUnits": 1.0},
                                                            {"TableName": "b", "CapacityUnits": 4.0}])
    assert [(e["table"], e["table_read"], e["unsplit_read"]) for e in batch] == [("a", None, 1.0), ("b", None, 4.0)]
    assert ddb_capacity._capacity_entries("GetItem", None) == []


def _report_lines(records: list[dict]) -> list[str]:
    for i, r in enumerate(records, 1):
        r.setdefault("seq", i)
        r.setdefault("tables", [TABLE])
    out = io.StringIO()
    ddb_capacity.report(records, out)
    return out.getvalue().splitlines()


def test_a_gsi_query_with_total_reports_its_units_as_unsplit_not_as_the_table():
    """调用方自己给了 TOTAL 的 GSI 查询：响应只有整体数字，归属未知，逐条与合计都单列为未细分；表本身不记 0，而是
    不出现（逐条没有「表」一项，合计没有这张表的「表」一行），索引也没有记录。"""
    records = [{"op": "Query", "index": INDEX, "capacity_applicable": True, "count": 3, "scanned": 3, "more": False,
                "capacity": ddb_capacity._capacity_entries("Query", {"TableName": TABLE, "CapacityUnits": 2.0})}]
    agg = ddb_capacity.totals(records)
    assert agg["tables"] == {} and agg["indexes"] == {}
    assert agg["unsplit"] == {TABLE: {"read": 2.0, "write": 0.0}}
    assert (agg["read"], agg["write"], agg["counted"]) == (2.0, 0.0, 1)
    lines = _report_lines(records)
    assert lines[2].endswith(f"| {TABLE}：未细分 R2 W0"), lines[2]
    assert not [line for line in lines if line.startswith(f"  表 {TABLE}")], lines
    assert f"  未细分 {TABLE}：读 2，写 0（响应未完整细分，这部分在表与各索引之间如何分摊未知）" in lines
    assert lines[-1] == "  全部：读 2，写 0", lines[-1]


def test_a_write_with_total_that_also_writes_an_index_reports_its_units_as_unsplit():
    """带 TOTAL 的写入（写表的同时写状态分组索引）：整体 3 个写单位不拆给表或索引，记为未细分；与带细目的写入并列累加。"""
    records = [
        {"op": "PutItem", "capacity_applicable": True,
         "capacity": ddb_capacity._capacity_entries("PutItem", {"TableName": TABLE, "CapacityUnits": 3.0})},
        {"op": "UpdateItem", "capacity_applicable": True,
         "capacity": ddb_capacity._capacity_entries("UpdateItem", {
             "TableName": TABLE, "CapacityUnits": 2.0, "Table": {"CapacityUnits": 1.0},
             "GlobalSecondaryIndexes": {INDEX: {"CapacityUnits": 1.0}}})},
    ]
    agg = ddb_capacity.totals(records)
    assert agg["tables"] == {TABLE: {"read": 0.0, "write": 1.0}}
    assert agg["indexes"] == {f"{TABLE}/{INDEX}": {"kind": "gsi", "read": 0.0, "write": 1.0}}
    assert agg["unsplit"] == {TABLE: {"read": 0.0, "write": 3.0}}
    assert (agg["read"], agg["write"]) == (0.0, 5.0)
    lines = _report_lines(records)
    assert lines[2].endswith(f"| {TABLE}：未细分 R0 W3"), lines[2]
    assert lines[3].endswith(f"{TABLE}：表 R0 W1，gsi {INDEX} R0 W1"), lines[3]
    assert f"  未细分 {TABLE}：读 0，写 3（响应未完整细分，这部分在表与各索引之间如何分摊未知）" in lines
    assert lines[-1] == "  全部：读 0，写 5", lines[-1]


def test_a_response_with_some_index_detail_but_no_table_entry_reports_the_rest_as_unsplit():
    """响应带了部分索引的细目、却没有 Table 一项：已报的索引照常记入，表本身未知，整体数字减去索引之后的部分记为未细分。"""
    records = [{"op": "PutItem", "capacity_applicable": True,
                "capacity": ddb_capacity._capacity_entries("PutItem", {
                    "TableName": TABLE, "CapacityUnits": 3.0, "GlobalSecondaryIndexes": {INDEX: {"CapacityUnits": 1.0}}})}]
    agg = ddb_capacity.totals(records)
    assert agg["tables"] == {}
    assert agg["indexes"] == {f"{TABLE}/{INDEX}": {"kind": "gsi", "read": 0.0, "write": 1.0}}
    assert agg["unsplit"] == {TABLE: {"read": 0.0, "write": 2.0}}
    lines = _report_lines(records)
    assert not [line for line in lines if line.startswith(f"  表 {TABLE}")], lines
    assert f"  未细分 {TABLE}：读 0，写 2（响应未完整细分，这部分在表与各索引之间如何分摊未知）" in lines
    assert lines[-1] == "  全部：读 0，写 3", lines[-1]


@pytest.mark.parametrize("resp, more", [({"Count": 0, "LastEvaluatedKey": {}}, False),
                                        ({"Count": 0}, False),
                                        ({"Count": 1, "LastEvaluatedKey": {"run_id": {"S": "r1"}}}, True)])
def test_an_empty_last_evaluated_key_means_there_is_no_next_page(resp, more):
    assert ddb_capacity._result_counts("Query", {}, resp)["more"] is more


def test_totals_add_up_per_table_and_per_index():
    records = [
        {"op": "Query", "capacity": ddb_capacity._capacity_entries("Query", {
            "TableName": "t", "CapacityUnits": 1.5, "Table": {"CapacityUnits": 0.0},
            "GlobalSecondaryIndexes": {"g": {"CapacityUnits": 1.5}}})},
        {"op": "Query", "capacity": ddb_capacity._capacity_entries("Query", {
            "TableName": "t", "CapacityUnits": 0.5, "Table": {"CapacityUnits": 0.0},
            "GlobalSecondaryIndexes": {"g": {"CapacityUnits": 0.5}}})},
        {"op": "BatchGetItem", "capacity": ddb_capacity._capacity_entries("BatchGetItem", [
            {"TableName": "t", "CapacityUnits": 4.0, "Table": {"CapacityUnits": 4.0}}])},
        {"op": "UpdateItem", "capacity": ddb_capacity._capacity_entries("UpdateItem", {
            "TableName": "t", "CapacityUnits": 3.0, "Table": {"CapacityUnits": 1.0},
            "GlobalSecondaryIndexes": {"g": {"CapacityUnits": 2.0}}})},
        {"op": "GetItem", "capacity_applicable": True, "capacity_missing": True},
        {"op": "GetItem", "capacity_applicable": True, "error": "ThrottlingException"},
        {"op": "DescribeTable", "capacity_applicable": False},
    ]
    agg = ddb_capacity.totals(records)
    assert agg["tables"] == {"t": {"read": 4.0, "write": 1.0}}
    assert agg["indexes"] == {"t/g": {"kind": "gsi", "read": 2.0, "write": 2.0}}
    assert (agg["read"], agg["write"]) == (6.0, 3.0)
    assert (agg["requests"], agg["counted"], agg["errors"], agg["without_capacity"], agg["not_applicable"]) == (
        7, 4, 1, 1, 1)
    assert agg["by_op"] == {"Query": 2, "BatchGetItem": 1, "UpdateItem": 1, "GetItem": 2, "DescribeTable": 1}
    # 合计处注明未计入的条数（不适用的操作没有消耗可言，不算在内）
    out = io.StringIO()
    for i, r in enumerate(records, 1):
        r.setdefault("seq", i)
        r.setdefault("tables", ["t"])
    ddb_capacity.report(records, out)
    lines = out.getvalue().splitlines()
    assert lines[1] == ddb_capacity.SCOPE
    assert lines[-1] == "  全部：读 6，写 3（另有 2 个请求的消耗未知、未计入：失败 1 个，未返回消耗 1 个）", lines[-1]
    assert lines[6].endswith("未返回消耗（消耗未知，未计入合计）") and lines[7].endswith("（消耗未知，未计入合计）")
    assert lines[8].endswith("不适用（该操作不报告读写单位）")


def test_a_malformed_request_still_gets_the_sdk_validation_error(ddb):
    """元数据在调用 SDK 之前从参数里提取；参数形状不合法时提取不得抛出自己的异常、盖掉 SDK 的参数校验错误。"""
    from botocore.exceptions import ParamValidationError

    with pytest.raises(ParamValidationError):
        ddb.transact_write_items(TransactItems=[None])
    recorder = ddb_capacity.Recorder()
    with recorder.installed(), pytest.raises(ParamValidationError):
        ddb.transact_write_items(TransactItems=[None])
    rec = recorder.records[0]
    assert (rec["op"], rec["tables"], rec["error"]) == ("TransactWriteItems", [], "ParamValidationError"), rec


def test_a_failed_request_with_a_table_name_that_is_not_a_string_still_appears_in_the_text_report(
        ddb, monkeypatch, capsys, tmp_path):
    """TableName=123：SDK 在发出之前报错（这个版本的 botocore 在解析端点时就抛出，错误的类型随版本而不同），错误被记下，
    表名记为文本「123」；文本报告拼接表名时不得因此失败、整份消失。批量请求里不是字符串的表名同样处理。"""
    import gherkai_cli.__main__ as cli_main

    errors: list[str] = []

    def fake_main(argv):
        for call in (lambda: ddb.get_item(TableName=123, Key={"run_id": {"S": "r0"}, "item_type": {"S": "STATE"}}),
                     lambda: ddb.batch_get_item(RequestItems={7: {"Keys": []}})):
            with pytest.raises(Exception) as info:
                call()
            errors.append(type(info.value).__name__)
        return 0

    monkeypatch.setattr(cli_main, "main", fake_main)
    rep, js = _paths(tmp_path)
    assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"]) == 0
    assert capsys.readouterr().err == ""
    lines = rep.read_text(encoding="utf-8").splitlines()
    assert lines[4:6] == [f"#1 GetItem 123 index=- Limit=- 失败 {errors[0]}（消耗未知，未计入合计）",
                          f"#2 BatchGetItem 7 index=- Limit=- 失败 {errors[1]}（消耗未知，未计入合计）"], lines
    assert lines[-1].startswith("  全部："), lines[-1]
    doc = json.loads(js.read_text(encoding="utf-8"))
    assert [(r["tables"], r["error"]) for r in doc["requests"]] == [(["123"], errors[0]), (["7"], errors[1])]


@pytest.mark.parametrize("params, shown", [
    ({"TableName": {"a": [1]}}, "{'a': [1]}"),
    ({}, "-"),
    ({"TransactItems": [{"Put": {"TableName": 5}}, {"Put": {"TableName": ["x"]}}]}, "5,['x']"),
    ({"TableName": "a\nb"}, "'a\\nb'"),
])
def test_table_names_of_any_shape_render_on_a_single_line_of_the_text_report(params, shown):
    """表名为嵌套结构、缺表名、批量请求里表名不是字符串、表名含换行：文本报告照样写出，每个请求只占一行。"""
    rec = {"op": "GetItem", **ddb_capacity._request_meta({**params, "IndexName": "i\nx"}), "error": "X", "seq": 1}
    lines = ddb_capacity.text_report([rec], ["status"], {"kind": "returned", "value": 0}).splitlines()
    assert lines[4] == f"#1 GetItem {shown} index='i\\nx' Limit=- 失败 X（消耗未知，未计入合计）", lines
    assert lines[5].startswith("合计：请求 1 个") and lines[-1].startswith("  全部：")


def test_an_exception_whose_response_has_an_unexpected_shape_is_raised_unchanged(ddb):
    """取错误码时响应的形状不合预期（Error 不是字典）：记下异常类名，原来的异常原样抛出，不被取错误码时的异常盖掉。"""
    class Odd(Exception):
        response = {"Error": None}

    raised = Odd()

    def fail(**_):
        raise raised

    ddb.meta.events.register("before-call.dynamodb.GetItem", fail)
    recorder = ddb_capacity.Recorder()
    with recorder.installed(), pytest.raises(Odd) as info:
        ddb.get_item(TableName=TABLE, Key={"run_id": {"S": "r0"}, "item_type": {"S": "STATE"}})
    assert info.value is raised
    assert recorder.records[0]["error"] == "Odd"


# ── 命令入口：结果原样传出，报告只写进文件 ──────────────────────────────────


def _fake_gherkai(monkeypatch, client, result):
    """把 gherkai 的入口函数换成一个发几次 DynamoDB 请求、往 stdout 写一行、再按 result 返回或抛出的替身。"""
    import gherkai_cli.__main__ as cli_main

    seen: list[list[str]] = []

    def fake_main(argv):
        seen.append(list(argv))
        _seed(client, 2)
        client.query(TableName=TABLE, IndexName=INDEX, KeyConditionExpression="status_group = :g",
                     ExpressionAttributeValues={":g": {"S": "live"}})
        print("COMMAND OUTPUT")
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(cli_main, "main", fake_main)
    return seen


def _paths(tmp_path):
    return tmp_path / "cap.txt", tmp_path / "cap.json"


def test_main_returns_the_command_result_and_writes_both_reports_without_touching_stdout_or_stderr(
        ddb, monkeypatch, capsys, tmp_path):
    seen = _fake_gherkai(monkeypatch, ddb, 3)
    rep, js = _paths(tmp_path)
    assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "list-runs", "--json"]) == 3
    assert seen == [["list-runs", "--json"]]
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("COMMAND OUTPUT\n", "")   # 只有命令自己的输出
    lines = rep.read_text(encoding="utf-8").splitlines()
    assert lines[:4] == [ddb_capacity.HEADER, "命令：gherkai list-runs --json", "结局：返回 3", ddb_capacity.SCOPE]
    assert "Lambda" in lines[3] and "worker" in lines[3]
    assert [line.split()[1] for line in lines[4:7]] == ["PutItem", "PutItem", "Query"]
    assert lines[7].startswith("合计：请求 3 个（PutItem 2、Query 1），计入合计 "), lines[7]
    assert lines[-1].startswith("  全部："), lines[-1]
    doc = json.loads(js.read_text(encoding="utf-8"))
    assert (doc["argv"], doc["exit_code"], doc["outcome"]) == (["list-runs", "--json"], 3,
                                                               {"kind": "returned", "value": 3})
    assert [r["op"] for r in doc["requests"]] == ["PutItem", "PutItem", "Query"]
    assert doc["totals"]["requests"] == 3


@pytest.mark.parametrize("raised, outcome, text", [
    (SystemExit(5), {"kind": "system_exit", "value": 5}, "SystemExit，值为 5"),
    (SystemExit(None), {"kind": "system_exit", "value": None}, "SystemExit，值为 None"),
    (SystemExit("bye"), {"kind": "system_exit", "value": "bye"}, "SystemExit，值为 'bye'"),
    (ValueError("boom"), {"kind": "exception", "type": "ValueError"}, "未捕获的异常 ValueError"),
    (KeyboardInterrupt(), {"kind": "exception", "type": "KeyboardInterrupt"}, "未捕获的异常 KeyboardInterrupt"),
])
def test_what_the_command_raises_is_raised_unchanged_and_the_reports_record_it(ddb, monkeypatch, capsys, tmp_path,
                                                                                raised, outcome, text):
    _fake_gherkai(monkeypatch, ddb, raised)
    rep, js = _paths(tmp_path)
    original = botocore.client.BaseClient._make_api_call
    with pytest.raises(BaseException) as info:
        ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"])
    assert info.value is raised   # 同一个对象，不是转换出来的退出码或新的异常
    assert botocore.client.BaseClient._make_api_call is original   # 补丁在异常路径上已还原
    assert capsys.readouterr().err == ""
    assert rep.read_text(encoding="utf-8").splitlines()[2] == f"结局：{text}"
    doc = json.loads(js.read_text(encoding="utf-8"))
    assert doc["outcome"] == outcome and doc["exit_code"] == outcome.get("value")
    assert doc["totals"]["requests"] == 3


def test_an_exception_type_outside_builtins_is_named_with_its_module():
    from botocore.exceptions import ParamValidationError

    assert ddb_capacity._type_name(ParamValidationError(report="x")) == "botocore.exceptions.ParamValidationError"


@pytest.fixture
def unwritable_dir(tmp_path):
    """一个存在、但不可写的空目录：报告路径通过执行之前的检查，写入时才失败。"""
    import os

    if os.geteuid() == 0:
        pytest.skip("root 不受目录权限约束，构造不出不可写的目录")
    where = tmp_path / "read-only"
    where.mkdir()
    where.chmod(0o500)
    yield where
    where.chmod(0o700)


@pytest.mark.parametrize("bad", ["report", "json", "both"])
@pytest.mark.parametrize("result", [7, ValueError("boom")])
def test_a_report_that_cannot_be_written_changes_nothing_and_does_not_stop_the_other(ddb, monkeypatch, capsys,
                                                                                     tmp_path, unwritable_dir,
                                                                                     bad, result):
    _fake_gherkai(monkeypatch, ddb, result)
    rep, js = _paths(tmp_path)
    rep = unwritable_dir / rep.name if bad in ("report", "both") else rep
    js = unwritable_dir / js.name if bad in ("json", "both") else js
    argv = ["--report", str(rep), "--json", str(js), "--", "status"]
    if isinstance(result, BaseException):
        with pytest.raises(ValueError) as info:
            ddb_capacity.main(argv)
        assert info.value is result
    else:
        assert ddb_capacity.main(argv) == result
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("COMMAND OUTPUT\n", "")   # 写不出也不提示
    assert rep.exists() is (bad == "json") and js.exists() is (bad == "report")
    if bad == "json":
        assert rep.read_text(encoding="utf-8").splitlines()[-1].startswith("  全部：")
    if bad == "report":
        assert json.loads(js.read_text(encoding="utf-8"))["totals"]["requests"] == 3


@pytest.mark.parametrize("broken", ["text_report", "json_report"])
def test_one_report_failing_to_render_does_not_stop_the_other(ddb, monkeypatch, capsys, tmp_path, broken):
    _fake_gherkai(monkeypatch, ddb, 7)

    def boom(*_):
        raise RuntimeError("render failed")

    monkeypatch.setattr(ddb_capacity, broken, boom)
    rep, js = _paths(tmp_path)
    assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"]) == 7
    assert capsys.readouterr().err == ""
    assert rep.exists() is (broken == "json_report") and js.exists() is (broken == "text_report")


def test_an_existing_report_file_is_removed_before_the_command_runs(ddb, monkeypatch, tmp_path):
    """报告写不出时没有提示：上一次留下的同名文件若还在，会被当成这一次的报告。所以执行命令之前先删掉它。"""
    rep, js = _paths(tmp_path)
    rep.write_text("old report", encoding="utf-8")
    js.write_text("{}", encoding="utf-8")
    import gherkai_cli.__main__ as cli_main

    existed: list[bool] = []
    monkeypatch.setattr(cli_main, "main", lambda argv: existed.append(rep.exists() or js.exists()) or 0)
    def broken(*_):
        raise RuntimeError("render failed")

    monkeypatch.setattr(ddb_capacity, "text_report", broken)   # 文本报告写不出：上一次的文件不得留下
    assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"]) == 0
    assert existed == [False]
    assert not rep.exists() and json.loads(js.read_text(encoding="utf-8"))["exit_code"] == 0


@pytest.mark.parametrize("argv", [["list-runs"], ["--", "list-runs"], ["--report", "a", "--json", "./a", "--", "x"],
                                  ["--report", "--", "x"]])
def test_a_usage_error_ends_before_the_command_runs(ddb, monkeypatch, capsys, tmp_path, argv):
    """缺 `--`、--report 与 --json 都不给、两者是同一个文件：本工具自己的用法错误，打印用法、退出码 2，命令没有执行。"""
    monkeypatch.chdir(tmp_path)
    seen = _fake_gherkai(monkeypatch, ddb, 0)
    with pytest.raises(SystemExit) as info:
        ddb_capacity.main(argv)
    assert info.value.code == 2 and seen == []
    captured = capsys.readouterr()
    assert captured.out == "" and "usage: ddb_capacity.py --report" in captured.err, captured.err
    assert list(tmp_path.iterdir()) == []


def _assert_usage_error(monkeypatch, ddb, capsys, argv, message):
    seen = _fake_gherkai(monkeypatch, ddb, 0)
    with pytest.raises(SystemExit) as info:
        ddb_capacity.main(argv)
    assert info.value.code == 2 and seen == []   # 命令没有执行
    captured = capsys.readouterr()
    assert captured.out == "" and "usage: ddb_capacity.py --report" in captured.err, captured.err
    assert message in captured.err, captured.err


@pytest.mark.parametrize("alias", ["dir-symlink", "private-tmp"])
def test_two_paths_that_name_the_same_file_through_an_alias_are_a_usage_error(ddb, monkeypatch, capsys, tmp_path,
                                                                             alias):
    """比较的是解析之后的目标：经符号链接的目录、macOS 上 /tmp 与 /private/tmp 指向同一个文件。
    执行之前就拒绝，路径上已有的文件也不删。"""
    import os
    import tempfile

    if alias == "private-tmp":
        if os.path.realpath("/tmp") == "/tmp":
            pytest.skip("这台机器上 /tmp 不是别名")
        base = Path(tempfile.mkdtemp(dir="/tmp"))
        rep, js = base / "cap", Path("/private") / base.relative_to("/") / "cap"
    else:
        real = tmp_path / "real"
        real.mkdir()
        (tmp_path / "link").symlink_to(real, target_is_directory=True)
        base = real
        rep, js = tmp_path / "link" / "cap", real / "cap"
    try:
        rep.write_text("old", encoding="utf-8")
        _assert_usage_error(monkeypatch, ddb, capsys, ["--report", str(rep), "--json", str(js), "--", "status"],
                            "指向同一个文件")
        assert rep.read_text(encoding="utf-8") == "old"
    finally:
        if alias == "private-tmp":
            import shutil

            shutil.rmtree(base)


def test_paths_in_different_directories_or_with_different_names_are_accepted(ddb, monkeypatch, tmp_path):
    """反面：同名文件在不同目录、同一目录里不同的名字，都照常执行。"""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    for rep, js in ((tmp_path / "a" / "cap", tmp_path / "b" / "cap"), (tmp_path / "cap.txt", tmp_path / "cap.json")):
        seen = _fake_gherkai(monkeypatch, ddb, 0)
        assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"]) == 0
        assert seen == [["status"]] and rep.exists() and js.exists()


@pytest.mark.parametrize("target", ["symlink-to-file", "dangling-symlink", "symlink-to-stderr", "dev-stderr", "dev-null",
                                    "fifo", "directory", "missing-dir", "parent-is-a-file"])
def test_a_report_target_that_is_not_a_plain_file_is_rejected_before_the_command_runs(ddb, monkeypatch, capsys,
                                                                                      tmp_path, target):
    """报告只写进普通文件：符号链接（含指向 /dev/stderr 的）、字符设备、FIFO、目录与不存在的目录都在执行之前被拒，
    --report 与 --json 两边一样；被拒的路径不删、不打开，符号链接指向的文件不变。"""
    import os

    victim = tmp_path / "victim"
    victim.write_text("victim", encoding="utf-8")
    path = tmp_path / "cap.txt"
    message = "已存在且不是普通文件"
    if target == "symlink-to-file":
        path.symlink_to(victim)
    elif target == "dangling-symlink":
        path.symlink_to(tmp_path / "nowhere")
    elif target == "symlink-to-stderr":
        path.symlink_to("/dev/stderr")
    elif target in ("dev-stderr", "dev-null"):
        path = Path("/dev/stderr" if target == "dev-stderr" else "/dev/null")
    if path.is_symlink():   # 含 /dev/stderr 本身（macOS 与 Linux 上它都是符号链接）
        message = "是符号链接"
    if target == "fifo":
        os.mkfifo(path)
    elif target == "directory":
        path.mkdir()
    elif target == "missing-dir":
        path, message = tmp_path / "no-such-dir" / "cap.txt", "所在的目录不存在"
    elif target == "parent-is-a-file":
        path, message = victim / "cap.txt", "所在的目录不存在"
    for argv in (["--report", str(path), "--", "status"], ["--json", str(path), "--", "status"]):
        _assert_usage_error(monkeypatch, ddb, capsys, argv, message)
    assert victim.read_text(encoding="utf-8") == "victim"
    if target == "fifo":
        assert os.path.exists(path) and not path.is_file()   # 不删、不打开


def test_an_existing_report_that_cannot_be_removed_is_a_usage_error_and_the_command_does_not_run(
        ddb, monkeypatch, capsys, tmp_path):
    """目录不可写、旧报告无法删除：留着它就会被误认成这一次的结果，所以执行之前以用法错误结束，旧文件原样留下。"""
    import os

    if os.geteuid() == 0:
        pytest.skip("root 不受目录权限约束，构造不出无法删除的文件")
    where = tmp_path / "read-only"
    where.mkdir()
    old = where / "cap.txt"
    old.write_text("old report", encoding="utf-8")
    where.chmod(0o500)
    try:
        _assert_usage_error(monkeypatch, ddb, capsys, ["--report", str(old), "--", "status"], "已有的文件无法删除")
        assert old.read_text(encoding="utf-8") == "old report"
    finally:
        where.chmod(0o700)


@pytest.mark.parametrize("intruder", ["file", "symlink", "fifo"])
def test_a_report_path_taken_while_the_command_runs_is_not_overwritten(ddb, monkeypatch, capsys, tmp_path, intruder):
    """执行期间有别人在报告路径上建出文件、符号链接或 FIFO：本工具不覆盖它、不经它写到别处、不阻塞，命令的结果不变，
    另一个报告照常写出。"""
    import os

    import gherkai_cli.__main__ as cli_main

    rep, js = _paths(tmp_path)
    victim = tmp_path / "victim"
    victim.write_text("victim", encoding="utf-8")

    def fake_main(argv):
        if intruder == "file":
            rep.write_text("intruder", encoding="utf-8")
        elif intruder == "symlink":
            rep.symlink_to(victim)
        else:
            os.mkfifo(rep)
        print("COMMAND OUTPUT")
        return 5

    monkeypatch.setattr(cli_main, "main", fake_main)
    assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"]) == 5
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("COMMAND OUTPUT\n", "")
    assert victim.read_text(encoding="utf-8") == "victim"
    if intruder == "file":
        assert rep.read_text(encoding="utf-8") == "intruder"
    elif intruder == "symlink":
        assert rep.is_symlink()
    else:
        assert os.path.exists(rep) and not rep.is_file()
    assert json.loads(js.read_text(encoding="utf-8"))["exit_code"] == 5


def test_both_reports_come_from_the_same_snapshot_even_when_a_request_completes_after_the_command_returns(
        ddb, monkeypatch, tmp_path):
    """命令返回时别的线程里还有一个在途的请求，它在文本报告写出之后、JSON 报告写出之前才完成。两份报告用的是同一份
    快照：请求数与逐条内容一致，那个晚完成的请求两份都没有。"""
    import threading

    import gherkai_cli.__main__ as cli_main

    entered, release = threading.Event(), threading.Event()

    def hold(**_):
        entered.set()
        assert release.wait(30)

    late: list[threading.Thread] = []

    def fake_main(argv):
        _seed(ddb, 2)
        ddb.meta.events.register("before-call.dynamodb.GetItem", hold)
        worker = threading.Thread(target=lambda: ddb.get_item(
            TableName=TABLE, Key={"run_id": {"S": "r0"}, "item_type": {"S": "STATE"}}))
        worker.start()
        late.append(worker)
        assert entered.wait(30)   # 请求已经进入补丁、停在发出之前
        return 0

    real_text_report = ddb_capacity.text_report

    def text_then_finish_the_late_request(*args):
        text = real_text_report(*args)
        release.set()
        late[0].join(30)   # 晚完成的请求在 JSON 报告生成之前已追加进记录
        return text

    monkeypatch.setattr(cli_main, "main", fake_main)
    monkeypatch.setattr(ddb_capacity, "text_report", text_then_finish_the_late_request)
    rep, js = _paths(tmp_path)
    assert ddb_capacity.main(["--report", str(rep), "--json", str(js), "--", "status"]) == 0
    assert not late[0].is_alive()
    lines = rep.read_text(encoding="utf-8").splitlines()
    doc = json.loads(js.read_text(encoding="utf-8"))
    assert lines[6].startswith("合计：请求 2 个（PutItem 2），"), lines[6]
    assert doc["totals"]["requests"] == 2 and [r["op"] for r in doc["requests"]] == ["PutItem", "PutItem"]
    assert [line.split()[:2] for line in lines[4:6]] == [[f"#{r['seq']}", r["op"]] for r in doc["requests"]]


# ── 真实管道加子进程：直接执行与经本工具执行，退出码、stdout 字节、stderr 字节三样都相同 ─────────────
#
# 替身 CLI 是放在临时目录、经 PYTHONPATH 排在已安装的 gherkai_cli 之前的一个同名包；它不发 DynamoDB 请求。直接执行用
# 与 console script 相同的形态（`sys.exit(main())`），经本工具执行就是真实的命令行 `python tools/ddb_capacity.py … -- …`。
# 替身的参数是（行为，stderr 的种类）：plain 是解释器自己的 stderr，forward 是命令一开始换上的、不带文件描述符、把 write
# 与 flush 转发给 sys.__stderr__ 的包装流；counting 把 stdout 与 stderr 都换成每次刷新先写一个标记的包装流，本工具额外
# 刷新或替换了哪个流，标记的个数与位置就会不同。

_FAKE_INIT = """
import os

if os.environ.get("FAKE_FSIZE"):   # 文件大小限制：之后这个进程写的文件（stderr 接的文件、报告文件）都受它约束
    import resource

    n = int(os.environ["FAKE_FSIZE"])
    resource.setrlimit(resource.RLIMIT_FSIZE, (n, n))
"""

_FAKE_MAIN = """
import atexit
import io
import logging   # 与真实的 gherkai_cli 相同，导入时即引入 logging：它在退出时刷新一次 sys.stderr
import sys


class Forward(io.TextIOBase):
    def write(self, s):
        return sys.__stderr__.write(s)

    def flush(self):
        sys.__stderr__.flush()


class Counting(io.TextIOBase):   # 每次刷新先写一个标记：流被刷新了几次、在什么时候刷新，都留在输出里
    def __init__(self, target, mark):
        super().__init__()
        self._target, self._mark = target, mark

    def write(self, s):
        return self._target.write(s)

    def flush(self):
        self._target.write(self._mark)
        self._target.flush()

    def close(self):   # 回收时不再刷新，标记只来自显式的刷新
        pass


def _big_write():   # 往 stderr 写一大块并自己捕获写失败
    try:
        sys.stderr.write("X" * 200000)
        sys.stderr.flush()
    except OSError:
        pass


def _flood():   # 写到接收端不再接收为止
    try:
        for _ in range(1000):
            sys.stderr.write("F" * 4096)
            sys.stderr.flush()
    except OSError:
        pass


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    behaviour, kind = argv
    if kind == "forward":
        sys.stderr = Forward()
    elif kind == "counting":
        sys.stdout, sys.stderr = Counting(sys.__stdout__, "<o>"), Counting(sys.__stderr__, "<e>")
    if behaviour == "raise":
        raise ValueError("boom")
    if behaviour == "exit9":
        sys.exit(9)
    if behaviour == "exit-str":
        sys.exit("bye")
    if behaviour == "stdout":
        print("COMMAND OUTPUT")
    elif behaviour == "stderr":
        sys.stderr.write("COMMAND NOTE")   # 不带换行：留在缓冲里，退出时才刷新
    elif behaviour == "stderr-line":
        print("COMMAND NOTE", file=sys.stderr)   # 带换行：写入时即刷新
    elif behaviour == "atexit-big":
        atexit.register(_big_write)
        return 7
    elif behaviour == "excepthook-big":
        sys.excepthook = lambda *_: _big_write()
        raise ValueError("boom")
    elif behaviour == "saved-ref":   # 命令保存的流引用，返回之后才写
        atexit.register(sys.stderr.write, "LATE NOTE")
    elif behaviour == "interleave":
        print("OUT 1")
        sys.stderr.write("ERR 1\\n")
        sys.stderr.write("ERR 2")   # 不带换行：主模块结束时解释器先刷新 stderr、再刷新 stdout
        atexit.register(lambda: sys.stderr.write("LATE\\n"))
        return 3
    elif behaviour == "non-ascii":
        sys.stderr.write("日")   # 不带换行：iso2022_jp 的编码器停在双字节的状态
    elif behaviour in ("flood", "flood-raise"):
        print("OUT")
        _flood()
        if behaviour == "flood-raise":
            raise ValueError("boom")
        sys.exit("bye")
    return int(behaviour) if behaviour.isdigit() else 0
"""

_DIRECT = "import sys\nfrom gherkai_cli.__main__ import main\nsys.exit(main())\n"

_SHORT_READ = 1000   # short-reader：接收端只读这么多字节就关闭
_FSIZE = 300         # fsize：文件大小限制（字节）

# setup 的取值：closed-stderr、closed-stdout 是该流接到读端已关闭的管道；merged 是 stdout 与 stderr 接同一个管道；
# short-reader 是 stderr 的接收端读 _SHORT_READ 字节后关闭；fsize 是两个流接文件、文件大小限制为 _FSIZE；
# open-<编码> 是两个流接普通管道、stderr 的编码由 PYTHONIOENCODING 指定。report 的取值：ok 是两个报告路径可写，bad 是都不可写
_CLOSED_STDERR = ["0", "7", "raise", "exit9", "exit-str", "stdout", "stderr", "stderr-line", "atexit-big",
                  "excepthook-big", "saved-ref"]
_CASES = (
    [("closed-stderr", b, k, "ok") for k in ("plain", "forward") for b in _CLOSED_STDERR]
    + [("closed-stderr", b, "plain", "bad") for b in ("7", "raise")]
    + [("closed-stdout", b, "plain", "ok") for b in ("stdout", "0")]
    + [("merged", "interleave", "plain", r) for r in ("ok", "bad")]
    + [("short-reader", b, k, "ok") for b in ("flood", "flood-raise") for k in ("plain", "forward")]
    + [("fsize", b, "plain", "ok") for b in ("flood", "flood-raise")]
    + [("open-utf-8", "non-ascii", k, "ok") for k in ("plain", "forward")]
    + [(f"open-{codec}", "non-ascii", "plain", "ok") for codec in ("iso2022_jp", "utf-16")]
    + [("open-utf-8", b, "counting", "ok") for b in ("0", "stderr", "interleave")]
    + [("merged", "interleave", "counting", "ok")]
    + [("open-utf-8", b, "plain", "bad") for b in ("exit-str", "interleave", "non-ascii")])
_DIRECT_RUNS = sorted({case[:3] for case in _CASES})


def _spawn(setup: str, argv: list[str], env: dict, work) -> tuple[int, bytes, bytes]:
    """按 setup 接好 stdout 与 stderr 执行 argv，返回（退出码，stdout 的字节，stderr 的字节）；接到读端已关闭的管道的那个流
    记为空。"""
    import os
    import subprocess

    if setup.startswith("closed-"):
        read_end, write_end = os.pipe()
        os.close(read_end)
        try:
            closed, other = ("stderr", "stdout") if setup == "closed-stderr" else ("stdout", "stderr")
            proc = subprocess.run(argv, **{closed: write_end, other: subprocess.PIPE}, env=env, timeout=120)
        finally:
            os.close(write_end)
        got = proc.stdout if other == "stdout" else proc.stderr
        return (proc.returncode, got, b"") if other == "stdout" else (proc.returncode, b"", got)
    if setup == "merged":
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, timeout=120)
        return proc.returncode, proc.stdout, b""
    if setup == "short-reader":
        out = work / "stdout"
        with out.open("wb") as sink:
            proc = subprocess.Popen(argv, stdout=sink, stderr=subprocess.PIPE, env=env)
            got = b""
            while len(got) < _SHORT_READ:
                chunk = proc.stderr.read(_SHORT_READ - len(got))
                if not chunk:
                    break
                got += chunk
            proc.stderr.close()
            proc.wait(timeout=120)
        return proc.returncode, out.read_bytes(), got
    if setup == "fsize":
        out, err = work / "stdout", work / "stderr"
        with out.open("wb") as o, err.open("wb") as e:
            proc = subprocess.run(argv, stdout=o, stderr=e, env={**env, "FAKE_FSIZE": str(_FSIZE)}, timeout=120)
        return proc.returncode, out.read_bytes(), err.read_bytes()
    proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env={**env, "PYTHONIOENCODING": setup.removeprefix("open-")}, timeout=120)
    return proc.returncode, proc.stdout, proc.stderr


@pytest.fixture(scope="module")
def pipe_results(tmp_path_factory):
    """全部直接执行与经本工具执行的子进程并行执行一次。返回（直接执行的结果，经本工具执行的结果，各用例的报告路径）。"""
    import os
    from concurrent.futures import ThreadPoolExecutor

    root = tmp_path_factory.mktemp("pipes")
    pkg = root / "fake" / "gherkai_cli"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text(_FAKE_INIT, encoding="utf-8")
    (pkg / "__main__.py").write_text(_FAKE_MAIN, encoding="utf-8")
    (root / "direct.py").write_text(_DIRECT, encoding="utf-8")
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTHONIOENCODING", "PYTHONUNBUFFERED", "PYTHONWARNINGS", "PYTHONDEVMODE", "PYTHONPATH")}
    env.update(PYTHONPATH=str(root / "fake"), PYTHONDONTWRITEBYTECODE="1")

    def direct(key):
        work = root / "direct" / "-".join(key)
        work.mkdir(parents=True)
        setup, behaviour, kind = key
        return _spawn(setup, [sys.executable, str(root / "direct.py"), behaviour, kind], env, work)

    works, reports = {}, {}
    for i, case in enumerate(_CASES):
        works[case] = root / "wrapped" / str(i)
        works[case].mkdir(parents=True)
        where = works[case]
        if case[3] == "bad":   # 存在但不可写的目录：通过执行之前的检查，写入时才失败
            where = works[case] / "read-only"
            where.mkdir()
            where.chmod(0o500)
        reports[case] = (where / "cap.txt", where / "cap.json")

    def wrapped(case):
        setup, behaviour, kind, _ = case
        rep, js = reports[case]
        return _spawn(setup, [sys.executable, str(TOOL), "--report", str(rep), "--json", str(js), "--", behaviour, kind],
                      env, works[case])

    jobs = [(direct, key) for key in _DIRECT_RUNS] + [(wrapped, case) for case in _CASES]
    with ThreadPoolExecutor(max_workers=min(len(jobs), (os.cpu_count() or 2) * 2)) as pool:
        results = list(pool.map(lambda job: job[0](job[1]), jobs))
    return (dict(zip(_DIRECT_RUNS, results[:len(_DIRECT_RUNS)])), dict(zip(_CASES, results[len(_DIRECT_RUNS):])),
            reports)


def test_the_real_cli_imports_logging_on_import_as_the_stand_in_does():
    """本工具经 botocore 在命令之前引入 logging，logging 在退出时刷新一次 sys.stderr。真实的 gherkai_cli 导入时同样引入
    它，直接执行时也有这次刷新，替身照此引入；真实 CLI 若不再在导入时引入 logging，这次刷新就成了本工具带来的差别。"""
    import subprocess

    code = "import sys, gherkai_cli.__main__; print('logging' in sys.modules)"
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert proc.stdout.strip() == "True", (proc.stdout, proc.stderr)


@pytest.mark.timeout(240)
@pytest.mark.parametrize("case", _CASES, ids=["-".join(c) for c in _CASES])
def test_the_command_streams_and_exit_code_are_the_same_with_and_without_the_tool(pipe_results, case):
    """本工具不写、不刷新、不替换 sys.stdout 与 sys.stderr：退出码、stdout 的字节、stderr 的字节（含先后次序与编码器的
    状态）都与直接执行相同，报告路径不可写时也一样。"""
    direct, wrapped, _ = pipe_results
    assert wrapped[case] == direct[case[:3]], (wrapped[case], direct[case[:3]])


@pytest.mark.timeout(240)
def test_the_pipe_setups_really_exercise_the_failure_paths(pipe_results):
    """对照的前提：读端确实已关闭、接收端确实只收下了限定的字节、次序确实取决于刷新的时机。直接执行的结果须是下面这些值，
    否则上面的对照只是在比较两次都成功的执行。"""
    direct, _, _ = pipe_results
    assert direct[("closed-stderr", "stderr", "plain")][0] == 120   # 退出时刷新 stderr 失败
    assert direct[("closed-stderr", "saved-ref", "plain")][0] == 120
    assert direct[("closed-stdout", "stdout", "plain")][0] == 120
    assert [direct[("closed-stderr", b, "plain")][0] for b in ("0", "7", "exit9")] == [0, 7, 9]
    assert direct[("merged", "interleave", "plain")] == (3, b"ERR 1\nERR 2OUT 1\nLATE\n", b"")
    for kind in ("plain", "forward"):
        assert direct[("short-reader", "flood", kind)][2] == b"F" * _SHORT_READ
    assert direct[("fsize", "flood", "plain")][2] == b"F" * _FSIZE
    assert direct[("open-iso2022_jp", "non-ascii", "plain")][2] == b"\x1b$BF|"   # 停在双字节的状态、没有切换回 ASCII
    # 解释器在主模块结束与退出时各刷新一次两个流，logging 在 atexit 里另刷新一次 stderr：本工具多刷新一次或换掉了流，
    # 标记的个数或位置就不同
    assert direct[("open-utf-8", "0", "counting")] == (0, b"<o><o>", b"<e><e><e>")
    assert direct[("merged", "interleave", "counting")] == (3, b"ERR 1\nERR 2<e>OUT 1\n<o>LATE\n<e><o><e>", b"")


@pytest.mark.timeout(240)
def test_the_reports_are_written_whatever_the_command_does(pipe_results):
    """报告在命令返回或抛出之后写出：返回、SystemExit、未捕获异常、自定义 excepthook 与 atexit 回调的情形都有报告。文件
    大小限制的情形报告本身也写不完整，不在此列。"""
    import os

    _, _, reports = pipe_results
    expected = {"raise": "exception", "excepthook-big": "exception", "flood-raise": "exception",
                "exit9": "system_exit", "exit-str": "system_exit", "flood": "system_exit"}
    for case, (rep, js) in reports.items():
        if case[3] != "ok" or case[0] == "fsize":
            # 不可写的目录对 root 不起作用，那时报告照常写出
            assert not rep.exists() or case[0] == "fsize" or os.geteuid() == 0, case
            continue
        kind = "exception" if case[:2] == ("closed-stderr", "stderr-line") else expected.get(case[1], "returned")
        doc = json.loads(js.read_text(encoding="utf-8"))
        assert doc["argv"] == [case[1], case[2]] and doc["outcome"]["kind"] == kind, (case, doc["outcome"])
        lines = rep.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ddb_capacity.HEADER and lines[-1].startswith("  全部："), (case, lines)
