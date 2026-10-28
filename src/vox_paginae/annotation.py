"""Annotation: books, pages, deeds, their deed annotation files, items and boxes (non-UI part)."""

# TODO: Split this into appropriate files and detailed human review

import copy
import functools
import io
import json
from datetime import datetime
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


def new_box(scan: str, bbox: list[int]) -> dict:
    """A BOX: ``bbox`` on ``scan``, in whole pixels, with no PageXML match computed."""
    return {
        "scan": scan,
        "bbox": [int(v) for v in bbox],
        "pagexml_link": None,
        "pagexml_baseline_ids": None,
    }


def new_deed_record(deed: dict, header_scan: str, header_bbox: list[int]) -> dict:
    """A blank deed record for ``deed``, opened on its header box.

    ``header_bbox`` on ``header_scan`` becomes ``annotation.header``; that is the header page.

    The deed's ``aktenummer``, ``plaats`` and its overledene's fields (all but ``rol``,
    always ``overledene``) are copied flat, as they are in ``deeds.json``.
    """
    overledene = {k: v for k, v in single_overledene(deed).items() if k != "rol"}
    return {
        "deed_id": deed["deed_id"],
        "copied_deed_person_data": {
            "aktenummer": deed["aktenummer"],
            "plaats": deed["plaats"],
            **overledene,
        },
        "scans": [header_scan],
        # Filled in by every write.
        "annotation_metadata": {"annotator_name": None, "annotation_date": None},
        "annotation": {
            "header": new_box(header_scan, header_bbox),
            "balance": None,  # optional: see set_balance
            "assets": [],
            "liabilities": [],
        },
    }


def add_item(
    deed_record: dict,
    type_: str,
    category: str,
    amount: str,
    description: str,
    layout_boxes: list[tuple[str, list[int]]],
) -> dict:
    """Return a copy of ``deed_record`` with a new ``type_`` item.

    Each ``(scan, bbox)`` in ``layout_boxes`` becomes one ``layout`` entry.

    ``amount`` and ``description`` are stored as typed; at least one must be non-blank.
    An empty ``category`` becomes ``None``.
    """
    if type_ not in TYPES:
        raise ValueError(f"type must be one of {TYPES}, got {type_!r}")
    if not layout_boxes:
        raise ValueError("an item needs at least one box")
    if not (amount.strip() or description.strip()):
        raise ValueError("an item needs an amount or a description")
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"][type_].append(
        {
            "layout": [new_box(scan, bbox) for scan, bbox in layout_boxes],
            "category": category or None,
            "amount": amount,
            "description": description,
        }
    )
    return deed_record


def set_balance(
    deed_record: dict,
    scan: str,
    bbox: list[int],
    total_assets: str,
    total_liabilities: str,
    total: str,
) -> dict:
    """Return a copy of ``deed_record`` with its balance: ``bbox`` on ``scan``.

    The totals are stored as typed; at least one must be non-blank. A deed has at
    most one balance: a second raises ``ValueError``; ``clear_balance`` first.
    """
    if deed_record["annotation"]["balance"] is not None:
        raise ValueError("a deed has at most one balance")
    if not any(t.strip() for t in (total_assets, total_liabilities, total)):
        raise ValueError("a balance needs at least one total")
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"]["balance"] = {
        "layout": new_box(scan, bbox),
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total": total,
    }
    return deed_record


def clear_balance(deed_record: dict) -> dict:
    """Return a copy of ``deed_record`` without a balance."""
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"]["balance"] = None
    return deed_record


def replace_balance(
    deed_record: dict,
    scan: str,
    bbox: list[int],
    total_assets: str,
    total_liabilities: str,
    total: str,
) -> dict:
    """``set_balance`` in place of the saved balance, with the same checks."""
    return set_balance(
        clear_balance(deed_record), scan, bbox, total_assets, total_liabilities, total
    )


def set_header(
    deed_record: dict, page_names: list[str], scan: str, bbox: list[int]
) -> dict:
    """Return a copy of ``deed_record`` with its header: ``bbox`` on ``scan``.

    ``scan`` becomes the header page, in ``page_names`` (the book's, in order). A
    closed deed's ``scans`` then runs from ``scan`` to its old last page (or is
    just ``scan``, if later); one never closed keeps only the header page. A balance or
    item box before ``scan`` would be outside ``scans``: that raises ``ValueError``.
    """
    start = page_names.index(scan)
    if any(
        page_names.index(box["scan"]) < start
        for tag, box in deed_boxes(deed_record)
        if tag != "H"
    ):
        raise ValueError("the header page cannot come after a saved box")
    # ponytail: one page also means closed on its header page; the next close redoes it.
    end = (
        start
        if len(deed_record["scans"]) == 1
        else max(start, page_names.index(deed_record["scans"][-1]))
    )
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"]["header"] = new_box(scan, bbox)
    deed_record["scans"] = page_names[start : end + 1]
    return deed_record


def item_tags(deed_record: dict | None) -> list[tuple[str, dict]]:
    """``(tag, item)`` for every item: ``A1, A2…`` for assets, then ``L1, L2…``.

    ``None`` (no open deed) has no items.
    """
    if deed_record is None:
        return []
    return [
        (f"{t[0].upper()}{i}", item)
        for t in TYPES
        for i, item in enumerate(deed_record["annotation"][t], start=1)
    ]


def deed_boxes(deed_record: dict | None) -> list[tuple[str, dict]]:
    """``(tag, BOX)`` for every box: ``("H", header)``, ``("B", balance)`` if any, then
    each item's, by tag.

    ``None`` (no open deed) has none.
    """
    if deed_record is None:
        return []
    balance = deed_record["annotation"]["balance"]
    return (
        [("H", deed_record["annotation"]["header"])]
        + ([("B", balance["layout"])] if balance else [])
        + [(tag, box) for tag, item in item_tags(deed_record) for box in item["layout"]]
    )


def split_tag(tag: str) -> tuple[str, int]:
    """``"A2"`` -> ``("assets", 1)``: the item's type and its index in that list."""
    return {"A": "assets", "L": "liabilities"}[tag[0]], int(tag[1:]) - 1


def delete_item(deed_record: dict, tag: str) -> dict:
    """Return a copy of ``deed_record`` without the item called ``tag`` (e.g. ``"A2"``)."""
    type_, i = split_tag(tag)
    deed_record = copy.deepcopy(deed_record)
    del deed_record["annotation"][type_][i]
    return deed_record


def replace_item(
    deed_record: dict,
    tag: str,
    type_: str,
    category: str,
    amount: str,
    description: str,
    layout_boxes: list[tuple[str, list[int]]],
) -> dict:
    """``add_item`` in place of the item called ``tag``, with the same checks.

    It keeps its position (``A2`` stays ``A2``) unless ``type_`` changes; then it goes
    last of ``type_``.
    """
    old_type, i = split_tag(tag)
    deed_record = add_item(
        delete_item(deed_record, tag),
        type_,
        category,
        amount,
        description,
        layout_boxes,
    )
    if type_ == old_type:
        items = deed_record["annotation"][type_]
        items.insert(i, items.pop())
    return deed_record


def close_deed_record(
    deed_record: dict, page_names: list[str], close_scan: str
) -> dict:
    """Return a copy of ``deed_record`` closed on ``close_scan``.

    ``scans`` becomes every page in ``page_names`` (the book's, in order) from the
    header page (``scans[0]``) to ``close_scan`` or the last page a box reaches,
    whichever is later, both included, with or without items. Closing before the header
    page raises ``ValueError``.
    """
    start = page_names.index(deed_record["scans"][0])
    end = page_names.index(close_scan)
    if end < start:
        raise ValueError("a deed cannot close before its header page")
    end = max(
        [end] + [page_names.index(box["scan"]) for _, box in deed_boxes(deed_record)]
    )
    deed_record = copy.deepcopy(deed_record)
    deed_record["scans"] = page_names[start : end + 1]
    return deed_record


def deed_path(book: Path, deed_id: str) -> Path:
    """``<book>/deed-annotation-<deed_id>.json``: one file per deed."""
    return Path(book) / f"deed-annotation-{deed_id}.json"


def save_deed_record(book: Path, deed_record: dict, annotator_name: str) -> Path:
    """Write ``deed_record`` to its ``deed_path``, by ``annotator_name``, now.

    Every write records the current annotator and the time (local, with its timezone),
    so a reopened file gets the latest of both.
    """
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation_metadata"] = {
        "annotator_name": annotator_name,
        "annotation_date": datetime.now().astimezone().isoformat(),
    }
    path = deed_path(book, deed_record["deed_id"])
    tmp = path.with_suffix(".json.tmp")  # write-then-rename: a crash never truncates
    tmp.write_text(
        json.dumps(deed_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    tmp.replace(path)
    return path


def move_deed_record(
    book: Path, deed_record: dict, deed: dict, annotator_name: str
) -> dict:
    """Move ``deed_record``'s annotation to ``deed``, a deed without a file in ``book``.

    ``deed_id`` and ``copied_deed_person_data`` come from ``deed``, as on open; the rest
    stays. The new file is written before the old one goes, so an interrupted move never
    loses the annotation. A deed that cannot be used, or has a file, raises ``ValueError``.
    """
    header = deed_record["annotation"]["header"]
    # As on open, for its checks and its copied data; the rest of it is not used.
    fresh = new_deed_record(deed, header["scan"], header["bbox"])
    if deed_path(book, deed["deed_id"]).exists():
        raise ValueError("this deed already has a file")
    moved = copy.deepcopy(deed_record)
    moved["deed_id"] = fresh["deed_id"]
    moved["copied_deed_person_data"] = fresh["copied_deed_person_data"]
    save_deed_record(book, moved, annotator_name)
    deed_path(book, deed_record["deed_id"]).unlink(missing_ok=True)
    return moved


def load_deed_records(book: Path) -> dict[str, dict]:
    """``{deed_id: deed_record}`` for every ``deed-annotation-*.json`` in ``book``.

    Files from the old format (``person-NNNN.json``) or with the old name
    (``labeled-deed-*.json``) are not read.
    """
    return {
        r["deed_id"]: r
        for r in (
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(Path(book).glob("deed-annotation-*.json"))
        )
    }


def load_deeds(book: Path) -> dict[str, dict] | None:
    """``{deed_id: deed}`` from ``<book>/deeds.json``, ``None`` if the book has none."""
    path = Path(book) / "deeds.json"
    if not path.exists():
        return None
    return {
        deed["deed_id"]: deed for deed in json.loads(path.read_text(encoding="utf-8"))
    }


def deed_choices(deeds: dict[str, dict], book: Path) -> dict[str, str]:
    """``{"93 · Westdorp · Jan Modaal": deed_id}``, by aktenummer, then place.

    Deeds with a file in ``book`` go last, labelled with their pages, e.g.
    ``"93 · Westdorp · Jan Modaal · pages 22-24"`` (counted from 1, as in the status line).
    ``aktenummer`` repeats within a book (e.g. 93 in two places), hence the place;
    ``deeds.json`` itself is not in page order.
    """
    deed_records = load_deed_records(book)
    page_number = {p.name: i + 1 for i, p in enumerate(list_pages(book))}

    def label(d):
        parts = [
            d["aktenummer"],
            d["plaats"],
            *(p["naam_volledig"] for p in d["personen"]),
        ]
        if d["deed_id"] in deed_records:
            numbers = [page_number[s] for s in deed_records[d["deed_id"]]["scans"]]
            first, last = min(numbers), max(numbers)
            parts.append(f"page {first}" if first == last else f"pages {first}-{last}")
        return " · ".join(parts)

    def order(d):
        has_file = d["deed_id"] in deed_records
        # A non-numeric aktenummer goes after the numbered ones.
        number = int(d["aktenummer"]) if d["aktenummer"].isdigit() else float("inf")
        return has_file, number, d["plaats"]

    ordered = sorted(deeds.values(), key=order)
    return {label(d): d["deed_id"] for d in ordered}


def single_overledene(deed: dict) -> dict:
    """The deed's one deed person, who must have ``rol: overledene``.

    Vox Paginae assumes exactly that; any other deed raises ``ValueError`` with a message
    for the annotator.
    """
    deed_persons = deed["personen"]
    if len(deed_persons) != 1:
        raise ValueError(
            f"This deed has {len(deed_persons)} deed persons: it needs exactly one, "
            "with `rol: overledene`. It cannot be used."
        )
    if deed_persons[0].get("rol") != "overledene":
        raise ValueError(
            f"Its one deed person has `rol: {deed_persons[0].get('rol')}`: it needs "
            "`rol: overledene`. It cannot be used."
        )
    return deed_persons[0]


def saved_boxes(
    book: Path, scan: str, skip_deed_id: str | None = None
) -> list[tuple[str, list[int]]]:
    """``(tag, bbox)`` of every box on ``scan`` in ``book``'s deed annotation files, by deed.

    Tags as in ``deed_boxes``: ``H`` for a header, ``B`` for a balance.

    ``skip_deed_id`` is the open deed: it is drawn from memory, tagged, not
    faded.
    """
    return [
        (tag, box["bbox"])
        for deed_id, deed_record in load_deed_records(book).items()
        if deed_id != skip_deed_id
        for tag, box in deed_boxes(deed_record)
        if box["scan"] == scan
    ]


def resume(books: list[Path]) -> tuple[int, int]:
    """Where to pick up, ``(book, page)``, from the output files alone.

    Books are annotated in order, so the last book with any ``deed-annotation-*.json`` is
    open, on the latest page among its files' last ``scans``: a closed deed's close
    page (or the later page a box reaches, see ``close_deed_record``), a not yet closed
    one's header page. No deed is reopened. With no files at all: ``(0, 0)``.
    """
    for b in reversed(range(len(books))):
        deed_records = load_deed_records(books[b])
        if deed_records:
            pages = [p.name for p in list_pages(books[b])]
            return b, max(pages.index(r["scans"][-1]) for r in deed_records.values())
    return 0, 0


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
