"""安装包上传与复用（ADR 0051 决策 9）：键按内容哈希、404 上传（managed 带标签）、年龄在复用窗口内复用、超窗同键刷新、刷新失败重传、
再失败报错、403 报权限、unmanaged 不打标签不刷新、超大包警告。全部用假 S3 client，不连真 AWS；标签在单段与分段上传路径都落到对象上、
CopyObject 刷新后 LastModified 更新已在真实桶上核过，证据内联在 ADR 0051 决策 9。"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

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
