#!/usr/bin/env python3
"""把 `--json` 字段契约页渲染成 agent skill 里的那份副本（确定性转换，ADR 0043 决策四）。

    docs/internals/cli-json-contract.md            ← 唯一**手写**源（给人的 guide）
      └─(本脚本)→ cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md   ← 入库副本，随 wheel 发行

**为什么不是 `cp`**：源页头部的引用块与姊妹页导航段带 ADR 编号、内部机制名和 `](./x.md)` 相对链接；
skill 的消费现场是使用方项目里的一份拷贝，那些指代对使用方是噪声、那些相对链接是死链
（ADR 0039 面二 + ADR 0043 决策四）。**为什么不是手工维护第二份**：无护栏的重复迟早漂——
`cli/tests/test_skill.py` 断言 `transform(源) == 入库副本`，改了源没重新生成副本即红。

转换规则（稳定契约，改这里要同步 ADR 0043 决策四那三条）：

1. 标题后到第一个 `##` 之间：剥掉全部 `>` 引用块（可多段）与「姊妹页…」导航段，换成一句产品语言。
   **由此得出一条写作约定**：源页头部要新增给 contributor 的话（护栏在哪、权威在哪），写进引用块里——
   块整体被剥；写成裸段落则会原样发到使用方项目。
2. 指向仓库内文件的指针 → `gherkai <子命令> --help` 或 `blob/HEAD/` 绝对 URL（`POINTER_REWRITES`）。
3. 禁词按 `FORBIDDEN_REWRITES` 改写成产品语言。

三条都**只做登记过的替换**，剩余禁词 / 相对链接 / 仓库内路径一律硬失败（`TransformError`）：
静默发出去比构建失败坏得多——错在使用方项目里才现形。

用法：
    python3 tools/render_skill_contract.py             # 渲染并写入副本
    python3 tools/render_skill_contract.py --check     # 只比对（漂了以退出码 1 结束），CI / 本地自查用
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "docs" / "internals" / "cli-json-contract.md"
TARGET = REPO_ROOT / "cli" / "gherkai_cli" / "skills" / "gherkai" / "references" / "cli-json-contract.md"

# 禁词 / 相对链接正则复用护栏那份单一事实源（两份表必漂，见该模块 docstring）。
sys.path.insert(0, str(REPO_ROOT / "cli" / "tests"))
from _doc_rules import FORBIDDEN, RELATIVE_LINK  # noqa: E402

# 剥掉头部引用块与导航段后补的一句：产品语言，只说这页是什么。
LEAD = "本页讲 `--json` 各命令输出有哪些字段、什么意思、何时出现。"

# 规则 2：仓库内文件指针 → 使用方拿得到的东西（`--help` 或绝对 URL）。key 是源页里的**原文片段**，
# 逐字匹配、命中零次即红（源页改了措辞就该回来改这张表，而不是让替换悄悄失效）。
POINTER_REWRITES: dict[str, str] = {
    "退出码含义见 `docs/user-guide/running-and-results.md`「退出码」。":
        "退出码含义见 `SKILL.md` 的退出码一节，或 "
        "https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/running-and-results.md 「退出码」。",
    "`--all` / `--full` 的语义见 `docs/user-guide/running-and-results.md` 的 `explain` 一节。":
        "`--all` / `--full` 的语义见 `gherkai explain --help`。",
}

# 规则 3：禁词 → 产品语言。同样是逐字替换的显式登记表；未登记的禁词由 `_assert_clean` 拦。
# `FORBIDDEN` 正则只收得住成形的内部指代（ADR 编号 / 决策号 / 那几个固定机制名），源页里的其它
# 内部用词（推进器 / 投影 / definition …）机械层照不出、只能靠人眼发现后登记在此。
FORBIDDEN_REWRITES: dict[str, str] = {
    "命中定位链的哪一级": "命中 worker 查找顺序的哪一级",
    "顶层由三部分组成：RunResult（判定）、": "顶层由三部分组成：这次运行的判定、",
    "RunState（控制面运行态）": "这个 run 的运行态",
    "| `report_index` | RunReport `index.html`": "| `report_index` | 报告首页 `index.html`",
    "已投影的事件水位（诊断用）；仅经推进器投影写入的 run 有":
        "已处理到的事件水位（诊断用）；仅由后台推进写入的 run 有",
    "（投影滞后于 job 级状态）": "（run 级状态滞后于 job 级状态）",
    "被推进器认领的时刻": "被后台推进认领的时刻",
    "`run_meta`（definition）": "`run_meta`（提交时固定的本次运行任务本身）",
    "本次 run 的 definition（提交时固定）": "本次 run 的任务定义（提交时固定）",
    "definition / 运行态的落点": "任务定义 / 运行态的落点",
    "内嵌的完整 `job` definition": "内嵌的完整 `job` 定义",
}

# 仓库内路径的形态（`路径/文件.后缀` 反引号 token）：转换后不该再有——它在使用方项目里既打不开也 grep 不到。
IN_REPO_PATH = re.compile(r"`[\w.-]+/[\w./-]+\.(?:py|md|mts|ts|toml|yml|yaml|json|cfg)`")


class TransformError(RuntimeError):
    """源页形态或内容超出登记范围。宁可失败，也不把内部指代发进使用方项目。"""


def transform(text: str) -> str:
    """纯函数：源页正文 → 副本正文。无 IO、无全局状态，护栏直接拿它比对入库副本。"""
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise TransformError("源页第一行不是 `# ` 标题——形态变了，先更新转换规则")

    head_end = next((i for i, ln in enumerate(lines) if ln.startswith("## ")), len(lines))
    head, body = lines[1:head_end], lines[head_end:]

    kept, dropped_quote, dropped_nav = [], 0, 0
    for para in _paragraphs(head):
        if para[0].lstrip().startswith(">"):        # 规则 1：头部引用块（定位 / 权威在 code / 护栏）
            dropped_quote += 1
            continue
        if para[0].startswith("姊妹页"):             # 规则 1：姊妹页导航段（三条 guide 间的相对链接）
            dropped_nav += 1
            continue
        kept.append(para)
    if not dropped_quote:
        raise TransformError("源页标题后没有 `>` 引用块——形态变了（定位/权威/护栏那块搬走了？），先更新转换规则")
    if dropped_nav != 1:
        raise TransformError(f"「姊妹页」导航段应恰好一段，实际 {dropped_nav} 段——先更新转换规则")

    out = [lines[0], "", LEAD]
    for para in kept:
        out += [""] + para
    out += [""] + body
    result = "\n".join(out).rstrip("\n") + "\n"

    for old, new in POINTER_REWRITES.items():
        if old not in result:
            raise TransformError(f"指针改写表里这条在源页里找不到（措辞变了？）：{old!r}")
        result = result.replace(old, new)
    for old, new in FORBIDDEN_REWRITES.items():
        if old not in result:
            raise TransformError(f"禁词改写表里这条在源页里找不到（措辞变了？）：{old!r}")
        result = result.replace(old, new)

    _assert_clean(result)
    return result


def _paragraphs(lines: list[str]) -> list[list[str]]:
    """按空行切段（段内保留原始换行——源页的长段是手工折行的，副本逐字继承才好 diff）。"""
    paras: list[list[str]] = []
    for line in lines:
        if line.strip():
            if not paras or paras[-1] == []:
                paras.append([])
            paras[-1].append(line)
        elif paras and paras[-1]:
            paras.append([])
    return [p for p in paras if p]


def _assert_clean(text: str) -> None:
    """转换后的三条硬断言：无禁词、无相对链接、无仓库内路径。命中即报行号，让人回去补登记表。"""
    problems: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        if FORBIDDEN.search(line):
            problems.append(f"{i}: 未登记的禁词（补进 FORBIDDEN_REWRITES）：{line.strip()[:140]}")
        if RELATIVE_LINK.search(line):
            problems.append(f"{i}: 相对链接（安装态是死链，改绝对 URL 或反引号裸路径）：{line.strip()[:140]}")
        for m in IN_REPO_PATH.finditer(line):
            problems.append(f"{i}: 仓库内文件指针 {m.group(0)}（补进 POINTER_REWRITES）：{line.strip()[:140]}")
    if problems:
        raise TransformError("转换后的副本仍不干净：\n  " + "\n  ".join(problems))


def render() -> str:
    return transform(SOURCE.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="渲染 skill 里的 `--json` 字段契约副本")
    ap.add_argument("--check", action="store_true", help="只比对入库副本、不写（漂了以退出码 1 结束）")
    args = ap.parse_args(argv)

    try:
        rendered = render()
    except TransformError as exc:
        print(f"渲染失败：{exc}", file=sys.stderr)
        return 1

    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.is_file() else None
        if current == rendered:
            print(f"副本与源一致：{TARGET.relative_to(REPO_ROOT)}")
            return 0
        print(f"副本与源不一致（或不存在）：{TARGET.relative_to(REPO_ROOT)}"
              f"——运行 `python3 tools/render_skill_contract.py` 重渲染", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(rendered, encoding="utf-8")
    print(f"已写入 {TARGET.relative_to(REPO_ROOT)}（{len(rendered.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
