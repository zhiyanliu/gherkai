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
- docs/diagrams/execution-timeout-chain.json 除了两个退役词，还有和新设计不符、但不会被退役词表命中的内容：卡片里「接力者按库里的领取时刻重算截止时刻，过了它 10 秒仍无退出记录即判超时」一句是本机接力的行为（「归因为超时失败」两处已在状态取法与结束写的第二笔按预算与期限分开改写，SVG 已重新导出）。journey「行为文档」块对这张图只提到改那两个词。依据 ADR 0034 被拒方案「本机接力，及其改法」。宜随本机接力删除一并改
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

第二批三笔都已实装：纯加法（取法、说明表、两个新的写入口）；前台改用新入口（`schedule` 返回执行事实 `Execution`、`RunPersistence` 逐 job 写终态并在需要时做结束写、run 的汇总从记录组装、期限截断记 aborted、`update_job_state` 只写 running 且不改写已结束的 run 与 job、`project_state` 不改写已写下的终态）；后台改用逐 job 写序（投影钳在 running；`tick` 每一轮为已有结果的 job 先存明细、再写终态，之后才做推进决策；`plan_next` 只有认领启动与到期的结束写两种动作；`try_finalize` 与 `expected_claim_count` 从端口删去；运行定义不可用时以结束写的 error 变体结束 run）。第三笔已集成、本机真实执行已核，待独立复核。原来「逐条」里的状态-4、6、7、11 都已做掉、删去。

第三笔之后后台记录与目标设计余下的差（保存失败的退避重试与按 scope_id 覆盖同键的三种残余已随判定明细点名那一批做掉：每次保存各有自己的键，读者一律按运行态里的标识取，`TickResult` 连同 `details` 删去，结束写不点名）：
1. DynamoDB 投影的形态（run 状态在把 job 写成 running 的那次逐 job 写里写、逐 job 写带 HWM 条件）与云端 `_mark` 的 error 变体只有 moto 的证据；Lambda 要等云端那一批重新部署才执行新 code，部署之后的核对项记在 0018「云端后端」一块。
   - 云端重读次数上限与投影写的关系有了一条固定先后的反例（另一家模型用 moto 与两个线程复现）：12 个 job 的 run，一方每次读运行态之后、整体替换之前，另一方落下一次投影写（标量一步加逐 job 写，各把写入序号加一），前者的 11 次尝试全部被挡、抛 `RunStateWriteContended`，后者下一轮读到完整事件之后提交，没有错的终态，也只有一方生成报告。实际的重叠里前者每次重试之间有退避（合计约 10 秒），远长于一次投影的耗时；但投影对库中已结束的 job 仍逐个发条件写，job 很多的 run 到后期每一轮的写次数与全部 job 数成正比。云端那一批定：重读次数上限、投影是否只为未结束的 job 发逐 job 写。

记下、不在第三笔处置的代价：
- 条件写已在服务端生效而响应丢失、SDK 重发被写入序号挡下时，没有一方得知自己使 run 成为终态，报告缺失。与「终态写之后的中断」同一类，已写进 0034 机制三④的「代价」一条；点名之后有一种可能的识别办法，记在「云端后端」小结。
- error 变体给每个未结束的 job 写一句原因，job 很多时可能超出单条记录的大小上限；异常从装配处冒出时，kicker 同一批里其它 run 的冷启动一并失败。与下面「云端那一批之前要定的」里结束写超出单条记录上限一条一起定；上限按含 `result_id` 的项大小实测。
- 报告一律按运行态里的标识逐个读回明细（判定明细点名那一批定的写法），耗时随 job 数增长（云端是逐个 S3 GetObject，按每次几十毫秒估，一千个 job 约二十秒）；与此前相比只多出使 run 成为终态的那一次 tick 写下终态的那几个 job（至多为并发上限个）。到点触发的那次调用只留了 30 秒给处置加一次 tick，使 run 成为终态的那一次落在其中时，报告可能被调用超时截断。留到云端那一批重估。

另有几处按设计现状留到以后：
- 重试注明的原因按检查次序取、结束写的来路按登记先后取，两者在同一个 run 里可能不同（见问-12）。
- `status` 的人读输出要不要显示 job 级说明（`status --json` 已带这个键），交 owner。
- 由第三笔之前的 code 推进到一半的 run 不加兼容分支；重新部署之前确认后端里没有执行中的 run，记在 0018「云端后端」一块。

前几笔的复核与集成另外记下、留给后面各批的：
- `explain` 点名「已结束而没有判定明细」的 job 时不理会 `--scenario` 与 `--step`，一律以 0 结束；有明细的分支在筛选没有命中时以 2 结束。输出形态（三个键）也是过渡的，explain 改造那一批按 0042 决策四改成以 job 定义为骨架时一并定筛选参数怎样处理。
- 运行期读写记录失败的出口按 `OSError` 分类，有两个边角：记录文件被改坏引起的解析错误仍打回溯；标准错误的管道已关闭时写提示抛出的 `BrokenPipeError` 也被说成读写记录失败。
- 真实 DynamoDB 上 `update_job_state` 靠条件失败时带回的条目分辨原因，只有 moto 的证据；`core/tests/test_cloud_integration.py` 里改写的集成用例随云端那一批重新部署之后执行。

云端那一批之前要定的：
- 结束写给每个未结束的 job 写一句说明，云端 STATE 在必须写成的那一次写上变大，job 很多的 run 建得成、推进得了，结束写却可能超出单条记录的大小上限（DynamoDB 抛的不是条件不成立，异常从 `end_run` 冒出，没有一方能结束这个 run）。ADR 0034 机制三②已记下这项代价与实测项；处理办法要定：计划阶段按 job 数设上限并给出提示，或缩短每个 job 存下的内容（不能违反「说明只是描述」，也不能在读取时另派生状态）。是否先撞上 META 的大小上限，取决于运行定义的大小，没有核。
- 云端以序号为条件的整体替换只能在真实 DynamoDB 与重新部署之后的云端验证，期间新 CLI 与旧 Lambda 混用时，序号条件形同虚设。

### 线索没有覆盖的改动点

第三笔之后没有余下的（DynamoDB 投影写 run 状态的位置已随第三笔改到把 job 写成 running 的那次逐 job 写里）。

### 逐条

这一块的逐条都已做掉。

## 判定明细点名与落库写序

### 小结

这一块已随判定明细点名那一批做完（0018「实装」一节第三批）：端口只有 `save_job_result(run_id, result_id, job)`、`load_job_result(run_id, result_id)` 与 `preflight()`，`load_all` 删去，本机文件名与 S3 键只用标识；`JobState.result_id` 由带结果的终态写写下，serialize 与两个 RunStore adapter 读写它，DynamoDB 的整体替换原样带上（「local.py 重建 JobState」一说已过时，`project_state` 用 replace 保留）；两种写入方生成标识、按标识保存、终态写点名，云端重读再算沿用同一组标识；本机组合根套保存失败的退避重试；读者共用 `named_details.load_named_details`。原来「逐条」的点名-1、2、3 与「线索没有覆盖的改动点」四条都已做掉、删去（契约页与 skill 副本的 jobs_dir 一行、ports、s3、compose 的 job-in 前缀理由、detached、`_atomic` 的注释一并改了）。

余下随别的块：
- 0030 实测项 1 的「`status --wait` 按说明表『锁拿到了』一行处置」与实测项 2 的「随后被处置时 explain 与报告不出现那份明细、explain 从事件流补取」：要等生命期锁与 run 处置（见「run 处置」小结）与 explain 骨架（见「查看命令与机读输出」小结）。
- 没被点名的明细只增不减，不读、不列、不清理；占用成为实际问题时按 0030「重议」条另议，到那时再定列举放在哪里。
- 过渡状态与留给后面各批的事项分别记在「本机推进器、生命期锁与边界检查」「run 处置」「云端后端」「查看命令与机读输出」「隧道」各小结。

## 本机推进器、生命期锁与边界检查

### 小结

生命期锁、边界检查与建 run 的暂存已随生命期锁一批做完（`core/gherkai_core/adapters/run_store/run_dir.py`：暂存加改名、锁交给注入的持有者 `HoldUntilExit` 与它登记的 fork 钩子、边界检查 `check_report_dir`、`check_fd` 与清单 `ALLOWED_FILESYSTEMS`；`run` 与本机 `submit` 在前置检查里对报告目录判断一次；两种后台进程入口的信号处置）；删接力的本机一半已随 run 处置一批做完。余下的是锁-2 里还欠的真实执行与 doctor 的调用方，以及锁-3 的云端一半。

### 逐条

#### 锁-2（mixed，M）

- 线索：本机后端报告目录的边界检查：对要取锁的那个 run 目录的描述符取文件系统类型
- 进度：判断函数与建 run 一侧的两个调用点已随生命期锁一批落地，等待中的 status --wait 与 settle-runs 的调用点已随 run 处置一批落地；清单里的各类型、绑定挂载、容器、HFS+ 与 FAT 磁盘映像、Docker Desktop 的宿主目录上的真实执行已内联进 0054 实测项 13、14。
- 要做的（余下）：doctor 的调用方（查看-6）；真实执行里还欠的：Linux 的 NFS、macOS 的 SMB 与 NFS 挂载上经命令的结果（0054 实测项 14「尚未核」），以及 x86_64 的 Python 上 `fstatfs` 的取法（只核过编译出的程序，没有核过解释器）。
- 文件：cli/gherkai_cli/__main__.py `_cmd_doctor`
- 必须同批：doctor 那一项与查看-6 同批
- 验证：NFS、SMB 挂载上 `run` 与本机 `submit` 以同一句被拒、不留目录（0054 实测项 14）。

#### 锁-3（mixed，M）

- 线索：删去本机接力：`status --wait` 不再进入推进循环
- 进度：本机一半已随 run 处置一批做完（`_cmd_status_body` 的接力分支、`drive_local_reconcile`、`_INTERRUPTED_RELAY_NOTICE`、`_recover_timed_out_claims`、`_RECOVERY_MARGIN_S`、`SubprocessLauncher.owned_scopes`、status 的 `--max-concurrency`、`build_local_reconcile` 的回落形参与 `SqliteEventLog` 的 `has_exit`、`record_timed_out_if_absent` 都已删去，`EventLog` 端口只剩 `records` 与 `record_exit`，两个点查与补写的方法只在 `DdbEventLog` 上；本机 status --wait 换成了处置循环，接力用例随之删去）。
- 要做的（余下）：`_WAIT_WITHOUT_RELAY_NOTICE` 仍由 `_status_cloud` 用（云端 `status --wait` 按后台执行标记分流），随云端 `status --wait` 的改写（处置-3）删去。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_backend_cloud.py
- 必须同批：云端 `status --wait` 的改写（处置-3），它又受云端次序约束（要在后端到期结束上线之后）

## run 处置：settle-runs 与 status --wait

### 小结

本机一半已随 run 处置一批做完：runtime 的处置模块 `settle.py`、本机的 `settle-runs`（含不给 run 标识时清理暂存目录）、本机等待中的 `status --wait`。余下云端的一半：`settle-runs` 接云端后端（这一批给出 `--backend cloud` 时以一句说明、退出码 2 结束），云端等待中的 `status --wait` 改为处置并删去 kickoff。

内部次序：云端一半（status --wait 处置并删 kickoff 与 _make_lambda_client）要与云端后端一块的定时触发、写入序号同批，在重新部署之后验证。settle-runs 的云端路径也宜放进那一批，因为新 CLI 版本高于后端时 skew 闸会拦下。

对别的块的依赖：余下的一半依赖写入序号与 kicker 定时触发（云端后端）。这一块在依赖链的末端。

最大风险：云端删 kickoff 早于后端到期结束，以及 dev 版本跳过 skew 闸时对没有写入序号的旧 STATE 做条件写。

判定明细点名那一批之后：
- 0030 实测项 1 的后半（重试用尽、推进器退出之后，`status --wait` 按说明表「锁拿到了」一行处置）与实测项 2 的「随后被处置」（存下明细之后、写下终态之前被 SIGKILL，处置之后 explain 与报告不出现那份明细，explain 从事件流补取已执行的 step）归这一块与 explain 骨架。点名那一批只能核接力推进的形态：接力方另存一份并点名自己的那一份，被杀进程留下的那一份不被读。
- `run` 发现 run 已被别处结束的出口现在在 stderr 给出判定明细目录的位置；点名之后目录里的文件名只是标识，其中可能有没被点名的一份。随这一块改为指向 `status` 与 `explain`（要先改 ADR 0054 决策五「说明与判定明细的位置写在 stderr」那一句）。

### 线索没有覆盖的改动点

- 存储访问失败不算「运行态读不出」的云端一侧（本机一侧已随 run 处置一批落地）：权限、凭证、region、网络失败时云端的 status --wait 与 settle-runs 以退出码 2 结束、不进入等待、不记 unreadable；status --wait 处置的结束写失败同样为 2；条件写被别处抢先不算失败。位置：cli/gherkai_cli/__main__.py 的 _status_cloud 和 settle-runs 的云端分支。依据：journey 0018 末节「存储访问失败不算『运行态读不出』」一条；ADR 0054 决策六末条、决策八。
- settle-runs --json 顶层带 cli_version（同 list-runs，恒有，取不到为 null），现在的输出没有这个键（被 Ctrl-C 中断时以 130 结束、已写成的处置保留，已随 run 处置一批落地）。位置：cli/gherkai_cli/__main__.py 的 settle-runs 命令函数、render.py、机读契约页。依据：journey 0018 末节「settle-runs --json 的 cli_version 与被使用方中断时的退出码」一条；ADR 0054 决策八的「机读输出」现在不含 cli_version。
- 云端的等待循环：status --wait 读到合法期限后不再重读运行定义，没读到时下一轮再读；等待中的说明首次打一次，原因变了再打（本机的等待循环已随 run 处置一批落地：每次处置读一次提交记录，等待中的说明按结构化的原因各给一次）。位置：cli/gherkai_cli/__main__.py 的 _status_cloud。依据：journey 0018 末节「status --wait 的期限只读一次，等待中的说明只打一次」一条。
- core/gherkai_core/run_deadline.py 的 `OVERDUE_MARGIN_S` 与 `overdue_at`（处置已随 run 处置一批接上，经 `run_deadline.past_overdue`）：status 与 list-runs 的期限提示、云端第二次定时触发接上它即可。依据：ADR 0054 决策六、九第 1 条；0041 决策七；0035 决策 3「边缘到点拒绝」。
- cli/DEVELOPMENT.md 目录树里 `__main__.py` 一行的 argparse 子命令清单还没有 settle-runs（settle-runs 的其余用户与技术文档已随 run 处置一批写出：running-and-results.md 的命令表与退出码表、configuration.md、troubleshooting.md、CHANGELOG、runtime/DEVELOPMENT.md 的处置模块）。依据：CLAUDE.md「改完 code 回头校准文档」；ADR 0054 决策八。
- cloud status --wait 要从现在不带卸载器的 DynamoDBRunStore 改为 build_cloud_stores 装配（带 S3 结果与报告两个 store、报告前缀取 --report-dir），否则处置写成之后读不了被点名的明细、写不了报告。位置：cli/gherkai_cli/__main__.py 的 _status_cloud。依据：ADR 0054 决策七（写成的一方生成报告）、决策八「云端用户一侧的处置方」条。
- agent skill 与 ADR 0043 决策五：骨架第 8 条「退出码分流」补 settle-runs 的退出码（任务域 A 的命令列表加 settle-runs、agent 先用 --dry-run 看再自己执行，已随 run 处置一批写进 0043 决策五）；skill 正文留给打磨批。位置：docs/adr/0043-agent-skill-for-driving-gherkai.md、cli/gherkai_cli/skills/gherkai/。依据：journey 末节「agent 可以自己执行 settle-runs」一条。

### 逐条

#### 处置-2（mixed，L）

- 线索：新命令 `gherkai settle-runs [run_id] [--dry-run] [--json]`
- 要做的（余下云端的一半）：先过 _cloud_skew_gate；不给 run_id 时经 build_cloud_run_list_store 列举，用 build_cloud_stores（带卸载器与 S3 两个 store）做结束写和写报告。（子命令、本机的处置与清理暂存目录、人读与 `--json` 输出、退出码与 settings 的两份名单已随 run 处置一批落地；这一批给出 `--backend cloud` 时以一句说明、退出码 2 结束。）
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、cli/tests/test_settle_runs.py、cli/tests/test_cli_json_contract.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、docs/user-guide/running-and-results.md、docs/user-guide/configuration.md、CHANGELOG.md
- 先要有：云端部分依赖写入序号（云端后端一块的 ddb.py）与重新部署：新 CLI 版本高于后端时 skew 闸会拦下（SKEW_BLOCK）
- 必须同批：机读契约页与 skill 副本写出 settle-runs 的 --json（契约测试守着已登记命令的键）；用户文档的命令表、选项表与 CHANGELOG（每批提交带上它所改行为的文档）
- 单独先落地的后果：云端一半在重新部署之前，正式版本会被 skew 闸拦下；dev 版本会跳过 skew 闸，对没有写入序号的旧 STATE 做条件写，结果没有保证。
- 验证：云端在重新部署之后：期限加 300 秒前后各一次，只给 runs 表读权限时写入失败以退出码 2 结束，不给 run_id 时经索引列举。
- 备注：_cloud_skew_gate 文档串里列的「四个 cloud 入口（submit / status / explain / list-runs）」要加上 settle-runs。--report-dir 在云端是报告前缀，settle-runs 写报告用它；是否和后端的 REPORT_DIR 比对还待 owner 定（journey「核对时补上的条目」）。

#### 处置-3（mixed，M）

- 线索：等待中的 `status --wait`，两个后端、前台与后台的 run 都一样
- 要做的（余下云端的一半）：_status_cloud 的等待循环改为每轮比期限，到点即处置；删去 _STALL_KICK、lam.invoke 及 ResourceNotFoundException 分支、kicker_fn。删去 compose._make_lambda_client。云端 run_store 改由 build_cloud_stores 装配，带卸载器和 S3 的结果、报告两个 store，供处置时写报告。（本机的等待与处置已随 run 处置一批落地。）
- 文件：cli/gherkai_cli/__main__.py（_status_cloud、_INTERRUPTED_WAIT_NOTICE、status 子命令 help）、runtime/gherkai_runtime/compose.py（删 _make_lambda_client）、cli/tests/test_backend_cloud.py、docs/user-guide/running-and-results.md、docs/internals/execution-and-reconciliation.md
- 先要有：删 kickoff 必须与后端到期结束（kicker 收到 STATE 新建时建两次定时触发，云端后端一块）同批或在它之后，即重新部署之后
- 必须同批：kicker 的定时触发与清扫、runs 表写入序号，与这些一起重新部署；测试删改：test_backend_cloud.py 里 kickoff 相关的用例（test_status_wait_cloud_kicker_missing_fails_fast、..._only_waits_for_a_run_that_is_not_detached、..._exits_2_when_the_detached_marker_cannot_be_read）
- 单独先落地的后果：如果早于后端到期结束落下，推进链断开的云端 run 失去唯一的唤醒手段（journey 写明的次序约束），只能等期限加 300 秒后被 status --wait 记为 aborted。上面列的测试会因断言旧行为而变红。
- 验证：云端在重新部署之后：断开推进链的 run 过期限加 300 秒后被 status --wait 处置并写出 S3 报告，核对 kicker 不再收到直接调用（看 Lambda 调用量与日志）。
- 备注：code 现状：云端连续 3 轮快照没变就调用一次 kicker。云端现在用的是不带卸载器的 DynamoDBRunStore，没有结果与报告两个 store，处置写不了报告，所以要改装配，这一点线索没有写。kicker 的 _run_ids_from_runs_stream 对 {"run_id": ...} 这种 payload 的分支不能删：job 超时的定时触发也用同一形状，只改它 docstring 里「status --wait 接力兜底」的说法（注释块已登记）。CloudTarget.kicker_lambda 仍供 submit 的 lambda:GetFunction 预检，保留。_INTERRUPTED_WAIT_NOTICE 的「这个 run 仍在原处继续执行」在推进器已不在时不成立，宜随之改写。

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
4. 点名明细（判定明细点名那一批已落 code，Lambda 侧要重新部署才生效）：旧 Lambda 不点名，新 CLI 的处置、报告与 explain 找不到明细，`status --json` 也没有 `result_id`。已部署的后端本来就读不了现在的提交记录，不做兼容；重新部署之前确认后端里没有执行中的 run（0018「云端后端」一块已记）。

判定明细点名那一批留给这一块的：
- 条件写已在服务端生效而响应丢失、SDK 重发被写入序号挡下时（0034 机制三④「代价」一条），点名之后可以凭本方的标识认出这次写已经落下：重读到的每个给出的 job 都是终态、标识都等于本方给出的值。要不要据此把 `ALREADY_ENDED` 改认成本方写成、判据够不够严（别的写入方不会写出相同的标识，但这一组 job 是不是这次写使 run 成为终态还要另判），在这一批定。
- 带 `result_id` 的 STATE 条目大小：每个被点名的 job 约多 25 字节，按 0034 机制三②的样本估算单条记录容纳的 job 数约减少 8%；结束写能写成的 job 数上限要按含标识与 job 级说明的实际项大小在真 DynamoDB 上重测。
- 报告逐个读明细的耗时与到点触发那次调用的 30 秒预算：见「状态取法与结束写」小结的代价一条。
- 部署之后的核对项（Lambda 写带标识的键、两次调用重叠时 explain 与报告取写成终态那一方的、没有 `s3:ListBucket` 的 explain）记在 0018「云端后端」一块。

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
- 先要有：端口上的结束写入口与 update_job_state 新语义（状态取法块，方法名与参数在 ports.py 定）；run 状态取法函数（取代 run_verdict 与 projected_run_status）；JobState 带点名标识（判定明细点名块，已落下）：整体替换的 jobs Map 要带上它
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

原查看-1（run --json 的 jobs[] 与文本汇总从记录组装）与查看-2（run 的退出码读记录）已随第二批第二笔落地。余下合计 L，大头是查看-7（explain 改按运行态与点名取明细），要改明细的读取方式，并重写大量 cli 测试。另有一组只读查看面的小改动：查看-3、4、5 的期限读取与提示，查看-6 的 doctor 一行，查看-8 的日志指引。

内部次序：
1. 先做查看-3 与查看-5 的头部读取扩展（peek_definition_header 与 RunListing 带 deadline_at）。它们只读 META 和 run_meta.json 里已有的属性，不依赖新的写入设计，可以先落；两列与 deadline_at 键可以同批。
2. 查看-4 的期限提示与删云端的 pending 接力提示（FOREGROUND_RUN_NOTE 与本机的 pending 提示已随 run 处置一批删去，settle-runs、本机 status --wait 的处置与 300 秒的判断已在）；删云端的那一句要与云端 kickoff 的删除同批或排在它之后。
3. 查看-6 要用的边界检查函数已随生命期锁一批落地，可以直接接上。
4. 查看-7 的读法部分已随判定明细点名那一批落下（见查看-7 的进度），余下的骨架改造是 explain 骨架那一批，查看-8 随它。

判定明细点名那一批之后 explain 的过渡缺口（如实记下，不写成符合 ADR；都留到 explain 以 job 定义为骨架的那一批）：
- 不点名 scope 时只列运行态里被点名的 job，由结束写结束的 job 不列出；ADR 0042 决策四要求列出它的状态与说明，现在只有点名这个 scope 时才给（三个键，状态与说明取运行态）。契约页 explain 一节与用户文档按现状写了「不点名时不列出」。
- 存过明细却由结束写结束的 job（两个推进方对运行定义一个读得懂、一个读不懂时的残余，以及以后由 run 处置结束的 job）只给状态与说明三个键，存储里那份没被点名的明细不读；它已执行的 step 要等骨架那一批从事件流补取。这是信息少了、不是错了：此前把残留明细当成判定列出，正是 0030 决定三拒绝的形态。
- 不点名 scope 时的次序由「按编码后的文件名」改为「按 scope_id」，两个后端规则相同；按运行定义排序随骨架那一批做。

对别的块的依赖：状态取法与结束写（取法函数、结束写、JobState.message）、报告（从记录组装）、本机推进器与边界检查、run 处置（settle-runs、300 秒判断）、删本机接力。云端一侧，status 的点名键和 explain 读点名明细、补取 aborted job 的真实验证，要等推进器 Lambda 重新部署之后才能做。这一块的读取改动本身（META 投影、BatchGetItem 投影多带 deadline_at）只读已有属性，不需要重新部署。

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
- status 的人读输出要不要显示由结束写写下的 job 级说明（`status --json` 已带这个键），ADR 0041 与 0034「命令形态」都没有写，交 owner。

### 逐条

#### 查看-3（mixed，M）

- 线索：`status --json` 的 jobs[] 每项带这个 job 终态点名的明细标识
- 进度：jobs[] 的点名标识 `result_id` 已随判定明细点名那一批落下（serialize 写出即自动带上，契约页 status 一节与 test_status_json_keys_are_documented 同提交登记）；余下 deadline_at 一半，与查看-5 同批。
- 要做的：deadline_at 要新增读取：把 RunStore.peek_definition_header 扩成同时返回 deadline_at（本机 run_meta.json 已经整份解析过；云端 META 的顶层已有 deadline_at，ProjectionExpression 加上这一项即可），_definition_header_gate 把头部交回调用方，_render_status 在 JSON 顶层加 deadline_at，读不到就省键。
- 文件：core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、cli/gherkai_cli/__main__.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py、core/tests/test_stores.py、core/tests/test_ddb_run_store.py
- 先要有：无
- 必须同批：契约页 status 一节加 deadline_at 一行（test_status_json_keys_are_documented 按真渲染器收集键，文档漏写即红）
- 单独先落地的后果：没有影响，契约页同一提交补上即可。
- 验证：单测够：本机文件 store 与 moto 上的头部读取都覆盖 deadline_at，契约护栏收集键名。deadline_at 只读 META 上已有的属性，不需要重新部署。云端 jobs Map 里真带点名键的核对记在 0018「云端后端」一块。
- 备注：头部读取扩成三项，要连带改 `_definition_header_gate` 和 `_definition_schema_gate` 的签名、`require_listing_header`，以及 list-runs 的 RunListing.header（查看-5 也要这次读取，两条宜同一批）。「_render_status 拿到 deadline_at」也是查看-4 的前提。status --json 的 RunState 部分要不要也带 job 级说明（JobState.message 写出之后会自动出现），ADR 0041 决策三没有提，契约页要写明。

#### 查看-4（code，M）

- 线索：不带 `--wait` 的 status 与 list-runs 给同一句期限提示
- 要做的：在 runtime 或 cli 放一个共用的判断（未结束，且当前墙钟严格晚于 deadline_at 加 300 秒），给出同一句「已超过允许运行的时间（可用 settle-runs 或 status --wait 记为已结束）」：_render_status 用在不带 --wait、非 --json 的人读输出上，render_run_list 用在提示列。删去 _status_cloud 里「推进可能未启动、可 status --wait 接力」的 pending 提示与 _relay_available。（本机一侧的 pending 提示、relay_available 参数、wait_hint 参数与 _cmd_status_body 里传入的回调已随 run 处置一批删去，_render_status 现在只收调用方算好的 hint。）
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、runtime/gherkai_runtime/deadline.py、cli/tests/test_main.py、cli/tests/test_render.py、cli/tests/test_backend_cloud.py
- 先要有：status 读到 deadline_at（查看-3 的头部读取）；list-runs 列举项带 deadline_at（查看-5）。期限加 300 秒的判断已在 core 的 run_deadline（`OVERDUE_MARGIN_S`、`past_overdue`，处置在用）
- 必须同批：删去云端 kickoff（处置块的处置-3）：在这之前云端「status --wait 接力」的提示仍然成立，先删提示会丢掉一条仍然有效的指引（settle-runs 与本机等待中的 status --wait 的处置已在）
- 单独先落地的后果：云端的 pending 接力提示删早了，现存的 kickoff 就少了一条指引；test_backend_cloud 里断言「可接力推进」提示的用例会红。
- 验证：单测够：只看记录与期限、不碰锁，注入墙钟后覆盖严格晚于、恰好相等、未结束与已结束几种情形。
- 备注：云端 _status_cloud 里的 _relay_available 读 is_detached，删去之后，云端 status 不带 --wait 时就不再读 detached 标记。读不到期限的 run 不给期限提示，ADR 0041 决策七写的是「其余不给期限提示」。

#### 查看-5（mixed，M）

- 线索：list-runs：人读表格按列序加「已运行」「允许运行至」两列
- 要做的：RunListing 加 deadline_at 字段，两个 adapter 的 list_runs 在同一次头部读取里取它：本机 _listing_header 同一次解析，云端 _LISTING_ATTRS 加 deadline_at 进 BatchGetItem 的投影。render_run_list 按列序加「已运行」「允许运行至」，提示列放期限提示（FOREGROUND_RUN_NOTE 已随 run 处置一批删去）；run_listing_to_dict 加 deadline_at，读不到时省键。--status 的 choices 去掉 skipped（argparse 给出时以退出码 2 结束）；_LIST_RUNS_TERMINAL 不再查 skipped，定了查几个终态分组之后回写 0041 决策七「代价」段与实测项的读量。
- 文件：core/gherkai_core/model.py、core/gherkai_core/ports.py、core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、docs/adr/0041-agent-facing-cli-affordances.md、cli/tests/test_main.py、cli/tests/test_render.py、cli/tests/test_cli_json_contract.py、core/tests/test_stores.py、core/tests/test_ddb_run_store.py
- 先要有：run 的状态不会是 skipped（状态取法与结束写块删去 run_verdict），--status 才能拒收 skipped、默认清单才能少查一个分组；期限加 300 秒的共用判断（查看-4）
- 必须同批：查看-4（提示列里的期限提示是同一句）；契约页 list-runs 一节加 deadline_at（detached 一行已随 run 处置一批改写）
- 单独先落地的后果：两列与 deadline_at 单独做没有影响。--status 拒收 skipped 与少查 skipped 分组要是先于删 run_verdict 落地，现行代码在理论上仍能产出 skipped 的 run，这样的 run 会从默认清单里消失。
- 验证：两列、JSON 与参数校验用单测（注入当前时刻，本机文件 store 与 moto）。BatchGetItem 投影多带 deadline_at 用 moto 即可。默认清单查几个分组之后的读量，ADR 要求回写实测值，要在真实 DynamoDB 上用 ReturnConsumedCapacity 测，只读、不需要重新部署。
- 备注：现在 RunListing 只有 run_id、state、detached、header，没有 deadline_at；本机 _listing_header 走 peek_definition_header 整份解析 run_meta.json，云端 _header_from_item 只取 schema_version 与 cli_version。--status 的 choices 现在取 [s.value for s in Status]，help 文案也是从 Status 拼出来的，两处都要排除 skipped。ADR 0041 决策七写的是「默认清单查五个终态」，现在的 _LIST_RUNS_TERMINAL 也是五个，其中含 skipped；去掉之后是四个，「代价」段的 N 到 5N 一类数字要随之改。detached 的判据改成 `is True` 那一条见 missing。

#### 查看-6（mixed，S）

- 线索：doctor 新增 report_dir 组的 report_dir.filesystem 一项
- 要做的：_cmd_doctor 在不查云端时（want_cloud 为假）add('report_dir', 'filesystem', ...)，必修。调用锁块新增的边界检查判断（对报告目录取文件系统类型；目录不存在时取最近一层已存在的上级），只读、不取锁，detail 写原因、检测到的类型与放行清单。doctor 子命令 --report-dir 的 help 去掉 [cloud]。契约页 doctor 一节的 section 取值加 report_dir、项名表加 filesystem。
- 文件：cli/gherkai_cli/__main__.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_main.py、cli/tests/test_cli_json_contract.py
- 先要有：边界检查判断函数（已随生命期锁一批落地，在 core 的 `adapters/run_store/run_dir.py`：`check_report_dir`）
- 必须同批：契约页 doctor 一节（test_doctor_json_keys_are_documented 核键名；项名表是人工对照，没有测试守）
- 单独先落地的后果：要是在 doctor 里自写一份判断，就和 run、submit、settle-runs、status --wait 用的不是同一份，违反 0054 决策四「共用同一判断」。test_main 里列举 doctor 全部行或未查行的用例（如第 2075 行、第 2481 行附近）要补上这一行。
- 验证：单测只能覆盖清单匹配与 detail 的写法，取文件系统类型依赖真实的 statfs 与挂载信息，要真实执行：macOS 的 APFS 目录放行；Linux 上 ext4、tmpfs、overlay（容器里）各放行一次；清单之外的类型（如 macOS Docker Desktop 宿主目录在容器里的 fakeowner，或 NFS、SMB）被拒、退出码 2。这项实测与锁块的边界检查共用，doctor 这一侧核一次输出即可。
- 备注：settings.py 把只给 --prefix 的 doctor 也当作云端（use_cloud 判据），而 ADR 0041 决策四只写「--backend cloud 时不出这一行」，没说只给 --prefix 时怎样；按现在的 want_cloud 判据，只给 --prefix 时也不出这一行，要在 ADR 或契约页写明。项名 report_dir.filesystem 是写回时执笔自定的，owner 还没有确认（journey「写回时留下、实装之前要定的问题」）。doctor 的 --report-dir 在本机后端缺省为 reports（BUILTIN_DEFAULTS），只有来自配置文件时才绝对化，判断前要先 resolve。

#### 查看-7（code，L）

- 线索：explain：先经 RunStore 读运行定义与运行态
- 进度：第二笔加了一个小分支：点名的 scope 在运行态里已结束而没有判定明细（由结束写结束的 job）时，按运行态给出状态与说明、以退出码 0 结束，`--json` 的 `scopes[]` 只有这一项三个键。第三批之前的修补改为先看运行态：未结束的 job 不读、不展示。判定明细点名那一批落下了读法：只按运行态里的点名标识经 `named_details.load_named_details` 取那一份，`load_all` 删去；不点名 scope 时只列被点名的 job、按 scope_id 排序；「未找到 scope」的候选取运行态；被点名而读不到时打一句说明、以退出码 2 结束；云端说明删去「不给 scope_id 时还需列举对象的权限」。过渡缺口见本块小结。
- 要做的（余下的骨架改造）：_cmd_explain 与 _explain_cloud 在头部闸之后读 load_run_meta（job 定义）。由结束写结束的 job 以 job 定义为骨架、不点名 scope 时同样列出，状态与说明取运行态，记 aborted 的经 _explain_recover 从事件流补取已执行的 step。_explain_emit 的空文档与 scope_id 分支按运行态判断：没有已结束的 job 时退 0，只打「判定明细尚未落地」加整条 status --wait 命令；给了 scope_id 而它还没结束时退 0 并提示；scope_id 不在定义里才退 2，候选清单取自运行定义；不点名 scope 时按运行定义的次序排列；scope 级 status 取运行态；无明细分支怎样处理 `--scenario` 与 `--step` 一并定（见「状态取法与结束写」小结「前几笔的复核与集成」一条）。删去「本 run 没有任何 job 的判定明细」。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、cli/tests/test_main.py、cli/tests/test_render.py、docs/internals/cli-json-contract.md、docs/internals/verdict-model.md
- 先要有：都已落下（按点名标识读明细、JobState 的点名标识与 job 级说明、结束写入口）
- 必须同批：0033 编排进程角色里 explain 的云端权限（读对象，不需要 s3:ListBucket；登记与否见 0018「写回时留下、实装之前要定的问题」）；若「判定明细尚未落地」的原文改了，同一提交改 0031 决定一·补里 TERMINAL_STATUSES 的消费方清单
- 单独先落地的后果：骨架改造可以单独一批：读法已经只按运行态取，改造只多读运行定义、多列出由结束写结束的 job，不影响已有的读者。
- 验证：本机的骨架、补取、scope_id 各分支用单测（fake store 与真本机文件 store 加 SqliteEventLog）。云端两项依赖重新部署之后的真实后端：推进器按新写序点名明细；由后端到期结束或处置记 aborted 的 job 能从 events 表补取 step；以一份不含 s3:ListBucket 的真实 IAM 策略执行 explain 不带 scope_id，确认不再需要列举权限。
- 备注：①现在 _definition_header_gate 只读头部；改读整份 load_run_meta 之后，同版本下的形态违约会在这里抛 DefinitionContractError（本机 run_meta_from_dict），要接住、以退出码 2 结束，否则用户终端会看到回溯。②由结束写结束的 job 没有 JobResult。最省事的做法是合成一个只有 job、status、message、空 scenarios 的 JobResult 交给 explain_to_dict，这样 _needs_recovery 与补取路径原样可用；它与报告块「从记录组装 RunResult」该是同一处组装，不要另写一份。③云端 load_run_meta 在运行定义卸载到 S3 时要多一次 GetObject，0042 决策四写的权限已含桶 s3:GetObject。④_explain_emit 的 docstring 与按 load_all 读的注释已随判定明细点名那一批改。

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
- 判定明细点名（已落下）：按标识读明细，JobState 带标识。
- 结束写：JobState 带 job 级说明，前台没有启动的 job 由结束写记 skipped。
- 状态取法：update_job_state 的新语义，后台逐 job 写序下 COMMITTED 的新含义。

处置块（settle-runs 与 status --wait）和云端的后端到期结束都调用这里的组装入口，所以它们排在本块之后，或与本块同一批。

改 deploy_aws 的 _tick_runs 要重新部署才生效。core 入口改名会迫使 Lambda 代码和测试在同一批里改，部署本身可以放到云端那一批。

最大的风险是「只有一方生成报告」：
- 端口现在规定 update_job_state 返回的是「这次写之前 run 是否仍未结束」，写入方无法直接知道「这次写是否使 run 成为终态」。前台和 tick 都要自己推出，或者端口多返回一项。要是靠写后读回判断，处置方在前台两次写之间落下结束写时，两方都会生成报告。
- 这个性质的证据只能来自真实执行：云端重新部署之后在真 DynamoDB 上并发，本机用真实进程 SIGKILL 推进器再由 settle-runs 处置。
- 次要的风险是前台 run 级墙钟的口径（0024 规定由 schedule 包住）。从记录组装之后取哪一个，要先定。

### 线索没有覆盖的改动点

- 云端后端到期结束（kicker 在期限加 300 秒那次一次性定时触发里做结束写）写成之后，要由 Lambda 从记录生成报告。云端块的线索只写了结束写，没写报告（位置：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py kicker_handler；依据：0054 决策九第 1 条；0027「报告由谁、在何时、从什么生成」；0034「命令形态」表）。

### 逐条

#### 报告-1（mixed，L）

- 线索：报告只由使 run 成为终态的那次写的写入方生成，生成时从记录组装 RunResult
- 进度：第二笔已落下组装与生成方：`project.assemble_run_result` 是唯一的组装处（每个 job 一个 `JobOutcome`，状态取运行态、有明细的附上明细），前台由 `RunPersistence.finalize` 在本进程使 run 成为终态之后读一次运行态组装，后台由收到 COMMITTED 的宿主经 `reconcile.write_report_from_record` 组装，`TickResult.result` 改为 `details`，`compose.run_duration_ms` 移进 core；index.html 与文本汇总按运行态显示由结束写结束的 job、删去「没有执行」（原报告-2）。判定明细点名那一批把明细改为一律按运行态里点名的标识从 ResultStore 读回（前台 finalize 与后台 `write_report_from_record(meta, run_store, result_store, report_store, created_at=…)` 都经 `named_details.load_named_details`），`TickResult` 连同 `details` 删去；下面备注③定为读不到即按记录残缺失败（前台走存储失败出口里「记录已是终态」的说明，后台在失败隔离之内不生成报告），备注④随之消失（前台不再用内存里的明细）。处置方写成结束写之后经同一组装生成报告已随 run 处置一批落地（`settle` 调 `reconcile.generate_report_from_record`，`write_report_from_record` 经它）。余下：云端后端到期写成结束写之后调用同一入口（云端批）；备注⑥ reconciler 的注释还没有改（现在第 511 行写「本 Lambda 与 detached 宿主两个调用点」）。
- 要做的：在 core 新增一处「从记录组装 RunResult」的函数：读 RunMeta 与 RunState，按运行定义的次序逐 job 处理。终态带点名标识的 job，按标识经 ResultStore 读那一份明细，状态改取运行态；终态不带标识的 job（由结束写结束）只带 Job 与运行态里的状态和说明。run 级 status、message 取运行态，合计四键用 project.run_totals 重算，run 级墙钟取 started_at 到 ended_at。用一个新入口取代 reconcile.finalize_report(result, report_store, created_at, run_duration_ms)，形如 write_report_from_record(run_id, run_store, result_store, report_store, created_at)：读记录、组装、ReportStore.write 整段放在失败隔离里（0034 机制三步骤④写明「为生成而读记录的那一次同样在隔离之内」）。删去 TickResult.result 及 __post_init__ 里「COMMITTED 必带结果」的不变量，COMMITTED 只表示这一方的写使 run 成为终态。调用方改为四处：RunPersistence.finalize（本进程的写使 run 成为终态时调用，返回 index 的 URI）、detached.run_reconcile_loop 的 COMMITTED 分支、reconciler._tick_runs 的 COMMITTED 分支，以及处置方（settle-runs、等待中的 status --wait 写成结束写之后）。两个宿主里单独读 RunState 求 duration 的那段隔离代码随之并入新入口。docstring 一并改：ReportStore 类与 write 的「可从 RunResult 完全重建」改为「从记录生成」，RunPersistence.finalize 删去「报告可后续从 RunResult 重建」，finalize_report、TickOutcome、TickResult、_finalize 步骤④、run_reconcile_loop 里讲「用 tick 交还的结果写报告」的说法，以及 compose.run_duration_ms docstring 里的「宿主在 finalize_report 前调」。
- 文件：core/gherkai_core/reconcile.py、core/gherkai_core/persist.py、core/gherkai_core/ports.py、core/gherkai_core/model.py、core/gherkai_core/project.py、runtime/gherkai_runtime/detached.py、runtime/gherkai_runtime/compose.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、cli/gherkai_cli/__main__.py、core/tests/test_reconcile.py、core/tests/test_persist.py、runtime/tests/test_detached_launcher.py、deploy_aws/tests/test_lambda_handlers.py
- 先要有（都已落下）：判定明细点名：ResultStore 按标识读明细（load_job_result 加标识参数、去掉 load_all），JobState 带点名标识，serialize 与两个 RunStore adapter 读写这个键；结束写入口与 JobState 的 job 级说明字段：由结束写结束的 job 的状态与说明要在运行态里（JobState 现在没有 message 字段）；update_job_state 的新语义：run 状态按取法随写落下，job 终态只写一次，写入方能确定这次写是否使 run 成为终态；后台推进的逐 job 写序：tick 的 COMMITTED 改为「记下最后一批终态的写或到期的结束写由本方写成」，不再由 _finalize 一次收尾给出
- 必须同批：测试块里 K2 的三个测试（test_report_comes_from_the_record_and_the_named_details_not_from_a_second_read_of_the_events、test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots、test_tick_runs_writes_the_report_from_the_record_when_its_tick_commits）；前台 run 的输出改为读记录（查看命令块里 run --json 的 jobs[]）：_cmd_run 的汇总与报告应当出自同一份组装结果；随所改行为的技术文档（core/DEVELOPMENT.md 的 project.py 与 reconcile.py 条目、docs/internals/artifacts-and-evidence.md 讲「可重建」的两处）
- 单独先落地的后果：在点名之前单独落地：组装只能按 scope_id 读明细，而现在的 _finalize 不论条件写成不成都先存明细、覆盖同 key，云端两次调用重叠时报告可能取到没写成终态那一方的明细，与记录里的终态不一致（现在靠 TickResult.result 避开了这个问题，test_report_follows_the_committing_round 的文档串写明「B 落下的判定明细与 A 的谁留在存储里不在断言之内」）。在结束写之前单独落地：因期限没有启动的 job 在运行态里停在 pending，从记录组装出来就是 pending。test_reconcile 里构造 TickResult(COMMITTED, result) 与读 done.result 的用例、test_detached_launcher 与 test_lambda_handlers 里的报告用例、test_persist 的 finalize 用例都会变红。
- 验证：组装逻辑（读哪一份明细、状态取运行态、次序、合计）、四处调用方各自在什么时候生成或不生成报告、失败隔离：单测就够，本机文件 adapter 与 moto 两侧都要有用例。「只有一方生成报告」依赖真实并发与条件写，单测不算证据：云端要在重新部署之后，经 Lambda 的代码在真 DynamoDB 上重做并发与几百个 job 的结束写（0034 机制三②的实测项）。本机要真实执行：后台推进进程在 job 结束之后被 SIGKILL，再由 settle-runs 处置，核对报告由处置方从记录生成，明细取被点名的那一份。还要在跳板机上带引擎真实执行一次前台 run 与一次 submit --backend local，核对报告里的 report_refs、合计与运行态一致。
- 备注：①0030 决定四规定 update_job_state 返回的是「run 在这次写之前是否仍未结束」，不是「这次写是否使 run 成为终态」。RunPersistence.finalize 要回答「本进程的写使 run 成为终态」，只能自己推出（每个 job 都由本进程写成终态且返回 True，最后一次就是使 run 成为终态的那次；或者结束写写成），否则端口要多返回一项。要先定下来：处置方在前台两次写之间落下结束写时，靠读回判断会让两方都生成报告。tick 一侧有同样的问题。②墙钟口径：0024「三级执行时长」写的是同步 run 的 run 级时长由 schedule 整体包住，只有 detached 取 RunState 的 started_at 到 ended_at。从记录组装之后前台取哪一个没有写，要么前台把内存里测的时长传进来，要么改 0024。③被点名的明细读不出（文件缺失或损坏）时怎样处理没有写；按失败隔离处理就是没有报告，也可以把这个 job 当作没有明细来显示，要定。④组装结果里由执行结果结束的 job 按什么次序排没有写（0027 只规定由结束写结束的 job 排在后面、按运行定义的次序）；现在前台按完成先后，后台按 project_full 的次序。⑤RunPersistence.finalize(result, ended_at) 的 result 参数在新设计里不再用来生成报告，结束写要的是来路的说明，接口形态随结束写块一起定。⑥reconciler.py 第 506 行注释写「finalize_report 只有本 Lambda 与 detached 宿主两个调用点」，改完之后不成立（前台与处置方也调用），要改。⑦Lambda 一侧的改动要重新部署才会生效。core 的入口改名会迫使 reconciler.py 与它的测试在同一批里改，部署可以排在云端那一批。

## 测试

### 小结

整体改动量 L：涉及 4 个包、约 20 个测试文件，几百行以上。线索列的只是受影响测试的一部分，下面 missing 里的连带改动（try_finalize 全量迁移、到期语义、job 级 skipped；load_all 的那两条已随判定明细点名那一批做掉、删去）比线索点名的更多。所有被点名的符号都在 code 里找到了，没有改名。

这一块本身没有独立的先后次序，各条跟着自己那一块的 code 批次走：
- 测-8 不依赖 code，可以随任何一批落地。
- 测-2（moto 与本机部分）跟着「状态取法与结束写」块（测-1、测-6 已随第二批做完、删去）。测-2 里点名标识的两端对拍（第二次终态写不改写第一次的点名、结束写与执行中的写保留点名）已随判定明细点名那一批补上。这是第一个大批，core 之内的测试量最大。
- 测-3、测-5、测-9 已做完、删去，测-4 与测-12 的本机部分已随 run 处置一批做完（测-3 的最后一处，即两个推进方读到不同快照的用例改到 DDB 一侧，也在这一批）。
- 测-11 只剩 kickoff，跟「run 处置」块，按次序约束要与后端到期结束同批或在其后（前台云端 run 与 resolve_network 那一半已随「云端只支持 submit」那一批做完）。
- 测-10、测-12 的云端部分、测-4 的云端用例、测-2 的真 DDB 部分跟「云端后端」块，宜集中在同一次重新部署的批次里。

最大的风险（try_finalize 的迁移与结束写来路的说明两项已随第二批解决、删去）：写入序号的条件、并发写入、几百个 job 的项大小上限，以及 DDB 一次写里区分「STATE 不存在」与「run 已结束」，都依赖 moto 之外的真实 DynamoDB 行为，必须在真表上执行。

### 线索没有覆盖的改动点

- handler 分流与清扫的测试，线索没有列全（依据 0034 端到端 cloud 1b、0054 决策九第 1、2 条）。①deploy_aws/tests/test_lambda_handlers.py 的 test_kicker_timeout_path_skips_tick_when_not_detached（767 行）、test_exit_observer_skips_non_detached_run 与 test_exit_observer_records_exit_for_detached_run（1174、1182 行），以及全文件 _seed_run 的 detached 参数。②「已收尾的 run 再被触发时 handler 整体 no-op」一节（1021 行起，含 test_finished_run_is_not_reprojected_by_a_late_or_replayed_event、test_timeout_payload_on_a_finished_run_is_a_noop）：新设计下已结束的 run 要清扫（按 startedBy 列 task、逐个停掉），断言要改。③kicker 建两次一次性定时触发、到点复查墙钟、run 已结束时只清扫，需要新增用例。
- deploy_aws/tests/test_stack.py 要新增定时触发与清扫的模板断言（依据 0054 决策九末段权限、0033 资源清单 15），test_reconciler_and_kicker_have_the_same_permission_face（989 行）随之核对。要断言的权限：Scheduler 资源域、推进 Lambda 角色上的 ecs:ListTasks、ecs:StopTask、scheduler:CreateSchedule 与 iam:PassRole。定时触发的名字形态与资源域在 journey 里标为待定，这些断言要等它定下。
- cli 一侧 detached 门控的云端用例，线索没有列（本机的接力用例与测试文件里描述本机接力的文档串已随 run 处置一批删改；依据 0041 决策七「人读形态」、0054 决策八 status --wait 条）。cli/tests/test_backend_cloud.py：test_status_wait_cloud_only_waits_for_a_run_that_is_not_detached、test_status_cloud_pending_hint_offers_relay_only_for_detached_runs_and_stays_quiet_when_the_marker_is_unreadable、test_status_wait_cloud_exits_2_when_the_detached_marker_cannot_be_read。
- 拿不准：deploy_aws/tests/test_lambda_handlers.py 的 test_starter_run_ids_from_direct_kick（160 行）测的是 kicker 收直接调用的 payload。status --wait 不再 invoke kicker 之后（0054 决策八、0034「推进器与触发源」第 2 条），_run_ids_from_runs_stream 里服务 kickoff 的那一路是否保留由实装定，这条用例随之删或改。

### 逐条

#### 测-2（test，M）

- 线索：补对拍用例，本机文件与 moto 两个 adapter 都覆盖
- 要做的：在 test_conditional_writes.py 新增两侧参数化用例：run 已结束时写 job 写不成、运行态不变（DDB 一次 update_item）；job 终态只写一次（第二次终态写不改记录、点名不变）；在 ddb 一侧新增：每次写序号加一、以序号为条件的终态写与结束写只在序号相等时写成、读之后落下的认领或投影挡住它。在 test_cloud_integration.py 新增真 DDB 用例：两个进程以同一序号并发写只有一方写成并使 run 成为终态，几百个 job（带点名标识的实际项大小）的结束写写成，只有一方生成报告。
- 文件：core/tests/test_conditional_writes.py、core/tests/test_cloud_integration.py
- 先要有：结束写入口；update_job_state 新语义；云端写入序号与 jobs 整体替换；JobState 带点名标识（判定明细块）；报告只由写成方生成（报告块，「只有一方生成报告」一条要用）
- 必须同批：moto 与本机部分：与测-1 同批（状态取法与结束写块的端口与 adapter 改动）；真 DDB 部分：云端后端块的 ddb.py 写入序号改动
- 单独先落地的后果：新用例对着旧 code 红（旧 code 照写 job、没有写入序号）。集成用例默认 deselect（-m 'not integration'），不影响默认测试，但不跑就没有证据。
- 验证：moto 与本机部分单测够。真 DDB 部分必须真实执行：并发写要两个真实进程打真表（不是 moto），几百个 job 的结束写要按实际 job 项大小（含点名标识）在真表上写，核写成与 400KB 边界；这些只用开发期自建的真表与 adapter/reconcile 代码，不需要重新部署（tools/ddb_capacity.py 可复用来测项大小与写入消耗）。「经 Lambda 的代码」指 Lambda 用的同一份 core 代码，不要求在 Lambda 里执行，拿不准时在重新部署之后再于云端核一次。
- 备注：跟着「状态取法与结束写」块（结束写、终态只写一次）与「云端后端」块（写入序号）走，点名标识跟「判定明细」块。线索说「写入序号……两个 adapter 都覆盖」，与 0034「两端对拍口径」不符：ADR 写明写入序号的对拍只在 moto 一侧，本机由锁内按整份运行态计算、不带序号，所以序号用例只写 ddb 一侧。0034 机制三②理由段里 1327 写成、1335 被拒的样本是未带点名标识时测的，点名标识会使上限下降，新用例要记下新的上限。

#### 测-4（test，M）

- 线索：机制三删去的测试项对应的测试删或改
- 进度：`_SpyRunStore` 的 try_finalize 覆写与按认领计数的到期用例已随第二批删改；云端同名用例的文档串已改为以写入序号为条件、不再用「推进方」「收尾写」「到期收尾」；「收尾写不带认领计数」的用例已改名为 `test_all_done_after_the_deadline_ends_by_the_terminal_write`。本机的竞态用例与本机多推进器的说法已随 run 处置一批删去；余下云端一半：0054 实测项 7 在重新部署之后用真实云端 run 核（见下「验证」）。
- 要做的：删去本机的 test_expiry_loses_to_a_claim_that_landed_after_the_read（本机锁内的结束写会把新认领的 job 记 aborted、结束 run，竞态不再成立）；云端的同名 _on_ddb 用例保留，文档串改成「被写入序号的条件挡下」，换掉「推进方」「收尾写」「到期收尾」；test_all_done_after_the_deadline_aggregates_without_the_claim_count_condition 改为：全部 job 已有结果时不做结束写，run 随最后一个 job 的终态写按取法成为终态。另删已不成立的「已结束 run 上 job 写照样写成」与本机多推进器的用例。
- 文件：core/tests/test_reconcile.py、core/tests/test_cloud_reconcile.py、core/tests/test_cloud_integration.py
- 先要有：后台推进逐 job 写序（tick 改写：已有结果的 job 先存明细再记终态，结束动作只剩到期结束写）；结束写入口；云端写入序号
- 必须同批：状态取法与结束写块对 reconcile.tick、_finalize、_claim_times 与 project.plan_next 的改动；云端用例另与云端后端块的写入序号同批
- 单独先落地的后果：只删本机竞态用例而 code 不动：无害（少一条用例）。code 改了而测试不动：_SpyRunStore.try_finalize 的覆写与 finalize_counts 断言在本文件多处变红（不止线索列的两条）。
- 验证：本机与 moto 单测够。云端竞态（0054 实测项 7）要在重新部署之后用真实云端 run 核：一个推进器读到「没有执行中、仍有未启动」之后另一方的认领落下，结束写被序号挡下、run 没有结束，并记下新认领的 job 怎样结束。
- 备注：跟着「状态取法与结束写」块（tick 写序、结束写）走，云端一半跟「云端后端」块（写入序号）走，所以本条本身会分到两批。线索说的「第 2 项的云端一半、第 4 项的后半、第 5 项的本机多推进器」指 0034 机制三旧实测项；ADR 那一侧已经改过，线索没有点名对应的测试。我找到的对应项：第 4 项后半就是 core/tests/test_cloud_integration.py 的 test_ddb_job_write_on_finalized_run_lands_job_only_real（151 行，真 DDB 上断言已结束 run 照写 job）；第 5 项的本机多推进器可能指 test_conditional_writes.py 710 行真 DDB 用例文档串里「对位 per-run 进程与 status --wait 接力者」的说法（它在 DDB 上仍成立，只需改文档串）；第 2 项的云端一半没有找到自动化用例。_SpyRunStore（test_reconcile.py 186 行）覆写 try_finalize，整个「到期处理」一节（test_past_stop_start_claims_nothing_and_expires_the_run 等）都靠它与 finalize_counts，要整体改写，见 missing。

#### 测-8（test，S）

- 线索：core/tests/test_status_group.py 模块文档串与 test_create_derives_group_from_the_initial_status
- 要做的：二选一：模块文档串与用例文档串写明「传入终态初始状态」是派生函数在函数层的性质，不出自 0030 决定六；或把 test_create_derives_group_from_the_initial_status 的参数化从 list(Status) 收窄为 PENDING，文档串里的终态一句删去。
- 文件：core/tests/test_status_group.py
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无（只改文档串或收窄参数，现有 code 照样通过）
- 验证：单测够。
- 备注：本身不依赖 code 改动，宜放进「云端后端」块改 runs 表写法（status_group 只在使 run 成为终态的那次写里换值）的那一批，同一文件里调 try_finalize 的 10 处届时也要迁到结束写入口（见 missing）。用例在 86 行，参数化为 list(Status)；模块文档串第 3 行写「含 create_run 传入终态初始状态的情形」。

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
- 进度：本机部分（test_detached_launcher.py 的接力用例与讲接力判定条件的一节、test_definition_schema.py 的两条接力用例、test_sqlite_event_log.py 的那一条、test_main.py 的三条接力用例）已随 run 处置一批删去；余下云端的 handler 分流。
- 要做的（余下）：删 test_lambda_handlers.py「只推进 detached run」一节，连同 test_kicker_timeout_path_skips_tick_when_not_detached、test_exit_observer_skips_non_detached_run 与 test_exit_observer_records_exit_for_detached_run，以及全文件 _seed_run(detached=...) 的参数。
- 文件：deploy_aws/tests/test_lambda_handlers.py
- 先要有：handler 不按 detached 分流（云端后端块）
- 必须同批：与 reconciler._build、exit_observer._is_detached 的删除同批（需要重新部署）
- 单独先落地的后果：分流删了而测试不动：test_reconciler_noop_for_non_detached_run 等断言非 detached 零动作的用例红。
- 验证：单测够的部分：用例删改本身。云端分流去掉之后在重新部署后核 kicker 只被 STATE 新建与终态写触发（实测项 21）。
- 备注：跟「云端后端」块（handler 不分流）走。

## 隧道（0035）与两种 `submit` 的新流程

### 小结

这一块已随隧道一批做完（0018「实装」一节第四批）：SDK 隧道；两种 submit 的交接（`gherkai_runtime.handoff`、`_advance_submitted`、`tunnel_host.hold_tunnel_for_cloud_run`）；删去 `--tunnel-ttl` 与 tunnel.json；前台 run 先取创建时刻再起隧道；`run_requires_backend_stamp(jobs, tunneled=…)`；三份 pyproject 与 uv.lock；讲隧道的用户文档与技术文档。余下：
- 隧道-3 的云端真实验证，等云端后端重新部署。
- skill 与评测资产里讲隧道的几处（行为文档-16、17）。4a 流程块里的取锁已随生命期锁一批改。

### 逐条

#### 隧道-3（mixed，L）

- 线索：云端 `submit`：先过云端各道闸并补全运行定义，取创建时刻、算出运行期限
- 进度：次序、守护进程主体（`tunnel_host.hold_tunnel_for_cloud_run`、`watch_cloud_run`）、交接（`_start_tunnel_watch`、`handoff.WatchChannel`）、删 --tunnel-ttl 与 TTL 记账都已随隧道一批落地；守护进程的几种出口用直接启动、照 submit 做法交接的真实进程核过（0035「实测项」已核的守护进程一条与三种宿主被 SIGKILL 一条）。
- 余下：经真实云端 run 的验证，即 0035「实测项」尚未核的第 1 条：云端 `submit --expose-local` 经真实的 run 执行通过；守护进程读到终态之后退出、之后公网不在线；守护进程在 submit 交出 run 的标识之前与之后各被强杀一次，submit 在交出标识之前被强杀一次。前提是云端后端部署了能读这一版提交记录的版本，随云端后端一批在重新部署之后做。守护进程判断终态用 `DynamoDBRunStore.load_run_state(run_id).status`，云端一批改 runs 表写法之后在同一次真实执行里一并核。

## 随实装改写的 code 注释（指针已处理，行为描述待改）

### 小结

这一块余下 5 条（注释-10 已随「云端只支持 submit」那一批做完，注释-1、注释-4 已随第二批做完，注释-6 已随判定明细点名那一批做完，注释-11 已随隧道一批做完），都是跟着别的块的 code 改动走的注释、文档串与 DEVELOPMENT.md 改写。改动量小：多数条 S，注释-5、注释-7 是 M，散在 core、runtime、cli、deploy_aws 二十来个文件里。每条都不能先落：注释描述的是目标行为，code 一天不改，先改注释就与 code 相反；也不能晚落：符号一删，注释就悬空。所以块内没有先后次序，每条随它所跟的块同一提交。

对别块的依赖与归属：注释-2、5 跟「状态取法与结束写」块（结束写入口、project_state 只推进、前台未启动的 job），注释-5 里归判定明细点名的部分与注释-6 已随那一批做掉，注释-2 另跟「报告」块。注释-7 本机那半已随 run 处置一批做掉；云端那半（_status_cloud、status help 的云端半句）跟 kickoff 删除走，受次序约束，要与后端到期结束 run 同批或在其后，也就是云端重新部署那一批。注释-8 跟「云端后端」块的流过滤与不分流（要重新部署），其中 test_main 那条的用例已随隧道一批按新流程重写，文档串已随 run 处置一批改为标记只作描述。注释-9 只是指针统一，随时可落，宜并进注释-8 那一批。

最大的风险是漏改和漂移。线索只列了一部分位置：仅「接力」一词，线索之外的 production code 命中就有二十多处，其中三处是用户可见文字，另有 detached 分流、try_finalize、run_verdict 与 _NON_VERDICT 的同类残留，见 missing。建议每批提交前按收尾审计的检索词对改到的文件做 grep 差集，不靠读。另一个风险是与 journey 0019 重叠：那份清单按文件列出了要加回的 ADR 指针，同样是「改到某文件时照做」。两份清单涉及同一批文件，每批改注释时应同时取 0019 里同一文件的条目，否则行为描述改了、指针没加回，或者反过来。注释-5 里 RunPersistence.begin 的理由取决于 preflight 去留，那是 owner 还没定的问题；注释-2 要写全「每条来路一句」，取决于「结束写取哪一个来路的说明」那个待定项。这两处要等答复。

### 线索没有覆盖的改动点

- core/gherkai_core/project.py projected_run_status 文档串第 857-861 行：「提前落 run 级终态会被 try_finalize 认成已 finalize」「commit point 的专属性」（依据：0034 机制三②；0031 决定三「结束写」小节）
- core/gherkai_core/model.py：RunState 类文档串第 616-618 行「try_finalize 以条件写落定总 status」；第 197 行（severity 表）与第 222-226 行（TERMINAL_STATUSES 注释）拿 _NON_VERDICT 作对照，_NON_VERDICT 删去后悬空；Status 的 SKIPPED、ABORTED 行内注释第 187-188 行没有写到结束写的来路（到期、处置）（依据：0031 决定三与决定一的表；0054 决策二「一次前台执行可能因三种原因停下」段）
- core/gherkai_core/persist.py：模块头第 12-14 行「commit-point 写序：ResultStore 先逐 job 落 → RunStore.try_finalize 最后写」；类文档串里「finalize（commit point）」；finalize 文档串第 185-186 行指向 project.run_verdict（依据：0030 决定三「逐 job 的提交点」；0031 决定三）
- core/gherkai_core/schedule.py：模块头第 18-20 行「已过停止启动或已发现 run 被别处结束就不启动、不产出判定；否则 run 已中止的记 SKIPPED」；schedule 文档串第 645-646 行与第 653 行「run 级状态与说明由 project.run_verdict 给出」（依据：0054 决策二「一次前台执行可能因三种原因停下」段；0031 决定三）
- 「接力」的线索外命中余下云端的几处（core、runtime 与 cli 本机一侧的已随 run 处置一批改；依据：0034「推进器与触发源」）：runtime/gherkai_runtime/names.py `BASE_KICKER_LAMBDA` 上方的注释（--wait 推理出 kicker 名做 kickoff）；deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py 模块头、`_run_ids_from_runs_stream` 的 kickoff 一格与 kicker 一段（行号以检索为准）；exit_observer.py 模块头
- 按 detached 分流的线索外命中（依据：0034 端到端 cloud 1b「触发过滤不看后台执行标记」）：core/gherkai_core/adapters/run_store/ddb.py DynamoDBRunStore.__init__ 文档串第 207-210 行（detached 参数、kicker 只认它、同步 run 双开推进器）与 create_run 文档串第 226 行；deploy_aws/gherkai_deploy_aws/stack.py 模块文档串第 15-16 行（kicker 只收带 detached 标记的 INSERT）与第 183 行注释
- cli/gherkai_cli/render.py 第 143 行 run_tree 注释「run 级说明：没有任何 job 能承载的原因」，以及 render_run_state 里 run 级消息那一句（依据：0031 决定三「结束写」小节说明表；0037 决策 7）。0019 只记了加回指针，行为描述要改

### 逐条

#### 注释-2（code，S）

- 线索：run 级说明「只给没有任何 job 能承载的原因」改为每条来路都有一句
- 要做的：RunState.message 与 RunResult.message 的注释改为：结束写的每条来路（到期、处置的两行、fail-fast 或中断、运行定义不可用）各有一句说明表里的话，只由结束写写下；RunVerdict 文档串随 RunVerdict 删去；ports 上结束写入口的文档串写明它写 run 级说明；render_index_html 第 357 行那句 run 级说明注释，以及 ddb.py 模块头 STATE 条目里 message「只在推进器不经任何 job 就终结 run 时随 try_finalize 写入」，都按说明表改写。
- 文件：core/gherkai_core/project.py、core/gherkai_core/model.py、core/gherkai_core/ports.py、core/gherkai_core/adapters/report_store/local.py、core/gherkai_core/adapters/run_store/ddb.py
- 先要有：删去 run_verdict 与 RunVerdict、新的 run 状态取法（状态取法与结束写块第 2 条）；结束写入口（状态取法与结束写块第 4 条）
- 必须同批：删 run_verdict 与新取法的那一批；index.html 由结束写结束的 job 的显示（报告块第 2 条），render_index_html 那句随它改
- 单独先落地的后果：测试不红；注释会说「每条来路都有说明」，但 code 仍只在到期或运行定义不可用时写 message，与 code 不符。
- 验证：单测够用：grep「没有任何 job 能承载」应为 0，再跑 doc_rules_check。说明表的句子是否逐来路写下，由状态取法块的单测守。
- 备注：跟「状态取法与结束写」块走，render_index_html 那句跟「报告」块走。逐处核过：project.py RunVerdict 在第 789-793 行，model.py RunResult.message 在第 518-521 行、RunState.message 在第 635-640 行，ports.py try_finalize 在第 176-178 行，report_store/local.py 在第 357 行，ddb.py 模块头在第 13-14 行，都还在。线索没列到的同类注释：cli/gherkai_cli/render.py 第 143 行 run_tree 里的「run 级说明：没有任何 job 能承载的原因」，以及 render_run_state 里 run 级消息那一句（0019 只记了要加回指针，行为描述同样要改）。0031 决定一的说明表里中断来路怎样说明，与「写回时留下」里「结束写取哪一个来路的说明」那个待定项相关，那项没定之前，注释写不全每条来路的句子。

#### 注释-5（code，M）

- 线索：「终态是 finalize 专属」「try_finalize」「判定真值的唯一权威是 jobs/*.json」一类说法改写
- 进度：随第二批第三笔已改的有 run_store/local.py 模块头的状态权威一段与写入口名单、两个 adapter 与端口的 project_state 文档串、NonTerminalSnapshot 的强制点、ports.RunStore 类文档串的 try_finalize 一段，projected_run_status 已删去；ports.ResultStore 文档串与 ReportStore 文档串的「可从 RunResult 完全重建」（改为从记录生成）已随判定明细点名那一批改；fcntl 一段里的「`status --wait` 接力」已随 run 处置一批改；余下的是 RunPersistence.begin 与探活注释（等 owner 定 preflight 的去留）。
- 要做的：run_store/local.py 模块头：「判定真值唯一权威是 jobs/*.json、run_state.json 是投影摘要」改为状态以运行态为准、明细对 scenario/step/归因负责（0030 决定三）；fcntl 一段的写入口名单去掉 try_finalize、加上结束写入口，去掉「status --wait 接力」。local 与 ddb 的 project_state 文档串，「终态是 finalize 专属」改为投影不写 job 终态、run 级只写 running。ports.RunStore 探活注释与 RunPersistence.begin 文档串里拿云端桶名错分裂退出码作理由的一段，按 run 只有本机后端之后的结论改写。NonTerminalSnapshot 的强制点改为保存一个 job 的明细之前。
- 文件：core/gherkai_core/adapters/run_store/local.py、core/gherkai_core/adapters/run_store/ddb.py、core/gherkai_core/ports.py、core/gherkai_core/persist.py、core/gherkai_core/project.py
- 先要有：状态投影只推进运行态（状态取法与结束写块第 6 条 project_state）；结束写入口（状态取法与结束写块第 4 条）；明细点名、去掉 load_all（判定明细点名那一批，已落下）；后台逐 job 写序（状态取法与结束写块第 7 条）；begin 的理由随 run --backend cloud 以退出码 2 结束（已随「云端只支持 submit」那一批做完）失效；owner 定 begin 与端口上 preflight 的去留（写回时留下的问题第 2 条）
- 必须同批：project_state 改为只推进运行态的那一批；RunPersistence.begin 的 preflight 去留定下之后那一批
- 单独先落地的后果：测试不红。说法改成「状态以运行态为准、投影不写 job 终态」，可 project_state 仍把 job 终态投影写进库，注释与 code 相反。
- 验证：单测够用：grep「finalize 专属」「判定真值」「唯一权威」「try_finalize」做差集。project_state 不写终态的行为由 test_conditional_writes 的对拍用例守。
- 备注：跟「状态取法与结束写」块（project_state、结束写、逐 job 写序）和「判定明细点名」块走；begin 那段跟 preflight 待定项走。逐处核过，都还在：local.py 模块头第 7-17 行，local.py project_state 第 301-305 行，ddb.py project_state 第 374 行，ports.py 第 215-217 行，persist.py begin 第 85-87 行，project.py NonTerminalSnapshot 第 657-662 行。疑点：begin 那段改成什么，取决于 preflight 保不保留，这是 owner 还没定的问题，这一处要等答复。线索没列到的同类：ports.py RunStore 类文档串第 137-146 行（生命周期写成 try_finalize 作 commit point，还提到「接力者」）；ports.py ResultStore 文档串「判定真值唯一权威」与固定路径 jobs/<encoded_scope_id>.json；ReportStore 类文档串「可从 RunResult 完全重建、判定真值在 RunResult/ResultStore」；project.projected_run_status 文档串第 857-861 行（被 try_finalize 认成已 finalize、commit point 的专属性）；model.py RunState 文档串第 616-618 行「try_finalize 以条件写落定总 status」；persist.py 模块头第 12-14 行「commit-point 写序……RunStore.try_finalize 最后写」。

#### 注释-7（code，M）

- 线索：接力的描述：reconcile.py 模块头触发源括注里的「status --wait 接力」
- 进度：本机那半（core 的 reconcile.py、project.py、model.py、ports.py、run_store/local.py，runtime 的 detached.py，__main__.py 本机一侧的 `_cmd_status`、`_cmd_status_body`、`_render_status`、`_advance_submitted`、`_advance_store_failure_notice` 与 status 的 `--max-concurrency`）已随 run 处置一批改；余下云端那半。
- 要做的（余下）：_status_cloud 的文档串与注释，以及 status 子命令 --wait、--prefix 的 help 里讲云端接力（检测卡住即调用 kicker）的半句，按云端 status --wait 的新行为改写。
- 文件：cli/gherkai_cli/__main__.py
- 先要有：云端 kickoff 删去（run 处置块处置-3），它又必须与后端到期结束 run 同批或在其后（云端后端块第 4 条，见「分批的次序约束」）
- 必须同批：删 kickoff 的那一批，也就是云端重新部署的那一批或之后
- 单独先落地的后果：测试不红，除非 status help 的文字被测试锁定。产品面：help 会写成云端也只处置，code 仍在云端调用 kicker，使用方看到的说明与实际行为相反。
- 验证：注释与 help 的改动用单测加 grep 差集：production code 里「接力」应为 0（收尾审计词），test_user_facing_messages 照常通过；「接力推进」进退役词表后由测试守。
- 备注：受「分批的次序约束」第一条限制（要与后端到期结束 run 同批或在其后），与云端重新部署的那一批绑在一起。线索之外的「接力」命中见 missing。

#### 注释-8（mixed，S）

- 线索：按 detached 分流的描述：ddb.py `is_detached` 文档串后半句
- 要做的：ddb.is_detached 文档串的后半句（云端推进器据它分流、同步 run 双开推进器）改为只供 list-runs --json 的 detached 键；ddb 模块头与 _state_item 的「kicker filter 认它」删去；exit_observer.py 模块头与 _is_detached 随分流删去；reconciler._build 与 _run_ids_from_runs_stream（status --wait kickoff 一格）、stack._reconcile_lambdas（三个 handler 自己分辨、kicker 靠流过滤）、compose.build_cloud_stores「触发 kicker 冷启动」一句都按两条流过滤与不分流改写；test_ddb_run_store 那条测试的文档串改为标记只作描述（test_main 那条已随 run 处置一批改）。
- 文件：core/gherkai_core/adapters/run_store/ddb.py、deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py、deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py、deploy_aws/gherkai_deploy_aws/stack.py、runtime/gherkai_runtime/compose.py、core/tests/test_ddb_run_store.py
- 先要有：kicker 的流过滤改为两条（云端后端块第 2 条）；handler 不按后台执行标记分流（云端后端块第 3 条）；kickoff 删去（run 处置块第 3 条），_run_ids_from_runs_stream 的 kickoff 一格才能删
- 必须同批：云端后端块第 2、3 条，与云端重新部署同一批
- 单独先落地的后果：测试不红；注释说不分流，Lambda 与流过滤仍按 detached 分流，注释与部署出去的行为相反。
- 验证：注释改动用 grep 差集（detached、filter、kicker 冷启动）。分流与过滤的行为要在重新部署之后的云端真实验证（一个云端 submit 的 run 由 kicker 冷启动、观察者照写），这属于云端后端块，这条只靠单测与 deploy_aws/tests/test_stack.py 的模板断言。
- 备注：跟「云端后端」块第 2、3 条走，属于要重新部署的一批。逐处核过，都还在：ddb.py 模块头第 19 行、_state_item 第 272 行、is_detached 第 721-736 行；exit_observer.py 第 9-10 行、第 21 行、第 55-67 行；reconciler.py 第 450 行、第 486-495 行（_build）；stack.py 第 588-601 行、第 733-745 行；compose.py 第 1118 行；test_ddb_run_store.py 第 131-132 行。journey「核对时补上的条目」第 2 条（_submit_cloud 里 detached=True 的注释）是同一类，应与这条同批。线索之外：ddb.DynamoDBRunStore.__init__ 文档串第 207-210 行（detached 参数、同步 run 双开推进器）、create_run 文档串第 226 行，stack.py 模块文档串第 15-16 行（kicker 只收带 detached 标记的 INSERT）与第 183 行，都没有列。

#### 注释-9（mixed，S）

- 线索：RunState 写入方的指针：stack.py `_grant_task_role` 与 `_reconcile_lambdas`
- 要做的：stack.py 第 392 行与第 640 行、test_stack.py 第 439、453、903 行的「RunState 的写入方见 ADR 0034『数据模型三件套』」，统一改为 0024 红线条用的 0034「命令形态」（那里的表列出谁写 RunState）。
- 文件：deploy_aws/gherkai_deploy_aws/stack.py、deploy_aws/tests/test_stack.py
- 先要有：无
- 必须同批：exit-observer 不再读 runs 表（云端后端块第 3 条）：第 639-640 行的注释与 test_exit_observer_can_read_runs_table_only 会随它重写，同批落地可以少改一遍
- 单独先落地的后果：无。两处指针所指的小节都存在，只是统一写法；单独先落也不破坏测试与产品。
- 验证：单测够用：跑 deploy_aws/tests/test_stack.py，再跑 doc_rules_check 或悬空指针护栏确认指针目标存在。
- 备注：这是指针统一，不依赖行为改动，可以排在任何一批；_grant_task_role 与 test_task_role_has_events_putitem_not_runs 两处随时可改。_reconcile_lambdas 第 639-640 行和 test_exit_observer_can_read_runs_table_only 第 903 行会随「云端后端」块第 3 条（观察者去掉 runs 表读权限）重写，建议并进那一批。已核实 0034 的「数据模型三件套」（第 22 行）与「命令形态」（第 33 行）都在；0024 第 278 行红线条指向「命令形态」。

## 行为文档（随所改行为的实装批同一提交改）

### 小结

这一块余下 11 条，全是文档（含 3 张图、评测 fixture 与 evals.json、契约页的生成副本与一处测试），本身没有生产 code，总量相当于几百行文档改写，最大的是 execution-and-reconciliation.md 的大面积重写（L）与 fixture 重录。每条都跟在别的块后面：①「状态取法与结束写」「判定明细点名」块 → 行为文档-2（写序部分）、6（键与取法）、8（fixture，判定明细的新形态已转换，余下带引擎重录）、10（到期与中断条目）；②「本机推进器、生命期锁」的删本机接力已随 run 处置一批做完（3 整条删去，2、5、7、10 里已注明）；③「run 处置」块的本机一半已随同一批做完（1、14 整条删去，6 里已注明），余下云端一半的处置权限与 settle-runs 接云端 → 5、7、19；④「云端后端」块（kicker 过滤、handler 不分流、清扫）→ 2 的 §7；⑤「云端只支持 submit」块已做完（3、5、6、7、9、10、19 里归它的部分已从各条删去，18 整条删去）；⑥「隧道」块的余下部分 → 16 与 17（12，即 4a 流程块的取锁，已随生命期锁一批做完、删去）（skill 与评测资产，随 skill 打磨批）；⑦「词表与退役词」块 → 9（execution-timeout-chain）。有测试守、必须与 code 同提交的是：契约页（test_cli_json_contract 收集真渲染器的键与 doctor 项名，副本由 test_skill 比对）、skill 正文（test_skill 用真 parser 核 flag 归属，改 flag 时即红）、图（导出与图源一致、退役词扫描）、退役词入表（扫 CHANGELOG 与图源）。其余条目没有测试守，漏改不会变红，要靠收尾的残留检索。最大的风险：一是行为文档-2、5、6、7、10 这几条各跨三到六块，排批时必须按块拆开、各随各的 code 批，否则文档会先于或落后于 code；二是这一块的线索按「点名的段落」列，同一文件里随同一行为失真的其它段落有不少没被列入（见 missing），只按线索改会留下漂移；三是 fixture 重录与评测、权限表要真实执行（引擎与 Device Farm、Bedrock 评测、重新部署后用最小权限角色），单测不证。

### 线索没有覆盖的改动点

- docs/internals/cli-json-contract.md（与生成的 skill 副本）里线索没点名的几行（run 一节 artifacts.jobs_dir 一行已随判定明细点名那一批改）：status 一节 status 行（skipped 只在全部 job 都没有执行时出现、aborted 只来自被中断的同步 run）与 message 行（「这些 job 保持 pending」，说明只在没有 job 能承载时才有）；list-runs 一节 --status 不再接受 skipped（detached 一行已随 run 处置一批改）；doctor 一节项名表加 report_dir.filesystem。依据 0031 决定三取法与「结束写」说明表、0030 决定三、0041 决策三、四、七、0054 决策八。
- docs/user-guide/running-and-results.md 里属于新行为、线索没写的：「找回 run_id：list-runs」一节加「已运行」「允许运行至」两列与期限提示，不带 --wait 的 status 的期限提示（退出码表里 run 与本机 submit 在报告目录不过边界检查、给 run 的目录加锁失败时以退出码 2 结束已随生命期锁一批写进；settle-runs 的命令表与退出码表各一行、删去「由前台 run 执行…只等待、不接力」的提示，以及同文件讲本机接力的各处，已随 run 处置一批改）。依据 0041 决策七。
- docs/diagrams 下线索没写的图源改动（改完都要用 tools/build_diagrams.mjs 重出 SVG/HTML）：run-execution.json 里「status --wait 两个后端不同」一处云端的半句（「云端仅在检测到停滞时唤醒推进函数」）；execution-detached-gates.json 整张图（后台标记的两道判断）在 kicker 不看后台标记、handler 不分流之后不再成立，要删图或重画，连同 execution-and-reconciliation.md §7 的嵌入与图注（run-execution.json 与 execution-timeout-chain.json 里讲本机接力的几处已随 run 处置一批改）。依据 0034 端到端 cloud 1b、0045 决策七。
- deploy_aws/DEVELOPMENT.md 里随「云端后端」块失真、线索没写的几处：第 40 行 exit-observer「另读 runs 表以判断 run 是否 detached」；第 41 行 kicker「status --wait 的主动调起」与推进器权限（要加建 run 两次定时触发、按 startedBy 列 task 清扫）；第 44 行 runs 表 Stream filter「INSERT 且 NewImage.detached=true」（改两条过滤）。依据 0034 端到端 cloud 1b、0054 决策九、0033 资源清单 13、15。
- cli/DEVELOPMENT.md 第 18 行：argparse 子命令清单加 settle-runs，内部子命令 _reconcile 说明里建 run 那一步补上边界检查与取锁（现在写的是「起隧道、生成运行定义、建 run、装配、回报、推进」）。模块清单的登记已做：处置模块 `settle.py` 随 run 处置一批登记在 runtime/DEVELOPMENT.md；生命期锁与边界检查放在 core 的 `adapters/run_store/run_dir.py`，随生命期锁一批登记在 core/DEVELOPMENT.md，持有者 `compose.process_lock_holder` 登记在 runtime/DEVELOPMENT.md 的 0054 一行。依据 0054 决策三、四、六至八、0035 决策 3「本机 submit」。
- CHANGELOG.md [Unreleased] 里新的使用者可见行为的条目：doctor 新增 report_dir.filesystem、list-runs 新列与 deadline_at、run --json 的 jobs[]、index.html 显示由结束写结束的 job（报告目录文件系统不在清单里时 run 与本机 submit 以退出码 2 结束一条已随生命期锁一批写进，settle-runs 新命令与 status --wait 把管它的进程已不在或已过期限的 run 记为已结束两条、其中 run 目录不在受支持的文件系统上时的处理，已随 run 处置一批写进）。线索只要求改写已有条目并加一句重构概述，owner「升级与迁移的细节不写」是否也排除这些新功能条目拿不准，要排批时问 owner。依据 0054 决策四、八、0041 决策三、四、七、0027「index.html 形态」。
- docs/internals/cloud-backend-carriers.md 第 11 行 stack 资源与 Scheduler 名字要补上 run 的两次一次性定时触发（名字定下之后）（architecture-overview.md 讲本机接力的半句已随 run 处置一批改）。依据 0054 决策九、0033 资源清单 15。

### 逐条

#### 行为文档-2（doc，L）

- 线索：docs/internals/execution-and-reconciliation.md：收尾的写序（try_finalize、
- 进度：第二笔改了 §1 两种驱动里的中断与到期、§3 前台生命周期、§4c 的 run 级终态与收尾写序、§6 的到点归因；第三笔改了 §1 的推进步骤、§4a 流程块里的逐 job 写序与运行定义不可用、§4c 的后台写序（投影不写终态、先写终态后决策、运行定义不可用）与读者保证；本机接力与 run 处置各处已随 run 处置一批改，生命期锁（4a 流程块里的取锁）已随生命期锁一批改；kicker 过滤与云端 kickoff 各处随云端后端一批。
- 要做的：按新设计重写这篇的大部分：§1 第 14、16 行（detached 分界、四个 tick 宿主、接力者）、§4a 第 58–68 行流程块（per-run 进程、status --wait 接力）、§5 第 91 与 96–101 行（run 级取值、try_finalize 提交点、jobs/*.json 写序、竞争收尾、两道判断、中途终止）、§6 第 140、143 行（接力判超时、补写）、§7 第 157–167 行（kicker 按 detached 过滤、handler 分流、权威指针）。新写法：逐 job 写序与点名、结束写、生命期锁与处置、kicker 两条过滤与清扫。
- 文件：docs/internals/execution-and-reconciliation.md
- 先要有：「状态取法与结束写」块（结束写、逐 job 写序）；「判定明细点名与落库写序」块（已落下）；「本机推进器、生命期锁与边界检查」块（含删本机接力）；「run 处置」块；「云端后端」块（kicker 两条过滤、handler 不分流、清扫、两次定时触发）
- 必须同批：与上面每一块各自的实装批同一提交改对应小节
- 单独先落地的后果：单独先改：文档描述的机制在 code 里还不存在；不改：每一批 code 落地之后这篇的相应小节立即失真。测试不受影响（第 167 行的「filter 必须区分写入者」「兜底/接力」条名指针已悬空，但没有测试守它）。
- 验证：文档改动，按批核对 diff 与 code 一致；退役词入表之后 test_user_docs 会扫它。
- 备注：一条跨五块（「云端只支持 submit」那部分，即 §3 与三种组合，已做完），分批时要拆：§5 写序跟「状态取法与结束写」+「判定明细点名」；§1/§4a/§5 第 98、101 行/§6 接力部分跟「本机推进器、生命期锁」块删接力那一批与「run 处置」块；§7 与第 16、80 行 kickoff 跟「云端后端」块与「run 处置」块里删 _STALL_KICK 那一条；4a 流程块第二行的取锁已随生命期锁一批改。§7 嵌的图 execution-detached-gates 整张所讲的「两道拦截」在新设计里不再成立，线索没写，见 missing。线索里的「local submit 的超时一行（per-run 进程）」对应第 140 行。

#### 行为文档-4（doc，S）

- 线索：docs/internals/artifacts-and-evidence.md：explain 文本形态表里「诊断细节见
- 要做的：第 103 行判定行的条件补一句：「诊断细节见 worker 日志」只对运行态里带认领时刻的 job 打；由结束写记 skipped 的、运行定义不可用时由 pending 记 error 的 job 只给状态与说明。
- 文件：docs/internals/artifacts-and-evidence.md
- 先要有：「查看命令与机读输出」块 explain 两条（render.py explain_tree/explain_to_dict 按认领时刻决定是否打这句）；「状态取法与结束写」块的结束写（产生没有认领时刻的终态 job）
- 必须同批：改 render.py 这一逻辑的实装批
- 单独先落地的后果：只改文档：现在的 code 按「没有 step 记录」判断，文档会与 code 不符；测试不受影响。
- 验证：文档改动，读 diff；对应 code 由单测覆盖。
- 备注：跟「查看命令与机读输出」块的「诊断细节见 worker 日志」一条走。同一篇里讲判定明细存放与读法的几处已随判定明细点名那一批改。

#### 行为文档-5（doc，M）

- 线索：用户指南：configuration.md 的 `[cloud]` 节键表去掉 events-table
- 要做的：running-and-results.md 权限表与 getting-started.md 角色表的云端一级按 0040 派生视图改为 submit、status --wait、settle-runs：去 lambda:InvokeFunction、留 lambda:GetFunction，加条件写、s3:GetObject 与写报告，推论改为不需要任何 ECS 写权限。（[cloud] 四键、run 的云端参数、「仅 --backend cloud」段与三种组合已随「云端只支持 submit」那一批做完，configuration.md 的 --max-concurrency 一行不再列 status 已随 run 处置一批做完。）
- 文件：docs/user-guide/running-and-results.md、docs/user-guide/getting-started.md
- 先要有：「run 处置」块的云端一半（settle-runs 接云端、status --wait 处置、删 kickoff）
- 必须同批：settle-runs 接云端与删 kickoff 的那一批（权限表部分）
- 单独先落地的后果：只改文档：权限表少了 lambda:InvokeFunction，按文档配权限的成员在 status --wait kickoff 时被拒。测试不受影响（test_user_docs 只查措辞与链接）。
- 验证：权限表要真实验证：重新部署之后用一个只带文档所列权限的角色真实执行 submit、status --wait（含处置一次过期 run）、settle-runs，确认没有 AccessDenied。
- 备注：权限表跟「run 处置」块的云端一半（新增处置权限），删 InvokeFunction 跟删 _STALL_KICK 那一条。getting-started.md 角色表「需要什么凭证」一列是权限的派生视图，现在写的是安装形态与凭证概述，要改多少拿不准，以 0040 决策 3 为准。

#### 行为文档-6（mixed，M）

- 线索：机读契约页与它的 skill 副本：写出 settle-runs 的 `--json`
- 进度：run 一节的 status、message、jobs[] 两种形态与末段，status 一节的 status 取值、message 与 jobs[].message，explain 一节没有明细的 scope，已随第二笔改（测试改写见 test_cli_json_contract.py）；status 一节 jobs[] 的 `result_id`、artifacts 的 jobs_dir 一行、explain 一节退出码 2 的清单与 `scopes[]` 的说法已随判定明细点名那一批改（test_status_json_keys_are_documented 收得到 `result_id`）；settle-runs 一节与 list-runs 的 detached 一行已随 run 处置一批写出；余下 deadline_at 与 doctor 新项。
- 要做的：docs/internals/cli-json-contract.md 新增 settle-runs 一节（dry_run、runs[]、outcome、reason 与落点字段），run --json 顶层 status/message 按新取法改写并加 jobs[] 全部 job 的形状，status 一节加 deadline_at 与 jobs[] 的点名标识键，list-runs 加 deadline_at；改完用 tools/render_skill_contract.py 重新生成 skill 副本；cli/tests/test_cli_json_contract.py 里 test_run_json_top_level_message_is_always_present_and_documented_as_run_level 断言的「没有执行」原句随之改。
- 文件：docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py
- 先要有：「查看命令与机读输出」块（run --json jobs[]、status --json 点名标识与 deadline_at、list-runs deadline_at、doctor report_dir.filesystem）；「run 处置」块的 settle-runs 命令；「状态取法与结束写」块（run 级取法与说明）；「判定明细点名」块（点名标识的键名 `result_id`，已落下）
- 必须同批：每个新增 JSON 键的那一批 code：test_cli_json_contract 用真渲染器收集全部键名、逐个断言出现在本页对应节，漏写即红；副本：test_skill.py test_contract_copy_equals_transform_of_source 断言副本等于转换结果，源页改了必须同提交重新生成；doctor 项名：test_cli_json_contract 第 333 行逐个对照 doctor 的 name 值，加 report_dir.filesystem 的 code 批必须同提交写进契约页
- 单独先落地的后果：只改文档不改 code：契约页写了 code 不产出的键，测试不红（只查 code 键在文档里），但对读者是错的；只改 code 不改文档：test_cli_json_contract 红；只改源页不重生副本：test_skill 红。
- 验证：单测够：test_cli_json_contract 与 test_skill 的差集护栏覆盖键名与副本一致；语义描述读 diff。
- 备注：一条跨四块，按键所属的 code 批拆开写，各自同提交。线索没写到、同页也要改的：status 一节 status 行「skipped 只在全部 job 都没有执行」「aborted 只来自被中断的同步 run」与 message 行「这些 job 保持 pending」（随状态取法改）；list-runs 一节 detached 行「status --wait 对它只等待、不接力」与 --status 不再接受 skipped；doctor 一节项名表加 report_dir.filesystem（线索放在「查看命令」块，但落在本页）。见 missing。test_run_json_top_level_message_... 的文档串与断言都要改写，不只换一句原文。

#### 行为文档-7（doc，S）

- 线索：agent skill 正文按 0043 决策五骨架改：第 3 步写明云端后端的执行只经
- 进度：SKILL.md 第 5 节去掉直接读 jobs/*.json 的说法、第 10 节「别解析」一条加上 `jobs/` 下的明细文件（一个 job 可能有多份、算数的那份由运行记录定），已随判定明细点名那一批做（最小修补）。正文已到 11999 字符，离 test_skill 的 12000 上限只剩 1 个字符，再加内容要先压缩。
- 要做的：--scope 取值写成 --json 输出里的 scope_id（受字符上限所限，并进 skill 打磨批）；references/cloud-backend.md「1 分工」表按 0040 派生视图改（QA/CI 一行加 settle-runs）。（第 3 节与第 7 节旗标表已随「云端只支持 submit」那一批做完，第 8 节的「它同时是接力」已随 run 处置一批删去。）
- 文件：cli/gherkai_cli/skills/gherkai/SKILL.md、cli/gherkai_cli/skills/gherkai/references/cloud-backend.md
- 先要有：「run 处置」块的云端一半（settle-runs 接云端）
- 必须同批：各条所属的实装批：test_skill.py 的 test_flags_are_attached_to_the_right_subcommand 与 test_exclusive_claims_are_true 用真 parser 核对 skill 里每个 flag 的归属，改 flag 的那一批要同提交改 skill
- 单独先落地的后果：只改 skill：agent 按新说法指导用户，但 code 里 status --wait 仍接力，属于描述先行；测试不红。只改 code 不改 skill：parser 的 flag 归属一变 test_skill 即红。
- 验证：test_skill 的 parser 对照与措辞护栏是单测；skill 行为变化按 0043 决策七的评测验证，是否要重跑评测由打磨批定。
- 备注：1 分工表跟「run 处置」块的云端一半，--scope 的取值跟 skill 打磨批。

#### 行为文档-8（mixed，M）

- 线索：评测 fixture 随实装重录：文件集改为 run_meta.json、run_state.json、运
- 进度：判定明细点名那一批用一次性脚本（放系统临时目录、不进仓库）把带录制报告的 4 个 run（wiki-search、job-failure、nova-zh、device-session-lost）转成新形态：每个有明细的终态 job 生成一个 16 位小写十六进制标识，`jobs/` 下的文件改名为 `<标识>.json`（内容不变），run_state.json 的条目加 `result_id`；materialize.py 模块头讲 jobs/ 文件名的说法随之改，完整性检查另核 `explain --json` 列出的 job 恰是点名了明细的 job。这四个 run 的 job 都由执行结果结束、都有明细，转出的形态与产品写出的逐字段相同，评测基线的内容不变。转换之后用工作区的读法（`LocalRunStore` 读运行态、`named_details.load_named_details` 读明细）逐个核过：每个终态 job 都被点名、读得到且属于它，`jobs/` 下没有没被点名的文件。materialize.py 的完整性检查在这一批之前就过不了，与点名无关：四个 run 的 `run_meta.json` 是结构版本 1（录于 1.4.9.post169 与 post300），运行定义的结构版本升到 2 之后，`explain --json` 读头部时即以退出码 2 结束（「记录是第 1 版，本机只认第 2 版」）。改正有两条路：用一次性脚本把四份 `run_meta.json` 升到第 2 版（要补 `deadline_at` 与第 2 版的固定键，期限要按当时的预算推出），或等下面的重录一并解决；交 owner 定。四份 `run_state.json` 另缺顶层的 `claim_count`（产品现在写出它，读法缺键时按缺省读入，不挡读取），选一次性脚本时一并补上。**改正之前评测无法进行**：物化之后的完整性检查对四个 run 都以 `explain --json` 退出码 2 失败；pytest 不执行这项检查，全量测试绿不说明 fixture 可用。改正之后用当前 CLI 执行一次完整性检查，过了才算可用。
- 要做的（余下）：带引擎重录这 4 个 run，放在报告形态定型之后（0018「现在做不了」表里评测 fixture 一行定的时机：云端一批落地之后），届时统一重录一次，免得两次改动评测内容。
- 文件：skills/gherkai-evals/fixtures/wiki-search/reports/、skills/gherkai-evals/fixtures/job-failure/reports/、skills/gherkai-evals/fixtures/nova-zh/reports/、skills/gherkai-evals/fixtures/device-session-lost/reports/、skills/gherkai-evals/materialize.py
- 先要有：「报告」块（index.html/manifest 由记录生成，录出的报告形态随之变）
- 必须同批：无（判定明细的新形态已转换，按新读法读得到；`run_meta.json` 的结构版本 1 仍挡住当前 CLI，见上「进度」）
- 单独先落地的后果：无：重录只换成真实写出的形态。
- 验证：要在带引擎的环境里真实执行一次录制（Nova Act 与 Midscene 都要用，device-session-lost 要 Device Farm 真机），按 0043 决策七的录制约束处理，然后执行 materialize.py 的完整性检查，并跑 test_skill 的 fixture 护栏。重录有 AWS 与 Device Farm 费用，开发期不计。
- 备注：eval 27（triage-device-session-lost）的评测要求里列了 jobs/*.json 作为「先 explain 再读」的文件类，目录名不变，文件名改为标识后仍匹配，不用改。

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
- 进度：到期与中断两条已随第二笔改写，另加了一条 run 的输出出自运行记录、没有启动的 job 的形态（与已发行版本比）；讲本机接力的条目已随 run 处置一批改写；余下讲云端 status --wait 接力的说法与重构一句。
- 要做的：CHANGELOG.md [Unreleased] 里接力两条、到期记 error 一条、中断记 aborted 一条直接改写为新行为（或删去），不写对照，保留与已发行版本相比的「此前……」；另加一句 run 的推进、处置与状态取法做了重构。（云端前台 run 的各条与删 SSM 两个参数的一句已随「云端只支持 submit」那一批做完。）
- 文件：CHANGELOG.md
- 先要有：「本机推进器、生命期锁」块删本机接力（接力两条）；「状态取法与结束写」块的取法与终结函数 timeout 拆行（到期与中断两条）
- 必须同批：各条所描述行为的那一批（退役词「接力推进」入表时第 59、60 行若含它会被 test_user_docs 扫到，要同提交改）
- 单独先落地的后果：只改 CHANGELOG：发行说明描述了未实装的行为；不改：每批 code 落地后条目与产品不符。测试只在退役词入表时可能红。
- 验证：文档改动，读 diff；test_user_docs 与 test_release_notes 查措辞与链接。
- 备注：一条跨两块，按条目所属的批拆开改。到期一条写「被它截断的 job 判 error、归因 timeout」「run 总状态记 error」，新设计里被期限截断的执行中 job 记 aborted、没有归因，pending 记 skipped，run 按取法为 aborted，要整句重写。线索只要求改写已有条目并加一句重构概述；settle-runs、报告目录边界检查（不支持的文件系统以退出码 2 结束）、锁已被持有时以退出码 2 结束、list-runs 新列、run --json 的 jobs[]、doctor 新项这些新的使用者可见行为要不要各写一条，线索没说，拿不准 owner 的「升级与迁移的细节不写」是否也排除新功能条目，见 missing。

#### 行为文档-16（doc，M）

- 线索：agent skill 里讲隧道的各处按 ADR 0035 改写（隧道一批只做了最小修补）
- 要做的：SKILL.md 第 3 节加上入口到运行期限加 300 秒在边缘关闭；references/setup-and-diagnosis.md 第 1 节「装什么」加 [tunnel]，第 5 节「被测应用收到的 Host 头」一条按账号区分域名、「隧道断了不自动重连」改为不写成无条件，第 7 节症状表「--expose-local 以退出码 2 结束」一行按四种说法写、地址已在线（ERR_NGROK_334）时照第 3 种说法写处理办法、不另作概括，「run 中途开始每条 scenario 都导航失败」一行的原因栏补上「宿主被暂停」。（第 3 节前置、--tunnel-ttl 两处、第 5 节的 PATH 前置、ngrok config、TTL、kill -9、排障入口，以及 cloud-backend.md 第 94 行已随隧道一批改。）
- 文件：cli/gherkai_cli/skills/gherkai/SKILL.md、cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md
- 先要有：无
- 必须同批：行为文档-17（评测要求是这几处改写的打分依据）
- 单独先落地的后果：不涉及 flag 变化，test_skill 不受影响；SKILL.md 正文接近 12000 字符上限，加句之前先压缩。
- 验证：test_skill 守 flag 归属与措辞；skill 行为按评测验证（见行为文档-17）。
- 备注：随 skill 打磨批或收尾做。依据：0043 决策五骨架第 3 条；0035 决策 1「启动失败的说法按原因分」「实测依据」、决策 2、决策 3「边缘到点拒绝」；0037 决策 2c。

#### 行为文档-17（doc，S）

- 线索：agent skill 的评测资产随隧道的行为文档同一批改
- 要做的：skills/gherkai-evals/evals.json 中 id 22（tunnel-origin-mismatch-and-host-block）的评测要求「因为域名每个 run 都会换」与 expected_output 的「免得每 run 换名再改」按地址随账号不同核对改写；notes 记下这一轮尺子的改动（id 10 的前置与 --tunnel-ttl 两条已随隧道一批改，notes 没有记）。是否加「公网入口到点在边缘关闭」的新评测要求，随行为文档-16 是否在 SKILL.md 第 3 节写进这一句一起定。
- 文件：skills/gherkai-evals/evals.json
- 先要有：行为文档-16（skill 隧道改写）
- 必须同批：行为文档-16
- 单独先落地的后果：只改评测：with-skill 臂按旧 skill 回答会被新尺子判不过；只改 skill 不改评测：按账号区分域名的回答可能被旧尺子判不过。pytest 不受影响。
- 验证：要真实执行评测：按 0043 决策七的流程在 Bedrock 上执行 expose-local-app 与 tunnel-origin-mismatch 两条（with-skill 与 baseline 两臂），看新尺子下的通过率；单测不证。
- 备注：与行为文档-16 同批。

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

这三小块的 code 改动不大，主要是收尾、跨块的连带改动与待定问题；写 code 的只有补-3、问-2 这两处，各在 S 到 M 之间。先后次序：收尾-1、收尾-2 必须排在所有实装批之后（0011 与 0051 的 Status 头那一句还要等隧道批）；补-x 各自挂在别的块的批上：补-1、补-6、补-7 已随「云端只支持 submit」那一批做完、已删去，补-2、补-3、补-4 随「云端后端」批（补-3 与补-4 是那一批开工的前置决定，补-3 还要在重新部署之后真实执行核 IAM 与名字长度），补-8、补-9 随各自对应的行为改写批。问-x 里真正挡住开工的有五组（问-1 与问-6 已随第二批第二笔定下、删去）：问-12 挡重试原因的取法；问-2 挡 begin 与端口 preflight 的清理；问-11 挡词表批的范围；问-14 挡 doctor 一行；问-16 挡 _status_cmd（读不出运行态那一支已由 owner 定下、随 run 处置一批落地）。另有一些只涉及 ADR 或用户文档：问-3、问-4、问-7、问-13 只改 ADR；问-8 要先于用户文档权限表那一批定。有三条已经被处理掉、与线索不符：补-5 已在 b0cd6349 里改完；问-10 的模块头已不含「决策二」；问-5 核实为到得了，只需补前提。最大的风险在收尾的残留检索：它的检索面漏了 tools/ 与 engines/，词表漏了隧道与前台云端执行的一批旧说法；Status 头那一句的删除还缺一道「实测项已逐项核并内联」的审计。不补上这两点，删掉那一句之后 ADR 会宣称已实装，而证据与残留其实还没清。

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
- 进度：verdict-model.md 与 troubleshooting.md 的到期部分已随第二笔改；余下讲接力的各处。
- 要做的：各文档跟随对应的实装批改：verdict-model.md（run 级取法、job 级 skipped 来自结束写，第 102 行「排队中的 job 起 worker 前看到它即记 skipped」等）、troubleshooting.md、local-app-testing.md、running-and-results.md 里讲接力的各处（分别有 2、1、5 处「接力」）、deterministic-step-lifecycle.md 第 83 行「三处宿主…status --wait 接力者」。（_doctor_worker_grace 文档串与 WorkerResolution.stop_timeout_s 两项已随「云端只支持 submit」那一批做完，字段连同填值删去。）
- 文件：docs/internals/verdict-model.md、docs/user-guide/troubleshooting.md、docs/user-guide/local-app-testing.md、docs/internals/deterministic-step-lifecycle.md、docs/user-guide/running-and-results.md
- 先要有：状态取法与结束写批（verdict-model）；删接力批（各篇讲接力的段落）
- 必须同批：各自对应的实装批（每批提交带上它所改行为的文档）
- 单独先落地的后果：提前改的话，文档描述的行为 code 里还没有。
- 验证：doc_rules_check 加 pytest（test_user_docs 等）；纯文档，单测够用。
- 备注：无。

#### 补-9（doc，S）

- 线索：docs/internals/verdict-model.md 与 docs/internals/execution-and-reconciliation.md 里有三处指针
- 进度：verdict-model.md 那一处已随第二笔改指 0031 决定一「aborted 来自主动中止与 run 的期限，不来自 job 自己的预算」注；余下 execution-and-reconciliation.md 讲接力那一格，随删接力。
- 要做的：按新行为改写两篇时，去掉两处已经悬空的条名：verdict-model.md 第 102 行「0031 决定一的注（aborted 只认主动中止…不认 timeout）」，以及 execution-and-reconciliation.md 第 140 行「0054 决策二『本机接力的改法』」。（execution-and-reconciliation.md §7 的「0034『filter 必须区分写入者』条与『兜底/接力』条」已随「云端只支持 submit」那一批改指 0016 决策 A。）
- 文件：docs/internals/verdict-model.md、docs/internals/execution-and-reconciliation.md
- 先要有：状态取法与结束写批、删接力批、kicker 过滤改写批里对这两篇的改写
- 必须同批：这两篇随行为改写的那几批
- 单独先落地的后果：单独去掉指针是安全的，只是三处所在的句子本身也是旧行为，单改指针要再改一次。
- 验证：差集法：从两篇抽出所有「ADR NNNN『条名』」，到对应 ADR 里 grep 条名，零缺失。
- 备注：两处都已确认存在。第 140 行那一格整格都在讲接力判超时（「接力者按…补写」），删接力时整格重写，指针随之消失。

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
- 进度：结束写的来路已定为按登记先后（停止启动与中止标志登记在一处、只记第一次，0031 决定三「结束写」小节、0026「起 worker 与重试之前的检查」）；余下检查次序的依据，以及等待重试的 job 注明原因是否同样改按登记先后，第二笔不处理、按 ADR 现文。
- 要做的：定下检查次序的依据，以及等待重试的 job（按固定次序取最先命中的原因，_Worker._retry_refused）与执行中的 job（按最先登记取原因，_AbortFlag）是否统一取法。写进 0054 决策二，0026、0028 改为指过去。
- 文件：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md、docs/adr/0026-schedule-module.md、docs/adr/0028-transient-network-ssl-resilience.md、core/gherkai_core/schedule.py
- 先要有：无
- 必须同批：无
- 单独先落地的后果：不定的话，_retry_refused 注明的原因（重试之前的检查按分支落实，状态取法与结束写块）照现行次序实现，日后改取法要再改一次 code 与测试。
- 验证：单测：重试退避期间先后让两种原因成立，断言注明的原因。
- 备注：我的判断：次序里「已发现 run 被别处结束」的位置不影响记录。它在哪一步命中都不写终态，而且写也写不成（0054 决策五），所以只有「已过停止启动」与「fail-fast 或中断」两者的先后决定注明的原因。显然的统一取法是都按最先登记，与执行中的 job 一致；固定次序只剩一条可写的依据：时间检查不依赖任何其它状态。交 owner。

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
- 先要有：边界检查的共用判断（已随生命期锁一批落地，在 core 的 `run_dir`）
- 必须同批：doctor 新增 report_dir.filesystem（查看命令与机读输出块）
- 单独先落地的后果：不定也能写边界检查本身；挡住的只是 doctor 那一行与契约页。
- 验证：单测：契约护栏。另在本机 APFS 与跳板机的 ext4 上各执行一次 doctor --json（真实文件系统类型取法要真实执行，fstatfs 与 mountinfo 不能只靠 mock）。
- 备注：我的判断：显然可以沿用。现有各项都是「section.name」形态（steps.dir、config.file、backend.worker.grace），机读输出里 section 与 name 分开（__main__.py 第 817 行），report_dir.filesystem 即 section=report_dir、name=filesystem，与现有命名一致，组名与 --report-dir 旗标同词。

#### 问-16（mixed，S）

- 线索：下面「删除过程文档之前找到、ADR 里还没有的内容」一块里另有两个待定：提示里的 `gherkai status`
- 进度：第二个待定已了结：owner 2026-11-21 定不带与带 --wait 的 status 遇到运行态解析不了都以退出码 2 结束，0031 决定五与 0054 决策八已写，本机一侧已随 run 处置一批落地（explain 的那一半见下「删除过程文档之前找到、ADR 里还没有的内容」一节补-5）。
- 要做的（余下）：_status_cmd 是否带上显式给出的 --config；同一批里它还要按已定规则带上显式给出的 --ddb-table、--region。
- 文件：cli/gherkai_cli/__main__.py、docs/adr/0042-step-evidence-and-explain.md、cli/tests/test_main.py
- 先要有：无
- 必须同批：_status_cmd 的拼法改动（查看命令块）
- 单独先落地的后果：不定挡 _status_cmd 那条实装。
- 验证：单测：--config 的拼法断言命令串。
- 备注：我的判断：带上显式给出的 --config。规则本身说「来自配置文件的值不另带，因为同一目录照抄会取到同样的值」，这个前提只对当前目录的 gherkai.toml 或 GHERKAI_CONFIG 成立；显式 --config 指向别处时，不带它照抄会取到不同的值。交 owner。

## 删除过程文档之前找到、ADR 里还没有的内容

### 小结

这一块余下 8 条：补-1、补-2 已随生命期锁一批写进 ADR 0054（被拒方案「run 目录不过边界检查时只读地等」、Docker Desktop 的取证），补-11 由 owner 定为别的版本写出的 run 不处置、已随 run 处置一批落地，三条删去；补-4、补-5、补-6、补-7、补-10 已做的部分各条写明。code 量合计不大（多是 S），主要成本在 ADR 改动和 owner 的确认。按性质分三类。（一）纯 ADR、可以现在就写：补-4（0043 骨架第 8 条）、补-5 的 0037 半句、补-9 的 ADR 那一句、补-8 的「括注按 deadline_at 本身计」。（二）先写进 ADR，但要 owner 先确认理由或取舍：补-3（status 命令拼法；--config 带不带待定）。（三）只是实装细节：补-5 的 explain、补-6 与补-10 的云端一侧、补-7，补-8 的计时取法。

分批归属：补-3、补-5、补-8、补-9 归查看命令批；补-6、补-10 余下的云端一侧随云端处置（settle-runs 接云端与云端 status --wait）；补-7 余下的 cli_version 随 settle-runs 的 --json 改动。

可以先于大改单独落、不留窗口的：补-9 的云端读法（CLI 一侧，不用重新部署）、补-3 的 _status_cmd 拼法。读期限的端口形态（头部读取带 deadline_at）是补-8 与补-10 的共同前提。云端真实验证只有补-6 要（只读身份做结束写），它依赖新的 runs 表写法，要排在云端批重新部署之后。

最大的风险在云端处置的失败分类（解析失败、访问失败、写被挡下、写失败）要与本机说法一致：本机一侧已落地，现在云端的「云端不可达」兜底会把写权限不足误说成不可达。

### 线索没有覆盖的改动点

- 云端运行态解析失败没有出口：_status_cloud 和云端 explain 只接 botocore 异常；STATE 状态值本版本不认识（_run_state_from_item 里 Status(item["status"]) 抛 ValueError）或形态违约（KeyError）时，回溯直接打到终端。补-5 第三段只写了本机，而 0054 决策八「运行态本身读不出时只等待并说明原因」是两个后端通用的，0041 决策七的云端列举也已把这类行列为无法读取。位置：cli/gherkai_cli/__main__.py 的 _status_cloud 和云端 explain 分支（约第 2700 行）；core/gherkai_core/adapters/run_store/ddb.py 的 load_run_state。
- 本机存储访问失败在 explain 里没有出口：load_run_state、peek_definition_header 遇到 PermissionError 一类 OSError 时是未捕获的异常（不带 --wait 的 status 已随 run 处置一批按读取记录失败以 2 结束）。补-6 定的判据（访问失败按读不到这个后端，以退出码 2 结束，与 0041 决策七「读不到」一致），explain 也该按同一判据以 2 结束。位置：cli/gherkai_cli/__main__.py 的 _cmd_explain；依据：0041 决策七「退出码」条（本机报告落点不可读即 2）、补-6。
- 云端 status --wait 处置时，结束写因权限不足失败的说明：现在 _status_cloud 把所有 botocore 异常都报成「云端不可达（表/凭证/region）」，处置时条件写被 AccessDenied 拒绝，这句会误导。要另给一句点名缺 runs 表条件写权限、并指向权限说明的话。位置：cli/gherkai_cli/__main__.py 的 _status_cloud 兜底 except；依据：补-6、0054 决策八「云端用户一侧的处置方」条、0033 编排进程角色。
- 提示里的 status 命令在云端不带显式给出的 --report-dir（云端报告前缀）。status --wait 改为会处置之后，要按 --report-dir 读被点名的明细、写报告；照抄提示执行时，会把报告写到默认前缀。补-3 的规则只带 --ddb-table、--region。依据：0054 决策七（写成的一方生成报告）、决策八；0043 决策五骨架第 3 条（云端读判定明细用的 --report-dir 也要一致）；与「核对时补上的条目」里「云端处置方按 --report-dir 写报告、是否比对报告前缀」那一待定项相关。位置：cli/gherkai_cli/__main__.py 的 _status_cmd。
- journey 0013 第 66 行（skill 打磨批欠账）现在指向 0018「实装」一节里的这一块。这一块的内容吸收进 ADR 后会删掉，那里的指针要改成指 0043 决策五（补-4 落下之后），否则就悬空了。位置：docs/journey/0013-mobile-devices-implementation.md。

### 逐条

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
- 进度：0043 决策五任务域 A 的命令列表加上 settle-runs、agent 先带 --dry-run 看会把哪些 run 记为已结束再执行，已随 run 处置一批写进。
- 要做的（余下）：骨架第 8 条「退出码分流」接上 settle-runs 的退出码（0/2 的含义，看 --json 的 runs[].outcome/reason）。skill 正文怎么写留给 skill 打磨批，journey 0013 里登记的「settle-runs 放在哪里教」补一个指向 0043 决策五的指针。
- 文件：docs/adr/0043-agent-skill-for-driving-gherkai.md、docs/journey/0013-mobile-devices-implementation.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：无。
- 验证：ADR 过复核即可。skill 一侧到打磨批用评测验证（evals 补 settle-runs 场景），这一批不需要真实执行。
- 备注：骨架第 8 条现在只列 submit/plan/list-runs/explain/doctor 只表做成没做成，settle-runs 进来时要一起列。journey 0013 第 66 行现在指向 0018 的这一块，这一块吸收之后会删，那里的指针要改成指 0043 决策五，不然就悬空了。

#### 补-5（mixed，M）

- 线索：提交记录或运行态本身解析不了时的出口
- 进度：本机 status（含 --wait）已随 run 处置一批落地：提交记录头部解析不了按定义违约（`serialize.definition_from_json`）、运行态解析不了（`serialize.UNREADABLE_RECORD_ERRORS`）、读记录失败，都以一句说明与退出码 2 结束；owner 2026-11-21 定 --wait 也以退出码 2 结束、不等待，0031 决定五「status」条与 0054 决策八已写。
- 要做的（余下）：本机 explain 读运行态时接住解析失败与读取失败、以退出码 2 结束，ADR 0037 决策 7「CLI 读端」的半句，都已做完（连同 0042 的退出码一条、用户指南与 CHANGELOG）。只剩云端：`_status_cloud` 与云端 explain 只接 botocore 异常，STATE 的内容解析不了时（如状态值不认识）仍出回溯，随云端一批处置入口接上处置模块时一并做。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_main.py、docs/adr/0037-distribution-and-packaging.md
- 先要有：无
- 必须同批：无
- 单独先落地的后果：云端的一半随云端一批，不单独落。
- 验证：单测够：损坏的 run_state.json（非法 JSON、顶层是数组、状态值不认识）各一例，断言 explain 退出码 2、stderr 没有 Traceback。
- 备注：余下的属于云端一批。

#### 补-6（mixed，M）

- 线索：存储访问失败不算「运行态读不出」
- 进度：本机一侧已随 run 处置一批落地：处置判定只把解析不了记 unreadable，读运行态、打开 run 目录与结束写的 OSError 都按读写记录失败，status --wait 与 settle-runs 以 2 结束；ADR 0054 决策六末条、决策八与 0031 决定五已写。
- 要做的（余下）：云端一侧：status --wait 与 settle-runs 的云端处置把 botocore 的权限、凭证、region、网络错误（重试做完仍失败）往上抛、以 2 结束并说明原因，不进入等待；结束写失败（比如云端只有读权限）同样以 2 结束；条件写因为别处先写成而被挡下不算失败（settle-runs 记 already_finished，status --wait 照常渲染终态）。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_backend_cloud.py
- 先要有：云端处置（处置-2、处置-3 的云端一半）
- 必须同批：settle-runs 接云端与云端 status --wait 处置（同一批）
- 单独先落地的后果：不能单独落，云端处置还不存在。现在云端 _status_cloud 已经把 botocore 异常一律报「云端不可达」并以 2 结束，读这一半已经接近目标。
- 验证：云端的判据要在真实 DynamoDB 上核：给一个只有 runs 表读权限的身份执行 status --wait，在一个过期限加 300 秒的 run 上看是否以 2 结束、说明原因，而不是继续等；moto 不校验 IAM，单测不算证据。这项依赖新的 runs 表写法（写入序号），要排在云端批重新部署之后。
- 备注：_status_cloud 的兜底说明写死成「云端不可达（表/凭证/region）」，结束写因 AccessDenied 失败时这句会误导，要另给一句点名缺 runs 表条件写权限的说明（见 missing）。

#### 补-7（mixed，S）

- 线索：settle-runs --json 的 cli_version 与被使用方中断时的退出码
- 进度：被使用方中断时以 130（SIGTERM 为 143）结束、不出回溯、已写成的处置保留，已随 run 处置一批落地，0031 决定五 settle-runs 条已写。
- 要做的（余下）：settle-runs 的 --json 顶层与 list-runs 一样带 cli_version（恒有，取不到为 null），复用 render.run_list_to_dict 那种拼法和 _installed_version()；runs[] 各项不带写出版本。机读契约页写出这一点。现在的输出与 0054 决策八的「机读输出」都没有这个键。
- 文件：cli/gherkai_cli/__main__.py、cli/gherkai_cli/render.py、docs/internals/cli-json-contract.md、cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md、cli/tests/test_cli_json_contract.py
- 先要有：无
- 必须同批：settle-runs 的 --json 与它的契约页条目（同一提交）
- 单独先落地的后果：无。
- 验证：cli_version 的键形状用单测和契约护栏（test_cli_json_contract 的键集差集）验证。
- 备注：建议首选落在 journey 和实装批里，不进 ADR：它沿用 list-runs 的既有惯例，不是新决定。

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
- 进度：本机的等待循环已随 run 处置一批落地：每次轮询做一次处置，每次处置读一次提交记录（0054 决策八「处置的次序」），等待中的说明按结构化的原因各给一次（`_wait_notice_key`）。
- 要做的（余下）：云端的等待循环（_status_cloud）：读到合法的期限之后不再重读运行定义，没读到时下一轮重读；说明用「上一次打印的原因」去重，原因没变不重复打，云端未过期限加 300 秒时不打。
- 文件：cli/gherkai_cli/__main__.py、cli/tests/test_backend_cloud.py
- 先要有：云端 status --wait 的处置（处置-3）
- 必须同批：处置-3（取代 _STALL_KICK 的同一批）
- 单独先落地的后果：不能单独落，现在云端的 status --wait 不按期限做任何事。
- 验证：单测够：注入头部读取的返回序列（先失败、后成功、再变）和原因序列，断言读取次数与打印次数。墙钟比较用注入的时钟。
- 备注：是实装细节，不进 ADR。「期限不合法」的判定要走 core 那一处严格解析（run_deadline 里的 instant_from_iso），带时区才算合法。
