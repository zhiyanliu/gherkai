"""worker 镜像交付测试的真实账户装置：把 `deploy_aws/tests/test_workers.py` 的全部用例原样对真实 AWS 账户执行。

用途、证据边界、前置、执行命令与判读见同目录 README.md；本文件头只写装置自身的机制，供改装置的人对照。

载入方式
  按路径载入仓库里的 `deploy_aws/tests/test_workers.py`（模块名取 `test_workers`），取得到 pytest 的断言改写钩子时经它载入，
  失败信息与直接执行原文件相同。原模块的 test_ 函数与辅助名字复制进本模块，pytest 在本模块里收集到同一批用例；用例与
  辅助函数仍经**原模块的全局**读 PREFIX / ACCOUNT / REGISTRY / REGION，夹具用 monkeypatch 改原模块对象上的这四个属性。
  夹具 `_presentation_is_environment_independent` 原样沿用原模块的那个对象；`_aws_env` 与 `aws` 在这里重定义。
  本文件不以 `test_` 开头，仓库的 pytest 配置不会顺带收集它；在命令行上显式给出它的路径时 pytest 照常收集。

环境变量（取值与校验见 conftest.py 的 `settings`）
  GKP_MODE              moto（缺省）| real
  GKP_FORCE_REAL_PATHS  =1 且 moto：惰性建表、写后等待（秒数 0）、ECS 适配、收尾清扫与补充用例都在 moto 上执行
  GKP_EXEC_ROLE         real 下必须显式给出：<已有 ECS 任务执行角色的 ARN> | none（不补角色）；
                        moto + FORCE 下缺省 auto：用一个合成的 ARN 字符串（moto 不校验角色是否存在）
  GKP_REGION            region；real 下缺省取 AWS_REGION / AWS_DEFAULT_REGION，都没有时报错；moto 下缺省 us-east-1
  GKP_TOKEN             会话令牌（1-12 位小写字母数字、以字母结尾，缺省随机 4 位）；资源名前缀为 gkp<令牌><三位序号>-
  GKP_SETTLE            real 下 DynamoDB 写操作返回前等待的秒数，有限的非负数（缺省 2.0；moto 下恒为 0，取值照样校验）
  GKP_ADAPT             1（缺省）| 0：real 下是否给注册请求做两项适配（见下）
  GKP_OBS_N             补充用例 c 前三项每项重复的次数，正整数（缺省 40）
  GKP_RESULTS           结果 jsonl 的路径（见 conftest.py）

IAM
  本装置在任何模式下都不调用 IAM：不建、不删、不改角色。real 下注册任务定义时引用的执行角色由使用者给出，
  它必须已存在且调用方对它有 iam:PassRole；给 none 时不补角色，种子模板的注册预期被真实 ECS 拒绝。

前缀形态
  前缀 gkp<令牌><序号>- 在令牌与序号之间不加连字符：原用例 test_cleanup_never_touches_the_template_revision 用
  `arn.rsplit("/", 1)[-1].split("-")[1]` 从 family 名里取引擎名，前缀里只能有末尾一个连字符。没有分隔符就要求令牌以字母
  结尾：否则令牌 ab 的清扫模式「gkpab + 三位以上数字 + 连字符」也匹配令牌 ab12 的 gkpab12001-，清扫会越出自己的范围。

DynamoDB 惰性建表（real 与 FORCE）
  aws.ddb 是 `LazyDdb` 壳：seed_backend 调的 create_table 只记参数；list_tables 原样转发并补上已记下或已建的表名；其余任何
  调用到来时先真正建表、等表与全部 GSI 为 ACTIVE 再转发。发出建表请求之前先登记「已请求」：服务端已接受请求、客户端随后
  超时或连接中断时表已在建，客户端却没有应答，teardown 一行把这样的表记在 table_create_unconfirmed 里。多数用例不读写表，惰性建表让它们不必为建表等待。real 下写操作
  返回前等 GKP_SETTLE 秒。`disable_lazy()` 丢掉记下的建表参数、此后一切原样转发（「表不存在」与「索引建立中」两条补充
  用例用它）。绕过 aws.ddb 自建 boto3 资源或 client 的用例（如 test_snapshot_sees_what_the_real_run_store_writes_until_the_run_finishes
  用 boto3.resource("dynamodb")）：每个用例换一个新的 boto3 默认 session，在它的事件发射器上挂 before-call.dynamodb（先惰性
  建表）与 after-call.dynamodb（写操作之后同样等待）两个钩子，经 boto3.resource / boto3.client 现建的 dynamodb 句柄因此与
  aws.ddb 共用同一次惰性建表。夹具自己的四个 client 来自另一个独立 session，不挂钩子。纯 moto 模式与原夹具相同。

real 下的两项注册适配（GKP_ADAPT=0 关闭），只作用于种子模板
  种子模板是用例自己摆的、不是 CDK 合成的模板，真实 ECS 对它有两处 moto 不查的校验：Fargate 任务定义引用 ECR 镜像时要求
  带 executionRoleArn；cpu 为 2048 时 memory 至少 4096（seed_backend(cpu="2048") 那几条摆的是 2048/2048）。`AdaptedEcs` 只在
  种子模板的注册请求缺 executionRoleArn 时补上、只在 memory 低于该 cpu 的 Fargate 下限时调高，每次适配记一行 `adaptation`。
  原用例不断言这两个字段。
  判别种子模板：装置把原模块的 `seed_backend` 换成一个只做标记的包装（`_marked_seed_backend`，参数与返回值原样），在它执行
  期间、于调用它的线程里置一个线程局部的标记；注册请求到来时标记在场才算种子模板。这个判别不会误判：用例里的模板注册只出现
  在 seed_backend 里（用例另行注册的 revision 都经被测代码的复制函数 `workers._register_revision`），seed_backend 自己不调用
  被测代码；参与方线程各在自己的线程里，看不到主线程的标记。其余注册请求（被测代码发出的复制请求）一律原样转发，装置另核对
  它们：复制请求带的模板 ARN（`gherkai:template` tag）是本用例的种子模板时，装置给那个模板补过或调过的字段必须原样出现在复制
  请求里，否则记一行 `copy_request_mismatch`（进 conftest 的问题清单），并在该用例的收尾之后让它以收尾错误失败：装置只适配
  种子模板，不替被测代码的请求补字段，被测代码漏带模板字段的缺陷因此不会被装置掩盖。

real 下预期失败的用例（real 与 FORCE）
  test_repush_retires_the_replaced_revision_and_prints_digest_change 用 ecr.put_image 放一份没有 layer 的手写 manifest，真实
  ECR 以 InvalidParameterException 拒绝。conftest 的 `pytest_runtest_makereport` 在报告生成之后调用本模块的 `expected_failure`：
  只有这条用例的 call 阶段、抛出的是 PutImage 操作的 ClientError、错误码为 InvalidParameterException 时，报告改为预期失败；
  setup 与 teardown 阶段的错误、其它操作或其它错误码的 ClientError、其它异常照常失败。纯 moto 模式下不作判定；FORCE 下照样
  判定（moto 接受这份 manifest，这条用例在 moto 上照常通过），自检借此在 moto 上核对判定的边界。给了 pytest 的 --runxfail
  时 conftest 不调用判定，这一种失败也照常报告。

收尾（real 与 FORCE，每个用例之后，尽力而为）
  两个引擎 family 的 revision 全部注销并删除、SSM /<前缀>backend 下的参数全部删除、两个 ECR 仓库强制删除，最后删除本用例
  前缀的 runs 表：表名按前缀精确拼出，不论客户端是否收到过建表的应答都尝试删除（表不存在按正常处理、不算失败），没有建过
  表的用例因此多一次返回 ResourceNotFoundException 的 DeleteTable；删表请求被拒绝（ResourceInUseException：表仍在建立时；
  对仍在删除中的表，官方文档写的是不返回错误，真实账户上观察到过这个错误）时按 `_delete_table` 的重试处理，发起删除
  之后不等表删完。经 aws.ddb 发出过建表请求的其它表名一并删除，只限以本用例前缀开头的；不以它开头的不删，各记一条
  `teardown_failure`。一步失败（Exception）记 `teardown_failure` 后继续下一步。收尾被 BaseException 打断时（如 pytest-timeout
  以 signal 方式超时，抛出的不是 Exception 的子类）记一行 `teardown_interrupted`（打断时正在执行的那一步），再原样抛出，
  余下的步骤不再执行。
  用例开始前先查一次同前缀残留（复用了令牌时会有）：两个 family 的 ACTIVE 与 INACTIVE revision、SSM 参数、两个 ECR 仓库与
  runs 表，有则先清掉并记 `residue`。DELETE_IN_PROGRESS 的 revision 不在 ACTIVE 与 INACTIVE 的列举里、不算残留。runs 表
  仍在删除（DescribeTable 照常返回、TableStatus 为 DELETING）时同样不算残留：共用令牌的上一条命令收尾时发起删表、不等它
  删完，间隔很短的下一条命令会看到它，这是正在完成的清理、不是遗留的资源。残留检查等它消失（`_TABLE_GONE_WAIT`：每 2 秒
  查一次、至多 120 次），记一行 `waited_for_table_deletion`（前缀、表名、等了多少秒；不是问题），residue 里表的那一项为
  false；别无其它残留时不记 `residue`。等不到时残留检查失败（DescribeTable 报其它错误时同样），记一条 step 为 residue
  check 的 `teardown_failure`。其它状态的表算残留。family 名、SSM 路径、仓库名与表名按前缀精确拼出，不按前缀模糊匹配。清扫入口（按令牌清残留）：
  python harness.py --sweep <令牌> --region <region>
  `teardown_failure`、`teardown_interrupted` 与 `residue` 另记进 conftest 的问题清单（`waited_for_table_deletion` 不在其中）：
  终端摘要单独列出，用例全部通过时会话的退出码也为 1（见 conftest.py 模块头）。

参与方线程残留时跳过清理并终止会话（全部模式）
  原模块的多方组合用例经 `_Party` 在线程里执行各方，并提供模块级的 `lingering_party_threads()`：中止之后仍存活的参与方
  线程。这样的线程之后仍可能对账户发出调用。aws 夹具的收尾在清理之前先查询这个入口（原模块没有这个名字时视为没有残留），
  并把结果锁存：有残留时记一行 `lingering_party_threads`、**不执行**对账户的清理（残留的线程可能在清理期间恢复执行、重新写入
  资源，清理与它竞争没有意义，资源留给进程退出之后的 --sweep），只记一行带 skipped 的 `teardown`。只在清理之后查询会漏掉
  「在清理期间恢复、写入并结束」的线程：查询那一刻它已不在，资源却留在了账户里。conftest 的 `pytest_runtest_protocol` 在
  每条用例的全部阶段结束之后调用本模块的 `after_each_test`：取锁存的结果（不用 aws 夹具的用例此时现查一次），有残留就以
  pytest.exit 终止整个会话（退出码 2），提示里给出清扫命令。线程是守护线程，随进程退出一并结束，清扫要在进程退出之后执行。
"""
from __future__ import annotations

import contextlib
import functools
import importlib.util
import itertools
import re
import sys
import threading
import time
from collections import Counter
from datetime import timedelta
from pathlib import Path

import boto3
import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ORIG_PATH = REPO / "deploy_aws" / "tests" / "test_workers.py"

_conftest_mod = None


def _conftest():
    """同目录 conftest.py 的模块对象：配置、结果文件与问题清单都在那里。pytest 已载入它时取那一份（按文件路径在
    sys.modules 里找，模块名随 pytest 的导入方式而不同），否则（清扫入口）按路径另载一份。"""
    global _conftest_mod
    if _conftest_mod is None:
        target = HERE / "conftest.py"
        mod = next((m for m in list(sys.modules.values())
                    if Path(getattr(m, "__file__", None) or "/").resolve() == target), None)
        if mod is not None:
            _conftest_mod = mod
        else:
            spec = importlib.util.spec_from_file_location("workers_real_aws_conftest", HERE / "conftest.py")
            _conftest_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_conftest_mod)
    return _conftest_mod


if __name__ != "__main__":
    # 配置在 conftest 的 pytest_configure 里已校验过一次（不合法时 pytest 以用法错误结束、不进入收集）
    _S = _conftest().settings()
    MODE, REAL, FORCE = _S["mode"], _S["real"], _S["force"]
    REAL_PATHS = REAL or FORCE
    TOKEN, REGION_, EXEC_ROLE = _S["token"], _S["region"], _S["exec_role"]
    SETTLE, OBS_N, ADAPT = _S["settle"], _S["obs_n"], _S["adapt"]
    PREFIX_RE = _conftest().token_pattern(TOKEN)

# 补充用例只在 real 下必须执行；FORCE 下在 moto 上走代码路径
_REAL_ONLY = pytest.mark.skipif(__name__ == "__main__" or not REAL_PATHS,
                                reason="仅 real 模式（或 moto + GKP_FORCE_REAL_PATHS=1）执行")

# real 下预期失败的原用例：只有 call 阶段、该操作、该错误码的 ClientError 算预期失败（见模块头）
REAL_XFAIL = {
    "test_repush_retires_the_replaced_revision_and_prints_digest_change": {
        "operation": "PutImage", "code": "InvalidParameterException",
        "reason": "用例用 ecr.put_image 放一份没有 layer 的手写 manifest，真实 ECR 以 InvalidParameterException 拒绝；"
                  "与清理和推送协议无关"},
}

_FARGATE_MIN_MEMORY = {"256": 512, "512": 1024, "1024": 2048, "2048": 4096, "4096": 8192, "8192": 16384,
                       "16384": 32768}
_DDB_WRITES = frozenset({"put_item", "update_item", "delete_item", "batch_write_item", "transact_write_items"})
_DDB_WRITE_OPS = frozenset({"PutItem", "UpdateItem", "DeleteItem", "BatchWriteItem", "TransactWriteItems"})


# --------------------------------------------------------------------------- 结果文件

def record(kind: str, **data) -> None:
    try:
        _conftest().record(kind, **data)
    except Exception as exc:  # 结果文件写不进也不该让用例失败
        print(f"[workers_real_aws] 写结果文件失败：{exc!r}", file=sys.stderr)


def _client_config(region: str):
    from botocore.config import Config

    return Config(region_name=region, retries={"mode": "adaptive", "max_attempts": 10})


def _error_code(exc) -> str | None:
    resp = getattr(exc, "response", None)
    return resp.get("Error", {}).get("Code") if isinstance(resp, dict) else None


# --------------------------------------------------------------------------- 载入原模块

def _load_original():
    name = "test_workers"
    cached = sys.modules.get(name)
    if cached is not None and Path(getattr(cached, "__file__", "") or "").resolve() == ORIG_PATH:
        return cached
    if not ORIG_PATH.is_file():
        pytest.exit(f"找不到 {ORIG_PATH}", returncode=4)
    spec = None
    for finder in sys.meta_path:
        if type(finder).__name__ == "AssertionRewritingHook":
            with contextlib.suppress(Exception):
                spec = finder.find_spec(name, [str(ORIG_PATH.parent)])
            break
    if spec is None or Path(spec.origin or "").resolve() != ORIG_PATH:
        spec = importlib.util.spec_from_file_location(name, ORIG_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# 后四者经原模块全局读，不留副本以免读到旧值
_SKIP_COPY = {"aws", "_aws_env", "PREFIX", "ACCOUNT", "REGISTRY", "REGION"}

if __name__ != "__main__":
    orig = _load_original()
    for _k, _v in list(vars(orig).items()):
        if _k.startswith("__") or _k in _SKIP_COPY:
            continue
        globals()[_k] = _v
    ORIGINAL_TEST_NAMES = sorted(k for k, v in vars(orig).items() if k.startswith("test_") and callable(v))
    from gherkai_deploy_aws import names, workers  # noqa: E402  与原模块同一对象
else:
    from gherkai_deploy_aws import names  # 清扫入口只需要命名


# --------------------------------------------------------------------------- 种子模板的标记

_SEEDING = threading.local()   # depth > 0：当前线程正在执行用例的 seed_backend


def _seeding_now() -> bool:
    return getattr(_SEEDING, "depth", 0) > 0


def _marked_seed_backend(seed):
    """seed_backend 的包装：执行期间在当前线程置种子标记，参数、返回值与异常原样（判别依据见模块头）。"""
    @functools.wraps(seed)
    def wrapper(*args, **kwargs):
        _SEEDING.depth = getattr(_SEEDING, "depth", 0) + 1
        try:
            return seed(*args, **kwargs)
        finally:
            _SEEDING.depth -= 1
    return wrapper


if __name__ != "__main__":
    # 原用例与原模块的辅助函数经原模块的全局取 seed_backend，补充用例经本模块的全局取：两处换成同一个包装
    seed_backend = orig.seed_backend = _marked_seed_backend(orig.seed_backend)


# --------------------------------------------------------------------------- 预期失败的判定

def expected_failure(item, call) -> str | None:
    """conftest 的 pytest_runtest_makereport 对失败的报告调用：符合 REAL_XFAIL 里那一条的限定时返回原因（报告改为预期失败），
    否则返回 None（照常失败）。"""
    if not REAL_PATHS or call.when != "call" or call.excinfo is None:
        return None
    rule = REAL_XFAIL.get(getattr(item, "originalname", None) or item.name)
    if rule is None:
        return None
    from botocore.exceptions import ClientError

    exc = call.excinfo.value
    if (isinstance(exc, ClientError) and exc.operation_name == rule["operation"]
            and _error_code(exc) == rule["code"]):
        return rule["reason"]
    return None


# --------------------------------------------------------------------------- 壳

class LazyDdb:
    """惰性建表的 DynamoDB client 壳（见模块头）。`raw` 是底下的真 client。"""

    def __init__(self, inner, *, settle: float, nodeid: str):
        self.raw = inner
        self.settle = settle
        self.nodeid = nodeid
        self.lazy = True
        self.pending: dict[str, dict] = {}   # 只记下了参数、还没有发出建表请求的表
        self.requested: set[str] = set()     # 已发出建表请求的表：服务端可能已接受，不论客户端是否收到了应答
        self.built: set[str] = set()         # 建表请求已正常返回的表
        self._building = False
        self.writes = 0

    def create_table(self, **kw):
        name = kw["TableName"]
        if not self.lazy:
            self.mark_requested(name)
            resp = self.raw.create_table(**kw)
            self.built.add(name)
            return resp
        if name not in self.built:
            self.pending.setdefault(name, kw)
        return {"TableDescription": {"TableName": name, "TableStatus": "CREATING"}}

    def list_tables(self, **kw):
        resp = self.raw.list_tables(**kw)
        listed = list(resp.get("TableNames") or [])
        listed += [n for n in (*self.pending, *sorted(self.built)) if n not in listed]
        return {**resp, "TableNames": listed}

    def disable_lazy(self) -> None:
        self.lazy = False
        self.pending.clear()

    def mark_requested(self, name: str) -> None:
        """在发出建表请求之前调用：请求被服务端接受、客户端随后超时或连接中断时，表已在建，收尾据此仍去删它。"""
        self.requested.add(name)

    def mark_built(self, name: str) -> None:
        self.built.add(name)

    def unconfirmed(self) -> list[str]:
        """发出过建表请求、却没有收到正常应答的表（可能已建）。"""
        return sorted(self.requested - self.built)

    def never_requested(self) -> list[str]:
        """记下了参数、从未发出建表请求的表。"""
        return sorted(set(self.pending) - self.requested)

    def ensure(self) -> None:
        if not self.lazy or self._building or not self.pending:
            return
        self._building = True
        try:
            for name, kw in list(self.pending.items()):
                t0 = time.monotonic()
                self.mark_requested(name)
                self.raw.create_table(**kw)
                self.built.add(name)
                del self.pending[name]
                wait_table_active(self.raw, name)
                record("lazy_table_built", nodeid=self.nodeid, table=name, seconds=round(time.monotonic() - t0, 2))
        finally:
            self._building = False

    def after_write(self) -> None:
        self.writes += 1
        time.sleep(self.settle)

    def __getattr__(self, item):
        attr = getattr(self.raw, item)
        if not callable(attr):
            return attr

        def call(*a, **kw):
            if self.lazy:
                self.ensure()
            resp = attr(*a, **kw)
            if item in _DDB_WRITES:
                self.after_write()
            return resp

        return call

    # 经 boto3 默认 session 现建的 dynamodb 句柄（绕过 aws.ddb 的用例）走这两个钩子
    def foreign_before(self, model=None, **_):
        if model is not None and model.name != "ListTables" and self.lazy:
            self.ensure()

    def foreign_after(self, model=None, **_):
        if model is not None and model.name in _DDB_WRITE_OPS:
            self.after_write()


_REG_STATS: Counter = Counter()


class AdaptedEcs:
    """ECS client 壳：记下注册过的 revision 与注册响应里是否带 registeredAt；按 GKP_ADAPT 给种子模板做两项注册适配，
    被测代码的复制请求原样转发并核对（见模块头）。"""

    def __init__(self, inner, *, exec_role_arn: str | None, nodeid: str):
        self._inner = inner
        self.exec_role_arn = exec_role_arn
        self.nodeid = nodeid
        self.registered: list[str] = []
        self.seeded: dict[str, dict] = {}            # 种子模板 ARN → 装置给它补过或调过的字段与取值
        self.copy_mismatches: list[dict] = []        # 被测代码的复制请求没有原样带着这些字段

    def _adapt_seed(self, kw: dict) -> tuple[list[str], dict]:
        changes, fields = [], {}
        if ADAPT and "FARGATE" in (kw.get("requiresCompatibilities") or []):
            if self.exec_role_arn and not kw.get("executionRoleArn"):
                kw["executionRoleArn"] = fields["executionRoleArn"] = self.exec_role_arn
                changes.append("executionRoleArn")
            floor = _FARGATE_MIN_MEMORY.get(str(kw.get("cpu")))
            if floor and kw.get("memory") and int(kw["memory"]) < floor:
                changes.append(f"memory {kw['memory']} to {floor}")
                kw["memory"] = fields["memory"] = str(floor)
        return changes, fields

    def _check_copy(self, kw: dict) -> None:
        template = {t.get("key"): t.get("value") for t in kw.get("tags") or []}.get(names.TAG_TEMPLATE)
        expected = self.seeded.get(template) if template else None
        if not expected:   # 不是从本用例的种子模板复制，或装置没有改过那个模板：没有可能被掩盖的字段
            return
        diff = {f: {"template": v, "request": kw.get(f)} for f, v in expected.items()
                if kw.get(f) is None or str(kw.get(f)) != str(v)}
        if diff:
            row = {"nodeid": self.nodeid, "family": kw.get("family"), "template": template, "fields": diff}
            self.copy_mismatches.append(row)
            record("copy_request_mismatch", **row)

    def register_task_definition(self, **kw):
        seeding = _seeding_now()
        changes: list[str] = []
        if seeding:
            kw = dict(kw)
            changes, fields = self._adapt_seed(kw)
        else:
            self._check_copy(kw)   # 原样转发，不改动请求
        resp = self._inner.register_task_definition(**kw)
        td = resp["taskDefinition"]
        arn = td["taskDefinitionArn"]
        self.registered.append(arn)
        if seeding:
            self.seeded[arn] = fields
        _REG_STATS["with_registeredAt" if td.get("registeredAt") is not None else "without_registeredAt"] += 1
        if changes:
            record("adaptation", nodeid=self.nodeid, family=kw.get("family"), arn=arn, changes=changes)
        return resp

    def describe_task_definition(self, **kw):
        """原样转发；顺带统计带血缘 tags 的 revision 的 describe 结果里有没有 registeredAt。
        本壳在用例的 HookedEcs 之内，看到的是 ECS 的原始结果，HookedEcs 的覆盖发生在它返回之后、不影响这里的计数。"""
        resp = self._inner.describe_task_definition(**kw)
        tags = {t.get("key"): t.get("value") for t in resp.get("tags") or []}
        if "TAGS" in (kw.get("include") or []) and tags.get(names.TAG_VARIANT) and tags.get(names.TAG_DIGEST):
            td = resp.get("taskDefinition") or {}
            arn = td.get("taskDefinitionArn")
            key = "with" if td.get("registeredAt") is not None else "without"
            _DESCRIBE_LINEAGE[key].add(arn)
        return resp

    def __getattr__(self, item):
        return getattr(self._inner, item)


# 带血缘 tags 的 revision：describe（include TAGS）结果里带 / 不带 registeredAt 的 ARN（整个会话，按 ARN 去重）
_DESCRIBE_LINEAGE: dict[str, set] = {"with": set(), "without": set()}


def wait_table_active(ddb, table: str, *, timeout: float = 900.0) -> dict:
    deadline = time.monotonic() + timeout
    while True:
        t = ddb.describe_table(TableName=table)["Table"]
        if t.get("TableStatus") == "ACTIVE" and all(
                g.get("IndexStatus") == "ACTIVE" for g in t.get("GlobalSecondaryIndexes") or []):
            return t
        if time.monotonic() > deadline:
            raise TimeoutError(f"表 {table} 在 {timeout}s 内未就绪：{t.get('TableStatus')}")
        time.sleep(1.0 if REAL else 0.0)


# --------------------------------------------------------------------------- 会话状态

_STATE: dict = {}
_SEQ = itertools.count(1)


def _sts_account(session, region: str) -> str:
    return session.client("sts", config=_client_config(region)).get_caller_identity()["Account"]


def _resolve_exec_role(account: str) -> str | None:
    """注册适配补进模板的执行角色 ARN。auto 只出现在 moto 下：合成一个 ARN 字符串，不建任何角色。"""
    if not ADAPT or EXEC_ROLE == "none":
        return None
    if EXEC_ROLE == "auto":
        assert not REAL, "real 模式必须显式给出执行角色"
        return f"arn:aws:iam::{account}:role/gkp-moto-exec"
    return EXEC_ROLE


@pytest.fixture(scope="session", autouse=True)
def _gkp_session():
    record("harness", mode=MODE, force_real_paths=FORCE, token=TOKEN, region=REGION_, settle=SETTLE, adapt=ADAPT,
           exec_role=EXEC_ROLE, obs_n=OBS_N, original_test_functions=len(ORIGINAL_TEST_NAMES),
           original_loader=type(orig.__spec__.loader).__name__, original_file=orig.__file__)
    if REAL:
        session = boto3.session.Session(region_name=REGION_)
        _STATE["account"] = _sts_account(session, REGION_)
        _STATE["exec_role_arn"] = _resolve_exec_role(_STATE["account"])
        record("session_account", account=_STATE["account"], exec_role_arn=_STATE["exec_role_arn"])
    yield
    record("register_response_registeredAt", **dict(_REG_STATS))
    record("describe_lineage_registeredAt", with_registeredAt=len(_DESCRIBE_LINEAGE["with"]),
           without_registeredAt=len(_DESCRIBE_LINEAGE["without"]), without=sorted(_DESCRIBE_LINEAGE["without"]))


# --------------------------------------------------------------------------- 夹具

@pytest.fixture(autouse=True)
def _aws_env(monkeypatch):
    if REAL:
        for var in ("AWS_DEFAULT_REGION", "AWS_REGION"):
            monkeypatch.setenv(var, REGION_)
        return
    for var, value in (("AWS_ACCESS_KEY_ID", "t"), ("AWS_SECRET_ACCESS_KEY", "t"),
                       ("AWS_DEFAULT_REGION", REGION_), ("AWS_REGION", REGION_)):
        monkeypatch.setenv(var, value)
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.fixture
def aws(request, monkeypatch):
    seq = next(_SEQ)
    prefix = f"gkp{TOKEN}{seq:03d}-"
    nodeid = request.node.nodeid
    assert PREFIX_RE.match(prefix), prefix   # 绝不用原前缀：real 下它会碰到账户里同名的真实部署
    monkeypatch.setattr(orig, "PREFIX", prefix)
    monkeypatch.setattr(orig, "REGION", REGION_)
    record("prefix", nodeid=nodeid, prefix=prefix)

    if REAL:
        ctx = contextlib.nullcontext()
    else:
        from moto import mock_aws

        ctx = mock_aws()
    with ctx:
        session = boto3.session.Session(region_name=REGION_)
        if not REAL_PATHS:
            monkeypatch.setattr(orig, "REGISTRY", f"{orig.ACCOUNT}.dkr.ecr.{REGION_}.amazonaws.com")
            raw = {svc: session.client(svc, region_name=REGION_) for svc in ("ssm", "ecs", "ecr", "dynamodb")}
            try:
                yield workers.Aws(ssm=raw["ssm"], ecs=raw["ecs"], ecr=raw["ecr"], ddb=raw["dynamodb"])
            finally:
                _latch_lingering(nodeid)   # 在模拟环境结束之前查询并锁存，与下面的分支同一时机
            return

        cfg = _client_config(REGION_)
        raw = {svc: session.client(svc, config=cfg) for svc in ("ssm", "ecs", "ecr", "dynamodb")}
        if REAL:
            account, role_arn = _STATE["account"], _STATE.get("exec_role_arn")
        else:  # FORCE：每个用例一个独立的 moto，账号在这里取一次
            account = _sts_account(session, REGION_)
            role_arn = _resolve_exec_role(account)
        monkeypatch.setattr(orig, "ACCOUNT", account)
        monkeypatch.setattr(orig, "REGISTRY", f"{account}.dkr.ecr.{REGION_}.amazonaws.com")

        lazy = LazyDdb(raw["dynamodb"], settle=SETTLE, nodeid=nodeid)
        ecs = AdaptedEcs(raw["ecs"], exec_role_arn=role_arn, nodeid=nodeid)
        # 绕过 aws.ddb 的用例经 boto3 默认 session 现建句柄：换一个新的默认 session 并挂上同一个惰性建表
        default = boto3.session.Session(region_name=REGION_)
        default.events.register("before-call.dynamodb", lazy.foreign_before)
        default.events.register("after-call.dynamodb", lazy.foreign_after)
        monkeypatch.setattr(boto3, "DEFAULT_SESSION", default)

        _precheck_residue(raw, prefix, nodeid)
        try:
            yield workers.Aws(ssm=raw["ssm"], ecs=ecs, ecr=raw["ecr"], ddb=lazy)
        finally:
            # 清理之前查询并锁存参与方线程残留：有残留时不清理（见模块头）
            if _latch_lingering(nodeid):
                record("teardown", nodeid=nodeid, prefix=prefix, skipped="lingering_party_threads", failures=None,
                       table_built=sorted(lazy.built), table_create_unconfirmed=lazy.unconfirmed(),
                       pending_never_built=lazy.never_requested(), ddb_writes=lazy.writes)
            else:
                _teardown(raw, prefix, lazy, nodeid)
        if ecs.copy_mismatches:
            raise AssertionError(
                "被测代码从种子模板复制 revision 的请求没有原样带着模板的字段（装置只适配种子模板、不替复制请求补字段）："
                + "；".join(f"{m['family']} {m['fields']}" for m in ecs.copy_mismatches))


# --------------------------------------------------------------------------- 收尾与清扫

def _family_arns(ecs, family: str, status: str) -> list[str]:
    arns, token = [], None
    while True:
        kw = {"familyPrefix": family, "status": status}
        if token:
            kw["nextToken"] = token
        resp = ecs.list_task_definitions(**kw)
        arns += [a for a in resp.get("taskDefinitionArns") or [] if a.rsplit("/", 1)[-1].rsplit(":", 1)[0] == family]
        token = resp.get("nextToken")
        if not token:
            return arns


def _purge_family(ecs, family: str, failures: list) -> None:
    active = _family_arns(ecs, family, "ACTIVE")
    for arn in active:
        try:
            ecs.deregister_task_definition(taskDefinition=arn)
        except Exception as exc:
            failures.append(("deregister", arn, repr(exc)))
    every = list(dict.fromkeys(active + _family_arns(ecs, family, "INACTIVE")))
    for i in range(0, len(every), 10):
        batch = every[i:i + 10]
        try:
            resp = ecs.delete_task_definitions(taskDefinitions=batch)
        except Exception as exc:
            failures.append(("delete_task_definitions", batch, repr(exc)))
            continue
        for f in resp.get("failures") or []:
            failures.append(("delete_task_definitions", f.get("arn"), f"{f.get('reason')} {f.get('detail') or ''}"))


def _ssm_names(ssm, path: str) -> list[str]:
    out, token = [], None
    while True:
        kw = {"Path": path, "Recursive": True}
        if token:
            kw["NextToken"] = token
        resp = ssm.get_parameters_by_path(**kw)
        out += [p["Name"] for p in resp.get("Parameters") or []]
        token = resp.get("NextToken")
        if not token:
            return out


def _delete_ssm(ssm, params: list[str], failures: list) -> None:
    for i in range(0, len(params), 10):
        batch = params[i:i + 10]
        try:
            resp = ssm.delete_parameters(Names=batch)
            for n in resp.get("InvalidParameters") or []:
                failures.append(("delete_parameters", n, "InvalidParameters"))
        except Exception as exc:
            failures.append(("delete_parameters", batch, repr(exc)))


def _delete_repo(ecr, repo: str, failures: list) -> None:
    try:
        ecr.delete_repository(repositoryName=repo, force=True)
    except Exception as exc:
        if _error_code(exc) != "RepositoryNotFoundException":
            failures.append(("delete_repository", repo, repr(exc)))


# 等一张表从 DescribeTable 里消失：每 2 秒查一次、至多 120 次（约 4 分钟）。残留检查里删除中的表与清掉残留表之后都用它
_TABLE_GONE_WAIT = {"Delay": 2, "MaxAttempts": 120}


def _delete_table(ddb, table: str, failures: list, *, real: bool, wait: bool = False) -> None:
    # 表还在 CREATING / UPDATING（补充用例 a 中途失败时索引可能仍在建立）时 DeleteTable 报 ResourceInUseException；
    # 对已在删除中的表再次 DeleteTable，官方文档写的是不返回错误，真实账户上观察到过同样的 ResourceInUseException，
    # 按同一重试处理，重试时表已不存在即结束。收尾、用例开始前的残留清理与 --sweep 都经这里：
    # real 下每 15 秒重试，至多约 25 分钟（索引建立的上限按补充用例 a 的 20 分钟估），仍不行就记进 failures
    # （收尾与残留清理记为 teardown_failure、留给 --sweep；--sweep 列为失败、退出码为 1）
    deadline = time.monotonic() + (1500 if real else 0)
    while True:
        try:
            ddb.delete_table(TableName=table)
            break
        except Exception as exc:
            code = _error_code(exc)
            if code == "ResourceInUseException" and time.monotonic() < deadline:
                time.sleep(15)
                continue
            if code != "ResourceNotFoundException":
                failures.append(("delete_table", table, repr(exc)))
            return
    if wait:
        with contextlib.suppress(Exception):
            ddb.get_waiter("table_not_exists").wait(TableName=table, WaiterConfig=_TABLE_GONE_WAIT)


def _purge_prefix(raw, prefix: str, *, tables: list[str], failures: list, progress: dict,
                  wait_table: bool = False) -> None:
    """按前缀精确拼出的资源逐步删除；一步失败（Exception）记进 failures 后继续。progress["step"] 是正在执行的那一步，
    BaseException 打断时调用方据此记下停在哪一步。"""
    steps = [(f"ecs {names.task_def_name(prefix, e)}",
              lambda e=e: _purge_family(raw["ecs"], names.task_def_name(prefix, e), failures)) for e in names.ENGINES]
    steps.append(("ssm", lambda: _delete_ssm(raw["ssm"], _ssm_names(raw["ssm"], f"/{prefix}backend"), failures)))
    steps += [(f"ecr {names.ecr_repo_name(prefix, e)}",
               lambda e=e: _delete_repo(raw["ecr"], names.ecr_repo_name(prefix, e), failures)) for e in names.ENGINES]
    steps += [(f"ddb {t}", lambda t=t: _delete_table(raw["dynamodb"], t, failures, real=REAL, wait=wait_table))
              for t in tables]
    for label, fn in steps:
        progress["step"] = label
        try:
            fn()
        except Exception as exc:
            failures.append((label, None, repr(exc)))
    progress["step"] = None


def _purge_recorded(raw, prefix: str, nodeid: str, *, tables: list[str], wait_table: bool = False,
                    label: str = "") -> int:
    """_purge_prefix 加记录：失败的每一步记 `teardown_failure`；被 BaseException 打断时先记下已有的失败与一行
    `teardown_interrupted`（停在哪一步），再原样抛出。返回失败的步数。"""
    failures: list = []
    progress: dict = {"step": None}

    def flush() -> None:
        for step, target, error in failures:
            record("teardown_failure", nodeid=nodeid, prefix=prefix, step=f"{label}{step}", target=target, error=error)

    try:
        _purge_prefix(raw, prefix, tables=tables, failures=failures, progress=progress, wait_table=wait_table)
    except Exception as exc:
        failures.append(("teardown", None, repr(exc)))
    except BaseException as exc:
        flush()
        record("teardown_interrupted", nodeid=nodeid, prefix=prefix, step=f"{label}{progress['step']}",
               error=repr(exc))
        raise
    flush()
    return len(failures)


def _teardown(raw, prefix: str, lazy: LazyDdb, nodeid: str) -> None:
    # 本用例前缀的 runs 表按前缀精确拼出、总是尝试删除（不存在按正常处理）：建表请求可能已被服务端接受而客户端没有收到
    # 应答，是否建过不能只看客户端的记录。另加发出过建表请求的其它表名（用例只建这一张，留作兜底），只取以本用例前缀开头的：
    # 收尾不动前缀之外的资源，不在前缀下的表名记一条收尾失败、留给使用者处理
    runs_table = names.default_name(prefix, names.BASE_RUNS_TABLE)
    others = sorted((lazy.requested | lazy.built) - {runs_table})
    tables = [runs_table] + [t for t in others if t.startswith(prefix)]
    failures = _purge_recorded(raw, prefix, nodeid, tables=tables)
    for t in others:
        if not t.startswith(prefix):
            record("teardown_failure", nodeid=nodeid, prefix=prefix, step=f"ddb {t}", target=t,
                   error="表名不以本用例的前缀开头，收尾没有删除它")
            failures += 1
    record("teardown", nodeid=nodeid, prefix=prefix, failures=failures, table_built=sorted(lazy.built),
           table_create_unconfirmed=lazy.unconfirmed(), pending_never_built=lazy.never_requested(),
           ddb_writes=lazy.writes)


def _repo_exists(ecr, repo: str) -> bool:
    try:
        ecr.describe_repositories(repositoryNames=[repo])
        return True
    except Exception as exc:
        if _error_code(exc) != "RepositoryNotFoundException":
            raise
        return False


def _runs_table_left(ddb, table: str, prefix: str, nodeid: str) -> bool:
    """按前缀拼出的 runs 表是不是残留。不存在不是；状态为 DELETING 也不是：它是上一条共用令牌的命令收尾时发起的删除、
    正在完成，等它从 DescribeTable 里消失（时限同 `_TABLE_GONE_WAIT`），记一行 `waited_for_table_deletion`（不是问题）。
    等不到时抛 TimeoutError，由调用方按残留检查失败处理；DescribeTable 的其它错误同样抛出。其它状态都算残留。"""
    try:
        status = ddb.describe_table(TableName=table)["Table"].get("TableStatus")
    except Exception as exc:
        if _error_code(exc) != "ResourceNotFoundException":
            raise
        return False
    if status != "DELETING":
        return True
    from botocore.exceptions import WaiterError

    t0 = time.monotonic()
    try:
        ddb.get_waiter("table_not_exists").wait(TableName=table, WaiterConfig=_TABLE_GONE_WAIT)
    except WaiterError as exc:
        # 只有等满次数才是「没有删完」；等待中 DescribeTable 报了别的错误（如权限不足）时原样抛出，错误码留在消息里
        if not str(exc.kwargs.get("reason", "")).startswith("Max attempts exceeded"):
            raise
        raise TimeoutError(f"表 {table} 处于 DELETING，{round(time.monotonic() - t0, 1)} 秒内没有删完：{exc}") from exc
    record("waited_for_table_deletion", nodeid=nodeid, prefix=prefix, table=table,
           seconds=round(time.monotonic() - t0, 2))
    return False


def find_residue(raw, prefix: str, nodeid: str) -> dict:
    """前缀下已有的资源：两个 family 的 ACTIVE 与 INACTIVE revision、SSM 参数、两个 ECR 仓库、runs 表（删除中的不算，
    见 `_runs_table_left`）。都为空即没有残留。"""
    table = names.default_name(prefix, names.BASE_RUNS_TABLE)
    families = {e: names.task_def_name(prefix, e) for e in names.ENGINES}
    has_table = _runs_table_left(raw["dynamodb"], table, prefix, nodeid)
    return {
        "revisions": {e: _family_arns(raw["ecs"], f, "ACTIVE") for e, f in families.items()},
        "inactive_revisions": {e: _family_arns(raw["ecs"], f, "INACTIVE") for e, f in families.items()},
        "params": _ssm_names(raw["ssm"], f"/{prefix}backend"),
        "repos": [r for r in (names.ecr_repo_name(prefix, e) for e in names.ENGINES) if _repo_exists(raw["ecr"], r)],
        "table": has_table,
    }


def _has_residue(found: dict) -> bool:
    return bool(any(found["revisions"].values()) or any(found["inactive_revisions"].values()) or found["params"]
                or found["repos"] or found["table"])


def _precheck_residue(raw, prefix: str, nodeid: str) -> None:
    """同前缀残留（复用了令牌、上次收尾失败）会让比较 revision 列表的用例出现与被测代码无关的失败：有则先清掉。"""
    try:
        found = find_residue(raw, prefix, nodeid)
    except Exception as exc:
        record("teardown_failure", nodeid=nodeid, prefix=prefix, step="residue check", target=None, error=repr(exc))
        return
    if _has_residue(found):
        record("residue", nodeid=nodeid, prefix=prefix, **found)
        _purge_recorded(raw, prefix, nodeid, tables=[names.default_name(prefix, names.BASE_RUNS_TABLE)],
                        wait_table=True, label="residue ")


def sweep(token: str, region: str) -> int:
    """列出并清掉名字形如 gkp<令牌><序号>- 的 family、SSM 参数、ECR 仓库、DynamoDB 表。不碰 IAM。"""
    cf = _conftest()
    if not re.fullmatch(cf.TOKEN_RE, token):
        print(f"令牌只能是 1-12 位小写字母数字、且以字母结尾：{token!r}")
        return 2
    pat = cf.token_pattern(token)
    stem = f"gkp{token}"
    session = boto3.session.Session(region_name=region)
    cfg = _client_config(region)
    c = {svc: session.client(svc, config=cfg) for svc in ("ssm", "ecs", "ecr", "dynamodb")}
    failures: list = []

    families = set()
    for page in c["ecs"].get_paginator("list_task_definition_families").paginate(familyPrefix=stem, status="ALL"):
        families.update(f for f in page.get("families") or [] if pat.match(f))
    for fam in sorted(families):
        print(f"family {fam}")
        _purge_family(c["ecs"], fam, failures)

    params = []
    for page in c["ssm"].get_paginator("describe_parameters").paginate(
            ParameterFilters=[{"Key": "Name", "Option": "BeginsWith", "Values": [f"/{stem}"]}]):
        params += [p["Name"] for p in page.get("Parameters") or [] if pat.match(p["Name"].lstrip("/"))]
    print(f"ssm 参数 {len(params)} 个")
    _delete_ssm(c["ssm"], params, failures)

    for page in c["ecr"].get_paginator("describe_repositories").paginate():
        for repo in page.get("repositories") or []:
            if pat.match(repo["repositoryName"]):
                print(f"ecr {repo['repositoryName']}")
                _delete_repo(c["ecr"], repo["repositoryName"], failures)

    for page in c["dynamodb"].get_paginator("list_tables").paginate():
        for table in page.get("TableNames") or []:
            if pat.match(table):
                print(f"table {table}")
                _delete_table(c["dynamodb"], table, failures, real=True)

    for f in failures:
        print("失败：", f)
    print(f"清扫完成，失败 {len(failures)} 项")
    return 1 if failures else 0


# --------------------------------------------------------------------------- 参与方线程残留

def _lingering_now() -> list[str]:
    query = getattr(orig, "lingering_party_threads", None)
    return [t.name for t in query()] if query is not None else []


def _latch_lingering(nodeid: str) -> bool:
    """aws 夹具的收尾在清理之前调用：查询参与方线程残留，有则记一行并锁存给 after_each_test，返回 True（不清理）。"""
    threads = _lingering_now()
    if not threads:
        return False
    _STATE["lingering"] = {"nodeid": nodeid, "threads": threads, "cleanup_skipped": REAL_PATHS}
    record("lingering_party_threads", nodeid=nodeid, threads=threads, cleanup_skipped=REAL_PATHS)
    return True


def after_each_test(nodeid: str) -> None:
    """每条用例的全部阶段结束之后由 conftest 调用：取 aws 夹具锁存的残留结果（不用 aws 夹具的用例在这里现查一次），
    有残留就终止会话（见模块头）。"""
    latched = _STATE.pop("lingering", None)
    if latched is None:
        threads = _lingering_now()
        if not threads:
            return
        latched = {"nodeid": nodeid, "threads": threads, "cleanup_skipped": False}
        record("lingering_party_threads", **latched)
    skipped = "该条用例对账户的清理已跳过、资源留在原处（残留的线程仍可能写入，清理与它竞争没有意义），" \
        if latched["cleanup_skipped"] else ""
    where = (f"进程退出之后执行 python tools/workers_real_aws/harness.py --sweep {TOKEN} --region {REGION_} 清扫残留"
             if REAL else "moto 模式下不必清扫")
    pytest.exit(f"用例 {nodeid} 结束之后仍有参与方线程存活（{'、'.join(latched['threads'])}），它们之后仍可能对账户发出"
                f"调用，已终止执行、后续用例不再执行；{skipped}{where}",
                returncode=pytest.ExitCode.INTERRUPTED)


# --------------------------------------------------------------------------- 补充用例（real；FORCE 下在 moto 上走代码路径）

def _index_state(ddb, table: str) -> dict:
    t = ddb.describe_table(TableName=table)["Table"]
    for g in t.get("GlobalSecondaryIndexes") or []:
        if g["IndexName"] == names.RUNS_STATUS_GROUP_GSI:
            return {"IndexStatus": g.get("IndexStatus"), "Backfilling": g.get("Backfilling"),
                    "ItemCount": g.get("ItemCount")}
    return {"IndexStatus": None, "Backfilling": None}


def _batch_put(ddb, table: str, items: list[dict]) -> None:
    for i in range(0, len(items), 25):
        req = {table: [{"PutRequest": {"Item": it}} for it in items[i:i + 25]]}
        for _ in range(20):
            resp = ddb.batch_write_item(RequestItems=req)
            req = resp.get("UnprocessedItems") or {}
            if not req:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("batch_write_item 有未处理的 item")


def _state_items(n: int) -> list[dict]:
    """与 `_put_state` 形态相同的 STATE item（分组属性取 core 写端的派生函数）；1/3 为 running，其余 passed，全不引用候选。"""
    from gherkai_core.adapters.run_store.ddb import status_group
    from gherkai_core.model import Status

    out = []
    for i in range(n):
        status = "running" if i % 3 == 0 else "passed"
        out.append({"run_id": {"S": f"r-{i:04d}"}, "item_type": {"S": "STATE"}, "status": {"S": status},
                    names.STATE_STATUS_GROUP_ATTR: {"S": status_group(Status(status))},
                    names.STATE_WORKER_TASK_DEF_ARNS_ATTR: {"L": [{"S": f"arn:gkp-obs-{i}"}]}})
    return out


@_REAL_ONLY
@pytest.mark.timeout(4200)   # 含收尾：索引仍在建立时 DeleteTable 要等（见 _delete_table）
def test_realaws_cleanup_skips_while_the_status_group_index_is_creating(aws):
    """a. 状态分组索引仍在建立（CREATING）时清理跳过；索引 ACTIVE 之后下一趟回收。"""
    nodeid = "a:index-creating"
    templates = seed_backend(aws)  # noqa: F821  原模块的辅助函数
    aws.ddb.disable_lazy()
    raw = aws.ddb.raw
    table = names.default_name(orig.PREFIX, names.BASE_RUNS_TABLE)
    aws.ddb.mark_requested(table)   # 先登记：请求被接受而应答丢失时收尾仍删它
    raw.create_table(
        TableName=table,
        KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"}, {"AttributeName": "item_type", "KeyType": "RANGE"}],
        AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"},
                              {"AttributeName": "item_type", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST")
    aws.ddb.mark_built(table)
    wait_table_active(raw, table)
    _batch_put(raw, table, _state_items(300))
    record("step", nodeid=nodeid, step="table without GSI ready, 300 STATE items written")
    cand = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))  # noqa: F821

    raw.update_table(
        TableName=table,
        AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"},
                              {"AttributeName": names.STATE_STATUS_GROUP_ATTR, "AttributeType": "S"}],
        GlobalSecondaryIndexUpdates=[{"Create": {
            "IndexName": names.RUNS_STATUS_GROUP_GSI,
            "KeySchema": [{"AttributeName": names.STATE_STATUS_GROUP_ATTR, "KeyType": "HASH"},
                          {"AttributeName": "run_id", "KeyType": "RANGE"}],
            "Projection": {"ProjectionType": "INCLUDE", "NonKeyAttributes": [names.STATE_WORKER_TASK_DEF_ARNS_ATTR]},
        }}])
    t_update = time.monotonic()
    before = _index_state(raw, table)
    ecs = HookedEcs(aws.ecs)  # noqa: F821
    outcome, text = _cleanup(aws, NOW, ecs=ecs)  # noqa: F821
    after = _index_state(raw, table)
    valid = before["IndexStatus"] == "CREATING" and after["IndexStatus"] == "CREATING"
    still_active = cand in _revisions(aws, "novaact")  # noqa: F821
    record("index_creating_observation", nodeid=nodeid, before=before, after=after, valid=valid,
           candidate_active=still_active, deregistered=ecs.deregistered, output=text,
           deleted=list(outcome.deleted), kept=[list(k) for k in outcome.kept])
    if valid:
        assert still_active, outcome
        assert "这次没有回收旧的 revision" in text and names.RUNS_STATUS_GROUP_GSI in text, text
        assert ecs.deregistered == []

    deadline = time.monotonic() + 1200
    while True:
        state = _index_state(raw, table)
        if state["IndexStatus"] == "ACTIVE":
            break
        assert time.monotonic() < deadline, f"索引 20 分钟内未 ACTIVE：{state}"
        time.sleep(15 if REAL else 0)
    record("index_became_active", nodeid=nodeid, seconds_after_update=round(time.monotonic() - t_update, 1),
           state=state)
    ecs2 = HookedEcs(aws.ecs)  # noqa: F821
    outcome2, text2 = _cleanup(aws, NOW, ecs=ecs2)  # noqa: F821
    reclaimed = cand not in _revisions(aws, "novaact")  # noqa: F821
    record("index_active_pass", nodeid=nodeid, reclaimed=reclaimed, deleted=list(outcome2.deleted),
           kept=[list(k) for k in outcome2.kept], output=text2)
    assert reclaimed, (outcome2, text2)
    if not valid:
        pytest.xfail(f"观察作废：pass 前后的索引状态不都是 CREATING（前 {before}，后 {after}）")


@_REAL_ONLY
@pytest.mark.timeout(600)
def test_realaws_cleanup_skips_when_the_runs_table_is_missing(aws):
    """b. runs 表不存在时清理跳过。"""
    templates = seed_backend(aws)  # noqa: F821
    aws.ddb.disable_lazy()
    cand = _unmapped_retired(aws, templates, retired_at=NOW - timedelta(hours=3))  # noqa: F821
    ecs = HookedEcs(aws.ecs)  # noqa: F821
    outcome, text = _cleanup(aws, NOW, ecs=ecs)  # noqa: F821
    still_active = cand in _revisions(aws, "novaact")  # noqa: F821
    record("table_missing_observation", nodeid="b:table-missing", candidate_active=still_active,
           deregistered=ecs.deregistered, output=text, kept=[list(k) for k in outcome.kept])
    assert still_active and outcome.deleted == ()
    assert "这次没有回收旧的 revision" in text, text
    assert ecs.deregistered == []


def _poll(check, *, t0: float, timeout: float = 30.0, interval: float = 0.1) -> float | None:
    """从 t0 起轮询到 check() 为真，返回经过的秒数；超时返回 None。"""
    while True:
        if check():
            return round(time.monotonic() - t0, 3)
        if time.monotonic() - t0 > timeout:
            return None
        time.sleep(interval if REAL else 0)


def _fresh_client(svc: str):
    return boto3.session.Session(region_name=REGION_).client(svc, config=_client_config(REGION_))


def _summary(rows: list[dict], key: str) -> dict:
    delays = [r[key] for r in rows if r[key] is not None]
    return {"n": len(rows), "never": sum(1 for r in rows if r[key] is None),
            "max_s": max(delays) if delays else None, "mean_s": round(sum(delays) / len(delays), 3) if delays else None}


@_REAL_ONLY
@pytest.mark.timeout(3000)
def test_realaws_visibility_and_ordering_observations(aws):
    """c. 可见性与次序的观察：只记录数字，不作通过与否的断言。"""
    templates = seed_backend(aws)  # noqa: F821
    path = f"/{orig.PREFIX}backend"

    # ① put_parameter 成功返回后，另一个独立 session/client 的 get_parameters_by_path 是否立刻读到
    rows = []
    for i in range(OBS_N):
        name = f"{path}/gkp-obs/p{i:03d}"
        other = _fresh_client("ssm")
        aws.ssm.put_parameter(Name=name, Value=str(i), Type="String", Overwrite=True)
        t0 = time.monotonic()
        immediate = name in _ssm_names(other, path)
        delay = 0.0 if immediate else _poll(lambda n=name, o=other: n in _ssm_names(o, path), t0=t0)
        rows.append({"i": i, "immediate": immediate, "delay_s": delay})
    record("obs_ssm_put_then_by_path", rows=rows, immediate=sum(r["immediate"] for r in rows),
           summary=_summary(rows, "delay_s"))

    # ② tag_resource 成功返回后，另一个独立 client 的 describe_task_definition(include TAGS) 是否立刻读到
    rev = _register_unmapped(aws, templates, digest="sha256:" + "e" * 64, variant="obs")  # noqa: F821
    other_ecs = _fresh_client("ecs")

    def tag_value(client, key):
        resp = client.describe_task_definition(taskDefinition=rev, include=["TAGS"])
        return {t["key"]: t["value"] for t in resp.get("tags") or []}.get(key)

    rows = []
    for i in range(OBS_N):
        value = f"v{i:03d}"
        aws.ecs.tag_resource(resourceArn=rev, tags=[{"key": "gkp-obs", "value": value}])
        t0 = time.monotonic()
        immediate = tag_value(other_ecs, "gkp-obs") == value
        delay = 0.0 if immediate else _poll(lambda v=value: tag_value(other_ecs, "gkp-obs") == v, t0=t0)
        rows.append({"i": i, "immediate": immediate, "delay_s": delay})
    record("obs_ecs_tag_then_describe_other_client", rows=rows, immediate=sum(r["immediate"] for r in rows),
           summary=_summary(rows, "delay_s"))

    # ③ 同一连接 tag 紧接 untag，之后立刻读与隔 2 秒再读，tag 是否都已不在（同连接与另一连接各读一次）
    rows = []
    for i in range(OBS_N):
        aws.ecs.tag_resource(resourceArn=rev, tags=[{"key": "gkp-obs3", "value": f"v{i:03d}"}])
        aws.ecs.untag_resource(resourceArn=rev, tagKeys=["gkp-obs3"])
        row = {"i": i, "absent_now_same": tag_value(aws.ecs, "gkp-obs3") is None,
               "absent_now_other": tag_value(other_ecs, "gkp-obs3") is None}
        time.sleep(2 if REAL else 0)
        row["absent_2s_same"] = tag_value(aws.ecs, "gkp-obs3") is None
        row["absent_2s_other"] = tag_value(other_ecs, "gkp-obs3") is None
        rows.append(row)
    # 次序倒置（untag 先于 tag 生效）时 tag 会在之后重新出现：全部轮次结束后再隔 10 秒读一次终态
    time.sleep(10 if REAL else 0)
    final = {"absent_same": tag_value(aws.ecs, "gkp-obs3") is None,
             "absent_other": tag_value(other_ecs, "gkp-obs3") is None}
    record("obs_ecs_tag_untag_then_read", rows=rows,
           counts={k: sum(r[k] for r in rows) for k in ("absent_now_same", "absent_now_other", "absent_2s_same",
                                                        "absent_2s_other")}, n=len(rows), final_after_10s=final)

    # ④ 本用例注册过的 revision 的 describe 结果是否都带 registeredAt，按带不带血缘 tags 分开记（整个会话里经清理与
    #    推送 describe 到的带血缘 revision 另由 describe_lineage_registeredAt 一行汇总）
    counts = Counter()
    without_at = []
    for arn in aws.ecs.registered:
        resp = aws.ecs.describe_task_definition(taskDefinition=arn, include=["TAGS"])
        tags = {t["key"]: t["value"] for t in resp.get("tags") or []}
        kind = "lineage" if tags.get(names.TAG_VARIANT) and tags.get(names.TAG_DIGEST) else "no_lineage"
        has = resp["taskDefinition"].get("registeredAt") is not None
        counts[f"{kind}_{'with' if has else 'without'}_registeredAt"] += 1
        if not has:
            without_at.append(arn)
    record("obs_describe_registeredAt", **dict(counts), without=without_at,
           register_response_counts=dict(_REG_STATS))


# --------------------------------------------------------------------------- 清扫入口

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="清扫本装置在真实账户里留下的资源（只动名字形如 gkp<令牌><序号>- 的资源，不碰 IAM）")
    parser.add_argument("--sweep", metavar="TOKEN", required=True, help="会话令牌（资源名前缀 gkp<令牌><序号>-）")
    parser.add_argument("--region", default=_conftest().env_region(),
                        help="region（缺省取 GKP_REGION / AWS_REGION / AWS_DEFAULT_REGION）")
    ns = parser.parse_args()
    if not ns.region:
        parser.error("需要 region：给 --region 或设 GKP_REGION / AWS_REGION / AWS_DEFAULT_REGION")
    sys.exit(sweep(ns.sweep.lower(), ns.region))
