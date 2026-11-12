"""The deed annotation file's format, pinned by snapshots, one folder per format version.

A test here fails when the file changes. If the change is meant, add a folder named
after the new version and bump ``FORMAT_VERSION``: see the reference's Format versions.
"""

import re
from pathlib import Path

from vox_paginae.annotation import (
    FORMAT_VERSION,
    add_balance_box,
    add_header_box,
    add_item,
    close_deed_record,
    deed_path,
    new_deed_record,
    save_deed_record,
    set_balance_totals,
    set_header_fields,
)

SNAPSHOTS = Path(__file__).parent / "format_snapshots"
COPIED = {"aktenummer": "93", "plaats": "Westdorp", "naam_volledig": "Jan Modaal"}


def snapshot_versions() -> list[str]:
    """Every snapshot folder's version, oldest first: ``0.10.0`` comes after ``0.9.0``."""
    return sorted(
        (path.name for path in SNAPSHOTS.iterdir() if path.is_dir()),
        key=lambda version: [int(part) for part in version.split(".")],
    )


def filled_deed_record() -> dict:
    """A closed deed with every part filled in: header, balance, an asset, a liability."""
    deed_record = new_deed_record("filled", COPIED, "p1.jpg")
    deed_record = add_header_box(deed_record, "p1.jpg", [300, 120, 2400, 520])
    deed_record = set_header_fields(
        deed_record, "Jan Modaal", "2 januari 1880", "Oostdorp"
    )
    deed_record = add_item(
        deed_record,
        "assets",
        "900,-",
        "Een huis met erf,\nŐdön",  # not ASCII: written as is, not escaped
        [("p1.jpg", [412, 1880, 2310, 2240]), ("p2.jpg", [380, 210, 2290, 420])],
    )
    deed_record = add_item(
        deed_record, "liabilities", "10,-", "", [("p2.jpg", [0, 0, 9, 9])]
    )
    deed_record = set_balance_totals(deed_record, "900,-", "10,-", "890,-")
    deed_record = add_balance_box(deed_record, "p3.jpg", [400, 2600, 2300, 3000])
    return close_deed_record(
        deed_record, ["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg"], "p2.jpg"
    )


def test_the_deed_annotation_files_match_the_newest_snapshots(tmp_path):
    save_deed_record(deed_path(tmp_path, "filled"), filled_deed_record(), "Ann")
    # Just opened: the empty header, balance and item lists, as written.
    save_deed_record(
        deed_path(tmp_path, "empty"), new_deed_record("empty", COPIED, "p1.jpg"), "Ann"
    )

    def files(folder: Path) -> dict[str, str]:
        # The time of the write is the one value that changes from run to run.
        return {
            path.name: re.sub(
                r'"annotation_date": "[^"]*"',
                '"annotation_date": "<time of the write>"',
                path.read_text(encoding="utf-8"),
            )
            for path in folder.iterdir()
        }

    # Names and contents: a renamed file fails too.
    assert files(tmp_path) == files(SNAPSHOTS / snapshot_versions()[-1])


def test_the_tool_writes_the_newest_snapshots_version():
    assert FORMAT_VERSION == snapshot_versions()[-1]
