"""Pure construction and validation for class-world configuration v0.1."""

from __future__ import annotations

from pathlib import PurePosixPath

from explore._colors import valid_color_names
from explore.packages.class_world_configuration_models import (
    CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH,
    COHORT_DISPLAY_NAME_MAX_LENGTH,
    SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationIssue,
    ClassWorldConfigurationIssueCode,
    ClassWorldConfigurationResult,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
)
from explore.packages.contribution_models import PackageAssetReference, PackageProvenance
from explore.packages.package_set_models import (
    PackageSetPlan,
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


def _issue(
    code: ClassWorldConfigurationIssueCode,
    message: str,
    location: str,
    *,
    package_id: object | None = None,
    package_index: int | None = None,
    field: str | None = None,
) -> ClassWorldConfigurationIssue:
    return ClassWorldConfigurationIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id if isinstance(package_id, str) else None,
        package_index=package_index,
        field=field,
    )


def _is_valid_display_name(value: object, maximum: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= maximum


def _validate_metadata(
    spec: ClassWorldConfigurationSpec,
) -> list[ClassWorldConfigurationIssue]:
    issues: list[ClassWorldConfigurationIssue] = []
    if spec.schema_version != SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.SCHEMA_VERSION_UNSUPPORTED,
                (
                    "spec.schema_version must be exactly "
                    f'"{SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION}".'
                ),
                "spec.schema_version",
                field="schema_version",
            )
        )
    if not isinstance(spec.class_world_id, str) or not is_valid_identifier(spec.class_world_id):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.CLASS_WORLD_ID_INVALID,
                "spec.class_world_id must be a valid lower-kebab-case identifier.",
                "spec.class_world_id",
                field="class_world_id",
            )
        )
    if not _is_valid_display_name(spec.display_name, CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.CLASS_WORLD_DISPLAY_NAME_INVALID,
                (
                    "spec.display_name must contain non-whitespace text no longer than "
                    f"{CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH} characters."
                ),
                "spec.display_name",
                field="display_name",
            )
        )
    if not isinstance(spec.class_world_version, str) or not is_valid_semantic_version(
        spec.class_world_version
    ):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.CLASS_WORLD_VERSION_INVALID,
                "spec.class_world_version must be an exact Semantic Version.",
                "spec.class_world_version",
                field="class_world_version",
            )
        )
    if not isinstance(spec.engine_version, str) or not is_valid_semantic_version(
        spec.engine_version
    ):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.ENGINE_VERSION_INVALID,
                "spec.engine_version must be an exact Semantic Version.",
                "spec.engine_version",
                field="engine_version",
            )
        )
    if spec.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                ("spec.student_api_version must be exactly " f'"{SUPPORTED_STUDENT_API_VERSION}".'),
                "spec.student_api_version",
                field="student_api_version",
            )
        )
    return issues


def _validate_cohort(
    cohort: object,
) -> list[ClassWorldConfigurationIssue]:
    if not isinstance(cohort, ClassWorldCohort):
        return [
            _issue(
                ClassWorldConfigurationIssueCode.COHORT_INVALID,
                "spec.cohort must be a ClassWorldCohort.",
                "spec.cohort",
                field="cohort",
            )
        ]

    issues: list[ClassWorldConfigurationIssue] = []
    if not isinstance(cohort.cohort_id, str) or not is_valid_identifier(cohort.cohort_id):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.COHORT_ID_INVALID,
                "spec.cohort.cohort_id must be a valid lower-kebab-case identifier.",
                "spec.cohort.cohort_id",
                field="cohort_id",
            )
        )
    if not _is_valid_display_name(cohort.display_name, COHORT_DISPLAY_NAME_MAX_LENGTH):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.COHORT_DISPLAY_NAME_INVALID,
                (
                    "spec.cohort.display_name must contain non-whitespace text no longer than "
                    f"{COHORT_DISPLAY_NAME_MAX_LENGTH} characters."
                ),
                "spec.cohort.display_name",
                field="display_name",
            )
        )
    return issues


def _validate_pins(
    pins: object,
) -> tuple[list[ClassWorldConfigurationIssue], tuple[ClassWorldPackagePin, ...]]:
    if not isinstance(pins, tuple) or not pins:
        return (
            [
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_SET_REQUIRED,
                    "spec.packages must be a non-empty immutable tuple.",
                    "spec.packages",
                    field="packages",
                )
            ],
            (),
        )

    issues: list[ClassWorldConfigurationIssue] = []
    valid_pins: list[ClassWorldPackagePin] = []
    identities: list[tuple[int, str, object]] = []
    for package_index, candidate in enumerate(pins):
        location = f"spec.packages[{package_index}]"
        if not isinstance(candidate, ClassWorldPackagePin):
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_PIN_INVALID_TYPE,
                    f"{location} must be a ClassWorldPackagePin.",
                    location,
                    package_index=package_index,
                )
            )
            continue

        pin = candidate
        valid_pins.append(pin)
        package_id_valid = isinstance(pin.package_id, str) and is_valid_identifier(pin.package_id)
        if not package_id_valid:
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_PIN_ID_INVALID,
                    f"{location}.package_id must be a valid Explorer Package identifier.",
                    f"{location}.package_id",
                    package_id=pin.package_id,
                    package_index=package_index,
                    field="package_id",
                )
            )
        if not isinstance(pin.package_version, str) or not is_valid_semantic_version(
            pin.package_version
        ):
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_PIN_VERSION_INVALID,
                    f"{location}.package_version must be an exact Semantic Version.",
                    f"{location}.package_version",
                    package_id=pin.package_id,
                    package_index=package_index,
                    field="package_version",
                )
            )
        if package_id_valid:
            identities.append((package_index, pin.package_id, pin.package_version))

    seen: dict[str, tuple[int, object]] = {}
    for package_index, package_id, package_version in identities:
        earlier = seen.get(package_id)
        if earlier is None:
            seen[package_id] = (package_index, package_version)
            continue
        earlier_index, earlier_version = earlier
        if package_version == earlier_version:
            code = ClassWorldConfigurationIssueCode.PACKAGE_PIN_DUPLICATE
            description = "duplicates the same exact package pin"
        else:
            code = ClassWorldConfigurationIssueCode.PACKAGE_PIN_VERSION_CONFLICT
            description = "selects a conflicting exact package version"
        issues.append(
            _issue(
                code,
                (
                    f'spec.packages[{package_index}] {description}; package "{package_id}" '
                    f"first appears at spec.packages[{earlier_index}]."
                ),
                f"spec.packages[{package_index}].package_version",
                package_id=package_id,
                package_index=package_index,
                field="package_version",
            )
        )
    return issues, tuple(valid_pins)


def _validate_package_provenance(
    package: SelectedPackagePlan,
    package_index: int,
    student_api_version: object,
) -> list[ClassWorldConfigurationIssue]:
    location = f"package_set_plan.packages[{package_index}]"
    issues: list[ClassWorldConfigurationIssue] = []
    provenance = package.provenance
    registration_plan = package.registration_plan
    valid_provenance = isinstance(provenance, PackageProvenance)
    valid_registration_plan = isinstance(registration_plan, StudentAPIRegistrationPlan)
    if (
        not valid_provenance
        or provenance.package_id != package.package_id
        or provenance.package_version != package.package_version
        or provenance.student_api_version != student_api_version
    ):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                f"{location}.provenance must exactly match package and package-set metadata.",
                f"{location}.provenance",
                package_id=package.package_id,
                package_index=package_index,
                field="provenance",
            )
        )
    if valid_provenance and provenance.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (
                    f"{location}.provenance.student_api_version must be exactly "
                    f'"{SUPPORTED_STUDENT_API_VERSION}".'
                ),
                f"{location}.provenance.student_api_version",
                package_id=package.package_id,
                package_index=package_index,
                field="student_api_version",
            )
        )
    if (
        not valid_registration_plan
        or not valid_provenance
        or registration_plan.provenance != provenance
    ):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                (
                    f"{location}.registration_plan.provenance must exactly match "
                    "selected-package provenance."
                ),
                f"{location}.registration_plan.provenance",
                package_id=package.package_id,
                package_index=package_index,
                field="provenance",
            )
        )
    if (
        valid_registration_plan
        and isinstance(registration_plan.provenance, PackageProvenance)
        and registration_plan.provenance.student_api_version != SUPPORTED_STUDENT_API_VERSION
    ):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (
                    f"{location}.registration_plan.provenance.student_api_version must be "
                    f'exactly "{SUPPORTED_STUDENT_API_VERSION}".'
                ),
                f"{location}.registration_plan.provenance.student_api_version",
                package_id=package.package_id,
                package_index=package_index,
                field="student_api_version",
            )
        )
    return issues


def _entry_structure_issues(
    entry: object,
    provenance: PackageProvenance | None,
    *,
    package_index: int,
    entry_index: int,
    package_id: object,
) -> list[ClassWorldConfigurationIssue]:
    location = (
        f"package_set_plan.packages[{package_index}].registration_plan.entries[{entry_index}]"
    )
    if type(entry) not in (CharacterRegistration, WorldObjectRegistration):
        return [
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                f"{location} must be a supported registration entry.",
                location,
                package_id=package_id,
                package_index=package_index,
            )
        ]

    typed_entry: StudentAPIRegistrationEntry = entry
    issues: list[ClassWorldConfigurationIssue] = []
    if typed_entry.provenance != provenance:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_PROVENANCE_MISMATCH,
                f"{location}.provenance must match its nested registration plan.",
                f"{location}.provenance",
                package_id=package_id,
                package_index=package_index,
                field="provenance",
            )
        )
    expected_id = (
        f"{provenance.package_id}:{typed_entry.contribution_id}"
        if provenance is not None
        and isinstance(typed_entry.contribution_id, str)
        and is_valid_identifier(typed_entry.contribution_id)
        else None
    )
    if expected_id is None or typed_entry.qualified_id != expected_id:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                f"{location}.qualified_id must match package and contribution identity.",
                f"{location}.qualified_id",
                package_id=package_id,
                package_index=package_index,
                field="qualified_id",
            )
        )
    issues.extend(
        _entry_value_issues(
            typed_entry,
            location=location,
            package_id=package_id,
            package_index=package_index,
        )
    )
    return issues


def _is_coordinate(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_common_registration_values(
    *,
    name: object,
    x: object,
    y: object,
    color: object,
) -> bool:
    return (
        isinstance(name, str)
        and bool(name.strip())
        and _is_coordinate(x)
        and _is_coordinate(y)
        and isinstance(color, str)
        and color in _VALID_COLORS
    )


def _valid_asset_reference(asset: object) -> bool:
    if asset is None:
        return True
    if not isinstance(asset, PackageAssetReference):
        return False
    if (
        not isinstance(asset.id, str)
        or not is_valid_identifier(asset.id)
        or asset.type != "image"
        or not isinstance(asset.path, str)
        or not asset.path.strip()
        or "\\" in asset.path
    ):
        return False
    path = PurePosixPath(asset.path)
    return not path.is_absolute() and ".." not in path.parts and path.suffix.lower() == ".png"


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


def _entry_value_issues(
    entry: StudentAPIRegistrationEntry,
    *,
    location: str,
    package_id: object,
    package_index: int,
) -> list[ClassWorldConfigurationIssue]:
    values_valid = False
    if type(entry) is CharacterRegistration and isinstance(
        entry.character, CharacterRegistrationSpec
    ):
        values_valid = (
            _valid_common_registration_values(
                name=entry.character.name,
                x=entry.character.x,
                y=entry.character.y,
                color=entry.character.color,
            )
            and (
                entry.character.greeting is None
                or (
                    isinstance(entry.character.greeting, str)
                    and bool(entry.character.greeting.strip())
                )
            )
            and (
                entry.character.conversation is None
                or (
                    isinstance(entry.character.conversation, tuple)
                    and 2 <= len(entry.character.conversation) <= 3
                    and all(
                        isinstance(line, str) and bool(line.strip())
                        for line in entry.character.conversation
                    )
                )
            )
            and not (
                entry.character.greeting is not None and entry.character.conversation is not None
            )
        )
    elif type(entry) is WorldObjectRegistration and isinstance(
        entry.world_object, WorldObjectRegistrationSpec
    ):
        values_valid = (
            _valid_common_registration_values(
                name=entry.world_object.name,
                x=entry.world_object.x,
                y=entry.world_object.y,
                color=entry.world_object.color,
            )
            and all(
                value is None or (isinstance(value, str) and bool(value.strip()))
                for value in (
                    entry.world_object.when_near,
                    entry.world_object.when_interacted,
                )
            )
            and _valid_toggle(entry.world_object.toggle, off_color=entry.world_object.color)
        )
        if entry.world_object.toggle is not None and entry.asset_reference is not None:
            values_valid = False
    if values_valid and _valid_asset_reference(entry.asset_reference):
        return []
    return [
        _issue(
            ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
            f"{location} must retain valid immutable Student API registration values.",
            location,
            package_id=package_id,
            package_index=package_index,
        )
    ]


def _validate_package_set_plan(
    plan: PackageSetPlan,
) -> tuple[list[ClassWorldConfigurationIssue], tuple[SelectedPackagePlan, ...]]:
    issues: list[ClassWorldConfigurationIssue] = []
    if plan.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (
                    "package_set_plan.student_api_version must be exactly "
                    f'"{SUPPORTED_STUDENT_API_VERSION}".'
                ),
                "package_set_plan.student_api_version",
                field="student_api_version",
            )
        )
    if not isinstance(plan.packages, tuple) or not plan.packages:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                "package_set_plan.packages must be a non-empty immutable tuple.",
                "package_set_plan.packages",
                field="packages",
            )
        )
    if not isinstance(plan.entries, tuple) or not plan.entries:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                "package_set_plan.entries must be a non-empty immutable tuple.",
                "package_set_plan.entries",
                field="entries",
            )
        )

    packages = plan.packages if isinstance(plan.packages, tuple) else ()
    valid_packages: list[SelectedPackagePlan] = []
    flattened: list[StudentAPIRegistrationEntry] = []
    seen_package_ids: dict[str, int] = {}
    seen_qualified_ids: dict[str, tuple[int, int]] = {}
    character_count = 0
    world_object_count = 0

    for package_index, candidate in enumerate(packages):
        location = f"package_set_plan.packages[{package_index}]"
        if not isinstance(candidate, SelectedPackagePlan):
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                    f"{location} must be a SelectedPackagePlan.",
                    location,
                    package_index=package_index,
                )
            )
            continue
        package = candidate
        valid_packages.append(package)
        identity_valid = (
            isinstance(package.package_id, str)
            and is_valid_identifier(package.package_id)
            and isinstance(package.package_version, str)
            and is_valid_semantic_version(package.package_version)
        )
        if not identity_valid:
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                    f"{location} must contain a valid exact package identity and version.",
                    location,
                    package_id=package.package_id,
                    package_index=package_index,
                )
            )
        if isinstance(package.package_id, str):
            earlier = seen_package_ids.get(package.package_id)
            if earlier is None:
                seen_package_ids[package.package_id] = package_index
            else:
                issues.append(
                    _issue(
                        ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                        (
                            f'{location}.package_id duplicates package "{package.package_id}" '
                            f"from package_set_plan.packages[{earlier}]."
                        ),
                        f"{location}.package_id",
                        package_id=package.package_id,
                        package_index=package_index,
                        field="package_id",
                    )
                )

        issues.extend(
            _validate_package_provenance(
                package,
                package_index,
                plan.student_api_version,
            )
        )
        registration_plan = package.registration_plan
        if not isinstance(registration_plan, StudentAPIRegistrationPlan):
            continue
        entries = registration_plan.entries
        if not isinstance(entries, tuple) or not entries:
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                    f"{location}.registration_plan.entries must be a non-empty tuple.",
                    f"{location}.registration_plan.entries",
                    package_id=package.package_id,
                    package_index=package_index,
                    field="entries",
                )
            )
            continue

        provenance = (
            registration_plan.provenance
            if isinstance(registration_plan.provenance, PackageProvenance)
            else None
        )
        for entry_index, entry in enumerate(entries):
            issues.extend(
                _entry_structure_issues(
                    entry,
                    provenance,
                    package_index=package_index,
                    entry_index=entry_index,
                    package_id=package.package_id,
                )
            )
            if type(entry) not in (CharacterRegistration, WorldObjectRegistration):
                continue
            flattened.append(entry)
            if type(entry) is CharacterRegistration:
                character_count += 1
            else:
                world_object_count += 1
            qualified_id = entry.qualified_id
            if not isinstance(qualified_id, str):
                continue
            earlier_entry = seen_qualified_ids.get(qualified_id)
            if earlier_entry is None:
                seen_qualified_ids[qualified_id] = (package_index, entry_index)
            else:
                earlier_package_index, earlier_entry_index = earlier_entry
                issues.append(
                    _issue(
                        ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                        (
                            f"{location}.registration_plan.entries[{entry_index}].qualified_id "
                            "duplicates "
                            f"package_set_plan.packages[{earlier_package_index}]"
                            f".registration_plan.entries[{earlier_entry_index}]."
                        ),
                        f"{location}.registration_plan.entries[{entry_index}].qualified_id",
                        package_id=package.package_id,
                        package_index=package_index,
                        field="qualified_id",
                    )
                )

    try:
        flattened_matches = isinstance(plan.entries, tuple) and tuple(flattened) == plan.entries
    except Exception:
        flattened_matches = False
    if not flattened_matches:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                (
                    "package_set_plan.entries must exactly equal nested registration entries "
                    "in package and entry order."
                ),
                "package_set_plan.entries",
                field="entries",
            )
        )
    if character_count > 1:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                "Student API v0.1 package sets support at most one character.",
                "package_set_plan.entries",
                field="entries",
            )
        )
    if world_object_count > 1:
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                "Student API v0.1 package sets support at most one world object.",
                "package_set_plan.entries",
                field="entries",
            )
        )
    return issues, tuple(valid_packages)


def _validate_pin_agreement(
    pins: tuple[ClassWorldPackagePin, ...],
    packages: tuple[SelectedPackagePlan, ...],
) -> list[ClassWorldConfigurationIssue]:
    issues: list[ClassWorldConfigurationIssue] = []
    if len(pins) != len(packages):
        issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_COUNT_MISMATCH,
                (
                    f"spec.packages contains {len(pins)} pins but package_set_plan.packages "
                    f"contains {len(packages)} packages."
                ),
                "spec.packages",
                field="packages",
            )
        )

    pin_ids = tuple(pin.package_id for pin in pins)
    package_ids = tuple(package.package_id for package in packages)
    comparable_ids = all(isinstance(package_id, str) for package_id in (*pin_ids, *package_ids))
    is_reordering = (
        comparable_ids and len(pin_ids) == len(package_ids) and set(pin_ids) == set(package_ids)
    )
    for package_index, (pin, package) in enumerate(zip(pins, packages, strict=False)):
        if pin.package_id != package.package_id:
            code = (
                ClassWorldConfigurationIssueCode.PACKAGE_ORDER_MISMATCH
                if is_reordering
                else ClassWorldConfigurationIssueCode.PACKAGE_ID_MISMATCH
            )
            issues.append(
                _issue(
                    code,
                    (
                        f"spec.packages[{package_index}].package_id must exactly match "
                        f"package_set_plan.packages[{package_index}].package_id."
                    ),
                    f"spec.packages[{package_index}].package_id",
                    package_id=pin.package_id,
                    package_index=package_index,
                    field="package_id",
                )
            )
        if pin.package_version != package.package_version:
            issues.append(
                _issue(
                    ClassWorldConfigurationIssueCode.PACKAGE_VERSION_MISMATCH,
                    (
                        f"spec.packages[{package_index}].package_version must exactly match "
                        f"package_set_plan.packages[{package_index}].package_version."
                    ),
                    f"spec.packages[{package_index}].package_version",
                    package_id=pin.package_id,
                    package_index=package_index,
                    field="package_version",
                )
            )
    return issues


def build_class_world_configuration(
    spec: ClassWorldConfigurationSpec | None,
    package_set_plan: PackageSetPlan | None,
) -> ClassWorldConfigurationResult:
    """Build one immutable class-world configuration from already planned inputs.

    The operation is pure and atomic. It validates metadata, exact ordered pins,
    and defensive package-set invariants without loading, planning, applying, or
    serializing packages. Any issue returns ``configuration=None``.

    Args:
        spec: Immutable class-world metadata and exact ordered package pins.
        package_set_plan: One successful immutable package-set preflight plan.

    Returns:
        A complete immutable configuration or deterministic structured issues.
    """
    input_issues: list[ClassWorldConfigurationIssue] = []
    if not isinstance(spec, ClassWorldConfigurationSpec):
        input_issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.CONFIGURATION_SPEC_REQUIRED,
                "spec must be a ClassWorldConfigurationSpec.",
                "spec",
            )
        )
    if not isinstance(package_set_plan, PackageSetPlan):
        input_issues.append(
            _issue(
                ClassWorldConfigurationIssueCode.PACKAGE_SET_PLAN_REQUIRED,
                "package_set_plan must be a PackageSetPlan.",
                "package_set_plan",
            )
        )
    if input_issues:
        return ClassWorldConfigurationResult(configuration=None, issues=tuple(input_issues))

    assert spec is not None
    assert package_set_plan is not None
    metadata_issues = _validate_metadata(spec)
    cohort_issues = _validate_cohort(spec.cohort)
    pin_issues, valid_pins = _validate_pins(spec.packages)
    plan_issues, valid_packages = _validate_package_set_plan(package_set_plan)
    agreement_issues = _validate_pin_agreement(valid_pins, valid_packages)
    if spec.student_api_version != package_set_plan.student_api_version:
        agreement_issues.insert(
            0,
            _issue(
                ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                (
                    "spec.student_api_version must exactly match "
                    "package_set_plan.student_api_version."
                ),
                "package_set_plan.student_api_version",
                field="student_api_version",
            ),
        )

    issues = (
        *metadata_issues,
        *cohort_issues,
        *pin_issues,
        *plan_issues,
        *agreement_issues,
    )
    if issues:
        return ClassWorldConfigurationResult(configuration=None, issues=issues)

    return ClassWorldConfigurationResult(
        configuration=ClassWorldConfiguration(
            schema_version=spec.schema_version,
            class_world_id=spec.class_world_id,
            display_name=spec.display_name,
            class_world_version=spec.class_world_version,
            engine_version=spec.engine_version,
            student_api_version=spec.student_api_version,
            cohort=spec.cohort,
            package_set_plan=package_set_plan,
        ),
        issues=(),
    )
