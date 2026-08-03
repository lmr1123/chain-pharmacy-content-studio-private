import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const require=createRequire(import.meta.url);const {chromium}=require('playwright');
const scriptDir=path.dirname(fileURLToPath(import.meta.url));const root=path.resolve(scriptDir,'..');
const browser=await chromium.launch({headless:true,executablePath:'/Users/liminrong/Library/Caches/ms-playwright/chromium_headless_shell-1148/chrome-mac/headless_shell'});
const page=await browser.newPage({viewport:{width:1600,height:1000}});const report={};
await page.goto('http://127.0.0.1:9014/',{waitUntil:'load'});await page.waitForSelector('.scene-item');
report.scene_count=await page.locator('.scene-item').count();
await page.locator('.scene-item').nth(1).click();const headline=page.locator('.scene-headline [contenteditable]');const original=await headline.textContent();
await headline.fill('网页编辑测试');await headline.evaluate(el=>el.blur());await page.waitForTimeout(100);report.text_edit=await headline.textContent()==='网页编辑测试';
await page.locator('#undoBtn').click();await page.waitForTimeout(100);report.undo=await page.locator('.scene-headline [contenteditable]').textContent()===original;
await page.locator('.visual').click();await page.locator('#replaceBtn').click();await page.locator('#imagePicker').setInputFiles(path.join(root,'assets/generated/antioxidant.png'));await page.waitForTimeout(200);report.image_replace=(await page.locator('.visual img').getAttribute('src'))?.startsWith('data:image/')||false;
await page.screenshot({path:path.join(root,'qa/editor-smoke.png'),fullPage:true});report.pptx_export_button=await page.locator('#exportPptxBtn').isVisible();report.mp4_export_button=await page.locator('#exportMp4Btn').isVisible();
await fs.writeFile(path.join(root,'qa/editor-smoke.json'),JSON.stringify(report,null,2)+'\n');await browser.close();
if(report.scene_count!==10||!report.text_edit||!report.undo||!report.image_replace||!report.pptx_export_button||!report.mp4_export_button)process.exitCode=1;else console.log(JSON.stringify(report));
