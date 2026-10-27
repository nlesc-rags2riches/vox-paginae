# Coding standards

Judgement calls for review. Mechanical rules live in ruff (the prek hook and CI).

## Tests

### A disabled-button check must be able to fail

Some features lock buttons while they run: while you edit the header or the balance,
**save**, **edit**, **delete** and **close deed/person** are disabled. A browser test
checks this with `expect(button(...)).to_be_disabled()`.

That check only proves something if nothing else could disable the button. **edit** is
also disabled when the deed/person has no items, so a check made then passes even if the
lock is broken.

Before the check, set up everything the button needs to be enabled: an item, a type, a
value, a drawn box. Example: `test_edit_balance_rewrites_it_in_place` saves an item first.
