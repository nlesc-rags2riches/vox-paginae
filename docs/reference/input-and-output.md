# Input and output

Exactly what the tool reads and writes. This is a promise to the annotator: it
changes only on purpose, and never describes internals.

## In

- You give your name as the **annotator** and lock it. Until it is locked, only the
  name and the root folder can be changed. While locked it cannot be edited; unlock it to change it.
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
  ignored, and so are files from the old format (`person-NNNN.json`), deed annotation
  files with the old name (`labeled-deed-<deed_id>.json`) and leftover `.json.tmp`
  files: they are neither read, shown nor removed. Rename an old deed annotation file to
  `deed-annotation-<deed_id>.json` to use it.

## Out

- One **deed annotation file** per deed:
  `<book>/deed-annotation-<deed_id>.json`, saved next to the jpgs. A deed that has a file
  cannot be opened anew, only reopened. It is written and read as UTF-8, on every
  system, so a file saved on one system opens unchanged on another.
- A deed belongs to exactly one book.
- A deed can be opened on any page, with no box drawn. That page is its **first
  page**. The file is written as soon as the deed is opened.
- While it is open, header, item and balance boxes can be saved only on its first page
  or a later page. It can be closed only there too.
- While it is open, **save box as header** saves a drawn box as one of its header
  boxes. A header has one or more boxes. **delete header box** removes one.
- A deed with no header box cannot be closed. Closing it shows why, and it stays open.
- A deed's **balance** is optional. Its three totals can be left empty and it can have
  no box. In the file it is then empty totals and an empty `layout`.
- While a deed is open, its totals can be typed at any time. **save balance totals**
  saves them. Any of them can be left empty. Totals typed but not saved are dropped by
  any other write.
- While it is open, **save box as balance** saves a drawn box as one of its balance
  boxes. **delete balance box** removes one.
- The file holds:
  - `format_version`: the version of the file's format (see Format versions)
  - `deed_id`: as in `deeds.json`
  - `copied_deed_person_data`: the deed's `aktenummer` and `plaats`, and every field
    of its overledene except `rol`, side by side, copied as they are in `deeds.json`
  - `scans`: every page from the first page to the page it was closed on, in page
    order, with or without items. If a box is on a later page, `scans` reaches that
    page instead. Until the first close, only the first page.
  - `annotation_metadata`:
    - `annotator_name`: the annotator of the latest write
    - `annotation_date`: the time of the latest write, with its timezone (ISO 8601,
      e.g. `2026-10-27T14:03:12.123456+01:00`)
  - `annotation`:
    - `header`: a list of the header boxes, each shaped like an item's `layout` entry
      (`scan`, `bbox`, `pagexml_link`, `pagexml_baseline_ids`); `[]` until one is
      saved
    - `balance`: `total_assets`, `total_liabilities` and `total`, strings (`""` when
      left empty), then `layout`, a list of the balance boxes, each shaped like a
      `header` entry; `[]` until one is saved. It is never `null`.
    - then `assets` and `liabilities`, each a list of items
- An item's **type** (asset or liability) is the list it's in. There is no separate
  field for it. Each item has:
  - `layout`: one entry per box, each with `scan` (the filename), `bbox`
    (`[x0, y0, x1, y1]` in image pixels, origin top-left), and `pagexml_link` and
    `pagexml_baseline_ids` (always `null`)
  - `category`: optional free text; left blank, it is written as `null`
  - `amount`: a string
  - `description`: a single line
  - at least one of `amount` and `description` is non-blank; the other may be `""`
- A deed can have no items: every item can be deleted, and the file stays.
- Fields the tool doesn't fill are written as `null`, not left out.
- Every typed field is stored exactly as typed, except for leading and trailing
  whitespaces, which are stripped off.
- **Not in the file:** transcriptions, whether the deed is open right now.
- Each write replaces the whole file, and an interrupted write leaves the previous
  version. An interrupted write can also leave a `deed-annotation-<deed_id>.json.tmp`.
  Opening, moving the annotation, every added, changed or deleted
  item, saving the balance totals, and saving or deleting a header or balance box, is
  in the file at once.
  Closing rewrites `scans`.
  Every write rewrites `format_version`, `annotator_name` and `annotation_date`.
- Moving past a book's last page closes the open deed there. A deed with no header box
  is not closed: it shows why, and the page stays.
- A closed deed can be reopened: it is open again, and the next writes rewrite the
  same file. `scans` stays as it was until the next close.
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
  "format_version": "<the tool's format version>",
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
    "header": [
      {"scan": "page_01.jpg", "bbox": [300, 120, 2400, 520],
       "pagexml_link": null, "pagexml_baseline_ids": null}],
    "balance": {
      "total_assets": "900,-", "total_liabilities": "", "total": "900,-",
      "layout": [
        {"scan": "page_02.jpg", "bbox": [400, 2600, 2300, 3000],
         "pagexml_link": null, "pagexml_baseline_ids": null}]},
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
  starts on the same page). Its first page does not move after opening.
- `copied_deed_person_data`: copied when the deed is opened or moved; a later
  change to `deeds.json` does not reach an existing file.
- Tags (`H1`, `B1`, `A1`, `L2`) are computed from list positions and never stored.

## Format versions

- `format_version` is the version of the file's format (`MAJOR.MINOR.PATCH`), not of
  the annotation or of the tool. It follows
  [Semantic Versioning 2.0.0](https://semver.org).
- The format is the file's name, its encoding, its fields, and what each field holds.
  How the tool lets you edit a deed is not part of the format.
- A change that can break a reader bumps MAJOR. For example: a field dropped or
  renamed, a changed type, a stricter rule, or a field that now holds something else.
- A change that breaks no reader bumps MINOR. For example: a new optional field.
- A change that leaves the fields as they are bumps PATCH. For example: a fixed typo
  in the format's description.
- While MAJOR is `0`, a change that can break a reader bumps MINOR, and any other
  change bumps PATCH.
- A file without `format_version` opens as usual. Its next write adds it. Its other
  fields stay as they were written.
