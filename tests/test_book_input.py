import json

import pytest

from vox_paginae.annotation import deed_path, new_deed_record, save_deed_record
from vox_paginae.book_input import (
    copied_deed_person_data,
    deed_choices,
    load_deeds,
    single_overledene,
)

DEED = {
    "deed_id": "d1",
    "aktenummer": "93",
    "plaats": "Westdorp",
    "personen": [
        {
            "person_id": "p1",
            "naam_volledig": "Jan Modaal",
            "datum_overlijden": "1880-01-02",
            "plaats_overlijden": "Oostdorp",
            "rol": "overledene",
        }
    ],
}


def test_copied_deed_person_data_is_the_deed_and_its_overledene_flat_without_rol():
    assert copied_deed_person_data(DEED) == {
        "aktenummer": "93",
        "plaats": "Westdorp",
        "person_id": "p1",
        "naam_volledig": "Jan Modaal",
        "datum_overlijden": "1880-01-02",
        "plaats_overlijden": "Oostdorp",
    }
    with pytest.raises(ValueError, match="2 deed persons"):
        copied_deed_person_data({**DEED, "personen": DEED["personen"] * 2})


def test_deed_choices_sort_by_aktenummer_then_place_files_last(tmp_path):
    def deed(deed_id, aktenummer, plaats, name):
        return {
            "deed_id": deed_id,
            "aktenummer": aktenummer,
            "plaats": plaats,
            "personen": [{"naam_volledig": name, "rol": "overledene"}],
        }

    assert load_deeds(tmp_path) is None
    (tmp_path / "deeds.json").write_text(
        json.dumps(
            [
                deed("d1", "93", "Westdorp", "B"),
                deed("d2", "105", "Alphen", "C"),
                deed("d3", "93", "Oostdorp", "A"),
            ]
        ),
        encoding="utf-8",
    )
    deeds = load_deeds(tmp_path)
    assert list(deeds) == ["d1", "d2", "d3"]
    assert deed_choices(deeds, tmp_path) == {
        "93 · Oostdorp · A": "d3",
        "93 · Westdorp · B": "d1",
        "105 · Alphen · C": "d2",
    }
    # Deeds with a file go last, with their pages (from 1, as in the status line).
    for name in ["a.jpg", "b.jpg", "c.jpg"]:
        (tmp_path / name).touch()
    save_deed_record(
        deed_path(tmp_path, "d3"), new_deed_record("d3", {}, "b.jpg", [0] * 4), "Ann"
    )
    save_deed_record(
        deed_path(tmp_path, "d2"),
        {
            **new_deed_record("d2", {}, "a.jpg", [0] * 4),
            "scans": ["a.jpg", "b.jpg", "c.jpg"],
        },
        "Ann",
    )
    assert list(deed_choices(deeds, tmp_path).items()) == [
        ("93 · Westdorp · B", "d1"),
        ("93 · Oostdorp · A · page 2", "d3"),
        ("105 · Alphen · C · pages 1-3", "d2"),
    ]


def test_load_deeds_reads_utf8_whatever_the_system_default(tmp_path):
    # Outside cp1252 (Windows' default) and Latin-1: only UTF-8 holds them.
    deed = {**DEED, "plaats": "Ődön Şahin ‐ Łódź"}
    (tmp_path / "deeds.json").write_bytes(
        json.dumps([deed], ensure_ascii=False).encode("utf-8")
    )
    assert load_deeds(tmp_path) == {"d1": deed}


@pytest.mark.parametrize(
    "personen, error",
    [
        ([], "has 0 deed persons"),
        ([{"rol": "overledene"}, {"rol": "erfgenaam"}], "has 2 deed persons"),
        ([{"rol": "erfgenaam"}], "Its one deed person has `rol: erfgenaam`"),
    ],
)
def test_single_overledene_rejects_a_deed_without_exactly_one(personen, error):
    with pytest.raises(ValueError, match=error):
        single_overledene({"personen": personen})


def test_single_overledene_returns_the_one_deed_person():
    overledene = {"naam_volledig": "Jan Modaal", "rol": "overledene"}
    assert single_overledene({"personen": [overledene]}) is overledene
