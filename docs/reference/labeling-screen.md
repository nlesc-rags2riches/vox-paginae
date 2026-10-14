# The labeling screen

One view, no scrolling. The page is on the left; the form and zooms on the right.

```
[root picker, collapsed]
[page image, box select ] | <book>/<file.jpg> · person 2 | no person · page 3/7 · pending 1 [· editing A2]
[                       ] | [person ▾] [go to person]
[                       ] | name [_____]  death [_____]
[                       ] | ─────────────────────────
[                       ] | (•) assets ( ) liabilities  category [____]  value [_______]
[                       ] | description [______________________________________]
[                       ] | [continue] [clear pending] [save]
[                       ] | [block ▾] [edit] [cancel edit] [delete]
[                       ] | [prev page] [next page] [close person]
[                       ] | [zoom: pending boxes, then the drawn box]
quality ━●━  height ━●━   |
[jump slider + go, thumbnail strip, folder bar (a trial)]
```

## Status line

`<book>/<file.jpg> · person N | no person · page P/T · pending K`, plus `· editing A2`
while a saved block is being edited.

## Buttons

Buttons are **disabled** while what they need is missing; they never show an error.
Every button that writes a file is disabled while **name** is empty.

| Button | Does | Writes | Disabled when |
|---|---|---|---|
| **continue** | Adds the drawn box to the pending block. The pending block survives page changes. | no | no box drawn |
| **clear pending** | Drops all pending boxes. | no | nothing pending |
| **save** | Adds the drawn box plus pending boxes as one block, or replaces the block being edited. The first save with no current person starts a new person. | yes | no box, no type, no name, or both value and description blank |
| **edit** | Loads the picked block into the inputs and its boxes into the pending block. | no | no saved blocks, editing, or a block is pending |
| **cancel edit** | Drops the inputs and pending boxes; the block is unchanged. | no | not editing |
| **delete** | Removes the picked block. | yes | no saved blocks, editing, or no name |
| **prev page** | One page back, never into the previous book. | no | on page 1 |
| **next page** | One page on. On a book's last page it closes the open person and opens the next book. | only on a book's last page | on a book's last page: a block is pending, editing, or a person is open with no name |
| **close person** | Writes and closes the current person; then there is no current person. | yes | no current person, a block is pending, editing, or no name |
| **go to person** | Moves to the picked saved person's start page (current book only). | no | no person picked, a person is open, or a block is pending |
| **go** (jump) | Moves to the slider's page, in any book. | no | a person is open, a block is pending, or the slider is on the current page |

## Blocks

- **Type** has no default for a person's first block, then stays on the last type used.
- Saved blocks are drawn in colour by type and labelled `A1, A2…` / `L1, L2…`.
- Boxes of every other person in the book are drawn faded and unlabelled.
- Saving an edited block keeps its label unless the type changed; then it goes last of
  the new type.
- Boxes smaller than 3 px on either side are ignored (a plain click is not a box).

## Persons

- A new person's number is the highest `person-NNNN.json` in the book plus one, read at
  save time, so no file is ever overwritten by a new person.
- The person dropdown lists the current book's saved persons, as
  `person-0002 · Antonia Spiering · pages 22-24`.

## Resume

On start, the labeler opens the **last book with any `person-NNNN.json`**, on the last
page in the `scans` of its highest-numbered person, with **no current person**. With no
files at all it opens the first book on page 1. A person is never reopened.

## Display

- **height** sets the on-screen size of the page; **quality** sets its pixel density.
  The page image is capped at 5 megapixels.
- The zooms show the pending boxes, then the drawn box, cropped from the original scan
  and enlarged at most 3×.

## Command-line options

Passed after `--`: `marimo run notebooks/item_block_labeler.py -- <options>`.

| Option | Effect |
|---|---|
| `--data-root <dir>` | Start folder for the root picker (default: home folder). The picker cannot go above it. |
| `--debug` | Shows a **DEBUG PANE** with the open (or last closed) person's file as on disk. |
