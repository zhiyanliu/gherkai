// agentcore-sigv4 单测（ADR 0033 / 0016 决策 C：Midscene region 全可配、不再硬编码 us-east-1）。
// 跑：node --import tsx --test worker/agentcore-sigv4.test.ts。纯逻辑、不连 AWS。
//
// 锁住三点：① getBaseUrl/getRegion 跟 process.env.AWS_REGION 走（证明 region 不再硬编码 east——注入 west
// 就该拿到 west 的 endpoint）；② 缺 AWS_REGION → fail-loud（对齐 Nova region=None→NoRegionError）；
// ③ 模型选择（ADR 0044）：家族推断表逐条、显式 env 优先、推不出即抛（见文件末那组）。
// **惰性求值是关键**（见 agentcore-sigv4.mts 注释）：这两个是函数、import 本模块不触发 region 校验，
// 故纯逻辑测试（run-scope 的派发/投票）import 链碰到它时不被误伤——本测试正是验「用时才 fail-loud」。
import { test } from "node:test";
import assert from "node:assert";
import { getRegion, getBaseUrl, modelFamily, MODEL, DEFAULT_MODEL, bedrockCompatBody } from "../lib/agentcore-sigv4.mjs";

function withRegion<T>(value: string | undefined, fn: () => T): T {
  const saved = process.env.AWS_REGION;
  if (value === undefined) delete process.env.AWS_REGION;
  else process.env.AWS_REGION = value;
  try {
    return fn();
  } finally {
    if (saved === undefined) delete process.env.AWS_REGION;
    else process.env.AWS_REGION = saved;
  }
}

test("getRegion/getBaseUrl 跟 AWS_REGION 走（region 可配，非硬编码 east）", () => {
  withRegion("us-west-2", () => {
    assert.equal(getRegion(), "us-west-2");
    assert.equal(getBaseUrl(), "https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1");
  });
  // 换个区证明真跟 env 走（若还硬编码 east，下面会失败）
  withRegion("eu-central-1", () => {
    assert.equal(getBaseUrl(), "https://bedrock-runtime.eu-central-1.amazonaws.com/openai/v1");
  });
});

test("缺 AWS_REGION → fail-loud（对齐 Nova region=None→NoRegionError）", () => {
  withRegion(undefined, () => {
    assert.throws(() => getRegion(), /AWS_REGION/);
    assert.throws(() => getBaseUrl(), /AWS_REGION/);  // getBaseUrl 经 getRegion 传导 fail-loud
  });
});


// ---- 模型家族推断 modelFamily（ADR 0044 决策 2）：显式 env 优先、否则按 id 推断、推不出即抛 ----
// 家族决定 Midscene 用哪套提示词与请求参数，猜错是**静默劣化**（不报错、判定悄悄变差），故这里逐条钉住推断表：
// 表里少一项 / 锚错位置，对应那行即红。
function withFamilyEnv<T>(value: string | undefined, fn: () => T): T {
  const saved = process.env.MIDSCENE_MODEL_FAMILY;
  if (value === undefined) delete process.env.MIDSCENE_MODEL_FAMILY;
  else process.env.MIDSCENE_MODEL_FAMILY = value;
  try {
    return fn();
  } finally {
    if (saved === undefined) delete process.env.MIDSCENE_MODEL_FAMILY;
    else process.env.MIDSCENE_MODEL_FAMILY = saved;
  }
}

test("modelFamily: 推断表逐条命中（含 inference profile 的 us./global. 前缀形态）", () => {
  withFamilyEnv(undefined, () => {
    const cases: [string, string][] = [
      ["qwen.qwen3-vl-235b-a22b", "qwen3-vl"],
      ["openai.gpt-6-astra", "gpt-6"],
      ["us.openai.gpt-6-astra", "gpt-6"],          // inference profile：带 region 前缀也得命中（锚首就漏）
      ["global.openai.gpt-6-astra", "gpt-6"],
      ["us.openai.gpt-5-6-sol", "gpt-5"],
      ["global.openai.gpt-5-6-luna", "gpt-5"],
      ["moonshotai.kimi-k2.5-instruct", "kimi"],
      ["us.moonshotai.kimi-k2-thinking", "kimi"],
      ["moonshotai.kimi-k3-instruct", "kimi3"],    // k3 是另一个家族，别被 k2 那行吃掉
      ["deepseek.r1-v1:0", "deepseek"],
      ["zai.glm-4.6v", "glm-v"],
    ];
    for (const [id, family] of cases) assert.equal(modelFamily(id), family, id);
  });
});

test("modelFamily: 显式 MIDSCENE_MODEL_FAMILY 优先于推断（使用方能压过我们的表）", () => {
  withFamilyEnv("doubao-seed", () => {
    assert.equal(modelFamily("qwen.qwen3-vl-235b-a22b"), "doubao-seed");  // 推断本会给 qwen3-vl
    assert.equal(modelFamily("完全没见过的-id"), "doubao-seed");            // 推不出也不抛：显式即答案
  });
});

test("modelFamily: 推不出且未显式指定 → 抛，且信息点名 MIDSCENE_MODEL_FAMILY（宁可拒绝，不猜家族）", () => {
  withFamilyEnv(undefined, () => {
    for (const id of ["nonexistent.model-x", "anthropic.claude-sonnet-4-5-20250929-v1:0", "amazon.nova-lite-v1:0"]) {
      assert.throws(() => modelFamily(id), (e: Error) => {
        assert.match(e.message, /MIDSCENE_MODEL_FAMILY/, `得告诉使用者怎么办：${e.message}`);
        assert.ok(e.message.includes(id), `得说清是哪个模型：${e.message}`);
        return true;
      }, id);
    }
  });
});

test("modelFamily: 默认模型自身必须推得出家族（换默认却忘了进推断表 → worker 起不来）", () => {
  withFamilyEnv(undefined, () => {
    assert.ok(modelFamily(DEFAULT_MODEL).length > 0);  // 不写死家族名：默认模型随发版评估会换（ADR 0044 决策 1）
  });
});

test("MODEL 缺省 = DEFAULT_MODEL（MIDSCENE_MODEL_ID 覆盖那条在 run-scope 的真子进程用例里）", () => {
  // MODEL 在 import 时定值（模块级读 env），故本条只在跑测试的 shell 未设覆盖时有意义。
  if (process.env.MIDSCENE_MODEL_ID) return;
  assert.equal(MODEL, DEFAULT_MODEL);
});

test("DEFAULT_MODEL 钉的是具体 id：换默认得连这条字面量一起改（刻意的升级闸门，对称 Nova 那条）", () => {
  // 换默认模型 = 换判定，流程是「评测集 A/B + 随发版并在 Release 正文点明」；字面量在这里是闸门、不是脆弱断言。
  assert.equal(DEFAULT_MODEL, "qwen.qwen3-vl-235b-a22b");
});

test("modelFamily: inference profile 形态（us./global. 前缀）对 qwen / deepseek 也推得出", () => {
  assert.equal(modelFamily("us.qwen.qwen3-vl-235b-a22b"), "qwen3-vl");
  assert.equal(modelFamily("global.deepseek.v4-flash-vision"), "deepseek");
});

// ---- Bedrock 兼容层方言：image_url.detail "original" 去掉（ADR 0044 决策 3；跳板机实测 Bedrock 对任何模型都拒该值）----
test("bedrockCompatBody: 只删 detail:original，其余字段与顺序原样；high / 无 detail / 非 JSON 都不动", () => {
  const body = JSON.stringify({ model: "us.openai.gpt-6-astra", reasoning_effort: "low", messages: [
    { role: "system", content: "sys" },
    { role: "user", content: [{ type: "text", text: "t" }, { type: "image_url", image_url: { url: "data:image/jpeg;base64,AAA", detail: "original" } }] },
    { role: "user", content: [{ type: "image_url", image_url: { url: "data:image/png;base64,BBB", detail: "high" } }] },
  ] });
  const out = JSON.parse(bedrockCompatBody(body));
  assert.equal(out.messages[1].content[1].image_url.detail, undefined, "original 该被去掉");
  assert.equal(out.messages[1].content[1].image_url.url, "data:image/jpeg;base64,AAA");
  assert.equal(out.messages[2].content[0].image_url.detail, "high", "high 不动");
  assert.equal(out.reasoning_effort, "low");
  const untouched = JSON.stringify({ model: "m", messages: [{ role: "user", content: "plain" }] });
  assert.equal(bedrockCompatBody(untouched), untouched, "没有要改的就原样返回（同一字符串）");
  assert.equal(bedrockCompatBody("not json"), "not json");
  assert.equal(bedrockCompatBody(bedrockCompatBody(body)), bedrockCompatBody(body), "幂等");
});
