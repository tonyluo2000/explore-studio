"""Deterministic creation and bounded readback of Class-World release bundles."""

from __future__ import annotations

import hashlib
import io
import os
import secrets
import stat
import zipfile
from contextlib import suppress
from pathlib import Path

from explore.packages import class_world_output_tree_verification as _tree
from explore.packages.class_world_assembled_output_manifest import (
    build_class_world_assembled_output_manifest,
    serialize_class_world_assembled_output_manifest,
)
from explore.packages.class_world_assembled_output_manifest_models import (
    ClassWorldAssembledOutputManifest,
)
from explore.packages.class_world_output_tree_verification_models import (
    SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION,
    ClassWorldOutputTreeVerificationResult,
    ClassWorldVerifiedOutputArtifact,
)
from explore.packages.class_world_release_bundle_models import (
    CLASS_WORLD_RELEASE_BUNDLE_DECLARATION_PATH,
    CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE,
    CLASS_WORLD_RELEASE_BUNDLE_OUTPUT_MANIFEST_PATH,
    MAX_CLASS_WORLD_RELEASE_BUNDLE_BYTES,
    SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_DIGEST_ALGORITHM,
    ClassWorldReleaseBundle,
    ClassWorldReleaseBundleDigest,
    ClassWorldReleaseBundleEntry,
    ClassWorldReleaseBundleIssue,
    ClassWorldReleaseBundleIssueCode,
    ClassWorldReleaseBundleVerificationResult,
    ClassWorldReleaseBundleWriteResult,
)
from explore.packages.class_world_release_declaration_digest import (
    compute_class_world_release_declaration_digest,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)
from explore.packages.class_world_release_declaration_serialization import (
    serialize_class_world_release_declaration,
)
from explore.packages.class_world_verified_materialization_models import (
    ClassWorldVerifiedMaterializationResult,
)

_Code = ClassWorldReleaseBundleIssueCode
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ZIP_SYSTEM_UNIX = 3
_ZIP_STORED = zipfile.ZIP_STORED
_ZIP_FILE_EXTERNAL_ATTRIBUTES = (stat.S_IFREG | CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE) << 16
_HEX = frozenset("0123456789abcdef")


def _issue(
    code: ClassWorldReleaseBundleIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    package_index: int | None = None,
) -> ClassWorldReleaseBundleIssue:
    return ClassWorldReleaseBundleIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id,
        package_index=package_index,
    )


def _write_failure(*issues: ClassWorldReleaseBundleIssue) -> ClassWorldReleaseBundleWriteResult:
    return ClassWorldReleaseBundleWriteResult(None, None, 0, tuple(issues))


def _verification_failure(
    *issues: ClassWorldReleaseBundleIssue,
    bytes_read: int = 0,
) -> ClassWorldReleaseBundleVerificationResult:
    return ClassWorldReleaseBundleVerificationResult(
        None, None, None, None, bytes_read, tuple(issues)
    )


def _is_digest(value: object) -> bool:
    return (
        type(value) is ClassWorldReleaseBundleDigest
        and value.algorithm == SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_DIGEST_ALGORITHM
        and type(value.hex_digest) is str
        and len(value.hex_digest) == 64
        and all(character in _HEX for character in value.hex_digest)
    )


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _bundle_projection(
    candidate: object,
) -> tuple[
    ClassWorldReleaseBundle | None,
    bytes | None,
    bytes | None,
    ClassWorldReleaseBundleIssue | None,
]:
    if candidate is None:
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_RESULT_REQUIRED,
                "A verified output-tree result is required.",
                "output_tree_result",
            ),
        )
    if type(candidate) is not ClassWorldOutputTreeVerificationResult:
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_RESULT_INVALID,
                "output_tree_result must be a ClassWorld output-tree verification result.",
                "output_tree_result",
            ),
        )
    result = candidate
    if (
        result.contract_version != SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION
        or not result.is_verified
        or type(result.issues) is not tuple
        or result.issues
        or type(result.manifest) is not ClassWorldAssembledOutputManifest
        or type(result.manifest.packages) is not tuple
        or type(result.artifacts) is not tuple
        or not result.artifacts
        or type(result.total_bytes) is not int
    ):
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_NOT_VERIFIED,
                "output_tree_result must contain one complete successful verification.",
                "output_tree_result",
            ),
        )

    manifest = result.manifest
    materialization = manifest.materialization
    rebuilt = build_class_world_assembled_output_manifest(
        ClassWorldVerifiedMaterializationResult(
            materialization=materialization,
            source_verification=getattr(materialization, "source_verification", None),
            issues=(),
        )
    )
    artifacts_match = len(result.artifacts) == len(manifest.packages) and all(
        type(artifact) is ClassWorldVerifiedOutputArtifact
        and type(artifact.bytes_verified) is int
        and artifact.package_id == package.package_id
        and artifact.package_version == package.package_version
        and artifact.relative_path == package.relative_path
        and artifact.digest_algorithm == package.digest_algorithm
        and artifact.digest_hex == package.digest_hex
        and artifact.bytes_verified == package.bytes_written
        for artifact, package in zip(result.artifacts, manifest.packages, strict=False)
    )
    if (
        not rebuilt.is_built
        or rebuilt.manifest != manifest
        or rebuilt.digest is None
        or not artifacts_match
        or result.total_bytes != manifest.total_bytes
    ):
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_INCONSISTENT,
                "output_tree_result is inconsistent with its canonical materialization graph.",
                "output_tree_result",
            ),
        )

    try:
        inventory = (
            materialization.plan.file_verification.content_verification.verification.plan.inventory
        )
        declaration = inventory.declaration
        retained_declaration_digest = inventory.declaration_digest
    except AttributeError:
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_INCONSISTENT,
                "output_tree_result does not retain canonical release provenance.",
                "output_tree_result.manifest.materialization",
            ),
        )
    if type(declaration) is not ClassWorldReleaseDeclaration:
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_INCONSISTENT,
                "The retained release declaration is invalid.",
                "output_tree_result.manifest.materialization",
            ),
        )
    try:
        declaration_bytes = serialize_class_world_release_declaration(declaration).encode("utf-8")
        declaration_digest = compute_class_world_release_declaration_digest(declaration)
        manifest_bytes = serialize_class_world_assembled_output_manifest(manifest).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_INCONSISTENT,
                "The retained release metadata cannot be canonically serialized.",
                "output_tree_result.manifest",
            ),
        )
    if declaration_digest != retained_declaration_digest:
        return (
            None,
            None,
            None,
            _issue(
                _Code.OUTPUT_TREE_INCONSISTENT,
                "The retained release-declaration digest is inconsistent.",
                "output_tree_result.manifest.materialization",
            ),
        )

    metadata_entries = (
        ClassWorldReleaseBundleEntry(
            CLASS_WORLD_RELEASE_BUNDLE_DECLARATION_PATH,
            "sha256",
            _sha256(declaration_bytes),
            len(declaration_bytes),
            CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE,
        ),
        ClassWorldReleaseBundleEntry(
            CLASS_WORLD_RELEASE_BUNDLE_OUTPUT_MANIFEST_PATH,
            "sha256",
            _sha256(manifest_bytes),
            len(manifest_bytes),
            CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE,
        ),
    )
    package_entries = tuple(
        ClassWorldReleaseBundleEntry(
            package.relative_path,
            package.digest_algorithm,
            package.digest_hex,
            package.bytes_written,
            CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE,
        )
        for package in manifest.packages
    )
    entries = metadata_entries + package_entries
    bundle = ClassWorldReleaseBundle(
        contract_version=SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_CONTRACT_VERSION,
        declaration=declaration,
        declaration_digest=declaration_digest,
        output_manifest=manifest,
        output_manifest_digest=rebuilt.digest,
        entries=entries,
        total_content_bytes=sum(entry.bytes_written for entry in entries),
    )
    return bundle, declaration_bytes, manifest_bytes, None


def _validated_path(
    candidate: object,
    *,
    location: str,
    required: ClassWorldReleaseBundleIssueCode,
    invalid_type: ClassWorldReleaseBundleIssueCode,
    not_absolute: ClassWorldReleaseBundleIssueCode,
    invalid: ClassWorldReleaseBundleIssueCode,
) -> tuple[Path | None, ClassWorldReleaseBundleIssue | None]:
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return None, _issue(required, f"{location} must be a non-empty absolute path.", location)
    if not isinstance(candidate, (str, Path)):
        return None, _issue(invalid_type, f"{location} must be a str or pathlib.Path.", location)
    try:
        path = Path(candidate)
        if not path.is_absolute():
            return None, _issue(not_absolute, f"{location} must be an absolute path.", location)
        if path.name in ("", ".", ".."):
            raise ValueError
    except (OSError, TypeError, ValueError):
        return None, _issue(invalid, f"{location} is not a usable path.", location)
    return path, None


def _has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor)
    try:
        for part in path.parts[1:]:
            current /= part
            if current.is_symlink():
                return True
    except (OSError, ValueError):
        return True
    return False


def _destination_state(
    path: Path,
) -> tuple[os.stat_result | None, ClassWorldReleaseBundleIssue | None]:
    parent = path.parent
    if not parent.exists():
        return None, _issue(
            _Code.DESTINATION_PARENT_NOT_FOUND,
            "The destination parent does not exist.",
            "destination",
        )
    if _has_symlink_component(parent):
        return None, _issue(
            _Code.DESTINATION_PARENT_SYMLINK_NOT_ALLOWED,
            "The destination parent must not contain symbolic links.",
            "destination",
        )
    try:
        if not parent.is_dir():
            return None, _issue(
                _Code.DESTINATION_PARENT_NOT_DIRECTORY,
                "The destination parent must be a directory.",
                "destination",
            )
        path.lstat()
    except FileNotFoundError:
        try:
            return parent.stat(), None
        except (OSError, ValueError):
            return None, _issue(
                _Code.DESTINATION_INVALID,
                "The destination parent could not be inspected.",
                "destination",
            )
    except (OSError, ValueError):
        return None, _issue(
            _Code.DESTINATION_INVALID,
            "The destination could not be inspected.",
            "destination",
        )
    return None, _issue(
        _Code.DESTINATION_EXISTS,
        "The destination must not already exist.",
        "destination",
    )


def _load_payloads(
    output_root: object,
    bundle: ClassWorldReleaseBundle,
) -> tuple[tuple[bytes, ...] | None, ClassWorldReleaseBundleIssue | None]:
    path, path_issue = _validated_path(
        output_root,
        location="output_root",
        required=_Code.OUTPUT_ROOT_REQUIRED,
        invalid_type=_Code.OUTPUT_ROOT_INVALID_TYPE,
        not_absolute=_Code.OUTPUT_ROOT_NOT_ABSOLUTE,
        invalid=_Code.OUTPUT_ROOT_INVALID,
    )
    if path_issue is not None:
        return None, path_issue
    assert path is not None
    resolved, metadata, root_issue = _tree._validated_output_root(path)
    if root_issue is not None:
        mapping = {
            _tree._Code.OUTPUT_ROOT_NOT_FOUND: _Code.OUTPUT_ROOT_NOT_FOUND,
            _tree._Code.OUTPUT_ROOT_SYMLINK_NOT_ALLOWED: _Code.OUTPUT_ROOT_SYMLINK_NOT_ALLOWED,
            _tree._Code.OUTPUT_ROOT_NOT_DIRECTORY: _Code.OUTPUT_ROOT_NOT_DIRECTORY,
        }
        return None, _issue(
            mapping.get(root_issue.code, _Code.OUTPUT_ROOT_INSPECTION_FAILED),
            root_issue.message,
            "output_root",
        )
    assert resolved is not None and metadata is not None
    if not _tree._descriptor_confinement_available():
        return None, _issue(
            _Code.DESCRIPTOR_CONFINEMENT_UNAVAILABLE,
            "Descriptor-confined output-tree reads are unavailable on this platform.",
            "output_root",
        )
    try:
        root_descriptor = os.open(resolved, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except (OSError, ValueError):
        return None, _issue(
            _Code.OUTPUT_ROOT_INSPECTION_FAILED,
            "output_root could not be opened for descriptor-confined reads.",
            "output_root",
        )

    payloads: list[bytes] = []
    seen: set[tuple[int, int]] = set()
    running_total = 0
    try:
        opened = os.fstat(root_descriptor)
        if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
            return None, _issue(
                _Code.OUTPUT_ROOT_INSPECTION_FAILED,
                "output_root changed identity before bundle creation.",
                "output_root",
            )
        for index, package in enumerate(bundle.output_manifest.packages):
            normalized, relative_issue = _tree._validated_relative_path(
                package.relative_path, index, package.package_id
            )
            if relative_issue is not None or normalized is None:
                return None, _issue(
                    _Code.OUTPUT_TREE_INCONSISTENT,
                    "A canonical package path is invalid.",
                    f"output_tree_result.artifacts[{index}].relative_path",
                    package_id=package.package_id,
                    package_index=index,
                )
            if _tree._contains_symlink(resolved, normalized):
                return None, _issue(
                    _Code.PAYLOAD_READ_FAILED,
                    "A package payload path contains a symbolic link.",
                    package.relative_path,
                    package_id=package.package_id,
                    package_index=index,
                )
            content, read_code = _tree._load_artifact(
                root_descriptor,
                normalized.parts,
                package.bytes_written,
                running_total,
                seen,
            )
            if read_code is not None or content is None:
                return None, _issue(
                    _Code.PAYLOAD_READ_FAILED,
                    "A verified package payload could not be reread safely.",
                    package.relative_path,
                    package_id=package.package_id,
                    package_index=index,
                )
            if _sha256(content) != package.digest_hex:
                return None, _issue(
                    _Code.PAYLOAD_MISMATCH,
                    "A package payload no longer matches its verified digest.",
                    package.relative_path,
                    package_id=package.package_id,
                    package_index=index,
                )
            payloads.append(content)
            running_total += len(content)
    except (OSError, ValueError):
        return None, _issue(
            _Code.PAYLOAD_READ_FAILED,
            "The verified package payload tree could not be read.",
            "output_root",
        )
    finally:
        with suppress(OSError):
            os.close(root_descriptor)
    if running_total != bundle.output_manifest.total_bytes:
        return None, _issue(
            _Code.PAYLOAD_MISMATCH,
            "The package payload total no longer matches the verified manifest.",
            "output_root",
        )
    return tuple(payloads), None


def _zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, _ZIP_TIMESTAMP)
    info.compress_type = _ZIP_STORED
    info.create_system = _ZIP_SYSTEM_UNIX
    info.external_attr = _ZIP_FILE_EXTERNAL_ATTRIBUTES
    info.internal_attr = 0
    info.extra = b""
    info.comment = b""
    return info


def _write_archive(
    target: io.BufferedIOBase,
    entries: tuple[ClassWorldReleaseBundleEntry, ...],
    contents: tuple[bytes, ...],
) -> None:
    with zipfile.ZipFile(target, "w", compression=_ZIP_STORED, allowZip64=False) as archive:
        archive.comment = b""
        for entry, content in zip(entries, contents, strict=True):
            archive.writestr(_zip_info(entry.relative_path), content)


def write_class_world_release_bundle(
    output_tree_result: ClassWorldOutputTreeVerificationResult,
    output_root: str | Path,
    destination: str | Path,
) -> ClassWorldReleaseBundleWriteResult:
    """Atomically write one deterministic self-contained Class-World ZIP archive."""
    bundle, declaration_bytes, manifest_bytes, projection_issue = _bundle_projection(
        output_tree_result
    )
    if projection_issue is not None:
        return _write_failure(projection_issue)
    assert bundle is not None and declaration_bytes is not None and manifest_bytes is not None

    payloads, payload_issue = _load_payloads(output_root, bundle)
    if payload_issue is not None:
        return _write_failure(payload_issue)
    assert payloads is not None

    destination_path, path_issue = _validated_path(
        destination,
        location="destination",
        required=_Code.DESTINATION_REQUIRED,
        invalid_type=_Code.DESTINATION_INVALID_TYPE,
        not_absolute=_Code.DESTINATION_NOT_ABSOLUTE,
        invalid=_Code.DESTINATION_INVALID,
    )
    if path_issue is not None:
        return _write_failure(path_issue)
    assert destination_path is not None
    parent_metadata, destination_issue = _destination_state(destination_path)
    if destination_issue is not None:
        return _write_failure(destination_issue)
    assert parent_metadata is not None

    parent_descriptor: int | None = None
    staging_descriptor: int | None = None
    staging_name: str | None = None
    published = False
    failure_issue: ClassWorldReleaseBundleIssue | None = None
    try:
        if (
            os.open not in os.supports_dir_fd
            or os.stat not in os.supports_dir_fd
            or os.unlink not in os.supports_dir_fd
            or os.link not in os.supports_dir_fd
            or not hasattr(os, "O_DIRECTORY")
            or not hasattr(os, "O_NOFOLLOW")
        ):
            raise OSError("descriptor-confined bundle output is unavailable")
        parent_descriptor = os.open(
            destination_path.parent,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        opened_parent = os.fstat(parent_descriptor)
        if (opened_parent.st_dev, opened_parent.st_ino) != (
            parent_metadata.st_dev,
            parent_metadata.st_ino,
        ):
            raise OSError("destination parent identity changed")
        try:
            os.stat(destination_path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            failure_issue = _issue(
                _Code.DESTINATION_EXISTS,
                "The destination must not already exist.",
                "destination",
            )
        if failure_issue is None:
            for _ in range(100):
                candidate = f".class-world-bundle-{secrets.token_hex(12)}.tmp"
                try:
                    staging_descriptor = os.open(
                        candidate,
                        os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=parent_descriptor,
                    )
                except FileExistsError:
                    continue
                staging_name = candidate
                break
            if staging_descriptor is None or staging_name is None:
                raise OSError("bundle staging file could not be created")
            with os.fdopen(os.dup(staging_descriptor), "w+b") as stream:
                _write_archive(
                    stream,
                    bundle.entries,
                    (declaration_bytes, manifest_bytes) + payloads,
                )
                stream.flush()
                os.fsync(stream.fileno())
            archive_size = os.fstat(staging_descriptor).st_size
        else:
            archive_size = 0
        if archive_size > MAX_CLASS_WORLD_RELEASE_BUNDLE_BYTES:
            raise OSError("release bundle exceeds its bounded archive size")
        if failure_issue is None:
            assert staging_descriptor is not None and staging_name is not None
            os.fchmod(staging_descriptor, CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE)
            os.fsync(staging_descriptor)
            os.lseek(staging_descriptor, 0, os.SEEK_SET)
            with os.fdopen(os.dup(staging_descriptor), "rb") as stream:
                digest = ClassWorldReleaseBundleDigest(
                    "sha256", hashlib.file_digest(stream, "sha256").hexdigest()
                )
            current_parent = os.fstat(parent_descriptor)
            if (current_parent.st_dev, current_parent.st_ino) != (
                parent_metadata.st_dev,
                parent_metadata.st_ino,
            ):
                raise OSError("destination parent identity changed")
            try:
                os.link(
                    staging_name,
                    destination_path.name,
                    src_dir_fd=parent_descriptor,
                    dst_dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError:
                failure_issue = _issue(
                    _Code.DESTINATION_EXISTS,
                    "The destination must not already exist.",
                    "destination",
                )
            else:
                published = True
                os.unlink(staging_name, dir_fd=parent_descriptor)
                staging_name = None
                os.fsync(parent_descriptor)
    except (OSError, ValueError, zipfile.LargeZipFile):
        code = _Code.ARCHIVE_PUBLISH_FAILED if published else _Code.ARCHIVE_WRITE_FAILED
        failure_issue = _issue(
            code,
            "The deterministic release bundle could not be atomically written.",
            "destination",
        )
    finally:
        if staging_descriptor is not None:
            with suppress(OSError):
                os.close(staging_descriptor)
        if staging_name is not None and parent_descriptor is not None:
            try:
                os.unlink(staging_name, dir_fd=parent_descriptor)
                staging_name = None
            except OSError:
                if not published:
                    failure_issue = _issue(
                        _Code.ARCHIVE_CLEANUP_FAILED,
                        "The operation-owned staging file could not be removed.",
                        "destination",
                    )
        if parent_descriptor is not None:
            with suppress(OSError):
                os.close(parent_descriptor)

    if failure_issue is not None:
        return _write_failure(failure_issue)
    return ClassWorldReleaseBundleWriteResult(bundle, digest, archive_size, ())


def _archive_path_issue(path: Path) -> ClassWorldReleaseBundleIssue | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return _issue(_Code.ARCHIVE_NOT_FOUND, "The release bundle does not exist.", "path")
    except (OSError, ValueError):
        return _issue(
            _Code.ARCHIVE_READ_FAILED, "The release bundle could not be inspected.", "path"
        )
    if _has_symlink_component(path):
        return _issue(
            _Code.ARCHIVE_SYMLINK_NOT_ALLOWED,
            "The release-bundle path must not contain symbolic links.",
            "path",
        )
    if not stat.S_ISREG(metadata.st_mode):
        return _issue(
            _Code.ARCHIVE_NOT_REGULAR, "The release bundle must be a regular file.", "path"
        )
    if metadata.st_size > MAX_CLASS_WORLD_RELEASE_BUNDLE_BYTES:
        return _issue(
            _Code.ARCHIVE_TOO_LARGE, "The release bundle exceeds the v0.1 size limit.", "path"
        )
    return None


def _canonical_member_metadata(info: zipfile.ZipInfo) -> bool:
    return (
        info.date_time == _ZIP_TIMESTAMP
        and info.create_system == _ZIP_SYSTEM_UNIX
        and info.create_version == 20
        and info.extract_version == 20
        and info.reserved == 0
        and info.flag_bits == 0
        and info.volume == 0
        and info.compress_type == _ZIP_STORED
        and info.external_attr == _ZIP_FILE_EXTERNAL_ATTRIBUTES
        and info.internal_attr == 0
        and info.extra == b""
        and info.comment == b""
        and not info.is_dir()
    )


def verify_class_world_release_bundle_file(
    path: str | Path,
    output_tree_result: ClassWorldOutputTreeVerificationResult,
    expected_digest: ClassWorldReleaseBundleDigest,
) -> ClassWorldReleaseBundleVerificationResult:
    """Read and verify one deterministic release bundle without extracting it."""
    bundle, declaration_bytes, manifest_bytes, projection_issue = _bundle_projection(
        output_tree_result
    )
    if projection_issue is not None:
        return _verification_failure(projection_issue)
    assert bundle is not None and declaration_bytes is not None and manifest_bytes is not None
    if not _is_digest(expected_digest):
        return _verification_failure(
            _issue(
                _Code.EXPECTED_DIGEST_INVALID,
                'expected_digest must be one "sha256" digest with 64 lowercase '
                "hexadecimal characters.",
                "expected_digest",
            )
        )
    archive_path, path_issue = _validated_path(
        path,
        location="path",
        required=_Code.PATH_REQUIRED,
        invalid_type=_Code.PATH_INVALID_TYPE,
        not_absolute=_Code.PATH_NOT_ABSOLUTE,
        invalid=_Code.PATH_INVALID,
    )
    if path_issue is not None:
        return _verification_failure(path_issue)
    assert archive_path is not None
    archive_issue = _archive_path_issue(archive_path)
    if archive_issue is not None:
        return _verification_failure(archive_issue)
    descriptor: int | None = None
    try:
        descriptor = os.open(
            archive_path,
            os.O_RDONLY | getattr(os, "O_BINARY", 0) | os.O_NOFOLLOW,
        )
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            return _verification_failure(
                _issue(
                    _Code.ARCHIVE_NOT_REGULAR,
                    "The release bundle must remain a regular file.",
                    "path",
                )
            )
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            content = stream.read(MAX_CLASS_WORLD_RELEASE_BUNDLE_BYTES + 1)
    except (OSError, ValueError):
        return _verification_failure(
            _issue(_Code.ARCHIVE_READ_FAILED, "The release bundle could not be read.", "path")
        )
    finally:
        if descriptor is not None:
            with suppress(OSError):
                os.close(descriptor)
    if len(content) > MAX_CLASS_WORLD_RELEASE_BUNDLE_BYTES:
        return _verification_failure(
            _issue(
                _Code.ARCHIVE_TOO_LARGE, "The release bundle exceeds the v0.1 size limit.", "path"
            ),
            bytes_read=len(content),
        )
    actual_digest = ClassWorldReleaseBundleDigest("sha256", _sha256(content))

    expected_paths = tuple(entry.relative_path for entry in bundle.entries)
    expected_contents = (declaration_bytes, manifest_bytes)
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
            if archive.comment != b"":
                raise ValueError("archive comment")
            members = archive.infolist()
            if tuple(member.filename for member in members) != expected_paths:
                return _verification_failure(
                    _issue(
                        _Code.ARCHIVE_MEMBER_MISMATCH,
                        "Release-bundle members do not equal the canonical ordered member set.",
                        "archive.members",
                    ),
                    bytes_read=len(content),
                )
            for index, (member, entry) in enumerate(zip(members, bundle.entries, strict=True)):
                if not _canonical_member_metadata(member):
                    return _verification_failure(
                        _issue(
                            _Code.ARCHIVE_METADATA_MISMATCH,
                            "A release-bundle member has noncanonical ZIP metadata.",
                            f"archive.members[{index}]",
                            package_index=index - 2 if index >= 2 else None,
                        ),
                        bytes_read=len(content),
                    )
                if (
                    member.file_size != entry.bytes_written
                    or member.compress_size != entry.bytes_written
                ):
                    return _verification_failure(
                        _issue(
                            _Code.ARCHIVE_CONTENT_MISMATCH,
                            "A release-bundle member has a noncanonical byte count.",
                            f"archive.members[{index}]",
                        ),
                        bytes_read=len(content),
                    )
                member_content = archive.read(member)
                if index < 2:
                    matches = member_content == expected_contents[index]
                else:
                    matches = _sha256(member_content) == entry.digest_hex
                if not matches:
                    return _verification_failure(
                        _issue(
                            _Code.ARCHIVE_CONTENT_MISMATCH,
                            "A release-bundle member does not match its canonical "
                            "content identity.",
                            f"archive.members[{index}]",
                            package_index=index - 2 if index >= 2 else None,
                        ),
                        bytes_read=len(content),
                    )
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError):
        return _verification_failure(
            _issue(
                _Code.ARCHIVE_INVALID,
                "The release bundle is not a valid canonical ZIP archive.",
                "archive",
            ),
            bytes_read=len(content),
        )

    return ClassWorldReleaseBundleVerificationResult(
        bundle=bundle,
        expected_digest=expected_digest,
        actual_digest=actual_digest,
        matches=actual_digest == expected_digest,
        bytes_read=len(content),
        issues=(),
    )
