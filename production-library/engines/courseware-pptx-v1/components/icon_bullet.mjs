/** Icon + bullet text row. */
export async function iconBullet(ctx, slide, pageId, items, opts = {}) {
  const {eid, imageFit, shape, text, centerBox, C, TS} = ctx;
  const list = items || [];
  const startY = opts.startY ?? -160;
  const stepY = opts.stepY ?? 110;
  const iconX = opts.iconX ?? -820;
  const textX = opts.textX ?? -420;
  const textW = opts.textW ?? 700;
  const iconSize = opts.iconSize ?? 64;
  const iconFile = opts.iconFile;
  const rolePrefix = opts.rolePrefix ?? 'benefit';

  for (let i = 0; i < list.length; i++) {
    const y = startY + i * stepY;
    const it = list[i];
    const textVal = typeof it === 'string' ? it : it.text || it.label || '';
    const file = (typeof it === 'object' && it.icon) || iconFile;
    const role = i === 0 ? 'icon_check' : `icon_check.${i + 1}`;
    if (file) {
      await imageFit(slide, eid(pageId, role), file, iconX, y, iconSize, iconSize, '✓');
    } else {
      const iconFill = opts.iconFill ?? C.red;
      shape(slide, 'ellipse', centerBox(iconX, y, iconSize, iconSize), iconFill, iconFill, eid(pageId, `${role}.bg`));
      text(slide, eid(pageId, role), '✓', centerBox(iconX, y, iconSize, iconSize), {
        fontSize: Math.round(iconSize * 0.52),
        color: opts.iconTextColor ?? C.white,
      });
    }
    text(slide, eid(pageId, `${rolePrefix}.${i + 1}`), textVal, centerBox(textX, y, textW, 72), {
      fontSize: opts.fontSize ?? TS.coverBenefit,
      color: opts.textColor ?? C.ink,
      align: 'left',
    });
  }
}
