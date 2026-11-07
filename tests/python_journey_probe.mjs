// Exercise the real TypeScript module and server-render the real component.
// stdin: { sessions?: string[], published?: string[] }; stdout: JSON.
import { readFileSync } from "node:fs";
import { createRequire, Module } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const website = join(dirname(fileURLToPath(import.meta.url)), "..", "course4teen-website");
const requireSite = createRequire(join(website, "package.json"));
const ts = requireSite("typescript");
for (const extension of [".ts", ".tsx"]) {
  Module._extensions[extension] = (module, filename) => {
    const { outputText } = ts.transpileModule(readFileSync(filename, "utf8"), {
      fileName: filename,
      compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
    });
    module._compile(outputText, filename);
  };
}
const request = JSON.parse(readFileSync(0, "utf8") || "{}");
const calendar = requireSite("./lib/calendar.ts");
if (request.published) calendar.sessionsWithSlides = request.published;
const journey = requireSite("./lib/pythonJourney.ts");
const PythonJourney = requireSite("./app/components/PythonJourney.tsx").default;
const { createElement } = requireSite("react");
const { renderToStaticMarkup } = requireSite("react-dom/server");
const render = (props) => renderToStaticMarkup(createElement(PythonJourney, props));
const sessions = request.sessions ?? [...calendar.sessionsWithSlides, "S08", "S30", "unknown"];
process.stdout.write(JSON.stringify({
  published: journey.publishedPythonSteps,
  publication: calendar.sessionsWithSlides,
  current: journey.currentPythonStep,
  total: journey.totalPythonSteps,
  full: render({ mode: "full" }),
  histories: Object.fromEntries(sessions.map((id) => [id, journey.pythonJourneyThrough(id)])),
  compact: Object.fromEntries(sessions.map((id) => [id, render({ mode: "compact", session: id })])),
}));
