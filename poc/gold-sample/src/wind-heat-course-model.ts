import {
  PRESENTER_RIG,
  MOTION_TOKENS,
  STYLE_TOKENS,
  SUBTITLE_TOKENS,
  VOICE_PROFILE,
} from './wind-heat-production-contract';

export type WindHeatSceneId =
  | 'intro'
  | 'character'
  | 'mechanism'
  | 'symptoms'
  | 'treatment'
  | 'medication'
  | 'summary';

export type WindHeatSceneContract = {
  id: WindHeatSceneId;
  sceneId: string;
  startFrame: number;
  endFrame: number;
  activeChapter: string;
  audio: string | null;
  editableRoles: readonly string[];
};

export const WIND_HEAT_SCENES: readonly WindHeatSceneContract[] = [
  {
    id: 'intro',
    sceneId: 'reference-native-intro',
    startFrame: 0,
    endFrame: 135,
    activeChapter: '基础认知',
    audio: '/wind-heat-audio-v2/intro-silence.wav',
    editableRoles: ['master', 'brand', 'notice', 'title', 'motion'],
  },
  {
    id: 'character',
    sceneId: 'reference-character-body',
    startFrame: 136,
    endFrame: 839,
    activeChapter: '基础认知',
    audio: '/reference-audio/qwen-cloned-reference-28s.wav',
    editableRoles: [
      'master',
      'presenter',
      'mouth',
      'symptom-card',
      'title',
      'equation',
      'subtitle',
    ],
  },
  {
    id: 'mechanism',
    sceneId: 'reference-mechanism-gap',
    startFrame: 840,
    endFrame: 1314,
    activeChapter: '病因机理',
    audio: '/reference-audio/qwen-cloned-mechanism-gap-v1.wav',
    editableRoles: [
      'master',
      'presenter',
      'pathogen',
      'body',
      'organ',
      'label',
      'subtitle',
      'motion',
    ],
  },
  {
    id: 'symptoms',
    sceneId: 'reference-typical-symptoms',
    startFrame: 1315,
    endFrame: 2104,
    activeChapter: '典型症状',
    audio: '/reference-audio/qwen-cloned-symptoms-semantic-v2.wav',
    editableRoles: [
      'master',
      'presenter',
      'card',
      'number',
      'title',
      'body',
      'illustration',
      'subtitle',
    ],
  },
  {
    id: 'treatment',
    sceneId: 'reference-treatment',
    startFrame: 2105,
    endFrame: 3362,
    activeChapter: '调理建议',
    audio: '/reference-audio/qwen-cloned-treatment-semantic-v2.wav',
    editableRoles: [
      'master',
      'presenter',
      'principle',
      'herb-card',
      'herb-asset',
      'recipe',
      'tea-asset',
      'subtitle',
    ],
  },
  {
    id: 'medication',
    sceneId: 'reference-medication-advice',
    startFrame: 3363,
    endFrame: 4595,
    activeChapter: '调理建议',
    audio: '/reference-audio/qwen-cloned-medication-advice-smooth-v2.wav',
    editableRoles: [
      'master',
      'presenter',
      'medication-card',
      'packshot',
      'advice-row',
      'advice-asset',
      'subtitle',
    ],
  },
  {
    id: 'summary',
    sceneId: 'reference-summary-outro',
    startFrame: 4596,
    endFrame: 5435,
    activeChapter: '重点总结',
    audio: '/reference-audio/qwen-cloned-summary-outro-v1.wav',
    editableRoles: [
      'master',
      'advice-row',
      'summary-cell',
      'brand-slot',
      'headline',
      'credit',
      'subtitle',
    ],
  },
] as const;

export const WIND_HEAT_COURSE_MODEL = {
  projectId: 'health.wind-heat.editable-v2',
  templateId: STYLE_TOKENS.templateId,
  stylePackId: STYLE_TOKENS.stylePackId,
  frameCount: 5436,
  durationSeconds: 181.2,
  contentLock: 'approved-script',
  referencePixelPolicy: 'measurement-only',
  masterComponentId: 'component.master.reference-medical-tech-native-v1',
  presenter: PRESENTER_RIG,
  voice: VOICE_PROFILE,
  subtitle: SUBTITLE_TOKENS,
  motion: MOTION_TOKENS,
  scenes: WIND_HEAT_SCENES,
} as const;

export function getWindHeatScene(id: WindHeatSceneId) {
  const scene = WIND_HEAT_SCENES.find(item => item.id === id);
  if (!scene) throw new Error(`Unknown wind-heat scene: ${id}`);
  return scene;
}
