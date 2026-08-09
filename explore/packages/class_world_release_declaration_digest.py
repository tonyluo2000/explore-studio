"""Deterministic SHA-256 digest computation for release declarations."""

from __future__ import annotations

import hashlib

from explore.packages.class_world_release_declaration_digest_models import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM,
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)
from explore.packages.class_world_release_declaration_serialization import (
    serialize_class_world_release_declaration,
)


def compute_class_world_release_declaration_digest(
    declaration: ClassWorldReleaseDeclaration,
) -> ClassWorldReleaseDeclarationDigest:
    """Compute SHA-256 over the canonical serialized declaration UTF-8 bytes.

    The canonical serializer is the sole byte authority. Its exact output,
    including its final newline, is encoded as UTF-8 and hashed in memory.

    Raises:
        TypeError: If *declaration* is not a ``ClassWorldReleaseDeclaration``.
        ValueError: If *declaration* is inconsistent with its configuration.
    """
    canonical_text = serialize_class_world_release_declaration(declaration)
    canonical_bytes = canonical_text.encode("utf-8")
    return ClassWorldReleaseDeclarationDigest(
        algorithm=SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM,
        hex_digest=hashlib.sha256(canonical_bytes).hexdigest(),
    )
