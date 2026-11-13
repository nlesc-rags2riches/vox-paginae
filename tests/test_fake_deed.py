import subprocess
import sys
from pathlib import Path

from vox_paginae.single_deed_input import (
    find_single_deed_folders,
    load_single_deed_input,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fake_deed.py"


def test_fake_deeds_open_as_single_deed_folders_and_are_never_overwritten(tmp_path):
    def run():
        return subprocess.run(
            [sys.executable, SCRIPT, tmp_path],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

    assert run().returncode == 0
    folders = find_single_deed_folders(tmp_path)
    assert [folder.name for folder in folders] == ["1-1001", "1-1002"]
    for folder in folders:
        metadata = load_single_deed_input(folder)
        assert metadata["ref_reg"] == folder.name.replace("-", "#")
        assert sorted(p.name for p in folder.glob("*.jpg")) == metadata["scans"]
    # 1#1002 has an item that runs from scan 2 onto scan 3.
    assert len(load_single_deed_input(folders[1])["scans"]) == 3

    files = {p: p.read_bytes() for p in tmp_path.glob("*/*")}
    refused = run()
    assert refused.returncode != 0
    assert "exists" in refused.stderr
    assert {p: p.read_bytes() for p in tmp_path.glob("*/*")} == files
