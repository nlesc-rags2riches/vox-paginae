# Vox Paginae

A [marimo](https://marimo.io) notebook for annotating scanned death-duty deeds: each
deed's header, balance and items (type, amount, description, boxes), saved as
one JSON file per deed.

> [!WARNING]
> **Minimum Viable Prototype, work in progress.** Much of this code was written with an
> AI coding assistant and has not been reviewed line by line by a human. Check the files
> it writes, keep a copy of your scans, and open an issue for anything odd.

```bash
uv sync
uv run marimo run notebooks/deed_annotation.py -- --data-root /path/to/scans
```

Documentation is in [`docs/`](docs/index.md). Preview it with `uv run --group docs zensical serve`.
