#!/usr/bin/env python3
"""人读文本的措辞与悬空指针护栏——命令行入口（hook 与提交闸门用；规则与扫描面在 cli/tests/_doc_rules.py，单一事实源）。

用法：
    uv run python tools/doc_rules_check.py --changed          # 工作区相对 HEAD 的改动：已跟踪文件只报改动的行、未跟踪文件全扫
    uv run python tools/doc_rules_check.py --staged           # 暂存区里的文件按暂存的内容全扫（提交闸门）
    uv run python tools/doc_rules_check.py <path> [<path>…]   # 指定文件全扫

输出每条命中一行 `路径:行号: 类别 · 原文`；有命中退出码 1、无命中退出码 0、自身出错退出码 2（hook 只在退出码 1 时阻断，
只把错误信息作为提示转给 agent，免得工具问题把编辑卡死）。判据与替换口径见 ADR 0045 决策六与 CLAUDE.md 文档纪律
「悬空指针红线」条；三层护栏的分工（测试兜底、hook 写完即查、提交闸门）见 ADR 0046。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "cli" / "tests"))

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout


def _changed_lines(rel: str) -> set[int]:
    """工作区相对 HEAD 新增或改动的行号（unified=0 的 hunk 头直接给出新文件侧的区间）。"""
    out = _git("diff", "-U0", "HEAD", "--", rel)
    lines: set[int] = set()
    for line in out.splitlines():
        m = _HUNK.match(line)
        if not m:
            continue
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        lines.update(range(start, start + count))
    return lines


# 扫描目标：(路径, 只报的行号——None 为整份, 要扫的内容——None 为读工作区里的文件)。
Target = tuple[Path, set[int] | None, str | None]


def _working_tree_targets() -> list[Target]:
    targets: list[Target] = []
    for row in _git("status", "--porcelain", "--untracked-files=all").splitlines():
        status, rel = row[:2], row[3:]
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if status.strip() == "D" or rel.startswith("graphify-out/"):
            continue
        p = REPO / rel
        if not p.is_file():
            continue
        untracked = status == "??" or status[1] == "A" or status[0] == "A"
        targets.append((p, None if untracked else _changed_lines(rel), None))
    return targets


def _staged_targets() -> list[Target]:
    """暂存区里新增或改动的文件，内容取暂存区（index）里将要提交的版本：部分暂存、暂存后又改了工作区时，判的仍是这次
    提交的内容。暂存后在工作区删掉的文件同样取暂存的版本来扫，但归类仍按工作区判断：按目录枚举的文档面认不出它，只套
    其余 markdown 那一束规则。`git show :<path>` 遵守 GIT_INDEX_FILE，`git commit <paths>` 用临时 index 时同样取对。"""
    targets: list[Target] = []
    # -z 让文件名原样输出：不加时含非 ASCII 字符的名字会被 git 加引号转义，git show 就找不到它
    for rel in _git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR").split("\0"):
        if not rel or rel.startswith("graphify-out/"):
            continue
        blob = subprocess.run(["git", "show", f":{rel}"], cwd=REPO, check=True, capture_output=True).stdout
        targets.append((REPO / rel, None, blob.decode("utf-8", errors="replace")))
    return targets


def main(argv: list[str]) -> int:
    # 在函数内 import：规则模块本身出错（如编辑中途留下的语法错误）时也落进 __main__ 的兜底，按自身出错以退出码 2 结束
    from _doc_rules import classify, scan
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    if argv == ["--changed"]:
        targets = _working_tree_targets()
    elif argv == ["--staged"]:
        targets = _staged_targets()
    else:
        targets = [(REPO / a if not Path(a).is_absolute() else Path(a), None, None) for a in argv]
    total = 0
    scanned = 0
    for path, only, text in targets:
        kind = classify(path)
        if kind is None:
            continue
        if only is not None and not only:
            continue  # 已跟踪但没有新增/改动的行（例如只删行）
        scanned += 1
        for line_no, label, line in scan(kind, path, only, text=text):
            total += 1
            print(f"{path.relative_to(REPO)}:{line_no}: {label} · {line}")
    print(f"doc_rules_check：扫了 {scanned} 个文件，命中 {total} 处", file=sys.stderr)
    return 1 if total else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except subprocess.CalledProcessError as exc:
        print(f"doc_rules_check：git 调用失败（{exc}）", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:  # 其余故障（文件不存在、路径在仓库外、找不到 git、规则模块出错）同属自身出错
        print(f"doc_rules_check：自身出错（{type(exc).__name__}: {exc}）", file=sys.stderr)
        sys.exit(2)
