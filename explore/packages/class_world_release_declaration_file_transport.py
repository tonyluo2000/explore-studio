"""Explicit bounded UTF-8 file transport for release declarations."""

from __future__ import annotations

import os
import stat
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import BinaryIO

from explore.packages.class_world_configuration_models import ClassWorldConfiguration
from explore.packages.class_world_release_declaration_file_transport_models import (
    MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES,
    ClassWorldReleaseDeclarationFileIssue,
    ClassWorldReleaseDeclarationFileIssueCode,
    ClassWorldReleaseDeclarationFileReadResult,
    ClassWorldReleaseDeclarationFileWriteResult,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)
from explore.packages.class_world_release_declaration_serialization import (
    parse_class_world_release_declaration,
    serialize_class_world_release_declaration,
)

_UTF8_BOM = b"\xef\xbb\xbf"


def _issue(
    code: ClassWorldReleaseDeclarationFileIssueCode,
    message: str,
    location: str,
) -> ClassWorldReleaseDeclarationFileIssue:
    return ClassWorldReleaseDeclarationFileIssue(code=code, message=message, location=location)


def _validated_path(
    path: object,
) -> tuple[Path | None, ClassWorldReleaseDeclarationFileIssue | None]:
    if path is None or (isinstance(path, str) and not path):
        return None, _issue(
            ClassWorldReleaseDeclarationFileIssueCode.PATH_REQUIRED,
            "path must be a non-empty str or pathlib.Path.",
            "path",
        )
    if not isinstance(path, (str, Path)):
        return None, _issue(
            ClassWorldReleaseDeclarationFileIssueCode.PATH_INVALID_TYPE,
            "path must be a str or pathlib.Path.",
            "path",
        )
    if not str(path).strip():
        return None, _issue(
            ClassWorldReleaseDeclarationFileIssueCode.PATH_REQUIRED,
            "path must contain non-whitespace text.",
            "path",
        )
    return Path(path), None


def _read_failure(
    issue: ClassWorldReleaseDeclarationFileIssue,
) -> ClassWorldReleaseDeclarationFileReadResult:
    return ClassWorldReleaseDeclarationFileReadResult(
        declaration=None,
        issues=(issue,),
        serialization_issues=(),
        declaration_issues=(),
    )


def _inspect_read_path(path: Path) -> ClassWorldReleaseDeclarationFileIssue | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_FOUND,
            "The release-declaration file does not exist.",
            "path",
        )
    except (OSError, ValueError):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.FILE_READ_FAILED,
            "The release-declaration path could not be inspected.",
            "path",
        )
    if stat.S_ISLNK(metadata.st_mode):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.FILE_SYMLINK_NOT_ALLOWED,
            "The final release-declaration path must not be a symbolic link.",
            "path",
        )
    if not stat.S_ISREG(metadata.st_mode):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_REGULAR,
            "The release-declaration path must refer to a regular file.",
            "path",
        )
    return None


def read_class_world_release_declaration_file(
    path: str | Path,
    configuration: ClassWorldConfiguration,
) -> ClassWorldReleaseDeclarationFileReadResult:
    """Read and strictly parse one release declaration from an explicit path.

    Transport failures, serialization issues, and release builder issues remain
    separate. Semantic parsing is delegated unchanged to
    :func:`parse_class_world_release_declaration`.
    """
    declaration_path, path_issue = _validated_path(path)
    if path_issue is not None:
        return _read_failure(path_issue)
    assert declaration_path is not None

    filesystem_issue = _inspect_read_path(declaration_path)
    if filesystem_issue is not None:
        return _read_failure(filesystem_issue)

    try:
        with declaration_path.open("rb") as stream:
            declaration_bytes = stream.read(MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES + 1)
    except (OSError, ValueError):
        return _read_failure(
            _issue(
                ClassWorldReleaseDeclarationFileIssueCode.FILE_READ_FAILED,
                "The release-declaration file could not be read.",
                "path",
            )
        )

    if len(declaration_bytes) > MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES:
        return _read_failure(
            _issue(
                ClassWorldReleaseDeclarationFileIssueCode.FILE_TOO_LARGE,
                (
                    "The release-declaration file exceeds the v0.1 limit of "
                    f"{MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES} UTF-8 bytes."
                ),
                "declaration",
            )
        )
    if declaration_bytes.startswith(_UTF8_BOM):
        return _read_failure(
            _issue(
                ClassWorldReleaseDeclarationFileIssueCode.DECLARATION_BOM_NOT_ALLOWED,
                "Release-declaration files must use UTF-8 without a byte-order mark.",
                "declaration",
            )
        )
    try:
        declaration_text = declaration_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _read_failure(
            _issue(
                ClassWorldReleaseDeclarationFileIssueCode.FILE_INVALID_UTF8,
                "The release-declaration file must contain strictly valid UTF-8 text.",
                "declaration",
            )
        )

    parsed = parse_class_world_release_declaration(declaration_text, configuration)
    return ClassWorldReleaseDeclarationFileReadResult(
        declaration=parsed.declaration,
        issues=(),
        serialization_issues=parsed.issues,
        declaration_issues=parsed.declaration_issues,
    )


def _inspect_write_path(path: Path) -> ClassWorldReleaseDeclarationFileIssue | None:
    parent = path.parent
    try:
        parent_metadata = parent.stat()
    except FileNotFoundError:
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.PARENT_NOT_FOUND,
            "The destination parent directory does not exist.",
            "parent",
        )
    except (OSError, ValueError):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.PARENT_NOT_DIRECTORY,
            "The destination parent could not be accessed as a directory.",
            "parent",
        )
    if not stat.S_ISDIR(parent_metadata.st_mode):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.PARENT_NOT_DIRECTORY,
            "The destination parent must be an existing directory.",
            "parent",
        )

    try:
        destination_metadata = path.lstat()
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_NOT_REGULAR,
            "The destination could not be inspected as a regular file.",
            "destination",
        )
    if stat.S_ISLNK(destination_metadata.st_mode):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.FILE_SYMLINK_NOT_ALLOWED,
            "The final destination path must not be a symbolic link.",
            "destination",
        )
    if stat.S_ISDIR(destination_metadata.st_mode):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_IS_DIRECTORY,
            "The destination path must not be a directory.",
            "destination",
        )
    if not stat.S_ISREG(destination_metadata.st_mode):
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_NOT_REGULAR,
            "An existing destination must be a regular file.",
            "destination",
        )
    return None


def _cleanup_temporary_file(path: Path) -> ClassWorldReleaseDeclarationFileIssue | None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return _issue(
            ClassWorldReleaseDeclarationFileIssueCode.TEMP_FILE_CLEANUP_FAILED,
            "The private temporary release-declaration file could not be removed.",
            "temporary_file",
        )
    return None


def _write_all(stream: BinaryIO, content: bytes) -> None:
    view = memoryview(content)
    offset = 0
    while offset < len(view):
        written = stream.write(view[offset:])
        if written is None or written <= 0:
            raise OSError("temporary release-declaration write made no progress")
        offset += written


def _failed_write(
    original_issue: ClassWorldReleaseDeclarationFileIssue,
    temporary_path: Path,
) -> ClassWorldReleaseDeclarationFileWriteResult:
    cleanup_issue = _cleanup_temporary_file(temporary_path)
    issues = (original_issue,) if cleanup_issue is None else (original_issue, cleanup_issue)
    return ClassWorldReleaseDeclarationFileWriteResult(bytes_written=0, issues=issues)


def write_class_world_release_declaration_file(
    declaration: ClassWorldReleaseDeclaration,
    path: str | Path,
) -> ClassWorldReleaseDeclarationFileWriteResult:
    """Atomically replace an explicit path with one canonical declaration.

    A wrong declaration type retains the serializer's ``TypeError`` contract.
    A manually inconsistent declaration returns ``DECLARATION_INVALID``. No
    directory, backup, readback, hash, inventory, or artifact is created.
    """
    try:
        declaration_text = serialize_class_world_release_declaration(declaration)
    except ValueError:
        return ClassWorldReleaseDeclarationFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.DECLARATION_INVALID,
                    "The declaration could not be serialized as a valid release declaration.",
                    "declaration",
                ),
            ),
        )
    try:
        declaration_bytes = declaration_text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        return ClassWorldReleaseDeclarationFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.FILE_INVALID_UTF8,
                    "The canonical release declaration could not be encoded as strict UTF-8.",
                    "declaration",
                ),
            ),
        )
    if len(declaration_bytes) > MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES:
        return ClassWorldReleaseDeclarationFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.FILE_TOO_LARGE,
                    (
                        "The canonical release declaration exceeds the v0.1 limit of "
                        f"{MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES} UTF-8 bytes."
                    ),
                    "declaration",
                ),
            ),
        )

    destination, path_issue = _validated_path(path)
    if path_issue is not None:
        return ClassWorldReleaseDeclarationFileWriteResult(bytes_written=0, issues=(path_issue,))
    assert destination is not None

    destination_issue = _inspect_write_path(destination)
    if destination_issue is not None:
        return ClassWorldReleaseDeclarationFileWriteResult(
            bytes_written=0,
            issues=(destination_issue,),
        )

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
    except OSError:
        return ClassWorldReleaseDeclarationFileWriteResult(
            bytes_written=0,
            issues=(
                _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.TEMP_FILE_CREATE_FAILED,
                    "A private temporary release-declaration file could not be created.",
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
                ClassWorldReleaseDeclarationFileIssueCode.TEMP_FILE_CREATE_FAILED,
                "The private temporary release-declaration file could not be opened.",
                "temporary_file",
            ),
            temporary_path,
        )

    failure: ClassWorldReleaseDeclarationFileIssue | None = None
    try:
        try:
            _write_all(stream, declaration_bytes)
        except OSError:
            failure = _issue(
                ClassWorldReleaseDeclarationFileIssueCode.FILE_WRITE_FAILED,
                "The canonical release-declaration bytes could not be written completely.",
                "temporary_file",
            )
        if failure is None:
            try:
                stream.flush()
            except OSError:
                failure = _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.FILE_FLUSH_FAILED,
                    "The temporary release-declaration file could not be flushed.",
                    "temporary_file",
                )
        if failure is None:
            try:
                os.fsync(stream.fileno())
            except OSError:
                failure = _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.FILE_SYNC_FAILED,
                    "The temporary release-declaration file could not be synchronized.",
                    "temporary_file",
                )
    finally:
        try:
            stream.close()
        except OSError:
            if failure is None:
                failure = _issue(
                    ClassWorldReleaseDeclarationFileIssueCode.FILE_WRITE_FAILED,
                    "The temporary release-declaration file could not be closed.",
                    "temporary_file",
                )

    if failure is not None:
        return _failed_write(failure, temporary_path)

    try:
        os.replace(temporary_path, destination)
    except OSError:
        return _failed_write(
            _issue(
                ClassWorldReleaseDeclarationFileIssueCode.ATOMIC_REPLACE_FAILED,
                "The destination could not be atomically replaced.",
                "destination",
            ),
            temporary_path,
        )

    return ClassWorldReleaseDeclarationFileWriteResult(
        bytes_written=len(declaration_bytes),
        issues=(),
    )
