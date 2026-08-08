/**
 * Scene builders for gold content-model types.
 * Use components + ctx tokens only (no literal brand colors).
 * Geometry preserved from cw4 for regression fidelity.
 */
import {
  chromeBg,
  chapterTitle,
  sectionLabel,
  navPills,
  imageChain,
  packSlot,
  iconBullet,
  audienceCards,
  whiteStage,
  noteBar,
} from '../components/index.mjs';
import {fitFontSize} from '../layout-rules.mjs';

export async function buildCover(ctx, slide, sc) {
  const {shape, text, eid, centerBox, C, TS} = ctx;
  chromeBg(ctx, slide);
  shape(slide, 'ellipse', centerBox(0, 520, 2200, 420), C.hill, 'none', 'hill');
  shape(slide, 'ellipse', centerBox(-400, 480, 900, 280), 'rgba(190,190,190,0.5)', 'none', 'hill-l');

  // 品名标题：强制单行（培训课件商品名尽量不换行）
  // 策略：长名略降字号 → 按 CJK 光学宽加宽 pill → 单行高度，避免 textbox 自动折行
  const title = String(sc.title_pill || '').replace(/\s+/g, '');
  const charN = Math.max(1, [...title].length);
  const titleMaxW = 1680;
  const preferred =
    charN >= 14 ? Math.round(TS.coverTitle * 0.78) : charN >= 11 ? Math.round(TS.coverTitle * 0.88) : TS.coverTitle;
  const tFit = fitFontSize(title, {
    preferred,
    min: 22,
    boxW: titleMaxW - 80,
    maxLines: 1,
  });
  // PPT 实测 CJK 约 1.15–1.25em；取 1.28 留余量
  const opticalW = Math.ceil(tFit.fontSize * charN * 1.28);
  const pillW = Math.min(titleMaxW, Math.max(880, opticalW + 120));
  const pillH = Math.round(tFit.fontSize * 1.45 + 20); // 单行高，不给第二行空间
  shape(
    slide,
    'roundRect',
    centerBox(0, -420, pillW, pillH),
    C.titlePill,
    C.titlePill,
    eid(sc.id, 'title_pill__bar'),
  );
  text(slide, eid(sc.id, 'title_pill'), title, centerBox(0, -420, pillW - 48, pillH - 8), {
    fontSize: tFit.fontSize,
    color: C.white,
    vAlign: 'middle',
  });

  // placeholder label must not inject policy-forbidden copy (好物推荐)
  await ctx.imageFit(
    slide,
    eid(sc.id, 'badge_img'),
    'badge-hot-recommend.png',
    760,
    -400,
    200,
    200,
    '角标',
    '角标',
  );

  await iconBullet(ctx, slide, sc.id, sc.benefits || [], {
    startY: -160,
    stepY: 110,
    iconFile: 'icon-check-red.png',
  });

  await packSlot(ctx, slide, sc.id, 'pack_a', 'slot-pack-box-a.png', 280, 60, 280, 400, '盒装A');
  await packSlot(ctx, slide, sc.id, 'pack_b', 'slot-pack-box-b.png', 560, 60, 280, 400, '盒装B');
  await packSlot(ctx, slide, sc.id, 'pack_bottle', 'slot-pack-bottle.png', 820, 40, 260, 440, '瓶装');
}

export async function buildTimeList(ctx, slide, sc) {
  const {shape, text, imageFit, eid, centerBox, C, TS, FS} = ctx;
  chromeBg(ctx, slide);
  shape(slide, 'rect', centerBox(-560, 40, 400, 560), C.white, C.red, 'time-card');
  text(slide, eid(sc.id, 'time_label'), 'TIME', centerBox(-560, -140, 340, 90), {
    fontSize: TS.timeLabel,
    color: C.red,
  });
  text(slide, eid(sc.id, 'time_sub'), 'Big\nTitle', centerBox(-560, 80, 320, 160), {
    fontSize: TS.cardTitle + 6,
    color: C.red,
  });

  shape(slide, 'roundRect', centerBox(320, 40, 980, 520), C.dark, C.dark, 'list-card');
  await imageFit(slide, eid(sc.id, 'list_chevron'), 'icon-chevron-lime.png', -80, -140, 64, 64, '»');
  text(
    slide,
    eid(sc.id, 'card_title'),
    sc.card_title || '对人类健康贡献最大的10种健康食品',
    centerBox(360, -140, 780, 70),
    {fontSize: TS.cardTitle, color: C.lime, align: 'left'},
  );
  shape(slide, 'rect', centerBox(320, -70, 840, 3), C.lime, C.lime, 'list-div');

  const list = sc.list || ['1.番茄', '2.***', '3.***'];
  for (let i = 0; i < list.length; i++) {
    text(slide, eid(sc.id, `list.${i + 1}`), list[i], centerBox(280, 20 + i * 100, 800, 72), {
      fontSize: TS.listItem,
      color: C.white,
      align: 'left',
    });
  }
}

export async function buildBroll(ctx, slide, sc) {
  chromeBg(ctx, slide);
  whiteStage(ctx, slide, 'photo-stage', 0, 20, 1200, 820, {
    fill: 'rgba(255,255,255,0.55)',
  });
  await packSlot(ctx, slide, sc.id, 'photo', 'slot-photo-tomato.png', 0, 0, 1100, 780, '实拍槽位');
}

export async function buildProductIntro(ctx, slide, sc) {
  chromeBg(ctx, slide);
  await packSlot(ctx, slide, sc.id, 'vine', 'slot-photo-vine.png', -520, 20, 520, 640, '实拍槽位');
  await packSlot(ctx, slide, sc.id, 'pack_a', 'slot-pack-box-a.png', 80, 40, 300, 480, '盒装A');
  await packSlot(ctx, slide, sc.id, 'pack_b', 'slot-pack-box-b.png', 400, 40, 300, 480, '盒装B');
  await packSlot(ctx, slide, sc.id, 'pack_bottle', 'slot-pack-bottle.png', 720, 20, 300, 520, '瓶装');
}

export async function buildBenefitChain(ctx, slide, sc) {
  const {C, TS, centerBox, shape, text, eid} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '一、三大核心功效');
  await sectionLabel(ctx, slide, sc.id, sc.section || '');
  await imageChain(ctx, slide, sc.id, sc);
  const bodyHint = (sc.subtitles || []).slice(-1)[0]?.text;
  if (bodyHint) {
    noteBar(ctx, slide, sc.id, bodyHint, {
      cy: 420,
      w: 1600,
      h: 64,
      role: 'hint',
      fontSize: TS.body24,
      color: C.brown,
    });
  }
}

export async function buildOrigin(ctx, slide, sc) {
  const {text, eid, centerBox, C, TS, imageFit} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '二、产品特点');
  await sectionLabel(ctx, slide, sc.id, sc.section || '1、产地好');
  const mapCap = sc.map_caption || '';
  if (mapCap) {
    text(
      slide,
      eid(sc.id, 'map_caption'),
      mapCap,
      centerBox(0, -280, 1600, 48),
      {fontSize: TS.mapCap, color: C.muted},
    );
  }
  whiteStage(ctx, slide, 'map-stage', 0, 40, 780, 520);
  await imageFit(slide, eid(sc.id, 'map'), 'map-xinjiang.png', 0, 20, 720, 480, '新疆地图');
  const bodyHint =
    (sc.subtitles || []).map((s) => s.text).filter(Boolean).slice(-1)[0] || sc.body || '';
  if (bodyHint) {
    noteBar(ctx, slide, sc.id, bodyHint, {
      cy: 420,
      w: 1680,
      h: 72,
      role: 'body',
      fontSize: TS.body22,
      color: C.brown,
    });
  }
}

export async function buildMaterial(ctx, slide, sc) {
  const {C, TS} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '二、产品特点');
  await sectionLabel(ctx, slide, sc.id, sc.section || '2、原料优');
  whiteStage(ctx, slide, 'vine-stage', 0, 20, 960, 560);
  await packSlot(ctx, slide, sc.id, 'vine', 'slot-photo-vine.png', 0, 0, 900, 520, '原料实拍');
  const bodyHint =
    (sc.subtitles || []).map((s) => s.text).filter(Boolean).slice(-1)[0] || sc.body || '';
  if (bodyHint) {
    noteBar(ctx, slide, sc.id, bodyHint, {
      cy: 420,
      w: 1680,
      h: 72,
      role: 'body',
      fontSize: TS.body22,
      color: C.brown,
    });
  }
}

export async function buildContent(ctx, slide, sc) {
  const {text, eid, centerBox, C, TS, imageFit} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '二、产品特点');
  await sectionLabel(ctx, slide, sc.id, sc.section || '3、含量高');
  whiteStage(ctx, slide, 'eq-stage', 0, 40, 1600, 520, {
    fill: 'rgba(255,255,255,0.72)',
  });
  await imageFit(slide, eid(sc.id, 'softgel'), 'softgel.png', -420, 20, 300, 300, '软胶囊');
  text(slide, eid(sc.id, 'eq'), '=', centerBox(0, 0, 160, 160), {
    fontSize: TS.heroEq,
    color: C.gold,
  });
  await imageFit(slide, eid(sc.id, 'five_tomatoes'), 'five-tomatoes.png', 420, 20, 480, 360, '五个番茄');
  // Prefer script-provided body/subtitle; never invent default marketing line
  const hint =
    (sc.subtitles || []).map((s) => s.text).filter(Boolean).slice(-1)[0] ||
    sc.body ||
    sc.eq_caption ||
    '';
  if (hint) {
    text(slide, eid(sc.id, 'eq_caption'), hint, centerBox(0, 360, 1600, 64), {
      fontSize: TS.body24,
      color: C.brown,
    });
  }
}

export async function buildAudience(ctx, slide, sc) {
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '三、适宜人群');
  await audienceCards(ctx, slide, sc.id, sc.items || []);
}

export async function buildEfficacyTable(ctx, slide, sc) {
  const {shape, text, imageFit, eid, centerBox, C, TS, FS} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '五、福尔番茄红素三大核心功效');
  const rows = sc.rows || [];
  const tableW = 1600;
  const tableH = 720;
  const topY = 40;
  shape(slide, 'roundRect', centerBox(0, topY, tableW, tableH), C.card || C.silkLight, C.tableBorder, 'eff-table');

  const fh = tableH / Math.max(rows.length, 1);
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const y = topY - tableH / 2 + fh * (i + 0.5);
    if (i > 0) {
      shape(
        slide,
        'rect',
        centerBox(0, y - fh / 2, tableW - 8, 2),
        C.tableBorder,
        C.tableBorder,
        `eff-div-${i}`,
      );
    }
    shape(slide, 'rect', centerBox(-400, y, 2, fh - 8), C.tableBorder, C.tableBorder, `eff-vdiv-${i}`);
    await imageFit(
      slide,
      eid(sc.id, `row.${i + 1}.chevron`),
      'icon-chevron-lime.png',
      -720,
      y,
      44,
      44,
      '»',
    );
    text(slide, eid(sc.id, `row.${i + 1}.label`), row.label, centerBox(-560, y, 300, fh - 24), {
      fontSize: TS.rowLabel + 4,
      color: C.brown,
      align: 'left',
    });
    text(slide, eid(sc.id, `row.${i + 1}.body`), row.body, centerBox(200, y, 1100, fh - 24), {
      fontSize: TS.body24,
      color: C.brown,
      align: 'left',
      bold: false,
    });
  }

  if (sc.side_left || sc.side_right) {
    shape(slide, 'roundRect', centerBox(0, 460, 1600, 56), 'rgba(106,58,48,0.08)', 'none', 'side-strip');
    const side = [sc.side_left, sc.side_right].filter(Boolean).join('　|　');
    text(slide, eid(sc.id, 'side_combined'), side, centerBox(0, 460, 1540, 48), {
      fontSize: TS.body18,
      color: C.muted,
      bold: false,
    });
  }
}

export async function buildRelatedMeds(ctx, slide, sc) {
  const {shape, text, eid, centerBox, C, TS} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '四、关联用药');

  const nav = sc.nav || ['组合1', '组合2'];
  const active = sc.active_nav ?? 0;
  navPills(ctx, slide, sc.id, nav, active);

  text(slide, eid(sc.id, 'note'), sc.note || '', centerBox(0, -240, 1600, 70), {
    fontSize: TS.body32,
    color: C.ink,
  });

  whiteStage(ctx, slide, 'related-stage', 0, 100, 1600, 560);
  shape(slide, 'roundRect', centerBox(-360, 40, 420, 360), C.silkLight, C.cardBorder, 'pack-l-card');
  shape(slide, 'roundRect', centerBox(360, 40, 420, 360), C.silkLight, C.cardBorder, 'pack-r-card');

  await packSlot(
    ctx,
    slide,
    sc.id,
    'pack_left',
    sc.left_pack || 'slot-pack-lycopene.png',
    -360,
    0,
    320,
    320,
    sc.left_label || '本品',
  );
  text(slide, eid(sc.id, 'plus'), '+', centerBox(0, 20, 100, 100), {
    fontSize: TS.plus,
    color: C.red,
  });
  await packSlot(
    ctx,
    slide,
    sc.id,
    'pack_right',
    sc.right_pack || 'slot-pack-zinc.png',
    360,
    0,
    300,
    300,
    sc.right_label || '关联品',
  );
  text(slide, eid(sc.id, 'left_label'), sc.left_label || '', centerBox(-360, 250, 400, 48), {
    fontSize: TS.body26,
    color: C.brown,
  });
  text(slide, eid(sc.id, 'right_label'), sc.right_label || '', centerBox(360, 250, 400, 48), {
    fontSize: TS.body26,
    color: C.brown,
  });
}

export async function buildSummaryRows(ctx, slide, sc) {
  const {shape, text, eid, centerBox, C, TS, FS} = ctx;
  chromeBg(ctx, slide);
  shape(slide, 'ellipse', centerBox(-820, -460, 28, 28), C.red, C.red, 'eyebrow-dot');
  text(slide, eid(sc.id, 'eyebrow'), sc.eyebrow || '敲重点', centerBox(-640, -460, 280, 48), {
    fontSize: TS.eyebrow,
    color: C.red,
    align: 'left',
  });
  shape(slide, 'roundRect', centerBox(0, -460, 280, 72), C.red, C.red, eid(sc.id, 'chapter__pill'));
  text(slide, eid(sc.id, 'chapter'), sc.chapter || '总结', centerBox(0, -460, 250, 64), {
    fontSize: TS.coverBenefit,
    color: C.white,
  });

  const cols = sc.columns || [];
  const n = Math.max(cols.length, 1);
  const tableW = 1760;
  const tableH = 720;
  const topY = 20;
  shape(slide, 'roundRect', centerBox(0, topY, tableW, tableH), C.card || C.silkLight, C.cardBorder, 'sum-table');

  const rowH = tableH / n;
  for (let i = 0; i < cols.length; i++) {
    const col = cols[i];
    const y = topY - tableH / 2 + rowH * (i + 0.5);
    if (i > 0) {
      shape(
        slide,
        'rect',
        centerBox(0, y - rowH / 2, tableW - 4, 2),
        C.cardBorder,
        C.cardBorder,
        `sum-div-${i}`,
      );
    }
    shape(
      slide,
      'rect',
      centerBox(-tableW / 2 + 120, y, 240, rowH - 2),
      C.red,
      C.red,
      eid(sc.id, `row.${i + 1}.label__bar`),
    );
    text(
      slide,
      eid(sc.id, `row.${i + 1}.label`),
      col.header,
      centerBox(-tableW / 2 + 120, y, 220, rowH - 16),
      {fontSize: TS.rowLabel, color: C.white},
    );
    const body = (col.items || []).join('\n');
    text(slide, eid(sc.id, `row.${i + 1}.body`), body, centerBox(140, y, 1400, rowH - 20), {
      fontSize: TS.rowBody,
      color: C.ink,
      align: 'left',
      bold: false,
      vAlign: 'middle',
    });
  }

  if (sc.footer) {
    text(slide, eid(sc.id, 'footer'), sc.footer, centerBox(0, 470, 1700, 44), {
      fontSize: TS.footer,
      color: C.ink,
    });
  }
}

/** Candidate: chips + data_stat; optional theme icons per symptom. */
export async function buildHookPainData(ctx, slide, sc) {
  const {text, eid, centerBox, C, TS, imageFit, shape} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || sc.title || '痛点数据');
  if (sc.section) await sectionLabel(ctx, slide, sc.id, sc.section);

  const chips = sc.symptoms || sc.chips || [];
  const chipIcons = sc.symptom_icons || sc.chip_icons || [];
  const nChip = chips.length;
  const chipW = 220;
  const chipH = chipIcons.length ? 200 : 56;
  const chipGap = 28;
  const chipSpan = nChip > 0 ? nChip * chipW + (nChip - 1) * chipGap : 0;
  const chipY = chipIcons.length ? -180 : -200;
  for (let i = 0; i < nChip; i++) {
    const x = -chipSpan / 2 + chipW / 2 + i * (chipW + chipGap);
    whiteStage(ctx, slide, `chip-${i}`, x, chipY, chipW, chipH);
    if (chipIcons[i]) {
      await imageFit(
        slide,
        eid(sc.id, `chip_icon.${i + 1}`),
        chipIcons[i].file || chipIcons[i],
        x,
        chipY - 28,
        110,
        110,
        chips[i],
      );
      const cFit = fitFontSize(chips[i], {
        preferred: TS.body20,
        min: TS.minimum,
        boxW: chipW - 24,
        maxLines: 2,
      });
      text(slide, eid(sc.id, `chip.${i + 1}`), chips[i], centerBox(x, chipY + 64, chipW - 24, 48), {
        fontSize: cFit.fontSize,
        color: C.ink,
        bold: false,
      });
    } else {
      const cFit = fitFontSize(chips[i], {
        preferred: TS.body22,
        min: TS.minimum,
        boxW: chipW - 24,
        maxLines: 1,
      });
      text(slide, eid(sc.id, `chip.${i + 1}`), chips[i], centerBox(x, chipY, chipW - 24, 48), {
        fontSize: cFit.fontSize,
        color: C.ink,
      });
    }
  }

  const stats = sc.stats || [];
  const n = Math.max(stats.length, 1);
  const span = 1400;
  const gap = 36;
  const cardW = Math.min(440, (span - gap * (n - 1)) / n);
  const cardH = 300;
  const statsY = chipIcons.length ? 160 : 100;
  const x0 = -((cardW * n + gap * (n - 1)) / 2) + cardW / 2;
  const {dataStat} = await import('../components/data_stat.mjs');
  for (let i = 0; i < stats.length; i++) {
    dataStat(ctx, slide, sc.id, {...stats[i], role: `stat${i + 1}`}, {
      cx: x0 + i * (cardW + gap),
      cy: statsY,
      w: cardW,
      h: cardH,
    });
  }
  if (sc.source) {
    const sFit = fitFontSize(sc.source, {
      preferred: TS.caption,
      min: TS.minimum,
      boxW: 1600,
      maxLines: 2,
    });
    noteBar(ctx, slide, sc.id, sc.source, {
      cy: 420,
      w: 1680,
      h: 52,
      role: 'source',
      fontSize: sFit.fontSize,
      color: C.muted,
      bold: false,
    });
  }
}

/**
 * Candidate: full-width ≤3 rows.
 * Columns (shared left edge for partner + talk): scenario | content | theme icon.
 * Layout: fill between section (~-360) and bottom margin (~480) — less vertical empty.
 */
export async function buildCombinationGuidance(ctx, slide, sc) {
  const {shape, text, eid, centerBox, C, TS, imageFit} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '联合用药指导');
  if (sc.section) await sectionLabel(ctx, slide, sc.id, sc.section);

  const raw = (sc.rows || sc.items || []).slice(0, 3);
  const n = Math.max(raw.length, 1);
  const tableW = 1760;
  // section at -360 → content top -280; bottom margin ~500 → tall content band
  const contentTop = sc.section ? -280 : -300;
  const contentBottom = 500;
  const tableH = contentBottom - contentTop;
  const topY = (contentTop + contentBottom) / 2;
  const rowH = tableH / n;
  const pad = 32;
  // 列：问题场景(短·单行) | 搭配药品+解说 | 组合图
  const scenarioW = 300;
  const iconW = 168;
  const gap = 28;
  // content column: partner title + talk — same left edge
  const contentLeft = -tableW / 2 + pad + scenarioW + gap;
  const contentW = tableW - pad * 2 - scenarioW - gap - iconW - gap;
  const contentCx = contentLeft + contentW / 2;
  const scenarioCx = -tableW / 2 + pad + scenarioW / 2;
  const iconCx = tableW / 2 - pad - iconW / 2;

  shape(slide, 'roundRect', centerBox(0, topY, tableW, tableH), C.card || C.silkLight, C.cardBorder, 'combo-table');

  for (let i = 0; i < raw.length; i++) {
    const r = raw[i];
    const y = topY - tableH / 2 + rowH * (i + 0.5);
    if (i > 0) {
      shape(
        slide,
        'rect',
        centerBox(0, y - rowH / 2, tableW - 16, 2),
        C.cardBorder,
        C.cardBorder,
        `combo-div-${i}`,
      );
    }

    // 优先 problem 短标题（如「改善排尿困难」），≤8 字强制单行
    const scen = r.problem || r.scenario || r.scene || r.label || '';
    const scenN = [...String(scen)].length;
    const sFit = fitFontSize(scen, {
      preferred: scenN <= 8 ? (TS.rowLabel || TS.body26) : TS.body22,
      min: 14,
      boxW: scenarioW - 36,
      maxLines: 1,
    });
    const pillH = Math.min(rowH - 28, Math.max(64, Math.round(sFit.fontSize * 1.5 + 24)));
    shape(
      slide,
      'roundRect',
      centerBox(scenarioCx, y, scenarioW, pillH),
      C.red,
      C.red,
      eid(sc.id, `row.${i + 1}.scenario__bar`),
    );
    text(slide, eid(sc.id, `row.${i + 1}.scenario`), scen, centerBox(scenarioCx, y, scenarioW - 28, pillH - 10), {
      fontSize: sFit.fontSize,
      color: C.white,
      vAlign: 'middle',
    });

    // partner + talk: compact stack, optical center = row mid (align with pill/icon)
    const partner = r.partner || r.product || '';
    const talk = r.talk_track || r.script || r.body || '';
    const partnerH = 52;
    const talkGap = 8;
    const talkH = 80;
    const stackH = partnerH + talkGap + talkH;
    const partnerCy = y - stackH / 2 + partnerH / 2;
    const talkCy = y + stackH / 2 - talkH / 2;

    const pFit = fitFontSize(partner, {
      preferred: TS.body32 || TS.body28,
      min: TS.body24 || 18,
      boxW: contentW,
      maxLines: 1,
    });
    text(slide, eid(sc.id, `row.${i + 1}.partner`), partner, centerBox(contentCx, partnerCy, contentW, partnerH), {
      fontSize: pFit.fontSize,
      color: C.brown,
      align: 'left',
      vAlign: 'middle',
    });

    const tFit = fitFontSize(talk, {
      preferred: TS.body26,
      min: TS.body22 || TS.minimum,
      boxW: contentW,
      maxLines: 2,
    });
    text(slide, eid(sc.id, `row.${i + 1}.talk`), talk, centerBox(contentCx, talkCy, contentW, talkH), {
      fontSize: tFit.fontSize,
      color: C.ink,
      align: 'left',
      bold: false,
      vAlign: 'middle',
    });

    const iconSize = Math.min(iconW - 8, rowH - 48, 150);
    const iconFile = r.icon || r.pack || r.partner_pack;
    if (iconFile) {
      await imageFit(
        slide,
        eid(sc.id, `row.${i + 1}.icon`),
        iconFile,
        iconCx,
        y,
        iconSize,
        iconSize,
        r.partner || r.scenario || '主题图',
      );
    } else {
      shape(
        slide,
        'roundRect',
        centerBox(iconCx, y, iconSize, iconSize),
        C.silkLight || C.card,
        C.cardBorder,
        eid(sc.id, `row.${i + 1}.icon__ph`),
      );
      text(slide, eid(sc.id, `row.${i + 1}.icon.label`), '可替换', centerBox(iconCx, y, iconSize - 12, 36), {
        fontSize: TS.caption,
        color: C.muted,
        bold: false,
      });
    }
  }
}

/**
 * Candidate: left numbered list + right 2×2 illustrations.
 * Fill under chapter (~-460) down to bottom margin — larger panels.
 */
export async function buildPrecautions(ctx, slide, sc) {
  const {shape, text, eid, centerBox, C, TS, imageFit} = ctx;
  chromeBg(ctx, slide);
  chapterTitle(ctx, slide, sc.id, sc.chapter || '注意事项');
  if (sc.section) await sectionLabel(ctx, slide, sc.id, sc.section);

  const items = sc.items || sc.list || [];
  // 左右等高大卡：上贴标题下近底，列表在左卡内紧凑居中
  const contentTop = sc.section ? -280 : -300;
  const contentBottom = 500;
  const panelH = contentBottom - contentTop;
  const panelCy = (contentTop + contentBottom) / 2;

  const nItem = Math.max(items.length, 1);
  const step = 96;
  const innerPadX = 40;
  const listW = 920;
  const listH = panelH;
  const listCx = -420;
  const listCy = panelCy;
  const listLeft = listCx - listW / 2;
  const numSize = 48;
  const numX = listLeft + innerPadX + numSize / 2;
  const textLeft = listLeft + innerPadX + numSize + 24;
  const textW = listW - innerPadX * 2 - numSize - 24;
  const textCx = textLeft + textW / 2;

  whiteStage(ctx, slide, 'pre-list-stage', listCx, listCy, listW, listH);

  const blockH = step * nItem;
  const startY = listCy - blockH / 2 + step / 2;

  for (let i = 0; i < items.length; i++) {
    const y = startY + i * step;
    const label = typeof items[i] === 'string' ? items[i] : items[i].text || '';
    shape(
      slide,
      'ellipse',
      centerBox(numX, y, numSize, numSize),
      C.red,
      C.red,
      eid(sc.id, `num.${i + 1}__dot`),
    );
    text(slide, eid(sc.id, `num.${i + 1}`), String(i + 1), centerBox(numX, y, numSize - 4, numSize - 4), {
      fontSize: TS.body26,
      color: C.white,
      vAlign: 'middle',
    });
    const iFit = fitFontSize(label, {
      preferred: TS.body32,
      min: TS.body24,
      boxW: textW,
      maxLines: 2,
    });
    text(slide, eid(sc.id, `item.${i + 1}`), label, centerBox(textCx, y, textW, step - 16), {
      fontSize: iFit.fontSize,
      color: C.ink,
      align: 'left',
      bold: false,
      vAlign: 'middle',
    });
  }

  // right 2×2 — same height as left
  const illos = sc.illustrations || sc.images || [];
  const defaultLabels = ['不代替药物', '禁忌人群', '随餐服用', '就医咨询'];
  const gridW = 680;
  const gridH = panelH;
  const gridCx = 500;
  const gridCy = panelCy;
  const cellGap = 22;
  const cellPad = 24;
  const cell = (Math.min(gridW, gridH) - cellGap - cellPad * 2) / 2;

  whiteStage(ctx, slide, 'pre-illo-stage', gridCx, gridCy, gridW, gridH, {
    fill: C.cardSoft || C.silkLight,
  });

  for (let i = 0; i < 4; i++) {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = gridCx - (cell + cellGap) / 2 + col * (cell + cellGap);
    const y = gridCy - (cell + cellGap) / 2 + row * (cell + cellGap);
    const illo = illos[i];
    const label = (illo && (illo.label || illo.caption)) || defaultLabels[i];
    shape(
      slide,
      'roundRect',
      centerBox(x, y, cell, cell),
      C.card || C.silkLight,
      C.cardBorder,
      eid(sc.id, `illo.${i + 1}__cell`),
    );
    if (illo && (illo.file || typeof illo === 'string')) {
      await imageFit(
        slide,
        eid(sc.id, `illo.${i + 1}`),
        illo.file || illo,
        x,
        y - 14,
        cell - 40,
        cell - 64,
        label,
      );
      const lFit = fitFontSize(label, {
        preferred: TS.body18,
        min: TS.minimum,
        boxW: cell - 28,
        maxLines: 1,
      });
      text(slide, eid(sc.id, `illo.${i + 1}.caption`), label, centerBox(x, y + cell / 2 - 24, cell - 28, 32), {
        fontSize: lFit.fontSize,
        color: C.brown,
        bold: false,
      });
    } else {
      text(slide, eid(sc.id, `illo.${i + 1}.label`), label, centerBox(x, y, cell - 32, 48), {
        fontSize: TS.body18,
        color: C.muted,
        bold: false,
      });
    }
  }
}

export const builders = {
  cover: buildCover,
  time_list: buildTimeList,
  broll: buildBroll,
  product_intro: buildProductIntro,
  benefit_chain: buildBenefitChain,
  feature_origin: buildOrigin,
  feature_material: buildMaterial,
  feature_content: buildContent,
  audience: buildAudience,
  efficacy_recap_table: buildEfficacyTable,
  related_meds: buildRelatedMeds,
  summary_4col: buildSummaryRows,
  // candidate page types (M3/M5)
  hook_pain_data: buildHookPainData,
  combination_guidance: buildCombinationGuidance,
  precautions: buildPrecautions,
};

export function notes(ctx, slide, scene) {
  const {modelPath, repoRoot, font, pathRelative} = ctx;
  const rel =
    pathRelative && modelPath
      ? pathRelative(repoRoot, modelPath)
      : modelPath || 'content-model.json';
  slide.speakerNotes.textFrame.setText(
    [
      `[Sources]`,
      `- content-model: ${rel}`,
      `- scene: ${scene.id} (${scene.type || '?'})`,
      `- layer: ${scene.layer || 'observed_reference'}`,
      `- font: ${font}`,
      `- engine: courseware-pptx-v1`,
      `- 图片按原比例装箱；包装/Logo 为业务授权槽位。`,
      scene.note ? `- note: ${scene.note}` : null,
    ]
      .filter(Boolean)
      .join('\n'),
  );
  slide.speakerNotes.setVisible(false);
}
