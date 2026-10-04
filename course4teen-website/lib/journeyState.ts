/**
 * Pure Course Journey logic: validation, progressive reveal, and per-session
 * context. It imports nothing, so `lib/journey.ts` wires it to the real data
 * for the site and the Journey tests can run it directly under Node.
 *
 * Progression is publication-based only. "Through S03" means the class has
 * been taught (and the site has published) S01–S03; it says nothing about any
 * one student's progress.
 */

export const JOURNEY_SCHEMA = "course4teen/journey@1";
export const STORY_MAX_CHARS = 90;

/** How visible one piece of the map is. Order matters: later is more visible. */
export type RevealState = "hidden" | "fogged" | "hinted" | "revealed" | "current";

export type RevealStep = { from: string; state: "fogged" | "hinted" | "revealed"; detail?: string };

export type JourneyRegion = {
  id: string;
  name?: string;
  frontier?: boolean;
  label: { x: number; y: number };
  shape: string;
  reveal: RevealStep[];
};

export type JourneyLandmark = {
  id: string;
  name: string;
  hint?: string;
  region: string;
  icon: string;
  x: number;
  y: number;
  reveal: RevealStep[];
};

export type JourneyPath = {
  id: string;
  kind: "trail" | "bearing";
  from: string;
  to: string;
  d: string;
  reveal: RevealStep[];
};

export type StopKind = "arrive" | "reveal" | "deepen";

export type JourneyStop = {
  session: string;
  kind: StopKind;
  landmark: string;
  headline: "landmark" | "region";
  story: string;
  snapshot: string;
  snapshotAlt: string;
};

export type JourneyData = {
  schema: string;
  note?: string;
  map: { width: number; height: number; plateOffsetY: number };
  regions: JourneyRegion[];
  landmarks: JourneyLandmark[];
  paths: JourneyPath[];
  frontier: { teaser: string };
  stops: JourneyStop[];
};

export type CalendarSession = { id: string; number: number; date: string; title: string };

export type SnapshotImage = { src: string; width: number; height: number };

export type SnapshotEntry = {
  session: string;
  moment: string;
  kind: string;
  images: Record<string, SnapshotImage>;
};

/** Everything the Journey derives from; only `journey` is Journey-specific. */
export type JourneyInputs = {
  journey: JourneyData;
  sessions: readonly CalendarSession[];
  /** Sessions with published Slides, in course order (the publication source). */
  published: readonly string[];
  /** Sessions with published Python Notes. */
  notes: readonly string[];
  snapshots: readonly SnapshotEntry[];
};

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

const RANK: Record<RevealState, number> = { hidden: 0, fogged: 1, hinted: 2, revealed: 3, current: 4 };
const LANDMARK_STATES = new Set(["hinted", "revealed"]);
const REGION_STATES = new Set(["fogged", "revealed"]);
const PATH_STATES = new Set(["hinted", "revealed"]);

/** The JSON shape journey.json may take. Every field it owns is listed here. */
type Shape =
  | { type: "string" | "number" | "true" }
  | { type: "enum"; values: readonly string[] }
  | { type: "array"; items: Shape }
  | { type: "object"; fields: Record<string, Shape>; optional: readonly string[] };

const STRING: Shape = { type: "string" };
const NUMBER: Shape = { type: "number" };
const oneOf = (...values: string[]): Shape => ({ type: "enum", values });
const list = (items: Shape): Shape => ({ type: "array", items });
const record = (fields: Record<string, Shape>, optional: readonly string[] = []): Shape => ({
  type: "object",
  fields,
  optional,
});

const STEP_SHAPE = record({ from: STRING, state: oneOf("fogged", "hinted", "revealed"), detail: STRING }, ["detail"]);
const REVEAL_SHAPE = list(STEP_SHAPE);
const JOURNEY_SHAPE = record(
  {
    schema: STRING,
    note: STRING,
    map: record({ width: NUMBER, height: NUMBER, plateOffsetY: NUMBER }),
    regions: list(
      record(
        {
          id: STRING,
          name: STRING,
          frontier: { type: "true" },
          label: record({ x: NUMBER, y: NUMBER }),
          shape: STRING,
          reveal: REVEAL_SHAPE,
        },
        ["name", "frontier"],
      ),
    ),
    landmarks: list(
      record(
        { id: STRING, name: STRING, hint: STRING, region: STRING, icon: STRING, x: NUMBER, y: NUMBER, reveal: REVEAL_SHAPE },
        ["hint"],
      ),
    ),
    paths: list(
      record({ id: STRING, kind: oneOf("trail", "bearing"), from: STRING, to: STRING, d: STRING, reveal: REVEAL_SHAPE }),
    ),
    frontier: record({ teaser: STRING }),
    stops: list(
      record({
        session: STRING,
        kind: oneOf("arrive", "reveal", "deepen"),
        landmark: STRING,
        headline: oneOf("landmark", "region"),
        story: STRING,
        snapshot: STRING,
        snapshotAlt: STRING,
      }),
    ),
  },
  ["note"],
);

/**
 * Field names for facts the Journey derives instead of owning: titles and
 * dates (calendar), publication (sessionsWithSlides), Slides and Notes URLs
 * (the session id), and HERO images (the snapshot manifest). Compared after
 * lower-casing and dropping punctuation, so `slides_url` is `slidesurl`.
 * Only the schema above may use one of these names, and only where it says.
 */
const CANONICAL_FIELDS = new Set([
  "title", "sessiontitle", "date", "dates", "sessiondate", "number", "sessionnumber", "totalsessions", "nextsession",
  "published", "publication", "publicationstate", "publishedat", "ispublished", "unpublished",
  "slides", "slidesurl", "slideshref", "slideslink", "slidespath",
  "notes", "notesurl", "noteshref", "noteslink", "learn", "learnurl", "learnhref", "learnlink",
  "href", "url", "link", "path", "src", "srcset",
  "image", "images", "img", "hero", "herourl", "herosrc", "heroimage", "snapshot", "snapshots",
  "snapshoturl", "snapshotsrc", "snapshotimage",
]);

function isCanonicalField(key: string): boolean {
  return CANONICAL_FIELDS.has(key.toLowerCase().replace(/[^a-z0-9]/g, ""));
}

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

/** Any canonical field name anywhere inside a subtree the schema does not own. */
function scanUnowned(value: unknown, where: string, errors: string[]): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => scanUnowned(item, `${where}[${index}]`, errors));
  } else if (isPlainObject(value)) {
    for (const [key, child] of Object.entries(value)) {
      if (isCanonicalField(key)) errors.push(`${where} has canonical field ${key}, which journey.json must not own`);
      scanUnowned(child, `${where}.${key}`, errors);
    }
  }
}

/**
 * Journey-owned text may describe the map but never restate a canonical
 * fact: no calendar title or date, and no Slides, Notes, or image URL.
 */
function checkOwnedText(text: string, where: string, sessions: readonly CalendarSession[], errors: string[]): void {
  if (/\b\d{4}-\d{2}-\d{2}\b/.test(text)) errors.push(`${where} carries a date; dates come from the calendar`);
  if (/(https?:)?\/\/|\/students\/|\/journey\/|\.(webp|png|jpe?g|gif|avif)\b/i.test(text)) {
    errors.push(`${where} carries a URL or image path; Slides, Notes, and HERO images are derived`);
  }
  const lower = text.toLowerCase();
  for (const session of sessions) {
    if (lower.includes(session.title.toLowerCase())) {
      errors.push(`${where} repeats the calendar title of ${session.id}`);
    }
  }
}

/** Walk `value` against `shape`: wrong types, missing fields, and unknown keys at any depth. */
function checkShape(
  value: unknown,
  shape: Shape,
  where: string,
  sessions: readonly CalendarSession[],
  errors: string[],
): void {
  // A scalar field holding an object or list is wrong, and may hide a copy.
  if (shape.type !== "object" && shape.type !== "array" && typeof value === "object" && value !== null) {
    scanUnowned(value, where, errors);
  }
  switch (shape.type) {
    case "string":
      if (typeof value !== "string") errors.push(`${where} must be a string`);
      else checkOwnedText(value, where, sessions, errors);
      return;
    case "number":
      if (typeof value !== "number" || !Number.isFinite(value)) errors.push(`${where} must be a number`);
      return;
    case "true":
      if (value !== true) errors.push(`${where} must be true when present`);
      return;
    case "enum":
      if (typeof value !== "string" || !shape.values.includes(value)) {
        errors.push(`${where} must be one of ${shape.values.join(", ")}`);
      }
      return;
    case "array":
      if (!Array.isArray(value)) errors.push(`${where} must be a list`);
      else value.forEach((item, index) => checkShape(item, shape.items, `${where}[${index}]`, sessions, errors));
      return;
    case "object":
      if (!isPlainObject(value)) {
        errors.push(`${where} must be an object`);
        return;
      }
      for (const [key, child] of Object.entries(value)) {
        const field = shape.fields[key];
        if (field) {
          checkShape(child, field, `${where}.${key}`, sessions, errors);
          continue;
        }
        errors.push(`${where} has unknown key ${key}`);
        if (isCanonicalField(key)) errors.push(`${where} has canonical field ${key}, which journey.json must not own`);
        scanUnowned(child, `${where}.${key}`, errors);
      }
      for (const key of Object.keys(shape.fields)) {
        if (!(key in value) && !shape.optional.includes(key)) errors.push(`${where} is missing ${key}`);
      }
  }
}

/** Lower-case words only, so a teaser can be matched inside the story it echoes. */
function words(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9']+/g, " ").trim();
}

/**
 * Every reason the Journey data disagrees with the calendar, the publication
 * state, or the snapshot manifest. An empty list means the data is valid.
 */
export function validateJourney(inputs: JourneyInputs): string[] {
  const { journey, sessions, published, snapshots } = inputs;
  const errors: string[] = [];

  // Shape first, recursively: nothing outside the schema, so no nested copy
  // of a title, date, publication flag, URL, or image can ride along. The
  // checks below assume the shape, so a malformed file stops here.
  checkShape(journey, JOURNEY_SHAPE, "journey", sessions, errors);
  if (errors.length > 0) return errors;

  const order = new Map(sessions.map((session, index) => [session.id, index]));
  if (journey.schema !== JOURNEY_SCHEMA) errors.push(`schema must be ${JOURNEY_SCHEMA}`);

  // Publication: the published sessions are S01..Sn in course order.
  published.forEach((id, index) => {
    if (sessions[index]?.id !== id) errors.push(`published sessions must run S01 onward in order; found ${id}`);
  });
  const latest = published.at(-1);

  // Exactly one stop per published session, and nothing for unpublished ones.
  const stopIds = journey.stops.map((stop) => stop.session);
  if (stopIds.join() !== published.join()) {
    errors.push(`stops ${stopIds.join(",")} must be exactly the published sessions ${published.join(",")}`);
  }
  const stopSessions = new Set(stopIds);

  const regionIds = new Set(journey.regions.map((region) => region.id));
  const landmarksById = new Map(journey.landmarks.map((landmark) => [landmark.id, landmark]));
  const ids = [...journey.regions, ...journey.landmarks, ...journey.paths].map((item) => item.id);
  for (const id of ids.filter((id, index) => ids.indexOf(id) !== index)) errors.push(`duplicate id ${id}`);

  const checkSteps = (owner: string, steps: RevealStep[], allowed: Set<string>, mustReveal: boolean) => {
    if (steps.length === 0) errors.push(`${owner} has no reveal steps`);
    let previousIndex = -1;
    let previousRank = 0;
    for (const step of steps) {
      if (!stopSessions.has(step.from)) {
        errors.push(`${owner} reveals in ${step.from}, which has no published Journey stop`);
      }
      if (!allowed.has(step.state)) errors.push(`${owner} cannot be ${step.state}`);
      const index = order.get(step.from) ?? -1;
      if (index <= previousIndex) errors.push(`${owner} reveal steps must move forward in course order`);
      if (RANK[step.state] < previousRank) errors.push(`${owner} cannot become less visible`);
      previousIndex = index;
      previousRank = RANK[step.state];
    }
    // A name may only ship once it is revealed: nothing named waits in the
    // data for a future session.
    if (mustReveal && steps.at(-1)?.state !== "revealed") {
      errors.push(`${owner} is named but never revealed by a published session`);
    }
  };

  // The frontier: exactly one generic, unnamed fog bank. It appears, fogged,
  // only at the current (latest published) stop, carries no detail, holds no
  // landmark, and its teaser only echoes that stop's published story.
  const frontiers = journey.regions.filter((region) => region.frontier === true);
  if (frontiers.length !== 1) {
    errors.push(`exactly one generic fog frontier is required; found ${frontiers.length}`);
  }
  for (const region of journey.regions) {
    if (region.frontier) {
      if (region.name !== undefined) errors.push(`frontier ${region.id} must stay unnamed`);
      const [step, ...more] = region.reveal;
      if (more.length > 0 || step?.state !== "fogged" || step.from !== latest) {
        errors.push(`frontier ${region.id} must appear once, fogged, at the current stop ${latest}`);
      }
      if (region.reveal.some((item) => item.detail !== undefined)) {
        errors.push(`frontier ${region.id} may carry no reveal detail`);
      }
      checkSteps(`region ${region.id}`, region.reveal, REGION_STATES, false);
    } else {
      if (!region.name) errors.push(`region ${region.id} needs a name`);
      checkSteps(`region ${region.id}`, region.reveal, REGION_STATES, true);
    }
  }
  const teaser = words(journey.frontier.teaser);
  const currentStory = words(journey.stops.find((stop) => stop.session === latest)?.story ?? "");
  if (!teaser || teaser.length > STORY_MAX_CHARS || !` ${currentStory} `.includes(` ${teaser} `)) {
    errors.push(`frontier teaser must only echo the current stop's published story`);
  }

  for (const landmark of journey.landmarks) {
    if (!regionIds.has(landmark.region)) errors.push(`landmark ${landmark.id} names unknown region ${landmark.region}`);
    if (frontiers.some((region) => region.id === landmark.region)) {
      errors.push(`landmark ${landmark.id} cannot sit in the unnamed frontier`);
    }
    if (landmark.reveal.some((step) => step.state === "hinted") && !landmark.hint) {
      errors.push(`landmark ${landmark.id} is hinted but has no unnamed hint text`);
    }
    checkSteps(`landmark ${landmark.id}`, landmark.reveal, LANDMARK_STATES, true);
  }

  // Path endpoints, at every step of every path, in the state that step
  // computes (the same stepAt the map uses):
  // - both ends exist and are on the map (hinted or revealed), never hidden;
  // - at least one end is revealed, so a line always starts from charted ground;
  // - a revealed bearing points at a revealed landmark at both ends.
  // A revealed trail may still reach a hinted landmark: in S01 the meadow
  // trails lead to the unnamed stone circle.
  for (const path of journey.paths) {
    for (const end of [path.from, path.to]) {
      if (!landmarksById.has(end)) errors.push(`path ${path.id} names unknown landmark ${end}`);
    }
    checkSteps(`path ${path.id}`, path.reveal, PATH_STATES, true);
    for (const step of path.reveal) {
      const index = order.get(step.from);
      if (index === undefined) continue;
      const ends = [path.from, path.to].flatMap((end) => {
        const landmark = landmarksById.get(end);
        const state: RevealState = stepAt(landmark?.reveal ?? [], index, order)?.state ?? "hidden";
        return landmark ? [{ end, state }] : [];
      });
      for (const { end, state } of ends) {
        if (RANK[state] < RANK.hinted) {
          errors.push(`path ${path.id} is ${step.state} in ${step.from}, but its end ${end} is ${state} there`);
        } else if (path.kind === "bearing" && step.state === "revealed" && state !== "revealed") {
          errors.push(`bearing ${path.id} is revealed in ${step.from}, but its end ${end} is only ${state} there`);
        }
      }
      if (ends.length === 2 && !ends.some(({ state }) => state === "revealed")) {
        errors.push(`path ${path.id} is ${step.state} in ${step.from}, but neither end is revealed there`);
      }
    }
  }

  journey.stops.forEach((stop, index) => {
    const owner = `stop ${stop.session}`;
    if (stop.story.length > STORY_MAX_CHARS) errors.push(`${owner} story is over ${STORY_MAX_CHARS} characters`);
    const landmark = landmarksById.get(stop.landmark);
    if (!landmark) {
      errors.push(`${owner} names unknown landmark ${stop.landmark}`);
      return;
    }
    const stepAtStop = landmark.reveal.find((step) => step.from === stop.session);
    const before = landmark.reveal.filter((step) => (order.get(step.from) ?? 0) < (order.get(stop.session) ?? 0));
    if (stop.kind === "arrive" && index !== 0) errors.push(`${owner} can only arrive at the first stop`);
    if ((stop.kind === "arrive" || stop.kind === "reveal") && stepAtStop?.state !== "revealed") {
      errors.push(`${owner} must reveal ${landmark.id} in that session`);
    }
    if (stop.kind === "deepen" && (before.at(-1)?.state !== "revealed" || !stepAtStop?.detail)) {
      errors.push(`${owner} must deepen an already revealed ${landmark.id} with a new detail`);
    }
    const hero = snapshots.find((entry) => entry.moment === stop.snapshot);
    if (!hero) errors.push(`${owner} names snapshot ${stop.snapshot}, which the manifest does not publish`);
    else if (hero.session !== stop.session || hero.kind !== "HERO") {
      errors.push(`${owner} snapshot ${stop.snapshot} must be that session's HERO`);
    }
  });

  return errors;
}

// ---------------------------------------------------------------------------
// Progressive reveal
// ---------------------------------------------------------------------------

export type RegionView = { id: string; name: string | null; frontier: boolean; state: RevealState; label: { x: number; y: number }; shape: string };
export type LandmarkView = {
  id: string;
  /** Present only once revealed: a hinted landmark ships no name. */
  name: string | null;
  hint: string | null;
  region: string;
  icon: string;
  x: number;
  y: number;
  state: RevealState;
  detail: string | null;
};
export type PathView = { id: string; kind: "trail" | "bearing"; from: string; to: string; d: string; state: RevealState };

export type StopView = {
  session: CalendarSession;
  kind: StopKind;
  landmark: { id: string; name: string };
  region: { id: string; name: string };
  /** The short stop name: "Compass Clearing", "Moonlit Ridge". */
  place: string;
  /** "Compass Clearing · Moon Meadow". */
  location: string;
  story: string;
  slidesHref: string | null;
  notesHref: string | null;
  hero: { alt: string; full: SnapshotImage; small: SnapshotImage };
};

export type JourneyState = {
  through: string;
  regions: RegionView[];
  landmarks: LandmarkView[];
  paths: PathView[];
  stops: StopView[];
  currentStop: StopView;
  /** The next calendar session, by public title and date only. */
  nextSession: CalendarSession | null;
  totalSessions: number;
};

function stepAt(steps: RevealStep[], through: number, order: Map<string, number>): RevealStep | null {
  let found: RevealStep | null = null;
  for (const step of steps) {
    if ((order.get(step.from) ?? Infinity) <= through) found = step;
  }
  return found;
}

export function sessionSlug(id: string): string {
  return id.toLowerCase();
}

function image({ src, width, height }: SnapshotImage): SnapshotImage {
  return { src, width, height };
}

function stopView(inputs: JourneyInputs, stop: JourneyStop): StopView {
  const { journey, sessions, published, notes, snapshots } = inputs;
  const session = sessions.find((item) => item.id === stop.session)!;
  const landmark = journey.landmarks.find((item) => item.id === stop.landmark)!;
  const region = journey.regions.find((item) => item.id === landmark.region)!;
  const regionName = region.name ?? "";
  const hero = snapshots.find((entry) => entry.moment === stop.snapshot)!;
  return {
    session,
    kind: stop.kind,
    landmark: { id: landmark.id, name: landmark.name },
    region: { id: region.id, name: regionName },
    place: stop.headline === "region" ? regionName : landmark.name,
    location: `${landmark.name} · ${regionName}`,
    story: stop.story,
    slidesHref: published.includes(session.id) ? `/students/slides/${sessionSlug(session.id)}/` : null,
    notesHref: notes.includes(session.id) ? `/students/learn/${sessionSlug(session.id)}/` : null,
    hero: { alt: stop.snapshotAlt, full: image(hero.images["960"]), small: image(hero.images["480"]) },
  };
}

/**
 * The map as it stands once the class has been taught every session up to and
 * including `through`. Hidden things are left out entirely, hinted landmarks
 * carry no name, and the current stop's landmark is marked `current`.
 */
export function journeyState(inputs: JourneyInputs, through: string): JourneyState {
  const { journey, sessions } = inputs;
  const order = new Map(sessions.map((session, index) => [session.id, index]));
  const limit = order.get(through);
  const stops = journey.stops.filter((stop) => (order.get(stop.session) ?? Infinity) <= (limit ?? -1));
  if (limit === undefined || stops.length === 0 || stops.at(-1)!.session !== through) {
    throw new Error(`No published Journey stop for ${through}`);
  }
  const current = stops.at(-1)!;

  const regions: RegionView[] = [];
  for (const region of journey.regions) {
    const step = stepAt(region.reveal, limit, order);
    if (!step) continue;
    regions.push({
      id: region.id,
      name: step.state === "revealed" ? (region.name ?? null) : null,
      frontier: Boolean(region.frontier),
      state: step.state,
      label: region.label,
      shape: region.shape,
    });
  }

  const landmarks: LandmarkView[] = [];
  for (const landmark of journey.landmarks) {
    const step = stepAt(landmark.reveal, limit, order);
    if (!step) continue;
    const revealed = step.state === "revealed";
    landmarks.push({
      id: landmark.id,
      name: revealed ? landmark.name : null,
      hint: revealed ? null : (landmark.hint ?? null),
      region: landmark.region,
      icon: landmark.icon,
      x: landmark.x,
      y: landmark.y,
      state: revealed && landmark.id === current.landmark ? "current" : step.state,
      detail: step.detail ?? null,
    });
  }

  const paths: PathView[] = [];
  for (const path of journey.paths) {
    const step = stepAt(path.reveal, limit, order);
    if (step) paths.push({ id: path.id, kind: path.kind, from: path.from, to: path.to, d: path.d, state: step.state });
  }

  const stopViews = stops.map((stop) => stopView(inputs, stop));
  return {
    through,
    regions,
    landmarks,
    paths,
    stops: stopViews,
    currentStop: stopViews.at(-1)!,
    nextSession: sessions[limit + 1] ?? null,
    totalSessions: sessions.length,
  };
}

/** The latest published session: the class Journey's current stop. */
export function currentSessionId(inputs: JourneyInputs): string {
  const last = inputs.published.at(-1);
  if (!last) throw new Error("No published session");
  return last;
}

/**
 * Compact "where we are" context for one session's Slides or Notes page, or
 * `null` when that session is unpublished and so has no Journey detail.
 */
export function journeyContextFor(inputs: JourneyInputs, sessionId: string): StopView | null {
  if (!inputs.published.includes(sessionId)) return null;
  const stop = inputs.journey.stops.find((item) => item.session === sessionId);
  return stop ? stopView(inputs, stop) : null;
}
