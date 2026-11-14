#!/usr/bin/env python
"""记录一条 gherkai 命令在本进程内发出的每个 DynamoDB 请求的读写消耗。

只记本进程发出、且响应里返回了消耗字段的请求的消耗：由这条命令触发、在别处执行的读写（云端推进用的 Lambda、ECS 上的
worker、命令拉起的子进程）不在其内；没有返回消耗字段的请求与失败的请求不当作零，逐条标出并在合计处注明有几条未计入。

用途
  在本进程内执行一条 gherkai 命令（与 `gherkai <参数…>` 同一个入口函数），给它发出的每个 DynamoDB 请求加上
  `ReturnConsumedCapacity=INDEXES`，逐条记下操作、表、索引名、Limit、返回条数与分页情况、表与各 GSI 的读写单位，末尾给合计。
  用来核对某条命令实际读了多少（例如 `list-runs` 一页读几次索引、各花多少读单位），给读量相关的设计取证。

用法（从仓库根执行，命令用仓库的 workspace venv）
  uv run python tools/ddb_capacity.py --report <路径> [--json <路径>] -- <gherkai 参数…>
  例：uv run python tools/ddb_capacity.py --report list-runs.txt --json list-runs.json -- list-runs --backend cloud --json
  `--` 之前是本工具的参数，之后原样交给 gherkai。--report 写人读的文本报告，--json 写机读的 JSON（逐条记录与合计，内容同
  文本报告），两者至少给一个，且不能指向同一个文件。下列情形本工具在执行命令之前以用法错误结束（打印用法，退出码 2），
  命令没有执行：
  - 缺 `--`，或 --report 与 --json 都不给；
  - 两个路径指向同一个文件：按所在目录的文件身份（设备号与 inode）加文件名比较，所以经符号链接的目录与目录别名（例如
    macOS 上的 /tmp 与 /private/tmp）都算同一个；
  - 报告路径不能作为普通文件写入：所在目录不存在（或不是目录），或路径上已有的不是普通文件（符号链接，含指向
    /dev/stderr 之类的符号链接；目录；设备，如 /dev/null；FIFO；socket），或路径本身无法检查；
  - 路径上已有的普通文件无法删除（例如所在目录不可写）：留着它，执行之后就分不清它是不是这一次写出的。

前置
  与被包裹的命令相同：它要连的后端与项目配置文件照常生效，凭证按 boto3 的常规解析链取，region 按被包裹命令自己的解析
  规则取（`--region` 参数、环境变量、项目配置文件与 profile 配置之间的优先级与直接执行这条命令时相同）；本工具不另读配置。
  只读命令与会写表的命令同样可用：本工具只加一个请求参数，不拦截、不重放、不改写任何请求。

输出去向
  报告只写进上面两个文件。从开始执行命令起直到进程退出，本工具不往 sys.stdout 与 sys.stderr 写任何内容，也不刷新、不替换
  它们，不碰它们的文件描述符。这样做是为了不改变被包裹命令的输出与结果：`… -- list-runs --json > runs.json` 得到的 JSON
  与直接执行 `gherkai <参数…>` 相同。自检用子进程逐项比较直接执行与经本工具执行的退出码、stdout 字节与 stderr 字节，
  比较过哪些情形以 `cli/tests/test_ddb_capacity.py` 里的 `_CASES` 为准（这里不另列，免得两处不一致）；没有比较过的环境
  不作保证。已知的差别见下「报告写不出时与局限」末段。
  文本报告的开头依次是标题「== DynamoDB 请求的读写消耗 ==」、被执行的 gherkai 参数、命令的结局（返回值、SystemExit 的值，
  或未捕获异常的类型）与一行记录范围的说明（见上），其后是逐条记录与合计（见「判读」）。JSON 里 argv 是 gherkai 参数，
  exit_code 是命令交给解释器的退出值（返回值或 SystemExit 的值，未捕获异常时为 null），outcome 是结局（kind 为
  returned、system_exit 或 exception，前两种带 value，最后一种带异常类型 type），requests 是逐条记录，totals 是合计。

报告写不出时与局限
  报告在命令返回或抛出之后写出。两份报告的内容来自同一份记录快照，截取时点是命令返回或抛出之后、写报告之前，所以两份
  报告的请求数与逐条内容一致。截取之后才完成的请求（命令返回时仍在别的线程里执行的请求）不在报告里；命令返回之后才发出
  的请求（atexit 回调、此后才发请求的线程）不经补丁，同样不在：补丁在命令返回时已还原。
  路径上已有的普通文件在命令开始执行之前删除（删除失败即上述用法错误），所以执行之后报告文件存在就说明它是这一次写出的
  （执行期间别人在这个路径上建出文件的情形除外，见下句），不存在说明没有写出。写入以独占创建、不跟随符号链接的方式打开文件：此时目标本应不存在，执行期间若有别人在这个路径上建出
  了文件、符号链接或 FIFO，本工具不覆盖它、不经它写到别处，按写不出处理。所以写入只会落在一个新建的普通文件里，不会落到
  设备、FIFO 或标准流上。
  写不出时（执行期间目录被删除、没有写权限、磁盘已满、超出文件大小限制、目标被抢先建出等）不改变命令的退出码与异常，也
  没有别处可以提示：本工具不用 stdout 与 stderr。两个报告各自写出，一个写不出不妨碍另一个。写到一半失败时文件不完整（文本
  报告的最后一行不是「全部」一行，JSON 不能解析）。
  进程被强制终止（SIGKILL、被外部超时杀掉）或经 os._exit 结束时没有报告。
  未捕获异常的 traceback 比直接执行时多出本工具的几层调用栈（本工具的入口与调用命令的那一层，DynamoDB 请求里抛出时另有
  补丁的那一层），最外层的文件名也不同；这是在同一个进程里包裹命令所致，异常本身与 traceback 末尾的类型和消息相同。
  同理，来源位置指向 gherkai 入口函数的调用方的警告（stacklevel 越过入口函数那一层）显示的是本工具的文件与行号。
  接收端容量有限时（只读若干字节就关闭的管道、文件大小限制、磁盘将满），多出的这几行可能恰好写不下：直接执行时写得下的
  traceback 经本工具执行时写不出，退出码由 1 变为 120。

判读
  文本报告里每行一个请求：序号、操作、表、索引（没有则为 -）、Limit、返回条数（Query / Scan 另给扫描条数与是否还有下一页）、
  消耗（表与每个 GSI 各自的读单位 R 与写单位 W）。合计按「表」与「表上的每个索引」分开累加，另给全部的读写单位总数。
  响应未完整细分、不带表本身那一项时（调用方自己给了 ReturnConsumedCapacity=TOTAL 时响应只有整体数字；服务端也可能
  只给部分索引的细目），表本身的消耗未知：逐条不给「表」一项，合计里这一条也不计入表本身；整体数字减去已报的索引之后
  的部分记为「未细分」，逐条与合计都单列，计在全部的读写里，因为它在表与各索引之间如何分摊是未知的。
  响应里只有 CapacityUnits、没有分读写时，按操作的性质归入读或写（GetItem / Query / Scan / BatchGetItem / TransactGetItems
  归读，其余归写；PartiQL 的 ExecuteStatement 等不按语句区分，一律归写）。
  合计只累加返回了消耗字段的请求，下面三种请求的消耗都不计入，「合计」一行分别给出三种的条数。前两种的消耗未知，
  「全部」一行另注明这两种共几条、各几条；不适用的请求没有读写单位可言，不在这一注明里：
  - 未返回消耗：操作带这个参数，响应里却没有消耗字段（调用方自己给了 ReturnConsumedCapacity=NONE，或服务端未给）。
    它的消耗未知，不是零。
  - 失败：请求抛出 ClientError 等，那一行记错误码（SDK 的参数校验错误记异常类名）。服务端可能已为它消耗了读写单位
    （例如条件不成立的写），错误响应不报告这一部分。参数形状不合法时本工具取不到的元数据（如表名）留空，取到的表名不是
    字符串时记为它的 repr 文本（例如 TableName=123 记为 123），索引名、Limit 等其它元数据不是字符串、数字或布尔值时同样
    记为 repr 文本，这样的请求照样出现在两份报告里；请求本身照常交给 SDK，由 SDK 报它自己的校验错误。表名、索引名等
    取自请求参数的字符串含换行等不可打印字符时，文本报告里记为 repr 文本（JSON 里保留原值），每个请求始终只占一行。
  - 不适用：操作本身没有这个参数（DescribeTable、ListTables 等控制面操作），不报告读写单位。

边界
  记的是这一次执行的读数：同一条命令再执行一次，表里的数据量、分页位置、最终一致读的取值都可能不同。只覆盖本进程里经
  botocore 发出的请求（含 boto3 resource 与各线程）；命令拉起的子进程、由命令触发的云端推进（Lambda）与 worker（ECS
  task）里的读写不在其内，例如 `submit` 之后推进 run 的那些写不会出现在 `submit` 的记录里。读写单位是
  DynamoDB 服务端按请求报告的值；按需计费模式下它就是计费的请求单位，预置容量模式下是消耗的容量单位。
  调用方没有自己要求 ReturnConsumedCapacity 时，本工具在把响应交还调用方之前删掉响应里的 ConsumedCapacity 字段，
  调用方看到的响应形态与不加参数时相同；调用方自己给了该参数时，原样保留它的取值与响应。
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import shlex
import stat
import sys
import threading
from collections import Counter
from pathlib import Path

import botocore.client

READ_OPS = frozenset({"GetItem", "BatchGetItem", "Query", "Scan", "TransactGetItems"})
HEADER = "== DynamoDB 请求的读写消耗 =="
SCOPE = ("（只含本进程发出的请求；由这条命令触发、在别处执行的读写，如云端推进用的 Lambda 与 worker，不在其内。"
         "合计只累加返回了消耗字段的请求）")


def _split_units(cap: dict | None, *, read_op: bool) -> tuple[float, float]:
    """一份 Capacity（表、某个索引或整体）的读写单位；只有 CapacityUnits 时按操作的性质归入读或写。"""
    if not cap:
        return 0.0, 0.0
    read, write = cap.get("ReadCapacityUnits"), cap.get("WriteCapacityUnits")
    if read is None and write is None:
        units = float(cap.get("CapacityUnits") or 0.0)
        return (units, 0.0) if read_op else (0.0, units)
    return float(read or 0.0), float(write or 0.0)


def _remainder(total: float, parts: float) -> float:
    """整体数字里没有归到任何细目的部分；浮点误差以内视为 0。"""
    rest = total - parts
    return rest if rest > 1e-9 else 0.0


def _capacity_entries(op: str, consumed) -> list[dict]:
    """把响应里的 ConsumedCapacity（单个对象或列表）拆成每张表一项：表本身、各索引与未细分部分的读写单位。

    响应带 Table 一项时，表与索引的数字即服务端给的细目。不带 Table 一项时（调用方自己要了 TOTAL，或服务端只报了索引），
    表本身的消耗未知：table_read / table_write 为 None（不是 0），整体数字减去已报的索引之后的余数记为「未细分」
    （unsplit_read / unsplit_write）；例如带 TOTAL 的 GSI 查询只有整体数字，全部记为未细分。"""
    entries = consumed if isinstance(consumed, list) else ([consumed] if consumed else [])
    read_op = op in READ_OPS
    out = []
    for c in entries:
        indexes = {}
        for key, kind in (("GlobalSecondaryIndexes", "gsi"), ("LocalSecondaryIndexes", "lsi")):
            for name, cap in (c.get(key) or {}).items():
                r, w = _split_units(cap, read_op=read_op)
                indexes[name] = {"kind": kind, "read": r, "write": w}
        total_r, total_w = _split_units(c, read_op=read_op)
        table_r: float | None
        table_w: float | None
        if "Table" in c:
            table_r, table_w = _split_units(c.get("Table"), read_op=read_op)
            unsplit_r = unsplit_w = 0.0
        else:
            table_r = table_w = None
            unsplit_r = _remainder(total_r, sum(u["read"] for u in indexes.values()))
            unsplit_w = _remainder(total_w, sum(u["write"] for u in indexes.values()))
        out.append({"table": c.get("TableName"), "read": total_r, "write": total_w,
                    "table_read": table_r, "table_write": table_w, "indexes": indexes,
                    "unsplit_read": unsplit_r, "unsplit_write": unsplit_w})
    return out


def _tables(params: dict) -> list[str]:
    """请求涉及的表名。参数在发出之前提取、尚未经 SDK 校验：形状不合法时可能抛出，调用方须容错（见 `_request_meta`）。"""
    if params.get("TableName"):
        return [params["TableName"]]
    names = list(params.get("RequestItems") or {})
    for item in params.get("TransactItems") or []:
        for body in item.values():
            if isinstance(body, dict) and body.get("TableName") and body["TableName"] not in names:
                names.append(body["TableName"])
    return names


def _result_counts(op: str, params: dict, resp: dict) -> dict:
    out: dict = {}
    if op in ("Query", "Scan"):
        # 按真值判断：空的 LastEvaluatedKey 表示结束（与 core 的 run_store 读分页的做法相同）
        out.update(count=resp.get("Count"), scanned=resp.get("ScannedCount"),
                   more=bool(resp.get("LastEvaluatedKey")))
    elif op == "GetItem":
        out["count"] = 1 if "Item" in resp else 0
    elif op == "BatchGetItem":
        out["keys"] = sum(len(v.get("Keys") or []) for v in (params.get("RequestItems") or {}).values())
        out["count"] = sum(len(v) for v in (resp.get("Responses") or {}).values())
        out["unprocessed"] = sum(len(v.get("Keys") or []) for v in (resp.get("UnprocessedKeys") or {}).values())
    elif op == "BatchWriteItem":
        out["requests"] = sum(len(v) for v in (params.get("RequestItems") or {}).values())
        out["unprocessed"] = sum(len(v) for v in (resp.get("UnprocessedItems") or {}).values())
    elif op == "TransactGetItems":
        out["count"] = sum(1 for r in resp.get("Responses") or [] if r.get("Item"))
    return out


def _repr_text(value) -> str:
    try:
        return repr(value)
    except Exception:
        return f"<{type(value).__name__}>"


def _plain(value):
    """元数据的一个值：None、字符串、数字与布尔值原样，其它（参数形状不合法时可能出现）记为 repr 文本，两份报告都能渲染。"""
    return value if value is None or isinstance(value, (str, int, float, bool)) else _repr_text(value)


def _request_meta(params: dict) -> dict:
    """一个请求的元数据（表、索引、Limit 等）。提取失败时（参数形状不合法，例如 TransactItems 里有 None）只记下能取到的
    部分，不抛出：请求照常交给 SDK，由 SDK 报它自己的参数校验错误。取到的表名一律是文本（不是字符串的记为 repr），
    文本报告拼接表名时因此不会失败。"""
    meta: dict = {"tables": []}
    with contextlib.suppress(Exception):
        meta["tables"] = [n if isinstance(n, str) else _repr_text(n) for n in _tables(params)]
    for key, field in (("index", "IndexName"), ("limit", "Limit"), ("consistent_read", "ConsistentRead"),
                       ("return_consumed_capacity", "ReturnConsumedCapacity")):
        meta[key] = _plain(params.get(field))
    return meta


class Recorder:
    """给本进程的 DynamoDB 请求加 ReturnConsumedCapacity 并逐条记下；`installed()` 期间生效，退出时还原。"""

    def __init__(self, mode: str = "INDEXES"):
        self.mode = mode
        self.records: list[dict] = []
        self._lock = threading.Lock()

    def _append(self, rec: dict) -> None:
        with self._lock:
            rec["seq"] = len(self.records) + 1
            self.records.append(rec)

    def snapshot(self) -> list[dict]:
        """此刻已记下的请求。别的线程里在途的请求之后仍可能追加记录，报告只用这样截取的一份，两份报告因此不会互相矛盾；
        每条记录在追加之前已经写全，之后不再改动，复制列表即可。"""
        with self._lock:
            return list(self.records)

    @contextlib.contextmanager
    def installed(self):
        original = botocore.client.BaseClient._make_api_call
        recorder = self

        def patched(client, operation_name, api_params):
            if client.meta.service_model.service_name != "dynamodb":
                return original(client, operation_name, api_params)
            shape = client.meta.service_model.operation_model(operation_name).input_shape
            supports = shape is not None and "ReturnConsumedCapacity" in shape.members
            added = supports and "ReturnConsumedCapacity" not in api_params
            params = {**api_params, "ReturnConsumedCapacity": recorder.mode} if added else api_params
            rec = {"op": operation_name, **_request_meta(params), "added_by_tool": added, "capacity_applicable": supports}
            try:
                resp = original(client, operation_name, params)
            except Exception as exc:
                code = None
                with contextlib.suppress(Exception):   # 取错误码不得抛出、盖掉原来的异常
                    code = exc.response["Error"]["Code"]
                rec["error"] = code if isinstance(code, str) and code else type(exc).__name__
                recorder._append(rec)
                raise
            with contextlib.suppress(Exception):   # 计数只是附带的元数据，取不到不影响交还响应
                rec.update(_result_counts(operation_name, params, resp))
            if supports:
                consumed = resp.get("ConsumedCapacity")
                if consumed:
                    rec["capacity"] = _capacity_entries(operation_name, consumed)
                else:
                    rec["capacity_missing"] = True   # 消耗未知，不当作零（见模块头「判读」）
            recorder._append(rec)
            if added:
                resp.pop("ConsumedCapacity", None)   # 调用方没有要这个字段：交还的响应与不加参数时形态相同
            return resp

        botocore.client.BaseClient._make_api_call = patched
        try:
            yield self
        finally:
            botocore.client.BaseClient._make_api_call = original


def _uncounted_kind(rec: dict) -> str | None:
    """这条请求为何不计入合计：failed / missing / not_applicable；返回了消耗字段的为 None。"""
    if "error" in rec:
        return "failed"
    if not rec.get("capacity_applicable", True):
        return "not_applicable"
    if not rec.get("capacity"):
        return "missing"
    return None


def totals(records: list[dict]) -> dict:
    """累加返回了消耗字段的请求：按表与表上的每个索引分开，另给全部的读写单位。未计入的请求按原因分开计数：
    失败（errors）、未返回消耗（without_capacity）、操作不适用（not_applicable）；counted 是计入合计的请求数。
    tables 只累加响应里带表本身那一项的请求（响应未完整细分、不带这一项的请求不计入，表本身的消耗未知）；unsplit 按表累加未细分的
    消耗（见 `_capacity_entries`），只列有未细分消耗的表；它计在全部的读写里，不计在表本身。"""
    tables: dict[str, dict] = {}
    indexes: dict[str, dict] = {}
    unsplit: dict[str, dict] = {}
    read = write = 0.0
    for rec in records:
        for c in rec.get("capacity") or []:
            name = c.get("table") or "?"
            if c["table_read"] is not None:
                t = tables.setdefault(name, {"read": 0.0, "write": 0.0})
                t["read"] += c["table_read"]
                t["write"] += c["table_write"]
            for idx, units in c["indexes"].items():
                i = indexes.setdefault(f"{name}/{idx}", {"kind": units["kind"], "read": 0.0, "write": 0.0})
                i["read"] += units["read"]
                i["write"] += units["write"]
            if c.get("unsplit_read") or c.get("unsplit_write"):
                u = unsplit.setdefault(name, {"read": 0.0, "write": 0.0})
                u["read"] += c.get("unsplit_read", 0.0)
                u["write"] += c.get("unsplit_write", 0.0)
            read += c["read"]
            write += c["write"]
    kinds = Counter(_uncounted_kind(r) for r in records)
    return {
        "requests": len(records),
        "by_op": dict(Counter(r["op"] for r in records)),
        "counted": kinds[None],
        "errors": kinds["failed"],
        "without_capacity": kinds["missing"],
        "not_applicable": kinds["not_applicable"],
        "tables": tables, "indexes": indexes, "unsplit": unsplit, "read": read, "write": write,
    }


def _fmt(x: float) -> str:
    return f"{x:g}"


def _cell(value):
    """文本报告里一项取自请求参数的值：含换行等不可打印字符的字符串记为 repr，每个请求才始终只占一行。"""
    return _repr_text(value) if isinstance(value, str) and not value.isprintable() else value


def _line(rec: dict) -> str:
    tables = ",".join(_cell(t) for t in rec["tables"])
    head = (f"#{rec['seq']} {rec['op']} {tables or '-'} index={_cell(rec.get('index')) or '-'}"
            f" Limit={_cell(rec.get('limit')) if rec.get('limit') is not None else '-'}")
    if "error" in rec:
        return f"{head} 失败 {_cell(rec['error'])}（消耗未知，未计入合计）"
    counts = []
    for key, label in (("count", "返回"), ("scanned", "扫描"), ("keys", "请求键"), ("requests", "写请求"),
                       ("unprocessed", "未处理")):
        if rec.get(key) is not None:
            counts.append(f"{label} {rec[key]}")
    if "more" in rec:
        counts.append("有下一页" if rec["more"] else "无下一页")
    caps = []
    for c in rec.get("capacity") or []:
        parts = [f"表 R{_fmt(c['table_read'])} W{_fmt(c['table_write'])}"] if c["table_read"] is not None else []
        parts += [f"{u['kind']} {idx} R{_fmt(u['read'])} W{_fmt(u['write'])}" for idx, u in c["indexes"].items()]
        if c.get("unsplit_read") or c.get("unsplit_write") or not parts:
            parts.append(f"未细分 R{_fmt(c.get('unsplit_read', 0.0))} W{_fmt(c.get('unsplit_write', 0.0))}")
        caps.append(f"{c.get('table') or '?'}：{'，'.join(parts)}")
    if caps:
        cap_text = "；".join(caps)
    elif _uncounted_kind(rec) == "not_applicable":
        cap_text = "不适用（该操作不报告读写单位）"
    else:
        cap_text = "未返回消耗（消耗未知，未计入合计）"
    return f"{head} | {'，'.join(counts) or '-'} | {cap_text}"


def report(records: list[dict], out, preamble: tuple[str, ...] = ()) -> dict:
    """把标题、preamble 各行、范围说明、逐条记录与合计写进 out，返回合计。"""
    agg = totals(records)
    print(HEADER, file=out)
    for line in preamble:
        print(line, file=out)
    print(SCOPE, file=out)
    for rec in records:
        print(_line(rec), file=out)
    ops = "、".join(f"{op} {n}" for op, n in sorted(agg["by_op"].items())) or "无"
    print(f"合计：请求 {agg['requests']} 个（{ops}），计入合计 {agg['counted']} 个，失败 {agg['errors']} 个，"
          f"未返回消耗 {agg['without_capacity']} 个，不适用 {agg['not_applicable']} 个", file=out)
    for name, t in sorted(agg["tables"].items()):
        print(f"  表 {name}：读 {_fmt(t['read'])}，写 {_fmt(t['write'])}", file=out)
    for name, i in sorted(agg["indexes"].items()):
        print(f"  {i['kind']} {name}：读 {_fmt(i['read'])}，写 {_fmt(i['write'])}", file=out)
    for name, u in sorted(agg["unsplit"].items()):
        print(f"  未细分 {name}：读 {_fmt(u['read'])}，写 {_fmt(u['write'])}（响应未完整细分，这部分在表与各索引之间如何分摊未知）",
              file=out)
    uncounted = agg["errors"] + agg["without_capacity"]
    note = (f"（另有 {uncounted} 个请求的消耗未知、未计入：失败 {agg['errors']} 个，未返回消耗 {agg['without_capacity']} 个）"
            if uncounted else "")
    print(f"  全部：读 {_fmt(agg['read'])}，写 {_fmt(agg['write'])}{note}", file=out)
    return agg


def _type_name(exc: BaseException) -> str:
    t = type(exc)
    return t.__qualname__ if t.__module__ == "builtins" else f"{t.__module__}.{t.__qualname__}"


def _outcome_text(outcome: dict) -> str:
    if outcome["kind"] == "returned":
        return f"返回 {outcome['value']!r}"
    if outcome["kind"] == "system_exit":
        return f"SystemExit，值为 {outcome['value']!r}"
    return f"未捕获的异常 {outcome['type']}"


def text_report(records: list[dict], argv: list[str], outcome: dict) -> str:
    """文本报告的全文：标题、gherkai 参数、结局，其后同 `report`。"""
    buf = io.StringIO()
    report(records, buf, (f"命令：{shlex.join(['gherkai', *argv])}", f"结局：{_outcome_text(outcome)}"))
    return buf.getvalue()


def json_report(records: list[dict], argv: list[str], outcome: dict) -> str:
    return json.dumps({"argv": argv, "exit_code": outcome.get("value"), "outcome": outcome, "requests": records,
                       "totals": totals(records)}, ensure_ascii=False, indent=1, default=str)


def _check_target(path: Path) -> tuple[str | None, tuple | None, bool]:
    """检查一个报告路径能否作为普通文件写入，返回（问题，目标的身份，路径上是否已有普通文件）；没有问题时问题为 None。

    目标的身份是所在目录的设备号与 inode 加文件名：符号链接与目录别名在比较目录身份时都已解析掉。路径上已有的
    必须是普通文件且不是符号链接，所在目录必须存在；写入时另以独占创建、不跟随符号链接的方式打开（见 `_create_and_write`），
    这里的检查让不合规的目标在执行命令之前以用法错误结束。"""
    try:
        st = os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        st = None
    except OSError as exc:
        return f"无法检查这个路径（{exc.strerror}）", None, False
    if st is not None and stat.S_ISLNK(st.st_mode):
        return "是符号链接，报告只写进普通文件", None, False
    if st is not None and not stat.S_ISREG(st.st_mode):
        return "已存在且不是普通文件（例如目录、设备或 FIFO），报告只写进普通文件", None, False
    try:
        parent = os.stat(path.parent)
    except OSError:
        parent = None
    if parent is None or not stat.S_ISDIR(parent.st_mode):
        return "所在的目录不存在", None, False
    return None, (parent.st_dev, parent.st_ino, path.name), st is not None


def _prepare_targets(parser: argparse.ArgumentParser, targets: list[tuple[str, Path]]) -> None:
    """命令开始执行之前：逐个检查报告路径、确认两者不是同一个文件，再删掉路径上已有的普通文件。报告写不出时没有别处可以
    提示，执行之后文件存在才能说明它是这一次写出的，所以无法删除也是用法错误。任一项不通过都经 parser.error 结束。"""
    existing: list[tuple[str, Path]] = []
    identities: dict[tuple, str] = {}
    for option, path in targets:
        problem, identity, exists = _check_target(path)
        if problem is not None:
            parser.error(f"{option} {path}：{problem}")
        if identity in identities:
            parser.error(f"{identities[identity]} 与 {option} 指向同一个文件，两个报告须写进不同的文件")
        identities[identity] = option
        if exists:
            existing.append((option, path))
    for option, path in existing:
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            parser.error(f"{option} {path}：已有的文件无法删除（{exc.strerror}），留着它就分不清报告是不是这一次写出的")


# 独占创建（O_CREAT | O_EXCL）：路径上已有任何东西（文件、符号链接、FIFO、设备）时打开失败，不覆盖、不跟随；O_NOFOLLOW
# 在独占创建之外再保证不经符号链接打开
_CREATE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


def _create_and_write(path: Path, text: str) -> None:
    data = text.encode("utf-8")
    fd = os.open(path, _CREATE_FLAGS, 0o666)
    try:
        f = open(fd, "wb")
    except BaseException:
        os.close(fd)
        raise
    with f:
        f.write(data)


def _write_reports(records: list[dict], argv: list[str], outcome: dict,
                   report_path: Path | None, json_path: Path | None) -> None:
    """两个报告各自生成并写出，任一步失败都不抛出、不提示（不用 stdout 与 stderr），也不妨碍另一个。"""
    for path, render in ((report_path, text_report), (json_path, json_report)):
        if path is None:
            continue
        with contextlib.suppress(Exception):
            _create_and_write(path, render(records, argv, outcome))


def main(argv: list[str] | None = None) -> int | str | None:
    """执行 `--` 之后的 gherkai 命令：返回它的返回值，或原样抛出它抛出的 SystemExit 与异常；报告在此之后写出。

    用法错误只在执行命令之前出现（argparse 打印用法、以 SystemExit(2) 结束）。从执行命令起本函数不碰 sys.stdout 与
    sys.stderr（见模块头「输出去向」）。"""
    argv = list(sys.argv[1:] if argv is None else argv)
    sep = argv.index("--") if "--" in argv else len(argv)
    parser = argparse.ArgumentParser(
        prog="ddb_capacity.py", usage="%(prog)s --report <路径> [--json <路径>] -- <gherkai 参数…>",
        description="记录一条 gherkai 命令发出的 DynamoDB 请求的读写消耗，报告只写进文件")
    parser.add_argument("--report", type=Path, help="把人读的文本报告写进这个文件")
    parser.add_argument("--json", type=Path, help="把逐条记录与合计写进这个 JSON 文件")
    ns = parser.parse_args(argv[:sep])
    if sep == len(argv):
        parser.error("gherkai 的参数写在 -- 之后")
    if ns.report is None and ns.json is None:
        parser.error("--report 与 --json 至少给一个：报告只写进文件，不输出到 stdout 或 stderr")
    _prepare_targets(parser, [(option, path) for option, path in (("--report", ns.report), ("--json", ns.json))
                              if path is not None])
    gherkai_argv = argv[sep + 1:]

    recorder = Recorder()
    outcome: dict = {"kind": "exception", "type": None}
    try:
        with recorder.installed():
            gherkai_main = importlib.import_module("gherkai_cli.__main__").main
            code = gherkai_main(gherkai_argv)
        outcome = {"kind": "returned", "value": code}
        return code
    except SystemExit as exc:
        outcome = {"kind": "system_exit", "value": exc.code}
        raise
    except BaseException as exc:
        outcome = {"kind": "exception", "type": _type_name(exc)}
        raise
    finally:
        # 两份报告都用这一份快照：此后才完成的请求不在报告里（见模块头「报告写不出时与局限」）
        _write_reports(recorder.snapshot(), gherkai_argv, outcome, ns.report, ns.json)


if __name__ == "__main__":
    sys.exit(main())
