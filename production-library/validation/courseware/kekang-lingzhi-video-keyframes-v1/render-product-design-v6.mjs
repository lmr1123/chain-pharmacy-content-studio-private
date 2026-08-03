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
  await page.setViewport({width: 2000, height: 10000, deviceScaleFactor: 1});
  await page.goto(
    pathToFileURL(path.join(here, 'product-course-design-v6.html')).href,
    {waitUntil: 'networkidle0'},
  );
  await page.evaluate(() => document.fonts.ready);

  for (let index = 1; index <= 8; index += 1) {
    const slide = await page.$(`#v6-slide-${index}`);
    if (!slide) throw new Error(`Missing #v6-slide-${index}`);
    await slide.screenshot({
      path: path.join(
        here,
        `product-course-v6-${String(index).padStart(2, '0')}.png`,
      ),
      type: 'png',
    });
  }
} finally {
  await browser.close();
}
