// Runs the website's real Journey logic (course4teen-website/lib/journeyState.ts)
// under Node's TypeScript type stripping, for tests/test_journey_map.py.
//
// stdin: JSON { journey?, published?, through?: string[], contexts?: string[],
//               render?: [{ through, idPrefix? }], identifierPrefix?, namespaces?: [[instanceId, idPrefix?]] }
//   journey / published override the committed data, so tests can mutate it.
//   render server-renders one app/components/JourneyMap.tsx per entry, side by
//   side in one document (TypeScript's own JSX transform, react-dom/server);
//   identifierPrefix is passed to React so useId carries unusual characters.
//   namespaces calls JourneyMap's svgIdNamespace directly on each pair.
// stdout: JSON { errors, current, states: {id: state}, contexts: {id: view|null}, rendered: html|null, namespaces }

import { readFileSync } from "node:fs";
import { createRequire, Module } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const website = join(dirname(fileURLToPath(import.meta.url)), "..", "course4teen-website");
const load = (relative) => import(pathToFileURL(join(website, relative)).href);

const { classSessions, sessionsWithSlides } = await load("lib/calendar.ts");
const { sessionsWithNotes } = await load("lib/learn.ts");
const logic = await load("lib/journeyState.ts");

const request = JSON.parse(readFileSync(0, "utf8") || "{}");
const readJson = (relative) => JSON.parse(readFileSync(join(website, relative), "utf8"));

const inputs = {
  journey: request.journey ?? readJson("journey/journey.json"),
  sessions: classSessions,
  published: request.published ?? sessionsWithSlides,
  notes: sessionsWithNotes,
  snapshots: readJson("journey/snapshots.json").snapshots,
};

const errors = logic.validateJourney(inputs);
const result = { errors, current: null, states: {}, contexts: {}, rendered: null, namespaces: null };
if (errors.length === 0) {
  result.current = logic.currentSessionId(inputs);
  for (const through of request.through ?? []) {
    try {
      result.states[through] = logic.journeyState(inputs, through);
    } catch (error) {
      result.states[through] = { error: String(error.message) };
    }
  }
  for (const id of request.contexts ?? []) result.contexts[id] = logic.journeyContextFor(inputs, id);
  if (request.render) result.rendered = renderMaps(request.render, request.identifierPrefix);
}
if (request.namespaces) {
  const { svgIdNamespace } = loadTsx("app/components/JourneyMap.tsx");
  result.namespaces = request.namespaces.map(([instanceId, idPrefix]) => svgIdNamespace(instanceId, idPrefix ?? undefined));
}
process.stdout.write(JSON.stringify(result));

/** Load a .tsx module from the website, resolving its imports from the website's node_modules. */
function loadTsx(relative) {
  const requireSite = createRequire(join(website, "package.json"));
  const ts = requireSite("typescript");
  const filename = join(website, relative);
  const { outputText } = ts.transpileModule(readFileSync(filename, "utf8"), {
    fileName: filename,
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
  });
  const module = new Module(filename);
  module.filename = filename;
  module.paths = Module._nodeModulePaths(dirname(filename));
  module._compile(outputText, filename);
  return module.exports;
}

function renderMaps(entries, identifierPrefix) {
  const requireSite = createRequire(join(website, "package.json"));
  const { createElement } = requireSite("react");
  const { renderToStaticMarkup } = requireSite("react-dom/server");
  const JourneyMap = loadTsx("app/components/JourneyMap.tsx").default;
  const { width, height } = inputs.journey.map;
  const maps = entries.map(({ through, idPrefix }, index) =>
    createElement(JourneyMap, { key: index, state: logic.journeyState(inputs, through), width, height, idPrefix }),
  );
  return renderToStaticMarkup(createElement("main", null, ...maps), identifierPrefix ? { identifierPrefix } : undefined);
}
