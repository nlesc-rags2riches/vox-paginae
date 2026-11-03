import io

import pytest
from PIL import Image

from vox_paginae.ui import crop, scan_for_display, thumbnail


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


def test_scan_for_display_keeps_original_size_and_shows_height_at_quality(scan):
    pixels, size, dpi = scan_for_display(scan, height=4, quality=100)
    assert size == (600, 800)  # boxes stay in original pixels
    assert pixels.shape == (400, 300)  # 4 in at 100 px/in, grayscale
    assert dpi == 100


def test_scan_for_display_caps_resolution_on_a_large_scan(tmp_path):
    scan = tmp_path / "large.jpg"
    Image.new("RGB", (3000, 4000), "white").save(scan)
    pixels, size, dpi = scan_for_display(scan, height=14, quality=300)
    assert size == (3000, 4000)
    assert dpi < 300
    assert pixels.size <= 5_000_000  # 14 in at 300 px/in would be ~11 M
    assert pixels.shape[0] == round(14 * dpi)
