/**
 * 截图像素级复刻 PPTX（去真人）
 * 每页 = cleaned-slides/slide-XX.png 全幅贴图，不做自研版式。
 */
import pptxgen from "pptxgenjs";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const dir = path.dirname(fileURLToPath(import.meta.url));
const slidesDir = path.join(dir, "cleaned-slides");
const out = path.join(dir, "急性上呼吸道感染_呼吸系统疾病健康知识培训_v1.pptx");

const pres = new pptxgen();
pres.defineLayout({ name: "HD", width: 13.333, height: 7.5 });
pres.layout = "HD";
pres.author = "chain-pharmacy-content-studio";
pres.title = "急性上呼吸道感染 · 呼吸系统疾病健康知识培训";
pres.subject = "参课截图像素复刻 · 去真人";

for (let i = 1; i <= 18; i++) {
  const file = path.join(slidesDir, `slide-${String(i).padStart(2, "0")}.png`);
  if (!fs.existsSync(file)) throw new Error(`missing ${file}`);
  const s = pres.addSlide();
  s.addImage({ path: file, x: 0, y: 0, w: 13.333, h: 7.5 });
}

await pres.writeFile({ fileName: out });
console.log("Wrote", out);
