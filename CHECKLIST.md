# Package checklist

What is still missing for a decent package, measured against
[NLeSC/python-template](https://github.com/NLeSC/python-template) (its "recommended"
profile). Template items are translated to this repo's tools: uv instead of
setuptools/tox, Zensical instead of Sphinx/Read the Docs, prek instead of
`.githooks`. Tick items off here; delete the file when it is empty.

## Essentials

- [x] `src/` layout, `tests/`, `docs/`, `README.md`, `.gitignore`, `pyproject.toml`
- [x] `LICENSE` (Apache-2.0), plus `license` and `license-files` in `pyproject.toml`.
      No `NOTICE`: Apache-2.0 only asks to keep one if it exists
- [x] GitHub repository, and `site_url` / `repo_url` / `edit_uri` in `zensical.toml`
- [ ] `[project.urls]` (Repository, Issues, Documentation) in `pyproject.toml`
- [ ] `classifiers` (`Development Status :: 2 - Pre-Alpha`, supported Python versions)
      and `keywords` in `pyproject.toml`
- [ ] `src/vox_paginae/py.typed` (from `uv init`): keep it only if a type checker runs
      (see below), otherwise delete it, as it promises type hints
- Not needed: `MANIFEST.in` (`uv_build` packages `src/` itself)

## Code quality

- [x] CI workflow: `uv run pytest` on Linux, macOS and Windows, Python 3.11 and 3.13
      (`.github/workflows/test.yml`). Replaces the template's tox.
- [ ] Same for `uv run pytest -m e2e`. Closes the "not checked on all platforms" known
      issue.
- [ ] Ruff config in `pyproject.toml` and a lint step in CI. First decide on the 4
      findings and the notebook formatting left from the port.
- [ ] prek hooks (`.pre-commit-config.yaml`; `~/brain/cookbook/prek.md`)
- [ ] `.editorconfig`
- [ ] Coverage (`pytest-cov`, `[tool.coverage.run] branch = true`)
- [ ] Type checker, or drop `py.typed`
- Optional in the template: SonarCloud
- [ ] Notebook clean-ups from the PR #5 review (not bugs):
  - [ ] close the pyplot figure after each redraw, or use a non-pyplot `Figure`
  - [ ] stop re-reading every person file and full-size scan on each redraw (cache by
        mtime, or `lru_cache` on the crop)
  - [ ] drop the unused deceased prefill state; share the close-person logic between
        **close person** and **next page** on the last page
  - [ ] move the page-image reading to `blocks.py` (it repeats `blocks.thumbnail`)

## Documentation

- [x] Local docs (Zensical, Diátaxis), building with `--strict` in CI
- [x] Developer docs (template: `README.dev.md`): `docs/how-to/develop.md`
- [ ] Docs workflow pushing to `gh-pages` (ready-made in `~/brain/cookbook/zensical.md`)
- [ ] Link check for external links (`--strict` only covers internal ones)

## Community

- [ ] `CONTRIBUTING.md` (can point to `docs/how-to/develop.md` and
      `docs/how-to/report-a-problem.md`)
- [ ] `CODE_OF_CONDUCT.md`
- [ ] Beyond the template, for this repo's main goal: a GitHub issue template for
      labelers' bug reports (status line, clicks in order, the person file)

## Publishing and release

- [ ] `CHANGELOG.md`
- [ ] `CITATION.cff`, validated in CI (cffconvert)
- [ ] Zenodo DOI on the first release
- [ ] Versioning: `uv version --bump` instead of the template's bump-my-version
- [ ] Publishing to PyPI: not needed while labelers clone and `uv sync`; decide at v1
