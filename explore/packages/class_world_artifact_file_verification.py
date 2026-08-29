"""Bounded artifact-file binding and delegated content verification."""

from __future__ import annotations

import os
import stat
from contextlib import suppress
from pathlib import Path, PurePosixPath, PureWindowsPath

from explore.packages.class_world_artifact_content_verification import (
    verify_class_world_artifact_contents,
)
from explore.packages.class_world_artifact_file_verification_models import (
    MAX_CLASS_WORLD_ARTIFACT_SET_BYTES,
    MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES,
    SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION,
    ClassWorldArtifactFileVerificationIssue,
    ClassWorldArtifactFileVerificationIssueCode,
    ClassWorldArtifactFileVerificationResult,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackageArtifactFileRead,
)
from explore.packages.class_world_artifact_inventory_models import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM,
    ClassWorldArtifactInventory,
    ClassWorldPackageArtifactDeclaration,
)
from explore.packages.class_world_assembly_plan_models import (
    SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM,
    SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION,
    ClassWorldAssemblyInputDigest,
    ClassWorldAssemblyPlan,
    ClassWorldAssemblyPlanResult,
)


def _issue(
    code: ClassWorldArtifactFileVerificationIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    binding_index: int | None = None,
) -> ClassWorldArtifactFileVerificationIssue:
    return ClassWorldArtifactFileVerificationIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id,
        binding_index=binding_index,
    )


def _failure(
    *issues: ClassWorldArtifactFileVerificationIssue,
) -> ClassWorldArtifactFileVerificationResult:
    return ClassWorldArtifactFileVerificationResult(
        contract_version=SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION,
        files=(),
        content_verification=None,
        issues=tuple(issues),
    )


def _is_sha256_hex(candidate: object) -> bool:
    return (
        isinstance(candidate, str)
        and len(candidate) == 64
        and all(character in "0123456789abcdef" for character in candidate)
    )


def _plan_issue(plan_result: object) -> ClassWorldArtifactFileVerificationIssue | None:
    if plan_result is None:
        return _issue(
            ClassWorldArtifactFileVerificationIssueCode.PLAN_RESULT_REQUIRED,
            "A class-world assembly plan result is required.",
            "plan_result",
        )
    if type(plan_result) is not ClassWorldAssemblyPlanResult:
        return _issue(
            ClassWorldArtifactFileVerificationIssueCode.PLAN_RESULT_INVALID,
            "plan_result must be a class-world assembly plan result.",
            "plan_result",
        )
    if type(plan_result.issues) is not tuple or plan_result.issues or plan_result.plan is None:
        return _issue(
            ClassWorldArtifactFileVerificationIssueCode.PLAN_NOT_BUILT,
            "plan_result must contain one successfully built assembly plan.",
            "plan_result",
        )

    plan = plan_result.plan
    usable = (
        type(plan) is ClassWorldAssemblyPlan
        and plan.contract_version == SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION
        and type(plan.input_digest) is ClassWorldAssemblyInputDigest
        and plan.input_digest.algorithm == SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM
        and _is_sha256_hex(plan.input_digest.hex_digest)
        and type(plan.inventory) is ClassWorldArtifactInventory
        and plan.inventory.contract_version
        == SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION
        and type(plan.inventory.artifacts) is tuple
        and bool(plan.inventory.artifacts)
        and all(
            type(artifact) is ClassWorldPackageArtifactDeclaration
            and artifact.digest_algorithm == SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM
            and _is_sha256_hex(artifact.digest_hex)
            for artifact in plan.inventory.artifacts
        )
    )
    if not usable:
        return _issue(
            ClassWorldArtifactFileVerificationIssueCode.PLAN_INVALID,
            "plan_result.plan must retain usable canonical assembly-plan output.",
            "plan_result.plan",
        )
    return None


def _validated_root_value(
    artifact_root: object,
) -> tuple[Path | None, ClassWorldArtifactFileVerificationIssue | None]:
    if artifact_root is None or (isinstance(artifact_root, str) and not artifact_root.strip()):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_REQUIRED,
            "artifact_root must be a non-empty absolute str or pathlib.Path.",
            "artifact_root",
        )
    if not isinstance(artifact_root, (str, Path)):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_INVALID_TYPE,
            "artifact_root must be a str or pathlib.Path.",
            "artifact_root",
        )
    root = Path(artifact_root)
    if not root.is_absolute():
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_NOT_ABSOLUTE,
            "artifact_root must be an absolute path.",
            "artifact_root",
        )
    return root, None


def _validated_relative_path(
    candidate: object,
    index: int,
    package_id: str | None,
) -> tuple[PurePosixPath | None, ClassWorldArtifactFileVerificationIssue | None]:
    location = f"bindings[{index}].relative_path"
    if candidate is None or (isinstance(candidate, str) and not candidate.strip()):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_REQUIRED,
            f"{location} must contain a canonical relative file path.",
            location,
            package_id=package_id,
            binding_index=index,
        )
    if type(candidate) is not str:
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID_TYPE,
            f"{location} must be a string.",
            location,
            package_id=package_id,
            binding_index=index,
        )
    if "\x00" in candidate or "\\" in candidate:
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID,
            f"{location} must use canonical portable forward-slash syntax.",
            location,
            package_id=package_id,
            binding_index=index,
        )

    posix_path = PurePosixPath(candidate)
    windows_path = PureWindowsPath(candidate)
    if posix_path.is_absolute() or windows_path.is_absolute() or bool(windows_path.drive):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_ABSOLUTE,
            f"{location} must be relative to artifact_root.",
            location,
            package_id=package_id,
            binding_index=index,
        )
    if ".." in posix_path.parts:
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_TRAVERSAL,
            f"{location} must not contain parent traversal.",
            location,
            package_id=package_id,
            binding_index=index,
        )
    normalized = PurePosixPath(*posix_path.parts)
    if not normalized.parts or normalized.as_posix() == "." or normalized.as_posix() != candidate:
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID,
            f"{location} must already be a canonical relative file path.",
            location,
            package_id=package_id,
            binding_index=index,
        )
    return normalized, None


def _validated_bindings(
    plan: ClassWorldAssemblyPlan,
    bindings: object,
) -> tuple[
    tuple[tuple[int, ClassWorldPackageArtifactFileBinding, PurePosixPath], ...],
    tuple[ClassWorldArtifactFileVerificationIssue, ...],
]:
    if type(bindings) is not tuple:
        return (), (
            _issue(
                ClassWorldArtifactFileVerificationIssueCode.BINDINGS_REQUIRED,
                "bindings must be an immutable tuple of package artifact file bindings.",
                "bindings",
            ),
        )

    expected_versions = {
        artifact.package_id: artifact.package_version for artifact in plan.inventory.artifacts
    }
    bindings_by_package: dict[
        str, tuple[int, ClassWorldPackageArtifactFileBinding, PurePosixPath]
    ] = {}
    seen_package_ids: set[str] = set()
    paths: dict[str, tuple[int, str]] = {}
    issues: list[ClassWorldArtifactFileVerificationIssue] = []

    for index, candidate in enumerate(bindings):
        location = f"bindings[{index}]"
        if type(candidate) is not ClassWorldPackageArtifactFileBinding:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.BINDING_INVALID_TYPE,
                    f"{location} must be a package artifact file binding.",
                    location,
                    binding_index=index,
                )
            )
            continue

        binding = candidate
        package_id = binding.package_id if isinstance(binding.package_id, str) else None
        normalized, path_issue = _validated_relative_path(
            binding.relative_path,
            index,
            package_id,
        )
        if path_issue is not None:
            issues.append(path_issue)

        if package_id is not None and package_id in seen_package_ids:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_DUPLICATE,
                    f'{location}.package_id duplicates package "{package_id}".',
                    f"{location}.package_id",
                    package_id=package_id,
                    binding_index=index,
                )
            )
        elif package_id is not None:
            seen_package_ids.add(package_id)

        if package_id not in expected_versions:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_UNEXPECTED,
                    f"{location} binds an unexpected package.",
                    location,
                    package_id=package_id,
                    binding_index=index,
                )
            )
        elif binding.package_version != expected_versions[package_id]:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_VERSION_MISMATCH,
                    f"{location}.package_version does not equal the planned package version.",
                    f"{location}.package_version",
                    package_id=package_id,
                    binding_index=index,
                )
            )

        if normalized is not None:
            normalized_string = normalized.as_posix()
            if normalized_string in paths:
                issues.append(
                    _issue(
                        ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_DUPLICATE,
                        f'{location}.relative_path duplicates "{normalized_string}".',
                        f"{location}.relative_path",
                        package_id=package_id,
                        binding_index=index,
                    )
                )
            else:
                paths[normalized_string] = (index, package_id or "")

        if (
            package_id in expected_versions
            and package_id not in bindings_by_package
            and normalized is not None
        ):
            bindings_by_package[package_id] = (index, binding, normalized)

    for artifact in plan.inventory.artifacts:
        if artifact.package_id not in bindings_by_package:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_MISSING,
                    f'No file binding was supplied for package "{artifact.package_id}".',
                    "bindings",
                    package_id=artifact.package_id,
                )
            )

    if issues:
        return (), tuple(issues)
    return (
        tuple(bindings_by_package[artifact.package_id] for artifact in plan.inventory.artifacts),
        (),
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


def _inspected_root(
    root: Path,
) -> tuple[Path | None, ClassWorldArtifactFileVerificationIssue | None]:
    try:
        metadata = root.lstat()
    except FileNotFoundError:
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_NOT_FOUND,
            "artifact_root does not exist.",
            "artifact_root",
        )
    except (OSError, ValueError):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_INSPECTION_FAILED,
            "artifact_root could not be inspected.",
            "artifact_root",
        )
    if stat.S_ISLNK(metadata.st_mode):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_SYMLINK_NOT_ALLOWED,
            "artifact_root must not be a symbolic link.",
            "artifact_root",
        )
    if not stat.S_ISDIR(metadata.st_mode):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_NOT_DIRECTORY,
            "artifact_root must be an existing directory.",
            "artifact_root",
        )
    try:
        return root.resolve(strict=True), None
    except (OSError, ValueError):
        return None, _issue(
            ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_INSPECTION_FAILED,
            "artifact_root could not be resolved.",
            "artifact_root",
        )


def _inspect_files(
    root: Path,
    bindings: tuple[tuple[int, ClassWorldPackageArtifactFileBinding, PurePosixPath], ...],
) -> tuple[
    tuple[tuple[int, ClassWorldPackageArtifactFileBinding, Path, os.stat_result], ...],
    tuple[ClassWorldArtifactFileVerificationIssue, ...],
]:
    inspected: list[tuple[int, ClassWorldPackageArtifactFileBinding, Path, os.stat_result]] = []
    issues: list[ClassWorldArtifactFileVerificationIssue] = []
    file_identities: dict[tuple[int, int], tuple[int, str]] = {}

    for index, binding, relative_path in bindings:
        location = f"bindings[{index}].relative_path"
        candidate = root.joinpath(*relative_path.parts)
        if _contains_symlink(root, relative_path):
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_SYMLINK_NOT_ALLOWED,
                    f"{location} must not refer to or pass through a symbolic link.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        try:
            resolved = candidate.resolve(strict=False)
        except (OSError, ValueError):
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_OUTSIDE_ROOT,
                    f"{location} could not be resolved inside artifact_root.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        if not resolved.is_relative_to(root):
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_OUTSIDE_ROOT,
                    f"{location} resolves outside artifact_root.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_NOT_FOUND,
                    f"{location} does not exist.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        except (OSError, ValueError):
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_READ_FAILED,
                    f"{location} could not be inspected.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        if stat.S_ISLNK(metadata.st_mode):
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_SYMLINK_NOT_ALLOWED,
                    f"{location} must not be a symbolic link.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        if not stat.S_ISREG(metadata.st_mode):
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_NOT_REGULAR,
                    f"{location} must refer to a regular file.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        identity = (metadata.st_dev, metadata.st_ino)
        if identity in file_identities:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_IDENTITY_DUPLICATE,
                    f"{location} aliases a file already bound to another package.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        file_identities[identity] = (index, binding.package_id)
        if metadata.st_size > MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES:
            issues.append(
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_TOO_LARGE,
                    (
                        f"{location} exceeds the per-artifact limit of "
                        f"{MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES} bytes."
                    ),
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                )
            )
            continue
        inspected.append((index, binding, candidate, metadata))

    total_size = sum(metadata.st_size for _, _, _, metadata in inspected)
    if total_size > MAX_CLASS_WORLD_ARTIFACT_SET_BYTES:
        issues.append(
            _issue(
                ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_SET_TOO_LARGE,
                (
                    "The bound artifact set exceeds the aggregate limit of "
                    f"{MAX_CLASS_WORLD_ARTIFACT_SET_BYTES} bytes."
                ),
                "bindings",
            )
        )
    if issues:
        return (), tuple(issues)
    return tuple(inspected), ()


def _read_files(
    inspected: tuple[tuple[int, ClassWorldPackageArtifactFileBinding, Path, os.stat_result], ...],
    *,
    root: Path | None = None,
    require_descriptor_confinement: bool = False,
) -> tuple[
    tuple[bytes, ...],
    tuple[ClassWorldPackageArtifactFileRead, ...],
    ClassWorldArtifactFileVerificationIssue | None,
]:
    contents: list[bytes] = []
    reads: list[ClassWorldPackageArtifactFileRead] = []
    total_read = 0
    if require_descriptor_confinement and (
        root is None
        or os.open not in os.supports_dir_fd
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
    ):
        return (
            (),
            (),
            _issue(
                ClassWorldArtifactFileVerificationIssueCode.FILE_READ_FAILED,
                "Descriptor-confined artifact reads are unavailable on this platform.",
                "bindings",
            ),
        )
    for index, binding, path, inspected_metadata in inspected:
        location = f"bindings[{index}].relative_path"
        descriptor: int | None = None
        parent_descriptor: int | None = None
        try:
            flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            if not require_descriptor_confinement:
                descriptor = os.open(path, flags)
            else:
                assert root is not None
                parent_descriptor = os.open(
                    root,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                )
                parts = PurePosixPath(binding.relative_path).parts
                for part in parts[:-1]:
                    next_descriptor = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=parent_descriptor,
                    )
                    os.close(parent_descriptor)
                    parent_descriptor = next_descriptor
                descriptor = os.open(parts[-1], flags, dir_fd=parent_descriptor)
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                return (
                    (),
                    (),
                    _issue(
                        ClassWorldArtifactFileVerificationIssueCode.FILE_NOT_REGULAR,
                        f"{location} must remain a regular file while being read.",
                        location,
                        package_id=binding.package_id,
                        binding_index=index,
                    ),
                )
            if (metadata.st_dev, metadata.st_ino) != (
                inspected_metadata.st_dev,
                inspected_metadata.st_ino,
            ):
                return (
                    (),
                    (),
                    _issue(
                        ClassWorldArtifactFileVerificationIssueCode.FILE_READ_FAILED,
                        f"{location} changed identity before it could be read.",
                        location,
                        package_id=binding.package_id,
                        binding_index=index,
                    ),
                )
            if metadata.st_size > MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES:
                return (
                    (),
                    (),
                    _issue(
                        ClassWorldArtifactFileVerificationIssueCode.FILE_TOO_LARGE,
                        (
                            f"{location} exceeds the per-artifact limit of "
                            f"{MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES} bytes."
                        ),
                        location,
                        package_id=binding.package_id,
                        binding_index=index,
                    ),
                )
            with os.fdopen(descriptor, "rb") as stream:
                descriptor = None
                content = stream.read(MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES + 1)
        except (OSError, ValueError):
            return (
                (),
                (),
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_READ_FAILED,
                    f"{location} could not be read safely.",
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                ),
            )
        finally:
            if descriptor is not None:
                with suppress(OSError):
                    os.close(descriptor)
            if parent_descriptor is not None:
                with suppress(OSError):
                    os.close(parent_descriptor)

        if len(content) > MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES:
            return (
                (),
                (),
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.FILE_TOO_LARGE,
                    (
                        f"{location} exceeds the per-artifact limit of "
                        f"{MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES} bytes."
                    ),
                    location,
                    package_id=binding.package_id,
                    binding_index=index,
                ),
            )
        total_read += len(content)
        if total_read > MAX_CLASS_WORLD_ARTIFACT_SET_BYTES:
            return (
                (),
                (),
                _issue(
                    ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_SET_TOO_LARGE,
                    (
                        "The bytes read exceed the aggregate artifact-set limit of "
                        f"{MAX_CLASS_WORLD_ARTIFACT_SET_BYTES} bytes."
                    ),
                    "bindings",
                ),
            )
        contents.append(content)
        reads.append(ClassWorldPackageArtifactFileRead(binding=binding, bytes_read=len(content)))
    return tuple(contents), tuple(reads), None


def _verify_class_world_artifact_files_with_contents(
    plan_result: ClassWorldAssemblyPlanResult,
    artifact_root: str | Path,
    bindings: tuple[ClassWorldPackageArtifactFileBinding, ...],
    *,
    require_descriptor_confinement: bool = False,
) -> tuple[ClassWorldArtifactFileVerificationResult, tuple[bytes, ...]]:
    """Run the existing pipeline and retain the exact delegated byte tuple."""
    plan_failure = _plan_issue(plan_result)
    if plan_failure is not None:
        return _failure(plan_failure), ()

    root, root_value_issue = _validated_root_value(artifact_root)
    if root_value_issue is not None:
        return _failure(root_value_issue), ()

    assert type(plan_result) is ClassWorldAssemblyPlanResult
    assert plan_result.plan is not None
    ordered_bindings, binding_issues = _validated_bindings(plan_result.plan, bindings)
    if binding_issues:
        return _failure(*binding_issues), ()

    assert root is not None
    resolved_root, root_issue = _inspected_root(root)
    if root_issue is not None:
        return _failure(root_issue), ()

    assert resolved_root is not None
    inspected, file_issues = _inspect_files(resolved_root, ordered_bindings)
    if file_issues:
        return _failure(*file_issues), ()

    contents, reads, read_issue = _read_files(
        inspected,
        root=resolved_root,
        require_descriptor_confinement=require_descriptor_confinement,
    )
    if read_issue is not None:
        return _failure(read_issue), ()

    content_verification = verify_class_world_artifact_contents(plan_result, contents)
    return (
        ClassWorldArtifactFileVerificationResult(
            contract_version=SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION,
            files=reads,
            content_verification=content_verification,
            issues=(),
        ),
        contents,
    )


def verify_class_world_artifact_files(
    plan_result: ClassWorldAssemblyPlanResult,
    artifact_root: str | Path,
    bindings: tuple[ClassWorldPackageArtifactFileBinding, ...],
) -> ClassWorldArtifactFileVerificationResult:
    """Bind, bounded-read, and delegate verification for planned artifacts."""
    result, _ = _verify_class_world_artifact_files_with_contents(
        plan_result,
        artifact_root,
        bindings,
    )
    return result
