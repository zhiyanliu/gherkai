"""`gherkai skill install`：把随 wheel 带的 agent skill 收敛安装到使用方项目 / 用户级 agent 目录（ADR 0043 决策三）。

**定位只有一条路**：`importlib.resources.files("gherkai_cli") / "skills" / "gherkai"`——editable 开发态与
装好的 wheel 是同一条路径，故**不设仓库根回落**（对齐 ADR 0037 决策 3「不设 dev 模式特判」）。

**语义是整目录收敛、不是幂等覆盖**（ADR 0043 决策三）：先删目标 skill 目录、整份写入包内那份、再写
`.gherkai-skill-version` 标记；装完的目录 = 包内那份 + 该标记（标记只存在于安装态，包内不得有），
跨版本升级不会留下上一版多出来的 reference。删前只认三种目标：不存在 / 空 / 带标记——否则退 2，
防 `--dir` 打错把用户自己的目录整掉。

**版本由调用方传进来**（`__main__._cmd_skill_install` 交 `_installed_version()`，与后端版本 skew 比对同一取法，
ADR 0037 决策 7）：本模块不自己去要版本，既避免与 `__main__` 循环 import，也让「版本怎么取」单点维护。
源码直跑取不到 → 标记记 `UNKNOWN_VERSION`、安装照常完成（与「取不到就跳过比较」的分叉一致）；
`_dist_version()` 给 `--version` 显示用的占位串绝不写进标记。

**输出面**：stdout 只属 `--print`（供管道），其余全部诊断走 stderr（同 `__main__._progress` 的约定）。
退出码只有 0 / 2。
"""
from __future__ import annotations

import shutil
import sys
from importlib.resources import as_file, files
from pathlib import Path

# skill 名 = 目录名 = frontmatter 的 name（ADR 0043 决策六的形态护栏据此断言）
SKILL_NAME = "gherkai"
# 安装态标记：值 = 已安装发行版本；它是「这个目录是本命令装的」的唯一凭据（删前判据）
MARKER_NAME = ".gherkai-skill-version"
UNKNOWN_VERSION = "版本未知"

# 一行提示，人手贴进项目的 agent 指令文件即可（发现与触发靠 SKILL.md 的 frontmatter，这行只是兜底提示）。
# 刻意**不带路径**：项目级 / 用户级两种落点混着写会让这行随机器而异，而它是要提交进仓库的。
POINTER_LINE = "驾驭 gherkai 用 skill `gherkai`"

# 各 agent 的 skill 发现位（项目级相对项目根、用户级相对 HOME，两者同后缀）与它的指令文件。
_AGENT_SKILL_HOME = {"claude-code": Path(".claude") / "skills", "codex": Path(".agents") / "skills"}
_AGENT_POINTER_FILE = {"claude-code": "CLAUDE.md", "codex": "AGENTS.md"}
AGENT_CHOICES = ("claude-code", "codex", "all")


def _stderr(*parts, end: str = "\n") -> None:
    """诊断 → stderr（stdout 留给 `--print` 的管道产出）。"""
    print(*parts, end=end, file=sys.stderr)


def _packaged_skill_dir():
    """包内那份 skill 的 Traversable（不落地成路径；要真路径的调用方自己套 `as_file`）。"""
    return files("gherkai_cli") / "skills" / SKILL_NAME


def _agents(choice: str) -> tuple[str, ...]:
    return ("claude-code", "codex") if choice == "all" else (choice,)


def _print_skill() -> int:
    """`--print`：把 SKILL.md 正文原样打到 stdout（不安装）。"""
    try:
        text = (_packaged_skill_dir() / "SKILL.md").read_text(encoding="utf-8")
    except OSError as e:
        _stderr(f"装的 gherkai 里找不到 skill 内容（安装包不完整？）：{e}。重装 gherkai 后再试")
        return 2
    print(text, end="")
    return 0


def _converge(src: Path, dst: Path, version_text: str) -> None:
    """整目录收敛：删旧 → 整份拷 → 写标记。`__pycache__` / `*.pyc` 不拷（保「装完 = 包内那份 + 标记」）。"""
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (dst / MARKER_NAME).write_text(version_text + "\n", encoding="utf-8")


def _is_ours(dst: Path) -> bool:
    """删得起吗：不存在 / 空目录 / 带安装标记 → 是；其余（含目标是文件）→ 不是。"""
    if not dst.exists():
        return True
    if not dst.is_dir():
        return False
    if (dst / MARKER_NAME).is_file():
        return True
    return not any(dst.iterdir())


def _ask_pointer(paths: list[Path]) -> bool:
    """交互终端下问一次（默认否）；非交互（管道 / CI）直接否，只打印那一行让人自己贴。"""
    stdin = getattr(sys, "stdin", None)
    if stdin is None or not stdin.isatty():
        return False
    _stderr(f"把这一行写进 {'、'.join(str(p) for p in paths)}？(y/N) ", end="")
    try:
        reply = input()
    except EOFError:
        return False
    return reply.strip().lower() in ("y", "yes")


def _append_pointer(path: Path) -> bool:
    """把提示那一行追加进 agent 指令文件（不存在就建）。已有即不动，返回 False。"""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if POINTER_LINE in text:
        return False
    if not text:
        block = POINTER_LINE + "\n"
    else:
        block = ("\n" if text.endswith("\n") else "\n\n") + POINTER_LINE + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(block)
    return True


def install(args, *, version: str | None) -> int:
    """`skill install` 的全部行为。读 args 上的 `agent` / `dir` / `global_` / `print_only` / `pointer`。

    先把所有目标都过一遍自护判据、再动手：`--agent all` 时任一目标不认，两处都不装（半装态更难收拾）。
    """
    if args.print_only:
        return _print_skill()

    agents = _agents(args.agent)
    if args.global_:
        root = Path.home()
        # 用户级装法没有「项目根」：指令文件仍按当前目录这个项目算（提示里给全路径，答 y 前看得见动的是谁）
        pointer_root = Path.cwd()
    else:
        if args.dir is not None and not Path(args.dir).is_dir():
            _stderr(f"--dir={args.dir!r} 不是目录：给项目根的路径（或先把它建出来）")
            return 2
        root = Path(args.dir) if args.dir is not None else Path.cwd()
        pointer_root = root
    targets = {a: root / _AGENT_SKILL_HOME[a] / SKILL_NAME for a in agents}

    refused = [dst for dst in targets.values() if not _is_ours(dst)]
    if refused:
        for dst in refused:
            _stderr(f"{dst} 里是别的东西（不是本命令装的）：安装会整个替掉它，为防误删这里先停下——"
                    "把它挪走后再装")
        return 2

    version_text = version or UNKNOWN_VERSION
    with as_file(_packaged_skill_dir()) as src:
        if not (src / "SKILL.md").is_file():
            _stderr(f"装的 gherkai 里找不到 skill 内容（安装包不完整？）：{src}。重装 gherkai 后再试")
            return 2
        label = f"版本 {version}" if version else UNKNOWN_VERSION
        # 落盘失败（路径里某段是文件、只读目录、盘满…）也必须收在 0/2 的退出码里，不抛栈给使用者
        try:
            for agent, dst in targets.items():
                _converge(Path(src), dst, version_text)
                _stderr(f"{agent}：skill `{SKILL_NAME}` 已装到 {dst}（{label}）")
        except OSError as e:
            _stderr(f"装不进去：{e}。看一眼这个路径与它的写权限，再重来")
            return 2

    pointer_paths: list[Path] = []
    for agent in agents:
        p = pointer_root / _AGENT_POINTER_FILE[agent]
        if p not in pointer_paths:
            pointer_paths.append(p)

    answer = args.pointer
    if answer == "yes" or (answer is None and _ask_pointer(pointer_paths)):
        for p in pointer_paths:
            try:
                added = _append_pointer(p)
            except UnicodeDecodeError:
                # 使用方的指令文件不是 UTF-8（GBK 存出的 CLAUDE.md 等）：读侧一个
                # `read_text(encoding="utf-8")` 抛的栈不该冲到使用者面前（同 `__main__` 读 feature 处的写法）。
                # 宁可不写也不改用 errors="replace"：那会把用户文件里的非 UTF-8 段落写坏。
                # 与下面的 OSError 分开报：混在「写不进去」里会把人引去查写权限/磁盘，真因（文件编码）只剩一句
                # 英文 codec 报文。skill 本身已装好，退出码照「没全做成」算。
                _stderr(f"skill 已装好，但 {p} 不是 UTF-8 编码、不敢改它（怕把原文写坏）。这一行请自己贴：{POINTER_LINE}")
                return 2
            except OSError as e:
                # skill 本身已装好；只是要加的那一行没写进去——说清两件事，退出码照「没全做成」算
                _stderr(f"skill 已装好，但写不进 {p}：{e}。这一行请自己贴：{POINTER_LINE}")
                return 2
            _stderr(f"已加进 {p}：{POINTER_LINE}" if added else f"{p} 里已有这一行，没重复加")
    else:
        _stderr("想让 agent 更早想起它，把这一行贴进 " + "、".join(str(p) for p in pointer_paths) + "：")
        _stderr(f"  {POINTER_LINE}")
    return 0
