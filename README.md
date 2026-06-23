# Gherkin × (Midscene + Nova Act) × AgentCore Browser

一套 UI 自动化测试框架原型：用 **Gherkin** 描述测试意图，由两个互相独立的 **AI 引擎**（Midscene / Nova Act）执行，由 **AWS Bedrock AgentCore** 云端浏览器承载。三层正交，靠 CDP（Chrome DevTools Protocol）串联。

> 术语与设计决策见 [`CONTEXT.md`](./CONTEXT.md) 和 [`docs/adr/`](./docs/adr/)，外部一手来源见 [`docs/REFERENCES.md`](./docs/REFERENCES.md)。（初始蓝图 `midscene-novaact-prototype-guide.md` 已退役——其内容被 CONTEXT+ADR 全面覆盖且经实测更正。）

## 现状（2026-06，已端到端验证）

三层链路的每一层、每个连接点都已在真实 AWS 账号用真实请求验证通过：

| 里程碑 | 内容                                        | 状态                |
|--------|---------------------------------------------|---------------------|
| M1     | 双引擎冒烟（各自 spike 针）                   | ✅                   |
| M2     | 单一 `.feature` 被两套 runner 驱动          | ✅                   |
| M3     | Nova Act 接 AgentCore 云端浏览器            | ✅                   |
| M4     | Midscene 接 AgentCore（一度被视为"最大难关"） | ✅ 实测零坑          |
| M5     | 报告统一                                    | ⬜ 推迟（见 ADR 0010） |

## 架构速览

```
① 用例层   features/*.feature              ← 单一共享 Gherkin（ADR 0005）
              │  被两套 runner 各自加载
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
├── docs/adr/                  ← 11 条架构决策记录
├── features/                  ← 单一共享 .feature（两套 runner 都加载）
│   └── wikipedia_search.feature
├── midscene/                  ← Midscene 引擎子工程（TS）
│   ├── cucumber.mjs           ← cucumber-js 配置（指向根 features/）
│   ├── lib/agentcore-sigv4.mts ← 共享 SigV4 模块（模型连接 + 浏览器连接/CDP；spike/bdd 共用）
│   ├── bdd/steps/             ← Midscene 侧 step definitions
│   └── spikes/midscene-sigv4/ ← 三段式自检 spike（01/02/03）+ SIGV4-FETCH-RECIPE.md 配方笔记
└── novaact/                   ← Nova Act 引擎子工程（Python）
    ├── bdd/test_wikipedia.py  ← Nova Act 侧 step definitions（pytest-bdd）
    └── spikes/wikipedia_benchmark.py  ← Nova Act 腿 spike
```

## 前置要求

- AWS 凭证（默认 profile 即可），region **us-east-1**，需具备：
  - Bedrock 模型访问：`qwen.qwen3-vl-235b-a22b`（Midscene 大脑）
  - AgentCore Browser（`bedrock-agentcore` 服务）
  - Nova Act 服务（`nova-act`）+ 模型 `nova-act-latest`
- Nova Act workflow definition（IAM 路径必需）：**代码会自动 create-if-not-exists**（`novaact/lib/workflow_setup.py`），无需手动操作。若想手动预建也可：`aws nova-act create-workflow-definition --region us-east-1 --name spike-wikipedia-benchmark`（见 ADR 0004）。
- Node 22（midscene）、Python 3.13 + uv（novaact）

## 运行（M2：同一份 .feature，两套引擎）

**Midscene 侧（cucumber-js + TS）：**
```bash
cd midscene
NODE_OPTIONS="--import tsx/esm" AWS_REGION=us-east-1 node_modules/.bin/cucumber-js -c cucumber.mjs
# → 报告：midscene/midscene_run/report/*.html
```

**Nova Act 侧（pytest-bdd + Python）：**
```bash
cd novaact
AWS_REGION=us-east-1 .venv/bin/python -m pytest bdd/test_wikipedia.py -s
# → trajectory：$TMPDIR/..._nova_act_logs/<sessionId>/（默认临时目录，见 ADR 0010）
```

两者加载的是**同一个** `features/wikipedia_search.feature`。

## Spike（可独立跑的技术验证脚本）

```bash
# Midscene 腿三段式自检（隔离验证：模型连接 / 浏览器连接(CDP) / 合体）
cd midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/01-model-sigv4.ts
# 02-agentcore-cdp.ts / 03-midscene-grounding.ts 同理

# Nova Act 腿对标 spike
cd novaact && AWS_REGION=us-east-1 .venv/bin/python spikes/wikipedia_benchmark.py
```

## 注意

- 运行会真实消耗 AWS 费用（模型调用 + AgentCore 会话）。
- 环境隔离：TS 依赖在 `midscene/node_modules`，Python 依赖在 `novaact/.venv`，均不污染全局。
