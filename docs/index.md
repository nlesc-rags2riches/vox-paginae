# Vox Paginae

A [marimo](https://marimo.io) notebook for labeling **item blocks** on scanned
death-duty deeds (*memories van successie*). An item block is one item of a deed: a
description of one or more lines, a value, a type (asset or liability), an optional
category, and one or more bounding boxes. Blocks are grouped per deceased person, and
each person is saved as one JSON file next to the scans.

!!! warning "Minimum Viable Prototype, work in progress"
    This is an MVP. Much of the code was written with an AI coding assistant and has
    **not been reviewed line by line by a human**. Treat it as untrusted: check the
    JSON files it writes, keep a copy of your scans, and
    [report anything odd](how-to/report-a-problem.md). The goal of this repository is
    to collect that feedback on the way to a v1.

## Where to go

| You want to… | Read |
|---|---|
| Label your first person, step by step | [Tutorial: label your first person](tutorials/label-your-first-person.md) |
| Install and start the labeler | [How to install and run](how-to/install-and-run.md) |
| Fix a block you already saved | [How to fix a saved block](how-to/fix-a-saved-block.md) |
| Report a bug or a wish | [How to report a problem](how-to/report-a-problem.md) |
| Work on the code or these docs | [How to develop](how-to/develop.md) |
| Know exactly what is read and written | [Input and output](reference/input-and-output.md) |
| Look up what a button does and when it is disabled | [The labeling screen](reference/labeling-screen.md) |
| See the known bugs and limits | [Known issues](reference/known-issues.md) |
| Understand why it works the way it does | [About the design decisions](explanation/design-decisions.md) |

## Origin

The labeler started as `item-block-labeler.py` in the Rags2Riches playground
(`exploration-loghi-fine-tuning`, at commit `abad656` plus uncommitted work of
2026-10-14). This repository is its standalone continuation.
