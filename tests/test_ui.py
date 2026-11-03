import io

import numpy as np
import pytest
from matplotlib.colors import to_rgba
from PIL import Image

from vox_paginae.ui import (
    MAX_DISPLAY_PX,
    crop,
    draw_scan,
    scan_for_display,
    thumbnail,
)


@pytest.fixture
def scan(tmp_path):
    path = tmp_path / "scan.jpg"
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
            ("B", [5, 5, 15, 15]),
            ("A2", [10, 10, 30, 40]),
            ("L1", [50, 50, 60, 60]),
        ],
        pending=[[100, 100, 120, 130]],
    )
    drawn = [
        (p.get_bbox().bounds, p.get_edgecolor(), p.get_linestyle()) for p in ax.patches
    ]
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
        ("B", (5, 5), "tab:purple"),
        ("A2", (10, 10), "tab:blue"),
        ("L1", (50, 50), "tab:orange"),
    ]
