"""Deterministic S06–S09 acceptance against a supplied extracted Course Kit.

Copied beside trail_driver.py into isolation by the live verifier. Runtime imports
must resolve to the fresh virtualenv, never this repository's engine/explore.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path

if __package__:
    from scripts.trail_driver import Trail
else:
    from trail_driver import Trail

MISSIONS = {
    "S06": "build-an-object-collection",
    "S07": "toggle-an-object-state",
    "S08": "respond-to-object-state",
    "S09": "count-object-interactions",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(f"TRAIL_ACCEPTANCE_FAILED: {message}")


def accept(root: Path, session: str) -> dict:
    package = root / f"lessons/sessions/{session.lower()}/student/explorer-package"
    card = (package.parent / "task-card.md").read_text()
    commands = []
    for block in re.findall(r"```(?:console|bash|sh)\s*\n(.*?)```", card, re.DOTALL):
        for line in block.replace("\\\n", " ").splitlines():
            if line.strip().startswith("explore-package trail "):
                commands.append(shlex.split(line.strip()))
    require(len(commands) == 1, f"{session}: exactly one canonical Trail command required")
    tokens = commands[0]
    require(
        tokens[2:4]
        == [
            "examples/explorer-packages/nova-character",
            f"lessons/sessions/{session.lower()}/student/explorer-package",
        ],
        f"{session}: acceptance package roots differ from task card",
    )
    require(len(tokens) == 10, f"{session}: unsupported canonical Trail arguments")
    options = dict(zip(tokens[4::2], tokens[5::2], strict=True))
    require(
        set(options) == {"--player", "--mission-id", "--name"},
        f"{session}: unsupported canonical Trail options",
    )
    require(
        options["--mission-id"] == MISSIONS[session]
        and options["--player"] == "nova-character:nova",
        f"{session}: canonical command changed; update acceptance contract",
    )
    trail = Trail(
        (root / "examples/explorer-packages/nova-character", package), mission_id=MISSIONS[session]
    )
    try:
        scene = trail.scene
        require(scene._presentation.active, f"{session}: Moon Meadow presentation inactive")
        require(not scene.mission_is_complete, f"{session}: premature completion")
        if session == "S06":
            require(len(scene.objects) == 3, "S06: expected three objects")
            for index, (x, y) in enumerate(((180, 180), (380, 300), (570, 420)), 1):
                trail.walk_to(x, y)
                trail.hold(3.2)
                trail.press()
                require(
                    scene.mission_is_complete == (index == 3),
                    "S06: completion must follow third visit",
                )
        elif session == "S07":
            trail.walk_to(290, 300)
            require(not scene.toggle_on_qualified_ids, "S07: initial OFF")
            for on in (True, False, True):
                trail.press()
                trail.hold(0.35)
                require(bool(scene.toggle_on_qualified_ids) == on, "S07: OFF → ON → OFF → ON")
                require(scene.mission_is_complete, "S07: complete after first change")
        elif session == "S08":
            import yaml

            responses = yaml.safe_load((package / "character/gate-guardian.yaml").read_text())[
                "respond_to_toggle"
            ]
            for state in (False, True):
                if state:
                    trail.walk_to(350, 340)
                    trail.press()
                trail.walk_to(650, 275)
                trail.press()
                trail.hold(0.35)
                text = " ".join(trail.renderer.texts)
                require(
                    responses["when_on" if state else "when_off"] in text,
                    "S08: authored Guardian response",
                )
                require(f"Responses {2 if state else 1} / 2" in text, "S08: response progress")
                require(scene.mission_is_complete == state, "S08: both branches required")
        else:
            device = scene.objects[0]
            qid = device.qualified_id
            require(
                scene._presentation.sprite_identity(qid) == "moon-meadow-presentation:storm-engine",
                "S09: polished Storm Engine",
            )
            trail.walk_to(350, 300)
            for count in range(1, device.counter.goal + 1):
                trail.press()
                trail.hold(0.35)
                require(scene.counter_counts[qid] == count, "S09: count must increase")
                require(
                    scene.mission_is_complete == (count == device.counter.goal),
                    "S09: completion exactly at goal",
                )
        return {"session": session, "acceptance": "passed"}
    finally:
        trail.close()


if __name__ == "__main__":
    root = Path(sys.argv[1])
    print(json.dumps([accept(root, session) for session in MISSIONS]))
