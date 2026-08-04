/**
 * fluent-ffmpeg 对 ffmpeg 7/8 `-formats` 输出中 lavfi 行的标志列解析失败
 * （行首为 " D  lavfi"，regex 期望第二列是 E/空格），导致 Revideo 无音轨工程
 * 生成静音轨时报 "Input format lavfi is not available"。
 * 这里在 getAvailableFormats 结果里补 lavfi 条目；fluent-ffmpeg 的 formats 缓存
 * 是模块级同对象引用，补丁一并写入缓存。
 * 必须在 renderVideo() 执行前 import（同进程生效）。
 */
// tsx 以 CommonJS 运行本工程（tsconfig module: CommonJS），require 直接可用
// eslint-disable-next-line @typescript-eslint/no-var-requires
const ffmpeg: any = require('fluent-ffmpeg');

const proto = ffmpeg.prototype;
for (const name of ['getAvailableFormats', 'availableFormats']) {
  const orig = proto[name];
  proto[name] = function (cb: any) {
    return orig.call(this, (err: any, formats: any) => {
      if (!err && formats && !formats.lavfi) {
        formats.lavfi = {
          description: 'Libavfilter virtual input device',
          canDemux: true,
          canMux: false,
        };
      }
      cb(err, formats);
    });
  };
}
