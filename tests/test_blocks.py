import json
from datetime import UTC, datetime

import pytest

# TODO: Together with the `src` correspondent, split and human-review
from vox_paginae.blocks import (
    add_block,
    block_labels,
    clear_balance,
    close_deed_record,
    deed_boxes,
    deed_choices,
    delete_block,
    find_books,
    list_pages,
    load_deed_records,
    load_deeds,
    new_deed_record,
    next_page,
    replace_block,
    resume,
    save_deed_record,
    saved_boxes,
    set_balance,
    set_header,
    single_overledene,
)


def test_next_page_crosses_books_and_stops_when_done():
    counts = [2, 1]
    assert next_page((0, 0), counts) == (0, 1)
    assert next_page((0, 1), counts) == (1, 0)
    assert next_page((1, 0), counts) == (2, 0)
    assert next_page((2, 0), counts) == (2, 0)


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


def test_new_deed_record_copies_the_deed_and_starts_on_the_header_box():
    assert new_deed_record(DEED, "p2.jpg", [1, 2.4, 30, 40]) == {
        "deed_id": "d1",
        "copied_deed_person_data": {
            "aktenummer": "93",
            "plaats": "Westdorp",
            "person_id": "p1",
            "naam_volledig": "Jan Modaal",
            "datum_overlijden": "1880-01-02",
            "plaats_overlijden": "Oostdorp",
        },
        "scans": ["p2.jpg"],
        "annotation_metadata": {"annotator_name": None, "annotation_date": None},
        "annotation": {
            "header": {
                "scan": "p2.jpg",
                "bbox": [1, 2, 30, 40],
                "pagexml_link": None,
                "pagexml_baseline_ids": None,
            },
            "balance": None,  # optional: none until one is saved
            "assets": [],
            "liabilities": [],
        },
    }


def test_blocks_go_into_the_annotation_and_leave_scans_alone():
    p = new_deed_record(DEED, "p2.jpg", [0] * 4)
    p = add_block(p, "assets", "", "900,-", "huis", [("p2.jpg", [1, 2, 3, 4])])
    p = add_block(
        p,
        "assets",
        "cash",
        "1,-",
        "",
        [("p1.jpg", [0, 0, 5, 5]), ("p4.jpg", [0, 0, 5, 5])],
    )
    p = add_block(p, "liabilities", "", "10", "schuld", [("p3.jpg", [0, 0, 9, 9])])
    assert [label for label, _ in block_labels(p)] == ["A1", "A2", "L1"]
    assert block_labels(None) == []  # no current deed/person
    assert p["annotation"]["liabilities"] == [
        {
            "layout": [
                {
                    "scan": "p3.jpg",
                    "bbox": [0, 0, 9, 9],
                    "pagexml_link": None,
                    "pagexml_baseline_ids": None,
                }
            ],
            "category": None,
            "amount": "10",
            "description": "schuld",
        }
    ]
    assert p["annotation"]["assets"][1]["category"] == "cash"
    # The header page is fixed at open: a box on an earlier page does not move it.
    assert p["scans"] == ["p2.jpg"]

    q = delete_block(p, "A2")
    assert [label for label, _ in block_labels(q)] == ["A1", "L1"]
    q = delete_block(delete_block(q, "A1"), "L1")
    assert (q["annotation"]["assets"], q["annotation"]["liabilities"]) == ([], [])
    assert q["scans"] == ["p2.jpg"]
    assert len(p["annotation"]["assets"]) == 2  # originals untouched


def test_balance_is_one_optional_box_with_three_totals_as_typed():
    p = new_deed_record(DEED, "p2.jpg", [0] * 4)
    q = set_balance(p, "p3.jpg", [1, 2.6, 30, 40], " 1.000,- ", "", "f 900")
    assert q["annotation"]["balance"] == {
        "layout": {
            "scan": "p3.jpg",
            "bbox": [1, 2, 30, 40],
            "pagexml_link": None,
            "pagexml_baseline_ids": None,
        },
        "total_assets": " 1.000,- ",
        "total_liabilities": "",
        "total": "f 900",
    }
    assert [label for label, _ in deed_boxes(q)] == ["H", "B"]
    assert p["annotation"]["balance"] is None  # original untouched
    with pytest.raises(ValueError):  # at most one
        set_balance(q, "p2.jpg", [0, 0, 5, 5], "1", "", "")
    with pytest.raises(ValueError):  # at least one total
        set_balance(p, "p2.jpg", [0, 0, 5, 5], " ", "", "")
    # Cleared, it can be saved again.
    assert clear_balance(q) == p
    assert set_balance(clear_balance(q), "p2.jpg", [0, 0, 5, 5], "1", "", "")


def test_replace_block_keeps_position_unless_type_changes():
    box = [("p1.jpg", [0, 0, 5, 5])]
    p = new_deed_record(DEED, "p1.jpg", [0] * 4)
    for amount in ["1", "2", "3"]:
        p = add_block(p, "assets", "", amount, "", box)
    p = replace_block(p, "A2", "assets", "cash", "20", "", [("p2.jpg", [1, 1, 9, 9])])
    items = p["annotation"]["assets"]
    assert [i["amount"] for i in items] == ["1", "20", "3"]  # A2 stays A2
    assert items[1]["category"] == "cash"
    assert p["scans"] == ["p1.jpg"]
    # A type change moves it to the end of the other type.
    p = replace_block(p, "A1", "liabilities", "", "1", "", box)
    assert [label for label, _ in block_labels(p)] == ["A1", "A2", "L1"]
    with pytest.raises(ValueError):  # same checks as add_block
        replace_block(p, "A1", "assets", "", "", "", box)


def test_set_header_moves_the_header_page_and_scans_with_it():
    page_names = ["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg"]
    p = close_deed_record(
        new_deed_record(DEED, "p2.jpg", [0] * 4), page_names, "p3.jpg"
    )
    q = set_header(p, page_names, "p1.jpg", [1, 2, 3, 4])
    assert q["annotation"]["header"]["scan"] == "p1.jpg"
    assert q["annotation"]["header"]["bbox"] == [1, 2, 3, 4]
    assert q["scans"] == ["p1.jpg", "p2.jpg", "p3.jpg"]  # to the old last page
    assert p["annotation"]["header"]["scan"] == "p2.jpg"  # original untouched
    # Never closed: scans stays just the header page.
    unclosed = new_deed_record(DEED, "p2.jpg", [0] * 4)
    assert set_header(unclosed, page_names, "p1.jpg", [0] * 4)["scans"] == ["p1.jpg"]
    # Later, but no box before it: scans is just the header page.
    assert set_header(p, page_names, "p4.jpg", [0] * 4)["scans"] == ["p4.jpg"]
    # A saved box before the new header page would be outside scans.
    with_item = add_block(p, "assets", "", "1,-", "", [("p2.jpg", [0] * 4)])
    with_balance = set_balance(p, "p2.jpg", [0] * 4, "1,-", "", "")
    for r in (with_item, with_balance):
        assert set_header(r, page_names, "p2.jpg", [0] * 4)["scans"][0] == "p2.jpg"
        with pytest.raises(ValueError):
            set_header(r, page_names, "p3.jpg", [0] * 4)


def test_close_fills_scans_from_the_header_page_to_the_close_page():
    page_names = ["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg", "p5.jpg"]
    p = new_deed_record(DEED, "p2.jpg", [0] * 4)
    p = add_block(p, "assets", "", "1,-", "", [("p2.jpg", [0, 0, 5, 5])])
    # p3 has no items: still in the range.
    assert close_deed_record(p, page_names, "p4.jpg")["scans"] == [
        "p2.jpg",
        "p3.jpg",
        "p4.jpg",
    ]
    assert close_deed_record(p, page_names, "p2.jpg")["scans"] == ["p2.jpg"]
    assert p["scans"] == ["p2.jpg"]  # original untouched
    # Reopened and closed again: the range starts from the header page, not the old end.
    q = close_deed_record(
        close_deed_record(p, page_names, "p5.jpg"), page_names, "p3.jpg"
    )
    assert q["scans"] == ["p2.jpg", "p3.jpg"]
    with pytest.raises(ValueError):  # before the header page
        close_deed_record(p, page_names, "p1.jpg")
    # Closed before an item's last page (e.g. right after reopen): the range reaches it.
    p = add_block(
        p, "assets", "", "2,-", "", [("p3.jpg", [0] * 4), ("p4.jpg", [0] * 4)]
    )
    assert close_deed_record(p, page_names, "p2.jpg")["scans"] == [
        "p2.jpg",
        "p3.jpg",
        "p4.jpg",
    ]
    # So does the balance's.
    p = set_balance(p, "p5.jpg", [0] * 4, "1", "", "")
    assert close_deed_record(p, page_names, "p2.jpg")["scans"][-1] == "p5.jpg"


def test_add_block_rejects_missing_type_boxes_or_text():
    p = new_deed_record(DEED, "p1.jpg", [0] * 4)
    box = [("p1.jpg", [0, 0, 5, 5])]
    with pytest.raises(ValueError):
        add_block(p, None, "", "1,-", "", box)
    with pytest.raises(ValueError):
        add_block(p, "assets", "", "1,-", "", [])
    with pytest.raises(ValueError):
        add_block(p, "assets", "", " ", "  ", box)  # needs amount or description
    add_block(p, "assets", "", "1,-", "", box)
    add_block(p, "assets", "", "", "Een huis", box)


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
        )
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
    save_deed_record(tmp_path, new_deed_record(deeds["d3"], "b.jpg", [0] * 4), "Ann")
    save_deed_record(
        tmp_path,
        {
            **new_deed_record(deeds["d2"], "a.jpg", [0] * 4),
            "scans": ["a.jpg", "b.jpg", "c.jpg"],
        },
        "Ann",
    )
    assert list(deed_choices(deeds, tmp_path).items()) == [
        ("93 · Westdorp · B", "d1"),
        ("93 · Oostdorp · A · page 2", "d3"),
        ("105 · Alphen · C · pages 1-3", "d2"),
    ]


@pytest.mark.parametrize(
    "personen, error",
    [
        ([], "has 0 persons"),
        ([{"rol": "overledene"}, {"rol": "erfgenaam"}], "has 2 persons"),
        ([{"rol": "erfgenaam"}], "`rol: erfgenaam`"),
    ],
)
def test_single_overledene_rejects_a_deed_without_exactly_one(personen, error):
    with pytest.raises(ValueError, match=error):
        single_overledene({"personen": personen})


def test_single_overledene_returns_the_one_person():
    person = {"naam_volledig": "Jan Modaal", "rol": "overledene"}
    assert single_overledene({"personen": [person]}) is person


def test_save_and_load_deed_records_ignore_old_person_files(tmp_path):
    assert load_deed_records(tmp_path) == {}
    (tmp_path / "person-0001.json").write_text('{"metadata": {}}')  # old format
    p = add_block(
        new_deed_record(DEED, "a.jpg", [0] * 4),
        "assets",
        "",
        "1,-",
        "",
        [("a.jpg", [0] * 4)],
    )
    before = datetime.now(UTC)
    path = save_deed_record(tmp_path, p, "Ann")
    assert path == tmp_path / "labeled-deed-d1.json"
    # Every write records who wrote it and when, and leaves the record passed in alone.
    assert p["annotation_metadata"] == {"annotator_name": None, "annotation_date": None}
    saved = load_deed_records(tmp_path)["d1"]
    meta = saved.pop("annotation_metadata")
    assert saved == {k: v for k, v in p.items() if k != "annotation_metadata"}
    assert meta["annotator_name"] == "Ann"
    date = datetime.fromisoformat(meta["annotation_date"])
    assert date.tzinfo is not None and before <= date <= datetime.now(UTC)
    # Saving again rewrites the same file: one file per deed, with the latest of both.
    save_deed_record(tmp_path, delete_block(p, "A1"), "Bob")
    again = load_deed_records(tmp_path)["d1"]
    assert again["annotation"]["assets"] == []
    assert again["annotation_metadata"]["annotator_name"] == "Bob"
    assert (
        datetime.fromisoformat(again["annotation_metadata"]["annotation_date"]) >= date
    )
    assert sorted(f.name for f in tmp_path.iterdir()) == [
        "labeled-deed-d1.json",
        "person-0001.json",
    ]


def test_resume_lands_on_the_latest_page_of_the_last_book_with_files(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for book, names in ((a, ["a1", "a2"]), (b, ["b1", "b2", "b3"])):
        book.mkdir()
        for n in names:
            (book / f"{n}.jpg").touch()
    books = find_books(tmp_path)
    assert resume(books) == (0, 0)  # nothing written yet

    save_deed_record(a, new_deed_record(DEED, "a2.jpg", [0] * 4), "Ann")
    assert resume(books) == (0, 1)
    # Book b has files, so labeling stopped there: on its latest page, whichever deed.
    save_deed_record(b, new_deed_record(DEED, "b2.jpg", [0] * 4), "Ann")
    save_deed_record(
        b, new_deed_record({**DEED, "deed_id": "d0"}, "b1.jpg", [0] * 4), "Ann"
    )
    assert resume(books) == (1, 1)
    # Closed: on its close page.
    record = load_deed_records(b)["d1"]
    save_deed_record(
        b, close_deed_record(record, [p.name for p in list_pages(b)], "b3.jpg"), "Ann"
    )
    assert resume(books) == (1, 2)


def test_saved_boxes_reads_every_deed_file_on_a_scan(tmp_path):
    p1 = add_block(
        new_deed_record(DEED, "a.jpg", [0] * 4),
        "liabilities",
        "",
        "1,-",
        "",
        [("a.jpg", [1, 2, 3, 4]), ("b.jpg", [5, 6, 7, 8])],
    )
    p2 = add_block(
        new_deed_record({**DEED, "deed_id": "d2"}, "b.jpg", [0] * 4),
        "assets",
        "",
        "1,-",
        "",
        [("b.jpg", [0, 0, 9, 9])],
    )
    save_deed_record(tmp_path, p1, "Ann")
    save_deed_record(tmp_path, p2, "Ann")
    assert saved_boxes(tmp_path, "b.jpg") == [
        ("L1", [5, 6, 7, 8]),
        ("H", [0, 0, 0, 0]),
        ("A1", [0, 0, 9, 9]),
    ]
    assert saved_boxes(tmp_path, "a.jpg") == [("H", [0, 0, 0, 0]), ("L1", [1, 2, 3, 4])]
    # The open deed/person is drawn from memory, not from its (stale) file.
    assert saved_boxes(tmp_path, "b.jpg", skip_deed_id="d2") == [("L1", [5, 6, 7, 8])]
