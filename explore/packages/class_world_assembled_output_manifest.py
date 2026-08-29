"""Pure deterministic composition of verified assembled-output identities."""

from __future__ import annotations

import hashlib
import json

from explore.packages.class_world_artifact_file_verification_models import (
    ClassWorldArtifactFileVerificationResult,
)
from explore.packages.class_world_materialization_plan import (
    build_class_world_materialization_plan,
)
from explore.packages.class_world_materialization_plan_models import (
    ClassWorldMaterializationPlan,
    ClassWorldMaterializationPlanResult,
)
from explore.packages.class_world_verified_materialization_models import (
    SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION,
    ClassWorldMaterializedPackage,
    ClassWorldVerifiedMaterialization,
    ClassWorldVerifiedMaterializationResult,
)

from .class_world_assembled_output_manifest_models import (
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM,
    ClassWorldAssembledOutputManifest,
    ClassWorldAssembledOutputManifestDigest,
    ClassWorldAssembledOutputManifestIssue,
    ClassWorldAssembledOutputManifestIssueCode,
    ClassWorldAssembledOutputManifestResult,
    ClassWorldAssembledOutputPackage,
)


def _issue(
    code: ClassWorldAssembledOutputManifestIssueCode,
    message: str,
    location: str,
) -> ClassWorldAssembledOutputManifestIssue:
    return ClassWorldAssembledOutputManifestIssue(code=code, message=message, location=location)


def _failure(
    issue: ClassWorldAssembledOutputManifestIssue,
) -> ClassWorldAssembledOutputManifestResult:
    return ClassWorldAssembledOutputManifestResult(manifest=None, digest=None, issues=(issue,))


def _complete_materialization(
    candidate: object,
) -> tuple[
    ClassWorldVerifiedMaterialization | None,
    ClassWorldAssembledOutputManifestIssue | None,
]:
    if candidate is None:
        return None, _issue(
            ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_RESULT_REQUIRED,
            "A verified class-world materialization result is required.",
            "materialization_result",
        )
    if type(candidate) is not ClassWorldVerifiedMaterializationResult:
        return None, _issue(
            ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_RESULT_INVALID,
            "materialization_result must be a verified materialization result.",
            "materialization_result",
        )
    if (
        type(candidate.issues) is not tuple
        or candidate.issues
        or type(candidate.materialization) is not ClassWorldVerifiedMaterialization
        or candidate.source_verification is not candidate.materialization.source_verification
    ):
        return None, _issue(
            ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_NOT_COMPLETE,
            "materialization_result must contain one complete verified materialization.",
            "materialization_result",
        )
    return candidate.materialization, None


def _materialization_is_coherent(materialization: ClassWorldVerifiedMaterialization) -> bool:
    if (
        materialization.contract_version
        != SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION
        or type(materialization.plan) is not ClassWorldMaterializationPlan
        or type(materialization.source_verification) is not ClassWorldArtifactFileVerificationResult
        or type(materialization.packages) is not tuple
        or not materialization.packages
        or type(materialization.total_bytes) is not int
        or materialization.total_bytes < 0
    ):
        return False

    rebuilt = build_class_world_materialization_plan(materialization.plan.file_verification)
    if (
        type(rebuilt) is not ClassWorldMaterializationPlanResult
        or not rebuilt.is_planned
        or rebuilt.plan != materialization.plan
        or materialization.source_verification != materialization.plan.file_verification
        or len(materialization.packages) != len(materialization.plan.packages)
    ):
        return False

    total_bytes = 0
    for materialized, planned in zip(
        materialization.packages, materialization.plan.packages, strict=True
    ):
        if (
            type(materialized) is not ClassWorldMaterializedPackage
            or materialized.package is not planned
            or type(materialized.bytes_written) is not int
            or materialized.bytes_written != planned.source.bytes_read
        ):
            return False
        total_bytes += materialized.bytes_written
    return total_bytes == materialization.total_bytes == materialization.plan.total_bytes


def _canonical_text(manifest: ClassWorldAssembledOutputManifest) -> str:
    payload = {
        "contract_version": manifest.contract_version,
        "packages": [
            {
                "package_id": package.package_id,
                "package_version": package.package_version,
                "digest_algorithm": package.digest_algorithm,
                "digest_hex": package.digest_hex,
                "relative_path": package.relative_path,
                "bytes_written": package.bytes_written,
            }
            for package in manifest.packages
        ],
        "total_bytes": manifest.total_bytes,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"


def _manifest_matches_materialization(manifest: ClassWorldAssembledOutputManifest) -> bool:
    if (
        manifest.contract_version
        != SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION
        or type(manifest.materialization) is not ClassWorldVerifiedMaterialization
        or not _materialization_is_coherent(manifest.materialization)
        or type(manifest.packages) is not tuple
        or len(manifest.packages) != len(manifest.materialization.packages)
        or type(manifest.total_bytes) is not int
        or manifest.total_bytes != manifest.materialization.total_bytes
    ):
        return False
    for output, materialized in zip(
        manifest.packages, manifest.materialization.packages, strict=True
    ):
        planned = materialized.package
        artifact = planned.artifact
        if (
            type(output) is not ClassWorldAssembledOutputPackage
            or output.package_id != artifact.package_id
            or output.package_version != artifact.package_version
            or output.digest_algorithm != artifact.digest_algorithm
            or output.digest_hex != artifact.digest_hex
            or output.relative_path != planned.relative_path
            or output.bytes_written != materialized.bytes_written
        ):
            return False
    return True


def serialize_class_world_assembled_output_manifest(
    manifest: ClassWorldAssembledOutputManifest,
) -> str:
    """Serialize one coherent manifest to its canonical compact JSON form."""
    if type(
        manifest
    ) is not ClassWorldAssembledOutputManifest or not _manifest_matches_materialization(manifest):
        raise ValueError("manifest must retain coherent verified materialization output.")
    return _canonical_text(manifest)


def build_class_world_assembled_output_manifest(
    materialization_result: ClassWorldVerifiedMaterializationResult,
) -> ClassWorldAssembledOutputManifestResult:
    """Project and digest an exact successful materialization without filesystem access."""
    materialization, upstream_issue = _complete_materialization(materialization_result)
    if upstream_issue is not None:
        return _failure(upstream_issue)
    assert materialization is not None
    if not _materialization_is_coherent(materialization):
        return _failure(
            _issue(
                ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_INCONSISTENT,
                "materialization_result must retain coherent canonical materialization output.",
                "materialization_result.materialization",
            )
        )

    packages = tuple(
        ClassWorldAssembledOutputPackage(
            package_id=materialized.package.artifact.package_id,
            package_version=materialized.package.artifact.package_version,
            digest_algorithm=materialized.package.artifact.digest_algorithm,
            digest_hex=materialized.package.artifact.digest_hex,
            relative_path=materialized.package.relative_path,
            bytes_written=materialized.bytes_written,
        )
        for materialized in materialization.packages
    )
    manifest = ClassWorldAssembledOutputManifest(
        contract_version=SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION,
        materialization=materialization,
        packages=packages,
        total_bytes=materialization.total_bytes,
    )
    canonical_bytes = serialize_class_world_assembled_output_manifest(manifest).encode("utf-8")
    digest = ClassWorldAssembledOutputManifestDigest(
        algorithm=SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM,
        hex_digest=hashlib.sha256(canonical_bytes).hexdigest(),
    )
    return ClassWorldAssembledOutputManifestResult(manifest=manifest, digest=digest, issues=())
