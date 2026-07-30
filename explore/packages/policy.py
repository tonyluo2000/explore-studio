"""Named prototype policy constants for Explorer Package contract v0.1."""

from __future__ import annotations

import re

SUPPORTED_SCHEMA_VERSION = "0.1"
SUPPORTED_STUDENT_API_VERSION = "0.1"

IDENTIFIER_MAX_LENGTH = 64
DISPLAY_NAME_MAX_LENGTH = 100
MAX_ASSET_SIZE_BYTES = 5 * 1024 * 1024

CONTRIBUTION_FILE_EXTENSIONS: dict[str, frozenset[str]] = {
    "character": frozenset({".yaml", ".yml"}),
    "world_object": frozenset({".yaml", ".yml"}),
}

ASSET_FILE_EXTENSIONS: dict[str, frozenset[str]] = {
    "audio": frozenset({".wav"}),
    "image": frozenset({".png"}),
}

_IDENTIFIER_PATTERN = re.compile(r"[a-z](?:[a-z0-9]|-(?!-))*", re.ASCII)
_SEMANTIC_VERSION_PATTERN = re.compile(
    r"""
    (0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)
    (?:-
        (
            (?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)
            (?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*
        )
    )?
    (?:\+
        (
            [0-9A-Za-z-]+
            (?:\.[0-9A-Za-z-]+)*
        )
    )?
    """,
    re.ASCII | re.VERBOSE,
)


def is_valid_identifier(value: str) -> bool:
    """Return whether *value* follows the v0.1 lower-kebab-case policy."""
    return (
        len(value) <= IDENTIFIER_MAX_LENGTH
        and _IDENTIFIER_PATTERN.fullmatch(value) is not None
        and not value.endswith("-")
    )


def is_valid_semantic_version(value: str) -> bool:
    """Return whether *value* is a Semantic Versioning 2.0.0 version."""
    return _SEMANTIC_VERSION_PATTERN.fullmatch(value) is not None
