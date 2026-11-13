import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_notes_are_one_version_section_without_headings_or_links():
    notes = subprocess.run(
        [sys.executable, ROOT / "scripts" / "release_notes.py"],
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert notes
    assert notes in changelog
    assert not re.search(r"^(## )?\[", notes, flags=re.MULTILINE)
