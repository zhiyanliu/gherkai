// 示范用确定性 step（Midscene 侧）：断言当前页面地址匹配给定正则。
//
// 这是 `steps/` 目录的模板：复制进你的项目后按需改措辞与判定。与 `url_matches.py` 成对（同一正则，具名组写法
// 不同），两个引擎读同一份 .feature 时行为一致。运行时经 `--steps-dir features/steps` 或环境变量
// `GHERKAI_STEPS_DIR` 加载进 worker 的注册表。
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '页面地址匹配 "(?<pattern>[^"]+)"', // [^"]+（非 .+）：防 step 里出现第二对引号时贪婪跨引号捕获
  ({ page }, { pattern }) => {
    const url = page.url();
    if (!new RegExp(pattern).test(url)) {
      throw new DeterministicAssertion(`页面地址应匹配 ${JSON.stringify(pattern)}，实际 ${JSON.stringify(url)}`);
    }
  },
  {
    description: "断言当前页面地址匹配给定正则（精确判定，不走 AI、不投票）",
    example: 'Then 页面地址匹配 "/wiki/OpenAI"',
    keywords: ["Then"],
  },
);
