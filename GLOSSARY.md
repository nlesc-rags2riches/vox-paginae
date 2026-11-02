# Vox Paginae

Vox Paginae annotates scanned death-duty deeds (*memories van successie*): where each
deed's header, balance and items are on its scans, and what the items say.

Where a term has another name in the UI, the files or the code, its entry says so.

## Language

### Sources

**Book**:
A set of scans. It may have a `deeds.json` listing its deeds.
*Avoid*: folder, register

**Scan**:
One image file in a book. It can show one page or two.
*File*: `scan` (the image's filename), `scans`
*Avoid*: page, image

**Deed**:
An entry in a book, shown on one or more consecutive scans. Also called a *memorie*
(van successie). It is what Vox Paginae annotates.
*Code*: `deed` (the `deeds.json` entry), `deed_record` (the deed annotation file's
contents)
*Avoid*: deed/person, person

**Single deed folder**:
The part of a book that holds one deed (for example scans 6–12), as a folder of its
own. It is identified by its deed's `ref_reg`.
*Avoid*: deed folder

**Single deed input**:
The JSON in a single deed folder describing its deed.

**Deed person**:
A person listed in a deed's `personen`.
*File*: an entry of `personen`
*Code*: `deed_persons`
*Avoid*: person (on its own)

**Overledene**:
The deceased: the deed person with `rol: overledene`. A deed in a book's
`deeds.json` can be annotated only if the overledene is its one deed person.
*Avoid*: deceased person, person

### Annotating

**Vox Paginae**:
The tool.
*Code*: `notebooks/deed_annotation.py`
*Avoid*: labeler, item-block labeler, annotator

**Annotator**:
The person doing the annotating.
*File*: `annotator_name`
*Avoid*: labeler, user, person

**Annotation**:
A deed's header, balance and items together.
*File*: `annotation`
*Avoid*: labels, blocks

**Deed annotation file**:
The file holding one deed's annotation, plus a copy of the deed's and its overledene's
data when its input has them. It sits next to the deed's scans: in its book, or in its
single deed folder.
*File*: `deed-annotation-<deed_id>.json`; the copy is `copied_deed_person_data`
*Avoid*: deed file, person file

**Open deed**:
The one deed being annotated right now; the others are closed.
*Avoid*: open person

**Move**:
Giving an open deed's annotation and scans to another deed that has no deed annotation
file yet.
*UI*: **move annotation**

### What is annotated

**Box**:
One rectangle on one scan.
*File*: an object with `scan` and `bbox`; an item's boxes are its `layout`
*Avoid*: block, region, layout

**Pending box**:
One of an item's boxes, kept while its next box is drawn, before the item is saved.
*UI*: pending
*Avoid*: pending block

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
*Avoid*: block, item block

**Type**:
Whether an item is an asset or a liability.
*File*: which list the item is in, `assets` or `liabilities`

**Amount**:
An item's value as written in the deed.
*Avoid*: value

**Tag**:
The short name shown on a box: `H` for the header, `B` for the balance, `A1, A2…` for
assets and `L1, L2…` for liabilities, by position.
*Avoid*: label

## Relationships

- A **book** has many **scans** and many **deeds**.
- A **single deed folder** is part of a **book**. It holds one **deed**, its **scans**
  and one **single deed input**.
- A scan can hold the end of one **deed** and the start of the next.
- A **deed** has at most one **deed annotation file**, which holds its **annotation**.
