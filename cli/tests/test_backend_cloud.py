"""cli --backend cloud 接线层测试。

**只验接线，不引 moto、不连真 AWS**：adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰。
做法——patch `compose._make_ddb_table`/`_make_s3_client`（store 句柄）+ `preflight_cloud_resources`（探活）
+ `resolve_worker_variant`（variant 解析）返回**记录调用的 fake**，验证：
- `run` 只有本机后端：给出 cloud 即以退出码 2 结束并指向 submit，此前不做任何检查、不发任何云端调用（ADR 0016 决策 A）；
- 云端 submit / status / explain 构造了正确的 store adapter：DDB 拿 table 句柄、三个 S3 件套共享同一个 client；submit 的提交记录
  是定义前缀下的一个 jobs 对象加 runs 表里的头与运行态（ADR 0016「cli `--backend {local,cloud}`」节，ADR 0030 决定六「云端提交记录」条）；
- **prefix 两层命名（ADR 0033）**：--prefix 批量推导默认名（{prefix}runs/artifacts/events/cluster）、单资源 --xxx 覆盖、环境变量兜底；
- **preflight fail-fast**：资源不存在即以退出码 2 结束 + 错误点名 prefix（ADR 0033「preflight fail-fast」节）；缺 boto3、
  建 run 撞 AWS 错同样以退出码 2 结束（ADR 0030 决定七「失败退出码分层」）；
- CLI 一侧不装配 FargateEngine：起 worker task 的是推进器 Lambda（ADR 0016 决策 C），云端 submit 只写提交记录；
- artifacts 在 cloud 下是 s3://+ddb:// 形态；
- **三道闸的次序与退出码**：版本 skew → 资源 preflight → worker 镜像 variant 解析，
  前一道拦下时后面的一次都不执行；variant miss 即以退出码 2 结束、不回落（ADR 0037 决策 7 / 0038）；解析结果进 definition
  （ADR 0038「运行时与 preflight」的「选择进 definition」条）；
- 带 `--expose-local` 时起不来守护进程、守护进程起隧道失败或在回报之前崩溃都以退出码 2 结束、不建 run；run 已存在时同样以
  退出码 2 结束、不改原有的记录（ADR 0035 决策 3「云端 `submit`」）。守护进程在线程里以真实的管道执行（`_inline_children`），
  隧道服务是假实现。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_runtime import tunnel as gtunnel

from _inline_children import inline_children  # noqa: F401 —— 夹具：submit 启动的后台进程在线程里执行
from test_main import _fake_schedule_factory


def _write_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "demo.feature"
    feat.write_text("Feature: demo\n  Scenario: s\n    When \"做点啥\"\n", encoding="utf-8")
    return feat


# ---- fake boto3 句柄：记录关键调用，不连真 AWS ----
# 云端 status / explain 读运行态之前先读 META 顶层的结构版本（ADR 0037 决策 7）：假 table 对 META 键给本版本的头
_META_HEADER = {"Item": {"run_id": "r1", "item_type": "META", "schema_version": 2, "cli_version": "1.5.0"}}


class _FakeTable:
    """假 DDB table 句柄：DynamoDBRunStore 吃它（put_item/update_item/get_item/load/meta.client.exceptions）。

    `puts` 留下每次 put_item 的 Item 原样——definition 真值只在云端后端的 DDB 写里（不落本地文件），
    要验「某字段真进了 definition」就从这里取（经 serialize，比断言构造入参更贴真实落库）。
    """
    def __init__(self, record):
        self._record = record
        self.puts: list[dict] = []
        self.meta = type("Meta", (), {"client": type("C", (), {"exceptions": type("E", (), {
            "ConditionalCheckFailedException": type("CCFE", (Exception,), {})})()})()})()

    def load(self): self._record.append(("ddb", "load"))
    def put_item(self, **kw):
        self._record.append(("ddb", "put_item"))
        self.puts.append(kw.get("Item", {}))
    def update_item(self, **kw): self._record.append(("ddb", "update_item"))
    def get_item(self, **kw):
        self._record.append(("ddb", "get_item"))
        return {}  # 读回空（submit 只写不读；此处防御）


class _FakeS3:
    """假 S3 client：三个件套共享一个；记录 head_bucket / put_object，`puts` 留下每次 put_object 的参数原样（含正文）。"""
    def __init__(self, record):
        self._record = record
        self.id = id(self)  # 用于断言「三个件套拿的是同一个 client」
        self.puts: list[dict] = []

    def head_bucket(self, **kw): self._record.append(("s3", "head_bucket"))
    def put_object(self, **kw):
        self._record.append(("s3", "put_object", kw.get("Key")))
        self.puts.append(kw)


def _patch_skew(monkeypatch, record=None, *, skew=("ok", "")):
    """把版本 skew 闸（ADR 0037 决策 7）patch 成默认放行且静默：读戳不建 ssm client、判定直接给 `skew`。

    两处都得 patch——`read_backend_version` 否则真去读 SSM、`check_version_skew` 否则会对 dev 版打「跳过比对」
    提示行、污染其它断言。skew 自身的判据在 runtime 的 compose 测试里验；此处只让云端路径通过这道闸。
    """
    def fake_read_version(**kwargs):
        if record is not None:
            record.append(("ssm", "read_backend_version", kwargs.get("prefix")))
        return "<stub 版本戳>"

    monkeypatch.setattr(m.compose, "read_backend_version", fake_read_version)
    monkeypatch.setattr(m.compose, "check_version_skew", lambda *a, **kw: skew)


_STUB_DIGEST = "sha256:" + "ab" * 32   # 64 位十六进制，形态同真 manifest digest（打印缩到前 12 位）


def _stub_revision(engine: str) -> str:
    return f"arn:aws:ecs:us-east-1:111122223333:task-definition/gherkai-{engine}-worker:7"


def _patch_cloud_handles(monkeypatch, record, *, preflight_err=None, skew=("ok", ""),
                         variant_err=None, resolved_variant="base"):
    """patch store 钩子 + preflight（默认放行）+ 版本 skew 闸 + worker variant 闸（都默认放行）返回记录调用的
    fake（不连真 AWS）。

    preflight_cloud_resources 默认 patch 成返回 preflight_err（None 表示资源都在、放行）——它自己建 boto client 探活，
    测试里不真探，只验「接线调它 + 它的返回决定要不要以退出码 2 结束」。返回 (fake_s3, made, preflight_calls)。

    **版本 skew 闸（ADR 0037 决策 7）两处都 patch**：`read_backend_version`（否则真去建 ssm client 读 SSM）与
    `check_version_skew`（默认判 `ok`，即无提示行，让本文件其它断言不被 skew 噪声干扰）。`skew=` 可换判定，
    skew 自身的判据在 runtime 的 compose 测试里验、此处只验接线。

    **worker variant 闸（ADR 0038）同理 patch `resolve_worker_variant`**：它的真实实现要读 SSM 映射 + 探 ECS/ECR。
    默认给每个被问到的引擎一条假 resolution（variant 取显式给的 `--worker-variant`，缺省则 `resolved_variant`
    ——模拟「解析到部署级默认指针」）；`variant_err=WorkerVariantError(...)` 改成拦下的情形。调用入参记进
    `made["variant"]`（可验次序、engines 只含本 run 用到的、backend_version 复用同一次读戳）。

    `build_fargate_engines` patch 成一调即失败：CLI 一侧不装配 FargateEngine（ADR 0016 决策 C），哪条路径调了它即红。
    """
    fake_s3 = _FakeS3(record)
    made = {"ddb_tables": [], "s3_clients": [], "variant": []}
    preflight_calls = []

    def fake_make_ddb(table, *, region, profile):
        record.append(("make", "ddb_table", table, region, profile))
        t = _FakeTable(record)
        made["ddb_tables"].append(t)
        return t

    def fake_make_s3(*, region, profile):
        record.append(("make", "s3_client", region, profile))
        made["s3_clients"].append(fake_s3)
        return fake_s3

    def fake_preflight(**kwargs):
        preflight_calls.append(kwargs)
        return preflight_err

    def forbidden_fargate(**kwargs):
        raise AssertionError("CLI 一侧不装配 FargateEngine（起 worker task 的是推进器 Lambda）")

    def fake_resolve_variant(**kwargs):
        made["variant"].append(kwargs)
        if variant_err is not None:
            raise variant_err
        effective = kwargs.get("variant") or resolved_variant
        return {
            e: m.compose.WorkerResolution(
                engine=e, variant=effective, revision_arn=_stub_revision(e), digest=_STUB_DIGEST)
            for e in kwargs["engines"]
        }

    _patch_skew(monkeypatch, record, skew=skew)
    monkeypatch.setattr(m.compose, "_make_ddb_table", fake_make_ddb)
    monkeypatch.setattr(m.compose, "_make_s3_client", fake_make_s3)
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", fake_preflight)
    monkeypatch.setattr(m.compose, "build_fargate_engines", forbidden_fargate)
    monkeypatch.setattr(m.compose, "resolve_worker_variant", fake_resolve_variant)
    return fake_s3, made, preflight_calls


def _definition(table, s3=None) -> dict:
    """从假句柄的写入里取回提交记录（ADR 0030 决定六「云端提交记录」条）：头（META item）的 meta_json，给了假 S3 client 时再按头里
    的 jobs_ref 取回那次 put_object 写下的 jobs 对象、放回 `jobs` 键，即整份运行定义。只看头部字段的用例不必给 s3。"""
    metas = [it for it in table.puts if it.get("item_type") == "META"]
    assert metas, "没有写 META item（definition 未落库）"
    d = json.loads(metas[-1]["meta_json"])
    if s3 is not None:
        [body] = [kw["Body"] for kw in s3.puts if metas[-1]["jobs_ref"] == f"s3://{kw['Bucket']}/{kw['Key']}"]
        d["jobs"] = json.loads(body)
    return d


def _clear_resource_env(monkeypatch) -> None:
    for var in ("AWS_DDB_TABLE", "AWS_S3_BUCKET", "AWS_RESOURCE_PREFIX"):
        monkeypatch.delenv(var, raising=False)


# ---- run 只有本机后端：给出 cloud 即以退出码 2 结束并指向 submit（ADR 0016 决策 A）----

def _forbid_run_steps(monkeypatch) -> None:
    """run 给出云端后端时，入口之后的每一步（读 feature、问本机 worker、解析 AWS 身份、建 store、起隧道、调度）一调即失败。"""
    def forbidden(*a, **k):
        raise AssertionError("run 给出云端后端时不该走到这一步")

    for name in ("load_feature", "resolve_worker_cmd", "query_capabilities", "engine_min_grace",
                 "resolve_aws_identity", "resolve_cloud_target", "build_local_stores", "build_cloud_stores", "build_engines"):
        monkeypatch.setattr(m.compose, name, forbidden)
    monkeypatch.setattr(m, "schedule", forbidden)
    monkeypatch.setattr(m, "_setup_tunnel", forbidden)


@pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])
def test_run_with_cloud_backend_exits_2_pointing_to_submit_before_any_check(tmp_path, monkeypatch, capsys, mode):
    """命令行给出 `run --backend cloud`：以退出码 2 结束，说明 run 只在本机执行、云端后端经 `gherkai submit --backend cloud` 提交。
    拒绝排在一切检查之前：不读 feature、不问本机 worker、不解析 AWS 身份、不起隧道、不落库，一次云端调用都不发。
    带 --json 时标准输出为空（机读契约：先看退出码，标准输出非空才解析），那句说明只在标准错误。"""
    record: list = []
    _fake_s3, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _forbid_run_steps(monkeypatch)
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--report-dir", str(reports),
                 "--grace", "300", "--expose-local", "http://localhost:3000", *mode])
    assert rc == 2
    cap = capsys.readouterr()
    assert cap.out == ""
    err = cap.err
    assert "gherkai run 只在本机执行" in err and "--backend" in err and "gherkai submit --backend cloud" in err
    assert "--backend local" not in err   # 后端由命令行给出：不提「用 --backend local 覆盖配置文件」
    assert "Traceback" not in err
    assert record == [] and preflight_calls == [] and made["variant"] == []
    assert not reports.exists()


def test_run_with_cloud_backend_and_submit_only_flags_still_points_to_submit(tmp_path, monkeypatch, capsys):
    """按 submit 的写法在 run 上同给 `--backend cloud` 与 run 没有的云端参数（--prefix、--worker-variant）：仍是那句指向
    submit 的说明、退出码 2，不被「不认识的参数」的报错盖过，也不做任何检查。"""
    record: list = []
    _fake_s3, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _forbid_run_steps(monkeypatch)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "stage-",
                 "--worker-variant", "login", "--json"])
    assert rc == 2
    cap = capsys.readouterr()
    assert cap.out == ""
    assert "gherkai submit --backend cloud" in cap.err
    assert "unrecognized arguments" not in cap.err
    assert record == [] and preflight_calls == [] and made["variant"] == []


@pytest.mark.parametrize("argv", [
    ["run", "--backend", "cloud"],
    ["run", "--backend", "cloud", "--json"],
    ["run", "--backend=cloud", "--json"],
    ["run", "--backend", "cloud", "--prefix=stage-", "--json"],
    ["run", "--backend", "local", "--backend", "cloud"],
    ["run", "--back", "cloud", "--json"],
    ["run", "--backend", "local", "--back=cloud"],
], ids=["no-feature", "no-feature-json", "equals-form", "submit-only-flag-equals-form", "last-backend-wins",
        "abbreviated-option", "abbreviated-option-overrides-earlier-local"])
def test_run_with_cloud_backend_points_to_submit_even_when_other_arguments_are_wrong(monkeypatch, capsys, argv):
    """云端后端下 run 一律先给那句指向 submit 的说明：没有给 feature、选项写成等号形式、带着 submit 才有的参数时都一样，
    不被「缺少 features」「不认识的参数」这类解析报错盖过；退出码 2，标准输出为空，不做任何检查。"""
    record: list = []
    _fake_s3, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _forbid_run_steps(monkeypatch)
    rc = m.main(argv)
    assert rc == 2
    cap = capsys.readouterr()
    assert cap.out == ""
    assert "gherkai run 只在本机执行" in cap.err and "gherkai submit --backend cloud" in cap.err
    assert "required" not in cap.err and "unrecognized arguments" not in cap.err
    assert record == [] and preflight_calls == [] and made["variant"] == []


@pytest.mark.parametrize("override", [["--back", "local"], ["--back=local"], ["--backend", "local"]],
                         ids=["abbreviated", "abbreviated-equals-form", "full-name"])
def test_run_whose_last_backend_is_local_is_not_turned_away(tmp_path, monkeypatch, capsys, override):
    """对偶：命令行先给 cloud、后面又给 local（含参数解析接受的缩写写法）时，生效的后端是 local，run 照常进入本机路径，
    不给那句指向 submit 的说明。这里用一个不存在的 feature 让本机路径在入口校验处停下。"""
    monkeypatch.chdir(tmp_path)
    rc = m.main(["run", "missing.feature", "--backend", "cloud", *override, "--json"])
    cap = capsys.readouterr()
    assert "gherkai submit --backend cloud" not in cap.err
    assert rc == 2 and "missing.feature" in cap.err


def test_run_help_is_available_with_cloud_backend_on_the_command_line(capsys):
    """对偶：同给 --help 时照常打印帮助、退出码 0，不被那句拒绝拦下。"""
    with pytest.raises(SystemExit) as ei:
        m.main(["run", "--backend", "cloud", "--help"])
    assert ei.value.code == 0
    assert "usage:" in capsys.readouterr().out


def test_run_without_a_feature_on_the_local_backend_is_reported_by_argument_parsing(capsys):
    """对偶：本机后端下没有给 feature，仍由命令行解析报出缺少参数、退出码 2，不改说成「改用 submit」。"""
    with pytest.raises(SystemExit) as ei:
        m.main(["run", "--backend", "local"])
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "features" in err and "gherkai submit --backend cloud" not in err


def test_run_without_cloud_backend_reports_submit_only_flags_as_unrecognized(tmp_path, capsys):
    """对偶：没有给出云端后端时，run 不认识的参数照常由命令行解析报出、退出码 2，不改说成「改用 submit」。"""
    with pytest.raises(SystemExit) as ei:
        m.main(["run", str(_write_feature(tmp_path)), "--prefix", "stage-"])
    assert ei.value.code == 2
    err = capsys.readouterr().err
    assert "unrecognized arguments: --prefix stage-" in err
    assert "gherkai submit --backend cloud" not in err


def test_run_help_describes_only_the_local_backend(capsys):
    """run 的 --help 与入口拒绝不许漂移：--backend 一项写明云端后端用 submit；只用于云端的参数不出现在 run 上。"""
    import re

    with pytest.raises(SystemExit):
        m.main(["run", "--help"])
    out = re.sub(r"\s+", " ", capsys.readouterr().out)   # argparse 按终端宽度折行，折行处原本是空格
    assert "gherkai submit --backend cloud" in out
    for flag in ("--prefix", "--ddb-table", "--s3-bucket", "--worker-variant",
                 "--events-table", "--cluster", "--subnet", "--security-group", "CloudWatch"):
        assert flag not in out, flag


def test_run_and_submit_do_not_accept_cloud_execution_flags(tmp_path):
    """事件表、cluster、子网与安全组不在任何子命令上：云端后端只经 submit 执行，这几项取自推进器 Lambda 的环境变量
    （ADR 0016 决策 C），在提交侧唯一可能的作用是改「提交前检查」探哪个资源，给错值会把「探针指错」伪装成「后端未部署」，
    故探针一律按 --prefix 推。run 另不收资源名与 variant 参数：run 只有本机后端，它们在本机路径上没有消费方。"""
    parser = m._build_parser()
    feat = str(_write_feature(tmp_path))
    for flag in ("--events-table", "--cluster", "--subnet", "--security-group"):
        with pytest.raises(SystemExit) as ei:
            parser.parse_args(["submit", feat, "--backend", "cloud", flag, "whatever"])
        assert ei.value.code == 2, f"submit 不该认 {flag}"
    for flag in ("--events-table", "--cluster", "--subnet", "--security-group",
                 "--prefix", "--ddb-table", "--s3-bucket", "--worker-variant"):
        with pytest.raises(SystemExit) as ei:
            parser.parse_args(["run", feat, flag, "whatever"])
        assert ei.value.code == 2, f"run 不该认 {flag}"


# ---- 云端 submit 构造正确 store adapter + 参数 + 提交记录的存放 + S3 client 同一性 ----

def test_cloud_submit_wires_stores_with_correct_handles(tmp_path, monkeypatch, capsys):
    record: list = []
    fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)

    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1"])
    assert rc == 0

    # 钩子按参数被调：ddb 用表名 T、s3 只造一次（三件套共享）
    ddb_makes = [r for r in record if r[:2] == ("make", "ddb_table")]
    s3_makes = [r for r in record if r[:2] == ("make", "s3_client")]
    assert ddb_makes == [("make", "ddb_table", "T", "us-east-1", None)]
    assert len(s3_makes) == 1, "S3 client 只该造一次（三个件套共享）"
    assert len(made["s3_clients"]) == 1 and made["s3_clients"][0] is fake_s3
    # 提交记录真写进 DDB——证 store adapter 真拿到可用句柄
    assert ("ddb", "put_item") in record


def test_cloud_submit_writes_one_jobs_object_under_the_definitions_prefix(tmp_path, monkeypatch, capsys):
    """云端 submit 的提交记录（ADR 0030 决定六「云端提交记录」条）：产物桶里唯一的写是定义前缀下这个 run 的一个 jobs 对象，带「键不存在
    才写」的条件、不带 tag，不在报告前缀之下；它先于 runs 表的两次写，头里的 jobs_ref 指向它，meta_json 里没有 jobs。DocString 正文
    原样在 jobs 对象里。"""
    import json
    import re

    record: list = []
    fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)
    feat = tmp_path / "d.feature"
    feat.write_text('Feature: F\n  Scenario: s\n    When "做" \n      """\n      多行正文\n      """\n', encoding="utf-8")

    rc = m.main(["submit", str(feat), "--backend", "cloud", "--ddb-table", "T", "--s3-bucket", "B",
                 "--region", "us-east-1", "--report-dir", "team/reports"])
    assert rc == 0
    run_id = capsys.readouterr().out.strip()
    [put] = fake_s3.puts
    assert put["Bucket"] == "B" and put["IfNoneMatch"] == "*" and "Tagging" not in put
    assert re.fullmatch(rf"definitions/{re.escape(run_id)}/[0-9a-f]{{32}}\.json", put["Key"]), put["Key"]
    writes = [r for r in record if r[:2] in (("s3", "put_object"), ("ddb", "put_item"))]
    assert [r[:2] for r in writes] == [("s3", "put_object"), ("ddb", "put_item"), ("ddb", "put_item")]
    head = made["ddb_tables"][0].puts[0]
    assert head["item_type"] == "META" and head["jobs_ref"] == f"s3://B/{put['Key']}"
    assert "jobs" not in json.loads(head["meta_json"])
    jobs = json.loads(put["Body"])
    assert jobs[0]["scenarios"][0]["steps"][0]["argument"]["content"] == "多行正文"


# ---- 两层命名（ADR 0033）：prefix 批量推导默认名 + 单资源覆盖 + 环境变量兜底 ----

def test_cloud_submit_prefix_derives_default_names(tmp_path, monkeypatch, capsys):
    # 不给 --ddb-table/--s3-bucket：全走 prefix 推导（默认 gherkai-）。
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _clear_resource_env(monkeypatch)

    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 0
    # RunStore 表是 gherkai-runs（prefix 默认推导）
    assert ("make", "ddb_table", "gherkai-runs", "us-east-1", None) in record
    # preflight 拿到全套 prefix 推导名
    pf = preflight_calls[0]
    assert pf["prefix"] == "gherkai-"
    assert pf["runs_table"] == "gherkai-runs"
    assert pf["events_table"] == "gherkai-events"
    assert pf["bucket"] == "gherkai-artifacts"
    assert pf["cluster"] == "gherkai-cluster"


def test_cloud_submit_prefix_custom_switches_whole_set(tmp_path, monkeypatch, capsys):
    # --prefix prod- 一键切整套默认名（多环境）。
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _clear_resource_env(monkeypatch)

    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "prod-",
                 "--region", "us-east-1"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["prefix"] == "prod-"
    assert pf["runs_table"] == "prod-runs" and pf["events_table"] == "prod-events"
    assert pf["bucket"] == "prod-artifacts" and pf["cluster"] == "prod-cluster"
    assert ("make", "ddb_table", "prod-runs", "us-east-1", None) in record


def test_cloud_submit_single_resource_override_beats_prefix(tmp_path, monkeypatch, capsys):
    # 单资源 --xxx 覆盖：给完整终值，prefix 自然不参与（覆盖不走「拼默认名」路径，无特判）。
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _clear_resource_env(monkeypatch)

    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "prod-",
                 "--ddb-table", "custom-runs", "--s3-bucket", "custom-artifacts", "--region", "us-east-1"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["runs_table"] == "custom-runs"       # 覆盖，非 prod-runs
    assert pf["bucket"] == "custom-artifacts"      # 覆盖
    assert pf["events_table"] == "prod-events"     # 没有覆盖参数 → 仍走 prefix
    assert pf["cluster"] == "prod-cluster"


def test_cloud_submit_table_bucket_from_env(tmp_path, monkeypatch, capsys):
    # 环境变量兜底：AWS_DDB_TABLE/AWS_S3_BUCKET 供值时无需 flag（优先级：flag > env > prefix 推导）
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setenv("AWS_DDB_TABLE", "ET")
    monkeypatch.setenv("AWS_S3_BUCKET", "EB")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 0
    assert ("make", "ddb_table", "ET", "us-east-1", None) in record
    assert preflight_calls[0]["bucket"] == "EB"


def test_cloud_submit_missing_boto3_exits_2(tmp_path, monkeypatch, capsys):
    # 缺 boto3：preflight 的 import boto3 抛 ImportError → 退出码 2 + 报错点名 boto3（CLI 只转述 ImportError；
    # 库消费者装 `gherkai-core[aws]` extra 补，ADR 0037 决策 2c 起 CLI 发行包自带）
    _patch_skew(monkeypatch)

    def boom_import(**k):
        raise ImportError("No module named 'boto3'")

    monkeypatch.setattr(m.compose, "preflight_cloud_resources", boom_import)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1"])
    assert rc == 2
    assert "boto3" in capsys.readouterr().err


# ---- preflight fail-fast：资源不存在 → 退出码 2 + 错误点名 prefix ----

def test_cloud_submit_preflight_missing_resource_exits_2_names_prefix(tmp_path, monkeypatch, capsys):
    # preflight 返回非 None（某资源不存在）→ 以退出码 2 结束，错误串含 prefix（引导「prefix 配错/CDK 没部署」）。
    record: list = []
    _patch_cloud_handles(monkeypatch, record,
                         preflight_err="--backend cloud 资源缺失：DynamoDB 表 gherkai-events（用 --prefix='gherkai-' 拼出）不存在——是 --prefix 配错、还是后端未部署（gherkai deploy）？")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "资源缺失" in err and "--prefix" in err and "gherkai deploy" in err


# ---- 一个 run 的规模上限（ADR 0025「一个 run 的规模上限」）：云端 submit 与 plan 同一句说明、退出码 2，没有连云端 ----

def test_cloud_submit_over_the_job_cap_exits_2_before_any_cloud_call(tmp_path, monkeypatch, capsys):
    """两个后端同一个数：501 个 job 的 run 在云端 submit 上同样在计划阶段被拒，说明与 plan 逐字相同；版本闸、资源检查与建 run
    一次都没有执行。"""
    from test_main import _size_cap_line, _write_feature_with_jobs

    record: list = []
    _, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    feat = str(_write_feature_with_jobs(tmp_path, 501))
    assert m.main(["plan", feat]) == 2
    planned = _size_cap_line(capsys.readouterr().err)
    assert m.main(["submit", feat, "--backend", "cloud", "--region", "us-east-1"]) == 2
    assert _size_cap_line(capsys.readouterr().err) == planned
    assert record == [] and preflight_calls == [] and made["ddb_tables"] == [] and made["variant"] == []


# ---- 写提交记录撞 AWS 错（表不可达）→ 退出码 2 ----

def test_cloud_submit_create_run_aws_error_exits_2(tmp_path, monkeypatch, capsys):
    # preflight 放行，但写提交记录时 put_item 抛 botocore（如权限）→ 以退出码 2 结束、一句诊断，不打回溯。
    from botocore.exceptions import ClientError

    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    real_make = m.compose._make_ddb_table

    def make_failing(table, *, region, profile):
        t = real_make(table, region=region, profile=profile)

        def boom_put(**kw):
            raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "PutItem")

        t.put_item = boom_put
        return t

    monkeypatch.setattr(m.compose, "_make_ddb_table", make_failing)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "云端不可达" in err and "Traceback" not in err


@pytest.mark.parametrize("code, sentence", [
    ("PreconditionFailed", "已经存在，没有重新建立。请重新执行这条命令。"),
    ("ConditionalRequestConflict", "云端不可达"),
    ("AccessDenied", "云端不可达"),
])
def test_cloud_submit_jobs_object_write_failure_exits_2_before_any_table_write(tmp_path, monkeypatch, capsys, code, sentence):
    """写 jobs 对象（建 run 的第一步）失败：键已存在（412）按 run 已存在报出，别的 S3 错误按写记录失败报出，都以退出码 2 结束、不打
    回溯；runs 表一次都没有写（ADR 0030 决定六「建 run 的次序与失败时留下的」）。"""
    from botocore.exceptions import ClientError

    record: list = []
    fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)

    def failing_put(**kw):
        record.append(("s3", "put_object", kw.get("Key")))
        raise ClientError({"Error": {"Code": code, "Message": code}}, "PutObject")

    fake_s3.put_object = failing_put
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1"])
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert sentence in cap.err and "Traceback" not in cap.err
    assert ("ddb", "put_item") not in record and made["ddb_tables"][0].puts == []


# ---- 本机 run 只走 build_engines（SubprocessEngine），不注入 S3 落点 ----

def test_local_uses_subprocess_not_fargate(tmp_path, monkeypatch, capsys):
    # local 不走 build_fargate_engines（走 build_engines/SubprocessEngine）。
    box = {"fargate": 0}
    monkeypatch.setattr(m.compose, "build_fargate_engines", lambda **k: box.__setitem__("fargate", box["fargate"] + 1) or {})
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0
    assert box["fargate"] == 0  # local 从不造 FargateEngine


def test_local_does_not_inject_artifact_s3(tmp_path, monkeypatch):
    # local 模式不注入 artifact_s3（worker 报 file://、不上传）——ADR 0029 零行为变化
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box.update(kwargs)
        return real_build(run_id=kwargs["run_id"])

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0
    assert box.get("artifact_s3") is None  # local 不注入


# ---- artifacts cloud 下是 s3://+ddb:// 形态 ----

def test_status_cloud_artifacts_follow_the_given_table_bucket_and_report_dir(monkeypatch, capsys):
    """status --json 的 artifacts 按给出的表名、桶名（环境变量）与 --report-dir 前缀拼：s3:// 报告与判定明细、ddb:// 元信息。"""
    class _PassedTable:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {}}}

    _patch_skew(monkeypatch)
    monkeypatch.setenv("AWS_S3_BUCKET", "B")
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _PassedTable())
    assert m.main(["status", "r1", "--backend", "cloud", "--ddb-table", "T", "--report-dir", "runs",
                   "--region", "us-east-1", "--json"]) == 0
    art = json.loads(capsys.readouterr().out)["artifacts"]
    assert art["jobs_dir"] == "s3://B/runs/r1/jobs/"
    assert art["run_meta"] == "ddb://T/r1#META" and art["run_state"] == "ddb://T/r1#STATE"
    assert art["report_index"] == "s3://B/runs/r1/index.html"


def test_status_cloud_reads_only_the_head_and_never_builds_an_s3_client(monkeypatch, capsys):
    """不带 `--wait` 的云端 status 只读提交记录的头与运行态（ADR 0030 决定六「读整份定义」一项末句）：不取 jobs 对象、不起 S3 client，
    读 META 时只投影头部的两个属性。"""
    gets: list[dict] = []

    class _PassedTable:
        def get_item(self, **kw):
            gets.append(kw)
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {}}}

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _PassedTable())
    monkeypatch.setattr(m.compose, "_make_s3_client", lambda **kw: pytest.fail("不带 --wait 的 status 不该起 S3 client"))
    assert m.main(["status", "r1", "--backend", "cloud", "--ddb-table", "T", "--region", "us-east-1", "--json"]) == 0
    capsys.readouterr()
    [head_read] = [kw for kw in gets if kw["Key"]["item_type"] == "META"]
    assert set(head_read["ExpressionAttributeNames"].values()) == {"schema_version", "cli_version"}


# ---- submit/status cloud 的 preflight/fail-fast 接线 ----

def test_submit_cloud_preflight_probes_taskdefs_and_lambda_chain(tmp_path, monkeypatch, capsys):
    """submit cloud 的 preflight 除表/桶/cluster 外还探：本 run 用到引擎的 task-def + 事件驱动链三 Lambda
    （任一缺就会提交成功而 run 不按正常的链推进，须挡在提交前）。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    _clear_resource_env(monkeypatch)

    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["task_defs"] == ["gherkai-novaact-worker"]
    assert pf["lambda_fns"] == ["gherkai-kicker", "gherkai-reconciler", "gherkai-exit-observer"]
    # 产物前缀一致性也在提交前比（--report-dir vs 推进器 REPORT_DIR，ADR 0033）——不传则该探针整体失效
    assert pf["report_dir"] == "reports"


def test_submit_cloud_preflight_probes_prefix_derived_names(tmp_path, monkeypatch, capsys):
    """submit 的 events 表/cluster 探针名一律按 --prefix 推（无 flag 可覆盖，见 test_run_and_submit_do_not_accept_cloud_execution_flags）。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--prefix", "stage-"])
    assert rc == 0
    pf = preflight_calls[0]
    assert pf["events_table"] == "stage-events" and pf["cluster"] == "stage-cluster"


def test_submit_cloud_passes_custom_report_dir_to_preflight(tmp_path, monkeypatch, capsys):
    """非默认 --report-dir 也要交给 preflight 比对（否则提交侧/推进侧前缀静默分裂、结果落别处）。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--report-dir", "mine"])
    assert rc == 0
    assert preflight_calls[0]["report_dir"] == "mine"


def test_submit_cloud_preflight_failure_exits_2(tmp_path, monkeypatch, capsys):
    """preflight 报资源缺（如链上 Lambda 不存在）→ 提交前以退出码 2 结束、不写任何东西。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record, preflight_err="Lambda 函数 gherkai-kicker 不存在——…")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2
    assert not [r for r in record if r[0] == "ddb"]  # 没碰 runs 表（挡在 create_run 前）


def test_status_wait_cloud_kicker_missing_fails_fast(monkeypatch, capsys):
    """--wait 接力 invoke 的 kicker 不存在（ResourceNotFound）→ 点名 prefix 并以退出码 2 结束，不再吞掉死等
    （接力对象缺失时轮询永不终止；其他 AWS 瞬时错仍吞掉、下一个卡住窗口再 invoke）。"""
    from botocore.exceptions import ClientError

    class _PendingTable:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "pending", "jobs": {}, "detached": True}}

    class _NoKickerLambda:
        def invoke(self, **kw):
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "Function not found"}},
                              "Invoke")

    _patch_skew(monkeypatch)  # 版本 skew 闸先于云端读（ADR 0037 决策 7），此处不是它的靶子
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _PendingTable())
    monkeypatch.setattr(m.compose, "_make_lambda_client", lambda *, region, profile: _NoKickerLambda())
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)  # 卡住判定要连续 3 轮，免真等
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--wait"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "gherkai-kicker" in err and "--prefix" in err


def test_status_wait_cloud_only_waits_for_a_run_that_is_not_detached(monkeypatch, capsys):
    """同步 `run --backend cloud` 的 run（STATE 没有 detached 标记）上执行 status --wait：只轮询等待、一次都不 invoke kicker
    （kicker 对它本就整体 no-op，invoke 只是空转；接力只对 submit 的 run），提示一句，等到终态按判定给退出码。"""
    reads = {"n": 0}

    class _Table:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            reads["n"] += 1
            status = "passed" if reads["n"] >= 6 else "running"  # 前几轮进行中（卡住判定本会在第 3 轮 invoke），之后到终态
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": status, "jobs": {}}}

    invoked = []

    class _Lambda:
        def invoke(self, **kw):
            invoked.append(kw)

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    monkeypatch.setattr(m.compose, "_make_lambda_client", lambda *, region, profile: _Lambda())
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: None)
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--wait"])
    assert rc == 0 and invoked == []
    assert "只等待它结束、不接力推进" in capsys.readouterr().err


def test_status_cloud_pending_hint_offers_relay_only_for_detached_runs_and_stays_quiet_when_the_marker_is_unreadable(monkeypatch, capsys):
    """云端 status（不带 --wait）全 job pending 时的「可接力推进」提示只对 submit 的 run 打；读标记遇到 AWS 错误时不提示、也不另报
    「云端不可达」（提示只是附加诊断，主查询已成功）。"""
    from botocore.exceptions import ClientError

    class _Table:
        def __init__(self, detached, marker_error=False):
            self.detached, self.marker_error = detached, marker_error

        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            if "ProjectionExpression" in kw:  # is_detached 的点查
                if self.marker_error:
                    raise ClientError({"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "slow down"}}, "GetItem")
                return {"Item": {"run_id": "r1", "item_type": "STATE", **({"detached": True} if self.detached else {})}}
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "pending", "jobs": {},
                             **({"detached": True} if self.detached else {})}}

    _patch_skew(monkeypatch)
    for table, expect_hint in ((_Table(False), False), (_Table(True), True), (_Table(True, marker_error=True), False)):
        monkeypatch.setattr(m.compose, "_make_ddb_table", lambda t, *, region, profile, _tb=table: _tb)
        rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"])
        err = capsys.readouterr().err
        assert rc == 0 and ("可接力推进" in err) is expect_hint and "云端不可达" not in err


def test_status_cloud_pending_run_with_a_claimed_job_does_not_hint(monkeypatch, capsys):
    """云端 run 级仍 pending 但已有 job 为 running 时，推进已开始，不提示「可能未启动」。现行写者写不出这个组合（认领的同一次写即把
    run 级置为 running，ADR 0034 机制三「run 级状态只进不退」条）；这条用例守的是提示判据的后半条，它为不采用该规则的写者留下的记录而
    保留。同一个 submit 的 run 在全部 job 仍 pending 时有提示（对照），所以没有提示出自 job 的状态、不出自别的条件。"""

    class _Table:
        def __init__(self, jobs):
            self.jobs = jobs

        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "pending", "detached": True, "jobs": self.jobs}}

    _patch_skew(monkeypatch)
    claimed = {"a": {"scope_id": "a", "status": "running"}, "b": {"scope_id": "b", "status": "pending"}}
    waiting = {"a": {"scope_id": "a", "status": "pending"}, "b": {"scope_id": "b", "status": "pending"}}
    for jobs, expect_hint in ((claimed, False), (waiting, True)):
        monkeypatch.setattr(m.compose, "_make_ddb_table", lambda t, *, region, profile, _tb=_Table(jobs): _tb)
        rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"])
        assert rc == 0 and ("可接力推进" in capsys.readouterr().err) is expect_hint


def test_status_wait_cloud_exits_2_when_the_detached_marker_cannot_be_read(monkeypatch, capsys):
    """--wait 要先知道能不能接力：读标记遇到 AWS 错误时以退出码 2 结束并报云端不可达，不能当成不可接力静默等下去（那会让本该接力的
    submit run 看起来像挂住）；一次都不 invoke kicker。"""
    from botocore.exceptions import ClientError

    class _Table:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            if "ProjectionExpression" in kw:
                raise ClientError({"Error": {"Code": "InternalServerError", "Message": "boom"}}, "GetItem")
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "pending", "jobs": {}, "detached": True}}

    invoked = []

    class _Lambda:
        def invoke(self, **kw):
            invoked.append(kw)

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    monkeypatch.setattr(m.compose, "_make_lambda_client", lambda *, region, profile: _Lambda())
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--wait"])
    assert rc == 2 and invoked == [] and "云端不可达" in capsys.readouterr().err


def test_status_cloud_exits_2_when_the_definition_header_read_hits_an_aws_error(monkeypatch, capsys):
    """读 definition 头（status 的第一个云端读）遇到 AWS 错误：报云端不可达并以退出码 2 结束，不再读运行态。"""
    from botocore.exceptions import ClientError

    reads = []

    class _Table:
        def get_item(self, **kw):
            reads.append(kw["Key"]["item_type"])
            if kw["Key"]["item_type"] == "META":
                raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "denied"}}, "GetItem")
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {}}}

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2 and reads == ["META"] and "云端不可达" in capsys.readouterr().err


def test_status_cloud_exits_2_when_the_first_state_read_hits_an_aws_error(monkeypatch, capsys):
    """首次读运行态遇到 AWS 错误：带不带 --wait 都报云端不可达并以退出码 2 结束；--wait 时不读接力标记、不 invoke kicker。"""
    from botocore.exceptions import ClientError

    class _Table:
        def __init__(self):
            self.marker_reads = 0

        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            if "ProjectionExpression" in kw:
                self.marker_reads += 1
                return {"Item": {"run_id": "r1", "item_type": "STATE", "detached": True}}
            raise ClientError({"Error": {"Code": "ResourceNotFoundException", "Message": "no table"}}, "GetItem")

    invoked = []

    class _Lambda:
        def invoke(self, **kw):
            invoked.append(kw)

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_lambda_client", lambda *, region, profile: _Lambda())
    for extra in ([], ["--wait"]):
        table = _Table()
        monkeypatch.setattr(m.compose, "_make_ddb_table", lambda t, *, region, profile, _tb=table: _tb)
        rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", *extra])
        assert rc == 2 and table.marker_reads == 0 and invoked == []
        assert "云端不可达" in capsys.readouterr().err


def test_status_wait_cloud_exits_2_when_a_poll_read_hits_an_aws_error_midway(monkeypatch, capsys):
    """--wait 轮询中途重读运行态遇到 AWS 错误：报云端不可达并以退出码 2 结束，不向用户终端输出回溯。"""
    from botocore.exceptions import ClientError

    state_reads = {"n": 0}
    sleeps = []

    class _Table:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            if "ProjectionExpression" in kw:
                return {"Item": {"run_id": "r1", "item_type": "STATE", "detached": True}}
            state_reads["n"] += 1
            if state_reads["n"] >= 3:  # 首次读与第一轮重读正常，第二轮重读出错
                raise ClientError({"Error": {"Code": "InternalServerError", "Message": "boom"}}, "GetItem")
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "running", "jobs": {}, "detached": True}}

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    import time as _t
    monkeypatch.setattr(_t, "sleep", lambda s: sleeps.append(s))
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--wait"])
    assert rc == 2 and len(sleeps) == 2 and state_reads["n"] == 3
    assert "云端不可达" in capsys.readouterr().err


def test_status_wait_cloud_interrupted_by_ctrl_c_exits_130_with_a_notice(monkeypatch, capsys):
    """云端 --wait 的轮询被 Ctrl-C 打断：一句说明、退出码 130，没有回溯。"""
    class _Table:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "running", "jobs": {}, "detached": True}}

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    import time as _t

    def interrupt(s):
        raise KeyboardInterrupt

    monkeypatch.setattr(_t, "sleep", interrupt)
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--wait"])
    err = capsys.readouterr().err
    assert rc == 130 and "已停止等待" in err and "Traceback" not in err


# ---- 云端 submit 带 --expose-local：其余以退出码 2 结束的出口（ADR 0035 决策 3「云端 `submit`」）----
# 守护进程以真实的管道与线程执行（`_inline_children`）。建成、守护进程在检查前后退出、建 run 撞 AWS 错与 Ctrl-C 的用例在
# test_tunnel_cli；这里是起不来守护进程、它起隧道失败、它在回报之前崩溃与 run 已存在四个出口。

ORIGIN = "http://localhost:3000"
_PUBLIC = "https://t.ngrok-free.app"
_FIXED_RUN_ID = "20300102T030405Z-abcdef"


class _FakeTunnelService:
    """登记进 `tunnel.PROVIDERS` 的假隧道服务：只模仿口子的外部表面（前置检查、起隧道、返回对象的 close），记下起隧道与关闭。"""

    def __init__(self) -> None:
        self.starts: list = []
        self.start_error: BaseException | None = None
        self.closed = False

    def provider(self) -> "_FakeTunnelService":
        return self

    def check_prerequisites(self) -> None:
        pass

    def start(self, local_origin, *, closes_at, timeout_s=gtunnel.START_TIMEOUT_S):
        self.starts.append(closes_at)
        if self.start_error is not None:
            raise self.start_error
        return gtunnel.TunnelInfo(url=_PUBLIC, local_origin=gtunnel.normalize_origin(local_origin),
                                  warmup_url=gtunnel.warmup_url_for(_PUBLIC, "a" * 32), closer=self._close)

    def _close(self) -> None:
        self.closed = True


def _install_fake_tunnel(monkeypatch) -> _FakeTunnelService:
    service = _FakeTunnelService()
    monkeypatch.setitem(gtunnel.PROVIDERS, "ngrok", service.provider)
    return service


def _cloud_submit_argv(tmp_path: Path, *extra: str) -> list[str]:
    return ["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--ddb-table", "T", "--region", "us-east-1",
            *extra]


def test_submit_cloud_cannot_start_the_tunnel_daemon(tmp_path, monkeypatch, capsys, inline_children):
    """起不来隧道守护进程：一句说明、退出码 2、stdout 为空；没有起隧道，也没有碰 runs 表。"""
    record: list = []
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)
    service = _install_fake_tunnel(monkeypatch)
    inline_children.popen_error = OSError("Cannot allocate memory")
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert "无法启动持有隧道的本机后台进程：Cannot allocate memory。没有提交。" in cap.err
    assert service.starts == [] and made["ddb_tables"] == []


def test_submit_cloud_prints_the_daemons_tunnel_failure_as_is_and_builds_no_run(tmp_path, monkeypatch, capsys,
                                                                               inline_children):
    """守护进程起不来隧道：它回报那一句与退出码 2，submit 原样打出、退出码 2、stdout 为空，不建 run；会话没有建成，所以没有关闭调用。"""
    record: list = []
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)
    service = _install_fake_tunnel(monkeypatch)
    sentence = "隧道没有建成：authentication failed（ERR_NGROK_105）。"
    service.start_error = gtunnel.TunnelError(sentence)
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert sentence in cap.err.splitlines() and "已提交" not in cap.err
    assert made["ddb_tables"] == [] and inline_children.only().returncode == 2 and not service.closed


def test_submit_cloud_exits_2_when_the_daemon_exits_before_reporting(tmp_path, monkeypatch, capsys, inline_children):
    """守护进程在回报之前崩溃：submit 读到回报管道的文件结束，说明它退出了、没有提交，退出码 2、stdout 为空，不建 run。"""
    record: list = []
    _fake_s3, made, _ = _patch_cloud_handles(monkeypatch, record)
    service = _install_fake_tunnel(monkeypatch)
    service.start_error = RuntimeError("boom")
    inline_children.expect_crash_before_report()
    rc = m.main(_cloud_submit_argv(tmp_path, "--expose-local", ORIGIN))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert "持有隧道的本机后台进程退出了，没有提交；它退出之前如果有输出，原因在上面。处理好原因之后请重新执行。" in cap.err
    assert made["ddb_tables"] == []
    inline_children.only().expect_error(RuntimeError)


@pytest.mark.parametrize("expose", [True, False], ids=["tunneled", "plain"])
def test_submit_cloud_run_already_exists_exits_2_after_releasing_the_daemon(expose, tmp_path, monkeypatch, capsys,
                                                                           inline_children):
    """云端已有同一个 run 标识的记录：建 run 不改任何东西，submit 打出「已经存在」那一句、退出码 2、stdout 为空。带隧道时 submit 先关闭
    守护进程的标准输入、等它退出再打出这一句：守护进程没有收到 run 的标识，这句打出时它的主体已经关闭会话、返回。替身不另加等待，
    这一点由 submit 自己的等待保证。"""
    _fake_s3, _made, _ = _patch_cloud_handles(monkeypatch, [])
    service = _install_fake_tunnel(monkeypatch)
    monkeypatch.setattr(m.compose, "new_run_id", lambda at=None: _FIXED_RUN_ID)
    real_make = m.compose._make_ddb_table

    def make_occupied(table, *, region, profile):
        t = real_make(table, region=region, profile=profile)

        def put_item(**kw):  # 这个 run 的头已在：「条目不存在」的条件挡下，什么都没写
            raise t.meta.client.exceptions.ConditionalCheckFailedException()

        t.put_item = put_item
        return t

    monkeypatch.setattr(m.compose, "_make_ddb_table", make_occupied)
    sentence = f"run {_FIXED_RUN_ID} 已经存在，没有重新建立。请重新执行这条命令。"
    daemon_when_reported: list[tuple] = []
    real_progress = m._progress

    def progress(*a, **k):
        if expose and a and str(a[0]) == sentence:
            daemon_when_reported.append((service.closed, inline_children.only().returncode))
        real_progress(*a, **k)

    monkeypatch.setattr(m, "_progress", progress)
    rc = m.main(_cloud_submit_argv(tmp_path, *(["--expose-local", ORIGIN] if expose else [])))
    inline_children.settle()
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert sentence in cap.err.splitlines() and "已提交" not in cap.err
    if expose:
        child = inline_children.only()
        assert daemon_when_reported == [(True, 0)]   # 会话已关闭，主体已经返回
        assert child.returncode == 0 and child.notes == [] and service.closed
    else:
        assert inline_children.children == [] and service.starts == []


# ---- 云端后端与 worker 定位链 / steps 定制面的边界（ADR 0037 决策 3/4）----

def _spy_run_meta(monkeypatch):
    """记录 definition 构造入参（云端后端只写 DDB、不落本地文件，故从构造处取真值）。"""
    box = {}
    real = m.RunMeta

    def spy(**kwargs):
        box.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(m, "RunMeta", spy)
    return box


def test_cloud_submit_does_not_consult_local_worker(tmp_path, monkeypatch, capsys):
    """云端 submit **不查本机 worker**：不走定位链（ADR 0037 决策 3 的 miss preflight 只管本机执行），也不向本机 worker 问停止宽限下限。

    cloud 的 worker 在 Fargate 容器里运行（镜像/task-def 由 cloud preflight 探），停止宽限是 task-def 的 stopTimeout、
    够不够由 `doctor --backend cloud` 的 worker.grace 行比对；提交机器压根不必装 worker 运行时——若在此也查，
    纯 cloud 用户会被本机环境无理由挡住。
    """
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m.compose, "resolve_worker_cmd",
                        lambda engine, **kw: (_ for _ in ()).throw(
                            m.compose.WorkerNotFoundError(engine, "本机没装 worker 运行时")))
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, **kw: (_ for _ in ()).throw(
        AssertionError("云端后端不该向本机 worker 问能力自述")))
    monkeypatch.setattr(m.compose, "engine_min_grace", lambda engine: (_ for _ in ()).throw(
        AssertionError("云端后端不该向本机 worker 问停止宽限下限")))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0


def test_cloud_submit_omits_steps_dir_and_warns_when_given(tmp_path, monkeypatch, capsys):
    """云端后端：definition **不写** steps_dir（本机路径对云端 worker 无意义——steps 构建在定制镜像里，
    ADR 0037 决策 4 / 0038）；用户显式给了 `--steps-dir` 则**警告不拦**（照常提交，只是这个 flag 无效）。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    steps = tmp_path / "steps"
    steps.mkdir()
    box = _spy_run_meta(monkeypatch)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--steps-dir", str(steps),
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0                     # 警告不拦
    assert box["steps_dir"] is None    # definition 不带该字段（serialize 侧 omit-when-None）
    assert "--steps-dir 不生效" in capsys.readouterr().err


def test_cloud_submit_ignores_default_steps_dir_silently(tmp_path, monkeypatch, capsys):
    """默认 `./steps` 恰好存在时云端后端也不写、且**不警告**——用户没主动要什么，警告是噪声
    （警告只针对显式给了 --steps-dir 的「你以为生效了」误解）。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    (tmp_path / "steps").mkdir()
    monkeypatch.chdir(tmp_path)
    box = _spy_run_meta(monkeypatch)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0 and box["steps_dir"] is None
    assert "--steps-dir" not in capsys.readouterr().err


# ---- 版本 skew 闸接线（ADR 0037 决策 7）：三态映射 + 「skew 先于资源 preflight」的次序 ----
# skew 自身的判据（哪个版本组合判哪一类）在 runtime 的 test_compose 里验；这里只验前端的接线：
# 判定 → 退出码/提示，以及 block 时**资源 preflight 一次都不执行**。

def test_skew_block_stops_submit_before_resource_preflight(tmp_path, monkeypatch, capsys):
    """block → 以退出码 2 结束，且资源 preflight 一次都没执行、runs 表没碰（决策 7 的次序：skew 先）。

    次序不是审美：skew 的修复动作是部署方运行 `gherkai deploy`，那一步同时把资源建齐——先报「表/task-def
    不存在」只会把人引去查 --prefix，绕一圈回到同一个动作。
    """
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(
        monkeypatch, record, skew=("block", "版本 skew：本机 CLI 新于后端"))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2
    assert preflight_calls == [], "block 时不该再探资源"
    assert not [r for r in record if r[0] == "ddb"], "block 时不该碰 runs 表"
    assert "版本 skew" in capsys.readouterr().err


def test_skew_block_stops_status_before_reading_ddb(monkeypatch, capsys):
    """status 同受闸（cloud 各入口一致）：block 时连 DDB 都不读。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record, skew=("block", "版本 skew：本机 CLI 新于后端"))
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2
    assert not [r for r in record if r[0] == "ddb"]
    assert "版本 skew" in capsys.readouterr().err


def test_skew_warn_and_skip_pass_through_with_one_line(tmp_path, monkeypatch, capsys):
    """warn（戳缺失 / CLI 偏旧）与 skip（dev 版）都只打一行、照常往下执行——决策 7 里这两种情形不拦。"""
    for verdict in ("warn", "skip"):
        record: list = []
        _, _, preflight_calls = _patch_cloud_handles(
            monkeypatch, record, skew=(verdict, f"提示：{verdict} 判定一行"))
        rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                     "--ddb-table", "T", "--region", "us-east-1"])
        assert rc == 0, verdict
        assert len(preflight_calls) == 1, verdict          # 闸放行 → 资源 preflight 照常执行
        assert f"提示：{verdict} 判定一行" in capsys.readouterr().err


def test_skew_ok_is_silent(tmp_path, monkeypatch, capsys):
    """ok 这一类不打任何东西（同版本是常态，别在每次提交上加噪声）。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record, skew=("ok", ""))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0 and "版本" not in capsys.readouterr().err


def test_skew_reads_stamp_with_resolved_prefix(tmp_path, monkeypatch):
    """读戳用的是**已解析的 prefix**（与 variant 映射同一族路径 `/{prefix}backend/*`，故无需新增授权）。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "stage-",
            "--ddb-table", "T", "--region", "us-east-1"])
    assert ("ssm", "read_backend_version", "stage-") in record


def test_skew_real_judgement_end_to_end(tmp_path, monkeypatch, capsys):
    """接线的真判定一次（只 stub 读戳与 CLI 自报版本，skew 判定用真函数）：新于 → 以退出码 2 结束且给两条出路。"""
    from gherkai_runtime.compose import check_version_skew as real_check

    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m.compose, "check_version_skew", real_check)  # 用真判定
    monkeypatch.setattr(m.compose, "read_backend_version", lambda **kw: "1.2.0")
    monkeypatch.setattr(m, "_installed_version", lambda: "9.9.9")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2 and preflight_calls == []
    err = capsys.readouterr().err
    assert "gherkai deploy" in err and "uvx --from 'gherkai==1.2.0'" in err

    # 同版本 → 放行且静默（同一条真判定，证不是「恒 block」）
    monkeypatch.setattr(m, "_installed_version", lambda: "1.2.0")
    rc2 = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc2 == 0 and len(preflight_calls) == 1
    assert "版本不一致" not in capsys.readouterr().err


def test_skew_read_failure_exits_2_naming_the_parameter(tmp_path, monkeypatch, capsys):
    """读戳撞非 ParameterNotFound 的 AWS 错（凭证/region/权限）→ 以退出码 2 结束且点名参数路径。

    不静默跳过：决策 7 的 block 这一类没有放行口，「读不到就放过」等于给它开了一个。
    """
    from botocore.exceptions import ClientError

    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)

    def boom(**kwargs):
        raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "GetParameter")

    monkeypatch.setattr(m.compose, "read_backend_version", boom)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 2 and preflight_calls == []
    assert "/gherkai-backend/version" in capsys.readouterr().err


# ---- worker 镜像 variant 闸接线 ----
# 解析本体（读 SSM 映射 / revision ACTIVE / ECR digest 存在）在 runtime 的 compose 测试里验；这里只验前端：
# 次序（skew → 资源 preflight → variant）、退出码 2、解析结果进 definition、打印（ADR 0038「运行时与 preflight」的
# 「选择进 definition」条与 preflight 条）。

def _two_engine_feature(tmp_path: Path) -> Path:
    """两个 scope 各走一个引擎 → 本 run「真用到」两个引擎（验 engines 参数按 job 取、不探全注册表）。"""
    feat = tmp_path / "two.feature"
    feat.write_text(
        "Feature: F\n"
        "  @scope:a @engine:novaact\n  Scenario: s1\n    When \"做 A\"\n"
        "  @scope:b @engine:midscene\n  Scenario: s2\n    When \"做 B\"\n",
        encoding="utf-8")
    return feat


def test_submit_cloud_resolves_default_variant_into_definition(tmp_path, monkeypatch, capsys):
    """不给 --worker-variant：解析到部署级默认指针，人读的 variant 名与引擎 → revision ARN 一起落 definition
    （云端推进器只用 definition 里的显式 revision 起 task，ADR 0038）。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0
    assert made["variant"][0]["variant"] is None   # 没给 flag：交给解析取默认指针
    meta = _definition(made["ddb_tables"][0])
    assert meta["worker_variant"] == "base"
    assert meta["worker_task_defs"] == {"novaact": _stub_revision("novaact")}


def test_submit_cloud_resolves_variant_into_definition(tmp_path, monkeypatch, capsys):
    """submit cloud 只写 definition（不起 task）——variant 必须写进去，否则云端推进器无从起 task。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1", "--worker-variant", "login"])
    assert rc == 0
    assert made["variant"][0]["variant"] == "login"
    meta = _definition(made["ddb_tables"][0])
    assert meta["worker_variant"] == "login"
    assert meta["worker_task_defs"] == {"novaact": _stub_revision("novaact")}


def test_variant_gate_only_probes_engines_the_run_uses(tmp_path, monkeypatch, capsys):
    """engines 参数是 **本 run 真用到的引擎**（对齐既有 task-def 判据「不探全注册表」，ADR 0038）：
    单引擎 run 不问另一个引擎（单引擎团队不必为它凭空推镜像）；两引擎 run 两个都问、都进 definition。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0
    assert made["variant"][0]["engines"] == ["novaact"]

    record2: list = []
    _, made2, _ = _patch_cloud_handles(monkeypatch, record2)
    rc = m.main(["submit", str(_two_engine_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0
    assert made2["variant"][0]["engines"] == ["midscene", "novaact"]
    meta = _definition(made2["ddb_tables"][0])
    assert meta["worker_task_defs"] == {"novaact": _stub_revision("novaact"),
                                        "midscene": _stub_revision("midscene")}


def test_variant_gate_reuses_the_one_stamp_read(tmp_path, monkeypatch, capsys):
    """**戳只读一次**：skew 闸读的那个戳原样喂给 variant 解析（提示语要按 skew 分叉，ADR 0038）——
    不再为提示语二次读同一个 SSM 参数。同时验 cli_version/prefix 传的是已解析值。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "_installed_version", lambda: "1.4.0")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--prefix", "stage-",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0
    reads = [r for r in record if r[:2] == ("ssm", "read_backend_version")]
    assert len(reads) == 1, "戳该只读一次（skew 闸读、variant 解析复用）"
    kw = made["variant"][0]
    assert kw["backend_version"] == "<stub 版本戳>"   # 即 _patch_skew 那次读的返回值
    assert kw["cli_version"] == "1.4.0" and kw["prefix"] == "stage-"
    assert kw["region"] == "us-east-1"


def test_variant_missing_exits_2_with_the_errors_message(tmp_path, monkeypatch, capsys):
    """variant 在某引擎缺映射 → 以退出码 2 结束且原样转述 WorkerVariantError 的提示语，**不回落默认**
    （静默换一套确定性 step 集是 ADR 0038 明拒的）；挡在写提交记录之前。"""
    from gherkai_runtime.compose import WorkerVariantError

    err = WorkerVariantError("variant 'login' 在引擎 midscene 尚无镜像：gherkai deploy push-worker …")
    record: list = []
    _patch_cloud_handles(monkeypatch, record, variant_err=err)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--worker-variant", "login",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 2
    assert "push-worker" in capsys.readouterr().err
    assert not [r for r in record if r[0] == "ddb"], "拦下时不该碰 runs 表（挡在 create_run 前）"


def test_variant_resolution_read_failure_exits_2(tmp_path, monkeypatch, capsys):
    """解析时撞 AWS 错（凭证/权限/region）→ 以退出码 2 结束并点名读的是哪族参数，不冒 traceback。"""
    from botocore.exceptions import ClientError

    record: list = []
    _patch_cloud_handles(monkeypatch, record, variant_err=ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "GetParameter"))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--prefix", "stage-"])
    assert rc == 2
    assert "/stage-backend/worker-" in capsys.readouterr().err


# ---- 次序：skew → 资源 preflight → variant（ADR 0038）----

def test_skew_block_prevents_both_resource_preflight_and_variant(tmp_path, monkeypatch, capsys):
    """skew block 时资源 preflight 与 variant 解析都一次不执行——skew 的修复动作（deploy）是镜像重推的前置，
    反过来先报「variant 没推」会让用户先推一轮镜像、推完仍要重做（ADR 0038）。"""
    record: list = []
    _, made, preflight_calls = _patch_cloud_handles(
        monkeypatch, record, skew=("block", "版本 skew：本机 CLI 新于后端"))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 2
    assert preflight_calls == [] and made["variant"] == []


def test_resource_preflight_failure_prevents_variant_resolution(tmp_path, monkeypatch, capsys):
    """资源 preflight 不过时不再解析 variant（ADR 0038 的位置：既有 preflight 之后）——
    表/cluster 都不在的环境里报「variant 没推」是把人往错方向引。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record, preflight_err="资源缺失：ECS cluster …")
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 2
    assert made["variant"] == []


def test_status_does_not_resolve_variant(monkeypatch, capsys):
    """status 不解析 variant（ADR 0038）：它只读运行态、不起 task，definition 里的 revision 提交时已定死。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)

    class _DoneTable:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {}}}

    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _DoneTable())
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 0
    assert made["variant"] == []


# ---- 打印（可见性）----

def test_variant_resolution_prints_one_line_per_engine(tmp_path, monkeypatch, capsys):
    """通过则每引擎一行「variant · digest · revision」（ADR 0038「通过则打印各引擎解析到的 variant / digest」）：
    digest 缩到前 12 位（整串 71 字符会把 revision 挤出屏幕）。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_two_engine_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1", "--worker-variant", "login"])
    assert rc == 0
    err = capsys.readouterr().err
    for engine in ("novaact", "midscene"):
        assert f"{engine}: variant login · digest sha256:{'ab' * 6} · revision {_stub_revision(engine)}" in err


# ---- 入口校验 + 本机后端忽略（ADR 0038）----

def test_worker_variant_invalid_name_exits_2_before_any_cloud_call(tmp_path, monkeypatch, capsys):
    """名字不合 tag 字符集 → 入口就以退出码 2 结束（对齐 --max-concurrency 的入口校验惯例）：真零副作用——
    连读戳都没发生。校验点复用 names.image_tag（ADR 0038「tag 命名」条）。"""
    record: list = []
    _, made, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    for bad in ("有中文", "-leading-dash", "bad name", ".dotfirst"):
        # `=` 形式给值：`-` 开头的值用空格分隔会被 argparse 当成另一个 flag（与本校验无关的前端侧现实）
        rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                     "--region", "us-east-1", f"--worker-variant={bad}"])
        assert rc == 2, bad
        assert "--worker-variant 无效" in capsys.readouterr().err
    assert record == [] and preflight_calls == [] and made["variant"] == []


def test_worker_variant_valid_names_pass_entry_validation(tmp_path, monkeypatch, capsys):
    """合法名放行（字母数字下划线开头，其后可含 `.` `-`）——校验不能宽到放过坏名、也不能严到误拦正常名。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    for good in ("base", "login", "checkout-v2", "v1.2_x"):
        rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                     "--ddb-table", "T", "--region", "us-east-1", "--worker-variant", good])
        assert rc == 0, good
    assert [c["variant"] for c in made["variant"]] == ["base", "login", "checkout-v2", "v1.2_x"]


def test_local_submit_ignores_worker_variant_with_one_note(tmp_path, monkeypatch, capsys, inline_children):
    """本机后端的 submit 忽略该 flag、只打一行提示（不拦、不校验——local 的确定性 step 直接从 steps 目录读、不经镜像）。
    run 不收这个 flag，见 test_run_and_submit_do_not_accept_cloud_execution_flags。后台推进进程在线程里执行，推进换成记录调用的函数。"""
    from gherkai_runtime import detached

    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    advanced: list = []
    monkeypatch.setattr(detached, "advance_local_run", lambda advancer, meta, **kw: advanced.append(meta))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"),
                 "--worker-variant", "login"])
    inline_children.settle()
    assert rc == 0
    assert "--worker-variant 不生效" in capsys.readouterr().err
    assert made["variant"] == []      # local 从不解析
    assert record == []               # 也没碰任何云端读
    assert len(advanced) == 1 and advanced[0].worker_variant is None


def test_local_definition_omits_worker_variant_fields(tmp_path, monkeypatch, capsys):
    """local run 的 definition 里这两个字段为 null（键集固定；本机后端不写值，见 ADR 0038「选择进 definition」条）。"""
    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    report_dir = tmp_path / "r"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(report_dir), "--quiet", "--json"])
    assert rc == 0
    meta_files = list(report_dir.glob("*/run_meta.json"))
    assert len(meta_files) == 1
    doc = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert doc["worker_variant"] is None and doc["worker_task_defs"] is None


def test_bad_default_pointer_name_exits_2_pointing_at_the_parameter(tmp_path, monkeypatch, capsys):
    """后端默认指针本身是个非法 variant 名（部署侧写坏）→ 以退出码 2 结束并点名那个 SSM 参数，不冒 traceback。

    显式 `--worker-variant` 的坏名字在入口就被拦（见上），故这条 ValueError 只可能来自后端的默认指针。
    """
    record: list = []
    _patch_cloud_handles(monkeypatch, record,
                         variant_err=ValueError("variant 名不合法：'有中文'——须匹配 …"))
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--region", "us-east-1", "--prefix", "stage-"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "/stage-backend/worker-default" in err and "不合法" in err


def test_status_cloud_terminal_prints_s3_and_ddb_locations(monkeypatch, capsys):
    """cloud status 到终态打出与本机 run 结束时同一形态的位置行（s3:// 报告与判定明细、ddb:// 元信息），
    落点按 --prefix 推理出的桶/表与 --report-dir 前缀拼——用户不用自己拼 S3 路径。"""
    class _PassedTable:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {},
                             "ended_at": "2026-09-10T04:28:41+00:00"}}

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _PassedTable())
    rc = m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "报告: s3://gherkai-artifacts/reports/r1/index.html" in err
    assert "判定明细: s3://gherkai-artifacts/reports/r1/jobs/" in err
    assert "ddb://gherkai-runs/r1#META" in err


def test_status_cloud_json_includes_artifact_locations(monkeypatch, capsys):
    """status --json 附加 artifacts：RunState 部分形状不变，多一个键给报告/判定明细/元信息位置。"""
    class _PassedTable:
        def get_item(self, **kw):
            if kw["Key"]["item_type"] == "META":
                return _META_HEADER
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {}}}

    _patch_skew(monkeypatch)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _PassedTable())
    assert m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1", "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["run_id"] == "r1" and doc["status"] == "passed"
    assert doc["artifacts"]["report_index"] == "s3://gherkai-artifacts/reports/r1/index.html"
    assert doc["artifacts"]["jobs_dir"] == "s3://gherkai-artifacts/reports/r1/jobs/"
    assert doc["artifacts"]["run_meta"] == "ddb://gherkai-runs/r1#META"


# ---- 运行期限进 definition（ADR 0054 决策二）：云端后端的每 job 尾段固定 210 秒，不看停止宽限 ----
def _deadline_offset_s(meta: dict) -> float:
    from datetime import datetime
    return (datetime.fromisoformat(meta["deadline_at"]) - datetime.fromisoformat(meta["created_at"])).total_seconds()


def test_cloud_submit_writes_deadline_with_the_cloud_per_job_tail(tmp_path, monkeypatch, capsys):
    """云端 submit：期限是创建时刻加 900 秒、再加各 job 的预算与 210 秒之和，两个 job 各算一份；META 条目另把它摊成顶层属性。"""
    record: list = []
    _, made, _ = _patch_cloud_handles(monkeypatch, record)
    rc = m.main(["submit", str(_two_engine_feature(tmp_path)), "--backend", "cloud", "--default-job-timeout", "600",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0
    meta = _definition(made["ddb_tables"][0])
    assert _deadline_offset_s(meta) == 900 + 2 * (600 + 210)
    [item] = [it for it in made["ddb_tables"][0].puts if it.get("item_type") == "META"]
    assert item["deadline_at"] == meta["deadline_at"]

    record2: list = []
    _, made2, _ = _patch_cloud_handles(monkeypatch, record2)
    rc = m.main(["submit", str(_two_engine_feature(tmp_path)), "--backend", "cloud",
                 "--ddb-table", "T", "--region", "us-east-1"])
    assert rc == 0
    assert _deadline_offset_s(_definition(made2["ddb_tables"][0])) == 900 + 2 * (300 + 210)  # 桌面缺省预算 300
