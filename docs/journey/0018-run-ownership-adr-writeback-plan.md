> 类型: 进度总纲

# 推进权与状态投影：ADR 写回的结果与实装线索

这次上游重新设计（推进权、生命期锁、run 处置、run 的状态由 job 的终态算出、云端后端只支持 `submit`、隧道建在宿主进程里）已经就地改写进各篇 ADR 与词表，另一家模型核过「落到位」。本文记四样：owner 定的写回口径；写回与复核的结果；留下的问题；之后实装的线索与还没有实装的部分。换会话或上下文压缩之后从本文恢复现场；线索逐条对到 code 的结果在 [0021](./0021-run-ownership-implementation-clue-map.md)。实装全部完成之后本文删除。

与 owner 逐条对齐的记录、合在一起的设计稿、写回之前的归位方案与逐篇改写计划，以及更早给 ADR 0054 实装第 4 步写的设计补充（复核没有闭合、交 owner 裁定的那一份待批报告）都已删除：内容在各篇 ADR 里，原文在版本历史里（`docs/journey/` 下以 0016、0017、0014 开头的三个文件，以及本文在删去计划各节之前的版本）。删除之前逐条核过其中的有效信息别处有没有，别处没有的并进了本文「实装」一节。

## owner 定的写回口径

- 这次重新设计是对之前设计的修正。不新增 ADR，不把内容堆进一篇：每一项决定写在「做这件事的人会去读的那一篇」里，别处放指针。
- 旧设计删掉、当作没有发生过；只把讨论中权衡过的做法留作被拒方案，理由写设计上的依据。ADR 里不提升级、迁移与版本共存。这一条只管未发行版本内部的改写；对使用方已部署后端的形态变更，长期规则仍是 ADR 0037 决策 7「后端形态变更的迁移口径」。CHANGELOG 未发行节直接写新行为，另提一句这一部分做了重构（owner 2026-11-18）。
- 读起来不能有打补丁的感觉：能原位改写既有小节的不新增小节；标题、背景、决策的开头句直接陈述现在的设计，不写「后来发现」「不再」「改为」。
- 文件名与改写后的内容对不上就改名，引用同步更新、保持有效。
- 用词：统一用词表的规范名「推进器」；run 级叫「run 处置」，job 级叫「job 到点停止」；「执行方式与执行后端有三种组合，云端后端只有后台」。
- 描述行为的文档（internals、用户指南、agent skill、机读契约页、CHANGELOG）随各实装批次在同一笔提交里改，这次只改 ADR 与词表。
- 进度记在本文。ADR 的 Status 头只留一句状态（这一篇描述的设计有一部分尚未实装），不列清单、不指向 journey；还没有实装的内容记在本文「实装」一节，不写进 ADR。

## 进度

| 批 | 内容 | 状态 |
|---|---|---|
| 设计 | 设计稿闭合（含后补的四块与隧道一块） | 已写回，设计稿已删除 |
| 第 1 批 | 0054 改名与全部引用 | 已提交 |
| 第 2 批 | CONTEXT.md 词表 | 已写回 |
| 第 3 批 | 承载新决定的各篇：0031、0030、0034、0054、0016、0027、0041、0053 | 已写回 |
| 第 4 批 | 只改受影响条文的各篇，以及纯改指向的 code 与测试注释 | 已写回 |
| 第 5 批 | 收口：Status 头、卫生测试、指针差集、另一家模型核落到位 | 另一家模型核了四轮，三份都已闭合（两份在第三轮熔断，owner 裁定之后第四轮闭合），见下「另一家模型核落到位」 |
| 隧道 | 隧道建在宿主进程里；本机 `submit` 由后台推进进程建 run，锁的交接取消 | 设计经另一家模型复核闭合，已写回 0035、0054、0034、0031、0037、0051、0011、0016、0053、0043 与词表；另一家模型分两份核落到位，都已闭合，见下「隧道」一节 |
| 过程文档审计 | 删除对齐记录、设计稿、第 4 步的待批报告与本文里已执行完的计划 | 已做；别处没有的有效信息并进了「实装」一节 |
| Status 头清理 | 全部 ADR 的 Status 头只留状态值与取代范围 | 已做，另一家模型分两份核落到位、都已闭合，见下「实装之前的一批：Status 头清理」 |
| 实装摸底 | 「实装」一节的线索逐条对到 code：改动量、先后依赖、单独落地的后果、验证方式，另补出线索没有覆盖的改动点 | 已做，见 [0021](./0021-run-ownership-implementation-clue-map.md) |
| ADR 补遗 | ADR 里还没有定的设计点随实装批次定：一批要用到的在这一批开工前落进 ADR，不整批定完再开工（owner 2026-11-19） | 按批取用：范围见「实装」一节末尾两块与 0021 各块的「线索没有覆盖的改动点」。把这些合并成一份清单的提取做到一半停下了，要用时重新做 |
| 实装第一批 | 删去前台云端执行（`run --backend cloud` 以退出码 2 结束并指向 `submit`，连同只为它设的参数、配置键、引擎的同步消费与 SSM 网络参数） | 已落地并闭合：全量测试通过，跳板机真实执行已核，另一家模型核落到位四轮（1、1、1、0）；欠下的云端真实执行见「实装」一节开头 |
| 实装第二批 | 状态取法与结束写，分三笔：纯加法；前台改用新入口；后台改用新入口（连同判定明细点名） | 第一笔已落地，见「实装」一节开头 |
| 实装其余各批 | 报告；本机的边界检查、生命期锁、`submit` 新流程，run 处置与删去接力同批；隧道改用 SDK；云端后端集中一批并重新部署一次；收尾 | 未开始，各批开工前定它要用的设计点 |

## 另一家模型核落到位

写回的提交分四份送另一家模型核（按篇分组；基准是复核闭合的那一版设计稿加 owner 的写回口径）。第一轮四份都是「继续修正」，基准之内的意见共 27 条（6、4、7、10），逐条到仓库核过都属实，归成五类处置：

- **没有改到的旧说法**：写回时只改了点名的小节，同一篇里别的段落还留着旧设计（例：0016 把 `fargate_engine.py` 称作执行引擎端口的云端实装，0041 说 job 没通过的原因都在判定明细里，0026 说报告从内存结果生成，0024 说使用方中断时停止原因一律记 `abort`）。逐处改到与现在的设计一致。
- **把做法写成了保证**：越过设计里写明的前提的句子（「没有人查看的后台 run 也不会无限期挂着」「run 被结束之后不再有新的执行」「最晚由后端在期限加 300 秒结束」「链上任一缺则 run 永不推进」）。收窄或改成指向写全前提的那一条。0054 的标题与决策五的标题随之改为「不再接受新的认领」。
- **云端投影的写法**（0034 机制三）：旧文里投影分两步写，写入序号只在标量那一步加一，run 状态也在那一步先写，并把「run 级 `running` 而 job 全为 `pending`」当作接受的窗口。这与 0031 决定三「每次改变 job 状态的写在同一次写里按取法写 run 状态」、机制三②「每次写加一」不符，后果是另一个调用凭旧序号整体替换 `jobs` 时会盖掉刚写的字段。主会话定的写法：两步的次序不变，标量那一步只推进 HWM；把 job 记为 `running` 的那次逐 job 写同时写 run 状态（与认领同一种形态，条件带 run 未结束）；两步里的每一次写都把写入序号加一。「接受的窗口」一条与成本条里的两种例外随之删去。
- **Status 头**：另一家模型按「头里只留一句」读。主会话的处置：删去头里叙述这次重新设计改了什么的句子；这一篇的条文现在与 0054 一致、没有哪一条被它取代的，把 0054 从取代清单里去掉；删去与「部分尚未实装」相抵的全称实装声称；0054 自己的头只留 Status 值与一句状态。各篇头里原有的、说明与别的 ADR 取代关系范围的文字保留。这个范围已请 owner 确认，答复之前按此处置。
- **升级、迁移与版本共存**：0054 里随运行期限写下的结构版本由 1 升到 2、版本 1 的记录怎样处理的几句已改为直接陈述（期限是运行定义键集的一项，键集由结构版本固定）。与这次重新设计无关的既有历史叙述（0030 里状态分组索引的在线迁移口径与步骤、0030 与 0034 背景里的沿革、0034「退出码缺失」条里的修正经过）没有动，对相应意见判了维持；要不要一并清理已请 owner 确认。

处置由五组修正者各改各的文件，每组之后有独立复核与第二次修正；跨文件的跟进由主会话落（注释里所指小节已改写的指针、三处把「永不推进」写成结论的注释、0037 里的版本叙述）。带条名的指针另做了机械差集，目标条名在改写之前有、现在没有的为 0。

### 闭合轮与两处熔断

四份闭合轮确认第一轮的 27 条都已处置到位，上面 Status 头与历史叙述两处范围的澄清四份都判成立。新指出的：

| 份 | 第一轮到闭合轮 | 流程处置 | 指出的 |
|---|---|---|---|
| 0054、0034 | 6 到 1 | 熔断 | 0054「边界与已知局限」表里又一句把计划的触发时刻写成了完成的先后 |
| 0031、0030、0027 | 4 到 1 | 继续修正 | 云端投影逐 job 的写没有带 HWM 的条件，较小 HWM 的投影能把旧的会话字段写回 |
| 0016、0033、0041、0053、词表 | 7 到 1 | 继续修正 | 0016「版本切分」1.2 一行还把 `status --wait` 接力列为已有的能力 |
| 其余各篇与注释 | 10 到 2 类 3 处 | 熔断 | 注释说明的是现在 code 的行为，旁边的指针所指的 ADR 小节现在写的是另一种设计 |

两处熔断都按「不需要 owner 的结构处置」处理，并已通知 owner 一次。

**时间保证的转述**（依据是 `docs/ai-eng/peer-review.md` 第四节「依据只在一处写全」）。反复失守的性质：不把计划的触发时刻转述成完成时刻或完成先后的保证。规则：关于「run 到什么时候会被结束、某个时刻之前已经发生了什么」的陈述只在下面几处写全，别处只放指针、不转述结果与先后。

- 云端后端到期结束 run、两次 run 级定时触发各做什么、前提与前提不成立时怎样：0054 决策九第 1 条。
- 可以处置的条件、期限加 300 秒按墙钟判断：0054 决策六。
- 谁能处置、本机没有常驻的处置方：0054 决策八。
- 执行方到期时自己怎样停：0054 决策二。
- job 的截止时刻与 job 到点停止：0054 决策二第 2 条、0034「job timeout」节。

按这条规则对写回涉及的各篇与词表做了全量枚举（按词检索、逐句判断是写全处、指针、转述还是验收内容）：0034 核 39 句、改 8 句，0054 核 62 句、改 17 句，其余各篇核 42 句、改 11 句；独立复核再做一遍枚举之后又核 16 句、改 12 句。决策九第 1 条补全了两次触发各自的前提，并写明两次调用彼此独立、完成的先后没有保证。

**注释里的指针**（依据是 CLAUDE.md「悬空指针红线」与 owner 定的「code 只改注释里的指针」）。反复失守的性质：注释里的 ADR 指针所括的说法与所指小节的现文一致。规则：注释、文档串与各包技术文档里的 ADR 指针，声明的是「这里说的事，那一节现在就是这样写的」；code 还没有跟上目标设计的地方，对现在行为的说明保留，指向目标设计那一节的指针去掉，等实装把 code 改成目标设计时加回来；判断单位是整个注释块。按这条规则对 code、测试与各包技术文档里指向这次改过的 22 篇 ADR 的指针做了全量核对（151 个文件、约 3000 处，分 14 批，每批核对、独立复核、第二次处理）：去掉 342 处，分布在 61 个文件；所有改过的 `.py` 文件去掉文档串之后的语法树与提交里的相同。去掉的指针与各自跟上之后对应的小节列在 [0019](./0019-comment-pointers-removed-pending-implementation.md)，实装时照它加回。

另外三处：

- 云端投影逐 job 的写加上「库中 HWM 不大于这次投影的 HWM」的条件（0034 机制三）。它挡不住 HWM 相同而读到的事件不同的两次投影（HWM 是整个 run 一个数，取各 scope 的最大序号）：先读的那一次仍可能把同等级的旧字段写回，下一轮重放后恢复。0034 照实写明这道条件只分得出 HWM 不同的投影，没有改成按 job 各记一个进度的条件；这一取舍已告知 owner。
- 0016「版本切分」那一行删去接力职责的概括，命令各自做什么指向 0034「命令形态」。
- 核对注释时顺带发现的几处 ADR 残留一并改了：0030 决定六「读用 `ConsistentRead`」一条里的「终读 drain」；0024「远程传输演进」节开头的「三方案被拒护栏」；0053 决策 3 里指向 0024 已删内容的半句；0034 机制三 K1 到 K3 的「证据」改称现有用例，并注明它们断言的是现在 code 的写法。

核对者另记下一批与这次重新设计无关的既有问题，留给文档健康复盘：条名在所指 ADR 里从来没有出现过的指针（如 0026「接口是测试面」、0034 的「P4b」、0037 决策 3 的两个引号条名、0024 的「A3」与「退出码约定」），以及 0038 里引用 0034 的一句引号原文。

### 第三轮：一份闭合，两份再次熔断

| 份 | 三轮趋势 | 流程处置 | 这一轮指出的 |
|---|---|---|---|
| 0016、0033、0041、0053、词表 | 7、1、0 | 已闭合 | 无 |
| 0054、0034、0031、0030、0027（原第 1、2 份合并送） | 6 与 4、各 1、1 | 熔断 | 0054 实测项 8 从「期限那一次先到达」推出「由它停掉 task」 |
| 其余十二篇与注释里的指针 | 10、3 处、4 处 | 熔断 | 又 4 处注释把现在 code 的旧行为归给 ADR 现文，其中 1 处与前两轮是同一种绑定 |

另一家模型在这一轮确认的：云端投影逐 job 的写带 HWM 条件的处置成立；「HWM 相同的投影分不出」是基准之外的边界、同意维持；正文里关于 run 何时结束的转述按词表枚举 137 个命中行，在基准之内只剩实测项里的一处；注释指针的三种判法（挪到一致的句子旁、补全相对指代、收窄混合指针）成立，节头的判法边界不清。

两份都是做过一次结构处置之后同一原因再次触发，按 `docs/ai-eng/peer-review.md` 第四节要等 owner，已停下不再改、不再送。要 owner 定的问题、各选项的后果与作者的倾向写成一份待批报告交了 owner（先过了另一家模型四轮复核；隧道记录定位那一项的方案比较没有通过，只交了事实与选项）。owner 的裁定与落实见下「owner 的裁定与落实」，报告已删。

留给实装批的（并入「实装」一节的线索）：

- core 里描述投影两步写法的注释与文档串（`run_store/ddb.py` 与 `run_store/local.py` 的 `project_state`、`project.projected_run_status`、`ports.py` 的 `project_state`）讲的是现在的 code，随 code 改成新写法时一起改。
- `ports.py` 的 `Engine` 文档串、`errors.py` 两个异常的文档串把 `FargateEngine` 称作执行引擎端口的实现，随删去同步云端路径一起改。
- `docs/internals/verdict-model.md` 里「run 级 `running` 不保证已有 job 离开 `pending`」一句随那一篇改写时删去。
- `skills/gherkai-evals/evals.json` 里 `expose-local-app` 一条的评测要求随隧道的行为文档一起改，改法见「实装」一节「行为文档」块里评测资产一条。

### owner 的裁定与落实

**实测项的断言**（0054、0034、0031、0030、0027 那一份）。交 owner 的选项：给实测项的断言定依据；这类验收不放在 ADR 里；实测项一律不写哪一次调用做了哪件事。owner 选第一种并加了篇幅的约束，原话：「甲我也倾向于一，但我觉得也要注意"篇幅"问题，不要过度铺垫，否则会本末倒置，标准就是能让实测项服务好ADR本身就够了，而非让实测项自己的篇幅完备无缺。」

规则：实测项里的每一条断言要有依据，二者之一：ADR 里规定这件事的那一条连同它的前提；这条实测项自己的布置把交错固定住了。两种都没有的不写成断言，改成要记下的事实。

落实：

- 0054「实测项」一节开头加了一句读法：各条写的是布置之下、所引条文的前提成立时应当看到的结果，例外按决策与「边界与已知局限」判，布置没有固定的先后只记下。前提由这一句用指针带上，各条不逐条重述。
- 0054 的 23 条与 0034 的 7 条逐条过了一遍：每组两位互不知情的代理，一位列断言与依据，一位找 ADR 原文允许的反例，之后裁决、独立复核。裁决建议改 22 条，多数是给断言补前提的括注。按篇幅的约束只收两类：读法那一句管不到的（把完成归给某一次调用，或所引条文的前提都成立时仍然不对），与不加长的准确性修正。改了 0054 的第 1、2、3、5、7、8、9、11、14、16、17、20、21 条与 0034 已核记录里的两处，其余不动。
- 第 8 条：布置加上「只有一个 job 的 run」（排除别的 job 的事件带起的防御性超时扫描），删去「期限那一次到达时 run 仍未结束的，由它的 job 到点停止停掉 task」，停掉 task 的是哪一方只记下。第 7 条末句、第 21 条里「过了期限加 300 秒之后 run 由后端结束」同样改为记下。

**注释里的 ADR 指针**（其余十二篇与注释那一份）。owner 选的是明示接受过渡期的风险、语义一致留到实装，原话：「乙我倾向三，因为现在就是在改的过程中，现在落设计，完了开始改code时就把这个改为一致的。」

落实：第三轮点名的 4 处已改。写回这一步只保证机械可核的一项：指针里的条名，写回之前的 ADR 里有、现在没有的为 0（重做的结果：code、测试与各包技术文档里 0 处；全仓另有 3 处在 `docs/internals/`，见「实装」一节）。随实装核对的责任范围记在 [0019](./0019-comment-pointers-removed-pending-implementation.md) 末节：带这类指针的文件共 277 个，其中 151 个在第三轮做过全量核对，其余 126 个（主要在 `engines/` 下）没有核过。交 owner 的选项里写的「151 个文件」只是前一组，另一家模型在确认轮指出清单不全之后补齐。

第四轮（换新的上下文、带上未闭合项，解除依据是 owner 的裁定）：

- 实测项那一份：另一家模型逐条核了 30 条实测项，基准之内 0 条，流程处置是已闭合。节首那一句读法、没有收的候选，都判成立。
- 注释指针那一份：4 处修正到位，条名的机械差集它独立重做也是 0；指出随实装核对的清单不全（见上）。补全之后续接同一会话确认，流程处置是已闭合。

至此写回的三份都已闭合。隧道一块的条文（0035 决策 3 等）不在这三份里，见下「隧道」一节。

方法上的一条观察，待与 owner 提：本家的执笔、通读、修正与差集按「改动处」核，没有照出同篇未改段落里的旧说法、成类的口径问题与把做法写成保证的句子；另一家模型以设计稿为清单逐项对到 ADR、整篇读，核出了这 27 条。

方法层的三条提议 owner 2026-11-19 同意，已写进 `docs/ai-eng/peer-review.md` 第四节（几处修正都在加机制时找它们共同的上游设计决定，附这次重新设计作样本）、CLAUDE.md「文档纪律」（未发行版本内部的重新设计写回 ADR 时当作修正）与 `docs/ai-eng/doc-health-review.md`「Status 头」一节（注解的范围与取代关系的判据）。同日 owner 另定子代理与 Workflow 代理的推理强度继承会话级别、不显式调低，写在 CLAUDE.md「工作方式」。

## 隧道

写回时暴露的一块：本机 run 的宿主（前台的 CLI 进程、本机 `submit` 的后台推进进程）被强杀之后，隧道代理与公网地址没有人拆。旧设计里本机 `submit` 靠 `status --wait` 接力兜底，接力已经去掉。

经过（细节在版本历史里）：

- 起初的方向是保留独立的 ngrok 代理进程：不为拆隧道再起一个守护进程（它同样会被强杀），留下的代理由 `status --wait` 与 `settle-runs` 拆，拆之前用 ngrok 代理自带的本机接口按端点名核对，免得按记录的进程号误杀别的进程。
- 这条路在另一家模型那里核了两轮，第二轮熔断：云端 run 的本机隧道记录先放系统临时目录、后放使用者主目录，两次都由写入方与查找方各按当次的环境变量定位，同一台机器、同一个使用者换了环境变量就找不到。
- 熔断之后先按 owner 的各项裁定把这条路写到了完整（隧道记录单独成一项并带「已拆」标记，处置命令在回环地址上按端点名问接口后补拆，云端借用状态分组索引列举，边缘到点拒绝的规则），那一版留在版本历史里（提交说明以「journey 0017：决策十二按「独立的 ngrok 代理进程加隧道记录」的做法写到完整」开头）。
- 随后做法换了。owner 指出根子：记录与进程是分开的两样东西，进程一侧又没有机制能配合给出单一的事实（代理自己没了而没有哪一方确知的记录会一直留着；公网一侧只看得出「此刻不在线」，被暂停的代理与已退出的代理回答相同）。owner 定的做法是把隧道建在宿主进程里，并在「`submit` 仍建 run、把锁经套接字传给先启动的后台推进进程」与「本机 `submit` 由后台推进进程自己建 run」之间选了后一种。

现在的设计写全在各篇 ADR 里，这里不复述，只列各项写全在哪里：

- 隧道的全部内容（三种宿主、寿命、边缘到点拒绝、前置条件、启动失败的说法、边界、被拒方案、实测项）：0035。
- 实测数字（官方 Python SDK 在两种账号、两个平台上的结果）：0035 决策 1「实测依据」。
- 本机 `submit` 各步的次序、回报、输出与退出码：0035 决策 3「本机 `submit`」一条；0034「命令形态」只留骨架。
- 生命期锁与本机 `submit` 由谁建 run：0054 决策三、四；「各命令写什么」的表：0034「命令形态」。
- 边缘策略的规则：0051 决策 13「边缘策略」；可选依赖：0037 决策 2c。

另一家模型的复核：

| 对象 | 各轮基准之内的意见 | 结果 | 指出的 |
|---|---|---|---|
| 设计文字 | 4、1、1、0 | 已闭合 | 宿主内持有隧道与取消交接的结构没有反例。第二轮熔断：正文与影响清单各自概括同一条等待建议。结构处置（不需要 owner，依据是 `docs/ai-eng/peer-review.md` 第四节「依据只在一处写全」）：提到这条规则的句子全量枚举 90 句，带条件、适用范围或处理办法的转述一律改成指针或逐字引用 |
| 写回：0035 等隧道各篇 | 3 类、0 | 已闭合 | 0035 里还留着「四条规则」的旧说法与几句手写概括；一句「凭据在整个隧道存活期间有效」的旧断言；0035、0037 的 Status 头里还有分项的实装状态 |
| 写回：0054、0034、0031 | 1、1、0 | 已闭合 | 0054 余量算例推不出「靠后的 job 被期限截断」；清理时把 0031 一句事故记录改成了指向现行存活上限的指针，已恢复原句 |

写回首轮之后另做了一遍全量清理：别篇提到写全处内容的句子逐句列出（138 句），改成指针或逐字引用。两处 code 注释里悬空的指针去掉了，记在 [0019](./0019-comment-pointers-removed-pending-implementation.md)。

留给 owner 的一处（不挡实装分批）：建 run 的过程中进程被强杀（已建出目录、还没有写下运行态），会留下一个没有运行态的目录。它不算 run：`list-runs` 跳过它（0041 决策七「本机实现」里「没有该文件的目录跳过」一句），它没有运行态，处置命令无从做结束写（0054 决策六最后一条），目录一直留着。前台 `run` 本来就有这个间隔，本机后台的这个间隔现在在后台推进进程里。这一条先前记作「之后一直列为读不出」，与 0041 的条文不符，已更正。owner 2026-11-19 定：要清。做法与要 owner 定的几点见「实装」一节「建 run 中途被强杀留下的残留」一块，写进 ADR 补遗那一批。

清理时看到、没有动的既有问题（留给文档健康复盘）：definition 完整性不变量在 0035 与 0051 各写全一次；0035 决策 4 末尾复述 0051 的一句；0043「验证」一节里有一处把 skill 参考页的地址匹配写成「逐字一致的前缀匹配」，0035 决策 2 写的是带边界的识别。

行为文档、agent skill、评测资产、用户可见文字与 code 的改动，见「实装」一节「隧道（0035）与两种 `submit` 的新流程」一块和「行为文档」块里讲隧道的各条。

## 留下的问题与缺省

下面四项不阻塞开工，按缺省写；owner 有不同意见时再改。

- ScheduleOpts.stop_bound_s 与 FargateEngine.run_scope 只服务于 run --backend cloud。0034 机制二与 Engine port 一节、0026 的 ScheduleOpts 说明，是写「等待预算就是 grace，FargateEngine 只有 start_scope」（意味着实装时删掉这两样），还是保留参数、只不写来源？缺省按前者写：ADR 不为不存在的组合留参数。
  - 缺省：ADR 不为不存在的组合留参数，写「等待预算就是 grace，FargateEngine 只有 start_scope」。
- 0054 被拒方案「让使用者强制把某个 run 记为已结束」，与「以后的取消命令是处置方之一」相抵触。是改写为只拒「替 run 下某个判定（如记成 passed）」，并注明取消命令走结束写；还是现在删去，等取消的设计再定？缺省按改写处理。
  - 缺省：改写为只拒「替 run 下一个判定」，并注明以后的取消命令走结束写。
- list-runs --status 现在接受 skipped（0041 决策七）。run 级不再出现 skipped 之后，是继续接受（只会得到空清单），还是把它从取值集里去掉、以退出码 2 拒绝？
  - 缺省：run 级不再有 `skipped`，从 `--status` 可接受的取值里去掉。
- 本机 status（不带 --wait）在 run 全部为 pending 时提示「推进可能未启动，可 status --wait 接力」。去掉接力之后，这句是删掉，还是改成「可用 status --wait 等待；管它的进程已不在时会被记为已结束」？要不要并进后补一节「list-runs 的提示」一起定？影响 0034 命令形态。
  - 已定（0041 决策七「人读形态」；0034「命令形态」里「不带 --wait 的 status」一条）：未结束而已过期限加 300 秒的 run 才给期限提示，接力的提示去掉。

## 实装之前的一批：Status 头清理

已做（owner 定：三份复核闭合之后、实装开始之前单独做）。

- 规则：头里只留状态值（连同验收日期）、取代关系及其范围（两个方向，含「其余不变」、改写处正文是否已是现行说法、正文哪些段落是旧形态或历史叙述）与过渡句。实装进度与施工记录直接删；还没有做完的验收、实测结论与证据、修订沿革里的理由、导读与定位、维护提示先到正文找，正文已有的删、没有的挪进正文相应小节。头里保留的文字逐字不改，只做删除。
- 结果：54 篇里 40 篇的头里有状态值、日期与过渡句之外的内容，其中 30 篇改了，10 篇的头里本来就只有取代范围。头部超过 400 字的由 25 篇降到 17 篇，超过 800 字的由 9 篇降到 4 篇（0019、0024、0033、0051；剩下的都是取代范围本身，要再短得改写，不在这一批里）。挪进正文 14 处（0001、0002、0003、0017、0032、0033、0040、0048）。0017 正文里两处「见 Status 头」随之改掉。
- CLAUDE.md「ADR Status 头」一条加了一句：头里只写状态值与取代范围，不写实装进度与实测结论。
- 取代关系的判据（复核里补明的）：分句点名另一篇 ADR，并说那一篇改动、撤除或扩展了本篇的条文，或本篇改动、落地或扩展了那一篇的条文，就属于取代关系，连同它后面说明改了什么的分句一起留在头里。本篇自己的修订、指向别篇的导读指针、实装与实测的进度不算。
- 复核：每篇一位执笔者、一位独立复核员；机械核对两项（改后的头相对原头只有删除与标点改动；状态值、取代方编号与过渡句的有无没有变）。另一家模型分两份核落到位：

  | 份 | 各轮基准之内的意见 | 结果 | 指出的 |
  |---|---|---|---|
  | 0016 等 15 篇 | 2、0 | 已闭合 | 0038 的头整段删掉了一句 0037 对本篇的改写关系（其中只有「真账户验过后」是进度）；0043 正文里一处定位所指的句子已从 0041 的头里移出 |
  | 0001 等 17 篇与 CLAUDE.md 的一句 | 0、1、0 | 已闭合 | 首轮没有意见；作者按上面的判据把同类分句补回之后，补回 0050 时只留了决策编号、删了各自改了什么，被指出，已恢复 |

  第一份的意见说明规则里「被别篇改写」与「随某修订改写」的界线没有划一，于是把判据写明、对删掉的全部分句重新过了一遍，补回 0038、0041、0049、0034、0050 的几处（0034 与 0050 的头恢复为清理之前的原文）。
- 仍超过 800 字的四篇（0019、0024、0033、0051）不改写。owner 2026-11-19 让作者判断；每篇一位分析员核了「留下的取代范围，正文里有没有同样的归属标注」，结论是头是这层对应关系唯一写全的地方，能安全缩短的只有约 5% 到 19%，改写出来的句子又都要重新核对。分析时看到的头与正文、头与反向链的出入在清理之前就有，留给文档健康复盘：
  - 0033：头在 0038 名下写「preflight 加版本 skew 与 variant 解析两项」，skew 一项属于 0037 决策 7；「三处默认建新」正文有四处；讲 0051 的一句把应用前缀各行都归到决策 10，正文有两处写的是 0051 决策 9。
  - 0024：头把 Job 输入三键归给 0051，正文写的出处是 0054 决策十、0048 与 0049 决策 7；本篇落地了 0016 推迟的字段级 schema，头里没有写，0016 的头也没有列 0024。
  - 0051：0019、0033、0042 三篇的头都写着被 0051 扩展，0051 的头里没有这三篇；它对 0049、0037、0028、0031、0024 列出的改动项与那几篇头里列的对不齐。
  - 0019：头点名 0034 与 0051 改动了本篇，两篇不在状态值的取代方列表里，它们的头也没有回指；正文仍有三处写「三个」tag，0048 加入两个 tag 的事只在头里。
- 不在这一批里的：正文里与这次重新设计无关的历史叙述（0030 背景的版本沿革与索引迁移口径、0034 的沿革与「退出码缺失」的修正经过），留给文档健康复盘：其中带着「为什么不这样做」的要改写成被拒方案，不能直接删。
- 这次写回留在各篇头里的那一句「有一部分尚未实装」，owner 同意维持到实装完成（见「实装」一节「收尾」）。

## 实装

ADR 已经由另一家模型核过。owner 2026-11-19 定的做法：不再往实装前面加批次；设计点随实装批次定；写 code 时的测试与真实执行也是对设计的核查，发现空缺补进 ADR 再继续；另一家模型的复核只用在设计层面与成批 code 落地之后。每个实装批的提交带上它所改行为的文档；做完一批，在这里与 [0021](./0021-run-ownership-implementation-clue-map.md) 里去掉对应的条目。

第一批（删去前台云端执行）的做法：范围是下面「云端只支持 submit」一块与 0021 同名小块（含它补出的改动点），连同「测试」「随实装改写的 code 注释」「行为文档」三块里跟着这一块走的条目。它不依赖别的块，不需要重新部署。两处原先标着待定的小取舍按「不为不存在的组合留参数」办，已告知 owner：`run` 解析器上其余几个只用于云端的参数（`--prefix`、`--ddb-table`、`--s3-bucket`、`--worker-variant`）逐个核对在本机 `run` 的路径上没有消费方之后一起删；`build_cloud_stores` 的第四返回值删去。分工按文件归属分四路同时改（cli、core、runtime 与 deploy_aws、文档与 skill），随后一位做跨包的集成与全量测试，再由独立的两位核落到位与测试覆盖有没有变少；之后在跳板机做真实执行（本机 `run`；云端 `submit` 加 `status --wait`；`run --backend cloud` 的出口），最后送另一家模型核落到位。

第一批已落地。下面「云端只支持 submit」一块，以及「测试」「随实装改写的 code 注释」「行为文档」「核对时补上的条目」里归这一批的条目与半边已删去，原文在提交 c56c8925 的本文与 0021 里。

- 核对：全量测试 4679 个通过；两位独立复核（是否照 ADR 做到位与残留；测试覆盖有没有变少）提了 19 条，其中须处置的 10 条都已改，包括补上两处缺的测试（推进器把 Fargate 配置交给起 task 的装配、`FargateEngine` 只有 `start_scope`）。
- 复核里定下的一处行为：`run --backend cloud` 同时带着 `run` 已不收的云端参数（如 `--prefix`）时，仍给出指向 `submit` 的那一句、以退出码 2 结束；没有给云端后端而带这些参数时，由参数解析照常报不认识的参数。
- 跳板机真实执行（Linux，nova 引擎，确定性 step 的 feature）：`run --backend cloud`、带云端参数的 `run --backend cloud`、配置文件把后端设为云端这三条路径都以退出码 2 结束并指向 `submit`；本机 `run` 通过；本机 `submit` 加 `status --wait` 通过；本机 `list-runs` 正常；对已部署后端的 `doctor --backend cloud` 与 `list-runs --backend cloud` 正常。
- 欠下的真实执行，留到云端那一批重新部署之后：云端 `submit` 加 `status --wait`，以及云端 `status`、`explain` 读到记录之后的路径（已部署的后端里只有结构版本 1 的记录，现在的命令行在读头部时就以退出码 2 结束，后面的路径只有单测覆盖）。`stack.py` 删去两个 SSM 参数与 Lambda 里收窄的装配签名同样要到重新部署才生效。
- 这一批没有动、仍把前台云端 run 当作存在的地方（按后台执行标记分流、kicker 的流过滤、`status --wait` 的 kickoff，含两句 Lambda 日志原文）留给各自的批次，0021 相应小块里已点名。
- 另一家模型核落到位：四轮，基准之内的意见 1、1、1、0，已闭合。其余五条性质（没有越界、仍然存在的路径没有被破坏、测试覆盖没有变少、ADR 的事实同步、用户可见文字）第一轮起就没有意见，四轮都在「`run` 怎样得知给出的是云端后端」这一处：先是不带 feature 时由参数解析先报缺少 features；作者在完整解析之前另加的一段扫描与参数解析对缩写、先后覆盖的解释不一致，误拒了一种本机写法，触发熔断；结构处置是后端只由参数解析一处解释（`run` 的 features 在解析这一步不设必填，缺少时在看过后端之后报出）；最后一轮改掉随之暴露的一处既有缺陷（配置文件里解析不了的路径没有按配置错误报出）。

第二批（状态取法与结束写）分三笔，每一笔之后测试全绿、产品可用。

第一笔（纯加法）已落地，现有调用方的行为不变：

- 新模块 core/gherkai_core/run_status.py：run 状态的取法 `run_status_of`；结束写的说明表 `RUN_ENDINGS` 与 `RunEnding`；两种写对运行态的作用 `ending_applied`、`commit_applied`（两个 adapter 都调它们，adapter 只管条件与落盘）；终态写的返回值 `CommitOutcome`（写成而 run 未结束、写成且这次写使 run 成为终态、run 已被别处结束）。
- 端口新入口 `RunStore.commit_job_states`（一次记一个或多个 job 的终态）与 `RunStore.end_run`（结束写），本机与 DynamoDB 两个 adapter 都实现；`JobState` 加 job 级说明，只由结束写写下。
- DynamoDB 的 STATE 条目带写入序号 `write_seq`，每个写 STATE 的入口都把它加一；两个新入口先强一致读、以序号等于读到的值且 run 未结束为条件整体替换 jobs，写不成重读再算。
- 随 code 写进 ADR 的设计点（0030 决定四、五、六；0031 决定三「结束写」小节；0034 机制三；0054 决策二、五）：`update_job_state` 只写执行中的 job，终态都经 `commit_job_states`；不结束执行中 job 的三条来路（执行方到期、fail-fast、使用方中断）的结束写，以写下时没有执行中的 job 为条件，条件随这次写一起判断，调用方不经手写入序号；多条来路先后成立时结束写取最先成立的那一条的说明；结束时刻由调用方给。
- 核对：全量测试通过；两位独立复核（设计与并发的反例；是否纯加法与测试）提了 21 条，须处置的 9 条里改了 8 条，另一条是下面的待定项。另一家模型对端口设计的复核结果记在这里。

后两笔动手之前要守的先后（复核时用探针在两个 adapter 上复现过反例，详见 0021「状态取法与结束写」小结）：`update_job_state` 以库中 job 未结束为条件、终态写与库中条目按字段合并，已随第一笔的复核修正落下（0030 决定四）。仍要做的：任何调用方开始用 `end_run` 或 `commit_job_states` 之前或同一笔里，`update_job_state` 去掉 run 已结束时仍写 job 的那次写（加了上述条件之后它只在经 try_finalize 结束、留有未结束 job 的 run 上写成；cli/tests/test_main.py 里别处以 try_finalize 结束 run 之后前台判定仍记进运行态的几条用例依赖它，所以随 try_finalize 删去同一笔）；`project_state` 的逐 job 写以库中 job 是 pending 或 running 为条件；前台迁到新入口与这两处改动同一笔；run 处置排在这些之后。

云端那一批之前要定的（记在 0021）：结束写给每个未结束的 job 各写一句说明，job 很多时这一次写可能超过单条记录的大小上限，超出时怎样处理（按 job 数设上限并在计划阶段提示，或缩短每个 job 存下的内容）；DynamoDB 上写不成重读的次数上限与持续投影的关系；运行定义不可用的几句说明现在在 Lambda 里，要挪进 core 的说明表。

下面是写回各批与删除过程文档之前的审计里记下的线索，不是完整清单；完整的实装分批对照 code 做。

分批的次序约束：

- 云端（owner 对齐时定）：删去 `_status_cloud` 的卡住检测与 kickoff（`_STALL_KICK`）以及 `compose._make_lambda_client`，这一步要与后端到期结束 run 的出口同批落地，或排在它之后。后端到期结束 run 的出口是指：kicker 收到 STATE 新建时建两次一次性定时触发，其中期限加 300 秒那一次在 run 仍未结束时按处置做结束写，见 0054 决策九第 1 条。理由：在后端到期结束上线之前，kickoff 是推进链断开的云端 run 唯一的唤醒手段，先删掉它，这类 run 在中间这段时间就没有出口。
- 本机（按同一理由推出，未经 owner 确认）：删去本机接力，即 `status --wait` 不再进入推进循环，这一步要与生命期锁、run 处置（settle-runs 与等待中的 `status --wait`）同批落地，或排在它们之后。理由：现在的接力能把推进进程已经不在、又过了期限的本机 run 推进到结束，先删接力，这类 run 在处置上线之前没有出口。

#### 词表与退役词

- 把 owner 定的「接力推进」「超时处置」「到点处置」加进退役词表，并在同一提交清掉全仓命中（code 与测试注释、技术文档与 internals、用户文档、图源 `docs/diagrams/execution-timeout-chain.json`、CHANGELOG 未发行节）；先加表测试即失败。「推进方」按 owner 只进 _Avoid_、不进表。其余新 _Avoid_ 词进不进表见下「写回时留下、实装之前要定的问题」；`test_each_write_entry_keeps_top_level_extras` 的文档串用「发起进程标识形态的对象」举例，那个词进表时一并改（位置：cli/tests/_doc_rules.py `RETIRED_TERMS_WORDS`；core/tests/test_conditional_writes.py `test_each_write_entry_keeps_top_level_extras`；依据：ADR 0045 决策八；CONTEXT「推进器」「job 到点停止」词条的 _Avoid_；下面「写回时留下、实装之前要定的问题」里「退役词表加哪些」一条）

#### 状态取法与结束写（core 与两个 RunStore adapter）

- 删去 run 级的过滤名单与空判定集规则：`_aggregate` 只在终结函数内容完整那一行把 scenario 判定归约成 job 判定（位置：core/gherkai_core/model.py `_NON_VERDICT`；core/gherkai_core/project.py `_aggregate`；core/tests/test_lifecycle_states.py 里引用 `_NON_VERDICT` 的用例；依据：0031 决定三「scenario 判定到 job 判定的归约是另一条路径」条与 touch points）
- 删去 `run_verdict` 与 `RunVerdict`（聚合之外的例外、到期优先于中断这类按原因区分的优先序），新增一处 run 状态的取法：有 job 未结束时全部 pending 为 pending、否则 running；全部结束时有 error 即 error，否则有 failed 即 failed，否则有 aborted 或 skipped 即 aborted，否则 passed；run 是终态当且仅当全部 job 是终态。前台 `schedule` 与后台 `project_full` 都不再给 run 级说明，run 级说明只由结束写写下（位置：core/gherkai_core/project.py `run_verdict`、`RunVerdict`、`project_full`、`projected_run_status`；core/gherkai_core/schedule.py `schedule`；依据：0031 决定三「取法」与被拒方案①至④；0054 决策二「run 级说明只由结束写写下」一句）
- 实装定下 run 状态取法函数的名字之后，回填 ADR 0031「touch points」里 core/gherkai_core/project.py 一条：把「run 状态的取法（决定三）」写成具体符号，与同节其余各条一样落到符号，不改写成「以 code 为准」。同一提交核对 schedule.py 一条里列的赋态点符号（abort_flag、stop_reason、project.finalize_job），看它们是否因结束写的改动而换了名字；如果端口上结束写入口的方法名与 0031 正文有交叉，也一并核对。（依据：0031 touch points；0030 决定四「方法名与参数形态以 ports.py 为准」只管端口签名，不管 touch points）
- 端口新增结束写入口，取代 `try_finalize` 与它的 `expected_claim_count`：一次条件写，run 未结束时把运行态里是 pending 的 job 记 skipped、running 的记 aborted，各带说明表里的一句，run 状态按取法随之成为终态并写下 run 级说明与结束时刻；判断只看运行态、不读事件；运行定义不可用时的变体把每个未结束的 job 记 error；不写明细、不点名；只在 run 未结束时写成、返回是否写成，STATE 不存在时返回 False；云端以写入序号为条件。前台、后台推进与处置方共用这一个入口，方法名与参数由实装定在 ports.py（位置：core/gherkai_core/ports.py `RunStore.try_finalize`；core/gherkai_core/adapters/run_store/local.py 与 ddb.py 的 `try_finalize`；依据：0031 决定三「结束写」小节与说明表；0030 决定四；0034 机制三②）
- `update_job_state` 改为新语义：同一次写按取法写 run 状态（云端连同 status_group），使 run 成为终态的那次写同时写下结束时刻；job 终态只写一次并带点名的标识；run 已结束时写不成、返回 False，删去 run 已结束时只写 job 的那次回退写；云端记下 job 终态的写以写入序号为条件、对 jobs 整体替换（位置：core/gherkai_core/ports.py `RunStore.update_job_state`；adapters/run_store/local.py 与 ddb.py 的 `update_job_state`；依据：0030 决定四；0034 机制三②③；0054 决策五）
- 状态投影只推进运行态：`project_state` 的逐 job 合并不越过 running、不写 job 终态，已写下的终态不被改动；run 级只写 running（位置：adapters/run_store/local.py 与 ddb.py 的 `project_state`；core/gherkai_core/project.py `project`；依据：0034 核心思想、机制三②与「run 级状态只进不退」条②；CONTEXT「状态投影」）
- 后台推进改为逐 job 写序：这一轮快照里已有结果的各 job 先存明细、再以一次条件写记下终态并点名（一次写可记多个 job），写不成即重读再算，不再等全部 job 结束才一次收尾；推进决策给出的结束动作只剩到期的结束写，「未启动」按这一轮运行态里的 pending 判断、不读事件；读不到可用运行定义时的结束写不经推进决策（位置：core/gherkai_core/reconcile.py `tick`、`_finalize`、`_claim_times`；core/gherkai_core/project.py `plan_next`、`project_full`；依据：0030 决定三「后台推进同守」；0034 机制三「收尾各步的先后与之后会不会变」的步骤；0054 决策二后台推进条「决策」「快照」）
- 终结函数真值表的 timeout 一行拆成两行：起作用的截止时刻是 job 预算时记 ERROR 加 timeout，是运行期限时记 ABORTED、没有归因（说明沿用「这个 run 已超过允许运行的时间，job 被中止」）；截止时刻由 `run_deadline.job_cutoff` 算，两者相等时算预算，不看说明；内容完整的 job 两种截断都不改判；stop_reason 的来源去掉接力补写（位置：core/gherkai_core/project.py `finalize_job`、`_reduce_scope`、`DEADLINE_TIMEOUT_MESSAGE`；core/gherkai_core/run_deadline.py `job_cutoff`；依据：0034 机制二「终结函数与真值表」「内容完整后不再仲裁」；0031 决定一提示框；0054 决策二第 2 条）
- 前台没有启动的 job 不再构造 skipped 的 JobResult：起 worker 之前三项检查（已过停止启动、已发现 run 被别处结束、已因 fail-fast 或使用方中断而中止）任一成立即不启动、job 留在 pending；`_stop_all` 不给排队中的 job 记 skipped；执行中的 job 都结束之后由 `RunPersistence.finalize` 的结束写记 skipped，已发现 run 被别处结束的不写；被期限截断的执行中 job 记 aborted；job 级 skipped 只在运行态里，结束写不产出 JobResult（位置：core/gherkai_core/schedule.py `_Worker.run`、`_Worker._run_once`、`_SKIPPED`、`schedule` 内的 `_stop_all`；core/gherkai_core/persist.py `RunPersistence.finalize`；依据：0054 决策二「一次前台执行可能因三种原因停下」段；0031 决定一的表与决定六层次对照表；0026「失败隔离」「起 worker 与重试之前的检查」；0024 终止契约「使用方中断」条）
- 核对重试之前的检查按分支落实：已过停止启动或已中止时写下上一次结果并注明没有再重试及原因；发现 run 已被别处结束（含重新起 worker 之前读到终态）的不写终态、不存明细（位置：core/gherkai_core/schedule.py `_Worker._retry_refused`；依据：0054 决策二「上一次尝试已经结束、正在等待重试的 job」条；0028「core 层 job 重试」节「重试之前的检查」条）
- 运行定义不可用时（结构版本不是后端认的、定义违约、缺 worker 镜像版本），云端推进器与本机后台推进进程都以结束写的 error 变体结束：每个未结束的 job 记 error、run 随之 error，说明取 0037 决策 7 的几句，不存明细（位置：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py `_load_definition`、`_build`；runtime/gherkai_runtime/detached.py `build_local_reconcile`；依据：0031 决定三「运行定义不可用时」条；0034 机制三「不经推进步骤的收尾」；0037 决策 7；0038「运行时与 preflight」）

#### 判定明细点名与落库写序

- 明细每次保存一个新对象、键里带写入方生成的随机标识，本机对同一次保存的重试用同一个标识；读者先读运行态、按被点名的标识取那一份，不列举目录或前缀，没被点名的不读、不清理；端口去掉 `load_all`，本机不再按 scope_id 覆盖同一个文件；S3 键在 `<prefix>/<run_id>/jobs/` 之下，是否还带 scope_id 由实装定（位置：core/gherkai_core/ports.py `ResultStore.save_job_result`、`load_job_result`、`load_all`；core/gherkai_core/adapters/result_store/local.py 与 s3.py；依据：0030 决定三「点名」条、决定六 ResultStore 段）
- 运行态每个 job 条目带点名的标识（未点名时省键），本机 run_state.json 与云端 jobs Map 两边都带，serialize 的 JobState 读写加这个键（位置：core/gherkai_core/model.py `JobState`；core/gherkai_core/serialize.py 的 run_state 读写；adapters/run_store/local.py 与 ddb.py；依据：0030 决定三、决定五括注、决定六「RunState.jobs 落 DDB 用原生 Map」段）
- `RunPersistence` 按逐 job 写序：`on_job_complete` 先生成标识、存明细，再写终态并点名（带认领时刻）；本机保存失败按 1、2、4 秒退避重试 3 次（同一个标识），仍失败即推进器退出（前台 `run` 以非零退出码结束），执行中的 job 留在 running、之后由 run 处置结束；本机后台推进进程保存失败同样处理；`finalize` 在还有未结束的 job 时做结束写，本进程的写使 run 成为终态时从记录生成报告（位置：core/gherkai_core/persist.py `RunPersistence.on_job_complete`、`finalize`；core/gherkai_core/reconcile.py `tick`；依据：0030 决定二、决定三「保存明细失败」条）

#### 本机推进器、生命期锁与边界检查

- 生命期锁：持有方以只读方式打开 `<report-dir>/<run_id>/`、取排他 flock，描述符不可继承，持锁进程只经 exec 起子进程（隧道建在宿主进程里，不是子进程）；`run` 和本机 `submit` 启动的后台推进进程都自己建 run：建出 run 目录、拿到锁之后才写运行定义与运行态，持有到进程退出；锁只在建 run 的那个进程里，不在进程之间传递；`submit --backend local` 不拿锁、不建 run：做完计划与补全运行定义之后，以新会话启动后台推进进程，经它的标准输入一次交给它建 run 所需的输入，另给一条回报管道；后台推进进程依次取创建时刻、起隧道、生成运行定义、建 run（含边界检查与取锁）、建事件库，回报结果（建成时是 run 的标识与公网地址，没有建成时是原因与退出码）并关闭管道，然后推进到 run 结束、退出；`submit` 按回报输出结果，以回报里的退出码结束；只有 EWOULDBLOCK 算持有者还在，其余错误按锁不可用；锁已被持有或不可用时不建 run、以退出码 2 结束（本机后台经回报由 `submit` 给出）（位置：cli/gherkai_cli/__main__.py `_cmd_run`、`_submit_local`、`_cmd_reconcile`；runtime/gherkai_runtime/detached.py `drive_local_reconcile`、`build_local_reconcile`；依据：0054 决策三；0035 决策 3「三种组合的宿主与次序」「本机 `submit`」一条；0034「命令形态」）
- 本机后端报告目录的边界检查：对要取锁的那个 run 目录的描述符取文件系统类型（macOS 用 fstatfs 取类型名，Linux 用描述符的 mnt_id 在本进程的挂载信息里取那一条），只放行清单里的类型（macOS 为 apfs；Linux 为 ext4、tmpfs、overlay、xfs、btrfs、ext3）；建 run 的一方另在建 run 目录之前对报告目录（不存在时取最近一层已存在的上级）判断一次，被拒时不留目录；判断不了或类型不在清单里时以退出码 2 结束，说明写原因、检测到的类型与清单；判断与取锁对同一次打开做，提交进程不打开 run 目录、也不做这项判断；`run`、本机 `submit` 启动的后台推进进程、等待中的 `status --wait`、`settle-runs` 与 `doctor` 共用同一判断，其余命令不查（位置：新增，模块由实装定（判定与处置在 runtime 包）；调用方 cli/gherkai_cli/__main__.py `_cmd_run`、`_cmd_status`、`_cmd_doctor`、新命令 settle-runs，以及后台推进进程一侧 runtime/gherkai_runtime/detached.py；依据：0054 决策四；0041 决策四）
- 删去本机接力：`status --wait` 不再进入推进循环（`_cmd_status_body` 里调 `detached.drive_local_reconcile` 的分支、`_INTERRUPTED_RELAY_NOTICE`、`_WAIT_WITHOUT_RELAY_NOTICE`），删去 `_recover_timed_out_claims`、`_RECOVERY_MARGIN_S`、`SubprocessLauncher.owned_scopes` 与 status 子命令的 `--max-concurrency`；`SqliteEventLog.record_timed_out_if_absent` 在本机只有接力用到，随 `EventLog` 端口一起定去留；后台执行标记只进 `list-runs --json` 的 detached 键、不参与任何判断（位置：runtime/gherkai_runtime/detached.py；cli/gherkai_cli/__main__.py `_cmd_status_body`、`_build_parser` 的 status 子命令；core/gherkai_core/adapters/event_log/sqlite.py；core/gherkai_core/reconcile.py `EventLog`；依据：0034 被拒方案「本机接力，及其改法」与「推进器与触发源」第 1 至 3 条；0054 决策八；0016 cli --backend 一节 `build_local_stores` 条）

#### run 处置：settle-runs 与 status --wait

- 处置的判定与动作放在 runtime 包，`status --wait` 与 `settle-runs` 共用：可以处置的条件是试拿锁拿到了，或当前时刻严格晚于期限加 300 秒（按墙钟），云端只有后一条；运行态读不出时不处置，期限读不出时只剩试拿锁一条；处置读运行态，已结束不动，否则做结束写（说明取说明表里处置的两行，两个条件同时成立取「锁拿到了」，句末加「（已记为已结束）」），写成的一方从记录生成报告；处置不推演事件、只改记录、不停执行（位置：新增于 runtime 包；依据：0054 决策六、七、八；0031 决定三「结束写」说明表）
- 新命令 `gherkai settle-runs [run_id] [--dry-run] [--json]`：取 0041 决策六的三项定位参数并读项目配置文件，取值来源与 status 相同，`--backend cloud` 下同样有效，任何云端读写之前先过版本 skew 闸；不给 run_id 时处理这个后端里全部未结束与运行态读不出的 run，不分前台与后台；reason 按序取 unreadable、already_finished、unsupported_filesystem、advancer_exited、past_deadline、lock_held、undetermined、within_deadline；advancer_exited 与 past_deadline 的 outcome 是 settled（`--dry-run` 下是 would_settle，锁拿到即放开），其余为 skipped；人读输出逐条给出 run、判定结果与处置，`--json` 给落点字段（同 list-runs）、dry_run 与 runs[]（各带 run_id、outcome、reason）；退出码：执行完成为 0（含一个都没处理，跳过不改变退出码），用法错误、后端不可达、给出的 run 不存在、报告目录不过边界检查、写入失败为 2，写入失败即停止、再执行一次安全（位置：cli/gherkai_cli/__main__.py `_build_parser` 与新的命令函数；runtime/gherkai_runtime/compose.py `check_backend_skew`；依据：0054 决策八 settle-runs 条；0031 决定五；0041 决策三、决策六；0053 决策 1；0037 决策 7「接线」条）
- 等待中的 `status --wait`，两个后端、前台与后台的 run 都一样：每次轮询看处置条件（本机先试拿锁再比期限，云端比期限），成立即处置，再照常渲染、给终态的退出码；锁被持有不另说明，锁不可用时说明原因，运行态读不出时只等待并说明原因；不推进，云端不调用 kicker：删去 `_status_cloud` 的卡住检测与 kickoff（`_STALL_KICK`）和只为它设的 `compose._make_lambda_client`（位置：cli/gherkai_cli/__main__.py `_cmd_status_body`、`_status_cloud`；runtime/gherkai_runtime/compose.py `_make_lambda_client`；依据：0054 决策八 status --wait 条；0034「推进器与触发源」第 2 条）

#### 云端后端（runs 表、kicker 与 reconciler、定时触发、清扫、权限）

- STATE 条目带写入序号，每次写加一；记下 job 终态的写与结束写以「序号等于读到的值」为条件、对 jobs 整体替换，写不成即重读再算；认领按 scope_id 单元素写、投影逐属性写，各自条件不变、同样加一；status_group 只在使 run 成为终态的那次写（最后一个终态写或结束写）里由 live 换成终态值；认领计数只作 `status --json` 的诊断键（位置：core/gherkai_core/adapters/run_store/ddb.py `DynamoDBRunStore` 的各写入口；依据：0030 决定六；0034 机制三②与「run 级状态只进不退」条①）
- kicker 的流过滤改为两条：INSERT 且 item_type 为 STATE（建 run 时 META 先于 STATE 的写序保留）；新映像 status_group 不是 live 的 STATE 条目（使 run 成为终态的那次写，触发清扫）；删去按 NewImage.detached 的过滤（位置：deploy_aws/gherkai_deploy_aws/stack.py `_reconcile_lambdas`；依据：0034 端到端 cloud 1b「触发过滤不看后台执行标记」；0054 决策九；0033 资源清单 13）
- handler 不按后台执行标记分流：删去 reconciler `_build` 里的 `is_detached` 判断，删去 exit-observer 的 `_is_detached`、它对 runs 表的读权限与 RUNS_TABLE 环境变量；`DynamoDBRunStore.is_detached` 只留给 `list-runs --json` 的 detached 键（位置：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py `_build`；lambdas/exit_observer.py `_is_detached`、`handler`；stack.py `_reconcile_lambdas`；adapters/run_store/ddb.py `is_detached`；依据：0034 端到端 cloud 1b；0041 决策七）
- kicker 收到 STATE 新建时建 run 的两次一次性定时触发：deadline_at 一次（对仍在执行的 job 做 job 到点停止再推进），deadline_at 加 300 秒一次（后端到期结束：run 仍未结束即按处置做结束写，说明取「已超过允许运行的时间」）；名字由 run 确定、重试不重复建，建不成时这次调用失败、由流重试；到点重新读墙钟确认已过，未过则在这次调用里等，run 已结束时只清扫（位置：deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py `kicker_handler`、`EventBridgeTimeoutWatch`；stack.py `_reconcile_lambdas` 的 Scheduler 资源域；依据：0054 决策九第 1 条；0033 资源清单 15）
- 结束即清扫：run 到终态之后按 startedBy 列出仍在执行的 task 逐个停掉，可重复、不写 runs 表，流触发的按批内 run 去重；各入口（worker 事件、退出记录、定时触发）遇到已结束的 run 都只清扫、不推演不投影不认领不存明细；清扫放在「已结束的 run 跳过」之前，job 超时入口先看 run 是否已结束再看 job 状态；推进 Lambda 角色上列 task、停 task、建定时触发的权限随之核对（资源域待定时触发的名字定）（位置：lambdas/reconciler.py `handler`、`kicker_handler`、`_build`、`_tick_runs`、`_handle_timeout`；stack.py `_reconcile_lambdas`；依据：0054 决策九第 2 条与「落实时清扫的位置」段、末段权限；0034 端到端 cloud 第 3、4 步）
- 编排进程一侧的权限按 0033 改：删去同步 run 的 ecs:RunTask、StopTask、DescribeTasks、iam:PassRole、events 表 Query 与 PutItem、job 上传与读 subnet、安全组的 SSM，删去 status --wait 的 lambda:InvokeFunction；加处置方（status --wait、settle-runs）的 runs 表条件写、报告桶 s3:GetObject（卸载的运行定义正文与被点名的明细）与报告前缀 s3:PutObject，settle-runs 不给 run_id 时另需 list-runs 的两项；列这份权限的文档随之改，见下「行为文档」块（位置：用户文档与 skill 的权限表；依据：0033 资源清单末段「编排进程角色」与 IAM 节；0040 决策 3）

#### 查看命令与机读输出

- `run --json` 新增 jobs[]：列出运行定义里的全部 job，状态与由结束写结束的 job 的说明取运行态，被点名的附上那一份明细的各键；run 在本次执行结束之前已被别处结束时，本次判出的结果不写进记录、不再存明细，不输出汇总，`--json` 的 stdout 为空，不生成报告，退出码 1（处理过使用方中断时按信号取 130 或 143）（位置：cli/gherkai_cli/__main__.py `_cmd_run`；cli/gherkai_cli/render.py `render_text`；core/gherkai_core/persist.py `RunPersistence.finalize`；依据：0041 决策三；0054 决策五「执行方服从记录」；0031 决定五）
- 退出码读记录：有记录时读记录里的 run 状态，`run --no-report` 在内存里按取法算；各命令按 0031 决定五（run 与 status --wait 以 passed 为 0、其余终态为 1，status 未结束或 passed 为 0，submit 不表示判定）；退出码 2 另有三类：边界检查不过、锁已被持有或不可用（只对建 run 的一方）、run 给出云端后端（位置：cli/gherkai_cli/__main__.py `_cmd_run`、`_cmd_status`、`_render_status`；依据：0031 决定五）
- `status --json` 的 jobs[] 每项带这个 job 终态点名的明细标识（未点名省键），顶层带 deadline_at，不另给由它推出的键（位置：cli/gherkai_cli/__main__.py `_render_status`；依据：0041 决策三）
- 不带 `--wait` 的 status 与 list-runs 给同一句期限提示（只看记录与期限、不碰锁：未结束而已过期限加 300 秒的 run 提示「已超过允许运行的时间（可用 settle-runs 或 status --wait 记为已结束）」），删去「推进可能未启动、可 status --wait 接力」的 pending 提示与 relay_available 回调（位置：cli/gherkai_cli/__main__.py `_render_status`、`_status_cloud`、`_cmd_status_body`；依据：0041 决策七「人读形态」；0034 命令形态「不带 --wait 的 status」条）
- list-runs：人读表格按列序加「已运行」「允许运行至」两列与期限提示，`--json` 加 deadline_at，detached 只作描述，`--status` 不再接受 skipped（给出以退出码 2 结束），命令只读、不推进、不处置、不碰锁；core 端口的列举项加 deadline_at，与写出版本同在一次头部读取里；run 不再会是 skipped，默认清单查几个终态分组由实装定（实测读量按 live 与五个终态分组计），定了之后回写 0041 决策七「代价」段与实测项的读量（位置：cli/gherkai_cli/__main__.py `_cmd_list_runs`；core/gherkai_core/model.py `RunListing`；core/gherkai_core/ports.py `RunStore.list_runs`；依据：0041 决策七）
- doctor 新增 report_dir 组的 report_dir.filesystem 一项：本机后端必修，只读、不碰锁，判断规则同 0054 决策四，`--backend cloud` 时不出这一行；doctor 子命令 `--report-dir` 的 help 不再标 [cloud]（位置：cli/gherkai_cli/__main__.py `_cmd_doctor`、`_build_parser` 的 doctor 子命令；依据：0041 决策四；0054 决策四）
- explain：先经 RunStore 读运行定义与运行态（job 清单与各 job 点名的标识），只按标识读被点名的那一份明细，不再调 `load_all`；run 与 job 的状态取运行态；由结束写结束的 job 以 job 定义为骨架，状态与说明取运行态，已执行的 step 从事件流补取（云端限事件保留期之内），由结束写记 aborted 的 job 的 step 记录全部来自事件流；运行态里还没有已结束的 job 时以退出码 0 结束、只打「判定明细尚未落地」并给出可原样执行的整条 status --wait 命令，删去「本 run 没有任何 job 的判定明细」一句；给了 scope_id 而这个 job 在运行态里还没有结束时同样以退出码 0 结束、提示它还没有结束，不报「未找到 scope」；云端不需要 s3:ListBucket；补测试；若改「判定明细尚未落地」的原文，0031 决定一·补的 TERMINAL_STATUSES 消费方清单同步改（位置：cli/gherkai_cli/__main__.py `_cmd_explain`、`_explain_emit`；cli/gherkai_cli/render.py `explain_tree`、`explain_to_dict`；依据：0042 决策四「数据来源」「未终态的 run」、决策七第 3 条；0031 决定一·补）
- 「诊断细节见 worker 日志」只对运行态里带认领时刻的 job 打；没有认领时刻的 job（由结束写记 skipped 的，以及运行定义不可用时由 pending 记 error 的）只给状态与说明；补测试（位置：cli/gherkai_cli/render.py `explain_tree` 与 `explain_to_dict` 里同一逻辑的注释；依据：0042 决策四「记录缺口的两种情形」第一条）

#### 报告

- 报告只由使 run 成为终态的那次写的写入方生成，生成时从记录组装 RunResult（运行态加各 job 被点名的明细）再渲染：前台由 `RunPersistence.finalize`、后台由收到 COMMITTED 的宿主、处置时由写成结束写的处置方调用同一处组装；后台不再用这一轮 `TickResult.result`；写入方在生成之前中断则没有报告，不设重建路径；`ReportStore.write` 的 docstring 改为从记录生成，`RunPersistence.finalize` 里「报告可后续从 RunResult 重建」的说法随之改（位置：core/gherkai_core/reconcile.py `finalize_report`、`TickResult`；core/gherkai_core/persist.py `RunPersistence.finalize`；runtime/gherkai_runtime/detached.py `run_reconcile_loop`；deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py `_tick_runs`；core/gherkai_core/ports.py `ReportStore.write`；依据：0027「ReportStore 接口：整 run 一次写」；0034 机制三「run 级状态只进不退」条④与 K2；0030 决定三）
- index.html：由结束写结束的 job 按运行态显示状态（配色同各状态）与说明，没有明细树，排在由执行结果结束的 job 之后、按运行定义的次序；删去「没有执行」这个字面量（core 的入口页与 cli 的 `_NOT_RUN_LABEL`）以及逐字锁定它的测试；report_index 与渲染取自由记录组装的 RunResult，manifest 的 ref 取被点名的那一份明细（位置：core/gherkai_core/adapters/report_store/local.py `render_index_html` 与 s3.py；cli/gherkai_cli/render.py `_NOT_RUN_LABEL`、`render_text`；依据：0027「index.html 形态」、职责边界与「manifest.json 形态」）

#### 测试

- 改写 test_conditional_writes.py 里断言旧设计的用例：`test_job_write_on_finalized_run_lands_job_only` 与 `test_job_write_on_a_finalized_run_reports_it_ended`（断言 run 已结束时 job 照写）、`test_ddb_job_write_update_item_counts`（断言已收尾时发两次 update_item）、`test_finalize_with_expected_claim_count_lands_only_on_an_equal_count`、`test_ddb_finalize_with_expected_claim_count_is_one_conditional_write`、`test_finalize_conditioned_on_the_read_count_is_blocked_by_a_claim_landing_after_the_read`（以认领计数作收尾条件，改为写入序号），以及守着已删被拒方案的 `test_finalize_from_nonterminal_succeeds`；模块文档串讲「收尾写可带期望的计数」一句随之改（位置：core/tests/test_conditional_writes.py；依据：0034 机制三②、K1 与「两端对拍口径」；0054 决策五）
- 补对拍用例，本机文件与 moto 两个 adapter 都覆盖：run 已结束时写 job 写不成、运行态不变，DDB 只发一次 update_item；写入序号每次写加一，以序号为条件的终态写与结束写只在序号相等时写成，读之后落下的写挡住它；job 终态只写一次；经 Lambda 的代码在真 DynamoDB 上重做并发与几百个 job 的结束写（按实际 job 项大小，含点名的标识），只有一方生成报告（位置：core/tests/test_conditional_writes.py；core/tests/test_cloud_integration.py；依据：0034 机制三②的实测项与「两端对拍口径」）
- K2 的三个测试改为断言报告从记录生成（位置：core/tests/test_reconcile.py `test_report_comes_from_the_committed_result_not_from_a_second_read_of_the_events`、`test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots`；deploy_aws/tests/test_lambda_handlers.py `test_tick_runs_writes_the_report_from_the_committed_tick_result`；依据：0034 机制三 K2）
- 机制三删去的测试项对应的测试删或改：第 2 项的云端一半（run --backend cloud）、第 4 项的后半（已结束 run 上 job 写照样写成）、第 5 项的本机多推进器；本机认领竞态用例不再成立（本机锁内的结束写会把新认领的 job 记 aborted 并结束 run），删去或改写；实测项 7 只留云端用例，它的文档串改为「被写入序号的条件挡下」并换掉「推进方」「收尾写」「到期收尾」；「收尾写不带认领计数」的用例随之改（位置：core/tests/test_reconcile.py `test_expiry_loses_to_a_claim_that_landed_after_the_read`、`test_all_done_after_the_deadline_aggregates_without_the_claim_count_condition`；core/tests/test_cloud_reconcile.py `test_expiry_loses_to_a_claim_that_landed_after_the_read_on_ddb`；依据：0034 机制三；0054 实测项 7 与决策二后台推进条「收尾与报告」）
- 终止对拍矩阵去掉接力补写，加上期限截断与预算截断的分行（预算为 error 加 timeout，期限为 aborted）；到期用例文档串里「后台的运行态里 b 保持 pending」随结束写改（位置：core/tests/test_termination_parity.py `test_expiry_agrees_between_the_foreground_and_the_advancer` 等；依据：0034 机制二「双路径对拍是实施护栏」）
- run_verdict 与按原因优先序的用例删改：`test_user_interrupt_with_passed_and_aborted_marks_run_aborted`、`test_interrupt_then_past_stop_start_reports_the_deadline_over_aborted` 与「使用方中断」「运行期限与这次 run 的记录」两节的分节注释；test_project.py 的「run 级裁决」一节与 `test_project_full_run_level_comes_from_the_shared_verdict`（写的是 0031 决定三被拒方案②）；`test_plan_next_past_stop_start_never_proposes_a_start` 与 `test_plan_next_past_stop_start_does_not_expire_while_a_recorded_job_is_still_pending` 的「未启动只指事件流里没有记录的 job」改为按运行态的 pending；另核 code 与测试注释里指向 0031 决定三已删内容（过滤名单、空判定集规则）的各处，按「0031 决定三」逐条查（位置：core/gherkai_core/model.py `_NON_VERDICT` 上方注释；core/gherkai_core/project.py `_aggregate`；core/tests/test_lifecycle_states.py、test_project.py、test_schedule.py、test_conditional_writes.py、test_reconcile.py；依据：0031 决定三；0054 决策二后台推进条「决策」）
- core/tests/test_status_group.py 模块文档串与 `test_create_derives_group_from_the_initial_status` 以 0030 决定六为出处写「传入终态初始状态」，决定六已不写这一情形：写明这是函数层的性质，或把用例收窄到 pending，由实装批择一（位置：core/tests/test_status_group.py；依据：0030 决定六「runs 表只有一个 GSI」条的写入规则）
- 0053 键集差集护栏：排除名单加 settle-runs 的 `--dry-run`，settle-runs 进读配置文件的命令清单（位置：cli/tests/test_project_config.py `test_every_long_option_is_classified_and_the_derived_key_sets_match`；依据：0053 决策 1、6）
- 部署模板测试：`test_exit_observer_can_read_runs_table_only` 随观察者不读 runs 表改；`test_kicker_mapping_insert_filter` 改为两条过滤（位置：deploy_aws/tests/test_stack.py；依据：0033 资源清单 13；0054 决策九）
- status --wait kickoff 的测试删改：cli/tests/test_backend_cloud.py 里 status --wait 调起 kicker 的用例（`test_status_wait_cloud_kicker_missing_fails_fast` 等），与删 kickoff 同批（依据：0054 决策八；0034「推进器与触发源」第 2 条）
- 接力与 handler 分流的测试随 code 删：runtime/tests/test_detached_launcher.py 的 `test_relay_recovers_foreign_timed_out_claim`、`test_relay_after_the_advancer_is_gone_ends_an_expired_run_without_starting_jobs`、`test_relay_keeps_a_real_exit_record_written_between_its_check_and_its_write` 与讲接力判定条件的一节；cli/tests/test_definition_schema.py `test_local_relay_reports_contract_violation_with_exit_2_instead_of_traceback`；deploy_aws/tests/test_lambda_handlers.py「只推进 detached run（handler 侧分流）」一节；core/tests/test_sqlite_event_log.py `test_record_timed_out_if_absent_writes_only_when_there_is_no_exit_record` 随端口方法定（位置：如列；依据：0034 被拒方案「本机接力，及其改法」、端到端 cloud 1b）

#### 隧道（0035）与两种 `submit` 的新流程

隧道一块（0035 决策 1、决策 3 与「边界与不变量」）的行为文档与 code，随隧道的实装批在同一提交里改。用户指南、internals、agent skill 与 CLI 用户可见文字一律照下面三条改：
1. 凡讲隧道前置条件的地方，都改为 0035 决策 1「前置条件」一条的写法：装可选依赖 `gherkai[tunnel]`，令牌只取环境变量 `NGROK_AUTHTOKEN`。安装 ngrok 可执行文件、ngrok 在 PATH 上、`ngrok config add-authtoken` 写进 ngrok 自己的配置文件，这些说法一律删去。缺前置在开始执行之前的检查里查出（`run` 与 `submit` 共用的前置检查，补全运行定义、上传安装包之前；退出码 2，不上传、不起后台进程），「在起隧道时失败」「起隧道时暴露」一类说法一并改掉：现在有这种说法的是 docs/user-guide/local-app-testing.md「前置」一节、docs/user-guide/troubleshooting.md「隧道（--expose-local）」一节、skill 的 SKILL.md 第 3 节与 references/setup-and-diagnosis.md 第 5 节。
2. 凡讲隧道拆不掉、要到进程列表里手动结束 ngrok（含 `kill -9` 之后要手动结束）的地方，一律删去：现在没有独立的 ngrok 进程，隧道随宿主进程退出而消失（0035 决策 3「寿命」）。
3. 0035「边界与不变量」里「同一个账号同一时间只有一条隧道在线（新注册的 ngrok 账号）」一条，要写进 docs/user-guide/local-app-testing.md 的「限制」一节。照 0035 那一条的原句写，报错与处理办法照它指向的决策 1「启动失败的说法按原因分」第 3 种说法写（等那条在线的隧道下线之后再试；报错带 `ERR_NGROK_334`，不点名 run，不提 `gherkai settle-runs`），不另作概括。troubleshooting.md 与 skill 的 references/setup-and-diagnosis.md 第 7 节里「地址已在线」时的处理办法，同样照第 3 种说法写。这条写法约束的来由是两家模型复核时做的「依据只在一处写全」结构处置。

- 隧道改用 ngrok 官方 Python SDK，建在宿主进程里，不再启动 ngrok 可执行文件。流量策略在内存里交给 SDK、不落盘，没有日志文件。令牌取环境变量 NGROK_AUTHTOKEN。runtime 的 pyproject 加 `[tunnel]` = `ngrok>=1.8.0`，cli 的 pyproject 加 `[tunnel]` = 同版本的 `gherkai-runtime[tunnel]`。SDK 只在给了 `--expose-local` 时导入。启动失败按四种原因给出说法，其中地址已在线时带 `ERR_NGROK_334`。`run` 与 `submit` 共用的前置检查先查这两项前置：SDK 已装、令牌已设。流量策略最前面一条是到点拒绝，时刻为运行期限加 300 秒（位置：runtime/gherkai_runtime/tunnel.py `NgrokTunnel`、`POLICY_RULE_LIMIT`；runtime/pyproject.toml、cli/pyproject.toml；依据：0035 决策 1「前置条件」「公网地址是 SDK 调用的返回值」「启动失败的说法按原因分」、决策 3「边缘到点拒绝」；0037 决策 2c）。
- 本机 `submit`：做完计划与补全运行定义之后，以新会话启动后台推进进程，经它的标准输入一次交给它建 run 所需的输入，另给它一条回报管道。后台推进进程依次取创建时刻、起隧道、生成运行定义、建 run（含边界检查与取锁）、建事件库，然后回报结果，再开始推进。建 run 之前查一次回报管道，另一端已关闭就不建 run，关闭会话后退出（位置：cli/gherkai_cli/__main__.py `_submit_local`、`_cmd_reconcile`；runtime/gherkai_runtime/detached.py；依据：0035 决策 3「三种组合的宿主与次序」本机 `submit` 一条；0034「命令形态」submit 行）。
- 云端 `submit`：先过云端各道闸并补全运行定义，取创建时刻、算出运行期限，以新会话启动隧道守护进程，并把到点时刻（运行期限加 300 秒）交给它。守护进程起隧道，经回报管道交回公网地址与预热地址。`submit` 在建 run 之前查一次管道，守护进程那一端已关闭即不建 run、以退出码 2 结束；否则生成运行定义、建 run，再把 run 的标识交给守护进程。守护进程轮询 run 的状态，到终态或到运行期限加 300 秒时退出。去掉 `--tunnel-ttl`，删去 TTL 记账常量与 `compute_watch_ttl_s`，删去 `tunnel.json` 兜底拆与 cleanup_tunnel（位置：cli/gherkai_cli/__main__.py `_cmd_submit`、`_submit_cloud`、`_tunnel_watch`；runtime/gherkai_runtime/tunnel_host.py；依据：0035 决策 3 云端 `submit` 一条）。
- 测试随之删改：runtime/tests/test_tunnel.py、runtime/tests/test_tunnel_host.py、cli/tests/test_tunnel_cli.py，以及 detached 一侧讲交接与拆隧道的用例（依据同上）。
- 隧道的用户可见文字随实装改为 0035 的目标设计（位置：cli/gherkai_cli/__main__.py、runtime/gherkai_runtime/tunnel.py；依据：0035 决策 1「前置条件」「启动失败的说法按原因分」，决策 3「寿命」「本机 submit」「云端 submit」与「cloud submit 的语义澄清」，被拒方案「保留 --tunnel-ttl，只允许调小」）：
    - run 与 submit 的 --expose-local help：「需已配 ngrok authtoken（NGROK_AUTHTOKEN）」改为可选依赖 gherkai[tunnel] 加环境变量 NGROK_AUTHTOKEN；「运行结束即拆除」按决策 3「寿命」改写。
    - 删去 submit 的 --tunnel-ttl 参数，连同它的 help（「[cloud + --expose-local] 隧道守护进程的兜底 TTL 秒」）和取值校验报错（「无效：须为有限正数（TTL 到点无条件拆隧道…」）。
    - 本机 submit 的进度行「隧道由本机后台进程持有（pid 记录于 …tunnel.json）：run 终态即拆」：删去进程号、tunnel.json 和「终态即拆」。
    - 云端 submit 的进度行「隧道由守护进程持有（日志 …）：run 终态即拆、TTL 兜底 …」：删去「终态即拆」、TTL 和 TTL 的来源；日志落点按决策 3「云端 submit」的「日志：」一句（系统临时目录里的 gherkai-tunnel-watch-<run_id>.log）；「本机需保持开机联网直到 run 终态」保留。
    - 删去进度行「隧道已拆除（本机的被测应用不再对外暴露）」。
    - tunnel.py 的启动失败报错（「找不到 ngrok 可执行文件」「ngrok 隧道未就绪（」）改为决策 1 的四种说法，都以退出码 2 结束。
    - 取舍：submit 不再打印生效的存活时长，也不改为打印别的时刻；要打印，先写进 0035 决策 3「cloud submit 的语义澄清」一条。
- _cmd_submit 末尾 finally 里就地拆隧道的一段整段删去，不改写。删除范围包括进度行「隧道已拆除（本机的被测应用不再对外暴露）。若上面已经打出提交成功，这个 run 就别再往下推……」、stop_tunnel(tunnel_info.pid)、handed_off 与 on_handoff，以及上方讲「隧道交棒的分界线」「没交棒不等于没提交」的注释。理由是 submit 自己不再起隧道：本机 submit 由后台推进进程起，云端 submit 由隧道守护进程起（0035 决策 3「三种组合的宿主与次序」）；也没有拆隧道的记录或命令（0035 决策 3「寿命」）。原先要在这里交代的情形改按 0035 决策 3 的回报管道各条输出：本机见「后台推进进程在回报之前退出」一条（报错、退出码 2，说明 run 可能已经建成而没有推进器，可以用 gherkai settle-runs 记为已结束）；云端见「与本机同一条规则」一条（守护进程在 submit 查过管道之后才退出时，照常输出 run 的标识、退出码 0，另在 stderr 说明隧道已经不在、这个 run 里要访问被测应用的 job 会失败）。0035 已没有「被接受的代价」与交棒边界一条，不需要同步改 ADR（位置：cli/gherkai_cli/__main__.py `_cmd_submit`；依据：0035 决策 3「寿命」「三种组合的宿主与次序」）

#### 随实装改写的 code 注释（指针已处理，行为描述待改）

- 认领计数作写条件的描述改为写入序号（认领计数不作任何写的条件）：`RunState.claim_count` 注释的「到期收尾写以库中计数等于读到的值为条件」、`RunStore.try_finalize` 的 expected_claim_count 说明、两个 adapter 的 `try_finalize`、`_finalize` 的步骤③、`RunPersistence.finalize` 的「不带认领计数的条件」、core/DEVELOPMENT.md reconcile.py 一条的「以带认领计数的条件写收尾」（前半句不动）（位置：core/gherkai_core/model.py、ports.py、reconcile.py、persist.py、adapters/run_store/local.py 与 ddb.py、core/DEVELOPMENT.md 目录树；依据：0034 机制三②、「run 级状态只进不退」条①；0054 决策二后台推进条「收尾与报告」）
- run 级说明「只给没有任何 job 能承载的原因」改为每条来路都有一句、只由结束写写下：`RunVerdict` 文档串、`RunResult` 与 `RunState.message` 注释、`RunStore.try_finalize`、`render_index_html` 里 run 级说明一句、ddb.py 模块头 STATE item 一条（位置：core/gherkai_core/project.py、model.py、ports.py、adapters/report_store/local.py、adapters/run_store/ddb.py；依据：0031 决定三「结束写」小节说明表；0037 决策 7）
- 「没有启动的 job 保持 pending、不产出判定、是 run_meta.jobs 与 jobs 的差」改为由结束写记 skipped：`RunPersistence.on_job_complete` 附近、`_Worker.run` docstring、`Status`（PENDING 一行与 skipped/aborted 段落）、`RunResult` 与 `jobs_without_verdict`、`render_text`、`render_index_html`（位置：core/gherkai_core/persist.py、schedule.py、model.py；cli/gherkai_cli/render.py；adapters/report_store/local.py；依据：0054 决策二「一次前台执行可能因三种原因停下」段；0031 决定一、决定三被拒方案②）
- 「run 级裁决：包住 _aggregate、加上聚合之外的例外」一类描述随 run_verdict 删改：`run_verdict`、`schedule` 里调裁决处的注释、core/DEVELOPMENT.md project.py 一条（run_verdict 一项，与 plan_next「余下的 job 在事件流里都没有记录时」半句）、`Status` 的 aborted 段落（位置：core/gherkai_core/project.py、schedule.py、model.py；core/DEVELOPMENT.md；依据：0031 决定三；0054 决策二后台推进条「决策」）
- 「终态是 finalize 专属」「try_finalize」「判定真值的唯一权威是 jobs/*.json」一类说法改写：run_store/local.py 模块头（含 fcntl 叙述）与 `project_state`、ddb.py `project_state`、ports.py `RunStore` 探活注释「配置错一律 begin 暴露」、`RunPersistence.begin`（以云端桶名错分裂退出码为理由）、`NonTerminalSnapshot`（强制点改为保存一个 job 的明细之前，不再写 jobs/*.json）（位置：core/gherkai_core/adapters/run_store/local.py 与 ddb.py；core/gherkai_core/ports.py；core/gherkai_core/persist.py；core/gherkai_core/project.py；依据：0030 决定三、决定四、决定七；0031 决定一·补）
- 明细「后写的盖掉先写的」「保存覆盖同 key」改为每次保存一份、由终态点名：result_store/local.py 模块头与 `save_job_result`、`_finalize` 步骤②、core/tests/test_local_result_store_atomic.py 模块文档串（位置：如列；依据：0030 决定三「点名」条；0034 机制三开头「判定明细」条）
- 接力的描述：reconcile.py 模块头触发源括注里的「status --wait 接力」（删掉之后可恢复指向 0034「推进器与触发源」）、`EventLog` 里讲本机接力恢复的两处、project.py `TaskExited` 的接力补写说法、detached.py 模块头与 `run_reconcile_loop`、`drive_local_reconcile`（含「接力者同样兜底拆」）、`build_local_reconcile` 的接力说明、`RunMeta` 与 `JobState.claimed_at` 注释和 `RunStore.try_claim_job` 里列的接力用途（claimed_at 只是截止时刻的起算点）、`LocalRunStore` 里「接力者」一句、`_cmd_status` 与 `_cmd_status_body` 的「两道闸」、`_render_status`、`_status_cloud`、`_submit_local` 与 status 子命令的 help（位置：core/gherkai_core/reconcile.py、project.py、model.py、ports.py、adapters/run_store/local.py；runtime/gherkai_runtime/detached.py；cli/gherkai_cli/__main__.py；依据：0034「推进器与触发源」、被拒方案「本机接力，及其改法」、「job timeout」节 JobState.claimed_at 条①）
- 按 detached 分流的描述：ddb.py `is_detached` 文档串后半句（标记是执行环境属性、在 STATE 条目上的前半句保留）、ddb.py 模块头与 `_state_item` 的「kicker filter 认它」、exit_observer.py 模块头与 `_is_detached`、reconciler.py `_build` 与 `_run_ids_from_runs_stream`（status --wait kickoff 一格）、stack.py `_reconcile_lambdas`（三个 handler 自己分辨、kicker 靠流过滤的说明）、compose.py `build_cloud_stores` 的「触发 kicker 冷启动」一句、core/tests/test_ddb_run_store.py `test_detached_flag_on_state_item` 与 cli/tests/test_main.py `test_local_submit_marks_the_run_detached_and_foreground_run_does_not` 的文档串（位置：如列；依据：0034 端到端 cloud 1b「触发过滤不看后台执行标记」）
- RunState 写入方的指针：stack.py `_grant_task_role` 与 `_reconcile_lambdas`、test_stack.py `test_task_role_has_events_putitem_not_runs` 与 `test_exit_observer_can_read_runs_table_only` 写「RunState 的写入方见 ADR 0034『数据模型三件套』」，与 0024 红线条所指的 0034「命令形态」表统一成同一个指向（两处所指都存在）（位置：如列；依据：0024「DynamoDB 作 events-out 传输」节红线条；0034「命令形态」「数据模型三件套」）
- 隧道建在宿主进程里之后，以下行为描述随隧道实装改写；所在函数随实装删去的，注释一并删去：
    - deadline.py：模块头把云端每 job 尾段说成「隧道存活时间上限已在用的每 job 余量（tunnel_host.CLOUD_PER_JOB_MARGIN_S，210 秒）」，并从 tunnel_host import 这个常量；STARTUP_MARGIN_S 与 CLOUD_PER_JOB_TAIL_S 的注释拿隧道 TTL 作对照。改为 210 秒归期限算式所有，组成指向 0054 决策二「尾段与余量是预算的取值」一段。tunnel_host 的 TTL 常量删去之后，这个值改在 deadline.py 里定义。
    - tunnel_host.py：TTL 的记账常量、compute_watch_ttl_s；watch_run_and_stop_tunnel 文档串的「TTL 到点 → 拆隧道自杀」「不在此拆就没人拆」。
    - compose.py：FARGATE_STOP_TIMEOUT_MAX_S 之前注释里的「按它给隧道守护 TTL 的每 job 余量」。
    - tunnel.py：模块头的「停止用 stop_tunnel(pid)」，NgrokTunnel 文档串的「不走本地 agent API」，TunnelInfo 文档串的「可落盘 tunnel.json 供跨进程收尾」与 pid 字段，_launch 里的「三形态宿主 + stop_tunnel(pid)」「唯一拆除面」，规则上限一行的「四条规则留一条余量」。现在是 5 条规则、POLICY_RULE_LIMIT 为 5，见 0051 决策 13「边缘策略」。
    - detached.py：write_tunnel_file、cleanup_tunnel，drive_local_reconcile 的「拆隧道」，run_reconcile_loop 文档串的「退出后由调用方照常拆隧道」。
    - cli/gherkai_cli/submission.py（complete_local_definition 的文档串）与 __main__.py 里提到 --tunnel-ttl 或守护进程 TTL 的注释与文档串。
    - __main__.py：_cmd_submit 文档串的「崩了 status --wait 接力」与交棒分界的注释，_submit_local 写 tunnel.json 之前的注释，_cmd_run 起隧道之前的注释（「可手动结束来兜底」），_cmd_tunnel_watch 文档串的「可手动结束」。

    （依据：0035 决策 1「公网地址是 SDK 调用的返回值」与决策 3「寿命」「三种组合的宿主与次序」「边缘到点拒绝」；0035 被拒方案「保留 --tunnel-ttl，只允许调小」；0051 决策 13「边缘策略」；0054 决策二「尾段与余量是预算的取值」）

#### 行为文档（随所改行为的实装批同一提交改）

- core/DEVELOPMENT.md：架构决策列表里 0054 一行括注的「run 级裁决」「run 级终态不可变」改为「期限规则 run_deadline、生命期锁、终态不可变、执行方先认领再启动、run 处置」，与删 run_verdict 的实装同一提交；目录树的 run_store 一条写明认领计数只作 status --json 的诊断键，「条件写 try_claim_job/project_state/try_finalize」随结束写入口改（位置：core/DEVELOPMENT.md；依据：0054；0031 决定三；0034 机制三「run 级状态只进不退」条①）
- docs/internals/execution-and-reconciliation.md：收尾的写序（try_finalize、jobs/*.json、竞争收尾）、local submit 的超时一行（per-run 进程）、触发过滤的叙述（§7 与 execution-detached-gates 图现在写对后台标记恒放行的两道判断，随 handler 不分流与 kicker 的流过滤改）、讲接力的各处都随实装对齐（位置：如列；依据：0034；0054）
- 技术文档：runtime/DEVELOPMENT.md 的 detached 一条（接力判超时与指向 0054 决策二「本机接力的改法」的指针）；cli/DEVELOPMENT.md 讲接力的行为描述（位置：如列；依据：0034 被拒方案「本机接力，及其改法」）
- docs/internals/artifacts-and-evidence.md：explain 文本形态表里「诊断细节见 worker 日志」的条件补上只对运行态里带认领时刻的 job 给（位置：如列；依据：0042 决策四「记录缺口的两种情形」第一条）
- 用户指南：configuration.md 跨命令选项表的 `--max-concurrency` 不再列 status；0040 派生视图的云端一级改为 submit、status --wait、settle-runs，去掉 lambda:InvokeFunction、保留 lambda:GetFunction，加处置所需的条件写、报告桶 s3:GetObject 与写报告，推论改为云端执行不需要任何 ECS 写权限：running-and-results.md「怎么运行、在哪运行：三种组合」节的权限表、getting-started.md「按角色选安装形态」的角色表（三种组合已改）（位置：docs/user-guide/configuration.md、running-and-results.md、getting-started.md；依据：0040 决策 3；0033 编排进程角色）
- 机读契约页与它的 skill 副本：写出 settle-runs 的 `--json`（runs[]、outcome、reason）、status 与 list-runs 的 deadline_at、status --json 的点名标识、run --json 的 jobs[]；`test_run_json_top_level_message_is_always_present_and_documented_as_run_level` 锁定的「没有执行」一句随之改（位置：docs/internals/cli-json-contract.md；cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md；cli/tests/test_cli_json_contract.py；依据：0041 决策三、决策七；0054 决策八）
- agent skill 正文按 0043 决策五骨架改：去掉直接读 jobs/*.json 的说法，`--scope` 的取值写成 `--json` 输出里的 scope_id；第 8 步删去「它同时是接力」；references/cloud-backend.md「1 分工」表同 0040 派生视图（位置：cli/gherkai_cli/skills/gherkai/SKILL.md 与 references/；依据：0043 决策五骨架 5、8；0040 决策 3）
- 评测 fixture 随实装重录：文件集改为 run_meta.json、run_state.json、运行态点名的各份判定明细（文件名带保存标识）与被引用的 evidence 和截图；占位符覆盖面里的 report_refs[].ref 落在判定明细上；run_meta 的 steps_dir 由后台推进进程读回（位置：skills/gherkai-evals/fixtures/、skills/gherkai-evals/materialize.py；依据：0043 决策七「fixture 可搬迁契约」）
- 图：docs/diagrams/execution-timeout-chain.json 的「超时处置」「到点处置」随退役词入表改，用 tools/build_diagrams.mjs 重出 SVG 与 HTML、与加表的提交同一提交（位置：如列；依据：0045 决策七；CONTEXT「job 到点停止」）
- CHANGELOG 未发行节：讲 status --wait 接力、到期记 error、中断记 aborted 的条目直接改写为新行为，不写对照（这些条目描述的旧行为是本版未发行期间才加的，从来没有发行过，使用者手上没有它们，所以不能拿来当对照基准。和已发行版本行为相比的「此前……」照常保留，例如后台 run 超时原先记 engine_error 那一句）；另在 `[Unreleased]` 里提一句 run 的推进、处置与状态取法这一部分做了重构，升级与迁移的细节不写（owner 2026-11-18）（位置：CHANGELOG.md `[Unreleased]`；依据：本文「owner 定的写回口径」）
- CHANGELOG 未发行节的隧道条目随隧道实装批改写为新行为，不写对照。第一项：讲 `submit --backend cloud --expose-local` 的 `--tunnel-ttl` 默认值的那一条（按各 job 墙钟预算之和加 900 秒、再加每个 job 210 秒，链到 local-app-testing.md「存活时间上限」一节）删去，`--tunnel-ttl` 不再提供（`gherkai.toml` 的 `tunnel-ttl` 同样去掉）。第二项：改写为新行为，要点是隧道建在本机持有隧道的进程里（前台 `run` 的 CLI 进程、本机 `submit` 的后台推进进程、云端 `submit` 的本机守护进程），用 ngrok 官方的 Python SDK，不再需要 ngrok 可执行文件，使用者安装 `gherkai[tunnel]`，令牌只从环境变量 `NGROK_AUTHTOKEN` 读取；云端 `submit` 的守护进程在 run 到终态或到运行期限加 300 秒时退出，公网入口在同一时刻由边缘拒绝访问。第三项：同一节里讲「后台进程还没接管就失败时隧道立即拆掉」的那一条按新的宿主次序核对，改写或删去。（位置：CHANGELOG.md `[Unreleased]`；依据：0035 决策 1「前置条件」、决策 3「云端 `submit`」与「边缘到点拒绝」、被拒方案「保留 `--tunnel-ttl`，只允许调小」；0037 决策 2c）
- docs/internals 里讲隧道的三处随隧道实装批同一提交改：
    - artifacts-and-evidence.md 产物表里 `tunnel.json` 一行（「隧道收尾凭据（pid）」，仅 local `submit` 且带 `--expose-local`）删去，不再有这个文件；
    - verdict-model.md 的 `TERMINAL_STATUSES` 一行里，「隧道守护的拆除判据（`runtime/gherkai_runtime/tunnel_host.py`：读到终态即提前拆除，否则等满 TTL）」改为隧道守护进程的退出判据：守护进程轮询 run 的状态，到终态或到运行期限加 300 秒时关闭会话、退出；
    - execution-and-reconciliation.md 4a 节流程块的首行（「submit:plan → 落 definition + 全 pending 初始态 → fork per-run 推进进程」）改成新次序：submit 做完计划与补全运行定义，以新会话启动后台推进进程，经标准输入交给它建 run 所需的输入，另给一条回报管道；后台推进进程依次取创建时刻、起隧道、生成运行定义、建 run 并取锁、建事件库，然后回报，再推进。

    （位置：如列。依据：0035 决策 3 的「寿命」一条、表里「云端 `submit`」一行与「本机 `submit`」一条；0034「local（对称，无 ECS/Lambda）」流程块；0031 决定一·补「终态有正向真源」一条的消费方清单）
- 用户指南 local-app-testing.md 按 0035 的隧道新做法改（隧道建在宿主进程里、用 ngrok 官方 Python SDK，没有独立的代理进程、隧道记录与 --tunnel-ttl），与隧道的实装同一提交，逐处如下：
    ①「前置：ngrok 与 authtoken」一节：去掉安装 ngrok 与 `ngrok config add-authtoken`，改为可选依赖 `gherkai[tunnel]` 加环境变量 `NGROK_AUTHTOKEN`（0035 决策 1「前置条件」）。
    ②「工作方式」的隧道拓扑图：改图源 docs/diagrams/local-app-testing-tunnel-topology.json 里的「隧道进程」节点及「命令行到隧道进程那条边只表示起进程」一类的图注，按隧道在宿主进程里、没有独立进程来写；改完用 tools/build_diagrams.mjs 重出 SVG 与 HTML，图源与产物在同一提交。
    ③「隧道的持有进程与拆除时机」一节的表：删去 submit 一行的「隧道进程号记在 `<report-dir>/<run_id>/tunnel.json`」与「由 `gherkai status <run_id> --wait` 接力拆」，删去云端一行的「到存活时间上限也拆」；何时消失按 0035 决策 3「寿命」与「云端 submit」一条里「守护进程轮询 run 的状态」那一句来写。
    ④「存活时间上限：`--tunnel-ttl S`」一节整节删去（0035 被拒方案「保留 --tunnel-ttl，只允许调小」）。
    ⑤「安全」一节分三处：「令牌与 cookie 随隧道拆除即失效」一句补上到点失效（0035 决策 3「边缘到点拒绝」里「它给出什么、不给什么」一条）；「隧道进程是本机上一个可见的独立进程」一条改为 0035 决策 3「寿命」一条的首句，kill -9 与「在进程列表里找到 ngrok 结束它」删去；「仍是明文的」清单里「本机系统临时目录下的隧道流量策略文件 gherkai-tunnel-policy-*.yml」一项连同它的残留说明删去（策略在内存里交给 SDK、不落盘，0035 决策 1「公网地址是 SDK 调用的返回值」）。
    ⑥「限制」一节分三处：「被测应用收到的 Host 头是隧道分配的 ngrok 域名」一条里的「固定开发域名」「不随 run 变化」按账号分开写，新注册的账号落在 ngrok-free.dev 下的一个固定域名上、停掉再起不变，较早注册的账号每次启动的地址不同（*.ngrok-free.app）；新增「同一个账号同一时间只有一条隧道在线」一条，照 0035「边界与不变量」中那一条的原句和它指向的决策 1 第 3 种说法写，不另作概括；「隧道中断后不会自动重连」一条改写，不写成无条件的「不会」，依据是 0035 决策 1「实测依据」里「宿主被暂停（SIGSTOP）45 秒」一条（恢复后 2 秒内重新在线），以及「没有核过的」一条中的宿主断网之后重连。
    ⑦「常见故障」：开头「ngrok 没装、authtoken 没配这两类报错」一句按新前置改；表中两行的 --tunnel-ttl 删去；「submit 打印「隧道已拆除（本机的被测应用不再对外暴露）」」一行删去；「确认隧道进程仍在后重新提交」随之改写，因为没有单独的隧道进程。
    ⑧「起隧道失败时，报错只附 ngrok 日志的尾部」一段（含系统临时目录里 gherkai-tunnel-*.log 的说明）改为 0035 决策 1「启动失败的说法按原因分」的四种说法。
    [0013](./0013-mobile-devices-implementation.md)「documenting 清单」下「既有用户文档的触点」里 local-app-testing.md 一条讲流量策略规则条数的那一句已按新设计改过（产品的策略是 5 条规则；较早注册的账号每个策略至多 5 条、已经用满，新注册的账号上六条也能建成），补「限制」一节时照它写。
- 用户指南与 README 里讲隧道的几处，与隧道的实装批同一提交改：
    - running-and-results.md：「同一目录下的 events.db」一段删去「用了 --expose-local 时另有隧道记录 tunnel.json」；命令表 `gherkai submit <feature...>` 一行与选项表 `--expose-local ORIGIN` 一行删去 `--tunnel-ttl`；退出码表 submit 一行（「提交成功了吗」）补上本机后台的一种情形：后台推进进程在回报之前退出时，submit 以退出码 2 结束，run 可能已经建成而没有推进器，可以用 `gherkai settle-runs` 记为已结束；讲 reconcile.log 的地方写明，后台推进进程回报之前的输出接在 submit 的标准错误上，回报之后写进 run 目录里的 reconcile.log。
    - configuration.md：`[common]` 一行删去 `tunnel-ttl`；`NGROK_AUTHTOKEN` 一行删去「也可以改用 `ngrok config add-authtoken <token>` 写进 ngrok 自己的配置文件」（令牌只取这个环境变量）；`--tunnel {ngrok}` 一行删去「存活时间上限 `--tunnel-ttl` 只有 submit 有」；「隧道的前置、限制与存活时间见」一句删去「存活时间」。
    - troubleshooting.md：「隧道（--expose-local）」一节的症状表，「找不到 ngrok 可执行文件」与「ngrok 隧道未就绪」两行改为四种启动失败的说法，处理办法里不再有 `ngrok config add-authtoken`；「地址已在线」一行的处理办法照第 3 种说法写，不另作概括。「gherkai doctor 不查隧道前置」一句照旧成立，因为 doctor 不查 ngrok。
    - getting-started.md：依赖表的 ngrok 一行（「可执行文件在 PATH 上 + authtoken」）改为可选依赖 `gherkai[tunnel]` 加环境变量 `NGROK_AUTHTOKEN`，不再要求 ngrok 可执行文件；角色表与安装命令（含 `uvx --from 'gherkai[local]'` 那一行）写明用 `--expose-local` 时另装 `[tunnel]`。根 README.md 与 cli/README.md 的安装命令块同样写明；runtime/README.md 的安装命令块（`uv add 'gherkai-runtime[aws]'` 所在的那一块）加上 `gherkai-runtime[tunnel]`。
    （位置：docs/user-guide/running-and-results.md、configuration.md、troubleshooting.md、getting-started.md、README.md、cli/README.md、runtime/README.md；依据：0035 决策 1「前置条件」与「启动失败的说法按原因分」；0035 决策 3「三种组合的宿主与次序」本机 submit 下「输出」与「后台推进进程在回报之前退出」两条；0035 被拒方案「保留 --tunnel-ttl，只允许调小」；0037 决策 2c「[tunnel] 的语义」；0053「配置文件也不收凭证与密钥」）
- 技术文档里讲隧道的几处，随隧道改为宿主进程里的 SDK 会话那一批实装同一提交改（依据：0035 决策 1「公网地址是 SDK 调用的返回值」、决策 3「寿命」与「云端 `submit`」；0051 决策 13「边缘策略」；0054 决策二「尾段与余量是预算的取值」）：
    - runtime/DEVELOPMENT.md：
      - `detached.py` 一条：删去「隧道事实文件的读写」。本机不再有 `tunnel.json`。
      - `deadline.py` 一条：删去「与 `tunnel_host.CLOUD_PER_JOB_MARGIN_S` 同值」。云端尾段 210 秒的组成见 0054 决策二。
      - `tunnel.py` 一条：「启动 / 拆除 ngrok」改为在宿主进程里经 SDK 建隧道；「渲染四条规则的流量策略」改为生成 5 条规则的策略（最前面一条是到点拒绝），在内存里交给 SDK、不落盘；删去「按 pid 跨进程收尾」。
      - `tunnel_host.py` 一条：删去「cloud submit 守护进程的轮询循环与其 TTL 算法」及括注里的 `compute_watch_ttl_s`、`CLOUD_STARTUP_MARGIN_S`（900 秒）、`CLOUD_PER_JOB_MARGIN_S`（210 秒）与它的组成；守护进程到 run 终态或运行期限加 300 秒时退出，按这一点改写。
    - cli/DEVELOPMENT.md：架构决策列表 0035 一行的括注删去「谁负责拆、TTL 算法」。
- agent skill 里讲隧道的各处按 ADR 0035 改写，与用户指南的同类改写在同一个实装批里做（位置：cli/gherkai_cli/skills/gherkai/）：
    - SKILL.md：第 3 节「被测应用在本机 / 内网时」的前置改为可选依赖 `gherkai[tunnel]` 与环境变量 `NGROK_AUTHTOKEN`，加上公网入口到运行期限加 300 秒在边缘关闭（依据 ADR 0043 决策五骨架第 3 条、0035 决策 3「边缘到点拒绝」）；「`--tunnel-ttl`（仅 `submit`）」一条与第 7 节选项表的「仅 `submit` | `--tunnel-ttl`」一行删去（0035 被拒方案「保留 `--tunnel-ttl`，只允许调小」）。
    - references/setup-and-diagnosis.md 第 1 节「装什么」：表里写明用 `--expose-local` 时另装 `[tunnel]`（0037 决策 2c）。
    - 同一文件第 5 节：「ngrok 可执行文件装好且在 PATH 上」一条删去。「ngrok 账号的 authtoken」只留环境变量 `NGROK_AUTHTOKEN`，不再提 `ngrok config add-authtoken` 和配置文件（0035 决策 1「前置条件」）。「被测应用收到的 Host 头」一条里「每个账号分配一个固定的开发域名」改为按账号区分：新注册的账号是 `ngrok-free.dev` 下的固定域名，较早注册的账号每次启动地址不同（0035 决策 2「plan 输出替换前的原始地址」）。「隧道的持有与拆除」删去「`--tunnel-ttl` 到点即拆」以及 `kill -9` 之后「到进程列表里结束 ngrok」，宿主怎样退出隧道都随之消失（0035 决策 3「寿命」）。「隧道断了不自动重连」按用户指南同一条的改法改写，不写成无条件，依据是 0035 决策 1「实测依据」里「宿主被暂停（SIGSTOP）45 秒」恢复后重新在线的实测，以及「没有核过的」一条里的宿主断网之后重连。「排障入口」删去本机 `submit` 的隧道进程号与 tunnel.json、ngrok 自己的日志、「隧道已拆除」一句。
    - 同一文件第 7 节症状表：「`--expose-local` 起隧道失败」一行按 0035 决策 1「启动失败的说法按原因分」的四种说法写；地址已在线（ERR_NGROK_334）时的处理办法照第 3 种说法写，不另作概括。「run 中途开始每条 scenario 都导航失败」一行的原因和处理两栏删去 `--tunnel-ttl`，原因一栏按 0035「边界与不变量」的「宿主被暂停」「云端的守护进程没了」两条写。
    - references/cloud-backend.md：「`submit --backend cloud --expose-local <原始 origin>` 时隧道由本机的守护进程持有」一段里讲 `--tunnel-ttl S` 兜底 TTL 的那一句删去；守护进程的存活上限由运行期限推出（0035 决策 3「云端 `submit`」）。
    - 这几处改动是评测的打分依据，skills/gherkai-evals/evals.json 里 `expose-local-app` 一条的评测要求与 expected_output 要一起改，见本文已登记的评测条目。
- agent skill 的评测资产随隧道的行为文档同一批改（位置：skills/gherkai-evals/evals.json 中 slug 为 expose-local-app 的一条；依据：0043 决策五骨架第 3 条「被测应用在本机时」；0035 决策 1「前置条件」与被拒方案「保留 `--tunnel-ttl`，只允许调小」）：
    - expectations 里以「前置两条都提到」开头的一条，与 expected_output 里的「前置：本机装好 ngrok 且在 PATH、配好 authtoken（ngrok config add-authtoken 或 NGROK_AUTHTOKEN 任一）」，改为前置是可选依赖 `gherkai[tunnel]` 与环境变量 `NGROK_AUTHTOKEN`，不再要求装 ngrok 可执行文件，也不再用 `ngrok config add-authtoken`。
    - expectations 里以「提到 --tunnel-ttl 调小会在 run 未完时无条件拆隧道」开头的一条整条删去；expected_output 里「--tunnel-ttl 调小会提前拆隧道」一句删去。
    - 「submit 后隧道由本机进程持有、本机须开机联网到终态」一句与对应的评测要求不变。
    - 可以另加一条评测要求：说明公网入口到点在 ngrok 边缘关闭（0035 决策 3「边缘到点拒绝」），是否加由实装批定。
    - 同一文件 eval 22 的评测要求里「域名每个 run 都会换」一句，按 0035 决策 2「`plan` 输出替换前的原始地址」一条（地址随账号不同）一并核对。
    - 改过评测要求之后，在 evals.json 的 notes 里记下这一轮尺子的改动。
- docs/user-guide/cloud-backend.md「团队成员需要的最小云端权限」一节也是 0040 决策 3 与 0033 编排进程角色的派生视图（已改为云端只有一级）。从「submit + status」一级里删去「调用 `<prefix>kicker` Lambda」，保留提交前检查用的 lambda:GetFunction。加上 run 处置所需的权限：runs 表的条件写，报告桶的 s3:GetObject（读卸载到 S3 的运行定义正文和被点名的判定明细），以及报告前缀的 s3:PutObject（写报告）；settle-runs 不给 run_id 时，另需 list-runs 的两项。结尾的推论改成云端执行不需要任何 ECS 写权限。依据：0040 决策 3；0033「资源清单」末段的编排进程角色；0054 决策八。

#### 收尾

- code 跟上之后，删去各篇 Status 头末尾说「这一篇描述的设计有一部分尚未实装，code 跟上之前实际行为以 code 为准」的那一句。各篇写法略有出入：0034 作「本篇」，多数篇在「之前」后面带逗号，所以按「尚未实装」定位。篇目以执行时在 docs/adr/ 全部 Status 头里检索「尚未实装」的结果为准，不靠下面的枚举。写本条时命中 20 篇：0011、0016、0024、0026、0027、0028、0030、0031、0033、0034、0035、0037、0038、0040、0041、0042、0043、0051、0053、0054。其中 0011 与 0051 的这一句是隧道写回时加上的，0051 决策 13 与 0011 里隧道相关的条文实装之后才能删。
- 实装全部完成、删 Status 头那一句之前，对 code、测试、docs/internals、docs/user-guide、各包 README 与 DEVELOPMENT、agent skill 发行源与评测材料（skills/gherkai-evals）、docs/diagrams 图源、CHANGELOG 未发行节做一次旧说法的残留检索，检索词如下：
    - 本机接力、接力、兜底/接力、三触发源、三个推进触发源、推进的三个触发源
    - 混合版本、真值日志、物化、四种组合
    - run --backend cloud、云端同步、云端前台
    - 超时处置、到点处置、推进方、发起进程
    - try_finalize、run_verdict、RunVerdict、load_all、判定真值唯一权威、jobs/*.json
    - 以认领计数（claim_count、expected_claim_count）作写条件的说法

    逐处判断是改成现行说法还是删去。「超时处置」「到点处置」「接力推进」进 RETIRED_TERMS 之后由测试守，其余各词没有测试守，只能靠这次检索。claim_count 作诊断键、launcher 一类类名、「正交」一词另有合法用法，要按语境判断，不按字面判。「物化」也可能有与旧设计无关的用法，同样按语境判断。

    豁免：已发行版本的 CHANGELOG 条目，以及 ADR 里保留原文的实测记录。ADR 里讲 run --backend cloud 的历史实测与发版验证记录保留原文，删去前台云端执行时不改写；全仓 grep run --backend cloud 时，这几处命中不算漏改。它们是：0037「施工前现状实测（历史快照）」表里「装进干净 venv 后 submit --backend cloud」一行；0042「验证」节里云端后端那一条（推两引擎 dev worker 镜像为 variant base 后 run --backend cloud 的故意失败断言）；0043「验证」节的 v1.4.3 发版验证记录；0051「实测依据」表里「真部署后的 task role 策略」一行。0041 决策二里 run --backend cloud --quiet 的那句执行记录与决策正文写在一起，已随「这个组合以退出码 2 结束」删去，不再补回。0016「版本切分」的 v1.2.0 行已经不含「接力收集」，「接力推进」进退役词表时，这一行不需要豁免。

    指针编号类的旧号（「0054 决策三末段」、0054 实测项旧号等）已在写回时改完，由上面的条名差集覆盖，不进这张表。

#### 核对时补上的条目

- cli/gherkai_cli/__main__.py `_submit_cloud` 里 `detached=True` 的注释（「kicker filter 认它冷启动」）随 kicker 的流过滤改为标记只供 `list-runs --json` 的 detached 键（依据：0034 端到端 cloud 1b）
- 待定：run 两次定时触发的名字形态与 IAM 资源域定下之后，按新名字重核 0033「两层命名」节的 prefix 长度上限与 `prefix_max_len()`（取各名字空间里最紧的一个；超过 64 字符时 kicker 处理 STATE 新建的调用会失败、由流反复重试），并补齐 0033 资源清单 15 与 0054 决策九末段的登记（位置：runtime/gherkai_runtime/names.py `prefix_max_len`；deploy_aws/gherkai_deploy_aws/stack.py `_reconcile_lambdas`；依据：0033 资源清单 15 与「两层命名」；0054 决策九）
- 待定：云端处置方按 CLI 的 `--report-dir` 读被点名的明细、写报告，推进器 Lambda 用 `REPORT_DIR`，两者只在 submit 的 preflight 比对过；处置一侧是否也比对报告前缀，交 owner 定（位置：处置的 runtime 实现；cli/gherkai_cli/__main__.py settle-runs 与 `_status_cloud`；依据：0054 决策七、八；0033 编排进程角色段）
- 删 Status 头那句时一并核对 0027「现在做 / 留口子」的「本 ADR 上述全部决策均已实装」与 0041 决策七开头的「本条已实装」：code 跟上之前它们与 Status 头相抵，跟上之后才成立（位置：docs/adr/0027-runreport-aggregation-index.md「现在做」；docs/adr/0041-agent-facing-cli-affordances.md 决策七）
- 另随实装校准：docs/internals/verdict-model.md（run 级取法、job 级 skipped 来自结束写）、docs/user-guide/troubleshooting.md 与 local-app-testing.md（到期与接力；隧道的部分见上「隧道（0035）与两种 `submit` 的新流程」一块与「行为文档」块里讲隧道的各条）、docs/internals/deterministic-step-lifecycle.md（宿主）、docs/user-guide/running-and-results.md（接力与前台 run 提示）（依据：0031 决定三；0034 被拒方案「本机接力，及其改法」）
- docs/internals/verdict-model.md 与 docs/internals/execution-and-reconciliation.md 里有两处指针所指的小节已经不在（0031 的「aborted 只认主动中止…不认 timeout」、0054「本机接力的改法」），随这两篇按新行为改写时一并去掉；这类指针用「目标条名在改写之前的 ADR 里有、现在没有」的差集查

#### 写回时留下、实装之前要定的问题

下面各条在写回时没有定，不阻塞另一家模型核落到位；涉及产品取舍的交 owner。上一节「核对时补上的条目」里标「待定」的几条同属此类。

- 本机 run 运行期失败的退出码，0030 决定七写的是「非零」，要定成 1 就要在 0031 决定五写全
- RunPersistence.begin 在 create_run 之前调三个 store 的 preflight，run 只有本机后端之后全是 no-op：begin 里与 Store 端口上的 preflight 保留与否、保留时理由怎么写，要 owner 定，0030 决定七现在只陈述现状
- 0030 决定五「Map 形状下 update_job_state 各 scope 互不干扰」一句与云端记下终态时对 jobs 整体替换有张力，要不要补一句
- 0030 决定六「形态变更」条与 status_group 写入规则里索引迁移、旧版 CLI 写出的记录的叙述，是否按「ADR 不提升级、迁移与版本共存」一并清理
- 0031 决定一「scenario 级 SKIPPED」条列的「scope 级 error 之后因主动中止得出 aborted」按 0034 机制二可能到不了，要不要另行核实
- 同一次前台执行里已过停止启动、又出现 fail-fast 或使用方中断时，结束写取哪一个来路的说明，设计时没有定，0031 决定三「结束写」小节与 0054 决策二都没写
- 0042（第三节标题、决策七的问题段与被拒方案、「不做 / 延后」与重议、云端交付链的实测记录）与 0027 重议条里的 jobs/*.json 还没有逐处判定换成「判定明细」还是作为历史记录保留
- 0033 编排进程角色没有登记 explain 读判定明细与 evidence 所需的 s3:GetObject（0042 决策四写了需要它），要不要补登记
- 只写「ADR 0034」的整篇指针紧邻的描述与 0034 端到端 cloud 1b 相反（ddb.py 模块头与 _state_item 的「kicker 的 Stream filter 认它」、model.py 的 RunMeta、core/tests/test_ddb_run_store.py 的 test_detached_flag_on_state_item，另有 __main__.py 的 _submit_local、_submit_cloud、_render_status，compose.py 的 build_cloud_stores 与 _make_lambda_client，detached.py 的 build_local_reconcile，stack.py 的 _reconcile_lambdas，lambdas/reconciler.py 的 _run_ids_from_runs_stream，cli/tests/test_main.py 的相关用例）：要不要把「指针目标否定紧邻描述就去掉条名」推广到整篇指针、现在删去编号，还是留给实装批连同描述一起改
- core/tests/test_conditional_writes.py 模块头的「ADR 0054 决策二/五」在该文件里已没有决策二的依据，是保留（实装改为写入序号条件之后又对得上）还是现在去掉「决策二」
- 退役词表加哪些：owner 定的是「接力推进」「超时处置」「到点处置」进表、「推进方」只进 _Avoid_；新词条 _Avoid_ 里另有「到期收尾」「收尾写」「发起进程标识」「进程核对」「遗留 run 收尾」，写回计划曾把它们连同「推进方」都列为要加，要主会话定
- 上面「结束写取哪一个来路」一条的相关问题：0054 决策二、0026「起 worker 与重试之前的检查」与 0028「重试之前的检查」三处写的检查次序（已过停止启动的时刻、已发现 run 被别处结束、已因 fail-fast 或使用方中断而中止，最后认领或读一次 run 状态）眼下没有写为什么这样排。旧理由「不能因此把未启动的 job 改记为 skipped」随未启动的 job 改由结束写记 skipped 而删去；现在只有最后一步的位置有依据（0054 决策五：认领紧贴起 worker）。这个次序仍决定重试之前注明的原因（取最先命中的一条），也可能决定结束写的来路。定来路时一并补上次序的依据，并看看等待重试的 job 按固定次序取原因、执行中的 job 按最先登记取原因，这两种取法要不要统一。
- 0016 决策 C「证据边界」一条：profile-only 的那次真实执行走的是 run --backend cloud，命令行组合根经 boto3.Session 从 profile config 解析出 region（--region、AWS_REGION、AWS_DEFAULT_REGION 都没有给），再经 RunTask 注入 Fargate 容器，两个引擎的确定性与 AI 场景全部通过，没有出现 InvalidRegionError 或 NoRegionError。写回时这一句改成了不提载体的说法（store 与 worker 同区、worker 消费注入的 region），可是现行设计里 Fargate 的 region 取部署所在区域，命令行解析出的 region 只交给 store 与 subprocess worker，而 subprocess 这一路没有真跑过。要 owner 在两种做法里选一种：一是恢复原句，作为实测快照保留，另加一句现状（profile config 回落现在只影响 store 与 subprocess worker，后者未经真跑，边界要重新判断）；二是保留现在的写法，但写明证据来自 Fargate 那一路，并说清 subprocess 那一路是否要补一次真跑。ADR 0031「终态有正向真源」一条恢复事故原句是同类的前例。
- doctor 的报告目录一项，项名 report_dir.filesystem（report_dir 组）是写回时执笔自定的，owner 没有确认过。ADR 0041 决策四已按这个名字写定：本机后端必修，只读，不碰锁，--backend cloud 时不出这一行；doctor 子命令的 --report-dir 不再标为只用于云端。这个名字会成为 doctor --json 里 name 字段的取值，并要写进契约页 doctor 一节的项名表。实装之前要确认；改名时同时改 0041 决策四与上面「查看命令与机读输出」里的 doctor 一条。
- 用户文档里隧道宿主的叫法：ADR 0035 决策 3 的表头和 0016 用「隧道宿主」；用户指南 local-app-testing.md 的小节名是「隧道的持有进程与拆除时机」，表头是「持有隧道的进程」；用户文档其余各处、agent skill 都不用「宿主」，CONTEXT.md 没有为它立条。改 local-app-testing.md 的拆除时机表时（三行改为前台 run 的 CLI 进程、本机 submit 的后台推进进程、云端 submit 的本机隧道守护进程，「拆除时机」一列改为隧道何时消失），要一并定下用户文档用哪种叫法，同一种叫法要用到 running-and-results.md、troubleshooting.md 和 skill 的 references/setup-and-diagnosis.md。
    - 缺省：用户文档沿用「持有隧道的进程」，不进词表；「隧道宿主」只在 ADR 里用。
- 下面「删除过程文档之前找到、ADR 里还没有的内容」一块里另有两个待定：提示里的 `gherkai status` 命令是否带上显式给出的 `--config`（「提示里的 `gherkai status` 命令怎样拼」一条）；运行态解析不了时 `status` 与 `status --wait` 各怎样结束（「提交记录或运行态本身解析不了时的出口」一条）

#### 删除过程文档之前找到、ADR 里还没有的内容

删除对齐记录、设计稿与第 4 步的待批报告之前，逐条核过其中的有效信息别处有没有。下面各条在现在的设计下仍然适用，而各篇 ADR 里还没有或写得不全：前两条出自与 owner 的对齐记录，其余出自第 4 步的设计补充（当时已经闭合，或经 owner 2026-11-15 裁定）。排实装分批时先定哪些写进 ADR（写进去的过独立复核），其余作为所在实装批的线索。各条开头括号里的「建议落点」是审计时给的建议，还没有执行：写着要放进本文别的块的实装条目与待定问题没有另搬，都留在这一块里，分批时从这里取。各条的理由凡不是 owner 原话的，写回 ADR 之前要再核一遍。

- **run 目录不过边界检查时 `status --wait` 只读地等到终态、不处置：owner 2026-11-18 不取，ADR 里没有记成被拒方案**（建议落点：ADR 0054「被拒方案」，放在「macOS 只看本机标志」一条之后。条文里的理由是从 0054 决策四、八推出来的，不是 owner 给的原话，提交之前请 owner 确认或改写。owner 一时定不下来时，先把这条连同「理由待 owner 确认」记进 docs/journey/0018「写回时留下、实装之前要定的问题」。）
  - **run 目录不过边界检查时 `status --wait` 只读地等到终态、不处置**（本机后端，run 未结束而 run 目录的文件系统类型不在清单里或判断不了）：这样的目录上锁可能互不可见，运行态的写可能互相覆盖（决策四「文件锁有效」一条），所以既判断不了管它的进程还在不在，也不能安全地做处置的条件写。同一个 run 在 `settle-runs` 那里同样被跳过（`unsupported_filesystem`，决策八），本机又没有常驻的处置方，管它的进程不在了时没有任何一方会把它带到终态，只读地等可能永远不返回。现在的做法：run 已是终态时直接返回、不检查；未结束时先检查，不过即以退出码 2 结束，说明原因、检测到的类型与清单，与 `run`、本机 `submit` 在同样的目录上拒绝建 run 是同一种表现。
- **macOS 的 Docker Desktop 取证里 ADR 没有带上的事实**（建议落点：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md 决策四「产品边界」一条（第 108 行）的 Docker Desktop 括注；锁实验那一项补进「实测项」第 13 条（第 13 条讲锁行为、已列 btrfs 子卷，比讲边界检查的第 14 条合适））
  0054 决策四「产品边界」一条里 Docker Desktop 的括注改为：（实测 macOS 的 Docker Desktop：宿主目录在容器里是 `fakeowner` 类型、被拒，宿主一侧是 APFS、放行，两侧的目录锁与文件锁两个方向都互不阻挡；命名卷在容器里的类型是 `ext4`、检查放行，命名卷上的读写都在虚拟机的同一个内核里，按本条属于边界之内，命名卷上的锁行为未照决策三理由逐项核过）

  实测项 13 末尾补一句：Docker Desktop 命名卷上（两个容器共用一个卷）照做决策三理由的各项。
- **提示里的 `gherkai status` 命令怎样拼（owner 2026-11-15 同意带 `--ddb-table` 与 `--region`、不带 `--profile`）**（建议落点：规则写进 docs/adr/0042-step-evidence-and-explain.md 决策四「未终态的 run」段，紧接「提示里给出可原样跑通的整条命令」那一句，补上 --ddb-table、--region，以及「不带 --profile、以同一份身份配置为前提、各处提示用同一个拼法」。也可以在 0041 决策六加一条「提示里的命令」作为权威，0042 改为指过去，二者选一处。  docs/adr/0054-run-deadline-lifetime-lock-and-settling.md 决策五末条（「说明与判定明细的位置写在 stderr」之后）补一句「说明里给出查看这条记录的 gherkai status 命令（写法见 0042 决策四）」。  三条实装条目记进 docs/journey/0018-run-ownership-adr-writeback-plan.md「实装」的「查看命令与机读输出」块：_status_cmd、加回 status 命令、running-and-results.md 退出码表。）
  规则（写进 ADR）：
  CLI 打给使用者照抄执行的 gherkai status 命令，用于 submit、status、explain 的提示，以及 run 在本次执行结束之前已被别处结束时的说明，按以下方式拼：
  - 本机后端带 --report-dir。
  - 云端后端带 --backend cloud --prefix <已解析的 prefix>，另带本次命令行上显式给出的 --ddb-table 与 --region。
  - 不带 --profile，因为身份信息不打到终端。
  - 来自项目配置文件或环境变量的值不另带：在同一目录、同一环境下照抄，会取到同样的值。

  所以「提示里的命令可原样跑通」以同一份身份配置（同一个 AWS profile 或凭证环境）为前提，身份配置不同时，照抄的命令可能查到别的后端或查不到。各处提示用同一个拼法。

  另外，run 发现这个 run 在本次执行结束之前已被别处记为已结束时，stderr 上的说明里给出查看这条记录的 gherkai status 命令（写法同上）。run 只走本机后端，这条命令带 --report-dir 即可。

  实装条目（写进 journey 0018「实装」的「查看命令与机读输出」块）：
  - 改 cli/gherkai_cli/__main__.py 的 _status_cmd，带上显式给出的 --ddb-table、--region，不带 --profile；submit、status --wait、explain 的提示都经它；补测试。
  - _ended_elsewhere_notice 的说明里加回查看这条记录的 status 命令。
  - docs/user-guide/running-and-results.md 退出码表的 run 行补上这一情形：run 已被别处记为已结束时，stdout 为空，退出码 1，处理过使用方中断时按信号取 130 或 143。
  - 待 owner 定：显式给出的 --config 是否也要带上。
- **agent 可以自己执行 `settle-runs`（owner 2026-11-15 同意）**（建议落点：docs/adr/0043-agent-skill-for-driving-gherkai.md 决策五：任务域 A 的命令列表，以及骨架第 8 条「退出码分流」。skill 正文怎么写留给 skill 打磨批去做，journey 0013「skill 打磨批」一条已经登记了「`settle-runs` 放在哪里教」，可以在那一条补一个指向 0043 决策五的指针。）
  （加在 0043 决策五：任务域 A 的命令列表里加 `settle-runs`；骨架第 8 条「退出码分流」后面接下面这段）`settle-runs` 只表示做成没做成：执行完成为 0（含一个都没处理，被跳过的 run 不改变退出码）；用法错误、后端不可达、给出的 run 不存在、报告目录不过边界检查、写入失败为 2，权威见 0031 决定五。哪些 run 被处置了、为什么跳过，看 `--json` 的 `runs[].outcome` 与 `reason`。agent 可以自己执行 `settle-runs`，不必先请使用者确认，但要先用 `--dry-run` 看会处置哪些。这样做的依据是：判定只靠记录与生命期锁，不靠使用者事后担保，拿不准就跳过（0054 决策一、八），所以它不会结束一个推进器还在管、又没过期限加 300 秒的 run。用到它的场合：`list-runs` 或不带 `--wait` 的 `status` 提示「已超过允许运行的时间（可用 settle-runs 或 status --wait 记为已结束）」；清单里有长期不结束、也没有人在等的 run。正在等待的 `status --wait` 遇到条件成立会自己处置，不需要另外执行 `settle-runs`。（owner 于 2026-11-15 同意由 agent 自己执行。）
- **提交记录或运行态本身解析不了时的出口**（建议落点：按四处分放： - 第一段进 docs/adr/0037-distribution-and-packaging.md 决策 7「definition 结构版本」段的「CLI 读端」那一句。 - 第二段进 docs/adr/0031-job-lifecycle-states-and-severity.md 决定五「status」条，以及 docs/adr/0054-run-deadline-lifetime-lock-and-settling.md 决策八「等待中的 status --wait」条。 - 第三段进 docs/journey/0018-run-ownership-adr-writeback-plan.md「实装」的「查看命令与机读输出」块。 - 第四段进 0018「写回时留下、实装之前要定的问题」。  ADR 两处要等 owner 对第四段拍板之后再改；拍板之前只写 0018 的两处。）
  一、给 0037 决策 7「definition 结构版本」段「CLI 读端」那一句补半句：
  提交记录本身解析不了时（本机的 run_meta.json 不是合法的 JSON、或顶层不是对象；云端读到的头部属性形状不对），status 与 explain 同样以退出码 2 结束，并说明这条提交记录读不出。它与结构版本不认、定义违约走同一个出口，不让解析异常的回溯出现在用户终端。

  二、给 0031 决定五「status」条与 0054 决策八「等待中的 status --wait」条各补一句：
  运行态本身解析不了时（本机的 run_state.json 不是合法的 JSON、不是对象、形态违约，或状态值本版本不认识），不带 --wait 的 status 以退出码 2 结束，并说明这条记录读不出（与 list-runs 把它列为无法读取、提示用 status 查看相衔接）。带 --wait 的 status 只等待并说明原因，不处置。这里按 0054 现行的写法，它取代了「两者都以退出码 2 结束、不进入等待」的旧做法；若 owner 不认可这一取代，改回以退出码 2 结束。

  三、给 0018「实装」的「查看命令与机读输出」块加一条：
  本机 status 与 explain 在提交记录头部读取（LocalRunStore.peek_definition_header）和运行态读取（load_run_state）上，捕获 JSON 解析失败与顶层不是对象这两种情形，以退出码 2 结束并给出一句产品语言的说明；_definition_header_gate 与 _cmd_status_body 现在只接 DefinitionContractError，两种情形都是未捕获的异常。带 --wait 的那一支按 0054 决策八只等待并说明原因。补一条测试：损坏的 run_meta.json 与损坏的 run_state.json 各一例，断言退出码 2、终端没有回溯。

  四、给 0018「写回时留下、实装之前要定的问题」加一条：
  运行态解析不了的 run，不带 --wait 的 status 是以退出码 2 结束，还是照常显示能读出的部分并说明？带 --wait 的 status 是按 0054 决策八只等待并说明原因，还是像原先那样以退出码 2 结束、不进入等待？0054 的「只等待」是否有意取代了原来的退出码 2，需要 owner 确认。
- **存储访问失败不算「运行态读不出」**（建议落点：0054 决策六末条（「运行态本身读不出」一句后面补上读不出的定义，写明不含存储访问失败）与决策八「等待中的 status --wait」条（补上结束写失败为 2）；0031 决定五「status --wait」条加「处置的结束写失败、后端访问失败为 2」，并在「退出码 2」条里登记这一类；实装条目进 journey 0018「实装」一节的「run 处置：settle-runs 与 status --wait」块）
  处置判定里的「运行态读不出」只指记录在、内容却解析不了，或者形态不对。存储访问本身失败不算读不出，按读不到这个后端处理，以退出码 2 结束并说明原因，不进入等待，也不记为 unreadable。存储访问失败包括：权限不足，凭证或 region 解析失败，网络失败（照既有的重试做完之后仍失败）。这条对 status --wait 与 settle-runs 都适用，判据与 list-runs 的「读不到」一致（0041 决策七）。同一类情形：status --wait 处置条件成立、做结束写时，这次写失败了（典型是云端使用者只有 runs 表的读权限，没有条件写权限），按后端访问失败处理，以退出码 2 结束并说明原因，不继续等待；settle-runs 的「写入失败为 2」也是这样。条件写因为别处先写成而被挡下，不算写失败：settle-runs 记 already_finished，status --wait 读到终态后照常渲染并给终态的退出码。
- **`settle-runs --json` 的 `cli_version` 与被使用方中断时的退出码**（建议落点：首选放进 docs/journey/0018-run-ownership-adr-writeback-plan.md「实装」节「run 处置：settle-runs 与 status --wait」块的 settle-runs 条，接在「--json 给落点字段（同 list-runs）、dry_run 与 runs[]」和退出码那一句之后，随实装一起落地，并写进机读契约页。如果要提升为 ADR：顶层的 cli_version 接到 ADR 0054 决策八 settle-runs 条的 --json 描述后面；中断以 130 结束补进 ADR 0031 决定五的 settle-runs 条，写法与 status --wait 条一致。）
  settle-runs 的 --json 顶层除了落点字段（与 list-runs 相同：backend 恒有，本机另带 report_dir，云端另带 prefix、region、ddb_table）和 dry_run，还像 list-runs 一样带 cli_version，表示执行这次命令的 gherkai 版本，恒有，取不到时为 null。runs[] 各项不带写出版本。settle-runs 被使用方中断（Ctrl-C）时，与 status --wait 的惯例相同：打一句说明，以退出码 130 结束，不把回溯打到终端；中断之前已写成的处置保留，再执行一次是安全的，已处置的 run 记为 already_finished。130 不属于这条命令自己的 0 与 2 两种退出码。
- **`list-runs`「已运行」「允许运行至」两列的计时细节**（建议落点：「括注按 deadline_at 本身计」一句进 docs/adr/0041-agent-facing-cli-affordances.md 决策七「人读形态」，紧接「已运行」那一句；两列的取法是实装细节，随「查看命令与机读输出」块里 list-runs 一条的实装落地，不必进 ADR。）
  放进 0041 决策七「人读形态」，接在「『已运行』：……读得到期限时括注还剩多久或已超多久」之后：
  「括注按 deadline_at 本身计，与『允许运行至』一列同一个时刻，不含期限提示所加的 300 秒。」

  放进 journey 0018「实装」下「查看命令与机读输出」块里 list-runs 那一条，作为补充：
  「两列的取法：『已运行』从运行态的 started_at 起算，已结束的 run 取 started_at 到 ended_at；『允许运行至』的表头与『开始（本地）』『结束（本地）』一样注明本地时区；当前时刻每次清单只取一次、各行共用，同一张表里各行的时长、括注与期限提示出自同一个时刻；运行态读不出的行两列都是 -。」
- **`detached` 键在两个后端用同一判据**（建议落点：docs/adr/0041-agent-facing-cli-affordances.md 决策七「机读形态」中「`detached` 是布尔，恒有……」一句之后；实装时对应改 core/gherkai_core/adapters/run_store/ddb.py 的 `is_detached` 与 `list_runs`，把 `bool(...)` 改为 `is True`。）
  `detached` 在两个后端用同一判据：后台执行标记恰为布尔真时为 true；标记不存在，或者是其它取值（数字、字符串等记录损坏的情形），都为 false，不输出 null，这一行也不因此算作无法读取。本机读 `run_state.json` 的顶层键，云端读 STATE 条目的顶层属性，都不按真值判断：按真值判断时，同一个异常取值在本机与云端会得出不同的 `detached`。
- **`status --wait` 的期限只读一次，等待中的说明只打一次**（建议落点：docs/journey/0018-run-ownership-adr-writeback-plan.md「实装」节中「run 处置：settle-runs 与 status --wait」块的第三条（开头是「等待中的 `status --wait`，两个后端、前台与后台的 run 都一样」），作为这一条的补充。）
  期限（deadline_at）在建 run 时写下、之后不变：status --wait 读到合法的期限之后不再重读运行定义，每次轮询只重读运行态并做处置判定；还没读到时（运行定义读不出或期限不合法），下一次轮询再读，不能因为进入等待前那一次读取失败，就放弃按期限处置（云端只有期限这一条处置条件）。等待中的说明（锁不可用的原因、运行态读不出的原因）在第一次遇到时打印一次，之后的轮询原因没变就不重复打印，原因变了再打印一次；锁被持有、云端未过期限加 300 秒时不打印说明。
- **结构版本不认的 run 仍可按锁处置**（建议落点：docs/adr/0054-run-deadline-lifetime-lock-and-settling.md：「被拒方案」节加一条；决策六「可以处置的条件是两者之一」条末的「期限读不出（运行定义读不出……）」括号里补上结构版本不认这一情形。owner 对「结构版本不认也按锁处置」拿不准时，改记进 docs/journey/0018-run-ownership-adr-writeback-plan.md「写回时留下、实装之前要定的问题」。）
  在 0054「被拒方案」加一条：

  - **提交记录的结构版本读不出或不是本版本认的 run 一律不处置**（理由会是：别的版本写下的运行态，形状不保证看得懂）：处置的判定只看生命期锁与期限，结束写只看运行态（0031 决定三「结束写」小节），都不读运行定义的键。运行态解析得了，就是本版本认得它的形状，条件写只改本版本认得的状态字段。本机写回时，运行态里不属于模型的顶层键原样带回（0030 决定四「local 的顶层附加键整体保留」）；云端的写不提及的属性，原样保留。推进器读不到可用的运行定义时，同样以结束写结束这个 run（0037 决策 7），处置方对同一批 run 不另设更严的门槛。一律不动的话，这些 run 在本版本里没有任何一方能结束：`status` 与 `explain` 对它们以退出码 2 结束，等待中的 `status --wait` 走不到处置。结构版本读不出或不认，只使期限读不出，按决策六只剩试拿锁一条。

  另在 0054 决策六「期限读不出」那一句的括号里写明「运行定义读不出」包括哪些情形：提交记录不存在、结构版本读不出或不是本版本认的、定义违约。

#### 建 run 中途被强杀留下的残留（owner 2026-11-19：要清）

现状与 ADR 目标都不清理这类残留。下面是只读摸底的结果与候选做法，设计要写进 ADR 补遗那一批、过复核之后才实装。

本机的候选做法：先在报告目录里用带固定前缀的临时名字建目录并取生命期锁，写好运行定义与运行态之后原子地改名成 run 标识。以 run 标识命名的目录一出现就是完整的 run；残留只会是带临时前缀的目录，试拿得到它的锁（建它的进程已不在）就可以删。已用真实进程核过：目录上的 flock 在目录改名之后仍由原持有者持有，改名之后别的进程按新名字试拿仍被挡住，持有者被 SIGKILL 之后别的进程 20 毫秒内拿到（macOS 的 APFS；Linux 内核 7.0 的 ext4）。清单里其余的文件系统类型、容器与宿主之间的绑定挂载还没有核。

本机一侧摸底的结论（候选做法要动什么、要补的两处、比较过的更简单做法）：

  【与运行态写下之前的交接有没有冲突】
  在 ADR 目标设计里没有冲突：没有哪一步在运行态写下之前就把 run 目录路径交给别的进程或写到别处。
  - 前台 `run`：起隧道在建 run 之前，不碰 run 目录。events.db、worker.log、产物目录、jobs/、报告都在 begin 之后（__main__.py 3023 → 3052/3061/2927）。
  - 本机 `submit`（0035 第 78-79 行）：提交进程只在回报里拿到 run 的标识，回报在建 run 与事件库之后；reconcile.log 在回报之后才写；worker 的 job 输入要等认领之后才产生。
  - 现状 code 的 `_submit_local` 也是 create_run 之后才 Popen，并传出 run_id（1761 → 1786）。
  - 唯一的约束：在进程内、改名之前，凡是按 `root / run_id` 拼路径的写都不能做。SqliteEventLog（sqlite.py 44）、LocalResultStore（40-41）、LocalReportStore（80-81）构造或写入时都会 `mkdir(parents=True, exist_ok=True)`，提前调用会抢先建出以 run_id 命名的目录。所以事件库要么在改名之后建，要么在临时目录里建好再随目录一起改名。

  【要动的 ADR】
  - 0030：决定四第 231 行要改判据与「只有 run_meta.json……照常建」，以及「建 run 的一方在调用 create_run 之前已持有锁」（锁对象变成临时目录）；决定三第 166-167 行的「中间态对读的一方可见」要限定到 DDB。
  - 0054 决策三：第 92 行（打开的是临时目录，改名后仍是同一个打开）；第 94-95 行（「建出 run 目录」改为「建出临时目录并取锁、写完再改名」，括号里那句「试拿方只碰运行态已读得出的目录，这只在 run_id 重复时出现」要重写）；第 97 行（多出对临时目录的试拿）；第 100 行的理由里补上「改名后锁仍在」的实测。
  - 0054 决策四第 109 行：取锁的对象是临时目录；清理方属于取锁或试拿锁的一方，也要做边界检查，现在「其余命令不碰锁，也不查」的名单要相应更新。
  - 0054 决策五第 119 行：「本机要求 run 目录里还没有运行态」改为「改名的目标不存在」。
  - 0054 决策八第 157 行：如果清理放进 settle-runs，要定它的输出形态与 reason。
  - 0054 其它局限第 238 行：写明掉电不在覆盖之内。实测项 14、15、18 要调整，再新增一条「改名与锁」的实测。被拒方案里加一条护栏，见下「更简单的做法」。
  - 0041 决策七第 97 行：列举时跳过临时前缀的目录。
  - 0027 第 39 行与 compose.new_run_id 的 docstring：加一条保证，run_id 不以点开头、不以临时前缀开头。
  - 0035 第 78 与 82 行：措辞要对齐（「建 run」含改名；回报之前死掉时，如果还没改名就没有以标识命名的 run）。
  - 人读文档 docs/user-guide/running-and-results.md 168-182 的目录树：说明报告目录里可能出现的临时目录与怎样清理。

  【要动的 code】（多数要与尚未落地的生命期锁一起写）
  - core/gherkai_core/adapters/run_store/local.py：create_run（153-166）改成在临时目录里写、写完 rename；list_runs（225-253）按名字跳过临时前缀；另加清理接口（只在 adapter 上，或放在 runtime）。
  - 生命期锁与边界检查本身（code 里还没有）。
  - cli/gherkai_cli/__main__.py：_cmd_run 的 begin（3016-3028）；_submit_local（1743-1793，本来就要按 0035 改成由后台推进进程建 run）；_cmd_reconcile（2750）及后台推进进程的新入口。
  - core/gherkai_core/persist.py 的 begin（79-104）：如果锁的取得放进 adapter，这里不用变；如果放在组合根，要传进临时路径。
  - settle-runs（未实装）。
  - runtime/gherkai_runtime/compose.py 的 new_run_id docstring。
  - 测试：test_adr_hygiene 不受影响；local run_store 的测试要改。

  【边界检查是否照样成立】成立。
  - 临时目录直接 mkdir 在报告目录下，和最终的 `<run_id>` 同一个父目录。同一父目录里的 rename 不会跨文件系统：跨了会得到 EXDEV，目标名是挂载点会得到 EBUSY，所以改名之后描述符所在的文件系统不变。Linux 按描述符的 mnt_id、macOS 按 fstatfs 取类型，都只看那次打开，与路径名无关。
  - 「建 run 目录之前另查报告目录、被拒不留目录」照旧，作用是不在边界之外建出报告目录本身。
  - 清理方必须先对临时目录的描述符做同一检查再试拿锁：在 NFS 一类边界之外的文件系统上，试拿锁可能假成功（0054 被拒方案第 257-258 行），那会删掉另一台机器上正在建的目录。

  【候选做法本身要补的两处】
  1. 窗口：mkdir 临时目录到 flock 之间，创建者还没拿到锁，清理方可能拿到锁并删掉这个目录。要求双方拿到锁之后都核对：路径仍指向自己锁住的那个 inode（fstat(fd) 与 stat(path) 的 st_dev 和 st_ino 相同）。创建者核对不过，或因清理方正持锁而拿不到锁，就换一个新名字重来，不以退出码 2 结束。清理方只按路径删、不按 fd 删，核对不过就跳过（防的是创建者已经改名并退出的情形）。
  2. 「已存在」的判定：POSIX rename 遇到已存在的空目录会静默替换，遇到非空目录才失败（ENOTEMPTY 或 EEXIST）；Python 的 os.rename 不提供 RENAME_NOREPLACE 或 RENAME_EXCL。改名失败时删掉自己的临时目录、抛 FileExistsError，可以保住「不改任何东西」。目标是空目录时被替换，不损坏任何 run。
  另外，暂存期间没有别的写入方能按 run_id 找到这个目录，所以 create_run 里的 `.runstate.lock` 短锁与「run_state 已在」的判断，在暂存阶段已无必要。

  【更简单的做法】
  - 不改名、就地清理：按内容判断「没有 run_state.json、只有 run_meta.json / .runstate.lock / *.tmp」并且锁拿得到就删。它同样有上面的窗口，而且凭内容分不清「建到一半」与「有人删了 run_state.json 的完整 run 目录」（里面有 jobs/、产物），可能误删用户数据。临时名靠名字区分，这一点更干净，建议把它作为被拒方案的护栏写进 ADR。
  - 只跳过、不清理：现状已经做到 list-runs 与 status 不受干扰（残留很小），但不满足 owner「要清」的要求。
  在我看到的范围内，临时名加改名是最小而完整的做法。

本机一侧要 owner 定或要实测的：

- 谁来清理、何时清理要 owner 定。可选：settle-runs（显式；已有列举，也已规定对报告目录做边界检查）；建 run 的一方在建 run 时顺带清理（自动，但每次建 run 都要列一次报告目录，而且让 run 和 submit 多出删除这一副作用）；两者都做。list-runs、status、explain 按 0054 第 155 行必须保持只读、不碰锁，不能当清理方。
- settle-runs 的输出形态要定：runs[] 以 run_id 为键，临时目录在名字上没有 run_id（里面的 run_meta 可能有，也可能没有）。是另起一组字段（如 staging），还是只在人读输出里给一行；dry-run 下要不要列出它们。
- 锁在 create_run 里取，还是在组合根里取，要定（接口诚实问题）。RunStore 端口与后端无关，云端没有锁；0030 第 231 行现在写「调用 create_run 之前已持有锁」。改名方案下临时路径要从取锁方流到写入方：要么给 LocalRunStore 加一个只在 adapter 上的建 run 方法，返回持有中的锁；要么由组合根取锁再把临时路径交给 adapter。
- 要实测，按 0054 决策四「先实测再加」：目录的 flock 在 rename 之后仍由原持有者持有。任务描述说 macOS 与 Linux 都已实测，但没说是哪些文件系统类型。清单里的 apfs、ext4、tmpfs、overlay、xfs、btrfs、ext3 要逐一核，还有宿主与容器之间的绑定挂载、容器里另一进程按新名字试拿。overlay 上新建的目录只在上层，按理可以改名，但没核过。
- 要实测：清理方与创建者的竞态（mkdir 到 flock 的窗口、清理方持锁时创建者拿锁失败后重试、创建者已改名并退出时清理方核对 inode 后跳过），在两个平台上用真实进程各核一次。这是并发时序问题，单测绿不构成证据。
- 掉电与内核崩溃：owner 的问题里写了「断电」，但 0054 第 238 行与 0030 决定三把它排除在外（原子写不做 fsync）。不加 fsync 时，候选做法只覆盖 SIGKILL，掉电后仍可能留下带空或截断文件的 <run_id>/，在清单里成为「无法读取」的行，也删不掉。要覆盖掉电，就要在改名之前对两个文件与临时目录 fsync、改名之后对报告目录 fsync，并改写 0054 第 238 行。要 owner 定。
- 临时前缀的取值，以及 run_id 不与它冲突的保证要不要写进 0027 第 39 行（与「不含 #」同类）。我推断现有格式（时间戳加 hex）不会以点开头，但 0027 把格式写成不入契约。
- 拿不准：现在 settle-runs 给了 run_id、而那个目录没有 run_state.json 时，0054 决策八没写给什么 reason（unreadable 还是「未找到」）。候选做法之下这种目录不会再以 run_id 命名，这个问题可能随之消失。
- 拿不准：0035 第 82 行在候选做法之下要不要改得更精确。后台推进进程在改名之前死掉时，没有以标识命名的 run，提交进程也没有拿到标识；改名之后、回报之前死掉，才是「建成了而没有推进器」。现在那一句仍然成立，只是没有区分这两种情况。
- 现状 code 落后于 ADR 的几处，改名方案要与它们一起实装，不能只改 create_run：本机 submit 仍由提交进程建 run 并写 tunnel.json（__main__.py 1761-1768）；status --wait 仍对 detached run 接力推进（2170-2184），而 0054 决策八写的是只处置、不推进；生命期锁、边界检查、settle-runs 都还没有。

云端一侧摸底的结论（建 run 的两次写之间被强杀会留下只有运行定义、没有运行态的条目；候选做法是一次事务写）：

  【候选：建 run 的两次 put 改成一次 TransactWriteItems，内含 Put META 与 Put STATE，各带 attribute_not_exists(run_id)】

  结论：可以做。它从写端消掉「只有 META、没有 STATE」这一种残留，改动集中在 DynamoDBRunStore.create_run 和它的测试，另有几处 ADR 措辞。它消不掉 S3 里 args/ 的孤儿对象。

  一、code 要改的地方
  - ddb.py:249-265：改成 `self._table.meta.client.transact_write_items(TransactItems=[{"Put": {...META...}}, {"Put": {...STATE...}}])`，表名取 self._table.name。
    - client 层要低层的类型化格式，需用 boto3.dynamodb.types.TypeSerializer 转换 Item；jobs Map、Decimal 与 BOOL 都经它转。据我所知 resource 层的 Table 没有 transact 方法，这一点要核。
    - 异常从 ConditionalCheckFailedException 改为 TransactionCanceledException：只有 CancellationReasons 里出现 ConditionalCheckFailed 才转成 FileExistsError。TransactionConflict、ThrottlingError、ValidationError 等照 AWS 错误上抛，由 _submit_cloud 归为退出码 2。
  - 先读和卸载的次序不变：两次强一致 GetItem 仍排在卸载之前，用来保证已有 run 的 S3 正文不被重写（0030 决定六 :260）。
  - ddb.py:226-234 的 docstring 要改写。
  - core/tests/test_ddb_run_store.py:356-400 的两条用例靠 monkeypatch table.put_item 造竞争窗口，要按新接口重写；318-333「只有一条在」的用例可保留。按「接口诚实优先」，测试为设计服务。

  二、限制
  - 每条条目仍不超过 400KB：META 本来就受此限，卸载就是为它设的；STATE 的大小随 job 数增长，这一点不变。
  - 一次事务至多 100 项、总计 4MB：两条最多约 800KB，够用。
  - 同一事务不能两次操作同一条目：两条主键不同，不违反。
  - 条件写兼容：Put 带 ConditionExpression 在事务里照常可用，与现有写法一致。

  三、费用（运行期成本，属于设计约束）
  - 事务写按两倍写单位计：每个 run 建一次时多付一份 META 与 STATE 的写量，META 数十到数百 KB 时这部分最明显。
  - 只在建 run 时发生一次。GSI 写不变：STATE 仍是一次进入 live 分组。
  - tools/ddb_capacity.py 已经识别 TransactWriteItems（:157-158），可以直接用它计量。

  四、对流与 kicker 过滤的影响
  - 两条条目仍各产生一条 INSERT 流记录。
  - 据 AWS 文档，事务完成之后改动才传播到流与 GSI。照此，kicker 拿到 STATE 的 INSERT 时 META 已经提交，强一致 GetItem 读得到。「写序 META→STATE 是契约」可以由「两条在同一次事务里写成」取代，两条流记录的先后不再承担意义。这一条要实测。
  - 过滤仍须只收 STATE：否则一个 run 会被冷启动两次，而且 META 没有 detached，也没有 status_group。
  - 现有过滤（detached）和 ADR 目标过滤（item_type=STATE）都不用改。

  五、IAM
  - 据我所知 DynamoDB 没有单独的 TransactWriteItems 授权动作，按事务里每个动作授权：Put 对应 dynamodb:PutItem；只有用到 ConditionCheck 动作时才要 ConditionCheckItem。
  - 编排进程角色已有「runs 表读写」（0033 :48），推进器 Lambda 用 grant_read_write_data，按此都不用新增动作。
  - 要按 0033 的惯例，用真实受限角色实测一次零 AccessDenied。

  六、要随之改的 ADR 措辞
  - 0030 决定六 :260，以及决定三 :190 里「真事务不用」的适用范围（限定为逐 job 的提交点）。
  - 0034 1b :86-87 的不变量。
  - 0054 决策五 :119、决策九 :166 里「META 已先写」「先写 META 再写 STATE」、边界 :241。
  - 0033 资源清单 13 :44 里「① 若匹配到 META 的新建……」的理由。
  按 owner #4，先改 ADR，再改 code。

  七、仍然留下的残留：卸载对象在事务之前写。被杀在卸载与事务之间，或事务失败，S3 里仍有无人引用的 args/ 对象：没有 tag、没有生命周期规则、桶 RETAIN。apps/ 对象 14 天后自动过期，不用管。

  【比较过、更简单但不如事务的做法】
  (a) 保留两次 put，STATE 失败时补偿删除 META：挡得住 AWS 错误，挡不住 SIGKILL。
  (b) 改成先写 STATE、kicker 改为滤 META：留下的会是只有 STATE 的 run。它进 live 分组，list-runs 永远看得见，清理 pass 永远保留它引用的 revision，推进器还要按「运行定义不可用」处理它，比现在更糟。
  (c) META 带 TTL 属性，STATE 落库后去掉：被杀在 STATE 之后、去 TTL 之前时，一个活 run 的 META 会被删，不可接受。
  (d) 不处理：META-only 对所有读者都不可见、只占存储，但 owner 要清；事后又因为不准 Scan 找不到它。

  所以事务是唯一能在写端消灭 META-only 的做法。

  【S3 孤儿对象】我没找到比「接受」更好的写端办法：
  - 卸载对象先打 tag、事务之后摘掉：被杀在两者之间时，活 run 的正文会被生命周期规则删掉。
  - 改成事务之后再卸载：kicker 可能先读到指针而对象还不在；被杀时 run 永远取不回正文。
  两者都更糟，只能交 owner 定。

云端现有的清理手段：

  现在没有任何手段能清理 META-only 条目，也没有手段清理 args/ 下的孤儿对象。
  - runs 表：没有 TTL。stack.py:185-193 没有设 time_to_live_attribute，同处 :203 注释写明「runs 表 RETAIN、无 TTL」；ADR 0030 决定六 :265 与 0038 :81 也这样写。表是 RemovalPolicy.RETAIN（stack.py:192；0033 :52）。
  - events 表：开了 TTL，属性 expires_at，7 天（stack.py:213-224；0033 :177）。它与这类残留无关。
  - 产物桶：只有两条按 tag 的生命周期规则，expire-job-in（tag gherkai=job-in，7 天）与 expire-apps（tag gherkai=app，14 天）（stack.py:240-257；0033 :96-101）。args/ 卸载对象不打 tag（arg_offload.py:86-92），没有规则覆盖；桶是 RETAIN。apps/ 对象 14 天后自动过期。
  - Lambda：kicker 与 reconciler 里没有扫 runs 表的清理。ADR 0054 决策九第 2 条所说的「清扫」是按 startedBy 停 ECS task，不写 runs 表，也不删条目；它只对由 STATE 流或定时触发带到的 run 生效，而且我在 code 里没找到它。`_scan_overdue_timeouts`（reconciler.py:377）只对已经装配成功、有 STATE 的 run 做超时兜底。exit-observer 只写 events 表。
  - worker revision 清理 pass 只回收 task-def revision，不碰 runs 表。
  - 结构上也做不到事后清：不准 Scan runs 表，META 又不在索引里，所以事后清理找不到 META-only 条目；用 S3 List 扫 args/ 前缀则会随历史无界增长。

云端一侧要 owner 定或要实测的：

- owner 定：云端建 run 要不要改成一次 TransactWriteItems。我的判断是能做，改动范围见 impact_of_candidate；照 owner #4 先改 ADR 再动 code。
- owner 定：S3 args/ 下卸载出来的孤儿对象（无 tag、无生命周期规则、桶 RETAIN）是否接受。按「行为不一致先做掉、不自行记局限」，这一条不能由我写成已知局限。我没找到能在写端消除它而不伤及活 run 的做法。
- 实测：事务提交之后，kicker 收到 STATE 的 INSERT 流记录时，强一致 load_run_meta 是否一定读得到 META。依据是 AWS 文档所说「事务完成后才传播到流」，没有实测过。
- 实测：真实 AWS 与 moto 在条件失败时 TransactionCanceledException 的 CancellationReasons 形态，以及 moto 是否支持事务里的 ConditionExpression。单测都在 moto 上。
- 实测：编排进程角色只有 runs 表读写（PutItem 等）、没有任何 Transact 字样的授权时，能否执行 TransactWriteItems。我的认识是没有单独的 IAM 动作，要用受限角色核一次。
- 实测：用 tools/ddb_capacity.py 量一次事务写的写单位，META 大小取典型值，和现在两次 PutItem 对比。运行期成本是设计约束。
- 拿不准：boto3 resource 层的 Table 没有 transact_write_items，这是我的记忆，没有查文档。要走 client 加 TypeSerializer 的话，jobs Map 等属性的序列化要再核一次。
- 要定措辞：现在 STATE 那次 put 因 ValidationException（如 jobs Map 使条目超过 400KB）失败时，CLI 报的是「云端不可达（表/桶/凭证/region）」，有误导。事务化之后仍是 botocore 异常，消息怎么写要定。拿不准：STATE 在多少个 job 时会撑到 400KB，我没有算（ADR 0034 机制三②有样本）。
- owner 定：网络失败时 put 或事务可能已在服务端成功而响应丢失，CLI 报退出码 2，但 run 实际已建成并会被推进。TransactWriteItems 的 ClientRequestToken 能让重试幂等，要不要用。
- 排序问题：code 与 ADR 现在有差距。kicker 过滤仍按 detached；第二条终态过滤、run 级定时触发与清扫、settle-runs 都未实装；同步 run --backend cloud 与 status --wait 调 kicker 仍在 code 里。改成事务应排在这些实装批之前、之中还是之后，要定。同步 run --backend cloud 在两次 put 之间被杀也留下 META-only；STATE 写成后被杀则留下没人推进的 live STATE。这条路径按 ADR 0016 决策 A 本来就要删除。
- 范围外、只记下：给了 --expose-local 时，当前 code 在建 run 之前用 setsid 起 ngrok 代理；SIGKILL 时 finally 不执行，代理留在本机。ADR 0035 的目标形态不同，我没有深入核对。
- 本机与云端一致性（owner #3 的本机清理）：本机的残留是只有 run_meta.json 的目录（ADR 0030 决定四 :231、0041 决策七 :97）。云端改成事务之后，本机是否也改成「建 run 不留只有定义的半成品」，以免两端在被强杀时表现不同，要和本机方案一起定。
