# gherkai 用户指南

给使用 gherkai 的人和替你操作它的 AI agent。这里讲**怎么用**：安装、写用例、运行、看结果、部署云端后端、配置、排错与常见问题。每个主题只在一篇里展开，其余页面只给链接。想了解内部机理请看 [`docs/internals/`](../internals/README.md)；仓库首页 [`README.md`](../../README.md) 是 30 秒版。

| 页 | 回答什么问题 | 这一篇负责的主题（其余页只给链接、不展开） |
|---|---|---|
| [`getting-started.md`](./getting-started.md) | 装什么、要哪些 AWS 前置、第一次怎么完整运行 | 安装形态（CLI、两个引擎 worker、部署 extra）、AWS 凭证与 region、需开通的服务、`doctor` 自检、用 AI agent 上手、手敲 CLI 的最小四步 |
| [`writing-features.md`](./writing-features.md) | `.feature` 怎么写才能稳定运行 | 最小 `.feature` 骨架与 Gherkin 支持范围（含中文关键字）、AI 步与确定性步的分工、断言怎么写、`@engine` / `@scope` / `@timeout` 标签、双引号地址直接导航的内建行为、按引擎选写法（含非英文 UI）、投票 |
| [`writing-deterministic-steps.md`](./writing-deterministic-steps.md) | 精确判定的步骤怎么自己写 | `steps/` 目录约定、Python 与 TypeScript 两侧并排的注册 API、`description` / `example` 的作用、加载失败怎么表现、如何核对与带到云端 |
| [`running-and-results.md`](./running-and-results.md) | 四种组合（执行方式 × 执行后端）怎么选、结果在哪、退出码什么意思 | `plan` / `run` / `submit` / `status` / `explain` 的用法与差别、`list-engines` / `list-deterministic` / `doctor` 的用途与常用选项、本机与云端两个后端、`run` / `submit` 的常用选项、退出码（部署方命令的退出码归云端后端页）、报告与证据在哪、费用量级、机读输出的入口 |
| [`local-app-testing.md`](./local-app-testing.md) | 被测应用只在本机或内网时怎么测 | `--expose-local` 的前置、行为、限制与存活时间 |
| [`cloud-backend.md`](./cloud-backend.md) | 团队怎么部署与维护云端后端 | `gherkai deploy` / `destroy`、VPC 三档、版本与升级、worker 镜像 variant 与默认指针、清理、部署机权限、`deploy` / `destroy` 的退出码、常见错误 |
| [`configuration.md`](./configuration.md) | 有哪些配置项、各自在哪里生效 | 环境变量与选项总表：模型选择、region、超时与停止宽限、报告与 steps 目录、worker 拉起、云端资源名与网络的单项覆盖、由 gherkai 注入的变量 |
| [`troubleshooting.md`](./troubleshooting.md) | 报错了先看哪 | `doctor` 的读法、按症状分表的处置（安装与版本 / 凭证与 region / 模型 / 引擎与判定 / 云端 / 提交后进度停住 / 其它退出码 2）；确定性 step 加载失败的表现归 writing-deterministic-steps，这里只留指针与 worker 自述失败两行 |
| [`faq.md`](./faq.md) | 决策前的疑问：必须先部署云端后端吗、AI 判定能不能当门禁、和别的测试框架什么关系 | 跨页问题的一句话结论加去哪读；就地拥有的选型类问题：与 Playwright / Cucumber 的关系与迁移、浏览器与视口、无 JUnit XML 等第三方报告格式的输出 |

## 约定

- 命令示例以 `gherkai` 已在 PATH 为前提；示例里的 `<占位>` 用你自己的值替换。
- 涉及费用的地方给量级，以你账户的 AWS 账单为准。
- 本指南描述的是最新发行版；某个版本对应的文档请看该版本 tag 下的同一路径。
