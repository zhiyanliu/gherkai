# 确定性 step 的写法：从「能注册」到「稳、可诊断、可维护」

本文给写 step 代码的人（测试开发）用。最小模板、签名、判定映射、目录遍历规则与「用错了会怎样」表在 `references/engines.md` 第 3 到 6 节，本文不复述，只讲把一条 step 写对之后怎么写稳、写得失败时能诊断、写得两侧能长期同步。完整的人读写法：
https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-deterministic-steps.md

## 1 先判该不该写成确定性 step

- **写**：URL、元素存在或可见、精确文本、数值与计数这类检查；必须可复现、要快；AI 断言反复抖动而检查本身能被机械定义（「购物车角标是 1」）。
- **成本与速度也是判据**：AI 步每次判定都调一次模型，投票再乘票数，一步要几秒到几十秒（模型往返与截图）；确定性 step 零模型费用、毫秒级完成，整套用例的墙钟与云端浏览器会话时长都跟着降。出现频次高的检查优先写成确定性：`Background` 里每条 scenario 都重做的前置检查、`Scenario Outline` 每行数据都要过的断言、被要求投票的断言。一条 5 步的 scenario 在默认模型上约几美分，乘上用例数、数据行数与每天的运行次数，这笔账不小。
- **不写**：语义判断（「看起来像错误页」「结果相关」）、页面结构常变、选择器只能靠猜。硬写只会得到一条脆弱的选择器，失败时比 AI 判否更难说清。这类改 AI 步的措辞成页面级陈述，或投票。
- 动作步（填表、点击）也能写成确定性，只在 AI 操作不可靠且选择器稳定时写；导航不必写，双引号内的地址已由内建捷径直接打开。

## 2 一条 step 的四个部分

**模式**。匹配是子串搜索、不锚定，一条 step 文本命中多条模式即记 error，所以模式要窄：带引号参数与特征词，参数组写 `[^"]+`（不写 `.+`，第二对引号会被贪婪吞掉），正则里不写 `Given` / `Then` 关键字。两侧方言只差具名组：Python `(?P<name>…)`，Midscene `(?<name>…)`。别让新模式与内建的 `页面地址(?:精确)?匹配 "…"` 有重叠的命中面。

**元数据**。`description` 一句话说这一步判什么，是 `gherkai list-deterministic` 与 `gherkai plan` 打给用例作者看的那行；`example` 是用例作者会照抄进 feature 的完整 step 文本（含关键字）。**`example` 的措辞就是接口**：改它等于改所有用到它的 feature，定下来别轻易动。

**handler**。签名见 `references/engines.md` 第 3 节；Python 侧必须是同步函数，写成 `async def` 的那一步直接记 error。handler 只拿到上下文与具名组，DataTable 与 DocString 不会传进来。同一 scope 的 scenario 串行共享一个浏览器会话，所以 handler 别假定页面是新鲜的、别在断言步里导航、别留下会改变后续 step 的状态（新开标签页、切换 frame 不复位）。

**失败消息**。确定性 step 不产截图与模型思考，`gherkai explain` 里这一步只有一行原因。消息必须自带现场：当前页面地址、用的选择器、期望值与实际值（长文本截断）。没有现场的失败消息在云端只剩「断言未过」四个字，人与 agent 都无从下手。

## 3 等待与判定：三条规则

1. **用带等待的判定，不用瞬时值、不用固定等待**。`isVisible()` / `is_visible()` 取的是当下那一瞬间，页面还在加载就判否，这是确定性 step 假失败的头号来源。Python 侧用 Playwright 的 `expect(locator).to_be_visible(timeout=…)` 一族（自动重试到超时，超时抛 AssertionError，这一步记 failed）；Midscene 侧用 `locator.waitFor({ state, timeout })` 与 `page.waitForURL(...)`。固定 sleep 既慢又照样抖。
2. **等待超时不是断言**。`locator.wait_for(...)` / `locator.waitFor(...)` 超时抛的是 Playwright 的 TimeoutError，这一步会记 error 而不是 failed，判定统计与汇报模板都会把它当执行错误。要让它记 failed，就捕获后转成 AssertionError（Python）或 DeterministicAssertion（Midscene），并在转换时补上现场。
3. **给等待一个几秒的上限**。Playwright 默认 30 秒，一条 step 等满 30 秒会吃掉这个 scope 的墙钟预算（`@timeout`），且拖慢整轮反馈。按页面实际响应给 3 到 10 秒。

## 4 组织：判定逻辑与注册分离

- `steps/<主题>.py` 与 `steps/<主题>.mts` 只做注册（薄壳）；判定逻辑放 `_` 前缀的辅助模块（`_checks.py`、`_checks.mts`，或整个 `_pages/` 目录），step 文件相对导入它。理由有三：判定逻辑能单测；两侧共享同一份选择器表；辅助模块不会被当成 step 文件加载（Midscene 侧一条都不注册的文件会让 worker 拒绝启动）。
- Midscene 侧的辅助模块里 `import type { Page } from "playwright"` 只当类型用，编译期擦除；**运行期不要 import playwright**：step 文件所在目录没有 node_modules，worker 只把 `@gherkai/worker-midscene` 这一个包名重定向到自己那份，别的包名解析不到。Python 侧 `from playwright.sync_api import expect` 可以直接用，worker 环境自带。
- 两侧成对：同一条判定两份实现，模式语义相同、`description` 与 `example` 同文；改一侧同步另一侧，用 `gherkai list-deterministic --engine novaact` 与 `gherkai list-deterministic --engine midscene` 各核一遍。只写一侧，另一引擎上这一步会静默换回 AI 判定。
- 文件按主题命名（`navigation.py`、`cart.py`），模式按用例作者的语言写，不按实现（「购物车角标是 N」，不是「cart-count 文本等于 N」）。

## 5 本地零费用核对与单测

写完先做三件不开浏览器会话、不调模型的事：

```bash
gherkai list-deterministic --engine novaact --steps-dir steps    # 清单里有你那条、模式与示例如预期
gherkai list-deterministic --engine midscene --steps-dir steps   # 另一侧也在
gherkai plan features/<x>.feature --steps-dir steps               # 该命中的步标了「确定性」、没有 ⚠ 冲突、AI 步没被误伤
```

判定逻辑用真浏览器在本地页面上单测，不花云端费用、不需要 AWS 凭证：

- Python：测试写在 `steps/test_<主题>.py`（worker 加载时跳过以 test_ 开头的文件），直接 `import _checks`（pytest 会把测试所在目录放进导入路径），用 `sync_playwright()` 起一个本地浏览器、`page.set_content(...)` 造出目标页面，断言通过与失败两条路：失败必须是 AssertionError 且消息带选择器与页面地址。项目的开发依赖需要 pytest 与 playwright（浏览器用 `playwright install chromium` 装一次）。
- Midscene：测试写在 `steps/<主题>.test.mts`（worker 跳过 `.test.` 文件），`node --test steps/*.test.mts` 直接执行（Node 22.18 起原生执行 `.mts`；更早的 22.x 写 `node --experimental-strip-types --test steps/*.test.mts`），或用 vitest。开发依赖需要 playwright 与 `@gherkai/worker-midscene`（取 DeterministicAssertion 与类型）。
- 测的是辅助模块里的判定函数，不是注册文件：Python 的注册文件用相对导入，只在 worker 的加载环境里成立。
- 单测与 `plan` 都过之后才值得实际运行；实际运行开云端浏览器会话、花真钱，只在人要结果时做。

## 6 改一条已在用的 step

- 改判定逻辑：单测，然后 `list-deterministic` 与 `plan`。
- **任何改动**（逻辑、措辞、新增、删除）云端都要重新构建镜像并 `gherkai deploy push-worker` 才生效：云端 worker 读的是镜像里那份，本机 `plan` 的标注不代表云端。汇报里提醒一句。
- 改措辞（`example`）：所有用到它的 feature 都要跟着改。宁可加一条新模式、旧模式保留一段过渡期，但两条模式不得同时命中同一句 step 文本。
- 删 step：先全文搜索全部 feature 确认没人用；删后那些 step 会静默换回 AI 判定，`plan` 里标注消失是唯一信号。

## 7 症状速查

| 症状 | 多半是 | 处置 |
|---|---|---|
| 时不时判否，手动打开页面明明能看到 | 用了 `isVisible()` / `is_visible()` 这类瞬时值，或没等页面就读文本 | 换成带等待的判定（第 3 节规则 1） |
| 判定不成立却记 error 而不是 failed | 抛的是 TimeoutError 或别的异常 | 捕获后转成 AssertionError / DeterministicAssertion，补现场 |
| Nova Act 上这一步记 error，Midscene 上正常 | Python handler 写成了 `async def` | 改成同步函数 |
| Midscene 上 `plan` 没有确定性标注，Nova Act 上有 | Midscene 侧文件扩展名是 `.ts` / `.js`（收集时静默跳过），或只写了 Python 一侧 | 改成 `.mts`，或补另一侧 |
| worker 起不来，说某文件一条 step 都没注册 | 辅助模块没加 `_` 前缀被当成 step 文件；或按文件路径 import 到了另一份包 | 加前缀或搬进 `_pages/`；import 只写包名 |
| 一步记 error 说命中多条模式 | 模式太宽或与内建重叠 | 收窄，带引号与特征词 |
| 云端失败只剩一句「断言未过」 | 失败消息没带现场 | 消息里带页面地址、选择器、期望与实际 |
| 本机改了 step，云端行为没变 | 没重新构建镜像并 `push-worker` | 见 `references/cloud-backend.md` |

## 8 修完怎么汇报

不管是修一条 step、加一条 step 还是查一个静默问题，汇报固定带三样，缺一样人就得再问一轮：

1. **根因与改法**：哪一行为什么错、改成了什么；同目录顺带发现的其它问题点出来，动没动、为什么。
2. **核对结果**：两个引擎的 `gherkai list-deterministic --engine` 清单里有没有这条、`gherkai plan` 的标注是什么，与改前对照说清变没变。
3. **以后怎么自查**：明确写给人一句「以后改完 steps/ 先对两个引擎各查一遍清单，再用 plan 看标注」。只写了一侧、扩展名不在加载范围、模式没命中，加载时都不报错，只有这两条命令能照出来。

汇报是给人的：直接给内容，不提「按 skill 第几节」「见 references/…」这类你自己的读物。
