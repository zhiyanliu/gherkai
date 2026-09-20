// 项目自写的确定性 step（Midscene 引擎）。
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '页面标题包含 "(?<text>[^"]+)"',
  async ({ page }, { text }) => {
    const title = await page.title();
    if (!title.includes(text)) {
      throw new DeterministicAssertion(`标题 ${title} 不含 ${text}`);
    }
  },
  { description: "断言页面标题包含给定文本（精确判定，不走 AI）", example: 'Then 页面标题包含 "示例商店"' },
);
