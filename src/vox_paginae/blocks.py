"""Item-block labeling: books, pages, person records and their blocks (non-UI part)."""

# TODO: Split this into appropriate files and detailed human review

import copy
import functools
import io
import json
import uuid
from pathlib import Path

from PIL import Image


def find_books(root: Path) -> list[Path]:
    """Every folder under ``root`` that directly contains ``*.jpg``, in sorted path order."""
    return sorted({p.parent for p in Path(root).rglob("*.jpg")})


def list_pages(book: Path) -> list[Path]:
    """The ``*.jpg`` in ``book``, sorted by filename as plain strings."""
    return sorted(Path(book).glob("*.jpg"), key=lambda p: p.name)


def next_page(book_page: tuple[int, int], page_counts: list[int]) -> tuple[int, int]:
    """Advance ``(book, page)``; past a book's last page go to the next book's first.

    ``(len(page_counts), 0)`` means all books are done; it stays put from there.
    """
    book, page = book_page
    if book >= len(page_counts):
        return book_page
    if page + 1 < page_counts[book]:
        return (book, page + 1)
    return (book + 1, 0)


TYPES = ("assets", "liabilities")


def new_person_record(first_scan: str) -> dict:
    """A blank person record starting on ``first_scan``, in the gold ``metadata`` shape."""
    return {
        "metadata": {
            "deed_id": str(uuid.uuid4()),
            "aktenummer": None,
            "tax_office": None,
            "total": None,
            "deceased": {
                "full_name": None,
                "date_of_death": None,
                "place_of_residence": None,
                "place_of_death": None,
            },
            "scans": [first_scan],
            "assets": {"total": None, "items": []},
            "liabilities": {"total": None, "items": []},
        }
    }


def _with_scans(person_record: dict) -> dict:
    """Recompute ``scans``: the start page (always first) plus every page with an item."""
    meta = person_record["metadata"]
    start = meta["scans"][0]
    used = {
        box["scan"]
        for t in TYPES
        for item in meta[t]["items"]
        for box in item["layout"]
    }
    meta["scans"] = [start, *sorted(used - {start})]
    return person_record


def add_block(
    person_record: dict,
    type_: str,
    category: str,
    amount: str,
    description: str,
    layout_boxes: list[tuple[str, list[int]]],
) -> dict:
    """Return a copy of ``person_record`` with a new ``type_`` item.

    Each ``(scan, bbox)`` in ``layout_boxes`` becomes one ``layout`` entry.

    ``amount`` and ``description`` are stored as typed; at least one must be non-blank.
    An empty ``category`` becomes ``None``.
    """
    if type_ not in TYPES:
        raise ValueError(f"type must be one of {TYPES}, got {type_!r}")
    if not layout_boxes:
        raise ValueError("a block needs at least one box")
    if not (amount.strip() or description.strip()):
        raise ValueError("a block needs an amount or a description")
    person_record = copy.deepcopy(person_record)
    meta = person_record["metadata"]
    if not any(meta[t]["items"] for t in TYPES):
        # The first block sets the start page to its earliest box, not the page it was
        # saved on: a continued block saved on page 2 can start on page 1.
        meta["scans"] = [min(scan for scan, _ in layout_boxes)]
    meta[type_]["items"].append(
        {
            "category": category or None,
            "amount": amount,
            "description": description,
            "layout": [
                {
                    "scan": scan,
                    "bbox": [int(v) for v in bbox],
                    "pagexml_link": None,
                    "pagexml_baseline_ids": None,
                }
                for scan, bbox in layout_boxes
            ],
        }
    )
    return _with_scans(person_record)


def block_labels(person_record: dict | None) -> list[tuple[str, dict]]:
    """``(label, item)`` for every item: ``A1, A2…`` for assets, then ``L1, L2…``.

    ``None`` (no current person) has no items.
    """
    if person_record is None:
        return []
    return [
        (f"{t[0].upper()}{i}", item)
        for t in TYPES
        for i, item in enumerate(person_record["metadata"][t]["items"], start=1)
    ]


def split_label(label: str) -> tuple[str, int]:
    """``"A2"`` -> ``("assets", 1)``: the item's type and its index in that list."""
    return {"A": "assets", "L": "liabilities"}[label[0]], int(label[1:]) - 1


def delete_block(person_record: dict, label: str) -> dict:
    """Return a copy of ``person_record`` without the item called ``label`` (e.g. ``"A2"``)."""
    type_, i = split_label(label)
    person_record = copy.deepcopy(person_record)
    del person_record["metadata"][type_]["items"][i]
    return _with_scans(person_record)


def replace_block(
    person_record: dict,
    label: str,
    type_: str,
    category: str,
    amount: str,
    description: str,
    layout_boxes: list[tuple[str, list[int]]],
) -> dict:
    """``add_block`` in place of the item called ``label``, with the same checks.

    It keeps its position (``A2`` stays ``A2``) unless ``type_`` changes; then it goes
    last of ``type_``. Replacing the only item sets the start page again, as a first
    block does.
    """
    old_type, i = split_label(label)
    person_record = add_block(
        delete_block(person_record, label),
        type_,
        category,
        amount,
        description,
        layout_boxes,
    )
    if type_ == old_type:
        items = person_record["metadata"][type_]["items"]
        items.insert(i, items.pop())
    return person_record


def person_path(book: Path, person_id: int) -> Path:
    """``<book>/person-NNNN.json``; ``person_id`` counts from 1 within each book."""
    return Path(book) / f"person-{person_id:04d}.json"


def save_person_record(
    book: Path, person_id: int, person_record: dict, full_name: str, date_of_death: str
) -> Path:
    """Write ``person_record`` with its deceased name and date; refuse an empty name."""
    if not full_name.strip():
        raise ValueError("full_name is required")
    person_record = copy.deepcopy(person_record)
    person_record["metadata"]["deceased"]["full_name"] = full_name.strip()
    person_record["metadata"]["deceased"]["date_of_death"] = (
        date_of_death.strip() or None
    )
    path = person_path(book, person_id)
    tmp = path.with_suffix(".json.tmp")  # write-then-rename: a crash never truncates
    tmp.write_text(json.dumps(person_record, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    return path


def load_person_records(book: Path) -> dict[int, dict]:
    """``{person_id: person_record}`` for every ``person-NNNN.json`` in ``book``, by id."""
    return {
        int(p.stem.removeprefix("person-")): json.loads(p.read_text())
        for p in sorted(Path(book).glob("person-*.json"))
    }


def person_choices(book: Path) -> dict[str, int]:
    """``{"person-0002 · Antonia Spiering · pages 22-24": start page index}`` per file.

    Page numbers count from 1, as in the status line; the value is the index of the
    person's start page (``scans[0]``) in ``list_pages(book)``.
    """
    page_index = {p.name: i for i, p in enumerate(list_pages(book))}
    choices = {}
    for person_id, person_record in load_person_records(book).items():
        meta = person_record["metadata"]
        numbers = [page_index[scan] + 1 for scan in meta["scans"]]
        first, last = min(numbers), max(numbers)
        pages = f"page {first}" if first == last else f"pages {first}-{last}"
        label = f"{person_path(book, person_id).stem} · {meta['deceased']['full_name']}"
        choices[f"{label} · {pages}"] = page_index[meta["scans"][0]]
    return choices


def last_person_id(book: Path) -> int:
    """The highest ``person-NNNN.json`` id in ``book``, 0 if none: the next save is +1."""
    return max(load_person_records(book), default=0)


def saved_boxes(
    book: Path, scan: str, skip_person_id: int | None = None
) -> list[tuple[str, list[int]]]:
    """``(label, bbox)`` of every box on ``scan`` in ``book``'s person files, by person.

    ``skip_person_id`` is the person being edited: they are drawn from memory, labelled,
    not faded.
    """
    return [
        (label, box["bbox"])
        for person_id, person_record in load_person_records(book).items()
        if person_id != skip_person_id
        for label, item in block_labels(person_record)
        for box in item["layout"]
        if box["scan"] == scan
    ]


def resume(books: list[Path]) -> tuple[tuple[int, int], int]:
    """Where to pick up, from the output files alone.

    Returns ``((book, page), person_id)``. Books are labeled in order, so the last book
    with any ``person-NNNN.json`` is open, on the last page of its newest person's
    ``scans``. That person is not reopened (closing is not recorded): there is no
    current person, and the next save starts ``person_id + 1``. With no files at all:
    ``((0, 0), 0)``.
    """
    for b in reversed(range(len(books))):
        person_records = load_person_records(books[b])
        if person_records:
            person_id = max(person_records)
            last_scan = person_records[person_id]["metadata"]["scans"][-1]
            pages = [p.name for p in list_pages(books[b])]
            return (b, pages.index(last_scan)), person_id
    return (0, 0), 0


@functools.lru_cache(maxsize=512)
def thumbnail(page: Path, height: int = 120) -> bytes:
    """``page`` as a small grayscale JPEG, ``height`` px tall (cached: pages never change)."""
    im = Image.open(page)
    im.draft("L", (1, height))
    im = im.convert("L")
    im.thumbnail((im.width, height))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def crop(page: Path, bbox: list[int]) -> bytes:
    """``bbox`` of ``page`` at full resolution, as a grayscale JPEG."""
    im = Image.open(page).crop(bbox).convert("L")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return buf.getvalue()
