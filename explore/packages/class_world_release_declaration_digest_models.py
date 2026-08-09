"""Immutable model for release-declaration digest v0.1."""

from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION = "0.1"
SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM = "sha256"


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationDigest:
    """SHA-256 identity of one canonical serialized release declaration."""

    algorithm: str
    hex_digest: str
