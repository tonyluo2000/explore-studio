/**
 * Shared class calendar + session data for course4teen-website.
 *
 * Class dates follow the HXGNY 2026-27 school calendar rule: every school
 * week starts Sunday and ends Saturday, and Explore Studio meets on the
 * Saturday ending each HXGNY-numbered school week. Source of truth:
 * https://www.hxgny.org/wp/wp-content/uploads/2026/04/2026-27-HXGNY-School-Calendar.pdf
 */

export type ClassSession = {
  /** Session id, e.g. "S01". */
  id: string;
  /** 1-indexed session number. */
  number: number;
  /** ISO date (YYYY-MM-DD) of the Saturday this session meets. */
  date: string;
  /** Canonical session title from the Explore Studio curriculum. */
  title: string;
};

export type BreakPeriod = {
  /** Human-readable label for the no-school period. */
  label: string;
  /** ISO date (YYYY-MM-DD) the break week starts (Sunday). */
  startDate: string;
  /** ISO date (YYYY-MM-DD) the break week ends (Saturday). */
  endDate: string;
  /** Session id this break falls immediately after, for display ordering. */
  afterSessionId: string;
};

export const classSessions: ClassSession[] = [
  { id: "S01", number: 1, date: "2026-09-19", title: "Explorer's Field Notes" },
  { id: "S02", number: 2, date: "2026-09-26", title: "Place Your First Prop" },
  { id: "S03", number: 3, date: "2026-10-03", title: "Make the World React" },
  { id: "S04", number: 4, date: "2026-10-10", title: "Introduce a Character" },
  { id: "S05", number: 5, date: "2026-10-17", title: "Script a Conversation" },
  { id: "S06", number: 6, date: "2026-10-24", title: "Build a Themed Collection" },
  { id: "S07", number: 7, date: "2026-10-31", title: "Create a Two-State Prop" },
  { id: "S08", number: 8, date: "2026-11-07", title: "Build an If/Else Guardian" },
  { id: "S09", number: 9, date: "2026-11-21", title: "Power Up a Device" },
  { id: "S10", number: 10, date: "2026-11-28", title: "Check the Boundary" },
  { id: "S11", number: 11, date: "2026-12-12", title: "Require Both Keys" },
  { id: "S12", number: 12, date: "2026-12-19", title: "Allow Either Key" },
  { id: "S13", number: 13, date: "2027-01-16", title: "Turn the Rule Around" },
  { id: "S14", number: 14, date: "2027-01-23", title: "Refactor a Shared Look" },
  { id: "S15", number: 15, date: "2027-01-30", title: "Ship a Secret Sequence" },
  { id: "S16", number: 16, date: "2027-02-06", title: "Curator's Atlas" },
  { id: "S17", number: 17, date: "2027-02-27", title: "Clue Finder" },
  { id: "S18", number: 18, date: "2027-03-06", title: "Power Station Scoreboard" },
  { id: "S19", number: 19, date: "2027-03-13", title: "Route Planner" },
  { id: "S20", number: 20, date: "2027-03-20", title: "Data-Built Mystery Trail" },
  { id: "S21", number: 21, date: "2027-03-27", title: "Package Gatekeeper" },
  { id: "S22", number: 22, date: "2027-04-10", title: "Traceback Detective" },
  { id: "S23", number: 23, date: "2027-04-17", title: "Builder's Workshop" },
  { id: "S24", number: 24, date: "2027-04-24", title: "Fast Ranger Index" },
  { id: "S25", number: 25, date: "2027-05-08", title: "Playable Prototype" },
  { id: "S26", number: 26, date: "2027-05-15", title: "Capstone Blueprint" },
  { id: "S27", number: 27, date: "2027-05-22", title: "Capstone Core" },
  { id: "S28", number: 28, date: "2027-05-29", title: "Capstone Integration" },
  { id: "S29", number: 29, date: "2027-06-12", title: "Expedition Review" },
  { id: "S30", number: 30, date: "2027-06-19", title: "World Premiere" },
];

export const breakPeriods: BreakPeriod[] = [
  { label: "Fall Break", startDate: "2026-11-08", endDate: "2026-11-14", afterSessionId: "S08" },
  { label: "Thanksgiving Break", startDate: "2026-11-29", endDate: "2026-12-05", afterSessionId: "S10" },
  { label: "Winter Holiday", startDate: "2026-12-20", endDate: "2027-01-09", afterSessionId: "S12" },
  { label: "Chinese New Year & Winter Break", startDate: "2027-02-07", endDate: "2027-02-20", afterSessionId: "S16" },
  { label: "Easter Weekend", startDate: "2027-03-28", endDate: "2027-04-03", afterSessionId: "S21" },
  { label: "Color Run Day", startDate: "2027-04-25", endDate: "2027-05-01", afterSessionId: "S24" },
  { label: "Memorial Day", startDate: "2027-05-30", endDate: "2027-06-05", afterSessionId: "S28" },
];

/** Ids of sessions that currently have a published web slide deck. */
export const sessionsWithSlides: readonly string[] = ["S01", "S02"];

export function formatSessionDate(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00`);
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatBreakRange(startIso: string, endIso: string): string {
  const start = new Date(`${startIso}T00:00:00`);
  const end = new Date(`${endIso}T00:00:00`);
  const sameMonth = start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear();
  const startMonth = start.toLocaleDateString("en-US", { month: "short" });
  const endMonth = end.toLocaleDateString("en-US", { month: "short" });
  const startLabel = `${startMonth} ${start.getDate()}`;
  const endLabel = sameMonth
    ? `${end.getDate()}, ${end.getFullYear()}`
    : `${endMonth} ${end.getDate()}, ${end.getFullYear()}`;
  return `${startLabel}–${endLabel}`;
}
