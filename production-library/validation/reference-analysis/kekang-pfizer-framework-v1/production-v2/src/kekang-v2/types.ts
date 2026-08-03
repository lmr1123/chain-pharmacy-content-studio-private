export type Microshot = {
  id: string;
  chapter_id: string;
  sequence_in_chapter: number;
  timeline_order: number;
  duration_seconds: number;
  narration_candidate: string;
  subtitle: string;
  recipe_id: string;
  frame_mode: string;
  focal_subject: string;
  visual_action: string;
  asset_ids: string[];
  layers: string[];
  animated_nontext_layers: string[];
  entry: string;
  performance: string;
  exit: string;
  camera_motion: string;
  static_hold_max_seconds: number;
  sfx_events: string[];
  content_approval: string;
  voice_render_policy: string;
  production_ready: boolean;
  transition_to: string;
};

export type SharedVisualState = {
  accent: string;
  heroX: number;
  heroY: number;
  heroScale: number;
  pathProgress: number;
};
