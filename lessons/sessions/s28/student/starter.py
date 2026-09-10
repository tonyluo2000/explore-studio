"""S28 thin entry point for the intentionally incomplete integration boundary."""

import sys
from pathlib import Path

if __package__ in (None, ""):  # Supports running this file directly.
    sys.path.insert(0, str(Path(__file__).parents[4]))

from lessons.sessions.s28.student.integration import SOURCE_PLAN_PATH, load_plan


def main():
    plan = load_plan(SOURCE_PLAN_PATH)
    print("S28 integration scaffold ready")
    print("Loaded project:", plan["name"])
    print("Complete the TODO boundaries before generating package files.")


if __name__ == "__main__":
    main()
