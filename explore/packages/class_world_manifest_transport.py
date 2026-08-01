"""Explicit local UTF-8 file transport for class-world manifests."""

from __future__ import annotations

import os
import stat
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import BinaryIO

from explore.packages.class_world_configuration_models import ClassWorldConfiguration
from explore.packages.class_world_manifest import (
    parse_class_world_manifest,
    serialize_class_world_manifest,
)
from explore.packages.class_world_manifest_models import (
    ClassWorldManifestIssue,
    ClassWorldManifestIssueCode,
)
from explore.packages.class_world_manifest_transport_models import (
    MAX_CLASS_WORLD_MANIFEST_BYTES,
    ClassWorldManifestFileIssue,
    ClassWorldManifestFileIssueCode,
    ClassWorldManifestFileReadResult,
    ClassWorldManifestFileWriteResult,
)
from explore.packages.package_set_models import PackageSetPlan

_UTF8_BOM = b"\xef\xbb\xbf"


def _issue(
    code: ClassWorldManifestFileIssueCode,
    message: str,
    location: str,
) -> ClassWorldManifestFileIssue:
    return ClassWorldManifestFileIssue(code=code, message=message, location=location)


def _validated_path(
    path: object,
) -> tuple[Path | None, ClassWorldManifestFileIssue | None]:
    if path is None or (isinstance(path, str) and not path):
        return None, _issue(
            ClassWorldManifestFileIssueCode.PATH_REQUIRED,
            "path must be a non-empty str or pathlib.Path.",
            "path",
        )
    if not isinstance(path, (str, Path)):
        return None, _issue(
            ClassWorldManifestFileIssueCode.PATH_INVALID_TYPE,
            "path must be a str or pathlib.Path.",
            "path",
        )
    if not str(path).strip():
        return None, _issue(
            ClassWorldManifestFileIssueCode.PATH_REQUIRED,
            "path must contain non-whitespace text.",
            "path",
        )
    return Path(path), None


def _required_plan_issue() -> ClassWorldManifestIssue:
    return ClassWorldManifestIssue(
        code=ClassWorldManifestIssueCode.PACKAGE_SET_PLAN_REQUIRED,
        message="package_set_plan must be a PackageSetPlan.",
        location="package_set_plan",
    )


def _read_failure(
    issue: ClassWorldManifestFileIssue,
    *,
    manifest_issues: tuple[ClassWorldManifestIssue, ...] = (),
) -> ClassWorldManifestFileReadResult:
    return ClassWorldManifestFileReadResult(
        configuration=None,
        issues=(issue,),
        manifest_issues=manifest_issues,
    )


def _inspect_read_path(path: Path) -> ClassWorldManifestFileIssue | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return _issue(
            ClassWorldManifestFileIssueCode.FILE_NOT_FOUND,
            "The manifest file does not exist.",
            "path",
        )
    except (OSError, ValueError):
        return _issue(
            ClassWorldManifestFileIssueCode.FILE_READ_FAILED,
            "The manifest path could not be inspected.",
            "path",
        )
    if stat.S_ISLNK(metadata.st_mode):
        return _issue(
            ClassWorldManifestFileIssueCode.FILE_SYMLINK_NOT_ALLOWED,
            "The final manifest path must not be a symbolic link.",
            "path",
        )
    if not stat.S_ISREG(metadata.st_mode):
        return _issue(
            ClassWorldManifestFileIssueCode.FILE_NOT_REGULAR,
            "The manifest path must refer to a regular file.",
            "path",
        )
    return None


def read_class_world_manifest_file(
    path: str | Path,
    package_set_plan: PackageSetPlan,
) -> ClassWorldManifestFileReadResult:
    """Read and strictly parse one manifest from an explicit local path.

    Invalid path values and transport failures are returned in ``issues``.
    An invalid package-set plan and manifest-semantic failures are returned in
    ``manifest_issues`` so parser diagnostics are not hidden or translated.
    """
    manifest_path, path_issue = _validated_path(path)
    manifest_issues = (
        () if isinstance(package_set_plan, PackageSetPlan) else (_required_plan_issue(),)
    )
    if path_issue is not None or manifest_issues:
        return ClassWorldManifestFileReadResult(
            configuration=None,
            issues=() if path_issue is None else (path_issue,),
            manifest_issues=manifest_issues,
        )
    assert manifest_path is not None

    filesystem_issue = _inspect_read_path(manifest_path)
    if filesystem_issue is not None:
        return _read_failure(filesystem_issue)

    try:
        with manifest_path.open("rb") as stream:
            manifest_bytes = stream.read(MAX_CLASS_WORLD_MANIFEST_BYTES + 1)
    except (OSError, ValueError):
        return _read_failure(
            _issue(
                ClassWorldManifestFileIssueCode.FILE_READ_FAILED,
                "The manifest file could not be read.",
                "path",
            )
        )

    if len(manifest_bytes) > MAX_CLASS_WORLD_MANIFEST_BYTES:
        return _read_failure(
            _issue(
                ClassWorldManifestFileIssueCode.FILE_TOO_LARGE,
                (
                    "The manifest file exceeds the v0.1 limit of "
                    f"{MAX_CLASS_WORLD_MANIFEST_BYTES} UTF-8 bytes."
                ),
                "manifest",
            )
        )
    if manifest_bytes.startswith(_UTF8_BOM):
        return _read_failure(
            _issue(
                ClassWorldManifestFileIssueCode.MANIFEST_BOM_NOT_ALLOWED,
                "Class-world manifest files must use UTF-8 without a byte-order mark.",
                "manifest",
            )
        )
    try:
        manifest_text = manifest_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _read_failure(
            _issue(
                ClassWorldManifestFileIssueCode.FILE_INVALID_UTF8,
                "The manifest file must contain strictly valid UTF-8 text.",
                "manifest",
            )
        )

    parsed = parse_class_world_manifest(manifest_text, package_set_plan)
    return ClassWorldManifestFileReadResult(
        configuration=parsed.configuration,
        issues=(),
        manifest_issues=parsed.issues,
    )


def _inspect_write_path(path: Path) -> ClassWorldManifestFileIssue | None:
    parent = path.parent
    try:
        parent_metadata = parent.stat()
    except FileNotFoundError:
        return _issue(
            ClassWorldManifestFileIssueCode.PARENT_NOT_FOUND,
            "The destination parent directory does not exist.",
            "parent",
        )
    except (OSError, ValueError):
        return _issue(
            ClassWorldManifestFileIssueCode.PARENT_NOT_DIRECTORY,
            "The destination parent could not be accessed as a directory.",
            "parent",
        )
    if not stat.S_ISDIR(parent_metadata.st_mode):
        return _issue(
            ClassWorldManifestFileIssueCode.PARENT_NOT_DIRECTORY,
            "The destination parent must be an existing directory.",
            "parent",
        )

    try:
        destination_metadata = path.lstat()
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return _issue(
            ClassWorldManifestFileIssueCode.DESTINATION_NOT_REGULAR,
            "The destination could not be inspected as a regular file.",
            "destination",
        )
    if stat.S_ISLNK(destination_metadata.st_mode):
        return _issue(
            ClassWorldManifestFileIssueCode.FILE_SYMLINK_NOT_ALLOWED,
            "The final destination path must not be a symbolic link.",
            "destination",
        )
    if stat.S_ISDIR(destination_metadata.st_mode):
        return _issue(
            ClassWorldManifestFileIssueCode.DESTINATION_IS_DIRECTORY,
            "The destination path must not be a directory.",
            "destination",
        )
    if not stat.S_ISREG(destination_metadata.st_mode):
        return _issue(
            ClassWorldManifestFileIssueCode.DESTINATION_NOT_REGULAR,
            "An existing destination must be a regular file.",
            "destination",
        )
    return None


def _cleanup_temporary_file(path: Path) -> ClassWorldManifestFileIssue | None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return _issue(
            ClassWorldManifestFileIssueCode.TEMP_FILE_CLEANUP_FAILED,
            "The private temporary manifest file could not be removed.",
            "temporary_file",
        )
    return None


def _write_all(stream: BinaryIO, content: bytes) -> None:
    view = memoryview(content)
    offset = 0
    while offset < len(view):
        written = stream.write(view[offset:])
        if written is None or written <= 0:
            raise OSError("temporary manifest write made no progress")
        offset += written


def _failed_write(
    original_issue: ClassWorldManifestFileIssue,
    temporary_path: Path,
) -> ClassWorldManifestFileWriteResult:
    cleanup_issue = _cleanup_temporary_file(temporary_path)
    issues = (original_issue,) if cleanup_issue is None else (original_issue, cleanup_issue)
    return ClassWorldManifestFileWriteResult(bytes_written=0, issues=issues)


def write_class_world_manifest_file(
    configuration: ClassWorldConfiguration,
    path: str | Path,
) -> ClassWorldManifestFileWriteResult:
    """Atomically replace an explicit local path with one canonical manifest.

    A wrong configuration type retains the serializer's ``TypeError``
    contract. A manually inconsistent configuration returns ``MANIFEST_INVALID``.
    The destination parent must already exist; this function creates no
    directories, backup, integrity or release output, or verification readback.
    """
    destination, path_issue = _validated_path(path)
    if path_issue is not None:
        return ClassWorldManifestFileWriteResult(bytes_written=0, issues=(path_issue,))
    assert destination is not None

    try:
        manifest_text = serialize_class_world_manifest(configuration)
    except ValueError:
        return ClassWorldManifestFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldManifestFileIssueCode.MANIFEST_INVALID,
                    "The configuration could not be serialized as a valid manifest.",
                    "manifest",
                ),
            ),
        )
    try:
        manifest_bytes = manifest_text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return ClassWorldManifestFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldManifestFileIssueCode.FILE_INVALID_UTF8,
                    "The canonical manifest could not be encoded as strict UTF-8.",
                    "manifest",
                ),
            ),
        )
    if len(manifest_bytes) > MAX_CLASS_WORLD_MANIFEST_BYTES:
        return ClassWorldManifestFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldManifestFileIssueCode.FILE_TOO_LARGE,
                    (
                        "The canonical manifest exceeds the v0.1 limit of "
                        f"{MAX_CLASS_WORLD_MANIFEST_BYTES} UTF-8 bytes."
                    ),
                    "manifest",
                ),
            ),
        )

    destination_issue = _inspect_write_path(destination)
    if destination_issue is not None:
        return ClassWorldManifestFileWriteResult(bytes_written=0, issues=(destination_issue,))

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
    except OSError:
        return ClassWorldManifestFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldManifestFileIssueCode.TEMP_FILE_CREATE_FAILED,
                    "A private temporary manifest file could not be created.",
                    "temporary_file",
                ),
            ),
        )

    temporary_path = Path(temporary_name)
    try:
        stream = os.fdopen(descriptor, "wb", buffering=0)
    except OSError:
        with suppress(OSError):
            os.close(descriptor)
        return _failed_write(
            _issue(
                ClassWorldManifestFileIssueCode.TEMP_FILE_CREATE_FAILED,
                "The private temporary manifest file could not be opened.",
                "temporary_file",
            ),
            temporary_path,
        )

    failure: ClassWorldManifestFileIssue | None = None
    try:
        try:
            _write_all(stream, manifest_bytes)
        except OSError:
            failure = _issue(
                ClassWorldManifestFileIssueCode.FILE_WRITE_FAILED,
                "The canonical manifest bytes could not be written completely.",
                "temporary_file",
            )
        if failure is None:
            try:
                stream.flush()
            except OSError:
                failure = _issue(
                    ClassWorldManifestFileIssueCode.FILE_FLUSH_FAILED,
                    "The temporary manifest file could not be flushed.",
                    "temporary_file",
                )
        if failure is None:
            try:
                os.fsync(stream.fileno())
            except OSError:
                failure = _issue(
                    ClassWorldManifestFileIssueCode.FILE_SYNC_FAILED,
                    "The temporary manifest file could not be synchronized.",
                    "temporary_file",
                )
    finally:
        try:
            stream.close()
        except OSError:
            if failure is None:
                failure = _issue(
                    ClassWorldManifestFileIssueCode.FILE_WRITE_FAILED,
                    "The temporary manifest file could not be closed.",
                    "temporary_file",
                )

    if failure is not None:
        return _failed_write(failure, temporary_path)

    try:
        os.replace(temporary_path, destination)
    except OSError:
        return _failed_write(
            _issue(
                ClassWorldManifestFileIssueCode.ATOMIC_REPLACE_FAILED,
                "The destination could not be atomically replaced.",
                "destination",
            ),
            temporary_path,
        )

    return ClassWorldManifestFileWriteResult(bytes_written=len(manifest_bytes), issues=())
