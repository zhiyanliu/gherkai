---
name: gherkai
description: 用 gherkai 做 AI 驱动的 UI 端到端测试：从需求与被测应用写出 Gherkin .feature 与确定性 steps 代码，plan 用例预检、本机 run 或 submit 后台或云端批量运行、status 收判定、explain 读失败证据、收窄后重新运行并汇报；也覆盖环境就位与排障（doctor、引擎 worker、AWS 凭证与 region、版本不一致）和云端后端交付（deploy 交人、variant 镜像与 push-worker）。触发规则：项目里有 .feature 且 gherkai 在场（装了 gherkai CLI、steps/ 里 import 了 gherkai 的 worker 包、或项目文档提到 gherkai）时，用户一提到跑测试、写用例、看为什么失败就用本 skill，哪怕没说出 gherkai；项目里还没有 .feature 时看项目级信号：本 skill 装在这个项目里、项目文档提到 gherkai、或有 gherkai 式 steps/，有其一就照测试意图触发（从零写第一条用例正是本 skill 的活）；只是机器上装了 gherkai CLI 不算信号，那时要用户明确提到 gherkai。不接管两类：纯 Cucumber / Playwright 项目（有自己的 step definitions 或配置）；用户点名别的测试工具（pytest、Selenium、Cypress、Playwright、Cucumber、behave……）的问题，哪怕项目里也有 .feature——除非他要把它们迁到 gherkai。English triggers - gherkai, run/plan/submit gherkai tests, .feature with AI steps, deterministic steps, explain a failed scenario, gherkai doctor, worker variant, push-worker.
---

# gherkai：替使用者把 UI 测试整条走通

gherkai 把 Gherkin `.feature` 里的每一步交给云端浏览器里的 AI 引擎去做、去判，精确检查则由项目自己注册的确定性 step 代码接管。你的任务不是给建议，而是从需求与被测应用写出用例、运行并得到判定、读懂失败、缩小范围后重新运行，最后用人一眼能定夺的形式汇报。全部选项以 `gherkai <命令> --help` 为准，本文只讲怎么用对。

## 0 先分域，再读对应 reference

| 你在做的事 | 去读 |
|---|---|
| 写用例、运行、判定、读证据、收窄后重新运行（最高频） | 本文正文全部 |
| 选引擎、被测 UI 不是英文、确定性 step 的最小模板与契约、证据字段两引擎为何填得不一样 | `references/engines.md` |
| 写好确定性 step 的代码：该不该写、等待与判定、失败消息、判定逻辑与注册分离、本地单测、改一条在用的 step | `references/deterministic-steps.md` |
| 装不上、`doctor` 有红、凭证 / region、ngrok、版本不一致导致退出码 2 | `references/setup-and-diagnosis.md` |
| 云端后端：部署交人、variant 镜像、`push-worker`、升级顺序、多环境、清理 | `references/cloud-backend.md` |
| CI 接 `--json` 与退出码、字段含义、产物落点 | `references/cli-json-contract.md` |

## 1 心智模型

- **一步三种执行路径**。默认走 AI：`Given` / `When` 的文本是动作，`Then` 的文本是布尔断言（可投票）。命中项目 `steps/` 里注册的正则则走确定性代码：不问 AI、不投票、可复现。另有一条内建捷径：文本里**双引号**内的内容以 `http://` / `https://` 开头时，整段引号内容当作地址、该步直接导航（本机应用照写的 `http://localhost:3000` 同样命中；单引号不触发），不耗 AI。派发优先级依次是确定性命中、双引号 URL 导航、AI。
- **边界**：精确检查（URL、DOM、数值、必须可复现、要快）交给确定性 step，出现频次高的检查（`Background` 前置、`Scenario Outline` 每行、要投票的断言）也优先写成确定性——它零模型费用、毫秒级完成（AI 步一步要几秒到几十秒），整套用例的墙钟与会话时长跟着降；模糊、一次性、页面变化多、靠语义理解的交给 AI。
- **scope 与 tag**：`@scope:<名>` 把多条 scenario 编进同一个 job，共享一个浏览器会话、串行执行（后一条接着前一条留下的页面状态）；未标 scope 的 scenario 各成一个 job，`scope_id` 就是这条 scenario 的 id：`<文件>:<行号>`，`Scenario Outline` 展开出的每条再多一段 Examples 数据行的行号——别自己拼，从判定明细 / `plan --json` / 筛空时打出的候选清单里逐字复制。**scope 名在整个 run 里是全局的**：两个 feature 文件写了同一个名字就合并成一个 job（并发变串行、互不相干的用例锁进同一会话，`@engine` / `@timeout` 按合并后的全体解析、两边标了不同值整个 run 拒绝运行），撞名只在 stderr 提示一行，所以名字带来源前缀（`checkout-happy-path`、`admin-login`），别用 `login` / `smoke` 这种通名；也别把 scope 名写成 `<文件>:<行号>` 这个形状——正好等于某条未标 scope 的 scenario 编号时整个 run 拒绝运行并以退出码 2 结束。`@engine:novaact|midscene` 选引擎，`@timeout:<秒>` 给该 scope 的墙钟预算；其它 tag 只是普通标签，靠 `--tags` 筛。feature 行的 tag 会传给其下每条 scenario——`@scope` 标在 feature 行就是把整个文件塞进一个串行 job，要的是这个再标。
- **引号只是书写习惯**：AI 步把关键字之后那段文本交给模型（整段被双引号包起来时，外层那对引号会去掉）；确定性 step 的正则匹配的是没去引号的原文——对象是关键字之后的那段文本、引号照留，正则里别写关键字，写用例时的写法要与它的 `example` 一致。匹配是**子串搜索、不自动锚定**，所以模式要写窄：带上引号与特征词（像内建那条 `页面地址匹配 "<正则>"` 的形状），别只写一个动词——宽模式会顺带命中本该走 AI 的步、悄悄换掉它的判法，两条模式同时命中一个 step 则该步直接记 error；宽窄靠 `gherkai plan` 的标注验。`And` / `But` 承前一步的关键字；`*` 或开头就是 `And` 会被拒（判不出动作还是断言）。

## 2 引擎怎么选

Midscene 对被测 UI 的语言不限。Nova Act 的支持范围是英文 UI：在非英文页面上能导航、能判页面级语义，但「正文里是否出现某个中文词」这类文本包含断言会系统性判否（同一页面上的英文词仍可靠），投票治不了。诊断规则：Nova Act 引擎下非英文页面的断言判否，先排查引擎语言面，别先当被测应用的 bug。三条出路：给 scenario 标 `@engine:midscene`（或 `--default-engine midscene`）、把断言改写成页面级语义陈述、把文本与结构检查改成确定性 step。默认引擎是 novaact；`gherkai list-engines` 看本机装了哪个。证据的 schema 两引擎结构相同，但填充有系统性差异（某些字段只有一侧给值），是引擎事实不是抽取失败，细表见 `references/engines.md`。

## 3 本机还是云端，run 还是 submit

- `run`：前台同步，CLI 全程在线，退出码即判定。人在等结果、批量不大时用它。
- `submit`：提交即返回，stdout 只打一个 `run_id`，退出码 0 只表示提交成功；判定看 `status <run_id> --wait`。local 后端由本机一个脱离 CLI 的后台进程推进（本机需开机）；cloud 后端由云端推进，提交后关机也会运行到结束。
- **cloud 一条线**：依次执行 `doctor --backend cloud --prefix P`、`plan`、`submit --backend cloud --prefix P`、`status --backend cloud --prefix P --wait`、`explain --backend cloud --prefix P`。`plan` 不依赖后端、两个后端都要先执行一次；但它的确定性标注问的是**本机** steps，云端实际运行用的是 worker 镜像里那份，标注只代表本机视图。`status` / `explain` 的 `--backend` / `--report-dir` / `--prefix` 必须与**产生这个 run 的那条命令**（`run` 或 `submit`）逐字一致——本机 `run --report-dir out/` 之后也得 `explain <run_id> --report-dir out/`；不一致就以退出码 2 结束、说找不到这个 run（那句提示只提 `submit`，按上面那条对齐参数，不要照它只改 `submit`）。
- **部署云端后端是部署方的事，你不自己运行 `gherkai deploy`**（改 AWS 资源与 IAM）。用 `doctor` 判缺什么，把该运行的命令与前置交给人；推定制 variant 镜像的 `gherkai deploy push-worker` 不改 IAM，你可以运行。细节见 `references/cloud-backend.md`。
- **被测应用在本机 / 内网时**：浏览器在云端，`http://localhost:3000` 不可达。唯一做法是 `--expose-local <feature 里书写的原始 origin>`，feature 照写原始地址，提交时替换成带每 run 一换凭据的公网 URL；选项值须与 feature 书写逐字一致（前缀字符串匹配，localhost 与 `127.0.0.1` 不互认），Host 放行与排障入口见 `references/setup-and-diagnosis.md` 第 5 节。`run` / `submit` / `plan` 都收（`plan` 只标注、不起隧道、也不校验地址是否匹配得上）。前置两条，`doctor` 都不查：本机装好 ngrok 且在 PATH 上（下载 https://ngrok.com/download ），以及配好 authtoken（`ngrok config add-authtoken <token>` 写进 ngrok 自己的配置文件，或环境变量 `NGROK_AUTHTOKEN`，任一处即可），少哪条都在起隧道时失败。`submit` 后隧道由本机后台进程持有，本机须保持开机联网到 run 终态，这是「提交后关机也会运行到结束」的唯一例外。
- **`--tunnel-ttl`（仅 `submit`）**——只在 cloud 后端且开了隧道时才有意义：隧道守护进程的兜底 TTL，缺省为这个 run 各 job 预算之和加余量；到点**无条件**拆隧道，调小会在 run 未完时断掉被测应用的入口，别为「省一点」去调它。

## 4 编写 feature 与 steps

从需求与被测应用（代码、文档、真实页面）取信息时，优先取稳定的语义：标题、可见文案、流程结果，而不是选择器、类名这类实现细节。写法：

- 一条 scenario 讲一件事，五到八步以内；导航步写 `Given 打开 "http(s)://…"`（双引号内 URL 走导航），动作步写用户会怎么说（`When "在搜索框输入 Python 并提交搜索"`），断言写成页面级语义陈述（`Then "当前是 Python 的词条页"`、`Then "页面没有报错"`），别把子串规则、段落边界塞进断言，那是确定性 step 的活。
- 需要接着上一条的页面状态继续，就把两条编进同一 `@scope`；互不相干的用例分开 scope 好并发，scope 名跨文件不能撞（见第 1 节）。被测 UI 非英文就标 `@engine:midscene`。单个 scope 会很长就标 `@timeout:<秒>`。
- DataTable / DocString 可以挂在 AI 步下，随 step 一起喂给模型。
- 公共前置步（登录、导航到基线页）写 `Background`：它展开进同一 feature 下每条 scenario 的最前面，步号从它的第一步 0 起数、scenario 里书写的步跟着后移（`explain --step N` 同此口径）；同一 `@scope` 里每条 scenario 都各自重新运行一遍它，别把导航塞进 `Background` 又指望后一条接着前一条的页面状态。
- 同一流程换数据运行多遍写 `Scenario Outline` + `Examples`：每行数据展开成一条独立 scenario（占位符已代入），未标 `@scope` 时各成一个 job、`scope_id` 比普通 scenario 多一段数据行号，收窄后重新运行时照抄判定明细里的完整值；`--scenario` 要一次选中该 Outline 的全部数据行就只给声明行的行号（纯数字或 `:行号`）。
- **什么时候配确定性 step**：URL 匹配、元素存在、精确数值、必须可复现、要快、出现频次高。两引擎各有最小模板与必填元数据（`description` / `example`，缺了启动即报错），见 `references/engines.md`。同一 feature 要在两个引擎上运行时正则两侧要成对写。内建一条 `Then 页面地址匹配 "<正则>"` 可直接用。**写代码时**（等待与判定、失败消息带现场、判定逻辑放 `_` 前缀模块并本地单测）按 `references/deterministic-steps.md`；改完的汇报带根因与改法、两侧清单与 `plan` 标注的核对结果、以后的自查方法三样。
- 写完先 `gherkai list-deterministic --engine <名>` 核对你的 step 在清单里，再 `gherkai plan <feature>` 看每步标注：命中确定性的标 `← 确定性: <说明>`，其余走 AI。

## 5 工作循环

1. `gherkai doctor`（首次或环境变过；cloud 后端加 `--backend cloud --prefix P`）。
2. `gherkai plan <feature…>`：看分组、引擎路由、派发标注、筛选结果。纯本地、零费用。**plan 打出的 job 数就是这个 run 要开几个云端浏览器会话**，费用随 job 数与步数走，`--max-concurrency` 只改同时运行几个、不减总账。首次在这个项目实际运行、或 job 数明显超出人交代的范围（人只说一条、plan 列出一屏）时，先把分组与规模报给人再执行；只想验证刚写的那条就按第 6 条收窄到一条。
3. `gherkai run <feature…>` 或 `gherkai submit <feature…>` + `gherkai status <run_id> --wait`。实际运行会产生 AWS 费用，先 `plan` 后运行。
4. 有用例没过，**第一个命令是 `gherkai explain <run_id>`**（哪怕你能直接读 `jobs/*.json` 与 evidence.json 也先用它：它把判定、原因、模型看见了什么与截图位置拼成一份别人能复现的证据，手翻 JSON 容易漏 message 与截图位置）：按书写顺序列每一步，失败 / 出错 / 跳过的步展开成三段：问了 AI 什么、它看见与想了什么、截图在哪；判定里已看出哪个 job 红了就直接 `gherkai explain <run_id> <scope_id>`（位置参数，值与重新运行时用的 `--scope` 同一个）；再往细走 `--scenario SEL` / `--step N`（0 起、与文本步号用同一口径，须与 `--scenario` 同给）缩到一步，`--all` 连通过的步也展开，`--full` 逐帧全文，`--json` 拿完整证据。要更多再读 `--json` 或 `jobs/*.json`，别解析 HTML 报告、别自己拼产物位置，顺 `ref` 走。
5. 修：断言写法问题改 feature（只动要改的那一步、别增删其它行——未标 scope 的 scenario 用行号当 id，行号一漂，旧报告与 `--scope` 的值就都指不到了）；精确检查改成确定性 step；语言面问题换引擎；确是被测应用的 bug 就交给人定夺。**要说「是被测应用的 bug」之前先复投**：AI 断言默认只判一次（`explain` 里那步打 `votes 0/1` 就是只判了一次），判否也可能是模型这一次没看准——收窄到那一条再多投几票：`gherkai run <feature> --scope <scope_id> --assertion-votes 3`（票数作用于本 run 每条 AI 断言、费用随票数涨，所以务必先收窄）。三票一致判否才报 bug；出现分歧票就是抖动或断言措辞歧义，改成直白的语义陈述或落到确定性 step。**例外：Nova Act 引擎下非英文页面的词匹配判否是系统性的，复投只增加费用、不要给 `--assertion-votes`，直接走第 2 节的三条出路。****四种处置都按第 9 节汇报**——人要知道的不只「哪条是产品 bug」，还有「你替他改了什么、为什么」：改断言写法、换引擎都动了验收口径，不报等于悄悄放宽了这条用例。
6. **收窄后重新运行**（`run` / `submit` / `plan` 同一套）：`--scope ID` 的值就是判定明细里的 `scope_id`，重新运行失败的 job 最直接；`--scenario SEL`（完整 scenario id、行号、或标题片段，区分大小写；给 `Scenario Outline` 声明行的行号表示选中它展开的全部数据行）；`--tags TAG[,TAG]`（一个值内的逗号表示任一命中，重复给表示都要命中，@ 可省）。`--scope` / `--scenario` 可重复、任一命中；`--tags` 重复给时都要命中；不同类同给时都要满足。筛成空集时以退出码 2 结束并列出全部候选，照着改。
7. `steps/` 里任一文件加载失败，`plan` / `run` / `submit` 都会在起第一个 job 前整个 run 拒绝运行并以退出码 2 结束，错误点名文件与异常。先修那个文件，不是怀疑 feature。显式给的 `--steps-dir` 不存在同样以退出码 2 结束；缺省 `./steps` 不存在不算错。
8. 只写了一侧的确定性 step，在另一引擎上这一步会悄悄换回 AI 判定，执行前预检不替你发现（它只查本次用到的引擎）。两引擎都用时 `list-deterministic --engine` 各查一遍。

## 6 机读读法

字段表在 `references/cli-json-contract.md`。几条读法：`message` 恒为「为何不是 passed」，job 级与 step 级同义，通过时为 null；`record_missing` 为 true 表示骨架里有这一步、判定明细里没有它的记录（没运行到或没上报），此时 `status` / `votes` / `error_type` / `message` / `duration_ms` 全为 null，但 `report_refs` 是空数组、`shortcircuited` 恒 false，判有没有记录只看 `record_missing`；`evidence_missing` 非 null 表示这一步没读到机读证据：`no_ref` 里混着「确定性 step 与导航步本就不产」「AI 运行了但抽取失败」「这一步根本没有记录」三种、在这里分不开，`unreadable` 表示指针在但读不到，`unsupported_schema` 表示格式版本不认，要区分「没运行」与「运行了但没产证据」一律看 `record_missing`；`aborted_hint` 非 null 表示这个 job 终态是 aborted 或 error、且判定明细里只有部分 step 的记录，别据此判终态，终态看同层 `status`；`has_step_records` 是 job 级事实、不随筛选变化，为 false 时判定只剩 job 级那一层。`run --json` 的 `artifacts` 给报告与判定明细位置，`--no-report` 时这个键省略（唯一例外：本机运行且同时给了 `--quiet`，那时它只剩一个 `worker_log`）；`status --json` 的 `artifacts` 恒在、给的是约定落点，未到终态那些路径可能还没写出来，别拿它的存在当终态判据，终态看同层 `status`。

## 7 选项按「谁有这个 flag」分组

| 谁有 | flag | 什么时候动 |
|---|---|---|
| `run` / `submit` 共用，多数 `plan` 也收 | `--default-engine` `--assertion-votes` `--default-job-timeout` `--steps-dir` `--scope` `--tags` `--scenario` `--expose-local`（这 8 个 `plan` 也收：用例预检要与实际运行一致就照样给）；`--max-concurrency` `--report-dir`（`plan` 不收） | `--assertion-votes 3` 查 AI 断言抖动；`--max-concurrency` 默认很保守（护成本与配额），scope 多且互不相干时调大；`--default-job-timeout` 只管未标 `@timeout` 的 scope。默认值都以 `--help` 为准，别背数字 |
| 仅 `run` | `--fail-fast` `--quiet` `--no-report` `--grace` | `--quiet` 少占屏幕与上下文、worker 日志改落文件，判定明细与证据照落；`--no-report` 连 `explain` 一起废掉——判定明细与 AI 证据都不落盘，事后 `explain` 找不到这个 run，失败原因只剩本次输出里每步那一句，想细看只能再花钱重新运行，所以只在确定不用读失败原因的纯 CI 门禁上用；`--grace` 别调小，过小直接以退出码 2 结束、且会泄漏浏览器会话 |
| 仅 `submit` | `--tunnel-ttl` | 只在 cloud + `--expose-local` 时有意义 |
| cloud 后端：`doctor` / `run` / `submit` / `status` / `explain` 各要给（`plan` 不吃） | `--backend cloud` `--prefix` `--region` `--profile` `--worker-variant`（仅 `run` / `submit`） | `--backend` / `--prefix` / `--report-dir` 必须与产生这个 run 的那条命令逐字一致，不一致即以退出码 2 结束、说找不到这个 run；`--region` 要指同一个 region（换了就查不到），`--profile` 换成另一个指向同账号同 region 的 profile 不影响；`--worker-variant` 选云端 worker 镜像上的确定性 step 集，不给用部署侧默认指针 |
| 查询类各自有 | `status --json`、`explain --json`、`plan --json`、`doctor --json`、`list-engines --json`、`list-deterministic --json` | `run --json` 有、`submit` 没有：run_id 走 stdout，进度与判定看 `status --json` |

## 8 退出码分流

- `run`：退出码即判定。0 全通过；1 已运行但有失败或出错；2 无法运行（feature 读不到、参数不合法、worker 没装、steps 加载失败、云端凭证 / 版本 / variant 问题）。
- `status`：**只有读到终态才表判定**（通过时退出码 0、其余终态 1）；未到终态一律以退出码 0 结束、只表示查到了。要判定必须 `status --wait`，它同时是接力：后台推进卡住时由这条命令续到底。退出码 2 表示查不到这个 run（cloud 后端还含云端读不到、版本不匹配）。
- `submit` / `plan` / `explain` / `doctor`：只表做成没做成（退出码 0 或 2）。`explain` 哪怕用例全红也以退出码 0 结束。
- CI 接 `run` 的退出码，或 `submit` 之后接 `status --wait` 的退出码；别接 `submit`、`explain` 的。

## 9 失败汇报模板

向人汇报每条没过的用例时用固定小结构，让人一眼能定夺。汇报是给人的：别提「按 skill 第几节」「见 references/…」这类你自己的读物，直接给内容。先认失败落在哪一层：**有某一步判 failed / error** 时用步级模板；**没有任何一步判否、只有 job 级的 error / aborted / skipped**（超时、起 worker 失败、网络、被 `--fail-fast` 中止，或中止前根本没启动）时用 job 级模板。硬套错的那个会逼你编出不存在的步号与模型证据。

步级：

```
用例：<feature 文件> / <scenario 标题>  第 <n> 步  <step 原文>
判定：<failed|error>  原因：<message 原文>
模型看见：<thought 最后一句>  截图：<screenshot 地址>
建议：<改断言写法 | 改成确定性 step | 换引擎（语言面） | 被测应用的问题（复投仍一致判否）：<一句>>
重新运行：gherkai run <feature> --scope <scope_id>
```

「模型看见 / 截图」这行只有 AI 步填得出：确定性步与导航步走的是代码、不问模型，本就没有 thought 与截图——整行删掉，别留空栏也别编；这类步的建议栏换成「确定性 step 的选择器或判定逻辑要改」或「这条检查本就该交给 AI 步」。

job 级：

```
用例：<scope_id>（整个 job，判否不落在某一步）  引擎：<engine>
判定：<error(<error_type>)|aborted|skipped>  原因：<message 原文>
建议：<把这个 scope 拆小 | 给它加 @timeout:<秒>（或调 --default-job-timeout） | 被 fail-fast 中止的：根因在先失败的那个 job，先汇报那条 | 环境或引擎的问题：<一句说清是哪一样，如 worker 版本与 CLI 不一致、region 或凭证缺失、隧道断开>>
重新运行：gherkai run <feature> --scope <scope_id>
```

## 10 别做的事

- 别把 `submit` 的退出码 0 当通过：它只说提交成功，判定还没出。
- 别把不带 `--wait` 的 `status` 退出码 0 当通过：未到终态它的退出码也是 0。
- 别解析 HTML 报告或引擎原生 trajectory 文件：`explain` 与 `--json` 才是稳定接口，报告是派生视图、文件名会变。
- 别自己拼产物位置：顺判定明细里的 `ref`（产物指针）走，本机与 S3 两侧同一形式。
- cloud 后端改了 steps 不 `push-worker` 等于没改：云端 worker 读的是镜像里那份，本机 `plan` 的标注不代表云端。
- 别只写一侧的确定性 step：另一引擎上会静默落回 AI，run 还可能「通过」。
- 别调小 `--grace`（仅 `run` 有，且只对本机后端；cloud 后端给了它会以退出码 2 结束）：云端的停止宽限在部署侧的 `gherkai deploy --stop-timeout`，归部署方。
- 别为了「验证一下改动」就 `run` / `submit`：每次实际运行都开云端浏览器会话、花真钱，改完用 `plan`（零费用）验写法与标注；实际运行只在人要结果时做。
- 别自己运行 `gherkai deploy` / `gherkai destroy`：交给人，你负责准备命令与前置清单。
