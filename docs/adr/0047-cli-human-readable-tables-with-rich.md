# 0047. CLI 人读输出：清单用表格、层级用树、状态上语义颜色，统一由 rich 渲染

> **Status:** Accepted（2026-09-30）

## 背景与问题

CLI 的人读输出里有一类内容是「多行同结构」的清单：`deploy list-workers` 的 variant 表、`list-engines` 的引擎探测结果、`list-deterministic` 的确定性 step 清单、`status` 的 job 清单。此前各自用缩进文本或手工补空格的方式排列，三处问题：手工列宽把中文表头按字符数补空格会歪，按显示宽度补又要各渲染点各写一份；内容变长（如带微秒与时区的时间戳、开发版的长 tag）撑破列宽；没有框线，在演示与截图里辨识度低。演示项目彩排时 `list-workers` 的时间列把 revision 列挤歪，是直接触发。

## 决策

- **凡是「多行同结构」的清单，人读输出用表格渲染；库选 `rich`。** 归入的输出：`deploy list-workers` 的 variant 表、`list-engines`、`list-deterministic`、`status` 的 job 清单、`doctor` 的检查项（结果 / 检查项 / 说明三列；说明列长文本由表格折行，此前以「长文本不适合表格」排除它是判断失误，同日修正）。判据：一行一个同类对象、各行字段相同，才是表。
- **层级结构用树渲染。** `run` 的判定汇总（job → scenario → step，下挂原因与产物地址）、`plan`（job → scenario → step 与派发标注）、`explain`（scope → scenario → step → AI 调用 → 推理与截图）三处此前靠两格缩进承载层级，改为 `rich` 的 `Tree`：引导线代替缩进，每一行属于哪个上级一眼可见。节点文字与此前相同，只有一处例外：`plan` 的标题行与统计行合并为根节点一行，`run` 汇总的标题行与总状态合并为根节点一行、总墙钟时长与成本合计作为根节点的子节点（不再有 `=====` 装饰）；其余节点的文字与字段名（`votes N/M`、`message:`、`thought:`、`screenshot:`、`error:`、`act N vote=`、`← 确定性:`）逐字不变，多行推理的续行仍对齐到 `thought: ` 之后，skill 与文档据此读取。**树不折行**：长的地址、原因、推理文本保持一行、由终端自行软换行，与此前纯文本一致，agent 复制产物地址不会被截断；实现上给树一个远超终端的名义宽度，表格才按终端宽度在单元格内折行。
- **不改形态的**：进度事件流（逐行追加、边执行边打印，没有整体结构可排）。
- **颜色只作语义标记，映射沿用 ADR 0031 决定二的视觉映射并翻译到终端基础 16 色**：通过绿、失败红、出错紫红（报告页的琥珀在基础色里无对应）、中止亮红（severity 最高、比出错更显眼）、跳过淡显（对应报告页的弱化灰）、运行中青、待执行蓝；次要信息（会话 id、产物地址、成本）淡显；`plan` 的派发标注绿、冲突黄；`doctor` 的结果列 ✓ 绿、✗ 红、- 黄。两条纪律：符号与文字仍是信息的主载体，去掉颜色不丢任何信息；只用基础 16 色，跟随终端主题，不用背景色与加粗。开关：`NO_COLOR` 为非空值或 `TERM=dumb` 不上色，`FORCE_COLOR` 为非空值上色（如 `| less -R`），否则看标准输出是否为终端（管道、重定向、CI 日志、测试捕获下不发任何 ANSI 序列）；非空语义同 no-color.org 与 rich。用户文本（step 原文、失败消息、推理）不解析标记语法，方括号不会被当成样式。
- **选 `rich` 的理由**：自带东亚宽字符的宽度表，中文表头与 ASCII 数据对齐正确；表格、树、样式都是现成组件；非终端输出自动无色。被拒：`tabulate`——全角宽度要另装 `wcwidth` 才对，只有表格、没有树，不随终端宽度调整；继续手写对齐与缩进——每个渲染点各一份宽度逻辑，已经出过撑歪的事故；只给 `list-workers` 加框线——同一个 CLI 一处带框线、其它清单缩进文本，观感割裂；颜色一律不用——观感是这一层的目的，`rich` 的自适应把副作用压到了可接受。
- **渲染面单点**：`gherkai_runtime.textui`（`render_table` / `render_tree` / `TreeNode` / `status_text` / `styled` / `plain` / `Text`）。`cli` 与 `deploy` provider 两个前端包都依赖 `gherkai-runtime`，把呈现件放在两者共同的依赖层，避免 provider 反向依赖 `cli`（包级循环）或各复制一份；`rich` 因此成为 runtime 的依赖，`cli` 与 provider 不直接 import rich、只经 textui（包括 `Text`）。core 不涉及。样式与宽度规则固定在 textui：圆角框线（`box.ROUNDED`）；表格宽度在终端取实际列数（窄终端也按实际列数，让 rich 自行收窄），非终端时不折行（管道、日志、CI 里每行保持一行，便于 grep）；**表格里标识列永不折断**（scope_id、session、示例、模式、tag、地址是逐字复制的对象），只有各渲染点显式声明的说明类列（`doctor` 的说明、`list-deterministic` 的说明、`list-engines` 的拉起命令与安装指引）在终端宽度不够时在格内折行。
- **`--json` 不变**：机读形态仍是原来的 JSON 文档（ADR 0041 决策三），表格与树只是文本视图。
- **测试只断言内容与归属，不断言排版，且与运行测试的终端无关**：树的构造与渲染分开（`run_tree` / `plan_tree` / `explain_tree` 返回 `TreeNode`），归属测试按节点断言「原因挂在所属 step 下」；文本测试只断言节点或单元格文本出现、不出现（表格里同一行的多个单元格可按同行匹配），不断言空格数、框线或引导线字符；涉及渲染的测试包用 autouse fixture 固定关色、表格不按终端取宽，`pytest -s` 在真实终端里也不假红；排版与颜色开关在 runtime 有独立单测（宽度对齐、标识列不折断、无 ANSI 序列、上色时去色后文字完整、标记不解析、树不折行、`NO_COLOR` 非空才生效、`FORCE_COLOR`）。此前按整行断言的测试改为按内容断言。

## 影响面

- `runtime/gherkai_runtime/textui.py` 新增；`runtime/pyproject.toml` 依赖加 `rich`。
- `cli/gherkai_cli/__main__.py` 的 `list-engines`、`list-deterministic`、`doctor`，`cli/gherkai_cli/render.py` 的 `render_text`（run 汇总）、`render_plan_text`、`render_explain_text`、`render_run_state`，`deploy_aws/gherkai_deploy_aws/workers.py` 的 `list_workers` 改用 textui；各自的首行说明与空清单提示保留。
- 用户指南：`doctor` 示例改为表格形态，「示例行」改「示例列」，配置页加 `NO_COLOR`；skill 的排障参考同步 `doctor` 读法；CHANGELOG 记为变化。

## 不做 / 延后

- 不给进度事件流改形态。
- 不引入基础 16 色之外的颜色、不引入背景色与加粗强调：跨终端主题的可读性只在基础色上有保证。
- 已知限制，接受：框线与引导线是东亚宽度歧义字符，把歧义字符设为双宽的终端（iTerm2 的对应选项、传统 conhost 配 CJK 代码页）会错位，所有带框线的终端界面同此；老式 Windows 控制台未开启虚拟终端序列时会显示原始转义码（本项目未针对 Windows 验证）。都只影响观感，`--json` 与 `NO_COLOR` 是退路。
