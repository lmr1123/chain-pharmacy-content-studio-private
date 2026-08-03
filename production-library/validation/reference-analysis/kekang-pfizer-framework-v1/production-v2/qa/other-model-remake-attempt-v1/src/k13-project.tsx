import {makeProject} from '@revideo/core';
import {k13Scene} from './k13-scene';

export default makeProject({
  scenes: [k13Scene],
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
    },
    rendering: {
      fps: 30,
    },
    preview: {
      fps: 30,
    },
  },
});
