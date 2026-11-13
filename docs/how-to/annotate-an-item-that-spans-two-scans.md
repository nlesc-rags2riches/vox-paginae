# Annotate an item that spans two scans

An item can start at the bottom of one scan and go on at the top of the next.
Box its start, click **continue** to keep that box, then box the rest on the next
scan. The item is saved once, with a box on each scan.

First start the single-deed notebook, as in
[How to install and run](install-and-run.md#single-deed-folders).

!!! note "Generated page"

    The browser test `tests/e2e/test_howtos.py::test_annotate_an_item_that_spans_two_scans` writes
    this page.
    To change the page, change the test.

1. Open the deed, as in [Annotate a deed](annotate-a-deed.md):

    1. Type `YourName` in **annotator**.
    2. Click **lock**.
    3. Click **deed** and type `1#1002`.
    4. Pick `1#1002 · Klaas Akkerman`.
    5. Click **open**.

2. Click **next page**.

    ![Step 2](screenshots/annotate-an-item-that-spans-two-scans/step-02.jpg)

3. The item starts at the bottom of the right page. Drag a box around the start of the item on the
    scan, then click **continue**.

    ![Step 3](screenshots/annotate-an-item-that-spans-two-scans/step-03.jpg)

4. Click **next page**.

    ![Step 4](screenshots/annotate-an-item-that-spans-two-scans/step-04.jpg)

5. It goes on at the top of the left page. Drag a box around the rest of the item on the scan, then
    pick `4 · assets · 185.45 · Twee koeien, drie schapen, een…` in **input item**.

    ![Step 5](screenshots/annotate-an-item-that-spans-two-scans/step-05.jpg)

6. Click **save**.

    ![Step 6](screenshots/annotate-an-item-that-spans-two-scans/step-06.jpg)

7. Click **close deed**.

    ![Step 7](screenshots/annotate-an-item-that-spans-two-scans/step-07.jpg)

The result:

![The result](screenshots/annotate-an-item-that-spans-two-scans/result.jpg)

In `deed-annotation-1#1002.json`, the item has one box on each scan:

<!-- markdownlint-disable MD013 MD046 -->
```json
{
  "layout": [
    {
      "scan": "scan-002.jpg",
      "bbox": [
        1310,
        1232,
        1910,
        1371
      ],
      "pagexml_link": null,
      "pagexml_baseline_ids": null
    },
    {
      "scan": "scan-003.jpg",
      "bbox": [
        370,
        131,
        940,
        277
      ],
      "pagexml_link": null,
      "pagexml_baseline_ids": null
    }
  ],
  "amount": "185.45",
  "description": "Twee koeien, drie schapen, een varken en twintig kippen, alsmede het landbouwgereedschap, het huisraad, de kleeding en het linnengoed van den overledene, alles bij schatting"
}
```
<!-- markdownlint-enable MD013 MD046 -->
