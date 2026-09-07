// agentcore-sigv4 单测（ADR 0033 / 0016 决策 C：Midscene region 全可配、不再硬编码 us-east-1）。
// 跑：node --import tsx --test worker/agentcore-sigv4.test.ts。纯逻辑、不连 AWS。
//
// 锁住两点：① getBaseUrl/getRegion 跟 process.env.AWS_REGION 走（证明 region 不再硬编码 east——注入 west
// 就该拿到 west 的 endpoint）；② 缺 AWS_REGION → fail-loud（对齐 Nova region=None→NoRegionError）。
// **惰性求值是关键**（见 agentcore-sigv4.mts 注释）：这两个是函数、import 本模块不触发 region 校验，
// 故纯逻辑测试（run-scope 的派发/投票）import 链碰到它时不被误伤——本测试正是验「用时才 fail-loud」。
import { test } from "node:test";
import assert from "node:assert";
import { getRegion, getBaseUrl } from "../lib/agentcore-sigv4.mjs";

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
