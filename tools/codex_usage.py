#!/usr/bin/env python
"""Codex 会话的用量分项与上下文占比（同僚复核续接时的读数：续接上限的判据见 docs/ai-eng/peer-review.md 第四节，Codex CLI 上的做法见第五节）。

用法（只读本机的会话记录，不联网）：
  uv run python tools/codex_usage.py <会话 id> [<会话 id> …] [--sessions-dir <目录> …] [--json]

  <会话 id>：`codex exec` 日志开头 `session id:` 一行的值，也可以给能唯一确定会话的前缀；给多个时逐个汇总。
  --sessions-dir：会话记录的根目录，可以重复给出。默认同时在 `$CODEX_HOME/sessions` 与 `$CODEX_HOME/archived_sessions`
                  里查找（未设 CODEX_HOME 时为 `~/.codex`）：会话归档后它的记录移到归档目录，同一会话的线程可能分在两处。
                  给出本选项时只在给出的目录里查找。实际查找的目录写在输出的「统计范围」里。
  --json：输出机读 JSON（每个会话一个对象，组成列表）；默认输出人读表格。

输出：每个会话一张表，一轮对应一次 `codex exec` 或 `codex exec resume`，没有模型调用的轮次不列出。每轮先列全部线程的合计，
再分列根线程与各子代理线程：Codex 起子代理时，子代理的用量记在各自的记录文件里，只读根线程的记录会漏掉它们，本脚本按记录
首行写明的所属会话一并计入。各列的含义：
  调用        模型调用次数（每次调用一条用量记录）。
  输入        输入 token，含命中缓存与未命中缓存两部分。
  命中缓存    从前缀缓存读出的输入。
  未命中缓存  输入减去命中缓存；缓存写入是其中写进缓存的部分，不另外相加。
  输出        输出 token，含推理输出。
  轮末上下文  该线程本轮最后一次调用之后的上下文大小与模型窗口之比，只对单个线程列出；本轮记录里出现压缩时一并注明次数。
表尾另起一行给出根线程最近一次调用之后的上下文占比，即判断下一轮续接还是改用全新上下文时要看的数。

读数是近似值。上下文大小取最近一次调用的 total_tokens（该次调用的输入加输出）。轮次正常结束、之后记录里没有再写入历史时，
下一次调用带上的历史与它相差不大：推理输出可能不带入下一次调用，读数比实际多出的部分最多是最后一次调用的推理输出，通常是
数百 token。以下情况下读数与下一次调用的实际上下文不符，或不足以支撑续接，表尾逐条注明：最近一次调用之后记录里又写入了历史
（例如工具结果），读数不含这些历史、实际上下文更大；最近一次调用之后发生了压缩，读数是压缩之前的、实际上下文更小；两者
同时出现时方向相反，只说明读数不能用来确定下一次调用的实际上下文；最后一轮被中断或没有结束记录（仍在执行，或进程异常
退出）；记录里出现过压缩，被压掉的细节已不在上下文里。判续接上限看根线程，因为
`codex exec resume` 续接的是它；子代理各有自己的窗口，表里一并列出供参考。

记录格式（按 Codex CLI 0.153.4 至 0.167.1 的本机记录核过）：每行一个 JSON 对象。一个线程的记录可能分成多个片段文件：最初
一份 `rollout-<时刻>-<线程 id>.jsonl`，之后可能有文件名另带一个后缀 id 的延续片段，延续片段的首行与用量记录仍属于原线程。
线程归属与片段关系只按记录内容判断、不看文件名：首行 session_meta 的 payload.id 是线程 id，payload.session_id 是所属会话
（根线程两者相同），payload.timestamp 决定同一线程各片段的先后，子代理另带 agent_path 作标签。每次模型调用一条
token_usage_record，payload.usage 是该次调用的分项，payload.root_turn_id 标明它属于哪一轮；轮次开始的 task_started 事件与
调用之后的 token_count 事件带 model_context_window；轮次以 task_complete 或 turn_aborted 事件结束。压缩在记录里有两种形式：
顶层类型为 compacted 的记录，与类型为 compaction 的 response_item（由压缩过的上下文派生出子代理时出现在记录开头）。
token_count 事件会以相同数值重复出现，不能用来数调用次数，所以分项取自 token_usage_record。
本脚本依赖的字段（首行 session_meta 的 id 与 session_id、用量记录的 root_turn_id 与各分项、有调用的轮次的窗口大小）缺失时，
脚本报出文件、行号与所缺字段，以退出码 2 结束，不按零值继续，也不改用别的字段代替：首行读不出归属的记录可能属于要查的会话，
跳过它会让结果偏少。同一线程分成多个片段、却有片段的首行没有可解析、带时区的 timestamp 时，片段先后无法确定，脚本照常给出
各分项的合计，但不给出该线程的上下文读数并说明原因。空文件跳过；会话仍在写入时最后一行可能不完整，无法解析的行跳过，两者都
在标准错误输出上提示。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 本脚本用到的用量分项（token_usage_record.payload.usage 的键）；缺任一项即视为记录格式变了。
_USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "total_tokens")
# 按轮累加的分项；未命中缓存的输入由输入减命中缓存得出，不单独累加。
_SUM_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens")
_PATTERN = "rollout-*.jsonl"
_ROOT_LABEL = "根线程"
_FORMAT_HINT = "（Codex 的记录格式可能变了）"


class RecordError(Exception):
    """会话记录找不到、有歧义或缺字段；main 打印原因并以退出码 2 结束。"""


@dataclass
class Segment:
    """一个记录文件：一个线程的全部记录，或其中的一个片段。"""

    path: Path
    thread_id: str
    session_id: str
    agent_path: str | None
    started: datetime | None  # 首行的 timestamp；同一线程有多个片段时据此排先后


@dataclass
class RoundUsage:
    """一个线程在一轮里的用量。"""

    calls: int = 0
    sums: Counter = field(default_factory=Counter)
    context: int | None = None  # 本轮最后一次调用的 total_tokens
    window: int | None = None   # 本轮见到的最后一个 model_context_window
    compactions: int = 0
    first_at: str = ""          # 本轮第一次调用所在的文件与行号，报错时指位置用


@dataclass
class Thread:
    thread_id: str
    label: str
    segments: list[Segment]
    order_known: bool               # 片段先后能否确定；不能确定时不给出上下文读数
    rounds: dict[str, RoundUsage]   # 键为 root_turn_id，按首次出现的次序
    last_call: RoundUsage | None = None  # 最近一次调用所在的轮次
    compactions: int = 0
    history_after_last_call: int = 0      # 最近一次调用之后写入的历史项（工具结果、消息等，不含压缩）
    compactions_after_last_call: int = 0
    last_turn_event: str | None = None  # 最后一个轮次事件：task_started / task_complete / turn_aborted


def _default_sessions_dirs() -> list[Path]:
    home = os.environ.get("CODEX_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".codex"
    return [base / "sessions", base / "archived_sessions"]


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    # 不带时区的时刻与带时区的无法比较先后，按无法解析处理。
    return parsed if parsed.tzinfo is not None else None


def _read_segment(path: Path) -> Segment | None:
    """读首行 session_meta 确定归属；空文件返回 None，首行读不出归属时报错。"""
    with path.open(encoding="utf-8") as fh:
        first = fh.readline()
    if not first.strip():
        return None
    try:
        rec = json.loads(first)
    except json.JSONDecodeError:
        raise RecordError(f"{path} 第 1 行：无法解析为 JSON，读不出这份记录属于哪个线程与会话") from None
    payload = rec.get("payload") if isinstance(rec, dict) else None
    if not (isinstance(rec, dict) and rec.get("type") == "session_meta" and isinstance(payload, dict)):
        raise RecordError(f"{path} 第 1 行：不是 session_meta 记录，读不出这份记录属于哪个线程与会话{_FORMAT_HINT}")
    missing = [f"payload.{k}" for k in ("id", "session_id") if not (isinstance(payload.get(k), str) and payload[k])]
    if missing:
        raise RecordError(f"{path} 第 1 行：session_meta 缺少字段 {', '.join(missing)}，读不出这份记录属于哪个线程与会话"
                          f"{_FORMAT_HINT}")
    agent_path = payload.get("agent_path")
    return Segment(path, payload["id"], payload["session_id"], agent_path if isinstance(agent_path, str) else None,
                   _parse_time(payload.get("timestamp")))


def _catalog(dirs: list[Path]) -> list[Segment]:
    files: dict[Path, Path] = {}  # 目录互相包含时同一文件只读一次
    for d in dirs:
        for p in d.rglob(_PATTERN):
            files.setdefault(p.resolve(), p)
    segments = []
    for p in sorted(files.values()):
        seg = _read_segment(p)
        if seg is None:
            print(f"codex_usage: {p} 是空文件，已跳过", file=sys.stderr)
        else:
            segments.append(seg)
    return segments


def _order_segments(segments: list[Segment]) -> tuple[list[Segment], bool]:
    """按首行时刻排同一线程的片段；返回排好的片段与先后能否确定。"""
    if len(segments) == 1:
        return segments, True
    if any(s.started is None for s in segments):
        return sorted(segments, key=lambda s: str(s.path)), False
    by_time = sorted(segments, key=lambda s: s.started)
    for a, b in zip(by_time, by_time[1:]):
        if a.started == b.started:
            raise RecordError(f"线程 {a.thread_id} 的两份记录首行时刻相同，可能是同一份记录同时存在于两个目录，"
                              f"合计会重复计入：\n  {a.path}\n  {b.path}")
    return by_time, True


def _read_thread(segments: list[Segment], label: str) -> Thread:
    ordered, order_known = _order_segments(segments)
    thread = Thread(ordered[0].thread_id, label, ordered, order_known, {})
    current: RoundUsage | None = None  # 最近一次调用所在的轮次；新一轮开始到第一次调用之前为 None
    pending_window: int | None = None  # 最近见到的窗口大小，进入新一轮时作为初值
    pending_compactions = 0            # 新一轮第一次调用之前出现的压缩，计入该轮

    for seg in ordered:
        skipped = 0
        with seg.path.open(encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    skipped += 1
                    continue
                payload = rec.get("payload") if isinstance(rec, dict) else None
                if not isinstance(payload, dict):
                    continue
                kind, event = rec.get("type"), payload.get("type")
                window = None
                if kind == "token_usage_record":
                    key, usage = payload.get("root_turn_id"), payload.get("usage")
                    if not (isinstance(key, str) and key) or not isinstance(usage, dict):
                        raise RecordError(f"{seg.path} 第 {line_no} 行：模型调用的用量记录缺少 payload.root_turn_id 或 "
                                          f"payload.usage{_FORMAT_HINT}")
                    missing = [k for k in _USAGE_FIELDS if not isinstance(usage.get(k), int)]
                    if missing:
                        raise RecordError(f"{seg.path} 第 {line_no} 行：模型调用的用量缺少字段 {', '.join(missing)}"
                                          f"{_FORMAT_HINT}")
                    if key not in thread.rounds:
                        thread.rounds[key] = RoundUsage(window=pending_window,
                                                        first_at=f"{seg.path} 第 {line_no} 行")
                    current = thread.rounds[key]
                    current.compactions += pending_compactions
                    pending_compactions = 0
                    current.calls += 1
                    for k in _SUM_FIELDS:
                        current.sums[k] += usage[k]
                    current.context = usage["total_tokens"]
                    thread.last_call = current
                    thread.history_after_last_call = thread.compactions_after_last_call = 0
                elif kind == "event_msg" and event in ("task_started", "task_complete", "turn_aborted"):
                    thread.last_turn_event = event
                    if event == "task_started":
                        current = None
                        window = payload.get("model_context_window")
                elif kind == "event_msg" and event == "token_count":
                    info = payload.get("info")
                    window = info.get("model_context_window") if isinstance(info, dict) else None
                elif kind == "compacted" or (kind == "response_item" and event == "compaction"):
                    thread.compactions += 1
                    if current is not None:
                        current.compactions += 1
                    else:
                        pending_compactions += 1
                    if thread.last_call is not None:
                        thread.compactions_after_last_call += 1
                elif kind == "response_item" and thread.last_call is not None:
                    # 一次调用的输出（消息、推理、工具调用）写在它的用量记录之前；用量记录之后的历史项（工具结果、
                    # 新消息等）不在那次调用的 total_tokens 里。
                    thread.history_after_last_call += 1
                if isinstance(window, int) and window > 0:
                    pending_window = window
                    if current is not None:
                        current.window = window
        if skipped:
            print(f"codex_usage: {seg.path} 有 {skipped} 行无法解析为 JSON，已跳过（会话仍在写入时最后一行可能不完整）",
                  file=sys.stderr)
    return thread


def _locate(session_id: str, segments: list[Segment], dirs: list[Path]) -> tuple[str, list[Thread]]:
    """按会话 id（或其唯一前缀）找到根线程与同一会话的子代理线程；返回完整会话 id 与线程列表（根线程在首位）。"""
    roots = sorted({s.thread_id for s in segments if s.thread_id == s.session_id and s.thread_id.startswith(session_id)})
    if not roots:
        orphaned = sorted({s.session_id for s in segments if s.session_id.startswith(session_id)})
        if orphaned:
            # 子代理线程的 id 与会话 id 常有相同的前缀，这时不能把它当作「给的是子代理 id」。
            raise RecordError(f"{_scope_text(dirs)} 下只找到会话 {', '.join(orphaned)} 的子代理记录、没有根线程的记录"
                              "（根线程的记录可能在统计范围之外的目录里），无法汇总")
        owners = sorted({s.session_id for s in segments if s.thread_id.startswith(session_id)})
        if owners:
            raise RecordError(f"{session_id} 匹配到的是子代理线程，所属会话 {', '.join(owners)}；请给出会话 id")
        raise RecordError(f"{_scope_text(dirs)} 下找不到会话 {session_id} 的记录"
                          "（会话 id 见 codex exec 日志开头的 session id 一行）")
    if len(roots) > 1:
        raise RecordError(f"会话 id {session_id} 匹配到多个会话，请给出更长的前缀或完整 id：\n  " + "\n  ".join(roots))
    full_id = roots[0]
    by_thread: dict[str, list[Segment]] = {}
    for s in segments:
        if s.session_id == full_id:
            by_thread.setdefault(s.thread_id, []).append(s)
    root = _read_thread(by_thread.pop(full_id), _ROOT_LABEL)

    def started(segs: list[Segment]) -> tuple:
        times = [s.started for s in segs if s.started is not None]
        return (not times, min(times) if times else None, min(str(s.path) for s in segs))

    subagents = []
    for tid, segs in sorted(by_thread.items(), key=lambda item: started(item[1])):
        agent_path = next((s.agent_path for s in segs if s.agent_path), None)
        subagents.append(_read_thread(segs, agent_path or f"子代理 {tid}"))
    return full_id, [root, *subagents]


def _scope_text(dirs: list[Path]) -> str:
    return "、".join(str(d) for d in dirs)


def _root_context(root: Thread) -> tuple[dict | None, str | None]:
    """根线程最近一次调用之后的上下文与读数说明；不能给出时返回 None 与原因。"""
    if not root.order_known:
        return None, (f"根线程的记录分成 {len(root.segments)} 个片段，其中有片段的首行没有可解析、带时区的 timestamp，"
                      "片段先后无法确定，不给出当前的上下文占比")
    last = root.last_call
    if last is None:
        return None, "根线程没有模型调用，无法给出上下文占比"
    caveats = []
    added, compacted_after = root.history_after_last_call, root.compactions_after_last_call
    if added and compacted_after:  # 两者方向相反，合成一条，不分别断言下一次的上下文更大或更小
        caveats.append(f"最近一次调用之后记录里又写入了 {added} 条历史（工具结果、消息等）并发生了压缩：读数是压缩之前的，"
                       "也不含这些历史，无法据此确定下一次调用的实际上下文")
    elif added:
        caveats.append(f"最近一次调用之后记录里又写入了 {added} 条历史（工具结果、消息等），读数不含这些历史，"
                       "下一次调用带上的上下文比它大")
    elif compacted_after:
        caveats.append("最近一次调用之后发生了压缩，读数是压缩之前的，下一次调用带上的上下文比它小")
    if root.last_turn_event == "turn_aborted":
        caveats.append("最后一轮被中断，没有正常结束")
    elif root.last_turn_event == "task_started":
        caveats.append("最后一轮没有结束记录：仍在执行，或进程异常退出")
    if root.compactions:
        caveats.append(f"根线程的记录里出现过 {root.compactions} 次压缩，被压掉的细节已不在上下文里")
    return {"tokens": last.context, "window": last.window, "ratio": last.context / last.window,
            "caveats": caveats}, None


def _summarize(session_id: str, segments: list[Segment], dirs: list[Path]) -> dict:
    full_id, threads = _locate(session_id, segments, dirs)
    if not any(r.calls for t in threads for r in t.rounds.values()):
        raise RecordError(f"会话 {full_id} 的记录里没有模型调用的用量（token_usage_record）：会话可能没有完成过一次模型调用，"
                          f"或 Codex 的记录格式变了（统计范围：{_scope_text(dirs)}）")
    for t in threads:
        for r in t.rounds.values():
            if r.window is None:
                raise RecordError(f"{r.first_at}起的一轮有模型调用、却没有 model_context_window"
                                  "（task_started 与 token_count 事件里都没有），无法计算上下文占比")

    order: list[str] = []  # 轮次的次序以根线程为准，只在子代理里出现的轮次排在其后
    for t in threads:
        order += [k for k in t.rounds if k not in order]
    rounds, grand = [], Counter()
    for n, key in enumerate(order, 1):
        rows, total = [], Counter()
        for t in threads:
            r = t.rounds.get(key)
            if r is None:
                continue
            row = _figures(r.calls, r.sums)
            context = r.context if t.order_known else None
            row.update(thread_id=t.thread_id, label=t.label, context_tokens=context, context_window=r.window,
                       context_ratio=(context / r.window) if context is not None else None,
                       compactions=r.compactions)
            rows.append(row)
            total["calls"] += r.calls
            total.update(r.sums)
        grand.update(total)
        rounds.append({"round": n, "root_turn_id": key, "total": _figures(total["calls"], total), "threads": rows})

    root_now, root_reason = _root_context(threads[0])
    return {"session_id": full_id, "scope": [str(d) for d in dirs],
            "threads": [{"thread_id": t.thread_id, "label": t.label, "files": [str(s.path) for s in t.segments],
                         "segment_order_known": t.order_known, "compactions": t.compactions} for t in threads],
            "rounds": rounds, "total": _figures(grand["calls"], grand),
            "root_context": root_now, "root_context_unavailable": root_reason}


def _figures(calls: int, sums: Counter) -> dict:
    return {"calls": calls, "input_tokens": sums["input_tokens"], "cached_input_tokens": sums["cached_input_tokens"],
            "uncached_input_tokens": sums["input_tokens"] - sums["cached_input_tokens"],
            "cache_write_input_tokens": sums["cache_write_input_tokens"], "output_tokens": sums["output_tokens"]}


def _width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int, right: bool) -> str:
    fill = " " * max(0, width - _width(text))
    return fill + text if right else text + fill


def _context_cell(row: dict) -> str:
    tokens, window = row["context_tokens"], row["context_window"]
    cell = "—" if tokens is None or not window else f"{tokens:,} / {window:,}（{tokens / window:.1%}）"
    return cell + (f"，本轮压缩 {row['compactions']} 次" if row["compactions"] else "")


def _render(report: dict) -> str:
    header = ["轮次", "线程", "调用", "输入", "命中缓存", "未命中缓存", "缓存写入", "输出", "轮末上下文"]
    numeric = ("calls", "input_tokens", "cached_input_tokens", "uncached_input_tokens", "cache_write_input_tokens",
               "output_tokens")

    def cells(round_label: str, label: str, fig: dict, context: str) -> list[str]:
        return [round_label, label, *(f"{fig[k]:,}" for k in numeric), context]

    table = [header]
    for rnd in report["rounds"]:
        table.append(cells(str(rnd["round"]), "合计", rnd["total"], ""))
        for row in rnd["threads"]:
            table.append(cells("", row["label"], row, _context_cell(row)))
    table.append(cells("共计", "合计", report["total"], ""))
    widths = [max(_width(row[i]) for row in table) for i in range(len(header))]
    right = {i for i in range(2, 2 + len(numeric))}
    lines = ["  ".join(_pad(cell, widths[i], i in right) for i, cell in enumerate(row)).rstrip() for row in table]

    subagents = len(report["threads"]) - 1
    title = f"会话 {report['session_id']}：{len(report['rounds'])} 轮，根线程" + (f"与 {subagents} 个子代理线程" if subagents else "")
    scope = f"统计范围：{'、'.join(report['scope'])}"
    now = report["root_context"]
    if now is None:
        tail = [report["root_context_unavailable"]]
    else:
        tail = [f"根线程最近一次调用之后的上下文：{now['tokens']:,} / {now['window']:,}，占模型窗口 {now['ratio']:.1%}"]
        if now["caveats"]:
            tail += ["这个读数与下一次调用的实际上下文可能不符："] + [f"  - {c}" for c in now["caveats"]]
    return "\n".join([title, scope, *lines, *tail])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="codex_usage.py",
        description="按轮次汇总 Codex 会话的用量分项，并给出复核者上下文占模型窗口的比例；只读本机的会话记录，不联网。")
    ap.add_argument("session_ids", nargs="+", metavar="会话id",
                    help="codex exec 日志开头 session id 一行的值，或能唯一确定会话的前缀")
    ap.add_argument("--sessions-dir", type=Path, action="append", default=None,
                    help="会话记录的根目录，可以重复给出（默认同时查找 $CODEX_HOME/sessions 与 $CODEX_HOME/archived_sessions，"
                         "未设 CODEX_HOME 时为 ~/.codex 下的这两个目录）")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    args = ap.parse_args(argv)
    try:
        if args.sessions_dir:
            dirs = [d.expanduser() for d in args.sessions_dir]
            absent = [d for d in dirs if not d.is_dir()]
            if absent:
                raise RecordError(f"会话记录目录不存在：{_scope_text(absent)}")
        else:
            defaults = _default_sessions_dirs()
            dirs = [d for d in defaults if d.is_dir()]
            if not dirs:
                raise RecordError(f"会话记录目录不存在：{_scope_text(defaults)}（用 --sessions-dir 指定，或检查 CODEX_HOME）")
        segments = _catalog(dirs)
        reports = [_summarize(sid, segments, dirs) for sid in args.session_ids]
    except RecordError as exc:
        print(f"codex_usage: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        print("\n\n".join(_render(r) for r in reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
