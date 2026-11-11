# Agent notes

Standalone continuation of `item-block-labeler.py` from the Rags2Riches playground
(`exploration-loghi-fine-tuning`). An MVP whose code is not yet
human-reviewed: keep changes small, one step at a time, with the user in the loop.

- Never write the developer's name in anything you write: files, commits, issues, PRs,
  comments. Write "the developer", even when your own instructions use a name. The one
  exception is the author in `pyproject.toml`.
- Domain words (deed, deed person, item, box, …): `GLOSSARY.md`. Use its terms, not
  the "Avoid" ones.
- UI: `notebooks/deed_annotation.py` (marimo). Logic: `src/vox_paginae/annotation.py`,
  the core, which works on an open deed and knows no input format; each input's
  reading and checks live beside it (`book_input.py` for a book's `deeds.json`).
  The `marimo-library` skill governs the split. The book notebook and the single-deed
  notebook (#85) share `annotation.py` and `marimo_ui.py`: put behaviour both need there,
  so each notebook cell stays a call. New features may land in one notebook only; the
  other's browser tests still pass. Edit the notebook only through
  `marimo-pair`, including when the server runs with `--watch`: the running kernel is
  the source of truth. To test an older notebook, use `git worktree add`: the watched
  file stays as the kernel wrote it. No server running: start one as in
  `docs/development.md` › Run a notebook on fake data, adding `--no-token --watch`
  after `edit`; for the book notebook, lock an annotator name before cells past the
  book cell run (`set_annotator((name, True))` from the scratchpad). The fake deed's
  scans look real, so they also serve for tutorial screenshots.
- Tests: `uv run pytest`; browser tests `uv run pytest -m e2e` take ~2 min, so while
  working run the affected ones with `-k`, and the whole suite once at the end. Known flake:
  `test_restart_resumes_on_last_page_with_no_open_deed`. A browser test that fails once:
  rerun it once alone, then report it to the developer. A browser test that fails in CI
  while #121 is open: check that the run uploaded `e2e-test-results` with a trace and a
  screenshot of that test, and report the result on #121.
- Docs follow Diátaxis, built with Zensical. Keep them in step with the code:
  a read/write change updates `docs/reference/input-and-output.md` (draft it to
  `CODING_STANDARDS.md` › Docs, then confirm the wording with the user: it is a promise
  to the annotator).
- Behaviour changes in the form might affect the user flow and break the how-to docs,
  or leave them longer than they need to be. The how-tos made by
  `tests/e2e/test_howtos.py` change only through that test: see `docs/development.md` ›
  Write the how-to pages. In your report, name each reference and how-to page the
  change touches, and say whether you updated it or why it still holds.

## Agent skills

### Issue tracker

GitHub Issues on `nlesc-rags2riches/vox-paginae`, via `gh`. See `agents/issue-tracker.md`.
Work on a `<issue>-<slug>` branch: prek refuses commits on `main`.
A refactor found in review and left out of the PR: suggest adding it to #52, the
running list of refactor opportunities.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`,
`wontfix`. See `agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` at the root, ADRs in `docs/adr/` (none yet). See `agents/domain.md`.
