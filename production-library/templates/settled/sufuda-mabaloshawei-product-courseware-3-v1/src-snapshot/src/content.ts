import model from '../content-model.json';

export type ContentElement = {
  id: string;
  kind: string;
  text?: string;
  asset?: string;
  slot?: string;
  replace?: string;
};

export type ContentPage = {
  id: string;
  type: string;
  title?: string;
  chapter?: string;
  nav?: string[];
  active_nav?: number;
  elements: Record<string, ContentElement>;
};

export const contentModel = model as {
  project_id: string;
  template_id: string;
  style_pack_id: string;
  voice_pack_id: string;
  title: string;
  product: Record<string, string>;
  tokens: Record<string, string>;
  assets: Record<string, string>;
  pages: ContentPage[];
};

const pageIndex = new Map(contentModel.pages.map(page => [page.id, page]));

export function pageOf(pageId: string): ContentPage {
  const page = pageIndex.get(pageId);
  if (!page) throw new Error(`Unknown content page: ${pageId}`);
  return page;
}

/** Stable editable layer key. */
export function K(pageId: string, role: string): string {
  const el = pageOf(pageId).elements[role];
  if (!el) throw new Error(`Unknown element ${pageId}.${role}`);
  return el.id;
}

/** Theme-replaceable text. */
export function T(pageId: string, role: string): string {
  const el = pageOf(pageId).elements[role];
  if (!el) throw new Error(`Unknown element ${pageId}.${role}`);
  return el.text ?? '';
}

/** Asset path from content-model assets map. */
export function A(assetKey: string): string {
  const src = contentModel.assets[assetKey];
  if (!src) throw new Error(`Unknown asset key: ${assetKey}`);
  return src;
}

/** Design tokens（色值 + fs_* 字号），project.tsx 单源读取。 */
export function tokens(): Record<string, string> {
  return contentModel.tokens;
}

export function elementOf(pageId: string, role: string): ContentElement {
  const el = pageOf(pageId).elements[role];
  if (!el) throw new Error(`Unknown element ${pageId}.${role}`);
  return el;
}
