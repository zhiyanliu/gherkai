# 0039. 用户可见面不带内部指代：产品文案与文档分层

> **Status:** Accepted（2026-09-09）—— 两面均已实装并有护栏：产品文案面（`cli/tests/test_user_facing_messages.py`）、文档面（`cli/tests/test_package_readmes.py`）。本 ADR 是 CLAUDE.md 代码纪律「产品面文案不带内部指代」与文档纪律「README / DEVELOPMENT 分层」两条约定的决策与理由所在；约定文件只留规则与指针。

## 背景与问题

项目的设计知识全部以 ADR 编号、决策号与一套内部机制名（不变量 / 定位链 / 被拒方案 / 重议闸门 / 实测项 / 接缝契约 / 组合根 / 皮…）组织，这对写代码与写 ADR 的人是高效的索引。但 v1.4.0 首发前后暴露出它漏到了**使用者能看到的面**上：

- **产品文案**：`--help`、提示、警告、错误、worker/Lambda 日志里带着「（定位链四级全 miss，ADR 0037 决策 3）」「（ADR 0037 决策 6 三态）」这类尾注。AST 扫描生产代码的非 docstring 字符串字面量，五个 Python 包命中 51 处、midscene 的 `.mts` 5 处。使用者手里没有仓库，这些既读不懂也查不到，还挤掉了「怎么办」的位置。
- **包页面**：六个发行包的 PyPI / npm 长描述就是各包目录的 `README.md`（pyproject `readme` / npm `files`），而它们一直按 contributor 文档写：ADR 提及 11–26 处不等、模块布局、跑测试、spike、从 checkout 跑，且满是 `../docs/adr/…` 相对链接——在 PyPI/npm 页面上全是死链。pyproject / package.json 的 `description`（页顶 Summary 一行）同样写着「组合根……（ADR 0016）」。根 `README.md`（仓库首页）亦以 ADR 编号组织叙事。

用户的判断（本 ADR 的起点，用户自己先改了一条 `compose.py` 文案）：**给用户看的东西不该带内部指代**。

## 决策

**一条原则、两个面**：凡使用者能看到的文字——终端输出/日志、仓库首页、发行包页面——只说**发生了什么、为什么（产品语言一句）、怎么办**；ADR 编号、决策号、内部机制名、内部函数名、「见模块头/接缝契约」这类指针**留给维护者**，住在紧邻的代码注释、docstring、contributor 文档里。判据 = 「装了包 / 点开仓库首页、没读过 ADR 的人看得懂且用得上」。

### 面一：产品文案（代码里的字符串）

- 范围：argparse help/description/epilog、`print`/stderr、CLI 的进度提示、provider 的输出、警告、展示给用户的异常文案（`WorkerVariantError` / `WorkerCommandError` / `WorkerNotFoundError` / 校验用户输入的 `ValueError`）、Lambda 日志行、worker stderr。
- 不写：`ADR NNNN`、`决策 N`/`决定 N`、内部机制名（不变量/定位链/被拒方案/重议闸门/实测项/接缝契约/模块头/组合根装配）、内部函数名、分层行话（皮/provider 侧作代码层义）。
- 搬家规则：被删掉的指针若对维护者有价值，进紧邻注释或 docstring；docstring/注释**不在**本约束范围、鼓励保留 ADR 指针。
- 例外：只在内部 API 被误用时才触发的契约型异常（`ValueError`/`RuntimeError`，永不因用户输入触发）可留一句点名内部符号的短诊断，但同样不写 ADR/决策字样。
- 实装时顺带的原则性修正：Nova worker 的信号 handler 曾在 handler 内 `log()`——它不只是文案问题，还撞出 stderr `BufferedWriter` 重入崩溃；文案归安全点补打（细节在 [0024](./0024-worker-core-protocol.md) 终止契约）。

### 面二：文档分层（README / DEVELOPMENT 成对）

按**读者**切文件而非按目录切：使用者向 = 根 `README.md` + 各包 `README.md`；contributor 向 = 根 `DEVELOPMENT.md` + 各包 `DEVELOPMENT.md`。使用者向只写「这是什么、装法、用法、配置、退出码/错误怎么办」，不写 ADR 编号/决策号/内部机制名/目录结构/开发环境/测试/spike/发布流程/设计叙事；这些全归 contributor 向并带 ADR 指针。四层只差**去向与链接形态**：

| 文件 | 去向 | 链接 |
|---|---|---|
| 根 `README.md` | 仓库首页（GitHub）；末尾「深入了解」一节链 CONTEXT / guides / adr / DEVELOPMENT | 相对链接可（GitHub 渲染） |
| 各包 `README.md`（`cli/` `core/` `runtime/` `deploy_aws/` `engines/novaact/` `engines/midscene/`） | **逐字上 PyPI / npm 页面**（pyproject `readme` / npm `files`）；改动随**下一个 tag** 才生效——PyPI 已发版本的长描述不可改 | **只用绝对 URL**（页面上相对链接全是死链；仓库内文件用 `https://github.com/zhiyanliu/gherkai/blob/HEAD/<path>`，`HEAD` 跟默认分支、不绑分支名）；最多末尾一句「设计文档见仓库 docs/adr」 |
| 根 `DEVELOPMENT.md` | contributor 入口：版本线叙事、目录结构、从 checkout 跑、测试、spike、发布与版本、各包 DEVELOPMENT 索引、纪律/术语/ADR 指针 | 相对链接 |
| 各包 `DEVELOPMENT.md` | 该包 contributor 文档：模块布局、从 checkout 跑、测试、维护者踩坑（真踩过的坑一条不丢）；**不进发行包**（wheel 本就不含，sdist 经 hatch `exclude` 排除） | 相对链接 |

页顶 Summary（pyproject / package.json 的 `description`）同属包页面，同一规则。搬家不是删：从使用者向文件移出的每条事实与踩坑，必须在对应 DEVELOPMENT.md 里找得到（实装时按旧文件逐字对照过）。

### 护栏

- `cli/tests/test_user_facing_messages.py`：AST 扫五个生产包全部**非 docstring** 字符串字面量 + midscene `.mts` 去注释后按行扫，禁词表 = ADR 编号 / 决策·决定编号 / 内部机制名 / 内部函数名；Python 与 TS 同一张表（曾因 TS 表更松漏掉一处「组合根装配错误」）。
- `cli/tests/test_package_readmes.py`：根 README 与进包的六份 README 零禁词，包 README 零相对链接（正则 `](../` `](./` `](x.md`），pyproject / package.json `description` 零禁词，根与每包都有 `DEVELOPMENT.md`；扫描面路径缺失即失败（包搬家不许让护栏变绿）。
- **护栏管不到的**：正则抓不住的行话（皮 / 装配 / 唯一真源 / 产品本体层）与「使用者读得懂吗」的判断，靠 review——两轮对抗核验都在这一档抓到过遗漏（runtime 页面整篇行话、`--grace` 漏标「仅 run」、定位链顺序写反）。

## 代价与权衡

- **双份文档**：每个包两份 markdown，改机制时要同时看使用者向与 contributor 向两处；换来的是两类读者各自拿到对的东西，且包页面不再暴露实现细节。
- **延迟生效**：包 README / Summary 的改动要等下一个 tag 才上 PyPI/npm（1.4.0 页面即带着 contributor 文档发出去了，不可改）——发版前把这两处也当作发布物核对。
- **禁词的误伤面**：正则对中文机制名是逐词匹配，「组合根」在 Summary 里也被禁——这是有意的（它对使用者同样是行话）；契约型异常的例外条给了内部符号一个口子，不至于把开发者诊断也拉平成人话。
- **文案变短了**：去掉「为什么」的长尾注后，个别文案失去了对维护者的自解释；由紧邻注释补回，对使用者反而更短更准。

## 被拒方案（护栏，防未来重踩）

- **把 contributor README 直接当 PyPI / npm 长描述**（v1.4.0 首发时的实态）：页面满是 ADR 编号、模块树、跑测试说明与相对死链，装了包的人看不懂也用不上。
- **只把根 README 分层、包 README 不动**：包页面恰是最多「没有仓库的人」看到的面，不能例外。
- **文案里保留 ADR 指针「给维护者看」**：维护者有仓库、有注释、有 docstring，不需要借用户的终端传话；用户终端只有用户在看。
- **用环境变量/详细模式切换是否显示内部指代**：两套文案等于两倍维护，且默认面仍会漏。
- **单份 README、分「使用者」「开发者」两节**：PyPI/npm 拿的是整份文件，节切分挡不住 contributor 内容上页面；分文件才能让「进包」这条线物理成立。
- **包 README 用相对链接指 `../docs/…`**：PyPI/npm 页面上全是死链；用 `blob/HEAD/` 的绝对 URL。
- **中文文件名**（journey 曾用）：文件名是引用锚点，要在 URL/终端/grep 里稳定可打——文档文件名一律英文 kebab（CLAUDE.md 文档纪律）。

## 重议闸门

- 有了文档站点（如 mkdocs）→ 包 README 可缩成「装法 + 站点链接」，contributor 内容与 guides 一并进站点；本 ADR 的分层原则不变、载体变。
- 国际化（英文文案/文档）→ 禁词表与护栏需按语言各立一份；原则不变。
- 若某类内部机制名成为使用者也需要理解的产品概念（如「variant」「默认指针」已是），从禁词表移出并进 CONTEXT/包 README 解释——判据仍是「使用者需要它才能用对」。

## 对既有文档与 code 的影响

- CLAUDE.md：代码纪律「产品面文案不带内部指代」与文档纪律「README / DEVELOPMENT 分层」两条压回规则 + 判据 + 护栏 + 指向本 ADR。
- [0037](./0037-distribution-and-packaging.md) 被拒方案里「contributor README 当长描述」一条改为指向本 ADR。
- 两条护栏测试的 docstring 指向本 ADR。
