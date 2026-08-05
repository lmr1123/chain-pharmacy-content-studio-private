/**
 * film 工程入口：15 页全量视觉 Revideo 原生渲染。
 * - mode 'film'      权威成片（动效 + 字幕；旁白由 render-film.ts 后合）
 * - mode 'editor-bg' 编辑器底板（只留 chrome 层，入场元素直置终态，每页 0.12s）
 * 文案/时码经 ../content 单源；坐标经 ../layout 单源。
 */
import {Node, makeScene2D} from '@revideo/2d';
import {all, fadeTransition, makeProject, waitFor} from '@revideo/core';

import {scenes as contentScenes, type Scene} from '../content';
import {
  CaptionLayer,
  captionSegments,
  captionText,
  playCaptions,
} from '../motion/captions';
import {SILK} from '../motion/primitives';
import {playFilmMotion} from './motion';
import {FilmPage} from './pages';
import {pageRootKey, type FilmMode} from './parts';

/** editor-bg 每页帧数（revideo floor(duration*fps) 有浮点损耗，+1e-4 保证整帧；render-stills 按它对齐抽帧） */
export const EDITOR_BG_PAGE_FRAMES = 4;

/** 页间默认硬切（对齐参考片）；仅这两页入场允许 0.24s 交叉淡（计划锁定） */
const XFADE_IN = new Set(['S01_time_list', 'S15_end']);

function makeFilmScene(sc: Scene, mode: FilmMode) {
  const full = Math.max(0.1, Number(sc.end) - Number(sc.start));
  const dur = mode === 'editor-bg' ? EDITOR_BG_PAGE_FRAMES / 30 + 1e-4 : full;
  const firstCap = captionSegments(sc)[0]?.text || captionText(sc);
  return makeScene2D(sc.id, function* (view) {
    view.fill(SILK);
    // 页根节点：S15 末 0.5s 整页（含字幕）淡到丝绸底色
    view.add(
      <Node key={pageRootKey(sc.id)}>
        <FilmPage sc={sc} mode={mode} />
        {mode === 'film' && (
          <CaptionLayer page={sc.id} text={firstCap} keyPrefix="film-cap" />
        )}
      </Node>,
    );
    if (mode === 'film') {
      const jobs: any[] = [
        playFilmMotion(view, sc),
        playCaptions(view, sc, 'film-cap'),
      ];
      if (XFADE_IN.has(sc.id)) jobs.push(fadeTransition(0.24));
      yield* all(...jobs);
    } else {
      yield* waitFor(dur);
    }
  });
}

export function buildFilmProject(mode: FilmMode, onlySceneIds?: string[]) {
  const list = contentScenes().filter(
    s => !onlySceneIds || onlySceneIds.includes(s.id),
  );
  return makeProject({
    name:
      mode === 'film'
        ? 'product-courseware-4-film-v2'
        : 'product-courseware-4-editor-bg',
    scenes: list.map(sc => makeFilmScene(sc, mode)),
    settings: {
      shared: {
        size: {x: 1920, y: 1080},
        background: SILK,
      },
      rendering: {fps: 30},
      preview: {fps: 30},
    },
  });
}

export default buildFilmProject('film');
