"""The how-to guides. Each test does one task the way an annotator does it, and writes
its page to `docs/how-to/`: its title from the `howto` marker, its intro from the
docstring, one step per helper action, each with a screenshot taken just before it.

Only the normal path, no edge cases. These tests write pages, they do not test the app:
the other tests check every behaviour (see `docs/development.md` › Write the how-to
pages).
"""

# TODO: Needs more detailed human review

import inspect
import json
import subprocess
import sys
import textwrap
from contextlib import contextmanager

import pytest
from playwright.sync_api import expect

from . import helpers
from .conftest import PROJECT, serve
from .helpers import (
    HEADER_HINT,
    click_button,
    drag_box_on_page,
    fill_text_input,
    fill_text_inputs,
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
OUTLINE_TARGETS_JS = """targets => targets.forEach(target => {
  const r = target.getBoundingClientRect();
  const box = document.createElement("div");
  box.className = "howto-target";
  box.style.cssText = "position:fixed;z-index:2147483647;pointer-events:none;" +
    "box-sizing:border-box;border:4px solid #e00;border-radius:6px;" +
    `left:${r.left - 6}px;top:${r.top - 6}px;` +
    `width:${r.width + 12}px;height:${r.height + 12}px`;
  document.body.appendChild(box);
})"""

# Where the fake deed's header and first asset are, as fractions of its scans.
FAKE_DEED_HEADER = (0.53, 0.09, 0.945, 0.28)  # scan 1, right page
# Scan 2: the balance on the left page, the items on the right one.
FAKE_DEED_BALANCE = (0.315, 0.125, 0.46, 0.27)  # its amounts only
FAKE_DEED_ASSETS = [(0.655, 0.4, 0.955, 0.575), (0.655, 0.58, 0.955, 0.69)]
FAKE_DEED_LIABILITY = (0.655, 0.715, 0.955, 0.755)
# The fake deed `1#1002`'s fourth asset spans two scans: its start at the bottom of
# scan 2's right page, its rest at the top of scan 3's left page.
FAKE_DEED_ITEM_START = (0.655, 0.8, 0.955, 0.89)
FAKE_DEED_ITEM_REST = (0.185, 0.085, 0.47, 0.18)


def wrap_markdown(text, first_indent, indent):
    """``text`` in lines of at most 100 characters, as markdownlint wants, never cut
    inside a `code span`."""
    parts = text.split("`")
    # Odd parts are code spans: their spaces become NULs, which textwrap never cuts at.
    kept = "`".join(p.replace(" ", "\0") if i % 2 else p for i, p in enumerate(parts))
    wrapped = textwrap.fill(
        kept, 100, initial_indent=first_indent, subsequent_indent=indent
    )
    return wrapped.replace("\0", " ")


class HowToRecorder:
    """The steps of one how-to: each with its text, its screenshot and, for a step
    done briefly, its sub-steps."""

    def __init__(self, page, slug):
        self.page, self.slug = page, slug
        self.screenshots = HOWTO_DIR / "screenshots" / slug
        self.screenshots.mkdir(parents=True, exist_ok=True)
        for old in self.screenshots.glob("*.jpg"):  # a step fewer leaves none behind
            old.unlink()
        self.steps = []  # (text, image, sub-steps)
        self.next_note = ""
        self.joins_next = ""  # a step recorded with `then`, waiting for the next one
        self.brief_step = None
        self.after_result = []  # markdown lines, below the result's screenshot

    def screenshot(self, name, target=None):
        # Again each time: idempotent, and it holds across a reload.
        self.page.add_style_tag(content=HIDDEN_IN_SCREENSHOTS)
        if target:
            target.first.scroll_into_view_if_needed()
            target.evaluate_all(OUTLINE_TARGETS_JS)
        self.page.screenshot(path=self.screenshots / name, type="jpeg", quality=80)
        self.page.evaluate(
            "document.querySelectorAll('.howto-target').forEach(b => b.remove())"
        )
        return f"screenshots/{self.slug}/{name}"

    def record(self, page, text, target, then):
        """Called by the helpers before each action (see `helpers.record_step`)."""
        if then:
            self.joins_next = text.removesuffix(".")
            return
        if self.joins_next:
            text = f"{self.joins_next}, then {text[0].lower()}{text[1:]}"
            self.joins_next = ""
        if self.brief_step:
            self.brief_step[2].append(text)
            return
        text, self.next_note = f"{self.next_note} {text}".strip(), ""
        name = f"step-{len(self.steps) + 1:02d}.jpg"
        self.steps.append((text, self.screenshot(name, target), []))

    def note(self, text):
        """Put ``text`` before the next step's own text."""
        self.next_note = text

    @contextmanager
    def briefly(self, text):
        """One step, ``text``, with no screenshot: the steps inside list under it."""
        self.brief_step = (text, None, [])
        self.steps.append(self.brief_step)
        yield
        self.brief_step = None

    def show_json(self, text, data):
        """Show ``text``, then ``data`` as a JSON block, below the result."""
        self.after_result += [
            "",
            wrap_markdown(text, "", ""),
            "",
            # JSON strings run long, and markdownlint takes the generated-page note's
            # indented text for a code block, so it wants no fenced one.
            "<!-- markdownlint-disable MD013 MD046 -->",
            "```json",
            json.dumps(data, indent=2, ensure_ascii=False),
            "```",
            "<!-- markdownlint-enable MD013 MD046 -->",
        ]

    def markdown(self, title, intro, test_id):
        assert not self.joins_next, f"no step after: {self.joins_next}"
        lines = [
            f"# {title}",
            "",
            intro,
            "",
            '!!! note "Generated page"',
            "",
            wrap_markdown(
                f"The browser test `{test_id}` writes this page.", "    ", "    "
            ),
            "    To change the page, change the test.",
            "",
        ]
        for number, (text, image, sub_steps) in enumerate(self.steps, 1):
            lines += [wrap_markdown(text, f"{number}. ", "    "), ""]
            if image:
                lines += [f"    ![Step {number}]({image})", ""]
            for sub_number, sub_text in enumerate(sub_steps, 1):
                lines += [wrap_markdown(sub_text, f"    {sub_number}. ", " " * 8)]
            if sub_steps:
                lines += [""]
        lines += ["The result:", "", f"![The result]({self.screenshot('result.jpg')})"]
        lines += self.after_result
        return "\n".join(lines) + "\n"


@pytest.fixture(autouse=True)
def howto(request, page):
    """Record the test's steps and, if it passes, write its how-to page."""
    title = request.node.get_closest_marker("howto").args[0]
    slug = title.lower().replace(" ", "-")
    recorder = HowToRecorder(page, slug)
    helpers.recorder = recorder.record
    yield recorder
    helpers.recorder = None
    # Set by pytest-playwright; missing when the test did not get to run.
    report = getattr(request.node, "rep_call", None)
    if not (report and report.passed):
        return
    page_text = recorder.markdown(
        title,
        inspect.cleandoc(request.function.__doc__),
        request.node.nodeid.split("[")[0],  # without the browser, as in `[chromium]`
    )
    (HOWTO_DIR / f"{slug}.md").write_text(page_text, encoding="utf-8")


@pytest.fixture
def fake_deed_root(tmp_path):
    """`<tmp>/data/` with the fake deeds `1#1001` and `1#1002`, as
    `scripts/fake_deed.py` writes them: their scans look real. The input of `1#1001` has
    a wrong amount for the first asset, 1234.56, for the annotator to correct."""
    root = tmp_path / "data"
    subprocess.run(
        [sys.executable, PROJECT / "scripts" / "fake_deed.py", root], check=True
    )
    input_path = root / "1-1001" / "input.json"
    deed_input = json.loads(input_path.read_text(encoding="utf-8"))
    deed_input["metadata"]["assets"]["items"][0]["amount"] = 1234.56
    input_path.write_text(json.dumps(deed_input), encoding="utf-8")
    return root


@pytest.fixture
def fake_deed_server(fake_deed_root):
    with serve(fake_deed_root, notebook="notebooks/single_deed_annotation.py") as url:
        yield url


def add_item_from_input(page, input_item, box):
    """Box ``input_item``, pick it in **input item**, and save it."""
    drag_box_on_page(page, *box, around="the item")
    pick_in_dropdown(page, input_item, "input item")
    save_item(page)


@pytest.mark.howto("Annotate a deed")
def test_annotate_a_deed(fake_deed_server, fake_deed_root, page, howto):
    """Open a deed, box its header, add its items and its balance. Each item is
    picked from the deed's input, boxed on the scan and corrected to what the scan
    says. On open, check the header fields the deed's input filled in.

    First start the single-deed notebook, as in
    [How to install and run](install-and-run.md#single-deed-folders).
    """
    # 16:9, as a screen: the app ends above a taller window's bottom.
    load_app_page(page, fake_deed_server, height=900)
    lock_annotator(page, "YourName")
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
    drag_box_on_page(page, *FAKE_DEED_ASSETS[0], around="the item")
    pick_in_dropdown(
        page, "1 · assets · 1234.56 · Een woonhuis met schuur en erf…", "input item"
    )
    expect(text_input(page, "amount")).to_have_value("1234.56")
    howto.note("It's possible to fix the **amount** and **description**.")
    fill_text_input(page, "amount", "4812.50")  # as on the scan
    save_item(page)
    expect(
        page.locator("option", has_text="A1 · 4812.50 · Een woonhuis")
    ).to_have_count(1)

    with howto.briefly("Add the other asset and the liability the same way:"):
        add_item_from_input(
            page,
            "2 · assets · 1250.75 · Een perceel bouwland, gelegen …",
            FAKE_DEED_ASSETS[1],
        )
        add_item_from_input(
            page,
            "3 · liabilities · 145.35 · Kosten der begrafenis",
            FAKE_DEED_LIABILITY,
        )
    expect(page.locator("option", has_text="L1 · 145.35")).to_have_count(1)

    # Box, then totals, then one click: save box saves the totals too.
    drag_box_on_page(page, *FAKE_DEED_BALANCE, around="the balance")
    fill_text_inputs(
        page,
        {"total assets": "6063.25", "total liabilities": "145.35", "total": "5917.90"},
    )
    click_button(page, "save box as balance")
    expect(page.locator("option", has_text="B1 · page 2")).to_have_count(1)

    click_button(page, "close deed")
    expect(status(page, "no deed · page 2/2")).to_be_visible()

    path = fake_deed_root / "1-1001" / "deed-annotation-1#1001.json"
    annotation = json.loads(path.read_text(encoding="utf-8"))
    # The time of the write: a fixed one, so every run writes the same page.
    annotation["annotation_metadata"]["annotation_date"] = "2026-01-05T14:30:00+01:00"
    howto.show_json(
        "Vox Paginae writes the annotation to `deed-annotation-1#1001.json`, in the"
        " deed's folder. Here it is, with an example `annotation_date`. See"
        " [Input and output](../reference/input-and-output.md) for what each field"
        " holds.",
        annotation,
    )


@pytest.mark.howto("Annotate an item that spans two scans")
def test_annotate_an_item_that_spans_two_scans(
    fake_deed_server, fake_deed_root, page, howto
):
    """An item can start at the bottom of one scan and go on at the top of the next.
    Box its start, click **continue** to keep that box, then box the rest on the next
    scan. The item is saved once, with a box on each scan.

    First start the single-deed notebook, as in
    [How to install and run](install-and-run.md#single-deed-folders).
    """
    # 16:9, as in test_annotate_a_deed.
    load_app_page(page, fake_deed_server, height=900)
    with howto.briefly("Open the deed, as in [Annotate a deed](annotate-a-deed.md):"):
        lock_annotator(page, "YourName")
        pick_in_deed_dropdown(page, "1#1002")
        click_button(page, "open")
    expect(status(page, "editing deed-annotation-1#1002 · page 1/3")).to_be_visible()
    click_button(page, "next page")
    expect(status(page, "page 2/3")).to_be_visible()

    howto.note("The item starts at the bottom of the right page.")
    drag_box_on_page(page, *FAKE_DEED_ITEM_START, around="the start of the item")
    click_button(page, "continue")
    expect(status(page, "page 2/3 · pending 1")).to_be_visible()
    click_button(page, "next page")
    expect(status(page, "page 3/3 · pending 1")).to_be_visible()
    howto.note("It goes on at the top of the left page.")
    drag_box_on_page(page, *FAKE_DEED_ITEM_REST, around="the rest of the item")
    pick_in_dropdown(
        page, "4 · assets · 185.45 · Twee koeien, drie schapen, een…", "input item"
    )
    save_item(page)
    expect(status(page, "page 3/3 · pending 0")).to_be_visible()
    click_button(page, "close deed")
    expect(status(page, "no deed · page 3/3")).to_be_visible()

    path = fake_deed_root / "1-1002" / "deed-annotation-1#1002.json"
    annotation = json.loads(path.read_text(encoding="utf-8"))["annotation"]
    assert annotation["liabilities"] == []
    (item,) = annotation["assets"]
    assert [box["scan"] for box in item["layout"]] == ["scan-002.jpg", "scan-003.jpg"]
    assert item["amount"] == "185.45"
    howto.show_json(
        "In `deed-annotation-1#1002.json`, the item has one box on each scan:", item
    )
