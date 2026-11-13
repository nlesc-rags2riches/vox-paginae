# How to install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and [git](https://git-scm.com).

```bash
git clone https://github.com/nlesc-rags2riches/vox-paginae vox-paginae
cd vox-paginae
uv sync
```

Vox Paginae has two notebooks. Use the one that fits how your scans are stored:

- One folder per deed, each with an `input.json`: the single-deed notebook. This is
  the main way to annotate.
- One folder per book, each with a `deeds.json`: the book notebook.

Both take `--data-root`: where the folder picker starts. The picker cannot go above it.
Without it, the picker starts in the folder you started the tool from.

The scans should be images and various formats are supported (`.jpg`, `.jpeg`, `.png`,
`.tif` or `.tiff` files). If your image is in a different format, [open an
issue](https://github.com/nlesc-rags2riches/vox-paginae/issues) to let us know.

See [Input and output](../reference/input-and-output.md) for more details on
the assumptions and expectations we have for the input and output.

## Single deed folders

From the `vox-paginae` folder, after `uv sync`:

```bash
uv run marimo run notebooks/single_deed_annotation.py -- --data-root /path/to/deeds
```

!!! warning "Limitation: `input.json` is required"
    Every folder under the root that has an `input.json` is a **single deed folder**.
    It should be possible to annotate a deed without one, but that use case is
    still not supported.
    If you need it, let us know by [opening an issue](https://github.com/nlesc-rags2riches/vox-paginae/issues).

## Books

From the `vox-paginae` folder, after `uv sync`:

```bash
uv run marimo run notebooks/deed_annotation.py -- --data-root /path/to/scans
```

The book notebook resumes where the saved files left off.

!!! warning "Limitation: `deeds.json` is required"
    Every folder under the root that has an `deeds.json` is a **book folder**.
    It should be possible to annotate a book without one, but that use case is
    still not supported.
    If you need it, let us know by [opening an issue](https://github.com/nlesc-rags2riches/vox-paginae/issues).

## Contributing

To work on Vox Paginae itself, see [Development](../development.md).
