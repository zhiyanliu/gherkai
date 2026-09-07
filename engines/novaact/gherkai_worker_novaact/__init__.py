"""gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。

本包 = 被 spawn 的 worker 进程本体（ADR 0024 协议的另一端）：读一个 scope 的 job → 跑它 →
把事件吐进事件通道。三个入口同一个 `main()`（见 `__main__`）：job 模式 / `--list-deterministic` /
`--match-steps`（ADR 0036 自述入口）。

**零 `gherkai_core` / `gherkai_runtime` 依赖**（ADR 0024）：worker 只讲线上协议（事件 JSON 形状 +
退出码约定），不 import core 的任何东西——协议是跨语言契约（Node 侧 worker 同形），共享代码会把
「契约」偷偷变成「共享实现」。`EX_WORKER_NETWORK=80` 这类常量两侧各自持有一份、以 ADR 0024 为准。

**必须是被直接 spawn 的那个进程**（ADR 0024 EVENTS_FD 经 `pass_fds` 继承）：故拉起形态是
`python -m gherkai_worker_novaact` / console script `gherkai-worker-novaact`，中间**不加包装进程**
（包装层会吞 fd3，midscene 换 `--import tsx` 那次已踩过）。
"""
