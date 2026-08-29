"""Pure deterministic composition of class-world assembly inputs."""

from __future__ import annotations

import hashlib
import json

from explore.packages.class_world_artifact_inventory_models import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldPackageArtifactDeclaration,
)
from explore.packages.class_world_assembly_plan_models import (
    SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM,
    SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION,
    ClassWorldAssemblyInputDigest,
    ClassWorldAssemblyPlan,
    ClassWorldAssemblyPlanIssue,
    ClassWorldAssemblyPlanIssueCode,
    ClassWorldAssemblyPlanResult,
)
from explore.packages.class_world_configuration_models import ClassWorldPackagePin
from explore.packages.class_world_release_declaration_digest_models import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM,
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseProvenance,
)


def _issue(
    code: ClassWorldAssemblyPlanIssueCode,
    message: str,
    location: str,
) -> ClassWorldAssemblyPlanIssue:
    return ClassWorldAssemblyPlanIssue(code=code, message=message, location=location)


def _is_sha256_hex(candidate: object) -> bool:
    return (
        isinstance(candidate, str)
        and len(candidate) == 64
        and all(character in "0123456789abcdef" for character in candidate)
    )


def _inventory_is_coherent(inventory: object) -> bool:
    """Check the successful inventory output graph without rebuilding it."""
    if type(inventory) is not ClassWorldArtifactInventory:
        return False
    if inventory.contract_version != SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION:
        return False
    if type(inventory.declaration) is not ClassWorldReleaseDeclaration:
        return False
    if type(inventory.declaration.provenance) is not ClassWorldReleaseProvenance:
        return False
    if type(inventory.declaration_digest) is not ClassWorldReleaseDeclarationDigest:
        return False
    if (
        inventory.declaration_digest.algorithm
        != SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM
        or not _is_sha256_hex(inventory.declaration_digest.hex_digest)
    ):
        return False
    if type(inventory.artifacts) is not tuple:
        return False

    pins = inventory.declaration.provenance.package_pins
    if type(pins) is not tuple or len(inventory.artifacts) != len(pins):
        return False
    for artifact, pin in zip(inventory.artifacts, pins, strict=True):
        if type(pin) is not ClassWorldPackagePin:
            return False
        if type(artifact) is not ClassWorldPackageArtifactDeclaration:
            return False
        if artifact.package_id != pin.package_id or artifact.package_version != pin.package_version:
            return False
        if (
            artifact.digest_algorithm != SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM
            or not _is_sha256_hex(artifact.digest_hex)
        ):
            return False
    return True


def _canonical_input_bytes(inventory: ClassWorldArtifactInventory) -> bytes:
    payload = {
        "contract_version": SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION,
        "release_declaration_digest": {
            "algorithm": inventory.declaration_digest.algorithm,
            "hex_digest": inventory.declaration_digest.hex_digest,
        },
        "package_artifacts": [
            {
                "package_id": artifact.package_id,
                "package_version": artifact.package_version,
                "digest_algorithm": artifact.digest_algorithm,
                "digest_hex": artifact.digest_hex,
            }
            for artifact in inventory.artifacts
        ],
    }
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    return text.encode("utf-8")


def build_class_world_assembly_plan(
    inventory_result: ClassWorldArtifactInventoryResult,
) -> ClassWorldAssemblyPlanResult:
    """Compose one content-addressed plan from a successful artifact inventory.

    This boundary neither rebuilds the inventory nor reads artifact bytes. It
    preserves the upstream inventory by identity and hashes only a canonical
    projection of its already-declared content identities.
    """
    if inventory_result is None:
        return ClassWorldAssemblyPlanResult(
            plan=None,
            issues=(
                _issue(
                    ClassWorldAssemblyPlanIssueCode.INVENTORY_RESULT_REQUIRED,
                    "A class-world artifact inventory result is required.",
                    "inventory_result",
                ),
            ),
        )
    if type(inventory_result) is not ClassWorldArtifactInventoryResult:
        return ClassWorldAssemblyPlanResult(
            plan=None,
            issues=(
                _issue(
                    ClassWorldAssemblyPlanIssueCode.INVENTORY_RESULT_INVALID,
                    "inventory_result must be a class-world artifact inventory result.",
                    "inventory_result",
                ),
            ),
        )
    if (
        type(inventory_result.issues) is not tuple
        or inventory_result.issues
        or inventory_result.inventory is None
    ):
        return ClassWorldAssemblyPlanResult(
            plan=None,
            issues=(
                _issue(
                    ClassWorldAssemblyPlanIssueCode.INVENTORY_NOT_BUILT,
                    "inventory_result must contain one successfully built artifact inventory.",
                    "inventory_result",
                ),
            ),
        )
    if not _inventory_is_coherent(inventory_result.inventory):
        return ClassWorldAssemblyPlanResult(
            plan=None,
            issues=(
                _issue(
                    ClassWorldAssemblyPlanIssueCode.INVENTORY_INVALID,
                    "inventory_result.inventory must retain coherent canonical inventory output.",
                    "inventory_result.inventory",
                ),
            ),
        )

    inventory = inventory_result.inventory
    digest = hashlib.sha256(_canonical_input_bytes(inventory)).hexdigest()
    return ClassWorldAssemblyPlanResult(
        plan=ClassWorldAssemblyPlan(
            contract_version=SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION,
            inventory=inventory,
            input_digest=ClassWorldAssemblyInputDigest(
                algorithm=SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM,
                hex_digest=digest,
            ),
        ),
        issues=(),
    )
