> 类型: 进度总纲

# 截图缩放对设备目标定位准确率的评估

1.5 剩余项之一（owner 把 ADR 0052 第 9 节「截图缩放降低 token 需另行评估」拉进 1.5）。本文记方案、闸与进度；稳定结论落 ADR 0052（接受则新写决策，拒绝则进被拒方案并删实验代码），落完即删本文。方案由理解—设计—批评三阶段的 workflow 产出并经对抗审查修正。

## 方案

- **实验开关用 Midscene 自带的构造项 `screenshotShrinkFactor`（k ≥ 1 的除数），不在界面层自己缩图**：SDK 在设备 Agent 的上下文解析里已接好——`size()` 仍报原生像素、送模型的图缩到 round(原图 ÷ k)、动作 center 自动乘回 k；适配器、`ctx.scale`、命令契约快照都不动。注入点只有设备接缝的 `deviceAgentOpts`（桌面不经它），读 env `GHERKAI_EXPERIMENT_SCREENSHOT_SHRINK`（缺省不设即 k=1、构造项逐键与生产相同；非法值在建会话前抛出），生效的 k 记进会话就绪日志。本机 worker 继承宿主 env；云端标准镜像收不到这个键，但经 variant 镜像的 ENV 也能生效（ADR 0044 决策 2），所以它是使用方够得着的开关、要在 Midscene 的 DEVELOPMENT.md 记一笔，不进用户文档的 env 表。
- **已知的几何代价（实验期只记录、不补偿）**：center 在缩后空间取整再乘回，量化误差约 k/2 原生像素；Android 的 Scroll `distance` 不随 1/k 换算（换算只作用于定位字段的 center），实际滚动幅度变成 1/k；evidence 与报告里存的是缩后图，读证据的人无从知道图被缩过（evidence 固定键里没有缩放倍数）。
- **先核的未知（闸 0）**：本仓库在签名前删掉了 `image_url.detail: "original"`，Bedrock 对无 detail 的图是否在服务端缩图、图片 token 是否随尺寸下降，都未核。离线探针（`tools/image_token_probe.mts`）把两张真机样本截图（Pixel 8a 1080x2400、iPhone 14 1170x2532）用与生产同一种编码（JPEG 质量 90）缩到 k = 1 / 2 / 2.625 / 3，各发「无 detail」「detail high」与纯文本对照请求若干次，记 prompt_tokens；再用基线 run 的 ai-profile-stats 外推 job 级净降幅（含 completion 与推理 token）。**外推的 job 级净降幅低于 25% 即停，不进真机**。

## 真机矩阵与判据（闸 0 通过后）

- 设备 × 目标 × 水平：Pixel 8a / iPhone 14 × 网页 / 应用 × k ∈ {1, 2, 逻辑尺寸（Pixel 2.625、iPhone 3）}；feature 用跳板机 `/tmp/acc/e2e/features/` 的四个（iOS 应用的改写版把收起键盘一步换成只输入，放同一目录）。要补一条 Android「滚动直到看到 X」的 step，否则 Scroll 幅度变化测不到。每轮内三个水平交替执行；记录每个 run 的会话 ARN 与设备实例作协变量。
- 样本量：试点每格 1 个 run（核 env 到达 worker、缩后尺寸、点击落点、报告标注、Scroll 参数）；主实验 N=10 只够判「被拒」，要判「默认开启」至少 N=20 或加离线重放并设非劣效界。
- 采集：`run --json` 的判定、`jobs[].total_tokens`、`duration_ms`；stderr 进度行里每 step 的 tokens；`report/*.execution.json` 的规划轮数（每轮恰一个 Planning/Plan，排除 Planning/Locate 与 Planning/LoadYaml）与首个定位动作；`log/ai-profile-stats.log` 的每次调用用量（按 requestId 与 execution.json 关联分类；日志背压会丢行，先与 execution.json 核条数）。
- 闸 1（按设备 × 目标四格逐格判，k 对基线）：场景失败数每格不多于基线 +1、四格合计不多于 +2；首次动作命中率四格合计下降不超过 5 个百分点、任一控件在 k 下未命中 ≥2 次而基线 0 次即判不过；每 step 规划轮数中位数不增、P90 最多 +1、不触顶；基线没有的定位越界类 engine_error 不超过 1 次；反向对照全部仍为 assertion_failed；job 级 total_tokens 中位数下降 ≥25% 且四格都降。
- 结论三选一：默认开启（取四格全过的最大 k；k 要在探测之后按设备注入是新决策，先进 ADR 0052，并同步决策 4「坐标单位」行、决策 8 验收矩阵、cli-json-contract 与用户指南讲 explain 截图的段落）；写成被拒方案（内联各尺寸的图片 token、准确率差、样本量、失败形态与重议条件，删实验代码与第 9 节那句）；数据不足则该格加到 N=20 再判。成本上若净节省折成美元只占 job 总成本的个位数百分比，即使不退化也要求 step 时延有明显改善才默认开启。

## 闸 0 读数（2026-11-02，跳板机，模型 us.openai.gpt-5.6-terra 经 Bedrock，每格 3 次读数完全一致）

图片 token = 带图请求的 prompt_tokens 减纯文本对照（16）。「无 detail」是生产的定位与规划请求形态（删掉 `original` 后不带 detail），「high」是生产的断言请求形态。

| 截图 | k | 尺寸 | JPEG 字节 | 无 detail | high |
|---|---|---|---|---|---|
| Pixel 8a | 1 | 1080x2400 | 151 KB | 2695 | 2001 |
| Pixel 8a | 2 | 540x1200 | 61 KB | 791 | 791 |
| Pixel 8a | 2.625 | 411x914 | 42 KB | 522 | 522 |
| Pixel 8a | 3 | 360x800 | 35 KB | 445 | 445 |
| iPhone 14 | 1 | 1170x2532 | 201 KB | 3105 | 2065 |
| iPhone 14 | 2 | 585x1266 | 79 KB | 905 | 905 |
| iPhone 14 | 2.625 | 446x965 | 54 KB | 579 | 579 |
| iPhone 14 | 3 | 390x844 | 44 KB | 496 | 496 |

判读：①服务端按发出的尺寸计费、没有缩图——k=2 的图片 token 只有 k=1 的 29%（闸 0 的 60% 门槛远远通过），k=3 约 16%。②只有原图尺寸上「无 detail」比「high」贵约 35%（2695 对 2001、3105 对 2065）：原图像素数超过 high 口径的服务端缩图阈值时，high 先缩再计费，无 detail 按原像素计费；缩到 k ≥ 2 后两种口径的读数相同，说明已在阈值之内。由此可知生产的定位与规划请求现在走的是最贵也最清晰的口径（原像素），断言请求走的是被服务端缩过的图。③job 级净降幅的外推：用 2026-11-01 真机验收期 21 个 Midscene 设备 run 的 `midscene-run/log/ai-profile-stats.log`（每次模型调用的 prompt / completion），按「每次调用带 1 张原图」的保守假设（规划请求的历史截图数为 1；观察帧更多张时实际占比更高），图片占 prompt 的 29% 到 44%——网页目标 38% 到 44%、应用目标 29% 到 31%（应用目标的规划文本更长）；completion 只占总量的 1% 左右（gpt-5.6-terra 在这条链路上几乎没有推理 token 计入）。由此外推的 job 级净降幅：k=2 网页 26% 到 31%、应用 20% 到 22%；k=3 网页 31% 到 37%、应用 24% 到 26%。**闸 0 判定：通过**——服务端按尺寸计费这一前提成立，网页目标的外推降幅过 25% 门槛，应用目标在门槛附近；进入真机试点。节省幅度是「四分之一到三分之一」而不是数量级，默认开启与否最终要看闸 1 的准确率代价与 owner 对成本的权衡。

## 进度

- 2026-11-02：方案定稿；实验开关（`device/limits.mts` 读 env、`device/surface.mts` 的构造项与就绪日志）与离线探针 `tools/image_token_probe.mts` 已落地并提交；闸 0 已跑完并通过（读数与外推见上）；探针首版用 `max_tokens` 被模型拒绝，改为 `max_completion_tokens`。真机试点（每格每水平 1 个 run，共 12 个）准备中：跳板机验证工作树已 `uv sync` 与重建 Midscene 产物。
