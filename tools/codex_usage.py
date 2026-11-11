#!/usr/bin/env python
"""Codex 会话的用量分项与上下文占比（同僚复核续接时的读数：续接上限的判据见 docs/ai-eng/peer-review.md 第四节，Codex CLI 上的做法见第五节）。

用法（只读本机的会话记录，不联网）：
  uv run python tools/codex_usage.py <会话 id> [<会话 id> …] [--sessions-dir <目录>] [--json]

  <会话 id>：`codex exec` 日志开头 `session id:` 一行的值，也可以给能唯一确定会话的前缀；给多个时逐个汇总。
  --sessions-dir：会话记录的根目录，默认 `$CODEX_HOME/sessions`（未设 CODEX_HOME 时为 `~/.codex/sessions`）；
                  已归档的会话在 `~/.codex/archived_sessions`，用本选项指向它。
  --json：输出机读 JSON（每个会话一个对象，组成列表）；默认输出人读表格。

输出：每个会话一张表，一轮对应一次 `codex exec` 或 `codex exec resume`。每轮先列全部线程的合计，再分列根线程与各子代理
线程：Codex 起子代理时，子代理的用量记在各自的记录文件里（文件名带子代理线程的 id、不带会话 id，首行写明所属会话），本脚本
按首行的会话 id 一并计入，只读文件名带会话 id 的那一份会漏掉它们。各列的含义：
  调用        模型调用次数（每次调用一条用量记录）。
  输入        输入 token，含命中缓存与未命中缓存两部分。
  命中缓存    从前缀缓存读出的输入。
  未命中缓存  输入减去命中缓存；缓存写入是其中写进缓存的部分，不另外相加。
  输出        输出 token，含推理输出。
  轮末上下文  该线程本轮最后一次调用之后的上下文大小与模型窗口之比，只对单个线程列出。
表尾另起一行给出根线程最近一次调用之后的上下文占比，即判断下一轮续接还是改用全新上下文时要看的数。

上下文大小取最近一次调用的 total_tokens（该次调用的输入加输出）。下一次调用带上的历史不会多于它：推理输出可能不带入下一次
调用，所以这个读数偏保守，多出的部分最多是最后一次调用的推理输出，通常是数百 token。判续接上限看根线程，因为
`codex exec resume` 续接的是它；子代理各有自己的窗口，表里一并列出供参考。

记录格式（按 Codex CLI 0.153 至 0.167 的本机记录核过）：每个线程一份 `rollout-<时刻>-<线程 id>.jsonl`，每行一个 JSON 对象。
首行 session_meta 带 session_id，子代理线程另带 parent_thread_id 与 agent_path；每次模型调用一条 token_usage_record，
payload.usage 是该次调用的分项，payload.root_turn_id 标明它属于哪一轮；轮次开始的 task_started 事件与调用之后的 token_count
事件都带 model_context_window。token_count 事件会以相同数值重复出现，不能用来数调用次数，所以分项取自 token_usage_record。
用量记录缺字段或某轮没有窗口大小时，脚本报出文件、行号与所缺字段，以退出码 2 结束，不按零值继续；无法解析的行（会话仍在写入
时最后一行可能不完整）跳过并在标准错误输出上提示。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# 本脚本用到的用量分项（token_usage_record.payload.usage 的键）；缺任一项即视为记录格式变了。
_USAGE_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "total_tokens")
# 按轮累加的分项；未命中缓存的输入由输入减命中缓存得出，不单独累加。
_SUM_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens")
_PREFIX = "rollout-"
_STAMP_LEN = len("2026-01-01T00-00-00-")  # 文件名里线程 id 之前的时刻段，含末尾的连字符
_ROOT_LABEL = "根线程"


class RecordError(Exception):
    """会话记录找不到、有歧义或缺字段；main 打印原因并以退出码 2 结束。"""


@dataclass
class RoundUsage:
    """一个线程在一轮里的用量。"""

    calls: int = 0
    sums: Counter = field(default_factory=Counter)
    context: int | None = None  # 本轮最后一次调用的 total_tokens
    window: int | None = None   # 本轮见到的最后一个 model_context_window
    first_line: int = 0         # 本轮在该线程记录里第一次出现的行号，报错时指位置用


@dataclass
class Thread:
    thread_id: str
    label: str
    path: Path
    rounds: dict[str, RoundUsage]  # 键为 root_turn_id，按在本线程记录里首次出现的次序
    skipped_lines: int


def _default_sessions_dir() -> Path:
    home = os.environ.get("CODEX_HOME")
    return (Path(home).expanduser() if home else Path.home() / ".codex") / "sessions"


def _thread_id_of(path: Path) -> str:
    """文件名 `rollout-<时刻>-<线程 id>.jsonl` 里的线程 id。"""
    return path.name[len(_PREFIX) + _STAMP_LEN:-len(".jsonl")]


def _read_meta(path: Path) -> dict:
    """首行 session_meta 的 payload；首行读不出或不是 session_meta 时返回空字典。"""
    try:
        with path.open(encoding="utf-8") as fh:
            rec = json.loads(fh.readline())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    payload = rec.get("payload") if isinstance(rec, dict) and rec.get("type") == "session_meta" else None
    return payload if isinstance(payload, dict) else {}


def _session_of(meta: dict, fallback: str) -> str:
    return meta.get("session_id") or meta.get("id") or fallback


def _is_subagent(meta: dict, path: Path) -> bool:
    thread_id = _thread_id_of(path)
    return bool(meta.get("parent_thread_id")) or meta.get("thread_source") == "subagent" \
        or _session_of(meta, thread_id) != thread_id


def _label_of(meta: dict, thread_id: str) -> str:
    return meta.get("agent_path") or f"子代理 {thread_id}"


def _read_thread(path: Path, label: str) -> Thread:
    rounds: dict[str, RoundUsage] = {}
    current: RoundUsage | None = None
    skipped = 0

    def enter(key: str, line_no: int) -> RoundUsage:
        if key not in rounds:
            rounds[key] = RoundUsage(first_line=line_no)
        return rounds[key]

    with path.open(encoding="utf-8") as fh:
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
            if kind == "event_msg" and event == "task_started":
                key = payload.get("root_turn_id") or payload.get("turn_id")
                if key:
                    current = enter(key, line_no)
                window = payload.get("model_context_window")
            elif kind == "event_msg" and event == "token_count":
                info = payload.get("info")
                window = info.get("model_context_window") if isinstance(info, dict) else None
            elif kind == "token_usage_record":
                key, usage = payload.get("root_turn_id"), payload.get("usage")
                if not key or not isinstance(usage, dict):
                    raise RecordError(f"{path} 第 {line_no} 行：模型调用的用量记录缺少 payload.root_turn_id 或 payload.usage"
                                      "（Codex 的记录格式可能变了）")
                missing = [k for k in _USAGE_FIELDS if not isinstance(usage.get(k), int)]
                if missing:
                    raise RecordError(f"{path} 第 {line_no} 行：模型调用的用量缺少字段 {', '.join(missing)}"
                                      "（Codex 的记录格式可能变了）")
                current = enter(key, line_no)
                current.calls += 1
                for k in _SUM_FIELDS:
                    current.sums[k] += usage[k]
                current.context = usage["total_tokens"]
            if current is not None and isinstance(window, int) and window > 0:
                current.window = window
    return Thread(_thread_id_of(path), label, path, rounds, skipped)


def _locate(session_id: str, files: list[Path], metas: dict[Path, dict], sessions_dir: Path) -> tuple[str, list[Path]]:
    """按会话 id（或其唯一前缀）找到根线程的记录与同一会话的子代理记录；返回完整会话 id 与文件列表（根线程在首位）。"""
    named = [p for p in files if _thread_id_of(p).startswith(session_id)]
    if not named:
        raise RecordError(f"{sessions_dir} 下找不到会话 {session_id} 的记录：没有文件名里的线程 id 以它开头的 {_PREFIX}*.jsonl"
                          "（会话 id 见 codex exec 日志开头的 session id 一行；已归档的会话用 --sessions-dir 指向 archived_sessions）")
    # 子代理线程与根线程的 id 前缀相近（id 以创建时刻开头），前缀同时匹配到两者时取根线程
    roots = [p for p in named if not _is_subagent(metas.get(p) or {}, p)]
    if not roots:
        owners = sorted({_session_of(metas.get(p) or {}, _thread_id_of(p)) for p in named})
        raise RecordError(f"{session_id} 匹配到的是子代理线程，所属会话 {', '.join(owners)}；请给出会话 id")
    if len(roots) > 1:
        listing = "\n  ".join(str(p) for p in roots)
        raise RecordError(f"会话 id {session_id} 匹配到多个会话，请给出更长的前缀或完整 id：\n  {listing}")
    root = roots[0]
    full_id = _thread_id_of(root)
    subagents = [p for p in files if p != root and _session_of(metas.get(p) or {}, _thread_id_of(p)) == full_id]
    return full_id, [root, *subagents]


def _summarize(session_id: str, files: list[Path], metas: dict[Path, dict], sessions_dir: Path) -> dict:
    full_id, paths = _locate(session_id, files, metas, sessions_dir)
    threads = [_read_thread(paths[0], _ROOT_LABEL)]
    threads += [_read_thread(p, _label_of(metas.get(p) or {}, _thread_id_of(p))) for p in paths[1:]]
    for t in threads:
        if t.skipped_lines:
            print(f"codex_usage: {t.path} 有 {t.skipped_lines} 行无法解析为 JSON，已跳过（会话仍在写入时最后一行可能不完整）",
                  file=sys.stderr)
    if not any(r.calls for t in threads for r in t.rounds.values()):
        raise RecordError(f"会话 {full_id} 的记录里没有模型调用的用量（token_usage_record）：会话可能没有完成过一次模型调用，"
                          "或 Codex 的记录格式变了")
    for t in threads:
        for r in t.rounds.values():
            if r.calls and r.window is None:
                raise RecordError(f"{t.path}：自第 {r.first_line} 行开始的一轮有模型调用、却没有 model_context_window"
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
            row.update(thread_id=t.thread_id, label=t.label, context_tokens=r.context, context_window=r.window,
                       context_ratio=(r.context / r.window) if r.context is not None and r.window else None)
            rows.append(row)
            total["calls"] += r.calls
            total.update(r.sums)
        grand.update(total)
        rounds.append({"round": n, "root_turn_id": key, "total": _figures(total["calls"], total), "threads": rows})

    root_now = None  # 根线程最近一次调用之后的上下文：取最后一个有调用的轮次
    for key in reversed(list(threads[0].rounds)):
        r = threads[0].rounds[key]
        if r.context is not None:
            root_now = {"tokens": r.context, "window": r.window, "ratio": r.context / r.window}
            break
    return {"session_id": full_id,
            "threads": [{"thread_id": t.thread_id, "label": t.label, "file": str(t.path)} for t in threads],
            "rounds": rounds, "total": _figures(grand["calls"], grand), "root_context": root_now}


def _figures(calls: int, sums: Counter) -> dict:
    return {"calls": calls, "input_tokens": sums["input_tokens"], "cached_input_tokens": sums["cached_input_tokens"],
            "uncached_input_tokens": sums["input_tokens"] - sums["cached_input_tokens"],
            "cache_write_input_tokens": sums["cache_write_input_tokens"], "output_tokens": sums["output_tokens"]}


def _width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _pad(text: str, width: int, right: bool) -> str:
    fill = " " * max(0, width - _width(text))
    return fill + text if right else text + fill


def _context_cell(tokens: int | None, window: int | None) -> str:
    if tokens is None or not window:
        return "—"
    return f"{tokens:,} / {window:,}（{tokens / window:.1%}）"


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
            table.append(cells("", row["label"], row, _context_cell(row["context_tokens"], row["context_window"])))
    table.append(cells("共计", "合计", report["total"], ""))
    widths = [max(_width(row[i]) for row in table) for i in range(len(header))]
    right = {i for i in range(2, 2 + len(numeric))}
    lines = ["  ".join(_pad(cell, widths[i], i in right) for i, cell in enumerate(row)).rstrip() for row in table]

    subagents = len(report["threads"]) - 1
    title = f"会话 {report['session_id']}：{len(report['rounds'])} 轮，根线程" + (f"与 {subagents} 个子代理线程" if subagents else "")
    now = report["root_context"]
    tail = (f"根线程最近一次调用之后的上下文：{now['tokens']:,} / {now['window']:,}，占模型窗口 {now['ratio']:.1%}"
            if now else "根线程没有模型调用，无法给出上下文占比")
    return "\n".join([title, *lines, tail])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="codex_usage.py",
        description="按轮次汇总 Codex 会话的用量分项，并给出复核者上下文占模型窗口的比例；只读本机的会话记录，不联网。")
    ap.add_argument("session_ids", nargs="+", metavar="会话id",
                    help="codex exec 日志开头 session id 一行的值，或能唯一确定会话的前缀")
    ap.add_argument("--sessions-dir", type=Path, default=None,
                    help="会话记录的根目录（默认 $CODEX_HOME/sessions，未设 CODEX_HOME 时为 ~/.codex/sessions）")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    args = ap.parse_args(argv)
    sessions_dir = (args.sessions_dir.expanduser() if args.sessions_dir else _default_sessions_dir())
    try:
        if not sessions_dir.is_dir():
            raise RecordError(f"会话记录目录不存在：{sessions_dir}（用 --sessions-dir 指定，或检查 CODEX_HOME）")
        files = sorted(sessions_dir.rglob(f"{_PREFIX}*.jsonl"))
        metas = {p: _read_meta(p) for p in files}
        reports = [_summarize(sid, files, metas, sessions_dir) for sid in args.session_ids]
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
