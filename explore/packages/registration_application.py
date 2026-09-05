"""Transactional application of immutable Student API registration plans."""

from __future__ import annotations

from pathlib import PurePosixPath

from explore import Character, Object, StudentAPIError, World
from explore._colors import valid_color_names
from explore.packages.contribution_models import (
    PackageAssetReference,
    PackageProvenance,
)
from explore.packages.policy import (
    SUPPORTED_STUDENT_API_VERSION,
    is_valid_identifier,
    is_valid_semantic_version,
)
from explore.packages.registration_application_models import (
    AppliedRegistration,
    RegistrationApplicationIssue,
    RegistrationApplicationIssueCode,
    RegistrationApplicationResult,
    RegistrationApplicationState,
    RegistrationType,
    StudentAPIRegistrationTarget,
)
from explore.packages.registration_models import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    StudentAPIRegistrationEntry,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
)

_VALID_COLORS = frozenset(valid_color_names())


class StudentAPIWorldRegistrationTarget:
    """Explicit registration target adapting one Student API v0.1 ``World``.

    The adapter owns qualified registration identities. It observes direct
    entities already present in the wrapped world for cardinality, but it never
    assigns identities to them and never removes them.
    """

    def __init__(self, world: World) -> None:
        if not isinstance(world, World):
            raise TypeError("world must be a Student API World")
        self._world = world
        self._registrations: dict[str, Character | Object] = {}

    def contains_registration(self, qualified_id: str) -> bool:
        """Return whether this target already owns *qualified_id*."""
        return qualified_id in self._registrations

    def has_character(self) -> bool:
        """Return whether the wrapped world's character slot is occupied."""
        return self._world.character is not None

    def has_world_object(self) -> bool:
        """Return whether the wrapped world's object slot is occupied."""
        return self._world.object is not None

    def add_character(self, qualified_id: str, character: Character) -> None:
        """Add one exact Student API character and retain its qualified ID."""
        self._check_new_registration(qualified_id)
        if not isinstance(character, Character):
            raise StudentAPIError("Registration requires a Student API Character.")
        self._world.add(character)
        self._registrations[qualified_id] = character

    def remove_character(self, qualified_id: str, character: Character) -> None:
        """Remove the exact character owned by the current transaction."""
        self._check_owned_registration(qualified_id, character)
        self._world._remove_registration_entity(character)
        del self._registrations[qualified_id]

    def add_world_object(self, qualified_id: str, world_object: Object) -> None:
        """Add one exact Student API world object and retain its qualified ID."""
        self._check_new_registration(qualified_id)
        if not isinstance(world_object, Object):
            raise StudentAPIError("Registration requires a Student API Object.")
        self._world.add(world_object)
        self._registrations[qualified_id] = world_object

    def remove_world_object(self, qualified_id: str, world_object: Object) -> None:
        """Remove the exact world object owned by the current transaction."""
        self._check_owned_registration(qualified_id, world_object)
        self._world._remove_registration_entity(world_object)
        del self._registrations[qualified_id]

    def _check_new_registration(self, qualified_id: str) -> None:
        if qualified_id in self._registrations:
            raise StudentAPIError("The qualified registration identity already exists.")

    def _check_owned_registration(
        self,
        qualified_id: str,
        entity: Character | Object,
    ) -> None:
        if self._registrations.get(qualified_id) is not entity:
            raise StudentAPIError("The registration target does not own this exact entity.")


def _issue(
    code: RegistrationApplicationIssueCode,
    message: str,
    location: str,
    *,
    entry: object | None = None,
) -> RegistrationApplicationIssue:
    qualified_id = getattr(entry, "qualified_id", None)
    contribution_id = getattr(entry, "contribution_id", None)
    return RegistrationApplicationIssue(
        code=code,
        message=message,
        location=location,
        qualified_id=qualified_id if isinstance(qualified_id, str) else None,
        contribution_id=contribution_id if isinstance(contribution_id, str) else None,
    )


def _is_nonblank_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_coordinate(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_provenance(
    provenance: object,
    issues: list[RegistrationApplicationIssue],
) -> PackageProvenance | None:
    if not isinstance(provenance, PackageProvenance):
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.PLAN_PROVENANCE_MISMATCH,
                "plan.provenance must be package provenance.",
                "plan.provenance",
            )
        )
        return None

    if provenance.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (
                    "plan.provenance.student_api_version must be "
                    f'"{SUPPORTED_STUDENT_API_VERSION}".'
                ),
                "plan.provenance.student_api_version",
            )
        )
    if (
        not isinstance(provenance.package_id, str)
        or not is_valid_identifier(provenance.package_id)
        or not isinstance(provenance.package_version, str)
        or not is_valid_semantic_version(provenance.package_version)
    ):
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.PLAN_PROVENANCE_MISMATCH,
                "plan.provenance must contain valid package identity and version metadata.",
                "plan.provenance",
            )
        )
    return provenance


def _validate_identity(
    entry: CharacterRegistration | WorldObjectRegistration,
    provenance: PackageProvenance | None,
    location: str,
    issues: list[RegistrationApplicationIssue],
) -> None:
    expected_qualified_id = (
        f"{provenance.package_id}:{entry.contribution_id}"
        if provenance is not None
        and isinstance(entry.contribution_id, str)
        and is_valid_identifier(entry.contribution_id)
        else None
    )
    if expected_qualified_id is None or entry.qualified_id != expected_qualified_id:
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_IDENTITY_INVALID,
                (
                    f"{location}.qualified_id must match the plan package ID "
                    "and a valid local contribution ID."
                ),
                f"{location}.qualified_id",
                entry=entry,
            )
        )


def _validate_asset(
    asset: object,
    location: str,
    entry: CharacterRegistration | WorldObjectRegistration,
    issues: list[RegistrationApplicationIssue],
) -> None:
    if asset is None:
        return
    if not isinstance(asset, PackageAssetReference) or asset.type != "image":
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_ASSET_TYPE_MISMATCH,
                f'{location} must retain a package asset reference of type "image".',
                location,
                entry=entry,
            )
        )
        return

    path = PurePosixPath(asset.path) if isinstance(asset.path, str) else None
    if (
        not isinstance(asset.id, str)
        or not is_valid_identifier(asset.id)
        or path is None
        or not asset.path.strip()
        or "\\" in asset.path
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix.lower() != ".png"
    ):
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                f"{location} must contain valid package-relative image metadata.",
                location,
                entry=entry,
            )
        )


def _validate_common_spec(
    *,
    name: object,
    x: object,
    y: object,
    color: object,
    location: str,
    entry: CharacterRegistration | WorldObjectRegistration,
    issues: list[RegistrationApplicationIssue],
) -> None:
    values = (
        ("name", _is_nonblank_text(name), "non-whitespace text"),
        ("x", _is_coordinate(x), "a whole number of 0 or greater"),
        ("y", _is_coordinate(y), "a whole number of 0 or greater"),
        ("color", isinstance(color, str) and color in _VALID_COLORS, "a Student API v0.1 colour"),
    )
    for field, valid, requirement in values:
        if not valid:
            field_location = f"{location}.{field}"
            issues.append(
                _issue(
                    RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} must be {requirement}.",
                    field_location,
                    entry=entry,
                )
            )


def _validate_character_entry(
    entry: CharacterRegistration,
    location: str,
    issues: list[RegistrationApplicationIssue],
) -> None:
    specification = entry.character
    if not isinstance(specification, CharacterRegistrationSpec):
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                f"{location}.character must be a character registration specification.",
                f"{location}.character",
                entry=entry,
            )
        )
        return
    _validate_common_spec(
        name=specification.name,
        x=specification.x,
        y=specification.y,
        color=specification.color,
        location=f"{location}.character",
        entry=entry,
        issues=issues,
    )
    if specification.greeting is not None and not _is_nonblank_text(specification.greeting):
        field_location = f"{location}.character.greeting"
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                f"{field_location} must be non-whitespace text when present.",
                field_location,
                entry=entry,
            )
        )
    _validate_asset(entry.asset_reference, f"{location}.asset_reference", entry, issues)


def _validate_world_object_entry(
    entry: WorldObjectRegistration,
    location: str,
    issues: list[RegistrationApplicationIssue],
) -> None:
    specification = entry.world_object
    if not isinstance(specification, WorldObjectRegistrationSpec):
        issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                f"{location}.world_object must be a world-object registration specification.",
                f"{location}.world_object",
                entry=entry,
            )
        )
        return
    _validate_common_spec(
        name=specification.name,
        x=specification.x,
        y=specification.y,
        color=specification.color,
        location=f"{location}.world_object",
        entry=entry,
        issues=issues,
    )
    for field, value in (
        ("when_near", specification.when_near),
        ("when_interacted", specification.when_interacted),
    ):
        if value is not None and not _is_nonblank_text(value):
            field_location = f"{location}.world_object.{field}"
            issues.append(
                _issue(
                    RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} must be non-whitespace text when present.",
                    field_location,
                    entry=entry,
                )
            )
    _validate_asset(entry.asset_reference, f"{location}.asset_reference", entry, issues)


def _target_compatibility_issues(
    target: object,
    entries: tuple[object, ...],
) -> tuple[
    list[RegistrationApplicationIssue],
    bool | None,
    bool | None,
    dict[str, bool],
]:
    issues: list[RegistrationApplicationIssue] = []
    try:
        target_is_compatible = isinstance(target, StudentAPIRegistrationTarget)
    except Exception:
        target_is_compatible = False
    if not target_is_compatible:
        return (
            [
                _issue(
                    RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE,
                    "target must satisfy the Student API registration target contract.",
                    "target",
                )
            ],
            None,
            None,
            {},
        )

    def query(method_name: str, location: str) -> bool | None:
        try:
            value = getattr(target, method_name)()
        except Exception:
            issues.append(
                _issue(
                    RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE,
                    f"{location} could not provide deterministic target state.",
                    location,
                )
            )
            return None
        if not isinstance(value, bool):
            issues.append(
                _issue(
                    RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE,
                    f"{location} must return a boolean.",
                    location,
                )
            )
            return None
        return value

    has_character = query("has_character", "target.has_character")
    has_world_object = query("has_world_object", "target.has_world_object")
    contains: dict[str, bool] = {}
    for entry in entries:
        qualified_id = getattr(entry, "qualified_id", None)
        if not isinstance(qualified_id, str) or qualified_id in contains:
            continue
        try:
            value = target.contains_registration(qualified_id)
        except Exception:
            issues.append(
                _issue(
                    RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE,
                    "target.contains_registration could not provide deterministic target state.",
                    "target.contains_registration",
                )
            )
            continue
        if not isinstance(value, bool):
            issues.append(
                _issue(
                    RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE,
                    "target.contains_registration must return a boolean.",
                    "target.contains_registration",
                )
            )
            continue
        contains[qualified_id] = value
    return issues, has_character, has_world_object, contains


def _preflight(
    plan: StudentAPIRegistrationPlan | None,
    target: StudentAPIRegistrationTarget | None,
) -> tuple[RegistrationApplicationIssue, ...]:
    input_issues: list[RegistrationApplicationIssue] = []
    target_issues: list[RegistrationApplicationIssue] = []
    plan_issues: list[RegistrationApplicationIssue] = []
    entry_issues: list[RegistrationApplicationIssue] = []

    if not isinstance(plan, StudentAPIRegistrationPlan):
        input_issues.append(
            _issue(
                RegistrationApplicationIssueCode.PLAN_REQUIRED,
                "plan must be a StudentAPIRegistrationPlan.",
                "plan",
            )
        )
    if target is None:
        input_issues.append(
            _issue(
                RegistrationApplicationIssueCode.TARGET_REQUIRED,
                "target must be supplied explicitly.",
                "target",
            )
        )
    if input_issues:
        return tuple(input_issues)

    assert plan is not None
    assert target is not None
    entries = plan.entries if isinstance(plan.entries, tuple) else ()
    target_state = _target_compatibility_issues(target, entries)
    target_issues.extend(target_state[0])
    target_has_character, target_has_world_object, target_contains = target_state[1:]

    provenance = _validate_provenance(plan.provenance, plan_issues)
    if not isinstance(plan.entries, tuple) or not plan.entries:
        plan_issues.append(
            _issue(
                RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
                "plan.entries must be a non-empty immutable tuple.",
                "plan.entries",
            )
        )
        return (*target_issues, *plan_issues)

    seen_qualified_ids: set[str] = set()
    planned_characters = 0
    planned_world_objects = 0
    for index, candidate in enumerate(plan.entries):
        location = f"entries[{index}]"
        cardinality_issue: RegistrationApplicationIssue | None = None
        if type(candidate) is CharacterRegistration:
            entry = candidate
            planned_characters += 1
            if target_has_character is True or planned_characters > 1:
                cardinality_issue = _issue(
                    RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
                    (
                        "Student API v0.1 targets accept at most one character "
                        "and never replace an existing character."
                    ),
                    location,
                    entry=entry,
                )
            validator = _validate_character_entry
        elif type(candidate) is WorldObjectRegistration:
            entry = candidate
            planned_world_objects += 1
            if target_has_world_object is True or planned_world_objects > 1:
                cardinality_issue = _issue(
                    RegistrationApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
                    (
                        "Student API v0.1 targets accept at most one world object "
                        "and never replace an existing object."
                    ),
                    location,
                    entry=entry,
                )
            validator = _validate_world_object_entry
        else:
            entry_issues.append(
                _issue(
                    RegistrationApplicationIssueCode.ENTRY_TYPE_UNSUPPORTED,
                    f"{location} must be a supported registration entry type.",
                    location,
                    entry=candidate,
                )
            )
            continue

        if entry.provenance != provenance:
            entry_issues.append(
                _issue(
                    RegistrationApplicationIssueCode.ENTRY_PROVENANCE_MISMATCH,
                    f"{location}.provenance must match plan.provenance.",
                    f"{location}.provenance",
                    entry=entry,
                )
            )
        _validate_identity(entry, provenance, location, entry_issues)
        validator(entry, location, entry_issues)

        qualified_id = entry.qualified_id
        if isinstance(qualified_id, str):
            if qualified_id in seen_qualified_ids:
                entry_issues.append(
                    _issue(
                        RegistrationApplicationIssueCode.ENTRY_DUPLICATE,
                        f"{location}.qualified_id duplicates an earlier plan entry.",
                        f"{location}.qualified_id",
                        entry=entry,
                    )
                )
            else:
                seen_qualified_ids.add(qualified_id)
            if target_contains.get(qualified_id) is True:
                entry_issues.append(
                    _issue(
                        RegistrationApplicationIssueCode.TARGET_DUPLICATE,
                        f'Target registration "{qualified_id}" already exists.',
                        f"{location}.qualified_id",
                        entry=entry,
                    )
                )
        if cardinality_issue is not None:
            entry_issues.append(cardinality_issue)

    return (*target_issues, *plan_issues, *entry_issues)


def _stage_entry(entry: StudentAPIRegistrationEntry) -> Character | Object:
    if isinstance(entry, CharacterRegistration):
        spec = entry.character
        return Character(name=spec.name, x=spec.x, y=spec.y, color=spec.color)

    spec = entry.world_object
    world_object = Object(name=spec.name, x=spec.x, y=spec.y, color=spec.color)
    if spec.when_near is not None:
        world_object.when_near(spec.when_near)
    if spec.when_interacted is not None:
        world_object.when_interacted(spec.when_interacted)
    return world_object


def _applied_metadata(entry: StudentAPIRegistrationEntry) -> AppliedRegistration:
    registration_type = (
        RegistrationType.CHARACTER
        if isinstance(entry, CharacterRegistration)
        else RegistrationType.WORLD_OBJECT
    )
    return AppliedRegistration(
        qualified_id=entry.qualified_id,
        contribution_id=entry.contribution_id,
        provenance=entry.provenance,
        registration_type=registration_type,
        asset_reference=entry.asset_reference,
    )


def _add_to_target(
    target: StudentAPIRegistrationTarget,
    entry: StudentAPIRegistrationEntry,
    instance: Character | Object,
) -> None:
    if isinstance(entry, CharacterRegistration):
        assert isinstance(instance, Character)
        target.add_character(entry.qualified_id, instance)
    else:
        assert isinstance(instance, Object)
        target.add_world_object(entry.qualified_id, instance)


def _remove_from_target(
    target: StudentAPIRegistrationTarget,
    entry: StudentAPIRegistrationEntry,
    instance: Character | Object,
) -> None:
    if isinstance(entry, CharacterRegistration):
        assert isinstance(instance, Character)
        target.remove_character(entry.qualified_id, instance)
    else:
        assert isinstance(instance, Object)
        target.remove_world_object(entry.qualified_id, instance)


def apply_student_api_registration_plan(
    plan: StudentAPIRegistrationPlan | None,
    target: StudentAPIRegistrationTarget | None,
) -> RegistrationApplicationResult:
    """Apply one valid plan to an explicitly supplied target transactionally.

    Preflight consumes only immutable in-memory values and target state.
    Student API instances are staged only after all predictable issues pass.
    Commit follows plan order; the first add failure triggers reverse-order
    rollback of only entries committed by this transaction.

    Args:
        plan: Immutable registration plan produced by the planning layer.
        target: Explicit compatible target with one character and one
            world-object slot.

    Returns:
        Immutable applied metadata or deterministic failure diagnostics.
    """
    preflight_issues = _preflight(plan, target)
    if preflight_issues:
        return RegistrationApplicationResult(
            state=RegistrationApplicationState.NOT_APPLIED,
            issues=preflight_issues,
        )

    assert plan is not None
    assert target is not None
    staged: list[tuple[StudentAPIRegistrationEntry, Character | Object]] = []
    construction_issues: list[RegistrationApplicationIssue] = []
    for index, entry in enumerate(plan.entries):
        try:
            instance = _stage_entry(entry)
        except Exception:
            construction_issues.append(
                _issue(
                    RegistrationApplicationIssueCode.INSTANCE_CONSTRUCTION_FAILED,
                    f"entries[{index}] could not construct a compatible Student API instance.",
                    f"entries[{index}]",
                    entry=entry,
                )
            )
            continue
        staged.append((entry, instance))

    if construction_issues:
        return RegistrationApplicationResult(
            state=RegistrationApplicationState.NOT_APPLIED,
            issues=tuple(construction_issues),
        )

    committed: list[tuple[StudentAPIRegistrationEntry, Character | Object]] = []
    application_issue: RegistrationApplicationIssue | None = None
    for index, (entry, instance) in enumerate(staged):
        try:
            _add_to_target(target, entry, instance)
        except Exception:
            application_issue = _issue(
                RegistrationApplicationIssueCode.TARGET_ADD_FAILED,
                f'Target rejected registration "{entry.qualified_id}" during commit.',
                f"entries[{index}]",
                entry=entry,
            )
            break
        committed.append((entry, instance))

    if application_issue is None:
        return RegistrationApplicationResult(
            state=RegistrationApplicationState.APPLIED,
            applied=tuple(_applied_metadata(entry) for entry, _ in committed),
        )

    rollback_issues: list[RegistrationApplicationIssue] = []
    unreverted: list[str] = []
    for entry, instance in reversed(committed):
        try:
            _remove_from_target(target, entry, instance)
        except Exception:
            rollback_issues.append(
                _issue(
                    RegistrationApplicationIssueCode.TARGET_REMOVE_FAILED,
                    f'Target could not remove registration "{entry.qualified_id}" during rollback.',
                    "rollback",
                    entry=entry,
                )
            )
            unreverted.append(entry.qualified_id)

    state = (
        RegistrationApplicationState.ROLLBACK_INCOMPLETE
        if rollback_issues
        else RegistrationApplicationState.ROLLED_BACK
    )
    return RegistrationApplicationResult(
        state=state,
        issues=(application_issue, *rollback_issues),
        unreverted_qualified_ids=tuple(unreverted),
    )
