> 类型: 调查记录

# 写回时去掉的注释指针：实装跟上之后加回

这次重新设计写回各篇 ADR 之后，code 还没有改。注释、文档串与各包技术文档里有一批 ADR 指针，所括的说法是现在 code 的行为，而所指的小节现在写的是目标设计。按 [0018](./0018-run-ownership-adr-writeback-plan.md)「另一家模型核落到位」里定的规则，这些指针已经去掉，对现在行为的说明保留。

下面按文件列出每一处：所在的函数、类、测试或文档小节，它当时所括的说法，以及这段 code 跟上目标设计之后应当对应的 ADR 小节。实装批改到某个文件时，把说明改成新行为，并照这里把指针加回去；标「无对应」的是随那段 code 一起删去的。做完一个文件就从这里删掉它的条目。没有去掉的指针是否与所指小节的现文一致，随实装核对，范围与清单在文末「语义一致随实装核对」一节；两部分都清空后本文删除。

- `cli/DEVELOPMENT.md`
  - 「为何拆 submit / status」节第二段：status --wait 是三个推进触发源之一，查询者到来即接力，推进中断后由查询者续到底。跟上之后对应 0034「命令形态」「推进器与触发源」；0054 决策八。
- `cli/gherkai_cli/__main__.py`
  - _add_config_flag 文档串：读项目配置文件的子命令有八个，名单在 settings.CONFIG_COMMANDS。跟上之后对应 0053 决策 1。
  - _build_parser，status 的 --wait 选项上方注释：status --wait 接力：本机在本进程 tick 推进，云端 invoke kicker，以此保持 status 机器零 ECS 权限。跟上之后对应 0034「推进器与触发源」第 2 条与「命令形态」；0054 决策八。
  - _submit_local，build_local_stores 的 detached 参数行注释：run_state.json 的 detached 标记让 status --wait 认它可以接力。跟上之后对应 0034 端到端 cloud 第 1b 步「触发过滤不看后台执行标记」（标记只进 list-runs --json 的 detached）。
  - _submit_cloud，资源 preflight 上方注释：链上任一 Lambda 缺失时 run 永不推进或收敛（kicker 缺卡在 pending、reconciler 缺无人接力、exit-observer 缺断链），所以要挡在提交前。跟上之后对应 0033「preflight fail-fast」节「task-def 与事件驱动链 Lambda 已纳入 preflight」条。
  - _submit_cloud，build_cloud_stores 的 detached 参数行注释：STATE 带 detached 标记，kicker 的过滤据此识别冷启动。跟上之后对应 0034 端到端 cloud 第 1b 步；过滤写法见 0054 决策九第 1 条。
  - _render_status 文档串，relay_available 一段：只有 detached run 能被 --wait 接力。跟上之后对应 0034「命令形态」节「不带 --wait 的 status」条（提示只看记录与期限）。
  - _cmd_status 文档串末段：--wait 的等待或接力被 Ctrl-C 打断时打一句说明、以 130 结束，不让回溯到终端。跟上之后对应 0031 决定五（status --wait 被 Ctrl-C 打断为 130）与 0039。
  - _status_cloud，接力 invoke kicker 的异常处理注释：status --wait 接力时 kicker 不存在即点名 prefix 并 fail-fast。跟上之后对应 无对应小节：实装后这段接力调用不再存在，status --wait 的处置见 0054 决策八。
- `cli/gherkai_cli/render.py`
  - 「run 清单（list-runs …）」节标题注释：下面的 list-runs 渲染就是 0041 决策七的人读形态与机读形态，包括前台执行遗留提示与按 detached 判断。跟上之后对应 0041 决策七「人读形态」「机读形态」。
  - render_run_list 文档串：job 级的原因不在运行态里，清单不列，用 explain 看。跟上之后对应 0041 决策七「人读形态」中「清单不给 job 没通过的原因」一段。
- `cli/gherkai_cli/settings.py`
  - 模块级注释块「---- 项目配置文件 gherkai.toml …----」（CONFIG_COMMANDS 上方）：有八个运行侧命令读配置文件，按「选项 > 环境变量 > 配置文件 > 内建默认」合成。跟上之后对应 ADR 0053 决策 1（读配置的命令清单）。
  - apply_project_config 文档串首行：只对八个读配置的命令做；_reconcile / _tunnel_watch、deploy 等不读。跟上之后对应 ADR 0053 决策 1。
- `cli/tests/test_backend_cloud.py`
  - 「submit/status cloud 的 preflight/fail-fast 接线」节头注释：submit 与 status 的 preflight/fail-fast 接线（含 status --wait 对 kicker 缺失 fail-fast）。跟上之后对应 0033「preflight fail-fast」节（submit 部分）。
  - test_status_wait_cloud_kicker_missing_fails_fast 文档串：status --wait 接力 invoke 的 kicker 不存在时点名 prefix、退出码 2，其他瞬时错吞掉再 invoke。跟上之后对应 无（status --wait 不调用 kicker）。
  - test_status_cloud_json_includes_artifact_locations 文档串：status --json 附加 artifacts，RunState 部分形状不变，只多一个键给报告、判定明细、元信息的位置。跟上之后对应 0041 决策三 status --json 一条。
- `cli/tests/test_definition_schema.py`
  - test_header_stage_contract_violation_exits_2_and_leaves_the_run_untouched 文档串：三个本机读端读头违约退出码 2、不写 run 级消息，理由是本机读端有退出码可交。跟上之后对应 0037 决策 7「definition 结构版本」段（CLI 读端退出码 2）。
- `cli/tests/test_main.py`
  - test_run_steps_dir_flag_resolves_absolute_and_persists 文档串：本机后台推进/接力宿主的 CWD 与提交进程不同，三宿主读回同一值。跟上之后对应 0037 决策 4「解析在组合根、随 definition 持久化」条。
  - test_submit_local_persists_steps_dir_into_definition 文档串：per-run 进程/接力者从 definition 读回，三宿主一致。跟上之后对应 0037 决策 4 同条。
  - test_local_submit_marks_the_run_detached_and_foreground_run_does_not 文档串：本机 submit 的 run_state.json 带 detached 标记，status --wait 据此接力。跟上之后对应 0034 端到端 cloud 第 1b 步（detached 只作描述）与 0041 决策七。
  - 「_render_status：local/cloud 共享的渲染+提示+退出码（两路一致）」节头：_render_status 让两个后端共享渲染、提示与退出码。跟上之后对应 0034「命令形态」不带 --wait 的 status 一条（两路共享 _render_status，提示只看记录与期限）。
  - 「list-runs」节头：本节用例验的 list-runs 行为就是决策七写的。跟上之后对应 0041 决策七。
- `cli/tests/test_project_config.py`
  - PER_CALL/COMMON/CLOUD 名单之上的行注释：测试里显式列出的三份名单就是 0053 决策 3 的名单。跟上之后对应 0053 决策 3「可配置的只是环境型选项」条（按次选择型名单），同注释里保留的决策 6「键集差集」。
  - test_local_relay_host_reads_definition_not_the_config_file 文档串：在另一 CWD 下，接力宿主从 definition 读回的设备与应用值仍是提交时的。跟上之后对应 0053 决策 6「宿主不读文件」条（后台推进进程），配合决策 1。
- `core/DEVELOPMENT.md`
  - 模块树 reconcile.py 条开头：tick 有多个触发源（含 status --wait 接力）。跟上之后对应 0034「推进器与触发源」节（「core 拆分」节与机制三的指针已随第二批第三笔加回；这一节写本机只有一个推进器，接力删去之后再加）。
- `core/gherkai_core/adapters/_atomic.py`
  - 模块文档串「控制面 run_state.json」一条：推进进程在锁内写 run_state.json 时，status 与接力进程无锁读它，这是设计内的读者。跟上之后对应 0030 决定三「local 三个写面一律原子写」框。
  - 模块文档串「权限显式给」段：jobs/*.json 的消费者是 CI 与人。跟上之后对应 0030 决定三「local 三个写面」框（数据面 0644、消费者 CI / 人 / 静态 server）。
- `core/gherkai_core/adapters/cloud_launcher.py`
  - CloudLauncher.launch，武装失败分支上方的行注释：武装失败不阻塞 launch，保护降级为 tick 防御扫加 status --wait，只打日志。跟上之后对应 0034「job timeout」节「best-effort 边界」条（连同 0054 决策九第 1 条）。
- `core/gherkai_core/adapters/event_log/recording.py`
  - 模块文档串第二段：同步 run 的记录器也写退出记录，好让 status --wait 的接力推进和 explain 的补取读到完整事件流。跟上之后对应 0042 决策七第 1 条，加 0034 机制二「两件都要」。
- `core/gherkai_core/adapters/event_log/sqlite.py`
  - 模块文档串「并发」段：status --wait 接力者在另一进程里同样起 worker、写同一个事件库，可能与 per-run 进程同时推进，两个进程的写由 WAL 写锁串行。跟上之后对应 0034「端到端流程」local 节（跨进程写 events sink 只有持锁的推进器）。
- `core/gherkai_core/adapters/run_store/ddb.py`
  - 模块文档串「STATE item」条的可选顶层标记一句：detached 顶层标记供 kicker 的 Stream filter 识别。跟上之后对应 0034 端到端 cloud 1b「触发过滤不看后台执行标记」。
  - 模块文档串「STATE item」条 jobs 必须原生 Map 一句：jobs 须为原生 Map，才能用 `SET jobs.#sid=:js` 按 scope_id 整 entry 单元素刷（update_job_state 的写法）。跟上之后对应 0030 决定六「RunState.jobs 落 DDB 用原生 Map」条。
  - DynamoDBRunStore.__init__ 文档串的 detached 参数：detached 标记让 kicker 的 Stream filter 只认 submit 建的 run，同步 `run --backend cloud` 不触发 kicker，免得双开推进器。跟上之后对应 0034 端到端 cloud 1b「触发过滤不看后台执行标记」。
  - _state_item 里 detached 一行的行注释：kicker filter 只认带 detached 标记的 INSERT。跟上之后对应 0034 端到端 cloud 1b（过滤写法见 0054 决策九）。
- `core/gherkai_core/adapters/run_store/local.py`
  - _atomic_write_json 文档串第二段：写入方在文件锁内写 run_state.json 时，`gherkai status` 和接力进程不持锁读同一个文件，所以确实有并发读者。跟上之后对应 0030 决定三「local 三个写面一律原子写」框（无锁读者为 status、list-runs 与处置方）；0034 没有对应的一节，因为本机接力已被拒。
- `core/gherkai_core/model.py`
  - RunMeta.steps_dir 字段注释：起 worker 的有三个宿主：同步 run、本机 per-run 进程、status --wait 接力者，三者 CWD 各不相同。跟上之后对应 0037 决策 4（两个宿主从 definition 读回）与 0034「local」一节。
  - JobState.claimed_at 字段注释：claimed_at 有三个用途：本机接力恢复 deadline、云端 tick 防御性超时扫、status 显示时长。跟上之后对应 0034「job timeout」节「JobState.claimed_at」条。
- `core/gherkai_core/persist.py`
  - RunPersistence.begin 文档串「create_run 前先 preflight」段：create_run 之前先 preflight；桶或表名错都在这里暴露，由组合根归到退出码 2，免得有无 offload 内容把同一个错分成退出码 2 与 1。跟上之后对应 0030 决定七「Store port 有 preflight()，begin 之前探活」。
- `core/gherkai_core/ports.py`
  - RunStore.try_claim_job 文档串 claimed_at 段：claimed_at 的用途：本机接力恢复 deadline、云端 tick 防御扫、status 显示时长。跟上之后对应 0034「job timeout」节 `JobState.claimed_at` 条。
  - RunStore「认领与投影」小节的行注释：认领由前台执行者与后台推进共用，后台推进会跨进程、跨实例并发调用。跟上之后对应 0034「推进器与触发源」第 1、2 条（本机只有一个推进器，云端多次调用可以重叠）与机制四；前台用同一种认领见 0034 机制三「run 级状态只进不退」条①。
- `core/gherkai_core/project.py`
  - TaskExited.timed_out 字段注释：超时标志的来源含接力方补写的未知退出。跟上之后对应 0034「job timeout」节「timed_out 归因链」条。
- `core/gherkai_core/reconcile.py`
  - 模块文档串「无状态 + 幂等」段：谁调、何时调、并发调 tick 都安全，由 CAS + HWM 条件写兜底，各触发源（cloud Stream / local per-run / status --wait 接力）共用 tick。跟上之后对应 0034「推进器与触发源」与机制三、机制四。
- `core/tests/test_atomic_write.py`
  - test_json_round_trip_and_default_mode_readable_by_others 文档串：判定真值与报告产物的消费者是 CI/人/静态 server。跟上之后对应 0030 决定三「local 三个写面一律原子写」框里的权限条（数据面与报告 0644，消费者是 CI / 人 / 静态 server）。
- `core/tests/test_ddb_run_store.py`
  - test_detached_flag_on_state_item 文档串：STATE item 上的 detached=true 标记供 kicker 的流过滤使用，同步 run 不落。跟上之后对应 ADR 0034 端到端 cloud 1b「触发过滤不看后台执行标记」；ADR 0033 资源清单第 13 条。
- `core/tests/test_lifecycle_states.py`
  - 「WorkerNetworkError 竞态块按 abort_flag 拆分」节标题注释：网络故障块按 abort_flag 拆成三支：abort_flag→ABORTED、超时→error+timeout、其余→network_error。跟上之后对应 0031 决定一「aborted 来自主动中止与 run 的期限，不来自 job 自己的预算」注，以及 0034 机制二「终结函数与真值表」。
  - 「WorkerNetworkError 竞态块按 abort_flag 拆分」节标题下的行注释块：超时与 fail-fast 两条路径都会主动停 worker，所以网络块的回填判据取 abort_flag，并说这正是 ADR 警告的做法。跟上之后对应 0031 决定一「aborted 来自主动中止与 run 的期限，不来自 job 自己的预算」注（按 stop_reason 判定；到点时再按预算还是期限分别记 error+timeout 或 aborted），以及 0031 touch points 里 schedule.py 那一条。
- `core/tests/test_local_run_store_atomic.py`
  - 模块文档串首行：LocalRunStore 原子写，推进进程写 run_state.json 时 status 与接力进程无锁读它。跟上之后对应 0030 决定三「local 三个写面一律原子写」框。
- `core/tests/test_report_store.py`
  - test_manifest_shape 里 `"result" not in m` 上方的行注释：manifest 靠 run_id 软引用，判定真值在 ResultStore。跟上之后对应 0027「manifest.json 形态」节与 0016「三层切分」节。
- `core/tests/test_stores.py`
  - test_run_meta_steps_dir_round_trip 文档串：steps_dir 随 definition 走，理由是三个 local 宿主（同步 run / per-run 进程 / status --wait 接力者）CWD 各不相同。跟上之后对应 0037 决策 4。
- `deploy_aws/DEVELOPMENT.md`
  - 「事件驱动推进」节「Event source mappings」条（events 表 Stream 的 REMOVE 过滤）：TTL 过期删除的 REMOVE 记录不触发推进，推进方读到终态即返回，各道防护挡哪些触发写在那一条。跟上之后对应 REMOVE 过滤对应 0033「资源清单」第 13 条与「events 表开 TTL」条护栏②；读到终态之后的处理对应 0034 端到端 cloud「已收尾的 run 不再推演」条。
- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
  - 模块文档串「只为 detached run 写」一段：同一 cluster 的同步 run --backend cloud 的 task 也会触发本 handler，所以写之前按 detached 分流，其不变量与故障形态在机制一。跟上之后对应 0034 机制一（独立键空间、读者按 item_type 分流），以及端到端 cloud 1b「触发过滤不看后台执行标记」。
  - _is_detached 文档串首句：按 runs 表 STATE item 上的 detached 标记，判断本 run 是否由云端推进器管。跟上之后对应 0034 端到端 cloud 1b（实装后这个分流退场）。
  - _is_detached 文档串第二段：给同步路径写 task_exited，会让它的 events Query 读端撞上没有 body 属性的 item。跟上之后对应 0034 机制一。
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
  - 模块文档串第一段：Stream 分片并发触发多个 handler 实例、叠加 status --wait 接力，全部安全。跟上之后对应 0034 机制三开头与「推进器与触发源」第 2 条。
  - _run_ids_from_stream 文档串：推进方读到终态即返回。跟上之后对应 0034 端到端 cloud 第 4 步「已收尾的 run 不再推演」。
  - _build「已收尾的 run 不再推演」注释：已收尾的 run 被重放推演会按写序无条件覆盖写。跟上之后对应 0034 端到端 cloud 第 4 步「已收尾的 run 不再推演」的理由句。
  - _build「已收尾的 run 不再推演」注释：到点 payload 遇到已收尾的 run 整体跳过，与 StopTask 的关系有两种例外。跟上之后对应 0034 端到端 cloud 第 4 步与 0054 决策九第 2 条。
  - _run_ids_from_runs_stream 文档串 ②：直接 invoke 的 kickoff 是 cloud status --wait 的接力兜底。跟上之后对应 0034「重议闸门」首条（kicker 认的两种 event 源，Scheduler 定时触发走直接调用的载荷）。
  - kicker_handler 文档串：kicker 只被 runs Stream 的 INSERT 触发，reconciler 之后写 runs 表不触发它。跟上之后对应 0034 被拒方案「runs 表 Stream 直接触发 reconciler」与 0054 决策九。
- `deploy_aws/gherkai_deploy_aws/stack.py`
  - 模块文档串资源清单的「Lambda/事件驱动链」一条：三个 Function、EventBridge 规则与两表 Stream 的映射，kicker 那条 filter 只收 INSERT 且带 detached 标记。跟上之后对应 0033 资源清单 12–15、0034 端到端 cloud 1b、0054 决策九。
  - BackendStack._storage 的 runs 表注释块：create_run 写 definition 的 INSERT 触发 kicker 冷启动，kicker 只被 INSERT 触发。跟上之后对应 0034 端到端 cloud 1b 与 0033 资源清单 13。
  - BackendStack._storage 的 runs 表注释块：runs 表的 MODIFY（project_state/finalize）不触发 kicker，所以没有自触发放大。跟上之后对应 0034 被拒方案「runs 表 Stream 直接触发 reconciler」。
  - BackendStack._reconcile_lambdas 文档串首行：文档串所写的推进链：kicker 还被 cli status --wait 直接 invoke，三个 handler 按 detached 标记分辨由谁推进（「复用同步 cloud run 的资源」一句已随云端只支持 submit 改写，指针等这两处跟上再加回）。跟上之后对应 0034「端到端流程」cloud 一节。
  - _reconcile_lambdas 里 ExitObserverFn 的 events 表权限注释：events 是 append-only 的判定真值日志。跟上之后对应 0034「核心思想：CQRS + 无状态 reconciler」写模型条。
  - _reconcile_lambdas 里 KickerFn 的 function_name 行注释：cli status --wait 按 prefix 推出 kicker 名并 invoke kickoff。跟上之后对应 目标设计里没有这一调用；kicker 的触发源见 0034「推进器与触发源」第 2 条。
  - _reconcile_lambdas 里 runs 表 Stream → kicker 的注释块：kicker 的 filter 只收 INSERT 且 NewImage.detached=true，用来滤掉同步 run --backend cloud。跟上之后对应 0033 资源清单 13、0054 决策九第 1、2 条、0034 端到端 cloud 1b。
  - events 表 Stream 事件源上方注释：过期删除不触发推进，推进方本次读到终态即返回。跟上之后对应 0034 端到端流程 cloud 一节「已收尾的 run 不再推演」条（遇到终态只清扫仍在执行的 task）；0054 决策九。
- `deploy_aws/tests/test_lambda_handlers.py`
  - test_run_ids_skips_ttl_remove_records 文档串：events 表 TTL 删除的 REMOVE 记录不算 run、不为它推进一次。跟上之后对应 0033「资源清单」第 13 条与「events 表开 TTL」条护栏②。
  - 「已收尾的 run 再被触发时 handler 整体 no-op」节标题注释：已收尾的 run 再被触发时两个 handler 整体 no-op，作为判定真值不被销毁的第二道闸。跟上之后对应 0034 端到端 cloud「已收尾的 run 不再推演」条与 0054 决策九第 2 条。
  - test_timeout_payload_on_a_finished_run_is_a_noop 文档串：超时触发打到已收尾的 run 时跳过，跳过与 StopTask 的关系及两种漏发 StopTask 的例外。跟上之后对应 0034 端到端 cloud「已收尾的 run 不再推演」条与 0054 决策九第 2 条。
- `deploy_aws/tests/test_stack.py`
  - test_kicker_mapping_insert_filter 行注释：kicker 的 event source mapping 只有一条 INSERT 过滤。跟上之后对应 0033 资源清单第 13 条，配合 0054 决策九第 1、2 条。
- `runtime/gherkai_runtime/compose.py`
  - build_engines 文档串 steps_dir 段：三个宿主（含 status --wait 接力者）CWD 各不相同，重解析必分叉。跟上之后对应 0037 决策 4（与 0034 local 一节）。
  - build_cloud_stores 内 detached 参数的行注释：detached 标记触发 kicker 冷启动，同步 run 不带标记即不触发，否则双开推进器。跟上之后对应 0034「端到端流程」cloud 1b「触发过滤不看后台执行标记」。
  - _make_lambda_client 文档串：cloud status --wait 接力 invoke kicker Lambda 做 kickoff。跟上之后对应 目标设计里没有这一用途（0034「推进器与触发源」第 2 条写的是相反做法）；这个 client 若另有用途，按那时的用途指。
- `runtime/gherkai_runtime/detached.py`
  - drive_local_reconcile 文档串：这里是本机推进的唯一入口，per-run 进程和 status --wait 接力都调它。跟上之后对应 0034 端到端 cloud 1b「三个宿主一份」与 local 节。
  - build_local_reconcile 中 steps_dir 的行注释：本函数有两个宿主：per-run 进程和 status --wait 接力者，两者的 CWD 都和提交进程不同。跟上之后对应 0034「local（对称，无 ECS/Lambda）」节，配合同处保留的 0037 决策 4。
  - _recover_timed_out_claims 文档串最后一段：接力方判超时、补写未知退出与这条被拒方案不冲突，因为那条拒的是有活观察链时绕过它。跟上之后对应 目标设计里没有本函数（0034 被拒方案「本机接力，及其改法」）；这件事归 run 处置：0054 决策六（处置条件）、决策七（处置做什么），入口见 0054 决策八。
  - _recover_timed_out_claims 文档串第三段末句：接力判超时的条件已经定下改法（改为按认领方的进程是否还在来判），只是还没有实装。跟上之后对应 同上：0034 被拒方案「本机接力，及其改法」；由 0054 决策三（生命期锁）与决策六、七（处置）取代。
  - 模块级常量 _RECOVERY_MARGIN_S 的行注释末尾：接力判超时的条件已经定下改法（按认领方的进程是否还在来判），只是还没有实装。跟上之后对应 目标设计里没有这个常量（本机接力被拒，见 0034 被拒方案「本机接力，及其改法」）；对应 0054 决策三、六、七。
  - run_reconcile_loop 里报告收尾一段的注释：这一步失败会跳过拆隧道（`drive_local_reconcile` 的 cleanup_tunnel 在本函数返回后才执行）。跟上之后对应 无对应小节：隧道建在后台推进进程里、随它退出而消失（0035 决策 3「寿命」），cleanup_tunnel 随之删去。
- `runtime/gherkai_runtime/names.py`
  - BASE_KICKER_LAMBDA 上方注释：cli 的 status --wait 据 --prefix 拼出 kicker 名并 invoke 接力 kickoff。跟上之后对应 0034「推进器与触发源」第 2 条（Lambda 名的同源见 0033 资源清单 12.）。
  - job_timeout_schedule_prefix 文档串：单侧改名使 CreateSchedule 被拒时，job timeout 降级为只剩防御扫，纯静默 job 彻底失去超时保护。跟上之后对应 0034「job timeout」节「best-effort 边界」条（配套见 0033 资源清单 15.）。
- `runtime/gherkai_runtime/tunnel_host.py`
  - 「cloud submit 隧道守护 TTL 的记账常量」一段的标题注释：TTL 是防 ngrok 进程泄漏的上界，由一次性余量与每 job 余量算出。跟上之后对应 无对应小节：守护进程的存活上限由运行期限推出（0035 决策 3「三种组合的宿主与次序」云端一条），这些常量与 compute_watch_ttl_s 随之删去；余量的组成见 0054 决策二「尾段与余量是预算的取值」一段。
- `runtime/tests/test_detached_launcher.py`
  - test_build_local_reconcile_prefers_meta_max_concurrency 文档串：status --wait 接力者的 flag 值可能与 submit 时不同，接力不该改并行度。跟上之后对应 0034 机制四「max_concurrency 随 definition 走」段。
  - test_build_local_reconcile_reads_steps_dir_from_definition 文档串：per-run 进程与 status --wait 接力者的 CWD 各不相同，重解析会让三个宿主用到不同的 step 集。跟上之后对应 0037 决策 4。
  - test_build_local_reconcile_reads_steps_dir_from_definition 文档串：per-run 进程与 status --wait 接力者的 CWD 与提交进程各不相同。跟上之后对应 0034「端到端流程」local 节（0037 决策 4 引它说明后台推进进程与提交 CLI 各是组合根）。
  - test_build_local_reconcile_host_env_steps_dir_does_not_leak 文档串：接力者是从 definition 读回 steps_dir 的宿主之一，它的 shell env 不得越过 definition。跟上之后对应 0037 决策 4（宿主建注入 env 时先抹掉组合根拥有的键）。
  - 「启动器记下退出时刻、接力的判定条件与条件补写」分节注释：本组覆盖接力的判定条件与条件补写。跟上之后对应 0054 决策二后台推进条「截止时刻与说明」。

## 语义一致随实装核对：范围与清单

写回这一步对注释里的 ADR 指针只保证机械可核的一项：指针里的条名，写回之前的 ADR 里有、现在没有的为 0。指针所括的说法与所指小节的现文是否一致，owner 定为随实装核对（现在落的是设计，code 跟上时把注释改成一致）。在那之前，下面清单里的文件可能仍有注释把现在 code 的行为归给已经改成目标设计的小节；另一家模型三轮各指出 3、3、4 处，都已改，上面的列表含其中去掉指针的各处。

责任范围是 `core/`、`cli/`、`runtime/`、`deploy_aws/`、`tools/`、`engines/` 与 `CONTRIBUTING.md` 里，写回时或现在带有指向这次改过的各篇 ADR 的指针的全部文件，共 277 个（0016、0024、0026、0027、0028、0030、0031、0032、0033、0034、0035、0037、0038、0040、0041、0042、0043、0044、0045、0051、0053、0054，另有隧道一块写回时改的 0011，带指向它的指针的三个文件都已在清单里；指针按「ADR 加篇号」、指向 `docs/adr/` 的链接与接在它们后面的篇号列举来认）。分两组列出：

- 写回时做过一次全量核对的 151 个（按「另一家模型核落到位」里的规则逐个注释块读过，上面的列表是那次去掉的指针）。
- 没有核过的 126 个：`engines/` 下的 worker 与它们的测试，以及其余目录里不是 `.py`、`.md` 的文件（配置、镜像定义、脚本）。那次核对的分批没有收它们。

两组适用同一套做法：

- 每个实装批核它改到的文件：其中指向这 22 篇的指针逐个对所指小节的现文，核过的文件从清单里删去。
- 全部实装批之后对清单做一次差集：剩下的文件（实装不需要改的）另作一批核完。清单清空后本节删除。

### 写回时核过一遍的（151）

（仓库根）（1）：

- `CONTRIBUTING.md`

cli（29）：

- `cli/DEVELOPMENT.md`
- `cli/gherkai_cli/__init__.py`
- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/config.py`
- `cli/gherkai_cli/deploy.py`
- `cli/gherkai_cli/device_selection.py`
- `cli/gherkai_cli/render.py`
- `cli/gherkai_cli/settings.py`
- `cli/gherkai_cli/skill_install.py`
- `cli/gherkai_cli/submission.py`
- `cli/tests/_doc_rules.py`
- `cli/tests/conftest.py`
- `cli/tests/test_backend_cloud.py`
- `cli/tests/test_cli_json_contract.py`
- `cli/tests/test_code_comments.py`
- `cli/tests/test_context_glossary.py`
- `cli/tests/test_definition_schema.py`
- `cli/tests/test_deploy_cmd.py`
- `cli/tests/test_job_timeout_cap.py`
- `cli/tests/test_main.py`
- `cli/tests/test_project_config.py`
- `cli/tests/test_release_notes.py`
- `cli/tests/test_render.py`
- `cli/tests/test_skill.py`
- `cli/tests/test_skill_install.py`
- `cli/tests/test_technical_docs.py`
- `cli/tests/test_tunnel_cli.py`
- `cli/tests/test_user_docs.py`
- `cli/tests/test_user_facing_messages.py`

core（71）：

- `core/DEVELOPMENT.md`
- `core/gherkai_core/adapters/__init__.py`
- `core/gherkai_core/adapters/_atomic.py`
- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/recording.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/report_store/__init__.py`
- `core/gherkai_core/adapters/report_store/local.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/device_session.py`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/gherkai_core/redact.py`
- `core/gherkai_core/run_deadline.py`
- `core/gherkai_core/schedule.py`
- `core/gherkai_core/scope.py`
- `core/gherkai_core/serialize.py`
- `core/gherkai_core/target.py`
- `core/gherkai_core/wire.py`
- `core/tests/README.md`
- `core/tests/conftest.py`
- `core/tests/fake_engine.py`
- `core/tests/fixtures/echo_worker.py`
- `core/tests/test_arg_offload.py`
- `core/tests/test_atomic_write.py`
- `core/tests/test_cloud_infra.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_conditional_writes.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_event_log_recording.py`
- `core/tests/test_fargate_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_list_runs.py`
- `core/tests/test_local_result_store_atomic.py`
- `core/tests/test_local_run_store_atomic.py`
- `core/tests/test_local_run_store_lock.py`
- `core/tests/test_persist.py`
- `core/tests/test_plan.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_redact.py`
- `core/tests/test_report_store.py`
- `core/tests/test_run_deadline.py`
- `core/tests/test_s3_report_store.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_schedule.py`
- `core/tests/test_session_events.py`
- `core/tests/test_sqlite_event_log.py`
- `core/tests/test_status_group.py`
- `core/tests/test_stores.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_terminal.py`
- `core/tests/test_termination_parity.py`
- `core/tests/test_wire.py`

deploy_aws（17）：

- `deploy_aws/DEVELOPMENT.md`
- `deploy_aws/gherkai_deploy_aws/app.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- `deploy_aws/gherkai_deploy_aws/names.py`
- `deploy_aws/gherkai_deploy_aws/stack.py`
- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_container.py`
- `deploy_aws/tests/test_lambda_asset.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `deploy_aws/tests/test_names.py`
- `deploy_aws/tests/test_provider.py`
- `deploy_aws/tests/test_skill_deploy_tokens.py`
- `deploy_aws/tests/test_stack.py`
- `deploy_aws/tests/test_workers.py`

engines（2）：

- `engines/midscene/DEVELOPMENT.md`
- `engines/novaact/DEVELOPMENT.md`

runtime（22）：

- `runtime/DEVELOPMENT.md`
- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/app_upload.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/deadline.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/gherkai_runtime/devicefarm.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/gherkai_runtime/textui.py`
- `runtime/gherkai_runtime/tunnel.py`
- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_app_upload.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_deadline.py`
- `runtime/tests/test_detached_launcher.py`
- `runtime/tests/test_devicefarm.py`
- `runtime/tests/test_devicefarm_client_placement.py`
- `runtime/tests/test_names_device_farm.py`
- `runtime/tests/test_names_worker.py`
- `runtime/tests/test_tunnel.py`
- `runtime/tests/test_tunnel_host.py`
- `runtime/tests/test_worker_variant.py`

tools（9）：

- `tools/build_diagrams.mjs`
- `tools/device_reprobe.md`
- `tools/doc_rules_check.py`
- `tools/e2e_harness.md`
- `tools/e2e_harness.py`
- `tools/ecs_task_timing.py`
- `tools/events_wallclock.py`
- `tools/render_skill_contract.py`
- `tools/workers_real_aws/README.md`

### 没有核过的（126）

cli（2）：

- `cli/.gitignore`
- `cli/pyproject.toml`

core（1）：

- `core/pyproject.toml`

deploy_aws（1）：

- `deploy_aws/pyproject.toml`

engines（118）：

- `engines/fixtures/browser-session-timeout.json`
- `engines/fixtures/job-lines.json`
- `engines/fixtures/one-line-text-cases.json`
- `engines/fixtures/redaction-cases.json`
- `engines/fixtures/tunnel-warmup.json`
- `engines/midscene/Dockerfile`
- `engines/midscene/spikes/01-model-sigv4.ts`
- `engines/midscene/spikes/02-agentcore-cdp.ts`
- `engines/midscene/spikes/03-midscene-grounding.ts`
- `engines/midscene/spikes/04-planning-probe.ts`
- `engines/midscene/spikes/05-negative-assertions.ts`
- `engines/midscene/src/bin.mts`
- `engines/midscene/src/device/adapters/adapters.contract.test.mts`
- `engines/midscene/src/device/adapters/uiautomator2.mts`
- `engines/midscene/src/device/adapters/xcuitest.mts`
- `engines/midscene/src/device/app.mts`
- `engines/midscene/src/device/app.test.mts`
- `engines/midscene/src/device/appium.mts`
- `engines/midscene/src/device/appium.test.mts`
- `engines/midscene/src/device/device-session.mts`
- `engines/midscene/src/device/finalize.mts`
- `engines/midscene/src/device/finalize.test.mts`
- `engines/midscene/src/device/guard.mts`
- `engines/midscene/src/device/guard.test.mts`
- `engines/midscene/src/device/interface.mts`
- `engines/midscene/src/device/limits.mts`
- `engines/midscene/src/device/limits.test.mts`
- `engines/midscene/src/device/parts.mts`
- `engines/midscene/src/device/read-points.test.mts`
- `engines/midscene/src/device/session-name.mts`
- `engines/midscene/src/device/session-name.test.mts`
- `engines/midscene/src/device/session.mts`
- `engines/midscene/src/device/session.test.mts`
- `engines/midscene/src/device/surface.mts`
- `engines/midscene/src/device/surface.test.mts`
- `engines/midscene/src/device/warmup.mts`
- `engines/midscene/src/device/warmup.test.mts`
- `engines/midscene/src/device/wdio-log.mts`
- `engines/midscene/src/device/wdio-log.test.mts`
- `engines/midscene/src/index.mts`
- `engines/midscene/src/lib/agentcore-sigv4.mts`
- `engines/midscene/src/lib/artifact-upload.mts`
- `engines/midscene/src/lib/error-text.mts`
- `engines/midscene/src/lib/event-sink.mts`
- `engines/midscene/src/lib/job-source.mts`
- `engines/midscene/src/lib/parent-watchdog.mts`
- `engines/midscene/src/lib/precheck.mts`
- `engines/midscene/src/lib/redact.mts`
- `engines/midscene/src/lib/tunnel-warmup.mts`
- `engines/midscene/src/resolve-hook.mts`
- `engines/midscene/src/worker/agentcore-sigv4.test.mts`
- `engines/midscene/src/worker/argument.mts`
- `engines/midscene/src/worker/argument.test.mts`
- `engines/midscene/src/worker/artifact-upload.test.mts`
- `engines/midscene/src/worker/browser-session-timeout.test.mts`
- `engines/midscene/src/worker/deterministic.mts`
- `engines/midscene/src/worker/deterministic.steps.mts`
- `engines/midscene/src/worker/error-text.test.mts`
- `engines/midscene/src/worker/event-sink.test.mts`
- `engines/midscene/src/worker/evidence.mts`
- `engines/midscene/src/worker/evidence.test.mts`
- `engines/midscene/src/worker/job-source.test.mts`
- `engines/midscene/src/worker/job-timeout-cap.test.mts`
- `engines/midscene/src/worker/no-artifacts.test.mts`
- `engines/midscene/src/worker/no-device-deps.test.mts`
- `engines/midscene/src/worker/parent-watchdog.test.mts`
- `engines/midscene/src/worker/precheck.test.mts`
- `engines/midscene/src/worker/redact.test.mts`
- `engines/midscene/src/worker/run-scope.mts`
- `engines/midscene/src/worker/run-scope.test.mts`
- `engines/midscene/src/worker/stderr-outlets.test.mts`
- `engines/midscene/src/worker/surface-desktop.mts`
- `engines/midscene/src/worker/surface.mts`
- `engines/midscene/src/worker/surface.test.mts`
- `engines/midscene/src/worker/tunnel-warmup.test.mts`
- `engines/midscene/src/worker/user-steps.mts`
- `engines/midscene/src/worker/user-steps.test.mts`
- `engines/midscene/tsconfig.json`
- `engines/novaact/Dockerfile`
- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/gherkai_worker_novaact/deterministic_steps.py`
- `engines/novaact/gherkai_worker_novaact/evidence.py`
- `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/lib/job_source.py`
- `engines/novaact/gherkai_worker_novaact/lib/precheck.py`
- `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- `engines/novaact/gherkai_worker_novaact/lib/tunnel_warmup.py`
- `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/gherkai_worker_novaact/user_steps.py`
- `engines/novaact/pyproject.toml`
- `engines/novaact/spikes/wikipedia_benchmark.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_argument.py`
- `engines/novaact/tests/test_artifact_upload.py`
- `engines/novaact/tests/test_capabilities.py`
- `engines/novaact/tests/test_deterministic.py`
- `engines/novaact/tests/test_event_sink.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_interrupt_model.py`
- `engines/novaact/tests/test_interrupt_process.py`
- `engines/novaact/tests/test_job_source.py`
- `engines/novaact/tests/test_no_artifacts.py`
- `engines/novaact/tests/test_one_line.py`
- `engines/novaact/tests/test_precheck.py`
- `engines/novaact/tests/test_redact.py`
- `engines/novaact/tests/test_run_step.py`
- `engines/novaact/tests/test_session_events.py`
- `engines/novaact/tests/test_stderr_redaction.py`
- `engines/novaact/tests/test_transient_network.py`
- `engines/novaact/tests/test_tunnel_warmup.py`
- `engines/novaact/tests/test_user_steps.py`
- `engines/novaact/tests/test_workflow_setup.py`

runtime（1）：

- `runtime/pyproject.toml`

tools（3）：

- `tools/device_reprobe.mts`
- `tools/git-hooks/pre-commit`
- `tools/presentations/production.md`
