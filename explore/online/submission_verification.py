"""Bounded, deterministic verification of submitted Explorer Package ZIP bytes."""

from __future__ import annotations

import hashlib
import io
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

import yaml

from explore.online.submission_models import (
    SubmissionVerificationIssue,
    SubmissionVerificationIssueCode,
    SubmittedArchiveMember,
    SubmittedArchiveVerification,
    VerifiedSubmittedArchive,
)
from explore.packages.explorer_package_export_models import (
    EXPLORER_PACKAGE_EXPORT_FILE_MODE,
    MAX_EXPLORER_PACKAGE_EXPORT_ARCHIVE_BYTES,
    MAX_EXPLORER_PACKAGE_EXPORT_CONTENT_BYTES,
    MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES,
)
from explore.packages.loader import load_explorer_package
from explore.packages.manifest import parse_manifest_document

MAX_SUBMISSION_ARCHIVE_MEMBERS = 1024
MAX_SUBMISSION_MANIFEST_BYTES = 1024 * 1024
MAX_SUBMISSION_YAML_BYTES = 1024 * 1024
MAX_SUBMISSION_YAML_TOKENS = 50_000
MAX_SUBMISSION_YAML_DEPTH = 64

_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ZIP_SYSTEM_UNIX = 3
_ZIP_FILE_EXTERNAL_ATTRIBUTES = (stat.S_IFREG | EXPLORER_PACKAGE_EXPORT_FILE_MODE) << 16
_Code = SubmissionVerificationIssueCode


def _issue(
    code: SubmissionVerificationIssueCode,
    message: str,
    location: str,
) -> SubmissionVerificationIssue:
    return SubmissionVerificationIssue(code, message, location)


def _failure(*issues: SubmissionVerificationIssue) -> SubmittedArchiveVerification:
    return SubmittedArchiveVerification(None, tuple(issues))


def _safe_member_path(value: str) -> PurePosixPath | None:
    if not value or value == "." or "\x00" in value or "\\" in value:
        return None
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        return None
    if ".." in posix_path.parts or not posix_path.parts:
        return None
    return PurePosixPath(*posix_path.parts)


def _canonical_archive(paths: tuple[str, ...], contents: tuple[bytes, ...]) -> bytes:
    target = io.BytesIO()
    with zipfile.ZipFile(
        target,
        "w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
    ) as archive:
        archive.comment = b""
        for path, content in zip(paths, contents, strict=True):
            info = zipfile.ZipInfo(path, _ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = _ZIP_SYSTEM_UNIX
            info.external_attr = _ZIP_FILE_EXTERNAL_ATTRIBUTES
            info.internal_attr = 0
            info.extra = b""
            info.comment = b""
            archive.writestr(info, content)
    return target.getvalue()


def _read_member(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
) -> bytes | None:
    if info.file_size > MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES:
        return None
    with archive.open(info, "r") as stream:
        content = stream.read(MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES + 1)
    if len(content) > MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES:
        return None
    return content


def _yaml_is_bounded_safe(text: str) -> bool:
    depth = 0
    starts = (
        yaml.tokens.BlockMappingStartToken,
        yaml.tokens.BlockSequenceStartToken,
        yaml.tokens.FlowMappingStartToken,
        yaml.tokens.FlowSequenceStartToken,
    )
    ends = (
        yaml.tokens.BlockEndToken,
        yaml.tokens.FlowMappingEndToken,
        yaml.tokens.FlowSequenceEndToken,
    )
    forbidden = (
        yaml.tokens.AliasToken,
        yaml.tokens.AnchorToken,
        yaml.tokens.TagToken,
    )
    try:
        for count, token in enumerate(yaml.scan(text), start=1):
            if count > MAX_SUBMISSION_YAML_TOKENS or isinstance(token, forbidden):
                return False
            if isinstance(token, starts):
                depth += 1
                if depth > MAX_SUBMISSION_YAML_DEPTH:
                    return False
            elif isinstance(token, ends):
                depth = max(0, depth - 1)
    except yaml.YAMLError:
        return False
    return True


def _verify_loaded_contents(
    paths: tuple[str, ...],
    contents: tuple[bytes, ...],
) -> tuple[SubmissionVerificationIssue, ...]:
    normalized: set[str] = set()
    safe_paths: list[PurePosixPath] = []
    for index, path in enumerate(paths):
        safe_path = _safe_member_path(path)
        if safe_path is None or safe_path.as_posix() in normalized:
            return (
                _issue(
                    _Code.PACKAGE_CONTENT_INVALID,
                    "A package member path is unsafe or aliases another member.",
                    f"members[{index}]",
                ),
            )
        normalized.add(safe_path.as_posix())
        safe_paths.append(safe_path)

    try:
        with tempfile.TemporaryDirectory(prefix="explore-submission-") as directory:
            root = Path(directory)
            for safe_path, content in zip(safe_paths, contents, strict=True):
                target = root.joinpath(*safe_path.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            loaded = load_explorer_package(root)
    except OSError:
        return (
            _issue(
                _Code.PACKAGE_CONTENT_INVALID,
                "Package contents could not be safely staged for declarative validation.",
                "archive",
            ),
        )

    issues = [
        _issue(_Code.PACKAGE_CONTENT_INVALID, issue.message, issue.location)
        for issue in loaded.validation_report.issues
    ]
    issues.extend(
        _issue(_Code.PACKAGE_CONTENT_INVALID, issue.message, issue.location)
        for issue in loaded.issues
    )
    if not loaded.is_loaded or loaded.package is None:
        if not issues:
            issues.append(
                _issue(
                    _Code.PACKAGE_CONTENT_INVALID,
                    "Explorer Package v0.1 declarative loading did not complete.",
                    "archive",
                )
            )
        return tuple(issues)
    return ()


def verify_submitted_archive(
    filename: str,
    archive_bytes: bytes,
) -> SubmittedArchiveVerification:
    """Verify exactly one bounded deterministic Explorer Package archive.

    Package identity, semantic version, and digest are derived exclusively from
    the supplied bytes. Validation safely parses declarative YAML and never
    imports or executes package content.
    """
    if (
        not isinstance(filename, str)
        or not filename
        or "/" in filename
        or "\\" in filename
        or not filename.endswith(".explorer-package.zip")
    ):
        return _failure(
            _issue(
                _Code.FILENAME_INVALID,
                "filename must identify one .explorer-package.zip file.",
                "filename",
            )
        )
    if type(archive_bytes) is not bytes or not archive_bytes:
        return _failure(
            _issue(_Code.ARCHIVE_REQUIRED, "archive_bytes must be non-empty bytes.", "archive")
        )
    if len(archive_bytes) > MAX_EXPLORER_PACKAGE_EXPORT_ARCHIVE_BYTES:
        return _failure(
            _issue(
                _Code.ARCHIVE_TOO_LARGE,
                "The submitted archive exceeds the bounded v0.1 archive limit.",
                "archive",
            )
        )

    raw_digest = hashlib.sha256(archive_bytes).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r", allowZip64=False) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_SUBMISSION_ARCHIVE_MEMBERS:
                return _failure(
                    _issue(
                        _Code.MEMBER_COUNT_EXCEEDED,
                        "Archive member count is empty or exceeds the submission limit.",
                        "archive",
                    )
                )
            if infos[0].filename != "manifest.yaml":
                return _failure(
                    _issue(
                        _Code.ARCHIVE_STRUCTURE_INVALID,
                        "manifest.yaml must be the first archive member.",
                        "members[0]",
                    )
                )
            if infos[0].file_size > MAX_SUBMISSION_MANIFEST_BYTES:
                return _failure(
                    _issue(
                        _Code.MEMBER_TOO_LARGE,
                        "manifest.yaml exceeds the submission manifest limit.",
                        "members[0]",
                    )
                )
            manifest_bytes = _read_member(archive, infos[0])
            if manifest_bytes is None:
                return _failure(
                    _issue(
                        _Code.MEMBER_TOO_LARGE,
                        "An archive member exceeds the v0.1 per-member limit.",
                        "members[0]",
                    )
                )
            try:
                manifest_text = manifest_bytes.decode("utf-8")
                if not _yaml_is_bounded_safe(manifest_text):
                    raise yaml.YAMLError
                document = yaml.safe_load(manifest_text)
            except (UnicodeDecodeError, yaml.YAMLError):
                return _failure(
                    _issue(
                        _Code.MANIFEST_INVALID,
                        "manifest.yaml must be valid UTF-8 safe YAML.",
                        "manifest.yaml",
                    )
                )
            manifest, manifest_issues = parse_manifest_document(document)
            if manifest is None or manifest_issues:
                return _failure(
                    *(
                        _issue(_Code.MANIFEST_INVALID, item.message, item.location)
                        for item in manifest_issues
                    )
                )

            expected_paths = (
                "manifest.yaml",
                *(item.path for item in manifest.contributions),
                *(item.path for item in manifest.assets),
            )
            actual_paths = tuple(info.filename for info in infos)
            if actual_paths != expected_paths:
                return _failure(
                    _issue(
                        _Code.ARCHIVE_STRUCTURE_INVALID,
                        "Archive members must exactly match manifest order and declarations.",
                        "archive",
                    )
                )
            expected_filename = (
                f"{manifest.package.id}-{manifest.package.version}.explorer-package.zip"
            )
            if filename != expected_filename:
                return _failure(
                    _issue(
                        _Code.FILENAME_INVALID,
                        f'filename must be "{expected_filename}".',
                        "filename",
                    )
                )

            contents: list[bytes] = []
            total = 0
            for index, info in enumerate(infos):
                if info.flag_bits & 0x1:
                    return _failure(
                        _issue(
                            _Code.ARCHIVE_STRUCTURE_INVALID,
                            "Encrypted archive members are not accepted.",
                            f"members[{index}]",
                        )
                    )
                content = manifest_bytes if index == 0 else _read_member(archive, info)
                if content is None:
                    return _failure(
                        _issue(
                            _Code.MEMBER_TOO_LARGE,
                            "An archive member exceeds the v0.1 per-member limit.",
                            f"members[{index}]",
                        )
                    )
                total += len(content)
                if total > MAX_EXPLORER_PACKAGE_EXPORT_CONTENT_BYTES:
                    return _failure(
                        _issue(
                            _Code.CONTENT_TOO_LARGE,
                            "Archive content exceeds the aggregate v0.1 content limit.",
                            "archive",
                        )
                    )
                contents.append(content)
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return _failure(
            _issue(_Code.ARCHIVE_INVALID, "archive_bytes is not a readable ZIP archive.", "archive")
        )

    immutable_contents = tuple(contents)
    if _canonical_archive(expected_paths, immutable_contents) != archive_bytes:
        return _failure(
            _issue(
                _Code.ARCHIVE_NOT_DETERMINISTIC,
                "Archive bytes do not match the deterministic export v0.1 contract.",
                "archive",
            )
        )

    for index, content in enumerate(
        immutable_contents[1 : len(manifest.contributions) + 1],
        start=1,
    ):
        if len(content) > MAX_SUBMISSION_YAML_BYTES:
            return _failure(
                _issue(
                    _Code.MEMBER_TOO_LARGE,
                    "A declarative YAML member exceeds the submission YAML limit.",
                    f"members[{index}]",
                )
            )
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = ""
        if not text or not _yaml_is_bounded_safe(text):
            return _failure(
                _issue(
                    _Code.PACKAGE_CONTENT_INVALID,
                    "Declarative YAML must be bounded safe YAML without aliases or tags.",
                    f"members[{index}]",
                )
            )

    content_issues = _verify_loaded_contents(expected_paths, immutable_contents)
    if content_issues:
        return _failure(*content_issues)

    members = tuple(
        SubmittedArchiveMember(path, len(content), hashlib.sha256(content).hexdigest())
        for path, content in zip(expected_paths, immutable_contents, strict=True)
    )
    return SubmittedArchiveVerification(
        VerifiedSubmittedArchive(
            package_id=manifest.package.id,
            semantic_version=manifest.package.version,
            student_api_version=manifest.compatibility.student_api,
            raw_archive_sha256=raw_digest,
            archive_bytes=len(archive_bytes),
            members=members,
        ),
        (),
    )


__all__ = [
    "MAX_SUBMISSION_ARCHIVE_MEMBERS",
    "MAX_SUBMISSION_MANIFEST_BYTES",
    "MAX_SUBMISSION_YAML_BYTES",
    "MAX_SUBMISSION_YAML_DEPTH",
    "MAX_SUBMISSION_YAML_TOKENS",
    "verify_submitted_archive",
]
