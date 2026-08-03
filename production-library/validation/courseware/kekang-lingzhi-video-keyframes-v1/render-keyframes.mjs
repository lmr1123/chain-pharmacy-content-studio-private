import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const requireFromGoldSample = createRequire(
  path.join(here, '../../../../poc/gold-sample/package.json'),
);
const puppeteer = requireFromGoldSample('puppeteer');

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

try {
  const page = await browser.newPage();
  await page.setViewport({width: 2000, height: 1200, deviceScaleFactor: 1});
  await page.goto(pathToFileURL(path.join(here, 'keyframes.html')).href, {
    waitUntil: 'networkidle0',
  });
  await page.evaluate(() => document.fonts.ready);

  for (let index = 1; index <= 4; index += 1) {
    const slide = await page.$(`#slide-${index}`);
    if (!slide) throw new Error(`Missing #slide-${index}`);
    await slide.screenshot({
      path: path.join(here, `keyframe-${String(index).padStart(2, '0')}.png`),
      type: 'png',
    });
  }
} finally {
  await browser.close();
}
