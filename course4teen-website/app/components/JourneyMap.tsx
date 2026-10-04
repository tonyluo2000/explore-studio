import { useId } from "react";
import type { JourneyState, LandmarkView, PathView, RegionView } from "../../lib/journey";

/**
 * The illustrated Course Journey map: a storybook night map of the frozen
 * Moon Meadow plate. Geometry comes from journey.json (plate positions, shifted
 * down to leave room for the ridge); this component only paints it. Icons are
 * simple SVG drawings in the plate's palette (lander, stone circle and Moon
 * Compass, Lantern Shrine, Moonlit Guide), not copies of the runtime art.
 *
 * The SVG is decorative to assistive technology beyond its title and summary:
 * the map key and the session list below it carry the same information as
 * text.
 */

type Props = { state: JourneyState; width: number; height: number; idPrefix?: string };

const STARS: readonly (readonly [number, number, number])[] = [
  [62, 34, 1.6], [148, 70, 1.1], [236, 28, 1.8], [318, 82, 1.2], [404, 40, 1.5], [452, 88, 1],
  [530, 22, 1.3], [612, 58, 1.9], [688, 30, 1.1], [742, 84, 1.4], [806, 26, 1.2], [36, 112, 1],
  [276, 126, 1.3], [566, 120, 1.1], [690, 132, 1.5], [850, 118, 1.2], [120, 150, 1], [940, 148, 1.3],
];

// Plate crystal clusters (x, ground y, scale, violet?) shifted by the map offset.
const CRYSTALS: readonly (readonly [number, number, number, boolean])[] = [
  [858, 496, 1.2, false], [602, 266, 0.75, true], [36, 492, 0.95, true],
  [398, 272, 0.6, false], [752, 306, 0.85, false], [318, 660, 0.8, true],
];

const RIDGE_TREES: readonly (readonly [number, number, number])[] = [
  [60, 214, 15], [104, 206, 12], [236, 210, 13], [318, 190, 16], [356, 186, 11], [470, 200, 12],
  [520, 198, 15], [600, 186, 12], [700, 172, 14], [744, 176, 11], [868, 192, 13], [920, 190, 16],
];

const FLOWERS: readonly (readonly [number, number])[] = [
  [712, 368], [728, 376], [744, 364], [598, 470], [612, 478], [462, 520], [478, 514], [520, 300],
  [800, 640], [816, 632], [210, 660], [226, 652], [380, 600], [880, 380], [896, 372],
];

/** How far above a landmark's anchor its current-stop gem floats, and its label sits below. */
const ICON_LAYOUT: Record<string, { gem: number; label: number }> = {
  lander: { gem: 58, label: 72 },
  compass: { gem: 78, label: 84 },
  lantern: { gem: 150, label: 72 },
  guide: { gem: 82, label: 62 },
};

function layout(icon: string) {
  return ICON_LAYOUT[icon] ?? { gem: 60, label: 60 };
}

function Region({ region, ids }: { region: RegionView; ids: Ids }) {
  if (region.frontier) {
    return (
      <g className="jm-frontier">
        <path d={region.shape} className="jm-land-fogged" />
        <g className="jm-mist jm-drift" filter={`url(#${ids.blur})`}>
          <ellipse cx={180} cy={150} rx={220} ry={40} />
          <ellipse cx={520} cy={130} rx={260} ry={46} />
          <ellipse cx={850} cy={150} rx={210} ry={38} />
        </g>
        <text x={region.label.x} y={region.label.y} className="jm-fog-label" textAnchor="middle">
          uncharted
        </text>
      </g>
    );
  }
  if (region.id === "moonlit-ridge") {
    const revealed = region.state === "revealed";
    return (
      <g className={revealed ? "jm-ridge" : "jm-ridge jm-ridge-fogged"}>
        <path d={region.shape} className={revealed ? "jm-ridge-land" : "jm-land-fogged"} />
        {revealed
          ? RIDGE_TREES.map(([x, y, r]) => (
              <g key={`${x}-${y}`} className="jm-tree">
                <rect x={x - 1.5} y={y} width={3} height={r * 0.9} />
                <circle cx={x} cy={y - r * 0.2} r={r} />
              </g>
            ))
          : (
              <g className="jm-mist" filter={`url(#${ids.blur})`}>
                <ellipse cx={240} cy={214} rx={240} ry={26} />
                <ellipse cx={720} cy={196} rx={260} ry={28} />
              </g>
            )}
        {revealed && region.name ? (
          <text x={region.label.x} y={region.label.y} className="jm-region-label" textAnchor="middle">
            {region.name}
          </text>
        ) : null}
      </g>
    );
  }
  return (
    <g className="jm-meadow">
      <path d={region.shape} fill={`url(#${ids.meadow})`} />
      <ellipse cx={82} cy={360} rx={62} ry={22} className="jm-pond" />
      <ellipse cx={100} cy={360} rx={8} ry={14} className="jm-pond-moon" />
      {CRYSTALS.map(([x, y, s, violet]) => (
        <path
          key={`${x}-${y}`}
          className={violet ? "jm-crystal jm-crystal-violet" : "jm-crystal"}
          d={`M${x - 10 * s} ${y}L${x - 6 * s} ${y - 20 * s}L${x} ${y - 34 * s}L${x + 6 * s} ${y - 22 * s}L${x + 11 * s} ${y}Z`}
        />
      ))}
      {FLOWERS.map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r={2.4} className="jm-flower" />
      ))}
      <g className="jm-tree jm-tree-big">
        <rect x={16} y={262} width={6} height={42} />
        <circle cx={20} cy={248} r={34} />
        <rect x={924} y={320} width={6} height={48} />
        <circle cx={926} cy={300} r={42} />
      </g>
      {region.name ? (
        <text x={region.label.x} y={region.label.y} className="jm-region-label" textAnchor="middle">
          {region.name}
        </text>
      ) : null}
    </g>
  );
}

function Path({ path, soft }: { path: PathView; soft: string }) {
  if (path.kind === "trail") {
    return (
      <g className="jm-trail">
        <path d={path.d} className="jm-trail-bed" />
        <path d={path.d} className="jm-trail-stones" />
      </g>
    );
  }
  return (
    <g className={path.state === "hinted" ? "jm-bearing jm-bearing-hinted" : "jm-bearing"}>
      <path d={path.d} className="jm-bearing-glow" filter={soft} />
      <path d={path.d} className="jm-bearing-dots" />
    </g>
  );
}

function Lander({ x, y }: { x: number; y: number }) {
  // The landing pad, with the parked lander east of it as on the plate.
  const lights = Array.from({ length: 12 }, (_, index) => {
    const angle = (index * Math.PI * 2) / 12;
    return [x + 104 * Math.cos(angle), y + 2 + 36 * Math.sin(angle)] as const;
  });
  const lx = x + 160;
  const ly = y - 12;
  return (
    <g className="jm-lander">
      <ellipse cx={x} cy={y} rx={104} ry={36} className="jm-pad" />
      <ellipse cx={x} cy={y} rx={70} ry={22} className="jm-pad-ring" />
      <path d={`M${x} ${y - 13}l4 9 10 1-8 6 3 10-9-6-9 6 3-10-8-6 10-1Z`} className="jm-pad-star" />
      {lights.map(([px, py]) => (
        <circle key={`${px.toFixed(1)}-${py.toFixed(1)}`} cx={px} cy={py} r={3} className="jm-pad-light" />
      ))}
      <path d={`M${lx - 22} ${ly + 22}l-12 18M${lx + 22} ${ly + 22}l12 18`} className="jm-lander-leg" />
      <path d={`M${lx - 24} ${ly + 8}l-14 20h16ZM${lx + 24} ${ly + 8}l14 20h-16Z`} className="jm-lander-fin" />
      <ellipse cx={lx} cy={ly} rx={26} ry={34} className="jm-lander-body" />
      <circle cx={lx} cy={ly - 6} r={11} className="jm-lander-port" />
      <path d={`M${lx} ${ly - 34}v-14`} className="jm-lander-leg" />
      <circle cx={lx} cy={ly - 50} r={4} className="jm-lander-beacon" />
    </g>
  );
}

function StoneCircle({ landmark, soft }: { landmark: LandmarkView; soft: string }) {
  const { x, y } = landmark;
  const hinted = landmark.state === "hinted";
  const awakened = landmark.detail === "awakened";
  const stones = Array.from({ length: 9 }, (_, index) => {
    const angle = Math.PI * 0.95 + (index * Math.PI * 1.1) / 8;
    return [x + 96 * Math.cos(angle), y + 50 * Math.sin(angle)] as const;
  });
  return (
    <g className={hinted ? "jm-clearing jm-hinted" : "jm-clearing"}>
      <ellipse cx={x} cy={y} rx={110} ry={62} className={awakened ? "jm-pool-violet jm-pool-strong" : "jm-pool-violet"} filter={soft} />
      <ellipse cx={x} cy={y} rx={70} ry={26} className="jm-clearing-floor" />
      {stones.map(([sx, sy]) => (
        <rect key={`${sx.toFixed(1)}`} x={sx - 7} y={sy - 30} width={14} height={30} rx={6} className="jm-stone" />
      ))}
      {hinted ? null : (
        <g className="jm-compass">
          <circle cx={x} cy={y - 6} r={20} className="jm-compass-ring" />
          <circle cx={x} cy={y - 6} r={15} className="jm-compass-body" />
          <circle cx={x} cy={y - 6} r={10} className="jm-compass-face" />
          {/* Awakened: the needle swings east, toward the ridge and the guide. */}
          <g transform={`rotate(${awakened ? 82 : 0} ${x} ${y - 6})`}>
            <path d={`M${x} ${y - 16}l3.5 10h-7Z`} className="jm-needle-north" />
            <path d={`M${x} ${y + 4}l3.5-10h-7Z`} className="jm-needle-south" />
          </g>
          {awakened
            ? [[-26, -30], [28, -26], [-30, 6], [32, 10], [0, -40]].map(([dx, dy]) => (
                <path
                  key={`${dx}-${dy}`}
                  d={`M${x + dx} ${y + dy - 5}l1.6 3.4 3.4 1.6-3.4 1.6-1.6 3.4-1.6-3.4-3.4-1.6 3.4-1.6Z`}
                  className="jm-sparkle"
                />
              ))
            : null}
        </g>
      )}
    </g>
  );
}

function Shrine({ x, y, soft }: { x: number; y: number; soft: string }) {
  return (
    <g className="jm-shrine">
      <ellipse cx={x} cy={y} rx={120} ry={60} className="jm-pool-warm" filter={soft} />
      <ellipse cx={x} cy={y + 8} rx={82} ry={28} className="jm-shrine-floor" />
      <rect x={x - 66} y={y - 112} width={16} height={116} rx={3} className="jm-shrine-pillar" />
      <rect x={x + 50} y={y - 112} width={16} height={116} rx={3} className="jm-shrine-pillar" />
      <rect x={x - 82} y={y - 124} width={164} height={16} rx={4} className="jm-shrine-lintel" />
      <path d={`M${x - 74} ${y - 124}q4-14 0-22q8 8 4 22ZM${x + 74} ${y - 124}q4-14 0-22q8 8 4 22Z`} className="jm-flame" />
      <circle cx={x} cy={y - 116} r={6} className="jm-shrine-orb" />
      <rect x={x - 9} y={y - 26} width={18} height={24} rx={3} className="jm-lantern" />
      <path d={`M${x - 11} ${y - 26}h22l-4-6h-14Z`} className="jm-lantern-cap" />
    </g>
  );
}

function Guide({ landmark, soft }: { landmark: LandmarkView; soft: string }) {
  const { x, y } = landmark;
  if (landmark.state === "hinted") {
    return (
      <g className="jm-guide jm-hinted">
        <circle cx={x} cy={y - 26} r={46} className="jm-pool-blue" filter={soft} />
        <path d={`M${x - 14} ${y}L${x} ${y - 46}L${x + 14} ${y}Z`} className="jm-guide-silhouette" />
        <circle cx={x + 20} cy={y - 50} r={5} className="jm-guide-glint" />
      </g>
    );
  }
  return (
    <g className="jm-guide">
      <circle cx={x} cy={y - 26} r={52} className="jm-pool-blue" filter={soft} />
      <path d={`M${x + 20} ${y + 2}V${y - 46}`} className="jm-guide-staff" />
      <path d={`M${x + 26} ${y - 58}a8 8 0 1 1-10-4a6 6 0 1 0 10 4Z`} className="jm-guide-moon" />
      <path d={`M${x - 18} ${y + 2}Q${x - 14} ${y - 30} ${x} ${y - 52}Q${x + 14} ${y - 30} ${x + 18} ${y + 2}Z`} className="jm-guide-robe" />
      <circle cx={x} cy={y - 30} r={6} className="jm-guide-face" />
      <path d={`M${x - 6} ${y - 27}q6 16 12 0Z`} className="jm-guide-beard" />
    </g>
  );
}

function Landmark({ landmark, number, soft }: { landmark: LandmarkView; number: number; soft: string }) {
  const { x, y } = landmark;
  const place = layout(landmark.icon);
  const icon =
    landmark.icon === "lander" ? <Lander x={x} y={y} />
    : landmark.icon === "compass" ? <StoneCircle landmark={landmark} soft={soft} />
    : landmark.icon === "lantern" ? <Shrine x={x} y={y} soft={soft} />
    : <Guide landmark={landmark} soft={soft} />;
  return (
    <g className={`jm-landmark jm-state-${landmark.state}`}>
      {icon}
      {landmark.name ? (
        <text x={x} y={y + place.label} className="jm-label" textAnchor="middle">
          {landmark.name}
        </text>
      ) : null}
      <g className="jm-badge">
        <circle cx={x} cy={y + place.label - 12} r={34} />
        <text x={x} y={y + place.label + 2} textAnchor="middle">
          {landmark.name ? number : "?"}
        </text>
      </g>
    </g>
  );
}

function CurrentGem({ landmark, soft }: { landmark: LandmarkView; soft: string }) {
  // The Trail's waypoint gem: a gold kite pointing down at the current stop.
  const cx = landmark.x;
  const tip = landmark.y - layout(landmark.icon).gem;
  const top = tip - 34;
  const mid = tip - 22;
  return (
    <g className="jm-gem">
      <circle cx={cx} cy={mid} r={24} className="jm-gem-glow" filter={soft} />
      <path d={`M${cx} ${top}L${cx + 12} ${mid}L${cx} ${tip}L${cx - 12} ${mid}Z`} className="jm-gem-body" />
      <path d={`M${cx} ${top + 3}L${cx + 9} ${mid}H${cx}Z`} className="jm-gem-light" />
      <path d={`M${cx} ${mid}H${cx - 9}L${cx} ${tip - 4}Z`} className="jm-gem-shade" />
    </g>
  );
}

export function landmarkNumbers(state: JourneyState): Map<string, number> {
  return new Map(state.landmarks.map((landmark, index) => [landmark.id, index + 1]));
}

type Ids = Record<"title" | "desc" | "sky" | "meadow" | "vignette" | "blur" | "soft" | "frame", string>;

/** Keep an id to characters that are safe in `url(#...)` and `aria-labelledby`. */
function safeId(value: string): string {
  return value.replace(/[^A-Za-z0-9_-]/g, "");
}

export default function JourneyMap({ state, width, height, idPrefix }: Props) {
  // Every gradient, filter, clip, title, and desc id is scoped to this
  // instance, so two maps in one document never resolve each other's paint.
  // useId runs during the server render (no client JS) and is deterministic
  // for a given tree, so the static export does not drift between builds.
  const instanceId = useId();
  const prefix = idPrefix ? safeId(idPrefix) : `jm-${safeId(instanceId)}`;
  const ids = Object.fromEntries(
    ["title", "desc", "sky", "meadow", "vignette", "blur", "soft", "frame"].map((key) => [key, `${prefix}-${key}`]),
  ) as Ids;
  const numbers = landmarkNumbers(state);
  const current = state.landmarks.find((landmark) => landmark.state === "current");
  const regionOrder = ["frontier", "moonlit-ridge", "moon-meadow"];
  const regions = [...state.regions].sort(
    (a, b) => regionOrder.indexOf(a.frontier ? "frontier" : a.id) - regionOrder.indexOf(b.frontier ? "frontier" : b.id),
  );
  const named = state.landmarks.filter((landmark) => landmark.name).map((landmark) => landmark.name);
  const summary = `Illustrated map of the class Journey through ${state.through}. Revealed: ${named.join(", ")}. Current stop: ${state.currentStop.place}.`;

  return (
    <svg
      className="jm-svg"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-labelledby={`${ids.title} ${ids.desc}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <title id={ids.title}>Course Journey map</title>
      <desc id={ids.desc}>{summary}</desc>
      <defs>
        <linearGradient id={ids.sky} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0b1030" />
          <stop offset=".45" stopColor="#1a1f4a" />
          <stop offset="1" stopColor="#262a5c" />
        </linearGradient>
        <linearGradient id={ids.meadow} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1f4a49" />
          <stop offset=".5" stopColor="#1a3d3c" />
          <stop offset="1" stopColor="#12292d" />
        </linearGradient>
        <radialGradient id={ids.vignette} cx=".5" cy=".55" r=".75">
          <stop offset=".6" stopColor="#060a1c" stopOpacity="0" />
          <stop offset="1" stopColor="#060a1c" stopOpacity=".7" />
        </radialGradient>
        <filter id={ids.blur} x="-20%" y="-50%" width="140%" height="200%">
          <feGaussianBlur stdDeviation="14" />
        </filter>
        <filter id={ids.soft} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" />
        </filter>
        <clipPath id={ids.frame}>
          <rect x={0} y={0} width={width} height={height} rx={28} />
        </clipPath>
      </defs>
      <g clipPath={`url(#${ids.frame})`}>
        <rect width={width} height={height} fill={`url(#${ids.sky})`} />
        {STARS.map(([x, y, r]) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={r} className="jm-star" />
        ))}
        <circle cx={892} cy={60} r={36} className="jm-moon" />
        <circle cx={880} cy={52} r={7} className="jm-moon-crater" />
        <circle cx={902} cy={72} r={5} className="jm-moon-crater" />
        {regions.map((region) => (
          <Region key={region.id} region={region} ids={ids} />
        ))}
        {state.paths.map((path) => (
          <Path key={path.id} path={path} soft={`url(#${ids.soft})`} />
        ))}
        {state.landmarks.map((landmark) => (
          <Landmark key={landmark.id} landmark={landmark} number={numbers.get(landmark.id) ?? 0} soft={`url(#${ids.soft})`} />
        ))}
        {current ? <CurrentGem landmark={current} soft={`url(#${ids.soft})`} /> : null}
        <rect width={width} height={height} fill={`url(#${ids.vignette})`} pointerEvents="none" />
      </g>
      <rect x={6} y={6} width={width - 12} height={height - 12} rx={24} className="jm-border" />
      <rect x={16} y={16} width={width - 32} height={height - 32} rx={18} className="jm-border-inner" />
    </svg>
  );
}
