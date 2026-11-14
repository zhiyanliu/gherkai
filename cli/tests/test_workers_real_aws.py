"""`tools/workers_real_aws/` 装置的自检：缺省的 moto 模式下，装置收集到的用例与直接执行 `deploy_aws/tests/test_workers.py`
收集到的相同（只多装置自己的补充用例），而且全部通过、补充用例跳过。

守的是测试文件与装置之间的脱节：测试文件新增或改名用例、改了夹具或模块全局的读法时，装置若跟不上，这里先失败，
而不是等到下一次对真实账户执行时才发现。装置在 moto 模式下也给每条用例换一个非缺省前缀，自检另取一个非缺省 region，
写死缺省前缀或缺省 region 的断言、由它们在导入时派生出的模块全局，在这里就会失败。另一条在 moto 上执行真实账户模式的
代码路径（惰性建表、注册适配、收尾与三条补充用例），守补充用例借用的原模块辅助函数改名或改签名，并核对不用 aws 夹具的
用例（`_Party` 自身的自测）不触发建表、适配与收尾。

失败不被装置吞掉：其余几条在测试文件的临时副本里注入用例（个别另变异被测代码的副本），在 moto 上以真实账户模式的代码
路径执行装置，分别核对：断言失败与执行异常照常让会话以非零退出码结束、完整的失败信息记进结果文件；收尾失败在用例通过时
也让会话以非零退出码结束并在终端摘要里列出；收尾被超时打断时记为「清理被中断」；参与方线程在用例结束之后仍存活（一直
等待的，与在清理期间恢复执行、写入并结束的）时清理被跳过、会话被终止且后续用例不再执行；预期失败只认这条用例 call 阶段、
PutImage 操作与 InvalidParameterException 的 ClientError（文字相同的其它异常、以它为起因的 AssertionError、setup 与 teardown
阶段的同一个错误、别的用例抛出的同一个错误都照常失败），给了 --runxfail 时不改判；被测代码的复制请求漏带模板的执行角色时
用例失败（装置不替它补）；用例开始前只有 ECR 仓库或只有 INACTIVE revision 的同前缀残留也被发现；建表请求已被服务端接受、客户端随后收到连接错误时
收尾仍删掉这张表，用例建了前缀之外的表时收尾不删它、记为收尾失败；thread 方式的超时直接终止
进程、装置来不及记下问题时，summarize.py 从结果文件推出收尾没有完成。这几条都另核对 summarize.py 在第一行计数之后列出装置
记下的问题与会话退出码。注入的手段见 `_injected_mirror`。

summarize.py 的推断另有几条纯逻辑的核对，直接构造结果文件：多次会话写进同一个文件时按会话各自判断（纯 moto 会话不被误报、
后来的会话不遮掉较早会话没有完成的收尾）、只有一次会话时输出不变、最后一行没有完整写入时报告并用之前的记录汇总、被终止的
会话留下的半行后面接着下一次会话的 session_start 时照常读入后者（同一行或下一行；装置追加之前补换行，得到的是后一种）、
缺换行而连在一起的完整对象都保留、其余坏行（包括接在 session_start 前面却不可能写成合法 JSON 的部分）报错并指出行号。
判断「是不是一个 JSON 对象没有写完的开头」的逻辑另对几条合法记录的每一个截断位置与随机改坏的开头逐一核对。

残留检查遇到删除中的 runs 表：moto 上构造不出 DELETING，另用替身 client 在子进程里直接调用装置的残留检查，核对先 DELETING
后消失的表不算残留、只记一行等待信息（同时有其它残留时 residue 照记、表的那一项为 false），ACTIVE、CREATING 等其它状态的表
算残留，DELETING 一直不消失时等满时限之后记为收尾失败，DescribeTable 报其它错误时同样记为收尾失败（见 `_RESIDUE_PROBE`）。

都在子进程里执行（装置要在全新的 pytest 会话里载入原模块、换掉夹具）；用例自带的超时留出慢机器上的余量。另有几条只核对
配置校验：真实账户模式缺执行角色、执行角色不合法或缺 region，与 GKP_SETTLE、GKP_OBS_N 取值不合法时，在收集之前以用法错误
结束，不发出任何 AWS 请求。
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from _doc_rules import REPO

HARNESS = "tools/workers_real_aws/harness.py"
SUMMARIZE = "tools/workers_real_aws/summarize.py"
ORIGINAL = "deploy_aws/tests/test_workers.py"
SUPPLEMENT_PREFIX = "test_realaws_"
REGION = "eu-west-1"   # 与原测试文件的缺省 region 不同


def _env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GKP_")}
    env.update(extra)
    return env


def _pytest(*args: str, env: dict[str, str], timeout: float, cwd=REPO) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=timeout)


def _names(nodeids) -> set[str]:
    return {n.split("::", 1)[1] for n in nodeids}


def _rows(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _outcomes(rows: list[dict]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        if r["kind"] == "test":
            out.setdefault(r["nodeid"].split("::", 1)[1], {})[r["phase"]] = r["outcome"]
    return out


@pytest.mark.timeout(300)
def test_harness_in_moto_mode_collects_the_same_cases_and_all_pass(tmp_path):
    collected = _pytest("--collect-only", ORIGINAL, env=_env(), timeout=120)
    assert collected.returncode == 0, collected.stdout + collected.stderr
    original = _names(line for line in collected.stdout.splitlines() if "::" in line)
    assert original, collected.stdout

    results = tmp_path / "results.jsonl"
    proc = _pytest(HARNESS, env=_env(GKP_RESULTS=str(results), GKP_REGION=REGION), timeout=240)
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-4000:]
    rows = _rows(results)
    outcomes = _outcomes(rows)

    supplements = {n for n in outcomes if n.startswith(SUPPLEMENT_PREFIX)}
    assert supplements, "装置的补充用例没有被收集"
    assert not {n for n in original if n.startswith(SUPPLEMENT_PREFIX)}, "原测试文件里出现了与补充用例同前缀的名字"
    assert set(outcomes) - supplements == original
    failed = sorted(n for n, phases in outcomes.items() if "failed" in phases.values())
    assert not failed, failed
    assert {n for n in original if outcomes[n].get("call") != "passed"} == set()
    assert {n: outcomes[n].get("setup") for n in supplements} == {n: "skipped" for n in supplements}
    harness_row = next(r for r in rows if r["kind"] == "harness")
    assert (harness_row["mode"], harness_row["force_real_paths"], harness_row["region"]) == ("moto", False, REGION)
    assert harness_row["original_loader"] == "AssertionRewritingHook"


# 真实账户模式代码路径的代表：推送、清理、经 boto3 默认 session 自建句柄读写表的那条，加三条补充用例；`party` 选中
# `_Party` 自身的自测（不用 aws 夹具）
_FORCE_SUBSET = ("test_realaws or test_push_worker_happy_path or test_cleanup_deletes_after_quiet_period_when_unreferenced"
                 " or test_snapshot_sees_what_the_real_run_store_writes_until_the_run_finishes or party")


@pytest.mark.timeout(300)
def test_harness_real_account_code_paths_run_on_moto(tmp_path):
    results = tmp_path / "results.jsonl"
    proc = _pytest(HARNESS, "-k", _FORCE_SUBSET, timeout=240,
                   env=_env(GKP_RESULTS=str(results), GKP_REGION=REGION, GKP_FORCE_REAL_PATHS="1"))
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-4000:]
    rows = _rows(results)
    outcomes = _outcomes(rows)
    calls = {n: phases.get("call") for n, phases in outcomes.items()}
    supplements = {n for n in calls if n.startswith(SUPPLEMENT_PREFIX)}
    assert len(supplements) == 3, calls
    # 补充用例 a 在 moto 上构造不出「索引仍在建立」，按设计以 xfail 结束；其余都通过
    assert {n: o for n, o in calls.items() if o != "passed"} == {
        "test_realaws_cleanup_skips_while_the_status_group_index_is_creating": "skipped"}, calls
    assert not [r for r in rows if r["kind"] in ("teardown_failure", "residue", "lingering_party_threads")]
    # 用 aws 夹具的用例各有一行 prefix 与一行 teardown；不用它的（`_Party` 自身的自测）一行都没有，也不建表、不适配
    with_aws = {r["nodeid"] for r in rows if r["kind"] == "prefix"}
    teardowns = [r for r in rows if r["kind"] == "teardown"]
    assert sorted(r["nodeid"] for r in teardowns) == sorted(with_aws) and all(r["failures"] == 0 for r in teardowns)
    without_aws = {n for n in calls if not any(nodeid.endswith("::" + n) for nodeid in with_aws)}
    assert without_aws and all("party" in n for n in without_aws), without_aws
    assert {r["nodeid"] for r in rows if r["kind"] in ("adaptation", "lazy_table_built")} <= with_aws
    assert any(r["kind"] == "adaptation" and r["changes"] == ["executionRoleArn"] for r in rows)
    assert any(r["kind"] == "lazy_table_built" and r["nodeid"].endswith("until_the_run_finishes") for r in rows)
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["exitstatus"] == 0 and rows[-1]["problems"] == {}


# ── 失败不被装置吞掉 ─────────────────────────────────────────────────────────────

# 追加在测试文件副本末尾的注入用例；它们在原模块的命名空间里执行，与原用例同样经原模块的全局读前缀
_INJECTED = '''

import os


def test_injected_assertion_failure(aws):
    seed_backend(aws)
    assert "a" == "b", "INJECTED-ASSERTION"


def _injected_deep(n):
    if n == 0:
        raise RuntimeError("INJECTED-DEEP-CAUSE")
    _injected_deep(n - 1)


def test_injected_long_traceback(aws):
    _injected_deep(60)   # 失败信息远超几十行，异常的原因在最后


def test_injected_exception(aws):
    seed_backend(aws)
    raise RuntimeError("INJECTED-EXCEPTION")


def test_injected_teardown_failure(aws):
    seed_backend(aws)
    aws.ddb.describe_table(TableName=names.default_name(PREFIX, names.BASE_RUNS_TABLE))  # 让惰性建表真正建出这张表

    def refuse(**_):
        raise RuntimeError("INJECTED-TEARDOWN")
    aws.ddb.raw.delete_table = refuse   # 收尾删表用的正是这个 client；用例本身通过


def test_injected_lingering_party(aws):
    seed_backend(aws)
    gate = threading.Event()   # 不设置：这一方一直不结束，中止对它不起作用
    stuck = _Party("INJECTED-STUCK", lambda: gate.wait(60.0), timeout=0.2)
    with pytest.raises(AssertionError, match="中止之后仍未结束的参与方"):
        with _parties(stuck):
            stuck.start_until_held()


def test_injected_after_lingering(aws):
    seed_backend(aws)


def test_injected_party_resumes_during_cleanup(aws):
    """一方在用例结束时仍存活，若清理照常执行，它在清理期间恢复执行、注册一个 revision 并结束：清理之后再查询残留时它已
    不在，资源却留在账户里。清理列举 SSM 参数（ECS 那一步之后）时放行它，并在 INJECTED_MARKS 文件里记下清理确实开始了。"""
    templates = seed_backend(aws)
    resumed = threading.Event()

    def late_write():
        if resumed.wait(5.0):
            _register_unmapped(aws, templates, digest="sha256:" + "f" * 64, variant="late")

    writer = _Party("INJECTED-LATE-WRITER", late_write, timeout=0.2)
    with pytest.raises(AssertionError, match="中止之后仍未结束的参与方"):
        with _parties(writer):
            writer.start_until_held()
    listing = aws.ssm.get_parameters_by_path

    def listing_during_cleanup(**kw):
        with open(os.environ["INJECTED_MARKS"], "a", encoding="utf-8") as fh:
            fh.write("cleanup started\\n")
        resumed.set()
        writer._thread.join(5.0)
        return listing(**kw)
    aws.ssm.get_parameters_by_path = listing_during_cleanup   # 收尾列举 SSM 参数用的正是这个 client


def test_injected_after_resuming(aws):
    seed_backend(aws)


@pytest.mark.timeout(3, method="signal")
def test_injected_teardown_interrupted(aws):
    seed_backend(aws)
    aws.ddb.describe_table(TableName=names.default_name(PREFIX, names.BASE_RUNS_TABLE))  # 让惰性建表真正建出这张表

    def slow(**_):
        time.sleep(30)
    aws.ddb.raw.delete_table = slow   # 收尾删表时被 signal 方式的超时打断


@pytest.mark.timeout(3, method="thread")
def test_injected_teardown_killed(aws):
    seed_backend(aws)
    aws.ddb.describe_table(TableName=names.default_name(PREFIX, names.BASE_RUNS_TABLE))  # 让惰性建表真正建出这张表

    def slow(**_):
        time.sleep(30)
    aws.ddb.raw.delete_table = slow   # 收尾删表时 thread 方式的超时直接终止进程，装置来不及记下任何一行


def _injected_client_error(operation, code):
    from botocore.exceptions import ClientError
    return ClientError({"Error": {"Code": code, "Message": "INJECTED-CLIENT-ERROR"}}, operation)


def _injected_error(form, operation, code):
    """form：client 即 ClientError 本身；same-text 是文字相同的 RuntimeError；as-cause 是以它为起因的 AssertionError。"""
    error = _injected_client_error(operation, code)
    if form == "same-text":
        return RuntimeError(str(error))
    if form == "as-cause":
        wrapped = AssertionError("INJECTED-WRAPPED")
        wrapped.__cause__ = error
        return wrapped
    return error


@pytest.fixture
def _injected_stage(request):
    """在 setup 或 teardown 阶段抛出与预期失败相同操作、相同错误码的 ClientError；取 call 时什么也不做。"""
    if request.param == "setup":
        raise _injected_client_error("PutImage", "InvalidParameterException")
    yield request.param
    if request.param == "teardown":
        raise _injected_client_error("PutImage", "InvalidParameterException")


# 与原用例同名、定义在后：替换它，按参数在 call 阶段（或 setup、teardown 阶段）抛出给定形态、操作与错误码的异常
@pytest.mark.parametrize("_injected_stage, form, operation, code", [
    ("call", "client", "PutImage", "InvalidParameterException"),
    ("call", "client", "CreateRepository", "AccessDeniedException"),
    ("call", "client", "PutImage", "AccessDeniedException"),
    ("setup", "client", "PutImage", "InvalidParameterException"),
    ("teardown", "client", "PutImage", "InvalidParameterException"),
    ("call", "same-text", "PutImage", "InvalidParameterException"),
    ("call", "as-cause", "PutImage", "InvalidParameterException"),
], indirect=["_injected_stage"],
   ids=["matching", "other-operation", "other-code", "in-setup", "in-teardown", "same-text", "as-cause"])
def test_repush_retires_the_replaced_revision_and_prints_digest_change(aws, _injected_stage, form, operation, code):
    seed_backend(aws)
    if _injected_stage == "call":
        raise _injected_error(form, operation, code)


def test_injected_same_error_in_another_case(aws):
    seed_backend(aws)
    raise _injected_client_error("PutImage", "InvalidParameterException")


@pytest.fixture
def _injected_residue(request):
    """在装置的 aws 夹具之前起一层外层模拟环境并预置同前缀的资源：moto 的模拟环境嵌套时内层不重置，aws 夹具开始时的
    残留检查因此能看到它们。前缀按装置的规则拼出（令牌取 GKP_TOKEN，序号即这条用例在本次会话里用到 aws 夹具的次序）。"""
    kind, seq = request.param
    prefix = f"gkp{os.environ['GKP_TOKEN']}{seq:03d}-"
    region = os.environ["AWS_REGION"]
    with mock_aws():
        if kind == "repo":
            boto3.client("ecr", region_name=region).create_repository(
                repositoryName=names.ecr_repo_name(prefix, "novaact"))
        else:
            ecs = boto3.client("ecs", region_name=region)
            arn = ecs.register_task_definition(
                family=names.task_def_name(prefix, "novaact"),
                containerDefinitions=[{"name": "c", "image": "busybox", "memory": 512}],
            )["taskDefinition"]["taskDefinitionArn"]
            ecs.deregister_task_definition(taskDefinition=arn)
        yield prefix


@pytest.mark.parametrize("_injected_residue", [("repo", 1), ("inactive", 2)], indirect=True, ids=["repo", "inactive"])
def test_injected_residue(_injected_residue, aws):
    assert PREFIX == _injected_residue
    seed_backend(aws)

@pytest.fixture
def _injected_tables_after_teardown():
    """外层模拟环境（同 `_injected_residue`）：装置的 aws 夹具收尾之后，把模拟账户里还在的表名写进 INJECTED_MARKS。"""
    import json

    region = os.environ["AWS_REGION"]
    with mock_aws():
        yield
        left = boto3.session.Session(region_name=region).client("dynamodb").list_tables()["TableNames"]
        with open(os.environ["INJECTED_MARKS"], "w", encoding="utf-8") as fh:
            fh.write(json.dumps(left))


@pytest.mark.parametrize("path", ["lazy", "direct"])
def test_injected_create_table_response_lost(_injected_tables_after_teardown, aws, path):
    """建表请求已被服务端接受（表已在建），客户端随后收到连接错误：lazy 经惰性建表发出请求，direct 像补充用例 a 那样先
    关掉惰性建表、直接用底下的 client 建表（不经装置登记）。收尾都要删掉这张表。"""
    from botocore.exceptions import ConnectionClosedError

    seed_backend(aws)
    table = names.default_name(PREFIX, names.BASE_RUNS_TABLE)
    create = aws.ddb.raw.create_table

    def accepted_then_lost(**kw):
        create(**kw)
        raise ConnectionClosedError(endpoint_url="https://dynamodb.injected")
    aws.ddb.raw.create_table = accepted_then_lost
    with pytest.raises(ConnectionClosedError):
        if path == "lazy":
            aws.ddb.describe_table(TableName=table)   # 惰性建表在这里真正发出建表请求
        else:
            aws.ddb.disable_lazy()
            aws.ddb.raw.create_table(
                TableName=table, BillingMode="PAY_PER_REQUEST",
                KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"}])
    assert table in aws.ddb.raw.list_tables()["TableNames"]


def test_injected_table_outside_the_prefix(_injected_tables_after_teardown, aws):
    """经惰性建表建了一张名字不以本用例前缀开头的表：收尾不删它，记一条收尾失败。"""
    aws.ddb.create_table(TableName="gkpforeign-table", BillingMode="PAY_PER_REQUEST",
                         KeySchema=[{"AttributeName": "run_id", "KeyType": "HASH"}],
                         AttributeDefinitions=[{"AttributeName": "run_id", "AttributeType": "S"}])
    aws.ddb.describe_table(TableName="gkpforeign-table")   # 惰性建表在这里真正发出建表请求

'''


PRODUCTION_PACKAGE = "deploy_aws/gherkai_deploy_aws"
# 被测代码复制模板时漏掉 executionRoleArn 的变异：只在副本里做（见 `_injected_mirror`）
_COPY_PAYLOAD = "payload = {k: v for k, v in td.items() if k not in _READ_ONLY_TASK_DEF_KEYS}"
_COPY_PAYLOAD_DROPPING_ROLE = ("payload = {k: v for k, v in td.items() if k not in _READ_ONLY_TASK_DEF_KEYS"
                               " and k != \"executionRoleArn\"}")


def _injected_mirror(tmp_path, *, drop_role_in_copy: bool = False):
    """注入手段：把装置（harness.py、conftest.py）与测试文件按仓库里的相对路径复制进 tmp_path，在测试文件副本末尾追加
    `_INJECTED`，返回副本的根目录。对副本执行装置，仓库里的装置与测试文件都不改动；装置本身没有任何故障注入开关，
    注入只存在于这份临时副本里，对真实账户执行仓库里的装置时不可能被触发。副本外没有 pyproject.toml，命令行另给超时。
    `drop_role_in_copy` 另把被测代码的包复制进副本，变异它从模板复制 revision 的那一行（漏掉 executionRoleArn），
    执行时经 PYTHONPATH 让副本里的包先于仓库里的包被导入（见 `_run_injected`）。"""
    root = tmp_path / "mirror"
    for rel in ("tools/workers_real_aws/harness.py", "tools/workers_real_aws/conftest.py", ORIGINAL):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, root / rel)
    with (root / ORIGINAL).open("a", encoding="utf-8") as fh:
        fh.write(_INJECTED)
    if drop_role_in_copy:
        shutil.copytree(REPO / PRODUCTION_PACKAGE, root / PRODUCTION_PACKAGE,
                        ignore=shutil.ignore_patterns("__pycache__"))
        workers_py = root / PRODUCTION_PACKAGE / "workers.py"
        source = workers_py.read_text(encoding="utf-8")
        assert source.count(_COPY_PAYLOAD) == 1, "被测代码复制模板的那一行变了，变异需要同步"
        workers_py.write_text(source.replace(_COPY_PAYLOAD, _COPY_PAYLOAD_DROPPING_ROLE), encoding="utf-8")
    return root


def _run_injected(tmp_path, select: str, *args: str, drop_role_in_copy: bool = False, **extra_env: str):
    root = _injected_mirror(tmp_path, drop_role_in_copy=drop_role_in_copy)
    results = tmp_path / "results.jsonl"
    env = _env(GKP_RESULTS=str(results), GKP_REGION=REGION, GKP_FORCE_REAL_PATHS="1", **extra_env)
    if drop_role_in_copy:
        env["PYTHONPATH"] = os.pathsep.join(p for p in (str(root / "deploy_aws"), env.get("PYTHONPATH")) if p)
    proc = _pytest(HARNESS, "--timeout=60", "-k", select, *args, cwd=root, timeout=120, env=env)
    return proc, _rows(results), proc.stdout + proc.stderr


def _summarize(tmp_path) -> list[str]:
    """仓库里的 summarize.py 对 `_run_injected` 写出的结果文件的输出，按行。"""
    proc = subprocess.run([sys.executable, str(REPO / SUMMARIZE), str(tmp_path / "results.jsonl")], cwd=REPO,
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout.splitlines()


@pytest.mark.timeout(180)
def test_a_failing_assertion_and_an_exception_end_the_session_with_a_nonzero_code(tmp_path):
    proc, rows, out = _run_injected(
        tmp_path, "injected_assertion_failure or injected_exception or injected_long_traceback")
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]
    calls = {r["nodeid"].split("::", 1)[1]: r for r in rows if r["kind"] == "test" and r["phase"] == "call"}
    assert set(calls) == {"test_injected_assertion_failure", "test_injected_exception",
                          "test_injected_long_traceback"}, calls
    assert calls["test_injected_assertion_failure"]["outcome"] == "failed"
    assert "INJECTED-ASSERTION" in calls["test_injected_assertion_failure"]["longrepr"]
    assert calls["test_injected_exception"]["outcome"] == "failed"
    assert "INJECTED-EXCEPTION" in calls["test_injected_exception"]["longrepr"]
    assert "FAILED" in out and "test_injected_assertion_failure" in out and "test_injected_exception" in out
    # 长 traceback 完整保存：异常的原因在末尾，结果文件里留着它
    deep = calls["test_injected_long_traceback"]["longrepr"].splitlines()
    assert len(deep) > 100 and "INJECTED-DEEP-CAUSE" in "\n".join(deep[-5:]), deep[-10:]
    # 用例失败时收尾照常执行
    assert len([r for r in rows if r["kind"] == "teardown" and r["failures"] == 0]) == 3
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["exitstatus"] == pytest.ExitCode.TESTS_FAILED
    summary = _summarize(tmp_path)
    assert summary[1:3] == ["需要处理：无", "会话退出码 [1]"], summary
    assert "FAILED test_injected_assertion_failure [call]" in summary and "FAILED test_injected_exception [call]" in summary
    # summarize.py 打印末尾几行（原因在其中），并注明略去了前面多少行
    at = summary.index("FAILED test_injected_long_traceback [call]")
    assert summary[at + 1].startswith("    （略去前 ") and any("INJECTED-DEEP-CAUSE" in s for s in summary[at + 2:at + 14])


@pytest.mark.timeout(180)
def test_a_teardown_failure_ends_the_session_with_a_nonzero_code_although_the_case_passed(tmp_path):
    proc, rows, out = _run_injected(tmp_path, "injected_teardown_failure")
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]
    assert [(r["phase"], r["outcome"]) for r in rows if r["kind"] == "test"] == [
        ("setup", "passed"), ("call", "passed"), ("teardown", "passed")]
    failures = [r for r in rows if r["kind"] == "teardown_failure"]
    assert len(failures) == 1 and failures[0]["step"] == "delete_table" and "INJECTED-TEARDOWN" in failures[0]["error"]
    assert "装置记下的问题" in out and "收尾失败" in out and "INJECTED-TEARDOWN" in out, out[-4000:]
    assert "1 装置问题" in out.splitlines()[-1], out[-1000:]
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["problems"] == {"收尾失败": 1}
    # summarize.py 把它放在第一行计数之后、失败用例之前
    summary = _summarize(tmp_path)
    assert summary[1] == "需要处理：收尾失败 1 条" and "INJECTED-TEARDOWN" in summary[2], summary
    assert summary[3] == "会话退出码 [1]", summary


@pytest.mark.timeout(180)
def test_a_lingering_party_thread_stops_the_session_before_the_next_case(tmp_path):
    proc, rows, out = _run_injected(tmp_path, "injected_lingering_party or injected_after_lingering")
    assert proc.returncode == pytest.ExitCode.INTERRUPTED, out[-4000:]
    tests = {r["nodeid"].split("::", 1)[1] for r in rows if r["kind"] in ("test", "prefix")}
    assert tests == {"test_injected_lingering_party"}, tests   # 后一条用例没有开始
    lingering = [r for r in rows if r["kind"] == "lingering_party_threads"]
    assert len(lingering) == 1 and lingering[0]["threads"] == ["INJECTED-STUCK"], lingering
    assert lingering[0]["cleanup_skipped"] is True
    # 终止之前，这条用例照常通过；对账户的清理被跳过（残留的线程仍可能写入）
    assert [r["outcome"] for r in rows if r["kind"] == "test"] == ["passed"] * 3
    assert [(r["skipped"], r["failures"]) for r in rows if r["kind"] == "teardown"] == [("lingering_party_threads", None)]
    assert "参与方线程残留" in out and "INJECTED-STUCK" in out and "后续用例不再执行" in out, out[-4000:]
    assert "清理已跳过" in out, out[-4000:]
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["exitstatus"] == pytest.ExitCode.INTERRUPTED
    summary = _summarize(tmp_path)
    assert summary[1] == "需要处理：参与方线程残留 1 条" and "INJECTED-STUCK" in summary[2], summary
    assert summary[3] == "会话退出码 [2]", summary
    assert summary[-1] == "teardowns 1 with failures 0 skipped 1", summary


@pytest.mark.timeout(180)
def test_a_party_that_would_resume_during_cleanup_is_caught_before_the_cleanup(tmp_path):
    """残留的一方若在清理期间恢复执行、写入并结束，清理之后再查询会漏检；装置在清理之前查询并锁存，跳过清理。"""
    marks = tmp_path / "marks.txt"
    proc, rows, out = _run_injected(tmp_path, "injected_party_resumes_during_cleanup or injected_after_resuming",
                                    INJECTED_MARKS=str(marks))
    assert proc.returncode == pytest.ExitCode.INTERRUPTED, out[-4000:]
    assert {r["nodeid"].split("::", 1)[1] for r in rows if r["kind"] in ("test", "prefix")} == {
        "test_injected_party_resumes_during_cleanup"}
    lingering = [r for r in rows if r["kind"] == "lingering_party_threads"]
    assert [(r["threads"], r["cleanup_skipped"]) for r in lingering] == [(["INJECTED-LATE-WRITER"], True)], lingering
    assert not marks.exists(), "清理不应开始：那一方仍存活时清理与它竞争没有意义"
    assert [r["skipped"] for r in rows if r["kind"] == "teardown"] == ["lingering_party_threads"]
    assert not [r for r in rows if r["kind"] == "teardown_failure"]
    assert "INJECTED-LATE-WRITER" in out and "清理已跳过" in out and "后续用例不再执行" in out, out[-4000:]
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["exitstatus"] == pytest.ExitCode.INTERRUPTED
    summary = _summarize(tmp_path)
    assert summary[1] == "需要处理：参与方线程残留 1 条" and "INJECTED-LATE-WRITER" in summary[2], summary


@pytest.mark.timeout(180)
def test_a_teardown_interrupted_by_a_signal_timeout_is_recorded_as_a_problem(tmp_path):
    proc, rows, out = _run_injected(tmp_path, "injected_teardown_interrupted")
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]
    assert [(r["phase"], r["outcome"]) for r in rows if r["kind"] == "test"] == [
        ("setup", "passed"), ("call", "passed"), ("teardown", "failed")]
    interrupted = [r for r in rows if r["kind"] == "teardown_interrupted"]
    assert len(interrupted) == 1 and interrupted[0]["step"].startswith("ddb ") and "Timeout" in interrupted[0]["error"], (
        interrupted)
    assert not [r for r in rows if r["kind"] == "teardown"], "被打断的收尾不应记成一次完成的收尾"
    assert "装置记下的问题" in out and "清理被中断" in out, out[-4000:]
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["problems"] == {"清理被中断": 1}
    summary = _summarize(tmp_path)
    assert summary[1] == "需要处理：清理被中断 1 条" and "Timeout" in summary[2], summary


@pytest.mark.timeout(180)
def test_a_teardown_cut_short_by_a_thread_timeout_is_flagged_by_summarize(tmp_path):
    """thread 方式的超时直接终止进程：装置记不下问题，summarize.py 从结果文件推出收尾没有完成、会话没有正常结束。"""
    proc, rows, out = _run_injected(tmp_path, "injected_teardown_killed")
    assert proc.returncode == 1 and "Timeout" in out, out[-4000:]
    assert not [r for r in rows if r["kind"] in ("teardown", "teardown_interrupted", "session_finish")], rows
    summary = _summarize(tmp_path)
    assert summary[1] == "需要处理：收尾没有完成 1 条、会话没有正常结束 1 次", summary
    assert summary[2].startswith("  收尾没有完成 test_injected_teardown_killed "), summary
    assert summary[3].startswith("  会话没有正常结束："), summary
    assert summary[4] == "会话退出码 没有 session_finish 一行（会话没有正常结束）", summary


_EXPECTED_FAILURE_CASES = "test_repush_retires_the_replaced_revision_and_prints_digest_change or injected_same_error"


def _phases_by_case(rows: list[dict]) -> dict[str, dict[str, tuple[str, bool]]]:
    phases: dict[str, dict[str, tuple[str, bool]]] = {}
    for r in rows:
        if r["kind"] == "test":
            name = r["nodeid"].split("::", 1)[1]
            case = name.rsplit("[", 1)[1].rstrip("]") if "[" in name else name
            phases.setdefault(case, {})[r["phase"]] = (r["outcome"], bool(r.get("xfail_reason")))
    return phases


@pytest.mark.timeout(180)
def test_only_a_putimage_invalid_parameter_error_in_the_call_phase_is_an_expected_failure(tmp_path):
    proc, rows, out = _run_injected(tmp_path, _EXPECTED_FAILURE_CASES)
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]
    ok, call_failed = ("passed", False), {"setup": ("passed", False), "call": ("failed", False),
                                          "teardown": ("passed", False)}
    assert _phases_by_case(rows) == {
        "matching": {"setup": ok, "call": ("skipped", True), "teardown": ok},
        "other-operation": call_failed,
        "other-code": call_failed,
        "in-setup": {"setup": ("failed", False), "teardown": ok},
        "in-teardown": {"setup": ok, "call": ok, "teardown": ("failed", False)},
        "same-text": call_failed,
        "as-cause": call_failed,
        "test_injected_same_error_in_another_case": call_failed,
    }, _phases_by_case(rows)
    last = out.splitlines()[-1]
    assert all(part in last for part in ("5 failed", "1 passed", "1 xfailed", "2 errors")), last
    matching = next(r for r in rows if r["kind"] == "test" and r["nodeid"].endswith("[matching]") and r["phase"] == "call")
    assert "InvalidParameterException" in matching["xfail_detail"]


@pytest.mark.timeout(180)
def test_runxfail_reports_the_expected_failure_as_a_failure(tmp_path):
    """给了 --runxfail 时装置不改判：那一种特定失败与 xfail 标记的用例一样照常报告失败。"""
    proc, rows, out = _run_injected(
        tmp_path, "test_repush_retires_the_replaced_revision_and_prints_digest_change and matching", "--runxfail")
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]
    assert _phases_by_case(rows) == {
        "matching": {"setup": ("passed", False), "call": ("failed", False), "teardown": ("passed", False)}}, rows
    call = next(r for r in rows if r["kind"] == "test" and r["phase"] == "call")
    assert "InvalidParameterException" in call["longrepr"] and "xfail_detail" not in call
    last = out.splitlines()[-1]
    assert "1 failed" in last and "xfailed" not in last, last


@pytest.mark.timeout(180)
def test_a_production_copy_that_drops_the_template_role_fails_instead_of_being_repaired(tmp_path):
    proc, rows, out = _run_injected(tmp_path, "test_push_worker_happy_path", drop_role_in_copy=True)
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]
    outcomes = [(r["phase"], r["outcome"]) for r in rows if r["kind"] == "test"]
    assert ("teardown", "failed") in outcomes, outcomes
    mismatches = [r for r in rows if r["kind"] == "copy_request_mismatch"]
    assert mismatches and all(set(m["fields"]) == {"executionRoleArn"} and m["fields"]["executionRoleArn"]["request"]
                              is None for m in mismatches), mismatches
    # 适配只出现在种子模板上（两个引擎各一个），复制请求没有被适配；漏带角色的复制请求复制的正是其中的模板
    adaptations = [r for r in rows if r["kind"] == "adaptation"]
    assert len(adaptations) == 2 and all(r["changes"] == ["executionRoleArn"] for r in adaptations), adaptations
    assert {m["template"] for m in mismatches} <= {r["arn"] for r in adaptations}, (adaptations, mismatches)
    assert "不替复制请求补字段" in out and "复制请求与模板不符" in out, out[-4000:]
    summary = _summarize(tmp_path)
    assert summary[1].startswith("需要处理：复制请求与模板不符 "), summary


@pytest.mark.timeout(180)
def test_residue_with_only_a_repository_or_only_inactive_revisions_is_found(tmp_path):
    token = "injx"
    proc, rows, out = _run_injected(tmp_path, "test_injected_residue", GKP_TOKEN=token)
    assert proc.returncode == pytest.ExitCode.TESTS_FAILED, out[-4000:]   # 残留是装置问题：用例通过、退出码仍为 1
    assert [(r["phase"], r["outcome"]) for r in rows if r["kind"] == "test"] == [
        ("setup", "passed"), ("call", "passed"), ("teardown", "passed")] * 2
    residue = {r["nodeid"].rsplit("[", 1)[1].rstrip("]"): r for r in rows if r["kind"] == "residue"}
    assert set(residue) == {"repo", "inactive"}, residue
    from gherkai_deploy_aws import names

    repo, inactive = residue["repo"], residue["inactive"]
    assert repo["repos"] == [names.ecr_repo_name(f"gkp{token}001-", "novaact")], repo
    assert not any(repo["revisions"].values()) and not any(repo["inactive_revisions"].values()) and not repo["params"]
    assert len(inactive["inactive_revisions"]["novaact"]) == 1 and not any(inactive["revisions"].values())
    assert not inactive["repos"] and not inactive["params"] and inactive["table"] is False
    assert not [r for r in rows if r["kind"] == "teardown_failure"]
    assert rows[-1]["problems"] == {"同前缀残留": 2}
    summary = _summarize(tmp_path)
    assert summary[1] == "需要处理：同前缀残留 2 条", summary


@pytest.mark.timeout(180)
@pytest.mark.parametrize("path", ["lazy", "direct"])
def test_a_table_whose_create_response_was_lost_is_still_deleted_by_the_teardown(tmp_path, path):
    """建表请求已被服务端接受、客户端随后收到连接错误：装置没有收到建表的应答，收尾仍按前缀删掉这张表，不得是零失败、
    没有记录而表仍在。"""
    marks = tmp_path / "marks.json"
    proc, rows, out = _run_injected(tmp_path, f"test_injected_create_table_response_lost and {path}",
                                    INJECTED_MARKS=str(marks))
    assert proc.returncode == 0, out[-4000:]
    from gherkai_deploy_aws import names

    teardown = next(r for r in rows if r["kind"] == "teardown")
    table = names.default_name(teardown["prefix"], names.BASE_RUNS_TABLE)
    assert teardown["failures"] == 0 and teardown["table_built"] == [], teardown
    assert teardown["table_create_unconfirmed"] == ([table] if path == "lazy" else []), teardown
    assert json.loads(marks.read_text(encoding="utf-8")) == [], "收尾之后表仍在"
    assert rows[-1]["kind"] == "session_finish" and rows[-1]["problems"] == {}
    assert _summarize(tmp_path)[1] == "需要处理：无"


@pytest.mark.timeout(180)
def test_the_teardown_leaves_a_table_outside_the_prefix_alone_and_reports_it(tmp_path):
    """收尾只删以本用例前缀开头的表：用例建了前缀之外的表时，收尾不删它，记一条收尾失败，会话以非零退出码结束。"""
    marks = tmp_path / "marks.json"
    proc, rows, out = _run_injected(tmp_path, "test_injected_table_outside_the_prefix", INJECTED_MARKS=str(marks))
    assert proc.returncode == 1, out[-4000:]
    assert [(r["target"], r["step"]) for r in rows if r["kind"] == "teardown_failure"] == [
        ("gkpforeign-table", "ddb gkpforeign-table")], rows
    teardown = next(r for r in rows if r["kind"] == "teardown")
    assert teardown["failures"] == 1 and teardown["table_built"] == ["gkpforeign-table"], teardown
    assert json.loads(marks.read_text(encoding="utf-8")) == ["gkpforeign-table"], "收尾不应删前缀之外的表"
    assert _summarize(tmp_path)[1] == "需要处理：收尾失败 1 条"


# ── 残留检查遇到删除中的 runs 表：替身 client ─────────────────────────────────────

# moto 上删表即刻生效、构造不出 DELETING，这几条在子进程里按路径载入装置，直接调用它的残留检查。DynamoDB 是挂了 botocore
# Stubber 的真 client（等待用的是 botocore 真实的 table_not_exists 等待器，只把它的 sleep 换成记录秒数），ECS、SSM、ECR
# 是只回答残留检查与清理所需调用的替身。子进程不连 AWS：Stubber 在发出请求之前给出应答，没有预置的调用直接报错。
_RESIDUE_PROBE = r'''
import importlib.util, json, os, sys, types

import boto3
import botocore.waiter
from botocore.exceptions import ClientError
from botocore.stub import Stubber

scenario, harness_path, out_path = sys.argv[1:4]
spec = importlib.util.spec_from_file_location("gkp_harness_probe", harness_path)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

prefix, nodeid = "gkpprobe001-", "probe::case"
table = h.names.default_name(prefix, h.names.BASE_RUNS_TABLE)
repo = h.names.ecr_repo_name(prefix, "novaact")
sleeps = []
botocore.waiter.time = types.SimpleNamespace(sleep=sleeps.append)


class Ecs:
    def list_task_definitions(self, **kw):
        return {"taskDefinitionArns": []}


class Ssm:
    def get_parameters_by_path(self, **kw):
        return {"Parameters": []}


class Ecr:
    def __init__(self, repos):
        self.repos = set(repos)

    def describe_repositories(self, repositoryNames):
        if repositoryNames[0] in self.repos:
            return {"repositories": [{"repositoryName": repositoryNames[0]}]}
        raise ClientError({"Error": {"Code": "RepositoryNotFoundException", "Message": "probe"}}, "DescribeRepositories")

    def delete_repository(self, repositoryName, force):
        self.repos.discard(repositoryName)


ddb = boto3.client("dynamodb", region_name="eu-west-1")
stub = Stubber(ddb)


def described(status):
    stub.add_response("describe_table", {"Table": {"TableName": table, "TableStatus": status}}, {"TableName": table})


def gone():
    stub.add_client_error("describe_table", service_error_code="ResourceNotFoundException", http_status_code=400,
                          expected_params={"TableName": table})


repos = []
if scenario == "deleting_then_gone":        # 残留检查读到 DELETING，等待器再读两次 DELETING、第三次表已不在
    for _ in range(3):
        described("DELETING")
    gone()
elif scenario == "deleting_with_other":     # 同时有一个 ECR 仓库残留：residue 照记、表的那一项为 false
    described("DELETING")
    gone()
    stub.add_client_error("delete_table", service_error_code="ResourceNotFoundException", http_status_code=400,
                          expected_params={"TableName": table})
    repos = [repo]
elif scenario.startswith("status:"):        # DELETING 以外的状态（ACTIVE、CREATING 等）算残留：清掉时删表、等它消失
    described(scenario.split(":", 1)[1])
    stub.add_response("delete_table", {"TableDescription": {"TableName": table, "TableStatus": "DELETING"}},
                      {"TableName": table})
    gone()
elif scenario == "describe_denied":         # DescribeTable 报不是「表不存在」的错误：不吞掉
    stub.add_client_error("describe_table", service_error_code="AccessDeniedException", http_status_code=400,
                          expected_params={"TableName": table})
elif scenario == "denied_while_waiting":    # 读到 DELETING 之后，等待中 DescribeTable 报别的错误：照实报告，不说成没有删完
    described("DELETING")
    stub.add_client_error("describe_table", service_error_code="AccessDeniedException", http_status_code=400,
                          expected_params={"TableName": table})
elif scenario == "deleting_forever":        # 残留检查一次加等待器的全部 120 次都读到 DELETING
    for _ in range(1 + h._TABLE_GONE_WAIT["MaxAttempts"]):
        described("DELETING")
else:
    raise SystemExit(f"unknown scenario {scenario}")

with stub:
    h._precheck_residue({"dynamodb": ddb, "ecs": Ecs(), "ssm": Ssm(), "ecr": Ecr(repos)}, prefix, nodeid)
    try:
        stub.assert_no_pending_responses()
        pending = 0
    except AssertionError as exc:
        pending = str(exc)
json.dump({"table": table, "repo": repo, "sleeps": sleeps, "pending": pending,
           "problems": [p["kind"] for p in h._conftest().problems()]}, open(out_path, "w"))
'''


def _probe_residue(tmp_path, scenario: str) -> tuple[dict, list[dict]]:
    script, out, results = tmp_path / "probe.py", tmp_path / "probe.json", tmp_path / "results.jsonl"
    script.write_text(_RESIDUE_PROBE, encoding="utf-8")
    env = _env(GKP_RESULTS=str(results), GKP_TOKEN="probe", AWS_ACCESS_KEY_ID="t", AWS_SECRET_ACCESS_KEY="t")
    env.pop("AWS_PROFILE", None)
    proc = subprocess.run([sys.executable, str(script), scenario, str(REPO / HARNESS), str(out)], cwd=tmp_path,
                          env=env, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-4000:]
    rows = _rows(results) if results.exists() else []
    return json.loads(out.read_text(encoding="utf-8")), rows


@pytest.mark.timeout(180)
def test_a_runs_table_still_being_deleted_is_waited_for_and_is_not_residue(tmp_path):
    """共用令牌的上一条命令收尾时发起删表、不等删完：下一条命令看到同前缀的表处于 DELETING。这是正在完成的清理，
    残留检查等它消失、记一行信息，不记 residue、不进问题清单。"""
    probe, rows = _probe_residue(tmp_path, "deleting_then_gone")
    assert probe["pending"] == 0, probe   # 等待器真的读到了表消失
    assert probe["sleeps"] == [2, 2], probe
    assert [r["kind"] for r in rows] == ["waited_for_table_deletion"], rows
    assert {k: rows[0][k] for k in ("nodeid", "prefix", "table")} == {
        "nodeid": "probe::case", "prefix": "gkpprobe001-", "table": probe["table"]}, rows
    assert isinstance(rows[0]["seconds"], (int, float)), rows
    assert probe["problems"] == [], probe


@pytest.mark.timeout(180)
def test_a_runs_table_being_deleted_alongside_other_residue_is_not_counted(tmp_path):
    probe, rows = _probe_residue(tmp_path, "deleting_with_other")
    assert probe["pending"] == 0, probe
    assert [r["kind"] for r in rows] == ["waited_for_table_deletion", "residue"], rows
    residue = rows[1]
    assert residue["table"] is False and residue["repos"] == [probe["repo"]], residue
    assert probe["problems"] == ["residue"], probe


@pytest.mark.timeout(180)
@pytest.mark.parametrize("status", ["ACTIVE", "CREATING", "UPDATING", "ARCHIVING", "ARCHIVED",
                                    "INACCESSIBLE_ENCRYPTION_CREDENTIALS", "REPLICATION_NOT_AUTHORIZED"])
def test_a_runs_table_in_any_other_status_is_still_residue(tmp_path, status):
    probe, rows = _probe_residue(tmp_path, f"status:{status}")
    assert probe["pending"] == 0, probe   # 清掉时删了表、等到它消失
    assert [r["kind"] for r in rows] == ["residue"], rows
    assert rows[0]["table"] is True and not rows[0]["repos"], rows
    assert probe["problems"] == ["residue"], probe


@pytest.mark.timeout(180)
def test_a_runs_table_that_never_finishes_deleting_fails_the_residue_check(tmp_path):
    """等满时限（每 2 秒查一次、至多 120 次）表仍为 DELETING：残留检查失败、记一条收尾失败（问题），不记 residue，也不记
    等待完成的那一行。"""
    probe, rows = _probe_residue(tmp_path, "deleting_forever")
    assert probe["pending"] == 0, probe
    assert probe["sleeps"] == [2] * 119, len(probe["sleeps"])
    assert [r["kind"] for r in rows] == ["teardown_failure"], rows
    failure = rows[0]
    assert failure["step"] == "residue check" and "TimeoutError" in failure["error"], failure
    assert probe["table"] in failure["error"] and "DELETING" in failure["error"], failure
    assert probe["problems"] == ["teardown_failure"], probe


@pytest.mark.timeout(180)
@pytest.mark.parametrize("scenario", ["describe_denied", "denied_while_waiting"])
def test_other_describe_table_errors_fail_the_residue_check(tmp_path, scenario):
    """DescribeTable 报不是「表不存在」的错误（残留检查的第一次读取，或等删除中的表消失期间）：残留检查失败、记一条
    收尾失败，错误码如实保留，不按没有残留处理，也不说成等待超时。"""
    probe, rows = _probe_residue(tmp_path, scenario)
    assert probe["pending"] == 0, probe
    assert [r["kind"] for r in rows] == ["teardown_failure"], rows
    failure = rows[0]
    assert failure["step"] == "residue check" and "AccessDeniedException" in failure["error"], failure
    assert "TimeoutError" not in failure["error"], failure
    assert probe["problems"] == ["teardown_failure"], probe


def _load_module(rel: str):
    spec = importlib.util.spec_from_file_location(f"_gkp_{Path(rel).stem}", REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_summarize_names_the_same_problem_kinds_as_the_harness():
    """summarize.py 只读结果文件、不导入装置，问题种类另写了一份：两份须相同，否则新加的一类不会出现在「需要处理」里。"""
    kinds = _load_module(SUMMARIZE).PROBLEM_KINDS
    assert kinds == _load_module("tools/workers_real_aws/conftest.py").PROBLEM_KINDS
    assert "waited_for_table_deletion" not in kinds   # 等删除中的表消失是信息记录，不是问题


# ── summarize.py 的推断：直接构造结果文件 ─────────────────────────────────────────

_CASE = "tools/workers_real_aws/harness.py::test_push_worker_happy_path"
_OTHER_CASE = "tools/workers_real_aws/harness.py::test_cleanup_deletes_after_quiet_period_when_unreferenced"


def _session(token: str, *, real: bool, finished: bool = True, torn_down: bool = True, prefix_seq: int = 1,
             case: str = _CASE) -> list[dict]:
    """一次会话写进结果文件的记录（只含 summarize.py 推断要用的几种）：真实账户模式的代码路径下，收尾完成时有 teardown 一行。"""
    prefix = f"gkp{token}{prefix_seq:03d}-"
    rows = [{"kind": "session_start", "env": {"GKP_TOKEN": token}},
            {"kind": "harness", "mode": "real" if real else "moto", "force_real_paths": False},
            {"kind": "prefix", "nodeid": case, "prefix": prefix}]
    rows += [{"kind": "test", "nodeid": case, "phase": phase, "outcome": "passed"} for phase in ("setup", "call")]
    if real and torn_down:
        rows.append({"kind": "teardown", "nodeid": case, "prefix": prefix, "failures": 0})
    if finished:
        rows.append({"kind": "test", "nodeid": case, "phase": "teardown", "outcome": "passed"})
        rows.append({"kind": "session_finish", "exitstatus": 0, "problems": {}})
    return rows


def _write_results(tmp_path, rows: list[dict], tail: bytes = b"") -> Path:
    path = tmp_path / "results.jsonl"
    path.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8") + tail)
    return path


def _summary_of(path: Path, capsys) -> list[str]:
    assert _load_module(SUMMARIZE).main([str(path)]) == 0
    return capsys.readouterr().out.splitlines()


def test_summarize_judges_each_session_by_its_own_mode(tmp_path, capsys):
    """纯 moto 会话不记 teardown 行；与一次执行了别的用例的真实账户会话写进同一个文件时，它的用例不算「收尾没有完成」。"""
    path = _write_results(tmp_path, _session("motoa", real=False, case=_OTHER_CASE) + _session("reala", real=True))
    summary = _summary_of(path, capsys)
    assert summary[1:3] == ["需要处理：无", "会话退出码 第 1 个会话 0，第 2 个会话 0"], summary


def test_summarize_does_not_let_a_later_session_hide_an_unfinished_teardown(tmp_path, capsys):
    """较早的会话没有完成收尾（进程被终止），后来的会话完成了同名用例：前者仍要列出，带上第几个会话与它的前缀。"""
    path = _write_results(tmp_path, _session("olda", real=True, finished=False, torn_down=False)
                          + _session("newa", real=True))
    summary = _summary_of(path, capsys)
    assert summary[1] == "需要处理：收尾没有完成 1 条、会话没有正常结束 1 次", summary
    assert summary[2] == "  收尾没有完成 第 1 个会话 test_push_worker_happy_path {'prefix': 'gkpolda001-'}", summary
    assert summary[3].startswith("  会话没有正常结束 第 1 个会话（令牌 olda）："), summary
    assert summary[4] == "会话退出码 第 1 个会话 没有 session_finish 一行，第 2 个会话 0", summary


def test_summarize_matches_a_teardown_to_its_case_by_prefix_within_a_session(tmp_path, capsys):
    """同一次会话里同名用例执行了两次（两个前缀），只有一次完成了收尾：另一次照样列出。"""
    first = _session("sama", real=True, finished=False, torn_down=False)
    second = [r for r in _session("sama", real=True, prefix_seq=2) if r["kind"] != "session_start"]
    summary = _summary_of(_write_results(tmp_path, first + second), capsys)
    assert summary[1] == "需要处理：收尾没有完成 1 条", summary
    assert summary[2] == "  收尾没有完成 test_push_worker_happy_path {'prefix': 'gkpsama001-'}", summary


@pytest.mark.parametrize("real, torn_down, finished, expected", [
    (False, False, True, ["需要处理：无", "会话退出码 [0]"]),
    (True, True, True, ["需要处理：无", "会话退出码 [0]"]),
    (True, False, False, ["需要处理：收尾没有完成 1 条、会话没有正常结束 1 次",
                          "  收尾没有完成 test_push_worker_happy_path {'prefix': 'gkpsoloa001-'}",
                          "  会话没有正常结束：结果文件里 session_finish 少于 session_start（例如 thread 方式的超时直接"
                          "终止了进程），收尾与结果文件都可能不完整",
                          "会话退出码 没有 session_finish 一行（会话没有正常结束）"]),
], ids=["moto", "real", "real-killed"])
def test_summarize_output_for_a_single_session_is_unchanged(tmp_path, capsys, real, torn_down, finished, expected):
    """只有一次会话时不标会话序号，输出与按整个文件判断时相同。"""
    rows = _session("soloa", real=real, torn_down=torn_down, finished=finished)
    summary = _summary_of(_write_results(tmp_path, rows), capsys)
    assert summary[1:1 + len(expected)] == expected, summary


@pytest.mark.parametrize("tail", [b'{"kind": "test", "nodeid": "tools/wor', '{"kind": "step", "note": "中'.encode("utf-8")[:-1]],
                         ids=["half-json", "half-multibyte-char"])
def test_summarize_reports_a_truncated_last_line_and_uses_the_complete_rows(tmp_path, capsys, tail):
    """进程被硬终止时最后一行可能只写了一半（可能截在多字节字符中间）：明确报告，并用之前的完整记录汇总。"""
    rows = _session("cuta", real=True, finished=False, torn_down=False)
    summary = _summary_of(_write_results(tmp_path, rows, tail), capsys)
    assert summary[0] == "{('setup', 'passed'): 1, ('call', 'passed'): 1}", summary
    assert summary[1] == "需要处理：收尾没有完成 1 条、会话没有正常结束 1 次、结果文件最后一行没有完整写入", summary
    assert summary[4] == (f"  结果文件最后一行没有完整写入：第 {len(rows) + 1} 行末尾的一个对象只写了一部分（进程在写它时"
                          "被终止），会话没有正常结束；以下按它之前的完整记录汇总"), summary


@pytest.mark.parametrize("finished", [True, False], ids=["next-session-finished", "next-session-killed-too"])
def test_summarize_reads_a_session_start_appended_to_a_half_written_line(tmp_path, capsys, finished):
    """被终止的会话最后一行只写了一半、没有换行，同一路径下一次会话的 session_start 接在同一行：略去没有写完的部分，
    session_start 照常读入，两次会话各自判断；下一次会话也只写了 session_start 就被终止时，这一行同时是文件的最后一行。"""
    old = _session("olda", real=True, finished=False, torn_down=False)
    new = _session("newa", real=True) if finished else _session("newa", real=True)[:1]
    lines = [json.dumps(r, ensure_ascii=False) for r in old + new]
    lines[len(old)] = '{"kind": "test", "nodeid": "tools/wor' + lines[len(old)]
    path = tmp_path / "results.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = _summary_of(path, capsys)
    not_ended = "1 次" if finished else "2 次"
    assert summary[1] == f"需要处理：收尾没有完成 1 条、会话没有正常结束 {not_ended}、结果文件中途有 1 行没有完整写入", summary
    assert summary[2] == "  收尾没有完成 第 1 个会话 test_push_worker_happy_path {'prefix': 'gkpolda001-'}", summary
    assert f"  结果文件中途有一行没有完整写入：第 {len(old) + 1} 行里有上一次会话没有写完的一个对象（进程在写它时被终止），"\
           "其后紧接着下一次会话的 session_start；没有写完的部分略去，其余照常汇总" in summary, summary
    second = "0" if finished else "没有 session_finish 一行"
    assert f"会话退出码 第 1 个会话 没有 session_finish 一行，第 2 个会话 {second}" in summary, summary


@pytest.mark.parametrize("broken", ['{"kind": "pre', '{"kind": "pre{"kind": "session_start", "env": {'],
                         ids=["half-line", "half-start"])
def test_summarize_refuses_a_broken_line_in_the_middle_and_names_it(tmp_path, capsys, broken):
    """中间的坏行不是被终止的会话留下的形态（接在后面的 session_start 也不完整时同样不是）：报错并指出行号。"""
    rows = _session("bada", real=True)
    path = tmp_path / "results.jsonl"
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    lines.insert(2, broken)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert _load_module(SUMMARIZE).main([str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "结果文件第 3 行不是完整的 JSON 对象" in captured.err, captured


@pytest.mark.parametrize("filler", [" \t\r", "\x0b", "\x0c", " \x0c ", "\u00a0"],
                         ids=["json-whitespace", "vertical-tab", "form-feed", "form-feed-in-spaces", "no-break-space"])
def test_summarize_skips_only_lines_of_json_whitespace(tmp_path, capsys, filler):
    """只含 JSON 允许的空白（空格、制表符、回车、换行）的行是空行、略去；只含其它空白字符（垂直制表符、换页符、不间断空格）的行是坏行，
    报错并指出行号。"""
    rows = _session("blka", real=True)
    path = tmp_path / "results.jsonl"
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    lines.insert(2, filler)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    code = _load_module(SUMMARIZE).main([str(path)])
    captured = capsys.readouterr()
    if filler.strip(" \t\r\n"):
        assert code == 1 and captured.out == "" and "结果文件第 3 行不是完整的 JSON 对象" in captured.err, captured
    else:
        assert code == 0 and captured.out.splitlines()[1] == "需要处理：无", captured


def test_summarize_keeps_complete_objects_that_lost_their_newline(tmp_path, capsys):
    """上一次会话最后的 session_finish 是完整的、只是缺了换行，下一次会话的 session_start 接在同一行：两个对象都读入，
    上一次会话照常算作正常结束，不报没有写完的行。"""
    old, new = _session("olda", real=True), _session("newa", real=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in old + new]
    lines[len(old) - 1:len(old) + 1] = [lines[len(old) - 1] + lines[len(old)]]
    path = tmp_path / "results.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = _summary_of(path, capsys)
    assert summary[1:3] == ["需要处理：无", "会话退出码 第 1 个会话 0，第 2 个会话 0"], summary


def test_summarize_keeps_complete_objects_before_a_half_written_one(tmp_path, capsys):
    """一行里没有写完的对象前面连着缺换行的完整对象（这里是上一次会话的 teardown 与 session_finish）：完整的照常读入，
    只略去没有写完的部分。"""
    old, new = _session("olda", real=True), _session("newa", real=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in old + new]
    lines[len(old) - 3:len(old) + 1] = [lines[len(old) - 3] + lines[len(old) - 2] + lines[len(old) - 1]
                                        + '{"kind": "test", "nodeid": "tools/wor' + lines[len(old)]]
    path = tmp_path / "results.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = _summary_of(path, capsys)
    assert summary[1] == "需要处理：结果文件中途有 1 行没有完整写入", summary
    assert "会话退出码 第 1 个会话 0，第 2 个会话 0" in summary, summary


def test_summarize_refuses_a_half_line_that_could_never_become_json(tmp_path, capsys):
    """接在 session_start 前面的部分不可能靠继续写入变成合法的 JSON（这里是未加引号的 INVALID）：不是被终止的会话留下的
    形态，报错并指出行号。"""
    rows = _session("olda", real=True, finished=False, torn_down=False) + _session("newa", real=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in rows]
    at = len(_session("olda", real=True, finished=False, torn_down=False))
    lines[at] = '{"kind": INVALID, ' + lines[at]
    path = tmp_path / "results.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert _load_module(SUMMARIZE).main([str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and f"结果文件第 {at + 1} 行不是完整的 JSON 对象" in captured.err, captured


def test_the_harness_starts_a_new_line_before_appending_to_a_half_written_file(tmp_path, monkeypatch, capsys):
    """结果文件末字节不是换行（上一次会话写到一半被终止）：装置追加之前先补一个换行，新会话的 session_start 在新的一行上；
    summarize.py 照样读出这个形态。末字节已是换行时不多补。"""
    old = _session("olda", real=True, finished=False, torn_down=False)
    path = _write_results(tmp_path, old, b'{"kind": "test", "nodeid": "tools/wor')
    monkeypatch.setenv("GKP_RESULTS", str(path))
    conftest = _load_module("tools/workers_real_aws/conftest.py")
    for row in _session("newa", real=True):
        conftest.record(row.pop("kind"), **row)
    lines = path.read_bytes().split(b"\n")
    assert lines[len(old)] == b'{"kind": "test", "nodeid": "tools/wor', lines
    assert lines[len(old) + 1].startswith(b'{"kind": "session_start"'), lines
    assert b"" not in lines[:-1] and lines[-1] == b"", lines   # 没有多出空行
    summary = _summary_of(path, capsys)
    assert summary[1] == "需要处理：收尾没有完成 1 条、会话没有正常结束 1 次、结果文件中途有 1 行没有完整写入", summary
    assert "会话退出码 第 1 个会话 没有 session_finish 一行，第 2 个会话 0" in summary, summary


# 判断「是不是一个 JSON 对象没有写完的开头」用的合法记录：各种值的形态（嵌套、空容器、转义、多字节字符、各种数字与字面量，
# 含 json 模块写出的 NaN 与 Infinity）
_SAMPLE_RECORDS = [
    {"kind": "test", "nodeid": "tools/workers_real_aws/harness.py::test_x[a-1]", "phase": "call", "outcome": "failed",
     "duration": 0.125, "longrepr": "E   assert 'a' == \"b\"\n\tline\\two \u0001 中文 ✓", "xfail": None, "ok": True,
     "bad": False},
    {"kind": "residue", "revisions": {"novaact": [], "act": ["arn:aws:ecs:eu-west-1:123:task-definition/x:1"]},
     "params": [], "table": False, "n": -12, "e": 1.5e-7, "z": 0, "f": -0.0, "big": 12345678901234567890, "x": 1e21},
    {"kind": "step", "nested": [[], {}, [1, [2, {"k": [None, True, False]}]]], "emoji": "😀", "esc": "\\u0041", "": ""},
    # 装置用 json.dumps 的缺省设置写出，nan 与 inf 写成 NaN、Infinity、-Infinity
    {"kind": "lazy_table_built", "seconds": float("nan"), "hi": float("inf"), "lo": [float("-inf"), -1]},
]


def _sample_texts() -> list[str]:
    return [json.dumps(r, ensure_ascii=ensure, separators=seps) for r in _SAMPLE_RECORDS
            for ensure in (False, True) for seps in ((", ", ": "), (",", ":"))]


def test_every_proper_prefix_of_a_valid_record_counts_as_unfinished():
    unfinished = _load_module(SUMMARIZE)._unfinished_object
    for text in _sample_texts():
        data = text.encode("utf-8")
        for k in range(1, len(data)):   # 逐个字节截断，含截在多字节字符中间
            assert unfinished(data[:k].decode("utf-8", "surrogateescape")), data[:k]
        assert not unfinished(text), "完整的对象不算没有写完"


def _insert_positions(text: str) -> tuple[list[int], list[int]]:
    """合法 JSON 文本里可以插入字符的位置：（字符串之外的，字符串里两个完整字符或转义序列之间的）。"""
    outside, inside = [0], []
    i, in_string = 0, False
    while i < len(text):
        c = text[i]
        if in_string:
            inside.append(i)
            if c == '"':
                in_string = False
                i += 1
                outside.append(i)
            else:
                i += 6 if text.startswith("\\u", i) else 2 if c == "\\" else 1
        elif c == '"':
            in_string, i = True, i + 1
        else:
            i += 1
            outside.append(i)
    return outside, inside


def test_randomly_corrupted_prefixes_are_refused():
    """在合法记录的随机位置做一处一定不合法的改动，再在改动之后的随机位置截断：都不算没有写完的开头。改动有四种：插入
    控制字符（JSON 里任何位置都不允许）、在字符串之外插入不可能出现在那里的字符、在字符串里插入不合法的转义、插入不可能
    出现在 UTF-8 里的字节 0xFF。"""
    import random

    unfinished = _load_module(SUMMARIZE)._unfinished_object
    rng = random.Random(20261114)
    for text in _sample_texts():
        outside, inside = _insert_positions(text)
        for _ in range(150):
            kind = rng.choice(("control", "outside", "escape", "byte"))
            if kind == "byte":
                data = text.encode("utf-8")
                p = rng.randrange(len(data) + 1)
                bad = data[:p] + b"\xff" + data[p:]
                cut = bad[:rng.randrange(p + 1, len(bad) + 1)].decode("utf-8", "surrogateescape")
            else:
                if kind == "control":
                    p, piece = rng.randrange(len(text) + 1), chr(rng.choice([*range(0x01, 0x09), 0x0B, 0x0C,
                                                                             *range(0x0E, 0x20)]))
                elif kind == "outside":
                    p, piece = rng.choice(outside), rng.choice("#@;=|x'")
                else:
                    p, piece = rng.choice(inside), "\\" + rng.choice("qxa0'")
                bad = text[:p] + piece + text[p:]
                cut = bad[:rng.randrange(p + len(piece), len(bad) + 1)]
            assert not unfinished(cut), (kind, cut)


@pytest.mark.parametrize("extra, message", [
    ({"GKP_REGION": "us-east-1"}, "GKP_EXEC_ROLE"),
    ({"GKP_REGION": "us-east-1", "GKP_EXEC_ROLE": "some-role"}, "GKP_EXEC_ROLE 必须是 none"),
    ({"GKP_EXEC_ROLE": "none", "AWS_REGION": "", "AWS_DEFAULT_REGION": ""}, "region"),
])
def test_real_mode_refuses_to_start_without_an_explicit_role_or_region(tmp_path, extra, message):
    results = tmp_path / "results.jsonl"
    proc = _pytest(HARNESS, env=_env(GKP_MODE="real", GKP_RESULTS=str(results), **extra), timeout=60)
    assert proc.returncode == pytest.ExitCode.USAGE_ERROR, proc.stdout + proc.stderr
    assert "装置配置有误" in proc.stderr and message in proc.stderr, proc.stderr
    assert not results.exists(), "配置校验失败时不应进入会话"


@pytest.mark.parametrize("var, value", [("GKP_SETTLE", "nan"), ("GKP_SETTLE", "inf"), ("GKP_SETTLE", "-1"),
                                        ("GKP_SETTLE", "abc"), ("GKP_OBS_N", "0"), ("GKP_OBS_N", "-3"),
                                        ("GKP_OBS_N", "1.5"), ("GKP_OBS_N", "x")])
def test_an_invalid_settle_or_observation_count_is_refused_before_collection(tmp_path, var, value):
    """GKP_SETTLE 只接受有限的非负秒数、GKP_OBS_N 只接受正整数，任何模式下都校验（这里是缺省的 moto 模式）。"""
    results = tmp_path / "results.jsonl"
    proc = _pytest(HARNESS, env=_env(GKP_RESULTS=str(results), **{var: value}), timeout=60)
    assert proc.returncode == pytest.ExitCode.USAGE_ERROR, proc.stdout + proc.stderr
    assert "装置配置有误" in proc.stderr and var in proc.stderr and repr(value) in proc.stderr, proc.stderr
    assert not results.exists(), "配置校验失败时不应进入会话"
