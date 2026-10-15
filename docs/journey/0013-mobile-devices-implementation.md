> 类型: 进度总纲

# 移动真机支持（1.5）：实施进度总纲

分支 `feat/v1.5-mobile-devices`。设计已定稿为 ADR 0048 到 0053（2026-10-15），spike 与方案总稿两份 journey 随之删除；本文只记实施阶段的现场：做到哪、下一步、documenting 清单。实施完成后删除。

## 现场

- 2026-10-15：ADR 0048 到 0053 写成并通过复审；CONTEXT.md 词表加目标、界面类型、应用别名、远程访问会话、驱动适配器、能力探测、确定性 step SDK 七条，旧词条三条改写；ADR 0019 / 0035 / 0036 的 Status 头标部分取代，0022 / 0024 / 0034 / 0042 / 0044 加互链。spike 脚本 `engines/midscene/spikes/06-devicefarm-appium.mts` 保留为真机能力探测的雏形，实施时演化成 `tools/` 下的真机重新探测工具。
- 2026-10-15（续）：定稿后的专家复审与 Codex 同僚复核发现 0051 的事件契约与收尾顺序、预算分层、隧道令牌载体、scenario 间复位、evidence 衔接、Job 形态六处要改；修订建议与定稿前实测结论在 journey 0014（待批），批准后先改 ADR 再实施。
- 实施尚未开始。建议次序：0049（能力自述增键，零风险、可独立发）→ 0048 与 0053（core 的 tag 解析、Job 字段、配置文件）→ 0050（注册面）→ 0051 与 0052（worker 设备模块）→ 文档与 skill。

## documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总，实施期逐项完成）

- user guide：新增 `engines.md`（引擎能力矩阵，差集测试守）与设备主题页（`@device` 与 `@app` 写法、应用别名、费用含取设备开销、限制：国内消费级应用线上包自退、iOS 26 的 DOM、Compose 无标识、数据驻留 us-west-2 与 400 天）；`writing-deterministic-steps.md` 加 webdriver 句柄、上下文六字段、材料规则、验收定位；`configuration.md` 加 `gherkai.toml`；`cloud-backend.md` 加三方权限表与 Device Farm 项目；`local-app-testing.md` 改隧道鉴权为令牌换 cookie；`troubleshooting.md` 加会话类错误与三个新错误类别。
- skill：路由表加设备；`references/` 加设备写法；确定性 step 参考按 0050 决策 4 改（期望来自需求、材料只定位置、来源平铺、agent 开会话须项目约定、长流程拆步）；评测集加设备用例（写 `@device` 用例、写一条 webdriver step、处置 precheck_failed）；不出现「先 AI 后硬化」类流程暗示。
- docs/internals：设备会话与 Appium 适配的机理解读一篇（权威指回 0051 / 0052）；`cli-json-contract.md` 加 `targets`、`available_targets`、三个新错误类别、session 为 null 的 scope 形态。
- CONTRIBUTING：发版后验证项加真机验收矩阵；`tools/` 的真机重新探测工具使用方法。
- CHANGELOG 与 README 门面一句；`docs/internals/README.md` 登记新篇。

## 实施期要核的点（ADR 已定、实施时顺手验证）

- 0051 决策 13 的边缘策略由 gherkai 的隧道实现生成后，在三种浏览器上各走一次（设计阶段已用手写策略文件验过）。
- 0051 决策 11 的脱敏：一次故意建连失败的真机执行，核报错文本里的签名与令牌已被盖住。
- 0049 决策 8 的差集测试在 CI 里如何取得两个 worker 的能力自述（直接调起 `--capabilities`，或各 worker 自测同步维护的快照）。
