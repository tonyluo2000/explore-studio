// Runs the website's real Journey logic (course4teen-website/lib/journeyState.ts)
// under Node's TypeScript type stripping, for tests/test_journey_map.py.
//
// stdin: JSON { journey?, published?, through?: string[], contexts?: string[] }
//   journey / published override the committed data, so tests can mutate it.
// stdout: JSON { errors, current, states: {id: state}, contexts: {id: view|null} }

import { readFileSync } from "node:fs";
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
const result = { errors, current: null, states: {}, contexts: {} };
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
}
process.stdout.write(JSON.stringify(result));
