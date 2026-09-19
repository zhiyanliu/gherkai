# 编写 .feature

本页讲 `.feature` 文件怎么写：一个最小骨架长什么样，哪些 step 交给 AI、哪些必须精确，AI 断言怎么写才稳定，投票次数怎么用，`@scope` / `@engine` / `@timeout` 三个 tag 的语义，Gherkin 各种写法的支持范围，按引擎调整写法（含非英文 UI），以及哪些内容不该写进 `.feature`。确定性 step 的代码怎么写见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)；运行命令、选项、退出码与结果位置见 [`running-and-results.md`](./running-and-results.md)。

本页引用的片段出自仓库的 [`features/`](../../features/) 目录。

## 一个最小的 .feature

一个 `.feature` 文件至少要有一行 `Feature:` 和一条 `Scenario:`，step 写在 scenario 下面：

```gherkin
Feature: 维基百科搜索

  Scenario: 搜索并判定
    Given 打开 "https://www.wikipedia.org/"
    When "在搜索框输入 OpenAI 并提交搜索"
    Then "当前页面是关于 OpenAI 的维基百科词条页"
```

本页后面的代码块都是节选。抄用时补上所属文件的 `Feature:` 行：缺这一行时解析失败，报错指向文件第 1 行。

## 一个 step 的三种执行路径

worker 拿到一个 step 后按固定顺序决定它走哪条执行路径：

| 顺序 | 命中条件 | 怎么执行 |
|---|---|---|
| ① 确定性 step | step 文本命中项目 `steps/` 目录里注册的正则，或引擎内建的正则 | 调用注册的函数，用 Playwright 直接查页面。不问 AI、不投票、逐次可复现 |
| ② 导航 | step 文本的双引号内**以** `http://` 或 `https://` 开头（小写；大写不命中） | 直接打开这个地址。不问 AI。引号内直到下一个双引号之间的全部内容都当成地址，所以引号里只写地址、不要再接别的话。单引号不触发 |
| ③ AI（默认） | 以上都不命中 | `Then` 的文本当布尔断言交给模型判真假（可投票）；`Given` / `When` 的文本当动作交给模型执行 |

表脚注：

- 关键字只决定第 ③ 条执行路径怎么派发：`Then` 是断言，`Given` / `When` 是动作，`And` / `But` 承接前一条的身份。前两条执行路径都不看关键字，所以 `Then 页面地址是 "https://example.com/a"` 也会被当成导航步——直接打开这个地址并记通过，断言不会发生。要判 URL 就用确定性 step：两个引擎各内建一条 `Then 页面地址匹配 "<正则>"`，装了对应引擎的 worker 即可用，无需写任何文件（见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)）。
- 外层双引号只是书写习惯。交给模型前会被去掉；确定性 step 的正则匹配的是关键字之后的原文、引号照留。

## 什么交给 AI，什么必须精确

| 这类判定 | 写成 | 理由 |
|---|---|---|
| 当前 URL、某个选择器命中的元素、精确数值、精确文本 | 确定性 step | 有唯一正确答案，交给代码逐次可复现，也更快、更省 |
| 必须写进验收口径、不容许结果波动的检查 | 确定性 step | AI 判定可能在两次运行之间给出不同结果 |
| 页面级语义（是不是这个词条页、有没有报错、内容是否完整） | AI step | 语义理解正是模型的长处，写起来零代码 |
| 页面结构经常变、一次性的探索式用例 | AI step | 选择器会随改版失效，语义陈述不会 |

确定性 step 是少数：多数用例整篇用自然语言写完即可，只在上表前两行的场景补一两条确定性 step。写法见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)。

## AI 断言怎么写才稳

- **写成一句可判真假的语义陈述**，主语是页面：`Then "当前页面是关于 OpenAI 的维基百科词条页"`、`Then "页面没有出现服务器错误"`。
- **不要把子串规则、段落边界、选择器写进断言**（「第三段第二句包含 X」「`#total` 的值等于 42」）。这类检查交给确定性 step。
- **判定前先让待判定的内容进入视口**：弹窗、Cookie 提示、捐款横幅都可能把目标内容推出屏幕，模型会如实判否。用一个动作步先关闭遮挡并滚动到目标位置。
- **一个 When 只做一件事**。多个动作压在一句话里，模型可能只完成前半句；拆成多个 When，失败时也能定位到具体哪一步。
- **一条 scenario 讲一件事**，步数控制在个位数；需要接着上一条的页面状态继续，用 `@scope` 把它们编到一起，而不是写成一条很长的 scenario。
- **判否时先提高票数复测，再改用例**：AI 断言默认只判一次，把 `--assertion-votes` 调到 3 或 5 后仍一致判否，才说明是被测应用的问题（用法见下一节）。票数出现分歧说明结果有波动或措辞有歧义，把断言改直白，或落成确定性 step。

下面这段出自 [`features/wikipedia_assertions.feature`](../../features/wikipedia_assertions.feature)，处理捐款横幅并滚动到首段的那一步，作用就是让待判定的内容进入视口（scenario 标题按你自己的验收口径写）：

```gherkin
Scenario: 维基百科首页与 OpenAI 词条首段的 AI 断言
  Given 打开 "https://www.wikipedia.org/"
  Then "页面没有出现服务器错误"
  Then "页面上展示的语言版本超过 5 种"
  When "在搜索框输入 OpenAI 并提交搜索"
  When "如果页面顶部有捐款横幅就关掉它，然后滚动到词条正文的第一段"
  Then "词条首段提到了 artificial intelligence"
```

## 投票：让 AI 断言判多次取多数

`--assertion-votes N`（`plan` / `run` / `submit` 都收，默认 1）把每条 AI 断言问 N 次，**过半数**才判通过。

| 事项 | 说明 |
|---|---|
| 取值 | 整数，最小 1（1 = 单次判定，不做波动检测）。用奇数：4 票里 2 票赞成不过半数，判否 |
| 作用范围 | 本次运行的**每一条** AI 断言。暂不支持按 scenario 或 scope 单独设置 |
| 代价 | AI 断言的模型调用次数与该步耗时随 N 成倍增长，费用随之上升。动作步与确定性 step 不投票，不受影响 |
| 用法 | 怀疑某条断言结果波动时，先把范围收窄到那一条 scenario 或那一个 scope，再调高票数，不要整批调高 |
| 无效场景 | Nova Act 在非英文页面上对「正文里是否出现某个中文词」这类断言会系统性判否，增加票数不改变结果（同一页面上判断是否出现英文词仍然可靠）。改法见「按引擎选写法」 |

收窄范围的选项见 [`running-and-results.md`](./running-and-results.md)。

## 三个有语义的 tag

| tag | 作用 |
|---|---|
| `@scope:<名>` | 把多条 scenario 编进同一个 job：共享一个浏览器会话、按书写顺序串行执行，后一条接着前一条留下的页面状态 |
| `@engine:midscene` / `@engine:novaact` | 指定这条 scenario 用哪个引擎 |
| `@timeout:<秒>` | 给这个 scope（一个 job）设墙钟预算 |

规则：

- **写在 Feature 行、`Rule` 行、`Examples` 块上的 tag 都会传给其下（或其展开出的）每一条 scenario**。`@scope` 标在 Feature 行等于把整个文件编成一个串行 job，标在 `Rule` 行等于把这条规则下的 scenario 编成一个。
- **传下来的 `@scope` 不能被单条 scenario 覆盖**：同一条 scenario 解析出两个不同的 `@scope` 值即整批拒绝运行。要按 scenario 分组，就不要在 Feature 行或 `Rule` 行标 `@scope`。
- **`@engine` 与 `@timeout` 按 scope 生效**：scope 里任一条 scenario 标了，整个 scope 继承；同一个 scope 出现两个不同值，整批拒绝运行（同一个会话不可能同时属于两个引擎，一个 job 也只能有一个预算）。都没标时用命令行的 `--default-engine`（默认 `novaact`）与 `--default-job-timeout`（默认 300 秒，`<=0` 表示不超时）。
- **scope 名在整批里是全局的**：两个 `.feature` 文件写了同一个名字就合并成一个 job，本可并发的两条用例只能串行共享一个会话。名字带上来源前缀（`checkout-happy-path`、`admin-login`），不要用 `login`、`smoke` 这类通名。
- **未标 `@scope` 的 job 用 `<文件路径>:<行号>` 当编号**。因此 `@scope` 的值不要写成这个形状：正好等于同批某条未标 scope 的 scenario 编号时，整批拒绝运行。
- **标了 tag 就得给值**：`@scope:`、`@engine:`、`@timeout:` 后面空着会被拒绝；想用默认值就删掉这个 tag。`@timeout` 的值必须是正数秒。连冒号和值一起漏掉、只写 `@scope` 不会报错：它会被当成普通标签忽略，这条 scenario 仍各自成为一个 job。分组没生效时先用 `gherkai plan` 看分组结果。
- **预算从这个 job 启动时算起**，云端后端下包含拉取 worker 镜像等启动开销；到点这个 job 会被停下，判定记为出错、原因是超时。
- **其它 tag 都是普通标签**，没有内置语义，用来配合 `--tags` 挑一部分 scenario 运行。
- 以上校验都在起第一个 job 之前完成，任一条不满足即整批拒绝运行，不产生模型与浏览器费用。用 `gherkai plan` 提前验。

一批 `.feature` 里的 scenario 先按 `@scope` 归成 job，job 才是调度与执行的单位：

![一批 .feature 里的 scenario 按 @scope 归成 job，job 再按并发上限决定同时运行还是排队](../diagrams/writing-features-scenario-to-job.svg)

图注：job 编号在图上只写出形状，准确形状见上面的规则；两个 `.feature` 文件用同一个 scope 名，也会并进同一个 job。并发上限就是 `--max-concurrency`：上限内的 job 同时运行，超出上限的排队等空位、有位子空出来再运行，它的取值与写法见 [`running-and-results.md`](./running-and-results.md)。

**scope 与并发**：并发只发生在 job 之间，所以互不相干的用例分到不同 scope，是并发执行的前提。并发上限默认是一个 job，即默认全部 job 依次运行；分好 scope 之后还要显式调高 `--max-concurrency` 才真的并发。用 `submit` 提交到云端后端时，并发还受部署侧设定的上限约束。

下面这段出自 [`features/concurrency_and_scope.feature`](../../features/concurrency_and_scope.feature)，第二条不重新导航，直接接着第一条的页面继续：

```gherkin
@scope:browse
Scenario: 进入 OpenAI 词条页
  Given 打开 "https://en.wikipedia.org/wiki/OpenAI"
  Then "当前页面是关于 OpenAI 的维基百科词条"

@scope:browse
Scenario: 仍停留在 OpenAI 词条页
  Then "当前仍停留在 OpenAI 的维基百科词条页"
```

## Gherkin 写法的支持范围

| 写法 | 支持 | 说明 |
|---|---|---|
| `Feature` / `Scenario` | 支持 | |
| `Background` | 支持 | 展开进同一 feature 下每条 scenario 的最前面。步号从 Background 的第一步 0 起数，scenario 里书写的步跟着后移。同一个 scope 里每条 scenario 都各自重新运行一遍 Background，所以不要把导航放进 Background 又指望后一条接着前一条的页面状态 |
| `Scenario Outline` + `Examples` | 支持 | 每行数据展开成一条独立 scenario、占位符已代入，标题末尾带一段 `[@<数据行行号>]` 以便区分。未标 `@scope` 时各自成为一个 job，编号比普通 scenario 多一段数据行行号 |
| `Rule` | 支持 | 其下的 scenario 照常展开 |
| DataTable | 支持 | 挂在 AI step 上，还原成表格文本接在该步文本后面，一起交给模型 |
| DocString | 支持 | 挂在 AI step 上，多行文本原样接在该步文本后面 |
| `And` / `But` | 支持 | 承接前一条 `Given` / `When` / `Then` 的派发身份 |
| `Example:`、`Scenario Template:`、`Scenarios:` | 支持 | 分别是 `Scenario:`、`Scenario Outline:`、`Examples:` 的同义写法 |
| 中文关键字（`功能:` / `背景:` / `场景:` / `场景大纲:` / `例子:` / `假如` / `当` / `那么` / `并且` / `而且` / `但是`） | 支持 | 文件第一行须写 `# language: zh-CN`；不写这一行时中文关键字解析失败，报错指向第 1 行。关键字用哪种语言写不影响派发：`那么` 等于 `Then`（断言），`假如` / `当` 等于 `Given` / `When`（动作） |
| `*` 开头的步；前面没有可继承关键字的 `And` / `But`（scenario 第一步且这个 feature 没有 `Background`，或紧跟在 `*` 之后） | 不支持 | 判不出是动作还是断言，整批拒绝运行；改成写明关键字 |

三点补充：step 文本用什么语言与关键字用什么语言无关，中文 step 文本配英文关键字是本页所有示例的写法；命中确定性 step 的那一步，挂在它上面的 DataTable / DocString 不会传给函数，多行参数只对 AI step 有效；`.feature` 有语法错误时整批拒绝运行，消息带出错的行号与列号。

## 按引擎选写法

| | Nova Act（`novaact`，默认） | Midscene（`midscene`） |
|---|---|---|
| 被测 UI 语言 | 英文 UI。非英文页面上能导航、能判页面级语义，但「正文里是否出现某个中文词」这类断言会系统性判否（同一页面上判断是否出现英文词仍然可靠） | 不限，中文 UI 上的动作与 AI 断言同样可靠 |
| 确定性 step 语言 | Python（`steps/*.py`） | TypeScript / JavaScript（`steps/*.mts`、`steps/*.mjs`） |

被测 UI 不是英文时有三条出路，按对用例的改动量从小到大：给 scenario 标 `@engine:midscene`（或整批用 `--default-engine midscene`），前提是运行用例的环境里装了这个引擎的 worker；把断言改写成页面级语义陈述；把文本与结构检查改成确定性 step——改动最大，但这些 step 之后不再产生模型费用。

同一份 `.feature` 要在两个引擎上运行时，用到的每条确定性 step 都要在两侧成对注册，否则在缺失的那一侧这一步会换回 AI 判定。见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)。

中文 UI 的写法见 [`features/wikipedia_zh.feature`](../../features/wikipedia_zh.feature)：

```gherkin
@engine:midscene @scope:zh-midscene
Scenario: Midscene 在中文 UI 上搜索并断言
  Given 打开 "https://zh.wikipedia.org/"
  Then "页面没有出现服务器错误"
  When "在搜索框输入 人工智能 并提交搜索"
  Then "当前页面是关于人工智能的维基百科词条页"
  Then "词条首段提到了计算机或机器"
```

## 敏感信息

走 AI 的那些 step（三种执行路径里的第 ③ 条）文本会原样进模型提示（外层的双引号去掉，挂在这一步上的 DataTable / DocString 一并附上）；不论走哪一条执行路径，全部 step 原文都会写进这次运行的判定明细与运行元信息。AI 断言没过时，断言原文还会进失败原因，引擎的报告与证据里留着这次调用的指令原文和页面截图。所以：

- **不要把密码、令牌、密钥、真实客户数据写进 `.feature`**，DataTable 与 DocString 里同样不要写。
- 需要登录的用例用**只在测试环境有效**的凭据；凭据本身不写进 step 文本，由确定性 step 从环境变量读（环境变量在哪设见 [`configuration.md`](./configuration.md)）。
- 报告目录（云端后端下是产物桶）按内部资料对待：里面有 step 原文、页面截图与引擎的 AI 证据。位置见 [`running-and-results.md`](./running-and-results.md)。
- 一个例外是隧道凭据：用 `--expose-local` 测本机应用时，basic-auth 凭据由 gherkai 自动生成并内嵌在地址里，必然出现在提示与报告中——生成方式与失效时机见 [`local-app-testing.md`](./local-app-testing.md)。

## 写完先自检

写完先运行 `gherkai plan features/*.feature`。它不启动浏览器、不调用模型、不产生费用，会暴露 tag 值缺失与冲突、`@scope` 撞编号、语法错误，并逐步标出这一步走确定性 step 还是走 AI。

确定性 step 的清单查法与命中标注的读法见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)，`plan` 的完整选项见 [`running-and-results.md`](./running-and-results.md)。
