# 项目约定

## 沟通

- 沟通、讨论一律用中文；思考过程也用中文。

## 文档纪律（ADR / CONTEXT 等）

- ADR 记稳定决策（what/why/trade-off）、按主题归位；施工进度（步骤/commit 节奏）属实现计划，放对话或 PR。
- 改 code 前先把设计决策落进 ADR——"不实现"≠"不设计"；**改完后回头校准受影响的 ADR/CONTEXT/README，别只落新决策、留旧描述漂移**（文档陈旧多半源于此）。
- 精简文档时不删决策理由、权衡、反模式。
- **读者比例决定优化方向**：ADR/CONTEXT 主要给 AI coding agent 读（约 80%）→ 优化向信息密度、单一事实源、精确指针，冗余=噪声、敢压；README 主要给人读 → 保叙事、不激进压缩。据此定"压缩 vs 保留"。
- **ADR Status 头**：每个 ADR 开头带一行 `> **Status:** Accepted / Superseded-by NNNN / Partially-superseded-by NNNN / Draft / Historical`。新增 ADR 必带；当某 ADR 取代/反转旧 ADR 时，**同步更新旧 ADR 的 Status 头**（反向链），别只在新 ADR 里单向记。

## 代码纪律

- **写/改 code 前对照相关 ADR 的已定决策、契约、不变量**——逐步叠加式开发最易偏离设计；先确认没违背相关 ADR 的红线（散见各 ADR，勿在此复述以免漂移），再动。
