"""Fixtures for Playwright tests: a `marimo run` server on synthetic pages."""

# TODO: Needs more detailed human review

import json
import socket
import subprocess
import sys
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


def deed(deed_id, aktenummer, plaats, name, date):
    """One `deeds.json` entry, with only the fields Vox Paginae reads."""
    return {
        "deed_id": deed_id,
        "aktenummer": aktenummer,
        "plaats": plaats,
        "personen": [
            {
                "naam_volledig": name,
                "datum_overlijden": date,
                "plaats_overlijden": plaats,
                "rol": "overledene",
            }
        ],
    }


DEED_3 = deed("deed-3", "3", "Oostdorp", "Jan Modaal", "1880-01-02")
DEED_7_OOST = deed("deed-7b", "7", "Oostdorp", "Jan de Wit", "1880-03-04")
DEED_7_WEST = deed("deed-7g", "7", "Westdorp", "Piet Smit", "1880-05-06")
# Two deed persons: Vox Paginae needs exactly one, so this deed cannot be used.
DEED_12 = deed("deed-12", "12", "Oostdorp", "Kees Bakker", "1880-07-08")
DEED_12["personen"].append({**DEED_12["personen"][0], "naam_volledig": "Klaas Bakker"})


def write_book(book):
    """Write three grayscale scans and a `deeds.json` into the new folder `book`."""
    book.mkdir(parents=True)
    page = np.full((PAGE_H, PAGE_W), 230, np.uint8)
    # Dark "text lines": a constant page renders black (imshow autoscales vmin == vmax).
    for y in range(200, PAGE_H - 200, 120):
        page[y : y + 30, 200 : PAGE_W - 200] = 60
    for name in ["page_01.jpg", "page_02.jpg", "page_03.jpg"]:
        Image.fromarray(page).save(book / name)
    # Not in page order, and aktenummer 7 repeats: as in a real book.
    (book / "deeds.json").write_text(
        json.dumps([DEED_7_WEST, DEED_12, DEED_3, DEED_7_OOST]), encoding="utf-8"
    )


@pytest.fixture
def data_root(tmp_path):
    """`<tmp>/data/book1/`, written by `write_book`."""
    write_book(tmp_path / "data" / "book1")
    return tmp_path / "data"


@contextmanager
def serve(data_root, *args):
    """Run the notebook as an app on `data_root` (plus notebook `args`); yields its URL."""
    port = get_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "marimo",
            "run",
            "notebooks/deed_annotation.py",
            "--port",
            str(port),
            "--headless",
            "--",
            "--data-root",
            str(data_root),
            *args,
        ],
        cwd=PROJECT,
    )
    try:
        wait_until_ready(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


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
