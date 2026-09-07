// 三段式自检 · 第 1 段：独立验「模型连接」
// 目标：TS 侧 SigV4 自签 fetch + openai-node v6 → Bedrock qwen3-vl，拿 200。
//   (a) 纯文本：证 SigV4 字节匹配 + 协议通
//   (b) 视觉：用一张合格的真实 PNG（非 1x1 占位图）证 image_url 能过 Bedrock 图像 sanitize 并返回视觉应答
// 跑：cd midscene && node_modules/.bin/tsx spikes/midscene-sigv4/01-model-sigv4.ts
import OpenAI from "openai";
import { sigv4Fetch, getBaseUrl, MODEL, getRegion } from "../src/lib/agentcore-sigv4.mjs";
// region 改惰性 getter（ADR 0033/0016 决策 C）；spike 直跑带 AWS_REGION=... 前缀，顶层求值 OK。
const REGION = getRegion(), BASE_URL = getBaseUrl();

// 生成一张 64x64 PNG：左半红、右半蓝（无需图像库，手写 PNG 编码）。
// 比 1x1 占位图大、有真实色块内容，用来验证 Bedrock 图像 sanitize 不再 400。
import { deflateSync } from "node:zlib";
function makePng(): Buffer {
  const W = 64, H = 64;
  const raw = Buffer.alloc(H * (1 + W * 3));
  let o = 0;
  for (let y = 0; y < H; y++) {
    raw[o++] = 0; // filter byte
    for (let x = 0; x < W; x++) {
      if (x < W / 2) { raw[o++] = 220; raw[o++] = 30; raw[o++] = 30; }   // red
      else { raw[o++] = 30; raw[o++] = 30; raw[o++] = 220; }             // blue
    }
  }
  const crcTable = (() => {
    const t: number[] = [];
    for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; }
    return t;
  })();
  const crc32 = (buf: Buffer) => { let c = 0xffffffff; for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  const chunk = (type: string, data: Buffer) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const typeBuf = Buffer.from(type, "ascii");
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])));
    return Buffer.concat([len, typeBuf, data, crc]);
  };
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 8; ihdr[9] = 2; // 8-bit RGB
  const idat = deflateSync(raw);
  return Buffer.concat([sig, chunk("IHDR", ihdr), chunk("IDAT", idat), chunk("IEND", Buffer.alloc(0))]);
}

async function main() {
  console.log(`[01] region=${REGION} base=${BASE_URL} model=${MODEL}`);
  const client = new OpenAI({ baseURL: BASE_URL, apiKey: "unused", fetch: sigv4Fetch });

  // (a) 纯文本 —— 证 SigV4 + chat-completions 通
  console.log("\n[01a] text-only ...");
  const t = await client.chat.completions.create({
    model: MODEL,
    messages: [{ role: "user", content: "Reply with exactly one word: ok" }],
    max_tokens: 16,
  });
  console.log("[01a] OK content=", JSON.stringify(t.choices[0]?.message?.content));

  // (b) 视觉 —— 合格 PNG，证 image_url 过 sanitize 且能识别
  console.log("\n[01b] vision (64x64 real png) ...");
  const b64 = makePng().toString("base64");
  const v = await client.chat.completions.create({
    model: MODEL,
    messages: [{
      role: "user",
      content: [
        { type: "text", text: "This image has two halves of different colors. Answer with exactly two words: left color and right color." },
        { type: "image_url", image_url: { url: `data:image/png;base64,${b64}` } },
      ] as any,
    }],
    max_tokens: 32,
  });
  console.log("[01b] OK content=", JSON.stringify(v.choices[0]?.message?.content));

  console.log("\n[01] PASS — 模型连接（文本+视觉）SigV4 自签全通");
}

main().catch((e) => {
  console.error("[01] FAIL:", e?.status ?? "", e?.message ?? e);
  if (e?.error) console.error("     body:", JSON.stringify(e.error).slice(0, 400));
  process.exit(1);
});
