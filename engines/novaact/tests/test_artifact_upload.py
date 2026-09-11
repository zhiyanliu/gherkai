"""ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-op 报 file://。

mock boto3 client（不连真 AWS、不加 moto 依赖）。重点护 ADR 0029：
- **key 镜像本地 run 树** + **ref 与上传 key 逐字一致**（否则 index 链接断）。
- **两级时机**：to_report_ref 实时传（不删）；flush_and_cleanup scope 末传剩余（跳过已传）+ 全成功才删整目录。
- **整目录传，不按文件挑**（抗 SDK 升级）：flush walk 整目录，log/.json 一并传。
- **失败护栏**：reportRef 实时传失败抛（可观测）；剩余 flush 失败吞掉但整目录不删；全成功才 rmtree。
- **no-op**：无 ARTIFACT_S3_BUCKET → 报 file://、不上传、不删。
- **后台队列**（ADR 0042 决策一）：enqueue 的 key 与 `ref_for` 先算的 URI 逐字一致（否则 evidence 里的截图 URI
  悬空）、FIFO、失败重试一次后一行日志放弃、成功让 flush 跳过、drain 有界（超时返 False，剩下的交给 flush）。
"""
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

from gherkai_worker_novaact.lib.artifact_upload import ArtifactUploader


class _Calls(list):
    """upload_file 调用记录：list 元素 = (local, bucket, key)，`extra_by_key` 另记 ExtraArgs。"""

    def __init__(self) -> None:
        super().__init__()
        self.extra_by_key: dict = {}


def _uploader_with_mock(bucket, prefix, run_dir, *, fail_keys=(), fail_times=None, delay_s=0.0):
    """造 uploader + 塞 mock s3 client（记录 upload_file 调用）。

    `fail_keys`：该 key 每次都抛（永久失败）。`fail_times`：{key: 前 N 次抛}（测「重试一次即成」）。
    `delay_s`：每次上传睡这么久（测 drain 的有界性——队列在途时 drain 应超时返 False）。
    """
    u = ArtifactUploader(bucket=bucket, prefix=prefix, run_dir=Path(run_dir))
    client = MagicMock()
    calls = _Calls()
    left = dict(fail_times or {})

    def _upload(local, bkt, key, ExtraArgs=None):  # noqa: N803  boto3 的形参名就是驼峰
        calls.append((local, bkt, key))
        calls.extra_by_key[key] = ExtraArgs
        if delay_s:
            time.sleep(delay_s)
        if key in fail_keys:
            raise RuntimeError(f"s3 fail: {key}")
        if left.get(key):
            left[key] -= 1
            raise RuntimeError(f"s3 flaky: {key}")

    client.upload_file.side_effect = _upload
    u._client = client
    return u, calls


# ---- no-op（无落点 env）：报 file://、不上传、不删、flush 是 no-op ----
def test_noop_reports_file_uri_and_no_delete(tmp_path):
    f = tmp_path / "nova-trajectories" / "sess" / "act_0.html"
    f.parent.mkdir(parents=True); f.write_text("html")
    u = ArtifactUploader(bucket=None, prefix="reports/rid/", run_dir=tmp_path)
    assert u.enabled is False
    assert u.to_report_ref(str(f)) == f"file://{f}"  # 裸 abspath、不 resolve
    u.flush_and_cleanup(tmp_path / "nova-trajectories")
    assert f.exists()  # no-op 不碰本地


def test_noop_preserves_bare_path_no_symlink_resolve():
    u = ArtifactUploader(bucket=None, prefix="", run_dir=None)
    assert u.to_report_ref("/tmp/foo/bar.html") == "file:///tmp/foo/bar.html"


# ---- to_report_ref：实时传（不删）、key 镜像 run 树、ref 逐字一致 ----
def test_report_ref_uploads_realtime_key_mirrors_tree_no_delete(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "sess"
    art.mkdir(parents=True)
    f = art / "act_0.html"; f.write_text("traj")
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    ref = u.to_report_ref(str(f))
    expected_key = "reports/rid/nova-trajectories/sess/act_0.html"
    assert calls == [(str(f), "bkt", expected_key)]           # 实时传、key 镜像 run 树
    assert ref == f"s3://bkt/{expected_key}"                  # ref 与 key 逐字一致（0029 主验）
    assert f.exists()                                         # 实时传**不删**（留到 flush 整目录删）


# ---- flush_and_cleanup：传剩余（跳过已传）+ 全成功删整目录 ----
def test_flush_uploads_rest_skips_uploaded_and_deletes_dir(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "sess"
    art.mkdir(parents=True)
    html = art / "act_0.html"; html.write_text("traj")           # reportRef 文件（实时传）
    js = art / "act_0_trajectory.json"; js.write_text("{}")      # 剩余（flush 传）
    log = run_dir / "nova-trajectories" / "run.log"; log.write_text("log")  # 剩余（flush 传，非产物也传）
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    u.to_report_ref(str(html))          # 实时传 html
    u.flush_and_cleanup(run_dir / "nova-trajectories")
    uploaded_keys = {c[2] for c in calls}
    # html 只传一次（实时；flush 跳过）；json + log 由 flush 传（整目录、不按文件挑）
    assert "reports/rid/nova-trajectories/sess/act_0.html" in uploaded_keys
    assert "reports/rid/nova-trajectories/sess/act_0_trajectory.json" in uploaded_keys
    assert "reports/rid/nova-trajectories/run.log" in uploaded_keys
    assert sum(1 for c in calls if c[2].endswith("act_0.html")) == 1  # html 不重复传
    # 全部成功 → 整目录删（本地零残留，含 log/.json）
    assert not (run_dir / "nova-trajectories").exists()


# ---- 幂等：已成功传的文件再调 to_report_ref → 不重传、直接返 s3:// ref（ADR 0029 幂等去重）----
def test_report_ref_idempotent_no_reupload(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "sess"
    art.mkdir(parents=True)
    f = art / "act_0.html"; f.write_text("traj")
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    ref1 = u.to_report_ref(str(f))   # 首次：真传
    ref2 = u.to_report_ref(str(f))   # 再调（模拟 except 重建 reportRefs）：幂等短路、不重传
    assert ref1 == ref2
    assert len(calls) == 1, "已传文件再调不应重复 upload"


# ---- reportRef 实时传失败 → 抛（可观测），本地不删 ----
def test_report_ref_upload_failure_raises_and_keeps_local(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "midscene-run"  # 借 run 树内任意路径
    art.mkdir(parents=True)
    f = art / "x.html"; f.write_text("html")
    key = "reports/rid/midscene-run/x.html"
    u, _ = _uploader_with_mock("bkt", "reports/rid/", run_dir, fail_keys={key})
    try:
        u.to_report_ref(str(f))
        assert False, "reportRef 实时传失败应抛"
    except RuntimeError:
        pass
    assert f.exists()  # 失败不删


# ---- 剩余 flush 失败 → 吞掉，但整目录不删（护栏：产物不丢）----
def test_flush_failure_swallowed_but_dir_kept(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "sess"
    art.mkdir(parents=True)
    html = art / "act_0.html"; html.write_text("traj")
    js = art / "act_0_trajectory.json"; js.write_text("{}")
    js_key = "reports/rid/nova-trajectories/sess/act_0_trajectory.json"
    u, _ = _uploader_with_mock("bkt", "reports/rid/", run_dir, fail_keys={js_key})
    u.to_report_ref(str(html))                       # 实时传 html（成功）
    u.flush_and_cleanup(run_dir / "nova-trajectories")  # 传 json 失败 → 吞掉
    # 剩余失败被吞（不抛），但整目录**保留不删**（产物不丢）
    assert (run_dir / "nova-trajectories").exists()
    assert html.exists() and js.exists()


# ---- Content-Type：.html 显式打 text/html（与 Midscene uploader 同一规则，ADR 0024 两引擎对称）----
# boto3 不猜 content type：不显式给 → binary/octet-stream → presigned 直开 trajectory 被当附件下载。
def test_html_gets_text_html_content_type_both_paths(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "sess"
    art.mkdir(parents=True)
    ref_html = art / "act_0.html"; ref_html.write_text("traj")        # 实时传（to_report_ref）
    rest_html = art / "act_1.html"; rest_html.write_text("traj")      # 剩余（flush）
    js = art / "act_0_trajectory.json"; js.write_text("{}")           # 非 html：不设 ContentType
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    u.to_report_ref(str(ref_html))
    u.flush_and_cleanup(run_dir / "nova-trajectories")
    ct = "text/html; charset=utf-8"
    assert calls.extra_by_key["reports/rid/nova-trajectories/sess/act_0.html"] == {"ContentType": ct}
    assert calls.extra_by_key["reports/rid/nova-trajectories/sess/act_1.html"] == {"ContentType": ct}
    # .json 亦显式打（ADR 0042 决策一：evidence.json 要能直开、不被当二进制下载；trajectory json 同规则受益）
    assert calls.extra_by_key["reports/rid/nova-trajectories/sess/act_0_trajectory.json"] == {
        "ContentType": "application/json"}


# ---- evidence 的截图/json Content-Type（ADR 0042 决策一）：不显式给 → 浏览器直开变下载 ----
def test_evidence_screenshot_and_json_content_types(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "evidence" / "sc" / "step-2"
    art.mkdir(parents=True)
    (art / "act-0-frame-4.jpg").write_bytes(b"\xff\xd8")
    (art / "act-0-frame-5.jpeg").write_bytes(b"\xff\xd8")
    (art / "shot.PNG").write_bytes(b"\x89PNG")
    (art / "evidence.json").write_text("{}")
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    u.flush_and_cleanup(run_dir / "nova-trajectories")
    base = "reports/rid/nova-trajectories/evidence/sc/step-2/"
    assert calls.extra_by_key[base + "act-0-frame-4.jpg"] == {"ContentType": "image/jpeg"}
    assert calls.extra_by_key[base + "act-0-frame-5.jpeg"] == {"ContentType": "image/jpeg"}
    assert calls.extra_by_key[base + "shot.PNG"] == {"ContentType": "image/png"}  # 后缀比对大小写无关
    assert calls.extra_by_key[base + "evidence.json"] == {"ContentType": "application/json"}


# ---- ref_for：只算 ref、不上传（ADR 0042 决策一「上传时机分两类」；截图字节随 scope 末 flush 走）----
def test_ref_for_equals_report_ref_without_uploading(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories" / "evidence" / "sc" / "step-2"
    art.mkdir(parents=True)
    shot = art / "act-0-frame-4.jpg"; shot.write_bytes(b"\xff\xd8")
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    ref = u.ref_for(str(shot))
    assert calls == []                                  # 关键：算 ref 不产生 PutObject（判定临界路径零网络）
    assert ref == u.to_report_ref(str(shot))             # 与真上传给出的 ref 逐字一致（否则 URI 悬空）
    assert len(calls) == 1                               # 上一句才是真上传


def test_ref_for_noop_reports_same_file_uri_as_report_ref(tmp_path):
    f = tmp_path / "nova-trajectories" / "evidence" / "sc" / "step-0" / "act-0-frame-0.jpg"
    f.parent.mkdir(parents=True); f.write_bytes(b"\xff\xd8")
    u = ArtifactUploader(bucket=None, prefix="reports/rid/", run_dir=tmp_path)
    assert u.ref_for(str(f)) == u.to_report_ref(str(f)) == f"file://{f}"
    assert f.exists()


def test_ref_for_does_not_need_the_file_to_exist(tmp_path):
    """key 是确定性纯路径计算 → 截图还没落盘也能先算 URI 写进 evidence.json。"""
    run_dir = tmp_path / "reports" / "rid"
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    missing = run_dir / "nova-trajectories" / "evidence" / "sc" / "step-0" / "act-0-frame-0.jpg"
    assert u.ref_for(str(missing)) == (
        "s3://bkt/reports/rid/nova-trajectories/evidence/sc/step-0/act-0-frame-0.jpg")
    assert calls == []


def test_content_type_suffix_match_is_case_insensitive(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories"
    art.mkdir(parents=True)
    f = art / "REPORT.HTML"; f.write_text("html")
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    u.to_report_ref(str(f))
    assert calls.extra_by_key["reports/rid/nova-trajectories/REPORT.HTML"] == {"ContentType": "text/html; charset=utf-8"}


# ---- from_env：读注入 env，run_dir = NOVA_LOGS_DIR 父级 ----
def test_from_env_enabled_when_bucket_set(monkeypatch, tmp_path):
    logs = tmp_path / "reports" / "rid" / "nova-trajectories"
    monkeypatch.setenv("ARTIFACT_S3_BUCKET", "bkt")
    monkeypatch.setenv("ARTIFACT_S3_PREFIX", "reports/rid/")
    monkeypatch.setenv("NOVA_LOGS_DIR", str(logs))
    u = ArtifactUploader.from_env()
    assert u.enabled is True
    assert u._bucket == "bkt" and u._prefix == "reports/rid/"
    assert u._run_dir == logs.parent  # run 树根 = NOVA_LOGS_DIR 父级


def test_from_env_noop_when_no_bucket(monkeypatch):
    monkeypatch.delenv("ARTIFACT_S3_BUCKET", raising=False)
    u = ArtifactUploader.from_env()
    assert u.enabled is False


# ---- boto client 超时/重试契约（ADR 0029「上传必须套超时」/退出时间有界）：真建 client 查 meta.config，
# 不 mock（别的测试都塞 mock _client、绕过 _s3()，故这些护栏值零覆盖——绿≠对，见 CLAUDE.md）。不连真 AWS。----
def test_s3_client_has_bounded_timeouts_and_no_retry():
    u = ArtifactUploader(bucket="bkt", prefix="reports/rid/", run_dir=Path("/tmp/rid"))
    cfg = u._s3().meta.config  # 真建 boto3 client（本地构造、不发请求）
    assert cfg.connect_timeout == 5
    assert cfg.read_timeout == 10
    # max_attempts=0 → botocore 归一化 total_max_attempts=1（真单次、零重试、零退避——「快速失败」意图）。
    # 若误写 max_attempts=1 会变成 total=2（1 重试 + 退避 sleep），此断言会红——锁住 C1 修复。
    assert cfg.retries["total_max_attempts"] == 1


def test_bucket_without_logs_dir_fails_loud(monkeypatch):
    """半注入(有桶缺 NOVA_LOGS_DIR)→ 装配矛盾 fail-loud(静默 no-op 会让产物随容器盘销毁必丢,ADR 0033)。"""
    import pytest
    from gherkai_worker_novaact.lib.artifact_upload import ArtifactUploader

    monkeypatch.setenv("ARTIFACT_S3_BUCKET", "b")
    monkeypatch.delenv("NOVA_LOGS_DIR", raising=False)
    with pytest.raises(ValueError, match="NOVA_LOGS_DIR"):
        ArtifactUploader.from_env()


# ---- 后台队列（ADR 0042 决策一「上传时机分两类」）：截图在 step_done 之后入队、字节不压判定临界路径 ----
def _shots(run_dir, n=3):
    art = run_dir / "nova-trajectories" / "evidence" / "sc" / "step-2"
    art.mkdir(parents=True, exist_ok=True)
    out = []
    for j in range(n):
        f = art / f"act-0-frame-{j}.jpg"
        f.write_bytes(b"\xff\xd8")
        out.append(f)
    return out


def test_enqueue_uploads_in_background_with_same_key_as_ref_for(tmp_path):
    """队列传出去的 key **必须**等于 evidence.json 里先算好的那个 URI——不等即永久 404。"""
    run_dir = tmp_path / "reports" / "rid"
    shots = _shots(run_dir)
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    refs = [u.ref_for(str(f)) for f in shots]      # evidence.json 里写下的 URI（只算不传）
    assert calls == []
    u.enqueue(str(f) for f in shots)               # step_done emit 之后入队（可迭代即可）
    assert u.drain(10.0) is True
    assert [f"s3://bkt/{c[2]}" for c in calls] == refs     # 逐字一致 + FIFO 顺序
    assert calls.extra_by_key[calls[0][2]] == {"ContentType": "image/jpeg"}  # ExtraArgs 同 to_report_ref


def test_flush_skips_files_already_uploaded_by_queue(tmp_path):
    run_dir = tmp_path / "reports" / "rid"
    shots = _shots(run_dir, 2)
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    u.enqueue([str(f) for f in shots])
    assert u.drain(10.0) is True
    n_queued = len(calls)
    u.flush_and_cleanup(run_dir / "nova-trajectories")
    assert len(calls) == n_queued == 2              # flush 一次都没重传（走已传集合）
    assert not (run_dir / "nova-trajectories").exists()   # 全成功 → 整目录删（队列传的也算成功）


def test_queue_retries_once_then_gives_up_and_keeps_going(tmp_path, capsys):
    """永久失败的那张：共 2 次尝试（首次 + 重试一次）→ 一行日志放弃；后面的项照传（线程不死）。"""
    run_dir = tmp_path / "reports" / "rid"
    bad, good = _shots(run_dir, 2)
    bad_key = "reports/rid/nova-trajectories/evidence/sc/step-2/act-0-frame-0.jpg"
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir, fail_keys={bad_key})
    u.enqueue([str(bad), str(good)])
    assert u.drain(10.0) is True
    assert sum(1 for c in calls if c[2] == bad_key) == 2          # 首次 + 重试一次，然后放弃
    assert any(c[2].endswith("act-0-frame-1.jpg") for c in calls)  # 后一项照传
    err = capsys.readouterr().err
    assert len([ln for ln in err.splitlines() if "证据截图上传失败" in ln]) == 1  # 只一行
    assert "act-0-frame-0.jpg" in err
    # 放弃的那张仍在本地 → flush 还有一次机会（这就是「放弃」的代价上界）
    assert bad.exists()


def test_queue_retry_succeeds_on_second_attempt(tmp_path, capsys):
    run_dir = tmp_path / "reports" / "rid"
    (shot,) = _shots(run_dir, 1)
    key = "reports/rid/nova-trajectories/evidence/sc/step-2/act-0-frame-0.jpg"
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir, fail_times={key: 1})
    u.enqueue([str(shot)])
    assert u.drain(10.0) is True
    assert sum(1 for c in calls if c[2] == key) == 2      # 第一次抖动、第二次成
    assert "证据截图上传失败" not in capsys.readouterr().err  # 成了就不该报失败
    u.flush_and_cleanup(run_dir / "nova-trajectories")
    assert sum(1 for c in calls if c[2] == key) == 2      # 已记进已传集合 → flush 跳过


def test_drain_is_bounded_returns_false_while_item_in_flight(tmp_path):
    """drain 有界：在途项没传完就到点 → False（调用方据此打一行日志，剩下的交给 flush）。"""
    run_dir = tmp_path / "reports" / "rid"
    (shot,) = _shots(run_dir, 1)
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir, delay_s=0.5)
    assert u.drain(0.0) is True          # 空队列：立即 True
    u.enqueue([str(shot)])
    t0 = time.monotonic()
    assert u.drain(0.05) is False        # 在途 → 到点即返（不等它）
    assert time.monotonic() - t0 < 0.4   # 真的没等满 0.5s 的上传
    assert u.drain(10.0) is True         # 传完后再问 → True
    assert len(calls) == 1


def test_noop_uploader_enqueue_and_drain_are_immediate(tmp_path):
    """本机 no-op 档：截图就在本地，队列/排空都是直接返回（不起线程、不碰 boto3）。"""
    u = ArtifactUploader(bucket=None, prefix="reports/rid/", run_dir=tmp_path)
    u.enqueue(["/nonexistent/act-0-frame-0.jpg"])
    assert u.drain(0.0) is True
    assert u._worker is None and u._pending == 0


def test_concurrent_report_ref_and_queue_share_uploaded_set(tmp_path):
    """线程安全 smoke：主流程实时传 + 队列并发传各自的文件 → 不抛、两边都记进同一个已传集合。"""
    run_dir = tmp_path / "reports" / "rid"
    art = run_dir / "nova-trajectories"
    art.mkdir(parents=True)
    queued = _shots(run_dir, 6)
    realtime = []
    for i in range(6):
        f = art / f"act_{i}.html"
        f.write_text("traj")
        realtime.append(f)
    u, calls = _uploader_with_mock("bkt", "reports/rid/", run_dir)
    start = threading.Event()

    def _realtime():
        start.wait()
        for f in realtime:
            u.to_report_ref(str(f))

    t = threading.Thread(target=_realtime)
    t.start()
    u.enqueue([str(f) for f in queued])
    start.set()
    t.join(10)
    assert u.drain(10.0) is True
    assert not t.is_alive()
    assert len(u._uploaded) == 12 and len(calls) == 12   # 12 个文件各传一次，无异常、无丢账
