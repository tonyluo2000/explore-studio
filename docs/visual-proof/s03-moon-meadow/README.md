# S03 Moon Meadow — runtime proof

Real 960 × 640 frames from the M03 Classroom Trail runtime, captured headlessly
with `scripts/capture_s03_visual_proof.py` from the canonical S03 command's
packages (`nova-character` + `lessons/sessions/s03/student/explorer-package`),
real directional input, one real `E` press, and fixed 60 FPS steps.

| Evidence | File |
|---|---|
| BEFORE (main 3a11c2f): plain frame, purple rectangle Compass, static Nova | `before-near-clue.png` |
| Idle: Moon Meadow, Nova V3, trusted Compass art, ambience, HUD panel | `s03-idle.png` |
| Near: `when_near` clue at the unchanged feedback line, shared `E` prompt, `Visited 0 / 1` | `s03-near-clue.png` |
| Interacted: `when_interacted` reveal, Compass discovery burst, `Visited 1 / 1`, complete | `s03-reveal.png` |
| After completion: no M02 "discovered!" label, confetti, or banner | `s03-complete.png` |

Gameplay parity (positions, target, visited count, completion, and the
authored feedback text with and without the presentation layer) is covered by
`tests/test_s03_presentation.py`.
