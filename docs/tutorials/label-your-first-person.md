# Label your first person

In this tutorial we will label one deceased person with two items: one asset that fits
on one page, and one item that runs across two pages. At the end we will have a
`person-0001.json` file next to the scans.

We assume the labeler is installed (see [How to install and run](../how-to/install-and-run.md))
and that you have a folder with a few `*.jpg` scans of one deed.

## 1. Start the labeler on your scans

Run, from the repository folder:

```bash
uv run marimo run notebooks/item_block_labeler.py -- --data-root /path/to/scans
```

Open the address it prints. The page image is on the left, the form on the right.
Notice the status line at the top of the form: it shows the file name, `no person`,
`page 1/N` and `pending 0`.

## 2. Name the person

Type the deceased's name in **name**. The date of death is optional; leave it empty
for now.

## 3. Save a one-page item

1. Drag a box around the first item on the page. A dashed box appears, and a zoom of
   it shows up below the buttons.
2. Pick **assets**.
3. Type the value as written, for example `900,-`, in **value**, and the text in
   **description**.
4. Click **save**.

A message confirms the save. The box is now drawn in colour with the label `A1`, and
the status line says `person 1`. The file `person-0001.json` now exists next to the
scans.

## 4. Save an item that runs onto the next page

1. Drag a box around the start of the item at the bottom of the page.
2. Click **continue**. The status line now says `pending 1`.
3. Click **next page**. Notice that `pending 1` stays.
4. Drag a box around the rest of the item, fill **value** and **description**, and
   click **save**.

The item is saved with two boxes, one on each page. On this page it is labelled `A2`.

## 5. Close the person

Click **close person**. The name field empties and the status line says `no person`.
The file is written again.

## What we have

Open `person-0001.json` next to your scans. It holds the name, the two pages in
`scans`, and two items under `assets`, the second one with two entries in `layout`.
The full format is in [Input and output](../reference/input-and-output.md).
