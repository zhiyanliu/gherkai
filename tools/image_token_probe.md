# image_token_probe：截图缩放后的图片 token 探针

ADR 0052 第 9 节「截图缩放降低 token」评估的离线第一步：不上真机，只向生产用的模型发请求，看同一张截图缩到不同尺寸后服务端计的 `prompt_tokens` 怎么变。它回答两个问题：Bedrock 对不带 `detail` 的图是否在服务端缩图（本仓库在签名前删掉了 `detail: "original"`）；图片 token 随尺寸下降的幅度，用来外推整个 job 的净降幅。

## 运行

要 AWS 凭证与 region（跳板机上），在 `engines/midscene` 目录里执行：

```bash
cd engines/midscene
AWS_REGION=us-east-1 node_modules/.bin/tsx ../../tools/image_token_probe.mts /path/android.png /path/ios.png --k 1,2,2.625,3 --n 3 --json /tmp/probe.json
```

- 输入是真机截图的 PNG（原生像素）。缩放用 Midscene 送模型前的同一种编码（JPEG 质量 90），尺寸为 round(原图 ÷ k)。
- 每个尺寸发两类带图请求：不带 `detail`（生产的定位与规划请求形态）、`detail: "high"`（生产的断言请求形态）；另发纯文本对照。每类 `--n` 次。
- 模型取 `lib/agentcore-sigv4` 的缺省（可用 `MIDSCENE_MODEL_ID` 覆盖），与生产相同。每次请求只要一个词、`max_tokens` 16，花费可忽略。

## 读数

表的最后一列是「图片 token 估算」= 带图请求的 `prompt_tokens` 均值减纯文本对照均值。判读：

- 若 k=2 的图片 token 不到 k=1 的 60%，说明服务端按发出的尺寸计费、缩放有效。
- 若 k=2 与 k=1 接近，说明服务端已在内部缩图或按固定额计费，客户端缩放省不了 token，评估到此为止。

外推 job 级净降幅要结合基线 run 的 `log/ai-profile-stats.log`（每次调用的 prompt / completion），见 `docs/journey/` 里截图缩放评估的进度总纲。
