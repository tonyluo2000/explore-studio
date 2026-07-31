"""Transactional application of immutable package-set plans."""

from __future__ import annotations

from dataclasses import dataclass

from explore import Character, Object
from explore.packages.package_set_application_models import (
    AppliedPackageSetRegistration,
    PackageSetApplicationIssue,
    PackageSetApplicationIssueCode,
    PackageSetApplicationResult,
)
from explore.packages.package_set_models import PackageSetPlan, SelectedPackagePlan
from explore.packages.policy import (
    SUPPORTED_STUDENT_API_VERSION,
    is_valid_identifier,
    is_valid_semantic_version,
)
from explore.packages.registration_application import (
    _add_to_target,
    _applied_metadata,
    _preflight,
    _remove_from_target,
    _stage_entry,
    _target_compatibility_issues,
)
from explore.packages.registration_application_models import (
    RegistrationApplicationIssue,
    RegistrationApplicationIssueCode,
    RegistrationApplicationState,
    StudentAPIRegistrationTarget,
)
from explore.packages.registration_models import (
    CharacterRegistration,
    StudentAPIRegistrationEntry,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
)


@dataclass(frozen=True)
class _LocatedEntry:
    package: SelectedPackagePlan
    package_index: int
    entry: StudentAPIRegistrationEntry
    entry_index: int


class _ValidationTarget:
    """Non-mutating empty target used only for shared entry validation."""

    def contains_registration(self, qualified_id: str) -> bool:
        return False

    def has_character(self) -> bool:
        return False

    def has_world_object(self) -> bool:
        return False

    def add_character(self, qualified_id: str, character: Character) -> None:
        raise AssertionError("validation must not mutate a target")

    def remove_character(self, qualified_id: str, character: Character) -> None:
        raise AssertionError("validation must not mutate a target")

    def add_world_object(self, qualified_id: str, world_object: Object) -> None:
        raise AssertionError("validation must not mutate a target")

    def remove_world_object(self, qualified_id: str, world_object: Object) -> None:
        raise AssertionError("validation must not mutate a target")


_SINGLE_ISSUE_CODES = {
    RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE: (
        PackageSetApplicationIssueCode.TARGET_INCOMPATIBLE
    ),
    RegistrationApplicationIssueCode.STUDENT_API_VERSION_UNSUPPORTED: (
        PackageSetApplicationIssueCode.STUDENT_API_VERSION_UNSUPPORTED
    ),
    RegistrationApplicationIssueCode.PLAN_PROVENANCE_MISMATCH: (
        PackageSetApplicationIssueCode.SELECTED_PACKAGE_MISMATCH
    ),
    RegistrationApplicationIssueCode.ENTRY_PROVENANCE_MISMATCH: (
        PackageSetApplicationIssueCode.ENTRY_PROVENANCE_MISMATCH
    ),
    RegistrationApplicationIssueCode.ENTRY_IDENTITY_INVALID: (
        PackageSetApplicationIssueCode.ENTRY_IDENTITY_INVALID
    ),
    RegistrationApplicationIssueCode.ENTRY_DUPLICATE: (
        PackageSetApplicationIssueCode.ENTRY_DUPLICATE
    ),
    RegistrationApplicationIssueCode.TARGET_DUPLICATE: (
        PackageSetApplicationIssueCode.TARGET_DUPLICATE
    ),
    RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED: (
        PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED
    ),
    RegistrationApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED: (
        PackageSetApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED
    ),
    RegistrationApplicationIssueCode.ENTRY_TYPE_UNSUPPORTED: (
        PackageSetApplicationIssueCode.ENTRY_TYPE_UNSUPPORTED
    ),
    RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID: (
        PackageSetApplicationIssueCode.ENTRY_VALUE_INVALID
    ),
    RegistrationApplicationIssueCode.ENTRY_ASSET_TYPE_MISMATCH: (
        PackageSetApplicationIssueCode.ENTRY_ASSET_TYPE_MISMATCH
    ),
}


def _safe_attribute(value: object, name: str) -> object | None:
    try:
        return getattr(value, name, None)
    except Exception:
        return None


def _issue(
    code: PackageSetApplicationIssueCode,
    message: str,
    location: str,
    *,
    located: _LocatedEntry | None = None,
    package: object | None = None,
    package_index: int | None = None,
) -> PackageSetApplicationIssue:
    entry = located.entry if located is not None else None
    selected = located.package if located is not None else package
    selected_index = located.package_index if located is not None else package_index
    selected_id = _safe_attribute(selected, "package_id")
    qualified_id = _safe_attribute(entry, "qualified_id")
    contribution_id = _safe_attribute(entry, "contribution_id")
    return PackageSetApplicationIssue(
        code=code,
        message=message,
        location=location,
        package_id=selected_id if isinstance(selected_id, str) else None,
        package_index=selected_index,
        qualified_id=qualified_id if isinstance(qualified_id, str) else None,
        contribution_id=contribution_id if isinstance(contribution_id, str) else None,
        entry_index=located.entry_index if located is not None else None,
    )


def _entry_location(located: _LocatedEntry) -> str:
    return f"packages[{located.package_index}].registration_plan.entries" f"[{located.entry_index}]"


def _single_issue_location(package_index: int, location: str) -> tuple[str, int | None]:
    if location == "plan":
        return f"packages[{package_index}].registration_plan", None
    if location.startswith("plan."):
        return f"packages[{package_index}].registration_plan.{location[5:]}", None
    if not location.startswith("entries["):
        return f"packages[{package_index}].registration_plan.{location}", None
    closing = location.find("]")
    try:
        entry_index = int(location[8:closing])
    except (TypeError, ValueError):
        entry_index = None
    return f"packages[{package_index}].registration_plan.{location}", entry_index


def _convert_single_issue(
    issue: RegistrationApplicationIssue,
    package: SelectedPackagePlan,
    package_index: int,
) -> PackageSetApplicationIssue:
    location, entry_index = _single_issue_location(package_index, issue.location)
    return PackageSetApplicationIssue(
        code=_SINGLE_ISSUE_CODES[issue.code],
        message=issue.message.replace("plan.", "registration_plan."),
        location=location,
        package_id=package.package_id if isinstance(package.package_id, str) else None,
        package_index=package_index,
        qualified_id=issue.qualified_id,
        contribution_id=issue.contribution_id,
        entry_index=entry_index,
    )


def _validate_structure(
    plan: PackageSetPlan,
) -> tuple[
    tuple[PackageSetApplicationIssue, ...],
    tuple[PackageSetApplicationIssue, ...],
    tuple[_LocatedEntry, ...],
    tuple[tuple[SelectedPackagePlan, int], ...],
]:
    top_issues: list[PackageSetApplicationIssue] = []
    package_issues: list[PackageSetApplicationIssue] = []
    cross_package_issues: list[PackageSetApplicationIssue] = []
    located_entries: list[_LocatedEntry] = []
    valid_packages: list[tuple[SelectedPackagePlan, int]] = []

    if plan.student_api_version != SUPPORTED_STUDENT_API_VERSION:
        top_issues.append(
            _issue(
                PackageSetApplicationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
                ("plan.student_api_version must be " f'"{SUPPORTED_STUDENT_API_VERSION}".'),
                "plan.student_api_version",
            )
        )
    if not isinstance(plan.packages, tuple) or not plan.packages:
        top_issues.append(
            _issue(
                PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                "plan.packages must be a non-empty immutable tuple.",
                "plan.packages",
            )
        )
    if not isinstance(plan.entries, tuple) or not plan.entries:
        top_issues.append(
            _issue(
                PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                "plan.entries must be a non-empty immutable tuple.",
                "plan.entries",
            )
        )

    packages = plan.packages if isinstance(plan.packages, tuple) else ()
    for package_index, candidate in enumerate(packages):
        location = f"packages[{package_index}]"
        if not isinstance(candidate, SelectedPackagePlan):
            package_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                    f"{location} must be a SelectedPackagePlan.",
                    location,
                    package_index=package_index,
                )
            )
            continue

        package = candidate
        registration_plan = package.registration_plan
        valid_identity = (
            isinstance(package.package_id, str)
            and is_valid_identifier(package.package_id)
            and isinstance(package.package_version, str)
            and is_valid_semantic_version(package.package_version)
        )
        try:
            consistent = (
                isinstance(registration_plan, StudentAPIRegistrationPlan)
                and package.provenance == registration_plan.provenance
                and getattr(package.provenance, "package_id", None) == package.package_id
                and getattr(package.provenance, "package_version", None) == package.package_version
                and getattr(package.provenance, "student_api_version", None)
                == plan.student_api_version
            )
        except Exception:
            consistent = False
        if not valid_identity or not consistent:
            package_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.SELECTED_PACKAGE_MISMATCH,
                    (
                        f"{location} must agree with its registration plan and "
                        "package-set provenance."
                    ),
                    location,
                    package=package,
                    package_index=package_index,
                )
            )
        if not isinstance(registration_plan, StudentAPIRegistrationPlan):
            continue

        entries = registration_plan.entries
        if not isinstance(entries, tuple) or not entries:
            package_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                    (
                        f"{location}.registration_plan.entries must be a "
                        "non-empty immutable tuple."
                    ),
                    f"{location}.registration_plan.entries",
                    package=package,
                    package_index=package_index,
                )
            )
            continue

        valid_packages.append((package, package_index))
        for entry_index, entry in enumerate(entries):
            located_entries.append(
                _LocatedEntry(
                    package=package,
                    package_index=package_index,
                    entry=entry,
                    entry_index=entry_index,
                )
            )

    flattened = tuple(located.entry for located in located_entries)
    try:
        flattened_matches = isinstance(plan.entries, tuple) and flattened == plan.entries
    except Exception:
        flattened_matches = False
    if not flattened_matches:
        top_issues.append(
            _issue(
                PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                (
                    "plan.entries must exactly equal nested registration entries in "
                    "package order and plan-entry order."
                ),
                "plan.entries",
            )
        )

    seen_ids: set[str] = set()
    character_count = sum(type(item.entry) is CharacterRegistration for item in located_entries)
    object_count = sum(type(item.entry) is WorldObjectRegistration for item in located_entries)
    for located in located_entries:
        qualified_id = _safe_attribute(located.entry, "qualified_id")
        if isinstance(qualified_id, str):
            if qualified_id in seen_ids:
                cross_package_issues.append(
                    _issue(
                        PackageSetApplicationIssueCode.ENTRY_DUPLICATE,
                        (
                            f"{_entry_location(located)} duplicates qualified identity "
                            f'"{qualified_id}".'
                        ),
                        f"{_entry_location(located)}.qualified_id",
                        located=located,
                    )
                )
            else:
                seen_ids.add(qualified_id)
        if type(located.entry) is CharacterRegistration and character_count > 1:
            cross_package_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
                    "Student API v0.1 package sets support at most one character.",
                    _entry_location(located),
                    located=located,
                )
            )
        if type(located.entry) is WorldObjectRegistration and object_count > 1:
            cross_package_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
                    "Student API v0.1 package sets support at most one world object.",
                    _entry_location(located),
                    located=located,
                )
            )

    return (
        (*top_issues, *package_issues),
        tuple(cross_package_issues),
        tuple(located_entries),
        tuple(valid_packages),
    )


def _package_validation_issues(
    packages: tuple[tuple[SelectedPackagePlan, int], ...],
) -> tuple[PackageSetApplicationIssue, ...]:
    issues: list[PackageSetApplicationIssue] = []
    ignored_codes = {
        RegistrationApplicationIssueCode.ENTRY_DUPLICATE,
        RegistrationApplicationIssueCode.TARGET_DUPLICATE,
        RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
        RegistrationApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
    }
    validation_target = _ValidationTarget()
    for package, package_index in packages:
        try:
            package_preflight = _preflight(package.registration_plan, validation_target)
        except Exception:
            issues.append(
                _issue(
                    PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID,
                    (
                        f"packages[{package_index}].registration_plan could not be "
                        "validated deterministically."
                    ),
                    f"packages[{package_index}].registration_plan",
                    package=package,
                    package_index=package_index,
                )
            )
            continue
        for issue in package_preflight:
            if issue.code in ignored_codes:
                continue
            issues.append(_convert_single_issue(issue, package, package_index))
    return tuple(issues)


def _target_issues(
    target: StudentAPIRegistrationTarget,
    entries: tuple[_LocatedEntry, ...],
) -> tuple[
    tuple[PackageSetApplicationIssue, ...],
    tuple[PackageSetApplicationIssue, ...],
]:
    raw_issues, has_character, has_world_object, contains = _target_compatibility_issues(
        target,
        tuple(located.entry for located in entries),
    )
    compatibility_issues = [
        PackageSetApplicationIssue(
            code=PackageSetApplicationIssueCode.TARGET_INCOMPATIBLE,
            message=issue.message,
            location=issue.location,
        )
        for issue in raw_issues
    ]
    state_issues: list[PackageSetApplicationIssue] = []
    for located in entries:
        entry = located.entry
        qualified_id = _safe_attribute(entry, "qualified_id")
        if isinstance(qualified_id, str) and contains.get(qualified_id) is True:
            state_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.TARGET_DUPLICATE,
                    f'Target registration "{qualified_id}" already exists.',
                    f"{_entry_location(located)}.qualified_id",
                    located=located,
                )
            )
        if type(entry) is CharacterRegistration and has_character is True:
            state_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
                    "The target character slot is already occupied and cannot be replaced.",
                    _entry_location(located),
                    located=located,
                )
            )
        if type(entry) is WorldObjectRegistration and has_world_object is True:
            state_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
                    "The target world-object slot is already occupied and cannot be replaced.",
                    _entry_location(located),
                    located=located,
                )
            )
    return tuple(compatibility_issues), tuple(state_issues)


def _metadata(located: _LocatedEntry) -> AppliedPackageSetRegistration:
    metadata = _applied_metadata(located.entry)
    return AppliedPackageSetRegistration(
        package_id=located.package.package_id,
        package_version=located.package.package_version,
        package_index=located.package_index,
        entry_index=located.entry_index,
        qualified_id=metadata.qualified_id,
        contribution_id=metadata.contribution_id,
        provenance=metadata.provenance,
        registration_type=metadata.registration_type,
        asset_reference=metadata.asset_reference,
    )


def apply_package_set_plan(
    plan: PackageSetPlan | None,
    target: StudentAPIRegistrationTarget | None,
) -> PackageSetApplicationResult:
    """Apply one immutable package-set plan to one explicit target atomically.

    Complete package-set and target preflight and runtime staging happen before
    mutation. Commit follows package order and each nested plan's entry order.
    The first add failure triggers global reverse-order rollback across package
    boundaries, with package-aware reporting for any unreverted entries.

    Args:
        plan: Successful immutable package-set preflight plan.
        target: Explicit compatible Student API registration target.

    Returns:
        Immutable package-aware transaction result and deterministic diagnostics.
    """
    input_issues: list[PackageSetApplicationIssue] = []
    if not isinstance(plan, PackageSetPlan):
        input_issues.append(
            _issue(
                PackageSetApplicationIssueCode.PACKAGE_SET_PLAN_REQUIRED,
                "plan must be a PackageSetPlan.",
                "plan",
            )
        )
    if target is None:
        input_issues.append(
            _issue(
                PackageSetApplicationIssueCode.TARGET_REQUIRED,
                "target must be supplied explicitly.",
                "target",
            )
        )
    if input_issues:
        return PackageSetApplicationResult(
            state=RegistrationApplicationState.NOT_APPLIED,
            issues=tuple(input_issues),
        )

    assert plan is not None
    assert target is not None
    structure_issues, cross_package_issues, located_entries, valid_packages = _validate_structure(
        plan
    )
    try:
        target_compatibility_issues, target_state_issues = _target_issues(
            target,
            located_entries,
        )
    except Exception:
        target_compatibility_issues = (
            _issue(
                PackageSetApplicationIssueCode.TARGET_INCOMPATIBLE,
                "target could not provide deterministic package-set state.",
                "target",
            ),
        )
        target_state_issues = ()
    package_issues = _package_validation_issues(valid_packages)
    preflight_issues = (
        *target_compatibility_issues,
        *structure_issues,
        *package_issues,
        *cross_package_issues,
        *target_state_issues,
    )
    if preflight_issues:
        return PackageSetApplicationResult(
            state=RegistrationApplicationState.NOT_APPLIED,
            issues=preflight_issues,
        )

    staged: list[tuple[_LocatedEntry, Character | Object]] = []
    construction_issues: list[PackageSetApplicationIssue] = []
    for located in located_entries:
        try:
            instance = _stage_entry(located.entry)
        except Exception:
            construction_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.INSTANCE_CONSTRUCTION_FAILED,
                    f"{_entry_location(located)} could not construct a compatible instance.",
                    _entry_location(located),
                    located=located,
                )
            )
            continue
        staged.append((located, instance))

    if construction_issues:
        return PackageSetApplicationResult(
            state=RegistrationApplicationState.NOT_APPLIED,
            issues=tuple(construction_issues),
        )

    committed: list[tuple[_LocatedEntry, Character | Object]] = []
    application_issue: PackageSetApplicationIssue | None = None
    for located, instance in staged:
        try:
            _add_to_target(target, located.entry, instance)
        except Exception:
            application_issue = _issue(
                PackageSetApplicationIssueCode.TARGET_ADD_FAILED,
                f'Target rejected registration "{located.entry.qualified_id}" during commit.',
                _entry_location(located),
                located=located,
            )
            break
        committed.append((located, instance))

    if application_issue is None:
        return PackageSetApplicationResult(
            state=RegistrationApplicationState.APPLIED,
            applied=tuple(_metadata(located) for located, _ in committed),
        )

    rollback_issues: list[PackageSetApplicationIssue] = []
    unreverted: list[AppliedPackageSetRegistration] = []
    for located, instance in reversed(committed):
        try:
            _remove_from_target(target, located.entry, instance)
        except Exception:
            rollback_issues.append(
                _issue(
                    PackageSetApplicationIssueCode.TARGET_REMOVE_FAILED,
                    (
                        f'Target could not remove registration "{located.entry.qualified_id}" '
                        "during rollback."
                    ),
                    f"rollback.{_entry_location(located)}",
                    located=located,
                )
            )
            unreverted.append(_metadata(located))

    state = (
        RegistrationApplicationState.ROLLBACK_INCOMPLETE
        if rollback_issues
        else RegistrationApplicationState.ROLLED_BACK
    )
    return PackageSetApplicationResult(
        state=state,
        issues=(application_issue, *rollback_issues),
        unreverted=tuple(unreverted),
    )
