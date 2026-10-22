# Agent notes

Standalone continuation of the item-block labeler from the Rags2Riches playground
(`exploration-loghi-fine-tuning/item-block-labeler.py`). An MVP whose code is not yet
human-reviewed: keep changes small, one step at a time, with the user in the loop.

- UI: `notebooks/item_block_labeler.py` (marimo). Logic: `src/vox_paginae/blocks.py`.
  The `marimo-library` skill governs the split; live notebook edits go through
  `marimo-pair` (the running kernel is the source of truth).
- Tests: `uv run pytest`; browser tests `uv run pytest -m e2e` (recipe:
  `~/brain/cookbook/marimo-playwright.md`). Known flakes:
  `test_restart_resumes_on_last_page_with_no_person`, `test_edit_replaces_block_in_place` (#11).
- Docs follow Diátaxis (`~/brain/cookbook/diataxis.md`), built with Zensical
  (`~/brain/cookbook/zensical.md`). Keep them in step with the code:
  a read/write change updates `docs/reference/input-and-output.md` (confirm wording with
  the user first: it is a promise to the person labeling).
- Generic marimo traps: `~/brain/cookbook/marimo-gotchas.md`.
