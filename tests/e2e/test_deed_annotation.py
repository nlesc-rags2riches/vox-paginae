import json
import shutil
import time
from datetime import datetime

# TODO: Needs more detailed human review
import pytest
from playwright.sync_api import expect

from vox_paginae.annotation import FORMAT_VERSION

from .conftest import PAGE_H, PAGE_W, serve
from .helpers import (
    HEADER,
    HEADER_HINT,
    NEWER_VERSION_ERROR,
    button,
    click_button,
    close_deed_dropdown,
    drag_box_on_page,
    fill_text_input,
    jump_to_overall_page,
    load_app_and_lock_annotator,
    load_app_page,
    lock_annotator,
    open_deed,
    pick_in_deed_dropdown,
    pick_in_dropdown,
    pick_item_type,
    pick_root,
    save_header_or_balance_box,
    save_item,
    search_deed_dropdown,
    set_quality_to_highest,
    status,
    text_input,
    toggle_debug_panel,
    type_in_text_input_key_by_key,
)

pytestmark = pytest.mark.e2e


def deed_record(data_root, deed_id="deed-3", book="book1"):
    path = data_root / book / f"deed-annotation-{deed_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def fractions(bbox):
    x0, y0, x1, y1 = bbox
    return [x0 / PAGE_W, y0 / PAGE_H, x1 / PAGE_W, y1 / PAGE_H]


def test_open_writes_the_file_at_once_then_items_go_into_it(
    marimo_server, data_root, page
):
    load_app_and_lock_annotator(page, marimo_server)
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    open_deed(page)
    expect(status(page, "editing deed-annotation-deed-3 · page 2/3")).to_be_visible()
    # Written at once, before any item: the current page is the first page.
    record = deed_record(data_root)
    assert record.pop("annotation_metadata")["annotator_name"] == "Ann"
    header = record["annotation"].pop("header")
    assert [box["scan"] for box in header.pop("layout")] == ["page_02.jpg"]
    # Pre-filled from the deed's copied data.
    assert header == {
        "full_name": "Jan Modaal",
        "date_of_death": "1880-01-02",
        "place_of_residence": "Oostdorp",
    }
    assert record == {
        "format_version": FORMAT_VERSION,
        "deed_id": "deed-3",
        "copied_deed_person_data": {
            "aktenummer": "3",
            "plaats": "Oostdorp",
            "naam_volledig": "Jan Modaal",
            "datum_overlijden": "1880-01-02",
            "plaats_overlijden": "Oostdorp",
        },
        "scans": ["page_02.jpg"],
        # Blank totals and no box: both optional.
        "annotation": {
            "balance": {
                "total_assets": "",
                "total_liabilities": "",
                "total": "",
                "layout": [],
            },
            "assets": [],
            "liabilities": [],
        },
    }
    # While open, the deed row is text: the one deed dropdown is the move annotation target.
    expect(page.get_by_test_id("marimo-plugin-searchable-dropdown")).to_have_count(1)
    expect(page.get_by_text("move to", exact=True)).to_be_visible()
    expect(page.get_by_text("deed: 3 · Oostdorp · Jan Modaal")).to_be_visible()
    expect(button(page, "open")).to_be_disabled()

    drag_box_on_page(page, 0.2, 0.3, 0.6, 0.5)
    fill_text_input(page, "amount", "900,-")
    fill_text_input(page, "description", "Een huis")
    pick_item_type(page, "assets")
    save_item(page)
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()
    expect(page.get_by_role("radio", name="assets")).not_to_be_checked()

    record = deed_record(data_root)
    assert record["scans"] == ["page_02.jpg"]
    (item,) = record["annotation"]["assets"]
    assert list(item) == ["layout", "amount", "description"]
    assert (item["amount"], item["description"]) == ("900,-", "Een huis")
    assert fractions(item["layout"][0]["bbox"]) == pytest.approx(
        [0.2, 0.3, 0.6, 0.5], abs=0.01
    )
    # One file per deed: a deed that has one is not opened anew.
    pick_in_deed_dropdown(page, "Jan Modaal")
    expect(button(page, "open")).to_be_disabled()
    pick_in_deed_dropdown(page, "Westdorp")
    expect(button(page, "open")).to_be_enabled()


def test_open_and_close_need_no_header_box(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    hint = page.get_by_text(HEADER_HINT)
    expect(hint).to_have_count(0)  # no deed open
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    pick_in_deed_dropdown(page, "Jan Modaal")
    expect(button(page, "open")).to_be_enabled()  # no box drawn
    click_button(page, "open")
    expect(status(page, "editing deed-annotation-deed-3 · page 2/3")).to_be_visible()
    expect(hint).to_be_visible()
    record = deed_record(data_root)
    assert (record["annotation"]["header"]["layout"], record["scans"]) == (
        [],
        ["page_02.jpg"],
    )

    click_button(page, "next page")
    expect(status(page, "editing deed-annotation-deed-3 · page 3/3")).to_be_visible()

    # One box per click, on any of the deed's pages: here a complementary one first.
    save_header_or_balance_box(page, NEW_HEADER, "H1 · page 3")
    expect(hint).to_have_count(0)
    click_button(page, "prev page")
    expect(status(page, "page 2/3")).to_be_visible()
    save_header_or_balance_box(page, HEADER, "H2 · page 2")
    header = deed_record(data_root)["annotation"]["header"]["layout"]
    assert [box["scan"] for box in header] == ["page_03.jpg", "page_02.jpg"]
    assert fractions(header[1]["bbox"]) == pytest.approx(HEADER, abs=0.01)
    # In green, tagged: not an item's blue or orange.
    r, g, b = colour_near(page, 0.5, HEADER[1])
    assert g > max(r, b)

    # Deleted: the later one moves up.
    pick_in_dropdown(page, "H1 · page 3")
    click_button(page, "delete header box")
    expect(page.locator("option", has_text="H1 · page 2")).to_have_count(1)
    expect(page.locator("option", has_text="H2")).to_have_count(0)
    (box,) = deed_record(data_root)["annotation"]["header"]["layout"]
    assert box["scan"] == "page_02.jpg"

    # The last one deleted too: the hint is back, and close deed still closes it.
    pick_in_dropdown(page, "H1 · page 2")
    click_button(page, "delete header box")
    expect(hint).to_be_visible()
    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/3")).to_be_visible()
    record = deed_record(data_root)
    assert (record["annotation"]["header"]["layout"], record["scans"]) == (
        [],
        ["page_02.jpg"],
    )


NEW_HEADER = (0.1, 0.2, 0.9, 0.3)


def test_header_fields_are_prefilled_corrected_and_can_be_empty(
    marimo_server, data_root, page
):
    load_app_and_lock_annotator(page, marimo_server)
    expect(text_input(page, "full name")).to_be_disabled()  # no deed open
    open_deed(page)
    for label, value in [
        ("full name", "Jan Modaal"),
        ("date of death", "1880-01-02"),
        ("place of residence", "Oostdorp"),
    ]:
        expect(text_input(page, label)).to_have_value(value)
    fill_text_input(page, "full name", " Jan Modaal Jr. ")
    fill_text_input(page, "place of residence", " ")
    click_button(page, "save header fields")
    # Re-created from the saved record: stripped.
    expect(text_input(page, "full name")).to_have_value("Jan Modaal Jr.")
    record = deed_record(data_root)
    header = record["annotation"]["header"]
    assert [
        header[f] for f in ["full_name", "date_of_death", "place_of_residence"]
    ] == [
        "Jan Modaal Jr.",
        "1880-01-02",
        "",
    ]
    # The originals stay.
    assert record["copied_deed_person_data"]["naam_volledig"] == "Jan Modaal"

    # Every field empty: the deed still closes, with "" for each.
    fill_text_input(page, "full name", "")
    fill_text_input(page, "date of death", "")
    click_button(page, "save header fields")
    expect(text_input(page, "full name")).to_have_value("")
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()
    header = deed_record(data_root)["annotation"]["header"]
    assert [
        header[f] for f in ["full_name", "date_of_death", "place_of_residence"]
    ] == ["", "", ""]


def test_save_box_as_header_also_saves_the_typed_fields(marimo_server, data_root, page):
    # Box drawn, fields typed, then save box: the fields are not lost.
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page, header=False)
    expect(page.get_by_text(HEADER_HINT)).to_be_visible()
    drag_box_on_page(page, *HEADER, around="the header")
    fill_text_input(page, "full name", "Jan Modaal Jr.")
    click_button(page, "save box as header")
    expect(page.locator("option", has_text="H1 · page")).to_have_count(1)
    expect(text_input(page, "full name")).to_have_value("Jan Modaal Jr.")
    header = deed_record(data_root)["annotation"]["header"]
    assert header["full_name"] == "Jan Modaal Jr."
    assert len(header["layout"]) == 1


BALANCE = (0.2, 0.6, 0.8, 0.8)


def test_balance_totals_and_boxes_are_saved_apart(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    # Its section sits between the header and the items.
    y = {
        label: button(page, label).bounding_box()["y"]
        for label in ["close deed", "save box as header", "save box as balance", "save"]
    }
    assert (
        y["close deed"] < y["save box as header"] < y["save box as balance"] < y["save"]
    )

    # The totals, with no box: saved stripped, shown again and still editable.
    fill_text_input(page, "total assets", " 1.000,- ")
    fill_text_input(page, "total", "f 900")
    click_button(page, "save balance totals")
    expect(text_input(page, "total assets")).to_have_value("1.000,-")
    expect(text_input(page, "total assets")).to_be_enabled()
    assert deed_record(data_root)["annotation"]["balance"] == {
        "total_assets": "1.000,-",
        "total_liabilities": "",
        "total": "f 900",
        "layout": [],
    }

    # One box per click, on any of the deed's pages: the totals stay.
    save_header_or_balance_box(page, BALANCE, "B1 · page 1", kind="balance")
    expect(text_input(page, "total")).to_have_value("f 900")
    r, g, b = colour_near(page, 0.5, BALANCE[1])  # in purple
    assert min(r, b) > g
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    save_header_or_balance_box(page, BALANCE, "B2 · page 2", kind="balance")
    balance = deed_record(data_root)["annotation"]["balance"]
    assert [box["scan"] for box in balance["layout"]] == ["page_01.jpg", "page_02.jpg"]
    assert fractions(balance["layout"][1]["bbox"]) == pytest.approx(BALANCE, abs=0.01)
    assert balance["total"] == "f 900"

    # Deleted: the later one moves up.
    pick_in_dropdown(page, "B1 · page 1")
    click_button(page, "delete balance box")
    expect(page.locator("option", has_text="B1 · page 2")).to_have_count(1)
    expect(page.locator("option", has_text="B2")).to_have_count(0)

    # Totals all blank, with a box: allowed, and close refuses nothing about it.
    fill_text_input(page, "total assets", "")
    fill_text_input(page, "total", "")
    click_button(page, "save balance totals")
    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/3")).to_be_visible()
    balance = deed_record(data_root)["annotation"]["balance"]
    assert [box["scan"] for box in balance.pop("layout")] == ["page_02.jpg"]
    assert balance == {"total_assets": "", "total_liabilities": "", "total": ""}


def test_annotator_name_is_locked_first_and_every_write_records_it(
    marimo_server, data_root, page
):
    load_app_page(page, marimo_server)
    expect(text_input(page, "annotator")).to_be_visible(timeout=60_000)
    # No locked name: no page, no book, no deed, no buttons.
    expect(page.get_by_text("give your name and lock it to start")).to_be_visible()
    expect(page.locator("canvas")).to_have_count(0)
    for label in ["open", "next page", "save", "go"]:
        expect(button(page, label)).to_have_count(0)
    expect(button(page, "lock")).to_be_disabled()
    fill_text_input(page, "annotator", "  ")
    expect(button(page, "lock")).to_be_disabled()  # blank counts as empty
    fill_text_input(page, "annotator", "Ann")
    expect(page.locator("canvas")).to_have_count(0)  # typed, not locked yet

    click_button(page, "lock")
    expect(status(page, "no deed")).to_be_visible()
    expect(text_input(page, "annotator")).to_be_disabled()  # no stray edits
    open_deed(page)
    # Every write records the annotator and the time, with its timezone.
    first = deed_record(data_root)["annotation_metadata"]
    assert first["annotator_name"] == "Ann"
    assert datetime.fromisoformat(first["annotation_date"]).tzinfo is not None
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()

    # Someone else unlocks, reopens and saves: the latest annotator and time.
    click_button(page, "unlock")
    expect(page.get_by_text("give your name and lock it to start")).to_be_visible()
    expect(text_input(page, "annotator")).to_have_value("Ann")  # kept to edit
    lock_annotator(page, "Bob")
    pick_in_deed_dropdown(page, "Jan Modaal")
    click_button(page, "reopen")
    expect(status(page, "editing deed-annotation-deed-3")).to_be_visible()
    pick_item_type(page, "assets")
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "1,-")
    save_item(page)
    second = deed_record(data_root)["annotation_metadata"]
    assert second["annotator_name"] == "Bob"
    assert datetime.fromisoformat(second["annotation_date"]) > datetime.fromisoformat(
        first["annotation_date"]
    )


def test_continued_item_spans_two_pages(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)

    drag_box_on_page(page, 0.1, 0.7, 0.9, 0.9)
    click_button(page, "continue")
    expect(status(page, "pending 1")).to_be_visible()
    click_button(page, "next page")
    expect(status(page, "page 2/3 · pending 1")).to_be_visible()

    drag_box_on_page(page, 0.1, 0.1, 0.9, 0.2)
    pick_item_type(page, "liabilities")
    fill_text_input(page, "amount", "1,-")  # save needs amount or description
    save_item(page)
    expect(
        status(page, "editing deed-annotation-deed-3 · page 2/3 · pending 0")
    ).to_be_visible()
    click_button(
        page, "next page"
    )  # page 3 has no items: closing there still includes it
    expect(status(page, "page 3/3")).to_be_visible()
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()

    record = deed_record(data_root)
    assert record["scans"] == ["page_01.jpg", "page_02.jpg", "page_03.jpg"]
    assert record["annotation"]["assets"] == []
    (item,) = record["annotation"]["liabilities"]
    layout = item["layout"]
    assert [box["scan"] for box in layout] == ["page_01.jpg", "page_02.jpg"]
    assert fractions(layout[0]["bbox"]) == pytest.approx([0.1, 0.7, 0.9, 0.9], abs=0.01)
    assert fractions(layout[1]["bbox"]) == pytest.approx([0.1, 0.1, 0.9, 0.2], abs=0.01)


def test_restart_resumes_on_last_page_with_no_open_deed(data_root, page):
    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        click_button(page, "next page")
        expect(status(page, "page 2/3")).to_be_visible()
        open_deed(page)
        pick_item_type(page, "assets")
        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        fill_text_input(page, "amount", "1,-")  # save needs amount or description
        save_item(page)
        click_button(page, "next page")
        expect(status(page, "page 3/3")).to_be_visible()
        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        fill_text_input(page, "amount", "1,-")  # save needs amount or description
        save_item(page)
        expect(
            status(page, "editing deed-annotation-deed-3 · page 3/3 · pending 0")
        ).to_be_visible()
        # No close: a restart mid-deed must not reopen it.

    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)  # waits for "no deed"
        # Not closed: scans holds only the first page.
        expect(status(page, "no deed · page 2/3 · pending 0")).to_be_visible()

        open_deed(page, "Westdorp")
        pick_item_type(page, "assets")
        drag_box_on_page(page, 0.2, 0.5, 0.8, 0.6)
        fill_text_input(page, "amount", "1,-")  # save needs amount or description
        save_item(page)
        expect(
            status(page, "editing deed-annotation-deed-7g · page 2/3")
        ).to_be_visible()

    assert len(deed_record(data_root)["annotation"]["assets"]) == 2
    second = deed_record(data_root, "deed-7g")
    assert second["copied_deed_person_data"]["naam_volledig"] == "Piet Smit"
    assert second["scans"] == ["page_02.jpg"]


def test_restart_after_close_lands_on_the_close_page(data_root, page):
    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        open_deed(page)
        click_button(page, "next page")
        expect(status(page, "page 2/3")).to_be_visible()
        click_button(page, "close deed")
        expect(status(page, "no deed · page 2/3")).to_be_visible()

    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)  # waits for "no deed"
        expect(status(page, "no deed · page 2/3 · pending 0")).to_be_visible()
        open_deed(page, "Westdorp")  # the close page is the next first page

    assert deed_record(data_root)["scans"] == ["page_01.jpg", "page_02.jpg"]
    assert deed_record(data_root, "deed-7g")["scans"] == ["page_02.jpg"]


def test_old_files_are_ignored(data_root, page):
    # Old format, on page 2: neither resumed from, listed nor drawn.
    (data_root / "book1" / "person-0001.json").write_text(
        json.dumps({"metadata": {"scans": ["page_02.jpg"]}}), encoding="utf-8"
    )
    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        expect(status(page, "no deed · page 1/3")).to_be_visible()
        expect(page.locator("option", has_text="person-0001")).to_have_count(0)


def test_buttons_are_disabled_until_their_fields_are_set(marimo_server, page):
    load_app_and_lock_annotator(page, marimo_server)
    # prev page: page 1 is the floor, never into a previous book.
    for label in ["continue", "save", "open", "close deed", "prev page"]:
        expect(button(page, label)).to_be_disabled()

    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    expect(button(page, "continue")).to_be_enabled()
    pick_item_type(page, "assets")
    fill_text_input(page, "amount", "900,-")
    expect(button(page, "save")).to_be_disabled()  # no deed open
    # Opening redraws the page and drops a drawn box: continue keeps it, as pending.
    click_button(page, "continue")
    expect(status(page, "pending 1")).to_be_visible()
    expect(button(page, "continue")).to_be_disabled()

    pick_in_deed_dropdown(page, "Bakker")
    expect(button(page, "open")).to_be_disabled()  # two deed persons: cannot be used
    open_deed(page, header=False)  # the pending box is the item's
    # A box drawn once open has redrawn the page: only the pending one can disable it.
    expect(page.get_by_text(HEADER_HINT)).to_be_visible()
    drag_box_on_page(page, *HEADER)
    expect(button(page, "save box as header")).to_be_disabled()
    # The item inputs are re-created on open.
    expect(button(page, "save")).to_be_disabled()  # no amount, no description
    fill_text_input(page, "amount", "  ")
    expect(button(page, "save")).to_be_disabled()  # blank counts as empty
    fill_text_input(page, "amount", "900,-")
    expect(button(page, "save")).to_be_enabled()
    fill_text_input(page, "amount", "")
    # Description alone is enough too, and enables save while typing (no blur).
    type_in_text_input_key_by_key(page, "description", "Een huis")
    expect(button(page, "save")).to_be_enabled()
    expect(button(page, "close deed")).to_be_disabled()  # boxes pending
    save_item(page)
    expect(
        status(page, "editing deed-annotation-deed-3 · page 1/3 · pending 0")
    ).to_be_visible()
    expect(button(page, "close deed")).to_be_enabled()


def add_book(data_root, *pages):
    """A ``book2`` after book1: ``pages`` are copies of book1's first page, and it gets
    book1's ``deeds.json``, as every book needs one."""
    book2 = data_root / "book2"
    book2.mkdir()
    for name in pages:
        shutil.copy(data_root / "book1" / "page_01.jpg", book2 / name)
    shutil.copy(data_root / "book1" / "deeds.json", book2 / "deeds.json")
    return book2


def test_end_of_book_closes_deed_then_all_books_done(data_root, page):
    book2 = add_book(data_root, "only.jpg")

    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        click_button(page, "next page")
        expect(status(page, "page 2/3")).to_be_visible()
        # No header box: the end of the book still closes it.
        open_deed(page, header=False)
        # Before the first page: nowhere to close, continue or save.
        click_button(page, "prev page")
        expect(status(page, "page 1/3")).to_be_visible()
        expect(button(page, "close deed")).to_be_disabled()
        pick_item_type(page, "assets")
        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        fill_text_input(page, "amount", "1,-")
        # Their boxes would be outside scans.
        for label in ["save", "continue", "save box as balance", "save box as header"]:
            expect(button(page, label)).to_be_disabled()
        click_button(page, "next page")
        expect(button(page, "close deed")).to_be_enabled()
        click_button(page, "next page")
        expect(status(page, "page 3/3")).to_be_visible()

        pick_item_type(page, "assets")
        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        click_button(page, "continue")
        expect(status(page, "pending 1")).to_be_visible()
        expect(
            button(page, "next page")
        ).to_be_disabled()  # would drop the pending boxes
        fill_text_input(page, "amount", "1,-")  # save needs amount or description
        save_item(page)
        expect(
            status(page, "editing deed-annotation-deed-3 · page 3/3 · pending 0")
        ).to_be_visible()
        expect(button(page, "next page")).to_be_enabled()

        click_button(
            page, "next page"
        )  # last page of book1: writes and closes the deed
        expect(page.get_by_text("book2/only.jpg", exact=True)).to_be_visible()
        expect(status(page, "no deed · page 1/1")).to_be_visible()
        record = deed_record(data_root)
        assert record["scans"] == ["page_02.jpg", "page_03.jpg"]
        assert record["annotation_metadata"]["annotator_name"] == "Ann"

        click_button(page, "next page")
        expect(page.get_by_text("all books done")).to_be_visible()
        pick_in_dropdown(
            page, "book1"
        )  # the book dropdown stays: no slider needed to go back
        expect(page.get_by_text("book1/page_01.jpg", exact=True)).to_be_visible()
    assert not list(book2.glob("deed-annotation-*.json"))


def test_delete_writes_at_once(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    pick_item_type(page, "assets")
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "1,-")  # save needs amount or description
    save_item(page)
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "12,-")
    fill_text_input(page, "description", "Een stoel")
    save_item(page)
    expect(
        status(page, "editing deed-annotation-deed-3 · page 2/3 · pending 0")
    ).to_be_visible()

    options = page.locator("select option")
    # The dropdown text shows amount and description start, not just the tag.
    expect(options.filter(has_text="A2 · 12,- · Een stoel")).to_have_count(1)
    pick_in_dropdown(page, "A2 · 12,- · Een stoel")
    click_button(page, "delete")
    expect(options.filter(has_text="A2")).to_have_count(0)
    (item,) = deed_record(data_root)["annotation"]["assets"]  # written at once
    assert item["amount"] == "1,-"

    # The last item too: the file stays, with its first page.
    pick_in_dropdown(page, "A1 · 1,- ·")
    click_button(page, "delete")
    expect(options.filter(has_text="A1")).to_have_count(0)
    record = deed_record(data_root)
    assert record["annotation"]["assets"] == [] and record["scans"] == ["page_01.jpg"]
    expect(button(page, "delete")).to_be_disabled()  # nothing left to delete


def test_item_pick_survives_typing_in_amount_and_description(
    marimo_server, data_root, page
):
    # #60: typing once re-created the item dropdown, so delete found nothing picked.
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    pick_item_type(page, "assets")
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "1,-")
    save_item(page)

    pick_in_dropdown(page, "A1 · 1,- ·")
    type_in_text_input_key_by_key(page, "amount", "2")
    type_in_text_input_key_by_key(page, "description", "Een")
    click_button(page, "delete")
    expect(page.locator("select option").filter(has_text="A1")).to_have_count(0)
    assert deed_record(data_root)["annotation"]["assets"] == []


def test_quality_changes_pixels_not_on_screen_size(marimo_server, page):
    load_app_and_lock_annotator(page, marimo_server)
    canvas = page.locator("canvas").first
    expect(canvas).to_have_attribute("height", "975", timeout=10_000)  # 6.5 in * 150
    shown = canvas.bounding_box()
    assert round(shown["height"]) == 650  # FIG_H * 100 px

    set_quality_to_highest(page)  # 300 dpi
    expect(canvas).to_have_attribute("height", "1950", timeout=10_000)
    assert canvas.bounding_box() == shown


def test_clear_pending_discards_the_pending_boxes(marimo_server, page):
    load_app_and_lock_annotator(page, marimo_server)
    expect(button(page, "clear pending")).to_be_disabled()
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    click_button(page, "continue")
    expect(status(page, "pending 1")).to_be_visible()
    # Needs no deed or type: a stray continue never traps you.
    click_button(page, "clear pending")
    expect(status(page, "pending 0")).to_be_visible()
    expect(button(page, "clear pending")).to_be_disabled()


def colour_near(page, fx, fy, timeout=10):
    """The first non-gray ``[r, g, b]`` on the page canvas within a few pixels of
    fraction (fx, fy), waiting up to ``timeout`` s for one; ``None`` if none."""
    js = """(c, [fx, fy]) => {
      const x = Math.round(fx * c.width), y = Math.round(fy * c.height);
      const d = c.getContext("2d").getImageData(x, y - 6, 1, 13).data;
      for (let i = 0; i < d.length; i += 4)
        if (Math.max(d[i], d[i + 1], d[i + 2]) - Math.min(d[i], d[i + 1], d[i + 2]) > 20)
          return [d[i], d[i + 1], d[i + 2]];
      return null;
    }"""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if rgb := page.locator("canvas").first.evaluate(js, [fx, fy]):
            return rgb
        time.sleep(0.2)
    return None


def test_saved_boxes_stay_visible_after_close_and_restart(data_root, page):
    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        assert not colour_near(page, 0.4, 0.3, timeout=1)  # sanity: blank page
        open_deed(page)
        pick_item_type(page, "assets")
        drag_box_on_page(page, 0.2, 0.3, 0.6, 0.5)
        fill_text_input(page, "amount", "1,-")  # save needs amount or description
        save_item(page)
        click_button(page, "close deed")
        # Leave and come back, so a lingering selection cannot pass for the box.
        click_button(page, "next page")
        expect(status(page, "no deed · page 2/3")).to_be_visible()
        click_button(page, "prev page")
        expect(status(page, "no deed · page 1/3")).to_be_visible()
        assert colour_near(page, 0.4, 0.3)  # closed deed's box, faded

    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        expect(status(page, "no deed · page 1/3")).to_be_visible()
        assert colour_near(page, 0.4, 0.3)


def test_jump_is_view_only_while_a_deed_is_open(data_root, page):
    book2 = add_book(data_root, "only.jpg")

    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        open_deed(page)
        jump_to_overall_page(page, 4)
        expect(page.get_by_text("4 book2")).to_be_visible()  # the strip follows
        expect(
            page.get_by_text("/ 4 · book2/only.jpg")
        ).to_be_visible()  # total, target
        expect(page.locator('[title="book2: 1 pages"]')).to_be_visible()  # folder bar
        expect(button(page, "go")).to_be_disabled()  # view only: a deed is open

        click_button(page, "close deed")
        expect(button(page, "go")).to_be_enabled()
        click_button(page, "go")
        expect(page.get_by_text("book2/only.jpg", exact=True)).to_be_visible()
        # Each book has its own files: deed-3 has one in book1 only.
        open_deed(page)
        expect(
            status(page, "editing deed-annotation-deed-3 · page 1/1")
        ).to_be_visible()

    assert [p.name for p in book2.glob("deed-annotation-*.json")] == [
        "deed-annotation-deed-3.json"
    ]


def test_edit_replaces_item_in_place(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    pick_item_type(page, "assets")
    for amount in ["1,-", "2,-"]:
        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        fill_text_input(page, "amount", amount)
        save_item(page)
    expect(button(page, "cancel edit")).to_be_disabled()
    # A balance box, so only the edit can disable delete balance box below.
    save_header_or_balance_box(page, BALANCE, "B1 · page 1", kind="balance")

    pick_in_dropdown(page, "A1 · 1,- ·")
    click_button(page, "edit")
    # The item is loaded into the inputs, its box into pending.
    expect(status(page, "pending 1 · editing A1")).to_be_visible()
    expect(text_input(page, "amount")).to_have_value("1,-")
    # No timed debounce (it renders a `delay`): marimo's can send back the value edit
    # or cancel edit just replaced (#11). Too narrow a race to catch by timing clicks.
    expect(page.locator("marimo-text input")).not_to_have_count(0)
    expect(page.locator("marimo-text input[delay]")).to_have_count(0)
    expect(button(page, "delete")).to_be_disabled()
    expect(button(page, "close deed")).to_be_disabled()
    expect(button(page, "delete header box")).to_be_disabled()  # H1 is saved
    expect(button(page, "delete balance box")).to_be_disabled()  # B1 is saved
    expect(button(page, "save box as balance")).to_be_disabled()

    fill_text_input(page, "amount", "10,-")
    fill_text_input(page, "description", "Een huis")
    save_item(page)
    expect(status(page, "pending 0")).to_be_visible()
    items = deed_record(data_root)["annotation"]["assets"]
    assert [i["amount"] for i in items] == ["10,-", "2,-"]  # A1 stays A1
    assert items[0]["description"] == "Een huis"

    # cancel edit drops the loaded item and leaves the file alone.
    pick_in_dropdown(page, "A2 · 2,- ·")
    click_button(page, "edit")
    expect(status(page, "editing A2")).to_be_visible()
    click_button(page, "cancel edit")
    expect(status(page, "pending 0")).to_be_visible()
    expect(text_input(page, "amount")).to_have_value("")
    assert deed_record(data_root)["annotation"]["assets"] == items


def test_debug_panel_shows_the_file(data_root, page):
    with serve(data_root, "--debug") as url:
        load_app_and_lock_annotator(page, url)
        expect(page.get_by_text("DEBUG PANE")).to_be_visible()
        expect(page.get_by_text("no file yet")).to_be_visible()
        open_deed(page)
        # Written at once, so shown before any item.
        expect(
            page.get_by_text("deed-annotation-deed-3.json", exact=True)
        ).to_be_visible()
        pick_item_type(page, "assets")
        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        fill_text_input(page, "amount", "12,-")
        save_item(page)
        expect(page.get_by_text('"12,-"')).to_be_visible()

        pick_in_dropdown(page, "A1 · 12,- ·")
        click_button(page, "delete")  # every write refreshes the panel
        expect(page.get_by_text('"12,-"')).to_have_count(0)

        debug = page.get_by_role("switch")
        toggle_debug_panel(page)  # hides the panel for a demo; the switch itself stays
        expect(page.get_by_text("DEBUG PANE")).to_have_count(0)
        expect(debug).to_be_visible()
        toggle_debug_panel(page)
        expect(page.get_by_text("DEBUG PANE")).to_be_visible()


def test_no_debug_panel_by_default(marimo_server, page):
    load_app_and_lock_annotator(page, marimo_server)
    expect(button(page, "open")).to_be_visible()
    expect(page.get_by_text("DEBUG PANE")).to_have_count(0)
    expect(page.get_by_role("switch")).to_have_count(0)


def test_pick_right_after_close_deed_is_kept(marimo_server, page):
    # The status line changes only together with the rebuilt dropdown. Before, it said
    # "no deed" while the old dropdown was still showing: a pick then sent
    # nothing, and the rebuilt dropdown came in empty.
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)

    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()
    pick_in_deed_dropdown(page, "Jan Modaal")
    # Check once the rebuilds are surely over (~350 ms after the click when measured).
    page.wait_for_timeout(1000)
    assert button(page, "go to deed").is_enabled()


def test_go_to_deed_moves_to_its_first_page(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    expect(button(page, "go to deed")).to_be_disabled()  # deed-3 is open

    click_button(page, "close deed")
    pick_in_deed_dropdown(page, "Westdorp")
    expect(button(page, "go to deed")).to_be_disabled()  # no file: open it
    for n in [2, 3]:
        click_button(page, "next page")
        expect(status(page, f"page {n}/3")).to_be_visible()
    pick_in_deed_dropdown(page, "Jan Modaal")
    click_button(page, "go to deed")
    expect(status(page, "no deed · page 1/3")).to_be_visible()  # moves, writes nothing
    assert len(list((data_root / "book1").glob("deed-annotation-*.json"))) == 1


def test_reopen_rewrites_the_same_file(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    pick_item_type(page, "assets")
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "1,-")
    save_item(page)
    expect(button(page, "reopen")).to_be_disabled()  # deed-3 is open
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "2,-")
    save_item(page)

    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/3")).to_be_visible()
    pick_in_deed_dropdown(page, "Westdorp")
    expect(button(page, "reopen")).to_be_disabled()  # no file: open it
    pick_in_deed_dropdown(page, "Jan Modaal")
    expect(button(page, "open")).to_be_disabled()  # has a file: reopen it
    click_button(page, "reopen")  # back on the first page
    expect(status(page, "editing deed-annotation-deed-3 · page 1/3")).to_be_visible()
    expect(page.get_by_text("deed: 3 · Oostdorp · Jan Modaal")).to_be_visible()

    pick_in_dropdown(page, "A1 · 1,- ·")
    click_button(page, "edit")
    expect(status(page, "editing A1")).to_be_visible()
    expect(text_input(page, "amount")).to_have_value("1,-")  # inputs rebuilt
    fill_text_input(page, "amount", "10,-")
    save_item(page)
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()

    assert [p.name for p in (data_root / "book1").glob("deed-annotation-*.json")] == [
        "deed-annotation-deed-3.json"
    ]
    record = deed_record(data_root)
    assert [i["amount"] for i in record["annotation"]["assets"]] == ["10,-", "2,-"]
    # Closed on the first page, but A2 is on page 2: scans still reaches it.
    assert record["scans"] == ["page_01.jpg", "page_02.jpg"]


def test_delete_deed_needs_confirmation(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)
    expect(button(page, "delete deed")).to_be_disabled()  # deed-3 is open

    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()
    pick_in_deed_dropdown(page, "Jan Modaal")
    click_button(page, "delete deed")
    click_button(page, "cancel")  # writes nothing
    expect(button(page, "delete deed")).to_be_enabled()
    path = data_root / "book1" / "deed-annotation-deed-3.json"
    assert path.exists()

    click_button(page, "delete deed")
    click_button(page, "confirm delete deed-annotation-deed-3")
    expect(
        button(page, "delete deed")
    ).to_be_disabled()  # dropdown rebuilt, nothing picked
    assert not path.exists()
    # Back among the deeds without a file, and it can be opened anew.
    expect(search_deed_dropdown(page, "Jan Modaal")).to_have_text(
        ["3 · Oostdorp · Jan Modaal"]
    )
    close_deed_dropdown(page)
    pick_in_deed_dropdown(page, "Jan Modaal")
    expect(button(page, "open")).to_be_enabled()
    expect(button(page, "delete deed")).to_be_disabled()
    click_button(page, "open")
    expect(status(page, "editing deed-annotation-deed-3 · page 1/3")).to_be_visible()
    assert path.exists()


def test_move_annotation_to_another_deed(marimo_server, data_root, page):
    load_app_and_lock_annotator(page, marimo_server)
    open_deed(page)  # the wrong deed
    pick_item_type(page, "assets")
    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    fill_text_input(page, "amount", "1,-")
    save_item(page)
    expect(button(page, "move annotation")).to_be_disabled()  # no deed picked
    # Only the deeds without a file.
    expect(search_deed_dropdown(page, "Jan Modaal", "move to")).to_have_count(0)
    close_deed_dropdown(page)
    drag_box_on_page(page, 0.2, 0.4, 0.8, 0.5)
    click_button(page, "continue")
    pick_in_deed_dropdown(page, "Westdorp", "move to")
    move_to = page.get_by_label("move to", exact=True)
    expect(move_to).to_contain_text("Westdorp")
    expect(button(page, "move annotation")).to_be_disabled()  # as close deed
    # Clearing pending re-creates the dropdown (via the book), empty: wait for that,
    # or the pick lands in the old one and is lost (#74). Then pick again.
    click_button(page, "clear pending")
    expect(move_to).not_to_contain_text("Westdorp")
    pick_in_deed_dropdown(page, "Westdorp", "move to")

    click_button(page, "move annotation")
    expect(status(page, "editing deed-annotation-deed-7g")).to_be_visible()
    expect(page.get_by_text("deed: 7 · Westdorp · Piet Smit")).to_be_visible()
    assert [p.name for p in (data_root / "book1").glob("deed-annotation-*.json")] == [
        "deed-annotation-deed-7g.json"
    ]
    moved = deed_record(data_root, "deed-7g")
    assert moved["copied_deed_person_data"]["naam_volledig"] == "Piet Smit"
    assert [i["amount"] for i in moved["annotation"]["assets"]] == ["1,-"]

    # Still open: the next item goes into the new file.
    pick_item_type(page, "assets")
    drag_box_on_page(page, 0.2, 0.4, 0.8, 0.5)
    fill_text_input(page, "amount", "2,-")
    save_item(page)
    moved = deed_record(data_root, "deed-7g")
    assert [i["amount"] for i in moved["annotation"]["assets"]] == ["1,-", "2,-"]

    # The old deed has no file again: it can be opened anew.
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()
    expect(search_deed_dropdown(page, "Jan Modaal")).to_have_text(
        ["3 · Oostdorp · Jan Modaal"]
    )
    close_deed_dropdown(page)
    pick_in_deed_dropdown(page, "Jan Modaal")
    expect(button(page, "open")).to_be_enabled()


def test_deed_dropdown_shows_the_picked_deed(marimo_server, page):
    load_app_and_lock_annotator(page, marimo_server)
    # Searchable, so not a <select>: a button opening a list of role "option".
    # By aktenummer, then place: deeds.json is in neither order.
    expect(search_deed_dropdown(page)).to_have_text(
        [
            "3 · Oostdorp · Jan Modaal",
            "7 · Oostdorp · Jan de Wit",
            "7 · Westdorp · Piet Smit",
            "12 · Oostdorp · Kees Bakker · Klaas Bakker",
        ]
    )
    close_deed_dropdown(page)
    pick_in_deed_dropdown(page, "Westdorp")
    expect(page.get_by_text("Piet Smit · died 1880-05-06 in Westdorp")).to_be_visible()

    # A deed with a file goes last, with its pages.
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    open_deed(page)
    click_button(page, "close deed")
    expect(status(page, "no deed")).to_be_visible()
    expect(search_deed_dropdown(page)).to_have_text(
        [
            "7 · Oostdorp · Jan de Wit",
            "7 · Westdorp · Piet Smit",
            "12 · Oostdorp · Kees Bakker · Klaas Bakker",
            "3 · Oostdorp · Jan Modaal · page 2",
        ]
    )


def test_book_without_deeds_json_stops_annotating(data_root, page):
    add_book(data_root, "only.jpg")  # copies book1's deeds.json: before removing it
    (data_root / "book1" / "deeds.json").unlink()
    with serve(data_root) as url:
        load_app_page(page, url)
        lock_annotator(page)
        expect(page.get_by_text("no deeds.json in book book1")).to_be_visible(
            timeout=60_000
        )
        # No scan, no form: nothing to draw on, open or save.
        expect(page.locator("canvas")).to_have_count(0)
        for label in ["save", "next page", "open", "close deed", "reopen"]:
            expect(button(page, label)).to_have_count(0)
        pick_in_dropdown(
            page, "book2"
        )  # the book dropdown stays: no slider needed to leave
        expect(page.get_by_text("book2/only.jpg", exact=True)).to_be_visible()
    assert not list((data_root / "book1").glob("deed-annotation-*.json"))


def test_deed_without_exactly_one_overledene_shows_an_error(marimo_server, page):
    load_app_and_lock_annotator(page, marimo_server)
    pick_in_deed_dropdown(page, "Bakker")
    expect(page.get_by_text("This deed has 2 deed persons")).to_be_visible()
    expect(button(page, "open")).to_be_disabled()
    # Only that deed fails: another one in the same book still shows its overledene.
    pick_in_deed_dropdown(page, "Jan Modaal")
    expect(page.get_by_text("This deed has 2 deed persons")).to_have_count(0)
    expect(page.get_by_text("Jan Modaal · died 1880-01-02 in Oostdorp")).to_be_visible()


def test_a_deed_file_from_a_newer_version_shows_an_error_and_is_never_touched(
    data_root, page
):
    path = data_root / "book1" / "deed-annotation-deed-3.json"
    path.write_text(
        json.dumps({"format_version": "99.0.0", "deed_id": "deed-3"}), encoding="utf-8"
    )
    before = path.read_bytes()
    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        pick_in_deed_dropdown(page, "Jan Modaal")
        expect(page.get_by_text(NEWER_VERSION_ERROR)).to_be_visible()
        expect(page.get_by_text(str(path))).to_be_visible()
        # A file this version can read would enable these: only the version stops them.
        # Not open: any file disables it.
        for label in ["go to deed", "reopen", "delete deed"]:
            expect(button(page, label)).to_be_disabled()
        # Only that deed fails: another one in the same book still opens.
        open_deed(page, "Piet Smit")
        expect(status(page, "editing deed-annotation-deed-7g")).to_be_visible()
    assert path.read_bytes() == before


def test_book_dropdown_moves_to_the_first_page(data_root, page):
    book2 = add_book(data_root, "a.jpg", "b.jpg")
    book_dd = page.locator("select", has=page.locator("option", has_text="book2"))

    with serve(data_root) as url:
        load_app_and_lock_annotator(page, url)
        pick_in_dropdown(page, "book2")
        expect(page.get_by_text("book2/a.jpg", exact=True)).to_be_visible()
        click_button(page, "next page")
        expect(page.get_by_text("book2/b.jpg", exact=True)).to_be_visible()
        pick_in_dropdown(page, "book1")
        expect(page.get_by_text("book1/page_01.jpg", exact=True)).to_be_visible()

        drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
        click_button(page, "continue")
        expect(status(page, "pending 1")).to_be_visible()
        expect(book_dd).to_be_disabled()  # pending boxes belong to this page
        click_button(page, "clear pending")
        # Its redraw drops a box drawn before it lands: wait for it.
        expect(status(page, "pending 0")).to_be_visible()

        open_deed(page)
        expect(book_dd).to_be_disabled()  # a deed never crosses books

        click_button(page, "close deed")
        expect(book_dd).to_be_enabled()
        pick_in_dropdown(page, "book2")
        expect(status(page, "no deed · page 1/2")).to_be_visible()
    assert not list(book2.glob("deed-annotation-*.json"))


@pytest.mark.parametrize(
    "notebook",
    ["notebooks/deed_annotation.py", "notebooks/single_deed_annotation.py"],
)
def test_without_data_root_the_root_is_the_folder_the_tool_started_from(
    tmp_path, page, notebook
):
    started_from = tmp_path.resolve()
    with serve(None, notebook=notebook, cwd=started_from) as url:
        load_app_page(page, url)
        expect(
            page.get_by_text(f"root: {started_from} (click to change)")
        ).to_be_visible(timeout=60_000)


def test_root_cannot_change_while_a_deed_is_open_or_boxes_are_pending(
    marimo_server, page
):
    load_app_and_lock_annotator(page, marimo_server)
    root_picker = page.get_by_text("(click to change)")
    expect(root_picker).to_be_visible()

    open_deed(page)
    expect(root_picker).to_have_count(0)
    click_button(page, "close deed")
    expect(root_picker).to_be_visible()

    drag_box_on_page(page, 0.2, 0.2, 0.8, 0.3)
    click_button(page, "continue")
    expect(status(page, "pending 1")).to_be_visible()
    expect(root_picker).to_have_count(0)
    click_button(page, "clear pending")
    expect(root_picker).to_be_visible()


def test_root_without_scans_says_so_until_one_with_scans_is_picked(
    tmp_path, data_root, page
):
    (tmp_path / "empty").mkdir()
    with serve(tmp_path) as url:
        load_app_and_lock_annotator(page, url)
        pick_root(page, "empty")
        expect(page.get_by_text(f"no scans under {tmp_path / 'empty'}")).to_be_visible()
        expect(page.locator("canvas")).to_have_count(0)
        pick_root(page, data_root.name)
        expect(status(page, "no deed · page 1/3")).to_be_visible()
        # A cell that raises shows this toast.
        expect(page.get_by_text("An internal error occurred")).to_have_count(0)
