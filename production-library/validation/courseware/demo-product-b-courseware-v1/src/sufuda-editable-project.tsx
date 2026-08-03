/**
 * 速福达商品培训课件 · 业务可编辑入口
 * 复用 wind-heat-editable-plugin（editable: 前缀），本场景元素使用 editable:sufuda:*。
 */
import project from './project';

const withPlugin = <T extends {plugins?: (string | object)[]}>(scene: T): T => ({
  ...scene,
  plugins: [...(scene.plugins ?? []), 'wind-heat-editable-plugin'],
});

const base = project as {
  name?: string;
  scenes: Array<{plugins?: (string | object)[]}>;
  settings?: unknown;
};

export default {
  ...base,
  name: 'sufuda-product-courseware-3-editable',
  scenes: (base.scenes ?? []).map(scene => withPlugin(scene)),
};
