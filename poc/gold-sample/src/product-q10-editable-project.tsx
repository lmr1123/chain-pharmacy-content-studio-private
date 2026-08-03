/**
 * 辅酶 Q10 商品培训视频 · 业务可编辑工程
 * 复用 wind-heat-editable-plugin（画面属性面板 · 点选/拖拽/改字换图/导出）
 * 稳定图层前缀：editable:q10:*
 */
import {makeProject} from '@revideo/core';

import {productTrainingOpeningScene} from './product-training-opening-project';
import {productTrainingBrandOverviewScene} from './product-training-brand-overview-project';
import {productTrainingFaithfulScene} from './product-training-faithful-project';
import {productTrainingEfficacyScene} from './product-training-efficacy-project';
import {productTrainingFeaturesScene} from './product-training-features-project';
import {productTrainingAudienceScene} from './product-training-audience-project';
import {productTrainingCombinationScene} from './product-training-combination-project';
import {productTrainingSummaryScene} from './product-training-summary-project';

const withPlugin = <T extends {plugins?: (string | object)[]}>(scene: T): T => ({
  ...scene,
  plugins: [...(scene.plugins ?? []), 'wind-heat-editable-plugin'],
});

export default makeProject({
  name: 'product.q10.full-editable-v1',
  scenes: [
    productTrainingOpeningScene,
    productTrainingBrandOverviewScene,
    productTrainingFaithfulScene,
    productTrainingEfficacyScene,
    productTrainingFeaturesScene,
    productTrainingAudienceScene,
    productTrainingCombinationScene,
    productTrainingSummaryScene,
  ].map(scene => withPlugin(scene)),
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#83cfea',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
