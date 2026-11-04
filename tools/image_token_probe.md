# image_token_probe：截图缩放后的图片 token 探针

「截图缩放降低 token」评估（结论见 ADR 0052 被拒方案节，换模型或 Midscene 改了缩后尺寸的范围校验时重议）的离线第一步：不使用真机，只向生产用的模型发请求，观察同一张截图缩到不同尺寸后服务端计入的 `prompt_tokens` 如何变化。它回答两个问题：Bedrock 对不带 `detail` 的图是否在服务端缩图（本仓库在签名前删掉了 `detail: "original"`）；图片 token 随尺寸下降的幅度，用来外推整个 job 的净降幅。

## 运行

需要 AWS 凭证与 region，且凭证能在该 region 的 Bedrock 上调用生产所用的模型（模型见下文），在 `engines/midscene` 目录里执行：

```bash
cd engines/midscene
AWS_REGION=us-east-1 node_modules/.bin/tsx ../../tools/image_token_probe.mts /path/android.png /path/ios.png --k 1,2,2.625,3 --n 3 --json /tmp/probe.json
```

- 输入是真机截图的 PNG（原生像素）。缩放用 Midscene 送模型前的同一种编码（JPEG 质量 90），尺寸为 round(原图 ÷ k)。
- 每个尺寸发两类带图请求：不带 `detail`（生产的定位与规划请求形态）、`detail: "high"`（生产的断言请求形态）；另发纯文本对照。每类 `--n` 次。
- 模型取 `lib/agentcore-sigv4` 的缺省（可用 `MIDSCENE_MODEL_ID` 覆盖），与生产相同。每次请求只要一个词、`max_completion_tokens` 16（GPT-5 系列不接受 `max_tokens`），花费可忽略。

## 读数

表的最后一列「图片 token 估算」是带图请求的 `prompt_tokens` 均值减去纯文本对照的均值。判读：

- 若 k=2 的图片 token 不到 k=1 的 60%，说明服务端按发出的尺寸计费、缩放有效。
- 若 k=2 与 k=1 接近，说明服务端已在内部缩图或按固定额计费，客户端缩放省不了 token，评估到此为止。

外推 job 级净降幅要结合基线 run 的 `midscene-run/log/ai-profile-stats.log`（每次模型调用一行，含 prompt-tokens 与 completion-tokens）：按每次调用带一张图估图片占比，再按本表的降幅折算。2026-11-02 的读数与外推内联在 ADR 0052 被拒方案节。
