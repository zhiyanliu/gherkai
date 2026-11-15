"""`tools/codex_review.py` 的单测（ADR 0046 决策 6）：每种轮次的必备标记缺一项、简报读不到或参数用法错误（含 --resume 与
--round first 同用）时 codex 一次都不被调用、退出码 2、提示点名缺的项；通过时传给 codex 的参数与两种调用形态逐项一致，
标准输入是简报全文加固定的附段而简报文件不变，日志落在指定文件，退出码原样传回。

用子进程执行工具；替身 codex 放在临时目录、经 PATH 排在最前面，它记下收到的参数与标准输入，按 `-o` 写出输出文件，
往 stdout 打印一行 `session id:`、往 stderr 打印一行，再按环境变量给出的退出码结束。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from _doc_rules import REPO

TOOL = REPO / "tools" / "codex_review.py"
METHOD_DOC = REPO / "docs" / "ai-eng" / "peer-review.md"

BAD = "# 复核简报\n\n请复核下面的改动，结尾一句总判定。\n"
GOOD_FIRST = "# 复核简报\n\n## 基准：受审对象要做到什么\n\n- 性质一\n"
TREND = "趋势：基准之内 6（误处置活进程）→ 3（同上）→ 1（文档失真）\n"
DISPOSITION = "上轮流程处置：继续修正\n"
GOOD_RESUME = "闭合轮：上一轮意见是否处置到位。\n\n" + TREND + DISPOSITION
GOOD_FOLLOWUP = GOOD_FIRST + TREND + DISPOSITION  # 换了上下文的后续轮：基准加后续轮的标记
RELEASE = "解除依据：取到了真实进程的日志\n"
# 三种轮次在命令行上的写法：新对象的首轮、换了上下文的后续轮、续接的后续轮。
ROUND_ARGS = {
    "first": ("--round", "first"),
    "fresh": ("--round", "followup"),
    "resume": ("--round", "followup", "--resume", "sid"),
}
# owner 批准的附段原文：在这里另写一份，附段的文字被改动时这里的断言失败。
APPENDIX = ("（发送工具附加）请在给出结论之前先读 `docs/ai-eng/peer-review.md` 第四节里闭合确认、「停下来的原因」与熔断的各条："
            "同一会话已经读过、文件没有变、此后也没有发生过上下文压缩时可以沿用，发生过压缩的按没读过处理。"
            "结尾给出一句总判定与流程处置，流程处置取「已闭合」「继续修正」「待取证」「待裁定」「熔断」之一，"
            "各值的含义与选择规则以那一节为准；是熔断的写明触发条件、相关轮次、反复失败的性质与恢复之前必须先确定什么。")


def _stdin_for(brief: bytes) -> bytes:
    """交给 codex 的标准输入应有的字节：以 LF 结尾的简报原文、一个空行、一行 `---`、一个空行、附段。"""
    return brief + b"\n---\n\n" + APPENDIX.encode("utf-8") + b"\n"


FAKE_CODEX = """\
import json, os, signal, sys
args = sys.argv[1:]
data = sys.stdin.buffer.read()
with open(os.environ["FAKE_CODEX_RECORD"], "w", encoding="utf-8") as f:
    json.dump({"args": args, "stdin": data.decode("latin-1")}, f)
if "-o" in args:
    with open(args[args.index("-o") + 1], "w", encoding="utf-8") as f:
        f.write("复核意见\\n")
if os.environ.get("FAKE_CODEX_SESSION", "1") == "1":
    print("session id: 0199-abc")
print("替身 codex 的 stderr", file=sys.stderr)
sys.stdout.flush()
if os.environ.get("FAKE_CODEX_SIGNAL"):
    os.kill(os.getpid(), signal.SIGTERM)
sys.exit(int(os.environ.get("FAKE_CODEX_RC", "0")))
"""


@pytest.fixture
def env(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "codex"
    fake.write_text(f"#!{sys.executable}\n{FAKE_CODEX}", encoding="utf-8")
    fake.chmod(0o755)
    return {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            "FAKE_CODEX_RECORD": str(tmp_path / "record.json")}


def _brief(tmp_path: Path, text: str | bytes) -> Path:
    path = tmp_path / "brief.md"
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


def _run(env: dict, *args: str, **extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args], env={**env, **extra}, capture_output=True, text=True)


def _record(tmp_path: Path) -> dict | None:
    path = tmp_path / "record.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@pytest.mark.parametrize(("text", "mode", "passes"), [
    # 新对象的首轮：只查基准
    (GOOD_FIRST, "first", True),
    (BAD, "first", False),
    (TREND + DISPOSITION, "first", False),                 # 后续轮的标记代替不了基准
    # 换了上下文的后续轮：基准加后续轮的标记
    (GOOD_FOLLOWUP, "fresh", True),
    (GOOD_FIRST, "fresh", False),                          # 只有基准
    (TREND + DISPOSITION, "fresh", False),                 # 没有基准
    (GOOD_FIRST + DISPOSITION, "fresh", False),            # 缺趋势
    (GOOD_FIRST + TREND, "fresh", False),                  # 缺上轮流程处置
    # 续接的后续轮：只查后续轮的标记
    (GOOD_RESUME, "resume", True),
    (TREND + DISPOSITION, "resume", True),                 # 不要求基准
    (GOOD_FOLLOWUP, "resume", True),
    (BAD, "resume", False),
    (GOOD_FIRST, "resume", False),                         # 只有基准
    (DISPOSITION, "resume", False),                        # 缺趋势
    (TREND, "resume", False),                              # 缺上轮流程处置
    (TREND + "上轮流程处置：继续修正\n上轮流程处置：熔断\n", "resume", False),  # 任一行取暂停类的值即要解除依据
    # 基准标题的形态（首轮）
    ("# 基准\n", "first", True),
    ("###### 基准\n", "first", True),
    ("####### 基准\n", "first", False),                    # 七个井号不是标题
    ("##基准\n", "first", False),                          # 井号后没有空格
    ("  ## 基准\n", "first", False),                       # 不在行首
    ("基准：受审对象要做到什么\n", "first", False),        # 不是标题
    ("## 受审对象\n\n正文提到基准\n", "first", False),
    ("\ufeff## 基准\n", "first", True),                    # 文件开头的 BOM 不影响首行标题
    ("复核简报\r## 基准\r", "first", True),                # 只用 CR 换行：标题在行首，算有
    ("# 复核简报\r正文提到基准\r", "first", False),        # 只用 CR 换行：基准不在标题行里，算缺
    ("# 复核简报\r\n## 基准\r\n", "first", True),          # CRLF 换行
    ("## 基准\r" + TREND.replace("\n", "\r") + DISPOSITION.replace("\n", "\r"), "fresh", True),  # 后续轮的标记同样按行检查
    # 趋势一行的形态（续接，上轮流程处置齐备）
    ("趋势：意见逐轮变少\n" + DISPOSITION, "resume", False),            # 趋势一行没有数字
    ("趋势：意见逐轮变少\n第 3 轮\n" + DISPOSITION, "resume", False),   # 数字不在同一行
    ("上一轮 3 条意见，本轮 1 条：趋势收敛\n" + DISPOSITION, "resume", True),
    # 条数没有下降照样放行：工具只查标记在不在，不按数字判断是否收敛
    ("趋势：基准之内 3（错误处置活进程）→ 3（文档失真）\n" + DISPOSITION, "resume", True),
    ("趋势：基准之内 2（文档失真）→ 3（错误处置活进程）\n" + DISPOSITION, "resume", True),
    # 解除依据冒号之后的内容不限写法，带引号也算有
    (TREND + "上轮流程处置：熔断\n解除依据：「owner 已答复」\n", "resume", True),
    ("普通任务，请写一个函数。\n", "first", False),        # 不判断是不是复核简报，一律检查
])
def test_marks_by_round_decide_whether_codex_is_called(tmp_path, env, text, mode, passes):
    brief = _brief(tmp_path, text)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS[mode], "--brief", str(brief), "--out", str(out))
    assert proc.returncode == (0 if passes else 2), proc.stderr
    assert (_record(tmp_path) is not None) == passes
    assert Path(f"{out}.log").exists() == passes


@pytest.mark.parametrize("value", ["已闭合", "继续修正", "待取证", "待裁定", "熔断"])
@pytest.mark.parametrize("mode", ["fresh", "resume"])
def test_each_of_the_five_dispositions_is_accepted(tmp_path, env, value, mode):
    brief = _brief(tmp_path, GOOD_FIRST + TREND + f"上轮流程处置：{value}\n" + RELEASE)
    proc = _run(env, *ROUND_ARGS[mode], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path) is not None


@pytest.mark.parametrize("line", [
    "上轮流程处置：尚未闭合",                              # 不是五个取值之一
    "上轮流程处置：尚不能确认收敛",
    "上轮流程处置：闭合",
    "上轮流程处置 继续修正",                               # 没有冒号
    "上轮流程处置继续修正",
    "上轮流程处置：",                                      # 冒号之后为空
    "上轮流程处置：复核者判为继续修正",                    # 冒号之后接的不是取值
    "流程处置：继续修正",                                  # 不是「上轮流程处置」
    "本轮流程处置：继续修正",
    "**上轮流程处置**：继续修正",                          # 名称加粗：名称与冒号之间夹了符号，不认
    "上轮流程处置：「继续修正」",                          # 取值加引号，不认
])
def test_disposition_line_is_the_name_a_colon_and_one_of_the_values(tmp_path, env, line):
    brief = _brief(tmp_path, TREND + line + "\n")
    proc = _run(env, *ROUND_ARGS["resume"], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 2 and _record(tmp_path) is None
    assert "\n  - 上轮流程处置：" in proc.stderr and "名称不加粗、取值不加引号" in proc.stderr


@pytest.mark.parametrize(("value", "needs_release"), [
    ("已闭合", False), ("继续修正", False), ("待取证", True), ("待裁定", True), ("熔断", True),
])
@pytest.mark.parametrize("mode", ["fresh", "resume"])
def test_paused_dispositions_need_a_release_line(tmp_path, env, value, needs_release, mode):
    brief = _brief(tmp_path, GOOD_FIRST + TREND + f"上轮流程处置：{value}\n")
    proc = _run(env, *ROUND_ARGS[mode], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == (2 if needs_release else 0), proc.stderr
    assert (_record(tmp_path) is None) == needs_release
    if needs_release:
        assert f"\n  - 解除依据：上轮流程处置是「{value}」" in proc.stderr


@pytest.mark.parametrize(("release", "passes"), [
    ("解除依据：取到了真实进程的日志", True),
    ("- 解除依据：owner 定下了信任边界", True),
    ("解除依据：已通知、仍待答复", True),                  # 解除依据是否成立不由工具判断
    ("解除依据：", False),                                 # 冒号之后为空
    ("解除依据：   ", False),                              # 冒号之后只有空白
    ("解除依据：\u3000\t", False),                         # 全角空格与制表符也是空白
    ("解除依据：\n取到了真实进程的日志", False),           # 内容在下一行，不算
    ("解除依据", False),                                   # 没有冒号
    ("解除依据 取到了真实进程的日志", False),
    ("解除的依据：取到了真实进程的日志", False),           # 不是「解除依据」
    ("**解除依据**：取到了真实进程的日志", False),         # 名称加粗，不认
])
def test_release_line_needs_content_after_the_colon(tmp_path, env, release, passes):
    brief = _brief(tmp_path, TREND + "上轮流程处置：熔断\n" + release + "\n")
    proc = _run(env, *ROUND_ARGS["resume"], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == (0 if passes else 2), proc.stderr
    assert (_record(tmp_path) is not None) == passes


@pytest.mark.parametrize("disposition_colon", ["：", ":", ": "])
@pytest.mark.parametrize("release_colon", ["：", ":", ": "])
def test_full_width_and_half_width_colons_are_both_accepted(tmp_path, env, disposition_colon, release_colon):
    brief = _brief(tmp_path, TREND + f"上轮流程处置{disposition_colon}熔断\n解除依据{release_colon}owner 已答复\n")
    proc = _run(env, *ROUND_ARGS["resume"], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 0, proc.stderr


def test_resume_with_first_round_is_a_usage_error(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FOLLOWUP)  # 标记齐备，拦下它的只是轮次与 --resume 不相容
    out = tmp_path / "out.md"
    proc = _run(env, "--round", "first", "--resume", "sid", "--brief", str(brief), "--out", str(out))
    assert proc.returncode == 2 and proc.stdout == ""
    assert "--resume 只能与 --round followup 同用" in proc.stderr
    assert _record(tmp_path) is None and not Path(f"{out}.log").exists()


@pytest.mark.parametrize("round_args", [(), ("--round", "second"), ("--round", "resume"), ("--round",)])
def test_round_must_be_first_or_followup(tmp_path, env, round_args):
    brief = _brief(tmp_path, GOOD_FOLLOWUP)
    out = tmp_path / "out.md"
    proc = _run(env, *round_args, "--brief", str(brief), "--out", str(out))
    assert proc.returncode == 2 and proc.stdout == "" and "--round" in proc.stderr
    assert _record(tmp_path) is None and not Path(f"{out}.log").exists()


@pytest.mark.parametrize(("text", "mode", "kind", "missing"), [
    (BAD, "first", "（--round first）", ["基准段"]),
    (BAD, "fresh", "（--round followup，不带 --resume）", ["基准段", "趋势", "上轮流程处置"]),
    (BAD, "resume", "（--round followup，带 --resume）", ["趋势", "上轮流程处置"]),
    (TREND + "上轮流程处置：待裁定\n", "resume", "（--round followup，带 --resume）", ["解除依据"]),
])
def test_missing_mark_message_names_the_items_and_the_guide(tmp_path, env, text, mode, kind, missing):
    brief = _brief(tmp_path, text)
    proc = _run(env, *ROUND_ARGS[mode], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 2 and proc.stdout == ""
    assert f"简报 {brief}{kind}缺少下列标记" in proc.stderr and "本轮没有送出" in proc.stderr
    assert re.findall(r"^  - (基准段|趋势|上轮流程处置|解除依据)：", proc.stderr, flags=re.M) == missing
    assert "docs/ai-eng/peer-review.md 第三、四节" in proc.stderr and "上下文压缩之后没有读过它的，先读再送" in proc.stderr
    assert "第三节「固定标记」条" in proc.stderr and "第四节「停下来的原因」条" in proc.stderr


def test_entries_named_in_the_hints_exist_in_the_method_doc():
    """提示与附段按条目名指向方法文档：第三节的「固定标记」条，第四节的「停下来的原因」条、看趋势的一条与熔断各条。"""
    sections = re.split(r"^## ", METHOD_DOC.read_text(encoding="utf-8"), flags=re.M)
    third = next(body for body in sections if body.startswith("三、"))
    fourth = next(body for body in sections if body.startswith("四、"))
    assert "\n- **固定标记**" in third
    assert "\n- **停下来的原因" in fourth and "\n- **每轮送出下一轮之前看趋势" in fourth and "\n- **熔断" in fourth


@pytest.mark.parametrize("target", ["no-such-brief.md", "."])
def test_unreadable_brief_is_a_usage_error(tmp_path, env, target):
    brief = tmp_path / target
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 2 and proc.stdout == ""
    assert f"简报 {brief} 读不到" in proc.stderr and "本轮没有送出" in proc.stderr
    assert _record(tmp_path) is None


def test_first_round_call_form_stdin_log_and_output(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    record = _record(tmp_path)
    assert record["args"] == ["exec", "-s", "read-only", "-o", str(out), "-"]
    assert record["stdin"].encode("latin-1") == _stdin_for(GOOD_FIRST.encode("utf-8"))
    log = Path(f"{out}.log").read_text(encoding="utf-8")
    assert "session id: 0199-abc" in log and "替身 codex 的 stderr" in log
    assert proc.stdout == f"session id: 0199-abc\n{out}\n"
    assert out.read_text(encoding="utf-8") == "复核意见\n"


def test_first_round_passes_model_and_effort(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(out), "--model", "m1", "--effort", "ultra")
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path)["args"] == ["exec", "-s", "read-only", "-m", "m1", "-c", 'model_reasoning_effort="ultra"',
                                         "-o", str(out), "-"]


def test_followup_without_resume_opens_a_new_session(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FOLLOWUP)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS["fresh"], "--brief", str(brief), "--out", str(out))
    assert proc.returncode == 0, proc.stderr
    record = _record(tmp_path)
    assert record["args"] == ["exec", "-s", "read-only", "-o", str(out), "-"]
    assert record["stdin"].encode("latin-1") == _stdin_for(GOOD_FOLLOWUP.encode("utf-8"))


def test_resume_call_form_and_explicit_log(tmp_path, env):
    brief = _brief(tmp_path, GOOD_RESUME)
    out, log = tmp_path / "out.md", tmp_path / "round-2.log"
    proc = _run(env, "--round", "followup", "--brief", str(brief), "--out", str(out), "--resume", "0199-abc",
                "--log", str(log), "--model", "m1", "--effort", "ultra")
    assert proc.returncode == 0, proc.stderr
    record = _record(tmp_path)
    assert record["args"] == ["exec", "resume", "0199-abc", "-c", 'sandbox_mode="read-only"',
                              "-m", "m1", "-c", 'model_reasoning_effort="ultra"', "-o", str(out), "-"]
    assert record["stdin"].encode("latin-1") == _stdin_for(GOOD_RESUME.encode("utf-8"))
    assert "替身 codex 的 stderr" in log.read_text(encoding="utf-8")
    assert not Path(f"{out}.log").exists()


def test_resume_without_model_and_effort(tmp_path, env):
    brief = _brief(tmp_path, GOOD_RESUME)
    out = tmp_path / "out.md"
    proc = _run(env, "--round", "followup", "--brief", str(brief), "--out", str(out), "--resume", "0199-abc")
    assert proc.returncode == 0, proc.stderr
    assert _record(tmp_path)["args"] == ["exec", "resume", "0199-abc", "-c", 'sandbox_mode="read-only"',
                                         "-o", str(out), "-"]


@pytest.mark.parametrize(("raw", "end"), [
    # BOM 与非法字节只在检查时容忍，传给 codex 的仍是文件的原始字节，附段接在其后
    ("\ufeff## 基准\n".encode("utf-8") + b"\xff\xfe\n", b""),
    ("## 基准\r\n".encode("utf-8"), b""),
    # 简报不以 LF 结尾（只用 CR 换行，或末尾没有换行）：先补一个 LF，附段之前仍是一个空行
    ("## 基准\r".encode("utf-8"), b"\n"),
    ("## 基准".encode("utf-8"), b"\n"),
])
def test_appendix_follows_the_brief_bytes_and_the_brief_file_is_unchanged(tmp_path, env, raw, end):
    brief = _brief(tmp_path, raw)
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(tmp_path / "out.md"))
    assert proc.returncode == 0, proc.stderr
    stdin = _record(tmp_path)["stdin"].encode("latin-1")
    assert stdin == _stdin_for(raw + end)
    # 不论简报用哪种换行，附段之前都是一个空行、一行 `---`、一个空行
    assert stdin.decode("utf-8", errors="replace").splitlines()[-4:] == ["", "---", "", APPENDIX]
    assert brief.read_bytes() == raw


def _case_insensitive(directory: Path) -> bool:
    probe = directory / "case-probe"
    probe.write_text("x", encoding="utf-8")
    try:
        return (directory / "CASE-PROBE").exists()
    finally:
        probe.unlink()


@pytest.mark.parametrize("collide", ["log-is-brief", "default-log-is-brief", "out-is-brief", "log-symlinks-brief",
                                     "out-hardlinks-brief", "log-differs-in-case"])
def test_output_and_log_may_not_be_the_brief_file(tmp_path, env, collide):
    """输出与日志都会被写入：哪一个就是简报文件，简报就被覆盖。写任何文件之前拦下，codex 不被调用，简报原样留着。

    只差大小写的写法跟着文件系统走：不区分大小写时它就是简报，拦下；区分时是另一个文件，照常送出。"""
    out = tmp_path / "out.md"
    brief = tmp_path / ("out.md.log" if collide == "default-log-is-brief" else "brief.md")
    brief.write_text(GOOD_FIRST, encoding="utf-8")
    args = ["--brief", str(brief), "--out", str(out)]
    rejected = True
    if collide == "log-is-brief":
        args += ["--log", str(brief)]
    elif collide == "out-is-brief":
        args = ["--brief", str(brief), "--out", str(brief), "--log", str(tmp_path / "run.log")]
    elif collide == "log-symlinks-brief":
        link = tmp_path / "alias.log"
        link.symlink_to(brief)
        args += ["--log", str(link)]
    elif collide == "out-hardlinks-brief":
        link = tmp_path / "alias.md"
        os.link(brief, link)
        args = ["--brief", str(brief), "--out", str(link), "--log", str(tmp_path / "run.log")]
    elif collide == "log-differs-in-case":
        rejected = _case_insensitive(tmp_path)
        args += ["--log", str(tmp_path / "BRIEF.MD")]
    proc = _run(env, *ROUND_ARGS["first"], *args)
    assert proc.returncode == (2 if rejected else 0), proc.stderr
    assert (_record(tmp_path) is None) == rejected
    if rejected:
        assert "就是简报文件" in proc.stderr
        assert not out.exists()
    assert brief.read_text(encoding="utf-8") == GOOD_FIRST


@pytest.mark.parametrize(("extra", "rc"), [
    ({"FAKE_CODEX_RC": "3"}, 3),
    ({"FAKE_CODEX_RC": "2"}, 2),
    ({"FAKE_CODEX_SIGNAL": "1"}, 128 + 15),
])
def test_exit_code_is_passed_through(tmp_path, env, extra, rc):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(out), **extra)
    assert proc.returncode == rc
    assert _record(tmp_path) is not None and proc.stdout.endswith(f"{out}\n")


def test_without_session_line_only_the_output_path_is_printed(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(out), FAKE_CODEX_SESSION="0")
    assert proc.returncode == 0 and proc.stdout == f"{out}\n"


def test_missing_codex_is_a_usage_error(tmp_path, env):
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    brief = _brief(tmp_path, GOOD_FIRST)
    out = tmp_path / "out.md"
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(out), PATH=str(empty))
    assert proc.returncode == 2 and proc.stdout == ""
    assert "PATH 里找不到 codex" in proc.stderr
    assert not Path(f"{out}.log").exists()


def test_unwritable_log_is_a_usage_error(tmp_path, env):
    brief = _brief(tmp_path, GOOD_FIRST)
    log = tmp_path / "no-such-dir" / "round.log"
    proc = _run(env, *ROUND_ARGS["first"], "--brief", str(brief), "--out", str(tmp_path / "out.md"), "--log", str(log))
    assert proc.returncode == 2 and f"日志文件 {log} 无法写入" in proc.stderr
    assert _record(tmp_path) is None
