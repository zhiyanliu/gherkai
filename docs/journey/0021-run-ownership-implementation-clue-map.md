> 类型: 调查记录

# 推进权与状态投影：实装线索逐条对到 code 的摸底

[0018](./0018-run-ownership-adr-writeback-plan.md)「实装」一节的线索逐条对到 code 的结果，供排实装分批与各批动手时查用。做法：每个小块一位只读代理，逐条读线索所指的 ADR 小节与 code 位置，给出落到 code 上要做什么、要动的文件、改动量、先后依赖、单独先落地的后果与验证方式；另列出读 code 时发现而线索没有覆盖的改动点。摸底时的 code 是提交 `e3940d69`。

读法：

- 每条的编号是小块名的缩写加序号，「线索」是 0018 里那一条开头的文字，用来回指原文。
- 改动量：S 是一个文件里几十行以内，M 是几个文件、一两百行，L 是跨包或改数据结构与端口、几百行以上。
- 这是一次摸底的记录，不是设计：其中的判断出自各位代理，没有逐条复核；与 ADR 不一致时以 ADR 为准，ADR 没有定的进了「ADR 补遗」那一批。
- 实装分批定下之后，各批做完即在这里删去对应的条目；实装全部完成之后本文删除。

## 词表与退役词

### 小结

这一块只有一条线索，工作是纯文字：加三个退役词，同时清掉全仓命中（扫描面上 67 行、29 个文件，跨 core、cli、runtime、deploy_aws 与文档），再重新导出一张图。没有内部先后可言，但对别的块有很强的次序关系。

「接力推进」要等本机接力删除（连同生命期锁与 run 处置）一起落地，或排在它之后：它的命中多半描述的是还在运行的接力机制，包括测试拦不住的 --help 与提示字面量。

「超时处置」「到点处置」只是改名，命中集中在云端 reconciler、stack 与 test_lambda_handlers 的注释里，和云端块同批最省事。只改注释不用重新部署。

建议拆成两半：各自并进本机接力删除批与云端批，或者整体放到最后的收尾批，避免同一批注释改两遍。代价是：加表越晚，护栏越晚开始防止中间各批重新写进这些词。

风险不在行为，在遗漏：
- 退役词护栏在 code 里只扫注释与 docstring，--help、提示、错误信息里的「接力推进」靠人工检索。
- 图源改了必须在本机用 archify 加 Chrome 重新导出 SVG，否则指纹测试红。
- 其余 _Avoid_ 词进不进表还没定。「进程核对」有合法的普通用法，不宜进表；「到期收尾」「收尾写」命中多，若进表应和结束写块同批。

### 线索没有覆盖的改动点

- cli/gherkai_cli/__main__.py 里带「接力推进」的用户可见字面量不在线索列出的清理面里，也不受 RETIRED_TERMS 护栏管：第 475、479 行 status 的 --wait 与 --max-concurrency 的 help，第 2112 行 pending 提示「可接力推进」，第 2200 行 _WAIT_WITHOUT_RELAY_NOTICE，第 2747 行错误信息。依据 ADR 0045 决策八（人读层全改）与 ADR 0039（产品文案）。它们应随本机接力删除改写或删去。另外要不要把退役词扫描扩到用户可见字符串（test_user_facing_messages.py），交人定，拿不准是否属于这一块
- docs/diagrams/execution-timeout-chain.json 除了两个退役词，还有和新设计不符、但不会被退役词表命中的内容：第 198 行讲「接力者按库里的领取时刻重算截止时刻，过了它 10 秒仍无退出记录即判超时」，是本机接力的行为；第 136、199 行写「归因为超时失败」，没有区分被运行期限截断的情形，而按 ADR 0034「job timeout」节产品语义与 0031 决定一，那种情形记 aborted、不算超时。journey「行为文档」块对这张图只提到改那两个词。依据 ADR 0034「job timeout」节与被拒方案「本机接力，及其改法」，以及 ADR 0031 决定一。宜随本机接力删除一并改，只重新导出一次 SVG
- docs/internals/execution-and-reconciliation.md 第 165 行（接力者按 is_detached 分流、「只等待它结束、不接力推进」）与 docs/internals/verdict-model.md 第 42 行（status 提示用 --wait 接力推进）描述的是要删去的行为，光换词不够，要按新行为改写（处置、生命期锁）。依据 ADR 0054 决策六至八，以及 ADR 0034 被拒方案「本机接力，及其改法」。journey 的「核对时补上的条目」与「行为文档」块笼统提过这两篇，退役词这条只当换词处理，可能漏掉内容改写
- core/tests/test_conditional_writes.py 的 _LAUNCHER 与 "launcher" 附加键：生产 code 里已经没有这个键，形状沿用的是被生命期锁取代的发起进程标识。即使「发起进程标识」不进表，也宜换成中性的示例键，免得测试暗示这个设计还在。依据 ADR 0054 的生命期锁（CONTEXT「生命期锁」词条的 _Avoid_）与 ADR 0030 决定四（local 的顶层附加键整体保留）

### 逐条

#### 词表-1（mixed，M）

- 线索：把 owner 定的「接力推进」「超时处置」「到点处置」加进退役词表
- 要做的：往 cli/tests/_doc_rules.py 的 RETIRED_TERMS_WORDS 元组里加入「接力推进」「超时处置」「到点处置」三项。三个词都不在「批」义集合 _BATCH_WORDS 里，所以 RETIRED_TERMS_IN_CODE 自动带上它们。同一提交清掉各扫描面上的全部命中：按 classify 与 scan 模拟扫描，共 67 行、29 个文件。分布：code 注释与 docstring 约 50 行（core 的 reconcile.py、project.py、serialize.py、event_log/ddb.py、event_log/recording.py、run_store/local.py、fargate_engine.py；cli 的 __main__.py；deploy_aws 的 lambdas/reconciler.py 11 行、exit_observer.py、stack.py；还有 core、cli、runtime、deploy_aws 下的各测试文件）；技术文档 4 行（docs/internals/execution-and-reconciliation.md 三行，deploy_aws/DEVELOPMENT.md 一行）；internals 的 verdict-model.md 一行；用户文档 4 行（CHANGELOG [Unreleased] 第 67 行，configuration.md 第 146、202 行，running-and-results.md 第 83 行）；图源 execution-timeout-chain.json 3 行。「超时处置」「到点处置」只是改名，改成 CONTEXT 规范名「job 到点停止」；「接力推进」描述的机制随本机接力一起删去，相应文字也删去或改写成新行为。「发起进程标识」要是进表，test_each_write_entry_keeps_top_level_extras 的文档串和 _LAUNCHER 示例一并换成中性的附加键。
- 文件：cli/tests/_doc_rules.py、core/tests/test_conditional_writes.py、core/gherkai_core/reconcile.py、core/gherkai_core/project.py、core/gherkai_core/serialize.py、core/gherkai_core/adapters/event_log/ddb.py、core/gherkai_core/adapters/event_log/recording.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/fargate_engine.py、cli/gherkai_cli/__main__.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py、deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/DEVELOPMENT.md、core/tests/test_cloud_reconcile.py、core/tests/test_fargate_engine.py、core/tests/test_project.py、core/tests/test_reconcile.py、core/tests/test_schedule.py、core/tests/test_termination_parity.py、cli/tests/test_backend_cloud.py、cli/tests/test_main.py、deploy_aws/tests/test_lambda_handlers.py、deploy_aws/tests/test_stack.py、runtime/tests/test_compose.py、docs/internals/execution-and-reconciliation.md、docs/internals/verdict-model.md、docs/user-guide/configuration.md、docs/user-guide/running-and-results.md、CHANGELOG.md、docs/diagrams/execution-timeout-chain.json、docs/diagrams/execution-timeout-chain.svg
- 先要有：「接力推进」：本机接力删除（status --wait 不再进入推进循环），连同生命期锁与 run 处置（settle-runs 与等待中的 status --wait）。现在命中的 --help、提示、注释、configuration.md 与 running-and-results.md 讲的都是还在运行的接力机制；在它删去之前退役这个词，只能给一个活着的机制另起临时名字，删机制时再改一遍；「超时处置」「到点处置」：没有行为上的前置。只是改名为「job 到点停止」，什么时候做都行
- 必须同批：同一提交清掉全部命中：先加表，test_user_docs、test_code_comments、test_technical_docs 与图源扫描就会红；同一提交用 tools/build_diagrams.mjs 重新导出 execution-timeout-chain.svg：test_user_docs 核对 SVG 末尾的图源 sha256 指纹，只改 JSON 会红；要是「到期收尾」进表：docs/internals/cli-json-contract.md 改完后，用 tools/render_skill_contract.py 重新渲染 skill 副本 references/cli-json-contract.md（test_skill 断言副本等于渲染结果）
- 单独先落地的后果：只加词、不清命中：cli/tests 下 test_user_docs（CHANGELOG、configuration.md、running-and-results.md）、test_code_comments（约 50 行注释）、test_technical_docs（internals 与 deploy_aws/DEVELOPMENT.md）以及图源扫描一起红；产品行为不受影响。加表之后，commit-gate 与写完即查的 hook 会拦下暂存文件里残留的这三个词。反过来，在接力删除之前只清「接力推进」的命中、不加表，等于给一个还在运行的机制换临时叫法，之后删接力时还得再改一遍。
- 验证：这条只动文字，单测加护栏检查就够了，不涉及 mock 之外的真实行为。具体：跑全量测试，重点是 cli/tests/test_user_docs.py（含 test_retired_terms_are_all_in_the_glossary 与 SVG 指纹）、test_code_comments.py、test_technical_docs.py、test_skill.py、test_package_readmes.py；对改过的文件跑 uv run python tools/doc_rules_check.py --uncommitted，看退出码。图要在本机真实执行一次 node tools/build_diagrams.mjs docs/diagrams/execution-timeout-chain.json：它依赖 ~/.agents/skills/archify、本机 Chrome 和 engines/midscene 的 node_modules，是工具的真实执行，不是产品行为。最后 git grep 这三个词，核对测试管不到的面：code 里的字符串字面量（--help 与提示）、ADR、CONTEXT 与 journey 以外的残留。
- 备注：1）线索里的位置都找到了，与 code 现状相符。CONTEXT 里三个词已分别列在「推进器」（第 242 行）与「job 到点停止」（第 282 行）的 _Avoid_ 下，test_retired_terms_are_all_in_the_glossary 加表后照样通过，不用改 CONTEXT。「推进方」也已在第 242 行的 _Avoid_ 里。
  2）护栏有一个漏洞，线索没写：RETIRED_TERMS 在 code 里只扫注释与 docstring（scan 的 code 分支用 comment_units），test_user_facing_messages.py 只用 FORBIDDEN。所以 __main__.py 里带「接力推进」的用户可见字面量不会被测试拦，加表后测试照样全绿：第 475、479 行 status --wait 与 --max-concurrency 的 help，第 2112 行的 pending 提示「可接力推进」，第 2200 行的 _WAIT_WITHOUT_RELAY_NOTICE，第 2747 行的错误信息。ADR 0045 决策八要求「人读层全改」，这些要靠人工检索，或者删接力时随代码一起删去。
  3）多数命中所在的 code，别的块本来就要改写或删除：「接力推进」在 detached、__main__ 的 status 与 run_store/local 一带，和本机接力删除同批；「超时处置」集中在 lambdas/reconciler.py、stack.py、test_lambda_handlers.py，和云端块同批；还有 reconcile.py 与 project.py 的收尾注释，和结束写块同批。这条单独先做，相当于把这些行先改一遍、之后再改一遍。Lambda 源码里只改注释不用重新部署：skew 闸比的是包版本，不比代码哈希。
  4）建议把这条拆成两半落地：「超时处置」「到点处置」并进云端块那一批（或者更早，作为纯改名）；「接力推进」并进本机接力删除那一批，或排在它之后。
  5）待定的其余 _Avoid_ 词。按同一套扫描规则（ADR、CONTEXT、journey 这类 ai-doc 面不扫退役词）模拟得到：
  - 「遗留 run 收尾」0 处命中，进表零成本。
  - 「发起进程标识」只有 1 处，就是线索点名的那个文档串。
  - 「进程核对」3 处全是合法的普通用法：subprocess_engine.py 的「父进程核对收尾」，test_conditional_writes.py 与 test_local_run_store_lock.py 的「真实进程核对」。正则分不出两种意思，不宜进表，和「推进方」「批次」同理。
  - 「推进方」：扫描面上 15 行、12 个文件，没有命中「推进方式」；但 ADR 0034 第 311 行有「推进方式」，是合法用词，佐证它只进 _Avoid_。
  - 「到期收尾」31 行、17 个文件，含 skill 副本 cli-json-contract.md。
  - 「收尾写」45 行、20 个文件，几乎全在结束写块要重写的 code 与测试里（try_finalize、_finalize、persist、errors.py）。
  要是这两个词进表，宜和结束写块同批。
  6）_LAUNCHER（{pid_namespace, pid, start_time, host}）和 "launcher" 键在生产 code 里已经没有使用者，只在这个测试里当附加键的示例，形状模仿的是已被生命期锁取代的发起进程标识设计。不管「发起进程标识」进不进表，都可以换成中性的示例键。
  7）execution-timeout-chain.html 没有入库，只需重新导出 SVG。

## 状态取法与结束写（core 与两个 RunStore adapter）

### 小结

整体改动量：L。core 的 project.py、schedule.py、persist.py、reconcile.py，ports.py，两个 RunStore adapter，加上 runtime、deploy_aws 各一处调用方；测试波及 4 个包约 20 个文件，其中 try_finalize 在 14 个测试文件里被当作准备步骤，RUN_DEADLINE_PASSED_MESSAGE 在测试里约 54 处。

端口与两个 adapter 的分步，每一步都保持测试通过：
1. 纯加法：
   - core 加 run 状态取法函数与结束写说明表常量。
   - JobState 加 job 级说明字段，serialize 与 DDB item 映射都省略 None。
   - ports.py 新增结束写入口，两个 adapter 各实现一份，与 try_finalize 并存，补本机文件与 moto 对拍用例。
   - DDB 版要用写入序号，必须与云端块「每个 DDB 写入口都把序号加一」同步落地；也可以这一步先只实现 local，DDB 版随序号一起上。

   这一步没有调用方，产品不变。
2. 前台一批：
   - 状态-1、2、8 一起换掉 run_verdict 与过滤名单，期限截断改记 aborted。
   - 状态-5 是 update_job_state 新语义。
   - 状态-9 让 schedule 不再构造 skipped，并改写 RunPersistence.finalize：本进程写成终态时生成报告，还有未结束的 job 时做结束写。
   - tick 的到期收尾在同一批改用结束写，避免后台丢掉 run 级说明。
   - 状态-3 的 ADR 回填一起提交。

   这时后台的「全部 job 已结束」那一路仍可走旧的 project_state（写终态）加 try_finalize，状态由取法算出，结果正确。状态-10 与这些都不耦合，可以最先单独落地。
3. 后台一批：
   - 状态-6 加状态-7：投影钳在 running，tick 逐 job 写终态，plan_next 删去 finalize。
   - 删去 try_finalize 与 expected_claim_count，测试准备步骤统一换成新入口。
   - 状态-11 的 error 变体。

   云端 Lambda 与 DDB adapter 的部分集中到这一批，与云端块同一次重新部署。

对别的块的依赖：
- DDB 写入序号（云端块第 1 条）是 DDB 结束写与终态写安全的前提。
- 判定明细的点名标识（判定明细块）可以晚一步：update_job_state 先不带标识，那一块再加键。
- 报告从记录生成（报告块）之前，COMMITTED 仍用 project_full 的结果。
- run --json 的 jobs[] 按记录列出，以及 run 的退出码改读记录（查看命令块），在状态-9 之后才完整。

最大的风险有三个：
- update_job_state 一旦按取法使 run 成为终态，RunPersistence.finalize 必须同批改，否则每个正常结束的前台 run 都会报「已被别处结束」、以退出码 1 结束。
- 投影钳在 running 与 tick 逐 job 写终态必须同批，否则后台 run 永远停在 running。
- 期限截断改记 aborted 必须与取法同批，否则旧的过滤名单会把这种 run 判成 passed。

此外，云端以序号为条件的整体替换只能在真实 DynamoDB 与重新部署之后的云端验证，期间新 CLI 与旧 Lambda 混用时，序号条件形同虚设。

### 线索没有覆盖的改动点

- JobState 缺 job 级说明字段：结束写给每个 job「各带一句说明」，由结束写结束的 job 的说明只在运行态里（0031 决定三「结束写」小节；0041 决策三「状态与由结束写结束的 job 的说明取运行态」；0027「index.html 形态」）。现在 core/gherkai_core/model.py 的 `JobState` 只有 scope_id、status、session_id、claimed_at。要改的有：model.py 加字段；serialize.py 的 run_state_to_dict 与 run_state_from_dict 里 job 条目加省略 None 的键；adapters/run_store/ddb.py 的 `_job_state_to_item` 与 `_job_state_from_item`；local 的 project_state 合并时保留它。ADR 0030 决定五列出的落盘键（scope_id、status、session_id、claimed_at、点名标识）没有这个键，ADR 要补一句，交人确认。
- 结束写的说明表要在 core 有一处唯一的常量（0031 决定三「结束写」小节的说明表：执行方到期、fail-fast、使用方中断、处置两行、运行定义不可用，处置句末加「（已记为已结束）」）。现在散在 run_deadline.py `RUN_DEADLINE_PASSED_MESSAGE`、schedule.py `_SKIPPED`（文案与表不同），以及 reconciler.py `_load_definition` 的三句；处置方（runtime）、前台（persist）、后台（reconcile）都要从这一处取。
- update_job_state 要有结束时刻的来源：0031 决定三与 0030 决定四要求「使 run 成为终态的那次写同时写下结束时刻」，而 adapter 不取时钟，core 只经注入的时钟取时刻（0054 决策二）。core/gherkai_core/ports.py `RunStore.update_job_state` 的签名要加 ended_at 一类的参数，两个 adapter 与 RunPersistence、tick 的调用跟着改；这一点线索与 ADR 都没写。
- 多个 job 一次记终态的端口入口：0030 决定三「后台推进同守」与 0054 决策二写的是「一次写可记多个 job，各点名各自的一份」，现在的 `RunStore.update_job_state` 一次只写一个 job（core/gherkai_core/ports.py）。tick 改成逐 job 写序时，要么新增批量入口，要么接受一轮多次写（云端每次写都按整个 STATE item 计费）。线索没有说用哪一种。
- 调用方要能知道自己这次写是否使 run 成为终态：报告只由使 run 成为终态的那次写的写入方生成（0030 决定三 run 结束一段、0027「ReportStore 接口：整 run 一次写」），而 0030 决定四规定 update_job_state 返回「这次写之前 run 是否仍未结束」。core/gherkai_core/persist.py 与 reconcile.py 要据此推断，或者改端口返回值（后者要改 0030 决定四，交人拍板）。
- 到期结束写「以这一轮读到的写入序号为条件」的读值怎样从 tick 传到端口（0054 决策二后台推进条「收尾与报告」）：现在 RunState 没有写入序号字段（core/gherkai_core/model.py），本机也没有这个量。要定下来：RunState 加一个可为 None 的序号字段由 tick 传入，还是结束写入口收一个按运行态表达的条件（「没有 running 的 job」），由 adapter 在锁内或读之后判断。
- DDB project_state 写 run 状态的位置与 ADR 不符：core/gherkai_core/adapters/run_store/ddb.py 第 405–411 行在标量那一步写 status 与 status_group；0034 机制三「② 的 job 级半边落地形态」与「投影写的 run 状态」段要求标量一步只推进 HWM，run 状态在把 job 写成 running 的那一次逐 job 写里一起写，并带「run 未结束」的条件。这一块的状态投影线索只说「run 级只写 running」，没写位置；可能算在云端块。

### 逐条

#### 状态-1（mixed，S）

- 线索：删去 run 级的过滤名单与空判定集规则：`_aggregate` 只在终结函数内容完整那一行
- 要做的：删去 model.py 的 `_NON_VERDICT`（含它上方注释、`TERMINAL_STATUSES` 注释里与它对照的几句）。`project._aggregate` 改成只收 worker 三态的归约（有 error 取 error，否则有 failed 取 failed，否则 passed），删掉过滤与「判定集为空按 aborted/skipped/running/pending 取」的分支。调用方只剩 `finalize_job` 内容完整那一行：`project()` 第 364 行用它算 run_status、`run_verdict` 用它算 run 级，这两处要同时改用新的 run 状态取法（状态-2）。
- 文件：core/gherkai_core/model.py、core/gherkai_core/project.py、core/tests/test_lifecycle_states.py、core/tests/test_project.py
- 先要有：run 状态取法函数（状态-2）
- 必须同批：状态-2（删 run_verdict、新增取法）：run_verdict 与 project() 现在把含 skipped/aborted/pending/running 的列表交给 _aggregate，单独删过滤就会算错
- 单独先落地的后果：只删过滤时，run_verdict 与 project() 交进来的前置态和派生态会被当成判定：全 pending 的投影会得出 passed（被当作终态，投影写把它钳成 running，plan_next 不受影响），中断的 run 得出错的状态。test_lifecycle_states 里 `_NON_VERDICT` 的等式与 `test_aggregate_*` 一组（第 63–116、234 行附近）会变红。
- 验证：单测就够（纯函数）：改写 test_lifecycle_states 里 _aggregate 的一组，只喂三态；另加一条断言 finalize_job 内容完整那一行与 _aggregate 一致。
- 备注：code 与线索一致：`_NON_VERDICT` 在 model.py 第 212 行，`_aggregate` 在 project.py 第 759 行。空输入现在返回 passed，docstring 拿「旧版本 CLI 提交的零个 job 的 run」作理由；按「不为旧数据留路」这条理由可以删，finalize_job 在调用之前已先判空集为 error，所以空输入到不了。test_lifecycle_states 第 83–85 行「两把刀」那组断言要随之删去。

#### 状态-2（mixed，L）

- 线索：删去 `run_verdict` 与 `RunVerdict`（聚合之外的例外、到期优先于中断
- 要做的：在 project.py 新增 run 状态取法函数（名字待定，例如 `run_status_of(statuses)`）：有未结束的 job 时，全部 pending 得 pending、否则 running；全部结束时依次看 error、failed、aborted 或 skipped，都没有则 passed。删去 `RunVerdict` 与 `run_verdict`。`schedule()` 的 RunResult.status 改用取法计算，算的时候把没有启动的 job 当作 skipped（`run --no-report` 在内存里按取法算，0031 决定五），message 恒为 None。`project_full` 的 status 同样改用取法，message 为 None，并删去 past_stop_start 参数。`projected_run_status` 用取法对钳到 running 的投影取值来代替，或者保留为它的薄封装。`RUN_DEADLINE_PASSED_MESSAGE` 并入结束写的说明表常量（见 missing）。
- 文件：core/gherkai_core/project.py、core/gherkai_core/schedule.py、core/gherkai_core/model.py、core/gherkai_core/run_deadline.py、core/gherkai_core/reconcile.py、core/gherkai_core/persist.py、core/tests/test_project.py、core/tests/test_schedule.py、core/tests/test_persist.py、core/tests/test_reconcile.py、core/tests/test_termination_parity.py、core/tests/test_cloud_reconcile.py、core/tests/test_subprocess_engine.py、runtime/tests/test_detached_launcher.py、cli/tests/test_main.py、cli/tests/test_render.py、cli/tests/test_cli_json_contract.py
- 先要有：结束写入口（状态-4）已在端口与两个 adapter 上可用：run 级说明要改由它写下
- 必须同批：状态-1；状态-8（期限截断记 aborted）：旧的 run_verdict 加过滤会把 [passed, aborted] 聚合成 passed，必须由新取法接住；状态-9（前台没有启动的 job 由 RunPersistence.finalize 的结束写记 skipped）：否则到期这一路的 run 级说明「已超过允许运行的时间」没有人写，记录里 run 是终态而 job 还停在 pending；tick 的到期收尾改用结束写（状态-7 里与 finalize_expired 对应的那一步）：project_full 不再给说明，后台到期的 run 同样会丢掉说明
- 单独先落地的后果：只换成取法、不接结束写时，到期 run 的 run 级 status 从 error 变成 aborted，run 级 message 为 None，try_finalize 也不再写说明；记录里出现「run 已终态、job 仍 pending」（这正是 0031 决定三拒绝的形态），status 与 list-runs 都看不到原因。RUN_DEADLINE_PASSED_MESSAGE 在 4 个包的测试里有约 54 处引用，test_project 的「run 级裁决」一节与 test_schedule 里中断、期限两组都会变红。
- 验证：取法本身靠单测（参数化真值表，包括零个 job 得 passed）。schedule 在中断与期限下的 run 级结果靠 fake clock 单测。使用方中断的真实信号路径（SIGINT 到 CLI 进程，交给 schedule 的 interrupt 轮询）要在本机真实执行一次 `gherkai run`，带引擎：跳板机上真实执行，Ctrl-C 之后核对 run_state.json 里 run 与各 job 的状态和退出码 130。
- 备注：这是用户能看到的行为变化：已过停止启动、还有 job 没有启动的 run，以前记 error 加说明，现在记 aborted（没有 job 出 error 时），退出码仍是 1；CHANGELOG 与用户文档由行为文档那一块跟进。`projected_run_status` 能不能删，看 project_state 怎样钳制（状态-6）。schedule.py 第 66 行 import run_verdict、第 774 行调用它；reconcile.py 第 247 行的注释与 persist.py 第 186 行的注释都要改。0031 决定五要求 `run` 的退出码读记录里的 run 状态（数据源），现在 CLI 读的是 schedule 返回的内存值（__main__.py 第 3224 行）；取法一致时两者相同，改读记录归不归这一块，拿不准，可能在查看命令那一块。

#### 状态-3（adr，S）

- 线索：实装定下 run 状态取法函数的名字之后，回填 ADR 0031「touch points」
- 要做的：把 0031「touch points」里 project.py 一条的「run 状态的取法（决定三）」改成具体符号（状态-2 定下的函数名）。核对 schedule.py 一条里列出的赋态点符号（`abort_flag`、`stop_reason`、`project.finalize_job`）是否因改动而换名；如果 0031 正文提到结束写入口的方法名，与 ports.py 核对。
- 文件：docs/adr/0031-job-lifecycle-states-and-severity.md
- 先要有：状态-2 定下取法函数名；状态-4 定下结束写入口的方法名
- 必须同批：状态-2（同一提交带上它所改行为的文档）
- 单独先落地的后果：无（只改文档）；如果先于 code 落地，touch points 指向的是还不存在的符号。
- 验证：用 `uv run python tools/doc_rules_check.py --uncommitted` 与 cli/tests/test_adr_hygiene.py 检查；再 grep 回填的符号名，确认 code 里有。
- 备注：0031 touch points 现在写的是「run 状态的取法（决定三）」，没有符号。schedule.py 一条描述的已是目标行为（不启动的 job 留在 pending，由结束写结束），code 跟上之后才成立。

#### 状态-4（mixed，L）

- 线索：端口新增结束写入口，取代 `try_finalize` 与它的 `expected_claim_count`
- 要做的：在 ports.py 的 RunStore 上新增结束写入口（名字与参数待定，例如 `end_run(run_id, *, ended_at, note)`；note 是 core 里的值对象，带 run 级说明以及 skipped、aborted 各一句，error 变体只带一句、把每个未结束的 job 记成 error）。返回是否写成；STATE 不存在时返回 False。local：用 `_locked_rmw` 实现，run 已结束时返回 None；否则把 pending 的 job 记 SKIPPED、running 的记 ABORTED，各带说明，保留 session_id 与 claimed_at，run 状态按取法计算，并写下 ended_at 与 message。DDB：先强一致 GetItem 读 STATE，算出整份 jobs 与 run 状态，再 update_item：整体替换 jobs，同时写 status、status_group、ended_at、message，写入序号加一；条件是 `#st IN (pending, running) AND 序号 = 读到的值`。CCF 时重读，已结束返回 False，否则重算再写。删去 `try_finalize` 与 `expected_claim_count`，调用方改用新入口（RunPersistence.finalize、tick 的到期收尾、reconciler._load_definition）。
- 文件：core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/model.py、core/gherkai_core/serialize.py、core/gherkai_core/project.py、core/gherkai_core/persist.py、core/gherkai_core/reconcile.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、core/tests/test_conditional_writes.py、core/tests/test_status_group.py、core/tests/test_ddb_run_store.py、core/tests/test_stores.py、core/tests/test_local_run_store_lock.py、core/tests/test_cloud_integration.py、core/tests/test_persist.py、core/tests/test_reconcile.py、runtime/tests/test_detached_launcher.py、cli/tests/test_main.py、deploy_aws/tests/test_lambda_handlers.py、deploy_aws/tests/test_workers.py
- 先要有：run 状态取法函数（状态-2；可以先作为纯加法落地）；JobState 的 job 级说明字段（见 missing）；DDB STATE 的写入序号：每个 DDB 写入口都把它加一（云端块第 1 条）
- 必须同批：DDB 一侧：云端块「STATE 条目带写入序号」一条。整体替换 jobs 只有在所有别的写（认领、投影）都加序号时才安全，否则会盖掉并发落下的认领
- 单独先落地的后果：按「加入口、旧入口不动、没有调用方」先落地时，测试全绿、产品不变。删去 try_finalize 时影响很大：14 个测试文件把它当作把 run 置成终态的准备步骤（test_status_group、cli test_main、deploy test_workers 等），要一起改成用新入口；生产调用方有 4 处（persist.finalize、reconcile._finalize、reconciler._load_definition，以及 run_store 的两个实现）。
- 验证：本机文件与 moto 两个 adapter 的对拍单测：pending→skipped、running→aborted，run 状态按取法，写成之后再写返回 False，STATE 不存在返回 False，error 变体，顶层附加键保留。本机锁内并发：两个真实进程同时做结束写，只有一方写成，要真实执行（文件锁属于真实行为）。DDB：moto 只能验证条件表达式，以序号为条件的整体替换在并发下的正确性、几百个 job 的结束写（含每个 job 的说明与点名标识，看 item 大小）要在真实 DynamoDB 上执行；经 Lambda 的那一半要在重新部署之后的云端验证（0034 机制三②的实测项）。
- 备注：线索和 ADR 都只说「方法名与参数由实装定」。拿不准的是：到期收尾要求「以这一轮读到的写入序号为条件」（0054 决策二后台推进条「收尾与报告」），所以要么 RunState 带写入序号字段、由 tick 传入，要么端口收一个条件（例如「没有 running 的 job」），由 adapter 在锁内或读之后判断；本机没有序号。两种做法都要先定。0030 决定六说结束写「与 local 同样在 STATE 不存在时返回 False」，现在的 try_finalize 也是这样。reconciler._load_definition（第 417 行）改用 error 变体属于云端 Lambda，要等重新部署才生效（见状态-11）。DDB 的 item 大小：0034 的 1327 个 job 上限是在不带 job 级说明的样本上测的，这次加了说明，要重测。

#### 状态-5（mixed，L）

- 线索：`update_job_state` 改为新语义：同一次写按取法写 run 状态（云端连同 status_group）
- 要做的：local 的 mutate：run 已结束时返回 None（写不成、返回 False），删去「已收尾仍写 job」那条；库中 job 已是终态时不覆盖（终态只写一次）。否则写入这个 job，用取法对整份 jobs 重算 run 状态，使 run 成为终态的那次写同时写 ended_at。DDB：删去第 319–326 行的回退写。running 写仍按单元素 SET，条件 `attribute_exists AND #st IN (pending, running)`，并把序号加一；终态写改成先读 STATE、算出整份 jobs 与 run 状态（含 status_group），对 jobs 整体替换，条件是序号等于读到的值，CCF 时重读再算。端口签名要加上结束时刻的来源（adapter 不取时钟），也可能要加一个一次写多个 job 的入口（见 missing）。ports.py 的 docstring 改写。
- 文件：core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/persist.py、core/tests/test_conditional_writes.py、core/tests/test_persist.py、core/tests/test_stores.py
- 先要有：run 状态取法函数（状态-2）；DDB 写入序号（云端块第 1 条）
- 必须同批：RunPersistence.finalize 的改写：能识别「本进程最后一次终态写已使 run 成为终态」，此时生成报告、不抛 RunAlreadyEnded，只在还有未结束的 job 时做结束写（状态-9 与判定明细块里 RunPersistence 那一条）；状态-2
- 单独先落地的后果：只改 update_job_state 时，前台每个正常跑完的 run，最后一个 job 的终态写已经让 run 成为终态，随后 RunPersistence.finalize 的 try_finalize 写不成，抛 RunAlreadyEnded，CLI 对每个成功的 run 都打印「已被别处结束」并以退出码 1 结束，报告也不生成。这是最危险的单独落地。test_conditional_writes 里断言旧设计的用例（`test_job_write_on_finalized_run_lands_job_only`、`test_job_write_on_a_finalized_run_reports_it_ended`、`test_ddb_job_write_update_item_counts`、`test_ddb_job_write_does_not_report_ended_on_a_run_created_between_its_two_writes`）会变红。
- 验证：两个 adapter 的对拍单测：run 已结束时写不成、运行态不变（DDB 只发一次 update_item）；终态只写一次；最后一个终态写使 run 成为终态并写下 ended_at；run 状态与 status_group 一致（test_status_group 的不变量测试）。并发：本机前台主线程与 worker 线程同时写（文件锁）已有单测覆盖。DDB 以序号为条件的终态写，两个进程并发时恰好一方写成：真实 DynamoDB，经 Lambda 的那一半在重新部署之后验证。
- 备注：按 0030 决定四，返回值是「run 在这次写之前是否仍未结束」，所以调用方看不出是不是自己这次写使 run 成为终态，而报告只能由那一方生成。RunPersistence 要么自己推断（它记得自己写下终态的 job 集合），要么端口返回更细的结果；后者要改 0030 决定四，交人拍板。库中 job 已是终态而 run 未结束时返回什么，ADR 没写。cloud `run` 删去之后（另一块），DDB 的 update_job_state 在生产里只剩 tick 的终态写这一个调用方（状态-7）；现在 tick 还不用它。

#### 状态-6（mixed，M）

- 线索：状态投影只推进运行态：`project_state` 的逐 job 合并不越过 running、不写 job 终态
- 要做的：local 的 `project_state`：投影里是终态的 job 按 running 合并（等级不超过 1），库中已是终态的 job 保持不变；run 级只写 RUNNING，也就是对钳制后的 jobs 用取法计算，全部 pending 时不写 run 状态。DDB 的 `project_state`：删去 `new_rank >= 2` 那个分支（现在它允许终态覆盖库中任何状态），终态改按 running 写，条件是 `IN (pending, running)`；按 0034 机制三②，run 状态改在「把 job 写成 running 的那一次逐 job 写」里写，标量那一步只推进 HWM；每次写都把序号加一（云端块）。project.py 的 `project()` 照常给出各 job 的推演状态（包括终态，供 tick 判断哪些 job 已有结果），run_status 改用取法。
- 文件：core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/project.py、core/tests/test_conditional_writes.py、core/tests/test_project.py、core/tests/test_reconcile.py、core/tests/test_cloud_reconcile.py
- 先要有：状态-2（取法）
- 必须同批：状态-7（tick 逐 job 写终态）：投影不写终态之后，后台 run 的 job 只能由 tick 的终态写结束
- 单独先落地的后果：只钳投影时，后台 run（本机 submit 与云端）的 job 永远停在 running，plan_next 因为有 running 永远不提议收尾，run 停住，现在只有期限加 300 秒的处置能把它带出来，而处置还没实装，所以会一直挂着。test_conditional_writes 里同 HWM 终态不回退、终态覆盖等对拍用例，以及 test_reconcile 的收尾用例都会变红。
- 验证：两个 adapter 的对拍单测：投影里的终态 job 落成 running，库中终态不被投影改动，全 pending 投影不写 run 状态。DDB 的逐 job 写次数断言（moto）。run 状态改由逐 job 写写下之后的索引写计费，要在真实 DynamoDB 上用 ReturnConsumedCapacity 重核（0034 实测项 6 的形态变了）；经 Lambda 的那一半要重新部署之后验证。
- 备注：与 ADR 不符：ddb.py 第 405–411 行现在在标量那一步写 run 状态（status 加 status_group），而 0034 机制三「② 的 job 级半边落地形态」写的是「标量一步只推进 HWM、不写 run 状态」，run 状态随把 job 写成 running 的那次逐 job 写一起写。线索没提这一点（列入 missing）。ports.py 的 project_state docstring（「run 级 status 只写 running、不落终态，终态是 finalize 专属」）要改写。

#### 状态-7（mixed，L）

- 线索：后台推进改为逐 job 写序：这一轮快照里已有结果的各 job 先存明细、再以一次条件写
- 要做的：reconcile.tick 在投影之后：对投影为终态、库中未结束、且 baseline 带认领时刻的 job（按 job 做快照检查，代替 `_claim_times` 的整轮全有或全无），逐个归约出 JobResult，先存明细，再用一次条件写记下这些终态（一次写可以记多个 job）；写不成时重读再算，使 run 成为终态的那次写返回 COMMITTED。plan_next 删去 `finalize` 动作，`finalize_expired` 改成到期结束写，判据是「这一轮运行态里有 pending、没有 running」，删去 `recorded` 参数（不读事件）。到期动作调用结束写入口（状态-4），说明取「执行方自己到期」那一行。删去 `_finalize` 里的 project_full 加 try_finalize，以及 `NonTerminalSnapshot` 这一路。project_full 改成按 job 给出明细（或拆成逐 job 的函数）。
- 文件：core/gherkai_core/reconcile.py、core/gherkai_core/project.py、runtime/gherkai_runtime/detached.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、core/tests/test_reconcile.py、core/tests/test_cloud_reconcile.py、core/tests/test_project.py、core/tests/test_termination_parity.py、runtime/tests/test_detached_launcher.py、deploy_aws/tests/test_lambda_handlers.py
- 先要有：update_job_state 新语义或多 job 终态写入口（状态-5）；结束写入口（状态-4）；状态-2（取法）
- 必须同批：状态-6（投影不越过 running）；报告生成：COMMITTED 现在用 TickResult.result；过渡期可以继续用 project_full 的全量结果，最终从记录组装（报告块）
- 单独先落地的后果：只改 tick、不钳投影时，投影已把终态写进库，tick 的「库中未结束」筛不出要写的 job，run 状态没有人按取法写成终态，后台 run 停在 running。不改 plan_next 而删 finalize 动作时，没有结束出口。云端一侧要重新部署才生效：部署之前 Lambda 仍跑旧 tick（投影写终态、再 try_finalize）。旧 Lambda 能读新 code 写出的 item（`_job_state_from_item` 用 .get，忽略多出的键）。
- 验证：core 单测（假的 EventLog、RunStore）覆盖逐 job 写序、终态只写一次、COMMITTED 与 ENDED、到期按运行态里的 pending 判断。本机后台推进进程要真实执行一次 `submit --backend local`（真实子进程 worker、SQLite 事件库），带引擎：跳板机上真实执行，核对各 job 的终态逐个落下、最后一次终态写使 run 成为终态、报告只生成一次。云端：重新部署之后执行多 job 的 submit，看两个重叠的 Lambda 调用各记一部分 job 时 run 是否正确成为终态（0034 机制三②实测项），要真实 DynamoDB 与重新部署后的云端。
- 备注：线索写「一次写可记多个 job」，但现有端口的 update_job_state 一次只写一个 job（见 missing）。`_claim_times`（第 219 行）现在是整轮全有或全无（有一个缺认领时刻就整轮不收尾）；目标是按 job 判断（0054 决策二后台推进条「快照」：不带认领时刻的那个 job 这一轮不写）。保存明细失败时的退避重试属于判定明细块。零个 job 的 run：plan_next 删去 finalize 之后，没有最后一次终态写，所以没有人结束它；CLI 对零个 scenario 的批次以退出码 2 拒绝，到不了这里，但取法说它应是 passed，值得在 code 注释里交代。reconciler.py `_tick_runs` 消费 TickResult，属于云端 Lambda，宜与云端块同批重新部署。

#### 状态-8（mixed，M）

- 线索：终结函数真值表的 timeout 一行拆成两行：起作用的截止时刻是 job 预算时记 ERROR
- 要做的：`finalize_job` 的 `stop_reason == timeout` 分支：timeout_cause 为 budget 时保持 ERROR、timeout 与预算那一句；为 deadline 时改成 ABORTED、error_type None、说明 `DEADLINE_TIMEOUT_MESSAGE`。`run_deadline.job_cutoff` 已按「相等算预算」实现，不用改。改写 finalize_job、`_reduce_scope`、`project()` 里「超时的 job 不论哪个截止时刻都是 error」「这条规则不改变状态」的 docstring；从 `TaskExited` 与 stop_reason 来源的说明里去掉接力补写。
- 文件：core/gherkai_core/project.py、core/tests/test_project.py、core/tests/test_schedule.py、core/tests/test_termination_parity.py、core/tests/test_reconcile.py、core/tests/test_cloud_reconcile.py
- 先要有：状态-2（取法）
- 必须同批：状态-2：现在的 run_verdict 加 _aggregate 会过滤掉 aborted，[passed, 期限截断的 aborted] 会聚合成 passed
- 单独先落地的后果：单独落地时，被期限截断的 job 记 aborted，而 run 级聚合过滤掉 aborted，有一个 job 被期限截断、其余通过的 run 会记成 passed、退出码 0，结果是错的。test_project、test_schedule、test_termination_parity 里期限截断那几行（断言 error 加 timeout）会变红。
- 验证：单测就够判定逻辑本身（终结函数是纯函数，加上前台与后台的对拍矩阵：期限一行与预算一行分开，各带一个「两者相等时算预算」的用例）。截止时刻真实到点、worker 被停下的端到端链路属于期限与停止，靠已有的真实执行实测；这条线索只改判定行，不另需真实执行。
- 备注：code 现状：project.py 第 599–606 行两种 timeout_cause 都记 ERROR 加 timeout，只有说明不同。`DEADLINE_TIMEOUT_MESSAGE` 现在只用在说明里；改完之后它是 aborted 的说明。`project()` 对读不出认领时刻的 job 用 timeout_cause="budget"（第 349 行），状态会是 error 而不是 aborted。但 tick 的快照检查不为这种 job 写终态，投影也钳在 running，不进记录；docstring 要说明这一点。「stop_reason 的来源去掉接力补写」在这个文件里只涉及注释；补写本身（`record_timed_out_if_absent`）的去留在本机推进器那一块。

#### 状态-9（mixed，L）

- 线索：前台没有启动的 job 不再构造 skipped 的 JobResult：起 worker 之前三项检查
- 要做的：`_Worker._run_once` 第一次尝试时，`_hold` 命中 fail-fast 或 interrupt 也返回 None（不启动，job 留在 pending），删去 `_SKIPPED` 字典与构造 SKIPPED JobResult 的分支。schedule 要把「这次执行因哪条来路停止启动」（停止启动已成立、中止来源）交给组合根或落库服务，例如作为 RunResult 上的一个字段或 schedule 的另一个返回值，供 `RunPersistence.finalize` 选说明表里的一行。`RunPersistence.finalize`：本进程的写还没使 run 成为终态、且有未结束的 job 时，做结束写（说明按来路取）；已发现 run 被别处结束时不写，抛 RunAlreadyEnded。改写 `_stop_all`、`_Worker.run`、`on_job_complete` 的注释（不再有「skipped 也经此落库」）。
- 文件：core/gherkai_core/schedule.py、core/gherkai_core/persist.py、core/gherkai_core/model.py、cli/gherkai_cli/__main__.py、core/tests/test_schedule.py、core/tests/test_persist.py、core/tests/test_termination_parity.py、cli/tests/test_main.py、cli/tests/test_render.py、cli/tests/test_cli_json_contract.py
- 先要有：结束写入口（状态-4）；状态-2（取法；schedule 内存里的 run 状态把没有启动的 job 当作 skipped）；「多条来路同时成立时结束写取哪一行说明」这一待定问题先定（journey「写回时留下、实装之前要定的问题」第 6 条与第 12 条）
- 必须同批：状态-2；状态-5（RunPersistence.finalize 同时要识别本进程写成的终态）
- 单独先落地的后果：只让 schedule 不再构造 SKIPPED、finalize 仍走旧的 try_finalize 时，fail-fast 或中断之后没有启动的 job 留在 pending，而 run 被 try_finalize 写成终态，记录违反「run 终态时每个 job 都是终态」。`run --json` 的 jobs[] 少了这些 job，文本汇总把它们显示成「没有执行」（`jobs_without_verdict`）。test_schedule 里约 13 处断言 SKIPPED 的用例、test_render 与 test_cli_json_contract 的 skipped 用例会变红。
- 验证：schedule 的分支靠单测（假的 engine 与 RunRecord）。fail-fast 与使用方中断在真实执行下的结果要真实执行：跳板机上带引擎执行 `gherkai run --fail-fast`，让一个 job 出错，核对 run_state.json 里排队中的 job 为 skipped、说明是 fail-fast 那一行、run 为 error；再执行一次并发 SIGINT，核对 skipped 与中断那一行、退出码 130。期限那一路用短预算真实执行一次，核对 skipped、run 级说明「已超过允许运行的时间」、run 为 aborted。
- 备注：现状：schedule.py 第 454–462 行，deadline 与 ended-elsewhere 已经返回 None，fail-fast 与 interrupt 返回 SKIPPED JobResult；`_SKIPPED` 的文案（「fail-fast：本次运行已中止，未启动（worker 未 spawn）」）与 0031 说明表（「fail-fast：其他 job 出错，本 job 没有启动」）不一致，改用说明表常量。线索说「`_stop_all` 不给排队中的 job 记 skipped」：_stop_all 本身并不记 skipped，只是置中止标志，排队的 worker 看到之后自己记；所以要改的是 `_run_once`，_stop_all 只改注释。「被期限截断的执行中 job 记 aborted」由状态-8 实现，这里不另写。CLI 一侧：__main__.py 第 3175 行调 finalize(result)，如果来路以别的形式传，要跟着改。`run --json` 的 jobs[] 要按记录列出全部 job（0041 决策三），属于查看命令那一块；本批之后那一块落地之前，jobs[] 里没有这些 job。

#### 状态-10（mixed，S）

- 线索：核对重试之前的检查按分支落实：已过停止启动或已中止时写下上一次结果
- 要做的：`_Worker._retry_refused` 与它的两个调用点：命中 deadline、fail-fast 或 interrupt 时保持现状（在 previous 的说明后注明没有再重试及原因，作为终态写下）；命中 ended-elsewhere 时（含 still_open 读到终态、`ended.seen()` 成立）不写终态、不存明细：`_run_once` 与 `run()` 对这一支返回 None（或一个不进 on_job_complete 的标记），不把 previous 交给 on_job_complete。
- 文件：core/gherkai_core/schedule.py、core/tests/test_schedule.py
- 先要有：无
- 必须同批：无
- 单独先落地的后果：可以单独落地：已发现 run 被别处结束时不再调 on_job_complete，运行态本来就写不成；现在的行为是先存一份明细（没被点名的残留）再写，写不成。改完之后少一份残留明细，产品不受影响。test_schedule 里断言「重试被拦下时 previous 带注明」且命中 ended-elsewhere 的用例要改。
- 验证：单测就够（重试与停手信号都在注入的 RunRecord、fake clock 之内，判断只靠调度循环自己的逻辑）。
- 备注：现状：schedule.py 第 451–452 行 `_retry_refused(previous, read_record=True)` 命中任一项都返回 previous；第 377 行 read_record=False 那一处同样把 result 交回、随后经 on_job_complete 写下。两处都要对 ended-elsewhere 分支。另外，0054 决策五「执行方得知 run 已结束之后就不存明细」要求 RunPersistence.on_job_complete 在停手信号成立之后不存明细，属于判定明细与写序那一块；两处都改才完整。返回 None 会让 `run()` 的 docstring「None 表示没有启动」不再准确，要改写。

#### 状态-11（mixed，S）

- 线索：运行定义不可用时（结构版本不是后端认的、定义违约、缺 worker 镜像版本），云端推进器与本机
- 要做的：reconciler.py `_load_definition` 的 `_mark`：把 `try_finalize(run_id, ERROR, …, message=…)` 换成结束写入口的 error 变体（每个未结束的 job 记 error，说明与 run 级相同，不存明细，不点名），三种原因的句子不变。本机：`detached.build_local_reconcile` 在 `load_run_meta` 抛 UnsupportedDefinitionSchema、DefinitionContractError 时，现在原样抛出（后台进程退出，run 无人推进），改成用同一个 error 变体结束这个 run，然后退出。
- 文件：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、runtime/gherkai_runtime/detached.py、deploy_aws/tests/test_lambda_handlers.py、runtime/tests/test_detached_launcher.py、cli/tests/test_definition_schema.py
- 先要有：结束写入口的 error 变体（状态-4）
- 必须同批：云端一半：与云端块其余 Lambda 改动同一次重新部署
- 单独先落地的后果：云端：只改 code、不部署时没有效果，部署之前 Lambda 仍只写 run 级 error，job 留在 pending 或 running。本机：改完之前，读不了定义的后台 run 直接退出、停在原状态。
- 验证：单测（moto 与本机文件）：三种原因都使每个未结束的 job 为 error、run 为 error、run 级 message 是对应那一句。云端在重新部署之后真实执行：在真实 runs 表上提交一个 run，把 META 的 schema_version 改成后端不认的值（或去掉 worker_task_defs），触发 kicker，核对 STATE。0054 实测项要求本机与云端在这种情形下结果相同（「对照」一组），本机一侧同样真实执行一次。
- 备注：疑点：按本机推进器那一块的新设计（0054 决策三、0035 决策 3），本机后台推进进程自己生成运行定义并建 run，可能不再从库里读回定义；这样本机的「运行定义不可用」只剩文件被改坏这一种，本机这一半是否还需要在 build_local_reconcile 里接，要等那一块定了流程再看。现状里 build_local_reconcile 读到 meta 为 None 时抛 FileNotFoundError（第 331 行），这种情形不属于「运行定义不可用」的三种原因，保持不变。cli/tests/test_definition_schema.py 的 `test_local_relay_reports_contract_violation_with_exit_2_instead_of_traceback` 是接力路径的用例，随接力一起删（测试块）。

## 判定明细点名与落库写序

### 小结

整块改动量为 L：跨 core 的端口、两个 ResultStore adapter、JobState 与 serialize、两个 RunStore adapter、RunPersistence 与 reconcile，再加上 runtime 组合根与 CLI 的 explain 和测试，合计几百行。内部次序：点名-2（JobState 加字段，可以单独先落、无害）→ 点名-1 与点名-3 的 on_job_complete 一半（标识、按标识保存、终态点名、本机重试），这两条必须同一批，而且要和后台 tick 的逐 job 写序（「状态取法与结束写」块）以及 explain 改为按运行态里的标识读（「查看命令」块）一起落，否则 submit 的 run 没有被点名的明细，explain 就读不到任何东西 → 点名-3 的 finalize 一半（改用结束写，从记录生成报告），要排在结束写入口与「报告」块从记录组装 RunResult 之后，或者同批。对别的块的依赖：结束写入口与 update_job_state 新语义（状态取法与结束写），从记录组装报告（报告），explain、status --json、run --json（查看命令），真实验证需要的生命期锁与 run 处置（本机推进器与 run 处置两块）。云端：Lambda 打包了 gherkai_core，改键、改 JobState、改 tick 写序之后，云端行为要等重新部署才变；CLI 一侧的 explain 先按新键读，就读不到旧 Lambda 写出的明细。所以这一块的 core 改动宜与云端那一批的重新部署对齐，或者在那之前接受云端 explain 暂不可用。最大的风险有三个：①删 load_all 与改键会造成过渡窗口，一定要与写入方和读者同批；②重试放在哪里：tick 与云端共用，重试只能放在本机一侧，标识还要在重试之间保持不变；③本机文件名长度（编码后的 scope_id 加标识可能超过 NAME_MAX）。

### 线索没有覆盖的改动点

- 前台执行方得知 run 已结束之后不存明细：RunPersistence.on_job_complete 现在不看停手信号（self._ended），照样 save_job_result 并写终态；schedule 在 ended_elsewhere 之后对仍在完成的 job 照常回调 on_job_complete。要在保存之前检查停手信号，成立就不存明细、不写终态。位置：core/gherkai_core/persist.py RunPersistence.on_job_complete。依据：ADR 0054 决策五「执行方得知 run 已结束之后就不存明细」条；0030 决定三「被点名的那一份就是写成终态的那一方存的」。（「查看命令」块 run --json 一条写到「不再存明细」，但没有点出这个位置。）
- 后台推进的终态写写不成、重读再算时，沿用已存的那一份及其标识，不再另存；改用别的结果时才另存一份。位置：core/gherkai_core/reconcile.py tick 的逐 job 写序（在「状态取法与结束写」块的新写法里）。依据：ADR 0030 决定三「被点名的那一份就是写成终态的那一方存的」条括注「写不成而重读再算时沿用这一份，改用别的结果先另存一份」。
- 机读契约页与 skill 副本里 artifacts 的 jobs_dir 一行写着「每 job 一份 JSON，文件名是 URL 编码的 scope_id……单文件自包含」，status --json 的 artifacts 一行写着「submit 提交的 run 在收尾时才写入」，这两处都与「每次保存一份、由终态点名、存放形态不是对外的约定」不符，要改写。位置：docs/internals/cli-json-contract.md 第 85、120 行；cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md 第 71、106 行。依据：ADR 0030 决定三「点名」条与「本机判定明细的落点」；ADR 0041 决策三「判定明细文件的存放形态不是对外的约定」。（「行为文档」块的契约页一条只列了 settle-runs、deadline_at、点名标识、run --json 的 jobs[]。）
- 以 load_all 或「每 job 一份」为前提的 code 注释，「随实装改写的 code 注释」块没有列出：core/gherkai_core/ports.py 里 ResultStore 的 docstring（「判定真值唯一权威」「每 job 落 <encoded_scope_id>.json」）；core/gherkai_core/adapters/result_store/s3.py 的模块头与 load_all 的 docstring；runtime/gherkai_runtime/compose.py 第 1320 行与第 1336 到 1339 行 job-in 用独立前缀的理由（「load_all 枚举 jobs/」）；runtime/gherkai_runtime/detached.py 第 220 行「判定真值（jobs/*.json）由 tick 在收尾的条件写之前落」；core/gherkai_core/adapters/_atomic.py 模块头与 atomic_write_text 里「jobs/<urlencode 后的 scope_id>.json」的落点说法。依据：ADR 0030 决定三「点名」条、决定六 ResultStore 段。
- 本机两种推进器的保存重试要放在本机这一侧（不放进 tick 与 S3ResultStore），线索没有写明。建议给 ResultStore 套一层由本机组合根装配的重试，或者从 tick 注入重试策略；退避用的 sleep 与标识工厂要可注入。位置：runtime/gherkai_runtime/compose.py build_local_stores、runtime/gherkai_runtime/detached.py build_local_reconcile、core/gherkai_core/persist.py。依据：ADR 0030 决定三「保存明细失败」条（云端由流的重试或之后的触发再做，本机两种推进器重试 3 次、用同一个标识）。

### 逐条

#### 点名-1（mixed，M）

- 线索：明细每次保存一个新对象、键里带写入方生成的随机标识
- 要做的：改 ResultStore 端口：save_job_result 增加写入方给出的标识参数（如 result_id），load_job_result 改为按标识取（是否还要 scope_id 视键形态而定），删去 load_all。LocalResultStore 改为每次保存写 <root>/<run_id>/jobs/<标识>.json（或 <quote(scope_id)>.<标识>.json），不再按 scope_id 覆盖同一个文件；S3ResultStore 的键改为 <prefix><run_id>/jobs/ 下带标识的一段，删去 list_objects_v2 翻页列举。两个 adapter 与端口的 docstring（「每 job 一份」「同 key 覆盖、幂等」「判定真值唯一权威」「CI 据 load_all 判退出码」）按 0030 决定三「点名」条改写。
- 文件：core/gherkai_core/ports.py、core/gherkai_core/adapters/result_store/local.py、core/gherkai_core/adapters/result_store/s3.py、core/gherkai_core/persist.py、core/gherkai_core/reconcile.py、runtime/gherkai_runtime/compose.py、cli/gherkai_cli/__main__.py、core/tests/test_stores.py、core/tests/test_s3_result_store.py、core/tests/test_local_result_store_atomic.py、core/tests/test_cloud_integration.py、core/tests/test_persist.py、core/tests/test_reconcile.py、cli/tests/test_main.py
- 先要有：写入方生成标识的位置（点名-3 的 RunPersistence.on_job_complete 与后台 tick 的逐 job 写序）
- 必须同批：点名-2（运行态里的点名标识，否则读者无从取那一份）；点名-3（前台写入方生成并点名标识）；状态取法与结束写块「后台推进改为逐 job 写序」（后台 tick 生成标识、终态写点名，否则 submit 的 run 一份被点名的明细都没有）；查看命令块 explain 一条（_explain_emit 现在调 load_all 与按 scope_id 的 load_job_result）；机读契约页与 skill 副本里 jobs_dir 一行的说明（现写「每 job 一份 JSON，文件名是 URL 编码的 scope_id」）
- 单独先落地的后果：删 load_all、改键之后 cli/gherkai_cli/__main__.py 的 _explain_emit 直接坏（AttributeError，或按 scope_id 取不到对象）；core/tests 里 test_stores、test_s3_result_store（含 1000 以上翻页、稳定排序两条用例）、test_local_result_store_atomic、test_persist（171、285、291、475 行用 load_all 断言）以及 cli/tests/test_main.py（848、990、1071 行用 load_all，3161、3547 行的假 store）都会变红。云端推进器 Lambda 打包了 gherkai_core，重新部署之前它仍按旧键写，CLI 一侧按新键读就读不到。
- 验证：单测够用于 adapter 行为：本机文件与 moto S3 对拍：同一个 job 存两份、各自按标识读回，互不覆盖；标识不同的两份不串；scope_id 含 /、:、中文时键是单段。test_cloud_integration 里的真实 S3 往返（opt-in，不用重新部署）改成按标识存取。云端端到端要在重新部署之后核：Lambda 写出的明细键带标识，explain 按运行态里的标识读到它，而且编排进程角色上没有 s3:ListBucket 也能读（0030 决定六、0042 决策四）。
- 备注：1）S3 键是否还带 scope_id 由实装定。本机文件名要考虑 NAME_MAX：现在文件名是 quote(scope_id)，中文一字就占 9 个字符，core/gherkai_core/adapters/_atomic.py 已经为接近 NAME_MAX 的这类文件名把 tmp 前缀截到 200 字符。如果在编码后的 scope_id 后面再接标识，长 scope_id 会更早遇到 ENAMETOOLONG；只用标识作文件名可以避开，读者也本来就从运行态拿 scope_id。2）runtime/gherkai_runtime/compose.py 第 1320 行与第 1336 到 1339 行讲 job-in 用 jobs-in/ 前缀的理由是「load_all 列出 jobs/ 前缀、会把 job-in 当判定读」。删了 load_all 这个理由就不成立了；独立前缀本身保留（生命周期规则按 tag 只框 job-in），注释要改写。3）core/gherkai_core/ports.py 里 ResultStore 的 docstring（「判定真值唯一权威」「每 job 落 <encoded_scope_id>.json」）与 s3.py 的模块头，「随实装改写的 code 注释」块没有列出。4）compose 的 local_artifact_locations 与 cloud_artifact_locations 里 jobs_dir 键可以保留（目录或前缀不变），但两份契约页对它的说明要改（见 missing）。5）skills/gherkai-evals/fixtures 下现存的 jobs/<scope>.json 与没有点名标识的 run_state.json，在新读法下 explain 读不到。重录已列在「行为文档」块，并且要和 explain 的改法同一批落地。

#### 点名-2（mixed，S）

- 线索：运行态每个 job 条目带点名的标识（未点名时省键）
- 要做的：model.JobState 加一个可选字段（如 result_id: str | None = None）。serialize.run_state_to_dict 与 run_state_from_dict 对这个键按 omit-when-None 读写；ddb.py 的 _job_state_to_item 与 _job_state_from_item 加同一个键。LocalRunStore.project_state 里那段重建 JobState 的回填（local.py 第 332 到 335 行，现在只回填 session_id 与 claimed_at）要把库中的标识带上，或者等到投影不再写 job 终态之后再删这段回填。
- 文件：core/gherkai_core/model.py、core/gherkai_core/serialize.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/tests/test_stores.py、core/tests/test_ddb_run_store.py、core/tests/test_conditional_writes.py、cli/tests/test_cli_json_contract.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md
- 先要有：无
- 必须同批：机读契约页 status --json 的 jobs[] 加这个键的说明（status --json 直接输出 run_state_to_dict，这个键一出现就进机读输出；test_status_json_keys_are_documented 一旦构造带标识的 JobState 就要求契约页登记它）
- 单独先落地的后果：无：字段缺省为 None，现在还没有写入方写它，落盘形态和 status --json 都不变。缺点是这段时间里有一个没人写的字段。
- 验证：单测够：serialize 往返（有值写键、None 省键）、本机与 moto 两个 adapter 在 update_job_state 整项写之后读回带键、project_state 之后键还在、DDB 逐属性投影不碰它。单条 STATE 能放下几百个 job 的结束写（按实际 job 项大小，含标识）要在真实 DynamoDB 上核，已列在「测试」块，要等重新部署后经 Lambda 的代码做。
- 备注：1）DDB 的 project_state 是逐属性 SET，没提到的属性天然保留，不用改。update_job_state 是整项 SET jobs.#sid = :js，只要 _job_state_to_item 带上这个键就会写进去。2）local 的 try_claim_job 重建 JobState 时只针对 pending 的 job，那时还没有标识，不受影响。3）cli/gherkai_cli/render.py 的 render_run_state 与 __main__.py 的人读 status 不需要显示这个键。4）字段名由实装定，0030 与 0041 都只说「点名的标识」，定名之后核对 0041 决策三的字段表。5）云端只有重新部署之后才会写出这个键（Lambda 打包了 core），CLI 一侧读到的是旧 Lambda 写出、不带键的条目，点名-1 的读者会因此读不到明细。

#### 点名-3（mixed，L）

- 线索：RunPersistence 按逐 job 写序：on_job_complete 先生成标识、存明细
- 要做的：RunPersistence.on_job_complete：先生成随机标识（建议注入标识工厂），带这个标识 save_job_result；本机失败按 1、2、4 秒退避重试 3 次，每次用同一个标识，sleep 要可注入；成功之后再 update_job_state，写下带认领时刻与这个标识的终态 JobState。重试用尽就让异常冒出，schedule 先 _stop_all 再重抛，前台 run 以非零退出码结束。RunPersistence.finalize 去掉 try_finalize(result.status, message=...)：仍有未结束的 job 时调端口的结束写；判断使 run 成为终态的那次写是不是本进程写的（最后一次终态写，或这次结束写），是本进程写的才从记录组装 RunResult 生成报告；写不成时照旧抛 RunAlreadyEnded。本机后台推进进程的保存失败走同一套重试，但 reconcile.tick 也是云端 Lambda 在用、云端不重试，所以重试要放在本机这一侧：比如 compose.build_local_stores 与 detached.build_local_reconcile 给 ResultStore 套一层重试，或者从 tick 注入重试策略。重试用尽时异常穿过 run_reconcile_loop，后台推进进程退出。
- 文件：core/gherkai_core/persist.py、core/gherkai_core/reconcile.py、runtime/gherkai_runtime/compose.py、runtime/gherkai_runtime/detached.py、cli/gherkai_cli/__main__.py、core/tests/test_persist.py、core/tests/test_reconcile.py、runtime/tests/test_detached_launcher.py、cli/tests/test_main.py
- 先要有：端口的结束写入口（状态取法与结束写块，取代 try_finalize）；update_job_state 的新语义：run 已结束时写不成、终态只写一次、同一次写按取法写 run 状态（状态取法与结束写块）；点名-1（save_job_result 带标识）；点名-2（JobState 带标识）；从记录组装 RunResult 的那一处（报告块）
- 必须同批：点名-1；点名-2；状态取法与结束写块「后台推进改为逐 job 写序」（tick 一侧的保存与点名，同一套写序与重试）；查看命令块 explain 改为按运行态里的标识读
- 单独先落地的后果：只改 on_job_complete（标识、重试、点名）、finalize 先不动时，没有破窗：端口签名改动由点名-1 一起带进来，cli/tests/test_main.py 第 758 到 777 行断言 save_job_result 在每个 update_job_state 之前、try_finalize 在全部保存之后，仍然成立。finalize 改用结束写之后，前提是结束写入口已经在端口上，否则 core/tests/test_persist.py 与 cli/tests/test_main.py 里断言 try_finalize 的用例都会红。退出的那一半，现状本来就是「前台 run 保存失败就带着 running 的 job 退出、没有任何一方能结束它」，后台推进进程退出之后现在还能靠 status --wait 接力。只落这一条不会让产品比现在差，但「之后由 run 处置结束」要等 settle-runs 与 status --wait 处置上线才成立。
- 验证：单测覆盖写序（保存先于终态写、标识一致）、重试次数与间隔（注入 sleep 与标识工厂）、三次都失败之后异常冒出、重试中途成功之后照常点名。0030 实测项 1、2 依赖真实进程与文件系统，单测不算证据，要在本机真实进程上核：真实的 gherkai run 与 gherkai submit --backend local（可以在跳板机上带引擎执行，也可以用 GHERKAI_WORKER_*_CMD 指向一个桩 worker），保存目录在中途短时不可写（注入一次失败）时，重试之后照常点名、进程不退出；一直不可写时，3 次重试之后进程退出、执行中的 job 留在 running，再由 status --wait 或 settle-runs 按「锁拿到了」一行处置。在存下明细之后、写下终态之前 SIGKILL 推进器，随后处置，explain 与报告不出现那份明细。后两项要等生命期锁与 run 处置上线才能核。
- 备注：1）现状不符：on_job_complete 现在不论停手信号都会保存并写终态；0054 决策五要求得知 run 已结束之后不存明细（见 missing）。现在的 on_job_complete 还会给 SKIPPED 的 JobResult 落库，这一点随「前台没有启动的 job 不再构造 skipped 的 JobResult」一条消失。2）update_job_state 的返回值按 0030 决定四是「这次写之前 run 是否仍未结束」，从它看不出这次写是否使 run 成为终态。finalize 要知道「本进程的写使 run 成为终态」，可以这样推出：全部 job 的终态都由本进程写成并返回 True；或者让端口多返回一项。实装时要定，并核对 0030 决定四的签名注释。3）RunPersistence._lock 在退避期间一直持着，最长约 7 秒，会挡住其它 worker 线程的认领与 on_event 写；要考虑是否在锁外做保存与重试，同时保住同一进程里的写按调用次序落库。4）reconcile.tick 是本机与云端共用的。0030 决定三写的是「云端由流的重试或之后的触发再做」，重试不能放进 tick 本体，也不能放进 S3ResultStore。5）前台重试用尽之后现在会冒出原始 traceback。0030 只写「前台终端里另有存储错误」「非零退出码」，退出码要不要定成 1 是「写回时留下、实装之前要定的问题」里的第一条；产品面文案按 ADR 0039，要不要包成一句产品说明，拿不准。6）后台推进进程因异常退出时，drive_local_reconcile 里的 cleanup_tunnel 被跳过；隧道改到宿主进程里之后，这个问题随进程退出自然消失，在那之前要留意。7）位置里写的 reconcile.tick 对应的逐 job 写序，与「状态取法与结束写」块的「后台推进改为逐 job 写序」是同一段 code，两条要合在一起做。

## 本机推进器、生命期锁与边界检查

### 小结

整块改动量为 L，主要在锁-1。本机 submit 要从『提交进程建 run，再 fork 一个推进进程』改成『提交进程只交输入、等回报，由后台推进进程建 run、持锁』，涉及 cli 的 _cmd_submit、_submit_local、_cmd_reconcile 与 `_reconcile` 解析器，runtime 的 detached 装配，新的锁模块与边界检查模块，还要重写一批靠伪造 Popen、从 submit 进程里读 run_meta.json 的 cli 测试。

内部次序：
1. 锁-2，边界检查函数，可以先单独落地，没有调用方。
2. 锁-1 的前台部分：_cmd_run 在 begin 之前查目录、取锁。可以单独一批。
3. 锁-1 的本机 submit 部分：stdin 交输入、回报管道、后台推进进程建 run。它必须与隧道块的『本机 submit』条和 _cmd_submit 就地拆隧道的删除合成一批，因为两条描述的是同一段改动，而且公网地址要在建 run 之前拿到。
4. 『run 处置』块：试拿锁、结束写、status --wait 处置、settle-runs。
5. 锁-3，删接力，与 status --wait 的处置替换放在同一提交。

对别的块的依赖：锁-3 依赖『状态取法与结束写』块的结束写入口和『run 处置』块；锁-1 带 --expose-local 时依赖隧道块，或者过渡期在后台推进进程里沿用 ngrok 可执行文件、退出时自己拆；锁-3 里 _WAIT_WITHOUT_RELAY_NOTICE 在云端分支也用到，牵连『云端只支持 submit』块和云端 status --wait 的次序约束。

最大的风险有三处：
- 依赖真实操作系统行为的地方单测证明不了：目录 flock 在 macOS 与 Linux 上的语义、macOS 用 ctypes 调 fstatfs 的结构布局、Linux mountinfo 的解析、回报管道另一端关闭在两个平台上怎样查到。都要在 macOS 本机和跳板机（含容器）上用真实进程验证。
- 处置不能早于锁上线。锁还没被持有时试拿一定成功，处置会把正在推进的 run 结束掉。
- 隧道过渡期：没有 SDK 又删了接力之后，后台推进进程被 SIGKILL 时，ngrok 可执行文件没有任何一方去拆。

### 线索没有覆盖的改动点

- 前台 run 的创建时刻取得太晚：cli/gherkai_cli/__main__.py 的 _cmd_run 在第 2900 行 _setup_tunnel 之后才调 _build_run_meta，而 created_at 在 _build_run_meta 里面用 compose.now_iso() 取，所以取在起隧道之后；ADR 要求在起隧道之前取一次，期限与边缘到点时刻都由这一次读数算出（ADR 0054 决策二『落点是运行定义』；0035 决策 3『三种组合的宿主与次序』前台 run 一条）。隧道块只为两种 submit 写了这一点，没有写 run。
- list-runs 人读提示列的 FOREGROUND_RUN_NOTE（cli/gherkai_cli/render.py 第 222-224 行定义、第 300-301 行按 item.detached 加入）：它按后台执行标记做判断，又写着『它不会再到终态；status --wait 对它只等待、不接力』。ADR 0041 决策七『人读形态』规定提示列只看记录与期限，ADR 0034 端到端 cloud 1b 规定 detached 只作描述、不参与任何判断。这一条应当删去，并改 render_run_list docstring 里『前台执行遗留的提示』一句，与删接力或 list-runs 的改动同批。
- _definition_contract_message（cli/gherkai_cli/__main__.py 第 2744-2747 行）是用户可见的说明，里面有『本机不能读取或接力推进』，docstring 也讲『status --wait 与 per-run 进程接力』。依据 ADR 0034 被拒方案『本机接力，及其改法』，『接力推进』又将进退役词表，删接力的同一批要改这句。
- LocalRunStore.is_detached 与 _marker_in（core/gherkai_core/adapters/run_store/local.py 第 115-131 行）：删接力、删 pending 提示的 relay_available 回调之后，生产代码里再没有调用方（list_runs 自己读标记）。它的 docstring 写着『status --wait 据此分流』，与 ADR 0034 端到端 cloud 1b 相反。线索只改了 DynamoDBRunStore.is_detached 的去留与 LocalRunStore 的『接力者』一句，没有写这个方法本身删还是留。
- EventLog 端口（core/gherkai_core/reconcile.py 第 68-89 行）上的 has_exit 与 record_timed_out_if_absent，tick 都不调用，只有云端 _handle_timeout 经 DdbEventLog 用到；本机的 SqliteEventLog.has_exit（core/gherkai_core/adapters/event_log/sqlite.py 第 120 行）同样只被接力用到。线索只写了 record_timed_out_if_absent，并说『随端口定去留』，has_exit 漏了（依据 ADR 0034 被拒方案『本机接力，及其改法』与『推进器与触发源』第 1 条）。
- max_concurrency 的回落通道：runtime/gherkai_runtime/detached.py 的 build_local_reconcile 有 max_concurrency 回落形参，cli 的 `_reconcile` 子命令有 --max-concurrency（第 539 行），cli/gherkai_cli/settings.py 第 15 行注释写『status --wait 与 reconcile 的同名 flag 只是提交记录缺值时的回落』，还有测试 test_build_local_reconcile_falls_back_to_flag_when_meta_missing。后台推进进程自己生成运行定义之后，提交记录里一定有 max_concurrency，这些都应当删（依据 ADR 0054 决策三『本机后台由后台推进进程自己建 run』；0034 机制四『max_concurrency 随 definition 到达』）。
- 后台推进进程的输出改向：回报之前接在 submit 的标准错误上，回报之后写进 run 目录里的 reconcile.log。现在 _submit_local 一开始就把 Popen 的 stdout 与 stderr 定向到 reconcile.log。改法是 Popen 继承 stderr、后台推进进程回报之后在 fd 一级 dup2 到 reconcile.log，worker 子进程继承的 stderr 才会跟着改。依据 ADR 0035 决策 3『本机 submit』下的『输出』一条。线索只在行为文档块里写了 running-and-results.md 的说法，code 一侧没有这一条。
- runtime/gherkai_runtime/compose.py 第 367、439、922 行的注释仍把『status --wait 接力者』列为宿主之一（三个宿主、各宿主持有 RUN_ID、事件库路径单点）。『随实装改写的 code 注释』块讲接力的那一条没有列 compose.py（依据 ADR 0034『推进器与触发源』第 1 条）。

### 逐条

#### 锁-1（mixed，L）

- 线索：生命期锁：持有方以只读方式打开 `<report-dir>/<run_id>/`、取排他 flock
- 要做的：在 runtime 包新增生命期锁模块：建 run 的一方先查报告目录，再 mkdir run 目录，用 os.open(O_RDONLY) 打开目录（Python 缺省不可继承）、fcntl.flock(LOCK_EX|LOCK_NB)，只有 EWOULDBLOCK 判为『已被持有』，其余 OSError 判为『锁不可用』；拿到的描述符放在进程级全局里，持有到进程退出。前台：_cmd_run 在 do_report 分支 persistence.begin 之前取锁，被持有或不可用时以退出码 2 结束。本机 submit：_submit_local 改为不建 run、不建事件库、不写 tunnel.json；用 stdin=PIPE 起 `_reconcile` 进程，经标准输入一次写入建 run 所需的输入（补全后的 jobs、steps_dir、max_concurrency、每 job 尾段、expose-local 来源与 provider、解析后的 region/profile、report_dir、cli_version），另传一条回报管道的 fd（pass_fds），然后阻塞读回报，按回报输出结果、以回报里的退出码结束。_cmd_reconcile 与 detached 一侧改成『建 run 的后台推进进程』，依次做：取创建时刻、起隧道、_build_run_meta、建 run 之前查一次回报管道、边界检查、取锁、create_run（detached=True）、建 SqliteEventLog、回报并关闭管道、把 fd 1/2 dup2 到 reconcile.log、run_reconcile_loop；build_local_reconcile 改为接收内存里的 meta，不再从 RunStore 读回。
- 文件：runtime/gherkai_runtime/<新的锁模块，名字由实装定>.py、runtime/gherkai_runtime/detached.py、cli/gherkai_cli/__main__.py、cli/tests/test_main.py、cli/tests/test_tunnel_cli.py、cli/tests/test_project_config.py、cli/tests/test_definition_schema.py、runtime/tests/test_detached_launcher.py、docs/user-guide/running-and-results.md、docs/internals/execution-and-reconciliation.md
- 先要有：边界检查函数（锁-2），建 run 时要先查；给了 --expose-local 时隧道要能在后台推进进程里起：用隧道块的 SDK 实装，或者过渡期在后台推进进程里沿用现有 ngrok 可执行文件，退出时自己拆
- 必须同批：改写依赖『submit 进程内建 run』的 cli 测试：test_main.py 里伪造 Popen 后读 run_meta.json 的那组用例（max_concurrency、steps_dir、deadline、detached 标记）、test_tunnel_cli.py 本机 submit 的隧道用例、test_definition_schema.py 的 _reconcile 入口用例；隧道块里『本机 submit』一条（第 304 行）和 _cmd_submit 末尾 finally 里就地拆隧道的删除（第 315 行）中本机这一半：两处写的是同一段改动；行为文档：running-and-results.md 的 submit 退出码一行与 reconcile.log 一段、execution-and-reconciliation.md 4a 节流程块的首行
- 单独先落地的后果：连同改好的测试一起落地时，产品照常可用：run 与本机后台都持锁，但还没有一方来试拿锁，所以行为上只多出『锁被持有或不可用时退出码 2』。本机接力还在，status --wait 仍会对仍持锁的 run 再开一个推进器，和现在一样，不算新的退化。不改那组测试的话，cli 的 submit 用例全红（submit 进程里已经没有 run_meta.json）。如果给了 --expose-local 而隧道还是现在的 ngrok 可执行文件（agent 在自己的会话里），后台推进进程被 SIGKILL 之后，ngrok 只能靠接力的 cleanup_tunnel 拆；接力一删，就没有任何一方去拆了。
- 验证：单测只能证明接线与载荷的往返（stdin 载荷序列化、回报解析、退出码映射）。下面几项要用本机真实进程在 macOS APFS 和 Linux（跳板机 ext4，加容器 overlay）上各执行一次（ADR 0054 实测项 15、16，0035 实测项 3、4）：经 CLI 提交之后，从 run 目录出现运行态起到后台推进进程退出，别的进程试拿锁都得到 EWOULDBLOCK，submit 退出前后都一样；后台推进进程被 SIGKILL 之后立即拿得到；SIGSTOP 期间仍被持有；worker 子进程还活着时杀掉推进器，锁随即可拿（子进程没有继承锁）；submit 在后台推进进程查回报管道之前、之后各被强杀一次，结果分别是不建 run、照常推进并在 reconcile.log 记一句；建成、起隧道失败、报告目录不过各回报一次，submit 的输出与退出码对得上；回报之前的 stderr 出现在 submit 的终端上，回报之后的输出写进 reconcile.log。worker 可以经 GHERKAI_WORKER_<ENGINE>_CMD 换成测试 fixture 里的 echo worker；带隧道的那一项要真实的 ngrok 隧道。
- 备注：现状：代码里还没有生命期锁，只有 LocalRunStore._run_lock 管 .runstate.lock 的短锁；create_run 自己 mkdir(exist_ok=True)，与先 mkdir 再取锁不冲突。本机 submit 交接的起点：_submit_local 第 1757-1792 行在提交进程里调 build_local_stores(detached=True)、create_run、建 SqliteEventLog、write_tunnel_file，再用 Popen(start_new_session=True, stdin=DEVNULL, stdout/stderr=reconcile.log) 起 `_reconcile run_id --report-dir --max-concurrency --region --profile`，没有回报管道；隧道在 _cmd_submit 第 1696 行由提交进程起，靠 on_handoff/handed_off 交给后台。_cmd_reconcile 调 detached.drive_local_reconcile，再由 build_local_reconcile 从 RunStore 读回 meta。疑点一：这一条与隧道块第 304 行几乎是同一段改动，那一条另写了『建 run 之前查一次回报管道，另一端已关闭就不建 run』，这一条没写，分批时应当合成一项。疑点二：后台推进进程自己生成运行定义之后，『运行定义不可用时以结束写的 error 变体结束』（状态取法块第 222 行、0054 实测项 23）在本机后台怎样出现，我拿不准：只有它仍然从 RunStore 读回 meta 才会遇到，要定下是否保留读回。疑点三：怎样查到回报管道的另一端已经关闭，两个平台的行为不同（Linux 上 poll 写端会给 POLLERR；macOS 可能要写一个探测字节、看是否 EPIPE），所以 0035 实测项 4 要求记下两个平台的结果，不能只看单测。连带改动：run_id 改由后台推进进程生成，submit 只能从回报里拿到；_build_run_meta 依赖 args，要拆成后台进程也能调的形态；『持锁进程只经 exec 起子进程』现在成立：SubprocessEngine 用 Popen，close_fds 取缺省值，pass_fds 只传事件写端，ngrok 也经 Popen 起，全仓没有 multiprocessing 与 os.fork；需要加一条测试守住这一点。建报告目录的检查放在哪一步（早于上传安装包与起隧道，还是到建 run 时才查），ADR 只要求在建 run 目录之前，没写更早，我拿不准。

#### 锁-2（mixed，M）

- 线索：本机后端报告目录的边界检查：对要取锁的那个 run 目录的描述符取文件系统类型
- 要做的：在 runtime 包新增文件系统判断函数，输入一个已打开目录的 fd。macOS 用 ctypes 调 libc 的 fstatfs，取 statfs.f_fstypename，只放行 apfs。Linux 读 /proc/self/fdinfo/<fd> 的 mnt_id，在 /proc/self/mountinfo 里找同一 mount id 那一行，取 ' - ' 之后的类型，只放行 ext4、tmpfs、overlay、xfs、btrfs、ext3。其他平台，或读不到、解析不了，都算判断不了。另给一个查报告目录的入口：路径不存在时取最近一层已存在的上级，打开之后判断。结果带原因、检测到的类型与清单，由调用方以退出码 2 结束，说明用产品语言。在锁-1 的取锁动作里，判断与取锁对同一次打开做；_cmd_run 与后台推进进程在 mkdir run 目录之前先查一次报告目录。
- 文件：runtime/gherkai_runtime/<新的边界检查模块，可与锁模块合一>.py、runtime/tests/<新测试>.py、cli/gherkai_cli/__main__.py、docs/user-guide/running-and-results.md 或 troubleshooting.md（产品边界与清单）
- 先要有：无
- 必须同批：至少一个调用方（锁-1 的 run 或后台推进进程）；用户文档写明产品边界并列出清单（ADR 0054 决策四『用户文档写明并列出清单』），与接上调用方的那一批同一提交
- 单独先落地的后果：只落函数和它的单测时，没有调用方，产品不受影响。接到 run 上之后，报告目录在 NFS、SMB、FUSE、Docker Desktop 宿主目录或其他不在清单里的类型上时，run 以退出码 2 结束，这是新的拒绝面。测试机的临时目录不在清单里时（如某些 CI 的 tmp），所有带记录的 run 与 submit 用例都会红，所以要留一个注入点让测试换掉类型读取。
- 验证：判断逻辑用注入的类型读取做单测。取类型这一步本身要真实执行：macOS arm64 上核 ctypes 取到的 statfs 结构与类型名（apfs，以及 HFS+、FAT 磁盘映像、autofs 各被拒）；跳板机 Linux 上核 mountinfo 解析，覆盖被盖住的挂载、符号链接、绑定挂载、容器内路径、不存在的目录取上级；ADR 0054 实测项 14 的各种挂载（Linux 的 NFS、FUSE，macOS 的 SMB、NFS、HFS+ 磁盘映像，Docker Desktop 绑定挂载的宿主目录）上四个命令都被拒，没有留下目录；已有 run 目录本身是挂载点或符号链接时不取锁。
- 备注：现状：全仓没有 fstatfs、mountinfo、文件系统类型相关的代码，Python 标准库也没有 os.fstatfs，macOS 只能走 ctypes，struct statfs 的布局与符号名（arm64 与 x86_64 的 INODE64 变体）是主要风险。线索列了五个调用方：run 与后台推进进程在这一块；status --wait、settle-runs 在『run 处置』块；doctor 的 report_dir.filesystem 一项在『查看命令与机读输出』块（项名还待 owner 确认，见 journey『写回时留下的问题』）。所以这一块只交付共用的判断函数和建 run 一侧的两个调用点。ADR 写『被拒时不留目录』只针对建 run 目录之前那一次；mkdir 之后对 run 目录 fd 再判一次而被拒时（极少，如 run 目录刚被另一层挂载盖住），要不要删掉空目录，ADR 没写，实装时要定。

#### 锁-3（mixed，M）

- 线索：删去本机接力：`status --wait` 不再进入推进循环
- 要做的：__main__.py：_cmd_status_body 删去 is_detached 分流与 drive_local_reconcile 分支、只为接力解析的 _aws_identity、_validate_max_concurrency 调用，_INTERRUPTED_RELAY_NOTICE 与 _WAIT_WITHOUT_RELAY_NOTICE 两个常量；status 子命令删去 --max-concurrency，--wait 与 --prefix 的 help 去掉『接力』。detached.py：删去 _recover_timed_out_claims、_RECOVERY_MARGIN_S、SubprocessLauncher.owned_scopes，run_reconcile_loop 的 CONTINUE 分支只 sleep；drive_local_reconcile 只剩后台推进进程一个调用方。SqliteEventLog.record_timed_out_if_absent（还有同样只被接力用到的 has_exit）删去，EventLog 端口去掉 tick 用不到的两个方法，或改成只由 DdbEventLog 提供。status --wait 的本机分支换成『run 处置』块的处置循环。
- 文件：cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/detached.py、core/gherkai_core/adapters/event_log/sqlite.py、core/gherkai_core/reconcile.py、cli/gherkai_cli/settings.py、cli/gherkai_cli/render.py、runtime/tests/test_detached_launcher.py、cli/tests/test_main.py、cli/tests/test_definition_schema.py、core/tests/test_sqlite_event_log.py、core/tests/test_reconcile.py、docs/user-guide/running-and-results.md、docs/user-guide/troubleshooting.md、docs/user-guide/local-app-testing.md、CHANGELOG.md
- 先要有：生命期锁已由 run 与本机后台推进进程持有（锁-1），否则处置的『试拿锁拿到了』会把仍在推进的 run 结束掉；结束写入口（『状态取法与结束写』块的端口新入口）；等待中的 status --wait 处置（『run 处置』块第三条）；settle-runs 宜同批或更早
- 必须同批：status --wait 的本机处置循环：与删去的接力分支是 _cmd_status_body 里同一段代码，应当替换而不是先删后补；删除接力相关测试（『测试』块第 294 行：test_relay_* 三条以及 test_relay_writes_only_once_…、test_relay_leaves_its_own_jobs_… 两条；test_definition_schema.py 的 status-wait 参数化；test_main.py 第 3353-3421 行的接力用例与 test_missing_profile_exits_2_on_cloud_submit_and_local_status_relay）；list-runs 人读输出里的 FOREGROUND_RUN_NOTE（render.py，见 missing）：它写的『status --wait 对它只等待、不接力』『不会再到终态』在处置上线之后不再成立；行为文档里讲接力的各处（running-and-results.md、troubleshooting.md、local-app-testing.md）与 CHANGELOG 未发行节的接力条目
- 单独先落地的后果：在处置上线之前单独删接力：推进进程已经不在、又过了期限的本机后台 run 没有任何出口，status --wait 永远等下去，只能 Ctrl-C，list-runs 里一直列为未结束。测试方面，runtime 的接力用例、cli 的 status --wait 接力用例、test_definition_schema.py 的 status-wait 参数会红。只删 SqliteEventLog.record_timed_out_if_absent 时，core/tests/test_reconcile.py 的 test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots（第 514 行）也会红，它要随『测试』块的 K2 改写一起改。
- 验证：删代码这部分，单测加全仓 grep 就够：grep _recover_timed_out_claims、owned_scopes、_RECOVERY_MARGIN_S、RELAY_NOTICE、drive_local_reconcile 的调用方，并确认 status 不再接受 --max-concurrency。『status --wait 不再起 worker、而是处置』这个结论靠真实进程：本机 submit 一个 run，SIGKILL 后台推进进程，status --wait 的下一次轮询按『锁拿到了』一行处置，有报告、退出码 1，进程列表里没有 status 起的 worker，孤儿 worker 释放会话后退出（ADR 0054 实测项 16）；前台 run 被 SIGKILL 的情形也做一次。要真实会话的话在跳板机上带引擎执行。
- 备注：线索里列的符号都在：__main__.py 第 2140、2178、2186、2200 行；detached.py 第 38-43、123-128、242、257-293 行；sqlite.py 第 108 行；status 子命令的 --max-concurrency 在第 478 行。与线索不符或线索没写到的地方：①_WAIT_WITHOUT_RELAY_NOTICE 在 _status_cloud 第 2266 行也用到（前台 run --backend cloud 的提示），删这个常量就得同时改云端分支，所以它要么排在『云端只支持 submit』块之后，要么与云端 status --wait 的改写同批；后者又受 journey 第 203 行的云端次序约束（要在后端到期结束上线之后）。②EventLog 端口的 has_exit 与 record_timed_out_if_absent，tick 都不调用，只有云端 _handle_timeout 经 DdbEventLog 用到；『随端口一起定去留』可以直接定为端口去掉这两个方法、留在 DdbEventLog 上，SqliteEventLog 的 has_exit 也一起删（线索只提到 record_timed_out_if_absent）。③删接力之后 drive_local_reconcile 的『唯一入口』docstring、build_local_reconcile 的 max_concurrency 回落形参、`_reconcile --max-concurrency` 与 settings.py 第 15 行 DEFAULT_MAX_CONCURRENCY 的注释都失去依据（后台推进进程自己生成 meta，max_concurrency 一定有值），test_build_local_reconcile_falls_back_to_flag_when_meta_missing 随之删。④本机 status 删掉接力之后不再需要 AWS 身份，test_missing_profile_exits_2_on_cloud_submit_and_local_status_relay 的本机一半要改。⑤次序：journey 第 204 行（未经 owner 确认）要求删接力与生命期锁、run 处置同批或排在它们之后。读 code 之后我认为这个结论成立，而且还要加一条更硬的约束：处置不能早于锁。锁还没被持有时，任何一方试拿都拿得到，处置会把正在推进的 run 记成『进程已退出』。所以次序是锁-1（含后台推进进程自己建 run）→ 结束写 → status --wait 处置替换接力（同一提交）→ 其余清理。只有『过了期限加 300 秒』这一条处置条件不依赖锁，但单靠它，本机接力现在还能收拾的『推进器已不在、还没到期』那类 run 要多等到期限加 300 秒。

## run 处置：settle-runs 与 status --wait

### 小结

这一块合计 L：一个新的 runtime 处置模块（M），一个新命令 settle-runs（L，跨 CLI、设置、渲染、契约页与用户文档），重写 status --wait 的两条等待循环（M）。code 里还没有任何处置相关的代码，现有的 try_finalize 只写 run 级，不能代替结束写。

内部次序：处置-1 先落（core 的 300 秒常量与判断随它或更早），处置-2、处置-3 都调用它。处置-3 的本机一半必须与锁一块的「删去本机接力」同批（改的是同一段代码，且先删接力就有窗口）；云端一半（status --wait 处置并删 kickoff 与 _make_lambda_client）要与云端后端一块的定时触发、写入序号同批，在重新部署之后验证。settle-runs 的云端路径也宜放进那一批，因为新 CLI 版本高于后端时 skew 闸会拦下。

对别的块的依赖：结束写入口（状态取法与结束写），生命期锁、试拿锁与边界检查（本机推进器与生命期锁），从记录组装报告（报告；它又依赖判定明细点名），写入序号与 kicker 定时触发（云端后端）。这一块在依赖链的末端。

最大风险：生命期锁上线之前就接上「试拿锁拿到即处置」，会把正在执行的 run 结束（试拿锁永远成功）。这一点单测发现不了，靠真实进程才能暴露。其次是云端删 kickoff 早于后端到期结束，以及 dev 版本跳过 skew 闸时对没有写入序号的旧 STATE 做条件写。

### 线索没有覆盖的改动点

- 存储访问失败不算「运行态读不出」：权限、凭证、region、网络失败时 status --wait 与 settle-runs 以退出码 2 结束、不进入等待、不记 unreadable；status --wait 处置的结束写失败同样为 2；条件写被别处抢先不算失败。位置：处置模块与 cli/gherkai_cli/__main__.py 的 _cmd_status_body、_status_cloud 和 settle-runs 命令函数。依据：journey 0018 末节「存储访问失败不算『运行态读不出』」一条（指明实装条目进本块）；ADR 0054 决策六末条、决策八与 0031 决定五都还没写，要先写进 ADR。
- settle-runs --json 顶层带 cli_version（同 list-runs，恒有，取不到为 null）；被 Ctrl-C 中断时打一句说明、以退出码 130 结束，已写成的处置保留。位置：cli/gherkai_cli/__main__.py 的 settle-runs 命令函数、render.py、机读契约页。依据：journey 0018 末节「settle-runs --json 的 cli_version 与被使用方中断时的退出码」一条（首选落点就是本块 settle-runs 条）；ADR 0054 决策八、0031 决定五尚未写。
- status --wait 读到合法期限后不再重读运行定义，没读到时下一轮再读；等待中的说明（锁不可用、运行态读不出）首次打一次，原因变了再打。位置：cli/gherkai_cli/__main__.py 的等待循环。依据：journey 0018 末节「status --wait 的期限只读一次，等待中的说明只打一次」一条（指明补进本块第三条）。
- 本机运行态解析不了时，status --wait 只等待并说明原因：现在 LocalRunStore.load_run_state 遇到损坏的 JSON 抛 ValueError，_cmd_status_body 只接 DefinitionContractError，会把回溯打到终端。位置：cli/gherkai_cli/__main__.py 的 _cmd_status_body 与等待循环。依据：ADR 0054 决策八「等待中的 status --wait」条「运行态本身读不出时只等待并说明原因」；journey 末节「提交记录或运行态本身解析不了时的出口」，其中「status 不带 --wait 时退出码 2 还是照常显示」仍待 owner 定。
- 结构版本不认或读不出的 run 按锁处置（settle-runs 每个 run 不过定义结构版本闸，期限读不出时只剩试拿锁一条），以及这种情形下有没有报告。位置：处置模块与 settle-runs。依据：journey 末节「结构版本不认的 run 仍可按锁处置」一条，建议写进 ADR 0054 被拒方案与决策六，尚待 owner 确认。
- 「期限加 300 秒」的常量与「严格晚于」判断在 code 里还没有，宜先在 core/gherkai_core/run_deadline.py 定一处：处置、status 与 list-runs 的期限提示、kicker 的第二次定时触发、隧道边缘到点拒绝与隧道守护进程退出都用它。依据：ADR 0054 决策六、九第 1 条；0041 决策七；0035 决策 3「边缘到点拒绝」。
- settle-runs 的用户与技术文档线索里没有列（只登记了机读契约页）：running-and-results.md 的命令表与退出码表加 settle-runs 一行；configuration.md 跨命令选项表加 settle-runs 的定位参数与 --dry-run；troubleshooting.md 写「run 一直不结束」时用 settle-runs；CHANGELOG [Unreleased] 加新命令一条；runtime/DEVELOPMENT.md 的模块清单加处置模块；cli/DEVELOPMENT.md 的命令清单加 settle-runs。依据：CLAUDE.md「改完 code 回头校准文档」；ADR 0054 决策八；0053 决策 1。
- cloud status --wait 要从现在不带卸载器的 DynamoDBRunStore 改为 build_cloud_stores 装配（带 S3 结果与报告两个 store、报告前缀取 --report-dir），否则处置写成之后读不了被点名的明细、写不了报告。位置：cli/gherkai_cli/__main__.py 的 _status_cloud。依据：ADR 0054 决策七（写成的一方生成报告）、决策八「云端用户一侧的处置方」条。
- agent skill 与 ADR 0043 决策五：任务域 A 的命令列表加 settle-runs，骨架第 8 条「退出码分流」补 settle-runs 的退出码，并写明 agent 可以先用 --dry-run 看、再自己执行（owner 2026-11-15 同意）；skill 正文留给打磨批。位置：docs/adr/0043-agent-skill-for-driving-gherkai.md、cli/gherkai_cli/skills/gherkai/。依据：journey 末节「agent 可以自己执行 settle-runs」一条。

### 逐条

#### 处置-1（mixed，M）

- 线索：处置的判定与动作放在 runtime 包，`status --wait` 与 `settle-runs` 共用
- 要做的：在 runtime 包新增一个处置模块（如 runtime/gherkai_runtime/settle.py）。判定函数输入是运行态、期限（可缺）、试拿锁的结果（只本机有）和墙钟，按 0054 决策八的次序给出 reason（unreadable / already_finished / unsupported_filesystem / advancer_exited / past_deadline / lock_held / undetermined / within_deadline）。动作函数拿到锁之后读运行态，已结束不动，否则调端口的结束写入口（来路是「处置：锁拿到了」或「处置：已过期限加 300 秒」，两者同时成立取前者，各句末尾加「（已记为已结束）」）；写成后经报告一块那处共用的组装，从记录生成报告；锁持有到处置做完，dry-run 时拿到即放开。core/gherkai_core/run_deadline.py 加「期限加 300 秒」的常量和「严格晚于」判断，与 past_deadline 写在一起。
- 文件：runtime/gherkai_runtime/settle.py（新增）、core/gherkai_core/run_deadline.py、core/gherkai_core/project.py 或结束写说明表所在的 core 模块（加处置两行的说明与「（已记为已结束）」后缀）、runtime/tests/test_settle.py（新增）、runtime/DEVELOPMENT.md
- 先要有：结束写入口（ports.py 新方法与 local.py、ddb.py 两个实现，按来路带说明；云端以写入序号为条件）；生命期锁：run 与后台推进进程从建 run 起持锁（否则试拿锁永远拿得到，会把正在执行的 run 记为已结束）；试拿锁与边界检查的 runtime 原语（锁一块的新模块：同一次打开先查类型、再非阻塞 flock，只有 EWOULDBLOCK 算持有）；从记录组装 RunResult 并生成报告的共用函数（报告一块），它又依赖按点名标识读明细（判定明细点名一块）；结束写说明表的常量（状态取法与结束写一块）
- 必须同批：至少一个调用方（处置-2 或处置-3），否则只是没人用的代码
- 单独先落地的后果：没有调用方时对产品没有影响，测试照常全绿；但如果连同调用方落在生命期锁之前，试拿锁永远拿得到，等待中的 status --wait 或 settle-runs 会把正在推进的 run 记为 aborted 或 skipped 并结束它。
- 验证：判定表（8 种 reason 的次序、两个条件同时成立取锁、期限读不出只剩锁、云端只看期限、严格晚于 300 秒的边界）用假锁和假墙钟做单测就够。锁的真实语义单测不能作证：SIGKILL 后拿得到、SIGSTOP 时仍被持有、fork 不 exec 的子进程会延长持有，要在本机 macOS APFS 和跳板机 Linux ext4 上起真实进程核（0054 实测项 16、19）。云端结束写的竞争（两个处置方、处置与推进器同时写）要在重新部署之后用真实 DynamoDB 核（实测项 18、19）。
- 备注：code 现状：这一块的东西一样都还没有。try_finalize 只写 run 级、不改 job，正是 0031 决定三被拒方案①，不能拿它凑合，必须等结束写入口。run_deadline.py 里只有 RUN_DEADLINE_PASSED_MESSAGE，注释还是旧语义（「run 级记为 error」），code 里没有 300 秒这个常量；它另有几个使用方（status / list-runs 的期限提示、kicker 的第二次定时触发、隧道边缘到点拒绝、隧道守护进程退出），宜先在 core 定一处。拿不准的设计点：(1) 期限从哪里读：云端 META 有顶层 deadline_at 副本，扩充 peek_definition_header 就能免去 S3 读；load_run_meta 可能要取 S3 卸载正文。但生成报告本来就要完整的运行定义，所以报告一定要读 load_run_meta。(2) 运行定义读不出（含结构版本不认）而按锁处置写成时，没有 job 定义可组装，报告生成不了；ADR 没写这种情形下有没有报告。(3) 本机 load_run_state 在 JSON 损坏时抛 ValueError，读不了目录时抛 OSError；处置要把前者归 unreadable，后者归后端访问失败（见 missing）。(4) 结束写的参数用来路枚举还是三句说明，由实装在 ports.py 定，处置一侧的调用形态跟着变。

#### 处置-2（mixed，L）

- 线索：新命令 `gherkai settle-runs [run_id] [--dry-run] [--json]`
- 要做的：在 _build_parser 加 settle-runs 子命令（三项定位参数、--config、--dry-run、--json、--prefix/--ddb-table/--region/--profile），main() 分派到新的 _cmd_settle_runs。本机：先对报告目录做边界检查（目录不存在则照常结束），不给 run_id 时用 run_store.list_runs([PENDING, RUNNING], limit=None) 取未结束和读不出的 run，逐个调处置-1。云端：先过 _cloud_skew_gate；不给 run_id 时经 build_cloud_run_list_store 列举，用 build_cloud_stores（带卸载器与 S3 两个 store）做结束写和写报告。人读输出逐条给出 run、reason、outcome；--json 给落点字段（同 list-runs）、dry_run 和 runs[]。退出码 0 或 2，写入失败即停止。settings.CONFIG_COMMANDS 加 settle-runs，PER_CALL_OPTIONS 加 dry_run。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/settings.py、cli/gherkai_cli/render.py（人读表格与 settle 的 JSON 文档）、cli/tests/test_settle_runs.py（新增）、cli/tests/test_project_config.py、cli/tests/test_cli_json_contract.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、docs/user-guide/running-and-results.md、docs/user-guide/configuration.md、CHANGELOG.md
- 先要有：处置-1（处置模块）；生命期锁与边界检查（锁一块）；结束写入口与从记录生成报告（状态取法、报告两块）；云端部分另依赖写入序号（云端后端一块的 ddb.py）与重新部署：新 CLI 版本高于后端时 skew 闸会拦下（SKEW_BLOCK）
- 必须同批：0053 键集差集护栏的改动（test_project_config 的排除名单加 --dry-run；不加则 test_every_long_option_is_classified... 立即变红）；机读契约页与 skill 副本写出 settle-runs 的 --json（契约测试守着已登记命令的键）；用户文档的命令表、选项表与 CHANGELOG（每批提交带上它所改行为的文档）
- 单独先落地的后果：在生命期锁之后、删本机接力之前单独落下时，产品多了一个可用的出口，与现有接力并存，不出窗口。在锁之前落下：本机 run 不持锁，settle-runs 对每个未结束的本机 run 都判 advancer_exited，会结束正在执行的 run（产品层面的错误，测试不一定能发现）。云端一半在重新部署之前，正式版本会被 skew 闸拦下；dev 版本会跳过 skew 闸，对没有写入序号的旧 STATE 做条件写，结果没有保证。
- 验证：CLI 单测：用 tmp 报告目录与另起的真实子进程持 flock，覆盖各 reason、--dry-run 放锁、退出码、--json 键集、配置文件层。单测不够的部分：本机真实执行，推进器分别为不在、仍在、被另一处置方持锁、被 SIGSTOP 过期限加 300 秒，以及 run 目录在类型清单之外、运行态损坏、已结束这几种情形（0054 实测项 19、20），在 macOS APFS 和跳板机 Linux 上各做一遍，跳板机上带引擎执行真实的 run；两个 settle-runs 并发只有一个写成（实测项 19）。云端在重新部署之后：期限加 300 秒前后各一次，只给 runs 表读权限时写入失败以退出码 2 结束，不给 run_id 时经索引列举。
- 备注：code 现状：没有这个命令，也没有任何文档提到它（只有 ADR 与 journey 里有）。连带改动：settings.py 与 __main__.py 的 _add_config_flag 里「八个读配置命令」的字样要改成九个（settings.py 第 1、19、23、68、125、209 行，__main__.py 第 93 行）；_cloud_skew_gate 与 compose.check_backend_skew docstring 里列的「五个 cloud 入口（run / submit / status / explain / list-runs）」要改（run 去掉，settle-runs 加上）。--report-dir 在云端是报告前缀，settle-runs 写报告用它；是否和后端的 REPORT_DIR 比对还待 owner 定（journey「核对时补上的条目」）。本机已有的 run 目录本身是挂载点或符号链接时，按实测项 14 不取锁、不写，属于 unsupported_filesystem。人读输出用不用 rich 表格（0047）线索没有写，由实装定。--json 顶层带不带 cli_version、Ctrl-C 以 130 结束，这两条线索里没有（见 missing）。

#### 处置-3（mixed，M）

- 线索：等待中的 `status --wait`，两个后端、前台与后台的 run 都一样
- 要做的：重写 _cmd_status_body 的本机等待：去掉 is_detached 分流和 drive_local_reconcile 调用，改成一个轮询循环。每轮读运行态，到终态即退出循环；未到终态时边界检查加试拿锁，再比期限，条件成立即调处置-1，然后照常 _render_status。锁被持有时不说明；锁不可用、运行态读不出时说明原因并继续等。_status_cloud 的等待循环改为每轮比期限，到点即处置；删去 _STALL_KICK、lam.invoke 及 ResourceNotFoundException 分支、kicker_fn。删去 compose._make_lambda_client。云端 run_store 改由 build_cloud_stores 装配，带卸载器和 S3 的结果、报告两个 store，供处置时写报告。
- 文件：cli/gherkai_cli/__main__.py（_cmd_status、_cmd_status_body、_status_cloud、_wait_local_terminal、_INTERRUPTED_* 常量、status 子命令 help）、runtime/gherkai_runtime/compose.py（删 _make_lambda_client）、cli/tests/test_main.py、cli/tests/test_backend_cloud.py、cli/tests/test_definition_schema.py、docs/user-guide/running-and-results.md、docs/internals/execution-and-reconciliation.md
- 先要有：处置-1；生命期锁与边界检查（锁一块）；本机一半：可与删本机接力（锁一块第 3 条）同批；云端一半：删 kickoff 必须与后端到期结束（kicker 收到 STATE 新建时建两次定时触发，云端后端一块）同批或在它之后，即重新部署之后
- 必须同批：本机一半：删本机接力（_cmd_status_body 调 drive_local_reconcile 的分支、_INTERRUPTED_RELAY_NOTICE、_WAIT_WITHOUT_RELAY_NOTICE、status 的 --max-concurrency、_recover_timed_out_claims）。两者改的是同一段代码，而且先删接力会让推进进程不在、又已过期的本机 run 没有出口；云端一半：kicker 的定时触发与清扫、runs 表写入序号，与这些一起重新部署；测试删改：test_backend_cloud.py 里 kickoff 相关的用例（test_status_wait_cloud_kicker_missing_fails_fast、..._only_waits_for_a_run_that_is_not_detached、..._exits_2_when_the_detached_marker_cannot_be_read），test_main.py 里 test_status_wait_on_a_foreground_run_only_waits_and_never_relays、test_status_wait_does_not_reconcile_a_terminal_run、test_missing_profile_exits_2_on_cloud_submit_and_local_status_relay 的本机 relay 一半，test_definition_schema.py 里 test_local_relay_reports_contract_violation_with_exit_2_instead_of_traceback
- 单独先落地的后果：本机一半如果早于生命期锁落下，试拿锁永远拿得到：在另一个终端对正在前台执行的 run 敲 status --wait，第一次轮询就会把它结束（现在的做法是只等待）。云端一半如果早于后端到期结束落下，推进链断开的云端 run 失去唯一的唤醒手段（journey 写明的次序约束），只能等期限加 300 秒后被 status --wait 记为 aborted。上面列的测试会因断言旧行为而变红。
- 验证：单测覆盖循环的分支：假锁的三种结果、期限缺失、运行态读不出时只等待、说明只打一次、Ctrl-C 以 130 结束。单测不够的部分：本机真实执行（实测项 16），两种推进器（前台 run 与后台推进进程）各 SIGKILL 一次，status --wait 下一次轮询即按「锁拿到了」处置、有报告、退出码 1，孤儿 worker 释放会话后退出；SIGSTOP 时到期限加 300 秒之后才处置，SIGCONT 之后推进器停手、不再存明细；在跳板机上带引擎执行真实的 run。云端在重新部署之后：断开推进链的 run 过期限加 300 秒后被 status --wait 处置并写出 S3 报告，核对 kicker 不再收到直接调用（看 Lambda 调用量与日志）。
- 备注：code 现状：本机按 is_detached 分流，后台 run 走 drive_local_reconcile，前台 run 走 _wait_local_terminal 只等待；云端连续 3 轮快照没变就调用一次 kicker。云端现在用的是不带卸载器的 DynamoDBRunStore，没有结果与报告两个 store，处置写不了报告，所以要改装配，这一点线索没有写。kicker 的 _run_ids_from_runs_stream 对 {"run_id": ...} 这种 payload 的分支不能删：job 超时的定时触发也用同一形状，只改它 docstring 里「status --wait 接力兜底」的说法（注释块已登记）。CloudTarget.kicker_lambda 仍供 submit 的 lambda:GetFunction 预检，保留。_INTERRUPTED_WAIT_NOTICE 的「这个 run 仍在原处继续执行」在推进器已不在时不成立，宜随之改写。现在的 _definition_header_gate 在等待之前遇到结构版本不认即以退出码 2 结束，走不到处置；journey 建议的「结构版本不认也按锁处置」只作用于 settle-runs，status --wait 维持退出码 2，有待 owner 确认。run 目录不过边界检查时，未结束的 run 以退出码 2 结束，已结束的不查（owner 不取「只读地等」），这一条写在锁一块与 journey 末节，与这里同一段代码。建议拆成两个提交：本机一半（含删接力）在本机批，云端一半（处置加上删 kickoff）在云端重新部署批。

## 云端后端（runs 表、kicker 与 reconciler、定时触发、清扫、权限）

### 小结

我只读不改，对照 ADR 与 code 摸完了这一块的 6 条线索。

**改动量与先后**
- 整块是 L。云端-1（DDB adapter 的写入序号与整体替换）是 L，是这一块的地基；它其实是状态取法块里端口新语义（结束写入口、update_job_state、取法函数）的 DDB 一半，必须和那一块、点名标识、reconcile.tick 的逐 job 写序同一批落地。
- 云端-2、3、4、5（kicker 两条过滤、handler 不分流、两次 run 级定时触发、清扫）是 M 到 L，几乎全在 reconciler.py、exit_observer.py 与 stack.py。
- 云端-6 只改文档，和「行为文档」块重复，要按各自的行为批拆开落。
- 内部次序：
  - 云端-1 在先，云端-4 的后端到期结束要用它的结束写。
  - 云端-2、3 必须一起落，而且要在「云端只支持 submit」块删掉 `run --backend cloud` 之后（或同批）。
  - 云端-5 依赖云端-2 的过滤②。
  - 云端-4 还依赖处置块（runtime 的处置函数）和报告块（从记录生成）。
  - 删 CLI 的 kickoff（`_STALL_KICK`）要与云端-4 同批或排在其后。

**必须重新部署才生效的**
- Lambda 代码：reconciler.py、exit_observer.py，以及打进 asset 的 gherkai_core（ddb.py、reconcile、project）与 gherkai_runtime（处置）。
- kicker 的流过滤。
- IAM：退出观察者撤掉 runs 表读、去掉 RUNS_TABLE；推进 Lambda 的 Scheduler 资源域要加 run 触发的名字空间（沿用 job-timeout 名字空间就不用改）。
- Scheduler：没有 CDK 资源，run 触发由 kicker 运行期建，只动 IAM 资源域。
- runs 表条目形状：STATE 多了写入序号，jobs 各项带点名标识，记下终态时整体替换 jobs。表的键、GSI 与属性定义都不变。

建议把这几项合进一次部署，并且和「云端只支持 submit」块删 SSM subnets 与 security-groups 的那次部署合并。

**「两边必须同时是新的」的耦合**
1. 写入序号：CLI（submit 的 create_run 写初值；status --wait 与 settle-runs 的结束写以序号为条件）和 Lambda（每次写加一）。新 CLI 配旧 Lambda 时，旧 Lambda 的写不加序号，新 CLI 的整体替换挡不住、可能盖掉 Lambda 刚写的 job 终态。所以云端处置要等 Lambda 重新部署之后才能用。
2. 去掉 detached 分流：新后端配还能 `run --backend cloud` 的 CLI，会双开推进器（重复起 task、两方收尾），观察者也会给前台 run 写退出记录。所以 CLI 一侧删前台云端 run 要先于（或同于）这次部署。反方向没问题：新 CLI 的 submit 仍写 detached，旧后端照常触发。
3. kickoff：新 CLI 删了 kickoff 而后端还没有到期结束时，推进链断开的云端 run 只能等用户一侧在期限加 300 秒之后处置。
4. 点名明细（另一块）：旧 Lambda 不点名，新 CLI 的处置、报告与 explain 找不到明细。

版本 skew 闸在发行版之间能挡住版本不一致，但开发期各提交的版本号相同，挡不住「代码新、部署旧」。每个改了云端的批之后，要等 owner 重新部署，再做云端验证。

**最大的风险**
- 一是端口形态：到期结束写要以调用方这一轮读到的序号为条件，所以序号要经 RunState 交给调用方；这影响状态取法块的端口设计，要先定。
- 二是 kicker 的失败面变大：建不成 run 级定时触发时让调用失败、整批重试，加上 2 分钟 Lambda 超时里要等待并停多个 task。
- 三是真实行为只能在部署后验证：过滤命中、Scheduler 精度与过去时刻、ECS 列举的最终一致性、真 DynamoDB 并发。0054 实测项 3、8、21 与 0034 机制三②实测项都要部署后真跑。

### 线索没有覆盖的改动点

- kicker 要按流记录的 eventName 区分 STATE 新建（建两次定时触发再 tick）与终态写（只清扫）。现在 `_run_ids_from_runs_stream`（deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py）只返回 run_id 集合，直接 invoke 的 timeout payload 也合在里面；这个函数不在任何一条线索的位置里。依据：ADR 0054 决策九第 1、2 条。
- 图 docs/diagrams/execution-detached-gates.json 整张画的是「是否后台执行」的两道分流（事件源层过滤、函数内判断），要删掉或改画成新的两条过滤与清扫，用 tools/build_diagrams.mjs 重出。docs/internals/cloud-backend-carriers.md 第 114 行「分流依据是 STATE 上的 detached 标记」与第 96 行讲前台 run --backend cloud 的图注也要改。docs/internals/execution-and-reconciliation.md 第 76、78、80、81 行讲 kicker 的 kickoff 入口，以及 docs/diagrams/execution-cloud-cascade 的图注，同样要改。journey「行为文档」块只列了 run-execution.json 与 execution-timeout-chain.json 两张图，cloud-backend-carriers.md 只列了 SSM 一行。依据：ADR 0034 端到端 cloud 1b「触发过滤不看后台执行标记」；ADR 0054 决策九；ADR 0045 决策七。
- 用户文档没有讲后端到期结束与清扫：docs/user-guide/cloud-backend.md 没有一处讲「过了允许运行的时间加 300 秒，后端把未结束的 run 记为已结束」与「run 结束之后后端停掉仍在执行的任务」，费用说明也没有「每个 run 另建两个一次性定时触发」。CHANGELOG `[Unreleased]` 也没有对应条目，journey 的 CHANGELOG 条只提 SSM 参数删除与重构。依据：ADR 0054 决策九（含末段代价）；ADR 0033 资源清单 15。
- 「随实装改写的 code 注释」块漏了几处。deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py：模块头第 6 行「叠加 status --wait 接力」；`_handle_timeout` docstring 的「保护交给防御扫与 status --wait」（应为防御扫与 run 的两次定时触发）与「对位 local 接力恢复」；kicker_handler docstring 的 kickoff 与「四宿主一份 tick（… status 接力）」；`_build` docstring 的「与同步 cloud run 路径一致」。deploy_aws/gherkai_deploy_aws/stack.py：`_storage` 第 183 行「kicker 只被 INSERT 触发」；第 782、785 行注释里的「超时处置」。core/gherkai_core/adapters/run_store/ddb.py：DynamoDBRunStore.__init__ 讲 detached 参数「kicker 的 Stream filter 只认它」。依据：ADR 0034「推进器与触发源」与端到端 cloud 1b；ADR 0054 决策九；CONTEXT「job 到点停止」词条。
- core/tests/test_cloud_integration.py::test_ddb_job_write_on_finalized_run_lands_job_only_real（真 DynamoDB 用例）断言「run 已结束时 job 照写」，是旧设计。journey「测试」块只列了 test_conditional_writes.py 里的同类用例，没有这一条。依据：ADR 0054 决策五；ADR 0034 机制三②。
- core/tests/test_status_group.py 的不变量测试要覆盖新写法：记下最后一个 job 终态的整体替换写，和结束写，在写 run 级 status 的同一次写里写 status_group。ADR 要求这条不变量「由覆盖全部写路径的不变量测试守」；journey「测试」块里关于这个文件的那一条只讲文档串的出处。依据：ADR 0030 决定六「runs 表只有一个 GSI」条的写入规则。
- deploy_aws/tests/test_lambda_handlers.py 要为两次 run 级定时触发（建名、幂等、建不成时调用失败、payload 分流、到点复查与等待）和清扫（各入口在已结束跳过之前清扫、批内去重、ENDED 时清扫）新增用例。现有「启动器 _run_ids_from_runs_stream」一节的 test_starter_run_ids_from_direct_kick 文档串讲 status --wait kickoff，也要随之改。journey「测试」块只列了 handler 分流一节与 K2 用例。依据：ADR 0054 决策九第 1、2 条与「落实时清扫的位置」段。

### 逐条

#### 云端-1（mixed，L）

- 线索：STATE 条目带写入序号，每次写加一；记下 job 终态的写与结束写以「序号等于读到的值」为条件
- 要做的：DynamoDBRunStore 的 STATE 加一个数值属性，名字由实装定，下称 write_seq。create_run 的 `_state_item` 把它写成 0；try_claim_job、project_state 的标量一步与每次逐 job 写、update_job_state 的非终态写，都在 UpdateExpression 里给它加一。记下 job 终态的写与结束写改成：强一致读 STATE，在内存里按取法算出整份 jobs Map（带点名标识）、run status、status_group，成为终态时连同 ended_at 与 message，再写 `SET jobs = :jobs, write_seq = :n+1 …`，条件是 `write_seq = :n AND #st IN (pending, running)`；条件不成立就重读再算。删去 try_finalize 的 expected_claim_count 分支，删去 update_job_state 在 run 已结束时只写 job 的第二次写。认领计数（#cc）只作诊断键保留。
- 文件：core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/ports.py、core/gherkai_core/model.py、core/gherkai_core/adapters/run_store/local.py、core/tests/test_conditional_writes.py、core/tests/test_ddb_run_store.py、core/tests/test_cloud_integration.py、core/tests/test_status_group.py、core/tests/test_cloud_reconcile.py
- 先要有：端口上的结束写入口与 update_job_state 新语义（状态取法块，方法名与参数在 ports.py 定）；run 状态取法函数（取代 run_verdict 与 projected_run_status）；JobState 带点名标识（判定明细点名块）：整体替换的 jobs Map 要带上它
- 必须同批：local adapter 的同名端口改动：两端对拍在 test_conditional_writes.py 的同一组参数化里；reconcile.tick 改成逐 job 终态写，到期的结束写以这一轮读到的序号为条件（0034 实测项 7 的 DDB 用例 test_expiry_loses_to_a_claim_that_landed_after_the_read_on_ddb）；「状态投影只推进运行态」：同一组 update_item 上要把 project_state 写 job 终态的分支删掉，run 级 running 从标量一步挪到逐 job 写；Lambda 重新部署：ddb.py 随 Lambda asset 打包，重新部署后才生效
- 单独先落地的后果：只改 DDB 一侧时，test_conditional_writes 的 local 与 moto 对拍立即不一致，测试变红。只加「每次写加一」、不改条件时测试不红，但 ADR 要的保证没有兑现：回退写和 expected_claim_count 都还在。部署层面：CLI 立刻用上新 adapter，已部署的 Lambda 在重新部署之前仍是旧 adapter，写的时候不加序号。新 CLI 做云端处置的结束写时，以序号为条件挡不住旧 Lambda 在它读之后落下的终态写，整体替换会把那次终态盖掉。
- 验证：moto 与本机对拍的单测只能证明表达式与条件写在 moto 里成立，不够。按 0034 机制三②的实测项，要在真 DynamoDB 上重做，用例加进 core/tests/test_cloud_integration.py（real_aws）：两个进程拿同一序号并发写，恰好一方写成，另一方重读重算后写成，恰好一方使 run 成为终态；几百个 job 的结束写与终态写都能写成（按实际 job 项大小，含点名标识）。重新部署之后，经 Lambda 再核一次只有一方生成报告。整体替换的写单位可以用 tools/ddb_capacity.py 核。
- 备注：现状：code 里没有任何写入序号（grep 无命中）。线索说的「各写入口」现在是 create_run/_state_item、update_job_state（两次写，第二次在已结束的 run 上照写 job）、try_claim_job（带 #cc）、project_state（标量一步加逐 job 写；new_rank>=2 的分支仍会写 job 终态，run 级 running 写在标量一步）、try_finalize（expected_claim_count）。
  
  疑点：「写不成即重读再算」放在 adapter 里还是调用方。0054 决策二后台推进条「收尾与报告」要求到期的结束写以「这一轮读到的」序号为条件：读之后有了新认领，就不再算到期。所以序号必须经 load_run_state 交给调用方（RunState 加字段，或一个不透明的令牌）。处置的结束写则可以在 adapter 里循环。这是端口形态的决定，要和状态取法块一起定。
  
  连带改动：RunState.claim_count 的注释（「到期收尾写以库中计数等于读到的值为条件」）；ddb.py 模块头说 message 随 try_finalize 写入的那一句。整体替换之前多一次强一致读，是新增的读量（运行成本），可以记下。cli-json-contract 里 status --json 的 claim_count 已经存在，不用改。

#### 云端-2（mixed，S）

- 线索：kicker 的流过滤改为两条：INSERT 且 item_type 为 STATE
- 要做的：stack.py `_reconcile_lambdas` 里 kicker 的 DynamoEventSource 换成两条 FilterCriteria：① eventName=INSERT，且 NewImage.item_type.S=STATE；② NewImage.item_type.S=STATE，且 NewImage.status_group.S 为 anything-but live。删去 NewImage.detached.BOOL 的条件，改写 733-737 行注释、模块 docstring 第 15-16 行和 `_storage` 第 183 行「kicker 只被 INSERT 触发」的说法。kicker 一侧要能分清一条流记录是新建还是终态写：`_run_ids_from_runs_stream` 现在只给出 run_id 集合，要改成带上 eventName。
- 文件：deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/tests/test_stack.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/tests/test_lambda_handlers.py
- 先要有：前台云端 run 已删去（「云端只支持 submit」块）；使 run 成为终态的那次写同时把 status_group 写成终态值（现在的 try_finalize 已经如此；新的终态写由云端-1 保证）
- 必须同批：handler 不按后台执行标记分流（云端-3），两处判据同时去掉；清扫（云端-5）与两次定时触发（云端-4）：没有它们，过滤②唤醒的 kicker 无事可做，过滤①也只做冷启动
- 单独先落地的后果：只删 detached 而 run --backend cloud 还在：重新部署后，前台云端 run 的 STATE 新建也会触发 kicker，云端推进器和前台进程同时推进同一个 run，重复起 task。少了 item_type=STATE 时，META 的新建也会触发，kicker 可能在 STATE 落库之前就推进。只加过滤②、没有清扫代码：kicker 被终态写唤醒，`_build` 读到终态就 no-op，只是多一次调用。test_kicker_mapping_insert_filter 只数含 INSERT 的 mapping，照样能过，要改成锁定两条过滤的确切形态。
- 验证：合成测试锁定两条 Pattern 的 JSON。过滤是否真按预期命中，单测给不了证据，要在重新部署后真跑：0054 实测项 21「流上只有 STATE 的新建与使 run 成为终态的写触发 kicker」。对照 kicker 的调用次数与日志：认领、投影、job 运行中写都不应触发。
- 备注：现状 filter 是 `eventName=INSERT` 且 `NewImage.detached.BOOL=true`（stack.py 743-746 行）。
  
  拿不准：Lambda 事件过滤的 anything-but 对缺 status_group 的旧 STATE 不命中。没有实测，不做兼容也无妨。
  
  过滤②会命中终态之后仍落下的写。现在 update_job_state 在已结束的 run 上还会写 job；状态取法块删掉这一写之前，每一次迟到的写都会唤醒 kicker 清扫一次，无害但多出调用，宜在同一次部署里一起上。runs 表没有 TTL，REMOVE 不带 NewImage，不会误中。

#### 云端-3（mixed，M）

- 线索：handler 不按后台执行标记分流：删去 reconciler `_build` 里的 `is_detached` 判断
- 要做的：reconciler.py：删掉 `_build` 里 `run_store.is_detached(run_id)` 那一支和它的注释。exit_observer.py：删掉 `_is_detached` 与 handler 里的跳过分支，改写模块头的「只为 detached run 写」和 env 说明。stack.py：退出观察者不再 `grant_read_data` runs 表；它的 environment 不再带 RUNS_TABLE，要把 common_env 拆开。ddb.py 的 `is_detached` docstring 后半句改成只供 list-runs --json 的 detached 键。
- 文件：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py、deploy_aws/gherkai_deploy_aws/stack.py、core/gherkai_core/adapters/run_store/ddb.py、deploy_aws/tests/test_lambda_handlers.py、deploy_aws/tests/test_stack.py
- 先要有：前台云端 run 已删去（「云端只支持 submit」块）：否则同一个 cluster 上的前台云端 run 会被推进器和观察者当成后台 run
- 必须同批：kicker 过滤删去 detached（云端-2）
- 单独先落地的后果：run --backend cloud 还在时：前台云端 run 的 worker 事件触发 reconciler，run 被认领、推进，重复起 task，两方各自收尾；观察者给前台 run 写 task_exited，前台 FargateWorkerHandle 读 events 表时会碰到没有 body 的退出项。会变红的测试：test_reconciler_noop_for_non_detached_run、test_exit_observer_skips_non_detached_run、test_kicker_timeout_path_skips_tick_when_not_detached、test_exit_observer_can_read_runs_table_only，以及 deploy_aws/tests/test_lambda_handlers.py「只推进 detached run」整节，都要删改。
- 验证：「已不分流」单测就够。观察者的 IAM 收窄（不读 runs 表）随重新部署生效；code 里已经没有读，单测可证；部署后一次真实云端 submit 的 exit-observer 日志零 AccessDenied 是顺带核对。
- 备注：现状与线索一致。
  
  `_build` 的 docstring 写「None 表示本 run 云端推进器不该动（非 detached / 已收尾 / definition 不在库）」，要随之改；「已收尾」那一支还要改成走清扫（云端-5）。
  
  「随实装改写的 code 注释」块没有列这几处：reconciler 模块头第 6 行（「叠加 status --wait 接力」），kicker_handler 的 docstring（status --wait kickoff、「四宿主一份 tick（… status 接力）」），`_build` docstring 里「与同步 cloud run 路径一致」，DynamoDBRunStore.__init__ 讲 detached 参数的 docstring。

#### 云端-4（mixed，L）

- 线索：kicker 收到 STATE 新建时建 run 的两次一次性定时触发：deadline_at 一次
- 要做的：reconciler.py：kicker 处理流上的 STATE INSERT 时，先给这个 run 建两个一次性 schedule，再 tick。名字由 run_id 确定；ConflictException 视为已建，其余异常照常抛出，让这次调用失败。payload 用新形态，例如 {"run_id", "run_timer": "deadline" 或 "expiry"}。kicker_handler 按 payload 分流：期限那一次，按墙钟复查 deadline_at（从 `_handle_timeout` 抽出等待循环复用，额度同样是 60 秒与 Lambda 剩余时间取小），已过就对每个 running 的 job 做 job 到点停止，然后 tick；期限加 300 秒那一次，复查已过，读运行态，已结束只清扫，否则调 runtime 的处置（结束写，说明取「已超过允许运行的时间」一行加「（已记为已结束）」），写成就从记录生成报告。把 EventBridgeTimeoutWatch 的建名与 create_schedule 抽出来共用。names.py 加 run 触发的基名与建名函数，重核 prefix_max_len。stack.py 的 timeout_schedule_arns 加入 run 触发的名字空间。
- 文件：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、runtime/gherkai_runtime/names.py、deploy_aws/gherkai_deploy_aws/names.py、deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/tests/test_lambda_handlers.py、deploy_aws/tests/test_stack.py、runtime/tests/test_names.py
- 先要有：结束写入口（状态取法块）；runtime 包里的处置判定与动作（处置块）：Lambda asset 已经带 gherkai_runtime，可以直接复用；报告从记录组装 RunResult 再生成（报告块）；run 两次触发的名字形态与 IAM 资源域（「核对时补上的条目」里的待定项）；META 带 deadline_at（已实装：create_run 把它摊成顶层属性，deadline_of(meta) 可读）
- 必须同批：清扫（云端-5）：定时触发到达时 run 已结束，只做清扫；kicker 过滤①按 item_type=STATE 收新建（云端-2）；删去 CLI status --wait 的卡住检测与 kickoff（处置块）：次序约束要求它与本条同批或排在之后
- 单独先落地的后果：只加期限那一次：无害，和 job 自己的到点触发重叠。只加期限加 300 秒那一次，而结束写入口与报告组装还没就绪：只能用 try_finalize 写下 run 级终态，job 留在 running 或 pending，违背「run 是终态当且仅当全部 job 是终态」。Scheduler 资源域没扩：每次 CreateSchedule 都 AccessDenied，kicker 这次调用失败，流重试耗尽后整批丢弃，同批其它 run 的冷启动跟着丢，后果比 job 超时触发的 best-effort 严重。
- 验证：单测（假 scheduler client、注入时钟）覆盖：建名、幂等、payload 分流、等待额度，以及到点时 run 已结束只清扫。真实行为要在重新部署后的云端核：0054 实测项 3（期限落在执行中途、无人查看，到期后 task 被停、未启动的 job 不启动、run 按 0031 决定三结束）；实测项 8（job 自己的超时触发缺失、worker 不出事件时，由期限那一次停掉 task）；实测项 21（停掉 events 表流的事件源映射、不执行处置命令，由期限加 300 秒那一次结束 run，记下两次触发的到达时刻）。另要核 at() 落在过去时 Scheduler 的表现（拿不准）。
- 备注：现状：kicker 只有 job 级的 schedule（CloudLauncher 起 task 之前调 EventBridgeTimeoutWatch.arm），没有任何 run 级触发。`_run_ids_from_runs_stream` 把流记录与直接 invoke 合成一个 run_id 集合，分不出新建和终态写。
  
  名字空间：沿用 `{prefix}job-timeout-` 可以不改 IAM 与 prefix 上限，但名字与用途不符；另立名字空间就要改 IAM 资源域、重核 prefix_max_len，并补 0033 资源清单 15 与 0054 决策九末段。由实装定。
  
  线索没写的连带：CreateSchedule 失败让调用失败，而 kicker ESM 是 batch_size=5、retry_attempts=2，一个 run 建不成会让同批其它 run 跟着重试（幂等，但多出认领与投影的调用）；可以考虑 bisect_batch_on_error。期限那一次要停的 job 至多 20 个（部署侧 cap），现在 `_handle_timeout` 每个 job 各自翻一遍 ListTasks 与 DescribeTasks；在 2 分钟的 Lambda 超时里（含至多 60 秒等待和 30 秒预留），宜改成整个 run 只列一次。

#### 云端-5（mixed，M）

- 线索：结束即清扫：run 到终态之后按 startedBy 列出仍在执行的 task 逐个停掉
- 要做的：reconciler.py 新增清扫函数：ListTasks(cluster, startedBy=run_id, desiredStatus=RUNNING) 翻页，逐个 StopTask，reason 不带超时哨兵；失败就抛出，让调用失败。`_build` 的「已结束」一支改为返回能和「不推进」区分的结果；handler、kicker_handler 与 `_tick_runs` 遇到它就清扫，流触发的在批内按 run 去重；tick 返回 ENDED 时同样清扫。`_handle_timeout` 的 `_check` 先看 run 是否已结束，已结束就清扫，再看 job 状态。清扫排在读 definition 之前，不需要 meta。
- 文件：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/tests/test_lambda_handlers.py
- 先要有：kicker 过滤②（云端-2）：把使 run 成为终态的写送到 kicker
- 必须同批：云端-2；云端-4：定时触发到达已结束的 run 时只清扫
- 单独先落地的后果：只在 handler 里加清扫、不改过滤：只有 run 结束之后迟到的事件或定时触发才会清扫，正常结束或被处置结束的 run 上仍在执行的 task 没人停。test_finished_run_is_not_reprojected_by_a_late_or_replayed_event 与 test_timeout_payload_on_a_finished_run_is_a_noop 现在断言「什么都不做」，要改成断言清扫（用假 ECS）。
- 验证：单测（假 ECS）证明调用次序，以及清扫排在「已结束的 run 跳过」之前。真实行为要在重新部署后核：0054 实测项 21 的后半（settle-runs 结束的 run、结束之后才启动的 task 都被清扫）；ListTasks 最终一致性下刚起的 task 列不到的情形；被停的 task 引出的 STOPPED 事件不形成回路（清扫不写 runs 表）。
- 备注：现状：`_build` 读到终态返回 None，handler 什么都不做。`_handle_timeout` 里已有按 startedBy 翻页列 task 的代码，可以抽出来复用。
  
  权限：推进 Lambda 已有 ecs:ListTasks、StopTask、DescribeTasks（资源为 *），不用新增；建定时触发的资源域随云端-4 一起改。stack.py 第 782、785 行注释里的「超时处置」是要退役的词，随之改。
  
  清扫的 StopTask reason 如果带 `gherkai-job-timeout`，观察者会把退出记成超时；run 已结束时这条记录不被采用，但为免误读，宜用另一句。cluster 名取 env CLUSTER，与 `_handle_timeout` 同源。

#### 云端-6（doc，M）

- 线索：编排进程一侧的权限按 0033 改：删去同步 run 的 ecs:RunTask、StopTask
- 要做的：只改文档，code 里没有编排进程角色（stack 不建它）。docs/user-guide/cloud-backend.md「团队成员需要的最小云端权限」改成单级（submit、status --wait、settle-runs）：删去 run --backend cloud 一级，删去「调用 `<prefix>kicker` Lambda」，保留 lambda:GetFunction；加上处置所需的 runs 表条件写、报告桶 s3:GetObject（卸载的运行定义正文与被点名的明细）、报告前缀 s3:PutObject，以及 settle-runs 不给 run_id 时 list-runs 的两项。running-and-results.md「怎么运行、在哪运行：三种组合」节的权限表、getting-started.md 的角色表、skill references/cloud-backend.md「1 分工」表同样改。
- 文件：docs/user-guide/cloud-backend.md、docs/user-guide/running-and-results.md、docs/user-guide/getting-started.md、cli/gherkai_cli/skills/gherkai/references/cloud-backend.md
- 先要有：删去 run --backend cloud（「云端只支持 submit」块）；删去 status --wait 的 kickoff（处置块）；settle-runs 与云端 status --wait 的处置（处置块）
- 必须同批：对应的行为批：删 lambda:InvokeFunction 和删 kickoff 同批；删 run 一级和删 run --backend cloud 同批；加处置权限和 settle-runs 同批
- 单独先落地的后果：单独先改文档，权限面就和 code 对不上。例如文档先去掉 InvokeFunction 时，status --wait 仍会 invoke kicker，按文档授权的角色会 AccessDenied。
- 验证：文档逐项对照 0033 资源清单末段的编排进程角色做差集。建议重新部署后按文档授权建一个受限角色，真跑 submit、status --wait（含处置）、settle-runs、list-runs、explain，核零 AccessDenied（0033 设备权限用过同样的做法）。
- 备注：这一条与「行为文档」块里三条重复：running-and-results.md 与 getting-started.md（0040 派生视图）、agent skill 的 references/cloud-backend.md、cloud-backend.md「最小云端权限」一节。排批时合并成一处。
  
  线索写的「删去同步 run 的 events 表 Query」只指 run 那一级；explain 补取仍要 events 表的 dynamodb:Query（0033 编排进程角色），不能一起删。0033 编排进程角色还没有登记 explain 读明细与 evidence 的 s3:GetObject，journey 的待定项里已经列了。

## 查看命令与机读输出

### 小结

整块合计 L，大头是查看-1（run --json 的 jobs[] 与文本汇总从记录组装）和查看-7（explain 改按运行态与点名取明细），两条都要改 RunResult 或明细的组装方式，并重写大量 cli 测试。另有一组只读查看面的小改动：查看-3、4、5 的期限读取与提示，查看-6 的 doctor 一行，查看-2 的退出码，查看-8 的日志指引。

内部次序：
1. 先做查看-3 与查看-5 的头部读取扩展（peek_definition_header 与 RunListing 带 deadline_at）。它们只读 META 和 run_meta.json 里已有的属性，不依赖新的写入设计，可以先落；两列与 deadline_at 键可以同批。
2. 查看-2 的退出码读记录现在单独落也安全。
3. 查看-4 的期限提示、FOREGROUND_RUN_NOTE 的删除、删 pending 接力提示，要与 run 处置块（settle-runs、status --wait 处置、300 秒常量）和删本机接力同批落，或排在它们之后。
4. 查看-6 排在锁块的边界检查函数之后。
5. 查看-1 与报告块（从记录组装 RunResult、index.html、删「没有执行」）、状态取法与结束写块（前台不构造 skipped、结束写、JobState 带说明）同批落。
6. 查看-7 与判定明细点名块（端口去掉 load_all）同批落，查看-8 随查看-7。

对别的块的依赖：状态取法与结束写（取法函数、结束写、JobState.message）、判定明细点名（JobState 标识、按标识读、去 load_all）、报告（从记录组装）、本机推进器与边界检查、run 处置（settle-runs、300 秒判断）、删本机接力。云端一侧，status 的点名键和 explain 读点名明细、补取 aborted job 的真实验证，要等推进器 Lambda 重新部署之后才能做。这一块的读取改动本身（META 投影、BatchGetItem 投影多带 deadline_at）只读已有属性，不需要重新部署。

最大的风险：
- 由结束写结束的 job 没有 JobResult，RunResult 用什么数据结构承载这类 job，ADR 只写了输出语义、没有定。run --json、文本汇总、报告、explain 四处都要从同一份组装出来，定错会让这几处各写一份。
- JobState 现在没有 job 级 message，这一点没有任何线索点名。
- 「run 被别处结束」的出口依赖真实的进程与时序，要在本机真实执行。
- doctor 的文件系统判断依赖真实的 statfs，单测不算证据。

### 线索没有覆盖的改动点

- cli/gherkai_cli/__main__.py `_status_cmd`：云端带上本次命令行显式给出的 --ddb-table 与 --region，不带 --profile；submit、status、explain 的提示都经它，并补测试。依据：journey 0018「删除过程文档之前找到、ADR 里还没有的内容」中「提示里的 gherkai status 命令怎样拼」一条（owner 2026-11-15 同意）。这条规则还没有写进 ADR 0042 决策四或 0041 决策六，要先定写进哪里；显式给出的 --config 带不带，待 owner 定。
- cli/gherkai_cli/__main__.py `_ended_elsewhere_notice`：说明里加回查看这条记录的 status 命令（本机带 --report-dir）。依据同上一条的「另外」段，以及建议补进 ADR 0054 决策五末条的那一句（还没有写进 ADR）。
- 本机 status 与 explain 在 LocalRunStore.peek_definition_header 与 load_run_state 上捕获 JSON 解析失败和顶层不是对象这两种情形，以退出码 2 结束并给一句产品语言的说明；status --wait 那一支按 0054 决策八只等待并说明原因。现在 `_definition_header_gate` 与 `_cmd_status_body` 只接 DefinitionContractError，这两种情形是未捕获的异常。补测试：损坏的 run_meta.json 与损坏的 run_state.json 各一例。位置：cli/gherkai_cli/__main__.py、core/gherkai_core/adapters/run_store/local.py。依据：journey 0018「提交记录或运行态本身解析不了时的出口」第三段；ADR 0037 决策 7 与 0031 决定五的补句要等 owner 对第四段拍板。
- list-runs 两列的计时细节：「已运行」从运行态的 started_at 起算，已结束的取 started_at 到 ended_at；「允许运行至」的表头注明本地时区；当前时刻每次清单只取一次、各行共用；运行态读不出的行两列都是 -；括注按 deadline_at 本身计、不含 300 秒。位置：cli/gherkai_cli/render.py `render_run_list`。依据：journey 0018「list-runs「已运行」「允许运行至」两列的计时细节」一条，其中括注一句建议进 ADR 0041 决策七「人读形态」，还没有写进去。
- detached 在两个后端用同一判据：core/gherkai_core/adapters/run_store/ddb.py 的 `is_detached` 与 `_read_listing_rows` 现在用 `bool(...)` 判断，要改为 `is True`（本机 local.py 已经是 `is True`）。依据：journey 0018「detached 键在两个后端用同一判据」一条，建议补进 ADR 0041 决策七「机读形态」，还没有写进去。
- 契约页 docs/internals/cli-json-contract.md 与 skill 副本里，按新取法改写的不只是行为文档块列出的几个新键：run 一节 status 与 message 两行（run_verdict 的两种例外、「没有执行的 scope 保持 pending」）；status 一节 status 取值去掉 run 级 skipped、改写 message 与 jobs[] 两行（job 不再「保持 pending」，结束写写下 job 说明）；list-runs 一节 detached 一行（去掉「status --wait 只等待、不接力」）；run 一节末段「已得出的 job 判定照常写入」。依据：ADR 0031 决定三、0041 决策三与决策七、0054 决策五。
- cli/gherkai_cli/render.py `render_run_state` 的 docstring 写着「权威判定明细读 jobs/*.json」，jobs/*.json 在收尾的残留检索表里，要改为经 explain 或 --json 读。status 的人读输出要不要显示由结束写写下的 job 级说明，ADR 0041 与 0034「命令形态」都没有写，实装时要定，或交 owner。

### 逐条

#### 查看-1（mixed，L）

- 线索：`run --json` 新增 jobs[]：列出运行定义里的全部 job
- 要做的：run --json 的 jobs[] 改为按运行定义逐个列出全部 job：状态取运行态，由结束写结束的 job 只带 scope_id、status 与运行态里的 job 说明，被点名的 job 附上那一份明细的各键；有记录时这份文档从记录组装（运行态加被点名的明细），--no-report 时按同一套规则在内存里给出。render_text 同步：删去 jobs_without_verdict 那段与「没有执行」标注，由结束写结束的 job 显示状态与说明。run 已被别处结束时：RunPersistence 一旦发出停手信号，on_job_complete 不再存明细、不写终态；_ended_elsewhere_notice 删去「已得出的判定已写入」这半句；stdout 为空、不生成报告、退出码 1 或 130/143，这几项现在已经是这样。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、core/gherkai_core/serialize.py、core/gherkai_core/model.py、core/gherkai_core/persist.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py、cli/tests/test_render.py、cli/tests/test_main.py、core/tests/test_persist.py
- 先要有：JobState 带 job 级说明（结束写把说明写进运行态的每个 job；现在的 JobState 没有 message 字段）；运行态的点名标识与 ResultStore 按标识读明细（判定明细点名块）；结束写入口与 RunPersistence.finalize 改用它（状态取法与结束写块）；前台没有启动的 job 不再构造 skipped 的 JobResult（状态取法与结束写块）；从记录组装 RunResult 的共用函数（报告块）；run 状态取法函数（--no-report 在内存里算要用）
- 必须同批：报告块的 index.html 一条（删 core 入口页与 cli `_NOT_RUN_LABEL` 的「没有执行」、render_text 改写）；契约页 run 一节与 `test_run_json_top_level_message_is_always_present_and_documented_as_run_level` 的改写；running-and-results.md 退出码表 run 一行（run 已被别处结束时 stdout 为空、退出码 1 或 130/143）
- 单独先落地的后果：做不成：现在的 RunResult 只装有判定的 job，运行态里没有 job 级说明、也没有点名标识，jobs[] 没有数据来源。要是硬按现在的运行态拼出 jobs[]，没有启动的 job 会以 pending、不带说明出现，与 render_text 的「没有执行」标注和契约页的「没有执行的 scope 不在 jobs[] 里」都对不上，test_cli_json_contract 与 test_render 会红。
- 验证：形状、--no-report 在内存里的取值、文本汇总用单测即可（fake store 与真本机文件 store）。「run 在本次执行结束之前已被别处结束」依赖真实的进程与时序，要在本机真实执行：前台 run 执行期间另开进程用 settle-runs 或 status --wait 处置（或把 run 进程 SIGSTOP 到期限加 300 秒之后再 SIGCONT，即 0054 实测项 16、17），断言 stdout 为空、退出码 1、之后没有新的明细文件、没有报告；带引擎的那一次放在跳板机上执行。
- 备注：①JobState 现在只有 scope_id、status、session_id、claimed_at，没有 job 级 message。run --json、status、explain、报告要给出结束写写下的说明，都要先给 JobState 加这个字段，连同 serialize 的 run_state 读写与 DDB 的 jobs Map。这件事应该放在结束写那一块，可那一块的线索没有点名 JobState.message。②0041 决策三只定了 jobs[] 的语义，RunResult 用什么数据结构承载「没有明细、只有运行态」的 job 没有定：JobResult 带可选的 job 状态，还是 RunResult 另带一份运行态。这一点决定 serialize.to_dict、from_dict、报告与 explain 怎么共用。③--no-report 没有记录，ADR 0054 决策二写的是「第 3、4 条的结果按同一套规则在内存里给出」，这里要有一处在内存里模拟结束写（pending 记 skipped），线索没有写。④__main__.py 第 3197 行 stderr 打的「判定明细: jobs_dir」仍然成立，0054 决策五要求说明与判定明细的落点写在 stderr。⑤契约页 run 一节的 status 与 message 两行（run_verdict 的两种例外、「没有执行的 scope 保持 pending」）都要按新取法改写，不只是加 jobs[]。

#### 查看-2（code，S）

- 线索：退出码读记录：有记录时读记录里的 run 状态
- 要做的：_cmd_run 在 finalize 之后读一次运行态（或让 finalize 返回它写成的或读到的运行态），按其中的 run 状态给退出码；--no-report 时用状态取法函数在内存里算。status 与 status --wait 已经经 _render_status 读记录，不用改。三类退出码 2（边界检查不过、锁被持有或不可用、run 给出云端后端）分别由锁块与云端只支持 submit 块实现，这一条只核对它们的出口。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_main.py
- 先要有：run 状态取法函数（状态取法与结束写块），--no-report 要用
- 必须同批：无
- 单独先落地的后果：无。现在 try_finalize 写进记录的就是 result.status，读记录与读内存得到同一个值；等状态取法块落地之后，这一条保证退出码与记录一致。
- 验证：单测够：退出码只看记录与取法，属于纯逻辑；在 fake store 里预置运行态，断言退出码跟着记录走，--no-report 走内存。
- 备注：现在第 3224 行写的是 `return 0 if result.status == Status.PASSED else 1`，注释里写着「不回读落库态」，正与目标相反，要改注释。0031 决定五的「退出码 2」条现在写的是四类，比线索多「本机后台推进进程在回报之前退出（由 submit 给出）」一类，这一类属于隧道与 submit 新流程块。journey「写回时留下、实装之前要定的问题」里还有一条没有定：本机 run 运行期失败的退出码是不是 1，0030 决定七写的是「非零」。

#### 查看-3（mixed，M）

- 线索：`status --json` 的 jobs[] 每项带这个 job 终态点名的明细标识
- 要做的：jobs[] 的点名标识一项，只要 serialize.run_state_to_dict 写出 JobState 的点名键（点名块的线索），status --json 就会自动带上。deadline_at 要新增读取：把 RunStore.peek_definition_header 扩成同时返回 deadline_at（本机 run_meta.json 已经整份解析过；云端 META 的顶层已有 deadline_at，ProjectionExpression 加上这一项即可），_definition_header_gate 把头部交回调用方，_render_status 在 JSON 顶层加 deadline_at，读不到就省键。
- 文件：core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、cli/gherkai_cli/__main__.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py、core/tests/test_stores.py、core/tests/test_ddb_run_store.py
- 先要有：运行态的点名标识（判定明细点名块，JobState 与 serialize 的那一条）
- 必须同批：契约页 status 一节加 deadline_at 与点名标识两行（test_status_json_keys_are_documented 按真渲染器收集键，文档漏写即红）
- 单独先落地的后果：只做 deadline_at 时没有影响，契约页同一提交补上即可。点名标识要等点名块落地之后才出现。
- 验证：单测够：本机文件 store 与 moto 上的头部读取都覆盖 deadline_at，契约护栏收集键名。云端 jobs Map 里真带点名键，要等推进器 Lambda 按新写序写下明细并点名之后，在重新部署的云端上执行 status --json 核一次。deadline_at 只读 META 上已有的属性，不需要重新部署。
- 备注：头部读取扩成三项，要连带改 `_definition_header_gate` 和 `_definition_schema_gate` 的签名、`require_listing_header`，以及 list-runs 的 RunListing.header（查看-5 也要这次读取，两条宜同一批）。「_render_status 拿到 deadline_at」也是查看-4 的前提。status --json 的 RunState 部分要不要也带 job 级说明（JobState.message 写出之后会自动出现），ADR 0041 决策三没有提，契约页要写明。

#### 查看-4（code，M）

- 线索：不带 `--wait` 的 status 与 list-runs 给同一句期限提示
- 要做的：在 runtime 或 cli 放一个共用的判断（未结束，且当前墙钟严格晚于 deadline_at 加 300 秒），给出同一句「已超过允许运行的时间（可用 settle-runs 或 status --wait 记为已结束）」：_render_status 用在不带 --wait、非 --json 的人读输出上，render_run_list 用在提示列。删去 _render_status 里「推进可能未启动、可 status --wait 接力」的 pending 提示、relay_available 参数与 wait_hint 参数，以及 _status_cloud 里的 _relay_available 和 _cmd_status_body 里传入的回调。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、runtime/gherkai_runtime/deadline.py、cli/tests/test_main.py、cli/tests/test_render.py
- 先要有：status 读到 deadline_at（查看-3 的头部读取）；list-runs 列举项带 deadline_at（查看-5）；期限加 300 秒这个常量与按墙钟判断的函数（run 处置块，status --wait 与 settle-runs 共用，宜只有一处）
- 必须同批：settle-runs 命令（run 处置块）：提示里点名了 settle-runs，命令不在就是一句指不到地方的提示；等待中的 status --wait 会处置（run 处置块）：提示说 status --wait 能记为已结束；删去本机接力与云端 kickoff（锁块与处置块）：在这之前「status --wait 接力」的提示仍然成立，先删提示会丢掉一条仍然有效的指引
- 单独先落地的后果：提示指向还不存在的 settle-runs，status --wait 现在也不会把过期的 run 记为已结束，使用者照提示做是做不成的；pending 接力提示删早了，现存的接力能力就少了一条指引。test_main 里断言「可接力推进」提示的用例会红。
- 验证：单测够：只看记录与期限、不碰锁，注入墙钟后覆盖严格晚于、恰好相等、未结束与已结束几种情形。
- 备注：现在 runtime 里没有「300 秒」这个常量，deadline.py 只有 STARTUP_MARGIN_S 与尾段。云端 _status_cloud 里的 _relay_available 读 is_detached，删去之后，云端 status 不带 --wait 时就不再读 detached 标记。_render_status 的 docstring 与第 2103 至 2112 行一大段注释讲的都是接力提示的判据，要一并删去。读不到期限的 run 不给期限提示，ADR 0041 决策七写的是「其余不给期限提示」。

#### 查看-5（mixed，M）

- 线索：list-runs：人读表格按列序加「已运行」「允许运行至」两列
- 要做的：RunListing 加 deadline_at 字段，两个 adapter 的 list_runs 在同一次头部读取里取它：本机 _listing_header 同一次解析，云端 _LISTING_ATTRS 加 deadline_at 进 BatchGetItem 的投影。render_run_list 按列序加「已运行」「允许运行至」，提示列放期限提示，删去 FOREGROUND_RUN_NOTE；run_listing_to_dict 加 deadline_at，读不到时省键。--status 的 choices 去掉 skipped（argparse 给出时以退出码 2 结束）；_LIST_RUNS_TERMINAL 不再查 skipped，定了查几个终态分组之后回写 0041 决策七「代价」段与实测项的读量。
- 文件：core/gherkai_core/model.py、core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、docs/adr/0041-agent-facing-cli-affordances.md、cli/tests/test_main.py、cli/tests/test_render.py、cli/tests/test_cli_json_contract.py、core/tests/test_stores.py、core/tests/test_ddb_run_store.py
- 先要有：run 的状态不会是 skipped（状态取法与结束写块删去 run_verdict），--status 才能拒收 skipped、默认清单才能少查一个分组；期限加 300 秒的共用判断（查看-4）
- 必须同批：查看-4（提示列里的期限提示是同一句）；删去本机接力（锁块）：FOREGROUND_RUN_NOTE 写的是「status --wait 对它只等待、不接力」，在接力还在时它是对的，删了接力它就错，要同一批删；契约页 list-runs 一节加 deadline_at，并改写 detached 一行的「status --wait 对它只等待、不接力」
- 单独先落地的后果：两列与 deadline_at 单独做没有影响。--status 拒收 skipped 与少查 skipped 分组要是先于删 run_verdict 落地，现行代码在理论上仍能产出 skipped 的 run，这样的 run 会从默认清单里消失。FOREGROUND_RUN_NOTE 先删，在接力还在的那段时间里就丢了一条仍然正确的说明。
- 验证：两列、JSON 与参数校验用单测（注入当前时刻，本机文件 store 与 moto）。BatchGetItem 投影多带 deadline_at 用 moto 即可。默认清单查几个分组之后的读量，ADR 要求回写实测值，要在真实 DynamoDB 上用 ReturnConsumedCapacity 测，只读、不需要重新部署。
- 备注：现在 RunListing 只有 run_id、state、detached、header，没有 deadline_at；本机 _listing_header 走 peek_definition_header 整份解析 run_meta.json，云端 _header_from_item 只取 schema_version 与 cli_version。--status 的 choices 现在取 [s.value for s in Status]，help 文案也是从 Status 拼出来的，两处都要排除 skipped。ADR 0041 决策七写的是「默认清单查五个终态」，现在的 _LIST_RUNS_TERMINAL 也是五个，其中含 skipped；去掉之后是四个，「代价」段的 N 到 5N 一类数字要随之改。detached 的判据改成 `is True` 那一条见 missing。

#### 查看-6（mixed，S）

- 线索：doctor 新增 report_dir 组的 report_dir.filesystem 一项
- 要做的：_cmd_doctor 在不查云端时（want_cloud 为假）add('report_dir', 'filesystem', ...)，必修。调用锁块新增的边界检查判断（对报告目录取文件系统类型；目录不存在时取最近一层已存在的上级），只读、不取锁，detail 写原因、检测到的类型与放行清单。doctor 子命令 --report-dir 的 help 去掉 [cloud]。契约页 doctor 一节的 section 取值加 report_dir、项名表加 filesystem。
- 文件：cli/gherkai_cli/__main__.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_main.py、cli/tests/test_cli_json_contract.py
- 先要有：边界检查判断函数（锁块的边界检查一条，模块放在 runtime）
- 必须同批：契约页 doctor 一节（test_doctor_json_keys_are_documented 核键名；项名表是人工对照，没有测试守）
- 单独先落地的后果：判断函数不在就无从调用。要是先在 doctor 里自写一份判断，就和 run、submit、settle-runs、status --wait 用的不是同一份，违反 0054 决策四「共用同一判断」。test_main 里列举 doctor 全部行或未查行的用例（如第 2075 行、第 2481 行附近）要补上这一行。
- 验证：单测只能覆盖清单匹配与 detail 的写法，取文件系统类型依赖真实的 statfs 与挂载信息，要真实执行：macOS 的 APFS 目录放行；Linux 上 ext4、tmpfs、overlay（容器里）各放行一次；清单之外的类型（如 macOS Docker Desktop 宿主目录在容器里的 fakeowner，或 NFS、SMB）被拒、退出码 2。这项实测与锁块的边界检查共用，doctor 这一侧核一次输出即可。
- 备注：settings.py 把只给 --prefix 的 doctor 也当作云端（use_cloud 判据），而 ADR 0041 决策四只写「--backend cloud 时不出这一行」，没说只给 --prefix 时怎样；按现在的 want_cloud 判据，只给 --prefix 时也不出这一行，要在 ADR 或契约页写明。项名 report_dir.filesystem 是写回时执笔自定的，owner 还没有确认（journey「写回时留下、实装之前要定的问题」）。doctor 的 --report-dir 在本机后端缺省为 reports（BUILTIN_DEFAULTS），只有来自配置文件时才绝对化，判断前要先 resolve。

#### 查看-7（code，L）

- 线索：explain：先经 RunStore 读运行定义与运行态
- 要做的：_cmd_explain 与 _explain_cloud 在头部闸之后读 load_run_meta（job 定义）与 load_run_state，按运行态里各 job 的点名标识用 ResultStore 取那一份明细，删去 load_all。运行态里未结束的 job 不进文档；由结束写结束的 job 以 job 定义为骨架，状态与说明取运行态，记 aborted 的经 _explain_recover 从事件流补取已执行的 step。_explain_emit 的空文档与 scope_id 分支按运行态判断：没有已结束的 job 时退 0，只打「判定明细尚未落地」加整条 status --wait 命令；给了 scope_id 而它还没结束时退 0 并提示；scope_id 不在定义里才退 2，候选清单取自运行定义。删去「本 run 没有任何 job 的判定明细」，云端删去「不给 scope_id 时还需列举对象的权限」的说法。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、cli/tests/test_main.py、cli/tests/test_render.py、docs/internals/cli-json-contract.md、docs/internals/verdict-model.md
- 先要有：ResultStore 按点名标识读明细、端口去掉 load_all（判定明细点名块）；运行态的点名标识与 JobState 带 job 级说明（判定明细点名块、状态取法与结束写块）；结束写入口（由结束写记 aborted 或 skipped 的 job 要由它产生）
- 必须同批：判定明细点名块的端口一条（它删去 load_all，explain 是 load_all 在 CLI 里唯一的调用方，两边要同一批）；用户文档与 0033 编排进程角色里 explain 的云端权限（不需要 s3:ListBucket）；若「判定明细尚未落地」的原文改了，同一提交改 0031 决定一·补里 TERMINAL_STATUSES 的消费方清单
- 单独先落地的后果：在点名标识与结束写落地之前做不成：没有标识可按，运行态里也没有 job 说明。要是先删 load_all 而 explain 不改，explain 会坏（AttributeError）。test_main 里的 explain 用例大量依赖带 load_all 的假 ResultStore（如第 3161 行、第 3547 行），要整体改写。
- 验证：本机的骨架、补取、scope_id 各分支用单测（fake store 与真本机文件 store 加 SqliteEventLog）。云端两项依赖重新部署之后的真实后端：推进器按新写序点名明细；由后端到期结束或处置记 aborted 的 job 能从 events 表补取 step；以一份不含 s3:ListBucket 的真实 IAM 策略执行 explain 不带 scope_id，确认不再需要列举权限。
- 备注：①现在 _definition_header_gate 只读头部；改读整份 load_run_meta 之后，同版本下的形态违约会在这里抛 DefinitionContractError（本机 run_meta_from_dict），要接住、以退出码 2 结束，否则用户终端会看到回溯。②由结束写结束的 job 没有 JobResult。最省事的做法是合成一个只有 job、status、message、空 scenarios 的 JobResult 交给 explain_to_dict，这样 _needs_recovery 与补取路径原样可用；它与报告块「从记录组装 RunResult」该是同一处组装，不要另写一份。③云端 load_run_meta 在运行定义卸载到 S3 时要多一次 GetObject，0042 决策四写的权限已含桶 s3:GetObject。④_explain_emit 的 docstring 讲「带 scope_id 只 load_job_result、不带才 load_all」，第 2627 至 2630 行的注释讲「后台 run 一次收尾尝试落下判定明细」，都随改。

#### 查看-8（code，S）

- 线索：「诊断细节见 worker 日志」只对运行态里带认领时刻的 job 打
- 要做的：explain_to_dict 的 scope 文档带上「这个 job 在运行态里有没有认领时刻」这一事实（取自 state.jobs[scope].claimed_at），explain_tree 打「诊断细节见 worker 日志」的条件加上这一项：没有认领时刻的 job 只给判定行（状态与说明）。改 explain_tree 与 explain_to_dict 里讲这条判据的注释，补测试。
- 文件：cli/gherkai_cli/render.py、cli/gherkai_cli/__main__.py、cli/tests/test_render.py、cli/tests/test_main.py
- 先要有：explain 从运行态取 job 清单（查看-7），把认领时刻传进渲染
- 必须同批：docs/internals/artifacts-and-evidence.md explain 文本形态表里这一条件（行为文档块已列）
- 单独先落地的后果：无害。现在 fail-fast 记 skipped 的 job 本来就没有认领时刻，单独落地只是这类 job 不再被引去看 worker 日志；只是取运行态要在 explain 里多读一次（现在 explain 已经读了运行态，传下去即可）。
- 验证：单测够：纯渲染判据。
- 备注：ADR 0042 只定了文本形态的条件，没有说 explain --json 要不要多一个键（比如 claimed_at）。如果在 scope 文档里加机读键，就进了契约面，契约页 explain 一节与 test_explain_json_keys_are_documented 都要跟着改；要是只作渲染用的内部参数，就不进 JSON。这一点要实装时定。

## 报告

### 小结

「报告」这一块有两条线索，合计属于 L 级。第一条跨 core、runtime、deploy_aws 三个包，要改 RunResult 的数据结构，删去 TickResult.result，生成报告的入口改为「从记录组装再渲染」，调用方有四处：前台的 RunPersistence.finalize、本机的 run_reconcile_loop、云端的 _tick_runs、处置方。第二条是 M 级的渲染改动，涉及 index.html 与 cli 文本汇总。

内部次序：先定 RunResult 怎样携带由结束写结束的 job，再改组装入口和调用方，渲染随后。两条必须在同一批落地。

对别的块的依赖很重，基本排在最后：
- 判定明细点名：按标识读明细，JobState 带标识。
- 结束写：JobState 带 job 级说明，前台没有启动的 job 由结束写记 skipped。
- 状态取法：update_job_state 的新语义，后台逐 job 写序下 COMMITTED 的新含义。

处置块（settle-runs 与 status --wait）和云端的后端到期结束都调用这里的组装入口，所以它们排在本块之后，或与本块同一批。

改 deploy_aws 的 _tick_runs 要重新部署才生效。core 入口改名会迫使 Lambda 代码和测试在同一批里改，部署本身可以放到云端那一批。

最大的风险是「只有一方生成报告」：
- 端口现在规定 update_job_state 返回的是「这次写之前 run 是否仍未结束」，写入方无法直接知道「这次写是否使 run 成为终态」。前台和 tick 都要自己推出，或者端口多返回一项。要是靠写后读回判断，处置方在前台两次写之间落下结束写时，两方都会生成报告。
- 这个性质的证据只能来自真实执行：云端重新部署之后在真 DynamoDB 上并发，本机用真实进程 SIGKILL 推进器再由 settle-runs 处置。
- 次要的风险是前台 run 级墙钟的口径（0024 规定由 schedule 包住）。从记录组装之后取哪一个，要先定。

### 线索没有覆盖的改动点

- RunResult 的数据结构改动（core/gherkai_core/model.py）：删去 RunResult.jobs_without_verdict，新增携带「由结束写结束的 job」的字段（Job 加运行态里的状态与说明），run 级 message 的注释改为「结束的原因」。现在的消费方有 local.py 第 348 行、render.py 第 199 行，以及 test_reconcile、test_project、test_termination_parity、test_detached_launcher 里断言 jobs_without_verdict 的用例。依据：0027「index.html 形态」由结束写结束的 job 一条；0041 决策三 run --json 的 jobs[]；0030 决定三「状态的权威是运行态」。
- 写入方怎样得知「本方的写使 run 成为终态」，线索没有写：0030 决定四里 update_job_state 返回的是「这次写之前 run 是否仍未结束」。前台的 RunPersistence（core/gherkai_core/persist.py，最后一个 job 的 on_job_complete 可能就是使 run 成为终态的那次写）与 tick 的逐 job 终态写（core/gherkai_core/reconcile.py）都要据此决定生成不生成报告，要么由调用方推出，要么端口多返回一项。依据：0030 决定二 finalize 一行与决定三时序块；0034 机制三④；0027「报告由谁、在何时、从什么生成」。
- 云端后端到期结束（kicker 在期限加 300 秒那次一次性定时触发里做结束写）写成之后，要由 Lambda 从记录生成报告。云端块的线索只写了结束写，没写报告（位置：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py kicker_handler；依据：0054 决策九第 1 条；0027「报告由谁、在何时、从什么生成」；0034「命令形态」表）。
- 前台 run 级墙钟的来源：0024「三级执行时长」规定同步 run 的 run 级时长由 schedule 整体包住，detached 取 RunState 的 started_at 到 ended_at。从记录组装之后前台报告与汇总取哪一个，要定。要么前台把 schedule 测得的时长传进组装入口，要么改写 0024 的这一句（位置：core/gherkai_core/schedule.py 第 765 行一带，runtime/gherkai_runtime/compose.py run_duration_ms；依据：0024「三级执行时长」）。
- run --no-report 的文本汇总与 --json 里，没有启动的 job 怎样显示：没有记录、没有结束写，结束写块改完之后 schedule 也不再给它们构造 skipped 的 JobResult。0031 决定五只写了 --no-report 的退出码在内存里按取法算，汇总怎样列这些 job 没有写（位置：cli/gherkai_cli/render.py render_text 与 to_dict，cli/gherkai_cli/__main__.py _cmd_run；依据：0031 决定五数据源；0054 决策一「run --no-report 不在范围内」）。
- 讲「没有执行」标注或「报告可重建」的文档，线索与行为文档块都没有逐处登记：docs/user-guide/running-and-results.md 第 122 行（报告首页标为「没有执行」，运行状态里保持 pending）；docs/user-guide/troubleshooting.md 第 89 行；cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md 第 96 行；cli/DEVELOPMENT.md 第 104 行；docs/internals/artifacts-and-evidence.md 第 116、120 行（「可重建」）；core/DEVELOPMENT.md 第 35 行 project.py 条目里的「报告由它直接生成」；CHANGELOG.md 未发行节第 30、31 行讲没有执行的 job 的说法。依据：0027「ReportStore 接口：整 run 一次写」与「index.html 形态」；0031 决定三「结束写」小节。
- 测试块只登记了 K2 的三个测试，报告这一块另外要删改的用例没有登记：core/tests/test_reconcile.py 的 test_report_write_failure_is_isolated（finalize_report 签名变了）与第 558 行对 done.result 的断言；core/tests/test_persist.py 的 test_finalize_without_report_store_returns_none、test_finalize_with_report_store_returns_uri；runtime/tests/test_detached_launcher.py 的 test_report_still_written_when_the_run_duration_read_fails、test_loop_ends_on_finalized_run_with_pending_jobs_without_report 以及第 617 行附近的断言；deploy_aws/tests/test_lambda_handlers.py 第 1087 行的 test_report_still_written_when_the_run_duration_read_fails 与构造 TickResult(COMMITTED, result) 的替身；cli/tests/test_render.py 锁定「没有执行」的两条；cli/tests/test_main.py 期限用例里的 `<b>没有执行</b>` 断言；core/tests/test_report_store.py 与 test_s3_report_store.py 要补「由结束写结束的 job」的渲染与两侧对拍用例。依据：0034 机制三 K2 与回归护栏；0027「index.html 形态」。
- deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py 第 506 行的注释写「finalize_report 只有本 Lambda 与 detached 宿主两个调用点」，改完之后前台与处置方也会调用，这句不再成立，要改（依据：0027「报告由谁、在何时、从什么生成」；0034 机制三④「代价」）。

### 逐条

#### 报告-1（mixed，L）

- 线索：报告只由使 run 成为终态的那次写的写入方生成，生成时从记录组装 RunResult
- 要做的：在 core 新增一处「从记录组装 RunResult」的函数：读 RunMeta 与 RunState，按运行定义的次序逐 job 处理。终态带点名标识的 job，按标识经 ResultStore 读那一份明细，状态改取运行态；终态不带标识的 job（由结束写结束）只带 Job 与运行态里的状态和说明。run 级 status、message 取运行态，合计四键用 project.run_totals 重算，run 级墙钟取 started_at 到 ended_at。用一个新入口取代 reconcile.finalize_report(result, report_store, created_at, run_duration_ms)，形如 write_report_from_record(run_id, run_store, result_store, report_store, created_at)：读记录、组装、ReportStore.write 整段放在失败隔离里（0034 机制三步骤④写明「为生成而读记录的那一次同样在隔离之内」）。删去 TickResult.result 及 __post_init__ 里「COMMITTED 必带结果」的不变量，COMMITTED 只表示这一方的写使 run 成为终态。调用方改为四处：RunPersistence.finalize（本进程的写使 run 成为终态时调用，返回 index 的 URI）、detached.run_reconcile_loop 的 COMMITTED 分支、reconciler._tick_runs 的 COMMITTED 分支，以及处置方（settle-runs、等待中的 status --wait 写成结束写之后）。两个宿主里单独读 RunState 求 duration 的那段隔离代码随之并入新入口。docstring 一并改：ReportStore 类与 write 的「可从 RunResult 完全重建」改为「从记录生成」，RunPersistence.finalize 删去「报告可后续从 RunResult 重建」，finalize_report、TickOutcome、TickResult、_finalize 步骤④、run_reconcile_loop 里讲「用 tick 交还的结果写报告」的说法，以及 compose.run_duration_ms docstring 里的「宿主在 finalize_report 前调」。
- 文件：core/gherkai_core/reconcile.py、core/gherkai_core/persist.py、core/gherkai_core/ports.py、core/gherkai_core/model.py、core/gherkai_core/project.py、runtime/gherkai_runtime/detached.py、runtime/gherkai_runtime/compose.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、cli/gherkai_cli/__main__.py、core/tests/test_reconcile.py、core/tests/test_persist.py、runtime/tests/test_detached_launcher.py、deploy_aws/tests/test_lambda_handlers.py
- 先要有：判定明细点名：ResultStore 按标识读明细（load_job_result 加标识参数、去掉 load_all），JobState 带点名标识，serialize 与两个 RunStore adapter 读写这个键；结束写入口与 JobState 的 job 级说明字段：由结束写结束的 job 的状态与说明要在运行态里（JobState 现在没有 message 字段）；update_job_state 的新语义：run 状态按取法随写落下，job 终态只写一次，写入方能确定这次写是否使 run 成为终态；后台推进的逐 job 写序：tick 的 COMMITTED 改为「记下最后一批终态的写或到期的结束写由本方写成」，不再由 _finalize 一次收尾给出
- 必须同批：报告-2：RunResult 不再用 jobs_without_verdict 表达未执行的 job 之后，render_index_html 与 render_text 必须同时改；测试块里 K2 的三个测试（test_report_comes_from_the_committed_result_not_from_a_second_read_of_the_events、test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots、test_tick_runs_writes_the_report_from_the_committed_tick_result）；前台 run 的输出改为读记录（查看命令块里 run --json 的 jobs[]）：_cmd_run 的汇总与报告应当出自同一份组装结果；随所改行为的技术文档（core/DEVELOPMENT.md 的 project.py 与 reconcile.py 条目、docs/internals/artifacts-and-evidence.md 讲「可重建」的两处）
- 单独先落地的后果：在点名之前单独落地：组装只能按 scope_id 读明细，而现在的 _finalize 不论条件写成不成都先存明细、覆盖同 key，云端两次调用重叠时报告可能取到没写成终态那一方的明细，与记录里的终态不一致（现在靠 TickResult.result 避开了这个问题，test_report_follows_the_committing_round 的文档串写明「B 落下的判定明细与 A 的谁留在存储里不在断言之内」）。在结束写之前单独落地：因期限没有启动的 job 在运行态里停在 pending，从记录组装出来就是 pending。test_reconcile 里构造 TickResult(COMMITTED, result) 与读 done.result 的用例、test_detached_launcher 与 test_lambda_handlers 里的报告用例、test_persist 的 finalize 用例都会变红。
- 验证：组装逻辑（读哪一份明细、状态取运行态、次序、合计）、四处调用方各自在什么时候生成或不生成报告、失败隔离：单测就够，本机文件 adapter 与 moto 两侧都要有用例。「只有一方生成报告」依赖真实并发与条件写，单测不算证据：云端要在重新部署之后，经 Lambda 的代码在真 DynamoDB 上重做并发与几百个 job 的结束写（0034 机制三②的实测项）。本机要真实执行：后台推进进程在 job 结束之后被 SIGKILL，再由 settle-runs 处置，核对报告由处置方从记录生成，明细取被点名的那一份。还要在跳板机上带引擎真实执行一次前台 run 与一次 submit --backend local，核对报告里的 report_refs、合计与运行态一致。
- 备注：①0030 决定四规定 update_job_state 返回的是「run 在这次写之前是否仍未结束」，不是「这次写是否使 run 成为终态」。RunPersistence.finalize 要回答「本进程的写使 run 成为终态」，只能自己推出（每个 job 都由本进程写成终态且返回 True，最后一次就是使 run 成为终态的那次；或者结束写写成），否则端口要多返回一项。要先定下来：处置方在前台两次写之间落下结束写时，靠读回判断会让两方都生成报告。tick 一侧有同样的问题。②墙钟口径：0024「三级执行时长」写的是同步 run 的 run 级时长由 schedule 整体包住，只有 detached 取 RunState 的 started_at 到 ended_at。从记录组装之后前台取哪一个没有写，要么前台把内存里测的时长传进来，要么改 0024。③被点名的明细读不出（文件缺失或损坏）时怎样处理没有写；按失败隔离处理就是没有报告，也可以把这个 job 当作没有明细来显示，要定。④组装结果里由执行结果结束的 job 按什么次序排没有写（0027 只规定由结束写结束的 job 排在后面、按运行定义的次序）；现在前台按完成先后，后台按 project_full 的次序。⑤RunPersistence.finalize(result, ended_at) 的 result 参数在新设计里不再用来生成报告，结束写要的是来路的说明，接口形态随结束写块一起定。⑥reconciler.py 第 506 行注释写「finalize_report 只有本 Lambda 与 detached 宿主两个调用点」，改完之后不成立（前台与处置方也调用），要改。⑦Lambda 一侧的改动要重新部署才会生效。core 的入口改名会迫使 reconciler.py 与它的测试在同一批里改，部署可以排在云端那一批。

#### 报告-2（mixed，M）

- 线索：index.html：由结束写结束的 job 按运行态显示状态（配色同各状态）与说明
- 要做的：render_index_html 渲染完由执行结果结束的 job 之后，按运行定义的次序渲染由结束写结束的 job：圆点按运行态里的状态上色（_STATUS_COLOR 已有 skipped、aborted、error），写出状态词，说明用 _reason_html(None, message)，没有 scenario 树和 📎。删去「没有执行」的字面量与 not_run 的标题写法「另有 N job 没有执行」，换成新的标题措辞；run 级说明那行注释的「没有任何 job 能承载的原因」改为「结束的原因」。cli 一侧删去 _NOT_RUN_LABEL 及上方注释，run_tree/render_text 对这类 job 同样输出状态加说明，不再标「没有执行」。manifest 的 report_index 与入口页都由报告-1 组装出的 RunResult 生成，ref 自然来自被点名的那一份明细，collect_report_index 与 s3.py 的写法不变，只改 docstring 里「判定真值以 ResultStore 的 jobs/*.json 为准」这类说法。删去逐字锁定「没有执行」的测试：test_render 的 test_run_tree_shows_run_message_and_marks_jobs_without_verdict_as_not_run 与 test_index_html_shows_run_message_and_not_run_label_matching_cli_wording，以及 test_main 的 test_run_past_the_deadline_ends_as_error_with_the_run_message 里断言 `<b>没有执行</b>` 的一句。补一个用例：由结束写结束的 job 显示状态与说明、排在后面、没有明细树。
- 文件：core/gherkai_core/adapters/report_store/local.py、core/gherkai_core/adapters/report_store/s3.py、cli/gherkai_cli/render.py、core/gherkai_core/model.py、cli/tests/test_render.py、cli/tests/test_main.py、core/tests/test_report_store.py、core/tests/test_s3_report_store.py、cli/DEVELOPMENT.md
- 先要有：报告-1 定下的 RunResult 结构：怎样携带由结束写结束的 job（Job 加运行态里的状态与说明），以及删去 jobs_without_verdict；JobState 的 job 级说明字段（结束写块）；前台没有启动的 job 改由结束写记 skipped（结束写块里 schedule 与 RunPersistence.finalize 的那一条）
- 必须同批：报告-1；前台与后台的结束写：没有它，因期限没有启动的 job 在运行态里还是 pending，入口页会把它们显示成 pending；查看命令块的 run --json jobs[]：render.to_dict 与 render_text 读的是同一个 RunResult，结构改了两边要一起改；docs/internals/cli-json-contract.md 与 skill 副本里 run 一节的「没有执行」（test_cli_json_contract.py 第 207 行锁定了这句，行为文档块已经登记）
- 单独先落地的后果：只改渲染、不改数据：RunResult 里没有由结束写结束的 job 的来源，那几个 job 在入口页与文本汇总里会消失（现在至少还标「没有执行」）。test_render 的两条与 test_main 的期限用例会变红。
- 验证：单测就够：纯渲染，输入输出都在内存里。可以另在浏览器里打开一份期限截断后的报告看一眼配色与排序，这只是检查外观，不作为证据。
- 备注：①线索说「manifest 的 ref 取被点名的那一份明细」，但 0027「manifest.json 形态」写明 manifest 每条只有 href、没有 ref。准确的说法是 href 由被点名那一份明细里的 ref 算出，code 不需要另改。②0027 只规定「没有明细树」与「措辞和 step 行的『未执行』旁注分开」，标题里的计数怎么写（现在是「判定明细（N job，另有 M job 没有执行）」）没有写，实装时要定新措辞。③s3.py 与 local 共用同一个 render_index_html，只有 docstring 要改。④run --no-report 不写记录，也就没有结束写：在内存结果里，没有启动的 job 既没有 JobResult（结束写块改完之后 schedule 不再构造 skipped），也没有运行态，文本汇总怎样显示它们 ADR 没有写，见 missing。

## 测试

### 小结

整体改动量 L：涉及 4 个包、约 20 个测试文件，几百行以上。线索列的只是受影响测试的一部分，下面 missing 里的连带改动（try_finalize 全量迁移、到期语义、job 级 skipped、load_all）比线索点名的更多。所有被点名的符号都在 code 里找到了，没有改名。

这一块本身没有独立的先后次序，各条跟着自己那一块的 code 批次走：
- 测-8 不依赖 code，可以随任何一批落地。
- 测-1、测-2（moto 与本机部分）、测-4（本机部分）、测-5、测-6 跟着「状态取法与结束写」块。其中测-3 另跟「报告」块，测-2 的点名标识跟「判定明细」块。这是第一个大批，core 之内的测试量最大。
- 测-12 的本机部分跟「本机推进器与锁」块的删接力，按次序约束要排在生命期锁与 run 处置之后或同批。
- 测-9 跟「run 处置」块的 settle-runs（CLOUD 四个键那一半已随「云端只支持 submit」那一批做完）。
- 测-11 只剩 kickoff，跟「run 处置」块，按次序约束要与后端到期结束同批或在其后（前台云端 run 与 resolve_network 那一半已随「云端只支持 submit」那一批做完）。
- 测-10、测-12 的云端部分、测-4 的云端用例、测-2 的真 DDB 部分跟「云端后端」块，宜集中在同一次重新部署的批次里。

最大的风险：
1. 端口把 try_finalize 换成结束写入口之后，13 个测试文件里约 117 处调用要一起迁。到期语义也变了：pending 由结束写记 skipped，run 按取法得 aborted，不再是 ERROR，也不再留 pending。这会在 core、runtime、cli 三个包的测试里连锁变红，第一批必须把它们一起改完才能全绿。
2. 写入序号的条件、并发写入、几百个 job 的项大小上限，以及 DDB 一次写里区分「STATE 不存在」与「run 已结束」，都依赖 moto 之外的真实 DynamoDB 行为，必须在真表上执行。
3. 有一条用例要等 owner 先定：结束写取哪一个来路的说明。在这之前，测-6 的「中断之后已过停止启动」用例写不完。

### 线索没有覆盖的改动点

- 测试里约 117 处 try_finalize 调用要迁到结束写入口（依据 0030 决定四、0031 决定三「结束写」小节）。分布：core/tests/test_persist.py 13、test_reconcile.py 14、test_status_group.py 10、test_cloud_integration.py 6、test_stores.py 5、test_ddb_run_store.py 3、test_local_run_store_lock.py 2、test_subprocess_engine.py 1、test_project.py 1；cli/tests/test_main.py 8；runtime/tests/test_detached_launcher.py 5；deploy_aws/tests/test_lambda_handlers.py 5、test_workers.py 3。其中 test_conditional_writes.py 的 41 处已在测-1 里。不迁则端口一改就红。
- 到期语义变了，断言旧语义的用例要改（依据 0031 决定三取法与「结束写」、0054 实测项 1 与 2）。新语义：未启动的 job 由结束写记 skipped，run 按取法为 aborted，run 级说明「已超过允许运行的时间」由结束写写下。旧用例断言的是 run 为 ERROR 加 RUN_DEADLINE_PASSED_MESSAGE、未启动的 job 留 pending。涉及：test_reconcile.py「到期处理」一节（test_past_stop_start_claims_nothing_and_expires_the_run、test_claim_refused_by_the_deadline_triggers_one_replan_in_the_same_round 等，连同 _SpyRunStore 的 try_finalize 覆写与 finalize_counts）；test_cloud_reconcile.py 的 test_expiry_commits_on_ddb；test_schedule.py「运行期限与这次 run 的记录」一节；test_persist.py；runtime/tests/test_detached_launcher.py；cli/tests/test_main.py、test_render.py、test_cli_json_contract.py。
- 前台不再构造 skipped 的 JobResult（依据 0054 决策二「一次前台执行可能因三种原因停下」段、0031 决定一）。core/tests/test_schedule.py 里有 13 处断言 Status.SKIPPED，含 fail-fast 与使用方中断各节里 b.status == SKIPPED、说明为「收到中断信号：本次运行已中止，未启动（worker 未 spawn）」的断言，要改为 result.jobs 里没有它、由 RunPersistence.finalize 的结束写记 skipped。
- core/tests/test_conditional_writes.py 的 test_ddb_job_write_does_not_report_ended_on_a_run_created_between_its_two_writes（639 行）要删（依据 0034 机制三③：前台 job 写是一次带条件的写）。它的前提是「第一次写被挡之后再写第二次」，回退写删去之后这个前提不在了。
- core/tests/test_cloud_integration.py 的 test_ddb_job_write_on_finalized_run_lands_job_only_real（151 行）在真 DDB 上断言已结束的 run 照写 job，要改为写不成（依据 0054 决策五、0034 机制三③）。同一文件的 test_s3_result_store_round_trip_real 调 load_all，要改为按点名读（依据 0030 决定三「点名」条）。
- ResultStore 去掉 load_all、改为点名读（依据 0030 决定三「点名」条、决定六 ResultStore 段），这一块没有列对应的测试改动。要改的：core/tests/test_s3_result_store.py（19 处）、test_persist.py（4 处）、test_local_result_store_atomic.py（含模块文档串「后写的盖掉先写的」）、test_stores.py；cli/tests/test_main.py（5 处）。
- handler 分流与清扫的测试，线索没有列全（依据 0034 端到端 cloud 1b、0054 决策九第 1、2 条）。①deploy_aws/tests/test_lambda_handlers.py 的 test_kicker_timeout_path_skips_tick_when_not_detached（767 行）、test_exit_observer_skips_non_detached_run 与 test_exit_observer_records_exit_for_detached_run（1174、1182 行），以及全文件 _seed_run 的 detached 参数。②「已收尾的 run 再被触发时 handler 整体 no-op」一节（1021 行起，含 test_finished_run_is_not_reprojected_by_a_late_or_replayed_event、test_timeout_payload_on_a_finished_run_is_a_noop）：新设计下已结束的 run 要清扫（按 startedBy 列 task、逐个停掉），断言要改。③kicker 建两次一次性定时触发、到点复查墙钟、run 已结束时只清扫，需要新增用例。
- deploy_aws/tests/test_stack.py 要新增定时触发与清扫的模板断言（依据 0054 决策九末段权限、0033 资源清单 15），test_reconciler_and_kicker_have_the_same_permission_face（989 行）随之核对。要断言的权限：Scheduler 资源域、推进 Lambda 角色上的 ecs:ListTasks、ecs:StopTask、scheduler:CreateSchedule 与 iam:PassRole。定时触发的名字形态与资源域在 journey 里标为待定，这些断言要等它定下。
- cli 一侧接力与 detached 门控的用例，线索没有列（依据 0034 被拒方案「本机接力，及其改法」、0041 决策七「人读形态」、0054 决策八 status --wait 条）。cli/tests/test_main.py：test_status_wait_on_a_foreground_run_only_waits_and_never_relays（3339 行）、test_status_pending_hint_offers_relay_only_for_detached_runs（3392 行）、test_missing_profile_exits_2_on_cloud_submit_and_local_status_relay（3879 行）。cli/tests/test_project_config.py：test_local_relay_host_reads_definition_not_the_config_file（901 行）。cli/tests/test_backend_cloud.py：test_status_wait_cloud_only_waits_for_a_run_that_is_not_detached（764 行）、test_status_cloud_pending_hint_offers_relay_only_for_detached_runs_and_stays_quiet_when_the_marker_is_unreadable（793 行）、test_status_wait_cloud_exits_2_when_the_detached_marker_cannot_be_read（820 行）。
- cli/tests/test_project_config.py 另有一处要改（依据 0035 被拒方案「保留 --tunnel-ttl，只允许调小」）：COMMON 名单里的 --tunnel-ttl，以及 test_config_errors_exit_2_naming_file_section_and_key 里「tunnel-ttl = 'x'」一行，要随隧道批删去。
- core/tests/test_project.py「投影写的 run 级 status」一节要改（依据 0031 决定三取法、0034 机制三「投影写的 run 状态按取法给出」段）：test_projected_run_status_pending_only_while_all_jobs_pending 的文档串写「终态归 finalize、try_finalize 这个 commit point 专属」；test_run_status_agrees_between_schedule_and_project_full 等对拍用例要随 projected_run_status、project_full 与新取法一起改。
- 测试文件里描述接力的文档串与注释，按新设计改写或删去（依据 0034 被拒方案「本机接力，及其改法」）。涉及：core/tests/test_local_run_store_atomic.py 与 test_local_result_store_atomic.py 的模块文档串；core/tests/test_stores.py 573 行、900 至 934 行（变量名 relay，以及「status --wait 从此把这个后台 run 当成前台 run 只等不接力」一句）；core/tests/test_reconcile.py 176 行；core/tests/test_conditional_writes.py 710 行；runtime/tests/test_compose.py 273 行。收尾检索会扫到它们，但不能指望到那时才改：写着接力的用例在删接力那一批就要改。
- 拿不准：deploy_aws/tests/test_lambda_handlers.py 的 test_starter_run_ids_from_direct_kick（160 行）测的是 kicker 收直接调用的 payload。status --wait 不再 invoke kicker 之后（0054 决策八、0034「推进器与触发源」第 2 条），_run_ids_from_runs_stream 里服务 kickoff 的那一路是否保留由实装定，这条用例随之删或改。

### 逐条

#### 测-1（test，M）

- 线索：改写 test_conditional_writes.py 里断言旧设计的用例
- 要做的：把列出的 7 个用例改成新语义：run 已结束时 update_job_state 写不成、运行态不变（不再「job 照写」），DDB 只发一次 update_item；收尾条件从 expected_claim_count 改为写入序号；删去 test_finalize_from_nonterminal_succeeds（结束写不接受调用方给的 run 状态）。模块文档串里「收尾写可带期望的计数」一句改成写入序号与结束写。文件里其余调用 try_finalize 的用例（约 41 处，含 _finalize 辅助函数与 test_each_write_entry_keeps_top_level_extras 的参数 id）一并迁到新的结束写入口。
- 文件：core/tests/test_conditional_writes.py
- 先要有：结束写入口（端口新方法取代 try_finalize/expected_claim_count，两个 adapter）；update_job_state 新语义（run 已结束写不成、删回退写）；云端 STATE 的写入序号
- 必须同批：状态取法与结束写块：端口结束写入口与 update_job_state 改写（local 与 ddb 两个 adapter）；云端后端块：DynamoDBRunStore 写入序号（ddb 一侧用例断言序号条件）
- 单独先落地的后果：只改测试：改写后的用例对着旧 code 全红（旧 code 照写 job、发两次 update_item、没有新入口）。只改 code 不改测试：这 7 个用例和所有调 try_finalize 的用例红。
- 验证：单测够：本机文件锁与 moto 条件表达式两侧对拍都是 mock 之内的逻辑。DDB 一侧「一次写里区分 STATE 不存在与 run 已结束」若用 ReturnValuesOnConditionCheckFailure，要在真 DynamoDB 上核一次 moto 对它的模拟是否一致（并入测-2 的真表用例）。
- 备注：跟着「状态取法与结束写」块的结束写与 update_job_state 改动走，ddb 一侧另跟着「云端后端」块的写入序号走。7 个用例都存在，行号：177、214、611、904、588、927、445。线索没写的连带：①test_ddb_job_write_does_not_report_ended_on_a_run_created_between_its_two_writes（639 行）的前提是「先写一次、被挡再只写 job」，回退写删去后前提不在，应删去；②test_job_write_leaving_pending_advances_run_status 与 test_job_write_reports_the_run_still_open 的参数化里含 Status.SKIPPED，job 级 skipped 改为只由结束写写下，经 update_job_state 写 skipped 不再是合法输入，参数要收窄；③test_finalize_with_pending_jobs_succeeds、test_claim_rejected_on_finalized_run_leaves_state_unchanged 等用 try_finalize(status=ERROR) 造「带 pending 的已结束 run」，新入口下 pending 会被记成 skipped，期望的 job 态要改。0034「两端对拍口径」写明写入序号只在 moto 一侧对拍（本机靠锁内按整份运行态计算），所以序号的断言只放 ddb 一侧。ADR 0034 K1 列的现有用例（test_double_finalize_rejected 等）同样调 try_finalize，也在迁移范围里。

#### 测-2（test，M）

- 线索：补对拍用例，本机文件与 moto 两个 adapter 都覆盖
- 要做的：在 test_conditional_writes.py 新增两侧参数化用例：run 已结束时写 job 写不成、运行态不变（DDB 一次 update_item）；job 终态只写一次（第二次终态写不改记录、点名不变）；在 ddb 一侧新增：每次写序号加一、以序号为条件的终态写与结束写只在序号相等时写成、读之后落下的认领或投影挡住它。在 test_cloud_integration.py 新增真 DDB 用例：两个进程以同一序号并发写只有一方写成并使 run 成为终态，几百个 job（带点名标识的实际项大小）的结束写写成，只有一方生成报告。
- 文件：core/tests/test_conditional_writes.py、core/tests/test_cloud_integration.py
- 先要有：结束写入口；update_job_state 新语义；云端写入序号与 jobs 整体替换；JobState 带点名标识（判定明细块）；报告只由写成方生成（报告块，「只有一方生成报告」一条要用）
- 必须同批：moto 与本机部分：与测-1 同批（状态取法与结束写块的端口与 adapter 改动）；真 DDB 部分：云端后端块的 ddb.py 写入序号改动
- 单独先落地的后果：新用例对着旧 code 红（旧 code 照写 job、没有写入序号）。集成用例默认 deselect（-m 'not integration'），不影响默认测试，但不跑就没有证据。
- 验证：moto 与本机部分单测够。真 DDB 部分必须真实执行：并发写要两个真实进程打真表（不是 moto），几百个 job 的结束写要按实际 job 项大小（含点名标识）在真表上写，核写成与 400KB 边界；这些只用开发期自建的真表与 adapter/reconcile 代码，不需要重新部署（tools/ddb_capacity.py 可复用来测项大小与写入消耗）。「经 Lambda 的代码」指 Lambda 用的同一份 core 代码，不要求在 Lambda 里执行，拿不准时在重新部署之后再于云端核一次。
- 备注：跟着「状态取法与结束写」块（结束写、终态只写一次）与「云端后端」块（写入序号）走，点名标识跟「判定明细」块。线索说「写入序号……两个 adapter 都覆盖」，与 0034「两端对拍口径」不符：ADR 写明写入序号的对拍只在 moto 一侧，本机由锁内按整份运行态计算、不带序号，所以序号用例只写 ddb 一侧。0034 机制三②理由段里 1327 写成、1335 被拒的样本是未带点名标识时测的，点名标识会使上限下降，新用例要记下新的上限。

#### 测-3（test，S）

- 线索：K2 的三个测试改为断言报告从记录生成
- 要做的：三个用例改成：COMMITTED 之后报告由宿主从记录（运行态加被点名的明细）组装 RunResult 生成，不用 TickResult.result；事件在提交后再变、或另一推进方读到不同快照，报告里的判定仍等于记录里的终态与被点名的那一份明细。test_lambda_handlers 那一条改为断言 _tick_runs 收到 COMMITTED 后调用从记录组装的入口、传入这个 run 的报告落点。
- 文件：core/tests/test_reconcile.py、deploy_aws/tests/test_lambda_handlers.py
- 先要有：报告块：finalize_report 改为从记录组装，TickResult 不再带 result；判定明细块：按点名标识读明细
- 必须同批：报告块对 reconcile.finalize_report、TickResult、detached.run_reconcile_loop 与 reconciler._tick_runs 的改动
- 单独先落地的后果：只改测试：旧 code 仍用 done.result 生成报告，改写后的断言红。只改 code：这三条（以及 TickResult.__post_init__ 要求 COMMITTED 带 result 的各处用例）红。
- 验证：单测够（报告组装是纯逻辑）。批级另做一次真实执行：本机 submit 一个 run 到结束，核 index.html 与 status --json 的状态和判定一致（0054 实测项 1、2、4）。
- 备注：跟着「报告」块走，读明细一侧跟「判定明细」块。三个用例都存在（test_reconcile.py 477、492 行；test_lambda_handlers.py 856 行）。疑点：①test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots 在本机 LocalRunStore 上造两个推进方，并用 SqliteEventLog.record_timed_out_if_absent（接力补写）造 B 的快照；新设计下本机只有一个推进器，这条要么改到 DDB 一侧（test_cloud_reconcile），要么换掉造快照的手段，不能只改断言。②ADR 0034 K2 列的现有用例与线索不同：test_commit_lost_to_another_advancer_ends_without_a_result、runtime 的 test_loop_ends_without_report_when_its_commit_is_lost 与 test_loop_does_not_rewrite_the_report_of_a_committed_run、test_tick_runs_branches_on_tick_outcome；TickResult 不再带 result 时它们也要改，线索没有列。

#### 测-4（test，M）

- 线索：机制三删去的测试项对应的测试删或改
- 要做的：删去本机的 test_expiry_loses_to_a_claim_that_landed_after_the_read（本机锁内的结束写会把新认领的 job 记 aborted、结束 run，竞态不再成立）；云端的同名 _on_ddb 用例保留，文档串改成「被写入序号的条件挡下」，换掉「推进方」「收尾写」「到期收尾」；test_all_done_after_the_deadline_aggregates_without_the_claim_count_condition 改为：全部 job 已有结果时不做结束写，run 随最后一个 job 的终态写按取法成为终态。另删已不成立的「已结束 run 上 job 写照样写成」与本机多推进器的用例。
- 文件：core/tests/test_reconcile.py、core/tests/test_cloud_reconcile.py、core/tests/test_cloud_integration.py
- 先要有：后台推进逐 job 写序（tick 改写：已有结果的 job 先存明细再记终态，结束动作只剩到期结束写）；结束写入口；云端写入序号
- 必须同批：状态取法与结束写块对 reconcile.tick、_finalize、_claim_times 与 project.plan_next 的改动；云端用例另与云端后端块的写入序号同批
- 单独先落地的后果：只删本机竞态用例而 code 不动：无害（少一条用例）。code 改了而测试不动：_SpyRunStore.try_finalize 的覆写与 finalize_counts 断言在本文件多处变红（不止线索列的两条）。
- 验证：本机与 moto 单测够。云端竞态（0054 实测项 7）要在重新部署之后用真实云端 run 核：一个推进器读到「没有执行中、仍有未启动」之后另一方的认领落下，结束写被序号挡下、run 没有结束，并记下新认领的 job 怎样结束。
- 备注：跟着「状态取法与结束写」块（tick 写序、结束写）走，云端一半跟「云端后端」块（写入序号）走，所以本条本身会分到两批。线索说的「第 2 项的云端一半、第 4 项的后半、第 5 项的本机多推进器」指 0034 机制三旧实测项；ADR 那一侧已经改过，线索没有点名对应的测试。我找到的对应项：第 4 项后半就是 core/tests/test_cloud_integration.py 的 test_ddb_job_write_on_finalized_run_lands_job_only_real（151 行，真 DDB 上断言已结束 run 照写 job）；第 5 项的本机多推进器可能指 test_conditional_writes.py 710 行真 DDB 用例文档串里「对位 per-run 进程与 status --wait 接力者」的说法（它在 DDB 上仍成立，只需改文档串）；第 2 项的云端一半没有找到自动化用例。_SpyRunStore（test_reconcile.py 186 行）覆写 try_finalize，整个「到期处理」一节（test_past_stop_start_claims_nothing_and_expires_the_run 等）都靠它与 finalize_counts，要整体改写，见 missing。

#### 测-5（test，M）

- 线索：终止对拍矩阵去掉接力补写，加上期限截断与预算截断的分行
- 要做的：MATRIX 去掉（或改名）「接力者直接落 timed_out（退出码未知）」一行；test_paths_agree_when_the_run_deadline_cuts_the_job 的期望改为：期限截断而内容不完整的 job 为 aborted、没有 error_type，预算截断仍为 error 加 timeout，两种截止时刻相等时按预算算；到期用例改为后台运行态里 b 由结束写记 skipped、run 状态按取法为 aborted，不再比较 jobs_without_verdict。
- 文件：core/tests/test_termination_parity.py
- 先要有：终结函数 timeout 一行拆成两行（project.finalize_job、run_deadline.job_cutoff）；结束写把 pending 记 skipped；前台不再构造 skipped 的 JobResult；run 状态取法
- 必须同批：状态取法与结束写块对 finalize_job、DEADLINE_TIMEOUT_MESSAGE、schedule 与 RunPersistence.finalize 的改动
- 单独先落地的后果：终结函数改了而矩阵不动：期限截断各行的 error/timeout 断言与 startswith(DEADLINE_TIMEOUT_MESSAGE) 红，到期用例的 ERROR 与 b pending 断言红。
- 验证：矩阵本身单测够（两条路径都是纯函数或 FakeEngine）。它守的结论依赖真实执行，批级要核 0054 实测项 4（三种组合各一个期限落在执行中途的 run，status --json 与 explain 一致）与实测项 11 本机一侧（真实进程在截止时刻之后自行退出）；云端一侧要等重新部署。
- 备注：跟着「状态取法与结束写」块（终结函数、结束写、前台不构造 skipped）走。疑点：「接力补写」这一行的输入（退出码未知、带超时标志、没有退出时刻）在新设计下仍会出现：云端 job 到点停止找不到 task 时经 DdbEventLog.record_timed_out_if_absent 补写（0054 实测项 12），所以这一行宜改名为云端补写的情形、保留，而不是删；test_crash_row_sync_side_really_exits_with_unknown_code 与 test_matrix_covers_expected_verdicts 按行名取这一行，要一起改。到期用例里 background = done.result 也受报告块 TickResult 不带 result 的影响。

#### 测-6（mixed，M）

- 线索：run_verdict 与按原因优先序的用例删改
- 要做的：删去 test_project.py「run 级裁决」一节（run_verdict/RunVerdict 的 import 与 7 个用例）与 test_project_full_run_level_comes_from_the_shared_verdict，换成新取法函数的真值表用例；test_schedule.py 的两条中断用例改为按取法断言（a aborted、b 由结束写记 skipped 时 run 为 aborted），删去两节分节注释里的「run 级裁决」；test_lifecycle_states.py 删去 _NON_VERDICT 断言；两条 plan_next 用例把「未启动」改为按运行态的 pending 判断；按「0031 决定三」核对 model.py `_NON_VERDICT` 上方注释与 project.py `_aggregate` 文档串里指向过滤名单与空判定集规则的说法。
- 文件：core/tests/test_project.py、core/tests/test_schedule.py、core/tests/test_lifecycle_states.py、core/tests/test_conditional_writes.py、core/tests/test_reconcile.py、core/gherkai_core/model.py、core/gherkai_core/project.py
- 先要有：删去 run_verdict、RunVerdict、_NON_VERDICT，新增 run 状态取法函数；plan_next 按运行态的 pending 判断未启动
- 必须同批：状态取法与结束写块删 run_verdict 与新取法、改 project_full 与 schedule 的那一批
- 单独先落地的后果：code 先删 run_verdict/RunVerdict：test_project.py 第 28 行的 import 失败，整个模块收集出错；test_lifecycle_states.py 导入 _NON_VERDICT 同样失败。测试先改：新取法函数不存在，新用例红。
- 验证：单测够（取法与 plan_next 都是纯函数）。
- 备注：跟着「状态取法与结束写」块（删 run_verdict、新取法、plan_next 的未启动判据）走。所列符号都存在（test_schedule.py 1674、2494 行；test_project.py 392 行起的一节、477、626、646 行；test_lifecycle_states.py 16、63、83 至 85 行）。疑点：①test_user_interrupt_with_passed_and_aborted_marks_run_aborted 在新取法下照样得 aborted（a aborted、b passed 时取法给 aborted），可以保留、只改文档串，不必删。②test_interrupt_then_past_stop_start_reports_the_deadline_over_aborted 的新期望取决于结束写取哪一个来路的说明（中断还是到期），journey「写回时留下、实装之前要定的问题」里这一条还没有定，这条用例在它定下之前写不完。③plan_next 按运行态判断未启动，签名可能要求 baseline 必给，test_project 里调 _plan 不带 baseline 的用例都受影响。test_project.py 另有「投影写的 run 级 status」一节（projected_run_status，文档串写「终态归 finalize」），线索没有列，见 missing。

#### 测-8（test，S）

- 线索：core/tests/test_status_group.py 模块文档串与 test_create_derives_group_from_the_initial_status
- 要做的：二选一：模块文档串与用例文档串写明「传入终态初始状态」是派生函数在函数层的性质，不出自 0030 决定六；或把 test_create_derives_group_from_the_initial_status 的参数化从 list(Status) 收窄为 PENDING，文档串里的终态一句删去。
- 文件：core/tests/test_status_group.py
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无（只改文档串或收窄参数，现有 code 照样通过）
- 验证：单测够。
- 备注：本身不依赖 code 改动，宜放进「云端后端」块改 runs 表写法（status_group 只在使 run 成为终态的那次写里换值）的那一批，同一文件里调 try_finalize 的 10 处届时也要迁到结束写入口（见 missing）。用例在 86 行，参数化为 list(Status)；模块文档串第 3 行写「含 create_run 传入终态初始状态的情形」。

#### 测-9（mixed，S）

- 线索：0053 键集差集护栏：排除名单加 settle-runs 的 --dry-run
- 要做的：test_project_config.py：PER_CALL 加 --dry-run；文档串「八个读配置命令」改为九个。code 一侧同批改 settings.py：CONFIG_COMMANDS 加 settle-runs、PER_CALL_OPTIONS 加 dry_run。（CLOUD 去掉四个键与 grace 用例已随「云端只支持 submit」那一批做完。）
- 文件：cli/tests/test_project_config.py、cli/gherkai_cli/settings.py
- 先要有：settle-runs 子命令的解析器（run 处置块）
- 必须同批：与 settle-runs 解析器同一批
- 单独先落地的后果：settle-runs 上了而名单不改：差集用例报 --dry-run 未归类（PER_CALL_OPTIONS 不改时它还会被算进 [common]，keys[common] 与 COMMON 不等），变红。
- 验证：单测够（argparse 差集）。
- 备注：跟「run 处置」块走。依据核过：0053 第 22 行已把 settle-runs 列进读配置的命令，第 67 行已把 settle-runs 的 --dry-run 列进按次选择型。线索没写的连带：COMMON 里的 --tunnel-ttl 与 test_config_errors_exit_2_naming_file_section_and_key 参数里「tunnel-ttl = 'x'」一行要随隧道块删去；同一文件 test_local_relay_host_reads_definition_not_the_config_file（接力宿主）也要删改，见 missing。

#### 测-10（test，M）

- 线索：部署模板测试：删 test_ssm_params_with_prefix_path
- 要做的：test_stack.py：test_exit_observer_can_read_runs_table_only 改为观察者对 runs 表没有任何权限；test_kicker_mapping_insert_filter 改为两条过滤（INSERT 且 item_type 为 STATE；新映像 status_group 不是 live 的 STATE）。（删 SSM 子网与安全组参数那一半已随「云端只支持 submit」那一批做完。）
- 文件：deploy_aws/tests/test_stack.py
- 先要有：exit-observer 不读 runs 表、删 RUNS_TABLE（云端后端块）；kicker 流过滤改两条（云端后端块）
- 必须同批：云端后端块里改 stack.py 的各项，宜集中在同一个需要重新部署的批次
- 单独先落地的后果：测试先改：对旧模板红。
- 验证：模板形态用 CDK synth 的单测够。真实行为要在 owner 重新部署之后核：流上只有 STATE 新建与使 run 成为终态的写触发 kicker（0054 实测项 21）；「云端只支持 submit」那一批删掉的两个 SSM 参数在这次重新部署时才真被 CloudFormation 删去，之后 submit、doctor 照常可用。
- 备注：跟着「云端后端」块（kicker 过滤、观察者权限）走。线索没写的连带：kicker 收到 STATE 新建时建两次一次性定时触发、结束即清扫，需要新的模板断言（Scheduler 资源或权限域、推进 Lambda 角色上 ecs:ListTasks、ecs:StopTask、scheduler:CreateSchedule 与给 Scheduler 的 iam:PassRole），test_reconciler_and_kicker_have_the_same_permission_face（989 行）也可能随之改；名字形态与资源域在 journey 里标为待定，这些断言要等它定下。见 missing。

#### 测-11（test，L）

- 线索：前台云端 run 的测试删改：cli/tests/test_backend_cloud.py
- 要做的：test_backend_cloud.py：删 status --wait kickoff 用例（test_status_wait_cloud_kicker_missing_fails_fast 等）。（前台云端 run 用例的删改与改用 submit 重写、test_compose.py 的 resolve_network 各条已随「云端只支持 submit」那一批做完。）
- 文件：cli/tests/test_backend_cloud.py
- 先要有：删 _status_cloud 的卡住检测与 kickoff、compose._make_lambda_client（run 处置块）
- 必须同批：与删 _STALL_KICK 同批，而那一批按次序约束要与后端到期结束（kicker 建两次定时触发）同批或在其后
- 单独先落地的后果：kickoff 删了而测试不动：test_status_wait_cloud_kicker_missing_fails_fast 打桩 compose._make_lambda_client 失败。
- 验证：CLI 形态单测够。云端真实验证要在重新部署之后：submit --backend cloud 加 status --wait 走到终态、不 invoke kicker。
- 备注：跟着「run 处置」块（删 status --wait 的 kickoff）走。线索没写的连带：本文件按 detached 标记决定接力或提示的三条 status 用例（test_status_wait_cloud_only_waits_for_a_run_that_is_not_detached 等），见 missing。

#### 测-12（test，M）

- 线索：接力与 handler 分流的测试随 code 删
- 要做的：删 test_detached_launcher.py 的三条接力用例与「启动器记下退出时刻……接力的判定条件与条件补写」一节里只测接力的用例（含 test_relay_writes_only_once_the_wall_clock_is_strictly_past_the_cutoff_plus_ten_seconds、test_relay_leaves_its_own_jobs_and_jobs_without_a_readable_claim_time）；test_definition_schema.py 那条的 status --wait 参数删去，_reconcile 参数改为断言后台推进进程以结束写的 error 变体结束 run；删 test_lambda_handlers.py「只推进 detached run」一节；test_sqlite_event_log.py 的那条按 EventLog 端口的定法删或留。
- 文件：runtime/tests/test_detached_launcher.py、cli/tests/test_definition_schema.py、deploy_aws/tests/test_lambda_handlers.py、core/tests/test_sqlite_event_log.py
- 先要有：删本机接力（本机推进器块：_cmd_status_body 不进推进循环、删 _recover_timed_out_claims 等）；handler 不按 detached 分流（云端后端块）；运行定义不可用时后台推进进程做结束写的 error 变体（状态取法与结束写块）；EventLog 端口里 record_timed_out_if_absent 的去留
- 必须同批：本机部分：与删本机接力同批，而它按次序约束要与生命期锁、run 处置同批或在其后；云端部分：与 reconciler._build、exit_observer._is_detached 的删除同批（需要重新部署）
- 单独先落地的后果：本机接力删了而测试不动：三条接力用例与 test_definition_schema 的 status --wait 参数红（status --wait 不再处理违约记录、不返回 2）。分流删了而测试不动：test_reconciler_noop_for_non_detached_run 等断言非 detached 零动作的用例红。
- 验证：单测够的部分：用例删改本身。接力取消之后能不能结束推进进程已死的 run，依赖真实进程与文件锁，要在本机真实执行：后台推进进程被 SIGKILL 后 status --wait 下一次轮询即处置（0054 实测项 16）；云端分流去掉之后在重新部署后核 kicker 只被 STATE 新建与终态写触发（实测项 21）。
- 备注：本机部分跟「本机推进器与锁」块（删接力）走，云端部分跟「云端后端」块（handler 不分流）走，拆到两批。所列用例都存在（131、653、951 行；test_definition_schema.py 142 行；test_lambda_handlers.py 877 行一节；test_sqlite_event_log.py 120 行）。疑点：①EventLog 端口的 record_timed_out_if_absent 云端仍在用（reconciler._handle_timeout 找不到 task 时补写，0054 实测项 12），端口方法要留；只是 SqliteEventLog 在本机没有调用方，要么留作端口实现，要么端口拆开，这决定 test_sqlite_event_log 那条删不删。②test_definition_schema 的 _reconcile 参数在新设计下不再是「以 2 结束、运行态不动」，而是 run 记 error（0031 决定三「运行定义不可用时」、0054 实测项 23），要改写而不是删。线索没写的连带：test_lambda_handlers.py 的 test_kicker_timeout_path_skips_tick_when_not_detached（767 行）、test_exit_observer_skips_non_detached_run 与 test_exit_observer_records_exit_for_detached_run（1174、1182 行，在「并发上限」一节之后，不在线索点名的那一节里）、全文件 _seed_run(detached=...) 的参数；cli/tests/test_main.py 3339、3392、3879 行的三条接力用例。见 missing。

## 隧道（0035）与两种 `submit` 的新流程

### 小结

整体改动量：约 3 个 L、1 个 M、2 个 S，跨 runtime 与 cli 两个包，另有三份 pyproject 与 uv.lock；code 在 1000 行上下，受影响的测试约 30 个以上。全部在本机一侧，不涉及 Lambda、部署模板与 runs 表写法，不需要重新部署。云端 submit 的真实验证用现有部署即可；若与云端块同期，重新部署之后再核一次。

能不能把「隧道改用 SDK」与「本机 submit 由后台推进进程建 run」分成两批：能，但只能按「先流程、后 SDK」的次序，反过来不行。
- SDK 的会话建在起它的进程里。现在两种 submit 都由 submit 进程起隧道、再按 pid 交给后台：先换 SDK 的话，submit 一退出隧道就没了，两种 submit 带 --expose-local 的 run 全部失败。
- 先改流程时，后台推进进程或守护进程可以照用现有的 start_tunnel_for_jobs（ngrok 可执行文件），在自己的收尾里 stop_tunnel(info.pid)。产品可用，过渡用的 code 只有几十行。
- 代价：宿主被 SIGKILL 时代理照旧泄漏；tunnel.json 若在第一批就删，接力也拆不了它。可以把到点拒绝规则放进第一批，ngrok 可执行文件对它的实测已在 ADR 0035 里，这样泄漏的公网入口至少在期限加 300 秒时由边缘关闭。

建议的分法：
- 第一批：「本机 submit 由后台推进进程建 run」（隧道-2，与锁块的「生命期锁」线索是同一个改动），放进生命期锁与 run 处置那一批。
- 第二批：SDK（隧道-1）加云端 submit 的新流程（隧道-3），连同 --tunnel-ttl 的删除与讲隧道的全部文档。这样守护进程只重写一次，直接写成 SDK 版。
- 隧道-6 跟着两批分两次删；隧道-4 与隧道-5 随各自的 code 走。

内部次序：missing 第 1、2 条（_build_run_meta 收创建时刻、run_requires_backend_stamp 改签名）先做或与第一批同做；然后隧道-2；然后隧道-1 与隧道-3。

可选依赖 [tunnel] 要改的文件：
- runtime/pyproject.toml 与 cli/pyproject.toml：都写在 [tool.hatch.metadata.hooks.uv-dynamic-versioning] 表的 optional-dependencies 里（dynamic 元数据，不在 [project] 表）。
- 根 pyproject.toml：dependencies 宜改为 gherkai[local,deploy-aws,tunnel]，开发 venv 与跳板机的真实执行才有 SDK。
- uv.lock：CI 执行 uv sync --locked，必须在同一提交里重新生成，要联网执行 uv lock。

对别的块的依赖：
- 隧道-2 依赖或必须与锁块同批（后台进程建 run 时取锁）。它报错里的 settle-runs 提示要求处置块的 settle-runs 已经存在。它的 reconcile.log 说法与 4a 流程块的文档也与删接力相关。
- 隧道-3 的守护进程判断终态，用状态取法块之后的 load_run_state。

最大的风险都在 mock 之外，单测给不了证据，必须真实执行：
- SDK 的调用不带时限，timeout_s 怎样截住它没有核过（ADR 0035 实测项 12）。
- 回报管道「对端已关闭」的检测在 macOS 与 Linux 上不同（实测项 4）。
- SDK 与推进循环、读事件线程长期共存（实测项 13）。
- 大量 submit 单测假定 submit 自己落库，要把测试接缝移到「启动后台推进进程」这一处，改写量容易低估。

### 线索没有覆盖的改动点

- 前台 run 与运行定义的次序：ADR 0035 决策 3「前台 run」与 0054 决策二「落点是运行定义」要求先取创建时刻、算期限，再起隧道（起隧道要用到点时刻），然后生成运行定义。现在 cli/gherkai_cli/__main__.py 的 _cmd_run 先 _setup_tunnel 再 _build_run_meta，而 _build_run_meta 内部自己 compose.now_iso() 取 created_at。要把 _build_run_meta 改为收调用方给的 created_at（云端还要合入 _worker_meta_fields），让 _cmd_run 与两种 submit 在起隧道之前取时刻；_cmd_run 里的 atexit.register(stop_tunnel, tunnel_info.pid) 改为注册关闭会话，上方「可手动结束来兜底」的注释随之改。这一块的线索只写了两种 submit，没写前台 run。
- compose.run_requires_backend_stamp(meta) 改签名（runtime/gherkai_runtime/compose.py；调用处在 cli/gherkai_cli/__main__.py 的 _submit_cloud 与 _cloud_skew_gate）：它现在看 RunMeta.session_warmup_url。按 ADR 0035 决策 3「云端 submit」，各道闸在生成运行定义之前执行，所需的「有没有隧道」从有没有给 --expose-local 取；0037 决策 7 的缺戳例外同样写明在生成运行定义之前判断。要改成收 jobs 加一个是否给了 --expose-local 的布尔值，前台 run 与测试里的调用同步改。
- 根 pyproject.toml 与 uv.lock：线索只写了 runtime 与 cli 两份 pyproject。根 pyproject 的 dependencies 现为 gherkai[local,deploy-aws]，不加 tunnel 的话，开发 venv 与跳板机上执行 uv run gherkai --expose-local 都没有 SDK；uv.lock 不重新生成，CI 的 uv sync --locked 会失败。依据 ADR 0037 决策 2c「[tunnel] 的语义」与 CONTRIBUTING 的单 lock 约定。
- _cmd_tunnel_watch 的信号处理（cli/gherkai_cli/__main__.py）：它现在把 SIGTERM 与 SIGHUP 转成 SystemExit，好在 finally 里按 pid 拆隧道。ADR 0035 决策 3「云端 submit」最后一条要求守护进程对 SIGTERM、SIGHUP 取缺省处置、不转成退出。SDK 落地时要删掉这个处理器连同它的文档串，线索的隧道-3 没写这一点（注释块只提到了文档串里的「可手动结束」）。
- 守护进程轮询时读不出或读不到这个 run 要记一句（runtime/gherkai_runtime/tunnel_host.py watch_run_and_stop_tunnel）：现在 state 为 None 时静默继续，只有抛异常才经 on_warn 报一句；到点判断现在用 time.monotonic 计 TTL，ADR 要求按墙钟到期限加 300 秒（0035 决策 3「云端 submit」，0054 决策二「检查用墙钟」）。线索只写了「轮询 run 的状态，到终态或到运行期限加 300 秒时退出」，没写这两处与现状的差别。

### 逐条

#### 隧道-1（mixed，L）

- 线索：隧道改用 ngrok 官方 Python SDK，建在宿主进程里，不再启动 ngrok 可执行文件
- 要做的：重写 tunnel.py 的 NgrokTunnel：start 不再 mkstemp 日志与策略文件、不再 Popen ngrok，改为在宿主进程里懒导入 ngrok SDK、把 render_traffic_policy 生成的策略字符串在内存里交给 SDK 的建立监听调用，令牌只取 NGROK_AUTHTOKEN；start 增收到点时刻参数，render_traffic_policy 在最前面插入到点拒绝规则（timestamp(time.now) >= timestamp('<期限+300s>') → 403），规则数恰为 POLICY_RULE_LIMIT=5。TunnelInfo 去掉 pid，返回对象带关闭会话的方法；删 stop_tunnel、_launch、_remove_quietly；启动失败按四种原因给 TunnelError（3 = 错误里带 ERR_NGROK_334，4 = 其余带 SDK 原因）。另加前置检查函数（SDK 可发现、NGROK_AUTHTOKEN 已设，不导入 SDK），由 __main__._plan_and_preflight 在给了 --expose-local 时调用，缺即退出码 2；runtime/cli 两份 pyproject 加 [tunnel] extra。
- 文件：runtime/gherkai_runtime/tunnel.py、runtime/gherkai_runtime/tunnel_host.py、cli/gherkai_cli/__main__.py、runtime/pyproject.toml、cli/pyproject.toml、pyproject.toml、uv.lock、runtime/tests/test_tunnel.py、cli/tests/test_tunnel_cli.py
- 先要有：本机 submit 由后台推进进程起隧道并建 run（隧道-2）；云端 submit 由隧道守护进程自己起隧道（隧道-3）；宿主在起隧道之前就取得创建时刻与期限（见 missing 第 1 条，前台 run 的次序调整）
- 必须同批：隧道-5 里 tunnel.py 启动失败的四种说法与 --expose-local help 的前置文字；uv.lock 重新生成（CI 用 uv sync --locked，pyproject 的 extra 变了而锁文件没变即失败）；行为文档块里讲隧道前置条件的各处：用户指南、skill、evals.json、CHANGELOG、runtime/DEVELOPMENT.md 的 tunnel.py 一条
- 单独先落地的后果：只换 SDK 而两种 submit 的流程不改时，submit 进程自己起隧道然后退出，隧道随 submit 进程一起消失：本机与云端 submit 带 --expose-local 的 run 全部导航失败。另外 _submit_local 的 write_tunnel_file、_submit_cloud 的 --tunnel-pid、_cmd_run 与 _cmd_submit 里的 stop_tunnel(tunnel_info.pid) 都读 pid，会抛 AttributeError 或 ImportError；test_tunnel.py 里的 NgrokTunnel 一节（_FakeProc、spawn、策略文件、进程组、stop_tunnel 幂等）与 test_tunnel_cli.py 里的 handoff 用例都会变红。只有前台 run 单独切到 SDK 是成立的。
- 验证：单测只能覆盖策略文本（5 条规则、到点规则在最前、时刻取值）、四种说法的分类（用假 SDK 抛错）、前置检查与懒导入（没给 --expose-local 时 ngrok 不进 sys.modules）。其余结论都靠真实的 SDK 与 ngrok 边缘，单测不算证据：要用真实 ngrok 账号（新注册与较早注册两种）在 macOS 与 Linux 上，按 ADR 0035「实测项」1、2、8、9、10、11、12、13 真实执行。包括前台 run、run --no-report 起隧道并执行通过；宿主被 SIGKILL 之后公网一侧不在线、没有残留进程；到点之后带 cookie 与预热的请求都答 403；新注册账号上第二条隧道得到 ERR_NGROK_334 的第 3 种说法；没装 SDK 或没设令牌时三种组合各一次；断网时 timeout_s 能不能截住 SDK 调用。装包另核：在干净 venv 里 uv pip install 'gherkai[tunnel]' 能解析，并装上 ngrok>=1.8.0。
- 备注：code 现状：tunnel.py 现在的实现是起 ngrok 可执行文件，再轮询 JSON 日志文件拿公网地址，策略写进 0600 的临时 yml；POLICY_RULE_LIMIT=5，注释写「四条规则留一条余量」，_POLICY_TEMPLATE 只有 4 条规则。TunnelInfo 带 pid，TunnelProvider 的形状仍是 start(local_origin, *, timeout_s)，没有到点时刻，也没有关闭方法。线索的「位置」只点了 NgrokTunnel 与 POLICY_RULE_LIMIT，没点到这些也要一起改的接口：TunnelInfo.pid、stop_tunnel（__main__ 里有 3 处调用，detached.cleanup_tunnel、tunnel_host.watch_run_and_stop_tunnel 各 1 处）、tunnel_host.start_tunnel_for_jobs 的签名（要把到点时刻传下去），以及 TunnelSetup.info 的文档串。
  pyproject 的写法：两个包的 optional-dependencies 都写在 [tool.hatch.metadata.hooks.uv-dynamic-versioning] 表里（dynamic 元数据），不在 [project] 表。runtime 写成 optional-dependencies = { aws = [...], tunnel = ["ngrok>=1.8.0"] }；cli 写成 { local = [...], deploy-aws = [...], tunnel = ["gherkai-runtime[tunnel]=={{ version }}"] }。
  根 pyproject.toml 的 dependencies 现在是 ["gherkai[local,deploy-aws]"]。要让开发 venv 与跳板机的 uv run gherkai 真有 SDK 可用，宜改成 gherkai[local,deploy-aws,tunnel]。这样单测环境里也装着 ngrok，「没装 SDK」那条用例要靠打桩 importlib 的发现函数来模拟。
  uv.lock 要在有网的环境里执行 uv lock 重新生成（会新增 ngrok 包条目；gherkai 与 gherkai-runtime 的 provides-extras 与 requires-dist 也会变），和 pyproject 放在同一提交。本次只读，没有执行。
  拿不准的地方：ngrok SDK 1.8.0 的确切函数名与参数名（forward、traffic_policy、authtoken_from_env，关闭是同步还是协程），我没有导入核对，实装时以 1.8.0 的类型声明为准。ADR 0035 实测项 12 写明 SDK 调用本身不带时限，timeout_s 怎样截住它（例如放进线程按时限 join，超时后补一次关闭）没有定、也没有核过，是这一条最大的不确定点。

#### 隧道-2（mixed，L）

- 线索：本机 `submit`：做完计划与补全运行定义之后，以新会话启动后台推进进程
- 要做的：_cmd_submit 的本机分支在 _complete_local_definition 之后不再起隧道、不再 _build_run_meta、不再 create_run。_submit_local 改为：把建 run 所需的输入（job_to_dict 序列化的 jobs、steps_dir、max_concurrency、每 job 尾段、cli_version、--expose-local 的 origin 与 provider、解析后的 region/profile、报告目录）一次写进后台推进进程的 stdin，另建一条回报管道经 pass_fds 交给它，以 start_new_session 启动，然后阻塞读回报：建成时输出进度行，stdout 只打 run_id，退出码 0；没建成时报原因、以回报里的退出码结束；管道关闭而没有回报时报错、退出码 2，并提示可用 settle-runs。detached.py 新增后台推进进程一侧的建 run 入口，次序是：取创建时刻、算期限、起隧道并映射 jobs、生成 RunMeta（新 run_id）、建 run（边界检查与取锁属锁块）、建事件库、建 run 之前查一次回报管道（对端已关即不建、退出）、回报并关闭管道、把 stdout/stderr 改接到 run 目录的 reconcile.log，之后进入 run_reconcile_loop，正常结束时先关闭隧道会话。_cmd_reconcile 与 _reconcile 子命令的参数（现在是 run_id 位置参数加 --report-dir 等）随之改为读 stdin 与回报 fd。
- 文件：cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/detached.py、cli/tests/test_main.py、cli/tests/test_project_config.py、cli/tests/test_tunnel_cli.py、runtime/tests/test_detached_launcher.py、docs/internals/execution-and-reconciliation.md、docs/user-guide/running-and-results.md、docs/internals/artifacts-and-evidence.md
- 先要有：_build_run_meta 能接收外部给的创建时刻（见 missing 第 1 条）
- 必须同批：锁块的「生命期锁」线索：它与本条写的是同一个改动，后台推进进程建 run 时取锁，submit 不拿锁。锁若晚于本条落地，只是暂时不取锁；锁若先落地而本条没落地，就只能先由 submit 建 run 再交给后台进程，这正是 0054 的被拒方案；隧道-6 的本机一半：_submit_local 不再接 tunnel_info/on_handoff，_cmd_submit 的 finally 就地拆隧道对本机失去意义；隧道-5 的本机进度行（删去 pid 与 tunnel.json、删去「终态即拆」）；CLI 用户可见文字里的 settle-runs 提示要求 settle-runs 命令已经存在（处置块）；早于处置块落地时这句要临时改写
- 单独先落地的后果：只落这一条而隧道仍用 ngrok 可执行文件时，产品可用：后台推进进程调用现有的 start_tunnel_for_jobs，再在自己的收尾里 stop_tunnel(info.pid)。代价是后台进程被 SIGKILL 时 ngrok 代理留在公网；如果同时不再写 tunnel.json，接力（status --wait）也拆不了它，直到 SDK 那一批落地。测试方面：test_main.py（约 13 处 submit 调用、12 处打桩 Popen，多处断言 submit 写出的 run_meta.json 或 run_state.json，如 detached 标记、max_concurrency、steps_dir、期限偏移）、test_project_config.py（3 处 Popen）、test_tunnel_cli.py 的 test_submit_local_* 都假定 submit 自己落库，要改成经后台进程一侧的建 run 入口在进程内执行，否则全红。
- 验证：单测可以覆盖：stdin 载荷的序列化往返、回报的三种结果怎样映射到 submit 的输出与退出码、建 run 之前对端已关就不建 run。测试接缝放在「启动后台推进进程」这一处，不为测试扭曲生产接口。但回报管道、新会话、Ctrl-C、强杀、文件描述符继承都是 mock 之外的真实行为，单测不算证据：要在 macOS 与 Linux 上用真实进程执行 ADR 0035 实测项 3（建成、起隧道失败、报告目录不合要求各一次）、实测项 4（submit 在后台进程查回报管道之前与之后被强杀各一次，并记下两个平台上怎样查到对端已关闭）、实测项 5（后台进程在回报之前被强杀），以及 ADR 0054 实测项 15（自建立起锁就在后台推进进程手里）。用 tools/ 里没有现成的工具，直接经 CLI 真实提交。
- 备注：code 现状：_submit_local 现在由 submit 自己 build_local_stores(detached=True)、create_run、建 SqliteEventLog、写 tunnel.json，再 Popen [python -m gherkai_cli _reconcile <run_id> --report-dir … --max-concurrency … --region/--profile]，stdin 接 DEVNULL，stdout 与 stderr 一开始就接 reconcile.log；之后 on_handoff()，打印并 print(run_id)。RunMeta 在 _cmd_submit 里起隧道之后经 _build_run_meta 生成，created_at 在起隧道之后才取，与 ADR 0054 决策二「创建时刻在起隧道之前取」相反。
  这条线索与锁块的「生命期锁」线索几乎逐字重复（submit 不拿锁、新会话、stdin、回报管道、次序），是同一个改动，分批时必须放在同一批，不能算两次工作量。
  线索没写的连带改动：
  - 后台进程在回报之前的 stdout 不能接到 submit 的 stdout 上（submit 的 stdout 只放 run_id），宜接 stderr 或 DEVNULL；回报之后用 dup2 把 1 与 2 改接到 reconcile.log，之后起的 worker 继承的才是日志文件。
  - 「建 run 之前查一次回报管道对端是否已关」：写端在读端关闭之后的可见性（poll 的 POLLERR/POLLHUP）在 macOS 与 Linux 上不同，实测项 4 要求记下，宜考虑改用 socketpair。
  - run_id 改由后台进程生成，现有 _status_cmd 提示与进度行都在收到回报之后才打。
  - build_local_reconcile 现在从 store 读回 meta：接力仍在时它照用；本条可以直接把内存里的 meta 交给推进循环，但 status --wait 接力（删接力那一条）仍要用读回的版本。
  - write_tunnel_file 与 cleanup_tunnel、drive_local_reconcile 末尾的拆隧道：SDK 落地时删去；若本条先于 SDK 落地，后台进程自己按 pid 收尾。

#### 隧道-3（mixed，L）

- 线索：云端 `submit`：先过云端各道闸并补全运行定义，取创建时刻、算出运行期限
- 要做的：_submit_cloud 的次序改为：target、skew 闸、资源 preflight、variant 闸、_complete_cloud_definition，都只用 jobs 与「有没有给 --expose-local」，不再收已建好的 run_meta；然后取创建时刻、算期限，给了 --expose-local 时以新会话启动 _tunnel_watch，经 stdin 与回报管道交互：把到点时刻（期限加 300 秒）、origin、provider、runs 表、region/profile 交给它，读回公网地址与预热地址后映射 jobs；生成 RunMeta（合入 _worker_meta_fields），建 run 之前查一次管道（守护进程一端已关即退出码 2），create_run，再把 run_id 写给守护进程（写不进去时照常输出、退出码 0，另在 stderr 说明隧道已不在）。tunnel_host 删去 CLOUD_STARTUP_MARGIN_S、CLOUD_PER_JOB_MARGIN_S、compute_watch_ttl_s，watch_run_and_stop_tunnel 改为守护进程主体：起隧道、回报、等 run_id、把日志改接到系统临时目录的 gherkai-tunnel-watch-<run_id>.log、按墙钟轮询 run 状态，到终态或到点时刻关闭会话并退出。删去 submit 的 --tunnel-ttl，以及 _tunnel_watch 的 --tunnel-pid、--ttl。
- 文件：cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/tunnel_host.py、runtime/gherkai_runtime/deadline.py、runtime/gherkai_runtime/compose.py、cli/gherkai_cli/settings.py、cli/tests/test_backend_cloud.py、cli/tests/test_tunnel_cli.py、cli/tests/test_project_config.py、runtime/tests/test_tunnel_host.py、runtime/tests/test_deadline.py
- 先要有：_build_run_meta 能接收外部给的创建时刻，并合入 worker variant 字段（见 missing 第 1 条）；compose.run_requires_backend_stamp 不再依赖 RunMeta（见 missing 第 2 条）
- 必须同批：deadline.py 自己定义 210 秒、不再 from tunnel_host import CLOUD_PER_JOB_MARGIN_S（否则删常量即 ImportError；注释块已写这一条）；runtime/tests/test_deadline.py 的 test_margins_reuse_the_tunnel_ttl_values（它 import tunnel_host 的两个常量）；隧道-6 的云端一半；隧道-5 里 --tunnel-ttl 的 help 与校验报错、云端进度行；skill 的 SKILL.md 与 references/ 里的 --tunnel-ttl：cli/tests/test_skill.py 的 test_flags_are_attached_to_the_right_subcommand 与 test_bare_flags_exist_somewhere 会因 flag 不存在而变红；test_project_config.py 的 COMMON 名单去掉 --tunnel-ttl（键集差集护栏）
- 单独先落地的后果：只落这一条而隧道仍用可执行文件时，产品可用：守护进程起 ngrok 代理，退出时按 pid 拆，并在 SIGTERM 时仍转成退出去拆；SIGKILL 时代理照旧泄漏。测试方面：test_backend_cloud.py（约 990-1012 行的 tunnel_ttl 覆盖用例与 TTL 文案断言）、test_tunnel_cli.py（test_tunnel_watch_*、test_submit_rejects_*_tunnel_ttl、test_submit_cloud_* 拆或保留隧道的四条）、runtime/tests/test_tunnel_host.py（TTL 一节与 watch 一节）、test_project_config.py（tunnel-ttl 的类型校验、conv('tunnel_ttl')、849-867 行的 --tunnel-ttl 0 用例）会变红。这一条不涉及 Lambda、部署模板与 runs 表写法，不需要重新部署。
- 验证：单测可以覆盖：次序（各道闸失败时不启动守护进程）、管道协议的各种结果怎样映射到退出码与 stderr 说明、到点时刻等于期限加 300 秒。守护进程的新会话与信号、强杀时机、真实轮询 runs 表、隧道随进程消失都要真实执行：在已部署的云端后端上（不必为这一条重新部署；若与云端块同期，在重新部署之后再核一次）用真实 ngrok 执行 ADR 0035 实测项 6（守护进程在 submit 交出 run_id 之前与之后各被强杀一次，submit 在交出之前被强杀一次）、实测项 7（读到终态与到点时刻两条退出路径各一次，之后公网不在线）、实测项 1 的云端组合，以及实测项 10 的云端一次。
- 备注：code 现状：_cmd_submit 先 _setup_tunnel 再 _build_run_meta，然后把建好的 run_meta 交给 _submit_cloud；skew 闸调用 compose.run_requires_backend_stamp(run_meta)，它看 meta.session_warmup_url。按新次序各道闸在起隧道与生成运行定义之前，函数要改成收 (jobs, 有没有隧道)，这一点线索没写，列入 missing。preflight 的 task_defs 与 variant 闸也从 run_meta.jobs 取，改为直接用 jobs。
  守护进程现在是：submit 起隧道之后，Popen _tunnel_watch --tunnel-pid --ttl，stdout 与 stderr 一开始就接临时目录日志；watch_run_and_stop_tunnel 按单调时钟计 TTL，state 为 None 时静默继续，finally 里 stop_tunnel。ADR 要求：按墙钟到期限加 300 秒；读不出或读不到这个 run 时记一句再继续轮询；回报之前的输出接在 submit 的 stderr 上；收到 run_id 之后才写临时目录日志；对 SIGTERM、SIGHUP 取缺省处置。_cmd_tunnel_watch 现在装了把两个信号转成 SystemExit 的处理器，SDK 落地时要删，线索没写，列入 missing。
  守护进程判断终态用的是 DynamoDBRunStore.load_run_state(run_id).status：状态取法块改成「run 的状态由 job 终态算出」之后，守护进程跟着用新的取法，不用另改。但云端块重新部署之后，这条要重新真跑一次。
  删 --tunnel-ttl 之后，配置文件的 tunnel-ttl 键随 argparse 自动消失（settings.configurable_keys 从 parser 派生），不用另删；settings.apply_project_config 的文档串点名了 _tunnel_watch 与 _reconcile，入口改名时同步改。
  线索的位置写的是 runtime/gherkai_runtime/tunnel_host.py，但云端 submit 的主体在 __main__._submit_cloud 与 _cmd_tunnel_watch，tunnel_host 只放守护进程的主体函数。

#### 隧道-4（test，M）

- 线索：测试随之删改：runtime/tests/test_tunnel.py、runtime/tests/test_tunnel_host.py
- 要做的：test_tunnel.py：NgrokTunnel 一节（_FakeProc、spawn 参数、authtoken 提示、可执行文件缺失、策略文件生命期、脱离进程组、stop_tunnel 幂等）改成对假 SDK 的用例：策略在内存里交给 SDK、四种失败说法、懒导入、关闭会话；test_traffic_policy_has_four_rules… 改为 5 条规则且到点规则在最前。test_tunnel_host.py：删 TTL 一节，watch 一节改为新的守护进程主体（终态退出、到点退出、读不到时记一句、不再在 finally 里拆）。test_tunnel_cli.py：test_submit_local_writes_tunnel_file…、test_submit_*_tears_down_tunnel、..._keeps_tunnel_after_*、test_tunnel_watch_requires_explicit_ttl、两条 tunnel_ttl 校验删除或改写为回报管道的各种结果；test_run_cloud_wires_session_warmup_url_into_fargate_engines 随云端前台 run 删去。test_detached_launcher.py 的 test_drive_local_reconcile_tears_down_tunnel_for_an_already_terminal_run 删去。
- 文件：runtime/tests/test_tunnel.py、runtime/tests/test_tunnel_host.py、cli/tests/test_tunnel_cli.py、runtime/tests/test_detached_launcher.py、cli/tests/test_main.py、cli/tests/test_project_config.py、cli/tests/test_backend_cloud.py、runtime/tests/test_deadline.py
- 先要有：隧道-1；隧道-2；隧道-3
- 必须同批：每个测试文件的改动与它所测的那条 code 改动放在同一提交（分别跟隧道-1、隧道-2、隧道-3）
- 单独先落地的后果：不能单独落：删改的是现行 code 的用例，code 没改时删掉它们只会让覆盖变少，改写成新行为的用例则会变红。
- 验证：pytest 全绿即可。这一条本身只是测试，它所测的结论凡依赖进程、管道与 SDK 的，验证见隧道-1、2、3 的真实执行项。
- 备注：线索只点名了三个隧道测试文件，加上「detached 一侧讲交接与拆隧道的用例」。实际受影响的范围更大：test_main.py 里所有断言 submit 自己写出 run_meta.json 或 run_state.json 的 submit 用例（如 1439-1450 行的 max_concurrency、1653-1666 行的 steps_dir、3324 行的 detached 标记、658-670 行的期限偏移），test_project_config.py 的 329、861、920 行，test_backend_cloud.py 990-1012 行的 tunnel_ttl，runtime/tests/test_deadline.py 第 20 行。这些都要随隧道-2 与隧道-3 改。test_main.py 第 550 行、cli/tests/_doc_rules.py 第 607 行、test_skill.py 第 233 行在说明或注释里拿 --tunnel-ttl 举例，flag 删掉之后宜换一个现存的 flag，否则最后那次残留检索会命中。

#### 隧道-5（code，S）

- 线索：隧道的用户可见文字随实装改为 0035 的目标设计
- 要做的：__main__.py：run 与 submit 的 --expose-local help 改为写可选依赖 gherkai[tunnel] 与环境变量 NGROK_AUTHTOKEN，「运行结束即拆除」按「寿命」一条改写；删去 submit 的 --tunnel-ttl 及其 help 与取值校验报错；_setup_tunnel 的「隧道已建立……运行结束即拆除」一句同步改；本机进度行去掉 pid、tunnel.json 与「终态即拆」；云端进度行去掉「终态即拆」、TTL 与 TTL 的来源，日志落点改写 gherkai-tunnel-watch-<run_id>.log，保留「本机需保持开机联网直到 run 终态」；删去「隧道已拆除……」一行。tunnel.py：「找不到 ngrok 可执行文件」「ngrok 隧道未就绪（」两句换成决策 1 的四种说法，都以退出码 2 结束。_cmd_tunnel_watch 里打印的「隧道已拆」几行一并改。
- 文件：cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/tunnel.py
- 先要有：隧道-1（四种说法、前置）；隧道-2（本机进度行）；隧道-3（--tunnel-ttl、云端进度行）
- 必须同批：分别与隧道-1、2、3 同一提交，各自带上自己那部分文字；用户指南、skill、evals.json 的同类改写（行为文档块）
- 单独先落地的后果：单独改文字而行为不改，文字就会描述不存在的行为，例如说需要 [tunnel] 而实际仍要求可执行文件；删 --tunnel-ttl 的 help 而不删 flag 也没有意义。
- 验证：单测即可：cli/tests/test_user_facing_messages.py 守 code 字面量里不带内部指代，test_skill.py 守 skill 里的 flag。四种失败说法在真实环境里是否真能触发，见隧道-1 的实测项 9、10、12。
- 备注：--expose-local 的 help 现在是：run 写「需已配 ngrok authtoken（NGROK_AUTHTOKEN）」与「运行结束即拆除」；submit 写「submit 后隧道由后台进程持有……本机需保持开机联网直到 run 终态」，后半句仍然成立。_setup_tunnel 的进度行「（访问受本次运行专用的会话保护，运行结束即拆除）」不在线索的逐条清单里，宜一并改。云端进度行现在把 CLOUD_STARTUP_MARGIN_S 与 CLOUD_PER_JOB_MARGIN_S 的数值拼进文案，随常量一起删。线索的取舍条写明 submit 不再打印生效的存活时长，照办即可。

#### 隧道-6（code，S）

- 线索：_cmd_submit 末尾 finally 里就地拆隧道的一段整段删去，不改写
- 要做的：删去 _cmd_submit 里 handed_off、_mark_handoff、try/finally 中的 stop_tunnel(tunnel_info.pid) 与「隧道已拆除……别再往下推」一句，连同上方讲隧道交棒分界线、「没交棒不等于没提交」的注释。_submit_local 与 _submit_cloud 去掉 tunnel_info、on_handoff 形参及紧跟 Popen 的 on_handoff() 调用。原先那些情形改由回报管道的输出交代：本机见「后台推进进程在回报之前退出」，云端见「与本机同一条规则」。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_tunnel_cli.py
- 先要有：隧道-2（本机一半）；隧道-3（云端一半）
- 必须同批：隧道-2 与隧道-3 中较晚落地的那一条（finally 同时覆盖两个后端：先落一个后端时只能删那个后端的分支）；test_tunnel_cli.py 里 325-478 行「隧道就地拆」一节
- 单独先落地的后果：在两种 submit 仍由 submit 进程起隧道时删它，preflight、落库或 fork 失败时隧道就没人拆，ngrok 代理一直留在公网。
- 验证：单测即可（handoff 一节删掉，回报管道的各种结果由隧道-2、3 的用例覆盖）；真实表现见隧道-2、3 的实测项。
- 备注：若隧道-2 与隧道-3 分在两批，这一段要分两次删：先落本机时，finally 只剩云端分支（tunnel_info 只在 backend 为 cloud 时由 submit 起）。线索说「0035 已没有『被接受的代价』与交棒边界一条，不需要同步改 ADR」，我核过：0035 现行正文没有这两条，所说属实。

## 随实装改写的 code 注释（指针已处理，行为描述待改）

### 小结

这一块有 10 条（注释-10 已随「云端只支持 submit」那一批做完），都是跟着别的块的 code 改动走的注释、文档串与 DEVELOPMENT.md 改写。改动量小：多数条 S，注释-5、注释-7、注释-11 是 M，合计约 200 到 300 行注释，散在 core、runtime、cli、deploy_aws 约 25 个文件里。只有注释-11 的 deadline.py 是真正的 code 改动（210 秒常量从 tunnel_host 搬进 deadline.py），也只有它可以先于对应块单独落地。其余每条都不能先落：注释描述的是目标行为，code 一天不改，先改注释就与 code 相反；也不能晚落：符号一删，注释就悬空。所以块内没有先后次序，每条随它所跟的块同一提交。

对别块的依赖与归属：注释-1、2、3、4、5 跟「状态取法与结束写」块（结束写入口、删 run_verdict、project_state 只推进、前台未启动的 job），注释-1、5、6 另跟「判定明细点名与落库写序」块，注释-2、3 另跟「报告」块。注释-7 本机那半跟「本机推进器、生命期锁」块的删接力和「run 处置」块；云端那半（_status_cloud、status help 的云端半句）跟 kickoff 删除走，受次序约束，要与后端到期结束 run 同批或在其后，也就是云端重新部署那一批。注释-8 跟「云端后端」块的流过滤与不分流（要重新部署），其中 test_main 那条跟本机 submit 新流程。注释-9 只是指针统一，随时可落，宜并进注释-8 那一批。注释-11 跟隧道块。

最大的风险是漏改和漂移。线索只列了一部分位置：仅「接力」一词，线索之外的 production code 命中就有二十多处，其中三处是用户可见文字，另有 detached 分流、try_finalize、run_verdict 与 _NON_VERDICT 的同类残留，见 missing。建议每批提交前按收尾审计的检索词对改到的文件做 grep 差集，不靠读。另一个风险是与 journey 0019 重叠：那份清单按文件列出了要加回的 ADR 指针，同样是「改到某文件时照做」。两份清单涉及同一批文件，每批改注释时应同时取 0019 里同一文件的条目，否则行为描述改了、指针没加回，或者反过来。注释-5 里 RunPersistence.begin 的理由取决于 preflight 去留，那是 owner 还没定的问题；注释-2 要写全「每条来路一句」，取决于「结束写取哪一个来路的说明」那个待定项。这两处要等答复。

### 线索没有覆盖的改动点

- core/gherkai_core/ports.py：模块头第 5 行「撑轮询接力」；RunStore 类文档串第 137-146 行，生命周期写成 try_finalize 作 commit point，写入方里有「接力者」（依据：0034「推进器与触发源」；0031 决定三「结束写」小节；0030 决定三）
- core/gherkai_core/ports.py：ResultStore 类文档串「判定真值唯一权威」与固定路径 jobs/<encoded_scope_id>.json；ReportStore 类文档串「可从 RunResult 完全重建、判定真值在 RunResult/ResultStore」（依据：0030 决定三「点名」条与「状态以运行态为准」；0027「ReportStore 接口：整 run 一次写」）。报告块只列了 ReportStore.write 的文档串
- core/gherkai_core/project.py projected_run_status 文档串第 857-861 行：「提前落 run 级终态会被 try_finalize 认成已 finalize」「commit point 的专属性」（依据：0034 机制三②；0031 决定三「结束写」小节）
- core/gherkai_core/model.py：RunState 类文档串第 616-618 行「try_finalize 以条件写落定总 status」；第 197 行（severity 表）与第 222-226 行（TERMINAL_STATUSES 注释）拿 _NON_VERDICT 作对照，_NON_VERDICT 删去后悬空；Status 的 SKIPPED、ABORTED 行内注释第 187-188 行没有写到结束写的来路（到期、处置）（依据：0031 决定三与决定一的表；0054 决策二「一次前台执行可能因三种原因停下」段）
- core/gherkai_core/persist.py：模块头第 12-14 行「commit-point 写序：ResultStore 先逐 job 落 → RunStore.try_finalize 最后写」；类文档串里「finalize（commit point）」；finalize 文档串第 185-186 行指向 project.run_verdict（依据：0030 决定三「逐 job 的提交点」；0031 决定三）
- core/gherkai_core/schedule.py：模块头第 18-20 行「已过停止启动或已发现 run 被别处结束就不启动、不产出判定；否则 run 已中止的记 SKIPPED」；schedule 文档串第 645-646 行与第 653 行「run 级状态与说明由 project.run_verdict 给出」（依据：0054 决策二「一次前台执行可能因三种原因停下」段；0031 决定三）
- core/DEVELOPMENT.md 第 34 行 schedule.py 一条「run 级经 project.run_verdict」（依据：0031 决定三）。行为文档块只列了 0054 一行与 run_store 一条，注释-4 只列了 project.py 一条
- 「接力」的线索外命中（依据：0034「推进器与触发源」与被拒方案「本机接力，及其改法」）：core/gherkai_core/serialize.py 第 501 行；core/gherkai_core/adapters/_atomic.py 第 7 行；run_store/local.py 第 57、60 行（_atomic_write_json 文档串）与第 124-126 行（is_detached 文档串「status --wait 据此分流、接力推进」）；event_log/recording.py 第 8 行；event_log/__init__.py 第 4 行；event_log/sqlite.py 第 12、15、19、111 行；reconcile.py 第 112 行（finalize_report）；runtime/gherkai_runtime/compose.py 第 367、439、922 行（「三宿主」含 status --wait 接力者）；runtime/gherkai_runtime/names.py 第 18 行（--wait 推理出 kicker 名做 kickoff）；deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py 第 6、257、563、642 行；exit_observer.py 第 8 行；cli/gherkai_cli/__main__.py 第 1759、1765、1783、2319 行
- 用户可见文字里的接力说法（依据：0054 决策八，status --wait 对前台与后台的 run 都会处置；0039）：cli/gherkai_cli/render.py 第 223-224 行 FOREGROUND_RUN_NOTE「status --wait 对它只等待、不接力」；cli/gherkai_cli/__main__.py 第 134-137 行 _STEPS_DIR_HELP_RUN_SUBMIT 的 help「本机后台推进/接力进程」（同一段的「[--backend cloud] 不生效」对 run 也失效，依据 0016 决策 A）；第 2744-2747 行 _definition_contract_message「本机不能读取或接力推进」。skill 副本 references/cli-json-contract.md 第 129 行 detached 一行的同一说法，要随契约页同批改
- 按 detached 分流的线索外命中（依据：0034 端到端 cloud 1b「触发过滤不看后台执行标记」）：core/gherkai_core/adapters/run_store/ddb.py DynamoDBRunStore.__init__ 文档串第 207-210 行（detached 参数、kicker 只认它、同步 run 双开推进器）与 create_run 文档串第 226 行；deploy_aws/gherkai_deploy_aws/stack.py 模块文档串第 15-16 行（kicker 只收带 detached 标记的 INSERT）与第 183 行注释
- core/gherkai_core/adapters/result_store/s3.py save_job_result 文档串第 46 行「追加语义即同 key 覆盖，幂等」（依据：0030 决定三「点名」条、决定六 ResultStore 段）
- cli/gherkai_cli/render.py 第 143 行 run_tree 注释「run 级说明：没有任何 job 能承载的原因」，以及 render_run_state 里 run 级消息那一句（依据：0031 决定三「结束写」小节说明表；0037 决策 7）。0019 只记了加回指针，行为描述要改
- 隧道相关的线索外连带（依据：0035 决策 3、被拒方案「保留 --tunnel-ttl，只允许调小」；0051 决策 13「边缘策略」）：runtime/tests/test_deadline.py 第 22-23 行与 tunnel_host 常量断言相等；cli/tests/test_backend_cloud.py 第 978-981 行用 tunnel_host 常量算 TTL；runtime/gherkai_runtime/tunnel.py 第 96 行「四条规则」注释（现在是 5 条，含到点拒绝）；tunnel_host.py 第 40-41 行第 ② 段「云端同步 run 的停止后等待预算」搬进 deadline.py 时要删（依据：0016 决策 A）
- runtime/gherkai_runtime/compose.py 第 1851-1854 行 FARGATE_STOP_TIMEOUT_MAX_S 之上讲「云端同步 run 的停止后等待预算」的注释块：cloud_stop_bound_s 随 run 不收云端后端删去之后，这个常量仍留着（doctor 的 stopTimeout 比对、210 秒尾段），注释要改为现存的两种用途（依据：0016 决策 A；0054 决策二「尾段与余量是预算的取值」）

### 逐条

#### 注释-1（mixed，S）

- 线索：认领计数作写条件的描述改为写入序号（认领计数不作任何写的条件）
- 要做的：RunState.claim_count 注释改为只是诊断键（status --json），删去「到期收尾写以库中计数等于读到的值为条件」；ports/local/ddb 三处 try_finalize 的 expected_claim_count 说明随 try_finalize 换成结束写入口一起删去，新入口的文档串写云端以写入序号为条件、本机在文件锁内；reconcile._finalize 步骤③、RunPersistence.finalize「不带认领计数的条件」一段随这两个函数改写；core/DEVELOPMENT.md reconcile.py 一条的后半句「以带认领计数的条件写收尾」改为写入序号或结束写。
- 文件：core/gherkai_core/model.py、core/gherkai_core/ports.py、core/gherkai_core/reconcile.py、core/gherkai_core/persist.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/DEVELOPMENT.md
- 先要有：结束写入口取代 try_finalize 与 expected_claim_count（状态取法与结束写块）；后台推进逐 job 写序，_finalize 改写（状态取法与结束写块）；云端 STATE 的写入序号（云端后端块第 1 条）
- 必须同批：结束写入口（状态取法与结束写块）；RunPersistence 逐 job 写序与 finalize 的结束写（判定明细点名与落库写序块）
- 单独先落地的后果：测试不会红，但注释说的是写入序号，code 仍按认领计数作条件，注释与 code 不符；产品不受影响。
- 验证：只改注释，单测够用：全仓 grep claim_count、expected_claim_count、认领计数，与收尾审计词表做差集，再跑 tools/doc_rules_check.py。写入序号的条件写本身要在真实 DynamoDB 上验证，那是云端块的事，不算这条的证据。
- 备注：跟「状态取法与结束写」块走（try_finalize 换成结束写入口、_finalize 改写），云端那半跟「云端后端」块的写入序号走。逐处核过：model.py 第 641-644 行、ports.py 第 170-182 行、reconcile.py 第 247-249 行、persist.py 第 177-178 行、local.py 第 344-356 行、ddb.py 第 462-485 行、core/DEVELOPMENT.md 第 37 行都还在。除 RunState.claim_count 注释与 DEVELOPMENT.md 那一句，其余几处都在要删或要重写的函数里，实际上随函数一起重写，不需要单独改。按 0034 机制三②，写入序号只在云端；本机靠文件锁，所以本机 adapter 的新文档串不能写「以写入序号为条件」。ddb.py 模块头第 15-16 行讲 claim_count「create_run 恒写、认领成功时原子加一」，在新设计下仍然对，可以不动，只需补一句只作诊断；写入序号属性要不要也进模块头的 STATE 条目，交给云端块定。

#### 注释-2（code，S）

- 线索：run 级说明「只给没有任何 job 能承载的原因」改为每条来路都有一句
- 要做的：RunState.message 与 RunResult.message 的注释改为：结束写的每条来路（到期、处置的两行、fail-fast 或中断、运行定义不可用）各有一句说明表里的话，只由结束写写下；RunVerdict 文档串随 RunVerdict 删去；ports 上结束写入口的文档串写明它写 run 级说明；render_index_html 第 357 行那句 run 级说明注释，以及 ddb.py 模块头 STATE 条目里 message「只在推进器不经任何 job 就终结 run 时随 try_finalize 写入」，都按说明表改写。
- 文件：core/gherkai_core/project.py、core/gherkai_core/model.py、core/gherkai_core/ports.py、core/gherkai_core/adapters/report_store/local.py、core/gherkai_core/adapters/run_store/ddb.py
- 先要有：删去 run_verdict 与 RunVerdict、新的 run 状态取法（状态取法与结束写块第 2 条）；结束写入口（状态取法与结束写块第 4 条）
- 必须同批：删 run_verdict 与新取法的那一批；index.html 由结束写结束的 job 的显示（报告块第 2 条），render_index_html 那句随它改
- 单独先落地的后果：测试不红；注释会说「每条来路都有说明」，但 code 仍只在到期或运行定义不可用时写 message，与 code 不符。
- 验证：单测够用：grep「没有任何 job 能承载」应为 0，再跑 doc_rules_check。说明表的句子是否逐来路写下，由状态取法块的单测守。
- 备注：跟「状态取法与结束写」块走，render_index_html 那句跟「报告」块走。逐处核过：project.py RunVerdict 在第 789-793 行，model.py RunResult.message 在第 518-521 行、RunState.message 在第 635-640 行，ports.py try_finalize 在第 176-178 行，report_store/local.py 在第 357 行，ddb.py 模块头在第 13-14 行，都还在。线索没列到的同类注释：cli/gherkai_cli/render.py 第 143 行 run_tree 里的「run 级说明：没有任何 job 能承载的原因」，以及 render_run_state 里 run 级消息那一句（0019 只记了要加回指针，行为描述同样要改）。0031 决定一的说明表里中断来路怎样说明，与「写回时留下」里「结束写取哪一个来路的说明」那个待定项相关，那项没定之前，注释写不全每条来路的句子。

#### 注释-3（code，S）

- 线索：「没有启动的 job 保持 pending、不产出判定、是 run_meta.jobs 与 jobs 的差」改为由结束写记 skipped
- 要做的：把「没有启动的 job 停在 pending、是 run_meta.jobs 与 jobs 的差」改为「起 worker 之前的检查命中即不启动，留在 pending，之后由结束写记 skipped、不产出 JobResult」。涉及：RunPersistence.on_job_complete 文档串（第 161-162 行）、_Worker.run 文档串（第 351-352 行）、Status 文档串的 skipped/aborted 段与 PENDING 行内注释、RunResult 文档串与 jobs_without_verdict、render_text 文档串、render_index_html 第 206 行与第 344-346 行的注释。
- 文件：core/gherkai_core/persist.py、core/gherkai_core/schedule.py、core/gherkai_core/model.py、cli/gherkai_cli/render.py、core/gherkai_core/adapters/report_store/local.py
- 先要有：前台没有启动的 job 不再构造 skipped 的 JobResult，_stop_all 不记 skipped（状态取法与结束写块第 7 条）；RunPersistence.finalize 的结束写（判定明细点名与落库写序块第 3 条）；index.html 与 render_text 改为按运行态显示由结束写结束的 job，删去「没有执行」（报告块第 2 条）
- 必须同批：状态取法与结束写块第 7 条；报告块第 2 条
- 单独先落地的后果：测试不红；注释说未启动的 job 由结束写记 skipped，code 仍让它停在 pending、在报告里标「没有执行」，注释反过来与 code 相反。
- 验证：单测够用：grep「run_meta.jobs 与 jobs 的差」「保持 pending、不产出判定」「没有执行」做差集。行为本身由 test_schedule 与 test_persist 的新用例守。
- 备注：跟「状态取法与结束写」块第 7 条和「报告」块第 2 条走。逐处核过，都还在：persist.py 第 161-162 行、schedule.py _Worker.run 第 351-352 行、model.py Status 第 176-189 行、RunResult 第 504-508 行、jobs_without_verdict 第 534-539 行、render.py 第 73-77 行与第 130-131 行、report_store/local.py 第 206 行与第 344-357 行。拿不准的一处：报告改为从记录组装 RunResult 之后，jobs_without_verdict 是删掉，还是改成「由结束写结束、没有明细的 job」继续给 render 用，要看报告块怎样组装；注释怎样写取决于这个选择。Status 的 SKIPPED 与 ABORTED 行内注释（第 187-188 行，「整批中止时 worker 从未 spawn」「主动中止时执行到一半被停止」）在新设计下还有到期、处置两条来路（running 记 aborted、pending 记 skipped），线索里的「skipped/aborted 段落」是否包括这两行不明，建议一并改。schedule.py 模块头第 18-20 行与 schedule 文档串第 645-646、653 行也是同一种说法，线索没有列。

#### 注释-4（mixed，S）

- 线索：「run 级裁决：包住 _aggregate、加上聚合之外的例外」一类描述随 run_verdict 删改
- 要做的：run_verdict 的文档串随函数删去；schedule() 第 771-773 行调裁决处的注释改为按取法算 run 状态（或只交出 job 结果，由结束写决定）；core/DEVELOPMENT.md project.py 一条删去 run_verdict 一项，plan_next 那半句「余下的 job 在事件流里都没有记录时」改为按运行态里的 pending；Status 文档串的 aborted 段删去「规则见 project.run_verdict」，改为按取法：有 aborted 或 skipped、没有 error 与 failed 时为 aborted。
- 文件：core/gherkai_core/project.py、core/gherkai_core/schedule.py、core/gherkai_core/model.py、core/DEVELOPMENT.md
- 先要有：删去 run_verdict/RunVerdict、新的取法函数（状态取法与结束写块第 2 条）；推进决策「未启动」按运行态 pending 判断（状态取法与结束写块第 6 条）
- 必须同批：状态取法与结束写块第 2 条（run_verdict 一删，指向它的注释就悬空）
- 单独先落地的后果：run_verdict 还在时先改注释，注释所描述的取法 code 里还没有；反过来先删 run_verdict 而不改注释，注释指向一个不存在的符号。测试不红。
- 验证：单测够用：grep run_verdict、RunVerdict、「聚合之外」应为 0，再跑 doc_rules_check。
- 备注：跟「状态取法与结束写」块第 2 条走，plan_next 那半句跟第 6 条走。逐处核过，都还在：project.py run_verdict 在第 796-841 行，schedule.py 第 771-778 行，core/DEVELOPMENT.md 第 35 行，model.py Status 第 177-179 行。线索没列到的同类：core/DEVELOPMENT.md 第 34 行 schedule.py 一条的「run 级经 project.run_verdict」；model.py RunResult 文档串第 507-508 行与 status 字段注释第 515-516 行；persist.py RunPersistence.finalize 文档串第 185-186 行「写下的是 run 级裁决对这种情形给出的 aborted（见 project.run_verdict）」（会随判定明细块重写 finalize 一起改）；project.py project_full 文档串第 692-696 行「run 级的状态与说明由 run_verdict 给出」（随 project_full 改写）。model.py 第 197 行（severity 表）、第 205-211 行（_NON_VERDICT 上方）、第 222-226 行（TERMINAL_STATUSES 注释）都拿 _NON_VERDICT 作对照，_NON_VERDICT 一删就悬空；测试块只列了「_NON_VERDICT 上方注释」，另两处没人列。

#### 注释-5（code，M）

- 线索：「终态是 finalize 专属」「try_finalize」「判定真值的唯一权威是 jobs/*.json」一类说法改写
- 要做的：run_store/local.py 模块头：「判定真值唯一权威是 jobs/*.json、run_state.json 是投影摘要」改为状态以运行态为准、明细对 scenario/step/归因负责（0030 决定三）；fcntl 一段的写入口名单去掉 try_finalize、加上结束写入口，去掉「status --wait 接力」。local 与 ddb 的 project_state 文档串，「终态是 finalize 专属」改为投影不写 job 终态、run 级只写 running。ports.RunStore 探活注释与 RunPersistence.begin 文档串里拿云端桶名错分裂退出码作理由的一段，按 run 只有本机后端之后的结论改写。NonTerminalSnapshot 的强制点改为保存一个 job 的明细之前。
- 文件：core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/ports.py、core/gherkai_core/persist.py、core/gherkai_core/project.py
- 先要有：状态投影只推进运行态（状态取法与结束写块第 6 条 project_state）；结束写入口（状态取法与结束写块第 4 条）；明细点名、去掉 load_all（判定明细点名与落库写序块第 1 条）；后台逐 job 写序（状态取法与结束写块第 7 条）；begin 的理由随 run --backend cloud 以退出码 2 结束（已随「云端只支持 submit」那一批做完）失效；owner 定 begin 与端口上 preflight 的去留（写回时留下的问题第 2 条）
- 必须同批：project_state 改为只推进运行态的那一批；RunPersistence.begin 的 preflight 去留定下之后那一批
- 单独先落地的后果：测试不红。说法改成「状态以运行态为准、投影不写 job 终态」，可 project_state 仍把 job 终态投影写进库，注释与 code 相反。
- 验证：单测够用：grep「finalize 专属」「判定真值」「唯一权威」「try_finalize」做差集。project_state 不写终态的行为由 test_conditional_writes 的对拍用例守。
- 备注：跟「状态取法与结束写」块（project_state、结束写、逐 job 写序）和「判定明细点名」块走；begin 那段跟 preflight 待定项走。逐处核过，都还在：local.py 模块头第 7-17 行，local.py project_state 第 301-305 行，ddb.py project_state 第 374 行，ports.py 第 215-217 行，persist.py begin 第 85-87 行，project.py NonTerminalSnapshot 第 657-662 行。疑点：begin 那段改成什么，取决于 preflight 保不保留，这是 owner 还没定的问题，这一处要等答复。线索没列到的同类：ports.py RunStore 类文档串第 137-146 行（生命周期写成 try_finalize 作 commit point，还提到「接力者」）；ports.py ResultStore 文档串「判定真值唯一权威」与固定路径 jobs/<encoded_scope_id>.json；ReportStore 类文档串「可从 RunResult 完全重建、判定真值在 RunResult/ResultStore」；project.projected_run_status 文档串第 857-861 行（被 try_finalize 认成已 finalize、commit point 的专属性）；model.py RunState 文档串第 616-618 行「try_finalize 以条件写落定总 status」；persist.py 模块头第 12-14 行「commit-point 写序……RunStore.try_finalize 最后写」。

#### 注释-6（mixed，S）

- 线索：明细「后写的盖掉先写的」「保存覆盖同 key」改为每次保存一份、由终态点名
- 要做的：result_store/local.py 模块头：「两个写者两种时序、finalize 分支在 commit 之前一次落下」改为逐 job「先存一份新的明细、再由终态写点名」。save_job_result 文档串去掉「两个推进器竞争收尾时先后各写一遍、后写的盖掉先写的」，改为每次保存一个新对象（文件名带保存标识），同一次保存的重试用同一个标识。reconcile._finalize 步骤②随逐 job 写序改写。test_local_result_store_atomic.py 模块文档串去掉 per-run 进程与 status --wait 接力竞争收尾的说法，原子写的理由改为 explain 读被点名的那一份。
- 文件：core/gherkai_core/adapters/result_store/local.py、core/gherkai_core/reconcile.py、core/tests/test_local_result_store_atomic.py
- 先要有：明细每次保存一份、键里带保存标识、终态点名（判定明细点名与落库写序块第 1、2 条）；后台推进逐 job 写序（状态取法与结束写块第 7 条）
- 必须同批：判定明细点名与落库写序块第 1 条（ResultStore 键形态的改动）
- 单独先落地的后果：测试不红；注释写的是一份一个对象，code 仍按 scope_id 覆盖同一个文件，与 code 不符。
- 验证：只改注释，单测够用。test_local_result_store_atomic 起真实子进程读文件，键形态改了之后它的构造要能照常运行，跑这个测试确认仍有判别力（回退成 write_text 会红）。
- 备注：跟「判定明细点名与落库写序」块走。逐处核过，都还在：result_store/local.py 模块头第 1-7 行与 save_job_result 第 33-39 行，reconcile.py 第 244-246 行，test_local_result_store_atomic.py 第 1-7 行。线索没列到的同类：core/gherkai_core/adapters/result_store/s3.py save_job_result 文档串第 46 行「追加语义即同 key 覆盖，幂等」，同样要改。连带：键里带标识之后，test_local_result_store_atomic 的写者要给同一个标识反复保存（按线索「本机对同一次保存的重试用同一个标识」），测试的构造才成立，所以可能不只是改文档串。

#### 注释-7（code，M）

- 线索：接力的描述：reconcile.py 模块头触发源括注里的「status --wait 接力」
- 要做的：删去或改写以下各处讲本机与云端接力的行为描述：reconcile.py 模块头的触发源括注（删去「status --wait 接力」，可恢复指向 0034「推进器与触发源」）；EventLog 文档串讲本机接力恢复的两处；project.TaskExited 里「接力者补写」的两处；detached.py 模块头、run_reconcile_loop、drive_local_reconcile（含「接力者同样兜底拆」）、build_local_reconcile；RunMeta.steps_dir 的「三宿主」；JobState.claimed_at 注释与 RunStore.try_claim_job 的用途改为只是截止时刻的起算点；LocalRunStore 类文档串里「接力者」一句；__main__.py _cmd_status 与 _cmd_status_body 的「两道闸」、_render_status、_status_cloud、_submit_local；status 子命令的 --wait、--max-concurrency、--prefix 的 help。
- 文件：core/gherkai_core/reconcile.py、core/gherkai_core/project.py、core/gherkai_core/model.py、core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、runtime/gherkai_runtime/detached.py、cli/gherkai_cli/__main__.py
- 先要有：删去本机接力（本机推进器、生命期锁与边界检查块第 3 条）；生命期锁（同块第 1 条）；run 处置与等待中的 status --wait（run 处置块第 1、3 条）；云端 kickoff 删去（run 处置块第 3 条的云端那半），它又必须与后端到期结束 run 同批或在其后（云端后端块第 4 条，见「分批的次序约束」）；EventLog 端口上 record_timed_out_if_absent 的去留（本机推进器块第 3 条）
- 必须同批：本机那半：删本机接力的那一批；云端那半（_status_cloud、help 里的「cloud 检测卡住即触发云端接力」）：删 kickoff 的那一批，也就是云端重新部署的那一批或之后
- 单独先落地的后果：测试不红，除非 status help 的文字被测试锁定。产品面：status --wait 的 help 会写成「不推进、只处置」，code 仍在接力推进，使用方看到的说明与实际行为相反。
- 验证：注释与 help 的改动用单测加 grep 差集：production code 里「接力」应为 0（收尾审计词），test_user_facing_messages 照常通过；「接力推进」进退役词表后由测试守。行为本身（没有接力、锁、处置）要真实执行：本机真实进程、杀掉后台推进进程之后用 status --wait 与 settle-runs 处置，那是本机推进器块与处置块的验证。
- 备注：本机那半跟「本机推进器、生命期锁与边界检查」块第 3 条（删接力）和「run 处置」块走；云端那半跟「run 处置」块第 3 条的 kickoff 删除走，受「分批的次序约束」第一条限制（要与后端到期结束 run 同批或在其后），也就是与云端重新部署的那一批绑在一起。所以这条要拆成两半，分别落在两个批次里。逐处核过，都还在：reconcile.py 第 9 行、第 71 行、第 77 行；project.py 第 256 行、第 278 行；detached.py 第 8 行、第 208-217 行、第 248-254 行、第 315-347 行；model.py 第 572 行、第 606-608 行；ports.py 第 231-232 行；local.py 第 75-76 行；__main__.py 第 472-482 行、第 2084-2112 行、第 2123-2127 行、第 2168-2172 行、第 2216-2295 行、第 1655 行。线索之外还有大量「接力」命中，见 missing。EventLog 那两处的写法取决于 record_timed_out_if_absent 留不留（云端 tick 的补写仍用它）。

#### 注释-8（mixed，S）

- 线索：按 detached 分流的描述：ddb.py `is_detached` 文档串后半句
- 要做的：ddb.is_detached 文档串的后半句（云端推进器据它分流、同步 run 双开推进器）改为只供 list-runs --json 的 detached 键；ddb 模块头与 _state_item 的「kicker filter 认它」删去；exit_observer.py 模块头与 _is_detached 随分流删去；reconciler._build 与 _run_ids_from_runs_stream（status --wait kickoff 一格）、stack._reconcile_lambdas（三个 handler 自己分辨、kicker 靠流过滤）、compose.build_cloud_stores「触发 kicker 冷启动」一句都按两条流过滤与不分流改写；两个测试的文档串改为标记只作描述。
- 文件：core/gherkai_core/adapters/run_store/ddb.py、deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/gherkai_deploy_aws/stack.py、runtime/gherkai_runtime/compose.py、core/tests/test_ddb_run_store.py、cli/tests/test_main.py
- 先要有：kicker 的流过滤改为两条（云端后端块第 2 条）；handler 不按后台执行标记分流（云端后端块第 3 条）；kickoff 删去（run 处置块第 3 条），_run_ids_from_runs_stream 的 kickoff 一格才能删；本机 submit 由后台推进进程建 run（本机推进器块第 1 条、隧道块第 2 条），test_main 那条用例要随之重写
- 必须同批：云端后端块第 2、3 条，与云端重新部署同一批；test_main 那一条随本机 submit 新流程那一批
- 单独先落地的后果：测试不红；注释说不分流，Lambda 与流过滤仍按 detached 分流，注释与部署出去的行为相反。
- 验证：注释改动用 grep 差集（detached、filter、kicker 冷启动）。分流与过滤的行为要在重新部署之后的云端真实验证（一个云端 submit 的 run 由 kicker 冷启动、观察者照写），这属于云端后端块，这条只靠单测与 deploy_aws/tests/test_stack.py 的模板断言。
- 备注：跟「云端后端」块第 2、3 条走，属于要重新部署的一批；test_main 那条跟本机 submit 新流程走（隧道块与锁块）。逐处核过，都还在：ddb.py 模块头第 19 行、_state_item 第 272 行、is_detached 第 721-736 行；exit_observer.py 第 9-10 行、第 21 行、第 55-67 行；reconciler.py 第 450 行、第 486-495 行（_build）；stack.py 第 588-601 行、第 733-745 行；compose.py 第 1118 行；test_ddb_run_store.py 第 131-132 行；test_main.py 第 3322-3323 行。连带：test_local_submit_marks_the_run_detached_and_foreground_run_does_not 打桩 Popen、断言 submit 进程写出的 run_state.json 带 detached；新流程下 submit 不建 run（由后台推进进程建），这条用例要整体重写，不只是改文档串。journey「核对时补上的条目」第 2 条（_submit_cloud 里 detached=True 的注释）是同一类，应与这条同批。线索之外：ddb.DynamoDBRunStore.__init__ 文档串第 207-210 行（detached 参数、同步 run 双开推进器）、create_run 文档串第 226 行，stack.py 模块文档串第 15-16 行（kicker 只收带 detached 标记的 INSERT）与第 183 行，都没有列。

#### 注释-9（mixed，S）

- 线索：RunState 写入方的指针：stack.py `_grant_task_role` 与 `_reconcile_lambdas`
- 要做的：stack.py 第 392 行与第 640 行、test_stack.py 第 439、453、903 行的「RunState 的写入方见 ADR 0034『数据模型三件套』」，统一改为 0024 红线条用的 0034「命令形态」（那里的表列出谁写 RunState）。
- 文件：deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/tests/test_stack.py
- 先要有：无
- 必须同批：exit-observer 不再读 runs 表（云端后端块第 3 条）：第 639-640 行的注释与 test_exit_observer_can_read_runs_table_only 会随它重写，同批落地可以少改一遍
- 单独先落地的后果：无。两处指针所指的小节都存在，只是统一写法；单独先落也不破坏测试与产品。
- 验证：单测够用：跑 deploy_aws/tests/test_stack.py，再跑 doc_rules_check 或悬空指针护栏确认指针目标存在。
- 备注：这是指针统一，不依赖行为改动，可以排在任何一批；_grant_task_role 与 test_task_role_has_events_putitem_not_runs 两处随时可改。_reconcile_lambdas 第 639-640 行和 test_exit_observer_can_read_runs_table_only 第 903 行会随「云端后端」块第 3 条（观察者去掉 runs 表读权限）重写，建议并进那一批。已核实 0034 的「数据模型三件套」（第 22 行）与「命令形态」（第 33 行）都在；0024 第 278 行红线条指向「命令形态」。

#### 注释-11（mixed，M）

- 线索：隧道建在宿主进程里之后，以下行为描述随隧道实装改写
- 要做的：deadline.py：删去 `from gherkai_runtime.tunnel_host import CLOUD_PER_JOB_MARGIN_S`，在本模块定义 CLOUD_PER_JOB_TAIL_S = 60 + compose.FARGATE_STOP_TIMEOUT_MAX_S + 30，三段组成的注释从 tunnel_host 移过来并指向 0054 决策二「尾段与余量是预算的取值」；模块头与 STARTUP_MARGIN_S 注释去掉拿隧道 TTL 与 compute_watch_ttl_s 作的对照。tunnel_host 的 TTL 常量、compute_watch_ttl_s 与 watch_run_and_stop_tunnel 里 TTL 与拆隧道的文档串随守护进程改写。compose 第 1857 行改为 deadline 的每 job 尾段按它记账。tunnel.py 模块头、NgrokTunnel、TunnelInfo（pid、tunnel.json）、_launch、规则上限注释随 SDK 改写。detached.py 的 write_tunnel_file、cleanup_tunnel 与两处拆隧道的说法删去。submission.py 与 __main__.py 里讲 --tunnel-ttl、交棒、「可手动结束」的注释删改。
- 文件：runtime/gherkai_runtime/deadline.py、runtime/gherkai_runtime/tunnel_host.py、runtime/gherkai_runtime/compose.py、runtime/gherkai_runtime/tunnel.py、runtime/gherkai_runtime/detached.py、cli/gherkai_cli/submission.py、cli/gherkai_cli/__main__.py、runtime/tests/test_deadline.py
- 先要有：隧道改用 ngrok SDK（隧道块第 1 条）；本机 submit 新流程（隧道块第 2 条）；云端 submit 去掉 --tunnel-ttl 与 TTL 记账（隧道块第 3 条）；_cmd_submit 末尾 finally 拆隧道那段删去（隧道块末条）
- 必须同批：隧道块第 1、3 条（TTL 常量删去时 deadline.py 必须已经自己持有 210 秒，否则 import 失败）
- 单独先落地的后果：deadline.py 的常量迁移可以单独先落：把 210 秒定义在 deadline.py，让 tunnel_host 反过来取它，行为不变、测试照常通过（test_deadline 第 22-23 行断言两边相等）。其余注释在隧道实装之前先改，会与仍在启动 ngrok 可执行文件的 code 相反。
- 验证：deadline.py 的迁移用单测：runtime/tests/test_deadline.py 断言 CLOUD_PER_JOB_TAIL_S == 210，并去掉与 tunnel_host 常量的相等断言。注释部分用 grep 差集（tunnel.json、stop_tunnel、--tunnel-ttl、compute_watch_ttl_s、「可手动结束」、「四条规则」）。隧道本身的行为（随宿主退出消失、到点拒绝）要用真实的 ngrok 隧道验证，那是隧道块的证据，不由这条提供。
- 备注：跟「隧道（0035）与两种 submit 的新流程」块走。逐处核过，都还在：deadline.py 第 6-9 行、第 22 行、第 24-27 行；tunnel_host.py 第 33-47 行、第 72-99 行；compose.py 第 1857 行；tunnel.py 第 3-5 行、第 51 行、第 60-65 行、第 177-181 行、第 222-273 行；detached.py 第 216 行、第 233 行、第 248-254 行、第 366-380 行；submission.py 第 273 行；__main__.py 第 1652-1716 行、第 1743-1765 行、第 2774-2784 行、第 2899 行。deadline.py 一项不只是注释：要搬常量、改 import（deadline 改为 import compose；compose 在模块层不 import deadline，__main__ 里是函数内的延迟 import，没有循环）。tunnel_host 第 40-41 行的第 ② 段还写着「云端同步 run 的停止后等待预算……也取它」，搬到 deadline.py 时要随 run 不收云端后端删去。线索没列到的连带改动：runtime/tests/test_deadline.py 第 22-23 行（与 tunnel_host 两个常量断言相等）；cli/tests/test_backend_cloud.py 第 978-981 行（用 tunnel_host 常量算 TTL，随 TTL 删去）；tunnel.py 第 96 行「四条规则」注释（现在是 5 条，含到点拒绝，见 0051 决策 13）；__main__.py 第 544-549 行内部命令 _tunnel_watch 的 --ttl 参数与注释；第 1297、1460、2861 行提到 --tunnel-ttl 的校验惯例对照，可以归进「提到 --tunnel-ttl 的注释」，但要逐处删改。

## 行为文档（随所改行为的实装批同一提交改）

### 小结

这一块 19 条全是文档（含 3 张图、评测 fixture 与 evals.json、契约页的生成副本与一处测试），本身没有生产 code，总量相当于几百行文档改写，最大的是 execution-and-reconciliation.md 的大面积重写（L）与 fixture 重录。每条都跟在别的块后面：①「状态取法与结束写」「判定明细点名」块 → 行为文档-1、2（写序部分）、6（键与取法）、8（fixture）、10（到期与中断条目）；②「本机推进器、生命期锁」的删本机接力 → 2、3、5（--max-concurrency）、7（第 8 节）、10（第 59–60 行）；③「run 处置」块 → 5、6、7、14、19 里讲 settle-runs 与处置权限的部分；④「云端后端」块（kicker 过滤、handler 不分流、清扫）→ 2 的 §7；⑤「云端只支持 submit」块已做完（3、5、6、7、9、10、19 里归它的部分已从各条删去，18 整条删去）；⑥「隧道」块 → 11–17 与 12 的 4a 首行；⑦「词表与退役词」块 → 9（execution-timeout-chain）。有测试守、必须与 code 同提交的是：契约页（test_cli_json_contract 收集真渲染器的键与 doctor 项名，副本由 test_skill 比对）、skill 正文（test_skill 用真 parser 核 flag 归属，删 --tunnel-ttl 或 run 的云端选项时即红）、图（导出与图源一致、退役词扫描）、退役词入表（扫 CHANGELOG 与图源）。其余条目没有测试守，漏改不会变红，要靠收尾的残留检索。最大的风险：一是行为文档-2、3、5、6、7、10 这几条各跨三到六块，排批时必须按块拆开、各随各的 code 批，否则文档会先于或落后于 code；二是这一块的线索按「点名的段落」列，同一文件里随同一行为失真的其它段落有不少没被列入（见 missing），只按线索改会留下漂移；三是 fixture 重录与评测、权限表要真实执行（引擎与 Device Farm、Bedrock 评测、重新部署后用最小权限角色），单测不证。

### 线索没有覆盖的改动点

- docs/internals/artifacts-and-evidence.md 第 19–21 行（「判定读 jobs/*.json」「run_state.json 落后于 jobs/*.json…不一致时以 jobs/*.json 为准」「ref 的权威落盘处只有 jobs/*.json」）、第 34 行产物表 `jobs/<enc>.json` 一行（文件名带保存标识、由运行态点名）、第 75 行 report_refs 落在 jobs/*.json：随判定明细点名改为「先读运行态、按点名读那一份」。依据 0030 决定三「点名」条、决定六 ResultStore 段。跟「判定明细点名与落库写序」块。
- docs/internals/cli-json-contract.md（与生成的 skill 副本）里线索没点名的几行：run 一节 artifacts.jobs_dir「文件名是 URL 编码的 scope_id」；status 一节 status 行（skipped 只在全部 job 都没有执行时出现、aborted 只来自被中断的同步 run）与 message 行（「这些 job 保持 pending」，说明只在没有 job 能承载时才有）；list-runs 一节 detached 行「status --wait 对它只等待、不接力」与 --status 不再接受 skipped；doctor 一节项名表加 report_dir.filesystem。依据 0031 决定三取法与「结束写」说明表、0030 决定三、0041 决策三、四、七、0054 决策八。
- agent skill 里线索没覆盖的几处：SKILL.md 第 57 行「status --wait 只等待、不接力」；references/setup-and-diagnosis.md 第 96 行到期一行（总状态记 error、job「没有执行」或保持 pending、job 记 timeout、「过了这个时刻才用 status --wait 接力」），新设计里被期限截断的执行中 job 记 aborted、pending 由结束写记 skipped、run 按取法为 aborted，处置由 settle-runs 或 status --wait 做。依据 0016 决策 A、0031 决定三、0034 机制二、0054 决策二、八。
- docs/user-guide/running-and-results.md 里属于新行为、线索没写的：命令表加 settle-runs 一行，退出码表加 settle-runs 一行及 run 与本机 submit 在报告目录不过边界检查、锁已被持有时以退出码 2 结束，「找回 run_id：list-runs」一节加「已运行」「允许运行至」两列与期限提示、删第 215 行「由前台 run 执行…只等待、不接力」的提示，不带 --wait 的 status 的期限提示。依据 0054 决策四、八、0041 决策七、0031 决定五。（同文件第 83、87、127、164 行的接力与到期描述已列在 0018「核对时补上的条目」末段，不在本块，排批时与本块合并。）
- docs/user-guide/configuration.md 第 63–71 行配置键表与第 200 行以下跨命令选项表：settle-runs 读项目配置文件，--backend/--report-dir/--prefix/--ddb-table/--region 等定位参数的适用命令要加上 settle-runs。依据 0053 决策 1、0041 决策六、0054 决策八。
- docs/user-guide/troubleshooting.md：要加报告目录文件系统类型不在清单里（如网络共享）或判断不了时以退出码 2 结束的症状行，与锁已被持有（同一个 run 已有进程在管）的症状行；第 138–142 行「提交后进度停住」一节改为用 settle-runs 或 status --wait 把管它的进程已不在或已过期限的 run 记为已结束。依据 0054 决策三、四、八。（到期与接力部分已列在 0018「核对时补上的条目」，新症状行没有列。）
- docs/diagrams 下线索没写的图源改动（改完都要用 tools/build_diagrams.mjs 重出 SVG/HTML）：run-execution.json 里「status --wait 两个后端不同：本机 per-run 进程已终止时只有接力者在推进…云端仅在检测到停滞时唤醒推进函数」与「submit 派生 · 可被接力」两处；execution-timeout-chain.json 里「接力者按库里的领取时刻重算截止时刻，过了它 10 秒仍无退出记录即判超时」一句；execution-detached-gates.json 整张图（后台标记的两道判断）在 kicker 不看后台标记、handler 不分流之后不再成立，要删图或重画，连同 execution-and-reconciliation.md 第 157–159 行的嵌入与图注。依据 0034 被拒方案「本机接力，及其改法」、端到端 cloud 1b、0045 决策七。
- core/DEVELOPMENT.md 目录树里线索与「随实装改写的 code 注释」块都没覆盖的几条：第 34 行 schedule.py「run 级经 project.run_verdict」；第 38 行 persist.py「收尾用 try_finalize 带 run 级说明」；第 46 行 event_log 的补写条件写与第 37 行 reconcile.py 里 record_timed_out_if_absent（随 EventLog 端口定去留）；第 51 行 result_store「每 job 一对象」（改为每次保存一份、由终态点名）。依据 0031 决定三、0030 决定三与 0034 被拒方案「本机接力」。
- deploy_aws/DEVELOPMENT.md 里随「云端后端」块失真、线索没写的几处：第 40 行 exit-observer「另读 runs 表以判断 run 是否 detached」；第 41 行 kicker「status --wait 的主动调起」与推进器权限（要加建 run 两次定时触发、按 startedBy 列 task 清扫）；第 44 行 runs 表 Stream filter「INSERT 且 NewImage.detached=true」（改两条过滤）。依据 0034 端到端 cloud 1b、0054 决策九、0033 资源清单 13、15。
- runtime/DEVELOPMENT.md 与 cli/DEVELOPMENT.md 的模块与子命令清单：runtime 新增的生命期锁、边界检查、处置模块要登记一条；cli/DEVELOPMENT.md 第 18 行 argparse 子命令清单加 settle-runs，内部子命令 _reconcile 的说明（本机 submit 经标准输入与回报管道启动、自己建 run 取锁）随之改。依据 0054 决策三、四、六至八、0035 决策 3「本机 submit」。
- CHANGELOG.md [Unreleased] 里新的使用者可见行为的条目：settle-runs 新命令、报告目录文件系统不在清单里时 run/submit/status --wait/settle-runs/doctor 以退出码 2 结束、doctor 新增 report_dir.filesystem、list-runs 新列与 deadline_at、run --json 的 jobs[]、status --wait 会把管它的进程已不在或已过期限的 run 记为已结束、index.html 显示由结束写结束的 job。线索只要求改写已有条目并加一句重构概述，owner「升级与迁移的细节不写」是否也排除这些新功能条目拿不准，要排批时问 owner。依据 0054 决策四、八、0041 决策三、四、七、0027「index.html 形态」。
- docs/internals/architecture-overview.md 第 42 行「由每个 run 一个的本机后台进程、status --wait（接力）」的接力半句（线索只为「四种组合」点名这一行）；docs/internals/cloud-backend-carriers.md 第 11 行 stack 资源与 Scheduler 名字要补上 run 的两次一次性定时触发（名字定下之后）。依据 0034 被拒方案「本机接力」、0054 决策九、0033 资源清单 15。

### 逐条

#### 行为文档-1（doc，S）

- 线索：core/DEVELOPMENT.md：架构决策列表里 0054 一行括注的「run 级裁决」
- 要做的：core/DEVELOPMENT.md 第 20 行 0054 括注改为「期限规则 run_deadline、生命期锁、终态不可变、执行方先认领再启动、run 处置」；目录树第 50 行 run_store 一条把「条件写 try_claim_job/project_state/try_finalize」换成新的结束写入口方法名，写明认领计数只作 status --json 的诊断键。
- 文件：core/DEVELOPMENT.md
- 先要有：「状态取法与结束写」块：删 run_verdict/RunVerdict，端口上结束写入口定名；「云端后端」块：写入序号取代认领计数作写条件（认领计数只作诊断键这半句）
- 必须同批：删 run_verdict 与新增结束写入口的实装批
- 单独先落地的后果：只改文档、code 未动时，目录树写的方法名在 ports.py 里找不到，文档先于 code 漂移；测试不受影响。
- 验证：文档改动，读 diff 核对符号名与 ports.py 一致即可；单测不涉及。
- 备注：跟「状态取法与结束写」块走（括注、try_finalize 一处）；「认领计数只作诊断键」这半句跟「云端后端」块的写入序号改动走（本机 adapter 的认领计数同时失去写条件角色，属「状态取法与结束写」块的 local.py 一侧），两者不在同一批时这一条要拆两次提交。括注里列的「生命期锁」「run 处置」是 ADR 主题的概括，不描述 code，提前写不算漂移。线索没有覆盖同一文件目录树里另外几条随实装失真的说明，见 missing。

#### 行为文档-2（doc，L）

- 线索：docs/internals/execution-and-reconciliation.md：收尾的写序（try_finalize、
- 要做的：按新设计重写这篇的大部分：§1 第 14、16 行（detached 分界、四个 tick 宿主、接力者）、§4a 第 58–68 行流程块（per-run 进程、status --wait 接力）、§5 第 91 与 96–101 行（run 级取值、try_finalize 提交点、jobs/*.json 写序、竞争收尾、两道判断、中途终止）、§6 第 140、143 行（接力判超时、补写）、§7 第 157–167 行（kicker 按 detached 过滤、handler 分流、权威指针）。新写法：逐 job 写序与点名、结束写、生命期锁与处置、kicker 两条过滤与清扫。
- 文件：docs/internals/execution-and-reconciliation.md
- 先要有：「状态取法与结束写」块（结束写、逐 job 写序）；「判定明细点名与落库写序」块；「本机推进器、生命期锁与边界检查」块（含删本机接力）；「run 处置」块；「云端后端」块（kicker 两条过滤、handler 不分流、清扫、两次定时触发）
- 必须同批：与上面每一块各自的实装批同一提交改对应小节
- 单独先落地的后果：单独先改：文档描述的机制在 code 里还不存在；不改：每一批 code 落地之后这篇的相应小节立即失真。测试不受影响（第 167 行的「filter 必须区分写入者」「兜底/接力」条名指针已悬空，但没有测试守它）。
- 验证：文档改动，按批核对 diff 与 code 一致；退役词入表之后 test_user_docs 会扫它。
- 备注：一条跨五块（「云端只支持 submit」那部分，即 §3 与三种组合，已做完），分批时要拆：§5 写序跟「状态取法与结束写」+「判定明细点名」；§1/§4a/§5 第 98、101 行/§6 接力部分跟「本机推进器、生命期锁」块删接力那一批与「run 处置」块；§7 与第 16、80 行 kickoff 跟「云端后端」块与「run 处置」块里删 _STALL_KICK 那一条；4a 首行隧道新次序见行为文档-12。§7 嵌的图 execution-detached-gates 整张所讲的「两道拦截」在新设计里不再成立，线索没写，见 missing。线索里的「local submit 的超时一行（per-run 进程）」对应第 140 行。

#### 行为文档-3（doc，M）

- 线索：技术文档：runtime/DEVELOPMENT.md 的 detached 一条（接力判超时
- 要做的：runtime/DEVELOPMENT.md detached 一条删去接力判超时 _recover_timed_out_claims 与指向 0054「本机接力的改法」的指针；cli/DEVELOPMENT.md「三个推进触发源之一（查询者到来即接力）」改写。（resolve_network、子网与安全组、run 的单项覆盖参数、SSM 参数族、_worker_subnet_ids 与 carriers 的 SSM 一行已随「云端只支持 submit」那一批做完。）
- 文件：runtime/DEVELOPMENT.md、cli/DEVELOPMENT.md
- 先要有：「本机推进器、生命期锁」块的删本机接力
- 必须同批：删本机接力那一批
- 单独先落地的后果：只改文档：说明与 code 不符；测试不受影响。
- 验证：文档改动，读 diff 即可。
- 备注：跟「本机推进器、生命期锁与边界检查」块（删本机接力）。deploy_aws/DEVELOPMENT.md 里另有 kicker 过滤、exit-observer 读 runs 表等失真处，线索没有覆盖，见 missing。

#### 行为文档-4（doc，S）

- 线索：docs/internals/artifacts-and-evidence.md：explain 文本形态表里「诊断细节见
- 要做的：第 103 行判定行的条件补一句：「诊断细节见 worker 日志」只对运行态里带认领时刻的 job 打；由结束写记 skipped 的、运行定义不可用时由 pending 记 error 的 job 只给状态与说明。
- 文件：docs/internals/artifacts-and-evidence.md
- 先要有：「查看命令与机读输出」块 explain 两条（render.py explain_tree/explain_to_dict 按认领时刻决定是否打这句）；「状态取法与结束写」块的结束写（产生没有认领时刻的终态 job）
- 必须同批：改 render.py 这一逻辑的实装批
- 单独先落地的后果：只改文档：现在的 code 按「没有 step 记录」判断，文档会与 code 不符；测试不受影响。
- 验证：文档改动，读 diff；对应 code 由单测覆盖。
- 备注：跟「查看命令与机读输出」块的「诊断细节见 worker 日志」一条走。同一篇里第 19–21、75 行与产物表的 jobs/<enc>.json 一行把 jobs/*.json 写成判定真值、「不一致时以 jobs/*.json 为准」，第 48 行 tunnel.json 一行（行为文档-12 管）；前者随判定明细点名失真，线索没有覆盖，见 missing。

#### 行为文档-5（doc，M）

- 线索：用户指南：configuration.md 的 `[cloud]` 节键表去掉 events-table
- 要做的：configuration.md --max-concurrency 一行不再列 status（连同「接力」说明）；running-and-results.md 权限表与 getting-started.md 角色表的云端一级按 0040 派生视图改为 submit、status --wait、settle-runs：去 lambda:InvokeFunction、留 lambda:GetFunction，加条件写、s3:GetObject 与写报告，推论改为不需要任何 ECS 写权限。（[cloud] 四键、run 的云端参数、「仅 --backend cloud」段与三种组合已随「云端只支持 submit」那一批做完。）
- 文件：docs/user-guide/configuration.md、docs/user-guide/running-and-results.md、docs/user-guide/getting-started.md
- 先要有：「本机推进器、生命期锁」块删 status 的 --max-concurrency；「run 处置」块（settle-runs、status --wait 处置、删 kickoff）
- 必须同批：删 status --max-concurrency 的那一批；settle-runs 与删 kickoff 的那一批（权限表部分）
- 单独先落地的后果：只改文档：权限表少了 lambda:InvokeFunction，按文档配权限的成员在 status --wait kickoff 时被拒。测试不受影响（test_user_docs 只查措辞与链接）。
- 验证：权限表要真实验证：重新部署之后用一个只带文档所列权限的角色真实执行 submit、status --wait（含处置一次过期 run）、settle-runs，确认没有 AccessDenied。
- 备注：一条跨两块：--max-concurrency 跟删本机接力那一批；权限表跟「run 处置」块（新增处置权限），删 InvokeFunction 跟删 _STALL_KICK 那一条。getting-started.md 角色表「需要什么凭证」一列是权限的派生视图，现在写的是安装形态与凭证概述，要改多少拿不准，以 0040 决策 3 为准。settle-runs 进 configuration.md 的命令清单，线索没写，见 missing。

#### 行为文档-6（mixed，M）

- 线索：机读契约页与它的 skill 副本：写出 settle-runs 的 `--json`
- 要做的：docs/internals/cli-json-contract.md 新增 settle-runs 一节（dry_run、runs[]、outcome、reason 与落点字段），run --json 顶层 status/message 按新取法改写并加 jobs[] 全部 job 的形状，status 一节加 deadline_at 与 jobs[] 的点名标识键，list-runs 加 deadline_at；改完用 tools/render_skill_contract.py 重新生成 skill 副本；cli/tests/test_cli_json_contract.py 里 test_run_json_top_level_message_is_always_present_and_documented_as_run_level 断言的「没有执行」原句随之改。
- 文件：docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py
- 先要有：「查看命令与机读输出」块（run --json jobs[]、status --json 点名标识与 deadline_at、list-runs deadline_at、doctor report_dir.filesystem）；「run 处置」块的 settle-runs 命令；「状态取法与结束写」块（run 级取法与说明）；「判定明细点名」块（点名标识的键名）
- 必须同批：每个新增 JSON 键的那一批 code：test_cli_json_contract 用真渲染器收集全部键名、逐个断言出现在本页对应节，漏写即红；副本：test_skill.py test_contract_copy_equals_transform_of_source 断言副本等于转换结果，源页改了必须同提交重新生成；doctor 项名：test_cli_json_contract 第 333 行逐个对照 doctor 的 name 值，加 report_dir.filesystem 的 code 批必须同提交写进契约页
- 单独先落地的后果：只改文档不改 code：契约页写了 code 不产出的键，测试不红（只查 code 键在文档里），但对读者是错的；只改 code 不改文档：test_cli_json_contract 红；只改源页不重生副本：test_skill 红。
- 验证：单测够：test_cli_json_contract 与 test_skill 的差集护栏覆盖键名与副本一致；语义描述读 diff。
- 备注：一条跨四块，按键所属的 code 批拆开写，各自同提交。线索没写到、同页也要改的：artifacts.jobs_dir 一行「文件名是 URL 编码的 scope_id」（随点名改为带保存标识）；status 一节 status 行「skipped 只在全部 job 都没有执行」「aborted 只来自被中断的同步 run」与 message 行「这些 job 保持 pending」（随状态取法改）；list-runs 一节 detached 行「status --wait 对它只等待、不接力」与 --status 不再接受 skipped；doctor 一节项名表加 report_dir.filesystem（线索放在「查看命令」块，但落在本页）。见 missing。test_run_json_top_level_message_... 的文档串与断言都要改写，不只换一句原文。

#### 行为文档-7（doc，S）

- 线索：agent skill 正文按 0043 决策五骨架改：第 3 步写明云端后端的执行只经
- 要做的：SKILL.md 第 5 节与第 10 节去掉直接读 jobs/*.json 的说法，--scope 取值写成 --json 输出里的 scope_id；第 8 节删「它同时是接力」；references/cloud-backend.md「1 分工」表按 0040 派生视图改（QA/CI 一行加 settle-runs）。（第 3 节与第 7 节旗标表已随「云端只支持 submit」那一批做完。）
- 文件：cli/gherkai_cli/skills/gherkai/SKILL.md、cli/gherkai_cli/skills/gherkai/references/cloud-backend.md
- 先要有：「判定明细点名」块（jobs/ 文件名带保存标识）；「本机推进器、生命期锁」块的删本机接力；「run 处置」块的 settle-runs
- 必须同批：各条所属的实装批：test_skill.py 的 test_flags_are_attached_to_the_right_subcommand 与 test_exclusive_claims_are_true 用真 parser 核对 skill 里每个 flag 的归属，改 flag 的那一批要同提交改 skill
- 单独先落地的后果：只改 skill：agent 按新说法指导用户，但 code 里 status --wait 仍接力，属于描述先行；测试不红。只改 code 不改 skill：parser 的 flag 归属一变 test_skill 即红。
- 验证：test_skill 的 parser 对照与措辞护栏是单测；skill 行为变化按 0043 决策七的评测验证，是否要重跑评测由打磨批定。
- 备注：一条跨三块：jobs/*.json 与 --scope 跟「判定明细点名」块；第 8 节接力跟删本机接力那一批；1 分工表跟「run 处置」块。线索写「第 8 步」，实际是第 8 节「退出码分流」。线索没覆盖、同样要改的：SKILL.md「status --wait 只等待、不接力」，references/setup-and-diagnosis.md 到期一行（记 error、没有执行、接力），见 missing。

#### 行为文档-8（mixed，M）

- 线索：评测 fixture 随实装重录：文件集改为 run_meta.json、run_state.json、运
- 要做的：重录 skills/gherkai-evals/fixtures 下带录制报告的 4 个 run（wiki-search、job-failure、nova-zh、device-session-lost）：jobs/ 下的判定明细文件名带保存标识、run_state.json 每个 job 带点名的标识，占位符覆盖 report_refs[].ref；materialize.py 头注释第 15–16、36–38 行讲 jobs/*.json 的说法随之改。
- 文件：skills/gherkai-evals/fixtures/wiki-search/reports/、skills/gherkai-evals/fixtures/job-failure/reports/、skills/gherkai-evals/fixtures/nova-zh/reports/、skills/gherkai-evals/fixtures/device-session-lost/reports/、skills/gherkai-evals/materialize.py
- 先要有：「判定明细点名与落库写序」块（明细文件名与运行态点名键）；「隧道与两种 submit 的新流程」块（steps_dir 由后台推进进程读回那半句）；「报告」块（index.html/manifest 由记录生成，录出的报告形态随之变）
- 必须同批：判定明细点名那一批：新 explain 只按运行态点名的标识读明细，旧 fixture 的 run_state 没有点名键，materialize 的 integrity_check（经真 CLI 执行 explain --json）会失败、评测无法进行
- 单独先落地的后果：只重录 fixture、code 未改：新文件名旧 CLI 读不到（旧 CLI 按 scope_id 找 jobs/<enc>.json），评测坏；只改 code 不重录：pytest 不红（test_skill 只查路径与入库），但评测 harness 的完整性检查失败。
- 验证：单测不够：要在带引擎的环境里真实执行一次录制（Nova Act 与 Midscene 都要用，device-session-lost 要 Device Farm 真机），按 0043 决策七的录制约束处理，然后执行 materialize.py 的完整性检查，并跑 test_skill 的 fixture 护栏。也可以拿拿不准的转换脚本把现有 fixture 改成新形态，但这样得不到真实写出的形态，以真录为准。
- 备注：跟「判定明细点名与落库写序」块走；steps_dir 那半句跟本机 submit 新流程（「隧道与两种 submit」块）。线索说「运行态点名的各份判定明细（文件名带保存标识）」，S3 键与本机文件名是否还带 scope_id 由实装定，录制要等这一点定下。eval 27（triage-device-session-lost）的评测要求里列了 jobs/*.json 作为「先 explain 再读」的文件类，目录名不变就不用改，文件名带标识后仍匹配。重录有 AWS 与 Device Farm 费用，开发期不计。

#### 行为文档-9（doc，S）

- 线索：图：docs/diagrams/run-execution.json 的三处「四种组合」改为三种组
- 要做的：改 execution-timeout-chain.json 里「云端超时处置」「到点处置」两处标签；用 tools/build_diagrams.mjs 重出 SVG 与 HTML，图源与产物同一提交。（run-execution.json 的三种组合已随「云端只支持 submit」那一批做完。）
- 文件：docs/diagrams/execution-timeout-chain.json、docs/diagrams/execution-timeout-chain.svg、docs/diagrams/execution-timeout-chain.html
- 先要有：「词表与退役词」块
- 必须同批：加退役词表的那一提交：test_user_docs 扫图源，「超时处置」「到点处置」入表而图源不改即红；test_user_docs 的 test_diagram_exports_match_their_sources：改图源必须同提交重出 SVG/HTML
- 单独先落地的后果：图源改了不重出产物：test_diagram_exports_match_their_sources 红；退役词入表而图不改：术语测试红。
- 验证：单测（导出与图源一致、术语扫描）够；重出产物要本机有 Chrome 与 Playwright（archify 工具链）。
- 备注：跟「词表与退役词」块。grep 核对：execution-timeout-chain.json 里命中的是「云端超时处置：从定时器到点到停止 worker」「到点处置」「是否停止由到点处置的一方现查状态决定」。线索没写到的图源改动：run-execution.json 另有「status --wait 两个后端不同：本机 per-run 进程已终止时只有接力者在推进…云端仅在检测到停滞时唤醒推进函数」「submit 派生 · 可被接力」两处接力与 kickoff；execution-timeout-chain.json 另有「接力者按库里的领取时刻重算截止时刻」一句；execution-detached-gates.json 整张图讲后台标记的两道判断。见 missing。

#### 行为文档-10（doc，M）

- 线索：CHANGELOG 未发行节：讲 status --wait 接力、到期记 error、中断记 abo
- 要做的：CHANGELOG.md [Unreleased] 里接力两条、到期记 error 一条、中断记 aborted 一条直接改写为新行为（或删去），不写对照，保留与已发行版本相比的「此前……」；另加一句 run 的推进、处置与状态取法做了重构。（云端前台 run 的各条与删 SSM 两个参数的一句已随「云端只支持 submit」那一批做完。）
- 文件：CHANGELOG.md
- 先要有：「本机推进器、生命期锁」块删本机接力（接力两条）；「状态取法与结束写」块的取法与终结函数 timeout 拆行（到期与中断两条）
- 必须同批：各条所描述行为的那一批（退役词「接力推进」入表时第 59、60 行若含它会被 test_user_docs 扫到，要同提交改）
- 单独先落地的后果：只改 CHANGELOG：发行说明描述了未实装的行为；不改：每批 code 落地后条目与产品不符。测试只在退役词入表时可能红。
- 验证：文档改动，读 diff；test_user_docs 与 test_release_notes 查措辞与链接。
- 备注：一条跨两块，按条目所属的批拆开改。到期一条写「被它截断的 job 判 error、归因 timeout」「run 总状态记 error」，新设计里被期限截断的执行中 job 记 aborted、没有归因，pending 记 skipped，run 按取法为 aborted，要整句重写。线索只要求改写已有条目并加一句重构概述；settle-runs、报告目录边界检查（不支持的文件系统以退出码 2 结束）、锁已被持有时以退出码 2 结束、list-runs 新列、run --json 的 jobs[]、doctor 新项这些新的使用者可见行为要不要各写一条，线索没说，拿不准 owner 的「升级与迁移的细节不写」是否也排除新功能条目，见 missing。

#### 行为文档-11（doc，S）

- 线索：CHANGELOG 未发行节的隧道条目随隧道实装批改写为新行为，不写对照。
- 要做的：CHANGELOG.md [Unreleased] 第 64 行 --tunnel-ttl 默认值一条删去（连同 gherkai.toml 的 tunnel-ttl）；第 28 行一带的隧道条目改写为宿主进程里的 ngrok Python SDK、装 gherkai[tunnel]、令牌只取 NGROK_AUTHTOKEN、云端守护进程到终态或期限加 300 秒退出、边缘同一时刻拒绝；「后台进程还没接管就失败时隧道立即拆掉」一条按新次序改写或删去。
- 文件：CHANGELOG.md
- 先要有：「隧道（0035）与两种 submit 的新流程」块
- 必须同批：隧道实装批
- 单独先落地的后果：只改 CHANGELOG：说明与 code 不符；测试不受影响。
- 验证：文档改动，读 diff。
- 备注：跟「隧道（0035）与两种 submit 的新流程」块。第 28 行令牌换 cookie 的条目讲 ngrok 流量策略，策略仍在、只是交给 SDK，要按新写法核对而不是删。

#### 行为文档-12（doc，S）

- 线索：docs/internals 里讲隧道的三处随隧道实装批同一提交改
- 要做的：artifacts-and-evidence.md 第 48 行 tunnel.json 一行删去；verdict-model.md 第 126 行 TERMINAL_STATUSES 消费方里「隧道守护的拆除判据（tunnel_host.py：读到终态即提前拆除，否则等满 TTL）」改为守护进程的退出判据（到终态或期限加 300 秒退出）；execution-and-reconciliation.md 第 58 行 4a 流程块首行改为新次序（submit 以新会话启动后台推进进程、经标准输入交输入、回报管道；后台进程取创建时刻、起隧道、生成运行定义、建 run 并取锁、建事件库、回报、推进）。
- 文件：docs/internals/artifacts-and-evidence.md、docs/internals/verdict-model.md、docs/internals/execution-and-reconciliation.md
- 先要有：「隧道（0035）与两种 submit 的新流程」块；「本机推进器、生命期锁」块（4a 首行里的「建 run 并取锁」）
- 必须同批：隧道实装批（本机 submit 新流程）
- 单独先落地的后果：只改文档：与 code 不符；测试不受影响。
- 验证：文档改动，读 diff。
- 备注：跟「隧道」块；4a 首行同时描述生命期锁的取锁步骤，「本机 submit 由后台推进进程建 run 并取锁」在 0018 里同时出现在「本机推进器、生命期锁」块与「隧道」块，两块若不同批，这一行跟后落的那一批。4a 其余几行（接力）属行为文档-2。

#### 行为文档-13（doc，M）

- 线索：用户指南 local-app-testing.md 按 0035 的隧道新做法改
- 要做的：local-app-testing.md 按 ①–⑧ 改：第 21 行「前置」一节改为 gherkai[tunnel] 加 NGROK_AUTHTOKEN；改 docs/diagrams/local-app-testing-tunnel-topology.json 的「隧道进程」节点与图注并重出 SVG/HTML；第 66 行持有进程表删 tunnel.json、接力拆与 TTL；第 80 行「存活时间上限」整节删；第 90 行「安全」一节三处；第 98 行「限制」一节三处（含新增「同一账号同一时间只有一条隧道在线」照 0035 原句）；第 108 行「常见故障」与第 124 行日志一段改为四种启动失败说法。
- 文件：docs/user-guide/local-app-testing.md、docs/diagrams/local-app-testing-tunnel-topology.json、docs/diagrams/local-app-testing-tunnel-topology.svg、docs/diagrams/local-app-testing-tunnel-topology.html
- 先要有：「隧道（0035）与两种 submit 的新流程」块
- 必须同批：隧道实装批；图源与 SVG/HTML 同提交（test_diagram_exports_match_their_sources）
- 单独先落地的后果：只改文档：用户照文档不装 ngrok 可执行文件、code 仍要它，起隧道失败；图源改了不重出产物则测试红。
- 验证：文档部分读 diff；「限制」一节里的重连说法依据 0035 的实测，本条不需另测；用户文档用「持有隧道的进程」还是「隧道宿主」要先定（0018「写回时留下」末条，缺省沿用前者）。
- 备注：跟「隧道」块。③ 里「由 gherkai status <run_id> --wait 接力拆」一句同时属于删本机接力，隧道批若晚于删接力批，删接力那一批就要先把这半句删掉，否则文档写着已不存在的行为。所指各节都在（第 7、21、66、80、90、98、108、124 行）。

#### 行为文档-14（doc，M）

- 线索：用户指南与 README 里讲隧道的几处，与隧道的实装批同一提交改
- 要做的：running-and-results.md 第 182 行删 tunnel.json，第 74、140 行删 --tunnel-ttl，第 153 行退出码表 submit 一行补「后台推进进程在回报之前退出以退出码 2 结束、可用 settle-runs 记为已结束」，并写明 reconcile.log 之前的输出接在 submit 的标准错误上；configuration.md 第 68、167、171、204 行删 tunnel-ttl 与 ngrok config add-authtoken；troubleshooting.md 第 144–150 行症状表改为四种启动失败说法；getting-started.md 第 44 行依赖表与安装命令、根 README.md、cli/README.md、runtime/README.md 安装命令块写明 [tunnel]。
- 文件：docs/user-guide/running-and-results.md、docs/user-guide/configuration.md、docs/user-guide/troubleshooting.md、docs/user-guide/getting-started.md、README.md、cli/README.md、runtime/README.md
- 先要有：「隧道（0035）与两种 submit 的新流程」块（含 pyproject 的 [tunnel] extra）；「run 处置」块的 settle-runs（退出码表那一句提到它）
- 必须同批：隧道实装批
- 单独先落地的后果：只改文档：安装命令写了不存在的 [tunnel] extra，uv tool install 会报 extra 不存在（或静默忽略）；退出码表提到尚不存在的 settle-runs。测试不受影响（test_package_readmes 只查措辞）。
- 验证：文档部分读 diff；安装命令要真实执行一次：从构建出的 wheel 用 uv tool install 'gherkai[tunnel]' 装进干净环境，确认 ngrok SDK 被装上（这是 extras 声明的真实行为，单测不证）。
- 备注：跟「隧道」块；退出码表 submit 一行的 settle-runs 半句要求「run 处置」块已落地或同批。runtime/README.md 第 9 行是 `uv add 'gherkai-runtime[aws]'`，所指的安装块存在。configuration.md 第 68 行 [common] 一行的 tunnel-ttl 删去时，settings.py 的键集与 test_project_config 的差集护栏也会跟着动，那是 code 批的事。

#### 行为文档-15（doc，S）

- 线索：技术文档里讲隧道的几处，随隧道改为宿主进程里的 SDK 会话那一批实装
- 要做的：runtime/DEVELOPMENT.md：第 58–64 行 detached 一条删「隧道事实文件的读写」，第 66–68 行 deadline.py 一条删「与 tunnel_host.CLOUD_PER_JOB_MARGIN_S 同值」，第 74 行 tunnel.py 一条改为宿主进程里经 SDK 建隧道、5 条规则（最前一条到点拒绝）、内存交给 SDK、删按 pid 收尾，第 78 行 tunnel_host.py 一条删 TTL 算法与常量、改为到终态或期限加 300 秒退出；cli/DEVELOPMENT.md 第 175 行 0035 括注删「谁负责拆、TTL 算法」。
- 文件：runtime/DEVELOPMENT.md、cli/DEVELOPMENT.md
- 先要有：「隧道（0035）与两种 submit 的新流程」块；「随实装改写的 code 注释」块的 deadline.py 常量搬家（210 秒改在 deadline.py 定义）
- 必须同批：隧道实装批
- 单独先落地的后果：只改文档：与 code 不符；测试不受影响。
- 验证：文档改动，读 diff 对照 tunnel.py 与 deadline.py 的实际常量。
- 备注：跟「隧道」块。runtime/DEVELOPMENT.md 的 detached 一条同时被行为文档-3（删接力）改，两批分开时注意合并顺序。runtime 包新增的锁、边界检查、处置模块要不要进 runtime/DEVELOPMENT.md 的模块清单，线索没写，见 missing。

#### 行为文档-16（doc，M）

- 线索：agent skill 里讲隧道的各处按 ADR 0035 改写，与用户指南的同类改写在
- 要做的：SKILL.md 第 38 行前置改为 gherkai[tunnel] 与 NGROK_AUTHTOKEN，加入口到期限加 300 秒在边缘关闭，第 39 行 --tunnel-ttl 一条与第 73 行「仅 submit | --tunnel-ttl」一行删去；references/setup-and-diagnosis.md 第 1 节装什么加 [tunnel]，第 5 节删 PATH 前置、ngrok config、TTL、kill -9、按账号区分域名、重连说法、第 72 行排障入口删 tunnel.json/ngrok 日志/隧道已拆除，第 7 节症状表改四种说法；references/cloud-backend.md 第 94 行删 --tunnel-ttl 一句。
- 文件：cli/gherkai_cli/skills/gherkai/SKILL.md、cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md、cli/gherkai_cli/skills/gherkai/references/cloud-backend.md
- 先要有：「隧道（0035）与两种 submit 的新流程」块（删 submit 的 --tunnel-ttl）
- 必须同批：删 --tunnel-ttl 参数的隧道实装批：test_skill 的 test_exclusive_claims_are_true 与 test_bare_flags_exist_somewhere 用真 parser 核对「仅 submit：--tunnel-ttl」，参数删了 skill 不改即红；行为文档-17（评测要求是这几处改写的打分依据）
- 单独先落地的后果：只改 skill：agent 按新前置指导，code 仍要 ngrok 可执行文件；只删参数不改 skill：test_skill 红。
- 验证：test_skill 单测守 flag 归属与措辞；skill 行为按评测验证（见行为文档-17）。
- 备注：跟「隧道」块。所指各节存在：SKILL.md 第 3 节第 38–39 行、第 7 节第 73 行；setup-and-diagnosis.md 第 72 行排障入口；cloud-backend.md 第 7 节第 94 行。

#### 行为文档-17（doc，S）

- 线索：agent skill 的评测资产随隧道的行为文档同一批改
- 要做的：skills/gherkai-evals/evals.json 中 id 10、slug expose-local-app 一条：expectations 里「前置两条都提到」一条与 expected_output 的前置句改为 gherkai[tunnel] 加 NGROK_AUTHTOKEN；删「提到 --tunnel-ttl 调小会在 run 未完时无条件拆隧道」一条与 expected_output 里对应句；id 22（tunnel-origin-mismatch-and-host-block）里「域名每个 run 都会换」一句按账号区分核对；notes 记下这一轮尺子的改动。
- 文件：skills/gherkai-evals/evals.json
- 先要有：行为文档-16（skill 隧道改写）
- 必须同批：行为文档-16
- 单独先落地的后果：只改评测：with-skill 臂按旧 skill 回答会被新尺子判不过；只改 skill 不改评测：旧尺子要求提 --tunnel-ttl，新 skill 回答会被判不过。pytest 不受影响。
- 验证：要真实执行评测：按 0043 决策七的流程在 Bedrock 上跑 expose-local-app 与 tunnel-origin-mismatch 两条（with-skill 与 baseline 两臂），看新尺子下的通过率；单测不证。
- 备注：跟「隧道」块，与行为文档-16 同批。是否加「公网入口到点在边缘关闭」的新评测要求由实装批定。

#### 行为文档-19（doc，S）

- 线索：docs/user-guide/cloud-backend.md「团队成员需要的最小云端权限」一节
- 要做的：cloud-backend.md「团队成员需要的最小云端权限」一节（已改为单级）：submit + status 一级删「调用 <prefix>kicker Lambda」、保留 lambda:GetFunction，加 runs 表条件写、报告桶 s3:GetObject（卸载的运行定义正文与被点名的明细）、报告前缀 s3:PutObject，settle-runs 不给 run_id 时另需 list-runs 两项，推论改为不需要任何 ECS 写权限。（删 run --backend cloud 一级、explain 括注与单级说法已随「云端只支持 submit」那一批做完。）
- 文件：docs/user-guide/cloud-backend.md
- 先要有：「run 处置」块（settle-runs、status --wait 处置、删 kickoff 与 _make_lambda_client）
- 必须同批：删 kickoff 的那一批，以及 settle-runs 上线那一批（两者若分批，本节要分两次改）
- 单独先落地的后果：先改：按文档配权限的成员没有 lambda:InvokeFunction，现有 code 的 status --wait kickoff 会 AccessDenied。不改：处置上线后成员缺条件写与 s3:GetObject，处置与 settle-runs 失败。
- 验证：要真实验证：重新部署之后，用一个只带本节所列权限的 IAM 角色真实执行 submit、status --wait（让它处置一个已过期限加 300 秒的 run）、settle-runs（带与不带 run_id）、explain 与 list-runs，确认没有 AccessDenied；单测不证 IAM。
- 备注：跟「run 处置」块。与行为文档-5 的权限表同为 0040 决策 3 与 0033 编排进程角色的派生视图，宜同批改。0018 待定项「0033 编排进程角色没有登记 explain 读判定明细与 evidence 的 s3:GetObject」会影响本节 explain 一段的写法。

## 收尾

### 小结

这三小块的 code 改动不大，主要是收尾、跨块的连带改动与待定问题；写 code 的只有补-3、问-2 这两处，各在 S 到 M 之间。先后次序：收尾-1、收尾-2 必须排在所有实装批之后（0011 与 0051 的 Status 头那一句还要等隧道批）；补-x 各自挂在别的块的批上：补-1、补-6、补-7 已随「云端只支持 submit」那一批做完、已删去，补-2、补-3、补-4 随「云端后端」批（补-3 与补-4 是那一批开工的前置决定，补-3 还要在重新部署之后真实执行核 IAM 与名字长度），补-8、补-9 随各自对应的行为改写批。问-x 里真正挡住开工的有六组：问-6 与问-12 挡状态取法与结束写批里前台收尾的来路与重试原因；问-1 挡落库写序批的保存失败出口；问-2 挡 begin 与端口 preflight 的清理；问-11 挡词表批的范围；问-14 挡 doctor 一行；问-16 挡 _status_cmd 与 status --wait 处置读不出运行态那一支。另有一些只涉及 ADR 或用户文档：问-3、问-4、问-7、问-13 只改 ADR；问-8 要先于用户文档权限表那一批定；问-15 已有缺省。有三条已经被处理掉、与线索不符：补-5 已在 b0cd6349 里改完；问-10 的模块头已不含「决策二」；问-5 核实为到得了，只需补前提。最大的风险在收尾的残留检索：它的检索面漏了 tools/ 与 engines/，词表漏了隧道与前台云端执行的一批旧说法；Status 头那一句的删除还缺一道「实测项已逐项核并内联」的审计。不补上这两点，删掉那一句之后 ADR 会宣称已实装，而证据与残留其实还没清。

### 线索没有覆盖的改动点

- 收尾-2 的检索面漏了 tools/ 与 engines/：engines/midscene/src/worker/error-text.test.mts 有「jobs/*.json」；tools/ 是长期资产，注释同样守悬空指针红线。依据：CLAUDE.md「tools/ 是复用工具库」条。另应明确排除已被 .gitignore 忽略的 skills/gherkai-workspace/。
- 收尾-2 的检索词表漏了隧道的旧说法，它们都没有测试守（前台云端执行的旧说法已在「云端只支持 submit」那一批做过一次残留检索）。现有命中（不含 ADR 与 journey、含 tools 与 engines）：tunnel.json 31、tunnel-ttl 277（多数在被忽略的评测工作区里）、add-authtoken（tunnel.py、skill references、troubleshooting.md、local-app-testing.md、configuration.md）、「ngrok 可执行文件」56、「隧道已拆除」8、stop_tunnel 35、kickoff 22、_STALL_KICK 4、_NON_VERDICT 17、jobs_without_verdict 10、relay_available 7，以及入口页字面量「没有执行」（要按语境筛）。依据：0035 决策 1、决策 3；0027「index.html 形态」。
- 删 Status 头「尚未实装」那一句之前，缺一道实测项审计：0054「实测项（实装时逐项核，结果内联回这里）」的 23 条，以及 0034 机制三、0035 决策 1 与决策 3、0041 决策七读量等写着「实装时核」的各项，要逐项确认已真实执行、判据型结果已内联、标题里「实装时逐项核」的过程说法已改。依据：CLAUDE.md 文档纪律「Journey 吸收进 ADR」与「绿≠对」；0054「实测项」节首。
- 收尾缺 journey 自身的收口：实装全部完成后，把 docs/journey/0018-run-ownership-adr-writeback-plan.md 里的决策吸收进 ADR、过程留给提交记录，然后删去；「agent 可以自己执行 settle-runs」一条要在 journey 0013「skill 打磨批」登记指向 0043 决策五的指针。依据：CLAUDE.md「docs/journey/ 是任务推进的 staging 区」条（任务收尾即审计点）。

### 逐条

#### 收尾-1（adr，S）

- 线索：code 跟上之后，删去各篇 Status 头末尾说「这一篇描述的设计有一部分尚未实装
- 要做的：在 docs/adr/ 全部 Status 头里检索「尚未实装」，逐篇删去那一句（只删这一句，头里其余文字逐字不动）。0011 与 0051 的这一句要等隧道批落地、0051 决策 13 与 0011 隧道条文都已实装之后才能删。删之前另查一遍各篇「实测项」是否已逐项核过、结果已内联（见 missing）。
- 文件：docs/adr/0011-agentcore-browser-system-default-vs-custom.md、docs/adr/0016-execution-architecture-core-lib-run-model.md、docs/adr/0024-worker-core-protocol.md、docs/adr/0026-schedule-module.md、docs/adr/0027-runreport-aggregation-index.md、docs/adr/0028-transient-network-ssl-resilience.md、docs/adr/0030-realtime-persistence-seam.md、docs/adr/0031-job-lifecycle-states-and-severity.md、docs/adr/0033-iac-aws-backend-and-composition-wiring.md、docs/adr/0034-detached-batch-reconciler.md、docs/adr/0035-local-app-testing-via-tunnel.md、docs/adr/0037-distribution-and-packaging.md、docs/adr/0038-worker-image-delivery.md、docs/adr/0040-consumer-role-model-and-terminology.md、docs/adr/0041-agent-facing-cli-affordances.md、docs/adr/0042-step-evidence-and-explain.md、docs/adr/0043-agent-skill-for-driving-gherkai.md、docs/adr/0051-device-session-lifecycle-and-app-distribution.md、docs/adr/0053-project-config-file.md、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md
- 先要有：全部实装批（状态取法与结束写、点名与写序、生命期锁、处置、云端后端、云端只支持 submit、查看命令、报告、隧道）；收尾-2 的残留检索；各篇实测项已核并内联
- 必须同批：无
- 单独先落地的后果：不会有测试变红（Status 头形态由 test_adr_hygiene 守，删去尾句不改状态值与取代链；这一点按规则推断，没有实际执行测试确认）。提前删的话，ADR 宣称的行为与 code 不符，读 ADR 的 agent 会照着不存在的行为工作。
- 验证：grep -l 尚未实装 docs/adr/*.md 结果为空；uv run pytest cli/tests/test_adr_hygiene.py；tools/doc_rules_check.py --uncommitted 退出码 0。单测够用（纯文档）。
- 备注：现在 grep 命中的正好是线索列出的 20 篇，全在第 3 行 Status 头里，与线索一致。可以按 ADR 分批删（某篇涉及的行为都已落地时删它那一句），但大多数 ADR 跨好几批，只在最后一批之后统一删更稳。0034 的写法是「本篇」，按「尚未实装」定位能覆盖。

#### 收尾-2（mixed，M）

- 线索：实装全部完成、删 Status 头那一句之前，对 code、测试、docs/internals、docs/user-guide
- 要做的：写一个一次性的 grep 脚本，放 /tmp，不入库。按线索里的词表逐词检索所列各面，逐处判断改成现行说法还是删去；豁免已发行的 CHANGELOG 节和 ADR 里保留原文的实测记录。「超时处置」「到点处置」「接力推进」入表之后由测试守，其余各词只能靠这次检索。
- 文件：core/、runtime/、cli/、deploy_aws/、engines/、tools/、docs/internals/、docs/user-guide/、docs/diagrams/、skills/gherkai-evals/、cli/gherkai_cli/skills/gherkai/、README.md、CHANGELOG.md、各包 README.md 与 DEVELOPMENT.md
- 先要有：全部实装批；词表与退役词批（RETIRED_TERMS 入表）
- 必须同批：无
- 单独先落地的后果：不能先做：现在就检索会命中大量还在工作的 code。现状基线（不含 ADR 与 journey）：try_finalize 138 行/24 个文件，jobs/*.json 212 行，run --backend cloud 60 行/42 个文件，接力 307 行/132 个文件，load_all 48 行，expected_claim_count 34 行，四种组合 47 行，超时处置 47 行/20 个文件。
- 验证：同一个脚本再跑一遍，除豁免项外零命中；全量 pytest 加 tools/doc_rules_check.py 退出码 0。纯文本核对，单测就够。
- 备注：检索面要注意三点。第一，skills/gherkai-workspace/ 已被 .gitignore 忽略（评测的历史输出，命中很多，比如 add-authtoken、tunnel-ttl），要明确排除，否则会误判。第二，线索列的面不含 tools/ 与 engines/（见 missing）。第三，词表不含隧道与前台云端执行的旧说法（见 missing）。claim_count 101 行里有合法的诊断键用法，「物化」49 行要按语境判断，与线索说的一致。

#### 补-2（code，S）

- 线索：同上一条，并补：cli/gherkai_cli/__main__.py `_submit_cloud` 里 `detached=True` 的注释
- 要做的：把 __main__.py 第 2033 行的注释「STATE 带 detached 标记 → kicker filter 认它冷启动（同步 run 不带）」改为：标记只供 list-runs --json 的 detached 键，只作描述。
- 文件：cli/gherkai_cli/__main__.py
- 先要有：kicker 流过滤改为两条、不看 detached（stack.py _reconcile_lambdas 第 733–745 行）
- 必须同批：kicker 流过滤改写（云端后端批）
- 单独先落地的后果：先改的话，注释与现在的 code 不符（现在 stack.py 第 745 行的过滤确实认 NewImage.detached）。不影响测试。
- 验证：只改注释：doc_rules_check 加 pytest 就够。
- 备注：本机这一侧第 1759 行同类注释（「status --wait 认它可接力」）由「随实装改写的 code 注释」块的接力条覆盖，要在删接力的那一批里一起改。

#### 补-3（mixed，M）

- 线索：待定：run 两次定时触发的名字形态与 IAM 资源域定下之后，按新名字重核 0033
- 要做的：在 runtime/gherkai_runtime/names.py 定下 run 级定时触发的名字空间前缀函数（与 job_timeout_schedule_prefix 同一形态，加摘要），prefix_max_len() 改为对各名字空间取最紧的一个；stack.py 推进 Lambda 的 scheduler:CreateSchedule/DeleteSchedule 资源域加上新前缀（现在第 677–678 行只有 job-timeout-*），_validate_prefix（第 102–105 行）按新公式校验；登记进 0033 资源清单 15 与「两层命名」、0054 决策九末段。
- 文件：runtime/gherkai_runtime/names.py、deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/tests/test_stack.py、docs/adr/0033-iac-aws-backend-and-composition-wiring.md、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md
- 先要有：定下名字形态（待定项本身）
- 必须同批：kicker 收到 STATE 新建时建两次定时触发（云端后端批）
- 单独先落地的后果：名字定了而 IAM 资源域没跟上时，部署照常成功，CreateSchedule 却被拒。0054 决策九要求建不成时这次调用失败、由流重试，所以 kicker 处理 STATE 新建会一直失败重试。资源域的单侧改名就是这种失败，test_stack 的资源域断言能拦一部分。
- 验证：单测：test_stack 断言资源域、prefix_max_len 的公式。不够的部分要在重新部署之后真实执行：用最长允许长度的 prefix 部署一套，提交一个 run，核对两次定时触发都建成、名字不超过 64 个字符、IAM 没有拒绝（IAM 模拟器在这个仓库有假阳性先例，0033 第 148 行，要以真实角色为准）。
- 备注：挡住云端后端批里定时触发与权限的实装。我的判断：显然的取法是基名不长于 job-timeout，复用同一摘要长度（例如 run-timer- 加 sha1(run_id#deadline/settle) 的前 20 位），这样 prefix_max_len 不变（现为 32），两层命名的上限说法不用改；也可以与 job 超时共用 job-timeout- 名字空间，资源域就不用改，但名字与语义不符。另需注意：job 超时现在是 best-effort（失败只打日志），run 级定时触发按 0054 决策九是建不成即失败重试，两者处理失败的方式不同，共用的 arm 代码要分开处理。

#### 补-4（mixed，S）

- 线索：待定：云端处置方按 CLI 的 `--report-dir` 读被点名的明细、写报告，推进器 Lambda 用
- 要做的：先定取法，再在 runtime 的处置实现里落实。取法有三种：(a) 处置前也做 submit 那样的前缀比对（lambda:GetFunction 读两个推进器的 REPORT_DIR 环境变量）；(b) submit 时把已比对过的报告前缀写进运行定义，处置方从记录读，不用 CLI 的 --report-dir；(c) 不比对，前缀错时结束写照样写成，明细读不到、报告写到别处。
- 文件：runtime/gherkai_runtime/（处置模块，新增）、cli/gherkai_cli/__main__.py、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、docs/adr/0033-iac-aws-backend-and-composition-wiring.md
- 先要有：owner 定取法
- 必须同批：云端处置（status --wait 与 settle-runs 的云端一侧）
- 单独先落地的后果：不定也能开工本机处置；挡住的是云端处置生成报告的那一步，以及编排进程的权限清单（取 (a) 要加 lambda:GetFunction）。
- 验证：取 (a) 或 (c)：重新部署之后，用不同的 --report-dir 执行 settle-runs，核对报告落点与说明。取 (b)：单测覆盖运行定义的键，另要在真实 DynamoDB 上核 META 读回。
- 备注：我的判断：(b) 最符合唯一事实源（前缀是 run 的属性，submit 已比对过），但会改运行定义的键集（RunMeta 现在没有报告前缀字段，见 model.py 第 548–590 行），要按 0037 决策 7 的结构版本办。另外发现：云端的 status 与 settle-runs 不收 --s3-bucket（cli/gherkai_cli/__main__.py 里只有 run 与 submit 有），处置方读明细、写报告用的桶只来自 prefix 推导、环境变量或配置文件。submit 若用 --s3-bucket 指了非默认的桶，处置方会用错桶，这是同类问题，应一起定。

#### 补-5（adr，S）

- 线索：删 Status 头那句时一并核对 0027「现在做 / 留口子」的「本 ADR 上述全部决策均已实装」
- 要做的：现在没有要改的：两句已在提交 b0cd6349 里改掉。0027 第 167 行现为逐项列出已实装的内容；0041 决策七开头的「本条已实装。」已删，第 84 行只剩实测完成情况。收尾时只要再核一次：0027 第 167 行列的各项在新设计下是否仍成立，0041 Status 头「决策一、二、五已实装并有护栏」是否仍成立。
- 文件：docs/adr/0027-runreport-aggregation-index.md、docs/adr/0041-agent-facing-cli-affordances.md
- 先要有：收尾-1 同时做
- 必须同批：无
- 单独先落地的后果：无
- 验证：读两处原文核对即可。
- 备注：线索与现状不符：git log -S 显示两句都在 b0cd6349 里删改，线索写于那之前或没有同步。0027 第 167 行「cli 默认生成 RunReport」等各项在新设计下仍成立（报告改由结束那次写的写入方生成，不影响「默认生成」）。

#### 补-8（mixed，M）

- 线索：另随实装校准：docs/internals/verdict-model.md（run 级取法、job 级 skipped 来自结束写）
- 要做的：各文档跟随对应的实装批改：verdict-model.md（run 级取法、job 级 skipped 来自结束写，第 102 行「排队中的 job 起 worker 前看到它即记 skipped」等）、troubleshooting.md、local-app-testing.md、running-and-results.md 里讲接力的各处（分别有 2、1、5 处「接力」）、deterministic-step-lifecycle.md 第 83 行「三处宿主…status --wait 接力者」。（_doctor_worker_grace 文档串与 WorkerResolution.stop_timeout_s 两项已随「云端只支持 submit」那一批做完，字段连同填值删去。）
- 文件：docs/internals/verdict-model.md、docs/user-guide/troubleshooting.md、docs/user-guide/local-app-testing.md、docs/internals/deterministic-step-lifecycle.md、docs/user-guide/running-and-results.md
- 先要有：状态取法与结束写批（verdict-model）；删接力批（各篇讲接力的段落）
- 必须同批：各自对应的实装批（每批提交带上它所改行为的文档）
- 单独先落地的后果：提前改的话，文档描述的行为 code 里还没有。
- 验证：doc_rules_check 加 pytest（test_user_docs 等）；纯文档，单测够用。
- 备注：无。

#### 补-9（doc，S）

- 线索：docs/internals/verdict-model.md 与 docs/internals/execution-and-reconciliation.md 里有三处指针
- 要做的：按新行为改写两篇时，去掉两处已经悬空的条名：verdict-model.md 第 102 行「0031 决定一的注（aborted 只认主动中止…不认 timeout）」，以及 execution-and-reconciliation.md 第 140 行「0054 决策二『本机接力的改法』」。（execution-and-reconciliation.md §7 的「0034『filter 必须区分写入者』条与『兜底/接力』条」已随「云端只支持 submit」那一批改指 0016 决策 A。）
- 文件：docs/internals/verdict-model.md、docs/internals/execution-and-reconciliation.md
- 先要有：状态取法与结束写批、删接力批、kicker 过滤改写批里对这两篇的改写
- 必须同批：这两篇随行为改写的那几批
- 单独先落地的后果：单独去掉指针是安全的，只是三处所在的句子本身也是旧行为，单改指针要再改一次。
- 验证：差集法：从两篇抽出所有「ADR NNNN『条名』」，到对应 ADR 里 grep 条名，零缺失。
- 备注：两处都已确认存在。第 140 行那一格整格都在讲接力判超时（「接力者按…补写」），删接力时整格重写，指针随之消失。

#### 问-1（mixed，S）

- 线索：本机 run 运行期失败的退出码，0030 决定七写的是「非零」，要定成 1
- 要做的：定下之后：若定成 1，在 0031 决定五写全；若维持「非零」，ADR 不改。code 一侧：删云端分支之后，_cmd_run 第 3151–3157 行的 need_cloud 兜底（return 1）随之删去，本机的存储异常现在是未捕获异常（Python 以 1 退出并打出回溯）。保存明细重试失败、推进器退出的路径要定是否捕获并给一句说明。
- 文件：docs/adr/0031-job-lifecycle-states-and-severity.md、docs/adr/0030-realtime-persistence-seam.md、cli/gherkai_cli/__main__.py、core/tests/test_schedule.py
- 先要有：无
- 必须同批：判定明细点名与落库写序批（保存失败重试 3 次后推进器退出）
- 单独先落地的后果：不定也不挡大多数开工；挡住的是落库写序批里「保存失败 → 推进器退出 → 前台 run 以什么退出码结束」的实现与测试断言。
- 验证：单测：注入一个抛出的 store，断言退出码与 stderr 不含回溯。本机真实进程可以补一次：把报告目录设成只读，执行一次 run。
- 备注：我的判断：维持「非零」，不在 ADR 里定死 1。理由一：1 在 0031 决定五里表示「判定不是 passed」，运行期存储失败并不是判定。理由二：照「不需要的承诺不要写」，写成 1 是没有人依赖的保证。实现上给一句产品语言的说明、不打回溯即可，测试块已把相关断言改为「非零」（test_on_event_exception_propagates_as_is_without_verdict_and_stops_workers）。

#### 问-2（mixed，M）

- 线索：RunPersistence.begin 在 create_run 之前调三个 store 的 preflight，run 只有本机后端之后全是 no-op
- 要做的：若定为删：persist.py 第 98–104 行去掉三次 preflight 调用及文档串第 85–87 行的理由；ports.py 第 217、261、288 行的 preflight 方法与六个 adapter 的 preflight（run_store/result_store/report_store 的 local、ddb/s3）一并删，core/tests/test_persist.py 的假 store 随之改；0030 决定七「Store port 有 preflight()」一段改写或删去，保留一条被拒方案作护栏。
- 文件：core/gherkai_core/persist.py、core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/adapters/result_store/local.py、core/gherkai_core/adapters/result_store/s3.py、core/gherkai_core/adapters/report_store/local.py、core/gherkai_core/adapters/report_store/s3.py、core/tests/test_persist.py、docs/adr/0030-realtime-persistence-seam.md
- 先要有：无（_cmd_run 的云端分支，即云端 store 经 RunPersistence.begin 的唯一路径，已随「云端只支持 submit」那一批删去）
- 必须同批：无
- 单独先落地的后果：无：云端前台 run 已删，删 preflight 不改变任何退出码。
- 验证：单测够用：全部 preflight 调用方只剩 persist.py 第 100–103 行（grep 已核）；云端 submit 走 compose.preflight_cloud_resources，不经 Store.preflight。
- 备注：挡住 begin 的清理与「随实装改写的 code 注释」块里 RunPersistence.begin 一条（「以云端桶名错分裂退出码为理由」）。我的判断：显然的取法是删。调用方只有 begin，本机 adapter 全是 no-op，留着就是不存在组合的接口面；以后 WebUI 在云端用 RunPersistence 时再加。由 owner 定。

#### 问-3（adr，S）

- 线索：0030 决定五「Map 形状下 update_job_state 各 scope 互不干扰」一句与云端记下终态时对 jobs 整体替换
- 要做的：改写 0030 第 239 行：Map 形状让写入口能按 scope_id 定位单个 job；本机是锁内读改写，云端认领与投影按单元素写，记下终态与结束写以写入序号为条件、对 jobs 整体替换（指 0034 机制三②）。
- 文件：docs/adr/0030-realtime-persistence-seam.md
- 先要有：无
- 必须同批：写入序号与终态写的实装（云端后端批）同一提交，或之前单独改
- 单独先落地的后果：无（只改 ADR）。
- 验证：读原文对照 0030 第 283 行「RunState.jobs 落 DDB 用原生 Map」段与 0034 机制三②，两处说法一致即可。
- 备注：不挡任何 code。我的判断：要补，因为第 283 行同一篇里已经写明终态写对 jobs 整体替换，第 239 行「互不干扰」与它直接矛盾。

#### 问-4（adr，S）

- 线索：0030 决定六「形态变更」条与 status_group 写入规则里索引迁移、旧版 CLI 写出的记录的叙述
- 要做的：清理 0030 决定六写入规则里讲「早于本形态写出、还没有 status_group 的 STATE」（迁移而来的记录、旧版 CLI 写出的记录）的那段及其处理。「改用状态分组索引的那次索引迁移的实测」与「这次没有核」两条是否保留由 owner 定。
- 文件：docs/adr/0030-realtime-persistence-seam.md、docs/adr/0038-worker-image-delivery.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无。code 里没有兼容缺分组属性的分支（grep 缺分组、早于本形态、旧版 CLI 都没有命中），所以只改 ADR。
- 验证：读原文；改后再 grep「旧版 CLI」「早于本形态」，只剩有意保留的历史记录。
- 备注：不挡 code。我的判断：旧记录的兼容叙述删去，依据是「没有用户之前不背兼容包袱」。迁移实测建议保留：它是 0037 决策 7「后端形态变更的迁移口径」的判据型证据（一次更新只能增删一个 GSI、部署完成不等于索引就绪），将来改索引形态时要用。0038 清理 pass 条的「残余风险」引用了旧版 CLI 写出的记录，要一并核对。

#### 问-5（mixed，S）

- 线索：0031 决定一「scenario 级 SKIPPED」条列的「scope 级 error 之后因主动中止得出 aborted」
- 要做的：核实的结论是到得了，只需在 0031 第 59 行补上前提：worker 先报 scope 级 error、再以非零退出码结束（内容不完整）时，才会落入真值表的 abort 或期限那两行；干净退出的 scope 级 error 内容完整，保留 ERROR。可以在 core/tests/test_termination_parity.py 的同步路径矩阵里补这一行。
- 文件：docs/adr/0031-job-lifecycle-states-and-severity.md、core/tests/test_termination_parity.py
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无
- 验证：单测够用（纯逻辑）：在 schedule 层注入事件序列「scope_done{status:error} 之后 abort_flag 置位、worker 以 1 退出」，断言 ABORTED 且合成的明细保留。
- 备注：我的判断（读 code 得出）：同步路径可达。schedule.py 第 571–580 行：exit_code≠0 时 _content_complete 置回 False；stop_reason 仍为 none 而 abort_flag 已置位时 decide_stop 落定 abort，经真值表第 185 行得 ABORTED。无状态路径没有 abort，但截止时刻之后非零退出时按第 184 行（期限截断）得 ABORTED，同样可达。0034 真值表第 186 行「先报了 scope 级 error 再非零退出的」承认 worker 会这样退出。不挡实装。

#### 问-6（mixed，S）

- 线索：同一次前台执行里已过停止启动、又出现 fail-fast 或使用方中断时，结束写取哪一个来路的说明
- 要做的：定下规则后：schedule 向 RunPersistence.finalize 交出结束写的来路（现在 _StopStart 与 _AbortFlag 是两个独立的登记点，见 schedule.py 第 203–240 行），finalize 的结束写按来路取 0031 说明表的一行；0031 决定三「结束写」小节与 0054 决策二补写规则。
- 文件：core/gherkai_core/schedule.py、core/gherkai_core/persist.py、docs/adr/0031-job-lifecycle-states-and-severity.md、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、core/tests/test_schedule.py、core/tests/test_persist.py
- 先要有：结束写入口（端口新方法）
- 必须同批：前台没有启动的 job 不再构造 skipped、由 RunPersistence.finalize 结束写记 skipped（状态取法与结束写块）
- 单独先落地的后果：不定的话，前台结束写的来路参数没法实现：这一条挡住状态取法与结束写批里前台收尾那部分。
- 验证：单测够用：注入时钟与中止标志，覆盖两种先后，断言运行态里的说明。
- 备注：run 状态不受影响（按取法，fail-fast 必有 error；中断与到期都是 skipped 或 aborted），只有说明不同。现在 run_verdict（project.py 第 830 行）是「已过停止启动」优先于中断。我的判断：显然的两种取法，一是沿用现行的固定优先（到期在先，与排队 job 的检查次序一致），二是按最先登记（与 0054 决策二「中止的说明取最先成立的那个来源」同一原则，要把 _StopStart 的成立也登记进同一个先后序）。后者更忠实于「最先成立」，也与问-12 要统一的方向一致。交 owner。

#### 问-7（adr，S）

- 线索：0042（第三节标题、决策七的问题段与被拒方案、「不做 / 延后」与重议、云端交付链的实测记录）与 0027
- 要做的：逐处判定：决策正文（0042 第 110 行第三节标题、第 191 行决策七问题段、第 206 行被拒方案、第 227 行重议）换成「判定明细」；验证与实测记录（第 257、275 行）作为历史保留原文。0027 两处同样处理。
- 文件：docs/adr/0042-step-evidence-and-explain.md、docs/adr/0027-runreport-aggregation-index.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无
- 验证：grep 'jobs/\*' 只剩判为历史记录的几处。
- 备注：0042 有 10 处，0027 有 2 处。不挡 code。收尾-2 的检索面不含 ADR，所以这一条不会被收尾检索兜住，要单独做。

#### 问-8（adr，S）

- 线索：0033 编排进程角色没有登记 explain 读判定明细与 evidence 所需的 s3:GetObject
- 要做的：在 0033 第 48 行「explain 补取…」那一句旁登记：explain 读被点名的判定明细与 evidence 对象需要报告桶前缀下的 s3:GetObject，不需要 s3:ListBucket（0042 决策四、「查看命令」块 explain 条）。
- 文件：docs/adr/0033-iac-aws-backend-and-composition-wiring.md、docs/adr/0040-consumer-role-model-and-terminology.md、docs/user-guide/cloud-backend.md、cli/gherkai_cli/skills/gherkai/references/cloud-backend.md
- 先要有：无
- 必须同批：cloud-backend.md「团队成员需要的最小云端权限」一节的改写（行为文档块）
- 单独先落地的后果：无
- 验证：读原文：0033 编排进程角色段与 0042 决策四一致，用户文档的权限表是它的派生视图。
- 备注：已确认 0033 第 48 行只有 explain 的 events 表 Query，没有 S3 读；处置方一条已写明 s3:GetObject。我的判断：要补。0042 决策四写了需要它，用户文档第 162 行也说了「判定明细与证据对象的读权限」，只差权威登记。挡住的是用户文档权限表那一批，必须先定。

#### 问-9（code，S）

- 线索：只写「ADR 0034」的整篇指针紧邻的描述与 0034 端到端 cloud 1b 相反
- 要做的：留给实装批：哪一批改 kicker 流过滤与 handler 分流，就在同一提交里改这些描述（指针随之落到「端到端 cloud 第 1b 步」或去掉）。现在不动。
- 文件：core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/model.py、core/tests/test_ddb_run_store.py、cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/compose.py、runtime/gherkai_runtime/detached.py、deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、cli/tests/test_main.py
- 先要有：kicker 流过滤与 handler 分流的实装（云端后端批）
- 必须同批：同上
- 单独先落地的后果：现在就改描述的话，注释会与 code 不符：ddb.py 第 19、209、272 行与 stack.py 第 733–745 行描述的正是现在 code 的行为。
- 验证：随所在批的 pytest 与 doc_rules_check。
- 备注：我的判断：显然留给实装批。这些描述对现在的 code 是真的，只是与 ADR 的目标相反；提前改会让注释与 code 失配，换来的只是指针形式上一致。「按 detached 分流的描述」一条（随实装改写的 code 注释块）已经列了同一批位置，两条合一处理。

#### 问-10（test，S）

- 线索：core/tests/test_conditional_writes.py 模块头的「ADR 0054 决策二/五」在该文件里已没有决策二的依据
- 要做的：现在没有要定的：模块头第 1 行现为「ADR 0034 机制三/机制四、ADR 0054 决策五、ADR 0030 决定四」，已经不含「决策二」。剩下的是随结束写的实装改模块头里 try_finalize 与「机制三 finalize 单调」的说法（测试块已登记）。
- 文件：core/tests/test_conditional_writes.py
- 先要有：结束写入口
- 必须同批：改写 test_conditional_writes 的那一批
- 单独先落地的后果：无
- 验证：grep -n 决策二 core/tests/test_conditional_writes.py 为空（已核）。
- 备注：线索与现状不符：这个问题已经被处理掉了。模块头第 9 行「机制四 CAS」在改写时可顺手换掉；退役词「CAS 认领」「CAS claim」「CAS 抢占」不按字面命中它，但属于同一个旧名。

#### 问-11（mixed，M）

- 线索：退役词表加哪些：owner 定的是「接力推进」「超时处置」「到点处置」进表
- 要做的：定下名单后改 cli/tests/_doc_rules.py 的 RETIRED_TERMS_WORDS，同一提交清掉人读层与 code 注释里的命中（RETIRED_TERMS_IN_CODE 也扫注释）。test_user_docs 只要求表内的词都在 CONTEXT 的 _Avoid_ 里，五个候选词都已在 CONTEXT 第 246、264、290 行的 _Avoid_ 里。
- 文件：cli/tests/_doc_rules.py、core/tests/test_conditional_writes.py、（随命中的 code 注释、技术文档与用户文档）
- 先要有：无
- 必须同批：词表与退役词批
- 单独先落地的后果：先加词再清会让 test_user_docs、test_skill 与注释护栏变红（「先加表测试即失败」）。
- 验证：单测够用：全量 pytest 加 tools/doc_rules_check.py。
- 备注：挡住词表与退役词批的范围。现有命中数（不含 ADR 与 journey）：到期收尾 33、收尾写 45、发起进程标识 1、进程核对 3、遗留 run 收尾 0、推进方 15。我的判断：「遗留 run 收尾」「发起进程标识」「进程核对」命中极少，随三个词一起进表代价很小；「到期收尾」「收尾写」的命中几乎都在 try_finalize 一带的 code 与测试注释里，那些注释会被结束写批整段重写，所以这两个词宜在结束写批（或收尾）时进表，不放在最早的词表批里，省得同一段注释改两次。「收尾写」作子串，要防「收尾写下」一类误伤，入表前先看一遍命中的语境。

#### 问-12（adr，S）

- 线索：上面「结束写取哪一个来路」一条的相关问题：0054 决策二、0026「起 worker 与重试之前的检查」
- 要做的：定下检查次序的依据，以及等待重试的 job（按固定次序取最先命中的原因，_Worker._retry_refused）与执行中的 job（按最先登记取原因，_AbortFlag）是否统一取法。写进 0054 决策二，0026、0028 改为指过去。
- 文件：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、docs/adr/0026-schedule-module.md、docs/adr/0028-transient-network-ssl-resilience.md、core/gherkai_core/schedule.py
- 先要有：无
- 必须同批：问-6 同时定
- 单独先落地的后果：不定的话，_retry_refused 注明的原因（重试之前的检查按分支落实，状态取法与结束写块）照现行次序实现，日后改取法要再改一次 code 与测试。
- 验证：单测：重试退避期间先后让两种原因成立，断言注明的原因。
- 备注：我的判断：次序里「已发现 run 被别处结束」的位置不影响记录。它在哪一步命中都不写终态，而且写也写不成（0054 决策五），所以只有「已过停止启动」与「fail-fast 或中断」两者的先后决定注明的原因。显然的统一取法是都按最先登记，与执行中的 job 一致；固定次序只剩一条可写的依据：时间检查不依赖任何其它状态。交 owner，与问-6 一起定。

#### 问-13（adr，S）

- 线索：0016 决策 C「证据边界」一条：profile-only 的那次真实执行走的是 run --backend cloud
- 要做的：owner 二选一：一是恢复原句作为实测快照，另加一句现状；二是保留现在的写法、注明证据来自 Fargate 一路，并说明 subprocess 一路是否补一次真实执行。
- 文件：docs/adr/0016-execution-architecture-core-lib-run-model.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无
- 验证：若补真实执行：在跳板机上不设 --region、AWS_REGION、AWS_DEFAULT_REGION，只靠 profile config 里的 region，执行一次带引擎的本机 run（两个引擎各一次），确认 store 与 subprocess worker 都拿到同一 region、没有出现 NoRegionError。
- 备注：不挡 code。我的判断：选二并补那次真实执行。开发期 AWS 费用不算决策变量，而「绿≠对」要求依赖真实行为（boto3 从 profile 解析 region）的结论有真实执行做证据；删了前台云端执行之后，Fargate 那一路的证据也已不再覆盖现行设计的 CLI 一侧。

#### 问-14（mixed，S）

- 线索：doctor 的报告目录一项，项名 report_dir.filesystem（report_dir 组）是写回时执笔自定的
- 要做的：确认项名之后实装 doctor 的 section=report_dir、name=filesystem 一行，契约页 docs/internals/cli-json-contract.md 第 247 行 name 表与 section 取值加上它，skill 副本经 tools/render_skill_contract.py 重出，cli/tests/test_cli_json_contract.py 第 374 行附近的项名集合加上它。
- 文件：cli/gherkai_cli/__main__.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py、docs/adr/0041-agent-facing-cli-affordances.md
- 先要有：边界检查的共用判断（runtime 新模块）
- 必须同批：doctor 新增 report_dir.filesystem（查看命令与机读输出块）
- 单独先落地的后果：不定也能写边界检查本身；挡住的只是 doctor 那一行与契约页。
- 验证：单测：契约护栏。另在本机 APFS 与跳板机的 ext4 上各执行一次 doctor --json（真实文件系统类型取法要真实执行，fstatfs 与 mountinfo 不能只靠 mock）。
- 备注：我的判断：显然可以沿用。现有各项都是「section.name」形态（steps.dir、config.file、backend.worker.grace），机读输出里 section 与 name 分开（__main__.py 第 817 行），report_dir.filesystem 即 section=report_dir、name=filesystem，与现有命名一致，组名与 --report-dir 旗标同词。

#### 问-15（doc，S）

- 线索：用户文档里隧道宿主的叫法：ADR 0035 决策 3 的表头和 0016 用「隧道宿主」
- 要做的：按缺省：用户文档统一用「持有隧道的进程」，不进 CONTEXT 词表；改 local-app-testing.md 拆除时机表时三行写成前台 run 的 CLI 进程、本机 submit 的后台推进进程、云端 submit 的本机隧道守护进程，同一叫法用到 running-and-results.md、troubleshooting.md 与 skill 的 references/setup-and-diagnosis.md。
- 文件：docs/user-guide/local-app-testing.md、docs/user-guide/running-and-results.md、docs/user-guide/troubleshooting.md、cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md
- 先要有：无
- 必须同批：隧道实装批的行为文档
- 单独先落地的后果：无
- 验证：grep「隧道宿主」在用户文档与 skill 里为零；test_user_docs、test_skill 通过。
- 备注：挡住隧道批的用户文档改写，缺省已给。我的判断：同意缺省。「宿主」在用户文档与 skill 里本来不用，用户层是产品说明口吻（ADR 0045），「持有隧道的进程」不必立新术语。

#### 问-16（mixed，S）

- 线索：下面「删除过程文档之前找到、ADR 里还没有的内容」一块里另有两个待定：提示里的 `gherkai status`
- 要做的：两件事。(1) _status_cmd（__main__.py 第 1862 行）是否带上显式给出的 --config；同一批里它还要按已定规则带上显式给出的 --ddb-table、--region。(2) 运行态解析不了时，不带 --wait 的 status 以退出码 2 结束；带 --wait 的是只等待并说明原因（0054 决策八现行写法），还是同样以退出码 2 结束。定下之后改 0031 决定五、0054 决策八与 0037 决策 7。
- 文件：cli/gherkai_cli/__main__.py、docs/adr/0042-step-evidence-and-explain.md、docs/adr/0031-job-lifecycle-states-and-severity.md、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、docs/adr/0037-distribution-and-packaging.md、cli/tests/test_main.py
- 先要有：无
- 必须同批：_status_cmd 的拼法改动（查看命令块）；status 与 status --wait 的处置轮询（run 处置块）
- 单独先落地的后果：(1) 不定挡 _status_cmd 那条实装；(2) 不定挡 status --wait 处置循环里读不出运行态那一支，以及本机 status、explain 捕获解析失败的那条实装。
- 验证：单测：损坏的 run_meta.json 与 run_state.json 各一例，断言退出码与终端没有回溯；--config 的拼法断言命令串。
- 备注：我的判断，(1)：带上显式给出的 --config。规则本身说「来自配置文件的值不另带，因为同一目录照抄会取到同样的值」，这个前提只对当前目录的 gherkai.toml 或 GHERKAI_CONFIG 成立；显式 --config 指向别处时，不带它照抄会取到不同的值。(2)：两者都以退出码 2 结束更合理。本机的运行态是先写临时文件再 rename 的原子写（run_store/local.py 第 50 行），读不出就是永久损坏或由更新的版本写出；按 0054 决策六末条，没有任何处置方能对它做条件写，--wait 只等待会永远不返回。交 owner。

## 删除过程文档之前找到、ADR 里还没有的内容

### 小结

这一块 11 条，code 量合计不大（多是 S），主要成本在 ADR 改动和 owner 的确认。按性质分三类。（一）纯 ADR、可以现在就写：补-2（Docker Desktop 证据）、补-4（0043 允许 agent 执行 settle-runs）、补-9 的 ADR 那一句、补-8 的「括注按 deadline_at 本身计」。（二）先写进 ADR，但要 owner 先确认理由或取舍：补-1（被拒方案，理由不是原话）、补-3（status 命令拼法；--config 带不带待定）、补-5（解析不了时的出口；「只等待」是否有意取代退出码 2 待定）、补-6（存储访问失败的定义与退出码 2）、补-11（版本不认仍按锁处置）。（三）只是实装细节：补-7、补-10，补-8 的计时取法。

分批归属：补-3、补-5 的非 --wait 部分、补-8、补-9 归查看命令批；补-5 的 --wait 部分、补-6、补-7、补-10、补-11 归 run 处置批（settle-runs 与 status --wait），它们都依赖 runtime 包里的处置判定、结束写入口和生命期锁；补-1、补-2 归边界检查批。

可以先于大改单独落、不留窗口的：补-9 的云端读法（CLI 一侧，不用重新部署）、补-3 的 _status_cmd 拼法、补-5 里「status、explain 遇到损坏文件以 2 结束」的修复（现在是回溯）。处置批内部的次序：处置判定与结束写在前，补-6、补-10、补-11 在其上，补-7 随 settle-runs 命令一起落。读期限的端口形态（头部读取带 deadline_at）是补-8 与补-10 的共同前提，宜在查看命令批或处置批开头一次定下。云端真实验证只有补-6 要（只读身份做结束写），它依赖新的 runs 表写法，要排在云端批重新部署之后。

最大的风险有两处。一是补-11 和运行定义不可用的路径都会碰到「结束写写成了，报告却需要运行定义」的空缺。二是处置批里本机与云端的失败分类（解析失败、访问失败、写被挡下、写失败）要两个后端说法一致，现在云端的「云端不可达」兜底会把写权限不足误说成不可达。

### 线索没有覆盖的改动点

- 云端运行态解析失败没有出口：_status_cloud 和云端 explain 只接 botocore 异常；STATE 状态值本版本不认识（_run_state_from_item 里 Status(item["status"]) 抛 ValueError）或形态违约（KeyError）时，回溯直接打到终端。补-5 第三段只写了本机，而 0054 决策八「运行态本身读不出时只等待并说明原因」是两个后端通用的，0041 决策七的云端列举也已把这类行列为无法读取。位置：cli/gherkai_cli/__main__.py 的 _status_cloud 和云端 explain 分支（约第 2700 行）；core/gherkai_core/adapters/run_store/ddb.py 的 load_run_state。
- 本机存储访问失败在 status、explain 里没有出口：load_run_state、peek_definition_header 遇到 PermissionError 一类 OSError 时是未捕获的异常。补-6 定的判据（访问失败按读不到这个后端，以退出码 2 结束、不进入等待，与 0041 决策七「读不到」一致）只点了 status --wait 和 settle-runs，不带 --wait 的 status 和 explain 也该按同一判据以 2 结束。位置：cli/gherkai_cli/__main__.py 的 _cmd_status_body、_cmd_explain；依据：0041 决策七「退出码」条（本机报告落点不可读即 2）、补-6。
- 云端 status --wait 处置时，结束写因权限不足失败的说明：现在 _status_cloud 把所有 botocore 异常都报成「云端不可达（表/凭证/region）」，处置时条件写被 AccessDenied 拒绝，这句会误导。要另给一句点名缺 runs 表条件写权限、并指向权限说明的话。位置：cli/gherkai_cli/__main__.py 的 _status_cloud 兜底 except；依据：补-6、0054 决策八「云端用户一侧的处置方」条、0033 编排进程角色。
- 提示里的 status 命令在云端不带显式给出的 --report-dir（云端报告前缀）。status --wait 改为会处置之后，要按 --report-dir 读被点名的明细、写报告；照抄提示执行时，会把报告写到默认前缀。补-3 的规则只带 --ddb-table、--region。依据：0054 决策七（写成的一方生成报告）、决策八；0043 决策五骨架第 3 条（云端读判定明细用的 --report-dir 也要一致）；与「核对时补上的条目」里「云端处置方按 --report-dir 写报告、是否比对报告前缀」那一待定项相关。位置：cli/gherkai_cli/__main__.py 的 _status_cmd。
- 运行定义读不出时，处置写成之后的报告怎么生成，ADR 和线索都没有写：0027「index.html 形态」要求由结束写结束的 job「按运行定义的次序」排、以 job 定义为骨架。补-11（结构版本不认仍按锁处置）、本机期限读不出时只按锁处置、0037 决策 7 里推进器以 error 变体结束，这三条路径都会走到「结束写写成，运行定义却读不出」。要定：这时不生成报告，还是只按运行态生成退化的报告。依据：0027「ReportStore 接口：整 run 一次写」与「index.html 形态」；0054 决策七；0037 决策 7。位置：报告块里「从记录组装 RunResult」的那一处（core/gherkai_core/reconcile.py 的 finalize_report）。
- journey 0013 第 66 行（skill 打磨批欠账）现在指向 0018「实装」一节里的这一块。这一块的内容吸收进 ADR 后会删掉，那里的指针要改成指 0043 决策五（补-4 落下之后），否则就悬空了。位置：docs/journey/0013-mobile-devices-implementation.md。

### 逐条

#### 补-1（adr，S）

- 线索：run 目录不过边界检查时 status --wait 只读地等到终态、不处置
- 要做的：只在 ADR 0054「被拒方案」里加一条（放在「macOS 只看本机标志」之后），记下「只读地等、不处置」为什么不取。目标行为已经在决策四里：未结束的 run 上 status --wait 做边界检查，不过即以退出码 2 结束。code 一侧的落实归「本机推进器、生命期锁与边界检查」块里的边界检查条：status --wait 先读运行态，已是终态直接渲染、不做检查；未结束时对 run 目录的描述符做检查，不过即以 2 结束，说明写原因、检测到的类型与清单。
- 文件：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无，只改 ADR。
- 验证：ADR 一侧要过独立复核，理由要 owner 确认。行为一侧随边界检查批真实执行，即 0054 实测项 14：在 macOS 的 SMB、HFS+ 磁盘映像和 Linux 的 NFS、FUSE 上各起一个未结束的 run，看 status --wait 是否以 2 结束；单测不够，因为文件系统类型的判断依赖真实挂载。
- 备注：属于边界检查批，这一条本身是设计层的被拒方案，要先进 ADR。现在的 code 没有任何边界检查：_cmd_status_body 对未结束的 run 要么接力（detached.drive_local_reconcile），要么经 _wait_local_terminal 只读地等，后者正是这条要拒的做法（_WAIT_WITHOUT_RELAY_NOTICE 还写着「可按 Ctrl-C 停止等待」）。条文的理由是审计者从决策四、八推出来的，不是 owner 原话，要 owner 确认。「已是终态时不检查」在决策三里只是隐含的（试拿锁只对未结束的 run），被拒方案里写明就够了。

#### 补-2（adr，S）

- 线索：macOS 的 Docker Desktop 取证里 ADR 没有带上的事实
- 要做的：把 0054 决策四「产品边界」一条（第 108 行）里 Docker Desktop 的括注换成审计给出的全文：fakeowner 被拒、宿主一侧 APFS 放行、两个方向目录锁与文件锁都互不阻挡、命名卷 ext4 放行且在边界之内、命名卷上的锁行为未逐项核过。实测项 13 末尾补一句：在 Docker Desktop 命名卷上照做决策三理由的各项。
- 文件：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无，只改 ADR。
- 验证：ADR 改动过复核即可。新加的实测项要在 macOS 的 Docker Desktop 上真实执行：两个容器共用一个命名卷，照决策三理由逐项核目录 flock 与事件库 POSIX 记录锁，在边界检查和生命期锁那一批做。
- 备注：这一条是证据，没有新决定，可以现在就写进 ADR，不必等实装。原始记录在 4dbb0dc7 删掉的设计稿里（git show 4dbb0dc7 能找回），那里还写着 VirtioFS 和「容器之间互斥」，新括注没带 VirtioFS；「容器之间」现在的正文已经覆盖。这台机器上我没能复核这些数。按「ADR 的实测项保持简短」，补进第 13 条的那一句宜短。现在的 code 没有边界检查，这一条不影响 code 行为。

#### 补-3（mixed，S）

- 线索：提示里的 gherkai status 命令怎样拼
- 要做的：ADR：规则写进 0042 决策四「未终态的 run」段，或者写进 0041 决策六由 0042 指过去，二选一。0054 决策五末条补一句：说明里给出查看这条记录的 status 命令。code：_status_cmd(run_id, *, report_dir, prefix, wait) 加 ddb_table、region 两个形参，只在 args.ddb_table / args.region 不是 None（即命令行显式给出）时带上，不带 --profile；调用处（_submit_local、_submit_cloud 的两处、_cmd_status_body、_status_cloud、_cmd_explain 的两处）把 args 里的值传进去。_ended_elsewhere_notice 加 report_dir 参数，在说明末尾给出 status 命令。running-and-results.md 退出码表的 run 一行补上「已被别处记为已结束：stdout 为空，退出码 1，中断时 130/143」。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_main.py、docs/user-guide/running-and-results.md、docs/adr/0042-step-evidence-and-explain.md、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、docs/internals/cli-json-contract.md
- 先要有：owner 定 --config 带不带
- 必须同批：无
- 单独先落地的后果：_status_cmd 的改动可以单独先落：现在的 code 只是少带两个参数，补上不破坏任何东西。test_main.py 第 3117、3560 行与第 3917 行起逐字断言提示串的用例，按新拼法改。_ended_elsewhere_notice 加命令也可以先落，run 已经能走到这个出口。
- 验证：拼串是纯逻辑，单测够：显式 --ddb-table/--region 带上，来自配置文件或环境变量的不带，--profile 恒不带，带空格的路径用 shlex 引号。
- 备注：属于「查看命令与机读输出」批，规则是用户可见契约，先写进 ADR。现在的 code：_status_cmd 只给本机的 --report-dir 或云端的 --backend cloud --prefix；_ended_elsewhere_notice 不给命令。判断「显式给出」容易：ddb_table 和 region 属于 ENV_LAYER_OPTIONS，配置文件的值只进 args.config_values，不写回 args，所以 args.ddb_table / args.region 不是 None 就是命令行给的。疑点有两处。其一，云端的 status --wait 改成会处置（写结束写、按 --report-dir 指的报告前缀写报告）之后，提示里的命令不带显式给出的 --report-dir，照抄执行时报告会写到默认前缀（见 missing）。其二，relay 提示删掉之后，status 自己不再打 status 命令，新的期限提示里也没有整条命令，所以「各处提示」实际只剩 submit、explain 和 run 被别处结束这三处。

#### 补-4（adr，S）

- 线索：agent 可以自己执行 settle-runs
- 要做的：只改 ADR 0043 决策五：任务域 A 的命令列表加上 settle-runs；骨架第 8 条「退出码分流」后面接审计给的那段（0/2 的含义，看 --json 的 runs[].outcome/reason，agent 不必先请使用者确认、但要先 --dry-run，用到它的场合）。skill 正文怎么写留给 skill 打磨批，journey 0013 里登记的「settle-runs 放在哪里教」补一个指向 0043 决策五的指针。
- 文件：docs/adr/0043-agent-skill-for-driving-gherkai.md、docs/journey/0013-mobile-devices-implementation.md
- 先要有：settle-runs 命令的 ADR 形态（0054 决策八，已有）
- 必须同批：无
- 单独先落地的后果：无。ADR 先于命令写下，按 Status 头那句「有一部分尚未实装」处理。
- 验证：ADR 过复核即可。skill 一侧到打磨批用评测验证（evals 补 settle-runs 场景），这一批不需要真实执行。
- 备注：这是 owner 2026-11-15 定的设计决定，要先进 ADR。现在的 code 和 skill 里都没有 settle-runs（grep 不到）。骨架第 8 条现在只列 submit/plan/list-runs/explain/doctor 只表做成没做成，settle-runs 进来时要一起列。journey 0013 第 66 行现在指向 0018 的这一块，这一块吸收之后会删，那里的指针要改成指 0043 决策五，不然就悬空了。

#### 补-5（mixed，M）

- 线索：提交记录或运行态本身解析不了时的出口
- 要做的：code：LocalRunStore.peek_definition_header 与 load_run_state 解析失败（JSONDecodeError、顶层不是对象、形态违约、状态值不认识）时抛一个契约类异常（比如 DefinitionContractError，或者新加一个 RunStateUnreadable），在 _definition_header_gate 和 _cmd_status_body / _cmd_explain 里接住，以退出码 2 结束并给一句产品语言的说明。status --wait 那一支改为只等待并说明原因，等新的处置循环上了再接进去。ADR：0037 决策 7「CLI 读端」补半句，0031 决定五「status」条与 0054 决策八「等待中的 status --wait」条各补一句，这三处等 owner 拍板第四段之后再改。
- 文件：core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、cli/gherkai_cli/__main__.py、cli/tests/test_definition_schema.py、cli/tests/test_main.py、docs/adr/0037-distribution-and-packaging.md、docs/adr/0031-job-lifecycle-states-and-severity.md、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md
- 先要有：owner 对第四段（status 退 2 还是照常显示；--wait 只等待还是退 2）拍板；--wait 一支依赖 run 处置的共用判定（runtime 包）
- 必须同批：--wait 只等待的那一支与 status --wait 的处置循环同批
- 单独先落地的后果：不带 --wait 的 status 和 explain 以退出码 2 结束的修复可以先单独落：现在这两个命令遇到损坏文件直接把回溯打到终端，修了只会更好。--wait 那一支在接力还在的时候先落，接力分支同样会在 load_run_state 处抛异常，要么一起接住，要么等接力删掉以后再落。
- 验证：单测够：损坏的 run_meta.json 和损坏的 run_state.json 各一例（非法 JSON、顶层是数组、状态值不认识），断言退出码 2、stderr 没有 Traceback。--wait 一支用注入的轮询间隔断言只等待、说明只打一次。
- 备注：属于查看命令批，--wait 部分属于 status --wait 处置批。前两段是设计决定，要等 owner 拍板第四段（「只等待」是否有意取代旧的退出码 2），拍板前只记在 journey。现在的 code 和线索说的一致：本机的 peek_definition_header 直接 json.loads，再调 d.get（顶层是数组时抛 AttributeError），load_run_state 经 _read_raw 和 run_state_from_dict 抛 JSONDecodeError、KeyError 或 ValueError；_definition_header_gate 只接 DefinitionContractError，main() 没有全局兜底，所以会出回溯。explain 本机路径（第 2652、2655 行）同样如此。线索第三段只写了本机，可是云端 _status_cloud 只接 botocore 异常，STATE 状态值不认识时（Status(...) 抛 ValueError）同样出回溯，见 missing。另一处会让使用者兜圈子：list-runs 把这类 run 列为「无法读取，用 status 查看」，status 却以 2 结束、说读不出，两处说法要衔接好。

#### 补-6（mixed，M）

- 线索：存储访问失败不算「运行态读不出」
- 要做的：在 runtime 包的处置判定里分开两类失败：解析失败记 unreadable，只等待或跳过；存储访问失败（本机 OSError 里的权限问题，云端 botocore 的权限、凭证、region、网络错误重试做完仍失败）往上抛，status --wait 和 settle-runs 都以 2 结束并说明原因，不进入等待。结束写失败（比如云端只有读权限）同样以 2 结束；条件写因为别处先写成而被挡下，不算失败（settle-runs 记 already_finished，status --wait 照常渲染终态）。ADR：0054 决策六末条写明「读不出」不含访问失败，决策八 status --wait 条补上结束写失败为 2；0031 决定五 status --wait 条与「退出码 2」条登记这一类。
- 文件：runtime/gherkai_runtime/（新的处置模块）、cli/gherkai_cli/__main__.py、docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、docs/adr/0031-job-lifecycle-states-and-severity.md、cli/tests/test_main.py、cli/tests/test_backend_cloud.py
- 先要有：结束写入口（端口新方法，返回写成与否）；run 处置的共用判定（runtime 包）
- 必须同批：settle-runs 命令与 status --wait 处置（同一批）
- 单独先落地的后果：不能单独落，处置还不存在。现在云端 _status_cloud 已经把 botocore 异常一律报「云端不可达」并以 2 结束，读这一半已经接近目标；本机读失败（PermissionError）在 status 里是未捕获的异常。
- 验证：本机用 chmod 造权限失败，pytest 的临时目录是真实文件系统，单测够。云端的判据要在真实 DynamoDB 上核：给一个只有 runs 表读权限的身份执行 status --wait，在一个过期限加 300 秒的 run 上看是否以 2 结束、说明原因，而不是继续等；moto 不校验 IAM，单测不算证据。这项依赖新的 runs 表写法（写入序号），要排在云端批重新部署之后。
- 备注：这是设计判据，要进 ADR，线索的建议落点合理。现在的 code 有一处不符：_status_cloud 的兜底说明写死成「云端不可达（表/凭证/region）」，结束写因 AccessDenied 失败时这句会误导，要另给一句点名缺 runs 表条件写权限的说明（见 missing）。0031 决定五「退出码 2」条现在写「另有四类」，加上这一类之后要改成五类，或者归进「查不到 run」一类，表述要定。

#### 补-7（mixed，S）

- 线索：settle-runs --json 的 cli_version 与被使用方中断时的退出码
- 要做的：settle-runs 的 --json 顶层与 list-runs 一样带 cli_version（恒有，取不到为 null），复用 render.run_list_to_dict 那种拼法和 _installed_version()；runs[] 各项不带写出版本。命令函数外面包一层 KeyboardInterrupt：打一句说明，以 130 结束，不出回溯；已写成的处置保留。机读契约页写出这两点。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py
- 先要有：settle-runs 命令本身
- 必须同批：settle-runs 命令与它的契约页条目（同一提交）
- 单独先落地的后果：不能单独落，命令还不存在。
- 验证：cli_version 的键形状用单测和契约护栏（test_cli_json_contract 的键集差集）验证。中断要真实执行一次：起一个真实的 settle-runs 进程处理多个 run，中途发 SIGINT，看退出码是否 130、有没有回溯、已写成的处置是否保留，再执行一次得到 already_finished。信号时序在 mock 之外。
- 备注：建议首选落在 journey 和实装批里，不进 ADR。我同意：两者都沿用既有惯例（list-runs 的 cli_version、status --wait 的 130），不是新决定。不过 0031 决定五 settle-runs 条现在只写 0 和 2，status --wait 条写了 130；要保持两条对称，可以在 0031 补半句，算 ADR 的小改。现在的 code 里 _cmd_status 用 128 + signal.SIGINT 处理中断，可以照抄。

#### 补-8（mixed，M）

- 线索：list-runs「已运行」「允许运行至」两列的计时细节
- 要做的：ADR 0041 决策七「人读形态」加一句：括注按 deadline_at 本身计，不含期限提示加的 300 秒。code：render_run_list 加 now 参数，由 _cmd_list_runs 只取一次、各行共用；「已运行」从 started_at 起算，已结束的取 started_at 到 ended_at；「允许运行至」用 _local_time_label 换算，表头注明本地；运行态读不出的行两列都是 -；期限提示用同一个 now。RunListing 加 deadline_at（另一条线索）。
- 文件：docs/adr/0041-agent-facing-cli-affordances.md、cli/gherkai_cli/render.py、cli/gherkai_cli/__main__.py、core/gherkai_core/model.py、cli/tests/test_list_runs_cli.py
- 先要有：端口列举项带 deadline_at（RunListing、两个 adapter 的 list_runs、头部读取带期限）
- 必须同批：查看命令块里 list-runs 加两列那一条
- 单独先落地的后果：ADR 那一句可以先落。code 部分离开加两列那一条就没有落点。
- 验证：单测够：注入 now，覆盖未结束（还剩多久、已超多久）、已结束（总时长）、期限读不到、运行态读不出四种行；时区用 TZ 固定。
- 备注：属于查看命令批。只有「括注按 deadline_at 本身计」是要进 ADR 的口径，其余是实装细节。现在的 code：render_run_list 的表头是 run_id、状态、开始（本地）、结束（本地）、job、版本、提示，没有这两列，也没有当前时刻参数。RunListing 没有 deadline_at；本机头部读取（_listing_header）只取结构版本和写端版本，云端 META 已经把 deadline_at 摊成顶层属性，但 BatchGetItem 的投影只有 schema_version 和 cli_version（ddb.py 第 98 行的投影集合），要加上。线索没写 started_at 缺失或解析不了时显示什么，按两列同为 - 处理最一致。

#### 补-9（mixed，S）

- 线索：detached 键在两个后端用同一判据
- 要做的：ADR 0041 决策七「机读形态」那一句（「detached 是布尔，恒有……」）之后补上判据：只有取值恰为布尔真才算 true，读的是顶层键或顶层属性，不按真值判断。code：DynamoDBRunStore._read_listing_rows 第 671 行的 bool(state_item.get("detached")) 改为 is True；is_detached 第 736 行同样改，或者随接力与 handler 分流的删除一起删掉这个方法。补一条 DDB 用例：detached 为 1、"true" 时列为 false、不算无法读取。
- 文件：docs/adr/0041-agent-facing-cli-affordances.md、core/gherkai_core/adapters/run_store/ddb.py、core/tests/test_list_runs.py
- 先要有：无
- 必须同批：无
- 单独先落地的后果：可以单独先落：只改云端 adapter 的读法，正常写下的 detached 恒为 True，现有用例不变。这是 CLI 一侧（list-runs）的读法，推进器 Lambda 虽然打包了 core，但它的分流用 is_detached，正常数据下结果不变，不用为这一条重新部署。
- 验证：单测够（用假表或 moto 写一个 detached 为数字或字符串的 STATE），纯逻辑。
- 备注：这一条单独成批或并入查看命令批都可以，ADR 那一句是口径，宜先写。现在的 code：本机两处已经是 is True（_marker_in 与 list_runs 里的 isinstance(d, dict) and d.get("detached") is True），云端两处是 bool(...)，和线索说的一致。连带：接力（_cmd_status_body、_status_cloud）和 reconciler._build 的分流删掉以后，两个 adapter 的 is_detached 都没有调用方了（list_runs 直接读标记，不经它），另一块说的「is_detached 只留给 list-runs --json」与 code 不符，应该删掉这个方法和它的用例（test_ddb_run_store.py 第 157 行起、test_stores.py 第 893 行起、test_local_run_store_lock.py 第 178 行）。还有本机 _marker_in 遇到顶层是数组时抛 AttributeError，is_detached 只接 OSError 和 ValueError，删掉这个方法这个问题也就没了。

#### 补-10（mixed，S）

- 线索：status --wait 的期限只读一次，等待中的说明只打一次
- 要做的：在 runtime 的处置判定或 status --wait 的轮询循环里缓存 deadline_at：读到合法值以后不再读运行定义，没读到时下一轮重读；每轮只重读运行态并做处置判定。说明用「上一次打印的原因」去重：原因没变不重复打，变了再打；锁被持有、云端未过期限加 300 秒时不打。
- 文件：cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/（新的处置模块）、cli/tests/test_main.py
- 先要有：run 处置的共用判定（runtime 包）；读期限的端口形态（头部读取带 deadline_at，与 list-runs 共用）
- 必须同批：status --wait 的处置循环（取代接力与 _STALL_KICK 的同一批）
- 单独先落地的后果：不能单独落，现在的 status --wait 不按期限做任何事。
- 验证：单测够：注入头部读取的返回序列（先失败、后成功、再变）和原因序列，断言读取次数与打印次数。墙钟比较用注入的时钟。
- 备注：属于 status --wait 处置批，是实装细节，不进 ADR，放在 journey 那一块的第三条下面合理。现在的 code：本机 _wait_local_terminal 每秒只读运行态，云端循环每 3 秒读运行态并用 _STALL_KICK 判卡住，都不读期限；端口上没有只读期限的方法（本机 peek_definition_header 解析整份 run_meta.json，只返回结构版本和写端版本），要扩展它返回 deadline_at，或者加一个方法，这和 list-runs 的头部读取是同一处改动，宜一起定。「期限不合法」的判定要走 core 那一处严格解析（run_deadline 里的 instant_from_iso），带时区才算合法。

#### 补-11（mixed，S）

- 线索：结构版本不认的 run 仍可按锁处置
- 要做的：ADR：0054「被拒方案」加「结构版本读不出或不认的 run 一律不处置」一条；决策六「期限读不出」的括号里写明运行定义读不出包括提交记录不存在、结构版本读不出或不认、定义违约。code：处置判定不过 _definition_header_gate 那道版本闸；读期限遇到版本不认或违约时按「期限读不出」处理，本机只剩试拿锁，云端记 undetermined；结束写只看运行态。status 和 explain 仍先过版本闸、以 2 结束（0037 决策 7 不变），所以这类 run 实际只能由 settle-runs 按锁结束。
- 文件：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、runtime/gherkai_runtime/（新的处置模块）、cli/gherkai_cli/__main__.py
- 先要有：生命期锁；结束写入口；run 处置的共用判定；owner 确认是否取这一做法
- 必须同批：settle-runs 命令
- 单独先落地的后果：ADR 可以先落（或者 owner 拿不准时先记进 journey 的待定问题）。code 离开处置模块没有落点。
- 验证：判定次序用单测。端到端要真实执行一次：本机起一个后台 run，把 run_meta.json 的 schema_version 改成别的值，SIGKILL 推进进程，执行 settle-runs，看它按锁结束（reason 为 advancer_exited），同时 status 以 2 结束。锁是真实 flock，单测不够。
- 备注：要先进 ADR，是被拒方案加一处定义；理由不是 owner 原话，要再核。疑点：处置写成之后要「从记录生成报告」，可 0027「index.html 形态」要求由结束写结束的 job「按运行定义的次序」排，RunResult 也要拿 job 定义作骨架。结构版本不认时运行定义读不出来，处置方写成了结束写，却组装不了报告。0037 决策 7 里运行定义不可用、推进器以 error 变体结束的路径有同样的问题，线索和 ADR 都没写这时报告怎么办（没有报告，还是只按运行态出报告），见 missing。
