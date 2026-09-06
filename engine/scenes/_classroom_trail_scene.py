"""Deterministic local Classroom Trail scene.

The scene owns one movable player plus package-qualified stationary NPCs and
objects. It executes no student code; callers provide already validated engine
entities and inert interaction text.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING

from engine.entities import Bounds, Character, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.interactions._proximity import (
    _center_distance_sq,
    _validate_interaction_range,
)
from engine.scenes._scene import Scene

if TYPE_CHECKING:
    from engine.rendering import Renderer

_MOVEMENT_SPEED = 160.0
_DEFAULT_INTERACTION_RANGE = 120.0
_FEEDBACK_DURATION = 2.0
_DEFAULT_NEAR_MESSAGE = "Press E to explore"
_DEFAULT_INTERACTED_MESSAGE = "You found a treasure!"
_FEEDBACK_X = 360
_FEEDBACK_Y = 560
_PROGRESS_X = 20
_PROGRESS_Y = 20
_COMPLETE_X = 360
_COMPLETE_Y = 520
_TEXT_COLOR = (240, 240, 240)
_FEEDBACK_FONT_SIZE = 28
_PROGRESS_FONT_SIZE = 24
_MISSION_X = 20
_MISSION_TITLE_Y = 55
_MISSION_INSTRUCTIONS_Y = 85
_MISSION_STATE_Y = 115


class ClassroomTrailMissionCompletionRule(StrEnum):
    """The fixed completion rules supported by Local Mission v0.1."""

    ALL_OBJECTS_VISITED = "ALL_OBJECTS_VISITED"
    ALL_INTERACTABLE_NPCS_SPOKEN_TO = "ALL_INTERACTABLE_NPCS_SPOKEN_TO"
    ALL_CONVERSATION_NPCS_COMPLETED = "ALL_CONVERSATION_NPCS_COMPLETED"
    ALL_TOGGLE_OBJECTS_CHANGED = "ALL_TOGGLE_OBJECTS_CHANGED"
    ALL_CONDITIONAL_BRANCHES_DISPLAYED = "ALL_CONDITIONAL_BRANCHES_DISPLAYED"
    ALL_COUNTER_GOALS_REACHED = "ALL_COUNTER_GOALS_REACHED"
    ALL_TWO_TOGGLE_BRANCHES_DISPLAYED = "ALL_TWO_TOGGLE_BRANCHES_DISPLAYED"
    ALL_EITHER_TOGGLE_CASES_DISPLAYED = "ALL_EITHER_TOGGLE_CASES_DISPLAYED"


@dataclass(frozen=True)
class ClassroomTrailMission:
    """One immutable local mission displayed by a Classroom Trail."""

    mission_id: str
    title: str
    instructions: str
    completion_rule: ClassroomTrailMissionCompletionRule = (
        ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    )

    def __post_init__(self) -> None:
        for field_name, value in (
            ("mission_id", self.mission_id),
            ("title", self.title),
            ("instructions", self.instructions),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-whitespace text")
        if (
            self.completion_rule is not ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_INTERACTABLE_NPCS_SPOKEN_TO
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_TOGGLE_OBJECTS_CHANGED
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_CONDITIONAL_BRANCHES_DISPLAYED
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_COUNTER_GOALS_REACHED
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_TWO_TOGGLE_BRANCHES_DISPLAYED
            and self.completion_rule
            is not ClassroomTrailMissionCompletionRule.ALL_EITHER_TOGGLE_CASES_DISPLAYED
        ):
            raise ValueError(
                'completion_rule must be "ALL_OBJECTS_VISITED" or '
                '"ALL_INTERACTABLE_NPCS_SPOKEN_TO" or '
                '"ALL_CONVERSATION_NPCS_COMPLETED" or '
                '"ALL_TOGGLE_OBJECTS_CHANGED"'
                ' or "ALL_CONDITIONAL_BRANCHES_DISPLAYED"'
                ' or "ALL_COUNTER_GOALS_REACHED"'
                ' or "ALL_TWO_TOGGLE_BRANCHES_DISPLAYED"'
                ' or "ALL_EITHER_TOGGLE_CASES_DISPLAYED"'
            )


@dataclass(frozen=True)
class ClassroomTrailObjectToggle:
    """Strict immutable two-color presentation for one toggle object."""

    off_color: tuple[int, int, int]
    on_color: tuple[int, int, int]

    def __post_init__(self) -> None:
        for field_name, color in (("off_color", self.off_color), ("on_color", self.on_color)):
            if (
                not isinstance(color, tuple)
                or len(color) != 3
                or any(
                    isinstance(channel, bool)
                    or not isinstance(channel, int)
                    or not 0 <= channel <= 255
                    for channel in color
                )
            ):
                raise ValueError(f"{field_name} must be a three-channel RGB color")
        if self.off_color == self.on_color:
            raise ValueError("off_color and on_color must be distinct")


@dataclass(frozen=True)
class ClassroomTrailObjectCounter:
    """One fixed bounded interaction goal and its authored feedback."""

    goal: int
    when_goal_reached: str

    def __post_init__(self) -> None:
        if isinstance(self.goal, bool) or not isinstance(self.goal, int) or not 2 <= self.goal <= 5:
            raise ValueError("goal must be a whole number from 2 through 5")
        if not isinstance(self.when_goal_reached, str) or not self.when_goal_reached.strip():
            raise ValueError("when_goal_reached must be non-whitespace text")


@dataclass(frozen=True)
class ClassroomTrailObject:
    """One inert, package-qualified object participating in a trail."""

    qualified_id: str
    world_object: WorldObject
    when_near: str | None = None
    when_interacted: str | None = None
    toggle: ClassroomTrailObjectToggle | None = None
    counter: ClassroomTrailObjectCounter | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.qualified_id, str) or not self.qualified_id.strip():
            raise ValueError("qualified_id must be non-whitespace text")
        if not isinstance(self.world_object, WorldObject):
            raise TypeError("world_object must be a WorldObject")
        if self.toggle is not None and not isinstance(self.toggle, ClassroomTrailObjectToggle):
            raise TypeError("toggle must be a ClassroomTrailObjectToggle when present")
        if self.toggle is not None and self.world_object.color != self.toggle.off_color:
            raise ValueError("world_object.color must equal toggle.off_color")
        if self.counter is not None and not isinstance(self.counter, ClassroomTrailObjectCounter):
            raise TypeError("counter must be a ClassroomTrailObjectCounter when present")
        for field_name, message in (
            ("when_near", self.when_near),
            ("when_interacted", self.when_interacted),
        ):
            if message is not None and (not isinstance(message, str) or not message.strip()):
                raise ValueError(f"{field_name} must be non-whitespace text when present")


@dataclass(frozen=True)
class ClassroomTrailNPCConditionalResponse:
    """Fixed if/else response bound to one package-local toggle object."""

    toggle_qualified_id: str
    when_off: str
    when_on: str

    def __post_init__(self) -> None:
        for field_name, value in (
            ("toggle_qualified_id", self.toggle_qualified_id),
            ("when_off", self.when_off),
            ("when_on", self.when_on),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-whitespace text")


@dataclass(frozen=True)
class ClassroomTrailNPCTwoToggleResponse:
    """Fixed Boolean-and response bound to exactly two package-local toggles."""

    toggle_qualified_ids: tuple[str, str]
    when_not_all_on: str
    when_all_on: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.toggle_qualified_ids, tuple)
            or len(self.toggle_qualified_ids) != 2
            or self.toggle_qualified_ids[0] == self.toggle_qualified_ids[1]
            or any(
                not isinstance(value, str) or not value.strip()
                for value in self.toggle_qualified_ids
            )
        ):
            raise ValueError("toggle_qualified_ids must contain exactly two distinct IDs")
        for field_name, value in (
            ("when_not_all_on", self.when_not_all_on),
            ("when_all_on", self.when_all_on),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-whitespace text")


@dataclass(frozen=True)
class ClassroomTrailNPCEitherToggleResponse:
    """Fixed Boolean-or response bound to exactly two package-local toggles."""

    toggle_qualified_ids: tuple[str, str]
    when_both_off: str
    when_either_on: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.toggle_qualified_ids, tuple)
            or len(self.toggle_qualified_ids) != 2
            or self.toggle_qualified_ids[0] == self.toggle_qualified_ids[1]
            or any(
                not isinstance(value, str) or not value.strip()
                for value in self.toggle_qualified_ids
            )
        ):
            raise ValueError("toggle_qualified_ids must contain exactly two distinct IDs")
        for field_name, value in (
            ("when_both_off", self.when_both_off),
            ("when_either_on", self.when_either_on),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-whitespace text")


@dataclass(frozen=True)
class ClassroomTrailNPC:
    """One stationary character whose NPC role exists only in this trail."""

    qualified_id: str
    character: Character
    greeting: str | None = None
    conversation: tuple[str, ...] | None = None
    respond_to_toggle: ClassroomTrailNPCConditionalResponse | None = None
    respond_to_two_toggles: ClassroomTrailNPCTwoToggleResponse | None = None
    respond_to_either_toggle: ClassroomTrailNPCEitherToggleResponse | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.qualified_id, str) or not self.qualified_id.strip():
            raise ValueError("qualified_id must be non-whitespace text")
        if not isinstance(self.character, Character):
            raise TypeError("character must be a Character")
        if self.greeting is not None and (
            not isinstance(self.greeting, str) or not self.greeting.strip()
        ):
            raise ValueError("greeting must be non-whitespace text when present")
        if self.conversation is not None and (
            not isinstance(self.conversation, tuple)
            or not 2 <= len(self.conversation) <= 3
            or any(not isinstance(line, str) or not line.strip() for line in self.conversation)
        ):
            raise ValueError("conversation must contain exactly 2 or 3 nonblank lines")
        if self.greeting is not None and self.conversation is not None:
            raise ValueError("conversation cannot be combined with greeting")
        if self.respond_to_toggle is not None and not isinstance(
            self.respond_to_toggle, ClassroomTrailNPCConditionalResponse
        ):
            raise TypeError(
                "respond_to_toggle must be a ClassroomTrailNPCConditionalResponse when present"
            )
        if self.respond_to_toggle is not None and (
            self.greeting is not None or self.conversation is not None
        ):
            raise ValueError("respond_to_toggle cannot be combined with greeting or conversation")
        if self.respond_to_two_toggles is not None and not isinstance(
            self.respond_to_two_toggles, ClassroomTrailNPCTwoToggleResponse
        ):
            raise TypeError(
                "respond_to_two_toggles must be a ClassroomTrailNPCTwoToggleResponse when present"
            )
        if self.respond_to_two_toggles is not None and (
            self.greeting is not None
            or self.conversation is not None
            or self.respond_to_toggle is not None
        ):
            raise ValueError(
                "respond_to_two_toggles cannot be combined with greeting, conversation, "
                "or respond_to_toggle"
            )
        if self.respond_to_either_toggle is not None and not isinstance(
            self.respond_to_either_toggle, ClassroomTrailNPCEitherToggleResponse
        ):
            raise TypeError(
                "respond_to_either_toggle must be a "
                "ClassroomTrailNPCEitherToggleResponse when present"
            )
        if self.respond_to_either_toggle is not None and (
            self.greeting is not None
            or self.conversation is not None
            or self.respond_to_toggle is not None
            or self.respond_to_two_toggles is not None
        ):
            raise ValueError(
                "respond_to_either_toggle cannot be combined with greeting, conversation, "
                "respond_to_toggle, or respond_to_two_toggles"
            )

    @property
    def conversation_lines(self) -> tuple[str, ...]:
        """Return the authored conversation or backward-compatible greeting."""
        if self.conversation is not None:
            return self.conversation
        if self.greeting is not None:
            return (self.greeting,)
        return ()


ClassroomTrailTarget = ClassroomTrailObject | ClassroomTrailNPC


class ClassroomTrailScene(Scene):
    """One-player trail with deterministic object and NPC targeting."""

    def __init__(
        self,
        renderer: Renderer,
        player: Character,
        objects: tuple[ClassroomTrailObject, ...],
        npcs: tuple[ClassroomTrailNPC, ...] = (),
        *,
        mission: ClassroomTrailMission,
        interaction_range: float | int = _DEFAULT_INTERACTION_RANGE,
    ) -> None:
        super().__init__()
        if not isinstance(player, Character):
            raise TypeError("player must be a Character")
        if not isinstance(objects, tuple) or not objects:
            raise ValueError("objects must be a non-empty tuple")
        if any(not isinstance(item, ClassroomTrailObject) for item in objects):
            raise TypeError("objects must contain only ClassroomTrailObject values")
        if not isinstance(npcs, tuple):
            raise TypeError("npcs must be a tuple")
        if any(not isinstance(item, ClassroomTrailNPC) for item in npcs):
            raise TypeError("npcs must contain only ClassroomTrailNPC values")
        if not isinstance(mission, ClassroomTrailMission):
            raise TypeError("mission must be a ClassroomTrailMission")
        qualified_ids = tuple(item.qualified_id for item in (*objects, *npcs))
        if len(qualified_ids) != len(set(qualified_ids)):
            raise ValueError("objects and npcs must have unique qualified IDs")

        self._renderer = renderer
        self._player = player
        self._objects = tuple(sorted(objects, key=lambda item: item.qualified_id))
        self._npcs = tuple(sorted(npcs, key=lambda item: item.qualified_id))
        self._mission = mission
        self._interaction_range = _validate_interaction_range(interaction_range)
        self._range_sq = self._interaction_range * self._interaction_range
        self._target: ClassroomTrailTarget | None = None
        self._visited_qualified_ids: frozenset[str] = frozenset()
        self._spoken_npc_ids: frozenset[str] = frozenset()
        self._completed_conversation_npc_ids: frozenset[str] = frozenset()
        self._toggle_on_qualified_ids: frozenset[str] = frozenset()
        self._changed_toggle_qualified_ids: frozenset[str] = frozenset()
        self._displayed_conditional_branches: frozenset[tuple[str, bool]] = frozenset()
        self._displayed_two_toggle_branches: frozenset[tuple[str, bool]] = frozenset()
        self._displayed_either_toggle_cases: frozenset[tuple[str, bool, bool]] = frozenset()
        self._counter_counts: Mapping[str, int] = MappingProxyType(
            {item.qualified_id: 0 for item in self._objects if item.counter is not None}
        )
        self._interaction_pulse = False
        self._feedback_message: str | None = None
        self._feedback_remaining = 0.0
        self._conversation_positions = {npc.qualified_id: 0 for npc in self._npcs}
        objects_by_id = {item.qualified_id: item for item in self._objects}
        for npc in self._npcs:
            conditional = npc.respond_to_toggle
            if conditional is None:
                continue
            target = objects_by_id.get(conditional.toggle_qualified_id)
            npc_package, _, _ = npc.qualified_id.partition(":")
            target_package, separator, _ = conditional.toggle_qualified_id.partition(":")
            if (
                target is None
                or target.toggle is None
                or not separator
                or target_package != npc_package
            ):
                raise ValueError("respond_to_toggle must reference one same-package toggle object")

        for npc in self._npcs:
            conditional = npc.respond_to_two_toggles
            if conditional is None:
                continue
            npc_package, _, _ = npc.qualified_id.partition(":")
            for toggle_qualified_id in conditional.toggle_qualified_ids:
                target = objects_by_id.get(toggle_qualified_id)
                target_package, separator, _ = toggle_qualified_id.partition(":")
                if (
                    target is None
                    or target.toggle is None
                    or not separator
                    or target_package != npc_package
                ):
                    raise ValueError(
                        "respond_to_two_toggles must reference exactly two same-package "
                        "toggle objects"
                    )

        for npc in self._npcs:
            conditional = npc.respond_to_either_toggle
            if conditional is None:
                continue
            npc_package, _, _ = npc.qualified_id.partition(":")
            for toggle_qualified_id in conditional.toggle_qualified_ids:
                target = objects_by_id.get(toggle_qualified_id)
                target_package, separator, _ = toggle_qualified_id.partition(":")
                if (
                    target is None
                    or target.toggle is None
                    or not separator
                    or target_package != npc_package
                ):
                    raise ValueError(
                        "respond_to_either_toggle must reference exactly two same-package "
                        "toggle objects"
                    )

    @property
    def player(self) -> Character:
        return self._player

    @property
    def objects(self) -> tuple[ClassroomTrailObject, ...]:
        return self._objects

    @property
    def npcs(self) -> tuple[ClassroomTrailNPC, ...]:
        return self._npcs

    @property
    def mission(self) -> ClassroomTrailMission:
        return self._mission

    @property
    def mission_is_complete(self) -> bool:
        """Derive mission completion from the selected fixed rule."""
        rule = self._mission.completion_rule
        if rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED:
            return self.is_complete
        if rule is ClassroomTrailMissionCompletionRule.ALL_INTERACTABLE_NPCS_SPOKEN_TO:
            interactable_npc_ids = frozenset(
                npc.qualified_id for npc in self._npcs if npc.conversation_lines
            )
            return bool(interactable_npc_ids) and interactable_npc_ids <= self._spoken_npc_ids
        if rule is ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED:
            conversation_npc_ids = frozenset(
                npc.qualified_id for npc in self._npcs if npc.conversation is not None
            )
            return (
                bool(conversation_npc_ids)
                and conversation_npc_ids <= self._completed_conversation_npc_ids
            )
        if rule is ClassroomTrailMissionCompletionRule.ALL_TOGGLE_OBJECTS_CHANGED:
            toggle_object_ids = frozenset(
                item.qualified_id for item in self._objects if item.toggle is not None
            )
            return bool(toggle_object_ids) and (
                toggle_object_ids <= self._changed_toggle_qualified_ids
            )
        if rule is ClassroomTrailMissionCompletionRule.ALL_CONDITIONAL_BRANCHES_DISPLAYED:
            conditional_npc_ids = frozenset(
                npc.qualified_id for npc in self._npcs if npc.respond_to_toggle is not None
            )
            required = frozenset(
                (qualified_id, is_on)
                for qualified_id in conditional_npc_ids
                for is_on in (False, True)
            )
            return bool(conditional_npc_ids) and required <= self._displayed_conditional_branches
        if rule is ClassroomTrailMissionCompletionRule.ALL_COUNTER_GOALS_REACHED:
            counter_objects = tuple(item for item in self._objects if item.counter is not None)
            return bool(counter_objects) and all(
                self._counter_counts[item.qualified_id] >= item.counter.goal
                for item in counter_objects
            )
        if rule is ClassroomTrailMissionCompletionRule.ALL_TWO_TOGGLE_BRANCHES_DISPLAYED:
            conditional_npc_ids = frozenset(
                npc.qualified_id for npc in self._npcs if npc.respond_to_two_toggles is not None
            )
            required = frozenset(
                (qualified_id, all_on)
                for qualified_id in conditional_npc_ids
                for all_on in (False, True)
            )
            return bool(conditional_npc_ids) and required <= self._displayed_two_toggle_branches
        if rule is ClassroomTrailMissionCompletionRule.ALL_EITHER_TOGGLE_CASES_DISPLAYED:
            conditional_npc_ids = frozenset(
                npc.qualified_id for npc in self._npcs if npc.respond_to_either_toggle is not None
            )
            required = frozenset(
                (qualified_id, first_on, second_on)
                for qualified_id in conditional_npc_ids
                for first_on, second_on in ((False, False), (True, False), (False, True))
            )
            return bool(conditional_npc_ids) and required <= self._displayed_either_toggle_cases
        raise AssertionError("unsupported mission completion rule")

    @property
    def target_qualified_id(self) -> str | None:
        return None if self._target is None else self._target.qualified_id

    @property
    def did_interact_this_frame(self) -> bool:
        return self._interaction_pulse

    @property
    def visited_qualified_ids(self) -> frozenset[str]:
        return self._visited_qualified_ids

    @property
    def spoken_npc_ids(self) -> frozenset[str]:
        return self._spoken_npc_ids

    @property
    def completed_conversation_npc_ids(self) -> frozenset[str]:
        return self._completed_conversation_npc_ids

    @property
    def toggle_on_qualified_ids(self) -> frozenset[str]:
        return self._toggle_on_qualified_ids

    @property
    def changed_toggle_qualified_ids(self) -> frozenset[str]:
        return self._changed_toggle_qualified_ids

    @property
    def displayed_conditional_branches(self) -> frozenset[tuple[str, bool]]:
        return self._displayed_conditional_branches

    @property
    def displayed_two_toggle_branches(self) -> frozenset[tuple[str, bool]]:
        return self._displayed_two_toggle_branches

    @property
    def displayed_either_toggle_cases(self) -> frozenset[tuple[str, bool, bool]]:
        return self._displayed_either_toggle_cases

    @property
    def counter_counts(self) -> Mapping[str, int]:
        return self._counter_counts

    @property
    def visited_count(self) -> int:
        return len(self._visited_qualified_ids)

    @property
    def total_objects(self) -> int:
        return len(self._objects)

    @property
    def is_complete(self) -> bool:
        return self.visited_count == self.total_objects

    def update(
        self,
        input_state: DirectionalInput,
        interaction_input: InteractionInput,
        dt: float,
    ) -> None:
        super().update(input_state, interaction_input, dt)
        self._move_player(input_state, dt)
        self._target = self._nearest_in_range_interactable()
        self._interaction_pulse = interaction_input.interact_pressed and self._target is not None
        if self._interaction_pulse:
            assert self._target is not None
            if isinstance(self._target, ClassroomTrailObject):
                self._visited_qualified_ids = self._visited_qualified_ids | {
                    self._target.qualified_id
                }
                self._feedback_message = self._target.when_interacted or _DEFAULT_INTERACTED_MESSAGE
                if self._target.toggle is not None:
                    qualified_id = self._target.qualified_id
                    if qualified_id in self._toggle_on_qualified_ids:
                        self._toggle_on_qualified_ids = self._toggle_on_qualified_ids - {
                            qualified_id
                        }
                    else:
                        self._toggle_on_qualified_ids = self._toggle_on_qualified_ids | {
                            qualified_id
                        }
                    self._changed_toggle_qualified_ids = self._changed_toggle_qualified_ids | {
                        qualified_id
                    }
                if self._target.counter is not None:
                    qualified_id = self._target.qualified_id
                    count = self._counter_counts[qualified_id] + 1
                    self._counter_counts = MappingProxyType(
                        {**self._counter_counts, qualified_id: count}
                    )
                    counter = self._target.counter
                    self._feedback_message = (
                        f"{self._feedback_message} Count: {count} / {counter.goal}."
                    )
                    if count >= counter.goal:
                        self._feedback_message = (
                            f"{self._feedback_message} {counter.when_goal_reached}"
                        )
            else:
                self._spoken_npc_ids = self._spoken_npc_ids | {self._target.qualified_id}
                conditional = self._target.respond_to_toggle
                if conditional is not None:
                    is_on = conditional.toggle_qualified_id in self._toggle_on_qualified_ids
                    response = conditional.when_on if is_on else conditional.when_off
                    self._feedback_message = f"{self._target.character.name}: {response}"
                    self._displayed_conditional_branches = self._displayed_conditional_branches | {
                        (self._target.qualified_id, is_on)
                    }
                elif self._target.respond_to_two_toggles is not None:
                    two_toggle = self._target.respond_to_two_toggles
                    first_toggle, second_toggle = two_toggle.toggle_qualified_ids
                    all_on = (
                        first_toggle in self._toggle_on_qualified_ids
                        and second_toggle in self._toggle_on_qualified_ids
                    )
                    response = two_toggle.when_all_on if all_on else two_toggle.when_not_all_on
                    self._feedback_message = f"{self._target.character.name}: {response}"
                    self._displayed_two_toggle_branches = self._displayed_two_toggle_branches | {
                        (self._target.qualified_id, all_on)
                    }
                elif self._target.respond_to_either_toggle is not None:
                    either_toggle = self._target.respond_to_either_toggle
                    first_toggle, second_toggle = either_toggle.toggle_qualified_ids
                    first_on = first_toggle in self._toggle_on_qualified_ids
                    second_on = second_toggle in self._toggle_on_qualified_ids
                    either_on = first_on or second_on
                    response = (
                        either_toggle.when_either_on if either_on else either_toggle.when_both_off
                    )
                    self._feedback_message = f"{self._target.character.name}: {response}"
                    self._displayed_either_toggle_cases = self._displayed_either_toggle_cases | {
                        (self._target.qualified_id, first_on, second_on)
                    }
                else:
                    lines = self._target.conversation_lines
                    assert lines
                    position = self._conversation_positions[self._target.qualified_id]
                    self._feedback_message = f"{self._target.character.name}: {lines[position]}"
                    if (
                        self._target.conversation is not None
                        and position == len(self._target.conversation) - 1
                    ):
                        self._completed_conversation_npc_ids = (
                            self._completed_conversation_npc_ids | {self._target.qualified_id}
                        )
                    self._conversation_positions[self._target.qualified_id] = (position + 1) % len(
                        lines
                    )
            self._feedback_remaining = _FEEDBACK_DURATION
        elif self._feedback_remaining > 0:
            self._feedback_remaining = max(0.0, self._feedback_remaining - dt)

    def render(self) -> None:
        super().render()
        for item in self._objects:
            world_object = item.world_object
            color = (
                item.toggle.on_color
                if item.toggle is not None and item.qualified_id in self._toggle_on_qualified_ids
                else world_object.color
            )
            self._renderer.draw_rect(
                world_object.x,
                world_object.y,
                world_object.width,
                world_object.height,
                color,
            )
        for item in self._npcs:
            character = item.character
            self._renderer.draw_rect(
                character.x,
                character.y,
                character.width,
                character.height,
                character.color,
            )
        self._renderer.draw_rect(
            self._player.x,
            self._player.y,
            self._player.width,
            self._player.height,
            self._player.color,
        )
        self._renderer.draw_text(
            f"Visited {self.visited_count} / {self.total_objects}",
            _PROGRESS_X,
            _PROGRESS_Y,
            _TEXT_COLOR,
            _PROGRESS_FONT_SIZE,
        )
        self._renderer.draw_text(
            f"Mission: {self._mission.title}",
            _MISSION_X,
            _MISSION_TITLE_Y,
            _TEXT_COLOR,
            _PROGRESS_FONT_SIZE,
        )
        self._renderer.draw_text(
            self._mission.instructions,
            _MISSION_X,
            _MISSION_INSTRUCTIONS_Y,
            _TEXT_COLOR,
            _PROGRESS_FONT_SIZE,
        )
        mission_state = "Complete" if self.mission_is_complete else "Incomplete"
        self._renderer.draw_text(
            f"Mission state: {mission_state}",
            _MISSION_X,
            _MISSION_STATE_Y,
            _TEXT_COLOR,
            _PROGRESS_FONT_SIZE,
        )
        if self.is_complete:
            self._renderer.draw_text(
                "Trail complete!",
                _COMPLETE_X,
                _COMPLETE_Y,
                _TEXT_COLOR,
                _FEEDBACK_FONT_SIZE,
            )
        if self._feedback_remaining > 0 and self._feedback_message is not None:
            message = self._feedback_message
        elif isinstance(self._target, ClassroomTrailObject):
            message = self._target.when_near or _DEFAULT_NEAR_MESSAGE
        elif self._target is not None:
            message = _DEFAULT_NEAR_MESSAGE
        else:
            message = None
        if message is not None:
            self._renderer.draw_text(
                message,
                _FEEDBACK_X,
                _FEEDBACK_Y,
                _TEXT_COLOR,
                _FEEDBACK_FONT_SIZE,
            )

    def _move_player(self, input_state: DirectionalInput, dt: float) -> None:
        displacement = _MOVEMENT_SPEED * dt
        self._player.move(
            input_state.horizontal * displacement,
            input_state.vertical * displacement,
            Bounds(
                min_x=0,
                min_y=0,
                max_x=960 - self._player.width,
                max_y=640 - self._player.height,
            ),
        )

    def _nearest_in_range_interactable(self) -> ClassroomTrailTarget | None:
        candidates: list[tuple[float, str, ClassroomTrailTarget]] = []
        interactables: tuple[ClassroomTrailTarget, ...] = (
            *self._objects,
            *(
                npc
                for npc in self._npcs
                if (
                    npc.conversation_lines
                    or npc.respond_to_toggle is not None
                    or npc.respond_to_two_toggles is not None
                    or npc.respond_to_either_toggle is not None
                )
            ),
        )
        for item in interactables:
            entity = item.world_object if isinstance(item, ClassroomTrailObject) else item.character
            distance_sq = _center_distance_sq(
                self._player.x_float,
                self._player.y_float,
                self._player.width,
                self._player.height,
                entity.x,
                entity.y,
                entity.width,
                entity.height,
            )
            if distance_sq <= self._range_sq:
                candidates.append((distance_sq, item.qualified_id, item))
        if not candidates:
            return None
        return min(candidates, key=lambda candidate: (candidate[0], candidate[1]))[2]
