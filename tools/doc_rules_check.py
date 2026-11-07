#!/usr/bin/env python3
"""人读文本的措辞与悬空指针护栏——命令行入口（hook 与提交闸门用；规则与扫描面在 cli/tests/_doc_rules.py，单一事实源）。

用法：
    uv run python tools/doc_rules_check.py --changed          # 工作区相对 HEAD 的改动：已跟踪文件只报改动的行、未跟踪文件全扫
    uv run python tools/doc_rules_check.py --staged           # 暂存区里的文件按暂存的内容全扫（提交闸门的常规形态）
    uv run python tools/doc_rules_check.py --uncommitted      # 暂存区、工作区相对 HEAD 的改动与未跟踪文件的并集全扫
                                                              # （提交内容还没进暂存区的写法，如 `git commit -a`）
    uv run python tools/doc_rules_check.py <path> [<path>…]   # 指定文件全扫

三种模式都排除 graphify-out/，且只能单独使用。输出每条命中一行 `路径:行号: 类别 · 原文`；有命中退出码 1、无命中退出码 0、
自身出错退出码 2（hook 只在退出码 1 时阻断，只把错误信息作为提示转给 agent，免得工具问题把编辑卡死）。git 调用失败、规则
模块出错、无法识别的选项、指定的路径不存在都归自身出错：Python 未捕获异常的默认退出码 1 与「有命中」相同，hook 会阻断却
给不出命中行；把拼错的选项当路径跳过、以退出码 0 结束，又会被当成检查已通过。判据与替换口径见 ADR 0045 决策六与
CLAUDE.md 文档纪律「悬空指针红线」条；三层护栏的分工（测试兜底、hook 写完即查、提交闸门）见 ADR 0046。
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


def _names(*args: str) -> list[str]:
    """git 以 `-z` 列出的文件名（原样输出：不加 `-z` 时含非 ASCII 字符的名字会被 git 加引号转义，git show 就找不到它），
    排除 graphify-out/。"""
    return [rel for rel in _git(*args, "-z").split("\0") if rel and not rel.startswith("graphify-out/")]


def _staged_targets() -> list[Target]:
    """暂存区里新增或改动的文件，内容取暂存区（index）里将要提交的版本：部分暂存、暂存后又改了工作区时，判的仍是这次
    提交的内容。暂存后在工作区删掉的文件同样取暂存的版本来扫，但归类仍按工作区判断：按目录枚举的文档面认不出它，只套
    其余 markdown 那一束规则。`git show :<path>` 遵守 GIT_INDEX_FILE，`git commit <paths>` 用临时 index 时同样取对。"""
    targets: list[Target] = []
    for rel in _names("diff", "--cached", "--name-only", "--diff-filter=ACMR"):
        blob = subprocess.run(["git", "show", f":{rel}"], cwd=REPO, check=True, capture_output=True).stdout
        targets.append((REPO / rel, None, blob.decode("utf-8", errors="replace")))
    return targets


def _uncommitted_targets() -> list[Target]:
    """提交内容还没进暂存区的写法用的超集：暂存区、工作区相对 HEAD 的改动与未跟踪文件（遵守 .gitignore）三者的并集，整份扫。
    暂存区里的文件取暂存的版本（与 `--staged` 同一实现），其余取工作区的版本；同一文件暂存版与工作区版不同时两版都扫，
    因为 `git commit -a`、带路径参数或 `-o` 这类写法提交进去的改动可能来自其中任意一版。工作区里已删掉的文件只剩暂存版可扫。"""
    targets = _staged_targets()
    staged = {path: text for path, _, text in targets}
    names = set(_names("diff", "HEAD", "--name-only", "--diff-filter=ACMR"))
    names.update(_names("ls-files", "--others", "--exclude-standard"))
    for rel in sorted(names):
        path = REPO / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if staged.get(path) != text:
            targets.append((path, None, text))
    return targets


MODES = {"--changed": _working_tree_targets, "--staged": _staged_targets, "--uncommitted": _uncommitted_targets}


def main(argv: list[str]) -> int:
    # 在函数内 import：规则模块本身出错（如编辑中途留下的语法错误）时也落进 __main__ 的兜底，按自身出错以退出码 2 结束
    from _doc_rules import classify, scan
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    if len(argv) == 1 and argv[0] in MODES:
        targets = MODES[argv[0]]()
    else:
        options = [a for a in argv if a.startswith("-")]
        if options:
            # 拼错的选项若被当成路径，归类不到任何扫描面就被跳过、以退出码 0 结束，调用方会误以为检查已通过
            print(f"doc_rules_check：无法识别的参数 {options[0]}（--changed / --staged / --uncommitted 只能单独使用，"
                  "其余参数都应是文件路径）", file=sys.stderr)
            return 2
        targets = [(REPO / a if not Path(a).is_absolute() else Path(a), None, None) for a in argv]
        missing = [a for a, (path, _, _) in zip(argv, targets) if not path.is_file()]
        if missing:  # 不论能否归类都先报错：归类不到扫描面的路径若因不存在而被跳过，同样会被当成检查已通过
            raise FileNotFoundError(f"指定的路径不存在或不是文件：{', '.join(missing)}")
    total = 0
    scanned: set[Path] = set()
    reported: set[tuple[Path, int, str, str]] = set()  # 两版都扫的文件，两版相同的命中只报一次
    for path, only, text in targets:
        kind = classify(path)
        if kind is None:
            continue
        if only is not None and not only:
            continue  # 已跟踪但没有新增/改动的行（例如只删行）
        scanned.add(path)
        for line_no, label, line in scan(kind, path, only, text=text):
            if (path, line_no, label, line) in reported:
                continue
            reported.add((path, line_no, label, line))
            total += 1
            print(f"{path.relative_to(REPO)}:{line_no}: {label} · {line}")
    print(f"doc_rules_check：扫了 {len(scanned)} 个文件，命中 {total} 处", file=sys.stderr)
    return 1 if total else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except subprocess.CalledProcessError as exc:
        print(f"doc_rules_check：git 调用失败（{exc}）", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:  # 其余故障（指定的路径不存在、路径在仓库外、找不到 git、规则模块出错）同属自身出错
        print(f"doc_rules_check：自身出错（{type(exc).__name__}: {exc}）", file=sys.stderr)
        sys.exit(2)
