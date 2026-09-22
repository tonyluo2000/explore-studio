/**
 * The Trail screen's coordinate system with the Moon Compass at (240, 180).
 *
 * Drawn to the Trail window's real 960 × 640 size: x grows to the right and
 * y grows downward from the top-left corner, as in pygame.
 */
const gridX = [0, 160, 320, 480, 640, 800, 960];
const gridY = [0, 160, 320, 480, 640];

export default function CoordinateMap() {
  return (
    <figure className="scene-figure coord-figure">
      <svg
        className="coord-art"
        viewBox="-100 -90 1170 800"
        role="img"
        aria-labelledby="coord-map-title"
      >
        <title id="coord-map-title">
          The Trail screen is 960 wide and 640 tall. The corner (0, 0) is at
          the top left. x grows to the right and y grows downward. The Moon
          Compass sits at x 240, y 180.
        </title>
        <rect x="0" y="0" width="960" height="640" rx="10" className="coord-screen" />
        {gridX.map((x) => (
          <g key={`x${x}`}>
            <line x1={x} y1="0" x2={x} y2="640" className="coord-grid" />
            <text x={x} y="-22" textAnchor="middle" className="coord-tick">
              {x}
            </text>
          </g>
        ))}
        {gridY.map((y) => (
          <g key={`y${y}`}>
            <line x1="0" y1={y} x2="960" y2={y} className="coord-grid" />
            <text x="-18" y={y + 9} textAnchor="end" className="coord-tick">
              {y}
            </text>
          </g>
        ))}
        <text x="1012" y="-22" className="coord-axis">x →</text>
        <text x="-18" y="690" textAnchor="end" className="coord-axis">y ↓</text>

        <line x1="240" y1="0" x2="240" y2="180" className="coord-guide" />
        <line x1="0" y1="180" x2="240" y2="180" className="coord-guide" />

        <g transform="translate(240 180)">
          <circle r="46" className="coord-compass-glow" />
          <circle r="30" className="coord-compass" />
          <circle r="21" className="coord-compass-face" />
          <path d="M0 -17 L6 0 L0 17 L-6 0 Z" className="coord-needle" />
          <circle r="3" className="coord-pin" />
        </g>
        <text x="296" y="172" className="coord-label">Moon Compass</text>
        <text x="296" y="210" className="coord-value">(240, 180)</text>

        <circle cx="0" cy="0" r="8" className="coord-origin" />
        <text x="16" y="36" className="coord-value">(0, 0)</text>
      </svg>
      <figcaption>
        The Trail screen: <code>x</code> grows to the right, <code>y</code>{" "}
        grows <strong>down</strong> from the top-left corner.
      </figcaption>
    </figure>
  );
}
