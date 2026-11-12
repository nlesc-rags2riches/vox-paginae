# How to install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and `git`.

```bash
git clone <repository-url> vox-paginae
cd vox-paginae
uv sync
```

Vox Paginae has two notebooks. Use the one that fits how your scans are stored:

- One folder per deed, each with an `input.json`: the single-deed notebook. This is
  the main way to annotate.
- One folder per book, each with a `deeds.json`: the book notebook.

Both take `--data-root`: where the folder picker starts. The picker cannot go above it.
Without it, the picker starts in the folder you started the tool from.

## Single deed folders

```bash
uv run marimo run notebooks/single_deed_annotation.py -- --data-root /path/to/deeds
```

- Point `--data-root` at a single deed folder or at any folder above it.
- Every folder under the root that has an `input.json` is a **single deed folder**;
  see [Input and output](../reference/input-and-output.md#single-deed-folders).

## Books

```bash
uv run marimo run notebooks/deed_annotation.py -- --data-root /path/to/scans
```

- Every folder under the root that directly holds scans (`.jpg` or `.jpeg` files, in lower
  or upper case) is a **book**; see [Input and output](../reference/input-and-output.md).
- The book notebook resumes where the saved files left off.

To work on Vox Paginae itself, see [Development](../development.md).
