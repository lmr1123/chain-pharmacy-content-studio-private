import manifest from './data/wind-heat-audio-v2.json';

export type UnifiedAudioSceneId = keyof typeof manifest.scenes;
export type UnifiedAudioCue = {
  start: number;
  end: number;
  text: string;
};

export function unifiedAudio(id: UnifiedAudioSceneId) {
  const scene = manifest.scenes[id];
  return {
    ...scene,
    cues: scene.cues as UnifiedAudioCue[],
  };
}

export const WIND_HEAT_AUDIO_V2 = manifest;
