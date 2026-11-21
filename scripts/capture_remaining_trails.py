"""Exercise and capture unpublished course Trails with real movement and E input.

Review artifacts only: never writes website assets or changes student packages.
S26 remains planning-only. S25 placeholder scaffold and authored recovery example
are reported separately; neither is represented as a finished student project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from engine.rendering._mission_presentation import COURSE_TRAIL_PROFILES  # noqa: E402
from scripts.trail_driver import Trail  # noqa: E402


def approach(trail: Trail, qualified_id: str) -> None:
    """Walk to a real prompt; nearby entities never substitute for this target."""
    entity = next(
        (o.world_object for o in trail.scene.objects if o.qualified_id == qualified_id), None
    )
    if entity is None:
        entity = next(n.character for n in trail.scene.npcs if n.qualified_id == qualified_id)
    for dx, dy in ((-70, 0), (65, 0), (0, 65), (0, -70), (-40, 40)):
        trail.walk_to(max(0, min(860, entity.x + dx)), max(0, min(540, entity.y + dy)))
        trail.hold(0.15)
        if trail.scene.target_qualified_id == qualified_id:
            return
    raise AssertionError(f"No reachable prompt for {qualified_id}")


def interact(trail: Trail, qualified_id: str) -> None:
    approach(trail, qualified_id)
    trail.press()
    trail.hold(0.35)


def observe_line(trail: Trail, npc, line: str) -> None:
    interact(trail, npc.qualified_id)
    assert trail.scene.feedback_message == f"{npc.character.name}: {line}"
    # The full authored line must survive wrapping and the focused HUD echo.
    drawn = " ".join(" ".join(trail.renderer.texts).split())
    assert " ".join(line.split()) in drawn, (npc.qualified_id, line, drawn)
    assert trail.scene._presentation.bubble.text == line


def signature(scene):
    return [
        (
            o.qualified_id,
            o.world_object.name,
            o.world_object.x,
            o.world_object.y,
            o.world_object.color,
            o.when_near,
            o.when_interacted,
        )
        for o in scene.objects
    ]


def exercise(
    session: str,
    out: Path | None = None,
    *,
    package: Path | None = None,
    mission: str | None = None,
    presentation_session: str | None = None,
) -> dict:
    root = package or ROOT / f"lessons/sessions/{session.lower()}/student/explorer-package"
    mission = mission or COURSE_TRAIL_PROFILES[session][1][0]
    trail = Trail(
        (ROOT / "examples/explorer-packages/nova-character", root),
        mission_id=mission,
        presentation_session=presentation_session,
    )
    frames = {}

    def capture(name):
        if out is not None:
            path = out / f"{name}.png"
            trail.save(path)
            frames[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    try:
        scene = trail.scene
        initial = signature(scene)
        trail.hold(0.3)
        assert scene._presentation.active
        assert all(
            scene._presentation.sprite_identity(o.qualified_id) != o.qualified_id
            for o in scene.objects
        )
        capture("spawn")
        assert not scene.mission_is_complete
        # Branch missions: verify every state with real authored feedback.
        if mission in (
            "compare-a-counter-to-its-goal",
            "require-all-switches-on",
            "open-with-either-switch",
            "respond-to-object-state",
            "invert-a-switch-condition",
        ):
            for npc in scene.npcs:
                if npc.respond_to_counter is not None:
                    rule = npc.respond_to_counter
                    item = next(
                        o for o in scene.objects if o.qualified_id == rule.counter_qualified_id
                    )
                    observe_line(trail, npc, rule.when_below_goal)
                    capture("below-initial")
                    for _ in range(item.counter.goal - 1):
                        interact(trail, item.qualified_id)
                    observe_line(trail, npc, rule.when_below_goal)
                    assert not scene.mission_is_complete
                    capture("one-before-goal")
                    interact(trail, item.qualified_id)
                    assert scene.counter_counts[item.qualified_id] == item.counter.goal
                    observe_line(trail, npc, rule.when_at_or_above_goal)
                    capture("exact-goal")
                    interact(trail, item.qualified_id)
                    observe_line(trail, npc, rule.when_at_or_above_goal)
                    assert scene.counter_counts[item.qualified_id] == item.counter.goal + 1
                else:
                    rule = (
                        npc.respond_to_toggle
                        or npc.respond_to_two_toggles
                        or npc.respond_to_either_toggle
                    )
                    if rule is None:
                        continue
                    ids = (
                        (rule.toggle_qualified_id,)
                        if npc.respond_to_toggle
                        else rule.toggle_qualified_ids
                    )
                    states = (
                        ((False,), (True,))
                        if len(ids) == 1
                        else ((False, False), (True, False), (True, True), (False, True))
                    )
                    for index, state in enumerate(states):
                        for qid, on in zip(ids, state, strict=True):
                            if (qid in scene.toggle_on_qualified_ids) != on:
                                interact(trail, qid)
                        if npc.respond_to_toggle:
                            line = rule.when_on if state[0] else rule.when_off
                        elif npc.respond_to_two_toggles:
                            line = rule.when_all_on if all(state) else rule.when_not_all_on
                        else:
                            line = rule.when_either_on if any(state) else rule.when_both_off
                        observe_line(trail, npc, line)
                        capture(f"case-{index}-{'-'.join(str(int(v)) for v in state)}")
                        if index == 0:
                            assert not scene.mission_is_complete
            assert scene.mission_is_complete
        elif mission == "complete-actions-in-order":
            for npc in scene.npcs:
                rule = npc.respond_to_sequence
                if rule is None:
                    continue
                ids = rule.object_qualified_ids
                observe_line(trail, npc, rule.when_incomplete)
                interact(trail, ids[1])
                assert scene.sequence_progress[npc.qualified_id] == 0
                interact(trail, ids[0])
                assert scene.sequence_progress[npc.qualified_id] == 1
                capture("prefix-one")
                interact(trail, ids[2])
                assert scene.sequence_progress[npc.qualified_id] == 0
                capture("wrong-member-reset")
                for index, qid in enumerate(ids, 1):
                    interact(trail, qid)
                    assert scene.sequence_progress[npc.qualified_id] == index
                    assert scene.mission_is_complete is (index == 3)
                    capture(f"sequence-{index}")
                observe_line(trail, npc, rule.when_complete)
                capture("complete")
            assert scene.mission_is_complete
        else:
            # M06, M14, M09 and M16 retain their own completion rules.
            for index, item in enumerate(scene.objects):
                repeats = item.counter.goal if mission == "count-object-interactions" else 1
                for _ in range(repeats):
                    interact(trail, item.qualified_id)
                if index < len(scene.objects) - 1:
                    assert not scene.mission_is_complete
                capture(f"object-{index + 1}")
            assert scene.mission_is_complete
        celebration = scene._presentation.celebration_start
        capture("complete")
        interact(trail, scene.objects[0].qualified_id)
        assert scene.mission_is_complete
        assert scene._presentation.celebration_start == celebration
        capture("post-completion")
        assert signature(scene) == initial
        assert not scene._presentation._failed_layers
        return {
            "session": session,
            "mission": mission,
            "package": scene.objects[0].qualified_id.split(":", 1)[0],
            "complete": True,
            "objects": len(scene.objects),
            "frames": frames,
            "counterCounts": dict(scene.counter_counts),
            "sequenceProgress": dict(scene.sequence_progress),
        }
    finally:
        trail.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    parser.add_argument("--session", action="append", choices=tuple(COURSE_TRAIL_PROFILES))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = [exercise(s, args.out / s.lower()) for s in args.session or COURSE_TRAIL_PROFILES]
    if args.session is None:
        for session, mission in (
            ("S18", "count-object-interactions"),
            ("S23", "respond-to-object-state"),
            ("S27", "reuse-a-named-toggle-style"),
            ("S28", "complete-actions-in-order"),
            ("S29", "complete-actions-in-order"),
            ("S30", "complete-actions-in-order"),
            ("S30", "reuse-a-named-toggle-style"),
        ):
            rows.append(
                exercise(session, args.out / f"{session.lower()}-{mission}", mission=mission)
            )
        rows.append(
            exercise(
                "S25",
                args.out / "s25-recovery",
                package=ROOT / "lessons/sessions/s25/student/recovery-package",
            )
        )
    (args.out / "report.json").write_text(
        json.dumps({"trails": rows, "S26": "planning-only; no Trail"}, indent=2) + "\n"
    )
    print(f"PASS {len(rows)} real Trail exercises")


if __name__ == "__main__":
    main()
