"""Print the newest released version's section of CHANGELOG.md, for its GitHub release.

Usage: uv run python scripts/release_notes.py
"""

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"

changelog = CHANGELOG.read_text(encoding="utf-8")
# From the first numbered version heading to the next heading or the link list.
section = re.search(
    r"^## \[\d.*?\n(.*?)^(?:## )?\[", changelog, flags=re.MULTILINE | re.DOTALL
)
if section is None:
    sys.exit("CHANGELOG.md has no released version.")
print(section.group(1).strip())
