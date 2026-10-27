# Agent notes

Standalone continuation of the item-block labeler from the Rags2Riches playground
(`exploration-loghi-fine-tuning/item-block-labeler.py`). An MVP whose code is not yet
human-reviewed: keep changes small, one step at a time, with the user in the loop.

- UI: `notebooks/item_block_labeler.py` (marimo). Logic: `src/vox_paginae/blocks.py`.
  The `marimo-library` skill governs the split. Edit the notebook only through
  `marimo-pair`, including when the server runs with `--watch`: the running kernel is
  the source of truth.
- Tests: `uv run pytest`; browser tests `uv run pytest -m e2e` take ~2 min, so while
  working run the affected ones with `-k`, and the whole suite once at the end. Known flakes:
  `test_restart_resumes_on_last_page_with_no_person`, `test_edit_replaces_block_in_place` (#11).
- Docs follow Diátaxis, built with Zensical. Keep them in step with the code:
  a read/write change updates `docs/reference/input-and-output.md` (confirm wording with
  the user first: it is a promise to the person labeling).
