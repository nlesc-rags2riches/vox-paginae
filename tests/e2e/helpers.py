"""What a person does in the app. Every e2e user action goes through a function here,
so a recorder (how-tos, user-flow diagram) hooks in at one place. Tests call these, and
use locators only to check what they see."""

# TODO: Needs more detailed human review

import re
from collections.abc import Callable
from functools import reduce

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, expect

HEADER = (0.1, 0.05, 0.9, 0.15)  # clear of the item boxes the tests draw
HEADER_HINT = "Draw a box around the header and click save box as header"

# Set by a how-to test (see test_howtos.py) while it runs: called with the page, the
# step's text, the element the step acts on and ``then``, before each action.
recorder: Callable | None = None


def record_step(page, text, target=None, then=False):
    """Hand one step to the how-to recorder, if one runs. With ``then``, the step has
    no screenshot of its own: it joins the next step, as in "…, then click save"."""
    if recorder:
        recorder(page, text, target, then)


def text_input(page, label):
    # marimo labels are not linked to their <input> (shadow DOM): match the label text.
    # The single-deed notebook's description is a text area.
    return page.locator(
        "marimo-text, marimo-text-area", has=page.get_by_text(label, exact=True)
    ).locator("input, textarea")


def button(page, label):
    return page.get_by_role("button", name=label, exact=True)


def status(page, text):
    """The status line, e.g. "· no deed · page 1/3 · pending 0"."""
    return page.get_by_text(text)


def load_app_page(page, url, width=1600, height=1200):
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url)


def click_button(page, label):
    """Click a button by its label."""
    record_step(page, f"Click **{label}**.", button(page, label))
    button(page, label).click()


def fill_text_input(page, label, text):
    """Type into a text input and leave it, so marimo sends the value."""
    box = text_input(page, label)
    record_step(page, f"Type `{text}` in **{label}**.", box)
    box.fill(text)
    box.blur()


def fill_text_inputs(page, texts):
    """Type into several text inputs, ``{label: text}``, as one step."""
    boxes = [text_input(page, label) for label in texts]
    values = [f"`{text}` in **{label}**" for label, text in texts.items()]
    record_step(
        page,
        f"Type {', '.join(values[:-1])} and {values[-1]}.",
        reduce(Locator.or_, boxes),
    )
    for box, text in zip(boxes, texts.values(), strict=True):
        box.fill(text)
        box.blur()


def type_in_text_input_key_by_key(page, label, text):
    """Type into a text input key by key, and stay in it."""
    box = text_input(page, label)
    record_step(page, f"Type `{text}` in **{label}**.", box)
    box.press_sequentially(text, delay=50)


def pick_in_dropdown(page, label, dropdown=None):
    """Pick ``label`` in the dropdown labeled ``dropdown``; without it, in whichever
    dropdown offers ``label`` (item or book)."""
    if dropdown:
        select = page.locator(
            "marimo-dropdown", has=page.get_by_text(dropdown, exact=True)
        ).locator("select")
        record_step(page, f"Pick `{label}` in **{dropdown}**.", select)
    else:
        select = page.locator("select", has=page.locator("option", has_text=label))
        record_step(page, f"Pick `{label}`.", select)
    select.select_option(label=label)


def pick_item_type(page, item_type):
    """Pick ``assets`` or ``liabilities``."""
    radio = page.get_by_role("radio", name=item_type)
    record_step(page, f"Pick **{item_type}**.", radio)
    radio.check()


def search_deed_dropdown(page, search="", label="deed"):
    """The entries matching ``search`` in the searchable dropdown labeled ``label``;
    leaves it open."""
    # Unlike text inputs (see text_input), its <label for=…> names the button.
    dropdown = page.get_by_label(label, exact=True)
    record_step(page, f"Click **{label}** and type `{search}`.", dropdown)
    dropdown.click()
    page.get_by_placeholder("Search...").fill(search)
    return page.get_by_role("dialog").get_by_role("option")


def pick_in_deed_dropdown(page, search, label="deed"):
    """Pick the one deed matching ``search`` in the searchable dropdown labeled
    ``label``."""
    option = search_deed_dropdown(page, search, label)
    if recorder:  # its text only for the step: reading it is one more wait
        record_step(page, f"Pick `{option.inner_text()}`.", option)
    option.click()


def close_deed_dropdown(page):
    """Close a searchable dropdown left open, without picking."""
    record_step(page, "Press **Escape** to close the list.")
    page.keyboard.press("Escape")


def drag_box_on_page(page, x0, y0, x1, y1, around=None):
    """Drag a box on the page image; coordinates are fractions of the image. ``around``
    says what it boxes, as in "the header", for the how-to step."""
    canvas = page.locator("canvas").first
    record_step(
        page,
        f"Drag a box around {around} on the scan."
        if around
        else "Drag a box on the scan.",
        then=True,  # the next step's screenshot shows the box drawn
    )
    # A click can leave the canvas partly out of view. Pressing on it then scrolls the
    # page (marimo focuses it), so the position read here would no longer hold.
    canvas.scroll_into_view_if_needed()
    b = canvas.bounding_box()
    page.mouse.move(b["x"] + x0 * b["width"], b["y"] + y0 * b["height"])
    page.mouse.down()
    page.mouse.move(b["x"] + x1 * b["width"], b["y"] + y1 * b["height"], steps=10)
    page.mouse.up()


def jump_to_overall_page(page, n):
    """Type ``n`` into the "all pages" slider's number box (overall page, from 1)."""
    box = page.locator("marimo-slider", has=page.get_by_text("all pages")).locator(
        "input"
    )
    record_step(page, f"Type `{n}` in **all pages**.", box)
    box.fill(str(n))
    box.press("Enter")


def set_quality_to_highest(page):
    """Move the quality slider to its highest value."""
    quality = page.get_by_role("slider").first
    record_step(page, "Move **quality** to its highest value.", quality)
    quality.focus()
    quality.press("End")


def toggle_debug_panel(page):
    """Click the switch that shows or hides the debug panel."""
    switch = page.get_by_role("switch")
    record_step(page, "Click the **debug** switch.", switch)
    switch.click()


def save_item(page):
    """Click save, then wait until the item inputs are re-created empty: typing the
    next item before that lands in the old inputs, and the kernel never sees it."""
    click_button(page, "save")
    for label in ["amount", "description"]:
        expect(text_input(page, label)).to_have_value("")


def lock_annotator(page, name="Ann"):
    """Give the annotator name and lock it: the form needs that first."""
    expect(text_input(page, "annotator")).to_be_visible(timeout=60_000)
    fill_text_input(page, "annotator", name)
    click_button(page, "lock")


def load_app_and_lock_annotator(page, url):
    load_app_page(page, url)
    lock_annotator(page)
    expect(status(page, "no deed")).to_be_visible(timeout=60_000)


def save_header_or_balance_box(page, box, option, kind="header"):
    """Draw ``box``, save it as a ``kind`` (header or balance) box and wait for
    ``option`` in its dropdown: the page has been redrawn by then, so the next box drawn
    is kept."""
    drag_box_on_page(page, *box, around=f"the {kind}")
    click_button(page, f"save box as {kind}")
    expect(page.locator("option", has_text=option)).to_have_count(1)


def open_deed(page, search="Jan Modaal", header=True):
    """Pick the deed matching ``search``, open it on the current page and, with
    ``header``, save ``HEADER`` there as its header box."""
    pick_in_deed_dropdown(page, search)
    click_button(page, "open")
    expect(status(page, "editing deed-annotation-")).to_be_visible()
    if header:
        # Shown once open has redrawn the page: a box drawn before that is dropped.
        expect(page.get_by_text(HEADER_HINT)).to_be_visible()
        save_header_or_balance_box(page, HEADER, "H1 · page")


def pick_root(page, folder):
    """Open the root picker and tick ``folder``, a folder right under the starting root.
    Returns once the root line shows ``folder``.

    While cells re-run, the picker can be redrawn between the steps and the pick is
    lost (#152), so the steps are tried again, up to three times."""
    record_step(page, f"Click **(click to change)**, then tick **{folder}**.")
    opener = page.get_by_role("button", name=re.compile(r"\(click to change\)"))
    row = page.get_by_role("gridcell", name=folder, exact=True)
    root_line = page.get_by_text(
        re.compile(rf"[/\\]{re.escape(folder)} \(click to change\)")
    )
    tries, lost = 3, None
    for attempt in range(tries):
        try:
            # A redraw can leave the picker closed; clicking an open one closes it.
            if opener.get_attribute("aria-expanded", timeout=5_000) != "true":
                opener.click(timeout=5_000)
            # The tick box shows only while the pointer is on its row.
            row.hover(timeout=5_000)
            page.get_by_role("checkbox", name=f"Select {folder}", exact=True).click(
                timeout=5_000
            )
        except PlaywrightError as error:
            lost = error  # to a redraw: the check below decides whether to try again
        try:
            expect(root_line).to_be_visible(timeout=10_000)
            return
        except AssertionError as not_picked:
            if attempt == tries - 1:
                if lost:  # a helper bug would show only here, not as "not visible"
                    not_picked.add_note(f"last error in the pick steps: {lost}")
                raise
