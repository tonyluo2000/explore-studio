"""Pure deterministic output-layout planning for verified package artifacts."""

from __future__ import annotations

from explore.packages.class_world_artifact_content_verification_models import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION,
    ClassWorldArtifactContentVerification,
    ClassWorldArtifactContentVerificationResult,
    ClassWorldPackageArtifactContentDigest,
    ClassWorldPackageArtifactContentVerification,
)
from explore.packages.class_world_artifact_file_verification_models import (
    MAX_CLASS_WORLD_ARTIFACT_SET_BYTES,
    MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES,
    SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION,
    ClassWorldArtifactFileVerificationResult,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackageArtifactFileRead,
)
from explore.packages.class_world_artifact_inventory_models import (
    SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM,
    ClassWorldArtifactInventory,
    ClassWorldPackageArtifactDeclaration,
)
from explore.packages.class_world_assembly_plan_models import ClassWorldAssemblyPlan
from explore.packages.class_world_materialization_plan_models import (
    SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION,
    ClassWorldMaterializationPlan,
    ClassWorldMaterializationPlanIssue,
    ClassWorldMaterializationPlanIssueCode,
    ClassWorldMaterializationPlanResult,
    ClassWorldPackageMaterialization,
)
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version


def _issue(
    code: ClassWorldMaterializationPlanIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    package_index: int | None = None,
) -> ClassWorldMaterializationPlanIssue:
    return ClassWorldMaterializationPlanIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id,
        package_index=package_index,
    )


def _failure(
    *issues: ClassWorldMaterializationPlanIssue,
) -> ClassWorldMaterializationPlanResult:
    return ClassWorldMaterializationPlanResult(plan=None, issues=tuple(issues))


def _is_sha256_hex(candidate: object) -> bool:
    return (
        type(candidate) is str
        and len(candidate) == 64
        and all(character in "0123456789abcdef" for character in candidate)
    )


def _upstream_issue(
    candidate: object,
) -> ClassWorldMaterializationPlanIssue | None:
    if candidate is None:
        return _issue(
            ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_RESULT_REQUIRED,
            "A class-world artifact-file verification result is required.",
            "file_verification_result",
        )
    if type(candidate) is not ClassWorldArtifactFileVerificationResult:
        return _issue(
            ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_RESULT_INVALID,
            "file_verification_result must be an artifact-file verification result.",
            "file_verification_result",
        )
    if (
        candidate.contract_version
        != SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION
        or type(candidate.issues) is not tuple
        or candidate.issues
        or type(candidate.files) is not tuple
        or not candidate.files
        or type(candidate.content_verification) is not ClassWorldArtifactContentVerificationResult
        or type(candidate.content_verification.issues) is not tuple
        or candidate.content_verification.issues
        or candidate.content_verification.verification is None
    ):
        return _issue(
            ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_NOT_COMPLETE,
            "file_verification_result must contain one complete artifact-file verification.",
            "file_verification_result",
        )
    return None


def _structural_issues(
    result: ClassWorldArtifactFileVerificationResult,
) -> tuple[ClassWorldMaterializationPlanIssue, ...]:
    content_result = result.content_verification
    assert type(content_result) is ClassWorldArtifactContentVerificationResult
    verification = content_result.verification
    if (
        type(verification) is not ClassWorldArtifactContentVerification
        or verification.contract_version
        != SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION
        or type(verification.plan) is not ClassWorldAssemblyPlan
        or type(verification.plan.inventory) is not ClassWorldArtifactInventory
        or type(verification.plan.inventory.artifacts) is not tuple
        or type(verification.packages) is not tuple
        or len(result.files) != len(verification.packages)
        or len(verification.packages) != len(verification.plan.inventory.artifacts)
    ):
        return (
            _issue(
                ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_INCONSISTENT,
                "file_verification_result must retain coherent canonical upstream output.",
                "file_verification_result",
            ),
        )

    issues: list[ClassWorldMaterializationPlanIssue] = []
    seen_package_ids: set[str] = set()
    for index, (source, package, planned_artifact) in enumerate(
        zip(
            result.files,
            verification.packages,
            verification.plan.inventory.artifacts,
            strict=True,
        )
    ):
        location = f"file_verification_result.files[{index}]"
        usable = (
            type(source) is ClassWorldPackageArtifactFileRead
            and type(source.binding) is ClassWorldPackageArtifactFileBinding
            and type(source.bytes_read) is int
            and 0 <= source.bytes_read <= MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES
            and type(package) is ClassWorldPackageArtifactContentVerification
            and type(planned_artifact) is ClassWorldPackageArtifactDeclaration
            and package.artifact is planned_artifact
            and type(package.actual_digest) is ClassWorldPackageArtifactContentDigest
            and package.actual_digest.algorithm
            == SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM
            and _is_sha256_hex(package.actual_digest.hex_digest)
            and type(package.matches) is bool
            and type(planned_artifact.package_id) is str
            and is_valid_identifier(planned_artifact.package_id)
            and type(planned_artifact.package_version) is str
            and is_valid_semantic_version(planned_artifact.package_version)
            and planned_artifact.digest_algorithm
            == SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM
            and _is_sha256_hex(planned_artifact.digest_hex)
            and source.binding.package_id == planned_artifact.package_id
            and source.binding.package_version == planned_artifact.package_version
            and (package.actual_digest.hex_digest == planned_artifact.digest_hex) == package.matches
            and planned_artifact.package_id not in seen_package_ids
        )
        if not usable:
            package_id = getattr(planned_artifact, "package_id", None)
            issues.append(
                _issue(
                    ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_INCONSISTENT,
                    f"{location} is inconsistent with canonical verified package output.",
                    location,
                    package_id=package_id if isinstance(package_id, str) else None,
                    package_index=index,
                )
            )
            continue
        seen_package_ids.add(planned_artifact.package_id)
    total_bytes = sum(
        source.bytes_read
        for source in result.files
        if type(source) is ClassWorldPackageArtifactFileRead and type(source.bytes_read) is int
    )
    if total_bytes > MAX_CLASS_WORLD_ARTIFACT_SET_BYTES:
        issues.append(
            _issue(
                ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_INCONSISTENT,
                "file_verification_result exceeds the verified aggregate byte limit.",
                "file_verification_result.files",
            )
        )
    return tuple(issues)


def build_class_world_materialization_plan(
    file_verification_result: ClassWorldArtifactFileVerificationResult,
) -> ClassWorldMaterializationPlanResult:
    """Derive canonical package-separated output paths without filesystem access."""
    upstream_issue = _upstream_issue(file_verification_result)
    if upstream_issue is not None:
        return _failure(upstream_issue)

    structural_issues = _structural_issues(file_verification_result)
    if structural_issues:
        return _failure(*structural_issues)

    assert file_verification_result.content_verification is not None
    verification = file_verification_result.content_verification.verification
    assert verification is not None
    mismatches = tuple(
        _issue(
            ClassWorldMaterializationPlanIssueCode.ARTIFACT_CONTENT_MISMATCH,
            f'Package "{package.artifact.package_id}" did not match its declared digest.',
            f"file_verification_result.content_verification.verification.packages[{index}]",
            package_id=package.artifact.package_id,
            package_index=index,
        )
        for index, package in enumerate(verification.packages)
        if not package.matches
    )
    if mismatches:
        return _failure(*mismatches)

    packages = tuple(
        ClassWorldPackageMaterialization(
            artifact=package.artifact,
            source=source,
            relative_path=(
                f"packages/{package.artifact.package_id}/"
                f"{package.artifact.package_version}/artifact"
            ),
        )
        for source, package in zip(
            file_verification_result.files,
            verification.packages,
            strict=True,
        )
    )
    return ClassWorldMaterializationPlanResult(
        plan=ClassWorldMaterializationPlan(
            contract_version=SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION,
            file_verification=file_verification_result,
            packages=packages,
            total_bytes=sum(package.source.bytes_read for package in packages),
        ),
        issues=(),
    )
