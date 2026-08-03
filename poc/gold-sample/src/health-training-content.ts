/**
 * Content-driven helpers for disease health-training (风热金样) video projects.
 * Prefer fields from segment JSON (`disease_name`, `screen`, `audio`, `cues`)
 * so theme replication can replace text/media without editing TSX.
 */

export type HealthScreenContent = {
  disease_name?: string;
  eyebrow?: string;
  tagline?: string;
  chapter_intro?: string;
  chapter_character?: string;
  chapter_mechanism?: string;
  chapter_symptoms?: string;
  chapter_treatment?: string;
  chapter_medication?: string;
  chapter_summary?: string;
  character_cards?: string[];
  mechanism_title?: string;
  equation_left?: string;
  equation_right?: string;
  equation_result?: string;
  symptoms_title?: string;
  core_heading?: string;
  core_treatment?: string;
  core_body_1?: string;
  core_body_2?: string;
  core_body_3?: string;
  treatment_principle?: string;
  treatment_line_1?: string;
  treatment_line_2?: string;
  recipe_text?: string;
  recipe_effect?: string;
  herbs?: Array<{name: string; image: string; lines: [string, string] | string[]}>;
  symptom_groups?: Array<{
    number: string;
    title: string;
    summaryLines: [string, string] | string[];
    items: Array<{image: string; label: string}>;
  }>;
  medication_names?: string[];
  advice_items?: Array<{
    title: string;
    body: string;
    image: string;
    transparent?: boolean;
  }>;
  summary_items?: Array<{title: string; body: string}>;
  advice_title?: string;
  summary_title?: string;
  slogan?: string;
};

export type HealthSegmentData = {
  disease_name?: string;
  theme?: string;
  title?: string;
  playback_duration?: number;
  audio?: {file?: string; source?: string};
  cues?: Array<{start: number; end: number; text: string}>;
  screen?: HealthScreenContent;
  outro_start_ratio?: number;
};

export function diseaseName(data: HealthSegmentData): string {
  return (
    data.disease_name ||
    data.screen?.disease_name ||
    data.theme ||
    data.title ||
    '风热证'
  );
}

export function screenOf(data: HealthSegmentData): HealthScreenContent {
  return data.screen || {};
}

export function playbackDuration(
  data: HealthSegmentData,
  fallback: number,
): number {
  const d = Number(data.playback_duration);
  return Number.isFinite(d) && d > 0.5 ? d : fallback;
}

export function audioFile(
  data: HealthSegmentData,
  fallback: string,
): string {
  return data.audio?.file || fallback;
}

export function cuesOf(
  data: HealthSegmentData,
  fallback: Array<{start: number; end: number; text: string}> = [],
) {
  return (data.cues && data.cues.length > 0 ? data.cues : fallback) as Array<{
    start: number;
    end: number;
    text: string;
  }>;
}
