"""Fixed S28 integration fixture paths and golden evidence. Students do not edit."""

from pathlib import Path

FIXTURE_ROOT = Path(__file__).parent / "fixtures"
VALID_SOURCE = FIXTURE_ROOT / "valid-plan.yaml"
CORRUPT_SOURCE = FIXTURE_ROOT / "corrupt-plan.yaml"
INVALID_SOURCE = FIXTURE_ROOT / "invalid-plan.yaml"
UNSAFE_ID_SOURCE = FIXTURE_ROOT / "unsafe-id-plan.yaml"

GOLDEN_FILE_LIST = (
    "manifest.yaml",
    "objects/echo-lens.yaml",
    "objects/wind-dial.yaml",
    "objects/comet-bell.yaml",
    "character/sky-guide.yaml",
)
EXPECTED_ROUTE_IDS = ("echo-lens", "wind-dial", "comet-bell")
EXPECTED_STYLE_ID = "observatory-glow"
EXPECTED_STYLED_IDS = ("echo-lens", "wind-dial")
