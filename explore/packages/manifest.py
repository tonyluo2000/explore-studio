"""Safe YAML parsing and structural validation for Explorer Package manifests."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import yaml

from explore.packages.models import (
    AssetDeclaration,
    Compatibility,
    ContributionDeclaration,
    ExplorerPackageManifest,
    IssueCode,
    PackageMetadata,
    ValidationIssue,
)
from explore.packages.policy import (
    ASSET_FILE_EXTENSIONS,
    CONTRIBUTION_FILE_EXTENSIONS,
    DISPLAY_NAME_MAX_LENGTH,
    IDENTIFIER_MAX_LENGTH,
    SUPPORTED_SCHEMA_VERSION,
    SUPPORTED_STUDENT_API_VERSION,
    is_valid_identifier,
    is_valid_semantic_version,
)

_ROOT_FIELDS = frozenset({"schema_version", "package", "compatibility", "contributions", "assets"})
_PACKAGE_FIELDS = frozenset({"id", "display_name", "version"})
_COMPATIBILITY_FIELDS = frozenset({"student_api"})
_DECLARATION_FIELDS = frozenset({"id", "type", "path"})


def _issue(code: IssueCode, message: str, location: str) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, location=location)


def load_manifest_document(
    manifest_path: Path,
) -> tuple[object | None, tuple[ValidationIssue, ...]]:
    """Load a UTF-8 manifest with PyYAML's safe loader.

    Args:
        manifest_path: Path to the package's ``manifest.yaml``.

    Returns:
        A pair containing the loaded YAML value and any loading issue.
    """
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, (
            _issue(
                IssueCode.MANIFEST_INVALID_ENCODING,
                "manifest.yaml must be encoded as UTF-8.",
                "manifest.yaml",
            ),
        )
    except OSError:
        return None, (
            _issue(
                IssueCode.MANIFEST_READ_ERROR,
                "manifest.yaml could not be read.",
                "manifest.yaml",
            ),
        )

    try:
        return yaml.safe_load(text), ()
    except yaml.YAMLError:
        return None, (
            _issue(
                IssueCode.MANIFEST_INVALID_YAML,
                "manifest.yaml is not valid safe YAML.",
                "manifest.yaml",
            ),
        )


def _mapping(
    value: object,
    location: str,
    issues: list[ValidationIssue],
) -> Mapping[object, object] | None:
    if isinstance(value, Mapping):
        return value
    issues.append(
        _issue(
            IssueCode.MANIFEST_INVALID_TYPE,
            f"{location} must be a mapping.",
            location,
        )
    )
    return None


def _required_string(
    mapping: Mapping[object, object],
    field: str,
    location: str,
    issues: list[ValidationIssue],
) -> str | None:
    field_location = f"{location}.{field}" if location else field
    if field not in mapping:
        issues.append(
            _issue(
                IssueCode.MANIFEST_FIELD_REQUIRED,
                f"{field_location} is required.",
                field_location,
            )
        )
        return None

    value = mapping[field]
    if not isinstance(value, str):
        issues.append(
            _issue(
                IssueCode.MANIFEST_INVALID_TYPE,
                f"{field_location} must be a string.",
                field_location,
            )
        )
        return None
    return value


def _unknown_fields(
    mapping: Mapping[object, object],
    allowed: frozenset[str],
    location: str,
    issues: list[ValidationIssue],
) -> None:
    unknown = sorted(str(key) for key in mapping if not isinstance(key, str) or key not in allowed)
    for field in unknown:
        field_location = f"{location}.{field}" if location else field
        issues.append(
            _issue(
                IssueCode.MANIFEST_FIELD_UNKNOWN,
                f"{field_location} is not part of Explorer Package manifest v0.1.",
                field_location,
            )
        )


def _validate_identifier(
    value: str | None,
    *,
    code: IssueCode,
    location: str,
    label: str,
    issues: list[ValidationIssue],
) -> None:
    if value is not None and not is_valid_identifier(value):
        issues.append(
            _issue(
                code,
                (
                    f"{label} must be 1-{IDENTIFIER_MAX_LENGTH} characters of lower-kebab-case "
                    "ASCII, beginning with a letter and without consecutive or trailing hyphens."
                ),
                location,
            )
        )


def _parse_declarations(
    root: Mapping[object, object],
    key: str,
    issues: list[ValidationIssue],
) -> tuple[tuple[ContributionDeclaration, ...] | tuple[AssetDeclaration, ...], bool]:
    value = root.get(key, [] if key == "assets" else None)
    if value is None and key == "contributions":
        issues.append(
            _issue(
                IssueCode.MANIFEST_FIELD_REQUIRED,
                "contributions is required.",
                "contributions",
            )
        )
        return (), False
    if not isinstance(value, list):
        issues.append(
            _issue(
                IssueCode.MANIFEST_INVALID_TYPE,
                f"{key} must be a list.",
                key,
            )
        )
        return (), False

    if key == "contributions" and not value:
        issues.append(
            _issue(
                IssueCode.CONTRIBUTIONS_REQUIRED,
                "contributions must declare at least one character or world_object.",
                "contributions",
            )
        )

    declarations: list[ContributionDeclaration | AssetDeclaration] = []
    structurally_complete = True
    seen_ids: set[str] = set()
    supported_types = (
        CONTRIBUTION_FILE_EXTENSIONS if key == "contributions" else ASSET_FILE_EXTENSIONS
    )
    invalid_id_code = (
        IssueCode.CONTRIBUTION_ID_INVALID if key == "contributions" else IssueCode.ASSET_ID_INVALID
    )
    duplicate_id_code = (
        IssueCode.CONTRIBUTION_ID_DUPLICATE
        if key == "contributions"
        else IssueCode.ASSET_ID_DUPLICATE
    )
    unsupported_type_code = (
        IssueCode.CONTRIBUTION_TYPE_UNSUPPORTED
        if key == "contributions"
        else IssueCode.ASSET_TYPE_UNSUPPORTED
    )

    for index, item in enumerate(value):
        location = f"{key}[{index}]"
        item_mapping = _mapping(item, location, issues)
        if item_mapping is None:
            structurally_complete = False
            continue

        declaration_id = _required_string(item_mapping, "id", location, issues)
        declaration_type = _required_string(item_mapping, "type", location, issues)
        declaration_path = _required_string(item_mapping, "path", location, issues)
        _unknown_fields(item_mapping, _DECLARATION_FIELDS, location, issues)

        _validate_identifier(
            declaration_id,
            code=invalid_id_code,
            location=f"{location}.id",
            label=f"{key[:-1].replace('_', ' ')} ID",
            issues=issues,
        )
        if declaration_id is not None:
            if declaration_id in seen_ids:
                issues.append(
                    _issue(
                        duplicate_id_code,
                        (
                            f'{key[:-1].replace("_", " ").capitalize()} ID '
                            f'"{declaration_id}" is duplicated.'
                        ),
                        f"{location}.id",
                    )
                )
            else:
                seen_ids.add(declaration_id)

        if declaration_type is not None and declaration_type not in supported_types:
            supported = ", ".join(sorted(supported_types))
            issues.append(
                _issue(
                    unsupported_type_code,
                    (
                        f'{location}.type "{declaration_type}" is unsupported; '
                        f"choose from: {supported}."
                    ),
                    f"{location}.type",
                )
            )

        if declaration_id is None or declaration_type is None or declaration_path is None:
            structurally_complete = False
            continue

        declaration_class: type[ContributionDeclaration] | type[AssetDeclaration]
        declaration_class = ContributionDeclaration if key == "contributions" else AssetDeclaration
        declarations.append(
            declaration_class(
                id=declaration_id,
                type=declaration_type,
                path=declaration_path,
            )
        )

    return tuple(declarations), structurally_complete


def parse_manifest_document(
    document: object,
) -> tuple[ExplorerPackageManifest | None, tuple[ValidationIssue, ...]]:
    """Validate a loaded YAML document and build its typed manifest.

    This validates only the manifest contract. Declared filesystem paths are
    validated separately by the package-directory validator.
    """
    issues: list[ValidationIssue] = []
    root = _mapping(document, "manifest.yaml", issues)
    if root is None:
        return None, tuple(issues)

    schema_version = _required_string(root, "schema_version", "", issues)
    if schema_version is not None and schema_version != SUPPORTED_SCHEMA_VERSION:
        issues.append(
            _issue(
                IssueCode.SCHEMA_VERSION_UNSUPPORTED,
                (
                    f'Explorer Package schema "{schema_version}" is unsupported; '
                    f'use "{SUPPORTED_SCHEMA_VERSION}".'
                ),
                "schema_version",
            )
        )

    package_value = root.get("package")
    if package_value is None:
        issues.append(
            _issue(
                IssueCode.MANIFEST_FIELD_REQUIRED,
                "package is required.",
                "package",
            )
        )
        package_mapping = None
    else:
        package_mapping = _mapping(package_value, "package", issues)

    package_id: str | None = None
    display_name: str | None = None
    package_version: str | None = None
    if package_mapping is not None:
        package_id = _required_string(package_mapping, "id", "package", issues)
        display_name = _required_string(package_mapping, "display_name", "package", issues)
        package_version = _required_string(package_mapping, "version", "package", issues)
        _unknown_fields(package_mapping, _PACKAGE_FIELDS, "package", issues)

        _validate_identifier(
            package_id,
            code=IssueCode.PACKAGE_ID_INVALID,
            location="package.id",
            label="Package ID",
            issues=issues,
        )
        if display_name is not None and (
            not display_name.strip() or len(display_name) > DISPLAY_NAME_MAX_LENGTH
        ):
            issues.append(
                _issue(
                    IssueCode.PACKAGE_DISPLAY_NAME_INVALID,
                    (
                        "package.display_name must contain visible text and be no more than "
                        f"{DISPLAY_NAME_MAX_LENGTH} characters."
                    ),
                    "package.display_name",
                )
            )
        if package_version is not None and not is_valid_semantic_version(package_version):
            issues.append(
                _issue(
                    IssueCode.PACKAGE_VERSION_INVALID,
                    (
                        f'Package version "{package_version}" is not a valid Semantic '
                        "Versioning 2.0.0 version."
                    ),
                    "package.version",
                )
            )

    compatibility_value = root.get("compatibility")
    if compatibility_value is None:
        issues.append(
            _issue(
                IssueCode.MANIFEST_FIELD_REQUIRED,
                "compatibility is required.",
                "compatibility",
            )
        )
        compatibility_mapping = None
    else:
        compatibility_mapping = _mapping(compatibility_value, "compatibility", issues)

    student_api: str | None = None
    if compatibility_mapping is not None:
        student_api = _required_string(
            compatibility_mapping,
            "student_api",
            "compatibility",
            issues,
        )
        _unknown_fields(
            compatibility_mapping,
            _COMPATIBILITY_FIELDS,
            "compatibility",
            issues,
        )
        if student_api is not None and student_api != SUPPORTED_STUDENT_API_VERSION:
            issues.append(
                _issue(
                    IssueCode.STUDENT_API_UNSUPPORTED,
                    (
                        f'Student API "{student_api}" is unsupported; this validator supports '
                        f'exactly "{SUPPORTED_STUDENT_API_VERSION}".'
                    ),
                    "compatibility.student_api",
                )
            )

    contributions, contributions_complete = _parse_declarations(root, "contributions", issues)
    assets, assets_complete = _parse_declarations(root, "assets", issues)
    _unknown_fields(root, _ROOT_FIELDS, "", issues)

    complete = all(
        value is not None
        for value in (
            schema_version,
            package_id,
            display_name,
            package_version,
            student_api,
        )
    )
    complete = complete and contributions_complete and assets_complete
    if not complete:
        return None, tuple(issues)

    return (
        ExplorerPackageManifest(
            schema_version=schema_version,
            package=PackageMetadata(
                id=package_id,
                display_name=display_name,
                version=package_version,
            ),
            compatibility=Compatibility(student_api=student_api),
            contributions=tuple(contributions),  # type: ignore[arg-type]
            assets=tuple(assets),  # type: ignore[arg-type]
        ),
        tuple(issues),
    )
