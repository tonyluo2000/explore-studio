"""Pure deterministic verification of package artifact content bytes."""

from __future__ import annotations

import hashlib

from explore.packages.class_world_artifact_content_verification_models import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION,
    ClassWorldArtifactContentVerification,
    ClassWorldArtifactContentVerificationIssue,
    ClassWorldArtifactContentVerificationIssueCode,
    ClassWorldArtifactContentVerificationResult,
    ClassWorldPackageArtifactContentDigest,
    ClassWorldPackageArtifactContentVerification,
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
    code: ClassWorldArtifactContentVerificationIssueCode,
    message: str,
    location: str,
    *,
    artifact_index: int | None = None,
) -> ClassWorldArtifactContentVerificationIssue:
    return ClassWorldArtifactContentVerificationIssue(
        code=code,
        message=message,
        location=location,
        artifact_index=artifact_index,
    )


def _is_sha256_hex(candidate: object) -> bool:
    return (
        isinstance(candidate, str)
        and len(candidate) == 64
        and all(character in "0123456789abcdef" for character in candidate)
    )


def _plan_is_usable(plan: object) -> bool:
    """Check only the upstream fields required by this verification layer."""
    if type(plan) is not ClassWorldAssemblyPlan:
        return False
    if plan.contract_version != SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION:
        return False
    if type(plan.input_digest) is not ClassWorldAssemblyInputDigest:
        return False
    if (
        plan.input_digest.algorithm != SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM
        or not _is_sha256_hex(plan.input_digest.hex_digest)
    ):
        return False
    if type(plan.inventory) is not ClassWorldArtifactInventory:
        return False
    if plan.inventory.contract_version != SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION:
        return False
    if type(plan.inventory.artifacts) is not tuple or not plan.inventory.artifacts:
        return False
    return all(
        type(artifact) is ClassWorldPackageArtifactDeclaration
        and artifact.digest_algorithm == SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM
        and _is_sha256_hex(artifact.digest_hex)
        for artifact in plan.inventory.artifacts
    )


def verify_class_world_artifact_contents(
    plan_result: ClassWorldAssemblyPlanResult,
    artifact_contents: tuple[bytes, ...],
) -> ClassWorldArtifactContentVerificationResult:
    """Hash and compare one immutable payload per canonical plan artifact.

    Artifact contents are positional only at this boundary: their order must
    match the canonical package order already retained by the assembly
    plan. No inventory joins, plan-digest recomputation, or file I/O occurs.
    """
    if plan_result is None:
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=(
                _issue(
                    ClassWorldArtifactContentVerificationIssueCode.PLAN_RESULT_REQUIRED,
                    "A class-world assembly plan result is required.",
                    "plan_result",
                ),
            ),
        )
    if type(plan_result) is not ClassWorldAssemblyPlanResult:
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=(
                _issue(
                    ClassWorldArtifactContentVerificationIssueCode.PLAN_RESULT_INVALID,
                    "plan_result must be a class-world assembly plan result.",
                    "plan_result",
                ),
            ),
        )
    if type(plan_result.issues) is not tuple or plan_result.issues or plan_result.plan is None:
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=(
                _issue(
                    ClassWorldArtifactContentVerificationIssueCode.PLAN_NOT_BUILT,
                    "plan_result must contain one successfully built assembly plan.",
                    "plan_result",
                ),
            ),
        )
    if not _plan_is_usable(plan_result.plan):
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=(
                _issue(
                    ClassWorldArtifactContentVerificationIssueCode.PLAN_INVALID,
                    "plan_result.plan must retain usable canonical assembly-plan output.",
                    "plan_result.plan",
                ),
            ),
        )

    if type(artifact_contents) is not tuple:
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=(
                _issue(
                    ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENTS_REQUIRED,
                    "artifact_contents must be an immutable ordered tuple of bytes.",
                    "artifact_contents",
                ),
            ),
        )

    plan = plan_result.plan
    artifacts = plan.inventory.artifacts
    if len(artifact_contents) != len(artifacts):
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=(
                _issue(
                    ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENT_COUNT_MISMATCH,
                    (
                        "artifact_contents must contain exactly one payload for each "
                        f"planned package artifact; expected {len(artifacts)}, "
                        f"received {len(artifact_contents)}."
                    ),
                    "artifact_contents",
                ),
            ),
        )

    content_issues = tuple(
        _issue(
            ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENT_INVALID_TYPE,
            f"artifact_contents[{index}] must be immutable bytes.",
            f"artifact_contents[{index}]",
            artifact_index=index,
        )
        for index, content in enumerate(artifact_contents)
        if type(content) is not bytes
    )
    if content_issues:
        return ClassWorldArtifactContentVerificationResult(
            verification=None,
            issues=content_issues,
        )

    packages: list[ClassWorldPackageArtifactContentVerification] = []
    for artifact, content in zip(artifacts, artifact_contents, strict=True):
        actual_hex = hashlib.sha256(content).hexdigest()
        packages.append(
            ClassWorldPackageArtifactContentVerification(
                artifact=artifact,
                actual_digest=ClassWorldPackageArtifactContentDigest(
                    algorithm=SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM,
                    hex_digest=actual_hex,
                ),
                matches=actual_hex == artifact.digest_hex,
            )
        )
    return ClassWorldArtifactContentVerificationResult(
        verification=ClassWorldArtifactContentVerification(
            contract_version=(SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION),
            plan=plan,
            packages=tuple(packages),
        ),
        issues=(),
    )
