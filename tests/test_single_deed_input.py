import json

import pytest

from vox_paginae.annotation import deed_path, new_deed_record, save_deed_record
from vox_paginae.single_deed_input import (
    copied_deed_person_data,
    deed_choices,
    find_single_deed_folders,
    header_fields,
    load_single_deed_input,
)

METADATA = {
    "aktenummer": None,
    "ref_reg": "10#1399",
    "tax_office": "Westdorp",
    "deceased": {
        "full_name": "Jan Modaal",
        "profession": "bakker",
        "date_of_death": "2 januari 1880",
        "place_of_residence": "Oostdorp",
        "place_of_death": None,
    },
    "scans": ["scan-1.jpg"],
    "assets": {"total": None, "items": [{"amount": 900, "description": "Een huis"}]},
    "liabilities": {"total": None, "items": []},
    "total": 900,
}


def write_single_deed_folder(folder, metadata):
    """A single deed folder: ``input.json`` with ``metadata``, and one scan."""
    folder.mkdir(parents=True)
    (folder / "input.json").write_text(
        json.dumps({"metadata": metadata, "scans": []}), encoding="utf-8"
    )
    (folder / "scan-1.jpg").touch()


def test_single_deed_folders_are_found_in_file_browser_order(tmp_path):
    for name in ["10-1", "6-1", "6-12", "6-2", "drenthe/1-1"]:
        write_single_deed_folder(tmp_path / name, {"ref_reg": name.replace("-", "#")})
    (tmp_path / "no-input").mkdir()
    (tmp_path / "no-input" / "scan-1.jpg").touch()
    # Numbers in a name count as numbers: 6-2 before 6-12, 6-x before 10-1.
    assert [
        p.relative_to(tmp_path).as_posix() for p in find_single_deed_folders(tmp_path)
    ] == [
        "6-1",
        "6-2",
        "6-12",
        "10-1",
        "drenthe/1-1",
    ]


def test_copied_deed_person_data_is_the_deed_and_its_deceased_flat(tmp_path):
    write_single_deed_folder(tmp_path / "10-1399", METADATA)
    copied = copied_deed_person_data(load_single_deed_input(tmp_path / "10-1399"))
    # No assets, liabilities, scans or total: items come from the input itself (#88).
    assert copied == {
        "ref_reg": "10#1399",
        "aktenummer": None,
        "tax_office": "Westdorp",
        "full_name": "Jan Modaal",
        "profession": "bakker",
        "date_of_death": "2 januari 1880",
        "place_of_residence": "Oostdorp",
        "place_of_death": None,
    }
    assert header_fields(copied) == {
        "full_name": "Jan Modaal",
        "date_of_death": "2 januari 1880",
        "place_of_residence": "Oostdorp",
    }
    assert header_fields({"full_name": "Jan Modaal", "date_of_death": None}) == {
        "full_name": "Jan Modaal",
        "date_of_death": "",
        "place_of_residence": "",
    }


def test_an_input_without_ref_reg_names_its_folder(tmp_path):
    write_single_deed_folder(tmp_path / "6-1", {"deceased": {}})
    with pytest.raises(ValueError, match="6-1.*ref_reg"):
        load_single_deed_input(tmp_path / "6-1")


def test_deed_choices_are_ref_reg_and_name_with_pages_once_annotated(tmp_path):
    write_single_deed_folder(tmp_path / "6-1", {**METADATA, "ref_reg": "6#1"})
    write_single_deed_folder(
        tmp_path / "10-1", {"ref_reg": "10#1", "deceased": {"full_name": None}}
    )
    folders = find_single_deed_folders(tmp_path)
    assert deed_choices(folders) == {
        "6#1 · Jan Modaal": tmp_path / "6-1",
        "10#1": tmp_path / "10-1",
    }
    (tmp_path / "6-1" / "scan-2.jpg").touch()
    save_deed_record(
        deed_path(tmp_path / "6-1", "6#1"),
        {
            **new_deed_record("6#1", {}, "scan-1.jpg"),
            "scans": ["scan-1.jpg", "scan-2.jpg"],
        },
        "Ann",
    )
    # Pages counted from 1, as in the status line; the order stays.
    assert list(deed_choices(folders)) == ["6#1 · Jan Modaal · pages 1-2", "10#1"]
