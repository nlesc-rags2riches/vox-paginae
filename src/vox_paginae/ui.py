"""Generic UI: images to show the annotator, with no UI framework."""

import functools
import io
from pathlib import Path

from PIL import Image


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
