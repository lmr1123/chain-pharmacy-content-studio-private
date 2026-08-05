/**
 * 速福达商品培训课件 · 业务可编辑入口
 * 复用 wind-heat-editable-plugin（editable: 前缀），本场景元素使用 editable:sufuda:*。
 */
import {makeProject} from '@revideo/core';

import baseProject from './project';

const withPlugin = <T extends {plugins?: string[]}>(scene: T): T => ({
  ...scene,
  plugins: [...(scene.plugins ?? []), 'wind-heat-editable-plugin'],
});

export default makeProject({
  name: 'sufuda-product-courseware-3-editable',
  scenes: (baseProject.scenes ?? []).map(scene => withPlugin(scene)),
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      // 珍珠白底，避免马赛克透出
      background: '#f7f5f2',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
