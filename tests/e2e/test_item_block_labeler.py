import json
import time
import shutil

# TODO: Needs more detailed human review
import pytest
from playwright.sync_api import expect

from .conftest import PAGE_H, PAGE_W, serve

pytestmark = pytest.mark.e2e


def text_input(page, label):
    # marimo labels are not linked to their <input> (shadow DOM): match the label text.
    return page.locator("marimo-text", has=page.get_by_text(label, exact=True)).locator(
        "input"
    )


def fill(page, label, text):
    """Type into a text input and leave it, so marimo sends the value.

    A debounced input (``debounce=300``, ``delay`` in the DOM) sends only after its
    delay, and leaving it does not flush that: wait it out, or a click right after (e.g.
    save) reaches the kernel first and the typed text arrives too late.
    """
    box = text_input(page, label)
    box.fill(text)
    box.blur()
    if delay := box.get_attribute("delay"):
        page.wait_for_timeout(int(delay) + 100)


def button(page, label):
    return page.get_by_role("button", name=label, exact=True)


def choose(page, label):
    """Pick ``label`` in whichever dropdown offers it (block or person)."""
    page.locator("select", has=page.locator("option", has_text=label)).select_option(
        label=label
    )


def save(page, click):
    """Click save, then wait until the block inputs are re-created empty: typing the
    next block before that lands in the old inputs, and the kernel never sees it."""
    click("save")
    for label in ["value", "description"]:
        expect(text_input(page, label)).to_have_value("")


def status(page, text):
    """The status line, e.g. "· no person · page 1/3 · pending 0"."""
    return page.get_by_text(text)


def open_app(page, url):
    page.set_viewport_size({"width": 1600, "height": 1200})
    page.goto(url)
    expect(status(page, "no person")).to_be_visible(timeout=60_000)


def drag_box(page, x0, y0, x1, y1):
    """Drag a box on the page image; coordinates are fractions of the image."""
    b = page.locator("canvas").first.bounding_box()
    page.mouse.move(b["x"] + x0 * b["width"], b["y"] + y0 * b["height"])
    page.mouse.down()
    page.mouse.move(b["x"] + x1 * b["width"], b["y"] + y1 * b["height"], steps=10)
    page.mouse.up()


def person_record(data_root, n):
    path = data_root / "book1" / f"person-{n:04d}.json"
    return json.loads(path.read_text())["metadata"]


def fractions(bbox):
    x0, y0, x1, y1 = bbox
    return [x0 / PAGE_W, y0 / PAGE_H, x1 / PAGE_W, y1 / PAGE_H]


def test_draw_save_close_writes_person(marimo_server, data_root, page, click):
    open_app(page, marimo_server)

    drag_box(page, 0.2, 0.3, 0.6, 0.5)
    fill(page, "name", "Jan Modaal")
    fill(page, "value", "900,-")
    fill(page, "description", "Een huis")
    page.get_by_role("radio", name="assets").check()
    expect(button(page, "save")).to_be_enabled()
    save(page, click)
    expect(status(page, "editing person-0001")).to_be_visible()

    click("close person")
    expect(text_input(page, "name")).to_have_value("")
    expect(page.get_by_role("radio", name="assets")).not_to_be_checked()

    meta = person_record(data_root, 1)
    assert meta["deceased"]["full_name"] == "Jan Modaal"
    assert meta["scans"] == ["page_01.jpg"]
    (item,) = meta["assets"]["items"]
    assert (item["amount"], item["description"]) == ("900,-", "Een huis")
    assert fractions(item["layout"][0]["bbox"]) == pytest.approx(
        [0.2, 0.3, 0.6, 0.5], abs=0.01
    )


def test_continued_block_spans_two_pages(marimo_server, data_root, page, click):
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")

    drag_box(page, 0.1, 0.7, 0.9, 0.9)
    click("continue")
    expect(status(page, "pending 1")).to_be_visible()
    click("next page")
    expect(status(page, "page 2/3 · pending 1")).to_be_visible()

    drag_box(page, 0.1, 0.1, 0.9, 0.2)
    page.get_by_role("radio", name="liabilities").check()
    fill(page, "value", "1,-")  # save needs value or description
    save(page, click)
    expect(status(page, "editing person-0001 · page 2/3 · pending 0")).to_be_visible()
    click("close person")
    expect(status(page, "no person")).to_be_visible()

    meta = person_record(data_root, 1)
    assert meta["scans"] == ["page_01.jpg", "page_02.jpg"]
    assert meta["assets"]["items"] == []
    (item,) = meta["liabilities"]["items"]
    layout = item["layout"]
    assert [box["scan"] for box in layout] == ["page_01.jpg", "page_02.jpg"]
    assert fractions(layout[0]["bbox"]) == pytest.approx([0.1, 0.7, 0.9, 0.9], abs=0.01)
    assert fractions(layout[1]["bbox"]) == pytest.approx([0.1, 0.1, 0.9, 0.2], abs=0.01)


def test_restart_resumes_on_last_page_with_no_person(data_root, page, click):
    with serve(data_root) as url:
        open_app(page, url)
        fill(page, "name", "Jan Modaal")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        expect(status(page, "editing person-0001 · page 1/3")).to_be_visible()
        click("next page")
        expect(status(page, "page 2/3")).to_be_visible()
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        expect(
            status(page, "editing person-0001 · page 2/3 · pending 0")
        ).to_be_visible()
        # No close: a restart mid-deed must still land here, without reopening person 1.

    with serve(data_root) as url:
        open_app(page, url)  # waits for "no person"
        expect(status(page, "no person · page 2/3 · pending 0")).to_be_visible()
        expect(text_input(page, "name")).to_have_value("")

        fill(page, "name", "Someone Else")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.5, 0.8, 0.6)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        expect(status(page, "editing person-0002 · page 2/3")).to_be_visible()

    assert person_record(data_root, 1)["scans"] == ["page_01.jpg", "page_02.jpg"]
    second = person_record(data_root, 2)
    assert second["deceased"]["full_name"] == "Someone Else"
    assert second["scans"] == ["page_02.jpg"]


def test_buttons_are_disabled_until_their_fields_are_set(marimo_server, page, click):
    open_app(page, marimo_server)
    # prev page: page 1 is the floor, never into a previous book.
    for label in ["continue", "save", "close person", "prev page"]:
        expect(button(page, label)).to_be_disabled()

    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    expect(button(page, "continue")).to_be_enabled()
    expect(button(page, "save")).to_be_disabled()  # no type, no name
    page.get_by_role("radio", name="assets").check()
    expect(button(page, "save")).to_be_disabled()  # no name
    fill(page, "name", "Jan Modaal")
    expect(button(page, "save")).to_be_disabled()  # no value, no description
    fill(page, "value", "  ")
    expect(button(page, "save")).to_be_disabled()  # blank counts as empty
    fill(page, "value", "900,-")
    expect(button(page, "save")).to_be_enabled()
    fill(page, "name", "  ")
    expect(button(page, "save")).to_be_disabled()  # blank counts as empty
    fill(page, "name", "Jan Modaal")
    fill(page, "value", "")
    # Description alone is enough too, and enables save while typing (no blur).
    text_input(page, "description").press_sequentially("Een huis", delay=50)
    expect(button(page, "save")).to_be_enabled()

    click("continue")  # a pending box alone is enough to save
    expect(status(page, "pending 1")).to_be_visible()
    expect(button(page, "continue")).to_be_disabled()
    expect(button(page, "save")).to_be_enabled()
    save(page, click)
    expect(status(page, "editing person-0001 · page 1/3 · pending 0")).to_be_visible()
    expect(button(page, "close person")).to_be_enabled()

    drag_box(page, 0.2, 0.5, 0.8, 0.6)
    click("continue")
    expect(status(page, "pending 1")).to_be_visible()
    expect(button(page, "close person")).to_be_disabled()  # block pending
    fill(page, "value", "1,-")
    save(page, click)
    expect(status(page, "pending 0")).to_be_visible()
    expect(button(page, "close person")).to_be_enabled()
    fill(page, "name", "")
    expect(button(page, "close person")).to_be_disabled()


def test_end_of_book_closes_person_then_all_books_done(data_root, page, click):
    book2 = data_root / "book2"
    book2.mkdir()
    shutil.copy(data_root / "book1" / "page_01.jpg", book2 / "only.jpg")

    with serve(data_root) as url:
        open_app(page, url)
        click("next page")
        expect(status(page, "page 2/3")).to_be_visible()
        click("next page")
        expect(status(page, "page 3/3")).to_be_visible()

        fill(page, "name", "Jan Modaal")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        click("continue")
        expect(status(page, "pending 1")).to_be_visible()
        expect(button(page, "next page")).to_be_disabled()  # would drop the block
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        expect(
            status(page, "editing person-0001 · page 3/3 · pending 0")
        ).to_be_visible()
        expect(button(page, "next page")).to_be_enabled()

        click("next page")  # last page of book1: writes and closes person 1
        expect(page.get_by_text("book2/only.jpg", exact=True)).to_be_visible()
        expect(status(page, "no person · page 1/1")).to_be_visible()
        expect(text_input(page, "name")).to_have_value("")
        assert person_record(data_root, 1)["scans"] == ["page_03.jpg"]

        click("next page")
        expect(page.get_by_text("all books done")).to_be_visible()
    assert not list(book2.glob("person-*.json"))


def test_delete_writes_and_drops_page(marimo_server, data_root, page, click):
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")
    page.get_by_role("radio", name="assets").check()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    fill(page, "value", "1,-")  # save needs value or description
    save(page, click)
    expect(status(page, "editing person-0001 · page 1/3")).to_be_visible()
    click("next page")
    expect(status(page, "page 2/3")).to_be_visible()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    fill(page, "value", "12,-")
    fill(page, "description", "Een stoel")
    save(page, click)
    expect(status(page, "editing person-0001 · page 2/3 · pending 0")).to_be_visible()
    assert person_record(data_root, 1)["scans"] == ["page_01.jpg", "page_02.jpg"]

    options = page.locator("select option")
    # The dropdown text shows amount and description start, not just the label.
    expect(options.filter(has_text="A2 · 12,- · Een stoel")).to_have_count(1)
    choose(page, "A2 · 12,- · Een stoel")
    click("delete")
    expect(options.filter(has_text="A2")).to_have_count(0)
    meta = person_record(data_root, 1)  # written at once, no close needed
    assert meta["scans"] == ["page_01.jpg"]
    assert [box["scan"] for box in meta["assets"]["items"][0]["layout"]] == [
        "page_01.jpg"
    ]

    # The last block too: the file stays, with only the start page.
    choose(page, "A1 · 1,- ·")
    click("delete")
    expect(options.filter(has_text="A1")).to_have_count(0)
    meta = person_record(data_root, 1)
    assert meta["assets"]["items"] == [] and meta["scans"] == ["page_01.jpg"]

    fill(page, "name", "")
    expect(button(page, "delete")).to_be_disabled()  # it writes, so needs a name


def test_quality_changes_pixels_not_on_screen_size(marimo_server, page):
    open_app(page, marimo_server)
    canvas = page.locator("canvas").first
    expect(canvas).to_have_attribute("height", "1200", timeout=10_000)  # 8 in * 150
    shown = canvas.bounding_box()
    assert round(shown["height"]) == 800  # FIG_H * 100 px

    quality = page.get_by_role("slider").first
    quality.focus()
    quality.press("End")  # 300 dpi
    expect(canvas).to_have_attribute("height", "2400", timeout=10_000)
    assert canvas.bounding_box() == shown


def test_clear_pending_discards_the_pending_block(marimo_server, page, click):
    open_app(page, marimo_server)
    expect(button(page, "clear pending")).to_be_disabled()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    click("continue")
    expect(status(page, "pending 1")).to_be_visible()
    click("clear pending")  # needs no name or type: a stray continue never traps you
    expect(status(page, "pending 0")).to_be_visible()
    expect(button(page, "clear pending")).to_be_disabled()


def test_save_enables_while_typing_the_name(marimo_server, page):
    open_app(page, marimo_server)
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    page.get_by_role("radio", name="assets").check()
    fill(page, "value", "1,-")
    name = text_input(page, "name")
    name.press_sequentially("Jan Modaal", delay=50)  # no blur, no Enter
    expect(button(page, "save")).to_be_enabled()
    expect(name).to_be_focused()  # the re-render must not steal focus mid-typing
    expect(name).to_have_value("Jan Modaal")


def coloured_near(page, fx, fy, timeout=10):
    """Whether the page canvas turns non-gray within a few pixels of fraction (fx, fy)."""
    js = """(c, [fx, fy]) => {
      const x = Math.round(fx * c.width), y = Math.round(fy * c.height);
      const d = c.getContext("2d").getImageData(x, y - 6, 1, 13).data;
      for (let i = 0; i < d.length; i += 4)
        if (Math.max(d[i], d[i + 1], d[i + 2]) - Math.min(d[i], d[i + 1], d[i + 2]) > 20)
          return true;
      return false;
    }"""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if page.locator("canvas").first.evaluate(js, [fx, fy]):
            return True
        time.sleep(0.2)
    return False


def test_saved_boxes_stay_visible_after_close_and_restart(data_root, page, click):
    with serve(data_root) as url:
        open_app(page, url)
        assert not coloured_near(page, 0.4, 0.3, timeout=1)  # sanity: blank page
        fill(page, "name", "Jan Modaal")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.3, 0.6, 0.5)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        click("close person")
        # Leave and come back, so a lingering selection cannot pass for the box.
        click("next page")
        expect(status(page, "no person · page 2/3")).to_be_visible()
        click("prev page")
        expect(status(page, "no person · page 1/3")).to_be_visible()
        assert coloured_near(page, 0.4, 0.3)  # closed person's box, faded

    with serve(data_root) as url:
        open_app(page, url)
        expect(status(page, "no person · page 1/3")).to_be_visible()
        assert coloured_near(page, 0.4, 0.3)


def jump_to(page, n):
    """Type ``n`` into the "all pages" slider's number box (overall page, from 1)."""
    box = page.locator("marimo-slider", has=page.get_by_text("all pages")).locator(
        "input"
    )
    box.fill(str(n))
    box.press("Enter")


def test_jump_is_view_only_while_a_person_is_open(data_root, page, click):
    book2 = data_root / "book2"
    book2.mkdir()
    shutil.copy(data_root / "book1" / "page_01.jpg", book2 / "only.jpg")

    with serve(data_root) as url:
        open_app(page, url)
        fill(page, "name", "Jan Modaal")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        expect(status(page, "editing person-0001 · page 1/3")).to_be_visible()
        jump_to(page, 4)
        expect(page.get_by_text("4 book2")).to_be_visible()  # the strip follows
        expect(
            page.get_by_text("/ 4 · book2/only.jpg")
        ).to_be_visible()  # total, target
        expect(page.locator('[title="book2: 1 pages"]')).to_be_visible()  # folder bar
        expect(button(page, "go")).to_be_disabled()  # view only: person 1 is open

        click("close person")
        expect(button(page, "go")).to_be_enabled()
        click("go")
        expect(page.get_by_text("book2/only.jpg", exact=True)).to_be_visible()
        fill(page, "name", "Bart")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        click("close person")
        expect(status(page, "no person")).to_be_visible()

        # Back to book1, then next page into book2, which already has person-0001:
        # the next save must add person-0002, not overwrite it.
        jump_to(page, 1)
        click("go")
        expect(page.get_by_text("book1/page_01.jpg", exact=True)).to_be_visible()
        for n in [2, 3]:
            click("next page")
            expect(status(page, f"page {n}/3")).to_be_visible()
        click("next page")
        expect(page.get_by_text("book2/only.jpg", exact=True)).to_be_visible()
        fill(page, "name", "Cor")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.5, 0.8, 0.6)
        fill(page, "value", "1,-")  # save needs value or description
        save(page, click)
        expect(status(page, "editing person-0002 · page 1/1")).to_be_visible()

    names = {
        p.name: json.loads(p.read_text())["metadata"]["deceased"]["full_name"]
        for p in book2.glob("person-*.json")
    }
    assert names == {"person-0001.json": "Bart", "person-0002.json": "Cor"}


def test_edit_replaces_block_in_place(marimo_server, data_root, page, click):
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")
    page.get_by_role("radio", name="assets").check()
    for value in ["1,-", "2,-"]:
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        fill(page, "value", value)
        save(page, click)
    expect(button(page, "cancel edit")).to_be_disabled()

    choose(page, "A1 · 1,- ·")
    click("edit")
    # The block is loaded into the inputs, its box into pending.
    expect(status(page, "pending 1 · editing A1")).to_be_visible()
    expect(text_input(page, "value")).to_have_value("1,-")
    expect(button(page, "delete")).to_be_disabled()
    expect(button(page, "close person")).to_be_disabled()

    fill(page, "value", "10,-")
    fill(page, "description", "Een huis")
    save(page, click)
    expect(status(page, "pending 0")).to_be_visible()
    items = person_record(data_root, 1)["assets"]["items"]
    assert [i["amount"] for i in items] == ["10,-", "2,-"]  # A1 stays A1
    assert items[0]["description"] == "Een huis"

    # cancel edit drops the loaded block and leaves the file alone.
    choose(page, "A2 · 2,- ·")
    click("edit")
    expect(status(page, "editing A2")).to_be_visible()
    click("cancel edit")
    expect(status(page, "pending 0")).to_be_visible()
    expect(text_input(page, "value")).to_have_value("")
    assert person_record(data_root, 1)["assets"]["items"] == items


def test_debug_panel_shows_the_file(data_root, page, click):
    with serve(data_root, "--debug") as url:
        open_app(page, url)
        expect(page.get_by_text("DEBUG PANE")).to_be_visible()
        expect(page.get_by_text("no file yet")).to_be_visible()
        fill(page, "name", "Jan Modaal")
        page.get_by_role("radio", name="assets").check()
        drag_box(page, 0.2, 0.2, 0.8, 0.3)
        fill(page, "value", "12,-")
        save(page, click)
        expect(page.get_by_text("person-0001.json", exact=True)).to_be_visible()
        expect(page.get_by_text('"12,-"')).to_be_visible()

        choose(page, "A1 · 12,- ·")
        click("delete")  # every write refreshes the panel
        expect(page.get_by_text('"12,-"')).to_have_count(0)

        debug = page.get_by_role("switch")
        debug.click()  # hides the panel for a demo; the switch itself stays
        expect(page.get_by_text("DEBUG PANE")).to_have_count(0)
        expect(debug).to_be_visible()
        debug.click()
        expect(page.get_by_text("DEBUG PANE")).to_be_visible()


def test_no_debug_panel_by_default(marimo_server, page):
    open_app(page, marimo_server)
    expect(text_input(page, "name")).to_be_visible()
    expect(page.get_by_text("DEBUG PANE")).to_have_count(0)
    expect(page.get_by_role("switch")).to_have_count(0)


def test_pick_right_after_close_person_is_kept(marimo_server, page, click):
    # The status line changes only together with the rebuilt dropdown. Before, it said
    # "no person" while the old dropdown still showed person 1 picked: picking it again
    # sent nothing, and the rebuilt dropdown then came in empty.
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")
    page.get_by_role("radio", name="assets").check()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    fill(page, "value", "1,-")
    save(page, click)
    choose(page, "person-0001 · Jan Modaal · page 1")

    click("close person")
    expect(status(page, "no person")).to_be_visible()
    choose(page, "person-0001 · Jan Modaal · page 1")
    # Check once the rebuilds are surely over (~350 ms after the click when measured).
    page.wait_for_timeout(1000)
    assert button(page, "go to person").is_enabled()


def test_go_to_person_moves_to_their_start_page(marimo_server, data_root, page, click):
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")
    page.get_by_role("radio", name="assets").check()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    fill(page, "value", "1,-")  # save needs value or description
    save(page, click)
    choose(page, "person-0001 · Jan Modaal · page 1")
    expect(button(page, "go to person")).to_be_disabled()  # person 1 is open

    click("close person")
    for n in [2, 3]:
        click("next page")
        expect(status(page, f"page {n}/3")).to_be_visible()
    choose(page, "person-0001 · Jan Modaal · page 1")
    click("go to person")
    expect(
        status(page, "no person · page 1/3")
    ).to_be_visible()  # moves, writes nothing
    assert len(list((data_root / "book1").glob("person-*.json"))) == 1


def test_reopen_rewrites_the_same_file(marimo_server, data_root, page, click):
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")
    page.get_by_role("radio", name="assets").check()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    fill(page, "value", "1,-")
    save(page, click)
    choose(page, "person-0001 · Jan Modaal · page 1")
    expect(button(page, "reopen")).to_be_disabled()  # person 1 is open

    click("close person")
    click("next page")
    expect(status(page, "no person · page 2/3")).to_be_visible()
    choose(page, "person-0001 · Jan Modaal · page 1")
    click("reopen")  # back on the start page, name prefilled
    expect(status(page, "editing person-0001 · page 1/3")).to_be_visible()
    expect(text_input(page, "name")).to_have_value("Jan Modaal")

    choose(page, "A1 · 1,- ·")
    click("edit")
    expect(status(page, "editing A1")).to_be_visible()
    expect(text_input(page, "value")).to_have_value("1,-")  # inputs rebuilt
    fill(page, "value", "10,-")
    save(page, click)
    fill(page, "name", "Jan Modaal-Smit")
    click("close person")
    expect(status(page, "no person")).to_be_visible()

    assert [p.name for p in (data_root / "book1").glob("person-*.json")] == [
        "person-0001.json"
    ]
    meta = person_record(data_root, 1)
    assert meta["deceased"]["full_name"] == "Jan Modaal-Smit"
    assert [i["amount"] for i in meta["assets"]["items"]] == ["10,-"]


def test_delete_person_needs_confirmation(marimo_server, data_root, page, click):
    open_app(page, marimo_server)
    fill(page, "name", "Jan Modaal")
    page.get_by_role("radio", name="assets").check()
    drag_box(page, 0.2, 0.2, 0.8, 0.3)
    fill(page, "value", "1,-")
    save(page, click)
    choose(page, "person-0001 · Jan Modaal · page 1")
    expect(button(page, "delete person")).to_be_disabled()  # person 1 is open

    click("close person")
    expect(status(page, "no person")).to_be_visible()
    choose(page, "person-0001 · Jan Modaal · page 1")
    click("delete person")
    click("cancel")  # writes nothing
    expect(button(page, "delete person")).to_be_enabled()
    assert (data_root / "book1" / "person-0001.json").exists()

    click("delete person")
    click("confirm delete person-0001")
    expect(button(page, "delete person")).to_be_disabled()  # dropdown rebuilt, empty
    expect(page.locator("option", has_text="person-0001")).to_have_count(0)
    assert not list((data_root / "book1").glob("person-*.json"))


def test_deed_dropdown_shows_the_picked_deed(marimo_server, page):
    open_app(page, marimo_server)
    # Searchable, so not a <select>: a button opening a list of role "option".
    page.get_by_test_id("marimo-plugin-searchable-dropdown").get_by_role(
        "button"
    ).click()
    # By aktenummer, then place: deeds.json is in neither order.
    expect(page.get_by_role("dialog").get_by_role("option")).to_have_text(
        [
            "3 · Oostdorp · Jan Modaal",
            "7 · Oostdorp · Jan de Wit",
            "7 · Westdorp · Piet Smit",
        ]
    )
    page.get_by_placeholder("Search...").fill("Westdorp")
    page.get_by_role("dialog").get_by_role("option").click()
    expect(page.get_by_text("Piet Smit · died 1880-05-06 in Westdorp")).to_be_visible()
