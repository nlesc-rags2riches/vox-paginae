# Vox Paginae

A [marimo](https://marimo.io) notebook for labeling item blocks (description, value,
type, bounding boxes) on scanned death-duty deeds, saved as one JSON file per deceased
person.

> [!WARNING]
> **Minimum Viable Prototype, work in progress.** Much of this code was written with an
> AI coding assistant and has not been reviewed line by line by a human. Check the files
> it writes, keep a copy of your scans, and open an issue for anything odd.

```bash
uv sync
uv run marimo run notebooks/item_block_labeler.py -- --data-root /path/to/scans
```

Documentation (Diátaxis: tutorials, how-to guides, reference, explanation) is in
[`docs/`](docs/index.md). Preview it with `uv run --group docs zensical serve`.
