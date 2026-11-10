# Vox Paginae

[marimo](https://marimo.io) notebooks for annotating scanned death-duty deeds
(_memories van successie_): where each deed's header, balance and **items** are on its
scans, and what the items say. An item is one asset or liability of a deed: its type,
an optional category, an amount or a description (or both), and one or more boxes.
Each deed's annotation is saved as one JSON file next to the deed's scans: in its
single deed folder, or in its book.

!!! warning "Minimum Viable Prototype, work in progress"
    This is an MVP. Much of the code was written with an AI coding assistant and has
    **not been reviewed line by line by a human**. Treat it as untrusted: check the
    JSON files it writes, keep a copy of your scans, and
    report anything odd as an issue. The goal of this repository is
    to collect that feedback on the way to a v1.

## Where to go

| You want to… | Read |
| --- | --- |
| Install and start Vox Paginae | [How to install and run](how-to/install-and-run.md) |
| Know exactly what is read and written | [Input and output](reference/input-and-output.md) |
| Work on Vox Paginae itself | [Development](development.md) |

## Origin

Vox Paginae started as `item-block-labeler.py` in the Rags2Riches playground
(`exploration-loghi-fine-tuning`, at commit `abad656` plus uncommitted work of
2026-10-14). This repository is its standalone continuation.
