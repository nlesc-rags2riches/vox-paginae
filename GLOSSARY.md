# Vox Paginae

Vox Paginae annotates scanned death-duty deeds (*memories van successie*): where each
deed's header, balance and items are on its scans, and what the items say.

Where a term has another name in the UI, the files or the code, its entry says so.

## Language

### Sources

**Book**:
A set of scans. It may have a `deeds.json` listing its deeds.
_Avoid_: folder, register

**Scan**:
One image file in a book. It can show one page or two.
_File_: `scan` (the image's filename), `scans`
_Avoid_: page, image

**Deed**:
An entry in a book, shown on one or more consecutive scans. Also called a *memorie*
(van successie). It is what Vox Paginae annotates.
_Code_: `deed` (the `deeds.json` entry), `deed_record` (the deed annotation file's
contents)
_Avoid_: deed/person, person

**Single deed folder**:
The part of a book that holds one deed (for example scans 6–12), as a folder of its
own. It is identified by its deed's `ref_reg`.
_Avoid_: deed folder

**Single deed input**:
The JSON in a single deed folder describing its deed.

**Deed person**:
A person listed in a deed's `personen`.
_File_: an entry of `personen`
_Code_: `deed_persons`
_Avoid_: person (on its own)

**Overledene**:
The deceased: the deed person with `rol: overledene`. A deed in a book's
`deeds.json` can be annotated only if the overledene is its one deed person.
_Avoid_: deceased person, person

### Annotating

**Vox Paginae**:
The tool.
_Code_: `notebooks/deed_annotation.py`
_Avoid_: labeler, item-block labeler, annotator

**Annotator**:
The person doing the annotating.
_File_: `annotator_name`
_Avoid_: labeler, user, person

**Annotation**:
A deed's header, balance and items together.
_File_: `annotation`
_Avoid_: labels, blocks

**Deed annotation file**:
The file holding one deed's annotation, plus a copy of the deed's and its overledene's
data when its input has them. It sits next to the deed's scans: in its book, or in its
single deed folder.
_File_: `deed-annotation-<deed_id>.json`; the copy is `copied_deed_person_data`
_Avoid_: deed file, person file

**Open deed**:
The one deed being annotated right now; the others are closed.
_Avoid_: open person

**Move**:
Giving an open deed's annotation and scans to another deed that has no deed annotation
file yet.
_UI_: **move annotation**

### What is annotated

**Box**:
One rectangle on one scan.
_File_: an object with `scan` and `bbox`; an item's boxes are its `layout`
_Avoid_: block, region, layout

**Pending box**:
One of an item's boxes, kept while its next box is drawn, before the item is saved.
_UI_: pending
_Avoid_: pending block

**Header**:
The heading where a deed starts, marked by one box.

**Header page**:
The scan of the header's box: a deed's first scan.

**Balance**:
A deed's totals (assets, liabilities, total), marked by one box on the header page or a
later scan. A deed has at most one balance, or none.

**Item**:
One asset or liability of a deed: its type, an optional category, an amount or a
description (or both), and one or more boxes.
_Avoid_: block, item block

**Type**:
Whether an item is an asset or a liability.
_File_: which list the item is in, `assets` or `liabilities`

**Amount**:
An item's value as written in the deed.
_Avoid_: value

**Tag**:
The short name shown on a box: `H` for the header, `B` for the balance, `A1, A2…` for
assets and `L1, L2…` for liabilities, by position.
_Avoid_: label

## Relationships

- A **book** has many **scans** and many **deeds**.
- A **single deed folder** is part of a **book**. It holds one **deed**, its **scans**
  and one **single deed input**.
- A scan can hold the end of one **deed** and the start of the next.
- A **deed** has at most one **deed annotation file**, which holds its **annotation**.
