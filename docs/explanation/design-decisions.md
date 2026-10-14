# About the design decisions

Why the labeler works the way it does. Each decision is short and says what it trades
away. Add new ones at the end of their section; mark a reversed one rather than
deleting it.

## Scope: an MVP, and untrusted code

The labeler fills a middle tier between labeling single text lines and labeling whole
deeds: one **item block** at a time. It was built quickly, mostly by an AI coding
assistant, in small steps tried out by one person. Nobody has reviewed the code line
by line, so it is treated as untrusted until v1. That is why the output format is
deliberately plain JSON a person can check by eye, and why the end-to-end browser tests
exist: they pin down behaviour without anyone having to trust the code.

## The output files are the only state

There is no database and no state file. Each person is one JSON file next to the scans,
and resume works out where to continue from those files alone.

- *Gained:* nothing to get out of sync; files can be inspected, copied or fixed by hand.
- *Lost:* closing a person is not recorded, so resume never reopens anyone, may land a
  bit early, and loses a named person who was never saved. A manifest at the root could
  fix that later.

## The output targets the gold JSON shape

Person files mirror the `metadata` section of the project's gold JSON files, with
`null` for every field the tool does not fill (never left out). That keeps comparison
with the gold data trivial. The gold data is a shape reference only; the tool never
reads it, because normal input is bare scans.

## A person starts on their first save

The first design started the next person as soon as the previous one was closed. In
practice a deed ends, irrelevant pages follow, and only later does the next name
appear. So a person now starts when their first block is saved, and their first page is
that block's earliest page. The cost: if the deed starts on a page with no item, that
page is missed. A two-step "start person, then close person" flow is the likely fix.

## Buttons are disabled, never refused

A button whose requirements are not met is greyed out instead of showing an error
after the click. This was the preference of the person labeling during the MVP: the screen always shows what is possible.
The cost is that a disabled button does not say *why*; tooltips are on the wishlist.

## Writes happen on a few clear actions

Files are written on **save**, **delete**, **close person**, and **next page** from a
book's last page. Page navigation within a book writes nothing. A person never crosses
books.

## Amounts are stored as typed

`amount` is a string exactly as written on the scan (`900,-`). Converting to numbers
loses information while the notation is still being understood; the gold data uses
numbers, so comparisons cast.

## Notebook for the UI, library for the logic

The marimo notebook holds only the UI. Everything else (books, pages, records, resume,
crops) is in `src/vox_paginae/blocks.py`, as plain functions that return copies and
never mutate, which keeps them safe in marimo state and easy to unit-test.

## Labels stay ASCII

Button labels avoid emoji (**delete**, not a bin icon). marimo measures output size in a
way that counts the whole screen, page image included, at 2–4 bytes per character as
soon as one wide character appears. The output limit is raised in `pyproject.toml` to
cover typed text.

## Open questions

- How much of the gold JSON should the tool fill: place of death, all pages or only
  pages with items, totals and subtotals?
- Should `deed_id` link to existing deed metadata instead of being a placeholder uuid?
- Should `amount` become a number, and with what semantics?
