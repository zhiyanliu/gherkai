# Engine & Protocol ADRs

> 33 nodes · cohesion 0.09

## Key Concepts

- **Midscene Worker 开发笔记** (17 connections) — `engines/midscene/DEVELOPMENT.md`
- **Nova Act Worker 开发笔记** (15 connections) — `engines/novaact/DEVELOPMENT.md`
- **e2e_harness 使用说明** (7 connections) — `tools/e2e_harness.md`
- **@gherkai/worker-midscene (README)** (6 connections) — `engines/midscene/README.md`
- **gherkai-worker-novaact (README)** (6 connections) — `engines/novaact/README.md`
- **ADR 0024 worker↔core 协议（三通道）** (4 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0037 分发与打包** (4 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0038 worker 镜像交付** (4 connections) — `engines/midscene/DEVELOPMENT.md`
- **确定性 step** (4 connections) — `engines/midscene/README.md`
- **ADR 0022 BDD runner 退役、core 解析 + 薄 worker** (3 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0029 引擎产物上传 S3** (3 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0033 IaC AWS 后端与装配接线** (3 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0036 确定性能力自述** (3 connections) — `engines/midscene/DEVELOPMENT.md`
- **薄 worker 执行形态** (3 connections) — `engines/midscene/DEVELOPMENT.md`
- **engines/midscene/Dockerfile — worker 基底镜像** (3 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0003 Midscene grounding 用 Qwen3-VL on Bedrock** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0008 Midscene Bedrock SigV4 自签** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0020 step 措辞默认 AI + 确定性脚手架** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **ADR 0028 瞬时网络/SSL 韧性与退出码 80** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **AgentCore 云浏览器（本机不装 Chromium）** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **镜像必须 --platform linux/amd64** (2 connections) — `engines/midscene/README.md`
- **纯 IAM 鉴权（无 API key）** (2 connections) — `engines/midscene/README.md`
- **engines/novaact/Dockerfile — worker 基底镜像** (2 connections) — `engines/novaact/DEVELOPMENT.md`
- **sample_valid 判读约定** (2 connections) — `tools/e2e_harness.md`
- **ADR 0002 不用 gpt-5.5 驱动 Midscene** (1 connections) — `engines/midscene/DEVELOPMENT.md`
- *... and 8 more nodes in this community*

## Relationships

- [Compose Root & ADR Links](Compose_Root_%26_ADR_Links.md) (6 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (3 shared connections)
- [Midscene Worker Entry & SigV4](Midscene_Worker_Entry_%26_SigV4.md) (2 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (2 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)

## Source Files

- `engines/midscene/DEVELOPMENT.md`
- `engines/midscene/README.md`
- `engines/novaact/DEVELOPMENT.md`
- `engines/novaact/README.md`
- `tools/e2e_harness.md`

## Audit Trail

- EXTRACTED: 63 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*