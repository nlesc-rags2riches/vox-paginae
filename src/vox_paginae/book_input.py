"""Book input: finding books, reading their `deeds.json` and checking its deeds."""

import json
from pathlib import Path

from vox_paginae.annotation import list_pages, load_deed_records


def find_books(root: Path) -> list[Path]:
    """Every folder under ``root`` that directly contains ``*.jpg``, in sorted path order."""
    return sorted({p.parent for p in Path(root).rglob("*.jpg")})


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


def copied_deed_person_data(deed: dict) -> dict:
    """The deed's ``aktenummer``, ``plaats`` and its overledene's fields, flat, for its
    deed record's ``copied_deed_person_data``.

    All but the overledene's ``rol``, always ``overledene``. A deed that cannot be used
    raises ``ValueError``, as in ``single_overledene``.
    """
    overledene = {k: v for k, v in single_overledene(deed).items() if k != "rol"}
    return {"aktenummer": deed["aktenummer"], "plaats": deed["plaats"], **overledene}


def header_fields(copied_deed_person_data: dict) -> dict[str, str]:
    """The header's fields, pre-filled from a deed's ``copied_deed_person_data``.

    A field missing or ``null`` there is blank. The place of residence is the
    overledene's ``plaats_overlijden`` (see issue #115).
    """
    copied = copied_deed_person_data
    return {
        "full_name": copied.get("naam_volledig") or "",
        "date_of_death": copied.get("datum_overlijden") or "",
        "place_of_residence": copied.get("plaats_overlijden") or "",
    }
