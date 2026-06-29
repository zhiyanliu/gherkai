# Gherkin × (Midscene + Nova Act) × AgentCore Browser

一套 UI 自动化测试框架原型：用 **Gherkin** 描述测试意图，由两个互相独立的 **AI 引擎**（Midscene / Nova Act）执行，由 **AWS Bedrock AgentCore** 云端浏览器承载。三层正交，靠 CDP（Chrome DevTools Protocol）串联。

> 术语与设计决策见 [`CONTEXT.md`](./CONTEXT.md) 和 [`docs/adr/`](./docs/adr/)，外部一手来源见 [`docs/REFERENCES.md`](./docs/REFERENCES.md)。（初始蓝图 `midscene-novaact-prototype-guide.md` 已退役——其内容被 CONTEXT+ADR 全面覆盖且经实测更正。）

## 现状（2026-06，已端到端验证）

> **本 README 描述 `spike-validated` / v0.x 形态**（双 BDD runner 直跑：cucumber-js + pytest-bdd）。此形态已端到端验证、当前可跑。**v1.0 起架构有重大调整**：核心库自解析 Gherkin + 两腿薄 worker 子进程，**退役** cucumber-js/pytest-bdd 及 cucumber 补丁，改为 `core/` + `cli/` + `engines/{midscene,novaact}` 布局——见 ADR 0016（执行架构）/ 0022（BDD runner 退役）/ 0023（核心语言）。下文凡涉双 runner、`cucumber.mjs`、cucumber 补丁处均为 v0.x 形态。

三层链路的每一层、每个连接点都已在真实 AWS 账号用真实请求验证通过：

| 里程碑 | 内容                                        | 状态                |
|--------|---------------------------------------------|---------------------|
| M1     | 双引擎冒烟（各自 spike 针）                   | ✅                   |
| M2     | 单一 `.feature` 被两套 runner 驱动          | ✅                   |
| M3     | Nova Act 接 AgentCore 云端浏览器            | ✅                   |
| M4     | Midscene 接 AgentCore（一度被视为"最大难关"） | ✅ 实测零坑          |
| M5     | 报告统一（= RunReport）                      | ✅ v1.0 归集索引（ADR 0027；manifest + index，不融合产物） |

## 架构速览

```
① 用例层   features/*.feature              ← 共享 Gherkin，两腿同读一份（ADR 0005）
              │  被两套 runner 各自加载（v0.x 形态）
② 执行层   Midscene(TS)    ┃  Nova Act(Python)   ← 两个独立 AI 引擎，平级
   runner  cucumber-js     ┃  pytest-bdd
   大脑    Qwen3-VL@Bedrock ┃  nova-act-latest
   鉴权    SigV4 自签        ┃  IAM @workflow
              │  都经 CDP 驱动
③ 浏览器层 AgentCore Browser（aws.browser.v1，每引擎各一个会话）
```

关键约束：**全栈托管在 AWS 内**（ADR 0009）；**范围限英文 UI**（ADR 0001）。

## 目录结构

```
yaozhou/
├── README.md                  ← 本文件
├── CONTEXT.md                 ← 领域术语表（glossary）
├── docs/adr/                  ← 27 条架构决策记录
├── features/                  ← 共享 .feature（同一份被两腿加载；通用 step 风格）
│   ├── wikipedia_generic.feature
│   ├── wikipedia_assertions.feature
│   ├── wikipedia_robustness.feature
│   ├── engine_routing.feature
│   └── deterministic_anchor.feature   ← @deterministic 锚点验证（ADR 0022/0027）
├── engines/midscene/                  ← Midscene 引擎子工程（TS）
│   ├── cucumber.mjs           ← cucumber-js 配置（指向根 features/）
│   ├── lib/agentcore-sigv4.mts ← 共享 SigV4 模块（模型连接 + 浏览器连接/CDP；spike/bdd 共用）
│   ├── bdd/steps/generic.steps.ts ← Midscene 侧通用 step（QA 不写代码）
│   └── spikes/ ← 自检 spike（01 模型/02 CDP/03 合体/04 planning/05 负向）+ SIGV4-FETCH-RECIPE.md
└── engines/novaact/                   ← Nova Act 引擎子工程（Python）
    ├── bdd/test_generic_steps.py  ← Nova Act 侧通用 step（pytest-bdd）
    └── spikes/wikipedia_benchmark.py  ← Nova Act 腿 spike
```

## 前置要求

- AWS 凭证（默认 profile 即可），region **us-east-1**，需具备：
  - Bedrock 模型访问：`qwen.qwen3-vl-235b-a22b`（Midscene 大脑）
  - AgentCore Browser（`bedrock-agentcore` 服务）
  - Nova Act 服务（`nova-act`）+ 模型 `nova-act-latest`
- Nova Act workflow definition（IAM 路径必需）：**代码会自动 create-if-not-exists**（`engines/novaact/lib/workflow_setup.py`），无需手动操作。若想手动预建也可：`aws nova-act create-workflow-definition --region us-east-1 --name spike-wikipedia-benchmark`（见 ADR 0004）。
- Node 22（midscene）、Python 3.13 + uv（novaact）

## 运行（同一份 .feature，两套引擎，通用 step）

**Midscene 侧（cucumber-js + TS）：**
```bash
cd engines/midscene
# 跑全部 feature：
NODE_OPTIONS="--import tsx/esm" AWS_REGION=us-east-1 node_modules/.bin/cucumber-js -c cucumber.mjs
# 跑子集用 tag（勿再传 feature 路径，会与配置 paths 合并）：... -c cucumber.mjs --tags "@engine:midscene"
# → 报告：engines/midscene/midscene_run/report/*.html
```

**Nova Act 侧（pytest-bdd + Python）：**
```bash
cd engines/novaact
AWS_REGION=us-east-1 .venv/bin/python -m pytest bdd/test_generic_steps.py -s
# → trajectory：$TMPDIR/..._nova_act_logs/<sessionId>/（默认临时目录，见 ADR 0010）
```

两腿加载的是**同一份** `features/` 下的 `.feature`（通用 step 风格，QA 只写自然语言）。

### 怎么写 `.feature`（QA 零代码，ADR 0020）

- 动作/断言都写**纯人话、无路由关键词**：`When "搜索 OpenAI"` / `Then "进入了 OpenAI 词条页"` → 默认走 AI（动作=aiAct/act；断言=aiBoolean/act_get+投票）。
- scope/引擎用 **tag**（ADR 0019）：`@scope:login`（共享会话、串行）/ `@engine:midscene|novaact`（选腿）。
- **确定性精确检查**（URL/DOM，不容 AI 抖动）：由 test engineer 在 `deterministic.steps.ts` / `deterministic_steps.py` 脚手架按需写（QA 不碰）。
- Midscene 侧依赖一个本地 cucumber 补丁让裸 `When/Then` 不冲突（ADR 0021，已随 `patches/` + `postinstall` 固化）。

## Spike（可独立跑的技术验证脚本）

```bash
# Midscene 腿三段式自检（隔离验证：模型连接 / 浏览器连接(CDP) / 合体）
cd engines/midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts
# 02-agentcore-cdp.ts / 03-midscene-grounding.ts 同理

# Nova Act 腿对标 spike
cd engines/novaact && AWS_REGION=us-east-1 .venv/bin/python spikes/wikipedia_benchmark.py
```

## 注意

- 运行会真实消耗 AWS 费用（模型调用 + AgentCore 会话）。
- 环境隔离：TS 依赖在 `engines/midscene/node_modules`，Python 依赖在 `engines/novaact/.venv`，均不污染全局。
