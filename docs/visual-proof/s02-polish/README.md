# S02 visual polish pass — runtime proof

Real 960 × 640 frames from the Classroom Trail runtime, captured with
`scripts/capture_s02_visual_proof.py` (same script, same input, fixed 60 FPS).

| Evidence | File |
|---|---|
| BEFORE_PR105 (base e89c96a) | `before-pr105.png` |
| CURRENT_PR105 (head 64ee4d5) | `current-pr105.png` (+ `-compass-prompt`, `-lantern-prompt`) |
| POLISHED_IDLE | `polished-idle.png` |
| NOVA_WALK_RIGHT / LEFT | `nova-walk-right.png`, `nova-walk-left.png` |
| PIXEL_GREETING | `pixel-greeting.png` |
| COMPASS_PROMPT / INTERACTION | `compass-prompt.png`, `compass-interaction.png` |
| LANTERN_PROMPT / INTERACTION | `lantern-prompt.png`, `lantern-interaction.png` |
| MISSION_COMPLETE | `mission-complete.png` |
| LIVING_WORLD_5S | `living-world-5s.png`, `living-world-5.5s.png`, `living-world-5s.gif` |
| HALF_SCALE_480x320 | `half-scale-480x320.png` |
| MOVED_COMPASS | `moved-compass.png` |
| Walking GIF | `nova-walking.gif` |
| Side-by-side | `comparison-pr105-vs-polished.png` |

## Side-by-side review (current PR #105 head vs polished)

- **Painterly softness:** clearly better. Edges are softened, distant hills are
  blurred, and bloom and grain add a painted feel. The whole scene is now hazier
  and a little lower in contrast.
- **Prop repetition:** clearly better. Shrine and meadow bushes, mushrooms
  (four cap colors) and crystal shards now differ by size, silhouette, tone and
  blossoms. They are no longer visible copies.
- **Depth:** better. Cool haze thickens with distance, a value band sits under
  the tree line, and foreground tufts and pebbles cover only the bottom strip.
  The occlusion is presentation-only and never overlaps an entity box.
- **HUD:** a modest gain. The card is softer and lifted, with a gentle edge.
  Text, order and position are unchanged. No font was added: no redistributable
  font was bundled or downloaded, so the current font remains.
- **Compass focal:** strongest gain. A contrast shadow, violet aura and rune
  ring on the dais, a two-tier ground ring, and eased sparkles make it the hero.
- **Lantern destination:** stronger. Warm shrine against cooled surroundings,
  with a lit approach path. This path is a little hot and could be toned down.
- **Character integration:** a subtle gain from soft edges, a cool lower shade
  and a moon rim. The characters are still crisp cutouts compared with the plate.

VISUAL_POLISH_DELTA: material improvement.
NORTH_STAR_DISTANCE: moderate. The mood is closer, but the plate is hazier and
darker than an ideal storybook target, and the characters are still crisp.

Frame timing (600 frames, same benchmark): PR #105 head mean 0.89–0.96 ms,
p95 1.03–1.30 ms. Polished head mean 0.93–1.03 ms, p95 1.02–1.54 ms. That is
within run-to-run noise.
