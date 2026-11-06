// Run against a fresh static export served locally. Playwright and axe can be
// installed outside the repo; set PLAYWRIGHT_MODULE and AXE_MODULE to their
// module paths. QA_SITE_URL defaults to localhost:4177; QA_OUTPUT_DIR is required.
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE ?? "playwright");
const AxeBuilder = require(process.env.AXE_MODULE ?? "@axe-core/playwright").default;
const base = process.env.QA_SITE_URL ?? "http://127.0.0.1:4177";
const output = process.env.QA_OUTPUT_DIR;
assert(output, "Set QA_OUTPUT_DIR to a screenshot/report folder outside the source tree");
mkdirSync(output, { recursive: true });
const published = Array.from({ length: 6 }, (_, i) => `s0${i + 1}`);
const routes = ["/students/journey/", ...published.flatMap((id) => [
  `/students/slides/${id}/`, `/students/learn/${id}/`,
])];
const screenshotRoutes = new Set(["/students/journey/", ...["s01", "s06"].flatMap((id) => [
  `/students/slides/${id}/`, `/students/learn/${id}/`,
])]);
const browser = await chromium.launch();
const results = [];
try {
  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await context.newPage();
    for (const route of routes) {
      const errors = [];
      const onError = (error) => errors.push(error.message);
      page.on("pageerror", onError);
      assert.equal((await page.goto(`${base}${route}`)).status(), 200);
      await page.locator(".python-journey").waitFor();
      await page.evaluate(() => document.fonts.ready);
      const layout = await page.evaluate(() => {
        const panel = document.querySelector(".python-journey");
        const world = document.querySelector(".journey-context");
        const pythonBox = panel.getBoundingClientRect();
        const worldBox = world?.getBoundingClientRect();
        const current = panel.querySelector('[aria-current="step"]');
        return {
          viewport: innerWidth,
          width: document.documentElement.scrollWidth,
          panelWidth: panel.scrollWidth,
          panelClient: panel.clientWidth,
          ids: [...panel.querySelectorAll("[data-python-step]")].map((node) => node.dataset.pythonStep),
          current: current?.dataset.pythonStep,
          currentText: current?.textContent,
          text: panel.textContent,
          topicFont: parseFloat(getComputedStyle(panel.querySelector(".python-journey-step-heading")).fontSize),
          parallel: worldBox ? (innerWidth >= 900
            ? Math.abs(worldBox.top - pythonBox.top) < 2 && worldBox.right < pythonBox.left
            : worldBox.bottom < pythonBox.top) : true,
          listRole: panel.querySelector("ol")?.getAttribute("role"),
        };
      });
      assert(layout.width <= layout.viewport, `${route} overflows at ${viewport.width}: ${layout.width}`);
      assert(layout.panelWidth <= layout.panelClient, `${route} panel overflows`);
      assert(layout.parallel, `${route} companion layout is wrong`);
      assert(layout.topicFont >= 14, `${route} has unreadably small topics`);
      assert.equal(layout.listRole, "list");
      const count = route.includes("journey") ? 6 : Number(route.match(/s(\d\d)/)[1]);
      assert.deepEqual(layout.ids, published.slice(0, count).map((id) => id.toUpperCase()));
      assert.equal(layout.current, `S0${count}`);
      assert(layout.currentText.includes("You are here"));
      assert(!layout.text.includes("Boolean"));
      if (route.includes("journey")) {
        await page.locator("#python-journey").scrollIntoViewIfNeeded();
      }
      const axe = await new AxeBuilder({ page })
        .include(".python-journey").include(".journey-context")
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      assert.deepEqual(axe.violations, [], `${route} accessibility violations`);
      // Start at the document and reach a Python link using only Tab.
      await page.evaluate(() => document.activeElement?.blur());
      let keyboardLink = false;
      for (let i = 0; i < 65; i++) {
        await page.keyboard.press("Tab");
        keyboardLink = await page.evaluate(() => Boolean(document.activeElement?.matches(".python-journey-link")));
        if (keyboardLink) break;
      }
      assert(keyboardLink, `${route} Python links are not keyboard reachable`);
      assert(await page.locator(".python-journey-link:focus-visible").count());
      if (!route.includes("journey")) {
        await page.keyboard.press("Enter");
        await page.waitForURL("**/students/journey/#python-journey");
        assert(await page.locator("#python-journey").isVisible());
        await page.goto(`${base}${route}`);
      }
      if (screenshotRoutes.has(route)) {
        await page.evaluate(() => document.activeElement?.blur());
        await page.mouse.click(0, 0);
        const name = `${viewport.width}-${route.split("/").filter(Boolean).join("-")}`;
        const capture = async (selector, path) => {
          // Capture document coordinates from the top, so fixed offscreen
          // controls are not pulled into a tall element's screenshot.
          await page.evaluate(() => window.scrollTo(0, 0));
          const clip = await page.locator(selector).boundingBox();
          assert(clip);
          await page.screenshot({ path, clip, fullPage: true });
        };
        if (route.includes("journey")) {
          for (const [part, selector] of [["hero", ".journey-hero"], ["map", ".journey-map-section"], ["python", ".python-journey"]]) {
            await capture(selector, join(output, `${name}-${part}.png`));
          }
        } else {
          await capture(".slides-hero", join(output, `${name}.png`));
        }
      }
      page.off("pageerror", onError);
      assert.deepEqual(errors, [], `${route} browser errors`);
      results.push({ route, viewport, ...layout, axeViolations: axe.violations.length, keyboardLink });
      process.stdout.write(`PASS ${viewport.width} ${route}\n`);
    }
    await context.close();
  }
} finally {
  await browser.close();
}
writeFileSync(join(output, "report.json"), JSON.stringify(results, null, 2));
process.stdout.write(`${results.length} responsive/accessibility checks passed. Evidence: ${output}\n`);
