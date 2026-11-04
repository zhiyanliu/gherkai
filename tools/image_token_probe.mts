// 图片 token 探针：同一张截图缩到不同尺寸后，模型侧 prompt_tokens 怎么变（「截图缩放降低 token」评估的离线第一步；结论见 ADR 0052 被拒方案节，换模型时重议用）。
//
// 做什么：读一张或多张 PNG 截图，用与生产同一种编码（Midscene 的 resizeBase64ImageToJpeg，JPEG 质量 90）缩到给定的除数 k，
// 对每个尺寸各发三类请求——「带图、无 detail」（生产的定位与规划请求经 lib/agentcore-sigv4 的方言适配后的形态）、「带图、detail
// high」（生产的断言请求形态）、「纯文本对照」——每类 N 次，记服务端返回的 usage.prompt_tokens，打印一张表并给出图片 token
// 的估算（带图请求减纯文本对照）。本仓库在签名前删掉 `detail: "original"`，Bedrock 对无 detail 的图是否在服务端缩图、图片
// token 是否随尺寸下降，都只能靠这张表回答。
//
// 运行（需要 AWS 凭证与 region，且凭证能在该 region 的 Bedrock 上调用生产所用的模型）：
//   cd engines/midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx ../../tools/image_token_probe.mts <png>... [--k 1,2,2.625,3] [--n 3] [--json out.json]
// 模型取 lib/agentcore-sigv4 的 MODEL（可用 MIDSCENE_MODEL_ID 覆盖），与生产同一个。请求只问一句「用一个词回答图里是什么」、
// max_completion_tokens 16（GPT-5 系列不接受 max_tokens），花费可忽略。输出不含任何凭证；打印的只有尺寸、字节数与 token 数。
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { sigv4Fetch, getBaseUrl, MODEL } from "../engines/midscene/src/lib/agentcore-sigv4.mjs";

// 第三方包按引擎目录解析：本文件在仓库根的 tools/ 下，裸包名从这里向上找不到 node_modules，所以借引擎的 package.json 建一个 require。
const engineRequire = createRequire(new URL("../engines/midscene/package.json", import.meta.url));
const OpenAI = engineRequire("openai").default ?? engineRequire("openai");
const { resizeBase64ImageToJpeg, imageInfoOfBase64 } = engineRequire("@midscene/shared/img");
type OpenAIClient = InstanceType<typeof OpenAI>;

type Row = { file: string; k: number; width: number; height: number; bytes: number; mode: "image" | "image-high" | "text"; prompt_tokens: number[] };

function parseArgs(argv: string[]) {
  const files: string[] = []; let ks = [1, 2, 2.625, 3]; let n = 3; let jsonOut: string | null = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--k") ks = argv[++i].split(",").map(Number);
    else if (a === "--n") n = Number(argv[++i]);
    else if (a === "--json") jsonOut = argv[++i];
    else files.push(a);
  }
  if (files.length === 0) throw new Error("用法：image_token_probe.mts <png>... [--k 1,2,3] [--n 3] [--json out.json]");
  return { files, ks, n, jsonOut };
}

async function promptTokens(client: OpenAIClient, content: unknown): Promise<number> {
  const r = await client.chat.completions.create({ model: MODEL, max_completion_tokens: 16, messages: [{ role: "user", content }] as never });
  const u = r.usage?.prompt_tokens;
  if (typeof u !== "number") throw new Error(`响应里没有 usage.prompt_tokens：${JSON.stringify(r.usage)}`);
  return u;
}

async function main() {
  const { files, ks, n, jsonOut } = parseArgs(process.argv.slice(2));
  const client = new OpenAI({ baseURL: getBaseUrl(), apiKey: "unused", fetch: sigv4Fetch });
  const rows: Row[] = [];
  const text = "用一个词回答：这张图里主要是什么？";
  const textOnly: number[] = [];
  for (let i = 0; i < n; i++) textOnly.push(await promptTokens(client, "用一个词回答：天空通常是什么颜色？"));
  rows.push({ file: "-", k: 0, width: 0, height: 0, bytes: 0, mode: "text", prompt_tokens: textOnly });
  for (const file of files) {
    const png = readFileSync(file);
    const pngB64 = `data:image/png;base64,${png.toString("base64")}`;
    const info = await imageInfoOfBase64(pngB64);
    for (const k of ks) {
      const target = { width: Math.max(1, Math.round(info.width / k)), height: Math.max(1, Math.round(info.height / k)) };
      const jpeg = await resizeBase64ImageToJpeg(pngB64, { targetSize: target, jpegQuality: 90 });  // 与 Midscene 送模型前的编码相同
      const bytes = Buffer.from(jpeg.split(",")[1], "base64").length;
      for (const mode of ["image", "image-high"] as const) {
        const img: Record<string, unknown> = { url: jpeg };
        if (mode === "image-high") img.detail = "high";
        const tokens: number[] = [];
        for (let i = 0; i < n; i++) tokens.push(await promptTokens(client, [{ type: "text", text }, { type: "image_url", image_url: img }]));
        rows.push({ file, k, ...target, bytes, mode, prompt_tokens: tokens });
        console.log(`${file} k=${k} ${target.width}x${target.height} ${bytes}B ${mode}: prompt_tokens=${tokens.join("/")}`);
      }
    }
  }
  const base = Math.round(textOnly.reduce((a, b) => a + b, 0) / textOnly.length);
  console.log(`\n纯文本对照 prompt_tokens=${textOnly.join("/")}（均值 ${base}）`);
  console.log("\n文件 | k | 尺寸 | 字节 | 模式 | prompt_tokens 均值 | 图片 token 估算（减纯文本对照）");
  for (const r of rows) {
    if (r.mode === "text") continue;
    const mean = r.prompt_tokens.reduce((a, b) => a + b, 0) / r.prompt_tokens.length;
    console.log(`${r.file} | ${r.k} | ${r.width}x${r.height} | ${r.bytes} | ${r.mode} | ${mean.toFixed(1)} | ${(mean - base).toFixed(1)}`);
  }
  if (jsonOut) writeFileSync(jsonOut, JSON.stringify({ model: MODEL, text_only: textOnly, rows }, null, 2));
}

main().catch((e) => { console.error("探针失败：", e?.status ?? "", e?.message ?? e); process.exit(1); });
