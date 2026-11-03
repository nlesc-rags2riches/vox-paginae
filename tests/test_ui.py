import io

import pytest
from PIL import Image

from vox_paginae.ui import crop, thumbnail


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
