# S02 procedural sprite visual proof

These screenshots use the real Classroom Trail runtime, M02, and the reviewed
S02 packages for Nova, Pixel, Moon Compass, and Crystal Lantern. They are not
mockups.

- `original.png` — authoritative base `5aa0622b73c292adf9e5221a86da3da2e9116071`;
  all four entities use the previous rectangle renderer.
- `new-scene.png` — the same packages and coordinates after the procedural
  sprite renderer change.
- `moved-compass.png` — the same scene with only the student-owned Moon Compass
  coordinates changed from `(240, 180)` to `(690, 360)` in a temporary package
  copy. The compass sprite follows those coordinates without changing its
  `80 x 60` gameplay bounds.

The generic Explorer Package `asset_id` image pipeline remains future work.
This classroom exception intentionally routes only the four stable,
package-qualified S02 identities and preserves rectangle fallback for every
other entity.
