import io
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PIL import Image

from vox_paginae.ui import (
    MAX_DISPLAY_PX,
    book_bar_html,
    crop,
    draw_scan,
    item_option,
    scan_for_display,
    selection_box,
    status_text,
    thumbnail,
)


# Each scan format is shown the same way.
@pytest.fixture(params=["scan.jpg", "scan.jpeg", "scan.png", "scan.tif", "scan.tiff"])
def scan(tmp_path, request):
    path = tmp_path / request.param
    Image.new("RGB", (600, 800), "white").save(path)
    return path


def test_thumbnail_is_a_grayscale_jpeg_of_the_given_height(scan):
    im = Image.open(io.BytesIO(thumbnail(scan, 100)))
    assert (im.format, im.mode, im.height) == ("JPEG", "L", 100)
    assert im.width == 75  # keeps the scan's 3:4 aspect


def test_crop_is_a_grayscale_jpeg_of_the_box_at_full_resolution(scan):
    im = Image.open(io.BytesIO(crop(scan, [10, 20, 210, 70])))
    assert (im.format, im.mode, im.size) == ("JPEG", "L", (200, 50))


def test_scan_for_display_keeps_original_size_and_shows_height_at_dpi(scan):
    pixels, size, dpi = scan_for_display(scan, height_in=4, dpi=100)
    assert size == (600, 800)  # boxes stay in original pixels
    assert pixels.shape == (400, 300)  # 4 in at 100 px/in, grayscale
    assert dpi == 100


def test_scan_for_display_caps_resolution_on_a_large_scan(tmp_path):
    scan = tmp_path / "large.jpg"
    Image.new("RGB", (3000, 4000), "white").save(scan)
    pixels, size, dpi = scan_for_display(scan, height_in=14, dpi=300)
    assert size == (3000, 4000)
    # 14 in tall at 3:4 is 147 sq in; at 300 dpi that is ~13 M px, 5 M allows ~184.4 dpi
    assert MAX_DISPLAY_PX == 5_000_000
    assert dpi == pytest.approx(184.4, abs=0.1)
    assert pixels.size <= MAX_DISPLAY_PX
    assert pixels.shape[0] == round(14 * dpi)


def test_draw_scan_fills_a_figure_of_the_scans_aspect():
    pixels = np.zeros((400, 300), np.uint8)
    ax = draw_scan(pixels, (600, 800), height_in=4, dpi=150)
    fig = ax.figure
    assert isinstance(fig, Figure)
    assert tuple(fig.get_size_inches()) == (3, 4)
    assert fig.dpi == 150
    # axes fill the figure and span the scan in original pixels, y down
    assert tuple(ax.get_position().bounds) == (0, 0, 1, 1)
    assert ax.get_xlim() == (0, 600)
    assert ax.get_ylim() == (800, 0)


def test_draw_scan_draws_saved_faded_deed_tagged_and_pending_dashed():
    pixels = np.zeros((400, 300), np.uint8)
    ax = draw_scan(
        pixels,
        (600, 800),
        height_in=4,
        dpi=100,
        saved=[("H", [0, 0, 10, 10])],
        deed=[
            ("B1", [5, 5, 15, 15]),
            ("A2", [10, 10, 30, 40]),
            ("L1", [50, 50, 60, 60]),
        ],
        pending=[[100, 100, 120, 130]],
    )
    rects = [p for p in ax.patches if isinstance(p, Rectangle)]
    assert len(rects) == len(ax.patches)
    drawn = [(p.get_bbox().bounds, p.get_edgecolor(), p.get_linestyle()) for p in rects]
    assert drawn == [
        ((0, 0, 10, 10), to_rgba("tab:green", 0.4), "-"),  # other deeds' saved
        ((5, 5, 10, 10), to_rgba("tab:purple"), "-"),  # open deed: balance
        ((10, 10, 20, 30), to_rgba("tab:blue"), "-"),  # open deed: asset
        ((50, 50, 10, 10), to_rgba("tab:orange"), "-"),  # open deed: liability
        ((100, 100, 20, 30), to_rgba("grey"), "--"),  # pending
    ]
    # only the open deed's boxes carry their tag, at the box's top-left, in its colour
    tags = [(t.get_text(), t.get_position(), t.get_color()) for t in ax.texts]
    assert tags == [
        ("B1", (5, 5), "tab:purple"),
        ("A2", (10, 10), "tab:blue"),
        ("L1", (50, 50), "tab:orange"),
    ]


def box_selection(x_min, y_min, x_max, y_max):
    # Stands in for mo.ui.matplotlib's BoxSelection: selection_box reads only these fields.
    return SimpleNamespace(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)


def test_selection_box_is_in_whole_pixels():
    assert selection_box(box_selection(10.4, 20.6, 110.3, 70.2)) == [10, 21, 110, 70]


def test_a_plain_click_or_no_selection_draws_no_box():
    assert selection_box(box_selection(50, 50, 50, 50)) is None  # a click
    assert selection_box(box_selection(50, 50, 52, 90)) is None  # under 3 px wide
    assert selection_box(None) is None


def test_item_option_shows_tag_amount_and_description_start():
    item = {
        "amount": "f 120,-",
        "description": "Een huis en erf aan de Hoogstraat te Ergens",
    }
    assert item_option("A1", item) == "A1 · f 120,- · Een huis en erf aan de Hoogstr"


def test_status_line_with_no_deed_open():
    text = status_text(Path("books/b1"), Path("books/b1/s003.jpg"), 2, 40, None, 0)
    assert text == "`b1/s003.jpg` · no deed · page 3/40 · pending 0"


def test_status_line_names_the_open_deed_and_what_is_being_edited():
    deed_record = {"deed_id": "d7"}
    status: dict = {
        "book": Path("b1"),
        "scan": Path("b1/s003.jpg"),
        "scan_i": 2,
        "n_scans": 40,
        "deed_record": deed_record,
        "n_pending": 1,
    }
    assert status_text(**status, editing="A2") == (
        "`b1/s003.jpg` · editing deed-annotation-d7 · page 3/40 · pending 1"
        " · editing A2"
    )


def test_book_bar_has_a_segment_per_book_and_marks_here_and_the_slider():
    books = [Path("b1"), Path("b2")]
    book_scans = [
        [Path("b1/1.jpg"), Path("b1/2.jpg"), Path("b1/3.jpg")],
        [Path("b2/1.jpg")],
    ]
    html = book_bar_html(books, book_scans, here=1, slider=3)
    segments = re.findall(r'title="([^"]+)" style="flex: (\d+);', html)
    assert segments == [("b1: 3 pages", "3"), ("b2: 1 pages", "1")]
    # each marker sits at the middle of its scan's quarter of the bar
    markers = re.findall(r"left: ([\d.]+)%; border-left: (\w+) (\w+)", html)
    assert markers == [("37.5", "3px", "solid"), ("87.5", "2px", "dashed")]
