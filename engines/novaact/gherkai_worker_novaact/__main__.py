"""worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。

argv 直通：`main()` 就是 `run_scope.main`，故三个入口（job 模式 / `--list-deterministic` /
`--match-steps`）经本模块与经 console script `gherkai-worker-novaact`（`[project.scripts]` 指向
`__main__:main`）行为完全一致——**只有一个 main，不存在「模块入口」与「命令入口」两份 argv 处理**。

**本模块不做任何包装**（不起子进程、不改 fd）：worker 进程必须是组合根直接 spawn 的那个进程，
`EVENTS_FD` 靠 `pass_fds` 继承（ADR 0024）；中间任何包装层都会吞掉 fd3。
"""
from __future__ import annotations

import sys

from gherkai_worker_novaact.run_scope import main

if __name__ == "__main__":
    sys.exit(main())
