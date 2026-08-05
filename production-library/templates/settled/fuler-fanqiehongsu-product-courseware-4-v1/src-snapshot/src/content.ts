/**
 * Content accessors for product-courseware-4 editable video.
 * IDs: editable:cw4:{page_id}:{role}  (from layer-manifest.json)
 */
import model from '../content-model.json';
import manifest from '../layer-manifest.json';

export type Scene = {
  id: string;
  start: number;
  end: number;
  /** false = 片段工作室中删除/隐藏，不进时间线 */
  enabled?: boolean;
  type?: string;
  layer?: string;
  narration?: string;
  title_pill?: string;
  badge?: string;
  benefits?: string[];
  chapter?: string;
  section?: string;
  card_title?: string;
  list?: string[];
  map_caption?: string;
  note?: string;
  nav?: string[];
  active_nav?: number;
  left_label?: string;
  right_label?: string;
  left_pack?: string;
  right_pack?: string;
  side_left?: string;
  side_right?: string;
  eyebrow?: string;
  footer?: string;
  rows?: {label: string; body: string}[];
  columns?: {header: string; items: string[]}[];
  items?: {label: string; icon?: string}[];
  subtitles?: {t: number; text: string}[];
};

export const contentModel = model as {
  project_id: string;
  scenes: Scene[];
  assets?: Record<string, string>;
};

export const layerManifest = manifest as {
  layer_count: number;
  layers: {
    element_id: string;
    page_id: string;
    role: string;
    kind: string;
    default_text?: string | null;
    asset_key?: string | null;
    slot?: string | null;
  }[];
};

const layerByPageRole = new Map<string, (typeof layerManifest.layers)[0]>();
for (const layer of layerManifest.layers) {
  layerByPageRole.set(`${layer.page_id}::${layer.role}`, layer);
}

export function scenes(): Scene[] {
  return contentModel.scenes.filter(s => s.enabled !== false);
}

export function totalDuration(): number {
  const list = contentModel.scenes;
  if (!list.length) return 0;
  return Number(list[list.length - 1].end);
}

/** Stable editable layer key → must match wind-heat-editable-plugin prefix `editable:`. */
export function K(pageId: string, role: string): string {
  const hit = layerByPageRole.get(`${pageId}::${role}`);
  if (hit) return hit.element_id;
  return `editable:cw4:${pageId}:${role}`;
}

export function T(pageId: string, role: string, fallback = ''): string {
  const scene = contentModel.scenes.find(s => s.id === pageId);
  if (!scene) return fallback;

  if (role === 'title_pill') return scene.title_pill ?? fallback;
  if (role === 'badge') return scene.badge ?? fallback;
  if (role === 'chapter') return scene.chapter ?? fallback;
  if (role === 'section') return scene.section ?? fallback;
  if (role === 'card_title') return scene.card_title ?? fallback;
  if (role === 'map_caption') return scene.map_caption ?? fallback;
  if (role === 'note') return scene.note ?? fallback;
  if (role === 'left_label') return scene.left_label ?? fallback;
  if (role === 'right_label') return scene.right_label ?? fallback;
  if (role === 'side_left') return scene.side_left ?? fallback;
  if (role === 'side_right') return scene.side_right ?? fallback;
  if (role === 'eyebrow') return scene.eyebrow ?? fallback;
  if (role === 'footer') return scene.footer ?? fallback;

  const benefit = role.match(/^benefit\.(\d+)$/);
  if (benefit) {
    const i = Number(benefit[1]) - 1;
    return scene.benefits?.[i] ?? fallback;
  }
  const list = role.match(/^list\.(\d+)$/);
  if (list) {
    const i = Number(list[1]) - 1;
    return scene.list?.[i] ?? fallback;
  }
  const nav = role.match(/^nav\.(\d+)$/);
  if (nav) {
    const i = Number(nav[1]) - 1;
    return scene.nav?.[i] ?? fallback;
  }
  const rowLabel = role.match(/^row\.(\d+)\.label$/);
  if (rowLabel) {
    const i = Number(rowLabel[1]) - 1;
    if (scene.rows?.[i]) return scene.rows[i].label;
    if (scene.columns?.[i]) return scene.columns[i].header;
    return fallback;
  }
  const rowBody = role.match(/^row\.(\d+)\.body$/);
  if (rowBody) {
    const i = Number(rowBody[1]) - 1;
    if (scene.rows?.[i]) return scene.rows[i].body;
    if (scene.columns?.[i]) return (scene.columns[i].items || []).join('\n');
    return fallback;
  }
  const aud = role.match(/^label\.(\d+)$/);
  if (aud) {
    const i = Number(aud[1]) - 1;
    return scene.items?.[i]?.label ?? fallback;
  }

  const hit = layerByPageRole.get(`${pageId}::${role}`);
  return hit?.default_text ?? fallback;
}

/** Public URL path for stills / assets under Vite publicDir. */
export function stillSrc(pageId: string): string {
  return `/stills/${pageId}.png`;
}

export function assetSrc(filename: string): string {
  return `/assets/${filename}`;
}
