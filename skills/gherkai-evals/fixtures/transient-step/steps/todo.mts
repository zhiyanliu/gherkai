// 待办清单的确定性 step（Midscene 引擎）。判定逻辑在 _checks.mts；与 todo.py 成对。
import { deterministic } from "@gherkai/worker-midscene";
import { deleteThenUndoKeepsItem } from "./_checks.mts";

deterministic(
  '删除 "(?<text>[^"]+)" 后立刻撤销，条目仍在',
  async ({ page }, { text }) => { await deleteThenUndoKeepsItem(page, text); },
  { description: "删除给定条目后立刻点撤销，断言条目仍在列表里（精确判定，不走 AI）", example: 'When 删除 "买牛奶" 后立刻撤销，条目仍在' },
);
