# 0047. CLI 人读输出：多行同结构的清单统一用 rich 表格渲染

> **Status:** Accepted（2026-09-30）

## 背景与问题

CLI 的人读输出里有一类内容是「多行同结构」的清单：`deploy list-workers` 的 variant 表、`list-engines` 的引擎探测结果、`list-deterministic` 的确定性 step 清单、`status` 的 job 清单。此前各自用缩进文本或手工补空格的方式排列，三处问题：手工列宽把中文表头按字符数补空格会歪，按显示宽度补又要各渲染点各写一份；内容变长（如带微秒与时区的时间戳、开发版的长 tag）撑破列宽；没有框线，在演示与截图里辨识度低。演示项目彩排时 `list-workers` 的时间列把 revision 列挤歪，是直接触发。

## 决策

- **凡是「多行同结构」的清单，人读输出用表格渲染；库选 `rich`。** 归入的输出：`deploy list-workers` 的 variant 表、`list-engines`、`list-deterministic`、`status` 的 job 清单。**不归入**：`doctor`（逐行核查，✓ / ✗ 加长文本，不是同构表）、`run` 的判定汇总与 `explain`（job → scenario → step 的树，缩进本身承载层级）、`plan`（job 分组下挂逐步标注，同为树）、进度事件流（逐行追加）。判据：一行一个同类对象、各行字段相同，才是表。
- **选 `rich` 的理由**：自带东亚宽字符的宽度表，中文表头与 ASCII 数据对齐正确；框线样式现成；按终端宽度折行；非终端输出（管道、CI 日志、文件）自动不带颜色。被拒：`tabulate`——全角宽度要另装 `wcwidth` 才对，不随终端宽度调整；继续手写对齐——每个渲染点各一份宽度逻辑，已经出过撑歪的事故；只给 `list-workers` 加框线——同一个 CLI 一处带框线、其它清单缩进文本，观感割裂。
- **渲染面单点**：`gherkai_runtime.textui.render_table(headers, rows, *, width=None) -> str`。`cli` 与 `deploy` provider 两个前端包都依赖 `gherkai-runtime`，把这个呈现件放在两者共同的依赖层，避免 provider 反向依赖 `cli`（包级循环）或各复制一份；`rich` 因此成为 runtime 的依赖。core 不涉及。表格样式固定：圆角框线（`box.ROUNDED`）、无颜色、无高亮、不解析标记语法；宽度取终端列数（至少 80），非终端时取 160，避免日志里无谓折行。
- **`--json` 不变**：机读形态仍是原来的 JSON 文档（ADR 0041 决策三），表格只是文本视图。
- **测试只断言内容，不断言排版**：断言单元格文本出现、不出现，不断言空格数、框线字符或整行文本；表格渲染本身在 runtime 有独立单测（宽度对齐、无 ANSI 序列、宽度参数）。此前已有的按整行断言的测试改为按内容断言。

## 影响面

- `runtime/gherkai_runtime/textui.py` 新增；`runtime/pyproject.toml` 依赖加 `rich`。
- `cli/gherkai_cli/__main__.py` 的 `list-engines`、`list-deterministic`，`cli/gherkai_cli/render.py` 的 `render_run_state`，`deploy_aws/gherkai_deploy_aws/workers.py` 的 `list_workers` 改用 `render_table`；各自的首行说明与空清单提示保留。
- 用户指南里提到「示例行」的措辞改为「示例列」；CHANGELOG 记为变化。

## 不做 / 延后

- 不给 `run` 汇总、`plan`、`explain` 改表：它们是树，表格会丢层级。
- 不引入颜色与高亮：与 ADR 0039「产品面文案」的克制一致，也免去终端配色差异；将来要做也是单独决策。
