// Planning 候选探针：验证一个纯文本推理模型能否做 Midscene 的 planning 角色。
// 两关：(a) chat-completions 在本账号 200；(b) 容忍 image_url 部件——
//   因为 Midscene 的 planner 即便不做定位也会无条件附带截图（调查 P1 挖出的真未知）。
// 复用已验证的 SigV4 自签（service "bedrock"，与 grounding 同源）。
// 跑：cd midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/midscene-sigv4/04-planning-probe.ts
import OpenAI from "openai";
import { sigv4Fetch, BASE_URL } from "../../lib/agentcore-sigv4.mjs";

// 主选 deepseek.v3.2，走已验证的 bedrock-runtime /openai/v1（与 grounding 同端点）。
// 备选（取消注释切换）：
const MODEL = "deepseek.v3.2";
// const MODEL = "openai.gpt-oss-120b-1:0";
// const MODEL = "qwen.qwen3-next-80b-a3b";
// const MODEL = "us.anthropic.claude-sonnet-4-6"; // 若要试 Claude（实测 bedrock-runtime 上曾 404，存疑）

// 1x1 png：只验证模型是否 TOLERATE image_url 部件
const PNG_1x1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

async function main() {
  console.log(`[probe] base=${BASE_URL} model=${MODEL}`);
  const client = new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch });

  // (a) 纯文本 — 本账号 chat-completions 是否 200
  const t = await client.chat.completions.create({
    model: MODEL,
    messages: [{ role: "user", content: "Reply with exactly one word: ok" }],
    max_tokens: 16,
  });
  console.log("[probe a] text OK ->", JSON.stringify(t.choices[0]?.message?.content));

  // (b) image_url 容忍 — Midscene planner 无条件附带截图
  const v = await client.chat.completions.create({
    model: MODEL,
    messages: [{
      role: "user",
      content: [
        { type: "text", text: "Ignore the image. Reply with exactly one word: ok" },
        { type: "image_url", image_url: { url: `data:image/png;base64,${PNG_1x1}` } },
      ] as any,
    }],
    max_tokens: 16,
  });
  console.log("[probe b] image-tolerant OK ->", JSON.stringify(v.choices[0]?.message?.content));
  console.log("[probe] PASS — planner 可达 + 容忍截图部件");
}

main().catch((e) => {
  console.error("[probe] FAIL:", e?.status ?? "", e?.message ?? e);
  if (e?.error) console.error("     body:", JSON.stringify(e.error).slice(0, 400));
  process.exit(1);
});
