// 项目自写的确定性 step（Midscene 引擎）。
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '页面标题包含 "(?<text>[^"]+)"',
  async ({ page }, { text }) => {
    try {
      await page.waitForFunction((t: string) => document.title.includes(t), text, { timeout: 5000 });
    } catch {
      throw new DeterministicAssertion(`标题应包含 ${JSON.stringify(text)}，实际 ${JSON.stringify(await page.title())}（页面 ${page.url()}）`);
    }
  },
  { description: "断言页面标题包含给定文本（精确判定，不走 AI）", example: 'Then 页面标题包含 "示例商店"' },
);
