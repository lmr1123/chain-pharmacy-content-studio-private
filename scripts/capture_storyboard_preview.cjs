#!/usr/bin/env node

const { chromium } = require("playwright");
const path = require("path");
const { pathToFileURL } = require("url");

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) {
    throw new Error("usage: capture_storyboard_preview.cjs <input.html> <output.png>");
  }

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 940 },
    deviceScaleFactor: 1.5,
  });
  await page.goto(pathToFileURL(path.resolve(input)).href, {
    waitUntil: "networkidle",
  });
  await page.screenshot({
    path: path.resolve(output),
    clip: { x: 0, y: 0, width: 1440, height: 940 },
  });
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
