> 类型: 调查记录

# 移动真机支持（1.5）：实施批次的改动面与先写的护栏测试

由实施规划 workflow 在 2026-10-16 产出：每个批次一个规划者，读点名的 ADR 与代码，给出改动面、先写的测试、依赖、真跑核对与易错点；规划者提出的设计缺口经逐条对抗复核，成立的已补进 ADR（见 journey 0013 现场）。次序与进度在 journey 0013；本文是各批的施工底稿，实施时按代码现状校准，批次完成后删去对应一节，全部完成后删除本文。行号与符号以产出当时的代码为准。


## 0. B0-navigation：导航规则与注册面关键字声明（1.4 行为的不兼容变更，自己发）

规模 M。来源：2026-10-26 的 0020 修订（导航判据改为「Given / When 后整句是一个地址」，内建「页面地址匹配」step 退役，注册表条目可声明关键字），见 0020 第 2、3 条、0050 决策 1、0048 决策 7。

**进度（2026-10-26）**：已落地并提交（落地 code 与文档各一笔，复核处置再各一笔，闭合处置再各一笔），两引擎桌面真跑核过（跳板机）：不带引号的整句地址导航、Then 后只有地址记 error、`shop://` 在网页目标记 error、导航 step 带 DocString 记 error、句中带地址走 AI、`features/steps` 的页面地址匹配按确定性执行；处置后 pytest 2008 绿、Midscene 207 绿。双轨复核（我这边七路窄核对加对抗驳回、Codex 第十七轮）合计确认并处置：① 不带引号的地址末尾是标点或右括号时模式仍命中（与 0020 第 3 条「不剥标点」相悖）——模式加末尾标点排除，引号内一律原样；② 模式里的 `\s` 两种正则方言字符集不同（BOM、U+0085）——改为只认 ASCII 空白；③ Midscene 把确定性 handler 抛的错按消息文本启发归 network_error（`shop://timeout` 被误归）——handler 抛的错不按消息文本分类，对齐 Nova 按异常类型；④ 组合根对 keywords 的校验先 set() 再核类型（非字符串元素抛 TypeError 绕过契约错误）、显式 null 被当缺键——改序并只认缺键；⑤ 补护栏：对拍夹具加末尾标点、BOM、U+0085 用例并加 registry 段（同一组注册输入两侧清单 keywords 与 match_batch 四态一致，含使用方宽模式与内建导航冲突）、两侧 error 路径核 errorType 与不转 AI、DataTable 形态、Midscene 的 `--match-steps` 真入口按 `{keyword, text}` 回答、组合根 keywords 正例与新契约载荷、list-deterministic 子集显示；⑥ 文档残留：两个包的 DEVELOPMENT、ADR 0020 / 0022 / 0024 / 0036 / 0037 / 0043、契约页「三键」、用户指南的多行参数与四列、skill 的多行参数与口语措辞、CHANGELOG 对 plan 标注的误述；⑦ 录制报告夹具（wiki-search、nova-zh、job-failure）的 step 原文随导航写法改为整句地址，job-failure 补 steps/ 成对文件。未处置并记下：契约页护栏按全页扁平键名核对、删掉 list-deterministic 节的 keywords 说明仍能过（既有设计限制，不在本批）；评测第 1 条的需求前提与 example.com 现状不符（见下方「与下方底稿的出入」第 ⑥ 条）。闭合轮（我这边五路核对、Codex 第十八轮）再处置：ADR 0020 第 3 条补写地址边界的细化（空白的显式集合、引号内原样、末尾标点集合）；空白加 U+00A0 与 U+3000，末尾标点集合补全角右括号、全角句点、省略号、右引号；Midscene 对命中多条的冲突也在派发处直接记 engine_error；组合根拒绝非对象的清单项；`--match-steps` 真入口补 conflict 一态，跨语言夹具加 keyword 为 null 的探针；skill 口语「撞」改书面。再一轮（Codex 第十九轮）：注册表层面的 error 消息（关键字不符、命中多条）两侧都走同一条有界归一化、不带异常类型名，Nova 的冲突也改为在派发处直接记。Codex 第二十轮总判定：这一批可以视为「设计已落到位」。另记一项既有的低优先级差异、不在本批：两侧错误文本归一化的分行与空白规则不完全对称（Python 的 splitlines / split 认 U+2028 等 Unicode 行列分隔符与 Unicode 空白，Midscene 只按 CR / LF 分行、按 JS 的空白折叠），`A\u2028B` 一侧得 `A`、一侧得 `A B`。与下方底稿的出入：① 「全仓不再出现『页面地址匹配』措辞」的 grep 守卫不立——该措辞作为 `steps/` 模板名合法出现在文档与 `features/steps/`，改以脚手架差集测试守（两引擎自述清单只有内建导航一条）；② 跨语言 fixture 落在 `engines/fixtures/navigation-address-cases.json`，两引擎单测共读；③ 内建导航的 description 定为「内建导航：整句只是一个地址时直接打开它（网页目标只接受 http(s) 地址）」；④ 关键字不符的错误消息按条目的 description 点名、末尾给改法；⑤ 真跑发现 example.com 页面已无「Example Domain」大标题，`engine_routing.feature` 与 getting-started 示例的断言随之改写；⑥ 评测集里以「打开 https://example.com/ 看到大标题 Example Domain、点 More information」为需求的那条用例前提已与该页现状不符，评测只做 plan 不真跑、暂未改。

**依赖**

- 无；改的是 1.4 已有行为，两个 worker 与 CLI 同批发。后续批次以它为前提：B1 的注册表条目 targets 测试按退役后的清单写；B4 的注册面在 keywords 之上加 targets / requires；B6 的设备导航复用内建导航条目的 webdriver 句柄。

**改动面**

- `engines/midscene/src/worker/run-scope.mts` · 派发（URL_IN_QUOTES 分支）：删去「引号内网址」分支，派发只剩注册表命中与 AI 两段；注册表命中但关键字不符时记 error、消息按 0050 决策 1（0020 第 3 条、0024「worker 派发」段）
- `engines/novaact/gherkai_worker_novaact/run_scope.py` · 派发（_URL_IN_QUOTES 分支）：同上（0020 第 3 条）
- `engines/midscene/src/worker/deterministic.mts` 与 `deterministic.steps.mts` · 注册面与脚手架：条目加可选 keywords（Given / When / Then 子集，注册期校验）；match() 接收关键字、区分「未命中」与「命中但关键字不符」；脚手架只留内建导航条目（模式 = 去掉关键字后整句为地址，引号可有可无；playwright 句柄打开 http(s)，非 http(s) 记 error），删「页面地址匹配」（0050 决策 1、0020 第 2 条）
- `engines/novaact/gherkai_worker_novaact/deterministic.py` 与 `deterministic_steps.py` · 注册面与脚手架：Python 同构——keywords、match(keyword, text)、内建导航条目、删「页面地址匹配」（0050 决策 1）
- 两侧的 listRegistry / list_registry · 能力自述：清单项带 keywords（缺省全部）；内建导航条目的 description 为「内建导航：整句只是一个地址时直接打开它（网页目标只接受 http(s) 地址）」、example 为 `Given "https://www.wikipedia.org/"`（0036、0049 决策 6）
- `cli/gherkai_cli/__main__.py` 与 `render.py` · plan 标注、list-deterministic：导航按确定性 step 标注（网页目标「内建导航：打开 <地址>」；应用目标「内建导航：经 DeepLink 交给被测应用」在 B6 落地后出现）；Then 后只有地址在 plan 里标为错误写法——由 worker 的派发探针以 keyword_mismatch 报出，CLI 只转述；网页目标非 http(s) 地址 plan 不预检、执行时由 playwright 句柄记 error（0020 第 3 条、0048 决策 7）
- `docs/internals/cli-json-contract.md` · plan 的 steps[].deterministic 与 list-deterministic：加 keywords 键；导航条目的形态与说明（0036）
- `features/*.feature`、core/tests、cli/tests 里的用例与夹具：`Given 打开 "…"` 改为 `Given "…"`；依赖内建「页面地址匹配」的用例改用测试自带的 steps/ 夹具（0018）
- `cli/gherkai_cli/skills/gherkai/SKILL.md`、`references/*.md`、评测集：导航写法、落点核对规则、deterministic-steps 参考加地址核对模板；评测断言同步（0043、0048 决策 7）
- `docs/user-guide/writing-features.md`、`writing-deterministic-steps.md`：导航写法；删「内建的确定性 step」节、加 steps/ 模板节（0020）
- `CHANGELOG.md` · Unreleased：不兼容变更两条——导航写法改为整句地址（含引号网址的旧写法改走 AI）；内建「页面地址匹配」step 退役（0020）

**先写的护栏测试**

- 两侧 deterministic 测试：内建导航模式——带引号与不带引号的地址都命中；地址前后有空白仍命中；句中还有其它文字不命中；两个引号参数不命中；Then + 整句地址得到「命中但关键字不符」；网页目标 playwright 句柄遇非 http(s) 地址记 error 并给消息（0020 第 3 条）
- 两侧注册期校验测试：keywords 取值封闭集合；使用方条目的模式也匹配裸地址时按 0022 冲突规则报错（0050 决策 1、0022）
- 跨语言 fixture：同一组注册输入两侧推出相同的清单项（含 keywords）与匹配结果（0050）
- 脚手架差集测试：两个脚手架文件除内建导航外不再注册任何条目；全仓用户文档、skill、features 不再出现「页面地址匹配」措辞（0020 第 2 条）
- `cli/tests/test_main.py`、`test_cli_json_contract.py`：plan 对导航 step 的标注形态与确定性 step 一致；错误写法的标注；keywords 进契约页（0020 第 3 条）

**真跑或对抗核查才算数的结论**

- 两引擎本机真跑一条只含整句地址导航与 AI 断言的 feature（桌面），确认派发与 plan 标注一致——已做（见上「进度」）；`tools/e2e_harness.py` 读的 features/ 已随导航写法改写，本批未另跑它。

**易错点**

① 把 Then + 整句地址交给 AI 或顺延到别的模式——必须是注册表的通用「关键字不符」错误。② 在 CLI 里复写地址识别去做 plan 标注——识别只在 worker，plan 只转述派发探针的结果。③ 删内建 step 时漏掉依赖它的 e2e 夹具与 skill 评测断言，用脚手架差集测试与全仓 grep 守。

## 1. B1-capabilities：能力自述增键（两个 worker 只声明桌面网页；CLI 唯一校验处与交集；doctor、list-deterministic 呈现）

规模 M。

**进度（2026-10-26）**：已落地，待真跑核查与双轨复核。与下方底稿的出入：① 交集与缺键语义不挂在缓存对象上、不改写自述对象——`compose` 提供纯函数 `worker_targets` / `step_targets` / `available_targets` / `unsupported_targets`，`list-deterministic` 与 doctor 调用它们，契约校验仍只在 `query_capabilities` 一处；② 没有加 `engine_targets(engine)` 访问器，doctor 用的是它已拿到的那份自述，等本机执行前预检（B2）有消费者时再加；③ plan 按目标标注这一项按底稿所述挪到 B2 之后；④ 引擎能力矩阵的差集测试按 CI 的两个 job 拆成两份：pytest 侧核表格结构与 Nova 行（真起 Nova worker），npm 侧 `engines-matrix.test.mts` 核 Midscene 行（真起 Midscene worker），两侧合起来覆盖「多一行、少一行、值不符」；⑤ 会话预热支持键定名 `session_warmup`（顶层布尔，worker 本批不发）；⑥ 目标的产品语言名称放 `cli/gherkai_cli/render.py`（`target_label` / `targets_label` / `requires_label`），doctor 的会话上限按分钟显示；⑦ 用户指南 README 的篇目表顺手改掉第 0 批遗留的「双引号地址直接导航」。 兼容性真跑（跳板机，2026-10-26）：新 CLI 读 1.4.9 的两个 worker——doctor 的目标行按缺键语义显示桌面网页、list-deterministic --json 带 available_targets、不报契约错误；旧 1.4.9 CLI 读新 worker——doctor / list-deterministic / plan 照常（多余键被容忍）；新 CLI 读新 worker——两引擎目标行与 available_targets 都对。另见一处第 0 批的版本不一致形态：新 CLI 对 1.4.9 worker 的 `--match-steps` 送 `{keyword, text}`，旧 Nova worker 抛 TypeError 使 plan 以退出码 2 结束、旧 Midscene worker 对对象原样匹配得 null 使步骤静默标为走 AI；两者都在「worker 与命令行工具须同版本安装」的既有规则之内，不另做兼容分支，只把 plan 这条失败的消息改为点出版本不一致的成因（与其它入口同一句提示）。 双轨复核（我这边六路核对加对抗驳回、Codex 第二十一轮）确认并处置：① 顶层与 step 级 `targets`、step 级 `requires` 的显式 null 曾被当缺键放行（requires 为 null 时消费点抛 TypeError）——只认缺键，null 不合契约；② 三项全同的重复判定曾按列表顺序比较——改为按集合比较；③ `max_session_s` 与 `min_grace_s` 遇超出 float 范围的整数曾抛 OverflowError——归为不是有限数；④ list-deterministic 对声明了但不支持的目标曾不显示前提——改为同样带前提原样显示（ADR 0049 决策 1 只豁免 doctor）；⑤ 模式列曾改为可折行，与 ADR 0047「标识列永不折断」相悖——回到不折行（内建导航的模式很长、表会撑宽，要原文用 --json；若要改规则须先改 0047）；⑥ 护栏补齐：null / 非字符串元素 / 顺序不同的重复 / 同 device 两条都带上限 / step 级 device 与 ui_kinds 规则 / 超大整数 / 空交集与声明顺序 / 不支持目标带未知前提；契约页护栏加 doctor 项名（`name` 的值）对照、list-deterministic 样例改取真实命令输出；矩阵测试加「目标名只能是产品名称」把两侧名称拼法钉在 render 一处；⑦ 文档：engines.md 去掉对尚未落地的 plan 按目标标注与 webdriver 句柄的承诺、去掉指向尚无设备内容的 writing-features 指针，troubleshooting 的 `steps.load` 出现条件补目标行，configuration 的 doctor 读法补测试目标，根 README 文档表登记矩阵页，ADR 0049 决策 3 的「在契约校验同一处计算交集」改为「同一组合根模块的纯函数、消费点调用」以与实现一致；plan 失败文案去掉内部协议名并与其它入口同格式。Nova 的自述整条拷出 targets（将来加 max_session_s 不会被丢）；doctor 对空目标清单显示「无」、分钟数非整数时留一位小数。 闭合轮（Codex 第二十二轮）：1 到 6 已到位；余项——确定性 step 查询失败的文案在异常源头仍带协议名「match 查询」——已改为「确定性 step 查询」并加对异常源的回归。 Codex 第二十三轮总判定：这一批可以视为「设计已落到位」。


**依赖**

- B2-core-target-job：Job 带目标（device、ui_kind）。plan 按 scope 目标标注确定性还是走 AI，要靠它；在它之前 plan 的目标一律当 desktop/web，这一项可以挪到 B2 之后
- B4-steps-registry：从句柄（playwright/webdriver、uiKinds、devices、requires）推出 step 级 targets。B1 先在 list_registry/listRegistry 写死 desktop/web，B4 换成推出值，输出形态不变
- B6-midscene-device：Midscene 顶层 targets 的 android/ios 条目，以及从设备释放预算常量算出的 max_session_s；B1 只做 CLI 侧校验和 doctor 的分钟数展示
- B7-tunnel：会话预热支持键由 worker 发出；本机 --expose-local 遇不声明的 worker 就拒绝，这条检查归 B7。B1 只把键名和 bool 校验定在 compose
- B5-core-events-termination：worker 自检（决策 7）的 scope_done{status: error, errorType: precheck_failed} 怎么传、core 怎么接住；B1 只提供 worker 侧 targets 的单一来源

**改动面**

- `engines/novaact/gherkai_worker_novaact/run_scope.py` · _capabilities()（约 777 行）及其上方 CAPABILITIES_SCHEMA_VERSION：自述对象加顶层 `targets`，显式写出 `[{"device":"desktop","ui_kinds":["web"]}]`，不带 max_session_s。targets 抽成模块级单一来源（如 WORKER_TARGETS 常量或 _targets() 函数），供之后 worker 侧建会话前的自检复用，不在自检里另写一份。schema_version 保持 1。会话预热支持键本批不发：缺键就表示不支持，等 Nova 实现预热时再加。（0049 决策 1、2、9；决策 7（targets 单一来源））
- `engines/novaact/gherkai_worker_novaact/deterministic.py` · list_registry()：每个条目加 `targets: [{"device":"desktop","ui_kinds":["web"]}]`。现在的 _Entry 只有 playwright 一种句柄，本批按 0050 的推出规则写死 desktop/web；改成从句柄推出、带 webdriver 条目和 requires，归注册面那一批。worker 原样报出、不与顶层 targets 求交。（0049 决策 1、3；0050 决策 1（推出规则））
- `engines/midscene/src/worker/run-scope.mts` · main() 里 `--capabilities` 分支（约 408 行）与 CAPABILITIES_SCHEMA_VERSION 附近：加顶层 `targets`。本批只写 desktop/web；android/ios 条目和 max_session_s 等设备模块落地时再加，max_session_s 从设备释放预算常量算出，那些常量现在还不存在。targets 同样抽成导出的单一来源（如 WORKER_TARGETS），之后的自检复用。（0049 决策 1、2、4、7）
- `engines/midscene/src/worker/deterministic.mts` · listRegistry() 返回类型与实现：每项加 `targets: [{device:"desktop", ui_kinds:["web"]}]`，返回类型声明里加 targets（以及可选的 requires 字段形态）。现在 Entry 只有 playwright handler；按句柄推出、拆分 requires 归注册面那一批。（0049 决策 1、3；0050 决策 1）
- `runtime/gherkai_runtime/compose.py` · query_capabilities() 契约校验段（约 516 到 558 行）：在同一处加新键的形态校验，不合即抛 RuntimeError、不写缓存：顶层 targets（可缺；数组，每项 device ∈ {desktop, android, ios}，ui_kinds 非空且 ⊆ {web, app}，desktop 只允许 [web]，max_session_s 可缺，有则为正有限数并排除 bool）；deterministic_steps[*].targets（可缺；同样的 device/ui_kinds 规则，requires 可缺，有则为字符串数组，取值不核）；会话预热支持键（可缺，有则为 bool；键名本批定下来）。缺键按决策 2 补成缺省值（顶层与 step 级缺 targets 都视为 desktop/web）。（0049 决策 1（校验位置不变）、决策 2）
- `runtime/gherkai_runtime/compose.py` · 新增交集函数（与 query_capabilities 同模块，例如 available_targets(step_targets, worker_targets) 与「声明了但不支持」的差集函数）：按 device 匹配、ui_kinds 取交、结果为空则丢弃，每个条目原样保留 requires；同一 device 与 ui_kind 只是 requires 不同的条目各自成条、不合并。结果在校验处算好、挂在缓存对象上（或与原样字段并列），plan、list-deterministic、doctor 只消费这份结果、不各自求交。（0049 决策 3）
- `runtime/gherkai_runtime/compose.py` · 新增 engine_targets(engine)（与 engine_min_grace 对称）：从该引擎任一份缓存取顶层 targets（与 steps 目录无关），没有缓存才无 steps 地问一次。本批给 doctor 用，后续本机执行前预检（目标是否支持、墙钟是否超过 max_session_s）复用。CLI 里不按引擎名硬编码。（0049 决策 4、6、9；被拒方案「CLI 按引擎名硬编码」）
- `cli/gherkai_cli/__main__.py` · _cmd_list_deterministic()：文本表格加「目标」列，列出交集目标（用中文目标名，如「桌面网页」「Android 网页」），带 requires 的条目附「需要网页上下文」；声明了但该引擎不支持的目标单独注明（「声明了 Android 应用，此引擎不支持」）。--json 每项保留 worker 原样报出的 `targets`，另加 `available_targets`（条目保留 requires）。不按目标过滤。（0049 决策 6）
- `cli/gherkai_cli/__main__.py` · _cmd_doctor()，engines 段 model.<engine> 行之后：每个自述成功的引擎加一行 `targets.<engine>`（required=False，纯展示），与模型行用同一份 caps；带 max_session_s 的目标附分钟数；不展示 requires；不支持设备不算失败；自述失败时不出这一行（与模型行同一口径）。（0049 决策 6）
- `cli/gherkai_cli/__main__.py + cli/gherkai_cli/render.py` · _probe_deterministic_dispatch()、render_plan_text()、plan_to_dict()：plan 按命中结果里的 pattern 到自述清单找该条目的交集目标，再与 job 的目标比对：不含该目标的 step 改标走 AI 并写明原因；带 requires 的写明前提（「需要网页上下文；设备不提供时记为错误」）。命中的条目在该目标上没有句柄时不顺延到下一条 pattern。这一项依赖 Job 带目标，job 的目标在那之前一律当 desktop/web；也可以把这一项挪到 Job 带目标之后再做。（0049 决策 3、6；0050 决策 1）
- `cli/gherkai_cli/render.py（或新的共享模块）` · 目标的产品语言名称映射：(device, ui_kind) 映射到中文名（桌面网页 / Android 网页 / Android 应用 / iOS 网页 / iOS 应用），list-deterministic、doctor、plan 共用一份；文案过用户可见文本的护栏。（0049 决策 6；ADR 0039）
- `docs/user-guide/engines.md（新增）+ 差集测试` · 引擎能力矩阵：表格列：引擎 × 目标 × 确定性句柄种类 × 默认模型 × 计价公式（只写公式）；差集测试逐行对照两个 worker 在无环境变量覆盖时的自述（targets、model_id），句柄种类按固定规则从目标推出。按 CLAUDE.md 同步校准 docs/internals/cli-json-contract.md、writing-deterministic-steps.md 与 getting-started / troubleshooting 里的 doctor 读法。（0049 决策 8）

**先写的护栏测试**

- `engines/novaact/tests/test_capabilities.py`：真子进程：键集全等断言改为六键（加 targets）；targets == [{device: desktop, ui_kinds: [web]}]，不带 max_session_s；schema_version 仍是 1；deterministic_steps 每项键集为 {pattern, description, example, keywords, targets}，内建导航条目的 targets == [desktop/web]、keywords == [Given, When]。（0049 决策 1、2、9）
- `engines/midscene/src/worker/run-scope.test.mts`：同上，真进程跑 --capabilities：六键全等，targets 显式含 desktop/web，desktop 条目不带 max_session_s，清单项含 targets；min_grace_s 断言本批不动（升到约 64 秒归设备收尾那一批）。（0049 决策 1、2、5）
- `runtime/tests/test_compose.py`：扩 test_query_capabilities_rejects_off_contract_answer 的参数表：未知 device、ui_kinds 为空、未知 ui_kind、desktop 带 app、max_session_s 为 0/负数/字符串/true/Infinity、step 级 targets 不是数组、requires 不是字符串数组、预热键不是 bool → 都抛 RuntimeError 且 _CAPABILITIES_CACHE 为空。另加正面用例：requires 含未知字符串（如 "foo"）时放行并原样保留。（0049 决策 1）
- `runtime/tests/test_compose.py`：缺键语义：顶层缺 targets 与 step 级缺 targets 都归一为 desktop/web；缺 max_session_s 表示无上限；不能被解释为「全部目标」。多出来的未知顶层键照旧容忍（向前兼容）。（0049 决策 2）
- `runtime/tests/test_compose.py`：交集是纯函数：step 声明 desktop/web + android/[web,app] + ios/[web]，worker 只有 desktop/web 时 available 只剩 desktop/web、差集列出 android 与 ios；同一 device 与 ui_kind 只是 requires 不同的两条结果各自保留、不合并；requires 原样带入；worker 有 android/[web] 而 step 声明 android/[web,app] 时结果为 android/[web]。（0049 决策 3）
- `cli/tests/test_main.py`：list-deterministic --json：每项同时有 targets（原样）和 available_targets（交集），两者分开；文本视图含目标列、「此引擎不支持」注明和前提标注。doctor：有 targets.<engine> 行、required=False，带 max_session_s 的目标显示分钟数，requires 不出现，自述失败时没有这一行。（0049 决策 6）
- `cli/tests/test_cli_json_contract.py`：test_list_engines_and_deterministic_json_keys_are_documented 的样例加 targets / available_targets（含 requires）；doctor 样例 caps 加 targets（含一个带 max_session_s 的设备条目），使 targets.<engine> 项名进入文档对照。（0049 决策 6）
- `cli/tests/ 下新增引擎能力矩阵差集测试（如 test_engines_matrix.py）`：解析 docs/user-guide/engines.md 表格，与两个 worker 无环境变量覆盖时的自述逐行比对（targets、model_id、由目标推出的句柄种类），多一行、少一行、值不符都失败。（0049 决策 8）
- `新增跨语言一致性检查（两侧各自的测试，或共用 fixture）`：两个 worker 的顶层 targets 与清单项 targets 的字段名、形态一致（snake_case 的 ui_kinds/max_session_s/requires，TS 侧不能写成 uiKinds 驼峰），否则 CLI 校验会对某一侧报 fail-loud。（0049 决策 1；0050 决策 1（跨语言 fixture））

**完整性审查补认领**

- 红线测试补：顶层重复 device（尤其同 device 带不同 max_session_s）、重复的 ui_kinds 或 requires 元素、完全重复的 step 条目都拒绝且不写缓存。0049 决策 1。

**真跑或对抗核查才算数的结论**

- 新 CLI 读旧 worker：装已发布的 1.4 worker（PyPI 上的 gherkai-worker-novaact，npm 上的 @gherkai/worker-midscene），用新 CLI 跑 doctor 和 list-deterministic。要真跑确认缺键语义生效：显示桌面网页、不报契约错误。
- 旧 CLI 读新 worker：已发布的 1.4 CLI 指向本批 worker（GHERKAI_WORKER_*_CMD），确认 run/doctor/list-deterministic 照常。「只核已知键、容忍多余键」现在只是读代码得出的结论，要真跑一遍才算数。
- 两个 worker 真进程跑 --capabilities，加上 CLI 真调起 worker（不 mock _ask_worker）走一遍 list-deterministic --json 和 doctor --json。确认 TS 侧输出的键名是 snake_case，交集和差集在真自述上算得对。
- 引擎能力矩阵差集测试在 CI 里真能拿到 Midscene 的自述：pytest job（uv）和 midscene npm job 是分开的两个 job，pytest 环境里未必有能运行的 Midscene worker。要在 CI 上跑出来，确认它没有被跳过。
- （B6 之后，不属本批）max_session_s 与 150 分钟上限的实际余量要在 Device Farm 真机上核：会话年龄到 max_session_s 时释放完成、不被服务端提前关掉。

**易错点**

一、最容易做错的是提前宣称设备能力。journey 把 0049 定为「零风险、可独立发」，前提是本批两个 worker 的顶层 targets 都只写 desktop/web。Midscene 的 android/ios 条目和 max_session_s 要等设备模块和释放预算常量落地后再加，否则新 CLI 会把设备 job 交给一个还不会驱动设备的 worker。max_session_s 不准在 CLI 或文档里写字面量（比如 8880），只能由 worker 用常量算出（决策 4）。

二、校验和交集都只在 compose.query_capabilities 那一处做，然后把结果交给 plan、list-deterministic 和 doctor。不要在各消费点各自求交或各自补缺省值；也不要让 worker 先求交（决策 3 的被拒方案）。

三、TS 侧对外的键必须是 snake_case（ui_kinds、max_session_s），不能把注册面的 uiKinds 驼峰直接写进自述。现有两侧测试都断言自述键集全等，本批要同步更新，这正好当作契约闸门。

四、doctor、list-deterministic 的目标名和「此引擎不支持」这类说明都是人读文案，要过 test_user_facing_messages 与 ADR 0045 决策六的措辞清单。改完要按差集校准 docs/internals/cli-json-contract.md（已提前写了 targets、available_targets 和 targets.&lt;engine&gt;）以及新的 engines.md。

五、按决策 9，Nova 只有桌面这件事只能由自述表达，CLI 不得按引擎名分支。

涉及的主要文件：/Users/lzy/workspace/yaozhou/runtime/gherkai_runtime/compose.py、/Users/lzy/workspace/yaozhou/cli/gherkai_cli/__main__.py、/Users/lzy/workspace/yaozhou/engines/novaact/gherkai_worker_novaact/run_scope.py、/Users/lzy/workspace/yaozhou/engines/midscene/src/worker/run-scope.mts。


## 2. B5-core-events-termination：core 侧会话事件、scope 级 error、合成 SKIPPED、终结函数与真值表、计量合计、explain 呈现

规模 L。

**进度（2026-10-26）**：已落地（model / wire / errors / serialize、project 的会话归约与代表会话、合成 SKIPPED、终结函数 `finalize_job` 与真值表、设备计量；schedule 的 stop_reason 首次仲裁与停止后有界消费；persist 的代表会话；render / 报告页 / explain 的设备摘要与合成 skipped 旁注；FakeEngine 的收尾事件与非零退出码），单测含真值表逐行、代表会话、合成 SKIPPED、计量、双路径对拍八行、停止后排空、首次仲裁三分支、SIGKILL 负码、零 scenario；真跑（跳板机，Nova 真子进程）：`@timeout:20` 的 scope 在第二步中途超时 → job 判 error、归因 timeout、消息「job 超时（预算 20s，已中止）」，总墙钟 27 秒（停止后排空没有拖到上界）；对执行中的 worker `kill -9` → job 判 error、归因 engine_error、消息带「exit -9」（负退出码不再按干净退出处理）。待双轨复核。与下方底稿的出入：① 退出信息不新建类型，终结函数直接收 `exited` / `exit_code` / `exit_reason` 三个参数；② 「是否设备目标」在 Job 带目标之前按 `is_device_job` 恒 False 实现，设备计量两键在「有会话记录或设备 job」时赋值（桌面 job 保持 None、省键）；③ `_job_status` 保留为终结函数的薄委托（既有测试与 ADR 指针不动）；④ fail-fast 的中止标志在 worker 线程里判定一出就置（不等主线程），排队中的下一个 job 才能稳定地在起 worker 前看到它、记 SKIPPED；⑤ 心跳包装在无 deadline 时也起（排空上界与 fail-fast 的检查都靠它醒来）；⑥ 没见过 `session_opened` 的 `session_closed` 按 created 登记（worker 违约时不丢会话事实）；⑦ 合成 skipped 的旁注在 render 与报告页各一份字面量、由 test_render 跨包锁定（同短路旁注的做法）。 双轨复核第一轮（我这边七路窄核对加三方对抗驳回：41 条原始发现、28 条成立、13 条核验未出结果由我逐条自判；Codex 第二十四轮同时在跑）确认并处置（code 与文档各一笔）：① fail-fast 标志此前在判定一出就置、再判可重试——开 fail_fast 时可重试的瞬时网络故障被直接变成整批中止，改为不再重试时才置；主线程的 `_stop_all` 以「标志未置」为条件而标志已由 worker 线程先置、从未执行——改为只做一次、不看标志；② 排空上界在 `stop()` 阻塞返回后才读时钟（上界可达两倍宽限加余量）——改从停止请求时刻起算；③ 内容完整（干净退出且有 scope_done）后 deadline 到点算不算超时此前没有定义：同步路径取决于 deadline 后、EOF 前有没有恰好来一次心跳——**设计决定（owner 于 2026-10-27 确认）**：内容完整后不再仲裁，判定按内容给出、推进器只催停并设排空上界、fail-fast 不打断其释放，无状态路径的 timed_out 遇 scope_done 加退出码 0 同样不改判，终结函数的前两行加「且内容不完整」条件（已写进 0034 机制二）；④ U 非空时置 None 丢掉原始失败原因（exit -9、worker 报的 session_lost 消息）——只改归因、消息保留；scope 级 error 后非零退出的消息此前说「事件流里没有失败原因」——保留 worker 报的那句；⑤ 退出码 80 的消息在同步路径重复一遍（异常文本被当平台归因）——WorkerExitError 不再传异常文本；255 的措辞对本机 worker 真以 255 退出也成立；⑥ 配对键一侧带 sessionId 一侧缺省时配不上（多登记一条、误判 release_failed）——先按 ARN 再按名、缺省侧事后带上的 ARN 补进记录；scope_done 之后再到的 scenario_done 曾追加第二条记录——取代合成记录；⑦ wire 对 scope_done 的 errorType 为 null 放行、observedS 非数值放行——协议层拒收；三字段同进同出的 ADR 原文与 code 一致，0051 决策 5 的序列写法是缩写、不改；⑧ explain 对带 error_type 的 error / aborted 只在零记录时打判定行——按 0042 决策四总打，全是合成记录的设备 job 由此看得到原因；⑨ 测试缺口：首次仲裁测试从未真置位 abort_flag、排空上界的 break 分支从未执行、对拍矩阵缺 ADR 列的五行、「scope 级 error 后超时」一行名不副实、各出口的 abort 对拍、explain 契约只核桌面 job、设备 job 不重试的门槛、project() 带 baseline 的 session_id、run 级计量、三字段的两种二元组合——全部补上；⑩ 文档：verdict-model 的三态边界 / skipped·aborted 赋值方 / error_type 表缺五项 / 分叉判据写成 abort_flag / 延伸阅读；artifacts-and-evidence 的判定行规则；CHANGELOG 漏 submit 路径归因变化、把中止说成超时文案、「真值表」内部词；ADR 0034 的 `_reduce_scope` 归因指针；注释里的 WorkerExitError 分类、负码、有界消费出处、「收停」缩写、format_event 新字段、reduce_event 的「零行为变化」（scope_done 不再覆盖 scope_started 的 session_id 是桌面可见变化，补进 CHANGELOG）。未处置并记下：workflow 核验阶段有 13 条没返回结果（流水线丢项），已逐条人判、不影响结论；复核处置这一轮没有再上跳板机真跑——改动都在调度逻辑且由真实线程的 FakeEngine 测试覆盖，进程级行为（SIGTERM 退出码、负码）未动。 Codex 第二十四轮（核的是处置前的两笔提交）与 workflow 高度重合，另指出并已处置（第二轮，code 与文档各一笔）：⑪ 事件流中的普通异常后不再停 worker（解析失败或 sink 抛错会留下活着的 worker）——恢复停止请求；⑫ 起 worker 失败自己写判定、绕过首次仲裁——改为以退出码未知进终结函数，消息保留「起 worker 失败」；⑬ 底稿补认领的两项设备呈现此前没做：会话记录带 session_opened.device、scope 表头显示代表会话的设备描述与 Device Farm 控制台链接（run 文本、explain 文本、报告页三处，core 与 cli 共用新模块 `device_session`），explain 渲染设备 evidence 的加键（step_kind、url 与 url_missing、controls 按预算与 controls_missing、page_source 与截断标记），设备上 failed / error 的 step 缺证据指针按抽取失败提示；契约页 sessions[] 补 device；⑭ 零事件判据对四种单事件在途、多 job 的 run 级计量补护栏。未处置并记下：控制台链接的路径形态（项目与会话两段）没有真实会话可核，首次拿到真实会话时须实际打开一次（已在第 8 批真跑清单）；底稿里「cloud tick 对无踪 task 直写 timed_out」与「接力者直接落 timed_out」在终结函数的输入上相同（退出码 None 加 timed_out），对拍矩阵只以后者一行覆盖。 Codex 第二十五轮又指出并已处置（第三轮，code 与文档各一笔）：⑮ `_stop_all` 边落定边停——真 stop() 阻塞到宽限到点，前一个 worker 消耗的宽限把后一个的仲裁推到 deadline 之后、ABORTED 记成 timeout；改为先对全部 worker 落定、再各起线程并行发停止请求；⑯ 普通异常分支先停再仲裁，停止期间越过的 deadline 把已成立的 abort 改成 timeout——改为先仲裁再停；⑰ 排空上界到点后才记未知退出，催停后卡死的 worker 判 engine_error、与无状态路径的 timed_out 不一致——先记再回落内容完整标志并仲裁；⑱ 网络重试退避期间被 fail-fast 中止的 job 被记成「未启动」的 SKIPPED——保留上次的 network_error 判定并注明未再重试；⑲ 按名命中只补 device 不补 ARN，discovered 无 ARN 之后到达的两个真实会话被并成一条——补 ARN；非零退出的 80 / 255 / 未知三个分支丢 worker 先报的 scope 级 error 原句——都保留；⑳ 表头借别的会话的 device 配代表会话的链接——只取代表会话自己的；explain 的设备表头与会话摘要用了中文字段名、controls 的截断只写「已截断」——改为 JSON 字段名（device / console_url / device_observed_s / device_observed_missing / sessions 逐项 origin、release、observed_s；controls 行 items / total / truncated），explain --json 的 scopes[] 加 `console_url`；㉑ 护栏：FakeEngine 事件发完后崩溃（对拍矩阵「接力者直接落 timed_out」同步侧此前实际输入退出码 0）、排空上界对「stop 返回后起算」的变异敏感、无 deadline 的 fail-fast 排空、内容完整后 SIGKILL / 80 / 普通异常与 deadline / abort 六种交叉、合成明细在 timeout / abort 下保留、「scope 级 error 后非零退出且超时」一行；㉒ 图：job 收场态图的「worker 能启动？」改为「起 worker」一步（起不来按退出码未知进后面的判据）、删直连 engine_error 的出口；project 两处注释、CHANGELOG 的「最终正常退出」限定。 第三轮后真跑（跳板机，Nova 真子进程，2026-10-26）：① fail-fast 两 job（一个 scope 只有「Then 后只跟地址」的 step、几秒内 error；另一个跑维基 AI 用例）——快速出错的 scope 发完 scope_done 后 victim 在 act 边界收 SIGTERM 协作退出（worker 日志「signal 15 received, cooperative stop — session shutdown complete」）、判 ABORTED、消息「fail-fast：其他 job 失败，本 job 被中止」、停止后到达的 step_done 仍被读到，run 全程 27.8 秒，结束后无残留 worker 进程；② `@timeout:20` 的 scope 判 error / timeout /「job 超时（预算 20s，已中止）」，全程 26.8 秒（排空上界改从停止请求时刻起算后与此前 27 秒持平：真 worker 在宽限内协作退出，上界没有被触及），无残留进程。两次真跑都没有制造「scope_done 之后收尾拖过 deadline」的情形（真 worker 不易稳定复现），该条设计的真实退出码行为仍待日后观察。 Codex 第二十六轮又指出并已处置（第四轮，code 一笔）：㉓ 退避之后到再次起 worker 之前仍有窗口，fail-fast 恰在窗口里置位时已运行过一次的 job 仍被记成 SKIPPED——判断收进 `_run_once` 的起 worker 前检查（`previous` 参数），退避后的那次检查删去；㉔ 两条护栏只是看起来覆盖：对拍矩阵「接力者直接落 timed_out」一行没锁住同步侧的退出码输入——加去掉超时处置的同侧对照（判 release_failed 且消息含「worker 异常：」）；合成明细在 ABORTED 下保留只核了独立的 result——改为经 `schedule()` 的用例（scope_done 之后非零退出，deadline 与 abort 两种触发）；㉕ 真实进程空白改用真子进程补（`echo_worker.py` 新增 done_then_deaf / done_then_slow / bad_line 三种形态与按 scope.name 选形态，经 SubprocessEngine 真 spawn、真信号、真管道，在 test_subprocess_engine）：fail-fast 下两个仍在运行的 victim 并行停、都判 ABORTED、总耗时远小于逐个等宽限；内容完整后 worker 无视 SIGTERM 挂死——deadline 到点催停、宽限耗尽 SIGKILL、负退出码回判 timeout、已完整的明细保留；内容完整后协作慢退判 PASSED 不记超时；事件行解析失败后仍活着的 worker 被停掉并回收（pid 核对）。「scope_done 之后收尾拖过 deadline」由此在真子进程上有了两条路（挂死记 timeout、协作退出保留判定），真 Nova / Midscene worker 收 SIGTERM 后的退出码按各自的终止契约（0024 / 0051 决策 5）。 Codex 第二十七轮又指出并已处置（第五轮，code 一笔）：㉖ 起 worker 前的检查到 spawn 之间仍有无法原子化的窗口——spawn 之后再查一次标志，置位即落定 abort 并停它（在起 reader 线程之前），判 ABORTED、不记 SKIPPED 也不保留上次判定，用「第二次解析引擎时置位」的用例钉住（run_count 为 2、判 ABORTED）；㉗ 三条真子进程护栏只是看起来覆盖：多 victim 并行停改用无视 SIGTERM 的 victim（各自要等满宽限才被强杀），总耗时上界「一份宽限」把并行钉死；内容完整后挂死的用例补进程回收核对与耗时上界（SIGKILL 后管道 EOF 的路远快于排空上界兜底）；㉘ 补两条真实进程组合：同一 handle 的两次 stop 并发（都返回、进程被回收）、强杀后孙进程仍持有事件管道写端（管道不 EOF，schedule 在宽限加余量到点结束消费、判 timeout，夹具自己回收孙进程）；对拍 docstring 的归因措辞。未处置并记下：「已有 abort、再遇解析或 sink 异常、停止等待跨过 deadline、最终保留 ABORTED」这一组合没有补真子进程用例——它在真子进程上**可以**稳定复现（在首事件的 sink 里依次置 abort_flag、再抛异常即可控制两个失败源的先后；Codex 第二十八轮自己的探针三次都保持 ABORTED），FakeEngine 的先仲裁再停用例已钉住同一顺序，故不再加一份真进程版本。另记一项过程纠偏：此前几笔提交信息里的 pytest 总数是估算、不是看到的汇总行——整仓真实数字以第五轮全量运行为准（见提交信息），此后只写看到的数字。 Codex 第二十八轮又指出并已处置（第六轮，code 一笔）：㉙ spawn 之后再查标志那一步的两个问题——重试解析期间 `_stop_all` 对着上一 attempt 已退出的旧 handle 落定、新 handle 起来后因「非首次仲裁」无人停它（`_run_once` 起始清掉旧 handle 与请求时刻，spawn 后对「标志已置或原因已落定」都向新 handle 发停止请求）；停止请求在 reader 线程起之前同步阻塞，worker 收尾写事件管道无人读、写满即卡死到强杀（停止请求改为另起线程发，reader 照常起）；「不执行任何 step」的承诺改为「尽早停，收到信号前已执行的部分照常归约」；㉚ 真子进程护栏再加固：多 victim 并行停关掉心跳（victim 的线程阻塞在管道读上、只有 `_stop_all` 能停它们）并让 crash job 等两个 victim 都装好 SIG_IGN 发出 scope_started 后再崩（文件信号），耗时从放行时刻起算；两次 stop 用栅栏同时发起并断言时间段重叠；fdholder 形态先装 SIG_IGN 再起孙进程（否则孙进程已起、pid 未记时一个 SIGTERM 就留下孤儿）；`_read_events` docstring 的「returncode>0」改为非零含负码。 Codex 第二十九轮又指出并已处置（第七轮，只动测试与夹具）：㉛ 重试窗口用例的第二次 attempt 可能自己执行完而误红——改为不发事件、等停止请求（假 worker 至多等 5 秒，之后自然 EOF）才结束的假 worker，并核实新 handle 确被停；㉜ 多 victim 并行停的放行只等两个 victim、没等 crash job 自己就绪，crash job 启动慢时正确实现也会被耗时上界误红——放行再等 crash job 的 scope_started；㉝ fdholder 的 SIG_IGN 封不住 SIGKILL，强杀恰落在孙进程起后、pid 登记前仍留孤儿——改为孙进程自己把 pid 追加进文件；并校正一处把 crash job 说成「ScopeDone 后退出」的注释（它在 scenario_started 之后退出、从不发 scope_done）。 Codex 第三十轮又指出并已处置（第八轮，只动测试）：㉞ 重试窗口用例只靠最终的 stopped 断言守不住 spawn 后的停止请求（假 worker 等满 5 秒自然 EOF 后收尾的幂等停也会置位）——加耗时上界 3 秒；㉟ 多 victim 并行停的上界没容下 crash job 退出时日志线程的收尾等待（两条线程各至多 2 秒）——先把宽限加大到 3 秒；㊱ fdholder 断言前没等孙进程登记、回收前只读一次——改为轮询等 pid 文件出现两行再断言、再回收。 Codex 第三十一轮指出加大宽限仍容不下两条日志线程累计 4 秒的等待（第九轮，只动测试）：㊲ 耗时改从 crash job 的判定回调（`on_job_complete`，紧接着就是主线程的 `_stop_all`）起算，日志收尾等待发生在它之前、不再混进上界，上下界 `[grace, 2*grace-0.2)` 只量「两个 victim 同时等满宽限被强杀」这一段。 Codex 第三十三轮指出终点取 `schedule()` 返回仍含 victim 自己的日志收尾与线程池收尾（第十轮，只动测试与夹具）：㊳ 改为由测试线程按 pid 轮询两个 victim 进程的死亡时刻（echo_worker 加 WORKER_PID_DIR，按 scope 各写一个 pid 文件），只量「停止阶段开始到进程被强杀」这一段。Codex 第三十四轮指出按 pid 轮询量的仍是回收时刻（强杀后到父进程回收之前进程是僵尸、kill(pid, 0) 仍成功，而回收发生在 reader 读到 EOF 与日志线程收尾之后），且 pid 文件建好未写完时有空读竞态（第十一轮，只动测试与夹具）：㊴ 改为 victim 启动时在 <scope>.lock 上持有 flock（先在临时名上加锁再改名，文件一出现即已上锁），测试线程轮询非阻塞加锁、加到即死亡时刻——内核在进程退出那一刻释放锁，与回收、EOF、日志线程全无关；WORKER_PID_DIR 随之去掉。实测两个 victim 的死亡时刻都在停止阶段开始后约 3.02 秒（宽限 3 秒），把 _stop_all 改成同步逐个停止则为 3.03 与 6.03 秒、用例红。Codex 第三十六轮总判定设计已落到位，本批闭合。


**依赖**

- B2-core-target-job：需要 Job 上的测试目标字段（cli-json-contract 里 run_meta.jobs[].target.device ∈ desktop/android/ios），并有一个「是否设备目标」的判据。用在三处：sessions[] 与设备计量键是否出现、网络重试门槛「job 目标不是设备」、设备 scope 总有 Job.timeout_s（排空期间心跳与上界检查依赖 deadline 存在）
- B1-capabilities（弱依赖）：同步路径排空上界取 grace_period_s 加余量，设备 Midscene worker 的 min_grace_s（约 64 秒）来自能力自述，由组合根注入 ScheduleOpts；B5 只消费 ScheduleOpts 里的 grace，不读能力自述

**改动面**

- `core/gherkai_core/model.py` · ScopeDone：加三个可选字段 status: Status | None（只取 ERROR）、error_type: str | None、message: str | None，缺省都为 None，正常路径的形态不变；docstring 写明三者同时出现或同时缺省（0051 决策 4；0024「scope_done 的可选 status / errorType / message」；0031 决定四）
- `core/gherkai_core/model.py` · 新增 SessionOpened / SessionClosed 事件类与 Event union：SessionOpened(scope_id, name, origin: Literal['created','discovered','attempted'], session_id: str | None, device: dict | None)；SessionClosed(scope_id, name, release: Literal['confirmed','unconfirmed'], session_id: str | None, observed_s: float | None, provider_minutes: dict | None)。两类都加进 Event union。device 与 provider_minutes 对 core 不透明，原样搬运（0051 决策 4、7；0024 会话事件段）
- `core/gherkai_core/model.py` · 新增 SessionRecord；JobResult / RunResult 加字段：SessionRecord(session_id, name, origin, release: str | None（没收到 session_closed 时为 None）, observed_s, provider_minutes)。JobResult 加 sessions: list[SessionRecord]、device_observed_s: float | None、device_observed_missing: int | None；RunResult 加 device_observed_s / device_observed_missing。None 表示非设备 job（序列化时省键）（0051 决策 7；0024 成本信封「设备会话的原生量」）
- `core/gherkai_core/model.py` · ErrorType Literal：加 precheck_failed / acquire_timeout / session_lost / capability_unavailable / release_failed 五项，各带注释写明适用层级（capability_unavailable 是 step 级；release_failed 由 core 推出，worker 不报）（0051 决策 4 类别表；0024 errorType 条）
- `core/gherkai_core/errors.py + wire.py` · raise_for_worker_exit 与退出码异常：新增 WorkerExitError(RuntimeError)，带 exit_code 属性；WorkerNetworkError 改为它的子类（exit_code=80）。raise_for_worker_exit 对正的非零退出码抛 WorkerExitError(rc)；负码（SIGKILL）也抛并带原码，不再按干净退出处理（见 open_questions）。schedule 由此拿到「非零退出码 / 80 / 未知」三种退出信息，不再从消息文本里解析（0034 机制二「终结函数与真值表」输入「退出信息」；0024「常量与退出码到异常的翻译归协议层 wire.py」）
- `core/gherkai_core/wire.py` · event_from_json：新增 session_opened / session_closed 分支：按 camelCase 解析 sessionId?、name、origin、device?{platform, model, osVersion, unit}、release、observedS?、providerMinutes?。origin 与 release 不在枚举内时抛 ValueError（core 会按它们分支）；sessionId 为 null 时 name 必须有值；observedS 为 null 时保持 None，不改成 0（0051 决策 4、7；0024「新事件类型对旧读端的影响」）
- `core/gherkai_core/wire.py` · event_from_json：scope_done 分支：读 status / errorType / message。status 出现且不等于 "error" 时抛 ValueError；三个字段同时出现或同时缺省（违约时的处置见 open_questions）。message 套 redact_url_userinfo，和 step_done 同样处理（隧道预热失败的消息可能带地址）（0051 决策 4、13；0035 决策 5 脱敏）
- `core/gherkai_core/project.py` · reduce_event：会话事件归约与代表会话：SessionOpened 按配对键（有 sessionId 用它，否则用 name）在 result.sessions 里登记一项；SessionClosed 按同一配对键回填 release / observed_s / provider_minutes。代表会话的取值规则：scope_started 一旦取到 session_id 就锁定（在 Timing 里加 session_locked 标志）；锁定前取最近一条 origin 不是 attempted 的 session_opened；attempted 永不写入；ScopeDone 只在 result.session_id 为 None 时才填。现在 ScopeDone 分支只要带值就覆盖，这一处要改（0051 决策 4 session_id 规则；0024 sessionId 取值优先级）
- `core/gherkai_core/project.py` · reduce_event：ScopeDone 的 scope 级 error 与合成 SKIPPED：ScopeDone.status == ERROR 时，取 result.job.scenarios 中零事件的 scenario（没有 scenario_started / scenario_done / 任何 step 事件；Timing 要能查到「见过事件的 scenario_id」集合），按 definition 顺序追加 ScenarioResult(status=SKIPPED)，其全部 step 为 StepResult(status=SKIPPED, shortcircuited=False, duration_ms=None)。在途 scenario 及其未开始的 step 都不合成；不写 scenario_status。合成放在共用的 reduce_event 里，让两条路径的明细出自同一份代码（0031 决定一、三、六的加法；0042 决策四；0034「明细补全与判定分开」）
- `core/gherkai_core/project.py` · 新增纯函数：终结函数（例如 finalize_job）：输入：stop_reason ∈ {none, timeout, abort}；退出信息（0 / 非零退出码 / 未知）；是否见到 scope_done 及其 status / errorType / message；scenario 判定集；未确认集 U（由 result.sessions 算出：release 不是 confirmed 的项，attempted 天然在内）。按 0034 真值表逐行取第一个命中的行，输出 (status, error_type, message)。U 非空时不论判定为何，message 都追加产品语言提示并列出会话名，attempted 的项另列为「结果未知的创建尝试」。超时与平台哨兵的消息文案也收进这里，同步路径与投影路径共用一份，不再各写一份（0034 机制二「终结函数与真值表」；0051 决策 4、5）
- `core/gherkai_core/project.py` · _job_status / _reduce_scope：_job_status 并入（或改为委托）终结函数：加 scope_done.status=error 一行；加零 scenario 的 scope_done 判 ERROR 一行（现在 _aggregate([]) 会给出 PASSED）；加 U 非空改判 release_failed；未退出时见过 session_opened 或 scope_started 都算 RUNNING。_reduce_scope 记录 saw_session_opened 与 scope_done 事实，job 级归因只由终结函数写（timed_out 的退出记录即 stop_reason=timeout）（0034 机制二真值表各行；0051 决策 4）
- `core/gherkai_core/project.py` · project / project_full：设备计量合计：job 级：device_observed_s 为 origin 是 created / discovered 且 observed_s 不为 None 的各项之和；device_observed_missing 为 origin 是 created / discovered 且 observed_s 为 None 的项数（包括没收到 session_closed 的会话）；attempted 的项两键都不计。只有设备 job 才赋值（判据取 B2 的 Job.target）。project_full 在现有 tok / tw 合计旁边加 run 级两键合计。project() 的 JobState.session_id 保留现有的「新值为空时退回 prior」合并逻辑（0051 决策 7；0024 成本信封）
- `core/gherkai_core/schedule.py` · _Worker：stop_reason 首次仲裁：每个 _Worker 持有 stop_reason（初值 none），用一把锁做比较后设置：第一次作出停止决定时落定；那一刻 deadline 已过就取 timeout（即使 abort_flag 也已置位），否则取 abort。事件循环、WorkerNetworkError 分支、EOF 分支都只读这个落定值，不再各自判断（现在异常分支与 EOF 分支先判 abort，和事件分支顺序相反）。schedule._stop_all 对每个仍在运行的 worker 当场按同一规则落定，已经返回的 worker 不改（0034「终结函数与真值表」stop_reason 首次仲裁规则）
- `core/gherkai_core/schedule.py` · _Worker._run_once：停止后继续有界消费：作出停止决定后不再立即 return：先把触发决定的那条事件照常 emit、on_event、reduce，然后继续迭代，直到 EOF、退出异常，或者到达排空上界（决定时刻加 grace_period_s 再加余量）。排空期间保留心跳唤醒，用来执行上界检查（deadline 为 None 时也要能唤醒）。最后统一调用终结函数，传入 stop_reason、退出信息（EOF 为 0；WorkerExitError 取其码；其它异常和起 worker 失败为未知）、scope_done 事实与 U（0034「停止后继续有界消费完整事件流」；0051 决策 5）
- `core/gherkai_core/schedule.py` · _Worker.run：网络重试门槛；run 级合计：重试条件加上「job 目标不是设备」（判据取 B2 的 Job.target）；schedule() 的 run 级合计加上 device_observed_s / device_observed_missing，与 project_full 写法一致（0051 决策 2（0028 core 层重试门槛）；0051 决策 7）
- `core/gherkai_core/persist.py` · RunPersistence.on_event：收到 SessionOpened（origin 不是 attempted）就把 job 刷成 RUNNING 并带上它的 session_id；收到 ScopeStarted 时改写为执行会话的 id 并锁定；attempted 不写 session_id。本服务在内存里按 scope 记代表会话与锁定状态（放在已有的 _lock 下）。因为 update_job_state 在本机与 DDB 两个 adapter 上都整项覆盖 JobState，任何写入都不能用 None 覆盖已有的 session_id。可以与 reduce_event 共用一个纯函数来计算代表会话（0051 决策 4「同步路径的 persist.on_event」条）
- `core/gherkai_core/serialize.py` · job_result_to_dict / job_result_from_dict / to_dict / from_dict：仅设备 job：加 sessions[]（键为 session_id、name、origin、release、observed_s、provider_minutes）与 device_observed_s / device_observed_missing；非设备 job 省略这些键。run 级同样处理。读端用 .get 兼容旧落盘，保证往返一致。release 为 None（没收到 session_closed）时的落盘形态要定下来；契约只列了 confirmed / unconfirmed，建议写端把它归为 unconfirmed（0051 决策 7；cli-json-contract run --json 的 jobs[] 段）
- `cli/gherkai_cli/render.py` · run_tree / explain_to_dict / _add_step / explain_tree / format_event：run_tree：设备 job 显示设备占用时长与缺计量会话数；U 非空时列出未确认停止的会话名，attempted 单独标「结果未知的创建尝试」。合成的 skipped（status=skipped 且 shortcircuited=False）打「未执行（scope 级错误，原因见 job 判定）」。explain_to_dict 的 scopes[] 加 sessions[] 与设备计量键。_add_step 对合成的 skipped 不打「无 AI 证据」。has_step_records 与判定块怎么处理见 open_questions。format_event 给会话事件补 origin / release 的显示（不显示 ARN 以外的端点信息）（0042 决策四；0051 决策 7；cli-json-contract explain 段）
- `core/gherkai_core/adapters/report_store/local.py` · index.html 的 step 旁注（约第 297 行，与 render._SHORTCIRCUIT_NOTE 措辞同源）：给合成的 skipped 加同一句「未执行（scope 级错误…）」旁注；有设备会话时显示会话摘要。措辞与 render.py 保持一致（0042 决策四；0031 决定六）
- `core/tests/fake_engine.py` · FakeEngine：加两个测试能力：①停止后仍吐指定的「收尾事件」（模拟 worker 在 SIGTERM 后发 session_closed），现在只要 handle.stopped 就直接 return；②事件流结束后抛 WorkerExitError(rc) 模拟非零退出码（0034 双路径对拍）

**先写的护栏测试**

- `core/tests/test_wire.py`：协议字段红线：session_opened、session_closed、scope_done 带 status 的 JSON 行，按 0024 的示例形状（camelCase）解析成对应 dataclass。sessionId 为 null 时只带 name；observedS 为 null 时得 None，为 0.0 时得 0.0；providerMinutes 原样搬运。origin 或 release 不在枚举内、或 scope_done.status 不是 "error" 时抛 ValueError。正常 scope_done 的 status / error_type / message 全为 None。scope_done.message 里带凭据的地址被脱敏。raise_for_worker_exit(1) 抛 WorkerExitError 且 exit_code==1；80 抛 WorkerNetworkError，它同时是 WorkerExitError；负码也抛，并带原码（0051 决策 4、7；0024 会话事件与 scope_done 可选字段）
- `core/tests/test_wire.py（或 test_model）`：差集护栏：ErrorType 的 get_args 包含 0024 类别集的全部 11 项（6 项原有加 5 项新增），用显式集合做相等断言，不只是检查包含（0024 errorType 条；0051 决策 4 类别表）
- `core/tests/test_project.py（新建 test_terminal.py 亦可）`：终结函数真值表按行参数化，每一行一个用例，并验证按行序取第一个命中的行：timeout 优先于 U 和非零退出；abort 判 ABORTED 且归因为空；非零或未知退出时，U 非空为 release_failed，否则 80 为 network_error、其余为 engine_error；退出码 0 且无 scope_done 为 engine_error；scope_done.status=error 时，U 非空为 release_failed，否则取 errorType 与 message；零 scenario 为 ERROR 且消息为「worker 未报告任何 scenario 判定」（这条现在会判 PASSED，测试应先红）；判定集非空且 U 非空改判 release_failed；未退出时，只见过 session_opened 也算 RUNNING。U 非空时 message 列出会话名，attempted 单独列出（0034 机制二「终结函数与真值表」）
- `core/tests/test_project.py`：代表会话规则：①opened(A, created) → opened(B, created，换台) → scope_started(B) → scope_done(sessionId=C)，得到 B；②只有 opened(A) 后接 opened(attempted)，得到 A；③只有 attempted 时为 None；④锁定以后，后到的 session_opened 不改写。同一序列经 project() 带 baseline 合并后，JobState.session_id 不会被 None 覆盖（0051 决策 4；0024 sessionId 取值优先级）
- `core/tests/test_persist.py（无此文件就新建）`：用一个记录型的假 RunStore，按顺序断言 update_job_state 的每次写入：session_opened(created) 写成 RUNNING 带 A；attempted 不产生 session_id 为 None 的写入，或写入时仍带 A；scope_started(B) 写成 B；之后任何写入都不带 None 的 session_id（0051 决策 4「同步路径的 persist.on_event」）
- `core/tests/test_lifecycle_states.py`：合成 SKIPPED：definition 有三条 scenario，s1 已完成，s2 在途（有 scenario_started 与 step_started），s3 没有事件；收到 scope_done(error) 后，只有 s3 合成 SKIPPED，其全部 step 为 SKIPPED、shortcircuited=False、duration_ms=None。s2 不出现在 JobResult.scenarios 里。scenario_status 不含 s3。没有 scope_done、或 scope_done 不带 status 时都不合成。之后到达的超时、abort 或非零退出只改变判定，不撤销已合成的明细。序列化往返保留 shortcircuited=False（0031 决定一、三、六；0042 决策四）
- `core/tests/test_project.py`：计量合计：created 的会话 observedS=10、discovered 的 observedS 为 null、created 的会话没收到 session_closed、外加一项 attempted，得到 device_observed_s=10、device_observed_missing=2，attempted 不计入两键；observedS=0.0 的会话计入合计、不计入缺失数（null 不等于 0）；run 级是各 job 之和；桌面 job 两键都是 None 且序列化时省键（0051 决策 7）
- `core/tests/test_termination_parity.py（新建）`：双路径对拍：0034 列出的事件矩阵同时输入 schedule（FakeEngine 支持停止后的收尾事件与 WorkerExitError；用 fake clock 触发 timeout）与 project_full（EventRecord 加 TaskExited，timed_out 对应 timeout），逐项比较 status、error_type、message、scenarios / steps 明细、sessions[]、session_id 与两个计量键。矩阵：前置 scope 级 error 加退出 0；scope 级 error 后超时；停止后到达的 session_opened；未确认的 session_closed；零 scenario 的 scope_done；接力者直接落 timed_out；cloud tick 直写 timed_out；没有 ARN 的未知 Create 加取消；已记真实 ARN 后到达的 attempted。含 abort 的两行只跑同步路径：timeout 与 abort 同时成立时判 timeout；先判 abort、收尾期间 deadline 才到，仍为 abort（0034「双路径对拍是实施护栏」）
- `core/tests/test_schedule.py`：停止后继续消费：在第 k 条事件上判定超时后，停止后才到达的 session_closed(confirmed) 照样被归约，U 为空、message 里没有释放失败提示；停止后再无事件、worker 也不结束时，消费在 grace 加余量处终止（fake clock 驱动，不挂死）。首次仲裁：在事件循环、WorkerNetworkError、EOF 三个分支上，deadline 已过且 abort_flag 已置位时都判 timeout（0034「停止后继续有界消费」与 stop_reason 首次仲裁）
- `core/tests/test_schedule.py`：设备 job 在零 step_done 的情况下以 network_error 失败，也不做 job 级重试（run_count==1）；同样条件的桌面 job 仍按原规则重试（0051 决策 2（0028 门槛加「job 目标不是设备」））
- `core/tests/test_serialize.py（现有 round-trip 测试文件）`：带 sessions[] 与设备计量键的 JobResult / RunResult 往返一致；读没有这些键的旧落盘不报错，读出的值为 None 或空列表；桌面 job 的输出里没有这些键（0051 决策 7；cli-json-contract jobs[] 段）
- `cli/tests/test_cli_json_contract.py`：_sample_run_result 加一个设备 job（sessions 每种 origin 至少一项，并含两个计量键），scenario 里放一条合成的 skipped step。另加一条正向断言：生成的 doc 里确实有 sessions、device_observed_s、device_observed_missing 这几个键。_mk 会悄悄丢掉 model 里还没有的字段，没有这条断言，护栏会在空集上直接变绿。provider_minutes 按 open_questions 的决定，或进 opaque，或在文档里逐键加反引号。explain 样例同样覆盖 sessions[]（0041 决策五 / CLAUDE.md 差集护栏；0051 决策 7）
- `cli/tests/test_render.py（现有渲染测试）`：run_tree 对 U 非空的 job 列出会话名，attempted 标为「结果未知的创建尝试」；合成的 skipped step 打「未执行（scope 级错误，原因见 job 判定）」，不打「无 AI 证据」，也不打短路旁注；新增的用户可见字符串由 test_user_facing_messages 扫描，不含 ADR 编号与内部机制名（0042 决策四；0051 决策 4 用户可见消息；0039）

**完整性审查补认领**

- 次序校正：B5 排在 B2 之前，先让 core 认 scope_done 的 status 字段与合成 SKIPPED，B2 的 worker 自检才有出口。凡依赖「是否设备目标」判据的部分（sessions[] 与计量键的出现条件等）先按缺省桌面实现，B2 落地 target 时补上。
- 本批对桌面是修复、不是零变化：负退出码（SIGKILL）不再按干净退出处理；零 scenario 的 scope_done 由 PASSED 改判 ERROR；超时与 fail-fast 同时成立时统一按首次仲裁取 timeout（现状两条分支顺序相反）。三处写进 CHANGELOG。
- 红线测试补：scope_done 的 status / errorType / message 部分出现即拒绝；桌面完整成功、scope_done 之后 SIGKILL、异常、退出码 80、EOF 各出口上 abort 与 deadline 的对拍。
- 双路径对拍护栏：同一组事件矩阵分别输入同步 schedule 与无状态 project，判定、归因与明细逐项相等；含 abort 的行只输入同步路径。0034 机制二。
- explain 渲染设备 evidence 的新字段（step_kind、url / url_missing、controls / controls_missing、page_source / page_source_truncated），设备上 failed / error 的确定性或导航 step 缺 ref 算抽取失败。0042 决策一、四。
- explain 与 run 的 scope 表头从 session_opened.device 与 scope_started.sessionId 派生；device_session 只渲染成链接；按会话 ARN 给出 Device Farm 控制台链接。0051 决策 8。
- 带 error_type 的 error / aborted 总打判定行，has_step_records 计入合成记录（本轮补进 0042 决策四）。

**真跑或对抗核查才算数的结论**

- 同步路径停止后排空（SubprocessEngine）：真实设备 Midscene worker 在 SIGTERM 后走终结四阶段，发出的 session_closed 要在 grace 内经 fd3 被 schedule 读到并归约，U 才算对。要用 tools/e2e_harness.py 加真实 Device Farm 会话去验证：超时处置后 jobs/*.json 里 sessions[].release 为 confirmed，并且没有 release_failed 提示。FakeEngine 证明不了 stop() 阻塞在 proc.wait(grace) 期间、心跳读线程与管道缓冲的真实交互
- 同步路径停止后排空（FargateEngine）：StopTask 之后迭代器继续拉 events 直到 STOPPED，_final_drain 的强一致读要能取到停止后写入的 session_closed，退出码要能读到（未确认时为 1）。要真部署、真 ECS 验证；moto 与假 DDB 证明不了最终一致读和 STOPPED 事件的时序
- 无状态路径的退出码通道：设备 worker 在 U 非空时以 1 退出，退出观察者写下 task_exited(exit=1)，reconciler 判 release_failed 并列出会话名。要真 Fargate 加 EventBridge 走一遍，确认退出码 1 不被 stopTimeout 处的 SIGKILL（137）掩盖：两者归因相同，但需要确认 min_grace（约 64 秒）真的小于 stopTimeout 120 秒且来得及
- SIGKILL 和负退出码在真实子进程里的形态：OOM 或外部 kill 之后 raise_for_worker_exit 收到负码，同步路径应判非零。要真跑一次 kill -9，确认同步路径与本机 detached 路径（SubprocessLauncher 记 -9）的判定一致
- DDB RunStore 的整项覆盖：同步 cloud run 的 persist.on_event 在收到 attempted 之后，runs 表 STATE.jobs[scope].session_id 仍保留原值。moto 能覆盖表达式语义，但「显式 null 会擦掉已有值」这条风险最好在真表上看一次 status --json 的输出

**易错点**

这一批最容易做错的几件事：

(1) 把终结判定写成两份。现状下同步 schedule._run_once 有三个分支，各自判 timeout 和 abort，顺序还不一致：事件分支先判 timeout，网络异常与 EOF 分支先判 abort。project._job_status 另有一套。消息文案也不同，同步是「job 超时（>Xs）」，投影是「job 超时（预算 Xs，已中止）」。必须收成 project.py 里的一个纯终结函数，两条路径只负责准备输入，再用对拍测试锁住，否则真值表会马上漂移。另外，零 scenario 的 scope_done 现在两条路径都判 PASSED（_aggregate([]) 的结果），这是现有的潜在错误，对拍矩阵会先让它变红。

(2) 停止后继续有界消费，加上 stop_reason 首次仲裁。现在超时或 abort 后会立即 return 并放弃 generator，所以停止后到达的 session_closed 不会被归约，U 会算错。改成继续消费后，generator 会走到 proc.wait 和 raise_for_worker_exit，负码与异常分类的语义就会变化，见 open_questions 第一条。stop_reason 要在 _Worker 上用加锁的比较后设置，在第一次作出停止决定时落定。schedule._stop_all 只对仍在运行的 worker 当场落定；deadline 已过的取 timeout。不能沿用现在「在哪个分支看到 abort_flag 就判什么」的写法。

其次要注意的几处：
- 代表会话 session_id 规则。现在 reduce_event 的 ScopeDone 分支只要带值就会覆盖 scope_started 的值，这与 0024 已写明的规则冲突，要一起改。persist.on_event 面对的是两个整项覆盖 JobState 的 adapter，必须在内存里自己维护代表会话，任何写入都不能带 None。
- 合成 SKIPPED 必须放在共用的 reduce_event 里，判据是「零事件」（scenario_started、scenario_done、任何 step 事件都没有），不能只看有没有 scenario_done，否则在途 scenario 会被误写成未执行。
- 契约护栏的 _mk 会悄悄丢掉 model 里还没有的字段。先写的护栏测试必须加一条「样例里确实有 sessions 键」的正向断言，否则测试在空集上直接变绿。


## 3. B2-core-target-job：测试目标与 Job 形态（core 侧 tag 归约、target 两形态、按目标的 timeout、plan 标注与目标拒绝、两个 worker 建会话前自检）

规模 M。

**进度（2026-10-26）**：已落地（三笔 code：core 的目标模型与 plan / wire / serialize、CLI 与 compose、两个 worker 的自检与 TS 侧字段契约），pytest 全量 2235 绿、Midscene node 测试 213 绿。真跑核对：① 本机真子进程（不碰 AWS）——两个真实 worker 收到 android/web 的 job 都只发 scope_done{error, precheck_failed}、不发 scope_started、以 0 退出，core 判 ERROR / precheck_failed 并把两个 step 合成 skipped；② 跳板机桌面真跑两引擎（Nova 109 秒、Midscene 63 秒，都 passed）——job 行带 timeoutS=300 两个 worker 行为不变，落盘的 run_meta 只多 timeout_s、没有 target / device_request 键。待双轨复核。与下方底稿的出入：① 结构校验放新模块 `gherkai_core.target`，`job_from_dict` 带 `validate` 开关（缺省开；plan 形态与测试夹具关）；② `Target.as_text()` 给出 `desktop/web`、`android/app:shop` 的紧凑写法，plan 文本与 run 的 job 列表行都用它；③ 设备缺省与下限由 PlanConfig 自带缺省值（按内建取设备预算 600 推出 1500 / 780），CLI 显式传入同样的值、配置文件接上后改由 B3 算；④ 发给 worker 的 `target` 只在非桌面写，桌面 job 的键集合与 1.4 相同（`timeoutS` 在有预算时写，桌面缺省 300 也写——旧 worker 不读该键，两引擎真跑证实）；⑤ plan 的目标拒绝在自述取不到时只警告，WorkerSelfDescribeError 交给随后的派发标注查询报；⑥ 两个 worker 的自检消息里的目标名称（桌面网页 / Android 应用）各自维护一份，与 CLI 的 `render.target_label` 同口径、由各侧测试钉住。未做、留到后续批：plan 把「在该目标上没有实现的确定性 step」标注为走 AI（0048 决策 5 第三条，依赖 B4 的句柄声明）；用户指南与 skill 对 @device / @app 的说明（设备尚不可用，放到文档批）；Fargate 路径带新键的 job 行经 S3 读回的真跑（要等新镜像推送，B8）；版本错位的拦截（新 CLI 写的带目标 definition 被旧 Lambda 读）依赖 0037 决策 7 的版本一致性检查，在部署批真部署上核。
双轨复核第一轮（我这边七路窄核对加三方对抗驳回：48 条原始发现、31 条成立；Codex 第三十二轮）确认并处置（code 一笔、文档一笔）：① 写 definition 之前的那次结构校验此前没接——云端 submit 会把 plan 形态的设备 job（设备请求为空）写进 definition，每个读 definition 的地方都会在读时被拒、而提交已显示成功；现在 run / submit 的共享前置在写前对每个 job 调 `validate_job_definition`，设备 job 在这里以退出码 2 被拒（本机后端在它之前已由执行前预检按能力自述拒绝），注释里「两处各核一次」由此成立；② 结构校验把错类型当「未提供」（device_arn 给数字或列表配os_version 能过）、`device=[]` 抛 TypeError、超大整数抛 OverflowError——改为类型严格、数值校验吞掉溢出，一律 DefinitionContractError；③ 读时映射对缺键与错形态漏 KeyError / TypeError、对 billing_method / acquire_timeout_s / provider 缺键静默补缺省——改为留 None 交校验拒绝、形态不对归 DefinitionContractError；写端省 target 键只对 desktop/web 且无应用条目（非法的桌面应用目标不再经往返变合法）；④ scope 的四条消息：非正 @timeout 的改法对设备 scope 不成立、低于下限的消息来源写法与建议、@device 取值非法不再建议删 tag、`--default-job-timeout` 非有限数给改法；⑤ plan 的目标核对只问有非桌面 job 的引擎（纯桌面 plan 不再多一行警告），worker 自述非零退出不再静默而以退出码 2 结束，降级警告写清本机与云端各由谁拒绝；⑥ 两侧 worker 自检消息与 CLI 消息在中文与拉丁字母之间补空格（「在 Android 网页上」），Python 侧秒数写法与 TS 一致（整数值不带小数点），Midscene 的字段清单与接口用 `satisfies` 加反向类型断言双向绑定、run-scope 与 precheck 的 Job 类型从 job-source 派生；⑦ 术语按 CONTEXT：远程访问会话（不再写设备会话）、获取预算、执行前预检；契约页 target 行改为「object 或省略」；CHANGELOG 注明配置文件读取尚未接入；ADR 0025 两处「engine/timeout」补 target；两个 DEVELOPMENT 补漏列的 redact 模块与测试；⑧ 护栏：test_target 的取值域差集此前是恒真断言——改用解析后的类型注解；结构校验矩阵（应用条目五项各缺失 / 空值 / 错类型、设备请求各字段、当且仅当的反向分支、错类型的 device、读端缺键与错形态十一种）；@device 标在非首成员；`--default-job-timeout` 的 nan；PlanConfig 自带缺省与 CLI 组装的三态 / 设备缺省直接断言；run / submit 的非有限数；引擎支持 Android 时 plan 的目标行、远程访问会话数、--json 的 target 与设备缺省 1500；写前校验直接用例；两侧自检的主入口真子进程用例（唯一事件 scope_done、退出码 0）；Midscene 补「设备受支持但界面类型不受支持」。Codex 与 workflow 中被驳回或我判不处置的：目标拒绝消息不点名可用引擎（当前没有引擎支持设备，点名反而误导，待 B6 后再看）；golden 的键集合不覆盖 scope / scenarios / steps（那是 1.4 既有形状、由 wire 的既有测试守）。Codex 第三十五轮（闭合，五条成立）处置（第二轮，code 与测试一笔）：⑨ 写前校验对「设备目标但组合根尚未填入设备请求」单独按产品语言拒绝（要在什么目标上执行、这个版本还不能指定测试设备、去掉 @device 与 @app 先在桌面执行），不再把「非桌面目标当且仅当带设备请求」的不变量打给使用方；其余 DefinitionContractError 只会由畸形 job 触发、按契约型异常原样转述；⑩ 低于设备下限的改法按删掉 tag 后真正接替的来源给：--default-job-timeout 也低于下限时写明「一并调它或不给」、够时写「改由它接替」、没给时才写「走缺省」，来自 --default-job-timeout 的则建议改它或单独标 tag；非正 @timeout 的消息写清删掉 tag 后由 --default-job-timeout 或目标缺省接替；⑪ plan 降级警告的云端阶段写「最迟由 worker 在建会话前自检拒绝」（当前写前校验更早拒绝，项目配置接入后由 worker 拒绝，两种状态都成立）；⑫ 护栏：plan --json 应用条目恰为别名与包名两键；云端 run / submit 真走共享前置、设备 job 以退出码 2 被拒且云端解析一步不走（内存删掉接线即红，已对抗核过）。Codex 第三十七轮（闭合）只剩一条：拒绝消息里「配置文件的读取尚未接入」是施工说明——第三轮去掉这半句，消息只说要在什么目标上执行、这个版本还不能指定测试设备、怎么改。Codex 第三十八轮总判定设计已落到位，本批闭合。


**依赖**

- B3-config-submit：提供 [apps] 别名映射（alias -> 平台 -> {file, package/bundle-id}）与 [devices.<平台>].acquire-timeout-s，用来算 default_device/min_device；之后在组合根填 device_request、上传安装包并补齐 AppRef 的 bucket/key/sha256、写 definition 前调用本批的 validate_job_definition。本批先用 0051 内建 600 秒，apps 映射用空表占位
- B6-midscene-device：TS 侧 Job interface（engines/midscene/src/lib/job-source.mts）扩展 timeoutS/target/deviceRequest，跨语言 golden 测试要它跟上才能转绿
- B1-capabilities：plan 标注（0048 决策 5 的目标行与会话数显示，决策 4 的「引擎不支持该目标」拒绝）消费本批的 Job.target；本批只产出 target，不做能力比对

**改动面**

- `core/gherkai_core/model.py` · 新增 Target / AppRef / DeviceFarmRequest 三个 frozen dataclass（放在 Job 之前的「输入侧」段）：Target(device: Literal['desktop','android','ios']='desktop', ui_kind: Literal['web','app']='web', app: AppRef|None=None)；AppRef(alias, app_id, bucket: str|None, key: str|None, sha256: str|None)，plan 形态只有 alias 与 app_id，位置三项由 run/submit 上传后补齐；DeviceFarmRequest(provider: Literal['aws-device-farm'], device_arn: str|None, os_version: str|None, billing_method: str, project_arn: str, acquire_timeout_s: float)。名字直接写明服务商，不起中立名，也不加形态字段（形态由 worker 固定只取手机）。另配一个模块级常量，列出五种合法组合 desktop/web、android/web、android/app、ios/web、ios/app（0048 决策 1、决策 3）
- `core/gherkai_core/model.py` · class Job：新增 target: Target = Target()（缺省 desktop/web，现有构造点不受影响）和 device_request: DeviceFarmRequest|None = None。改写 timeout_s 的注释：原文「worker 不消费」改为「worker 只在建会话前拿它与 max_session_s 比较作自检，不计时」，并写明设备 scope 恒为有限正数（0048 决策 3；0034「job timeout」节载体条；0051 决策 2）
- `core/gherkai_core/model.py（或新建 core/gherkai_core/target.py）` · 新增纯函数 validate_job_definition(job) -> None：做结构校验，违约抛契约型异常：非桌面目标当且仅当 device_request 存在；project_arn 非空；device_arn 与 os_version 恰有一个；字段类型正确；(device, ui_kind) 属于合法组合；ui_kind=app 当且仅当 app 存在；桌面目标不得带 app。取值域校验（billing_method 枚举、os_version 点分数字、ARN 前缀）不放这里，归 CLI。plan 形态的 Job（device_request 为空）不走这道校验，或者另给 plan 形态一个宽松入口，两种形态要分开（0048 决策 3「写 definition 之前与推进器读 definition 时各做一次结构校验」）
- `core/gherkai_core/scope.py` · 常量段与新增 _resolve_target(scope_id, members, apps) -> Target：新增 _DEVICE_PREFIX='@device:' 和 _APP_PREFIX='@app:'，复用 _values_with_prefix，空值因此自动报错。规则与 _resolve_engine 同构：任一成员标了，整个 scope 生效；同一 scope 内出现多个不同值报 FeatureContractError。另四种情形也报 FeatureContractError：@device 取值不是 android/ios（显式写 @device:desktop 也报）；@app 出现在桌面 scope；别名在 apps 里查不到；别名缺本平台条目。device 与 app 两个维度分别做冲突判定。核对 apps 需要 CLI 注入的 apps 映射（见 open_questions）（0048 决策 2、决策 3「解析」；0019 三条规则）
- `core/gherkai_core/scope.py` · class PlanConfig：字段改成 0025 接口：default_job_timeout_s 的语义改为「显式给出的值，未指定为 None」，并且要能区分三态：未指定 / 显式非正 / 显式正值。现在 CLI 把 <=0 归一成 None，与「未指定」撞在一起，必须拆开，可以把非正值原样传进来，或另加一个哨兵。新增 default_desktop_job_timeout_s（300）、default_device_job_timeout_s、min_device_job_timeout_s（后两者由 CLI 按获取预算算出），以及 apps 映射（alias -> {platform -> app_id}）（0025 接口段与「timeout 解析」节；0034「job timeout」节覆盖顺序①②）
- `core/gherkai_core/scope.py` · _resolve_timeout：签名加上目标（或 is_device）和整份 config。顺序：① 有 tag 用 tag，否则用显式值，再否则用目标缺省（桌面 300，设备取 default_device）；② 显式非正：非设备 scope 返回 None（不超时），设备 scope 落到设备缺省、不报错；③ 下限只对 tag 与显式正值校验：设备 scope 低于 min_device 抛 FeatureContractError，消息说明可能还没拿到设备就被判超时；目标缺省本身不校验。保留现有的有限正数校验和冲突校验（0034「job timeout」节覆盖顺序与校验顺序；0019 @timeout 段；0025「timeout 解析」节）
- `core/gherkai_core/scope.py` · plan() 第 3 步循环与模块 docstring：跳过筛空 scope 之后，先对全量成员调 _resolve_target，再把目标交给 _resolve_timeout（timeout 依赖目标），最后 Job(..., target=target)，device_request 保持 None。筛选的不变量照旧：目标也按全量成员解析。模块 docstring 的「语义」列表补上 device/app 两条，timeout 那条改写为按目标给缺省与下限（0048 决策 3；0041 决策一不变量（经 0025 select 条））
- `core/gherkai_core/wire.py` · job_to_json：按可选键追加三项：timeoutS（job.timeout_s 不为 None 才写）；target（非桌面才写，也可以一律写，待定，见 open_questions），形状 {device, uiKind, app?{alias, bucket, key, sha256, appId}}；deviceRequest（不为 None 才写）。新增私有 _target_to_json / _device_request_to_json，同文件保持手写映射。现有键 scope/engine/scenarios/assertionVotes 不动（0024 输入行「可选键 timeoutS / deviceRequest / target」；0048 决策 3）
- `core/gherkai_core/serialize.py` · job_to_dict / job_from_dict：持久化 target 与 device_request，桌面目标且 device_request 为 None 时不写这两个键（omit），旧落盘缺键读回 desktop/web 与 None，往返恒等。job_from_dict 读回后调 validate_job_definition，对应推进器读 definition 时的那次校验；写端那次在组合根，归 B3。字段名用 snake_case，与本文件其余持久化键一致（0048 决策 3（definition 自包含、读时结构校验）；serialize 模块头的往返约束）
- `core/gherkai_core/parse.py` · 无需改动：ParsedScenario.tags 已合并 feature 级与 scenario 级，继承规则已由 gherkin Compiler 兑现；只需把 ParsedScenario docstring 里「按 @scope/@engine」的举例补上 device/app（0048 决策 2 继承条）
- `cli/gherkai_cli/__main__.py` · run / plan / submit 三处 --default-job-timeout 的 argparse（约 208、306、341 行）：default 由 300.0 改为「未指定」哨兵（None），type 换成只收有限数的转换函数（拒绝 nan/inf，报错形态与 argparse 一致）。help 改写：默认按目标给出（桌面 300 秒，设备另算）；<=0 只让非设备 scope 不超时（0034「job timeout」节①②（argparse 缺省为未指定哨兵、归一化只接受有限数））
- `cli/gherkai_cli/__main__.py` · _load_and_plan 里的 PlanConfig 组装（约 951-960 行）：不再把 <=0 归一成 None，按三态原样传入；补上 default_desktop_job_timeout_s=300、default_device_job_timeout_s=acquire+900、min_device_job_timeout_s=acquire+180 和 apps 映射。acquire 取 0051 内建 600 秒，配置文件覆盖接上后改由 B3 提供。约 2165 行打印 default_job_timeout 的那一行要能处理 None（0025 接口；0051 决策 2；0053 default-job-timeout 条）
- `tools/e2e_harness.py` · 约 64 行 PlanConfig(default_engine=..., default_assertion_votes=...)：新字段缺省一旦生效，这里的桌面 job 会从「不超时」变成 300 秒。需要确认 harness 是否依赖不超时，必要时显式传参（0034「job timeout」节（桌面缺省 300））
- `core/gherkai_core/scope.py 模块头、docs/adr/0025（如实现偏离接口段）` · 文档校准：实现落地后按差集逐项核对 0025 接口段的 config 字段与 PlanConfig 实际字段；0025 若要补 apps 字段，先改 ADR（CLAUDE.md 文档纪律；0025 接口段）

**先写的护栏测试**

- `core/tests/test_plan.py`：@device 与 @app 的归约：feature 级 @device:android 由 scenario 继承；同一 scope 里一条标 android、一条不标，整个 scope 都是 android；同一 scope 里 android 与 ios 并存报 FeatureContractError；同一 scope 里两个不同 @app 别名报错；@device:desktop 与 @device:foo 都报错；裸 @device: 和 @app: 报错且消息带 uri:line（扩展 test_bare_tag_without_value_errors_with_location 的参数）（0048 决策 2）
- `core/tests/test_plan.py`：@app 的合法性：@app 用在桌面 scope 报错；别名不在 apps 映射里报错；别名只有 android 条目却用在 @device:ios 的 scope 上报错；合法时 Job.target == Target('android','app',AppRef(alias, app_id, None, None, None))，device_request 为 None（0048 决策 2、决策 3（plan 形态只填 target））
- `core/tests/test_plan.py`：按目标解析 timeout 的真值表：未指定加桌面得 300；未指定加设备得 acquire+900；显式 0 或负值加桌面得 None；显式 0 或负值加设备得设备缺省、不报错；显式正值低于下限加设备报 FeatureContractError；@timeout:N 低于下限加设备报错；N 等于下限通过；tag 优先于显式值；设备缺省本身低于下限也不校验（构造 default_device < min 的 config 验证不抛）。改写 test_timeout_absent_and_no_default_is_none，因为无 tag 无显式值的桌面 scope 不再是 None（0034「job timeout」节①②③；0019 @timeout 段；0025 test cases 第 124 行）
- `core/tests/test_plan.py`：select 不变量扩到 target：筛掉部分成员后，Job.target 和按目标得出的 timeout_s 与全量解析逐字一致；被整组筛空的 scope 里即便有 @device 冲突，也不拦本次迭代（0041 决策一（经 0025 select 条）；0048 决策 3）
- `core/tests/test_wire.py`：协议字段红线：桌面且无 timeout 的 job，job_to_json 的键集合与现状完全相同（scope/engine/scenarios/assertionVotes），旧 worker 零变化；有 timeout 时多出 timeoutS；设备 app 的 job 输出 target.device/uiKind/app.{alias,bucket,key,sha256,appId} 和 deviceRequest.{provider='aws-device-farm', deviceArn 或 osVersion 二选一, billingMethod, projectArn, acquireTimeoutS}；用键集合差集断言，不逐个读（0024 输入行可选键；0048 决策 3）
- `core/tests/test_serialize.py（或现有 serialize 往返测试所在文件）`：job_from_dict(job_to_dict(job)) == job 对桌面、android/web、ios/app（带 device_request）三种形态都成立；桌面 job 的 dict 里没有 target/device_request 键；旧落盘缺键读回 desktop/web；读回非桌面却缺 device_request、ARN 与 os_version 同时出现或同时缺失、project_arn 为空，都由 validate_job_definition 拒绝（0048 决策 3 结构校验；serialize 往返约束）
- `core/tests/test_plan.py 或新建 core/tests/test_target.py`：差集护栏：合法组合常量 == {desktop/web, android/web, android/app, ios/web, ios/app}；Target 的 device 与 ui_kind 取值域等于 0048 决策 1 表格；DeviceFarmRequest 的字段集合 == {provider, device_arn, os_version, billing_method, project_arn, acquire_timeout_s}（0048 决策 1、决策 3）
- `engines/midscene/src/worker/job-source.test.mts 加 Python 侧 fixture 生成（core/tests/test_wire.py 写出 golden JSON）`：Python 到 TS 的往返：由 job_to_json 生成桌面、android/web、ios/app 三份 golden 行，TS 的 Job 类型解析后再序列化，键集合与 Python 一致；以后任一侧加字段而另一侧没跟，测试就会变红。TS 的 Job interface 扩展本身归 B6，但 fixture 与断言应在本批先立起来（0048 决策 3「由一条 Python 到 TS 的往返测试守字段集合一致」）
- `cli/tests（argparse 相关测试）`：--default-job-timeout 不给时 args 值为哨兵 None，PlanConfig 拿到「未指定」；给 300 时为显式 300（与内建 300 可区分）；给 nan 或 inf 以退出码 2 结束（0034「job timeout」节①②）

**完整性审查补认领**

- 两个 worker 建会话前的自检（Job 的 target 与 timeoutS 对照自身 targets 与 max_session_s，不满足发 scope_done{status: error, errorType: precheck_failed}）；Nova worker 必须读 target，否则设备 job 落到 Nova 镜像会被当桌面执行。0049 决策 7。
- 发布边界（第十轮同僚复核指出）：本批是第一个能产出非桌面 Job 的批次，必须与上面的 worker 自检同批发布，并依赖 B5 已让 core 认 scope_done 的 status 字段。这样在 B6 完成前，非桌面目标由设计内的机制拦住：没有 worker 声明设备目标，本机预检拒绝、云端 worker 记 precheck_failed，不需要临时闸门。
- 红线测试补：plan --json 的 app 恰有 alias 与 app_id 两键；完整 definition 的应用条目五项逐项缺失、空值、错类型、半成品，在写入与读取两处都拒绝；跨语言往返测试必须在删掉一个 TS 侧契约字段后确实失败（JobSource 只是 JSON.parse，「解析再序列化」会假绿，要对照显式的字段清单）。
- 本机执行前预检的两项目标检查（目标不在该引擎 targets 里、墙钟超过 max_session_s）与 plan 的目标拒绝（FeatureContractError、消息给两种改法；能力查询失败时只警告），消费 B1 的 engine_targets。0048 决策 4、0049 决策 4。
- plan 的目标标注：每个 job 行显示目标，汇总这次 run 要开的设备会话数，同步到 plan --json。0048 决策 5、0049 决策 6。
- Python 到 TS 的 Job 往返测试（target、deviceRequest、timeoutS 与嵌套 app 的字段集合），TS 侧 job-source.mts 的类型同批扩展。0048 决策 3。

**真跑或对抗核查才算数的结论**

- 版本错位：新 CLI 写入带 target/device_request 的 RunMeta，若被旧版 cloud Lambda 推进器读（旧 job_from_dict 忽略未知键），设备 job 会被当作桌面 job 静默起桌面 worker。要在真部署上确认 CLI 与后端版本不一致时有拦截（版本一致性检查覆盖这条路径），或者确认这一路不可达。单测证明不了
- Fargate 路径：带 target/deviceRequest/timeoutS 的 job 行经 S3 PutObject 后，由真实 Midscene 与 Nova 镜像的 JobSource 读回，旧字段行为不变（Nova 遇到多出的 timeoutS 键不出错）。至少用 tools/e2e_harness.py 真跑一次桌面 job，确认加了 timeoutS 后两引擎行为与之前一致
- 桌面缺省由「CLI 内建 300」改为「哨兵加 plan 层补 300」之后，同步 run、local submit、cloud submit 三路推进器对桌面 job 的到点处置时刻不变。可用短 @timeout 与不标 tag 各真跑一次（local 与 cloud）核对 timed_out 归因

**易错点**

本批最容易做错的有三件事。

1）timeout 的「未指定」与「显式非正」混成一个 None。现状 CLI 把 <=0 归一成 None，argparse 的 default 又是 300.0。只在 core 里补按目标给缺省，而 CLI 照旧把 300 当显式值传进来，设备 scope 会被 300 秒的显式值顶掉，而且 300 低于下限 780，会被误拒（或者误放行）。必须先改 argparse 哨兵和 PlanConfig 的三态，再写 _resolve_timeout，顺序是：目标先解析，再解析 timeout；下限只校验 tag 与显式正值。

2）协议向后兼容。job_to_json 对桌面且无 timeout 的 job，键集合必须与现状逐字一致，job_to_dict 对桌面 job 也不写新键。否则旧镜像、旧落盘、旧 Lambda 会出现差异，CLI 新、Lambda 旧时，设备 job 还可能被静默当成桌面 job（见 real_run_checks）。

另外，target 必须和 engine、timeout 一样按全量成员解析（0041 不变量），不能在 select 之后解析。显式写 @device:desktop 按 0048 的字面规定是错误，测试要钉住，免得实现者顺手放行。

涉及文件：/Users/lzy/workspace/yaozhou/core/gherkai_core/scope.py、model.py、wire.py、serialize.py，/Users/lzy/workspace/yaozhou/cli/gherkai_cli/__main__.py（约 208、306、341、951 行），/Users/lzy/workspace/yaozhou/tools/e2e_harness.py（约 64 行）。


## 4. B3-config-submit：项目配置文件、组合根填 device_request、definition 格式版本、CLI 侧应用上传

规模 L。

**进度（2026-10-27）**：分五个子批提交：①配置模块与取值顺序、②设备请求解析与 plan 标注、③definition 格式版本与缺戳例外、④应用上传、⑤文档。① 已落地（code 一笔）：`cli/gherkai_cli/config.py` 做定位 / 读取 / 形态校验（[devices] 与 [apps] 类型化解析、[apps] 的 file 按配置文件目录绝对化、acquire-timeout-s 上界取 core 的 MAX_ACQUIRE_TIMEOUT_S）；七个命令加 `--config`；会被配置覆盖的六个选项（default-engine / assertion-votes / max-concurrency / report-dir / backend / tunnel）改 None 哨兵、内建默认在配置合成后补；`_apply_project_config` 三类去向——没有环境变量层的填进 args，有环境变量层的（prefix / ddb-table / s3-bucket / region / profile / steps-dir）只校验后存 `args.config_values`、经 compose 三个解析链与 steps-dir 链新加的 config_* 形参插在环境变量之后，[cloud] 整节只在云端后端生效；[common] / [cloud] 的接受键由 argparse 差集推出（按次选择型、云端专用、设备映射三份名单在 `__main__`，护栏 test_project_config 对照显式名单）；本机 submit 的 per-run 进程与 status --wait 接力改收解析后的 region / profile；doctor 多 config.file 行（契约页与 skill 副本同步）；PlanConfig 的 apps 与获取预算改由配置给出。与底稿的出入：events-table / cluster 没有环境变量层，配置值直接当选项值传、不另开 config 形参；设备专用的四个选项与 plan 的设备标注归 ②。pytest 整仓 2334 绿。


**依赖**

- B2-core-target-job：Job.target（device/ui_kind/app{alias,bucket,key,sha256,app_id}）与 device_request 数据类及其 serialize 往返、写 definition 前的结构校验函数、PlanConfig 新增的 apps 别名表与 acquire_timeout_s 入参、default_job_timeout_s 区分「未显式给出」与「显式不超时」的新表示，以及 plan 解析 @device/@app 时的 FeatureContractError
- B8-deploy-iac：SSM 设备项目参数的键名常量（names 里与 BACKEND_VERSION_KEY 并列）、产物桶按 gherkai=app 标签 14 天过期的生命周期规则（E、R 常量应与本批共享一处）、CLI 角色的 S3 应用前缀读写/分段中止/打标签与 HeadObject 区分 404 所需的 ListBucket 授权
- B7-tunnel：会话预热地址在 RunMeta 上的字段名，供「run 带设备目标或会话预热地址」谓词与缺戳例外共用；预热地址也是 format 升到 1 的理由之一
- B5-core-events-termination：本批只提供 UnsupportedDefinitionFormat 与 DEFINITION_FORMAT，云端推进器遇更高格式「不推进、记诊断、标 error」由该批（或 B8 的 Lambda 侧）消费实现

**改动面**

- `cli/gherkai_cli/config.py（新增模块）` · locate_config / load_config / ProjectConfig 数据类：按 --config > GHERKAI_CONFIG > ./gherkai.toml 定位；缺省位置不存在等于无配置，显式路径不存在或 tomllib.TOMLDecodeError 以退出码 2 结束并点名文件与行列；不向上级目录查找。解析出 common/cloud（按键名=长选项名）、devices（顶层 billing-method / acquire-timeout-s / project-arn / app-bucket + android/ios 子表 arn | os-version | billing-method）、apps（别名 → {android:{file,package}, ios:{file,bundle-id}}）。未知节/键以退出码 2 结束并点名文件、节、键；os-version 为 float/int 时以退出码 2 结束并提示加引号；同一子表 arn 与 os-version 同给以退出码 2 结束；apps 条目 package / bundle-id 缺失以退出码 2 结束。路径类值（steps-dir、report-dir 仅本机后端时、apps.*.file）以配置文件所在目录为基准绝对化。记录每个值的来源（flag/env/config/default），供后续「config 来源不触发 flag 专属提示/拒绝」判断。（0053 决策 1、2、3、6）
- `cli/gherkai_cli/__main__.py` · _build_parser（run/plan/submit/status/explain/doctor/list-deterministic 各子命令）：七个读配置的子命令加 --config PATH；run/submit（是否给 plan 见 open_questions）加 --android-device-arn / --ios-device-arn / --device-farm-project-arn / --app-bucket。把会被配置层覆盖的选项的 argparse default 改成 None 哨兵（现状 --default-engine='novaact'、--assertion-votes=1、--max-concurrency=DEFAULT_MAX_CONCURRENCY、--default-job-timeout=300.0、--report-dir='reports'、--backend='local'、--tunnel='ngrok' 都是硬默认，分不出「用户没给」），内建默认移到配置合成之后补。help 文本里的「默认 300」改写为按目标补缺省的说法。（0053 决策 2、3、4）
- `cli/gherkai_cli/__main__.py` · main（parse_args 之后、分派之前）新增 _apply_project_config(args, parser)：仅对七个读配置命令执行（_reconcile/_tunnel_watch/deploy/destroy/skill/list-engines 不读）。对没有环境变量层的选项：取 config 值经与 argparse 同一套 type/choices 转换（例如经子 parser 重新解析由 config 构造的 argv 片段，或复用 action.type 与 action.choices），填入仍为 None 的 args 字段，再补内建默认；对有环境变量层的选项（prefix、ddb-table、s3-bucket、region、profile、steps-dir）不得把 config 值写进 args（否则 config 越过 env），改为以 config_* 形参传给下面的解析链。[cloud] 键在 backend=local 时静默不生效；对当前命令不存在的键忽略。（0053 决策 2、3）
- `runtime/gherkai_runtime/compose.py` · resolve_region / resolve_aws_identity / resolve_cloud_target：新增 config 层形参：resolve_region(explicit, profile, *, config_region=None) 的顺序改为 --region > AWS_REGION > AWS_DEFAULT_REGION > config_region > profile config；resolve_aws_identity 增 config_profile（AWS_PROFILE 之后）；resolve_cloud_target 增 config_prefix / config_runs_table / config_bucket 等，插在 env 兜底之后、prefix 默认名之前。detached.build_local_reconcile 不传 config 层（宿主不读文件，值已在 definition 或由提交侧 argv 传给 per-run 进程）。（0053 决策 2（region 链）、决策 1）
- `cli/gherkai_cli/__main__.py` · _steps_dir_or_error / _resolve_steps_dir / _resolve_steps_dir_for_backend：顺序改为 --steps-dir > GHERKAI_STEPS_DIR > config steps-dir（已按配置文件目录绝对化，显式给出但不是目录同样以退出码 2 结束）> ./steps（存在才用）。云端后端的「--steps-dir 不生效」提示对 config 来源同样给出（0053 决策 3 对 project-arn/app-bucket 采用同一形态）。doctor 调用点同步。（0053 决策 2、0037 决策 4）
- `cli/gherkai_cli/__main__.py` · _load_and_plan（PlanConfig 构造）：PlanConfig 增传 apps 别名表（别名 → 平台 → app_id，供 core 报 FeatureContractError）与 acquire_timeout_s（供 plan 层按目标补缺省墙钟与下限校验）；default_job_timeout_s 区分「未显式给出」与「显式不超时」（现状把 <=0 归一成 None 且 None=不超时，与「None=按目标补缺省」冲突，需要 B2 定的新表示）。plan 只核对 [apps] 引用到的 file 存在，不读内容、不算哈希。（0053 决策 2、3；0048 决策 2、3）
- `cli/gherkai_cli/__main__.py` · _plan_and_preflight 末尾新增 _resolve_device_requests（本机后端在此；云端后端放在 _submit_cloud / _cmd_run 云端分支的 skew 闸与资源 preflight 之后）：按 job.target.device 收集平台；每平台 arn 依次取 --<平台>-device-arn > GHERKAI_<平台>_DEVICE_ARN > config arn，否则 config os-version；都没有以退出码 2 结束（文案按 0053 决策 4 示例）。billing_method 取平台子表 > [devices] > METERED，取值域校验（METERED/UNMETERED、os_version 点分数字串、ARN 前缀 arn:aws:devicefarm:）在此以退出码 2 结束。acquire_timeout_s 取 config > 600，上界 3600 校验。project_arn：本机后端 --device-farm-project-arn > GHERKAI_DEVICE_FARM_PROJECT_ARN > config，缺失以退出码 2 结束；本机后端调 compose.probe_aws_identity 比对 ARN 账号段，不一致仅警告并点名两账号；云端后端读 SSM 设备项目参数，ParameterNotFound 以退出码 2 结束「部署未启用设备支持」，config/flag 里的 project-arn/app-bucket 只提示不生效。用 dataclasses.replace 把 device_request 填进每个非桌面 job，然后调用 B2 的结构校验。（0048 决策 3；0053 决策 3、4；0051 决策 2、10）
- `runtime/gherkai_runtime/app_upload.py（新增，或放进 compose，带 [aws] 延迟导入）` · ensure_app_object(bucket, file, *, managed: bool, now, s3) -> AppLocation(bucket, key, sha256)：流式算 sha256；键 = apps/<sha256>/<原文件名>。HeadObject：404 → 上传（upload_file 分段，managed 时 ExtraArgs Tagging='gherkai=app'）；managed 且 LastModified 年龄 <= E−R（14−7=7 天）→ 复用；超过 → 同键 CopyObject（MetadataDirective=REPLACE、TaggingDirective=REPLACE、Tagging='gherkai=app'），失败则重传，再失败抛错让 CLI 以退出码 2 结束、不复用；403 → 以退出码 2 结束并说明权限。unmanaged（本机后端应用桶）只做存在性复用，不打标签、不刷新。>500 MB 警告不拦截。E、R 为具名常量，与 B8 的生命周期规则共享一处定义。（0051 决策 9）
- `cli/gherkai_cli/__main__.py` · _cmd_run / _submit_local / _submit_cloud：应用上传接线：在全部零副作用闸（skew、资源 preflight、variant、device_request）之后、persistence.begin / create_run 之前调用上传，把 bucket/key/sha256 补进 job.target.app（云端用 target.bucket 产物桶、本机用 --app-bucket > GHERKAI_APP_BUCKET > config app-bucket，缺失且有 app scope 以退出码 2 结束）。同一 (文件, 桶) 在一个 run 内只上传一次。（0051 决策 9；0053 决策 3；0048 决策 3）
- `cli/gherkai_cli/__main__.py` · _cloud_skew_gate：增形参 requires_stamp（由「run 带设备目标或会话预热地址」谓词算出，谓词单点放 compose，供 B7 共用）；戳缺失且 requires_stamp 时以退出码 2 结束，文案「后端部署早于本功能，请先升级部署」。只在 run/submit 传 True；status/explain 维持只警告。对应改 compose.check_version_skew / check_backend_skew 增同名参数，保持判据与措辞单点。（0037 决策 7（缺戳例外））
- `core/gherkai_core/serialize.py` · run_meta_to_dict / run_meta_from_dict + 新常量与异常：新增 DEFINITION_FORMAT = 1 与 UnsupportedDefinitionFormat(found, supported)；写端恒写整数 format；读端缺键读作 0，> DEFINITION_FORMAT 抛 UnsupportedDefinitionFormat（类型错误同样拒）。注意 serialize.from_dict（RunReport/manifest）经 run_meta_from_dict，会一并受闸。（0037 决策 7（definition 格式版本））
- `core/gherkai_core/adapters/run_store/ddb.py、local.py` · DynamoDBRunStore.create_run / load_run_meta；LocalRunStore.load_run_meta；新增只读 peek_definition_format(run_id)：META 的 format 随 run_meta_to_dict 进 meta_json（另可冗余成 META item 顶层属性，便于 status 不触发 arg_offloader 的 S3 取回而只读格式号）；load_run_meta 透传 UnsupportedDefinitionFormat。新增轻量 peek 供 status/explain 用。（0037 决策 7）
- `cli/gherkai_cli/__main__.py` · _cmd_status / _status_cloud / _cmd_explain / _explain_cloud；runtime/gherkai_runtime/detached.build_local_reconcile 与 _cmd_reconcile：现状 status/explain 只读 run_state、不读 definition，格式闸照不到；加一步读格式号（本机 run_meta.json、云端 META），高于支持值以退出码 2 结束并用产品语言提示升级 CLI。本机接力（status --wait、_reconcile）在 load_run_meta 处捕获异常同样以退出码 2 结束。云端推进器「标 error 不推进」不在本批（见 depends_on）。（0037 决策 7）
- `cli/gherkai_cli/__main__.py` · _cmd_plan / render.plan_to_dict、render_plan_text：plan 读配置；有设备 scope 的平台未指定设备时在输出标注并 stderr 警告、退出码 0；原样展示配置的 ARN 或 os-version；os-version 段数少于设备版本常见全段（只写前缀）时提示「写全版本号可以固定」。不调用任何 AWS。plan --json 新字段需同步 test_cli_json_contract。（0053 决策 4；0048 决策 5）
- `cli/gherkai_cli/__main__.py` · _cmd_doctor：增一行显示所加载配置文件的绝对路径或「未使用配置文件」（--json 同进 checks）。（0053 决策 1）
- `docs/user-guide/configuration.md、cloud-backend.md、CONTEXT.md、docs/adr/0053` · 文档校准：configuration.md 加 gherkai.toml 节、键表与取值顺序；升级说明写明同一 report 目录混用 1.4 与 1.5 CLI 不受支持；CONTEXT 词表若需「项目配置文件」词条按 0045 决策八先立条。键表用差集校对 argparse 真值。（0053；0037 决策 7；CLAUDE.md 文档纪律）

**先写的护栏测试**

- `cli/tests/test_project_config.py（新增）`：键集差集：从 _build_parser() 遍历七个读配置子命令的长选项全集，减去测试内显式列出的按次选择型排除名单（scope/tags/scenario/step/json/quiet/wait/config/位置参数/help/version 及评审后补入的项）与设备专用选项映射，等于解析器接受的 [common]∪[cloud] 键集；[cloud] 子集恰为只在 --backend cloud 下生效的那批。[devices] 顶层与平台子表接受集逐项等于 ADR 0053 决策 3 键表（billing-method/acquire-timeout-s/project-arn/app-bucket；arn/os-version/billing-method），多一键或少一键都失败。（0053 决策 6）
- `cli/tests/test_project_config.py`：取值顺序：对 default-engine、assertion-votes、max-concurrency、report-dir 断言 flag > config > 内建；对 prefix（AWS_RESOURCE_PREFIX）、steps-dir（GHERKAI_STEPS_DIR）、region（AWS_REGION、AWS_DEFAULT_REGION、config、profile config）、设备 ARN（GHERKAI_ANDROID_DEVICE_ARN）断言 env 胜过 config、config 胜过内建；特别钉住「config 值不会越过 env」这一反例。（0053 决策 2）
- `cli/tests/test_project_config.py`：错误形态：显式 --config 路径不存在、非法 TOML（消息含文件与行列）、未知节/键（点名文件、节、键）、类型/choices 不合法（与命令行给错时形态相同）均退出码 2；缺省位置不存在不报错；向上级目录不查找（子目录执行时父目录有 gherkai.toml 也不加载）。（0053 决策 1、3）
- `cli/tests/test_project_config.py`：设备段形态：同一子表 arn 与 os-version 同给退出码 2；os-version = 18.6（TOML 浮点）退出码 2 且消息含加引号提示；平台子表 billing-method 覆盖顶层；有 android scope 而任何来源都没给设备时 run/submit 退出码 2（文案含 [devices.android] 与 --android-device-arn）、plan 退出码 0 且 stderr 警告；本机后端 project-arn 账号与 stub 的 STS 账号不一致时警告文本点名两账号且不拦截。（0053 决策 3、4、6）
- `cli/tests/test_project_config.py`：解析结果落成 Job 里的具名 device_request：provider='aws-device-farm'、device_arn 与 os_version 恰一、billing_method、project_arn 非空、acquire_timeout_s 默认 600 且 >3600 退出码 2；桌面 job 的 device_request 为 None；云端 stub SSM 缺设备项目参数时提交前退出码 2「部署未启用设备支持」且 create_run 未被调用。（0048 决策 3；0051 决策 2、10）
- `cli/tests/test_project_config.py`：路径基准：在项目子目录执行、--config 指向别处两种情形下，definition 的 steps_dir 与 target.app 引用的本地文件都以配置文件目录为基准；flag/env 给的路径仍以 CWD 为基准。（0053 决策 2、6）
- `cli/tests/test_project_config.py`：宿主不读文件：submit 后把 CWD 换到另一个带不同 gherkai.toml 的目录，执行 status --wait（stub worker 记录收到的 Job）得到的 device_request 与 target.app 与提交时一致；build_local_reconcile 不调用配置加载（monkeypatch 加载函数抛错证明未被调用）。（0053 决策 1、6）
- `core/tests/test_stores.py（或新增 core/tests/test_definition_format.py）`：run_meta_to_dict 恒写 format=DEFINITION_FORMAT；缺 format 键的 1.4 形态 dict 读作 0 且正常反序列化；format=DEFINITION_FORMAT+1 时 run_meta_from_dict、LocalRunStore.load_run_meta、DynamoDBRunStore.load_run_meta（fake table）都抛 UnsupportedDefinitionFormat；带值往返恒等。（0037 决策 7）
- `cli/tests/test_main.py、cli/tests/test_backend_cloud.py`：CLI 读端格式闸：本机 status、status --wait、explain、_reconcile 与云端 status/explain 遇到更高 format 退出码 2 且消息为升级提示（无 ADR 编号、无内部名，过 test_user_facing_messages）；云端 status 的格式检查不触发 arg_offloader 的 S3 取回。（0037 决策 7；0039）
- `cli/tests/test_backend_cloud.py`：缺戳例外：stub SSM 无版本戳时，带设备 scope 的 run/submit --backend cloud 退出码 2「后端部署早于本功能，请先升级部署」、未做资源 preflight；纯桌面无隧道 run 维持警告并放行；status/explain 缺戳只警告。（0037 决策 7）
- `runtime/tests/test_app_upload.py（新增）`：stub S3：HeadObject 404 → upload 一次且 Tagging='gherkai=app'、键为 apps/<sha256>/<原文件名>；存在且 LastModified 年龄 <=7 天 → 不上传不复制；>7 天 → CopyObject 同键且 MetadataDirective/TaggingDirective 均为 REPLACE；CopyObject 失败 → 重传；重传也失败 → 抛错且 CLI 不调用 create_run；HeadObject 403 → 权限错误；unmanaged（本机应用桶）不带 Tagging、不 CopyObject；>500 MB 警告；同一文件在一个 run 内只算一次哈希、只上传一次；Job 的 target.app 带同一 sha256。（0051 决策 9）

**完整性审查补认领**

- 次序校正：完整结构校验放在应用上传补齐 bucket / key / sha256 之后、持久化之前；只补完 device_request 就做完整校验会挡住合法的应用提交（0048 决策 3 不定义半成品形态）。
- 本批前移定义三个纯接口，供后续批次消费：SSM 设备项目参数的键名常量（与 BACKEND_VERSION_KEY 并列）、应用对象保留期常量 E 与 R、RunMeta 的会话预热地址字段（B7 只填值、B8 只读键名）。
- 云端推进器读到更高 definition 格式时不推进、记诊断、把 run 标为 error 并带升级提示（Lambda 侧）。0037 决策 7。
- 0053 决策 6 的护栏测试：键集差集（排除名单 + 同词键 + 设备映射表）、设备段形态、路径基准、宿主不读文件、云端 report-dir 不绝对化。
- 真跑核对：CopyObject 同键刷新后 S3 生命周期是否按新创建时间重新计时（决定 E − R 复用规则是否成立）。0051 决策 9。

**真跑或对抗核查才算数的结论**

- boto3 upload_file 走分段上传时 ExtraArgs 的 Tagging 是否真落到对象上（单段与分段两条路径都要真跑核对 GetObjectTagging）
- 同键 CopyObject（MetadataDirective=REPLACE、TaggingDirective=REPLACE）后 LastModified 是否刷新、标签是否保留，以及生命周期过期是否按新创建时间重新计时（0051 决策 9 明写实施期核对）
- 按 0033 权限表建的真实 CLI 角色：对应用前缀 HeadObject 缺失键返回 404 而非 403、PutObject/PutObjectTagging/CopyObject/AbortMultipartUpload 允许、前缀外拒绝；云端读 SSM 设备项目参数落在 /{prefix}backend/* 已授范围内
- 原文件名含空格、中文或特殊字符时，S3 键经 worker 预签名后 Device Farm 的 Appium 主机能否下载安装（键编码问题只能真机验证）
- 本机后端 project-arn 账号比对用的 STS GetCallerIdentity 在 profile/SSO 凭证下的真实返回
- 端到端：submit 带设备 scope 后在另一 CWD 执行 status --wait，worker 实际收到的 Job 与提交时一致（stub worker 可证逻辑，真 worker 证 Job 线格式与 B2 的 Python 到 TS 往返一致）
- 真 1.4 发行版 CLI 读 1.5 写的 report 目录的实际表现，确认用户文档「不受支持组合」的描述准确

**易错点**

本批规划依据的代码在 /Users/lzy/workspace/yaozhou/cli/gherkai_cli/__main__.py、/Users/lzy/workspace/yaozhou/runtime/gherkai_runtime/compose.py、/Users/lzy/workspace/yaozhou/core/gherkai_core/serialize.py，以及 /Users/lzy/workspace/yaozhou/core/gherkai_core/adapters/run_store/ 下的 local.py 和 ddb.py。

最容易做错的两件事：

一、配置层插在环境变量层之后。现有的 env 兜底分散在三处：compose.resolve_cloud_target 管 AWS_RESOURCE_PREFIX、AWS_DDB_TABLE、AWS_S3_BUCKET；resolve_region / resolve_aws_identity 管 AWS_REGION、AWS_DEFAULT_REGION、AWS_PROFILE；_steps_dir_or_error 管 GHERKAI_STEPS_DIR。顺序都是「args 值 > env > 默认」。最省事的做法是把配置值写进 args 或 argparse default，但这样配置会静默越过环境变量，正好违反 0053 决策 2 的理由（CI 里的环境变量被入库文件覆盖）。这些项必须给解析链加独立的 config 形参。

同一处的另一个坑：argparse 现有硬默认（novaact、1、300.0、reports、local、ngrok）分不出「用户没给」，要改成 None 哨兵。其中 default-job-timeout 的 None 现在表示「不超时」，与 0053「未给时按目标补缺省」冲突，需要和 B2 先定新表示。改哨兵会波及 test_main.py 里一批依赖默认值的测试，按「接口诚实优先」照改。

二、definition 格式闸目前照不到 status/explain。这两个读端现在只读 run_state，从不读 run_meta / META，所以只在 run_meta_from_dict 加检查覆盖不了它们，要显式加一步读格式号。云端 status 不能为了读格式号就整份 load_run_meta：那样会触发 arg_offloader 去 S3 取回参数正文，改变 status 的权限面和开销。建议 META 上冗余一个顶层 format 属性或提供 peek 函数。

另外，run_meta_from_dict 也被 serialize.from_dict（manifest/RunReport）复用，闸会一并作用到报告读取，要确认这是想要的行为。

其它几点：
- 应用上传要排在所有零副作用闸之后、create_run / persistence.begin 之前。上传失败必须以退出码 2 结束，不能落下半成品 run。
- 有设备 scope 的 run 要先过缺戳例外（退出码 2），再读 SSM 设备项目参数。
- 新增的用户可见文案（设备未指定、部署未启用设备支持、后端早于本功能、升级 CLI、加引号提示、账号不一致）都要过 test_user_facing_messages，不带 ADR 编号与内部名。


## 5. B4-steps-registry：确定性 step 多句柄注册（targets、requires、driver 代理的注册面）

规模 M。


**依赖**

- B1-capabilities：CLI 契约校验接受 deterministic_steps[*].targets 与 requires 的形态，并做交集与 plan/list-deterministic 呈现（B4 只产出原样声明）
- B2-core-target-job：worker 侧拿到当前 scope 的测试目标（device、ui_kind、appId）的接口，供 selectHandler 与 ctx.uiKind/appId 使用
- B5-core-events-termination：errorType 枚举接纳 capability_unavailable（core 侧映射成产品文案）
- B6-midscene-device：命令守卫 driver 代理、能力探测结论（提供 / 不提供 / 探测出错）、withWebContext 的重新定位与切回、step 结束后的上下文核对复原、WebdriverCtx 的构造与 requires 前置判定在设备派发路径上的实现

**改动面**

- `engines/midscene/src/worker/deterministic.mts` · 类型段（DeterministicCtx / DeterministicHandler / Entry）：保留现 DeterministicCtx{page} 与 DeterministicHandler 作 playwright 句柄类型；新增 WebdriverCtx（driver / device{platform,osVersion,scale} / uiKind / appId / app / log / withWebContext 七字段，driver 类型只做 type import，实现由设备批次注入）、WebdriverEntry{uiKinds?, devices?, requires?, handler}、DeterministicHandlers{playwright?, webdriver?: WebdriverEntry | WebdriverEntry[]}；Entry 由单 handler 改为规范化后的 {playwright?: fn, webdriver: NormalizedEntry[]}（uiKinds/devices 缺省展开为全集、requires 缺省为 []）（0050 决策 1、决策 2）
- `engines/midscene/src/worker/deterministic.mts` · deterministic(pattern, handler, meta)：第二参改为 `DeterministicHandler | DeterministicHandlers`；函数形态等价于 {playwright: fn}。注册期校验（违反即抛、走 0037 决策 4 的加载失败）：未知句柄键；uiKinds 不属 web/app、devices 不属 android/ios；requires 不属封闭集合 {web_context}；含 web_context 时 uiKinds 必须恰为 ["web"]（因此缺省 uiKinds 加 web_context 也拒）；同一 step 两个 webdriver 条目覆盖同一（device, uiKind）组合（不论 requires 是否相同）；handler 非函数。保留现有 meta 必填校验（0050 决策 1；0048 决策 6）
- `engines/midscene/src/worker/deterministic.mts` · listRegistry()：每项加 `targets`：playwright 推出 {device:'desktop', ui_kinds:['web']}；每个 webdriver 条目按 device 展开、按（device, requires）聚合 ui_kinds，requires 非空时带 `requires`、不同 requires 的拆条不聚合；输出字段用协议的 snake_case（ui_kinds），原样报声明、不与 worker 顶层 targets 求交。顺序取规范序（见 open_questions 第 1 条）（0050 决策 1；0049 决策 1、3）
- `engines/midscene/src/worker/deterministic.mts` · match() / Match 类型 + 新增纯函数 selectHandler：scan()/matchBatch() 不动（命中与目标无关、--match-steps 输入输出不变）；match() 返回值改为 {entry 句柄集, groups}；新增 `selectHandler(hit, target:{device, uiKind})` → {kind:'playwright', fn} | {kind:'webdriver', fn, requires} | null。null 表示命中的 pattern 在当前目标上没有句柄，调用方走 AI，绝不顺延到下一个 pattern（0050 决策 1（跨 step 的命中与目标无关）；0049 决策 3）
- `engines/midscene/src/worker/run-scope.mts` · _runStep 派发 ①（约 772 行 matchDeterministic 分支）：桌面路径：hit 后 selectHandler(hit, {device:'desktop', uiKind:'web'})；为 null 时跳过 ① 落到 AI（现状是任何命中都调用 handler({page})，只有 webdriver 句柄的 step 在桌面上会把 page 喂给 webdriver handler 或直接崩）。设备路径的 requires 前置判定（capability_unavailable / engine_error）与 WebdriverCtx 构造在此留接缝，实现归设备批次（0050 决策 1、决策 2；0048 决策 6）
- `engines/midscene/src/worker/deterministic.steps.mts` · 脚手架只有内建导航条目（B0 已退役「页面地址匹配」）：本批给它补 webdriver 形态的约定注释；地址精确核对的 webdriver 写法（withWebContext 读地址后正则判定、抛 DeterministicAssertion，requires:['web_context']）作为 steps/ 模板示范进用户指南与 skill 参考，不进脚手架（0050 决策 1、2；0020 第 2 条）
- `engines/midscene/src/index.mts` · 公开导出面：再导出新增类型 DeterministicHandlers / WebdriverEntry / WebdriverCtx；头注释示例补多句柄写法；match/selectHandler 仍不对使用方开放（0050 决策 1、2；0037 决策 4）
- `engines/novaact/gherkai_worker_novaact/deterministic.py` · _Entry / deterministic() / list_registry() / match()：同构：_Entry.handler 改为规范化句柄集（playwright 可空 + webdriver 条目元组）；装饰器 `@deterministic(pattern, description=, example=)` 维持等价 playwright；新增多句柄注册形态（字典 {'playwright': fn, 'webdriver': [ {...}, ... ]}，具体签名随实现定），同一套注册期校验与 TS 逐项一致；list_registry 加 targets（同一推出与聚合规则）；新增 select_handler(hit, device, ui_kind)；_hits/match_batch 不动（0050 决策 1「Python 完全同构」）
- `engines/novaact/gherkai_worker_novaact/run_scope.py` · _run_step 派发 ①（约 392 行）：hit 后按 desktop/web 选 playwright 句柄；无 playwright 句柄（只写了 webdriver 的 Python step）时走 AI、不调用 handler、不报错——Nova 没有设备路径，这类 step 在本 worker 上永远走 AI，靠 targets 原样自述让测试开发看见（0050 决策 1；0049 决策 3、9）
- `engines/novaact/gherkai_worker_novaact/deterministic_steps.py` · 脚手架同样只有内建导航条目（B0 已退役 url_matches）：Python 侧没有设备路径，不补 webdriver 形态的示范；多句柄注册面的 Python 同构由跨语言 fixture 验收（0050 决策 1；0049 决策 9）
- `新增跨语言 fixture（如 engines/ 下两侧都能读到的共享 JSON）` · 注册输入与期望输出：一组注册输入（句柄键、条目字段、handler 用占位）配期望：推出的 targets（规范序）或期望的校验失败类别；TS 测试与 pytest 各自读同一份文件断言（0050 决策 1「两侧共用一套跨语言 fixture」）
- `docs/user-guide/writing-deterministic-steps.md 与 skill 的确定性 step 参考` · 注册面、ctx 字段、写作方法：补多句柄注册、targets/requires 含义、七字段 ctx（含 app.restart()）与原生上下文不变量、输入与定位事实、测试分层（离线缓存目录 cacheDir / WEBDRIVER_CACHE_DIR）、写作方法六条；不出现「先 AI 后硬化」建议。按 0039/0045 产品口吻，不写 ADR 编号（0050 决策 2、3、4、被拒方案）

**先写的护栏测试**

- `共享 fixture + engines/midscene/src/worker/deterministic.test.mts + engines/novaact/tests/test_deterministic.py`：跨语言一致：两侧读同一份 fixture，对每组注册输入断言 listRegistry/list_registry 的 targets 逐字节相同（含聚合、requires 拆条、规范序、snake_case 的 ui_kinds），对每个非法输入断言两侧都在注册期失败（未知句柄键、未知 uiKinds/devices/requires 取值、web_context 配非 ["web"]、缺省 uiKinds 配 web_context、两个 webdriver 条目覆盖同一组合含 requires 不同的情形、空 handlers / 空 webdriver 数组）（0050 决策 1）
- `engines/midscene/src/worker/deterministic.test.mts`：单函数写法向后兼容：deterministic(p, fn, meta) 的 targets 恰为 [{device:'desktop', ui_kinds:['web']}]，selectHandler(desktop/web) 返回该 fn；现有全部用例不改仍绿（0050 决策 1「单函数写法保持有效」；0049 决策 2）
- `engines/midscene/src/worker/deterministic.test.mts 与 test_deterministic.py`：不顺延红线：注册 A（只 webdriver android/app）与 B（另一个 pattern、playwright），若某文本同时命中两者 → 仍是冲突（命中与目标无关）；只命中 A 时 selectHandler(desktop/web) 返回 null，不回落到 B；matchBatch 输出形态不变（无 targets 字段）（0050 决策 1（跨 step 的命中与目标无关）；0049 决策 3）
- `engines/midscene/src/worker/run-scope.test.mts（及 Nova 对应派发测试）`：桌面派发：命中只有 webdriver 句柄的 step 时不调用任何 handler、走 AI 分支（用桩 agent 断言发生了 AI 调用、step 未记 error）（0050 决策 1；0049 决策 9）
- `engines/midscene/src/worker/deterministic.test.mts`：用测试自带的 steps/ 夹具注册一条带 webdriver 条目（requires:['web_context']）的地址核对 step，断言推出的 targets 为 desktop/web 无前提加 android/web 与 ios/web 各一条带 requires（与 0049 示例第二条一致）；webdriver handler 用伪 ctx（withWebContext 直接调用 fn、driver.getUrl 返回定值）判定通过与 DeterministicAssertion 两向（0050 决策 1；0048 决策 7）
- `engines/midscene/src/worker/user-steps.test.mts（真实运行层）与 test_user_steps.py`：真 loader 下使用方 steps 文件用多句柄形态注册、经 --capabilities 输出带 targets；注册期校验失败的 steps 文件让 worker 以加载失败退出、诊断带文件名（0050 决策 1 注册期校验；0037 决策 4）
- `cli 侧能力自述契约测试（与能力自述批次共建）`：两个 worker 真子进程 --capabilities 输出的 deterministic_steps[*].targets 通过 CLI 唯一契约校验（device/ui_kinds/requires 形态）（0049 决策 1）

**真跑或对抗核查才算数的结论**

- 命令守卫对 WebdriverIO 元素对象是否也生效：handler 经 ctx.driver.$() 拿到元素后在 step 结束后再调用 el.click()，必须被拒；Proxy 只包浏览器对象顶层方法时元素命令会绕过守卫，要用真实 WebdriverIO 客户端（Appium fake driver 或 Chrome for Testing）验证，mock 证明不了
- withWebContext 在真机上切入与（含抛错时）切回原生上下文、handler 自行 switchContext 不切回时 worker 复原：Android Chrome 与 iOS 15.8/18.6 Safari 各一次，下一条 AI 步截图坐标正确
- steps/ 模板里的地址核对 step（webdriver 条目，requires:['web_context']）：Android Chrome 真机读地址判定通过；iOS 26.3 Safari 上记 error、类别 capability_unavailable、不调 handler、不转 AI
- 真 loader（repo 外临时目录、真 dynamic import）下使用方 steps 文件 import 新增的类型与多句柄形态，注册进同一张表（类型只在编译期，但转译器对 type-only import 的处理要真跑确认不残留运行期 import 到 webdriverio）
- 离线层：本机 WebdriverIO 加 Chrome for Testing 打开材料页执行设备网页句柄，缓存目录显式指定后重启机器不重新下载（文档承诺的行为）

**易错点**

相关文件都在 /Users/lzy/workspace/yaozhou/engines/midscene/src/worker/ 与 /Users/lzy/workspace/yaozhou/engines/novaact/gherkai_worker_novaact/ 下。

最容易做错的两件事：
(1) 派发时把「目标上没有句柄」做成顺延或报错。现有 match() 命中即返回 handler，两侧 run_scope 都无条件调用 handler({page})。改造后命中的 pattern 若在当前目标上没有句柄，必须走 AI，不能去找下一个能匹配的 pattern，也不能记 error。scan/_hits 与 matchBatch/match_batch 必须保持与目标无关，否则 plan 标注会和实际派发对不上。这一条要先用测试钉住，尤其是 Nova 侧：只写了 webdriver 句柄的 Python step 在桌面上要走 AI。
(2) targets 推出与注册期校验两侧各写一份、悄悄漂移。规范形态（聚合键、顺序、snake_case 字段、单函数写法是否显式写出 targets）要先定下来，再落成共享 fixture，两侧测试读同一份文件。另外，「两个条目覆盖同一组合」不论 requires 是否相同都要拒绝，不能理解成「带前提的条目加一个无前提的兜底条目」，那等于把不转 AI 的契约变成静默回落。

次要风险：命令守卫与 withWebContext 的实现归设备批次，但 ctx.driver 的语义在本批写进类型与文档。要提醒设备批次：守卫必须覆盖 $() / $$() 返回的元素对象，只包浏览器对象的顶层方法不够。


## 6. B7-tunnel：隧道改为令牌换 cookie（桌面先行）、桌面 worker 的预热失败出口、脱敏规则三条

规模 L。


**依赖**

- B1-capabilities：自述对象里的会话预热支持布尔键（键名、CLI 侧唯一的契约校验处要核它是布尔，缺键语义为不支持）；本批在 _preflight_worker_runtimes 消费它，在两个 worker 的 _capabilities 产出它
- B5-core-events-termination：scope_done 的可选 status / errorType / message 字段（wire.py 编解码、ScopeDone 模型、对无事件 scenario 合成 SKIPPED），以及 precheck_failed 错误类别；本批两个桌面 worker 的预热失败与完整性不变量都经这个载体传递
- B2-core-target-job：job 的 target（ui_kind web / app），worker 据此判断「网页目标预热、应用目标不预热」；同时依赖 definition 格式版本 format（带预热地址的 definition 属于 1.5 格式）
- B3-config-submit：0037 决策 7 的缺戳例外，即带会话预热地址的 run 遇到无版本戳的后端时以退出码 2 结束；本批提供判定谓词「这次 run 是否带预热地址」（等价于给了 --expose-local），提交闸门归 B3。若这个谓词放在起隧道之后求值，失败要走 0035 决策 3 的「交棒前当场拆」
- B8-deploy-iac：新 reconciler Lambda 要随部署发布才会读回并注入预热地址（不然云端就是完整性不变量要抓的旧后端）；Lambda 代码改动本身列在本批 change_surface

**改动面**

- `runtime/gherkai_runtime/tunnel.py` · TunnelInfo：去掉 auth 字段与凭据内嵌的 mapped_base 拼接逻辑：mapped_base 直接返回干净的隧道地址 url；新增 warmup_url（形如 https://<隧道主机>/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T）。T 与 C 不作为可展示字段（避免 repr / tunnel.json 意外带出），只出现在 warmup_url 与策略文件里（0035 决策 1；0051 决策 13「做什么」）
- `runtime/gherkai_runtime/tunnel.py` · _gen_auth 与 NgrokTunnel.start 里的 basic-auth 策略 YAML：_gen_auth 换成两个各至少 128 位的随机串（T、C，例如 secrets.token_urlsafe(16) 以上，字符集不需要 URL 编码）。手写的 basic-auth 策略改为 4 条 on_http_request 规则：①预热路径加 GET 加令牌相等，返回 200 的 custom-response，带 Set-Cookie `__Host-gherkai_tunnel=C; Secure; HttpOnly; Path=/; SameSite=None`、`Cache-Control: no-store`、`Referrer-Policy: no-referrer`，响应体是带脚本的预热页（向校验路径请求一次，按结果把标题和正文改为 READY / DENIED / ERROR）；②预热路径其余情形返回 401，正文标记 AUTH REQUIRED；③校验路径 /.well-known/gherkai-tunnel-check 只凭 cookie 放行，返回 200 空体；④其余路径在 cookie 不等于 C 时返回 401（正文用产品语言说明「此地址需要测试会话」），同名 cookie 任一命中即放行，命中则原样转发。不得出现 remove-headers，规则数不超过 5。策略文件保持 mkstemp 生成的 0600 且不删除（理由同现注释）。docstring 与类注释里的「basic-auth 默认开启」改写（0051 决策 13「边缘策略」「对隧道服务商的要求」；0035 决策 1、4）
- `runtime/gherkai_runtime/tunnel.py` · NgrokTunnel.start 的 with_auth 参数：按 open_questions 第 5 条的结论处理：要么删掉这个参数（隧道模式恒带鉴权），要么定义关掉鉴权时 warmup_url 如何取值。目前 with_auth=False 产出的 TunnelInfo 没有预热地址，会被 worker 的完整性不变量判 precheck_failed（0035 决策 1 签名；0035「边界与不变量」definition 完整性）
- `runtime/gherkai_runtime/tunnel.py` · map_origin_in_jobs 内的 sub：把裸的 str.replace 换成带边界的识别：左边界是串首或 [A-Za-z0-9+.-] 以外的字符；右边界是 origin 之后最长的 RFC 3986 URL 字符串 R，R 为空、以 / ? # 开头、或全部由 . , ; : ! ) ] ' 组成才算命中。替换目标是干净的隧道地址。step 正文、DocString、每个表格单元格各自独立套用规则，一段文本里可以有多处命中（0035 决策 2「识别带边界」）
- `runtime/gherkai_runtime/tunnel_host.py` · TunnelSetup 与 start_tunnel_for_jobs：TunnelSetup 增加 warmup_url，与 extra_http_headers 一同返回；映射改用干净的 info.url，不再用凭据内嵌的地址。隧道模式下恒同时给出两项（额外请求头与预热地址），包括只有设备目标的 run，使 worker 侧的完整性判据在任何目标上都成立（0035 决策 4、「边界与不变量」definition 完整性；0051 决策 13）
- `core/gherkai_core/model.py` · RunMeta：新增可选字段 session_warmup_url: str | None = None（字段名可另取），注释说明 core 只搬运、不解释语义，载体是 definition 的原因与 extra_http_headers 相同（0051 决策 13；0035「边界与不变量」）
- `core/gherkai_core/serialize.py` · run_meta_to_dict / run_meta_from_dict：预热地址无值时省键（omit-when-None），读端缺键得 None；与 extra_http_headers、steps_dir 同一惯例。DDB META 与 S3 参数卸载对象经同一序列化，自动随带（0051 决策 13「无值省键」；0035 决策 5「明确不脱敏」清单）
- `runtime/gherkai_runtime/compose.py` · _COMPOSE_OWNED_WORKER_ENV、build_engines 的 common_env、_env 的判据：组合根拥有的键加上 GHERKAI_SESSION_WARMUP_URL（宿主继承的同名值必须抹掉）；build_engines 增加 session_warmup_url 参数，有值时写入 common_env，两个引擎都注入。更新段首注释，清单从三键改为四键（0037 决策 4「组合根拥有的四个 worker env」；0051 决策 13）
- `runtime/gherkai_runtime/compose.py` · build_fargate_engines 的 headers_env：增加 session_warmup_url 参数，有值时与 GHERKAI_EXTRA_HTTP_HEADERS 一同进入 RunTask containerOverrides 的 env（0051 决策 13；0035 决策 4、5（containerOverrides 列入明确不脱敏））
- `runtime/gherkai_runtime/detached.py` · build_engines 调用处（约 265 行）：从 meta 读回预热地址并传给 build_engines（per-run 进程与 status --wait 接力者两个宿主）（0035 决策 4 载体；0037 决策 4）
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py` · build_fargate_engines 调用处（约 368 行）：从 meta 读回预热地址并传入。这正是完整性不变量要抓的旧 Lambda 丢字段情形，新 Lambda 必须带上（0051 决策 13 完整性不变量）
- `cli/gherkai_cli/__main__.py` · _setup_tunnel、_build_run_meta 以及同步 run 的 build_engines / build_fargate_engines 调用（约 2122、2137 行）：_setup_tunnel 返回值加上 warmup_url，进度提示里的「basic-auth 已启用」改为产品语言（访问受每次运行一换的会话保护、运行结束即拆除），文中不出现令牌；_build_run_meta 写入预热地址；同步 run 的两个后端都传预热地址（0051 决策 13；0039（产品面文案））
- `cli/gherkai_cli/__main__.py` · _preflight_worker_runtimes：给了 --expose-local 且是本机后端时，worker 自述里没有声明会话预热支持（键缺失或为 false）就拒绝，退出码 2，提示用产品语言。这一步在起隧道之前（_plan_and_preflight 本就排在 _setup_tunnel 之前），所以不需要拆隧道（0051 决策 13「能力与拒绝点」；0049 决策 1、2）
- `core/gherkai_core/redact.py` · _USERINFO 正则、redact_url_userinfo、redact_deep：增加规则②：签名类查询参数与 gherkai_tunnel_token 的值替换成 ***，同时匹配 `?` / `&` / `&amp;` 三种前导形态；规则①按 open_questions 第 1 条的结论确定字符集。函数改名以反映覆盖面不只 userinfo，或保留旧名作为调用入口（wire.py、subprocess_engine.py、cli render.py 与 __main__ 的调用点跟着改）。模块头的三份互指说明保留（0035 决策 5 规则②；0051 决策 11）
- `engines/novaact/gherkai_worker_novaact/lib/redact.py` · 同上：与 core 逐字同步规则②（这个包不依赖 core，只能复制一份）；调用点 event_sink.py、evidence.py、run_scope._error_text 保持「先脱敏再截断」（0035 决策 5）
- `engines/midscene/src/lib/redact.mts` · USERINFO 与 redactUrlUserinfo：同步规则②；注意全局正则的 lastIndex 陷阱（已有测试覆盖）；调用点 event-sink.mts、evidence.mts、error-text.mts 不变（0035 决策 5）
- `engines/novaact/gherkai_worker_novaact/run_scope.py` · _run_session：set_extra_http_headers 之后、scope_started 之前：读 GHERKAI_SESSION_WARMUP_URL。完整性检查：有额外请求头而没有预热地址时，发 scope_done{status: error, errorType: precheck_failed, message: 后端未传递会话预热地址…}，不发 scope_started。有预热地址时，经 nova.page 导航一次，读响应状态与页面标记：READY 即就绪；DENIED 或 AUTH REQUIRED（401）为 precheck_failed；ERROR 或预算内没有任何标记时原地有界重导航，用尽后为 engine_error。预热导航抛出的异常不得被外层 _is_transient_network(connecting=True) 的建连重试吞掉或归为 EX_WORKER_NETWORK。没有这两个 env 时行为零变化（0051 决策 13「预热页面三种可见结果」「完整性不变量」；0051 决策 4 执行前失败走 scope_done）
- `engines/novaact/gherkai_worker_novaact/run_scope.py` · _capabilities：自述对象加一个布尔键，声明支持会话预热（键名与 B1 约定的一致）（0049 决策 1、2；0051 决策 13）
- `engines/midscene/src/worker/run-scope.mts` · connect() 之后、emit scope_started 之前（桌面路径）：与 Nova 对称：先做完整性检查，再用 page.goto 预热一次并确认标记，按同样规则归因，经 scope_done{status, errorType, message} 传递（按 0051 决策 5 与现有 cleanup 顺序，先释放会话再发事件）。预热不在建连重试的 catch 分支里被当作瞬时网络错误重试。设备路径的预热由 B6 的适配器实现，本批只提供 env 与共用的标记、归因常量（0051 决策 13；0052 决策 6（设备侧归 B6））
- `engines/midscene/src/worker/run-scope.mts` · --capabilities 分支：加会话预热支持键（0049；0051 决策 13）
- `core/tests/test_redact.py、engines/novaact/tests/test_redact.py、engines/midscene/src/worker/redact.test.mts` · CASES 用例表：三份同步加规则②的用例（见 guard_tests_first），并加一条差集护栏，保证三份表逐条相同（0035 决策 5「三份共用同一组用例」）
- `docs/adr/0035-local-app-testing-via-tunnel.md 与 docs/adr/0051 决策 13；docs/user-guide/local-app-testing.md、writing-features.md；cli/gherkai_cli/skills/gherkai/references/setup-and-diagnosis.md；runtime/DEVELOPMENT.md、core/DEVELOPMENT.md、CONTRIBUTING.md 里的 basic-auth 描述` · Status 头与描述：0035 Status 头里「按 0051 决策 13 改写的部分尚未实现」一段改为已落地；用户文档换掉 basic-auth 与「凭据内嵌地址」的说法，补上已知边界：Clear-Site-Data、step 代码须经浏览器上下文发请求、cookie 会到达被测应用的访问日志（CLAUDE.md 文档纪律「改完 code 回头校准文档」；0045）

**先写的护栏测试**

- `runtime/tests/test_tunnel.py`：mapped_base 等于干净的 url，不含 @。warmup_url 的形态精确等于 https://<host>/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=<T>。两次 start 的 T 与 C 都不同，且各自至少 128 位（按字符集与长度推算）。替换掉现有 test_mapped_base_embeds_credentials，以及断言 basic-auth 出现在策略里的那条（0035 决策 1；0051 决策 13）
- `runtime/tests/test_tunnel.py`：生成的策略 YAML（解析后，或做结构化断言）：恰 4 条规则（不超过 5）；不含 basic-auth 与 remove-headers；Set-Cookie 精确等于 `__Host-gherkai_tunnel=C; Secure; HttpOnly; Path=/; SameSite=None`（无 Domain、无 Max-Age）；预热响应带 Cache-Control: no-store 与 Referrer-Policy: no-referrer；四个页面标记字面量 READY、DENIED、ERROR、AUTH REQUIRED 都在；策略文件权限是 0600（0051 决策 13 边缘策略）
- `runtime/tests/test_tunnel.py`：map_origin_in_jobs 的边界用例照 ADR 原文逐条钉住：`http://localhost:3000.evil/` 与 `http://localhost:30001/x` 不命中，`xhttp://localhost:3000` 不命中；`next=http://localhost:3000/x`、`去 http://localhost:3000。`、`Go to http://localhost:3000.`、`(see http://localhost:3000)`、`打开http://localhost:3000/a页面` 命中；同一段文本多处命中都替换；DocString 与每个单元格各自独立判定（0035 决策 2）
- `core/tests/test_redact.py（另两份同文）`：`?gherkai_tunnel_token=abc` 与 `&gherkai_tunnel_token=abc` 换成 `***`；S3 预签名地址的签名类参数（如 X-Amz-Signature、X-Amz-Credential、X-Amz-Security-Token，具体清单待 open_questions 第 2 条定）的值被盖住，其余参数保留；`&amp;X-Amz-Signature=…` 的 XML 转义形态被盖住；已序列化的 JSON 行脱敏后仍可解析，且匹配不跨越引号；值内的 URL 编码字符（%2F 等）被完整盖住、不留尾巴；与规则①叠加时两条都生效（0035 决策 5 规则②；0051 决策 11）
- `core/tests/test_redact_parity.py（新）`：差集护栏：读出另两份测试文件（engines/novaact/tests/test_redact.py、engines/midscene/src/worker/redact.test.mts）里的用例表，与 core 的 CASES 逐条集合相等；或者把用例搬进一个共享的 JSON fixture，三端都从它读。任何一份漏改都直接红（0035 决策 5「三份共用同一组用例」）
- `runtime/tests/test_compose.py（或现有 compose 测试文件）`：_COMPOSE_OWNED_WORKER_ENV 含 GHERKAI_SESSION_WARMUP_URL；宿主 os.environ 带这个键而入参为 None 时，两个引擎的注入 env 都没有它；入参有值时两个引擎都注入；build_fargate_engines 有值时进入 RunTask overrides 的 env，无值时不出现该键（0037 决策 4）
- `core/tests/test_serialize.py`：RunMeta 的预热地址无值时省键、有值时往返恒等；旧落盘缺键读作 None（0051 决策 13（无值省键））
- `engines/novaact/tests/test_run_scope*.py 与 engines/midscene/src/worker/run-scope*.test.mts`：终结判定：①有 GHERKAI_EXTRA_HTTP_HEADERS 而没有预热地址时，事件序列恰为一条 scope_done{status:error, errorType:precheck_failed}，没有 scope_started，没有任何 scenario 事件；②标记 DENIED 或 401 的 AUTH REQUIRED 时，结果是 precheck_failed；③ERROR 或一直没有标记直到重试用尽时，结果是 engine_error，退出码不是 EX_WORKER_NETWORK（80），即便导航抛出 Playwright 网络类异常也一样；④READY 时，预热导航恰好发生一次且在 scope_started 之前，多个 scenario 不重做；⑤两个 env 都没有时，事件序列与现状一致；⑥capabilities 输出含预热支持键且为 true（0051 决策 13、决策 4；0028 分类红线）
- `cli/tests/test_tunnel_cli.py`：改写现有用例：run_meta.json 含 warmup_url（含令牌），但 step 文本只含干净的隧道地址；jobs/*.json 与 tunnel.json 不含令牌；run --json 的输出里 gherkai_tunnel_token 的值是 ***，落盘的 run_meta 保留明文；本机后端在 --expose-local 下遇到不声明预热支持的 worker，以退出码 2 拒绝，且隧道没有起（make_tunnel 未被调用）；进度输出不再出现 basic-auth（0035 决策 5；0051 决策 13「能力与拒绝点」）

**完整性审查补认领**

- 红线测试补：把已实测的边缘鉴权矩阵固化为测试——正确 cookie 也不能绕过错误令牌或 POST 预热，业务路径只带令牌不放行，多个同名 cookie 的处置，.well-known 请求不到达上游；只断言策略文件的形状不够。
- 脱敏规则 ② 的封闭名单与规则 ③ 的 Appium 端点路径令牌（本轮补进 0035 决策 5），三份实现共用用例，含一条按实测结构构造的端点地址。
- 真跑核对：预热的三个失败分支（边缘拒收 cookie、校验返回 401、请求失败）各实际触发一次。0052 决策 8。

**真跑或对抗核查才算数的结论**

- 代码生成的流量策略（而不是 spike 里手写的那份）要在真实 ngrok 免费层账号上被接受，并逐条重放 0051 实测表「边缘契约」的 16 项 curl 用例：无 cookie 401、错令牌 401、预热路径 POST 401、正确令牌 200 且带 Set-Cookie 与 no-store、校验路径凭 cookie 才 200、多值同名 cookie 其一正确即 200、同名查询参数原样转发、上游日志里没有 .well-known 请求。单测只能断言 YAML 的形状，证明不了 ngrok 的 CEL 求值语义
- Nova Act 真实会话（AgentCore aws.browser.v1）上的桌面预热：SDK 自注册的 context.route("**") 做 SSL 校验时，若用 route.fetch / fulfill 中转响应，自定义响应里的 Set-Cookie 是否仍然写进浏览器 cookie 库、后续业务请求是否带上。spike 的桌面 Chromium 结论不一定覆盖 Nova 的 route 中转；同时要核实预热导航发生在 nova.page 上时 READY 标记读得到
- Midscene 桌面 worker 在 AgentCore 浏览器上的预热：确认 READY，业务页 200 且 cookie 到达上游，被测应用用 history.pushState 不再抛 SecurityError；故意给错令牌，核对 AUTH REQUIRED 归 precheck_failed，且 run 的最终退出码与 explain 呈现符合预期
- 三种宿主下预热地址都能端到端到达 worker：同步 run、本机 submit 的 per-run 进程与 status --wait 接力者、云端 submit 的 reconciler 到 RunTask containerOverrides 到容器 env。可用 tools/e2e_harness.py 打通真实边界；顺带确认宿主 shell 里 export 的同名值不会越过 definition
- 开发版本混搭的完整性不变量：用不传预热地址的旧 reconciler 与新 worker 组合，确认 worker 发出 precheck_failed，而不是在 401 页上把导航和地址断言判成通过
- 预热导航遇到真实网络失败（拆掉隧道或断网后再预热）：确认归 engine_error，不进入 0028 的建连重试，也不以退出码 80 退出。这依赖 Playwright 与 Nova 真实抛出的异常类型，mock 构造的异常证明不了
- 0035 决策 5 待实施期核实的一项：云端 RunTask 的 containerOverrides 带着预热地址，CloudTrail 的 RunTask 事件是否记录 overrides 里的 env 值；task 停止后约 1 小时内经 ecs:DescribeTasks 读到它的实际窗口
- 策略文件不删除的前提仍需真实核实：ngrok agent 在隧道存活期是否会重读策略文件（现有代码注释已点明，只靠单测证明不了）

**易错点**

最容易做错的有两件。（1）预热放进现有的建连重试域。两个 worker 在 scope_started 之前的整段都被 0028 的瞬时网络判定包着（Nova 的 _run_session 外层循环、Midscene 的 connect 循环 catch）。直接把 goto(warmup) 插在 scope_started 前面，预热的网络失败就会被重建会话重试，最后以退出码 80 落成 network_error，正好踩到 0051 决策 13 与 0028 的分类红线；单测用 mock 异常很容易测绿，必须用真实拆隧道的方式核对。（2）漏掉某个宿主或出口。预热地址要走完 RunMeta、serialize、三个宿主（sync run、detached.py、reconciler.py）和 build_engines / build_fargate_engines 两个装配点，还要进 _COMPOSE_OWNED_WORKER_ENV 的抹除清单；漏掉任何一处，worker 就会在对应宿主下触发完整性不变量的 precheck_failed，或者被宿主 shell 里的同名值污染。脱敏规则②要三份逐字同步，靠差集护栏而不是靠人读。另外，隧道模式下即使只有设备目标，definition 也要恒带额外请求头：0035 决策 4 说请求头「仅桌面浏览器」注入，指的是 worker 的注入动作，不是 definition 可以省掉它，否则完整性判据在设备上失效。现有测试里的 auth=\"u1:p1\" 固定数据与「u1:p1@」断言，需要整组改写为令牌形态。主要文件：/Users/lzy/workspace/yaozhou/runtime/gherkai_runtime/tunnel.py、/Users/lzy/workspace/yaozhou/runtime/gherkai_runtime/tunnel_host.py、/Users/lzy/workspace/yaozhou/runtime/gherkai_runtime/compose.py、/Users/lzy/workspace/yaozhou/engines/novaact/gherkai_worker_novaact/run_scope.py、/Users/lzy/workspace/yaozhou/engines/midscene/src/worker/run-scope.mts、三份 redact 实现。


## 7. B8-deploy-iac：部署侧：权限、Device Farm 项目找回或建立、SSM、doctor 设备项

规模 M。


**依赖**

- B3-config-submit：提交侧从 SSM（names.DEVICE_FARM_PROJECT_KEY）读项目 ARN，写进 device_request.project_arn，缺值时以退出码 2 结束并提示「部署未启用设备支持」；方向上是 B3 消费 B8 的命名常量。doctor 在本机后端时要取项目 ARN，依赖 B3 的 gherkai.toml / GHERKAI_DEVICE_FARM_PROJECT_ARN 解析结果（0053）
- B1-capabilities：doctor 目标清单这一行要用 query_capabilities 返回的 targets / max_session_s（已校验形态）
- B6-midscene-device：不是接口依赖，而是端到端验收依赖。task role 授权是否够，要等 worker 的设备模块（列举、建会话、查询、停止、按名列举，以及应用存在性检查）真跑过才能确认

**改动面**

- `runtime/gherkai_runtime/names.py` · 模块级常量（与 SUBNETS_KEY / VPC_KEY 并列）：新增 Device Farm 命名单点：项目基名 BASE_DEVICE_FARM_PROJECT="devices"（项目名 default_name(prefix, 它) 即 `{prefix}devices`）、SSM 相对键 DEVICE_FARM_PROJECT_KEY（如 "device-farm-project"，全路径经 ssm_path）、固定区域常量 DEVICE_FARM_REGION="us-west-2"、「待建立」占位值常量，以及纯函数 device_farm_project_id(arn) 和 device_farm_session_arn_prefix(project_arn)（得到 arn:aws:devicefarm:us-west-2:<账户>:session:<项目 id>/*）。stack、provider、doctor、提交侧都只引用这些常量，调用点不写裸字面量（与 0038「SSM 参数与命名真源」同一纪律）（0051 决策 10「项目」；0033 资源清单 11.；0038 SSM 命名真源）
- `deploy_aws/gherkai_deploy_aws/names.py` · re-export 列表 + ssm_* 便捷函数：re-export 上面新增的常量与函数；加 ssm_device_farm_project_path(prefix)，形状与 ssm_vpc_path 相同，供 stack 写、provider 读（0051 决策 10；0033 资源清单 11.）
- `runtime/gherkai_runtime/devicefarm.py（新模块）` · 部署与诊断用的 Device Farm 客户端模块（`gherkai-runtime[aws]`，boto3 函数内延迟导入）：Python 侧唯一构造 devicefarm 客户端的地方，客户端恒用 region_name=DEVICE_FARM_REGION，凭证沿用调用方的 profile。提供以下函数：read_project_arn(ssm, prefix)，从后端区域的 SSM 读，ParameterNotFound 时返回 None；resolve_or_create_project(prefix, profile, stored_arn)，SSM 有值时先用 GetProject 核对，再按名翻页 ListProjects，命中多个抛专用异常，零个则 CreateProject；list_open_sessions(project_arn, profile)，翻页 ListRemoteAccessSessions，过滤掉状态为 COMPLETED 的会话，返回 arn、name、status、created，用于 doctor 拼控制台链接和停止命令。不创建也不停止会话。权限错误单独分类成一种异常（AccessDenied），供 deploy 降级（0051 决策 10「调用归属」「项目」；0051 决策 6（doctor 列未完成会话）；0033 部署方 ListProjects/CreateProject 于 *、GetProject 于项目 ARN）
- `deploy_aws/gherkai_deploy_aws/cli.py` · Provider.build_context：context 闭集加 device_farm_project。build_context 保持纯推导：ARN 由调用方先解析好再传入（新增一个关键字参数，或者让 _run_cdk 把解析结果放在 args 的私有属性上），不在 build_context 里做 IO。值为 None 时这个键不进 context，或者给占位常量，两者在 stack 里等价（0037 决策 6 context 闭集加 device_farm_project；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/cli.py` · Provider.deploy（_guard_vpc_spec 之后、_run_cdk 之前新加一步 _resolve_device_farm_project_for_deploy）：放在工具链闸、容器引擎、--vpc、VPC 三态之后，cdk 之前。先读 SSM，再调 runtime.devicefarm.resolve_or_create_project：同名项目命中多个时以退出码 2 结束；遇到 AccessDenied 时，SSM 有 ARN 就沿用并打一条警告，没有就警告后跳过（context 不带 ARN）；其余错误按前置失败处理，以退出码 2 结束。文案按 0039 只说发生了什么、为什么、怎么办，不出现 ADR 编号。解析结果交给 _run_cdk 和 build_context（0051 决策 10「项目」与无权限降级；0033「设备目标增量」部署方行）
- `deploy_aws/gherkai_deploy_aws/cli.py` · Provider.diff / synth_only / destroy（经 _run_cdk）：这三个动作不建立项目：只读 SSM 现值，没有值时传占位值。读 SSM 失败时怎么处理见 open_questions。diff 的 docstring 要写明「待建立」时变更集里看不到 Device Farm 授权（0037 决策 6（diff 不建立、synth-only 与 destroy 取 SSM 现值或占位）；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/cli.py` · 模块头 docstring「Provider 负责」「退出码」两段：职责清单加「deploy 在 cdk 之前找回或建立 Device Farm 项目」；退出码 2 的情形加「同名项目命中多个」（0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · BackendStack.__init__ 新增 _resolve_device_farm_project()：读 try_get_context("device_farm_project")。缺失或等于占位值时 self.device_farm_project_arn=None，不报错（这一点与 _resolve_version 相反，app 不 fail-fast）。非占位的值要过 ARN 形态校验，必须是 arn:aws:devicefarm:us-west-2:<12 位>:project:<id>，不合法即在 synth 期报错，因为拼出错的 session 前缀只会表现为运行期 AccessDenied（0037 决策 6（缺少或占位不 fail-fast）；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · 新增 _ssm_device_farm()（与 _ssm_deployment_stamp 并列）：ARN 不为 None 时写 StringParameter，路径为 ssm_device_farm_project_path(prefix)，作为 stack 资源，随部署事务同生死、随 destroy 删除（项目本身由 SDK 建立、不归 stack 管，所以 destroy 不删项目）；ARN 为 None 时不建这个参数（0033 资源清单 11.；0051 决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · _grant_task_role 的 elif engine == "midscene" 分支：只在 ARN 不为 None 时，给 Midscene task role 加以下几条 statement，区域段一律写字面量 us-west-2，不用 self.region。① devicefarm:ListDevices，资源 *，单独一条 statement。② GetDevice，资源 arn:aws:devicefarm:us-west-2::device:*。③ CreateRemoteAccessSession，同一条 statement 里列项目 ARN 和 device:*。④ Get/StopRemoteAccessSession，同一条里列 session:<项目 id>/* 和项目 ARN，两种都要。⑤ ListRemoteAccessSessions，资源为项目 ARN。⑥ s3:ListBucket，资源为桶 ARN，条件按 spike 实测形态写 StringLike s3:prefix ["apps/*"]。现有两个引擎共享的 GetObject（资源 {bucket}/*）已经覆盖 apps/*，不必重复授。Nova 的 role 不加任何 devicefarm 动作，也不加 ListBucket（0033 task role 表 devicefarm / apps 行；0051 决策 9（ListBucket 把 403 变 404）、决策 10）
- `deploy_aws/gherkai_deploy_aws/stack.py` · _storage 的 ArtifactsBucket lifecycle_rules：加规则 expire-apps：tag_filters {"gherkai": "app"}，expiration 14 天（E=14）。与现有 expire-job-in 并列，规则 id 用常量（0051 决策 9 保留承诺（E=14 天））
- `deploy_aws/gherkai_deploy_aws/stack.py / app.py` · 模块头 docstring（资源清单、context 配置项）：stack 头的 SSM 部署戳清单加 device-farm-project；app 头的 context 清单加 device_farm_project（由命令派生，可缺省）（0037 决策 6）
- `cli/gherkai_cli/__main__.py` · _doctor_cloud 末尾，新增 _doctor_devices(target, add)：读 SSM 的项目 ARN：没有值时加一行「部署未启用设备支持」，required=False。有值时调 runtime.devicefarm.list_open_sessions，列出未到 COMPLETED 的会话（含排队中），每条附控制台链接和 `aws devicefarm stop-remote-access-session --region us-west-2 --arn …` 停止命令；没有权限时单独一行说明。runtime.devicefarm 在函数内导入，CLI --help 不拉 boto3（0051 决策 6 泄漏护栏（doctor 列出）；0033 CLI 的 ListRemoteAccessSessions）
- `cli/gherkai_cli/__main__.py` · _cmd_doctor 的 engines 段（模型行旁边）：每个可用引擎加一行 targets.<engine>，required=False，纯展示：列交集前的目标清单，带 max_session_s 的目标附分钟数，不展示 requires；数据与模型行取自同一次 query_capabilities。如果 B1 已经承担这一行，这项移交 B1（0049 决策 6 doctor）
- `cli/gherkai_cli/deploy.py` · destroy 子命令的 description（约第 169 行）：保留清单加 Device Farm 项目（含会话记录与录像），并给出手动删除命令（0033 RETAIN 段；0051 决策 10）
- `docs/user-guide/cloud-backend.md + docs/adr/0038（SSM 命名真源常量清单）` · 「拆除与清理」节；0038「键名常量」枚举：拆除手册加 `aws devicefarm delete-project --region us-west-2 --arn <项目 ARN>`；0038 常量清单补上 DEVICE_FARM_PROJECT_KEY（按差集对照 names.py），SSM 参数族表加一行，写者为 stack 资源（0033 RETAIN 段；0038 SSM 命名真源；CLAUDE.md 文档校准）

**先写的护栏测试**

- `deploy_aws/tests/test_stack.py`：SSM 参数全集按 context 分两种情形锁定：不带 device_farm_project 或带占位值时，仍是现有 6 条（改写 test_ssm_parameter_set_is_exactly_six）；带合法 ARN 时恰为 7 条，多出的那条值等于传入的 ARN（0033 资源清单 11.；0037 决策 6）
- `deploy_aws/tests/test_stack.py`：带 ARN 合成时 Midscene task role 的权限：ListDevices 只出现在资源为 "*" 的 statement；Get/StopRemoteAccessSession 所在 statement 的 Resource 同时含 session:<id>/* 和项目 ARN（缺一种即失败，这是模拟器假阳性留下的护栏）；CreateRemoteAccessSession 同时含项目 ARN 和 device:*；GetDevice 的设备 ARN 账户段为空；所有 devicefarm ARN 的区域段都是 us-west-2，夹具的 REGION=us-east-1 正好用来反证没有误用 self.region；ListBucket 带 StringLike s3:prefix apps/*（0033 task role 表 devicefarm / apps 行；0051 决策 10）
- `deploy_aws/tests/test_stack.py`：两个引擎的 role 分开：Nova task role 的策略里没有任何 devicefarm: 动作，也没有 s3:ListBucket；不带 ARN 合成时整个模板没有任何 devicefarm: 动作。在 test_task_role_resource_arns_narrowed 里补一条：只能用 * 的动作恰好是 AgentCore 4 个加 ListDevices，对应 0033 写的「这 5 个」（0033「两个引擎 task role 分立」「风险收在两道」）
- `deploy_aws/tests/test_stack.py`：非占位但形态不合法的 device_farm_project（区域不对、不是 project 资源）在 synth 期抛 ValueError；缺失或占位不抛（0037 决策 6（缺少或占位不 fail-fast））
- `deploy_aws/tests/test_stack.py`：产物桶 lifecycle 规则恰为 expire-job-in 和 expire-apps 两条，后者 TagFilters 为 gherkai=app、过期 14 天（0051 决策 9）
- `deploy_aws/tests/test_provider.py`：context 闭集差集护栏：build_context 可能产出的键集合，等于 stack.py/app.py 源码里所有 try_get_context("…") 字面量的集合，即 {prefix, version, vpc_id, use_default_vpc, stop_timeout, device_farm_project}，并断言 device_farm_project 不是任何 argparse flag（0037 决策 6 flag 面与 context 对齐、闭集）
- `deploy_aws/tests/test_provider.py`：deploy 编排顺序与分支（用 stub 掉的 devicefarm 模块）：VPC 三态拦下时零次 devicefarm 调用；同名项目命中多个时以退出码 2 结束且不调 cdk；AccessDenied 且 SSM 有值时 cdk argv 带该 ARN 并打警告；AccessDenied 且 SSM 无值时 argv 不带 device_farm_project（或带占位）且打警告；diff、synth、destroy 永不调用 CreateProject。现有 cdk 夹具要同时把 devicefarm 和 SSM 读 stub 掉，否则现有测试会直连真 AWS（0051 决策 10「项目」与降级）
- `runtime/tests（或 cli/tests）新增 test_devicefarm_client_placement.py`：差集护栏：Python 源码里 client("devicefarm" 只出现在 runtime/gherkai_runtime/devicefarm.py；core/ 零引用；推进器 Lambda 源零引用；构造客户端时的 region 引用 names.DEVICE_FARM_REGION（0051 决策 10「调用归属」护栏测试）
- `runtime/tests 新增 test_devicefarm.py（botocore Stubber 或 moto）`：resolve_or_create_project 的情形：SSM 有值且 GetProject 成功时直接用，不 List；按名翻页（带 nextToken）时零个就 Create、一个就复用、多个抛异常；list_open_sessions 过滤掉 COMPLETED、保留 PENDING 等排队态；构造的客户端区域恒为 us-west-2，与传入的后端区域无关（0051 决策 10；0051 决策 6）
- `cli/tests/test_doctor*.py`：SSM 无项目 ARN 时出一行「未启用设备支持」，required=False，退出码不变；有未完成会话时 detail 含会话 ARN、us-west-2 停止命令和控制台链接；文本过 test_user_facing_messages 的内部指代护栏（0051 决策 6；ADR 0039）

**完整性审查补认领**

- 红线测试补：SSM 参数缺失与无凭证、拒绝、网络、限流分开处置；只有完全无凭证的 --synth-only 可占位并警告；旧 ARN NotFound 后零、一、多个命中三种结果；无凭证且无 region 时仍能离线导出。
- 护栏测试：Device Farm 客户端在 Python 侧只在 runtime 的设备模块构造，core 不引用它（TS 侧的同类断言归 B6）。0051 决策 10。
- SSM 值失效时 deploy 的 GetProject 核对、diff / --synth-only / destroy 的读失败处置（本轮补进 0051 决策 10 与 0037 决策 6）。

**真跑或对抗核查才算数的结论**

- 真部署后，用 Midscene task role 的真实凭证（在容器内，或按同一份 CDK 产出的策略 assume）把 worker 的全部设备动作正反面走一遍。0033 明写「尚未经真部署后的 task role 端到端验证」；CDK 会合并或改写 statement、拼 Fn::Join，合成出的策略不等于 spike 手写的 JSON，单测只能比对形态
- 会话 Get/Stop 的两种资源同授要在真 task 上再确认一次（ECS task role 的调用者身份由 ECS 签发，不经探针的 AssumeRole）：同授放行、只授一种被拒。探针验证时 assume 之后先核对调用者身份，会话名至少两个字符
- CDK 生成的 ListBucket 条件（StringLike s3:prefix apps/*）下，缺失键的 HeadObject 回 404、无权限回 403，在部署后的真实桶上复核
- deploy 的项目生命周期跑一整轮真账户：首次部署建立项目，再次部署经 SSM 复用，destroy 后项目还在、SSM 参数被删，同 prefix 重新部署时按名找回同一个项目；后端在 us-east-1 时，Device Farm 调用落在 us-west-2、SSM 落在后端区域
- 部署方没有 Device Farm 权限时，真实报错码的形态（AccessDeniedException 还是别的），决定降级分类写得对不对；mock 给不出真实错误码
- doctor 对真实排队中或运行中的会话：ListRemoteAccessSessions 返回的状态取值，以及控制台链接格式（会话 ARN 到控制台 URL 的拼法）实际能打开
- 按标签 gherkai=app 的 14 天过期规则，CopyObject 同键刷新之后是否按新的创建时间重新计时（0051 决策 9 明写「实施期核对」）
- 只授本项目时，访问别的项目的会话被拒，在部署后的 role 上反证

**易错点**

最容易做错的有三件。

① Get/StopRemoteAccessSession 必须在同一条 statement 里同时列会话前缀和项目 ARN，所有 devicefarm ARN 的区域段都要写死 us-west-2，不能沿用 _grant_task_role 现有的 `region = self.region` 习惯。测试夹具 REGION=us-east-1，护栏测试正好用它反证；资源少一种、或区域跟着 self.region 走，模拟器会判允许，真实角色却被拒。

② build_context 要保持纯推导，项目的找回或建立放在 deploy 里 VPC 三态之后、cdk 之前，而且只有 deploy 走这一步，diff、synth、destroy 绝不能调 CreateProject。现有 test_provider 的 cdk 夹具只 stub 了 subprocess 和四步，加入 Device Farm 和 SSM 读之后必须一并 stub，否则现有测试会直连真 AWS，这条在仓库里踩过一次。runtime.devicefarm 必须在函数内导入，否则会破坏「--help 不拉 boto3/aws_cdk」的护栏测试。

另外，无权限降级只针对 AccessDenied，限流、网络等其他错误不能悄悄跳过，否则一次偶发错误就会让 stack 删掉 Midscene 的 Device Farm 授权，而且只有设备 run 运行时才会暴露。


## 8. B6-midscene-device：Midscene worker 设备模块（接缝、命令守卫、能力探测、适配器、终结四阶段、evidence）

规模 L。


**依赖**

- B1-capabilities：--capabilities 输出 targets 与 max_session_s、会话预热支持键，以及建会话前的 targets 自检函数（B6 提供 device/limits 的常量，B1 消费；自检失败时调用 B6 新增的 scope_done{status:error} 出口）
- B2-core-target-job：Job 的 target{device, ui_kind, app{alias,bucket,key,sha256,app_id}}、device_request{provider, device_arn|os_version, billing_method, project_arn, acquire_timeout_s}、timeoutS 的线上形态，以及 Python 到 TS 的字段往返 fixture
- B4-steps-registry：webdriver 句柄种类、uiKinds 与 devices 过滤、requires 封闭集，以及按 (device, ui_kind) 匹配并返回条目及其 requires 的 match API；B6 构造它定义的 ctx 七字段
- B5-core-events-termination：core 认 session_opened、session_closed、ScopeDone 的 status/errorType/message 三个新字段，新错误类别（precheck_failed、acquire_timeout、session_lost、capability_unavailable、release_failed），新配对规则与合成 SKIPPED；B6 发事件的形状以 B5 的 wire.py 为准
- B7-tunnel：env GHERKAI_SESSION_WARMUP_URL 的注入、预热页的标记字符串、令牌参数名 gherkai_tunnel_token，以及三份脱敏实现共用的规则与用例（签名类参数集合）
- B8-deploy-iac：真跑依赖 task role 的 Device Farm 权限、应用前缀的 s3:ListBucket（使缺失返回 404）、project ARN 写进 SSM
- B3-config-submit：只在端到端真跑应用目标时需要，即 CLI 把应用上传到 apps/<sha256>/ 并填 device_request

**改动面**

- `engines/midscene/package.json（及 package-lock.json）` · dependencies / devDependencies：webdriverio 与 @aws-sdk/client-device-farm 从 devDependencies 移到 dependencies（现状两者只在 devDependencies，供 spike 用）；新增 @midscene/core 显式依赖，版本锁定为 1.15.1，与 @midscene/web 同版本。锁文件按 DEVELOPMENT 的规定用 npm 10 重算（npx npm@10 install --package-lock-only）（0052 决策 7（依赖）、决策 3（动态加载的前提））
- `engines/midscene/src/device/limits.mts（新，轻量、不 import 任何 SDK）` · 设备预算常量：放终结四阶段常量（等在途 Create 10s、终结核对 5s、释放 25s、Stop 3s、终结期 Get 5s）、Device Farm 单次调用超时（Create/Get/List 10s）、获取预算缺省 600s、上界 3600s、换台下限 150s、会话上限 150min 与由它推出的 max_session_s、newSession 下限（4min+65s）、pageLoad 150s、执行期请求超时、探测短预算 5s。--capabilities 与 minGraceSeconds 只 import 这个文件，保证不加载 webdriverio 与 Device Farm SDK（0052 决策 6 分层表、0051 决策 2、5，0049 决策 4、5）
- `engines/midscene/src/worker/run-scope.mts` · main()：把建连、Agent、清理收成界面接缝（新的 TargetSurface 接口）：现有 connect()、stopSession()、cleanupRun()、makeGuardedCleanup 包装、BedrockAgentCoreClient 和 chromium.connectOverCDP 原样搬进桌面实现（如 worker/surface-desktop.mts），行为不变。接缝提供五个操作（取 agent、取确定性句柄、导航或启动应用、释放、预热）和三项 step 边界义务（step 前核对、step 后复原并核对、采集界面快照）。scope 开头按 job.target.device 选一次实现；设备实现用 `await import("../device/surface.mjs")` 动态加载。主流程里不写任何按设备的条件分支（0052 决策 2、3）
- `engines/midscene/src/worker/run-scope.mts` · interface Job（同步 lib/job-source.mts 的 Job）：加 target{device, ui_kind, app?{alias,bucket,key,sha256,app_id}}、device_request{provider, device_arn|os_version, billing_method, project_arn, acquire_timeout_s}、可选 timeoutS。两处重复的 Job 类型合成一份（也可以从共享类型文件 import）（0048 决策（Job 携带目标）、0051 决策 2）
- `engines/midscene/src/worker/run-scope.mts` · main()：执行前失败的出口（新）：现状：建连阶段的异常一律 throw，由 bin 打 fatal 后退出码 1，网络重试耗尽时退出码 80。新增 scope 级失败出口：发 scope_done{status:'error', errorType, message}，不发 scope_started，不发任何 scenario 或 step 事件，会话确认释放后以 0 退出。它覆盖这几种失败：自检不通过、收到额外请求头却没有 GHERKAI_SESSION_WARMUP_URL（桌面同样适用）、设备解析零候选、应用对象 404 或 403、启动即自退、获取超时、隧道预热被拒或无法确认。之前允许出现的只有 session_opened 与 session_closed。设备路径不使用 EX_WORKER_NETWORK（80）；桌面建连重试与 80 照旧（0051 决策 4、5（退出码）、13（完整性不变量），0049 决策 7）
- `engines/midscene/src/worker/run-scope.mts` · runScenario / runStep 的签名与 step 内顺序：参数 (agent: PlaywrightAgent, page) 改为接缝对象。runStep 按 7 步固定顺序执行：①step_started；②surface.preStep()，失败记 engine_error、不调 handler 也不调 AI；③执行（确定性 handler 拿 surface 给的句柄，现状写死的 `hit.handler({ page }, groups)` 改掉；URL_IN_QUOTES 导航改成 surface.navigate，不再直接 page.goto）；④按条件读地址；⑤surface.restore()，失败时判定改为 error，原判定写进 message；⑥只在 failed 或 error 时采控件摘要；⑦产 evidence、发 step_done，然后把截图与原始树入队。桌面实现的三项义务都是空操作，只有快照在 AI step 上取 page.url()。所有 step 的 step_kind 取 ai / deterministic / navigation 之一。确定性 handler 声明了 requires:['web_context'] 而探测结论为「不提供」或「探测出错」时，不调 handler，分别记 capability_unavailable 和 engine_error（0052 决策 2、5（后果段）、6（固定规则），0050 决策 2，0051 决策 8）
- `engines/midscene/src/worker/run-scope.mts` · main() 的 scenario 循环：加 scope 级终止状态：发生 session_lost（按会话状态判定或按年龄到期）时，序列为当前 step 记 error、本 scenario 余下 step 发 step_skipped、发 scenario_done{error}，后续 scenario 一律不发事件，最后发 scope_done{status:error, errorType:session_lost}。结果未知之后，下一条 scenario 开始前（scenario_started 之前）做一次截图存活探测，失败就发 scope_done{status:error, errorType:engine_error}。现状循环会无条件跑完全部 scenario（0051 决策 4、5（会话丢失序列），0052 决策 6（结果未知））
- `engines/midscene/src/worker/run-scope.mts` · agentOpts / cumulativeTokens / stepCost：类型从 PlaywrightAgent 放宽到 @midscene/core 的 Agent。agentOpts 拆成两份：forceChromeSelectRendering 只给桌面；设备 Agent 的重规划上限缺省 12，可按 0044 决策 2 的 worker 侧 env 覆盖，桌面行为不变。generateReport 和 persistExecutionDump 两端同真同假的约束保留（0052 决策 6（⑨ 重规划）、决策 7（复用 Agent），0044 决策 2）
- `engines/midscene/src/worker/run-scope.mts` · minGraceSeconds / shutdownSequence / onSignal / 进程级兜底：minGraceSeconds 改为由 device/limits 的四段常量和 UPLOAD_TIMEOUT_MS、QUEUE_DRAIN_EXIT_MS、MIN_GRACE_MARGIN_MS 一起推出，结果约 64s（口径见 open_questions）。设备路径的 SIGTERM 收尾换成终结四阶段：置 act 的 abortSignal 并撤销执行令牌、等在途 Create、终结核对、并行释放、发 session_closed、兜底上传与排空；SIGTERM 路径不调 deleteSession；终结只进入一次。新增 unhandledRejection 与 uncaughtException 处理器，记录后进入终结。正常收尾的顺序为：agent.destroy → 报告上传 → deleteSession（5s） → 终结核对 → 释放 → session_closed → scope_done（reportRefs 带 kind:'device_session' 的 device-session.json） → 排空（0051 决策 5，0049 决策 5）
- `engines/midscene/src/worker/run-scope.mts` · log()：现状 log() 直接写 stderr、不脱敏，而 WebdriverIO 的 UND_ERR_CLOSED 会把带签名的端点地址写进错误文本。改为输出前一律经脱敏出口。bin.mts 的 `worker fatal:` 输出同样处理（0051 决策 11）
- `engines/midscene/src/lib/redact.mts` · redactUrlUserinfo（新增规则 ②，建议改名为统一的脱敏出口）：保留 userinfo 规则，新增一条：签名类查询参数与 gherkai_tunnel_token 的值替换成 ***，覆盖 `&` 与 `&amp;` 两种分隔形态。与 core redact.py、Nova lib/redact.py 共用同一组用例。调用点 event-sink.emit、evidence.writeEvidence、error-text.oneLineError、log、device-session.json、page_source 写盘全部改调新出口（0051 决策 11，0035 决策 5）
- `engines/midscene/src/worker/evidence.mts` · StepEvidenceInput / BuildEvidenceInput / EvidenceDoc / stepEvidenceRef：输入里的 `page: {url()}` 换成界面快照 `snapshot{url, url_missing, controls?, controls_missing?, page_source_path?, page_source_truncated?, step_kind?}`，模块保持纯映射、不发 WebDriver 命令。EvidenceDoc 只在设备目标上加 step_kind、顶层 url/url_missing、controls/controls_missing、page_source/page_source_truncated，桌面输出不变。stepEvidenceRef 的跳过规则（无 execution 且无 prompt 就返回 null）加一个设备例外：确定性与导航 step 在 failed 或 error 时也产 evidence，此时 acts 为 []。page_source 文件的 URI 用 refFor 算，字节进 screenshots 回传列表、走后台队列。写盘改用新的脱敏出口（0051 决策 8，0052 决策 7（evidence 输入），0042 决策一）
- `engines/midscene/src/worker/error-text.mts` · oneLineError：redactUrlUserinfo 换成新的脱敏出口，顺序保持「先脱敏再截断」（截断可能切在查询参数中间）（0051 决策 11）
- `engines/midscene/src/lib/artifact-upload.mts` · ArtifactUploader（基本不改）：page_source 文件复用 refFor 加 enqueue，device-session.json 复用 toReportRef。不新增上传时机，只核对 page_source 进入整目录 flush 的根（0051 决策 8）
- `engines/midscene/src/device/session.mts（新）` · Device Farm 会话：执行期唯一构造 DeviceFarmClient 的地方：region 固定 us-west-2，maxAttempts=1，每次调用显式 abortSignal 超时。负责设备列举（完整分页、静态过滤、版本族按点分段匹配、排除 BUSY 与 TEMPORARY_NOT_AVAILABLE、排序）、Create、Get、Stop、按名 List（带 nextToken）。获取预算内手写退避，停止信号可穿透。维护待清理集与待核尝试；只有按名列举命中才能消除待核。Stop 规则只有一条：仍是 RUNNING 才发 Stop，确认只认 STOPPING 或 COMPLETED，Stop 报错就补查一次 Get。发 session_opened 与 session_closed，带 observedS 和 providerMinutes。会话年龄到达 max_session_s 时触发后备路径。可复用 spike 里的 startSession、stopSession、releaseProbe 原语，但要去掉其中的 15 分钟和 5 分钟轮询字面量（0052 决策 3，0051 决策 2、3、4、5、7、10）
- `engines/midscene/src/device/session-name.mts（新）` · 会话名编解码：格式 `gherkai:<run_id>:<sha256(scope_id) 前 16 位十六进制>:<尝试序号>:<scope_id 百分号编码>`。总长上限 256，超长只截最后一段；按整名相等匹配（0051 决策 3）
- `engines/midscene/src/device/appium.mts（新）` · Appium 建连与上下文切换：建连、执行、探测各用一个 WebdriverIO 实例，超时分别设置：建连实例的 newSession 超时不小于 4min+65s、以剩余获取预算封顶、传输层 0 次重试；执行实例 connectionRetryCount=0；探测实例自带 5s 短超时。logLevel 固定为 error。caps 显式设 newCommandTimeout、appium:autoLaunch:false，应用目标设 appium:app 为预签名地址。网页上下文每次重新定位：只认 WEBVIEW_<pid> 与 CHROMIUM，单候选才采用，多候选或零候选按决策 5 处置。提供 withWebContext 和读当前上下文。newSession 的瞬时失败只重试 newSession；拒装驱动辅助包时换一台重建，至多一次（0052 决策 3、5、6，0051 决策 3、9）
- `engines/midscene/src/device/guard.mts（新）` · 命令守卫：会话级的 driver 代理（Proxy），交给 Midscene 界面、内建导航与确定性 handler 的都是它，不暴露裸客户端。维护执行令牌：step 开始时发出，step 结束、取消或进入终结时立即撤销。维护结果未知标志：置位后本 step 内一切有副作用的命令被拒绝，只读白名单放行。白名单按原语列（截图、上下文列表、page source、已确认网页上下文中的读地址、/status、deviceScreenInfo），只对网络错误码与 502、503、504 重试 1 次。结果未知时置标志、abort 当前 act，再查一次会话状态：非 RUNNING 归 session_lost，RUNNING 归 engine_error 并使用 ADR 规定的消息。元素句柄、解构出的方法、晚到的回调同样受令牌约束（0052 决策 6（命令守卫、结果未知、执行期关闭重试），0051 决策 12，0050 决策 2）
- `engines/midscene/src/device/probe.mts（新）` · 能力探测：建连后、预热前执行一次。网页上下文（只对网页目标）判为三类：提供、不提供、探测出错。判据是在 5s 预算内经独立探测实例成功执行一条只读命令，有界重试一次，按证据性质归类。spike 里的 usableWebCtx 用 Promise.race，这正是 ADR 拒绝的方案，不能照搬。另外取 iOS 输入路线、坐标比例（iOS 读 deviceScreenInfo.scale，失败时按截图长边除以窗口长边取整回退；Android 为 1）、/status 的 Appium 版本、候选数。只缓存结论，不缓存句柄；结论写进 device-session.json 与 worker 日志（0052 决策 5、7（DPR 回退规则自写））
- `engines/midscene/src/device/adapters/uiautomator2.mts 与 xcuitest.mts（新）` · 驱动适配器：按会话回报的 automationName 选一次。原语映射照 0052 决策 4 的表：点击、长按、滚动用 mobile: swipe 与 scrollGesture，不用 W3C 指针拖动；输入在 Android 用 mobile: type，iOS 对活动元素 sendKeys，所在上下文由探测定，不用 POST /keys；按键与主屏；iOS 坐标按点（像素除以比例）；导航按探测结论走 url 或 mobile: deepLink。从控件树抽取控件摘要 items[{type,id,text,a11y_id}]、total、truncated，只在 failed 或 error 时调用。`mobile:` 命令不得出现在这两个文件之外。spike 里 AppiumInterface 的 typingRoutes 多路线试错与 swipe 回落都不能保留（ADR 拒绝运行期试错回落）（0052 决策 1、4、6）
- `engines/midscene/src/device/interface.mts（新）` · 界面实现：AppiumInterface extends AbstractInterface：实现截图（原生上下文）、尺寸、defineActionsFromInputPrimitives 动作集，原语全部经适配器与守卫下发。系统版本与机型只经唯一的会话能力读取点进入诊断。spike 里的 class AppiumInterface 是原型，要去掉其中的 PLATFORM、SCENARIO 全局分支（0052 决策 3、7）
- `engines/midscene/src/device/app.mts（新）` · 应用启停：建会话前对应用键做存在性检查，404 与 403 都记 precheck_failed，消息不同；对键预签名。建好后 activateApp 并采样应用状态，回到「未运行」即 precheck_failed。为句柄上下文的 `app.restart()` 提供 terminate、activate、采样三个原语，采样到自退记 engine_error（0052 决策 3，0051 决策 9、14）
- `engines/midscene/src/device/warmup.mts（新）与桌面实现中的预热` · 隧道预热：设备上按探测结论选 url 或 deepLink，导航 GHERKAI_SESSION_WARMUP_URL 一次，再在原生 page source 里找标记：READY 即就绪；DENIED 或 AUTH REQUIRED 归 precheck_failed；ERROR 或无任何标记时原地重导航、有界重试，耗尽归 engine_error，永不归 network_error。桌面用 page.goto 读响应状态与标记。预热地址只经脱敏出口进入诊断。可复用 spike 的 navigateTo、waitMarkers、nativeMarkers 结构（0052 决策 6（预热），0051 决策 13）
- `engines/midscene/src/device/surface.mts（新）` · 设备侧接缝实现：串起解析 → Create → 等 RUNNING → 存在性检查与预签名 → newSession → activateApp 与采样 → 探测 → 预热，全程受获取预算约束，到期归 acquire_timeout；完成后 run-scope 才发 scope_started，sessionId 填会话 ARN。实现 step 前核对、复原核对（命令失败先查会话状态）、快照（按条件读地址；在原生上下文取控件与 page_source）、取确定性句柄 ctx{driver, device{platform,osVersion,scale}, uiKind, appId, app{restart}, log, withWebContext}（0052 决策 2，0051 决策 4，0050 决策 2）
- `engines/midscene/src/worker/deterministic.steps.mts` · 内建导航条目加 webdriver 句柄：应用目标经 DeepLink（0048 决策 7），网页目标按能力探测择路（0052 决策 4）；不注册「重新启动应用」与「页面地址匹配」（产品不内置有措辞的 step，0020 第 2 条），两者的示范进 steps/ 模板，重启经 ctx.app.restart()（0050 决策 1、2）
- `tools/（新，真机重新探测工具）` · 如 tools/device_reprobe.mts 或 .py 包装：在真实会话里逐项执行探测与原语，生成能力矩阵，并与 adapter 和 probe 测试 fixture 做差集。这是长期资产，注释守悬空指针红线（0052 决策 8）
- `engines/midscene/DEVELOPMENT.md、CONTRIBUTING.md` · 真机验收矩阵、设备模块说明：写明人工触发的真机验收矩阵：Android 加两代 iOS、网页加应用、故障演练、iOS 26 整链路单列一行，列为发版后验证项。DEVELOPMENT 补设备模块的划分与动态加载约定（0052 决策 8）

**先写的护栏测试**

- `engines/midscene/src/device/guard.test.mts`：用假 driver 断言以下调用都被拒：带旧令牌的调用、step 结束后保留的代理引用、解构或先取后调的方法引用、缓存的元素句柄、await 之后晚到的回调、进入终结后的调用、结果未知置位后的有副作用命令（click、type、execute('mobile: tap')）。只读白名单在结果未知后仍放行；白名单只对网络错误码与 502、503、504 重试 1 次，对超时和 500 不重试；有副作用的命令任何情况都不补发（0052 决策 6、8（命令守卫护栏））
- `engines/midscene/src/device/adapters/adapters.contract.test.mts（加快照 fixture）`：两个适配器对每个原语（tap、longPress、scroll、typeText、keyboardPress、home、navigate 的两条路线）发出的命令名与参数形态和快照完全一致；iOS 坐标是像素除以比例；Android 输入只发 mobile: type；iOS 不发 POST /keys，也不用 W3C 指针拖动（0052 决策 4、8（命令契约快照））
- `engines/midscene/src/device/read-points.test.mts`：差集护栏：在 src/device 与 src/worker 下 grep，`mobile:` 只出现在 adapters/ 下；系统版本与机型字段（platformVersion、osVersion、deviceModel 等）只在会话能力读取模块里读，且读出的值只流向诊断；new DeviceFarmClient 只出现在 device/session.mts；src/ 中 webdriverio 与 client-device-farm 的静态 import 只出现在 src/device/ 下（0052 决策 1、3、8（读取点），0051 决策 10）
- `engines/midscene/src/device/probe.test.mts`：归类真值表（假 driver）：重试后候选仍为零 → 不提供；有候选、切得进，只读命令超时而原生只读命令正常 → 不提供；列上下文本身失败或传输层错误 → 探测出错；原生只读命令也失败 → 先查会话状态，丢失则归 session_lost；原生应用会话里出现 WEBVIEW_chrome 不算候选；应用目标不探测网页上下文。另断言探测使用独立的短超时客户端实例，而不是 Promise.race；比例读取失败时按 DPR 回退规则计算（0052 决策 5）
- `engines/midscene/src/device/web-context.test.mts`：withWebContext 与设备上的导航：多候选与零候选（短等待后再列一次）都记 engine_error，并使用 ADR 原文消息，能力结论不翻转；fn 执行中句柄失效不在 fn 内重试。为 evidence 读地址时，多候选或零候选只把 url 置 null，url_missing 记 error 或 timeout，step 判定不变；能力结论为「不提供」时绝不调用 url（0052 决策 5）
- `engines/midscene/src/worker/run-scope.test.mts（新增 step 顺序契约组）`：用记录调用序列的假接缝断言：step_started → preStep → 执行 → 读地址（只在要产 evidence、目标是网页、结论为「提供」时） → restore → 控件采集（只在 failed 或 error） → evidence → step_done → enqueue。preStep 失败时 handler 与 AI 都不被调用，记 engine_error；restore 失败时最终判定为 error，原判定写进 message；restore 期间会话丢失归 session_lost；requires:web_context 遇「不提供」记 capability_unavailable、遇「探测出错」记 engine_error，都不调 handler、不转 AI。桌面接缝下的事件流与现有测试逐字节一致（回归）（0052 决策 2，0050 决策 1、2）
- `engines/midscene/src/worker/run-scope.test.mts（事件序列与退出码组）`：执行前失败：scope_started 之前只有 session_opened 与 session_closed，然后发 scope_done{status:'error', errorType}，没有任何 scenario 或 step 事件，退出码 0。session_lost：当前 step error、余下 step_skipped（shortcircuited）、scenario_done error，后续 scenario 零事件，最后 scope_done{status:error, errorType:session_lost}。结果未知后存活探测失败：下一条 scenario 不发 scenario_started，先查会话状态，非 RUNNING 发 scope_done{error, session_lost}、否则发 scope_done{error, engine_error}。设备路径的退出码只会是 0 或 1，永不出现 80；有 unconfirmed 会话或 attempted 尝试时退出码为 1。收到额外请求头却没有预热地址：桌面与设备都记 precheck_failed（0051 决策 4、5，0052 决策 6，0051 决策 13）
- `engines/midscene/src/device/finalize.test.mts`：假时钟下断言：四个阶段各自的截止线；SIGTERM 路径不调 deleteSession；正常路径的顺序为 destroy → 上传 → deleteSession → 核对 → 释放 → session_closed → scope_done → 排空；每个真实会话按 ARN 去重、恰有一条 session_closed，不会先 unconfirmed 再补 confirmed；待核尝试只发一对 attempted 事件；信号重复到达、超时与信号交叠时只进入一次四阶段；只有状态为 RUNNING 才发 Stop；Stop 报错后补查 Get；确认只认 STOPPING 或 COMPLETED；进入终结的那一刻撤销令牌并 abort act（0051 决策 5）
- `engines/midscene/src/device/session.test.mts`：版本族匹配：'18' 命中 18.x.y，'18.1' 不命中 18.10，写全段即精确匹配。选择顺序：先排除 BUSY 与 TEMPORARY_NOT_AVAILABLE，再按版本号降序、HIGHLY_AVAILABLE 优先、ARN 字典序。零候选重列一次仍为零 → precheck_failed，消息带最接近的可用版本。Create 结果未知只能由按名列举命中来消除，列举为空不构成排除；分页没扫完视为未核对。换台至多一次，剩余预算不足 150s 不再换台，被替换的会话先 Stop。observedS 的起止点正确，缺失记 null 而不是 0（0051 决策 3、7）
- `engines/midscene/src/device/session-name.test.mts`：名字格式与段序正确；scope 哈希是 SHA-256 前 16 位十六进制；A-Z a-z 0-9 . _ - 之外的字符按 UTF-8 字节百分号编码；总长超过 256 时只截最后一段，其余四段永不截断；按整名相等匹配，同一 run 内不同 scope 不互认（0051 决策 3）
- `engines/midscene/src/worker/redact.test.mts（共用跨语言 fixture，与 core 和 Nova 同一组用例）`：签名类查询参数与 gherkai_tunnel_token 的值被替换成 ***，`&` 与 `&amp;` 两种形态都覆盖；UND_ERR_CLOSED 错误文本里的整条端点地址被盖住；userinfo 旧用例不回归；经 log()、event-sink、evidence、device-session.json、page_source 五个出口的输出都不含签名（0051 决策 11，0035 决策 5）
- `engines/midscene/src/worker/no-device-deps.test.mts`：起子进程执行 --capabilities 与桌面 job（用 --import 钩子记录被解析的 specifier），断言 webdriverio、@aws-sdk/client-device-farm、src/device/*（limits.mts 除外）都没有被加载；min_grace_s 由常量推出、约 64 且小于 120；max_session_s 由常量推出（0052 决策 3（动态加载），0049 决策 4、5）
- `engines/midscene/src/device/warmup.test.mts`：标记归因：READY 即就绪；DENIED 或 AUTH REQUIRED 归 precheck_failed；ERROR 或预算内无标记时有界重试，耗尽归 engine_error；任何情形都不归 network_error。导航路线由探测结论决定。标记字符串与隧道侧预热页模板共用同一份 fixture（0051 决策 13，0052 决策 6）
- `engines/midscene/src/worker/evidence.test.mts（加组）`：传入快照时设备键正确落位；设备上 failed 或 error 的确定性与导航 step 产出 acts:[]，step_kind 正确，passed 的不产；桌面 evidence 不出现任何新键（与现有 fixture 逐字节一致）；page_source 的 URI 由 refFor 算出，路径进入回传的入队列表（0051 决策 8，0042 决策一）

**完整性审查补认领**

- 应用目标上的导航 step（0048 决策 7，deepLink spike 已定）：导航判据为 Given / When 后整句是一个地址，应用目标接受任意 scheme；Android 发命令前按 RFC 3986 校验并拦 ; ' ( )，deepLink 带 package，报 unable to resolve Intent 记 capability_unavailable，成功后轮询前台包名；iOS 带 bundleId、成功即已送达；首次遇到 WebDriverAgent 不支持打开地址即缓存为设备不支持；前台应用查询进只读白名单。护栏测试：字符集校验用例（含 | ; 截断风险的字符）、三种失败情形的归类、缓存只记能力否定。
- 红线测试补：scenario 前核对在第一条 scenario 前不调用、年龄恰到边界、探测成功后下一条照常执行、失败按会话状态分流 session_lost / engine_error；释放与 session_closed 先于 scope_done；安装包 HeadObject 回 404 或 403 时 Create 零调用（存在性检查必须排在建会话之前）。
- 设备模块的两条护栏测试：系统版本与机型只经会话能力对象的唯一读取点进入；两个驱动适配器的命令契约快照。Device Farm 客户端只在 TS 设备模块构造的断言。0052 决策 8、0051 决策 10。
- 接缝第四项边界义务「scenario 前核对」（本轮补进 0052 决策 2）。
- 真跑核对：一次故意建连失败的真机执行，核对报错文本里的路径令牌与签名已被盖住。0051 决策 11。

**真跑或对抗核查才算数的结论**

- 全新会话、尚未导航时的探测时机：iOS 15.8、18.6 Safari 与 Android Chrome 刚建好会话时是否已有 WEBVIEW_<pid> 或 CHROMIUM 候选。若首次导航前候选为零，探测会把 iOS 15.8 判成「不提供」，转去走它不支持的 deepLink，导致预热失败。这一点 mock 证明不了
- iOS 26 整条链路：探测超时 → 恢复原生上下文 → deepLink → READY，在真机验收矩阵里单列一行
- 预热三个失败分支各真实触发一次：边缘拒收 cookie、校验 401、请求失败
- 执行实例 connectionRetryCount=0 时，真实点击或输入在客户端超时后不被重复执行；结果未知处置后的截图存活探测；多个客户端实例的超时在同一会话上各自生效
- Midscene 1.15.1 用真实的 Agent 加自写 AppiumInterface 时，适配器抛错并置 abortSignal 后，act 立即结束、零后续动作（spike 只用假界面验过）
- SIGTERM 落在各阶段的表现：Create 在途、PENDING_CONCURRENCY 排队、释放中网络退化；终结四阶段在 Fargate stopTimeout 下能否收完，约 64s 是否够用，要在网络退化条件下校准
- 进程级兜底：newSession 客户端超时触发 unhandledRejection 后能进入终结，会话不泄漏
- 脱敏：故意建连失败一次、外部 Stop 一次（制造 UND_ERR_CLOSED），核对 stderr、事件、evidence、device-session.json 中的签名都已盖住
- session_lost 的两条路径：外部停止会话；会话年龄后备（可在测试构建里注入较小的年龄上限），以及 150 分钟边界上端点拒绝命令而 API 仍报 RUNNING 的情形
- 应用分发：预签名 S3 地址配 appium:app 加 autoLaunch:false，再 activateApp、采样，以及换台重建；task role 下 HeadObject 缺失键返回 404
- 获取预算 600s 在并发排队与换台重建下是否够用，实施期校准
- --capabilities 在容器镜像里不加载设备依赖、启动耗时不回退
- 桌面路径在接缝搬移和新增桌面预热之后，用 tools/e2e_harness.py 在本机与云端各真跑一次，对照事件与 evidence 无回归
- 真机验收矩阵：Android 加两代 iOS，网页加应用，加故障演练

**易错点**

最容易做错的四件事：
（1）桌面接缝必须是现有代码的原样搬移。makeGuardedCleanup 的重入语义、建连重试与退出码 80、cleanup 先于提前上传、排空的顺序，都要用现有 run-scope 测试与真跑回归钉住。设备差异只能落在接缝实现里，不能在 runStep 或 scenario 循环里写 `if (device)`。桌面唯一的新行为是预热，以及「有额外请求头却没有预热地址」时记 precheck_failed，它会走新的 scope_done{status:error} 出口，不再走 throw 退出码 1。
（2）spike 06 的原语可以借，但其中三处正是 ADR 的被拒方案，照抄就会违背决策：usableWebCtx 用 Promise.race 放弃挂住的命令；typingRoutes 和 iosSendKeys 在运行期多路线试错回落；scroll 在 mobile: swipe 失败后回落到 W3C 指针拖动。此外 PLATFORM 与 SCENARIO 全局分支、logLevel 'warn'、缺省的传输层重试也都要去掉。命令守卫必须是 Midscene 界面、导航与 handler 拿到的唯一句柄；令牌在 step 结束或进入终结的那一刻撤销，不能等到下一个 step。
（3）动态加载与常量分层：--capabilities 要输出由设备常量推出的 max_session_s 与 min_grace_s，所以这些常量必须放在不 import 任何 SDK 的 limits 模块里，否则「能力自述零依赖」会被悄悄打破。webdriverio 与 Device Farm SDK 现在仍在 devDependencies，要移到 dependencies，并用 npm 10 重算锁文件。
（4）log() 现在不脱敏，而 WebdriverIO 会把整条带签名的端点地址写进错误文本。stderr、bin 的 fatal 行、device-session.json、page_source 都要经同一个脱敏出口。参数名集合待定（见 open_questions），三份实现要同步改。

另外两点：
- 「真实 IAM 角色闭环」在最近一次提交（3739ce5）里已经按表建角色逐项核过。本批真跑前还剩一项要复核：经 worker 代码路径走一遍 HeadObject 缺失键返回 404 与预签名。
- 建议先写 guard、session-name、probe、step 顺序这四组测试，再动 run-scope；open_questions 第一条（scenario 前钩子）会改变接缝形状，最好在开工前定下来。

