"""Generic UI: images and figures to show the annotator, with no UI framework."""

import functools
import io
from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from PIL import Image

from vox_paginae.annotation import deed_path


@functools.lru_cache(maxsize=512)
def thumbnail(scan: Path, height: int = 120) -> bytes:
    """``scan`` as a small grayscale JPEG, ``height`` px tall (cached: scans never change)."""
    im = Image.open(scan)
    im.draft("L", (1, height))
    im = im.convert("L")
    im.thumbnail((im.width, height))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def crop(scan: Path, bbox: list[int]) -> bytes:
    """``bbox`` of ``scan`` at full resolution, as a grayscale JPEG."""
    im = Image.open(scan).crop(bbox).convert("L")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return buf.getvalue()


# The display goes out in a notebook output, which marimo caps (output_max_bytes in
# pyproject.toml; over it, the whole form is replaced by an error). Measured ~1.1 bytes
# per pixel as PNG on these scans, so pixels are capped and past that the quality stops
# adding any.
MAX_DISPLAY_PX = 5_000_000


def scan_for_display(
    scan: Path, height_in: float, dpi: float
) -> tuple[np.ndarray, tuple[int, int], float]:
    """``scan`` as grayscale pixels ``height_in`` inches tall at ``dpi`` px per inch.

    Returns the pixels, the scan's original size (boxes stay in original pixels) and the
    dpi used: ``dpi``, unless capped at ``MAX_DISPLAY_PX`` pixels.
    """
    im = Image.open(scan)
    size = im.size
    area = height_in**2 * size[0] / size[1]  # square inches
    dpi = min(dpi, (MAX_DISPLAY_PX / area) ** 0.5)
    px = round(height_in * dpi)
    # Decode at reduced scale (fast), then Lanczos down to exactly px tall (sharp).
    im.draft("L", (1, px))
    im = im.convert("L")
    im.thumbnail((size[0], px), Image.LANCZOS)
    return np.asarray(im), size, dpi


# By tag initial: header, balance, asset, liability.
TAG_COLOURS = {"H": "tab:green", "B": "tab:purple", "A": "tab:blue", "L": "tab:orange"}


def draw_scan(
    pixels: np.ndarray,
    size: tuple[int, int],
    height_in: float,
    dpi: float,
    saved: Iterable[tuple[str, list[int]]] = (),
    deed: Iterable[tuple[str, list[int]]] = (),
    pending: Iterable[list[int]] = (),
) -> Axes:
    """Axes showing a scan with its boxes, ``height_in`` inches tall at ``dpi``.

    ``pixels`` come from ``scan_for_display``; ``size`` is the scan's original size,
    which the axes span, so boxes drawn on them come back in original pixels. Boxes:
    ``saved`` (tag, bbox) pairs not of the open deed (all of them with no deed open),
    faded; ``deed`` (tag, bbox) pairs of the open deed, with their tag; ``pending``
    bboxes, dashed.
    """
    w, h = size
    # Figure matches the scan's aspect and axes fill it; otherwise mo.ui.matplotlib maps
    # the pointer across the whole canvas and every box comes back offset.
    fig, ax = plt.subplots(figsize=(height_in * w / h, height_in), dpi=dpi)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.imshow(
        pixels,
        extent=(0, w, h, 0),
        cmap="gray",
        vmin=0,  # fixed uint8 range: no contrast stretch, flat scans not black
        vmax=255,
    )
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.set_axis_off()

    def draw(bbox, colour, tag=None, style="-", alpha=1.0):
        x0, y0, x1, y1 = bbox
        ax.add_patch(
            plt.Rectangle(
                (x0, y0),
                x1 - x0,
                y1 - y0,
                fill=False,
                edgecolor=colour,
                linewidth=2,
                linestyle=style,
                alpha=alpha,
            )
        )
        if tag:
            ax.text(
                x0, y0, tag, color=colour, va="bottom", fontsize=14, fontweight="bold"
            )

    for tag, bbox in saved:
        draw(bbox, TAG_COLOURS[tag[0]], alpha=0.4)
    for tag, bbox in deed:
        draw(bbox, TAG_COLOURS[tag[0]], tag)
    for bbox in pending:
        draw(bbox, "grey", style="--")
    return ax


MIN_BOX_PX = 3  # a plain click still yields a zero-area box selection


def selection_box(selection) -> list[int] | None:
    """The page widget's box ``selection`` as a bbox in whole pixels.

    ``None`` for no selection, a selection that is not a box, or one under
    ``MIN_BOX_PX`` on a side (a plain click).
    """
    if not hasattr(selection, "x_min"):
        return None
    s = selection
    if s.x_max - s.x_min < MIN_BOX_PX or s.y_max - s.y_min < MIN_BOX_PX:
        return None
    return [round(s.x_min), round(s.y_min), round(s.x_max), round(s.y_max)]


def item_label(tag: str, item: dict) -> str:
    """``item``'s entry in the item dropdown: its tag, amount and description start.

    Showing them makes the list double as a typo check.
    """
    return f"{tag} · {item['amount']} · {item['description'][:30]}"


def status_text(
    book: Path,
    scan: Path,
    scan_i: int,
    n_scans: int,
    deed_record: dict | None,
    n_pending: int,
    editing: str | None = None,
    editing_header: bool = False,
    editing_balance: bool = False,
) -> str:
    """The status line, as Markdown: where the annotator is and what is being edited.

    ``scan`` is number ``scan_i`` (from 0) of the book's ``n_scans``; ``deed_record`` is
    the open deed's, or ``None``; ``editing`` is the tag of the item being edited.
    """
    deed = (
        f"editing {deed_path(book, deed_record['deed_id']).stem}"
        if deed_record
        else "no deed"
    )
    return (
        f"`{book.name}/{scan.name}` · {deed} · page {scan_i + 1}/{n_scans}"
        f" · pending {n_pending}"
        + (f" · editing {editing}" if editing else "")
        + (" · editing header" if editing_header else "")
        + (" · editing balance" if editing_balance else "")
    )


# Okabe-Ito (colour-blind safe), without black, which vanishes in dark mode.
OKABE_ITO = [
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
]


def folder_bar_html(
    books: list[Path], book_scans: list[list[Path]], here: int, slider: int
) -> str:
    """A bar of all scans of all ``books``, as HTML.

    One segment per book, sized by its scans (hover: name). Markers, in the text colour
    so they show on any segment: solid at scan ``here`` (the current one), dashed at
    scan ``slider``, both counted from 0 over all books. Not pixel-aligned with the
    slider track (wishlist).
    """
    n = sum(len(scans) for scans in book_scans)
    segments = "".join(
        f'<div title="{book.name}: {len(scans)} pages" style="flex: {len(scans)}; '
        f"background: {OKABE_ITO[k % len(OKABE_ITO)]}99; overflow: hidden; "
        f'white-space: nowrap; text-overflow: ellipsis; font-size: 11px; padding: 0 4px">'
        f"{book.name}</div>"
        for k, (book, scans) in enumerate(zip(books, book_scans))
    )

    def marker(j, css):
        return (
            '<div style="position: absolute; top: 0; bottom: 0; '
            f'left: {100 * (j + 0.5) / n}%; {css}"></div>'
        )

    return (
        '<div style="position: relative; display: flex; height: 18px">'
        + segments
        + marker(here, "border-left: 3px solid currentColor")
        + marker(slider, "border-left: 2px dashed currentColor")
        + "</div>"
    )
