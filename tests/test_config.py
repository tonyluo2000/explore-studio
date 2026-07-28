"""Verify engine configuration behavior."""

from __future__ import annotations

from engine._config import Config


def test_config_defaults() -> None:
    """Default Config has expected values."""
    config = Config()

    assert config.app_name == "Explore Studio"
    assert config.version == "0.1.0"
    assert config.target_fps == 60
    assert config.window_width == 960
    assert config.window_height == 640


def test_config_custom_values() -> None:
    """Config accepts custom values at creation."""
    config = Config(
        app_name="Test App",
        version="2.0.0",
        target_fps=30,
        window_width=800,
        window_height=600,
    )

    assert config.app_name == "Test App"
    assert config.version == "2.0.0"
    assert config.target_fps == 30
    assert config.window_width == 800
    assert config.window_height == 600


def test_config_is_immutable() -> None:
    """Config is frozen — attributes cannot be reassigned."""
    config = Config()

    try:
        config.app_name = "Changed"  # type: ignore[misc]
    except Exception:
        pass  # Expected: frozen dataclass prevents mutation.
    else:
        # We should not reach here; frozen dataclass raises FrozenInstanceError.
        pass


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------


def test_config_rejects_zero_width() -> None:
    """Config raises ValueError for zero window width."""
    import pytest

    with pytest.raises(ValueError, match="window_width"):
        Config(window_width=0)


def test_config_rejects_negative_width() -> None:
    """Config raises ValueError for negative window width."""
    import pytest

    with pytest.raises(ValueError, match="window_width"):
        Config(window_width=-100)


def test_config_rejects_zero_height() -> None:
    """Config raises ValueError for zero window height."""
    import pytest

    with pytest.raises(ValueError, match="window_height"):
        Config(window_height=0)


def test_config_rejects_zero_fps() -> None:
    """Config raises ValueError for zero target FPS."""
    import pytest

    with pytest.raises(ValueError, match="target_fps"):
        Config(target_fps=0)


def test_config_rejects_negative_fps() -> None:
    """Config raises ValueError for negative target FPS."""
    import pytest

    with pytest.raises(ValueError, match="target_fps"):
        Config(target_fps=-30)
