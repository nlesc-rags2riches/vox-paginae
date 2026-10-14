# How to develop

```bash
uv sync                                 # all groups but docs
uv run pytest                           # unit tests (tests/test_blocks.py)
uv run playwright install chromium      # once per machine
uv run pytest -m e2e                    # browser tests, about a minute
uv run marimo edit notebooks/item_block_labeler.py -- --data-root <dir>
```

Build and preview these docs:

```bash
uv run --group docs zensical serve      # live preview
uv run --group docs zensical build      # static site in site/
```

Where things go:

- `notebooks/item_block_labeler.py`: the UI only.
- `src/vox_paginae/blocks.py`: everything else (books, pages, person records, resume,
  crops). New logic goes here, with a test.
- A behaviour change updates [The labeling screen](../reference/labeling-screen.md);
  a change to what is read or written updates
  [Input and output](../reference/input-and-output.md); a decision worth remembering
  goes in [About the design decisions](../explanation/design-decisions.md).
