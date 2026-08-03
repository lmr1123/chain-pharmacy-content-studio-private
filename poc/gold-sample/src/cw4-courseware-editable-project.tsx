/**
 * Bridge: Revideo editor (Vite root = gold-sample) loads courseware-4 project.
 */
import {makeProject} from '@revideo/core';

import baseProject from '../../../production-library/validation/courseware/product-courseware-4-faithful-replica-v1/src/project';

const withPlugin = <T extends {plugins?: string[]}>(scene: T): T => ({
  ...scene,
  plugins: [...(scene.plugins ?? []), 'wind-heat-editable-plugin'],
});

export default makeProject({
  name: 'product-courseware-4-editable',
  scenes: (baseProject.scenes ?? []).map(scene => withPlugin(scene)),
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#cecbc4',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
