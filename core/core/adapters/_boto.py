"""云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。

四个云端 adapter（DynamoDBRunStore / S3ResultStore / S3ReportStore / S3StepArgumentOffloader）共用一处，
不各抄一份（消除同一 bug 修四遍的系统性重复）。

**定位（务必读清）**：这是**冗余兜底、非主要拦截点**。缺 boto3 的真正早失败发生在**组合根**——是组合根
`import boto3` 造 client/表资源再注入 adapter；缺 boto3 时组合根先炸，根本走不到 adapter 构造。adapter 内部
只用注入的 client/table、运行期从不 import boto3。故本守卫只在「adapter 被脱离标准组合根直接构造」（测试/
未来 WebUI 直连）这类边角路径给一句友好提示，主路径由组合根兜。检 **boto3**（不是 botocore）——aws extra
声明的是 `boto3>=1.34`，而 botocore 可脱 boto3 单独存在（awscli/s3transfer 带），检 botocore 会误放行
「装了 botocore 没装 boto3」的环境。
"""
from __future__ import annotations


def require_boto3(component: str) -> None:
    """缺 boto3 时抛带组件名的友好 ImportError（`pip install core[aws]`）；模块 import 不崩、构造时才检。"""
    try:
        import boto3  # noqa: F401
    except ImportError as e:  # pragma: no cover  # 主拦截在组合根；此处仅冗余兜底
        raise ImportError(
            f"{component} 需要 boto3——请装云端依赖：`pip install core[aws]`（或 uv 装 aws extra）"
        ) from e
