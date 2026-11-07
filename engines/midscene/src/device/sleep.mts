// 设备模块共用的缺省等待：等待函数的类型 Sleep 与它的实现 defaultSleep。Appium 块、应用启停、能力探测、网页上下文的重新定位与
// UiAutomator2 适配器在调用方不注入等待时都用这一份。Device Farm 会话块的计时器（session.mts 的 Timers）语义不同：中止时以中止
// 原因拒绝，且与单次调用的上界作为一组注入（测试注入虚拟时钟），不用本模块。
//
// 语义：到时或调用方传入的中止信号中止时结束；中止时不抛出，由调用方在等待之后自己核对信号再决定是否继续（例如应用启动采样
// 在每次等待之后、发采样命令之前核对）。不传信号时就是普通的定时等待，不能被中止。结束时摘掉挂在信号上的监听。
//
// 本模块不 import 任何文件：接缝模块 device/surface.mts 经 parts.mts 静态 import appium.mts，appium.mts 又 import 接缝模块，两者
// 在同一个静态 import 循环里（见 parts.mts 头注释）；app.mts 与 web-context.mts 不在这个循环里，等待若由 appium.mts 导出，它们
// 从 appium.mts 取等待就会被带进循环。放在零依赖的独立模块里，各引用方 import 它不改变现有的 import 循环。
export type Sleep = (ms: number, signal?: AbortSignal) => Promise<void>;

export const defaultSleep: Sleep = (ms, signal) => new Promise((resolve) => {
  if (signal?.aborted) return resolve();
  const timer = setTimeout(done, ms);
  function done(): void {
    clearTimeout(timer);
    signal?.removeEventListener("abort", done);
    resolve();
  }
  signal?.addEventListener("abort", done, { once: true });
});
