/** Icon + bullet text row. */
export async function iconBullet(ctx, slide, pageId, items, opts = {}) {
  const {eid, imageFit, text, centerBox, C, TS} = ctx;
  const list = items || [];
  const startY = opts.startY ?? -160;
  const stepY = opts.stepY ?? 110;
  const iconX = opts.iconX ?? -820;
  const textX = opts.textX ?? -420;
  const iconSize = opts.iconSize ?? 64;
  const iconFile = opts.iconFile ?? 'icon-check-red.png';

  for (let i = 0; i < list.length; i++) {
    const y = startY + i * stepY;
    const it = list[i];
    const textVal = typeof it === 'string' ? it : it.text || it.label || '';
    const file = (typeof it === 'object' && it.icon) || iconFile;
    const role = i === 0 ? 'icon_check' : `icon_check.${i + 1}`;
    await imageFit(slide, eid(pageId, role), file, iconX, y, iconSize, iconSize, '✓');
    text(slide, eid(pageId, `benefit.${i + 1}`), textVal, centerBox(textX, y, 700, 72), {
      fontSize: opts.fontSize ?? TS.coverBenefit,
      color: C.ink,
      align: 'left',
    });
  }
}
