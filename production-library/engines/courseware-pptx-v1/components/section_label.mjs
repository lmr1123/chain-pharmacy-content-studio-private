/** Section label with optional lime chevron. */
export async function sectionLabel(ctx, slide, pageId, section) {
  const {eid, shape, text, centerBox, C, TS, style} = ctx;
  if (!section) return;
  const conf = style.components?.section_label || {};
  if (conf.mode === 'blue-tab' || style.visual_grammar === 'product-blue-asymmetric-v1') {
    const cy = style.layout?.section_y_design ?? -330;
    shape(
      slide,
      'roundRect',
      centerBox(-570, cy, 680, 62),
      C.primaryDeep,
      C.primaryDeep,
      eid(pageId, 'section__tab'),
    );
    shape(
      slide,
      'roundRect',
      centerBox(-875, cy, 34, 34),
      C.coral,
      C.coral,
      eid(pageId, 'section__accent'),
    );
    text(slide, eid(pageId, 'section'), section, centerBox(-550, cy, 580, 50), {
      fontSize: TS.section,
      color: C.white,
      align: 'left',
    });
    return;
  }
  text(slide, eid(pageId, 'section_chevron'), '»', centerBox(-860, -360, 48, 48), {
    fontSize: TS.body24,
    color: C.lime,
  });
  text(slide, eid(pageId, 'section'), section, centerBox(-280, -360, 1040, 56), {
    fontSize: TS.section,
    color: C.brown,
    align: 'left',
  });
}
