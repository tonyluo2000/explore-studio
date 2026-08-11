"""Immutable model for release-declaration file digest verification v0.1."""

from __future__ import annotations

from dataclasses import dataclass

from explore.packages.class_world_release_declaration_digest_verification_models import (
    ClassWorldReleaseDeclarationDigestVerificationResult,
)
from explore.packages.class_world_release_declaration_file_transport_models import (
    ClassWorldReleaseDeclarationFileIssue,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationIssue,
)
from explore.packages.class_world_release_declaration_serialization_models import (
    ClassWorldReleaseDeclarationSerializationIssue,
)

SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION = "0.1"


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationFileDigestVerificationResult:
    """One declaration read result with optional digest verification state."""

    declaration: ClassWorldReleaseDeclaration | None
    verification: ClassWorldReleaseDeclarationDigestVerificationResult | None
    issues: tuple[ClassWorldReleaseDeclarationFileIssue, ...]
    serialization_issues: tuple[ClassWorldReleaseDeclarationSerializationIssue, ...]
    declaration_issues: tuple[ClassWorldReleaseDeclarationIssue, ...]
