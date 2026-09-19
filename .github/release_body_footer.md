## 安装

```bash
uv tool install 'gherkai[local]=={{VERSION}}'          # CLI + 本机 Nova Act worker
npm i -g @gherkai/worker-midscene@{{VERSION}}          # 本机 Midscene worker
uv tool install 'gherkai[deploy-aws]=={{VERSION}}'     # 部署方：云端后端的部署命令
```

worker 基础镜像（linux/amd64）：
`ghcr.io/{{OWNER}}/gherkai-worker-novaact:{{VERSION}}` · `ghcr.io/{{OWNER}}/gherkai-worker-midscene:{{VERSION}}`

## 升级

1. 部署方升级 CLI：`uv tool upgrade gherkai`（安装时带的 extras 沿用）。
2. 部署方立刻执行 `gherkai deploy --vpc <与上次相同的档> --prefix <同前缀>`，让云端后端与 CLI 同版本。这两步之间，只有这台刚升级的机器自己的提交与查询会被拒绝（退 2），属预期；团队其他成员不受影响。
3. 团队其他成员再升级各自的 CLI；在本机运行用例的人同时把 Midscene worker 升到同版本：`npm i -g @gherkai/worker-midscene@{{VERSION}}`。有自定义 worker 镜像 variant 的团队，从新版本的基础镜像重新构建后，用 `gherkai deploy push-worker` 推送一次。

本版文档：https://github.com/{{OWNER}}/{{REPO}}/blob/v{{VERSION}}/docs/user-guide/README.md
· 云端后端升级细节：https://github.com/{{OWNER}}/{{REPO}}/blob/v{{VERSION}}/docs/user-guide/cloud-backend.md
· 完整变更历史：https://github.com/{{OWNER}}/{{REPO}}/blob/v{{VERSION}}/CHANGELOG.md
