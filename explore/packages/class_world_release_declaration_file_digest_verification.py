"""Read and verify one release declaration through existing contracts."""

from __future__ import annotations

from pathlib import Path

from explore.packages.class_world_configuration_models import ClassWorldConfiguration
from explore.packages.class_world_release_declaration_digest_models import (
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_digest_verification import (
    verify_class_world_release_declaration_digest,
)
from explore.packages.class_world_release_declaration_file_digest_verification_models import (
    ClassWorldReleaseDeclarationFileDigestVerificationResult,
)
from explore.packages.class_world_release_declaration_file_transport import (
    read_class_world_release_declaration_file,
)


def verify_class_world_release_declaration_file_digest(
    path: str | Path,
    configuration: ClassWorldConfiguration,
    expected_digest: ClassWorldReleaseDeclarationDigest,
) -> ClassWorldReleaseDeclarationFileDigestVerificationResult:
    """Read one declaration first, then verify its canonical declaration digest.

    Reader failures take precedence and preserve all existing reader diagnostics.
    Expected-digest validation therefore occurs only after a successful read.
    """
    read_result = read_class_world_release_declaration_file(path, configuration)
    if not read_result.is_read:
        return ClassWorldReleaseDeclarationFileDigestVerificationResult(
            declaration=read_result.declaration,
            verification=None,
            issues=read_result.issues,
            serialization_issues=read_result.serialization_issues,
            declaration_issues=read_result.declaration_issues,
        )

    assert read_result.declaration is not None
    verification = verify_class_world_release_declaration_digest(
        read_result.declaration,
        expected_digest,
    )
    return ClassWorldReleaseDeclarationFileDigestVerificationResult(
        declaration=read_result.declaration,
        verification=verification,
        issues=read_result.issues,
        serialization_issues=read_result.serialization_issues,
        declaration_issues=read_result.declaration_issues,
    )
