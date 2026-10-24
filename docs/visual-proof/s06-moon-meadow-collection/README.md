# S06 Moon Meadow collection visual proof

These frames come from the real canonical S06 Classroom Trail runtime. The
capture drives Nova with normal directional input and presses `E`; it does not
mock the scene or paint over screenshots.

Regenerate from the repository root:

```console
SDL_VIDEODRIVER=dummy python3 scripts/capture_s06_visual_proof.py \
  docs/visual-proof/s06-moon-meadow-collection
```

Review sequence:

1. `s06-spawn.png`
2. `s06-sun-seed-near.png` and `s06-sun-seed-interacted.png`
3. `s06-rain-bell-near.png` and `s06-rain-bell-interacted.png`
4. `s06-two-of-three.png` — Journey HERO moment, Wind Flower targeted
5. `s06-wind-flower-near.png` and `s06-wind-flower-interacted.png` — complete

The frames verify the Moon Meadow backdrop, trusted Nova art, distinct marker
silhouettes, authored proximity and interaction responses, readable progress,
and completion only at 3 / 3. No NPC, Lantern, gate entity, or S07 state
mechanic is present.
