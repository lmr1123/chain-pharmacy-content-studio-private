/**
 * 签样/调试预览入口：只渲染 PREVIEW_SCENES 列出的页面（改常量即可）。
 * 签样门禁 2：S07 推镜头 + S10 序贯 + S11 级联。
 */
import {buildFilmProject} from './project';

export const PREVIEW_SCENES = ['S07_origin', 'S10_audience', 'S11_summary'];

export default buildFilmProject('film', PREVIEW_SCENES);
