"""Generic UI: images to show the annotator, with no UI framework."""

import functools
import io
from pathlib import Path

import numpy as np
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


# The display goes out in a notebook output, which marimo caps (output_max_bytes in
# pyproject.toml; over it, the whole form is replaced by an error). Measured ~1.1 bytes
# per pixel as PNG on these scans, so pixels are capped and past that the quality stops
# adding any.
MAX_DISPLAY_PX = 5_000_000


def scan_for_display(
    scan: Path, height: float, quality: float
) -> tuple[np.ndarray, tuple[int, int], float]:
    """``scan`` as grayscale pixels ``height`` inches tall at ``quality`` px per inch.

    Returns the pixels, the scan's original size (boxes stay in original pixels) and the
    px per inch used: ``quality``, unless capped at ``MAX_DISPLAY_PX`` pixels.
    """
    im = Image.open(scan)
    size = im.size
    area = height**2 * size[0] / size[1]  # square inches
    dpi = min(quality, (MAX_DISPLAY_PX / area) ** 0.5)
    px = round(height * dpi)
    # Decode at reduced scale (fast), then Lanczos down to exactly px tall (sharp).
    im.draft("L", (1, px))
    im = im.convert("L")
    im.thumbnail((size[0], px), Image.LANCZOS)
    return np.asarray(im), size, dpi
