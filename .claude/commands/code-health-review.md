---
description: 代码健康度复盘（全部生产代码：死代码/过时低效/违背 ADR，对照 code+ADR）
---

Read `docs/code-health-review.md` 并**严格按其中记录的方法**执行代码健康度复盘任务。

要点（细节以 `docs/code-health-review.md` 为准，不在此复制以免漂移）：
- 这是重活，覆盖全部生产代码（core + runtime + cli + 各引擎 worker + deploy_aws 含 lambdas，tools/ 注释与死代码同查）——起 workflow 并行分片 review，别单线程扫。
- 文件里标 **【强制】** 的步骤不可跳过：违背 ADR 类必读相关 ADR 核实、死代码类必 grep 确认无调用（含 worker 子进程入口/组合根注入/Lambda 字符串装配入口）、违背/中高置信死代码类对抗验证。
- 三类：DEAD / STALE_INEFFICIENT / VIOLATES_ADR（后者最高价值）。STALE 含 **code 注释的引用方向违规**（引 journey / 裸 WP 编号 = 悬空指针；判据权威在 CLAUDE.md 文档纪律，`.md` 文档归姊妹 doc-health）。
- 客观类（真死代码/bug/违背）确认后改、每批跑测试；重构/主观类先出报告待操作者批。
- 提交前 git status 自检，别把调试残留误提交。
