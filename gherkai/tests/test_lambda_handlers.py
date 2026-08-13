"""Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler _run_ids_from_stream。

只测**事件格式解析**（最易错、最该测的纯逻辑）——用 P4 真验抓到的真实 ECS STOPPED event / DDB Stream event 形状。
handler 的装配部分（造 boto3/core、tick）靠 P4d 真跑验（moto 测不到真 Stream 触发/真 Fargate）。

lambdas/ 在仓库根，测试经 sys.path 加它（Lambda 部署时 handler + core + cli 打进同一 zip）。
"""
from __future__ import annotations

import sys
from pathlib import Path

# lambdas/ 在仓库根（cli/ 的上一级）
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lambdas"))

import exit_observer  # noqa: E402
import reconciler  # noqa: E402


# ---------- 退出观察者 _extract（从 STOPPED event detail 拿 run_id/scope_id/exit_code）----------

def _stopped_detail(run_id, scope_id, exit_code):
    """构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。"""
    return {
        "taskArn": "arn:aws:ecs:us-east-1:000000000000:task/gherkai-cluster/abc",
        "lastStatus": "STOPPED",
        "overrides": {"containerOverrides": [{"environment": [
            {"name": "JOB_S3_URI", "value": "s3://b/x.json"},
            {"name": "RUN_ID", "value": run_id},
            {"name": "SCOPE_ID", "value": scope_id},
        ]}]},
        "containers": [{"name": "novaact-worker", "exitCode": exit_code}],
    }


def test_extract_run_scope_exit():
    run_id, scope_id, exit_code = exit_observer._extract(_stopped_detail("run-1", "a", 0))
    assert run_id == "run-1" and scope_id == "a" and exit_code == 0


def test_extract_nonzero_exit():
    _r, _s, exit_code = exit_observer._extract(_stopped_detail("run-1", "a", 137))
    assert exit_code == 137


def test_extract_missing_exitcode_is_none():
    """container 缺 exitCode（宽限态）→ None（机制二保守）。"""
    detail = _stopped_detail("run-1", "a", 0)
    detail["containers"] = [{"name": "novaact-worker"}]  # 无 exitCode
    _r, _s, exit_code = exit_observer._extract(detail)
    assert exit_code is None


def test_extract_missing_env_returns_none():
    """非本框架起的 task（env 无 RUN_ID/SCOPE_ID）→ (None, None, ...)，handler 会跳过。"""
    detail = {"overrides": {"containerOverrides": [{"environment": []}]}, "containers": []}
    run_id, scope_id, _e = exit_observer._extract(detail)
    assert run_id is None and scope_id is None


def test_handler_skips_when_no_run_id():
    """handler 对缺 run_id 的事件返回 skipped（不崩、不误处理别的 cluster 负载）。"""
    r = exit_observer.handler({"detail": {"overrides": {"containerOverrides": []}, "containers": []}}, None)
    assert r.get("skipped") is True


# ---------- reconciler _run_ids_from_stream（从 DDB Stream records 提取 run_id 集）----------

def _stream_record(pk):
    return {"dynamodb": {"Keys": {"pk": {"S": pk}, "seq": {"N": "1"}}}}


def test_run_ids_single():
    event = {"Records": [_stream_record("run-1#features/x.feature:7")]}
    assert reconciler._run_ids_from_stream(event) == {"run-1"}


def test_run_ids_dedup_multi_scope_same_run():
    """同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。"""
    event = {"Records": [
        _stream_record("run-1#a"), _stream_record("run-1#b"), _stream_record("run-1#a"),
    ]}
    assert reconciler._run_ids_from_stream(event) == {"run-1"}


def test_run_ids_multi_run():
    event = {"Records": [_stream_record("run-1#a"), _stream_record("run-2#b")]}
    assert reconciler._run_ids_from_stream(event) == {"run-1", "run-2"}


def test_run_ids_scope_with_colon_not_hash():
    """scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。"""
    event = {"Records": [_stream_record("20260719T04Z-abc#features/deterministic_anchor.feature:7")]}
    assert reconciler._run_ids_from_stream(event) == {"20260719T04Z-abc"}


# ---------- 启动器 _run_ids_from_runs_stream（两种 event 源，ADR 0034 status --wait 接力 bug 回归）----------

def _runs_stream_record(run_id):
    return {"dynamodb": {"Keys": {"run_id": {"S": run_id}, "item_type": {"S": "META"}}}}


def test_starter_run_ids_from_runs_stream():
    """① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。"""
    event = {"Records": [_runs_stream_record("run-1"), _runs_stream_record("run-2")]}
    assert reconciler._run_ids_from_runs_stream(event) == {"run-1", "run-2"}


def test_starter_run_ids_from_direct_kick():
    """② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug：
    原启动器只认 Stream records、忽略此格式 → status --wait invoke 空转救不了卡 pending 的 run。"""
    assert reconciler._run_ids_from_runs_stream({"run_id": "run-x"}) == {"run-x"}


def test_starter_run_ids_both_sources():
    """Stream records + 直接 run_id 并存时都提取（健壮）。"""
    event = {"Records": [_runs_stream_record("run-1")], "run_id": "run-2"}
    assert reconciler._run_ids_from_runs_stream(event) == {"run-1", "run-2"}


def test_starter_run_ids_empty_when_neither():
    """既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。"""
    assert reconciler._run_ids_from_runs_stream({"test": "kick"}) == set()
