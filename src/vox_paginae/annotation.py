"""Annotation: books, pages, deeds, their deed annotation files, items and boxes (non-UI part)."""

# TODO: Split this into appropriate files and detailed human review

import copy
import json
import re
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

SCAN_EXTENSIONS = {".jpg", ".jpeg"}


def is_scan(path: Path) -> bool:
    """Whether ``path`` is a scan: its extension is in ``SCAN_EXTENSIONS``, in any case."""
    return path.suffix.lower() in SCAN_EXTENSIONS


def list_pages(book: Path) -> list[Path]:
    """The scans in ``book``, sorted by filename as plain strings."""
    return sorted(filter(is_scan, Path(book).glob("*")), key=lambda p: p.name)


def scans_label(book: Path, scans: list[str]) -> str:
    """``"page 3"`` or ``"pages 2-4"``: where ``scans`` of ``book`` are, counted from 1
    as in the status line.
    """
    page_number = {p.name: i + 1 for i, p in enumerate(list_pages(book))}
    numbers = [page_number[s] for s in scans]
    first, last = min(numbers), max(numbers)
    return f"page {first}" if first == last else f"pages {first}-{last}"


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
HEADER_FIELDS = ("full_name", "date_of_death", "place_of_residence")
# The version of the deed annotation file's format (Semantic Versioning 2.0.0), written
# into every file. The reference's Format versions section says when it changes.
FORMAT_VERSION = "0.1.0"


def is_newer_format_version(version: str | None) -> bool:
    """Whether ``version``, a file's ``format_version``, is newer than ``FORMAT_VERSION``.

    Compared by MAJOR, MINOR and PATCH, as numbers. ``None`` (a file without one) is
    not newer. A version without those three numbers, or not a string, is: it cannot
    be read.
    """
    if version is None:
        return False
    if not isinstance(version, str):
        return True
    parts = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if parts is None:
        return True
    current = tuple(int(n) for n in FORMAT_VERSION.split("."))
    return tuple(int(n) for n in parts.groups()) > current


def new_box(scan: str, bbox: Sequence[float]) -> dict:
    """A BOX: ``bbox`` on ``scan``, in whole pixels, with no PageXML match computed."""
    return {
        "scan": scan,
        "bbox": [int(v) for v in bbox],
        "pagexml_link": None,
        "pagexml_baseline_ids": None,
    }


def new_deed_record(
    deed_id: str, copied_deed_person_data: dict, first_scan: str
) -> dict:
    """A blank deed record for deed ``deed_id``, opened on ``first_scan``: its first scan.

    It has no header box yet: see ``add_header_box``.

    ``copied_deed_person_data`` is the deed's data from its input, kept as given.
    """
    return {
        "deed_id": deed_id,
        "copied_deed_person_data": copy.deepcopy(copied_deed_person_data),
        "scans": [first_scan],
        # Filled in by every write.
        "annotation_metadata": {"annotator_name": None, "annotation_date": None},
        "annotation": {
            # Fields from set_header_fields, boxes from add_header_box: both optional.
            "header": {
                "full_name": "",
                "date_of_death": "",
                "place_of_residence": "",
                "layout": [],
            },
            # Totals from set_balance_totals, boxes from add_balance_box: both optional.
            "balance": {
                "total_assets": "",
                "total_liabilities": "",
                "total": "",
                "layout": [],
            },
            "assets": [],
            "liabilities": [],
        },
    }


def add_item(
    deed_record: dict,
    type_: str | None,
    amount: str,
    description: str,
    layout_boxes: Sequence[tuple[str, Sequence[float]]],
) -> dict:
    """Return a copy of ``deed_record`` with a new ``type_`` item.

    Each ``(scan, bbox)`` in ``layout_boxes`` becomes one ``layout`` entry.

    ``amount`` and ``description`` are stored as typed, stripped; at least one must be
    non-blank.
    """
    if type_ not in TYPES:
        raise ValueError(f"type must be one of {TYPES}, got {type_!r}")
    if not layout_boxes:
        raise ValueError("an item needs at least one box")
    amount, description = amount.strip(), description.strip()
    if not (amount or description):
        raise ValueError("an item needs an amount or a description")
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"][type_].append(
        {
            "layout": [new_box(scan, bbox) for scan, bbox in layout_boxes],
            "amount": amount,
            "description": description,
        }
    )
    return deed_record


def set_balance_totals(
    deed_record: dict, total_assets: str, total_liabilities: str, total: str
) -> dict:
    """Return a copy of ``deed_record`` with its balance's totals replaced.

    They are stored as typed, stripped; any or all may be blank. The boxes stay.
    """
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"]["balance"].update(
        total_assets=total_assets.strip(),
        total_liabilities=total_liabilities.strip(),
        total=total.strip(),
    )
    return deed_record


def set_header_fields(
    deed_record: dict, full_name: str, date_of_death: str, place_of_residence: str
) -> dict:
    """Return a copy of ``deed_record`` with its header's fields replaced.

    They are stored as typed, stripped; empty ones stop the deed from closing (see
    ``close_deed_record``). The boxes stay.
    """
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"]["header"].update(
        full_name=full_name.strip(),
        date_of_death=date_of_death.strip(),
        place_of_residence=place_of_residence.strip(),
    )
    return deed_record


def _add_tagged_box(
    deed_record: dict, section: str, scan: str, bbox: Sequence[float]
) -> dict:
    """Return a copy of ``deed_record`` with ``bbox`` on ``scan`` as the last box of
    ``section``: ``"header"`` or ``"balance"``.
    """
    deed_record = copy.deepcopy(deed_record)
    deed_record["annotation"][section]["layout"].append(new_box(scan, bbox))
    return deed_record


def _delete_tagged_box(deed_record: dict, section: str, tag: str) -> dict:
    """Return a copy of ``deed_record`` without the box of ``section`` called ``tag``."""
    deed_record = copy.deepcopy(deed_record)
    del deed_record["annotation"][section]["layout"][int(tag[1:]) - 1]
    return deed_record


def add_header_box(deed_record: dict, scan: str, bbox: Sequence[float]) -> dict:
    """Return a copy of ``deed_record`` with ``bbox`` on ``scan`` as its last header box.

    A header has zero or more boxes, on any of the deed's scans, tagged ``H1, H2…`` by
    position.
    """
    return _add_tagged_box(deed_record, "header", scan, bbox)


def delete_header_box(deed_record: dict, tag: str) -> dict:
    """Return a copy of ``deed_record`` without the header box called ``tag`` (``"H2"``)."""
    return _delete_tagged_box(deed_record, "header", tag)


def add_balance_box(deed_record: dict, scan: str, bbox: Sequence[float]) -> dict:
    """Return a copy of ``deed_record`` with ``bbox`` on ``scan`` as its last balance box.

    A balance has zero or more boxes, on any of the deed's scans, tagged ``B1, B2…`` by
    position. Each is another written version of the same totals.
    """
    return _add_tagged_box(deed_record, "balance", scan, bbox)


def delete_balance_box(deed_record: dict, tag: str) -> dict:
    """Return a copy of ``deed_record`` without the balance box called ``tag`` (``"B2"``)."""
    return _delete_tagged_box(deed_record, "balance", tag)


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


def tagged_section_boxes(
    deed_record: dict | None, section: str
) -> list[tuple[str, dict]]:
    """``(tag, BOX)`` for every box of ``section``: ``H1, H2…`` for ``"header"``,
    ``B1, B2…`` for ``"balance"``.

    ``None`` (no open deed) has none.
    """
    if deed_record is None:
        return []
    return [
        (f"{section[0].upper()}{i}", box)
        for i, box in enumerate(deed_record["annotation"][section]["layout"], start=1)
    ]


def deed_boxes(deed_record: dict | None) -> list[tuple[str, dict]]:
    """``(tag, BOX)`` for every box: the header's (``H1, H2…``), the balance's
    (``B1, B2…``), then each item's, by tag.

    ``None`` (no open deed) has none.
    """
    return (
        tagged_section_boxes(deed_record, "header")
        + tagged_section_boxes(deed_record, "balance")
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
    type_: str | None,
    amount: str,
    description: str,
    layout_boxes: Sequence[tuple[str, Sequence[float]]],
) -> dict:
    """``add_item`` in place of the item called ``tag``, with the same checks.

    It keeps its position (``A2`` stays ``A2``) unless ``type_`` changes; then it goes
    last of ``type_``.
    """
    old_type, i = split_tag(tag)
    deed_record = add_item(
        delete_item(deed_record, tag),
        type_,
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

    ``scans`` becomes every scan in ``page_names`` (the book's, in order) from the
    first scan (``scans[0]``) to ``close_scan`` or the last scan a box reaches,
    whichever is later, both included, with or without items. The header is optional:
    no box and empty fields are fine. Closing before its first scan raises
    ``ValueError`` saying why.
    """
    start = page_names.index(deed_record["scans"][0])
    end = page_names.index(close_scan)
    if end < start:
        raise ValueError("a deed cannot close before its first scan")
    end = max(
        [end] + [page_names.index(box["scan"]) for _, box in deed_boxes(deed_record)]
    )
    deed_record = copy.deepcopy(deed_record)
    deed_record["scans"] = page_names[start : end + 1]
    return deed_record


def deed_path(book: Path, deed_id: str) -> Path:
    """``<book>/deed-annotation-<deed_id>.json``: one file per deed."""
    return Path(book) / f"deed-annotation-{deed_id}.json"


def check_not_newer_format_version(path: Path) -> None:
    """Raise ``ValueError`` if ``path``, a deed annotation file, has a newer format
    version (see ``is_newer_format_version``). A missing file passes.

    The message, in Markdown for the annotator, names the file and says to update.
    """
    path = Path(path)
    if not path.exists():
        return
    version = json.loads(path.read_text(encoding="utf-8")).get("format_version")
    if is_newer_format_version(version):
        raise ValueError(
            "**This deed seems to have been edited with a newer version of Vox "
            "Paginae. [Update Vox Paginae]"
            "(https://nlesc-rags2riches.github.io/vox-paginae/how-to/install-and-run/).**"
            f"\n\nIts file, `{path}`, has format version {version}. This version of "
            f"Vox Paginae writes only {FORMAT_VERSION}, so the file was written by "
            "another version. If you think something else is wrong, [open an issue]"
            "(https://github.com/nlesc-rags2riches/vox-paginae/issues)."
        )


def save_deed_record(path: Path, deed_record: dict, annotator_name: str) -> Path:
    """Write ``deed_record`` to ``path``, its deed annotation file, by ``annotator_name``, now.

    Every write records the format version, the current annotator and the time (local,
    with its timezone), so a reopened file, or one without a version, gets the latest.
    A file with a newer format version is never written: see
    ``check_not_newer_format_version``.
    """
    check_not_newer_format_version(path)
    # First in the file, for whoever reads it; an older version is replaced.
    deed_record = {"format_version": FORMAT_VERSION, **copy.deepcopy(deed_record)}
    deed_record["format_version"] = FORMAT_VERSION
    deed_record["annotation_metadata"] = {
        "annotator_name": annotator_name,
        "annotation_date": datetime.now().astimezone().isoformat(),
    }
    path = Path(path)
    tmp = path.with_suffix(".json.tmp")  # write-then-rename: a crash never truncates
    tmp.write_text(
        json.dumps(deed_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    tmp.replace(path)
    return path


def move_deed_record(
    deed_record: dict,
    *,
    old_path: Path,
    new_path: Path,
    deed_id: str,
    copied_deed_person_data: dict,
    annotator_name: str,
) -> dict:
    """Move ``deed_record``'s annotation from ``old_path`` to deed ``deed_id``'s file,
    ``new_path``.

    ``deed_id`` and ``copied_deed_person_data`` are replaced, as on open; the rest
    stays. The new file is written before the old one goes, so an interrupted move never
    loses the annotation. A ``new_path`` that exists raises ``ValueError``.
    """
    if Path(new_path).exists():
        raise ValueError("this deed already has a file")
    moved = copy.deepcopy(deed_record)
    moved["deed_id"] = deed_id
    moved["copied_deed_person_data"] = copy.deepcopy(copied_deed_person_data)
    save_deed_record(new_path, moved, annotator_name)
    Path(old_path).unlink(missing_ok=True)
    return moved


def load_deed_records(book: Path) -> dict[str, dict]:
    """``{deed_id: deed_record}`` for every ``deed-annotation-*.json`` in ``book``.

    Files from the old format (``person-NNNN.json``) or with the old name
    (``labeled-deed-*.json``) are not read. Files with a newer format version are
    skipped: their fields may differ. ``check_not_newer_format_version`` says why.
    """
    return {
        r["deed_id"]: r
        for r in (
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(Path(book).glob("deed-annotation-*.json"))
        )
        if not is_newer_format_version(r.get("format_version"))
    }


def saved_boxes(
    book: Path, scan: str, skip_deed_id: str | None = None
) -> list[tuple[str, list[int]]]:
    """``(tag, bbox)`` of every box on ``scan`` in ``book``'s deed annotation files, by deed.

    Tags as in ``deed_boxes``: ``H1, H2…`` for the header, ``B1, B2…`` for the
    balance.

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
    one's first scan. No deed is reopened. With no files at all: ``(0, 0)``.
    """
    for b in reversed(range(len(books))):
        deed_records = load_deed_records(books[b])
        if deed_records:
            pages = [p.name for p in list_pages(books[b])]
            return b, max(pages.index(r["scans"][-1]) for r in deed_records.values())
    return 0, 0
