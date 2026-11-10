import subprocess
import sys
from pathlib import Path

from vox_paginae.single_deed_input import (
    find_single_deed_folders,
    load_single_deed_input,
)

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fake_deed.py"


def test_fake_deed_opens_as_a_single_deed_folder_and_is_never_overwritten(tmp_path):
    def run():
        return subprocess.run(
            [sys.executable, SCRIPT, tmp_path],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )

    assert run().returncode == 0
    [folder] = find_single_deed_folders(tmp_path)
    assert folder.name == "1-1001"
    metadata = load_single_deed_input(folder)
    assert metadata["ref_reg"] == "1#1001"
    assert sorted(p.name for p in folder.glob("*.jpg")) == metadata["scans"]

    scans = {p.name: p.read_bytes() for p in folder.iterdir()}
    refused = run()
    assert refused.returncode != 0
    assert "exists" in refused.stderr
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == scans
