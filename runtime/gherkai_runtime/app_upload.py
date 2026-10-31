"""安装包上传到 S3 应用前缀（ADR 0051 决策 9）。

键为 `apps/<sha256>/<原文件名>`：按内容哈希放，同一文件（同内容、同名）只传一次；同内容不同名的文件各占一个键。两种桶两种承诺：
- **云端产物桶由本工具管理**（`managed=True`）：对象带标签 `gherkai=app`，桶按该标签在 E 天后过期；为兑现「已提交 run 引用的对象自提交起
  至少保留 R 天」，复用前看对象年龄——不超过 E 减 R 天直接复用，超过就同键 CopyObject 刷新（回写元数据与标签，让过期从新时刻重算），
  刷新失败重传，再失败即报错、不复用快过期的对象。E 与 R 的常量与部署侧的生命周期规则同一处（`names`）。
- **本机后端的应用桶归使用方所有**（`managed=False`）：只做存在性复用，不打标签、不刷新、不承诺保留。
HeadObject 的 404 走上传、403 报权限（存在性检查靠前缀 ListBucket 把缺失键的 403 变成 404，权限表登记在 ADR 0033）。
桶不在客户端区域时 boto3 自动跟随 S3 的区域重定向；本模块只观察这个过程：公开的 request-created 事件给出每次发出的 HeadObject 的签名区域，
最后一次就是桶所在的区域（没有重定向时即客户端区域），随位置返回，调用方据此提示使用方（ADR 0051 决策 9）。不读响应头：区域端点回带区域头
的 301、us-east-1 的全局端点回带区域头的 307（实测），客户端缓存过桶区域之后则不再出现重定向——签名区域在这几种情形下都正确。
boto3 由调用方注入 s3 client（`[aws]` extra，本模块不 import）。所有 `AppUploadError` 的消息都是给使用方看的整句。
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gherkai_runtime import names as _names

LARGE_APP_WARN_BYTES = 500 * 1024 * 1024  # 超过只警告不拦（ADR 0051 决策 9：下载上界是有前提的估算，实测过的最大包 88 MB）


class AppUploadError(Exception):
    """安装包上传或复用失败（权限、刷新与重传都失败）。消息即给使用方看的整句。"""


@dataclass(frozen=True)
class AppLocation:
    bucket: str
    key: str
    sha256: str
    uploaded: bool    # 本次真上传了（否则复用既有对象）
    refreshed: bool   # 本次做了同键刷新（只在 managed 桶）
    bucket_region: str | None = None   # 桶所在区域（本次最后一次 HeadObject 的签名区域）；None 只在客户端没有事件系统时出现


_REQUEST_EVENT = "request-created.s3.HeadObject"
_OBSERVER_ID = "gherkai-app-bucket-region"


class _BucketRegionObserver:
    """通过 boto3 公开的 request-created 事件读取桶所在区域，只读不改：记下每次发出的 HeadObject 的签名区域。boto3 跟随区域重定向之后
    重发的请求按桶所在区域签名，所以最后一次的签名区域就是桶的区域；没有重定向时它就是客户端自己的区域。"""

    def __init__(self) -> None:
        self.region: str | None = None

    def __call__(self, request=None, **_kwargs):
        context = getattr(request, "context", None) or {}
        region = (context.get("signing") or {}).get("region")
        if region:
            self.region = region
        return None


def _events(s3):
    """boto3 client 的事件系统；假 client 没有时返回 None（观察随之跳过）。"""
    return getattr(getattr(s3, "meta", None), "events", None)


def sha256_of_file(path: Path) -> str:
    """流式算文件内容的 sha256（安装包可达数百 MB，不整读进内存）。"""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def app_object_key(sha256: str, filename: str) -> str:
    return f"{_names.APP_OBJECT_PREFIX}{sha256}/{filename}"


def reuse_window() -> timedelta:
    """managed 桶里对象可直接复用的最大年龄：E 减 R（ADR 0051 决策 9）。"""
    return timedelta(days=_names.APP_OBJECT_EXPIRE_DAYS - _names.APP_OBJECT_RETAIN_DAYS)


def _error_code(e: BaseException) -> str | None:
    resp = getattr(e, "response", None)
    if not isinstance(resp, dict):
        return None
    code = (resp.get("Error") or {}).get("Code")
    if code:
        return str(code)
    status = (resp.get("ResponseMetadata") or {}).get("HTTPStatusCode")
    return str(status) if status is not None else None


def _upload(s3, bucket: str, key: str, file: Path, *, managed: bool) -> None:
    # upload_file 走 boto3 的分段传输（大包自动分段）；标签随 ExtraArgs 进 PutObject / CreateMultipartUpload——单段与分段两条路径的标签都
    # 已在真实桶上核过，证据见 ADR 0051 决策 9。unmanaged 桶不打标签——那是使用方的桶，不替他们定义清理规则。
    # upload_file 把 ClientError 包成 boto3 自己的 S3UploadFailedError（不是 botocore 异常），调用方按 botocore 分流抓不到，
    # 故在这里一律翻成带原因的产品提示：桶不存在、没有写权限、网络问题都走这一句。
    try:
        if managed:
            s3.upload_file(str(file), bucket, key, ExtraArgs={"Tagging": _names.APP_OBJECT_TAG})
        else:
            s3.upload_file(str(file), bucket, key)
    except Exception as e:
        raise AppUploadError(f"上传安装包 {file} 到 S3 桶 {bucket} 失败（桶不存在、没有写权限或网络问题）：{e}") from e


def ensure_app_object(bucket: str, file: Path, *, managed: bool, s3, now: datetime | None = None,
                      on_warn: Callable[[str], None] | None = None, large_bytes: int = LARGE_APP_WARN_BYTES) -> AppLocation:
    """保证安装包在桶里且（managed 时）保留承诺成立，返回它的 S3 位置与内容哈希（填进 Job 的应用条目，ADR 0048 决策 3）。"""
    now = now or datetime.now(timezone.utc)
    size = file.stat().st_size
    if size > large_bytes and on_warn is not None:
        on_warn(f"安装包 {file} 有 {size / (1024 * 1024):.0f} MB：设备上安装前要从 S3 下载，太大可能超过单条安装命令的时间上限，建议精简包体")
    sha = sha256_of_file(file)
    key = app_object_key(sha, file.name)
    observer = _BucketRegionObserver()
    events = _events(s3)
    if events is not None:
        events.register(_REQUEST_EVENT, observer, unique_id=_OBSERVER_ID)
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
    except Exception as e:
        code = _error_code(e)
        if code in ("404", "NoSuchKey", "NotFound"):
            _upload(s3, bucket, key, file, managed=managed)
            return AppLocation(bucket, key, sha, uploaded=True, refreshed=False, bucket_region=observer.region)
        if code in ("403", "AccessDenied", "Forbidden"):
            raise AppUploadError(f"没有权限读取 S3 桶 {bucket} 里 {key} 的对象信息（403）：请给当前凭证加上该桶 "
                                 f"{_names.APP_OBJECT_PREFIX} 前缀的读取、列举与写入权限后重试") from e
        raise
    finally:
        if events is not None:
            events.unregister(_REQUEST_EVENT, unique_id=_OBSERVER_ID)
    region = observer.region
    if not managed:
        return AppLocation(bucket, key, sha, uploaded=False, refreshed=False, bucket_region=region)
    last_modified = head.get("LastModified")
    if last_modified is not None and now - last_modified <= reuse_window():
        return AppLocation(bucket, key, sha, uploaded=False, refreshed=False, bucket_region=region)
    try:
        s3.copy_object(Bucket=bucket, Key=key, CopySource={"Bucket": bucket, "Key": key},
                       MetadataDirective="REPLACE", TaggingDirective="REPLACE", Tagging=_names.APP_OBJECT_TAG)
        return AppLocation(bucket, key, sha, uploaded=False, refreshed=True, bucket_region=region)
    except Exception as refresh_error:
        try:
            _upload(s3, bucket, key, file, managed=True)
            return AppLocation(bucket, key, sha, uploaded=True, refreshed=False, bucket_region=region)
        except Exception as upload_error:
            raise AppUploadError(f"安装包 {file} 在 S3 桶 {bucket} 里的副本即将到保留期，刷新（{refresh_error}）与重传（{upload_error}）都失败，"
                                 "不能复用快过期的对象：请检查权限与网络后重试") from upload_error
