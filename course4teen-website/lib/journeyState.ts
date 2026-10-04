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

const ALLOWED_KEYS: Record<string, readonly string[]> = {
  root: ["schema", "note", "map", "regions", "landmarks", "paths", "frontier", "stops"],
  region: ["id", "name", "frontier", "label", "shape", "reveal"],
  landmark: ["id", "name", "hint", "region", "icon", "x", "y", "reveal"],
  path: ["id", "kind", "from", "to", "d", "reveal"],
  stop: ["session", "kind", "landmark", "headline", "story", "snapshot", "snapshotAlt"],
  step: ["from", "state", "detail"],
};

function extraKeys(value: object, kind: string): string[] {
  return Object.keys(value).filter((key) => !ALLOWED_KEYS[kind].includes(key));
}

/**
 * Every reason the Journey data disagrees with the calendar, the publication
 * state, or the snapshot manifest. An empty list means the data is valid.
 */
export function validateJourney(inputs: JourneyInputs): string[] {
  const { journey, sessions, published, snapshots } = inputs;
  const errors: string[] = [];
  const order = new Map(sessions.map((session, index) => [session.id, index]));

  if (journey.schema !== JOURNEY_SCHEMA) errors.push(`schema must be ${JOURNEY_SCHEMA}`);
  for (const key of extraKeys(journey, "root")) errors.push(`unknown top-level key ${key}`);

  // Publication: the published sessions are S01..Sn in course order.
  published.forEach((id, index) => {
    if (sessions[index]?.id !== id) errors.push(`published sessions must run S01 onward in order; found ${id}`);
  });

  // Exactly one stop per published session, and nothing for unpublished ones.
  const stopIds = journey.stops.map((stop) => stop.session);
  if (stopIds.join() !== published.join()) {
    errors.push(`stops ${stopIds.join(",")} must be exactly the published sessions ${published.join(",")}`);
  }
  const stopSessions = new Set(stopIds);

  const regionIds = new Set(journey.regions.map((region) => region.id));
  const landmarkIds = new Set(journey.landmarks.map((landmark) => landmark.id));
  const ids = [...journey.regions, ...journey.landmarks, ...journey.paths].map((item) => item.id);
  for (const id of ids.filter((id, index) => ids.indexOf(id) !== index)) errors.push(`duplicate id ${id}`);

  const checkSteps = (owner: string, steps: RevealStep[], allowed: Set<string>, mustReveal: boolean) => {
    if (steps.length === 0) errors.push(`${owner} has no reveal steps`);
    let previousIndex = -1;
    let previousRank = 0;
    for (const step of steps) {
      for (const key of extraKeys(step, "step")) errors.push(`${owner} reveal step has unknown key ${key}`);
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

  const frontiers = journey.regions.filter((region) => region.frontier);
  if (frontiers.length > 1) errors.push("only one generic fog frontier is allowed");
  for (const region of journey.regions) {
    for (const key of extraKeys(region, "region")) errors.push(`region ${region.id} has unknown key ${key}`);
    if (region.frontier) {
      if (region.name) errors.push(`frontier ${region.id} must stay unnamed`);
      if (region.reveal.some((step) => step.state !== "fogged")) {
        errors.push(`frontier ${region.id} may only ever be fogged`);
      }
      checkSteps(`region ${region.id}`, region.reveal, REGION_STATES, false);
    } else {
      if (!region.name) errors.push(`region ${region.id} needs a name`);
      checkSteps(`region ${region.id}`, region.reveal, REGION_STATES, true);
    }
  }
  for (const landmark of journey.landmarks) {
    for (const key of extraKeys(landmark, "landmark")) errors.push(`landmark ${landmark.id} has unknown key ${key}`);
    if (!regionIds.has(landmark.region)) errors.push(`landmark ${landmark.id} names unknown region ${landmark.region}`);
    if (landmark.reveal.some((step) => step.state === "hinted") && !landmark.hint) {
      errors.push(`landmark ${landmark.id} is hinted but has no unnamed hint text`);
    }
    checkSteps(`landmark ${landmark.id}`, landmark.reveal, LANDMARK_STATES, true);
  }
  for (const path of journey.paths) {
    for (const key of extraKeys(path, "path")) errors.push(`path ${path.id} has unknown key ${key}`);
    for (const end of [path.from, path.to]) {
      if (!landmarkIds.has(end)) errors.push(`path ${path.id} names unknown landmark ${end}`);
    }
    checkSteps(`path ${path.id}`, path.reveal, PATH_STATES, true);
  }

  journey.stops.forEach((stop, index) => {
    const owner = `stop ${stop.session}`;
    for (const key of extraKeys(stop, "stop")) errors.push(`${owner} has unknown key ${key}`);
    if (stop.story.length > STORY_MAX_CHARS) errors.push(`${owner} story is over ${STORY_MAX_CHARS} characters`);
    const landmark = journey.landmarks.find((item) => item.id === stop.landmark);
    if (!landmark) {
      errors.push(`${owner} names unknown landmark ${stop.landmark}`);
      return;
    }
    const stepAt = landmark.reveal.find((step) => step.from === stop.session);
    const before = landmark.reveal.filter((step) => (order.get(step.from) ?? 0) < (order.get(stop.session) ?? 0));
    if (stop.kind === "arrive" && index !== 0) errors.push(`${owner} can only arrive at the first stop`);
    if ((stop.kind === "arrive" || stop.kind === "reveal") && stepAt?.state !== "revealed") {
      errors.push(`${owner} must reveal ${landmark.id} in that session`);
    }
    if (stop.kind === "deepen" && (before.at(-1)?.state !== "revealed" || !stepAt?.detail)) {
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
export type PathView = { id: string; kind: "trail" | "bearing"; d: string; state: RevealState };

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
    if (step) paths.push({ id: path.id, kind: path.kind, d: path.d, state: step.state });
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
