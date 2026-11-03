"""marimo widgets for the annotator, built from the generic UI in ``vox_paginae.ui``."""

from collections.abc import Callable
from pathlib import Path

import marimo as mo
from matplotlib.axes import Axes

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
