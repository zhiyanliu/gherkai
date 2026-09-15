# 文档健康度复盘第六轮 — 待批报告

> 类型: 待批报告（批毕落改吸收后删除）

基线：第五轮落地锚点 `a97f912`（2026-09-09）→ 本轮 HEAD。审计集 43 ADR + CONTEXT：21 份层读、23 份沿用第五轮具名结论（自 `a97f912` 起零改动）。

客观发现：CONFIRMED 120（其中第③类「code 偏离已定设计」1 条报裁定、其余 119 条已落地）/ REFUTED 5 / UNCERTAIN 0；提纯提案 25 条（红线复核通过 23，否决 2）；主观发现 12 条。


## 一、请裁定：code 偏离 ADR 已定设计（不改文档，移交 code-health）

- **docs/adr/0039-user-facing-surfaces-no-internal-references.md:43** — 「Python 与 TS 同一张表」与 code 不符：TS 侧禁词表缺 `决定 <序数>`、`推进器`、`宿主` 三项，正是该括注立下的「别让 TS 侧更松」要防的形态；且其中两项是本 ADR 落盘之后只往 Python 侧加的。
  - 证据：cli/tests/test_user_facing_messages.py:34-41 `FORBIDDEN` = `ADR\s*\d{4}|决策\s*[0-9A-Za-z]|决定\s*[一二三四五六七八九十0-9]|推进器|宿主|不变量|定位链|实测项|被拒方案|重议闸门|接缝契约|模块头|组合根装配|_require_vpc`；:43 `FORBIDDEN_TS = ("ADR", "决策", "不变量", "定位链", "实测项", "被拒方案", "重议闸门", "接缝契约", "模块头", "组合根装配")` —— 无 `决定`、`推进器`、`宿主`（TS 侧在 `ADR`/`决策` 两词上反而更严，是裸子串）。史实：`git log -S"推进器|宿主" -- cli/tests/test_user_facing_messages.py` = 6ff9a5c（2026-09-09 16:58，晚于本 ADR 落盘 …
  - 复核员：① 引文核对：`/Users/lzy/workspace/yaozhou/docs/adr/0039-user-facing-surfaces-no-internal-references.md:43` 逐字与提交者引用一致，位于 `### 护栏`（:41）小节首条，主句「Python 与 TS 同一张表」是**现在时断言**；括注「（曾因 TS 表更松漏掉一处「组合根装配错误」）」的「曾」只框住那次泄漏事故，作为该不变量的 why，反而强化「现在两侧一致」的主张——不属红线护栏里「历史记录 ≠ 过时」的豁免形态，也没有任何例外/子集条款。

② code 真值（亲自读）：`/Users/lzy/workspace/yaozhou/cli/tests/test_user_facing_messages.py:34-41` 的 `FORBIDDEN` 含 `决定\s*[一二三四五六七八九十0-9]`、`推进器|宿主`（:38 带注释「内部机制名（ADR 0034 的 advancer/host 词条）」）；`:43` 的 `FORBIDDEN_TS = ("ADR", "决策", "不变…


### 一b、其它请裁定项（决策层面，复盘不代选边）

- **docs/adr/0039-user-facing-surfaces-no-internal-references.md**（修补员未落）：revised_fix 本身就判定这是 code 漂移而非文档陈旧，明确要求「移交 code-health（不改文档）」，故本文件无可落项；改动面为 cli/tests/test_user_facing_messages.py 的 FORBIDDEN_TS，已记入 cross_file。ADR 该句（含「曾因 TS 表更松漏掉一处组合根装配错误」的护栏理由）只在人反向裁定「TS 面只需覆盖子集」时才由人显式改，不由本轮复盘代改。

- **docs/adr/0009-maximize-aws-hard-constraint.md**（修补员未落）：revised_fix 的处置结论本身就是「报人裁定，本轮不落 0009 决策面改动」，并明写「裁定前 0009/0037 一字不改」；它未给出单一可落地的替换文字，只给了两条互斥候选分支（A：0009「决定」段末尾加适用面句 + 0037 补指针；B：0009 不动、改 0037 登记例外或把 registry 重议回 ECR Public），选哪条取决于人对「维护者发布通道是否在 0009 射程内」的裁定；任选其一落下去就是复盘替人改决策（0009 自陈「不是可权衡的偏好」）。前置事实已亲验仍成立（0009:15 quote 在位、Status 仍 Accepted、例外清单仍只 0035/ngrok 一条；0037:40/:136/:141 仍将 worker 基底镜像定在 GHCR 且自陈 ECR Public 可行但优势碰不到；deploy_aws/gherkai_deploy_aws/workers.py:47 GHCR_BASE_IMAGE 与 :762 sync_base 仍拉 GHCR），故矛盾真存在，但属决策面待裁，不是可自行拉齐的文档漂移。

- **ADR 0001 文件名**：审计与复核均确认文件名 `0001-scope-limited-to-english-ui.md` 断言的范围已被该 ADR 2026-09-09 的修订反转（Midscene 不限 UI 语言），修补员据此把文件改名为 `0001-ui-language-scope-per-engine.md` 并要求改 5 个文件里的 9 处链接。**我已撤回改名**（内容一字未动）：按 CLAUDE.md 文档纪律「文件名是引用锚点、要在 URL/终端/grep 里稳定可打」，ADR 文件名是历史锚点、标题在首行 `#` 已改准；是否接受「文件名停在旧世界」为已知不一致、还是改名并改链接，请裁定。


落地后逐 hunk 自审（独立复核员逐文件）：主批 45 文件 / 88 hunk，意见 16 条（全部 low：指针略窄、括注歧义、新句绝对化、清单漏项被新行照出的连带句），落回 15 条、跳过 1 条纯排版；零元评论泄漏、零受保护要素丢失。补跑批（0017/0032/0033）3 文件 / 6 hunk，意见 1 条 low（整行粗体内嵌粗体）已落回。code 侧同源漂移移交 code-health：`deploy_aws/gherkai_deploy_aws/stack.py:132` 注释仍写「schema 与 core/tests/conftest.py fixture 一致」，方向与 ADR 0033 本轮纠正的相反（CDK 才是权威源）。


## 二、提纯提案待批（红线复核通过；approve_reduced 的按「缩小后改法」落）


### docs/adr/0015-v1-positioning-smoke-not-regression.md

- **P1**（第 36 行，approve）候选句：「- **未点名不抓**（种类 B）：最左档定位的必然代价，接受。」
  - 沉积判据：同一事实在本 ADR 内第三次完整重述、且用词与上文逐字重合：第 30 行已写「**v1.0 不解决，作为已知边界接受。**」、第 32 行已写「种类 B 不是 bug，是最左档定位的必然代价。」。本句不承载新决策/why/trade-off/反模式/不变量，也不带指针；同节第 37 行恰恰已是「列条目 + 指针」形态，证明本节的结构功能（单点枚举 v1.0 的边界）用指针即可满足，属「可指针化的完整重复」。
  - 改法：- **未点名不抓**（种类 B）：见上「两种"不确定性"——只治其一」。
  - 复核员：证伪未成立。逐要素核验：①决策本身=条目标签「未点名不抓（种类 B）」，改法原样保留（含「未点名不抓≡种类 B」映射）；②why/trade-off「最左档定位的必然代价」在同文件第 32 行逐字存在，且那里还挂着本文件唯一的反模式（混淆 A/B→误以为投票能带来确定性）；「接受」在第 30 行加粗存在（v1.0 不解决，作为已知边界接受），并由节标题「已知边界（v1.0 明确不做）」二次承载；③候选句自身无不变量、无「曾/原/已被取代」历史框定、无实测数据/日期/真跑结论类内联证据、无指针（改法反而新增指针）；④「有意重复」的红线保护对象是「跨切面事实带指针的简短重述」、理由是「ADR 该能被单独读懂」——本处是同文件内相隔 4–6 行且无指针的重述，ADR 自包含性不受影响，改法恰是把它转成红线自己的受保护形态；⑤骨架句测试（删了论证结构是否断）不成立：兄弟条第 37 行已是「条目+指…


### docs/adr/0016-execution-architecture-core-lib-run-model.md

- **P2**（第 167 行，approve_reduced）候选句：「- **测试注入点随之迁移**：原 cli 测试 `monkeypatch m.LocalRunStore/...`（模块级名字）改为 patch `compose.build_local_stores`（或其内部构造钩子）——注入点从「__main__ 模块级 Local* 名字」迁到「compose 的 build 函数」，验的东西不变（写序 / --no-report 不构造 / running→final），只换注入锚。cloud 同理 patch `compose` 的 boto3 钩子。」
  - 沉积判据：这半句是一次性重构的迁移节奏（「原 X 改为 Y」「验的东西不变、只换注入锚」），承载的稳定信息只有「cli 测试的注入锚 = compose 的 build 函数 / boto3 钩子」一条现状；被替换掉的旧世界（3 个 `monkeypatch m.Local*`）已在紧邻的 line 168 trade-off 条里作为**代价**保留（那条受 trade-off 红线保护、不动），故此处的「原…改为…」是重复的施工叙事。同条后半句「cli 测试**只验接线层**…不引 moto——adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰」是测试边界决策 + 理由，须原样留下。
  - 改法：- **测试注入锚 = `compose.build_local_stores`（或其内部构造钩子），cloud 同理 patch `compose` 的 boto3 钩子**：cli 侧据此验写序 / --no-report 不构造 / running→final，且**只验接线层**（backend 选对了、构造了正确 adapter + 参数对 + offloader 挂了），不引 moto——adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰。
  - 复核员：提纯方向成立但提案给的改法保不住要素，故改法修正后放行。① 可删部分确认：「原 cli 测试 monkeypatch m.LocalRunStore/… 改为 …」「注入点从『__main__ 模块级 Local* 名字』迁到『compose 的 build 函数』」「验的东西不变…只换注入锚」是施工节奏；被替换的旧世界（`monkeypatch m.Local*` + `__main__`→`compose`）在紧邻 line 168 trade-off 条原样在册，删它不丢历史框定，红线「历史记录≠过时」不被触发。② 但提案改法额外抹掉两处受保护要素：(a) 精确指针 `（写序 / --no-report 不构造 / running→final）`——经对照 code，这三项与 cli/tests/test_main.py 现存三个具名测试一一对应（test_realtime_comm…

- **P3**（第 143 行，approve）候选句：「**关键：这只是重定位「谁来用、是不是用户档」，不删预演的价值论证**——「上传/抢传能力提前在 subprocess 环境建好并验证、为 Fargate 铺路」这套论证（见 [0029](./0029-engine-artifacts-to-s3.md)/[0032](./0032-fargate-execution-environment.md)）完全成立、一字不动，只是承载它的 `subprocess + 注入云存储` 从「CLI 用户可选一档」标注为「e2e_harness/开发预演手段」。」
  - 沉积判据：「这只是重定位…不删…一字不动」是对当次文档编辑动作本身的自述（编辑叙事，读者是当时的改稿人）。该句真正承载的两条要素——① 预演价值论证仍成立 + 指针 0029/0032，② 该组合的定位从用户档降为内部手段——去掉编辑自述后完整保留；「不删/一字不动」对未来读者没有信息量。
  - 改法：**预演的价值论证仍完全成立**——「上传/抢传能力提前在 subprocess 环境建好并验证、为 Fargate 铺路」（见 [0029](./0029-engine-artifacts-to-s3.md)/[0032](./0032-fargate-execution-environment.md)）；变的只是承载它的 `subprocess + 注入云存储` 的定位：从「CLI 用户可选一档」改为「e2e_harness/开发预演手段」。
  - 复核员：候选句（0016 第 143 行）自身跨度内承载的受保护要素为四项：精确指针（0029/0032）、带指针的简短重述（「上传/抢传能力提前在 subprocess 建好并验证、为 Fargate 铺路」）、历史框定（从「CLI 用户可选一档」→「e2e_harness/开发预演手段」）、框定/骨架功能（限定决策 B 只动定位轴）。这四项在改法中全部保住：链接原样、重述句原文照留、旧/新定位两个引号内原样、「变的只是承载它的…的定位」承接同一结构功能。本句自身不含 why/trade-off（理由体在 0029 第 95 行「定位澄清」条『能力可提前、需求属 Fargate』与 0032 第 22 行）、不含反模式/被拒方案、不含不变量、不含内联实测证据（~930KB/~2.0MB、丢失归零等数据内联在 0032 第 18/22 行与 0029 第 95 行，均在他处、未被触碰）。真正删掉的…


### docs/adr/0024-worker-core-protocol.md

- **P4**（第 177 行，approve）候选句：「**传输选型已定 + adapter 已实装 + 组合根接线已落地**：」
  - 沉积判据：施工进度式预告：其后紧接的三个分句把同样三件事各自完整说了一遍（events-out 焊死 DDB / FargateEngine 已编码 / 组合根接线已完成），标题本身不承载 why、trade-off、不变量、被拒方案或指针；本节的框定功能由同句前半截「本节钉的是已想清、不会变的边界（哪些 survive、哪些必改）」承担，删掉后论证结构不断。
  - 改法：删掉这个三段式进度标题，本节引文接成：「> 本节钉的是**已想清、不会变**的边界（哪些 survive、哪些必改）。events-out 焊死到 DynamoDB events 表（worker PutItem / core Query 轮询，非 SQS/MSK/CloudWatch——见下「DynamoDB 作 events-out 传输」+ 三方案被拒护栏），`FargateEngine` adapter 已编码（`core/gherkai_core/adapters/fargate_engine.py`，job-in 走 S3、events-out 走 DDB、stop→StopTask、退出码→DescribeTasks），**组合根接线已完成**（`compose.build_fargate_engines` + `--backend cloud` 切执行 + IaC，[0033](./0033-iac-aws-backend-and-composition-wiring.md) Accepted、真部署真跑）。产物→S3 是**正交的另一条边**，见 [0029](./0029-engine-artifacts-to-s3.md)。」
  - 复核员：候选句仅为加粗标签「**传输选型已定 + adapter 已实装 + 组合根接线已落地**：」，逐条对红线护栏证伪未成立：①决策本身不在标签而在其后分句（events-out 焊死到 DDB events 表，含「非 SQS/MSK/CloudWatch」）；②why/trade-off/被拒方案零承载，被拒护栏指针「+ 三方案被拒护栏」在保留段；③非不变量（是状态断言）；④它重复的三件事就在同句紧后、且标签本身零指针，属「同一事实完整重复」，不是护栏保护的「带指针的简短重述」；⑤无「曾/原/已被取代」历史框定；⑥全部精确指针（fargate_engine.py 路径、compose.build_fargate_engines、[0033]、[0029]、「见下『DynamoDB 作 events-out 传输』」）均在保留段；⑦自包含证据「0033 Accepted、真部署真跑」在保留段…


### docs/adr/0025-plan-module-feature-to-jobs.md

- **P5**（第 5 行，approve_reduced）候选句：「下一块 `schedule`（scope 串/并行调度）以本模块输出为输入，另立。」
  - 沉积判据：「下一块…另立」是本 ADR 撰写当时（0026 尚未成文）的施工序列语；其承载的稳定信息只有「调度另有一篇 ADR、以本模块输出为输入」这条边界，且指针不精确（未链 0026，读者得自己找），与同段其它句子（0019/0016/0024 都带链接）不一致。
  - 改法：调度（scope 间串/并行、会话共享）另立 `schedule` 模块，见 [0026](./0026-schedule-module.md)，以本模块输出为输入。
  - 复核员：候选句承载两项受保护要素，但改法基本能保住，只需收窄一处。①边界决策（调度另立一篇 + 「以本模块输出为输入」的接口关系）——提案改法完整保留，且补上本篇缺失的 0026 链接（现状 0025 零处链 0026，而 0026 反向链了 0025，属指针精化、方向正确）。②模块名符号 `schedule`——本句是全篇唯一引入点，下游第 23/51/85 行均裸用「schedule」（`= schedule 交给单个 worker 的活`、`由 schedule 的并发上限治理`、`schedule 归位错乱`），提案改法把反引号模块名换成纯 ADR 编号，会让这三处失去本篇内的引入，属可避免的信息丢失，故在 reduced_change 里把 `schedule` 留住。真正该删的施工语只有「下一块」（build order）；「另立」是范围边界陈述、非施工节奏，保留。三模块次序（协议 0…

- **P6**（第 93 行，approve_reduced）候选句：「若未来需更强稳定性可引 `@id:` tag，暂不做。」
  - 沉积判据：同一留口子在本文出现三处：line 123「留口子不实现：`@id:` 显式 id tag」、line 128「重议」条（且是唯一带触发条件「若出现 id 跨运行不稳的真实痛点（feature 频繁改行号）」的一份）。此处第三份是无指针、无增量的完整重复。
  - 改法：将第 93 行改为：「- 行号稳定（feature 不大改即不变）、人可读出来源；更强稳定性靠 `@id:` tag，暂不做（见下「留口子不实现」/「重议」）。」
  - 复核员：候选句在自身跨度内承载受保护要素：① 决策本身（`@id:` tag「暂不做」）；② 该决策的 why/权衡条件（「更强稳定性」——恰是紧前半句「行号稳定（feature 不大改即不变）」这个有条件稳定性的另一面），且位于 id 派生规则的落点处。层读证伪了「沉积」定性：git show ae2002e（本 ADR 首个提交）里三处同时存在（当时 line 75 点位句 / 102 留口子 / 107 重议），既非逐层叠加的施工括注、也非被覆盖未删的旧描述层，而是作者原始的三位结构（点位带 why 的暂缓决策 + 留口子清单作边界索引 + 重议给触发条件）。红线护栏「有意重复」条的压缩触发是「同一事实多处完整重复且已漂移」，逐条比对三处措辞完全一致、零漂移，且 line 123 是不带任何理由的裸清单项、line 129 在 30+ 行之后，故整句删除会让点位处只剩「行号稳定（featur…


### docs/adr/0027-runreport-aggregation-index.md

- **P7**（第 96 行，approve）候选句：「`ResultStore` 旧 docstring「RunReport 归集靠它」一句删除——归集职责移交 `ReportStore`。」
  - 沉积判据：这是一次已完成的 code 编辑动作记录（施工流水），不是决策：其承载的决策「归集职责属 ReportStore」在同句前半的三 port 职责定义与 line 13–14、line 96 前半已写死；真值侧该 docstring 早已不含此句（core/gherkai_core/ports.py:159-166 的 ResultStore docstring 现只讲「数据面/判定真值唯一权威」）。
  - 改法：删除该句，「职责边界（三 port 正交…）」条止于「`ReportStore`=**纯派生只读导航视图**（可从 `RunResult` 完全重建、永不作 CI 判定源）。」
  - 复核员：候选句「`ResultStore` 旧 docstring「RunReport 归集靠它」一句删除——归集职责移交 `ReportStore`。」不承载任一受保护要素，是施工流水（已完成的 code 编辑动作记录）。逐项证伪：①决策本身不唯一承载——「归集职责属 ReportStore」在同句前半（三 port 正交定义 + [0016] 指针）、ADR 标题、line 5「落地 ReportStore 的 local adapter」、line 18「『产物在哪、属于谁』是归集索引的本分」、以及 0016:78「ReportStore —— 把 RunResult 归集成 RunReport」多处写死，后半分句是同句前半的重复，不属「带指针的跨切面简短重述」。②非历史框定：语面有「旧」，但框住的是一个 code 字符串、不是被取代的决策——git 层读证实 8caac30（ADR 002…

- **P8**（第 169 行，approve）候选句：「（注：store 读回面**已落地**——`RunStore.load_run_meta`/`load_run_state` + `ResultStore.load_job_result`/`load_all`，靠 `serialize` 完整重建，[0016](./0016-execution-architecture-core-lib-run-model.md)。）」
  - 沉积判据：它挂在「留口子**不实现**」列表下却宣告「已落地」= 毕业项没删的旧描述层（列表的语义是仍敞着的口子）；读回面 API 的权威在 0016（该括注自己就指向 0016），此处第二份只是状态镜像。
  - 改法：整条删除（store 读回面由 [0016](./0016-execution-architecture-core-lib-run-model.md) 承载；本节只列仍敞着的口子）。
  - 复核员：候选句（docs/adr/0027-runreport-aggregation-index.md:169）自身跨度不承载任一受保护要素：非 0027 的决策、无 why/trade-off（原口子条目里的「v1.0 只先行写面」why 在落地时已随条目删除）、非被拒方案、非不变量（相邻 168 行的「core 仍不解析任何产物」不连坐）、无历史框定词（现文是现在时状态断言；早期版本的「原此处『读回面顺延』已兑现」框定尾巴已被前轮删掉）、无实测数据/日期/真跑结论（本节真跑证据在 165 行）、非骨架句（删了论证不断，且「已落地」挂在「留口子不实现」列表下与列表语义相冲，删除反而修正结构）。「带指针有意重复」的护栏不成立：红线只护「简短重述」，而此句三要素在权威 0016 逐条都有（0016:76-77 列出 load_run_meta/load_run_state/load_job_res…

- **P9**（第 65 行，approve）候选句：「**返回 `ResourceUri` 而非 `Path`**（封版前收口）」
  - 沉积判据：「（封版前收口）」是施工时点标记，不承载 why/trade-off/不变量——同句后文已给完整 why（S3 adapter 否则被迫返回 `Path` 包 `s3://`，而 `Path` 会把 `s3://b/x` 折成 `s3:/b/x`），删掉该括注论证不断。
  - 改法：**返回 `ResourceUri` 而非 `Path`**
  - 复核员：证伪未成立，提案通过。逐要素核查候选句自身跨度（`docs/adr/0027-runreport-aggregation-index.md:65`，Status 头为 Accepted）：

被删的只有括注「（封版前收口）」，四字全部是**施工时点**信息，不承载任一受保护要素：
- **决策本身**在粗体「返回 `ResourceUri` 而非 `Path`」里，改法原样保留；
- **why** 在同句后文且完整独立于时点——「**同一签名容两种落点**，否则 S3 adapter 被迫返回 `Path` 包 `s3://`（`Path` 会把 `s3://b/x` 折成 `s3:/b/x`，错）」，删括注后论证链（决策→两 adapter 返回形态→why→`NewType` 定义与零成本→消费端约束）完整，**骨架不断**（删了论证结构照样立，非「读着顺」型骨架）；
- **tra…


### docs/adr/0029-engine-artifacts-to-s3.md

- **P10**（第 69 行，approve_reduced）候选句：「## 分期：上传第一期（subprocess 预演环境落地，现在做）/ Fargate 增强（未来）」
  - 沉积判据：「现在做」是 Draft 期的施工时间坐标，与第 76 行「第一期实现定论（…已实现）」及 Status 头「已在该预演环境实现并验证」同文冲突；分期本身（第一期 vs Fargate 增强的边界与理由）是决策、保留，只有时态标记是施工残留。
  - 改法：## 分期：上传第一期（subprocess 预演环境落地，已实现）/ Fargate 增强（未来）
  - 复核员：候选句（第 69 行整条标题）确实承载受保护要素——决策本身（第一期 subprocess 预演落地 / Fargate 增强未来 的分期边界）与骨架框定功能（框住 71-74 行两条分期论证，并用「现在/未来」建立次序对比）；但提案定向的子跨度「现在做」自身不承载任一要素，且提议改法把上述两项全部保住，故按「承载要素但改法能保住（只删施工节奏词）」一档通过。逐项证伪均未成立：①非历史框定（无「曾/原/已被取代」框，纯裸时态）；②非自包含证据（无实测数据/日期/真跑结论——本文真正的证据锚在 62-67 行「调查依据」与 95 行「定位澄清」的真跑结论）；③非精确指针，且全 repo 除本行外无任何文档/code 引用「分期」这个小节标题（已 grep docs/ + README/CONTEXT + cli/，零命中），改括注不制造 DEADLINK；④次序结构功能不丢（「已实现 / 未…

- **P11**（第 78 行，approve）候选句：「第一期真做时把下面几点从"待定"钉死（原"留口子"里对应项标状态）：」
  - 沉积判据：整句讲的是「我改这篇文档时做了什么」（把待定项钉死、给留口子条目标状态）——编辑动作与施工节奏，不承载决策 / why / 权衡 / 不变量 / 精确指针；留口子节自己的删除线条目已自明其状态。
  - 改法：下面几点是第一期敲定的定论（「留口子」里对应项已标状态）：
  - 复核员：候选句（0029 第 78 行）自身跨度只承载两项受保护要素，改法都保住了：① 叙事骨架功能（引出下方 bullet 清单）——改后仍是同功能引导句 + 冒号，论证结构不断；② 精确指针（指向本篇第 108 行「留口子 / 待真做时定」节）——改后保留为「（「留口子」里对应项已标状态）」。不承载决策本身、why、trade-off、反模式/被拒方案、不变量、Accepted ADR 内联证据。唯一需要谨慎的是「从『待定』钉死」「原」带的历史框定味，但已核实该血缘在本篇另有三处权威落点、非本句独有：第 108 行节标题字面即「留口子 / 待真做时定」（「推迟到真做时定」这条决策本身写在那里）；第 110、111 行是删除线条目 + 显式状态注（如「~~S3 key 命名 ↔ ResourceUri s3:// 形态~~（第一期已定，见上「第一期实现定论」）」），删除线即历史框定；第 73 行…


### docs/adr/0032-fargate-execution-environment.md

- **P12**（第 56 行，approve_reduced）候选句：「**Midscene `MIDSCENE_GRACE_MIN_S=25` 不动**（实测 12.4s、~2x 余量；Midscene 无 greenlet、会话释放 0.2s，长 act 下也远快于 Nova）。后来的 step 级 evidence（[0042](./0042-step-evidence-and-explain.md) 决策一）给两 worker 的收尾序列各加了一段**有界的截图队列排空**（退出路径 6 s，排在会话释放之后）：Nova 落在 `NOVA_GRACE_MARGIN_S=30` 内不动；Midscene 的下限组成多一项 → `MIDSCENE_GRACE_…」
  - 沉积判据：层读定位的两层叠加：前层（校准当时）断言「=25 不动」，89cfc8b 追加的后层把值改成 31 却没回改前层——同一句里先给旧值再给新值，当前值埋在句尾。前半句除数据（12.4s / ~2x / 无 greenlet 0.2s，受保护的自包含证据）之外，「=25 不动」这个**值断言**本身不承载 why/trade-off/不变量，只是被后层覆盖的旧描述层；按密度看，读者/agent 检索 `MIDSCENE_GRACE_MIN_S` 时先撞到的是失效值。
  - 改法：   **据此的 code 决策**：Nova `NOVA_GRACE_MARGIN_S` **60→30**（下限 180→150，主要收益在 subprocess 路径满足不变量 + 留 ~1.5x 余量；Fargate 路径 grace 被忽略、此改动不影响其行为）；**`ACT_TIMEOUT_S=120` 不动**（见上②③）；**Midscene `MIDSCENE_GRACE_MIN_S`：本次校准判 25 够用**（实测 12.4s、~2x 余量；Midscene 无 greenlet、会话释放 0.2s，长 act 下也远快于 Nova），**后被 step 级 evidence（[0042](./0042-step-evidence-and-explain.md) 决策一）的有界截图队列排空顶到今值 31**——该排空（退出路径 6 s）排在会话释放之后，Nova 侧落在 `NOVA_GRACE_MARGIN_S=30` 内、不动，Midscene 的下限组成多一项。
  - 复核员：候选句跨度（「Midscene `MIDSCENE_GRACE_MIN_S=25` 不动（实测 12.4s…）」+ 紧随的 0042 排空句）确实承载受保护要素，共四项：① Accepted ADR 内联的自包含证据（实测 12.4s、~2x 余量、Midscene 无 greenlet、会话释放 0.2s，正是本 ADR「真容器校准结论」表格的引擎侧读数）；② 校准期的决策本身（当时判 Midscene 下限不用动）；③ 精确指针（0042 决策一，链接文件存在，其第 81 行确认「退出路径 6 s」「Nova 落在 NOVA_GRACE_MARGIN_S 内、Midscene 相应上调」）；④ 排空「排在会话释放之后」= 0024「会话释放优先」不变量的落点。但提案改法把这四项全部原样保住，只把失效的值断言改成历史框定：「本次校准判 25 够用…后被…顶到今值 31」——符合红线「历史…


### docs/adr/0033-iac-aws-backend-and-composition-wiring.md

- **P13**（第 182 行，approve）候选句：「- **镜像瘦身**：属施工，不在本 ADR 决策面。（真容器 grace/中断校准已完成，归 [0032](./0032-fargate-execution-environment.md) Accepted。）」
  - 沉积判据：括注是跨 ADR 的**进度回响**：0032 的完成状态真源在它自己的 Status 头（本文第 3 行与「资源清单」5. 已两处指过去），此处再复述一次「已完成」只会随对方状态漂移；它不承载 why / trade-off / 被拒方案 / 不变量，是「留待」清单上一个已勾掉的旧条目残留（该项原本与镜像瘦身并列在 defer 里）。同族改动第五轮已有先例并获批（[P26] approve：删另一 ADR 里「仅余 Fargate 特有的真容器 grace/中断校准（0032）」这句进度复述，理由同为「真源应留在 0032 自己的 Status/正文」）。
  - 改法：- **镜像瘦身**：属施工，不在本 ADR 决策面。
  - 复核员：逐要素对照红线护栏，候选句被删跨度（括注「（真容器 grace/中断校准已完成，归 0032 Accepted。）」）不承载任一受保护要素，且 git 层读坐实它就是沉积残层。

逐条证伪尝试：
1) why / trade-off / 反模式·被拒方案 / 不变量 / 决策本身 —— 括注只陈述「另一 ADR 的一项已完成」，不给任何理由、代价、护栏或决策；本行承载决策边界的是保留部分「属施工，不在本 ADR 决策面」。
2) 「历史记录 ≠ 过时」（曾/原/已被 X 取代框住的旧世界） —— 不成立。护栏保的是**被取代的旧设计/旧决策脉络**；此处从无决策被反转，「真容器 grace/中断校准」在 0033 里从来只是 defer 占位（见下 git 证据），括注框的是**进度状态**（完成）而非旧世界，删它丢不掉任何决策脉络。
3) 精确指针 / 有意重复（跨切面事实带指针的简短重…


### docs/adr/0034-detached-batch-reconciler.md

- **P14**（第 236 行，approve）候选句：「临时 PoC 脚手架验后即清、未入库」
  - 沉积判据：施工卫生流水：交代脚手架事后怎么处置，不承载决策 / why / trade-off / 反模式 / 不变量，也不是证据本身（H1/H2/H3 三条数据的可信度与可核性不依赖它）。且它复述的是 CLAUDE.md「工作方式」已有的通行约定（一次性脚本放 $CLAUDE_JOB_DIR/tmp、不入 tools/），在一个证据节的标题里再声明一次是净噪声。
  - 改法：标题改为：`## 地基实测（2026-07-19，真实 AWS 账户/us-east-1；6 个真 Fargate task——其中 4 个构成 H1 退出场景矩阵——+ 真 DDB Streams/条件写）`
  - 复核员：候选子句「临时 PoC 脚手架验后即清、未入库」只交代脚手架事后处置，逐条比对红线护栏 10 项均不命中：非决策/why/trade-off（本 ADR 的 why 与被拒方案节均无脚手架相关条目）、非反模式·被拒方案（「一次性脚本不入库」是 CLAUDE.md「工作方式」的通行工作规范，不是本系统被拒的设计选项）、非不变量、无指针故非「带指针的有意重复」、无「曾/原/已被取代」历史框定、非精确指针（反而声明无制品可指）、非叙事骨架（删后标题的「何时/在哪/跑了什么规模」框定功能不断，节名「地基实测」未动）。唯一需权衡的「Accepted ADR 内联的自包含证据」也不成立：证据要素 = 日期 2026-07-19、真实账户/us-east-1、6 个真 Fargate task/4 个 H1 退出场景矩阵、真 DDB Streams/条件写，以及正文 H1（exitCode 4/4 含 …


### docs/adr/0037-distribution-and-packaging.md

- **P15**（第 63 行，approve）候选句：「目标态文档里凡指命名真源模块一律写 `gherkai_runtime.names`（当前 `gherkai/gherkai/names.py`）。」
  - 沉积判据：施工窗口期的**文档写作指令**（迁移期告诉写文档的人该写哪个名字）+ 一条已随目录改名消失的迁移前路径。三名分离的决策本身由同 bullet 前半句（「CLI 发行包叫 `gherkai`，当前的中间层 `gherkai` 让位改 `gherkai-runtime`」）与 2a 表格承载；此句不承载 why / trade-off / 不变量 / 被拒方案，也不是精确指针——`gherkai/gherkai/names.py` 已不存在（真值 runtime/gherkai_runtime/names.py，`git ls-files` 核实），指过去是空指针；迁移完成后「凡指…一律写…」已无适用对象（全库都已写新名）。删了 2a 的论证结构不断。
  - 改法：删除整句，该 bullet 收在「→ CLI 发行包叫 `gherkai`，当前的中间层 `gherkai` 让位改 `gherkai-runtime`。」结束（命名真源模块的当前真值由 2a 表格与 0016 布局树承载）。
  - 复核员：证伪未成立，红线护栏逐项过关。① 决策本身不在本句：三名分离由同 bullet 前半句「唯一硬约束：用户敲的发行名 = 命令名 → CLI 发行包叫 gherkai，当前的中间层 gherkai 让位改 gherkai-runtime」与 2a 表格（第 55–61 行）承载，删后 bullet 结论完整。② why / trade-off / 反模式·被拒方案 / Accepted 内联自包含证据（实测数据·日期·真跑结论）：句内一概没有。③ 不变量「命名真源单点」不在本句、别处硬承载：docs/adr/0016-execution-architecture-core-lib-run-model.md:227「命名真源只余 gherkai_runtime.names.BASE_* 一处」、0033:56「命名真源的落位演进…复刻消除、真同源」、0038:104「键名常量与路径构造单点在 …

- **P16**（第 75 行，approve）候选句：「dirty 状态下 `uv sync` 的解析行为列入实测项。」
  - 沉积判据：Draft 期的待验 TODO 指针（「已排入待办」这层施工流水），实测项 1 已把该验证连同结论内联（「五个 wheel 的 `==` pin 与 extras 渲染正确、`uv sync` 解析通过」+「`uv.lock` 对动态版本的 workspace 成员只记 `source = { editable = "<dir>" }`、任意 commit 上 `uv lock --check` 通过」）。留着等于在同一 ADR 内既说「待验」又说「已验」，且不承载任何 why/不变量；bullet 的两条实体内容（同 git 状态派生故天然同号；editable 版本是 `uv sync` 时的快照）不受影响。
  - 改法：删该句，bullet 变为：「- **同 repo 所有 workspace 成员的版本从同一 git 状态派生**，天然同号：本地 dev 版本两侧一致、pin 自满足。**editable 安装的元数据版本是 `uv sync` 时算出的快照**，工作树之后再改、版本串不会自动变……」（其余逐字不动）。
  - 复核员：候选句「dirty 状态下 `uv sync` 的解析行为列入实测项。」经逐要素过筛不承载任何受保护要素：①无决策/why/trade-off——它只登记「待验」，不做选择也不给理由；②无被拒方案·反模式——dirty 的决策面与被拒面完整存在于别处（第 72 行 `dirty=true` 显式钉死的理由 + `metadata=true` 真跑证伪、第 240 行「被拒方案」条）；③无不变量——它是「尚不知道」的欠条，相关不变量「非纯净构建必带 `+`、决策 7 判据成立」在第 72、167 行；④非精确指针、非带指针的有意重复——不点条号、语义是 TODO 而非「证据见 X」，且 实测项 1 正文自带同关键词（「`=={{ version }}` 与 `uv sync`/`uv run` 的解析行为」），删后可检索性不丢；⑤非内联证据——git 层读证实该句与 Draft 首版 ad9…

- **P17**（第 96 行，approve）候选句：「；当前混在主依赖里的 pytest 挪去 dev group」
  - 沉积判据：一次性搬迁指令，已完成且无再犯价值：engines/novaact/pyproject.toml 的 `dependencies` 只有 `nova-act>=3.4.187.0` + `boto3>=1.34`，dev 依赖统一在根 pyproject.toml 的 `[dependency-groups] dev`。它挂在 2c 依赖表的 extras 单元格里，前半句（「无（**不依赖 gherkai-core**：worker 讲协议、零 core 依赖，0024）」）才是承载不变量的那半；此半句既非 why 也非反模式护栏（「测试依赖别混主依赖」是通行常识、非本项目踩过的坑）。
  - 改法：该单元格收成：「无（**不依赖 gherkai-core**：worker 讲协议、零 core 依赖，[0024](./0024-worker-core-protocol.md)）」——删分号后的搬迁句。
  - 复核员：候选句「；当前混在主依赖里的 pytest 挪去 dev group」逐要素核查后不承载任一受保护要素：①非决策本身——决策 2c 的主题是 extras 边界，此半句谈的是主依赖卫生，且被写在 extras 列里（pytest 当时是主依赖），栏位错配本身即施工残留迹象；②无 why、无 trade-off（句中零理由）；③非被拒方案/反模式护栏——pytest 混主依赖不是考虑过又拒掉的方案，而是包化前 novaact 自带独立 venv 的顺手产物；真正非显然的那条护栏在同表第 93 行且不在候选跨度内、原样保留（「当前 venv 里能 import 到纯属 pytest 的传递依赖，生产路径必须自己声明」承载「别靠 pytest 传递依赖活着」的不变量）；④不变量由前半句承载（不依赖 gherkai-core、worker 讲协议零 core 依赖），改法完整保留含 0024 精确…


### docs/adr/0039-user-facing-surfaces-no-internal-references.md

- **P18**（第 39 行，approve）候选句：「搬家不是删：从使用者向文件移出的每条事实与踩坑，必须在对应 DEVELOPMENT.md 里找得到（实装时按旧文件逐字对照过）。」
  - 沉积判据：括注是一次性施工核对记录（「实装时……逐字对照过」），不承载 why / trade-off / 反模式 / 指针；前半句「搬家不是删……必须在对应 DEVELOPMENT.md 里找得到」才是不变量，删括注后它独立成立、约束力不减。与被保护的「内联证据」不同：这里对照的不是某个设计选择的支撑数据，而是「那一批搬家做过一遍人工核对」的过程流水，对未来读者/AI 不产生可复用判据。
  - 改法：搬家不是删：从使用者向文件移出的每条事实与踩坑，必须在对应 DEVELOPMENT.md 里找得到。
  - 复核员：逐要素证伪未能推翻提案。候选句被删部分仅括注「（实装时按旧文件逐字对照过）」：不含 why/trade-off/反模式·被拒方案（这些在同 ADR 第 50、57-59 行独立承载）；不变量在前半句、删后约束力不减；无任何指针（「旧文件」不点名文件/符号，删后不产生悬空引用，也不涉 journey/WP 编号）；非「曾/原/已被取代」框住的历史，只是一次动作的完成态；非带指针的有意重复；骨架测试通过——删后同段论证结构不断。唯一近似项「Accepted ADR 内联的自包含证据」不成立：无实测数据、无日期、无真跑结论，且不支撑「为何这样设计」（规则先验采纳），只是某批搬家的核对流水；对比同 ADR 第 24 行「实装时顺带的原则性修正：……撞出 stderr BufferedWriter 重入崩溃……（细节在 0024 终止契约）」，那条才是受保护的内联证据（具体故障事实 + 稳定指针），…

- **P19**（第 75 行，approve）候选句：「- 两条护栏测试的 docstring 指向本 ADR。」
  - 沉积判据：「对既有文档与 code 的影响」里唯一纯施工记账的一条：既非决策、非 why、非不变量，也不是指针（真指针在护栏节，那里逐个点名了测试文件路径），只记「实装那批顺手加了 backlink」。同一批次的第 73、74 条不同——它们记的是规则/被拒方案的落位（CLAUDE.md 压回规则、0037 被拒方案改指本 ADR），是跨文档单一真源映射，留。附带：该条的「两条」已随 test_skill.py 成为第三只护栏而失准，删掉正好消掉一个会持续漂的数字（若人判保留，则须一并改成不数数的说法，如「护栏测试的 docstring 均指向本 ADR」）。
  - 改法：删掉这一行（该节余下两条不动）。
  - 复核员：候选句（docs/adr/0039 第 75 行「- 两条护栏测试的 docstring 指向本 ADR.」）逐要素过筛后不承载任一受保护要素，属实装记账：①规范/决策不在此句——「被删掉的指针进紧邻注释或 docstring；docstring/注释不在本约束范围、鼓励保留 ADR 指针」写在第 27 行「面一·搬家规则」，对照的被拒方案在第 59 行，此句只是该规范一次落地的过去式陈述；②非精确指针——它不点名任何文件/符号，真指针在第 42-45 行「护栏」节（逐个点名 test_user_facing_messages.py / test_package_readmes.py / test_skill.py 及各自扫描面）与第 3 行 Status 头，code→ADR 反向链 grep「ADR 0039」即得，删后无导航损失；③无 why/trade-off/反模式/不变量语气（…


### docs/adr/0042-step-evidence-and-explain.md

- **P20**（第 241 行，approve_reduced）候选句：「- 真跑（跳板机；**先重传 Lambda asset + 推新 worker 镜像**，否则 cloud 档必然看不到 message / evidence、易误判成 bug）：」
  - 沉积判据：Draft 期的「待做真跑清单」四条子 bullet 已被同节前面的实测结论段逐条完整覆盖（本机档 line 225-229、cloud 档 line 231、submit 路径 line 233、后台队列真跑 line 235），且前者更详细、带数字与原文；括注里的部署 gotcha 已在「交付链」节 line 218-219 写明。它不承载决策 / why / 权衡 / 不变量 / 历史框定，只是被覆盖的计划层；子条 4 的「flush 后截图 URI 可取」还是决策一修订前的形态，留着会误导。
  - 改法：分三步，顺序不可颠倒（先保住护栏、再删）：

1) 第 217 行（「交付链」节头）改为下面这句完整句，把误诊警告落到其永久归属处：
`**交付链（不改 IaC 资源，但不重部署云端看不到——cloud 档跑不出 message / evidence，易误判成 bug）**`

2) 删除第 241-245 行整块（即「- 真跑（跳板机；…）：」表头及其四条子 bullet），不动 224-238 的实测结论段。

3) 第 240 行开头「- 单测：」改为「**单测护栏**：」，该行其余原文一字不动。
  - 复核员：逐句评候选句自身跨度（第 241 行）+ 核提案删除范围是否连带丢要素，结论：整块基本属 SEDIMENT，但括注里有一处误诊护栏必须先保住，故不整删而改为 approve_reduced。

不承载要素的部分（证伪失败，提案方判断成立）：
1. 「真跑（跳板机；…）：」这个 bullet 表头是 Draft 期「待做清单」的计划层标签。git 初版 214db19 该节标题为「## 验证（Accepted 前必做，结论内联到此处）」，正文只有 240/241 两条待做 bullet；此后 c7e7c1d / eb7ab9a / ec0187c / a58cd40 / 2cf0237 逐层把实测结论加在其上、标题改为「验证（已完成，结论内联）」，却没删旧的待做层——正是「被后续迭代覆盖却没删的旧描述层」。「跳板机」这一定位也已在 224 行「本机档（跳板机本机 run…）」保留。
2. 四…

- **P21**（第 206 行，approve）候选句：「**文档（反向链逐处列出，Accepted 前逐条核）**」
  - 沉积判据：「Accepted 前逐条核」是 Draft 期给自己下的施工指令，Status 头（line 3）已声明「影响面所列反向链（0024 / 0027 / 0029 / 0032 / 0037 / 0041 / CONTEXT）已逐条落」，指令已执行完毕；「反向链逐处列出」这半句仍有导航价值，保留。
  - 改法：**文档（反向链逐处列出）**
  - 复核员：候选句为「影响面」节的文档子标签。逐半句核:①「文档」= 子节结构标签、②「反向链逐处列出」= 导航框定,二者改法均保留;③「Accepted 前逐条核」不承载任一受保护要素——非决策本身(六项决策在「决策」节)、非 why/trade-off、非反模式/被拒方案、非不变量(该纪律权威源在 CLAUDE.md 文档纪律「引用方向单向」的「绑死 Status 头」条与 docs/doc-health-review.md「Status 头连带审计」节,0042 不是 owner 且此处未带指针)、非「曾/原/已被取代」框住的历史、非精确指针、非内联证据;删后论证结构不断(骨架功能全在保留的前两半),故为 Draft 期自下的施工指令 = SEDIMENT。git 层读证实:该括注随首个 Draft 提交 214db19(2026-09-10)一次写入、此后从未改动(git log -S 仅一条…


### docs/adr/0043-agent-skill-for-driving-gherkai.md

- **P22**（第 145 行，approve_reduced）候选句：「护栏实装中两处偏离设计已回写决策六：JSON 键真值集取契约页字段表**任一列**加散文行（首列-only 会把 `kind` / `ref` / `votes.yes` 等真键逼进「非键豁免表」）；fixture 绝对路径不变量只认已知机器根（`/Users` `/home` `/tmp` `/var` `/app` …）——「JSON 里以 `/` 打头的字符串一律算路径」会把 step 原文 `"/wiki/OpenAI"` 判成机器路径。」
  - 沉积判据：两条的结论**连同理由**已完整住在决策里：决策六第 69 行「真值集取契约页字段表**任一列**里的反引号键加「顶层 / 每项 …」散文行记的键（`report_refs[]` 行的 `kind` / `ref`、`votes` 的 `yes` / `total` 这类真键只出现在含义列，首列-only 会把它们逼进非键豁免表、语义反了）」，决策七第 85 行「曾试「JSON 里以 `/` 打头的字符串值一律算路径」，假红——step 原文 `Then 页面地址匹配 "/wiki/OpenAI"` 会以转义字串嵌进 `run_meta` / `jobs`」。验证节这句是「实装时发现偏离→已回写」的施工节奏叙事 + 同一事实的第二份完整重复（且措辞已微漂：这里只提「回写决策六」，第二条实际住决策七）。
  - 改法：把第 145 行 bullet 的**第二句**（自「护栏实装中两处偏离设计已回写决策六：」至行尾）整句替换为：

护栏实装中两处偏离设计已回写决策：JSON 键真值集取契约页字段表**任一列**加散文行（决策六）、fixture 绝对路径不变量只认已知机器根（决策七）——各自的反例与理由在那两条里。

该 bullet 第一句（`cli/tests/test_skill.py` 38 用例、`test_skill_install.py` 23 用例、全仓 1197 通过等实测证据）原样不动；决策六第 69 行与决策七第 85 行的原文一字不改（反例、机器根列举、「曾试…假红」的历史框定全部留在那里作权威）。
  - 复核员：逐要素核过，候选句（第 145 行 bullet 的第二句）确实承载受保护要素，但都不是唯一载体，且改法能全部保住：

① 决策本身 + 被拒方案/反例：「字段表任一列加散文行（首列-only 的反例）」的权威全文在决策六第 69 行（`report_refs[]` 行的 `kind`/`ref`、`votes` 的 `yes`/`total` 这类真键只出现在含义列，首列-only 会把它们逼进非键豁免表、语义反了）；「只认已知机器根 + 曾试『以 / 打头一律算路径』假红」的权威全文在决策七第 85 行，且那里更全——机器根列举是超集（`/Users` `/home` `/private` `/var` `/tmp` `/opt` `/app` `/workspace`）、还多一句判别原理「URL 路径与机器路径只有根目录名能分」，并已用「曾试」框成历史。故删验证节这份不丢任何 why…

- **P23**（第 159 行，approve_reduced）候选句：「评分者对评测集的批评（复合断言拆条、`--help` 不算执行、缺正向断言）留在 `evals.json` 的 notes 里待下轮。」
  - 沉积判据：这条「留待下轮」已被紧随的下一轮消化：第 160 行开头即写「评测集按第三轮评分者的批评收紧到 94 条断言（复合断言拆条、放行开关与投票判据正向化、禁绕过式修复、正则须匹配真实落地地址、禁留新 run 目录、「`--help` 与只读命令不算执行」统一）」——同一份批评在相邻两段各写一遍，前一遍只剩「当时还没做」的时间坐标，是逐层追加留下的过程编号式残留（第 169 行末尾的第四轮同款句同理，已被第 170 行「尺子 121 条断言…」消化）。
  - 改法：照原改法删 docs/adr/0043-agent-skill-for-driving-gherkai.md 第 159 行末句（「评分者对评测集的批评（复合断言拆条、`--help` 不算执行、缺正向断言）留在 `evals.json` 的 notes 里待下轮。」）与第 169 行末句（「评分者对尺子的新批评（断言 2 一类仍是四合一、缺「正则须匹配真实 301 终点」的机械判据、缺「不得把评测脚手架的空凭证当用户环境上报」）留待下轮。」），两处删后各自保留同段其余内容（169 行仍以「本轮零污染、CLI 哈希未变、无 run 读到别的会话记忆。」收尾）。附加约束：第 179 行末句的重写必须把 `evals.json` 的 `notes` 指针一并带上（它是长期文档里唯一出处），改后完整句为——「评分者对尺子的新批评（eval 1 的正则判据要加「裸 iana.org 须命中」、eval 16 的两条知识点拆开、eval 2 的条件式断言不改 feature 即白过）已逐条落进评测集（缺省集 122 条；每轮尺子改了什么逐轮记在 `evals.json` 的 `notes` 里），按新尺子的测量留待下一轮。零污染、CLI 哈希未变。」
  - 复核员：候选句自身跨度不承载任何受保护要素：它不是决策/why/trade-off/不变量，没有「曾/原/已被取代」的历史框定（「待下轮」是前瞻式过程坐标，正是 SEDIMENT 定义的「过程编号式残留」），也不含实测数据。三条批评逐条核对已被紧随的 160 行消化且 160 更完整（复合断言拆条 ✓；`--help` 不算执行 → 「`--help` 与只读命令不算执行」统一，是超集 ✓；缺正向断言 → 「放行开关与投票判据正向化」，evals.json 的 notes 记「eval 9/14」佐证同一项 ✓），且 160 另列三项 159 没写的，故 159 的清单本身是有损子集、不藏「提了但没做」的项；169 行末句同理被 170 行逐条消化（断言 2 四合一 → eval 1 拆条；301 终点机械判据 ✓；空凭证当用户环境 ✓，其中「0 字节假凭证」的具体证据在 179 行 ④ 保留）。…


## 三、主观发现待批（REDUNDANCY / SEDIMENT / OVERLAP / WHY-LEAK / BOUNDARY / UNCERTAIN STATUS）

- **S1** REDUNDANCY · docs/adr/0015-v1-positioning-smoke-not-regression.md:36 — 「已知边界」节第一条是同一事实在本 ADR 内的第三次完整重述，且与上文用词逐字重合，属可指针化的完整重复；本节另一条（第 37 行）已是纯指针形态，本条却把上文原话再抄一遍。
  - 证据：docs/adr/0015-v1-positioning-smoke-not-regression.md:30「**种类 B：柔性吞掉真实变更**…**v1.0 不解决，作为已知边界接受。**」与 :32「种类 B 不是 bug，是最左档定位的必然代价。」已把「最左档定位的必然代价」「接受」两处说全；:37「- 像素级回归见上「定位·不做」（含 Percy 理由）；精确色值/坐标见上「关键澄清」表。」证明本节的既有形态就是「列条目 + 指针」，不需要复述。
  - 提议：- **未点名不抓**（种类 B）：见上「两种"不确定性"——只治其一」。

- **S2** SEDIMENT · docs/adr/0042-step-evidence-and-explain.md:241 — 验证节末尾还留着 Draft 期的「待做真跑清单」四条，其内容已被同节前面的实测结论段逐条覆盖（且更详细），是被后续迭代覆盖却没删的旧层。
  - 证据：git show 214db19（Draft 建档）该节标题为「## 验证（Accepted 前必做，结论内联到此处）」，正文只有「- 单测：…」「- 真跑（跳板机…）：」两条计划；c7e7c1d 起把实测结论**前置**（prepend）到计划之上，eb7ab9a 把标题改成「## 验证（已完成，结论内联）」，计划清单一直没删。逐条覆盖关系：子条 1（Nova 失败断言 frames 非空/末帧 thought/vote=false）↔ line 225 本机档第 1 条；子条 2（Nova act 超时、frames == []、explain 退 0）↔ line 227；子条 3（Midscene Insight/Boolean thought + 截图被引用）↔ line 229；子条 4（Content-Type=image/jpeg 浏览器渲染、`--json` 可解析、cloud `s3://` 可读）↔ lin…
  - 提议：删掉第 241-245 行（「- 真跑（跳板机…」及其四条子 bullet）；第 240 行的单测清单保留但去掉计划语气，改为「**单测护栏**：两引擎映射函数对真产物 fixture（含 Midscene 的 error task、Nova 的 N 票）；best-effort 路径（抽取 / 上传抛异常 → `step_done` 照发、无 evidence ref、status 不变）；serialize round-trip 带非默认 step message；`explain` 本地 / 云端两档读取、`record_missing` 与三种 `evidence_missing`、多命中 `--scenario` + `--step`、退出码；cloud 档 skew 三态；契约护栏含 evidence 夹具。」

- **S3** SEDIMENT · docs/adr/0029-engine-artifacts-to-s3.md:69 — 章节标题的「现在做」与紧随其后的「第一期实现定论（subprocess 预演环境敲定，已实现）」互相打架，是施工时态残留；第 78 行「第一期真做时把下面几点从"待定"钉死（原"留口子"里对应项标状态）」同样是描述编辑动作的施工句。
  - 证据：同文档第 76 行标题「## 第一期实现定论（subprocess 预演环境敲定，已实现）」、Status 头（第 3 行）「上传能力按「第一期实现定论」节**已在该预演环境实现并验证**」——第一期早已完成，「现在做」是 Draft 期坐标。第 78 行的「原"留口子"里对应项标状态」讲的是「我改文档时给留口子条目加了状态标记」这一编辑动作，不承载决策/why/权衡/不变量；留口子节（第 100-105 行）的删除线条目本身已自明。
  - 提议：第 69 行改为「## 分期：上传第一期（subprocess 预演环境落地，已实现）/ Fargate 增强（未来）」；第 78 行改为「下面几点是第一期敲定的定论（「留口子」里对应项已标状态）：」

- **S4** OVERLAP · docs/guides/execution-and-reconciliation.md:126 — 「退出码按命令分工」按索引表归 `verdict-model.md` 所有，本篇只应给链接；这条把 submit / status / status --wait 三条命令的 0/1/2 又完整讲了一遍（连「未到终态退 0 是查询成功」「查不到 run 退 2」都复述），且不带指向 owner 篇的指针——两篇各写一份，日后必各自漂。
  - 证据：docs/guides/README.md:3「**一个机制只有一篇是 owner**，其余篇只给链接」；README.md:8 verdict-model 行的「拥有的主题」含「退出码按命令分工」；被复述的原文在 docs/guides/verdict-model.md:127-144（§5 退出码表的 submit / status / status --wait 三行 + 「CI 该接哪一条」三条）。本篇 §8 延伸阅读（第 207 行）已有「判定怎么算出来（四层归约 / 七个状态 / 各命令退出码语义）→ verdict-model.md」这条正确形态的指针。
  - 提议：- **退出码分层**（CI 接线最易建错心智）：`submit` 的退出码只表示「提交成功与否」、**不是判定**；判定退出码由 `status --wait` 等到终态后给。根因：CLI 脱离后不再有内存里的判定终值——各命令退出码的完整分工见 [`verdict-model.md`](./verdict-model.md) §5（本篇不重复它的表）。

- **S5** OVERLAP · docs/guides/artifacts-and-evidence.md:90 — 「退出码按命令分工」的 owner 是 verdict-model.md（归属表明写），这里把 `status` 与 `explain` 的退出码规则完整重述了一遍且不给该篇指针——两处各写一份必各自漂。
  - 证据：`docs/guides/README.md:8` 归属表把「退出码按命令分工」列为 verdict-model.md 拥有的主题；`docs/guides/verdict-model.md:125-137` 的「退出码：每条命令回答的是**不同的问题**」表逐命令给出同一批规则（`status`（不带 `--wait`）「查到了——含未达终态」、`status --wait`、`explain`「从不表判定 / run 判 failed 也退 0 / 参数写错…退 2」）。本篇 §4 的段落尾指针（artifacts-and-evidence.md:103）只把「判定语义本身（各态怎么聚合、`shortcircuited` 判据）」和「`--wait` 谁在推进」路由出去，退出码这一段没有任何指针，等于第二份权威。（code 侧两处描述都对：`cli/gherkai_cli/__main__.py:1326-1331` 的 `…
  - 提议：把该句压成指针 + 只留操作性告警：「读这三步时别把 `explain` 当判定门：它**从不表判定**（只用 0 / 2，哪怕一条证据都没有也退 0），判定码只由 `run` 与 `status --wait` 给——各命令退出码分别在回答什么见 [`./verdict-model.md`](./verdict-model.md)「退出码」节。detached run 未到终态时判定明细还没落地，`explain` 会打一行「先用 `status --wait`」并退 0。」（同时删去后面那句重复的 detached 句，避免留两遍）

- **S6** OVERLAP · docs/guides/deterministic-step-lifecycle.md:85 — 「提交侧 variant 三环解析」的完整枚举在两篇 guide 里各写了一份，而归属表把这个主题判给了 cloud-backend-carriers；两份各自漂移是时间问题（本篇要立的点其实只是末句「不看 steps 内容」，三环细节是铺垫）。
  - 证据：docs/guides/README.md:11 把「提交侧 revision 解析与退休规则」列为 cloud-backend-carriers.md 拥有的主题（同行规则：「**一个机制只有一篇是 owner**，其余篇只给链接」，见 README.md:3）；owner 侧的完整版在 docs/guides/cloud-backend-carriers.md:95「preflight 把 `--worker-variant`（缺省 = 默认指针）解析成**本 run 用到的每个引擎**的 task-def revision，三环校验：SSM 有当前版本的映射 → 该 revision 仍 `ACTIVE` → 该 digest 在 ECR 仍在。任一环缺即退 2，**绝不回落**默认指针 / family 最新 ACTIVE / 模板 revision。」两处所述与 code 一致（runtime/gherkai_runt…
  - 提议：cloud 侧的关键是**镜像是唯一载体**：你的 `steps/` 靠三行 Dockerfile（`FROM <基底>:X.Y.Z` + `COPY steps/ /app/steps` + `ENV GHERKAI_STEPS_DIR=/app/steps`，模板唯一真源在 [ADR 0038](../adr/0038-worker-image-delivery.md)「概念模型」节）烙进一个 **variant**，由部署方 `gherkai deploy push-worker` 推上去。提交时 `compose.resolve_worker_variant` 做三环存在性/一致性校验（三环各查什么、缺哪一环怎么报，见 [`cloud-backend-carriers.md`](./cloud-backend-carriers.md) §5）——**一个字节的 steps 内容都不看**。

- **S7** WHY-LEAK · docs/guides/cloud-backend-carriers.md:102 — 这一条把 ADR 0038 的**被拒方案理由**（为什么不加 untagged 过期规则）连同**被接受的代价**（untagged 层随重推永久增长）整段搬进 guide 正文，正是 guides 层不该复述的两类 why；同一节末的权威行已给了指针，形成双源。
  - 证据：CLAUDE.md 文档纪律 guides 条：「**只讲 how、不复述 why**（决策理由/权衡/被拒方案留 ADR，guide 只给指针）」。ADR 侧同一内容在 docs/adr/0038-worker-image-delivery.md:32：「**护栏**：这条正确性依赖 ECR 保留被顶掉 tag 的 untagged 镜像（在跑 run 的旧 revision 按 digest 指着它），故 ECR 仓库**不设 untagged 过期的 lifecycle 规则**；代价是每次重推永久留一层 untagged 存储、随重推次数增长——记为已知运行期成本」，且 0038「被拒方案」节收了这条；本节第 105 行的权威行已写「（含被拒方案：RunTask 传 family、缺字段回落模板、ECR untagged 过期规则）」。code 侧事实本身无误（deploy_aws/gherkai_deploy_aws/…
  - 提议：- **ECR 仓库不设任何 lifecycle 规则**——在跑 run 的旧 revision 按 digest 指着被重推顶成 untagged 的那一层，所以这两个 repo 上**别加 untagged 过期规则**；随之而来的 untagged 层增长是已知的存储成本（为什么这样定、代价怎么记在案，见本节末权威行 ADR 0038）。

- **S8** DEADLINK · docs/REFERENCES.md:15 — 指针没给路径：这份「配方」是 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`，但「spike 配方」四个字在仓库里 grep 不出该文件，而 REFERENCES 的全部价值就在指针可直达（同文件 41 行同类内点就给了完整路径）。
  - 证据：grep '配方' 全 docs/：docs/REFERENCES.md:15 与 docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md:30 用无路径简称，docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md:19 与 engines/midscene/DEVELOPMENT.md:23 给的是完整路径 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md`。该文件 §7 确实存在且正是此内容（第 109 行 `## 7. 合体实测…`，其下 117 行 `### ⚠️ 关键坑…：createOpenAIClient → 隔离 ModelConfigManager`），故只是指针不可直达、不是断链。
  - 提议：  - 隔离 ModelConfigManager：`@midscene/core .../agent/agent.js`（传 createOpenAIClient/modelConfig 即切隔离，见 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md` §7）

- **S9** STALE · docs/REFERENCES.md:21 — Nova Act 节的一手来源停在 GitHub README + Playground 那一刻的世界：AWS 现已有官方用户指南（含 HITL 实现、workflow/IAM 面），而它没被登记——恰是 ADR 0004/0007 要查证的两块。
  - 证据：`curl -L https://docs.aws.amazon.com/nova-act/latest/userguide/` → 200；被引的 README 自己就把实现细节外链过去（`https://raw.githubusercontent.com/aws/nova-act/main/README.md` 第 512 行「Please refer to the Amazon Nova Act User Guide documentation on HITL … /nova-act/latest/userguide/hitl.html#implementing-hitl」）。docs/adr/0004-novaact-iam-auth-via-workflow.md 与 0007 全文零外链，查证只能靠本节。
  - 提议：在 Nova Act 节 21 行下补一条：
- https://docs.aws.amazon.com/nova-act/latest/userguide/ — 官方用户指南（HITL 实现、workflow definition 与 IAM 路径、SDK 行为的一手权威；README 只给上手面）

- **S10** REDUNDANCY · docs/REFERENCES.md:49 — 一节吞了 33 条（51–83 行）、占全文近四成，且混装两套互不相干的主题——发行打包（uv / PyPI / npm / attestation / 占名）与镜像·ECS 交付（镜像引用语法、GHCR/ECR、RunTask 与 task-def、Fargate 架构与定价、SSM、moby RepoDigests）；对 AI 检索，节标题是唯一的粗粒度过滤器，两个 ADR 的证据基座挤在一个标题下等于没有过滤。其它各节都是 3–6 条。
  - 证据：docs/REFERENCES.md 51–83 行共 33 条 bullet；其中 51–67、71–75 属发行打包（uv/PyPI/npm/PEP/homebrew/CDK 前置/同类 CLI 抽样），68–70、76–83 属镜像与 ECS 交付。ADR 侧也是两篇分治：docs/adr/0037-distribution-and-packaging.md:24 只把「业界现状」一手来源登记到本节，镜像交付面归 docs/adr/0038-worker-image-delivery.md。
  - 提议：把 49 行一节拆成两节，条目按归属搬（不改条目文字）：
`## 发行与打包（见 ADR 0037）` ← 现 51–67、71–75 各条（uv / `tool.uv.sources` / `uv build`·`uv publish` / attest-action / uv#9811 / uv-dynamic-versioning / clai 先例 / trusted publishers / 发行名与 import 名 / PyPA 推荐与 pipx / pypistats / uv 托管 CPython / PEP 685·541·740 / `core` 僵尸包 / npm scope 与争议政策 / 同类 CLI README 抽样 / Node `module.register` 与 tsx / homebrew 门槛 / CDK 需 Node.js / dagster chart / prefect 版本兼容 / chalice·metaflow IaC 对照）
`## 镜像与 ECS 交付（见 ADR 0038）` ← 现 68–70、76–83 各条（镜像引用语法 / GHCR / ECR 与 Docker Hub 拉取 / RunTask 与 ContainerOverride / Deregister·Delete task-def / Fargate `runtimePlatform` 与定价 / ECR push 最小权限 / Fargate ARM64 与 task-def 资源级权限 / Describe·RegisterTaskDefini…

- **S11** BOUNDARY · cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md:93 — 随包发到使用方项目的契约副本里留着「推进器」「投影」「definition」这几个内部机制名——使用方 agent 无从解析（仓库里没有它可读的定义），属产品面禁内部指代的射程；护栏禁词表恰好没收这几个词，故机械项照不出。
  - 证据：同文件 line 91「job 已被认领时 run 级仍可能 `pending`（投影滞后一拍）」、line 94「`claimed_at`（被推进器认领的时刻…）」、line 11 / 20 / 50 / 66 / 67 的「definition」。cli/tests/_doc_rules.py:29-33 的 FORBIDDEN 只收 ADR / 决策 N / 不变量 / 定位链 / 被拒方案 / 重议闸门 / 实测项 / 接缝契约 / 模块头 / 组合根，不含这几个词；tools/render_skill_contract.py:59-61 的 FORBIDDEN_REWRITES 目前只登记了一条（「命中定位链的哪一级」→「命中 worker 查找顺序的哪一级」），说明这几个词是漏筛、不是有意保留。
  - 提议：改手写源 docs/guides/cli-json-contract.md 或给 tools/render_skill_contract.py 的 FORBIDDEN_REWRITES 补三条产品语言替换，再重跑生成器（副本不能手改，test_skill.py 断言逐字节相等）。建议替换：「已投影的事件水位（诊断用）；仅经推进器投影写过的 run 有」→「已处理到的事件水位（诊断用）；仅由后台推进写过的 run 有」；「（投影滞后一拍）」→「（run 级状态比 job 级晚一拍）」；「被推进器认领的时刻」→「被后台推进认领的时刻」；「`run_meta`（definition）」→「`run_meta`（提交时定死的这批任务本身）」。

- **S12** STATUS · docs/adr/0027-runreport-aggregation-index.md:3 — UNCERTAIN（交人裁定）：0027 的「消费端只当 URI 用、不 stat / open」这条操作性规则被 0042 按层收窄、「trajectory 内部结构化提取」留口子也被 0042 填上，正文两处都已就地改写并反向链，但 Status 头是裸 Accepted——本仓遇到同类情形（0030「重议」条被 0034 落地、0036 查询面被 0037 追加、0041 闸门被 0042 落地）的惯例都是在 Status 头追加一句反向链，0027 是唯一例外，只读 Status 头的人/agent 看不出它已被 0042 动过。
  - 证据：docs/adr/0042-step-evidence-and-explain.md:151-155 决策五「与 0027 的关系：铁律不破，一条消费端规则按层收窄，一个留口子用对的方式填上」，并说「0027 该条原地改写并反向链本 ADR」——已落（docs/adr/0027-runreport-aggregation-index.md:26 与 :168）。对照惯例：0030:3「Accepted —— 本 ADR「重议」条预告的…已由 [0034] 落地」、0036:3「Accepted（`plan` 标注降级的例外与 `--steps-dir` 查询面由 [0037] 决策 4 追加）」、0041:3「…本 ADR「重议闸门」失败证据机读化一条已由 [0042] 落地」。判断边界：0042 明确定性为「收窄」而非反转、且铁律未破，故不建议改成 Partially-superseded——只是 Status 头缺那句指针。
  - 提议：把 Status 行改为：> **Status:** Accepted —— 归集索引语义/形态/扩展性契约与不透明搬运铁律不变；「消费端只当 URI 用、不 stat / open」一条由 [0042](./0042-step-evidence-and-explain.md) **按层收窄**（`model / wire / schedule / ReportStore` 永不解引用不变，皮层 `explain` / `read_resource` 只对 `kind == "evidence"` 的自有 schema 解引用），留口子「trajectory 内部结构化提取」亦由其落地（位置在 worker）。（正文两处已就地改写并反向链。）


## 四、红线复核否决的提纯提案（存档不落改）

- docs/adr/0030-realtime-persistence-seam.md:3 「已由 [0034](./0034-detached-batch-reconciler.md)（无状态跑批，reconciler 直写 RunState）落地：`RunState` 投影带 `high_water_mark` 条件写、finalize 单独条件写（见下「重议」条反向链）。」— 否决理由：候选句承载红线护栏点名保护的「带指针的有意重复」＋决策级事实，且提案的核心前提（「零距离完整重复」）事实错误。

一、不是完整重复，是已压到名字级的带指针简短重述。被删的只有两个机制名（"`RunState` 投影带 `high_water_mark` 条件写、finalize 单独条件写"）；权威处（第 223 行「重议」条）另有条件表达式（`:hwm >= 库中 hwm`）、异常名（`ConditionalCheckFailedException`）、终态语义（状态机非终态→终态）、"无需 lease 租约"与真 DDB 实测结论——这些一概只在 223 行。护栏原文："有意重复 ≠ 冗余……跨切面事实带指针的**简短**重述是可读性设计。只压『同一事实多处**完整**重复且已漂移』的。" 候选句既不完整、也未漂移（第 3/129/219/223 四处措辞互相一致），恰落在保护面而非压缩面，且它句末已自带指针正是该保护形态的特征、不是"因为有指针所以可删"的理由。

二、承载决策本身。头部前半句陈述预告方案"需 owner/lease + 条件更新"，后半句的机制名承担"实际兑现形…

- docs/adr/0034-detached-batch-reconciler.md:234 「同步 `run` 路径仍用现驱动循环（两种驱动模型并存，按命令分流）。」— 否决理由：候选句承载三项受保护要素，且都在本句自身跨度内，非从邻句继承：

**① 它不是「完整重复」，而是红线明文保护的「带指针的简短重述」。** 第 48 行是权威完整版（`run` 走 `schedule()` 的进程内 ThreadPoolExecutor 驱动循环、**不触 `reconcile.tick`**、故「共享同一 reconciler」只在 `submit`/`status`+kicker/reconciler Lambda 四宿主成立、不含 `run`）；本句只有一句 24 字的浓缩版，且**与第 48 行零漂移**（我对照 `core/gherkai_core/schedule.py`：`ThreadPoolExecutor`/`as_completed`/`abort_flag`/`_stop_all` 全在，两处陈述与 code 都一致）。红线只允许压「同一事实多处**完整**重复**且已漂移**」的，两个条件本句都不满足。提案方把「第三次提及」当成「第三次完整陈述」，是判据误用。第 232 行 (b) 条也不构成第二次陈述——它讲的是「核心与接口要动」，通篇没说 …


## 五、对抗验证驳回的客观发现（存档）

- docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md:23 — 主张：「换模型要改哪儿」这份清单只列了 2 类改动点，漏掉真值集里另外一整类：逐字点名 model id 的使用者面文档与随包发行的 agent skill（共 6 处），照此清单换模型会把旧 model id 留在 PyPI/npm 页面与使用方项目里。
  - 驳回：quote 确在 docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md:23（全文仅 23 行，该括注在末段「待观察（上游代际）」句尾）。提交者列的 6 处文档 + 1 处护栏我逐条亲核，全部存在：README.md:60、cli/README.md:21、engines/midscene/README.md:21 与 :105、engines/midscene/DEVELOPMENT.md:20、cli/gherkai_cli/skills/gherkai/references/engines.md:14、cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md:43、deploy_aws/tests/test_stack.py:362（`assert "foundation-model/qwen.qwen3-vl-235b-a22b" in r`）；清单已列的三处也核实无误（engines/midscene/src/lib/agentcore-sigv4.mts…

- docs/adr/0018-generic-steps-capability.md:20 — 主张：0018 正文说取数/取串两条原语已被删，但原语表里这两行不带任何「已删」标记，而同表的另一条已删项（AI 否定断言）却标了——表内标记不对称，读表的人/AI 会把 `aiNumber`/`aiString` 当现役原语。
  - 驳回：quote 确实在 /Users/lzy/workspace/yaozhou/docs/adr/0018-generic-steps-capability.md:20（:21 为取串行），提交者对 code / CONTEXT 的转述我逐条核过、全部为真；但**语境已用「已删」显式框住这两行**，落在红线护栏「历史记录 ≠ 过时」射程内，故「读表会当现役原语」这个主张不成立。

真值侧（我亲自核到的）：
1) 生产 code 只有一条 AI 断言路径：/Users/lzy/workspace/yaozhou/engines/midscene/src/worker/run-scope.mts:660-667（`if (keyword === "Then")` → `await agent.aiBoolean(instr)` 逐票）与 /Users/lzy/workspace/yaozhou/engines/novaact/gherkai_worker_novaact/run_scope.py:392-400（`nova.act_get(instruction, BOOL_SCHEMA, …

- docs/adr/0028-transient-network-ssl-resilience.md:132 — 主张：同上：「r1」是无定义的会话内跑批标号，且第 134 行「实测：r1 3 次重试…」靠它回指同一次真跑——未来读者无从解析，须换成自明的事件描述（同一次真跑用「同一次真跑」回指）。
  - 驳回：① quote 核实：/Users/lzy/workspace/yaozhou/docs/adr/0028-transient-network-ssl-resilience.md:132 确有「（如实测 r1 连撞 3 次瞬时故障、第 4 次成功）」，:134 确有「实测：r1 3 次重试（光 attempt 1 的 CDP 超时就 30s）+ Nova 会话建立固有延迟（~40s）使总墙钟 249s 远大于两 scope 墙钟之和 67s」。语境是「留口子不实现」下的「已知边界 + 增强方向」，非历史框定；ADR 头 Status 为 Accepted（:3）。

② 真值核对推翻了主张的事实基础——「r1」不是会话内跑批标号，而是仓库内长期存在的 **scope id**：
- /Users/lzy/workspace/yaozhou/features/engine_routing.feature:5 `@engine:midscene @scope:r1`、:10 `@engine:novaact @scope:r2`。该 fixture 已被 git 跟踪（`git ls-fi…

- docs/adr/0043-agent-skill-for-driving-gherkai.md:179 — 主张：这三条批评已经落进评测集（评测集自己的 notes 明写「第五轮后尺子备忘已落」、缺省集断言 121 → 122），ADR 仍写「留待下轮」，与评测集真值不一致：读 ADR 的人会以为尺子还没改、可能重复改一遍。
  - 驳回：quote 确实在 /Users/lzy/workspace/yaozhou/docs/adr/0043-agent-skill-for-driving-gherkai.md:179 末句，逐字符一致；提交者引的评测集真值我也亲自核了，全部对得上：/Users/lzy/workspace/yaozhou/skills/gherkai-evals/evals.json 的 `notes` 末句确有「第五轮后尺子备忘已落…（缺省集 122 条）」；eval 1 的 expectations[2]（不是提交者说的 [3]，索引报错一位、内容在）含「对 https://iana.org/domains/example（裸主机）须命中」；eval 2 的 expectations[6][7][8] 三条已从「如果改了 feature：…」改成无条件的「把改法落盘到 features/wiki_search.feature（不只是口头建议）」等；eval 16 的 expectations[3][4] 已拆成「步号口径」与「Background 的执行语义」。我自己用 python 统计非 opt…

- CLAUDE.md:19 — 主张：例外清单已跨出 `docs/`（含各包 `README.md`/`DEVELOPMENT.md`），却漏了同属「靠通行惯例被认出的全大写入口文件」的 `SKILL.md`——Agent Skills 规范强制此名，随 ADR 0043（2026-09-14 Accepted）入库时这条没跟着补。注：kebab-case 规则本身自述「全 `docs/` 通用」，SKILL.md 在 docs/ 之外，故是清单一致性而非当前违规。
  - 驳回：三条独立核到的真值都不支持 STALE。① 规则射程：CLAUDE.md:19 自述「全 `docs/` 通用」，SKILL.md 位于 cli/gherkai_cli/skills/gherkai/（发行树、非 docs/），提交者自己也承认「是清单一致性而非当前违规」——文档没有对 code 作出任何虚假描述，不满足 STALE 定义（描述与 code 不符 / 旧世界未标历史）。docs/ 内真值集侧清单完整：git ls-files docs/* 全量 → 全大写仅 docs/REFERENCES.md 与 docs/guides/README.md，均已覆盖；清单点名的 7 个文件（根 README.md / CONTEXT.md / CLAUDE.md / DEVELOPMENT.md + cli、core、runtime、deploy_aws、engines/midscene、engines/novaact 的 DEVELOPMENT.md）全部存在，无 DEADLINK。② 「随 0043 入库时漏补」不成立：git log -L 19,19:CLAUDE.md 仅命中…


## 六、已落地的客观发现（CONFIRMED，按文件）

共 119 条：{'CONTRADICTION': 20, 'STALE': 87, 'DEADLINK': 8, 'STATUS': 4}。落地结果：applied 118 / skipped 2 / 跨文件 6。

- docs/adr/0016-execution-architecture-core-lib-run-model.md：10
- docs/adr/0024-worker-core-protocol.md：9
- CONTEXT.md：9
- docs/adr/0037-distribution-and-packaging.md：5
- docs/adr/0027-runreport-aggregation-index.md：5
- docs/adr/0042-step-evidence-and-explain.md：5
- docs/doc-health-review.md：5
- docs/adr/0038-worker-image-delivery.md：4
- docs/adr/0043-agent-skill-for-driving-gherkai.md：4
- docs/adr/0033-iac-aws-backend-and-composition-wiring.md：4
- docs/adr/0034-detached-batch-reconciler.md：3
- docs/REFERENCES.md：3
- tools/e2e_harness.md：3
- docs/adr/0025-plan-module-feature-to-jobs.md：2
- docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md：2
- docs/adr/0030-realtime-persistence-seam.md：2
- docs/adr/0029-engine-artifacts-to-s3.md：2
- docs/adr/0041-agent-facing-cli-affordances.md：2
- cli/README.md：2
- .github/workflows/README.md：2
- engines/midscene/README.md：2
- engines/novaact/README.md：2
- cli/DEVELOPMENT.md：2
- DEVELOPMENT.md：2
- docs/guides/verdict-model.md：2
- cli/gherkai_cli/skills/gherkai/SKILL.md：2
- docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md：1
- docs/adr/0004-novaact-iam-auth-via-workflow.md：1
- docs/adr/0010-spike-as-apples-to-apples-benchmark.md：1
- docs/adr/0002-midscene-not-driven-by-gpt55.md：1
- docs/adr/0009-maximize-aws-hard-constraint.md：1
- docs/adr/0001-scope-limited-to-english-ui.md：1
- docs/adr/0013-cross-engine-sharing-boundary.md：1
- docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md：1
- docs/adr/0028-transient-network-ssl-resilience.md：1
- docs/adr/0035-local-app-testing-via-tunnel.md：1
- docs/adr/0040-consumer-role-model-and-terminology.md：1
- docs/adr/0039-user-facing-surfaces-no-internal-references.md：1
- README.md：1
- deploy_aws/README.md：1
- deploy_aws/DEVELOPMENT.md：1
- docs/guides/execution-and-reconciliation.md：1
- docs/guides/cli-json-contract.md：1
- docs/guides/deterministic-step-lifecycle.md：1
- engines/midscene/spikes/SIGV4-FETCH-RECIPE.md：1
- CLAUDE.md：1
- skills/gherkai-evals/grader-prompt.md：1
- cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md：1
- docs/adr/0032-fargate-execution-environment.md：1
- docs/adr/0017-cloud-execution-fargate-over-runtime.md：1

未落（修补员判前置事实已变或 quote 不在）：
- docs/adr/0039-user-facing-surfaces-no-internal-references.md [2]：revised_fix 本身就判定这是 code 漂移而非文档陈旧，明确要求「移交 code-health（不改文档）」，故本文件无可落项；改动面为 cli/tests/test_user_facing_messages.py 的 FORBIDDEN_TS，已记入 cross_file。ADR 该句（含「曾因 TS 表更松漏掉一处组合根装配错误」的护栏理由）只在人反向裁定「TS 面只需覆盖子集」时才由人显式改，不由本轮复盘代改。
- /Users/lzy/workspace/yaozhou/docs/adr/0009-maximize-aws-hard-constraint.md [1]：revised_fix 的处置结论本身就是「报人裁定，本轮不落 0009 决策面改动」，并明写「裁定前 0009/0037 一字不改」；它未给出单一可落地的替换文字，只给了两条互斥候选分支（A：0009「决定」段末尾加适用面句 + 0037 补指针；B：0009 不动、改 0037 登记例外或把 registry 重议回 ECR Public），选哪条取决于人对「维护者发布通道是否在 0009 射程内」的裁定；任选其一落下去就是复盘替人改决策（0009 自陈「不是可权衡的偏好」）。前置事实已亲验仍成立（0009:15 quote 在位、Status 仍 Accepted、例外清单仍只 0035…

## 七、具名提纯审计记录（审计集 43 ADR + CONTEXT = 44 份）


### CONTEXT.md · none（0 提案）
- 层读：git log --oneline a97f912..HEAD -- CONTEXT.md = 3 层：e7515ff（4 行：标题与首段定位词「框架」→「工具」+ 首段补「命令行 + 运行时 + 引擎 worker + 部署包」判据、line 53/105 两处「框架」→「gherkai」）、14f5989（2 行：line 47 报告产物模型整段重写只为插入 `kind=evidence` 分句；line 168 把 skew 闸门命令表「run/submit/status」改成「run/submit/status/explain」并加「（explain 无 preflight，先于任何云端读）」括注）、8470fa0（+4 行：新增「agent skill (gherkai skill)」词条，纯新增、未动邻条）。三层 git show 差异逐条读毕：全部是整句原地替换或新增词条，**无一处留下被后层覆盖的旧描述层**，也无「先做 X 后改成 Z」的叠加括注。再整读当前 169 行全文。
- 判无依据 / 说明：层读史实：三层增长（e7515ff/14f5989/8470fa0）全为整句替换或新词条追加，14f5989 对 line 47 是整段替换（旧句未残留在下一行）、对 line 168 是就地扩表，8470fa0 只在 line 89/95 之间插一条新词条——没有沉积层可摘。整读全文时四句险成候选、各因具名要素留下：① line 100 尾「历史：早期无 step 短路时，"error 后的 failed"曾靠"按 status 顺序猜"加旁注（渲染层缓解）；现已升级为执行层短路 + 读 `shortcircuited` 精确判定。」= 用「早期/现已」框住的旧世界（红线「历史框定」），且它解释了为何 `shortcircuited` 必须是独立第二维；② line 146 _Avoid_「曾是 `ScheduleOpts` 参数、不进 definition，detached 推进器就拿不到它——已退役」= 被拒方案 + why（预算不进 definition 就到不了推进器），删掉即失去护栏；③ line 161 头「曾经的形态——`tools/build_push_workers.py` 全量 build、task-def 焊死 `latest`、RunTask 传 family——已退役。」= 施工生平已删（`git ls-files | grep build_push` 零命中，脚本确已不在库）、只留反模式清单，且 line 162 _Avoid_ 正是配套护栏「task-def 引用 `latest` 或 RunTask 传 family（任何一次 push 都会劫持默认）」；④ line 153 头「（`repo_root()` 已整体退役，ADR 0037 决策 3。）」= 指向已删符号的历史框定 + 支撑「dev 与分发同一条链」这条不变量。全文唯一带过程编号的一句 line 25「M1–M5 的工程推进」不作提纯提案计数——它已按客观项 STALE 上报（里程碑轴被版本切分取代，其余文档均写「原里程碑 M5」），修法是校准措辞而非删句。

### docs/adr/0001-scope-limited-to-english-ui.md · none（0 提案）
- 层读：git log --oneline a97f912..HEAD -- 该文件：1 层（8470fa0「ADR 0043 实施」）。--stat = 1 insertion(+) / 1 deletion(-)，git show 读差异：只把「影响」首条尾部加了「；随 CLI 发行的 agent skill 在 `references/engines.md` 同承载这条口径、诊断规则与三条出路（同为使用者面，[0043]）」一句，原句逐字保留、无旧层被覆盖。随后整读当前 69 行全文。
- 判无依据 / 说明：最险成候选 = 第 15 行「**实测（两引擎都有）**：Midscene 在中文 UI 上直白断言 120 票一致且正确（另有边缘题 5 票 3/5 抖动，见下）；Nova Act 的中文词语包含类断言 0/45 系统性假阴性。」——「0/45」这个数在第 8 行（决策）、第 15 行、第 56 行（结论）三处各出现一次，形态上是同一数字的完整重复。留它的受保护要素在该句自身跨度内：这句是「为什么这样划（按证据强度排）」第 2 档的**全部实质内容**（第 1 档=AWS 支持契约、第 3 档=AI 断言语义面），抽掉数字该档只剩标题、证据强度排序就断；同句尾「**功能性可跑 ≠ 同等可靠**（[CLAUDE.md](../../CLAUDE.md)「绿≠对」的分流判据）」是本 ADR 判据的显式援引。次险 = 第 31 行「另见形近字错读（「格希凯」读成「格希列」）。」，读着像随手记的观察，实为首次实测的自包含证据，支撑「读得出中文 ≠ 中文文本级精确」这条与第 56 行同形态的结论。层读之外另做了内部一致性核对（若有旧层残留最易在此漏出）：Status 头「两引擎各 125 票」= 量化表 3 断言×10 票×3 次 = 90 + 诊断表 7 题×5 票 = 35，两表逐格相加吻合；Nova「0/45」= 量化表 0/10×3 + 诊断表三条中文词题 0/5×3，亦吻合——无过时数据层。

### docs/adr/0002-midscene-not-driven-by-gpt55.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0002-midscene-not-driven-by-gpt55.md → 零命中（未动）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：none（0 提案）——「窗口内唯一一层（cab6a8e）是句内插入一个带跨文档指针的定性括注，未在任何旧句上叠加、未留双层；最险成候选 line 21「诚实存档（本 ADR 的判断反复）：Responses-only → 中途误判……」形状虽像施工节奏，但同句尾承载反模式「只认响应 body，不认 HTTP 状态码」、其证据锚就在紧上方 line 19，故留。」

### docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md → 零命中（未动）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：none（0 提案）——「区间 4 层全部读差异，两次都是整句替换/整句移动、旧层零残留（853d730 把原型期「视觉通道尚未实证」层就地换成「此后已端到端真验」；015585e 把处置规则句整句移到「未实测项」段、现文仅一份）；最险成候选是 06-22 本账号实测段，留它是因为它是 Accepted ADR 内联的自包含证据 + 给出前段没有的三条结论（模型访问已授予 / 协议可用 / 本账号 region 可达），删掉会让 0008 的互链悬空。」

### docs/adr/0004-novaact-iam-auth-via-workflow.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0004-novaact-iam-auth-via-workflow.md → 零命中（未动；第五轮的 2 条提案已随 a97f912 落地，现文 line 20-21 即落地后的形态）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：proposal（2 提案，均 approve_reduced 并已于 a97f912 落地）——[P56] 把「注册可用 CLI 或 boto3（等价）」的 fenced CLI block + 「但…无需手动 CLI 前置」转折改成正述的 `ensure_workflow_definition()` 一句（逃生舱在 docs/REFERENCES.md:41-42 与 engines/novaact/DEVELOPMENT.md:42 仍在，不丢操作路径）；[P57] 把无 why 的「生产化时也可改由 IaC / 部署脚本统一管理。」换成带闸门与代价的一版（保住「definition 归属」这条设计轴的路标，因紧邻下段为 worker 自建付代价、并被 0028 当幂等依据）。

### docs/adr/0005-single-shared-feature-file.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0005-single-shared-feature-file.md 零命中（同一条命令同区间在 0001/0015 各命中 1 层，作对照证明区间与路径写法有效）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。摘要：第五轮判 none（0 提案）——最险成候选是第 20 行「同一句自然语言 step 同时驱动了两个不同语言/不同大脑的引擎——本框架立身之本落地。」，与第 9 行立论用词重合但它是「✅ 已实测（M2 起）」段的结论句（把第 9 行的主张变成已验证），且整段被第 15 行演进注显式历史框定，属 Accepted ADR 内联的自包含证据；区间内 2 层都只改第 15 行的 code 指针、无内容增长。

### docs/adr/0006-form-a-two-subprojects-no-orchestrator.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0006-form-a-two-subprojects-no-orchestrator.md 零命中（同一条命令同区间在 0001/0015 各命中 1 层，作对照）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。摘要：第五轮判 none（0 提案）——层读史实是窗口内唯一一层（40fe732）把「未验证 hedge + 后来的证伪结论」这对双层压成单层（前层整条删、后层原样留），当前文无 hedge 残留；最险成候选 line 12「工程形态 = 形态 A…不是合成一个引擎、也不是单进程统一 runner。」是全文唯一点名两个被拒形态的句子（被拒方案护栏），line 9 结尾「下述原决策脉络保留。」是把 line 5 框成历史的标记。

### docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md 零命中（同一条命令同区间在 0001/0015 各命中 1 层，作对照）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮该条自身是沿用基线（§六 首段：「沿用基线（自 ec12b4b 一字未动…）：0007、0012、0021 三份判无」，基线记录见 `git show ec12b4b:docs/journey/0003-adr-density-baseline-audit.md` 的 0007 节，已核读）。摘要：判无——2 层增长中 layer2 只加一行 `> **Status:** Accepted`、正文一字未动，SEDIMENT 的两个信号（旧层被覆盖未删 / 逐层叠加括注）结构性缺席；最险成 SEDIMENT 候选 = spike 段「第一根穿刺针用无登录站点（维基百科），完全不碰认证……登录代码留到接入真实被测系统时再写」，承载有意 defer 决策与 why「避免登录复杂度污染链路验证」，属「为何这样设计」不属施工节奏。

### docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md → 零命中（未动；第五轮 P60 已随 a97f912 落地，现文 line 16 末句即改后形态）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：proposal（2 提案，1 落地 1 被否）——[P60] approve_reduced：「注：合格图片的成功视觉应答尚未实证，留待 spike。」承载的是证据边界（撞「绿≠对」）而非纯待办，故只换措辞加正向指针、不删边界，现为「注：0003 的证据止于文本应答与 image_url 字段被接受；合格图片的成功视觉应答由下节 spike 第 1 段坐实。」；[P61]「**剩余风险（spike 第一锤要坐实）**：」被红线复核否决——trade-off/风险评估骨架 + 历史框定，且「spike 第一锤」并非悬空坐标（同文末尾有带日期的闭合节收口）。

### docs/adr/0009-maximize-aws-hard-constraint.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0009-maximize-aws-hard-constraint.md 零命中（同一条命令同区间在 0001/0015 各命中 1 层，作对照）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。摘要：第五轮判 none（0 提案）——区间内仅 1 层（853d730）按 0009 自己「决定」段的登记要求末尾纯追加「已记录的例外」整段，原有四段逐字未动、无覆盖残留；最险成候选 = 第 12 行 gpt-5.5 括注，形似离题旁白，实为唯一阻止未来读者把 0002 的排除算进「AWS 硬约束战果」的防误读护栏 + 带真因的精确指针；次险 = 第 15 行例外条尾「例外面被压到最小…」。（本轮对 0009 的发现是**补一条例外登记 + 界定适用面**，属增补不属提纯，与本条判无不冲突。）

### docs/adr/0010-spike-as-apples-to-apples-benchmark.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0010-spike-as-apples-to-apples-benchmark.md → 零命中（未动）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：proposal（2 提案，两条均被红线复核否决、存档不落改）——[P42]「spike 阶段尚未固定（用例已验证通过即可），M2/M5 接入时应设 `logs_directory` 并 gitignore。」被否：该句承载历史框定 + why（spike 的验收线只是用例跑通、故意不做持久化，属决策理由）；[P43]「## 实测挖出的洞察（对 M5 报告统一关键）」被否：提案前提「M5 是悬空过程编号」被真值集证伪——CONTEXT.md:25 明确定义「里程碑（M1–M5 的工程推进）」为项目术语，repo 惯例是保留里程碑标签 + 加已落地注（现文节标题即「（对报告统一关键，即原里程碑 M5）」这一形态）。注：本轮对本文另报一条纠错（line 41 delta 清单漏 Midscene 落点），属纠错类、不进提纯槽。

### docs/adr/0011-agentcore-browser-system-default-vs-custom.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0011-agentcore-browser-system-default-vs-custom.md → 零命中（未动；第五轮 P62 已随 a97f912 落地，现文 line 8 末句即改后形态）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：proposal（2 提案，1 落地 1 被否）——[P62] approve：删掉「本会话已实测可 `start-browser-session` 起停。」里的会话坐标前缀，现为「已实测可 `start-browser-session` 起停（时间与账号见本节标题括注）。」，实测事实与 2026-06 账号锚点、以及「`list-browsers` 返回空 `[]` 是正常的」这条踩坑护栏全保；[P63] 末段收尾句「它适配的正是本 ADR「被测系统在内网/VPC」这一面，重议时从该结论起步而非从零调研。」被否——它是紧跟负向结论（够不到开发者笔记本）之后阻止读者顺推「所以还得重新调研」的反模式护栏。

### docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md → 零命中（未动）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮对本篇的结论本身是二次沿用，其 §六 开篇逐字为：「沿用基线（自 ec12b4b 一字未动，记录见 `git show ec12b4b:docs/journey/0003-adr-density-baseline-audit.md`）：0007、0012、0021 三份判无。」即本篇自基线审计（ec12b4b）以来一字未动、基线判无提纯候选，本轮区间同样零命中，故延续判无。

### docs/adr/0013-cross-engine-sharing-boundary.md · none（0 提案）
- 层读：git log --oneline a97f912..HEAD 命中 2 层，逐层 git show 读差异：0cd40d3（「判断」节句中插入「跨引擎共享的**框架代码**仍止于此；使用方侧另有一个跨引擎共享的**约定面**——项目 `steps/` 目录…见 0037 决策 4」）、a90554c（Status 头「共享止于 features/」→「跨引擎共享的框架代码止于 features/」、「何时重议」末句同步补「（使用方侧的 `steps/` 约定面见上「判断」节）」）。两层都是原句内替换/限定词追加，diff 里旧措辞被就地改写、无被覆盖却留下的旧描述层；随后整读当前 35 行全文。
- 判无依据 / 说明：两处险成候选各由具名要素挡住，且第五轮已分别被独立红线复核证伪、不再重提：① :26 括注「（下述三项各自的承载方式见本节末段）」——末段的逐项映射是「报告归集=`ReportStore`/RunReport、会话生命周期=各 worker 内、跑批入口=核心调度+CLI」，其中「会话生命周期=各 worker 内」不是『往下看』式噪声而是非平凡落点，第五轮 P54 以「精确指针 + 承载纠偏功能」驳回；② :31 段末「即「跨引擎共享止于 `features/`」仍成立（worker 代码仍各属各引擎），公共设施落在**核心库**这一层、不靠跨引擎共享引擎代码。」——它是「原前提（统一到一种语言）被 0023 证伪 → 承载方式改核心库 → 结论仍立」这条论证链的收口，且「worker 代码仍各属各引擎」专防「公共设施落核心库 = 引擎代码被共享了」的误读，第五轮 P55 以「骨架句 + 带框有意重述」驳回。另两处逐句核过后留下：:22 的「（CONTEXT 曾误把 SigV4 写成"两个引擎共享"，已更正）」= 反模式护栏 + 历史框定；:27 的「报告归集 / 统一（M5）」= CONTEXT.md:25 已立的「里程碑（M1–M5 的工程推进）」项目词汇（0010:30/0016:46/0027:5 同用「原里程碑 M5」），是稳定坐标而非施工节奏编号。

### docs/adr/0014-ai-first-assertions.md · 沿用第五轮
- 层读：未层读：`git log --oneline a97f912..HEAD -- docs/adr/0014-ai-first-assertions.md` 零命中，按跨轮沿用规则沿用第五轮结论。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：0014 是密度基线漏审文、第五轮单独补审，唯一提案 P66（原句「Midscene 取结构化全家族可选：`aiBoolean / aiNumber / aiString / aiQuery<T> / aiAsk`」= 裸 SDK 列举，同一列举在 REFERENCES.md 与 0010 各有更权威版本）经复核缩小为「不整删，替换为指向 0018 的正向指针 + REFERENCES 指针、不动 :16 的反模式句」，已落地为现文第 17 行；同批还修掉首段的 aiAssert 矛盾。

### docs/adr/0015-v1-positioning-smoke-not-regression.md · proposal（1 提案）
- 层读：git log --oneline a97f912..HEAD -- 该文件：1 层（a90554c「doc-health 第五轮改动自审」）。git show 读差异：该层本身就是提纯动作——决策 2 条尾部残留的旧句「脚手架各预置一个通用 URL 锚点（`页面地址匹配 "<正则>"`）作范例，**不预置任何项目专属锚点**，不要求 QA 学措辞」整段删除（与同句前半逐字重复），收成「…（改它等于 fork 发行包），也不要求 QA 学措辞」；其余 48 行未动。随后整读当前 49 行全文。
- 判无依据 / 说明：提案 1 条（见 proposals）。同时记两处险成候选、按红线留下：① 第 42 行「"点名精确核对某项"（如"价格是 ¥99"）也走这层——QA 仍只写自然语言，AI 去看那一项。」与第 10 行「点名时也能测」条用同一 ¥99 例子，险判完整重复；留下因它承载的是独立断言**路由归属**（点名 ∈ 第 1 层默认 AI，不是第 2 层确定性锚点），正是 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md):40「早先"显式断言锚点=QA 点名让 AI 看"（0015 原措辞）澄清」点名要消除的那处误读，删了误读会回流。② 第 49 行「当出现"纯视觉/像素级回归"需求时，交给专用工具，不强行塞进本工具。」与第 11 行「**不做**：像素级 / DOM 快照式精确回归」重合，留下因两者结构功能不同：第 11 行是当下决策 + Percy 理由，第 49 行是「何时重议」的反转闸门（触发条件），去掉后本 ADR 无重议出口。
  - 提案（第 36 行）：- **未点名不抓**（种类 B）：最左档定位的必然代价，接受。 → 同一事实在本 ADR 内第三次完整重述、且用词与上文逐字重合：第 30 行已写「**v1.0 不解决，作为已知边界接受。**」、第 32 行已写「种类 B 不是 bug，是最左档定位的必然代价。」。本句不承载新决策/why/trade-off/反模式/不变量，也不带指针；同节第 37 行恰恰已是「列条目 + 指针」形态，证明本节的结构功能（单点枚举 v1.0 的边界）用指针即可满足，属「可指针化的…

### docs/adr/0016-execution-architecture-core-lib-run-model.md · proposal（2 提案）
- 层读：git log --oneline a97f912..HEAD 命中 3 层，--stat 显示全是小改、且全为原地整句替换、无叠加残留：a90554c（第五轮自审：节标题 + 「三名分离」段 + 布局树补 `deploy_aws/` 行、workspace 成员数「三→五」，5 insert / 4 delete）；8470fa0（v1.4 行「claude/ai skills 暴露」→「agent skill（一份 SKILL.md + references…0043）」，1 行替换）；d910c1b（同一 v1.4 行补「✅ 2026-09-14 Accepted」，1 行替换）。三层只落在两处（布局树 / v1.4 行），前层文字被整句覆盖、未见「旧描述层 + 新描述层」并存。随后整读当前 266 行做逐句布尔。
- 判无依据 / 说明：（有提案，此栏记险成候选却留下的具体句 + 层读史实）险成候选而按红线留下的：① line 168「**trade-off**：把 local 装配从 `__main__` 迁进 `compose` 要改现有 3 个 `monkeypatch m.Local*` 测试的注入点——换来 compose 两后端对称可复用…值得」——带施工期计数（3 个测试），但整句形态就是 trade-off（代价 vs 收益 + 结论），受红线「权衡」保护，留；② line 141-142 决策 B 首段「`subprocess worker + 注入 S3 落点/DDB events`（旧称「subprocess+cloud」）**不再是面向用户的 CLI 档**…而是**内部预演/测试手段**」——「旧称」是历史框定、其余是决策本身，留；③ line 144「**承载机制 = …不由 `compose.build_engines` 暴露形参**：`build_engines` 曾留一个 `artifact_s3=(bucket, prefix)` 形参…故删。**护栏（防未来重复进坑）**：…别把它当「cloud 档的注入点」复活」——「曾留…故删」是被拒方案护栏（且真值已核：compose.py:309-318 build_engines 签名确无 artifact_s3），留；④ line 155「**证据边界（绿≠对）：profile-only 端到端已真验 ✅**…全 passed、零 `InvalidRegionError`/`NoRegionError`」——Accepted ADR 内联的自包含证据，留；⑤ line 165「**两种 boto3 句柄别混**（静默出错高危）…喂错句柄类型运行时才 AttributeError、moto/cli 都测不到」——不变量 + 危害说明，留（code 侧 compose.py:661-672 docstring 也照它写）。层读史实：3 层增长全为原地整句替换（布局树一处、v1.4 行两次），未产生并存的旧描述层，故本轮沉积候…
  - 提案（第 167 行）：- **测试注入点随之迁移**：原 cli 测试 `monkeypatch m.LocalRunStore/...`（模块级名字）改为 patch `compose.build_local_stores`（或其内部构造钩子）——注入点从「__main__ 模块级 Local* 名字」迁到「compose 的 build… → 这半句是一次性重构的迁移节奏（「原 X 改为 Y」「验的东西不变、只换注入锚」），承载的稳定信息只有「cli 测试的注入锚 = compose 的 build 函数 / boto3 钩子」一条现状；被替换掉的旧世界（3 个 `monkeypatch m.Local*`）已在紧邻的 line 168 trade-off 条里作为**代价**保留（那条受 trade-off 红线保护、不动），故此处的…
  - 提案（第 143 行）：**关键：这只是重定位「谁来用、是不是用户档」，不删预演的价值论证**——「上传/抢传能力提前在 subprocess 环境建好并验证、为 Fargate 铺路」这套论证（见 [0029](./0029-engine-artifacts-to-s3.md)/[0032](./0032-fargate-execution… → 「这只是重定位…不删…一字不动」是对当次文档编辑动作本身的自述（编辑叙事，读者是当时的改稿人）。该句真正承载的两条要素——① 预演价值论证仍成立 + 指针 0029/0032，② 该组合的定位从用户档降为内部手段——去掉编辑自述后完整保留；「不删/一字不动」对未来读者没有信息量。

### docs/adr/0017-cloud-execution-fargate-over-runtime.md · 沿用第五轮
- 层读：未层读（区间零命中）：`git log --oneline a97f912..HEAD -- docs/adr/0017-cloud-execution-fargate-over-runtime.md` 返回 0 行；本轮只整读当前 35 行全文做纠错扫描（产出 1 条 DEADLINK：`runScope`）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。§六 抄录：「### docs/adr/0017-... · proposal（1 提案）— 层读：40fe732（标题「## 诚实修正（grilling 挤掉的水分）」去掉括注）、853d730（同一层做三件事：Status 头追加「倾向已落地为实态……」长句、开篇倾向句尾加「（此句为上云前的原始表述，保留作决策史……）」括注、「何时坐实」节前插一条 > 已落地演进注）——随后整读当前 35 行全文」；该提案（P44）经红线复核缩小为「只压第 33 行首句里与 Status 头逐字级重复的机制枚举、保留 0032/0033 精确指针」，并已随 a97f912 落地——现文第 33 行即「Fargate/ECS 即 `--backend cloud` 的执行实态（见 Status 头与 [0032]/[0033]）」，与该缩小改法逐字一致，故本轮无新提纯依据。

### docs/adr/0018-generic-steps-capability.md · 沿用第五轮
- 层读：未层读：`git log --oneline a97f912..HEAD -- docs/adr/0018-generic-steps-capability.md` 零命中，按跨轮沿用规则沿用第五轮结论。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：「0018 · proposal（2 提案）；层读：区间内仅 1 层 40fe732（只删 lead 一句与标题逐项重复的自述），正文各节（含「刁钻用例暴露的边界」两个批次小标题）逐字未动」——那 2 条提案（把「两批打磨」小标题与 ①⑤/②④ 圈码当施工编号）随后被独立复核证伪：features/wikipedia_robustness.feature:1 自身即以「第二批」标识、圈码是 in-repo 的活交叉引用而非悬空过程编号，故 0018 的批次/圈码坐标按「不误伤」留。

### docs/adr/0019-feature-tags-scope-and-engine.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0019-feature-tags-scope-and-engine.md → 零命中（窗口内未动），故沿用第五轮结论、本轮不重做层读。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮该条摘要：「层读：d88f774（+4 行：新增「### `@timeout:<N>`」两条语义 + 「范围」节加「`@timeout:` 的实现落点」条）、853d730（「范围」节「语义已定」条补上 `@timeout:`、称「三个 tag」）——两层都是 @timeout 一条线的增补，前层内容未被后层覆盖、无旧描述残留；随后整读当前 71 行全文。」（第五轮 verdict=proposal，1 提案，仍在待批/存档状态，本轮不重提。）

### docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md · 沿用第五轮
- 层读：未层读：`git log --oneline a97f912..HEAD -- docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md` 零命中，按跨轮沿用规则沿用第五轮结论。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：「0020 · proposal（1 提案）；层读：区间内 2 层——24943d8（角色边界节头加「单一真源现为 0040」指针）、38aa74e（test engineer→测试开发逐词替换）；沉积来自更早的「落地现状」追加层」——该提案（把「落地现状」条压成结论 + 0022「实现状态」指针）经复核缩小：落点重述确属沉积可压，但括注「锚点仍写在脚手架文件里、注册表只是收集机制」是防「锚点住在注册表里」误读的护栏、须随改法保留，缩小后的改法已于 0cd40d3 落地（即现文 :20）。

### docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md · 沿用第五轮
- 层读：未层读：`git log --oneline a97f912..HEAD -- docs/adr/0021-local-cucumber-patch-step-keyword-disambiguation.md` 零命中，按跨轮沿用规则沿用第五轮结论。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：§六 开头「沿用基线（自 ec12b4b 一字未动，记录见 `git show ec12b4b:docs/journey/0003-adr-density-baseline-audit.md`）：0007、0012、**0021** 三份判无」——0021 是 Superseded-by 0022 的纯决策史文（全文由 Status 头「下文描述 B1 之前（v0.x）的状态」框住），自密度基线以来一字未动、无新增层可沉积。

### docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md → 零命中（窗口内未动），故沿用第五轮结论、本轮不重做层读（本轮对本文只做客观类核实，见 findings 中 0022 两条）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮该条摘要：「层读：区间内 2 层，均单点替换：8bb961a（worker 包化，1 行——第 42 行「实现状态」块里的 code 落点 `engines/novaact/worker/deterministic.py` → `engines/novaact/gherkai_worker_novaact/deterministic.py`、midscene 侧同步）；38aa74e（术语 2 处）。沉积是此二层之前叠加的状态块与迁移段，整读当前文 93 行取证。」（第五轮 verdict=proposal，3 提案，其中 [P35] 经红线复核缩小，仍待批，本轮不重提。）

### docs/adr/0023-novaact-acting-python-locked-no-ts-core.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0023-novaact-acting-python-locked-no-ts-core.md → 零命中（未动）
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：none（0 提案）——「区间内仅 1 层（03ad86d）且该层本身即提纯动作（把伪逐字引用『medium 置信、未验证』备用路径改成概括『未验证备用路径』，因引号内表述已随 0006 提纯删除），其余 37 行逐字未动；最险成候选是第 26 行「`@aws-sdk/client-nova-act` 本 ADR 未独立核实成……不是本 ADR 抓到的页面。」，句首句尾看似同义重复，但它是本 ADR 逐条标注证据归属/置信度这套体系里唯一把 `apiVersion 2025-08-22`、`endpointPrefix nova-act` 两个字段的出处判回 0006 的句子，删掉会让未来读者把它们当成本 ADR 的实锤、误升级证据强度（裁决标了高置信）。」

### docs/adr/0024-worker-core-protocol.md · proposal（1 提案）
- 层读：git log a97f912..HEAD 得 6 层（3376b2f / 5d04676 / aeda8ec / 1a2def8 / 8b86e98 / 2e5f157），--stat 每层 2–6 行、合计 16 行；逐层 git show 读差异后整读当前 263 行。
- 判无依据 / 说明：层读史实：6 层全是原地整句替换、无被覆盖却残留的旧描述层——3376b2f 把「读一致性」条整句从「强一致终读 / EC 轮询+断号检测 二选一」换成「连续前缀游标 + 终读两者都做」并把旧写法收进「本条曾写…（code-health 对抗验证发现）」的历史框定里；2e5f157 把「midscene-only≈`MIDSCENE_GRACE_MIN_S`=25s」的硬值换成指向 `runtime/gherkai_runtime/compose.py` 的指针（今值 31，若不换即成过时）；1a2def8 只在「失败/超时的 act 同样带 cost」段尾内联真跑证据（NOVA_ACT_TIMEOUT_S=2 逼出 ActTimeoutError、time_worked_s=23.09），属 Accepted ADR 的自包含证据、不动。另有两处险成候选但因承载受保护要素留下：line 15 句末「（cost 信封同样几经收窄——最终砍成「engine 只报原生量、core 只合计」，见下「成本信封」。）」带精确指针且与前半截同属「删除测试逼出的收窄」这条被拒方案脉络；line 166「**旧默认值漂移已消除**：此前 cli `--grace`=10 / `ScheduleOpts`=5 远小于 ACT_TIMEOUT_S=120、每个 Nova run 恒在违约区靠 session TTL 兜底」看似施工节奏，实为「两处独立 120 会漂移」这条反模式的记录 + 「改哨兵默认」的 why，红线护栏保。
  - 提案（第 177 行）：**传输选型已定 + adapter 已实装 + 组合根接线已落地**： → 施工进度式预告：其后紧接的三个分句把同样三件事各自完整说了一遍（events-out 焊死 DDB / FargateEngine 已编码 / 组合根接线已完成），标题本身不承载 why、trade-off、不变量、被拒方案或指针；本节的框定功能由同句前半截「本节钉的是已想清、不会变的边界（哪些 survive、哪些必改）」承担，删掉后论证结构不断。

### docs/adr/0025-plan-module-feature-to-jobs.md · proposal（2 提案）
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0025 → 2 层，均已 git show 读差异：① 5d04676（+2 行，`--stat` 2 ++）在「已定语义」原位追加裸 `@scope:` / 裸 `@engine:` 空值报错两条，未覆盖任何旧句；② a90554c（1 行整行替换）把 gherkin 版本条按原尾巴复原（被拒 pytest-bdd 内部符号那句 + 「core 用哪版 gherkin 与 worker 无版本耦合」结论）并去掉不存在的 `core/tests/test_parse.py`。两层皆原地增补/整行替换，前层无残留、无施工括注新增；随后整读当前 128 行全文取证。
- 判无依据 / 说明：审过判留（内容锚定）：line 81「**keyword 判不出 = 拒绝猜（fail-fast，首轮 code-health 逼出）**」与 line 58 括注「（code-health 对抗验证发现，曾无声放行）」都险成「过程坐标」候选，留下是因为二者是自包含的血缘事件描述（不含 journey 链接、不含裸 WP 编号），且「曾无声放行」「静默兜底成 Given，会把本该是断言的 step 当动作派发」正是 CLAUDE.md 要求保留的「被拒/曾进坑」护栏；line 24「**删除测试**：删掉本模块…→ 它在挣钱」是深模块存在理由（why），line 33 的边角清单（And/But keywordType 继承、多 Examples 表 + 三层 tag 合并、Rule 层 background 叠加、占位符转义）是「不自己写展开」这条被拒方案的支撑证据，均属红线保护。
  - 提案（第 5 行）：下一块 `schedule`（scope 串/并行调度）以本模块输出为输入，另立。 → 「下一块…另立」是本 ADR 撰写当时（0026 尚未成文）的施工序列语；其承载的稳定信息只有「调度另有一篇 ADR、以本模块输出为输入」这条边界，且指针不精确（未链 0026，读者得自己找），与同段其它句子（0019/0016/0024 都带链接）不一致。
  - 提案（第 93 行）：若未来需更强稳定性可引 `@id:` tag，暂不做。 → 同一留口子在本文出现三处：line 123「留口子不实现：`@id:` 显式 id tag」、line 128「重议」条（且是唯一带触发条件「若出现 id 跨运行不稳的真实痛点（feature 频繁改行号）」的一份）。此处第三份是无指针、无增量的完整重复。

### docs/adr/0026-schedule-module.md · 沿用第五轮
- 层读：未层读（沿用第五轮）：git log --oneline a97f912..HEAD -- docs/adr/0026-schedule-module.md 零命中（区间共 72 个 commit）。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮该条结论摘要：verdict=none（0 提案）——最险成候选是「## 治理旋钮 = 注入参数 + 保守默认（贯穿原则）」节（四个旋钮的「注入+保守默认」上文已各说一遍、看着像第四遍复读），留它因两条都在本节自身跨度内的受保护要素：①把四个旋钮抽成一条命名贯穿原则并挂「同 0016 组合根注入精神」指针（带指针的有意重述）②括注补了唯一例外「job 墙钟预算同守此精神、只是载体不同…见上「超时兜底」」，正是第 27 行「per-job 墙钟预算不在 opts」的呼应；史实层面本文两处 ⚠️ 纠正注与 Status 头 Partially-superseded 表述同出 b7228a1 一次落定，非叠加型旧层。

### docs/adr/0027-runreport-aggregation-index.md · proposal（3 提案）
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0027 → 1 层（`--stat` 12 行 6+/6-），已 git show 全读：8b86e98（ADR 0042 落地反向链）——6 处整行替换：`kind` 表补 `evidence`、`ref` 条加「皮层侧按层收窄」、②标题改「报告产物导航清单（引擎原生产物 + gherkai evidence）」、空态括注「无原生产物」→「无报告产物」、「Midscene 保持 scope 级」→「Midscene 的 report 仍 scope 级…evidence 都下沉 step 级」、留口子里 trajectory 提取标为已落地。全为整行替换、无叠加残句；唯一残留是该层只改了 129 行的空态文案、漏改 147 行同一引号串（已作客观类 STALE 报出）。随后整读当前 174 行全文取证。
- 判无依据 / 说明：审过判留（内容锚定）：line 165「**现在做（v1.0）**：本 ADR 上述全部决策均已实装（单测 + 两引擎真 e2e 覆盖）」形似状态镜像，留下是因为它是全文唯一交代 Accepted 态证据强度（「两引擎真 e2e」）的地方，属 Accepted ADR 内联的自包含证据；line 33 标题括注「（落地逼出）」与 line 35「[0016] 早把 `run_id` 列为「持久化层 Run 级字段、deferred」——RunReport 落地把它逼了出来」看似一事两写，但 line 35 承载的是「为何 run_id 现在才出现」的决策血缘、标题括注是该论证的框定词，删任一句论证结构即断。另：第五轮对本文的唯一提案（[P53]，「纯确定性用例」节第三条「行为与含 AI step 的用例一致…」）已被红线复核否决为「空态行为不变量 + 防重复进坑护栏」，本轮复核同意、不重提。
  - 提案（第 96 行）：`ResultStore` 旧 docstring「RunReport 归集靠它」一句删除——归集职责移交 `ReportStore`。 → 这是一次已完成的 code 编辑动作记录（施工流水），不是决策：其承载的决策「归集职责属 ReportStore」在同句前半的三 port 职责定义与 line 13–14、line 96 前半已写死；真值侧该 docstring 早已不含此句（core/gherkai_core/ports.py:159-166 的 ResultStore docstring 现只讲「数据面/判定真值唯一权威」）…
  - 提案（第 169 行）：（注：store 读回面**已落地**——`RunStore.load_run_meta`/`load_run_state` + `ResultStore.load_job_result`/`load_all`，靠 `serialize` 完整重建，[0016](./0016-execution-architectur… → 它挂在「留口子**不实现**」列表下却宣告「已落地」= 毕业项没删的旧描述层（列表的语义是仍敞着的口子）；读回面 API 的权威在 0016（该括注自己就指向 0016），此处第二份只是状态镜像。
  - 提案（第 65 行）：**返回 `ResourceUri` 而非 `Path`**（封版前收口） → 「（封版前收口）」是施工时点标记，不承载 why/trade-off/不变量——同句后文已给完整 why（S3 adapter 否则被迫返回 `Path` 包 `s3://`，而 `Path` 会把 `s3://b/x` 折成 `s3:/b/x`），删掉该括注论证不断。

### docs/adr/0028-transient-network-ssl-resilience.md · 沿用第五轮
- 层读：未层读（沿用第五轮）：git log --oneline a97f912..HEAD -- docs/adr/0028-transient-network-ssl-resilience.md 零命中。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮该条结论摘要：verdict=proposal（2 提案）——层读区间内 2 层均逐词替换（7e1eca3 改 core/wire.py→core/gherkai_core/wire.py 等 code 指针；4916589「烧钱」→「持续计费」），沉积来自此二层之前的多轮真跑追加（静默超时根治／血缘回传／Midscene 两窗口／step 短路都是后续轮次往「留口子」节追加），整读 143 行取证；其中 [P34]（「已知欠账」条的 step 短路注意句压成指针 + 本地独有结论）已批准并落地（当前 0028:69 已是压缩后文字、0028:93 已改指「上文『已知欠账』条」），[P33]（删「现在做（v1.0）」清单条）经红线复核被否（该行是「现在做／留口子」in/out 对照的骨架句 + 带「（v1.0）」历史框定，本身即范围决策）。本轮另在该文报了两条 DEADLINK（r1/r2 会话内标号），属客观类、不占提纯槽。

### docs/adr/0029-engine-artifacts-to-s3.md · proposal（2 提案）
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0029-*.md = 2 层：a90554c（第五轮改动自审：「0029 上传时机条按 0032 层2 收窄 scope 级强保证」）、8b86e98（0042 实现批次：给同一条 bullet 追加 evidence 具名例外句）。git show 逐层读差异：两层都只改「上传时机 → reportRef 指向的文件」这一条 bullet，是就地改写而非叠加，无被覆盖的旧描述层残留——唯一的旧内容是该 bullet 里 pre-修订的「字节随 scope 末 flush」（已作 CONTRADICTION 单独报，属纠错不属提纯）。再整读当前 118 行全文。
- 判无依据 / 说明：非判无。逐句过时险成候选但因承载受保护要素留下的三处：① 第 34 行「（注：Fargate Engine adapter「怎么起 worker/怎么停/事件怎么回」属传输/执行环境，见 0024/0032——它注入 S3 落点的动作与 subprocess adapter 对称、无特殊性，不在本 ADR。）」看似边角旁注，实为 ADR 边界划定 + 精确指针，删了读者会以为本篇该管 Fargate adapter；② 第 90 行「**被拒方案 D（护栏，防重进坑）**：Midscene「每步存 dump JSON 事后重建 report / 周期性 destroy 重建」——**否决**：…」是红线明列的反模式/被拒方案，不动；③ 第 100-105 行三条 `~~…~~`（S3 key 命名 / 上传错误分类 / materialize 语义）是「曾计划 X、现已废弃/已定」的历史框定，红线护栏「历史记录 ≠ 过时」直接命中，且 materialize 那条还内联了两条否决理由。
  - 提案（第 69 行）：## 分期：上传第一期（subprocess 预演环境落地，现在做）/ Fargate 增强（未来） → 「现在做」是 Draft 期的施工时间坐标，与第 76 行「第一期实现定论（…已实现）」及 Status 头「已在该预演环境实现并验证」同文冲突；分期本身（第一期 vs Fargate 增强的边界与理由）是决策、保留，只有时态标记是施工残留。
  - 提案（第 78 行）：第一期真做时把下面几点从"待定"钉死（原"留口子"里对应项标状态）： → 整句讲的是「我改这篇文档时做了什么」（把待定项钉死、给留口子条目标状态）——编辑动作与施工节奏，不承载决策 / why / 权衡 / 不变量 / 精确指针；留口子节自己的删除线条目已自明其状态。

### docs/adr/0030-realtime-persistence-seam.md · proposal（1 提案）
- 层读：层读 a97f912..HEAD 共 4 层，全部 --stat 后逐个 git show 读差异：6ff9a5c（1 行：ConsistentRead 那条就地扩写，补 events 表投影读同理强一致 + 2× RRU 权衡）；9c6ebfb（+2 行：决定三新增「detached 路径同守」整段）；06f7acd（1 行：就地在 9c6ebfb 刚加的那段句尾追加真跑坐实证据——后层扩前层同一句，无残留旧句）；5d04676（2 行：update_job_state「整 entry 刷」与 project_state「逐属性刷」两句就地分开重写，替换而非并存）。随后整读当前 223 行全文。史实结论：本区间零「后层覆盖前层却没删」的残留，四层全是原地补 why/证据/口径的加固。
- 判无依据 / 说明：（verdict=proposal）另附审过判留：①「## 现在做 / 留口子」的决定六／七两条 bullet 不再提——第五轮 [P29] 已就同一处出提案并被红线复核否决（第 215-216 行「moto 全程 mock 单测、行为对拍 local——坐实「换后端 core 不动」」与「真跑通 local↔cloud 端到端」是全文仅此两处的 Accepted ADR 内联自包含证据，且搬入决定六与其首段自设边界「怎么实现/怎么测是实现细节，不在此」正面冲突）；决定一~五那条 bullet 同理按「现在做 = in/out 范围决策的一半」判留（同第五轮 0028 [P33] 的判据）。②本区间新增的三处文字全部承载受保护要素、不成候选：决定三「detached 路径同守」段带被拒实装史（「曾如此实装：先 CAS 再在 tick 之外补聚合」）与不可重试论证；5d04676 的 project_state 逐属性那句带反模式（「曾整 entry 覆盖，不带 baseline 的投影会抹掉只由 claim 落库的 `claimed_at`」）；6ff9a5c 的 ConsistentRead 扩写带 why + 成本权衡。
  - 提案（第 3 行）：已由 [0034](./0034-detached-batch-reconciler.md)（无状态跑批，reconciler 直写 RunState）落地：`RunState` 投影带 `high_water_mark` 条件写、finalize 单独条件写（见下「重议」条反向链）。 → Status 头这半句把机制（`high_water_mark` 条件写 + finalize 单独条件写）完整重复了同文件「重议」条（第 222-223 行）的表述，而那里才是带 why 与证据的权威处（「比当初预告的 owner/lease 更轻…无需 lease 租约」＋「真 DDB 实测挡住了 stale 快照把 passed 刷回 running 的 lost-update」）。头部本身…

### docs/adr/0031-job-lifecycle-states-and-severity.md · none（0 提案）
- 层读：层读 a97f912..HEAD 共 1 层：9c6ebfb（1 行，git show 已读差异）——在决定一·补既有那句不变量（「绝不进 `JobResult.status`…绝不进 wire。」）的句尾就地追加「**不变量的强制点 = `project_full`**…同步 run 路径由 schedule 的归约器天然只产终态。」，纯追加、未改写也未遗留任何旧句。随后整读当前 196 行全文。
- 判无依据 / 说明：史实层面本区间只有 1 层纯追加，结构上不可能留下被覆盖的旧描述层；整读后两处最险候选均因本节内可定位的受保护要素留下：①新增那句本身 = 不变量的强制点（「收尾快照里任一 job 仍非终态即抛、本轮不落任何判定真值」，并带「归约中间态用 JobResult 作载体不算违背」的边界澄清），是关键不变量、红线直接保护；②决定五第 139 行「当前结果不变：含 aborted/skipped 的 run 必伴随 error → run=error → 退 1（CI 红）」与决定二第 95-98 行「为何 run 级不含 skipped/aborted」共用同一条因果事实、看着像重复，但两处结论不同（前者答「换 severity 后退出码会不会变」、后者答「run 级聚合为何可以排除这两态」），且第 139 行后半「aborted 有副作用、skipped 因别人崩才没跑，整批确实失败，退非 0 正确」是本条独有的 why，压成指针会让决定五失去自身论证的收尾。（第五轮对本文同判 none，其锚定候选是决定六表格后的收尾句与「core 内态、不进 wire」四处各自承重，与本轮所举两处不同，两轮无重叠。）

### docs/adr/0032-fargate-execution-environment.md · proposal（1 提案）
- 层读：`git log --oneline a97f912..HEAD -- docs/adr/0032-...md` 共 3 层，`--stat` 显示每层均 1 行改动，三层 diff 全读（都是在既有长句尾**追加从句**，非重写）：① 1dd7194 把 retry 条从「两腿机制不同：Midscene 不关 SDK 重试」改写实为「两腿同一策略 = 关 SDK 重试 + 单次墙钟封顶」，并在真验括注里补「真验当时尚未关重试…此后 Midscene 亦加 `maxAttempts: 1`」；② 8b86e98 在「层2 降级」条尾追加 0042 evidence 的具名例外；③ 89cfc8b 在「据此的 code 决策」条尾追加 0042 截图队列排空与 `MIDSCENE_GRACE_MIN_S` 25→31。随后整读当前 75 行全文。
- 判无依据 / 说明：（verdict=proposal）逐条核过、有意留在原处的近候选：① 第 60 行 retry 条里 1dd7194 补的「Midscene 真验当时尚未关重试、10.00s 是 `AbortSignal` 到点 abort 掉整个 send 连同其内部重试…此后 Midscene 亦加 `maxAttempts: 1`」——形态像施工流水，但它界定的是那四个掐秒数字的**证据边界**（真验跑的是哪一版配置），删掉即把「当时未关重试」的实测悄悄记成「已关重试下的实测」，属受保护的自包含证据；② 第 54 行「实测覆盖边界（诚实声明）」与第 44 行「适用面注记」沿用第五轮同一判无理由（证据边界 / 不变量适用面），本轮复核仍成立。
  - 提案（第 56 行）：**Midscene `MIDSCENE_GRACE_MIN_S=25` 不动**（实测 12.4s、~2x 余量；Midscene 无 greenlet、会话释放 0.2s，长 act 下也远快于 Nova）。后来的 step 级 evidence（[0042](./0042-step-evidence-and-ex… → 层读定位的两层叠加：前层（校准当时）断言「=25 不动」，89cfc8b 追加的后层把值改成 31 却没回改前层——同一句里先给旧值再给新值，当前值埋在句尾。前半句除数据（12.4s / ~2x / 无 greenlet 0.2s，受保护的自包含证据）之外，「=25 不动」这个**值断言**本身不承载 why/trade-off/不变量，只是被后层覆盖的旧描述层；按密度看，读者/agent 检索 …

### docs/adr/0033-iac-aws-backend-and-composition-wiring.md · proposal（1 提案）
- 层读：`git log --oneline a97f912..HEAD -- docs/adr/0033-...md` 只有 1 层且 1 行：5d04676（code-health 批准项 [35] 的 ADR 校准——第 35 行 Lambda 角色条的 `iam:PassRole` 枚举从「到 execution role 与各 task role」补成「到 execution role、各 task role 与 `{prefix}timeout-scheduler`——后者是 CreateSchedule 传 Target role 的 IAM 前置，见 15.」），diff 全读：纯枚举补齐、无叠加。区间之前的 11 层增长史已由第五轮层读覆盖（其 39 条缩小改法随 a97f912 落地，含本文 Status 头语气改完成态）。随后整读当前 188 行全文。
- 判无依据 / 说明：（verdict=proposal）除上一条外逐段核过、有意留下的近候选：① 第 56 行「**命名真源的落位演进**：曾因「CDK 独立工程、不能 import `gherkai_cli`」在 `iac_aws_backend/names.py` **复刻**一份命名函数（双写、靠对拍测试防漂移）…复刻消除、护栏测试转为「真同源」的结构性保证」——读着是施工史，但它是「IaC 侧复刻双写」这个被拒形态 + 「为何今天能真同源 import」的决策脉络（护栏从对拍测试降级为结构性保证也在此交代），且带历史框定「曾」，按红线留；② 第 3 行 Status 头那段 0037/0038 delta 枚举，第五轮红线复核已判其为 Partially-superseded 必需的「结论存什么/立场变什么」+ 反向链（[P13] 驳回），本轮只在正文侧发现它承诺的「就地历史注」有两处未兑现，按纠错报（见 findings，不走提纯）。
  - 提案（第 182 行）：- **镜像瘦身**：属施工，不在本 ADR 决策面。（真容器 grace/中断校准已完成，归 [0032](./0032-fargate-execution-environment.md) Accepted。） → 括注是跨 ADR 的**进度回响**：0032 的完成状态真源在它自己的 Status 头（本文第 3 行与「资源清单」5. 已两处指过去），此处再复述一次「已完成」只会随对方状态漂移；它不承载 why / trade-off / 被拒方案 / 不变量，是「留待」清单上一个已勾掉的旧条目残留（该项原本与镜像瘦身并列在 defer 里）。同族改动第五轮已有先例并获批（[P26] approve：删另…

### docs/adr/0034-detached-batch-reconciler.md · proposal（2 提案）
- 层读：git log --oneline a97f912..HEAD 命中 7 层，--numstat 逐层量：105c704（6+/6-，最大改层）、9c6ebfb（5+/3-）、06f7acd（1+/1-）、3376b2f（1+/1-）、5d04676（1+/1-）、aeda8ec（1+/1-）、57e9209（1+/1-）。对 105c704 / 9c6ebfb / aeda8ec / 57e9209 逐个 git show <c> -- docs/adr/0034-…md 读差异：全部是**原地整句/整段替换**，无并列留旧层——105c704 把旧段「exitCode 落值延迟兜底（防御性冗余）……仍保留一条廉价兜底（payload 缺 exitCode 则短暂重查 DescribeTasks / 重试）……留而不依赖」整段删掉换成「退出码缺失：观察者落哨兵、不留宽限态（修正）」段，并同步改了真值表行、端到端流程行、exit item 属性行；9c6ebfb 把 RunReport 一行拆成 ResultStore + RunReport 两行并重写 ④ 写序；aeda8ec 只在…
- 判无依据 / 说明：
  - 提案（第 236 行）：临时 PoC 脚手架验后即清、未入库 → 施工卫生流水：交代脚手架事后怎么处置，不承载决策 / why / trade-off / 反模式 / 不变量，也不是证据本身（H1/H2/H3 三条数据的可信度与可核性不依赖它）。且它复述的是 CLAUDE.md「工作方式」已有的通行约定（一次性脚本放 $CLAUDE_JOB_DIR/tmp、不入 tools/），在一个证据节的标题里再声明一次是净噪声。
  - 提案（第 234 行）：同步 `run` 路径仍用现驱动循环（两种驱动模型并存，按命令分流）。 → 同一事实的第三次完整陈述：第 48 行已权威给出「**两种皮各有自己的驱动模型、按命令分流**……故「共享同一 reconciler」只在 `submit`/`status`（连同 kicker/reconciler Lambda——tick 四宿主一份）成立，不含 `run`」，第 232 行 (b) 条又说了一遍「核心与接口要动」的分层，本句只是把它再说一次；本句所在段的前半句「存活的是纯归约…

### docs/adr/0035-local-app-testing-via-tunnel.md · none（0 提案）
- 层读：git log --oneline a97f912..HEAD 命中 1 层：3376b2f（--numstat 1+/1-）。git show 3376b2f -- docs/adr/0035-…md 读差异：决策 3 表格 cloud submit 行原地追加「**任何异常路径同样拆**（store 装配抛 / 轮询被中断）：守护进程是隧道唯一宿主……曾只在循环之后拆、装配段裸奔，装配一炸 ngrok 即永久留在公网（code-health 对抗验证发现）」——纯加一条不变量 + 一条反模式，旧内容原样保留、无被覆盖未删的描述层、无叠加式施工括注。再整读当前 81 行。
- 判无依据 / 说明：两处险成候选、逐句核后判留：① 第 35 行（决策 1 的 0009 例外登记）里重列了「SSM 端口转发方向相反；IoT Secure Tunneling 两端 localproxy、不产公网 URL；AgentCore Browser VPC 模式够不到开发者笔记本」——与第 24 行（调研结论④尾）和第 22 行（调研结论③）内容重叠，看着像可指针化的重复；留下的理由是它承载「按 [0009](./0009-maximize-aws-hard-constraint.md) 要求登记」的例外记录、须自包含可审，且句内**已经**带了指针「见调研结论③与被拒/被缓方案」，属红线护栏点名保护的「带指针的有意重复」。② 第 81 行「本机关机/断网 = 隧道断 = run 以导航失败（AI 报错形态）告终——明示边界，submit 时提示，不做「断线重连恢复」（隧道进程崩溃同理；测试可重跑，不值守护复杂度）」与第 60 行 cloud submit 语义澄清讲同一件事；留下的理由是两句功能不同——第 60 行是操作面（submit 打印什么、为什么把例外变明示边界），第 81 行是「边界与不变量」节收口的不变量条，且**被拒方案「断线重连恢复」+ 其理由「不值守护复杂度」只在第 81 行出现**（红线护栏：反模式/被拒方案绝不删）。

### docs/adr/0036-deterministic-capability-discovery.md · 沿用第五轮
- 层读：未层读：`git log --oneline a97f912..HEAD -- docs/adr/0036-deterministic-capability-discovery.md` 零命中，按跨轮沿用规则沿用第五轮结论。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md），自 a97f912 起 git log 零命中。第五轮结论摘要：「0036 · none（0 提案）；区间内只有两个一行术语层（38aa74e test engineer→测试开发、4916589 烧钱→零费用/计费），零内容叠加、无施工节奏可残留。整读 54 行后最险的候选是 Status 头尾巴「清单查询（`list-deterministic`）与 plan 命中标注均已实现」——留它是因为决策 4「plan 命中标注」是 015585e 才纳编进本 ADR 的，这句是全文唯一交代「决策 3 与决策 4 都在已落地范围、不是前向留口子」的地方，且点的是稳定 CLI 面而非施工步骤；第二险是 0022「匹配放 worker，不放核心」指针出现三次（决策 2 第三条 / 决策 4 引言 / 被拒方案），但三处各挂不同机制，属带指针的有意重复。」

### docs/adr/0037-distribution-and-packaging.md · proposal（3 提案）
- 层读：git log --oneline a97f912..HEAD 得 6 层：8470fa0（0043：决策总览 CLI 行 + 不分发行 + 布局树两行，4 处）、8b86e98（决策 7 接线句「三个 cloud 入口」→「四个…补 explain」）、eb057cf（决策 6 provider 契约补可选 `doctor(args) -> list[dict]` 及 0041 指针）、5d04676（决策 6 两处 SSM 键从裸字面量 `names.ssm_path(prefix, "vpc"/"version")` 改常量 `ssm_path(prefix, VPC_KEY/BACKEND_VERSION_KEY)`）、6ff9a5c（决策 6 补「子动词与 --diff/--synth-only/--bootstrap 同给 → 皮退 2」）、a90554c（决策 3 midscene 条的指针由已搬走的「重议闸门」条改指「被拒方案」节『进程包装层的 fd 转发补丁』条）。--stat 各层仅 2–8 行；逐层 git show 差异：**全部是整行原地替换**，无一层在旧描…
- 判无依据 / 说明：verdict=proposal（3 条）。附交代两处险成候选却按红线留下的：①决策 4 首段 line 125「当前「定制」= 直接改 repo 里的 `worker/deterministic_steps.py` / `worker/deterministic.steps.ts`（fork 模式；两引擎各只有一条生效的内建注册——页面地址匹配），在 clone-repo 分发下成立、在 PyPI 化后不成立」——两条路径都已随包化失效（真值 engines/novaact/gherkai_worker_novaact/deterministic_steps.py、engines/midscene/src/worker/deterministic.steps.mts），一眼像沉积，但整句承载**决策 4 存在的 why**（「fork 模式在 PyPI 化后不成立」正是「定制面必须先画清」的理由，并解释了它为何同时决定决策 5 的镜像切面与决策 3 的 local 形态），删 why 断，留；②实测项第 4 条 line 219 的「**无凭证下已验** → **真账户已验** → **追加已验** → **待真账户**」四层叠加读着像施工节奏，但每层都是 Accepted ADR 内联的自包含证据（含「asset 在剥掉 site-packages 的解释器里真 import 抓出 `typing_extensions` 漏项」「对早于本机制的旧 stack 落迁移档退 2、不动账户」这类只有真跑才拿得到的具体值），按判据「Accepted ADR 内联的自包含证据」受保护，留（其末尾「待真账户」残留与节标题「已清零」的矛盾走客观项，见 findings 第 3 条，非提纯）。另：line 63/77 的「（当前 `gherkai/gherkai/names.py`）」「（当前没有）」两处在第五轮已作为 STALE 被对抗验证 REFUTED（理由：2a 表格列头「当前（施工前）」已在本节定义「当前」）；本轮不复议其 STALE 判定，只对 line 63 那句按*…
  - 提案（第 63 行）：目标态文档里凡指命名真源模块一律写 `gherkai_runtime.names`（当前 `gherkai/gherkai/names.py`）。 → 施工窗口期的**文档写作指令**（迁移期告诉写文档的人该写哪个名字）+ 一条已随目录改名消失的迁移前路径。三名分离的决策本身由同 bullet 前半句（「CLI 发行包叫 `gherkai`，当前的中间层 `gherkai` 让位改 `gherkai-runtime`」）与 2a 表格承载；此句不承载 why / trade-off / 不变量 / 被拒方案，也不是精确指针——`gherkai/g…
  - 提案（第 75 行）：dirty 状态下 `uv sync` 的解析行为列入实测项。 → Draft 期的待验 TODO 指针（「已排入待办」这层施工流水），实测项 1 已把该验证连同结论内联（「五个 wheel 的 `==` pin 与 extras 渲染正确、`uv sync` 解析通过」+「`uv.lock` 对动态版本的 workspace 成员只记 `source = { editable = "<dir>" }`、任意 commit 上 `uv lock --check` …
  - 提案（第 96 行）：；当前混在主依赖里的 pytest 挪去 dev group → 一次性搬迁指令，已完成且无再犯价值：engines/novaact/pyproject.toml 的 `dependencies` 只有 `nova-act>=3.4.187.0` + `boto3>=1.34`，dev 依赖统一在根 pyproject.toml 的 `[dependency-groups] dev`。它挂在 2c 依赖表的 extras 单元格里，前半句（「无（**不依赖 gh…

### docs/adr/0038-worker-image-delivery.md · none（0 提案）
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0038-worker-image-delivery.md → 仅 1 层：5d04676（code-health 批准项落地）。git show 5d04676 -- 该文件 → 纯新增 2 行（第 104 行那句「键名常量与路径构造**单点在 `gherkai_runtime.names`**（…九项…）」+ 空行），零删除、零改写，无「后层覆盖前层却留旧层」的痕迹。随后整读当前 192 行全文。
- 判无依据 / 说明：① 唯一新增层（5d04676 加的第 104 行）本身承载三样受保护要素：决策（键名与路径构造单点）、精确指针（逐个点名 `ssm_path`/`worker_template_key`/`worker_image_key`/`WORKER_DEFAULT_KEY`/`WORKER_IMAGE_ROOT_KEY`/`BACKEND_VERSION_KEY`/`SUBNETS_KEY`/`SECURITY_GROUPS_KEY`/`VPC_KEY`，与 runtime/gherkai_runtime/names.py:30-34/92/129/143 逐条对得上）、反模式（「曾在组合根、IaC 命名层、deploy 皮三个模块各写裸 `"version"`」）——不构成候选。② 本轮最像候选的是第 137–143「## 落地次序与依赖」整节（已全部落地的 1–5 编号步骤，形态即施工节奏）：不提，因为第五轮红线复核已对「删整节」逐条证伪并留下两条具名依据——步 1 括注「（可在 0037 之前先落：把当前 IaC 建的唯一 revision 当作解析结果，行为不变）」承载「为何该步能与 0037 解耦而行为中立」的 why，且 0037:216 同名节在 Accepted 下保留是 house style；当时只批「标题改完成态」，而第 137 行标题正是那个终态（「已全部落地，本节编号只在本节内部使用，其它文档不引用它」）。③ 第二像的是第 135 行的校准清单单句（`deploy_aws/README.md` 改写 / 两个 Dockerfile 补指针 / CONTEXT 去施工标记 / `tools/build_push_workers.py` 退役）——它已是第五轮把四条 bullet 压成一句的批准终态，再删是同一处第二次下刀。④ 另两处险成候选但各有护栏：第 52 行末「否则 CLI 跑在后端前面的人会把镜像静默推进一个没人解析的版本命名空间…形成死循环」与第 180 行被拒方案「push-worker 不校版本 skew」同一 why 两处成文，属本 A…

### docs/adr/0039-user-facing-surfaces-no-internal-references.md · proposal（2 提案）
- 层读：git log --oneline a97f912..HEAD -- 该文件：2 层。--stat：30ff262（+2/-1）、8470fa0（+3/-1），都是小改层，两层差异全读。30ff262 = 面二表追加「GitHub Release 正文」一行 + 护栏节 test_package_readmes 那条就地扩写（加 release body 扫描面、括注从「包搬家」改「包搬家 / workflow 改形态」）；8470fa0 = 面二表追加「agent skill」一行 + 护栏节新增 test_skill.py 一条 + 表前「四层只差去向与链接形态」→「各层只差……」（0043:135 明写「钉数字必再漂」）。两层均为纯追加或原地收紧，无「后层覆盖前层却留旧描述」的残留（旧句 76 处仅那一处被替换且替换彻底）。随后整读当前 75 行取证。
- 判无依据 / 说明：verdict=proposal，判无依据不适用。附交代本轮复核过、判留的三处（与第五轮 §六 对 0039 的判留一致，不重复提案）：① line 12「用户的判断（本 ADR 的起点，用户自己先改了一条 `compose.py` 文案）」= 决策来源与触发事件，决定重议门槛，留；② line 43「（曾因 TS 表更松漏掉一处「组合根装配错误」）」与 line 46「两轮对抗核验都在这一档抓到过遗漏（runtime 页面整篇行话、`--grace` 漏标「仅 run」、定位链顺序写反）」= 护栏为何长这样、为何还需人 review 的内联证据，留（前者本轮另有客观发现，属 code 侧未跟齐，不是删句问题）；③ line 24「实装时顺带的原则性修正：Nova worker 的信号 handler 曾在 handler 内 `log()`……」带「曾」框定 + 交去 0024 终止契约的指针，属历史框定 + 精确指针，留。
  - 提案（第 39 行）：搬家不是删：从使用者向文件移出的每条事实与踩坑，必须在对应 DEVELOPMENT.md 里找得到（实装时按旧文件逐字对照过）。 → 括注是一次性施工核对记录（「实装时……逐字对照过」），不承载 why / trade-off / 反模式 / 指针；前半句「搬家不是删……必须在对应 DEVELOPMENT.md 里找得到」才是不变量，删括注后它独立成立、约束力不减。与被保护的「内联证据」不同：这里对照的不是某个设计选择的支撑数据，而是「那一批搬家做过一遍人工核对」的过程流水，对未来读者/AI 不产生可复用判据。
  - 提案（第 75 行）：- 两条护栏测试的 docstring 指向本 ADR。 → 「对既有文档与 code 的影响」里唯一纯施工记账的一条：既非决策、非 why、非不变量，也不是指针（真指针在护栏节，那里逐个点名了测试文件路径），只记「实装那批顺手加了 backlink」。同一批次的第 73、74 条不同——它们记的是规则/被拒方案的落位（CLAUDE.md 压回规则、0037 被拒方案改指本 ADR），是跨文档单一真源映射，留。附带：该条的「两条」已随 test_skill.…

### docs/adr/0040-consumer-role-model-and-terminology.md · 沿用第五轮
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0040-consumer-role-model-and-terminology.md：零命中（自第五轮提纯审计 commit a97f912 起未被改动），按沿用条走。
- 判无依据 / 说明：沿用第五轮具名结论，锚定 a97f912^:docs/journey/0004-doc-health-round5-pending-approval.md §六（本地副本 /tmp/dhr6/round5-report.md:406-408），自 a97f912 起 git log 零命中。抄录该轮 §六 对本文的结论摘要：「层读 24943d8（区间内唯一层，86 行一次落盘：四顶帽子与正名表、帽子不是人、跑法权限梯、边界矩阵、术语真源与立新角色门槛、代价、被拒方案、影响），确认无第二层、无『后层覆盖前层』的叠加史；提案 1 条（P51：删影响节「全仓「test engineer」→「测试开发」（已落）」一行，落地状态由 Status 头承担），另判留两处——「用户补充的事实：……角色重合是常态、不是例外」属自包含的事实来源声明、直接决定决策 2 的重议门槛；Status 头「派生视图，改这里再改那里」与决策 5 第一条分工不同（维护告示 vs「单一真源」这条决策本身）、非副本。」本轮核对：P51 已随 a97f912 落地（当前影响节只剩 README / CONTEXT.md / 0020+0038 三条，无 test-engineer 行），两处判留句仍在原位（line 17、line 3），沿用成立。

### docs/adr/0041-agent-facing-cli-affordances.md · none（0 提案）
- 层读：git log a97f912..HEAD 命中 7 层：9b96824 初版（+66 行）→ eb057cf 对抗审查 33 条（26 行改，本文件最大改层）→ 6f5eda4 加 --scope（只改决策一标题 1 行）→ 152abce 真跑证据内联（+1 行）→ 8b86e98 / 8470fa0 / d910c1b 各 2–6 行反向链与 Status 头。对 eb057cf 与 6f5eda4 两层做了 git show 差异读，其余三层按 stat 判为单行反向链改动。
- 判无依据 / 说明：层读的史实：eb057cf 是**整句替换式**改写（diff 里 `-`/`+` 逐句成对，决策一、二、三、四各段旧句无一句被留在文旁），故没有「新旧两层并存」的沉积；唯一的旧层残留是决策一被拒项里的「两个 flag」（已按 CONTRADICTION 单独报，属纠错不属提纯）。逐句过筛后两处险成候选、因承载受保护要素留下：第 30 行整段「真跑坐实（跳板机本机 novaact run）」看似流水账，实为 Accepted ADR 内联的自包含证据（worker.log 38 行零 ANSI、`--backend cloud --quiet` 不建该文件、同步 run 的 run_state 无 high_water_mark），删了「决策二为何是这个形态」就失去实证；第 31 行「句柄生命周期」段里「带超时是因为定位链第 4 级 uvx 是包装进程、孙进程可能仍持写端」是不变量成因，不是施工节奏。

### docs/adr/0042-step-evidence-and-explain.md · proposal（2 提案）
- 层读：git log --oneline a97f912..HEAD -- docs/adr/0042-*.md = 14 层。--stat 挑大改层后 git show 逐个读差异：214db19（Draft 建档，含「## 验证（Accepted 前必做，结论内联到此处）」+ 单测/真跑两条计划）、1d10101 与 14f5989（真跑回修 / 对抗审查 18 条）、14a00d6（explain 文本 key 统一为 JSON 字段名，样例改写 + 新增「文本 key = JSON 字段名」段）、bfc6ed1（决策一「上传时机」段与闸门条整段替换为后台队列形态）、c7e7c1d → eb7ab9a → ec0187c → a58cd40 → 2cf0237（验证节逐次内联真跑结论）。层读史实两条：bfc6ed1 是**整段替换**、决策一与闸门条无旧层残留（但同批漏了「被拒方案」与 0029 的两处旁引，已作 CONTRADICTION 报）；验证节相反，是「新结论 prepend、旧计划留底」的叠加式增长——c7e7c1d 起把实测段插在计划清单之上，eb7ab9a 只把节标题从…
- 判无依据 / 说明：非判无。逐句过时险成候选但因承载受保护要素留下的三处：① 第 191 行「决策一已改为「step_done 后进后台队列上传 + 收尾有界排空 + 重试一次」，取代最初「只靠 scope 末 flush」的形态——那个形态有两面风险：…」看似「先做 X 后改成 Z」的施工节奏，实为红线明列的历史框定 + 被拒形态的风险论证（提前退出路径不 flush / flush 单次无重试 → 永久 404 URI），删了未来读者会重提「只靠 flush」；② 第 143 行「**护栏盲区两处，手工补**：契约页按裸键名比对、`message` 已在 job 级出现过，step 级漏写不会变红；round-trip 样例全 None 时照不出漏读端」带「手工补」施工语气，但正文是两条真实的护栏失效机制（反模式/不变量），保留；③ 第 235 行「**对抗审查真跑核出并已吸收**：…boto3 `upload_file` 默认交 s3transfer 非 daemon 线程池 → 黑洞端点下 drain(1.0) 后进程 11.2 s 才退…改 `TransferConfig(use_threads=False)` 后 1.15 s」是 Accepted ADR 内联的自包含证据（CLAUDE.md「值得让 ADR 长一点」），且给出了 `use_threads=False` 这条不变量的唯一理由。
  - 提案（第 241 行）：- 真跑（跳板机；**先重传 Lambda asset + 推新 worker 镜像**，否则 cloud 档必然看不到 message / evidence、易误判成 bug）： → Draft 期的「待做真跑清单」四条子 bullet 已被同节前面的实测结论段逐条完整覆盖（本机档 line 225-229、cloud 档 line 231、submit 路径 line 233、后台队列真跑 line 235），且前者更详细、带数字与原文；括注里的部署 gotcha 已在「交付链」节 line 218-219 写明。它不承载决策 / why / 权衡 / 不变量 / 历史框定，…
  - 提案（第 206 行）：**文档（反向链逐处列出，Accepted 前逐条核）** → 「Accepted 前逐条核」是 Draft 期给自己下的施工指令，Status 头（line 3）已声明「影响面所列反向链（0024 / 0027 / 0029 / 0032 / 0037 / 0041 / CONTEXT）已逐条落」，指令已执行完毕；「反向链逐处列出」这半句仍有导航价值，保留。

### docs/adr/0043-agent-skill-for-driving-gherkai.md · proposal（2 提案）
- 层读：git log a97f912..HEAD 命中 19 层。按 --stat 挑大改层并 git show 读差异：79c0e91 Draft（+98）、46607c1 重写（130 行改）、6876685 二轮审查 33 条（57 行改）、d910c1b 翻 Accepted（30 行改）；其余为小改层（0280ed2 / be8ceee / f471129 / d4d57ff / e5feca7 / d5ab0c4 / dcace9b 23 行 / 085becd / f5f0c47 9 行 / bd08b17 10 行 / ada9d6c 10 行）与三层纯追加的验证轮（13ea5c6 / d75aa61 / a0839ba）+ 240e765 待办一行。46607c1 的 diff 证实早期草案的机制（真身放仓库根 `skills/gherkai/`、`.codex/skills` 作 Codex 落点、`npx skills add owner/repo --skill`、幂等覆盖、「不花 AWS 钱」）被整句删除、只以「被拒方案」条目带框定复活，正文无残留。
- 判无依据 / 说明：proposals 之外逐句过筛，几处最像流水账的段落都因承载受保护要素保留、未提案：决策一第 18 行 force-include 段（`uv build` 先出 sdist 再构 wheel 故跨根 force-include 必 FileNotFoundError、只写 sdist target 则 editable 树静默漏文件）是被拒方案护栏；决策七第 78/90 行的三条硬规则各自绑一次实测污染事件（148 次工具调用里 54 次触仓库、共享 venv 被某个 baseline 改出放行开关、同名舞台把上一次 run 的 memory 灌进新会话），删任一句即失去「为何要随机舞台名/只读 CLI/副本不可枚举」的成因；第 88 行「为什么是物化式而不是程序化生成」是权衡本身。
  - 提案（第 145 行）：护栏实装中两处偏离设计已回写决策六：JSON 键真值集取契约页字段表**任一列**加散文行（首列-only 会把 `kind` / `ref` / `votes.yes` 等真键逼进「非键豁免表」）；fixture 绝对路径不变量只认已知机器根（`/Users` `/home` `/tmp` `/var` `/app`… → 两条的结论**连同理由**已完整住在决策里：决策六第 69 行「真值集取契约页字段表**任一列**里的反引号键加「顶层 / 每项 …」散文行记的键（`report_refs[]` 行的 `kind` / `ref`、`votes` 的 `yes` / `total` 这类真键只出现在含义列，首列-only 会把它们逼进非键豁免表、语义反了）」，决策七第 85 行「曾试「JSON 里以 `/` 打头…
  - 提案（第 159 行）：评分者对评测集的批评（复合断言拆条、`--help` 不算执行、缺正向断言）留在 `evals.json` 的 notes 里待下轮。 → 这条「留待下轮」已被紧随的下一轮消化：第 160 行开头即写「评测集按第三轮评分者的批评收紧到 94 条断言（复合断言拆条、放行开关与投票判据正向化、禁绕过式修复、正则须匹配真实落地地址、禁留新 run 目录、「`--help` 与只读命令不算执行」统一）」——同一份批评在相邻两段各写一遍，前一遍只剩「当时还没做」的时间坐标，是逐层追加留下的过程编号式残留（第 169 行末尾的第四轮同款句同理，已…
