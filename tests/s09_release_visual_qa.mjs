// Supplement the shared journey QA with calendar/listing and S09 teaching cards.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE ?? "playwright");
const output = process.env.QA_OUTPUT_DIR;
assert(output);
mkdirSync(output, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.QA_BROWSER_PATH });
const results = [];
try {
  for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 1000 }]) {
    const page = await browser.newPage({ viewport, reducedMotion: "reduce" });
    for (const route of ["/calendar/", "/students/slides/", "/students/slides/s09/", "/students/learn/s09/", "/students/journey/"]) {
      assert.equal((await page.goto(`http://127.0.0.1:4177${route}`)).status(), 200);
      await page.evaluate(() => document.fonts.ready);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const text = await page.locator("main").innerText();
      for (const phrase of ["Comparisons and assertions", "Weather Reader", "respond_to_counter", ">="]) assert(!text.includes(phrase));
      if (route.includes("s09")) {
        const cards = page.locator(".slide-card");
        for (let i = 0; i < await cards.count(); i++) {
          const card = cards.nth(i);
          await card.scrollIntoViewIfNeeded();
          await card.evaluate(async (element) => Promise.all([...element.querySelectorAll("img")].map((img) => img.decode())));
          assert(await card.isVisible());
        }
        const index = route.includes("slides") ? 8 : 1;
        await cards.nth(index).screenshot({ path: join(output, `${viewport.width}-${route.includes("slides") ? "off-by-one" : "learn-code"}.png`) });
        if (route.includes("slides")) await cards.nth(17).screenshot({ path: join(output, `${viewport.width}-exact-goal.png`) });
      } else {
        await page.screenshot({ path: join(output, `${viewport.width}-${route.split("/").filter(Boolean).join("-")}.png`), fullPage: true });
      }
      results.push({ route, viewport, overflow: false, futureDetails: false });
    }
    await page.close();
  }
} finally { await browser.close(); }
writeFileSync(join(output, "report.json"), JSON.stringify(results, null, 2));
console.log(`${results.length} S09 content/listing checks passed`);
