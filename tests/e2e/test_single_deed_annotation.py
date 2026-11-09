import json

import pytest
from playwright.sync_api import expect

from .conftest import PAGE_H, PAGE_W
from .helpers import (
    HEADER,
    HEADER_HINT,
    click_button,
    close_deed_dropdown,
    drag_box_on_page,
    fill_text_input,
    load_app_page,
    lock_annotator,
    pick_in_deed_dropdown,
    pick_in_dropdown,
    pick_item_type,
    save_header_or_balance_box,
    save_item,
    search_deed_dropdown,
    status,
    text_input,
)

pytestmark = pytest.mark.e2e

PICK_HINT = "pick a deed to see its pages"


def deed_record(single_deed_root, folder, ref_reg):
    path = single_deed_root / folder / f"deed-annotation-{ref_reg}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_app_and_lock_annotator(page, url):
    load_app_page(page, url)
    lock_annotator(page)
    expect(page.get_by_text(PICK_HINT)).to_be_visible(timeout=60_000)


def deed_dropdown(page):
    return page.get_by_label("deed", exact=True)


def test_lock_open_annotate_close_writes_the_deed_annotation_file(
    single_deed_server, single_deed_root, page
):
    load_app_and_lock_annotator(page, single_deed_server)
    # In the order a file browser shows the folders: 6-1 before 10-1.
    expect(search_deed_dropdown(page)).to_have_text(
        ["6#1 · Jan Modaal", "10#1 · Piet Smit"]
    )
    close_deed_dropdown(page)
    expect(search_deed_dropdown(page, "10#")).to_have_text(["10#1 · Piet Smit"])
    close_deed_dropdown(page)
    pick_in_deed_dropdown(page, "10#1")
    expect(status(page, "10-1/scan-1.jpg · no deed · page 1/3")).to_be_visible()
    click_button(page, "next page")
    expect(status(page, "no deed · page 2/3")).to_be_visible()
    assert not list(
        single_deed_root.glob("*/deed-annotation-*")
    )  # a pick writes nothing

    click_button(page, "open")
    expect(status(page, "editing deed-annotation-10#1 · page 2/3")).to_be_visible()
    # Pre-filled from the single deed input.
    expect(text_input(page, "full name")).to_have_value("Piet Smit")
    expect(text_input(page, "date of death")).to_have_value("5 mei 1880")
    expect(text_input(page, "place of residence")).to_have_value("Westdorp")
    expect(page.get_by_text(HEADER_HINT)).to_be_visible()
    save_header_or_balance_box(page, HEADER, "H1 · page 2")
    drag_box_on_page(page, 0.2, 0.3, 0.6, 0.5)
    fill_text_input(page, "amount", "900,-")
    fill_text_input(page, "description", "Een huis")
    pick_item_type(page, "assets")
    save_item(page)
    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/3")).to_be_visible()

    record = deed_record(single_deed_root, "10-1", "10#1")
    assert record["deed_id"] == "10#1"
    assert record["annotation_metadata"]["annotator_name"] == "Ann"
    assert record["copied_deed_person_data"] == {
        "ref_reg": "10#1",
        "aktenummer": None,
        "tax_office": "Westdorp",
        "full_name": "Piet Smit",
        "profession": "bakker",
        "date_of_death": "5 mei 1880",
        "place_of_residence": "Westdorp",
        "place_of_death": None,
    }
    assert record["scans"] == ["scan-2.jpg"]
    header = record["annotation"]["header"]
    assert [box["scan"] for box in header.pop("layout")] == ["scan-2.jpg"]
    assert header == {
        "full_name": "Piet Smit",
        "date_of_death": "5 mei 1880",
        "place_of_residence": "Westdorp",
    }
    (item,) = record["annotation"]["assets"]
    assert (item["amount"], item["description"]) == ("900,-", "Een huis")
    x0, y0, x1, y1 = item["layout"][0]["bbox"]
    assert [x0 / PAGE_W, y0 / PAGE_H, x1 / PAGE_W, y1 / PAGE_H] == pytest.approx(
        [0.2, 0.3, 0.6, 0.5], abs=0.01
    )


def test_open_reopens_a_deed_with_a_file_on_its_first_scan(
    single_deed_server, single_deed_root, page
):
    load_app_and_lock_annotator(page, single_deed_server)
    pick_in_deed_dropdown(page, "6#1")
    click_button(page, "open")
    expect(status(page, "editing deed-annotation-6#1 · page 1/3")).to_be_visible()
    expect(page.get_by_text(HEADER_HINT)).to_be_visible()
    save_header_or_balance_box(page, HEADER, "H1 · page 1")
    # The deed dropdown is locked while a deed is open.
    expect(deed_dropdown(page)).to_be_disabled()
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/3")).to_be_visible()
    expect(deed_dropdown(page)).to_be_enabled()
    closed = deed_record(single_deed_root, "6-1", "6#1")
    assert closed["scans"] == ["scan-1.jpg", "scan-2.jpg"]

    pick_in_deed_dropdown(page, "10#1")
    expect(status(page, "10-1/scan-1.jpg · no deed")).to_be_visible()
    pick_in_deed_dropdown(page, "6#1 · Jan Modaal · pages 1-2")
    for n in [2, 3]:
        click_button(page, "next page")
        expect(status(page, f"page {n}/3")).to_be_visible()
    click_button(page, "open")
    # Reopened on its first scan, with its boxes; its file is as it was.
    expect(status(page, "editing deed-annotation-6#1 · page 1/3")).to_be_visible()
    expect(page.locator("option", has_text="H1 · page 1")).to_have_count(1)
    assert deed_record(single_deed_root, "6-1", "6#1") == closed
    assert not (single_deed_root / "10-1" / "deed-annotation-10#1.json").exists()


def test_pick_an_input_item_correct_it_and_save(
    single_deed_server, single_deed_root, page
):
    load_app_and_lock_annotator(page, single_deed_server)
    pick_in_deed_dropdown(page, "10#1")
    click_button(page, "open")
    expect(page.get_by_text(HEADER_HINT)).to_be_visible()
    save_header_or_balance_box(page, HEADER, "H1 · page 1")
    drag_box_on_page(page, 0.2, 0.3, 0.6, 0.5)
    click_button(page, "continue")
    expect(status(page, "pending 1")).to_be_visible()
    pick_in_dropdown(page, "1 · assets · 900 · Een huis")
    # The pick fills in the type, amount and description.
    expect(page.get_by_role("radio", name="assets")).to_be_checked()
    expect(text_input(page, "amount")).to_have_value("900")
    expect(text_input(page, "description")).to_have_value("Een huis")
    fill_text_input(page, "description", "Een huis met erf")
    # The item goes on: the pick and the correction stay on the next page.
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()
    expect(text_input(page, "description")).to_have_value("Een huis met erf")
    expect(page.get_by_role("radio", name="assets")).to_be_checked()
    drag_box_on_page(page, 0.2, 0.1, 0.6, 0.2)
    save_item(page)
    # Picked: last, and marked.
    expect(page.locator("option", has_text="Een huis · picked")).to_have_count(1)

    record = deed_record(single_deed_root, "10-1", "10#1")
    (item,) = record["annotation"]["assets"]
    # Only the saved values: nothing links back to the input item.
    assert set(item) == {"layout", "category", "amount", "description"}
    assert (item["amount"], item["description"]) == ("900", "Een huis met erf")
    assert [box["scan"] for box in item["layout"]] == ["scan-1.jpg", "scan-2.jpg"]
    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/3")).to_be_visible()
