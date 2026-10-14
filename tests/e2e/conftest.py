"""Fixtures for Playwright tests: a `marimo run` server on synthetic pages.

Recipe and selector gotchas: ~/brain/cookbook/marimo-playwright.md.
"""

import socket
import subprocess
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

PROJECT = Path(__file__).resolve().parents[2]
PAGE_W, PAGE_H = 2000, 2600


def get_free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_until_ready(port, timeout=60):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            return
        except OSError:
            time.sleep(0.3)
    raise TimeoutError(f"marimo not up on port {port}")


@pytest.fixture
def data_root(tmp_path):
    """`<tmp>/data/book1/` with three grayscale pages, like the gold scans."""
    book = tmp_path / "data" / "book1"
    book.mkdir(parents=True)
    page = np.full((PAGE_H, PAGE_W), 230, np.uint8)
    # Dark "text lines": a constant page renders black (imshow autoscales vmin == vmax).
    for y in range(200, PAGE_H - 200, 120):
        page[y : y + 30, 200 : PAGE_W - 200] = 60
    for name in ["page_01.jpg", "page_02.jpg", "page_03.jpg"]:
        Image.fromarray(page).save(book / name)
    return tmp_path / "data"


@contextmanager
def serve(data_root, *args):
    """Run the notebook as an app on `data_root` (plus notebook `args`); yields its URL."""
    port = get_free_port()
    # fmt: off
    proc = subprocess.Popen(
        ["uv", "run", "marimo", "run", "notebooks/item_block_labeler.py",
         "--port", str(port), "--headless", "--", "--data-root", str(data_root), *args],
        cwd=PROJECT,
    )
    # fmt: on
    try:
        wait_until_ready(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        proc.wait(10)


@pytest.fixture
def marimo_server(data_root):
    with serve(data_root) as url:
        yield url


@pytest.fixture
def click(page):
    """Click a button by its label. Every e2e click goes through here, so a flow
    recorder can hook in later (user-flow diagram, see the backlog)."""

    def _click(label):
        page.get_by_role("button", name=label, exact=True).click()

    return _click


# Playwright draws no pointer, so in --headed runs show one: a dot that follows the
# mouse and turns red while the button is down.
CURSOR_JS = """
window.addEventListener("DOMContentLoaded", () => {
  const dot = document.createElement("div");
  dot.style.cssText = "position:fixed;z-index:2147483647;pointer-events:none;" +
    "width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;" +
    "background:rgba(0,120,255,.5);border:2px solid #fff;left:-50px;top:-50px";
  document.body.appendChild(dot);
  const move = (e) => { dot.style.left = e.clientX + "px"; dot.style.top = e.clientY + "px"; };
  window.addEventListener("mousemove", move, true);
  window.addEventListener("mousedown", (e) => { move(e); dot.style.background = "rgba(255,0,0,.7)"; }, true);
  window.addEventListener("mouseup", () => { dot.style.background = "rgba(0,120,255,.5)"; }, true);
});
"""


@pytest.fixture(autouse=True)
def show_cursor(page, pytestconfig):
    if pytestconfig.getoption("headed"):
        page.add_init_script(CURSOR_JS)
