import {makeProject} from '@revideo/core';
import {referenceNativeIntroCanonicalScene} from './reference-native-intro-project';
import {referenceCharacterBodyScene} from './reference-replica-project';
import {referenceMechanismGapScene} from './reference-mechanism-gap-project';
import {referenceSymptomsCanonicalScene} from './reference-symptoms-project';
import {referenceTreatmentScene} from './reference-treatment-project';
import {referenceMedicationAdviceScene} from './reference-medication-advice-project';
import {referenceSummaryOutroScene} from './reference-summary-outro-project';
import {WIND_HEAT_COURSE_MODEL} from './wind-heat-course-model';

const editable = <T extends {plugins?: (string | object)[]}>(scene: T): T => ({
  ...scene,
  plugins: [...(scene.plugins ?? []), 'wind-heat-editable-plugin'],
});

export default makeProject({
  name: WIND_HEAT_COURSE_MODEL.projectId,
  scenes: WIND_HEAT_COURSE_MODEL.scenes.map(scene =>
    editable({
      intro: referenceNativeIntroCanonicalScene,
      character: referenceCharacterBodyScene,
      mechanism: referenceMechanismGapScene,
      symptoms: referenceSymptomsCanonicalScene,
      treatment: referenceTreatmentScene,
      medication: referenceMedicationAdviceScene,
      summary: referenceSummaryOutroScene,
    }[scene.id]),
  ),
  settings: {
    shared: {
      size: {x: 1920, y: 1080},
      background: '#020a15',
    },
    rendering: {fps: 30},
    preview: {fps: 30},
  },
});
