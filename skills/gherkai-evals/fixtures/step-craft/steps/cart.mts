// 项目自写的确定性 step（Midscene 引擎）。
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '元素 "(?<sel>[^"]+)" 可见',
  async ({ page }, { sel }) => {
    if (!(await page.locator(sel).isVisible())) {
      throw new DeterministicAssertion("元素不可见");
    }
  },
  { description: "断言选择器命中的元素可见（精确判定，不走 AI）", example: 'Then 元素 "#cart-count" 可见' },
);
