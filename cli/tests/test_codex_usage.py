"""`tools/codex_usage.py` 的单测：用合成的小型会话记录核对线程归属、片段先后、统计范围、读数说明与缺字段报错。

夹具里的 id、时刻与数值都是合成的，只保留脚本依赖的字段与记录形态（首行 session_meta、每次模型调用一条 token_usage_record、
轮次事件、压缩记录），记录形态按 Codex CLI 的本机记录核过，见脚本头注释「记录格式」段。
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from _doc_rules import REPO

TOOL = REPO / "tools" / "codex_usage.py"
WINDOW = 1000
ROOT = "00000000-0000-7000-8000-00000000a001"
SUB = "00000000-0000-7000-8000-00000000b001"
TURN1 = "00000000-0000-7000-8000-00000000c001"
TURN2 = "00000000-0000-7000-8000-00000000c002"


def _load():
    spec = importlib.util.spec_from_file_location("codex_usage", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclass 解析注解时要在 sys.modules 里找到模块
    spec.loader.exec_module(module)
    return module


codex_usage = _load()


# ── 合成记录的构造 ─────────────────────────────────────────────────────────


def meta(thread: str, session: str, ts: str | None = "2026-01-01T00:00:00.000Z", **extra) -> dict:
    payload = {"id": thread, "session_id": session, **extra}
    if ts is not None:
        payload["timestamp"] = ts
    return {"type": "session_meta", "payload": payload}


def started(turn: str, window: int | None = WINDOW, root_turn: bool = True) -> dict:
    payload = {"type": "task_started", "turn_id": turn}
    if root_turn:
        payload["root_turn_id"] = turn
    if window is not None:
        payload["model_context_window"] = window
    return {"type": "event_msg", "payload": payload}


def call(turn: str, inp: int, cached: int, out: int, write: int = 0) -> list[dict]:
    """一次模型调用：输出项写在用量记录之前，之后是 token_count 事件。"""
    usage = {"input_tokens": inp, "cached_input_tokens": cached, "cache_write_input_tokens": write,
             "output_tokens": out, "reasoning_output_tokens": 0, "total_tokens": inp + out}
    return [{"type": "response_item", "payload": {"type": "function_call"}},
            {"type": "token_usage_record", "payload": {"root_turn_id": turn, "usage": usage}},
            {"type": "event_msg", "payload": {"type": "token_count", "info": {"model_context_window": WINDOW}}}]


def tool_output() -> dict:
    return {"type": "response_item", "payload": {"type": "function_call_output"}}


def complete(turn: str) -> dict:
    return {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": turn}}


def aborted(turn: str) -> dict:
    return {"type": "event_msg", "payload": {"type": "turn_aborted", "turn_id": turn, "reason": "interrupted"}}


COMPACTED = {"type": "compacted", "payload": {"message": "", "replacement_history": []}}
COMPACTION_ITEM = {"type": "response_item", "payload": {"type": "compaction"}}


def write(directory: Path, name: str, *records) -> Path:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for rec in records:
        lines += [json.dumps(r) for r in (rec if isinstance(rec, list) else [rec])]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def two_round_root(directory: Path, name: str = f"2026/01/01/rollout-2026-01-01T00-00-00-{ROOT}.jsonl") -> Path:
    """根线程两轮三次调用，正常结束；第一轮的窗口只出现在 task_started 里。"""
    return write(directory, name, meta(ROOT, ROOT),
                 started(TURN1), call(TURN1, 100, 60, 10)[:2], complete(TURN1),
                 started(TURN2, window=None), call(TURN2, 200, 150, 20), call(TURN2, 300, 250, 30), complete(TURN2))


def run(capsys, *argv: str) -> tuple[int, list | None, str]:
    code = codex_usage.main([*argv, "--json"])
    out, err = capsys.readouterr()
    return code, (json.loads(out) if code == 0 else None), err


# ── 用例 ───────────────────────────────────────────────────────────────────


def test_single_thread_rounds_totals_and_root_context(tmp_path, capsys):
    """单线程两轮：每轮分项与共计按用量记录累加，表尾读数取最后一次调用的 total_tokens；正常结束的会话没有读数说明。"""
    two_round_root(tmp_path)
    code, reports, _ = run(capsys, ROOT[:30], "--sessions-dir", str(tmp_path))
    assert code == 0
    report = reports[0]
    assert [r["total"]["calls"] for r in report["rounds"]] == [1, 2]
    assert report["rounds"][0]["threads"][0]["context_window"] == WINDOW
    assert report["total"] == {"calls": 3, "input_tokens": 600, "cached_input_tokens": 460, "uncached_input_tokens": 140,
                               "cache_write_input_tokens": 0, "output_tokens": 60}
    assert report["root_context"] == {"tokens": 330, "window": WINDOW, "ratio": 0.33, "caveats": []}
    assert report["scope"] == [str(tmp_path)]


def test_subagent_is_counted_in_the_round_of_its_usage_records(tmp_path, capsys):
    """子代理按首行的所属会话计入；它的 task_started 只带自己的 turn_id，轮次仍按用量记录的 root_turn_id 归入，不多出一轮。"""
    two_round_root(tmp_path)
    write(tmp_path, f"2026/01/01/rollout-2026-01-01T00-00-05-{SUB}.jsonl",
          meta(SUB, ROOT, "2026-01-01T00:00:05.000Z", parent_thread_id=ROOT, agent_path="/root/checker"),
          started("00000000-0000-7000-8000-00000000d001", root_turn=False), call(TURN2, 40, 0, 4),
          complete("00000000-0000-7000-8000-00000000d001"))
    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 0
    report = reports[0]
    assert [t["label"] for t in report["threads"]] == ["根线程", "/root/checker"]
    assert len(report["rounds"]) == 2
    assert [row["label"] for row in report["rounds"][1]["threads"]] == ["根线程", "/root/checker"]
    assert report["rounds"][1]["total"]["calls"] == 3
    assert report["total"]["input_tokens"] == 640
    assert report["root_context"]["tokens"] == 330  # 子代理的调用不影响根线程的读数


def test_continuation_segment_is_part_of_the_root_thread(tmp_path, capsys):
    """延续片段（文件名另带后缀 id）按首行元数据归入根线程，不当作子代理；片段先后按首行时刻排，读数取最后一个片段里的
    最后一次调用。延续片段放在路径排序靠前的目录里，按路径排先后就会取错读数。"""
    two_round_root(tmp_path, f"2026/01/02/rollout-2026-01-02T00-00-00-{ROOT}.jsonl")
    turn3 = "00000000-0000-7000-8000-00000000c003"
    write(tmp_path, f"2026/01/01/rollout-2026-01-03T00-00-00-{ROOT}_00000000-0000-7000-8000-00000000e001.jsonl",
          meta(ROOT, ROOT, "2026-01-03T00:00:00.000Z", history_base={"thread_id": ROOT, "end_ordinal_exclusive": 12}),
          started(turn3), call(turn3, 800, 700, 50), complete(turn3))
    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 0
    report = reports[0]
    assert len(report["threads"]) == 1 and len(report["threads"][0]["files"]) == 2
    assert [r["threads"][0]["label"] for r in report["rounds"]] == ["根线程"] * 3
    assert report["total"]["calls"] == 4
    assert report["root_context"]["tokens"] == 850


def test_segment_order_unknown_refuses_root_context(tmp_path, capsys):
    """同一线程的片段里有一份首行没有 timestamp：合计照常给出，上下文读数不给出并说明原因。"""
    two_round_root(tmp_path)
    turn3 = "00000000-0000-7000-8000-00000000c003"
    write(tmp_path, f"2026/01/03/rollout-2026-01-03T00-00-00-{ROOT}_00000000-0000-7000-8000-00000000e001.jsonl",
          meta(ROOT, ROOT, ts=None), started(turn3), call(turn3, 800, 700, 50), complete(turn3))
    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 0
    report = reports[0]
    assert report["total"]["calls"] == 4
    assert report["root_context"] is None
    assert "片段先后无法确定" in report["root_context_unavailable"]
    assert all(row["context_tokens"] is None for r in report["rounds"] for row in r["threads"])


def test_timestamp_without_timezone_counts_as_unknown_order(tmp_path, capsys):
    """不带时区的首行时刻与带时区的无法比较先后，按先后无法确定处理，不让排序出错退出。"""
    two_round_root(tmp_path)
    turn3 = "00000000-0000-7000-8000-00000000c003"
    write(tmp_path, f"2026/01/03/rollout-2026-01-03T00-00-00-{ROOT}_00000000-0000-7000-8000-00000000e001.jsonl",
          meta(ROOT, ROOT, ts="2026-01-03T00:00:00"), started(turn3), call(turn3, 800, 700, 50), complete(turn3))
    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 0
    assert reports[0]["root_context"] is None and "片段先后无法确定" in reports[0]["root_context_unavailable"]


def test_subagents_without_root_thread_are_an_error(tmp_path, capsys):
    """统计范围里只有某会话的子代理记录、没有根线程记录时报错，并且不因子代理 id 与会话 id 前缀相同而误报「给的是子代理 id」。"""
    sub = ROOT[:-4] + "b001"
    write(tmp_path, f"rollout-2026-01-01T00-00-05-{sub}.jsonl",
          meta(sub, ROOT, "2026-01-01T00:00:05.000Z", parent_thread_id=ROOT), started(TURN1), call(TURN1, 40, 0, 4))
    code, _, err = run(capsys, ROOT[:30], "--sessions-dir", str(tmp_path))
    assert code == 2
    assert f"只找到会话 {ROOT} 的子代理记录、没有根线程的记录" in err


def test_default_scope_covers_active_and_archived_sessions(tmp_path, capsys, monkeypatch):
    """默认同时在活动目录与归档目录里查找，输出写明统计范围；给出 --sessions-dir 时只查给出的目录。"""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    active, archived = tmp_path / "sessions", tmp_path / "archived_sessions"
    two_round_root(active)
    write(archived, f"rollout-2026-01-01T00-00-05-{SUB}.jsonl",
          meta(SUB, ROOT, "2026-01-01T00:00:05.000Z", parent_thread_id=ROOT), started(TURN2), call(TURN2, 40, 0, 4))
    code, reports, _ = run(capsys, ROOT)
    assert code == 0
    assert reports[0]["scope"] == [str(active), str(archived)]
    assert reports[0]["total"]["calls"] == 4

    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(active))
    assert code == 0
    assert reports[0]["scope"] == [str(active)]
    assert reports[0]["total"]["calls"] == 3


def test_same_segment_in_both_directories_is_an_error(tmp_path, capsys):
    """同一份记录同时出现在两个目录里时报错，不重复计入。"""
    active, archived = tmp_path / "sessions", tmp_path / "archived_sessions"
    path = two_round_root(active)
    archived.mkdir()
    shutil.copy(path, archived / path.name)
    code, _, err = run(capsys, ROOT, "--sessions-dir", str(active), "--sessions-dir", str(archived))
    assert code == 2
    assert "首行时刻相同" in err and str(archived / path.name) in err


def test_compaction_is_marked_on_the_round_and_the_root_reading(tmp_path, capsys):
    """压缩记录计入所在轮次与线程，表尾注明；发生在最近一次调用之后时另注明读数偏大。子代理开头的 compaction 历史项
    计入它的第一轮。"""
    write(tmp_path, f"rollout-2026-01-01T00-00-00-{ROOT}.jsonl", meta(ROOT, ROOT),
          started(TURN1), call(TURN1, 900, 0, 10), COMPACTED, call(TURN1, 150, 0, 10), complete(TURN1),
          started(TURN2), call(TURN2, 300, 0, 10), COMPACTED, complete(TURN2))
    write(tmp_path, f"rollout-2026-01-01T00-00-05-{SUB}.jsonl",
          meta(SUB, ROOT, "2026-01-01T00:00:05.000Z", parent_thread_id=ROOT), COMPACTION_ITEM,
          started(TURN1, root_turn=False), call(TURN1, 40, 0, 4))
    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 0
    report = reports[0]
    assert [row["compactions"] for row in report["rounds"][0]["threads"]] == [1, 1]
    assert report["rounds"][1]["threads"][0]["compactions"] == 1
    assert [t["compactions"] for t in report["threads"]] == [2, 1]
    caveats = report["root_context"]["caveats"]
    assert any("之后发生了压缩" in c for c in caveats)
    assert any("出现过 2 次压缩" in c for c in caveats)

    assert codex_usage.main([ROOT, "--sessions-dir", str(tmp_path)]) == 0
    text = capsys.readouterr().out
    assert "本轮压缩 1 次" in text and "出现过 2 次压缩" in text and f"统计范围：{tmp_path}" in text


@pytest.mark.parametrize(("tail", "expected"), [
    ([tool_output(), complete(TURN1)], "又写入了 1 条历史"),
    ([tool_output(), aborted(TURN1)], "最后一轮被中断"),
    ([tool_output()], "最后一轮没有结束记录"),
])
def test_stale_reading_is_marked(tmp_path, capsys, tail, expected):
    """最近一次调用之后又写入历史、最后一轮被中断、最后一轮没有结束记录，三种情况都在读数说明里注明。"""
    write(tmp_path, f"rollout-2026-01-01T00-00-00-{ROOT}.jsonl", meta(ROOT, ROOT),
          started(TURN1), call(TURN1, 100, 0, 10), *tail)
    code, reports, _ = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 0
    caveats = reports[0]["root_context"]["caveats"]
    assert any(expected in c for c in caveats), caveats


@pytest.mark.parametrize(("records", "where"), [
    ([{"type": "session_meta", "payload": {"id": SUB}}, started(TURN1), call(TURN1, 40, 0, 4)],
     "第 1 行：session_meta 缺少字段 payload.session_id"),
    ([{"type": "event_msg", "payload": {"type": "task_started"}}], "第 1 行：不是 session_meta 记录"),
    ([meta(SUB, ROOT, parent_thread_id=ROOT), started(TURN1),
      {"type": "token_usage_record", "payload": {"usage": {}}}], "第 3 行：模型调用的用量记录缺少 payload.root_turn_id"),
    ([meta(SUB, ROOT, parent_thread_id=ROOT), started(TURN1),
      {"type": "token_usage_record", "payload": {"root_turn_id": TURN1, "usage": {
          "input_tokens": 1, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "total_tokens": 1}}}],
     "第 3 行：模型调用的用量缺少字段 output_tokens"),
])
def test_missing_fields_are_errors_with_file_and_line(tmp_path, capsys, records, where):
    """依赖的字段缺失时以退出码 2 结束并报出文件、行号与字段，不改用别的字段代替：首行读不出归属的记录可能属于要查的会话。"""
    two_round_root(tmp_path)
    bad = write(tmp_path, f"rollout-2026-01-01T00-00-05-{SUB}.jsonl", *records)
    code, _, err = run(capsys, ROOT, "--sessions-dir", str(tmp_path))
    assert code == 2
    assert f"{bad} {where}" in err
