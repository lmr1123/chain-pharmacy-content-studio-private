import {makeProject} from '@revideo/core';
import {k16RelationScene} from './kekang-k16-relation-scene';

export default makeProject({
  scenes: [k16RelationScene],
  settings: {shared: {size: {x: 1920, y: 1080}}},
});
