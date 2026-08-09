"""Pure in-memory verification of a release-declaration digest."""

from __future__ import annotations

from explore.packages.class_world_release_declaration_digest import (
    compute_class_world_release_declaration_digest,
)
from explore.packages.class_world_release_declaration_digest_models import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM,
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_digest_verification_models import (
    ClassWorldReleaseDeclarationDigestVerificationResult,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)

_LOWERCASE_HEXADECIMAL_CHARACTERS = frozenset("0123456789abcdef")


def _validate_expected_digest(
    expected_digest: ClassWorldReleaseDeclarationDigest,
) -> None:
    if not isinstance(expected_digest, ClassWorldReleaseDeclarationDigest):
        raise TypeError("expected_digest must be a ClassWorldReleaseDeclarationDigest.")
    if (
        not isinstance(expected_digest.algorithm, str)
        or expected_digest.algorithm != SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM
    ):
        raise ValueError('expected_digest.algorithm must be exactly "sha256".')
    if not isinstance(expected_digest.hex_digest, str):
        raise ValueError("expected_digest.hex_digest must be a string.")
    if len(expected_digest.hex_digest) != 64 or any(
        character not in _LOWERCASE_HEXADECIMAL_CHARACTERS
        for character in expected_digest.hex_digest
    ):
        raise ValueError(
            "expected_digest.hex_digest must be exactly 64 lowercase hexadecimal characters."
        )


def verify_class_world_release_declaration_digest(
    declaration: ClassWorldReleaseDeclaration,
    expected_digest: ClassWorldReleaseDeclarationDigest,
) -> ClassWorldReleaseDeclarationDigestVerificationResult:
    """Recompute and compare one declaration digest with validated expected input.

    Expected-input validation completes before declaration digest computation.
    A well-formed unequal digest returns a result whose matches value is false
    rather than raising an exception.

    Raises:
        TypeError: If either input has the wrong programmer-level type.
        ValueError: If the expected digest is malformed or the declaration is
            inconsistent with its authoritative configuration.
    """
    _validate_expected_digest(expected_digest)
    actual_digest = compute_class_world_release_declaration_digest(declaration)
    return ClassWorldReleaseDeclarationDigestVerificationResult(
        expected_digest=expected_digest,
        actual_digest=actual_digest,
        matches=expected_digest == actual_digest,
    )
