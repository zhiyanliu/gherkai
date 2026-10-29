# 引擎能力矩阵

两个引擎各能在什么测试目标上运行、确定性 step 在那个目标上用哪种句柄、默认用哪个模型、费用按什么公式计，汇总在一张表里。表里的目标与默认模型取自每个引擎 worker 自己的能力自述，`gherkai doctor` 的 `engines.targets.<引擎>` 与 `engines.model.<引擎>` 两行显示的就是这台机器上实际装的 worker 自报的值；两者不一致时以 `doctor` 为准，多半是本机 worker 与本文描述的发行版不同，或用环境变量换了模型。确定性 step 怎么写见 [`writing-deterministic-steps.md`](./writing-deterministic-steps.md)，模型怎么换见 [`configuration.md`](./configuration.md)。

## 矩阵

一行是「一个引擎在一个目标上」。测试目标由设备（桌面、Android、iOS）与界面类型（网页、应用）组成；表里没有的组合当前不受支持。

| 引擎 | 测试目标 | 确定性 step 的句柄 | 默认模型 | 计价（公式） |
|---|---|---|---|---|
| Nova Act（`novaact`） | 桌面网页 | `playwright` | `nova-act-v1.0` | Nova Act 服务按智能体工作时长计费，加云端浏览器会话按时长计费 |
| Midscene（`midscene`） | 桌面网页 | `playwright` | `us.openai.gpt-5.6-terra` | Bedrock 按模型的输入与输出 token 数乘各自单价计费，加云端浏览器会话按时长计费 |

读法：

- **测试目标**：这个引擎的 worker 能在上面建会话并执行 step 的目标。设备目标会随后续版本加入，加入时这张表、`gherkai doctor` 的目标行与 `gherkai list-deterministic` 的目标列同步变化。
- **确定性 step 的句柄**：在该目标上，项目 `steps/` 里注册的确定性 step 拿到的是哪种对象。`playwright` 是 Playwright 的页面对象。`gherkai list-deterministic` 的「目标」列显示每条 step 实际可用的目标。
- **默认模型**：不设任何模型环境变量时 worker 使用的模型，`gherkai doctor` 的 `engines.model.<引擎>` 行显示本机实际会用的那个。
- **计价**：只给公式，单价以 AWS 当时的标价为准，金额以你账户的账单为准；量级见 [`running-and-results.md`](./running-and-results.md) 的费用一节。

## 用 `doctor` 与 `list-deterministic` 核对

```bash
gherkai doctor                                   # engines.targets.<引擎>：本机 worker 支持的测试目标（带会话上限的目标附分钟数）
gherkai list-deterministic --engine midscene     # 「目标」列：每条确定性 step 在这个引擎上实际可用的目标
```

`list-deterministic` 的「目标」列是两份声明的交集：step 注册时声明的目标，与这个引擎的 worker 支持的目标。一条 step 声明了该引擎不支持的目标时，这一格会单独注明「声明了「…」，此引擎不支持」：那条实现在这个引擎上永远不会被调用，写它的人应当知道。`--json` 里 `targets` 是 worker 原样报出的声明，`available_targets` 是交集，两者分开给出。
