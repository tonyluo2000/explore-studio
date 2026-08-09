"""Immutable model for release-declaration digest verification v0.1."""

from __future__ import annotations

from dataclasses import dataclass

from explore.packages.class_world_release_declaration_digest_models import (
    ClassWorldReleaseDeclarationDigest,
)

SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION = "0.1"


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationDigestVerificationResult:
    """Expected and recomputed declaration digests with their equality result."""

    expected_digest: ClassWorldReleaseDeclarationDigest
    actual_digest: ClassWorldReleaseDeclarationDigest
    matches: bool
