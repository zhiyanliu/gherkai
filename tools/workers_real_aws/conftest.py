"""装置的配置与结果文件。

配置：`settings()` 读 GKP_* 环境变量并校验（各变量的含义见 harness.py 文件头），结果在本进程内缓存；`pytest_configure` 先调用
一次，不合法时以 pytest 的用法错误结束（退出码 4），不进入收集、不发出任何 AWS 请求。未给 GKP_TOKEN 时随机生成一个，并写回
本进程的 GKP_TOKEN，结果文件 `session_start` 一行与清扫入口因此看到同一个令牌；未给 GKP_RESULTS 时取的缺省路径同样写回。

结果文件：每个用例各阶段的结果，与补充用例、收尾记下的观察，逐行追加到一个 jsonl；文件末字节不是换行（上一次会话写到
一半被终止）时先补一个换行再追加。路径取 GKP_RESULTS；未设时取系统临时
目录下 `workers-real-aws-<UTC 时刻>-<进程号>.jsonl`，会话结束时在终端摘要末尾打印。`record(kind, **data)` 是模块级函数，
harness.py 经它写同一个文件。每行一个 JSON 对象，必有 `kind` 与 `ts`；各 kind 的含义见同目录 README.md「读结果」节，
汇总用 summarize.py。

装置记下的问题：种类见 `PROBLEM_KINDS`（收尾里失败的一步、收尾被打断、用例开始前发现的同前缀残留、用例结束之后仍存活的
参与方线程、被测代码的复制请求与种子模板不符），经 `record()` 写入时另记进本进程的问题清单。它们说明真实账户里可能留有
资源、曾有一方在用例之外发出调用，或装置的适配可能掩盖了被测代码的缺陷，与用例本身的通过与否无关，所以单独处理：终端
摘要里列在「装置记下的问题」一节、末行的计数里多出一项「装置问题」；用例全部通过时会话的退出码也改为 1
（`pytest_sessionfinish`，排在 pytest 自身的收尾之后，那里补做的收尾也计在内），不让「全部通过」掩盖它们。参与方线程
残留另由 `pytest_runtest_protocol` 在该条用例的全部阶段结束之后调用装置的 `after_each_test` 终止整个会话（装置在清理之前
已锁存残留并跳过清理），见 harness.py 文件头。

预期失败：`pytest_runtest_makereport` 在报告生成之后，对失败的报告调用装置的 `expected_failure`，返回原因时把报告改为
预期失败；判定的限定见 harness.py 文件头「real 下预期失败的用例」。给了 `--runxfail` 时不作判定，失败照常报告。
"""
from __future__ import annotations

import json
import math
import os
import random
import re
import string
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pytest

# 令牌必须以字母结尾：前缀是 gkp<令牌><序号>-、令牌与序号之间没有分隔符，令牌以数字结尾时「令牌 ab 的清扫」会把
# 令牌 ab12 的 gkpab12001- 当成 ab 的第 12001 号一并清掉；以字母结尾时 gkp<令牌> 之后紧跟的数字串只能是序号，没有歧义。
TOKEN_RE = r"[a-z0-9]{0,11}[a-z]"
EXEC_ROLE_ARN_RE = r"arn:aws[a-z-]*:iam::\d{12}:role/[\w+=,.@/-]+"
MOTO_REGION = "us-east-1"
_DEFAULT_RESULTS = Path(tempfile.gettempdir()) / (
    f"workers-real-aws-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}.jsonl")
_SETTINGS: dict | None = None

# 用例结果之外、要使用者处理的问题（见模块头「装置记下的问题」）：kind 与终端摘要里的名称
PROBLEM_KINDS = {"teardown_failure": "收尾失败", "teardown_interrupted": "清理被中断", "residue": "同前缀残留",
                 "lingering_party_threads": "参与方线程残留", "copy_request_mismatch": "复制请求与模板不符"}
PROBLEM_STAT = "装置问题"   # 终端摘要末行计数里的名称
_PROBLEMS: list[dict] = []


def token_pattern(token: str) -> re.Pattern:
    """令牌 token 的资源名模式：gkp<令牌> 之后紧跟三位以上序号与一个连字符。"""
    return re.compile(rf"^gkp{re.escape(token)}\d{{3,}}-")


def env_region() -> str | None:
    return (os.environ.get("GKP_REGION") or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION") or None)


def _parse() -> dict:
    mode = os.environ.get("GKP_MODE", "moto").strip().lower()
    if mode not in ("moto", "real"):
        raise ValueError(f"GKP_MODE 只能是 moto 或 real，现为 {mode!r}")
    real = mode == "real"
    force = mode == "moto" and os.environ.get("GKP_FORCE_REAL_PATHS") == "1"
    token = (os.environ.get("GKP_TOKEN") or "").strip().lower()
    if not token:
        token = "".join(random.choices(string.ascii_lowercase + string.digits, k=3)) + random.choice(string.ascii_lowercase)
    if not re.fullmatch(TOKEN_RE, token):
        raise ValueError(f"GKP_TOKEN 只能是 1-12 位小写字母数字、且以字母结尾，现为 {token!r}")
    exec_role = os.environ.get("GKP_EXEC_ROLE", "").strip()
    if real:
        if not exec_role:
            raise ValueError("real 模式必须显式给出 GKP_EXEC_ROLE：一个已有的 ECS 任务执行角色的 ARN，或 none（不补角色，"
                             "种子模板的注册预期被真实 ECS 拒绝）。本装置不建、不删、不改任何 IAM 角色")
        if exec_role != "none" and not re.fullmatch(EXEC_ROLE_ARN_RE, exec_role):
            raise ValueError(f"GKP_EXEC_ROLE 必须是 none 或一个 IAM 角色的 ARN，现为 {exec_role!r}")
        region = env_region()
        if not region:
            raise ValueError("real 模式需要 region：设 GKP_REGION（或 AWS_REGION / AWS_DEFAULT_REGION）")
    else:
        if exec_role and exec_role not in ("auto", "none") and not re.fullmatch(EXEC_ROLE_ARN_RE, exec_role):
            raise ValueError(f"GKP_EXEC_ROLE 只能是 auto、none 或一个 IAM 角色的 ARN，现为 {exec_role!r}")
        exec_role = exec_role or "auto"
        region = os.environ.get("GKP_REGION") or MOTO_REGION
    raw_settle = os.environ.get("GKP_SETTLE", "2.0")
    try:
        settle = float(raw_settle)
    except ValueError:
        settle = math.nan
    if not (math.isfinite(settle) and settle >= 0):
        raise ValueError(f"GKP_SETTLE 只能是有限的非负秒数，现为 {raw_settle!r}")
    settle = settle if real else 0.0   # moto 下恒为 0；取值照样校验
    raw_obs_n = os.environ.get("GKP_OBS_N", "40")
    try:
        obs_n = int(raw_obs_n)
    except ValueError:
        obs_n = 0
    if obs_n < 1:
        raise ValueError(f"GKP_OBS_N 只能是正整数，现为 {raw_obs_n!r}")
    os.environ["GKP_TOKEN"] = token
    # 缺省路径同样写回：harness.py 在取不到 pytest 载入的这份 conftest 时会另载一份，两份须写同一个文件
    os.environ["GKP_RESULTS"] = os.environ.get("GKP_RESULTS") or str(_DEFAULT_RESULTS)
    return {"mode": mode, "real": real, "force": force, "token": token, "region": region, "exec_role": exec_role,
            "settle": settle, "obs_n": obs_n, "adapt": os.environ.get("GKP_ADAPT", "1") != "0"}


def settings() -> dict:
    """读 GKP_* 环境变量并校验；不合法时抛 ValueError（消息给使用者看）。同一进程内只解析一次。"""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = _parse()
    return _SETTINGS


def results_path() -> Path:
    return Path(os.environ.get("GKP_RESULTS") or _DEFAULT_RESULTS)


def problems() -> list[dict]:
    """本进程里记下的问题行（种类见 PROBLEM_KINDS），按发生的先后。"""
    return list(_PROBLEMS)


def record(kind: str, **data) -> None:
    line = {"kind": kind, "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), **data}
    if kind in PROBLEM_KINDS:
        _PROBLEMS.append(line)   # 先记进清单：结果文件写不进时问题也不丢
    path = results_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(line, ensure_ascii=False, default=str) + "\n").encode("utf-8")
    with path.open("a+b") as fh:
        # 文件末字节不是换行（上一次会话写到一半被终止）时先补一个换行：新的一行（含新会话的 session_start）总在新的一行上
        fh.seek(0, os.SEEK_END)
        if fh.tell():
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != b"\n":
                data = b"\n" + data
        fh.write(data)


def pytest_configure(config):
    try:
        settings()
    except ValueError as exc:
        raise pytest.UsageError(f"装置配置有误：{exc}") from None


def pytest_sessionstart(session):
    record("session_start", env={k: v for k, v in os.environ.items() if k.startswith("GKP_")},
           rootdir=str(session.config.rootpath), inifile=str(session.config.inipath or ""))


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """一条用例的全部阶段（含收尾）结束、结果都已报告之后，交给装置检查参与方线程（装置借此终止会话，见模块头）。
    放在这里而不是夹具的收尾里：夹具收尾里抛出的退出请求，遇到同一用例另有收尾失败时会被合并成收尾错误，会话照常继续。"""
    result = yield
    after = getattr(getattr(item, "module", None), "after_each_test", None)
    if after is not None:
        after(item.nodeid)
    return result


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """失败的报告交给装置判定是否属于预期失败（限定见 harness.py 文件头），是则改为预期失败，与 xfail 标记的报告形态相同。
    给了 --runxfail 时不改判、照常报告失败，与 pytest 对 xfail 标记的处理一致。"""
    report = yield
    judge = getattr(getattr(item, "module", None), "expected_failure", None)
    if judge is not None and report.failed and not item.config.getoption("runxfail", False):
        reason = judge(item, call)
        if reason:
            report.outcome = "skipped"
            report.wasxfail = reason
    return report


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    # trylast：排在 pytest 自身的 sessionfinish 之后，会话被中途终止时它补做的夹具收尾所记下的问题也计在内
    if _PROBLEMS and session.exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    record("session_finish", exitstatus=int(session.exitstatus),
           problems=dict(Counter(PROBLEM_KINDS[p["kind"]] for p in _PROBLEMS)))


def _problem_line(row: dict) -> str:
    detail = {k: v for k, v in row.items() if k not in ("kind", "ts", "nodeid")}
    return f"{PROBLEM_KINDS[row['kind']]} {row.get('nodeid') or '-'}：{json.dumps(detail, ensure_ascii=False, default=str)[:400]}"


def pytest_terminal_summary(terminalreporter):
    if _PROBLEMS:
        tr = terminalreporter
        tr.section("装置记下的问题（与用例的通过与否无关，会话因此以非零退出码结束）", sep="=", red=True, bold=True)
        for row in _PROBLEMS:
            tr.write_line(_problem_line(row), red=True)
        s = settings()
        if s["real"]:
            tr.write_line("真实账户里可能留有本次执行的资源：进程退出之后执行 "
                          f"python tools/workers_real_aws/harness.py --sweep {s['token']} --region {s['region']}"
                          "（见 README.md「清扫残留」）", red=True)
        else:
            tr.write_line("moto 模式下的资源随每条用例的模拟环境一起消失，不必清扫；这些问题说明装置或测试文件需要修正",
                          red=True)
        tr.stats.setdefault(PROBLEM_STAT, []).extend(_PROBLEMS)   # 末行计数里多出一项「装置问题」
    terminalreporter.write_line(f"结果文件：{results_path()}")


def pytest_runtest_logreport(report):
    data = {"nodeid": report.nodeid, "phase": report.when, "outcome": report.outcome,
            "duration": round(report.duration, 3)}
    if hasattr(report, "wasxfail"):
        data["xfail_reason"] = report.wasxfail
    if report.failed:
        data["longrepr"] = report.longreprtext or ""   # 完整保存：长 traceback 的末尾几行才是异常的原因
    elif hasattr(report, "wasxfail"):
        data["xfail_detail"] = report.longreprtext or ""   # 预期失败时实际抛出的异常，用来核对判定的依据
    elif report.skipped:
        longrepr = report.longrepr
        if isinstance(longrepr, tuple) and len(longrepr) == 3:
            data["skip_reason"] = str(longrepr[2])
        elif longrepr is not None:
            data["skip_reason"] = str(longrepr)
    record("test", **data)
