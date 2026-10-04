"""Course-owned trusted audio catalog.

The audio twin of ``_trusted_art``: only sounds listed in
``trusted_audio/manifest.json`` can be read, only from inside that directory,
and only when their bytes match the recorded SHA-256 digest. Anything
missing, malformed, tampered with, or outside the directory reads as
unavailable (``None``), so the Trail simply stays silent for that cue.

The sounds are synthesized in-repo by ``scripts/build_trail_audio.py``.
This module is pure Python: it never imports Pygame and never decodes audio.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_LOGGER = logging.getLogger("explore-studio.assets.trusted-audio")

#: Directory that ships inside the ``engine`` distribution package.
TRUSTED_AUDIO_ROOT: Final = Path(__file__).resolve().parent / "trusted_audio"
MANIFEST_NAME: Final = "manifest.json"
SUPPORTED_MANIFEST_SCHEMA: Final = 1


@dataclass(frozen=True)
class SoundSpec:
    """One manifest entry: a PCM WAV file and its recorded format."""

    asset_id: str
    file: str
    sha256: str
    sample_rate: int
    channels: int
    sample_width: int
    frames: int
    loop: bool

    @property
    def duration(self) -> float:
        return self.frames / self.sample_rate


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _parse_entry(asset_id: str, entry: object) -> SoundSpec:
    if not isinstance(entry, dict):
        raise ValueError("asset entries must be objects")
    file = entry.get("file")
    digest = entry.get("sha256")
    loop = entry.get("loop", False)
    if not isinstance(file, str) or not file.endswith(".wav"):
        raise ValueError("asset file must be a .wav path")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("asset sha256 must be 64 lowercase hex characters")
    if not isinstance(loop, bool):
        raise ValueError("loop must be true or false")
    return SoundSpec(
        asset_id=asset_id,
        file=file,
        sha256=digest,
        sample_rate=_positive_int(entry.get("sample_rate"), "sample_rate"),
        channels=_positive_int(entry.get("channels"), "channels"),
        sample_width=_positive_int(entry.get("sample_width"), "sample_width"),
        frames=_positive_int(entry.get("frames"), "frames"),
        loop=loop,
    )


class TrustedAudioCatalog:
    """Read-only, digest-verified access to course-owned sounds."""

    def __init__(self, root: Path = TRUSTED_AUDIO_ROOT) -> None:
        self._root = Path(root)
        self._specs: dict[str, SoundSpec] | None = None

    @property
    def root(self) -> Path:
        return self._root

    def _load_manifest(self) -> dict[str, SoundSpec]:
        if self._specs is not None:
            return self._specs
        specs: dict[str, SoundSpec] = {}
        try:
            raw = json.loads((self._root / MANIFEST_NAME).read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("schema_version") != SUPPORTED_MANIFEST_SCHEMA:
                raise ValueError("unsupported trusted audio manifest schema")
            assets = raw.get("assets")
            if not isinstance(assets, dict):
                raise ValueError("manifest assets must be an object")
            for asset_id, entry in sorted(assets.items()):
                specs[asset_id] = _parse_entry(asset_id, entry)
        except (OSError, ValueError) as error:
            _LOGGER.warning("Trusted audio manifest unavailable (%s); staying silent", error)
            specs = {}
        self._specs = specs
        return specs

    def spec(self, asset_id: str) -> SoundSpec | None:
        """Return the manifest entry for *asset_id*, or ``None``."""
        return self._load_manifest().get(asset_id)

    def asset_ids(self) -> tuple[str, ...]:
        return tuple(self._load_manifest())

    def read_verified(self, asset_id: str) -> bytes | None:
        """Return the sound's bytes only when they match the recorded digest."""
        spec = self.spec(asset_id)
        if spec is None:
            return None
        root = self._root.resolve()
        path = (root / spec.file).resolve()
        if not path.is_relative_to(root):
            _LOGGER.warning("Trusted audio %s points outside the trusted directory", asset_id)
            return None
        try:
            data = path.read_bytes()
        except OSError as error:
            _LOGGER.warning("Trusted audio %s is unavailable (%s)", asset_id, error)
            return None
        if hashlib.sha256(data).hexdigest() != spec.sha256:
            _LOGGER.warning("Trusted audio %s failed its digest check", asset_id)
            return None
        return data
