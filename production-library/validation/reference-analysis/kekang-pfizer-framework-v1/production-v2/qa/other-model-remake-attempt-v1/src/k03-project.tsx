import {makeProject} from '@revideo/core';
import {k03Scene} from './k03-scene';

export default makeProject({
  scenes: [k03Scene],
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
