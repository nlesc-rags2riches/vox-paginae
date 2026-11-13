# Development

How to work on Vox Paginae itself. First install it as in
[How to install and run](how-to/install-and-run.md): `uv sync` also installs the
development tools.

## Set up the git hooks

The hooks lint, format and type-check the code, and check the Markdown and the
workflow files. CI runs the same hooks. Install them once, so they run on each commit:

```bash
uvx prek install
```

Run them on every file:

```bash
uvx prek run --all-files
```

A hook refuses commits on `main`. Work on a branch.

## Run the tests

```bash
uv run pytest
```

This skips the browser tests. They need Chromium, installed once with:

```bash
uv run playwright install chromium
```

Then run them (about 2 minutes):

```bash
uv run pytest -m e2e
```

Add `-k <part of a test name>` to run only some tests.

A failed browser test leaves a trace and a screenshot in `test-results/`. Open the
trace with:

```bash
uv run playwright show-trace <trace.zip>
```

## Run a notebook on fake data

Both scripts below write into a folder you name, here `.scratch/demo`, which git
ignores.

### Book notebook

Write the demo book, the one the browser tests use:

```bash
uv run python scripts/demo_data.py .scratch/demo
```

It writes one book, `.scratch/demo/book1/`, with three plain grey scans and a
`deeds.json`. Start the book notebook on it in edit mode, to see the code next to the
app:

```bash
uv run marimo edit notebooks/deed_annotation.py -- --data-root .scratch/demo
```

Pick `book1` in the folder picker.

Add `--debug` after `--data-root .scratch/demo` to show the open (or last closed)
deed's annotation file in a panel. A **debug** switch then hides it.

### Single-deed notebook

Write two fake single deed folders, with scans that look like a real deed:

```bash
uv run python scripts/fake_deed.py .scratch/demo
```

It writes `.scratch/demo/1-1001/` and `.scratch/demo/1-1002/`, the same on every run.
In `1#1002`, an asset starts on one scan and ends on the next. The script refuses to
write a folder that exists. Start the single-deed notebook on them in edit mode:

```bash
uv run marimo edit notebooks/single_deed_annotation.py -- --data-root .scratch/demo
```

## Write the how-to pages

Some how-to pages are written by the browser tests in `tests/e2e/test_howtos.py`,
screenshots included. Each test there is one page: its title comes from the test's
`howto` marker, its intro from the docstring, and its steps from what the test does.
To change such a page, change its test, then run:

```bash
uv run pytest -m e2e tests/e2e/test_howtos.py
```

Commit the pages it writes. CI fails if they differ from what the tests write. The
screenshots are not committed: the docs workflow writes them before it builds the site.

A how-to test writes a page. It does not test the app. Skip every how-to test and
nothing should go untested:

- The other tests check every behaviour, including what a how-to shows.
- A how-to test only waits for what its steps need, as with `expect(status(...))`, and
  checks that its page shows the right thing, such as the JSON at its end.

So when one of the other tests fails, the app has a bug. When a how-to test fails, its
page or the flow it follows has changed.

## Build the docs

The docs use [Zensical](https://zensical.org). Preview them at
<http://localhost:8000> while you write:

```bash
uv run --only-group docs zensical serve
```

Build them as CI does. `--strict` stops the build on any warning:

```bash
uv run --only-group docs zensical build --strict
```

Each push to `main` builds the docs and publishes them at
<https://nlesc-rags2riches.github.io/vox-paginae/>. Pull requests only build them.
