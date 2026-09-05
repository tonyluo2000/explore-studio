"""Local contract test for the student's declarative Explorer Package."""

from pathlib import Path

from explore.packages import load_explorer_package


def test_explorer_package_loads() -> None:
    package_root = Path(__file__).parents[1] / "explorer-package"

    result = load_explorer_package(package_root)

    assert result.is_loaded
    assert result.package is not None
    assert result.package.metadata.id == "student-beacon"
    assert result.package.metadata.version == "1.0.0"
    assert len(result.package.contributions) == 1
