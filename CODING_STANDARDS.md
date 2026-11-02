# Coding standards

Judgement calls for review. Mechanical rules live in the prek hooks (run locally and in CI).

## Notebook or library

Code that belongs in the library (reused, tested, or read just to work on something
downstream) lives in `src/vox_paginae/`, not in a notebook cell. The `marimo-library`
skill sets the rules.

## Tests

### A disabled-button check must be able to fail

Some features lock buttons while they run: while you edit the header or the balance,
**save**, **edit**, **delete**, **close deed** and **move annotation** are disabled. A browser test
checks this with `expect(button(...)).to_be_disabled()`.

That check only proves something if nothing else could disable the button. **edit** is
also disabled when the deed has no items, so a check made then passes even if the
lock is broken.

Before the check, set up everything the button needs to be enabled: an item, a type, an
amount, a drawn box. Example: `test_edit_balance_rewrites_it_in_place` saves an item first.

## Docs

### Reference wording is short and says each fact once

`docs/reference/` is a promise to the annotator, confirmed with the user word by
word. Short sentences, one fact each, no nested clauses. Each fact has one place: a
bullet adds to the ones above it, and a field note adds to the rule it annotates.

Example: for the balance edit, "changes the saved balance's totals and, if a new box is
drawn on the header page or a later page, its box" became "Its totals can be retyped. A
new box drawn on the page replaces its box"; where a balance box can go was already in
the bullet above.
