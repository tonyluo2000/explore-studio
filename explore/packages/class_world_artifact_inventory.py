"""Pure deterministic inventory of pinned Explorer Package artifacts."""

from __future__ import annotations

from explore.packages.class_world_artifact_inventory_models import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryIssue,
    ClassWorldArtifactInventoryIssueCode,
    ClassWorldArtifactInventoryResult,
    ClassWorldPackageArtifactDeclaration,
)
from explore.packages.class_world_release_declaration_digest_verification_models import (
    ClassWorldReleaseDeclarationDigestVerificationResult,
)
from explore.packages.class_world_release_declaration_file_digest_verification_models import (
    ClassWorldReleaseDeclarationFileDigestVerificationResult,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version


def _issue(
    code: ClassWorldArtifactInventoryIssueCode,
    message: str,
    location: str,
    *,
    package_id: str | None = None,
    artifact_index: int | None = None,
) -> ClassWorldArtifactInventoryIssue:
    return ClassWorldArtifactInventoryIssue(
        code=code,
        message=message,
        location=location,
        package_id=package_id,
        artifact_index=artifact_index,
    )


def _verification_issue(
    candidate: object,
) -> ClassWorldArtifactInventoryIssue | None:
    if candidate is None:
        return _issue(
            ClassWorldArtifactInventoryIssueCode.VERIFICATION_RESULT_REQUIRED,
            "A release-declaration file digest verification result is required.",
            "verification_result",
        )
    if type(candidate) is not ClassWorldReleaseDeclarationFileDigestVerificationResult:
        return _issue(
            ClassWorldArtifactInventoryIssueCode.VERIFICATION_RESULT_INVALID,
            "verification_result must be a release-declaration file digest verification result.",
            "verification_result",
        )

    result = candidate
    verification = result.verification
    if (
        type(result.declaration) is not ClassWorldReleaseDeclaration
        or type(verification) is not ClassWorldReleaseDeclarationDigestVerificationResult
        or result.issues != ()
        or result.serialization_issues != ()
        or result.declaration_issues != ()
        or verification.matches is not True
        or verification.expected_digest != verification.actual_digest
    ):
        return _issue(
            ClassWorldArtifactInventoryIssueCode.DECLARATION_NOT_VERIFIED,
            "verification_result must contain one successfully verified release declaration.",
            "verification_result",
        )
    return None


def _validate_artifact(
    candidate: object,
    index: int,
) -> tuple[
    ClassWorldPackageArtifactDeclaration | None,
    tuple[ClassWorldArtifactInventoryIssue, ...],
]:
    location = f"artifact_declarations[{index}]"
    if type(candidate) is not ClassWorldPackageArtifactDeclaration:
        return None, (
            _issue(
                ClassWorldArtifactInventoryIssueCode.ARTIFACT_DECLARATION_INVALID_TYPE,
                f"{location} must be a package artifact declaration.",
                location,
                artifact_index=index,
            ),
        )

    artifact = candidate
    package_id = artifact.package_id if isinstance(artifact.package_id, str) else None
    issues: list[ClassWorldArtifactInventoryIssue] = []
    if not isinstance(artifact.package_id, str) or not is_valid_identifier(artifact.package_id):
        issues.append(
            _issue(
                ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_ID_INVALID,
                f"{location}.package_id must be a valid Explorer Package identifier.",
                f"{location}.package_id",
                package_id=package_id,
                artifact_index=index,
            )
        )
    if not isinstance(artifact.package_version, str) or not is_valid_semantic_version(
        artifact.package_version
    ):
        issues.append(
            _issue(
                ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_VERSION_INVALID,
                f"{location}.package_version must be a semantic version.",
                f"{location}.package_version",
                package_id=package_id,
                artifact_index=index,
            )
        )
    if artifact.digest_algorithm != SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM:
        issues.append(
            _issue(
                ClassWorldArtifactInventoryIssueCode.ARTIFACT_DIGEST_ALGORITHM_INVALID,
                f'{location}.digest_algorithm must be "sha256".',
                f"{location}.digest_algorithm",
                package_id=package_id,
                artifact_index=index,
            )
        )
    if (
        not isinstance(artifact.digest_hex, str)
        or len(artifact.digest_hex) != 64
        or any(character not in "0123456789abcdef" for character in artifact.digest_hex)
    ):
        issues.append(
            _issue(
                ClassWorldArtifactInventoryIssueCode.ARTIFACT_DIGEST_INVALID,
                f"{location}.digest_hex must contain exactly 64 lowercase hexadecimal characters.",
                f"{location}.digest_hex",
                package_id=package_id,
                artifact_index=index,
            )
        )
    return artifact, tuple(issues)


def build_class_world_artifact_inventory(
    verification_result: ClassWorldReleaseDeclarationFileDigestVerificationResult,
    artifact_declarations: tuple[ClassWorldPackageArtifactDeclaration, ...],
) -> ClassWorldArtifactInventoryResult:
    """Join verified release pins to exact package artifacts without reading files.

    Input declaration order is not authoritative. A successful inventory always
    follows the verified release declaration's package-pin order.
    """
    upstream_issue = _verification_issue(verification_result)
    if upstream_issue is not None:
        return ClassWorldArtifactInventoryResult(inventory=None, issues=(upstream_issue,))

    if type(artifact_declarations) is not tuple:
        return ClassWorldArtifactInventoryResult(
            inventory=None,
            issues=(
                _issue(
                    ClassWorldArtifactInventoryIssueCode.ARTIFACT_DECLARATIONS_REQUIRED,
                    "artifact_declarations must be an immutable ordered tuple.",
                    "artifact_declarations",
                ),
            ),
        )

    valid_artifacts: list[tuple[int, ClassWorldPackageArtifactDeclaration]] = []
    issues: list[ClassWorldArtifactInventoryIssue] = []
    for index, candidate in enumerate(artifact_declarations):
        artifact, artifact_issues = _validate_artifact(candidate, index)
        issues.extend(artifact_issues)
        if artifact is not None and not artifact_issues:
            valid_artifacts.append((index, artifact))

    assert verification_result.declaration is not None
    assert verification_result.verification is not None
    pins = verification_result.declaration.provenance.package_pins
    expected_versions = {pin.package_id: pin.package_version for pin in pins}
    artifacts_by_package: dict[str, ClassWorldPackageArtifactDeclaration] = {}

    for index, artifact in valid_artifacts:
        package_id = artifact.package_id
        location = f"artifact_declarations[{index}]"
        if package_id in artifacts_by_package:
            issues.append(
                _issue(
                    ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_DUPLICATE,
                    f'{location}.package_id duplicates package "{package_id}".',
                    f"{location}.package_id",
                    package_id=package_id,
                    artifact_index=index,
                )
            )
            continue
        artifacts_by_package[package_id] = artifact
        if package_id not in expected_versions:
            issues.append(
                _issue(
                    ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_UNEXPECTED,
                    f'{location} declares unpinned package "{package_id}".',
                    location,
                    package_id=package_id,
                    artifact_index=index,
                )
            )
        elif artifact.package_version != expected_versions[package_id]:
            issues.append(
                _issue(
                    ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_VERSION_MISMATCH,
                    (
                        f"{location}.package_version must equal pinned version "
                        f'"{expected_versions[package_id]}" for package "{package_id}".'
                    ),
                    f"{location}.package_version",
                    package_id=package_id,
                    artifact_index=index,
                )
            )

    for pin in pins:
        if pin.package_id not in artifacts_by_package:
            issues.append(
                _issue(
                    ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_MISSING,
                    f'No artifact declaration was supplied for pinned package "{pin.package_id}".',
                    "artifact_declarations",
                    package_id=pin.package_id,
                )
            )

    if issues:
        return ClassWorldArtifactInventoryResult(inventory=None, issues=tuple(issues))

    artifacts = tuple(artifacts_by_package[pin.package_id] for pin in pins)
    return ClassWorldArtifactInventoryResult(
        inventory=ClassWorldArtifactInventory(
            contract_version=SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION,
            declaration=verification_result.declaration,
            declaration_digest=verification_result.verification.actual_digest,
            artifacts=artifacts,
        ),
        issues=(),
    )
