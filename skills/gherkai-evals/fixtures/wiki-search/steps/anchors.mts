// 项目自写的确定性 step（Midscene 引擎，TypeScript）。与 steps/anchors.py 成对：同一正则、同一元数据。
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '页面标题包含 "(?<word>[^"]+)"',
  async ({ page }, { word }) => {
    const title = await page.title();
    if (!title.includes(word)) {
      throw new DeterministicAssertion(`页面标题应包含 ${JSON.stringify(word)}，实际是 ${JSON.stringify(title)}`);
    }
  },
  { description: "精确检查浏览器标题是否包含给定文字（不走 AI）", example: 'Then 页面标题包含 "Python"' },
);
