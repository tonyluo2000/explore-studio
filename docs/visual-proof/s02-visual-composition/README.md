# S02 visual composition proof

These screenshots are real 960 × 640 frames from the Classroom Trail runtime,
captured headlessly (`SDL_VIDEODRIVER=dummy`) with M02 and the reviewed S02
packages for Nova, Pixel, Moon Compass, and Crystal Lantern. They are not
mockups.

- `current-merged-scene.png` — authoritative base
  `5f6858630fe20a4a78851d0093c957236e446b24`: procedural sprites on the plain
  cleared frame.
- `improved-scene.png` — the same packages and coordinates after this pass:
  static moon-meadow backdrop, a night-sky band behind the HUD text, a start
  pad with a flag, a stone-ringed discovery clearing, a gated Lantern shrine,
  and one trail with chevrons pointing from the start, through the clearing,
  to the shrine.
- `moved-compass-scene.png` — only the student-owned Moon Compass moved from
  `(240, 180)` to `(690, 360)` in a temporary package copy. The backdrop is
  static and reads no entity state, so the compass sprite (with its own shadow
  and sparkles) moves while the clearing stays a generic waypoint.
- `zoom-half-scale.png` — `improved-scene.png` smoothly scaled to 480 × 320,
  approximating a Zoom screen share.
- `pixel-greeting.png` — Nova near Pixel after pressing E; the unchanged
  greeting text over the new terrain.

The backdrop is allow-listed to the M02 mission id only; every other Trail
keeps its plain frame. Entity coordinates, bounds, hitboxes, interaction range,
movement, and HUD text are unchanged.
