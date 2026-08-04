/**
 * 签样/调试预览入口：只渲染 PREVIEW_SCENES 列出的页面（改常量即可）。
 * 签样门禁 1：S04 终态帧 + S05 微镜头。
 */
import {buildFilmProject} from './project';

export const PREVIEW_SCENES = ['S04_benefit_1', 'S05_benefit_2'];

export default buildFilmProject('film', PREVIEW_SCENES);
