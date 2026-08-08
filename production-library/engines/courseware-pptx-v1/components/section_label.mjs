/** Section label with optional lime chevron. */
export async function sectionLabel(ctx, slide, pageId, section) {
  const {eid, text, imageFit, centerBox, C, TS} = ctx;
  if (!section) return;
  await imageFit(
    slide,
    eid(pageId, 'section_chevron'),
    'icon-chevron-lime.png',
    -860,
    -360,
    48,
    48,
    '»',
  );
  text(slide, eid(pageId, 'section'), section, centerBox(-280, -360, 1040, 56), {
    fontSize: TS.section,
    color: C.brown,
    align: 'left',
  });
}
