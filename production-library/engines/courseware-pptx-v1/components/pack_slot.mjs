/** Authorized pack image or labeled placeholder. */
export async function packSlot(ctx, slide, pageId, role, assetKey, cx, cy, maxW, maxH, label) {
  const {eid, imageFit} = ctx;
  const placeholder = label ? `${label}\n待业务授权` : '待业务授权';
  return imageFit(
    slide,
    eid(pageId, role),
    assetKey,
    cx,
    cy,
    maxW,
    maxH,
    label || role,
    placeholder,
  );
}
