"""DynamoDBRunStore 对拍测试（ADR 0030 决定六）：与 LocalRunStore 同一批行为断言，moto mock、不产生真实 AWS 费用。

对拍的是**后端无关的行为契约**（save/load round-trip、实时写生命周期、Map 单元素刷、未 create 报错、
omit-null 时间戳）——即 test_stores.py 里 LocalRunStore 那批。物理落点断言（文件存在/JSON 是 list）是
Local 专属、不在此。复用 test_stores 的 _sample_run/_initial_state 造数据。
"""
from __future__ import annotations

import pytest

from gherkai_core.model import JobState, Status, run_state_from_result
from tests.test_stores import _initial_state, _sample_run


# ---- save/load round-trip（对拍 test_run_store_save_load）----
def test_save_load_round_trip(ddb_run_store):
    r = _sample_run("run-1")
    ddb_run_store.save_run(r.run_meta, run_state_from_result(r))

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
    # 这是第 4 步 offload 必须保持的基线：不 offload 时 argument 内容原样往返。
    from gherkai_core.model import Job, RunMeta, RunState, Scenario, Step, StepArgument, Status

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("k", "v"), ("", "空cell")))),
            Step(1, "Then", "看结果", StepArgument(kind="docString", content="多行\n内容\ns3://像指针的正文")),
        )),
    ))
    meta = RunMeta(run_id="deep", created_at="t", jobs=(job,))
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

    # 2) 一个 job 起跑 → running（带血缘）；中途读到部分完成态（Map 单元素刷不互相污染）
    ddb_run_store.update_job_state("rt-run", JobState("features/wiki.feature:6", Status.RUNNING, session_id="sess-1"))
    mid = ddb_run_store.load_run_state("rt-run")
    assert mid.jobs["features/wiki.feature:6"].status == Status.RUNNING
    assert mid.jobs["features/wiki.feature:6"].session_id == "sess-1"
    assert mid.jobs["登录场景"].status == Status.PENDING   # 另一个没动
    assert mid.status == Status.PENDING                      # 总状态还没 finalize

    # 3) 两个 job 各自完成
    ddb_run_store.update_job_state("rt-run", JobState("features/wiki.feature:6", Status.PASSED, session_id="sess-1"))
    ddb_run_store.update_job_state("rt-run", JobState("登录场景", Status.FAILED))
    s2 = ddb_run_store.load_run_state("rt-run")
    assert s2.jobs["features/wiki.feature:6"].status == Status.PASSED
    assert s2.jobs["登录场景"].status == Status.FAILED

    # 4) finalize（commit point）：写总 status + ended_at，各 job 态保留
    ddb_run_store.finalize_run("rt-run", Status.FAILED, "2026-07-01T00:05:00Z")
    final = ddb_run_store.load_run_state("rt-run")
    assert final.status == Status.FAILED
    assert final.ended_at == "2026-07-01T00:05:00Z"
    assert final.started_at == "2026-07-01T00:00:00Z"  # create_run 填的起点保留
    assert final.jobs["features/wiki.feature:6"].status == Status.PASSED  # 没被 finalize 覆盖


def test_update_and_finalize_before_create_raise(ddb_run_store):
    # 未 create_run 就 update/finalize → 报错（对拍 local：ConditionExpression 命中 → FileNotFoundError）
    with pytest.raises(FileNotFoundError):
        ddb_run_store.update_job_state("nope", JobState("s", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        ddb_run_store.finalize_run("nope", Status.PASSED, "t")


def test_session_id_none_omitted_and_roundtrips(ddb_run_store):
    # session_id=None：omit-when-None（不写该键），读回仍 None（对拍 local/serialize 语义）
    meta = _sample_run("s-run").run_meta
    ddb_run_store.create_run(meta, _initial_state("s-run", ["features/wiki.feature:6", "登录场景"]))
    ddb_run_store.update_job_state("s-run", JobState("登录场景", Status.ABORTED, session_id=None))
    js = ddb_run_store.load_run_state("s-run").jobs["登录场景"]
    assert js.status == Status.ABORTED and js.session_id is None


def test_started_ended_omit_when_none_round_trip(ddb_run_store):
    # 起止为 None 时不写、读回仍 None；非 None 时完整保留（对拍 test_run_state_omits/timestamps）
    meta = _sample_run("ts-run").run_meta
    # 初始态 started 填、ended 缺
    ddb_run_store.create_run(meta, _initial_state("ts-run", ["s"]))
    got = ddb_run_store.load_run_state("ts-run")
    assert got.started_at == "2026-07-01T00:00:00Z" and got.ended_at is None
    # finalize 后 ended 出现
    ddb_run_store.finalize_run("ts-run", Status.PASSED, "2026-07-01T01:00:00Z")
    got2 = ddb_run_store.load_run_state("ts-run")
    assert got2.ended_at == "2026-07-01T01:00:00Z"


def test_detached_flag_on_state_item(aws):
    """detached 组合根的 create_run 在 STATE item 落 detached=true 标记;默认(同步 run)不落（ADR 0034 kicker filter）。"""
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

    def _mk(run_id):
        job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(
            Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),))
        meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,))
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

    # 只读访问器（推进器 handler 侧分流用它,ADR 0034 端到端 cloud 1b）:读同一个标记,未知 run 保守判 False
    reader = DynamoDBRunStore(table)
    assert reader.is_detached("det-1") is True
    assert reader.is_detached("sync-1") is False
    assert reader.is_detached("没这个 run") is False


def test_worker_task_def_arns_on_state_item(aws):
    """create_run 把 definition 的 worker revision ARN 摊平成 STATE 顶层属性（ADR 0038 清理 pass 安全阀）。

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
            Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "x"),)),))
        meta = RunMeta(run_id=run_id, created_at="t", jobs=(job,),
                       worker_task_defs=worker_task_defs)
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

    # 旧 definition / local 档（无该字段）→ 属性缺席
    meta, state = _mk("wk-none")
    DynamoDBRunStore(table).create_run(meta, state)
    item = table.get_item(Key={"run_id": "wk-none", "item_type": "STATE"}, ConsistentRead=True)["Item"]
    assert ATTR not in item
