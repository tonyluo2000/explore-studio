/**
 * Map of the S02 Trail screen: where Nova, Pixel, the Moon Compass, and the
 * Crystal Lantern really are when M02 launches.
 *
 * Boxes use the Trail's real 960 × 640 window, positions, sizes, and named
 * colors (characters are 100 × 100, world objects 80 × 60). In the Trail, the
 * four named S02 entities appear as simple pictures and no names are drawn. The
 * small symbols and labels are map-only; an entity without a known picture
 * still uses the plain colored-box fallback. Hand-authored for this project;
 * no third-party artwork.
 * The Course Kit copy is `lessons/sessions/s02/student/trail-map.svg`.
 */

type MapItem = {
  id: string;
  x: number;
  y: number;
  size: [number, number];
  color: string;
  fill: string;
  label: string;
  note: string;
  labelAt: [number, number];
  xy: string;
  step?: string;
  yours?: boolean;
  /** Dark plate behind the label where the route line passes under it. */
  plate?: [number, number, number, number];
};

// Draw order matches the Trail: world objects, then Pixel, then the player.
const items: MapItem[] = [
  {
    id: "crystal-lantern",
    x: 120,
    y: 460,
    size: [80, 60],
    color: "yellow",
    fill: "rgb(240, 210, 50)",
    label: "Crystal Lantern · the destination",
    note: "Already in the world. End your trail here.",
    labelAt: [250, 478],
    xy: "(120, 460)",
    step: "2",
  },
  {
    id: "moon-compass",
    x: 240,
    y: 180,
    size: [80, 60],
    color: "purple",
    fill: "rgb(140, 50, 180)",
    label: "Moon Compass · YOU place it",
    note: "Your tool. You choose x, y, and color.",
    labelAt: [30, 290],
    xy: "(240, 180) → your x and y",
    step: "1",
    yours: true,
    plate: [20, 266, 332, 88],
  },
  {
    id: "pixel",
    x: 480,
    y: 310,
    size: [100, 100],
    color: "blue",
    fill: "rgb(50, 80, 220)",
    label: "Pixel · class example",
    note: "Says hello when you press E.",
    labelAt: [600, 382],
    xy: "(480, 310)",
  },
  {
    id: "nova",
    x: 430,
    y: 270,
    size: [100, 100],
    color: "gold",
    fill: "rgb(255, 200, 50)",
    label: "Nova · you walk as Nova",
    note: "Start here. Arrow keys move.",
    labelAt: [600, 262],
    xy: "(430, 270)",
  },
];

const gridX = [160, 320, 480, 640, 800];
const gridY = [160, 320, 480];

function Glyph({ id }: { id: string }) {
  switch (id) {
    case "crystal-lantern":
      return (
        <path d="M160 468 L172 490 L160 512 L148 490 Z" fill="#fff4d6" stroke="#122131" strokeWidth="3" />
      );
    case "moon-compass":
      return (
        <>
          <circle cx="280" cy="210" r="21" fill="#efe6ff" stroke="#122131" strokeWidth="3" />
          <path d="M280 193 L286 210 L280 227 L274 210 Z" fill="#b04b2b" />
        </>
      );
    case "pixel":
      return (
        <>
          <line x1="560" y1="388" x2="560" y2="372" stroke="#122131" strokeWidth="3" />
          <circle cx="560" cy="368" r="5" fill="#ff8f66" />
        </>
      );
    default:
      return (
        <>
          <circle cx="480" cy="306" r="14" fill="#122131" opacity="0.8" />
          <path d="M458 350 Q480 328 502 350 Z" fill="#122131" opacity="0.8" />
        </>
      );
  }
}

export default function S02TrailMap() {
  return (
    <figure className="scene-figure trail-map-figure">
      <div className="trail-map-scroll">
        <svg
          className="trail-map-art"
          viewBox="-80 -70 1120 750"
          role="img"
          aria-labelledby="s02-trail-map-title"
        >
          <title id="s02-trail-map-title">
            Map of the S02 Trail screen. Nova, the class example explorer, starts
            at (430, 270) with Pixel, the class example companion, at (480, 310).
            Step 1: walk to the Moon Compass at (240, 180), the tool you place
            with x and y. Step 2: walk to the Crystal Lantern at (120, 460), the
            destination in the bottom-left corner. Visiting both completes the
            mission.
          </title>
          <rect x="0" y="0" width="960" height="640" fill="#202030" />
          {gridX.map((x) => (
            <g key={`x${x}`}>
              <line x1={x} y1="0" x2={x} y2="640" className="tm-grid" />
              <text x={x} y="-18" textAnchor="middle" className="tm-tick">
                {x}
              </text>
            </g>
          ))}
          {gridY.map((y) => (
            <g key={`y${y}`}>
              <line x1="0" y1={y} x2="960" y2={y} className="tm-grid" />
              <text x="-14" y={y + 7} textAnchor="end" className="tm-tick">
                {y}
              </text>
            </g>
          ))}
          <text x="0" y="-18" textAnchor="middle" className="tm-tick">0</text>
          <text x="960" y="-18" textAnchor="middle" className="tm-tick">960</text>
          <text x="-14" y="647" textAnchor="end" className="tm-tick">640</text>
          <text x="990" y="-16" className="tm-axis">x →</text>
          <text x="-14" y="690" textAnchor="end" className="tm-axis">y ↓</text>

          <text x="20" y="40" className="tm-hud">Visited 0 / 2</text>
          <text x="20" y="75" className="tm-hud">Mission: Create Your First Object</text>
          <text x="20" y="130" className="tm-zone">Mission words stay up here.</text>
          <text x="360" y="620" className="tm-zone">
            Messages appear here, like “Press E to explore”.
          </text>

          <path className="tm-route" d="M 480 300 C 420 240 360 220 320 212" />
          <path className="tm-route" d="M 262 240 C 250 330 200 390 170 458" />
          <circle cx="160" cy="490" r="78" className="tm-destination" />

          {items.map((item) => (
            <g key={item.id} data-id={item.id} data-x={item.x} data-y={item.y} data-color={item.color}>
              <rect
                x={item.x}
                y={item.y}
                width={item.size[0]}
                height={item.size[1]}
                fill={item.fill}
                className={item.yours ? "tm-yours" : undefined}
              />
              <Glyph id={item.id} />
              {item.step ? (
                <>
                  <circle cx={item.x - 20} cy={item.y - 8} r="18" className="tm-step-dot" />
                  <text x={item.x - 20} y={item.y + 1} textAnchor="middle" className="tm-step">
                    {item.step}
                  </text>
                </>
              ) : null}
              {item.plate ? (
                <rect
                  x={item.plate[0]}
                  y={item.plate[1]}
                  width={item.plate[2]}
                  height={item.plate[3]}
                  rx="8"
                  className="tm-plate"
                />
              ) : null}
              <text x={item.labelAt[0]} y={item.labelAt[1]} className="tm-label">
                {item.label}
              </text>
              <text x={item.labelAt[0]} y={item.labelAt[1] + 28} className="tm-note">
                {item.note}
              </text>
              <text x={item.labelAt[0]} y={item.labelAt[1] + 54} className="tm-xy">
                {item.xy}
              </text>
            </g>
          ))}
        </svg>
      </div>
      <figcaption>
        Your trail today: walk from Nova to your <strong>Moon Compass</strong>{" "}
        (1), then to the <strong>Crystal Lantern</strong> (2). Visiting both, in
        any order, completes the mission. In the Trail, Nova, Pixel, the Moon
        Compass, and Crystal Lantern appear as simple pictures. Names are not
        drawn on screen; the labels and symbols are map-only. A thing without a
        known picture still appears as a plain colored box.
      </figcaption>
    </figure>
  );
}
