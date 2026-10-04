/**
 * Course Journey for the site: `journey/journey.json` wired to the calendar,
 * the published Slides and Notes, and the Phase C snapshot manifest.
 *
 * Only Journey-specific facts live in journey.json. Titles and dates come from
 * `classSessions`, publication from `sessionsWithSlides`, Notes from
 * `sessionsWithNotes`, and HERO images from `journey/snapshots.json`. The data
 * is validated when this module loads, so drift fails the build.
 */

import journeyData from "../journey/journey.json";
import snapshotManifest from "../journey/snapshots.json";
import { classSessions, sessionsWithSlides } from "./calendar";
import { sessionsWithNotes } from "./learn";
import {
  currentSessionId,
  journeyContextFor,
  journeyState,
  validateJourney,
  type JourneyData,
  type JourneyInputs,
  type SnapshotEntry,
  type StopView,
} from "./journeyState";

export type { JourneyState, LandmarkView, PathView, RegionView, StopView } from "./journeyState";

export const journeyInputs: JourneyInputs = {
  journey: journeyData as JourneyData,
  sessions: classSessions,
  published: sessionsWithSlides,
  notes: sessionsWithNotes,
  snapshots: snapshotManifest.snapshots as SnapshotEntry[],
};

const problems = validateJourney(journeyInputs);
if (problems.length > 0) {
  throw new Error(`journey/journey.json is out of step:\n- ${problems.join("\n- ")}`);
}

export const JOURNEY_HREF = "/students/journey/";

/** The class Journey as currently published. */
export const currentJourney = journeyState(journeyInputs, currentSessionId(journeyInputs));

export const frontierTeaser = journeyInputs.journey.frontier.teaser;

export const journeyMapSize = {
  width: journeyInputs.journey.map.width,
  height: journeyInputs.journey.map.height,
};

/** Where the class is in the Journey for one published session's page. */
export function journeyContext(sessionId: string): StopView | null {
  return journeyContextFor(journeyInputs, sessionId);
}
