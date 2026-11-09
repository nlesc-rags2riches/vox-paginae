import json

import pytest

from vox_paginae.annotation import (
    add_item,
    deed_path,
    new_deed_record,
    save_deed_record,
)
from vox_paginae.single_deed_input import (
    copied_deed_person_data,
    deed_choices,
    find_single_deed_folders,
    header_fields,
    input_item_choices,
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


def test_deed_choices_keep_two_folders_with_the_same_label(tmp_path):
    for name in ["6-1", "copy/6-1"]:
        write_single_deed_folder(tmp_path / name, {"ref_reg": "6#1"})
    # The later one gets its folder: none goes missing from the list.
    assert deed_choices(find_single_deed_folders(tmp_path)) == {
        "6#1": tmp_path / "6-1",
        f"6#1 · {tmp_path / 'copy' / '6-1'}": tmp_path / "copy" / "6-1",
    }


def input_with_items(assets, liabilities):
    return {
        "ref_reg": "10#1399",
        "assets": {"total": None, "items": assets},
        "liabilities": {"total": None, "items": liabilities},
    }


def test_input_item_choices_list_the_input_items_with_type_amount_and_description():
    single_deed_input = input_with_items(
        [
            {"amount": 900, "description": "Een huis"},
            {"amount": None, "description": " Een stoel "},
        ],
        [{"amount": "12,50", "description": None}],
    )
    # Numbered so two equal items stay apart. Amounts become strings, as typed ones.
    assert input_item_choices(single_deed_input, None) == {
        "1 · assets · 900 · Een huis": {
            "type": "assets",
            "amount": "900",
            "description": "Een huis",
        },
        "2 · assets ·  · Een stoel": {
            "type": "assets",
            "amount": "",
            "description": "Een stoel",
        },
        "3 · liabilities · 12,50 · ": {
            "type": "liabilities",
            "amount": "12,50",
            "description": "",
        },
    }


def test_input_item_choices_are_empty_when_the_input_has_no_items():
    assert input_item_choices(input_with_items([], []), None) == {}
    assert input_item_choices({"ref_reg": "10#1399", "assets": None}, None) == {}


def with_items(*items):
    """A deed record with ``items``: ``(type, amount, description)`` each."""
    deed_record = new_deed_record("10#1399", {}, "scan-1.jpg")
    for type_, amount, description in items:
        deed_record = add_item(
            deed_record, type_, "", amount, description, [("scan-1.jpg", [0, 0, 1, 1])]
        )
    return deed_record


def test_a_saved_input_item_goes_last_marked_picked():
    single_deed_input = input_with_items(
        [
            {"amount": 900, "description": "Een huis"},
            {"amount": 5, "description": "Een stoel"},
        ],
        [],
    )
    deed_record = with_items(("assets", "900", "Een huis"))
    assert list(input_item_choices(single_deed_input, deed_record)) == [
        "2 · assets · 5 · Een stoel",
        "1 · assets · 900 · Een huis · picked",
    ]


def picked_labels(single_deed_input, deed_record):
    return [
        label
        for label in input_item_choices(single_deed_input, deed_record)
        if label.endswith(" · picked")
    ]


def test_an_input_item_corrected_in_one_field_still_counts_as_picked():
    single_deed_input = input_with_items(
        [
            {"amount": 900, "description": "Een huis"},
            {"amount": 5, "description": "Een stoel"},
            {"amount": 7, "description": "Een tafel"},
        ],
        [{"amount": 12, "description": "Schuld"}],
    )
    deed_record = with_items(
        ("assets", "900", "Een huis met erf"),  # description corrected
        ("assets", "6", "Een stoel"),  # amount corrected
        ("assets", "8", "Twee tafels"),  # both corrected: not recognised
        ("assets", "12", "Schuld"),  # type corrected: not recognised
    )
    assert picked_labels(single_deed_input, deed_record) == [
        "1 · assets · 900 · Een huis · picked",
        "2 · assets · 5 · Een stoel · picked",
    ]


def test_each_saved_item_marks_at_most_one_input_item_preferring_an_exact_match():
    single_deed_input = input_with_items(
        [
            {"amount": 100, "description": "Een stoel"},
            {"amount": 100, "description": "Een tafel"},
            {"amount": 100, "description": "Een tafel"},
        ],
        [],
    )
    # Equal on amount to all three, but exactly equal to the second only.
    assert picked_labels(
        single_deed_input, with_items(("assets", "100", "Een tafel"))
    ) == ["2 · assets · 100 · Een tafel · picked"]


def test_blank_fields_do_not_count_as_equal():
    single_deed_input = input_with_items(
        [{"amount": None, "description": "Een huis"}], []
    )
    assert (
        picked_labels(single_deed_input, with_items(("assets", "", "Een stoel"))) == []
    )


def test_a_long_description_is_cut_in_the_label_but_kept_whole_in_the_item():
    description = "Een huis met erf en tuin aan de Kerkstraat te Oostdorp"
    single_deed_input = input_with_items(
        [{"amount": 900, "description": description}], []
    )
    # As in the item dropdown: 30 characters, so the dropdown stays narrow.
    assert input_item_choices(single_deed_input, None) == {
        "1 · assets · 900 · Een huis met erf en tuin aan d…": {
            "type": "assets",
            "amount": "900",
            "description": description,
        }
    }
