"""Pure compatibility and collision preflight for ordered package selections."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath

from explore._colors import valid_color_names
from explore.packages.contribution_models import (
    PackageAssetReference,
    PackageProvenance,
)
from explore.packages.package_set_models import (
    PackageSelection,
    PackageSetIssue,
    PackageSetIssueCode,
    PackageSetPlan,
    PackageSetPlanResult,
    SelectedPackagePlan,
)
from explore.packages.policy import (
    SUPPORTED_STUDENT_API_VERSION,
    is_valid_identifier,
    is_valid_semantic_version,
)
from explore.packages.registration_models import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    StudentAPIRegistrationEntry,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    WorldObjectToggleRegistrationSpec,
)

_VALID_COLORS = frozenset(valid_color_names())


def _safe_qualified_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    package_id, separator, contribution_id = value.partition(":")
    if separator and is_valid_identifier(package_id) and is_valid_identifier(contribution_id):
        return value
    return None


def _issue(
    code: PackageSetIssueCode,
    message: str,
    location: str,
    *,
    package_index: int | None = None,
    package_id: object | None = None,
    entry_index: int | None = None,
    entry: object | None = None,
) -> PackageSetIssue:
    qualified_id = _safe_qualified_id(getattr(entry, "qualified_id", None))
    return PackageSetIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id if isinstance(package_id, str) else None,
        package_index=package_index,
        qualified_id=qualified_id,
        entry_index=entry_index,
    )


def _is_nonblank_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_coordinate(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_asset(
    asset: object,
    *,
    location: str,
    package_index: int,
    package_id: object,
    entry_index: int,
    entry: CharacterRegistration | WorldObjectRegistration,
    issues: list[PackageSetIssue],
) -> None:
    if asset is None:
        return
    path = (
        PurePosixPath(asset.path)
        if isinstance(asset, PackageAssetReference) and isinstance(asset.path, str)
        else None
    )
    if (
        not isinstance(asset, PackageAssetReference)
        or not isinstance(asset.id, str)
        or not is_valid_identifier(asset.id)
        or asset.type != "image"
        or path is None
        or not asset.path.strip()
        or "\\" in asset.path
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix.lower() != ".png"
    ):
        issues.append(
            _issue(
                PackageSetIssueCode.ENTRY_VALUE_INVALID,
                f"{location} must contain valid package-relative image metadata.",
                location,
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
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
    package_index: int,
    package_id: object,
    entry_index: int,
    entry: CharacterRegistration | WorldObjectRegistration,
    issues: list[PackageSetIssue],
) -> None:
    checks = (
        ("name", _is_nonblank_text(name), "non-whitespace text"),
        ("x", _is_coordinate(x), "a whole number of 0 or greater"),
        ("y", _is_coordinate(y), "a whole number of 0 or greater"),
        ("color", isinstance(color, str) and color in _VALID_COLORS, "a Student API v0.1 colour"),
    )
    for field, valid, requirement in checks:
        if valid:
            continue
        field_location = f"{location}.{field}"
        issues.append(
            _issue(
                PackageSetIssueCode.ENTRY_VALUE_INVALID,
                f"{field_location} must be {requirement}.",
                field_location,
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
                entry=entry,
            )
        )


def _valid_toggle(value: object, *, off_color: object) -> bool:
    return value is None or (
        isinstance(value, WorldObjectToggleRegistrationSpec)
        and isinstance(value.off_color, str)
        and value.off_color in _VALID_COLORS
        and isinstance(value.on_color, str)
        and value.on_color in _VALID_COLORS
        and value.off_color != value.on_color
        and off_color == value.off_color
    )


def _validate_entry_value(
    entry: CharacterRegistration | WorldObjectRegistration,
    *,
    location: str,
    package_index: int,
    package_id: object,
    entry_index: int,
    issues: list[PackageSetIssue],
) -> None:
    if type(entry) is CharacterRegistration:
        specification = entry.character
        if not isinstance(specification, CharacterRegistrationSpec):
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{location}.character must be a character registration specification.",
                    f"{location}.character",
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
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
            package_index=package_index,
            package_id=package_id,
            entry_index=entry_index,
            entry=entry,
            issues=issues,
        )
        if specification.greeting is not None and not _is_nonblank_text(specification.greeting):
            field_location = f"{location}.character.greeting"
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} must be non-whitespace text when present.",
                    field_location,
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
                    entry=entry,
                )
            )
        if specification.conversation is not None and not (
            isinstance(specification.conversation, tuple)
            and 2 <= len(specification.conversation) <= 3
            and all(_is_nonblank_text(line) for line in specification.conversation)
        ):
            field_location = f"{location}.character.conversation"
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} must contain exactly 2 or 3 nonblank lines.",
                    field_location,
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
                    entry=entry,
                )
            )
        if specification.greeting is not None and specification.conversation is not None:
            field_location = f"{location}.character.conversation"
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} cannot be combined with greeting.",
                    field_location,
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
                    entry=entry,
                )
            )
    else:
        specification = entry.world_object
        if not isinstance(specification, WorldObjectRegistrationSpec):
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{location}.world_object must be a world-object registration specification.",
                    f"{location}.world_object",
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
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
            package_index=package_index,
            package_id=package_id,
            entry_index=entry_index,
            entry=entry,
            issues=issues,
        )
        for field, value in (
            ("when_near", specification.when_near),
            ("when_interacted", specification.when_interacted),
        ):
            if value is None or _is_nonblank_text(value):
                continue
            field_location = f"{location}.world_object.{field}"
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} must be non-whitespace text when present.",
                    field_location,
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
                    entry=entry,
                )
            )
        if not _valid_toggle(specification.toggle, off_color=specification.color):
            field_location = f"{location}.world_object.toggle"
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} must retain distinct supported off and on colors.",
                    field_location,
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
                    entry=entry,
                )
            )
        if specification.toggle is not None and entry.asset_reference is not None:
            field_location = f"{location}.asset_reference"
            issues.append(
                _issue(
                    PackageSetIssueCode.ENTRY_VALUE_INVALID,
                    f"{field_location} cannot be combined with toggle metadata.",
                    field_location,
                    package_index=package_index,
                    package_id=package_id,
                    entry_index=entry_index,
                    entry=entry,
                )
            )
    _validate_asset(
        entry.asset_reference,
        location=f"{location}.asset_reference",
        package_index=package_index,
        package_id=package_id,
        entry_index=entry_index,
        entry=entry,
        issues=issues,
    )


def _validate_provenance(
    provenance: object,
    *,
    selection: PackageSelection,
    package_index: int,
    issues: list[PackageSetIssue],
) -> PackageProvenance | None:
    location = f"selections[{package_index}].registration_plan.provenance"
    if not isinstance(provenance, PackageProvenance):
        issues.append(
            _issue(
                PackageSetIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                f"{location} must be package provenance.",
                location,
                package_index=package_index,
                package_id=selection.package_id,
            )
        )
        return None

    valid_identity = (
        isinstance(provenance.package_id, str)
        and is_valid_identifier(provenance.package_id)
        and isinstance(provenance.package_version, str)
        and is_valid_semantic_version(provenance.package_version)
    )
    if (
        not valid_identity
        or provenance.package_id != selection.package_id
        or provenance.package_version != selection.package_version
    ):
        issues.append(
            _issue(
                PackageSetIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                (
                    "The selection pin and registration-plan provenance must describe "
                    "the same package."
                ),
                location,
                package_index=package_index,
                package_id=selection.package_id,
            )
        )

    if provenance.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        issues.append(
            _issue(
                PackageSetIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (f"{location}.student_api_version must be " f'"{SUPPORTED_STUDENT_API_VERSION}".'),
                f"{location}.student_api_version",
                package_index=package_index,
                package_id=selection.package_id,
            )
        )
    return provenance


def _validate_entry(
    candidate: object,
    *,
    provenance: PackageProvenance | None,
    package_index: int,
    package_id: object,
    entry_index: int,
    issues: list[PackageSetIssue],
) -> StudentAPIRegistrationEntry | None:
    location = f"selections[{package_index}].registration_plan.entries[{entry_index}]"
    if type(candidate) not in (CharacterRegistration, WorldObjectRegistration):
        issues.append(
            _issue(
                PackageSetIssueCode.ENTRY_TYPE_UNSUPPORTED,
                f"{location} must be a supported registration entry type.",
                location,
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
                entry=candidate,
            )
        )
        return None

    entry = candidate
    if entry.provenance != provenance:
        issues.append(
            _issue(
                PackageSetIssueCode.ENTRY_PROVENANCE_MISMATCH,
                f"{location}.provenance must match the containing registration plan.",
                f"{location}.provenance",
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
                entry=entry,
            )
        )

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
                PackageSetIssueCode.ENTRY_IDENTITY_INVALID,
                (
                    f"{location}.qualified_id must match the plan package ID "
                    "and a valid local contribution ID."
                ),
                f"{location}.qualified_id",
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
                entry=entry,
            )
        )

    _validate_entry_value(
        entry,
        location=location,
        package_index=package_index,
        package_id=package_id,
        entry_index=entry_index,
        issues=issues,
    )
    return entry


def _build_package_set_plan(
    selections: Iterable[PackageSelection],
    *,
    maximum_characters: int | None,
    maximum_world_objects: int | None,
    cardinality_contract: str,
) -> PackageSetPlanResult:
    """Preflight exact package selections under an explicit cardinality policy.

    Caller-provided package order is preserved. Entries are flattened by that
    package order and then by each registration plan's existing entry order.
    Any issue makes the result atomic: ``plan`` is ``None`` and no partial
    selected-package or entry output is returned.

    Args:
        selections: Ordered package-version pins and completed registration plans.

    Returns:
        A complete immutable package-set plan or deterministic preflight issues.

    Raises:
        TypeError: If *selections* is not an iterable package-selection collection.
    """
    if isinstance(selections, (str, bytes)):
        raise TypeError("selections must be an iterable of PackageSelection values")
    try:
        ordered_selections = tuple(selections)
    except TypeError as error:
        raise TypeError("selections must be an iterable of PackageSelection values") from error

    if not ordered_selections:
        return PackageSetPlanResult(
            plan=None,
            issues=(
                _issue(
                    PackageSetIssueCode.PACKAGE_SET_REQUIRED,
                    "selections must contain at least one package selection.",
                    "selections",
                ),
            ),
        )

    selection_issues: list[PackageSetIssue] = []
    cross_selection_issues: list[PackageSetIssue] = []
    selected_packages: list[SelectedPackagePlan] = []
    flattened: list[tuple[int, int, object, StudentAPIRegistrationEntry]] = []
    package_identity: list[tuple[int, str, object]] = []
    student_api_versions: list[tuple[int, object, str]] = []

    for package_index, candidate in enumerate(ordered_selections):
        selection_location = f"selections[{package_index}]"
        if not isinstance(candidate, PackageSelection):
            selection_issues.append(
                _issue(
                    PackageSetIssueCode.SELECTION_INVALID_TYPE,
                    f"{selection_location} must be a PackageSelection.",
                    selection_location,
                    package_index=package_index,
                )
            )
            continue

        selection = candidate
        package_id = selection.package_id
        package_version = selection.package_version
        package_id_valid = isinstance(package_id, str) and is_valid_identifier(package_id)
        package_version_valid = isinstance(package_version, str) and is_valid_semantic_version(
            package_version
        )
        if not package_id_valid:
            selection_issues.append(
                _issue(
                    PackageSetIssueCode.PACKAGE_ID_INVALID,
                    f"{selection_location}.package_id must be a valid Explorer Package identifier.",
                    f"{selection_location}.package_id",
                    package_index=package_index,
                    package_id=package_id,
                )
            )
        if not package_version_valid:
            selection_issues.append(
                _issue(
                    PackageSetIssueCode.PACKAGE_VERSION_INVALID,
                    f"{selection_location}.package_version must be an exact Semantic Version.",
                    f"{selection_location}.package_version",
                    package_index=package_index,
                    package_id=package_id,
                )
            )
        if package_id_valid:
            package_identity.append((package_index, package_id, package_version))

        registration_plan = selection.registration_plan
        if not isinstance(registration_plan, StudentAPIRegistrationPlan):
            selection_issues.append(
                _issue(
                    PackageSetIssueCode.REGISTRATION_PLAN_INVALID,
                    f"{selection_location}.registration_plan must be a StudentAPIRegistrationPlan.",
                    f"{selection_location}.registration_plan",
                    package_index=package_index,
                    package_id=package_id,
                )
            )
            continue

        provenance = _validate_provenance(
            registration_plan.provenance,
            selection=selection,
            package_index=package_index,
            issues=selection_issues,
        )
        if provenance is not None and isinstance(provenance.student_api_version, str):
            student_api_versions.append((package_index, package_id, provenance.student_api_version))

        entries = registration_plan.entries
        if not isinstance(entries, tuple) or not entries:
            selection_issues.append(
                _issue(
                    PackageSetIssueCode.REGISTRATION_PLAN_INVALID,
                    f"{selection_location}.registration_plan.entries must be a non-empty tuple.",
                    f"{selection_location}.registration_plan.entries",
                    package_index=package_index,
                    package_id=package_id,
                )
            )
            continue

        selected_packages.append(
            SelectedPackagePlan(
                package_id=package_id,
                package_version=package_version,
                provenance=registration_plan.provenance,
                registration_plan=registration_plan,
            )
        )
        for entry_index, entry_candidate in enumerate(entries):
            entry = _validate_entry(
                entry_candidate,
                provenance=provenance,
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
                issues=selection_issues,
            )
            if entry is not None:
                flattened.append((package_index, entry_index, package_id, entry))

    seen_packages: dict[str, tuple[int, object]] = {}
    for package_index, package_id, package_version in package_identity:
        earlier = seen_packages.get(package_id)
        if earlier is None:
            seen_packages[package_id] = (package_index, package_version)
            continue
        earlier_index, earlier_version = earlier
        if package_version == earlier_version:
            code = PackageSetIssueCode.PACKAGE_SELECTION_DUPLICATE
            message = (
                f'Package "{package_id}" is selected more than once; '
                f"the first selection is selections[{earlier_index}]."
            )
        else:
            code = PackageSetIssueCode.PACKAGE_VERSION_CONFLICT
            message = (
                f'Package "{package_id}" selects conflicting exact versions; '
                f"the first selection is selections[{earlier_index}]."
            )
        cross_selection_issues.append(
            _issue(
                code,
                message,
                f"selections[{package_index}].package_version",
                package_index=package_index,
                package_id=package_id,
            )
        )

    if student_api_versions:
        first_index, _, first_version = student_api_versions[0]
        for package_index, package_id, version in student_api_versions[1:]:
            if version == first_version:
                continue
            cross_selection_issues.append(
                _issue(
                    PackageSetIssueCode.STUDENT_API_VERSION_MISMATCH,
                    (
                        "Selected registration plans must target one exact Student API version; "
                        f"selections[{first_index}] establishes a different version."
                    ),
                    f"selections[{package_index}].registration_plan.provenance.student_api_version",
                    package_index=package_index,
                    package_id=package_id,
                )
            )

    seen_qualified_ids: dict[str, tuple[int, int]] = {}
    for package_index, entry_index, package_id, entry in flattened:
        qualified_id = entry.qualified_id
        if not isinstance(qualified_id, str) or not qualified_id:
            continue
        earlier = seen_qualified_ids.get(qualified_id)
        if earlier is None:
            seen_qualified_ids[qualified_id] = (package_index, entry_index)
            continue
        earlier_package, earlier_entry = earlier
        cross_selection_issues.append(
            _issue(
                PackageSetIssueCode.ENTRY_IDENTITY_DUPLICATE,
                (
                    "A registration identity duplicates "
                    f"selections[{earlier_package}].registration_plan.entries[{earlier_entry}]."
                ),
                f"selections[{package_index}].registration_plan.entries[{entry_index}].qualified_id",
                package_index=package_index,
                package_id=package_id,
                entry_index=entry_index,
                entry=entry,
            )
        )

    character_count = sum(type(item[3]) is CharacterRegistration for item in flattened)
    world_object_count = sum(type(item[3]) is WorldObjectRegistration for item in flattened)
    character_limit_exceeded = (
        maximum_characters is not None and character_count > maximum_characters
    )
    world_object_limit_exceeded = (
        maximum_world_objects is not None and world_object_count > maximum_world_objects
    )
    if character_limit_exceeded or world_object_limit_exceeded:
        for package_index, entry_index, package_id, entry in flattened:
            location = f"selections[{package_index}].registration_plan.entries[{entry_index}]"
            if type(entry) is CharacterRegistration and character_limit_exceeded:
                cross_selection_issues.append(
                    _issue(
                        PackageSetIssueCode.CHARACTER_CARDINALITY_EXCEEDED,
                        (
                            f"{cardinality_contract} at most "
                            f"{maximum_characters} character; "
                            f"this set contains {character_count}."
                        ),
                        location,
                        package_index=package_index,
                        package_id=package_id,
                        entry_index=entry_index,
                        entry=entry,
                    )
                )
            elif type(entry) is WorldObjectRegistration and world_object_limit_exceeded:
                cross_selection_issues.append(
                    _issue(
                        PackageSetIssueCode.WORLD_OBJECT_CARDINALITY_EXCEEDED,
                        (
                            f"{cardinality_contract} at most "
                            f"{maximum_world_objects} world object; "
                            f"this set contains {world_object_count}."
                        ),
                        location,
                        package_index=package_index,
                        package_id=package_id,
                        entry_index=entry_index,
                        entry=entry,
                    )
                )

    issues = (*selection_issues, *cross_selection_issues)
    if issues:
        return PackageSetPlanResult(plan=None, issues=issues)

    return PackageSetPlanResult(
        plan=PackageSetPlan(
            student_api_version=SUPPORTED_STUDENT_API_VERSION,
            packages=tuple(selected_packages),
            entries=tuple(item[3] for item in flattened),
        ),
        issues=(),
    )


def build_package_set_plan(
    selections: Iterable[PackageSelection],
) -> PackageSetPlanResult:
    """Build one unchanged Student API v0.1 package-set plan."""
    return _build_package_set_plan(
        selections,
        maximum_characters=1,
        maximum_world_objects=1,
        cardinality_contract="Student API v0.1 package sets support",
    )
