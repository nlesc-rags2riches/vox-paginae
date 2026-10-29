# How to install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and `git`.

```bash
git clone <repository-url> vox-paginae
cd vox-paginae
uv sync
```

Start Vox Paginae on a folder of scans:

```bash
uv run marimo run notebooks/deed_annotation.py -- --data-root /path/to/scans
```

- `--data-root` is where the folder picker starts, and it cannot go above it. Without
  it, the picker starts in your home folder.
- Every folder under the root that directly holds `*.jpg` files is a **book**; see
  [Input and output](../reference/input-and-output.md).
- Vox Paginae resumes where the saved files left off.

To see the code next to the app (for development), use `marimo edit` instead of
`marimo run`. Add `--debug` after `--data-root <dir>` to show the open (or last closed)
deed's file in a panel. A **debug** switch then hides it.
