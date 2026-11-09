"""Single deed input: finding single deed folders and reading their `input.json`."""

import json
import re
from pathlib import Path

from vox_paginae.annotation import HEADER_FIELDS, load_deed_records, scans_label


def file_browser_order(path: Path) -> list[list[str | int]]:
    """A sort key for ``path`` that orders names as Finder and Windows Explorer do.

    Numbers in a name count as numbers, so ``6-1`` comes before ``10-1``. Case is
    ignored.
    """
    # re.split with a group alternates text and digits, always starting with text, so
    # two keys compare str to str and int to int.
    return [
        [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", part)]
        for part in path.parts
    ]


def find_single_deed_folders(root: Path) -> list[Path]:
    """Every folder under ``root`` that has an ``input.json``, in file browser order."""
    root = Path(root)
    return sorted(
        (p.parent for p in root.rglob("input.json")),
        key=lambda folder: file_browser_order(folder.relative_to(root)),
    )


def load_single_deed_input(folder: Path) -> dict:
    """The ``metadata`` of ``<folder>/input.json``, read as UTF-8.

    An input without ``metadata.ref_reg`` raises ``ValueError`` naming the folder: the
    deed is known by it.
    """
    path = Path(folder) / "input.json"
    metadata = json.loads(path.read_text(encoding="utf-8")).get("metadata") or {}
    if not metadata.get("ref_reg"):
        raise ValueError(f"`{path}` has no `metadata.ref_reg`: it cannot be used.")
    return metadata


def copied_deed_person_data(single_deed_input: dict) -> dict:
    """The deed's ``ref_reg``, ``aktenummer`` and ``tax_office`` and the fields of its
    ``deceased``, flat, for its deed record's ``copied_deed_person_data``.

    ``single_deed_input`` is from ``load_single_deed_input``. Its ``assets``,
    ``liabilities``, ``scans`` and ``total`` are left out.
    """
    return {
        "ref_reg": single_deed_input["ref_reg"],
        "aktenummer": single_deed_input.get("aktenummer"),
        "tax_office": single_deed_input.get("tax_office"),
        **(single_deed_input.get("deceased") or {}),
    }


def header_fields(copied_deed_person_data: dict) -> dict[str, str]:
    """The header's fields, pre-filled from a deed's ``copied_deed_person_data``: the
    deceased's fields of the same names. A field missing or ``null`` there is blank.
    """
    return {field: copied_deed_person_data.get(field) or "" for field in HEADER_FIELDS}


def deed_choices(folders: list[Path]) -> dict[str, Path]:
    """``{"10#1399 · Jan Modaal": folder}`` for each of ``folders``, in their order.

    A folder with a deed annotation file is labelled with its pages too, e.g.
    ``"10#1399 · Jan Modaal · pages 2-4"``. Each input is read as in
    ``load_single_deed_input``.
    """
    choices = {}
    for folder in folders:
        single_deed_input = load_single_deed_input(folder)
        ref_reg = single_deed_input["ref_reg"]
        deed_record = load_deed_records(folder).get(ref_reg)
        full_name = (single_deed_input.get("deceased") or {}).get("full_name")
        parts = [ref_reg] + ([full_name] if full_name else [])
        if deed_record:
            parts.append(scans_label(folder, deed_record["scans"]))
        choices[" · ".join(parts)] = folder
    return choices
