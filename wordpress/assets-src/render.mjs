// Renders banner.html into the WordPress.org banner sizes in ../assets/.
//   node wordpress/assets-src/render.mjs   (needs `npm run start`, and Playwright)
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
for (const [scale, name] of [[1, "banner-772x250.png"], [2, "banner-1544x500.png"]]) {
  const page = await browser.newPage({ viewport: { width: 772, height: 250 }, deviceScaleFactor: scale });
  await page.goto("file://" + path.join(here, "banner.html"));
  await page.waitForFunction(() => document.querySelectorAll("quran-madina-html-line").length > 0);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(here, "..", "assets", name) });
  console.log("wrote", name);
}
await browser.close();
