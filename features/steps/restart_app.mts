// 示范用确定性 step（Midscene 侧）：重新启动被测应用，让后面的步骤从应用刚启动时的界面开始。
//
// 这是 `steps/` 目录的模板：复制进你的项目后按需改措辞。设备目标上同一个 scope 的 scenario 共用一个远程访问会话，
// scenario 之间不重启应用；需要干净起点的用例在 Background 里写这一步。运行时经 `--steps-dir features/steps` 或环境变量
// `GHERKAI_STEPS_DIR` 加载进 worker 的注册表。
//
// 只有一个 webdriver 条目，只覆盖应用目标：`ctx.app` 只在应用目标上有值，`restart()` 关闭被测应用、再启动它，并确认它
// 启动后没有自行退出（自行退出时这一步记 error）。桌面与设备网页上这条 step 没有实现，写在那些目标上会交给 AI 执行，
// plan 里可以看到。没有 Nova Act 侧的成对文件：Nova Act 没有设备目标。
import { deterministic } from "@gherkai/worker-midscene";

deterministic(
  "^重新启动应用$",
  {
    webdriver: {
      uiKinds: ["app"],
      handler: async ({ app }) => {
        await app!.restart(); // 条目只覆盖应用目标，app 在这里一定有值
      },
    },
  },
  {
    description: "重新启动被测应用，后面的步骤从应用刚启动时的界面开始",
    example: "Given 重新启动应用",
    keywords: ["Given", "When"],
  },
);
