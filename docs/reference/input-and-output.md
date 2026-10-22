# Input and output

Exactly what the tool reads and writes. This is a promise to the person labeling: it
changes only on purpose, and never describes internals.

## In

- You pick a root folder. Every folder under it that directly contains `*.jpg` is a
  **book**, and books are taken in sorted path order.
- A book's **pages** are its `*.jpg` files, sorted by filename.
- Nothing else is read: no JSON, no PageXML, no state file. Other files in the tree are
  ignored.

## Out

- One file per person: `<book>/person-NNNN.json`, saved next to the jpgs and numbered
  from `0001` within each book.
- A person belongs to exactly one book.
- The file holds one `metadata` object:
  - `deed_id`: a placeholder uuid4 for now. Whether the real id comes from `deeds.json`
    is an open question.
  - `aktenummer`, `tax_office`, `total`: always `null`
  - `deceased.full_name`: required
  - `deceased.date_of_death`: optional, free text
  - `deceased.place_of_residence`, `deceased.place_of_death`: always `null`
  - `scans`: the person's first page plus every page that has one of their items, in
    page order. When **continue** carries a block across pages, every page with one
    of its boxes is added, still in page order: normally the page where continue was
    pressed, then the page where save was pressed
  - A person can have no items: every block can be deleted, and the file stays. Its
    `scans` then keeps only the person's first page.
  - `assets` and `liabilities`: each has `total` (always `null`) and `items`
- An item's **type** (asset or liability) is the list it's in. There is no separate
  field for it. Each item has:
  - `category`: optional free text; left empty, it is written as `null`
  - `amount`: a string, stored exactly as typed
  - `description`: a single line
  - at least one of `amount` and `description` is non-blank; the other may be `""`
  - `layout`: one entry per box, each with `scan` (the filename), `bbox`
    (`[x0, y0, x1, y1]` in image pixels, origin top-left), and `pagexml_link` and
    `pagexml_baseline_ids` (always `null`)
- Fields the tool doesn't fill are written as `null`, not left out.
- **Not in the file:** transcriptions, whether the person was closed, who labeled it, or
  when.
- The file is written on save, on delete, on close person, and on next page from the
  last page of a book.
- Resume reads only these files, and so does the page view, which draws every other
  person's saved boxes faded.

## Example

```json
{
  "metadata": {
    "deed_id": "<uuid4>",
    "aktenummer": null,
    "tax_office": null,
    "total": null,
    "deceased": {"full_name": "Jan Modaal", "date_of_death": null,
                 "place_of_residence": null, "place_of_death": null},
    "scans": ["page_01.jpg", "page_02.jpg"],
    "assets": {"total": null, "items": [
      {"category": "property", "amount": "900,-",
       "description": "Een huis met erf ...",
       "layout": [
         {"scan": "page_01.jpg", "bbox": [412, 1880, 2310, 2240],
          "pagexml_link": null, "pagexml_baseline_ids": null},
         {"scan": "page_02.jpg", "bbox": [380, 210, 2290, 420],
          "pagexml_link": null, "pagexml_baseline_ids": null}]}
    ]},
    "liabilities": {"total": null, "items": []}
  }
}
```

## Field notes

- `amount`: a string; whether it becomes a number is still open.
- `bbox`: in the same pixel space as PageXML.
- `pagexml_link`, `pagexml_baseline_ids`: `null` means "not computed"; `[]` would mean
  "computed, no match".
- `scans`: deleting a page's last block drops that page. A page can appear in two
  persons' files (one deed ends and the next starts on the same page). The **start
  page** is the earliest page of the person's first block, not the page it was saved
  on. Later blocks never move it; deleting every block resets it.
- Item labels (`A1`, `L2`) are computed from list positions and never stored.
