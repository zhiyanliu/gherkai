"""安装包上传与复用（ADR 0051 决策 9）：键按内容哈希、404 上传（managed 带标签）、年龄在复用窗口内复用、超窗同键刷新、刷新失败重传、
再失败报错、403 报权限、unmanaged 不打标签不刷新、超大包警告。全部用假 S3 client，不连真 AWS；标签在单段与分段上传路径都落到对象上、
CopyObject 刷新后 LastModified 更新已在真实桶上核过，证据内联在 ADR 0051 决策 9。"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from botocore.hooks import HierarchicalEmitter

from gherkai_runtime import app_upload, names

NOW = datetime(2026, 10, 27, tzinfo=timezone.utc)


class _ClientError(Exception):
    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.response = {"Error": {"Code": code, "Message": code}, "ResponseMetadata": {"HTTPStatusCode": status}}


class _S3:
    """假 S3 client：head 按预设返回或抛；记录 upload_file / copy_object 的入参；可让它们失败。"""

    def __init__(self, *, head=None, head_error: str | None = None, upload_fail: int = 0, copy_fail: bool = False):
        self._head, self._head_error = head, head_error
        self._upload_fail, self._copy_fail = upload_fail, copy_fail
        self.uploads: list = []
        self.copies: list = []

    def head_object(self, *, Bucket, Key):
        if self._head_error is not None:
            raise _ClientError(self._head_error, 404 if self._head_error == "404" else 403)
        return dict(self._head or {})

    def upload_file(self, Filename, Bucket, Key, ExtraArgs=None):
        if self._upload_fail:
            self._upload_fail -= 1
            raise RuntimeError("upload failed")
        self.uploads.append((Filename, Bucket, Key, ExtraArgs))

    def copy_object(self, **kw):
        if self._copy_fail:
            raise RuntimeError("copy failed")
        self.copies.append(kw)


def _file(tmp_path: Path, content: bytes = b"apk-bytes", name: str = "app.apk") -> Path:
    p = tmp_path / name
    p.write_bytes(content)
    return p


class _Request:
    """request-created 事件里的请求对象的结构子集：签名上下文与地址。"""

    def __init__(self, region: str, host: str):
        self.context = {"signing": {"region": region}}
        self.url = f"https://{host}/k"


class _S3Redirecting(_S3):
    """带真实事件系统（botocore 的 HierarchicalEmitter）的假 client：head 时按 boto3 跟随区域重定向的样子发 request-created 事件——
    先按客户端区域签一次，桶在别的区域时再按桶区域签一次。用真实事件系统是为了让「按 unique_id 注销」真的被核对。"""

    def __init__(self, *, client_region: str = "us-east-1", bucket_region: str = "eu-west-1", **kw):
        super().__init__(**kw)
        self.meta = type("Meta", (), {"events": HierarchicalEmitter(), "region_name": client_region})()
        self._regions = [client_region] + ([bucket_region] if bucket_region != client_region else [])

    def head_object(self, *, Bucket, Key):
        for region in self._regions:
            self.meta.events.emit("request-created.s3.HeadObject", request=_Request(region, f"{Bucket}.s3.{region}.amazonaws.com"),
                                  operation_name="HeadObject")
        return super().head_object(Bucket=Bucket, Key=Key)


def _observer_gone(s3) -> bool:
    """事件系统上已没有任何 request-created.s3.HeadObject 的处理器（emit 返回空列表）。"""
    return s3.meta.events.emit("request-created.s3.HeadObject", request=_Request("x", "h")) == []


def test_bucket_region_observer_records_the_signing_region_of_the_last_request():
    obs = app_upload._BucketRegionObserver()
    assert obs(request=None) is None and obs.region is None
    obs(request=_Request("us-east-1", "b.s3.amazonaws.com"))
    assert obs.region == "us-east-1"
    obs(request=_Request("eu-west-1", "b.s3.eu-west-1.amazonaws.com"))   # 跟随重定向后重发的请求：最后一次为准
    assert obs.region == "eu-west-1"
    obs(request=type("R", (), {"context": {}})())   # 没有签名上下文的请求不改已记下的区域
    assert obs.region == "eu-west-1"


def test_ensure_app_object_returns_the_last_signing_region_and_unregisters_on_every_path(tmp_path):
    redirected = _S3Redirecting(head={})
    loc = app_upload.ensure_app_object("b", _file(tmp_path), managed=False, s3=redirected, now=NOW)
    assert loc.bucket_region == "eu-west-1" and _observer_gone(redirected)
    same_region = _S3Redirecting(head={}, bucket_region="us-east-1")
    assert app_upload.ensure_app_object("b", _file(tmp_path), managed=False, s3=same_region, now=NOW).bucket_region == "us-east-1"
    assert _observer_gone(same_region)
    no_events = app_upload.ensure_app_object("b", _file(tmp_path), managed=False, s3=_S3(head={}), now=NOW)
    assert no_events.bucket_region is None   # 没有事件系统的 client（测试的假 client）照常工作，区域记为未知
    uploaded_after_redirect = _S3Redirecting(head_error="404")
    uploaded = app_upload.ensure_app_object("b", _file(tmp_path), managed=False, s3=uploaded_after_redirect, now=NOW)
    assert uploaded.uploaded and uploaded.bucket_region == "eu-west-1" and _observer_gone(uploaded_after_redirect)   # 上传路径同样带回区域
    denied = _S3Redirecting(head_error="403")
    with pytest.raises(app_upload.AppUploadError, match="没有权限"):
        app_upload.ensure_app_object("b", _file(tmp_path), managed=False, s3=denied, now=NOW)
    assert _observer_gone(denied)   # 异常路径同样注销

def test_key_is_content_hash_plus_original_name_and_404_uploads_with_tag_when_managed(tmp_path):
    f = _file(tmp_path)
    s3 = _S3(head_error="404")
    loc = app_upload.ensure_app_object("b", f, managed=True, s3=s3, now=NOW)
    sha = hashlib.sha256(b"apk-bytes").hexdigest()
    assert loc == app_upload.AppLocation("b", f"apps/{sha}/app.apk", sha, uploaded=True, refreshed=False)
    assert s3.uploads == [(str(f), "b", f"apps/{sha}/app.apk", {"Tagging": "gherkai=app"})] and s3.copies == []


def test_unmanaged_bucket_uploads_without_tag_and_never_refreshes(tmp_path):
    f = _file(tmp_path)
    s3 = _S3(head_error="404")
    loc = app_upload.ensure_app_object("mine", f, managed=False, s3=s3, now=NOW)
    assert loc.uploaded and s3.uploads[0][3] is None
    old = _S3(head={"LastModified": NOW - timedelta(days=400)})
    loc = app_upload.ensure_app_object("mine", f, managed=False, s3=old, now=NOW)
    assert not loc.uploaded and not loc.refreshed and old.uploads == [] and old.copies == []   # 只做存在性复用


def test_managed_reuse_within_window_and_refresh_beyond_it(tmp_path):
    f = _file(tmp_path)
    window = app_upload.reuse_window()
    assert window == timedelta(days=names.APP_OBJECT_EXPIRE_DAYS - names.APP_OBJECT_RETAIN_DAYS) == timedelta(days=7)
    young = _S3(head={"LastModified": NOW - window})   # 恰在窗口边界：复用
    loc = app_upload.ensure_app_object("b", f, managed=True, s3=young, now=NOW)
    assert not loc.uploaded and not loc.refreshed and young.copies == [] and young.uploads == []
    old = _S3(head={"LastModified": NOW - window - timedelta(seconds=1)})
    loc = app_upload.ensure_app_object("b", f, managed=True, s3=old, now=NOW)
    assert loc.refreshed and not loc.uploaded and old.uploads == []
    [copy] = old.copies
    assert copy == {"Bucket": "b", "Key": loc.key, "CopySource": {"Bucket": "b", "Key": loc.key},
                    "MetadataDirective": "REPLACE", "TaggingDirective": "REPLACE", "Tagging": "gherkai=app"}


def test_refresh_failure_falls_back_to_reupload_and_double_failure_raises(tmp_path):
    f = _file(tmp_path)
    stale = {"LastModified": NOW - timedelta(days=30)}
    s3 = _S3(head=stale, copy_fail=True)
    loc = app_upload.ensure_app_object("b", f, managed=True, s3=s3, now=NOW)
    assert loc.uploaded and not loc.refreshed and s3.uploads[0][3] == {"Tagging": "gherkai=app"}
    both = _S3(head=stale, copy_fail=True, upload_fail=1)
    with pytest.raises(app_upload.AppUploadError, match="刷新.*与重传.*都失败"):
        app_upload.ensure_app_object("b", f, managed=True, s3=both, now=NOW)


def test_403_on_head_is_a_permission_error_and_other_errors_propagate(tmp_path):
    f = _file(tmp_path)
    with pytest.raises(app_upload.AppUploadError, match="没有权限.*apps/"):
        app_upload.ensure_app_object("b", f, managed=True, s3=_S3(head_error="403"), now=NOW)
    with pytest.raises(_ClientError):
        app_upload.ensure_app_object("b", f, managed=True, s3=_S3(head_error="500"), now=NOW)


def test_large_package_warns_but_proceeds(tmp_path):
    f = _file(tmp_path, b"x" * 2048)
    warnings: list = []
    s3 = _S3(head_error="404")
    app_upload.ensure_app_object("b", f, managed=True, s3=s3, now=NOW, on_warn=warnings.append, large_bytes=1024)
    assert len(warnings) == 1 and "MB" in warnings[0] and len(s3.uploads) == 1


def test_first_upload_failure_is_a_product_error_not_a_raw_exception(tmp_path):
    """boto3 的 upload_file 把 ClientError 包成自己的 S3UploadFailedError（不是 botocore 异常）：404 分支的首次上传失败也要翻成 AppUploadError。"""
    f = _file(tmp_path)
    s3 = _S3(head_error="404", upload_fail=1)
    with pytest.raises(app_upload.AppUploadError, match="上传安装包.*失败.*upload failed"):
        app_upload.ensure_app_object("b", f, managed=True, s3=s3, now=NOW)
