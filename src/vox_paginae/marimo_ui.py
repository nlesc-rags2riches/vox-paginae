"""marimo widgets for the annotator, built from the generic UI in ``vox_paginae.ui``."""

from collections.abc import Callable
from pathlib import Path

import marimo as mo
from matplotlib.axes import Axes

from vox_paginae.annotation import tagged_section_boxes
from vox_paginae.ui import book_bar_html, crop, thumbnail


def root_picker(initial_path: Path) -> mo.ui.file_browser:
    """A picker for the root folder that books are found under."""
    return mo.ui.file_browser(
        initial_path=initial_path, selection_mode="directory", multiple=False
    )


def annotator_input(name: str, locked: bool) -> mo.ui.text:
    """The annotator name input, holding ``name``; read only while ``locked``."""
    # Read-only while locked: a stray keystroke cannot change who is recorded.
    # debounce=False: lock enables while typing, as save does (no timed debounce: #11)
    return mo.ui.text(label="annotator", value=name, disabled=locked, debounce=False)


def annotator_row(
    annotator_in: mo.ui.text,
    get_annotator: Callable[[], tuple[str, bool]],
    set_annotator: Callable[[tuple[str, bool]], None],
) -> mo.Html:
    """``annotator_in`` with its lock (unlock while locked) button.

    The annotator state is a ``(name, locked)`` pair: lock stores the typed name.
    """
    name, locked = get_annotator()
    lock_btn = mo.ui.button(
        label="unlock" if locked else "lock",
        disabled=not (locked or annotator_in.value.strip()),
        on_click=lambda _: set_annotator(
            (name, False) if locked else (annotator_in.value.strip(), True)
        ),
    )
    return mo.hstack([annotator_in, lock_btn], justify="start", align="end")


def tagged_box_list_buttons(
    section: str,
    *,
    add_box: Callable[..., dict],
    delete_box: Callable[..., dict],
    get_deed_record: Callable[[], dict | None],
    save_and_show_open_deed: Callable[[dict], None],
    scan_names: list[str],
    scan_name: str,
    drawn_box: list[int] | None,
    has_pending_boxes: bool,
    editing_item: bool,
) -> tuple[mo.ui.button, mo.ui.dropdown, mo.ui.button]:
    """The save box button, tag dropdown and delete box button of ``section``.

    ``section`` is ``"header"`` or ``"balance"``. Boxes go in one at a time, on the
    deed's first scan or a later one: before it they would be outside scans. Editing an
    item locks them.
    """
    open_deed = get_deed_record()
    tag_by_option = {
        f"{tag} · page {scan_names.index(box['scan']) + 1}": tag
        for tag, box in tagged_section_boxes(open_deed, section)
    }
    tag_dropdown = mo.ui.dropdown(options=tag_by_option)

    def delete_picked_box(_):
        if tag_dropdown.value:
            save_and_show_open_deed(delete_box(get_deed_record(), tag_dropdown.value))

    save_box_btn = mo.ui.button(
        label=f"save box as {section}",
        # Not with pending boxes: the drawn box is then the item's next one.
        disabled=open_deed is None
        or editing_item
        or drawn_box is None
        or has_pending_boxes
        or scan_names.index(scan_name) < scan_names.index(open_deed["scans"][0]),
        on_click=lambda _: save_and_show_open_deed(
            add_box(get_deed_record(), scan_name, drawn_box)
        ),
    )
    # The later ones move up: the second box becomes the first.
    delete_box_btn = mo.ui.button(
        label=f"delete {section} box",
        disabled=not tag_by_option or editing_item,
        on_click=delete_picked_box,
    )
    return save_box_btn, tag_dropdown, delete_box_btn


# Quality = PNG pixels per inch of the page height: 100 is 1:1 with the screen, higher
# is sharper (on HiDPI screens) but slower.
QUALITY_DPI = [100, 150, 200, 300]


def view_sliders() -> tuple[mo.ui.slider, mo.ui.slider]:
    """The quality (dpi) and height (inches, shown at 100 px each) sliders of the page."""
    quality = mo.ui.slider(steps=QUALITY_DPI, value=150, label="quality")
    height = mo.ui.slider(4.0, 14.0, step=0.5, value=8.0, label="height")
    return quality, height


def page_view(
    ax: Axes, size: tuple[int, int], height_in: float
) -> tuple[mo.ui.matplotlib, mo.Html]:
    """The page widget for ``ax`` (from ``draw_scan``), and its view.

    The view shows the scan ``height_in`` * 100 px tall whatever its dpi. ``size`` is
    the scan's original size.
    """
    page_sel = mo.ui.matplotlib(ax, debounce=True)
    # mo.ui.matplotlib shows the PNG at its pixel size (capped at 100% width): this box
    # keeps the on-screen size fixed.
    w, h = size
    view = mo.Html(
        f'<div style="width: {round(100 * height_in * w / h)}px">{page_sel}</div>'
    )
    return page_sel, view


ZOOM_MAX = 3  # upscale cap: past 3x the scan's pixels a crop only gets blurrier


def zooms(book: Path, boxes: list[tuple[str, list[int]]]) -> mo.Html:
    """``boxes`` (scan, bbox) of ``book`` at full resolution, stacked in order."""
    return mo.vstack(
        [
            mo.image(
                crop(book / scan, bbox),
                style={
                    "width": "100%",
                    "max-width": f"{ZOOM_MAX * (bbox[2] - bbox[0])}px",
                },
            )
            for scan, bbox in boxes
        ]
    )


THUMB_SPAN = 4  # scans shown on each side of the slider position
THUMB_PX = 100


def thumbnail_strip(
    books: list[Path], book_scans: list[list[Path]], here: tuple[int, int], slider: int
) -> mo.Html:
    """The bar of all books, then thumbnails of the scans around scan ``slider``.

    ``here`` is the current (book, scan) index pair; ``slider`` counts from 0 over all
    books. Marked: ``here`` solid, ``slider`` dashed.
    """
    all_scans = [
        (b, s) for b, scans in enumerate(book_scans) for s in range(len(scans))
    ]
    # here is (len(books), 0) once all books are done: the bar marks the last scan.
    bar = book_bar_html(
        books,
        book_scans,
        all_scans.index(here) if here in all_scans else len(all_scans) - 1,
        slider,
    )

    def thumb(j):
        b, s = all_scans[j]
        style = {"outline": "3px solid currentColor"} if (b, s) == here else {}
        if j == slider:
            style = {**style, "border": "3px dashed currentColor"}
        return mo.image(
            thumbnail(book_scans[b][s], THUMB_PX),
            height=THUMB_PX,
            style=style,
            caption=f"{j + 1}" + (f" {books[b].name}" if s == 0 else ""),
        )

    span = range(
        max(0, slider - THUMB_SPAN), min(len(all_scans), slider + THUMB_SPAN + 1)
    )
    return mo.vstack(
        [mo.Html(bar), mo.hstack([thumb(j) for j in span], justify="start")]
    )
