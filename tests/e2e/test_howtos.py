"""The how-to guides. Each test does one task the way an annotator does it, and writes
its page to `docs/how-to/`: its title from the `howto` marker, its intro from the
docstring, one step per helper action, each with a screenshot taken just before it.

Only the normal path, no edge cases: those are in the other browser tests.
"""

# TODO: Needs more detailed human review

import inspect
import subprocess
import sys

import pytest
from playwright.sync_api import expect

from . import helpers
from .conftest import PROJECT, serve
from .helpers import (
    HEADER_HINT,
    click_button,
    drag_box_on_page,
    fill_text_input,
    load_app_page,
    lock_annotator,
    pick_in_deed_dropdown,
    pick_in_dropdown,
    save_header_or_balance_box,
    save_item,
    status,
    text_input,
)

pytestmark = pytest.mark.e2e

HOWTO_DIR = PROJECT / "docs" / "how-to"
# The root line shows the test's temp folder, and toasts come and go with timing.
# `visibility: hidden` does not hide marimo's elements.
HIDDEN_IN_SCREENSHOTS = """
.marimo-cell:has(marimo-accordion), li[data-swipe-direction] {
  display: none !important;
}
"""
# A box drawn over the target, not an outline on it: that comes out faint on a marimo
# button, or clipped by its parent.
OUTLINE_TARGET_JS = """target => {
  const r = target.getBoundingClientRect();
  const box = document.createElement("div");
  box.id = "howto-target";
  box.style.cssText = "position:fixed;z-index:2147483647;pointer-events:none;" +
    "box-sizing:border-box;border:4px solid #e00;border-radius:6px;" +
    `left:${r.left - 6}px;top:${r.top - 6}px;` +
    `width:${r.width + 12}px;height:${r.height + 12}px`;
  document.body.appendChild(box);
}"""

# Where the fake deed's header and first asset are, as fractions of its scans.
FAKE_DEED_HEADER = (0.53, 0.09, 0.945, 0.28)  # scan 1, right page
FAKE_DEED_FIRST_ASSET = (0.655, 0.4, 0.955, 0.575)  # scan 2, right page


@pytest.fixture(autouse=True)
def howto(request, page):
    """Record the test's steps and, if it passes, write its how-to page."""
    title = request.node.get_closest_marker("howto").args[0]
    slug = title.lower().replace(" ", "-")
    screenshots = HOWTO_DIR / "screenshots" / slug
    screenshots.mkdir(parents=True, exist_ok=True)
    for old in screenshots.glob("*.jpg"):  # a step fewer leaves none behind
        old.unlink()
    steps = []

    def screenshot(name, target=None):
        # Again each time: idempotent, and it holds across a reload.
        page.add_style_tag(content=HIDDEN_IN_SCREENSHOTS)
        if target:
            target.scroll_into_view_if_needed()
            target.evaluate(OUTLINE_TARGET_JS)
        page.screenshot(path=screenshots / name, type="jpeg", quality=80)
        page.evaluate("document.getElementById('howto-target')?.remove()")
        return f"screenshots/{slug}/{name}"

    def record(page, text, target):
        steps.append((text, screenshot(f"step-{len(steps) + 1:02d}.jpg", target)))

    helpers.recorder = record
    yield
    helpers.recorder = None
    # Set by pytest-playwright; missing when the test did not get to run.
    report = getattr(request.node, "rep_call", None)
    if not (report and report.passed):
        return
    lines = [
        f"# {title}",
        "",
        inspect.cleandoc(request.function.__doc__),
        "",
        '!!! note "Generated page"',
        "",
        # Without the browser, as in `[chromium]`.
        f"    The browser test `{request.node.nodeid.split('[')[0]}` writes this page.",
        "    To change the page, change the test.",
        "",
    ]
    for number, (text, image) in enumerate(steps, 1):
        lines += [f"{number}. {text}", "", f"    ![Step {number}]({image})", ""]
    lines += ["The result:", "", f"![The result]({screenshot('result.jpg')})"]
    (HOWTO_DIR / f"{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def fake_deed_server(tmp_path):
    """The single-deed notebook on the fake deed `1#1001`, as `scripts/fake_deed.py`
    writes it: its scans look real."""
    root = tmp_path / "data"
    subprocess.run(
        [sys.executable, PROJECT / "scripts" / "fake_deed.py", root], check=True
    )
    with serve(root, notebook="notebooks/single_deed_annotation.py") as url:
        yield url


@pytest.mark.howto("Annotate a deed")
def test_annotate_a_deed(fake_deed_server, page):
    """Open a deed, box its header, and add one of its items: picked from the deed's
    input, boxed on the scan and corrected to what the scan says. On open, check the
    header fields the deed's input filled in.

    First start the single-deed notebook, as in
    [How to install and run](install-and-run.md#single-deed-folders).
    """
    load_app_page(page, fake_deed_server)
    lock_annotator(page)
    pick_in_deed_dropdown(page, "1#1001")
    click_button(page, "open")
    expect(status(page, "editing deed-annotation-1#1001 · page 1/2")).to_be_visible()
    # Pre-filled from the deed's input.
    expect(text_input(page, "full name")).to_have_value("Jan Modaal")
    expect(text_input(page, "date of death")).to_have_value("14 maart 1921")
    expect(text_input(page, "place of residence")).to_have_value("Oostdorp")
    expect(page.get_by_text(HEADER_HINT)).to_be_visible()
    save_header_or_balance_box(page, FAKE_DEED_HEADER, "H1 · page 1")

    click_button(page, "next page")
    expect(status(page, "page 2/2")).to_be_visible()
    pick_in_dropdown(
        page, "1 · assets · 4812.5 · Een woonhuis met schuur en erf…", "input item"
    )
    expect(text_input(page, "amount")).to_have_value("4812.5")
    drag_box_on_page(page, *FAKE_DEED_FIRST_ASSET, around="the item")
    fill_text_input(page, "amount", "4812.50")  # as on the scan
    save_item(page)
    expect(
        page.locator("option", has_text="A1 · 4812.50 · Een woonhuis")
    ).to_have_count(1)

    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/2")).to_be_visible()
