"""What a person does in the app. Every e2e user action goes through a function here,
so a recorder (how-tos, user-flow diagram) hooks in at one place. Tests call these, and
use locators only to check what they see."""

# TODO: Needs more detailed human review

from playwright.sync_api import expect

HEADER = (0.1, 0.05, 0.9, 0.15)  # clear of the item boxes the tests draw
HEADER_HINT = "Draw a box around the header and click save box as header"


def text_input(page, label):
    # marimo labels are not linked to their <input> (shadow DOM): match the label text.
    return page.locator("marimo-text", has=page.get_by_text(label, exact=True)).locator(
        "input"
    )


def button(page, label):
    return page.get_by_role("button", name=label, exact=True)


def status(page, text):
    """The status line, e.g. "· no deed · page 1/3 · pending 0"."""
    return page.get_by_text(text)


def visit(page, url):
    page.set_viewport_size({"width": 1600, "height": 1200})
    page.goto(url)


def click(page, label):
    """Click a button by its label."""
    button(page, label).click()


def fill(page, label, text):
    """Type into a text input and leave it, so marimo sends the value."""
    box = text_input(page, label)
    box.fill(text)
    box.blur()


def type_keys(page, label, text):
    """Type into a text input key by key, and stay in it."""
    text_input(page, label).press_sequentially(text, delay=50)


def choose(page, label):
    """Pick ``label`` in whichever dropdown offers it (item or book)."""
    page.locator("select", has=page.locator("option", has_text=label)).select_option(
        label=label
    )


def pick_item_type(page, item_type):
    """Pick ``assets`` or ``liabilities``."""
    page.get_by_role("radio", name=item_type).check()


def deed_options(page, search="", label="deed"):
    """The entries matching ``search`` in the searchable dropdown labeled ``label``;
    leaves it open."""
    # Unlike text inputs (see text_input), its <label for=…> names the button.
    page.get_by_label(label, exact=True).click()
    page.get_by_placeholder("Search...").fill(search)
    return page.get_by_role("dialog").get_by_role("option")


def pick_deed(page, search, label="deed"):
    """Pick the one deed matching ``search`` in the searchable dropdown labeled
    ``label``."""
    deed_options(page, search, label).click()


def close_dropdown(page):
    """Close a searchable dropdown left open, without picking."""
    page.keyboard.press("Escape")


def drag_box(page, x0, y0, x1, y1):
    """Drag a box on the page image; coordinates are fractions of the image."""
    b = page.locator("canvas").first.bounding_box()
    page.mouse.move(b["x"] + x0 * b["width"], b["y"] + y0 * b["height"])
    page.mouse.down()
    page.mouse.move(b["x"] + x1 * b["width"], b["y"] + y1 * b["height"], steps=10)
    page.mouse.up()


def jump_to(page, n):
    """Type ``n`` into the "all pages" slider's number box (overall page, from 1)."""
    box = page.locator("marimo-slider", has=page.get_by_text("all pages")).locator(
        "input"
    )
    box.fill(str(n))
    box.press("Enter")


def max_quality(page):
    """Move the quality slider to its highest value."""
    quality = page.get_by_role("slider").first
    quality.focus()
    quality.press("End")


def toggle_debug(page):
    """Click the switch that shows or hides the debug panel."""
    page.get_by_role("switch").click()


def save(page):
    """Click save, then wait until the item inputs are re-created empty: typing the
    next item before that lands in the old inputs, and the kernel never sees it."""
    click(page, "save")
    for label in ["amount", "description"]:
        expect(text_input(page, label)).to_have_value("")


def lock_annotator(page, name="Ann"):
    """Give the annotator name and lock it: the form needs that first."""
    expect(text_input(page, "annotator")).to_be_visible(timeout=60_000)
    fill(page, "annotator", name)
    click(page, "lock")


def open_app(page, url):
    visit(page, url)
    lock_annotator(page)
    expect(status(page, "no deed")).to_be_visible(timeout=60_000)


def save_box(page, box, option, kind="header"):
    """Draw ``box``, save it as a ``kind`` (header or balance) box and wait for
    ``option`` in its dropdown: the page has been redrawn by then, so the next box drawn
    is kept."""
    drag_box(page, *box)
    click(page, f"save box as {kind}")
    expect(page.locator("option", has_text=option)).to_have_count(1)


def open_deed(page, search="Jan Modaal", header=True):
    """Pick the deed matching ``search``, open it on the current page and, with
    ``header``, save ``HEADER`` there as its header box."""
    pick_deed(page, search)
    click(page, "open")
    expect(status(page, "editing deed-annotation-")).to_be_visible()
    if header:
        # Shown once open has redrawn the page: a box drawn before that is dropped.
        expect(page.get_by_text(HEADER_HINT)).to_be_visible()
        save_box(page, HEADER, "H1 · page")
