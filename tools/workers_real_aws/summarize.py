"""汇总装置的结果 jsonl：各阶段结果计数、装置记下的问题（种类同 PROBLEM_KINDS）与会话退出码、失败用例与失败信息末尾几行、
预期失败与跳过的原因、观察行，末尾给适配、建表与收尾的统计。

用法：python tools/workers_real_aws/summarize.py <结果 jsonl> [--lines N]
  --lines：每个失败用例打印的失败信息末尾行数（缺省 12）。结果文件保存完整的失败信息，异常的原因在末尾；更早的行只注明
  略去了几行，要看全文直接读结果文件里那一行的 longrepr。

判读：第一行是（阶段, 结果）的计数，call 阶段之外出现 failed 说明夹具或收尾出了问题。紧接着的「需要处理」一节列出装置
记下的问题，它们与用例的通过与否无关：不为「无」时，真实账户里可能留有资源，先按 README.md「清扫残留」节清一次；参与方
线程残留时会话已被终止，其后的用例没有执行。装置来不及记下的三种情形由本脚本从结果文件推出、同样列在这一节：会话没有
正常结束（某次会话的 session_start 之后没有它的 session_finish，例如 thread 方式的超时直接终止了进程）、收尾没有完成（真实
账户模式的代码路径下，用例有 prefix 一行、却没有同一用例同一前缀的 teardown 或 teardown_interrupted 一行），与结果文件有
一个对象没有写完（进程在写它时被终止）。没有写完的部分只在它确实是一个 JSON 对象的开头（逐字符判断再追加字符能否成为
合法的 JSON）、且其后是文件末尾或紧接着下一次会话的一个 session_start 时才认作这种情形：前者列为最后一行没有完整写入；
后者是同一路径之后又有会话追加，列为中途有一行没有完整写入（conftest 现在追加之前先补换行，session_start 在下一行开头；
较早写出的结果文件里它接在这半行后面、同在一行）。两者都略去没有写完的部分、其余照常汇总。同一行里缺换行而连在一起的完整对象都照常
读入。结果文件里有多次会话时（同一路径逐次追加），记录按 session_start 分段，每次会话各自判断模式与完成状态，「需要处理」
的各条与会话退出码都注明第几个会话；只有一次会话时不标。其它不是完整 JSON 对象的内容一律报错并指出行号、退出码为 1。
各 kind 的含义见 README.md「读结果」节。只读文件、不联网。
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

# 与 conftest.py 的 PROBLEM_KINDS 相同：本文件只读结果文件、不导入装置
PROBLEM_KINDS = {"teardown_failure": "收尾失败", "teardown_interrupted": "清理被中断", "residue": "同前缀残留",
                 "lingering_party_threads": "参与方线程残留", "copy_request_mismatch": "复制请求与模板不符"}

OBSERVATION_KINDS = (
    "harness", "step", "index_creating_observation", "index_became_active", "index_active_pass",
    "table_missing_observation", "register_response_registeredAt", "describe_lineage_registeredAt",
    "waited_for_table_deletion",
)


def _short(name: str) -> str:
    return name.split("::")[-1]


class BadLine(ValueError):
    """结果文件的一行不是被终止的会话可能留下的形态。"""

    def __init__(self, lineno: int, cause: str):
        super().__init__(f"结果文件第 {lineno} 行不是完整的 JSON 对象（{cause}）；进程被终止时没有写完的只可能是一个 JSON "
                         "对象的开头，且它要么在文件末尾，要么后面紧接着下一次会话的 session_start，这一行不属于这两种情形")
        self.lineno = lineno


# conftest.record 写出的每一行都以 kind 开头；一次会话的第一行以此开头
_SESSION_START = '{"kind": "session_start"'
_DECODER = json.JSONDecoder()
_WHITESPACE = " \t\r\n"
# conftest.record 用 json.dumps 的缺省设置写出，浮点的 nan 与 inf 写成 NaN、Infinity、-Infinity，json 模块读入时同样接受
_LITERALS = ("true", "false", "null", "NaN", "Infinity")
_NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
# 再追加字符有可能成为合法数字的串：-、整数部分（可带 . 与小数位）、或带完整小数位之后的指数部分（指数位可为空）
_NUMBER_PREFIX = re.compile(r"-|-?(?:0|[1-9]\d*)(?:\.\d*)?|-?(?:0|[1-9]\d*)(?:\.\d+)?[eE][+-]?\d*")
# 截断的多字节字符（surrogateescape 解码之后是 U+DC80 到 U+DCFF 的孤立代理）
_ESCAPED_BYTE = re.compile("[\udc80-\udcff]")
_UTF8_SECOND = {**dict.fromkeys(range(0xC2, 0xE0), (0x80, 0xBF)), 0xE0: (0xA0, 0xBF),
                **dict.fromkeys(range(0xE1, 0xED), (0x80, 0xBF)), 0xED: (0x80, 0x9F),
                **dict.fromkeys(range(0xEE, 0xF0), (0x80, 0xBF)), 0xF0: (0x90, 0xBF),
                **dict.fromkeys(range(0xF1, 0xF4), (0x80, 0xBF)), 0xF4: (0x80, 0x8F)}


def _utf8_char_prefix(data: bytes) -> bool:
    """data 是否是某个 UTF-8 多字节字符的编码去掉末尾若干字节之后剩下的开头（至少缺一个字节）。"""
    if not data or data[0] not in _UTF8_SECOND:
        return False
    need = 2 if data[0] < 0xE0 else 3 if data[0] < 0xF0 else 4
    if len(data) >= need:
        return False
    if len(data) > 1:
        low, high = _UTF8_SECOND[data[0]]
        if not low <= data[1] <= high or any(not 0x80 <= b <= 0xBF for b in data[2:]):
            return False
    return True


def _scan_string(text: str, i: int) -> tuple[int, str]:
    """text[i] 是左引号：返回（字符串之后的位置，"closed"）；到 text 末尾仍未闭合时返回（len(text)，"open" 或 "escape"，
    后者表示停在转义序列中间）；字符串里出现 JSON 不允许的内容时返回（i，"bad"）。"""
    j, n = i + 1, len(text)
    while j < n:
        c = text[j]
        if c == '"':
            return j + 1, "closed"
        if c == "\\":
            if j + 1 == n:
                return n, "escape"
            e = text[j + 1]
            if e in '"\\/bfnrt':
                j += 2
                continue
            if e != "u":
                return i, "bad"
            digits = text[j + 2:j + 6]
            if any(d not in "0123456789abcdefABCDEF" for d in digits):
                return i, "bad"
            if len(digits) < 4:
                return n, "escape"
            j += 6
            continue
        if ord(c) < 0x20 or "\ud800" <= c <= "\udfff":
            return i, "bad"
        j += 1
    return n, "open"


def _unfinished_object(text: str) -> bool:
    """text 是否是一个 JSON 对象没有写完的开头：再追加字符有可能成为合法的 JSON 对象。逐字符按字符串、转义、括号栈与
    字面量（数字、true / false / null，与 json 模块写出的 NaN / Infinity / -Infinity，见 `_LITERALS`）的前缀判断；对象已经闭合的不算没有写完。末尾被截断的多字节字符只允许出现在字符串
    里、且须是某个 UTF-8 字符编码的开头；别处不是合法 UTF-8 的字节一律不算。"""
    cut = len(text)
    while cut and "\udc80" <= text[cut - 1] <= "\udcff":
        cut -= 1
    head, partial = text[:cut], text[cut:]
    if partial and not _utf8_char_prefix(bytes(ord(c) - 0xDC00 for c in partial)):
        return False
    stack: list[str] = []
    expect = "object"   # 下一个记号：object（只能是 {）、value、value_or_close、key、key_or_close、colon、comma_or_close
    tail = "token"      # 走到末尾时停在什么之中：token（两个记号之间）、string、escape、number、literal
    i, n = 0, len(head)
    while i < n:
        c = head[i]
        if c in _WHITESPACE:
            i += 1
            continue
        closer = {"{": "}", "[": "]"}.get(stack[-1]) if stack else None
        if expect in ("comma_or_close", "key_or_close", "value_or_close") and c == closer:
            stack.pop()
            if not stack:
                return False   # 对象已经闭合：不是没有写完的开头（其后也不能再有字符）
            expect, i = "comma_or_close", i + 1
            continue
        if expect == "comma_or_close":
            if c != ",":
                return False
            expect, i = ("key" if closer == "}" else "value"), i + 1
        elif expect == "colon":
            if c != ":":
                return False
            expect, i = "value", i + 1
        elif expect in ("key", "key_or_close"):
            if c != '"':
                return False
            i, state = _scan_string(head, i)
            if state == "bad":
                return False
            expect, tail = "colon", ("token" if state == "closed" else "string" if state == "open" else "escape")
        elif expect == "object":
            if c != "{":
                return False
            stack.append("{")
            expect, i = "key_or_close", i + 1
        else:   # value 或 value_or_close
            if c in "{[":
                stack.append(c)
                expect, i = ("key_or_close" if c == "{" else "value_or_close"), i + 1
            elif c == '"':
                i, state = _scan_string(head, i)
                if state == "bad":
                    return False
                expect, tail = "comma_or_close", ("token" if state == "closed" else "string" if state == "open"
                                                  else "escape")
            elif c.isalpha() or (c == "-" and head[i + 1:i + 2].isalpha()):
                j = i + 1
                while j < n and head[j].isalpha():
                    j += 1
                token = head[i:j]
                words = ("-Infinity",) if c == "-" else _LITERALS
                if not (any(w.startswith(token) for w in words) if j == n else token in words):
                    return False
                expect, i, tail = "comma_or_close", j, ("literal" if j == n else "token")
            elif c in "-0123456789":
                j = i
                while j < n and head[j] in "0123456789+-.eE":
                    j += 1
                token = head[i:j]
                if not (_NUMBER_PREFIX if j == n else _NUMBER).fullmatch(token):
                    return False
                expect, i, tail = "comma_or_close", j, ("number" if j == n else "token")
            else:
                return False
    if not stack:
        return False   # 空串或只有空白
    return tail == "string" if partial else True


def _complete_objects(text: str) -> tuple[list[dict], str]:
    """从 text 开头依次解析尽可能多的完整 JSON 对象（缺换行而连在一起的也逐个取出），返回（这些对象，剩下的部分）。
    完整的值不是对象、或含有不是合法 UTF-8 的字节时抛 ValueError。"""
    rows: list[dict] = []
    pos = 0
    while True:
        while pos < len(text) and text[pos] in _WHITESPACE:
            pos += 1
        if pos == len(text):
            return rows, ""
        try:
            row, end = _DECODER.raw_decode(text, pos)
        except json.JSONDecodeError:
            return rows, text[pos:]
        if not isinstance(row, dict):
            raise ValueError("不是 JSON 对象")
        if _ESCAPED_BYTE.search(text, pos, end):
            raise ValueError("含有不是合法 UTF-8 的字节")
        rows.append(row)
        pos = end


def _starts_session(text: str, *, last: bool) -> bool:
    """text 是否以下一次会话的 session_start 开头：一个完整的 session_start 对象，或（text 在文件末尾时）一个没有写完的
    session_start。"""
    try:
        rows, rest = _complete_objects(text)
    except ValueError:
        return False
    if rows:
        return rows[0].get("kind") == "session_start"
    return last and rest.startswith(_SESSION_START) and _unfinished_object(rest)


def _parse_line(text: str, *, last: bool, next_starts_session: bool) -> tuple[list[dict], list[str]]:
    """一行里的记录与其中没有写完的对象：返回（完整的记录，形态列表）。形态 "cut" 是一个没有写完的对象、其后紧接着下一次
    会话的 session_start（同一行里，或这一行到此为止、下一行以它开头）；"truncated" 是文件最后一行末尾没有写完的对象。
    last：这是文件的最后一行；next_starts_session：下一行以 session_start 开头。其它形态抛 ValueError。"""
    rows: list[dict] = []
    shapes: list[str] = []
    while True:
        got, rest = _complete_objects(text)
        rows += got
        if not rest:
            return rows, shapes
        at = rest.find(_SESSION_START, 1)
        while at > 0 and not (_unfinished_object(rest[:at]) and _starts_session(rest[at:], last=last)):
            at = rest.find(_SESSION_START, at + 1)
        if at > 0:
            shapes.append("cut")
            text = rest[at:]
            continue
        if _unfinished_object(rest) and (last or next_starts_session):
            shapes.append("truncated" if last else "cut")
            return rows, shapes
        raise ValueError("剩下的部分不是一个没有写完的 JSON 对象，或它后面接着的不是下一次会话的 session_start")


def load(path: Path) -> tuple[list[dict], int | None, list[int]]:
    """读结果文件，返回（完整的记录，最后一行末尾的对象没有写完时它的行号、否则 None，有一个对象没有写完、其后紧接着下一次
    会话 session_start 的各行行号）。

    一行里缺换行而连在一起的完整对象都保留。进程被直接终止时它写的最后一个对象可能只写了一半（含被截断的多字节字符）：
    没有写完的部分确实是一个 JSON 对象的开头（见 `_unfinished_object`），且其后是文件的末尾，或紧接着下一次会话的一个
    session_start（旧形态的结果文件里接在同一行；conftest 现在追加之前先补换行，它在下一行开头）时，略去这一部分、其余照常
    读入。其它形态一律抛 BadLine，指出行号。空行（只含 JSON 允许的空白：空格、制表符、回车、换行）略去；只含其它空白字符
    （如垂直制表符、换页符）的行不是空行，照坏行处理。
    结果文件按 LF 切行。被外部工具转成 CRLF 行尾的文件里，完整的行照常读入（行尾的回车是 JSON 允许的空白），截断在字符串
    中间的半行却会按坏行报错：留在行尾的回车落进了没有写完的字符串，字符串里不允许出现未转义的控制字符。"""
    numbered = [(i, line.decode("utf-8", "surrogateescape"))
                for i, line in enumerate(path.read_bytes().split(b"\n"), 1) if line.strip(_WHITESPACE.encode())]
    rows: list[dict] = []
    joined: list[int] = []
    truncated: int | None = None
    for pos, (lineno, text) in enumerate(numbered):
        last = pos == len(numbered) - 1
        following = not last and _starts_session(numbered[pos + 1][1], last=pos + 1 == len(numbered) - 1)
        try:
            got, shapes = _parse_line(text, last=last, next_starts_session=following)
        except ValueError as exc:
            raise BadLine(lineno, str(exc)) from None
        rows += got
        if "cut" in shapes:
            joined.append(lineno)
        if "truncated" in shapes:
            truncated = lineno
    return rows, truncated, joined


def _sessions(rows: list[dict]) -> list[tuple[int, list[dict]]]:
    """按 session_start 把记录分段：每段从一行 session_start 起、到下一行 session_start 之前，编号从 1 起。第一行
    session_start 之前若有记录（装置不会这样写），单独成一段、编号 0。"""
    segments: list[tuple[int, list[dict]]] = []
    current: list[dict] = []
    number = 0
    for x in rows:
        if x.get("kind") == "session_start":
            if current:
                segments.append((number, current))
            number += 1
            current = [x]
        else:
            current.append(x)
    if current:
        segments.append((number, current))
    return segments


def _unfinished_teardowns(rows: list[dict]) -> list[dict]:
    """一次会话里，真实账户模式的代码路径下，有 prefix 一行、却没有同一用例同一前缀的 teardown 或 teardown_interrupted
    一行的用例：收尾没有执行到底，装置也来不及记下（例如进程被直接终止）。纯 moto 模式不记 teardown 行，不在此列。
    rows 只取一次会话的记录（见 `_sessions`）：模式与完成状态都按会话判断，别的会话不会遮掉或误报它。"""
    if not any(x.get("kind") == "harness" and (x.get("mode") == "real" or x.get("force_real_paths")) for x in rows):
        return []
    done = {(x.get("nodeid"), x.get("prefix")) for x in rows if x.get("kind") in ("teardown", "teardown_interrupted")}
    return [x for x in rows if x.get("kind") == "prefix" and (x.get("nodeid"), x.get("prefix")) not in done]


def _token(segment: list[dict]) -> str:
    start = segment[0] if segment and segment[0].get("kind") == "session_start" else {}
    return str((start.get("env") or {}).get("GKP_TOKEN") or "-")


def summarize(rows: list[dict], *, lines: int = 12, out=sys.stdout, truncated_line: int | None = None,
              joined_lines: list[int] = ()) -> None:
    """truncated_line：结果文件最后一行末尾的一个对象没有写完时它的行号；joined_lines：有一个对象没有写完、其后紧接着下一次
    会话 session_start 的各行行号（都见 `load`）。两者都列进「需要处理」。"""
    def emit(text: str = "") -> None:
        print(text, file=out)

    tests = [x for x in rows if x.get("kind") == "test"]
    emit(str(dict(collections.Counter((x.get("phase"), x.get("outcome")) for x in tests))))
    segments = _sessions(rows)
    multi = len(segments) > 1   # 只有一次会话时不标会话序号，输出与按整个文件判断时相同
    problems, unfinished, not_ended, finishes = [], [], [], []
    for number, segment in segments:
        tag = f"第 {number} 个会话 " if multi else ""
        problems += [(tag, x) for x in segment if x.get("kind") in PROBLEM_KINDS]
        unfinished += [(tag, x) for x in _unfinished_teardowns(segment)]
        finish = next((x for x in segment if x.get("kind") == "session_finish"), None)
        finishes.append((number, finish.get("exitstatus") if finish else None))
        if finish is None and segment[0].get("kind") == "session_start":
            not_ended.append((number, _token(segment)))
    counts = collections.Counter(PROBLEM_KINDS[x["kind"]] for _, x in problems)
    items = [f"{name} {n} 条" for name, n in counts.items()]
    if unfinished:
        items.append(f"收尾没有完成 {len(unfinished)} 条")
    if not_ended:
        items.append(f"会话没有正常结束 {len(not_ended)} 次")
    if truncated_line is not None:
        items.append("结果文件最后一行没有完整写入")
    if joined_lines:
        items.append(f"结果文件中途有 {len(joined_lines)} 行没有完整写入")
    emit("需要处理：" + ("、".join(items) if items else "无"))
    for tag, x in problems:
        detail = {k: str(v)[:200] for k, v in x.items() if k not in ("kind", "ts", "nodeid")}
        emit(f"  {PROBLEM_KINDS[x['kind']]} {tag}{_short(x.get('nodeid') or '-')} {detail}")
    for tag, x in unfinished:
        emit(f"  收尾没有完成 {tag}{_short(x.get('nodeid') or '-')} {{'prefix': {x.get('prefix')!r}}}")
    if not_ended and not multi:
        emit("  会话没有正常结束：结果文件里 session_finish 少于 session_start（例如 thread 方式的超时直接终止了进程），"
             "收尾与结果文件都可能不完整")
    for number, token in (not_ended if multi else []):
        emit(f"  会话没有正常结束 第 {number} 个会话（令牌 {token}）：没有 session_finish 一行（例如 thread 方式的超时"
             "直接终止了进程），收尾与结果文件都可能不完整")
    if truncated_line is not None:
        emit(f"  结果文件最后一行没有完整写入：第 {truncated_line} 行末尾的一个对象只写了一部分（进程在写它时被终止），"
             "会话没有正常结束；以下按它之前的完整记录汇总")
    for lineno in joined_lines:
        emit(f"  结果文件中途有一行没有完整写入：第 {lineno} 行里有上一次会话没有写完的一个对象（进程在写它时被终止），"
             "其后紧接着下一次会话的 session_start；没有写完的部分略去，其余照常汇总")
    if multi:
        emit("会话退出码 " + "，".join(f"第 {n} 个会话 {code if code is not None else '没有 session_finish 一行'}"
                                     for n, code in finishes))
    else:
        codes = [code for _, code in finishes if code is not None]
        emit(f"会话退出码 {codes if codes else '没有 session_finish 一行（会话没有正常结束）'}")
    for x in rows:
        kind = x.get("kind")
        if kind == "test" and x.get("outcome") == "failed":
            emit(f"FAILED {_short(x['nodeid'])} [{x.get('phase')}]")
            text = (x.get("longrepr") or "").splitlines()
            if len(text) > lines:
                emit(f"    （略去前 {len(text) - lines} 行）")
            emit("    " + "\n    ".join(text[-lines:]))
        elif kind == "test" and x.get("phase") == "call" and x.get("xfail_reason"):
            emit(f"XFAIL {_short(x['nodeid'])}: {str(x['xfail_reason'])[:300]}")
        elif kind == "test" and x.get("outcome") == "skipped" and x.get("skip_reason"):
            emit(f"SKIP {_short(x['nodeid'])} [{x.get('phase')}]: {str(x['skip_reason'])[:300]}")
        elif kind and (kind.startswith("obs_") or kind in OBSERVATION_KINDS):
            emit(f"{kind} " + str({k: str(v)[:400] for k, v in x.items() if k not in ("kind", "ts")}))
    emit("adaptations " + str(dict(collections.Counter(tuple(x["changes"]) for x in rows
                                                        if x.get("kind") == "adaptation"))))
    built = [x["seconds"] for x in rows if x.get("kind") == "lazy_table_built"]
    emit(f"tables built {len(built)} seconds {(round(min(built), 1), round(max(built), 1)) if built else None}")
    teardowns = [x for x in rows if x.get("kind") == "teardown"]
    emit(f"teardowns {len(teardowns)} with failures {sum(1 for x in teardowns if x.get('failures'))}"
         f" skipped {sum(1 for x in teardowns if x.get('skipped'))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="汇总 worker 镜像交付测试真实账户装置的结果 jsonl")
    parser.add_argument("results", type=Path, help="结果 jsonl 的路径")
    parser.add_argument("--lines", type=int, default=12, help="每个失败用例打印的失败信息末尾行数（缺省 12）")
    ns = parser.parse_args(argv)
    try:
        rows, truncated, joined = load(ns.results)
    except BadLine as exc:
        print(exc, file=sys.stderr)
        return 1
    summarize(rows, lines=ns.lines, truncated_line=truncated, joined_lines=joined)
    return 0


if __name__ == "__main__":
    sys.exit(main())
