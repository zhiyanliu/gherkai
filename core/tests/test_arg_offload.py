"""StepArgument S3 offload 测试（ADR 0030 决定六）：docString/dataTable 搬 S3、META 只留指针，moto mock。

重点验四条决策，全是「静默出错」高风险区：
1. **round-trip 逐字节**：挂 offloader 后 RunMeta 深树（docString 多行/dataTable 空 cell）读回逐字节等于原树。
2. **META 里没有裸正文**：offload 后 meta_json 里出现 content_ref/rows_ref（s3:// 指针）、且**不含**原 content/rows 键。
3. **位置区分、非值探测**：docString 正文本身以 s3:// 开头也能正确 offload/restore（不被误判成"已是指针"）。
4. **key 含 step_index**：同 scenario 多 docString 不撞 key、不串值。
"""
from __future__ import annotations

import json
from urllib.parse import urlparse

from core.model import Job, RunMeta, RunState, Scenario, Status, Step, StepArgument


def _meta_json(aws, run_id: str) -> dict:
    """取回 DDB META item 里 meta_json（解成 dict，验其形态）。"""
    item = aws["ddb"].Table(aws["table_name"]).get_item(
        Key={"run_id": run_id, "item_type": "META"}, ConsistentRead=True
    )["Item"]
    return json.loads(item["meta_json"])


def _steps_of(meta_dict: dict):
    """摊平 meta_dict 里所有 step 的 argument（供断言遍历）。"""
    return [
        step["argument"]
        for job in meta_dict["jobs"]
        for sc in job["scenarios"]
        for step in sc["steps"]
        if "argument" in step
    ]


# ---- round-trip 逐字节（对拍 test_run_meta_deep_argument_round_trip，但走 offload 路径）----
def test_offload_round_trip_byte_exact(ddb_run_store_offload):
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("k", "v"), ("", "空cell")))),
            Step(1, "Then", "看结果", StepArgument(kind="docString", content="多行\n内容\ns3://像指针的正文")),
        )),
    ))
    meta = RunMeta(run_id="off", created_at="t", jobs=(job,))
    ddb_run_store_offload.create_run(meta, RunState(run_id="off", status=Status.PENDING, jobs={}))

    got = ddb_run_store_offload.load_run_meta("off")
    arg0 = got.jobs[0].scenarios[0].steps[0].argument
    arg1 = got.jobs[0].scenarios[0].steps[1].argument
    assert arg0.kind == "dataTable" and arg0.rows == (("k", "v"), ("", "空cell"))  # 空 cell 保留
    assert arg1.kind == "docString" and arg1.content == "多行\n内容\ns3://像指针的正文"  # 逐字节


# ---- META 里只留指针、无裸正文（解 400KB 限的本质）----
def test_meta_json_holds_pointers_not_payload(ddb_run_store_offload, aws):
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("a", "b"),))),
            Step(1, "Then", "看", StepArgument(kind="docString", content="独一无二的正文标记X")),
        )),
    ))
    meta = RunMeta(run_id="ptr", created_at="t", jobs=(job,))
    ddb_run_store_offload.create_run(meta, RunState(run_id="ptr", status=Status.PENDING, jobs={}))

    m = _meta_json(aws, "ptr")
    args = _steps_of(m)
    dt = next(a for a in args if a["kind"] == "dataTable")
    ds = next(a for a in args if a["kind"] == "docString")
    # 指针键在、原正文键缺席
    assert "rows_ref" in dt and "rows" not in dt
    assert "content_ref" in ds and "content" not in ds
    # 指针是 s3:// URI
    assert dt["rows_ref"].startswith("s3://") and ds["content_ref"].startswith("s3://")
    # META item 里根本不含正文标记（真的没内联，才解 400KB 限）
    assert "独一无二的正文标记X" not in json.dumps(m, ensure_ascii=False)
    # 正文确实躺在 S3 对象里
    p = urlparse(ds["content_ref"])
    body = json.loads(aws["s3"].get_object(Bucket=p.netloc, Key=p.path.lstrip("/"))["Body"].read())
    assert body == "独一无二的正文标记X"


# ---- 位置区分、非值探测：正文以 s3:// 开头也不被误判 ----
def test_docstring_starting_with_s3_scheme_survives(ddb_run_store_offload):
    # 正文本身就长得像指针——若读端靠"值是不是 s3:// 开头"猜，就会把正文当指针去 get、炸或串值。
    tricky = "s3://not-a-real-bucket/looks/like/a/pointer.json"
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "Given", "正文即指针样", StepArgument(kind="docString", content=tricky)),
        )),
    ))
    meta = RunMeta(run_id="tricky", created_at="t", jobs=(job,))
    ddb_run_store_offload.create_run(meta, RunState(run_id="tricky", status=Status.PENDING, jobs={}))

    got = ddb_run_store_offload.load_run_meta("tricky")
    assert got.jobs[0].scenarios[0].steps[0].argument.content == tricky  # 原样还原，没被当真指针去取


# ---- key 含 step_index：同 scenario 多 docString 不撞 key、不串值 ----
def test_multiple_docstrings_same_scenario_no_collision(ddb_run_store_offload):
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "Given", "第一段", StepArgument(kind="docString", content="正文AAA")),
            Step(1, "Then", "第二段", StepArgument(kind="docString", content="正文BBB")),
        )),
    ))
    meta = RunMeta(run_id="multi", created_at="t", jobs=(job,))
    ddb_run_store_offload.create_run(meta, RunState(run_id="multi", status=Status.PENDING, jobs={}))

    got = ddb_run_store_offload.load_run_meta("multi")
    steps = got.jobs[0].scenarios[0].steps
    assert steps[0].argument.content == "正文AAA"  # 没被第二段覆盖
    assert steps[1].argument.content == "正文BBB"


# ---- 无 argument 的 run：offloader 挂着也不生事（不 put 任何 args 对象）----
def test_no_argument_run_offload_is_inert(ddb_run_store_offload, aws):
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(Step(0, "Given", "无参数步骤"),)),
    ))
    meta = RunMeta(run_id="noarg", created_at="t", jobs=(job,))
    ddb_run_store_offload.create_run(meta, RunState(run_id="noarg", status=Status.PENDING, jobs={}))

    got = ddb_run_store_offload.load_run_meta("noarg")
    assert got.jobs[0].scenarios[0].steps[0].argument is None
    # 没往 args/ 前缀写任何对象
    listed = aws["s3"].list_objects_v2(Bucket=aws["bucket"], Prefix="noarg/args/")
    assert listed.get("KeyCount", 0) == 0


# ---- restore 按 s3:// URI 自解析、不依赖当前 prefix（核心承诺的回归锚）----
def test_restore_uses_uri_not_current_prefix(aws):
    # offloader 的 s3:// 指针是自描述的：restore 应直接解析 URI 取回，不用 self._prefix 重算 key。
    # 若有人回归成 restore 用 self._prefix 拼 key，同 prefix 测试仍全绿、但换了 prefix 就 NoSuchKey 炸。
    # 故这里用「写端 prefix='writer/' 、读端 prefix='reader/'」的两个 offloader 验：读端仍逐字节还原。
    from core.adapters.run_store.arg_offload import S3StepArgumentOffloader
    from core.serialize import run_meta_from_dict, run_meta_to_dict

    writer = S3StepArgumentOffloader(aws["s3"], aws["bucket"], prefix="writer/")
    reader = S3StepArgumentOffloader(aws["s3"], aws["bucket"], prefix="reader/")

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "When", "填表", StepArgument(kind="dataTable", rows=(("k", "v"), ("", "空")))),
            Step(1, "Then", "看", StepArgument(kind="docString", content="多行\n正文X")),
        )),
    ))
    meta = RunMeta(run_id="xp", created_at="t", jobs=(job,))

    offloaded = writer.offload(run_meta_to_dict(meta), "xp")   # 指针带 writer/ 前缀
    restored = run_meta_from_dict(reader.restore(offloaded, "xp"))  # 读端 prefix 不同，仍应还原
    arg0 = restored.jobs[0].scenarios[0].steps[0].argument
    arg1 = restored.jobs[0].scenarios[0].steps[1].argument
    assert arg0.rows == (("k", "v"), ("", "空"))
    assert arg1.content == "多行\n正文X"


def test_reader_without_offloader_fails_loud_on_offloaded_meta(ddb_run_store_offload, aws):
    """跨组合根边界护栏（曾发生:Lambda 组合根漏注入 offloader → 正文静默丢成 None、worker 拿空参数）：

    写侧带 offloader offload 正文后,读侧若没注入 offloader,load_run_meta 必须 fail-loud——
    静默还原成 None 是「给生产选要不要正确」（ADR 0030 决定七禁止）。
    """
    import pytest
    from core.adapters.run_store.ddb import DynamoDBRunStore

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "Then", "看", StepArgument(kind="docString", content="会被 offload 的正文")),
        )),
    ))
    meta = RunMeta(run_id="noofl", created_at="t", jobs=(job,))
    ddb_run_store_offload.create_run(meta, RunState(run_id="noofl", status=Status.PENDING, jobs={}))

    reader = DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))  # 没注入 offloader 的读者（错误装配）
    with pytest.raises(RuntimeError, match="arg_offloader"):
        reader.load_run_meta("noofl")


def test_reader_without_offloader_not_fooled_by_content_ref_as_text(aws):
    """fail-loud 的判据也守「位置区分、非值探测」（决定六）：正文**恰为** `content_ref` 的内联 META
    （从未 offload）必须能被没注入 offloader 的读者正常读回——按原始 meta_json 串 sniff `"content_ref"`
    会误命中、把好 run 判成组合根装配错误、直接读不回来。
    """
    from core.adapters.run_store.ddb import DynamoDBRunStore

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(
        Scenario(id="s:1", name="sc", steps=(
            Step(0, "Then", "看", StepArgument(kind="docString", content="content_ref")),
            Step(1, "When", "填", StepArgument(kind="dataTable", rows=(("rows_ref", "content_ref"),))),
        )),
    ))
    meta = RunMeta(run_id="inline", created_at="t", jobs=(job,))
    store = DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))  # 无 offloader：写读两侧都内联
    store.create_run(meta, RunState(run_id="inline", status=Status.PENDING, jobs={}))

    back = store.load_run_meta("inline")
    steps = back.jobs[0].scenarios[0].steps
    assert steps[0].argument.content == "content_ref"
    assert steps[1].argument.rows == (("rows_ref", "content_ref"),)
