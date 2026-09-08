# gherkai-deploy-aws

`gherkai` 的 **AWS 后端供给** provider 包：Python CDK 定义 `--backend cloud` 所需的全部云资源（DDB / S3 / ECS / ECR / IAM / VPC + 无状态跑批的 Stream·Lambda·EventBridge，ADR [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md)/[0034](../docs/adr/0034-detached-batch-reconciler.md)），以及 worker 镜像的推送与注册（ADR [0038](../docs/adr/0038-worker-image-delivery.md)）。

- 发行名 `gherkai-deploy-aws` · import 名 `gherkai_deploy_aws`（ADR [0037](../docs/adr/0037-distribution-and-packaging.md) 决策 2a/6）。
- **不单独安装**：随 CLI 的 extra 进来——`uv tool install 'gherkai[deploy-aws]'`；命令面在 CLI 侧（`gherkai deploy` / `destroy` / `deploy push-worker` / `deploy list-workers`），本包经 entry point group `gherkai.deploy` 被发现。
- `aws-cdk-lib` 只在本包上（jsii 绑定，import 即起 node 子进程）；`gherkai deploy` 要求 Node ≥ 22 在 PATH。
- 只有**部署方**需要装它：改云端环境（供给资源、推 worker 镜像）是云端写操作；只提交 run 的人不需要（ADR 0037 决策 2c）。

施工中（ADR 0037 落地次序第 4 步）：本包正从 `iac_aws_backend/` 收编而来，命令面与流程以 ADR 0037 决策 6、ADR 0038 为权威。
