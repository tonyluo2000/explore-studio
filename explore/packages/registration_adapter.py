"""Pure Loaded Explorer Package to Student API registration planning."""

from __future__ import annotations

from explore._colors import valid_color_names
from explore.packages.contribution_models import (
    LoadedCharacter,
    LoadedCharacterEitherToggleResponse,
    LoadedCharacterToggleResponse,
    LoadedCharacterTwoToggleResponse,
    LoadedExplorerPackage,
    LoadedWorldObject,
    LoadedWorldObjectCounter,
    LoadedWorldObjectToggle,
    PackageAssetReference,
    PackageLoadResult,
    PackageProvenance,
)
from explore.packages.models import Compatibility, PackageMetadata
from explore.packages.policy import (
    SUPPORTED_STUDENT_API_VERSION,
    is_valid_identifier,
    is_valid_semantic_version,
)
from explore.packages.registration_models import (
    CharacterEitherToggleResponseRegistrationSpec,
    CharacterRegistration,
    CharacterRegistrationSpec,
    CharacterToggleResponseRegistrationSpec,
    CharacterTwoToggleResponseRegistrationSpec,
    RegistrationPlanIssue,
    RegistrationPlanIssueCode,
    RegistrationPlanResult,
    StudentAPIRegistrationEntry,
    StudentAPIRegistrationPlan,
    WorldObjectCounterRegistrationSpec,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    WorldObjectToggleRegistrationSpec,
)

_VALID_COLORS = frozenset(valid_color_names())


def _issue(
    code: RegistrationPlanIssueCode,
    message: str,
    location: str,
    *,
    contribution: object | None = None,
    field: str | None = None,
) -> RegistrationPlanIssue:
    qualified_id = getattr(contribution, "qualified_id", None)
    contribution_id = getattr(contribution, "contribution_id", None)
    return RegistrationPlanIssue(
        code=code,
        message=message,
        location=location,
        qualified_id=qualified_id if isinstance(qualified_id, str) else None,
        contribution_id=contribution_id if isinstance(contribution_id, str) else None,
        field=field,
    )


def _is_nonblank_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_coordinate(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_conversation(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and 2 <= len(value) <= 3
        and all(_is_nonblank_text(line) for line in value)
    )


def _valid_respond_to_toggle(value: object) -> bool:
    return value is None or (
        isinstance(value, LoadedCharacterToggleResponse)
        and isinstance(value.object_id, str)
        and is_valid_identifier(value.object_id)
        and _is_nonblank_text(value.when_off)
        and _is_nonblank_text(value.when_on)
    )


def _valid_respond_to_two_toggles(value: object) -> bool:
    return value is None or (
        isinstance(value, LoadedCharacterTwoToggleResponse)
        and isinstance(value.object_ids, tuple)
        and len(value.object_ids) == 2
        and value.object_ids[0] != value.object_ids[1]
        and all(isinstance(item, str) and is_valid_identifier(item) for item in value.object_ids)
        and _is_nonblank_text(value.when_not_all_on)
        and _is_nonblank_text(value.when_all_on)
    )


def _valid_respond_to_either_toggle(value: object) -> bool:
    return value is None or (
        isinstance(value, LoadedCharacterEitherToggleResponse)
        and isinstance(value.object_ids, tuple)
        and len(value.object_ids) == 2
        and value.object_ids[0] != value.object_ids[1]
        and all(isinstance(item, str) and is_valid_identifier(item) for item in value.object_ids)
        and _is_nonblank_text(value.when_both_off)
        and _is_nonblank_text(value.when_either_on)
    )


def _validate_text(
    value: object,
    *,
    contribution: object,
    location: str,
    field: str,
    issues: list[RegistrationPlanIssue],
    optional: bool = False,
) -> None:
    if optional and value is None:
        return
    if not _is_nonblank_text(value):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must contain non-whitespace text.",
                location,
                contribution=contribution,
                field=field,
            )
        )


def _validate_coordinate(
    value: object,
    *,
    contribution: object,
    location: str,
    field: str,
    issues: list[RegistrationPlanIssue],
) -> None:
    if not _is_coordinate(value):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must be a whole number of 0 or greater.",
                location,
                contribution=contribution,
                field=field,
            )
        )


def _validate_color(
    value: object,
    *,
    contribution: object,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> None:
    if not isinstance(value, str) or value not in _VALID_COLORS:
        options = ", ".join(sorted(_VALID_COLORS))
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_COLOR_UNSUPPORTED,
                f"{location} must be a Student API v0.1 colour; choose from: {options}.",
                location,
                contribution=contribution,
                field="color",
            )
        )


def _validate_image(
    value: object,
    *,
    contribution: object,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> None:
    if value is None:
        return
    if not isinstance(value, PackageAssetReference) or value.type != "image":
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_ASSET_TYPE_MISMATCH,
                f'{location} must retain a package asset reference of type "image".',
                location,
                contribution=contribution,
                field="image",
            )
        )
        return
    if not _is_nonblank_text(value.id) or not _is_nonblank_text(value.path):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must retain non-empty package-relative asset identity.",
                location,
                contribution=contribution,
                field="image",
            )
        )


def _validate_toggle(
    value: object,
    *,
    contribution: LoadedWorldObject,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> None:
    if value is None:
        return
    if (
        not isinstance(value, LoadedWorldObjectToggle)
        or not isinstance(value.off_color, str)
        or value.off_color not in _VALID_COLORS
        or not isinstance(value.on_color, str)
        or value.on_color not in _VALID_COLORS
        or value.off_color == value.on_color
        or contribution.color != value.off_color
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must retain distinct supported off and on colors.",
                location,
                contribution=contribution,
                field="toggle",
            )
        )
    if contribution.image is not None:
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} cannot be combined with image metadata.",
                location,
                contribution=contribution,
                field="toggle",
            )
        )


def _validate_counter(
    value: object,
    *,
    contribution: LoadedWorldObject,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> None:
    if value is None:
        return
    if (
        not isinstance(value, LoadedWorldObjectCounter)
        or isinstance(value.goal, bool)
        or not isinstance(value.goal, int)
        or not 2 <= value.goal <= 5
        or not _is_nonblank_text(value.when_goal_reached)
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must retain a goal from 2 through 5 and a nonblank message.",
                location,
                contribution=contribution,
                field="counter",
            )
        )


def _validate_package_provenance(
    package: LoadedExplorerPackage,
    issues: list[RegistrationPlanIssue],
) -> PackageProvenance | None:
    provenance = package.provenance
    if not isinstance(provenance, PackageProvenance):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                "package.provenance must be loaded package provenance.",
                "package.provenance",
            )
        )
        return None

    if provenance.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        issues.append(
            _issue(
                RegistrationPlanIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (
                    "package.provenance.student_api_version must be "
                    f'"{SUPPORTED_STUDENT_API_VERSION}".'
                ),
                "package.provenance.student_api_version",
            )
        )

    metadata = package.metadata
    compatibility = package.compatibility
    metadata_matches = (
        isinstance(metadata, PackageMetadata)
        and isinstance(metadata.id, str)
        and is_valid_identifier(metadata.id)
        and isinstance(metadata.version, str)
        and is_valid_semantic_version(metadata.version)
        and metadata.id == provenance.package_id
        and metadata.version == provenance.package_version
    )
    compatibility_matches = (
        isinstance(compatibility, Compatibility)
        and compatibility.student_api == provenance.student_api_version
    )
    if not metadata_matches or not compatibility_matches:
        issues.append(
            _issue(
                RegistrationPlanIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                "Package metadata, compatibility, and provenance must describe the same package.",
                "package.provenance",
            )
        )
    return provenance


def _validate_contribution_identity(
    contribution: LoadedCharacter | LoadedWorldObject,
    package_provenance: PackageProvenance | None,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> None:
    contribution_id = contribution.contribution_id
    if not isinstance(contribution_id, str) or not is_valid_identifier(contribution_id):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_ID_INVALID,
                f"{location}.contribution_id must be a valid Explorer Package identifier.",
                f"{location}.contribution_id",
                contribution=contribution,
                field="contribution_id",
            )
        )

    provenance = contribution.provenance
    if (
        package_provenance is None
        or not isinstance(provenance, PackageProvenance)
        or provenance != package_provenance
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_PROVENANCE_MISMATCH,
                f"{location}.provenance must match the containing package provenance.",
                f"{location}.provenance",
                contribution=contribution,
                field="provenance",
            )
        )

    qualified_id = contribution.qualified_id
    expected_id = (
        f"{package_provenance.package_id}:{contribution_id}"
        if package_provenance is not None and isinstance(contribution_id, str)
        else None
    )
    if (
        not isinstance(qualified_id, str)
        or not qualified_id
        or expected_id is None
        or qualified_id != expected_id
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_ID_INVALID,
                (
                    f"{location}.qualified_id must match the containing package ID "
                    "and local contribution ID."
                ),
                f"{location}.qualified_id",
                contribution=contribution,
                field="qualified_id",
            )
        )


def _map_character(
    contribution: LoadedCharacter,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> CharacterRegistration:
    _validate_text(
        contribution.name,
        contribution=contribution,
        location=f"{location}.name",
        field="name",
        issues=issues,
    )
    _validate_coordinate(
        contribution.x,
        contribution=contribution,
        location=f"{location}.x",
        field="x",
        issues=issues,
    )
    _validate_coordinate(
        contribution.y,
        contribution=contribution,
        location=f"{location}.y",
        field="y",
        issues=issues,
    )
    _validate_color(
        contribution.color,
        contribution=contribution,
        location=f"{location}.color",
        issues=issues,
    )
    _validate_image(
        contribution.image,
        contribution=contribution,
        location=f"{location}.image",
        issues=issues,
    )
    _validate_text(
        contribution.greeting,
        contribution=contribution,
        location=f"{location}.greeting",
        field="greeting",
        issues=issues,
        optional=True,
    )
    if contribution.conversation is not None and not _is_conversation(contribution.conversation):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location}.conversation must contain exactly 2 or 3 nonblank lines.",
                f"{location}.conversation",
                contribution=contribution,
                field="conversation",
            )
        )
    if contribution.greeting is not None and contribution.conversation is not None:
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location}.conversation cannot be combined with greeting.",
                f"{location}.conversation",
                contribution=contribution,
                field="conversation",
            )
        )
    if not _valid_respond_to_toggle(contribution.respond_to_toggle):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location}.respond_to_toggle must retain one valid package-local conditional.",
                f"{location}.respond_to_toggle",
                contribution=contribution,
                field="respond_to_toggle",
            )
        )
    if contribution.respond_to_toggle is not None and (
        contribution.greeting is not None or contribution.conversation is not None
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location}.respond_to_toggle cannot be combined with greeting or conversation.",
                f"{location}.respond_to_toggle",
                contribution=contribution,
                field="respond_to_toggle",
            )
        )
    if not _valid_respond_to_two_toggles(contribution.respond_to_two_toggles):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                (
                    f"{location}.respond_to_two_toggles must retain exactly two distinct "
                    "package-local toggle IDs and two valid responses."
                ),
                f"{location}.respond_to_two_toggles",
                contribution=contribution,
                field="respond_to_two_toggles",
            )
        )
    if contribution.respond_to_two_toggles is not None and (
        contribution.greeting is not None
        or contribution.conversation is not None
        or contribution.respond_to_toggle is not None
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                (
                    f"{location}.respond_to_two_toggles cannot be combined with greeting, "
                    "conversation, or respond_to_toggle."
                ),
                f"{location}.respond_to_two_toggles",
                contribution=contribution,
                field="respond_to_two_toggles",
            )
        )
    if not _valid_respond_to_either_toggle(contribution.respond_to_either_toggle):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location}.respond_to_either_toggle must retain exactly two distinct "
                "package-local toggle IDs and two valid responses.",
                f"{location}.respond_to_either_toggle",
                contribution=contribution,
                field="respond_to_either_toggle",
            )
        )
    if contribution.respond_to_either_toggle is not None and (
        contribution.greeting is not None
        or contribution.conversation is not None
        or contribution.respond_to_toggle is not None
        or contribution.respond_to_two_toggles is not None
    ):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location}.respond_to_either_toggle cannot be combined with greeting, "
                "conversation, respond_to_toggle, or respond_to_two_toggles.",
                f"{location}.respond_to_either_toggle",
                contribution=contribution,
                field="respond_to_either_toggle",
            )
        )
    conditional = (
        CharacterToggleResponseRegistrationSpec(
            object_id=contribution.respond_to_toggle.object_id,
            when_off=contribution.respond_to_toggle.when_off,
            when_on=contribution.respond_to_toggle.when_on,
        )
        if isinstance(contribution.respond_to_toggle, LoadedCharacterToggleResponse)
        else None
    )
    two_toggle = (
        CharacterTwoToggleResponseRegistrationSpec(
            object_ids=contribution.respond_to_two_toggles.object_ids,
            when_not_all_on=contribution.respond_to_two_toggles.when_not_all_on,
            when_all_on=contribution.respond_to_two_toggles.when_all_on,
        )
        if isinstance(contribution.respond_to_two_toggles, LoadedCharacterTwoToggleResponse)
        else None
    )
    either_toggle = (
        CharacterEitherToggleResponseRegistrationSpec(
            object_ids=contribution.respond_to_either_toggle.object_ids,
            when_both_off=contribution.respond_to_either_toggle.when_both_off,
            when_either_on=contribution.respond_to_either_toggle.when_either_on,
        )
        if isinstance(contribution.respond_to_either_toggle, LoadedCharacterEitherToggleResponse)
        else None
    )
    return CharacterRegistration(
        qualified_id=contribution.qualified_id,
        contribution_id=contribution.contribution_id,
        provenance=contribution.provenance,
        character=CharacterRegistrationSpec(
            name=contribution.name,
            x=contribution.x,
            y=contribution.y,
            color=contribution.color,
            greeting=contribution.greeting,
            conversation=contribution.conversation,
            respond_to_toggle=conditional,
            respond_to_two_toggles=two_toggle,
            respond_to_either_toggle=either_toggle,
        ),
        asset_reference=contribution.image,
    )


def _map_world_object(
    contribution: LoadedWorldObject,
    location: str,
    issues: list[RegistrationPlanIssue],
) -> WorldObjectRegistration:
    toggle = (
        None
        if not isinstance(contribution.toggle, LoadedWorldObjectToggle)
        else WorldObjectToggleRegistrationSpec(
            off_color=contribution.toggle.off_color,
            on_color=contribution.toggle.on_color,
        )
    )
    counter = (
        None
        if not isinstance(contribution.counter, LoadedWorldObjectCounter)
        else WorldObjectCounterRegistrationSpec(
            goal=contribution.counter.goal,
            when_goal_reached=contribution.counter.when_goal_reached,
        )
    )
    _validate_text(
        contribution.name,
        contribution=contribution,
        location=f"{location}.name",
        field="name",
        issues=issues,
    )
    _validate_coordinate(
        contribution.x,
        contribution=contribution,
        location=f"{location}.x",
        field="x",
        issues=issues,
    )
    _validate_coordinate(
        contribution.y,
        contribution=contribution,
        location=f"{location}.y",
        field="y",
        issues=issues,
    )
    _validate_color(
        contribution.color,
        contribution=contribution,
        location=f"{location}.color",
        issues=issues,
    )
    _validate_image(
        contribution.image,
        contribution=contribution,
        location=f"{location}.image",
        issues=issues,
    )
    _validate_toggle(
        contribution.toggle,
        contribution=contribution,
        location=f"{location}.toggle",
        issues=issues,
    )
    _validate_counter(
        contribution.counter,
        contribution=contribution,
        location=f"{location}.counter",
        issues=issues,
    )
    _validate_text(
        contribution.when_near,
        contribution=contribution,
        location=f"{location}.when_near",
        field="when_near",
        issues=issues,
        optional=True,
    )
    _validate_text(
        contribution.when_interacted,
        contribution=contribution,
        location=f"{location}.when_interacted",
        field="when_interacted",
        issues=issues,
        optional=True,
    )
    return WorldObjectRegistration(
        qualified_id=contribution.qualified_id,
        contribution_id=contribution.contribution_id,
        provenance=contribution.provenance,
        world_object=WorldObjectRegistrationSpec(
            name=contribution.name,
            x=contribution.x,
            y=contribution.y,
            color=contribution.color,
            when_near=contribution.when_near,
            when_interacted=contribution.when_interacted,
            toggle=toggle,
            counter=counter,
        ),
        asset_reference=contribution.image,
    )


def build_student_api_registration_plan(
    loaded_package: LoadedExplorerPackage,
) -> RegistrationPlanResult:
    """Build an immutable Student API registration plan without applying it.

    The adapter consumes only already-loaded in-memory models. It performs no
    package I/O, YAML parsing, asset materialization, engine registration, or
    Pygame initialization. Any compatibility issue makes the result atomic:
    ``plan`` is ``None`` and no partial entries are returned.

    Args:
        loaded_package: A successfully loaded Explorer Package.

    Returns:
        A complete immutable plan or deterministic compatibility issues.

    Raises:
        TypeError: If *loaded_package* is not a ``LoadedExplorerPackage``.
    """
    if not isinstance(loaded_package, LoadedExplorerPackage):
        raise TypeError("loaded_package must be a LoadedExplorerPackage")

    issues: list[RegistrationPlanIssue] = []
    provenance = _validate_package_provenance(loaded_package, issues)
    contributions = loaded_package.contributions
    if not isinstance(contributions, tuple):
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                "package.contributions must be an immutable tuple of loaded contributions.",
                "package.contributions",
            )
        )
        return RegistrationPlanResult(plan=None, issues=tuple(issues))
    if not contributions:
        issues.append(
            _issue(
                RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
                "package.contributions must contain at least one loaded contribution.",
                "package.contributions",
            )
        )

    entries: list[StudentAPIRegistrationEntry] = []
    seen_qualified_ids: set[str] = set()

    contributions_by_id: dict[str, list[LoadedCharacter | LoadedWorldObject]] = {}
    for contribution in contributions:
        if type(contribution) in (LoadedCharacter, LoadedWorldObject) and isinstance(
            contribution.contribution_id, str
        ):
            contributions_by_id.setdefault(contribution.contribution_id, []).append(contribution)

    for index, contribution in enumerate(contributions):
        location = f"contributions[{index}]"
        if type(contribution) is LoadedCharacter:
            mapper = _map_character
        elif type(contribution) is LoadedWorldObject:
            mapper = _map_world_object
        else:
            issues.append(
                _issue(
                    RegistrationPlanIssueCode.CONTRIBUTION_TYPE_UNSUPPORTED,
                    f"{location} must be a supported loaded contribution type.",
                    location,
                    contribution=contribution,
                )
            )
            continue

        _validate_contribution_identity(
            contribution,
            provenance,
            location,
            issues,
        )
        entry = mapper(contribution, location, issues)
        entries.append(entry)

        if type(contribution) is LoadedCharacter and isinstance(
            contribution.respond_to_toggle, LoadedCharacterToggleResponse
        ):
            reference = contribution.respond_to_toggle
            matches = contributions_by_id.get(reference.object_id, [])
            target = matches[0] if len(matches) == 1 else None
            if (
                len(matches) != 1
                or not isinstance(target, LoadedWorldObject)
                or target.toggle is None
            ):
                issues.append(
                    _issue(
                        RegistrationPlanIssueCode.CONDITIONAL_REFERENCE_INVALID,
                        (
                            f"{location}.respond_to_toggle.object_id must resolve exactly to "
                            "one toggle world object in the containing package."
                        ),
                        f"{location}.respond_to_toggle.object_id",
                        contribution=contribution,
                        field="object_id",
                    )
                )

        if (
            type(contribution) is LoadedCharacter
            and isinstance(contribution.respond_to_two_toggles, LoadedCharacterTwoToggleResponse)
            and _valid_respond_to_two_toggles(contribution.respond_to_two_toggles)
        ):
            for object_id in contribution.respond_to_two_toggles.object_ids:
                matches = contributions_by_id.get(object_id, [])
                target = matches[0] if len(matches) == 1 else None
                if (
                    len(matches) != 1
                    or not isinstance(target, LoadedWorldObject)
                    or target.toggle is None
                ):
                    issues.append(
                        _issue(
                            RegistrationPlanIssueCode.CONDITIONAL_REFERENCE_INVALID,
                            (
                                f"{location}.respond_to_two_toggles.object_ids must each "
                                "resolve exactly to one toggle world object in the "
                                "containing package."
                            ),
                            f"{location}.respond_to_two_toggles.object_ids",
                            contribution=contribution,
                            field="object_ids",
                        )
                    )

        if (
            type(contribution) is LoadedCharacter
            and isinstance(
                contribution.respond_to_either_toggle, LoadedCharacterEitherToggleResponse
            )
            and _valid_respond_to_either_toggle(contribution.respond_to_either_toggle)
        ):
            for object_id in contribution.respond_to_either_toggle.object_ids:
                matches = contributions_by_id.get(object_id, [])
                target = matches[0] if len(matches) == 1 else None
                if (
                    len(matches) != 1
                    or not isinstance(target, LoadedWorldObject)
                    or target.toggle is None
                ):
                    issues.append(
                        _issue(
                            RegistrationPlanIssueCode.CONDITIONAL_REFERENCE_INVALID,
                            f"{location}.respond_to_either_toggle.object_ids must each resolve "
                            "exactly to one toggle world object in the containing package.",
                            f"{location}.respond_to_either_toggle.object_ids",
                            contribution=contribution,
                            field="object_ids",
                        )
                    )

        qualified_id = contribution.qualified_id
        if isinstance(qualified_id, str):
            if qualified_id in seen_qualified_ids:
                issues.append(
                    _issue(
                        RegistrationPlanIssueCode.CONTRIBUTION_ID_DUPLICATE,
                        f"{location}.qualified_id duplicates an earlier registration identity.",
                        f"{location}.qualified_id",
                        contribution=contribution,
                        field="qualified_id",
                    )
                )
            else:
                seen_qualified_ids.add(qualified_id)

    if issues or provenance is None:
        return RegistrationPlanResult(plan=None, issues=tuple(issues))
    return RegistrationPlanResult(
        plan=StudentAPIRegistrationPlan(
            provenance=provenance,
            entries=tuple(entries),
        ),
        issues=(),
    )


def plan_loaded_explorer_package(
    load_result: PackageLoadResult,
) -> RegistrationPlanResult:
    """Plan a successful loader result while retaining failed-load diagnostics.

    Args:
        load_result: Result previously returned by ``load_explorer_package``.

    Returns:
        The delegated registration result on loader success. A failed or
        incomplete loader result produces no plan and retains all original
        loader diagnostics.

    Raises:
        TypeError: If *load_result* is not a ``PackageLoadResult``.
    """
    if not isinstance(load_result, PackageLoadResult):
        raise TypeError("load_result must be a PackageLoadResult")
    if load_result.package is None:
        return RegistrationPlanResult(
            plan=None,
            issues=(
                _issue(
                    RegistrationPlanIssueCode.LOADED_PACKAGE_REQUIRED,
                    "A complete loaded package is required before registration planning.",
                    "load_result.package",
                ),
            ),
            loader_diagnostics=load_result.all_issues,
        )
    if not load_result.is_loaded:
        return RegistrationPlanResult(
            plan=None,
            issues=(
                _issue(
                    RegistrationPlanIssueCode.LOAD_RESULT_NOT_LOADED,
                    "Registration planning requires a successful package load result.",
                    "load_result",
                ),
            ),
            loader_diagnostics=load_result.all_issues,
        )
    return build_student_api_registration_plan(load_result.package)
