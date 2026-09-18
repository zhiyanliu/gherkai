# 文档图作者化方法（archify）— 任务说明

> 给要在本仓库新增或修改 `docs/diagrams/` 下的图的 AI agent：本文是**可复用的任务指令**。形态与门槛的决策在 [ADR 0045](../adr/0045-documentation-layering-and-placement.md) 决策七，这里只记「怎么一次画对」：本项目的图长什么样、布局清单、archify 里达成它们的技法、交付前的自检。规则来自两轮人工评审（十余张图、二十来条布局意见）的提炼，每条技法都在仓库现有图源上验证过。入口 skill：`.claude/skills/diagram/SKILL.md`。

## 一、流程（每张图）

1. **先定要不要画**：结构 / 顺序 / 状态 / 分支用文字确实费劲，且能指出它替代或压缩了哪段文字；一张表能说清的不画。
2. **选类型**（archify 五类）：组件与边界 → `architecture`；步骤 / 分支 / 循环 / 闸门 → `workflow`（schema_version 2）；数据从哪流到哪、谁消费 → `dataflow`；调用链与时序 → `sequence`；状态与终态 → `lifecycle`。拿不准跑 `node ~/.agents/skills/archify/bin/archify.mjs guide "<一句话场景>" --lang zh --json`。
3. **作者化 JSON**：读 archify `SKILL.md` 的 fast authoring path，只读匹配类型的 `schemas/<type>.schema.json`、`schemas/common.schema.json` 与一个 `examples/*.<type>.json`；写 `docs/diagrams/<页面短名>-<主题>.json`；`meta.locale: "zh-CN"`、`meta.quality_profile: "showcase"`。
4. **校验**：`node ~/.agents/skills/archify/bin/archify.mjs validate <type> docs/diagrams/<name>.json --quality showcase --json`，循环到 0 error 0 warning（9 项 artifact 检查全过）。
5. **构建与目视**：`node tools/build_diagrams.mjs --png docs/diagrams/<name>.json`（deliver 出 HTML → 导出 SVG 与 PNG，SVG 末尾带图源指纹）。用 Read 打开 PNG，按第三节清单逐项过。**迭代时不要用 `--no-deliver`**：它复用旧 HTML，看不到 JSON 改动。看完**删掉 PNG**。
6. **嵌入**：`![<一句话说明>](../diagrams/<name>.svg)`（根 README 用 `./docs/diagrams/`），图下一行图注交代图外事实与和别图的分工；只有发布到 Pages 的图在图注末尾加交互版链接。被图替代的散文删掉或压成一句，结论句与指针保留（user-guide / README 的读者含 AI agent，它读不了图）。
7. **交付**：JSON 与 SVG 同 commit；已发布的图连 HTML 一起 `git add`；跑 `cli/tests/test_user_docs.py`（成对、指纹、禁词、无 mermaid、已发布 HTML 与 index 一致）。

## 二、本项目的图长什么样（内容规则）

- 主节点 ≤ 12，一条主路径，短标签（≤ 14 字），边标签只写语义（动作 / 方向 / 同步异步 / 跨界机制），细节进 cards / notes、不加节点。
- 图上**只画结构与指向**：默认值、键名、个数、函数名、模型名、region、ADR 编号、内部机制名（宿主 / 推进器 / 组合根 / 不变量…）一律不入图——会漂的字面量留正文或表；图源受 `test_user_docs.py` 的禁词扫描。
- 标识符保留英文（run / submit / local / cloud / Lambda / Fargate / S3 / DynamoDB / SSM / ECR），说明性文字中文。
- 一张图一个主命题；与别的图的分工写进图注，不重画别图已画的链。
- cards 不进导出的 SVG（只在交互 HTML 与 JSON 里可见）：靠 SVG 传达的事实不能只写在 card 里。

## 三、布局清单（PNG 自检项，也是评审验收项）

逐项过，任一项不满足就回去改 JSON：

1. **链式关系排一行**：A → B → C → D 这类归约 / 流水线放同一 row，不折行。
2. **能直的边不折**：相邻且对齐的两个节点之间用两点直线；同一节点出多条边用同一出口侧、同一折法（或都不折）；进入节点的最后一段与该侧垂直。
3. **判定 / 分支图**：分支线竖直向下直指目标，不向左右折；全图分支线起点统一（都从判定框底边中点出，不从主路线上分叉）。
4. **不重叠、不交叉、不拧劲**：两条边不得共线重叠（尤其同一节点的多条出线共用一段干线）；同源同目标的两条边各自平直、不互绕不交叉；不同边的走廊分开。
5. **标签不压东西**：边标签不压节点、不压另一条边、不压时序图的生命线与激活条、不跨容器 / lane 的虚线边框；时序图消息文字过长时把括号部分放进该消息的 `note`（archify 不支持标签折行）。
6. **实体位置服从走线**：右侧 / 边缘的实体框位置以「虚线不无谓折弯」为先，其次才是对齐美观。
7. **画布贴内容**：viewBox 收到内容边界，右侧 / 下方不留没有线框的空白；单行图用 `yOffset` 把节点行在容器里居中。
8. **对齐**：同类节点同 row / 同 col；跨栏节点不做零散 `yOffset` 造成错位（只为躲开校验的最小段长时才用，并记在返回值里）。

## 四、技法（archify 里怎么达成）

顺序：**先动节点，再动路由，最后动标签**。每次只改一处、重渲染看效果。

- **让边变直**：把两端节点放到同一 row / col（`col` / `row` / `yOffset`），自动路由就是两点直线。相邻已对齐仍绕行时，显式 `route: "straight"`；若校验报 label-route-clearance，是因为两点路由的标签默认落在起点上方、掉进源节点框内——配 `labelDx` / `labelDy` 把标签挪到线旁即可。斜线（两端不对齐的 `straight`）在 showcase 下是硬失败（orthogonal-arrows）。
- **钉一段竖直下落 / 单拐 L 形**：`via: [[x, y]]` 单点钉在目标列中心线上；配 `fromSide` / `toSide` 指定出入侧（`toSide: "left"` 要求最后一段自左向右水平入）。几何上不共线的两点至少一个拐点，做不到零拐。
- **同一节点多条出线**：显式 `via` / `channelX` / `channelY` / `labelAt` 或非 auto 的 `route` 会**关掉自动端口分散**，两条边会从同一端口出发、首段共线重叠。解法：给两条边不同的出口侧（如一条 `fromSide: "top"`、一条 `"bottom"`，上下镜像单折），或把其中一条留给自动路由。
- **走廊选 channel 不选绝对 via**：`channelY` / `channelX` 只钉一维，布局重解时会响亮报 explicit-pin-conflict；绝对 `[x, y]` via 会随节点坐标漂而悄悄失效。lane 里可用的走廊通常只有标题带（框顶 30 单位）。
- **标签位置**：`labelDy` 沿垂直方向、`labelDx` 沿水平方向偏移，`labelSegment` 选落在哪一段，`labelAt` 绝对钉（最后手段）。短线上的 `labelDy` 可行区间很窄（实测 72 单位的线约 46～62），逐个值渲染比对。
- **时序图（sequence）**：标签是单个矩形、不折行；牌子中心恒在两端参与者列心的中点，跨偶数列距的消息牌子必压中间那一列——文字控制在约 23 个字宽以内，括号说明放 `note`；参与者顺序决定穿越次数，按叙事从左到右排；加宽画布会撞 desktop-readability 门（宽度上限约 930）。
- **数据流（dataflow）**：相邻 stage 容器间隙只有约 47 单位，横向流标签超过约 40 单位必压两侧虚线——标签要短；`meta.viewBox` 高度下限 360；单行时用统一 `yOffset` 居中。
- **校验器的盲区**：共享端点的两条边之间的交叉与共线重叠**不报**（`properCrossings` 照样 0），标签压容器边框只要过了 clearance 也不报——所以「跑绿」不等于形态达标，布局意见只能靠折点数值 + PNG 局部放大判定。取精确折点不必起 Chrome：workflow 类型用 `validate … --layout-json`；dataflow / architecture 用 `node bin/archify.mjs render <type> <json> /tmp/x.html --quality standard` 后 grep `data-composition-points`。局部放大用 `sips -c <h> <w> --cropOffset <y> <x> <png> --out <crop.png>` 再 Read。
- **端口模型（dataflow / architecture）**：同一侧的自动边按固定 14 单位分散，带 via / channel 的显式边一律锚在该侧中点——一侧同时有两条自动边和一条显式边，显式那条必夹在正中（±7 单位），箭头三角互压。因此每个节点每一侧最多放两条边，第三条换侧（顶 / 底）；同源同目标的两条边要各走不同入口侧（一条左侧、一条顶边），做成嵌套直角而不是并排同形——同一对节点的两条自动边会共用同一条走廊、竖段完全共线。
- **改一条边的副作用**：把某条边改成 `straight` 或改侧后，自动路由会重算其它边，可能把别的边绕进已放置的标签而使 `straight` 被否（route-preset-conflict）——用 `toSide` / `fromSide` 把受影响的边钉回原侧。
- **画布贴内容**：dataflow 横向几何固定（列距 215、容器宽 168），右侧留白由 `meta.viewBox[0]` 决定，最小宽度 = 图例单行宽度 + 80（图例换行会撞 legend/vertical-overflow）；收窄会改变长宽比，只对发布到 Pages 的交互版有 viewport-overflow 影响，静态 SVG 无碍。workflow v2 的画布由编译器算出，无 `meta.viewBox` 可调。
- **图上文字同守口吻**：节点与图例里的字读者直接看到，隐喻（「烙进」）、口头语一律不用，护栏 `test_user_docs.py` 对图源扫禁词与口头语表。
- **相对的两个节点之间走直线（workflow v2）**：`straight` 要求两节点之间的净空 ≥ max(28, 标签遮罩宽 + 8)——标签是横在两点之间的，`labelDx` / `labelDy` 挪不掉这条判定；净空不够时缩短标签文字（如「派发一个 job」→「派发 job」）或拉开两节点（`yOffset` 会与别的边的显式 via 起 explicit-pin-conflict，先看哪条边钉了绝对坐标）。`validate --layout-json` 只在校验失败时给 diagnostics、不给几何，拿几何要先让它过校验。
- **回传边（workflow v2）**：优先用预设 `route: "return-left"`；把目标节点对齐到同一列后预设会因端口被占而失效，此时改为 `fromSide` / `toSide` + `channelX` 钉一条走廊（走廊离任何节点边缘 ≥ 28 单位，否则报 route-preset-conflict）并用 `labelSegment` / `labelDx` 把标签放到竖段旁；`layout/constraint` 的 message 里带具体的 labelDy / labelAt 建议值，直接照抄。**别把回传边留给全自动路由**：它会为躲开走廊绕整张画布的外沿。
- **校验常见告警与含义**：`short-interior-segment`（< 16 单位的中间段，多由端口错位造成，调 row / yOffset 对齐）；`label-route-clearance`（标签离线 < 4 单位）；`unrelated collinear overlap`（共线重叠 > 8 单位）；`routesOverSuggestedBends`（拐点 > 2）；`desktop-readability`（画布太宽导致最小文字投影 < 6px）。

## 五、返回与记录

- 返回值写清：改了哪些几何键、达成 / 部分 / 未达成、校验摘要、做不到的项「试了什么、校验报什么」——**不用违反校验或改语义的产物交付**。
- 把新学到的、可复用的约束补回本文第四节（连同验证它的图名），别留在对话里。
