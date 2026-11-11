"""marimo widgets for the annotator, built from the generic UI in ``vox_paginae.ui``."""

from collections.abc import Callable
from pathlib import Path

import marimo as mo
from matplotlib.axes import Axes

from vox_paginae.annotation import (
    add_item,
    close_deed_record,
    delete_item,
    item_tags,
    replace_item,
    split_tag,
    tagged_section_boxes,
)
from vox_paginae.ui import book_bar_html, crop, item_option, thumbnail


def root_picker(initial_path: Path) -> mo.ui.file_browser:
    """A picker for the root folder that books are found under."""
    return mo.ui.file_browser(
        initial_path=initial_path, selection_mode="directory", multiple=False
    )


def root_line_or_picker(
    root: Path,
    picker: mo.ui.file_browser,
    open_deed: dict | None,
    pending_boxes: list[tuple[str, list[int]]],
) -> mo.Html:
    """``root``, with ``picker`` to change it unless a deed is open or boxes are
    pending: a root change resets the session and drops that work."""
    # The file browser has no disabled state: hide it instead.
    if open_deed is not None or pending_boxes:
        return mo.md(f"root: {root} (locked while a deed is open or boxes are pending)")
    return mo.accordion({f"root: {root} (click to change)": picker})


def annotator_input(name: str, locked: bool) -> mo.ui.text:
    """The annotator name input, holding ``name``; read only while ``locked``."""
    # Read-only while locked: a stray keystroke cannot change who is recorded.
    # debounce=False: lock enables while typing, as save does (no timed debounce: #11)
    return mo.ui.text(label="annotator", value=name, disabled=locked, debounce=False)


def annotator_row(
    annotator_in: mo.ui.text,
    get_annotator: Callable[[], tuple[str, bool]],
    set_annotator: Callable[[tuple[str, bool]], None],
) -> mo.Html:
    """``annotator_in`` with its lock (unlock while locked) button.

    The annotator state is a ``(name, locked)`` pair: lock stores the typed name.
    """
    name, locked = get_annotator()
    lock_btn = mo.ui.button(
        label="unlock" if locked else "lock",
        disabled=not (locked or annotator_in.value.strip()),
        on_click=lambda _: set_annotator(
            (name, False) if locked else (annotator_in.value.strip(), True)
        ),
    )
    return mo.hstack([annotator_in, lock_btn], justify="start", align="end")


def section_field_inputs(
    open_deed: dict | None, section: str, fields: list[str]
) -> tuple[mo.ui.text, ...]:
    """Text inputs for ``fields`` of ``open_deed``'s ``section``, in order.

    ``section`` is ``"header"`` or ``"balance"``. They show the saved values and are
    editable only while a deed is open. Rebuilt on every open, write and close: values
    typed but not saved are then gone.
    """
    saved = open_deed["annotation"][section] if open_deed else {}
    # debounce=False: the value is in before a click on the save button, as for the
    # item amount
    return tuple(
        mo.ui.text(
            label=field.replace("_", " "),
            value=saved.get(field, ""),
            disabled=open_deed is None,
            debounce=False,
        )
        for field in fields
    )


def section_buttons(
    section: str,
    field_inputs: tuple[mo.ui.text, ...],
    *,
    save_fields_label: str,
    set_fields: Callable[..., dict],
    add_box: Callable[..., dict],
    delete_box: Callable[..., dict],
    get_deed_record: Callable[[], dict | None],
    save_and_show_open_deed: Callable[[dict], None],
    scan_names: list[str],
    scan_name: str,
    drawn_box: list[int] | None,
    has_pending_boxes: bool,
    editing_item: bool,
) -> tuple[mo.ui.button, mo.ui.button, mo.ui.dropdown, mo.ui.button]:
    """The save fields button, save box button, tag dropdown and delete box button of
    ``section``.

    ``section`` is ``"header"`` or ``"balance"``. Save fields passes the values of
    ``field_inputs`` (from ``section_field_inputs``) to ``set_fields`` in order, blank
    ones too; save box does so as well. Boxes go in one at a time, on the deed's first
    scan or a later one: before it they would be outside scans. Editing an item locks
    them.
    """
    open_deed = get_deed_record()

    def deed_record_with_typed_fields():
        return set_fields(get_deed_record(), *(field.value for field in field_inputs))

    save_fields_btn = mo.ui.button(
        label=save_fields_label,
        disabled=open_deed is None,
        on_click=lambda _: save_and_show_open_deed(deed_record_with_typed_fields()),
    )
    tag_by_option = {
        f"{tag} · page {scan_names.index(box['scan']) + 1}": tag
        for tag, box in tagged_section_boxes(open_deed, section)
    }
    tag_dropdown = mo.ui.dropdown(options=tag_by_option)

    def delete_picked_box(_):
        if tag_dropdown.value:
            save_and_show_open_deed(delete_box(get_deed_record(), tag_dropdown.value))

    save_box_btn = mo.ui.button(
        label=f"save box as {section}",
        kind="success",
        # Not with pending boxes: the drawn box is then the item's next one.
        disabled=open_deed is None
        or editing_item
        or drawn_box is None
        or has_pending_boxes
        or scan_names.index(scan_name) < scan_names.index(open_deed["scans"][0]),
        # The typed fields too: the inputs are rebuilt on save, so they would be lost.
        on_click=lambda _: save_and_show_open_deed(
            add_box(deed_record_with_typed_fields(), scan_name, drawn_box)
        ),
    )
    # The later ones move up: the second box becomes the first.
    delete_box_btn = mo.ui.button(
        label=f"delete {section} box",
        kind="danger",
        disabled=not tag_by_option or editing_item,
        on_click=delete_picked_box,
    )
    return save_fields_btn, save_box_btn, tag_dropdown, delete_box_btn


def item_dropdown(open_deed: dict | None) -> mo.ui.dropdown:
    """The dropdown of ``open_deed``'s items, by tag.

    Built in its own cell, apart from the item inputs: typing there would rebuild it and
    lose the pick (#60).
    """
    return mo.ui.dropdown(
        options={item_option(tag, item): tag for tag, item in item_tags(open_deed)}
    )


def item_buttons(
    item_dd: mo.ui.dropdown,
    *,
    type_radio: mo.ui.radio,
    category_in: mo.ui.text,
    amount_in: mo.ui.text,
    desc_in: mo.ui.text,
    get_deed_record: Callable[[], dict | None],
    set_deed_record: Callable[[dict | None], None],
    save_open_deed: Callable[[dict], Path],
    save_and_show_open_deed: Callable[[dict], None],
    get_pending_boxes: Callable[[], list[tuple[str, list[int]]]],
    set_pending_boxes: Callable,
    get_editing: Callable[[], str | None],
    set_editing: Callable[[str | None], None],
    set_type: Callable[[str | None], None],
    scan_names: list[str],
    scan_name: str,
    drawn_box: list[int] | None,
    layout_boxes: list[tuple[str, list[int]]],
) -> tuple[mo.ui.button, ...]:
    """The item buttons: continue, clear pending, save, edit, cancel edit, delete and
    close deed, in that order.

    ``item_dd`` (from ``item_dropdown``) picks the item to edit or delete. Save adds the
    item from the inputs and ``layout_boxes``, or replaces the one being edited.
    """

    def open_deed_record() -> dict:
        # The buttons that call this are disabled while no deed is open.
        deed_record = get_deed_record()
        assert deed_record is not None
        return deed_record

    def before_first_scan(scan):
        # Nothing is continued, saved or closed there: it would be outside scans.
        return scan_names.index(scan) < scan_names.index(open_deed_record()["scans"][0])

    def save_item(_):
        fields = (
            type_radio.value,
            category_in.value,
            amount_in.value,
            desc_in.value,
            layout_boxes,
        )
        editing_tag = get_editing()
        if editing_tag is None:
            deed_record = add_item(open_deed_record(), *fields)
        else:
            deed_record = replace_item(open_deed_record(), editing_tag, *fields)
        save_and_show_open_deed(deed_record)
        set_pending_boxes([])
        set_editing(None)

    def edit_item(_):
        if item_dd.value:
            item = dict(item_tags(open_deed_record()))[item_dd.value]
            set_pending_boxes([(box["scan"], box["bbox"]) for box in item["layout"]])
            set_type(split_tag(item_dd.value)[0])
            set_editing(item_dd.value)

    def cancel_edit(_):
        set_editing(None)
        set_pending_boxes([])

    def delete_picked_item(_):
        if item_dd.value:
            deed_record = delete_item(open_deed_record(), item_dd.value)
            save_and_show_open_deed(deed_record)

    def close_open_deed(_):
        try:
            deed_record = close_deed_record(open_deed_record(), scan_names, scan_name)
        except ValueError as e:  # no header box or a blank field: it stays open
            mo.status.toast(str(e))
            return
        path = save_open_deed(deed_record)
        set_deed_record(None)  # no deed open until the next open
        set_type(None)
        mo.status.toast(f"saved {path.name}, deed closed")

    open_deed = get_deed_record()
    has_items = bool(item_dd.options)
    editing = get_editing() is not None
    continue_btn = mo.ui.button(
        label="continue",
        disabled=drawn_box is None
        or (open_deed is not None and before_first_scan(scan_name)),
        on_click=lambda _: set_pending_boxes(lambda p: p + [(scan_name, drawn_box)]),
    )
    # Discards a stray continue: needs no deed or type, unlike save.
    clear_pending_btn = mo.ui.button(
        label="clear pending",
        disabled=not get_pending_boxes(),
        on_click=lambda _: set_pending_boxes([]),
    )
    save_btn = mo.ui.button(
        label="save",
        kind="success",
        disabled=open_deed is None
        or not layout_boxes
        or type_radio.value is None
        or not (amount_in.value.strip() or desc_in.value.strip())
        or any(before_first_scan(scan) for scan, _ in layout_boxes),
        on_click=save_item,
    )
    # Edit loads the item into the inputs and its boxes into pending; save replaces it.
    edit_btn = mo.ui.button(
        label="edit",
        disabled=not has_items or bool(get_pending_boxes()) or editing,
        on_click=edit_item,
    )
    cancel_edit_btn = mo.ui.button(
        label="cancel edit", disabled=not editing, on_click=cancel_edit
    )
    delete_btn = mo.ui.button(
        label="delete",
        kind="danger",
        disabled=not has_items or editing,  # tags would shift
        on_click=delete_picked_item,
    )
    close_deed_btn = mo.ui.button(
        label="close deed",
        disabled=open_deed is None
        or bool(get_pending_boxes())
        or editing
        or before_first_scan(scan_name),
        on_click=close_open_deed,
    )
    return (
        continue_btn,
        clear_pending_btn,
        save_btn,
        edit_btn,
        cancel_edit_btn,
        delete_btn,
        close_deed_btn,
    )


# Quality = PNG pixels per inch of the page height: 100 is 1:1 with the screen, higher
# is sharper (on HiDPI screens) but slower.
QUALITY_DPI = [100, 150, 200, 300]


def view_sliders() -> tuple[mo.ui.slider, mo.ui.slider]:
    """The quality (dpi) and height (inches, shown at 100 px each) sliders of the page."""
    quality = mo.ui.slider(steps=QUALITY_DPI, value=150, label="quality")
    height = mo.ui.slider(4.0, 14.0, step=0.5, value=6.5, label="height")
    return quality, height


def page_view(
    ax: Axes, size: tuple[int, int], height_in: float
) -> tuple[mo.ui.matplotlib, mo.Html]:
    """The page widget for ``ax`` (from ``draw_scan``), and its view.

    The view shows the scan ``height_in`` * 100 px tall whatever its dpi. ``size`` is
    the scan's original size.
    """
    page_sel = mo.ui.matplotlib(ax, debounce=True)
    # mo.ui.matplotlib shows the PNG at its pixel size (capped at 100% width): this box
    # keeps the on-screen size fixed.
    w, h = size
    view = mo.Html(
        f'<div style="width: {round(100 * height_in * w / h)}px">{page_sel}</div>'
    )
    return page_sel, view


ZOOM_MAX = 3  # upscale cap: past 3x the scan's pixels a crop only gets blurrier


def zooms(book: Path, boxes: list[tuple[str, list[int]]]) -> mo.Html:
    """``boxes`` (scan, bbox) of ``book`` at full resolution, stacked in order."""
    return mo.vstack(
        [
            mo.image(
                crop(book / scan, bbox),
                style={
                    "width": "100%",
                    "max-width": f"{ZOOM_MAX * (bbox[2] - bbox[0])}px",
                },
            )
            for scan, bbox in boxes
        ]
    )


THUMB_SPAN = 4  # scans shown on each side of the slider position
THUMB_PX = 100


def thumbnail_strip(
    books: list[Path], book_scans: list[list[Path]], here: tuple[int, int], slider: int
) -> mo.Html:
    """The bar of all books, then thumbnails of the scans around scan ``slider``.

    ``here`` is the current (book, scan) index pair; ``slider`` counts from 0 over all
    books. Marked: ``here`` solid, ``slider`` dashed.
    """
    all_scans = [
        (b, s) for b, scans in enumerate(book_scans) for s in range(len(scans))
    ]
    # here is (len(books), 0) once all books are done: the bar marks the last scan.
    bar = book_bar_html(
        books,
        book_scans,
        all_scans.index(here) if here in all_scans else len(all_scans) - 1,
        slider,
    )

    def thumb(j):
        b, s = all_scans[j]
        style = {"outline": "3px solid currentColor"} if (b, s) == here else {}
        if j == slider:
            style = {**style, "border": "3px dashed currentColor"}
        return mo.image(
            thumbnail(book_scans[b][s], THUMB_PX),
            height=THUMB_PX,
            style=style,
            caption=f"{j + 1}" + (f" {books[b].name}" if s == 0 else ""),
        )

    span = range(
        max(0, slider - THUMB_SPAN), min(len(all_scans), slider + THUMB_SPAN + 1)
    )
    return mo.vstack(
        [mo.Html(bar), mo.hstack([thumb(j) for j in span], justify="start")]
    )
