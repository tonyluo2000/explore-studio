"""Bounded readback and canonical digest verification for assembled manifests."""

from __future__ import annotations

import json
import stat
from dataclasses import dataclass
from pathlib import Path

from explore.packages.class_world_assembled_output_manifest import (
    build_class_world_assembled_output_manifest,
    serialize_class_world_assembled_output_manifest,
)
from explore.packages.class_world_assembled_output_manifest_file_digest_verification_models import (
    MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES,
    ClassWorldAssembledOutputManifestFileDigestVerificationResult,
    ClassWorldAssembledOutputManifestFileIssue,
    ClassWorldAssembledOutputManifestFileIssueCode,
)
from explore.packages.class_world_assembled_output_manifest_models import (
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM,
    ClassWorldAssembledOutputManifest,
    ClassWorldAssembledOutputManifestDigest,
)
from explore.packages.class_world_verified_materialization_models import (
    ClassWorldVerifiedMaterializationResult,
)

_UTF8_BOM = b"\xef\xbb\xbf"
_ROOT_FIELDS = ("contract_version", "packages", "total_bytes")
_PACKAGE_FIELDS = (
    "package_id",
    "package_version",
    "digest_algorithm",
    "digest_hex",
    "relative_path",
    "bytes_written",
)
_LOWERCASE_HEXADECIMAL = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class _JSONObject:
    pairs: tuple[tuple[str, object], ...]


class _NonFiniteNumberError(ValueError):
    pass


def _object_pairs(pairs: list[tuple[str, object]]) -> _JSONObject:
    return _JSONObject(tuple(pairs))


def _reject_non_finite(value: str) -> object:
    raise _NonFiniteNumberError(value)


def _issue(
    code: ClassWorldAssembledOutputManifestFileIssueCode,
    message: str,
    location: str,
) -> ClassWorldAssembledOutputManifestFileIssue:
    return ClassWorldAssembledOutputManifestFileIssue(code=code, message=message, location=location)


def _failure(
    *issues: ClassWorldAssembledOutputManifestFileIssue,
    bytes_read: int = 0,
) -> ClassWorldAssembledOutputManifestFileDigestVerificationResult:
    return ClassWorldAssembledOutputManifestFileDigestVerificationResult(
        manifest=None,
        expected_digest=None,
        actual_digest=None,
        matches=None,
        bytes_read=bytes_read,
        issues=tuple(issues),
    )


def _validated_path(
    candidate: object,
) -> tuple[Path | None, ClassWorldAssembledOutputManifestFileIssue | None]:
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return None, _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.PATH_REQUIRED,
            "path must be a non-empty str or pathlib.Path.",
            "path",
        )
    if not isinstance(candidate, (str, Path)):
        return None, _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.PATH_INVALID_TYPE,
            "path must be a str or pathlib.Path.",
            "path",
        )
    return Path(candidate), None


def _expected_digest_issue(
    candidate: object,
) -> ClassWorldAssembledOutputManifestFileIssue | None:
    if (
        type(candidate) is not ClassWorldAssembledOutputManifestDigest
        or candidate.algorithm != SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM
        or type(candidate.hex_digest) is not str
        or len(candidate.hex_digest) != 64
        or any(character not in _LOWERCASE_HEXADECIMAL for character in candidate.hex_digest)
    ):
        return _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.EXPECTED_DIGEST_INVALID,
            'expected_digest must be one "sha256" digest with 64 lowercase hexadecimal characters.',
            "expected_digest",
        )
    return None


def _inspect_path(path: Path) -> ClassWorldAssembledOutputManifestFileIssue | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.FILE_NOT_FOUND,
            "The assembled-output manifest file does not exist.",
            "path",
        )
    except (OSError, ValueError):
        return _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.FILE_READ_FAILED,
            "The assembled-output manifest path could not be inspected.",
            "path",
        )
    if stat.S_ISLNK(metadata.st_mode):
        return _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.FILE_SYMLINK_NOT_ALLOWED,
            "The final assembled-output manifest path must not be a symbolic link.",
            "path",
        )
    if not stat.S_ISREG(metadata.st_mode):
        return _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.FILE_NOT_REGULAR,
            "The assembled-output manifest path must refer to a regular file.",
            "path",
        )
    return None


def _duplicate_issues(
    value: object,
    location: str = "",
) -> list[ClassWorldAssembledOutputManifestFileIssue]:
    issues: list[ClassWorldAssembledOutputManifestFileIssue] = []
    if isinstance(value, _JSONObject):
        seen: set[str] = set()
        for key, child in value.pairs:
            child_location = f"{location}.{key}" if location else key
            if key in seen:
                issues.append(
                    _issue(
                        ClassWorldAssembledOutputManifestFileIssueCode.JSON_DUPLICATE_KEY,
                        f'Duplicate JSON key "{key}" is not permitted.',
                        child_location,
                    )
                )
            else:
                seen.add(key)
            issues.extend(_duplicate_issues(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_duplicate_issues(child, f"{location}[{index}]"))
    return issues


def _to_json_value(value: object) -> object:
    if isinstance(value, _JSONObject):
        return {key: _to_json_value(child) for key, child in value.pairs}
    if isinstance(value, list):
        return [_to_json_value(child) for child in value]
    return value


def _unknown_issues(
    value: dict[str, object],
    allowed: tuple[str, ...],
    location: str = "",
) -> list[ClassWorldAssembledOutputManifestFileIssue]:
    allowed_fields = frozenset(allowed)
    return [
        _issue(
            ClassWorldAssembledOutputManifestFileIssueCode.FIELD_UNKNOWN,
            f"{field_location} is not a recognized assembled-output manifest field.",
            field_location,
        )
        for key in sorted(value.keys() - allowed_fields)
        for field_location in (f"{location}.{key}" if location else key,)
    ]


def _required(location: str) -> ClassWorldAssembledOutputManifestFileIssue:
    return _issue(
        ClassWorldAssembledOutputManifestFileIssueCode.FIELD_REQUIRED,
        f"{location} is required.",
        location,
    )


def _invalid_type(
    location: str,
    expected: str,
) -> ClassWorldAssembledOutputManifestFileIssue:
    return _issue(
        ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_TYPE,
        f"{location} must be a JSON {expected}.",
        location,
    )


def _structure_issues(root: dict[str, object]) -> list[ClassWorldAssembledOutputManifestFileIssue]:
    issues: list[ClassWorldAssembledOutputManifestFileIssue] = []
    expected_types: dict[str, tuple[type, str]] = {
        "contract_version": (str, "string"),
        "packages": (list, "array"),
        "total_bytes": (int, "integer"),
    }
    for field in _ROOT_FIELDS:
        if field not in root:
            issues.append(_required(field))
            continue
        expected_type, description = expected_types[field]
        if type(root[field]) is not expected_type:
            issues.append(_invalid_type(field, description))
    issues.extend(_unknown_issues(root, _ROOT_FIELDS))

    if type(root.get("contract_version")) is str and root["contract_version"] != (
        SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION
    ):
        issues.append(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
                'contract_version must be exactly "0.1".',
                "contract_version",
            )
        )
    if type(root.get("total_bytes")) is int and root["total_bytes"] < 0:
        issues.append(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
                "total_bytes must be non-negative.",
                "total_bytes",
            )
        )

    packages = root.get("packages")
    if type(packages) is list:
        if not packages:
            issues.append(
                _issue(
                    ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
                    "packages must contain the complete non-empty materialized package set.",
                    "packages",
                )
            )
        for index, package in enumerate(packages):
            location = f"packages[{index}]"
            if type(package) is not dict:
                issues.append(_invalid_type(location, "object"))
                continue
            for field in _PACKAGE_FIELDS:
                field_location = f"{location}.{field}"
                if field not in package:
                    issues.append(_required(field_location))
                    continue
                expected_type = int if field == "bytes_written" else str
                if type(package[field]) is not expected_type:
                    issues.append(
                        _invalid_type(
                            field_location,
                            "integer" if expected_type is int else "string",
                        )
                    )
            issues.extend(_unknown_issues(package, _PACKAGE_FIELDS, location))
            digest = package.get("digest_hex")
            if type(digest) is str and (
                len(digest) != 64
                or any(character not in _LOWERCASE_HEXADECIMAL for character in digest)
            ):
                issues.append(
                    _issue(
                        ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
                        f"{location}.digest_hex must contain 64 lowercase hexadecimal characters.",
                        f"{location}.digest_hex",
                    )
                )
            algorithm = package.get("digest_algorithm")
            if type(algorithm) is str and algorithm != "sha256":
                issues.append(
                    _issue(
                        ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
                        f'{location}.digest_algorithm must be exactly "sha256".',
                        f"{location}.digest_algorithm",
                    )
                )
            count = package.get("bytes_written")
            if type(count) is int and count < 0:
                issues.append(
                    _issue(
                        ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
                        f"{location}.bytes_written must be non-negative.",
                        f"{location}.bytes_written",
                    )
                )
    return issues


def _parse_json(
    text: str,
) -> tuple[dict[str, object] | None, tuple[ClassWorldAssembledOutputManifestFileIssue, ...]]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_non_finite,
        )
    except (ValueError, RecursionError):
        return None, (
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.JSON_INVALID,
                "The assembled-output manifest must contain one finite JSON value.",
                "manifest",
            ),
        )
    try:
        duplicates = _duplicate_issues(value)
        converted = _to_json_value(value)
    except RecursionError:
        return None, (
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.JSON_INVALID,
                "The assembled-output manifest JSON nesting is too deep.",
                "manifest",
            ),
        )
    if duplicates:
        return None, tuple(duplicates)
    if type(converted) is not dict:
        return None, (_invalid_type("manifest", "object"),)
    structure_issues = _structure_issues(converted)
    return (None, tuple(structure_issues)) if structure_issues else (converted, ())


def _canonical_payload(manifest: ClassWorldAssembledOutputManifest) -> dict[str, object]:
    value = json.loads(serialize_class_world_assembled_output_manifest(manifest))
    assert type(value) is dict
    return value


def verify_class_world_assembled_output_manifest_file_digest(
    path: str | Path,
    materialization_result: ClassWorldVerifiedMaterializationResult,
    expected_digest: ClassWorldAssembledOutputManifestDigest,
) -> ClassWorldAssembledOutputManifestFileDigestVerificationResult:
    """Read, bind, and digest-verify one explicit assembled-output manifest file."""
    manifest_path, path_issue = _validated_path(path)
    if path_issue is not None:
        return _failure(path_issue)
    assert manifest_path is not None

    digest_issue = _expected_digest_issue(expected_digest)
    if digest_issue is not None:
        return _failure(digest_issue)

    expected_result = build_class_world_assembled_output_manifest(materialization_result)
    if not expected_result.is_built:
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.MATERIALIZATION_INVALID,
                "materialization_result must produce one coherent assembled-output manifest.",
                "materialization_result",
            )
        )
    assert expected_result.manifest is not None
    assert expected_result.digest is not None

    filesystem_issue = _inspect_path(manifest_path)
    if filesystem_issue is not None:
        return _failure(filesystem_issue)
    try:
        with manifest_path.open("rb") as stream:
            content = stream.read(MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES + 1)
    except (OSError, ValueError):
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.FILE_READ_FAILED,
                "The assembled-output manifest file could not be read.",
                "path",
            )
        )
    if len(content) > MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES:
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.FILE_TOO_LARGE,
                (
                    "The assembled-output manifest exceeds the v0.1 limit of "
                    f"{MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES} UTF-8 bytes."
                ),
                "manifest",
            ),
            bytes_read=len(content),
        )
    if content.startswith(_UTF8_BOM):
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.FILE_BOM_NOT_ALLOWED,
                "Assembled-output manifest files must use UTF-8 without a byte-order mark.",
                "manifest",
            ),
            bytes_read=len(content),
        )
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.FILE_INVALID_UTF8,
                "The assembled-output manifest file must contain strictly valid UTF-8 text.",
                "manifest",
            ),
            bytes_read=len(content),
        )

    parsed, parse_issues = _parse_json(text)
    if parse_issues:
        return _failure(*parse_issues, bytes_read=len(content))
    assert parsed is not None
    if parsed != _canonical_payload(expected_result.manifest):
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestFileIssueCode.MANIFEST_MISMATCH,
                (
                    "The parsed manifest does not match the complete "
                    "materialization-authorized manifest."
                ),
                "manifest",
            ),
            bytes_read=len(content),
        )

    matches = expected_digest == expected_result.digest
    return ClassWorldAssembledOutputManifestFileDigestVerificationResult(
        manifest=expected_result.manifest,
        expected_digest=expected_digest,
        actual_digest=expected_result.digest,
        matches=matches,
        bytes_read=len(content),
        issues=(),
    )
