"""Explore Studio engine — scene management.

Owns scene lifecycle: creation, activation, frame participation, and exit.
Does not own rendering, input, or world state.

Submodules:
    _scene          — Scene base class and lifecycle states.
    _default_scene  — DefaultScene: empty scene for lifecycle validation.

Ownership: Engine team.
"""

from engine.scenes._classroom_trail_scene import (
    ClassroomTrailMission,
    ClassroomTrailMissionCompletionRule,
    ClassroomTrailNPC,
    ClassroomTrailNPCConditionalResponse,
    ClassroomTrailNPCEitherToggleResponse,
    ClassroomTrailNPCTwoToggleResponse,
    ClassroomTrailObject,
    ClassroomTrailObjectCounter,
    ClassroomTrailObjectToggle,
    ClassroomTrailScene,
)
from engine.scenes._default_scene import DefaultScene
from engine.scenes._scene import Scene, SceneLifecycleError, SceneState

__all__ = [
    "ClassroomTrailMission",
    "ClassroomTrailMissionCompletionRule",
    "ClassroomTrailNPC",
    "ClassroomTrailNPCConditionalResponse",
    "ClassroomTrailNPCEitherToggleResponse",
    "ClassroomTrailNPCTwoToggleResponse",
    "ClassroomTrailObject",
    "ClassroomTrailObjectCounter",
    "ClassroomTrailObjectToggle",
    "ClassroomTrailScene",
    "DefaultScene",
    "Scene",
    "SceneLifecycleError",
    "SceneState",
]
