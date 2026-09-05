"""Deterministic, bounded export of validated Explorer Packages."""

from __future__ import annotations

import hashlib
import io
import json
import os
import secrets
import stat
import zipfile
from contextlib import suppress
from pathlib import Path, PurePosixPath

from explore.packages.explorer_package_export_models import (
    EXPLORER_PACKAGE_EXPORT_FILE_MODE,
    MAX_EXPLORER_PACKAGE_EXPORT_ARCHIVE_BYTES,
    MAX_EXPLORER_PACKAGE_EXPORT_CONTENT_BYTES,
    MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES,
    SUPPORTED_EXPLORER_PACKAGE_EXPORT_CONTRACT_VERSION,
    SUPPORTED_EXPLORER_PACKAGE_EXPORT_DIGEST_ALGORITHM,
    ExplorerPackageExportArtifact,
    ExplorerPackageExportDigest,
    ExplorerPackageExportEntry,
    ExplorerPackageExportIssue,
    ExplorerPackageExportIssueCode,
    ExplorerPackageExportResult,
)
from explore.packages.loader import load_explorer_package

_Code = ExplorerPackageExportIssueCode
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ZIP_SYSTEM_UNIX = 3
_ZIP_STORED = zipfile.ZIP_STORED
_ZIP_FILE_EXTERNAL_ATTRIBUTES = (stat.S_IFREG | EXPLORER_PACKAGE_EXPORT_FILE_MODE) << 16


def _issue(
    code: ExplorerPackageExportIssueCode,
    message: str,
    location: str,
    *,
    member_path: str | None = None,
    member_index: int | None = None,
) -> ExplorerPackageExportIssue:
    return ExplorerPackageExportIssue(code, message, location, member_path, member_index)


def _failure(*issues: ExplorerPackageExportIssue) -> ExplorerPackageExportResult:
    return ExplorerPackageExportResult(None, None, 0, tuple(issues))


def _has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor)
    try:
        for part in path.parts[1:]:
            current /= part
            if stat.S_ISLNK(current.lstat().st_mode):
                return True
    except (OSError, ValueError):
        return False
    return False


def _validated_root(candidate: object) -> tuple[Path | None, ExplorerPackageExportIssue | None]:
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return None, _issue(
            _Code.PACKAGE_ROOT_REQUIRED,
            "package_root must be a non-empty absolute path.",
            "package_root",
        )
    if not isinstance(candidate, (str, Path)):
        return None, _issue(
            _Code.PACKAGE_ROOT_INVALID_TYPE,
            "package_root must be a str or pathlib.Path.",
            "package_root",
        )
    path = Path(candidate)
    if not path.is_absolute():
        return None, _issue(
            _Code.PACKAGE_ROOT_NOT_ABSOLUTE,
            "package_root must be an absolute path.",
            "package_root",
        )
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None, _issue(
            _Code.PACKAGE_ROOT_NOT_FOUND, "package_root does not exist.", "package_root"
        )
    except (OSError, ValueError):
        return None, _issue(
            _Code.PACKAGE_ROOT_INSPECTION_FAILED,
            "package_root could not be inspected.",
            "package_root",
        )
    if _has_symlink_component(path):
        return None, _issue(
            _Code.PACKAGE_ROOT_SYMLINK_NOT_ALLOWED,
            "package_root must not contain symbolic links.",
            "package_root",
        )
    if not stat.S_ISDIR(metadata.st_mode):
        return None, _issue(
            _Code.PACKAGE_ROOT_NOT_DIRECTORY,
            "package_root must be an existing directory.",
            "package_root",
        )
    try:
        return path.resolve(strict=True), None
    except (OSError, ValueError):
        return None, _issue(
            _Code.PACKAGE_ROOT_INSPECTION_FAILED,
            "package_root could not be resolved.",
            "package_root",
        )


def _read_member(
    root_descriptor: int,
    relative_path: str,
    index: int,
) -> tuple[bytes | None, tuple[int, int] | None, ExplorerPackageExportIssue | None]:
    descriptor: int | None = None
    parent_descriptor: int | None = None
    try:
        parent_descriptor = os.dup(root_descriptor)
        parts = PurePosixPath(relative_path).parts
        for part in parts[:-1]:
            next_descriptor = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent_descriptor,
            )
            os.close(parent_descriptor)
            parent_descriptor = next_descriptor
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_BINARY", 0) | os.O_NOFOLLOW,
            dir_fd=parent_descriptor,
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            return (
                None,
                None,
                _issue(
                    _Code.MEMBER_NOT_REGULAR,
                    "An export member must be a regular file.",
                    f"members[{index}]",
                    member_path=relative_path,
                    member_index=index,
                ),
            )
        if before.st_size > MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES:
            return (
                None,
                None,
                _issue(
                    _Code.MEMBER_TOO_LARGE,
                    "An export member exceeds the v0.1 per-member limit.",
                    f"members[{index}]",
                    member_path=relative_path,
                    member_index=index,
                ),
            )
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            content = stream.read(MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES + 1)
            after = os.fstat(stream.fileno())
        if len(content) > MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES:
            return (
                None,
                None,
                _issue(
                    _Code.MEMBER_TOO_LARGE,
                    "An export member exceeds the v0.1 per-member limit.",
                    f"members[{index}]",
                    member_path=relative_path,
                    member_index=index,
                ),
            )
        stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
            return (
                None,
                None,
                _issue(
                    _Code.PACKAGE_CHANGED,
                    "An export member changed while it was being read.",
                    f"members[{index}]",
                    member_path=relative_path,
                    member_index=index,
                ),
            )
        return content, (after.st_dev, after.st_ino), None
    except FileNotFoundError:
        return (
            None,
            None,
            _issue(
                _Code.MEMBER_NOT_FOUND,
                "An export member no longer exists.",
                f"members[{index}]",
                member_path=relative_path,
                member_index=index,
            ),
        )
    except (OSError, ValueError):
        return (
            None,
            None,
            _issue(
                _Code.MEMBER_READ_FAILED,
                "An export member could not be read safely.",
                f"members[{index}]",
                member_path=relative_path,
                member_index=index,
            ),
        )
    finally:
        if descriptor is not None:
            with suppress(OSError):
                os.close(descriptor)
        if parent_descriptor is not None:
            with suppress(OSError):
                os.close(parent_descriptor)


def _snapshot(
    root_descriptor: int,
    paths: tuple[str, ...],
) -> tuple[tuple[bytes, ...] | None, ExplorerPackageExportIssue | None]:
    contents: list[bytes] = []
    identities: set[tuple[int, int]] = set()
    total = 0
    for index, path in enumerate(paths):
        content, identity, issue = _read_member(root_descriptor, path, index)
        if issue is not None:
            return None, issue
        assert content is not None and identity is not None
        if identity in identities:
            return None, _issue(
                _Code.PACKAGE_CHANGED,
                "Two export members alias the same file.",
                f"members[{index}]",
                member_path=path,
                member_index=index,
            )
        identities.add(identity)
        total += len(content)
        if total > MAX_EXPLORER_PACKAGE_EXPORT_CONTENT_BYTES:
            return None, _issue(
                _Code.CONTENT_TOO_LARGE,
                "The package exceeds the v0.1 aggregate content limit.",
                "members",
            )
        contents.append(content)
    return tuple(contents), None


def _validated_destination(
    candidate: object,
    expected_name: str,
) -> tuple[Path | None, os.stat_result | None, ExplorerPackageExportIssue | None]:
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_REQUIRED,
                "destination must be a non-empty absolute path.",
                "destination",
            ),
        )
    if not isinstance(candidate, (str, Path)):
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_INVALID_TYPE,
                "destination must be a str or pathlib.Path.",
                "destination",
            ),
        )
    path = Path(candidate)
    if not path.is_absolute():
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_NOT_ABSOLUTE,
                "destination must be an absolute path.",
                "destination",
            ),
        )
    if path.name != expected_name:
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_NAME_MISMATCH,
                f'destination filename must be "{expected_name}".',
                "destination",
            ),
        )
    try:
        parent = path.parent.lstat()
    except FileNotFoundError:
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_PARENT_NOT_FOUND,
                "destination parent does not exist.",
                "destination",
            ),
        )
    except (OSError, ValueError):
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_PARENT_NOT_DIRECTORY,
                "destination parent could not be inspected.",
                "destination",
            ),
        )
    if _has_symlink_component(path.parent):
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_PARENT_SYMLINK_NOT_ALLOWED,
                "destination parent must not contain symbolic links.",
                "destination",
            ),
        )
    if not stat.S_ISDIR(parent.st_mode):
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_PARENT_NOT_DIRECTORY,
                "destination parent must be a directory.",
                "destination",
            ),
        )
    if path.exists() or path.is_symlink():
        return (
            None,
            None,
            _issue(
                _Code.DESTINATION_EXISTS,
                "destination must not already exist.",
                "destination",
            ),
        )
    return path, parent, None


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
    paths: tuple[str, ...],
    contents: tuple[bytes, ...],
) -> None:
    with zipfile.ZipFile(target, "w", compression=_ZIP_STORED, allowZip64=False) as archive:
        archive.comment = b""
        for path, content in zip(paths, contents, strict=True):
            archive.writestr(_zip_info(path), content)


def export_explorer_package(
    package_root: str | Path,
    destination: str | Path,
) -> ExplorerPackageExportResult:
    """Validate, snapshot, and atomically export one declarative package."""
    root, root_issue = _validated_root(package_root)
    if root_issue is not None:
        return _failure(root_issue)
    assert root is not None
    if (
        os.open not in os.supports_dir_fd
        or os.stat not in os.supports_dir_fd
        or os.unlink not in os.supports_dir_fd
        or os.link not in os.supports_dir_fd
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
    ):
        return _failure(
            _issue(
                _Code.DESCRIPTOR_CONFINEMENT_UNAVAILABLE,
                "Descriptor-confined export is unavailable on this platform.",
                "package_root",
            )
        )

    root_descriptor: int | None = None
    try:
        root_descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        initial_manifest, snapshot_issue = _snapshot(root_descriptor, ("manifest.yaml",))
        if snapshot_issue is not None:
            return _failure(snapshot_issue)
        first_load = load_explorer_package(root)
        if not first_load.validation_report.is_valid:
            return _failure(
                _issue(
                    _Code.PACKAGE_NOT_VALID,
                    "Explorer Package validation failed; run explore-package validate.",
                    "package_root",
                )
            )
        if not first_load.is_loaded or first_load.package is None:
            return _failure(
                _issue(
                    _Code.PACKAGE_NOT_LOADED,
                    "Explorer Package declarative loading failed; run explore-package validate.",
                    "package_root",
                )
            )
        manifest = first_load.validation_report.manifest
        assert manifest is not None
        paths = (
            "manifest.yaml",
            *(item.path for item in manifest.contributions),
            *(item.path for item in manifest.assets),
        )
        first_contents, snapshot_issue = _snapshot(root_descriptor, paths)
        if snapshot_issue is not None:
            return _failure(snapshot_issue)
        assert initial_manifest is not None and first_contents is not None
        if initial_manifest[0] != first_contents[0]:
            return _failure(
                _issue(
                    _Code.PACKAGE_CHANGED,
                    "manifest.yaml changed after validation began.",
                    "members[0]",
                    member_path="manifest.yaml",
                    member_index=0,
                )
            )
        second_load = load_explorer_package(root)
        second_contents, snapshot_issue = _snapshot(root_descriptor, paths)
        if snapshot_issue is not None:
            return _failure(snapshot_issue)
        assert second_contents is not None
        if first_load != second_load or first_contents != second_contents:
            return _failure(
                _issue(
                    _Code.PACKAGE_CHANGED,
                    "Package contents changed during export validation and reread.",
                    "package_root",
                )
            )
        contents = second_contents
    finally:
        if root_descriptor is not None:
            with suppress(OSError):
                os.close(root_descriptor)

    package = first_load.package
    assert package is not None
    expected_name = f"{package.metadata.id}-{package.metadata.version}.explorer-package.zip"
    destination_path, parent_metadata, destination_issue = _validated_destination(
        destination, expected_name
    )
    if destination_issue is not None:
        return _failure(destination_issue)
    assert destination_path is not None and parent_metadata is not None

    entries = tuple(
        ExplorerPackageExportEntry(
            path,
            SUPPORTED_EXPLORER_PACKAGE_EXPORT_DIGEST_ALGORITHM,
            hashlib.sha256(content).hexdigest(),
            len(content),
            EXPLORER_PACKAGE_EXPORT_FILE_MODE,
        )
        for path, content in zip(paths, contents, strict=True)
    )
    artifact = ExplorerPackageExportArtifact(
        SUPPORTED_EXPLORER_PACKAGE_EXPORT_CONTRACT_VERSION,
        package.metadata.id,
        package.metadata.version,
        package.compatibility.student_api,
        entries,
        sum(entry.bytes_written for entry in entries),
    )

    parent_descriptor: int | None = None
    staging_descriptor: int | None = None
    staging_name: str | None = None
    digest: ExplorerPackageExportDigest | None = None
    archive_size = 0
    failure_issue: ExplorerPackageExportIssue | None = None
    try:
        parent_descriptor = os.open(
            destination_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
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
                "destination must not already exist.",
                "destination",
            )
        if failure_issue is None:
            for _ in range(100):
                candidate = f".explorer-package-export-{secrets.token_hex(12)}.tmp"
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
                raise OSError("staging file unavailable")
            with os.fdopen(os.dup(staging_descriptor), "w+b") as stream:
                _write_archive(stream, paths, contents)
                stream.flush()
                os.fsync(stream.fileno())
            archive_size = os.fstat(staging_descriptor).st_size
            if archive_size > MAX_EXPLORER_PACKAGE_EXPORT_ARCHIVE_BYTES:
                raise OSError("archive too large")
            os.fchmod(staging_descriptor, EXPLORER_PACKAGE_EXPORT_FILE_MODE)
            os.fsync(staging_descriptor)
            os.lseek(staging_descriptor, 0, os.SEEK_SET)
            with os.fdopen(os.dup(staging_descriptor), "rb") as stream:
                digest = ExplorerPackageExportDigest(
                    SUPPORTED_EXPLORER_PACKAGE_EXPORT_DIGEST_ALGORITHM,
                    hashlib.file_digest(
                        stream, SUPPORTED_EXPLORER_PACKAGE_EXPORT_DIGEST_ALGORITHM
                    ).hexdigest(),
                )
            os.link(
                staging_name,
                destination_path.name,
                src_dir_fd=parent_descriptor,
                dst_dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            os.unlink(staging_name, dir_fd=parent_descriptor)
            staging_name = None
            os.fsync(parent_descriptor)
    except FileExistsError:
        failure_issue = _issue(
            _Code.DESTINATION_EXISTS, "destination must not already exist.", "destination"
        )
    except (OSError, ValueError, zipfile.LargeZipFile):
        failure_issue = _issue(
            _Code.ARCHIVE_WRITE_FAILED,
            "The deterministic package archive could not be atomically written.",
            "destination",
        )
    finally:
        if staging_descriptor is not None:
            with suppress(OSError):
                os.close(staging_descriptor)
        if staging_name is not None and parent_descriptor is not None:
            try:
                os.unlink(staging_name, dir_fd=parent_descriptor)
            except OSError:
                failure_issue = _issue(
                    _Code.ARCHIVE_CLEANUP_FAILED,
                    "The operation-owned staging file could not be removed.",
                    "destination",
                )
        if parent_descriptor is not None:
            with suppress(OSError):
                os.close(parent_descriptor)
    if failure_issue is not None:
        return _failure(failure_issue)
    assert digest is not None
    return ExplorerPackageExportResult(artifact, digest, archive_size, ())


def serialize_explorer_package_export_result(result: ExplorerPackageExportResult) -> str:
    """Serialize one immutable export result as stable compact JSON."""
    if type(result) is not ExplorerPackageExportResult:
        raise TypeError("result must be an ExplorerPackageExportResult")
    artifact = result.artifact
    document = {
        "exported": result.is_exported,
        "artifact": (
            None
            if artifact is None
            else {
                "contract_version": artifact.contract_version,
                "package_id": artifact.package_id,
                "package_version": artifact.package_version,
                "student_api_version": artifact.student_api_version,
                "entries": [
                    {
                        "relative_path": entry.relative_path,
                        "digest_algorithm": entry.digest_algorithm,
                        "digest_hex": entry.digest_hex,
                        "bytes_written": entry.bytes_written,
                        "mode": entry.mode,
                    }
                    for entry in artifact.entries
                ],
                "total_content_bytes": artifact.total_content_bytes,
            }
        ),
        "digest": (
            None
            if result.digest is None
            else {
                "algorithm": result.digest.algorithm,
                "hex_digest": result.digest.hex_digest,
            }
        ),
        "bytes_written": result.bytes_written,
        "issues": [
            {
                "code": issue.code.value,
                "message": issue.message,
                "location": issue.location,
                "member_path": issue.member_path,
                "member_index": issue.member_index,
            }
            for issue in result.issues
        ],
    }
    return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
