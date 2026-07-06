"""JobSource 单测（Nova，ADR 0024 I/O 边缘可注入接口第一期）：subprocess 态读 stdin 首行 JSON。

此前内联在 run_scope main（json.loads(sys.stdin.readline())），无测试覆盖。不连真 AWS、不起子进程。
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.job_source import JobSource


def test_read_parses_first_line_json_from_stdin(monkeypatch):
    # subprocess 态：读 stdin 首行、解析成 job dict。
    job_line = '{"scope": {"id": "s:0", "name": "S"}, "scenarios": [], "assertionVotes": 3}\n'
    monkeypatch.setattr(sys, "stdin", io.StringIO(job_line))
    job = JobSource.from_env().read()
    assert job["scope"]["id"] == "s:0"
    assert job["assertionVotes"] == 3


def test_read_takes_only_first_line_not_eof(monkeypatch):
    # readline 只取首行、不等 EOF——尾随行（噪声/多 job）不影响首行解析。
    stdin = '{"scope": {"id": "s:0"}, "scenarios": []}\n后续噪声行不该被解析\n'
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    job = JobSource.from_env().read()
    assert job["scope"]["id"] == "s:0"  # 只解析首行，尾随行不干扰


def test_s3_uri_injected_raises_not_silently_stdin(monkeypatch):
    # S3 态守卫（Fargate 化未实现）：注入 JOB_S3_URI → read() fail-loud 抛，不静默走 stdin（否则 Fargate 无
    # stdin 会挂在 readline）。锁死守卫不被误删。
    import pytest
    monkeypatch.setenv("JOB_S3_URI", "s3://bucket/job.json")
    with pytest.raises(NotImplementedError, match="S3 态未实现"):
        JobSource.from_env().read()


def test_empty_s3_uri_treated_as_unset(monkeypatch):
    # 空串 JOB_S3_URI 统一当「未注入」（or None，对称 Midscene）→ 走 stdin、不误当 S3 态抛。
    monkeypatch.setenv("JOB_S3_URI", "")
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"scope": {"id": "s:0"}, "scenarios": []}\n'))
    job = JobSource.from_env().read()
    assert job["scope"]["id"] == "s:0"
