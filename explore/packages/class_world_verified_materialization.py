"""Atomic materialization of the exact package bytes verified during the operation."""

from __future__ import annotations

import os
import secrets
import stat
import unicodedata
from contextlib import suppress
from pathlib import Path, PurePosixPath

from explore.packages.class_world_artifact_file_verification import (
    _verify_class_world_artifact_files_with_contents,
)
from explore.packages.class_world_artifact_file_verification_models import (
    ClassWorldArtifactFileVerificationResult,
)
from explore.packages.class_world_assembly_plan_models import ClassWorldAssemblyPlanResult
from explore.packages.class_world_materialization_plan import (
    build_class_world_materialization_plan,
)
from explore.packages.class_world_materialization_plan_models import (
    SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION,
    ClassWorldMaterializationPlan,
    ClassWorldMaterializationPlanResult,
    ClassWorldPackageMaterialization,
)
from explore.packages.class_world_verified_materialization_models import (
    SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION,
    ClassWorldMaterializedPackage,
    ClassWorldVerifiedMaterialization,
    ClassWorldVerifiedMaterializationIssue,
    ClassWorldVerifiedMaterializationIssueCode,
    ClassWorldVerifiedMaterializationResult,
)

_WRITE_CHUNK_BYTES = 1024 * 1024


def _issue(
    code: ClassWorldVerifiedMaterializationIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    package_index: int | None = None,
) -> ClassWorldVerifiedMaterializationIssue:
    return ClassWorldVerifiedMaterializationIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id,
        package_index=package_index,
    )


def _result(
    *,
    materialization: ClassWorldVerifiedMaterialization | None = None,
    source_verification: ClassWorldArtifactFileVerificationResult | None = None,
    issues: tuple[ClassWorldVerifiedMaterializationIssue, ...] = (),
) -> ClassWorldVerifiedMaterializationResult:
    return ClassWorldVerifiedMaterializationResult(
        materialization=materialization,
        source_verification=source_verification,
        issues=issues,
    )


def _plan_issue(candidate: object) -> ClassWorldVerifiedMaterializationIssue | None:
    if candidate is None:
        return _issue(
            ClassWorldVerifiedMaterializationIssueCode.PLAN_RESULT_REQUIRED,
            "A class-world materialization plan result is required.",
            "plan_result",
        )
    if type(candidate) is not ClassWorldMaterializationPlanResult:
        return _issue(
            ClassWorldVerifiedMaterializationIssueCode.PLAN_RESULT_INVALID,
            "plan_result must be a class-world materialization plan result.",
            "plan_result",
        )
    if type(candidate.issues) is not tuple or candidate.issues or candidate.plan is None:
        return _issue(
            ClassWorldVerifiedMaterializationIssueCode.PLAN_NOT_BUILT,
            "plan_result must contain one successfully built materialization plan.",
            "plan_result",
        )
    if type(candidate.plan) is not ClassWorldMaterializationPlan:
        return _issue(
            ClassWorldVerifiedMaterializationIssueCode.PLAN_INCONSISTENT,
            "plan_result.plan must be a materialization plan.",
            "plan_result.plan",
        )
    rebuilt = build_class_world_materialization_plan(candidate.plan.file_verification)
    if (
        not rebuilt.is_planned
        or rebuilt.plan != candidate.plan
        or candidate.plan.contract_version
        != SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION
    ):
        return _issue(
            ClassWorldVerifiedMaterializationIssueCode.PLAN_INCONSISTENT,
            "plan_result.plan must retain coherent canonical layout-plan output.",
            "plan_result.plan",
        )
    collision_keys = [
        unicodedata.normalize("NFC", package.relative_path).casefold()
        for package in candidate.plan.packages
    ]
    if len(collision_keys) != len(set(collision_keys)):
        return _issue(
            ClassWorldVerifiedMaterializationIssueCode.PLAN_INCONSISTENT,
            "plan_result.plan contains colliding destination paths.",
            "plan_result.plan.packages",
        )
    return None


def _output_root(
    candidate: object,
) -> tuple[
    Path | None, Path | None, os.stat_result | None, ClassWorldVerifiedMaterializationIssue | None
]:
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_REQUIRED,
                "output_root must be a non-empty absolute str or pathlib.Path.",
                "output_root",
            ),
        )
    if not isinstance(candidate, (str, Path)):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_INVALID_TYPE,
                "output_root must be a str or pathlib.Path.",
                "output_root",
            ),
        )
    output = Path(candidate)
    if not output.is_absolute():
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_NOT_ABSOLUTE,
                "output_root must be an absolute path.",
                "output_root",
            ),
        )
    if output.name in ("", ".", "..") or ".." in output.parts:
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_INVALID,
                "output_root must identify one canonical new directory.",
                "output_root",
            ),
        )

    parent = output.parent
    try:
        parent_metadata = parent.lstat()
    except FileNotFoundError:
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_NOT_FOUND,
                "The output_root parent directory does not exist.",
                "output_root",
            ),
        )
    except (OSError, ValueError):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
                "The output_root parent directory could not be inspected safely.",
                "output_root",
            ),
        )
    if stat.S_ISLNK(parent_metadata.st_mode):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_SYMLINK_NOT_ALLOWED,
                "The output_root parent directory must not be a symbolic link.",
                "output_root",
            ),
        )
    if not stat.S_ISDIR(parent_metadata.st_mode):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_NOT_DIRECTORY,
                "The output_root parent must be a directory.",
                "output_root",
            ),
        )
    try:
        resolved_parent = parent.resolve(strict=True)
    except (OSError, ValueError):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
                "The output_root parent directory could not be resolved safely.",
                "output_root",
            ),
        )
    if resolved_parent != parent:
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_SYMLINK_NOT_ALLOWED,
                "The output_root parent path must not pass through symbolic links.",
                "output_root",
            ),
        )
    output = resolved_parent / output.name
    try:
        output.lstat()
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
                "The output destination could not be inspected safely.",
                "output_root",
            ),
        )
    else:
        return (
            None,
            None,
            None,
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.OUTPUT_DESTINATION_EXISTS,
                "output_root must not already exist.",
                "output_root",
            ),
        )
    return output, resolved_parent, parent_metadata, None


def _source_snapshot(
    plan: ClassWorldMaterializationPlan,
    artifact_root: object,
) -> tuple[ClassWorldArtifactFileVerificationResult, tuple[bytes, ...]]:
    prior_content_result = plan.file_verification.content_verification
    assert prior_content_result is not None
    prior_verification = prior_content_result.verification
    assert prior_verification is not None
    assembly_plan_result = ClassWorldAssemblyPlanResult(plan=prior_verification.plan, issues=())
    bindings = tuple(package.source.binding for package in plan.packages)
    return _verify_class_world_artifact_files_with_contents(
        assembly_plan_result,
        artifact_root,  # type: ignore[arg-type]
        bindings,
        require_descriptor_confinement=True,
    )


def _open_output_parent(
    parent: Path,
    expected: os.stat_result,
) -> tuple[int | None, ClassWorldVerifiedMaterializationIssue | None]:
    if (
        os.open not in os.supports_dir_fd
        or os.mkdir not in os.supports_dir_fd
        or os.stat not in os.supports_dir_fd
        or os.unlink not in os.supports_dir_fd
        or os.rmdir not in os.supports_dir_fd
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
    ):
        return None, _issue(
            ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
            "Descriptor-confined output operations are unavailable on this platform.",
            "output_root",
        )
    descriptor: int | None = None
    try:
        descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        actual = os.fstat(descriptor)
    except (OSError, ValueError):
        if descriptor is not None:
            with suppress(OSError):
                os.close(descriptor)
        return None, _issue(
            ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
            "The output_root parent could not be opened safely.",
            "output_root",
        )
    if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
        with suppress(OSError):
            os.close(descriptor)
        return None, _issue(
            ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
            "The output_root parent changed before materialization.",
            "output_root",
        )
    return descriptor, None


def _create_staging_directory(
    parent_descriptor: int,
) -> tuple[str | None, int | None, os.stat_result | None]:
    for _ in range(100):
        name = f".class-world-stage-{secrets.token_hex(12)}"
        try:
            os.mkdir(name, 0o700, dir_fd=parent_descriptor)
        except FileExistsError:
            continue
        except (OSError, ValueError):
            return None, None, None
        descriptor: int | None = None
        try:
            descriptor = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent_descriptor,
            )
            return name, descriptor, os.fstat(descriptor)
        except (OSError, ValueError):
            if descriptor is not None:
                with suppress(OSError):
                    os.close(descriptor)
            with suppress(OSError):
                os.rmdir(name, dir_fd=parent_descriptor)
            return None, None, None
    return None, None, None


def _write_all(descriptor: int, content: bytes) -> None:
    view = memoryview(content)
    offset = 0
    while offset < len(view):
        written = os.write(descriptor, view[offset : offset + _WRITE_CHUNK_BYTES])
        if written <= 0:
            raise OSError("bounded write made no progress")
        offset += written


def _write_package(
    staging_descriptor: int,
    package: ClassWorldPackageMaterialization,
    content: bytes,
) -> None:
    parts = PurePosixPath(package.relative_path).parts
    directory_descriptor = os.dup(staging_descriptor)
    file_descriptor: int | None = None
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, 0o755, dir_fd=directory_descriptor)
                os.fsync(directory_descriptor)
            except FileExistsError:
                pass
            next_descriptor = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory_descriptor,
            )
            os.fchmod(next_descriptor, 0o755)
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        file_descriptor = os.open(
            parts[-1],
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_descriptor,
        )
        os.fchmod(file_descriptor, 0o644)
        _write_all(file_descriptor, content)
        os.fsync(file_descriptor)
        os.close(file_descriptor)
        file_descriptor = None
        os.fsync(directory_descriptor)
    finally:
        if file_descriptor is not None:
            with suppress(OSError):
                os.close(file_descriptor)
        with suppress(OSError):
            os.close(directory_descriptor)


def _clean_directory(descriptor: int) -> None:
    for name in os.listdir(descriptor):
        metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        if stat.S_ISDIR(metadata.st_mode):
            child = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            try:
                _clean_directory(child)
            finally:
                os.close(child)
            os.rmdir(name, dir_fd=descriptor)
        else:
            os.unlink(name, dir_fd=descriptor)


def _cleanup_staging(
    parent_descriptor: int,
    staging_name: str,
    staging_descriptor: int,
    expected: os.stat_result,
) -> bool:
    try:
        _clean_directory(staging_descriptor)
        os.close(staging_descriptor)
        actual = os.stat(staging_name, dir_fd=parent_descriptor, follow_symlinks=False)
        if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
            return False
        os.rmdir(staging_name, dir_fd=parent_descriptor)
        return True
    except (OSError, ValueError):
        with suppress(OSError):
            os.close(staging_descriptor)
        return False


def _with_cleanup_issue(
    issue: ClassWorldVerifiedMaterializationIssue,
    parent_descriptor: int,
    staging_name: str,
    staging_descriptor: int,
    staging_metadata: os.stat_result,
) -> tuple[ClassWorldVerifiedMaterializationIssue, ...]:
    if _cleanup_staging(
        parent_descriptor,
        staging_name,
        staging_descriptor,
        staging_metadata,
    ):
        return (issue,)
    return (
        issue,
        _issue(
            ClassWorldVerifiedMaterializationIssueCode.STAGING_CLEANUP_FAILED,
            "Private staging content could not be cleaned completely.",
            "output_root",
        ),
    )


def materialize_verified_class_world_artifacts(
    plan_result: ClassWorldMaterializationPlanResult,
    artifact_root: str | Path,
    output_root: str | Path,
) -> ClassWorldVerifiedMaterializationResult:
    """Reverify, stage, and atomically publish exactly the planned package bytes."""
    plan_failure = _plan_issue(plan_result)
    if plan_failure is not None:
        return _result(issues=(plan_failure,))

    output, output_parent, parent_metadata, output_issue = _output_root(output_root)
    if output_issue is not None:
        return _result(issues=(output_issue,))
    assert output is not None and output_parent is not None and parent_metadata is not None
    assert type(plan_result) is ClassWorldMaterializationPlanResult
    assert plan_result.plan is not None
    plan = plan_result.plan

    source_verification, contents = _source_snapshot(plan, artifact_root)
    if not source_verification.is_complete:
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.SOURCE_VERIFICATION_FAILED,
                    "Source artifact files could not be reverified for materialization.",
                    "artifact_root",
                ),
            ),
        )
    assert source_verification.content_verification is not None
    current_verification = source_verification.content_verification.verification
    assert current_verification is not None
    if not current_verification.all_match:
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.SOURCE_CONTENT_MISMATCH,
                    "Source artifact bytes no longer match every planned digest.",
                    "artifact_root",
                ),
            ),
        )
    if (
        source_verification != plan.file_verification
        or len(contents) != len(plan.packages)
        or sum(len(content) for content in contents) != plan.total_bytes
    ):
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.SOURCE_SNAPSHOT_INCONSISTENT,
                    "The freshly verified source snapshot is inconsistent with the plan.",
                    "artifact_root",
                ),
            ),
        )

    try:
        resolved_source_root = Path(artifact_root).resolve(strict=True)
    except (OSError, TypeError, ValueError):
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.SOURCE_VERIFICATION_FAILED,
                    "artifact_root could not be retained after source verification.",
                    "artifact_root",
                ),
            ),
        )
    if output.is_relative_to(resolved_source_root):
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.OUTPUT_OVERLAPS_SOURCE,
                    "output_root must be outside artifact_root.",
                    "output_root",
                ),
            ),
        )

    parent_descriptor, parent_issue = _open_output_parent(output_parent, parent_metadata)
    if parent_issue is not None:
        return _result(source_verification=source_verification, issues=(parent_issue,))
    assert parent_descriptor is not None

    try:
        os.stat(output.name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        with suppress(OSError):
            os.close(parent_descriptor)
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_UNSAFE,
                    "The output destination could not be rechecked safely.",
                    "output_root",
                ),
            ),
        )
    else:
        with suppress(OSError):
            os.close(parent_descriptor)
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.OUTPUT_DESTINATION_EXISTS,
                    "output_root appeared before materialization could begin.",
                    "output_root",
                ),
            ),
        )

    staging_name, staging_descriptor, staging_metadata = _create_staging_directory(
        parent_descriptor
    )
    if staging_name is None or staging_descriptor is None or staging_metadata is None:
        with suppress(OSError):
            os.close(parent_descriptor)
        return _result(
            source_verification=source_verification,
            issues=(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.STAGING_CREATE_FAILED,
                    "Private sibling staging could not be created.",
                    "output_root",
                ),
            ),
        )

    materialized_packages: list[ClassWorldMaterializedPackage] = []
    for index, (package, content) in enumerate(zip(plan.packages, contents, strict=True)):
        try:
            _write_package(staging_descriptor, package, content)
        except (OSError, ValueError):
            issues = _with_cleanup_issue(
                _issue(
                    ClassWorldVerifiedMaterializationIssueCode.DESTINATION_WRITE_FAILED,
                    f'Package "{package.artifact.package_id}" could not be staged safely.',
                    f"plan_result.plan.packages[{index}]",
                    package_id=package.artifact.package_id,
                    package_index=index,
                ),
                parent_descriptor,
                staging_name,
                staging_descriptor,
                staging_metadata,
            )
            with suppress(OSError):
                os.close(parent_descriptor)
            return _result(source_verification=source_verification, issues=issues)
        materialized_packages.append(
            ClassWorldMaterializedPackage(package=package, bytes_written=len(content))
        )

    try:
        os.fchmod(staging_descriptor, 0o755)
        os.fsync(staging_descriptor)
        current_parent = os.fstat(parent_descriptor)
        current_staging = os.stat(
            staging_name,
            dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        if (current_parent.st_dev, current_parent.st_ino) != (
            parent_metadata.st_dev,
            parent_metadata.st_ino,
        ) or (current_staging.st_dev, current_staging.st_ino) != (
            staging_metadata.st_dev,
            staging_metadata.st_ino,
        ):
            raise OSError("output staging identity changed")
        try:
            os.stat(output.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError("output destination appeared before atomic publish")

        materialization = ClassWorldVerifiedMaterialization(
            contract_version=SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION,
            plan=plan,
            source_verification=source_verification,
            packages=tuple(materialized_packages),
            total_bytes=sum(package.bytes_written for package in materialized_packages),
        )
        os.replace(
            staging_name,
            output.name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
    except (OSError, ValueError):
        issues = _with_cleanup_issue(
            _issue(
                ClassWorldVerifiedMaterializationIssueCode.ATOMIC_PUBLISH_FAILED,
                "The staged output tree could not be atomically published.",
                "output_root",
            ),
            parent_descriptor,
            staging_name,
            staging_descriptor,
            staging_metadata,
        )
        with suppress(OSError):
            os.close(parent_descriptor)
        return _result(source_verification=source_verification, issues=issues)

    with suppress(OSError):
        os.close(staging_descriptor)
    with suppress(OSError):
        os.close(parent_descriptor)
    return _result(
        materialization=materialization,
        source_verification=source_verification,
    )
