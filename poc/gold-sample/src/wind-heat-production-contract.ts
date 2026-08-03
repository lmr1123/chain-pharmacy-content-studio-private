export const STYLE_TOKENS = {
  templateId: 'template.health-reference-tech-v1',
  stylePackId: 'style-pack.reference-medical-tech-v1',
  frame: {
    width: 1920,
    height: 1080,
    fps: 30,
    background: '#020a15',
  },
  colors: {
    text: '#f7faf8',
    cyan: '#35e5e8',
    panel: 'rgba(24, 42, 55, 0.96)',
    panelStroke: '#55adb6',
  },
  fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif',
} as const;

export const PRESENTER_RIG = {
  componentId: 'component.presenter.bound-pharmacist',
  mouthEffectId: 'effect.presenter.stable-mouth-v1',
  preserveIntrinsicAspectRatio: true,
  mouthStates: ['closed', 'small', 'o', 'wide'],
  mouthPalette: {
    line: '#d58d98',
    cavity: '#dfa0a9',
    tongue: '#f8c7cc',
    teeth: '#fffaf7',
    maxStrokeWidth: 1.35,
    maxOpacity: 0.9,
  },
  closedMouthSilenceMs: 80,
  mouthStepMs: {min: 120, max: 220},
  poses: {
    palm: {
      asset: '/wind-heat-presenter-v2/pharmacist-palm-mouthless.png',
      intrinsicSize: [334, 941],
      normalizedMouthAnchor: [0.551, 0.387],
      effectiveHeight: 1,
      footBaseline: 0.965,
      placementPreset: 'sideLeft',
    },
    openArms: {
      asset: '/wind-heat-presenter-v2/pharmacist-open-arms-mouthless.png',
      intrinsicSize: [415, 941],
      normalizedMouthAnchor: [0.544, 0.416],
      effectiveHeight: 1,
      footBaseline: 0.965,
      placementPreset: 'heroCenter',
    },
    point: {
      asset: '/wind-heat-presenter-v2/pharmacist-point-mouthless.png',
      intrinsicSize: [405, 941],
      normalizedMouthAnchor: [0.526, 0.415],
      effectiveHeight: 1,
      footBaseline: 0.965,
      placementPreset: 'sideLeft',
    },
    megaphone: {
      asset: '/wind-heat-presenter-v2/pharmacist-megaphone-mouthless.png',
      intrinsicSize: [462, 941],
      normalizedMouthAnchor: [0.526, 0.421],
      effectiveHeight: 1,
      footBaseline: 0.965,
      placementPreset: 'sideRight',
    },
  },
  placementPresets: {
    heroCenter: {
      anchor: [0.5, 0.965],
      effectiveHeightPx: 1000,
    },
    sideLeft: {
      anchor: [0.16, 0.965],
      effectiveHeightPx: 850,
    },
    sideRight: {
      anchor: [0.84, 0.965],
      effectiveHeightPx: 850,
    },
    supportLeft: {
      anchor: [0.14, 0.965],
      effectiveHeightPx: 760,
    },
    supportRight: {
      anchor: [0.86, 0.965],
      effectiveHeightPx: 760,
    },
  },
} as const;

export const VOICE_PROFILE = {
  voiceId: 'voice.reference-pharmacist-qwen-v1',
  engine: 'Qwen3-TTS 0.6B Base BF16',
  generateBySemanticBlock: true,
  forbidMicroCueTts: true,
  tempo: {
    default: 1.16,
    min: 1,
    max: 1.18,
  },
  loudness: {
    integratedLufs: -16,
    toleranceLu: 0.5,
    truePeakDbfs: -1.5,
    maxTruePeakDbfs: -1,
    maxSceneDeltaLu: 1,
  },
  crossfadeSeconds: 0.035,
  leadInSeconds: 0.06,
  leadOutSeconds: 0.1,
  sourceSampleRate: 24000,
  renderSampleRate: 48000,
  sourceChannels: 1,
  renderChannels: 2,
  filters: {
    highpassHz: 65,
    lowpassHz: 12000,
    declick: true,
  },
} as const;

export const SUBTITLE_TOKENS = {
  componentId: 'component.subtitle.reference-bottom',
  position: [0, 435],
  width: 1580,
  fontFamily: STYLE_TOKENS.fontFamily,
  fontSize: 52,
  fontWeight: 700,
  fill: '#ffffff',
  stroke: 'rgba(0, 0, 0, 0.96)',
  lineWidth: 2,
  shadowColor: 'rgba(0, 0, 0, 0.9)',
  shadowBlur: 5,
  textAlign: 'center',
  maxLines: 2,
  cueFadeSeconds: 0.04,
} as const;

export const MOTION_TOKENS = {
  electricCurrent: {
    componentId: 'effect.background.four-way-current-v1',
    halfPeriodSeconds: 1.2,
    color: '#d9ffff',
    glow: '#4feaf3',
    opacityRange: [0.12, 0.9],
  },
  cardEntry: {
    durationSeconds: 0.3,
    initialScale: 0.92,
  },
  traceBorder: {
    cycles: 2,
    thickness: 8,
    glow: '#73f8ff',
  },
  subtitleFadeSeconds: 0.04,
} as const;

export type PresenterPose = keyof typeof PRESENTER_RIG.poses;
export type PresenterPlacement = keyof typeof PRESENTER_RIG.placementPresets;

export function presenterLayout(
  poseName: PresenterPose,
  placementName?: PresenterPlacement,
) {
  const pose = PRESENTER_RIG.poses[poseName];
  const presetName =
    placementName ?? (pose.placementPreset as PresenterPlacement);
  const preset = PRESENTER_RIG.placementPresets[presetName];
  const [intrinsicWidth, intrinsicHeight] = pose.intrinsicSize;
  const height = preset.effectiveHeightPx / pose.effectiveHeight;
  const width = height * (intrinsicWidth / intrinsicHeight);
  const footX = (preset.anchor[0] - 0.5) * STYLE_TOKENS.frame.width;
  const footY = (preset.anchor[1] - 0.5) * STYLE_TOKENS.frame.height;
  const centerY = footY - (pose.footBaseline - 0.5) * height;

  return {
    pose: poseName,
    placement: presetName,
    asset: pose.asset,
    size: [width, height] as [number, number],
    position: [footX, centerY] as [number, number],
    mouthAnchor: pose.normalizedMouthAnchor as readonly [number, number],
  };
}

export function presenterMouthLayout(
  poseName: PresenterPose,
  size: readonly [number, number],
) {
  const anchor = PRESENTER_RIG.poses[poseName].normalizedMouthAnchor;
  const [width, height] = size;
  return {
    position: [
      (anchor[0] - 0.5) * width,
      (anchor[1] - 0.5) * height,
    ] as [number, number],
    closedSize: [width * 0.115, width * 0.072] as [number, number],
    openSize: [width * 0.124, width * 0.083] as [number, number],
  };
}
