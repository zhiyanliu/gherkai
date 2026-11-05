"""worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）及包根共用的辅助模块。

`job_source` / `event_sink` / `artifact_upload` 各自封一条边缘的两态（fd/stdin ↔ S3/DDB，判据一律是
「注入了哪个 env」而非「是否 Fargate」，ADR 0016 红线）；`workflow_setup` / `constants` 是与 spike 共用
的建连前置与单一真源常量；`precheck`（建会话前对 job 行的自检，ADR 0049 决策 7）与 `redact`（工具自产文字的凭据
脱敏，ADR 0035 决策 5）是不读 env、不建会话的纯函数，`tunnel_warmup`（隧道会话预热，ADR 0051 决策 13）通过调用方
传入的页面对象导航，各自的契约见模块头。

放在子包里而非包根，是为了让「协议/派发逻辑」（包根的 `run_scope` / `deterministic*`）与「跟外界打交道
的那几个 I/O 边缘组件」在目录上就分开——后者是单测里被替换掉的那部分。
"""
