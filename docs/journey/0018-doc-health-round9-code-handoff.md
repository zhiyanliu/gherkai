> 类型: 调查记录

# doc-health 第九轮移交 code-health 的输入：code 侧客观发现与「改 code、ADR 不动」的裁定

第九轮文档健康度复盘（2026-11-04）对照 code 核文档时，顺带核出一批落在 code、配置与注释上的客观漂移，以及若干「code 偏离 ADR 已定设计且无 ADR 记录」的 ③ 类项；按方法文档的分工它们由 code-health 复盘接收（VIOLATES_ADR 条）。本文是那次复盘的产物清单，供下一次 code-health 作输入；吸收完即删。每条带原发现编号（F 编号只在第九轮待批报告与本文内有效）、文件与行号（行号为当时值）、问题与改法摘要。

## 一、裁定为「改 code、ADR 不动」的设计偏离（VIOLATES_ADR）

- **D01** plan 不预告确定性 step 的 requires 前提：ADR 0048 决策 6 与 0049 决策 6 规定交集条目带 requires 时 plan 写明「需要网页上下文；设备不提供时记为错误」，并（第九轮补定）在 `plan --json` 的 `steps[].deterministic` 带 `requires` 键（字符串数组、无前提省略）。改 `cli/gherkai_cli/__main__.py` 的 `_probe_deterministic_dispatch` 把与 scope 目标相符的交集条目 requires 附到 probe，`render._dispatch_hint` 借 `requires_label` 追加文本，`plan_to_dict` 带键；`cli/tests/test_cli_json_contract.py` 的 plan 样例加一条带 requires 的命中；改后重渲染 skill 副本。
- **D02** 模板 task-def 没显式设 runtimePlatform：ADR 0038 概念模型把架构载体定为模板 revision 的 runtimePlatform。改 `deploy_aws/gherkai_deploy_aws/stack.py` 的 `ecs.FargateTaskDefinition(...)` 显式传 `runtime_platform=ecs.RuntimePlatform(cpu_architecture=X86_64, operating_system_family=LINUX)`；下次 deploy 出新模板 revision 后第 4 步重派生各 variant（镜像不动）。真实 DescribeTaskDefinition 对未设该字段的 revision 返回形态未真跑核过，改 code 后不再依赖它。
- **D05** 提前返回路径跳过设备计量：`core/gherkai_core/schedule.py` `_Worker._run_once` 的「未启动记 SKIPPED」与「起 worker 失败」两条提前返回没调 `apply_device_metering`，设备 job 缺 `sessions[]` 与两个计量键，违背 ADR 0051 决策 7「只按目标判」。在两处返回前补调（或在 `_Worker.run` 收口统一调一次），补设备 job SKIPPED 形态的单测。
- **D06** Nova 三条提前退出路径的排空超时提示与 ADR 0039 面一「两引擎措辞一致、只说已放弃加不影响什么」不一致：改 `engines/novaact/gherkai_worker_novaact/run_scope.py` 约 :441 那句与 Midscene 对齐（例如「部分证据截图未能在收尾时限内传完（已放弃，不影响判定结果；这些截图的链接可能打不开）」），同步 `engines/novaact/tests/test_evidence.py` 的断言。
- **D07** 护栏扫描面落后于 ADR 0045 决策一：`cli/tests/_doc_rules.py` 的 `ai_side_docs()` 把已入库的 `.claude/skills/*/SKILL.md` 与 `skills/gherkai-evals/grader-prompt.md` 纳入（只收 git 已跟踪文件；journey 与 fixtures 继续排除）。
- **D11** 护栏规则源两处缺口：`_doc_rules.FORBIDDEN` 补「推进器」（代价：`docs/diagrams/execution-detached-gates.json` 两处与 `run-execution.json` 一处要改说「云端后台 / 后台推进」并重出 SVG；契约源页的「推进器」已登记在 render_skill_contract 的改写表，核一致）；`BARE_WP` 正则扩成覆盖纯字母形态如 `\bWP(?:-?\d+[A-Za-z]?(?:-\d+)?|-[A-Z])\b`，`test_adr_hygiene` 补 `WP-S` 命中、`WPS` 不命中两例。
- **D12** wire 解码不校验三态：`core/gherkai_core/wire.py` `event_from_json` 的 step_done / scenario_done 分支按 scope_done 的写法校验 status ∈ {passed, failed, error}，否则抛 ValueError（worker 违约），并校准 :183 注释。

补充：D08（导航地址只带一侧引号的不对称处置）与 D09（task role 多授 `devicefarm:GetDevice`，须用受限角色真跑后再撤）待 owner 定，定为改 code 时一并接收。

## 二、code / 配置 / 注释上的客观漂移（83 条，经对抗验证 CONFIRMED，文档复盘不改 code）

### `.github/workflows/release.yml`（2）
- F607 :7 · STALE · 头注释写「一次性人工前置（PyPI trusted publisher / npm token / GHCR 包可见性）」，但 npm 侧已改走 trusted publishing、无 token 无 secret（同文件 :182-185 与 workflows README §3 都这么写），这里的「npm token」是旧方案的残 → release.yml:7 旧句「# 一次性人工前置（PyPI trusted publisher / npm token / GHCR 包可见性）见 .github/workflows/README.md。」→ 新句「# 一次性人工前置（PyPI trusted publisher / npm t
- F608 :5 · STALE · 头注释列 gate 时只有「tag 形态 + 算出的版本==tag」，漏了 :71-75 那道「CHANGELOG 有本版节、README 的 skill 安装命令钉本版 tag」的 gate；另外「版本==tag」在注释里把 == 当谓语用。 → release.yml:5 旧句「# 顺序与失败语义按 ADR 0037 决策 8：gate（tag 形态 + 算出的版本==tag）→ ① PyPI（build → attest → publish）」→ 新句「# 顺序与失败语义按 ADR 0037 决策 8：gate（tag 形态 + CHAN

### `.gitignore`（2）
- F236 :88 · STALE · 注释写「项目级 skill 只放行 diagram/」，下面的规则（:91）实际放行的是 `!.claude/skills/doc-diagram/`，注释里的目录名漂了（非 markdown，归 code-health）。 → .gitignore:88 旧句「# 项目级 skill 只放行 diagram/（作图入口，随仓库走）；其余 .claude/skills/ 是个人的」→ 新句「# 项目级 skill 只放行 doc-diagram/（作图入口，随仓库走）；其余 .claude/skills/ 是个人的」
- F533 :80 · STALE · 注释说「只放行 .claude/commands/」「skills / settings 是个人配置，不入库」，路径还写 docs/{doc,code}-health-review.md（现在在 docs/ai-eng/ 下）。紧跟的规则其实另外放行了 .claude/settings.json、.claude/hooks/ 和 .cla → .gitignore:81-82 旧句「# Claude 工作流工具（个人/工作流，非本项目框架代码）——只放行 .claude/commands/：那是复盘方法\n# （docs/{doc,code}-health-review.md）的 Claude Code 入口、属项目资产；skills /

### `cli/gherkai_cli/__main__.py`（11）
- F120 :2786 · STALE · 注释说「cloud 下 <report_dir>/<run_id>/ 只是 worker 写产物的临时暂存区——产物已上传 S3、worker 已 rmtree 各自子目录」，Fargate 下这个前提不成立（产物在容器里），cloud 分支下 prune_empty_dirs 实际一直是 no-op；交 code-health 判断这个 → cli/gherkai_cli/__main__.py:2787-2788 旧：『# cloud 模式：清理本地 run 根的空壳（ADR 0029）。cloud 下 <report_dir>/<run_id>/ 只是 worker 写产物的临时 # 暂存区——产物已上传 S3、worker 已 r
- F132 :2710 · STALE · 注释「on_event（sink_lock 外，收 ScopeStarted 刷 RUNNING+血缘…）」漏了非 attempted 的 SessionOpened 也会刷 RUNNING（ADR 0051 决策 4，persist.py:97）。 → cli/gherkai_cli/__main__.py:2711 旧：『#   on_event（sink_lock 外，收 ScopeStarted 刷 RUNNING+血缘，不阻塞别 worker 进度显示）』 → 新：『#   on_event（sink_lock 外，收 ScopeStart
- F189 :1664 · STALE · `_cloud_skew_gate` docstring 写「WebUI/推进器都调用它」，与 0037 :168 是同一个失实说法：推进器从不调用 `check_backend_skew`、也不读 SSM 版本戳，WebUI 不存在（归 code-health）。 → cli/gherkai_cli/__main__.py:1664 旧：『读戳 + 判定住产品本体（`compose.check_backend_skew`，第三元即戳；WebUI/推进器都调用它，措辞单点），』 → 新：『读戳 + 判定住产品本体（`compose.check_backend_ske
- F199 :1735 · STALE · `_worker_meta_fields` docstring「走 serialize 的 omit-when-None」已过时：现行序列化键集固定、None 写 null（core/gherkai_core/serialize.py:430）。 → cli/gherkai_cli/__main__.py:1735 旧：『空 dict（理论上不会有：plan 至少产一个 job）→ 两个字段都 None，走 serialize 的 omit-when-None。』 → 新：『空 dict（理论上不会有：plan 至少产一个 job）时两个字段都为
- F340 :352 · STALE · `--profile` 的 help 写的是「（--profile > AWS_PROFILE）；喂 store + subprocess worker」：漏了配置文件 `[common] profile` 这一层（settings.py 的 ENV_LAYER_OPTIONS 含 profile），「喂」「store」是口语和内部用语， → cli/gherkai_cli/__main__.py:352 旧：『AWS profile（--profile > AWS_PROFILE）；喂 store + subprocess worker（其 region 字段也作 --region 兜底）』 → 新：『AWS profile（依次取本参
- F394 :2509 · STALE · 注释「SIGTERM 直杀的极端泄漏由 ngrok 进程可见性兜」已过时，原因同上：SIGTERM 在执行期间被中断处理器接住，atexit 会拆隧道。 → cli/gherkai_cli/__main__.py:2509 旧：『#     跟 CLI 进程走——atexit 拆（正常结束/Ctrl-C 都收；SIGTERM 直杀的极端泄漏由 ngrok 进程可见性兜）。』 → 新：『#     跟 CLI 进程走——atexit 拆（正常结束、Ctrl
- F412 :256 · STALE · --max-concurrency 的 help「并发只改同时开几个浏览器会话」没有覆盖设备目标的远程访问会话（产品面文案，属 code 侧） → cli/gherkai_cli/__main__.py:256 旧：『并发只改同时开几个浏览器会话、不改 job 数与总费用，』 → 新：『并发只改同时开几个会话（桌面目标是云端浏览器会话，设备目标是 Device Farm 远程访问会话）、不改 job 数与总费用，』。docs/user-guid
- F543 :437 · STALE · submit parser 处的注释「cloud submit 只写 runs 表、不碰 SSM/ECS（ADR 0034）」与 _submit_cloud 实际读 SSM（版本戳、variant 映射、Device Farm 项目）且对 ECS 做 preflight 不符，同文件 L1797-1801 的注释才是准确权限面（code- → cli/gherkai_cli/__main__.py:437 旧：「# 注：submit 不收 --subnet/--security-group——cloud submit 只写 runs 表、不碰 SSM/ECS（ADR 0034），」 → 新：「# 注：submit 不收 --subnet/
- F642 :2156 · STALE · _explain_read_evidence 的 except 注释写「文件不在（云端后端 flush 前被杀）」，但两个 worker 的 evidence.json 都是先经 to_report_ref / toReportRef 同步上传、再随 step_done 发出 ref，flush 前被杀不会让有指针的 evidence.j → cli/gherkai_cli/__main__.py:2157 旧：「except Exception:  # 文件不在（云端后端 flush 前被杀）/ 权限 / 不是 JSON：一律归「读不到」」 → 新：「except Exception:  # 文件或对象不在（如产物被手动清理）/ 无权限
- F685 :256 · STALE · run 的 --max-concurrency 帮助文本「并发只改同时开几个浏览器会话」未覆盖设备 scope 的远程访问会话（用户可见字符串，交 code-health） → cli/gherkai_cli/__main__.py:256 旧：「并发只改同时开几个浏览器会话、不改 job 数与总费用，」 → 新：「并发只改同时开几个会话（桌面目标是浏览器会话，设备目标是远程访问会话）、不改 job 数与总费用，」；同句另两处同改：cli/gherkai_cli/setti
- F756 :2509 · STALE · 注释「SIGTERM 直杀的极端泄漏由 ngrok 进程可见性兜」已过时：SIGTERM 现在由 _InterruptState 协作处理，atexit 会照常执行 → cli/gherkai_cli/__main__.py:2509 旧：「#     跟 CLI 进程走——atexit 拆（正常结束/Ctrl-C 都收；SIGTERM 直杀的极端泄漏由 ngrok 进程可见性兜）。」 → 新：「#     跟 CLI 进程走——atexit 拆（正常结束/Ctrl

### `cli/gherkai_cli/render.py`（1）
- F816 :681 · CONTRADICTION · 条件 sc[status] in (error, aborted) and sc[error_type] 里 aborted 那一半永不成立：aborted 的 error_type 恒为 None（core/gherkai_core/project.py:526）。ADR 0042:111 与 artifacts-and-evidenc → 1) cli/gherkai_cli/render.py:681 旧：`if (sc["status"] in ("error", "aborted") and sc["error_type"]) or not sc["has_step_records"]:` → 新：`if (sc["status

### `cli/pyproject.toml`（1）
- F516 :6 · STALE · PyPI 摘要 description「用 Gherkin .feature 驱动 AI 浏览器测试（Nova Act / Midscene），本机或 AWS 云端执行」没提 1.5 的真机目标，与 README 门面句不一致（低优先） → cli/pyproject.toml:5：description = "gherkai 命令行：用 Gherkin .feature 驱动 AI 浏览器测试（Nova Act / Midscene），本机或 AWS 云端执行" → description = "gherkai 命令行：用 Gherk

### `cli/tests/test_main.py`（2）
- F061 :1310 · DEADLINK · docstring 写「退出码语义见 ADR 0021」，但 0021 是已被 0022 取代的 cucumber 本地补丁 ADR，与退出码无关，是错指针。同文件邻近 code 注释把退出码分层指向 ADR 0030 决定七（cli/gherkai_cli/__main__.py:1143）和 ADR 0031 决定五（:2813），应 → cli/tests/test_main.py:1310 docstring：「（退出码语义见 ADR 0021）」→「（退出码分层见 ADR 0030 决定七）」
- F070 :2997 · STALE · 测试 docstring 写「提示会话可能未释放、用 doctor 核对」，但实现（cli/gherkai_cli/__main__.py:2821）与 ADR 0024 第 197 行都写明提示指向 AWS 控制台、不指向 doctor（测试 docstring，归 code-health）。 → cli/tests/test_main.py:2998 docstring：「再次中断（级别 2）：提示会话可能未释放、用 doctor 核对。」→「再次中断（级别 2）：提示会话可能未释放、到 AWS 控制台核对（设备目标看 Device Farm，桌面目标看 AgentCore）。」

### `core/gherkai_core/adapters/_atomic.py`（1）
- F134 :8 · DEADLINK · 「（读面不持 `.runstate.lock`，只写面互斥；ADR 0030 决定四 / 0034）」：原子写与并发读者那段在 0030 决定三的引用块（:142-151），不在决定四。 → core/gherkai_core/adapters/_atomic.py:8「（读面不持 `.runstate.lock`，只写面互斥；ADR 0030 决定四 / 0034）。」→「（读面不持 `.runstate.lock`，只写面互斥；ADR 0030 决定三 / 0034）。」；core/

### `core/gherkai_core/adapters/event_log/sqlite.py`（2）
- F168 :16 · STALE · 模块 docstring 写「也可能 status --wait 另进程读……跨进程写并发不在 local 目标内」，和 ADR 0034 第 123 行冲突：那里写的是接力者会自己 spawn worker、写同一个 SQLite，可以和活着的 per-run 进程同时推进，跨进程写由 WAL 写锁串行化。属于 code 注释，交 co → core/gherkai_core/adapters/event_log/sqlite.py:15-16 旧：「并发：detached 下 per-run 进程写、reconciler 读（同进程内两职责，也可能 status --wait 另进程读）；同步 run 下 schedule 的各 wo
- F169 :12 · STALE · exits 表注释写「NULL 表示退出码未知，仅超时处置直写时出现」，但 runtime/gherkai_runtime/detached.py:120-124 在 handle.wait() 抛异常时也写 None。core/tests/test_sqlite_event_log.py:53 的 docstring 措辞相同。交 co → ① core/gherkai_core/adapters/event_log/sqlite.py:12 旧：「exit_code（NULL 表示退出码未知，仅超时处置直写时出现；投影判 ERROR、非宽限）」 → 新：「exit_code（NULL 表示退出码未知：超时处置直写时，以及本机宿主未能取

### `core/gherkai_core/adapters/subprocess_engine.py`（1）
- F802 :231 · STALE · 注释「正非零表示 worker 自行异常退出（崩溃 / 会话清理失败的 1 / 网络故障的 80）」同样漏了 Nova steps 加载失败的 2（云端镜像里 steps 加载失败时，job 模式会以 2 退出） → core/gherkai_core/adapters/subprocess_engine.py:231 旧句：「正非零表示 worker 自行异常退出（崩溃 / 会话清理失败的 1 / 网络故障的 80）；」→ 新句：「正非零表示 worker 自行异常退出（崩溃 / 会话清理失败的 1 / Nov

### `core/gherkai_core/errors.py`（1）
- F801 :12 · STALE · WorkerExitError 的 docstring 写「正码是 worker 自报（崩溃 / 会话清理失败的 1 / 网络故障的 80）」，没列 Nova worker 使用方 steps 加载失败时的 `EX_STEPS_LOAD = 2`（engines/novaact/gherkai_worker_novaact/user_st → core/gherkai_core/errors.py 的 WorkerExitError docstring：旧句「`wire.raise_for_worker_exit` 把非零退出码翻成本异常（两个 Engine adapter 共用），`exit_code` 带原码：正码是 worker 自

### `core/gherkai_core/model.py`（2）
- F098 :249 · STALE · ReportRef docstring 的 kind 约定值只列 report / trajectory / summary / evidence，漏了已实装的 device_session（engines/midscene/src/device/device-session.mts:116）；这是 code 注释，归 code-heal → core/gherkai_core/model.py 的 ReportRef docstring。旧："summary"（数字汇总）/"evidence"（gherkai 自有 schema 的 step 级机读证据，ADR 0042 决策一），            未来可 "video"/"tr
- F147 :186 · CONTRADICTION · `_NON_VERDICT` 注释「此处过滤**承重**——否则前置态会污染 run 级 status」不成立（code-health 侧）。 → ① core/gherkai_core/model.py:191-193。旧：# 两路共用（ADR 0031 决定三 / 0034）：schedule 沿事件流实时聚合，喂的都是终态、过滤是 no-op； # project 的无状态投影真实喂入 pending/running（未起/正在运行的 j

### `core/gherkai_core/persist.py`（3）
- F128 :8 · STALE · 模块 docstring 写「它经 sink / on_job_complete 两个回调把事件/JobResult 喂给本服务」，实际注入点是 on_event / on_job_complete，sink 已不再被 persistence 装饰（ADR 0030 决定二末注、persist.py:42 自己也这么写）。 → core/gherkai_core/persist.py:8-9 「schedule 一行不碰 store——它经 sink / on_job_complete 两个回调把事件/JobResult 喂给本服务（ADR 0026/0030）。」 → 「schedule 一行不碰 store——它经 o
- F129 :16 · STALE · 「（经 on_job_complete，as_completed 串行）」以及 :110「主线程 as_completed 串行 fire」：主线程收集循环已改为 wait(FIRST_COMPLETED)（schedule.py:522）。 → core/gherkai_core/persist.py:16 「（经 on_job_complete，as_completed 串行）。」 → 「（经 on_job_complete，在 schedule 等待 job 完成的循环里串行调用）。」；core/gherkai_core/persist
- F823 :0 · STALE · code 注释 / docstring 与 ADR 现状不一致（落地收口时核出） → :90 docstring「取设备期间 job 即算 RUNNING」→「scope_started 之前的准备期 job 即算 RUNNING」（可选）

### `core/gherkai_core/ports.py`（2）
- F130 :90 · STALE · JobSink 注释「schedule 在 as_completed 主线程串行 fire」：收集循环已改为 wait(FIRST_COMPLETED)（schedule.py:522，ADR 0024:197）。 → core/gherkai_core/ports.py:90 "# schedule 在 as_completed 主线程串行 fire，故实现无需自己加锁。" → "# schedule 在主线程等待 job 完成的循环（`wait(FIRST_COMPLETED)`）里串行 fire，故实现无需自
- F306 :13 · STALE · 模块 docstring 写 EventLog / Launcher「只服务无状态推进路径」，已过时：同步 run 经 EventRecordingEngine 往 SqliteEventLog 落事件流，explain 读 EventLog（本机读 SqliteEventLog，云端读 DdbEventLog），ADR 0016:111 → core/gherkai_core/ports.py:13-15 "**另两个 port 不在本模块**：`EventLog` 与 `Launcher` 定义在 `reconcile.py`、与消费它们的 reconciler 同处——\n只服务无状态推进路径，与本模块那批「同步 `run` 也用」

### `core/gherkai_core/project.py`（1）
- F148 :698 · CONTRADICTION · `_aggregate` 的 docstring 写「防未来引入主动 skip 时全-skipped run 被误判 passed」，但全 skipped 过滤后为空，照样返回 PASSED（code-health 侧）。 → ① core/gherkai_core/project.py:699-700 docstring：旧「把正确性钉在函数内、不依赖「skipped 必伴随 error」的外部不变量（防未来引入主动 skip 时     全-skipped run 被误判 passed）。」→ 新「过滤后为空（全 sk

### `core/gherkai_core/schedule.py`（4）
- F089 :232 · STALE · `_Worker.run` docstring 写「重试门槛（双条件 AND，绝不放宽）」，但 code（第 251-256 行）已是三条件，多了 `not is_device_job(self.job)`（ADR 0028 第 111 行、0051 决策 2），注释落后于 code。 → core/gherkai_core/schedule.py `_Worker.run` docstring：「重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error 失败（worker 建连失败、         重试耗尽）② 「会话未起」指本次零 step_done（证明 a
- F090 :132 · STALE · ScheduleOpts 的 network_retry 注释「仅对 error_type==network_error 且『会话未起（零 step_done）』的 job 重试」漏了「job 目标不是设备」这一条件。 → core/gherkai_core/schedule.py ScheduleOpts：「# 网络瞬时故障的 job 级重试（ADR 0028）：仅对 error_type==network_error 且「会话未起（零 step_done）」     # 的 job 重试整批。」→「# 网络瞬时故障
- F091 :7 · STALE · 模块 docstring「同时活的 AgentCore 会话数」只覆盖桌面目标；设备 job 占的是 Device Farm 远程访问会话。 → core/gherkai_core/schedule.py 模块 docstring：「同时运行的 worker 数（也就是同时活的 AgentCore 会话数，保护 AWS 配额与峰值消耗）。」→「同时运行的 worker 数（也就是同时在用的云端会话数：桌面目标为 AgentCore 浏览器会话
- F703 :317 · STALE · 注释「已过 deadline / 已被 fail-fast 中止的照常按首次仲裁落定」以及 L275、L297、L398 同类注释只写 fail-fast，可 abort_flag 也由使用方中断（_stop_all("interrupt")）置位，代码也按 abort_flag.cause 区分了两者，注释与代码不一致（交 code-h → core/gherkai_core/schedule.py 下列各处同改： 1) 模块 docstring：「超时/fail-fast 用**事件间检查**：」→「超时与整批中止（fail-fast 或使用方中断）用**事件间检查**：」 2) _Worker.run 内注释：「+ 未被 fail-

### `core/gherkai_core/wire.py`（2）
- F067 :84 · DEADLINK · `job_to_json` 的 docstring 引用的节名「job 行的结构版本与固定键集」在 ADR 0024 里不存在，现节名是「协议版本与 job 行的固定键集」（code 注释，归 code-health）。 → core/gherkai_core/wire.py:84：「键集固定（ADR 0024「job 行的结构版本与固定键集」、0048 决策 3）」→「键集固定（ADR 0024「协议版本与 job 行的固定键集」、0048 决策 3）」。另外几处同样的旧名一起改：core/tests/test_wir
- F106 :248 · STALE · EX_WORKER_NETWORK 的注释写「建连早于任何事件 emit，无法走事件通道」，1.5 起各 attempt 先发 session_opened，准确的理由是「建连失败不发能承载原因的判定事件」（0028:76 已改，code 注释没跟；归 code-health） → core/gherkai_core/wire.py:248：「# worker 网络故障专用退出码：建连失败、重试耗尽时 worker 以这个退出码退出（建连早于任何事件 emit，无法走事件通道）。」→「# worker 网络故障专用退出码：桌面 worker 建连失败、重试耗尽时以这个退出码退出

### `core/tests/test_lifecycle_states.py`（1）
- F149 :98 · CONTRADICTION · 测试名 `test_aggregate_all_skipped_no_error_not_misjudged_passed` 断言的却是 `== Status.PASSED`，名实相反（code-health 侧）。 → core/tests/test_lifecycle_states.py L98-99： 旧：`def test_aggregate_all_skipped_no_error_not_misjudged_passed():` 新：`def test_aggregate_all_skipped_filt

### `core/tests/test_stores.py`（1）
- F198 :569 · STALE · docstring「None 省键（本机后端 / 旧落盘）」已过时：serialize.run_meta_to_dict 键集固定、None 写 null（serialize.py:430，0037 决策 7）。同文件 :530、:548 的「None 省键」同样过时。 → core/tests/test_stores.py 共 5 处： 1) :513 `# RunMeta.extra_http_headers（ADR 0035 决策 4）：非空往返不丢；None/空表均省键（旧落盘兼容 + 空即无）` → `# RunMeta.extra_http_headers（

### `deploy_aws/gherkai_deploy_aws/cli.py`（1）
- F664 :468 · DEADLINK · destroy docstring 写「残留清单见 README」，但完整的残留清单与清理步骤在 docs/user-guide/cloud-backend.md「拆除与清理」节，deploy_aws/README.md 只有一句。指针不准。 → deploy_aws/gherkai_deploy_aws/cli.py:468 `"""销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。` → `"""销毁 stack。**表/桶/ECR 是 `RETAIN`、不随

### `deploy_aws/gherkai_deploy_aws/stack.py`（4）
- F155 :97 · DEADLINK · docstring 写「解法见 ADR 0032 grace 预算条」，但 0032 里没有叫「grace 预算条」的节或条，对应内容是「真容器校准结论」节的结论 4（grace 下限 vs stopTimeout 的冲突），指针应改为「ADR 0032 结论 4」。 → deploy_aws/gherkai_deploy_aws/stack.py（_resolve_stop_timeout docstring）：「（Nova grace 下限 150s>120s 的冲突正卡在这条硬上限上，解法见 ADR 0032 grace 预算条。）」→「（Nova grace 
- F164 :491 · STALE · 注释「Fargate 用的默认安全组」与实际不符：这是本 stack 新建的出站专用 WorkerSg，不是 VPC 的 default SG。上一轮已按同一理由改了 0033 L80；runtime/gherkai_runtime/compose.py:1118 docstring「sg 写默认 SG id」同样需要改。 → ① deploy_aws/gherkai_deploy_aws/stack.py（_ssm_network）：「# Fargate 用的默认安全组（出站全开、入站无——worker 只出不入）。」→「# worker task 缺省用的安全组（未给 --security-group 时经 SSM 读
- F572 :767 · CONTRADICTION · 注释写 typing_extensions 是「`gherkin-official>=42` 的传递依赖」。PyPI 元数据显示 gherkin-official 自 31.0.0（core 声明的下限）起就声明 `typing_extensions>=4`，「>=42」把适用范围说窄了，与 deploy_aws/DEVELOPMENT. → deploy_aws/gherkai_deploy_aws/stack.py（LAMBDA_ASSET_PACKAGES 上方注释）：「它是 `gherkin-official>=42` 的传递依赖（`gherkin/parser_types.py` 无条件」→「它是 `gherkin-offici
- F573 :255 · STALE · _network 注释写私有隔离时要同步「cli assignPublicIp=DISABLED」。实际取值点是 gherkai_runtime.compose.resolve_network 的缺省值和推进器的 ASSIGN_PUBLIC_IP env（lambdas/reconciler.py:368），注释只点名 cli 一处（与本 → deploy_aws/gherkai_deploy_aws/stack.py： ① _vpc 建新分支注释：「与 _worker_subnet_ids 的         # 「公有子网优先」及 cli assignPublicIp=ENABLED 一致」→「与 _worker_subnet_ids

### `deploy_aws/gherkai_deploy_aws/workers.py`（1）
- F661 :18 · STALE · 模块头写「删 revision 前有两个前置条件」，cleanup_pass 的 docstring（L436）也写「删的两个前置条件」，但实现（L458-462）还有第三个条件：仍被任何版本 worker-image 映射引用的已退休 revision 不删（ADR 0038 不变量「退休 ≠ 可删」）。注释与实现不一致，交 code- → workers.py:18「- **删 revision 前有两个前置条件**：退休满 `RETIRE_QUIET_PERIOD` + 无未到终态的 run 引用（`cleanup_pass`）。」 → 「- **删 revision 前有三个前置条件**：退休满 `RETIRE_QUIET_PER

### `engines/fixtures/redaction-cases.json`（1）
- F919 :2 · STALE · _comment 写「消费者：core/tests/test_redact.py、engines/novaact/tests/test_redact.py、engines/midscene/src/worker/redact.test.mts」，但 git grep 显示还有 engines/midscene/src/device/wdi → engines/fixtures/redaction-cases.json 的 _comment：旧「消费者：core/tests/test_redact.py、engines/novaact/tests/test_redact.py、engines/midscene/src/worker/reda

### `engines/midscene/package.json`（1）
- F521 :4 · STALE · npm 包 Summary「用 Amazon Bedrock 上的视觉模型在云端浏览器里做 UI 自动化」没跟上 1.5 的 Device Farm 真机执行（这是上 npm 页面的使用者文本，受 test_package_summaries 管）；cli/pyproject.toml 第 5 行的 description「用 Gherk → engines/midscene/package.json:4：「gherkai 的 Midscene 引擎 worker：由 gherkai 命令行拉起，用 Amazon Bedrock 上的视觉模型在云端浏览器里做 UI 自动化」 → 「gherkai 的 Midscene 引擎 worker：

### `engines/midscene/spikes/01-model-sigv4.ts`（1）
- F691 :5 · STALE · 文件头的运行命令「cd engines/midscene && node_modules/.bin/tsx spikes/01-model-sigv4.ts」没有 AWS_REGION 前缀，而同文件第 8 行写着「spike 直接运行时带 AWS_REGION=... 前缀」，getRegion() 在 region 未设时直接抛错。D → engines/midscene/spikes/01-model-sigv4.ts:5 旧句「// 运行：cd engines/midscene && node_modules/.bin/tsx spikes/01-model-sigv4.ts」 → 新句「// 运行：cd engines/mids

### `engines/midscene/spikes/03-midscene-grounding.ts`（1）
- F690 :61 · STALE · 注释「关键（源码 agent.js:852-853）：一旦给 Agent 传 createOpenAIClient，它就切到「隔离 ModelConfigManager」」是 1.9.8 的语义。1.15.1 里只给 createOpenAIClient 会走 AgentScopedModelConfigManager、仍读 env，给  → engines/midscene/spikes/03-midscene-grounding.ts 第 61-63 行 旧： // 关键（源码 agent.js:852-853）：一旦给 Agent 传 createOpenAIClient，它就切到「隔离 ModelConfigManager」， /

### `engines/midscene/spikes/04-planning-probe.ts`（1）
- F033 :3 · DEADLINK · repo 内 code 注释「（调查 P1 挖出的真未知）」用的是过程编号，对未来读者是悬空指代，按 CLAUDE.md 悬空指针红线应改为自明的描述（例如「源码核查发现的」）。 → engines/midscene/spikes/04-planning-probe.ts:3：旧句 `//   因为 Midscene 的 planner 即便不做定位也会无条件附带截图（调查 P1 挖出的真未知）。` → 新句 `//   因为 Midscene 的 planner 即便不做定位也

### `engines/midscene/src/device/limits.mts`（2）
- F268 :128 · CONTRADICTION · code 注释「各段上限以网络退化实测校准后定数（ADR 0049 决策 5）」同样与 ADR 0052 已知缺口不符，交 code-health 按 0049 的改法同步。 → engines/midscene/src/device/limits.mts:129 旧：// 这三段。各段上限以网络退化实测校准后定数（ADR 0049 决策 5）。 新：// 这三段。各段上限按阶段推导取定，未在网络退化条件下校准（到 us-west-2 的丢包无法人工制造，见 ADR 0052
- F279 :0 · STALE · code 注释 / docstring 与 ADR 现状不一致（落地收口时核出） → :37 →「缺省值与上界只在 core 持有一份，由 CLI 读项目配置时填入缺省、校验上界（ADR 0051 决策 2）」

### `engines/midscene/src/device/read-points.test.mts`（1）
- F586 :13 · STALE · 测试文件头注释的透传白名单写「或用 ?? 与 || 给缺省值」「括号、类型断言、非空断言与赋值表达式不改变取值」，漏了 valueUse 实际当作包装穿过的 `&&` 与条件表达式两个分支（:259-262、:286），也没有箭头函数表达式体这个去处；同文件 :274-281 的 docstring 写全了。头注释与实现不一致，交 cod → engines/midscene/src/device/read-points.test.mts 头注释（第 12-16 行，改后按原宽度重新折行）：旧句「读出的值只能原样透传，按白名单判：填进对象字段、数组或模板插值，作变量或字段的初值，以单独成句的赋值写进变量或字段（外面带括号、类型断言或非空断

### `engines/midscene/src/lib/agentcore-sigv4.mts`（3）
- F694 :8 · CONTRADICTION · 模块头先列出两套签名场景（模型连接与 CDP 升级），然后写「签名契约与失败模式的机理解读见 docs/internals/midscene-bedrock-sigv4-signing.md」，但该页只讲模型连接（service bedrock），不涉及 signCdpUpgrade（service bedrock-agentcore）。 → engines/midscene/src/lib/agentcore-sigv4.mts:8 旧句：`// 签名契约与失败模式的机理解读见 repo 里的 docs/internals/midscene-bedrock-sigv4-signing.md（不随包发行），决策见 docs/adr/000
- F726 :64 · STALE · 用户可见的报错文案里引的 https://midscenejs.com/model-common-config.html 已改名为 https://midscenejs.com/model-api-setup（旧地址靠重定向还能打开）；改这句时要同步检查断言该文案的测试。 → engines/midscene/src/lib/agentcore-sigv4.mts:64 旧句：`+ `请设 MIDSCENE_MODEL_FAMILY 指明它属于哪个家族（可取值见 Midscene 文档 https://midscenejs.com/model-common-config.
- F032 :0 · STALE · code 注释 / docstring 与 ADR 现状不一致（落地收口时核出） → :87 注释 →「Midscene 的 gpt-5 / gpt-6 family 适配器对定位请求与兼任定位的规划请求（未设独立定位模型且不是 deepThink）固定发它、无配置可关。」

### `engines/midscene/src/resolve-hook.mts`（1）
- F442 :7 · STALE · 头注释「云镜像里恰好能解析——`/app/steps` 上溯命中 `/app/node_modules`」和现行 Dockerfile 的全局安装不符，和上一条 ADR 0037 是同一事实。 → engines/midscene/src/resolve-hook.mts 第 7 行：旧句「// （云镜像里恰好能解析——`/app/steps` 上溯命中 `/app/node_modules`——那是巧合，不能当机制。）」→ 新句「// 云镜像同样不能靠默认解析：基础镜像用 `npm inst

### `engines/midscene/src/worker/deterministic.steps.mts`（1）
- F058 :5 · DEADLINK · code 注释把「ADR 0036「注册即暴露」」当作 0036 的节名引用，但 0036 全文没有这个短语，对应内容在「### 1. 注册面扩元数据（暴露的前提）」。这个指针看似精确、实际对不上，归 code-health。 → engines/midscene/src/worker/deterministic.steps.mts:5：`（元数据必填、缺则 fail-loud——ADR 0036「注册即暴露」），` → `（元数据必填、缺则 fail-loud——ADR 0036 决策 1 与「边界与互链」节），`

### `engines/midscene/src/worker/run-scope.mts`（3）
- F107 :886 · STALE · 注释写「双条件 AND 天然不满足」，schedule 的 job 级重试门槛已是三条件（code 注释，归 code-health） → ① engines/midscene/src/worker/run-scope.mts:885-886：「schedule job 级重试要求「会话未起（零     // step_done）」，此处 step_started 早已 emit、saw_step=True，双条件 AND 天然不满足；
- F183 :356 · STALE · 同上，注释「stdin 一行 JSON 数组（step 文本）」已过时，下一行的类型注释才是 `{keyword, text}[]`。归 code-health。 → ① engines/midscene/src/worker/run-scope.mts:356：「stdin 一行 JSON 数组（step 文本）→ stdout 一行」→「stdin 一行 JSON 数组（每项 `{keyword, text}`，旧版 CLI 给裸字符串）→ stdout 一行
- F877 :409 · STALE · code 注释「timeoutS 只在这里被读，不计时、不自停」已过时：worker/surface-desktop.mts:317 用 browserSessionTimeoutS(deps.job.timeoutS) 设浏览器会话存活上限，交 code-health。 → ① engines/midscene/src/worker/run-scope.mts:409：「（timeoutS 只在这里被读，不计时、不自停）」→「（worker 不据 timeoutS 计时、不自停；此外它只用于桌面实现建会话时推算浏览器会话的存活上限，见 surface-desktop.m

### `engines/midscene/src/worker/surface.mts`（1）
- F585 :30 · STALE · 接缝契约头注释写「读不到的（桌面路径的全部异常）沿用瞬时网络判定」，但 surface-desktop.mts:410 在句柄不适用于桌面浏览器时调用了 attachClassification，桌面路径并非全部异常都不带标记（DEVELOPMENT.md:141 的写法是对的）。属 code 注释漂移，交 code-health。 → engines/midscene/src/worker/surface.mts:30 旧：`// 分类先读这个标记（readClassification）、读到即按它归类，读不到的（桌面路径的全部异常）沿用瞬时网络判定（ADR 0052 决策 6）。` → 新（两行）：`// 分类先读这个标记（re

### `engines/midscene/src/worker/user-steps.mts`（1）
- F757 :3 · STALE · 模块头注释写「目录由组合根解析（`--steps-dir` > env > `./steps`）」，漏了 ADR 0053 加的配置文件 `steps-dir` 一层（CLI 的 `_resolve_steps_dir` docstring 里有） → engines/midscene/src/worker/user-steps.mts:3 旧句「// 契约（约定逻辑**不在这里**）：目录由组合根解析（`--steps-dir` > env > `./steps`）、随 definition 持久化、」→ 新句「// 契约（约定逻辑**不在这里*

### `engines/novaact/gherkai_worker_novaact/__main__.py`（1）
- F600 :8 · CONTRADICTION · 「中间任何包装层都会吞掉 fd3」（__init__.py 第 11–12 行措辞相同）与 ADR 0037 决策 3 记的 uvx 实测穿透不一致，宜改为「包装层可能吞掉 fd3」。 → ① engines/novaact/gherkai_worker_novaact/__main__.py 第 7–8 行：旧句「**本模块不做任何包装**（不起子进程、不改 fd）：worker 进程必须是组合根直接 spawn 的那个进程， `EVENTS_FD` 靠 `pass_fds` 继承（

### `engines/novaact/gherkai_worker_novaact/lib/__init__.py`（1）
- F599 :3 · STALE · 子包 docstring 只说到 job_source / event_sink / artifact_upload / workflow_setup / constants 五个模块，没提后加的 redact、precheck、tunnel_warmup。 → lib/__init__.py 第 1 行：`"""worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。` → `"""worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）及包根共用的辅助模块。`；第 4-5 行：`的建连前置与单一真源常量。

### `engines/novaact/gherkai_worker_novaact/lib/constants.py`（1）
- F014 :21 · CONTRADICTION · 注释里的升级流程「新 GA → 重新运行同一批用例的 A/B → 改本常量 → 发版点明模型换代」与 0004 :33 用的是同一种表述；如果 0004 改为指向 0044 决策 1 的模型评测集，这里的「同一批用例」应一并改成「模型评测集」，否则与 0044 决策 1 的评测集定义不一致。 → engines/novaact/gherkai_worker_novaact/lib/constants.py:21-22 旧句「升级流程（新 GA → 重新运行同一批用例的 A/B → 改本常量 # → 发版点明模型换代）见该 ADR，别在这里改成别名。」→ 新句「升级流程（新 GA → 用模型评

### `engines/novaact/gherkai_worker_novaact/run_scope.py`（2）
- F182 :1196 · STALE · code 注释「stdin 一行 JSON 数组（step 文本）」已过时：现在输入是 `{keyword, text}` 对象数组，裸字符串只作为兼容旧 CLI 的形态（deterministic.py:310）。归 code-health。 → engines/novaact/gherkai_worker_novaact/run_scope.py:1196 「# 批量 match 查询（ADR 0036「4.」，plan 命中标注）：stdin 一行 JSON 数组（step 文本）→ stdout」 → 「# 批量 match 查询（AD
- F876 :1224 · STALE · code 注释「timeoutS 只在这里被读，不计时、不自停」已过时：同文件 1280 行 browser_session_timeout_s(job.get('timeoutS')) 也读它（桌面浏览器会话存活上限，ADR 0024 泄漏兜底条），交 code-health。 → engines/novaact/gherkai_worker_novaact/run_scope.py:1224 「（timeoutS 只在这里被读，不计时、不自停）」 → 「（worker 不按 timeoutS 计时、不自停；除这里的自检外，它只用来设定浏览器会话的存活上限，见 browser_

### `engines/novaact/gherkai_worker_novaact/user_steps.py`（1）
- F598 :3 · STALE · 模块头 docstring 写「`--steps-dir` flag > env > 默认 `./steps` 的解析」，漏了项目配置文件 `steps-dir` 一层（ADR 0053 决策 2）；属 code 注释，交 code-health。 → engines/novaact/gherkai_worker_novaact/user_steps.py:3「`--steps-dir` flag > env > 默认 `./steps` 的解析」→「`--steps-dir` flag > env > 项目配置文件 `steps-dir`（ADR

### `runtime/gherkai_runtime/__init__.py`（1）
- F562 :3 · STALE · 包说明列举产品级知识时只写了 compose / detached / names / tunnel / tunnel_host，没有 devicefarm、app_upload、textui 三个模块。 → runtime/gherkai_runtime/__init__.py 第 3-4 行：旧句「持有产品级知识——引擎注册表与装配（compose）、local 无状态批量运行宿主（detached）、资源命名真源（names）、 隧道与其宿主编排（tunnel / tunnel_host，ADR 0

### `runtime/gherkai_runtime/compose.py`（3）
- F046 :42 · CONTRADICTION · 代码注释「prefix 含分隔符、原样拼（使用方负责，防粘连——同 S3 prefix 先例）」和 0033:65 一样搞错了先例：S3 key 前缀其实由 `_normalize_prefix`（:831）补 `/`，不是原样拼。注释归 code-health 处理。 → runtime/gherkai_runtime/compose.py:42 旧：「prefix 含分隔符、原样拼（使用方负责，防粘连——同 S3 prefix 先例）。」→ 新：「prefix 自带分隔符、按原样拼接（分隔符由使用方负责，不带分隔符的 prefix 会与基名粘连）；这与 S3 key
- F133 :1710 · STALE · is_botocore_error docstring 写「cli 主依赖不含 boto3」，已被 ADR 0037 决策 2c 反转（cli/pyproject.toml:31-34 硬依赖 gherkai-runtime[aws]）。 → runtime/gherkai_runtime/compose.py:1710-1711 旧：「惰性 import botocore（cli 主依赖不含 boto3，顶层 import 会在纯 local 环境炸；且只在 cloud 路径才会调到     这里）。缺 botocore（不该发生，能走
- F190 :1326 · STALE · `check_version_skew` docstring 写「它靠 2b 的 `dirty=true`/`metadata=true` 保证」，与 ADR 0037 决策 2b 相反：2b 明定 metadata 用默认、显式 `metadata = true` 是被拒方案；各 pyproject 的注释也写的是默认（归 code-h → runtime/gherkai_runtime/compose.py:1326-1327 旧：「（判据 `is_pure_release` 与定位链第四级共用——它靠 2b 的 `dirty=true`/`metadata=true`        保证「非纯净构建一定带 `+`」才可靠）。」→ 新

### `runtime/gherkai_runtime/detached.py`（1）
- F560 :33 · STALE · 注释写「今值 midscene 31s / Nova 150s」，但 Midscene 的 minGraceSeconds 现在取桌面与设备两条收尾路径里较大的那个，按当前常量是 63.5 秒（engines/midscene/src/worker/run-scope.mts:108-123），31 秒只是桌面那一条。 → runtime/gherkai_runtime/detached.py 第 32-33 行：旧句「各引擎 worker 经自述入口 `--capabilities` 自报、compose.engine_min_grace 只查询聚合；今值 # midscene 31s / Nova 150s）」→ 

### `runtime/gherkai_runtime/tunnel.py`（1）
- F887 :216 · STALE · 注释「前台 run 方式语义不变：Ctrl-C → KeyboardInterrupt → atexit 拆」的机制已过时：执行期间 Ctrl-C 走中断标志，不再抛 KeyboardInterrupt。 → runtime/gherkai_runtime/tunnel.py:216-217 旧句：             # 守护进程，两个宿主本身也都 setsid）。前台 run 方式语义不变：Ctrl-C → KeyboardInterrupt → atexit             # 拆（决策

### `runtime/gherkai_runtime/tunnel_host.py`（1）
- F561 :7 · STALE · 模块头写的是「起隧道 → 映射 definition → 给出隧道模式恒注入的额外请求头」，漏了同时给出的会话预热地址（同文件 TunnelSetup docstring :44-46 写的是四件产物）。 → runtime/gherkai_runtime/tunnel_host.py:7 旧句：「- `start_tunnel_for_jobs`：起隧道 → 映射 definition → 给出隧道模式恒注入的额外请求头（决策 1/2/4）。」→ 新句：「- `start_tunnel_for_jobs

### `skills/gherkai-evals/fixtures/android-app/steps/url_matches.mts`（1）
- F766 :4 · CONTRADICTION · fixture 的 step 模板头注释写「运行时经 `--steps-dir features/steps` 或环境变量」，是从仓库 features/steps/ 原样拷来的。fixture 里 steps 在 `steps/`，靠缺省的 ./steps 自动加载；无 skill 臂照注释传 `--steps-dir features → 同一处改动落到 8 个文件。  (1) 四个 .mts：skills/gherkai-evals/fixtures/android-app/steps/{url_matches.mts,restart_app.mts}、ios-app/steps/{url_matches.mts,restart_a

### `skills/gherkai-evals/summarize_runs.py`（1）
- F235 :6 · STALE · 模块 docstring 写「baseline 臂的 repo_touches / skill_copy_touches 非零即污染样本」，同文件 :65-67 的实现却是任何臂触仓库都算污染、只有触 skill 副本限于 baseline（ADR 0043 :80 与 code 一致），docstring 是旧口径（code 注释，归  → skills/gherkai-evals/summarize_runs.py:6 旧句「baseline 臂的 repo_touches / skill_copy_touches 非零即污染样本，先隔离再谈通过率；network_calls 非零说明结果依赖活网、不可重放。」→ 新句「任何臂的 re

### `tools/build_diagrams.mjs`（2）
- F248 :3 · CONTRADICTION · 头注释写「Pages 上暴露的就是它，CI 也运行同一条命令」，但没有任何 workflow 运行 archify 或 build_diagrams（grep .github 零命中）。pages.yml 头注释写「不做任何构建」，只原样上传 docs/diagrams；ADR 0045 决策七还把「CI 由 JSON 现场渲染 HTML → tools/build_diagrams.mjs:3 旧：`//   ① 渲染  JSON 图源 --archify deliver--> 可交互 HTML   纯 CLI、确定性、无 LLM；Pages 上暴露的就是它，CI 也运行同一条命令` → 新：`//   ① 渲染  JSON 图源 --
- F739 :14 · STALE · 注释说「archify skill 升级后这些名字可能变……届时对照新版 HTML 改这两处即可」。实测 archify 3.2.0 的 viewer 选择器（button[data-format]、data-last-export-*）仍在，真正的断点在第 51 行的 deliver：图源缺 meta.output，每张图 exit 1 → tools/build_diagrams.mjs:14 旧：`//   archify skill 升级后这些名字可能变——脚本会响亮失败（找不到按钮 / 回执不符），届时对照新版 HTML 改这两处即可。` → 新：`//   archify skill 升级后这些名字可能变——脚本会响亮失败（找

### `tools/e2e_harness.py`（2）
- F779 :12 · STALE · docstring 说「忠实复现 SubprocessEngine adapter 的 spawn 环境」，但 adapter 现在还注入 GHERKAI_PARENT_PID 并以 process_group=0 启动 worker（core/gherkai_core/adapters/subprocess_engine.py:137、 → tools/e2e_harness.py 第 12 行：「忠实复现 SubprocessEngine adapter 的 spawn 环境（自建 events pipe + EVENTS_FD、」→「复现 SubprocessEngine adapter 的 spawn 环境（自建 events p
- F780 :28 · STALE · docstring「宿主 export 的 GHERKAI_* 一律不生效」说得太宽：scrubbed_environ 只清五个组合根拥有的键，GHERKAI_WORKER_<ENGINE>_CMD 与 GHERKAI_PARENT_PID 照常继承（与手册第 18 行是同一个问题）。 → tools/e2e_harness.py 第 27-28 行：「  # --steps-dir: 使用方确定性 step 目录（ADR 0037 决策 4），也可经环境变量 HARNESS_STEPS_DIR 给；不给则显式清空，\n  #              **宿主 export 的 GH

## 三、第九轮落地时顺手改过的 code 文件（已随「code 连带」提交，code-health 只需知悉）

- `cli/gherkai_cli/__main__.py` doctor 行三句「未查：…」的用户可见文案改为书面写法；`deploy_aws/gherkai_deploy_aws/cli.py` 与 `container.py` 的用户可见提示同类改写；`cli/tests/_doc_rules.py` 退役词表加「部署者」（与 CONTEXT 词条 _Avoid_ 同源）；`tools/image_token_probe.mts` 头注释与手册一致；`tools/build_diagrams.mjs` 适配 archify 3.x。
