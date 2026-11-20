"""DynamoDBRunStore 对拍测试（ADR 0030 决定六）：与 LocalRunStore 同一批行为断言，moto mock、不产生真实 AWS 费用。

对拍的是**后端无关的行为契约**（create/load round-trip、实时写生命周期、Map 单元素刷、未 create 报错、
omit-null 时间戳）——即 test_stores.py 里 LocalRunStore 那批。物理落点断言（文件存在/JSON 是 list）是
Local 专属、不在此。复用 test_stores 的 _sample_run/_initial_state 造数据。文末另有 DDB 一侧才有的两项：jobs Map 条目里点名标识的
键，以及终态写被写入序号挡下、重读再算时点名的仍是同一个标识。
"""
from __future__ import annotations

import json

import pytest

from gherkai_core.model import JobState, Status
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from tests.test_stores import _initial_state, _sample_run


# ---- create/load round-trip（对拍 test_run_store_create_load）----
def test_create_load_round_trip(ddb_run_store):
    r = _sample_run("run-1")
    ddb_run_store.create_run(r.run_meta, r.state)

    # definition 读回
    meta = ddb_run_store.load_run_meta("run-1")
    assert meta is not None and meta.run_id == "run-1" and meta.created_at == "2026-06-29T00:00:00Z"
    assert len(meta.jobs) == 2 and meta.jobs[0].scope_id == "features/wiki.feature:6"
    # definition 深树完整重建（含 assertion_votes 非默认值）
    assert meta.jobs[0].scenarios[0].steps[1].text == "搜索 OpenAI"
    assert meta.jobs[0].assertion_votes == 3

    # 运行态读回（jobs 是 Map，按 scope_id 取）
    state = ddb_run_store.load_run_state("run-1")
    assert state is not None and state.status == Status.FAILED
    j0 = state.jobs["features/wiki.feature:6"]
    j1 = state.jobs["登录场景"]
    assert j0.status == Status.PASSED and j0.session_id == "sess-1"
    assert j1.status == Status.FAILED


def test_load_missing_returns_none(ddb_run_store):
    assert ddb_run_store.load_run_meta("nope") is None
    assert ddb_run_store.load_run_state("nope") is None


def test_run_meta_deep_argument_round_trip(ddb_run_store):
    # META 存 JSON 字符串——含 docString/dataTable（含空 cell）的深 Job 树要逐字节还原。
    # 这是 StepArgument offload（ADR 0030 决定六）必须保持的基线：不 offload 时 argument 内容原样往返。
    from gherkai_core.model import Job, RunMeta, RunState, Scenario, Step, StepArgument, Status

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("k", "v"), ("", "空cell")))),
            Step(1, "Then", "看结果", StepArgument(kind="docString", content="多行\n内容\ns3://像指针的正文")),
        )),
    ), timeout_s=300.0)
    meta = RunMeta(run_id="deep", created_at="t", jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00")
    ddb_run_store.create_run(meta, RunState(run_id="deep", status=Status.PENDING, jobs={}))

    got = ddb_run_store.load_run_meta("deep")
    arg0 = got.jobs[0].scenarios[0].steps[0].argument
    arg1 = got.jobs[0].scenarios[0].steps[1].argument
    assert arg0.kind == "dataTable" and arg0.rows == (("k", "v"), ("", "空cell"))  # 空 cell 保留
    assert arg1.kind == "docString" and arg1.content == "多行\n内容\ns3://像指针的正文"  # 含 s3:// 正文原样


# ---- 实时写生命周期（对拍 test_realtime_write_lifecycle）----
def test_realtime_write_lifecycle(ddb_run_store):
    meta = _sample_run("rt-run").run_meta
    scope_ids = ["features/wiki.feature:6", "登录场景"]

    # 1) 开始：全 pending
    ddb_run_store.create_run(meta, _initial_state("rt-run", scope_ids))
    s0 = ddb_run_store.load_run_state("rt-run")
    assert s0 is not None and s0.status == Status.PENDING
    assert all(js.status == Status.PENDING for js in s0.jobs.values())
    assert ddb_run_store.load_run_meta("rt-run") is not None  # definition 也落了

    # 2) 一个 job 开始运行 → running（带血缘）；中途读到部分完成态（Map 单元素刷不互相污染）
    ddb_run_store.update_job_state("rt-run", JobState("features/wiki.feature:6", Status.RUNNING, session_id="sess-1"))
    mid = ddb_run_store.load_run_state("rt-run")
    assert mid.jobs["features/wiki.feature:6"].status == Status.RUNNING
    assert mid.jobs["features/wiki.feature:6"].session_id == "sess-1"
    assert mid.jobs["登录场景"].status == Status.PENDING   # 另一个没动
    assert mid.status == Status.RUNNING                      # job 记为 running 时 run 级随之为 running

    # 3) 第一个 job 完成：终态写记下它，run 仍 running、没有结束时刻
    assert ddb_run_store.commit_job_states(
        "rt-run", [JobState("features/wiki.feature:6", Status.PASSED, session_id="sess-1")],
        ended_at="2026-07-01T00:04:00Z") is CommitOutcome.OPEN
    s2 = ddb_run_store.load_run_state("rt-run")
    assert s2.jobs["features/wiki.feature:6"].status == Status.PASSED
    assert (s2.status, s2.ended_at) == (Status.RUNNING, None)

    # 4) 最后一个 job 完成：这次终态写使 run 成为终态，run 状态按取法写下，同一次写下结束时刻；各 job 态保留
    assert ddb_run_store.commit_job_states("rt-run", [JobState("登录场景", Status.FAILED)],
                                           ended_at="2026-07-01T00:05:00Z") is CommitOutcome.ENDED_RUN
    final = ddb_run_store.load_run_state("rt-run")
    assert final.status == Status.FAILED
    assert final.ended_at == "2026-07-01T00:05:00Z"
    assert final.started_at == "2026-07-01T00:00:00Z"  # create_run 填的起点保留
    assert final.jobs["features/wiki.feature:6"] == JobState("features/wiki.feature:6", Status.PASSED, session_id="sess-1")
    assert final.jobs["登录场景"].status == Status.FAILED


def test_writes_before_create_raise_or_write_nothing(ddb_run_store):
    # 未 create_run 就写 → 执行中的写与终态写报错（对拍 local：条件不成立且带回的条目为空 → FileNotFoundError）；结束写写不成；
    # 都不臆造 STATE
    with pytest.raises(FileNotFoundError):
        ddb_run_store.update_job_state("nope", JobState("s", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        ddb_run_store.commit_job_states("nope", [JobState("s", Status.PASSED)], ended_at="t")
    assert ddb_run_store.end_run("nope", RUN_ENDINGS["deadline"], ended_at="t") is False
    assert ddb_run_store.load_run_state("nope") is None


def test_session_id_none_omitted_and_roundtrips(ddb_run_store):
    # session_id=None：omit-when-None（不写该键），读回仍 None（对拍 local/serialize 语义）
    meta = _sample_run("s-run").run_meta
    ddb_run_store.create_run(meta, _initial_state("s-run", ["features/wiki.feature:6", "登录场景"]))
    assert ddb_run_store.update_job_state("s-run", JobState("登录场景", Status.RUNNING, session_id=None)) is True
    js = ddb_run_store.load_run_state("s-run").jobs["登录场景"]
    assert js.status == Status.RUNNING and js.session_id is None


def test_started_ended_omit_when_none_round_trip(ddb_run_store):
    # 起止为 None 时不写、读回仍 None；非 None 时完整保留（对拍 test_run_state_omits/timestamps）
    meta = _sample_run("ts-run").run_meta
    # 初始态 started 填、ended 缺
    ddb_run_store.create_run(meta, _initial_state("ts-run", ["s"]))
    got = ddb_run_store.load_run_state("ts-run")
    assert got.started_at == "2026-07-01T00:00:00Z" and got.ended_at is None
    # 使 run 成为终态的那次写之后 ended 出现
    assert ddb_run_store.commit_job_states("ts-run", [JobState("s", Status.PASSED)],
                                           ended_at="2026-07-01T01:00:00Z") is CommitOutcome.ENDED_RUN
    got2 = ddb_run_store.load_run_state("ts-run")
    assert got2.ended_at == "2026-07-01T01:00:00Z"


def test_detached_flag_on_state_item(aws):
    """detached 组合根的 create_run 在 STATE item 落 detached=true 标记;默认(同步 run)不落。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

    def _mk(run_id):
        job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(
            Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
        meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00")
        state = RunState(run_id=run_id, status=Status.PENDING,
                         jobs={"s": JobState("s", Status.PENDING)}, started_at="t")
        return meta, state

    table = aws["ddb"].Table(aws["table_name"])
    meta, state = _mk("det-1")
    DynamoDBRunStore(table, detached=True).create_run(meta, state)
    item = table.get_item(Key={"run_id": "det-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item.get("detached") is True  # kicker filter 匹配 {"BOOL": true}

    meta, state = _mk("sync-1")
    DynamoDBRunStore(table).create_run(meta, state)  # 同步 run 组合根:默认不带
    item = table.get_item(Key={"run_id": "sync-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert "detached" not in item  # 属性缺席 → Stream filter 不命中 → kicker 不触发

    # 只读访问器（推进器 handler 侧分流用它）:读同一个标记,未知 run 保守判 False
    reader = DynamoDBRunStore(table)
    assert reader.is_detached("det-1") is True
    assert reader.is_detached("sync-1") is False
    assert reader.is_detached("没这个 run") is False


def test_worker_task_def_arns_on_state_item(aws):
    """create_run 把 definition 的 worker revision ARN 摊平成 STATE 顶层属性（ADR 0038 清理 pass 的运行中 run 引用检查）。

    为什么必须摊平：同一批 ARN 也在 definition 里，但那在 META 的 `meta_json` 字符串内、DDB 查不动；清理 pass
    要按 `status` GSI Query 非终态 run + `contains` 过滤引用，只有顶层属性做得到（沿用 `detached` 顶层标记先例）。
    未设 → 属性缺席（`contains` 对缺属性天然不匹配，语义即「未引用」）——不落空 list。
    """
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

    # 属性名写死在此（**不 import `gherkai_runtime.names`**：core 是窄腰下层，其测试也不该反向依赖组合根
    # 共享层）。与读端命名真源 `names.STATE_WORKER_TASK_DEF_ARNS_ATTR` 的逐字一致由 runtime 侧的对拍测试
    # `runtime/tests/test_names_worker.py` 守——那里能同时看见两边。
    ATTR = "worker_task_def_arns"

    def _mk(run_id, worker_task_defs=None):
        job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(
            Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
        meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,),
                       worker_task_defs=worker_task_defs, deadline_at="2026-01-01T01:00:00+00:00")
        state = RunState(run_id=run_id, status=Status.PENDING,
                         jobs={"s": JobState("s", Status.PENDING)}, started_at="t")
        return meta, state

    table = aws["ddb"].Table(aws["table_name"])
    nova = "arn:aws:ecs:us-east-1:1:task-definition/gherkai-novaact-worker:7"
    mid = "arn:aws:ecs:us-east-1:1:task-definition/gherkai-midscene-worker:3"
    meta, state = _mk("wk-1", {"novaact": nova, "midscene": mid})
    DynamoDBRunStore(table).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-1", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item[ATTR] == sorted([nova, mid])  # list of ARN、稳定排序（item 可比对）

    # 两引擎共用同一 revision（同一 variant 名跨引擎、极端下 ARN 相同）→ 去重，不留重复项
    meta, state = _mk("wk-dup", {"novaact": nova, "midscene": nova})
    DynamoDBRunStore(table).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-dup", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item[ATTR] == [nova]

    # 旧 definition / 本机后端（无该字段）→ 属性缺席
    meta, state = _mk("wk-none")
    DynamoDBRunStore(table).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-none", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert ATTR not in item


# ---- definition 结构版本摊成 META 顶层属性 + 轻量读头（ADR 0037 决策 7）----
def test_meta_item_carries_schema_header_top_level_and_peek_reads_only_it(ddb_run_store):
    import dataclasses

    from gherkai_core.errors import UnsupportedDefinitionSchema
    r = _sample_run("hdr")
    ddb_run_store.create_run(dataclasses.replace(r.run_meta, cli_version="1.5.0"), r.state)
    assert ddb_run_store.peek_definition_header("hdr") == (2, "1.5.0")
    assert ddb_run_store.peek_definition_header("nope") is None
    raw = ddb_run_store._table.get_item(Key={"run_id": "hdr", "item_type": "META"})["Item"]
    assert int(raw["schema_version"]) == 2 and raw["cli_version"] == "1.5.0"   # 顶层属性与 meta_json 同值
    # 运行期限同样摊成顶层属性（ADR 0054 决策二），值与 meta_json 里的同名键恒同，读回的 definition 也带着它
    assert raw["deadline_at"] == json.loads(raw["meta_json"])["deadline_at"] == r.run_meta.deadline_at
    assert ddb_run_store.load_run_meta("hdr").deadline_at == r.run_meta.deadline_at
    # 没有顶层属性的 META（早于结构版本号的写端）：读头得 (0, None)，整读按版本不符拒绝
    ddb_run_store._table.put_item(Item={"run_id": "old", "item_type": "META",
                                        "meta_json": '{"run_id": "old", "created_at": "", "jobs": []}'})
    assert ddb_run_store.peek_definition_header("old") == (0, None)
    with pytest.raises(UnsupportedDefinitionSchema):
        ddb_run_store.load_run_meta("old")


@pytest.mark.parametrize("bad", ["1", True], ids=["string", "bool"])
def test_peek_rejects_non_integer_schema_attribute(ddb_run_store, bad):
    from gherkai_core.errors import DefinitionContractError

    ddb_run_store._table.put_item(Item={"run_id": "weird", "item_type": "META", "schema_version": bad, "meta_json": "{}"})
    with pytest.raises(DefinitionContractError, match="schema_version 须为整数"):
        ddb_run_store.peek_definition_header("weird")


def test_peek_rejects_fractional_and_accepts_integral_decimal(ddb_run_store):
    from decimal import Decimal

    from gherkai_core.errors import DefinitionContractError

    ddb_run_store._table.put_item(Item={"run_id": "frac", "item_type": "META", "schema_version": Decimal("1.9"), "meta_json": "{}"})
    with pytest.raises(DefinitionContractError):
        ddb_run_store.peek_definition_header("frac")
    ddb_run_store._table.put_item(Item={"run_id": "whole", "item_type": "META", "schema_version": Decimal("1"), "cli_version": "1.5.0", "meta_json": "{}"})
    assert ddb_run_store.peek_definition_header("whole") == (1, "1.5.0")


def test_load_run_meta_checks_schema_before_restoring_offloaded_arguments(ddb_run_store_offload):
    """版本核对先于参数还原：别的版本写出的 META 不该先在还原遍历里抛 KeyError（那会绕过读端按版本不合的处置）。"""
    from gherkai_core.errors import DefinitionContractError, UnsupportedDefinitionSchema

    ddb_run_store_offload._table.put_item(Item={"run_id": "future", "item_type": "META", "schema_version": 3,
                                                "meta_json": '{"schema_version": 3, "jobs": [{"scenarios": [{"steps": [{"argument": {"kind": "docString", "content_ref": "s3://b/k"}}]}]}]}'})
    with pytest.raises(UnsupportedDefinitionSchema):
        ddb_run_store_offload.load_run_meta("future")
    # 同版本下还原遍历撞到的形状错归定义违约，不漏 KeyError
    ddb_run_store_offload._table.put_item(Item={"run_id": "malformed", "item_type": "META", "schema_version": 2,
                                                "meta_json": '{"schema_version": 2, "jobs": [{"scenarios": [{"steps": [{"argument": {"kind": "docString", "content_ref": "s3://b/k"}}]}]}]}'})
    with pytest.raises(DefinitionContractError):
        ddb_run_store_offload.load_run_meta("malformed")


def test_load_run_meta_lets_fetch_failures_through_untranslated(ddb_run_store_offload):
    """S3 取回失败不是定义违约（ADR 0037 决策 7 的读端边界）：指针指向不存在的桶时原样抛 botocore 异常——可重试的故障不该被读端永久标成 error。"""
    from botocore.exceptions import ClientError

    ddb_run_store_offload._table.put_item(Item={"run_id": "gone", "item_type": "META", "schema_version": 2,
                                                "meta_json": '{"schema_version": 2, "jobs": [{"scope_id": "s", "scenarios": [{"id": "sc", "steps": '
                                                             '[{"index": 0, "argument": {"kind": "docString", "content_ref": "s3://no-such-bucket-gherkai-x/k"}}]}]}]}'})
    with pytest.raises(ClientError):
        ddb_run_store_offload.load_run_meta("gone")


# ---- 建 run 只在 run 不存在时成立（ADR 0054 决策五）：两个条目与已卸载的正文都不被重写 ----
def _doc_meta(run_id: str, content: str, *, extra_scope: bool = False):
    """带 docString 的 definition：挂 offloader 时正文卸载到 S3。同一 run_id 下换 content 再建，若被重写，同一 key 的正文就会变；
    extra_scope 再多一个 scope，若被重写会多出一个对象。"""
    from gherkai_core.model import Job, RunMeta, RunState, Scenario, Step, StepArgument

    def job(scope_id):
        return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", timeout_s=300.0, scenarios=(
            Scenario(id=f"{scope_id}:1", name="sc", steps=(
                Step(0, "Then", "看结果", StepArgument(kind="docString", content=content)),)),))
    jobs = (job("s"), job("t")) if extra_scope else (job("s"),)
    meta = RunMeta(run_id=run_id, created_at="t", jobs=jobs, deadline_at="2026-01-01T01:00:00+00:00")
    state = RunState(run_id=run_id, status=Status.PENDING, started_at="t",
                     jobs={j.scope_id: JobState(j.scope_id, Status.PENDING) for j in jobs})
    return meta, state


def _snapshot(aws, run_id: str) -> tuple[dict | None, dict | None, dict[str, bytes]]:
    """库中原样：META item、STATE item 与桶里全部对象（key → 正文）。"""
    table = aws["ddb"].Table(aws["table_name"])
    items = tuple(table.get_item(Key={"run_id": run_id, "item_type": t}, ConsistentRead=True).get("Item")
                  for t in ("META", "STATE"))
    s3 = aws["s3"]
    objects = {o["Key"]: s3.get_object(Bucket=aws["bucket"], Key=o["Key"])["Body"].read()
               for o in s3.list_objects_v2(Bucket=aws["bucket"]).get("Contents", [])}
    return items[0], items[1], objects


def test_create_run_on_existing_run_rewrites_neither_item_nor_offloaded_content(aws, ddb_run_store_offload):
    """对已有的 run 再建：抛 FileExistsError，META、STATE 与已卸载到 S3 的正文都不变，也不多出对象。再建时给的 definition
    正文不同、scope 更多，被重写就一定看得出来。"""
    meta, state = _doc_meta("dup", "第一版正文")
    ddb_run_store_offload.create_run(meta, state)
    assert ddb_run_store_offload.try_claim_job("dup", "s") is True
    before = _snapshot(aws, "dup")
    assert before[0] is not None and before[1] is not None and len(before[2]) == 1, "前提：两个条目与一个卸载对象都在"

    meta2, state2 = _doc_meta("dup", "第二版正文", extra_scope=True)
    with pytest.raises(FileExistsError):
        ddb_run_store_offload.create_run(meta2, state2)
    assert _snapshot(aws, "dup") == before
    assert ddb_run_store_offload.load_run_meta("dup").jobs[0].scenarios[0].steps[0].argument.content == "第一版正文"


@pytest.mark.parametrize("present", ["META", "STATE"])
def test_create_run_fails_when_either_item_already_exists(aws, ddb_run_store_offload, present):
    """只有 META 或只有 STATE 在（建 run 在两次写之间中断，或另一个写入方只写了其中一条）同样算已存在：失败、已在的那条不变、
    缺的那条仍缺、不卸载任何正文。"""
    table = aws["ddb"].Table(aws["table_name"])
    meta, state = _doc_meta("half", "正文")
    ddb_run_store_offload.create_run(meta, state)
    table.delete_item(Key={"run_id": "half", "item_type": "STATE" if present == "META" else "META"})
    for o in aws["s3"].list_objects_v2(Bucket=aws["bucket"]).get("Contents", []):
        aws["s3"].delete_object(Bucket=aws["bucket"], Key=o["Key"])
    before = _snapshot(aws, "half")

    with pytest.raises(FileExistsError):
        ddb_run_store_offload.create_run(*_doc_meta("half", "另一份正文"))
    assert _snapshot(aws, "half") == before
    assert before[2] == {}


def test_create_run_reads_strongly_consistently_before_offloading(aws, ddb_run_store_offload, monkeypatch):
    """存在性检查在卸载正文之前、且是强一致读：两次读（META、STATE）都排在第一次 S3 写之前，都带 ConsistentRead。"""
    order: list[str] = []
    table = ddb_run_store_offload._table
    real_get, real_put = table.get_item, aws["s3"].put_object

    def get_item(**kwargs):
        order.append(f"get {kwargs['Key']['item_type']} consistent={kwargs.get('ConsistentRead')}")
        return real_get(**kwargs)

    def put_object(**kwargs):
        order.append("s3 put")
        return real_put(**kwargs)

    monkeypatch.setattr(table, "get_item", get_item)
    monkeypatch.setattr(aws["s3"], "put_object", put_object)
    ddb_run_store_offload.create_run(*_doc_meta("ord", "正文"))
    assert order == ["get META consistent=True", "get STATE consistent=True", "s3 put"]


def test_create_run_puts_are_conditional_when_another_writer_lands_after_the_check(aws, ddb_run_store_offload, monkeypatch):
    """检查与写之间另一方建了同一个 run_id（这里让检查读不到已有的条目来造出这个窗口）：两次 put 的「条目不存在」条件挡下本方，
    抛 FileExistsError，META 与 STATE 仍是先建的那一方的内容。这个窗口里 S3 正文可能已被本方重写，属已知边界、不断言。"""
    meta, state = _doc_meta("race", "先到的正文")
    ddb_run_store_offload.create_run(meta, state)
    table = aws["ddb"].Table(aws["table_name"])
    meta_before, state_before = (table.get_item(Key={"run_id": "race", "item_type": t}, ConsistentRead=True)["Item"]
                                 for t in ("META", "STATE"))

    monkeypatch.setattr(ddb_run_store_offload._table, "get_item", lambda **kwargs: {})
    with pytest.raises(FileExistsError):
        ddb_run_store_offload.create_run(*_doc_meta("race", "后到的正文", extra_scope=True))
    monkeypatch.undo()
    assert table.get_item(Key={"run_id": "race", "item_type": "META"}, ConsistentRead=True)["Item"] == meta_before
    assert table.get_item(Key={"run_id": "race", "item_type": "STATE"}, ConsistentRead=True)["Item"] == state_before


def test_create_run_state_put_is_conditional_on_its_own(aws, ddb_run_store_offload, monkeypatch):
    """STATE 那一次写自己带「条目不存在」的条件：让检查读不到已有的条目、META 又不在（META 的写因此成立），本方走到第二次写，
    已有的 STATE 挡下它，抛 FileExistsError，STATE 仍是原来的内容（含已有的认领）。上一条用例在 META 的写上就被挡下，
    走不到这一次写。"""
    meta, state = _doc_meta("race2", "先到的正文")
    ddb_run_store_offload.create_run(meta, state)
    assert ddb_run_store_offload.try_claim_job("race2", "s") is True
    table = aws["ddb"].Table(aws["table_name"])
    table.delete_item(Key={"run_id": "race2", "item_type": "META"})
    state_before = table.get_item(Key={"run_id": "race2", "item_type": "STATE"}, ConsistentRead=True)["Item"]

    puts: list[str] = []
    real_put = ddb_run_store_offload._table.put_item

    def put_item(**kwargs):
        puts.append(kwargs["Item"]["item_type"])
        return real_put(**kwargs)

    monkeypatch.setattr(ddb_run_store_offload._table, "get_item", lambda **kwargs: {})
    monkeypatch.setattr(ddb_run_store_offload._table, "put_item", put_item)
    with pytest.raises(FileExistsError):
        ddb_run_store_offload.create_run(*_doc_meta("race2", "后到的正文", extra_scope=True))
    monkeypatch.undo()
    assert puts == ["META", "STATE"], "前提：这一次确实走到了 STATE 的写"
    assert table.get_item(Key={"run_id": "race2", "item_type": "STATE"}, ConsistentRead=True)["Item"] == state_before


def test_create_run_writes_claim_count_zero_on_the_state_item(aws, ddb_run_store):
    """STATE item 写下认领计数 0（写端恒写，数值属性）。"""
    meta, state = _doc_meta("cc", "正文")
    ddb_run_store.create_run(meta, state)
    item = aws["ddb"].Table(aws["table_name"]).get_item(Key={"run_id": "cc", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert item["claim_count"] == 0


# ---- 点名的标识（ADR 0030 决定三「点名」条）：jobs Map 条目里的键，与重读再算时的沿用 ----
def test_job_entries_carry_result_id_only_when_named(aws, ddb_run_store):
    """STATE 的 jobs Map 里，被点名的 job 的条目带 `result_id`，没被点名的（未结束、由结束写结束）省键；读回与写下的标识相同。读原始
    STATE，不经 load_run_state。"""
    meta = _sample_run("rid-run").run_meta
    sid0, sid1 = (j.scope_id for j in meta.jobs)
    ddb_run_store.create_run(meta, _initial_state("rid-run", [sid0, sid1]))
    assert ddb_run_store.try_claim_job("rid-run", sid0, claimed_at="2026-07-01T00:01:00Z") is True
    assert ddb_run_store.commit_job_states("rid-run", [JobState(sid0, Status.PASSED, result_id="0123456789abcdef")],
                                           ended_at="never") is CommitOutcome.OPEN
    assert ddb_run_store.end_run("rid-run", RUN_ENDINGS["deadline"], ended_at="2026-07-01T00:05:00Z") is True

    raw = aws["ddb"].Table(aws["table_name"]).get_item(Key={"run_id": "rid-run", "item_type": "STATE"})["Item"]["jobs"]
    assert raw[sid0]["result_id"] == "0123456789abcdef"
    assert "result_id" not in raw[sid1]
    got = ddb_run_store.load_run_state("rid-run")
    assert (got.jobs[sid0].result_id, got.jobs[sid1].result_id) == ("0123456789abcdef", None)


def test_commit_rejected_by_the_write_seq_names_the_same_id_after_rereading(aws, monkeypatch):
    """终态写读到 STATE 之后、发出写之前，另一个写入方认领了 b：整体替换被写入序号的条件挡下，重读再算之后写成，a 点名的仍是调用方给出
    的那个标识（重读再算用的是同一组 JobState，不另生成标识），b 的认领也留下。先后靠包住被测表对象的 update_item 固定。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    table = aws["ddb"].Table(aws["table_name"])
    store, other = DynamoDBRunStore(table), DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))
    meta = _sample_run("seq-run").run_meta
    sid_a, sid_b = (j.scope_id for j in meta.jobs)
    store.create_run(meta, _initial_state("seq-run", [sid_a, sid_b]))
    assert store.try_claim_job("seq-run", sid_a, claimed_at="2026-07-01T00:01:00Z") is True

    ccf = table.meta.client.exceptions.ConditionalCheckFailedException
    real_update = table.update_item
    log: list[str] = []

    def update_item(**kwargs):
        if not log:
            assert other.try_claim_job("seq-run", sid_b, claimed_at="2026-07-01T00:02:00Z") is True  # 插在读与写之间
            log.append("other")
        try:
            resp = real_update(**kwargs)
        except ccf:
            log.append("write-rejected")
            raise
        log.append("write-ok")
        return resp

    monkeypatch.setattr(table, "update_item", update_item)
    given = JobState(sid_a, Status.PASSED, session_id="sess-a", result_id="00000000000000a1")
    assert store.commit_job_states("seq-run", [given], ended_at="never") is CommitOutcome.OPEN

    assert log == ["other", "write-rejected", "write-ok"]
    got = store.load_run_state("seq-run")
    assert got.jobs[sid_a] == JobState(sid_a, Status.PASSED, session_id="sess-a", claimed_at="2026-07-01T00:01:00Z",
                                       result_id="00000000000000a1")
    assert got.jobs[sid_b] == JobState(sid_b, Status.RUNNING, claimed_at="2026-07-01T00:02:00Z")
