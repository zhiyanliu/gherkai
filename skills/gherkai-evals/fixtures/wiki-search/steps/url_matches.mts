// 项目自写的确定性 step（Midscene 引擎）：断言当前页面地址匹配给定正则。与 steps/url_matches.py 成对：同一正则、同一元数据。
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
