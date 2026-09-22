/**
 * Original illustration of Nova (explorer) and Pixel (companion) at dusk.
 *
 * Hand-authored SVG made for this project; no third-party artwork. It is a
 * reference illustration for slides, not a picture of the Trail runtime.
 */
export default function NovaPixelScene({ caption }: { caption?: string }) {
  return (
    <figure className="scene-figure">
      <svg
        className="scene-art"
        viewBox="0 0 640 360"
        role="img"
        aria-labelledby="nova-pixel-title"
      >
        <title id="nova-pixel-title">
          Nova, a young explorer with a coral coat and a backpack, points toward
          distant mountains at dusk. Pixel, a small round mint-green robot with
          one bright eye and a glowing antenna, hovers beside Nova. A crystal
          lantern glows beside the path.
        </title>
        <defs>
          <linearGradient id="np-sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#15223a" />
            <stop offset="0.55" stopColor="#3b3f6b" />
            <stop offset="0.85" stopColor="#c9786a" />
            <stop offset="1" stopColor="#f2a57e" />
          </linearGradient>
          <radialGradient id="np-moon-glow">
            <stop offset="0" stopColor="#fff4d6" stopOpacity="0.55" />
            <stop offset="1" stopColor="#fff4d6" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="np-lantern-glow">
            <stop offset="0" stopColor="#ffe28a" stopOpacity="0.8" />
            <stop offset="1" stopColor="#ffe28a" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="np-path" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stopColor="#efdcb6" />
            <stop offset="1" stopColor="#c9a98a" stopOpacity="0.4" />
          </linearGradient>
        </defs>

        <rect width="640" height="360" fill="url(#np-sky)" />

        <g fill="#fff8e7">
          <circle cx="60" cy="40" r="1.6" />
          <circle cx="140" cy="78" r="1.1" />
          <circle cx="210" cy="30" r="1.4" />
          <circle cx="300" cy="62" r="1" />
          <circle cx="380" cy="24" r="1.5" />
          <circle cx="455" cy="88" r="1.1" />
          <circle cx="600" cy="44" r="1.3" />
          <circle cx="560" cy="110" r="0.9" />
          <circle cx="30" cy="120" r="1" />
        </g>

        <circle cx="505" cy="70" r="60" fill="url(#np-moon-glow)" />
        <circle cx="505" cy="70" r="24" fill="#fff4d6" />
        <circle cx="496" cy="64" r="4" fill="#efe1bd" />
        <circle cx="512" cy="78" r="2.6" fill="#efe1bd" />

        <path
          d="M0 230 L70 170 L120 205 L190 140 L260 200 L320 160 L390 210 L470 150 L550 205 L640 170 L640 360 L0 360 Z"
          fill="#2f3a5c"
        />
        <path
          d="M0 262 C90 232 170 250 250 236 C340 220 420 246 500 232 C560 222 610 236 640 230 L640 360 L0 360 Z"
          fill="#2b5a57"
        />
        <path
          d="M0 300 C120 280 220 296 330 288 C450 280 540 298 640 290 L640 360 L0 360 Z"
          fill="#1d3b3b"
        />
        <path d="M250 360 C300 320 340 300 372 262 C380 252 390 246 400 242 L408 246 C396 256 386 268 380 280 C366 310 350 334 360 360 Z" fill="url(#np-path)" />

        <g>
          <circle cx="132" cy="262" r="42" fill="url(#np-lantern-glow)" />
          <rect x="130" y="266" width="4" height="40" rx="2" fill="#122131" />
          <path d="M132 244 L142 258 L132 274 L122 258 Z" fill="#ffe28a" stroke="#fff4d6" strokeWidth="1.5" />
        </g>

        <g transform="translate(334 316) scale(1.3) translate(-334 -316)">
          <g>
            <ellipse cx="300" cy="316" rx="28" ry="5" fill="#0d1d22" opacity="0.5" />
            <rect x="274" y="226" width="16" height="36" rx="5" fill="#8e3b22" />
            <rect x="290" y="270" width="8" height="40" rx="3" fill="#122131" />
            <rect x="303" y="270" width="8" height="40" rx="3" fill="#122131" />
            <rect x="286" y="304" width="14" height="8" rx="3" fill="#3a2a22" />
            <rect x="302" y="304" width="14" height="8" rx="3" fill="#3a2a22" />
            <path d="M286 222 L316 222 L322 280 L280 280 Z" fill="#ff8f66" />
            <rect x="298" y="232" width="4" height="40" fill="#e66f48" opacity="0.6" />
            <path d="M316 232 L340 208" stroke="#ff8f66" strokeWidth="8" strokeLinecap="round" />
            <circle cx="341" cy="207" r="4.5" fill="#f1c7a3" />
            <rect x="286" y="214" width="30" height="9" rx="4" fill="#8ed8bf" />
            <path d="M290 222 L286 244 L294 244 Z" fill="#8ed8bf" />
            <circle cx="301" cy="198" r="16" fill="#f1c7a3" />
            <path d="M285 196 C285 180 298 176 306 178 C316 180 320 190 317 198 C312 190 300 188 292 196 Z" fill="#3a2a22" />
            <path d="M287 192 C278 198 278 212 284 218 C286 210 288 202 290 196 Z" fill="#3a2a22" />
            <circle cx="307" cy="199" r="1.8" fill="#122131" />
            <path d="M305 206 Q309 208 312 205" stroke="#122131" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          </g>

          <g>
            <ellipse cx="368" cy="316" rx="14" ry="3" fill="#0d1d22" opacity="0.35" />
            <ellipse cx="368" cy="282" rx="12" ry="4" fill="#8ed8bf" opacity="0.35" />
            <line x1="368" y1="232" x2="368" y2="218" stroke="#122131" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="368" cy="215" r="4.5" fill="#ff8f66" />
            <circle cx="368" cy="215" r="9" fill="#ff8f66" opacity="0.25" />
            <ellipse cx="349" cy="256" rx="5" ry="8" fill="#5fb89d" />
            <ellipse cx="387" cy="256" rx="5" ry="8" fill="#5fb89d" />
            <rect x="350" y="232" width="36" height="44" rx="16" fill="#8ed8bf" stroke="#122131" strokeWidth="2.5" />
            <rect x="356" y="240" width="24" height="18" rx="8" fill="#122131" />
            <circle cx="368" cy="249" r="5.5" fill="#bff3ff" />
            <circle cx="370" cy="247" r="1.8" fill="#ffffff" />
            <circle cx="368" cy="268" r="2" fill="#122131" opacity="0.5" />
          </g>
        </g>
      </svg>
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}
