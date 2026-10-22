import json

import pytest

# TODO: Together with the `src` correspondent, split and human-review

from vox_paginae.blocks import (
    add_block,
    block_labels,
    deed_choices,
    delete_block,
    find_books,
    last_person_id,
    load_deeds,
    load_person_records,
    new_person_record,
    next_page,
    person_choices,
    replace_block,
    resume,
    save_person_record,
    saved_boxes,
)


def test_next_page_crosses_books_and_stops_when_done():
    counts = [2, 1]
    assert next_page((0, 0), counts) == (0, 1)
    assert next_page((0, 1), counts) == (1, 0)
    assert next_page((1, 0), counts) == (2, 0)
    assert next_page((2, 0), counts) == (2, 0)


def test_blocks_labels_and_scans():
    p = new_person_record("p2.jpg")
    p = add_block(p, "assets", "", "900,-", "huis", [("p2.jpg", [1, 2, 3, 4])])
    p = add_block(
        p,
        "assets",
        "cash",
        "1,-",
        "",
        [("p3.jpg", [0, 0, 5, 5]), ("p4.jpg", [0, 0, 5, 5])],
    )
    p = add_block(p, "liabilities", "", "10", "schuld", [("p3.jpg", [0, 0, 9, 9])])
    meta = p["metadata"]
    assert [label for label, _ in block_labels(p)] == ["A1", "A2", "L1"]
    assert meta["assets"]["items"][0]["category"] is None
    assert meta["scans"] == ["p2.jpg", "p3.jpg", "p4.jpg"]

    p = delete_block(p, "A2")
    assert [label for label, _ in block_labels(p)] == ["A1", "L1"]
    assert block_labels(None) == []  # no current person
    assert p["metadata"]["scans"] == ["p2.jpg", "p3.jpg"]  # p4 had only A2

    p = delete_block(delete_block(p, "A1"), "L1")
    assert p["metadata"]["scans"] == ["p2.jpg"]  # start page always stays
    assert meta["scans"] == ["p2.jpg", "p3.jpg", "p4.jpg"]  # originals untouched


def test_first_block_sets_start_to_its_earliest_page():
    # Continued block drawn on p1 and p2, saved on p2: the person starts on p1.
    p = new_person_record("p2.jpg")
    boxes = [("p1.jpg", [0, 0, 5, 5]), ("p2.jpg", [0, 0, 5, 5])]
    p = add_block(p, "assets", "", "1,-", "", boxes)
    assert p["metadata"]["scans"] == ["p1.jpg", "p2.jpg"]
    # Later blocks never move the start page.
    p = add_block(p, "assets", "", "1,-", "", [("p0.jpg", [0, 0, 5, 5])])
    assert p["metadata"]["scans"] == ["p1.jpg", "p0.jpg", "p2.jpg"]
    # Deleting every block is a fresh start: the next block sets the start page again.
    p = delete_block(delete_block(p, "A2"), "A1")
    p = add_block(p, "assets", "", "1,-", "", [("p3.jpg", [0, 0, 5, 5])])
    assert p["metadata"]["scans"] == ["p3.jpg"]


def test_replace_block_keeps_position_unless_type_changes():
    box = [("p1.jpg", [0, 0, 5, 5])]
    p = new_person_record("p1.jpg")
    for amount in ["1", "2", "3"]:
        p = add_block(p, "assets", "", amount, "", box)
    p = replace_block(p, "A2", "assets", "cash", "20", "", [("p2.jpg", [1, 1, 9, 9])])
    items = p["metadata"]["assets"]["items"]
    assert [i["amount"] for i in items] == ["1", "20", "3"]  # A2 stays A2
    assert items[1]["category"] == "cash"
    assert p["metadata"]["scans"] == ["p1.jpg", "p2.jpg"]
    # A type change moves it to the end of the other type.
    p = replace_block(p, "A1", "liabilities", "", "1", "", box)
    assert [label for label, _ in block_labels(p)] == ["A1", "A2", "L1"]
    with pytest.raises(ValueError):  # same checks as add_block
        replace_block(p, "A1", "assets", "", "", "", box)


def test_replace_only_block_resets_start_page():
    p = new_person_record("p1.jpg")
    p = add_block(p, "assets", "", "1", "", [("p1.jpg", [0, 0, 5, 5])])
    p = replace_block(p, "A1", "assets", "", "1", "", [("p2.jpg", [0, 0, 5, 5])])
    assert p["metadata"]["scans"] == ["p2.jpg"]


def test_add_block_rejects_missing_type_boxes_or_text():
    p = new_person_record("p1.jpg")
    box = [("p1.jpg", [0, 0, 5, 5])]
    with pytest.raises(ValueError):
        add_block(p, None, "", "1,-", "", box)
    with pytest.raises(ValueError):
        add_block(p, "assets", "", "1,-", "", [])
    with pytest.raises(ValueError):
        add_block(p, "assets", "", " ", "  ", box)  # needs amount or description
    add_block(p, "assets", "", "1,-", "", box)
    add_block(p, "assets", "", "", "Een huis", box)


def test_save_load_resume_round_trip(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for book, names in ((a, ["a1", "a2"]), (b, ["b1", "b2", "b3"])):
        book.mkdir()
        for n in names:
            (book / f"{n}.jpg").touch()
    books = find_books(tmp_path)
    # Nothing written yet: page 0, newest person 0 (the first save starts person 1).
    assert resume(books) == ((0, 0), 0)

    # Book a: one person whose last item is not on a's last page. Book a is still done:
    # b, the last book with files, is where labeling stopped.
    p = add_block(
        new_person_record("a1.jpg"), "assets", "", "1", "x", [("a1.jpg", [0, 0, 5, 5])]
    )
    save_person_record(a, 1, p, "Anna", "")
    # Book b: person 1 ends on b1, person 2 starts on b1 and has an item on b2.
    save_person_record(b, 1, new_person_record("b1.jpg"), "Bert", "1881")
    p2 = add_block(
        new_person_record("b1.jpg"),
        "liabilities",
        "",
        "1,-",
        "",
        [("b2.jpg", [1, 2, 3, 4])],
    )
    save_person_record(b, 2, p2, "  Cor  ", "")

    assert list(load_person_records(b)) == [1, 2]
    assert resume(books) == ((1, 1), 2)  # book b, page b2, after person 2 (closed)
    person_record = load_person_records(b)[2]
    assert person_record["metadata"]["deceased"]["full_name"] == "Cor"
    assert person_record["metadata"]["deceased"]["date_of_death"] is None
    assert (
        person_record["metadata"]["liabilities"]["items"]
        == p2["metadata"]["liabilities"]["items"]
    )

    with pytest.raises(ValueError):
        save_person_record(b, 3, new_person_record("b2.jpg"), " ", "")
    assert list(load_person_records(b)) == [1, 2]

    save_person_record(
        b,
        3,
        add_block(
            new_person_record("b2.jpg"),
            "assets",
            "",
            "1,-",
            "",
            [("b3.jpg", [0, 0, 5, 5])],
        ),
        "Dirk",
        "",
    )
    assert resume(books) == ((1, 2), 3)  # last page of the last book, after Dirk


def test_saved_boxes_reads_every_person_file_on_a_scan(tmp_path):
    p1 = add_block(
        new_person_record("a.jpg"),
        "liabilities",
        "",
        "1,-",
        "",
        [("a.jpg", [1, 2, 3, 4]), ("b.jpg", [5, 6, 7, 8])],
    )
    p2 = add_block(
        new_person_record("b.jpg"), "assets", "", "1,-", "", [("b.jpg", [0, 0, 9, 9])]
    )
    save_person_record(tmp_path, 1, p1, "Anna", "")
    save_person_record(tmp_path, 2, p2, "Bert", "")
    assert saved_boxes(tmp_path, "b.jpg") == [
        ("L1", [5, 6, 7, 8]),
        ("A1", [0, 0, 9, 9]),
    ]
    assert saved_boxes(tmp_path, "a.jpg") == [("L1", [1, 2, 3, 4])]
    # The person being edited is drawn from memory, not from their (stale) file.
    assert saved_boxes(tmp_path, "b.jpg", skip_person_id=2) == [("L1", [5, 6, 7, 8])]


def test_last_person_id_counts_files_per_book(tmp_path):
    assert last_person_id(tmp_path) == 0
    p = add_block(
        new_person_record("a.jpg"), "assets", "", "1,-", "", [("a.jpg", [0, 0, 5, 5])]
    )
    save_person_record(tmp_path, 3, p, "X", "")
    assert last_person_id(tmp_path) == 3


def test_person_choices_go_to_each_start_page(tmp_path):
    for name in ["a.jpg", "b.jpg", "c.jpg"]:
        (tmp_path / name).touch()
    assert person_choices(tmp_path) == {}
    p1 = add_block(
        new_person_record("a.jpg"),
        "assets",
        "",
        "1,-",
        "",
        [("a.jpg", [0, 0, 5, 5]), ("b.jpg", [0, 0, 5, 5])],
    )
    p2 = new_person_record("c.jpg")  # every block deleted: only the start page left
    save_person_record(tmp_path, 1, p1, "Anna", "")
    save_person_record(tmp_path, 2, p2, "Bert", "")
    assert person_choices(tmp_path) == {
        "person-0001 · Anna · pages 1-2": (1, 0),
        "person-0002 · Bert · page 3": (2, 2),
    }


def test_deed_choices_sort_by_aktenummer_then_place(tmp_path):
    def deed(deed_id, aktenummer, plaats, name):
        return {
            "deed_id": deed_id,
            "aktenummer": aktenummer,
            "plaats": plaats,
            "personen": [{"naam_volledig": name}],
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
    assert deed_choices(deeds) == {
        "93 · Oostdorp · A": "d3",
        "93 · Westdorp · B": "d1",
        "105 · Alphen · C": "d2",
    }
