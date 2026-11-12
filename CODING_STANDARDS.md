# Coding standards

Judgement calls for review. Mechanical rules live in the prek hooks (run locally and in CI).

## Notebook or library

Code that belongs in the library (reused, tested, or read just to work on something
downstream) lives in `src/vox_paginae/`, not in a notebook cell. The `marimo-library`
skill sets the rules.

## Names

### A name says what the thing does, even when long

A reader should know what a function does without opening it. Prefer the descriptive
name to the short one.

Example: `save_item`, not `save`: the app also saves header and balance boxes.

## File format

### A format change bumps the format version

The format of the deed annotation file is what the reference's Format versions section
says it is: the file's name, its encoding, its fields, and what each field holds. Any
change to it bumps `FORMAT_VERSION` in `annotation.py`. Which part to bump is a human
call, guided by that section.

`tests/test_format_snapshots.py` compares two files the tool writes, one filled in and
one just opened, with their snapshots in `tests/format_snapshots/<version>/`. A change
to the files' names, encoding or fields fails it. The fix is a new folder named after
the new version, never an edit to an old one.

A change in what a field holds, with the same fields, fails no test. It still bumps the
version. Example: if `scans` held only the pages with boxes, the snapshot could still
pass, but a reader that counts pages would break.

## Tests

### A disabled-button check must be able to fail

Some features lock buttons while they run: while you edit an item, **delete**, **close
deed**, **move annotation** and the header and balance box buttons are disabled. A
browser test checks this with `expect(button(...)).to_be_disabled()`.

That check only proves something if nothing else could disable the button. **delete
header box** is also disabled when the deed has no header box, so a check made then
passes even if the lock is broken.

Before the check, set up everything the button needs to be enabled: a saved box, an
item, a drawn box. Example: `test_edit_replaces_item_in_place` checks **delete header
box** with `H1` saved.

## Docs

### Reference wording is short and says each fact once

`docs/reference/` is a promise to the annotator, confirmed with the user word by
word. Short sentences, one fact each, no nested clauses. Each fact has one place: a
bullet adds to the ones above it, and a field note adds to the rule it annotates.

Example: for the optional balance, "A deed has one balance: three totals and zero or
more boxes" and "Nothing about the balance stops a deed from closing" became "A deed's
balance is optional. Its three totals can be left empty and it can have no box." The
first read as if the balance had to be filled in. The second dropped out: "optional"
already says it.
