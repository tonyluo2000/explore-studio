"""Bounded verification of a materialized output tree against a verified manifest.

This layer consumes one already successfully verified assembled-output
manifest-file result plus one explicitly supplied output root. It confirms that
every manifest-authorized relative path resolves, descriptor-confined, to a
regular file under that root whose byte count and recomputed SHA-256 match the
manifest, and that the aggregate byte total agrees.

It never rereads or reparses the manifest file, never rebuilds the manifest
projection, never mutates the output tree, and never interprets artifact bytes
beyond hashing the bounded content it reads read-only.
"""

from __future__ import annotations

import errno
import hashlib
import os
import stat
import unicodedata
from contextlib import suppress
from pathlib import Path, PurePosixPath, PureWindowsPath

from explore.packages.class_world_artifact_file_verification_models import (
    MAX_CLASS_WORLD_ARTIFACT_SET_BYTES,
    MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES,
)
from explore.packages.class_world_assembled_output_manifest_file_digest_verification_models import (
    ClassWorldAssembledOutputManifestFileDigestVerificationResult,
)
from explore.packages.class_world_assembled_output_manifest_models import (
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM,
    ClassWorldAssembledOutputManifest,
    ClassWorldAssembledOutputPackage,
)
from explore.packages.class_world_output_tree_verification_models import (
    SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION,
    ClassWorldOutputTreeVerificationIssue,
    ClassWorldOutputTreeVerificationIssueCode,
    ClassWorldOutputTreeVerificationResult,
    ClassWorldVerifiedOutputArtifact,
)

_LOWERCASE_HEXADECIMAL = frozenset("0123456789abcdef")
_SYMLINK_ERRNOS = frozenset({errno.ELOOP, getattr(errno, "EMLINK", errno.ELOOP)})

_Code = ClassWorldOutputTreeVerificationIssueCode


def _issue(
    code: ClassWorldOutputTreeVerificationIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    package_index: int | None = None,
) -> ClassWorldOutputTreeVerificationIssue:
    return ClassWorldOutputTreeVerificationIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id,
        package_index=package_index,
    )


def _failure(
    issue: ClassWorldOutputTreeVerificationIssue,
) -> ClassWorldOutputTreeVerificationResult:
    return ClassWorldOutputTreeVerificationResult(
        contract_version=SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION,
        manifest=None,
        artifacts=(),
        total_bytes=None,
        issues=(issue,),
    )


def _is_sha256_hex(candidate: object) -> bool:
    return (
        type(candidate) is str
        and len(candidate) == 64
        and all(character in _LOWERCASE_HEXADECIMAL for character in candidate)
    )


def _verified_manifest(
    candidate: object,
) -> tuple[ClassWorldAssembledOutputManifest | None, ClassWorldOutputTreeVerificationIssue | None]:
    if candidate is None:
        return None, _issue(
            _Code.VERIFIED_MANIFEST_REQUIRED,
            "A successfully verified assembled-output manifest-file result is required.",
            "verified_manifest",
        )
    if type(candidate) is not ClassWorldAssembledOutputManifestFileDigestVerificationResult:
        return None, _issue(
            _Code.VERIFIED_MANIFEST_INVALID,
            "verified_manifest must be an assembled-output manifest-file "
            "digest verification result.",
            "verified_manifest",
        )
    if not candidate.is_verified:
        return None, _issue(
            _Code.VERIFIED_MANIFEST_NOT_VERIFIED,
            "verified_manifest must be one complete matching canonical manifest read.",
            "verified_manifest",
        )

    manifest = candidate.manifest
    if type(manifest) is not ClassWorldAssembledOutputManifest:
        return None, _issue(
            _Code.VERIFIED_MANIFEST_INVALID,
            "verified_manifest must retain one canonical assembled-output manifest.",
            "verified_manifest.manifest",
        )
    if (
        manifest.contract_version
        != SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION
        or type(manifest.packages) is not tuple
        or not manifest.packages
        or type(manifest.total_bytes) is not int
        or manifest.total_bytes < 0
    ):
        return None, _issue(
            _Code.VERIFIED_MANIFEST_INCONSISTENT,
            "verified_manifest.manifest must retain a coherent canonical package projection.",
            "verified_manifest.manifest",
        )

    running_total = 0
    for index, package in enumerate(manifest.packages):
        location = f"verified_manifest.manifest.packages[{index}]"
        if type(package) is not ClassWorldAssembledOutputPackage:
            return None, _issue(
                _Code.VERIFIED_MANIFEST_INCONSISTENT,
                f"{location} must be a canonical assembled-output package.",
                location,
            )
        if not (
            type(package.package_id) is str
            and package.package_id
            and type(package.package_version) is str
            and package.package_version
            and type(package.relative_path) is str
            and package.relative_path
            and type(package.digest_algorithm) is str
            and type(package.digest_hex) is str
            and type(package.bytes_written) is int
            and package.bytes_written >= 0
        ):
            return None, _issue(
                _Code.VERIFIED_MANIFEST_INCONSISTENT,
                f"{location} must retain canonical package identity and byte-count fields.",
                location,
            )
        running_total += package.bytes_written
    if running_total != manifest.total_bytes:
        return None, _issue(
            _Code.VERIFIED_MANIFEST_INCONSISTENT,
            "verified_manifest.manifest total_bytes must equal the sum of package byte counts.",
            "verified_manifest.manifest.total_bytes",
        )
    return manifest, None


def _validated_relative_path(
    candidate: str,
    index: int,
    package_id: str,
) -> tuple[PurePosixPath | None, ClassWorldOutputTreeVerificationIssue | None]:
    location = f"verified_manifest.manifest.packages[{index}].relative_path"
    reject = _issue(
        _Code.RELATIVE_PATH_INVALID,
        f"{location} must be one canonical output-root-relative forward-slash file path.",
        location,
        package_id=package_id,
        package_index=index,
    )
    if "\x00" in candidate or "\\" in candidate:
        return None, reject
    posix_path = PurePosixPath(candidate)
    windows_path = PureWindowsPath(candidate)
    if posix_path.is_absolute() or windows_path.is_absolute() or bool(windows_path.drive):
        return None, reject
    if ".." in posix_path.parts:
        return None, reject
    normalized = PurePosixPath(*posix_path.parts)
    if not normalized.parts or normalized.as_posix() == "." or normalized.as_posix() != candidate:
        return None, reject
    return normalized, None


def _validated_output_root(
    candidate: object,
) -> tuple[
    Path | None,
    os.stat_result | None,
    ClassWorldOutputTreeVerificationIssue | None,
]:
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_REQUIRED,
                "output_root must be a non-empty absolute str or pathlib.Path.",
                "output_root",
            ),
        )
    if not isinstance(candidate, (str, Path)):
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_INVALID_TYPE,
                "output_root must be a str or pathlib.Path.",
                "output_root",
            ),
        )
    root = Path(candidate)
    if not root.is_absolute():
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_NOT_ABSOLUTE,
                "output_root must be an absolute path.",
                "output_root",
            ),
        )
    if root.name in ("", ".", "..") or ".." in root.parts:
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_INVALID,
                "output_root must identify one canonical existing directory.",
                "output_root",
            ),
        )
    try:
        metadata = root.lstat()
    except FileNotFoundError:
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_NOT_FOUND,
                "output_root does not exist.",
                "output_root",
            ),
        )
    except (OSError, ValueError):
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_INSPECTION_FAILED,
                "output_root could not be inspected safely.",
                "output_root",
            ),
        )
    if stat.S_ISLNK(metadata.st_mode):
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_SYMLINK_NOT_ALLOWED,
                "output_root must not be a symbolic link.",
                "output_root",
            ),
        )
    if not stat.S_ISDIR(metadata.st_mode):
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_NOT_DIRECTORY,
                "output_root must be an existing directory.",
                "output_root",
            ),
        )
    try:
        resolved = root.resolve(strict=True)
    except (OSError, ValueError):
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_INSPECTION_FAILED,
                "output_root could not be resolved safely.",
                "output_root",
            ),
        )
    if resolved != root:
        return (
            None,
            None,
            _issue(
                _Code.OUTPUT_ROOT_SYMLINK_NOT_ALLOWED,
                "The output_root path must not pass through symbolic links.",
                "output_root",
            ),
        )
    return resolved, metadata, None


def _descriptor_confinement_available() -> bool:
    return (
        os.open in os.supports_dir_fd and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
    )


def _contains_symlink(root: Path, relative_path: PurePosixPath) -> bool:
    current = root
    for part in relative_path.parts:
        current = current / part
        try:
            if stat.S_ISLNK(current.lstat().st_mode):
                return True
        except (FileNotFoundError, OSError, ValueError):
            return False
    return False


def _open_confined(root_descriptor: int, parts: tuple[str, ...]) -> int:
    parent = os.dup(root_descriptor)
    try:
        for part in parts[:-1]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent,
            )
            os.close(parent)
            parent = child
        return os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_BINARY", 0) | os.O_NOFOLLOW,
            dir_fd=parent,
        )
    finally:
        with suppress(OSError):
            os.close(parent)


def _load_artifact(
    root_descriptor: int,
    parts: tuple[str, ...],
    expected_bytes: int,
    running_total: int,
    seen_identities: set[tuple[int, int]],
) -> tuple[bytes | None, ClassWorldOutputTreeVerificationIssueCode | None]:
    try:
        descriptor: int | None = _open_confined(root_descriptor, parts)
    except FileNotFoundError:
        return None, _Code.ARTIFACT_NOT_FOUND
    except ValueError:
        return None, _Code.ARTIFACT_READ_FAILED
    except OSError as error:
        if error.errno in _SYMLINK_ERRNOS:
            return None, _Code.ARTIFACT_SYMLINK_NOT_ALLOWED
        if error.errno == errno.ENOTDIR:
            return None, _Code.ARTIFACT_NOT_FOUND
        return None, _Code.ARTIFACT_READ_FAILED

    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            return None, _Code.ARTIFACT_NOT_REGULAR
        identity = (metadata.st_dev, metadata.st_ino)
        if identity in seen_identities:
            return None, _Code.ARTIFACT_IDENTITY_DUPLICATE
        if expected_bytes > MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES:
            return None, _Code.ARTIFACT_TOO_LARGE
        if running_total + expected_bytes > MAX_CLASS_WORLD_ARTIFACT_SET_BYTES:
            return None, _Code.OUTPUT_TREE_TOO_LARGE
        if metadata.st_size != expected_bytes:
            return None, _Code.BYTE_COUNT_MISMATCH
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            content = stream.read(expected_bytes + 1)
    except (OSError, ValueError):
        return None, _Code.ARTIFACT_READ_FAILED
    finally:
        if descriptor is not None:
            with suppress(OSError):
                os.close(descriptor)

    if len(content) != expected_bytes:
        return None, _Code.BYTE_COUNT_MISMATCH
    seen_identities.add(identity)
    return content, None


def verify_class_world_output_tree(
    verified_manifest: ClassWorldAssembledOutputManifestFileDigestVerificationResult,
    output_root: str | Path,
) -> ClassWorldOutputTreeVerificationResult:
    """Verify a materialized output tree against one verified assembled-output manifest."""
    manifest, manifest_issue = _verified_manifest(verified_manifest)
    if manifest_issue is not None:
        return _failure(manifest_issue)
    assert manifest is not None

    resolved_root, root_metadata, root_issue = _validated_output_root(output_root)
    if root_issue is not None:
        return _failure(root_issue)
    assert resolved_root is not None and root_metadata is not None

    normalized_paths: list[PurePosixPath] = []
    collision_keys: dict[str, int] = {}
    for index, package in enumerate(manifest.packages):
        if (
            package.digest_algorithm
            != SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM
        ):
            return _failure(
                _issue(
                    _Code.DIGEST_ALGORITHM_UNSUPPORTED,
                    'Every manifest package digest_algorithm must be exactly "sha256".',
                    f"verified_manifest.manifest.packages[{index}].digest_algorithm",
                    package_id=package.package_id,
                    package_index=index,
                )
            )
        if not _is_sha256_hex(package.digest_hex):
            return _failure(
                _issue(
                    _Code.DIGEST_ALGORITHM_UNSUPPORTED,
                    "Every manifest package digest_hex must be 64 lowercase "
                    "hexadecimal characters.",
                    f"verified_manifest.manifest.packages[{index}].digest_hex",
                    package_id=package.package_id,
                    package_index=index,
                )
            )
        normalized, path_issue = _validated_relative_path(
            package.relative_path, index, package.package_id
        )
        if path_issue is not None:
            return _failure(path_issue)
        assert normalized is not None
        key = unicodedata.normalize("NFC", normalized.as_posix()).casefold()
        if key in collision_keys:
            return _failure(
                _issue(
                    _Code.RELATIVE_PATH_COLLISION,
                    (
                        f"packages[{index}].relative_path collides with "
                        f"packages[{collision_keys[key]}].relative_path after normalization."
                    ),
                    f"verified_manifest.manifest.packages[{index}].relative_path",
                    package_id=package.package_id,
                    package_index=index,
                )
            )
        collision_keys[key] = index
        normalized_paths.append(normalized)

    if not _descriptor_confinement_available():
        return _failure(
            _issue(
                _Code.DESCRIPTOR_CONFINEMENT_UNAVAILABLE,
                "Descriptor-confined output-tree reads are unavailable on this platform.",
                "output_root",
            )
        )

    try:
        root_descriptor = os.open(resolved_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except (OSError, ValueError):
        return _failure(
            _issue(
                _Code.OUTPUT_ROOT_INSPECTION_FAILED,
                "output_root could not be opened for descriptor-confined reads.",
                "output_root",
            )
        )

    try:
        opened_root = os.fstat(root_descriptor)
        if (opened_root.st_dev, opened_root.st_ino) != (
            root_metadata.st_dev,
            root_metadata.st_ino,
        ):
            return _failure(
                _issue(
                    _Code.OUTPUT_ROOT_INSPECTION_FAILED,
                    "output_root changed identity before verification.",
                    "output_root",
                )
            )

        verified: list[ClassWorldVerifiedOutputArtifact] = []
        seen_identities: set[tuple[int, int]] = set()
        running_total = 0
        for index, (package, normalized) in enumerate(
            zip(manifest.packages, normalized_paths, strict=True)
        ):
            location = f"verified_manifest.manifest.packages[{index}].relative_path"
            if _contains_symlink(resolved_root, normalized):
                return _failure(
                    _issue(
                        _Code.ARTIFACT_SYMLINK_NOT_ALLOWED,
                        f"{location} must not refer to or pass through a symbolic link.",
                        location,
                        package_id=package.package_id,
                        package_index=index,
                    )
                )
            candidate = resolved_root.joinpath(*normalized.parts)
            try:
                escapes = not candidate.resolve(strict=False).is_relative_to(resolved_root)
            except (OSError, ValueError):
                escapes = True
            if escapes:
                return _failure(
                    _issue(
                        _Code.ARTIFACT_OUTSIDE_ROOT,
                        f"{location} resolves outside output_root.",
                        location,
                        package_id=package.package_id,
                        package_index=index,
                    )
                )

            content, read_code = _load_artifact(
                root_descriptor,
                normalized.parts,
                package.bytes_written,
                running_total,
                seen_identities,
            )
            if read_code is not None:
                return _failure(
                    _issue(
                        read_code,
                        f"{location} could not be verified against the manifest.",
                        location,
                        package_id=package.package_id,
                        package_index=index,
                    )
                )
            assert content is not None
            running_total += len(content)
            if hashlib.sha256(content).hexdigest() != package.digest_hex:
                return _failure(
                    _issue(
                        _Code.DIGEST_MISMATCH,
                        f"{location} SHA-256 does not equal the manifest digest_hex.",
                        location,
                        package_id=package.package_id,
                        package_index=index,
                    )
                )
            verified.append(
                ClassWorldVerifiedOutputArtifact(
                    package_id=package.package_id,
                    package_version=package.package_version,
                    relative_path=package.relative_path,
                    digest_algorithm=package.digest_algorithm,
                    digest_hex=package.digest_hex,
                    bytes_verified=len(content),
                )
            )
    finally:
        with suppress(OSError):
            os.close(root_descriptor)

    if running_total != manifest.total_bytes:
        return _failure(
            _issue(
                _Code.AGGREGATE_BYTE_TOTAL_MISMATCH,
                "The verified output-tree byte total does not equal manifest total_bytes.",
                "verified_manifest.manifest.total_bytes",
            )
        )

    return ClassWorldOutputTreeVerificationResult(
        contract_version=SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION,
        manifest=manifest,
        artifacts=tuple(verified),
        total_bytes=running_total,
        issues=(),
    )
