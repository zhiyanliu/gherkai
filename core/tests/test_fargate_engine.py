"""FargateEngine adapter 单测（ADR 0034「Engine port 演进」节、ADR 0024「远程传输演进」节）。

FargateEngine 只有 `start_scope`：上传 job 到 S3、发 RunTask、返回 task ARN。这里用 `fargate` fixture（moto）测 RunTask 的参数与
env 注入、job 对象的键与 tag、放置失败的报错——moto 对这些编排调用忠实。task 能否真起来只有真部署之后的云端 submit 能证。
读 events 表的一方是 `DdbEventLog`，其测试在 test_cloud_reconcile.py。
"""
from __future__ import annotations

import json
from urllib.parse import quote

import pytest

from gherkai_core.adapters.fargate_engine import FargateEngine, events_pk
from gherkai_core.model import Job, Scenario, Step


_RUN_ID = "20260707T120000Z-abc123"


def _job(scope_id: str = "browse") -> Job:
    return Job(
        scope_id=scope_id, scope_name=scope_id, engine="novaact",
        scenarios=(Scenario(id="sc:0", name="s", steps=(Step(index=0, keyword="When", text='"做事"'),)),),
        assertion_votes=1, timeout_s=300.0,
    )


def _engine(fargate, run_id: str = _RUN_ID, region: str | None = None,
            artifact_s3: tuple[str, str] | None = None, sdk_artifact_dir_env: dict | None = None,
            extra_env: dict | None = None) -> FargateEngine:
    return FargateEngine(
        ecs_client=fargate["ecs"], s3_client=fargate["s3"],
        run_id=run_id, cluster=fargate["cluster"], task_definition=fargate["task_def"],
        network_config=fargate["network_config"], job_s3=(fargate["bucket"], f"{run_id}/jobs-in/"),
        events_table_name=fargate["events_table_name"], container_name=fargate["container_name"],
        artifact_s3=artifact_s3, sdk_artifact_dir_env=sdk_artifact_dir_env, extra_env=extra_env, region=region,
        # 不接 profile——容器用 task role
    )


def _spy_run_task(fargate, monkeypatch) -> dict:
    """拦 ecs.run_task（仍转给 moto 真起 task），返回记下的那次调用参数。"""
    real = fargate["ecs"].run_task
    captured: dict = {}
    monkeypatch.setattr(fargate["ecs"], "run_task", lambda **kw: captured.update(kw) or real(**kw))
    return captured


def _start_and_capture_env(fargate, monkeypatch, eng) -> dict:
    """执行 start_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。"""
    captured = _spy_run_task(fargate, monkeypatch)
    eng.start_scope(_job("browse"))
    return {e["name"]: e["value"] for e in captured["overrides"]["containerOverrides"][0]["environment"]}


# ---- events_pk：复合键防重复运行相撞（ADR 0024）----
def test_events_pk_composite_run_id_scope_id():
    assert events_pk("run-A", "browse") == "run-A#browse"
    # 同 feature 重复运行（scope_id 同、run_id 异）→ PK 不同、不撞
    assert events_pk("run-A", "browse") != events_pk("run-B", "browse")


# ---- 对外只有 start_scope：云端后端只有后台推进（ADR 0016 决策 A；ADR 0034「Engine port 演进」节）----
def test_fargate_engine_offers_only_start_scope_and_no_engine_port():
    """FargateEngine 对外只有 start_scope，没有 `Engine` port 的 run_scope：它不能被注入 schedule 去同步消费 worker 的事件流，
    云端 run 只由推进器从 events 表重放推进。重新加上返回事件迭代器的入口、或别的对外方法，本用例即红。"""
    public = sorted(name for name, value in vars(FargateEngine).items() if callable(value) and not name.startswith("_"))
    assert public == ["start_scope"]
    assert not hasattr(FargateEngine, "run_scope")


# ---- start_scope：PutObject job + RunTask 注入 env（moto 忠实）----
def test_start_scope_puts_job_to_s3_and_returns_task_arn(fargate):
    eng = _engine(fargate)
    task_arn = eng.start_scope(_job())
    # 返回 moto 真起的那个 task 的 ARN（调用方不轮询、不读事件，只拿它）
    tasks = fargate["ecs"].list_tasks(cluster=fargate["cluster"])["taskArns"]
    assert task_arn in tasks
    # job 已 PutObject 到 s3://bucket/<run_id>/jobs-in/<scope_id>.json，内容就是 job_to_line 的输出
    obj = fargate["s3"].get_object(Bucket=fargate["bucket"], Key=f"{_RUN_ID}/jobs-in/browse.json")
    body = obj["Body"].read().decode("utf-8").strip()
    assert json.loads(body)["scope"]["id"] == "browse"


def test_start_scope_job_key_quotes_scope_id(fargate):
    # scope_id 含 `/`:（如 feature 路径 features/x.feature:7）→ job key 用 quote(safe='')：/ 编码成 %2F、: 成 %3A，
    # 不造 S3 假子前缀、与 S3ResultStore（同 quote）一致（实际运行暴露的一致性缺陷回归守卫）。
    eng = _engine(fargate)
    sid = "features/deterministic_step.feature:7"
    eng.start_scope(_job(sid))
    expected_key = f"{_RUN_ID}/jobs-in/{quote(sid, safe='')}.json"  # features%2Fdeterministic_step.feature%3A7.json
    obj = fargate["s3"].get_object(Bucket=fargate["bucket"], Key=expected_key)  # 能取到就说明 key 用了 quote
    assert json.loads(obj["Body"].read().decode("utf-8"))["scope"]["id"] == sid
    assert "%2F" in expected_key and "%3A" in expected_key  # 确认 / 和 : 都被编码（不造子前缀）


def test_start_scope_job_in_tagged_for_lifecycle(fargate):
    # job-in 对象打 tag gherkai=job-in，供桶按 tag 挂 S3 lifecycle 过期清理（ADR 0033「job-in S3 对象生命周期」条；tag 而非
    # key 前缀，因 run_id 在 key 中间、前缀 filter 框不住且会误伤 jobs/reports）。回归守卫：防将来漏打 tag → lifecycle 收不到、job-in 堆积。
    eng = _engine(fargate)
    sid = "features/x.feature:1"
    eng.start_scope(_job(sid))
    key = f"{_RUN_ID}/jobs-in/{quote(sid, safe='')}.json"
    tags = fargate["s3"].get_object_tagging(Bucket=fargate["bucket"], Key=key)["TagSet"]
    assert {"Key": "gherkai", "Value": "job-in"} in tags, f"job-in 对象缺 gherkai=job-in tag：{tags}"


def test_start_scope_runtask_injects_env(fargate, monkeypatch):
    # 拦 ecs.run_task 记录 env 注入（验 JOB_S3_URI/EVENTS_DDB_TABLE/RUN_ID/SCOPE_ID 都传对）与 RunTask 的其余参数
    captured = _spy_run_task(fargate, monkeypatch)
    _engine(fargate).start_scope(_job("browse"))
    # env 注入在 containerOverrides，指名的是 worker container
    override = captured["overrides"]["containerOverrides"][0]
    assert override["name"] == fargate["container_name"]
    env = {e["name"]: e["value"] for e in override["environment"]}
    assert env["RUN_ID"] == _RUN_ID
    assert env["SCOPE_ID"] == "browse"
    assert env["EVENTS_DDB_TABLE"] == fargate["events_table_name"]
    assert env["JOB_S3_URI"] == f"s3://{fargate['bucket']}/{_RUN_ID}/jobs-in/browse.json"
    assert captured["launchType"] == "FARGATE"
    assert captured["taskDefinition"] == fargate["task_def"]  # 原样传入的显式 revision ARN（ADR 0038），不做名字推导
    assert captured["cluster"] == fargate["cluster"]
    assert captured["networkConfiguration"] == {"awsvpcConfiguration": fargate["network_config"]}
    assert captured["count"] == 1


def test_start_scope_injects_extra_env(fargate, monkeypatch):
    # extra_env（ADR 0035）：组合根算好的通用附加 env（如 GHERKAI_EXTRA_HTTP_HEADERS）逐条注 RunTask overrides
    eng = _engine(fargate, extra_env={"GHERKAI_EXTRA_HTTP_HEADERS": '{"ngrok-skip-browser-warning": "1"}'})
    env = _start_and_capture_env(fargate, monkeypatch, eng)
    assert env["GHERKAI_EXTRA_HTTP_HEADERS"] == '{"ngrok-skip-browser-warning": "1"}'


def test_artifact_injection_kwargs_are_mandatory(fargate):
    """产物落点两参数**必给关键字、无缺省**：cloud 下两者必注，漏传即静默丢产物（实际运行暴露过一次）。

    与 ADR 0038 的显式 revision 判法一致——漏传即在装配点抛 TypeError，不做成「忘了传就静默破」。
    显式给 None（不上传）/ 空 dict（无 SDK 落点）仍可构造：本条锁的是「不许省」，不是「不许为空」。
    """
    base = dict(
        ecs_client=fargate["ecs"], s3_client=fargate["s3"],
        run_id=_RUN_ID, cluster=fargate["cluster"], task_definition=fargate["task_def"],
        network_config=fargate["network_config"], job_s3=(fargate["bucket"], f"{_RUN_ID}/jobs-in/"),
        events_table_name=fargate["events_table_name"], container_name=fargate["container_name"],
        artifact_s3=None, sdk_artifact_dir_env={},
    )
    assert FargateEngine(**base) is not None  # 前提：显式给空值照样构造得出
    for omitted in ("artifact_s3", "sdk_artifact_dir_env"):
        with pytest.raises(TypeError):
            FargateEngine(**{k: v for k, v in base.items() if k != omitted})  # type: ignore[call-arg]


def test_start_scope_sets_started_by_run_id(fargate, monkeypatch):
    # startedBy=run_id（ADR 0034「job timeout」节）：超时处置用 ListTasks(startedBy=run_id) 定位本 run 的
    # task（≤36 字符：run_id 形如 20260707T120000Z-abc123 共 23 字符）。
    captured = _spy_run_task(fargate, monkeypatch)
    _engine(fargate).start_scope(_job())
    assert captured["startedBy"] == _RUN_ID


def test_start_scope_injects_region_never_profile(fargate, monkeypatch):
    # region 非 None（部署所在区域，ADR 0016 决策 C）→ overrides env 注入 AWS_REGION，与推进器 store 句柄同一个 region。
    # Fargate 容器不继承宿主 env、不吃 profile config，不注入 region 则 worker → NoRegionError/AgentCore InvalidRegionError。
    # **AWS_PROFILE 绝不注入**（正确的非对称）：容器用 task role，注入 profile 名会 ProfileNotFound 盖过 task role。
    env = _start_and_capture_env(fargate, monkeypatch, _engine(fargate, region="us-west-2"))
    assert env["AWS_REGION"] == "us-west-2"
    assert "AWS_PROFILE" not in env  # FargateEngine 根本不接 profile 参数、绝不注入


def test_start_scope_omits_region_when_none(fargate, monkeypatch):
    # region=None（真无 region）→ 不注入（不硬写空值、留 fail-loud）。AWS_PROFILE 同样从不注入。
    env = _start_and_capture_env(fargate, monkeypatch, _engine(fargate, region=None))
    assert "AWS_REGION" not in env
    assert "AWS_PROFILE" not in env


def test_start_scope_injects_artifact_s3_env(fargate, monkeypatch):
    # artifact_s3 非 None（cloud 必注入，ADR 0029）→ overrides env 注入 ARTIFACT_S3_BUCKET/PREFIX，worker
    # ArtifactUploader 据此上传→报 s3://→删本地。**不注入则容器盘停即销毁、产物必丢**（ADR 0029/0032）——这条守卫防回归。
    env = _start_and_capture_env(fargate, monkeypatch, _engine(fargate, artifact_s3=("bkt", "reports/rid-1/")))
    assert env["ARTIFACT_S3_BUCKET"] == "bkt"
    assert env["ARTIFACT_S3_PREFIX"] == "reports/rid-1/"


def test_start_scope_omits_artifact_s3_when_none(fargate, monkeypatch):
    # artifact_s3=None（不上传，如无 report 落点）→ 不注入 ARTIFACT_S3_*（worker no-op 报 file://）。
    env = _start_and_capture_env(fargate, monkeypatch, _engine(fargate, artifact_s3=None))
    assert "ARTIFACT_S3_BUCKET" not in env
    assert "ARTIFACT_S3_PREFIX" not in env


def test_start_scope_injects_sdk_artifact_dir_env(fargate, monkeypatch):
    # SDK 产物落点 env（NOVA_LOGS_DIR 等）也须注入——**否则 worker ArtifactUploader run_dir=None→no-op→产物随容器盘销毁丢**
    # （实际运行暴露：只注 ARTIFACT_S3_* 不够，uploader 还要 SDK 落点 env 算 run_dir/相对 key）。这条守卫防回归。
    env = _start_and_capture_env(fargate, monkeypatch,
                                 _engine(fargate, sdk_artifact_dir_env={"NOVA_LOGS_DIR": "/tmp/gherkai-run/rid/nova-trajectories"}))
    assert env["NOVA_LOGS_DIR"] == "/tmp/gherkai-run/rid/nova-trajectories"


# ---- run_task 放置失败（failures 非空）→ 明确异常，非裸 IndexError ----
def test_start_scope_runtask_failure_raises_meaningful_error(fargate, monkeypatch):
    """RunTask 容量不足/子网无 IP 等 → HTTP 200 + 空 tasks + failures。须翻成带 reason 与 detail 的明确异常，非 IndexError。"""
    monkeypatch.setattr(fargate["ecs"], "run_task",
                        lambda **kw: {"tasks": [], "failures": [{"reason": "RESOURCE:MEMORY", "detail": "no capacity"}]})
    eng = _engine(fargate)
    with pytest.raises(RuntimeError, match="RESOURCE:MEMORY.*no capacity"):
        eng.start_scope(_job("browse"))
