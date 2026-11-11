# Annotate a deed

Open a deed, box its header, add its items and its balance. Each item is
picked from the deed's input, boxed on the scan and corrected to what the scan
says. On open, check the header fields the deed's input filled in.

First start the single-deed notebook, as in
[How to install and run](install-and-run.md#single-deed-folders).

!!! note "Generated page"

    The browser test `tests/e2e/test_howtos.py::test_annotate_a_deed` writes this page.
    To change the page, change the test.

1. Type `YourName` in **annotator**.

    ![Step 1](screenshots/annotate-a-deed/step-01.jpg)

2. Click **lock**.

    ![Step 2](screenshots/annotate-a-deed/step-02.jpg)

3. Click **deed** and type `1#1001`.

    ![Step 3](screenshots/annotate-a-deed/step-03.jpg)

4. Pick `1#1001 · Jan Modaal`.

    ![Step 4](screenshots/annotate-a-deed/step-04.jpg)

5. Click **open**.

    ![Step 5](screenshots/annotate-a-deed/step-05.jpg)

6. Drag a box around the header on the scan, then click **save box as header**.

    ![Step 6](screenshots/annotate-a-deed/step-06.jpg)

7. Click **next page**.

    ![Step 7](screenshots/annotate-a-deed/step-07.jpg)

8. Drag a box around the item on the scan, then pick
    `1 · assets · 1234.56 · Een woonhuis met schuur en erf…` in **input item**.

    ![Step 8](screenshots/annotate-a-deed/step-08.jpg)

9. It's possible to fix the **amount** and **description**. Type `4812.50` in **amount**.

    ![Step 9](screenshots/annotate-a-deed/step-09.jpg)

10. Click **save**.

    ![Step 10](screenshots/annotate-a-deed/step-10.jpg)

11. Add the other asset and the liability the same way:

    1. Drag a box around the item on the scan, then pick
        `2 · assets · 1250.75 · Een perceel bouwland, gelegen …` in **input item**.
    2. Click **save**.
    3. Drag a box around the item on the scan, then pick
        `3 · liabilities · 145.35 · Kosten der begrafenis` in **input item**.
    4. Click **save**.

12. Drag a box around the balance on the scan, then type `6063.25` in **total assets**, `145.35` in
    **total liabilities** and `5917.90` in **total**.

    ![Step 12](screenshots/annotate-a-deed/step-12.jpg)

13. Click **save box as balance**.

    ![Step 13](screenshots/annotate-a-deed/step-13.jpg)

14. Click **close deed**.

    ![Step 14](screenshots/annotate-a-deed/step-14.jpg)

The result:

![The result](screenshots/annotate-a-deed/result.jpg)

Vox Paginae writes the annotation to `deed-annotation-1#1001.json`, in the deed's folder. Here it
is, with an example `annotation_date`. See [Input and output](../reference/input-and-output.md) for
what each field holds.

<!-- markdownlint-disable MD013 MD046 -->
```json
{
  "format_version": "0.1.0",
  "deed_id": "1#1001",
  "copied_deed_person_data": {
    "ref_reg": "1#1001",
    "aktenummer": null,
    "tax_office": "Westdorp",
    "full_name": "Jan Modaal",
    "profession": "landbouwer",
    "date_of_death": "14 maart 1921",
    "place_of_residence": "Oostdorp",
    "place_of_death": "Oostdorp"
  },
  "scans": [
    "scan-001.jpg",
    "scan-002.jpg"
  ],
  "annotation_metadata": {
    "annotator_name": "YourName",
    "annotation_date": "2026-01-05T14:30:00+01:00"
  },
  "annotation": {
    "header": {
      "full_name": "Jan Modaal",
      "date_of_death": "14 maart 1921",
      "place_of_residence": "Oostdorp",
      "layout": [
        {
          "scan": "scan-001.jpg",
          "bbox": [
            1060,
            139,
            1890,
            431
          ],
          "pagexml_link": null,
          "pagexml_baseline_ids": null
        }
      ]
    },
    "balance": {
      "total_assets": "6063.25",
      "total_liabilities": "145.35",
      "total": "5917.90",
      "layout": [
        {
          "scan": "scan-002.jpg",
          "bbox": [
            630,
            192,
            920,
            416
          ],
          "pagexml_link": null,
          "pagexml_baseline_ids": null
        }
      ]
    },
    "assets": [
      {
        "layout": [
          {
            "scan": "scan-002.jpg",
            "bbox": [
              1310,
              616,
              1910,
              886
            ],
            "pagexml_link": null,
            "pagexml_baseline_ids": null
          }
        ],
        "category": null,
        "amount": "4812.50",
        "description": "Een woonhuis met schuur en erf, staande en gelegen te Oostdorp aan den Brink, kadastraal bekend gemeente Oostdorp sectie A nummer 214, groot achttien aren veertig centiaren"
      },
      {
        "layout": [
          {
            "scan": "scan-002.jpg",
            "bbox": [
              1310,
              893,
              1910,
              1063
            ],
            "pagexml_link": null,
            "pagexml_baseline_ids": null
          }
        ],
        "category": null,
        "amount": "1250.75",
        "description": "Een perceel bouwland, gelegen onder Oostdorp in de Noordesch, kadastraal bekend sectie B nummer 87"
      }
    ],
    "liabilities": [
      {
        "layout": [
          {
            "scan": "scan-002.jpg",
            "bbox": [
              1310,
              1101,
              1910,
              1163
            ],
            "pagexml_link": null,
            "pagexml_baseline_ids": null
          }
        ],
        "category": null,
        "amount": "145.35",
        "description": "Kosten der begrafenis"
      }
    ]
  }
}
```
<!-- markdownlint-enable MD013 MD046 -->
