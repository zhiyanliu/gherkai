#!/usr/bin/env python
"""把一轮同僚复核经 Codex CLI 送出：先检查简报带有让复核循环能停下来的固定标记，通过后以只读沙箱调用 `codex exec`。

用法：
  uv run python tools/codex_review.py --brief <简报> --out <输出文件> [--resume <会话 id>] [--log <日志文件>]
                                      [--model <模型>] [--effort <推理强度>]

  --brief：简报文件。按 UTF-8 读出后检查，开头的 BOM 与非法字节不影响检查；文件内容原样作为 codex 的标准输入。
  --out：codex 写入最后一条消息的文件（codex 的 `-o`）。
  --resume：续接上一轮的会话，值为上一轮日志里 `session id:` 一行的值；不给时开启新会话。
  --log：codex 的 stdout 与 stderr 一并写入的文件，缺省为输出文件路径加 `.log`。
  --model、--effort：传给 codex 的模型（`-m`）与推理强度（`-c model_reasoning_effort`）；不给时不传，沿用 contributor
                     自己的 codex 配置。

检查的两项（docs/ai-eng/peer-review.md 第三节「两处固定标记」）：
  不带 --resume：有一行顶格、以 1 到 6 个 # 加空格开头、含「基准」的标题。
  带 --resume：有一行同时含「趋势」与至少一个数字。
只查有没有，不查写得对不对；经本工具送出的简报一律按复核轮检查，不判断它是不是复核简报。

调用形态（codex 在当前工作目录启动）：
  codex exec -s read-only [-m <模型>] [-c model_reasoning_effort="<强度>"] -o <输出文件> -
  codex exec resume <会话 id> -c sandbox_mode="read-only" [-m <模型>] [-c model_reasoning_effort="<强度>"] -o <输出文件> -
续接子命令没有 `-s`，只读沙箱经 `-c sandbox_mode` 指定。codex 结束后本工具在 stdout 打印两行：日志里 `session id:` 的那一行
（找得到时）与输出文件路径。

退出码：简报读不到、缺少固定标记、日志文件无法写入、PATH 里没有 codex 时为 2，这几种情形 codex 没有被调用；参数用法错误
同为 2；其余情形等于 codex 的退出码，codex 被信号终止时为 128 加信号编号。

不做：不转入后台（需要时由调用方以后台方式执行本工具）、不重试、不判断复核者的上下文占用（见 tools/codex_usage.py）、
不解析输出内容。

为什么经它送出见 ADR 0046 决策 6。
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

_BASELINE = re.compile(r"#{1,6} .*基准")
_NEEDS = {
    False: "基准段：一行顶格、以 # 加空格开头、含「基准」的标题（如「## 基准：受审对象要做到什么」；缩进的标题不算），"
           "标题下写受审对象必须成立的性质",
    True: "趋势：一行同时写出「趋势」与逐轮意见的数目（如「趋势：基准之内的意见 5、3、1 条，逐轮变少、变轻」）",
}
_GUIDE = ("细则见 docs/ai-eng/peer-review.md 第三、四节（两项标记的写法在第三节「两处固定标记」条，趋势怎么看在第四节「每轮送出下一轮之前看趋势」条）；"
          "本会话上下文压缩之后没有读过它的，先读再送。")


def has_mark(text: str, resume: bool) -> bool:
    lines = text.splitlines()  # 两项都按行检查，CR、CRLF、LF 换行的简报结果相同
    if resume:
        return any("趋势" in line and re.search(r"\d", line) for line in lines)
    return any(_BASELINE.match(line) for line in lines)


def codex_args(out: Path, resume: str | None, model: str | None, effort: str | None) -> list[str]:
    if resume is None:
        args = ["codex", "exec", "-s", "read-only"]
    else:
        args = ["codex", "exec", "resume", resume, "-c", 'sandbox_mode="read-only"']
    if model is not None:
        args += ["-m", model]
    if effort is not None:
        args += ["-c", f'model_reasoning_effort="{effort}"']
    return args + ["-o", str(out), "-"]


def _fail(message: str) -> int:
    print(f"codex_review: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="检查复核简报的固定标记，通过后以只读沙箱调用 codex exec")
    ap.add_argument("--brief", type=Path, required=True, help="简报文件，原样作为 codex 的标准输入")
    ap.add_argument("--out", type=Path, required=True, help="codex 写入最后一条消息的文件")
    ap.add_argument("--resume", metavar="会话 id", help="续接上一轮的会话（上一轮日志里 session id: 一行的值）")
    ap.add_argument("--log", type=Path, help="codex 的 stdout 与 stderr 写入的文件，缺省为输出文件路径加 .log")
    ap.add_argument("--model", help="传给 codex 的模型；不给时沿用 codex 自己的配置")
    ap.add_argument("--effort", help="传给 codex 的推理强度；不给时沿用 codex 自己的配置")
    args = ap.parse_args(argv)
    resume = args.resume is not None
    log = args.log if args.log is not None else Path(f"{args.out}.log")

    try:
        brief = args.brief.read_bytes()
    except OSError as exc:
        return _fail(f"简报 {args.brief} 读不到（{exc.strerror or type(exc).__name__}），本轮没有送出。")
    if not has_mark(brief.decode("utf-8-sig", errors="replace"), resume):
        return _fail(f"简报 {args.brief}（{'带' if resume else '不带'} --resume）缺少{_NEEDS[resume]}。"
                     f"本轮没有送出，补上再送。{_GUIDE}")
    if shutil.which("codex") is None:
        return _fail("PATH 里找不到 codex，本轮没有送出。先安装 Codex CLI，或把它所在的目录加进 PATH。")
    try:
        log_file = log.open("wb")
    except OSError as exc:
        return _fail(f"日志文件 {log} 无法写入（{exc.strerror or type(exc).__name__}），本轮没有送出。")
    with log_file:
        proc = subprocess.run(codex_args(args.out, args.resume, args.model, args.effort),
                              input=brief, stdout=log_file, stderr=subprocess.STDOUT)
    session = next((line.strip() for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                    if line.strip().startswith("session id:")), None)
    if session is not None:
        print(session)
    print(args.out)
    return proc.returncode if proc.returncode >= 0 else 128 - proc.returncode


if __name__ == "__main__":
    sys.exit(main())
