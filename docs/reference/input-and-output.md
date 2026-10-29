# Input and output

Exactly what the tool reads and writes. This is a promise to the annotator: it
changes only on purpose, and never describes internals.

## In

- You give your name as the **annotator** and lock it. Until it is locked, only the
  root folder can be changed. While locked it cannot be edited; unlock it to change it.
- You pick a root folder. Every folder under it that directly contains `*.jpg` is a
  **book**, and books are taken in sorted path order.
- A book's **pages** are its `*.jpg` files, sorted by filename.
- Every book must have a `deeds.json`; a book without one shows an error naming the
  book, and nothing can be annotated or saved in it. Its deeds are listed to pick from. A
  deed must have exactly one deed person, with `rol: overledene`; picking it shows that
  deed person's name, death place and death date. Picking a deed that doesn't satisfy this
  rule shows an error, and that deed cannot be used. `deeds.json` is read as UTF-8.
- Nothing else is read except the tool's own output (see Out): no other JSON
  (`metadata.json` included), no PageXML, no state file. Other files in the tree are
  ignored, and so are files from the old format (`person-NNNN.json`) and deed
  annotation files with the old name (`labeled-deed-<deed_id>.json`): they are neither
  read, shown nor removed. Rename an old deed annotation file to
  `deed-annotation-<deed_id>.json` to use it.

## Out

- One **deed annotation file** per deed:
  `<book>/deed-annotation-<deed_id>.json`, saved next to the jpgs. A deed that has a file
  cannot be opened anew, only reopened. It is written and read as UTF-8, on every
  system, so a file saved on one system opens unchanged on another.
- A deed belongs to exactly one book.
- Before opening, you draw a box around the deed's header on its first page;
  **open** stays disabled until there is one. The file is written as soon as the
  deed is opened. The page of the header box is its **header page**.
- While it is open, its item and balance boxes go on its header page or a later page.
  It is closed on one of those pages too.
- While it is open, **edit header** redraws the header box on any page up to the first
  page with a saved item or balance box; that page becomes the header page. Until
  **save header** or **cancel header edit**, the balance and items cannot be changed.
- While a deed is open, a drawn box can be saved as its **balance**, with three
  totals, at least one filled in. A deed has at most one balance, or none: clear it to
  save another.
  **edit balance box** lets you change the saved balance. Its totals can be retyped.
  A new box drawn on the page replaces its box; without one, the old box stays. Until
  **save box as balance** or **cancel balance edit**, the header and items cannot be
  changed.
- The file holds:
  - `deed_id`: as in `deeds.json`
  - `copied_deed_person_data`: the deed's `aktenummer` and `plaats`, and every field
    of its overledene except `rol`, side by side, copied as they are in `deeds.json`
  - `scans`: every page from the header page to the page it was closed on, in page
    order, with or without items. If an item or the balance has a box on a later page,
    `scans` reaches that page instead. Until the first close, only the header page.
  - `annotation_metadata`:
    - `annotator_name`: the annotator of the latest write
    - `annotation_date`: the time of the latest write, with its timezone (ISO 8601,
      e.g. `2026-10-27T14:03:12.123456+01:00`)
  - `annotation`:
    - `header`: the header box, a single box shaped like an item's `layout` entry
      (`scan`, `bbox`, `pagexml_link`, `pagexml_baseline_ids`)
    - `balance`: `null` without one; otherwise `layout` (a single box, shaped like
      `header`), and `total_assets`, `total_liabilities` and `total`, strings stored
      exactly as typed (`""` when left empty)
    - then `assets` and `liabilities`, each a list of items
- An item's **type** (asset or liability) is the list it's in. There is no separate
  field for it. Each item has:
  - `layout`: one entry per box, each with `scan` (the filename), `bbox`
    (`[x0, y0, x1, y1]` in image pixels, origin top-left), and `pagexml_link` and
    `pagexml_baseline_ids` (always `null`)
  - `category`: optional free text; left empty, it is written as `null`
  - `amount`: a string, stored exactly as typed
  - `description`: a single line
  - at least one of `amount` and `description` is non-blank; the other may be `""`
- A deed can have no items: every item can be deleted, and the file stays.
- Fields the tool doesn't fill are written as `null`, not left out.
- **Not in the file:** transcriptions, whether the deed is open right now.
- Each write replaces the whole file, and an interrupted write leaves the previous
  version. It can also leave a `deed-annotation-<deed_id>.json.tmp` next to it. That
  file is never read. Opening, moving the annotation, every added, changed or deleted
  item, saving, editing or clearing the balance, and saving the header, is in the file
  at once.
  Closing and saving the header rewrite `scans`. Every write rewrites `annotator_name` and
  `annotation_date`.
- Moving past a book's last page closes the open deed there.
- A closed deed can be reopened: it is open again as if never closed, and the
  next writes rewrite the same file.
- A deed's file can be deleted, after a confirmation. The deed can then be opened
  anew.
- While a deed is open, **move annotation** moves its annotation to another deed
  without a file. The file is then that deed's `deed-annotation-<deed_id>.json`. The old
  file is gone. `deed_id` and `copied_deed_person_data` come from the new deed; the
  header, balance, items and `scans` are kept. The new deed is open. The old deed can
  then be opened anew. An interrupted move can leave both files, with the same
  annotation.
- These files are read back as they are on disk; no other state is kept between
  runs. A deed open when the tool stopped is not open after a restart.

## Example

```json
{
  "deed_id": "<deed_id from deeds.json>",
  "copied_deed_person_data": {
    "aktenummer": "93",
    "plaats": "Westdorp",
    "naam_volledig": "Jan Modaal",
    "datum_overlijden": "1880-01-02",
    "plaats_overlijden": "Oostdorp"
  },
  "scans": ["page_01.jpg", "page_02.jpg"],
  "annotation_metadata": {
    "annotator_name": "Ann",
    "annotation_date": "2026-10-27T14:03:12.123456+01:00"
  },
  "annotation": {
    "header": {"scan": "page_01.jpg", "bbox": [300, 120, 2400, 520],
               "pagexml_link": null, "pagexml_baseline_ids": null},
    "balance": {
      "layout": {"scan": "page_02.jpg", "bbox": [400, 2600, 2300, 3000],
                 "pagexml_link": null, "pagexml_baseline_ids": null},
      "total_assets": "900,-", "total_liabilities": "", "total": "900,-"},
    "assets": [
      {"layout": [
         {"scan": "page_01.jpg", "bbox": [412, 1880, 2310, 2240],
          "pagexml_link": null, "pagexml_baseline_ids": null},
         {"scan": "page_02.jpg", "bbox": [380, 210, 2290, 420],
          "pagexml_link": null, "pagexml_baseline_ids": null}],
       "category": "property", "amount": "900,-",
       "description": "Een huis met erf ..."}
    ],
    "liabilities": []
  }
}
```

## Field notes

- `amount`: a string; whether it becomes a number is still open.
- `bbox`: in the same pixel space as PageXML.
- `pagexml_link`, `pagexml_baseline_ids`: `null` means "not computed"; `[]` would mean
  "computed, no match".
- `scans`: a page can appear in two deeds' files (one deed ends and the next
  starts on the same page). `scans` always starts on the header page, the page of
  `annotation.header`. Opening sets it. **save header** on another page moves it, and
  `scans` then starts on that page.
- `copied_deed_person_data`: copied when the deed is opened or moved; a later
  change to `deeds.json` does not reach an existing file.
- Item tags (`A1`, `L2`) are computed from list positions and never stored.
