// 设备部件的缺省装配（ADR 0052 决策 3 的模块划分）：把各设备模块的真实实现装成设备侧接缝（device/surface.mts）的 DeviceParts，
// 每个 scope 装配一次。只组装、不做 I/O：Device Farm 与 S3 客户端惰性构造，WebdriverIO 实例到建连时才建。缺本次运行编号时同步抛出
// （会话名不能缺 run 段，ADR 0051 决策 3）。
//
// 装配约定：
//   - Device Farm 会话块与终结块是同一个会话块实例，两者共享会话登记（待清理集、待核尝试与在途的 Create，ADR 0051 决策 5）；
//   - 本次运行编号由会话块从部件环境的 processEnv 读（接缝的构造项可注入它），不另读进程 env；
//   - 能力探测读 iOS 坐标比例的只读命令取 XCUITest 适配器的导出，本文件不写 `mobile:` 命令（ADR 0052 决策 4）；
//   - 适配器清单按会话回报的 automationName 每次选出一个新实例，适配器按会话缓存的结论只属于一个会话；
//   - 常量一律取 device/limits.mts。
//
// 接缝模块静态 import 本文件，本文件再静态带到 WebdriverIO 与 Device Farm SDK：镜像里的设备依赖冒烟只 import 接缝模块，靠这条
// 静态闭包才拦得住依赖没装进镜像（engines/midscene/Dockerfile；护栏见 device/surface.test.mts）。接缝模块与各块因此互相 import：
// 本文件只取接缝模块的类型，各块只在函数体内读它导出的消息常量、模块顶层不读，循环里不会读到未初始化的值。
import { s3AppObjectStore } from "./app.mjs";
import { createAppiumConnector } from "./appium.mjs";
import { createDeviceFinalizer } from "./finalize.mjs";
import { commandGuardFactory } from "./guard.mjs";
import { adapterRegistry, deviceAgentFactory, type DeviceAdapter } from "./interface.mjs";
import { DEEP_LINK_FOREGROUND_POLL_ATTEMPTS, DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS } from "./limits.mjs";
import { createCapabilityProbe } from "./probe.mjs";
import { createDeviceFarmSessions } from "./session.mjs";
import type { DeviceParts, DevicePartsEnv } from "./surface.mjs";
import { createDeviceWarmup } from "./warmup.mjs";
import { uiautomator2Entry } from "./adapters/uiautomator2.mjs";
import { deviceScreenInfo, xcuitestEntry } from "./adapters/xcuitest.mjs";

/** 缺省的部件装配（接缝的 DevicePartsFactory）。 */
export function defaultDeviceParts(env: DevicePartsEnv): DeviceParts<DeviceAdapter> {
  const sessions = createDeviceFarmSessions(env);
  return {
    sessions,
    finalizer: createDeviceFinalizer(sessions),
    appium: createAppiumConnector({ log: env.log }),
    probe: createCapabilityProbe({ deviceScreenInfo, log: env.log }),
    adapters: adapterRegistry([
      xcuitestEntry,
      uiautomator2Entry({
        foregroundPoll: { attempts: DEEP_LINK_FOREGROUND_POLL_ATTEMPTS, intervalMs: DEEP_LINK_FOREGROUND_POLL_INTERVAL_MS },
      }),
    ]),
    guards: commandGuardFactory,
    agents: deviceAgentFactory,
    warmup: createDeviceWarmup({ log: env.log, now: env.now }),
    appStore: s3AppObjectStore(),
  };
}
