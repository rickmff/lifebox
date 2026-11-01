// Renders docs/video/flow.html frame by frame (1920x1080) with Playwright.
// Usage: node docs/video/render.js <frames dir> [frame numbers...]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const out = path.resolve(process.argv[2] || '.work/frames');
  const only = process.argv.slice(3).map(Number);
  fs.rmSync(out, { recursive: true, force: true });
  fs.mkdirSync(out, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await page.goto('file://' + path.join(__dirname, 'flow.html'));
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(() => window.TOTAL_FRAMES);
  const frames = only.length ? only : [...Array(total).keys()];
  for (const i of frames) {
    await page.evaluate(f => window.render(f), i);
    await page.screenshot({ path: path.join(out, `f${String(i).padStart(4, '0')}.png`) });
  }
  await browser.close();
  console.log(`rendered ${frames.length} of ${total} frames into ${out}`);
})();
