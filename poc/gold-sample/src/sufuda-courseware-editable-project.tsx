/**
 * Bridge entry so the Revideo editor loads the sufuda gold project from inside
 * poc/gold-sample (stable Vite root + JSX runtime), while the real scene source
 * stays in production-library/validation/courseware/sufuda-product-courseware-3-gold-v1.
 */
import {makeProject} from '@revideo/core';

// Relative path from poc/gold-sample/src → validation gold
import baseProject from '../../../production-library/validation/courseware/sufuda-product-courseware-3-gold-v1/src/project';

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
      background: '#f7f5f2',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
