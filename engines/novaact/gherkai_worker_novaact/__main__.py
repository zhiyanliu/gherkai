"""worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。

argv 直通：`main()` 就是 `run_scope.main`，故三条路径（job 模式 + 两个非 job 入口 `--capabilities` 自述 /
`--match-steps` 查询）经本模块与经 console script `gherkai-worker-novaact`（`[project.scripts]` 指向
`__main__:main`）行为完全一致——**只有一个 main，不存在「模块入口」与「命令入口」两份 argv 处理**。

**本模块不做任何包装**（不起子进程、不改 fd）：`EVENTS_FD` 靠 `pass_fds` 继承（ADR 0024），
本模块所在的进程必须就是写事件的那个进程；包装进程能否把 fd3 原样传给子进程不能预设——tsx 二进制与 npx
实测都没有原样传下，uvx 实测原样传下（这是定位链第四级只为 novaact 保留 uvx 的依据，ADR 0037 决策 3）。
"""
from __future__ import annotations

import sys

from gherkai_worker_novaact.run_scope import main

if __name__ == "__main__":
    sys.exit(main())
