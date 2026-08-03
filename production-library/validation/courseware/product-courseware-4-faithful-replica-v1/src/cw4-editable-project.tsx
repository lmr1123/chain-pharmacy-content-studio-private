/**
 * 课件4 · 业务可编辑入口（挂 wind-heat-editable-plugin）
 * 稳定图层前缀：editable:cw4:*
 */
import {makeProject} from '@revideo/core';

import baseProject from './project';

const withPlugin = <T extends {plugins?: string[]}>(scene: T): T => ({
  ...scene,
  plugins: [...(scene.plugins ?? []), 'wind-heat-editable-plugin'],
});

export default makeProject({
  name: 'product-courseware-4-editable',
  scenes: (baseProject.scenes ?? []).map(scene => withPlugin(scene as {plugins?: string[]})),
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#cecbc4',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
