"""云端提交记录的 jobs 对象（ADR 0030 决定六「云端提交记录」条）：运行定义的 `jobs` 数组整份序列化成产物桶里的一个对象。

由 `DynamoDBRunStore` 注入，只在建 run 与读整份运行定义时用到；提交记录的头（runs 表的 META 条目）里的 `jobs_ref` 是这个对象的
`s3://` 地址。对象的内容与 `serialize.run_meta_to_dict` 产出的 `jobs` 同一形态，DocString 与 DataTable 原样内联，serialize 与 model
不知道它的存在。

- **键**：`<定义前缀><run_id>/<随机段>.json`。定义前缀由组合根注入（命名真源 `gherkai_runtime.names.DEFINITIONS_PREFIX`，core 不 import
  runtime），在产物桶根下、不随报告前缀变化；随机段每次建 run 新生成，同一个 run 标识的两次建 run 通常写出两个不同的对象。
- **写**：带「键不存在才写」的条件（`IfNoneMatch="*"`），已有的对象不被覆盖；条件挡下（412 `PreconditionFailed`）即抛
  `RunAlreadyExists`，什么都没写下。不覆盖已有对象由这个条件保证，不靠随机段不相撞（ADR 0030 决定六「建 run 是条件写」条）。不带对象
  tag：桶上两条按 tag 过期的规则不作用于它（ADR 0033「资源清单」3.）。
- **读**：按头里的地址取回。S3 的错误包成 `JobsObjectUnreadable`，带上得到的是键不存在、拒绝访问还是别的错误（`JobsObjectFailure`），
  调用方据它分支、不解析文字（ADR 0030 决定六「jobs 对象取不到时」：后端确认缺键才结束 run，用户一侧不按错误码分支）。地址或内容
  不合约定的形态是定义违约（`DefinitionContractError`）。

**云端 adapter，需 boto3**（`gherkai-core[aws]` extra，缺它 import 本模块不崩、构造时才友好报错）。
"""
from __future__ import annotations

import enum
import json
import secrets

from gherkai_core.adapters._boto import require_boto3
from gherkai_core.errors import DefinitionContractError, RunAlreadyExists

_REF_SCHEME = "s3://"


def _new_segment() -> str:
    """键里的随机段：每次建 run 新生成（32 个小写十六进制字符）。测试替换它，让两次建 run 取到同一个键。"""
    return secrets.token_hex(16)


class JobsObjectFailure(enum.Enum):
    """取 jobs 对象失败时得到的是哪一种错误。"""

    MISSING = "missing"              # 键不存在（S3 的 NoSuchKey；读的一方有桶的列举权限时，缺键才得到它）
    ACCESS_DENIED = "access_denied"  # 拒绝访问（没有列举权限时，缺键得到的也是它）
    OTHER = "other"                  # 别的 S3 错误：网络、限流、桶不存在、凭证等


class JobsObjectUnreadable(RuntimeError):
    """读整份运行定义时，取 jobs 对象的那一次读失败（ADR 0030 决定六「jobs 对象取不到时」）。

    异常类型本身表明失败出在取 jobs 对象的那一次读；`failure` 是得到的错误种类，`error_code` 是 S3 给出的错误码（没有收到 S3 的
    响应时为 None），原异常在 `__cause__` 里。`run_id` 与 `ref`（头里的地址）供调用方写进说明。它不是 ValueError、KeyError、TypeError
    或 AttributeError 的子类：按 `serialize.UNREADABLE_RECORD_ERRORS` 归为内容不合法的调用方不会把它当成定义违约，它是读取本身的失败。

    它也不是 botocore 的异常、不是 OSError：按 `gherkai_runtime.compose.is_botocore_error` 认云端读写失败的入口与按 OSError 认读写
    失败的本机处置都接不住它。读整份定义的用户一侧调用方（处置方与 `explain`）须显式接住它，按读写记录失败处理；说明里要不要补
    「提交记录可能已不完整」那半句看 `failure`，所以不能只按「是不是 botocore 的异常」归类（ADR 0054 决策八「读写记录失败的类别」）。
    """

    def __init__(self, run_id: str, ref: str, failure: JobsObjectFailure, error_code: str | None, detail: str) -> None:
        what = {JobsObjectFailure.MISSING: "对象不存在",
                JobsObjectFailure.ACCESS_DENIED: "被拒绝访问"}.get(failure, detail)
        super().__init__(f"读取 run {run_id} 的提交记录里的 job 列表（{ref}）失败：{what}")
        self.run_id = run_id
        self.ref = ref
        self.failure = failure
        self.error_code = error_code


def _classify(error) -> tuple[JobsObjectFailure, str | None]:
    """把 S3 的异常归成（错误种类, 错误码）：ClientError 按响应里的错误码分；没有收到响应的 BotoCoreError（网络、凭证）归为别的错误。"""
    from botocore.exceptions import ClientError

    if not isinstance(error, ClientError):
        return JobsObjectFailure.OTHER, None
    code = error.response.get("Error", {}).get("Code")
    if code == "NoSuchKey":
        return JobsObjectFailure.MISSING, code
    if code == "AccessDenied":
        return JobsObjectFailure.ACCESS_DENIED, code
    return JobsObjectFailure.OTHER, code


def _parse_ref(ref) -> tuple[str, str]:
    """把头里的地址拆成（桶, 键）。不是 `s3://<桶>/<键>` 形态的文本即定义违约。不用 urlparse：键里的 `#`、`?` 不是片段与查询串。"""
    if not isinstance(ref, str) or not ref.startswith(_REF_SCHEME):
        raise DefinitionContractError(f"提交记录头里的 jobs_ref 须为 s3:// 地址，现为 {type(ref).__name__}")
    bucket, _, key = ref[len(_REF_SCHEME):].partition("/")
    if not bucket or not key:
        raise DefinitionContractError(f"提交记录头里的 jobs_ref 缺桶名或键：{ref!r}")
    return bucket, key


class S3JobsObjects:
    """jobs 对象的存取（组合根注入 boto3 s3 client、产物桶与定义前缀）。"""

    def __init__(self, s3_client, bucket: str, definitions_prefix: str) -> None:
        """s3_client：boto3 s3 client；bucket：产物桶（判定明细与报告所在的同一个桶）；definitions_prefix：定义前缀，带结尾的 `/`。"""
        require_boto3("S3JobsObjects")
        self._s3 = s3_client
        self._bucket = bucket
        self._prefix = definitions_prefix

    def put(self, run_id: str, jobs: list) -> str:
        """把 jobs 数组写成一个新对象，返回它的 `s3://` 地址。键已存在（条件写得到 412）抛 `RunAlreadyExists`、什么都没写下；别的
        S3 错误原样抛出，调用方按写记录失败报出。"""
        from botocore.exceptions import ClientError

        key = f"{self._prefix}{run_id}/{_new_segment()}.json"
        try:
            self._s3.put_object(
                Bucket=self._bucket, Key=key,
                Body=json.dumps(jobs, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json",
                IfNoneMatch="*",
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "PreconditionFailed":
                raise RunAlreadyExists(run_id) from e
            raise
        return f"{_REF_SCHEME}{self._bucket}/{key}"

    def get(self, run_id: str, ref) -> list:
        """按头里的地址取回 jobs 数组（一次 GetObject，不列举）。地址按它自己写明的桶与键取，不按本实例的配置重算。

        取回失败（含读响应正文时的失败）抛 `JobsObjectUnreadable`；地址形态不对、内容不是 JSON 数组抛 `DefinitionContractError`。
        S3 之外的异常（如注入的句柄不对）原样抛出：那是装配错误，不是这次读的结果。"""
        from botocore.exceptions import BotoCoreError, ClientError

        bucket, key = _parse_ref(ref)
        try:
            body = self._s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        except (BotoCoreError, ClientError) as e:
            failure, code = _classify(e)
            raise JobsObjectUnreadable(run_id, ref, failure, code, str(e)) from e
        try:
            jobs = json.loads(body)
        except ValueError as e:  # 含正文不是 UTF-8
            raise DefinitionContractError(f"提交记录里的 job 列表不是合法的 JSON（{e}）") from e
        if not isinstance(jobs, list):
            raise DefinitionContractError(f"提交记录里的 job 列表须为 JSON 数组，现为 {type(jobs).__name__}")
        return jobs
