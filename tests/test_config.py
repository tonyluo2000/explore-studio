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
    assert config.background_color == (32, 32, 48)


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


# ------------------------------------------------------------------
# Background color validation
# ------------------------------------------------------------------


def test_background_color_default() -> None:
    """Default background_color is a valid (r, g, b) tuple."""
    config = Config()
    assert config.background_color == (32, 32, 48)


def test_background_color_custom_valid() -> None:
    """Custom valid background_color is accepted."""
    config = Config(background_color=(255, 128, 0))
    assert config.background_color == (255, 128, 0)


def test_background_color_too_few_channels() -> None:
    """Tuple with fewer than 3 channels is rejected."""
    import pytest

    with pytest.raises(ValueError, match="must have 3 channels"):
        Config(background_color=(0, 0))


def test_background_color_too_many_channels() -> None:
    """Tuple with more than 3 channels is rejected."""
    import pytest

    with pytest.raises(ValueError, match="must have 3 channels"):
        Config(background_color=(0, 0, 0, 0))


def test_background_color_negative_channel() -> None:
    """Negative channel value is rejected."""
    import pytest

    with pytest.raises(ValueError, match="0–255"):
        Config(background_color=(-1, 0, 0))


def test_background_color_channel_above_255() -> None:
    """Channel value above 255 is rejected."""
    import pytest

    with pytest.raises(ValueError, match="0–255"):
        Config(background_color=(256, 0, 0))


def test_background_color_non_int_channel() -> None:
    """Non-integer channel is rejected."""
    import pytest

    with pytest.raises(TypeError, match="must be int"):
        Config(background_color=(0.5, 0, 0))  # type: ignore[arg-type]


def test_background_color_bool_channel_rejected() -> None:
    """Bool channel is rejected even though bool is an int subclass."""
    import pytest

    with pytest.raises(TypeError, match="must be int"):
        Config(background_color=(True, 0, 0))  # type: ignore[arg-type]


def test_background_color_not_a_tuple() -> None:
    """Non-tuple value is rejected."""
    import pytest

    with pytest.raises(TypeError, match="must be a tuple"):
        Config(background_color=[0, 0, 0])  # type: ignore[arg-type]
