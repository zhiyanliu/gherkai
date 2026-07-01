"""StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3 指针，解 DDB 400KB 限。

**DdbRunStore 内部钩子、对 core 透明**：只加工 `serialize.run_meta_to_dict` 的**产物 dict**——写端 `json.dumps` 前把
docString 的 `content` / dataTable 的 `rows` 搬去 S3、原键换成 `content_ref` / `rows_ref`（值=s3:// URI）；读端
`json.loads` 后按指针取回、消解回内联，再交 `run_meta_from_dict`。serialize/model 零感知。

两条关键决策（ADR 0030 决定六）：
1. **位置区分、非值探测**：offload 后 argument dict 里原 `content`/`rows` 键**缺席**、代之以 `content_ref`/`rows_ref`；
   读端按「哪个键在」分支，**绝不**靠「值是不是 s3:// 开头」猜内联/指针——docString 正文本身可能以 s3:// 开头（值 sniff 脆）。
2. **key 含 step_index**：`<prefix><run_id>/args/<quote(scope_id)>/<quote(scenario_id)>/<step_index>/<kind>.json`
   ——否则同 scenario 多 docString 撞 key、静默串值。

粒度「一律 offload」（无 size 阈值，ADR 决定六）：凡 docString/dataTable 都搬 S3，size 阈值是未来纯加法优化、不预置。
只挂 RunMeta 写/读路径；RunState（update_job_state/finalize/load_run_state）无 argument、零 S3 依赖。
"""
from __future__ import annotations

import json
from urllib.parse import quote, urlparse


def _require_boto3():
    """云端 adapter 缺 boto3 时友好提示（模块 import 不崩、构造时才检；守 [0016] 窄腰、方案 A）。"""
    try:
        import botocore.exceptions  # noqa: F401
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "StepArgument S3 offload 需要 boto3——请装云端依赖：`pip install core[aws]`（或 uv 装 aws extra）"
        ) from e


def _iter_arguments(meta_dict: dict):
    """遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id, scenario_id, step_index)。

    位置驱动（走 jobs→scenarios→steps 的 def 结构），不猜内容；只碰确有 argument 的 step。
    """
    for job in meta_dict.get("jobs", []):
        scope_id = job["scope_id"]
        for sc in job.get("scenarios", []):
            scenario_id = sc["id"]
            for step in sc.get("steps", []):
                arg = step.get("argument")
                if arg is not None:
                    yield arg, scope_id, scenario_id, step["index"]


class S3StepArgumentOffloader:
    """把 RunMeta 里 docString/dataTable 的正文搬 S3（DdbRunStore 注入）。offload/restore 一对，互逆。"""

    def __init__(self, s3_client, bucket: str, prefix: str = "") -> None:
        """s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。"""
        _require_boto3()
        self._s3 = s3_client
        self._bucket = bucket
        self._prefix = prefix

    def _key(self, run_id: str, scope_id: str, scenario_id: str, step_index: int, kind: str) -> str:
        # 含 step_index（否则同 scenario 多 docString 撞 key）；scope_id/scenario_id 不透明 → quote(safe='')
        return (
            f"{self._prefix}{run_id}/args/"
            f"{quote(scope_id, safe='')}/{quote(scenario_id, safe='')}/{step_index}/{kind}.json"
        )

    def _put(self, key: str, value) -> str:
        """把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。"""
        self._s3.put_object(
            Bucket=self._bucket, Key=key,
            Body=json.dumps(value, ensure_ascii=False).encode("utf-8"),
        )
        return f"s3://{self._bucket}/{key}"

    def offload(self, meta_dict: dict, run_id: str) -> dict:
        """就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。

        meta_dict 是 run_meta_to_dict 的新鲜产物（非模型别名），就地改安全。返回同一 dict（便于链式）。
        """
        for arg, scope_id, scenario_id, step_index in _iter_arguments(meta_dict):
            kind = arg["kind"]
            key = self._key(run_id, scope_id, scenario_id, step_index, kind)
            if kind == "docString":
                arg["content_ref"] = self._put(key, arg.pop("content"))  # content 键消失、代之以 content_ref
            else:  # dataTable
                arg["rows_ref"] = self._put(key, arg.pop("rows"))        # rows 键消失、代之以 rows_ref
        return meta_dict

    def restore(self, meta_dict: dict, run_id: str) -> dict:
        """就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。

        按「哪个 _ref 键在」分支（不靠值 sniff）；指针是 s3:// URI，直接解析取回、不依赖当前 prefix 配置。
        run_id 仅签名对称（restore 用不到，key 已编码在 URI 里）。
        """
        for arg, _scope_id, _scenario_id, _step_index in _iter_arguments(meta_dict):
            if "content_ref" in arg:
                arg["content"] = self._fetch(arg.pop("content_ref"))
            elif "rows_ref" in arg:
                arg["rows"] = self._fetch(arg.pop("rows_ref"))
        return meta_dict

    def _fetch(self, uri: str):
        """按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。"""
        p = urlparse(uri)
        body = self._s3.get_object(Bucket=p.netloc, Key=p.path.lstrip("/"))["Body"].read()
        return json.loads(body)
