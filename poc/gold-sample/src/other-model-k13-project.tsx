/**
 * Thin render bridge for K13 independent scene under
 * other-model-remake-attempt-v1.
 */
import {makeProject} from '@revideo/core';
import {k13Scene} from '../../../production-library/validation/reference-analysis/kekang-pfizer-framework-v1/production-v2/qa/other-model-remake-attempt-v1/src/k13-scene';

export default makeProject({
  scenes: [k13Scene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
