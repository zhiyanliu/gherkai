#!/usr/bin/env python
"""把一轮同僚复核经 Codex CLI 送出：先检查简报带有让复核循环能停下来的固定标记，通过后在标准输入末尾附上固定的一段，
以只读沙箱调用 `codex exec`。

用法：
  uv run python tools/codex_review.py --round first|followup --brief <简报> --out <输出文件> [--resume <会话 id>]
                                      [--log <日志文件>] [--model <模型>] [--effort <推理强度>]

  --round：必须给出。first 是新对象的首轮；followup 是同一受审对象的后续轮，续接与换了上下文的都是。
  --brief：简报文件。按 UTF-8 读出后检查，开头的 BOM 与非法字节不影响检查；文件本身不改。
  --out：codex 写入最后一条消息的文件（codex 的 `-o`）。
  --resume：续接上一轮的会话，值为上一轮日志里 `session id:` 一行的值；只能与 --round followup 同用，不给时开启新会话。
  --log：codex 的 stdout 与 stderr 一并写入的文件，缺省为输出文件路径加 `.log`。
  --model、--effort：传给 codex 的模型（`-m`）与推理强度（`-c model_reasoning_effort`）；不给时不传，沿用 contributor
                     自己的 codex 配置。

检查的标记（docs/ai-eng/peer-review.md 第三节「固定标记」条），各项都按行检查：
  基准：有一行顶格、以 1 到 6 个 # 加空格开头、含「基准」的标题。--round first 与不带 --resume 的 --round followup 检查。
  --round followup（带不带 --resume 都一样）另查三项：
    趋势：有一行同时含「趋势」与至少一个数字；
    上轮流程处置：有一行含「上轮流程处置」加冒号（全角或半角），冒号之后接「已闭合」「继续修正」「待取证」「待裁定」「熔断」之一；
    解除依据：上轮流程处置取「待取证」「待裁定」「熔断」时，另有一行含「解除依据」加冒号，且冒号之后有非空白内容。
  这两项的名称都要紧接冒号，名称加粗（`**上轮流程处置**：`）的写法不认，按缺项拦下。上轮流程处置的冒号与取值之间只容空白，
  取值加引号的写法同样不认；解除依据冒号之后的内容不限写法。
只查有没有：不检查重复项的资料，不解析趋势数字的大小，不推断解除依据是否成立；轮次由调用方声明，本工具不核对。
经本工具送出的简报一律按复核轮检查，不判断它是不是复核简报。

交给 codex 的标准输入：简报文件的原始字节，其后是一个空行、一行 `---`、一个空行与固定的附段（APPENDIX）。附段请复核者
先读方法文档第四节里闭合确认、「停下来的原因」与熔断的各条，结尾给出总判定与流程处置；判据只在方法文档里，附段不另抄一份。

调用形态（codex 在当前工作目录启动）：
  codex exec -s read-only [-m <模型>] [-c model_reasoning_effort="<强度>"] -o <输出文件> -
  codex exec resume <会话 id> -c sandbox_mode="read-only" [-m <模型>] [-c model_reasoning_effort="<强度>"] -o <输出文件> -
续接子命令没有 `-s`，只读沙箱经 `-c sandbox_mode` 指定。codex 结束后本工具在 stdout 打印两行：日志里 `session id:` 的那一行
（找得到时）与输出文件路径。

退出码：输出或日志就是简报文件，简报读不到、缺少固定标记、日志文件无法写入、PATH 里没有 codex 时为 2，这几种情形
codex 没有被调用、简报文件也没有被动过；参数用法错误
（含 --resume 与 --round first 同用）同为 2，codex 同样没有被调用；其余情形等于 codex 的退出码，codex 被信号终止时为
128 加信号编号。

不做：不检查输出与日志之间是否重合（重合时后写的盖掉先写的，只影响这一轮的产物）、不转入后台（需要时由调用方以后台方式执行本工具）、不重试、不判断复核者的上下文占用（见 tools/codex_usage.py）、
不从输出或日志判断流程处置、趋势与复核循环是否收敛（日志只用来取 `session id:` 一行）。

为什么经它送出、为什么只查这些标记见 ADR 0046 决策 6。
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

_BASELINE = re.compile(r"#{1,6} .*基准")
DISPOSITIONS = ("已闭合", "继续修正", "待取证", "待裁定", "熔断")
PAUSED = ("待取证", "待裁定", "熔断")  # 暂停类的流程处置，下一轮要写解除依据
_DISPOSITION = re.compile(r"上轮流程处置[:：]\s*(" + "|".join(DISPOSITIONS) + ")")
_RELEASE = re.compile(r"解除依据[:：]\s*\S")
_NEEDS = {
    "baseline": "基准段：一行顶格、以 # 加空格开头、含「基准」的标题（如「## 基准：受审对象要做到什么」；缩进的标题不算），"
                "标题下写受审对象必须成立的性质",
    "trend": "趋势：一行同时写出「趋势」与各轮基准之内的意见条数，括号里注当轮最重的后果"
             "（如「趋势：基准之内 6（误处置活进程）→ 3（同上）→ 1（文档失真）」）",
    "disposition": "上轮流程处置：一行写「上轮流程处置：」，冒号之后抄复核者上一轮的原判，取「已闭合」「继续修正」「待取证」"
                   "「待裁定」「熔断」之一，名称不加粗、取值不加引号（如「上轮流程处置：继续修正」）",
    "release": "解除依据：上轮流程处置是{values}，要另有一行「解除依据：」（名称不加粗），冒号之后写明暂停的原因凭什么已经解除"
               "（如取到的证据、owner 的答复）；还没有解除依据时不送",
}
_GUIDE = ("细则见 docs/ai-eng/peer-review.md 第三、四节：各项标记的写法在第三节「固定标记」条，暂停的原因与解除依据在第四节"
          "「停下来的原因」条，趋势怎么看在第四节「每轮送出下一轮之前看趋势」条；本会话上下文压缩之后没有读过它的，先读再送。")
# 附在交给 codex 的标准输入末尾的一段。熔断等判据只写在方法文档里，这里只请复核者去读，不另抄一份（两份会各自变化）。
APPENDIX = ("（发送工具附加）请在给出结论之前先读 `docs/ai-eng/peer-review.md` 第四节里闭合确认、「停下来的原因」与熔断的各条："
            "同一会话已经读过、文件没有变、此后也没有发生过上下文压缩时可以沿用，发生过压缩的按没读过处理。"
            "结尾给出一句总判定与流程处置，流程处置取「已闭合」「继续修正」「待取证」「待裁定」「熔断」之一，"
            "各值的含义与选择规则以那一节为准；是熔断的写明触发条件、相关轮次、反复失败的性质与恢复之前必须先确定什么。")


def missing_marks(text: str, round_: str, resume: bool) -> list[str]:
    """按轮次返回简报缺少的各项标记的说明（`_NEEDS` 里的文字），齐备时为空表。"""
    lines = text.splitlines()  # 各项都按行检查，CR、CRLF、LF 换行的简报结果相同
    missing = []
    if not resume and not any(_BASELINE.match(line) for line in lines):
        missing.append(_NEEDS["baseline"])
    if round_ == "followup":
        if not any("趋势" in line and re.search(r"\d", line) for line in lines):
            missing.append(_NEEDS["trend"])
        found = {m.group(1) for line in lines for m in _DISPOSITION.finditer(line)}
        paused = [value for value in PAUSED if value in found]
        if not found:
            missing.append(_NEEDS["disposition"])
        elif paused and not any(_RELEASE.search(line) for line in lines):
            missing.append(_NEEDS["release"].format(values="、".join(f"「{value}」" for value in paused)))
    return missing


def with_appendix(brief: bytes) -> bytes:
    """简报的原始字节之后接一个空行、一行 `---`、一个空行与附段。简报不以 LF 结尾时（末尾没有换行，或只用 CR 换行）
    先补一个 LF：只用 CR 换行的简报末尾的 CR 与其后的 LF 合成一个换行，不补的话 `---` 会紧接最后一行、前面没有空行。"""
    end = b"" if brief.endswith(b"\n") else b"\n"
    return brief + end + b"\n---\n\n" + APPENDIX.encode("utf-8") + b"\n"


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


def _is_the_brief(path: Path, brief: Path) -> bool:
    """这个路径此刻是否存在并且就是简报文件（按文件系统判断）。

    简报在送出之前就存在，所以这一条认得全会写到它头上的路径：同一路径、符号链接、硬链接、不区分大小写的文件系统上只差大小写
    的写法，打开它们得到的都是已经存在的那个文件。还不存在的路径不可能是它。"""
    try:
        return path.exists() and path.samefile(brief)
    except OSError:
        return False


def _fail(message: str) -> int:
    print(f"codex_review: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="检查复核简报的固定标记，通过后附上固定的一段、以只读沙箱调用 codex exec")
    ap.add_argument("--round", required=True, choices=("first", "followup"), dest="round_",
                    help="first：新对象的首轮；followup：同一受审对象的后续轮（续接与换了上下文的都是）")
    ap.add_argument("--brief", type=Path, required=True, help="简报文件；检查通过后连同附段作为 codex 的标准输入，文件本身不改")
    ap.add_argument("--out", type=Path, required=True, help="codex 写入最后一条消息的文件")
    ap.add_argument("--resume", metavar="会话 id",
                    help="续接上一轮的会话（上一轮日志里 session id: 一行的值），只能与 --round followup 同用")
    ap.add_argument("--log", type=Path, help="codex 的 stdout 与 stderr 写入的文件，缺省为输出文件路径加 .log")
    ap.add_argument("--model", help="传给 codex 的模型；不给时沿用 codex 自己的配置")
    ap.add_argument("--effort", help="传给 codex 的推理强度；不给时沿用 codex 自己的配置")
    args = ap.parse_args(argv)
    resume = args.resume is not None
    if resume and args.round_ != "followup":
        ap.error("--resume 只能与 --round followup 同用：续接的是同一受审对象上一轮的会话，新对象的首轮用全新会话")
    log = args.log if args.log is not None else Path(f"{args.out}.log")
    # 输出与日志都会被写入，哪一个就是简报文件，简报就被覆盖：写任何文件之前先拦下。只保护简报这一个文件，输出与日志之间是否
    # 重合不检查：两者都是这一轮要新写的，重合只影响这一轮自己的产物；要认全两个还不存在的路径是否重合，得去推断文件系统的性质。
    for name, path in (("输出", args.out), ("日志", log)):
        if _is_the_brief(path, args.brief):
            return _fail(f"{name} {path} 就是简报文件，写入会覆盖简报，本轮没有送出。给{name}换一个路径。")

    try:
        brief = args.brief.read_bytes()
    except OSError as exc:
        return _fail(f"简报 {args.brief} 读不到（{exc.strerror or type(exc).__name__}），本轮没有送出。")
    missing = missing_marks(brief.decode("utf-8-sig", errors="replace"), args.round_, resume)
    if missing:
        kind = f"--round {args.round_}" + ("" if args.round_ == "first" else f"，{'带' if resume else '不带'} --resume")
        items = "".join(f"\n  - {item}" for item in missing)
        return _fail(f"简报 {args.brief}（{kind}）缺少下列标记，本轮没有送出，补上再送：{items}\n{_GUIDE}")
    if shutil.which("codex") is None:
        return _fail("PATH 里找不到 codex，本轮没有送出。先安装 Codex CLI，或把它所在的目录加进 PATH。")
    try:
        log_file = log.open("wb")
    except OSError as exc:
        return _fail(f"日志文件 {log} 无法写入（{exc.strerror or type(exc).__name__}），本轮没有送出。")
    with log_file:
        proc = subprocess.run(codex_args(args.out, args.resume, args.model, args.effort),
                              input=with_appendix(brief), stdout=log_file, stderr=subprocess.STDOUT)
    session = next((line.strip() for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                    if line.strip().startswith("session id:")), None)
    if session is not None:
        print(session)
    print(args.out)
    return proc.returncode if proc.returncode >= 0 else 128 - proc.returncode


if __name__ == "__main__":
    sys.exit(main())
