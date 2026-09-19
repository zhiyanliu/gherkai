"""本地 adapter 共享的原子落盘（同目录 tmp + `os.replace`）：读者要么看到旧文件、要么看到新文件，绝不看到半截/空内容。

`Path.write_text` 是 truncate 再写，两步之间的读者会拿到**空文件**或前半截、`json.loads` 直接炸
（本项目实测：紧循环读同一被反复重写的文件，几十次读内即可稳定撞到空文件）。tmp 与目标同目录保证 rename 同分区原子。

三面的并发读者都是**设计内的、真实存在的**（不是防御性假设）：
- 控制面 `run_state.json`：per-run 推进进程在文件锁内写它时，`gherkai status` / 接力进程**无锁**读同一文件
  （读面不持 `.runstate.lock`，只写面互斥；ADR 0030 决定四 / 0034）。
- 数据面 `jobs/*.json`：`explain` 被允许在 run 执行到一半时读已完成 job（ADR 0042 决策四），读者是另一个进程。
- 报告面 `manifest.json` / `index.html`：finalize 可被两个推进器各写一遍同一份报告（ADR 0027 派生视图、
  可重建），而人/CI 会在第一个写者退出后立刻读。

**权限显式给**（调用方声明 `mode`）：`tempfile.mkstemp` 建的文件是 0600，直接 rename 会把产物静默收窄成
owner-only。`jobs/*.json`（消费者 CI/人，ADR 0034）与报告产物（给人/CI/静态 server 读，ADR 0027）要保持
可读，故落盘前 chmod；控制面文件按其调用方的声明保持更严的权限。mode 是显式值、不按 umask 折算——
产物的可读性是契约的一部分，不该随环境 umask 漂移。

不做 fsync：本层防的是**并发读者看到中间态**，不是掉电后的持久性（那需要 fsync 文件 + 目录，成本进每次收尾）。
"""
from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, text: str, *, mode: int = 0o644) -> None:
    """把 text 原子落到 path（UTF-8）：写同目录 tmp → chmod 成 mode → `os.replace` 顶上。失败清理 tmp、异常冒泡。"""
    # 前缀截断到 200 字符：tmp 名 = prefix + 8 随机 + ".tmp"，不截断会把「目标名本身已接近 NAME_MAX」的落点
    # （jobs/<urlencode 后的 scope_id>.json——scope_id 可含中文、每字 9 字符，ADR 0025「id 派生」）在建 tmp 时
    # 就 ENAMETOOLONG，比非原子写更早失败。mkstemp 自身保唯一，截断不会撞名。
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name[:200] + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(tmp, mode)  # mkstemp 是 0600；见模块头「权限显式给」
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def atomic_write_json(path: Path, obj, *, mode: int = 0o644) -> None:
    """同 `atomic_write_text`，内容是 obj 的 JSON（`ensure_ascii=False, indent=2`——全仓落盘口径一致）。"""
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2), mode=mode)
