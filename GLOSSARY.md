# Vox Paginae

Vox Paginae annotates scanned death-duty deeds (*memories van successie*): where each
deed's header, balance and items are on its pages, and what the items say.

Where a term has another name in the UI, the files or the code, its entry says so.
Names marked "today" are out of step and due to be renamed.

## Language

### Sources

**Book**:
A set of scanned pages and the deeds listed for them in its `deeds.json`.
_Avoid_: folder, register

**Page**:
One scanned image in a book.
_File_: `scan` (the image's filename), `scans`
_Avoid_: scan, image

**Deed**:
One memorie van successie: an entry in its book's `deeds.json`, written on one or more
consecutive pages. It is what Vox Paginae annotates.
_UI today_: deed/person
_Code_: `deed` (the `deeds.json` entry), `deed_record` (the deed file's contents)
_Avoid_: deed/person, person, record

**Deed person**:
A person listed in a deed's `personen`.
_File_: an entry of `personen`
_Avoid_: person (on its own)

**Overledene**:
The deceased: the deed person with `rol: overledene`. A deed can be annotated only if
the overledene is its one deed person.
_Avoid_: deceased person, person

### Annotating

**Vox Paginae**:
The tool.
_Code today_: `item_block_labeler.py`
_Avoid_: labeler, item-block labeler, annotator

**Annotator**:
The person doing the annotating, who gives their name before anything else.
_File_: `annotator_name`
_Avoid_: labeler, user, person

**Annotation**:
A deed's header, balance and items together.
_UI today_: labels (**move labels**)
_File_: `annotation`
_Avoid_: labels, blocks

**Deed file**:
The file holding one deed's annotation, plus a copy of the deed's and its overledene's
data, next to its book's pages.
_File_: `labeled-deed-<deed_id>.json`; the copy is `copied_deed_person_data`
_Avoid_: person file

**Open deed**:
The deed being annotated. At most one deed is open at a time. A closed deed can be
reopened.
_Avoid_: open person, current record

**Move**:
Giving an open deed's annotation to another deed that has no deed file yet.
_UI today_: **move labels**

### What is annotated

**Box**:
One rectangle on one page.
_File_: a `layout` entry (`scan` and `bbox`)
_Avoid_: block, region, layout

**Pending box**:
A box drawn but not yet saved into the annotation.
_UI_: pending
_Avoid_: pending block

**Header**:
The heading where a deed starts, marked by one box. A deed cannot be opened without it.

**Header page**:
The page of the header's box: a deed's first page.

**Balance**:
A deed's totals (assets, liabilities, total), marked by one box on the header page or a
later page. A deed has at most one balance, or none.

**Item**:
One asset or liability of a deed: its type, an optional category, an amount, a
description, and one or more boxes.
_Code today_: block (`add_block`, `block_labels`)
_Avoid_: block, item block, entry

**Type**:
Whether an item is an asset or a liability.
_File_: which list the item is in, `assets` or `liabilities`

**Amount**:
An item's value as written in the deed, kept exactly as typed.
_UI today_: value
_Avoid_: value

**Tag**:
The short name shown on a box: `H` for the header, `B` for the balance, `A1, A2…` for
assets and `L1, L2…` for liabilities, by position.
_Code_: label
_Avoid_: label

## Relationships

- A **book** has many **pages** and many **deeds**.
- A **deed** runs over consecutive pages, starting at its **header page**. A page can
  hold the end of one deed and the start of the next.
- A **deed** has at most one **deed file**, with its **annotation**: one **header**, at
  most one **balance**, and any number of **items**.
