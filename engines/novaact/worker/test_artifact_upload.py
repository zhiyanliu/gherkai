"""ArtifactUploader 单测（ADR 0029 第一期）：整目录上传 + 删本地 + reportRef 报 s3://，无落点 env 时 no-op 报 file://。

mock boto3 client（不连真 AWS、不加 moto 依赖）。重点护 ADR 0029：
- **key 镜像本地 run 树** + **ref 与上传 key 逐字一致**（否则 index 链接断）。
- **两级时机**：to_report_ref 实时传（不删）；flush_and_cleanup scope 末传剩余（跳过已传）+ 全成功才删整目录。
- **整目录传，不按文件挑**（抗 SDK 升级）：flush walk 整目录，log/.json 一并传。
- **失败护栏**：reportRef 实时传失败抛（可观测）；剩余 flush 失败吞掉但整目录不删；全成功才 rmtree。
- **no-op**：无 ARTIFACT_S3_BUCKET → 报 file://、不上传、不删。
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.artifact_upload import ArtifactUploader


def _uploader_with_mock(bucket, prefix, run_dir, *, fail_keys=()):
    """造 uploader + 塞 mock s3 client（记录 upload_file 调用；fail_keys 里的 key 抛错）。"""
    u = ArtifactUploader(bucket=bucket, prefix=prefix, run_dir=Path(run_dir))
    client = MagicMock()
    calls = []

    def _upload(local, bkt, key):
        calls.append((local, bkt, key))
        if key in fail_keys:
            raise RuntimeError(f"s3 fail: {key}")

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
