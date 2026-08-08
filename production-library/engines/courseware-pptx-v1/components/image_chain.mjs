import {imageChainLayout, resolveChainItems} from '../layout-rules.mjs';

/**
 * Image chain.
 * Prefer fixed design coords (x/y on items) for gold regression;
 * otherwise auto-center via layout-rules.
 */
export async function imageChain(ctx, slide, pageId, sceneOrItems, opts = {}) {
  const {eid, imageFit} = ctx;
  const items = Array.isArray(sceneOrItems)
    ? sceneOrItems
    : resolveChainItems(sceneOrItems || {});

  const hasFixed = items.some((it) => it.x != null);
  const laid = hasFixed
    ? items.map((it, i) => ({
        ...it,
        cx: it.x,
        cy: it.y ?? opts.y ?? 80,
        size: it.size ?? opts.defaultSize ?? 280,
        index: i,
      }))
    : imageChainLayout(items, opts);

  for (const it of laid) {
    await imageFit(
      slide,
      eid(pageId, it.role),
      it.file || it.asset,
      it.cx,
      it.cy,
      it.size,
      it.size,
      it.role,
    );
  }
  return laid;
}
